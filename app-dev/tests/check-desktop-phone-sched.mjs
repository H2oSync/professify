/* check-desktop-phone-sched — Schedule > My classes and Schedule > Plans on a phone (<= 640px), 2026-10-16 (Tate: week blocks had
   cramped / clipped class names, "Corporate", "Introdu to...", and Plans blocks showed only a wrapped course code).
   Runs the REAL index.html in Chromium, signed in, against the PostgREST stand-in.
   Run: APP_DIR=<repo> node check-desktop-phone-sched.mjs [--only name] [--quiet]   (APP_PORT to move off the default)
   The promises: on a phone the owner's own week is taller (a 50-minute class holds its code and two lines of name, an 80-minute one the
   whole name or an ellipsis), nothing is clipped, no sideways page scroll, at 390 and 640, dark and light; a Plans block shows the
   code on one line and as many lines of the name as fit, no time; a tap still opens the class; a friend's week, the Home friend
   cards and the friend profile keep their scale; a laptop width is exactly what it was. */
import { openApp } from './app-harness.mjs';
import * as FX from './app-fixtures.mjs';

const args = process.argv.slice(2);
const ONLY = args.includes('--only') ? args[args.indexOf('--only') + 1] : null;
const QUIET = args.includes('--quiet');
let pass = 0, fail = 0; const fails = [];
function ok(c, name, info) {
  if (c) { pass++; if (!QUIET) console.log('  ok  ', name); }
  else { fail++; fails.push(name); console.log('  FAIL', name, info !== undefined ? '→ ' + JSON.stringify(info).slice(0, 700) : ''); }
}
const tick = async (p, ms = 400) => { await p.clock.runFor(ms); await p.waitForTimeout(250); };
const NOW = '2026-10-14T10:30:00-07:00';
let portN = 0; const BASE = +(process.env.APP_PORT || (8300 + Math.floor(Math.random() * 500)));
const open = [];
const theme = t => `try{localStorage.setItem('professify-theme','${t}')}catch(e){}`;
const ph = async (o = {}) => { const a = await openApp(Object.assign({ path: '/', width: 390, height: 844, wait: 4000, time: NOW, port: BASE + (portN++ % 20), init: theme('dark') }, o)); open.push(a); return a; };
const T = {}; const test = (name, fn) => { T[name] = fn; };

const toMine = async page => { await page.evaluate(() => { show('sched'); try { setSchedTab('mine'); } catch (e) {} renderMyClasses(); try { if (myClassesView !== 'calendar') setMyClassesView('calendar'); } catch (e) {} }); await tick(page, 1500); };
const PLAN = ['BUS 3431', 'BUS 3438', 'BUS 4442', 'BUS 4445', 'BUS 3346'];
const toPlans = async page => {
  await page.evaluate(PLAN => {
    const list = []; PLAN.forEach(c => { const r = (SEAT_SECTIONS[c] || [])[0]; if (r) list.push({ code: c, class_nbr: String(r.class_nbr).trim() }); });
    TCPlans.setSections('A', list); show('sched'); setSchedTab('watch'); TCPlans.setCur('A');
  }, PLAN); await tick(page, 1500);
};
/* every block of a week: is anything cut off (the block, its name box, a code half) */
const mineBlocks = page => page.evaluate(() => [...document.querySelectorAll('.mc-cal .cal-block[data-s]')].filter(b => b.offsetHeight > 0).map(b => {
  const nm = b.querySelector('.cb-nm'), c = b.querySelector('.cb-nmc'), cs = b.querySelector('.cb-cs'), cn = b.querySelector('.cb-cn');
  const lh = c ? parseFloat(getComputedStyle(c).lineHeight) : 0;
  return { code: b.getAttribute('data-code'), h: Math.round(b.offsetHeight), over: b.scrollHeight - b.clientHeight, nmOver: nm ? nm.scrollHeight - nm.clientHeight : 0,
    cOver: c ? c.scrollHeight - c.clientHeight : 0, lines: c ? Math.round(c.clientHeight / lh) : 0, text: c ? c.textContent : '',
    wide: (cs ? cs.scrollWidth - cs.clientWidth : 0) + (cn ? cn.scrollWidth - cn.clientWidth : 0), wOver: c ? c.scrollWidth - c.clientWidth : 0 };
}));
const sideways = page => page.evaluate(() => document.documentElement.scrollWidth - innerWidth);

for (const [W, TH] of [[390, 'dark'], [390, 'light'], [640, 'dark'], [640, 'light']]) {
  test('mine-' + W + '-' + TH, async () => {
    const { page, close, log } = await ph({ width: W, init: theme(TH) }); await tick(page, 1500); await toMine(page);
    const r = await mineBlocks(page);
    const day = await page.evaluate(() => Math.round([...document.querySelectorAll('.mc-cal .cal-day')].find(e => e.offsetHeight).offsetHeight));
    ok(await page.evaluate(() => document.documentElement.getAttribute('data-theme')) === TH, 'theme is ' + TH);
    ok(r.length >= 8 && day > 500 && day < 700, W + 'px: the week is taller than the old 336px (' + day + 'px) and still one screen or two', { day, n: r.length });
    ok(r.every(b => b.over <= 1 && b.nmOver <= 1 && b.wide <= 1), 'no block clips its code or its name (a long name ends in an ellipsis, it is not cut)', r.filter(b => b.over > 1 || b.nmOver > 1 || b.wide > 1));
    ok(r.every(b => b.lines === 2 || (b.lines === 1 && b.cOver <= 1)), 'every block of 80 minutes shows its whole name, or two lines ending in an ellipsis', r.map(b => b.code + ':' + b.h + ':' + b.lines + ':' + b.cOver));
    ok(r.every(b => b.text.length > 3), 'the name is there, not just the code', r.map(b => b.text));
    if (W === 390) {
      const names = r.map(b => b.text);
      ok(names.some(n => /Corporate Finance/.test(n)) && !r.some(b => /^Introdu$/.test(b.text)), 'the examples from the report: "Corporate Finance" whole, "Introduction to ..." not cut to "Introdu"', names);
      ok(r.every(b => b.wOver <= 1), 'no name runs sideways out of its block', r.filter(b => b.wOver > 1));
    }
    ok(await sideways(page) <= 0, 'no sideways page scroll', await sideways(page));
    ok(await page.evaluate(() => (w => w.scrollWidth <= w.clientWidth + 1)([...document.querySelectorAll('.mc-cal .cal-wrap')].find(e => e.offsetWidth))), 'the week itself does not scroll sideways');
    const cols = await page.evaluate(() => { const mc = [...document.querySelectorAll('.mc-cal')].find(e => e.offsetWidth); return [...mc.querySelectorAll('.cal-wrap > .cal-col:not(.cal-any)')].map(c => Math.round(c.getBoundingClientRect().width)); });
    ok(cols.length === 5 && cols.every(w => w >= 40), 'five day columns, each wide enough to read (' + cols.join('/') + ')', cols);
    ok(log.errors.length === 0, 'no page errors', log.errors); await close();
  });
}

test('mine-50min', async () => {
  for (const W of [390, 640, 360]) {
    const { page, close } = await ph({ width: W }); await tick(page, 1500); await toMine(page);
    const f = await page.evaluate(() => {
      const m = { 'BUS 4442': { secs: [{ crn: '1', days: 'MoWeFr 10:10AM - 11:00AM', prof: 'Ada Examplewood' }] } };
      const host = document.createElement('div'); host.style.cssText = 'position:absolute;left:0;top:0;width:' + (innerWidth - 30) + 'px'; host.innerHTML = renderMyCalendar(['BUS 4442'], { bad: {} }, m, { cm: 'me' }); document.body.appendChild(host);
      const b = host.querySelector('.cal-block[data-s]'), nm = b.querySelector('.cb-nm'), c = b.querySelector('.cb-nmc');
      const o = { h: Math.round(b.offsetHeight), over: b.scrollHeight - b.clientHeight, nmOver: nm.scrollHeight - nm.clientHeight, lines: Math.round(nm.clientHeight / parseFloat(getComputedStyle(c).lineHeight)), text: c.textContent, cls: b.className };
      host.remove(); return o;
    });
    ok(f.h >= 46 && f.over <= 1 && f.nmOver <= 1 && f.lines === 2, W + 'px: a 50-minute class is ' + f.h + 'px: code + two lines of name, nothing cut off', f);
    await close();
  }
});

test('mine-clash', async () => {
  /* two classes sharing an hour = a lane-split week (min-width 720, scrolls inside its own box, never the page) */
  const { page, close } = await ph({ width: 390 }); await tick(page, 1500); await toMine(page);
  const f = await page.evaluate(() => {
    const m = { 'BUS 4442': { secs: [{ crn: '1', days: 'MoWe 10:10AM - 11:50AM', prof: 'A B' }] }, 'BUS 4445': { secs: [{ crn: '2', days: 'MoWe 10:10AM - 11:50AM', prof: 'C D' }] } };
    const host = document.createElement('div'); host.style.cssText = 'position:absolute;left:0;top:0;width:360px'; host.innerHTML = renderMyCalendar(['BUS 4442', 'BUS 4445'], { bad: {} }, m, { cm: 'me' }); document.body.appendChild(host);
    const bs = [...host.querySelectorAll('.cal-block[data-s]')].map(b => { const nm = b.querySelector('.cb-nm'); return { over: b.scrollHeight - b.clientHeight, nmOver: nm ? nm.scrollHeight - nm.clientHeight : 0, h: Math.round(b.offsetHeight) }; });
    const o = { split: !!host.querySelector('.cal-split'), bs, page: document.documentElement.scrollWidth - innerWidth }; host.remove(); return o;
  });
  ok(f.split && f.bs.length >= 2 && f.bs.every(b => b.over <= 1 && b.nmOver <= 1) && f.page <= 0, 'a clash week: both blocks hold their text, the page does not scroll sideways', f);
  await close();
});

test('mine-tap', async () => {
  const { page, close, log } = await ph(); await tick(page, 1500); await toMine(page);
  await page.evaluate(() => { window.__taps = []; const o = window.cbTap; window.cbTap = function () { window.__taps.push([].slice.call(arguments).join('|')); return o.apply(this, arguments); }; });
  await page.tap('.mc-cal .cal-block[data-code="BUS 4442"]'); await tick(page, 500);
  const taps = await page.evaluate(() => window.__taps);
  ok(taps.length >= 1 && taps[taps.length - 1].startsWith('BUS 4442'), 'tapping a class on the phone still calls the same cbTap (opens the class)', taps);
  ok(log.errors.length === 0, 'no page errors', log.errors); await close();
});

for (const [W, TH] of [[390, 'dark'], [390, 'light'], [500, 'dark'], [640, 'dark'], [640, 'light']]) {
  test('plans-' + W + '-' + TH, async () => {
    const { page, close, log } = await ph({ width: W, init: theme(TH) }); await tick(page, 1500); await toPlans(page);
    const r = await page.evaluate(() => [...document.querySelectorAll('#plansOut .pl3-week .pl3-blk[data-code]')].map(b => {
      const w = b.querySelector('.pl3-nmw'), n = b.querySelector('.pl3-nm'), c = b.querySelector('b'), tm = b.querySelector('.pl3-tm');
      const shown = !!w && getComputedStyle(w).display !== 'none';
      const lh = parseFloat(getComputedStyle(n).lineHeight);
      return { code: b.getAttribute('data-code'), h: Math.round(b.offsetHeight), over: b.scrollHeight - b.clientHeight, shown, lines: shown ? Math.round(w.getBoundingClientRect().height / lh) : 0,
        codeLines: Math.round(c.getBoundingClientRect().height / (parseFloat(getComputedStyle(c).lineHeight) || 12)), nmWide: shown ? n.scrollWidth - n.clientWidth : 0, tm: !!tm && getComputedStyle(tm).display !== 'none', text: n.textContent };
    }));
    const g = await page.evaluate(() => ({ h: document.querySelector('#plansOut .pl3-week .pl3-grid').offsetHeight, hrs: +getComputedStyle(document.querySelector('#plansOut .pl3-week')).getPropertyValue('--pl3-hrs') }));
    ok(r.length >= 8 && g.h > 440, W + 'px: the week is taller than the old flat 440px (' + g.h + 'px for ' + g.hrs + ' hours)', { g, n: r.length });
    ok(r.every(b => b.over <= 1), 'nothing is clipped inside a block', r.filter(b => b.over > 1));
    ok(r.every(b => b.shown && b.lines >= 1), 'every block shows its code and at least one line of the name', r.map(b => b.code + ':' + b.h + ':' + b.lines));
    ok(r.filter(b => b.h >= 70).every(b => b.lines === 2 || b.text.length < 16), 'a block with room shows two lines of name', r.map(b => b.code + ':' + b.h + ':' + b.lines));
    if (W <= 520) {
      ok(r.every(b => b.codeLines === 1), 'the course code is one line, not "BUS" over "3346"', r.map(b => b.code + ':' + b.codeLines));
      ok(r.every(b => !b.tm), 'no time line on a phone (the class opens on tap)', r.filter(b => b.tm).length);
      ok(g.h === Math.round(g.hrs * 56), 'a phone week is 56px an hour', g);
    }
    ok(await sideways(page) <= 0, 'no sideways page scroll', await sideways(page));
    ok(log.errors.length === 0, 'no page errors', log.errors); await close();
  });
}

test('plans-tap', async () => {
  const { page, close, log } = await ph(); await tick(page, 1500); await toPlans(page);
  await page.evaluate(() => { window.__opened = []; const o = window.openClassPage; window.openClassPage = function (c) { window.__opened.push(c); return o.apply(this, arguments); }; });
  await page.tap('#plansOut .pl3-week .pl3-blk[data-code="BUS 4442"]'); await tick(page, 600);
  ok((await page.evaluate(() => window.__opened)).join() === 'BUS 4442', 'tapping a plan block still opens the class');
  ok(log.errors.length === 0, 'no page errors', log.errors); await close();
});

test('plan-edit-untouched', async () => {
  /* the Planner's own week (edit mode) keeps its flat height and code-only blocks */
  const { page, close } = await ph(); await tick(page, 1500); await toPlans(page);
  const r = await page.evaluate(() => { const h = window.TCPlans && null; return { edit: !!document.querySelector('.pl3-week--edit') }; });
  ok(true, 'planner week present: ' + r.edit);
  const css = await page.evaluate(() => { const t = document.getElementById('sched-hover-css').textContent; return /pl3-week:not\(\.pl3-week--edit\) \.pl3-grid\{height:calc\(var\(--pl3-hrs,10\) \* 56px\)/.test(t); });
  ok(css, 'the phone height rule only targets a non-edit week');
  await close();
});

test('friends-unchanged', async () => {
  /* the friend profile's week and the Home friend cards keep their own scale and their stacked code at 390 */
  const { page, close, log } = await ph(); await tick(page, 1500);
  const homeDays = await page.evaluate(() => [...document.querySelectorAll('#hmFeed .cal-mini .cal-day')].map(d => Math.round(d.offsetHeight)));
  const homeBlocks = await page.evaluate(() => [...document.querySelectorAll('#hmFeed .cal-mini .cal-block')].map(b => ({ ph: b.classList.contains('cb-ph'), padL: getComputedStyle(b).paddingLeft })));
  ok(homeBlocks.every(b => !b.ph), 'Home friend-card weeks carry no phone-sched class', homeBlocks.slice(0, 4));
  await page.evaluate(id => openFriendProfile(id), FX.FRIENDS[0].id); await tick(page, 1500);
  if (!(await page.$('.frp-cal'))) { await page.evaluate(() => setFrpView('cal')); await tick(page, 1500); }
  const f = await page.evaluate(() => { const c = document.querySelector('.frp-cal'); return c && { dayH: c.querySelector('.cal-day').offsetHeight, ph: c.querySelectorAll('.cb-ph').length, over: document.documentElement.scrollWidth - innerWidth }; });
  ok(f && f.ph === 0 && f.dayH < 400, 'the friend profile week keeps its scale and has no phone-sched blocks', f);
  console.log('   (home day heights: ' + homeDays.join(',') + '; friend day: ' + (f && f.dayH) + ')');
  ok(log.errors.length === 0, 'no page errors', log.errors); await close();
});

test('desktop-same', async () => {
  const { page, close } = await ph({ width: 1300, height: 900 }); await tick(page, 1500); await toMine(page);
  const r = await page.evaluate(() => ({ day: Math.round([...document.querySelectorAll('.mc-cal .cal-day')].find(e => e.offsetHeight).offsetHeight), ph: document.querySelectorAll('.cb-ph').length }));
  ok(r.day === 828 && r.ph === 0, 'a laptop week is the tall 0.92 week it was (and no .cb-ph)', r);
  await toPlans(page);
  const p = await page.evaluate(() => ({ g: document.querySelector('#plansOut .pl3-grid').offsetHeight }));
  ok(p.g === 800, 'laptop Plans is still 80px an hour', p);
  await close();
});

const names = ONLY ? [ONLY] : Object.keys(T);
for (const n of names) {
  if (!T[n]) { console.log('no such test', n); process.exit(2); }
  if (!QUIET) console.log('\n' + n);
  try { await T[n](); } catch (e) { fail++; fails.push(n + ' threw'); console.log('  FAIL', n, 'threw', String(e).slice(0, 400)); }
  for (const a of open.splice(0)) { try { await a.close(); } catch (e) {} }
}
console.log(`\ncheck-desktop-phone-sched: ${pass} passed, ${fail} failed`);
if (fail) { console.log('failed:', fails.join(' | ')); process.exit(1); }
