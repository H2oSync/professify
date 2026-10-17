/* check-desktop-sched-hover — Schedule > My classes and Schedule > Plans, 2026-10-16 (Tate: "make the my classes schedule longer
   vertically so the class names aren't as packed. also for plans add class names in them ... only show the professor and
   connector when you hover over a class ... also show the class's time in a simple and clean way").
   Runs the REAL index.html in Chromium, signed in, against the PostgREST stand-in.
   Run: APP_DIR=<repo> node check-desktop-sched-hover.mjs [--only name] [--quiet]   (APP_PORT to move off the default)
   The promises: My classes is taller on a desktop width (and ONLY there: a friend's week and the phone keep their scale), a block's name is
   never clipped; a Plans block shows code + name + time; nothing professor-shaped is drawn at rest; hovering (or keyboard focus on)
   a class shows that class's professor card, a connector to EVERY meeting, and one plain time line ("MW 12:10-2:00p"); the rest
   dim; a touch device draws nothing and a tap still opens the class; the friend profile still draws its own always-on layer. */
import { openApp } from './app-harness.mjs';
import * as FX from './app-fixtures.mjs';

const args = process.argv.slice(2);
const ONLY = args.includes('--only') ? args[args.indexOf('--only') + 1] : null;
const QUIET = args.includes('--quiet');
let pass = 0, fail = 0; const fails = [];
function ok(c, name, info) {
  if (c) { pass++; if (!QUIET) console.log('  ok  ', name); }
  else { fail++; fails.push(name); console.log('  FAIL', name, info !== undefined ? '→ ' + JSON.stringify(info).slice(0, 600) : ''); }
}
const tick = async (p, ms = 400) => { await p.clock.runFor(ms); await p.waitForTimeout(250); };
const NOW = '2026-10-14T10:30:00-07:00';
let portN = 0; const BASE = +(process.env.APP_PORT || (8300 + Math.floor(Math.random() * 500)));
const open = [];
const dark = `try{localStorage.setItem('professify-theme','dark')}catch(e){}`;
const desk = async (o = {}) => { const a = await openApp(Object.assign({ path: '/', width: 1300, height: 900, wait: 4000, time: NOW, port: BASE + (portN++ % 20), init: dark }, o)); open.push(a); return a; };
const T = {};
const test = (name, fn) => { T[name] = fn; };

const toMine = async page => { await page.evaluate(() => { show('sched'); try { setSchedTab('mine'); } catch (e) {} renderMyClasses(); try { if (myClassesView !== 'calendar') setMyClassesView('calendar'); } catch (e) {} }); await tick(page, 1500); };
const PLAN = ['BUS 3431', 'BUS 3438', 'BUS 4442', 'BUS 4445', 'BUS 3346'];
const toPlans = async page => {
  await page.evaluate(PLAN => {
    const list = []; PLAN.forEach(c => { const r = (SEAT_SECTIONS[c] || [])[0]; if (r) list.push({ code: c, class_nbr: String(r.class_nbr).trim() }); });
    TCPlans.setSections('A', list); show('sched'); setSchedTab('watch'); TCPlans.setCur('A');
  }, PLAN); await tick(page, 1500);
};
const stray = page => page.evaluate(() => ({ hv: document.querySelectorAll('.hv-card,.hv-svg').length, hz: document.querySelectorAll('#schedMineWrap .hz-card,#schedMineWrap .hz-svg,#plansOut .hz-card,#plansOut .hz-svg').length, live: document.querySelectorAll('.hv-live').length, me: document.querySelectorAll('.hv-me').length }));

test('mine-rest', async () => {
  const { page, close, log } = await desk(); await tick(page, 1500); await toMine(page);
  const r = await page.evaluate(() => ({ blocks: document.querySelectorAll('.mc-cal .cal-block[data-code]').length, host: document.querySelector('.mc-cal').getAttribute('data-hv'), foot: !!document.querySelector('.mc-cal .hz-foot.in') }));
  ok(r.blocks >= 8 && r.host === 'mc', 'My classes week is drawn and is a hover host', r);
  const s = await stray(page);
  ok(s.hv === 0 && s.hz === 0 && s.live === 0 && s.me === 0, 'at rest: no professor card, no connector, nothing dimmed (the old always-on layer is gone from My classes)', s);
  ok(r.foot, 'the average line under the week is still there');
  ok(await page.evaluate(() => { const h = document.querySelector('.mc-cal').getBoundingClientRect(), w = document.querySelector('.mc-cal .cal-wrap').getBoundingClientRect(); return Math.abs(h.right - w.right) <= 2; }), 'no margin is reserved: the week panel runs the full width, level with the buttons above it');
  ok(log.errors.length === 0, 'no page errors', log.errors); await close();
});

test('mine-taller', async () => {
  const { page, close } = await desk(); await tick(page, 1500); await toMine(page);
  const r = await page.evaluate(() => {
    const own = renderMyCalendar(myClasses.slice(), { bad: {} }, undefined, { cm: 'me' }), other = renderMyCalendar(myClasses.slice(), { bad: {} }, undefined, {});
    const h = s => +(/class="cal-day" style="height:([\d.]+)px/.exec(s) || [])[1];
    const blocks = [...document.querySelectorAll('.mc-cal .cal-block[data-s]')].map(b => {
      const nm = b.querySelector('.cb-nm'), c = b.querySelector('.cb-nmc');
      return { code: b.getAttribute('data-code'), h: b.offsetHeight, over: b.scrollHeight - b.clientHeight, nmOver: nm ? nm.scrollHeight - nm.clientHeight : 0, cOver: c ? c.scrollHeight - c.clientHeight : 0, lines: c ? Math.round(c.clientHeight / parseFloat(getComputedStyle(c).lineHeight)) : 0 };
    });
    return { own: h(own), other: h(other), blocks, win: innerWidth };
  });
  ok(r.own >= 780 && Math.round(r.other) === 504 && r.own / r.other > 1.5, 'your week is taller (' + r.own + 'px vs ' + r.other + 'px), a week drawn for anyone else keeps 504px', r);
  ok(r.blocks.length >= 8 && r.blocks.every(b => b.over <= 1 && b.nmOver <= 1), 'no block clips its code or its name', r.blocks.filter(b => b.over > 1 || b.nmOver > 1));
  /* the case that started this: a 50-minute class (TuTh 10:10-11:00) must hold its code AND a two-line name, the second line ending in an ellipsis */
  const f = await page.evaluate(() => {
    const m = { 'BUS 4442': { secs: [{ crn: '1', days: 'MoWeFr 10:10AM - 11:00AM', prof: 'Ada Examplewood' }] } };
    const host = document.createElement('div'); host.style.cssText = 'position:absolute;left:0;top:0;width:900px'; host.innerHTML = renderMyCalendar(['BUS 4442'], { bad: {} }, m, { cm: 'me' }); document.body.appendChild(host);
    const b = host.querySelector('.cal-block[data-s]'), nm = b.querySelector('.cb-nm'), c = b.querySelector('.cb-nmc');
    const o = { h: Math.round(b.offsetHeight), over: b.scrollHeight - b.clientHeight, nmOver: nm.scrollHeight - nm.clientHeight, lines: Math.round(nm.clientHeight / parseFloat(getComputedStyle(c).lineHeight)), text: c.textContent };
    host.remove(); return o;
  });
  ok(f.h >= 46 && f.over <= 1 && f.nmOver <= 1 && f.lines === 2, 'a 50-minute class is ' + f.h + 'px: code + two lines of name, nothing cut off', f);
  await close();
});

test('mine-hover', async () => {
  const { page, close, log } = await desk(); await tick(page, 1500); await toMine(page);
  const sel = '.mc-cal .cal-block[data-code="BUS 4442"]';
  await page.hover(sel); await tick(page, 400);
  const r = await page.evaluate(() => {
    const c = document.querySelector('.mc-cal .hv-card'), host = document.querySelector('.mc-cal');
    const lit = [...host.querySelectorAll('.cal-block.hv-me')].map(b => b.getAttribute('data-code') + ':' + b.getAttribute('data-d'));
    const dim = [...host.querySelectorAll('.cal-block[data-code]:not(.hv-me)')].map(b => +getComputedStyle(b).opacity);
    const cr = c && c.getBoundingClientRect(), hr = host.getBoundingClientRect(), g = host.querySelector('.cal-wrap').getBoundingClientRect();
    return { text: c && c.innerText.replace(/\s+/g, ' ').trim(), paths: host.querySelectorAll('.hv-svg path').length, dots: host.querySelectorAll('.hv-svg circle').length,
      lit, dimMax: Math.max.apply(null, dim), dimN: dim.length, inside: !!cr && cr.left >= g.left - 1 && cr.right <= g.right + 1 && cr.top >= g.top - 1 && cr.bottom <= g.bottom + 1, overlap: !!cr && [...host.querySelectorAll('.cal-block')].filter(b => { const r = b.getBoundingClientRect(); return cr.left < r.right && cr.right > r.left && cr.top < r.bottom && cr.bottom > r.top; }).length, live: host.classList.contains('hv-live') };
  });
  ok(/Examplewood, Ada/.test(r.text || '') && /4\.5\/5/.test(r.text) && /BUS 4442/.test(r.text), 'the professor card names the professor, the rating and the class', r.text);
  ok(/MW 12:10–2:00p$/.test(r.text || ''), 'the time is one plain line: "MW 12:10–2:00p"', r.text);
  ok(r.paths === 2 && r.dots === 2, 'one connector to EVERY meeting of the class (Mon and Wed)', r);
  ok(r.lit.length === 2 && r.lit.every(x => x.startsWith('BUS 4442')), 'both meetings of that class are lit, nothing else', r.lit);
  ok(r.dimN >= 6 && r.dimMax < 0.9, 'every other block is dimmed', { max: r.dimMax, n: r.dimN });
  ok(r.inside && r.overlap === 0 && r.live, 'the card sits inside the week panel in an empty spot, on top of no class', r);
  /* a different class, a different card */
  await page.hover('.mc-cal .cal-block[data-code="BUS 3438"]'); await tick(page, 300);
  const t2 = await page.evaluate(() => document.querySelector('.mc-cal .hv-card').innerText.replace(/\s+/g, ' ').trim());
  ok(/Fixturesen, Bram/.test(t2) && /MW 10:10a–12:00p$/.test(t2) && (await page.$$('.mc-cal .hv-card')).length === 1, 'moving to another class swaps the card (one card at a time)', t2);
  /* a class with no listed instructor, or a TBA one, still gets its time */
  await page.mouse.move(5, 5); await tick(page, 300);
  const s = await stray(page);
  ok(s.hv === 0 && s.live === 0 && s.me === 0, 'moving off the week clears everything', s);
  const nodim = await page.evaluate(() => [...document.querySelectorAll('.mc-cal .cal-block')].every(b => getComputedStyle(b).opacity === '1'));
  ok(nodim, 'and nothing stays dimmed');
  await page.hover('.mc-cal .cal-block.cal-tbablk'); await tick(page, 300);
  const tba = await page.evaluate(() => { const c = document.querySelector('.mc-cal .hv-card'); return c && c.innerText.replace(/\s+/g, ' ').trim(); });
  ok(/Time TBA$/.test(tba || ''), 'a class with no time says "Time TBA" in the same place', tba);
  ok(log.errors.length === 0, 'no page errors', log.errors); await close();
});

test('mine-keyboard-click', async () => {
  const { page, close, log } = await desk(); await tick(page, 1500); await toMine(page);
  await page.evaluate(() => { window.__taps = []; const o = window.cbTap; window.cbTap = function () { window.__taps.push([].slice.call(arguments).join('|')); return o.apply(this, arguments); }; });
  await page.focus('.mc-cal .cal-block[data-code="BUS 4445"]'); await page.keyboard.press('Shift+Tab'); await page.keyboard.press('Tab'); await tick(page, 300);
  const f = await page.evaluate(() => ({ on: document.activeElement && document.activeElement.getAttribute('data-code'), text: (document.querySelector('.mc-cal .hv-card') || {}).innerText, vis: !!document.activeElement && document.activeElement.matches(':focus-visible') }));
  ok(f.on === 'BUS 4445' && f.vis && /Dummelow, Faro/.test(f.text || '') && /MW 2:10–4:00p/.test((f.text || '').replace(/\s+/g, ' ')), 'keyboard focus on a class shows the same card and time as hovering', f);
  await page.keyboard.press('Escape'); await tick(page, 200);
  ok((await stray(page)).hv === 0, 'Escape puts it away');
  await page.keyboard.press('Shift+Tab'); await page.keyboard.press('Tab'); await tick(page, 200);
  await page.keyboard.press('Tab'); await tick(page, 200);
  /* click: still opens the class exactly as before, and the overlay is gone by then */
  await page.hover('.mc-cal .cal-block[data-code="BUS 4442"]'); await tick(page, 300);
  await page.click('.mc-cal .cal-block[data-code="BUS 4442"]'); await tick(page, 600);
  const c = await page.evaluate(() => ({ taps: window.__taps.slice(), strays: document.querySelectorAll('.hv-card,.hv-svg').length }));
  ok(c.taps.length >= 1 && c.taps[c.taps.length - 1].startsWith('BUS 4442'), 'clicking a class still calls the same cbTap (opens the class)', c);
  ok(c.strays === 0, 'and the overlay is cleared when it does', c);
  ok(log.errors.length === 0, 'no page errors', log.errors); await close();
});

test('touch', async () => {
  const { page, close, log } = await desk({ touch: true }); await tick(page, 1500); await toMine(page);
  const r = await page.evaluate(() => ({ hover: matchMedia('(hover: hover)').matches, gut: document.querySelector('.mc-cal').classList.contains('hv-gut') }));
  ok(!r.hover, 'the browser reports no hover (touch)', r);
  ok(!r.gut, 'no margin on a touch device either', r);
  await page.evaluate(() => { window.__taps = []; const o = window.cbTap; window.cbTap = function () { window.__taps.push([].slice.call(arguments).join('|')); return o.apply(this, arguments); }; });
  await page.tap('.mc-cal .cal-block[data-code="BUS 4442"]'); await tick(page, 500);
  const t = await page.evaluate(() => ({ taps: window.__taps.slice(), strays: document.querySelectorAll('.hv-card,.hv-svg').length }));
  ok(t.taps.length === 1 && t.taps[0].startsWith('BUS 4442') && t.strays === 0, 'a tap opens the class once and draws nothing', t);
  ok(log.errors.length === 0, 'no page errors', log.errors); await close();
});

test('plans', async () => {
  const { page, close, log } = await desk(); await tick(page, 1500); await toPlans(page);
  const r = await page.evaluate(() => [...document.querySelectorAll('#plansOut .pl3-week .pl3-blk[data-code]')].map(b => {
    const code = b.querySelector('b'), nm = b.querySelector('.pl3-nm'), tm = b.querySelector('.pl3-tm'), w = b.querySelector('.pl3-nmw');
    return { code: code.innerText, nm: nm.innerText, nmShown: getComputedStyle(w).display !== 'none', tm: tm.innerText, over: b.scrollHeight - b.clientHeight, h: b.offsetHeight,
      lines: getComputedStyle(w).display === 'none' ? 0 : Math.round(w.clientHeight / parseFloat(getComputedStyle(nm).lineHeight)) };
  }));
  ok(r.length >= 8, 'the plan week draws its blocks', r.length);
  ok(r.every(b => b.nm.length > 3 && b.nmShown && /\d(am|pm)–/.test(b.tm)), 'every block shows code + class name + time', r.slice(0, 3));
  ok(r.every(b => b.over <= 1), 'nothing is clipped inside a block', r.filter(b => b.over > 1));
  ok(r.filter(b => b.h >= 80).every(b => b.lines === (b.nm.length > 24 ? 2 : 1)), 'a block with room shows its whole name: two lines when it needs two', r.map(b => b.code + ':' + b.h + ':' + b.lines));
  const g = await page.evaluate(() => ({ h: document.querySelector('#plansOut .pl3-week .pl3-grid').offsetHeight, hrs: getComputedStyle(document.querySelector('#plansOut .pl3-week')).getPropertyValue('--pl3-hrs') }));
  ok(g.h === 800 && +g.hrs === 10, 'the week is 80px an hour on a laptop (10 hours = 800px)', g);
  ok((await stray(page)).hv === 0, 'at rest: no professor card, no connector');
  await page.hover('#plansOut .pl3-week .pl3-blk[data-code="BUS 3346"]'); await tick(page, 400);
  const h = await page.evaluate(() => { const c = document.querySelector('#plansOut .pl3-week .hv-card'), host = document.querySelector('#plansOut .pl3-week'); return { text: c && c.innerText.replace(/\s+/g, ' ').trim(), paths: host.querySelectorAll('.hv-svg path').length, lit: host.querySelectorAll('.pl3-blk.hv-me').length, dim: +getComputedStyle(host.querySelector('.pl3-blk:not(.hv-me)')).opacity, inside: (() => { const r = c.getBoundingClientRect(), b = host.getBoundingClientRect(); return r.left >= b.left && r.right <= b.right && r.top >= b.top && r.bottom <= b.bottom; })(), overlap: [...host.querySelectorAll('.pl3-blk')].filter(x => { const r = x.getBoundingClientRect(), k = c.getBoundingClientRect(); return k.left < r.right && k.right > r.left && k.top < r.bottom && k.bottom > r.top; }).length }; });
  ok(/Dummelow/.test(h.text || '') && /MW 8:10–9:30a$/.test(h.text || ''), 'hovering a plan block shows the professor and "MW 8:10–9:30a"', h);
  ok(h.paths === 2 && h.lit === 2 && h.dim < 0.9 && h.overlap === 0 && h.inside, 'a connector to both meetings, the rest dim, the card in an empty spot of the panel', h);
  await page.mouse.move(5, 5); await tick(page, 300);
  ok((await stray(page)).hv === 0 && (await stray(page)).me === 0, 'moving off clears it');
  /* a click on a plan block still does what it did */
  await page.evaluate(() => { window.__opens = 0; document.addEventListener('click', e => { const b = e.target.closest && e.target.closest('.pl3-blk[data-pl-act="open"]'); if (b) window.__opens++; }, true); });
  await page.click('#plansOut .pl3-week .pl3-blk[data-code="BUS 4442"]'); await tick(page, 500);
  ok((await page.evaluate(() => window.__opens)) === 1 && (await stray(page)).hv === 0, 'a click on a plan block reaches the same handler and clears the overlay');
  /* the Builder's week (edit mode) is not a hover host and keeps its height */
  ok(await page.evaluate(() => !document.querySelector('.pl3-week--edit') || !document.querySelector('.pl3-week--edit').hasAttribute('data-hv')), 'the Builder week is not touched');
  ok(log.errors.length === 0, 'no page errors', log.errors); await close();
});

test('plans-empty', async () => {
  const { page, close } = await desk(); await tick(page, 1500);
  await page.evaluate(() => { show('sched'); TCPlans.setSections('C', []); setSchedTab('watch'); TCPlans.setCur('C'); }); await tick(page, 1200);
  const r = await page.evaluate(() => ({ host: document.querySelector('#plansOut .pl3-week').hasAttribute('data-hv'), gut: document.querySelector('#plansOut .pl3-week').classList.contains('hv-gut'), empty: !!document.querySelector('.pl3-empty') }));
  ok(r.empty && !r.host && !r.gut, 'an empty plan keeps its full-width empty state (no hover host, no margin)', r);
  await close();
});

/* every hover at several widths: the card is always inside the panel and never on a class */
for (const W of [1100, 1000, 800]) {
  test('widths-' + W, async () => {
    const { page, close, log } = await desk({ width: W }); await tick(page, 1500); await toMine(page);
    const probe = async (host, blk, sel) => page.evaluate(([host, blk, sel]) => {
      const h = document.querySelector(host), c = h.querySelector('.hv-card'); if (!c) return { none: true };
      const k = c.getBoundingClientRect(), p = h.querySelector(sel).getBoundingClientRect();
      return { inside: k.left >= p.left - 1 && k.right <= p.right + 1 && k.top >= p.top - 1 && k.bottom <= p.bottom + 1,
        overlap: [...h.querySelectorAll(blk)].filter(x => { const r = x.getBoundingClientRect(); return k.left < r.right && k.right > r.left && k.top < r.bottom && k.bottom > r.top; }).length };
    }, [host, blk, sel]);
    const codes = ['BUS 3438', 'BUS 4442', 'BUS 4445', 'BUS 3431'];
    for (const c of codes) { await page.hover('.mc-cal .cal-block[data-code="' + c + '"]'); await tick(page, 250);
      const r = await probe('.mc-cal', '.cal-block', '.cal-wrap');
      ok(!r.none && r.inside && r.overlap === 0, W + 'px, My classes ' + c + ': the card is inside the panel and covers no class', r); }
    await page.mouse.move(5, 5); await tick(page, 200);
    await toPlans(page);
    for (const c of ['BUS 3346', 'BUS 4442', 'BUS 3431']) { await page.hover('#plansOut .pl3-week .pl3-blk[data-code="' + c + '"]'); await tick(page, 250);
      const r = await probe('#plansOut .pl3-week', '.pl3-blk', '.pl3-grid');
      ok(!r.none && r.inside && r.overlap === 0, W + 'px, Plans ' + c + ': the card is inside the panel and covers no class', r); }
    ok(log.errors.length === 0, 'no page errors', log.errors); await close();
  });
}

test('resize', async () => {
  const { page, close, log } = await desk(); await tick(page, 1500); await toMine(page);
  await page.hover('.mc-cal .cal-block[data-code="BUS 4442"]'); await tick(page, 300);
  ok((await page.$$('.mc-cal .hv-card')).length === 1, 'a card is open');
  await page.setViewportSize({ width: 1100, height: 900 }); await tick(page, 700);
  ok((await stray(page)).hv === 0, 'resizing the window with a card open clears it (no stale card or lines)');
  await page.mouse.move(2, 2); await page.hover('.mc-cal .cal-block[data-code="BUS 4442"]'); await tick(page, 300);
  ok((await page.$$('.mc-cal .hv-card')).length === 1, 'and it comes back on the next hover');
  /* the tall week follows the window: under 640px it is drawn at the phone scale, over it the tall one again */
  const day = () => page.evaluate(() => Math.round(document.querySelector('.mc-cal .cal-day').offsetHeight));
  ok(await day() > 800, 'at 1100px the week is the tall one', await day());
  await page.setViewportSize({ width: 500, height: 900 }); await tick(page, 900);
  const small = await day();
  ok(small < 600, 'crossing under 640px draws the phone scale', small);
  await page.setViewportSize({ width: 1200, height: 900 }); await tick(page, 900);
  const big = await day();
  ok(big > 800, 'and back over it draws the tall week again', big);
  ok(log.errors.length === 0, 'no page errors', log.errors); await close();
});

test('friend-profile', async () => {
  const { page, close, log } = await desk(); await tick(page, 1500);
  await page.evaluate(id => openFriendProfile(id), FX.FRIENDS[0].id); await tick(page, 1500);
  if (!(await page.$('.frp-cal'))) { await page.evaluate(() => setFrpView('cal')); await tick(page, 1500); }
  const r = await page.evaluate(() => { const c = document.querySelector('.frp-cal'); return c && { cards: c.querySelectorAll('.hz-card').length, svg: c.querySelectorAll('.hz-svg').length, hv: c.querySelectorAll('.hv-svg,.hv-card').length, hasHv: c.hasAttribute('data-hv'), dayH: c.querySelector('.cal-day').offsetHeight }; });
  ok(r && r.cards >= 1 && r.svg === 1 && r.hv === 0 && !r.hasHv, 'the friend profile still draws its own always-on professor wires, untouched', r);
  ok(r && r.dayH === 504, 'and keeps its week scale (504px)', r);
  ok(log.errors.length === 0, 'no page errors', log.errors); await close();
});

test('phone', async () => {
  const { page, close, log } = await desk({ width: 390, height: 844 }); await tick(page, 1500); await toMine(page);
  const m = await page.evaluate(() => ({ day: document.querySelector('.mc-cal .cal-day').offsetHeight, gut: document.querySelector('.mc-cal').classList.contains('hv-gut'), over: document.documentElement.scrollWidth - innerWidth, hv: document.querySelectorAll('.hv-card,.hv-svg').length }));
  ok(m.day > 500 && m.day < 700 && !m.gut && m.over <= 0 && m.hv === 0, 'phone: My classes is the phone-sized taller week (phone-sched, 2026-10-16), reserves no margin, no sideways scroll', m);
  await toPlans(page);
  const p = await page.evaluate(() => ({ grid: document.querySelector('#plansOut .pl3-week .pl3-grid').offsetHeight, nm: [...document.querySelectorAll('#plansOut .pl3-week .pl3-nmw')].every(w => getComputedStyle(w).display !== 'none'), gut: document.querySelector('#plansOut .pl3-week').classList.contains('hv-gut'), over: document.documentElement.scrollWidth - innerWidth }));
  ok(p.grid === 560 && p.nm && !p.gut && p.over <= 0, 'phone: Plans is 56px an hour (560px for 10h) with the class names in (phone-sched, 2026-10-16), no margin, no sideways scroll', p);
  ok(log.errors.length === 0, 'no page errors', log.errors); await close();
});

test('light-theme', async () => {
  const { page, close } = await desk({ init: `try{localStorage.setItem('professify-theme','light')}catch(e){}` }); await tick(page, 1500); await toMine(page);
  await page.hover('.mc-cal .cal-block[data-code="BUS 4442"]'); await tick(page, 300);
  const r = await page.evaluate(() => { const c = document.querySelector('.mc-cal .hv-card'), when = c.querySelector('.hv-when'); const rgb = s => s.match(/[\d.]+/g).map(Number); const L = a => { const f = v => { v /= 255; return v <= .03928 ? v / 12.92 : Math.pow((v + .055) / 1.055, 2.4); }; return .2126 * f(a[0]) + .7152 * f(a[1]) + .0722 * f(a[2]); };
    const fg = rgb(getComputedStyle(when).color), bg = rgb(getComputedStyle(c).backgroundColor); const a = L(fg), b = L(bg); return { ratio: (Math.max(a, b) + .05) / (Math.min(a, b) + .05), theme: document.documentElement.getAttribute('data-theme') }; });
  ok(r.theme === 'light' && r.ratio >= 4.5, 'the time line holds 4.5:1 on the card in light', r);
  await close();
});

const names = ONLY ? [ONLY] : Object.keys(T);
for (const n of names) {
  if (!T[n]) { console.log('no such test', n); process.exit(2); }
  if (!QUIET) console.log('\n' + n);
  try { await T[n](); } catch (e) { fail++; fails.push(n + ' threw'); console.log('  FAIL', n, 'threw', String(e).slice(0, 400)); }
  for (const a of open.splice(0)) { try { await a.close(); } catch (e) {} }
}
console.log(`\ncheck-desktop-sched-hover: ${pass} passed, ${fail} failed`);
if (fail) { console.log('failed:', fails.join(' | ')); process.exit(1); }
