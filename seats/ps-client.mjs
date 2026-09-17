/**
 * Professify — a plain-HTTP driver for Cal Poly's public PeopleSoft class search.
 * =============================================================================
 *
 * WHY THIS EXISTS. scrape-seats.mjs drives the same pages with Playwright: a real Chromium,
 * clicking links and waiting for the DOM to settle. Measured against the live site on
 * 2026-09-15, that is the wrong tool by an order of magnitude:
 *
 *   · every interaction is already an XHR POST to the same .GBL returning text/xml
 *   · one search POST returns an ENTIRE subject — 486 CSC sections in 1,420,019 bytes
 *   · a section's detail POST is  28,425 bytes and  401 ms
 *   · the "View Search Results" (Back) POST is 1,420,233 bytes and 4,360–4,668 ms
 *
 * So the browser was never the bottleneck the timings blamed it for, and neither was the
 * detail page. THE BACK BUTTON IS: it costs 11× the thing we actually want and re-sends the
 * whole result list every single time. For one subject that is 486 × 1.4 MB of redundant
 * traffic to return to a list the client already has in memory.
 *
 * Two consequences shape this file:
 *   1. No browser. The protocol is an ordinary form POST; Chromium bought us nothing but
 *      startup cost, rendering and click choreography.
 *   2. Search NARROW. Because Back re-sends the current result set, the cost of coming back
 *      is set by how big that set is. A course-number band of ~20 sections makes Back cheap;
 *      a whole subject makes it ruinous. The banding logic already exists in scrape-seats.mjs
 *      for the 300-section cap — this reuses the idea for a different reason.
 *
 * THE PROTOCOL, as observed rather than assumed:
 *   · POST to /psc/CSLOPRD/EMPLOYEE/SA/c/COMMUNITY_ACCESS.CLASS_SEARCH.GBL, form name win0
 *   · the body is a DELTA: ~25 IC* control fields plus only the field(s) that changed (479
 *     bytes for a select change), not the whole form
 *   · the response is <?xml ...?><PAGE id='SSR_CLSRCH_ENTRY'>…</PAGE> with HTML in CDATA
 *   · the PAGE id says which screen you are on, which is how this file knows where it is
 *   · ICStateNum comes back in the response and must be echoed on the next post
 *   · nMaxSavedStates = 5, so PeopleSoft retains five page states — see branchable() below
 *
 * POLITENESS IS A FEATURE, NOT A SETTING. This talks to a public university that has been
 * generous and has never once throttled us. Every request goes through one shared limiter,
 * the default ceiling is deliberately low, and the User-Agent says who we are and how to
 * reach us. Do not raise DEFAULT_RPS without asking Cal Poly first.
 */

const ENDPOINT = 'https://cmsweb.pscs.calpoly.edu/psc/CSLOPRD/EMPLOYEE/SA/c/COMMUNITY_ACCESS.CLASS_SEARCH.GBL';

/* One request every 500 ms across every session in the process. The theoretical ceiling is far
   higher — 20 in flight at 400 ms each would be ~50 rps — and that is exactly why the number is
   pinned here rather than derived from what the machine can manage. */
const DEFAULT_RPS = 2;

const UA = process.env.CP_USER_AGENT
  || 'Professify/1.0 (Cal Poly student project; +https://github.com/H2oSync/professify)';

/* ---------------------------------------------------------------- rate limiting ---- */
/* A token bucket shared by every session, because politeness is a property of the PROCESS,
   not of any one worker. Four sessions each "being careful" independently is four times the
   load on a server that only sees one origin. */
class Limiter {
  constructor(rps = DEFAULT_RPS) { this.interval = 1000 / rps; this.next = 0; this.ceiling = this.interval; }
  async take() {
    const now = Date.now();
    const at = Math.max(now, this.next);
    this.next = at + this.interval;
    if (at > now) await new Promise(r => setTimeout(r, at - now));
  }
  /* Back off on trouble and creep back afterwards. Halving is deliberate: a server under
     pressure wants relief now, not a linear apology. */
  slower(reason) {
    this.interval = Math.min(this.interval * 2, 10000);
    console.warn(`  · slowing to ${(1000 / this.interval).toFixed(2)} rps — ${reason}`);
  }
  faster() { this.interval = Math.max(this.ceiling, this.interval * 0.8); }
}

/* ------------------------------------------------------------------ cookie jar ---- */
/* Deliberately minimal: one jar per session, name→value, no domain/path logic. Everything
   here is one host and one path, and a real cookie library would be a dependency carrying
   rules this never exercises. */
class Jar {
  constructor() { this.c = new Map(); }
  absorb(res) {
    const raw = res.headers.getSetCookie ? res.headers.getSetCookie() : [];
    for (const line of raw) {
      const [pair] = line.split(';');
      const i = pair.indexOf('=');
      if (i > 0) this.c.set(pair.slice(0, i).trim(), pair.slice(i + 1).trim());
    }
  }
  header() { return [...this.c].map(([k, v]) => `${k}=${v}`).join('; '); }
}

/* --------------------------------------------------------------- tiny HTML bits ---- */
const dec = s => String(s ?? '')
  .replace(/&nbsp;/g, ' ').replace(/&amp;/g, '&').replace(/&lt;/g, '<')
  .replace(/&gt;/g, '>').replace(/&quot;/g, '"').replace(/&#0?39;|&apos;/g, "'")
  .replace(/\s+/g, ' ').trim();

const stripTags = s => dec(String(s ?? '').replace(/<[^>]*>/g, ' '));

/* Hidden inputs carry the IC* control block. Values are read with either quote style because
   PeopleSoft emits both. */
function hiddenFields(html) {
  const out = {};
  const re = /<input\b[^>]*\bname=['"]([^'"]+)['"][^>]*>/gi;
  let m;
  while ((m = re.exec(html))) {
    const tag = m[0];
    if (!/type=['"]hidden['"]/i.test(tag)) continue;
    const v = tag.match(/\bvalue=['"]([^'"]*)['"]/i);
    out[m[1]] = v ? dec(v[1]) : '';
  }
  return out;
}

/* PeopleSoft appends $N$ / $N to field ids and the index moves between sessions and states,
   so nothing here may ever hardcode one. Find by prefix, like the Playwright version does. */
function findId(html, prefix) {
  const re = new RegExp(`\\bid=['"](${prefix}[^'"]*)['"]`, 'i');
  const m = html.match(re);
  return m ? m[1] : null;
}

/* ------------------------------------------------------------------- the session ---- */
export class PSSession {
  /**
   * @param {object}  opts
   * @param {Limiter} opts.limiter  shared across sessions — pass the SAME one to all of them
   */
  constructor({ limiter, label = 'ps' } = {}) {
    this.jar = new Jar();
    this.limiter = limiter || new Limiter();
    this.label = label;
    this.html = '';        // the last page's HTML, reassembled from the XML envelope
    this.page = null;      // PAGE id — SSR_CLSRCH_ENTRY | SSR_CLSRCH_RSLT | SSR_CLSRCH_DTL
    this.ic = {};          // the IC* control block
    this.bytes = 0;        // running total, so a caller can see what it actually cost
    this.requests = 0;
  }

  /* --- the one place a request is made, so the limiter and the failure rules cannot be
     bypassed by a caller in a hurry --- */
  async #send(body) {
    await this.limiter.take();
    const res = await fetch(ENDPOINT + (body ? '' : ''), {
      method: body ? 'POST' : 'GET',
      headers: {
        'User-Agent': UA,
        'Accept': body ? 'text/xml, */*' : 'text/html,*/*',
        ...(body ? { 'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8' } : {}),
        ...(this.jar.c.size ? { 'Cookie': this.jar.header() } : {}),
      },
      body: body || undefined,
      redirect: 'follow',
    });
    this.jar.absorb(res);
    const text = await res.text();
    this.requests++; this.bytes += text.length;

    /* FAILURE MODES THAT ARRIVE AS HTTP 200. Cal Poly returns a sign-in page when PeopleSoft is
       down for maintenance (errorCode=105), and PeopleSoft itself returns "expired" pages rather
       than a status code. A scraper that only checks res.ok records an outage as "no sections",
       which is exactly how a green run can hold a fraction of a term. */
    if (res.status === 429 || res.status === 503) { this.limiter.slower(`HTTP ${res.status}`); throw new PSError('throttled', res.status); }
    if (res.status >= 500) { this.limiter.slower(`HTTP ${res.status}`); throw new PSError('server', res.status); }
    if (/PeopleSoft is currently offline/i.test(text)) throw new PSError('offline', res.status);
    if (/Oracle PeopleSoft Sign-in|idp\.calpoly\.edu/i.test(text)) throw new PSError('signin', res.status);
    if (/Your session has (expired|timed out)|Page Expired|invalid state/i.test(text)) throw new PSError('expired', res.status);
    this.limiter.faster();
    return text;
  }

  /* The partial-refresh envelope: <PAGE id='…'> with HTML inside CDATA sections. Concatenating
     the CDATA blocks gives back something close enough to a page to read fields out of, which
     is all this needs — no DOM, no parser dependency. */
  #absorb(xml) {
    const pid = xml.match(/<PAGE\b[^>]*\bid=['"]([^'"]+)['"]/i);
    if (pid) this.page = pid[1];
    const parts = [...xml.matchAll(/<!\[CDATA\[([\s\S]*?)\]\]>/g)].map(m => m[1]);
    this.html = parts.length ? parts.join('\n') : xml;
    const fresh = hiddenFields(this.html);
    /* The response only carries the control fields it changed, so merge rather than replace —
       dropping ICSID because one response omitted it is how a session silently dies. */
    for (const [k, v] of Object.entries(fresh)) if (v !== '' || !(k in this.ic)) this.ic[k] = v;
    return this.html;
  }

  async open() {
    const html = await this.#send(null);
    this.html = html;
    this.ic = hiddenFields(html);
    const pid = html.match(/<\w+\b[^>]*\bid=['"](SSR_CLSRCH_\w+)['"]/i);
    this.page = pid ? pid[1] : 'SSR_CLSRCH_ENTRY';
    if (!this.ic.ICSID) throw new PSError('no-session', 200);
    return this;
  }

  /* Build the delta body: the IC* block, then whatever the caller is changing. Field order
     follows the browser's, which costs nothing and keeps the request recognisable to anyone
     reading Cal Poly's logs. */
  #body(action, extra = {}) {
    const p = new URLSearchParams();
    p.set('ICAJAX', '1');
    p.set('ICNAVTYPEDROPDOWN', '0');
    p.set('ICType', this.ic.ICType || 'Panel');
    p.set('ICElementNum', this.ic.ICElementNum || '0');
    p.set('ICStateNum', this.ic.ICStateNum || '1');
    p.set('ICAction', action);
    p.set('ICModelCancel', '0');
    p.set('ICXPos', '0'); p.set('ICYPos', '0');
    p.set('ResponsetoDiffFrame', '-1');
    p.set('TargetFrameName', 'None');
    p.set('FacetPath', 'None');
    p.set('ICFocus', '');
    p.set('ICSaveWarningFilter', '0');
    p.set('ICChanged', '-1');
    p.set('ICSkipPending', '0');
    p.set('ICAutoSave', '0');
    p.set('ICResubmit', '0');
    p.set('ICSID', this.ic.ICSID || '');
    p.set('ICActionPrompt', 'false');
    p.set('ICBcDomData', this.ic.ICBcDomData || '');
    p.set('ICPanelName', '');
    p.set('ICFind', '');
    p.set('ICAddCount', '');
    p.set('ICAppClsData', '');
    for (const [k, v] of Object.entries(extra)) p.set(k, v);
    return p.toString();
  }

  /* Set a field by id-PREFIX and let PeopleSoft process the change, exactly as a blur would. */
  async setField(prefix, value) {
    const id = findId(this.html, prefix);
    if (!id) throw new PSError('no-field:' + prefix, 0);
    this.#absorb(await this.#send(this.#body(id, { [id]: value })));
    return id;
  }

  /* Activate a control (a button, or a section link in the results grid). */
  async press(idOrPrefix) {
    const id = findId(this.html, idOrPrefix) || idOrPrefix;
    this.#absorb(await this.#send(this.#body(id, {})));
    return id;
  }

  /* A SNAPSHOT OF THE CURRENT STATE, so a caller can try branching from it instead of paying
     for Back. PeopleSoft's generated JS reports nMaxSavedStates = 5, i.e. five page states stay
     addressable, which is what makes this worth attempting at all. Unproven against Cal Poly —
     scrape-http.mjs tests it and falls back to Back when it does not hold. */
  snapshot() { return { ic: { ...this.ic }, html: this.html, page: this.page }; }
  restore(snap) { this.ic = { ...snap.ic }; this.html = snap.html; this.page = snap.page; }
}

export class PSError extends Error {
  constructor(kind, status) { super(`${kind} (HTTP ${status})`); this.kind = kind; this.status = status; }
}

/* --------------------------------------------------------------- page readers ---- */

/* One row per section from a results page. Same fields the Playwright parser pulls, read from
   the same markup — class number, section, meeting time, room, instructor, and the status badge
   that lives in an <img alt>. There are NO seat numbers here; that is the whole problem, and it
   was verified directly: `Available Seats`, `Class Capacity` and `Enrollment Total` appear
   nowhere in a 1.7 MB results payload. */
export function parseResults(html) {
  const rows = [];
  const re = /<a\b[^>]*\bid=['"](MTG_CLASS_NBR\$\d+)['"][^>]*>([\s\S]*?)<\/a>/gi;
  let m;
  while ((m = re.exec(html))) {
    const idx = +m[1].split('$')[1];
    rows.push({ actionId: m[1], index: idx, class_nbr: stripTags(m[2]) });
  }
  return rows;
}

/* The four numbers the whole exercise is for, plus the waitlist pair. Read as labelled values
   because PeopleSoft's detail layout is a label/value table and the labels are stable even when
   the surrounding markup is not. */
export function parseDetail(html) {
  const t = stripTags(html);
  const g = label => { const m = t.match(new RegExp(label + '\\s*([0-9]+)', 'i')); return m ? +m[1] : null; };
  return {
    capacity: g('Class Capacity') ?? g('Enrollment Capacity'),
    enrolled: g('Enrollment Total'),
    available: g('Available Seats'),
    waitlist_capacity: g('Wait List Capacity'),
    waitlist_total: g('Wait List Total'),
  };
}

/* A results page can arrive behind "your search will return over N classes, would you like to
   continue?" — the same interstitial the Playwright version dismisses. */
export function oversizePrompt(html) {
  return /would you like to continue|return more than|exceed the maximum limit/i.test(stripTags(html));
}

export { Limiter, ENDPOINT, DEFAULT_RPS, UA };
