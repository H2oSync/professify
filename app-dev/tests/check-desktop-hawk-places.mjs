/* check-desktop-hawk-places — (1) help chips (website-hawk-help-chips-2026-10-14): a question about TermChamp that
   the router refuses or the model can't answer is offered the matching help topic ("Did you mean …"); a tap answers on
   the page with nothing sent; a question naming a course never gets one; the dark-mode and Plans answers fit the website.
   (2) With client:'app', the ask function's go_to may only name the phone's APP_PLACES
   (supabase/functions/ask/shared.ts). Every one of them must land on a real website screen with no page error,
   and set_theme's two values must work. Run: APP_DIR=<repo> node check-desktop-hawk-places.mjs [--quiet] */
import { openApp } from './app-harness.mjs';
import fs from 'fs';
const QUIET = process.argv.includes('--quiet');
let pass = 0, fail = 0; const fails = [];
const ok = (c, n, i) => { if (c) { pass++; if (!QUIET) console.log('  ok  ', n); } else { fail++; fails.push(n); console.log('  FAIL', n, i !== undefined ? '→ ' + JSON.stringify(i).slice(0, 300) : ''); } };
const src = fs.readFileSync(new URL('../../supabase/functions/ask/shared.ts', import.meta.url), 'utf8');
const PLACES = JSON.parse(src.match(/export const APP_PLACES = (\[[\s\S]*?\]);/)[1].replace(/'/g, '"'));
const TOOLS = {};
PLACES.forEach(p => { TOOLS['take me to the ' + p + ' screen'] = ['go_to', { where: p }]; });
TOOLS['can i change the colours of the app'] = ['cant_answer', {}]; TOOLS['what are plans a b and c'] = ['cant_answer', {}];
TOOLS['how do i contact termchamp'] = ['cant_answer', { reason: 'not_about_classes' }];
TOOLS['is hawk safe with my data'] = ['cant_answer', {}];
TOOLS['is this app free to use'] = ['cant_answer', { reason: 'not_about_classes' }];
TOOLS['how do i add the class bus 4442'] = ['cant_answer', {}];
TOOLS['dark mode'] = ['set_theme', { theme: 'dark' }]; TOOLS['light mode'] = ['set_theme', { theme: 'light' }];
const ask = b => (TOOLS[b.q] ? { tool: TOOLS[b.q][0], args: TOOLS[b.q][1] } : { tool: 'cant_answer', args: {} });
const tick = async (p, ms = 400) => { await p.clock.runFor(ms); await p.waitForTimeout(200); };
const { page, close, log } = await openApp({ path: '/', width: 1440, height: 900, wait: 4000, ask });
await tick(page, 2500);
const lastTurn = () => page.evaluate(() => { const t = [...document.querySelectorAll('.hawk-turn')].pop(); return t ? { text: t.textContent, rows: [...t.querySelectorAll('.hawk-row')].map(r => r.textContent.trim()) } : null; });
const askQ = async q => { await page.evaluate(q => HawkAsk.ask(q), q); await tick(page, 1500); return lastTurn(); };
for (const [q, want] of [['how do i contact termchamp', 'How do I contact TermChamp?'], ['how do i contact you guys', 'How do I contact TermChamp?'],
                         ['is hawk safe with my data', 'What does Hawk do and where does my information go?'], ['is this app free to use', 'Is TermChamp free?']]) {
  const t = await askQ(q);
  ok(t && t.rows.some(r => r.includes(want)), `help chips: “${q}” is offered “${want}”`, t);
  if (q === 'how do i contact termchamp' && t && t.rows.some(r => r.includes(want))) {
    const n = log.asks.length;
    await page.evaluate(w => [...document.querySelectorAll('.hawk-turn .hawk-row')].find(r => r.textContent.includes(w)).click(), want); await tick(page, 900);
    const a = await lastTurn();
    ok(/support@termchamp\.com/.test(a.text), 'help chips: the chip answers with the help topic (support@termchamp.com)', a);
    ok(log.asks.length === n, 'help chips: answering a chip sends nothing', { before: n, after: log.asks.length });
  }
}
const course = await askQ('how do i add the class bus 4442');
ok(!/Did you mean (this|one of these)\?/.test(course.text) && !course.rows.some(r => /How do I add a class/.test(r)), 'help chips: a question naming a course never gets a help chip', course);
const viaChip = async (q, chip) => { await askQ(q); await page.evaluate(w => { const r = [...document.querySelectorAll('.hawk-turn .hawk-row')].find(r => r.textContent.includes(w)); if (r) r.click(); }, chip); await tick(page, 900); return lastTurn(); };
const dm = await viaChip('can i change the colours of the app', 'Is there a dark mode?');
ok(/Light or Dark/.test(dm.text) && !/System/.test(dm.text), 'help: dark mode names the website’s two choices (no “System”)', dm.text);
const pl = await viaChip('what are plans a b and c', 'What are Plans A, B and C?');
ok(/Schedule › Plans/.test(pl.text) && pl.rows.some(r => /Open Plans/.test(r)), 'help: Plans lives in Schedule › Plans and the button says Open Plans', pl);
await page.evaluate(() => { const r = [...document.querySelectorAll('.hawk-turn .hawk-row')].find(r => /Open Plans/.test(r.textContent)); if (r) r.click(); }); await tick(page, 900);
ok(await page.evaluate(() => document.getElementById('view-sched').classList.contains('active') && document.getElementById('stab-watch').classList.contains('on')), 'help: Open Plans lands on Schedule › Plans', null);
ok(PLACES.length >= 25, 'read the phone menu’s places from shared.ts', PLACES.length);
for (const p of PLACES) {
  await page.evaluate(() => { try { HawkAsk.close && HawkAsk.close(); } catch (_) {} try { if (typeof closeAllModals === 'function') closeAllModals(); } catch (_) {} document.querySelectorAll('.modal-back.open,.open[role=dialog]').forEach(e => e.classList.remove('open')); show('home'); });
  await tick(page, 300);
  const before = log.errors.length;
  await page.evaluate(q => HawkAsk.ask(q), 'take me to the ' + p + ' screen');
  await tick(page, 1500);
  const r = await page.evaluate(() => { const rows = [...document.querySelectorAll('.hawk-turn .hawk-row')]; const last = rows[rows.length - 1]; return { n: rows.length, name: last ? last.textContent.trim().slice(0, 60) : '', notes: [...document.querySelectorAll('.hawk-turn .hawk-note')].map(x => x.textContent).slice(-2) }; });
  const rowShown = r.n > 0 && !/Not it\?/.test(r.name);
  if (rowShown) { await page.evaluate(() => { const rows = document.querySelectorAll('.hawk-turn .hawk-row'); rows[rows.length - 1].click(); }); await tick(page, 900); }
  const where = await page.evaluate(() => ({ view: (document.querySelector('.view.active,section.active,[id^=view-].active') || {}).id || '', modal: [...document.querySelectorAll('.open,[open]')].filter(e => { const r = e.getBoundingClientRect(); const cs = getComputedStyle(e); return r.width > 200 && r.height > 150 && cs.visibility !== 'hidden' && cs.display !== 'none' && (cs.position === 'fixed' || e.tagName === 'DIALOG') && !e.closest('.hawk, #hawk, [class*=hawk]'); }).map(e => e.id || e.className.toString().slice(0, 30)).join(',') }));
  ok(rowShown && log.errors.length === before && (where.view || where.modal), `go_to "${p}" → a website screen (${where.view}${where.modal ? ' + ' + where.modal : ''})`, { r, where, err: log.errors.slice(before) });
}
for (const t of ['dark', 'light']) {
  await page.evaluate(q => HawkAsk.ask(q), t + ' mode'); await tick(page, 1500);
  const th = await page.evaluate(() => document.documentElement.getAttribute('data-theme') || document.body.className);
  ok(new RegExp(t).test(th) || (t === 'light' && !/dark/.test(th)), `set_theme ${t}`, th);
}
ok(log.errors.length === 0, 'no page errors', log.errors);
await close();
console.log(`\ncheck-desktop-hawk-places: ${pass} passed, ${fail} failed`);
if (fail) { console.log('failed: ' + fails.join(' | ')); process.exitCode = 1; }
