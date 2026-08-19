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

const CFG = {
  URL: process.env.CP_URL || 'https://cmsweb.pscs.calpoly.edu/psc/CSLOPRD/EMPLOYEE/SA/c/COMMUNITY_ACCESS.CLASS_SEARCH.GBL',
  INSTITUTION: process.env.CP_INSTITUTION || 'SLCMP',
  TERM: process.env.CP_TERM || '2268',                       // Fall Semester 2026
  SUBJECTS: (process.env.CP_SUBJECTS || 'BUS').split(',').map(s => s.trim()).filter(Boolean),
  FETCH_DETAILS: process.env.CP_FETCH_DETAILS !== '0',        // ON by default (seat counts)
  HEADLESS: process.env.CP_HEADLESS !== '0',
  SUPABASE_URL: process.env.SUPABASE_URL || '',
  SUPABASE_SERVICE_KEY: process.env.SUPABASE_SERVICE_KEY || '',
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
  await page.evaluate(i => { const a = document.getElementById('MTG_CLASS_NBR$' + i); if (a) a.click(); }, index);
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
    const prereq = grab(/Enrollment Requirements/i, /(Class Availability|Class Capacity|Description|Textbook|View Search Results)/i).slice(0, 700);
    const description = grab(/\bDescription\b/i, /(Textbook\s*\/?\s*Other|Special Instructions|Course Materials|View Search Results)/i).slice(0, 1500);
    return {
      capacity: g('Class Capacity') ?? g('Enrollment Capacity'), enrolled: g('Enrollment Total'),
      available: g('Available Seats'), waitlist_capacity: g('Wait List Capacity'), waitlist_total: g('Wait List Total'),
      days_detail, prereq, description,
    };
  });
  await page.evaluate(() => { const b = document.getElementById('CLASS_SRCH_WRK2_SSR_PB_BACK'); if (b) b.click(); });
  await page.waitForFunction(() => document.getElementById('MTG_CLASS_NBR$0') && !document.getElementById('CLASS_SRCH_WRK2_SSR_PB_BACK'), null, { timeout: 12000 }).catch(() => {});
  await sleep(120);
  return c;
}

const statusBadge = s => { s = (s || '').toLowerCase(); return s.includes('wait') ? 'Waitlist' : s.includes('open') ? 'Open' : s.includes('clos') ? 'Closed' : null; };

async function run() {
  console.log(`Professify seat scraper v2 — term ${CFG.TERM}, subjects [${CFG.SUBJECTS.join(', ')}], counts=${CFG.FETCH_DETAILS ? 'on' : 'off'}, headless=${CFG.HEADLESS}`);
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
  await setField(page, 'SLO_SS_DERIVED_STRM', CFG.TERM, 'term');                        // validates term
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
    // The real checkbox id has a "$N" suffix (SSR_CLSRCH_WRK_SSR_OPEN_ONLY$4) with decoy
    // siblings (a hidden "$chk" input and a "_LBL" label) — target the actual checkbox input
    // directly and uncheck it. Client-side filter, applied at Search time.
    const openOnlyState = await page.evaluate(() => {
      const o = document.querySelector('input[type="checkbox"][id^="SSR_CLSRCH_WRK_SSR_OPEN_ONLY$"]');
      if (!o) return 'absent';
      const before = o.checked ? 'on' : 'off';
      if (o.checked) o.click();                                   // native click unchecks
      if (o.checked) { o.checked = false; o.dispatchEvent(new Event('change', { bubbles: true })); }
      return before + '->' + (o.checked ? 'on' : 'off');
    });
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

  const all = [];
  let searchesRun = 0;
  for (let s = 0; s < CFG.SUBJECTS.length; s++) {
    const subj = CFG.SUBJECTS[s];
    const collected = [];          // survives an error mid-subject, so partial data is never lost
    try {
      // Pass 1: the whole subject in one search (what every subject under the cap needs).
      let r = await searchOnce(subj, 'G', 0, searchesRun++ === 0);
      let bandsUsed = 'all';

      if (r.overLimit) {
        // Over Cal Poly's 300 cap — slice into course-number bands and union them.
        let done = false;
        for (const boundary of CAP_SPLITS) {
          const lowHalf  = await searchOnce(subj, 'L', boundary - 1, false); searchesRun++;
          const highHalf = await searchOnce(subj, 'G', boundary,     false); searchesRun++;
          if (!lowHalf.overLimit && !highHalf.overLimit) {
            collected.push(...lowHalf.list, ...highHalf.list);
            bandsUsed = `<=${boundary - 1} + >=${boundary}`;
            r = highHalf;                                   // keep a real outcome for logging
            done = true;
            break;
          }
          console.log(`    · ${subj}: split at ${boundary} still over the 300 cap (low=${lowHalf.overLimit ? 'over' : lowHalf.list.length}, high=${highHalf.overLimit ? 'over' : highHalf.list.length}) — trying a finer boundary`);
        }
        if (!done) {
          // Never silently under-report: say so loudly and dump what the runner saw.
          console.log(`  ${subj}: STILL over Cal Poly's 300-section cap after every split — this subject needs a finer band list (CAP_SPLITS).`);
          await dumpDiag(page, subj.toLowerCase() + '-overlimit');
        }
      } else {
        collected.push(...r.list);
      }

      // De-duplicate by class number: bands can overlap, and the same section must never be
      // counted twice.
      const seenNbr = new Set();
      const list = collected.filter(x => {
        const k = String(x.class_nbr || '') + '|' + String(x.section || '') + '|' + String(x.course_code || '');
        if (seenNbr.has(k)) return false; seenNbr.add(k); return true;
      });

      const codeSet = new Set(list.map(x => x.course_code).filter(Boolean));
      const blanks = list.filter(x => !x.course_code).length;
      const statusMix = list.reduce((m, x) => { const st = statusBadge(x.status_raw) || 'null'; m[st] = (m[st] || 0) + 1; return m; }, {});
      console.log(`  ${subj}: ${list.length} sections / ${codeSet.size} courses  (bands=${bandsUsed}, crit=${r.criterionState}, open-only=${r.openOnlyState}, statuses=${JSON.stringify(statusMix)}${blanks ? `, ${blanks} BLANK-code` : ''}${r.diag.capNote ? ', CAP-NOTE!' : ''}, msg=${r.outcome.msg || 'none'})${CFG.FETCH_DETAILS && list.length ? ' — fetching counts…' : ''}`);
      if (list.length === 0) await dumpDiag(page, subj.toLowerCase());

      if (CFG.FETCH_DETAILS) {
        for (let i = 0; i < list.length; i++) {
          const c = await fetchDetail(page, i);
          Object.assign(list[i], c);
          if (!String(list[i].days || '').trim() && c.days_detail) list[i].days = c.days_detail;  // detail-page fallback
          if (i === 0) console.log(`    ↳ sample: ${list[0].course_code} — seats cap=${list[0].capacity} avail=${list[0].available} · time="${list[0].days || 'none'}" · instr="${list[0].instructor || 'none'}"`);
          if ((i + 1) % 25 === 0) console.log(`    …${i + 1}/${list.length}`);
        }
      }
      list.forEach(x => { x.status = statusBadge(x.status_raw); x.term = CFG.TERM; x.updated_at = new Date().toISOString(); });
      all.push(...list);
    } catch (e) {
      console.error(`  ${subj}: ERROR — ${e.message.split('\n')[0]}`);
      // Keep whatever this subject already produced instead of throwing the whole lane away.
      const salvaged = collected.filter(x => x && x.class_nbr);
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
  const clean = rows.filter(r => r.class_nbr).map(r => ({
    term: r.term, class_nbr: r.class_nbr, subject: r.subject, course_code: r.course_code, title: r.title,
    section: r.section, instructor: r.instructor, days: r.days, dates: r.dates, status: r.status,
    capacity: r.capacity ?? null, enrolled: r.enrolled ?? null, available: r.available ?? null,
    waitlist_total: r.waitlist_total ?? null, waitlist_capacity: r.waitlist_capacity ?? null, updated_at: r.updated_at,
  }));
  // Dedupe by (term, class_nbr): a cross-listed course can appear under two
  // subjects in the same lane with the same class number. Postgres rejects an
  // upsert that affects the same row twice in one command ("ON CONFLICT DO
  // UPDATE command cannot affect row a second time"), which would reject the
  // whole lane's write. Collapse to one row per class number (last wins).
  const byKey = new Map();
  for (const r of clean) byKey.set(r.term + '|' + r.class_nbr, r);
  const deduped = [...byKey.values()];
  if (deduped.length !== clean.length) console.log(`• Collapsed ${clean.length - deduped.length} cross-listed duplicate class number(s) before upsert.`);
  for (let i = 0; i < deduped.length; i += 500) {
    const res = await fetch(url, {
      method: 'POST',
      headers: { apikey: CFG.SUPABASE_SERVICE_KEY, Authorization: `Bearer ${CFG.SUPABASE_SERVICE_KEY}`, 'Content-Type': 'application/json', Prefer: 'resolution=merge-duplicates,return=minimal' },
      body: JSON.stringify(deduped.slice(i, i + 500)),
    });
    if (!res.ok) throw new Error(`Supabase upsert failed: HTTP ${res.status}\n${(await res.text()).slice(0, 300)}`);
  }
  console.log(`• Upserted ${deduped.length} rows into Supabase.`);
}

run().catch(e => { console.error('FATAL:', e.message); process.exit(1); });
