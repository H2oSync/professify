#!/usr/bin/env node
/**
 * Professify — what does each way of walking the class search actually COST?
 * =========================================================================
 *
 * The whole speed argument rests on one number nobody has measured properly: what the
 * "View Search Results" button costs. Every seat count needs a round trip out to a section's
 * detail page and back, and the way back re-sends the ENTIRE current result set. Search a whole
 * subject and that is 486 sections of HTML, 486 times over, to return to a list the client is
 * already holding.
 *
 * If that is true, the fix is not a faster client. It is a SMALLER RESULT SET: search one course
 * at a time and the trip back costs what four sections weigh instead of four hundred. Same number
 * of requests, a fraction of the bytes.
 *
 * "If that is true" is the point of this file. It walks the same subject three ways against the
 * live site and reports real bytes and real milliseconds for each step:
 *
 *   A  whole subject   search all -> detail -> View Search Results      (what runs today)
 *   B  one course      search E=<nbr> -> detail -> View Search Results  (the proposal)
 *   C  no return       search E=<nbr> -> detail -> Start a New Search   (skip the list entirely)
 *
 * C is the interesting one. If leaving via the search form is cheaper than returning to a result
 * list — and the form is a few KB where the list is over a megabyte — then the cheapest loop
 * never goes back to a list at all.
 *
 * AND D, WHICH IS A DIFFERENT QUESTION ENTIRELY.
 *
 * A/B/C ask how cheaply we can collect EXACT COUNTS for every section. D asks how cheaply we can
 * find out WHICH SECTIONS CHANGED, so the expensive walk only has to visit those. The planned
 * architecture (claude/seat-refresh-tiers) runs a transition sweep every few minutes and a full
 * reconciliation twice a day, and the whole economics of that first tier rest on one unmeasured
 * number: how big is a results page with "Show Open Classes Only" TURNED ON?
 *
 *   D  transition sweep   whole subject, open-only OFF  vs  open-only ON
 *
 * The bet is that the open-only response is a fraction of the full one — it contains only the
 * open sections — and that a set-difference between two consecutive sweeps yields exactly the
 * Closed->Open and Open->Closed transitions. If it does, 84 of those requests cover the whole
 * campus and can run every few minutes. If it comes back near the full 1.4 MB, an 84-subject
 * sweep is ~118 MB a cycle and the tier needs rethinking.
 *
 * D also records the open sections' class numbers. Run the bench twice an hour apart during
 * add/drop and diff those two lists: that is the transition detector, validated on real data,
 * before a line of it is built.
 *
 * It upserts NOTHING and changes nothing. Run it from the workflow (mode: bench). Its output is
 * evidence for a decision, and until it has run, the decision is not made.
 */
import { chromium } from 'playwright';
import { writeFile } from 'node:fs/promises';

const TERM = process.env.CP_TERM || '2268';
const SUBJECT = process.env.CP_BENCH_SUBJECT || 'CSC';
const URL = process.env.CP_URL || 'https://cmsweb.pscs.calpoly.edu/psc/CSLOPRD/EMPLOYEE/SA/c/COMMUNITY_ACCESS.CLASS_SEARCH.GBL';
const sleep = ms => new Promise(r => setTimeout(r, ms));

const results = [];
let step = null;          // the label the next .GBL response is attributed to

async function main() {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newContext({ viewport: { width: 1366, height: 900 }, locale: 'en-US' }).then(c => c.newPage());
  page.on('dialog', d => d.dismiss().catch(() => {}));

  /* Bytes measured off the wire, not guessed from the DOM. A partial-refresh response is XML
     with the HTML inside CDATA, so the DOM after the fact is a poor proxy for what crossed the
     network — which is the thing we are trying to make smaller. */
  page.on('response', async res => {
    if (!res.url().includes('CLASS_SEARCH')) return;
    if (res.request().method() !== 'POST' && !res.url().endsWith('.GBL')) return;
    let bytes = null;
    try { bytes = (await res.body()).length; } catch { /* body already gone */ }
    if (step) results.push({ step: step.name, bytes, ms: Date.now() - step.t0, status: res.status() });
  });

  const timed = async (name, fn) => {
    step = { name, t0: Date.now() };
    await fn();
    await sleep(250);
    step = null;
  };

  const find = p => page.evaluate(x => {
    const el = document.getElementById(x) || document.querySelector('[id^="' + x + '"]');
    return el ? el.id : null;
  }, p);

  const set = async (prefix, value) => {
    const id = await find(prefix);
    if (!id) throw new Error('no field ' + prefix);
    await page.evaluate(({ id, value }) => {
      const el = document.getElementById(id);
      el.value = value;
      el.dispatchEvent(new Event('change', { bubbles: true }));
    }, { id, value });
    await sleep(900);
  };

  const clickById = prefix => page.evaluate(x => {
    const el = document.getElementById(x) || document.querySelector('[id^="' + x + '"]');
    if (el) el.click();
    return !!el;
  }, prefix);

  const sectionCount = () => page.evaluate(() => document.querySelectorAll('a[id^="MTG_CLASS_NBR$"]').length);
  const courseNumbers = () => page.evaluate(() =>
    [...new Set([...document.querySelectorAll('*')]
      .map(e => (e.textContent || '').match(/^\s*[A-Z]{2,5}\s+(\d{3,4})\s*[-–]/))
      .filter(Boolean).map(m => m[1]))].slice(0, 40));

  await page.goto(URL, { waitUntil: 'domcontentloaded' });
  await page.waitForSelector('[id^="CLASS_SRCH_WRK2_INSTITUTION"]', { timeout: 45000 });
  await set('CLASS_SRCH_WRK2_INSTITUTION', 'SLCMP');
  await set('SLO_SS_DERIVED_STRM', TERM);
  await page.waitForFunction(() => {
    const s = document.querySelector('select[id^="SSR_CLSRCH_WRK_SUBJECT_SRCH"]');
    return s && s.options.length > 1;
  }, null, { timeout: 20000 });

  /* "Show Open Classes Only", set in either direction and VERIFIED.
     Two things learned the hard way in scrape-seats.mjs and repeated here, because a bench that
     silently measures the wrong result set is worse than no bench:
       · the hidden `$chk` partner is what actually rides the form post, not the visible box, and
         after a re-render PeopleSoft's own JS may not have synced them;
       · a postback from the previous field edit can land AFTER the click and restore the default. */
  const setOpenOnly = async (want) => {
    for (let attempt = 1; attempt <= 4; attempt++) {
      await page.waitForLoadState('networkidle', { timeout: 4000 }).catch(() => {});
      const st = await page.evaluate((want) => {
        const o = document.querySelector('input[type="checkbox"][id^="SSR_CLSRCH_WRK_SSR_OPEN_ONLY$"]');
        if (!o) return { absent: true };
        if (o.checked !== want) o.click();
        if (o.checked !== want) { o.checked = want; o.dispatchEvent(new Event('change', { bubbles: true })); }
        const hidden = document.querySelector('input[id^="SSR_CLSRCH_WRK_SSR_OPEN_ONLY$"][type="hidden"]')
                    || document.getElementById(o.id + '$chk')
                    || document.querySelector('input[name="' + o.name + '$chk"]');
        if (hidden) hidden.value = want ? 'Y' : 'N';
        return { absent: false, now: o.checked, hidden: hidden ? hidden.value : null };
      }, want);
      if (st.absent) return 'absent';
      if (st.now === want && st.hidden === (want ? 'Y' : 'N')) {
        await sleep(250);
        const still = await page.evaluate(() => {
          const o = document.querySelector('input[type="checkbox"][id^="SSR_CLSRCH_WRK_SSR_OPEN_ONLY$"]');
          return o ? o.checked : null;
        });
        if (still === want) return want ? 'on' : 'off';
      }
    }
    return want ? 'STUCK-OFF' : 'STUCK-ON';
  };
  const openOnlyOff = () => setOpenOnly(false);

  const band = async (op, num) => page.evaluate(({ op, num }) => {
    const sel = document.querySelector('select[id^="SSR_CLSRCH_WRK_SSR_EXACT_MATCH1"]');
    const inp = document.querySelector('input[id^="SSR_CLSRCH_WRK_CATALOG_NBR"]');
    if (!sel || !inp) return false;
    const WANT = { G: /greater than or equal/i, E: /is exactly/i, T: /less than or equal/i, C: /contains/i }[op];
    for (const o of sel.options) if (WANT.test(o.textContent || '')) { sel.value = o.value; break; }
    sel.dispatchEvent(new Event('change', { bubbles: true }));
    inp.value = String(num);
    inp.dispatchEvent(new Event('change', { bubbles: true }));
    return true;
  }, { op, num });

  const newSearch = async () => {
    const ok = await page.evaluate(() => {
      const btn = [...document.querySelectorAll('a,input,button')]
        .find(e => /start a new search|modify search|new search/i.test(e.value || e.textContent || ''));
      if (btn) { btn.click(); return (btn.value || btn.textContent || '').trim().slice(0, 30); }
      return null;
    });
    await sleep(1200);
    return ok;
  };

  const runOnce = async (label, op, num, leaveVia) => {
    await page.waitForSelector('select[id^="SSR_CLSRCH_WRK_SUBJECT_SRCH"]', { timeout: 20000 });
    await set('SSR_CLSRCH_WRK_SUBJECT_SRCH', SUBJECT);
    await band(op, num);
    await openOnlyOff();
    await timed(label + ':search', async () => {
      await clickById('CLASS_SRCH_WRK2_SSR_PB_CLASS_SRCH');
      await page.waitForFunction(() =>
        !!document.querySelector('a[id^="MTG_CLASS_NBR$"]') ||
        /Class Capacity|no classes found|exceed the maximum limit/i.test(document.body.innerText),
        null, { timeout: 45000 }).catch(() => {});
    });
    const n = await sectionCount();
    const straightToDetail = n === 0 && await page.evaluate(() => /Class Capacity/i.test(document.body.innerText));
    const nums = n ? await courseNumbers() : [];

    if (!straightToDetail) {
      await timed(label + ':detail', async () => {
        await clickById('MTG_CLASS_NBR$0');
        await page.waitForFunction(() => /Class Capacity|Enrollment Total/i.test(document.body.innerText), null, { timeout: 20000 }).catch(() => {});
      });
    }
    const seats = await page.evaluate(() => {
      const t = document.body.innerText;
      const g = l => { const m = t.match(new RegExp(l + '\\s*([0-9]+)', 'i')); return m ? +m[1] : null; };
      return { capacity: g('Class Capacity'), enrolled: g('Enrollment Total'), available: g('Available Seats'),
               wlCap: g('Wait List Capacity'), wlTot: g('Wait List Total') };
    });

    let left = null;
    if (leaveVia === 'back') {
      await timed(label + ':back(View Search Results)', async () => {
        await clickById('CLASS_SRCH_WRK2_SSR_PB_BACK');
        await page.waitForFunction(() => !!document.getElementById('MTG_CLASS_NBR$0'), null, { timeout: 45000 }).catch(() => {});
      });
      left = 'results list';
    } else {
      await timed(label + ':newSearch(form)', async () => { left = await newSearch(); });
    }
    return { label, sections: n, straightToDetail, seats, courseNumbers: nums, left };
  };

  const report = { term: TERM, subject: SUBJECT, at: new Date().toISOString(), runs: [], steps: results };

  /* A — what runs today. */
  report.runs.push(await runOnce('A whole-subject', 'G', 0, 'back'));
  await newSearch();

  /* Pick a real course number out of A's own results rather than hardcoding one, so this works
     for any subject and cannot silently bench a course that does not exist. */
  const pick = (report.runs[0].courseNumbers || [])[0];
  if (!pick) {
    console.log('!! could not read a course number from the whole-subject results — B and C skipped');
  } else {
    report.pickedCourse = pick;
    report.runs.push(await runOnce('B one-course->back', 'E', pick, 'back'));
    await newSearch();
    report.runs.push(await runOnce('C one-course->form', 'E', pick, 'form'));
  }

  /* ---- D: what does a transition sweep cost? --------------------------------------------
     The same subject searched twice, once with every section and once with only the open ones.
     Nothing is clicked into: this measures the LIST, because the list is the whole of tier 1. */
  const sweepOnce = async (label, openOnly) => {
    await newSearch();
    await page.waitForSelector('select[id^="SSR_CLSRCH_WRK_SUBJECT_SRCH"]', { timeout: 20000 }).catch(() => {});
    await set('SSR_CLSRCH_WRK_SUBJECT_SRCH', SUBJECT);
    await band('G', 0);                                   // the whole subject, no course-number band
    const ooState = await setOpenOnly(openOnly);
    await timed(label, async () => {
      await clickById('CLASS_SRCH_WRK2_SSR_PB_CLASS_SRCH');
      await page.waitForFunction(() =>
        !!document.querySelector('a[id^="MTG_CLASS_NBR$"]') ||
        /no classes found|exceed the maximum limit|did not return any/i.test(document.body.innerText),
        null, { timeout: 60000 }).catch(() => {});
    });
    const sections = await sectionCount();
    /* The class numbers ARE the transition detector. Two sweeps an hour apart, set-differenced:
       appeared = just opened, vanished = just filled. Captured here so the idea can be validated
       against real movement before anything is built on it. */
    const classNbrs = await page.evaluate(() =>
      [...document.querySelectorAll('a[id^="MTG_CLASS_NBR$"]')].map(a => (a.innerText || '').trim()).filter(Boolean));
    const capped = await page.evaluate(() => /exceed the maximum limit/i.test(document.body.innerText || ''));
    /* An open-only sweep that silently failed to set the checkbox measures the full list and
       reports a 1.0x ratio — the answer that kills the idea. Say so rather than publish it. */
    const trustworthy = ooState === (openOnly ? 'on' : 'off');
    if (!trustworthy) console.log(`!! ${label}: open-only ended up "${ooState}", NOT ${openOnly ? 'on' : 'off'} — this row is not measuring what it says.`);
    return { label, openOnly, ooState, trustworthy, sections, capped, classNbrs };
  };

  report.sweeps = [];
  report.sweeps.push(await sweepOnce('D-off full list (open-only OFF)', false));
  report.sweeps.push(await sweepOnce('D-on  open sections only', true));

  await browser.close();

  const w = 34;
  console.log(`\n${SUBJECT} · term ${TERM}` + (report.pickedCourse ? ` · course ${report.pickedCourse}` : '') + '\n');
  console.log('step'.padEnd(w) + 'bytes'.padStart(12) + 'ms'.padStart(8));
  console.log('-'.repeat(w + 20));
  for (const r of results) console.log(String(r.step).padEnd(w) + String(r.bytes ?? '?').padStart(12) + String(r.ms).padStart(8));
  console.log('\nper run:');
  for (const r of report.runs) console.log(`  ${r.label.padEnd(22)} sections=${String(r.sections).padStart(4)}  seats=${JSON.stringify(r.seats)}  left via ${r.left}`);

  const tot = name => results.filter(r => r.step.startsWith(name)).reduce((a, b) => ({ bytes: a.bytes + (b.bytes || 0), ms: Math.max(a.ms, b.ms) }), { bytes: 0, ms: 0 });
  const A = tot('A '), B = tot('B '), C = tot('C ');
  console.log(`\nround-trip totals   A ${A.bytes} bytes   B ${B.bytes} bytes   C ${C.bytes} bytes`);
  if (A.bytes && B.bytes) console.log(`B is ${(A.bytes / B.bytes).toFixed(1)}x cheaper than A per section visited`);
  if (A.bytes && C.bytes) console.log(`C is ${(A.bytes / C.bytes).toFixed(1)}x cheaper than A per section visited`);

  /* ---- what D means for tier 1 ---------------------------------------------------------- */
  const CAMPUS_SUBJECTS = 84;                 // the lane matrix covers ~84 Cal Poly subjects
  const bytesOf = name => results.filter(r => r.step === name).reduce((a, b) => a + (b.bytes || 0), 0);
  const msOf = name => Math.max(0, ...results.filter(r => r.step === name).map(r => r.ms || 0));
  /* If D did not complete, the block below would throw on `on.label` and lose A/B/C's results
     with it. A bench that discards measurements it already has because a later one failed is
     worse than useless. */
  const EMPTY = { label: '(not run)', sections: 0, capped: false, trustworthy: false, classNbrs: [] };
  const off = report.sweeps[0] || EMPTY, on = report.sweeps[1] || EMPTY;
  const offB = bytesOf(off.label), onB = bytesOf(on.label);
  const mb = b => (b / 1048576).toFixed(1) + ' MB';

  console.log('\ntransition sweep (tier 1):');
  console.log(`  full list        ${String(off.sections).padStart(4)} sections  ${String(offB).padStart(9)} bytes  ${String(msOf(off.label)).padStart(6)} ms${off.capped ? '  [HIT THE 300 CAP]' : ''}`);
  console.log(`  open only        ${String(on.sections).padStart(4)} sections  ${String(onB).padStart(9)} bytes  ${String(msOf(on.label)).padStart(6)} ms${on.capped ? '  [HIT THE 300 CAP]' : ''}`);
  if (!off.trustworthy || !on.trustworthy) {
    console.log('  !! one of these did not get the checkbox it asked for — treat the comparison as void.');
  } else if (offB && onB) {
    console.log(`  open-only is ${(offB / onB).toFixed(1)}x smaller, and ${off.sections ? (100 * on.sections / off.sections).toFixed(0) : '?'}% of ${SUBJECT} is open right now`);
    console.log(`  a ${CAMPUS_SUBJECTS}-subject campus sweep: ${mb(offB * CAMPUS_SUBJECTS)} full  vs  ${mb(onB * CAMPUS_SUBJECTS)} open-only`);
    /* The number the decision turns on. Under ~20 MB a sweep is comfortable every few minutes;
       near 118 MB it is not, and tier 1 needs a different signal. */
    const sweepMB = onB * CAMPUS_SUBJECTS / 1048576;
    console.log(`  => ${sweepMB < 20 ? 'AFFORDABLE every few minutes' : sweepMB < 50 ? 'affordable every 10-15 min' : 'TOO HEAVY for a frequent sweep — rethink tier 1'} (${sweepMB.toFixed(0)} MB per campus sweep)`);
    console.log(`  open-section class numbers captured (${on.classNbrs.length}) — run this again in an hour and diff them to see the transition detector work on real movement.`);

    /* THE MOST DIAGNOSTIC LINE IN THE WHOLE BENCH.
       Both big ideas — a cheap transition sweep, and narrowing the result set so the trip back is
       small — assume the cost of a results page is the BYTES. If open-only returns a fifth of the
       payload in the same wall-clock time, that assumption is wrong: the cost is server-side query
       time, and shrinking result sets buys nothing. Then the only lever left is not fetching the
       page at all — state branching against a retained ICStateNum. Worth knowing from this one run
       rather than after building the wrong thing. */
    const offMs = msOf(off.label), onMs = msOf(on.label);
    const byteRatio = offB / onB, msRatio = offMs / Math.max(1, onMs);
    console.log(`\n  bytes ${byteRatio.toFixed(1)}x smaller, time ${msRatio.toFixed(1)}x faster`);
    if (msRatio < 1.3 && byteRatio > 2) {
      console.log('  => THE COST IS THE QUERY, NOT THE WIRE. A smaller result set does not come back faster,');
      console.log('     so neither the transition sweep nor the narrow-band idea buys what it assumes.');
      console.log('     Re-read A/B/C above with that in mind; state branching becomes the only real lever.');
    } else {
      console.log('  => cost tracks payload, so shrinking the result set genuinely helps — both tier 1 and narrow-band hold up.');
    }
  }

  await writeFile(`bench-${SUBJECT}-${TERM}.json`, JSON.stringify(report, null, 2));
  if (process.env.GITHUB_STEP_SUMMARY) {
    const { appendFileSync } = await import('node:fs');
    appendFileSync(process.env.GITHUB_STEP_SUMMARY,
      `### Search-strategy bench — ${SUBJECT}, term ${TERM}\n\n| step | bytes | ms |\n|---|---:|---:|\n` +
      results.map(r => `| ${r.step} | ${r.bytes ?? '?'} | ${r.ms} |`).join('\n') +
      `\n\n**A** ${A.bytes} · **B** ${B.bytes} · **C** ${C.bytes} bytes per section visited.\n` +
      `\n**Transition sweep:** full list ${offB} bytes / ${off.sections} sections · open-only ${onB} bytes / ${on.sections} sections` +
      (offB && onB ? ` — **${(offB / onB).toFixed(1)}x smaller**, ${mb(onB * CAMPUS_SUBJECTS)} for an ${CAMPUS_SUBJECTS}-subject campus sweep.\n` : '\n'));
  }
}

main().catch(e => { console.error('BENCH FAILED:', e.message); process.exit(1); });
