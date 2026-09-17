#!/usr/bin/env node
/**
 * Professify — Cal Poly seat scraper (Playwright, with real seat COUNTS)
 * ---------------------------------------------------------------------
 * Drives the public PeopleSoft class search exactly like a person:
 *   institution SLCMP -> term 2268 -> per subject: search -> parse list
 *   -> (optional) open each section's detail page for capacity/enrolled/
 *   available/waitlist -> upsert into Supabase.
 *
 * v2 — hardened for unattended GitHub Actions runs:
 *   • Field IDs found by PREFIX (PeopleSoft's $N$ indices differ per session).
 *   • Every set verifies the value actually stuck, and retries if not.
 *   • After Search, waits for EITHER a results list OR a known message.
 *   • On zero results it writes diagnostics (screenshot + page text) so the
 *     workflow artifact shows exactly what the runner saw.
 *
 *   npm i && npx playwright install --with-deps chromium
 *   CP_SUBJECTS=BUS CP_FETCH_DETAILS=1 SUPABASE_URL=... SUPABASE_SERVICE_KEY=... node scrape-seats.mjs
 */
import { chromium } from 'playwright';
import { writeFile } from 'node:fs/promises';
import { planFor, describe } from './cadence.mjs';
import { resolveTerm, termCandidates, matchesTerm, termsNamedIn } from './term.mjs';
import { buildUpsertRows, dedupeByClassNbr, confirmTerm } from './rows.mjs';
import { indexableAgainstPage, bandPlan, mergeBands } from './bands.mjs';

const CFG = {
  URL: process.env.CP_URL || 'https://cmsweb.pscs.calpoly.edu/psc/CSLOPRD/EMPLOYEE/SA/c/COMMUNITY_ACCESS.CLASS_SEARCH.GBL',
  INSTITUTION: process.env.CP_INSTITUTION || 'SLCMP',
  TERM: process.env.CP_TERM || '2268',                       // Fall Semester 2026
  SUBJECTS: (process.env.CP_SUBJECTS || 'BUS').split(',').map(s => s.trim()).filter(Boolean),
  FETCH_DETAILS: process.env.CP_FETCH_DETAILS !== '0',        // ON by default (seat counts)
  HEADLESS: process.env.CP_HEADLESS !== '0',
  SUPABASE_URL: process.env.SUPABASE_URL || '',
  SUPABASE_SERVICE_KEY: process.env.SUPABASE_SERVICE_KEY || '',

  /* THE REGISTRAR'S CLOCK (cadence.mjs). The scraper used to run every morning whether or not a
     seat could move; now Cal Poly's published calendar decides. CP_IGNORE_CALENDAR=1 runs anyway
     — for a manual pull, or for the day the calendar file is wrong and the data matters more. */
  TERM_LABEL: process.env.CP_TERM_LABEL || '',
  IGNORE_CALENDAR: process.env.CP_IGNORE_CALENDAR === '1',
  /* Resolve the term code against the live page and print it, without scraping anything. */
  DISCOVER_ONLY: process.env.CP_DISCOVER_TERM === '1' || process.argv.includes('--discover-term'),
};
const sleep = ms => new Promise(r => setTimeout(r, ms));

// ---- in-page helpers (run inside the browser) --------------------------------
// Find a field by exact id OR by id-prefix (PeopleSoft appends $N$ that varies).
const PAGE_HELPERS = () => {
  window.__pf_find = function (idOrPrefix) {
    let el = document.getElementById(idOrPrefix);
    if (el) return el;
    return document.querySelector('[id^="' + idOrPrefix + '"]') || null;
  };
};

// Fire an action and wait for the PeopleSoft postback (POST to the .GBL) to land.
async function postback(page, action) {
  await Promise.all([
    page.waitForResponse(r => r.url().includes('CLASS_SEARCH') && r.request().method() === 'POST', { timeout: 25000 }).catch(() => {}),
    action(),
  ]);
  await sleep(450);
}

// Read a field's current value (by id or prefix).
function readField(page, idOrPrefix) {
  return page.evaluate(p => { const el = window.__pf_find(p); return el ? (el.value ?? '') : null; }, idOrPrefix);
}

// Set a field the way PeopleSoft needs (real change event), verify it stuck, retry.
async function setField(page, idOrPrefix, value, label) {
  for (let attempt = 1; attempt <= 3; attempt++) {
    const found = await postback(page, () => page.evaluate(({ p, value }) => {
      const el = window.__pf_find(p); if (!el) return false;
      el.focus && el.focus();
      el.value = value;
      el.dispatchEvent(new Event('change', { bubbles: true }));
      el.dispatchEvent(new Event('blur', { bubbles: true }));
      return true;
    }, { p: idOrPrefix, value })).then(() => true).catch(() => false);
    const now = await readField(page, idOrPrefix);
    if (now != null && String(now).trim() === String(value).trim()) return true;
    console.log(`    · ${label || idOrPrefix}: set "${value}" attempt ${attempt} -> now "${now}" (retrying)`);
    await sleep(500);
  }
  const now = await readField(page, idOrPrefix);
  console.log(`    · ${label || idOrPrefix}: value is "${now}" after 3 tries (wanted "${value}")`);
  return false;
}

async function dismissOversize(page) {
  const txt = await page.evaluate(() => document.body.innerText);
  if (/would you like to continue|more than \d+ (classes|results)|return more than/i.test(txt)) {
    console.log('    · oversize prompt detected — clicking OK');
    await postback(page, () => page.evaluate(() => {
      const ok = [...document.querySelectorAll('input[type="button"],input[type="submit"],a,button')]
        .find(e => /^OK$/i.test((e.value || e.textContent || '').trim()));
      if (ok) ok.click();
    }));
  }
}

// Detect a "nothing here" / error state after a search, for logging + diagnostics.
// Uncheck "Show Open Classes Only" and PROVE it stuck. Returns a string for the log:
//   'off'            already off
//   'on->off'        unchecked cleanly
//   'on->off(retry2)'unchecked, but only after the form re-rendered under us
//   'STUCK-ON'       could not clear it — the caller treats this as a failed search
//   'absent'         no such control on this page
async function setOpenOnlyOff(page) {
  let before = null;
  for (let attempt = 1; attempt <= 4; attempt++) {
    // Let any postback triggered by the previous field edit finish before we touch anything.
    await page.waitForLoadState('networkidle', { timeout: 4000 }).catch(() => {});
    const state = await page.evaluate(() => {
      const o = document.querySelector('input[type="checkbox"][id^="SSR_CLSRCH_WRK_SSR_OPEN_ONLY$"]');
      if (!o) return { absent: true };
      const was = o.checked;
      if (o.checked) o.click();                                  // native click; syncs $chk via PeopleSoft JS
      if (o.checked) { o.checked = false; o.dispatchEvent(new Event('change', { bubbles: true })); }
      // The hidden partner is what actually rides the form post. Clear it explicitly rather
      // than trusting that the framework's own handler ran.
      const hidden = document.querySelector('input[id^="SSR_CLSRCH_WRK_SSR_OPEN_ONLY$"][type="hidden"]')
                  || document.getElementById(o.id + '$chk')
                  || document.querySelector('input[name="' + o.name + '$chk"]');
      if (hidden) hidden.value = 'N';
      return { absent: false, was, now: o.checked, hidden: hidden ? hidden.value : null };
    });
    if (state.absent) return 'absent';
    if (before === null) before = state.was ? 'on' : 'off';
    if (!state.now && state.hidden !== 'Y') {
      // Read it back one more time — a postback landing in this gap is the whole bug.
      await page.waitForTimeout(250);
      const still = await page.evaluate(() => {
        const o = document.querySelector('input[type="checkbox"][id^="SSR_CLSRCH_WRK_SSR_OPEN_ONLY$"]');
        return o ? o.checked : null;
      });
      if (still === false || still === null) return before + '->off' + (attempt > 1 ? `(retry${attempt})` : '');
    }
  }
  return 'STUCK-ON';
}

async function searchOutcome(page) {
  return page.evaluate(() => {
    const t = document.body.innerText || '';
    const has = re => re.test(t);
    const results = !!document.querySelector('a[id^="MTG_CLASS_NBR$"]');
    let msg = '';
    // Check the 300-section cap FIRST. Cal Poly's form ALWAYS carries the static instruction
    // "Select at least 2 search criteria", so the need-criteria test below matches on every
    // page and used to mask the real cause — an over-limit refusal was reported as
    // "need-criteria", which is why this failure was so hard to read in the logs.
    if (has(/exceed(s)? the maximum limit of \d+ sections|Specify additional criteria to continue/i)) msg = 'over-limit';
    // Only classify a "problem" message when the page actually has NO results — the criteria
    // instructions stay on screen next to a perfectly good result set, and reporting
    // "need-criteria" on a successful search made healthy runs look broken.
    else if (results) msg = '';
    else if (has(/no classes found|search returns no results|did not return any/i)) msg = 'no-results';
    else if (has(/at least \d+ search criteria|enter (at least|any) .*criteria|Please enter/i)) msg = 'need-criteria';
    else if (has(/is a required field/i)) msg = 'required-field';
    else if (has(/would you like to continue|return more than/i)) msg = 'oversize-prompt';
    return { results, msg, title: document.title };
  });
}

async function dumpDiag(page, tag) {
  try {
    await page.screenshot({ path: `diag-${tag}.png`, fullPage: true }).catch(() => {});
    const info = await page.evaluate(() => ({
      title: document.title, url: location.href,
      text: (document.body.innerText || '').slice(0, 8000),
      inst: (window.__pf_find && window.__pf_find('CLASS_SRCH_WRK2_INSTITUTION') || {}).value,
      strm: (window.__pf_find && window.__pf_find('SLO_SS_DERIVED_STRM') || {}).value,
      subj: (window.__pf_find && window.__pf_find('SSR_CLSRCH_WRK_SUBJECT_SRCH') || {}).value,
      hasSearchBtn: !!(window.__pf_find && window.__pf_find('CLASS_SRCH_WRK2_SSR_PB_CLASS_SRCH')),
    }));
    await writeFile(`diag-${tag}.txt`,
      `title: ${info.title}\nurl: ${info.url}\ninstitution: ${info.inst}\nterm(strm): ${info.strm}\nsubject: ${info.subj}\nsearchBtnPresent: ${info.hasSearchBtn}\n\n----- page text (first 8k) -----\n${info.text}\n`);
    console.log(`    · wrote diag-${tag}.png / diag-${tag}.txt  (inst=${info.inst} strm=${info.strm} subj=${info.subj} searchBtn=${info.hasSearchBtn})`);
  } catch (e) { console.log('    · diag dump failed:', e.message.split('\n')[0]); }
}

function parseList(page, subject) {
  return page.evaluate((subject) => {
    const out = []; let title = '';
    const nodes = document.querySelectorAll('td, a[id^="MTG_CLASS_NBR$"]');
    nodes.forEach(el => {
      if (el.tagName === 'TD') {
        const first = (el.innerText || '').split('\n')[0].trim();
        if (/^[A-Z]{2,6}\s+\d+\w*\s+-\s+/.test(first)) title = first;
      } else {
        const tr = el.closest('tr'); if (!tr) return;
        const cells = [...tr.querySelectorAll('td')].map(td => (td.innerText || '').trim().replace(/\s+/g, ' '));
        const img = tr.querySelector('img[alt]');
        const tm = title.match(/^([A-Z]{2,6})\s+(\d+\w*)\s+-\s+(.+)$/);
        // Meeting time is normally the 3rd cell, but the column can shift; pick whichever
        // cell actually looks like a meeting pattern, else fall back to cells[2].
        const looksTime = v => /(?:Mo|Tu|We|Th|Fr|Sa|Su)/.test(v || '') || /\d{1,2}:\d{2}\s*[AP]M/i.test(v || '') || /\b(?:TBA|TBD|Arranged|ARR)\b/i.test(v || '');
        let days = cells[2] || '';
        if (!looksTime(days)) { const hit = cells.find(looksTime); if (hit) days = hit; }
        out.push({
          subject, index: out.length,
          course_code: tm ? (tm[1] + ' ' + tm[2]) : '',
          title: tm ? tm[3] : title,
          class_nbr: (el.innerText || '').trim(),
          section: cells[1] || '', instructor: cells[4] || '', days: days, dates: cells[5] || '',
          status_raw: img ? img.getAttribute('alt') : '',
        });
      }
    });
    return out;
  }, subject);
}

async function fetchDetail(page, index) {
  /* CLICK NOTHING AND WAIT ANYWAY — the shape of the 40-minute stall.
     `if (a) a.click()` made a missing link a no-op, and the wait below then sat for its full 12
     seconds before .catch() swallowed the timeout. Two hundred orphaned indices is forty minutes
     of a lane doing nothing, with not one line in the log saying so.
     A missing link is now an immediate, named failure. It should also be unreachable: the caller
     checks the page's link count against the list length before it starts. */
  const clicked = await page.evaluate(i => {
    const a = document.getElementById('MTG_CLASS_NBR$' + i);
    if (!a) return false;
    a.click();
    return true;
  }, index);
  if (!clicked) return { missing: true, index };
  await page.waitForFunction(() => /Class Capacity|Enrollment Total/i.test(document.body.innerText) && document.getElementById('CLASS_SRCH_WRK2_SSR_PB_BACK'), null, { timeout: 12000 }).catch(() => {});
  // NOTE: real meeting day/time AND instructor already come from the fast LIST page
  // (parseList -> cells[2]/cells[4]); they're verified correct, so we do NOT touch them
  // here — the detail page is opened ONLY for the numeric seat counts.
  const c = await page.evaluate(() => {
    const t = document.body.innerText;
    const g = l => { const m = t.match(new RegExp(l + '\\s*([0-9]+)', 'i')); return m ? +m[1] : null; };
    // Meeting day/time from the detail page's Meeting Information — used only as a fallback
    // when the list-page cell was blank, so sections that DO have a time stop showing TBA.
    let days_detail = '';
    const mm = t.match(/((?:Mo|Tu|We|Th|Fr|Sa|Su)+)\s+(\d{1,2}:\d{2}\s*[AP]M)\s*[-–to]+\s*(\d{1,2}:\d{2}\s*[AP]M)/i);
    if (mm) days_detail = (mm[1] + ' ' + mm[2] + '-' + mm[3]).replace(/\s+/g, ' ').trim();
    // CATALOG (static per course) — prerequisites + description, both on this same detail page.
    // Captured here for free (no extra page load). Stored in a separate course_catalog table so
    // it NEVER touches the seat upsert. `grab` slices the text between a start label and the next
    // section header. Prereqs also appear in prose inside Description, giving a natural fallback.
    const grab = (startRe, stopRe) => {
      const i = t.search(startRe); if (i < 0) return '';
      const rest = t.slice(i).replace(startRe, '');
      const e = rest.search(stopRe);
      return (e < 0 ? rest : rest.slice(0, e)).replace(/\s+/g, ' ').trim();
    };
    /* INSTRUCTION MODE + LOCATION. PeopleSoft prints both in the Class Details block of this
       same detail page, so they cost nothing extra — no additional page load, no extra time.
       They are the ONLY thing that says whether a class is asynchronous or online; a blank
       meeting time does not, because "not scheduled yet" looks identical. */
    const label = (re) => {
      const m = t.match(re); if (!m) return '';
      const v = (m[1] || '').replace(/\s+/g, ' ').trim();
      // Reject a capture that is really the next label (empty value rows shift the text).
      if (!v || /^(Career|Dates|Grading|Units|Campus|Location|Session|Status|Class Number|Class Components|Instruction Mode|Add Consent|Drop Consent)$/i.test(v)) return '';
      return v.slice(0, 60);
    };
    const instruction_mode = label(/Instruction Mode\s*[:\n\r]*\s*([^\n\r]{1,60})/i);
    const location = label(/(?:^|\n)\s*Location\s*[:\n\r]*\s*([^\n\r]{1,60})/i);
    const room = label(/(?:^|\n)\s*Room\s*[:\n\r]*\s*([^\n\r]{1,60})/i);
    const prereq = grab(/Enrollment Requirements/i, /(Class Availability|Class Capacity|Description|Textbook|View Search Results)/i).slice(0, 700);
    const description = grab(/\bDescription\b/i, /(Textbook\s*\/?\s*Other|Special Instructions|Course Materials|View Search Results)/i).slice(0, 1500);
    return {
      capacity: g('Class Capacity') ?? g('Enrollment Capacity'), enrolled: g('Enrollment Total'),
      available: g('Available Seats'), waitlist_capacity: g('Wait List Capacity'), waitlist_total: g('Wait List Total'),
      days_detail, prereq, description,
      instruction_mode, location, room,
    };
  });
  await page.evaluate(() => { const b = document.getElementById('CLASS_SRCH_WRK2_SSR_PB_BACK'); if (b) b.click(); });
  await page.waitForFunction(() => document.getElementById('MTG_CLASS_NBR$0') && !document.getElementById('CLASS_SRCH_WRK2_SSR_PB_BACK'), null, { timeout: 12000 }).catch(() => {});
  await sleep(120);
  return c;
}

const statusBadge = s => { s = (s || '').toLowerCase(); return s.includes('wait') ? 'Waitlist' : s.includes('open') ? 'Open' : s.includes('clos') ? 'Closed' : null; };

async function run() {
  console.log(`Professify seat scraper v2 — term ${CFG.TERM || '(resolve ' + CFG.TERM_LABEL + ')'}, subjects [${CFG.SUBJECTS.join(', ')}], counts=${CFG.FETCH_DETAILS ? 'on' : 'off'}, headless=${CFG.HEADLESS}`);

  /* ---- the registrar's clock -------------------------------------------------------------
     Ask the calendar before spending anything. This is belt-and-braces: the workflow already
     gates on plan.mjs, so a lane that gets here is normally due. It is repeated inside the
     scraper because the workflow is not the only way this runs — a local invocation, a rerun of
     an old job, or a matrix entry that was queued hours ago all arrive with no gate at all, and
     a rerun of yesterday's job hammering Cal Poly for a term nobody can enrol in is exactly the
     behaviour this whole change exists to stop.

     Exit 0, not an error: "nothing to do" is a correct outcome, and a red run for it teaches
     everyone to ignore red runs. */
  if (!CFG.IGNORE_CALENDAR && !CFG.DISCOVER_ONLY) {
    const plan = planFor(new Date());
    console.log(describe(plan));
    const label = CFG.TERM_LABEL;
    const mine = label
      ? plan.terms.find(t => t.label === label)
      : plan.terms.find(t => t.term_code && t.term_code === CFG.TERM);
    if (!mine) {
      console.log(`• No calendar entry matches ${label || 'term ' + CFG.TERM} — running anyway rather than skipping a term the calendar has not heard of.`);
    } else if (mine.phase === 'dark') {
      console.log(`• Skipping: ${mine.why}. Set CP_IGNORE_CALENDAR=1 to override.`);
      return;
    }
    /* THIS CHECKS THE PHASE, NOT THE SLOT — and that distinction is the whole point.
       plan.mjs decides whether this MINUTE is a scheduled pull, using a five-minute tolerance
       around the aligned slot. By the time a lane reaches this line it has paid for a checkout,
       setup-node, `npm install` and `npx playwright install --with-deps chromium` — reliably two
       to six minutes. Re-asking "is this minute a slot?" therefore asks a question whose answer
       has already expired: the lane prints one line and exits 0 having scraped nothing, and a
       cron running more than five minutes late (which GitHub explicitly does not promise not to
       do) takes the scraper to ZERO pulls a day with every run green.
       `dark` is the only thing a lane can usefully re-check, because it is a property of the DAY
       and cannot expire while the job installs a browser. */
  }
  const browser = await chromium.launch({ headless: CFG.HEADLESS });
  const ctx = await browser.newContext({
    userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
    viewport: { width: 1366, height: 900 }, locale: 'en-US',
  });
  const page = await ctx.newPage();
  page.on('dialog', d => d.dismiss().catch(() => {}));

  await page.goto(CFG.URL, { waitUntil: 'domcontentloaded' });
  await page.addInitScript(PAGE_HELPERS);                 // for future navigations
  await page.evaluate(PAGE_HELPERS);                      // and this page
  // Wait for the search FORM (institution field, any $N$ index) to render.
  await page.waitForFunction(() => !!document.querySelector('[id^="CLASS_SRCH_WRK2_INSTITUTION"]'), null, { timeout: 45000 })
    .catch(() => {});
  const gotForm = await page.evaluate(() => !!document.querySelector('[id^="CLASS_SRCH_WRK2_INSTITUTION"]'));
  console.log(`• Loaded search form: ${gotForm ? 'yes' : 'NO'}  (title="${await page.title()}")`);
  if (!gotForm) { await dumpDiag(page, 'noform'); }

  await setField(page, 'CLASS_SRCH_WRK2_INSTITUTION', CFG.INSTITUTION, 'institution'); // populates subjects

  /* ---- which term is this, really? -------------------------------------------------------
     A wrong STRM does not fail. The search accepts it, returns nothing, and the run goes green
     with an empty result that is indistinguishable from "no classes this term". So the code is
     either one production has already proven (CP_TERM), or one the live page confirms by name
     (term.mjs). Never one computed from a convention and trusted. */
  const termIO = {
    log: m => console.log(m),
    /* setField returns FALSE after three failed attempts and otherwise only logs, so discarding
       its result makes "the field silently kept its old value" indistinguishable from success —
       and the old value is a different term. */
    setTerm: async code => {
      const stuck = await setField(page, 'SLO_SS_DERIVED_STRM', code, 'term');
      if (!stuck) throw new Error(`could not set the term field to ${code} — it still reads "${await readField(page, 'SLO_SS_DERIVED_STRM')}"`);
    },
    /* Only the term field's own row, not the whole page: elsewhere on this page sits a notice
       about when the NEXT term's schedule becomes available, and a page-wide search for
       "Spring 2027" would happily match that and confirm the wrong term. */
    readEcho: () => page.evaluate(() => {
      const el = document.querySelector('[id^="SLO_SS_DERIVED_STRM"]');
      if (!el) return '';
      const row = el.closest('tr, .ps_box-group, div');
      return ((row && row.innerText) || '').replace(/\s+/g, ' ').trim().slice(0, 200);
    }),
    subjectCount: () => page.evaluate(() => {
      const s = document.querySelector('select[id^="SSR_CLSRCH_WRK_SUBJECT_SRCH"]');
      return s ? s.options.length : 0;
    }),
    /* The one signal neighbouring text cannot contaminate: what the field itself now holds. */
    readField: () => readField(page, 'SLO_SS_DERIVED_STRM'),
  };

  if (CFG.TERM && !CFG.DISCOVER_ONLY) {
    await termIO.setTerm(CFG.TERM);
    /* rows.mjs decides; see the note there on why an UNREADABLE echo degrades while a
       CONTRADICTING one refuses. */
    const verdict = confirmTerm(
      { code: CFG.TERM, label: CFG.TERM_LABEL, echo: await termIO.readEcho(), back: await readField(page, 'SLO_SS_DERIVED_STRM') },
      termsNamedIn, matchesTerm);
    if (verdict.degraded) console.log(`::warning title=Term echo unreadable::${verdict.note}`);
    console.log(`• ${verdict.note}`);
  } else {
    const label = CFG.TERM_LABEL;
    if (!label) throw new Error('set CP_TERM, or CP_TERM_LABEL so the term code can be resolved');
    console.log(`• Resolving "${label}" — candidates ${termCandidates(label).join(', ')}`);
    const found = await resolveTerm(termIO, label);
    CFG.TERM = found.code;
    console.log(`\n==> TERM CODE for ${label} is ${found.code}  (page says ${JSON.stringify(found.echo.slice(0, 60))}, ${found.subjects} subjects)`);
    console.log(`    Write it into seats/registrar-calendar.json as this term's term_code, with a note saying how it was confirmed.`);
    if (process.env.GITHUB_STEP_SUMMARY) {
      const { appendFileSync } = await import('node:fs');
      appendFileSync(process.env.GITHUB_STEP_SUMMARY, `### Term discovery\n\n**${label} = \`${found.code}\`** — page echo: \`${found.echo.slice(0, 60)}\`, ${found.subjects} subjects.\n\nAdd to \`seats/registrar-calendar.json\`.\n`);
    }
    if (CFG.DISCOVER_ONLY) { await browser.close(); return; }
  }
  console.log(`• After setup — institution="${await readField(page, 'CLASS_SRCH_WRK2_INSTITUTION')}" term="${await readField(page, 'SLO_SS_DERIVED_STRM')}"`);

  // ---- Cal Poly's hard 300-section search cap -------------------------------------------
  // PeopleSoft refuses outright to run a search whose result set would exceed 300 sections:
  //   "Your search will exceed the maximum limit of 300 sections. Specify additional
  //    criteria to continue."
  // It returns ZERO rows in that case. A whole-subject sweep of a big subject (CSC) trips
  // this every single day, which is exactly why that lane always reported 0 sections and
  // exited 2 while every smaller lane succeeded.
  //
  // The form allows exactly ONE course-number criterion (operators: contains / greater than
  // or equal to / is exactly / less than or equal to — there is no "between"), so we slice
  // an over-limit subject into course-number bands and union the results. Bands are
  // expressed as a single operator each, which is all the form can hold:
  //   <= 2999   (lower division + most upper division)
  //   >= 3000   (the rest)
  // and, if a half is STILL over the cap, it is split again around a finer boundary. Every
  // pass is de-duplicated by class number, so overlapping bands are harmless.
  const CAP_SPLITS = [3000, 2000, 4000, 1000, 5000];   // boundaries to try, most useful first

  // Return to the search FORM after a results page so another search can be run.
  async function backToForm() {
    const modify = page.locator('input[value="Modify Search"], a:has-text("Modify Search")').first();
    if (await modify.count()) await postback(page, () => modify.click());
    await page.evaluate(PAGE_HELPERS);
  }

  // Set the course-number criterion. Cal Poly requires at least 2 search criteria; subject is
  // one and this is the second, so it is always set — the operator/value is what we vary to
  // slice a subject that would otherwise blow the 300 cap.
  //   op: 'G' = greater than or equal to · 'L' = less than or equal to · 'E' = is exactly
  async function setCourseNum(op, value) {
    for (let a = 1; a <= 3; a++) {
      const ok = await page.evaluate(({ op, value }) => {
        const sel = document.querySelector('select[id^="SSR_CLSRCH_WRK_SSR_EXACT_MATCH1"]');
        const num = document.querySelector('input[id^="SSR_CLSRCH_WRK_CATALOG_NBR"]');
        if (!sel || !num) return null;
        // Resolve the operator by its VISIBLE LABEL first, falling back to the option value.
        // Only the 'G' value is proven against the live form (it's what the daily run has always
        // used); the others are PeopleSoft convention, so we never depend on guessing them —
        // the labels below are copied verbatim from the real Cal Poly dropdown.
        const WANT = { G: /greater than or equal/i, L: /less than or equal/i, E: /is exactly/i, C: /contains/i }[op];
        let chosen = null;
        if (WANT) for (const o of sel.options) { if (WANT.test(o.textContent || '')) { chosen = o.value; break; } }
        if (chosen == null) chosen = op;                  // fall back to the raw value
        sel.value = chosen;
        sel.dispatchEvent(new Event('change', { bubbles: true }));
        num.value = String(value);
        num.dispatchEvent(new Event('change', { bubbles: true }));
        return sel.value === chosen && String(num.value) === String(value);
      }, { op, value });
      if (ok) return op + (op === 'G' ? '>=' : op === 'L' ? '<=' : '=') + value;
      if (ok === null) return 'missing';
      await sleep(400);
    }
    return 'retry';
  }

  // Run ONE search for a subject with one course-number band. Returns the parsed rows plus
  // whether the server refused the search for exceeding its 300-section cap.
  async function searchOnce(subj, op, num, isFirstSearch) {
    if (!isFirstSearch) await backToForm();
    await page.waitForFunction(() => {
      const s = document.querySelector('select[id^="SSR_CLSRCH_WRK_SUBJECT_SRCH"]');
      return s && s.options.length > 1;
    }, null, { timeout: 20000 }).catch(() => {});
    await setField(page, 'SSR_CLSRCH_WRK_SUBJECT_SRCH', subj, 'subject');
    const criterionState = await setCourseNum(op, num);

    // Turn OFF "Show Open Classes Only" so FULL / WAITLISTED / CLOSED sections are included.
    //
    // THIS LEAKED, AND THE DATA PROVED IT (2026-08-25). Term 2268 in course_seats held 1,090
    // sections with 0 seats available — so the uncheck plainly worked for most subjects. But
    // HIST came back 41 sections, 100% status "Open", ZERO full; same for ANT, SPAN and GEOG,
    // and ECON had exactly one non-Open row in the entire subject. HIST 2202 — two sections,
    // 0/120 open, 91 deep on the waitlist on Cal Poly's own class search — was simply absent
    // from the app. Per-subject, not global: the uncheck is racing something.
    //
    // Two causes, both handled below rather than guessed between:
    //   1. setCourseNum() dispatches a `change`, and PeopleSoft answers some field changes
    //      with a postback that re-renders the form. If that lands AFTER we uncheck, the
    //      freshly rendered checkbox is back to its default (checked) when Search fires.
    //      Fix: settle first, then uncheck, then VERIFY, and redo if it came back checked.
    //   2. PeopleSoft submits the paired hidden "$chk" input, not the visible checkbox. The
    //      old comment dismissed that input as a decoy; it is what the server reads. Clicking
    //      the visible box normally syncs it via PeopleSoft's own JS — but only if that JS
    //      ran, which after a re-render it may not have. Fix: set the hidden field too.
    const openOnlyState = await setOpenOnlyOff(page);
    await postback(page, () => page.evaluate(() => { const b = window.__pf_find('CLASS_SRCH_WRK2_SSR_PB_CLASS_SRCH'); if (b) b.click(); }));
    await dismissOversize(page);

    // Wait for results OR a message, up to 30s.
    await page.waitForFunction(() =>
      !!document.querySelector('a[id^="MTG_CLASS_NBR$"]') ||
      /no classes found|search returns no results|did not return any|exceed the maximum limit|is a required field/i.test(document.body.innerText),
      null, { timeout: 30000 }).catch(() => {});

    const outcome = await searchOutcome(page);
    const list = await parseList(page, subj);
    const diag = await page.evaluate(() => ({
      rawLinks: document.querySelectorAll('a[id^="MTG_CLASS_NBR$"]').length,
      capNote: /(only the first|maximum number|more than \d+|has been limited|limited to \d+|exceeds the maximum|exceed the maximum limit)/i.test(document.body.innerText || ''),
    }));
    return { list, outcome, diag, criterionState, openOnlyState, overLimit: outcome.msg === 'over-limit' };
  }

  /**
   * Fetch seat counts for one band's rows, against the result page that produced them.
   *
   * THE GUARD IS THE POINT. `list[i]` is reached by clicking `MTG_CLASS_NBR$i`, so the index is
   * the only key tying a row to its section — and it is only valid on the page that emitted the
   * list. Enriching a list against a different page does not fail: it writes real numbers onto
   * the wrong sections, upserts them clean, and the app shows a student a seat count belonging to
   * a class they are not looking at. Counting the links first turns that from a silent corruption
   * into a refusal with a name.
   *
   * When it refuses, rows are left WITHOUT counts rather than with wrong ones, and they are
   * upserted list-only so the numbers already in the table survive untouched.
   */
  async function enrichLive(list, label) {
    if (!CFG.FETCH_DETAILS || !list.length) return;
    const links = await page.evaluate(() => document.querySelectorAll('a[id^="MTG_CLASS_NBR$"]').length);
    const v = indexableAgainstPage(list.length, links);
    if (!v.ok) {
      console.warn(`    !! ${label}: REFUSING to fetch seat counts — ${v.reason}`);
      await dumpDiag(page, label.toLowerCase().replace(/[^a-z0-9]+/g, '-') + '-indexmismatch');
      return;
    }
    let missing = 0;
    for (let i = 0; i < list.length; i++) {
      const c = await fetchDetail(page, i);
      if (c && c.missing) { missing++; continue; }
      Object.assign(list[i], c);
      list[i]._enriched = true;
      if (!String(list[i].days || '').trim() && c.days_detail) list[i].days = c.days_detail;  // detail-page fallback
      if (i === 0) console.log(`    ↳ sample: ${list[0].course_code} — seats cap=${list[0].capacity} avail=${list[0].available} · time="${list[0].days || 'none'}" · instr="${list[0].instructor || 'none'}" · mode="${list[0].instruction_mode || 'NOT FOUND'}" · loc="${list[0].location || 'none'}"`);
      if ((i + 1) % 25 === 0) console.log(`    …${i + 1}/${list.length} (${label})`);
    }
    /* Unreachable if the guard above held — which is exactly why it is reported rather than
       ignored. It would mean the page changed under the loop. */
    if (missing) console.warn(`    !! ${label}: ${missing} of ${list.length} rows had no result link mid-loop — the page changed while counts were being fetched.`);
  }

  const all = [];
  let searchesRun = 0;
  for (let s = 0; s < CFG.SUBJECTS.length; s++) {
    const subj = CFG.SUBJECTS[s];
    /* Bands that finished BEFORE an error, so a subject that dies half way still writes what it
       already has. It holds whole bands, each already enriched against its own page — partial
       data, never mismatched data. */
    const salvage = [];
    try {
      /* ENRICH EACH BAND WHILE ITS OWN RESULT PAGE IS LOADED.
         The list index IS the DOM id suffix — `list[i]` is reached by clicking
         `MTG_CLASS_NBR$i` — so a list and a page belong together and nothing else ties a row to
         its link. The previous version concatenated both bands' lists and then walked the
         combined list against whichever page happened to be loaded last, which wrote the high
         band's seat counts onto the low band's rows and then spent twelve seconds per orphaned
         index discovering there was nothing to click. See bands.mjs for the full trace.
         So: search, enrich, merge — in that order, per band, never across them. */
      let r = await searchOnce(subj, 'G', 0, searchesRun++ === 0);
      const bandLists = [];
      let plan = bandPlan(r.overLimit, []);

      if (!r.overLimit) {
        /* The common case, and the cheap one: one search, and its page is live right now. */
        await enrichLive(r.list, subj);
        bandLists.push(r.list); salvage.push(r.list);
      } else {
        /* Over Cal Poly's 300 cap. Probe for a boundary list-only first — enriching a band we
           might discard because its partner is still over the cap would be minutes wasted. */
        const attempts = [];
        for (const boundary of CAP_SPLITS) {
          const lowHalf  = await searchOnce(subj, 'L', boundary - 1, false); searchesRun++;
          const highHalf = await searchOnce(subj, 'G', boundary,     false); searchesRun++;
          attempts.push({ boundary, lowOverLimit: lowHalf.overLimit, highOverLimit: highHalf.overLimit });
          if (!lowHalf.overLimit && !highHalf.overLimit) {
            /* The HIGH band's page is the one loaded — it was the last search — so enrich it
               here rather than paying for the same search twice. */
            await enrichLive(highHalf.list, `${subj} >=${boundary}`);
            bandLists.push(highHalf.list); salvage.push(highHalf.list);
            r = highHalf;                                   // a real outcome, for the log line
            break;
          }
          console.log(`    · ${subj}: split at ${boundary} still over the 300 cap (low=${lowHalf.overLimit ? 'over' : lowHalf.list.length}, high=${highHalf.overLimit ? 'over' : highHalf.list.length}) — trying a finer boundary`);
        }
        plan = bandPlan(true, attempts);
        if (!plan.bands) {
          // Never silently under-report: say so loudly and dump what the runner saw.
          console.log(`  ${subj}: STILL over Cal Poly's 300-section cap after every split — this subject needs a finer band list (CAP_SPLITS).`);
          await dumpDiag(page, subj.toLowerCase() + '-overlimit');
        } else {
          /* Now the LOW band, searched fresh so its own page is the one being indexed. */
          const lo = plan.bands.find(x => x.op === 'L');
          const loRes = await searchOnce(subj, lo.op, lo.num, false); searchesRun++;
          await enrichLive(loRes.list, `${subj} ${lo.label}`);
          bandLists.push(loRes.list); salvage.push(loRes.list);
        }
      }

      const bandsUsed = plan.label;
      /* Merge only after every band has its own numbers on it. Bands are disjoint by
         construction, but a section that appeared twice would make Postgres reject the whole
         lane's upsert, so the dedupe stays. */
      const list = mergeBands(bandLists);

      const codeSet = new Set(list.map(x => x.course_code).filter(Boolean));
      const blanks = list.filter(x => !x.course_code).length;
      const statusMix = list.reduce((m, x) => { const st = statusBadge(x.status_raw) || 'null'; m[st] = (m[st] || 0) + 1; return m; }, {});
      console.log(`  ${subj}: ${list.length} sections / ${codeSet.size} courses  (bands=${bandsUsed}, crit=${r.criterionState}, open-only=${r.openOnlyState}, statuses=${JSON.stringify(statusMix)}${blanks ? `, ${blanks} BLANK-code` : ''}${r.diag.capNote ? ', CAP-NOTE!' : ''}, msg=${r.outcome.msg || 'none'})${CFG.FETCH_DETAILS && list.length ? ' — fetching counts…' : ''}`);
      if (list.length === 0) await dumpDiag(page, subj.toLowerCase());

      /* INTEGRITY CHECK — the one that would have caught this the day it started.
         A subject of any size that comes back 100% "Open" is not a subject where nothing is
         full; it is a subject where the open-only filter leaked. Real ones are mixed: across
         term 2268 about a quarter of all sections are Waitlist or Closed. HIST returned 41
         sections, every single one Open, and nothing anywhere in the log said so — the run
         looked completely healthy while the app was silently missing every full class in the
         subject, which are exactly the ones a student needs a waitlist position for.
         This does not throw: a partial subject is still worth writing. It makes the failure
         VISIBLE and names the fix, which is what a nightly log is for. */
      const nonOpen = list.filter(x => { const st = statusBadge(x.status_raw); return st && st !== 'Open'; }).length;
      if (list.length >= 8 && nonOpen === 0) {
        console.warn(`    !! ${subj}: ${list.length} sections and NOT ONE is full or waitlisted — "Show Open Classes Only" almost certainly leaked for this subject (open-only=${r.openOnlyState}). Every full section is missing from this lane. Re-run this subject.`);
        await dumpDiag(page, subj.toLowerCase() + '-openonly-leak');
      }
      if (r.openOnlyState === 'STUCK-ON') {
        console.warn(`    !! ${subj}: could not clear "Show Open Classes Only" after 4 attempts — this lane's data is open-classes-only and INCOMPLETE.`);
      }

      all.push(...list);
    } catch (e) {
      console.error(`  ${subj}: ERROR — ${e.message.split('\n')[0]}`);
      // Keep whatever this subject already produced instead of throwing the whole lane away.
      const salvaged = mergeBands(salvage).filter(x => x && x.class_nbr);
      if (salvaged.length) {
        salvaged.forEach(x => { x.status = statusBadge(x.status_raw); x.term = CFG.TERM; x.updated_at = new Date().toISOString(); });
        all.push(...salvaged);
        console.log(`    · ${subj}: kept ${salvaged.length} sections collected before the error.`);
      }
      await dumpDiag(page, subj.toLowerCase() + '-error');
    }
  }
  await browser.close();

  await writeFile('seats.json', JSON.stringify({ term: CFG.TERM, generated_at: new Date().toISOString(), count: all.length, sections: all }, null, 2));
  console.log(`• Wrote seats.json (${all.length} sections).`);
  await upsertSupabase(all);
  // Prereqs/description are STATIC per course, so collapse to one row per course_code (first
  // section that has the text wins) and write them to their own table. This is wrapped so a
  // missing table or any error here can NEVER affect the seat upsert above.
  const catByCourse = new Map();
  for (const r of all) {
    if (!r.course_code) continue;
    const existing = catByCourse.get(r.course_code);
    if (!existing || (!existing.prereqs && r.prereq) || (!existing.description && r.description)) {
      catByCourse.set(r.course_code, {
        course_code: r.course_code, subject: r.subject, title: r.title,
        prereqs: r.prereq || (existing && existing.prereqs) || null,
        description: r.description || (existing && existing.description) || null,
        updated_at: r.updated_at,
      });
    }
  }
  await upsertCatalog([...catByCourse.values()]);
  if (!all.length) { console.log('\n⚠  Zero sections — see the uploaded diag-*.png / diag-*.txt artifact to see what the runner saw.'); process.exit(2); }
}

// Write per-course prerequisites + description to a SEPARATE table (course_catalog). Fully
// isolated: if the table doesn't exist yet or the request fails, we log and return WITHOUT
// throwing, so the critical seat pipeline is never impacted. Create the table once (SQL in the
// deploy notes) to start collecting this data.
async function upsertCatalog(rows) {
  if (!CFG.SUPABASE_URL || !CFG.SUPABASE_SERVICE_KEY) return;
  const withText = rows.filter(r => r.prereqs || r.description);
  if (!withText.length) { console.log('• No prereq/description text captured this lane.'); return; }
  const url = `${CFG.SUPABASE_URL.replace(/\/$/, '')}/rest/v1/course_catalog?on_conflict=course_code`;
  try {
    for (let i = 0; i < withText.length; i += 500) {
      const res = await fetch(url, {
        method: 'POST',
        headers: { apikey: CFG.SUPABASE_SERVICE_KEY, Authorization: `Bearer ${CFG.SUPABASE_SERVICE_KEY}`, 'Content-Type': 'application/json', Prefer: 'resolution=merge-duplicates,return=minimal' },
        body: JSON.stringify(withText.slice(i, i + 500)),
      });
      if (!res.ok) {
        console.log(`• Prereq/catalog upsert skipped (non-fatal): HTTP ${res.status} — ${(await res.text()).slice(0, 160)}  [create the course_catalog table to enable]`);
        return;
      }
    }
    console.log(`• Upserted ${withText.length} course prereq/catalog rows.`);
  } catch (e) {
    console.log('• Prereq/catalog upsert error (non-fatal):', e.message.split('\n')[0]);
  }
}

async function upsertSupabase(rows) {
  if (!CFG.SUPABASE_URL || !CFG.SUPABASE_SERVICE_KEY) { console.log('• Supabase not configured — seats.json written, DB upsert skipped.'); return; }
  const url = `${CFG.SUPABASE_URL.replace(/\/$/, '')}/rest/v1/course_seats?on_conflict=term,class_nbr`;
  /* Shaped in rows.mjs so it can be tested without a browser — see the note there on why the
     seat-count columns are omitted rather than nulled when details are off.
     TWO BATCHES, NOT ONE, WHEN COUNTS ARE ON. A band whose page-index guard refused (see
     enrichLive) has rows with no counts, and sending those in the same batch as the enriched
     ones would write NULL over numbers that are still perfectly good — the same data loss the
     discovery-pull fix exists to prevent, arriving by a different door. PostgREST needs a uniform
     key set per request, so they go as their own list-only batch and their existing counts are
     left alone. */
  const wantCounts = CFG.FETCH_DETAILS;
  if (!wantCounts) console.log('• Discovery pull (CP_FETCH_DETAILS=0) — seat-count columns are LEFT UNTOUCHED, not overwritten.');
  const groups = wantCounts
    ? [
        { rows: rows.filter(r => r._enriched), withCounts: true,  tag: 'with counts' },
        { rows: rows.filter(r => !r._enriched), withCounts: false, tag: 'list-only (counts left untouched)' },
      ].filter(g => g.rows.length)
    : [{ rows, withCounts: false, tag: 'list-only' }];
  if (wantCounts && groups.length > 1) {
    console.warn(`• ${groups[1].rows.length} row(s) were never enriched — upserting them list-only so their existing seat counts survive.`);
  }
  for (const g of groups) await upsertGroup(url, g.rows, g.withCounts, g.tag);
}

async function upsertGroup(url, rows, withCounts, tag) {
  const clean = buildUpsertRows(rows, { withCounts });
  // Dedupe by (term, class_nbr): a cross-listed course can appear under two
  // subjects in the same lane with the same class number. Postgres rejects an
  // upsert that affects the same row twice in one command ("ON CONFLICT DO
  // UPDATE command cannot affect row a second time"), which would reject the
  // whole lane's write. Collapse to one row per class number (last wins).
  const deduped = dedupeByClassNbr(clean);
  if (deduped.length !== clean.length) console.log(`• Collapsed ${clean.length - deduped.length} cross-listed duplicate class number(s) before upsert.`);
  /* The three new columns may not exist yet. PostgREST rejects the WHOLE batch with a 400
     naming the unknown column, which would take the entire seat feed down — the one failure
     mode this scraper must never have. Detect that specific error once and fall back to the
     original column set, so the order you apply the SQL in cannot break the nightly run. */
  const NEW_COLS = ['instruction_mode', 'location', 'room'];
  let dropNew = false;
  const strip = rows => rows.map(r => { const c = { ...r }; NEW_COLS.forEach(k => delete c[k]); return c; });
  const send = async batch => fetch(url, {
    method: 'POST',
    headers: { apikey: CFG.SUPABASE_SERVICE_KEY, Authorization: `Bearer ${CFG.SUPABASE_SERVICE_KEY}`, 'Content-Type': 'application/json', Prefer: 'resolution=merge-duplicates,return=minimal' },
    body: JSON.stringify(batch),
  });
  for (let i = 0; i < deduped.length; i += 500) {
    const batch = deduped.slice(i, i + 500);
    let res = await send(dropNew ? strip(batch) : batch);
    if (!res.ok && !dropNew) {
      const body = (await res.text()).slice(0, 400);
      if (/PGRST204|could not find|column .* does not exist|schema cache/i.test(body) &&
          NEW_COLS.some(k => body.includes(k))) {
        console.log('• course_seats has no instruction_mode/location/room column yet — upserting without them.');
        console.log('  Run: alter table public.course_seats add column if not exists instruction_mode text, add column if not exists location text, add column if not exists room text;');
        dropNew = true;
        res = await send(strip(batch));
      } else {
        throw new Error(`Supabase upsert failed: HTTP ${res.status}\n${body}`);
      }
    }
    if (!res.ok) throw new Error(`Supabase upsert failed: HTTP ${res.status}\n${(await res.text()).slice(0, 300)}`);
  }
  const withMode = deduped.filter(r => r.instruction_mode).length;
  console.log(`• Upserted ${deduped.length} rows into Supabase (${tag}).` +
    (dropNew ? ' (instruction_mode/location/room skipped — column missing)'
             : ` ${withMode} of them carry an instruction mode.`));
}

run().catch(e => { console.error('FATAL:', e.message); process.exit(1); });
