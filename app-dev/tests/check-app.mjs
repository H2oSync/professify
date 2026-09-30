/* check-app — the phone app (app/index.html) against synthetic fixtures, asserting on the RENDERED
   DOM and on the exact rows it writes. Run: node check-app.mjs [--only name] [--quiet]
   Exit code 1 on any failure. mutate.mjs runs this against deliberately broken copies. */
import { openApp } from './app-harness.mjs';
import * as FX from './app-fixtures.mjs';

const only = process.argv.includes('--only') ? process.argv[process.argv.indexOf('--only') + 1] : null;
const quiet = process.argv.includes('--quiet');
let pass = 0, fail = 0; const fails = [];
function ok(cond, name, info) { if (cond) { pass++; if (!quiet) console.log('  ok  ', name); } else { fail++; fails.push(name); console.log('  FAIL', name, info !== undefined ? '→ ' + JSON.stringify(info).slice(0, 300) : ''); } }
const text = p => p.locator('#scroll').innerText();
const settle = async (p, ms = 400) => { await p.clock.runFor(ms); await p.waitForTimeout(250); await p.clock.runFor(50); await p.waitForTimeout(100); };
const click = async (p, sel) => { await p.locator(sel).first().click(); await settle(p); };
/* The class page's + opens "Add to a plan"; this taps + (nth), optionally picks a plan, then Add/Remove. */
const addVia = async (p, nth = 0, k = null) => { await click(p, `.secrow .addbtn >> nth=${nth}`); if (k) await click(p, `#sheet [data-a="addPlanPick"][data-x="${k}"]`); const go = p.locator('#sheet [data-a="addPlanGo"]'); if (await go.count()) await click(p, '#sheet [data-a="addPlanGo"]'); };
const tick = (p, ms = 400) => settle(p, ms);
const tests = {};

/* The prototype's invented people and professors must never reach a screen. */
const PROTO = ['Garrett', 'Min Kim', 'Swstern', 'swstern', 'Maya Rios', 'Lehman', 'Greenbaum', 'Jabeast', 'Tristan', 'Surf Team', 'Finance Squad', 'Reset demo', 'Entrepreneurial Finance', 'Whitfield', 'termchamp.app/invite'];
const noProto = (t, where) => { const hit = PROTO.filter(w => t.includes(w)); ok(!hit.length, `no prototype data on ${where}`, hit); };

tests.signedOut = async () => {
  const { page, close, log } = await openApp({ signedIn: false });
  const t = await text(page);
  ok(!/Google/.test(t), 'signed out: no Google button (Google sign-in is off, as on the desktop)');
  ok(/Plan your next term, stress-free\./.test(t) && /Get started/.test(t) && /I already have an account/.test(t), 'signed out: Sean’s landing — get started or log in');
  ok(await page.locator('.onb .onb-hawk').count() === 1 && /^data:image\/webp/.test(await page.locator('.onb .onb-hawk').getAttribute('src')) && await page.locator('.onb svg[aria-label="Champ"]').count() === 0, 'signed out: our hawk, not the sketch’s bird');
  ok(await page.locator('.tabbar').count() === 0, 'signed out: no tab bar');
  ok(!log.reads.some(r => /^(my_sections|friend_requests|messages)/.test(r)), 'signed out: no private reads', log.reads);
  await click(page, '[data-a="siMode"][data-x="password"]');
  ok(await page.locator('#si-email').count() === 1 && await page.locator('#si-pw').count() === 1, 'password form shows');
  await page.locator('#si-email').fill('typing@calpoly.edu'); await page.locator('#si-pw').fill('half-typed');
  await page.evaluate(() => render(true));   // what a late seat or ratings load does
  ok(await page.locator('#si-email').inputValue() === 'typing@calpoly.edu' && await page.locator('#si-pw').inputValue() === 'half-typed', 'signed out: a background load doesn’t wipe what you’re typing');
  ok(log.errors.length === 0, 'signed out: no page errors', log.errors);
  await close();
};

tests.home = async () => {
  const { page, close, log } = await openApp({});
  await page.waitForFunction(() => document.querySelectorAll('.hfeed .fcard').length === 5 && TC.ready, null, { timeout: 8000 });
  const t = await text(page);
  noProto(t, 'Home');
  const stories = await page.locator('.story .nm').allInnerTexts();
  ok(stories.length === 5 && !stories.includes('You') && stories.includes('Avery') && stories.includes('Harper'), 'home: stories are the 5 real friends, not me', stories);
  const cards = await page.locator('.hfeed .fcard').count();
  ok(cards === 5, 'home: the feed has a week card for every friend (5), not just one', cards);
  ok(!/Your week/.test(t), 'home: my own week is not in the friends feed', t.slice(0, 300));
  const heads = await page.locator('.hfeed .fcard .top').allInnerTexts();
  ok(heads.some(h => /Avery Quill/.test(h)) && heads.every(h => !/with you/.test(h)) && await page.locator('.hfeed .fcard .pillchip').count() === 0, 'home: each card is a friend, with no “N classes with you” pill (Tate, 2026-09-30)', heads);
  const av = '#hf-' + FX.FRIENDS[0].id;
  const sh = [...new Set((await page.locator(av + ' .g-b.shared').allInnerTexts()).map(b => b.replace(/\s+/g, ' ')))];
  const notSh = (await page.locator(av + ' .g-b:not(.shared)').allInnerTexts()).map(b => b.replace(/\s+/g, ' '));
  ok(sh.length >= 1 && notSh.some(b => /PHIL 3331/.test(b)), 'home: Avery’s card still rings only the classes she shares with me', { sh, notSh });
  const avCard = await page.locator(av).innerText();
  ok(!/yellow\s*=\s*shared/i.test(avCard) && !/yellow\s*=\s*shared/i.test(t) && await page.locator(av + ' .foot').count() === 0, 'home: no “yellow = shared” line under a card, even one with shared classes (Tate, 2026-09-30)', avCard.slice(-160));
  const f2 = (await page.locator('#hf-' + FX.FRIENDS[2].id + ' .g-b').allInnerTexts()).map(b => b.replace(/\s/g, ''));
  ok(f2.includes('STAT2170') && f2.includes('BUS3438') && !f2.includes('ECON2303'), 'home: Sky’s own card draws her classes, not her orphaned ECON 2303 row', f2);
  const f1 = await page.locator('#hf-' + FX.FRIENDS[1].id).innerText();
  ok(/No set time\s*UNIV 1101\s*No section/i.test(f1) && !/No times yet/.test(f1), 'home: Rowan’s class saved without a section sits in the “No set time” row under his week', f1);
  ok(/You might know[\s\S]*Pat Suggestia[\s\S]*Taking one of your classes/.test(t), 'home: suggestion with the server’s own reason');
  ok(/Where your friends are[\s\S]*PHIL 3331/.test(t), 'home: where friends are, from real classes');
  const id4 = FX.FRIENDS[3].id;
  await page.evaluate(() => { document.getElementById('scroll').scrollTop = 0; });
  await click(page, `.story[data-x="${id4}"]`); await tick(page, 900);
  const dy = await page.evaluate(id => { const c = document.getElementById('hf-' + id).getBoundingClientRect(), s = document.getElementById('scroll').getBoundingClientRect(); return { top: c.top - s.top, st: document.getElementById('scroll').scrollTop }; }, id4);
  ok(dy.st > 0 && dy.top >= -2 && dy.top < 60, 'home: tapping a story scrolls to that friend’s card', dy);
  ok(log.errors.length === 0, 'home: no page errors', log.errors);
  await close();
};

/* Home width (Tate, 2026-09-30, from the Home Card Width mockup): Home sits 12px from the screen edge
   and a friend's week 8px inside its card, with a 26px hour column and 5px day gaps. Schedule keeps
   16 / 14 / 30 / 6. */
tests.homeWidth = async () => {
  const { page, close, log } = await openApp({ width: 390 });
  await page.waitForFunction(() => TC.ready && document.querySelectorAll('.hfeed .fcard').length === 5, null, { timeout: 8000 });
  const m = await page.evaluate(() => {
    const sc = document.getElementById('scroll').getBoundingClientRect(), L = el => Math.round(el.getBoundingClientRect().left - sc.left), R = el => Math.round(sc.right - el.getBoundingClientRect().right);
    const card = document.querySelector('.hfeed .fcard'), body = card.querySelector('.g-body'), lab = body.querySelector('.g-lab'), cols = [...body.querySelectorAll('.g-col')];
    const where = document.querySelector('.card.where'), mk = document.querySelector('.mightknow');
    return { hdr: L(document.querySelector('.homehdr .tc-wordmark')), story: L(document.querySelector('.story')), cards: [...document.querySelectorAll('.hfeed .fcard')].map(c => [L(c), R(c)]),
      gridL: Math.round(body.getBoundingClientRect().left - card.getBoundingClientRect().left), gridR: Math.round(card.getBoundingClientRect().right - body.getBoundingClientRect().right),
      lab: Math.round(lab.getBoundingClientRect().width), gap: Math.round(cols[1].getBoundingClientRect().left - cols[0].getBoundingClientRect().right), col: cols[0].getBoundingClientRect().width,
      where: where ? [L(where), R(where)] : null, mk: mk ? [L(mk), R(mk)] : null,
      labsFit: [...card.querySelectorAll('.g-lab span')].every(x => x.getBoundingClientRect().left >= card.getBoundingClientRect().left + 8 - 0.5) };
  });
  ok(m.hdr === 12 && m.story === 12, 'width: the wordmark and the stories start 12px from the screen edge', m);
  ok(m.cards.every(([l, r]) => l === 12 && r === 12), 'width: every friend card is 12px from both screen edges', m.cards);
  ok(m.gridL === 8 && m.gridR === 8 && m.lab === 26 && m.gap === 5, 'width: the week sits 8px inside the card, 26px hour column, 5px day gaps', m);
  ok(m.col > 59 && m.labsFit, 'width: each day column is about 60px (was 54) and the hour labels stay inside the card', m.col);
  ok((!m.where || (m.where[0] === 12 && m.where[1] === 12)) && (!m.mk || (m.mk[0] === 12 && m.mk[1] === 12)), 'width: the cards below the feed share the same 12px edge', { where: m.where, mk: m.mk });
  const cid = await page.evaluate(() => document.querySelector('.hfeed .fcard').id);
  await click(page, `#${cid} .g-day[data-x="M"]`);
  const foc = await page.evaluate(id => getComputedStyle(document.querySelector('#' + id + ' .g-body')).gridTemplateColumns.split(' ')[0], cid);
  ok(foc === '26px', 'width: a tapped day on a Home card keeps the 26px hour column', foc);
  await click(page, `#${cid} .top`);
  const fp = await page.evaluate(() => [...document.querySelectorAll('#scroll .grid')].map(g => [getComputedStyle(g).paddingLeft, getComputedStyle(g.querySelector('.g-body')).gridTemplateColumns.split(' ')[0]]));
  ok(fp.length > 0 && fp.every(([p, c]) => p === '14px' && c === '30px'), 'width: the friend page keeps its 14px inset and 30px hour column', fp);
  await click(page, '[data-a="tab"][data-x="schedule"]');
  const sc = await page.evaluate(() => { const g = document.querySelector('#scroll .grid'), b = g.querySelector('.g-body'); return { pad: getComputedStyle(g).paddingLeft, cols: getComputedStyle(b).gridTemplateColumns.split(' ')[0], gap: getComputedStyle(b).columnGap }; });
  ok(sc.pad === '14px' && sc.cols === '30px' && sc.gap === '6px', 'width: Schedule keeps its own 14px inset, 30px hour column and 6px gaps', sc);
  ok(log.errors.length === 0, 'width: no page errors', log.errors);
  await close();
};

tests.homeGridFit = async () => {
  const { page, close, log } = await openApp({});
  await page.waitForFunction(() => TC.ready && document.querySelectorAll('.hfeed .fcard').length === 5, null, { timeout: 8000 });
  const [A, S2, Q] = [FX.FRIENDS[0].id, FX.FRIENDS[2].id, FX.FRIENDS[3].id];
  /* Each card is as tall as the hours its classes fill: 30px an hour (three hours at least), a little
     more where one class starts within 70 minutes of the one before it, never over 300px. */
  const fit = await page.evaluate(ids => ids.map(id => { const el = document.querySelector('#hf-' + id + ' .g-body'); if (!el) return null;
    const secs = personSecs(id), [a, b] = gridSpan(secs, 180), body = el.getBoundingClientRect();
    const out = [...el.querySelectorAll('.g-b')].filter(x => { const r = x.getBoundingClientRect(); return r.top < body.top - 1 || r.bottom > body.bottom + 1; }).length;
    const b2b = DAYS.some(d => { const ds = secs.filter(s => s.s != null && !s.async && s.days.includes(d)).sort((x, y) => x.s - y.s); return ds.some((s, i) => i && s.s - ds[i - 1].s > 0 && s.s - ds[i - 1].s <= 70); });
    return { id, h: Math.round(body.height), want: (b - a) / 2, hours: (b - a) / 60, out, b2b, folds: el.querySelectorAll('.g-fold').length }; }), [A, S2, Q]);
  ok(fit.every(f => f && f.out === 0 && f.h <= 300 && f.folds === 0 && (f.b2b || f.h === f.want) && (!f.b2b || f.h > f.want || f.h === 300)), 'home: each card is its own hours at 30px/h (a bit more for back-to-back classes), every class inside, never over 300px, no “No classes” band', fit);
  ok(fit.every(f => f.h < 300) && new Set(fit.map(f => f.h)).size > 1, 'home: cards are smaller than the old fixed 300px and differ by schedule', fit.map(f => f.h));
  const q = fit.find(f => f.id === Q);
  ok(q.hours < 6, 'home: a short day is not padded out to six hours', q);
  const labs = await page.locator('#hf-' + Q + ' .g-lab span').allInnerTexts();
  const hr = t => { const m = /^(\d+)(a|p)$/.exec(t); return (+m[1] % 12) + (m[2] === 'p' ? 12 : 0); };
  ok(labs.length === q.hours + 1 && labs.every((t, i) => !i || hr(t) - hr(labs[i - 1]) === 1), 'home: a short card labels every hour on an even step (12p 1p 2p 3p, never 12p 2p 3p)', labs);
  /* Each card's days work on their own. */
  const focused = () => page.evaluate(() => [...document.querySelectorAll('.hfeed .fcard')].map(c => { const f = c.querySelector('.g-day.on'); return f ? f.dataset.x : null; }));
  await click(page, `#hf-${A} .g-day[data-x="M"]`);
  let f = await focused();
  ok(f[0] === 'M' && f.slice(1).every(x => x === null), 'home: tapping Monday on one card opens only that card', f);
  await click(page, `#hf-${S2} .g-day[data-x="W"]`);
  f = await focused();
  ok(f[0] === 'M' && f[2] === 'W' && f[1] === null && f[3] === null, 'home: another card’s day opens on its own; the first stays', f);
  await click(page, `#hf-${A} .g-day[data-x="M"]`);
  f = await focused();
  ok(f[0] === null && f[2] === 'W', 'home: tapping it again closes only that card', f);
  await click(page, `#hf-${A} .g-day[data-x="M"]`);
  await click(page, `#hf-${A} .top`);
  ok(await page.locator('.g-day.on').count() === 0, 'home: the friend’s own page grid is not opened by the Home card', await page.locator('.g-day.on').allInnerTexts());
  /* On the friend page, the week grid and the shared-plan grid are separate too. */
  const gridsOn = () => page.evaluate(() => [...document.querySelectorAll('.grid')].map(g => { const f = g.querySelector('.g-day.on'); return f ? f.dataset.x : null; }));
  ok((await page.locator('.grid').count()) === 2, 'friend page: week grid + plan grid', await page.locator('.grid').count());
  await click(page, '.plancol .g-day[data-x="T"]');
  let g = await gridsOn();
  ok(g[0] === null && g[1] === 'T', 'friend page: tapping a day on the plan opens only the plan grid', g);
  /* The grid itself, on synthetic sections: hourly classes keep a gap, a class ending at the axis end
     stays inside, a long day is capped at the old 300px, and 30-minute classes never hang out. */
  const probe = await page.evaluate(() => {
    const mk = (id, s, e, days) => ({ id: 'x' + id, code: 'TEST ' + (1000 + id), days, s, e, async: false });
    const run = secs => { const d = document.createElement('div'); d.style.width = '340px'; document.body.appendChild(d); d.innerHTML = grid(secs, { act: 'homeDay', key: 'probe', one: true, fit: 30, H: 300 });
      const body = d.querySelector('.g-body').getBoundingClientRect(), bs = [...d.querySelectorAll('.g-b')].map(b => b.getBoundingClientRect());
      const out = bs.filter(r => r.bottom > body.bottom + 0.5 || r.top < body.top - 0.5).length;
      let lap = 0; for (let i = 0; i < bs.length; i++) for (let j = i + 1; j < bs.length; j++) if (Math.abs(bs[i].left - bs[j].left) < 1 && bs[i].bottom > bs[j].top + 0.5 && bs[j].bottom > bs[i].top + 0.5) lap++;
      let gap = Infinity; for (let i = 0; i < bs.length; i++) for (let j = 0; j < bs.length; j++) if (i !== j && Math.abs(bs[i].left - bs[j].left) < 1 && bs[j].top >= bs[i].top) gap = Math.min(gap, bs[j].top - bs[i].bottom);
      d.remove(); return { H: Math.round(body.height), out, lap, gap: Math.round(gap * 10) / 10 }; };
    return { hourly: run([mk(1, 540, 590, 'M'), mk(2, 600, 650, 'M'), mk(3, 660, 710, 'M')]),
             end: run([mk(1, 490, 540, 'T'), mk(2, 610, 660, 'T')]),
             long: run([mk(1, 430, 480, 'W'), mk(2, 550, 600, 'W'), mk(3, 670, 720, 'W'), mk(4, 790, 840, 'W'), mk(5, 910, 960, 'W'), mk(6, 1030, 1080, 'W'), mk(7, 1150, 1200, 'W'), mk(8, 1200, 1250, 'R')]),
             short: run([mk(1, 600, 630, 'R'), mk(2, 720, 750, 'R')]) };
  });
  ok(probe.hourly.lap === 0 && probe.hourly.out === 0 && probe.hourly.gap >= 3, 'grid fit: 9:00, 10:00, 11:00 fifty-minute classes keep a visible gap', probe.hourly);
  ok(probe.end.out === 0 && probe.end.H === 90, 'grid fit: a class ending at the axis end stays inside (8:10–9:00 + 10:10–11:00 → 8a–11a, 90px)', probe.end);
  ok(probe.long.H === 300 && probe.long.out === 0, 'grid fit: a 7a–9p day with no long break is capped at 300px, not 420', probe.long);
  /* Tjudd's card: TuTh 8:00–8:50 and 9:00–10:50, 12:00–1:20, 6:00–7:20p, Fri 10:00–10:50. No band for
     the empty 2p–6p (Tate took the bands back out, 2026-09-30): the hours run straight through at the
     300px cap, and the two morning classes still never touch. */
  const tj = await page.evaluate(() => {
    const mk = (id, code, s, e, days) => ({ id: 'tj' + id, code, days, s, e, async: false });
    const secs = [mk(1, 'PSY 3323', 480, 530, 'TR'), mk(2, 'PSY 3323', 540, 650, 'TR'), mk(3, 'PSY 3333', 720, 800, 'TR'), mk(4, 'BIO 3312', 1080, 1160, 'TR'), mk(5, 'PSY 3333', 600, 650, 'F')];
    const look = sel => { const d = document.createElement('div'); d.style.width = '340px'; document.body.appendChild(d);
      d.innerHTML = grid(secs, { sel, act: 'homeDay', key: 'tj', one: true, fit: 30, H: 300 });
      const body = d.querySelector('.g-body').getBoundingClientRect(), col = [...d.querySelectorAll('.g-col')].find(c => c.classList.contains('on')) || d.querySelectorAll('.g-col')[1];
      const bs = [...col.querySelectorAll('.g-b')].map(b => { const r = b.getBoundingClientRect(); return { top: r.top, bottom: r.bottom, h: r.height, fits: b.scrollHeight <= b.clientHeight + 1 }; }).sort((x, y) => x.top - y.top);
      const fold = d.querySelector('.g-fold'), fr = fold && fold.getBoundingClientRect();
      const l6 = [...d.querySelectorAll('.g-lab span')].find(x => x.innerText === '6p'), bio = bs[bs.length - 1];
      const out = { H: Math.round(body.height), labs: [...d.querySelectorAll('.g-lab span')].map(x => x.innerText), fold: fold ? fold.innerText : null,
        at6: l6 ? Math.round((bio.top - (l6.getBoundingClientRect().top + l6.getBoundingClientRect().height / 2)) * 10) / 10 : null,
        gap12: bs[1].top - bs[0].bottom, h1: bs[0].h, fits: bs.every(b => b.fits), clear: !fr || bs.every(b => b.bottom <= fr.top + 0.5 || b.top >= fr.bottom - 0.5) };
      d.remove(); return out; };
    return { rest: look(null), thu: look('R') }; });
  ok(tj.rest.fold === null && tj.rest.labs.join(' ') === '8a 10a 12p 2p 4p 6p 8p', 'grid fit: no “No classes” band — the empty 2p–6p runs straight through, every label on its step', tj.rest);
  ok(tj.rest.H === 300 && tj.rest.h1 >= 24 && tj.rest.gap12 >= 0.5, 'grid fit: an 8a–8p card stops at 300px, and the back-to-back 8:00 and 9:00 classes still don’t touch', tj.rest);
  ok(tj.rest.at6 !== null && Math.abs(tj.rest.at6) <= 1, 'grid fit: the 6p class starts at the middle of the “6p” label', tj.rest);
  ok(tj.thu.H === tj.rest.H && tj.thu.gap12 >= 0.5 && tj.thu.fits, 'grid fit: tapped Thursday keeps the height, and 8:00–8:50 shows its code and time without touching 9:00', tj.thu);
  /* Edge cases: long empty stretches draw no band; a minimum height never runs into the next class; two
     sections 5 minutes apart (a clash) don't blow a small card up to 300px. */
  const edge = await page.evaluate(() => {
    const mk = (id, s, e, days) => ({ id: 'e' + id, code: 'TEST ' + (1000 + id), days, s, e, async: false });
    const run = (secs, o) => { const d = document.createElement('div'); d.style.width = '340px'; document.body.appendChild(d);
      d.innerHTML = grid(secs, Object.assign({ act: 'homeDay', key: 'e', one: true }, o));
      const body = d.querySelector('.g-body').getBoundingClientRect(), band = d.querySelector('.g-fold'), br = band && band.getBoundingClientRect();
      const bs = [...d.querySelectorAll('.g-b')].map(b => b.getBoundingClientRect());
      let lap = 0; for (let i = 0; i < bs.length; i++) for (let j = i + 1; j < bs.length; j++) if (Math.abs(bs[i].left - bs[j].left) < 1 && bs[i].bottom > bs[j].top + 0.5 && bs[j].bottom > bs[i].top + 0.5) lap++;
      const out = { H: Math.round(body.height), labs: [...d.querySelectorAll('.g-lab span')].map(x => x.innerText), under: br ? bs.filter(r => r.bottom > br.top + 0.5 && r.top < br.bottom - 0.5).length : 0, lap };
      d.remove(); return out; };
    return { beforeFold: run([mk(1, 630, 660, 'M'), mk(2, 780, 830, 'M')], { fit: 30, H: 300 }),
             offStep: run([mk(1, 490, 650, 'M'), mk(2, 910, 1190, 'M')], { fit: 30, H: 300 }),
             tight: run([mk(1, 480, 510, 'M'), mk(2, 515, 545, 'M'), mk(3, 1200, 1260, 'W')], { H: 330 }),
             clash: run([mk(1, 600, 650, 'M'), mk(2, 605, 655, 'M'), mk(3, 720, 770, 'W')], { fit: 30, H: 300 }) }; });
  ok(edge.beforeFold.labs.every((t, i, a) => !i || t !== a[i - 1]) && !edge.offStep.labs.includes('11a') && !edge.offStep.labs.includes('3p'), 'grid fit: long empty stretches get no edge labels off the step (no 11a / 3p)', { offStep: edge.offStep.labs });
  ok(edge.tight.lap === 0, 'grid: a minimum height never runs into the next class that day', edge.tight);
  ok(edge.clash.H < 150, 'grid fit: two sections 5 minutes apart don’t blow a 3-hour card up to 300px', edge.clash);
  /* A tapped day takes 2/3 of the width it used to; the other days get the rest. */
  const wd = await page.evaluate(() => {
    const mk = (id, code, s, e, days) => ({ id: 'wd' + id, code, days, s, e, async: false });
    const secs = [mk(1, 'BUS 4434', 480, 530, 'TR'), mk(2, 'BUS 3438', 600, 710, 'MW'), mk(3, 'BUS 3431', 840, 950, 'MW')];
    const d = document.createElement('div'); d.style.width = '358px'; document.body.appendChild(d);   /* a Home card on a 390px phone */
    d.innerHTML = grid(secs, { sel: 'W', act: 'homeDay', key: 'wd', one: true, fit: 30, H: 300 });
    const body = d.querySelector('.g-body'), cs = getComputedStyle(body), W = body.clientWidth - parseFloat(cs.paddingLeft) - parseFloat(cs.paddingRight);
    const cols = [...d.querySelectorAll('.g-col')].map(c => ({ on: c.classList.contains('on'), w: c.getBoundingClientRect().width }));
    const n = cols.length - 1, old = W - 30 - 6 * cols.length - 32 * n;
    d.remove(); return { W, n, old, on: cols.find(c => c.on).w, others: cols.filter(c => !c.on).map(c => c.w) }; });
  ok(Math.abs(wd.on - wd.old * 2 / 3) < 1.5 && wd.on >= 110 && wd.others.every(w => w > 40), 'grid: a tapped day is 2/3 as wide as before, and the other days widen', wd);
  ok(probe.short.out === 0 && probe.short.lap === 0, 'grid fit: 30-minute classes stay inside and apart', probe.short);
  /* A friend whose classes have no set times gets the list, not an empty grid. */
  const noTimes = await page.evaluate(id => { const keep = PEOPLE[id].secs, u = PEOPLE[id].unplaced; PEOPLE[id].secs = []; PEOPLE[id].unplaced = ['UNIV 1101'];
    try { return homeWeekCard(id); } finally { PEOPLE[id].secs = keep; PEOPLE[id].unplaced = u; } }, FX.FRIENDS[4].id);
  ok(!/g-body/.test(noTimes) && /class="anyrow"[\s\S]*UNIV 1101[\s\S]*No section/.test(noTimes) && !/No set times for/.test(noTimes), 'home: a friend with no set class times gets the “No set time” row, not an empty grid', noTimes.slice(-400));
  ok(log.errors.length === 0, 'home fit: no page errors', log.errors);
  await close();
};

/* Class blocks: the text fills the block as far as it can without looking crowded (Tate, 2026-09-30:
   "lets fill as much before it looks crowded the squares so the text is easier to read"). A card like
   Swstern's: MW BUS 3348 12:00–1:50, MW BUS 4404 6:00–7:20p, TR BUS 4418 1:50–2:40, Tu BUS 4453 3:10–5:40. */
tests.gridTextFill = async () => {
  const { page, close, log } = await openApp({});
  await page.waitForFunction(() => TC.ready && document.querySelectorAll('.hfeed .fcard').length === 5, null, { timeout: 8000 });
  const look = (sel, secs, width) => page.evaluate(([sel, secs, width]) => {
    const host = width ? Object.assign(document.createElement('div'), { className: 'homepg' }) : document.querySelector('#hf-' + TC.friends[0]);
    if (width) { host.style.cssText = 'width:' + width + 'px;position:absolute;top:0;left:0'; document.body.appendChild(host); host.innerHTML = '<div class="grid"></div>'; }
    host.querySelector('.grid').outerHTML = grid(secs.map((x, i) => ({ id: 'tf' + i, code: x[0], s: x[1], e: x[2], days: x[3], async: false })), { sel, act: 'homeDay', key: 'tf', one: true, fit: 30, H: 300 });
    const out = [...host.querySelectorAll('.g-b')].map(b => { const r = b.getBoundingClientRect(), rg = document.createRange(); rg.selectNodeContents(b); const t = rg.getBoundingClientRect(), c = b.querySelector('.g-code'), tm = b.querySelector('.g-time');
      return { txt: b.innerText.replace(/\s+/g, ' '), wide: b.classList.contains('wide'), w: Math.round(r.width), h: Math.round(r.height), f: parseFloat(getComputedStyle(c || b).fontSize), ft: tm ? parseFloat(getComputedStyle(tm).fontSize) : 0,
        /* under 9px (a code shrunk to fit a 32px column) headless Chromium rounds each glyph's advance, so 1px of slack */
        inside: (sl => t.left >= r.left - sl && t.right <= r.right + sl && t.top >= r.top - 0.5 && t.bottom <= r.bottom + 0.5)(parseFloat(getComputedStyle(c || b).fontSize) < 9 ? 1 : 0.5) }; });
    if (width) host.remove(); return out; }, [sel, secs, width]);
  const SW = [['BUS 3348', 720, 830, 'MW'], ['BUS 4404', 1080, 1160, 'MW'], ['BUS 4418', 830, 880, 'TR'], ['BUS 4453', 910, 1060, 'T']];
  let b = await look(null, SW);
  const tall = b.filter(x => x.h >= 40), short = b.filter(x => x.h < 30);
  ok(tall.length >= 4 && tall.every(x => x.f >= 13.5) && b.every(x => x.inside), 'text fill: a tall block’s code is ~14px (was 10), and every block’s text stays inside it', b);
  ok(short.length >= 2 && short.every(x => x.f >= 10 && x.f <= 11.5 && x.inside), 'text fill: a 50-minute block keeps its old small size rather than crowd', short);
  b = await look('W', SW);
  const wide = b.filter(x => x.wide);
  ok(wide.length === 2 && wide.every(x => x.f >= 13.5 && x.ft >= 11.5 && x.inside) && b.filter(x => !x.wide && x.h >= 40).every(x => x.f >= 12.5 && x.inside), 'text fill: a tapped day’s code and time grow too (14 / 12px), and the days beside it still fill their blocks', b);
  /* A 75-minute class on the tapped day: its height, not the 14px cap, sets the size (code + time with air). */
  b = (await look('W', SW.concat([['BUS 4499', 1195, 1270, 'W']]))).filter(x => x.wide && /BUS 4499/.test(x.txt));
  ok(b.length === 1 && b[0].h >= 36 && b[0].h < 40 && b[0].f >= 11 && b[0].f < 13.8 && b[0].inside, 'text fill: a tapped day’s short block is sized by its height and still fits', b);
  /* The widest real subjects, five days, one tapped, on a narrow phone: the text shrinks to fit, never spills. */
  const WIDE = [['WGQS 3500', 480, 590, 'MTWRF'], ['MATH 1261', 600, 710, 'MTWRF'], ['HNRS 1100', 720, 830, 'MTWRF']];
  for (const [sel, w] of [[null, 300], ['W', 300], ['W', 358], [null, 358]]) {
    b = await look(sel, WIDE, w);
    ok(b.length === 15 && b.every(x => x.inside && x.f >= (x.wide ? 9 : 7)), `text fill: WGQS / MATH / HNRS show whole at ${w}px${sel ? ', a day tapped' : ''} — smaller only where they’d spill`, b.filter(x => !x.inside).concat(b.slice(0, 3)));
    if (w === 358) ok(b.every(x => x.f >= (x.wide ? 11 : sel ? 9 : 10)), `text fill: at ${w}px${sel ? ', a day tapped' : ''} nothing is smaller than it used to be`, b);
  }
  ok(log.errors.length === 0, 'text fill: no page errors', log.errors);
  await close();
};

/* Classes that don't sit on a time slot — online/self-paced sections, sections whose time isn't posted
   (projects), classes saved with no section — get one row under the week (Tate, 2026-09-30). */
tests.homeNoSetTime = async () => {
  const { page, close, log } = await openApp({});
  await page.waitForFunction(() => TC.ready && document.querySelectorAll('.hfeed .fcard').length === 5, null, { timeout: 8000 });
  const A = FX.FRIENDS[0].id, card = '#hf-' + A;
  const before = await page.locator(card + ' .g-b').count();
  await page.evaluate(id => { PEOPLE[id].secs = PEOPLE[id].secs.concat([SEC['70901'], SEC['70902']]); render(true); }, A);
  await tick(page, 200);
  const row = await page.evaluate(c => { const r = document.querySelector(c + ' .anyrow'), g = document.querySelector(c + ' .g-body');
    return r && { t: r.innerText.replace(/\s+/g, ' '), below: r.getBoundingClientRect().top >= g.getBoundingClientRect().bottom, chips: [...r.querySelectorAll('.any-c')].map(b => [b.innerText.replace(/\s+/g, ' '), b.dataset.a, b.dataset.y || '', b.classList.contains('shared')]) }; }, card);
  ok(row && row.below && /^No set time BUS 4488 Online BUS 4488$/i.test(row.t), 'no set time: Avery’s online section and her unposted-time section sit in a row under her week', row);
  ok(await page.locator(card + ' .g-b').count() === before && await page.locator(card + ' .g-b[data-x="BUS 4488"]').count() === 0, 'no set time: neither is drawn on the grid', before);
  ok(row && row.chips.every(c => c[1] === 'secSheet' && c[2]) && row.chips.every(c => !c[3]), 'no set time: section chips open the section preview; no ring on a class I’m not in', row && row.chips);
  await click(page, `${card} .any-c[data-y="70901"]`); await tick(page, 400);
  let sh = (await page.locator('#sheet').innerText()).replace(/\s+/g, ' ');
  ok(/BUS 4488/.test(sh) && /Online · self-paced/.test(sh) && /IN THIS SECTION (\w+ )?Avery/i.test(sh) && await page.locator('.homehdr').count() === 1, 'no set time: tapping the online chip opens its preview — online, self-paced, Avery in it — and stays on Home', sh.slice(0, 240));
  await click(page, '[data-a="closeSheet"]');
  await click(page, `${card} .any-c[data-y="70902"]`); await tick(page, 400);
  sh = (await page.locator('#sheet').innerText()).replace(/\s+/g, ' ');
  ok(/BUS 4488/.test(sh) && /Time not posted/.test(sh), 'no set time: the unposted-time chip says “Time not posted”, never a made-up time', sh.slice(0, 200));
  await click(page, '[data-a="closeSheet"]');
  /* A class I'm in too gets the same yellow ring as a shared block. */
  await page.evaluate(() => { PEOPLE.me.unplaced = (PEOPLE.me.unplaced || []).concat(['BUS 4488']); render(true); });
  await tick(page, 200);
  const rings = await page.locator(card + ' .any-c.shared').count();
  ok(rings === 2, 'no set time: a class I share gets the yellow ring, as on the grid', rings);
  /* On my own week there is no ring — every class is mine. */
  const meCard = await page.evaluate(() => { const k = PEOPLE.me.secs; PEOPLE.me.secs = k.concat([SEC['70901']]); try { return homeWeekCard('me'); } finally { PEOPLE.me.secs = k; } });
  ok(/class="anyrow"[\s\S]*BUS 4488[\s\S]*Online/.test(meCard) && !/any-c shared/.test(meCard), 'no set time: my own week lists my online class, with no ring', meCard.slice(-400));
  /* The same class on the week AND in the row: the chips name their section. A weekend-only section (no
     column for it) goes in the row with its day. */
  await page.evaluate(id => { PEOPLE[id].secs = PEOPLE[id].secs.concat([SEC['70900'], { id: 'wk1', code: 'KINE 1001', sec: '01', prof: null, days: 'S', s: 540, e: 650, async: false }]); render(true); }, A);
  await tick(page, 200);
  const t2 = (await page.locator(card + ' .anyrow').innerText()).replace(/\s+/g, ' ');
  ok(/BUS 4488 Online · Sec 70 BUS 4488 Sec 02 KINE 1001 Sat/i.test(t2) && await page.locator(card + ' .g-b[data-x="BUS 4488"]').count() === 1 && await page.locator(card + ' .g-b[data-x="KINE 1001"]').count() === 0, 'no set time: with BUS 4488 also on Friday the chips say which section; a Saturday class sits in the row with its day', t2);
  const tall = await page.locator(card + ' .any-c').evaluateAll(es => es.map(e => Math.round(e.getBoundingClientRect().height)));
  ok(tall.every(h => h >= 42), 'no set time: chips are at least 42px tall to tap', tall);
  /* A class saved with no section opens the class itself — there is no section to preview. */
  const R = '#hf-' + FX.FRIENDS[1].id;
  await page.evaluate(r => document.querySelector(r).scrollIntoView(), R);
  await click(page, `${R} .any-c[data-x="UNIV 1101"]`); await tick(page, 500);
  ok(await page.locator('.homehdr').count() === 0 && /UNIV 1101/.test(await text(page)) && await page.locator('#sheet .xbtn').count() === 0, 'no set time: a class with no section opens its class page', (await text(page)).slice(0, 200));
  ok(log.errors.length === 0, 'no set time: no page errors', log.errors);
  await close();
};

tests.sectionLabel = async () => {
  /* Cal Poly's feed names sections "S04-SEM Regular": show "S04" — no "§", no "-SEM Regular". */
  const seats = FX.TABLES.course_seats.map(r => r.course_code === 'BUS 4488' && r.section === '01' ? { ...r, section: 'S04-SEM Regular' } : r);
  const mineS = FX.TABLES.my_sections.map((r, i) => r.user_id === FX.ME.id && i === FX.TABLES.my_sections.findIndex(x => x.user_id === FX.ME.id) ? { ...r, section: 'S04-SEM Regular' } : r);
  const { page, close, log } = await openApp({ tables: { ...FX.TABLES, course_seats: seats, my_sections: mineS } });
  await page.waitForFunction(() => TC.ready && TC.seatsLoaded, null, { timeout: 8000 });
  await page.evaluate(() => A.openClass('BUS 4488')); await tick(page, 500);
  const rows = await page.locator('.secrow').allInnerTexts();
  ok(rows.some(r => /^S04 Fri\b/.test(r.trim())), 'section: class page row reads “S04 Fri”', rows);
  ok(rows.every(r => !/§|SEM Regular/.test(r)), 'section: no “§” and no “-SEM Regular” anywhere in the sections', rows);
  ok(rows.some(r => /^Sec 02\b/.test(r.trim())), 'section: a bare-number section reads “Sec 02”', rows);
  const lab = await page.evaluate(() => [secLabel('S04-SEM Regular'), secLabel('01-LEC Regular'), secLabel(' S12 '), secLabel(''), secLabel(null)]);
  ok(JSON.stringify(lab) === JSON.stringify(['S04', 'Sec 01', 'S12', '', '']), 'section: labels from the real feed shapes', lab);
  const body = await page.evaluate(() => document.body.innerText);
  ok(!/§/.test(body), 'section: no “§” on the page');
  /* Onboarding's "your classes" list uses the same label. */
  await page.evaluate(() => { S.stack.home.push({ s: 'onb', p: { step: 'confirm' } }); render(); }); await settle(page, 1200);
  const onbS = await page.locator('.crow .s').allInnerTexts();
  ok(onbS.includes('S04') && onbS.every(x => !/SEM|§|Sec S/.test(x)), 'section: onboarding lists “S04”, not the raw feed string', onbS);
  await page.evaluate(() => { S.stack.home.pop(); render(); });
  /* Champ's "open / add / watch section …": the exact code first; a bare number only when it's unambiguous. */
  const found = await page.evaluate(() => { const L = [{ sec: 'S04-SEM Regular' }, { sec: '04-LAB' }, { sec: '02' }, { sec: 'S12' }];
    const f = w => { const x = secFind(L, w); return x ? x.sec : null; };
    return [f('S04'), f('s04'), f('S04-SEM Regular'), f('04-LAB'), f('4'), f('2'), f('02'), f('12'), f(''), f(null), f('S99')]; });
  ok(JSON.stringify(found) === JSON.stringify(['S04-SEM Regular', 'S04-SEM Regular', 'S04-SEM Regular', '04-LAB', null, '02', '02', 'S12', null, null, null]), 'section: Champ finds the exact section, and a bare number only when one section has it', found);
  ok(log.errors.length === 0, 'section: no page errors', log.errors);
  await close();
};

tests.planPicker = async () => {
  /* + on a class page opens "Add to a plan": Plan A/B/C, and that plan's week with this section drawn
     see-through. Fixture Plan B holds ECON 2303 Sec 03 (TuTh 10:10–12:00). */
  const { page, close, log } = await openApp({});
  await page.waitForFunction(() => TC.ready && TC.seatsLoaded, null, { timeout: 8000 });
  await page.evaluate(() => A.openClass('PHIL 3331')); await settle(page, 500);
  ok(/Tap \+ to add a section to a plan/.test(await text(page)), 'picker: the hint says “to a plan”');
  await click(page, '.secrow .addbtn');
  ok(await page.locator('#sheet .ap-pick button').count() === 3 && (await page.locator('#sheet .ap-pick button.on').innerText()).startsWith('Plan A'), 'picker: three plans, the last-used one (A) picked', await page.locator('#sheet .ap-pick').innerText());
  ok(await page.locator('#sheet .g-b.ghost').count() >= 1 && await page.locator('#sheet .g-b.ghost.clash').count() === 0, 'picker: the section is drawn see-through on Plan A’s week');
  const ghostBg = await page.locator('#sheet .g-b.ghost').first().evaluate(b => getComputedStyle(b).backgroundColor);
  ok(/rgba\(.*0\.1\d?\)/.test(ghostBg), 'picker: the preview block is translucent', ghostBg);
  await click(page, '#sheet [data-a="addPlanPick"][data-x="B"]');
  const b = await page.locator('#sheet').innerText();
  const codesB = (await page.locator('#sheet .g-b').allInnerTexts()).map(x => x.replace(/\s+/g, ' '));
  ok(codesB.some(c => /ECON 2303/.test(c)) && await page.locator('#sheet .g-b.ghost.clash').count() >= 1, 'picker: Plan B shows its own ECON 2303 with PHIL drawn red over it', codesB);
  ok(/Clashes with ECON 2303 Sec 03/.test(b) && await page.locator('#sheet [data-a="addPlanGo"]').count() === 0, 'picker: a clash names the class and there is no Add button', b);
  await click(page, '#sheet [data-a="addPlanPick"][data-x="C"]');
  ok(/Fits Plan C/.test(await page.locator('#sheet').innerText()), 'picker: an empty Plan C fits');
  const n0 = log.writes.filter(w => w.table === 'plans').length;
  await click(page, '#sheet [data-a="addPlanGo"]'); await settle(page, 800);
  const up = log.writes.filter(w => w.table === 'plans').slice(n0);
  ok(up.length === 1 && up[0].body.slot === 'C' && up[0].body.sections.some(x => x.code === 'PHIL 3331'), 'picker: Add writes to the plan picked in the sheet (C)', up.map(w => w.body));
  ok(await page.locator('#sheet .ap-pick').count() === 0 && /Added PHIL 3331 to Plan C/.test(await page.locator('#toast').innerText()), 'picker: the sheet closes and says where it went');
  ok(await page.locator('.secrow .addbtn.in').count() === 1, 'picker: the section now shows as in a plan');
  /* The same class in another section is shown as a switch. */
  await page.evaluate(() => A.openClass('ECON 2303')); await settle(page, 500);
  await click(page, '.secrow .addbtn >> nth=1'); await click(page, '#sheet [data-a="addPlanPick"][data-x="B"]');
  const sw = await page.locator('#sheet').innerText();
  ok(/Replaces ECON 2303 Sec 03 in Plan B/.test(sw) && /Switch to Plan B/.test(sw), 'picker: another section of a class already in the plan is a switch', sw);
  ok((await page.locator('#sheet .g-b').allInnerTexts()).filter(x => /2303/.test(x)).length === 2, 'picker: the switch preview shows only the new section (Tu + Th), not both');
  /* Tapping the pills redraws the open sheet in place: no slide-in again. */
  const anim = await page.locator('#sheet .sheet').evaluate(e => getComputedStyle(e).animationName);
  ok(anim === 'none', 'picker: picking a plan redraws the sheet in place, no slide-in again', anim);
  await click(page, '#sheet .xbtn[data-a="closeSheet"]');
  /* A section already in a plan: the sheet opens on that plan, marks it, and offers Remove. */
  await page.evaluate(() => A.openClass('PHIL 3331')); await settle(page, 500);
  await page.evaluate(() => { S.plan = 'A'; });
  await click(page, '.secrow .addbtn');
  const on = await page.locator('#sheet .ap-pick button.on').innerText(), has = await page.locator('#sheet .ap-pick button.has').count();
  ok(on.startsWith('Plan C') && has === 1 && /Remove from Plan C/.test(await page.locator('#sheet').innerText()), 'picker: a section already in Plan C opens on Plan C, marked, with Remove', { on, has });
  const n1 = log.writes.filter(w => w.table === 'plans').length;
  await click(page, '#sheet [data-a="addPlanGo"]'); await settle(page, 800);
  const rm = log.writes.filter(w => w.table === 'plans').slice(n1);
  const gone = rm.length === 1 && (rm[0].m === 'DELETE' ? /slot=eq\.C/.test(rm[0].query) : rm[0].body.slot === 'C' && !rm[0].body.sections.some(x => x.code === 'PHIL 3331'));
  ok(gone, 'picker: Remove takes it out of Plan C only (the emptied plan’s row goes)', rm.map(w => [w.m, w.query, w.body]));
  ok(log.errors.length === 0, 'picker: no page errors', log.errors);
  await close();
};

tests.toolbarBlue = async () => {
  /* Every tab is Home's blue when selected; Explore's magnifying glass is blue on Classes, purple on Professors. */
  const { page, close, log } = await openApp({});
  const seen = {};
  for (const k of ['home', 'explore', 'rate', 'schedule', 'friends']) {
    await click(page, `.tabbar [data-a="tab"][data-x="${k}"]`);
    seen[k] = await page.locator('.tabbar .tab.on').evaluate(b => [b.dataset.x, getComputedStyle(b).color, getComputedStyle(b.querySelector('.pill')).backgroundColor]);
  }
  ok(Object.entries(seen).every(([k, v]) => v[0] === k && v[1] === 'rgb(29, 78, 216)' && v[2] === 'rgb(227, 236, 255)'), 'toolbar: every selected tab is Home’s blue', seen);
  await click(page, '.tabbar [data-a="tab"][data-x="explore"]');
  await click(page, '[data-a="exMode"][data-x="classes"]');
  const onClasses = await page.locator('.search .sico').evaluate(e => getComputedStyle(e).color);
  await click(page, '[data-a="exMode"][data-x="profs"]');
  const onProfs = await page.locator('.search .sico').evaluate(e => getComputedStyle(e).color);
  ok(onClasses === 'rgb(37, 99, 235)' && onProfs === 'rgb(124, 58, 237)', 'explore: the magnifying glass is blue on Classes, purple on Professors', { onClasses, onProfs });
  await click(page, '[data-a="exMode"][data-x="classes"]');
  ok(await page.locator('.search .sico').evaluate(e => getComputedStyle(e).color) === 'rgb(37, 99, 235)', 'explore: back to blue on Classes');
  ok(log.errors.length === 0, 'toolbar: no page errors', log.errors);
  await close();
};

tests.ratingColors = async () => {
  /* Stars take the rating's colour on the desktop's cut-offs (PolyRatings 3.3 / 2.5 of 4): Ada 3.62 and
     Dov 3.88 green, Bram 2.85 · Cleo 3.21 · Faro 3.05 yellow, Esme 2.44 red. Counts read "N ratings". */
  const { page, close, log } = await openApp({});
  await click(page, '[data-a="tab"][data-x="explore"]');
  await click(page, '[data-a="exMode"][data-x="profs"]'); await settle(page, 500);
  const chips = await page.evaluate(() => Object.fromEntries([...document.querySelectorAll('#exlist .pcard')].map(c => {
    const ch = c.querySelector('.rchip'), nm = c.querySelector('div[style*="font-weight:900"]').textContent.trim();
    return [nm.split(' ')[0], ch ? [ch.className.replace('rchip', '').trim(), getComputedStyle(ch).backgroundColor, ch.querySelector('svg').getAttribute('fill')] : null]; })));
  const want = { Ada: 'good', Dov: 'good', Bram: 'mid', Cleo: 'mid', Faro: 'mid', Esme: 'low' };
  ok(Object.entries(want).every(([n, k]) => chips[n] && chips[n][0] === 'rt-' + k), 'ratings: each chip is green / yellow / red by its rating', chips);
  ok(chips.Ada[1] === 'rgb(220, 252, 231)' && chips.Ada[2] === '#16A34A' && chips.Esme[1] === 'rgb(254, 226, 226)' && chips.Esme[2] === '#DC2626' && chips.Bram[2] === '#D97706', 'ratings: the star matches the chip (green / yellow / red)', chips);
  const cards = await page.locator('#exlist').innerText();
  ok(!/PolyRatings|evaluation/.test(cards) && /41 ratings/.test(cards), 'ratings: cards say “41 ratings”, never “PolyRatings”', cards.slice(0, 300));
  const cut = await page.evaluate(() => [4.13, 4.12, 3.13, 3.12, 5, 0].map(r => rateTone(r).k));
  ok(JSON.stringify(cut) === JSON.stringify(['good', 'mid', 'mid', 'low', 'good', 'low']), 'ratings: cut-offs are the desktop’s (3.3 and 2.5 of 4)', cut);
  /* class page row and professor page use the same colours */
  await page.evaluate(() => A.openClass('STAT 2170')); await settle(page, 500);
  const row = await page.locator('.profrow .rt-low').count();
  ok(row === 1, 'ratings: Esme’s row on STAT 2170 is red', row);
  await click(page, '[data-a="tab"][data-x="explore"]');
  await click(page, '#exlist .pcard:has-text("Ada Examplewood")'); await settle(page, 800);
  ok(await page.locator('.rt-good').count() >= 1 && /41 ratings/.test(await text(page)), 'ratings: Ada’s page shows her rating in green, “41 ratings”');
  ok(log.errors.length === 0, 'ratings: no page errors', log.errors);
  await close();
};

tests.ratingZero = async () => {
  /* A PolyRatings entry with 0 evaluations (and a 0 score) has no rating — never a red "★ 0.0". */
  const poly = FX.POLY.map(p => p.id === 'p5' ? { ...p, numEvals: 0, overallRating: 0 } : p).filter(p => p.id !== 'p1');
  const { page, close, log } = await openApp({ poly });
  await page.waitForFunction(() => TC.ready && TC.seatsLoaded, null, { timeout: 8000 }); await settle(page, 800);
  await page.evaluate(() => A.openClass('STAT 2170')); await settle(page, 500);
  const row = await page.locator('.profrow').first().innerText();
  ok(/Esme Samplesworth/.test(row) && /No ratings yet/.test(row) && !/0\.0|★/.test(row) && await page.locator('.profrow .rt-low').count() === 0, 'ratings: 0 evaluations shows “No ratings yet”, not a red 0.0', row);
  /* Ada is off PolyRatings here but has TermChamp reviews: her card must not claim "No ratings yet". */
  await click(page, '[data-a="tab"][data-x="explore"]'); await click(page, '[data-a="exMode"][data-x="profs"]'); await settle(page, 400);
  const ada = await page.locator('#exlist .pcard:has-text("Ada Examplewood")').innerText();
  ok(!/No ratings yet/.test(ada) && /would take again/.test(ada), 'ratings: a professor with TermChamp reviews never reads “No ratings yet”', ada);
  ok(log.errors.length === 0, 'rating zero: no page errors', log.errors);
  await close();
};

tests.homeNoFriends = async () => {
  const tables = { ...FX.TABLES, friend_requests: FX.TABLES.friend_requests.filter(r => r.status !== 'accepted') };
  const { page, close, log } = await openApp({ tables });
  await page.waitForFunction(() => TC.ready, null, { timeout: 8000 });
  const t = await text(page);
  const stories = await page.locator('.story .nm').allInnerTexts();
  ok(stories.length === 1 && stories[0] === 'Add', 'home, no friends: the only story is Add (not me)', stories);
  ok(/Your week/.test(t) && /Fall 2026 · 5 classes/.test(t), 'home, no friends: my own week fills the feed', t.slice(0, 300));
  const blocks = await page.locator('.hfeed .fcard .g-b').allInnerTexts();
  ok(blocks.filter(b => b.replace(/\s/g, '') === 'BUS3438').length === 2, 'home, no friends: BUS 3438 drawn Mon+Wed', blocks);
  ok(/See your friends’ weeks/.test(t), 'home, no friends: the add-friends invite');
  ok(log.errors.length === 0, 'home, no friends: no page errors', log.errors);
  await close();
};

tests.homeFriendsErr = async () => {
  const { page, close } = await openApp({ hook: (url, m) => url.pathname.endsWith('/friend_requests') && m === 'GET' ? { status: 500, body: '{"message":"boom"}' } : null });
  await page.waitForFunction(() => TC.ready, null, { timeout: 8000 });
  const t = await text(page);
  ok(/Couldn’t load your friends/.test(t) && !/See your friends’ weeks/.test(t) && !/Your week/.test(t), 'home: friends failing to load says so — it doesn’t pretend you have none', t.slice(0, 300));
  ok(await page.locator('.story').count() === 0, 'home: no Add story when friends failed to load');
  await close();
};

tests.homeFriendSecsErr = async () => {
  let fails = 1;
  const { page, close } = await openApp({ hook: (url, m) => url.pathname.endsWith('/my_sections') && /user_id=in/.test(url.search) && m === 'GET' && fails-- > 0 ? { status: 500, body: '{"message":"boom"}' } : null });
  await page.waitForFunction(() => TC.ready && document.querySelectorAll('.hfeed .fcard').length === 5, null, { timeout: 8000 });
  const t = await page.locator('.hfeed').innerText();
  ok(/Couldn’t load Avery’s classes/.test(t) && !/hasn’t added classes|No times yet|No set time|with you/i.test(t), 'home: when friends’ classes fail to load every card says so — no “hasn’t added”, no false “No times yet” or “0 with you”', t.slice(0, 400));
  await click(page, '#hf-' + FX.FRIENDS[0].id + ' [data-a="refresh"]'); await tick(page, 2500);
  const t2 = await page.locator('#hf-' + FX.FRIENDS[0].id).innerText();
  ok(!/Couldn’t load/.test(t2) && /PHIL/.test(t2), 'home: Try again clears the error once the classes load', t2.slice(0, 300));
  await close();
};

tests.status = async () => {
  /* Monday 4:30pm Pacific: I am in BUS 3431 §01 (MoWe 4:10–6:00). I'm no longer a story, so check
     the status the app computes for me, plus that friends' rings still carry their own status. */
  const { page, close } = await openApp({ time: '2026-09-28T16:30:00-07:00' });
  const me = await page.evaluate(() => status('me'));
  ok(me.c === '#2563EB' && /In BUS 3431/.test(me.t), 'status: I show as in class at Mon 4:30p', me);
  const rings = await page.evaluate(() => TC.friends.map(id => [status(id).c || 'transparent', document.querySelector(`.story[data-x="${id}"] .ring`).getAttribute('style')]));
  ok(rings.length === 5 && rings.every(([c, st]) => st.includes(c)), 'status: every friend story ring is that friend’s status colour', rings);
  await close();
};

tests.explore = async () => {
  const { page, close, log } = await openApp({});
  await click(page, '[data-a="tab"][data-x="explore"]');
  let t = await text(page);
  noProto(t, 'Explore');
  const codes = await page.locator('#exlist .ccard .code').allInnerTexts();
  ok(codes.length === 11, 'explore: every fixture course listed once', codes);
  const card = n => page.locator('#exlist .ccard', { hasText: n }).first().innerText();
  ok(/BUS 3431[\s\S]*9 seats/.test(await card('BUS 3431')), 'explore: BUS 3431 shows the real open seats (9)', await card('BUS 3431'));
  ok(/Full/.test(await card('STAT 2170')) === false && /16 seats/.test(await card('STAT 2170')), 'explore: STAT 2170 counts only the open section', await card('STAT 2170'));
  ok(/Full/.test(await card('BUS 4442')), 'explore: BUS 4442 all full → Full', await card('BUS 4442'));
  await page.locator('#exq').fill('econ'); await tick(page);
  const c2 = await page.locator('#exlist .ccard .code').allInnerTexts();
  ok(c2.length === 1 && c2[0] === 'ECON 2303', 'explore: search narrows to ECON 2303', c2);
  await page.locator('#exq').fill(''); await tick(page);
  await click(page, '[data-a="exMode"][data-x="profs"]');
  const pc = await page.locator('#exlist .pcard').allInnerTexts();
  const ada = pc.find(x => /Ada Examplewood/.test(x)) || '';
  ok(/4\.5/.test(ada) && !/3\.6/.test(ada) && /41 ratings/.test(ada) && !/PolyRatings/.test(ada), 'explore: Ada shows PolyRatings 3.62/4 as 4.5/5, from “41 ratings”', ada);
  ok(/67% would take again/.test(ada), 'explore: Ada shows TermChamp would-again from her 3 reviews', ada);
  const bram = pc.find(x => /Bram Fixturesen/.test(x)) || '';
  ok(bram && !/would take again/.test(bram), 'explore: 2 reviews is below the floor — no percentage', bram);
  const gil = pc.find(x => /Gil Unratedson/.test(x)) || '';
  ok(gil && /No ratings yet/.test(gil) && !/★|\d\.\d/.test(gil.replace(/BUS \d+/g, '')), 'explore: an unrated professor shows no number', gil);
  ok(pc[0].includes('Dov Mockridge'), 'explore: professors sorted by rating', pc[0]);
  ok(!pc.some(x => /(^|\n)Staff(\n|$)/.test(x)), 'explore: Staff is not a professor');
  ok(log.errors.length === 0, 'explore: no page errors', log.errors);
  await close();
};

tests.classDetail = async () => {
  const { page, close, log } = await openApp({});
  await click(page, '[data-a="tab"][data-x="explore"]');
  await click(page, '#exlist [data-x="BUS 4401"]');
  let t = await text(page);
  ok(/Strategic Management/.test(t), 'class: title');
  ok(/Fixture text about strategy\. 3 lectures\./.test(t) && !/Enrl Tot/.test(t), 'class: scraper chrome stripped from description', t.slice(0, 400));
  ok(/PREREQ\s*None listed/.test(t), 'class: no prereq in catalog → “None listed”');
  await click(page, '[data-a="back"]');
  await click(page, '#exlist [data-x="BUS 4488"]');
  t = await text(page);
  ok(/Instructor not assigned/.test(t), 'class: Staff section says instructor not assigned');
  ok(/Online self-paced/.test(t.replace(/\s+/g, ' ')), 'class: async section says online', t);
  ok(/Time not posted/.test(t), 'class: TBA section says time not posted');
  ok(/Seats unknown/.test(t), 'class: no seat data → “Seats unknown”, not a number');
  ok(/No ratings yet/.test(t) && !/PolyRatings|\bevals?\b/.test(t), 'class: unrated professor row has no rating; counts read “ratings”');
  ok(!/NaN|undefined|null/.test(t), 'class: no NaN/undefined/null on screen', t.match(/NaN|undefined|null/));
  await click(page, '[data-a="back"]');
  await click(page, '#exlist [data-x="ECON 2303"]');
  t = await text(page);
  ok(/Waitlist · 11/.test(t) && /2 seats/.test(t), 'class: waitlist and open seat counts per section', t);
  ok(await page.locator('.wl').count() === 1, 'class: Watch offered only on the closed section');
  ok(log.errors.length === 0, 'class: no page errors', log.errors);
  await close();
};

tests.plans = async () => {
  const { page, close, log } = await openApp({});
  await click(page, '[data-a="tab"][data-x="explore"]');
  await click(page, '#exlist [data-x="PHIL 3331"]');
  await addVia(page);
  await settle(page, 1500);
  const up = log.writes.filter(w => w.table === 'plans');
  ok(up.length === 1 && up[0].m === 'POST' && /on_conflict=user_id%2Cterm%2Cslot|on_conflict=user_id,term,slot/.test(up[0].query), 'plans: one upsert on user_id,term,slot', up);
  const b = up[0] && up[0].body;
  ok(b && b.slot === 'A' && b.term === '2268' && b.user_id === FX.ME.id && JSON.stringify(b.sections) === JSON.stringify([{ code: 'PHIL 3331', class_nbr: FX.seat('PHIL 3331', '01').class_nbr }]), 'plans: row is {slot A, term, sections:[{code,class_nbr}]}', b);
  ok(log.writes.some(w => w.table === 'watch_sections' && w.m === 'DELETE') === false, 'plans: PHIL already watched → no second watch write');
  /* a clash: BUS 3438 §01 is MoWe 10:10–12:00; STAT 2170 §02 is MoWeFr 9:10–10:00 — no clash; ECON §03 TuTh 10:10 clashes with PHIL TuTh 9:10–11:00 */
  await click(page, '[data-a="back"]');
  await click(page, '#exlist [data-x="ECON 2303"]');
  await click(page, '.secrow .addbtn >> nth=0'); await click(page, '#sheet [data-a="addPlanPick"][data-x="A"]');
  const clashSheet = await page.locator('#sheet').innerText();
  ok(/Clashes with PHIL 3331/.test(clashSheet) && await page.locator('#sheet [data-a="addPlanGo"]').count() === 0 && await page.locator('#sheet button[disabled]').count() === 1, 'plans: a clash is shown with the real reason and can’t be added', clashSheet);
  await click(page, '#sheet .xbtn[data-a="closeSheet"]');
  /* Plan B from the server: one real section and one the feed no longer has. */
  await click(page, '[data-a="tab"][data-x="schedule"]');
  await click(page, '[data-a="schedTab"][data-x="plans"]');
  await click(page, '[data-a="pickPlan"][data-x="B"]');
  const t = await text(page);
  ok(/1 class\b/.test(t) && /1 section in this plan is no longer in the Fall 2026 list/.test(t), 'plans: plan B loads from the server and says what it can’t show', t.slice(0, 400));
  ok(!/Use as my schedule|Make this my schedule/.test(t), 'plans: no register button');
  ok(log.errors.length === 0, 'plans: no page errors', log.errors);
  await close();
};

tests.autowatch = async () => {
  const { page, close, log } = await openApp({});
  await click(page, '[data-a="tab"][data-x="explore"]');
  await click(page, '#exlist [data-x="BUS 3346"]');
  await addVia(page);
  const w = log.writes.filter(x => x.table === 'watch_sections');
  ok(w.length === 1 && w[0].m === 'POST' && w[0].body.class_nbr === FX.seat('BUS 3346', '01').class_nbr && w[0].body.term === '2268', 'autowatch: adding to a plan watches the section', w);
  await addVia(page);
  const w2 = log.writes.filter(x => x.table === 'watch_sections');
  ok(w2.length === 2 && w2[1].m === 'DELETE', 'autowatch: removing it un-watches what the plan watched', w2.map(x => x.m));
  /* PHIL 3331 §01 was watched BEFORE it went in a plan: taking it out must leave that alone. */
  await click(page, '[data-a="back"]');
  await click(page, '#exlist [data-x="PHIL 3331"]');
  await addVia(page); await addVia(page);
  const w3 = log.writes.filter(x => x.table === 'watch_sections');
  ok(w3.length === 2, 'autowatch: a section watched on its own stays watched', w3.map(x => x.m + ' ' + x.query));
  ok(log.errors.length === 0, 'autowatch: no page errors', log.errors);
  await close();
};

tests.prof = async () => {
  const { page, close, log } = await openApp({});
  await click(page, '[data-a="tab"][data-x="explore"]');
  await click(page, '[data-a="exMode"][data-x="profs"]');
  await click(page, '#exlist .pcard:has-text("Ada Examplewood")');
  await tick(page, 800);
  let t = await text(page);
  ok(/AVERAGE\s*★ 4\.5/.test(t) && /RATINGS\s*41/.test(t) && !/POLYRATINGS|EVALUATIONS/.test(t), 'prof: rating (out of 5) + “RATINGS 41”', t.slice(0, 300));
  ok(/RETAKE\s*67%/.test(t), 'prof: retake % from TermChamp reviews');
  ok(/3 reviews/.test(t) && /Difficulty 3\/5 from 3 reviews/.test(t), 'prof: difficulty says how many reviews it stands on');
  ok(await page.locator('#scroll .bars').count() === 1, 'prof: rating spread drawn at 3 reviews');
  ok(/Fixture review text, clear lectures\./.test(t), 'prof: written review shown');
  ok(/polyratings\.dev\/professor\/p1/.test(await page.locator('#scroll').innerHTML()), 'prof: links to her PolyRatings page');
  await click(page, '[data-a="back"]');
  await click(page, '#exlist .pcard:has-text("Faro Dummelow")');
  t = await text(page);
  ok(/Friends who took this professor[\s\S]*Avery Quill[\s\S]*BUS 3346 · Spring 2026/.test(t), 'prof: friends who took, from class_history', t.slice(-400));
  ok(/RETAKE\s*—/.test(t) && /No TermChamp reviews yet/.test(t), 'prof: no reviews → dashes, not numbers');
  await click(page, '[data-a="back"]');
  await click(page, '#exlist .pcard:has-text("Bram Fixturesen")');
  t = await text(page);
  ok(/RETAKE\s*—/.test(t) && /2 reviews/.test(t) && !/Difficulty/.test(t) && await page.locator('#scroll .bars').count() === 0 && /Fixture note about Bram\./.test(t), 'prof: 2 reviews → written review shown, but no %, average or spread', t.slice(0, 700));
  ok(log.errors.length === 0, 'prof: no page errors', log.errors);
  await close();
};

tests.rate = async () => {
  const { page, close, log } = await openApp({});
  await click(page, '[data-a="tab"][data-x="rate"]');
  let t = await text(page);
  ok(/Fall 2026[\s\S]*Current term/.test(t) && /Spring 2026/.test(t), 'rate: this term and past terms', t);
  ok(/Dov Mockridge[\s\S]*PHIL 3331/.test(t), 'rate: past class professor from class_history');
  ok(await page.locator('.li:has-text("Ada Examplewood")').count() === 1, 'rate: one row per professor (Ada teaches two of my classes)');
  await click(page, '.li:has-text("Ada Examplewood")');
  ok(await page.locator('.rf').count() === 1, 'rate: form opens');
  await click(page, '[data-a="draft"][data-x="stars"][data-y="4"]');
  await click(page, '[data-a="draft"][data-x="diff"][data-y="2"]');
  await click(page, '[data-a="draft"][data-x="again"][data-y="yes"]');
  await click(page, '[data-a="draftMore"]');
  await click(page, '[data-a="draft"][data-x="grade"][data-y="B+"]');
  await click(page, '[data-a="draft"][data-x="format"][data-y="Hybrid"]');
  await page.locator('#revta').fill('Fixture words from the test.');
  await click(page, '[data-a="postRating"]');
  await tick(page, 800);
  const w = log.writes.filter(x => x.table === 'reviews');
  const r = w[0] && w[0].body;
  const want = { professor_key: 'ada examplewood|bus', professor_name: 'Ada Examplewood', department: 'BUS', score: 4, difficulty: 2, format: 'Hybrid', grade: 'B+', would_again: true, note: 'Fixture words from the test.' };
  ok(w.length === 1 && r && Object.keys(want).every(k => r[k] === want[k]) && ['BUS 3431', 'BUS 4442'].includes(r.course), 'rate: inserts the desktop’s review row shape', r);
  ok(r && !('user_id' in r) && !('emplid' in r), 'rate: no user id or EMPLID in the row');
  t = await text(page);
  ok(/Thanks for your review/.test(t) && /Posted anonymously|Anonymous to everyone else/.test(t), 'rate: thanks screen');
  ok(!/Jordan, Aisha/.test(t), 'rate: no invented friends on the thanks screen');
  ok(log.errors.length === 0, 'rate: no page errors', log.errors);
  await close();
};

tests.rateOnce = async () => {
  const { page, close, log } = await openApp({ rpc: Object.assign({}, FX.RPC, { my_reviews: [{ id: 77, professor_key: 'ada examplewood|bus', score: 5, course: 'BUS 3431' }] }) });
  await click(page, '[data-a="tab"][data-x="rate"]');
  const row = await page.locator('.li:has-text("Ada Examplewood")').first().innerText();
  ok(/5\.0/.test(row) && !/Rate$/.test(row.trim()), 'rate: already-reviewed professor shows your score', row);
  await click(page, '.li:has-text("Ada Examplewood")');
  ok(await page.locator('.rf').count() === 0 && /already reviewed/.test(await page.locator('#toast').innerText()), 'rate: one review per professor');
  await close();
};

/* Focused day in the week grid (2026-09-30): nothing widens until a day is tapped; the tapped day
   shows full codes, exact times and friends; the now line only when that day is today; empty days
   drop out while focused; the subject is never cut off a course code. Monday 4:30pm SLO here. */
tests.focusDay = async () => {
  const { page, close, log } = await openApp({ time: '2026-09-28T16:30:00-07:00' });
  await click(page, '[data-a="tab"][data-x="schedule"]');
  const codeRe = /^[A-Z]{2,4}\s?\d{4}$/;
  const codes = async () => (await page.locator('.g-b').allInnerTexts()).map(x => x.replace(/\s+/g, ' ').trim());
  let c = await codes();
  ok(c.length === 8 && c.every(x => codeRe.test(x)), 'focus: at rest every block carries subject + number (no bare "3438")', c);
  ok(await page.locator('.g-b.wide').count() === 0 && await page.locator('.g-now').count() === 0 && await page.locator('.g-day').count() === 5, 'focus: nothing widens on its own, no now line, all five days');
  ok((await page.locator('.g-day.g-today').allInnerTexts()).join() === 'MON', 'focus: today is marked, not opened');
  await click(page, '.g-day[data-x="M"]');
  const bodyH = () => page.evaluate(() => Math.round(document.querySelector('#scroll .g-body').getBoundingClientRect().height));
  const wide = await page.locator('.g-b.wide').allInnerTexts();
  ok(wide.length === 4 && wide.every(x => /^BUS \d{4}\n\d{1,2}:\d{2}–\d{1,2}:\d{2}[ap]/.test(x)), 'focus: tapped day shows full code and exact time on every block', wide);
  ok(!/Rm|Bldg|§|\b7\d{4}\b/.test(wide.join(' ')), 'focus: no room and no class number on the blocks');
  ok(await page.locator('.g-now').count() === 1 && await page.locator('.g-b.live').count() === 1 && /BUS 3431/.test(await page.locator('.g-b.live').innerText()), 'focus: today tapped → now line, and the class I am in is live');
  ok((await page.locator('.g-day').allInnerTexts()).join('/') === 'MON/WED', 'focus: days with no classes drop out while a day is focused');
  ok(await page.locator('.g-b.wide[data-x="BUS 3438"] .g-face.sq').count() === 1 && await page.locator('.g-b.wide[data-x="BUS 3431"] .g-face.ci').count() === 1, 'focus: square face = same section (Sky), round = same class other section (Avery)');
  await click(page, '.g-day[data-x="W"]');
  ok(await page.locator('.g-b.wide').count() === 4 && await page.locator('.g-now').count() === 0, 'focus: another day tapped → times shown, no now line (it is Monday)');
  const hFocused = await bodyH();
  await click(page, '.g-day[data-x="W"]'); const hRest = await bodyH(); await click(page, '.g-day[data-x="W"]');
  ok(hFocused === hRest && hRest > 0, 'focus: tapping a day never changes the grid height', { hFocused, hRest });
  ok((await page.locator('#scroll .g-lab span').allInnerTexts()).join(' ') === '10a 12p 2p 4p 6p', 'focus: an 8-hour day is labelled every two hours, first to last', await page.locator('#scroll .g-lab span').allInnerTexts());
  await click(page, '.g-day[data-x="W"]');
  ok(await page.locator('.g-b.wide').count() === 0 && await page.locator('.g-day').count() === 5, 'focus: tapping the focused day again clears it');
  ok(log.errors.length === 0, 'focus: no page errors', log.errors);
  await close();
};

/* The same grid under pressure: a 360px phone, a 13-hour day, 30- and 50-minute classes, back-to-back
   classes, and five friends on one block. Sections are injected into the loaded state (synthetic, the
   same shape the seat feed produces) and the grid is re-rendered. Every block must hold its text. */
tests.focusDayFit = async () => {
  const { page, close, log } = await openApp({ time: '2026-09-28T16:30:00-07:00', width: 360 });
  await click(page, '[data-a="tab"][data-x="schedule"]');
  const mk = (code, days, s, e) => ({ code, days, s, e, async: false });
  const scenario = (secs, focus, everyone) => page.evaluate(([secs, focus, everyone]) => {
    const me = PEOPLE.me; if (!window.__fixSecs) window.__fixSecs = me.secs;
    me.secs = secs.map((x, i) => Object.assign({}, window.__fixSecs[0], x, { id: 'FX' + i }));
    if (everyone) TC.friends.forEach(f => { PEOPLE[f].secs = me.secs.map(s => Object.assign({}, s)); });
    S.schedDay = focus; render(true);
    const grid = document.querySelector('#scroll .grid');
    const bs = [...grid.querySelectorAll('.g-b')].map(b => { const r = b.getBoundingClientRect(); return { t: b.innerText.replace(/\s+/g, ' ').trim(), fits: b.scrollWidth <= b.clientWidth + 1 && b.scrollHeight <= b.clientHeight + 1, top: r.top, bottom: r.bottom, wide: b.classList.contains('wide'), tight: b.classList.contains('tight'), title: b.title,
      /* "+N" counts as showing only when it sits inside the faces' clip box (innerText also returns hidden overflow) */
      more: !!b.querySelector('.g-more') && (() => { const m = b.querySelector('.g-more').getBoundingClientRect(), c = b.querySelector('.g-faces').getBoundingClientRect(); return m.right > c.left + 0.5 && m.left < c.right - 0.5 && m.bottom > c.top + 0.5 && m.top < c.bottom - 0.5; })(),
      /* in a tight block the code and the time share a left edge */
      aligned: !b.classList.contains('tight') || Math.abs(b.querySelector('.g-code').getBoundingClientRect().left - b.querySelector('.g-time').getBoundingClientRect().left) < 0.5,
      /* every showing face sits at least its 1.5px ring inside the clip box, so the ring is never cut */
      ringRoom: [...b.querySelectorAll('.g-face')].every(f => { const fr = f.getBoundingClientRect(), c = f.closest('.g-faces').getBoundingClientRect(); const shows = fr.right > c.left && fr.left < c.right && fr.bottom > c.top && fr.top < c.bottom; return !shows || (fr.left >= c.left + 1.5 && fr.right <= c.right - 1.5 && fr.top >= c.top + 1.5 && fr.bottom <= c.bottom - 1.5); }),
      faces: [...b.querySelectorAll('.g-face')].filter(f => { const fr = f.getBoundingClientRect(); return fr.width > 0 && fr.right <= r.right + 0.5 && fr.bottom <= r.bottom + 0.5 && fr.left >= r.left - 0.5; }).length,
      /* a face is "cut" when part of it shows: it crosses the edge of the clip box (.g-faces) or of the block */
      cut: [...b.querySelectorAll('.g-face')].filter(f => { const fr = f.getBoundingClientRect(), c = f.closest('.g-faces').getBoundingClientRect();
        const box = { l: Math.max(c.left, r.left), t: Math.max(c.top, r.top), r: Math.min(c.right, r.right), b: Math.min(c.bottom, r.bottom) };
        const meets = fr.right > box.l + 0.5 && fr.left < box.r - 0.5 && fr.bottom > box.t + 0.5 && fr.top < box.b - 0.5;
        const whole = fr.left >= box.l - 0.5 && fr.right <= box.r + 0.5 && fr.top >= box.t - 0.5 && fr.bottom <= box.b + 0.5;
        return meets && !whole; }).length,
      inside: [...b.querySelectorAll('.g-faces,.g-time,.g-code')].every(k => { const kr = k.getBoundingClientRect(); return kr.right <= r.right + 0.5 && kr.bottom <= r.bottom + 0.5; }) }; });
    const lab = [...grid.querySelectorAll('.g-lab span')].map(x => x.innerText);
    return { bs, lab, days: [...grid.querySelectorAll('.g-day')].map(x => x.innerText), H: grid.querySelector('.g-body').getBoundingClientRect().height };
  }, [secs, focus, everyone]);
  const codeRe = /^[A-Z]{2,4} \d{4}/;
  /* 1. a 13-hour day with 30- and 50-minute classes, nothing focused, at 360px */
  let r = await scenario([mk('BUS 3438', ['M', 'W'], 480, 530), mk('MATH 1420', ['T', 'R'], 540, 590), mk('ARCH 2010', ['M', 'W'], 1200, 1260), mk('CSC 1010', ['R'], 600, 630)], null, false);
  ok(r.bs.length === 7 && r.bs.every(b => codeRe.test(b.t) && b.fits), 'fit: 13-hour day at 360px, every block keeps subject + number and nothing is clipped', r.bs);
  const hr = t => { const m = /^(\d+)(a|p)$/.exec(t); return (+m[1] % 12) + (m[2] === 'p' ? 12 : 0); };
  const even = lab => lab.length >= 3 && lab.every((t, i) => !i || hr(t) - hr(lab[i - 1]) === hr(lab[1]) - hr(lab[0]));
  ok(r.lab[0] === '8a' && even(r.lab) && hr(r.lab[r.lab.length - 1]) >= 20, 'fit: the axis starts at the first class hour and its labels sit on one even step (no stray last label)', r.lab);
  const restH = r.H;
  /* 2. back-to-back 50-minute classes on a focused long day: wide blocks must not overlap */
  const hourly = [mk('BUS 3438', ['M'], 480, 530), mk('MATH 1420', ['M'], 540, 590), mk('ARCH 2010', ['M'], 600, 650), mk('CSC 1010', ['M'], 1200, 1260)];
  const rest2 = (await scenario(hourly, null, false)).H;
  r = await scenario(hourly, 'M', false);
  const w = r.bs.filter(b => b.wide).sort((a, b) => a.top - b.top);
  ok(w.length === 4 && w.every((b, i) => !i || b.top >= w[i - 1].bottom - 0.5) && w.every(b => b.fits && b.inside && /\d:\d\d–\d{1,2}:\d\d[ap]/.test(b.t)), 'fit: focused hourly classes never overlap and each still shows its code and time', w.map(b => [b.t, Math.round(b.top), Math.round(b.bottom)]));
  ok(r.H === rest2 && rest2 === restH, 'fit: the body did not grow for the focused day (Tate: "have it not grow at all")', { focused: r.H, rest: rest2 });
  ok(w.every(b => b.tight && b.aligned), 'fit: the short focused blocks are tight, code and time flush left', w.map(b => [b.t, b.tight, b.aligned]));
  /* 3. five friends in every class, a full five-day week, Monday focused */
  r = await scenario([mk('BUS 3438', ['M', 'W', 'F'], 610, 720), mk('MATH 1420', ['T', 'R'], 540, 650), mk('ARCH 2010', ['M', 'W', 'F'], 780, 830), mk('CSC 1010', ['R'], 900, 930), mk('WVIT 3010', ['F', 'T'], 1200, 1260)], 'M', true);
  ok(r.days.length === 5 && r.bs.filter(b => b.wide).every(b => b.fits && b.inside && /\d:\d\d[ap]/.test(b.t)), 'fit: with five days showing every focused block still holds its code and time inside', r.bs.filter(b => b.wide));
  ok(r.bs.filter(b => b.wide).every(b => b.cut === 0 && b.ringRoom && !b.more) && r.bs.some(b => b.wide && b.tight && b.faces < 3), 'fit: in the narrow focused column the faces that fit show whole, the rest are left off with their "+N" — never a half face, never a count for faces that are not there', r.bs.filter(b => b.wide).map(b => [b.t, b.faces, b.cut]));
  ok(r.bs.filter(b => !b.wide).every(b => codeRe.test(b.t) && b.fits), 'fit: the 32px columns still hold "MATH 1420" on two lines', r.bs.filter(b => !b.wide));
  /* 3b. two 80-minute classes on a short day: tall enough for three rows — code, time, three faces and "+2" */
  r = await scenario([mk('POLS 4445', ['M', 'W'], 720, 800), mk('POLS 4451', ['M', 'W'], 810, 890)], 'M', true);
  ok(r.bs.filter(b => b.wide).length === 2 && r.bs.filter(b => b.wide).every(b => !b.tight && b.fits && b.inside && b.faces === 3 && /\+2/.test(b.t)), 'fit: a block tall enough for three rows stacks code, time and three faces plus "+2"', r.bs.filter(b => b.wide));
  /* 4. a 30-minute class with friends on a 13-hour focused day: no room for three rows */
  const thirty = [mk('CSC 1010', ['M'], 480, 510), mk('ARCH 2010', ['M'], 1200, 1260)];
  const rest4 = (await scenario(thirty, null, true)).H;
  r = await scenario(thirty, 'M', true);
  ok(r.bs.filter(b => b.wide).every(b => b.tight && b.fits && b.inside && b.faces === 3 && b.cut === 0 && b.ringRoom && b.more && /\+2$/.test(b.t.trim())), 'fit: a 30-minute class with five friends goes tight — code over time, three whole faces and "+2" beside them, rings uncut', r.bs.filter(b => b.wide));
  ok(r.bs.filter(b => b.wide).every(b => /· 5 friends in this class$/.test(b.title)), 'fit: the block title carries the friend count, so a narrow column never hides it', r.bs.filter(b => b.wide).map(b => b.title));
  ok(r.H === rest4, 'fit: still the same height with a 30-minute class focused', { focused: r.H, rest: rest4 });
  ok(log.errors.length === 0, 'fit: no page errors', log.errors);
  await close();
};

tests.schedule = async () => {
  const { page, close, log } = await openApp({});
  await click(page, '[data-a="tab"][data-x="schedule"]');
  let t = await text(page);
  ok(/My Classes/.test(t) && /5 classes/.test(t), 'schedule: my classes');
  ok(/BUS 2201[\s\S]*No section yet/.test(t), 'schedule: a saved class without a section is listed');
  ok(/Financial Markets[\s\S]*Bram Fixturesen · Mon\/Wed 10:10–12:00/.test(t), 'schedule: section line from the seat feed', t.slice(0, 600));
  ok(/Avery[\s\S]*in your section/.test(t), 'schedule: friends in my section');
  await click(page, '[data-a="schedTab"][data-x="planner"]');
  t = await text(page);
  await tick(page, 2500); t = await text(page);
  ok(/requirements filled/.test(t) && !/Finance concentration|Graduating Spring 2027/.test(t), 'schedule: the planner is the real ledger, not the prototype’s invented requirements');
  ok(log.errors.length === 0, 'schedule: no page errors', log.errors);
  await close();
};

tests.friends = async () => {
  const { page, close, log } = await openApp({});
  await click(page, '[data-a="tab"][data-x="friends"]');
  let t = await text(page);
  noProto(t, 'Friends');
  ok(/Avery Quill[\s\S]*Fixture reply from Avery/.test(t), 'friends: direct chat with last message', t.slice(0, 300));
  ok(/Fixture Study Group[\s\S]*Rowan: Fixture group note/.test(t), 'friends: group chat with sender');
  ok(await page.locator('.thread:has-text("Avery Quill") .udot').count() === 1 && await page.locator('.thread:has-text("Fixture Study Group") .udot').count() === 0, 'friends: unread follows last_read_at (Avery new, group already read)');
  await click(page, '.thread:has-text("Avery Quill")');
  await tick(page, 600);
  t = await text(page);
  ok(/Fixture message from me/.test(t) && /Fixture reply from Avery/.test(t), 'chat: messages load');
  ok(log.writes.some(w => w.table === 'conversation_members' && w.m === 'PATCH'), 'chat: opening marks it read');
  await page.locator('#chatin').fill('Hello from the test');
  await page.locator('#chatin').press('Enter');
  await tick(page, 600);
  const sent = log.writes.filter(w => w.table === 'messages');
  ok(sent.length === 1 && sent[0].body.body === 'Hello from the test' && sent[0].body.sender === FX.ME.id && sent[0].body.kind === 'text' && sent[0].body.conversation_id === FX.CONVS[0].id, 'chat: sends the real message row', sent[0] && sent[0].body);
  ok(/Hello from the test/.test(await text(page)), 'chat: sent message appears');
  await tick(page, 3000);
  ok(!/typing/.test(await page.locator('#scroll').innerHTML()) && await page.locator('#scroll .msg').count() === 3, 'chat: no invented reply (exactly the 3 real messages)', await page.locator('#scroll .msg').count());
  ok(log.errors.length === 0, 'friends: no page errors', log.errors);
  await close();
};

tests.requests = async () => {
  const { page, close, log } = await openApp({});
  await click(page, '[data-a="tab"][data-x="friends"]');
  await click(page, '[data-a="fFilter"][data-x="requests"]');
  ok(/Morgan Nobody/.test(await text(page)), 'requests: incoming request shown');
  await click(page, '[data-a="acceptReq"]');
  await tick(page, 600);
  const w = log.writes.filter(x => x.table === 'friend_requests');
  ok(w.length === 1 && w[0].m === 'PATCH' && w[0].body.status === 'accepted' && /id=eq\.990/.test(w[0].query), 'requests: accept updates that request by id', w);
  await click(page, '[data-a="fFilter"][data-x="all"]');
  await page.locator('.pym [data-a="addFriend"]').first().dblclick();
  await tick(page, 600);
  const w2 = log.writes.filter(x => x.table === 'friend_requests' && x.m === 'POST');
  ok(w2.length === 1 && w2[0].body.to_user === FX.SUGGESTED.id && w2[0].body.from_user === FX.ME.id && w2[0].body.status === 'pending', 'requests: Add (even double-tapped) sends ONE pending request', w2);
  ok(/Requested/.test(await page.locator('.pym').first().innerText()), 'requests: button turns to Requested');
  ok(log.errors.length === 0, 'requests: no page errors', log.errors);
  await close();
};

tests.friendProfile = async () => {
  const { page, close, log } = await openApp({});
  await click(page, '[data-a="tab"][data-x="friends"]');
  await click(page, '[data-a="fFilter"][data-x="people"]');
  await click(page, '.li:has-text("Rowan Testa")');
  let t = await text(page);
  ok(/UNIV 1101[\s\S]*No section yet/.test(t), 'friend: saved class with no section is listed, not drawn', t);
  await click(page, '[data-a="back"]');
  await click(page, '.li:has-text("Sky Placeholder")');
  t = await text(page);
  ok(/STAT 2170/.test(t) && !/ECON 2303/.test(t), 'friend: an orphaned section row (class not saved) is not shown', t);
  ok(log.errors.length === 0, 'friend: no page errors', log.errors);
  await close();
};

tests.champ = async () => {
  const asks = { 'open bus 3431 after 8': { tool: 'search_sections', args: { course: 'BUS3431', open_only: true } },
    'is ada good': { tool: 'professor_stats', args: { name: 'Ada Examplewood' } },
    'what is the weather': { tool: 'cant_answer', args: { reason: 'not_about_classes' } } };
  const { page, close, log } = await openApp({ ask: b => asks[b.q] || null });
  await click(page, '[data-a="openChamp"]');
  const say = async q => { await page.locator('#champin').fill(q); await page.locator('#champin').press('Enter'); await tick(page, 800); return (await page.locator('.bot .msg').last().innerText()); };
  let a = await say('open bus 3431 after 8');
  ok(/1 section matches/.test(a) && /Sec 02/.test(a) && !/Sec 01/.test(a) && !/§/.test(a), 'champ: search_sections answered from the real feed (open only)', a);
  ok(log.asks[0] && log.asks[0].term === '2268' && typeof log.asks[0].who === 'string' && log.asks[0].who.length === 16 && !('user_id' in log.asks[0]), 'champ: asks with term + 16-char pseudonym only', log.asks[0]);
  a = await say('is ada good');
  ok(/Ada Examplewood/.test(a) && /★4\.5 from 41 ratings/.test(a) && /67% would take again/.test(a), 'champ: professor_stats from real numbers', a);
  a = await say('what is the weather');
  ok(/only know Cal Poly classes/.test(a), 'champ: out of scope is refused', a);
  a = await say('BUS 4442');     // ask stand-in returns a fallback → local answer
  ok(/BUS 4442 · Investments/.test(a) && /Every section is full/.test(a), 'champ: local fallback answers a bare code', a);
  a = await say('write me a poem');
  ok(/not sure|can’t reach/.test(a) && !/★/.test(a), 'champ: unknown question says so, invents nothing', a);
  ok(log.errors.length === 0, 'champ: no page errors', log.errors);
  await close();
};

tests.seatsFail = async () => {
  const { page, close, log } = await openApp({ hook: (url, m) => url.pathname.endsWith('/course_seats') && /offset=0/.test(url.search) && !/limit=1&/.test(url.search) ? { status: 500, body: '{}' } : null });
  await click(page, '[data-a="tab"][data-x="explore"]');
  const t = await text(page);
  ok(/Couldn’t load Fall 2026 classes/.test(t) && await page.locator('#exlist .ccard').count() === 0, 'seats: a failed feed says so and shows no classes', t);
  ok(log.errors.length === 0, 'seats: no page errors', log.errors);
  await close();
};

tests.chatFail = async () => {
  const { page, close, log } = await openApp({ hook: (url, m) => url.pathname.endsWith('/messages') && /conversation_id=eq\./.test(url.search) && m === 'GET' ? { status: 500, body: '{"message":"boom"}' } : null });
  await click(page, '[data-a="tab"][data-x="friends"]');
  await click(page, '.thread:has-text("Avery Quill")');
  const t = await text(page);
  ok(/Couldn’t load these messages/.test(t) && !/Say hi/.test(t), 'chat: a failed load says so, never “empty”', t);
  await close();
};

tests.wordFilter = async () => {
  const { page, close, log } = await openApp({});
  await click(page, '[data-a="tab"][data-x="rate"]');
  await click(page, '.li:has-text("Bram Fixturesen")');
  await click(page, '[data-a="draft"][data-x="stars"][data-y="2"]');
  await click(page, '[data-a="draftMore"]');
  await page.locator('#revta').fill('this class was sh1t honestly');
  await click(page, '[data-a="postRating"]');
  const t = await page.locator('.rf').innerText();
  ok(/Reviews are public, so “shit” can’t go in one/.test(t) && !log.writes.some(w => w.table === 'reviews'), 'rate: the desktop’s word filter refuses before posting', t.slice(-300));
  ok(await page.locator('#revta').inputValue() === 'this class was sh1t honestly', 'rate: the text is kept');
  await close();
};

/* ---------------- PR 2: rating refusals, profile, settings, planner ---------------- */
const rateAda = async (page, text = 'Fixture words from the test.') => {
  await click(page, '[data-a="tab"][data-x="rate"]');
  await click(page, '.li:has-text("Ada Examplewood")');
  await click(page, '[data-a="draft"][data-x="stars"][data-y="4"]');
  await click(page, '[data-a="draftMore"]');
  await page.locator('#revta').fill(text); await tick(page);
  await click(page, '[data-a="postRating"]'); await tick(page, 800);
  return page.locator('.rf').innerText();
};
const refuse = (status, err) => (url, m) => url.pathname.endsWith('/rest/v1/reviews') && m === 'POST' ? { status, body: JSON.stringify(err) } : null;

tests.rateServerFault = async () => {
  /* What Tate hit on 2026-09-28: every insert refused because the policy's count can't read user_id. */
  const denied = { code: '42501', message: 'permission denied for table reviews' };
  const { page, close, log } = await openApp({ hook: refuse(403, denied), rpc: Object.assign({}, FX.RPC, { why_cant_i_review: { __error: denied } }) });
  const t = await rateAda(page, 'Kept words.');
  ok(/refusing every review, not just yours/.test(t) && /code 42501/.test(t) && !/limit/i.test(t), 'rate: the server fault is named, with its code, and never called a limit', t.slice(-300));
  ok(log.reads.includes('rpc:why_cant_i_review'), 'rate: asks why_cant_i_review() before explaining');
  await click(page, '[data-a="back"]');
  await click(page, '.li:has-text("Ada Examplewood")');
  ok(await page.locator('#revta').inputValue() === 'Kept words.', 'rate: the unposted review comes back when the form reopens');
  await close();
};
tests.rateRefusedReason = async () => {
  const rls = { code: '42501', message: 'new row violates row-level security policy for table "reviews"' };
  const why = [{ check_name: 'signed in', ok: true }, { check_name: 'email claim ends in .edu', ok: false, detail: 'x@icloud.com' }];
  const { page, close } = await openApp({ hook: refuse(403, rls), rpc: Object.assign({}, FX.RPC, { why_cant_i_review: why }) });
  const t = await rateAda(page);
  ok(/verified school email/.test(t) && !/limit/i.test(t), 'rate: an RLS refusal says the real failing check (.edu)', t.slice(-250));
  await close();
};
tests.rateP0001 = async () => {
  const { page, close } = await openApp({ hook: refuse(400, { code: 'P0001', message: 'This account is suspended, so it cannot post reviews right now.' }) });
  const t = await rateAda(page);
  ok(/This account is suspended, so it cannot post reviews right now\./.test(t), 'rate: the database’s own sentence is shown as written', t.slice(-200));
  await close();
};
tests.rateJwtRetry = async () => {
  let n = 0;
  const { page, close, log } = await openApp({ hook: (url, m) => { if (url.pathname.endsWith('/rest/v1/reviews') && m === 'POST' && n++ === 0) return { status: 401, body: JSON.stringify({ code: 'PGRST301', message: 'JWT expired' }) }; return null; } });
  const t = await rateAda(page);
  ok(/Thanks for your review/.test(await text(page)) && n === 2 && log.writes.filter(w => w.table === 'reviews').length === 1 && log.writes.some(w => /auth:token/.test(w.table)), 'rate: an expired sign-in is refreshed and the review posts', log.writes.map(w => w.table));
  await close();
};

tests.me = async () => {
  const { page, close, log } = await openApp({ tables: Object.assign({}, FX.TABLES, { reviews: [Object.assign({}, FX.MY_REVIEW)] }), rpc: Object.assign({}, FX.RPC, { my_reviews: [FX.MY_REVIEW] }) });
  await click(page, '.homehdr .me-btn'); await tick(page, 600);
  let t = await text(page);
  ok(/Jordan Fixture/.test(t) && /@jfixture/.test(t) && /Business Administration\n/.test(t) && /Junior · jordan\.fixture@calpoly\.edu/.test(t), 'me: profile shows real name, username, major, year and your own email', t.slice(0, 200));
  ok(!/%/.test(t.slice(0, t.indexOf('Your reviews'))), 'me: no degree-progress percentage');
  ok(/Your reviews[\s\S]*Faro Dummelow[\s\S]*BUS 4445[\s\S]*Fixture review I wrote\./.test(t), 'me: your own reviews listed');
  const exp = await page.evaluate(() => { const timed = TC.friends.filter(f => status(f).free !== null); return { n: myCodes().size, f: TC.friends.length, free: timed.filter(f => status(f).free === true).length, timed: timed.length }; });
  ok(new RegExp(`${exp.n}\\s*classes\\s*Fall 2026`).test(t) && new RegExp(`${exp.f}\\s*friends\\s*${exp.free} free right now`).test(t) && exp.n === 5 && exp.f === 5 && exp.timed > 0, 'me: class, friend and free-now counts are the real ones', [exp, t.match(/\d+\s*classes[\s\S]{0,60}/)]);
  ok(/My ratings\s*1 posted/.test(t) && /Who sees my schedule\s*Friends/.test(t) && /Name on my ratings\s*(Anonymous|Friends see 1)/.test(t) && /Degree Progress Report\s*Import PDF/.test(t) && /Major and concentration\s*Business Administration/.test(t), 'me: the settings rows show real values', t.slice(t.indexOf('My ratings'), t.indexOf('My ratings') + 260));
  ok((FX.MY_REVIEW.share_with_friends ? /Friends see 1/ : /Anonymous/).test(t), 'me: name-on-ratings matches your reviews’ own share setting');
  await click(page, '[data-a="editReview"]');
  ok(/EDIT YOUR REVIEW OF/.test(await page.locator('.rf').innerText()) && /Save changes/.test(await page.locator('.bottombar').innerText()), 'me: Edit opens the form headed as an edit, with Save changes');
  await click(page, '[data-a="draft"][data-x="stars"][data-y="2"]');
  await click(page, '[data-a="postRating"]'); await tick(page, 600);
  const w = log.writes.filter(x => x.table === 'reviews');
  ok(w.length === 1 && w[0].m === 'PATCH' && /id=eq\.77/.test(w[0].query) && w[0].body.score === 2 && !('professor_key' in w[0].body) && !('user_id' in w[0].body) && !('course' in w[0].body) && w[0].body.would_again === true, 'me: an edit PATCHes that review by id — not its professor or class, and keeps take-again', w);
  await click(page, '[data-a="askDeleteReview"]');
  ok(/Delete your review\?/.test(await page.locator('#sheet').innerText()), 'me: delete asks first');
  await click(page, '#sheet [data-a="deleteReview"]'); await tick(page, 400);
  ok(log.writes.some(x => x.table === 'reviews' && x.m === 'DELETE' && /id=eq\.77/.test(x.query)), 'me: delete removes that review by id');
  ok(log.errors.length === 0, 'me: no page errors', log.errors);
  await close();
};

tests.meNothingChanged = async () => {
  /* RLS refuses a delete by changing nothing: that must not be reported as done. */
  const { page, close } = await openApp({ rpc: Object.assign({}, FX.RPC, { my_reviews: [FX.MY_REVIEW] }) });
  await click(page, '.homehdr .me-btn'); await tick(page, 600);
  await click(page, '[data-a="askDeleteReview"]'); await click(page, '#sheet [data-a="deleteReview"]'); await tick(page, 400);
  ok(/still there/.test(await page.locator('#toast').innerText()), 'me: a delete that removed nothing says so', await page.locator('#toast').innerText());
  await close();
};

tests.settings = async () => {
  const { page, close, log } = await openApp({});
  await click(page, '.homehdr .me-btn'); await click(page, '[data-a="openSettings"]'); await tick(page, 500);
  let t = await text(page);
  ok(/Signed in as\s*jordan\.fixture@calpoly\.edu/.test(t), 'settings: shows the signed-in email');
  ok(/Blocked Fixture/.test(t), 'settings: blocked people from my_blocks()');
  await click(page, '[data-a="unblock"]');
  ok(log.reads.includes('rpc:unblock_user') && !/Blocked Fixture/.test(await text(page)), 'settings: unblock calls unblock_user() and drops the row');
  await click(page, '[data-a="togglePlanShare"][data-x="B"]'); await tick(page, 400);
  const pw = log.writes.filter(x => x.table === 'plans');
  ok(pw.length === 1 && pw[0].body.slot === 'B' && pw[0].body.shared === false, 'settings: turning off Plan B sharing writes shared=false', pw);
  await page.locator('#setpw').fill('short'); await page.locator('#setpw').press('Enter'); await tick(page);
  ok(/At least 8 characters/.test(await text(page)) && !log.writes.some(x => x.table === 'auth:user'), 'settings: a short password is refused before it is sent');
  await page.locator('#setpw').fill('a-long-fixture-pw'); await page.locator('#setpw').press('Enter'); await tick(page, 500);
  ok(log.writes.some(x => x.table === 'auth:user' && x.body && x.body.password === 'a-long-fixture-pw') && /Password changed/.test(await text(page)), 'settings: password change goes to Supabase Auth');
  await click(page, '[data-a="openLegal"][data-x="privacy"]'); await tick(page, 1500);
  t = await text(page);
  ok(/Privacy/.test(t) && /Last updated/i.test(t) && t.length > 2000, 'settings: the privacy policy is the desktop’s own text', t.slice(0, 120));
  ok(log.errors.length === 0, 'settings: no page errors', log.errors);
  await close();
};

tests.editProfile = async () => {
  const { page, close, log } = await openApp({});
  await click(page, '.homehdr .me-btn'); await click(page, '[data-a="openEditProfile"]'); await tick(page, 1500);
  ok(await page.locator('select[data-k="major"] option').count() > 60, 'edit: major list is the flowchart majors');
  await page.locator('#ep-user').fill('admin'); await tick(page);
  ok(/reserved/.test(await page.locator('#ep-usermsg').innerText()), 'edit: a reserved username is refused on the spot');
  await page.locator('#ep-user').fill('jfixture_2'); await tick(page, 800);
  ok(/available/.test(await page.locator('#ep-usermsg').innerText()) && log.reads.includes('rpc:username_taken'), 'edit: availability checked with username_taken()');
  await page.locator('#ep-name').fill('Jordan Q Fixture');
  await page.locator('select[data-k="class_standing"]').selectOption('Senior'); await tick(page);
  const png = Buffer.from('iVBORw0KGgoAAAANSUhEUgAAAAIAAAADCAYAAAC56t6BAAAAEklEQVR4nGP4z8DwnwEIGBgYAB3wA/3kDNRfAAAAAElFTkSuQmCC', 'base64');
  await page.locator('#epfile').setInputFiles({ name: 'me.png', mimeType: 'image/png', buffer: png }); await tick(page, 800);
  await click(page, 'form[data-submit="saveProfile"] .btn'); await tick(page, 800);
  const up = log.writes.find(x => /^storage:avatars\//.test(x.table));
  const pr = log.writes.filter(x => x.table === 'profiles' && x.m === 'PATCH');
  ok(up && /avatar\.jpg$/.test(up.table) && up.bytes > 100, 'edit: photo uploaded as a square JPEG to avatars/<id>/avatar.jpg', up);
  const b = pr[0] && pr[0].body;
  ok(b && b.display_name === 'Jordan Q Fixture' && b.username === 'jfixture_2' && b.class_standing === 'Senior' && /avatar\.jpg\?v=\d+/.test(b.avatar_url || '') && b.major === 'Business Administration', 'edit: profile row patched with every field', b);
  ok(/Jordan Q Fixture/.test(await text(page)), 'edit: the new name shows straight away');
  ok(log.errors.length === 0, 'edit: no page errors', log.errors);
  await close();
};

/* Prerequisites as one answer (2026-09-29): the class page shows only the verdict; anything short
   of fulfilled opens the Planner with the classes still needed. */
/* The profile picture is on Home only (2026-09-30), as on the live /app. */
tests.profileHomeOnly = async () => {
  const { page, close, log } = await openApp({});
  ok(await page.locator('.homehdr .me-btn').count() === 1, 'profile button: on Home');
  for (const tab of ['explore', 'rate', 'schedule', 'friends']) {
    await click(page, `[data-a="tab"][data-x="${tab}"]`);
    ok(await page.locator('#scroll .me-btn').count() === 0, `profile button: not on ${tab}`);
  }
  await click(page, '[data-a="tab"][data-x="home"]'); await click(page, '.homehdr .me-btn'); await tick(page, 600);
  ok(/Edit profile/.test(await text(page)), 'profile button: Home still opens the profile page');
  ok(log.errors.length === 0, 'profile button: no page errors', log.errors);
  await close();
};

/* Tapping a class on a friend's week opens the same preview as My Classes / Plans, with who is in it (2026-09-30). */
tests.homeSecPreview = async () => {
  const { page, close, log } = await openApp({});
  const avery = FX.FRIENDS[0].id, sky = FX.FRIENDS[2].id;
  await click(page, `#hf-${sky} .g-b[data-x="BUS 3438"]`); await tick(page, 400);
  let sh = (await page.locator('#sheet').innerText()).replace(/\s+/g, ' ');
  ok(/BUS 3438/.test(sh) && /View class/.test(sh), 'home preview: tapping a friend’s class opens the section preview', sh.slice(0, 200));
  ok(await page.locator('.homehdr').count() === 1, 'home preview: it stays on Home (no jump to the class page)');
  ok(/IN THIS SECTION (\w+ )?You (\w+ )?Sky/i.test(sh), 'home preview: you and the friend in the same section are listed', sh);
  await click(page, '[data-a="closeSheet"]');
  await click(page, `#hf-${avery} .g-b[data-x="BUS 3431"]`); await tick(page, 400);
  sh = (await page.locator('#sheet').innerText()).replace(/\s+/g, ' ');
  ok(/IN THIS SECTION (\w+ )?Avery/i.test(sh) && /OTHER SECTIONS (\w+ )?You/i.test(sh) && !/IN THIS SECTION[^O]*You/i.test(sh), 'home preview: a friend in another section of your class — you are under Other sections', sh);
  const names = await page.locator('#sheet [data-a="openFriend"]').evaluateAll(es => es.map(e => [e.dataset.x, Math.round(e.getBoundingClientRect().height)]));
  ok(names.length >= 1 && names.every(([, h]) => h >= 44), 'home preview: friend names are 44px buttons', names);
  await click(page, '#sheet [data-a="openFriend"]'); await tick(page, 600);
  ok(await page.locator('#sheet .sheet').count() === 0 && /Avery/.test(await text(page)), 'home preview: tapping a friend opens their page');
  await click(page, '.g-b[data-x="BUS 3431"]'); await tick(page, 400);
  sh = (await page.locator('#sheet').innerText()).replace(/\s+/g, ' ');
  ok(/IN THIS SECTION (\w+ )?Avery/i.test(sh), 'home preview: the friend page week opens the same preview', sh.slice(0, 300) || await text(page).then(x => x.slice(0, 300)));
  await click(page, '#sheet [data-a="openClass"]'); await tick(page, 600);
  ok(/Sections/.test(await text(page)) && /BUS 3431/.test(await text(page)), 'home preview: View class opens the class page');
  ok(log.errors.length === 0, 'home preview: no page errors', log.errors);
  await close();
};

/* Scrolling down tucks the tab bar and Champ away; a small scroll up brings them back (2026-09-30). */
tests.scrollHideBars = async () => {
  const { page, close, log } = await openApp({});
  const st = () => page.evaluate(() => { const ch = document.getElementById('chrome'), tb = ch.querySelector('.tabbar'), fab = ch.querySelector('.fab');
    const W = document.querySelector('.phone').getBoundingClientRect(); const r = fab && fab.querySelector('img').getBoundingClientRect(), tr = tb && tb.getBoundingClientRect();
    return { hid: ch.classList.contains('bars-hid'), typing: ch.classList.contains('bub-type'), tbTop: tr && Math.round(tr.top - W.bottom), imgVis: r && Math.round(W.right - r.left), bub: fab && getComputedStyle(fab.querySelector('.bub')).opacity, H: document.getElementById('scroll').scrollHeight - document.getElementById('scroll').clientHeight }; });
  const scrollTo = async y => { await page.evaluate(y => { document.getElementById('scroll').scrollTop = y; }, y); await page.waitForTimeout(80); await page.clock.runFor(600); await page.waitForTimeout(450); };
  let s = await st();
  ok(!s.hid && s.H > 200, 'scroll bars: shown at rest, and Home scrolls', s);
  await scrollTo(30); ok(!(await st()).hid, 'scroll bars: a nudge near the top keeps them');
  await scrollTo(250); s = await st();
  ok(s.hid && s.tbTop >= -1, 'scroll bars: scrolling down slides the tab bar off the bottom', s);
  ok(s.imgVis >= 34 && s.imgVis < 50 && +s.bub < 0.05, 'scroll bars: Champ peeks out from the right edge (most of him showing) and his bubble is gone', s);
  await page.evaluate(() => { document.getElementById('scroll').scrollTop = 245; }); await page.waitForTimeout(60);
  ok((await st()).hid, 'scroll bars: a 5px wobble up does not bring them back');
  await page.evaluate(() => { document.getElementById('scroll').scrollTop = 230; }); await page.waitForTimeout(60); s = await st();
  ok(!s.hid && !s.typing, 'scroll bars: a small scroll up brings them back, with no typing effect', s);
  await page.clock.runFor(1500); await page.waitForTimeout(80);
  ok(/Ask Me!/.test(await page.locator('.fab .bub').innerText()) && +(await st()).bub > 0.95 && await page.evaluate(() => getComputedStyle(document.querySelector('.fab .bub .t')).animationName === 'none'), 'scroll bars: the bubble is back, whole, with nothing typing');
  await scrollTo(600); ok((await st()).hid, 'scroll bars: hidden again going down');
  await page.locator('#chrome .fab').click({ force: true }); await page.waitForTimeout(150); await page.clock.runFor(400);
  ok(await page.locator('#champin').count() === 1, 'scroll bars: the peeking Champ still opens Champ');
  await page.evaluate(() => { const x = document.querySelector('#sheet [data-a="closeSheet"]'); if (x) x.click(); }); await page.clock.runFor(300); await page.waitForTimeout(80);
  await page.evaluate(() => { document.getElementById('scroll').scrollTop = 900; }); await page.waitForTimeout(80);
  const tab = async x => { await page.evaluate(x => document.querySelector(`#chrome .tab[data-x="${x}"]`).click(), x); await page.clock.runFor(500); await page.waitForTimeout(120); };
  await tab('explore'); ok(!(await st()).hid, 'scroll bars: a new screen brings the bars back');
  await scrollTo(900); ok((await st()).hid, 'scroll bars: hidden again on Explore');
  await tab('home');   /* Home comes back at its saved scroll, far from the top */
  const back = await st(); ok(!back.hid && await page.evaluate(() => document.getElementById('scroll').scrollTop) > 100, 'scroll bars: returning to a screen mid-page still brings the bars back', back);
  ok(log.errors.length === 0, 'scroll bars: no page errors', log.errors);
  await close();
};

/* Recent searches on Explore, each with its own x (2026-09-30). */
tests.recentSearches = async () => {
  const { page, close, log } = await openApp({});
  const tick2 = async (ms = 500) => { await page.clock.runFor(ms); await page.waitForTimeout(120); };
  await click(page, '[data-a="tab"][data-x="explore"]');
  await click(page, '#exlist [data-x="BUS 4401"]'); await tick2();          // opened from browsing, not a search
  await click(page, '[data-a="back"]');
  await page.locator('#exq').focus(); await tick2();
  ok(await page.locator('.rs').count() === 0, 'recent: nothing recorded from plain browsing, so no Recent panel');
  await page.locator('#exq').fill('strat'); await tick2();
  await click(page, '#exlist [data-x="BUS 4401"]'); await tick2();
  await click(page, '[data-a="back"]');
  await click(page, '[data-a="exMode"][data-x="profs"]');
  await page.locator('#exq').fill('ada'); await tick2();
  const pid = await page.locator('#exlist [data-a="openProf"]').first().getAttribute('data-x');
  await click(page, `#exlist [data-a="openProf"][data-x="${pid}"]`); await tick2();
  await click(page, '[data-a="back"]');
  await page.locator('#exq').fill(''); await page.locator('#exq').focus(); await tick2();
  let rows = await page.locator('.rs .rs-open').allInnerTexts();
  ok(rows.length === 2 && /Ada/.test(rows[0]) && /BUS 4401/.test(rows[1]), 'recent: the empty focused box shows Recent, newest first, classes and professors together', rows);
  const xs = await page.locator('.rs .rs-x').evaluateAll(es => es.map(e => [Math.round(e.getBoundingClientRect().width), Math.round(e.getBoundingClientRect().height), e.getAttribute('aria-label')]));
  ok(xs.length === 2 && xs.every(([w, h, l]) => w >= 44 && h >= 44 && /^Remove .+ from recent$/.test(l)), 'recent: each row has a small labelled x with a 44px target', xs);
  await page.locator('.rs .rs-x').nth(1).click(); await tick2();
  rows = await page.locator('.rs .rs-open').allInnerTexts();
  ok(rows.length === 1 && /Ada/.test(rows[0]), 'recent: the x removes just that one and the panel stays open', rows);
  const stored = await page.evaluate(() => JSON.parse(localStorage.getItem('termchamp_app_recent')));
  ok(stored && stored.items.length === 1 && stored.items[0].k === 'p', 'recent: removal is saved on the phone', stored);
  await page.locator('#exq').fill('x'); await tick2();
  ok(await page.locator('.rs').count() === 0, 'recent: typing hides Recent and shows results');
  await page.locator('#exq').fill(''); await page.locator('#exq').focus(); await tick2();
  await click(page, '.rs [data-a="recentOpen"]'); await tick2();
  ok(await page.locator('.hero').count() === 1 && /Ada/.test(await text(page)), 'recent: tapping a recent opens it');
  await click(page, '[data-a="back"]'); await page.locator('#exq').focus(); await tick2();
  await click(page, '.rs [data-a="recentClear"]'); await tick2();
  ok(await page.locator('.rs').count() === 0 && (await page.evaluate(() => JSON.parse(localStorage.getItem('termchamp_app_recent')).items.length)) === 0, 'recent: Clear all empties it');
  await page.locator('#exq').blur(); await tick2(600);
  ok(await page.locator('#exlist .card').count() > 1, 'recent: leaving the box brings back the browse list');
  await page.evaluate(() => localStorage.setItem('termchamp_app_recent', JSON.stringify({ u: JSON.parse(localStorage.getItem('termchamp_app_recent')).u, items: [{ k: 'c', x: 'BUS 4401' }] })));
  await page.locator('#exq').focus(); await tick2();
  ok(await page.locator('.rs').count() === 1, 'recent: focus shows it again');
  await click(page, '[data-a="tab"][data-x="home"]'); await click(page, '[data-a="tab"][data-x="explore"]'); await tick2();
  ok(await page.locator('.rs').count() === 0 && await page.locator('#exlist .card').count() > 1, 'recent: tabbing away and back (box not focused) shows the browse list, not Recent');
  /* Another account's recents on the same phone are never shown. */
  await page.evaluate(() => localStorage.setItem('termchamp_app_recent', JSON.stringify({ u: 'someone-else', items: [{ k: 'c', x: 'BUS 4401' }] })));
  await page.locator('#exq').focus(); await tick2();
  ok(await page.locator('.rs').count() === 0, 'recent: another account’s recent searches never show');
  ok(log.errors.length === 0 && !log.writes.some(w => /recent/i.test(JSON.stringify(w))), 'recent: no page errors and nothing sent to the server', log.errors);
  await close();
};

tests.prereqVerdict = async () => {
  const PQ = [
    { course_code: 'STAT 2170', prereq_json: { req: [['MATH 1000', 'MATH 1180'], ['PHIL 3331']] } },   // one done, one missing
    { course_code: 'ECON 2303', prereq_json: { req: [['PHIL 3331']] } },                                 // on the record
    { course_code: 'BUS 4401', prereq_json: { req: [['BUS 3431']] } },                                   // taking it now
    { course_code: 'BUS 3346', prereq_json: { req: [['PHIL 3331']] } },                                  // the class, plus "Junior standing"
  ];
  const asks = { 'prereqs for stat 2170': { tool: 'prereqs', args: { course: 'STAT2170' } } };
  const { page, close, log } = await openApp({ tables: Object.assign({}, FX.TABLES, { course_prereqs: PQ }), ask: q => asks[q.q] || null });
  const tile = async () => (await page.locator('.hero .stats > :nth-child(2)').innerText()).replace(/\s+/g, ' ').trim();
  const openC = async c => { await click(page, '[data-a="tab"][data-x="explore"]'); if (!await page.locator('#exlist').count()) await click(page, '[data-a="tab"][data-x="explore"]'); await click(page, `#exlist [data-x="${c}"]`); await tick(page, 2500); };
  await openC('ECON 2303');
  ok(await tile() === 'PREREQ Fulfilled', 'prereq: a met prerequisite reads “Fulfilled”', await tile());
  ok(await page.locator('.hero .stat.pq').count() === 0, 'prereq: “Fulfilled” is not a button');
  ok(!/PHIL 3331/.test(await page.locator('.hero').innerText()), 'prereq: the class list is not shown on the class page');
  await openC('BUS 4401');
  ok(await tile() === 'PREREQ In progress', 'prereq: a prerequisite taken this term reads “In progress”', await tile());
  await openC('BUS 4488');
  ok(await tile() === 'PREREQ None listed', 'prereq: nothing listed anywhere → “None listed”', await tile());
  await openC('BUS 3346');
  ok(await tile() === 'PREREQ Check note', 'prereq: classes met but Cal Poly also lists standing → “Check note”, not “Fulfilled”', await tile());
  await click(page, '.hero .stat.pq');
  const note = await page.locator('#sheet').innerText();
  ok(/classes it needs are on your record/.test(note) && /Cal Poly lists: Junior standing/.test(note), 'prereq: the note says what is met and what Cal Poly also lists', note);
  await click(page, '[data-a="closeSheet"]');
  await openC('STAT 2170');
  ok(await tile() === 'PREREQ Not fulfilled', 'prereq: a missing prerequisite reads “Not fulfilled”', await tile());
  const lbl = await page.locator('.hero .stat.pq').getAttribute('aria-label');
  const box = await page.locator('.hero .stat.pq').boundingBox();
  ok(/Not fulfilled\. Show the classes/.test(lbl) && box.height >= 44, 'prereq: the tile is a labelled button at least 44px tall', { lbl, h: box.height });
  const [bg, fg] = await page.locator('.pqv.bad').evaluate(e => [getComputedStyle(e).backgroundColor, getComputedStyle(e).color]);
  const L = c => { const v = c.match(/\d+/g).slice(0, 3).map(x => { x /= 255; return x <= .03928 ? x / 12.92 : ((x + .055) / 1.055) ** 2.4; }); return .2126 * v[0] + .7152 * v[1] + .0722 * v[2]; };
  const cr = (Math.max(L(bg), L(fg)) + .05) / (Math.min(L(bg), L(fg)) + .05);
  ok(cr >= 4.5, 'prereq: the verdict pill text is ≥4.5:1', cr.toFixed(2));
  await click(page, '.hero .stat.pq'); await tick(page, 2500);
  ok(await page.locator('.tabbar .tab.on').getAttribute('data-x') === 'schedule' && await page.locator('.stabs .on').innerText() === 'Planner', 'prereq: “Not fulfilled” opens Schedule › Planner');
  let t = await text(page);
  ok(t.indexOf('Before') >= 0 && t.indexOf('Before') < t.indexOf('requirements filled'), 'prereq: the card sits above the rest of the Planner', t.slice(0, 300));
  ok(/You need 1 more class before STAT 2170/.test(t), 'prereq: the card says what is left', t.slice(0, 400));
  ok(/Still need · any one[\s\S]*MATH 1000[\s\S]*MATH 1180/.test(t), 'prereq: an either/or group lists each class that satisfies it');
  ok(/✓ PHIL 3331 · on your record/.test(t), 'prereq: the part already done is ticked, not listed as needed');
  ok(!/Add your past classes/.test(t), 'prereq: no “add your past classes” nudge when history exists');
  const sizes = await page.locator('.tc-pqfor .xbtn, .tc-pqfor .tc-sech .code').evaluateAll(es => es.map(e => Math.round(e.getBoundingClientRect().height)));
  ok(sizes.length === 2 && sizes.every(h => h >= 44), 'prereq: the card’s close and class buttons are ≥44px', sizes);
  await click(page, '.tc-pqfor [data-a="plCourse"][data-x="MATH 1000"]');
  ok(/MATH 1000/.test(await page.locator('#sheet').innerText()), 'prereq: a class not offered this term opens its planner sheet');
  await click(page, '[data-a="closeSheet"]');
  await click(page, '[data-a="tab"][data-x="home"]'); await click(page, '[data-a="tab"][data-x="schedule"]'); await tick(page, 800);
  ok(await page.locator('.tc-pqfor').count() === 0, 'prereq: leaving Schedule clears the card');
  await openC('STAT 2170'); await click(page, '.hero .stat.pq'); await tick(page, 1500);
  await click(page, '[data-a="plForClose"]');
  ok(await page.locator('.tc-pqfor').count() === 0 && /requirements filled/.test(await text(page)), 'prereq: the card closes and the Planner stays');
  await click(page, '[data-a="openChamp"]');
  await page.locator('#champin').fill('prereqs for stat 2170'); await page.locator('#champin').press('Enter'); await tick(page, 800);
  const ch = await page.locator('.bot .msg').last().innerText();
  ok(/Not yet\. You still need MATH 1000 or MATH 1180 for STAT 2170/.test(ch) && /Show in Planner/.test(await page.locator('#sheet').innerText()), 'prereq: Champ gives the same answer, with a way to the Planner', ch);
  const reads = log.reads.filter(r => /^course_prereqs/.test(r)).length;
  ok(reads === 1, 'prereq: course_prereqs is read once, not on every render', reads);
  ok(log.errors.length === 0, 'prereq: no page errors', log.errors);
  await close();

  /* The answers that must never be a guess. Each opens the app with one input broken. */
  const tileFor = async (code, tables, hook) => {
    const o = await openApp({ tables: Object.assign({}, FX.TABLES, { course_prereqs: PQ }, tables || {}), hook });
    await click(o.page, '[data-a="tab"][data-x="explore"]'); await click(o.page, `#exlist [data-x="${code}"]`); await tick(o.page, 2500);
    const v = (await o.page.locator('.hero .stats > :nth-child(2)').innerText()).replace(/\s+/g, ' ').trim();
    return { v, o };
  };
  const fail = tbl => (url, m) => url.pathname.endsWith('/' + tbl) && m === 'GET' ? { status: 500, body: '{"message":"boom"}' } : null;
  for (const [tbl, code] of [['class_history', 'STAT 2170'], ['class_waivers', 'STAT 2170'], ['saved_classes', 'BUS 4401'], ['course_prereqs', 'STAT 2170']]) {
    const { v, o } = await tileFor(code, null, fail(tbl));
    ok(v === 'PREREQ Can’t check', `prereq: ${tbl} failed to load → “Can’t check”`, v);
    await o.close();
  }
  { /* A quarter-era class on the record counts through the crosswalk — and if the crosswalk fails, that's unknown, not "Not fulfilled". */
    const T = { class_history: [{ user_id: FX.ME.id, code: 'ZZZ 101', term: 'Spring', year: 2025, professor: null }], course_equiv: [{ legacy_code: 'ZZZ 101', current_code: 'ZZZ 1101' }],
      course_prereqs: [{ course_code: 'ECON 2303', prereq_json: { req: [['ZZZ 1101']] } }] };
    let { v, o } = await tileFor('ECON 2303', T); ok(v === 'PREREQ Fulfilled', 'prereq: a legacy code on the record counts via the crosswalk', v); await o.close();
    ({ v, o } = await tileFor('ECON 2303', T, fail('course_equiv'))); ok(v === 'PREREQ Can’t check', 'prereq: crosswalk failed → “Can’t check”, never “Not fulfilled”', v); await o.close();
  }
  { const { v, o } = await tileFor('BUS 3346', { course_prereqs: [{ course_code: 'BUS 3346', prereq_json: { req: [] } }] });
    ok(v === 'PREREQ Can’t check', 'prereq: a standing-only prerequisite is “Can’t check”, never “Fulfilled”', v);
    await click(o.page, '.hero .stat.pq'); ok(/Cal Poly lists: Junior standing/.test(await o.page.locator('#sheet').innerText()), 'prereq: “Can’t check” shows what Cal Poly lists'); await o.close(); }
  { const { v, o } = await tileFor('STAT 2170', { course_prereqs: [{ course_code: 'STAT 2170', prereq_json: { req: [['MATH 1000']], concurrent: ['MATH 1000'] } }] });
    ok(v === 'PREREQ Take together', 'prereq: a corequisite reads “Take together”', v); await o.close(); }
  { /* With nothing logged, "Not fulfilled" would just mean an empty record — so it isn't said. */
    const { v, o } = await tileFor('STAT 2170', { class_history: [], class_waivers: [] });
    ok(v === 'PREREQ Can’t check', 'prereq: an empty record reads “Can’t check”, not “Not fulfilled”', v);
    await click(o.page, '.hero .stat.pq'); await tick(o.page, 2500);
    const bt = await text(o.page);
    ok(/Nothing’s logged in your past classes yet/.test(bt) && /MATH 1000/.test(bt) && await o.page.locator('.tc-pqfor input[data-in="dprfile"]').count() === 1, 'prereq: …and the Planner card lists what it needs and offers Log a class / Import report', bt.slice(0, 400));
    await o.close(); }
};

tests.planner = async () => {
  const T = Object.assign({}, FX.TABLES, { course_seats: FX.TABLES.course_seats.concat([{ term: '2268', course_code: 'COMS 1101', title: 'Public Speaking', section: '01', instructor: 'Mockridge, Dov', days: 'MoWe 8:10AM - 9:30AM', status: 'Open', capacity: 30, enrolled: 20, available: 10, waitlist_total: 0, waitlist_capacity: 0, class_nbr: '71001', instruction_mode: 'In Person', location: '' }]) });
  const { page, close, log } = await openApp({ tables: T });
  await click(page, '[data-a="tab"][data-x="schedule"]'); await click(page, '[data-a="schedTab"][data-x="planner"]'); await tick(page, 2500);
  let t = await text(page);
  ok(/Business Administration/.test(t) && /2 of 31\s*requirements filled/.test(t) && /4 in progress/.test(t), 'planner: the desktop’s ledger — 2 of 31 filled, 4 in progress (one via the ENGL 1134 waiver)', (t.match(/[\s\S]{0,40}requirements filled[\s\S]{0,60}/) || [''])[0]);
  ok(/We can’t check 12 from your record/.test(t), 'planner: what it can’t judge is listed, not counted');
  ok(/Still need[\s\S]*BUS 1100[\s\S]*Career Readiness I/.test(t), 'planner: still-need list in flowchart order');
  ok(/STAT 1210[\s\S]{0,160}Needs MATH 1000 first/.test(t), 'planner: prerequisites from course_prereqs say what is missing');
  ok(/PHIL 3331/.test(t) && /Spring 2026/i.test(t) && /ENGL 1134\s*AP \/ IB credit/.test(t), 'planner: past classes and waivers listed, with the desktop’s reason labels', t.slice(t.indexOf('Past classes'), t.indexOf('Past classes') + 200));
  ok(/Pick your concentration/.test(t) && /Financial Management/.test(t), 'planner: concentration choices from the catalog');
  await click(page, '[data-a="plGe"][data-x="1C"]'); await tick(page);
  const g = await page.locator('#sheet').innerText();
  ok(/Oral Communication \(1C\)/.test(g) && /COMS 1101/.test(g) && /1 of \d+ classes in this area are offered Fall 2026/.test(g), 'planner: a GE area lists this term’s real classes for it', g.slice(0, 200));
  await click(page, '[data-a="closeSheet"]');
  await click(page, '[data-a="sheet"][data-x="logClass"]');
  await page.locator('#lc-code').fill('bus 2214'); await page.locator('#lc-term').selectOption('Fall'); await page.locator('#lc-year').selectOption('2025');
  await click(page, 'form[data-submit="logClass"] .btn'); await tick(page, 600);
  const w = log.writes.filter(x => x.table === 'class_history');
  ok(w.length === 1 && w[0].m === 'POST' && w[0].body.code === 'BUS 2214' && w[0].body.term === 'Fall' && w[0].body.year === 2025 && w[0].body.user_id === FX.ME.id && !('grade' in w[0].body), 'planner: logging a class upserts the desktop’s class_history row (no grade)', w);
  t = await text(page);
  ok(/3 of 31\s*requirements filled/.test(t), 'planner: the ledger moves when a class is logged', (t.match(/\d+ of 31/) || [''])[0]);
  await click(page, '[data-a="askRemoveHistory"][data-x="PHIL 3331"]');
  await click(page, '#sheet [data-a="removeHistory"]'); await tick(page, 400);
  ok(log.writes.some(x => x.table === 'class_history' && x.m === 'DELETE' && /code=eq\.PHIL/.test(x.query)), 'planner: remove asks, then deletes that row');
  ok(log.errors.length === 0, 'planner: no page errors', log.errors);
  await close();
};

tests.plannerMissing = async () => {
  const { page, close } = await openApp({ hook: (url, m) => url.pathname.endsWith('/class_history') && /user_id=eq/.test(url.search) && m === 'GET' ? { status: 500, body: '{}' } : null });
  await click(page, '[data-a="tab"][data-x="schedule"]'); await click(page, '[data-a="schedTab"][data-x="planner"]'); await tick(page, 2500);
  const t = await text(page);
  ok(/Couldn’t load your past classes/.test(t) && !/requirements filled/.test(t), 'planner: no count is shown when its inputs didn’t load', t.slice(0, 300));
  await close();
};

tests.wordmark = async () => {
  const { page, close } = await openApp({});
  const t = await page.locator('.homehdr').innerText();
  ok(/^TermChamp/.test(t.trim()) && await page.locator('.homehdr img.logo').count() === 0, 'design: Home header is the TermChamp wordmark, not the tile', t);
  await close();
};

tests.ovalRing = async () => {
  const { page, close } = await openApp({});
  await click(page, '[data-a="tab"][data-x="friends"]');
  const boxes = await page.locator('.thread .ringav').evaluateAll(els => els.map(e => { const r = e.getBoundingClientRect(); return [Math.round(r.width), Math.round(r.height)]; }));
  const disp = await page.locator('.thread .ringav').evaluateAll(els => els.map(e => getComputedStyle(e).display));
  ok(boxes.length && boxes.every(([w, h]) => w === h) && disp.every(d => /grid/.test(d)), 'design: chat avatar rings are circle boxes, not inline spans (which drew ovals on iPhone)', { boxes, disp });
  await close();
};

/* ---------------- PR 3: tags, DPR, year grid, friends' plans ---------------- */
tests.rateTags = async () => {
  const { page, close, log } = await openApp({});
  await click(page, '[data-a="tab"][data-x="rate"]');
  await click(page, '.li:has-text("Ada Examplewood")');
  await click(page, '[data-a="draft"][data-x="stars"][data-y="5"]');
  await click(page, '[data-a="draftMore"]');
  const chips = await page.locator('.tc-tags button').allInnerTexts();
  ok(chips.length === 10 && chips.includes('Graded fairly & transparently') && !chips.some(c => /unclear|busywork/i.test(c)), 'rate: the desktop’s “did well” chips, and none of the unsaved “struggled” ones', chips);
  await click(page, '.tc-tags button:has-text("Explains concepts clearly")');
  await click(page, '.tc-tags button:has-text("Helpful in office hours")');
  await click(page, '[data-a="postRating"]'); await tick(page, 800);
  const r = (log.writes.find(w => w.table === 'reviews') || {}).body;
  ok(r && JSON.stringify(r.tags) === JSON.stringify(['Explains concepts clearly', 'Helpful in office hours']), 'rate: picked chips are the review’s tags', r && r.tags);
  await close();
};

tests.plannerGrid = async () => {
  const { page, close, log } = await openApp({});
  await click(page, '[data-a="tab"][data-x="schedule"]'); await click(page, '[data-a="schedTab"][data-x="planner"]'); await tick(page, 2500);
  const t = await text(page);
  ok(/Your flowchart[\s\S]*Year 1[\s\S]*of \d+ done/.test(t), 'grid: the flowchart by year');
  const y1 = await page.locator('.tc-year').first().innerText();
  ok(/Fall/i.test(y1) && /BUS 1100[\s\S]*Career Readiness I/.test(y1) && /✓\s*GE · Area 1A/.test(y1), 'grid: Year 1 is open, with the waiver filling GE 1A (✓) — the same state the ledger counts', y1.slice(0, 400));
  const heads = await page.locator('.tc-yearh').allInnerTexts();
  const judged = heads.reduce((a, h) => a + (+((h.match(/of (\d+) done/) || [])[1] || 0)), 0);
  ok(judged === 31 && /can’t check/.test(heads[0]), 'grid: the years add up to the ledger’s 31, with can’t-check slots said separately', heads);
  ok(await page.locator('.tc-year').nth(1).locator('.tc-cell').count() === 0, 'grid: later years start folded');
  await click(page, '[data-a="plYear"][data-x="2"]');
  ok(await page.locator('.tc-year').nth(1).locator('.tc-cell').count() > 3, 'grid: tapping a year opens it');
  await click(page, '.tc-year >> nth=0 >> [data-a="plLogSlot"][data-x="BUS 1100"]');
  ok(await page.locator('#lc-code').inputValue() === 'BUS 1100', 'grid: tapping a class to do opens Log a class with its code filled in');
  ok(log.errors.length === 0, 'grid: no page errors', log.errors);
  await close();
};

tests.dprFromProfile = async () => {
  const { page, close, log } = await openApp({});
  await click(page, '.homehdr .me-btn'); await tick(page, 600);
  await page.locator('input[data-in="dprfile"]').setInputFiles('files/dpr-fixture.pdf');
  for (let i = 0; i < 20 && !(await page.locator('#sheet .tc-dprrow').count()); i++) await tick(page, 500);
  const sh = await page.locator('#sheet').innerText();
  ok(/Past classes · 4/i.test(sh) && /PHIL 3331[\s\S]{0,80}already logged/.test(sh), 'dpr (profile): Import PDF on your profile reads the report, knowing your past classes', sh.slice(0, 200));
  ok(log.errors.length === 0, 'dpr (profile): no page errors', log.errors);
  await close();
};

tests.planColors = async () => {
  const { page, close } = await openApp({});
  const rgb = h => { const n = parseInt(h.slice(1), 16); return `rgb(${n >> 16}, ${(n >> 8) & 255}, ${n & 255})`; };
  const PC = { A: rgb('#0F766E'), B: rgb('#C2410C'), C: rgb('#BE185D') }, PROF = rgb('#7C3AED'), BLUE = rgb('#2563EB');
  await click(page, '[data-a="tab"][data-x="schedule"]'); await click(page, '[data-a="schedTab"][data-x="plans"]'); await tick(page, 600);
  const seen = {};
  for (const k of ['A', 'B', 'C']) {
    await click(page, `.seg.plans [data-a="pickPlan"][data-x="${k}"]`);
    const on = await page.locator('.seg.plans button.on').evaluate(b => [b.textContent.trim(), getComputedStyle(b).backgroundColor]);
    const blk = await page.locator('.plancol .g-b').first().evaluate(b => getComputedStyle(b).backgroundColor).catch(() => null);
    seen[k] = { on, blk };
    ok(on[0] === 'Plan ' + k && on[1] === PC[k], `plan colours: Plan ${k} tab is its own colour`, on);
  }
  ok(new Set(Object.values(seen).map(x => x.on[1])).size === 3 && !Object.values(seen).some(x => x.on[1] === BLUE || x.blk === BLUE || x.blk === rgb('#D6E4FF')), 'plan colours: three different colours, none of them My Classes blue', seen);
  ok(!Object.values(seen).some(x => x.on[1] === PROF), 'plan colours: no plan is the professor page’s purple', seen);
  ok(seen.B.blk === rgb('#FED7AA') || seen.B.blk === PC.B, 'plan colours: the plan’s blocks are in the plan’s colour (Plan B has classes in the fixture)', seen.B.blk);
  await click(page, '[data-a="schedTab"][data-x="mine"]'); await tick(page, 400);
  const mineBlk = await page.locator('.g-b').first().evaluate(b => getComputedStyle(b).backgroundColor).catch(() => null);
  ok(mineBlk === rgb('#D6E4FF') || mineBlk === BLUE, 'plan colours: My Classes stays blue', mineBlk);
  await click(page, '[data-a="tab"][data-x="explore"]');
  const code = await page.evaluate(() => Object.keys(COURSES).find(c => secsOf(c).length));
  await page.evaluate(c => A.openClass(c), code); await tick(page, 500);
  const add = await page.locator('.addbtn').first().evaluate(b => getComputedStyle(b).backgroundColor);
  ok(add === BLUE, 'plan colours: + on a class page is the regular blue even with Plan C picked', add);
  ok(await page.locator('.planpick').count() === 0, 'plan colours: no plan pills on the class page (the + asks which plan)');
  await close();
};

tests.dpr = async () => {
  const { page, close, log } = await openApp({});
  await click(page, '[data-a="tab"][data-x="schedule"]'); await click(page, '[data-a="schedTab"][data-x="planner"]'); await tick(page, 2500);
  await page.locator('input[data-in="dprfile"]').setInputFiles('files/dpr-fixture.pdf');
  for (let i = 0; i < 20 && !(await page.locator('#sheet .tc-dprrow').count()); i++) await tick(page, 500);
  const sh = await page.locator('#sheet').innerText(), html = await page.locator('#sheet').innerHTML();
  ok(/Past classes · 4/i.test(sh) && /In progress · Fall 2026/i.test(sh) && /Financial Accounting/.test(sh) && !/\(2214\)/.test(sh) && /BUS 2214/.test(sh) && /Business Administration/.test(sh), 'dpr: the report is read on the phone, split into past and this term', sh.slice(0, 400));
  ok(!/9876543/.test(html) && !/\bA-\b|\bB\+|\bC\+/.test(sh), 'dpr: neither the EMPLID nor any grade reaches the screen');
  ok(/PHIL 3331[\s\S]{0,80}already logged/.test(sh) && /BUS 3438[\s\S]{0,80}already in My Classes/.test(sh), 'dpr: classes already logged or already in My Classes are marked, not added twice');
  await click(page, '[data-a="dprSave"]'); await tick(page, 800);
  const hist = log.writes.filter(w => w.table === 'class_history'), saved = log.writes.filter(w => w.table === 'saved_classes');
  const rows = hist[0] && hist[0].body;
  ok(Array.isArray(rows) && rows.length === 3 && rows.every(r => Object.keys(r).sort().join() === 'code,professor,term,user_id,year') && rows.some(r => r.code === 'BUS 2214' && r.term === 'Fall' && r.year === 2024) && rows.some(r => r.code === 'AP 300' && r.professor === '🌍'), 'dpr: past classes upserted as {user_id, code, term, year, professor} — transfer credit marked, no grade', rows);
  ok(saved.length === 1 && JSON.stringify(saved[0].body) === JSON.stringify([{ user_id: FX.ME.id, term: '2268', code: 'BUS 4488' }]), 'dpr: this term’s class goes to My Classes — even when the report also lists next term', saved[0] && saved[0].body);
  ok(!JSON.stringify(hist.map(h => h.body)).includes('BUS 4401') && /BUS 4401[\s\S]{0,120}registered for Spring 2027/.test(sh), 'dpr: next term’s registered class is shown but never filed as finished');
  ok(!JSON.stringify(log.writes).includes('9876543'), 'dpr: the EMPLID is in no write');
  ok(log.errors.length === 0, 'dpr: no page errors', log.errors);
  await close();
};
tests.dprWrong = async () => {
  const { page, close } = await openApp({});
  await click(page, '[data-a="tab"][data-x="schedule"]'); await click(page, '[data-a="schedTab"][data-x="planner"]'); await tick(page, 2500);
  await page.locator('input[data-in="dprfile"]').setInputFiles('files/not-a-dpr.pdf');
  for (let i = 0; i < 20 && !/isn’t a Degree Progress Report/.test(await page.locator('#sheet').innerText()); i++) await tick(page, 500);
  ok(/isn’t a Degree Progress Report/.test(await page.locator('#sheet').innerText()), 'dpr: another PDF is refused with what to do instead');
  await close();
};

tests.friendPlans = async () => {
  const { page, close, log } = await openApp({});
  ok(log.reads.some(r => /^plans\?/.test(r) && /user_id=neq\./.test(r) && /term=eq\.2268/.test(r)), 'friend plans: read with the desktop’s query (term, not me)');
  await click(page, '[data-a="tab"][data-x="friends"]'); await click(page, '[data-a="fFilter"][data-x="people"]');
  await click(page, '.li:has-text("Avery Quill")');
  let t = await text(page);
  ok(/Avery’s plans[\s\S]*Plan A[\s\S]*2 classes[\s\S]*BUS 3438[\s\S]*STAT 2170/.test(t) && !/Plan B/.test(t.slice(t.indexOf('Avery’s plans'))), 'friend plans: a friend’s shared Plan A, and no plan they didn’t share', t.slice(t.indexOf('Avery’s plans'), t.indexOf('Avery’s plans') + 300));
  ok(/You too/.test(t), 'friend plans: classes you’re also in are marked');
  await click(page, '[data-a="back"]'); await click(page, '.li:has-text("Rowan Testa")');
  ok(/No shared plans/.test(await text(page)), 'friend plans: says so, neutrally, when a friend shares none');
  await close();
};

tests.friendPlansLoading = async () => {
  /* Plans that haven't arrived yet must not read as "no shared plans". */
  const { page, close } = await openApp({ hook: (url, m) => url.pathname.endsWith('/plans') && /neq/.test(url.search) ? { status: 500, body: '{}' } : null });
  await click(page, '[data-a="tab"][data-x="friends"]'); await click(page, '[data-a="fFilter"][data-x="people"]'); await click(page, '.li:has-text("Rowan Testa")');
  ok(!/No shared plans/.test(await text(page)), 'friend plans: a failed or pending load says nothing, not “none”');
  await close();
};

tests.seatsPartial = async () => {
  /* A term bigger than one page, where page two fails: nothing is shown rather than half a term. */
  const extra = Array.from({ length: 1000 }, (_, i) => ({ term: '2268', course_code: 'ZZZ ' + (1000 + i), title: 'Synthetic ' + i, section: '01', instructor: 'Staff', days: 'TBA', status: 'Open', capacity: 10, enrolled: 1, available: 9, waitlist_total: 0, waitlist_capacity: 0, class_nbr: String(80000 + i), instruction_mode: 'In Person', location: '' }));
  const T = Object.assign({}, FX.TABLES, { course_seats: FX.TABLES.course_seats.concat(extra) });
  const { page, close, log } = await openApp({ tables: T, hook: url => url.pathname.endsWith('/course_seats') && /offset=1000/.test(url.search) ? { status: 500, body: '{}' } : null });
  await click(page, '[data-a="tab"][data-x="explore"]');
  const t = await text(page);
  ok(/Couldn’t load Fall 2026 classes/.test(t) && await page.locator('#exlist .ccard').count() === 0, 'seats: a partial term is never shown', t.slice(0, 200));
  await close();
};

tests.noPoly = async () => {
  const { page, close, log } = await openApp({ poly: null });
  await click(page, '[data-a="tab"][data-x="explore"]');
  await click(page, '#exlist [data-x="BUS 3431"]');
  const t = await text(page);
  ok(!/★\s*\d|\d\.\d/.test(t.replace(/\d{1,2}:\d{2}/g, '')), 'no PolyRatings: no ratings shown anywhere on the class', t);
  ok(log.errors.length === 0, 'noPoly: no page errors', log.errors);
  await close();
};

tests.noProfile = async () => {
  const T = Object.assign({}, FX.TABLES, { profiles: FX.TABLES.profiles.filter(p => p.id !== FX.ME.id) });
  const { page, close } = await openApp({ tables: T });
  const t = await text(page);
  for (let i = 0; i < 10 && !/claim your username/.test(await text(page)); i++) await tick(page, 500);
  const t2 = await text(page);
  ok(/claim your username/.test(t2) && !/Finish setting up/.test(t2) && await page.locator('.tabbar').count() === 0, 'no profile: set up right here, not sent to termchamp.com', t2.slice(0, 200));
  await close();
};

/* The live database grants `authenticated` SELECT on named profile columns only; the harness
   now refuses anything else with 42501, as PostgREST does. Tate's own sign-in on 2026-09-29 hit
   this: the build asked for `concentration`, the read failed, and the app said his account
   "hasn't been set up yet". */
tests.profileGrants = async () => {
  let { page, close, log } = await openApp();
  const own = log.reads.filter(r => r.startsWith('profiles?') && r.includes(FX.ME.id));
  ok(own.length >= 1 && own.every(r => !/concentration|select=\*/.test(decodeURIComponent(r))), 'profile: own read names only granted columns', own);
  ok(await page.locator('.tabbar').count() === 1 && !/Finish setting up/.test(await text(page)), 'profile: a set-up account loads the app');
  await close();

  ({ page, close } = await openApp({ hook: (url, m) => m === 'GET' && url.pathname.endsWith('/profiles') && url.search.includes(FX.ME.id) ? { status: 403, body: JSON.stringify({ code: '42501', message: 'permission denied for table profiles' }) } : null }));
  let t = await text(page);
  ok(/Couldn’t load your profile/.test(t) && /42501/.test(t) && !/Finish setting up|hasn’t been set up/.test(t), 'profile: a failed read says so — never “finish setting up”', t.slice(0, 200));
  await close();

  const desk = conc => `localStorage.setItem('professify-profile', JSON.stringify({ school: 'calpoly', major: ${JSON.stringify(FX.ME.major)}, conc: ${JSON.stringify(conc)} }))`;
  ({ page, close } = await openApp({ init: desk('Financial Management') }));
  await click(page, '[data-a="tab"][data-x="schedule"]'); await click(page, '[data-a="schedTab"][data-x="planner"]'); await tick(page, 2500);
  t = await text(page);
  ok(/Financial Management/.test(t) && !/Pick your concentration/.test(t), 'profile: the concentration picked on the desktop carries over (same origin, same major)', t.slice(0, 300));
  await close();

  ({ page, close } = await openApp({ init: `localStorage.setItem('professify-profile', JSON.stringify({ major: 'Plant Sciences', conc: 'Financial Management' }))` }));
  await click(page, '[data-a="tab"][data-x="schedule"]'); await click(page, '[data-a="schedTab"][data-x="planner"]'); await tick(page, 2500);
  ok(/Pick your concentration/.test(await text(page)), 'profile: a desktop memory for another major is ignored');
  await click(page, '[data-a="pickConc"][data-x="Financial Management"]'); await tick(page, 800);
  const mem = await page.evaluate(() => localStorage.getItem('termchamp_app_conc'));
  ok(mem && JSON.parse(mem).conc === 'Financial Management' && JSON.parse(mem).u === FX.ME.id && JSON.parse(mem).major === FX.ME.major, 'profile: picking a concentration is remembered on this device, per account', mem);
  await close();
  ({ page, close } = await openApp({ init: `localStorage.setItem('termchamp_app_conc', JSON.stringify({ u: ${JSON.stringify(FX.ME.id)}, major: ${JSON.stringify(FX.ME.major)}, conc: 'Financial Management' }))` }));
  await click(page, '[data-a="tab"][data-x="schedule"]'); await click(page, '[data-a="schedTab"][data-x="planner"]'); await tick(page, 2500);
  ok(!/Pick your concentration/.test(await text(page)), 'profile: the phone’s own memory is read back on the next visit');
  await close();
  ({ page, close } = await openApp({ init: `localStorage.setItem('termchamp_app_conc', JSON.stringify({ u: 'someone-else', major: ${JSON.stringify(FX.ME.major)}, conc: 'Financial Management' }))` }));
  await click(page, '[data-a="tab"][data-x="schedule"]'); await click(page, '[data-a="schedTab"][data-x="planner"]'); await tick(page, 2500);
  ok(/Pick your concentration/.test(await text(page)), 'profile: another account’s memory on this device is not used');
  await close();
};

tests.signup = async () => {
  const T = Object.assign({}, FX.TABLES, { profiles: FX.TABLES.profiles.filter(p => p.id !== FX.ME.id) });
  const { page, close, log } = await openApp({ signedIn: false, tables: T, rpc: Object.assign({}, FX.RPC, { username_taken: false }) });
  await click(page, '[data-a="siMode"][data-x="signup"]');
  const otp = () => log.writes.filter(w => /^auth:otp/.test(w.table));
  const go = () => page.locator('#su-go').isDisabled();
  let t = await text(page);
  ok(/Sign up with your school email/.test(t) && !/born|birth|13 or older/i.test(t) && await page.locator('#su-year').count() === 0, 'signup: Sean’s screen, and no age question (Tate: the school email and year in school are enough)', t.slice(0, 300));
  await page.locator('#su-email').fill('jordan@gmail.com'); await page.locator('#su-pw').fill('longenough1'); await page.locator('#su-agree').check();
  ok(await go() && /ends in \.edu/.test(await page.locator('#su-emailhint').innerText()), 'signup: a non-school address can’t be sent — and the hint says why');
  await page.locator('#su-email').fill(FX.ME.email);
  ok(/Student email recognized · Cal Poly/.test(await page.locator('#su-emailhint').innerText()) && !(await go()), 'signup: a Cal Poly email is recognised and the button wakes up');
  await page.locator('#su-pw').fill('short1');
  ok(await go() && !(await page.locator('#su-r1').evaluate(e => e.classList.contains('ok'))), 'signup: under 8 characters, the rule stays unticked and the button stays off');
  await page.locator('#su-pw').fill('longenough1');
  ok(await page.locator('#su-r1').evaluate(e => e.classList.contains('ok')), 'signup: 8+ ticks the rule');
  await page.locator('#su-agree').uncheck(); ok(await go(), 'signup: the Terms must be agreed to'); await page.locator('#su-agree').check();
  await click(page, '[data-a="suEye"]');
  ok(await page.locator('#su-pw').getAttribute('type') === 'text' && await page.locator('#su-pw').inputValue() === 'longenough1', 'signup: Show reveals the password without clearing it');
  ok(!otp().length, 'signup: nothing sent yet');
  await page.locator('#su-go').click(); await settle(page, 600);
  const o = otp();
  ok(o.length === 1 && o[0].body.email === FX.ME.email && o[0].body.create_user === true && !JSON.stringify(o[0].body).includes('longenough1'), 'signup: one code is requested, creating the account; the password isn’t sent with it', o.map(x => x.body));
  t = await text(page);
  ok(/Check your email/.test(t) && t.includes('jo***@calpoly.edu') && await page.locator('.code6 input').count() === 6 && /Resend in 0:\d\d/.test(t), 'signup: six code boxes, the masked address and a resend countdown', t.slice(0, 300));
  await click(page, '#resend'); ok(otp().length === 1, 'signup: no resend during the countdown');
  await click(page, '[data-a="onbBack"]');
  ok(/Sign up with your school email/.test(await text(page)) && await page.locator('#su-pw').inputValue() === 'longenough1', 'signup: Back to the form keeps what you typed');
  await page.locator('#su-go').click(); await settle(page, 600);
  ok(otp().length === 1 && /already sent/.test(await text(page)), 'signup: sending again for the same address goes back to the code — no second request to be refused');
  ok(await page.evaluate(() => document.activeElement && document.activeElement.closest('.code6') !== null), 'signup: the first code box is focused, so iOS offers the emailed code');
  await page.locator('.code6 input').first().fill('123456');   // how iOS autofill lands: the whole code in box one
  await settle(page, 1500); await tick(page, 1500);
  const ver = log.writes.filter(w => /^auth:verify/.test(w.table)), pw = log.writes.filter(w => w.table === 'auth:user' && w.m === 'PUT');
  ok(ver.length === 1 && ver[0].body.token === '123456' && pw.length === 1 && pw[0].body.password === 'longenough1', 'signup: six digits verify on their own, then the password is set on that session', [ver.map(x => x.body), pw.length]);
  for (let i = 0; i < 10 && !/claim your username/.test(await text(page)); i++) await tick(page, 500);
  t = await text(page);
  ok(/Next, claim your username/.test(t) && await page.locator('#ob-go').isDisabled(), 'onboard: “claim your username”, Continue off until it’s filled', t.slice(0, 200));
  await page.locator('#ob-first').fill('Jordan'); await page.locator('#ob-last').fill('Fixture'); await tick(page, 700);
  ok(await page.locator('#ob-user').inputValue() === 'jordanfixture' && /available/.test(await page.locator('#ob-usermsg').innerText()) && !(await page.locator('#ob-go').isDisabled()), 'onboard: the username is suggested from the name, checked, and Continue wakes up');
  await page.locator('#ob-user').fill(''); await tick(page, 300);
  ok(await page.locator('#ob-go').isDisabled(), 'onboard: username is required (Tate)');
  await page.locator('#ob-user').fill('new_fixture'); await tick(page, 700);
  await page.locator('#ob-go').click(); await settle(page, 800); await tick(page, 1500);
  const ins = log.writes.filter(w => w.table === 'profiles' && w.m === 'POST'), b = ins[0] && ins[0].body;
  ok(ins.length === 1 && b.id === FX.ME.id && b.edu_email === FX.ME.email && b.display_name === 'Jordan Fixture' && b.username === 'new_fixture' && !('school' in b), 'onboard: the profile row — name and username, no school (the server stamps it)', b);
  for (let i = 0; i < 10 && !/Add this term’s schedule/.test(await text(page)); i++) await tick(page, 500);
  t = await text(page);
  ok(/Add this term’s schedule/.test(t) && await page.locator('.tabbar').count() === 0, 'onboard: then this term’s classes (step 1 of 2)', t.slice(0, 200));
  await click(page, '[data-a="onbStep"][data-x="manual"]');
  const qEl = await page.locator('#onb-q').elementHandle();
  await page.locator('#onb-q').fill('ECON'); await tick(page, 400);
  ok(await qEl.evaluate(e => e.isConnected && document.activeElement === e), 'manual: the search box isn’t rebuilt while you type (the keyboard stays up)');
  await click(page, '.rrow[data-x="ECON 2303"]');
  const secBtn = page.locator('.secbtn[data-y]').first(), secId = await secBtn.getAttribute('data-y');
  await secBtn.click(); await settle(page, 800);
  const sc = log.writes.filter(w => w.table === 'saved_classes' && w.m === 'POST').pop(), ms = log.writes.filter(w => w.table === 'my_sections' && w.m === 'POST').pop();
  ok(sc && sc.body.code === 'ECON 2303' && sc.body.term === '2268' && sc.body.user_id === FX.ME.id && ms && ms.body.class_nbr === secId && ms.body.status === 'enrolled', 'manual: taking now saves the class and its section, as the desktop does', [sc && sc.body, ms && ms.body]);
  await click(page, '[data-a="onbTab"][data-x="took"]');
  await page.locator('#onb-q').fill('ECON 2303'); await tick(page, 400);
  await click(page, '.rrow[data-x="ECON 2303"]');
  await click(page, '[data-a="onbTook"][data-y="Spring 2026"]'); await tick(page, 600);
  const h = log.writes.filter(w => w.table === 'class_history').pop();
  ok(h && h.body.code === 'ECON 2303' && h.body.term === 'Spring' && h.body.year === 2026 && !('grade' in h.body), 'manual: took before asks when, and logs code + term + year — no grade', h && h.body);
  await click(page, '[data-a="onbStep"][data-x="confirm"]'); await tick(page, 1500);
  t = await text(page);
  ok(/Does this look right\?/.test(t) && /Year\s*Pick one/.test(t) && /Major\s*Pick one/.test(t) && !/Graduating/.test(t) && await page.locator('[data-a="onbConfirmDone"]').isDisabled(), 'confirm: year and major needed, no “Graduating”', t.slice(0, 300));
  await click(page, '[data-a="onbPick"][data-x="major"]'); await click(page, '[data-a="onbSet"][data-y="Business Administration"]');
  ok(await page.locator('[data-a="onbConfirmDone"]').isDisabled(), 'confirm: a major alone isn’t enough — the year is needed too');
  await click(page, '[data-a="onbPick"][data-x="standing"]'); await click(page, '[data-a="onbSet"][data-y="Junior"]');
  await click(page, '[data-a="onbConfirmDone"]'); await tick(page, 800);
  const up = log.writes.filter(w => w.table === 'profiles' && w.m === 'PATCH').pop();
  ok(up && up.body.class_standing === 'Junior' && up.body.major === 'Business Administration' && /id=eq\./.test(up.query), 'confirm: saves year and major to your profile', up && up.body);
  t = await text(page);
  ok(/People you may know/.test(t) && /Invite a friend/.test(t), 'onboard: people you may know');
  await page.reload(); await tick(page, 2500); await tick(page, 1500);
  ok(/People you may know/.test(await text(page)), 'onboard: closing the app mid-way comes back to the same step');
  noProto(t, 'onboarding');
  await click(page, '[data-a="onbStep"][data-x="payoff"]');
  t = await text(page);
  ok(/You’re in, Jordan!/.test(t) && /Start planning!/.test(t) && !/Stay up to date/.test(t), 'onboard: the payoff — and no notifications step while push isn’t live', t.slice(0, 200));
  await click(page, '[data-a="onbFinish"][data-x="home"]');
  ok(await page.locator('.tabbar').count() === 1, 'onboard: Start planning lands in the app');
  ok(log.errors.length === 0, 'signup: no page errors', log.errors);
  await close();
};

tests.onbFriendsOnly = async () => {
  const { page, close, log } = await openApp({});
  await page.evaluate(() => { S.stack.home.push({ s: 'onb', p: { step: 'payoff' } }); render(); });
  await tick(page, 600);
  const t = await text(page), friendNames = await page.evaluate(() => TC.friends.map(id => PEOPLE[id].name)), everyone = await page.evaluate(() => Object.keys(PEOPLE).filter(id => id !== 'me' && !TC.friends.includes(id)).map(id => PEOPLE[id].name));
  const shown = await page.locator('.onb .li .t, .onb .hcard b').allInnerTexts();
  ok(shown.length > 0 && shown.every(n => friendNames.includes(n)) && !everyone.some(n => shown.includes(n)), 'payoff: only friends are named — never a stranger (Tate)', { shown, friendNames });
  const exp = await page.evaluate(() => { const o = {}; onbMine().forEach(c => { const n = ((TC.tookCode || {})[c] || []).filter(id => TC.friends.includes(id)).length; if (n) o[c] = n; }); return o; });
  const cards = await page.locator('.onb .hcard').evaluateAll(els => els.map(e => [e.querySelector('.codechip').textContent.trim(), (e.textContent.match(/and (\d+) other/) || [0, 0])[1] * 1 + 1]));
  ok(cards.length === Object.keys(exp).length && cards.every(([c, n]) => exp[c] === n), 'payoff: each class counts only the friends who took it', { cards, exp });
  ok(/Friends who took your classes/i.test(t) && (!/in your classes/i.test(t) || /Friends in your classes/i.test(t)), 'payoff: says “friends”, because that’s all it shows');
  ok(!log.reads.some(r => /class_history\?.*user_id=in/.test(r) && !r.includes(FX.FRIENDS[0].id)), 'payoff: no extra reads of anyone’s history');
  await close();
};

tests.loginNoAccount = async () => {
  const sent = [];
  const { page, close } = await openApp({ signedIn: false, hook: (url, m, body) => { if (!url.pathname.endsWith('/auth/v1/otp')) return null; sent.push(body); return { status: 422, body: JSON.stringify({ code: 422, error_code: 'otp_disabled', msg: 'Signups not allowed for otp' }) }; } });
  await click(page, '[data-a="siMode"][data-x="password"]'); await click(page, '[data-a="siMode"][data-x="code"]');
  await page.locator('#si-email').fill(FX.ME.email); await page.locator('form[data-submit="sendCode"] .btn').click(); await settle(page, 600);
  const t = await text(page);
  ok(/No TermChamp account uses that email yet/.test(t) && /Create an account/.test(t), 'log in: an address with no account is told so and offered sign-up — not made into an empty account', t.slice(0, 300));
  ok(sent.length === 1 && sent[0].create_user === false, 'log in: a code to log in never creates an account', sent);
  await close();
};

tests.ga = async () => {
  const { page, close } = await openApp({});
  const r = await page.evaluate(() => {
    const L = (host, protocol = 'https:') => ({ host, protocol });
    return {
      prod: gaAllowedFor(L('termchamp.com'), {}, CFG),
      preview: gaAllowedFor(L('deploy-preview-62--termchamp.netlify.app'), {}, CFG),
      local: gaAllowedFor(L('localhost:8642', 'http:'), {}, CFG),
      http: gaAllowedFor(L('termchamp.com', 'http:'), {}, CFG),
      gpc: gaAllowedFor(L('termchamp.com'), { globalPrivacyControl: true }, CFG),
      dnt: gaAllowedFor(L('termchamp.com'), { doNotTrack: '1' }, CFG),
      blank: gaAllowedFor(L('termchamp.com'), {}, Object.assign({}, CFG, { GA_MEASUREMENT_ID: '' })),
      loaded: !!document.querySelector('script[src*="googletagmanager"]') || !!window.dataLayer,
      cls: gaPage('classDetail'), odd: gaPage('BUS 2201')
    };
  });
  ok(r.prod === 'G-L98ZTJQ1LY' && !r.preview && !r.local && !r.http && !r.gpc && !r.dnt && !r.blank, 'ga: only on https://termchamp.com, and never under GPC or Do Not Track', r);
  ok(!r.loaded, 'ga: nothing loads on localhost (so previews and tests never count)');
  ok(r.cls.page_location.endsWith('/app/?tab=classDetail') && r.odd.page_location.endsWith('/app/?tab=app') && r.odd.page_title === 'TermChamp app — App', 'ga: a page is a screen name, and anything unknown is “app”', [r.cls, r.odd]);
  await page.evaluate(() => { window.__ga = []; window.gtag = (...a) => window.__ga.push(a); _gaOn = true; _gaLast = ''; });
  await click(page, '[data-a="tab"][data-x="explore"]');
  const code = await page.evaluate(() => Object.keys(COURSES).find(c => secsOf(c).length));
  await page.evaluate(c => A.openClass(c), code); await settle(page);
  await click(page, '[data-a="tab"][data-x="friends"]');
  const sent = await page.evaluate(() => window.__ga);
  const views = sent.filter(a => a[0] === 'event' && a[1] === 'page_view').map(a => a[2].page_location);
  ok(views.some(v => v.endsWith('?tab=explore')) && views.some(v => v.endsWith('?tab=classDetail')) && views.some(v => v.endsWith('?tab=friends')), 'ga: tabs and screens are counted', views);
  ok(!JSON.stringify(sent).includes(code) && !/[0-9a-f]{8}-[0-9a-f]{4}-/.test(JSON.stringify(sent)), 'ga: no class code or account id ever reaches Google', sent);
  await close();
};

tests.waitlist = async () => {
  let { page, close, log } = await openApp({ signedIn: false });
  await click(page, '[data-a="siMode"][data-x="signup"]');
  await page.locator('#su-email').fill('Aztec.Fixture@SDSU.edu'); await page.locator('#su-pw').fill('whatever12'); await page.locator('#su-agree').check();
  ok(/SDSU is coming soon/.test(await page.locator('#su-emailhint').innerText()), 'waitlist: the hint says SDSU is coming as you type');
  await page.locator('#su-go').click(); await settle(page, 500);
  let t = await text(page);
  ok(/TermChamp is coming to SDSU/.test(t) && /Join the list/.test(t) && !log.writes.some(w => /^auth:/.test(w.table)), 'waitlist: an SDSU email gets the waitlist, and no account or code', t.slice(0, 250));
  await click(page, '[data-a="joinWaitlist"]'); await tick(page, 500);
  const w = log.writes.filter(x => x.table === 'school_waitlist');
  ok(w.length === 1 && w[0].m === 'POST' && JSON.stringify(w[0].body) === JSON.stringify({ email: 'aztec.fixture@sdsu.edu', school: 'sdsu' }), 'waitlist: joining stores only the lower-cased address and the school', w.map(x => x.body));
  ok(!/select=/.test(w[0].query || ''), 'waitlist: the app never asks to read the list back');
  ok(/You’re on the list!/.test(await text(page)) && /aztec\.fixture@sdsu\.edu|Aztec\.Fixture@SDSU\.edu/i.test(await text(page)), 'waitlist: says you’re on it, and which address');
  await close();

  ({ page, close, log } = await openApp({ signedIn: false, hook: (url, m) => url.pathname.endsWith('/school_waitlist') && m === 'POST' ? { status: 409, body: JSON.stringify({ code: '23505', message: 'duplicate key value violates unique constraint "school_waitlist_pkey"' }) } : null }));
  await click(page, '[data-a="siMode"][data-x="password"]');
  await page.locator('#si-email').fill('gaucho@ucsb.edu'); await page.locator('#si-pw').fill('whatever1');
  await page.locator('form[data-submit="pw"] .btn').click(); await settle(page, 500);
  ok(/coming to UCSB/.test(await text(page)) && !log.writes.some(x => /^auth:/.test(x.table)), 'waitlist: logging in with a UCSB email goes to the waitlist, and the password is never sent');
  await click(page, '[data-a="joinWaitlist"]'); await tick(page, 500);
  ok(/already on the list/.test(await text(page)), 'waitlist: joining twice says you’re already on it');
  await close();

  ({ page, close, log } = await openApp({ signedIn: false, hook: (url, m) => url.pathname.endsWith('/school_waitlist') ? { status: 404, body: JSON.stringify({ code: '42P01', message: 'relation "public.school_waitlist" does not exist' }) } : null }));
  await click(page, '[data-a="siMode"][data-x="password"]'); await click(page, '[data-a="siMode"][data-x="code"]');
  await page.locator('#si-email').fill('aztec@sdsu.edu'); await page.locator('form[data-submit="sendCode"] .btn').click(); await settle(page, 500);
  await click(page, '[data-a="joinWaitlist"]'); await tick(page, 500);
  t = await text(page);
  ok(/isn’t open yet/.test(t) && !/on the list/.test(t), 'waitlist: before the SQL is run it says so — never “you’re on the list”', t.slice(0, 300));
  await close();
};

tests.otherSchoolSession = async () => {
  const { page, close, log } = await openApp({ hook: (url, m) => url.pathname.startsWith('/auth/v1/user') && m === 'GET' ? { status: 200, body: JSON.stringify({ id: FX.ME.id, aud: 'authenticated', role: 'authenticated', email: 'aztec@sdsu.edu' }) } : null, init: `(() => { const k = 'sb-rqkndeqbcahozidniesn-auth-token'; try { const s = JSON.parse(localStorage.getItem(k)); s.user.email = 'aztec@sdsu.edu'; localStorage.setItem(k, JSON.stringify(s)); } catch (e) {} })()` });
  const t = await text(page);
  ok(/TermChamp is coming to SDSU/.test(t) && /still works on/.test(t) && await page.locator('.tabbar').count() === 0, 'waitlist: a signed-in SDSU account gets the waitlist, not Cal Poly’s app', t.slice(0, 250));
  ok(!log.reads.some(r => /^(profiles|my_sections|saved_classes|friend_requests|plans)\b/.test(r)), 'waitlist: none of the account’s data is loaded', log.reads.filter(r => !/course_|rpc:/.test(r)));
  await close();
};

tests.desktopWidth = async () => {
  const { page, close, log } = await openApp({ width: 1280, height: 900 });
  ok(await page.locator('.side').isVisible() && /termchamp\.com\/app/.test(await page.locator('.side').innerText()), 'desktop: side panel says to open it on a phone');
  ok(/^\d{1,2}:\d{2}$/.test((await page.locator('#status > span:first-child').innerText()).trim()) && (await page.locator('#status > span:first-child').innerText()).trim() !== '9:41', 'desktop: frame status bar shows the real time', await page.locator('#status > span:first-child').innerText());
  ok(log.errors.length === 0, 'desktop: no page errors', log.errors);
  await close();
};

const names = Object.keys(tests).filter(n => !only || n === only);
for (const n of names) {
  if (!quiet) console.log('#', n);
  try { await tests[n](); } catch (e) { fail++; fails.push(n + ' threw'); console.log('  FAIL', n, 'threw', e.message.split('\n')[0]); }
}
console.log(`\ncheck-app: ${pass} passed, ${fail} failed`);
if (fail) { console.log('failed:', fails.join(' | ')); process.exit(1); }
