#!/usr/bin/env node
/**
 * Professify — Cal Poly seat scraper (Playwright, with real seat COUNTS)
 * ---------------------------------------------------------------------
 * Drives the public PeopleSoft class search exactly like a person:
 *   institution SLCMP -> term 2268 -> per subject: search -> parse list
 *   -> (optional) open each section's detail page for capacity/enrolled/
 *   available/waitlist -> upsert into Supabase.
 *
 * Every selector below was confirmed live on cmsweb.pscs.calpoly.edu.
 * Runs on GitHub Actions (which can reach Cal Poly). Local run works too
 * from any machine on a normal network.
 *
 *   npm i && npx playwright install --with-deps chromium
 *   CP_SUBJECTS=BUS CP_FETCH_DETAILS=1 SUPABASE_URL=... SUPABASE_SERVICE_KEY=... node scrape-seats.mjs
 */
import { chromium } from 'playwright';

const CFG = {
  URL: 'https://cmsweb.pscs.calpoly.edu/psc/CSLOPRD/EMPLOYEE/SA/c/COMMUNITY_ACCESS.CLASS_SEARCH.GBL',
  INSTITUTION: process.env.CP_INSTITUTION || 'SLCMP',
  TERM: process.env.CP_TERM || '2268',                       // Fall Semester 2026
  SUBJECTS: (process.env.CP_SUBJECTS || 'BUS').split(',').map(s => s.trim()).filter(Boolean),
  FETCH_DETAILS: process.env.CP_FETCH_DETAILS !== '0',        // ON by default (seat counts)
  HEADLESS: process.env.CP_HEADLESS !== '0',
  SUPABASE_URL: process.env.SUPABASE_URL || '',
  SUPABASE_SERVICE_KEY: process.env.SUPABASE_SERVICE_KEY || '',
};
const sel = id => `[id="${id}"]`;
const sleep = ms => new Promise(r => setTimeout(r, ms));

// Fire an action and wait for the PeopleSoft postback (POST to the .GBL) to land.
async function postback(page, action) {
  await Promise.all([
    page.waitForResponse(r => r.url().includes('CLASS_SEARCH') && r.request().method() === 'POST', { timeout: 25000 }).catch(() => {}),
    action(),
  ]);
  await sleep(350);
}
// Set a <select>/text field value the way PeopleSoft needs (real change event) and wait for its postback.
async function setField(page, id, value) {
  await postback(page, () => page.evaluate(({ id, value }) => {
    const el = document.getElementById(id); if (!el) return;
    el.value = value; el.dispatchEvent(new Event('change', { bubbles: true }));
  }, { id, value }));
}
async function dismissOversize(page) {
  if (/would you like to continue/i.test(await page.evaluate(() => document.body.innerText))) {
    await postback(page, () => page.evaluate(() => {
      const ok = [...document.querySelectorAll('input[type="button"],input[type="submit"],a,button')]
        .find(e => /^OK$/i.test((e.value || e.textContent || '').trim()));
      if (ok) ok.click();
    }));
  }
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
        out.push({
          subject, index: out.length,
          course_code: tm ? (tm[1] + ' ' + tm[2]) : '',
          title: tm ? tm[3] : title,
          class_nbr: (el.innerText || '').trim(),
          section: cells[1] || '', instructor: cells[4] || '', days: cells[2] || '', dates: cells[5] || '',
          status_raw: img ? img.getAttribute('alt') : '',
        });
      }
    });
    return out;
  }, subject);
}

async function fetchDetail(page, index) {
  // click the class number -> detail page -> read counts -> back to list
  await page.evaluate(i => { const a = document.getElementById('MTG_CLASS_NBR$' + i); if (a) a.click(); }, index);
  await page.waitForFunction(() => /Class Capacity|Enrollment Total/i.test(document.body.innerText) && document.getElementById('CLASS_SRCH_WRK2_SSR_PB_BACK'), null, { timeout: 12000 }).catch(() => {});
  const c = await page.evaluate(() => {
    const t = document.body.innerText;
    const g = l => { const m = t.match(new RegExp(l + '\\s*([0-9]+)', 'i')); return m ? +m[1] : null; };
    return { capacity: g('Class Capacity') ?? g('Enrollment Capacity'), enrolled: g('Enrollment Total'), available: g('Available Seats'), waitlist_capacity: g('Wait List Capacity'), waitlist_total: g('Wait List Total') };
  });
  await page.evaluate(() => { const b = document.getElementById('CLASS_SRCH_WRK2_SSR_PB_BACK'); if (b) b.click(); });
  await page.waitForFunction(() => document.getElementById('MTG_CLASS_NBR$0') && !document.getElementById('CLASS_SRCH_WRK2_SSR_PB_BACK'), null, { timeout: 12000 }).catch(() => {});
  await sleep(120);
  return c;
}

const statusBadge = s => { s = (s || '').toLowerCase(); return s.includes('wait') ? 'Waitlist' : s.includes('open') ? 'Open' : s.includes('clos') ? 'Closed' : null; };

async function run() {
  console.log(`Professify seat scraper — term ${CFG.TERM}, subjects [${CFG.SUBJECTS.join(', ')}], counts=${CFG.FETCH_DETAILS ? 'on' : 'off'}`);
  const browser = await chromium.launch({ headless: CFG.HEADLESS });
  const page = await browser.newPage();
  await page.goto(CFG.URL, { waitUntil: 'domcontentloaded' });
  await page.waitForSelector(sel('CLASS_SRCH_WRK2_INSTITUTION$31$'), { timeout: 30000 });
  await setField(page, 'CLASS_SRCH_WRK2_INSTITUTION$31$', CFG.INSTITUTION);   // populates subjects
  await setField(page, 'SLO_SS_DERIVED_STRM', CFG.TERM);                       // validates term

  const all = [];
  for (let s = 0; s < CFG.SUBJECTS.length; s++) {
    const subj = CFG.SUBJECTS[s];
    try {
      if (s > 0) {
        const modify = page.locator('input[value="Modify Search"], a:has-text("Modify Search")').first();
        if (await modify.count()) await postback(page, () => modify.click());
      }
      await setField(page, 'SSR_CLSRCH_WRK_SUBJECT_SRCH$1', subj);
      await page.evaluate(() => { const o = document.getElementById('SSR_CLSRCH_WRK_SSR_OPEN_ONLY$4'); if (o) o.checked = false; });
      await postback(page, () => page.evaluate(() => document.getElementById('CLASS_SRCH_WRK2_SSR_PB_CLASS_SRCH').click()));
      await dismissOversize(page);

      const list = await parseList(page, subj);
      console.log(`  ${subj}: ${list.length} sections${CFG.FETCH_DETAILS ? ' — fetching counts…' : ''}`);
      if (CFG.FETCH_DETAILS) {
        for (let i = 0; i < list.length; i++) {
          const c = await fetchDetail(page, i);
          Object.assign(list[i], c);
          if ((i + 1) % 25 === 0) console.log(`    …${i + 1}/${list.length}`);
        }
      }
      list.forEach(r => { r.status = statusBadge(r.status_raw); r.term = CFG.TERM; r.updated_at = new Date().toISOString(); });
      all.push(...list);
    } catch (e) { console.error(`  ${subj}: ERROR — ${e.message.split('\n')[0]}`); }
  }
  await browser.close();

  const { writeFile } = await import('node:fs/promises');
  await writeFile('seats.json', JSON.stringify({ term: CFG.TERM, generated_at: new Date().toISOString(), count: all.length, sections: all }, null, 2));
  console.log(`• Wrote seats.json (${all.length} sections).`);
  await upsertSupabase(all);
  if (!all.length) { console.log('\n⚠  Zero sections — run with CP_HEADLESS=0 to watch where it breaks.'); process.exit(2); }
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
  for (let i = 0; i < clean.length; i += 500) {
    const res = await fetch(url, {
      method: 'POST',
      headers: { apikey: CFG.SUPABASE_SERVICE_KEY, Authorization: `Bearer ${CFG.SUPABASE_SERVICE_KEY}`, 'Content-Type': 'application/json', Prefer: 'resolution=merge-duplicates,return=minimal' },
      body: JSON.stringify(clean.slice(i, i + 500)),
    });
    if (!res.ok) throw new Error(`Supabase upsert failed: HTTP ${res.status}\n${(await res.text()).slice(0, 300)}`);
  }
  console.log(`• Upserted ${clean.length} rows into Supabase.`);
}

run().catch(e => { console.error('FATAL:', e.message); process.exit(1); });
