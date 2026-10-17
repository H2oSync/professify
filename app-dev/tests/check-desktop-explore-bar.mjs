/* check-desktop-explore-bar — Explore's filter bar is one quiet row (explore-bar, mockup option A, 2026-10-16).
   Runs the REAL index.html in Chromium, signed in, against the PostgREST stand-in of check-app.
   Run: APP_DIR=<repo> node check-desktop-explore-bar.mjs [--only name] [--quiet]   (APP_PORT to move off the random 8300+ port)
   The promises: GEs / My major / Saved are plain text tabs (no pills) with an underline on the active one; the term is the phone's switch —
   ONE button, plain muted bold words + a small up/down icon, that flips Spring 2027 <-> Fall 2026; a small Classes | Professors toggle sits on the
   same line; every behaviour is as before (filters, Spring first, Fall reads, Saved hidden on Fall, professors mode, aria-pressed, keyboard);
   on a phone it wraps cleanly with no horizontal page scroll. Schedule > My classes uses the same single switch. */
import { openApp } from './app-harness.mjs';
import * as FX from './app-fixtures.mjs';

if (!process.env.APP_PORT) process.env.APP_PORT = String(8300 + Math.floor(Math.random() * 600));
const args = process.argv.slice(2);
const ONLY = args.includes('--only') ? args[args.indexOf('--only') + 1] : null;
const QUIET = args.includes('--quiet');
let pass = 0, fail = 0; const fails = [];
function ok(c, name, info) {
  if (c) { pass++; if (!QUIET) console.log('  ok  ', name); }
  else { fail++; fails.push(name); console.log('  FAIL', name, info !== undefined ? '→ ' + JSON.stringify(info).slice(0, 400) : ''); }
}
const tick = async (p, ms = 400) => { await p.clock.runFor(ms); await p.waitForTimeout(250); };
const desk = (o = {}) => openApp(Object.assign({ path: '/', width: 1300, height: 900, wait: 4000 }, o));
const T = {};
const test = (name, fn) => { T[name] = fn; };
const SPRING_CFG = { TERM: '2274', TERM_LABEL: 'Spring 2027', NOW_TERM: '2268', NOW_LABEL: 'Fall 2026', NOW_UNTIL: '2027-01-25' };
function springTables() {
  const t = JSON.parse(JSON.stringify(FX.TABLES));
  t.course_seats = t.course_seats.concat(t.course_seats.filter(r => r.course_code !== 'BUS 3438').map(r => Object.assign({}, r, { term: '2274' })));
  return t;
}
const dark = `try{localStorage.setItem('professify-theme','dark')}catch(e){}`;
const open = async page => { await page.evaluate(() => { try { closeReviewLanding && closeReviewLanding(); } catch (e) {} show('explore'); renderExContext(); }); await tick(page, 800); };
const BAR = () => {
  const r = e => e && e.getBoundingClientRect();
  const bar = document.querySelector('#view-explore .ex-bar'), tabs = [...document.querySelectorAll('#exContext .ex-gesw button')];
  const sw = [...document.querySelectorAll('#exContext .ex-termsw')], seg = document.querySelector('.ex-seg-v'), q = document.querySelector('.ex-spot');
  const cs = tabs.length ? getComputedStyle(tabs.find(b => b.classList.contains('on')) || tabs[0]) : null;
  const cs0 = tabs.length ? getComputedStyle(tabs.find(b => !b.classList.contains('on')) || tabs[0]) : null;
  return {
    inBar: !!bar && !!bar.contains(document.getElementById('exContext')) && !!bar.contains(seg), tabs: tabs.map(b => b.textContent.trim() + (b.getAttribute('aria-pressed') === 'true' ? '*' : '')).join('|'),
    pills: [...document.querySelectorAll('#exContext .ex-term, #exContext .ex-tsep')].length,
    swN: sw.length, swTxt: sw[0] ? sw[0].textContent.trim() : null, swSvg: !!(sw[0] && sw[0].querySelector('svg')), swAria: sw[0] && sw[0].getAttribute('aria-label'), swTitle: sw[0] && sw[0].title, swDt: sw[0] && sw[0].getAttribute('data-term'),
    swColor: sw[0] && getComputedStyle(sw[0]).color, swWt: sw[0] && +getComputedStyle(sw[0]).fontWeight, swBg: sw[0] && getComputedStyle(sw[0]).backgroundColor,
    tabBg: cs && cs.backgroundColor, tabRad: cs && cs.borderTopLeftRadius, tabLine: cs && cs.borderBottomWidth, tabLine0: cs0 && cs0.borderBottomWidth, tabBorderSide: cs && cs.borderLeftWidth,
    tabH: tabs[0] && r(tabs[0]).height, swH: sw[0] && r(sw[0]).height,
    ys: { tabs: tabs[0] && Math.round(r(tabs[0]).top + r(tabs[0]).height / 2), sw: sw[0] && Math.round(r(sw[0]).top + r(sw[0]).height / 2), seg: seg && Math.round(r(seg).top + r(seg).height / 2) },
    xs: { tabsR: tabs.length && Math.round(r(tabs[tabs.length - 1]).right), sw: sw[0] && Math.round(r(sw[0]).left), segL: seg && Math.round(r(seg).left), segR: seg && Math.round(r(seg).right), barR: bar && Math.round(r(bar).right) },
    segTop: seg && Math.round(r(seg).top), tabsBottom: tabs[0] && Math.round(r(tabs[0]).bottom), qBottom: q && Math.round(r(q).bottom), qW: q && Math.round(r(q).width), barW: bar && Math.round(r(bar).width),
    /* the page itself is 4px wider than a phone from the header (avatar button) before and after this change; judge Explore's own content */
    scrollW: document.getElementById('view-explore').scrollWidth, clientW: document.documentElement.clientWidth,
    segTxt: [...document.querySelectorAll('.ex-seg-v button')].map(b => b.textContent.trim() + (b.getAttribute('aria-pressed') === 'true' ? '*' : '')).join('|'),
  };
};

test('single', async () => {
  const { page, close, log } = await desk({ init: dark }); await tick(page, 1500); await open(page);
  const b = await page.evaluate(BAR);
  ok(b.inBar && b.swN === 0 && b.pills === 0, 'single term: the row has the tabs and the toggle, no term switch', b);
  ok(/^GEs\|My major\*?\|Saved$|^GEs\|My major\|Saved\*$/.test(b.tabs.replace('My major*', 'My major')) || b.tabs.split('|').length === 3, 'single term: three tabs GEs / My major / Saved', b.tabs);
  ok(b.xs.segR >= b.xs.barR - 2 && Math.abs(b.ys.tabs - b.ys.seg) < 24, 'single term: the toggle is at the right end of the same row', b);
  ok(log.errors.length === 0, 'single term: no page errors', log.errors);
  await close();
});

test('row', async () => {
  const { page, close, log } = await desk({ terms: SPRING_CFG, tables: springTables(), init: dark }); await tick(page, 2500); await open(page);
  let b = await page.evaluate(BAR);
  ok(b.inBar, 'row: the tabs, the term and the toggle are one row (.ex-bar) under the search', b);
  ok(b.pills === 0 && b.swN === 1 && b.swTxt === 'Spring 2027' && b.swSvg && b.swDt === 'spring', 'row: the term is ONE switch: “Spring 2027” + the up/down icon, no pills', b);
  ok(/^Showing Spring 2027\. Switch to Fall 2026$/.test(b.swAria) && b.swTitle === 'Switch to Fall 2026', 'row: the switch says what it shows and what a tap does (aria-label + tooltip)', b);
  ok(b.swWt >= 700 && b.swBg === 'rgba(0, 0, 0, 0)', 'row: the term is plain bold words — no pill background', b);
  ok(b.tabBg === 'rgba(0, 0, 0, 0)' && b.tabRad === '0px' && b.tabBorderSide === '0px', 'row: the tabs are plain text — no pill background, radius or border', b);
  ok(b.tabLine === '2px' && b.tabLine0 === '2px', 'row: every tab holds a 2px underline slot', b);
  ok(await page.evaluate(() => { const on = document.querySelector('#exContext .ex-gesw button.on'), off = document.querySelector('#exContext .ex-gesw button:not(.on)'); return getComputedStyle(on).borderBottomColor !== getComputedStyle(off).borderBottomColor && getComputedStyle(off).borderBottomColor === 'rgba(0, 0, 0, 0)' || getComputedStyle(off).borderBottomColor.indexOf(', 0)') > 0; }), 'row: only the active tab shows its underline', null);
  ok(Math.abs(b.ys.tabs - b.ys.sw) < 12 && Math.abs(b.ys.tabs - b.ys.seg) < 24, 'row: tabs, term and toggle sit on ONE line', b.ys);
  ok(b.xs.tabsR < b.xs.sw && b.xs.sw < b.xs.segL && b.xs.segR >= b.xs.barR - 2, 'row: tabs on the left, then the term, then the toggle at the right edge', b.xs);
  ok(b.qW === b.barW, 'row: the search field is full width (the toggle no longer takes a column beside it)', { q: b.qW, bar: b.barW });
  ok(b.segTxt === 'Classes*|Professors', 'row: Classes | Professors toggle, Classes on', b.segTxt);
  /* tabs: the existing filters */
  const tab = name => page.evaluate(n => [...document.querySelectorAll('#exContext .ex-gesw button')].find(x => x.textContent.trim() === n).click(), name);
  await tab('GEs'); await tick(page, 500);
  b = await page.evaluate(BAR);
  ok(await page.evaluate(() => exMode) === 'ge' && /^GEs\*\|/.test(b.tabs) && b.swN === 1 && b.swTxt === 'Spring 2027', 'tabs: GEs filters to GEs (aria-pressed on the tab), the term switch stays', b.tabs);
  await tab('Saved'); await tick(page, 500);
  ok(await page.evaluate(() => !!window.exSaved) && /Saved\*$/.test((await page.evaluate(BAR)).tabs), 'tabs: Saved shows what you kept (aria-pressed)', null);
  await page.evaluate(() => document.getElementById('ex-profs').click()); await tick(page, 500);
  b = await page.evaluate(BAR);
  ok(await page.evaluate(() => exMode) === 'professors' && b.segTxt === 'Classes|Professors*' && /^My major|^All professors/.test(b.tabs) && b.tabs.split('|').length === 2 && b.swN === 1, 'toggle: Professors → the professor tabs (My major · Saved), toggle and term unchanged', b);
  const thumb = await page.evaluate(() => { const t = document.querySelector('.ex-seg-thumb').getBoundingClientRect(), p = document.getElementById('ex-profs').getBoundingClientRect(); return { dl: Math.abs(t.left - p.left), dw: Math.abs(t.width - p.width) }; });
  ok(thumb.dl < 8 && thumb.dw < 8, 'toggle: the highlight sits under Professors', thumb);
  await page.evaluate(() => document.getElementById('ex-classes').click()); await tick(page, 500);
  await tab('GEs'); await tick(page, 300);
  /* the term: one tap flips, Fall hides Saved, reads once */
  await page.evaluate(() => document.querySelector('#exContext .ex-termsw').click()); await tick(page, 1500);
  b = await page.evaluate(BAR);
  ok(b.swN === 1 && b.swTxt === 'Fall 2026' && b.swDt === 'now' && /^Showing Fall 2026\. Switch to Spring 2027$/.test(b.swAria), 'term: one tap flips Spring 2027 → Fall 2026 (label, aria, data-term)', b);
  ok(!/Saved/.test(b.tabs) && b.tabs.split('|').length === 2, 'term: Fall has no Saved tab (it is read-only)', b.tabs);
  ok(await page.evaluate(() => fallActive() && exTermSel === 'now'), 'term: Explore is on Fall (exTermSel = now)', null);
  await page.evaluate(() => document.querySelector('#exContext .ex-termsw').click()); await tick(page, 800);
  b = await page.evaluate(BAR);
  ok(b.swTxt === 'Spring 2027' && /Saved/.test(b.tabs) && await page.evaluate(() => exTermSel) === 'spring', 'term: and back to Spring 2027 (Saved is back)', b);
  /* keyboard */
  await page.evaluate(() => document.querySelector('#exContext .ex-termsw').focus());
  await page.keyboard.press('Enter'); await tick(page, 1200);
  ok(await page.evaluate(() => exTermSel) === 'now' && (await page.evaluate(BAR)).swTxt === 'Fall 2026', 'keyboard: Enter on the focused switch flips the term', null);
  await page.evaluate(() => document.querySelector('#exContext .ex-termsw').focus());
  await page.keyboard.press('Space'); await tick(page, 800);
  ok(await page.evaluate(() => exTermSel) === 'spring', 'keyboard: Space flips it back', null);
  ok(await page.evaluate(() => { const b = document.querySelector('#exContext .ex-gesw button'); b.focus(); return document.activeElement === b; }), 'keyboard: the tabs are focusable buttons', null);
  ok(log.errors.length === 0, 'row: no page errors', log.errors);
  await close();
});

test('phone', async () => {
  const { page, close, log } = await desk({ width: 390, height: 844, terms: SPRING_CFG, tables: springTables(), init: dark }); await tick(page, 2500); await open(page);
  let b = await page.evaluate(BAR);
  ok(b.scrollW <= b.clientW, 'phone: Explore has no horizontal scroll of its own', { s: b.scrollW, c: b.clientW });
  ok(b.inBar && b.swN === 1 && b.pills === 0, 'phone: same single-switch bar', b);
  ok(Math.abs(b.ys.tabs - b.ys.sw) < 12, 'phone: the tabs and the term share the first line', b.ys);
  ok(b.segTop > b.tabsBottom && b.segTxt === 'Classes*|Professors', 'phone: the Classes | Professors toggle wraps onto the line under (full width)', { segTop: b.segTop, tabsBottom: b.tabsBottom });
  ok(b.tabH >= 40 && b.swH >= 40, 'phone: tabs and term are at least 40px tall touch targets', { t: b.tabH, s: b.swH });
  const out = await page.evaluate(() => [...document.querySelectorAll('#view-explore .ex-bar *')].filter(e => { const r = e.getBoundingClientRect(); return r.width && (r.right > innerWidth + 1 || r.left < -1); }).map(e => e.className || e.tagName));
  ok(out.length === 0, 'phone: nothing in the row sticks out of the screen', out);
  await page.evaluate(() => document.querySelector('#exContext .ex-termsw').click()); await tick(page, 1500);
  b = await page.evaluate(BAR);
  ok(b.swTxt === 'Fall 2026' && b.scrollW <= b.clientW && Math.abs(b.ys.tabs - b.ys.sw) < 12, 'phone: on Fall it still fits one line, no horizontal scroll', b);
  await page.evaluate(() => document.getElementById('ex-profs').click()); await tick(page, 600);
  b = await page.evaluate(BAR);
  ok(b.scrollW <= b.clientW && b.segTxt === 'Classes|Professors*', 'phone: Professors mode fits too', b);
  ok(log.errors.length === 0, 'phone: no page errors', log.errors);
  await close();
});

test('myclasses', async () => {
  const { page, close, log } = await desk({ terms: SPRING_CFG, tables: springTables(), init: dark }); await tick(page, 2500);
  await page.evaluate(() => { show('sched'); try { setSchedTab('mine'); } catch (e) {} mcSetTermView('term'); }); await tick(page, 800);
  const q = () => page.evaluate(() => { const t = document.querySelector('#watchMineOut > .mc-terms'), b = t && t.querySelectorAll('button');
    return { n: b ? b.length : 0, txt: b && b[0] ? b[0].textContent.trim() : null, svg: !!(b && b[0] && b[0].querySelector('svg')), aria: b && b[0] && b[0].getAttribute('aria-label'), dt: b && b[0] && b[0].getAttribute('data-term'),
      pills: document.querySelectorAll('#watchMineOut .mc-viewtog.mc-terms').length, note: (document.querySelector('.mc-now-note') || {}).textContent || '', add: !!document.querySelector('#watchMineOut .mc-addbtn'),
      title: (document.getElementById('schedTerm') || {}).textContent, bg: b && b[0] && getComputedStyle(b[0]).backgroundColor, wt: b && b[0] && +getComputedStyle(b[0]).fontWeight }; });
  let m = await q();
  ok(m.n === 1 && m.pills === 0 && m.txt === 'Spring 2027' && m.svg && m.dt === 'term' && /^Showing Spring 2027\. Switch to Fall 2026$/.test(m.aria) && m.bg === 'rgba(0, 0, 0, 0)' && m.wt >= 700, 'my classes: ONE term switch (Spring 2027 + icon, no pills) over the Spring list', m);
  ok(m.add && m.title === 'Spring 2027', 'my classes: Spring is the list you add to', m);
  await page.evaluate(() => document.querySelector('#watchMineOut > .mc-terms button').click()); await tick(page, 800);
  m = await q();
  ok(m.n === 1 && m.txt === 'Fall 2026' && m.dt === 'now' && /^Showing Fall 2026\. Switch to Spring 2027$/.test(m.aria), 'my classes: one tap flips to Fall 2026', m);
  ok(/What you’re in now\. Read-only here — Spring 2027 is where you add classes\./.test(m.note) && !m.add && m.title === 'Fall 2026', 'my classes: the line under it explains Fall (read-only; Spring is where you add)', m);
  await page.evaluate(() => document.querySelector('#watchMineOut > .mc-terms button').click()); await tick(page, 800);
  m = await q();
  ok(m.txt === 'Spring 2027' && m.add && m.note === '' && m.title === 'Spring 2027', 'my classes: and back — the Spring list, with its Add controls', m);
  ok(await page.evaluate(() => localStorage.getItem('tc-mc-term-view')) === 'term', 'my classes: the pick is remembered', null);
  /* phone */
  await page.setViewportSize({ width: 390, height: 844 }); await tick(page, 600);
  ok(await page.evaluate(() => document.getElementById('view-sched').scrollWidth <= document.documentElement.clientWidth), 'my classes: phone width, nothing scrolls sideways', null);
  ok(log.errors.length === 0, 'my classes: no page errors', log.errors);
  await close();
});

/* the Classes | Professors highlight: the same neutral thumb in both states, label >= 4.5:1 on it, in both themes (the old purple Professors fill was 2:1) */
test('segContrast', async () => {
  for (const th of ['dark', 'light']) {
    const { page, close, log } = await desk({ terms: SPRING_CFG, tables: springTables(), init: `try{localStorage.setItem('professify-theme','${th}')}catch(e){}` }); await tick(page, 2500); await open(page);
    const read = () => page.evaluate(() => {
      const px = c => { const m = /rgba?\(([^)]+)\)/.exec(c)[1].split(',').map(Number); return m; };
      const L = a => { const f = v => { v /= 255; return v <= .03928 ? v / 12.92 : Math.pow((v + .055) / 1.055, 2.4); }; return .2126 * f(a[0]) + .7152 * f(a[1]) + .0722 * f(a[2]); };
      const k = (a, b) => { const x = L(a), y = L(b); return (Math.max(x, y) + .05) / (Math.min(x, y) + .05); };
      const th = document.querySelector('.ex-seg-thumb'), act = document.querySelector('.ex-seg-v button.active'), off = document.querySelector('.ex-seg-v button:not(.active)');
      const tb = getComputedStyle(th), bar = px(getComputedStyle(document.querySelector('.ex-seg-v')).backgroundColor);
      const page = px(getComputedStyle(document.body).backgroundColor);
      return { bg: tb.backgroundColor, ring: tb.boxShadow, on: +k(px(getComputedStyle(act).color), px(tb.backgroundColor)).toFixed(2), off: +k(px(getComputedStyle(off).color), page).toFixed(2), lab: act.textContent.trim() };
    });
    const a = await read();
    await page.evaluate(() => document.getElementById('ex-profs').click()); await tick(page, 600);
    const b = await read();
    ok(a.lab === 'Classes' && a.on >= 4.5 && b.lab === 'Professors' && b.on >= 4.5, th + ': the lit label reads on the highlight (≥ 4.5:1) in both states', { a, b });
    ok(a.bg === b.bg && b.bg !== 'rgb(124, 58, 237)' && b.bg !== 'rgb(183, 148, 255)', th + ': Professors uses the same neutral highlight as Classes (no purple fill)', { a: a.bg, b: b.bg });
    ok(/rgb/.test(a.ring) && a.ring !== 'none' && a.ring === b.ring, th + ': the highlight has a hairline ring so it shows on any background', { a: a.ring });
    ok(log.errors.length === 0, th + ': no page errors', log.errors);
    await close();
  }
});

/* focus rings are not clipped; the divider is its own element; a scrolling tab row fades at its right edge */
test('focus', async () => {
  const { page, close, log } = await desk({ width: 320, height: 700, terms: SPRING_CFG, tables: springTables(), init: dark }); await tick(page, 2500); await open(page);
  const f = await page.evaluate(() => {
    const g = document.querySelector('#exContext .ex-gesw'), b = g.querySelector('button'), cs = getComputedStyle(g), bc = getComputedStyle(b);
    const sw = document.querySelector('#exContext .ex-termsw'), dv = document.querySelector('#exContext .ex-tdiv');
    return { padL: parseFloat(cs.paddingLeft), padT: parseFloat(cs.paddingTop), ovx: cs.overflowX, bpad: bc.paddingLeft, ring: getComputedStyle(sw, '::after').content, dv: !!dv && dv.tagName === 'SPAN' && dv.getAttribute('aria-hidden') === 'true' && !sw.contains(dv), dvShown: dv && getComputedStyle(dv).display !== 'none',
      more: g.classList.contains('ex-more'), over: g.scrollWidth > g.clientWidth + 1, mask: cs.webkitMaskImage || cs.maskImage, first: Math.round(b.getBoundingClientRect().left - g.getBoundingClientRect().left) };
  });
  ok(f.padL >= 4 && f.padT >= 4, 'focus: the scrolling tab row keeps 4px around its tabs so the ring is not clipped (phone)', f);
  ok(f.dv && f.ring === 'none' || f.ring === 'normal', 'focus: the divider before the toggle is its own aria-hidden element, not inside the term button', f);
  ok(f.over ? (f.more && /gradient/.test(f.mask)) : (!f.more), '320px: while the tab row scrolls its right edge fades; when it fits there is no fade', f);
  if (f.over) {
    await page.evaluate(() => { const g = document.querySelector('#exContext .ex-gesw'); g.scrollLeft = g.scrollWidth; g.dispatchEvent(new Event('scroll')); });
    ok(await page.evaluate(() => !document.querySelector('#exContext .ex-gesw').classList.contains('ex-more')), '320px: scrolled to the end, the fade is gone', null);
  }
  await page.evaluate(() => document.querySelector('#exContext .ex-gesw button').focus());
  const ring = await page.evaluate(() => { const g = document.querySelector('#exContext .ex-gesw'), b = document.activeElement, r = b.getBoundingClientRect(), gr = g.getBoundingClientRect(), cs = getComputedStyle(b), reach = parseFloat(cs.outlineOffset) + parseFloat(cs.outlineWidth);
    return { reach, leftRoom: r.left - gr.left, topRoom: r.top - gr.top }; });
  ok(ring.leftRoom >= ring.reach && ring.topRoom >= ring.reach, 'focus: the first tab’s focus ring fits inside the scrolling row (phone)', ring);
  await page.setViewportSize({ width: 1300, height: 900 }); await tick(page, 600);
  const d = await page.evaluate(() => { const b = document.querySelector('#exContext .ex-gesw button'), t = document.querySelector('#exContext .ex-termsw');
    return { pad: getComputedStyle(b).paddingLeft, tpad: getComputedStyle(t).paddingLeft, fs: getComputedStyle(t).fontSize }; });
  ok(d.pad === '4px' && d.fs === '14px', 'focus: desktop tabs have 4px side padding; the term switch is 14px', d);
  ok(log.errors.length === 0, 'focus: no page errors', log.errors);
  await close();
});

test('lone', async () => {
  const { page, close, log } = await desk({ terms: SPRING_CFG, tables: springTables(), time: '2027-01-25T09:00:00-08:00', init: dark }); await tick(page, 1500); await open(page);
  ok((await page.evaluate(BAR)).swN === 0, 'from Jan 25: one term again, no switch in Explore', null);
  await page.evaluate(() => { show('sched'); try { setSchedTab('mine'); } catch (e) {} renderMyClasses(); }); await tick(page, 600);
  ok(!(await page.$('#watchMineOut > .mc-terms')), 'from Jan 25: no switch on My classes', null);
  ok(log.errors.length === 0, 'lone: no page errors', log.errors);
  await close();
});

for (const n of Object.keys(T)) {
  if (ONLY && ONLY !== n) continue;
  console.log('\n' + n);
  try { await T[n](); } catch (e) { fail++; fails.push(n + ' (threw)'); console.log('  FAIL', n, 'threw', e && e.stack ? e.stack.split('\n').slice(0, 3).join(' | ') : e); }
}
console.log('\n' + pass + ' passed, ' + fail + ' failed');
if (fail) { console.log('FAILED:\n  ' + fails.join('\n  ')); process.exit(1); }
