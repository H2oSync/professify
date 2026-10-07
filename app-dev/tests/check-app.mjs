/* check-app — the phone app (app/index.html) against synthetic fixtures, asserting on the RENDERED
   DOM and on the exact rows it writes. Run: node check-app.mjs [--only name] [--quiet]
   Exit code 1 on any failure. mutate.mjs runs this against deliberately broken copies. */
import { openApp } from './app-harness.mjs';
import * as FX from './app-fixtures.mjs';
import nodeFs from 'node:fs'; import nodePath from 'node:path'; import nodeVm from 'node:vm';

const only = process.argv.includes('--only') ? process.argv[process.argv.indexOf('--only') + 1] : null;
const quiet = process.argv.includes('--quiet');
let pass = 0, fail = 0; const fails = [];
function ok(cond, name, info) { if (cond) { pass++; if (!quiet) console.log('  ok  ', name); } else { fail++; fails.push(name); console.log('  FAIL', name, info !== undefined ? '→ ' + JSON.stringify(info).slice(0, 300) : ''); } }
const text = p => p.locator('#scroll').innerText();
const settle = async (p, ms = 400) => { await p.clock.runFor(ms); await p.waitForTimeout(250); await p.clock.runFor(50); await p.waitForTimeout(100); };
const click = async (p, sel) => { await p.locator(sel).first().click(); await settle(p); };
/* The class page's + opens "Add to a plan"; this taps + (nth), optionally picks a plan, then Add/Remove. */
const addVia = async (p, nth = 0, k = null) => { await click(p, `.secrow .addbtn >> nth=${nth}`); if (k) { if (await p.locator('#sheet [data-a="atGroup"][data-x="plans"][aria-pressed="false"]').count()) await click(p, '#sheet [data-a="atGroup"][data-x="plans"]'); await click(p, `#sheet [data-a="atPick"][data-x="${k}"]`); } if (await p.locator('#sheet [data-a="atGo"]').count()) { await click(p, '#sheet [data-a="atGo"]'); await settle(p, 700); await settle(p, 1100); } else if (await p.locator('#sheet [data-a="atRemove"]').count()) { await click(p, '#sheet [data-a="atRemove"]'); await settle(p, 600); } };
const atGo = async p => { await click(p, '#sheet [data-a="atGo"]'); await settle(p, 700); await settle(p, 1100); };
const tick = (p, ms = 400) => settle(p, ms);
/* Your reviews live on My ratings since 2026-10-06 (profile → My ratings). */
const openRatings = async p => { await click(p, '.homehdr .me-btn'); await tick(p, 600); await click(p, '[data-a="openMyRatings"]'); await tick(p, 600); };
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
  ok(/Anytime\s*UNIV\s+1101$/i.test(f1.trim()) && !/No times yet|No section/.test(f1), 'home: Rowan’s class saved without a section sits in the Anytime tray under his week, code only', f1);
  ok(/You might know[\s\S]*Pat Suggestia[\s\S]*Taking one of your classes/.test(t), 'home: suggestion with the server’s own reason');
  ok(/Classes your friends are taking\s*Suggested/i.test(t) && !/Where your friends are/.test(t), 'home: friends’ classes are a suggested row in the feed; the “Where your friends are” card is gone (2026-10-04)');
  const id4 = FX.FRIENDS[3].id;
  await page.evaluate(() => { document.getElementById('scroll').scrollTop = 0; });
  await click(page, `.story[data-x="${id4}"]`); await tick(page, 900);
  const dy = await page.evaluate(() => ({ st: document.getElementById('scroll').scrollTop, sheet: UI.sheet && UI.sheet.type, id: UI.sheet && UI.sheet.id }));
  ok(dy.st === 0 && dy.sheet === 'story' && dy.id === id4, 'home: tapping a story opens that friend’s day, not a jump down the feed (Tate, 2026-09-30)', dy);
  await click(page, '#sheet .xbtn');
  ok(log.errors.length === 0, 'home: no page errors', log.errors);
  await close();
};

/* Home width (Tate, 2026-09-30, from the Home Card Width mockup): Home sits 12px from the screen edge
   and a friend's week 8px inside its card, with a 26px hour column and 5px day gaps. Schedule's My Classes
   and Plans match it since 2026-10-04; the Planner tab is unchanged. */
tests.homeWidth = async () => {
  const { page, close, log } = await openApp({ width: 390 });
  await page.waitForFunction(() => TC.ready && document.querySelectorAll('.hfeed .fcard').length === 5, null, { timeout: 8000 });
  const m = await page.evaluate(() => {
    const sc = document.getElementById('scroll').getBoundingClientRect(), L = el => Math.round(el.getBoundingClientRect().left - sc.left), R = el => Math.round(sc.right - el.getBoundingClientRect().right);
    const card = document.getElementById('hf-' + TC.friends[0]), body = card.querySelector('.g-body'), lab = body.querySelector('.g-lab'), cols = [...body.querySelectorAll('.g-col')];
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
  const cid = await page.evaluate(() => 'hf-' + TC.friends[0]);   /* the feed order is random (2026-10-04); the first friend has a week and plans */
  await click(page, `#${cid} .g-day[data-x="M"]`);
  const foc = await page.evaluate(id => getComputedStyle(document.querySelector('#' + id + ' .g-body')).gridTemplateColumns.split(' ')[0], cid);
  ok(foc === '26px', 'width: a tapped day on a Home card keeps the 26px hour column', foc);
  await click(page, `#${cid} .top`);
  const fp = await page.evaluate(() => [...document.querySelectorAll('#scroll .grid')].map(g => [getComputedStyle(g).paddingLeft, getComputedStyle(g.querySelector('.g-body')).gridTemplateColumns.split(' ')[0]]));
  await click(page, '.fsw button[data-y="A"]');
  fp.push(...await page.evaluate(() => [...document.querySelectorAll('#scroll .grid')].map(g => [getComputedStyle(g).paddingLeft, getComputedStyle(g.querySelector('.g-body')).gridTemplateColumns.split(' ')[0]])));
  ok(fp.length === 2 && fp.every(([p, c]) => p === '8px' && c === '26px'), 'width: the friend page’s week and plan grid use Home’s 8px inset and 26px hour column', fp);
  const fwOne = () => page.evaluate(() => { const sc = document.getElementById('scroll').getBoundingClientRect();
    return [...document.querySelectorAll('#scroll .grid')].map(g => { const c = g.closest('.card'), b = g.querySelector('.g-body'), cols = [...b.querySelectorAll('.g-col')];
      return [Math.round(c.getBoundingClientRect().left - sc.left), Math.round(sc.right - c.getBoundingClientRect().right), Math.round(b.getBoundingClientRect().left - c.getBoundingClientRect().left), Math.round(c.getBoundingClientRect().right - b.getBoundingClientRect().right), Math.round(cols[1].getBoundingClientRect().left - cols[0].getBoundingClientRect().right), Math.round(cols[0].getBoundingClientRect().width * 10) / 10]; })
      .concat([[...document.querySelectorAll('#scroll .card.list')].map(c => [Math.round(c.getBoundingClientRect().left - sc.left), Math.round(sc.right - c.getBoundingClientRect().right)])]); });
  const fwA = await fwOne(); await click(page, '.fsw button[data-y="now"]'); const fwN = await fwOne();
  const fw = [fwN[0], fwA[0], fwN[1]];
  ok(fw.slice(0, 2).every(([l, r, gl, gr, gap, col]) => l === 12 && r === 12 && gl === 8 && gr === 8 && gap === 5 && col === Math.round(m.col * 10) / 10), 'width: on the friend page the week and the plan grid are 12px from the screen, 8px inside the card, 5px gaps — the same day width as Home', { fw, home: m.col });
  ok(fw[2].length > 0 && fw[2].every(([l, r]) => l === 12 && r === 12), 'width: the friend page’s class list shares the 12px edge', fw[2]);
  await click(page, '[data-a="tab"][data-x="schedule"]');
  /* Schedule's My Classes and Plans at Home's widths (Tate, 2026-10-04) */
  const schW = () => page.evaluate(() => { const sc = document.getElementById('scroll').getBoundingClientRect(), L = el => Math.round(el.getBoundingClientRect().left - sc.left), R = el => Math.round(sc.right - el.getBoundingClientRect().right);
    const g = document.querySelector('#scroll .grid'), c = g && g.closest('.card'), b = g && g.querySelector('.g-body'), cols = b ? [...b.querySelectorAll('.g-col')] : [];
    const share = document.querySelector('#scroll .schhdr .schshare');
    return { card: c ? [L(c), R(c)] : null, gridL: c ? Math.round(b.getBoundingClientRect().left - c.getBoundingClientRect().left) : null, gridR: c ? Math.round(c.getBoundingClientRect().right - b.getBoundingClientRect().right) : null,
      lab: b ? getComputedStyle(b).gridTemplateColumns.split(' ')[0] : null, gap: cols.length > 1 ? Math.round(cols[1].getBoundingClientRect().left - cols[0].getBoundingClientRect().right) : null, col: cols.length ? Math.round(cols[0].getBoundingClientRect().width * 10) / 10 : null,
      others: [...document.querySelectorAll('#scroll .ccard, #scroll .agenda, #scroll .anytime, #scroll .seg.plans')].map(e => [L(e), R(e)]), share: share ? R(share) : null }; });
  const mine = await schW();
  ok(mine.card && mine.card[0] === 12 && mine.card[1] === 12 && mine.gridL === 8 && mine.gridR === 8 && mine.lab === '26px' && mine.gap === 5 && mine.col === Math.round(m.col * 10) / 10, 'width: My Classes’ week is 12px from the screen, 8px inside its card, 26px hours, 5px gaps — the same day width as Home', { mine, home: m.col });
  ok(mine.others.length > 0 && mine.others.every(([l, r]) => l === 12 && r === 12) && mine.share === 16, 'width: My Classes’ class cards share the 12px edge; Share sits top right, 16px in like the title', mine);
  await click(page, '[data-a="schedTab"][data-x="plans"]');
  await page.evaluate(() => { const ids = personSecs('me').map(s => s.id); TC.plans.A = ids.slice(); S.plan = 'A'; render(true); }); await settle(page, 300);
  const pl = await schW();
  ok(pl.card && pl.card[0] === 12 && pl.card[1] === 12 && pl.gridL === 8 && pl.gridR === 8 && pl.lab === '26px' && pl.gap === 5 && pl.col === mine.col, 'width: a plan’s week matches My Classes and Home', pl);
  ok(pl.others.length > 1 && pl.others.every(([l, r]) => l === 12 && r === 12), 'width: the plan switch and the day cards under a plan share the 12px edge', pl.others);
  ok(pl.share === 16, 'width: a plan’s Share sits top right, 16px in like the title', pl.share);
  /* a tapped day keeps the 26px hour column on both tabs */
  const tapLab = async () => { await click(page, '#scroll .g-day[data-x="M"]'); const v = await page.evaluate(() => getComputedStyle(document.querySelector('#scroll .g-body')).gridTemplateColumns.split(' ')[0]); await click(page, '#scroll .g-day[data-x="M"]'); return v; };
  const plTap = await tapLab();
  /* a section with no set time sits in its own card on the same edge */
  await page.evaluate(() => { const any = Object.values(SEC).find(s => s.async || s.s == null); if (any) TC.plans.A = TC.plans.A.concat([any.id]); else { const s0 = SEC[TC.plans.A[0]]; SEC['zz-any'] = Object.assign({}, s0, { id: 'zz-any', s: null, e: null, days: [] }); TC.plans.A = TC.plans.A.concat(['zz-any']); } render(true); }); await settle(page, 300);
  const anyW = await page.evaluate(() => { const sc = document.getElementById('scroll').getBoundingClientRect(), a = document.querySelector('#scroll .anytime'); return a ? [Math.round(a.getBoundingClientRect().left - sc.left), Math.round(sc.right - a.getBoundingClientRect().right)] : null; });
  ok(anyW && anyW[0] === 12 && anyW[1] === 12, 'width: a plan’s No set time card shares the 12px edge', anyW);
  await click(page, '[data-a="schedTab"][data-x="mine"]');
  const mineTap = await tapLab();
  ok(plTap === '26px' && mineTap === '26px', 'width: a tapped day keeps the 26px hour column on My Classes and on a plan', { plTap, mineTap });
  await click(page, '[data-a="schedTab"][data-x="planner"]');
  ok(await page.locator('#scroll .schpg').count() === 0, 'width: the Planner tab is unchanged');
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
  /* + 12: 6px of air above the first hour and below the last (2026-10-05) */
  ok(fit.every(f => f && f.out === 0 && f.h <= 312 && f.folds === 0 && (f.b2b || f.h === f.want + 12) && (!f.b2b || f.h > f.want + 12 || f.h === 312)), 'home: each card is its own hours at 30px/h (a bit more for back-to-back classes) plus 6px top and bottom, every class inside, hours never over 300px, no “No classes” band', fit);
  ok(fit.every(f => f.h < 300) && new Set(fit.map(f => f.h)).size > 1, 'home: cards are smaller than the old fixed 300px and differ by schedule', fit.map(f => f.h));
  const q = fit.find(f => f.id === Q);
  ok(q.hours < 6, 'home: a short day is not padded out to six hours', q);
  const labs = await page.locator('#hf-' + Q + ' .g-lab span').allInnerTexts();
  const hr = t => { const m = /^(\d+)(a|p)$/.exec(t); return (+m[1] % 12) + (m[2] === 'p' ? 12 : 0); };
  ok(labs.length === q.hours + 1 && labs.every((t, i) => !i || hr(t) - hr(labs[i - 1]) === 1), 'home: a short card labels every hour on an even step (12p 1p 2p 3p, never 12p 2p 3p)', labs);
  /* Each card's days work on their own. */
  /* in friend-list order: the feed itself is shuffled (2026-10-04) */
  const focused = () => page.evaluate(() => TC.friends.map(id => document.getElementById('hf-' + id)).map(c => { const f = c && c.querySelector('.g-day.on'); return f ? f.dataset.x : null; }));
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
  /* On the friend page, the week and each shared plan keep their own open day (one grid shows at a time). */
  const gridsOn = () => page.evaluate(() => [...document.querySelectorAll('.grid')].map(g => { const f = g.querySelector('.g-day.on'); return f ? f.dataset.x : null; }));
  ok((await page.locator('.grid').count()) === 1, 'friend page: one grid, the week', await page.locator('.grid').count());
  await click(page, '.fsw button[data-y="A"]');
  await click(page, '.plancol .g-day[data-x="T"]');
  let g = await gridsOn();
  await click(page, '.fsw button[data-y="now"]');
  const g2 = await gridsOn();
  ok(g[0] === 'T' && g2[0] === null, 'friend page: tapping a day on the plan opens only the plan’s grid; the week stays closed', { plan: g, week: g2 });
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
  ok(probe.end.out === 0 && probe.end.H === 102, 'grid fit: a class ending at the axis end stays inside (8:10–9:00 + 10:10–11:00 → 8a–11a, 90px of hours + 12px of air)', probe.end);
  ok(probe.long.H === 312 && probe.long.out === 0, 'grid fit: a 7a–9p day with no long break is capped at 300px of hours (+12px of air), not 420', probe.long);
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
  ok(tj.rest.H === 312 && tj.rest.h1 >= 24 && tj.rest.gap12 >= 0.5, 'grid fit: an 8a–8p card stops at 300px of hours (+12px of air), and the back-to-back 8:00 and 9:00 classes still don’t touch', tj.rest);
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
  ok(!/g-body/.test(noTimes) && /class="anyrow"[\s\S]*UNIV 1101[\s\S]*No section/.test(noTimes) && !/No set times for/.test(noTimes), 'home: a friend with no set class times gets the Anytime tray, not an empty grid', noTimes.slice(-400));
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
  const row = await page.evaluate(c => { const r = document.querySelector(c + ' .anyrow'), g = document.querySelector(c + ' .g-body'), cs = getComputedStyle(r);
    return r && { t: r.innerText.replace(/\s+/g, ' '), below: r.getBoundingClientRect().top >= g.getBoundingClientRect().bottom + 8, tray: cs.backgroundColor !== 'rgba(0, 0, 0, 0)' && cs.borderRadius === '14px', notes: r.querySelectorAll('small,svg,img').length,
      white: (bl => [...r.querySelectorAll('.any-c')].every(b => getComputedStyle(b).backgroundColor === bl && getComputedStyle(b).color === getComputedStyle(document.querySelector(c + ' .g-b:not(.live):not(.sel)')).color))(getComputedStyle(document.querySelector(c + ' .g-b:not(.live):not(.sel)')).backgroundColor),
      chips: [...r.querySelectorAll('.any-c')].map(b => [b.innerText.replace(/\s+/g, ' '), b.dataset.a, b.dataset.y || '', b.classList.contains('shared')]) }; }, card);
  ok(row && row.below && /^Anytime BUS 4488 BUS 4488$/i.test(row.t), 'anytime: Avery’s online section and her unposted-time section sit in the Anytime tray, apart from her week', row);
  ok(row && row.tray && row.notes === 0 && row.white, 'anytime: a soft grey tray with chips in the week’s own light blue, holding just the code — no notes, no icons (2026-10-04)', row);
  ok(await page.locator(card + ' .g-b').count() === before && await page.locator(card + ' .g-b[data-x="BUS 4488"]').count() === 0, 'anytime: neither is drawn on the grid', before);
  ok(row && row.chips.every(c => c[1] === 'secSheet' && c[2]) && row.chips.every(c => !c[3]), 'anytime: section chips open the section preview; no ring on a class I’m not in', row && row.chips);
  await click(page, `${card} .any-c[data-y="70901"]`); await tick(page, 400);
  let sh = (await page.locator('#sheet').innerText()).replace(/\s+/g, ' ');
  ok(/BUS 4488/.test(sh) && /Online · self-paced/.test(sh) && /IN THIS SECTION (\w+ )?Avery/i.test(sh) && await page.locator('.homehdr').count() === 1, 'anytime: tapping the online chip opens its preview — online, self-paced, Avery in it — and stays on Home', sh.slice(0, 240));
  await click(page, '#sheet .xbtn');
  await click(page, `${card} .any-c[data-y="70902"]`); await tick(page, 400);
  sh = (await page.locator('#sheet').innerText()).replace(/\s+/g, ' ');
  ok(/BUS 4488/.test(sh) && /Time not posted/.test(sh), 'anytime: the unposted-time chip’s preview says “Time not posted”, never a made-up time', sh.slice(0, 200));
  await click(page, '#sheet .xbtn');
  /* A class I'm in too gets the same yellow ring as a shared block. */
  await page.evaluate(() => { PEOPLE.me.unplaced = (PEOPLE.me.unplaced || []).concat(['BUS 4488']); render(true); });
  await tick(page, 200);
  const rings = await page.locator(card + ' .any-c.shared').count();
  ok(rings === 2, 'anytime: a class I share gets the yellow ring, as on the grid', rings);
  /* On my own week there is no ring — every class is mine. */
  const meCard = await page.evaluate(() => { const k = PEOPLE.me.secs; PEOPLE.me.secs = k.concat([SEC['70901']]); try { return homeWeekCard('me'); } finally { PEOPLE.me.secs = k; } });
  ok(/class="anyrow"[\s\S]*BUS 4488/.test(meCard) && !/any-c shared/.test(meCard), 'anytime: my own week lists my online class, with no ring', meCard.slice(-400));
  /* Two-line codes, every class shown (Tate, 2026-10-03: "put the class codes under the Bus … i dont like the +1"). */
  await page.evaluate(id => { PEOPLE[id].secs = PEOPLE[id].secs.concat([SEC['70900'], { id: 'wk1', code: 'KINE 1001', sec: '01', prof: null, days: 'S', s: 540, e: 650, async: false }]); render(true); }, A);
  await tick(page, 200);
  const line = () => page.evaluate(c => { const r = document.querySelector(c + ' .anyrow'), rb = r.getBoundingClientRect(), chips = [...r.querySelectorAll('.any-c')];
    return { n: chips.length, more: r.querySelectorAll('.any-more').length + (/\+\d/.test(r.innerText) ? 1 : 0), lines: new Set(chips.map(k => Math.round(k.getBoundingClientRect().top))).size,
      fits: chips.every(k => { const b = k.getBoundingClientRect(); return b.right <= rb.right - 7.5 && b.left >= rb.left; }), whole: r.scrollWidth <= r.clientWidth,
      stacked: chips.every(k => { const sp = k.querySelectorAll('span'); return sp.length === 2 && sp[1].getBoundingClientRect().top >= sp[0].getBoundingClientRect().bottom - 1 && /^[A-Z]+$/.test(sp[0].innerText) && /^\d/.test(sp[1].innerText); }),
      codes: chips.map(k => k.getAttribute('aria-label')), w: Math.max(...chips.map(k => Math.round(k.getBoundingClientRect().width))) }; }, card);
  const L390 = await line();
  ok(L390.n === 3 && L390.more === 0 && L390.codes.includes('KINE 1001') && L390.lines === 1, 'anytime: every class is shown — no “+N” — and three fit on one line at 390px', L390);
  ok(L390.stacked && L390.w <= 72, 'anytime: each chip has the subject over the number, like a block on the week, so it is narrow', L390);
  ok(await page.locator(card + ' .g-b[data-x="BUS 4488"]').count() === 1 && await page.locator(card + ' .g-b[data-x="KINE 1001"]').count() === 0, 'anytime: her Friday BUS 4488 is on the week; the Saturday class is not', L390);
  const tall = await page.locator(card + ' .anyrow > button').evaluateAll(es => es.map(e => Math.round(e.getBoundingClientRect().height)));
  ok(tall.every(h => h >= 42), 'anytime: chips are at least 42px tall to tap', tall);
  /* Many classes at any width: all of them, wrapping to more lines, never clipped. */
  await page.evaluate(id => { PEOPLE[id].unplaced = (PEOPLE[id].unplaced || []).concat(['WGS 3100', 'MU 1010', 'ME 2000', 'MATH 1410']); render(true); }, A);
  const sweep = [];
  for (const w of [300, 330, 360, 375, 390, 414, 430]) {
    await page.setViewportSize({ width: w, height: 844 }); await tick(page, 400);
    const L = await line(); L.vw = w; sweep.push(L);
  }
  ok(sweep.every(L => L.n === 7 && L.more === 0 && L.fits && L.whole && L.stacked), 'anytime: from 300px to 430px, all seven classes show, two-line codes, nothing clipped', sweep.map(L => [L.vw, L.n, L.lines]));
  ok(sweep.every(L => L.lines <= 2) && sweep.some(L => L.lines === 2), 'anytime: seven classes wrap to a second line rather than hide', sweep.map(L => [L.vw, L.lines]));
  await page.setViewportSize({ width: 390, height: 844 }); await tick(page, 600);
  /* A class saved with no section opens the class itself — there is no section to preview. */
  const R = '#hf-' + FX.FRIENDS[1].id;
  await page.evaluate(r => document.querySelector(r).scrollIntoView(), R);
  await click(page, `${R} .any-c[data-x="UNIV 1101"]`); await tick(page, 500);
  ok(await page.locator('.homehdr').count() === 0 && /UNIV 1101/.test(await text(page)) && await page.locator('#sheet .xbtn').count() === 0, 'anytime: a class with no section opens its class page', (await text(page)).slice(0, 200));
  ok(log.errors.length === 0, 'anytime: no page errors', log.errors);
  await close();
};

/* ============ Share your week or a plan (Tate, 2026-09-30) ============ */
/* The desktop's own decoder, lifted out of the desktop index.html, so "the landing can read it" is
   checked with the code that actually reads it. */
function deskDecoder() {
  const here = nodePath.dirname(new URL(import.meta.url).pathname);
  const f = [nodePath.resolve(here, '..', 'out', 'index.html'), nodePath.resolve(here, '..', '..', 'index.html')].find(x => nodeFs.existsSync(x));
  const h = nodeFs.readFileSync(f, 'utf8');
  const a = h.indexOf('function _b64urlEnc('), b = h.indexOf('function myScheduleForShare(');
  const ctx = { atob, btoa, escape, unescape, decodeURIComponent, encodeURIComponent };
  nodeVm.createContext(ctx); nodeVm.runInContext(h.slice(a, b) + '\nthis.dec = s => _shDecode(_b64urlDec(s));', ctx);
  return ctx.dec;
}
const shareWrites = log => log.writes.filter(w => w.table.startsWith('storage:schedule-cards/'));
const sharePayload = w => { const m = /\r\n\r\n([A-Za-z0-9_-]{8,})\r\n--/.exec(w.text || '') || /^([A-Za-z0-9_-]{8,})$/.exec(w.text || ''); return m ? m[1] : null; };
async function shareOpenAndWait(page, x) {
  await page.evaluate(x => A.shareOpen(x), x);
  await page.waitForFunction(() => UI.share && ['ready', 'err', 'empty'].includes(UI.share.state), null, { timeout: 8000 });
  await settle(page);
}
const SHARE_INIT = () => { navigator.share = d => { window.__shared = (window.__shared || []).concat([d]); return Promise.resolve(); }; };

tests.shareWeek = async () => {
  const { page, close, log } = await openApp({ init: SHARE_INIT });
  await page.waitForFunction(() => TC.ready, null, { timeout: 8000 });
  await click(page, '[data-a="tab"][data-x="schedule"]');
  await page.evaluate(() => { S.schedTab = 'mine'; PEOPLE.me.secs = PEOPLE.me.secs.concat([SEC['70901']]); render(); });
  ok(await page.locator('.schhdr .schshare[data-x="mine"]').count() === 1, 'share: My Classes has a Share button top right');
  await page.locator('.schhdr .schshare[data-x="mine"]').click();
  await page.waitForFunction(() => UI.share && ['ready', 'err', 'empty'].includes(UI.share.state), null, { timeout: 8000 }); await settle(page);
  const sheet = (await page.locator('#sheet').innerText()).replace(/\s+/g, ' ');
  ok(/Share your week/.test(sheet) && /Send a link/.test(sheet) && /Anyone with the link can see these classes/.test(sheet) && /Send to a friend in TermChamp/.test(sheet), 'share: the sheet — picture, Send a link, who can see it, send to a friend', sheet.slice(0, 260));
  const w = shareWrites(log), png = w.find(x => /\.png$/.test(x.table)), js = w.find(x => /\.json$/.test(x.table));
  const id = png && /schedule-cards\/([0-9a-f]{32})\.png$/.exec(png.table);
  ok(w.length === 2 && id && js && js.table === 'storage:schedule-cards/' + id[1] + '.json', 'share: the picture and the week go up once, under one random 32-hex name', w.map(x => x.table));
  ok(id && id[1] !== FX.ME.id.replace(/-/g, '') && png.bytes > 20000, 'share: the name is random, not the account id; the picture is a real image', png && { id: id && id[1], bytes: png.bytes });
  ok(w.every(x => x.upsert !== 'true'), 'share: no upsert — the bucket has an insert policy only, and an upsert 403s', w.map(x => x.upsert));
  const dec = deskDecoder(), data = dec(sharePayload(js) || '');
  const want = await page.evaluate(() => personSecs('me').map(x => x.code).concat((PEOPLE.me.unplaced || []).filter(c => !personSecs('me').some(y => y.code === c))));
  ok(data && data.term === 'Fall 2026' && JSON.stringify(data.cl.map(r => r.c)) === JSON.stringify(want), 'share: the desktop’s own decoder reads the week back — every class, in order', { data, want });
  const b3438 = data && data.cl.find(r => r.c === 'BUS 3438');
  ok(b3438 && b3438.t === 'MoWe 10:10AM–12:00PM' && data.cl.find(r => r.c === 'BUS 4488').t === 'Online', 'share: times come through as the desktop prints them; an online class says Online', data && data.cl);
  const img = await page.evaluate(() => new Promise(r => { const i = document.querySelector('#sheet .shimg'); if (!i || !i.src) return r(null); if (i.complete) return r(i.naturalWidth); i.onload = () => r(i.naturalWidth); }));
  ok(img === 1200, 'share: the sheet shows the 1200×1200 picture it uploads', img);
  const sync = await page.evaluate(() => { document.querySelector('#sheet .shgo').click(); return (window.__shared || []).length; });
  ok(sync === 1, 'share: the phone’s share sheet opens inside the tap (iOS refuses it after a wait)', sync);
  await settle(page);
  const shared = await page.evaluate(() => window.__shared);
  const url = `https://termchamp.com/s?i=${id && id[1]}.png&nm=Jordan&tm=Fall%202026&add=${FX.ME.id}`;
  ok(shared && shared.length === 1 && shared[0].url === url && !shared[0].text && !shared[0].files, 'share: Send a link hands the phone’s share sheet one bare link (iMessage then shows the preview)', shared);
  await click(page, '#sheet .xbtn');
  await shareOpenAndWait(page, 'mine');
  const again = await page.evaluate(() => UI.share.link);
  ok(shareWrites(log).length === 2 && again === url, 'share: opening it again on the same week reuses the link and uploads nothing', { n: shareWrites(log).length, again });
  ok(log.errors.length === 0, 'share: no page errors', log.errors);
  await close();
};

tests.sharePlan = async () => {
  const { page, close, log } = await openApp({ init: SHARE_INIT });
  await page.waitForFunction(() => TC.ready, null, { timeout: 8000 });
  await click(page, '[data-a="tab"][data-x="schedule"]');
  await page.evaluate(() => { S.schedTab = 'plans'; S.plan = 'B'; render(); });
  ok(await page.locator('.schhdr .schshare[data-x="B"]').count() === 1, 'share plan: the open plan is what the top-right Share sends');
  await page.locator('.schhdr .schshare[data-x="B"]').click();
  await page.waitForFunction(() => UI.share && ['ready', 'err', 'empty'].includes(UI.share.state), null, { timeout: 8000 }); await settle(page);
  const js = shareWrites(log).find(x => /\.json$/.test(x.table)), data = deskDecoder()(sharePayload(js) || '');
  ok(data && data.term === 'Fall 2026 Plan B' && data.cl.length === 1 && data.cl[0].c === 'ECON 2303', 'share plan: just the plan’s real sections (the one no longer offered is left out), labelled Plan B', data);
  const link = await page.evaluate(() => UI.share.link);
  ok(/^https:\/\/termchamp\.com\/s\?i=[0-9a-f]{32}\.png&nm=Jordan&tm=Fall%202026&add=[^&]+&pl=B$/.test(link), 'share plan: the link says which plan (the preview reads “Look at Jordan’s Plan B”)', link);
  const px = await page.evaluate(() => new Promise(r => { const i = document.querySelector('#sheet .shimg'); const go = () => { const c = document.createElement('canvas'); c.width = 1200; c.height = 1200; const g = c.getContext('2d'); g.drawImage(i, 0, 0); r([...g.getImageData(70, 160, 1, 1).data].slice(0, 3)); }; if (i.complete) go(); else i.onload = go; }));
  ok(JSON.stringify(px) === JSON.stringify([194, 65, 12]), 'share plan: the picture carries Plan B’s colour', px);
  const title = await page.locator('#sheet h3').innerText();
  ok(title === 'Share Plan B', 'share plan: the sheet says which plan', title);
  ok(log.errors.length === 0, 'share plan: no page errors', log.errors);
  await close();
};

tests.shareSend = async () => {
  const { page, close, log } = await openApp({ init: SHARE_INIT });
  await page.waitForFunction(() => TC.ready && TC.threads.length, null, { timeout: 8000 });
  await shareOpenAndWait(page, 'mine');
  const A0 = FX.FRIENDS[0].id, G = 'c0000000-0000-4000-8000-000000000002';
  const rows = await page.locator('#sheet .shrow').evaluateAll(es => es.map(e => [e.dataset.a, e.dataset.x]));
  ok(rows.some(r => r[0] === 'shareTo' && r[1] === A0) && rows.some(r => r[0] === 'shareToThread' && r[1] === G), 'share send: friends and group chats are listed', rows);
  const link = await page.evaluate(() => UI.share.link);
  await click(page, `#sheet .shrow[data-a="shareTo"][data-x="${A0}"]`); await settle(page, 800);
  const sent = log.writes.filter(w => w.table === 'messages' && w.m === 'POST');
  ok(sent.length === 1 && sent[0].body.kind === 'text' && sent[0].body.body === 'Here’s my Fall 2026 schedule ' + link, 'share send: one plain text message with the sentence and the link (messages.kind only allows text/class/professor/ask)', sent.map(w => w.body));
  const row = await page.locator(`#sheet .shrow[data-x="${A0}"]`).evaluate(e => ({ t: e.innerText.replace(/\s+/g, ' '), dis: e.disabled }));
  await page.evaluate(id => A.shareTo(id), A0); await settle(page, 800);
  ok(/Sent/.test(row.t) && row.dis && log.writes.filter(w => w.table === 'messages' && w.m === 'POST').length === 1, 'share send: the row says Sent and can’t be sent twice', row);
  await click(page, `#sheet .shrow[data-a="shareToThread"][data-x="${G}"]`); await settle(page, 800);
  const g = log.writes.filter(w => w.table === 'messages' && w.m === 'POST');
  ok(g.length === 2 && g[1].body.conversation_id === G, 'share send: to a group chat too', g.map(w => w.body.conversation_id));
  await click(page, '#sheet .xbtn');
  /* In the chat it reads as a card with the picture; the thread list shows the sentence, not the link. */
  const cid = sent[0].body.conversation_id;
  await page.evaluate(cid => { S.tab = 'friends'; S.stack.friends = [{ s: 'friends' }]; A.openChat(cid); }, cid); await settle(page, 800);
  const card = await page.evaluate(() => { const c = [...document.querySelectorAll('.shcard')].pop(); return c && { img: c.querySelector('img').getAttribute('src'), t: c.innerText.trim(), x: c.dataset.x }; });
  const id = /i=([0-9a-f]{32})\.png/.exec(link)[1];
  ok(card && card.img === `https://rqkndeqbcahozidniesn.supabase.co/storage/v1/object/public/schedule-cards/${id}.png` && card.t === 'Here’s my Fall 2026 schedule', 'share send: in the chat it is a card with the picture and the sentence', card);
  const prev = await page.evaluate(cid => msgText(TC.threads.find(t => t.id === cid).last), cid);
  ok(prev === 'Here’s my Fall 2026 schedule', 'share send: the chat list shows the sentence, not the long link', prev);
  await click(page, `.shcard[data-x="${id}"]`);
  const view = (await page.locator('#sheet').innerText()).replace(/\s+/g, ' ');
  ok(/Your schedule/.test(view) && await page.locator('#sheet .shimg').getAttribute('src') === card.img, 'share send: tapping the card shows the picture full size', view.slice(0, 120));
  /* Only OUR links, on /s, with a 32-hex name, become cards. */
  const plain = await page.evaluate(id => ['look https://evil.com/s?i=' + id + '.png', 'https://termchamp.com/s?i=../../x.png', 'https://termchamp.com/x?i=' + id + '.png', 'https://termchamp.com/s?i=' + id + '.png.evil'].map(b => shMsg({ kind: 'text', body: b })), id);
  ok(plain.every(x => x === null), 'share send: anything but our own share link stays plain text', plain);
  ok(log.errors.length === 0, 'share send: no page errors', log.errors);
  await close();
};

tests.shareErr = async () => {
  const hook = (url, m) => url.pathname.startsWith('/storage/v1/object/schedule-cards/') ? { status: 403, body: JSON.stringify({ statusCode: '403', error: 'Unauthorized', message: 'new row violates row-level security policy' }) } : null;
  const { page, close, log } = await openApp({ init: SHARE_INIT, hook });
  await page.waitForFunction(() => TC.ready, null, { timeout: 8000 });
  await shareOpenAndWait(page, 'mine');
  const t = (await page.locator('#sheet').innerText()).replace(/\s+/g, ' ');
  const dis = await page.evaluate(() => ({ go: document.querySelector('#sheet .shgo').disabled, rows: [...document.querySelectorAll('#sheet .shrow')].every(r => r.disabled) }));
  ok(/Couldn’t get the link ready/.test(t) && dis.go && dis.rows, 'share: a failed upload says so, and offers no link that would open to nothing', { t: t.slice(0, 200), dis });
  await page.evaluate(() => { A.shareLink(); A.shareTo(TC.friends[0]); }); await settle(page, 800);
  ok(!(await page.evaluate(() => window.__shared)) && !log.writes.some(w => w.table === 'messages'), 'share: nothing is sent when the link isn’t ready', log.writes.filter(w => w.table === 'messages'));
  await close();
  /* While the picture is still going up, there is nothing to send yet (iMessage keeps a link's first preview for good). */
  const o3 = await openApp({ init: SHARE_INIT });
  await o3.page.waitForFunction(() => TC.ready, null, { timeout: 8000 });
  await o3.page.evaluate(() => { const c = TC.client(); c.storage.from = () => ({ upload: () => new Promise(() => {}) }); A.shareOpen('mine'); });
  await o3.page.waitForFunction(() => UI.share && UI.share.state === 'up', null, { timeout: 8000 }); await settle(o3.page);
  const up = await o3.page.evaluate(() => { A.shareLink(); return { go: document.querySelector('#sheet .shgo').disabled, rows: [...document.querySelectorAll('#sheet .shrow')].every(r => r.disabled), shared: (window.__shared || []).length }; });
  ok(up.go && up.rows && up.shared === 0, 'share: while the picture is still uploading, the link can’t be sent yet', up);
  await o3.close();
  /* Nothing to share: says so, uploads nothing. */
  const T = Object.assign({}, FX.TABLES, { my_sections: FX.TABLES.my_sections.filter(r => r.user_id !== FX.ME.id), saved_classes: FX.TABLES.saved_classes.filter(r => r.user_id !== FX.ME.id) });
  const o2 = await openApp({ init: SHARE_INIT, tables: T });
  await o2.page.waitForFunction(() => TC.ready, null, { timeout: 8000 });
  await shareOpenAndWait(o2.page, 'mine');
  const t2 = (await o2.page.locator('#sheet').innerText()).replace(/\s+/g, ' ');
  ok(/Nothing to share yet/.test(t2) && !shareWrites(o2.log).length, 'share: with no classes it says so and uploads nothing', t2.slice(0, 120));
  await o2.close();
};

/* ============ Stories: today, most free first; a tap opens their day (Tate, 2026-09-30) ============ */
const STORY_SET = (page, plan) => page.evaluate(plan => {
  const mk = (id, code, s, e, days, prof) => ({ id: 'st' + id + code, code, s, e, days, async: false, sec: '01', prof: prof || null });
  const F = TC.friends.slice().sort((a, b) => PEOPLE[a].name.localeCompare(PEOPLE[b].name));   /* Avery, Harper, Quinn, Rowan, Sky */
  plan.forEach(([k, secs], i) => { const id = F[k]; PEOPLE[id].secs = secs.map(x => mk(i, ...x)); PEOPLE[id].unplaced = []; });
  UI.storyOrder = null; render(true);
  return F.map(id => PEOPLE[id].short);
}, plan);
const storyNames = page => page.locator('.story .nm').allInnerTexts();

tests.storyOrder = async () => {
  const { page, close, log } = await openApp({});   /* Tuesday 10:30a */
  await page.waitForFunction(() => TC.ready && document.querySelectorAll('.story').length === 5, null, { timeout: 8000 });
  /* 0 Avery in class till 11:40 · 1 Harper no classes added · 2 Quinn in class till 11 · 3 Rowan free till 12 · 4 Sky no classes today */
  await STORY_SET(page, [[0, [['BUS 1', 600, 700, 'TR']]], [1, []], [2, [['BUS 2', 600, 660, 'TR']]], [3, [['BUS 3', 720, 800, 'TR']]], [4, [['BUS 4', 600, 700, 'MW']]]]);
  let n = await storyNames(page);
  ok(n.join(',') === 'Sky,Rowan,Quinn,Avery,Harper', 'stories: free now (longest stretch first), then in class (out soonest first), then no classes added', n);
  /* Busy people by when they're next free: Harper starts a class at 10:40 and another straight after
     (free at 12:40), so she comes after Quinn (out at 11) and Avery (out at 11:40). */
  await STORY_SET(page, [[1, [['BUS 5', 640, 680, 'TR'], ['BUS 6', 685, 760, 'TR']]]]);
  n = await storyNames(page);
  ok(n.join(',') === 'Sky,Rowan,Quinn,Avery,Harper', 'stories: busy friends — in class or about to start one — by when they’re next free (back-to-back classes count as one stretch)', n);
  /* A new friend joins the row; a removed one leaves it — without re-sorting everyone else. */
  const gone = await page.evaluate(() => { const g = TC.friends.pop(); render(true); return g; });
  n = await storyNames(page);
  ok(n.length === 4, 'stories: an unfriended person leaves the row', n);
  await page.evaluate(g => { TC.friends.push(g); render(true); }, gone);
  ok((await storyNames(page)).length === 5, 'stories: a new friend joins the row');
  /* Held while you look: statuses change, the row doesn't move — until Home is opened again. */
  await page.evaluate(() => { const sky = TC.friends.find(f => PEOPLE[f].short === 'Sky'); PEOPLE[sky].secs = [{ id: 'hold', code: 'BUS 9', s: 600, e: 720, days: 'TR', async: false }]; render(true); });
  n = await storyNames(page);
  ok(n[0] === 'Sky', 'stories: the row holds its order while you’re looking (rings update, circles don’t jump)', n);
  await click(page, '[data-a="tab"][data-x="explore"]'); await click(page, '[data-a="tab"][data-x="home"]');
  n = await storyNames(page);
  ok(n.join(',') === 'Rowan,Quinn,Avery,Sky,Harper', 'stories: opening Home again re-sorts (Sky, now in class till noon, moves in among the busy)', n);
  /* Ties keep one fixed order, whatever order the friends list arrives in. */
  await page.evaluate(() => { TC.friends.reverse(); TC.friends.forEach(f => { PEOPLE[f].secs = []; PEOPLE[f].unplaced = []; }); UI.storyOrder = null; render(true); });
  n = await storyNames(page);
  ok(n.join(',') === 'Avery,Harper,Quinn,Rowan,Sky', 'stories: a tie keeps one fixed order (by name), not the order the list arrived in', n);
  ok(log.errors.length === 0, 'stories: no page errors', log.errors);
  await close();
};

tests.storyDay = async () => {
  const { page, close, log } = await openApp({});   /* Tuesday 10:30a */
  await page.waitForFunction(() => TC.ready && document.querySelectorAll('.story').length === 5, null, { timeout: 8000 });
  /* Avery today: a class she's in now (with a rated professor, and me in the same section), a free
     stretch, a later class with no professor; plus a Monday class that must not show, and an online one. */
  const setup = await page.evaluate(() => {
    const av = TC.friends.find(f => PEOPLE[f].short === 'Avery');
    const mine = personSecs('me'), rated = SECTIONS.find(x => x.prof && ratingOf(x.prof) != null && mine.some(y => y.id === x.id));
    const nowSec = Object.assign({}, rated, { s: 600, e: 700, days: 'TR' });
    PEOPLE.me.secs = PEOPLE.me.secs.map(y => y.id === rated.id ? nowSec : y);
    PEOPLE[av].secs = [nowSec, { id: 'later', code: 'BUS 7777', s: 840, e: 900, days: 'TR', async: false, prof: null }, { id: 'mon', code: 'BUS 8888', s: 540, e: 600, days: 'MW', async: false }, { id: 'onl', code: 'BUS 6666', async: true, s: null, e: null, days: '' }, { id: 'tba', code: 'BUS 5555', async: false, s: null, e: null, days: '' }];
    PEOPLE[av].unplaced = ['UNIV 1101'];
    UI.storyOrder = null; render(true);
    return { av, code: rated.code, title: course(rated.code).title, prof: profName(rated.prof), r: ratingOf(rated.prof).toFixed(1) };
  });
  const y0 = await page.evaluate(() => document.getElementById('scroll').scrollTop);
  await click(page, `.story[data-x="${setup.av}"]`);
  const t = (await page.locator('#sheet').innerText()).replace(/\s+/g, ' ');
  /* 2026-10-05: the day in the schedule look — one column, every class a block to scale (Tate's option C) */
  const rows = await page.locator('#sheet .stb').evaluateAll(es => es.map(e => { const r = e.getBoundingClientRect(), bd = e.parentElement.getBoundingClientRect();
    const box = e.querySelector('.stbox'), pp = e.querySelector('.stpp'), fc = e.querySelector('.stfaces'), nm = e.querySelector('.stbox .nm');
    return { t: e.innerText.replace(/\s+/g, ' '), now: e.classList.contains('now'), shared: e.classList.contains('shared'), top: r.top - bd.top, h: r.height, l: r.left - bd.left, w: r.width, bw: bd.width,
      box: box && box.dataset.a + ':' + box.dataset.x, boxW: box && box.getBoundingClientRect().width, code: box && box.querySelector('b').innerText, tm: box && box.querySelector('.tm').innerText,
      nmShown: !!(nm && nm.offsetParent && nm.getBoundingClientRect().height > 0 && getComputedStyle(nm).whiteSpace === 'nowrap'), nmH: nm ? nm.getBoundingClientRect().height : 0,
      pp: pp && { a: pp.dataset.a || null, x: pp.dataset.x || null, t: pp.innerText.replace(/\s+/g, ' '), rc: !!pp.querySelector('.rc'), inside: pp.querySelector('.rc') ? pp.getBoundingClientRect().right >= pp.querySelector('.rc').getBoundingClientRect().right - 0.5 : null, bg: getComputedStyle(pp).backgroundColor },
      faces: fc && fc.getAttribute('aria-label'), boxBg: box && getComputedStyle(box).backgroundColor, bg: getComputedStyle(e).backgroundColor }; }));
  ok(await page.evaluate(() => document.getElementById('scroll').scrollTop) === y0 && /Avery Quill/.test(t) && /Tuesday · today/.test(t), 'story: tapping Avery opens her day; the feed doesn’t move', { t: t.slice(0, 120) });
  ok(rows.length === 2 && rows[0].code === setup.code && rows[0].tm === '10:00–11:40a' && rows[1].code === 'BUS 7777' && rows[1].tm === '2:00–3:00p' && !/BUS 8888/.test(t) && rows[0].top < rows[1].top, 'story: today’s classes only, in time order, each with its time in the box', rows.map(r => [r.code, r.tm, r.top]));
  ok(Math.abs(rows[0].h / rows[1].h - 100 / 60) < 0.08 && Math.abs((rows[1].top - rows[0].top) - (rows[0].h + 2) * 240 / 100) < 4, 'story: blocks are to scale — a 100-minute class is 5/3 as tall as an hour, and 2p sits four hours below 10a', rows.map(r => [r.top, r.h]));
  ok(rows[0].h >= 92 && rows[1].h >= 92, 'story: the shortest class today is still tall enough for its box and professor (about 100px)', rows.map(r => r.h));
  const ax = await page.locator('#sheet .stday-ax span').allInnerTexts();
  ok(ax[0] === '10a' && ax.includes('2p') && ax[ax.length - 1] === '3p', 'story: hours down the left, from the first class’s hour to the last one’s', ax);
  ok(await page.locator('#sheet .stday .g-now').count() === 1, 'story: the red now-line is on the day (10:30a is inside it)');
  ok(rows[0].now && rows[0].box === 'openClass:' + setup.code && rows[0].boxW >= rows[0].w - 16, 'story: the class she’s in now carries .now (the red line runs through it); its blue box runs the block’s width and opens the class', rows[0]);
  ok(rows[0].pp && rows[0].pp.a === 'openProf' && rows[0].pp.t.includes(setup.prof) && rows[0].pp.t.includes(setup.r) && rows[0].pp.rc && rows[0].pp.inside, 'story: the professor is a pill with their rating chip inside it, and opens their page', rows[0].pp);
  ok(rows[0].pp.bg !== rows[0].boxBg && rows[0].pp.bg !== 'rgba(0, 0, 0, 0)', 'story: the professor pill and the class box are different colours (purple, blue)', [rows[0].pp.bg, rows[0].boxBg]);
  ok(setup.title && setup.title !== setup.code && rows[0].t.includes(setup.title) && rows[0].nmShown && rows[0].nmH < 24 && rows[1].t.split('BUS 7777').length === 2, 'story: the course name is on one line under the code, and a course with no name doesn’t repeat its code', { title: setup.title, rows: rows.map(r => [r.t, r.nmH]) });
  ok(rows[1].pp && !rows[1].pp.a && /Instructor not assigned/.test(rows[1].t) && !/No ratings yet/.test(rows[1].t), 'story: no professor is said plainly — no rating invented, nothing to tap', rows[1]);
  ok(rows[0].faces === 'With them: You' && rows[0].shared && /With you/.test(rows[0].t) && !rows[1].faces && !rows[1].shared && !/With you/.test(rows[1].t), 'story: who you know is in that class with them (you, here: your face, the yellow ring, “With you”)', rows.map(r => [r.faces, r.shared]));
  ok(rows.every(r => r.l >= 0 && r.l + r.w <= r.bw + 0.5), 'story: blocks stay inside the day', rows.map(r => [r.l, r.w, r.bw]));
  ok(!/Free 11:40a/.test(t) && /Anytime: BUS 6666, BUS 5555, UNIV 1101/.test(t), 'story: no free-time rows; the same Anytime classes as the Home tray (online, time not posted, no section yet)', t);
  const head = await page.evaluate(() => { const el = document.querySelector('#sheet .sthead'), ln = el && el.querySelector('.b'), ring = el && el.querySelector('.ringav');
    return { a: el && el.dataset.a, x: el && el.dataset.x, line: ln && ln.innerText, col: ln && getComputedStyle(ln).color, rc: ring && ring.getAttribute('style'),
      nav: document.querySelectorAll('#sheet [data-a="story"], #sheet [data-a="openChatWith"], #sheet .stnav').length, green: [...document.querySelectorAll('#sheet *')].filter(e => /^rgb\(22, 163, 74\)$/.test(getComputedStyle(e).color)).length }; });
  ok(head.a === 'openFriend' && head.x === setup.av, 'story: the photo and name open their page (Full week is gone)', head);
  ok(head.nav === 0, 'story: no Message, Full week or ‹ › arrows (Tate, 2026-10-05)', head);
  ok(head.line && !/●/.test(head.line) && head.col !== 'rgb(22, 163, 74)' && head.green === 0 && /var\(--line2\)/.test(head.rc || ''), 'story: no green for free time — the status line is grey and the ring neutral', head);
  /* two classes that overlap sit side by side */
  await page.evaluate(av => { PEOPLE[av].secs.push({ id: 'clash', code: 'BUS 4444', s: 870, e: 950, days: 'TR', async: false, prof: null }); A.story(av); }, setup.av); await settle(page);
  const cl = await page.locator('#sheet .stb').evaluateAll(es => es.map(e => { const r = e.getBoundingClientRect(); return { code: e.querySelector('.stbox b').innerText, l: r.left, r: r.right, t: r.top, b: r.bottom }; }));
  const a1 = cl.find(x => x.code === 'BUS 7777'), a2 = cl.find(x => x.code === 'BUS 4444');
  ok(cl.length === 3 && a1 && a2 && (a1.r <= a2.l + 0.5 || a2.r <= a1.l + 0.5) && a1.t < a2.b && a2.t < a1.b && cl.find(x => x.code === setup.code).r - cl.find(x => x.code === setup.code).l > (a1.r - a1.l) * 1.8, 'story: two classes at the same time sit side by side, never on top of each other; a class with no clash keeps the full width', cl);
  /* a 50-minute class (the usual MWF length) keeps its name line, "With you" and its professor */
  await page.evaluate(([av, code]) => { const s0 = PEOPLE[av].secs[0]; PEOPLE[av].secs = [Object.assign({}, s0, { s: 600, e: 650 }), PEOPLE[av].secs[1]]; PEOPLE.me.secs = PEOPLE.me.secs.map(y => y.id === s0.id ? Object.assign({}, y, { s: 600, e: 650 }) : y); A.story(av); }, [setup.av, setup.code]); await settle(page);
  const f50 = await page.locator('#sheet .stb').first().evaluate(e => { const nm = e.querySelector('.stbox .nm'), wy = e.querySelector('.wy'), pp = e.querySelector('.stpp');
    const vis = el => !!(el && el.getClientRects().length && el.getBoundingClientRect().bottom <= e.getBoundingClientRect().bottom + 0.5);
    return { h: e.getBoundingClientRect().height, nm: vis(nm), wy: vis(wy), pp: vis(pp), cls: e.className }; });
  ok(f50.h >= 88 && f50.h <= 100 && f50.nm && f50.wy && f50.pp, 'story: a 50-minute class keeps its name line, “With you” and its professor, all inside the block', f50);
  /* narrow phone: nothing spills sideways */
  await page.setViewportSize({ width: 320, height: 760 }); await settle(page);
  const sp = await page.evaluate(() => { const b = document.querySelector('#sheet .sbody'); return { sw: b.scrollWidth, cw: b.clientWidth, over: [...document.querySelectorAll('#sheet .stb')].filter(e => e.scrollWidth > e.clientWidth + 1).length }; });
  ok(sp.sw <= sp.cw + 1 && sp.over === 0, 'story: at 320px nothing spills sideways', sp);
  await page.setViewportSize({ width: 390, height: 844 }); await settle(page);
  const harper = await page.evaluate(() => TC.friends.find(f => PEOPLE[f].short === 'Harper'));
  await page.evaluate(h => A.story(h), harper); await settle(page);
  ok(/Harper hasn’t added classes/.test(await page.locator('#sheet').innerText()) && !/Anytime/.test(await page.locator('#sheet').innerText()), 'story: a friend with no classes says so');
  /* only classes with no time: said plainly, and listed — not "hasn't added classes" */
  await page.evaluate(h => { PEOPLE[h].secs = [{ id: 'o2', code: 'BUS 6666', async: true, s: null, e: null, days: '' }]; PEOPLE[h].unplaced = ['UNIV 1101']; A.story(h); }, harper); await settle(page);
  const ht = (await page.locator('#sheet').innerText()).replace(/\s+/g, ' ');
  ok(/No set class times/.test(ht) && /Anytime: BUS 6666, UNIV 1101/.test(ht) && !/hasn’t added/.test(ht), 'story: a friend whose classes all have no time says so and lists them', ht.slice(0, 200));
  ok(log.errors.length === 0, 'story: no page errors', log.errors);
  await close();
};

tests.pullRefresh = async () => {
  const { page, close, log } = await openApp({});
  await page.waitForFunction(() => TC.ready && document.querySelectorAll('.story').length === 5, null, { timeout: 8000 });
  const loads = () => log.reads.filter(r => /^my_sections/.test(r)).length;
  const pull = (dy, at = 120, tap = null) => page.evaluate(([dy, at, tap]) => { const sc = document.getElementById('scroll');
    const T = y => new Touch({ identifier: 1, target: sc, clientX: 150, clientY: y });
    sc.dispatchEvent(new TouchEvent('touchstart', { touches: [T(at)], bubbles: true }));
    for (let k = 1; k <= 5; k++) sc.dispatchEvent(new TouchEvent('touchmove', { touches: [T(at + dy * k / 5)], bubbles: true }));
    sc.dispatchEvent(new TouchEvent('touchend', { touches: [], bubbles: true }));
    if (tap) document.querySelector(tap).click(); }, [dy, at, tap]);
  let n0 = loads();
  await pull(40); await settle(page, 800);
  ok(loads() === n0, 'pull: a short tug does not refresh');
  const order0 = await page.evaluate(() => UI.storyOrder);
  await pull(120); await settle(page, 1500);
  ok(loads() > n0 && await page.evaluate(o => UI.storyOrder !== o && Array.isArray(storyOrder()), order0), 'pull: pulling down past the line reloads everything and re-sorts the stories', { n0, n1: loads() });
  /* a tap straight after letting go (a finger never makes a click from a pull, so nothing may be swallowed) */
  await pull(120, 120, '[data-a="tab"][data-x="schedule"]'); await settle(page, 1500);
  ok(await page.evaluate(() => S.tab) === 'schedule', 'pull: a tap right after a pull still works (a pull doesn’t eat it)');
  await click(page, '[data-a="tab"][data-x="home"]');
  /* A refresh never jumps you back down the page (Home remembered where you were before a class page). */
  await page.evaluate(() => { document.getElementById('scroll').scrollTop = 500; });
  await page.evaluate(() => A.openClass('BUS 3438')); await settle(page); await click(page, '[data-a="back"]');
  await page.evaluate(() => { document.getElementById('scroll').scrollTop = 0; }); await settle(page);
  await pull(120); await settle(page, 1500);
  ok(await page.evaluate(() => document.getElementById('scroll').scrollTop) === 0, 'pull: after the refresh you are still at the top, where you pulled');
  n0 = loads();
  await page.evaluate(() => { document.getElementById('scroll').scrollTop = 300; }); await pull(150); await settle(page, 800);
  ok(loads() === n0, 'pull: not when the page is scrolled down (that is just scrolling)');
  await page.evaluate(() => { document.getElementById('scroll').scrollTop = 0; });
  await click(page, '[data-a="tab"][data-x="explore"]'); n0 = loads(); await pull(150); await settle(page, 800);
  ok(loads() === n0, 'pull: only on Home', { n0, n1: loads(), tab: await page.evaluate(() => [S.tab, cur().s, PTR.busy, PTR.y0]), last: log.reads.slice(-6) });
  await close();
  /* No connection: the refresh says so and leaves you in the app (it used to be "Couldn't load your profile"). */
  let offline = false;
  const o3 = await openApp({ hook: url => offline && url.pathname === '/rest/v1/profiles' ? { status: 503, body: JSON.stringify({ message: 'offline' }) } : null });
  await o3.page.waitForFunction(() => TC.ready && document.querySelectorAll('.story').length === 5, null, { timeout: 8000 });
  offline = true;
  await o3.page.evaluate(() => homeRefresh()); await settle(o3.page, 800);
  const st3 = await o3.page.evaluate(() => ({ phase: TC.phase, toast: document.getElementById('toast').textContent, busy: PTR.busy, stories: document.querySelectorAll('.story').length, prof: TC.profile && TC.profile.id === TC.user.id }));
  ok(st3.phase === 'ok' && /Couldn’t refresh/.test(st3.toast) && !st3.busy && st3.stories === 5, 'pull: offline, the refresh says so and you stay in the app', st3);
  ok(st3.prof === true, 'pull: a failed refresh keeps your profile (a nulled one broke every later profile edit)', st3);
  await o3.close();
  /* The Desktop preview: a mouse drag does it too, and a drag that starts on a story is not a tap. */
  const o2 = await openApp({ width: 1200, height: 900 });
  await o2.page.waitForFunction(() => TC.ready && document.querySelectorAll('.story').length === 5, null, { timeout: 8000 });
  const m0 = o2.log.reads.filter(r => /^my_sections/.test(r)).length;
  const b = await o2.page.locator('.story').first().boundingBox();
  /* let go still on the same story (it is 95px tall): the browser then sends a click to it */
  ok(b.height >= 90, 'pull: the story is tall enough to drag 80px within it', b);
  await o2.page.mouse.move(b.x + b.width / 2, b.y + 6); await o2.page.mouse.down();
  for (let k = 1; k <= 4; k++) await o2.page.mouse.move(b.x + b.width / 2, b.y + 6 + k * 20);
  await o2.page.mouse.up(); await settle(o2.page, 1500);
  ok(o2.log.reads.filter(r => /^my_sections/.test(r)).length > m0 && await o2.page.evaluate(() => !UI.sheet), 'pull: a mouse drag in the Desktop preview refreshes, and doesn’t also open the story it started on');
  ok(log.errors.length === 0 && o2.log.errors.length === 0, 'pull: no page errors', log.errors.concat(o2.log.errors));
  await o2.close();
};

/* ============ On a phone the strip over the clock is the app's colour (Tate, 2026-10-04) ============ */
tests.phoneTopBlend = async () => {
  const look = page => page.evaluate(() => { const b = getComputedStyle(document.body), h = getComputedStyle(document.documentElement), st = getComputedStyle(document.getElementById('status')), ph = getComputedStyle(document.querySelector('.phone'));
    return { body: b.backgroundColor, img: b.backgroundImage, html: h.backgroundColor, status: st.backgroundColor, phone: ph.backgroundColor }; });
  const o = await openApp({}); await o.page.waitForFunction(() => TC.ready, null, { timeout: 8000 });
  const a = await look(o.page);
  const BG = 'rgb(231, 236, 245)'; /* Home is the deep page since 20:30; Schedule is checked below */
  ok(a.body === BG && a.img === 'none' && (a.html === BG || a.html === 'rgba(0, 0, 0, 0)') && a.status === BG && a.phone === BG, 'top blend: on a phone the page behind the clock, the app’s top band and the app are one colour', a);
  await o.page.evaluate(() => { document.getElementById('scroll').scrollTop = 400; }); await settle(o.page);
  const a2 = await look(o.page);
  ok(a2.body === BG && a2.status === BG, 'top blend: scrolled, still one colour', a2);
  await o.page.evaluate(() => { document.getElementById('scroll').scrollTop = 0; }); await settle(o.page);
  await click(o.page, '[data-a="tab"][data-x="schedule"]');
  const a3 = await look(o.page), L = 'rgb(244, 246, 251)';
  ok(a3.body === L && a3.status === L && a3.phone === L, 'top blend: on another tab all one colour too (#F4F6FB)', a3);
  await o.close();
  const d = await openApp({ width: 1200, height: 900 }); await d.page.waitForFunction(() => TC.ready, null, { timeout: 8000 });
  const b = await look(d.page);
  ok(/radial-gradient/.test(b.img) && b.body !== BG, 'top blend: the Desktop preview keeps its dotted desk', b);
  ok(o.log.errors.length === 0 && d.log.errors.length === 0, 'top blend: no page errors', o.log.errors.concat(d.log.errors));
  await d.close();
};

/* ============ ITP and Physics (BA) in the major list; Experience & Event Management renamed (Tate, 2026-10-06) ============ */
tests.newMajors = async () => {
  const OLD = 'Recreation, Parks & Tourism Administration / Experience Industry Management', NEW = 'Experience & Event Management';
  const T = Object.assign({}, FX.TABLES, { profiles: FX.TABLES.profiles.map(p => p.id === FX.ME.id ? Object.assign({}, p, { major: OLD, concentration: null }) : p.id === FX.FRIENDS[0].id ? Object.assign({}, p, { major: OLD }) : p) });
  /* the concentration this phone kept, saved beside the old major name */
  const init = `try{localStorage.setItem('termchamp_app_conc',JSON.stringify({u:${JSON.stringify(FX.ME.id)},major:${JSON.stringify(OLD)},conc:'Event Planning and Management'}))}catch(e){}`;
  const { page, close, log } = await openApp({ tables: T, init });
  await page.waitForFunction(() => TC.ready && window.TCPL, null, { timeout: 8000 }).catch(() => {});
  await page.evaluate(() => TC.loadPlanner && TC.loadPlanner()); await page.waitForFunction(() => window.TCPL && TCPL.majors && TCPL.majors.length > 60, null, { timeout: 8000 });
  const m = await page.evaluate(([OLD, NEW]) => ({ list: TCPL.majors, sorted: TCPL.majors.join('|') === TCPL.majors.slice().sort().join('|'), me: TC.profile.major }), [OLD, NEW]);
  ok(['Industrial Technology & Packaging', 'Physics (BA)', 'Physics', NEW].every(n => m.list.includes(n)) && !m.list.includes(OLD) && m.sorted, 'majors: ITP and Physics (BA) are in the phone’s major list, EEM under its catalog name, the old name gone', m.list.filter(n => /Packag|Physics|Experience|Recreation/.test(n)));
  ok(m.me === NEW, 'majors: a profile saved with the old EEM name reads as Experience & Event Management', m.me);
  const mc = await page.evaluate(() => TC.profile.concentration);
  ok(mc === 'Event Planning and Management', 'majors: the concentration kept on the phone under the old name still belongs to the student', mc);
  const fm = await page.evaluate(id => PEOPLE[id] && PEOPLE[id].major, FX.FRIENDS[0].id);
  ok(fm === NEW, 'majors: a friend saved with the old EEM name shows Experience & Event Management on their page', fm);
  /* each new plan is the catalog's own: its classes, term by term, and its unit totals */
  const plan = await page.evaluate(() => { const S = n => { const k = Object.keys(SCHED_MAJORS).find(k => SCHED_MAJORS[k].name === n); return k && SCHED_MAJORS[k]; };
    const sum = e => e.terms.map(t => t.slots.reduce((a, x) => a + x.units, 0)), codes = e => e.terms.flatMap(t => t.slots.map(x => x.code || (x.options ? x.options.join('/') : x.type)));
    const itp = S('Industrial Technology & Packaging'), ba = S('Physics (BA)'), eem = S('Experience & Event Management');
    return { itp: itp && { deg: itp.degree, src: itp.src, units: sum(itp), codes: codes(itp), conc: TCPL.concInfo('Industrial Technology & Packaging').list.map(c => c.name + ':' + c.classes.length) },
      ba: ba && { deg: ba.degree, src: ba.src, units: sum(ba), codes: codes(ba) }, eem: eem && { units: sum(eem), conc: TCPL.concInfo('Experience & Event Management').list.map(c => c.name) } }; });
  const IC = plan.itp && plan.itp.codes.join(' ');
  ok(plan.itp && plan.itp.deg === 'BS' && /industrial-technology-packaging-bs/.test(plan.itp.src) && plan.itp.units.join() === '13,16,15,15,17,15,15,12'
    && /^ITP 1100 ITP 1125 MATH 1261\/MATH 1277 PHYS 1121 ge ITP 1150 ITP 2233 CHEM 1120 STAT 1110\/STAT 1210 ge ITP 3330 ITP 3371 ECON 2001 concentration ge/.test(IC)
    && !/ITP 2260|ITP 3390|ITP 4403/.test(IC) && (IC.match(/concentration/g) || []).length === 10, 'majors: ITP is the catalog’s undeclared roadmap — the shared core, 10 concentration slots, no Industrial Technology classes forced on everyone', plan.itp);
  ok(plan.itp && plan.itp.conc.join() === 'Industrial Technology:8,Packaging:7', 'majors: ITP’s two concentrations with their required classes', plan.itp && plan.itp.conc);
  ok(plan.ba && plan.ba.deg === 'BA' && /physics-ba/.test(plan.ba.src) && plan.ba.units.join() === '15,15,16,14,14,15,15,16' && /PHYS 3341 PHYS 4405 PHYS 4461/.test(plan.ba.codes.join(' ')), 'majors: Physics (BA) is the catalog’s four-year plan, term totals 15·15·16·14·14·15·15·16', plan.ba);
  ok(plan.eem && plan.eem.units.join() === '15,13,16,16,15,15,16,12' /* 13: its 1–3 unit free elective counts as 1 */ && plan.eem.conc.join('|') === 'Event Planning and Management|Sport and Recreation Management|Tourism, Hospitality, and Destination Management', 'majors: EEM keeps its flowchart (Year 2 Spring now has its third GE) and its three concentrations under the new name', plan.eem);
  /* the Planner works for an EEM student saved under the old name */
  await click(page, '[data-a="tab"][data-x="schedule"]'); await click(page, '[data-a="schedTab"][data-x="past"]'); await tick(page, 2500);
  const t = await text(page);
  ok(/Experience & Event Management/.test(t) && /requirements filled/.test(t) && !/Recreation, Parks/.test(t), 'majors: the old-name student’s Planner opens on Experience & Event Management with its ledger', t.slice(0, 300));
  /* the Edit profile picker offers the new majors */
  await page.evaluate(() => A.openEditProfile && A.openEditProfile()); await tick(page, 600);
  const opts = await page.evaluate(() => { const sel = document.querySelector('select[data-k="major"]'); return sel && { all: [...sel.options].map(o => o.value), cur: sel.value }; });
  ok(opts && ['Industrial Technology & Packaging', 'Physics (BA)', 'Experience & Event Management'].every(n => opts.all.includes(n)) && !opts.all.includes(OLD) && opts.cur === NEW, 'majors: Edit profile offers ITP and Physics (BA), and shows the old-name student as Experience & Event Management', opts && { cur: opts.cur, n: opts.all.length });
  ok(log.errors.length === 0, 'majors: no page errors', log.errors);
  await close();
  /* a student who picks ITP gets its ledger */
  const T2 = Object.assign({}, FX.TABLES, { profiles: FX.TABLES.profiles.map(p => p.id === FX.ME.id ? Object.assign({}, p, { major: 'Industrial Technology & Packaging', concentration: 'Packaging' }) : p) });
  const o = await openApp({ tables: T2 });
  await click(o.page, '[data-a="tab"][data-x="schedule"]'); await click(o.page, '[data-a="schedTab"][data-x="past"]'); await tick(o.page, 2500);
  const t2 = await text(o.page);
  ok(/Industrial Technology & Packaging/.test(t2) && /requirements filled/.test(t2) && /ITP 1100/.test(t2), 'majors: an ITP student’s Planner shows the ITP ledger and flowchart', t2.slice(0, 300));
  ok(o.log.errors.length === 0, 'majors: no page errors (ITP)', o.log.errors);
  await o.close();
};

/* ============ Home: a deeper page and blue-topped suggestions (Tate, 2026-10-04) ============ */
tests.homeDeep = async () => {
  const { page, close, log } = await openApp({});
  await page.waitForFunction(() => TC.ready && document.querySelectorAll('.hfeed .fcard').length === 5 && TC.myHistory !== undefined, null, { timeout: 8000 });
  await page.evaluate(() => { [TC.friends[0], TC.friends[3]].forEach(f => { PEOPLE[f].unplaced = (PEOPLE[f].unplaced || []).concat(['MATH 1001']); }); render(true); }); await settle(page, 200);
  const DEEP = 'rgb(231, 236, 245)', BG = 'rgb(244, 246, 251)';
  const look = () => page.evaluate(() => { const C = el => el ? getComputedStyle(el) : null, fc = document.querySelector('.hfeed .fcard'), col = document.querySelector('.hfeed .g-col');
    return { phone: C(document.querySelector('.phone')).backgroundColor, status: C(document.getElementById('status')).backgroundColor, body: C(document.body).backgroundColor, meta: [...document.querySelectorAll('meta[name=theme-color]')].map(m => m.content),
      card: fc ? C(fc).backgroundColor : null, sh: fc ? C(fc).boxShadow : null, col: col ? C(col).backgroundColor : null, tab: S.tab }; });
  const h = await look();
  ok(h.phone === DEEP && h.status === DEEP && h.body === DEEP && h.meta.every(m => m === '#E7ECF5'), 'deep: on Home the page, the top band, the phone strip and the page behind the clock are all #E7ECF5', h);
  ok(h.card === 'rgb(255, 255, 255)' && /0px 14px 30px/.test(h.sh) && h.col === BG, 'deep: friend weeks stay white with a firmer shadow, their day columns unchanged', h);
  await click(page, '[data-a="tab"][data-x="schedule"]');
  const s = await look();
  ok(s.phone === BG && s.status === BG && s.body === BG && s.meta.every(m => m === '#F4F6FB'), 'deep: other tabs keep #F4F6FB (top still one colour)', s);
  await click(page, '[data-a="tab"][data-x="home"]');
  ok((await look()).phone === DEEP, 'deep: back on Home it is deep again');
  /* suggestions: blue tops */
  const r = await page.evaluate(() => { const sec = document.querySelector('.hfeed .recs'), b = sec && sec.querySelector('.rmini'); if (!b) return null; const top = b.querySelector('.rm-top'), k = b.querySelector('.rm-k'), bd = b.querySelector('.rm-bd'), C = el => el && getComputedStyle(el);
    const rows = [...sec.querySelectorAll('.rmini')].map(x => x.querySelector('.rm-top') && getComputedStyle(x.querySelector('.rm-top')).backgroundColor);
    return { h: [...sec.querySelector('.recs-h').children].map(x => x.textContent.trim()).join(' '), tag: C(sec.querySelector('.rs-tag')) && sec.querySelector('.rs-tag').textContent, top: C(top) && C(top).backgroundColor, k: k && k.innerText, kc: C(k) && C(k).color, kfs: C(k) && C(k).fontSize, kbg: C(k) && C(k).backgroundColor,
      friendsInTop: !!(top && /\d+ friends?/.test(top.innerText)), bd: C(bd) && C(bd).backgroundColor, nameInBd: !!(bd && bd.querySelector('.rm-t')), rows, code: b.dataset.x }; });
  ok(r && r.top === 'rgb(227, 236, 255)' && r.rows.every(c => c === r.top) && r.kc === 'rgb(30, 64, 175)' && r.kfs === '20px' && r.kbg === 'rgba(0, 0, 0, 0)' && r.k === r.code, 'recs: every card has a class-blue top (#E3ECFF) with the code large in #1E40AF', r);
  ok(r && r.friendsInTop && r.nameInBd && r.bd !== r.top, 'recs: friends in the blue top; the class name below it on white', r);
  ok(r && /^Classes your friends are taking Suggested$/.test(r.h) && r.tag === 'Suggested', 'recs: heading “Classes your friends are taking” with a “Suggested” tag', r);
  /* a full-page sheet over Home is light, so the band and strip go light with it (review fix) */
  await page.evaluate(() => openAddTo(Object.keys(SEC)[0])); await settle(page);
  const fs = await look();
  ok(fs.status === BG && fs.meta.every(m => m === '#F4F6FB'), 'deep: a full-page sheet over Home takes the light band and strip with it', fs);
  await page.evaluate(() => { UI.sheet = null; render(true); }); await settle(page);
  /* a second finger drops a pull (review fix) */
  const two = await page.evaluate(() => { const sc = document.getElementById('scroll'), T = (id, x, y) => new Touch({ identifier: id, target: sc, clientX: x, clientY: y });
    sc.dispatchEvent(new TouchEvent('touchstart', { touches: [T(1, 150, 200)], bubbles: true }));
    sc.dispatchEvent(new TouchEvent('touchmove', { touches: [T(1, 150, 260)], bubbles: true }));
    const mid = parseFloat(document.getElementById('hptr').style.height) || 0;
    sc.dispatchEvent(new TouchEvent('touchstart', { touches: [T(1, 150, 260), T(2, 250, 300)], bubbles: true }));
    sc.dispatchEvent(new TouchEvent('touchmove', { touches: [T(2, 250, 420)], bubbles: true }));
    const after = parseFloat(document.getElementById('hptr').style.height) || 0, y0 = PTR.y0;
    sc.dispatchEvent(new TouchEvent('touchend', { touches: [], bubbles: true })); return { mid, after, y0 }; });
  await settle(page, 900);
  ok(two.mid > 0 && two.after === 0 && two.y0 === null && !(await page.evaluate(() => PTR.busy)), 'swipe: a second finger during a pull drops it (no refresh)', two);
  /* signed out while on Home: the deep colour goes (review fix) */
  await page.evaluate(() => { TC.phase = 'signin'; render(); }); await settle(page);
  const so = await page.evaluate(() => ({ deep: document.documentElement.classList.contains('deep'), meta: [...document.querySelectorAll('meta[name=theme-color]')].map(m => m.content), phone: getComputedStyle(document.querySelector('.phone')).backgroundColor }));
  ok(!so.deep && so.meta.every(m => m === '#F4F6FB') && so.phone === BG, 'deep: the sign-in view is never deep', so);
  ok(log.errors.length === 0, 'deep: no page errors', log.errors);
  await close();
  /* dark mode: Home stays the dark page (deep is a light-mode look) */
  { const d = await openApp({ init: () => { try { localStorage.setItem('tc-theme', 'dark'); } catch (e) {} } });
    await d.page.waitForFunction(() => TC.ready && document.querySelectorAll('.hfeed .fcard').length === 5, null, { timeout: 8000 }); await settle(d.page, 300);
    const k = await d.page.evaluate(() => ({ th: document.documentElement.getAttribute('data-theme'), deep: document.documentElement.classList.contains('deep'), phone: getComputedStyle(document.querySelector('.phone')).backgroundColor, status: getComputedStyle(document.getElementById('status')).backgroundColor, body: getComputedStyle(document.body).backgroundColor, meta: [...document.querySelectorAll('meta[name=theme-color]')].map(m => m.content) }));
    const N = 'rgb(10, 15, 28)';
    ok(k.th === 'dark' && !k.deep && k.phone === N && k.status === N && k.body === N && k.meta.every(m => m === '#0A0F1C'), 'deep: in dark mode Home is the dark page, strip and page behind the clock one colour', k);
    const off = await d.page.evaluate(() => { TC.phase = 'offline'; render(); return { onb: !!document.querySelector('#scroll .onb'), meta: [...document.querySelectorAll('meta[name=theme-color]')].map(m => m.content), deep: document.documentElement.classList.contains('deep') }; });
    ok(!off.onb && !off.deep && off.meta.every(m => m === '#0A0F1C'), 'deep: in dark mode the offline screen keeps the dark strip (no light flash)', off);
    await d.close(); }
  /* Champ never covers the last thing on a page once you've scrolled to the end (Home: the last friend's week) */
  const o = await openApp({}); await o.page.waitForFunction(() => TC.ready && document.querySelectorAll('.hfeed .fcard').length === 5, null, { timeout: 8000 });
  const f = await o.page.evaluate(() => { const sc = document.getElementById('scroll'); sc.scrollTop = sc.scrollHeight; const sp = sc.querySelector('.spacer'), last = sp && sp.previousElementSibling, r = last.getBoundingClientRect(), fab = document.querySelector('.fab').getBoundingClientRect();
    return { scrolls: sc.scrollHeight > sc.clientHeight + 100, clear: r.bottom <= fab.top, b: [r.top, r.bottom], fab: [fab.top, fab.bottom], last: last.className }; });
  ok(f.scrolls && f.clear, 'fab: scrolled to the end, the last thing on Home sits above Champ', f);
  await o.close();
};

/* ============ A plan's day lists show the class names (Tate, 2026-10-04) ============ */
tests.agendaNames = async () => {
  const { page, close, log } = await openApp({});
  await page.waitForFunction(() => TC.ready && TC.seatsLoaded, null, { timeout: 8000 });
  await click(page, '[data-a="tab"][data-x="schedule"]'); await click(page, '[data-a="schedTab"][data-x="plans"]'); await click(page, '[data-a="pickPlan"][data-x="B"]');
  await page.waitForFunction(() => document.querySelectorAll('#scroll .agenda .arow').length > 0, null, { timeout: 8000 });
  const rows = () => page.evaluate(() => [...document.querySelectorAll('#scroll .agenda .arow')].map(r => { const cn = r.querySelector('.cn');
    return { code: r.dataset.x, want: courseName(r.dataset.x), cn: cn ? cn.textContent : null, h: cn ? cn.getBoundingClientRect().height : 0, fs: cn ? parseFloat(getComputedStyle(cn).fontSize) : 0,
      fit: r.getBoundingClientRect().right <= document.getElementById('scroll').getBoundingClientRect().right + 0.5 }; }));
  const a = await rows();
  ok(a.length > 0 && a.every(r => r.want ? r.cn === r.want : r.cn === null), 'names: every plan day row shows its class’s catalog name under the code', a);
  ok(a.some(r => r.cn), 'names: at least one row has a name (else this proves nothing)', a);
  ok(a.filter(r => r.cn).every(r => r.h > 0 && r.h <= r.fs * 1.5 && r.fit), 'names: a name stays on one line and inside the screen', a);
  const code = a[0].code;
  /* a long name (test-only text) still takes one line, cut with … */
  await page.evaluate(code => { const c = COURSES[code]; if (c) c.title = 'A Very Long Course Title That Could Never Fit On One Line Of A Phone'; else CAT_TITLE[code] = 'A Very Long Course Title That Could Never Fit On One Line Of A Phone'; render(true); }, code);
  const l = (await rows()).filter(r => r.code === code);
  ok(l.length > 0 && l.every(r => r.cn && r.h <= r.fs * 1.5 && r.fit), 'names: a long name stays on one line and inside the screen', l);
  /* a class we have no name for: the line is left out, nothing invented */
  const b = await page.evaluate(code => { const c = COURSES[code]; if (c) c.title = code; delete CAT_TITLE[code]; delete LIFTED_NAMES[code]; const f = flowNames(); if (f) delete f[code]; render(true);
    return [...document.querySelectorAll('#scroll .agenda .arow')].filter(r => r.dataset.x === code).map(r => [courseName(code), !!r.querySelector('.cn'), r.textContent]); }, code);
  ok(b.length > 0 && b.every(([n, has]) => n === '' && !has), 'names: a class with no known name shows just its code', b);
  ok(log.errors.length === 0, 'names: no page errors', log.errors);
  await close();
};

/* ============ A sideways swipe through the stories never pulls to refresh (Tate, 2026-10-04) ============ */
tests.pullSideways = async () => {
  const { page, close, log } = await openApp({});
  await page.waitForFunction(() => TC.ready && document.querySelectorAll('.story').length === 5, null, { timeout: 8000 });
  const loads = () => log.reads.filter(r => /^my_sections/.test(r)).length;
  /* a touch from (x,y) moving (dx,dy) in 6 steps; sl: how far the row scrolls along with it (the browser would) */
  const swipe = (sel, dx, dy, sl = 0) => page.evaluate(([sel, dx, dy, sl]) => {
    const el = document.querySelector(sel), r = el.getBoundingClientRect(), x = r.left + r.width / 2, y = r.top + 20, row = el.closest('.stories');
    const T = (a, b) => new Touch({ identifier: 1, target: el, clientX: a, clientY: b });
    el.dispatchEvent(new TouchEvent('touchstart', { touches: [T(x, y)], bubbles: true }));
    let maxH = 0;
    for (let k = 1; k <= 6; k++) { if (sl && row) row.scrollLeft = sl * k / 6;
      el.dispatchEvent(new TouchEvent('touchmove', { touches: [T(x + dx * k / 6, y + dy * k / 6)], bubbles: true }));
      maxH = Math.max(maxH, parseFloat(document.getElementById('hptr').style.height) || 0); }
    el.dispatchEvent(new TouchEvent('touchend', { touches: [], bubbles: true }));
    if (row) row.scrollLeft = 0;
    return maxH; }, [sel, dx, dy, sl]);
  const ov = await page.evaluate(() => { const r = document.querySelector('.stories'); return r.scrollWidth > r.clientWidth + 1; });
  ok(ov, 'swipe: the stories row scrolls sideways on a phone (else this test proves nothing)');
  let n0 = loads();
  let h = await swipe('.story:nth-child(3)', -120, 80); await settle(page, 900);
  ok(loads() === n0 && h === 0, 'swipe: left through the stories with the finger drifting down 80px does not refresh (or even tug)', { h, n0, n1: loads() });
  h = await swipe('.story:nth-child(3)', -50, 110, 60); await settle(page, 900);
  ok(loads() === n0, 'swipe: once the stories row has scrolled, the touch is a swipe, however far down it drifts', { h });
  h = await swipe('.story:nth-child(3)', -70, 100); await settle(page, 900);
  ok(loads() === n0, 'swipe: on the stories a slanted pull (less than twice as much down as sideways) is still a swipe', { h });
  h = await swipe('.story:nth-child(2)', 12, 130); await settle(page, 1500);
  ok(loads() > n0, 'swipe: pulling straight down from a story still refreshes', { h, n0, n1: loads() });
  await page.waitForFunction(() => !PTR.busy, null, { timeout: 8000 }); await settle(page, 400);
  /* off the stories: down beats sideways */
  n0 = loads();
  h = await swipe('.recs, .feed, #hptr + *', -120, 90); await settle(page, 900);
  ok(loads() === n0, 'swipe: anywhere on Home, more sideways than down is not a pull', { h });
  h = await swipe('.recs, .feed, #hptr + *', -60, 130); await settle(page, 1500);
  ok(loads() > n0, 'swipe: off the stories, a pull mostly down still refreshes', { h, n0, n1: loads() });
  ok(log.errors.length === 0, 'swipe: no page errors', log.errors);
  await close();
};

/* ============ Pull to refresh shuffles the feed; the spinner sits under the stories (Tate, 2026-10-04) ============ */
const pullOn = (page, dy, end = true) => page.evaluate(([dy, end]) => { const sc = document.getElementById('scroll');
  const T = y => new Touch({ identifier: 1, target: sc, clientX: 150, clientY: y });
  sc.dispatchEvent(new TouchEvent('touchstart', { touches: [T(120)], bubbles: true }));
  for (let k = 1; k <= 5; k++) sc.dispatchEvent(new TouchEvent('touchmove', { touches: [T(120 + dy * k / 5)], bubbles: true }));
  if (end) sc.dispatchEvent(new TouchEvent('touchend', { touches: [], bubbles: true })); }, [dy, end]);
tests.refreshShuffle = async () => {
  const { page, close, log } = await openApp({});
  await page.waitForFunction(() => TC.ready && document.querySelectorAll('.hfeed .fcard').length === 5, null, { timeout: 8000 });
  const dom = () => page.evaluate(() => [...document.querySelectorAll('.hfeed .fcard')].map(c => c.id.slice(3)));
  let st = await page.evaluate(() => ({ order: feedOrder(), friends: TC.friends.slice() }));
  ok(JSON.stringify(await dom()) === JSON.stringify(st.order) && st.order.slice().sort().join() === st.friends.slice().sort().join(), 'refresh: the feed draws every friend once, in feedOrder()', st);
  /* mid-pull: the gap opens between the stories and the feed, with the spinner in it */
  await pullOn(page, 120, false); await page.waitForTimeout(300);
  const g = await page.evaluate(() => { const h = document.getElementById('hptr'), r = h.getBoundingClientRect(), s = document.querySelector('.stories').getBoundingClientRect(), c = document.querySelector('.hfeed .fcard').getBoundingClientRect(), sp = h.querySelector('.tc-spin').getBoundingClientRect();
    return { prev: h.previousElementSibling && h.previousElementSibling.className, next: h.nextElementSibling && h.nextElementSibling.className, h: r.height, spinMid: sp.top + sp.height / 2, storiesBottom: s.bottom, cardTop: c.top, op: getComputedStyle(h.querySelector('.tc-spin')).opacity, old: !!document.getElementById('ptr') }; });
  ok(g.prev === 'stories' && /^hfeed/.test(g.next) && g.h >= 40 && g.spinMid > g.storiesBottom && g.spinMid < g.cardTop && +g.op > 0.9 && !g.old, 'refresh: pulling opens a gap between the stories and the feed, with the spinner in it (no floating spinner)', g);
  await page.evaluate(() => document.getElementById('scroll').dispatchEvent(new TouchEvent('touchend', { touches: [], bubbles: true })));
  await page.clock.runFor(100);
  ok(await page.evaluate(() => PTR.busy && document.getElementById('hptr').classList.contains('spin') && document.getElementById('hptr').getBoundingClientRect().height > 40), 'refresh: while it loads the spinner turns in the gap');
  for (let round = 0; round < 3; round++) {
    const before = await dom();
    if (round) await pullOn(page, 120);
    await settle(page, 1500); await settle(page, 1500);
    const after = await dom(), fo = await page.evaluate(() => UI.feedOrder);
    ok(JSON.stringify(after) === JSON.stringify(fo) && after.length === 5 && after.slice().sort().join() === before.slice().sort().join() && !after.slice(0, 2).some(id => before.slice(0, 2).includes(id)), `refresh ${round + 1}: the feed is reshuffled and the two cards that were on top aren’t on top again`, { before, after });
    ok(await page.evaluate(() => !PTR.busy && document.getElementById('hptr').getBoundingClientRect().height === 0 && !document.querySelector('.hfeed.fin, .hfeed.fout')), `refresh ${round + 1}: the gap closes and the cards settle`);
  }
  const prop = await page.evaluate(() => { const bad = []; for (let n = 1; n <= 7; n++) { const ids = Array.from({ length: n }, (_, i) => 'f' + i); let prev = ids.slice(), firsts = new Set();
    for (let t = 0; t < 300; t++) { const nx = reshuffle(prev, ids), k = Math.min(2, Math.floor(n / 2));
      if (nx.length !== n || nx.slice().sort().join() !== ids.slice().sort().join()) bad.push(['perm', n, nx]);
      if (nx.slice(0, k).some(id => prev.slice(0, k).includes(id))) bad.push(['top', n, prev, nx]);
      firsts.add(nx[0]); prev = nx; }
    if (n >= 3 && firsts.size < n) bad.push(['every friend leads sometimes', n, firsts.size]); }
    return bad.slice(0, 3); });
  ok(prop.length === 0, 'refresh: a reshuffle is always a full reshuffle of everyone, never with the old top on top, and anyone can come first', prop);
  /* the cards rise in, then the class is gone */
  await pullOn(page, 120); await page.clock.runFor(700); await page.waitForTimeout(150); await page.clock.runFor(50); await page.waitForTimeout(100);
  ok(await page.evaluate(() => !!document.querySelector('.hfeed.fin')), 'refresh: the new cards animate in');
  await settle(page, 1200);
  ok(log.errors.length === 0, 'refresh: no page errors', log.errors);
  await close();
  /* a refresh that fails says so and keeps the order you were looking at */
  let down = null;
  const o2 = await openApp({ hook: url => down && url.pathname === down ? { status: 500, body: JSON.stringify({ message: 'down' }) } : null });   /* 500: supabase-js retries a 503 on a timer */
  await o2.page.waitForFunction(() => TC.ready && document.querySelectorAll('.hfeed .fcard').length === 5, null, { timeout: 8000 });
  for (const [path, re] of [['/rest/v1/profiles', /^Couldn’t refresh/], ['/rest/v1/friend_requests', /^Couldn’t load your friends — pull/]]) {
    const was = await o2.page.evaluate(() => UI.feedOrder.slice()); down = path;
    await pullOn(o2.page, 120); await settle(o2.page, 1500); await settle(o2.page, 800);
    const r = await o2.page.evaluate(() => ({ order: UI.feedOrder.slice(), toast: document.getElementById('toast').textContent, busy: PTR.busy, gap: document.getElementById('hptr').getBoundingClientRect().height }));
    ok(JSON.stringify(r.order) === JSON.stringify(was) && re.test(r.toast) && !r.busy && r.gap === 0, `refresh: when ${path.split('/').pop()} can’t load, it says so and doesn’t pretend to have refreshed`, r);
    down = null;
  }
  ok(await o2.page.evaluate(() => document.getElementById('toast').getAttribute('role')) === 'status', 'refresh: the toast is announced (role=status)');
  await o2.close();
  /* reduced motion: no fade and no rise, the order still changes */
  const o3 = await openApp({});
  await o3.page.emulateMedia({ reducedMotion: 'reduce' });
  await o3.page.waitForFunction(() => TC.ready && document.querySelectorAll('.hfeed .fcard').length === 5, null, { timeout: 8000 });
  await o3.page.evaluate(() => { window.__anim = 0; new MutationObserver(() => { if (document.querySelector('.hfeed.fin, .hfeed.fout')) window.__anim++; }).observe(document.getElementById('scroll'), { subtree: true, childList: true, attributes: true }); });
  const w3 = await o3.page.evaluate(() => UI.feedOrder.slice());
  await pullOn(o3.page, 120); await settle(o3.page, 1500); await settle(o3.page, 800);
  const r3 = await o3.page.evaluate(() => ({ anim: window.__anim, order: UI.feedOrder.slice() }));
  ok(r3.anim === 0 && JSON.stringify(r3.order) !== JSON.stringify(w3), 'refresh: with Reduce Motion on it reshuffles without the fade or the rise', r3);
  await o3.close();
};

/* ============ Schedule: Share top right, like a professor's page (Tate, 2026-10-04, 19:40) ============ */
tests.shareTop = async () => {
  const { page, close, log } = await openApp({});
  await page.waitForFunction(() => TC.ready && TC.seatsLoaded, null, { timeout: 8000 });
  await click(page, '[data-a="tab"][data-x="schedule"]');
  const where = () => page.evaluate(() => { const sc = document.getElementById('scroll').getBoundingClientRect(), t = document.querySelector('#scroll .schhdr .title'), b = document.querySelector('#scroll .schhdr .schshare'), g = document.querySelector('#scroll .grid'), c = g && g.closest('.card'), bars = [...document.querySelectorAll('#scroll .regbar')], bar = bars[0];
    const tr = t && t.getBoundingClientRect(), br = b && b.getBoundingClientRect();
    return { btn: b ? { x: b.dataset.x, label: b.getAttribute('aria-label'), right: Math.round(sc.right - br.right), mid: Math.round(Math.abs((br.top + br.bottom) / 2 - (tr.top + tr.bottom) / 2)), size: Math.round(br.width), round: getComputedStyle(b).borderRadius } : null,
      bars: bars.length, barText: bar ? bar.innerText.replace(/\s+/g, ' ').trim() : null, barAfter: !!(c && bar && c.nextElementSibling === bar), gap: c && bar ? Math.round(bar.getBoundingClientRect().top - c.getBoundingClientRect().bottom) : null, barL: bar ? Math.round(bar.getBoundingClientRect().left - sc.left) : null, oldShare: document.querySelectorAll('#scroll .shbtn').length }; });
  const mine = await where();
  ok(mine.btn && mine.btn.x === 'mine' && mine.btn.label === 'Share your week' && mine.btn.right === 16 && mine.btn.mid <= 2 && mine.btn.size === 44 && mine.btn.round === '50%', 'share top: My Classes’ Share is the round button top right, level with “Schedule”', mine);
  ok(mine.bars === 0 && mine.oldShare === 0, 'share top: no Share bar under My Classes’ week any more', mine);
  /* its colour is the colour of what it shares — the same as the chip that's on (Tate, 20:00) */
  const col = () => page.evaluate(() => { const b = document.querySelector('#scroll .schhdr .schshare'), on = document.querySelector('#scroll .seg.terms button.on, #scroll .seg.plans button.on'), cs = getComputedStyle(b);
    return { bg: cs.backgroundColor, fg: cs.color, chip: on ? getComputedStyle(on).backgroundColor : null, svg: getComputedStyle(b.querySelector('svg')).color }; });
  const cm = await col();
  ok(cm.bg === 'rgb(37, 99, 235)' && cm.bg === cm.chip && cm.fg === 'rgb(255, 255, 255)', 'share top: on My Classes it is filled My Classes blue, like the Fall chip, with a white arrow', cm);
  await click(page, '[data-a="schedTab"][data-x="plans"]');
  await page.evaluate(() => { TC.plans.A = personSecs('me').map(s => s.id); S.plan = 'A'; render(true); }); await settle(page, 300);
  const pl = await where();
  ok(pl.btn && pl.btn.x === 'A' && pl.btn.label === 'Share Plan A' && pl.btn.right === 16, 'share top: on Plans it shares the open plan', pl);
  const ca = await col();
  ok(ca.bg === 'rgb(15, 118, 110)' && ca.fg === 'rgb(255, 255, 255)', 'share top: on Plan A it turns Plan A’s teal', ca);
  ok(pl.bars === 1 && pl.barAfter && pl.barL === 14 && pl.gap >= 6 && pl.gap <= 14 && /^(Friends can see|Only you)$/.test(pl.barText) && pl.oldShare === 0, 'share top: a plan keeps “Friends can see” under its week, alone', pl);
  await click(page, '[data-a="pickPlan"][data-x="C"]');
  ok((await where()).btn.x === 'C', 'share top: switching plan switches what it shares');
  const cc = await col();
  ok(cc.bg === 'rgb(190, 24, 93)' && cc.fg === 'rgb(255, 255, 255)', 'share top: on Plan C it turns Plan C’s rose', cc);
  await click(page, '[data-a="pickPlan"][data-x="B"]');
  const cb = await col(); await click(page, '[data-a="pickPlan"][data-x="C"]');
  ok(cb.bg === 'rgb(194, 65, 12)' && cb.bg === cb.chip && cb.fg === 'rgb(255, 255, 255)', 'share top: on Plan B it turns Plan B’s orange', cb);
  await click(page, '#scroll .schhdr .schshare');
  ok(await page.evaluate(() => UI.sheet && UI.sheet.type === 'share' && UI.share && UI.share.plan === 'C'), 'share top: tapping it opens the share sheet for that plan');
  await click(page, '#sheet .xbtn');
  await click(page, '[data-a="schedTab"][data-x="planner"]');
  ok((await where()).btn === null, 'share top: Planner has nothing to share and shows no button');
  ok(log.errors.length === 0, 'share top: no page errors', log.errors);
  await close();
};

/* ============ Share a professor or a class by iMessage, with a picture (Tate, 2026-10-04, 19:40) ============ */
const cardReady = page => page.waitForFunction(() => UI.card && UI.card.ln && ['ready', 'err'].includes(UI.card.ln.state), null, { timeout: 8000 });
tests.shareProfClass = async () => {
  let hold = null;
  const hook = (url, m) => /\/storage\/v1\/object\//.test(url.pathname) && hold ? hold : null;
  const { page, close, log } = await openApp({ init: SHARE_INIT, hook });
  await page.waitForFunction(() => TC.ready && TC.seatsLoaded && TC.profsLoaded, null, { timeout: 8000 });
  await page.evaluate(() => A.openProf('ada examplewood')); await settle(page, 400);
  await click(page, '.topbtns [data-a="sendCard"]');
  await cardReady(page); await settle(page);
  const sh = (await page.locator('#sheet').innerText()).replace(/\s+/g, ' ');
  ok(/Share Ada Examplewood/.test(sh) && /Send a link/.test(sh) && /shows this picture and “Jordan shared a professor”/.test(sh) && /Send to a friend in TermChamp/.test(sh), 'share prof: the sheet — picture, Send a link, what iMessage shows, then send in TermChamp', sh.slice(0, 400));
  const order = await page.evaluate(() => { const s = document.getElementById('sheet'), a = s.querySelector('.shimg'), b = s.querySelector('[data-a="cardLink"]'), c = s.querySelector('[data-a="cardTo"], [data-a="cardToThread"]'); return !!(a && b && c && (a.compareDocumentPosition(b) & 4) && (b.compareDocumentPosition(c) & 4)); });
  ok(order, 'share prof: picture, then Send a link, then the friends');
  const w = shareWrites(log), id = w.length === 1 && /storage:schedule-cards\/([0-9a-f]{32})\.png$/.exec(w[0].table);
  ok(id && w[0].upsert !== 'true' && w[0].bytes > 15000 && id[1] !== FX.ME.id.replace(/-/g, ''), 'share prof: one picture goes up, insert only, under a random name — nothing else', w.map(x => [x.table, x.bytes, x.ctype, x.upsert]));
  const img = await page.evaluate(() => new Promise(r => { const i = document.querySelector('#sheet .shimg'); const f = () => r([i.naturalWidth, i.naturalHeight, i.alt]); if (i.complete) f(); else i.onload = f; }));
  ok(img[0] === 1200 && img[1] === 630 && /^Ada Examplewood · BUS · 4\.5 out of 5 from 41 ratings$/.test(img[2]), 'share prof: a 1200×630 picture of their real rating and count', img);
  /* the picture's own pixels: the rating circle is the rating's colour, not something invented */
  const px = await page.evaluate(() => new Promise(r => { const i = document.querySelector('#sheet .shimg'); const c = document.createElement('canvas'); c.width = 1200; c.height = 630; const g = c.getContext('2d'); g.drawImage(i, 0, 0); const d = g.getImageData(150, 300, 1, 1).data; const t = profTone(ratingOf('ada examplewood')); const e = document.createElement('i'); e.style.color = t.bg; document.body.appendChild(e); const want = getComputedStyle(e).color; e.remove(); r([`rgb(${d[0]}, ${d[1]}, ${d[2]})`, want]); }));
  ok(px[0] === px[1], 'share prof: the picture’s circle is their rating’s colour', px);
  const sync = await page.evaluate(() => { document.querySelector('#sheet [data-a="cardLink"]').click(); return (window.__shared || []).length; });
  await settle(page);
  const shared = await page.evaluate(() => window.__shared);
  ok(sync === 1 && shared[0].url === `https://termchamp.com/s?k=p&i=${id && id[1]}.png&nm=Jordan&p=ada-examplewood` && !shared[0].text, 'share prof: Send a link opens the share sheet in the tap, with one bare /s link (k first, so a chat never reads it as a shared week)', shared);
  ok(await page.evaluate(u => !shMsg({ kind: 'text', body: 'look ' + u }), shared[0].url), 'share prof: pasted into a chat, the link is not mistaken for a shared week');
  /* again: same picture, no second upload */
  await click(page, '#sheet .xbtn'); await click(page, '.topbtns [data-a="sendCard"]'); await cardReady(page);
  ok(shareWrites(log).length === 1 && await page.evaluate(() => UI.card.ln.link) === shared[0].url, 'share prof: opening it again reuses the link and uploads nothing');
  await click(page, '#sheet .xbtn');
  /* a class */
  await page.evaluate(() => A.openClass('BUS 3438')); await settle(page, 400);
  await click(page, '.topbtns [data-a="sendCard"]'); await cardReady(page); await settle(page);
  const ci = await page.evaluate(() => new Promise(r => { const i = document.querySelector('#sheet .shimg'); const f = () => r([i.naturalWidth, i.naturalHeight, i.alt]); if (i.complete) f(); else i.onload = f; }));
  const cl = await page.evaluate(() => UI.card.ln.link);
  ok(ci[0] === 1200 && ci[1] === 630 && /^BUS 3438 · Financial Markets · Fall 2026 · 1 section · Bram Fixturesen 3\.6$/.test(ci[2]) && /^https:\/\/termchamp\.com\/s\?k=c&i=[0-9a-f]{32}\.png&nm=Jordan&c=BUS%203438$/.test(cl), 'share class: its own picture and a k=c link to the class', { ci, cl });
  ok(/Share BUS 3438/.test(await page.locator('#sheet').innerText()) && /“Jordan shared a class”/.test(await page.locator('#sheet').innerText()), 'share class: the sheet says what iMessage will show');
  await click(page, '#sheet .xbtn');
  /* not ready yet → disabled; a refused upload says so and can be retried */
  hold = { status: 403, body: JSON.stringify({ statusCode: '403', error: 'Unauthorized', message: 'new row violates row-level security policy' }) };
  await page.evaluate(() => A.openProf('bram fixturesen')); await settle(page, 300);
  await click(page, '.topbtns [data-a="sendCard"]'); await cardReady(page); await settle(page);
  ok(await page.evaluate(() => UI.card.ln.state) === 'err' && await page.locator('#sheet [data-a="cardLink"][disabled]').count() === 1 && /Couldn’t get the link ready/.test(await page.locator('#sheet').innerText()), 'share prof: a refused upload keeps Send a link off and says so');
  hold = null;
  await click(page, '#sheet [data-a="cardLinkRetry"]'); await cardReady(page); await settle(page);
  ok(await page.evaluate(() => UI.card.ln.state) === 'ready' && await page.locator('#sheet [data-a="cardLink"]:not([disabled])').count() === 1, 'share prof: Try again gets it ready');
  /* the in-app card still sends */
  await click(page, '#sheet [data-a="cardTo"]'); await settle(page, 500);
  ok(log.writes.some(x => x.table === 'messages' && x.body && x.body.kind === 'professor'), 'share prof: sending it to a friend in TermChamp still works');
  ok(log.errors.length === 0, 'share prof: no page errors', log.errors);
  await close();
};
tests.shareNoRatingsYet = async () => {
  /* PolyRatings fails: no picture is drawn or sent with a blank or invented rating; it says why */
  const { page, close, log } = await openApp({ init: SHARE_INIT, poly: null });
  await page.waitForFunction(() => TC.ready && TC.seatsLoaded, null, { timeout: 8000 });
  await page.evaluate(() => { TC.profsLoaded = false; TC.err.poly = true; A.openClass('BUS 3438'); }); await settle(page, 300);
  await click(page, '.topbtns [data-a="sendCard"]'); await page.waitForFunction(() => UI.card && UI.card.ln && UI.card.ln.state === 'err', null, { timeout: 8000 }); await settle(page);
  ok(shareWrites(log).length === 0 && await page.locator('#sheet [data-a="cardLink"][disabled]').count() === 1 && /Ratings didn’t load/.test(await page.locator('#sheet').innerText()), 'share: with ratings not loaded, nothing is drawn or uploaded and it says why', shareWrites(log).map(x => x.table));
  ok(log.errors.length === 0, 'share no ratings: no page errors', log.errors);
  await close();
};
tests.shareDeepLink = async () => {
  let o = await openApp({ search: '?p=ada-examplewood' });
  await o.page.waitForFunction(() => TC.ready && TC.profsLoaded, null, { timeout: 8000 }); await settle(o.page, 400);
  ok(await o.page.evaluate(() => cur().s === 'profDetail' && cur().p.id === 'ada examplewood' && location.search === ''), 'deep link: ?p= opens that professor, and the address is cleaned', await o.page.evaluate(() => [cur().s, cur().p, location.search]));
  await o.close();
  o = await openApp({ search: '?c=BUS%203438' });
  await o.page.waitForFunction(() => TC.ready && TC.seatsLoaded, null, { timeout: 8000 }); await settle(o.page, 400);
  ok(await o.page.evaluate(() => cur().s === 'classDetail' && cur().p.code === 'BUS 3438'), 'deep link: ?c= opens that class', await o.page.evaluate(() => [cur().s, cur().p]));
  await o.page.reload({ waitUntil: 'domcontentloaded' }); await o.page.clock.runFor(2500); await settle(o.page, 400);
  ok(await o.page.evaluate(() => cur().s !== 'classDetail'), 'deep link: it opens once, not again on the next visit');
  await o.close();
  o = await openApp({ search: '?p=nobody-real' });
  await o.page.waitForFunction(() => TC.ready && TC.profsLoaded, null, { timeout: 8000 }); await settle(o.page, 400);
  ok(await o.page.evaluate(() => cur().s !== 'profDetail') && /Couldn’t find that professor/.test(await toastText(o.page)), 'deep link: a professor it can’t find says so');
  await o.close();
  o = await openApp({ search: '?p=constructor' });
  await o.page.waitForFunction(() => TC.ready && TC.profsLoaded, null, { timeout: 8000 }); await settle(o.page, 400);
  ok(await o.page.evaluate(() => cur().s !== 'profDetail') && /Couldn’t find that professor/.test(await toastText(o.page)), 'deep link: a built-in name like “constructor” is not a professor');
  await o.close();
  /* signed out: kept through signing in */
  o = await openApp({ search: '?c=BUS%203438', signedIn: false });
  ok(await o.page.evaluate(() => sessionStorage.getItem('tc-dl')) === JSON.stringify({ p: '', c: 'BUS 3438' }) && await o.page.evaluate(() => location.search === ''), 'deep link: signed out, it waits for you to sign in');
  ok(o.log.errors.length === 0, 'deep link: no page errors', o.log.errors);
  await o.close();
};

/* ============ No password sheet over the searches (Tate, 2026-10-04, 20:30) ============ */
tests.searchNoAutofill = async () => {
  const { page, close, log } = await openApp({});
  await page.waitForFunction(() => TC.ready, null, { timeout: 8000 });
  await click(page, '[data-a="tab"][data-x="friends"]');
  const a = await page.evaluate(() => { const i = document.getElementById('fq'); return { ph: i.placeholder, al: i.getAttribute('aria-label'), ty: i.type, ac: i.getAttribute('autocomplete'), op: i.hasAttribute('data-1p-ignore') && i.getAttribute('data-lpignore') === 'true' && i.getAttribute('data-form-type') === 'other' }; });
  ok(!/user\s*name/i.test(a.ph + ' ' + a.al) && /@handle/.test(a.ph) && a.ty === 'search' && a.ac === 'off' && a.op, 'search: the Friends search never says “username” (iOS reads that as a sign-in field) and opts out of password managers', a);
  await page.evaluate(() => { UI.sheet = { type: 'addFriend' }; render(true); }); await tick(page, 300);
  const b = await page.evaluate(() => { const i = document.getElementById('pq'); return i ? { ph: i.placeholder, ty: i.type, ac: i.getAttribute('autocomplete'), op: i.hasAttribute('data-1p-ignore') } : null; });
  ok(b && !/user\s*name/i.test(b.ph) && b.ty === 'search' && b.ac === 'off' && b.op, 'search: the add-friend search too', b);
  ok(log.errors.length === 0, 'search: no page errors', log.errors);
  await close();
};
/* ============ A class's and a professor's page at Home's width (Tate, 2026-10-04, 20:30) ============ */
tests.classProfWidth = async () => {
  const { page, close, log } = await openApp({});
  await page.waitForFunction(() => TC.ready && TC.seatsLoaded && TC.profsLoaded, null, { timeout: 8000 });
  const m = () => page.evaluate(() => { const sc = document.getElementById('scroll').getBoundingClientRect(), L = e => Math.round(e.getBoundingClientRect().left - sc.left), R = e => Math.round(sc.right - e.getBoundingClientRect().right);
    const cards = [...document.querySelectorAll('#scroll > * .hero, #scroll .hero, #scroll .card')].filter(e => e.offsetParent);
    const rows = [...document.querySelectorAll('#scroll .secrow')].map(r => { const card = r.closest('.card'), t = r.querySelector('.nw'), lines = t ? t.getClientRects().length : 0; return { inL: Math.round(r.getBoundingClientRect().left - card.getBoundingClientRect().left), inR: Math.round(card.getBoundingClientRect().right - r.getBoundingClientRect().right), split: lines > 1, txt: t && t.textContent }; });
    return { edges: [...new Set(cards.map(e => L(e) + '/' + R(e)))], rows }; });
  await page.evaluate(() => A.openClass('BUS 3431')); await settle(page, 400);
  const c = await m();
  ok(c.edges.length === 1 && c.edges[0] === '12/12', 'width: a class page’s hero and cards sit 12px from the screen edge, like Home and Schedule', c.edges);
  ok(c.rows.length > 0 && c.rows.every(r => r.inL === 8 && r.inR === 8), 'width: section rows sit 8px inside their card (was 12)', c.rows);
  ok(c.rows.every(r => !r.split), 'width: a section’s time never splits over two lines', c.rows);
  await page.setViewportSize({ width: 320, height: 740 }); await settle(page, 300);
  const n = await m();
  ok(n.rows.every(r => !r.split), 'width: even at 320px the time moves as a whole instead of splitting', n.rows);
  await page.setViewportSize({ width: 390, height: 844 });
  await page.evaluate(() => A.openProf('ada examplewood')); await settle(page, 400);
  const p = await m();
  ok(p.edges.length === 1 && p.edges[0] === '12/12', 'width: a professor’s page too', p.edges);
  ok(log.errors.length === 0, 'width: no page errors', log.errors);
  await close();
};

/* ============ Pull to refresh with a trackpad or wheel — the Desktop preview (Tate, 2026-10-04) ============ */
tests.pullWheel = async () => {
  const { page, close, log } = await openApp({ width: 390 });
  await page.waitForFunction(() => TC.ready && document.querySelectorAll('.hfeed .fcard').length === 5, null, { timeout: 8000 });
  const loads = () => log.reads.filter(r => /^my_sections/.test(r)).length;
  const swipe = async (dys, at = 420) => { await page.mouse.move(195, at); for (const d of dys) await page.mouse.wheel(0, d); };
  const gap = () => page.evaluate(() => Math.round(document.getElementById('hptr').getBoundingClientRect().height));
  /* the gap closes with a 0.3s CSS transition, which runs on real time */
  const shut = () => page.waitForFunction(() => document.getElementById('hptr').getBoundingClientRect().height === 0, null, { timeout: 2000 }).then(() => true, () => false);
  /* a two-finger swipe down at the top of Home opens the gap, then refreshes and reshuffles */
  let n0 = loads(); const before = await page.evaluate(() => UI.feedOrder.slice(0, 2));
  await swipe([-40, -40, -40, -40]);
  const mid = await gap();
  ok(mid >= 30, 'wheel: a trackpad swipe down at the top opens the gap under the stories', mid);
  await page.clock.runFor(250); await settle(page, 1500); await settle(page, 800);
  const after = await page.evaluate(() => UI.feedOrder.slice(0, 2));
  ok(loads() > n0 && !after.some(id => before.includes(id)) && await shut(), 'wheel: letting go past the line refreshes and reshuffles, and the gap closes', { n0, n1: loads(), before, after });
  /* a short nudge closes without refreshing */
  n0 = loads(); await swipe([-20, -20]); await page.clock.runFor(250); await settle(page, 600);
  ok(loads() === n0 && await shut(), 'wheel: a short nudge springs back without refreshing', { n0, n1: loads(), gap: await gap(), st: await page.evaluate(() => [PTR.y0, PTR.dy, PTR.busy, document.getElementById('hptr').style.height, document.getElementById('hptr').className]) });
  /* scrolling back up to the top never pulls: the gesture began below the top */
  await page.evaluate(() => { document.getElementById('scroll').scrollTop = 120; });
  n0 = loads(); await swipe([-60, -60, -60, -60, -60, -60]); await page.clock.runFor(250); await settle(page, 600);
  ok(loads() === n0 && await shut(), 'wheel: momentum from scrolling up the feed doesn’t refresh (the swipe has to start at the top)', { n0, n1: loads(), top: await page.evaluate(() => document.getElementById('scroll').scrollTop) });
  /* scrolling down at the top just scrolls */
  await page.evaluate(() => { document.getElementById('scroll').scrollTop = 0; }); await page.clock.runFor(300);
  n0 = loads(); await swipe([40, 40]); await page.clock.runFor(250); await settle(page, 600);
  ok(loads() === n0 && await shut(), 'wheel: scrolling down the feed doesn’t pull');
  /* only on Home */
  await page.evaluate(() => { document.getElementById('scroll').scrollTop = 0; }); await click(page, '[data-a="tab"][data-x="explore"]'); await page.clock.runFor(300);
  n0 = loads(); await swipe([-40, -40, -40, -40]); await page.clock.runFor(250); await settle(page, 600);
  ok(loads() === n0, 'wheel: only on Home');
  await click(page, '[data-a="tab"][data-x="home"]'); await page.evaluate(() => { document.getElementById('scroll').scrollTop = 0; }); await page.clock.runFor(300);
  const wh = (list) => page.evaluate(list => { const sc = document.getElementById('scroll'); list.forEach(o => sc.dispatchEvent(new WheelEvent('wheel', Object.assign({ bubbles: true, deltaMode: 0 }, o)))); }, list);
  const quiet = async () => { await page.clock.runFor(250); await settle(page, 600); };
  /* pinch-zoom on a trackpad is ctrl + wheel: never a pull */
  n0 = loads(); await wh([1, 2, 3, 4, 5].map(() => ({ deltaY: -60, ctrlKey: true }))); await quiet();
  ok(loads() === n0 && await shut(), 'wheel: a pinch (ctrl + wheel) at the top doesn’t refresh');
  /* a sideways swipe along the stories with a little vertical drift */
  n0 = loads(); await wh([1, 2, 3, 4, 5, 6].map(() => ({ deltaX: 80, deltaY: -30 }))); await quiet();
  ok(loads() === n0 && await shut(), 'wheel: a sideways swipe (the stories row) doesn’t refresh');
  /* one notch of a mouse wheel is not enough on its own */
  n0 = loads(); await wh([{ deltaY: -100 }]); await quiet();
  ok(loads() === n0 && await shut(), 'wheel: one mouse-wheel notch up at the top doesn’t refresh');
  /* a second gesture after a pause starts fresh and can refresh */
  n0 = loads(); await wh([{ deltaY: -20 }]); await page.clock.runFor(300); await wh([{ deltaY: -80 }, { deltaY: -80 }]); await quiet(); await settle(page, 1500);
  ok(loads() > n0, 'wheel: a new swipe after a pause pulls on its own', { n0, n1: loads() });
  await settle(page, 800);
  /* a touch pull in progress isn't hijacked by a stray wheel event */
  n0 = loads();
  await page.evaluate(() => { const sc = document.getElementById('scroll'), T = y => new Touch({ identifier: 1, target: sc, clientX: 150, clientY: y });
    sc.dispatchEvent(new TouchEvent('touchstart', { touches: [T(120)], bubbles: true })); sc.dispatchEvent(new TouchEvent('touchmove', { touches: [T(240)], bubbles: true })); });
  await page.clock.runFor(300); await wh([{ deltaY: -10 }]);
  await page.evaluate(() => document.getElementById('scroll').dispatchEvent(new TouchEvent('touchend', { touches: [], bubbles: true })));
  await quiet(); await settle(page, 1500);
  ok(loads() > n0, 'wheel: a wheel event during a finger pull doesn’t take it over (the pull still refreshes)', { n0, n1: loads() });
  ok(log.errors.length === 0, 'wheel: no page errors', log.errors);
  await close();
};

/* ============ Classes your friends are taking, between friends' weeks (Tate, 2026-10-04, option C) ============ */
tests.feedRecs = async () => {
  const { page, close, log } = await openApp({});
  await page.waitForFunction(() => TC.ready && document.querySelectorAll('.hfeed .fcard').length === 5 && TC.myHistory !== undefined, null, { timeout: 8000 });
  /* the expected list, worked out here from the raw data rather than by the app's function */
  const exp = () => page.evaluate(() => { const mine = myCodes(), took = new Set((TC.myHistory || []).map(h => String(h.code).toUpperCase().replace(/\s+/g, ' ').trim())), n = {};
    TC.friends.forEach(f => new Set(personSecs(f).map(x => x.code).concat(PEOPLE[f].unplaced || [])).forEach(c => { if (c && !mine.has(c) && !took.has(c)) n[c] = (n[c] || 0) + 1; }));
    return Object.entries(n).sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0])).slice(0, 8); });
  const got = () => page.evaluate(() => { const r = document.querySelector('.hfeed .recs'); if (!r) return null; const kids = [...document.querySelector('.hfeed').children];
    return { at: kids.indexOf(r), cards: [...r.querySelectorAll('.rmini')].map(b => [b.dataset.x, +(/(\d+) friends?/.exec(b.innerText) || [])[1], b.querySelector('.rchip') ? b.querySelector('.rchip').innerText.replace(/\s+/g, ' ').trim() : null, b.querySelector('.rm-t') ? b.querySelector('.rm-t').innerText : null]), label: r.querySelector('.recs-h').innerText }; });
  /* two friends share one class, so "most friends first" has something to order */
  await page.evaluate(() => { [TC.friends[0], TC.friends[3]].forEach(f => { PEOPLE[f].unplaced = (PEOPLE[f].unplaced || []).concat(['MATH 1001']); }); render(true); }); await settle(page, 200);
  let e = await exp(), g = await got();
  ok(g && g.cards[0] && g.cards[0][0] === 'MATH 1001' && g.cards[0][1] === 2, 'recs: a class two friends are in comes first, “2 friends”', g && g.cards[0]);
  ok(g && g.at === 3 && /^classes your friends are taking\s*suggested$/i.test(g.label.trim()), 'recs: one labelled “Suggested” row, right after the third friend’s week', g);
  ok(g && e.length > 0 && JSON.stringify(g.cards.map(c => [c[0], c[1]])) === JSON.stringify(e), 'recs: the classes friends are in that you aren’t in and haven’t taken, most friends first, with the right friend counts', { got: g && g.cards, exp: e });
  const mine = await page.evaluate(() => [...myCodes()]), hist = await page.evaluate(() => (TC.myHistory || []).map(h => h.code));
  ok(g && !g.cards.some(c => mine.includes(c[0]) || hist.includes(c[0])) && hist.length > 0, 'recs: never a class you’re in or one on your record', { mine, hist });
  const chips = await page.evaluate(() => [...document.querySelectorAll('.recs .rmini')].map(b => { const r = friendClassRecs().find(x => x.code === b.dataset.x), rt = r && ratingOf(r.prof); return { code: b.dataset.x, chip: b.querySelector('.rchip') ? b.querySelector('.rchip').innerText.replace(/\s+/g, ' ').trim() : null, want: rt != null ? rt.toFixed(1) + ' · ' + String(PROFS[r.prof].name).trim().split(/\s+/).pop() : null, title: courseName(b.dataset.x) || null, shown: b.querySelector('.rm-t') ? b.querySelector('.rm-t').innerText : null }; }));
  ok(chips.length > 0 && chips.every(c => c.want ? c.chip === c.want : c.chip === null) && chips.some(c => c.want) && chips.some(c => !c.want), 'recs: the rating chip is the professor most of those friends have (number · surname); no rating, no chip', chips);
  ok(chips.every(c => c.title ? c.shown === c.title : c.shown === null), 'recs: each card names the class (no name → just the code)', chips);
  const fit = await page.evaluate(() => { const sc = document.getElementById('scroll').getBoundingClientRect(), row = document.querySelector('.recs-row'), c = row.querySelector('.rmini').getBoundingClientRect(), cards = [...row.querySelectorAll('.rmini')].map(b => b.getBoundingClientRect());
    return { left: Math.round(c.left - sc.left), oneLine: [...row.querySelectorAll('.rchip')].every(x => x.getBoundingClientRect().height < 30), sameH: cards.every(b => Math.abs(b.height - cards[0].height) < 1), scrolls: row.scrollWidth > row.clientWidth || cards.length < 2, pageWide: document.getElementById('scroll').scrollWidth <= document.getElementById('scroll').clientWidth }; });
  ok(fit.left === 12 && fit.oneLine && fit.sameH && fit.pageWide, 'recs: the row starts at Home’s 12px edge, cards are one height, chips one line, and the page never scrolls sideways', fit);
  const code0 = g.cards[0][0];
  await page.evaluate(c => document.querySelector(`.recs .rmini[data-x="${c}"]`).click(), code0); await settle(page);
  ok(await page.evaluate(() => cur().s) === 'classDetail' || /classDetail|class/i.test(await page.evaluate(() => cur().s)), 'recs: a card opens its class', await page.evaluate(() => cur().s));
  await click(page, '[data-a="back"]');
  /* taking it (it lands on your record) takes it out of the row */
  await page.evaluate(c => { TC.myHistory = (TC.myHistory || []).concat([{ code: c, term: null, year: null, professor: null }]); render(true); }, code0); await settle(page, 200);
  g = await got();
  ok(g && !g.cards.some(c => c[0] === code0), 'recs: a class once on your record leaves the row', g && g.cards.map(c => c[0]));
  /* with two friends the row comes after the last week; with nothing to suggest there's no row */
  await page.evaluate(() => { UI._f = TC.friends.slice(); TC.friends = TC.friends.slice(0, 2); UI.feedOrder = null; render(true); }); await settle(page, 200);
  g = await got();
  ok(g && g.at === 2, 'recs: with fewer than three friends the row comes after the last week', g && g.at);
  await page.evaluate(() => { TC.friends.forEach(f => { PEOPLE[f]._s = PEOPLE[f].secs; PEOPLE[f]._u = PEOPLE[f].unplaced; PEOPLE[f].secs = []; PEOPLE[f].unplaced = []; }); render(true); }); await settle(page, 200);
  ok(await page.locator('.recs').count() === 0, 'recs: nothing to suggest → no row');
  ok(log.errors.length === 0, 'recs: no page errors', log.errors);
  await close();
  /* honest or nothing: the record not loaded, the record failed, a friend's classes failed */
  const o = await openApp({});
  await o.page.waitForFunction(() => TC.ready && document.querySelectorAll('.hfeed .fcard').length === 5 && TC.myHistory !== undefined, null, { timeout: 8000 });
  const has = () => o.page.evaluate(() => !!document.querySelector('.recs'));
  ok(await has(), 'recs: (baseline) the row is there');
  await o.page.evaluate(() => { UI._h = TC.myHistory; TC.myHistory = undefined; render(true); }); await settle(o.page, 200);
  ok(!await has(), 'recs: no row before your record has loaded (it could suggest a class you took)');
  await o.page.evaluate(() => { TC.myHistory = UI._h; TC.err.history = 'down'; render(true); }); await settle(o.page, 200);
  ok(!await has(), 'recs: no row when your record failed to load');
  await o.page.evaluate(() => { delete TC.err.history; TC.err.friendSecs = 'down'; render(true); }); await settle(o.page, 200);
  ok(!await has(), 'recs: no row while friends’ classes failed to load (counts would be short)');
  await o.page.evaluate(() => { delete TC.err.friendSecs; render(true); }); await settle(o.page, 200);
  /* a quarter-era code on your record is the same course as its semester code */
  await o.page.evaluate(() => { [TC.friends[0], TC.friends[1]].forEach(f => { PEOPLE[f].unplaced = (PEOPLE[f].unplaced || []).concat(['ECON 2001']); }); render(true); }); await settle(o.page, 200);
  ok(await o.page.evaluate(() => !!document.querySelector('.recs .rmini[data-x="ECON 2001"]')), 'recs: (baseline) ECON 2001, two friends, is suggested');
  await o.page.evaluate(() => { TC.myHistory = TC.myHistory.concat([{ code: 'ECON 201', term: 'Fall', year: 2025, professor: null }]); render(true); }); await settle(o.page, 1500); await settle(o.page, 400);
  const q = await o.page.evaluate(() => ({ tcpl: !!window.TCPL, row: !!document.querySelector('.recs'), econ: !!document.querySelector('.recs .rmini[data-x="ECON 2001"]') }));
  ok(q.tcpl && q.row && !q.econ, 'recs: ECON 201 on your record (quarter code) keeps ECON 2001 out — the crosswalk loads first', q);
  /* the rating follows the professor most of those friends have; a tie shows none */
  const pr = await o.page.evaluate(() => { const ks = Object.keys(PROFS).filter(k => ratingOf(k) != null).slice(0, 2), [f0, f1, f2] = TC.friends, code = 'ZZT 1000';
    const mk = (f, pk, n) => ({ id: 'zz' + n, code, sec: '01', prof: pk, days: [], s: null, e: null, async: true });
    PEOPLE[f0]._zz = PEOPLE[f0].secs; PEOPLE[f1]._zz = PEOPLE[f1].secs; PEOPLE[f2]._zz = PEOPLE[f2].secs;
    /* friend 0 in two of A's sections (lecture + lab), friends 1 and 2 with B: B leads by friends */
    PEOPLE[f0].secs = PEOPLE[f0].secs.concat([mk(f0, ks[0], 1), mk(f0, ks[0], 2)]); PEOPLE[f1].secs = PEOPLE[f1].secs.concat([mk(f1, ks[1], 3)]); PEOPLE[f2].secs = PEOPLE[f2].secs.concat([mk(f2, ks[1], 4)]);
    const a = (friendClassRecs().find(r => r.code === code) || {}).prof;
    PEOPLE[f2].secs = PEOPLE[f2]._zz;   /* now one friend each: a tie */
    const b = (friendClassRecs().find(r => r.code === code) || {}).prof;
    PEOPLE[f0].secs = PEOPLE[f0]._zz; PEOPLE[f1].secs = PEOPLE[f1]._zz;
    return { lead: a === ks[1], tie: b === null, ks, a, b }; });
  ok(pr.lead && pr.tie, 'recs: the rating is the professor most friends have (by friends, not sections); a tie shows no rating', pr);
  ok(o.log.errors.length === 0, 'recs: no page errors (honesty checks)', o.log.errors);
  await o.close();
};

/* ============ Pin up to 3 friends to the front of the stories (Tate, 2026-10-04) ============ */
tests.storyPins = async () => {
  const { page, close, log } = await openApp({});
  await page.waitForFunction(() => TC.ready && document.querySelectorAll('.stories .story').length === 5, null, { timeout: 8000 });
  const order = () => page.evaluate(() => [...document.querySelectorAll('.stories .story')].map(b => b.dataset.x));
  const o0 = await order();
  const hold = (id, ms, move = 0) => page.evaluate(([id, move]) => { const el = document.querySelector(`.stories .story[data-x="${id}"]`), r = el.getBoundingClientRect();
    const T = (x, y) => new Touch({ identifier: 1, target: el, clientX: x, clientY: y });
    el.dispatchEvent(new TouchEvent('touchstart', { touches: [T(r.x + 30, r.y + 30)], bubbles: true }));
    if (move) el.dispatchEvent(new TouchEvent('touchmove', { touches: [T(r.x + 30 + move, r.y + 30)], bubbles: true })); }, [id, move]).then(() => page.clock.runFor(ms)).then(() => page.evaluate(id => { const el = document.querySelector(`.stories .story[data-x="${id}"]`);
    (el || document).dispatchEvent(new TouchEvent('touchend', { touches: [], bubbles: true })); if (el) el.click(); }, id));
  await hold(o0[1], 200); await settle(page);
  ok(await page.evaluate(() => pinsGet().length === 0 && UI.sheet && UI.sheet.type === 'story'), 'pins: a quick tap opens the story and pins nothing');
  await click(page, '#sheet .xbtn'); await settle(page);
  await hold(o0[2], 600, 20); await settle(page);
  ok(await page.evaluate(() => pinsGet().length === 0), 'pins: a hold that slides (scrolling the row) pins nothing');
  await page.evaluate(() => { UI.sheet = null; render(true); }); await settle(page);
  await hold(o0[3], 600); await settle(page);
  let st = await page.evaluate(() => ({ pins: pinsGet(), sheet: !!UI.sheet, first: document.querySelector('.stories .story').dataset.x, badge: !!document.querySelector('.stories .story:first-child .pinbadge'), badges: document.querySelectorAll('.pinbadge').length, label: document.querySelector('.stories .story').getAttribute('aria-label'), toast: document.getElementById('toast').textContent }));
  ok(JSON.stringify(st.pins) === JSON.stringify([o0[3]]) && !st.sheet && st.first === o0[3] && st.badge && st.badges === 1 && /, pinned$/.test(st.label) && /^Pinned /.test(st.toast), 'pins: holding a story pins it to the front with a pin on its ring, and the hold doesn’t also open it', st);
  await page.evaluate(id => document.querySelector(`.stories .story[data-x="${id}"]`).click(), o0[1]); await settle(page);
  ok(await page.evaluate(() => UI.sheet && UI.sheet.type === 'story'), 'pins: the next tap after a hold opens the story as normal');
  ok(await page.locator('#sheet .stpin').getAttribute('aria-pressed') === 'false' && /^Pin .* to the front of your stories$/.test(await page.locator('#sheet .stpin').getAttribute('aria-label')), 'pins: a story’s sheet has a pin button, not pressed');
  await page.focus('#sheet .stpin'); await page.keyboard.press('Enter'); await settle(page);
  const fz = await page.evaluate(() => { const a = document.activeElement; return { pin: !!(a && a.matches('#sheet .stpin')), pressed: a && a.getAttribute('aria-pressed'), label: a && a.getAttribute('aria-label') }; });
  ok(fz.pin && fz.pressed === 'true' && /^Pin .* to the front of your stories$/.test(fz.label), 'pins: from the keyboard, focus stays on the pin; its name stays the same and aria-pressed says it’s on', fz);
  ok(await page.evaluate(() => !!UI.sheet) && await page.locator('#sheet .stpin').getAttribute('aria-pressed') === 'true' && JSON.stringify((await order()).slice(0, 2)) === JSON.stringify([o0[3], o0[1]]), 'pins: pinning from the sheet keeps the sheet open, and pins go first in the order pinned', await order());
  await click(page, '#sheet .xbtn'); await settle(page);
  /* a hold that leaves no click behind (Android, keyboard) doesn't eat the next tap */
  await page.evaluate(id => { const el = document.querySelector(`.stories .story[data-x="${id}"]`), r = el.getBoundingClientRect(); el.dispatchEvent(new TouchEvent('touchstart', { touches: [new Touch({ identifier: 1, target: el, clientX: r.x + 30, clientY: r.y + 30 })], bubbles: true })); }, o0[2]);
  await page.clock.runFor(600); await page.evaluate(() => document.dispatchEvent(new TouchEvent('touchend', { touches: [], bubbles: true }))); await settle(page, 600);
  await page.evaluate(id => A.togglePin(id), o0[2]); await settle(page);   /* undo that pin */
  await page.evaluate(() => document.querySelector('.stories .story:last-child').click()); await settle(page);
  ok(await page.evaluate(() => UI.sheet && UI.sheet.type === 'story'), 'pins: a hold with no click after it doesn’t swallow the next tap');
  await click(page, '#sheet .xbtn');
  await page.evaluate(id => A.openFriend(id), o0[4]); await settle(page);
  await click(page, '.fpin'); await settle(page);
  ok(await page.locator('.fpin').getAttribute('aria-pressed') === 'true' && await page.evaluate(() => pinsGet().length) === 3, 'pins: a friend’s page has a pin beside Message');
  await page.evaluate(id => A.togglePin(id), o0[0]); await settle(page, 100);
  st = await page.evaluate(() => ({ n: pinsGet().length, toast: document.getElementById('toast').textContent }));
  ok(st.n === 3 && /^3 pinned already — unpin \S+, \S+ or \S+ first$/.test(st.toast), 'pins: a fourth is refused, naming the three', st);
  await page.evaluate(id => A.togglePin(id), o0[3]); await settle(page);
  await click(page, '[data-a="back"]'); await settle(page);
  st = await page.evaluate(() => ({ pins: pinsGet(), key: Object.keys(localStorage).filter(k => /^tc-story-pins:/.test(k)), uid: TC.user.id }));
  ok(JSON.stringify(st.pins) === JSON.stringify([o0[1], o0[4]]) && JSON.stringify((await order()).slice(0, 2)) === JSON.stringify([o0[1], o0[4]]) && st.key.length === 1 && st.key[0] === 'tc-story-pins:' + st.uid, 'pins: unpinning frees a slot; pins are kept on this phone under your account', st);
  /* a saved pin for someone not in the friend list right now is kept, not wiped by the next pin */
  await page.evaluate(() => { localStorage.setItem(pinKey(), JSON.stringify(['gone-friend'].concat(pinsSaved()))); });
  await page.evaluate(id => A.togglePin(id), o0[0]); await settle(page);
  st = await page.evaluate(() => ({ saved: pinsSaved(), shown: pinsGet() }));
  ok(st.saved.includes('gone-friend') && !st.shown.includes('gone-friend') && st.shown.length === 3, 'pins: a pin for someone not in your friend list now is kept on the phone, just not shown', st);
  ok(log.errors.length === 0 && !log.writes.some(w => w.table === 'profiles'), 'pins: no page errors, nothing sent to the server', log.errors);
  await close();
};

/* ============ A friend's major, concentration and year (Tate, 2026-10-04) ============ */
tests.friendMajor = async () => {
  const T = JSON.parse(JSON.stringify(FX.TABLES));
  Object.assign(T.profiles[1], { major: 'Finance', class_standing: 'Junior', concentration: 'Financial Management' });
  Object.assign(T.profiles[2], { major: 'Computer Science', class_standing: null, concentration: 'General / Open' });
  Object.assign(T.profiles[3], { major: null, class_standing: null, concentration: null });
  Object.assign(T.profiles[6], { major: 'Economics', class_standing: 'Senior', concentration: 'Real Estate' });   /* a pending requester, not a friend */
  const ids = T.profiles.slice(1, 4).map(p => p.id);
  const look = async (page, id) => { await page.evaluate(id => A.openFriend(id), id); await settle(page);
    const r = await page.evaluate(() => ({ pill: (document.querySelector('.fmaj-pill') || {}).textContent || null, sub: (document.querySelector('.fmaj-sub') || {}).textContent || null })); await click(page, '[data-a="back"]'); await settle(page); return r; };
  /* before the SQL runs: concentration can't be read, so major and year only */
  let o = await openApp({ tables: T });
  await o.page.waitForFunction(() => TC.ready && document.querySelectorAll('.hfeed .fcard').length === 5, null, { timeout: 8000 });
  let a = await look(o.page, ids[0]);
  ok(a.pill === 'Finance' && a.sub === 'Junior', 'friend major: before the SQL, the major pill and the year (no concentration)', a);
  const cq = () => o.log.reads.filter(r => /^profiles\?select=[^&]*concentration/.test(r) && /id=in/.test(r)).length;
  const n1 = cq(); await o.page.evaluate(() => homeRefresh()); await settle(o.page, 1500);
  ok(n1 === 1 && cq() === 1, 'friend major: a refused concentration read is not tried again on every refresh', { n1, n2: cq() });
  ok(o.log.errors.length === 0, 'friend major: no page errors (no grant)', o.log.errors);
  await o.close();
  /* after it runs */
  o = await openApp({ tables: T, grants: { profiles: ['concentration'] } });
  await o.page.waitForFunction(() => TC.ready && document.querySelectorAll('.hfeed .fcard').length === 5, null, { timeout: 8000 });
  a = await look(o.page, ids[0]);
  ok(a.pill === 'Finance' && a.sub === 'Financial Management concentration · Junior', 'friend major: major, then “<concentration> concentration · <year>”', a);
  a = await look(o.page, ids[1]);
  ok(a.pill === 'Computer Science' && a.sub === null, 'friend major: “General / Open” and no year → the major alone', a);
  a = await look(o.page, ids[2]);
  ok(a.pill === null && a.sub === null, 'friend major: nothing set → nothing drawn', a);
  await o.page.evaluate(id => A.openFriend(id), T.profiles[6].id); await settle(o.page);
  a = await o.page.evaluate(() => ({ page: /Morgan Nobody/.test(document.getElementById('scroll').innerText) && !!document.querySelector('[data-a="acceptReq"]'), maj: document.querySelectorAll('.fmaj').length, econ: /Economics|Real Estate/.test(document.getElementById('scroll').innerText) }));
  ok(a.page && a.maj === 0 && !a.econ, 'friend major: someone who isn’t your friend yet (a pending request) shows no major', a);
  await click(o.page, '[data-a="back"]');
  const box = await o.page.evaluate(id => { A.openFriend(id); return null; }, ids[0]); await settle(o.page);
  const lay = await o.page.evaluate(() => { const h = document.querySelector('.fhandle').getBoundingClientRect(), m = document.querySelector('.fmaj').getBoundingClientRect(), b = document.querySelector('[data-a="openChatWith"]').getBoundingClientRect(), pill = document.querySelector('.fmaj-pill').getBoundingClientRect(); return { order: h.bottom <= m.top && m.bottom <= b.top, centred: Math.abs((pill.left + pill.right) / 2 - innerWidth / 2) < 2, fits: pill.right <= innerWidth - 16 }; });
  ok(lay.order && lay.centred && lay.fits, 'friend major: under the handle, above Message, centred', lay);
  ok(o.log.errors.length === 0, 'friend major: no page errors', o.log.errors);
  await o.close();
};

/* ============ The top of the screen is one colour (Tate, 2026-09-30) ============ */
tests.topColour = async () => {
  for (const [w, h, tag] of [[1200, 900, 'preview'], [390, 844, 'phone']]) {
    const { page, close, log } = await openApp({ width: w, height: h });
    await page.waitForFunction(() => TC.ready && document.querySelectorAll('.hfeed .fcard').length === 5, null, { timeout: 8000 });
    const top = () => page.evaluate(() => { const s = document.getElementById('status'), cs = getComputedStyle(s), r = s.getBoundingClientRect(), ph = getComputedStyle(document.querySelector('.phone'));
      return { bg: cs.backgroundColor, img: cs.backgroundImage, sh: cs.boxShadow, disp: cs.display, h: Math.round(r.height), page: ph.backgroundColor, kids: [...s.children].map(k => getComputedStyle(k).visibility) }; });
    let t = await top();
    ok(t.disp !== 'none' && t.h >= 14 && t.bg === 'rgb(231, 236, 245)' /* Home is deep since 20:30 */ && t.img === 'none' && t.bg === t.page && t.sh === 'none', `top (${tag}): the strip at the top is the page’s own colour, solid, with no line at rest`, t);
    if (tag === 'phone') ok(t.kids.every(v => v === 'hidden'), 'top (phone): the phone’s real clock shows there — the drawn one is hidden', t.kids);
    await page.evaluate(() => { document.getElementById('scroll').scrollTop = 200; }); await settle(page);
    t = await top();
    /* no hairline any more (Tate, 2026-10-06: "make it seemless and blend") — in light or dark */
    ok(t.sh === 'none' && t.bg === t.page, `top (${tag}): scrolled, the strip still blends into the page — no line under it`, t);
    await page.evaluate(() => { document.documentElement.setAttribute('data-theme', 'dark'); render(true); document.getElementById('scroll').scrollTop = 200; }); await settle(page);
    const td = await top();
    ok(td.sh === 'none' && td.bg === td.page && td.bg === 'rgb(10, 15, 28)', `top (${tag}): in dark mode too, no line and the page's own navy`, td);
    await page.evaluate(() => { document.documentElement.setAttribute('data-theme', 'light'); render(true); }); await settle(page);
    await page.evaluate(() => { document.getElementById('scroll').scrollTop = 0; }); await settle(page);
    ok((await top()).sh === 'none', `top (${tag}): back at the top, the line goes`);
    if (tag === 'preview') {
      await page.evaluate(() => { S.tab = 'friends'; S.stack.friends = [{ s: 'friends' }]; A.openChat(TC.threads[0].id); }); await settle(page, 800);
      /* a long chat, scrolled */
      await page.evaluate(() => { const id = TC.threads[0].id, r0 = TC.rows[id][0]; for (let k = 0; k < 40; k++) TC.rows[id].push(Object.assign({}, r0, { id: 'pad' + k, body: 'line ' + k })); render(true); }); await settle(page);
      const cy = await page.evaluate(() => { const sc = document.getElementById('scroll'); sc.scrollTop = 0; sc.scrollTop = 99999; return sc.scrollTop; }); await settle(page);
      const c = await top();
      ok(cy > 200 && await page.locator('#fixtop .chathdr').count() === 1 && c.sh === 'none', 'top: no second line over a screen with its own header (a long chat, scrolled)', { cy, sh: c.sh });
      await page.evaluate(() => { S.lastRated = { prof: Object.keys(PROFS)[0], diff: 3, again: 'yes' }; go('rateThanks'); }); await settle(page);
      const dk = await page.evaluate(() => [...document.querySelectorAll('meta[name=theme-color]')].map(m => m.content));
      /* 2026-10-04: no black behind rating (Tate): the Thanks screen and the form keep the light strip, status bar and page */
      const rq = () => page.evaluate(() => ({ st: document.getElementById('status').classList.contains('dark'), stBg: getComputedStyle(document.getElementById('status')).backgroundColor,
        scBg: document.getElementById('scroll').style.background, rfBg: getComputedStyle(document.querySelector('.rf')).backgroundImage, rfCol: getComputedStyle(document.querySelector('.rf')).backgroundColor }));
      const r1 = await rq().catch(e => String(e));
      await page.evaluate(() => A.back()); await settle(page);
      const lt = await page.evaluate(() => [...document.querySelectorAll('meta[name=theme-color]')].map(m => m.content));
      await page.evaluate(() => { A.rateProf(Object.keys(PROFS).find(k => !iReviewed(k))); }); await settle(page);
      const dk2 = await page.evaluate(() => [...document.querySelectorAll('meta[name=theme-color]')].map(m => m.content)), r2 = await rq().catch(e => String(e)), onForm = await page.evaluate(() => cur().s);
      await page.evaluate(() => A.back()); await settle(page);
      const light = r => r && r.st === false && r.stBg === 'rgb(244, 246, 251)' && r.scBg === '' && r.rfBg === 'none' && r.rfCol === 'rgba(0, 0, 0, 0)';
      ok(dk.concat(dk2, lt).every(c => c === '#F4F6FB') && onForm === 'rateForm' && light(r1) && light(r2), 'top: no black behind rating — the form and the Thanks screen keep the light strip, status bar and page', { dk, dk2, lt, r1, r2, onForm });
    }
    ok(log.errors.length === 0, `top (${tag}): no page errors`, log.errors);
    await close();
  }
  const html = nodeFs.readFileSync(nodePath.join(process.env.APP_DIR || nodePath.resolve(nodePath.dirname(new URL(import.meta.url).pathname), '..', 'out'), 'app', 'index.html'), 'utf8');
  const tc = [...html.matchAll(/<meta name="theme-color" content="([^"]+)"( media="([^"]+)")?>/g)].map(m => [m[1], m[3]]);
  ok(tc.length === 2 && tc.every(x => x[0] === '#F4F6FB') && tc.some(x => /light/.test(x[1])) && tc.some(x => /dark/.test(x[1])) && /<meta name="color-scheme" content="light">/.test(html), 'top: the phone’s own strip is the page colour in light AND dark mode', tc);
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
  /* + on a class page opens "Add to your week" (2026-10-04): a full screen, My Classes | Plans, the
     place's week with the section lit in its colour and the rest greyed. Fixture Plan B holds ECON 2303
     Sec 03 (TuTh 10:10–12:00). */
  const { page, close, log } = await openApp({});
  await page.waitForFunction(() => TC.ready && TC.seatsLoaded, null, { timeout: 8000 });
  await page.evaluate(() => A.openClass('PHIL 3331')); await settle(page, 500);
  ok(!/Tap \+ to add/.test(await text(page)) && await page.locator('.secrow .addbtn').count() > 0, 'picker: no hint line under Sections (2026-10-03); the + buttons are still there');
  ok(await page.locator('.secrow .addbtn').first().getAttribute('aria-label') === 'Add to your week', 'picker: the + reads "Add to your week"');
  await click(page, '.secrow .addbtn');
  const fp = await page.evaluate(() => { const f = document.querySelector('#sheet .fullpg'), r = f && f.getBoundingClientRect(), ph = document.getElementById('phone').getBoundingClientRect(); return f && { full: Math.round(r.width) === Math.round(ph.width) && Math.round(r.height) === Math.round(ph.height), z: getComputedStyle(f).zIndex, dlg: f.getAttribute('role'), scrim: !!document.querySelector('#sheet .scrim') }; });
  ok(fp && fp.full && fp.dlg === 'dialog' && !fp.scrim, 'picker: it is a full screen over the app (no sheet, no scrim)', fp);
  ok(await page.locator('#sheet .at-chip[data-a="atPick"]').count() === 3 && await page.locator('#sheet .at-chip.on').getAttribute('data-x') === 'A' && await page.locator('#sheet [data-a="atGroup"][data-x="plans"]').getAttribute('aria-pressed') === 'true', 'picker: Plans picked, three plans, the last-used one (A) on');
  const head = await page.locator('#sheet .at-head').innerText();
  ok(/^PHIL 3331\s*Sec 01\s*Business Ethics\s*Tue\/Thu · 9:10–11:00\s*·\s*5 seats\s*Dov Mockridge\s*★ \d\.\d/.test(head.trim()), 'picker: a clean top — code and section, the name, when · seats, the professor and rating', head);
  ok(/Avery and Quinn are in this section/.test(head), 'picker: friends in that section are named', head);
  const g = await page.evaluate(() => { const b = document.querySelector('#sheet .g-b.ghost'); const cs = getComputedStyle(b); return { bg: cs.backgroundColor, fg: cs.color, n: document.querySelectorAll('#sheet .g-b.ghost').length, spot: document.querySelector('#sheet .addto').classList.contains('spot'), hi: [...document.querySelectorAll('#sheet .g-day.hi')].map(x => x.dataset.x).join('') }; });
  ok(g.n === 2 && g.bg === 'rgb(15, 118, 110)' && g.fg === 'rgb(255, 255, 255)' && g.spot && g.hi === 'TR', 'picker: the section is lit in Plan A’s teal, white text, its days lit', g);
  const wd = await page.evaluate(() => { const c = document.querySelector('#sheet .g-col').getBoundingClientRect(), wk = document.querySelector('#sheet .at-week').getBoundingClientRect(), ph = document.getElementById('phone').getBoundingClientRect(); return { col: +c.width.toFixed(1), edge: Math.round(wk.left - ph.left) }; });
  ok(Math.abs(wd.col - 59.8) < 0.6 && wd.edge === 12, 'picker: the week is at Home’s width (12px edge, 59.8px day at 390)', wd);
  await click(page, '#sheet [data-a="atPick"][data-x="B"]');
  const b = await page.locator('#sheet').innerText();
  const bg = await page.evaluate(() => ({ ghost: getComputedStyle(document.querySelector('#sheet .g-b.ghost')).backgroundColor, clashb: document.querySelectorAll('#sheet .g-b.clashb').length, chip: getComputedStyle(document.querySelector('#sheet .at-chip.on')).backgroundColor }));
  ok(bg.ghost === 'rgb(220, 38, 38)' && bg.clashb === 2 && bg.chip === 'rgb(194, 65, 12)', 'picker: on Plan B (orange chip) the section goes red over ECON 2303, which is marked too', bg);
  ok(/Clashes with ECON 2303 Sec 03 · Tue\/Thu 10:10–12:00/.test(b) && await page.locator('#sheet [data-a="atGo"]').count() === 0 && await page.locator('#sheet .at-cta button[disabled]').count() === 1, 'picker: a clash in a plan names the class and can’t be added', b);
  await click(page, '#sheet [data-a="atPick"][data-x="C"]');
  ok(/Fits Plan C/.test(await page.locator('#sheet').innerText()) && await page.locator('#sheet .addto.plan-C').count() === 1, 'picker: an empty Plan C fits, in Plan C’s colours');
  const fxOnce = await page.evaluate(() => { const a = !!document.querySelector('#sheet .addto.fx'); render(true); return [a, !!document.querySelector('#sheet .addto.fx'), getComputedStyle(document.querySelector('#sheet .fullpg')).animationName]; });
  ok(fxOnce[0] === true && fxOnce[1] === false && fxOnce[2] === 'none', 'picker: the light-up plays once — a redraw doesn’t replay it or the screen’s entrance', fxOnce);
  const n0 = log.writes.filter(w => w.table === 'plans').length;
  /* (clicked through A.atGo so the first frame can be read: a click waits for the lit block to settle) */
  const ad = await page.evaluate(() => { A.atGo('add'); const a = document.querySelector('#sheet .addto'); return { cls: a.className, ghosts: a.querySelectorAll('.g-b.ghost').length, cta: a.querySelector('.at-cta').innerText }; });
  ok(/\badding\b/.test(ad.cls) && /\bfx\b/.test(ad.cls) && ad.ghosts === 2 && /Adding…/.test(ad.cta), 'picker: Add drops it in (adding)', ad);
  await page.waitForFunction(() => UI.sheet && UI.sheet.phase === 'done', null, { timeout: 5000 });
  const done = await page.evaluate(() => ({ added: !!document.querySelector('#sheet .addto.added'), spot: !!document.querySelector('#sheet .addto.spot'), btn: (document.querySelector('#sheet .at-cta') || {}).innerText }));
  ok(done.added && !done.spot && /Added to Plan C/.test(done.btn), 'picker: then the week lights back up and says where it went', done);
  await settle(page, 1100);
  const up = log.writes.filter(w => w.table === 'plans').slice(n0);
  ok(up.length === 1 && up[0].body.slot === 'C' && up[0].body.sections.some(x => x.code === 'PHIL 3331'), 'picker: Add writes to the plan picked (C)', up.map(w => w.body));
  const tt = await page.locator('#toast').innerText();
  ok(await page.locator('#sheet .fullpg').count() === 0 && /Added PHIL 3331 to Plan C/.test(tt) && await page.locator('#toast.act [data-a="toastUndo"]').count() === 1, 'picker: it closes by itself with “Added … · Undo”', tt);
  ok(await page.locator('.secrow .addbtn.in').count() === 1, 'picker: the section now shows as in your week');
  const n1 = log.writes.filter(w => w.table === 'plans').length;
  await click(page, '#toast [data-a="toastUndo"]'); await settle(page, 800);
  const un = log.writes.filter(w => w.table === 'plans').slice(n1);
  ok(un.length === 1 && (un[0].m === 'DELETE' ? /slot=eq\.C/.test(un[0].query) : !un[0].body.sections.some(x => x.code === 'PHIL 3331')) && await page.locator('.secrow .addbtn.in').count() === 0, 'picker: Undo takes it back out', un.map(w => [w.m, w.query]));
  /* The same class in another section is a swap: the old one dashed, the new one lit. */
  await page.evaluate(() => A.openClass('ECON 2303')); await settle(page, 500);
  await click(page, '.secrow .addbtn >> nth=1'); await click(page, '#sheet [data-a="atPick"][data-x="B"]');
  const sw = await page.locator('#sheet').innerText();
  ok(/Swaps out ECON 2303 Sec 03 \(Tue\/Thu 10:10–12:00\)/.test(sw) && /Swap into Plan B/.test(sw) && await page.locator('#sheet .g-b.repl').count() === 2 && await page.locator('#sheet .g-b.ghost').count() === 2, 'picker: another section already in the plan shows dashed, with Swap', sw);
  await click(page, '#sheet .xbtn[data-a="closeSheet"]');
  /* A section already in a plan opens there, ticked, with Remove (and Undo). */
  await page.evaluate(id => { TC.setPlan('C', [id]); S.plan = 'A'; S.addDest = 'A'; A.openClass('PHIL 3331'); }, FX.seat('PHIL 3331', '01').class_nbr); await settle(page, 600);
  await click(page, '.secrow .addbtn');
  const on = await page.locator('#sheet .at-chip.on').getAttribute('data-x'), has = await page.locator('#sheet .at-chip[aria-label="Plan C, has this section"] svg').count();
  ok(on === 'C' && has === 1 && /Remove from Plan C/.test(await page.locator('#sheet').innerText()) && await page.locator('#sheet .addto.spot').count() === 0, 'picker: a section already in Plan C opens on Plan C, ticked, not spotlit, with Remove', { on, has });
  const n2 = log.writes.filter(w => w.table === 'plans').length;
  await click(page, '#sheet [data-a="atRemove"]'); await settle(page, 800);
  const rm = log.writes.filter(w => w.table === 'plans').slice(n2);
  ok(rm.length === 1 && (rm[0].m === 'DELETE' ? /slot=eq\.C/.test(rm[0].query) : !rm[0].body.sections.some(x => x.code === 'PHIL 3331')) && /Removed PHIL 3331 from Plan C/.test(await page.locator('#toast').innerText()) && await page.locator('#sheet .fullpg').count() === 0, 'picker: Remove takes it out of Plan C only, closes, offers Undo', rm.map(w => [w.m, w.query]));
  /* Reduce Motion: nothing bounces or slides. */
  await page.emulateMedia({ reducedMotion: 'reduce' });
  await click(page, '.secrow .addbtn');
  const rmo = await page.evaluate(() => [getComputedStyle(document.querySelector('#sheet .fullpg')).animationName, getComputedStyle(document.querySelector('#sheet .g-b.ghost')).animationName, getComputedStyle(document.querySelector('#sheet .g-b.ghost'), '::before').animationName]);
  ok(rmo.every(x => x === 'none'), 'picker: Reduce Motion turns the animations off', rmo);
  ok(log.errors.length === 0, 'picker: no page errors', log.errors);
  await close();
};

/* My Classes from the same screen (2026-10-04): this term only; full sections ask Enrolled or
   Waitlisted; a clash warns but can be added; another section of a class you have is Swap or Keep both;
   Undo puts the class's own rows back. Fixture My Classes: BUS 3438 §01 MoWe 10:10, BUS 4442 §01 MoWe
   12:10, BUS 4445 §01 MoWe 2:10, BUS 3431 §01 MoWe 4:10, BUS 2201 (no section). */
tests.addToWeek = async () => {
  let failSec = false;
  const { page, close, log } = await openApp({ hook: (url, m) => failSec && m === 'POST' && url.pathname.endsWith('/my_sections') ? { status: 400, body: JSON.stringify({ code: '23514', message: 'check violation' }) } : null });
  await page.waitForFunction(() => TC.ready && TC.seatsLoaded, null, { timeout: 8000 });
  const W = t => log.writes.filter(w => w.table === t);
  await page.evaluate(() => A.openClass('PHIL 3331')); await settle(page, 500);
  await click(page, '.secrow .addbtn');
  await click(page, '#sheet [data-a="atGroup"][data-x="classes"]');
  const ch = await page.evaluate(() => [...document.querySelectorAll('#sheet .at-chip')].map(b => ({ x: b.dataset.x, t: b.innerText.trim(), on: b.classList.contains('on'), dis: b.classList.contains('dis'), al: b.getAttribute('aria-label') })));
  ok(ch.length === 2 && ch[0].x === 'mine' && ch[0].t === 'Fall 2026' && ch[0].on && !ch[0].dis && ch[1].t === 'Spring 2027' && ch[1].dis && /needs a Spring 2027 section/.test(ch[1].al), 'mine: My Classes shows the term chips; Fall on, Spring can’t take a Fall section', ch);
  await page.waitForTimeout(700);   /* the grey fades in (CSS, real time) */
  const dim = await page.evaluate(() => { const o = [...document.querySelectorAll('#sheet .g-b:not(.ghost)')].map(b => getComputedStyle(b).backgroundColor); const gh = getComputedStyle(document.querySelector('#sheet .g-b.ghost')).backgroundColor; return { o: [...new Set(o)], gh, n: o.length }; });
  ok(dim.n === 8 && dim.o.length === 1 && dim.o[0] === 'rgb(236, 239, 244)' && dim.gh === 'rgb(37, 99, 235)', 'mine: your other classes go grey; the one going in is lit blue', dim);
  ok(/Fits your week\./.test(await page.locator('#sheet .at-note').innerText()), 'mine: PHIL fits');
  await click(page, '#sheet [data-a="atPick"][data-x="term:Spring 2027"]');
  const sp = await page.locator('#sheet').innerText();
  ok(/Spring 2027 sections aren’t posted yet/.test(sp) && await page.locator('#sheet [data-a="atGo"]').count() === 0 && await page.locator('#sheet .g-b').count() === 0, 'mine: the Spring chip explains and offers nothing to add', sp.slice(-200));
  await click(page, '#sheet [data-a="atPick"][data-x="mine"]');
  const s0 = W('saved_classes').length, m0 = W('my_sections').length;
  await atGo(page);
  const sv = W('saved_classes').slice(s0), ms = W('my_sections').slice(m0);
  ok(sv.length === 1 && sv[0].m === 'POST' && sv[0].body.code === 'PHIL 3331' && sv[0].body.term === '2268' && ms.length === 1 && ms[0].body.class_nbr === FX.seat('PHIL 3331', '01').class_nbr && ms[0].body.status === 'enrolled' && ms[0].body.wl_pos === null, 'mine: Add saves the class and its section, enrolled', [sv.map(w => w.body), ms.map(w => w.body)]);
  ok(/Added PHIL 3331 to My Classes/.test(await page.locator('#toast').innerText()) && await page.evaluate(() => S.addDest) === 'mine', 'mine: it says so, and My Classes is now where it opens next');
  const s1 = W('saved_classes').length, m1 = W('my_sections').length;
  await click(page, '#toast [data-a="toastUndo"]'); await settle(page, 800);
  const usv = W('saved_classes').slice(s1), ums = W('my_sections').slice(m1);
  ok(ums.length === 1 && ums[0].m === 'DELETE' && /code=eq\.PHIL(\+|%20)3331/.test(ums[0].query) && usv.length === 1 && usv[0].m === 'DELETE' && await page.evaluate(() => !myCodes().has('PHIL 3331')), 'mine: Undo removes exactly what Add put there', [ums.map(w => w.m + w.query), usv.map(w => w.m)]);
  /* A full section asks: enrolled or waitlisted (+ your spot). ECON 2303 §04 is Wait List. */
  await page.evaluate(() => A.openClass('ECON 2303')); await settle(page, 500);
  await page.evaluate(() => { const sc = document.getElementById('scroll'); sc.scrollTop = sc.scrollHeight; }); await settle(page); /* scrolled to the end, clear of the floating Champ */ await click(page, '.secrow .addbtn >> nth=1');
  ok(await page.locator('#sheet [data-a="atGroup"][data-x="classes"]').getAttribute('aria-pressed') === 'true', 'mine: it opens on My Classes, where you last added');
  ok(/are you in it, or on the waitlist/.test(await page.locator('#sheet .at-note').innerText()) && await page.locator('#sheet [data-a="atGo"]').count() === 0 && await page.locator('#sheet [data-a="atStatus"]').count() === 2, 'mine: a full section asks Enrolled or Waitlisted before it can be added');
  await click(page, '#sheet [data-a="atStatus"][data-x="waitlisted"]');
  await page.locator('#atwl').fill('7x');
  ok(await page.locator('#atwl').inputValue() === '7', 'mine: the spot takes digits only');
  const m2 = W('my_sections').length;
  await atGo(page);
  const wl = W('my_sections').slice(m2);
  ok(wl.length === 1 && wl[0].body.status === 'waitlisted' && wl[0].body.wl_pos === 7 && wl[0].body.class_nbr === FX.seat('ECON 2303', '04').class_nbr, 'mine: saved as waitlisted, spot 7 (the desktop’s row shape)', wl.map(w => w.body));
  await click(page, '[data-a="tab"][data-x="schedule"]'); await click(page, '[data-a="schedTab"][data-x="mine"]');
  const wt = await text(page), gold = await page.evaluate(() => [...document.querySelectorAll('#scroll .g-b.wlist')].map(b => b.dataset.x + '|' + getComputedStyle(b).borderTopStyle));
  ok(/ECON 2303[\s\S]{0,80}Waitlist #7/.test(wt) && gold.length === 2 && gold.every(x => x === 'ECON 2303|dashed'), 'mine: My Classes shows it as a dashed gold block and “Waitlist #7”', { gold, t: wt.slice(-300) });
  /* A clash in My Classes warns, and can still be added. BUS 4401 §01 MoWe 10:10 clashes with BUS 3438. */
  await page.evaluate(() => A.openClass('BUS 4401')); await settle(page, 500);
  await click(page, '.secrow .addbtn');
  const cn = await page.locator('#sheet .at-note').innerText();
  ok(/Clashes with BUS 3438 Sec 01 · Mon\/Wed 10:10–12:00/.test(cn) && /Add anyway/.test(await page.locator('#sheet [data-a="atGo"]').innerText()) && await page.locator('#sheet .g-b.clashb').count() === 2, 'mine: a clash warns, marks the class, and offers Add anyway', cn);
  const m3 = W('my_sections').length;
  await atGo(page);
  ok(W('my_sections').slice(m3).length === 1 && await page.evaluate(() => myCodes().has('BUS 4401')), 'mine: Add anyway adds it');
  /* Another section of a class you have: Swap, or Keep both. BUS 3431 §02 vs your §01. */
  await page.evaluate(() => A.openClass('BUS 3431')); await settle(page, 500);
  await page.evaluate(() => { const sc = document.getElementById('scroll'); sc.scrollTop = sc.scrollHeight; }); await settle(page); /* scrolled to the end, clear of the floating Champ */ await click(page, '.secrow .addbtn >> nth=1');
  const swn = await page.locator('#sheet').innerText();
  ok(/You have BUS 3431 Sec 01 \(Mon\/Wed 4:10–6:00pm\)/.test(swn) && /Swap for Sec 02/.test(swn) && /Keep both/.test(swn) && await page.locator('#sheet .g-b.repl').count() === 2, 'mine: another section of your class offers Swap or Keep both', swn.slice(-300));
  await click(page, '#sheet [data-a="atBoth"]');
  ok(/Fits your week/.test(await page.locator('#sheet .at-note').innerText()) && await page.locator('#sheet .g-b.repl').count() === 0, 'mine: Keep both keeps the old section as it is');
  await click(page, '#sheet .xbtn[data-a="closeSheet"]');
  await page.evaluate(() => { const sc = document.getElementById('scroll'); sc.scrollTop = sc.scrollHeight; }); await settle(page); /* scrolled to the end, clear of the floating Champ */ await click(page, '.secrow .addbtn >> nth=1');
  const m4 = W('my_sections').length;
  await atGo(page);
  const swp = W('my_sections').slice(m4);
  const oldNbr = FX.seat('BUS 3431', '01').class_nbr, newNbr = FX.seat('BUS 3431', '02').class_nbr;
  ok(swp.length === 2 && swp[0].m === 'POST' && swp[0].body.class_nbr === newNbr && swp[1].m === 'DELETE' && new RegExp('class_nbr=eq\\.' + oldNbr).test(swp[1].query), 'mine: Swap saves the new section, then drops the old one', swp.map(w => w.m + ' ' + (w.body ? w.body.class_nbr : w.query)));
  const m5 = W('my_sections').length;
  await click(page, '#toast [data-a="toastUndo"]'); await settle(page, 800);
  const und = W('my_sections').slice(m5);
  ok(und.length === 2 && und[0].m === 'POST' && und[0].body.class_nbr === oldNbr && und[1].m === 'DELETE' && new RegExp('class_nbr=eq\\.' + newNbr).test(und[1].query) && await page.evaluate(o => personSecs('me').some(x => x.id === o) && !personSecs('me').some(x => x.code === 'BUS 3431' && x.id !== o), oldNbr), 'mine: Undo puts your old section back first, then takes out only the new one', und.map(w => w.m + ' ' + JSON.stringify(w.body || w.query).slice(0, 80)));
  /* A section that won't save takes the new saved row back with it, and says so. */
  await page.evaluate(() => A.openClass('STAT 2170')); await settle(page, 500);
  await page.evaluate(() => { const sc = document.getElementById('scroll'); sc.scrollTop = sc.scrollHeight; }); await settle(page); /* scrolled to the end, clear of the floating Champ */ await click(page, '.secrow .addbtn >> nth=1');
  failSec = true; const s7 = W('saved_classes').length;
  await atGo(page);
  failSec = false;
  const rb = W('saved_classes').slice(s7);
  ok(rb.length === 2 && rb[0].m === 'POST' && rb[1].m === 'DELETE' && /STAT(\+|%20)2170/.test(rb[1].query) && await page.locator('#sheet .at-note.bad').count() === 1 && await page.evaluate(() => !myCodes().has('STAT 2170') && UI.sheet && UI.sheet.phase === 'preview' && !UI.busy.at), 'mine: a section that fails to save rolls the class back and stays open with the error', rb.map(w => w.m));
  ok(await page.evaluate(() => document.getElementById('scroll').inert && document.getElementById('chrome').inert), 'mine: the app behind the full screen is inert');
  await click(page, '#sheet .xbtn[data-a="closeSheet"]');
  ok(await page.evaluate(() => !document.getElementById('scroll').inert), 'mine: and usable again once it closes');
  /* A section you have opens on My Classes with Remove. */
  await page.evaluate(() => A.openClass('BUS 4442')); await settle(page, 500);
  await click(page, '.secrow .addbtn');
  ok(/BUS 4442 Sec 01 is in My Classes/.test(await page.locator('#sheet .at-note').innerText()) && await page.locator('#sheet .at-chip.on svg').count() === 1, 'mine: your own section opens on My Classes, ticked, with Remove');
  const s6 = W('saved_classes').length;
  await click(page, '#sheet [data-a="atRemove"]'); await settle(page, 800);
  ok(W('saved_classes').slice(s6).some(w => w.m === 'DELETE' && /BUS(\+|%20)4442/.test(w.query)) && /Removed BUS 4442 from My Classes/.test(await page.locator('#toast').innerText()), 'mine: Remove takes the class out, with Undo');
  ok(log.errors.length === 0, 'mine: no page errors', log.errors);
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
  const chipWant = await page.evaluate(() => { const norm = c => { const e = document.createElement('i'); e.style.backgroundColor = c; document.body.appendChild(e); const v = getComputedStyle(e).backgroundColor; e.remove(); return v; };
    return Object.fromEntries(['ada examplewood', 'esme samplesworth', 'bram fixturesen'].map(pk => { const st = rateStep(ratingOf(pk)); return [pk.split(' ')[0][0].toUpperCase() + pk.split(' ')[0].slice(1), [norm(RATE_PALE(st)), RATE_DARK(st)]]; })); });
  ok(['Ada', 'Esme', 'Bram'].every(n => chips[n][1] === chipWant[n][0] && chips[n][2] === chipWant[n][1]) && chips.Ada[2] !== chips.Esme[2] && chips.Esme[2] !== chips.Bram[2], 'ratings: each chip is its half star’s pale tint with that step’s dark star (one scale)', { chips, chipWant });
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
  ok(/Couldn’t load Avery’s classes/.test(t) && !/hasn’t added classes|No times yet|No set time|Anytime|with you/i.test(t), 'home: when friends’ classes fail to load every card says so — no “hasn’t added”, no false “No times yet” or “0 with you”', t.slice(0, 400));
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
  const rings = await page.evaluate(() => TC.friends.map(id => [status(id).rc || status(id).c || 'transparent', document.querySelector(`.story[data-x="${id}"] .ring`).getAttribute('style')]));
  ok(rings.length === 5 && rings.every(([c, st]) => st.includes(c)), 'status: every friend story ring is that friend’s status colour', rings);
  await close();
};

/* Rings (Tate, 2026-10-03): no class today = free = green; no classes added = a grey "unknown" ring, last. */
tests.ringsToday = async () => {
  const { page, close, log } = await openApp({ time: '2026-10-03T12:00:00-07:00' });   /* a Saturday */
  await page.waitForFunction(() => typeof TC === 'object' && TC.ready && document.querySelectorAll('.story').length === 5, null, { timeout: 8000 });
  const r = await page.evaluate(() => TC.friends.map(id => { const st = status(id), el = document.querySelector(`.story[data-x="${id}"] .ring`);
    return { n: PEOPLE[id].short, t: st.t, free: st.free, ring: (el.getAttribute('style').match(/--rc:([^;"]+)/) || [])[1], has: personSecs(id).length > 0 }; }));
  const withC = r.filter(x => x.has), none = r.filter(x => !x.has);
  ok(withC.length >= 3 && withC.every(x => x.t === 'No classes today' && x.free === true && x.ring === '#16A34A'), 'rings: on a day with no classes, every friend with classes is free and green', withC);
  ok(none.length >= 1 && none.every(x => x.free === null && x.ring === '#CBD5E1'), 'rings: a friend with no classes added gets a grey ring, never green', none);
  const ord = await page.evaluate(() => storyOrder().map(id => PEOPLE[id].short));
  ok(none.every(x => ord.indexOf(x.n) >= ord.length - none.length), 'rings: friends with no classes added are last in the row', { ord, none });
  const line = await page.evaluate(id => { A.story(id); render(true); const el = document.querySelector('#sheet .sthead .b'); return el && getComputedStyle(el).color; }, await page.evaluate(() => TC.friends.find(id => personSecs(id).length)));
  ok(line && line !== 'rgb(22, 163, 74)', 'rings: in a story’s sheet “No classes today” is grey, not green (Tate, 2026-10-05: no green for free time); the ring on the story stays green', line);
  /* busyToday is the one place a day is filled: a work shift plugged in there makes them busy. */
  const busy = await page.evaluate(() => { const id = TC.friends.find(f => personSecs(f).length), old = busyToday;
    busyToday = f => f === id ? [{ code: 'Work', s: CLOCK.min - 10, e: CLOCK.min + 60, days: CLOCK.day }] : old(f);
    const st = status(id); UI.storyOrder = null; const ord = storyOrder(), rk = storyRank(id); busyToday = old; UI.storyOrder = null;
    const free = TC.friends.filter(f => f !== id && status(f).free === true);
    return Object.assign(st, { last: free.every(f => ord.indexOf(f) < ord.indexOf(id)), rk, end: CLOCK.min + 60 }); });
  ok(busy.free === false && /Work/.test(busy.t), 'rings: status reads busyToday (where work shifts will plug in)', busy);
  ok(busy.last && busy.rk[0] === 1 && busy.rk[1] === busy.end, 'rings: the story order reads busyToday too — someone at work comes after everyone free, ranked by when the shift ends', busy);
  /* the friend page's photo ring matches the stories */
  const pr = await page.evaluate(() => { UI.sheet = null; const out = {}; [TC.friends.find(f => !personSecs(f).length), TC.friends.find(f => personSecs(f).length)].forEach((id, i) => {
    A.openFriend(id); render(true); const el = document.querySelector('#scroll .ringav'); out[i ? 'with' : 'none'] = el && (el.getAttribute('style').match(/--rc:([^;"]+)/) || [])[1]; back(); }); return out; });
  ok(pr.none === '#CBD5E1' && pr.with === '#16A34A', 'rings: a friend’s page shows the same ring — grey for no classes added, green for a day off', pr);
  ok(log.errors.length === 0, 'rings: no page errors', log.errors);
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
  await click(page, '.secrow .addbtn >> nth=0'); await click(page, '#sheet [data-a="atPick"][data-x="A"]');
  const clashSheet = await page.locator('#sheet').innerText();
  ok(/Clashes with PHIL 3331/.test(clashSheet) && await page.locator('#sheet [data-a="atGo"]').count() === 0 && await page.locator('#sheet .at-cta button[disabled]').count() === 1, 'plans: a clash is shown with the real reason and can’t be added', clashSheet);
  await click(page, '#sheet .xbtn[data-a="closeSheet"]');
  /* Plan B from the server: one real section and one the feed no longer has. */
  await click(page, '[data-a="tab"][data-x="schedule"]');
  await click(page, '[data-a="schedTab"][data-x="plans"]');
  await click(page, '[data-a="pickPlan"][data-x="B"]');
  const t = await text(page);
  ok(!/\d+ class(es)?\b/.test(t.split('Share')[0]) && /1 section in this plan is no longer in the Fall 2026 list/.test(t) && /ECON 2303/.test(t), 'plans: plan B loads from the server and says what it can’t show', t.slice(0, 400));
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
  ok(/AVERAGE\s*4\.5/.test(t) && await page.locator('.hero .avgstar').count() === 1 && /RATINGS\s*41/.test(t) && !/POLYRATINGS|EVALUATIONS/.test(t), 'prof: rating (out of 5) + “RATINGS 41”', t.slice(0, 300));
  ok(/RETAKE\s*67%/.test(t), 'prof: retake % from TermChamp reviews');
  ok(/3 reviews/.test(t) && /Difficulty 3\/5 from 3 reviews/.test(t), 'prof: difficulty says how many reviews it stands on');
  ok(await page.locator('#scroll .bars').count() === 1, 'prof: rating spread drawn at 3 reviews');
  ok(/Fixture review text, clear lectures\./.test(t), 'prof: written review shown');
  ok(!/Fixture tag one/.test(t) && await page.locator('#scroll .tag').count() === 0 && /TermChamp reviews/.test(t), 'prof: no “did well” tags on the TermChamp reviews card, though an old review has one (2026-10-04)');
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

/* Rate tab: the score you gave is coloured like every rating (Tate, 2026-10-02: "a 5 should be green"). */
tests.rateListColors = async () => {
  const run = async score => { const o = await openApp({ rpc: Object.assign({}, FX.RPC, { my_reviews: [Object.assign({}, FX.MY_REVIEW, { score })] }) });
    await click(o.page, '[data-a="tab"][data-x="rate"]');
    const row = o.page.locator('.rscore').first();
    const got = (await row.count()) ? await row.evaluate((e, sc) => { const w = document.createElement('i'); w.style.color = RATE_DARK(rateStep(sc)); document.body.appendChild(w); const wc = getComputedStyle(w).color; w.remove();
      return { ink: getComputedStyle(e).color, star: (e.querySelector('svg') || {}).getAttribute ? e.querySelector('svg').getAttribute('fill') : null, t: e.innerText.trim(), want: RATE_DARK(rateStep(sc)), wantC: wc }; }, score) : null;
    await o.close(); return got; };
  const g = await run(5), m = await run(3.5), l = await run(2);
  ok(g && g.t === '5.0' && g.star === '#166534' && g.ink === 'rgb(22, 101, 52)', 'rate list: a 5 you gave is the big 5.0’s dark green', g);
  ok(m && m.star === m.want && m.ink === m.wantC && l && l.star === l.want && l.ink === l.wantC && m.star !== l.star && m.star !== g.star, 'rate list: 3.5 and 2 take their own half-star step of the one scale', { m, l });
};

/* Half stars (Tate, 2026-10-03: "make it so you can rate half stars"). */
tests.rateHalf = async () => {
  const { page, close, log } = await openApp({});
  await click(page, '[data-a="tab"][data-x="rate"]');
  await click(page, '.li:has-text("Ada Examplewood")');
  const geo = await page.evaluate(() => [...document.querySelectorAll('.rf .hstar')].map(c => { const r = c.getBoundingClientRect(), l = c.querySelector('.hh.l').getBoundingClientRect(), rr = c.querySelector('.hh.r').getBoundingClientRect();
    return { w: Math.round(r.width), lw: Math.round(l.width), lh: Math.round(l.height), rw: Math.round(rr.width), touch: Math.round(l.right) === Math.round(rr.left) }; }));
  ok(geo.length === 5 && geo.every(g => g.w === 44 && g.lw === 22 && g.rw === 22 && g.lh === 44 && g.touch), 'rate half: five 44px stars, each two 22×44 halves side by side', geo);
  const fit = await page.evaluate(() => { const r = document.querySelector('.rf .hstars').getBoundingClientRect(), f = document.querySelector('.rf .fcardx').getBoundingClientRect(); return { right: r.right, card: f.right, left: r.left }; });
  ok(fit.right <= fit.card && fit.left > 0, 'rate half: the star row fits inside the card', fit);
  await click(page, '.rf .hstar:nth-child(4) .hh.l');
  const st = async () => page.evaluate(() => ({ v: S.draft.stars, word: document.querySelector('.rf-sw').innerText.trim(),
    clips: [...document.querySelectorAll('.rf .hstar')].map(c => { const o = c.querySelector('.hs-on'); return o ? o.style.clipPath.replace(/\s+/g, ' ') : 'none'; }),
    fill: (document.querySelector('.rf .hstar .hs-on svg') || {}).getAttribute('fill'),
    pressed: [...document.querySelectorAll('.rf .hh[aria-pressed="true"]')].map(b => b.getAttribute('aria-label')) }));
  const RB = await page.evaluate(() => [null, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10].map(k => k && RATE_BRIGHT(k)));
  let a = await st();
  ok(a.v === 3.5 && a.word === '3.5 · Good' && a.pressed.join() === '3.5 stars', 'rate half: the left half of the 4th star is 3.5, said as “3.5 · Good”', a);
  ok(a.clips.slice(0, 3).every(c => c === 'inset(0px 0% 0px 0px)' || c === 'inset(0 0% 0 0)' || c === 'inset(0px 0%)' || c === 'inset(0px)' ) && /50%/.test(a.clips[3]) && a.clips[4] === 'none' && a.fill === RB[7], 'rate half: three full stars, half a fourth, in 3.5’s own colour on the one scale', a);
  await click(page, '.rf .hstar:nth-child(5) .hh.l');
  a = await st();
  ok(a.v === 4.5 && a.word === '4.5 · Excellent' && a.fill === RB[9], 'rate half: 4.5 is its step’s green, “Excellent”', a);
  await click(page, '.rf .hstar:nth-child(1) .hh.l');
  a = await st();
  ok(a.v === 0.5 && /50%/.test(a.clips[0]) && a.clips.slice(1).every(c => c === 'none') && a.fill === RB[1] && !(await page.locator('[data-a="postRating"]').isDisabled()), 'rate half: half a star is a rating you can post', a);
  await click(page, '.rf .hstar:nth-child(4) .hh.l');
  const labs = await page.evaluate(() => [...document.querySelectorAll('.rf .hh')].map(b => b.tagName + ':' + b.getAttribute('aria-label') + (b.tabIndex < 0 ? ':hidden' : '')));
  ok(labs.join('|') === ['0.5 stars', '1 star', '1.5 stars', '2 stars', '2.5 stars', '3 stars', '3.5 stars', '4 stars', '4.5 stars', '5 stars'].map(x => 'BUTTON:' + x).join('|'), 'rate half: all ten values are labelled buttons a keyboard or VoiceOver reaches', labs);
  await click(page, '.rf .hstar:nth-child(5) .hh.r');
  a = await st();
  ok(a.v === 5 && a.word === '5.0 · Amazing' && a.pressed.join() === '5 stars' && a.clips.every(c => !/50%/.test(c)), 'rate half: the right half of the 5th star is a full 5', a);
  await page.focus('.rf .hstar:nth-child(3) .hh.l'); await page.keyboard.press('Enter'); await tick(page, 150);
  const fo = await page.evaluate(() => ({ v: S.draft.stars, f: document.activeElement && document.activeElement.getAttribute('aria-label'), live: document.querySelector('.rf-sw').getAttribute('aria-live') }));
  ok(fo.v === 2.5 && fo.f === '2.5 stars' && fo.live === 'polite', 'rate half: a keyboard pick keeps focus on that half and the word is announced', fo);
  await click(page, '.rf .hstar:nth-child(5) .hh.l');
  const fits = [];
  for (const wd of [375, 360, 320]) { await page.setViewportSize({ width: wd, height: 760 }); await tick(page, 100);
    fits.push(await page.evaluate(wd => { const r = document.querySelector('.rf .hstars').getBoundingClientRect(), f = document.querySelector('.rf .fcardx').getBoundingClientRect(), l = document.querySelector('.rf .rf-sw').getBoundingClientRect(), h = document.querySelector('.rf .hh.l').getBoundingClientRect();
      return { wd, fits: r.right <= f.right - 8 && l.right <= r.left, oneLine: l.height < 20, hh: Math.round(h.height) }; }, wd)); }
  await page.setViewportSize({ width: 390, height: 844 }); await tick(page, 100);
  ok(fits.every(f => f.fits && f.oneLine && f.hh === 44), 'rate half: on 375, 360 and 320px phones all five stars fit beside “4.5 · Excellent” on one line', fits);
  await click(page, '.rf .hstar:nth-child(4) .hh.l');
  await click(page, '[data-a="draft"][data-x="diff"][data-y="2"]');
  await click(page, '[data-a="postRating"]'); await tick(page, 800);
  const w = log.writes.filter(x => x.table === 'reviews');
  ok(w.length === 1 && w[0].body.score === 3.5, 'rate half: posts 3.5 (the desktop already does)', w[0] && w[0].body);
  const th = await page.evaluate(() => [...document.querySelectorAll('.rf .hs')].map(h => { const o = h.querySelector('.hs-on'); return o ? o.style.clipPath : 'none'; }));
  ok(th.length === 5 && /50%/.test(th[3]) && th[4] === 'none', 'rate half: the thanks screen shows 3½ stars', th);
  ok(log.errors.length === 0, 'rate half: no page errors', log.errors);
  await close();
};

tests.rateHalfDraft = async () => {
  const { page, close } = await openApp({});
  await click(page, '[data-a="tab"][data-x="rate"]');
  await click(page, '.li:has-text("Ada Examplewood")');
  await click(page, '.rf .hstar:nth-child(3) .hh.l');
  await click(page, '[data-a="back"]'); await tick(page, 200);
  await click(page, '.li:has-text("Ada Examplewood")');
  let a = await page.evaluate(() => ({ v: S.draft.stars, p: [...document.querySelectorAll('.rf .hh[aria-pressed="true"]')].map(b => b.getAttribute('aria-label')) }));
  ok(a.v === 2.5 && a.p.join() === '2.5 stars', 'rate half: a half-star draft comes back as 2.5', a);
  await click(page, '[data-a="back"]'); await tick(page, 200);
  await page.evaluate(() => { const k = DRAFT_KEY, all = JSON.parse(localStorage.getItem(k)); Object.values(all.d).forEach(x => { x.stars = 3.7; }); localStorage.setItem(k, JSON.stringify(all)); });
  await click(page, '.li:has-text("Ada Examplewood")');
  a = await page.evaluate(() => ({ v: S.draft.stars, p: [...document.querySelectorAll('.rf .hh[aria-pressed="true"]')].map(b => b.getAttribute('aria-label')) }));
  ok(a.v === 3.5 && a.p.join() === '3.5 stars', 'rate half: an odd saved value (3.7) comes back snapped to 3.5, so what’s drawn is what posts', a);
  await click(page, '[data-a="back"]'); await tick(page, 200);
  await page.evaluate(() => { const k = DRAFT_KEY, all = JSON.parse(localStorage.getItem(k)); Object.values(all.d).forEach(x => { x.grade = 'A-'; }); localStorage.setItem(k, JSON.stringify(all)); });
  await click(page, '.li:has-text("Ada Examplewood")');
  ok(await page.evaluate(() => S.draft.grade) === null, 'no grade: a draft saved with a grade comes back without it, so nothing hidden is posted');
  await close();
};

tests.rateHalfProf = async () => {
  const reviews = FX.REVIEWS.map(r => r.professor_key === 'bram fixturesen|bus' && r.note ? Object.assign({}, r, { score: 2.5 }) : r);
  const { page, close } = await openApp({ tables: Object.assign({}, FX.TABLES, { reviews_public: reviews }) });
  await click(page, '[data-a="tab"][data-x="explore"]');
  await click(page, '[data-a="exMode"][data-x="profs"]');
  await click(page, '#exlist .pcard:has-text("Bram Fixturesen")'); await tick(page, 600);
  const r = await page.evaluate(() => { const rv = [...document.querySelectorAll('#scroll .review')].find(x => /Fixture note about Bram/.test(x.innerText)); const st = rv && rv.querySelector('.tc-revstars');
    return st && { label: st.getAttribute('aria-label'), clips: [...st.querySelectorAll('.hs')].map(h => { const o = h.querySelector('.hs-on'); return o ? o.style.clipPath : 'none'; }), fill: (st.querySelector('.hs-on svg') || {}).getAttribute('fill'), t: rv.innerText }; });
  ok(r && r.label === '2.5 of 5 stars' && /50%/.test(r.clips[2]) && r.clips[3] === 'none' && r.fill === await page.evaluate(() => RATE_BRIGHT(5)) && !/★/.test(r.t), 'rate half: a 2.5 review on a professor’s page shows 2½ stars, not three amber ★', r);
  await close();
};

tests.rateHalfEdit = async () => {
  const mine = Object.assign({}, FX.MY_REVIEW, { score: 4.5, grade: 'B' });
  const { page, close, log } = await openApp({ tables: Object.assign({}, FX.TABLES, { reviews: [mine] }), rpc: Object.assign({}, FX.RPC, { my_reviews: [mine] }) });
  await openRatings(page);
  const me = await page.evaluate(() => { const r = document.querySelector('.tc-revstars'); return r && { label: r.getAttribute('aria-label'), clips: [...r.querySelectorAll('.hs')].map(h => { const o = h.querySelector('.hs-on'); return o ? o.style.clipPath : 'none'; }), t: r.innerText }; });
  ok(me && me.label === '4.5 of 5 stars' && /50%/.test(me.clips[4]) && !/★/.test(me.t), 'rate half: your 4.5 review shows 4½ stars on Me, not five', me);
  await click(page, '[data-a="editReview"]');
  const v = await page.evaluate(() => ({ v: S.draft.stars, word: document.querySelector('.rf-sw').innerText.trim() }));
  ok(v.v === 4.5 && v.word === '4.5 · Excellent', 'rate half: editing a 4.5 opens on 4.5', v);
  await click(page, '[data-a="postRating"]'); await tick(page, 600);
  const w = log.writes.filter(x => x.table === 'reviews');
  ok(w.length === 1 && w[0].body.score === 4.5, 'rate half: saving an edit you didn’t change keeps 4.5 (it used to save 5)', w[0] && w[0].body);
  ok(w.length === 1 && w[0].body.grade === 'B', 'no grade: editing an older review keeps the grade it already had', w[0] && w[0].body);
  await close();
};

tests.rateClassName = async () => {
  const { page, close } = await openApp({});
  await click(page, '[data-a="tab"][data-x="rate"]');
  await click(page, '.li:has-text("Dov Mockridge")');
  const row = await page.locator('.rf .frow2').first().innerText();
  ok(/PHIL 3331/.test(row) && /Ethics/.test(row), 'rate: one class — its code, term and name (“Ethics”, from the desktop’s catalog names)', row);
  await close();
};

tests.rateFormat = async () => {
  const v = await (async () => { const { page, close } = await openApp({}); await tick(page, 300);
    const out = await page.evaluate(() => [[['In person'], 'In person'], [['Online'], 'Online'], [['Asynchronous'], 'Asynchronous'], [['In person', 'Online'], 'Hybrid'], [['Online', 'Asynchronous'], 'Online and asynchronous'], [[], null]]
      .map(([set, want]) => ({ set, want, got: fmtOf(set), back: fmtSet(fmtOf(set)) })));
    await close(); return out; })();
  ok(v.every(x => x.got === x.want && JSON.stringify(x.back) === JSON.stringify(x.set)), 'rate format: each combination saves as one value and reads back into the same chips (In person + Online = the desktop’s “Hybrid”)', v);
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
  ok(!/Your grade/.test(await page.locator('.rf').innerText()) && await page.locator('[data-a="draft"][data-x="grade"]').count() === 0, 'rate: no “Your grade” in the form (Tate: “take grade out”)');
  ok(!/RATE A PROFESSOR/i.test(await page.locator('.rf-head').innerText()), 'rate: no “Rate a professor” above the name');
  const cn = await page.evaluate(() => ({ shown: (document.querySelector('.rf .rf-cname') || {}).innerText || '', want: courseName(S.draft.code), code: S.draft.code }));
  ok(cn.want && cn.shown.trim() === cn.want && cn.want !== cn.code, 'rate: the class shows its name, not just its code', cn);
  const fmt = sel => page.locator(`[data-a="fmtTog"][data-x="${sel}"]`);
  ok(await page.locator('[data-a="fmtTog"]').allInnerTexts().then(x => x.join('|')) === 'In person|Online|Async', 'rate: format is In person, Online, Async');
  const fh = await page.locator('[data-a="fmtTog"]').evaluateAll(els => els.map(e => Math.round(e.getBoundingClientRect().height)));
  ok(fh.every(h => h >= 44), 'rate: format chips are 44px tall', fh);
  await click(page, '[data-a="fmtTog"][data-x="Asynchronous"]'); await click(page, '[data-a="fmtTog"][data-x="In person"]');
  ok(await fmt('In person').getAttribute('aria-pressed') === 'true' && await fmt('Asynchronous').getAttribute('aria-pressed') === 'false', 'rate: In person turns Async off (never both)');
  await click(page, '[data-a="fmtTog"][data-x="Asynchronous"]');
  ok(await fmt('Asynchronous').getAttribute('aria-pressed') === 'true' && await fmt('In person').getAttribute('aria-pressed') === 'false', 'rate: Async turns In person off');
  await click(page, '[data-a="fmtTog"][data-x="Asynchronous"]');
  await click(page, '[data-a="fmtTog"][data-x="In person"]'); await click(page, '[data-a="fmtTog"][data-x="Online"]');
  ok(await fmt('In person').getAttribute('aria-pressed') === 'true' && await fmt('Online').getAttribute('aria-pressed') === 'true', 'rate: In person and Online can both be on');
  await page.locator('#revta').fill('Fixture words from the test.');
  await click(page, '[data-a="postRating"]');
  await tick(page, 800);
  const w = log.writes.filter(x => x.table === 'reviews');
  const r = w[0] && w[0].body;
  const want = { professor_key: 'ada examplewood|bus', professor_name: 'Ada Examplewood', department: 'BUS', score: 4, difficulty: 2, format: 'Hybrid', grade: null, would_again: true, note: 'Fixture words from the test.' };
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

/* My Classes' term chips (2026-10-04): Fall 2026 · Spring 2027, like Plans' A · B · C. */
tests.myClassesTerms = async () => {
  const SP = [{ user_id: FX.ME.id, term: '2274', code: 'BUS 3346', class_nbr: '70100', section: '02', instructor: 'Dummelow, Faro', days: 'TuTh 9:40AM - 11:00AM', status: 'enrolled', wl_pos: null },
    { user_id: FX.ME.id, term: '2274', code: 'BUS 4401', class_nbr: '70500', section: '01', instructor: 'Fixturesen, Bram', days: 'MoWe 1:10PM - 2:30PM', status: 'enrolled', wl_pos: null }];
  const T = Object.assign({}, FX.TABLES, { my_sections: FX.TABLES.my_sections.concat(SP),
    saved_classes: FX.TABLES.saved_classes.concat(SP.map(r => ({ user_id: r.user_id, term: '2274', code: r.code, class_nbr: r.class_nbr, created_at: '2026-10-20T00:00:00Z', waitlist_pos: null })),
      [{ user_id: FX.ME.id, term: '2274', code: 'BUS 3411', class_nbr: null, created_at: '2026-10-20T00:00:00Z', waitlist_pos: null }]) });
  let failSpring = false, failSecs = false;
  const { page, close, log } = await openApp({ tables: T, hook: (url, m) => (m === 'GET' && /term=eq\.2274/.test(url.search) && ((failSpring && url.pathname.endsWith('/saved_classes')) || (failSecs && url.pathname.endsWith('/my_sections')))) ? { status: 500, body: JSON.stringify({ message: 'boom' }) } : null });
  await click(page, '[data-a="tab"][data-x="schedule"]');
  const chips = () => page.evaluate(() => [...document.querySelectorAll('.seg.terms button')].map(b => ({ t: b.innerText.trim(), on: b.classList.contains('on'), pr: b.getAttribute('aria-pressed') })));
  let c = await chips();
  ok(c.length === 2 && c[0].t === 'Fall 2026' && c[0].on && c[0].pr === 'true' && c[1].t === 'Spring 2027' && !c[1].on && c[1].pr === 'false', 'terms: two chips, Fall 2026 on', c);
  let t = await text(page);
  ok(/Financial Markets[\s\S]*Bram Fixturesen · Mon\/Wed 10:10–12:00/.test(t) && await page.locator('#scroll .schshare[data-x="mine"]').count() === 1, 'terms: the Fall chip is My Classes as before, with Share');
  // Spring's code is still '' → its chip reads nothing
  await click(page, '[data-a="pickMineTerm"][data-x="Spring 2027"]');
  t = await text(page); c = await chips();
  const other = () => log.reads.filter(r => /^(saved_classes|my_sections)\?/.test(r) && /term=eq\./.test(r) && !/term=eq\.2268/.test(r));
  ok(c[1].on && /Spring 2027 isn’t posted yet/.test(t) && !other().length && await page.locator('#scroll .shbtn, #scroll .schshare').count() === 0, 'terms: Spring with no confirmed code says not posted yet, reads nothing, no Share', { t: t.slice(0, 200), r: other() });
  ok(JSON.parse(await page.evaluate(() => localStorage.getItem('termchamp-app-v1'))).mineTerm === 'Spring 2027', 'terms: the chosen chip is remembered');
  // the code arrives (Oct 5): read that term's own rows
  await page.evaluate(() => { CFG.MY_TERMS[1].code = '2274'; render(true); }); await tick(page, 800);
  t = await text(page);
  ok(other().length === 2 && other().every(r => /term=eq\.2274/.test(r) && /user_id=eq\./.test(r)), 'terms: Spring reads only your saved_classes + my_sections at its own term', other());
  ok(/BUS 3346[\s\S]*Sec 02[\s\S]*Principles of Marketing[\s\S]*Faro Dummelow · Tue\/Thu 9:40–11:00/.test(t) && /BUS 4401[\s\S]*Bram Fixturesen · Mon\/Wed 1:10–2:30/.test(t), 'terms: Spring cards from your own rows', t.slice(0, 500));
  ok(!/BUS 3431|BUS 3438|Financial Markets/.test(t), 'terms: Fall’s class number 70100 (BUS 3431) never stands in for Spring’s', t.slice(0, 300));
  ok(/BUS 3411[\s\S]{0,40}No section yet[\s\S]{0,20}Finance Practicum/.test(t), 'terms: a saved Spring class with no section is listed', t.slice(-200));
  const g = await page.evaluate(() => ({ blocks: [...document.querySelectorAll('#scroll .g-b')].map(b => b.dataset.x + '|' + b.dataset.a), today: document.querySelectorAll('#scroll .g-today').length, now: document.querySelectorAll('#scroll .g-now').length }));
  ok(g.blocks.filter(x => x === 'BUS 3346|openClass').length === 2 && g.blocks.filter(x => x === 'BUS 4401|openClass').length === 2 && g.today === 0, 'terms: Spring’s week draws its classes, with no today or now marks', g);
  await click(page, '#scroll .g-day[data-x="T"]');
  ok(await page.locator('#scroll .g-now').count() === 0 && await page.locator('#scroll .g-b.live').count() === 0, 'terms: a focused day in another term has no now line or live class');
  await click(page, '#scroll .ccard[data-x="BUS 4401"]');
  ok(await page.evaluate(() => S.stack.schedule.length === 2 && cur().s === 'classDetail' && cur().p.code === 'BUS 4401'), 'terms: a Spring card opens its class', await page.evaluate(() => cur()));
  await page.evaluate(() => { S.stack.schedule = [{ s: 'schedule' }]; render(true); }); await tick(page, 200);
  // a refresh reads again; a failed read says so and can retry
  failSpring = true; const before = other().length;
  await page.evaluate(() => TC.refresh()); await tick(page, 1200);
  t = await text(page);
  ok(other().length > before && /Couldn’t load your Spring 2027 classes/.test(t) && await page.locator('#scroll [data-a="mineTermRetry"]').count() === 1, 'terms: a refresh reads Spring again; a failed read says so', t.slice(0, 300));
  failSpring = false;
  await click(page, '#scroll [data-a="mineTermRetry"]'); await tick(page, 600);
  ok(/Principles of Marketing/.test(await text(page)), 'terms: Try again reads it');
  // nothing on the account for that term
  await page.evaluate(() => { TC.termMine['2274'] = { rows: [], saved: [] }; render(true); }); await tick(page, 200);
  t = await text(page);
  ok(/No Spring 2027 classes yet[\s\S]*import your Spring 2027 schedule on termchamp\.com/.test(t), 'terms: an empty later term says how to add it', t.slice(0, 300));
  // a stale read that lands after a refresh never wins
  const stale = await page.evaluate(async () => { TC.termMine = {}; const p = loadTermMine('2274'); TC.termMine = {}; TC.termGen++; TC.termMine['2274'] = { rows: [], saved: ['ZZZ 1000'] }; await p; return TC.termMine['2274'].saved; });
  ok(JSON.stringify(stale) === '["ZZZ 1000"]', 'terms: a read from before a refresh is dropped', stale);
  // a my_sections error is an error, not "No section yet"
  failSecs = true; await page.evaluate(() => { delete TC.termMine['2274']; render(true); }); await tick(page, 600);
  ok(/Couldn’t load your Spring 2027 classes/.test(await text(page)), 'terms: a failed my_sections read says so', (await text(page)).slice(0, 200));
  failSecs = false;
  // back to Fall: unchanged, and the current term is stored as null (so the Oct 5 flip lands everyone on Spring)
  await click(page, '[data-a="pickMineTerm"][data-x="Fall 2026"]');
  ok(/Financial Markets/.test(await text(page)) && (await chips())[0].on && JSON.parse(await page.evaluate(() => localStorage.getItem('termchamp-app-v1'))).mineTerm === null, 'terms: back to Fall, stored as the current term');
  // the Oct 5 flip: TERM/TERM_LABEL move to Spring; Spring takes TERM, Fall keeps its code
  const flip = await page.evaluate(() => { const o = [CFG.TERM, CFG.TERM_LABEL, CFG.MY_TERMS[1].code]; CFG.TERM = '2274'; CFG.TERM_LABEL = 'Spring 2027'; CFG.MY_TERMS[1].code = ''; const r = myTerms(); CFG.TERM = o[0]; CFG.TERM_LABEL = o[1]; CFG.MY_TERMS[1].code = o[2]; return r; });
  ok(JSON.stringify(flip) === JSON.stringify([{ code: '2268', label: 'Fall 2026' }, { code: '2274', label: 'Spring 2027' }]), 'terms: flipping TERM to Spring fills Spring’s chip with TERM; Fall keeps 2268', flip);
  ok(!log.errors.length, 'terms: no page errors', log.errors);
  await close();
};
tests.schedule = async () => {
  const { page, close, log } = await openApp({});
  await click(page, '[data-a="tab"][data-x="schedule"]');
  let t = await text(page);
  ok(/My Classes/.test(t) && /BUS 2201/.test(t), 'schedule: my classes');
  const bar = async () => page.evaluate(() => { const b = [...document.querySelectorAll('.regbar')].find(e => e.offsetParent); return b ? { text: b.innerText.trim(), n: b.children.length, count: /\d+\s*class/i.test(b.innerText) } : null; });
  let rb = await bar();
  ok(rb === null && await page.locator('#scroll .schhdr .schshare[data-x="mine"]').count() === 1, 'schedule: My Classes has no bar (Share is top right) — no class count', rb);
  await page.evaluate(() => { S.schedTab = 'plans'; S.plan = 'A'; render(); }); await tick(page, 200);
  rb = await bar();
  ok(rb && /^(Friends can see|Only you)$/.test(rb.text) && rb.n === 1 && !rb.count, 'schedule: a plan’s bar is who can see it, alone — no class count', rb);
  await page.evaluate(() => { S.schedTab = 'mine'; render(); }); await tick(page, 200);
  ok(/BUS 2201[\s\S]*No section yet/.test(t), 'schedule: a saved class without a section is listed');
  ok(/Financial Markets[\s\S]*Bram Fixturesen · Mon\/Wed 10:10–12:00/.test(t), 'schedule: section line from the seat feed', t.slice(0, 600));
  ok(/Avery[\s\S]*in your section/.test(t), 'schedule: friends in my section');
  await click(page, '[data-a="schedTab"][data-x="past"]');
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
  ok(/FRIEND REQUESTS\s*1[\s\S]*Morgan Nobody/i.test(await page.locator('#fbody').innerText()), 'requests: incoming request shown at the top of Friends, no chip to tap');
  await click(page, '[data-a="acceptReq"]');
  await tick(page, 600);
  const w = log.writes.filter(x => x.table === 'friend_requests');
  ok(w.length === 1 && w[0].m === 'PATCH' && w[0].body.status === 'accepted' && /id=eq\.990/.test(w[0].query), 'requests: accept updates that request by id', w);
  await page.locator('.pym [data-a="addFriend"]').first().dblclick();
  await tick(page, 600);
  const w2 = log.writes.filter(x => x.table === 'friend_requests' && x.m === 'POST');
  ok(w2.length === 1 && w2[0].body.to_user === FX.SUGGESTED.id && w2[0].body.from_user === FX.ME.id && w2[0].body.status === 'pending', 'requests: Add (even double-tapped) sends ONE pending request', w2);
  ok(/Requested/.test(await page.locator('.pym').first().innerText()), 'requests: button turns to Requested');
  ok(log.errors.length === 0, 'requests: no page errors', log.errors);
  await close();
};

/* Friends (Tate, 2026-09-30): one search for everyone, Instagram-style; Invite friends opens the link
   and a QR code; a red count on the tab while requests wait. */
tests.friendsSearch = async () => {
  /* find_people (sql/professify-find-people.sql) returns id, display_name, username — nothing else. */
  const rpc = Object.assign({}, FX.RPC, { find_people: [{ id: FX.SUGGESTED.id, display_name: FX.SUGGESTED.display_name, username: FX.SUGGESTED.username }, { id: FX.FRIENDS[0].id, display_name: FX.FRIENDS[0].display_name, username: FX.FRIENDS[0].username }] });
  const { page, close, log } = await openApp({ rpc });
  await page.waitForFunction(() => typeof TC === 'object' && TC.ready, null, { timeout: 8000 });
  const tab = page.locator('[data-a="tab"][data-x="friends"]');
  ok((await tab.locator('.tbadge').innerText()).trim() === '1' && (await tab.getAttribute('aria-label')) === 'Friends, 1 friend request', 'friends tab: a red count of waiting requests, and the tab says so', await tab.innerHTML());
  const red = await tab.locator('.tbadge').evaluate(e => getComputedStyle(e).backgroundColor);
  ok(red === 'rgb(220, 38, 38)', 'friends tab: the count is red', red);
  await click(page, '[data-a="tab"][data-x="friends"]');
  ok(await page.locator('#fq').getAttribute('placeholder') === 'Find friends by name or @handle' && await page.locator('.plusbtn').count() === 0, 'friends: one full-width search at the top, no + button');
  const sb = await page.locator('.fsearch').boundingBox(), ib = await page.locator('.fhdr .invpill').boundingBox(), tb = await page.locator('.fhdr .title').boundingBox(), hb = await page.locator('.fhdr').boundingBox();
  ok(sb && ib && tb && ib.y + ib.height <= sb.y && Math.abs((ib.y + ib.height / 2) - (tb.y + tb.height / 2)) < 8 && 390 - (ib.x + ib.width) <= 20 && ib.width < 140 && ib.height >= 44 && /^Invite$/.test((await page.locator('.invpill').innerText()).trim()) && await page.locator('.invbtn').count() === 0, 'friends: Invite is a small button at the top right, beside the title — nothing big between the title and the search', { sb, ib, tb });
  ok(sb.y - (hb.y + hb.height) < 12, 'friends: the search sits right under the title row', { sb, hb });
  const secsBefore = await page.evaluate(id => personSecs(id).length, FX.FRIENDS[0].id);
  await page.locator('#fq').pressSequentially('a'); await tick(page, 600);
  ok(!log.reads.some(r => /rpc:(find_people|search_people)/.test(r)), 'friends search: one letter searches only your friends, not the server');
  await page.locator('#fq').pressSequentially('v');
  const early = await page.evaluate(() => ({ busy: UI.fPeople && UI.fPeople.res === 'busy' && UI.fPeople.q === 'av', shows: /Searching TermChamp/.test(document.getElementById('fbody').innerText) }));
  ok(!log.reads.some(r => /rpc:(find_people|search_people)/.test(r)) && early.busy && early.shows, 'friends search: shows “Searching…” and waits for a pause before asking the server', early);
  await tick(page, 700);
  const t = await page.locator('#fbody').innerText();
  ok(log.reads.filter(r => r === 'rpc:find_people').length === 1 && !log.reads.includes('rpc:search_people'), 'friends search: asks find_people (name or @username) once after the pause', log.reads.filter(r => /rpc:/.test(r)));
  ok(/@psuggest/.test(await page.locator('#fbody .fsr').innerText()), 'friends search: a stranger shows with their @username');
  ok(/FRIENDS[\s\S]*Avery Quill[\s\S]*MORE PEOPLE[\s\S]*Pat Suggestia/i.test(t) && (t.match(/Avery Quill/g) || []).length === 1, 'friends search: your friends first, then everyone else — a friend the server also returns shows once', t);
  ok(!/^CHATS$/m.test(t) && await page.evaluate(() => document.activeElement && document.activeElement.id) === 'fq', 'friends search: the list gives way to results, and the box keeps focus', t);
  const secsAfter = await page.evaluate(id => personSecs(id).length, FX.FRIENDS[0].id);
  ok(secsBefore > 0 && secsAfter === secsBefore, 'friends search: a search result never wipes a friend’s classes', { secsBefore, secsAfter });
  await click(page, '#fbody .fsr [data-a="addFriend"]');
  const w = log.writes.filter(x => x.table === 'friend_requests' && x.m === 'POST');
  ok(w.length === 1 && w[0].body.to_user === FX.SUGGESTED.id && w[0].body.from_user === FX.ME.id, 'friends search: Add sends the real request', w);
  ok(/Requested/.test(await page.locator('#fbody .fsr').innerText()), 'friends search: the row turns to Requested');
  ok(await page.locator('.fqx').isVisible(), 'friends search: a clear (x) button while there is text');
  await click(page, '.fqx');
  ok(await page.locator('#fq').inputValue() === '' && !(await page.locator('.fqx').isVisible()) && await page.evaluate(() => document.activeElement && document.activeElement.id) === 'fq', 'friends search: x clears the box, hides itself and keeps the keyboard up');
  ok(/CHATS[\s\S]*Fixture Study Group/i.test(await page.locator('#fbody').innerText()), 'friends search: clearing the box brings the chats back');
  await page.locator('#fq').fill('study'); await tick(page, 800);
  ok(/GROUP CHATS[\s\S]*Fixture Study Group/i.test(await page.locator('#fbody').innerText()), 'friends search: group chats that match are found too');
  await page.locator('#fq').fill(''); await tick(page);
  await click(page, '.invpill');
  const url = await page.locator('#sheet .invurl').innerText();
  ok(url === 'https://termchamp.com/invite?add=' + FX.ME.id + '&to=app', 'invite: the desktop’s own link (/invite?add=<your id>), not ?invite=<username>, opening the phone app (to=app)', url);
  const qr = await page.locator('#sheet .invqr svg').count(), qrb = await page.locator('#sheet .invqr').boundingBox();
  ok(qr === 1 && qrb && qrb.width >= 200, 'invite: a QR code, big enough to scan', qrb);
  ok(/Copy link/.test(await page.locator('#sheet').innerText()) && /Share link/.test(await page.locator('#sheet').innerText()), 'invite: Copy link and Share link');
  await click(page, '#sheet .xbtn[data-a="closeSheet"]');
  await click(page, '[data-a="acceptReq"]'); await tick(page, 600);
  ok(await page.locator('[data-a="tab"][data-x="friends"] .tbadge').count() === 0, 'friends tab: the count goes once the request is answered');
  await page.evaluate(() => { TC.requests = Array.from({ length: 12 }, (_, i) => 'r' + i); render(true); });
  ok((await page.locator('[data-a="tab"][data-x="friends"] .tbadge').innerText()).trim() === '9+' && (await page.locator('[data-a="tab"][data-x="friends"]').getAttribute('aria-label')) === 'Friends, 12 friend requests', 'friends tab: past nine it reads 9+, and the label says the real number');
  await page.evaluate(() => { TC.requests = []; render(true); });
  ok(log.errors.length === 0, 'friends search: no page errors', log.errors);
  await close();
  /* Before sql/professify-find-people.sql runs: find_people is missing, so the phone uses the
     desktop's search_people (which returns instagram_handle, not username) — and asks find_people
     only once. */
  const NOFN = { __error: { code: 'PGRST202', message: 'Could not find the function public.find_people(q) in the schema cache' } };
  const old = await openApp({ rpc: Object.assign({}, FX.RPC, { find_people: NOFN, search_people: [{ id: FX.SUGGESTED.id, display_name: FX.SUGGESTED.display_name, instagram_handle: 'pat.ig' }] }) });
  await old.page.waitForFunction(() => typeof TC === 'object' && TC.ready, null, { timeout: 8000 });
  await click(old.page, '[data-a="tab"][data-x="friends"]');
  await old.page.locator('#fq').pressSequentially('pat'); await tick(old.page, 900);
  await old.page.locator('#fq').pressSequentially('s'); await tick(old.page, 900);
  const ot = await old.page.locator('#fbody').innerText();
  ok(/Pat Suggestia/.test(ot) && !/Couldn’t search/.test(ot), 'friends search: before the SQL runs, the desktop’s search_people still finds people', ot);
  ok(old.log.reads.filter(r => r === 'rpc:find_people').length === 1 && old.log.reads.filter(r => r === 'rpc:search_people').length === 2, 'friends search: a missing find_people is asked once, then skipped', old.log.reads.filter(r => /rpc:/.test(r)));
  await old.close();
  const half = await openApp({ rpc: Object.assign({}, FX.RPC, { find_people: NOFN, search_people: [], find_profile_by_handle: { __error: { message: 'boom', code: '500' } } }) });
  await half.page.waitForFunction(() => typeof TC === 'object' && TC.ready, null, { timeout: 8000 });
  await click(half.page, '[data-a="tab"][data-x="friends"]');
  await half.page.locator('#fq').pressSequentially('@psug'); await tick(half.page, 900);
  const ht = await half.page.locator('#fbody').innerText();
  ok(/Couldn’t search right now/.test(ht) && !/No one/.test(ht), 'friends search: a failed @username lookup is never read as “no one”', ht);
  await half.close();
  const bad = await openApp({ rpc: Object.assign({}, FX.RPC, { find_people: { __error: { message: 'boom', code: '500' } } }) });
  await bad.page.waitForFunction(() => typeof TC === 'object' && TC.ready, null, { timeout: 8000 });
  await click(bad.page, '[data-a="tab"][data-x="friends"]');
  await bad.page.locator('#fq').pressSequentially('pat'); await tick(bad.page, 900);
  const bt = await bad.page.locator('#fbody').innerText();
  ok(/Couldn’t search right now/.test(bt) && /Try again/.test(bt) && !/No one/.test(bt), 'friends search: a failed search says so — never “no one on TermChamp”', bt);
  await bad.close();
};

/* Friends is one list (Tate, 2026-10-03): requests, then chats, then the friends you haven't chatted with. */
/* Groups (Tate, 2026-10-03): two smaller photos for a group; "+ New group" on the Chats label in Invite's pink. */
tests.groups = async () => {
  const { page, close, log } = await openApp({});
  await click(page, '[data-a="tab"][data-x="friends"]'); await tick(page, 300);
  const av = await page.evaluate(() => { const row = [...document.querySelectorAll('.thread')].find(r => /Fixture Study Group/.test(r.innerText)); const g = row && row.querySelector('.gav');
    return g && { n: g.querySelectorAll('.av').length, box: Math.round(g.getBoundingClientRect().width), sizes: [...g.querySelectorAll('.av')].map(a => Math.round(a.getBoundingClientRect().width)), ring: getComputedStyle(g.querySelector('.gav-f')).boxShadow, sq: row.querySelectorAll('.sq').length }; });
  ok(av && av.n === 2 && av.box === 48 && av.sizes.every(x => x === 33) && /255, 255, 255/.test(av.ring) && av.sq === 0, 'groups: a group shows two smaller photos, the front one ringed — no initials square', av);
  const b = await page.evaluate(() => { const e = document.querySelector('.fs-hrow .ngbtn'); if (!e) return null; const r = e.getBoundingClientRect(), c = getComputedStyle(e), hit = y => { const t = document.elementFromPoint(r.left + r.width / 2, y); return !!(t && t.closest('.ngbtn')); };
    return { t: e.innerText.trim(), bg: c.backgroundColor, fg: c.color, label: e.closest('.fs-hrow').innerText.trim().split('\n')[0], top: hit(r.top - 5), bot: hit(r.bottom + 5) }; });
  ok(b && b.t === 'New group' && b.bg === 'rgba(0, 0, 0, 0)' && b.fg === 'rgb(204, 31, 108)' && /chats/i.test(b.label), 'groups: “+ New group” sits on the Chats label as plain pink text — no pill', b);
  ok(b && b.top && b.bot, 'groups: its tap area reaches 44px', b);
  await click(page, '.ngbtn'); await tick(page, 200);
  await page.fill('#ngTitle', 'Midterm crew');
  const st = () => page.evaluate(() => { const go = document.querySelector('#sheet [data-a="ngCreate"]'); return { dis: go.disabled, t: go.innerText.trim(), chips: [...document.querySelectorAll('#sheet .ng-chip')].map(c => c.innerText.trim()), rows: document.querySelectorAll('#sheet .ng-row').length, on: document.querySelectorAll('#sheet .ng-row[aria-pressed="true"]').length }; });
  let a = await st();
  const nFr = await page.evaluate(() => TC.friends.filter(id => PEOPLE[id]).length);
  ok(a.dis && a.t === 'Pick 2 more friends' && a.rows === nFr && a.chips.length === 0, 'groups: the sheet lists your friends, and Create waits for 2', a);
  await click(page, '#sheet .ng-row >> nth=0'); a = await st();
  ok(a.dis && a.t === 'Pick 1 more friend' && a.chips.length === 1, 'groups: one picked — one more to go', a);
  await click(page, '#sheet .ng-row >> nth=2'); a = await st();
  ok(!a.dis && a.t === 'Create group · 3 people' && a.chips.length === 2 && a.on === 2, 'groups: two picked — Create says 3 people', a);
  await click(page, '#sheet .ng-chip >> nth=1'); a = await st();
  ok(a.chips.length === 1 && a.on === 1 && a.dis, 'groups: tapping a chip takes them out', a);
  await page.focus('#ngq'); await page.keyboard.type('quinn'); await tick(page, 100);
  ok(await page.evaluate(() => document.activeElement && document.activeElement.id) === 'ngq' && await page.inputValue('#ngTitle') === 'Midterm crew', 'groups: typing keeps focus in the search, and the name typed first survives the picks');
  ok(await page.locator('#sheet .ng-row').count() === 1 && /Quinn/.test(await page.locator('#sheet .ng-row').innerText()), 'groups: search narrows your friends');
  await click(page, '#sheet .ng-row'); await page.fill('#ngq', ''); await tick(page, 100);
  const picked = await page.evaluate(() => UI.ng.picked.slice());
  await page.evaluate(() => { A.ngCreate(); A.ngCreate(); }); await tick(page, 800);
  ok(log.writes.filter(w => w.table === 'conversations' && w.m === 'POST').length === 1, 'groups: a double tap on Create makes one group');
  const conv = log.writes.find(w => w.table === 'conversations' && w.m === 'POST'), mem = log.writes.find(w => w.table === 'conversation_members' && w.m === 'POST');
  const me = await page.evaluate(() => TC.user.id);
  ok(conv && conv.body.kind === 'group' && conv.body.title === 'Midterm crew' && conv.body.created_by === me, 'groups: creates a group conversation with its name', conv && conv.body);
  ok(mem && Array.isArray(mem.body) && mem.body.length === 3 && [me].concat(picked).every(u => mem.body.some(r => r.user_id === u)) && mem.body.every(r => r.conversation_id === mem.body[0].conversation_id), 'groups: you and both friends are added in one insert', mem && mem.body);
  const on = await page.evaluate(() => ({ s: cur().s, gav: document.querySelectorAll('.chathdr .gav').length, name: (document.querySelector('.chathdr') || {}).innerText, sheet: !!UI.sheet }));
  ok(on.s === 'chat' && on.gav === 1 && /Midterm crew/.test(on.name) && !on.sheet, 'groups: the new group opens, with the two-photo picture', on);
  ok(log.errors.length === 0, 'groups: no page errors', log.errors);
  await close();
};

tests.groupsRefused = async () => {
  let refuse = true;
  const hook = (url, m) => refuse && url.pathname === '/rest/v1/conversation_members' && m === 'POST' ? { status: 403, body: JSON.stringify({ code: '42501', message: 'new row violates row-level security policy for table "conversation_members"' }) } : null;
  const { page, close, log } = await openApp({ hook });
  await click(page, '[data-a="tab"][data-x="friends"]'); await tick(page, 300);
  await click(page, '.ngbtn'); await click(page, '#sheet .ng-row >> nth=0'); await click(page, '#sheet .ng-row >> nth=1');
  const bad = await page.evaluate(() => WF_WORDS[0]);
  await page.fill('#ngTitle', 'the ' + bad + ' crew');
  await click(page, '#sheet [data-a="ngCreate"]'); await tick(page, 300);
  ok(!log.writes.some(w => w.table === 'conversations') && /can’t be in one/.test(await page.locator('#sheet .tc-err').innerText()), 'groups: a blocked word in the name is stopped before anything is sent');
  await page.fill('#ngTitle', ''); await click(page, '#sheet [data-a="ngCreate"]'); await tick(page, 800);
  const err = await page.locator('#sheet .tc-err').innerText().catch(() => '');
  ok(/^Couldn’t add everyone, so the group wasn’t made/.test(err) && await page.evaluate(() => UI.sheet && UI.sheet.type === 'newGroup' && cur().s !== 'chat'), 'groups: a refused member insert says so and keeps the sheet', err);
  refuse = false; await click(page, '#sheet [data-a="ngCreate"]'); await tick(page, 800);
  ok(log.writes.filter(w => w.table === 'conversations' && w.m === 'POST').length === 1 && await page.evaluate(() => cur().s === 'chat'), 'groups: trying again reuses the first try’s group instead of making another', log.writes.filter(w => w.table === 'conversations').map(w => w.m));
  const sh = await page.evaluate(() => shTargets().filter(x => x.k.startsWith('t:')).map(x => /class="gav"/.test(x.av)));
  ok(sh.length && sh.every(Boolean), 'groups: Send to a friend shows groups with the two-photo picture', sh);
  await click(page, '[data-a="back"]'); await click(page, '[data-a="tab"][data-x="friends"]');
  await page.evaluate(() => { TC.threads = []; render(true); }); await tick(page, 200);
  ok(await page.locator('.ngbtn').count() === 1 && /^CHATS/i.test(await page.locator('.fs-hrow').innerText()), 'groups: with no chats yet, the Chats label and New group still show');
  const lone = await page.evaluate(() => groupAv({ id: 'x', kind: 'group', members: [TC.user.id], senders: [] }, 48));
  ok(!/gav-b/.test(lone) && /noph/.test(lone), 'groups: a group with nobody else left shows one grey circle, never you twice');
  await page.evaluate(() => { TC.friends = TC.friends.slice(0, 1); render(true); }); await tick(page, 200);
  ok(await page.locator('.ngbtn').count() === 0, 'groups: with fewer than 2 friends there is no New group');
  await close();
};

tests.friendsOneList = async () => {
  const { page, close, log } = await openApp({});
  await page.waitForFunction(() => typeof TC === 'object' && TC.ready, null, { timeout: 8000 });
  await click(page, '[data-a="tab"][data-x="friends"]'); await tick(page, 400);
  const heads = await page.locator('#fbody .fs-h').evaluateAll(es => es.map(e => e.innerText.replace(/\s+/g, ' ').trim()));
  ok(await page.locator('#fbody .chips, [data-a="fFilter"]').count() === 0 && !/Class chats/i.test(await text(page)), 'one list: no filter chips, no Class chats', heads);
  ok(heads.length >= 3 && /^FRIEND REQUESTS ?1$/i.test(heads[0]) && /^CHATS( New group)?$/i.test(heads[1]) && /^FRIENDS$/i.test(heads[2]), 'one list: requests first, then chats, then friends', heads);
  const badge = await page.locator('.freq-h .n').evaluate(e => getComputedStyle(e).backgroundColor);
  ok(badge === 'rgb(220, 38, 38)', 'one list: the request count is red', badge);
  const chatNames = await page.locator('#fbody .thread .nm').allInnerTexts();
  const exp = await page.evaluate(() => TC.threads.filter(t => t.last || t.kind !== 'direct').map(threadName));
  ok(exp.length >= 2 && JSON.stringify(chatNames) === JSON.stringify(exp) && await page.evaluate(() => TC.threads.some(t => t.kind === 'group')), 'one list: every chat, newest first, group chats included', { chatNames, exp });
  const avery = FX.FRIENDS[0].id;
  const listed = () => page.locator('#fbody .card.list:not(.freq) [data-a="openFriend"]').evaluateAll(es => es.map(e => e.dataset.x));
  let ids = await listed();
  const others = await page.evaluate(a => TC.friends.filter(f => f !== a), avery);
  ok(!ids.includes(avery) && ids.length === others.length && others.every(f => ids.includes(f)), 'one list: a friend you have chatted with is under Chats only; every other friend is under Friends', { ids, others });
  const names = await page.evaluate(ids => ids.map(i => PEOPLE[i].name), ids);
  ok(names.length >= 2 && JSON.stringify(names) === JSON.stringify(names.slice().sort((a, b) => a.localeCompare(b))), 'one list: friends A–Z', names);
  /* A 1:1 that never had a message is not a chat: that friend stays under Friends. */
  const f3 = FX.FRIENDS[3].id;
  await page.evaluate(id => { TC.threads.push({ id: 'empty1', kind: 'direct', title: null, last_at: '2026-09-28T00:00:00Z', members: [TC.user.id, id], last: null }); render(true); }, f3);
  ids = await listed();
  ok(ids.includes(f3) && await page.locator('#fbody .thread[data-x="empty1"]').count() === 0, 'one list: a 1:1 with no messages yet is not a chat', ids);
  await page.evaluate(() => { TC.requests = []; render(true); });
  ok(await page.locator('#fbody .freq').count() === 0 && !/FRIEND REQUESTS/i.test(await page.locator('#fbody').innerText()), 'one list: with no requests, no requests card');
  ok(log.errors.length === 0, 'one list: no page errors', log.errors);
  await close();
};

/* A chat opens on its newest message, and a new one keeps you there — unless you scrolled up (2026-10-03). */
tests.chatOpensAtEnd = async () => {
  const conv = FX.CONVS[0].id;
  const many = Array.from({ length: 40 }, (_, i) => ({ id: 100 + i, conversation_id: conv, sender: i % 2 ? FX.ME.id : FX.FRIENDS[0].id, kind: 'text', body: 'Older line ' + i, payload: null, created_at: new Date(Date.parse('2026-09-20T10:00:00Z') + i * 3600e3).toISOString() }));
  const { page, close, log } = await openApp({ tables: Object.assign({}, FX.TABLES, { messages: FX.TABLES.messages.concat(many) }) });
  await page.waitForFunction(() => typeof TC === 'object' && TC.ready, null, { timeout: 8000 });
  const pos = () => page.evaluate(() => { const sc = document.getElementById('scroll'); return { gap: Math.round(sc.scrollHeight - sc.scrollTop - sc.clientHeight), top: Math.round(sc.scrollTop), h: sc.scrollHeight, last: (document.querySelector('#scroll .msgs .msg:last-of-type') || {}).innerText }; });
  await click(page, '[data-a="tab"][data-x="friends"]');
  await click(page, `#fbody .thread[data-x="${conv}"]`); await tick(page, 900);
  let p = await pos();
  ok(p.h > 1500 && p.gap <= 2 && /Fixture reply from Avery/.test(p.last || ''), 'chat: opens on the newest message, not the top', p);
  await page.evaluate(id => { const r = TC.rows[id], m = Object.assign({}, r[r.length - 1], { id: 999, body: 'A new one', created_at: new Date().toISOString() }); r.push(m); render(true); }, conv); await tick(page, 200);
  p = await pos();
  ok(p.gap <= 2 && /A new one/.test(p.last || ''), 'chat: at the bottom, a new message keeps you at the newest', p);
  await page.evaluate(() => { document.getElementById('scroll').scrollTop = 200; }); await tick(page, 100);
  await page.evaluate(id => { const r = TC.rows[id], m = Object.assign({}, r[r.length - 1], { id: 1000, body: 'Another', created_at: new Date().toISOString() }); r.push(m); render(true); }, conv); await tick(page, 200);
  p = await pos();
  ok(p.top === 200, 'chat: scrolled up to read, a new message does not move you', p);
  await click(page, '[data-a="back"]'); await click(page, `#fbody .thread[data-x="${conv}"]`); await tick(page, 900);
  p = await pos();
  ok(p.gap <= 2, 'chat: opening it again also lands on the newest message', p);
  ok(log.errors.length === 0, 'chat: no page errors', log.errors);
  await close();
};

/* Tap anywhere in a day to widen it; a class block still opens the class (Tate, 2026-10-03). */
tests.dayColumnTap = async () => {
  const { page, close, log } = await openApp({});
  await page.waitForFunction(() => TC.ready && TC.seatsLoaded && document.querySelectorAll('.hfeed .fcard').length === 5, null, { timeout: 8000 });
  const A = FX.FRIENDS[0].id, card = '#hf-' + A;
  /* a point in the given day's column that is not on any class block */
  const emptySpot = (scope, i) => page.evaluate(([scope, i]) => { const col = document.querySelectorAll(scope + ' .g-col')[i], r = col.getBoundingClientRect();
    for (let y = r.bottom - 3; y > r.top + 3; y -= 4) { const x = r.left + r.width / 2, el = document.elementFromPoint(x, y); if (el && el.closest('.g-col') === col && !el.closest('.g-b')) return { x, y, day: col.dataset.x, want: col.closest('.grid').querySelectorAll('.g-head .g-day')[i].dataset.x }; }
    return null; }, [scope, i]);
  await page.evaluate(c => document.querySelector(c).scrollIntoView({ block: 'center' }), card); await tick(page, 200);
  let pt = await emptySpot(card, 2);
  ok(pt && pt.day && pt.day === pt.want, 'day tap: the day column carries its own day (the header above it)', pt);
  await page.mouse.click(pt.x, pt.y); await tick(page, 300);
  ok(await page.evaluate(id => S.homeDays[id], A) === pt.want && await page.locator(card + ' .g-col.on').count() === 1 && !(await page.evaluate(() => UI.sheet)), 'day tap: tapping an empty part of a day widens that day (only on this card)', await page.evaluate(id => S.homeDays[id], A));
  const other = await page.evaluate(() => Object.keys(S.homeDays).filter(k => S.homeDays[k]).length);
  ok(other === 1, 'day tap: other cards keep their own day', other);
  pt = await emptySpot(card, [...'MTWRF'].indexOf(pt.day) >= 0 ? await page.evaluate(c => [...document.querySelectorAll(c + ' .g-col')].findIndex(e => e.classList.contains('on')), card) : 2);
  await page.mouse.click(pt.x, pt.y); await tick(page, 300);
  ok(!(await page.evaluate(id => S.homeDays[id], A)), 'day tap: tapping the open day again closes it', await page.evaluate(id => S.homeDays[id], A));
  const b = await page.locator(card + ' .g-b').first().boundingBox();
  await page.mouse.click(b.x + b.width / 2, b.y + Math.min(8, b.height / 2)); await tick(page, 400);
  ok(await page.evaluate(() => UI.sheet && UI.sheet.type) === 'sec' && !(await page.evaluate(id => S.homeDays[id], A)), 'day tap: tapping a class block opens the class, not the day', await page.evaluate(() => UI.sheet));
  await click(page, '#sheet .xbtn');
  /* Schedule: the same */
  await click(page, '[data-a="tab"][data-x="schedule"]'); await tick(page, 400);
  pt = await emptySpot('#scroll .card', 1);
  await page.mouse.click(pt.x, pt.y); await tick(page, 300);
  ok(await page.evaluate(() => S.schedDay) === pt.want, 'day tap: on My Classes too', { want: pt.want, got: await page.evaluate(() => S.schedDay) });
  /* a friend's page (Sky has no 1:1 chat, so she is under Friends) */
  const sky = FX.FRIENDS[2].id;
  await click(page, '[data-a="tab"][data-x="friends"]'); await click(page, '.li:has-text("Sky Placeholder")'); await tick(page, 300);
  pt = await emptySpot('#scroll .card.fweek', 0);
  await page.mouse.click(pt.x, pt.y); await tick(page, 300);
  ok(pt.day === pt.want && await page.evaluate(k => S.homeDays[k], 'f:' + sky) === pt.want && await page.locator('#scroll .card.fweek .g-col.on').count() === 1, 'day tap: on a friend’s week too', { pt, got: await page.evaluate(() => S.homeDays) });
  ok(log.errors.length === 0, 'day tap: no page errors', log.errors);
  await close();
};

/* A message arriving live never pulls you down while you read older ones (review, 2026-10-03). */
tests.chatLiveMessage = async () => {
  const conv = FX.CONVS[0].id;
  const many = Array.from({ length: 40 }, (_, i) => ({ id: 200 + i, conversation_id: conv, sender: FX.FRIENDS[0].id, kind: 'text', body: 'Old ' + i, payload: null, created_at: new Date(Date.parse('2026-09-20T10:00:00Z') + i * 3600e3).toISOString() }));
  const { page, close, log } = await openApp({ tables: Object.assign({}, FX.TABLES, { messages: FX.TABLES.messages.concat(many) }) });
  await page.waitForFunction(() => typeof TC === 'object' && TC.ready && typeof TC.onMessage === 'function', null, { timeout: 8000 });
  await click(page, '[data-a="tab"][data-x="friends"]'); await click(page, `#fbody .thread[data-x="${conv}"]`); await tick(page, 900);
  const gap = () => page.evaluate(() => { const sc = document.getElementById('scroll'); return Math.round(sc.scrollHeight - sc.scrollTop - sc.clientHeight); });
  const live = (id, body) => page.evaluate(([conv, id, body, from]) => TC.onMessage({ new: { id, conversation_id: conv, sender: from, kind: 'text', body, payload: null, created_at: new Date().toISOString() } }), [conv, id, body, FX.FRIENDS[0].id]);
  await live(5001, 'Live at the bottom'); await tick(page, 200);
  ok(await gap() <= 2 && /Live at the bottom/.test(await page.locator('#scroll .msgs').innerText()), 'live: at the bottom, a new message shows and you stay at the newest');
  await page.evaluate(() => { document.getElementById('scroll').scrollTop = 150; }); await tick(page, 100);
  await live(5002, 'Live while reading'); await tick(page, 200);
  ok(await page.evaluate(() => Math.round(document.getElementById('scroll').scrollTop)) === 150, 'live: scrolled up to read, a new message does not move you');
  ok(log.errors.length === 0, 'live: no page errors', log.errors);
  await close();
};

/* Chats: like, delete for me, report, delete a chat, live class / professor cards (Tate, 2026-10-03). */
const CHAT_X = () => {
  const conv = FX.CONVS[0].id, AV = FX.FRIENDS[0].id, crn = FX.seat('BUS 3431', '02').class_nbr;
  const extra = [
    { id: 4, conversation_id: conv, sender: AV, kind: 'class', body: null, payload: { code: 'BUS 3431', name: 'Business Finance', section: '02', crn, prof: 'Bram Fixturesen', days: 'TuTh 8:10 AM' }, created_at: '2026-09-27T20:05:00Z' },
    { id: 5, conversation_id: conv, sender: AV, kind: 'professor', body: null, payload: { key: 'ada examplewood|bus', name: 'Ada Examplewood' }, created_at: '2026-09-27T20:06:00Z' },
    { id: 6, conversation_id: conv, sender: AV, kind: 'professor', body: null, payload: { key: 'zed nobody|math', name: 'Zed Nobody' }, created_at: '2026-09-27T20:07:00Z' },
  ];
  const T = JSON.parse(JSON.stringify(FX.TABLES));
  T.messages = T.messages.concat(extra);
  T.conversations = T.conversations.map(c => c.id === conv ? Object.assign({}, c, { last_at: '2026-09-27T20:07:00Z' }) : c);
  T.message_likes = [{ message_id: 2, user_id: AV, created_at: '2026-09-27T20:10:00Z' }];
  T.message_hides = []; T.conversation_clears = [];
  return { conv, AV, crn, T };
};
const msgAt = (page, mid) => page.evaluate(mid => { const r = document.querySelector(`#scroll .msg[data-mid="${mid}"]`).getBoundingClientRect(); return { x: r.left + Math.min(24, r.width / 2), y: r.top + r.height / 2 }; }, String(mid));
const hold = async (page, pt) => { await page.mouse.move(pt.x, pt.y); await page.mouse.down(); await tick(page, 600); await page.mouse.up(); await tick(page, 200); };
/* drag a chat row left by dx px with the mouse (pointer events), the way a thumb swipes it */
const swipe = async (page, sel, dx = 130, dy = 0) => { await page.locator(sel).first().evaluate(e => e.scrollIntoView({ block: 'center' })); await tick(page, 200); const b = await page.locator(sel).first().boundingBox(); const y = b.y + b.height / 2, x = b.x + b.width - 30;
  await page.mouse.move(x, y); await page.mouse.down(); for (let i = 1; i <= 8; i++) await page.mouse.move(x - dx * i / 8, y + dy * i / 8); await page.mouse.up(); await tick(page, 400); };
const sheetActs = page => page.evaluate(() => [...document.querySelectorAll('#sheet [data-a]')].map(b => b.dataset.a));

tests.chatActions = async () => {
  const { conv, AV, crn, T } = CHAT_X();
  const { page, close, log, tables } = await openApp({ tables: T });
  await page.waitForFunction(() => TC.ready && TC.seatsLoaded, null, { timeout: 8000 });
  await click(page, '[data-a="tab"][data-x="friends"]');
  const row = () => page.locator(`#fbody .thread[data-x="${conv}"]`);
  ok(/Shared Zed Nobody/.test(await row().innerText()) && !/Shared professor/.test(await row().innerText()), 'chat: the list names what was shared, not “Shared professor”', await row().innerText());
  /* hold a chat in the list: its menu */
  const rb = await row().boundingBox();
  await hold(page, { x: rb.x + rb.width / 2, y: rb.y + rb.height / 2 });
  ok(await page.evaluate(() => UI.sheet && UI.sheet.type) === 'chatAct' && await page.evaluate(() => cur().s) !== 'chat', 'chat: holding a chat in the list opens its menu, and the release doesn’t open the chat', await page.evaluate(() => [UI.sheet, cur().s]));
  await click(page, '#sheet .xbtn');
  await click(page, `#fbody .thread[data-x="${conv}"]`); await tick(page, 600);

  /* cards: read now, from live data */
  const c4 = page.locator('#scroll .msg[data-mid="4"]');
  let t4 = (await c4.innerText()).replace(/\s+/g, ' ');
  ok(await c4.locator('.mcc[data-a="openClass"][data-x="BUS 3431"]').count() === 1 && /BUS 3431 · Sec 02/.test(t4) && /Business Finance/.test(t4) && /9 seats/.test(t4) && /See the class/.test(t4), 'chat: a shared class is a card with the section, its title and its seats', t4);
  await page.evaluate(crn => { SEC[crn].seats = 2; render(true); }, crn); await tick(page, 100);
  t4 = (await c4.innerText()).replace(/\s+/g, ' ');
  ok(/2 seats/.test(t4) && !/9 seats/.test(t4), 'chat: the class card’s seats are today’s, not the ones from when it was sent', t4);
  const c5 = page.locator('#scroll .msg[data-mid="5"]'), t5 = (await c5.innerText()).replace(/\s+/g, ' ');
  const want5 = await page.evaluate(() => ratingOf('ada examplewood').toFixed(1));
  ok(await c5.locator('.mcc[data-a="openProf"][data-x="ada examplewood"]').count() === 1 && /Ada Examplewood/.test(t5) && t5.includes(want5) && /41 ratings/.test(t5), 'chat: a shared professor (desktop “name|dept” key) shows their rating now and opens their page', { t5, want5 });
  const t6 = (await page.locator('#scroll .msg[data-mid="6"]').innerText()).replace(/\s+/g, ' ');
  ok(/Zed Nobody/.test(t6) && /We don’t have a rating for them/.test(t6) && await page.locator('#scroll .msg[data-mid="6"] [data-a]').count() === 0 && !/[0-9]\.[0-9]/.test(t6), 'chat: a professor we have no data for says so — no number, no link', t6);
  ok(!/Shared class|Shared professor/.test(await text(page)), 'chat: no grey “Shared class” / “Shared professor” bubbles');

  /* likes */
  const lk2 = page.locator('#scroll .msg[data-mid="2"] + .mlk');
  ok(await lk2.count() === 1 && !(await lk2.getAttribute('class')).includes(' on') && (await lk2.getAttribute('aria-label')) === 'Liked by Avery', 'chat: a message someone liked carries a heart', await lk2.count() && await lk2.getAttribute('aria-label'));
  let p1 = await msgAt(page, 1);
  await page.mouse.dblclick(p1.x, p1.y); await tick(page, 300);
  const likeW = () => log.writes.filter(w => w.table === 'message_likes');
  ok(likeW().length === 1 && likeW()[0].m === 'POST' && String(likeW()[0].body.message_id) === '1' && !('user_id' in likeW()[0].body) && await page.locator('#scroll .msg[data-mid="1"] + .mlk.on').count() === 1, 'chat: double-tap likes (the server stamps who)', likeW());
  p1 = await msgAt(page, 1);
  await page.mouse.dblclick(p1.x, p1.y); await tick(page, 300);
  ok(likeW().length === 1 && await page.locator('#scroll .msg[data-mid="1"] + .mlk.on').count() === 1, 'chat: double-tapping a liked message keeps the like', likeW().length);
  await click(page, '#scroll .msg[data-mid="1"] + .mlk');
  const un = likeW()[1];
  ok(un && un.m === 'DELETE' && /message_id=eq\.1/.test(un.query) && un.query.includes('user_id=eq.' + FX.ME.id) && await page.locator('#scroll .msg[data-mid="1"] + .mlk').count() === 0, 'chat: tapping your heart unlikes it, only your own like', un);

  /* hold a message: its actions */
  await hold(page, await msgAt(page, 1));
  let acts = await sheetActs(page);
  ok(await page.evaluate(() => UI.sheet && UI.sheet.type) === 'msgAct' && acts.includes('likeMsg') && acts.includes('copyMsg') && acts.includes('hideMsg') && !acts.includes('reportMsg'), 'chat: holding your own message: Like, Copy, Delete for me — no Report; the release doesn’t close it', acts);
  await click(page, '#sheet .xbtn');
  await hold(page, await msgAt(page, 2));
  acts = await sheetActs(page);
  const sh2 = await page.locator('#sheet').innerText();
  ok(acts.includes('reportMsg') && acts.includes('hideMsg') && /Avery still sees it/.test(sh2) && /Fixture reply from Avery/.test(sh2), 'chat: holding their message adds Report, and Delete for me says they still see it', { acts, sh2: sh2.slice(0, 200) });
  await click(page, '#sheet .xbtn');

  /* delete for me — the newest message, so the list falls back to the one before it */
  await hold(page, await msgAt(page, 6));
  await click(page, '#sheet [data-a="hideMsg"]');
  const hw = log.writes.filter(w => w.table === 'message_hides');
  ok(hw.length === 1 && hw[0].m === 'POST' && String(hw[0].body.message_id) === '6' && await page.locator('#scroll .msg[data-mid="6"]').count() === 0 && await page.locator('#scroll .msg[data-mid="5"]').count() === 1 && !(await page.evaluate(() => UI.sheet)), 'chat: Delete for me hides it for you (message_hides) and leaves the rest', hw);
  ok(!log.writes.some(w => w.table === 'messages' && w.m === 'DELETE'), 'chat: Delete for me never deletes the message itself');

  /* report */
  await hold(page, await msgAt(page, 2));
  await click(page, '#sheet [data-a="reportMsg"]');
  ok(/A moderator will see this message and who sent it/.test(await page.locator('#sheet').innerText()), 'chat: the report sheet says what a moderator gets');
  await click(page, '#sheet [data-a="sendReport"][data-x="hate"]');
  const rp = log.writes.filter(w => w.table === 'reports');
  ok(rp.length === 1 && rp[0].body.kind === 'message' && rp[0].body.target_id === '2' && rp[0].body.target_user === AV && rp[0].body.reporter === FX.ME.id && rp[0].body.reason === 'hate' && rp[0].body.note === 'Fixture reply from Avery' && !(await page.evaluate(() => UI.sheet)), 'chat: Report files a reports row with the message’s words (a moderator can’t open the chat)', rp);

  await click(page, '[data-a="back"]');
  ok(/Shared Ada Examplewood/.test(await row().innerText()), 'chat: with the newest message deleted for you, the list shows the one before it', await row().innerText());
  await page.evaluate(() => loadThreads().then(() => render(true))); await tick(page, 400);
  ok(/Shared Ada Examplewood/.test(await row().innerText()), 'chat: …and still does after the list reloads', await row().innerText());

  /* delete the chat: swipe its row left, tap Delete (Tate, 2026-10-04: no ⋯ in the chat) */
  await hold(page, await page.locator(`#fbody .thread[data-x="${conv}"]`).evaluate(e => { const r = e.getBoundingClientRect(); return { x: r.x + r.width / 2, y: r.y + r.height / 2 }; }));
  const hs = await page.locator('#sheet').innerText();
  ok(/See Avery’s page/.test(hs) && /Pin chat/.test(hs) && /Delete chat/.test(hs), 'chat: holding a chat offers the friend’s page, Pin and Delete chat', hs);
  await click(page, '#sheet .xbtn');
  await swipe(page, `#fbody .swrow[data-cid="${conv}"]`);
  await click(page, `#fbody .swrow[data-cid="${conv}"] .swdel`);
  ok(/removed for you only/.test(await page.locator('#sheet').innerText()) && /Avery still has it/.test(await page.locator('#sheet').innerText()), 'chat: Delete chat asks first and says it’s only for you');
  /* a message the phone never heard about (the live connection slept) */
  tables.messages.push({ id: 6500, conversation_id: conv, sender: AV, kind: 'text', body: 'Sent while you were away', payload: null, created_at: '2026-09-27T20:08:00Z' });
  await click(page, '#sheet [data-a="delChat"]');
  const cw = log.writes.filter(w => w.table === 'conversation_clears');
  ok(cw.length === 2 && cw[0].m === 'PATCH' && cw[1].m === 'POST' && cw[1].body.conversation_id === conv && cw[1].body.cleared_at === '2026-09-27T20:08:00Z' && !('user_id' in cw[1].body), 'chat: Delete chat records the newest message’s own server time, read at delete (update, then insert)', cw);
  ok(await page.evaluate(() => cur().s) !== 'chat' && await row().count() === 0, 'chat: a deleted chat leaves the list', await page.evaluate(() => cur().s));
  ok(!log.writes.some(w => (w.table === 'messages' || w.table === 'conversations' || w.table === 'conversation_members') && w.m !== 'POST' && w.m !== 'PATCH'), 'chat: deleting a chat never deletes it for the other person');

  /* a new message brings it back, with just the new message */
  const nm = { id: 7001, conversation_id: conv, sender: AV, kind: 'text', body: 'Back again', payload: null, created_at: '2026-09-29T17:31:00Z' };
  tables.messages.push(nm); tables.conversations.find(c => c.id === conv).last_at = nm.created_at;
  await page.evaluate(m => TC.onMessage({ new: m }), nm); await tick(page, 300);
  ok(await row().count() === 1 && /Back again/.test(await row().innerText()), 'chat: a new message brings the chat back', await row().count());
  await click(page, `#fbody .thread[data-x="${conv}"]`); await tick(page, 500);
  const after = await page.locator('#scroll .msgs').innerText();
  ok(/Back again/.test(after) && !/Fixture message from me|Fixture reply from Avery|Ada Examplewood|Sent while you were away/.test(after), 'chat: …starting fresh — nothing from before you deleted it', after);
  /* a group chat too: it has no "last message" rule to hide it, only the clear */
  const g = FX.CONVS[1].id;
  await click(page, '[data-a="back"]');
  await swipe(page, `#fbody .swrow[data-cid="${g}"]`);
  await click(page, `#fbody .swrow[data-cid="${g}"] .swdel`);
  ok(/Everyone else still has it/.test(await page.locator('#sheet').innerText()), 'chat: deleting a group chat says everyone else keeps it');
  await click(page, '#sheet [data-a="delChat"]');
  ok(await page.locator(`#fbody .thread[data-x="${g}"]`).count() === 0 && await page.locator(`#fbody .thread[data-x="${conv}"]`).count() === 1, 'chat: a deleted group chat leaves the list too');
  ok(log.errors.length === 0, 'chat actions: no page errors', log.errors);
  await close();
};

/* Before sql/professify-chat-likes-hides.sql runs: Like and the deletes stay out; the rest works. */
tests.chatActionsOff = async () => {
  const { conv, T } = CHAT_X();
  const miss = (url) => /\/rest\/v1\/(message_likes|message_hides|conversation_clears)$/.test(url.pathname) ? { status: 404, body: JSON.stringify({ code: 'PGRST205', message: "Could not find the table 'public." + url.pathname.split('/').pop() + "' in the schema cache", details: null, hint: null }) } : null;
  const { page, close, log } = await openApp({ tables: T, hook: miss });
  await page.waitForFunction(() => TC.ready, null, { timeout: 8000 });
  await click(page, '[data-a="tab"][data-x="friends"]');
  ok(await page.locator(`#fbody .thread[data-x="${conv}"]`).count() === 1, 'chat (no tables yet): the chat list still loads');
  await click(page, `#fbody .thread[data-x="${conv}"]`); await tick(page, 500);
  ok(await page.locator('#scroll .msg[data-mid="4"] .mcc').count() === 1 && await page.locator('#scroll .mlk').count() === 0, 'chat (no tables yet): cards show, no hearts');
  await hold(page, await msgAt(page, 2));
  const acts = await sheetActs(page);
  ok(acts.includes('copyMsg') && acts.includes('reportMsg') && !acts.includes('likeMsg') && !acts.includes('hideMsg'), 'chat (no tables yet): Copy and Report only', acts);
  await click(page, '#sheet .xbtn');
  const p = await msgAt(page, 1); await page.mouse.dblclick(p.x, p.y); await tick(page, 300);
  ok(!log.writes.some(w => w.table === 'message_likes'), 'chat (no tables yet): double-tap does nothing');
  await click(page, '[data-a="back"]');
  await swipe(page, `#fbody .swrow[data-cid="${conv}"]`);
  ok(await page.locator(`#fbody .swrow[data-cid="${conv}"] .swpin`).count() === 1 && await page.locator(`#fbody .swrow[data-cid="${conv}"] .swdel`).count() === 0, 'chat (no tables yet): a swipe shows Pin only, no Delete');
  await page.mouse.click(5, 5); await tick(page, 300);
  await hold(page, await page.locator(`#fbody .thread[data-x="${conv}"]`).evaluate(e => { const r = e.getBoundingClientRect(); return { x: r.x + r.width / 2, y: r.y + r.height / 2 }; }));
  ok(/Deleting chats isn’t switched on yet/.test(await page.locator('#sheet').innerText()) && await page.locator('#sheet [data-a="chatDelAsk"]').count() === 0, 'chat (no tables yet): holding a chat says deleting isn’t on yet');
  ok(log.errors.length === 0, 'chat (no tables yet): no page errors', log.errors);
  await close();
};

/* Send a class or a professor from its page; the card shows once even when the echo lands first. */
tests.chatSendCards = async () => {
  const conv = FX.CONVS[0].id, AV = FX.FRIENDS[0].id, sent = []; let n = 0, TT = null;
  const hook = (url, m, body) => {
    if (url.pathname !== '/rest/v1/messages' || m !== 'POST') return null;
    n++; const row = Object.assign({ id: 9000 + n, created_at: new Date(Date.parse('2026-09-29T17:31:00Z') + n * 1000).toISOString() }, body);
    sent.push(row); if (TT) TT.messages.push(row);
    return { status: 201, body: JSON.stringify(row) };
  };
  const { page, close, log, tables } = await openApp({ hook }); TT = tables;
  await page.waitForFunction(() => TC.ready && TC.seatsLoaded, null, { timeout: 8000 });
  await click(page, '[data-a="tab"][data-x="friends"]');
  await click(page, `#fbody .thread[data-x="${conv}"]`); await tick(page, 400);
  await click(page, '[data-a="back"]');
  await page.evaluate(() => A.openClass('BUS 3431')); await tick(page, 400);
  await click(page, '[data-a="sendCard"][data-x="class"]');
  ok(await page.evaluate(() => UI.sheet && UI.sheet.type) === 'sendCard' && /Share BUS 3431/.test(await page.locator('#sheet').innerText()), 'cards: the class page’s send button opens “Share BUS 3431”');
  /* the realtime echo of the send lands before the insert returns */
  await page.evaluate(([conv, me]) => TC.onMessage({ new: { id: 9001, conversation_id: conv, sender: me, kind: 'class', body: null, payload: { code: 'BUS 3431', name: 'Business Finance' }, created_at: '2026-09-29T17:31:01Z' } }), [conv, FX.ME.id]);
  await click(page, `#sheet [data-a="cardTo"][data-x="${AV}"]`); await tick(page, 300);
  ok(sent.length === 1 && sent[0].conversation_id === conv && sent[0].sender === FX.ME.id && sent[0].kind === 'class' && sent[0].body === null && sent[0].payload.code === 'BUS 3431' && sent[0].payload.name === 'Business Finance', 'cards: sends a class message with the code and title', sent[0]);
  ok(/Sent/.test(await page.locator(`#sheet [data-a="cardTo"][data-x="${AV}"]`).innerText()) && await page.evaluate(conv => TC.rows[conv].filter(m => String(m.id) === '9001').length, conv) === 1, 'cards: “Sent”, and the message is in the chat once (the echo came first)', await page.evaluate(conv => TC.rows[conv].map(m => m.id), conv));
  await click(page, '#sheet .xbtn');
  await page.evaluate(() => A.openProf('ada examplewood')); await tick(page, 400);
  await click(page, '[data-a="sendCard"][data-x="professor"]');
  await click(page, `#sheet [data-a="cardTo"][data-x="${AV}"]`); await tick(page, 300);
  ok(sent.length === 2 && sent[1].kind === 'professor' && sent[1].payload.key === 'ada examplewood|bus' && sent[1].payload.pkey === 'ada examplewood' && sent[1].payload.name === 'Ada Examplewood', 'cards: sends a professor message the desktop can read too (“name|dept”)', sent[1]);
  await click(page, '#sheet .xbtn');
  await click(page, '[data-a="tab"][data-x="friends"]');
  const rt = await page.locator(`#fbody .thread[data-x="${conv}"]`).innerText();
  ok(/Shared Ada Examplewood/.test(rt), 'cards: the chat list reads “Shared Ada Examplewood”', rt);
  await click(page, `#fbody .thread[data-x="${conv}"]`); await tick(page, 500);
  ok(await page.locator('#scroll .msg[data-mid="9001"]').count() === 1 && await page.locator('#scroll .msg[data-mid="9001"] .mcc[data-x="BUS 3431"]').count() === 1 && await page.locator('#scroll .msg[data-mid="9002"] .mcc[data-x="ada examplewood"]').count() === 1, 'cards: both show in the chat as cards, once each');
  ok(log.errors.length === 0, 'cards: no page errors', log.errors);
  await close();
};

/* Holding: a late lift, a lift that lands on the sheet, and a real touch (the bubble is redrawn under the finger). */
/* Swipe a chat left for Pin / Delete; no ⋯ in a chat (Tate, 2026-10-04). */
tests.chatSwipe = async () => {
  const { conv, T } = CHAT_X();
  const { page, close, log } = await openApp({ tables: T });
  await page.waitForFunction(() => TC.ready, null, { timeout: 8000 });
  await click(page, '[data-a="tab"][data-x="friends"]');
  const ids = await page.evaluate(() => [...document.querySelectorAll('#fbody .swrow')].map(r => r.dataset.cid));
  ok(ids.length >= 2 && await page.locator('#fbody .thread').count() === ids.length, 'swipe: every row in Chats can be swiped', ids);
  const tx = id => page.evaluate(id => getComputedStyle(document.querySelector(`#fbody .swrow[data-cid="${id}"] > .thread`)).transform, id);
  const last = ids.at(-1);
  /* at rest no Pin / Delete colour is on screen behind any row: no blue or red lines between chats (Tate, 18:45) */
  const vis = () => page.evaluate(() => [...document.querySelectorAll('#fbody .swrow > .swacts')].map(a => getComputedStyle(a).visibility));
  ok((await vis()).length > 1 && (await vis()).every(v => v === 'hidden'), 'swipe: at rest no row’s Pin / Delete is drawn (no coloured lines between chats)', await vis());
  /* a short drag springs back; a drag past half stays open with Pin and Delete showing */
  await swipe(page, `#fbody .swrow[data-cid="${last}"]`, 40);
  ok(await tx(last) === 'none' && await page.evaluate(() => cur().s) === 'friends', 'swipe: a short drag springs back and opens nothing', await tx(last));
  await swipe(page, `#fbody .swrow[data-cid="${last}"]`);
  const open = await page.evaluate(id => { const r = document.querySelector(`#fbody .swrow[data-cid="${id}"]`), rb = r.getBoundingClientRect(), th = r.querySelector('.thread').getBoundingClientRect(), pin = r.querySelector('.swpin').getBoundingClientRect(), del = r.querySelector('.swdel').getBoundingClientRect();
    return { shift: Math.round(rb.right - th.right), pinIn: pin.left >= th.right - 1 && pin.right <= rb.right + 1, delIn: del.left >= pin.right - 1 && Math.round(del.right) === Math.round(rb.right), pinTxt: r.querySelector('.swpin').textContent, delTxt: r.querySelector('.swdel').textContent, pinBg: getComputedStyle(r.querySelector('.swpin')).backgroundColor, delBg: getComputedStyle(r.querySelector('.swdel')).backgroundColor }; }, last);
  ok(await page.evaluate(id => getComputedStyle(document.querySelector(`#fbody .swrow[data-cid="${id}"] > .swacts`)).visibility, last) === 'visible', 'swipe: an open row shows its Pin / Delete');
  ok(open.shift === 152 && open.pinIn && open.delIn && open.pinTxt === 'Pin' && open.delTxt === 'Delete' && open.delBg === 'rgb(220, 38, 38)', 'swipe: past half it stays open, Pin then a red Delete at the right edge', open);
  ok(await page.evaluate(() => cur().s) === 'friends', 'swipe: swiping never opens the chat');
  /* a tap elsewhere only closes it */
  await click(page, `#fbody .thread[data-x="${ids[0]}"]`);
  await tick(page, 400);
  ok((await vis()).every(v => v === 'hidden'), 'swipe: once it has slid closed, its Pin / Delete are hidden again', await vis());
  ok(await tx(last) === 'none' && await page.evaluate(() => cur().s) === 'friends', 'swipe: a tap on another row closes the open one and opens nothing', await page.evaluate(() => cur().s));
  /* swiping back closes it */
  await swipe(page, `#fbody .swrow[data-cid="${last}"]`);
  await swipe(page, `#fbody .swrow[data-cid="${last}"]`, -130);
  ok(await tx(last) === 'none', 'swipe: dragging it back to the right closes it', await tx(last));
  /* an up-and-down drag is a scroll, not a swipe */
  await swipe(page, `#fbody .swrow[data-cid="${last}"]`, 90, 200);
  ok(await tx(last) === 'none', 'swipe: a mostly vertical drag doesn’t slide the row', await tx(last));
  /* Pin: the chat goes to the top with a pin by its time, kept on this phone */
  await swipe(page, `#fbody .swrow[data-cid="${last}"]`);
  await click(page, `#fbody .swrow[data-cid="${last}"] .swpin`);
  const pin = await page.evaluate(id => ({ first: document.querySelector('#fbody .swrow').dataset.cid, mark: !!document.querySelector(`#fbody .thread[data-x="${id}"] .pinm`), others: document.querySelectorAll('#fbody .pinm').length, store: localStorage.getItem('tc-chat-pins-' + TC.user.id), toast: document.getElementById('toast').textContent }), last);
  ok(pin.first === last && pin.mark && pin.others === 1 && pin.store === JSON.stringify([last]) && pin.toast === 'Pinned', 'swipe: Pin moves the chat to the top with a pin by its time, kept on this phone', pin);
  ok(!log.writes.some(w => /pin/i.test(w.table)), 'swipe: pinning sends nothing to the server');
  await swipe(page, `#fbody .swrow[data-cid="${last}"]`);
  ok(await page.locator(`#fbody .swrow[data-cid="${last}"] .swpin`).innerText() === 'Unpin', 'swipe: a pinned chat offers Unpin');
  await click(page, `#fbody .swrow[data-cid="${last}"] .swpin`);
  ok(await page.evaluate(id => [...document.querySelectorAll('#fbody .swrow')].map(r => r.dataset.cid).join() , last) === ids.join() && await page.locator('#fbody .pinm').count() === 0, 'swipe: Unpin puts it back in its place');
  /* up to three chats pinned at once */
  const PK = () => page.evaluate(() => localStorage.getItem('tc-chat-pins-' + TC.user.id));
  await page.evaluate(() => { const b = TC.threads.find(t => t.last); ['z1', 'z2', 'z3'].forEach((id, i) => TC.threads.push(Object.assign({}, b, { id, last: Object.assign({}, b.last, { body: 'Seed ' + i }) }))); localStorage.setItem('tc-chat-pins-' + TC.user.id, JSON.stringify(['z1', 'z2', 'z3'])); render(true); }); await tick(page, 200);
  await swipe(page, `#fbody .swrow[data-cid="${last}"]`);
  await click(page, `#fbody .swrow[data-cid="${last}"] .swpin`);
  ok(await PK() === JSON.stringify(['z1', 'z2', 'z3']) && /up to 3/.test(await page.locator('#toast').textContent()), 'swipe: a fourth pin is refused with a reason');
  /* a pin whose chat is gone doesn't count, and is dropped on the next pin */
  await page.evaluate(() => { TC.threads = TC.threads.filter(t => !/^z/.test(t.id)); render(true); }); await tick(page, 200);
  await swipe(page, `#fbody .swrow[data-cid="${last}"]`);
  await click(page, `#fbody .swrow[data-cid="${last}"] .swpin`);
  ok(await PK() === JSON.stringify([last]), 'swipe: pins of chats that are gone don’t count toward the three', await PK());
  /* a redraw while a row is open closes it; the next short drag starts from closed, not open */
  await swipe(page, `#fbody .swrow[data-cid="${ids[0]}"]`);
  await page.evaluate(() => render(true)); await tick(page, 200);
  await swipe(page, `#fbody .swrow[data-cid="${ids[0]}"]`, 40);
  ok(await tx(ids[0]) === 'none', 'swipe: after a redraw, a short drag on that row doesn’t jump it open', await tx(ids[0]));
  /* a finger swipe (touch) works too */
  const cdp = await page.context().newCDPSession(page);
  const tb = await page.locator(`#fbody .swrow[data-cid="${conv}"]`).boundingBox(), ty = tb.y + tb.height / 2, tx0 = tb.x + tb.width - 30;
  await cdp.send('Input.dispatchTouchEvent', { type: 'touchStart', touchPoints: [{ x: tx0, y: ty }] });
  for (let i = 1; i <= 8; i++) await cdp.send('Input.dispatchTouchEvent', { type: 'touchMove', touchPoints: [{ x: tx0 - 130 * i / 8, y: ty }] });
  await cdp.send('Input.dispatchTouchEvent', { type: 'touchEnd', touchPoints: [] }); await tick(page, 400);
  ok(/translateX\(-152px\)/.test(await page.evaluate(id => document.querySelector(`#fbody .swrow[data-cid="${id}"] > .thread`).style.transform, conv)) && /pan-y/.test(await page.evaluate(() => getComputedStyle(document.querySelector('#fbody .swrow > .thread')).touchAction)), 'swipe: a finger swipe opens it; rows still scroll up and down (pan-y)');
  /* Delete asks first; a deleted chat drops its pin */
  await page.evaluate(id => { localStorage.setItem('tc-chat-pins-' + TC.user.id, JSON.stringify([id])); }, conv);
  await click(page, `#fbody .swrow[data-cid="${conv}"] .swdel`);
  ok(await page.evaluate(() => UI.sheet && UI.sheet.type) === 'chatDel' && /removed for you only/.test(await page.locator('#sheet').innerText()), 'swipe: Delete opens the “Delete this chat?” confirm');
  await click(page, '#sheet [data-a="delChat"]'); await tick(page, 400);
  ok(await PK() === '[]' && await page.locator(`#fbody .swrow[data-cid="${conv}"]`).count() === 0, 'swipe: deleting a pinned chat drops its pin', await PK());
  /* holding a chat: Pin works from there too */
  const keep = await page.evaluate(() => document.querySelector('#fbody .swrow').dataset.cid);
  await hold(page, await page.locator(`#fbody .thread[data-x="${keep}"]`).evaluate(e => { const r = e.getBoundingClientRect(); return { x: r.x + r.width / 2, y: r.y + r.height / 2 }; }));
  await click(page, '#sheet [data-a="pinChat"]');
  ok(await PK() === JSON.stringify([keep]) && await page.evaluate(() => UI.sheet) === null, 'swipe: Pin chat from the hold menu pins it', await PK());
  await page.evaluate(() => localStorage.removeItem('tc-chat-pins-' + TC.user.id));
  const conv2 = keep;
  /* no ⋯ inside a chat */
  await click(page, `#fbody .thread[data-x="${conv2}"]`); await tick(page, 400);
  ok(await page.evaluate(() => cur().s) === 'chat' && await page.locator('.chathdr').count() === 1 && await page.locator('.chathdr .iconbtn').count() === 1 && await page.locator('.chathdr [data-a="back"]').count() === 1 && await page.locator('.chathdr [aria-label="Chat options"]').count() === 0, 'swipe: a chat has no ⋯ at the top (only Back)', await page.locator('.chathdr').innerHTML());
  ok(log.errors.length === 0, 'swipe: no page errors', log.errors);
  await close();
};

/* Remove a friend, discreetly (Tate, 2026-10-04): tucked in a ⋯ on their page, one confirm, nothing sent to them. */
/* 18:15: no ⋯ in a chat — a 1:1's name opens their page (Remove friend / Report / Block in its ⋯), a group's
   name opens the group's sheet (who's in it, Pin, Delete, Leave). */
tests.chatNoDots = async () => {
  const { page, close, log } = await openApp({});
  await page.waitForFunction(() => TC.ready, null, { timeout: 8000 });
  await openChatRow(page, DIRECT.id);
  ok(await page.locator('.chathdr .iconbtn').count() === 1 && await page.locator('.chathdr [data-a="back"]').count() === 1 && await page.locator('.chathdr [data-a="chatMenu"]').count() === 0, 'no dots: a 1:1 chat’s header has only Back');
  await click(page, '.chathdr [data-a="openFriend"]'); await tick(page, 300);
  await click(page, '#scroll [data-a="personMenu"]');
  const pa = await sheetActs(page);
  ok(await page.evaluate(() => cur().s) === 'friend' && pa.includes('friendRmAsk') && pa.includes('reportAsk') && pa.includes('blockAsk'), 'no dots: its name opens their page, whose ⋯ has Remove friend, Report and Block', pa);
  await click(page, '#sheet .xbtn');
  await openChatRow(page, GROUP.id);
  ok(await page.locator('.chathdr .iconbtn').count() === 1 && await page.locator('.chathdr [data-a="chatMenu"]').count() === 1, 'no dots: a group chat’s header has only Back, and its name is a button');
  await click(page, '.chathdr [data-a="chatMenu"]');
  const ga = await sheetActs(page);
  ok(await page.evaluate(() => UI.sheet && UI.sheet.type) === 'chatAct' && ga.includes('pinChat') && ga.includes('leaveAsk') && ga.includes('chatDelAsk') && /In this group/.test(await page.locator('#sheet').innerText()), 'no dots: a group’s name opens its sheet (who’s in it, Pin, Delete, Leave)', ga);
  ok(log.errors.length === 0, 'no dots: no page errors', log.errors);
  await close();
};

tests.removeFriend = async () => {
  const AV = FX.FRIENDS[0].id;
  const run = async (fail) => {
    const o = await openApp({ hook: fail ? ((url, m) => m === 'DELETE' && /friend_requests/.test(url.pathname) ? { status: 500, body: JSON.stringify({ message: 'boom', code: 'XX000' }) } : null) : null });
    await o.page.waitForFunction(() => TC.ready && TC.friends.length > 0, null, { timeout: 8000 });
    await o.page.evaluate(id => A.openFriend(id), AV); await settle(o.page, 500);
    return o;
  };
  let { page, close, log } = await run(false);
  const dot = page.locator('.topbtns [data-a="personMenu"]');
  ok(await dot.count() === 1 && await page.locator('.topbtns .iconbtn').count() === 2, 'remove friend: in the one small ⋯ at the top right of a friend’s page (no new button)');
  ok(await page.locator('#scroll [data-a="friendRmAsk"], #scroll [data-a="rmFriend"]').count() === 0, 'remove friend: nothing on the page itself says Remove');
  await click(page, '.topbtns [data-a="personMenu"]');
  const acts0 = [...new Set(await sheetActs(page))].filter(a => a !== 'closeSheet'), sh0 = await page.locator('#sheet').innerText();
  ok(acts0[0] === 'friendRmAsk' && acts0.includes('reportAsk') && acts0.includes('blockAsk') && /Remove friend\s*Avery isn’t told/.test(sh0), 'remove friend: first row of the ⋯ (above Report and Block), “Avery isn’t told”', { acts0, sh0 });
  await click(page, '#sheet [data-a="friendRmAsk"]');
  const cf = await page.locator('#sheet').innerText();
  ok(/Remove Avery\?/.test(cf) && /We won’t tell Avery/.test(cf) && /stop seeing each other’s classes and plans/.test(cf) && /Any chat you have stays/.test(cf), 'remove friend: one confirm that says they won’t be told', cf);
  await click(page, '#sheet .btn.soft');
  ok(await page.evaluate(() => UI.sheet) === null && !log.writes.length && await page.evaluate(id => TC.friends.includes(id), AV), 'remove friend: Cancel changes nothing');
  await click(page, '.topbtns [data-a="personMenu"]'); await click(page, '#sheet [data-a="friendRmAsk"]'); await click(page, '#sheet [data-a="rmFriend"]'); await settle(page, 600);
  const w = log.writes;
  ok(w.length === 1 && w[0].m === 'DELETE' && w[0].table === 'friend_requests' && /from_user=in\./.test(w[0].query) && /to_user=in\./.test(w[0].query) && w[0].query.includes(AV) && w[0].query.includes(FX.ME.id), 'remove friend: one delete of the friendship row, both directions — no message, no notice', w);
  const after = await page.evaluate(id => ({ fr: TC.friends.includes(id), s: cur().s, toast: document.getElementById('toast').textContent, story: !!document.querySelector(`.story[data-x="${id}"]`) }), AV);
  ok(!after.fr && after.s !== 'friend' && after.toast === 'Removed', 'remove friend: they leave your friends, you go back, “Removed”', after);
  await click(page, '[data-a="tab"][data-x="friends"]');
  ok(!/Avery Quill/.test(await page.locator('#fbody').innerText()) || await page.locator(`#fbody [data-a="openFriend"][data-x="${AV}"]`).count() === 0, 'remove friend: they’re gone from your Friends list');
  await click(page, '[data-a="tab"][data-x="home"]');
  ok(await page.evaluate(id => !document.querySelector(`#hf-${id}`) && ![...document.querySelectorAll('.story')].some(s => s.dataset.x === id), AV), 'remove friend: their story and week card leave Home');
  /* a friendship that started from your request (the other direction) */
  const F2 = FX.FRIENDS[1].id, dir = await page.evaluate(id => 'mine', F2);
  await page.evaluate(id => A.openFriend(id), F2); await settle(page, 500);
  await click(page, '.topbtns [data-a="personMenu"]'); await click(page, '#sheet [data-a="friendRmAsk"]'); await click(page, '#sheet [data-a="rmFriend"]'); await settle(page, 600);
  ok(await page.evaluate(id => !TC.friends.includes(id), F2), 'remove friend: works whichever of you sent the request');
  ok(log.errors.length === 0, 'remove friend: no page errors', log.errors);
  await close();
  /* a refused delete keeps them and says so */
  ({ page, close, log } = await run(true));
  await click(page, '.topbtns [data-a="personMenu"]'); await click(page, '#sheet [data-a="friendRmAsk"]'); await click(page, '#sheet [data-a="rmFriend"]'); await settle(page, 600);
  ok(await page.evaluate(id => TC.friends.includes(id) && cur().s === 'friend', AV) && /Couldn’t remove/.test(await page.locator('#toast').textContent()) && await page.evaluate(() => UI.sheet && UI.sheet.type) === 'friendRm', 'remove friend: a refused delete keeps them, keeps the confirm open and says so');
  await close();
  /* not on a non-friend's page */
  ({ page, close, log } = await run(false));
  await page.evaluate(() => { const s = { id: '33333333-3333-4333-8333-333333333331', display_name: 'Morgan Nobody', username: 'mnobody', avatar_url: null }; PEOPLE[s.id] = personFrom(s); A.openFriend(s.id); }); await settle(page, 400);
  await click(page, '.topbtns [data-a="personMenu"]');
  const acts1 = await sheetActs(page);
  ok(!acts1.includes('friendRmAsk') && acts1.includes('blockAsk'), 'remove friend: not offered for someone who isn’t your friend (Report / Block still are)', acts1);
  await close();
};

tests.chatHold = async () => {
  const { conv, T } = CHAT_X();
  const { page, close, log } = await openApp({ tables: T });
  await page.waitForFunction(() => TC.ready, null, { timeout: 8000 });
  await click(page, '[data-a="tab"][data-x="friends"]');
  await click(page, `#fbody .thread[data-x="${conv}"]`); await tick(page, 500);
  /* a half-typed message survives a hold and a like */
  await page.locator('#chatin').fill('half a thought');
  await hold(page, await msgAt(page, 2));
  await click(page, '#sheet .xbtn');
  const q1 = await msgAt(page, 1); await page.mouse.dblclick(q1.x, q1.y); await tick(page, 300);
  ok(await page.locator('#chatin').inputValue() === 'half a thought' && await page.locator('#scroll .msg[data-mid="1"] + .mlk.on').count() === 1, 'hold: what you were typing is still there after a hold and a like', await page.locator('#chatin').inputValue());
  /* a lift that never arrives (alt-tab mid-hold): the next press still works */
  await page.evaluate(() => { LP.held = true; });
  await click(page, '.chathdr [data-a="openFriend"]');
  ok(await page.evaluate(() => cur().s) === 'friend', 'hold: a lost lift never leaves the app ignoring taps', await page.evaluate(() => [cur().s, LP.held]));
  await click(page, '[data-a="back"]'); await tick(page, 300);
  let p = await msgAt(page, 2);
  await page.mouse.move(p.x, p.y); await page.mouse.down(); await tick(page, 1500);
  ok(await page.evaluate(() => UI.sheet && UI.sheet.type) === 'msgAct', 'hold: the sheet opens while you are still holding');
  const hb = await page.locator('#sheet [data-a="hideMsg"]').boundingBox();
  await page.mouse.up();
  await page.mouse.click(hb.x + hb.width / 2, hb.y + hb.height / 2);   /* iOS: the lift's click lands where the finger is */
  ok(!log.writes.some(w => w.table === 'message_hides') && await page.evaluate(() => UI.sheet && UI.sheet.type) === 'msgAct', 'hold: a late lift that lands on “Delete for me” does not delete', log.writes.filter(w => w.table === 'message_hides'));
  await tick(page, 500);
  await click(page, '#sheet [data-a="hideMsg"]');
  ok(log.writes.filter(w => w.table === 'message_hides').length === 1, 'hold: a real tap afterwards works');
  /* a real touch: start on a bubble, hold, lift. iOS fires no contextmenu on a long press (Chrome does, and its
     handler would end the hold by itself), so keep it away from the app here: only the lift may end the hold. */
  await page.evaluate(() => window.addEventListener('contextmenu', e => { e.stopImmediatePropagation(); e.preventDefault(); }, { capture: true }));
  const cdp = await page.context().newCDPSession(page);
  p = await msgAt(page, 1);
  await cdp.send('Input.dispatchTouchEvent', { type: 'touchStart', touchPoints: [{ x: p.x, y: p.y }] });
  await tick(page, 600);
  ok(await page.evaluate(() => UI.sheet && UI.sheet.type) === 'msgAct' && await page.evaluate(() => LP.held) === true, 'hold (touch): holding a bubble with a finger opens its actions');
  /* make the redraw certain (a timer or realtime redraw does this on a phone): the touched bubble leaves the page */
  await page.evaluate(() => { window.__lpb = document.querySelector('#scroll .msg[data-mid="1"]'); render(); });
  ok(await page.evaluate(() => !!window.__lpb && !window.__lpb.isConnected) && await page.evaluate(() => LP.held) === true, 'hold (touch): the touched bubble was redrawn while held');
  await cdp.send('Input.dispatchTouchEvent', { type: 'touchEnd', touchPoints: [] }); await tick(page, 50);
  ok(await page.evaluate(() => LP.held === false && LP.until > 0), 'hold (touch): the lift is seen even though the bubble was redrawn', await page.evaluate(() => [LP.held, LP.until]));
  await click(page, '#sheet .xbtn');
  /* moving the finger (scrolling) cancels the hold */
  p = await msgAt(page, 1);
  await cdp.send('Input.dispatchTouchEvent', { type: 'touchStart', touchPoints: [{ x: p.x, y: p.y }] });
  await cdp.send('Input.dispatchTouchEvent', { type: 'touchMove', touchPoints: [{ x: p.x, y: p.y - 30 }] });
  await tick(page, 700);
  await cdp.send('Input.dispatchTouchEvent', { type: 'touchEnd', touchPoints: [] }); await tick(page, 100);
  ok(!(await page.evaluate(() => UI.sheet)), 'hold (touch): scrolling instead of holding opens nothing');
  ok(log.errors.length === 0, 'hold: no page errors', log.errors);
  await close();
};

/* Cards are other people's JSON: nothing in them runs, a CRN from another class shows no seats, a professor
   not teaching this term still shows their real PolyRatings score, and a missing rating is said as such. */
tests.chatCardsSafe = async () => {
  const conv = FX.CONVS[0].id, AV = FX.FRIENDS[0].id;
  const T = JSON.parse(JSON.stringify(FX.TABLES));
  const other = FX.seat('BUS 4442', '01').class_nbr;
  T.messages = T.messages.concat([
    { id: 11, conversation_id: conv, sender: AV, kind: 'class', body: null, payload: { code: '<img src=x onerror="window.__pwn=1">', name: '<b>bold</b>' }, created_at: '2026-09-27T20:01:00Z' },
    { id: 12, conversation_id: conv, sender: AV, kind: 'class', body: null, payload: { code: 'BUS 3431', name: 'Business Finance', section: '01', crn: other }, created_at: '2026-09-27T20:02:00Z' },
    { id: 13, conversation_id: conv, sender: AV, kind: 'professor', body: null, payload: { pkey: 'constructor', name: '<img src=x onerror="window.__pwn=2">' }, created_at: '2026-09-27T20:03:00Z' },
    { id: 14, conversation_id: conv, sender: AV, kind: 'professor', body: null, payload: { key: 'gil offterm|math', name: 'Gil Offterm' }, created_at: '2026-09-27T20:04:00Z' },
    { id: 16, conversation_id: conv, sender: AV, kind: 'professor', body: null, payload: { name: 'Gil Offterm' }, created_at: '2026-09-27T20:04:30Z' },
  ]);
  T.conversations = T.conversations.map(c => c.id === conv ? Object.assign({}, c, { last_at: '2026-09-27T20:04:30Z' }) : c);
  /* two Gil Offterms: MATH (3.2/4, 9) and ENGL (1.0/4, 50) — the card's department decides, never the bigger count */
  const poly = FX.POLY.concat([{ id: 'p9', firstName: 'Gil', lastName: 'Offterm', department: 'MATH', overallRating: 3.2, numEvals: 9, courses: [] }, { id: 'p10', firstName: 'Gil', lastName: 'Offterm', department: 'ENGL', overallRating: 1.0, numEvals: 50, courses: [] }]);
  const { page, close, log } = await openApp({ tables: T, poly });
  await page.waitForFunction(() => TC.ready && TC.seatsLoaded && TC.profsLoaded, null, { timeout: 8000 });
  await click(page, '[data-a="tab"][data-x="friends"]');
  await click(page, `#fbody .thread[data-x="${conv}"]`); await tick(page, 500);
  ok(await page.evaluate(() => window.__pwn) === undefined && await page.locator('#scroll .msgs img, #scroll .msgs b b').count() === 0, 'cards: nothing in a payload becomes markup or runs');
  ok(/<img src=x/.test(await page.locator('#scroll .msg[data-mid="11"]').innerText()) && await page.locator('#scroll .msg[data-mid="11"] [data-a]').count() === 0, 'cards: a code that isn’t a class shows as text, with no link');
  const t12 = (await page.locator('#scroll .msg[data-mid="12"]').innerText()).replace(/\s+/g, ' ');
  ok(/BUS 3431/.test(t12) && !/seat|Full|Waitlist|Open/.test(t12), 'cards: a CRN that is another class this term shows no seats (never another class’s number)', t12);
  const t13 = (await page.locator('#scroll .msg[data-mid="13"]').innerText()).replace(/\s+/g, ' ');
  ok(/We don’t have a rating for them/.test(t13) && !/Object/.test(t13) && await page.locator('#scroll .msg[data-mid="13"] [data-a]').count() === 0, 'cards: a made-up professor key finds nobody', t13);
  const t14 = (await page.locator('#scroll .msg[data-mid="14"]').innerText()).replace(/\s+/g, ' ');
  ok(/Gil Offterm/.test(t14) && /4\.0/.test(t14) && /9 ratings/.test(t14) && await page.locator('#scroll .msg[data-mid="14"] [data-a]').count() === 0, 'cards: a professor not teaching this term shows their real PolyRatings score, from their department (no page to open)', t14);
  const t16 = (await page.locator('#scroll .msg[data-mid="16"]').innerText()).replace(/\s+/g, ' ');
  ok(/We don’t have a rating for them/.test(t16) && !/[0-9]\.[0-9]/.test(t16), 'cards: the same name in two departments, with nothing to tell them apart, shows no one’s number', t16);
  ok(log.errors.length === 0, 'cards (unsafe payloads): no page errors', log.errors);
  await close();
  /* PolyRatings didn't load: say so, never "No ratings yet" */
  const T2 = JSON.parse(JSON.stringify(FX.TABLES));
  T2.messages = T2.messages.concat([{ id: 15, conversation_id: conv, sender: AV, kind: 'professor', body: null, payload: { key: 'ada examplewood|bus', name: 'Ada Examplewood' }, created_at: '2026-09-27T20:05:00Z' }]);
  const o2 = await openApp({ tables: T2, poly: null });
  await o2.page.waitForFunction(() => TC.ready && TC.seatsLoaded, null, { timeout: 8000 });
  await click(o2.page, '[data-a="tab"][data-x="friends"]');
  await click(o2.page, `#fbody .thread[data-x="${conv}"]`); await tick(o2.page, 500);
  const t15 = (await o2.page.locator('#scroll .msg[data-mid="15"]').innerText()).replace(/\s+/g, ' ');
  ok(/Ratings didn’t load/.test(t15) && !/No ratings yet/.test(t15), 'cards: with PolyRatings down, the card says the rating didn’t load', t15);
  await o2.close();
};

/* A like that fails comes back off; a second report of the same message says it's already in. */
tests.chatErrors = async () => {
  const { conv, T } = CHAT_X();
  const hook = (url, m) => {
    if (url.pathname === '/rest/v1/message_likes' && m === 'POST') return { status: 500, body: JSON.stringify({ code: 'XX000', message: 'boom' }) };
    if (url.pathname === '/rest/v1/reports' && m === 'POST') return { status: 409, body: JSON.stringify({ code: '23505', message: 'duplicate key value violates unique constraint "reports_one_per_target_idx"' }) };
    return null;
  };
  const { page, close, log } = await openApp({ tables: T, hook });
  await page.waitForFunction(() => TC.ready, null, { timeout: 8000 });
  await click(page, '[data-a="tab"][data-x="friends"]');
  await click(page, `#fbody .thread[data-x="${conv}"]`); await tick(page, 500);
  const p = await msgAt(page, 1); await page.mouse.dblclick(p.x, p.y); await tick(page, 400);
  ok(await page.locator('#scroll .msg[data-mid="1"] + .mlk').count() === 0 && /Couldn’t like that/.test(await page.locator('#toast').innerText()), 'errors: a like the server refused comes back off and says so', await page.locator('#toast').innerText());
  await hold(page, await msgAt(page, 2));
  await click(page, '#sheet [data-a="reportMsg"]');
  await click(page, '#sheet [data-a="sendReport"][data-x="spam"]');
  ok(/You already reported this/.test(await page.locator('#toast').innerText()) && !(await page.evaluate(() => UI.sheet)), 'errors: reporting the same message twice says it’s already with a moderator', await page.locator('#toast').innerText());
  ok(log.errors.length === 0, 'errors: no page errors', log.errors);
  await close();
};

/* Message on a friend's page you opened from your chat with them goes back to that chat (review, 2026-10-03). */
tests.chatFriendBack = async () => {
  const { page, close, log } = await openApp({});
  await page.waitForFunction(() => TC.ready, null, { timeout: 8000 });
  await click(page, '[data-a="tab"][data-x="friends"]');
  await click(page, `#fbody .thread[data-x="${FX.CONVS[0].id}"]`); await tick(page, 400);
  const depth = () => page.evaluate(() => S.stack[S.tab].map(e => e.s).join('>'));
  const d0 = await depth();
  await click(page, '.chathdr [data-a="openFriend"]'); await tick(page, 300);
  await click(page, '#scroll [data-a="openChatWith"]'); await tick(page, 400);
  ok(await depth() === d0 && await page.evaluate(() => cur().s === 'chat' && cur().p.id) === FX.CONVS[0].id, 'chat back: Message on her page returns to the same chat, not a second copy', { d0, now: await depth() });
  await click(page, '[data-a="back"]');
  ok(await page.evaluate(() => cur().s) !== 'chat' && await page.locator(`#fbody .thread[data-x="${FX.CONVS[0].id}"]`).count() === 1, 'chat back: one back from there is the Friends list', await depth());
  /* from the list, Message still opens the chat on top of her page */
  await click(page, '.li:has-text("Sky Placeholder")'); await tick(page, 300);
  await click(page, '#scroll [data-a="openChatWith"]'); await tick(page, 500);
  ok(/>friend>chat$/.test(await depth()), 'chat back: Message from a friend reached from the list opens a chat over her page', await depth());
  ok(log.errors.length === 0, 'chat back: no page errors', log.errors);
  await close();
};

/* A professor's circle takes their rating's colour by half star (Tate, 2026-10-03). */
tests.profAvatarTone = async () => {
  const { page, close, log } = await openApp({});
  await page.waitForFunction(() => TC.ready && TC.profsLoaded, null, { timeout: 8000 });
  await click(page, '[data-a="tab"][data-x="explore"]'); await click(page, '[data-a="exMode"][data-x="profs"]'); await settle(page, 400);
  const seen = await page.evaluate(() => [...document.querySelectorAll('#scroll .pav-t')].map(el => {
    const card = el.closest('[data-x]'), pk = card && card.dataset.x, r = pk ? ratingOf(pk) : undefined;
    const probe = document.createElement('span'); document.body.appendChild(probe);
    return { pk, r, step: el.dataset.step, bg: getComputedStyle(el).backgroundColor, ink: getComputedStyle(el).color, txt: el.textContent, probe };
  }).map(x => { delete x.probe; return x; }));
  ok(seen.length >= 5, 'prof circles: Explore’s professor cards draw rating-coloured circles', seen.length);
  const want = await page.evaluate(() => { const out = {}; for (let k = 1; k <= 10; k++) { const e = document.createElement('span'); e.style.background = RATE_BRIGHT(k); document.body.appendChild(e); out[k] = getComputedStyle(e).backgroundColor; e.remove(); } return out; });
  const rated = seen.filter(x => typeof x.r === 'number'), unrated = seen.filter(x => x.r === null);
  ok(unrated.every(x => x.step === '' && x.bg === 'rgb(230, 234, 241)'), 'prof circles: a professor with no rating has a grey circle', unrated);
  const bad = rated.filter(x => +x.step !== Math.round(x.r * 2) / 2 || x.bg !== want[Math.round(x.r * 2)]);
  ok(!bad.length, 'prof circles: each circle’s step is the rating rounded to the half star, in that step’s colour', { bad, want });
  const steps = [...new Set(rated.map(x => x.step))];
  ok(steps.length >= 4 && new Set(rated.map(x => x.bg)).size === steps.length, 'prof circles: different half stars, different colours', { steps, bgs: [...new Set(rated.map(x => x.bg))] });
  /* every half star, drawn by the app itself on a real card: ten different colours, each readable */
  const drawn = await page.evaluate(() => { const pk = 'ada examplewood', old = PROFS[pk].r, out = [];
    for (let k = 1; k <= 10; k++) { PROFS[pk].r = k / 2; render(true); const el = [...document.querySelectorAll('#scroll .pav-t')].find(e => e.closest('[data-x]') && e.closest('[data-x]').dataset.x === pk); const cs = getComputedStyle(el); out.push([el.dataset.step, cs.backgroundColor, cs.color, el.getAttribute('aria-hidden')]); }
    PROFS[pk].r = old; render(true); return out; });
  const lum = c => { const v = c.match(/\d+/g).slice(0, 3).map(x => { x /= 255; return x <= 0.03928 ? x / 12.92 : ((x + 0.055) / 1.055) ** 2.4; }); return 0.2126 * v[0] + 0.7152 * v[1] + 0.0722 * v[2]; };
  const cr = (a, b) => { const [x, y] = [lum(a), lum(b)].sort((p, q) => q - p); return (x + 0.05) / (y + 0.05); };
  ok(new Set(drawn.map(d => d[1])).size === 10 && drawn.every((d, i) => d[0] === String((i + 1) / 2)), 'prof circles: all ten half stars draw ten different colours', drawn);
  ok(drawn.every(d => cr(d[1], d[2]) >= 4.5 && d[3] === 'true'), 'prof circles: the initials stay readable on every step (4.5:1+), and the circle is hidden from screen readers (the name and rating are beside it)', drawn.map(d => [d[0], cr(d[1], d[2]).toFixed(2), d[3]]));
  /* the class page's professor row too */
  const cls = await page.evaluate(() => { A.openClass('BUS 3431'); render(true); const el = document.querySelector('#scroll .profrow .pav-t'); const pk = el && el.closest('[data-x]').dataset.x; const out = el && { step: el.dataset.step, want: String(Math.round(ratingOf(pk) * 2) / 2) }; back(); return out; });
  ok(cls && cls.step === cls.want, 'prof circles: a class page’s professor rows use the same colours', cls);
  const top = await page.evaluate(() => { const pk = Object.keys(PROFS).find(k => ratingOf(k) != null && Math.round(ratingOf(k) * 2) === 10); A.openProf(pk); render(true); const el = document.querySelector('#scroll .hero .pav-t'); return el && { step: el.dataset.step, bg: getComputedStyle(el).backgroundColor }; });
  ok(top && top.step === '5' && top.bg === want[10], 'prof circles: a 5.0 professor’s page header circle is green', top);
  const none = await page.evaluate(() => { const pk = 'esme samplesworth'; PROFS[pk].r = null; UI.sheet = null; back(); render(true); const el = [...document.querySelectorAll('#scroll .pav-t')].find(e => e.closest('[data-x]') && e.closest('[data-x]').dataset.x === pk); return el && { step: el.dataset.step, bg: getComputedStyle(el).backgroundColor, label: el.getAttribute('aria-label') }; });
  ok(none && none.step === '' && none.bg === 'rgb(230, 234, 241)', 'prof circles: no rating → a grey circle, never a score colour', none);
  ok(log.errors.length === 0, 'prof circles: no page errors', log.errors);
  await close();
};

/* One rating scale everywhere (Tate, 2026-10-03: "a 5 on everything should be the farthest left green and the worst
   teachers furthest right"). The scale itself is checked from the colours the browser computes; then every place a
   rating is drawn is checked to take ITS step from that one scale. */
tests.ratingGradient = async () => {
  const { page, close, log } = await openApp({});
  await page.waitForFunction(() => TC.ready && TC.profsLoaded, null, { timeout: 8000 });
  const pal = await page.evaluate(() => { const c = (prop, v) => { const e = document.createElement('i'); e.style[prop] = v; document.body.appendChild(e); const o = getComputedStyle(e)[prop]; e.remove(); return o; };
    const out = []; for (let k = 1; k <= 10; k++) out.push({ k, bright: c('backgroundColor', RATE_BRIGHT(k)), dark: c('color', RATE_DARK(k)), pale: c('backgroundColor', RATE_PALE(k)), ink: c('color', RATE_INK(k)) }); return out; });
  const rgb = c => c.match(/\d+(\.\d+)?/g).slice(0, 3).map(Number);
  const hue = c => { const [r, g, b] = rgb(c).map(x => x / 255), mx = Math.max(r, g, b), mn = Math.min(r, g, b), d = mx - mn; if (!d) return 0;
    let h = mx === r ? ((g - b) / d) % 6 : mx === g ? (b - r) / d + 2 : (r - g) / d + 4; h *= 60; return h < 0 ? h + 360 : h; };
  const lum = c => { const v = rgb(c).map(x => { x /= 255; return x <= 0.03928 ? x / 12.92 : ((x + 0.055) / 1.055) ** 2.4; }); return 0.2126 * v[0] + 0.7152 * v[1] + 0.0722 * v[2]; };
  const cr = (a, b) => { const [x, y] = [lum(a), lum(b)].sort((p, q) => q - p); return (x + 0.05) / (y + 0.05); };
  const hs = pal.map(p => hue(p.bright));
  const hd = (a, b) => Math.min(Math.abs(a - b), 360 - Math.abs(a - b));
  const skew = pal.filter(p => p.k < 10 && (hd(hue(p.dark), hue(p.bright)) > 6 || hd(hue(p.pale), hue(p.bright)) > 6));
  ok(!skew.length, 'rating scale: a step’s number and chip are the same hue as its circle', skew.map(p => [p.k / 2, hue(p.bright).toFixed(0), hue(p.dark).toFixed(0), hue(p.pale).toFixed(0)]));
  ok(hs[9] >= 100 && hs[9] <= 150 && hs[5] >= 45 && hs[5] <= 65 && hs[0] <= 12 && hs.every((h, i) => !i || h > hs[i - 1]), 'rating scale: 5.0 is green, 3.0 yellow, 0.5 red, and every half star in between steps along the gradient', hs.map(h => h.toFixed(0)));
  ok(new Set(pal.map(p => p.bright)).size === 10 && new Set(pal.map(p => p.dark)).size === 10, 'rating scale: ten half stars, ten colours', pal);
  ok(pal[9].dark === 'rgb(22, 101, 52)', 'rating scale: a 5’s dark shade is the big 5.0’s green #166534', pal[9]);
  ok(pal.every(p => cr(p.ink, p.bright) >= 4.5 && cr(p.dark, p.pale) >= 4.5 && cr(p.dark, 'rgb(255, 255, 255)') >= 4.5), 'rating scale: initials read (4.5:1+) on their circle; numbers on their pale chip and on white', pal.map(p => [p.k / 2, cr(p.ink, p.bright).toFixed(2), cr(p.dark, p.pale).toFixed(2)]));
  /* not neon (Tate, 2026-10-04: "dont make it so bright it can be more darker green") */
  const hsl = c => { const [r, g, b] = rgb(c).map(x => x / 255), mx = Math.max(r, g, b), mn = Math.min(r, g, b), l = (mx + mn) / 2, d = mx - mn; return { s: d ? d / (1 - Math.abs(2 * l - 1)) : 0, l }; };
  ok(pal.every(p => hsl(p.bright).s <= 0.8 && hsl(p.bright).l <= 0.63 && cr(p.bright, 'rgb(255, 255, 255)') >= 2) && hsl(pal[9].bright).l <= 0.4, 'rating scale: no neon — fills at 80% saturation or less, standing out from white (2:1+), and a 5’s green is a deep one', pal.map(p => [p.k / 2, p.bright, hsl(p.bright).s.toFixed(2), hsl(p.bright).l.toFixed(2), cr(p.bright, 'rgb(255, 255, 255)').toFixed(2)]));
  /* Explore: on every card the circle, the chip and the chip's star are the same half star */
  await click(page, '[data-a="tab"][data-x="explore"]'); await click(page, '[data-a="exMode"][data-x="profs"]'); await settle(page, 400);
  const cards = await page.evaluate(() => [...document.querySelectorAll('#exlist .pcard')].map(c => { const pk = c.dataset.x, r = ratingOf(pk), av = c.querySelector('.pav-t'), ch = c.querySelector('.rchip');
    return r == null ? null : { pk, step: rateStep(r), av: getComputedStyle(av).backgroundColor, ini: getComputedStyle(av).color, chip: ch && getComputedStyle(ch).backgroundColor, num: ch && getComputedStyle(ch).color, star: ch && ch.querySelector('svg').getAttribute('fill'), dark: RATE_DARK(rateStep(r)) }; }).filter(Boolean));
  const off = cards.filter(c => { const p = pal[c.step - 1]; return c.av !== p.bright || c.ini !== p.ink || c.chip !== p.pale || c.num !== p.dark || c.star !== c.dark; });
  ok(cards.length >= 5 && !off.length && new Set(cards.map(c => c.step)).size >= 4, 'rating scale: on each Explore card the circle, the chip and its star are one half star of the one scale', { off, n: cards.length });
  /* a professor's page: AVERAGE's star bright, the big number and its star dark, the review bars 5→1 and a review's stars all on the scale */
  const prof = await page.evaluate(() => { const pk = 'ada examplewood'; PROFS[pk].r = 4.5; A.openProf(pk); render(true);
    const sc = document.getElementById('scroll'), big = sc.querySelector('.card [class^="rt-"]'), avg = sc.querySelector('.hero .avgstar svg'), bars = [...sc.querySelectorAll('.bars .bar u')].map(u => getComputedStyle(u).backgroundColor), rs = sc.querySelector('.tc-revstars .hs-on svg');
    const rv = rs && rs.closest('.review'); return { avg: avg && avg.getAttribute('fill'), num: big && getComputedStyle(big).color, bigStar: big && big.querySelector('svg').getAttribute('fill'), bars, rev: rs && rs.getAttribute('fill'), revV: rv && +(rv.querySelector('.tc-revstars').getAttribute('aria-label') || '').split(' ')[0],
      want: { avg: RATE_BRIGHT(9), fill: RATE_BRIGHT(9) } }; });
  ok(prof.avg === prof.want.avg && prof.num === pal[8].bright && prof.bigStar === prof.want.fill, 'rating scale: a 4.5 professor’s AVERAGE star, big number and its star are all 4.5’s one colour', prof);
  ok(prof.bars.length === 5 && prof.bars.join() === [10, 8, 6, 4, 2].map(k => pal[k - 1].bright).join(), 'rating scale: the 5 → 1 review bars are the 5.0, 4.0, 3.0, 2.0 and 1.0 colours', prof.bars);
  ok(prof.rev && prof.revV > 0 && prof.rev === await page.evaluate(v => RATE_BRIGHT(Math.round(v * 2)), prof.revV), 'rating scale: a review’s stars are its own half star’s colour', prof);
  /* a class page's professor rows, and the class preview sheet's professor row */
  const rows = await page.evaluate(() => { back(); A.openClass('BUS 3431'); render(true);
    const read = b => { const pk = b.dataset.x, st = rateStep(ratingOf(pk)), sv = b.querySelector('.row svg'), num = b.querySelector('.row [class^="rt-"]');
      return { pk, star: sv && sv.getAttribute('fill'), num: num && getComputedStyle(num).color, want: RATE_DARK(st) }; };
    const cls = [...document.querySelectorAll('#scroll .profrow')].filter(b => ratingOf(b.dataset.x) != null).map(read);
    const d = document.createElement('div'); d.innerHTML = secProfRow(cls[0].pk); document.body.appendChild(d); const sec = read(d.querySelector('.profrow')); d.remove();
    const norm = c => { const e = document.createElement('i'); e.style.color = c; document.body.appendChild(e); const v = getComputedStyle(e).color; e.remove(); return v; };
    return { cls, sec, norm: Object.fromEntries([...cls, sec].map(x => [x.want, norm(x.want)])) }; });
  ok(rows.cls.length >= 1 && [...rows.cls, rows.sec].every(x => x.star === x.want && x.num === rows.norm[x.want]), 'rating scale: a class page’s professor rows and the class preview’s professor row use the same half-star dark', rows);
  ok(log.errors.length === 0, 'rating scale: no page errors', log.errors);
  await close();
};

/* People with no photo: a light grey circle with a white person, like Instagram / LinkedIn (Tate, 2026-10-03). */
tests.noPhotoGray = async () => {
  const T = JSON.parse(JSON.stringify(FX.TABLES));
  const rowan = FX.FRIENDS[1].id;
  T.profiles = T.profiles.map(p => p.id === rowan ? Object.assign({}, p, { avatar_url: 'https://photos.example.invalid/rowan.png' }) : p);
  const { page, close, log } = await openApp({ tables: T });
  await page.waitForFunction(() => TC.ready && document.querySelectorAll('.story').length >= 5, null, { timeout: 8000 });
  await tick(page, 400);
  const GREY = 'rgb(218, 221, 227)';
  const st = await page.evaluate(() => [...document.querySelectorAll('.story[data-x] .ring > span')].map(el => ({ id: el.closest('.story').dataset.x, bg: getComputedStyle(el).backgroundColor, svg: !!el.querySelector('svg.nophoto'), txt: el.textContent.trim(), img: !!el.querySelector('img') })));
  ok(st.length === 5 && st.every(x => x.bg === GREY && x.svg && x.txt === ''), 'no photo: every story circle without a photo is light grey with a person, no coloured initials', st);
  ok(st.find(x => x.id === rowan) && st.filter(x => x.id !== rowan).every(x => !x.img), 'no photo: only the friend with a photo carries one (laid over the grey)', st);
  const me = await page.evaluate(() => { const b = document.querySelector('.homehdr .me-btn'); return { bg: getComputedStyle(b).backgroundColor, svg: !!b.querySelector('svg.nophoto'), txt: b.textContent.trim() }; });
  ok(me.bg === GREY && me.svg && me.txt === '', 'no photo: your profile button too', me);
  const ph = await page.evaluate(id => { const d = document.createElement('div'); d.innerHTML = pav(id, 44); const el = d.firstElementChild; return { bg: el.style.background, kids: [...el.children].map(c => c.tagName.toLowerCase()) }; }, rowan);
  ok(/218, 221, 227|#DADDE3|var\(--nophoto\)/i.test(ph.bg) && ph.kids.join() === 'svg,img', 'no photo: a photo sits on top of the grey person, so a photo that fails to load leaves the grey circle', ph);
  await click(page, '[data-a="tab"][data-x="friends"]'); await tick(page, 300);
  const rows = await page.evaluate(() => [...document.querySelectorAll('#fbody .av')].filter(el => !el.querySelector('img')).map(el => ({ bg: getComputedStyle(el).backgroundColor, svg: !!el.querySelector('svg.nophoto'), txt: el.textContent.trim() })));
  ok(rows.length >= 3 && rows.every(x => x.bg === GREY && x.svg && x.txt === ''), 'no photo: the Friends list uses the same grey person', rows);
  await click(page, '[data-a="tab"][data-x="explore"]'); await click(page, '[data-a="exMode"][data-x="profs"]'); await tick(page, 400);
  const pr = await page.evaluate(() => [...document.querySelectorAll('#scroll .pav-t')].map(el => ({ svg: !!el.querySelector('svg'), txt: el.textContent.trim(), bg: getComputedStyle(el).backgroundColor })));
  ok(pr.length >= 5 && pr.every(x => !x.svg && /^[A-Z?]{1,2}$/.test(x.txt) && x.bg !== 'rgb(218, 221, 227)'), 'no photo: professors keep their rating-coloured initials', pr);
  /* onboarding's friend suggestions, and a 1:1 chat whose person isn't loaded yet */
  const onb = await page.evaluate(() => { S.stack[S.tab].push({ s: 'onb', p: { step: 'payoff' } }); render(); return [...document.querySelectorAll('.onb .ava')].filter(e => !e.querySelector('img')).map(e => ({ bg: getComputedStyle(e).backgroundColor, svg: !!e.querySelector('svg.nophoto'), txt: e.textContent.trim() })); });
  ok(onb.length >= 1 && onb.every(x => x.bg === GREY && x.svg && x.txt === ''), 'no photo: onboarding’s friends too', onb);
  const unk = await page.evaluate(() => { const d = document.createElement('div'); d.innerHTML = threadRow({ id: 'zz', kind: 'direct', members: [TC.user.id], senders: [], last: null, last_at: null }); const el = d.querySelector('.av'); return el && { bg: el.style.background, svg: !!el.querySelector('svg.nophoto'), txt: el.textContent.trim() }; });
  ok(unk && /218, 221, 227|DADDE3|var\(--nophoto\)/i.test(unk.bg) && unk.svg && unk.txt === '', 'no photo: a chat whose person isn’t known yet shows the grey person, not a “?”', unk);
  ok(log.errors.length === 0, 'no photo: no page errors', log.errors);
  await close();
};

tests.friendProfile = async () => {
  const { page, close, log } = await openApp({});
  await click(page, '[data-a="tab"][data-x="friends"]');
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
  ok(/Jordan Fixture/.test(t) && /@jfixture/.test(t) && /MAJOR\s*Business Administration/.test(t) && /Junior/.test(t), 'me: name, username, major (labelled) and year', t.slice(0, 200));
  ok(!/jordan\.fixture@calpoly\.edu/.test(t) && !/%/.test(t), 'me (D2): no email and no degree-progress percentage on the profile');
  ok(await page.locator('#scroll .mecard [data-a="openEditProfile"][aria-label="Edit profile"]').count() === 1 && await page.locator('#scroll .btn[data-a="openSettings"], #scroll .btn[data-a="openEditProfile"]').count() === 0 && await page.locator('.topbtns [data-a="openSettings"][aria-label="Settings"]').count() === 1,
    'me (D2): a round pencil edits, the gear is Settings, no Edit profile / Settings buttons');
  /* rows: separate bubbles, all blue, Friends first, semi-bold */
  const rows = await page.evaluate(() => [...document.querySelectorAll('.merows > .merow')].map(r => ({ l: r.querySelector('.merow-l').textContent, v: (r.querySelector('.merow-v') || {}).textContent || '', edge: getComputedStyle(r).borderLeftColor, w: getComputedStyle(r.querySelector('.merow-l')).fontWeight, ic: getComputedStyle(r.querySelector('.merow-i')).backgroundColor, top: r.getBoundingClientRect().top, bottom: r.getBoundingClientRect().bottom })));
  ok(rows.map(r => r.l).join('|').startsWith('Friends|My ratings|Who sees my schedule|Name on my ratings|Degree Progress Report'), 'me (D2): the rows are Friends, My ratings, Who sees my schedule, Name on my ratings, Degree Progress Report', rows.map(r => r.l));
  ok(rows.length >= 5 && rows.every(r => r.edge === rows[0].edge && r.ic === rows[0].ic) && rows[0].edge === 'rgb(191, 211, 255)' && rows[0].ic === 'rgb(227, 236, 255)', 'me (D2): every row has the same blue edge and blue icon (Tate: “make all of these blue”)', rows.map(r => [r.edge, r.ic]));
  ok(rows.every(r => r.w === '600'), 'me (D2): row labels are semi-bold', rows.map(r => r.w));
  ok(rows.every((r, i) => !i || r.top - rows[i - 1].bottom >= 8), 'me (D2): each row is its own bubble with space between', rows.map(r => [r.top, r.bottom]));
  ok(rows[0].v === '5' && rows[1].v === '1 posted' && rows[2].v === 'Friends' && rows[3].v === (FX.MY_REVIEW.share_with_friends ? 'Friends see 1' : 'Anonymous') && rows[4].v === 'Import PDF', 'me (D2): real values — friend count, posted, sharing, name on ratings', rows.map(r => r.v));
  ok(!/Major and concentration/.test(t) && await page.locator('#scroll .tc-rev, #tcMyRevs').count() === 0 && !/Avery Quill/.test(t), 'me (D2): no reviews and no friend list on the profile itself, no Major and concentration row');
  ok(/requirements filled/.test(rows.map(r => r.l).join('|')) || await page.evaluate(() => !(window.TCPL && TC.waived && TC.myHistory)), 'me (D2): the requirements row stays (Tate: “keep in the requirements filled tab”)', rows.map(r => r.l));
  /* My ratings and Friends open their own pages */
  await click(page, '.merow[data-a="openMyRatings"]'); await tick(page, 400);
  ok(await page.evaluate(() => cur().s) === 'myRatings', 'me: My ratings opens its own page');
  await click(page, '[data-a="back"]');
  await click(page, '.merow[data-a="openMyFriends"]'); await tick(page, 300);
  ok(await page.evaluate(() => cur().s) === 'myFriends', 'me: Friends opens its own page');
  await click(page, '[data-a="back"]');
  await click(page, '.merow:has-text("Name on my ratings")'); await tick(page, 300);
  ok(await page.evaluate(() => cur().s) === 'myRatings', 'me: Name on my ratings opens My ratings, where each review says who sees it');
  await click(page, '[data-a="back"]');
  await click(page, '.merow[data-a="openSettings"]'); await tick(page, 300);
  ok(await page.evaluate(() => cur().s) === 'settings', 'me: Who sees my schedule opens Settings');
  /* 2026-10-04 (Tate, "take this out"): no class / friend count tiles on the profile. */
  await click(page, '[data-a="back"]');
  t = await text(page);
  ok(!/free right now/.test(t) && !/\d+\s*classes\s*Fall 2026/.test(t) && await page.locator('.tc-mestats, .tc-stat').count() === 0, 'me: no class or friend count tiles (2026-10-04)', t.slice(0, 300));
  /* Edit and Delete, now on My ratings (2026-10-06) */
  await click(page, '.merow[data-a="openMyRatings"]'); await tick(page, 400);
  await click(page, '[data-a="editReview"]');
  ok(/EDIT YOUR REVIEW OF/.test(await page.locator('.rf').innerText()) && /Save changes/.test(await page.locator('.bottombar').innerText()), 'me: Edit opens the form headed as an edit, with Save changes');
  await click(page, '[data-a="draft"][data-x="stars"][data-y="2"]');
  await click(page, '[data-a="postRating"]'); await tick(page, 600);
  const w = log.writes.filter(x => x.table === 'reviews');
  ok(w.length === 1 && w[0].m === 'PATCH' && /id=eq\.77/.test(w[0].query) && w[0].body.score === 2 && !('professor_key' in w[0].body) && !('user_id' in w[0].body) && !('course' in w[0].body) && w[0].body.would_again === true, 'me: an edit PATCHes that review by id — not its professor or class, and keeps take-again', w);
  ok(await page.evaluate(() => cur().s) === 'myRatings', 'me: saving an edit brings you back to My ratings');
  await click(page, '[data-a="askDeleteReview"]');
  ok(/Delete your review\?/.test(await page.locator('#sheet').innerText()), 'me: delete asks first');
  await click(page, '#sheet [data-a="deleteReview"]'); await tick(page, 400);
  ok(log.writes.some(x => x.table === 'reviews' && x.m === 'DELETE' && /id=eq\.77/.test(x.query)), 'me: delete removes that review by id');
  ok(log.errors.length === 0, 'me: no page errors', log.errors);
  await close();
};

/* The top card (Tate's D2, 2026-10-06): major and concentration in solid green bubbles, labelled, the
   year in a blue bubble beside the concentration with no label; every shape of profile; both themes. */
tests.meBubbles = async () => {
  const { page, close, log } = await openApp({});
  const open = async (P) => { await page.evaluate(P => { Object.assign(TC.profile, P); S.stack[S.tab] = [{ s: 'home' }]; render(true); }, P); await click(page, '.homehdr .me-btn'); await tick(page, 300);
    return page.evaluate(() => { const r = el => el && el.getBoundingClientRect(); const bs = [...document.querySelectorAll('.mebubs .mebub')];
      return bs.map(b => ({ l: (b.querySelector('.mebub-l') || {}).textContent || '', v: b.querySelector('.mebub-v').textContent, tag: b.tagName, act: b.dataset.a || '', bg: getComputedStyle(b).backgroundImage === 'none' ? getComputedStyle(b).backgroundColor : 'gradient', ink: getComputedStyle(b.querySelector('.mebub-v')).color, top: Math.round(r(b).top), left: Math.round(r(b).left), right: Math.round(r(b).right) })); }); };
  let b = await open({ major: 'Business Administration', concentration: 'Financial Management', class_standing: 'Senior' });
  ok(b.length === 3 && b[0].l === 'MAJOR' && b[0].v === 'Business Administration' && b[1].l === 'CONCENTRATION' && b[1].v === 'Financial Management' && b[2].l === '' && b[2].v === 'Senior', 'bubbles: Major, Concentration, and Senior with no “YEAR” label', b);
  ok(b[0].bg === 'rgb(198, 238, 228)' && b[1].bg === b[0].bg && b[0].bg !== 'gradient', 'bubbles: major and concentration are the same solid green (no gradient)', b.map(x => x.bg));
  ok(b[2].bg === 'rgb(214, 228, 255)' && b[2].top === b[1].top && b[2].left > b[1].right, 'bubbles: the year is a blue bubble beside the concentration', b);
  ok(b[0].top < b[1].top, 'bubbles: the major sits above the concentration', b);
  b = await open({ concentration: 'Financial Management concentration' });
  ok(b[1].v === 'Financial Management', 'bubbles: a stored “… concentration” isn’t said twice under its label', b[1]);
  b = await open({ concentration: null, class_standing: 'Senior' });
  ok(b.length === 2 && b[0].l === 'MAJOR' && b[1].v === 'Senior' && b[0].top === b[1].top, 'bubbles: no concentration → the year sits beside the major', b);
  b = await open({ concentration: null, class_standing: null });
  ok(b.length === 1 && b[0].v === 'Business Administration', 'bubbles: no year → no empty year bubble', b);
  b = await open({ major: null, concentration: null, class_standing: 'Junior' });
  ok(b[0].tag === 'BUTTON' && b[0].act === 'openEditProfile' && b[0].v === 'Add your major', 'bubbles: no major → “Add your major” opens Edit profile', b[0]);
  /* contrast, light and dark */
  await page.evaluate(() => { Object.assign(TC.profile, { major: 'Business Administration', concentration: 'Financial Management', class_standing: 'Senior' }); });
  const lum = c => { const m = c.match(/\d+(\.\d+)?/g).map(Number).slice(0, 3).map(v => { v /= 255; return v <= 0.03928 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4; }); return 0.2126 * m[0] + 0.7152 * m[1] + 0.0722 * m[2]; };
  const cr = (a, b) => { const x = lum(a), y = lum(b); return (Math.max(x, y) + 0.05) / (Math.min(x, y) + 0.05); };
  for (const th of ['light', 'dark']) {
    await page.evaluate(th => { try { localStorage.setItem('tc-theme', th); } catch (e) {} applyTheme(true); }, th);
    b = await open({});
    const pairs = await page.evaluate(() => [...document.querySelectorAll('.mebubs .mebub-l, .mebubs .mebub-v, .merow-l, .merow-v, .merow-s')].map(e => { let n = e, bg = 'rgba(0, 0, 0, 0)'; while (n && /rgba\(0, 0, 0, 0\)|transparent/.test(bg)) { bg = getComputedStyle(n).backgroundColor; n = n.parentElement; } return { t: e.textContent, fg: getComputedStyle(e).color, bg }; }));
    const low = pairs.filter(x => cr(x.fg, x.bg) < 4.5).map(x => [x.t, x.fg, x.bg, cr(x.fg, x.bg).toFixed(2)]);
    ok(pairs.length >= 12 && !low.length, `bubbles: every word on the profile is 4.5:1+ (${th})`, low);
  }
  ok(log.errors.length === 0, 'bubbles: no page errors', log.errors);
  await close();
};

/* My ratings, its own page (2026-10-06): cards set apart from each other, a rating-coloured edge, Edit
   and Delete as before, and honest loading / failure / empty states. */
tests.myRatings = async () => {
  const two = [FX.MY_REVIEW, Object.assign({}, FX.MY_REVIEW, { id: 78, professor_name: 'Bram Fixturesen', professor_key: 'bram fixturesen|bus', course: 'BUS 2100', score: 1.5, note: null, share_with_friends: true, created_at: '2026-09-25T00:00:00Z' })];
  const { page, close, log } = await openApp({ rpc: Object.assign({}, FX.RPC, { my_reviews: two }) });
  await openRatings(page);
  const t = await text(page);
  ok(/My ratings/.test(t) && /2\s*posted/.test(t) && /1\s*friends see it’s you/.test(t), 'my ratings: a title and real counts', t.slice(0, 200));
  const c = await page.evaluate(() => [...document.querySelectorAll('.mrlist > .mrcard')].map(e => { const r = e.getBoundingClientRect(), cs = getComputedStyle(e); return { t: e.innerText, top: r.top, bottom: r.bottom, edge: cs.borderLeftColor, ew: cs.borderLeftWidth, bd: cs.borderTopWidth, sh: cs.boxShadow }; }));
  ok(c.length === 2 && /Bram Fixturesen/.test(c[0].t) && /Faro Dummelow/.test(c[1].t), 'my ratings: one card per review, newest first', c.map(x => x.t.slice(0, 30)));
  ok(c.length === 2 && c[1].top - c[0].bottom >= 12 && c.every(x => x.bd === '1px' && x.ew === '6px' && x.sh !== 'none'), 'my ratings: each card stands apart — border, shadow and space between (Tate: “so it doesn’t blend in”)', c.map(x => [x.top, x.bottom, x.bd, x.ew, x.sh]));
  const want = await page.evaluate(() => [RATE_BRIGHT(3), RATE_BRIGHT(8)]);
  const hex = h => { const n = parseInt(h.slice(1), 16); return `rgb(${n >> 16}, ${(n >> 8) & 255}, ${n & 255})`; };
  ok(c[0].edge === hex(want[0]) && c[1].edge === hex(want[1]) && c[0].edge !== c[1].edge, 'my ratings: the edge is the review’s own rating colour (1.5 and 4 differ)', [c.map(x => x.edge), want]);
  ok(/Friends see it’s yours/.test(c[0].t) && /Anonymous/.test(c[1].t) && /Fixture review I wrote\./.test(c[1].t) && /BUS 4445/.test(c[1].t), 'my ratings: who sees each one, the course and your words', c.map(x => x.t));
  ok(await page.locator('.mrcard [data-a="editReview"]').count() === 2 && await page.locator('.mrcard [data-a="askDeleteReview"]').count() === 2, 'my ratings: Edit and Delete on every card');
  ok(await page.locator('.tabbar').count() === 1 && log.errors.length === 0, 'my ratings: tab bar, no page errors', log.errors);
  await close();
  /* failure says so and retries; empty says so */
  let fail = true;
  const o2 = await openApp({ hook: (url) => { if (url.pathname.endsWith('/rpc/my_reviews') && fail) return { status: 500, body: JSON.stringify({ message: 'boom' }) }; return null; }, rpc: Object.assign({}, FX.RPC, { my_reviews: [FX.MY_REVIEW] }) });
  await openRatings(o2.page);
  const t2 = await text(o2.page);
  ok(/Couldn’t load your ratings/.test(t2) && !/No ratings yet/.test(t2) && await o2.page.locator('.mrcard').count() === 0, 'my ratings: a failed load says so, never “No ratings yet”', t2.slice(0, 200));
  fail = false; await click(o2.page, '[data-a="reloadMyRatings"]'); await tick(o2.page, 600);
  ok(await o2.page.locator('.mrcard').count() === 1, 'my ratings: Try again loads them');
  await o2.close();
  const o3 = await openApp({ rpc: Object.assign({}, FX.RPC, { my_reviews: [] }) });
  await openRatings(o3.page);
  ok(/No ratings yet/.test(await text(o3.page)) && await o3.page.locator('.mrstats').count() === 0, 'my ratings: none yet says so, with no count tiles');
  await o3.close();
};

/* A phone never gets the desktop's phone frame (Tate, 2026-10-06: Home shrunk into the middle of his
   iPhone — "don't let it do this"): a touch screen with a phone-sized screen is full-screen even when
   the page is wider than 520 CSS px (page zoom, Request Desktop Website), scaled back to its own size. */
tests.phoneFullBleed = async () => {
  const look = p => p.evaluate(() => { const ph = document.querySelector('.phone'), r = ph.getBoundingClientRect(), tb = document.querySelector('.tabbar').getBoundingClientRect(), cs = getComputedStyle(ph);
    return { pm: document.documentElement.classList.contains('pm'), pz: document.documentElement.classList.contains('pz'), w: Math.round(r.width), h: Math.round(r.height), left: Math.round(r.left), top: Math.round(r.top), radius: cs.borderTopLeftRadius, shadow: cs.boxShadow,
      tabW: Math.round(tb.width), tabBottom: Math.round(tb.bottom), vw: innerWidth, vh: innerHeight, title: (() => { const t = document.querySelector('.homehdr'); return t ? Math.round(t.getBoundingClientRect().height) : 0; })() }; });
  /* an iPhone 16 Pro whose Safari lays the page out 655px wide */
  let o = await openApp({ width: 655, height: 1424, screen: { width: 402, height: 874 }, touch: true });
  let v = await look(o.page);
  ok(v.pm && v.pz && v.left === 0 && v.top === 0 && Math.abs(v.w - v.vw) <= 1 && Math.abs(v.h - v.vh) <= 2 && v.radius === '0px' && v.shadow === 'none', 'phone: a phone page wider than 520px fills the whole screen — no frame, no desk around it', v);
  ok(Math.abs(v.tabW - v.vw) <= 1 && Math.abs(v.tabBottom - v.vh) <= 2, 'phone: the tab bar runs the full width at the bottom of the screen', v);
  const narrow = await openApp({ width: 402, height: 874, port: 8193 });
  const v0 = await look(narrow.page); await narrow.close();
  ok(Math.abs(v.title / (v.vw / 402) - v0.title) <= 2, 'phone: scaled back to the phone’s own size (Home’s header as tall, relative to the screen, as at 402px)', { wide: v.title, zoom: v.vw / 402, normal: v0.title });
  const g = await o.page.evaluate(() => ({ pz: pzNow(), want: innerWidth / 402, tbPad: getComputedStyle(document.querySelector('.tabbar')).paddingBottom, statusPad: getComputedStyle(document.querySelector('.status')).paddingLeft, island: getComputedStyle(document.querySelector('.island')).display, side: document.querySelector('.side') ? getComputedStyle(document.querySelector('.side')).display : 'none', sb: getComputedStyle(document.documentElement).getPropertyValue('--sb').trim() }));
  ok(Math.abs(g.pz - g.want) < 0.01, 'phone: a finger’s travel is read at the app’s own scale (pzNow = page ÷ screen)', g);
  const g0 = await (async () => { const n = await openApp({ width: 402, height: 874, port: 8194 }); const r = await n.page.evaluate(() => ({ tbPad: getComputedStyle(document.querySelector('.tabbar')).paddingBottom, statusPad: getComputedStyle(document.querySelector('.status')).paddingLeft, island: getComputedStyle(document.querySelector('.island')).display, side: document.querySelector('.side') ? getComputedStyle(document.querySelector('.side')).display : 'none' })); await n.close(); return r; })();
  ok(g.tbPad === g0.tbPad && g.statusPad === g0.statusPad && g.island === g0.island && g.side === g0.side, 'phone: the same rules as a phone at its own width (tab bar, top strip, no island, no side panel)', { zoomed: g, normal: g0 });
  await o.page.setViewportSize({ width: 402, height: 874 }); await o.page.waitForTimeout(300);
  const rot = await o.page.evaluate(() => ({ pm: document.documentElement.classList.contains('pm'), pz: document.documentElement.classList.contains('pz'), z: pzNow() }));
  ok(rot.pm && !rot.pz && rot.z === 1, 'phone: when the page comes back to the screen’s width the zoom comes off (re-measured on resize)', rot);
  ok(o.log.errors.length === 0, 'phone: no page errors', o.log.errors);
  await o.close();
  /* rotating / a page exactly the screen's width: full-bleed, no zoom */
  o = await openApp({ width: 390, height: 844, screen: { width: 390, height: 844 }, touch: true });
  v = await look(o.page);
  ok(v.pm && !v.pz && Math.abs(v.w - 390) <= 1, 'phone: at its own width a phone is full-screen with no zoom', v);
  await o.close();
  /* a phone that reports a fine pointer in desktop mode still counts by its touch points */
  o = await openApp({ width: 655, height: 1424, screen: { width: 402, height: 874 }, touch: true, init: () => { const mm = window.matchMedia.bind(window); window.matchMedia = q => /pointer:\s*coarse/.test(q) ? { matches: false, media: q, addEventListener() {}, removeEventListener() {}, addListener() {}, removeListener() {} } : mm(q); } });
  v = await look(o.page);
  ok(v.pm && v.radius === '0px', 'phone: a phone whose browser reports no coarse pointer still fills the screen (touch points)', v);
  await o.close();
  /* a desktop browser and an iPad keep the phone frame */
  o = await openApp({ width: 1200, height: 900, touch: false });
  v = await look(o.page);
  ok(!v.pm && v.w < 420 && v.left > 300 && v.radius === '58px', 'phone: a desktop browser still shows the phone frame', v);
  await o.close();
  o = await openApp({ width: 820, height: 1180, screen: { width: 820, height: 1180 }, touch: true });
  v = await look(o.page);
  ok(!v.pm && v.radius === '58px', 'phone: an iPad (a large touch screen) still shows the phone frame', v);
  await o.close();
};

/* Review fixes (2026-10-06): a failing Try again never breaks the page or the Rate tab; a failed reload
   after a delete never reads as "none"; every word on My ratings is 4.5:1+ in both themes. */
tests.myRatingsFail = async () => {
  let fail = true;
  const { page, close, log } = await openApp({ hook: (url) => url.pathname.endsWith('/rpc/my_reviews') && fail ? { status: 500, body: JSON.stringify({ message: 'boom' }) } : null, rpc: Object.assign({}, FX.RPC, { my_reviews: [FX.MY_REVIEW] }) });
  await openRatings(page);
  ok(await page.locator('.tc-row-err, .row-err').count() === 0 && /Couldn’t load your ratings/.test(await text(page)), 'my ratings fail: says so');
  await click(page, '[data-a="reloadMyRatings"]'); await tick(page, 600);
  const t = await text(page);
  ok(/Couldn’t load your ratings/.test(t) && !/Something went wrong/.test(t), 'my ratings fail: Try again that fails again still says so (no broken screen)', t.slice(0, 200));
  await click(page, '[data-a="back"]');
  ok(/Name on my ratings\s*Couldn’t load/.test(await text(page)), 'my ratings fail: the profile row says Couldn’t load, not Anonymous');
  await click(page, '[data-a="tab"][data-x="rate"]'); await tick(page, 400);
  ok(!/Something went wrong/.test(await text(page)) && log.errors.length === 0, 'my ratings fail: the Rate tab still works after a failed Try again', log.errors);
  await close();
  /* a delete whose reload fails */
  let off = false;
  const o2 = await openApp({ hook: (url) => url.pathname.endsWith('/rpc/my_reviews') && off ? { status: 500, body: JSON.stringify({ message: 'boom' }) } : null, tables: Object.assign({}, FX.TABLES, { reviews: [Object.assign({}, FX.MY_REVIEW)] }), rpc: Object.assign({}, FX.RPC, { my_reviews: [FX.MY_REVIEW] }) });
  await openRatings(o2.page);
  off = true; await click(o2.page, '[data-a="askDeleteReview"]'); await click(o2.page, '#sheet [data-a="deleteReview"]'); await tick(o2.page, 600);
  const t2 = await text(o2.page);
  ok(!/No ratings yet/.test(t2) && /Couldn’t load your ratings/.test(t2), 'my ratings fail: a reload that fails after a delete says so, never “No ratings yet”', t2.slice(0, 200));
  await o2.close();
};
tests.myRatingsContrast = async () => {
  const two = [FX.MY_REVIEW, Object.assign({}, FX.MY_REVIEW, { id: 78, share_with_friends: true, score: 2 })];
  const { page, close, log } = await openApp({ rpc: Object.assign({}, FX.RPC, { my_reviews: two }) });
  const lum = c => { const m = c.match(/\d+(\.\d+)?/g).map(Number).slice(0, 3).map(v => { v /= 255; return v <= 0.03928 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4; }); return 0.2126 * m[0] + 0.7152 * m[1] + 0.0722 * m[2]; };
  const cr = (a, b) => { const x = lum(a), y = lum(b); return (Math.max(x, y) + 0.05) / (Math.min(x, y) + 0.05); };
  for (const th of ['light', 'dark']) {
    await page.evaluate(th => { try { localStorage.setItem('tc-theme', th); } catch (e) {} applyTheme(true); S.stack[S.tab] = [{ s: 'home' }]; render(true); }, th);
    await openRatings(page);
    const pairs = await page.evaluate(() => [...document.querySelectorAll('.mrstat b, .mrstat span, .mrname, .mrago, .mrtag, .mrcard .tc-revnote, .mrcard .code')].map(e => { let n = e, bg = 'rgba(0, 0, 0, 0)'; while (n && /rgba\(0, 0, 0, 0\)|transparent/.test(bg)) { bg = getComputedStyle(n).backgroundColor; n = n.parentElement; } return { t: e.textContent, fg: getComputedStyle(e).color, bg }; }));
    const low = pairs.filter(x => cr(x.fg, x.bg) < 4.5).map(x => [x.t, x.fg, x.bg, cr(x.fg, x.bg).toFixed(2)]);
    ok(pairs.length >= 10 && !low.length, `my ratings: every word 4.5:1+ (${th})`, low);
    const small = await page.evaluate(() => [...document.querySelectorAll('#scroll .mrcard button, #scroll .topbtns button')].map(b => [b.textContent.trim(), Math.round(b.getBoundingClientRect().height)]).filter(x => x[1] < 44));
    ok(!small.length, `my ratings: every button 44px tall (${th})`, small);
  }
  ok(log.errors.length === 0, 'my ratings contrast: no page errors', log.errors);
  await close();
};
tests.myFriendsFail = async () => {
  let fail = true;
  const { page, close, log } = await openApp({ hook: (url, m) => url.pathname.endsWith('/friend_requests') && m === 'GET' && fail ? { status: 500, body: '{"message":"boom"}' } : null });
  await page.waitForFunction(() => TC.ready, null, { timeout: 8000 });
  await click(page, '.homehdr .me-btn'); await tick(page, 400);
  ok(/Friends\s*Couldn’t load/.test(await text(page)), 'my friends fail: the profile row says Couldn’t load, never 0');
  await click(page, '.merow[data-a="openMyFriends"]'); await tick(page, 300);
  const t = await text(page);
  ok(/Couldn’t load your friends/.test(t) && !/No friends yet/.test(t) && !/Friends\s*0/.test(t), 'my friends fail: the page says so, with no count and never “No friends yet”', t.slice(0, 200));
  fail = false; await click(page, '[data-a="reloadMyFriends"]'); await tick(page, 1500);
  const n = await page.evaluate(() => document.querySelectorAll('#mflist .mfname').length);
  ok(n === 5, 'my friends fail: Try again loads them', n);
  ok(log.errors.length === 0, 'my friends fail: no page errors', log.errors);
  await close();
};

/* Friends, its own page (2026-10-06): everyone A–Z, a search, and a ⋯ with only Remove friend, Report
   and Block. No friend requests on it. */
tests.myFriends = async () => {
  const { page, close, log } = await openApp({});
  await page.evaluate(() => { const id = TC.friends.find(x => PEOPLE[x].name === 'Rowan Testa'); PEOPLE[id].major = 'Economics'; });
  await click(page, '.homehdr .me-btn'); await tick(page, 600);
  await click(page, '.merow[data-a="openMyFriends"]'); await tick(page, 400);
  const names = await page.evaluate(() => [...document.querySelectorAll('#mflist .mfname')].map(e => e.textContent));
  ok(names.join('|') === 'Avery Quill|Harper Mock|Quinn Sample|Rowan Testa|Sky Placeholder', 'my friends: every friend, A–Z', names);
  const t = await text(page);
  ok(/Friends\s*5/.test(t) && /Economics/.test(t), 'my friends: the count, and a friend’s major under their name', t.slice(0, 200));
  ok(await page.locator('#scroll [data-a="acceptReq"], #scroll [data-a="declineReq"]').count() === 0 && !/request/i.test(t), 'my friends: no friend requests here (Tate: “dont include the friends request”)');
  await page.locator('#myfq').fill('qu'); await tick(page, 100);
  let n2 = await page.evaluate(() => [...document.querySelectorAll('#mflist .mfname')].map(e => e.textContent));
  ok(n2.join('|') === 'Avery Quill|Quinn Sample' && await page.locator('#myfq').evaluate(e => e === document.activeElement), 'my friends: search narrows the list as you type and keeps the keyboard up', n2);
  await page.locator('#myfq').fill('@rtes'); await tick(page, 100);
  n2 = await page.evaluate(() => [...document.querySelectorAll('#mflist .mfname')].map(e => e.textContent));
  ok(n2.join('|') === 'Rowan Testa', 'my friends: search by @handle', n2);
  await page.locator('#myfq').fill('zzz'); await tick(page, 100);
  ok(/No friends match “zzz”/.test(await text(page)), 'my friends: no match says so');
  await page.locator('#myfq').fill(''); await tick(page, 100);
  const AV = FX.FRIENDS[0].id;
  const more = page.locator(`.mfmore[data-x="${AV}"]`);
  const box = await more.boundingBox();
  ok(box && box.width >= 44 && box.height >= 44 && await more.getAttribute('aria-label') === 'More for Avery', 'my friends: each row has a 44px ⋯ named for the friend', box);
  await more.click(); await settle(page);
  const acts = await page.evaluate(() => [...document.querySelectorAll('#sheet [data-a]')].map(b => b.dataset.a).filter(a => a !== 'closeSheet'));
  ok(acts.join('|') === 'friendRmAsk|reportAsk|blockAsk', 'my friends: the ⋯ has only Remove friend, Report and Block', acts);
  await click(page, '#sheet [data-a="friendRmAsk"]'); await click(page, '#sheet [data-a="rmFriend"]'); await settle(page, 600);
  const w = log.writes.filter(x => x.table === 'friend_requests' && x.m === 'DELETE');
  const after = await page.evaluate(() => ({ s: cur().s, names: [...document.querySelectorAll('#mflist .mfname')].map(e => e.textContent), n: document.querySelector('.mfhd span').textContent }));
  ok(w.length === 1 && w[0].query.includes(AV) && after.s === 'myFriends' && !after.names.includes('Avery Quill') && after.n === '4', 'my friends: Remove friend deletes the friendship and you stay on the list, one shorter', { w: w.length, after });
  await click(page, '.mfmain >> nth=0'); await tick(page, 400);
  ok(await page.evaluate(() => cur().s) === 'friend', 'my friends: a row opens their page');
  ok(log.errors.length === 0, 'my friends: no page errors', log.errors);
  await close();
};

tests.meNothingChanged = async () => {
  /* RLS refuses a delete by changing nothing: that must not be reported as done. */
  const { page, close } = await openApp({ rpc: Object.assign({}, FX.RPC, { my_reviews: [FX.MY_REVIEW] }) });
  await openRatings(page);
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
  ok(await page.evaluate(() => cur().s) === 'me' && await page.locator('#scroll [aria-label="Edit profile"]').count() === 1, 'profile button: Home still opens the profile page');
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
  await click(page, '#sheet .xbtn');
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

/* The section preview: the professor and friends look tappable; no campus (Tate, 2026-10-03). */
tests.secSheetLinks = async () => {
  const { page, close, log } = await openApp({});
  const sky = FX.FRIENDS[2].id;
  await page.waitForFunction(() => TC.ready && TC.seatsLoaded, null, { timeout: 8000 });
  /* Real Cal Poly rows carry the campus in "location" — never shown. */
  const sec = await page.evaluate(sky => { const s = personSecs(sky).find(x => x.code === 'BUS 3438'); SEC[s.id].location = 'Cal Poly-San Luis Obispo';
    const r = ratingOf(s.prof); return { id: s.id, prof: s.prof, name: profName(s.prof), r: r == null ? null : r.toFixed(1), when: secWhen(SEC[s.id]).replace(/<[^>]+>/g, '') }; }, sky);
  await click(page, `#hf-${sky} .g-b[data-x="BUS 3438"]`); await tick(page, 400);
  const sh = (await page.locator('#sheet').innerText()).replace(/\s+/g, ' ');
  ok(!/Cal Poly|San Luis Obispo|Bldg/.test(sh), 'sec links: the campus is gone from the preview', sh.slice(0, 260));
  const line = (await page.locator('#sheet .secwhen').innerText()).replace(/\s+/g, ' ');
  ok(line.includes(sec.when) && /seat|Full|Waitlist/i.test(line), 'sec links: time and seats share one line under the title', { line, when: sec.when });
  const pr = await page.evaluate(() => { const b = document.querySelector('#sheet button.profrow'); if (!b) return null; const r = b.getBoundingClientRect();
    return { a: b.dataset.a, x: b.dataset.x, t: b.innerText.replace(/\s+/g, ' '), h: Math.round(r.height), chev: !!(b.lastElementChild && b.lastElementChild.tagName === 'SPAN' && b.lastElementChild.querySelector('svg')) }; });
  ok(pr && pr.a === 'openProf' && pr.x === sec.prof && pr.t.includes(sec.name) && pr.h >= 44 && pr.chev, 'sec links: the professor is a 44px+ row with a chevron that opens their page', { pr, sec });
  ok(pr && (sec.r ? pr.t.includes(sec.r) : /No ratings yet/.test(pr.t)), 'sec links: the row carries their real rating (or says there is none)', { pr, sec });
  const pill = await page.evaluate(sky => { const b = document.querySelector(`#sheet .secppl[data-x="${sky}"]`); if (!b) return null; const cs = getComputedStyle(b), r = b.getBoundingClientRect();
    return { a: b.dataset.a, tag: b.tagName, bg: cs.backgroundColor, sheetBg: getComputedStyle(document.querySelector('#sheet .sheet')).backgroundColor, h: Math.round(r.height), chev: !!b.querySelector('svg'), you: [...document.querySelectorAll('#sheet [data-a="openFriend"]')].some(e => /\bYou\b/.test(e.innerText)) }; }, sky);
  ok(pill && pill.tag === 'BUTTON' && pill.a === 'openFriend' && pill.h >= 44 && pill.chev && pill.bg !== pill.sheetBg && !/rgba\(0, 0, 0, 0\)/.test(pill.bg) && !pill.you, 'sec links: a friend is a filled chip with a chevron (you are not a button)', pill);
  await click(page, '#sheet button.profrow'); await tick(page, 600);
  ok(await page.evaluate(() => cur().s === 'profDetail' && !UI.sheet) && (await text(page)).includes(sec.name), 'sec links: tapping the professor opens their page', await page.evaluate(() => cur()));
  /* A section with no instructor listed: said plainly, and nothing to tap. */
  await page.evaluate(id => { back(); SEC[id].prof = null; }, sec.id); await tick(page, 300);
  await page.evaluate(id => A.secSheet('BUS 3438', id), sec.id); await tick(page, 400);
  const st = await page.evaluate(() => ({ t: document.querySelector('#sheet .profrow') && document.querySelector('#sheet .profrow').innerText, btn: document.querySelectorAll('#sheet [data-a="openProf"]').length }));
  ok(/Instructor not assigned/.test(st.t || '') && st.btn === 0, 'sec links: no instructor listed — said plainly, and not a button', st);
  /* On a friend's page, their class → their own chip: the sheet closes, the same page is not pushed again. */
  await page.evaluate(sky => A.openFriend(sky), sky); await tick(page, 500);
  const d0 = await page.evaluate(() => S.stack[S.tab].length);
  await page.evaluate(id => A.secSheet('BUS 3438', id), sec.id); await tick(page, 400);
  await click(page, `#sheet .secppl[data-x="${sky}"]`); await tick(page, 400);
  const d1 = await page.evaluate(sky => ({ n: S.stack[S.tab].length, s: cur().s, id: cur().p.id === sky, sheet: !!UI.sheet }), sky);
  ok(d1.n === d0 && d1.s === 'friend' && d1.id && !d1.sheet, 'sec links: tapping the friend whose page you are on just closes the sheet', { d0, d1 });
  ok(log.errors.length === 0, 'sec links: no page errors', log.errors);
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
/* Teaching rows on a professor's page (2026-10-03): no "N sec", a bold blue arrow, the name on up to two lines;
   and no "Tap + to add a section…" line on a class page. */
tests.teachRows = async () => {
  const { page, close } = await openApp({});
  const tick2 = async (ms = 500) => { await page.clock.runFor(ms); await page.waitForTimeout(120); };
  const pid = await page.evaluate(() => Object.keys(PROFS).filter(k => profCourses(k).length >= 2).sort((a, b) => Math.max(...profCourses(b).map(c => course(c).short.length)) - Math.max(...profCourses(a).map(c => course(c).short.length)))[0]);
  ok(!!pid, 'teach: a fixture professor teaches 2+ classes', pid);
  await page.evaluate(id => { const c = profCourses(id)[0]; course(c).title = 'Seminar in Advanced Topics of Partial Differential Equations and Applied Analysis'; go('profDetail', { id }); }, pid); await tick2();
  const rows = await page.locator('.teach').evaluateAll(bs => bs.map(b => { const nm = b.querySelector('.teach-nm'), go = b.querySelector('.teach-go'), svg = go && go.querySelector('svg'), r = b.getBoundingClientRect(), nr = nm.getBoundingClientRect(), lh = parseFloat(getComputedStyle(nm).lineHeight);
    return { t: b.innerText, x: b.dataset.x, a: b.dataset.a, h: r.height, color: go && getComputedStyle(go).color, w: svg && svg.getAttribute('stroke-width'), sz: svg && svg.getAttribute('width'), lines: Math.round(nr.height / lh), clipped: nm.scrollWidth > nm.clientWidth + 1, inside: nr.right <= r.right && go.getBoundingClientRect().right <= r.right }; }));
  const blue = await page.evaluate(() => { const d = document.createElement('i'); d.style.color = 'var(--blue)'; document.body.appendChild(d); const c = getComputedStyle(d).color; d.remove(); return c; });
  ok(rows.length >= 2 && rows.every(r => !/\bsecs?\b/.test(r.t)), 'teach: no section count on the rows', rows.map(r => r.t));
  const full = await page.evaluate(id => profCourses(id).map(c => course(c).title), pid);
  ok(rows.every((r, i) => r.t.includes(full[i]) && !/…/.test(r.t)), 'teach: rows show the full class title, not the cut-short name', { rows: rows.map(r => r.t), full });
  ok(rows.every(r => r.color === blue && r.w === '2.8' && r.sz === '20'), 'teach: each row has a 20px blue arrow at a 2.8 stroke', { rows, blue });
  ok(rows.every(r => r.lines >= 1 && r.lines <= 2 && !r.clipped && r.inside && r.h >= 44), 'teach: the name takes one or two lines, nothing spills, rows 44px+', rows);
  await page.setViewportSize({ width: 320, height: 760 }); await tick2();
  const narrow = await page.locator('.teach-nm').evaluateAll(ns => ns.map(n => Math.round(n.getBoundingClientRect().height / parseFloat(getComputedStyle(n).lineHeight))));
  ok(narrow.every(l => l <= 2) && narrow[0] === 2, 'teach: at 320px a very long name wraps to two lines and stops there', narrow);
  await page.locator('.teach').first().click(); await tick2();
  ok(await page.evaluate(() => cur().s === 'classDetail') && await page.locator('.hero').count() === 1, 'teach: tapping a row opens the class', await page.evaluate(() => cur()));
  await page.evaluate(() => A.openClass('BUS 4401')); await tick2();
  const t = await text(page);
  ok(/Sections/.test(t) && !/Tap \+ to add/.test(t) && !/seats as of/.test(t), 'class page: no "Tap + to add a section…" line under Sections', t.slice(0, 600));
  await close();
};

/* A professor's header stars (2026-10-03): AVERAGE's star in the rating's colour (rateTone), the Rate star an outline, like the Rate tab (12:00). */
tests.profStars = async () => {
  const { page, close } = await openApp({});
  const tick2 = async (ms = 500) => { await page.clock.runFor(ms); await page.waitForTimeout(120); };
  const pid = await page.evaluate(() => Object.keys(PROFS).find(k => ratingOf(k) != null));
  const look = async r => {
    await page.evaluate(([id, r]) => { PROFS[id].r = r; go('profDetail', { id }); render(true); }, [pid, r]); await tick2();
    return page.evaluate(() => { const st = [...document.querySelectorAll('.hero .stat')].find(x => /AVERAGE/.test(x.innerText)), b = st.querySelector('.avgstar'), sv = b && b.querySelector('svg'), big = document.querySelector('.card [class^="rt-"]');
      const rb = document.querySelector('.hero [data-a="rateProf"]'), rs = rb.querySelector('.rstar svg'), br = rb.getBoundingClientRect(), sr = rs && rs.getBoundingClientRect();
      let gap = null, dy = null; if (b && b.nextSibling) { const rg = document.createRange(); rg.selectNodeContents(b.nextSibling); const tr = rg.getBoundingClientRect(), cr = b.getBoundingClientRect(); gap = tr.left - cr.right; dy = Math.abs((tr.top + tr.bottom) / 2 - (cr.top + cr.bottom) / 2); }
      return { gap, dy, t: st.innerText.trim(), fill: sv && sv.getAttribute('fill'), bg: b && getComputedStyle(b).backgroundColor, w: b && b.getBoundingClientRect().width, bigK: big && big.className, k: b && b.className,
        rate: rs && rs.getAttribute('fill'), rstroke: rs && rs.getAttribute('stroke'), rcol: rs && getComputedStyle(rs).color, bcol: getComputedStyle(rb).color, rpath: rs && rs.innerHTML, tabpath: (document.querySelector('.tab[data-x="rate"] svg') || {}).innerHTML, amber: /D97706/i.test(rb.innerHTML), mid: sr && Math.abs((sr.top + sr.bottom) / 2 - (br.top + br.bottom) / 2) }; });
  };
  const hi = await look(5), lo = await look(1), md = await look(3.4);
  const hb = await page.evaluate(() => [RATE_BRIGHT(10), RATE_BRIGHT(2), RATE_BRIGHT(7)]);
  ok(hi.fill === hb[0] && lo.fill === hb[1] && md.fill === hb[2] && /^5\.0$/.test(hi.t.replace(/AVERAGE\s*/, '')), 'prof stars: AVERAGE’s star is its half star’s one colour (green at 5, red at 1)', { hi, lo, md, hb });
  /* one green (2026-10-04): the header circle, AVERAGE's star, the big number and the big star are one colour at every half star */
  const one = [];
  for (const k of [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]) {
    await page.evaluate(([id, r]) => { PROFS[id].r = r; render(true); }, [pid, k / 2]); await tick2(100);
    one.push(await page.evaluate(k => { const norm = c => { const e = document.createElement('i'); e.style.color = c; document.body.appendChild(e); const v = getComputedStyle(e).color; e.remove(); return v; };
      const circ = document.querySelector('.hero .pav-t'), avg = document.querySelector('.hero .avgstar svg'), big = document.querySelector('.card [class^="rt-"]');
      return { k, want: norm(RATE_BRIGHT(k)), circle: getComputedStyle(circ).backgroundColor, avg: norm(avg.getAttribute('fill')), num: getComputedStyle(big).color, bigStar: norm(big.querySelector('svg').getAttribute('fill')) }; }, k));
  }
  const ring = await page.evaluate(() => getComputedStyle(document.querySelector('.hero .pav-t')).boxShadow);
  ok(ring === 'none', 'prof page: the header circle has no white ring (2026-10-04)', ring);
  ok(one.every(o => o.circle === o.want && o.avg === o.want && o.num === o.want && o.bigStar === o.want) && new Set(one.map(o => o.want)).size === 10, 'prof page: circle, AVERAGE star, big number and big star are one colour at every half star', one.filter(o => !(o.circle === o.want && o.avg === o.want && o.num === o.want && o.bigStar === o.want)));
  ok([hi, lo, md].every(x => x.k && x.bigK && x.k.split(' ')[1] === x.bigK.split(' ')[0]), 'prof stars: the header star matches the big rating’s colour below it', [hi, lo, md].map(x => [x.k, x.bigK]));
  ok([hi, lo, md].every(x => /rgba\(0, 0, 0, 0\)|transparent/.test(x.bg) && x.w >= 14 && x.w <= 18 && x.gap >= 3 && x.dy <= 2), 'prof stars: a plain star (no circle) about the old ★’s size, beside the number and centred on it', hi);
  ok([hi, lo, md].every(x => x.rate === 'none' && x.rstroke === 'currentColor' && x.rcol === x.bcol && x.tabpath && x.rpath === x.tabpath && !x.amber && x.mid <= 2), 'prof stars: the Rate button’s star is the empty star from the Rate tab, in the button’s colour, centred', { hi, lo });
  await page.evaluate(id => { PROFS[id].r = null; render(true); }, pid); await tick2();
  ok(await page.locator('.hero .avgstar').count() === 0, 'prof stars: no rating, no star');
  await close();
};

/* Explore professor cards (2026-10-04, option D): "N ratings" sits under the star chip, centred on it; the middle
   line keeps only "N% would take again"; a professor with no chip keeps the count / "No ratings yet" there. */
tests.profCardCount = async () => {
  for (const w of [390, 320]) {
    const { page, close, log } = await openApp({ port: 8190, width: w });
    await page.waitForFunction(() => TC.ready && TC.profsLoaded, null, { timeout: 8000 });
    await click(page, '[data-a="tab"][data-x="explore"]');
    await click(page, '[data-a="exMode"][data-x="profs"]'); await settle(page, 500);
    const cards = await page.evaluate(() => [...document.querySelectorAll('#exlist .pcard')].map(c => {
      const pk = c.dataset.x, ch = c.querySelector('.rchip'), n = c.querySelector('.prt-n'), mid = c.querySelector(':scope > .muted'), cr = c.getBoundingClientRect();
      const a = ch && ch.getBoundingClientRect(), b = n && n.getBoundingClientRect();
      return { pk, nm: PROFS[pk].name, r: ratingOf(pk), count: PROFS[pk].count || 0, want: PROFS[pk].count ? nRatings(PROFS[pk].count) : null,
        chip: !!ch, n: n && n.textContent, mid: mid ? mid.textContent : '', under: a && b ? b.top >= a.bottom - 0.5 && Math.abs((a.left + a.right) / 2 - (b.left + b.right) / 2) <= 1.5 : null,
        inside: b ? b.right <= cr.right - 8 && b.left >= cr.left : true, oneLine: b ? b.height < 24 : true };
    }));
    const rated = cards.filter(c => c.r != null && c.count);
    ok(rated.length >= 3 && rated.every(c => c.chip && c.n === c.want && c.under && c.inside && c.oneLine), `prof cards @${w}: “N ratings” sits under the star chip, centred, on one line inside the card`, rated);
    ok(rated.every(c => !/ratings?\b/.test(c.mid)), `prof cards @${w}: the count is not repeated on the middle line`, rated.map(c => [c.nm, c.mid]));
    const ada = cards.find(c => /Ada/.test(c.nm));
    ok(ada && ada.mid === '67% would take again', `prof cards @${w}: the middle line keeps only “would take again”`, ada);
    {
      await page.evaluate(() => { const k = Object.keys(PROFS).find(k => /Esme/.test(PROFS[k].name)); PROFS[k].r = null; render(true); }); await settle(page, 300);
      const rightOf = () => { const c = [...document.querySelectorAll('#exlist .pcard')].find(c => c.querySelector('.rchip')); return c.querySelector('.prt').getBoundingClientRect().right; };
      const esme = await page.evaluate(rightOf => { const ratedRight = eval(rightOf)(); const c = [...document.querySelectorAll('#exlist .pcard')].find(c => /Esme/.test(c.innerText)); const n = c && c.querySelector('.prt-n');
        return c ? { chip: !!c.querySelector('.rchip'), n: n && n.textContent, right: n && n.closest('.prt').getBoundingClientRect().right, ratedRight, mid: (c.querySelector(':scope > .muted') || {}).textContent || '' } : null; }, rightOf.toString());
      ok(esme && !esme.chip && /^\d+ ratings?$/.test(esme.n) && Math.abs(esme.right - esme.ratedRight) <= 1 && !/ratings?\b/.test(esme.mid), `prof cards @${w}: no rating chip → the count is on the right, where a rated card’s count sits (Tate, 2026-10-04)`, esme);
      const edge = await page.evaluate(() => { const ks = Object.keys(PROFS), e = ks.find(k => /Esme/.test(PROFS[k].name)), d = ks.find(k => /Dov/.test(PROFS[k].name));
        PROFS[e].count = 0; PROFS[d].count = 0; render(true);
        const card = re => [...document.querySelectorAll('#exlist .pcard')].find(c => re.test(c.innerText));
        const ce = card(/Esme/), cd = card(/Dov/);
        const nr = ce.querySelector('.prt-n'), nm = ce.querySelector('.grow').getBoundingClientRect(), nb = nr && nr.getBoundingClientRect();
        const tr = document.createRange(); tr.selectNodeContents(ce.querySelector('.grow > div')); const nameRight = Math.max(...[...tr.getClientRects()].map(r => r.right));
        return { esme: { mid: (ce.querySelector(':scope > .muted') || {}).textContent || '', side: nr && nr.textContent, beside: !!nb && nb.left >= nm.right - 1 && nb.top < nm.bottom && nb.bottom > nm.top, clear: !!nb && nameRight <= nr.closest('.prt').getBoundingClientRect().left + 0.5, align: getComputedStyle(ce.querySelector(':scope > .row')).alignItems, st: !!reviewStats(e) },
                 dov: { chip: !!cd.querySelector('.rchip'), n: !!cd.querySelector('.prt-n'), text: cd.innerText, st: !!reviewStats(d) } }; });
      ok(!edge.esme.st && edge.esme.side === 'No ratings yet' && edge.esme.beside && edge.esme.clear && edge.esme.mid === '' && edge.esme.align === 'center', `prof cards @${w}: no rating, no count, no reviews → “No ratings yet” on the right beside the name, never over it, name centred on the avatar`, edge.esme);
      ok(edge.dov.chip && !edge.dov.n && !/No ratings yet|\bratings?\b/.test(edge.dov.text), `prof cards @${w}: a chip with no count shows no count and never “No ratings yet”`, edge.dov);
    }
    ok(log.errors.length === 0, `prof cards @${w}: no page errors`, log.errors);
    await close();
  }
};

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
  ok(t.indexOf('Before') >= 0 && t.indexOf('Before') < t.indexOf('TermChamp’s picks'), 'prereq: the card sits above the rest of the Planner (the picks)', t.slice(0, 300));
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
  ok(await page.locator('.tc-pqfor').count() === 0 && /TermChamp’s picks/.test(await text(page)), 'prereq: the card closes and the Planner stays');
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
  await click(page, '[data-a="tab"][data-x="schedule"]'); await click(page, '[data-a="schedTab"][data-x="past"]'); await tick(page, 2500);
  let t = await text(page);
  ok(/Business Administration/.test(t) && /2 of 33\s*requirements filled/.test(t) && /4 in progress/.test(t), 'planner: the desktop’s ledger — 2 of 33 filled (31 + the 2 choice slots, checked since 2026-10-02), 4 in progress (one via the ENGL 1134 waiver)', (t.match(/[\s\S]{0,40}requirements filled[\s\S]{0,60}/) || [''])[0]);
  ok(/We can’t check 10 from your record/.test(t), 'planner: what it can’t judge is listed, not counted');
  /* 2026-10-06: the ledger, flowchart and record are Past classes; the full Still need list is folded at the foot of the Planner */
  await click(page, '[data-a="schedTab"][data-x="planner"]'); await tick(page, 600);
  ok(await page.locator('details.pk-all').evaluate(d => !d.open), 'planner: “Still need · all” starts folded under the picks');
  await click(page, 'details.pk-all > summary'); await tick(page, 200);
  const t2 = await text(page);
  ok(await page.locator('details.pk-all').evaluate(d => d.open), 'planner: tapping “Still need · all” opens it');
  ok(/Still need[\s\S]*BUS 1100[\s\S]*Career Readiness I/.test(t2), 'planner: still-need list in flowchart order');
  /* GEs left are part of "Still need", not a card of their own (Tate, 2026-10-03). */
  const sn = await page.evaluate(() => { const cards = [...document.querySelectorAll('.tc-sec')].filter(c => /^Still need/.test(c.querySelector('.tc-sech')?.innerText.trim() || ''));
    const c = cards[0]; if (!c) return null;
    return { cards: cards.length, n: +c.querySelector('.tc-sech').innerText.replace(/\D+/g, ''), rows: c.querySelectorAll('.li').length, ge: c.querySelectorAll('[data-a="plGe"]').length,
      heads: [...c.querySelectorAll('.tc-needh')].map(h => h.innerText.replace(/\s+/g, ' ').trim()), order: [...c.children].map(x => x.classList.contains('tc-needh') ? 'H' : x.dataset.a === 'plGe' ? 'G' : x.classList.contains('li') ? 'C' : '').filter(Boolean).join(''),
      geCard: [...document.querySelectorAll('.tc-sech')].some(h => /GE areas and electives/.test(h.innerText)) }; });
  ok(sn && sn.cards === 1 && !sn.geCard && sn.ge > 0 && sn.rows === sn.n, 'planner: one “Still need” card holds the classes and the GE areas, and its count is every row in it', sn);
  ok(sn && sn.heads.length === 2 && /^CLASSES \d+$/i.test(sn.heads[0]) && /^(GENERAL EDUCATION|GE AND ELECTIVES) \d+$/i.test(sn.heads[1]) && /^HC+HG+/.test(sn.order), 'planner: labelled “Classes” then “General education”, each with its count', sn);
  await click(page, '[data-a="schedTab"][data-x="past"]'); await tick(page, 400);
  const key = await page.evaluate(() => { const k = document.querySelector('.tc-key'); const row = document.querySelector('.tc-cell.taking .tc-dot');
    return k && { t: k.innerText.replace(/\s+/g, ' ').trim(), half: [...k.querySelectorAll('.tc-dot')][1]?.innerText, rowHalf: row ? row.innerText : null, oneLine: new Set([...k.children].map(x => Math.round(x.getBoundingClientRect().top))).size }; });
  for (let i = 0; i < 6; i++) { const closed = page.locator('[data-a="plYear"][aria-expanded="false"]'); if (!(await closed.count())) break; await closed.first().click(); await tick(page, 150); }
  key.rowHalf = await page.evaluate(() => { const r = document.querySelector('.tc-cell.taking .tc-dot'); return r ? r.innerText : null; });
  ok(key && key.t === '✓ Done ◐ In progress To do ? Can’t check' && key.half === '◐' && key.rowHalf === key.half && key.oneLine === 1, 'planner: the flowchart has a key for its marks — ◐ is In progress — on one line', key);
  await page.setViewportSize({ width: 375, height: 844 }); await tick(page, 400);
  const k375 = await page.evaluate(() => new Set([...document.querySelector('.tc-key').children].map(x => Math.round(x.getBoundingClientRect().top))).size);
  ok(k375 === 1, 'planner: the key stays on one line on a 375px phone', k375);
  await page.setViewportSize({ width: 390, height: 844 }); await tick(page, 300);
  /* Every shape of what's left: one card, labels only when both kinds are there, no empty card. */
  const shapes = await page.evaluate(() => { const real = TCPL.ledger, L0 = real(), out = {};
    const run = (k, f) => { TCPL.ledger = () => Object.assign({}, L0, f(L0)); try { const h = document.createElement('div'); h.innerHTML = plannerView();
      const c = [...h.querySelectorAll('.tc-sec')].find(x => /^Still need/.test(x.querySelector('.tc-sech')?.textContent.trim() || ''));
      out[k] = c ? { n: +c.querySelector('.tc-sech').textContent.replace(/\D+/g, ''), rows: c.querySelectorAll('.li').length, heads: [...c.querySelectorAll('.tc-needh span:first-child')].map(x => x.textContent), note: /Prerequisites didn’t load/.test(c.textContent) } : null; } finally { TCPL.ledger = real; } };
    const el = { title: 'Free Elective', type: 'elective', id: 'zz', ti: 0, area: null };
    run('geOnly', L => ({ need: [] })); run('classesOnly', L => ({ needU: [] })); run('none', L => ({ need: [], needU: [] }));
    run('mixed', L => ({ needU: L.needU.concat([el]) })); run('elOnly', L => ({ needU: [el] }));
    const pq = UI.pl.prereqs; UI.pl.prereqs = false; run('pqClasses', L => ({})); run('pqGeOnly', L => ({ need: [] })); UI.pl.prereqs = pq;
    return out; });
  const S5 = shapes;
  ok(S5.geOnly && S5.geOnly.heads.length === 0 && S5.geOnly.rows === S5.geOnly.n && S5.classesOnly && S5.classesOnly.heads.length === 0 && S5.classesOnly.rows === S5.classesOnly.n && S5.none === null,
    'planner: only GEs or only classes left → one card, no group labels; nothing left → no card', S5);
  ok(S5.mixed && S5.mixed.heads.join('|') === 'Classes|GE and electives' && S5.mixed.rows === S5.mixed.n && S5.elOnly && S5.elOnly.heads.join('|') === 'Classes|Electives',
    'planner: GEs and electives together read “GE and electives”; electives alone read “Electives”', S5);
  ok(S5.pqClasses && S5.pqClasses.note && S5.pqGeOnly && !S5.pqGeOnly.note, 'planner: “Prerequisites didn’t load” sits with the classes, never on a GE-only card', S5);
  ok(/STAT 1210[\s\S]{0,160}Needs MATH 1000 first/.test(t2), 'planner: prerequisites from course_prereqs say what is missing');
  ok(/PHIL 3331/.test(t) && /Spring 2026/i.test(t) && /ENGL 1134\s*AP \/ IB credit/.test(t), 'planner: past classes and waivers listed, with the desktop’s reason labels', t.slice(t.indexOf('Past classes'), t.indexOf('Past classes') + 200));
  ok(/Pick your concentration/.test(t) && /Financial Management/.test(t), 'planner: concentration choices from the catalog');
  await click(page, '[data-a="schedTab"][data-x="planner"]'); await tick(page, 400);
  await click(page, '[data-a="plGe"][data-x="1C"]'); await tick(page);
  const g = await page.locator('#sheet').innerText();
  ok(/Oral Communication \(1C\)/.test(g) && /COMS 1101/.test(g) && /1 of \d+ classes in this area are offered Fall 2026/.test(g), 'planner: a GE area lists this term’s real classes for it', g.slice(0, 200));
  await click(page, '[data-a="closeSheet"]');
  await click(page, '[data-a="schedTab"][data-x="past"]'); await tick(page, 400);
  await click(page, '[data-a="sheet"][data-x="logClass"]');
  await page.locator('#lc-code').fill('bus 2214'); await page.locator('#lc-term').selectOption('Fall'); await page.locator('#lc-year').selectOption('2025');
  await click(page, 'form[data-submit="logClass"] .btn'); await tick(page, 600);
  const w = log.writes.filter(x => x.table === 'class_history');
  ok(w.length === 1 && w[0].m === 'POST' && w[0].body.code === 'BUS 2214' && w[0].body.term === 'Fall' && w[0].body.year === 2025 && w[0].body.user_id === FX.ME.id && !('grade' in w[0].body), 'planner: logging a class upserts the desktop’s class_history row (no grade)', w);
  t = await text(page);
  ok(/3 of 33\s*requirements filled/.test(t), 'planner: the ledger moves when a class is logged', (t.match(/\d+ of 33/) || [''])[0]);
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
/* Rate form (Tate, 2026-10-03): no “What did they do well?”, no “In person + Online = hybrid” line. */
tests.rateNoTags = async () => {
  const { page, close, log } = await openApp({});
  await click(page, '[data-a="tab"][data-x="rate"]');
  await click(page, '.li:has-text("Ada Examplewood")');
  await click(page, '[data-a="draft"][data-x="stars"][data-y="5"]');
  await click(page, '[data-a="draftMore"]');
  const t = await page.locator('.rf').innerText();
  ok(await page.locator('.rf .tc-tags, [data-a="draftTag"]').count() === 0 && !/What did they do well|Pick any/.test(t), 'rate: no “What did they do well?” chips', t.slice(0, 400));
  ok(!/hybrid/i.test(t) && await page.locator('[data-a="fmtTog"]').count() === 3, 'rate: Format keeps its three chips, without the “= hybrid” line');
  await click(page, '[data-a="postRating"]'); await tick(page, 800);
  const r = (log.writes.find(w => w.table === 'reviews') || {}).body;
  ok(r && Array.isArray(r.tags) && r.tags.length === 0, 'rate: a new review posts no tags', r && r.tags);
  await close();
};

/* Favorite teacher (Tate, 2026-10-03): “students only get 3 of these”. The server is stood in for by a
   hook that keeps the student's list, so the order and arguments of the calls can be checked. */
function favServer({ mine = [], counts = {}, missing = false, refuse = null, reviewFails = false } = {}) {
  const st = { mine: mine.slice(), calls: [] };
  st.hook = (url, m, body) => {
    if (reviewFails && url.pathname === '/rest/v1/reviews' && m === 'POST') return { status: 400, body: JSON.stringify({ code: 'P0001', message: 'refused by the fixture' }) };
    const fn = url.pathname.startsWith('/rest/v1/rpc/') ? url.pathname.slice(13) : '';
    if (!/^(my_favorite_teachers|favorite_teacher_counts|set_favorite_teacher)$/.test(fn)) return null;
    if (missing) return { status: 404, body: JSON.stringify({ code: 'PGRST202', message: 'Could not find the function public.' + fn + ' without parameters in the schema cache' }) };
    if (fn === 'my_favorite_teachers') return { status: 200, body: JSON.stringify(st.mine) };
    if (fn === 'favorite_teacher_counts') return { status: 200, body: JSON.stringify(Object.entries(counts).map(([professor_key, n]) => ({ professor_key, n }))) };
    st.calls.push(body);
    if (refuse) return { status: 400, body: JSON.stringify({ code: 'P0001', message: refuse }) };
    st.mine = body.p_on ? [...new Set(st.mine.concat(body.p_key))] : st.mine.filter(k => k !== body.p_key);
    return { status: 200, body: JSON.stringify(st.mine.length) };
  };
  return st;
}

tests.favTeacher = async () => {
  const srv = favServer({ mine: ['one|bus', 'two|bus'], counts: { 'ada examplewood|bus': 4 } });
  const { page, close, log } = await openApp({ hook: srv.hook });
  await click(page, '[data-a="tab"][data-x="explore"]'); await click(page, '[data-a="exMode"][data-x="profs"]');
  await click(page, '#exlist .pcard:has-text("Ada Examplewood")'); await tick(page, 400);
  ok(/Favorite teacher of 4 students/.test(await page.locator('#scroll .hero').innerText()), 'fav: a professor’s page says how many students picked them');
  await click(page, '[data-a="back"]');
  await click(page, '[data-a="tab"][data-x="rate"]');
  await click(page, '.li:has-text("Ada Examplewood")');
  /* 2026-10-04: it lives in "+ Add detail", the row right above Review */
  const closed = await page.locator('.rf .favbtn').count();
  await click(page, '[data-a="draftMore"]');
  const place = await page.evaluate(() => { const fr = document.querySelector('.rf .favbtn').closest('.frow2'), nx = fr.nextElementSibling, pv = fr.previousElementSibling;
    return { next: nx && nx.querySelector('.flabel') && nx.querySelector('.flabel').textContent.trim(), ta: !!(nx && nx.querySelector('#revta')), prev: pv && pv.querySelector('.flabel') && pv.querySelector('.flabel').textContent.trim(), afterAgain: /Take again/.test((fr.previousElementSibling || {}).textContent || '') }; });
  ok(closed === 0 && place.next === 'Review' && place.ta && place.prev === 'Format' && !place.afterAgain, 'fav: Favorite teacher sits in Add detail, right above the Review box (not under Take again?)', { closed, place });
  const row = async () => page.evaluate(() => { const b = document.querySelector('.rf .favbtn'), h = document.querySelector('.rf .rf-fh'); return b && { on: b.getAttribute('aria-pressed'), dis: b.disabled, t: b.innerText.trim(), hint: h.innerText.trim(), h: Math.round(b.getBoundingClientRect().height) }; });
  let a = await row();
  ok(a && a.on === 'false' && !a.dis && a.t === 'Pick' && a.hint === '1 of 3 left' && a.h >= 44, 'fav: the form offers it, with how many are left', a);
  await click(page, '.rf .favbtn'); a = await row();
  ok(a.on === 'true' && a.t === 'Favorite' && a.hint === '0 of 3 left', 'fav: tapping picks it', a);
  await click(page, '[data-a="draftMore"]');
  const hid = await page.evaluate(() => ({ btn: document.querySelectorAll('.rf .favbtn').length, flag: (document.querySelector('.rf .favhid') || {}).textContent || '', opt: [...document.querySelectorAll('.rf .hint')].some(h => h.textContent.trim() === 'Optional') }));
  ok(hid.btn === 0 && hid.flag.trim() === 'Favorite' && !hid.opt, 'fav: hiding detail with a favorite picked shows “♥ Favorite” on the Add detail row, never a hidden pick', hid);
  await click(page, '[data-a="draft"][data-x="stars"][data-y="5"]');
  await click(page, '[data-a="postRating"]'); await tick(page, 900);
  ok(srv.calls.length === 1 && srv.calls[0].p_key === 'ada examplewood|bus' && srv.calls[0].p_on === true, 'fav: saved for that professor after posting', srv.calls);
  ok(log.writes.some(w => w.table === 'reviews' && w.m === 'POST'), 'fav: the review itself posted');
  ok(/FAVORITE\s*♥ Yes/.test(await page.locator('.rf').innerText()), 'fav: the thanks screen says so');
  await close();

  const full = favServer({ mine: ['one|bus', 'two|bus', 'three|bus'] });
  const o2 = await openApp({ hook: full.hook });
  await click(o2.page, '[data-a="tab"][data-x="rate"]'); await click(o2.page, '.li:has-text("Ada Examplewood")'); await click(o2.page, '[data-a="draftMore"]');
  const b2 = await o2.page.evaluate(() => { const b = document.querySelector('.rf .favbtn'); return { dis: b.disabled, hint: document.querySelector('.rf .rf-fh').innerText.trim() }; });
  await o2.page.evaluate(() => A.favTog());
  await click(o2.page, '[data-a="draft"][data-x="stars"][data-y="4"]'); await click(o2.page, '[data-a="postRating"]'); await tick(o2.page, 800);
  ok(b2.dis && b2.hint === 'All 3 used' && full.calls.length === 0, 'fav: with 3 used elsewhere the button is off and nothing is sent', { b2, calls: full.calls });
  await o2.close();

  const no = favServer({ missing: true });
  const o3 = await openApp({ hook: no.hook });
  await click(o3.page, '[data-a="tab"][data-x="rate"]'); await click(o3.page, '.li:has-text("Ada Examplewood")'); await click(o3.page, '[data-a="draftMore"]');
  ok(await o3.page.locator('.favbtn').count() === 0 && o3.log.errors.length === 0, 'fav: before the SQL runs, no button and no errors');
  await o3.close();

  const ref = favServer({ refuse: 'You’ve used all 3 favorite teachers. Take one back first.' });
  const o4 = await openApp({ hook: ref.hook });
  await click(o4.page, '[data-a="tab"][data-x="rate"]'); await click(o4.page, '.li:has-text("Ada Examplewood")'); await click(o4.page, '[data-a="draftMore"]');
  await click(o4.page, '.rf .favbtn'); await click(o4.page, '[data-a="draft"][data-x="stars"][data-y="4"]');
  await click(o4.page, '[data-a="postRating"]'); await tick(o4.page, 900);
  const t4 = await o4.page.locator('#toast').innerText();
  ok(/Rating posted\. You’ve used all 3/.test(t4) && /Thanks for your review/.test(await o4.page.locator('.rf').innerText()) && !/FAVORITE/.test(await o4.page.locator('.rf').innerText()), 'fav: a refusal says the server’s sentence, and the rating still posts', t4);
  await o4.close();

  const bad = favServer({ reviewFails: true });
  const o5 = await openApp({ hook: bad.hook });
  await click(o5.page, '[data-a="tab"][data-x="rate"]'); await click(o5.page, '.li:has-text("Ada Examplewood")'); await click(o5.page, '[data-a="draftMore"]');
  await click(o5.page, '.rf .favbtn'); await click(o5.page, '[data-a="draft"][data-x="stars"][data-y="4"]');
  await click(o5.page, '[data-a="postRating"]'); await tick(o5.page, 800);
  ok(bad.calls.length === 0 && await o5.page.locator('.rf .tc-err').count() === 1, 'fav: a refused review saves no favorite', bad.calls);
  await click(o5.page, '[data-a="back"]'); await tick(o5.page, 200);
  await click(o5.page, '.li:has-text("Ada Examplewood")');
  ok(await o5.page.locator('.rf .favbtn').getAttribute('aria-pressed') === 'true', 'fav: the heart is kept in the saved draft');
  const lab = await o5.page.locator('.rf .favbtn').getAttribute('aria-label');
  await o5.page.focus('.rf .favbtn'); await o5.page.keyboard.press('Enter'); await tick(o5.page, 150);
  const fo = await o5.page.evaluate(() => ({ f: document.activeElement && document.activeElement.getAttribute('aria-label'), live: document.querySelector('.rf .rf-fh').getAttribute('aria-live'), on: document.querySelector('.rf .favbtn').getAttribute('aria-pressed') }));
  ok(lab === 'Favorite teacher' && fo.f === 'Favorite teacher' && fo.on === 'false' && fo.live === 'polite', 'fav: one name for the button, focus stays on it, the count is announced', { lab, fo });
  await o5.close();
};

tests.favTeacherEdit = async () => {
  const mine = Object.assign({}, FX.MY_REVIEW, { tags: ['Explains concepts clearly'] });
  const srv = favServer({ mine: [mine.professor_key] });
  const { page, close, log } = await openApp({ hook: srv.hook, tables: Object.assign({}, FX.TABLES, { reviews: [mine] }), rpc: Object.assign({}, FX.RPC, { my_reviews: [mine] }) });
  await openRatings(page);
  ok(/Favorite/.test(await page.locator('.tc-rev').first().innerText()) && await page.locator('.tc-rev .favchip').count() === 1, 'fav: your review on Me carries the ♥ Favorite chip');
  await click(page, '[data-a="editReview"]');
  ok(await page.locator('.rf .favbtn').getAttribute('aria-pressed') === 'true', 'fav: editing shows it as picked');
  await click(page, '.rf .favbtn');
  await click(page, '[data-a="postRating"]'); await tick(page, 800);
  ok(srv.calls.length === 1 && srv.calls[0].p_on === false && srv.calls[0].p_key === mine.professor_key, 'fav: taking it back in an edit frees the slot', srv.calls);
  const w = log.writes.filter(x => x.table === 'reviews');
  ok(w.length === 1 && JSON.stringify(w[0].body.tags) === JSON.stringify(['Explains concepts clearly']), 'no tags: editing an older review keeps the tags it had', w[0] && w[0].body);
  await close();

  /* An edit that changes nothing about the favorite sends nothing; one that opens before the
     favorites load picks them up; picking in an edit that the server refuses says so. */
  const s2 = favServer({ mine: [mine.professor_key] });
  const o2 = await openApp({ hook: s2.hook, tables: Object.assign({}, FX.TABLES, { reviews: [mine] }), rpc: Object.assign({}, FX.RPC, { my_reviews: [mine] }) });
  await openRatings(o2.page);
  await o2.page.evaluate(() => { TC.myFavs = new Set(); });
  await click(o2.page, '[data-a="editReview"]');
  const before = await o2.page.locator('.rf .favbtn').getAttribute('aria-pressed');
  await o2.page.evaluate(() => TC.loadFavs().then(() => render(true))); await tick(o2.page, 300);
  const after = await o2.page.locator('.rf .favbtn').getAttribute('aria-pressed');
  ok(before === 'false' && after === 'true', 'fav: an edit opened before the favorites loaded shows the saved heart once they do', { before, after });
  await click(o2.page, '[data-a="postRating"]'); await tick(o2.page, 800);
  ok(s2.calls.length === 0, 'fav: an edit that leaves the heart alone sends nothing', s2.calls);
  await o2.close();

  const bare = Object.assign({}, FX.MY_REVIEW, { format: null, note: null });
  const s4 = favServer({ mine: [bare.professor_key] });
  const o4 = await openApp({ hook: s4.hook, tables: Object.assign({}, FX.TABLES, { reviews: [bare] }), rpc: Object.assign({}, FX.RPC, { my_reviews: [bare] }) });
  await openRatings(o4.page);
  await click(o4.page, '[data-a="editReview"]');
  ok(await o4.page.locator('.rf .favbtn').getAttribute('aria-pressed') === 'true' && await o4.page.locator('.rf #revta').count() === 1, 'fav: editing a favorite with no format or note opens Add detail, so the picked heart shows above Review');
  await o4.close();
  const s5 = favServer({ mine: [bare.professor_key] });
  const o5 = await openApp({ hook: s5.hook, tables: Object.assign({}, FX.TABLES, { reviews: [bare] }), rpc: Object.assign({}, FX.RPC, { my_reviews: [bare] }) });
  await openRatings(o5.page);
  await o5.page.evaluate(() => { TC.myFavs = new Set(); });
  await click(o5.page, '[data-a="editReview"]');
  const shut = await o5.page.locator('.rf .favbtn').count();
  await o5.page.evaluate(() => TC.loadFavs().then(() => render(true))); await tick(o5.page, 300);
  ok(shut === 0 && await o5.page.locator('.rf .favbtn').getAttribute('aria-pressed') === 'true', 'fav: favorites that load after the edit opened open Add detail to show the heart', shut);
  await o5.close();

  const s3 = favServer({ mine: [], refuse: 'You’ve used all 3 favorite teachers. Take one back first.' });
  const o3 = await openApp({ hook: s3.hook, tables: Object.assign({}, FX.TABLES, { reviews: [mine] }), rpc: Object.assign({}, FX.RPC, { my_reviews: [mine] }) });
  await openRatings(o3.page);
  await click(o3.page, '[data-a="editReview"]'); await click(o3.page, '.rf .favbtn');
  await click(o3.page, '[data-a="postRating"]'); await tick(o3.page, 800);
  ok(s3.calls.length === 1 && s3.calls[0].p_on === true && /Review updated\. You’ve used all 3/.test(await o3.page.locator('#toast').innerText()), 'fav: picking in an edit saves it, and a refusal says so', s3.calls);
  await o3.close();
};

/* Planner (Tate, 2026-10-02): every class shows its NAME once, no per-row units, a one-tap “I took it”
   on the flowchart, and choice slots (“… or …”) checked against their options. */
tests.plannerQuickTick = async () => {
  const T = Object.assign({}, FX.TABLES, { course_catalog: FX.TABLES.course_catalog.concat([{ course_code: 'BUS 4468', title: 'Blockchain in Finance (catalog title)', prereqs: '', description: '' }]) });
  const { page, close, log } = await openApp({ tables: T });
  await click(page, '[data-a="tab"][data-x="schedule"]'); await click(page, '[data-a="schedTab"][data-x="past"]'); await tick(page, 2500);
  const nm = await page.evaluate(() => ({ a: courseName('BUS 3411'), b: courseName('BUS 3441'), c: courseName('BUS 4468'), d: courseName('ZZZ 9999'), e: courseName('BUS 1100') }));
  ok(nm.a === 'Finance Practicum' && nm.b === 'Financial Modeling and Analytics in Python or R' && nm.c === 'Blockchain in Finance (catalog title)' && nm.d === '' && nm.e === 'Career Readiness I', 'names: catalog title first, then the flowchart, then the desktop’s 2026–28 names — never a code, nothing invented', nm);
  await page.evaluate(() => { TC.profile.concentration = 'Financial Management'; for (let y = 1; y <= 5; y++) UI.plYears[y] = true; render(true); }); await tick(page, 800);
  const c3411 = await page.locator('.tc-cell:has(.tc-ccode:text("BUS 3411")) .tc-ctitle').first().innerText();
  /* Still need · all lives folded at the foot of the Planner (2026-10-06) */
  const needText = async () => { await page.evaluate(() => { UI.plAllOpen = true; S.schedTab = 'planner'; render(true); }); await tick(page, 300); const x = await text(page); await page.evaluate(() => { S.schedTab = 'past'; render(true); }); await tick(page, 300); return x; };
  const need = await needText();
  ok(/^BUS 3411\s*Finance Practicum$/.test(c3411.trim()) && /Still need[\s\S]*BUS 3411\s*Finance Practicum/.test(need), 'names: a slot that only repeats its code (BUS 3411) shows the class’s name, in the flowchart and in Still need', c3411);
  const cells = await page.locator('.tc-cell').evaluateAll(els => els.map(e => ({ t: e.querySelector('.tc-ctitle') ? e.querySelector('.tc-ctitle').innerText.trim() : '', code: e.querySelector('.tc-ccode') ? e.querySelector('.tc-ccode').innerText.trim() : '', all: e.innerText })));
  const dup = cells.filter(c => c.code && c.t.replace(c.code, '').trim().replace(/\s+/g, ' ') === c.code.replace(/\s+/g, ' '));
  ok(cells.length > 20 && !dup.length, 'flowchart: no class names its number twice', dup.slice(0, 3));
  ok(!cells.some(c => /\b\d+u\s*$/.test(c.all.trim())), 'flowchart: no units on the rows', cells.filter(c => /\d+u\s*$/.test(c.all.trim())).slice(0, 2));
  ok(/Still need[\s\S]*BUS 1100\s*Career Readiness I/.test(need) && !/Still need[\s\S]*BUS (\d{4})\s*BUS \1\b/.test(need), 'still need: the blue code, then the class’s name — never the code twice');
  ok(/Pick 1\s*Calculus for Data Science I or Business Calculus[\s\S]{0,80}MATH 1264/.test(need), 'still need: a choice slot reads as one pick, with its options', (need.match(/Pick 1[\s\S]{0,120}/) || [''])[0]);
  const before = (await text(page)).match(/(\d+) of \d+\s*requirements/)[1];
  // one tap: on your record, no term, nothing else to do
  await click(page, '.tc-cell:has(.tc-ccode:text("BUS 1100")) .tc-tick'); await tick(page, 600);
  let w = log.writes.filter(x => x.table === 'class_history');
  ok(w.length === 1 && w[0].m === 'POST' && w[0].body.code === 'BUS 1100' && w[0].body.term === null && w[0].body.year === null && w[0].body.user_id === FX.ME.id && await page.locator('#sheet .tc-form').count() === 0, 'one tap: the class goes on your record with no term, and nothing opens', w);
  let after = (await text(page)).match(/(\d+) of \d+\s*requirements/)[1];
  const c1 = page.locator('.tc-cell:has(.tc-ccode:text("BUS 1100"))');
  ok(+after === +before + 1 && /✓/.test(await c1.locator('.tc-dot').innerText()) && /^Undo/.test(await c1.locator('.tc-tick').getAttribute('aria-label')), 'one tap: the slot is ✓ and the count moves', { before, after });
  await click(page, '.tc-cell:has(.tc-ccode:text("BUS 1100")) .tc-tick'); await tick(page, 600);
  w = log.writes.filter(x => x.table === 'class_history' && x.m === 'DELETE');
  ok(w.length === 1 && /code=eq\.BUS(\+|%20)1100/.test(w[0].query) && /term=is\.null/.test(w[0].query) && /year=is\.null/.test(w[0].query) && (await text(page)).match(/(\d+) of \d+\s*requirements/)[1] === before, 'one tap: ✓ again undoes it — only the term-less record', w);
  ok(await page.locator('.tc-cell:has(.tc-ccode:text("BUS 1100")) .tc-cbody[data-a="plLogSlot"]').count() === 1, 'one tap: the row itself still opens Log a class for the term and professor');
  // a choice slot: one question, which one
  const ch = page.locator('.tc-cell:has-text("Calculus for Data Science I or Business Calculus")').first();
  ok(await ch.locator('.tc-tick').count() === 1 && !/\?/.test(await ch.locator('.tc-dot').innerText()), 'choice: “… or …” is no longer “can’t check” — it has the check button');
  await ch.locator('.tc-tick').click(); await tick(page);
  const opts = await page.locator('.tc-pick .tc-pickb').allInnerTexts();
  ok(opts.length === 2 && /MATH 1264/.test(opts[0]) && /MATH 1267/.test(opts[1]), 'choice: the tap asks only which one', opts);
  const fBefore = +(await text(page)).match(/(\d+) of \d+\s*requirements/)[1];
  await click(page, '.tc-pick [data-a="plTickCode"][data-x="MATH 1267"]'); await tick(page, 600);
  const fAfter = +(await text(page)).match(/(\d+) of \d+\s*requirements/)[1];
  w = log.writes.filter(x => x.table === 'class_history' && x.m === 'POST');
  const chDone = await page.locator('.tc-cell.done:has(.tc-ccode:text("MATH 1267"))').count();
  ok(w.length === 2 && w[1].body.code === 'MATH 1267' && w[1].body.term === null && chDone === 1 && fAfter === fBefore + 1, 'choice: the pick goes on your record and fills exactly one slot', { w: w.map(x => x.body && x.body.code), fBefore, fAfter });
  ok((await page.locator('.tc-cell.done:has(.tc-ccode:text("MATH 1267")) .tc-ctitle').innerText()).trim() === 'MATH 1267  Business Calculus'.replace('  ', ' ') || /^MATH 1267\s*Business Calculus$/.test((await page.locator('.tc-cell.done:has(.tc-ccode:text("MATH 1267")) .tc-ctitle').innerText()).trim()), 'choice: the filled slot names the class taken, not the “… or …” line');
  const posts = log.writes.filter(x => x.table === 'class_history' && x.m === 'POST').length;
  await page.evaluate(() => quickLog('PHIL 3331', 'rep')); await tick(page, 400);
  ok(log.writes.filter(x => x.table === 'class_history' && x.m === 'POST').length === posts && await page.locator('#lc-code').inputValue() === 'PHIL 3331' && /already on your record once/.test(await page.locator('#sheet').innerText()), 'one tap: a class already on the record (a repeatable one) asks for the term — a term-less row never lands on a dated one');
  await click(page, '#sheet .xbtn[data-a="closeSheet"]');
  ok(log.errors.length === 0, 'planner tick: no page errors', log.errors);
  await close();
  /* If the database ever refuses a record with no term, the tap opens Log a class instead of failing. */
  const nn = await openApp({ hook: (url, m) => url.pathname.endsWith('/class_history') && m === 'POST' ? { status: 400, body: JSON.stringify({ code: '23502', message: 'null value in column "term" violates not-null constraint' }) } : null });
  await click(nn.page, '[data-a="tab"][data-x="schedule"]'); await click(nn.page, '[data-a="schedTab"][data-x="past"]'); await tick(nn.page, 2500);
  await click(nn.page, '.tc-cell:has(.tc-ccode:text("BUS 1100")) .tc-tick'); await tick(nn.page, 600);
  ok(await nn.page.locator('#lc-code').inputValue() === 'BUS 1100' && /Add the term you took it/.test(await nn.page.locator('#sheet').innerText()), 'one tap: a refused term-less record opens Log a class with the class filled in');
  await nn.close();
};

tests.plannerGrid = async () => {
  const { page, close, log } = await openApp({});
  await click(page, '[data-a="tab"][data-x="schedule"]'); await click(page, '[data-a="schedTab"][data-x="past"]'); await tick(page, 2500);
  const t = await text(page);
  ok(/Your flowchart[\s\S]*Year 1[\s\S]*of \d+ done/.test(t), 'grid: the flowchart by year');
  const y1 = await page.locator('.tc-year').first().innerText();
  ok(/Fall/i.test(y1) && /BUS 1100[\s\S]*Career Readiness I/.test(y1) && /✓\s*GE · Area 1A/.test(y1), 'grid: Year 1 is open, with the waiver filling GE 1A (✓) — the same state the ledger counts', y1.slice(0, 400));
  const heads = await page.locator('.tc-yearh').allInnerTexts();
  const judged = heads.reduce((a, h) => a + (+((h.match(/of (\d+) done/) || [])[1] || 0)), 0);
  ok(judged === 33 && heads.some(h => /can’t check/.test(h)), 'grid: the years add up to the ledger’s 33, with can’t-check slots said separately', heads);
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
  await click(page, '[data-a="tab"][data-x="schedule"]'); await click(page, '[data-a="schedTab"][data-x="past"]'); await tick(page, 2500);
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
  await click(page, '[data-a="tab"][data-x="schedule"]'); await click(page, '[data-a="schedTab"][data-x="past"]'); await tick(page, 2500);
  await page.locator('input[data-in="dprfile"]').setInputFiles('files/not-a-dpr.pdf');
  for (let i = 0; i < 20 && !/isn’t a Degree Progress Report/.test(await page.locator('#sheet').innerText()); i++) await tick(page, 500);
  ok(/isn’t a Degree Progress Report/.test(await page.locator('#sheet').innerText()), 'dpr: another PDF is refused with what to do instead');
  await close();
};

/* ============ Schedule split: Past classes and TermChamp's picks (Tate, 2026-10-06) ============
   "people first upload the DPR", then the Planner shows the best classes to take, with the best professors and friends. */
tests.plannerPicks = async () => {
  const { page, close, log } = await openApp({});
  await page.waitForFunction(() => TC.ready && TC.seatsLoaded, null, { timeout: 8000 });
  await click(page, '[data-a="tab"][data-x="schedule"]');
  const tabs = await page.locator('.stabs [data-a="schedTab"]').evaluateAll(es => es.map(e => e.dataset.x + ':' + e.innerText.trim()));
  ok(tabs.join('|') === 'mine:My Classes|plans:Plans|past:Past classes|planner:Planner', 'split: Schedule’s tabs are My Classes · Plans · Past classes · Planner', tabs);
  for (const w of [320, 390]) { await page.setViewportSize({ width: w, height: 844 }); await tick(page, 300);
    const f = await page.evaluate(() => { const s = document.querySelector('.stabs'); return { sw: s.scrollWidth, cw: s.clientWidth, tops: new Set([...s.children].map(c => Math.round(c.getBoundingClientRect().top))).size }; });
    ok(f.sw <= f.cw && f.tops === 1, `split: the four tabs fit on one line at ${w}px`, f); }
  /* Past classes: the ledger, then the flowchart in term bubbles, then the record */
  await click(page, '[data-a="schedTab"][data-x="past"]'); await tick(page, 2500);
  const past = await page.evaluate(() => { const sc = document.getElementById('scroll'), at = sel => { const e = sc.querySelector(sel); return e ? e.getBoundingClientRect().top + sc.scrollTop : -1; };
    const h = [...sc.querySelectorAll('.tc-sech, h2, .tc-ltitle')].map(x => x.innerText.trim());
    return { ledger: at('.tc-lrow'), grid: at('.tc-year'), hist: [...sc.querySelectorAll('.card')].findIndex(c => /Classes you’ve taken/.test(c.innerText)), histTop: (() => { const c = [...sc.querySelectorAll('.card')].find(c => /Classes you’ve taken/.test(c.innerText)); return c ? c.getBoundingClientRect().top + sc.scrollTop : -1; })(),
      picks: !!sc.querySelector('.pk-hero'), dpr: !!sc.querySelector('.tc-dpr'), oldHead: /(^|\n)Past classes\n\d/.test(sc.innerText.replace(/^[\s\S]*?Planner\n/, '')),
      terms: sc.querySelectorAll('.tc-term').length, termCells: sc.querySelectorAll('.tc-term .tc-cell').length, cells: sc.querySelectorAll('.tc-cell').length,
      termBg: sc.querySelector('.tc-term') && getComputedStyle(sc.querySelector('.tc-term')).backgroundColor, yearBg: sc.querySelector('.tc-yearh') && getComputedStyle(sc.querySelector('.tc-yearh')).backgroundColor,
      termHead: sc.querySelector('.tc-termh') && sc.querySelector('.tc-termh').innerText.replace(/\s+/g, ' ').trim() }; });
  ok(past.ledger > 0 && past.grid > past.ledger && past.histTop > past.grid && !past.picks && !past.dpr, 'past: the ledger first, then the flowchart, then the classes you’ve taken — no picks, and no DPR card when there is a record', past);
  ok(past.terms >= 2 && past.termCells === past.cells && /rgba\(37, 99, 235, 0\.06\)/.test(past.termBg) && /rgba\(37, 99, 235, 0\.1\)/.test(past.yearBg), 'past: each term of an open year is its own translucent blue bubble, every class inside one', past);
  ok(/^FALL \d+ of \d+ done · \d+ units$/i.test(past.termHead), 'past: a term bubble says how much of it is done and its units', past.termHead);
  const doneInk = await page.evaluate(() => { const d = document.querySelector('#scroll .tc-cell.done .tc-dot'); return d && getComputedStyle(d).color; });
  ok(doneInk === 'rgb(15, 118, 110)', 'past: a done ✓ is teal in light mode', doneInk);
  /* Planner: TermChamp's picks */
  await click(page, '[data-a="schedTab"][data-x="planner"]'); await tick(page, 800);
  const pl = await page.evaluate(() => { const sc = document.getElementById('scroll'), L = TCPL.ledger(), R = planRecs(L), done = new Set(TCPL.completed().map(c => TCPL.canon(c) || c)), mine = new Set([...myCodes()].map(c => TCPL.canon(c) || c));
    const shown = [...sc.querySelectorAll('.pk-hero .pk')].map(p => p.querySelector('.pk-main').dataset.x);
    return { shown, picks: R.picks.map(c => ({ code: c.code, key: c.key, score: c.score, st: c.prereq, n: !!c.n })), ledgerHere: !!sc.querySelector('.tc-lrow'), gridHere: !!sc.querySelector('.tc-year'),
      bad: R.picks.filter(c => done.has(TCPL.canon(c.code) || c.code) || mine.has(TCPL.canon(c.code) || c.code) || !secsOf(c.code).length).map(c => c.code),
      sorted: R.picks.every((c, i) => !i || R.picks[i - 1].score >= c.score), keys: new Set(R.picks.map(c => c.key)).size,
      eyebrow: (sc.querySelector('.pk-ey') || {}).innerText, rows: [...sc.querySelectorAll('.pk-sec .recs-h')].map(h => h.innerText.trim()), order: (() => { const a = sc.querySelector('.pk-hero'), b = sc.querySelector('.pk-sec'), c = sc.querySelector('details.pk-all'); return !!(a && b && c && (a.compareDocumentPosition(b) & 4) && (b.compareDocumentPosition(c) & 4)); })() }; });
  ok(pl.shown.length >= 1 && pl.shown.length <= 4 && pl.shown.join() === pl.picks.map(c => c.code).join(), 'picks: up to four classes, shown in the order they rank', pl);
  ok(!pl.bad.length && pl.sorted && pl.keys === pl.picks.length, 'picks: never a class you’ve taken, are taking, or that isn’t offered; one per requirement; best score first', pl);
  ok(!pl.ledgerHere && !pl.gridHere && pl.eyebrow === 'FALL 2026 CLASSES', 'picks: the Planner has no ledger or flowchart (they’re in Past classes); the picks are for Fall 2026', pl);
  ok(pl.order && pl.rows.includes('Best professors teaching what you need'), 'picks: the rows come after the picks, then the full Still need list', pl.rows);
  /* the rules a pick has to follow */
  const rk = await page.evaluate(() => { const L = TCPL.ledger(), all = planRecs(L).all;
    const was = TC.profile.class_standing;
    TC.profile.class_standing = 'Senior'; const sen = planRecs(L); TC.profile.class_standing = was;
    const top = sen.picks[0]; const pre = all.every(c => !c.prereq || ['met', 'concurrent', 'none'].includes(c.prereq));
    return { pre, top: top && { code: top.code, behind: top.behind, yr: top.yr, tag: pickReason(top).t }, rest: sen.picks.slice(1).map(c => c.behind), allBehind: sen.all.filter(c => c.behind).map(c => c.code) }; });
  ok(rk.top && rk.top.behind > 0 && rk.top.tag === 'Top priority', 'picks: for a senior, a class their flowchart put in an earlier year is #1, tagged “Top priority”', rk);
  /* the + opens Add to your week for that class's best section */
  const first = pl.shown[0];
  await click(page, '.pk-hero .pk-add >> nth=0'); await tick(page, 300);
  const at = await page.evaluate(() => UI.sheet && UI.sheet.type === 'addTo' && SEC[UI.sheet.id] && SEC[UI.sheet.id].code);
  ok(at === first, 'picks: + opens Add to your week for that class', { at, first });
  await click(page, '#sheet .xbtn[data-a="closeSheet"]'); await tick(page, 200);
  /* the Why sheet */
  await click(page, '.pk-hero .pk-main >> nth=0'); await tick(page, 300);
  const why = await page.evaluate(() => { const s = document.getElementById('sheet'); return { t: s.innerText, n: s.querySelectorAll('.pw').length, nums: [...s.querySelectorAll('.pw-n')].map(x => x.innerText.trim()).join(), add: !!s.querySelector('[data-a="addPlanSheet"]'), open: !!s.querySelector('[data-a="openClass"]') }; });
  ok(new RegExp(first.replace(' ', '\\s') + '[\\s\\S]*Why it’s #1 of your picks for Fall 2026').test(why.t) && why.n >= 3 && why.nums.startsWith('1,2,3') && why.add && why.open, 'why: tapping a pick says, numbered, why it’s #1 — with Add and Open class', why);
  ok(/\d+ sections? in Fall 2026\s*\d+ fits? your week/.test(why.t), 'why: it says how many sections there are and how many fit your week', why.t.slice(0, 500));
  await click(page, '#sheet .xbtn[data-a="closeSheet"]'); await tick(page, 200);
  /* rows: a friend in one of the classes, and a class that also fills a GE area */
  const inj = await page.evaluate(() => { const L = TCPL.ledger(), R = planRecs(L), c = R.picks[0], c2 = R.picks[1] || c, ge = L.needU.find(n => n.type === 'ge' && n.area);
    TCPL.geCourses.push({ code: c.code, name: 'fixture', area: 'Area ' + ge.area, areaKey: ge.area, units: 4, prof: '__tbd', workload: '' });
    const f = TC.friends[0]; PEOPLE[f].unplaced = (PEOPLE[f].unplaced || []).concat([c2.code]); render(true);
    return { fill: c.code, friend: c2.code, short: PEOPLE[f].short }; });
  await tick(page, 300);
  const rw = await page.evaluate(() => [...document.querySelectorAll('#scroll .pk-sec')].map(s => [s.querySelector('.recs-h').innerText.trim(), [...s.querySelectorAll('.rmini')].map(b => b.dataset.x)]));
  ok(rw.map(r => r[0]).join('|') === 'Your friends are taking|Best professors teaching what you need|Fill the most requirements', 'rows: friends, best professors, then classes that fill the most — each a row you scroll', rw);
  ok(rw[0] && rw[0][1].includes(inj.friend) && rw[2] && rw[2][1].includes(inj.fill), 'rows: the class a friend is in, and the class that also fills a GE area, are in their rows', { rw, inj });
  const sx = await page.evaluate(() => { const r = document.querySelector('#scroll .pk-sec .recs-row'); return r && getComputedStyle(r).overflowX; });
  ok(/auto|scroll/.test(sx), 'rows: they scroll sideways', sx);
  /* rows carry what they say */
  const rows = await page.evaluate(() => { const R = planRecs(TCPL.ledger()); return { fr: R.friends.every(c => c.fr.length > 0), fill: R.fill.every(c => c.reqN >= 2), pr: R.profs.every((p, i) => !i || R.profs[i - 1].r >= p.r), prN: R.profs.length }; });
  ok(rows.fr && rows.fill && rows.pr, 'rows: friends’ classes have friends in them, “fill the most” counts at least twice, professors best-rated first', rows);
  ok(log.errors.length === 0, 'picks: no page errors', log.errors);
  await close();

  /* Nothing on the record: the Degree Progress Report comes first, on both tabs */
  const T0 = Object.assign({}, FX.TABLES, { class_history: [], class_waivers: [] });
  const o = await openApp({ tables: T0 });
  await click(o.page, '[data-a="tab"][data-x="schedule"]'); await click(o.page, '[data-a="schedTab"][data-x="planner"]'); await tick(o.page, 2500);
  let d = await o.page.evaluate(() => { const sc = document.getElementById('scroll'); return { dpr: !!sc.querySelector('.tc-dpr'), t: sc.innerText, input: sc.querySelectorAll('.tc-dpr input[data-in="dprfile"]').length, log: !!sc.querySelector('.tc-dpr [data-a="sheet"][data-x="logClass"]'), picks: !!sc.querySelector('.pk-hero'), skip: !!sc.querySelector('[data-a="plShowPicks"]'), go: (() => { const b = sc.querySelector('.tc-dpr-go'); return b && Math.round(b.getBoundingClientRect().height); })() }; });
  ok(d.dpr && /Upload your Degree Progress Report/.test(d.t) && d.input === 1 && d.log && !d.picks && d.skip && d.go >= 44, 'dpr first: with nothing on your record the Planner asks for the DPR first (upload, or add classes one at a time)', d);
  await click(o.page, '[data-a="plShowPicks"]'); await tick(o.page, 400);
  d = await o.page.evaluate(() => { const sc = document.getElementById('scroll'); return { dpr: !!sc.querySelector('.tc-dpr'), nudge: !!sc.querySelector('.tc-dpr-row input[data-in="dprfile"]'), picks: !!sc.querySelector('.pk-hero'), key: localStorage.getItem('tc-pl-nodpr:' + TC.user.id) }; });
  ok(!d.dpr && d.nudge && d.picks && d.key === '1', 'dpr first: “show picks” shows them, keeps a small upload row, and is remembered for this account', d);
  await click(o.page, '[data-a="schedTab"][data-x="past"]'); await tick(o.page, 400);
  d = await o.page.evaluate(() => { const sc = document.getElementById('scroll'), a = sc.querySelector('.tc-dpr'), b = sc.querySelector('.tc-lrow'); return { first: !!(a && b && (a.compareDocumentPosition(b) & 4)), hist: /Classes you’ve taken/.test(sc.innerText) }; });
  ok(d.first && !d.hist, 'dpr first: Past classes opens on the DPR card, above the ledger (no empty record card)', d);
  await o.page.locator('.tc-dpr input[data-in="dprfile"]').setInputFiles('files/dpr-fixture.pdf');
  for (let i = 0; i < 20 && !(await o.page.locator('#sheet .tc-dprrow').count()); i++) await tick(o.page, 500);
  ok(/Past classes · \d/i.test(await o.page.locator('#sheet').innerText()), 'dpr first: the card’s upload reads the report');
  ok(o.log.errors.length === 0, 'dpr first: no page errors', o.log.errors);
  await o.close();
  /* a freshman has nothing to upload: straight to the picks */
  const T1 = Object.assign({}, T0, { profiles: FX.TABLES.profiles.map(p => p.id === FX.ME.id ? Object.assign({}, p, { class_standing: 'Freshman' }) : p) });
  const f = await openApp({ tables: T1 });
  await click(f.page, '[data-a="tab"][data-x="schedule"]'); await click(f.page, '[data-a="schedTab"][data-x="planner"]'); await tick(f.page, 2500);
  d = await f.page.evaluate(() => { const sc = document.getElementById('scroll'); return { dpr: !!sc.querySelector('.tc-dpr'), picks: sc.querySelectorAll('.pk-hero .pk').length, st: TC.profile.class_standing }; });
  ok(d.st === 'Freshman' && !d.dpr && d.picks > 0, 'dpr first: a freshman with no record goes straight to the picks', d);
  await f.close();
};

/* The ranking rules, each on a small made-up ledger over the fixture's real Fall 2026 classes.
   Offered and free: BUS 3346, BUS 3387, BUS 4401, BUS 4488, ECON 2303, STAT 2170. Taking now: BUS 3431. The student is a Junior. */
tests.plannerRank = async () => {
  const { page, close, log } = await openApp({});
  await page.waitForFunction(() => TC.ready && TC.seatsLoaded, null, { timeout: 8000 });
  await click(page, '[data-a="tab"][data-x="schedule"]'); await click(page, '[data-a="schedTab"][data-x="planner"]'); await tick(page, 2500);
  const r = await page.evaluate(() => {
    const L0 = TCPL.ledger(), cp = TCPL.coursePrereqs, ps = TCPL.prereqStatus, G = TCPL.geCourses, gN = G.length, st = TC.profile.class_standing, out = {};
    const N = (codes, year, term, more) => Object.assign({ codes, year, term: term || 'Fall', title: codes.join(' or '), choice: codes.length > 1 }, more || {});
    const run = (need, needU) => planRecs(Object.assign({}, L0, { need, needU: needU || [] }));
    const codes = R => R.picks.map(c => c.code);
    const keepPeople = TC.friends.map(f => [f, (PEOPLE[f].unplaced || []).slice()]);
    try {
      TCPL.coursePrereqs = c => c === 'BUS 4488' ? { req: [['MATH 9999']] } : c === 'BUS 4401' ? { req: [['BUS 3346']] } : c === 'STAT 2170' ? { req: [['BUS 3346', 'PHIL 3331']] } : null;
      TCPL.prereqStatus = c => ({ state: c === 'BUS 4488' ? 'unmet' : 'met' });
      out.taking = codes(run([N(['BUS 3431'], 3), N(['ECON 2303'], 3)]));
      out.prereq = { picks: codes(run([N(['BUS 4488'], 3), N(['ECON 2303'], 3)])), all: run([N(['BUS 4488'], 3)]).all.map(c => c.code) };
      out.choice = codes(run([N(['BUS 3346', 'BUS 3387'], 3)]));
      out.dupe = codes(run([N(['BUS 3346'], 3), N(['BUS 3346', 'BUS 4401'], 3)]));   /* BUS 3346 outscores BUS 4401 for both */
      const un = run([N(['BUS 3346'], 3), N(['BUS 4401'], 3), N(['STAT 2170'], 3)]).all.find(c => c.code === 'BUS 3346');
      out.unlocks = un && un.un;   /* BUS 4401 needs it; STAT 2170's group is already covered by PHIL 3331 */
      TCPL.coursePrereqs = () => null;
      /* behind the flowchart beats friends, a GE and the term: BUS 4488 (Year 3 Fall, 3 friends, counts twice) vs STAT 2170 (Year 2 Spring) */
      TC.friends.slice(0, 3).forEach(f => { PEOPLE[f].unplaced = (PEOPLE[f].unplaced || []).concat(['BUS 4488']); });
      G.push({ code: 'BUS 4488', name: 'fixture', area: 'Area ZZ', areaKey: 'ZZ', units: 4, prof: '__tbd', workload: '' });
      const b = run([N(['BUS 4488'], 3, 'Fall'), N(['STAT 2170'], 2, 'Spring')], [{ type: 'ge', area: 'ZZ', ti: 0, title: 'GE ZZ' }]);
      out.behind = b.picks.map(c => [c.code, pickReason(c).t, c.behind, c.reqN, c.fr.length]);
      G.splice(gN);
      TC.profile.class_standing = 'Freshman';
      out.ahead = codes(run([N(['BUS 4401'], 4), N(['ECON 2303'], 2)]));
    } finally { TCPL.coursePrereqs = cp; TCPL.prereqStatus = ps; G.splice(gN); TC.profile.class_standing = st; keepPeople.forEach(([f, u]) => { PEOPLE[f].unplaced = u; }); }
    return out; });
  ok(r.taking.length === 1 && r.taking[0] === 'ECON 2303', 'rank: a class you’re taking now is never a pick', r.taking);
  ok(!r.prereq.picks.includes('BUS 4488') && !r.prereq.all.includes('BUS 4488') && r.prereq.picks.includes('ECON 2303'), 'rank: a class whose prerequisites you haven’t met is never a pick (or a candidate)', r.prereq);
  ok(r.choice.length === 1, 'rank: a “pick 1” requirement gets one pick, not one per option', r.choice);
  ok(r.dupe.filter(c => c === 'BUS 3346').length === 1 && r.dupe.includes('BUS 4401'), 'rank: a class that fits two requirements is picked once', r.dupe);
  ok(Array.isArray(r.unlocks) && r.unlocks.join() === 'BUS 4401', 'rank: “unlocks” counts a requirement that still needs it, not one whose prerequisite you already covered', r.unlocks);
  ok(r.behind[0] && r.behind[0][0] === 'STAT 2170' && r.behind[0][1] === 'Top priority' && r.behind[1] && r.behind[1][0] === 'BUS 4488' && r.behind[1][3] === 2 && r.behind[1][4] === 3, 'rank: a class you’re behind on is #1 even against a class with three friends that counts twice', r.behind);
  ok(r.ahead.join() === 'ECON 2303', 'rank: a freshman isn’t handed a Year 4 class', r.ahead);
  /* the section a pick adds: an open seat over a waitlist even with a better-rated professor; a waitlist over full */
  const bs = await page.evaluate(() => { const ss = secsOf('BUS 3431'), keep = ss.map(x => x.status), out = {};
    try { out.open = plBestSec('BUS 3431').id; ss.find(x => x.id === '70100').status = 'full'; ss.find(x => x.id === '70101').status = 'wait'; out.full = plBestSec('BUS 3431').id; } finally { ss.forEach((x, i) => { x.status = keep[i]; }); }
    return out; });
  ok(bs.open === '70101' && bs.full === '70101', 'rank: a pick’s section is an open seat before a waitlist (even with a better-rated professor), and a waitlist before a full one (70100 at 4.5 full, 70101 at 3.6 waitlisted)', bs);
  /* the hero while prerequisites load, and when they failed */
  const hero = async v => { await page.evaluate(v => { UI.pl.prereqs = v; render(true); }, v); await tick(page, 200); return page.evaluate(() => ({ t: document.querySelector('.pk-hero').innerText, n: document.querySelectorAll('.pk-hero .pk').length })); };
  let h = await hero(undefined);
  ok(/Checking prerequisites/.test(h.t) && h.n === 0, 'rank: no picks until the prerequisites have loaded', h);
  h = await hero(false);
  ok(/Prerequisites didn’t load, so these picks don’t check them/.test(h.t) && h.n > 0, 'rank: if they failed, the picks say they don’t check prerequisites', h);
  await hero(true);
  /* no concentration yet: the Planner asks, with its choices as buttons */
  const cc = await page.evaluate(() => { const c = document.querySelector('#scroll .pk-conc'); return c && { t: c.innerText, b: [...c.querySelectorAll('[data-a="pickConc"]')].map(b => [b.dataset.x, Math.round(b.getBoundingClientRect().height)]) }; });
  ok(cc && /Pick your concentration/.test(cc.t) && cc.b.length >= 2 && cc.b.every(b => b[1] >= 44) && cc.b.some(b => b[0] === 'Financial Management'), 'rank: with no concentration chosen the Planner asks for it, 44px buttons', cc);
  await click(page, '.pk-conc [data-a="pickConc"][data-x="Financial Management"]'); await tick(page, 800);
  ok(await page.locator('#scroll .pk-conc').count() === 0, 'rank: choosing one clears the ask');
  ok(log.errors.length === 0, 'rank: no page errors', log.errors);
  await close();
};

tests.friendPlans = async () => {
  const { page, close, log } = await openApp({});
  ok(log.reads.some(r => /^plans\?/.test(r) && /user_id=neq\./.test(r) && /term=eq\.2268/.test(r)), 'friend plans: read with the desktop’s query (term, not me)');
  /* Avery has a chat with me, so she is under Chats (2026-10-03); her page opens from the chat header. */
  const openAvery = async () => { await click(page, '.chathdr [data-a="openFriend"]'); await tick(page, 400); };
  await click(page, '[data-a="tab"][data-x="friends"]');
  await click(page, `#fbody .thread[data-x="${FX.CONVS[0].id}"]`); await tick(page, 400);
  await openAvery();
  const view = () => page.evaluate(() => { const c = document.querySelector('.card.fweek'), sw = c && c.querySelector('.fsw'), l = document.querySelector('.card.list');
    return c && { title: c.querySelector('.fwk-t').innerText, sw: sw ? [...sw.querySelectorAll('button')].map(b => [b.innerText, b.dataset.y, b.getAttribute('aria-pressed'), Math.round(b.getBoundingClientRect().height)]) : null,
      plan: !!c.querySelector('.plancol.plan-A'), blocks: [...c.querySelectorAll('.g-b')].map(b => b.dataset.x), note: (c.querySelector('.fwk-n') || {}).innerText || '', list: l ? l.innerText.replace(/\s+/g, ' ') : '',
      cards: document.querySelectorAll('.card.fweek').length, oldCard: /’s plans/.test(document.getElementById('scroll').innerText), pill: /with you/i.test((document.querySelector('#scroll .row') || {}).innerText || '') || !!document.querySelector('#scroll .pillchip'),
      handle: (document.querySelector('.fhandle') || {}).innerText || '' }; });
  let v = await view();
  ok(v && v.title === 'Fall 2026' && v.sw && v.sw.map(x => x[0]).join('|') === 'Fall|A' && v.sw[0][2] === 'true' && !v.plan && v.cards === 1 && !v.oldCard, 'friend plans: the week card says Fall 2026 and has a Fall / A switch — only the plan she shares; no separate plans card', v);
  ok(v.sw.every(x => x[3] >= 40) && !v.pill && /^@aquill · /.test(v.handle), 'friend plans: the switch is tappable; no “N classes with you” pill; the status sits after the @handle', v);
  await click(page, '.fsw button[data-y="A"]');
  v = await view();
  ok(v.title === 'Plan A' && v.plan && v.sw[1][2] === 'true' && v.blocks.includes('BUS 3438') && v.blocks.includes('STAT 2170') && /^2 classes · 1 with you$/.test(v.note), 'friend plans: A draws her Plan A on the same card in the plan’s colour, with what’s in it', v);
  ok(/BUS 3438[\s\S]*You too[\s\S]*STAT 2170/.test(v.list) && !/PHIL 3331/.test(v.list), 'friend plans: the class list follows the switch — her plan’s sections, “You too” on yours', v.list);
  await click(page, '[data-a="back"]'); await openAvery();
  ok((await view()).title === 'Plan A', 'friend plans: the choice is kept for that friend while the app is open');
  await click(page, '.fsw button[data-y="now"]');
  v = await view();
  ok(v.title === 'Fall 2026' && !v.plan && v.blocks.includes('BUS 4442') && /PHIL 3331/.test(v.list), 'friend plans: Fall brings back her week and its list', v);
  /* A choice pointing at a plan she no longer shares falls back to her week; a plan whose sections are all gone
     says so and draws no empty list. */
  const A = await page.evaluate(() => Object.keys(TC.friendPlans).find(id => PEOPLE[id] && PEOPLE[id].name === 'Avery Quill'));
  await page.evaluate(id => { UI.fplan[id] = 'C'; render(true); }, A);
  v = await view();
  ok(v.title === 'Fall 2026' && v.sw[0][2] === 'true', 'friend plans: a remembered plan she no longer shares falls back to her week', v);
  const keep = await page.evaluate(id => { const k = TC.friendPlans[id].A; TC.friendPlans[id].A = ['zz-gone']; UI.fplan[id] = 'A'; render(true); return k; }, A);
  v = await view();
  ok(v.title === 'Plan A' && /^0 classes · 1 no longer listed$/.test(v.note) && await page.locator('#scroll .card.list').count() === 0 && v.blocks.length === 0, 'friend plans: a plan whose sections are all gone says so, with no empty grid or list', v);
  await page.evaluate(([id, k]) => { TC.friendPlans[id].A = k; UI.fplan[id] = null; render(true); }, [A, keep]);
  await click(page, '[data-a="back"]'); await click(page, '[data-a="back"]'); await click(page, '.li:has-text("Rowan Testa")');
  v = await view();
  ok(v && v.sw === null && /No plans shared/.test(await page.locator('.card.fweek .fwk-h').innerText()), 'friend plans: says so, neutrally, when a friend shares none — and no switch', v);
  ok(log.errors.length === 0, 'friend plans: no page errors', log.errors);
  await close();
};

tests.friendPlansLoading = async () => {
  /* Plans that haven't arrived yet must not read as "no shared plans". */
  const { page, close } = await openApp({ hook: (url, m) => url.pathname.endsWith('/plans') && /neq/.test(url.search) ? { status: 500, body: '{}' } : null });
  await click(page, '[data-a="tab"][data-x="friends"]'); await click(page, '.li:has-text("Rowan Testa")');
  ok(!/No plans shared/.test(await text(page)) && await page.locator('.fsw').count() === 0, 'friend plans: a failed or pending load says nothing, not “none”, and shows no switch');
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
  await click(page, '[data-a="tab"][data-x="schedule"]'); await click(page, '[data-a="schedTab"][data-x="past"]'); await tick(page, 2500);
  t = await text(page);
  ok(/Financial Management/.test(t) && !/Pick your concentration/.test(t), 'profile: the concentration picked on the desktop carries over (same origin, same major)', t.slice(0, 300));
  await close();

  ({ page, close } = await openApp({ init: `localStorage.setItem('professify-profile', JSON.stringify({ major: 'Plant Sciences', conc: 'Financial Management' }))` }));
  await click(page, '[data-a="tab"][data-x="schedule"]'); await click(page, '[data-a="schedTab"][data-x="past"]'); await tick(page, 2500);
  ok(/Pick your concentration/.test(await text(page)), 'profile: a desktop memory for another major is ignored');
  await click(page, '[data-a="pickConc"][data-x="Financial Management"]'); await tick(page, 800);
  const mem = await page.evaluate(() => localStorage.getItem('termchamp_app_conc'));
  ok(mem && JSON.parse(mem).conc === 'Financial Management' && JSON.parse(mem).u === FX.ME.id && JSON.parse(mem).major === FX.ME.major, 'profile: picking a concentration is remembered on this device, per account', mem);
  await close();
  ({ page, close } = await openApp({ init: `localStorage.setItem('termchamp_app_conc', JSON.stringify({ u: ${JSON.stringify(FX.ME.id)}, major: ${JSON.stringify(FX.ME.major)}, conc: 'Financial Management' }))` }));
  await click(page, '[data-a="tab"][data-x="schedule"]'); await click(page, '[data-a="schedTab"][data-x="past"]'); await tick(page, 2500);
  ok(!/Pick your concentration/.test(await text(page)), 'profile: the phone’s own memory is read back on the next visit');
  await close();
  ({ page, close } = await openApp({ init: `localStorage.setItem('termchamp_app_conc', JSON.stringify({ u: 'someone-else', major: ${JSON.stringify(FX.ME.major)}, conc: 'Financial Management' }))` }));
  await click(page, '[data-a="tab"][data-x="schedule"]'); await click(page, '[data-a="schedTab"][data-x="past"]'); await tick(page, 2500);
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

/* Delete account in the app (App Store 5.1.1(v), 2026-10-04), with 30 days to recover (same day).
   The rpc body is the promise: keep = p_delete_reviews false, switch off = true. A hook answers the
   deletion rpcs so the bodies are seen; my_account_deletion is stateful for the recovery tests. */
const PURGE_AT = '2026-11-03T12:00:00.123456+00:00';   // noon UTC: Nov 3 in every US zone; microseconds as Postgres sends them
const delHook = (calls, answer) => (url, m, body) => {
  const fn = url.pathname.startsWith('/rest/v1/rpc/') ? url.pathname.slice(13) : '';
  if (['request_account_deletion', 'cancel_account_deletion', 'my_account_deletion', 'delete_my_account_v2', 'delete_my_account'].includes(fn)) {
    calls.push({ fn, body }); return answer(fn, body);
  }
  return null;
};
const okDel = fn => fn === 'request_account_deletion' ? { status: 200, body: JSON.stringify(PURGE_AT) } : fn === 'my_account_deletion' ? { status: 200, body: '[]' } : { status: 200, body: 'null' };
const toDelete = async page => {
  await click(page, '.homehdr .me-btn'); await click(page, '[data-a="openSettings"]'); await tick(page, 500);
  await click(page, '[data-a="openDeleteAccount"]'); await tick(page, 500);
};
tests.deleteAccount = async () => {
  const calls = [];
  const { page, close, log } = await openApp({ rpc: Object.assign({}, FX.RPC, { my_reviews: [FX.MY_REVIEW] }), hook: delHook(calls, okDel) });
  await click(page, '.homehdr .me-btn'); await click(page, '[data-a="openSettings"]'); await tick(page, 500);
  let t = await text(page);
  ok(await page.locator('[data-a="openDeleteAccount"]').count() === 1 && !/use Settings on/.test(t), 'delete: Settings has a Delete account button, not a pointer to the website', t.slice(-300));
  await click(page, '[data-a="openDeleteAccount"]'); await tick(page, 500);
  t = await text(page);
  ok(/Other students stop seeing your profile, classes and plans right away/.test(t) && /permanently deleted after 30 days/.test(t) && /Sign in before then to recover it/.test(t) && /profile photo is removed now/.test(t), 'delete: the screen says 30 days, hidden at once, the photo now, and how to recover', t.slice(0, 500));
  ok(/Deleted after 30 days/.test(t) && /Messages you sent/.test(t) && /What’s kept/.test(t) && !/permanently deletes your TermChamp account/.test(t), 'delete: what goes after 30 days, and what stays', t.slice(0, 500));
  ok(/Your 1 review/.test(t) && await page.locator('[data-a="toggleKeepReviews"].on').count() === 1, 'delete: one review counted, and Keep my reviews is ON by default', t);
  ok(await page.locator('#delgo').isDisabled(), 'delete: the button is off until DELETE is typed');
  await page.locator('#delconfirm').fill('DELET');
  ok(await page.locator('#delgo').isDisabled(), 'delete: a partial word keeps it off');
  await page.locator('#delconfirm').fill('delete');
  ok(!(await page.locator('#delgo').isDisabled()), 'delete: DELETE in any case turns it on');
  ok(!calls.some(c => c.fn === 'request_account_deletion'), 'delete: nothing is sent before the button', calls);
  await page.locator('#delconfirm').press('Enter'); await tick(page, 400);
  ok(!calls.some(c => c.fn === 'request_account_deletion') && /Delete account/.test(await text(page)), 'delete: Enter in the box does not delete — only the button does', calls);
  await page.evaluate(() => {
    localStorage.setItem('termchamp_app_recent', '{"u":"x","items":[]}'); localStorage.setItem('termchamp_app_conc', '{"u":"x"}');
    /* survive the reload: every set/remove is noted in sessionStorage */
    const note = (k, v) => { try { Storage.prototype.setItem.__o.call(sessionStorage, k, (sessionStorage.getItem(k) || '') + '|' + v); } catch (e) {} };
    const os = Storage.prototype.setItem, orm = Storage.prototype.removeItem;
    Storage.prototype.setItem = function (k, v) { if (k !== '__set' && k !== '__rm') note('__set', k + '=' + v); return os.call(this, k, v); };
    Storage.prototype.setItem.__o = os;
    Storage.prototype.removeItem = function (k) { note('__rm', k); return orm.call(this, k); };
  });
  await page.locator('#delconfirm').fill('delete');
  await Promise.all([page.waitForEvent('framenavigated', { timeout: 10000 }), page.locator('#delgo').click()]);
  await page.waitForTimeout(800);
  const req = calls.filter(c => c.fn === 'request_account_deletion');
  ok(req.length === 1 && req[0].body && req[0].body.p_delete_reviews === false, 'delete: keep → request_account_deletion(p_delete_reviews: false), once', calls);
  ok(!calls.some(c => /^delete_my_account/.test(c.fn)), 'delete: nothing is deleted now — no immediate delete is called', calls);
  const photoAt = log.writes.findIndex(x => /^storage:avatars/.test(x.table) && x.m === 'DELETE');
  ok(photoAt >= 0, 'delete: the photo is removed through the Storage API', log.writes.filter(x => /storage/.test(x.table)));
  ok(log.writes.some(x => x.table === 'profiles' && x.m === 'PATCH' && x.body && x.body.avatar_url === null), 'delete: the profile stops pointing at the photo', log.writes.filter(x => x.table === 'profiles'));
  const outs = log.writes.filter(x => x.table === 'auth:logout');
  ok(outs.length === 1 && /scope=global/.test(outs[0].query || ''), 'delete: signs out on every device (one global sign-out)', log.writes.filter(x => /^auth/.test(x.table)).map(x => x.table + (x.query || '')));
  const noted = await page.evaluate(() => [sessionStorage.getItem('__set') || '', sessionStorage.getItem('__rm') || '']);
  ok(noted[0].includes('|tc_deleted=' + PURGE_AT), 'delete: the sign-in screen is handed the recovery date', noted);
  ok(/\|sb-rqkndeqbcahozidniesn-auth-token\b/.test(noted[1]), 'delete: the session is dropped on this phone before the reload', noted);
  const left = await page.evaluate(() => [localStorage.getItem('termchamp_app_recent'), localStorage.getItem('termchamp_app_conc')]);
  ok(left[0] === null && left[1] !== null, 'delete: recent searches are cleared; the concentration (phone-only) stays for a recovery', left);
  ok(log.errors.length === 0, 'delete: no page errors', log.errors);
  await close();
};
tests.deletePhotoFails = async () => {
  /* Storage refuses the photo twice: the account is still scheduled, and the profile keeps its link
     (a recovered profile never points at a file that's gone). */
  const calls = [];
  const { page, close, log } = await openApp({ rpc: Object.assign({}, FX.RPC, { my_reviews: [] }), hook: (url, m, body) => {
    if (url.pathname.startsWith('/storage/v1/object/avatars') && m === 'DELETE') { log.writes.push({ m, table: 'storage:avatars(refused)' }); return { status: 500, body: JSON.stringify({ statusCode: '500', error: 'x', message: 'refused' }) }; }
    return delHook(calls, okDel)(url, m, body);
  } });
  await toDelete(page); await page.locator('#delconfirm').fill('DELETE');
  await Promise.all([page.waitForEvent('framenavigated', { timeout: 10000 }), page.locator('#delgo').click()]);
  ok(log.writes.filter(x => x.table === 'storage:avatars(refused)').length === 2, 'delete: a refused photo removal is tried twice', log.writes.filter(x => /storage/.test(x.table)).length);
  ok(!log.writes.some(x => x.table === 'profiles' && x.m === 'PATCH'), 'delete: the profile keeps its photo link when the photo couldn’t be removed', log.writes.filter(x => x.table === 'profiles'));
  ok(calls.filter(c => c.fn === 'request_account_deletion').length === 1, 'delete: the deletion is still scheduled', calls);
  await close();
};
tests.deleteAccountReviews = async () => {
  const calls = [];
  const { page, close } = await openApp({ rpc: Object.assign({}, FX.RPC, { my_reviews: [FX.MY_REVIEW] }), hook: delHook(calls, okDel) });
  await toDelete(page);
  await click(page, '[data-a="toggleKeepReviews"]');
  ok(await page.locator('[data-a="toggleKeepReviews"].off').count() === 1 && /Your review is deleted along with your account/.test(await text(page)), 'delete: switching it off says the review goes too', await text(page));
  await page.locator('#delconfirm').fill('DELETE');
  await Promise.all([page.waitForEvent('framenavigated', { timeout: 10000 }), page.locator('#delgo').click()]);
  const req = calls.filter(c => c.fn === 'request_account_deletion');
  ok(req.length === 1 && req[0].body && req[0].body.p_delete_reviews === true, 'delete: off → p_delete_reviews: true', calls);
  await close();
};
tests.deleteAccountFails = async () => {
  const calls = [];
  const { page, close } = await openApp({ rpc: Object.assign({}, FX.RPC, { my_reviews: [] }), hook: delHook(calls, fn => fn === 'request_account_deletion' ? { status: 400, body: JSON.stringify({ code: 'XX000', message: 'internal boom', details: null, hint: null }) } : okDel(fn)) });
  await toDelete(page);
  let t = await text(page);
  ok(!/Keep my reviews/.test(t), 'delete: no reviews → no reviews switch', t);
  await page.locator('#delconfirm').fill('DELETE'); await page.locator('#delgo').click(); await tick(page, 600);
  t = await text(page);
  ok(/still here/.test(t) && /Delete account/.test(t) && !(await page.locator('#delgo').isDisabled()), 'delete: a refusal stays on the screen, says the account is still here, and can be retried', t.slice(-300));
  ok(!/boom/.test(t), 'delete: raw database text is never shown', t.slice(-300));
  await close();
  const c2 = [];
  const o = await openApp({ rpc: Object.assign({}, FX.RPC, { my_reviews: [] }), hook: delHook(c2, fn => fn === 'request_account_deletion' ? { status: 400, body: JSON.stringify({ code: 'P0001', message: 'not signed in', details: null, hint: null }) } : okDel(fn)) });
  await toDelete(o.page); await o.page.locator('#delconfirm').fill('DELETE'); await o.page.locator('#delgo').click(); await tick(o.page, 600);
  ok(/Not signed in\. Your account wasn’t deleted\./.test(await text(o.page)), 'delete: our own refusal is shown, and says the account wasn’t deleted', (await text(o.page)).slice(-200));
  await o.close();
  const o2 = await openApp({ rpc: Object.assign({}, FX.RPC, { my_reviews: { __error: { code: 'XX000', message: 'down', details: null, hint: null } } }), hook: delHook([], okDel) });
  await toDelete(o2.page);
  ok(/Your reviews/.test(await text(o2.page)) && await o2.page.locator('[data-a="toggleKeepReviews"]').count() === 1, 'delete: reviews that failed to load still get the switch (never hidden because we couldn’t tell)', (await text(o2.page)).slice(0, 400));
  await o2.close();
};
tests.deleteAccountOldSql = async () => {
  /* Before professify-delete-account-30-days.sql runs: refuse, and never fall back to deleting now. */
  const missing = { status: 404, body: JSON.stringify({ code: 'PGRST202', message: 'Could not find the function', details: null, hint: null }) };
  const calls = [];
  const o = await openApp({ rpc: Object.assign({}, FX.RPC, { my_reviews: [FX.MY_REVIEW] }), hook: delHook(calls, fn => fn === 'my_account_deletion' ? okDel(fn) : missing) });
  await toDelete(o.page);
  await o.page.locator('#delconfirm').fill('DELETE'); await o.page.locator('#delgo').click(); await tick(o.page, 600);
  ok(/isn’t switched on yet, so your account wasn’t deleted/.test(await text(o.page)), 'delete: old SQL → says it isn’t on and nothing happened', (await text(o.page)).slice(-200));
  ok(!calls.some(c => /^delete_my_account/.test(c.fn)), 'delete: old SQL never falls back to deleting at once', calls);
  await o.close();
};
tests.deletedLanding = async () => {
  const { page, close } = await openApp({ signedIn: false, init: `try { if (!sessionStorage.getItem('tc_seen')) { sessionStorage.setItem('tc_seen', '1'); sessionStorage.setItem('tc_deleted', '${PURGE_AT}'); } } catch (e) {}` });
  const t = await page.locator('body').innerText();
  ok(/Your account is scheduled for deletion\. Sign in before Nov 3, 2026 to recover it\./.test(t), 'delete: the sign-in screen says it’s scheduled and until when it can be recovered (with the year)', t.slice(0, 300));
  await page.reload(); await page.waitForTimeout(1500);
  ok(!/scheduled for deletion/.test(await page.locator('body').innerText()), 'delete: only once — a later open doesn’t say it again');
  await close();
};
tests.recoverAccount = async () => {
  /* Signing in to an account being deleted: one screen first, nothing else loaded. Recover → back. */
  let pending = true; const calls = [];
  const { page, close, log } = await openApp({ hook: delHook(calls, fn => fn === 'my_account_deletion' ? { status: 200, body: JSON.stringify(pending ? [{ purge_after: PURGE_AT, delete_reviews: false }] : []) }
    : fn === 'cancel_account_deletion' ? (pending = false, { status: 200, body: 'true' }) : { status: 200, body: 'null' }) });
  let t = await page.locator('body').innerText();
  ok(/Recover your account\?/.test(t) && /permanently deleted on Nov 3, 2026/.test(t) && /other students can’t see it/.test(t) && /except your profile photo/.test(t), 'recover: signing in shows the recover screen with the date, and says the photo doesn’t come back', t.slice(0, 400));
  ok(await page.locator('.tabbar').count() === 0, 'recover: the app isn’t behind it');
  /* (your own profile row is read alongside the check, so the check adds no wait; nothing else is) */
  ok(!log.reads.some(r => /^(my_sections|saved_classes|friend_requests|plans|class_history|conversation_members|messages)\b/.test(r)) && log.reads.filter(r => /^profiles\b/.test(r)).length <= 1, 'recover: nothing beyond your own profile row is loaded before deciding', log.reads.filter(r => !/course_|rpc:/.test(r)));
  await page.locator('[data-a="recoverAccount"]').click(); await tick(page, 1500); await tick(page, 1500);
  ok(calls.filter(c => c.fn === 'cancel_account_deletion').length === 1, 'recover: Recover my account calls cancel_account_deletion() once', calls);
  ok(await page.locator('.tabbar').count() === 1 && !/Recover your account\?/.test(await page.locator('body').innerText()), 'recover: the app loads as before afterwards', (await page.locator('body').innerText()).slice(0, 200));
  ok(log.reads.some(r => /^profiles\b/.test(r)), 'recover: the account’s data loads after recovering');
  ok(log.errors.length === 0, 'recover: no page errors', log.errors);
  await close();
};
tests.recoverAccountFails = async () => {
  const calls = [];
  const { page, close, log } = await openApp({ hook: delHook(calls, fn => fn === 'my_account_deletion' ? { status: 200, body: JSON.stringify([{ purge_after: PURGE_AT, delete_reviews: true }]) }
    : fn === 'cancel_account_deletion' ? { status: 400, body: JSON.stringify({ code: 'XX000', message: 'internal boom', details: null, hint: null }) } : { status: 200, body: 'null' }) });
  await page.locator('[data-a="recoverAccount"]').click(); await tick(page, 800);
  const t = await page.locator('body').innerText();
  ok(/Recover your account\?/.test(t) && /still set to be deleted/.test(t) && !/boom/.test(t), 'recover: a refused recovery says so and stays on the screen', t.slice(0, 400));
  ok(!(await page.locator('[data-a="recoverAccount"]').isDisabled()), 'recover: it can be tried again');
  /* (the harness signs back in on every load, so the proof is the sign-out request, and no cancel) */
  await Promise.all([page.waitForEvent('framenavigated', { timeout: 10000 }), page.locator('[data-a="signOut"]').first().click()]);
  ok(log.writes.some(x => x.table === 'auth:logout') && calls.filter(c => c.fn === 'cancel_account_deletion').length === 1, 'recover: Sign out signs out and leaves it pending (no second cancel)', log.writes.filter(x => /^auth/.test(x.table)).map(x => x.table));
  await close();
};
tests.pendingCheckRefresh = async () => {
  /* The check also runs on every refresh. A failed one there keeps the app and says so. */
  let n = 0;
  const { page, close } = await openApp({ hook: delHook([], fn => fn === 'my_account_deletion' ? (n++ ? { status: 500, body: JSON.stringify({ code: 'XX000', message: 'down', details: null, hint: null }) } : { status: 200, body: '[]' }) : { status: 200, body: 'null' }) });
  ok(await page.locator('.tabbar').count() === 1, 'refresh: the app loaded');
  await page.clock.runFor(125000); await page.evaluate(() => document.dispatchEvent(new Event('visibilitychange'))); await tick(page, 800);
  ok(n >= 2, 'refresh: coming back to the app asks again', n);
  ok(await page.locator('.tabbar').count() === 1 && !/Couldn’t load your profile/.test(await page.locator('body').innerText()), 'refresh: a failed check keeps the app (never the error screen)', (await page.locator('body').innerText()).slice(0, 200));
  ok(/Couldn’t refresh/.test(await page.locator('#toast').innerText()), 'refresh: and says it couldn’t refresh', await page.locator('#toast').innerText());
  await close();
};
tests.pendingCheck = async () => {
  /* Couldn't tell → say so (never load the app over an account that may be being deleted). The SQL
     not being there yet → the app loads as it always has. */
  const o = await openApp({ hook: delHook([], fn => fn === 'my_account_deletion' ? { status: 500, body: JSON.stringify({ code: 'XX000', message: 'down', details: null, hint: null }) } : { status: 200, body: 'null' }) });
  ok(/Couldn’t load your profile/.test(await o.page.locator('body').innerText()) && await o.page.locator('.tabbar').count() === 0, 'recover: a failed check shows the error screen, not the app', (await o.page.locator('body').innerText()).slice(0, 200));
  await o.close();
  const o2 = await openApp({ hook: delHook([], fn => fn === 'my_account_deletion' ? { status: 404, body: JSON.stringify({ code: 'PGRST202', message: 'Could not find the function', details: null, hint: null }) } : { status: 200, body: 'null' }) });
  ok(await o2.page.locator('.tabbar').count() === 1, 'recover: before the SQL runs, the app loads normally');
  await o2.close();
};

/* ---- Block, Report, Leave group (App Store chunk 3, 2026-10-04) -------------------------------- */
const RW = FX.FRIENDS[1], SKY = FX.FRIENDS[2], GROUP = FX.CONVS[1], DIRECT = FX.CONVS[0];
const BLK = { id: '33333333-3333-4333-8333-333333333339', display_name: 'Blocked Fixture', username: 'bfix', avatar_url: null };
const toastText = page => page.locator('#toast').innerText();
/* block_user() / unblock_user() / my_blocks() as the database does them: the block, and the
   friendship gone in the same call; my_blocks() answers with what's blocked now. */
const blockHook = (calls, ref, fail) => (url, m, body) => {
  ref.blocks = ref.blocks || [];
  if (url.pathname === '/rest/v1/rpc/my_blocks') { ref.reads = (ref.reads || 0) + 1; return { status: 200, body: JSON.stringify(ref.blocks) }; }
  if (url.pathname === '/rest/v1/rpc/unblock_user') { ref.blocks = ref.blocks.filter(b => b.id !== (body && body.p_target)); return null; }   // the stand-in answers (and logs) it
  if (url.pathname !== '/rest/v1/rpc/block_user') return null;
  calls.push(body);
  if (fail) return { status: 400, body: JSON.stringify({ code: 'XX000', message: 'boom', details: null, hint: null }) };
  if (ref.T) ref.T.friend_requests = ref.T.friend_requests.filter(r => !((r.from_user === body.p_target && r.to_user === FX.ME.id) || (r.to_user === body.p_target && r.from_user === FX.ME.id)));
  ref.blocks = ref.blocks.filter(b => b.id !== body.p_target).concat([{ id: body.p_target, display_name: 'Blocked by test', username: null, avatar_url: null, created_at: '2026-09-29T17:00:00Z' }]);
  return { status: 200, body: 'null' };
};
/* 18:15: no ⋯ in a chat. A group's name opens its sheet; a 1:1's sheet is a hold on its row in Chats
   (and its Report / Block live on the person's page too). */
const chatSheet = async (page) => {
  if (await page.locator('.chathdr [data-a="chatMenu"]').count()) { await click(page, '.chathdr [data-a="chatMenu"]'); return; }
  const cid = await page.evaluate(() => cur().s === 'chat' && cur().p ? String(cur().p.id) : null);
  if (cid) { await click(page, '[data-a="back"]'); await tick(page, 300); }
  const row = page.locator(`#fbody .thread[data-x="${cid}"]`);
  await row.evaluate(e => e.scrollIntoView({ block: 'center' })); await tick(page, 300);
  await hold(page, await row.evaluate(e => { const r = e.getBoundingClientRect(); return { x: r.x + r.width / 2, y: r.y + r.height / 2 }; }));
};
const openChatRow = async (page, cid) => { await click(page, '[data-a="tab"][data-x="friends"]'); await tick(page, 300); await click(page, `#fbody .thread[data-x="${cid}"]`); await tick(page, 600); };

tests.blockFromProfile = async () => {
  const calls = [], ref = {};
  const o = await openApp({ hook: blockHook(calls, ref), rpc: Object.assign({}, FX.RPC, { my_blocks: [] }) });
  ref.T = o.tables; const { page, close, log } = o;
  await page.waitForFunction(() => TC.ready, null, { timeout: 8000 });
  ok(ref.reads === 1, 'block: who you blocked is read at sign-in, not only in Settings', ref.reads);
  await page.evaluate(id => A.openFriend(id), RW.id); await tick(page, 400);
  const menu = page.locator(`#scroll .topbtns [data-a="personMenu"][data-x="${RW.id}"]`);
  ok(await menu.count() === 1 && /report or block/.test(await menu.getAttribute('aria-label')), 'block: a person’s page has ⋯ top right (report or block)');
  await click(page, '#scroll [data-a="personMenu"]');
  const sh = await page.locator('#sheet').innerText(), acts = await sheetActs(page);
  ok(acts.includes('reportAsk') && acts.includes('blockAsk') && /Report Rowan/.test(sh) && /Block Rowan/.test(sh) && /Rowan isn’t told/.test(sh), 'block: ⋯ offers Report Rowan and Block Rowan', { acts, sh });
  await click(page, '#sheet [data-a="blockAsk"]');
  const ask = await page.locator('#sheet').innerText();
  ok(/Block Rowan Testa\?/.test(ask) && /won’t be able to message each other or send friend requests/.test(ask) && /You stop being friends/.test(ask) && /neither of you can send messages/.test(ask) && /Rowan isn’t told/.test(ask) && calls.length === 0, 'block: asks first, and says what it does — friendship ends, shared groups stop, they aren’t told', ask);
  await click(page, '#sheet [data-a="blockGo"]'); await tick(page, 600);
  ok(calls.length === 1 && calls[0].p_target === RW.id, 'block: calls block_user() with them', calls);
  const t = await text(page);
  ok(/You blocked Rowan/.test(t) && await page.locator(`#scroll [data-a="unblock"][data-x="${RW.id}"]`).count() === 1 && await page.locator('#scroll [data-a="openChatWith"]').count() === 0 && await page.locator('#scroll [data-a="addFriend"]').count() === 0 && await page.locator('#scroll .fweek').count() === 0, 'block: their page says you blocked them, with Unblock — no Message, no Add friend, no week', t.slice(0, 300));
  ok(/Blocked Rowan/.test(await toastText(page)) && !(await page.evaluate(() => UI.sheet)), 'block: the sheet closes and says it’s done');
  ok(!(await page.evaluate(id => TC.friends.includes(id), RW.id)), 'block: no longer one of your friends');
  await click(page, '[data-a="tab"][data-x="friends"]');
  ok(await page.locator(`#fbody [data-a="openFriend"][data-x="${RW.id}"]`).count() === 0, 'block: gone from the Friends list');
  await page.evaluate(id => A.openFriend(id), RW.id); await tick(page, 400);
  await click(page, `#scroll [data-a="unblock"][data-x="${RW.id}"]`); await tick(page, 400);
  const ub = log.rpcs.filter(r => r.fn === 'unblock_user');
  ok(ub.length === 1 && ub[0].body.p_target === RW.id && !/You blocked/.test(await text(page)) && await page.locator(`#scroll [data-a="addFriend"][data-x="${RW.id}"]`).count() === 1, 'block: Unblock on their page calls unblock_user(); they come back as someone to add, not a friend', ub);
  ok(log.errors.length === 0, 'block: no page errors', log.errors);
  await close();
};

tests.blockFails = async () => {
  const calls = [];
  const { page, close } = await openApp({ hook: blockHook(calls, {}, true), rpc: Object.assign({}, FX.RPC, { my_blocks: [] }) });
  await page.waitForFunction(() => TC.ready, null, { timeout: 8000 });
  await page.evaluate(id => A.openFriend(id), RW.id); await tick(page, 400);
  await click(page, '#scroll [data-a="personMenu"]'); await click(page, '#sheet [data-a="blockAsk"]'); await click(page, '#sheet [data-a="blockGo"]'); await tick(page, 400);
  const sh = await page.locator('#sheet').innerText();
  ok(calls.length === 1 && /Couldn’t block them/.test(sh) && await page.evaluate(() => UI.sheet && UI.sheet.type) === 'blockAsk' && !/You blocked/.test(await text(page)) && await page.evaluate(id => TC.friends.includes(id), RW.id), 'block: a refused block says so and changes nothing', sh);
  await close();
};

tests.blockInChat = async () => {
  const calls = [], ref = {}, inner = blockHook(calls, ref);
  /* after a block, the friend list can't be re-read: what the app already knows has to hold */
  const hook = (url, m, body) => url.pathname === '/rest/v1/friend_requests' && m === 'GET' && calls.length ? { status: 500, body: JSON.stringify({ code: 'XX000', message: 'down', details: null, hint: null }) } : inner(url, m, body);
  const T = Object.assign({}, FX.TABLES, { messages: FX.MESSAGES.concat([{ id: 4, conversation_id: GROUP.id, sender: SKY.id, kind: 'text', body: 'Fixture note from Sky', payload: null, created_at: '2026-09-26T21:00:00Z' }]) });
  const o = await openApp({ hook, tables: T, rpc: Object.assign({}, FX.RPC, { my_blocks: [] }) });
  ref.T = o.tables; const { page, close, log } = o;
  await page.waitForFunction(() => TC.ready, null, { timeout: 8000 });
  await openChatRow(page, DIRECT.id);
  await chatSheet(page);
  let acts = await sheetActs(page), sh = await page.locator('#sheet').innerText();
  ok(acts.includes('blockAsk') && acts.includes('reportAsk') && !acts.includes('leaveAsk') && /Report Avery/.test(sh) && /Block Avery/.test(sh) && /See Avery’s page/.test(sh), 'block: a 1:1 chat’s menu (hold it in Chats) has Report Avery and Block Avery (and no Leave group)', { acts, sh });
  await click(page, '#sheet [data-a="blockAsk"]'); await click(page, '#sheet [data-a="blockGo"]'); await tick(page, 600);
  /* the 1:1's sheet was held open from Chats (no ⋯ in a chat since 18:15): open the chat again */
  if (await page.evaluate(() => cur().s) !== 'chat') { await click(page, `#fbody .thread[data-x="${DIRECT.id}"]`); await tick(page, 500); }
  const bar = page.locator('#fixbot .blockbar');
  ok(calls.length === 1 && calls[0].p_target === FX.FRIENDS[0].id && await bar.count() === 1 && /You blocked Avery\./.test(await bar.innerText()) && await page.locator('#chatin').count() === 0, 'block: the chat shows “You blocked Avery.” in place of the message box', await bar.count() && await bar.innerText());
  ok(await page.locator('#scroll .msg[data-mid="2"]').count() === 0 && await page.locator('#scroll .msg[data-mid="1"]').count() === 1 && /Messages from Avery are hidden because you blocked them\./.test(await text(page)), 'block: Avery’s messages are hidden (yours stay), and it says why', (await text(page)).slice(0, 300));
  ok(!(await page.evaluate(id => TC.friends.includes(id), FX.FRIENDS[0].id)), 'block: no longer a friend, even when the friend list can’t be re-read');
  await click(page, '[data-a="back"]'); await tick(page, 300);
  const pv = await page.locator(`#fbody .thread[data-x="${DIRECT.id}"]`).innerText().catch(() => '');
  ok(/You: Fixture message from me/.test(pv) && !/Fixture reply from Avery/.test(pv), 'block: the chat’s preview skips their message', pv);
  await click(page, `#fbody .thread[data-x="${DIRECT.id}"]`); await tick(page, 500);
  await click(page, '#fixbot .blockbar [data-a="unblock"]'); await tick(page, 400);
  ok(log.rpcs.some(r => r.fn === 'unblock_user' && r.body.p_target === FX.FRIENDS[0].id) && await page.locator('#chatin').count() === 1 && await page.locator('#fixbot .blockbar').count() === 0 && await page.locator('#scroll .msg[data-mid="2"]').count() === 1, 'block: Unblock there brings the message box and their messages back');
  /* holding someone's message in a group: Block them too */
  await page.evaluate(id => A.openChatTab(id), GROUP.id); await tick(page, 600);
  await hold(page, await msgAt(page, 3));
  acts = await sheetActs(page); sh = await page.locator('#sheet').innerText();
  ok(acts.includes('reportMsg') && acts.includes('blockAsk') && /Block Rowan/.test(sh), 'block: holding someone’s message offers Block under Report', { acts, sh });
  await click(page, '#sheet [data-a="blockAsk"]'); await click(page, '#sheet [data-a="blockGo"]'); await tick(page, 600);
  const gb = await page.locator('#fixbot .blockbar').innerText().catch(() => '');
  ok(calls.length === 2 && calls[1].p_target === RW.id && /You blocked Rowan, who’s in this group\. Neither of you can send messages here\./.test(gb) && await page.locator('#chatin').count() === 0, 'block: a group with someone you blocked says why there’s no message box', gb);
  ok(await page.locator('#fixbot .blockbar [data-a="leaveAsk"]').count() === 1 && await page.locator('#fixbot .blockbar [data-a="unblock"]').count() === 1, 'block: …and offers Leave group as well as Unblock');
  ok(await page.locator('#scroll .msg[data-mid="3"]').count() === 0 && await page.locator('#scroll .msg[data-mid="4"]').count() === 1, 'block: Rowan’s group message is hidden; Sky’s isn’t');
  const lb = await page.evaluate(() => { const el = document.getElementById('fixbot').getBoundingClientRect(), m = [...document.querySelectorAll('#scroll .msg')].pop().getBoundingClientRect(); return { bar: el.top, msg: m.bottom }; });
  ok(lb.msg <= lb.bar, 'block: the last message isn’t under the bar', lb);
  await hold(page, await msgAt(page, 4));
  ok(!(await sheetActs(page)).includes('likeMsg'), 'block: no Like in a group with someone you blocked (the database refuses it)', await sheetActs(page));
  await click(page, '#sheet .xbtn');
  const p4 = await msgAt(page, 4); await page.mouse.dblclick(p4.x, p4.y); await tick(page, 300);
  ok(!log.writes.some(w => w.table === 'message_likes'), 'block: a double-tap there doesn’t try to like');
  ok(log.errors.length === 0, 'block in chat: no page errors', log.errors);
  await close();
};

tests.blocksKept = async () => {
  let n = 0;
  const hook = url => { if (url.pathname !== '/rest/v1/rpc/my_blocks') return null; n++; return n === 1 ? new Promise(res => setTimeout(() => res({ status: 200, body: JSON.stringify([Object.assign({ created_at: '2026-09-01T00:00:00Z' }, { id: FX.FRIENDS[0].id, display_name: 'Avery Quill', username: 'aquill', avatar_url: null })]) }), 700)) :   /* the block list answers after the chats would have */ { status: 500, body: JSON.stringify({ code: 'XX000', message: 'down', details: null, hint: null }) }; };
  const { page, close } = await openApp({ hook });
  await page.waitForFunction(() => TC.ready, null, { timeout: 8000 });
  await click(page, '[data-a="tab"][data-x="friends"]'); await tick(page, 300);
  const pv = await page.locator(`#fbody .thread[data-x="${DIRECT.id}"]`).innerText().catch(() => '');
  ok(/You: Fixture message from me/.test(pv) && !/Fixture reply from Avery/.test(pv), 'blocked at sign-in: their message is never a chat’s preview', pv);
  await page.evaluate(() => TC.loadBlocks()); await tick(page, 300);
  await click(page, `#fbody .thread[data-x="${DIRECT.id}"]`); await tick(page, 500);
  ok(n === 2 && await page.locator('#fixbot .blockbar').count() === 1 && await page.locator('#scroll .msg[data-mid="2"]').count() === 0, 'blocks: a failed re-read keeps who you blocked', n);
  await page.evaluate(() => { A.openSettings(); }); await tick(page, 600);
  ok(/Couldn’t load that list/.test(await text(page)), 'blocks: Settings says the list couldn’t be read');
  await close();
};

tests.blockedHidden = async () => {
  /* People you blocked stay out of search and suggestions (the database stops everything else). */
  const rpc = Object.assign({}, FX.RPC, {
    find_people: [BLK, { id: FX.SUGGESTED.id, display_name: FX.SUGGESTED.display_name, username: FX.SUGGESTED.username }],
    suggest_friends: [Object.assign({ reason: 'Taking one of your classes', mutuals: 0, score: 11 }, BLK)].concat(FX.RPC.suggest_friends)
  });
  const { page, close } = await openApp({ rpc });
  await page.waitForFunction(() => TC.ready, null, { timeout: 8000 });
  await click(page, '[data-a="tab"][data-x="friends"]'); await tick(page, 400);
  let t = await page.locator('#fbody').innerText();
  ok(/Pat Suggestia/.test(t) && !/Blocked Fixture/.test(t), 'blocked: not in People you might know', t.slice(-300));
  await page.locator('#fq').pressSequentially('fix'); await tick(page, 900);
  t = await page.locator('#fbody').innerText();
  ok(/Pat Suggestia/.test(t) && !/Blocked Fixture/.test(t), 'blocked: not in search results', t);
  await close();
};

tests.reportPerson = async () => {
  let dup = false;
  const hook = (url, m) => dup && url.pathname === '/rest/v1/reports' && m === 'POST' ? { status: 409, body: JSON.stringify({ code: '23505', message: 'duplicate key value violates unique constraint "reports_one_per_target_idx"', details: null, hint: null }) } : null;
  const { page, close, log } = await openApp({ hook });
  await page.waitForFunction(() => TC.ready, null, { timeout: 8000 });
  await page.evaluate(id => A.openFriend(id), RW.id); await tick(page, 400);
  await click(page, '#scroll [data-a="personMenu"]'); await click(page, '#sheet [data-a="reportAsk"]');
  const sh = await page.locator('#sheet').innerText(), why = await page.evaluate(() => [...document.querySelectorAll('#sheet [data-a="sendReportX"]')].map(b => b.dataset.x));
  ok(/Report Rowan Testa/.test(sh) && /A moderator will see Rowan’s profile\. Rowan won’t know it was you\./.test(sh) && why.includes('impersonation') && why.includes('harassment') && why.length === 8 && /call 911/.test(sh), 'report: a person’s report sheet says what a moderator sees, with “Pretending to be someone else”', { sh, why });
  await click(page, '#sheet [data-a="sendReportX"][data-x="impersonation"]'); await tick(page, 300);
  const rp = log.writes.filter(w => w.table === 'reports');
  ok(rp.length === 1 && rp[0].m === 'POST' && rp[0].body.reporter === FX.ME.id && rp[0].body.kind === 'user' && rp[0].body.target_id === RW.id && rp[0].body.target_user === RW.id && rp[0].body.reason === 'impersonation' && rp[0].body.note === 'Profile: Rowan Testa (@rtesta)', 'report: files a reports row about the person, with their name and @ as they were', rp);
  ok(/Reported\. A moderator will look at it\./.test(await toastText(page)) && !(await page.evaluate(() => UI.sheet)), 'report: closes and says it went');
  dup = true;
  await click(page, '#scroll [data-a="personMenu"]'); await click(page, '#sheet [data-a="reportAsk"]'); await click(page, '#sheet [data-a="sendReportX"][data-x="spam"]'); await tick(page, 300);
  ok(/You already reported this/.test(await toastText(page)) && !(await page.evaluate(() => UI.sheet)), 'report: a second report of the same person says it’s already with a moderator');
  /* the hourly limit is a row-security refusal; a lost session is "permission denied" — not the limit */
  dup = false;
  await page.evaluate(() => { window.__rej = null; });
  const say = async err => { await page.route('**/rest/v1/reports*', r => r.fulfill({ status: 403, headers: { 'access-control-allow-origin': '*' }, contentType: 'application/json', body: JSON.stringify(err) })); await click(page, '#scroll [data-a="personMenu"]'); await click(page, '#sheet [data-a="reportAsk"]'); await click(page, '#sheet [data-a="sendReportX"][data-x="spam"]'); await tick(page, 300); const t = await toastText(page); await page.unroute('**/rest/v1/reports*'); await click(page, '#sheet .xbtn'); return t; };
  const lim = await say({ code: '42501', message: 'new row violates row-level security policy for table "reports"', details: null, hint: null });
  ok(/a lot of reports this hour/.test(lim), 'report: the hourly limit says so', lim);
  const den = await say({ code: '42501', message: 'permission denied for table reports', details: null, hint: null });
  ok(/sign-in expired/.test(den) && !/this hour/.test(den), 'report: a lost sign-in isn’t called the hourly limit', den);
  await close();
};

tests.reportReview = async () => {
  const { page, close, log } = await openApp({});
  await page.waitForFunction(() => TC.ready && TC.seatsLoaded, null, { timeout: 8000 });
  ok(log.reads.some(r => /^reviews_public\?select=id(%2C|,)professor_key/.test(r)), 'report review: reviews are read with their id', log.reads.filter(r => /reviews_public/.test(r)));
  await page.evaluate(() => A.openProf('ada examplewood')); await tick(page, 600);
  const pr = log.reads.filter(r => /^reviews_public\?/.test(r) && /professor_key=ilike/.test(r));
  ok(pr.length >= 1 && pr.every(r => /select=id(%2C|,)professor_key/.test(r)), 'report review: a professor’s own review read asks for the id too', pr);
  const flag = page.locator('#scroll .review [data-a="reportAsk"][data-x="review"][data-y="501"]');
  const fb = await flag.boundingBox().catch(() => null);
  ok(await flag.count() === 1 && (await flag.getAttribute('aria-label')) === 'Report this review' && fb && fb.width >= 40 && fb.height >= 40, 'report review: each written review has a 40px Report flag', fb);
  /* Champ's button floats over the bottom right; at the very end of the page (where a short page
     sits, and where it stays visible) the last review's flag must clear it */
  await page.evaluate(() => { const sc = document.getElementById('scroll'); sc.scrollTop = sc.scrollHeight; }); await tick(page, 300);
  const hit = await page.evaluate(() => { const q = document.querySelector('#scroll .review [data-y="501"]').getBoundingClientRect(), f = document.querySelector('.fab'); const el = document.elementFromPoint(q.left + q.width / 2, q.top + q.height / 2); return { on: !!(el && el.closest('[data-y="501"]')), fab: !!f && !document.getElementById('chrome').classList.contains('bars-hid') }; });
  ok(hit.on && hit.fab, 'report review: at the end of the page, with Champ showing, the last review’s flag is still tappable', hit);
  await flag.click(); await settle(page);
  const sh = await page.locator('#sheet').innerText(), why = await page.evaluate(() => [...document.querySelectorAll('#sheet [data-a="sendReportX"]')].map(b => b.dataset.x));
  ok(/Report this review/.test(sh) && /Whoever wrote it won’t know it was you/.test(sh) && why[0] === 'not_about_teaching' && /Not about the class or teaching/.test(sh), 'report review: the first reason is “Not about the class or teaching”', { sh, why });
  await click(page, '#sheet [data-a="sendReportX"][data-x="not_about_teaching"]'); await tick(page, 300);
  const rp = log.writes.filter(w => w.table === 'reports');
  ok(rp.length === 1 && rp[0].body.kind === 'review' && rp[0].body.target_id === '501' && rp[0].body.target_user === null && rp[0].body.reason === 'not_about_teaching' && rp[0].body.note === 'Fixture review text, clear lectures.' && rp[0].body.reporter === FX.ME.id, 'report review: files kind review with the review’s id and its words (the writer stays anonymous)', rp);
  await close();
  /* your own review has no flag */
  const o2 = await openApp({ rpc: Object.assign({}, FX.RPC, { my_reviews: [Object.assign({}, FX.MY_REVIEW, { id: 501 })] }) });
  await o2.page.waitForFunction(() => TC.ready && TC.seatsLoaded, null, { timeout: 8000 });
  await o2.page.evaluate(() => A.openProf('ada examplewood')); await tick(o2.page, 600);
  ok(await o2.page.locator('#scroll .review').count() >= 1 && await o2.page.locator('#scroll .review [data-a="reportAsk"]').count() === 0, 'report review: no flag on your own review');
  await o2.close();
};

tests.groupMenu = async () => {
  const { page, close, log } = await openApp({});
  await page.waitForFunction(() => TC.ready, null, { timeout: 8000 });
  await openChatRow(page, GROUP.id);
  await chatSheet(page);
  const sh = await page.locator('#sheet').innerText(), acts = await sheetActs(page);
  const mem = await page.evaluate(() => [...document.querySelectorAll('#sheet [data-a="openFriend"]')].map(b => b.dataset.x));
  ok(/In this group · 3 people/.test(sh) && mem.length === 2 && mem.includes(RW.id) && mem.includes(SKY.id) && /Rowan Testa/.test(sh) && /Sky Placeholder/.test(sh), 'group: its name opens a sheet that lists who’s in it', { sh, mem });
  ok(acts.includes('leaveAsk') && acts.includes('chatDelAsk') && /Report this group’s name/.test(sh) && !/Block /.test(sh), 'group: its sheet has Delete chat, Leave group and Report this group’s name', acts);
  await click(page, '#sheet [data-a="reportAsk"][data-x="group"]');
  const rs = await page.locator('#sheet').innerText();
  ok(/Report this group’s name/.test(rs) && /“Fixture Study Group”/.test(rs) && /who gave it/.test(rs), 'group: the name report says what a moderator sees', rs);
  await click(page, '#sheet [data-a="sendReportX"][data-x="hate"]'); await tick(page, 300);
  const rp = log.writes.filter(w => w.table === 'reports');
  ok(rp.length === 1 && rp[0].body.kind === 'user' && rp[0].body.target_id === 'group:' + GROUP.id && rp[0].body.target_user === RW.id && rp[0].body.reason === 'hate' && rp[0].body.note === 'Group chat name: “Fixture Study Group”', 'group: the name report is about whoever named it, with the name in the note', rp);
  await chatSheet(page);
  await click(page, `#sheet [data-a="openFriend"][data-x="${SKY.id}"]`); await tick(page, 400);
  ok(await page.evaluate(() => cur().s) === 'friend' && /Sky Placeholder/.test(await text(page)) && await page.locator('#scroll [data-a="personMenu"]').count() === 1, 'group: a member opens their page, where they can be reported or blocked');
  await close();
  /* a group you named yourself: nothing to report */
  const T = Object.assign({}, FX.TABLES, { conversations: FX.CONVS.map(c => c.id === GROUP.id ? Object.assign({}, c, { created_by: FX.ME.id }) : c) });
  const o2 = await openApp({ tables: T });
  await o2.page.waitForFunction(() => TC.ready, null, { timeout: 8000 });
  await openChatRow(o2.page, GROUP.id); await chatSheet(o2.page);
  ok(!/Report this group’s name/.test(await o2.page.locator('#sheet').innerText()) && (await sheetActs(o2.page)).includes('leaveAsk'), 'group: no name report on a group you named');
  await o2.close();
};

tests.groupStranger = async () => {
  const CASEY = { id: '44444444-4444-4444-8444-444444444441', display_name: 'Casey Member', username: 'cmember', avatar_url: null, school: 'calpoly' };
  const title = '<img src=x onerror="window.__x=1">Crew';
  const T = Object.assign({}, FX.TABLES, { profiles: FX.TABLES.profiles.concat([CASEY]), conversation_members: FX.MEMBERS.concat([{ conversation_id: GROUP.id, user_id: CASEY.id, last_read_at: null }]),
    conversations: FX.CONVS.map(c => c.id === GROUP.id ? Object.assign({}, c, { title }) : c) });
  const calls = [];
  const { page, close, log } = await openApp({ tables: T, hook: blockHook(calls, {}), rpc: Object.assign({}, FX.RPC, { my_blocks: [] }) });
  await page.waitForFunction(() => TC.ready, null, { timeout: 8000 });
  await openChatRow(page, GROUP.id);
  await chatSheet(page);
  const sh = await page.locator('#sheet').innerText();
  ok(/In this group · 4 people/.test(sh) && /Casey Member/.test(sh) && sh.includes(title) && await page.locator('#sheet img[src="x"]').count() === 0, 'group: a member who isn’t your friend is listed by name; the group’s name is shown as text', sh.slice(0, 200));
  await click(page, '#sheet [data-a="reportAsk"][data-x="group"]');
  ok((await page.locator('#sheet').innerText()).includes('“' + title + '”') && await page.locator('#sheet img[src="x"]').count() === 0 && !(await page.evaluate(() => window.__x)), 'group: the name report shows the name as text, never as markup');
  await click(page, '#sheet .xbtn'); await chatSheet(page);
  await click(page, `#sheet [data-a="openFriend"][data-x="${CASEY.id}"]`); await tick(page, 400);
  const t = await text(page);
  ok(await page.evaluate(() => cur().s) === 'friend' && /Casey Member/.test(t) && !/Not found/.test(t) && await page.locator(`#scroll [data-a="addFriend"][data-x="${CASEY.id}"]`).count() === 1, 'group: their page opens (not “Not found”), with Add friend', t.slice(0, 200));
  await click(page, '#scroll [data-a="personMenu"]'); await click(page, '#sheet [data-a="blockAsk"]');
  ok(/Block Casey Member\?/.test(await page.locator('#sheet').innerText()) && !/You stop being friends/.test(await page.locator('#sheet').innerText()), 'group: blocking someone who isn’t a friend doesn’t talk about ending a friendship');
  await click(page, '#sheet [data-a="blockGo"]'); await tick(page, 500);
  ok(calls.length === 1 && calls[0].p_target === CASEY.id && /You blocked Casey/.test(await text(page)), 'group: and they can be blocked from there', calls);
  ok(log.errors.length === 0, 'group: no page errors', log.errors);
  await close();
};

tests.leaveGroup = async () => {
  const { page, close, log } = await openApp({});
  await page.waitForFunction(() => TC.ready, null, { timeout: 8000 });
  await openChatRow(page, GROUP.id);
  await chatSheet(page); await click(page, '#sheet [data-a="leaveAsk"]');
  const ask = await page.locator('#sheet').innerText();
  ok(/Leave Fixture Study Group\?/.test(ask) && /stop getting its messages/.test(ask) && /Everyone else stays/.test(ask) && !log.writes.some(w => w.table === 'conversation_members' && w.m === 'DELETE'), 'leave: asks first', ask);
  await click(page, '#sheet [data-a="leaveGo"]'); await tick(page, 600);
  const del = log.writes.filter(w => w.table === 'conversation_members' && w.m === 'DELETE');
  ok(del.length === 1 && del[0].query.includes('conversation_id=eq.' + GROUP.id) && del[0].query.includes('user_id=eq.' + FX.ME.id), 'leave: deletes only your own membership', del);
  ok(await page.evaluate(() => cur().s) === 'friends' && await page.locator(`#fbody .thread[data-x="${GROUP.id}"]`).count() === 0 && /You left Fixture Study Group/.test(await toastText(page)), 'leave: back on Friends, the group gone from your chats, and it says so');
  ok(!log.writes.some(w => w.table === 'conversations' && w.m === 'DELETE') && !log.writes.some(w => w.table === 'messages'), 'leave: the group and its messages stay for everyone else');
  await close();
  /* a delete that removes nothing is not a leave */
  const o2 = await openApp({ hook: (url, m) => url.pathname === '/rest/v1/conversation_members' && m === 'DELETE' ? { status: 200, body: '[]' } : null });
  await o2.page.waitForFunction(() => TC.ready, null, { timeout: 8000 });
  await openChatRow(o2.page, GROUP.id);
  await chatSheet(o2.page); await click(o2.page, '#sheet [data-a="leaveAsk"]'); await click(o2.page, '#sheet [data-a="leaveGo"]'); await tick(o2.page, 500);
  ok(/still in it/.test(await toastText(o2.page)) && await o2.page.evaluate(id => TC.threads.some(t => t.id === id), GROUP.id), 'leave: a refused leave says you’re still in it and keeps the chat');
  await o2.close();
};

tests.blockedSettingsText = async () => {
  const { page, close } = await openApp({ rpc: Object.assign({}, FX.RPC, { my_blocks: [] }) });
  await click(page, '.homehdr .me-btn'); await click(page, '[data-a="openSettings"]'); await tick(page, 500);
  const t = await text(page);
  ok(/Nobody\. To block someone, tap ⋯ on their page or in your chat with them\./.test(t) && !/on termchamp\.com\./.test(t), 'settings: Blocked people says how to block in the app, not on the website', t.slice(0, 600));
  await close();
};

/* ---- Champ asks first; legal text; no screen sends you to the website (chunks 4 and 5, 2026-10-04) ---- */
tests.champConsent = async () => {
  const asks = { 'is ada good': { tool: 'professor_stats', args: { name: 'Ada Examplewood' } } };
  const { page, close, log } = await openApp({ champ: false, ask: b => asks[b.q] || null });
  await page.waitForFunction(() => TC.ready, null, { timeout: 8000 });
  await click(page, '[data-a="openChamp"]');
  let sh = await page.locator('#sheet').innerText();
  ok(/Before you ask Champ/.test(sh) && /Champ uses AI from Anthropic, the company that makes Claude/.test(sh) && /Each question you ask Champ is sent to Anthropic/.test(sh) && /Never your name, email or account/.test(sh) && /names a class or a friend, that goes with it/.test(sh) && /about 30 days, not linked to your account/.test(sh), 'consent: the first open names Anthropic and says what is sent and kept', sh.slice(0, 400));
  ok(await page.locator('#sheet [data-a="champAllow"]').count() === 1 && await page.locator('#sheet button.btn[data-a="champNotNow"]').count() === 1 && await page.locator('#champin').count() === 0 && await page.locator('#sheet [data-a="ask"]').count() === 0, 'consent: only Allow and Not now — no box, no suggestion chips');
  await click(page, '#sheet [data-a="champNotNow"]');
  ok(!(await page.evaluate(() => UI.champ)) && log.asks.length === 0, 'consent: Not now closes it, and nothing was sent');
  await page.evaluate(() => ask('first try')); await tick(page, 300); await click(page, '#sheet .xbtn');
  ok(await page.evaluate(() => UI.champPending) == null && log.asks.length === 0, 'consent: closing with × forgets the held question');
  /* a question asked another way before Allow waits on the consent screen */
  await page.evaluate(() => ask('is ada good')); await tick(page, 400);
  sh = await page.locator('#sheet').innerText();
  ok(log.asks.length === 0 && /Before you ask Champ/.test(sh) && /“is ada good” is asked as soon as you allow it/.test(sh), 'consent: a question before Allow is held, not sent', sh.slice(-300));
  ok(await page.evaluate(() => TC.ask('x')) === null && log.asks.length === 0, 'consent: TC.ask sends nothing before Allow');
  await click(page, '#sheet [data-a="champAllow"]'); await tick(page, 800);
  ok(log.asks.length === 1 && log.asks[0].q === 'is ada good' && /Ada Examplewood/.test(await page.locator('.bot .msg').last().innerText()), 'consent: Allow asks the held question', log.asks);
  ok(await page.evaluate(id => localStorage.getItem('tc_champ_ai:' + id), FX.ME.id) === '1', 'consent: remembered for this account on this phone');
  ok(/Questions go to Anthropic’s AI/.test(await page.locator('#sheet').innerText()), 'consent: the line under the box names Anthropic');
  await click(page, '#sheet button[data-a="closeSheet"]');
  /* Settings › Champ turns it off again */
  await click(page, '.homehdr .me-btn'); await click(page, '[data-a="openSettings"]'); await tick(page, 400);
  const tg = page.locator('[data-a="toggleChampAi"]');
  ok(await tg.count() === 1 && await tg.getAttribute('aria-checked') === 'true' && /Answers from Anthropic’s AI/.test(await text(page)), 'settings: Champ is on, and says it uses Anthropic’s AI');
  await click(page, '[data-a="toggleChampAi"]');
  ok(await page.locator('[data-a="toggleChampAi"]').getAttribute('aria-checked') === 'false' && await page.evaluate(id => localStorage.getItem('tc_champ_ai:' + id), FX.ME.id) === null && /Champ is off/.test(await page.locator('#toast').innerText()), 'settings: off forgets the consent');
  await page.evaluate(() => ask('is ada good')); await tick(page, 400);
  ok(log.asks.length === 1 && /Before you ask Champ/.test(await page.locator('#sheet').innerText()), 'settings: off → Champ asks again before sending anything');
  await click(page, '#sheet [data-a="champPrivacy"]'); await tick(page, 800);
  ok(await page.evaluate(() => cur().s) === 'legal' && /Champ, the assistant/.test(await text(page)), 'consent: “How Champ uses your questions” opens the privacy policy’s Champ section');
  ok(log.errors.length === 0, 'consent: no page errors', log.errors);
  await close();
};

tests.legalText = async () => {
  const { page, close } = await openApp({});
  await page.waitForFunction(() => TC.ready, null, { timeout: 8000 });
  const doc = async w => { await page.evaluate(w => A.openLegal(w), w); await tick(page, 800); return text(page); };
  const terms = await doc('terms'), guide = await doc('guidelines'), priv = await doc('privacy'), sec = await doc('security');
  const all = terms + guide + priv + sec;
  ok(/Last updated 4 October 2026/.test(terms) && /Last updated 4 October 2026/.test(priv) && /support@termchamp\.com/.test(all) && !/tdogtate/.test(all), 'legal: dated 4 October 2026, contact support@termchamp.com');
  ok(/There is no tolerance for objectionable content or abusive users/.test(terms) && /There is no tolerance for objectionable content or abusive users/.test(guide), 'legal: zero tolerance in the Terms and the Guidelines');
  ok(/a person looks at every report within 24 hours/i.test(terms) && /A person looks at every report within 24 hours/.test(guide) && !/nine reasons/.test(guide) && /group chat names/.test(guide), 'legal: reports looked at within 24 hours; what can be reported is what the app offers');
  ok(/permanently deleted after 30 days/.test(terms) && /sign in before then to recover it/.test(terms) && /after 30 days/.test(priv) && /Keep my reviews up anonymously/.test(priv) && /deleted with your account/.test(priv) && !/Your reviews stay up when you delete your account/.test(priv), 'legal: 30 days to recover, and reviews kept only if you choose');
  ok(/Champ, the assistant/.test(priv) && /called Hawk on the website/.test(priv) && /nothing is sent until you tap Allow/.test(priv) && (priv.match(/Hawk/g) || []).length === 2, 'legal: Hawk is Champ, and the phone asks first', (priv.match(/.{30}Hawk.{30}/g) || []));
  ok(!/There is no password to steal/.test(sec) && !/No advertising or analytics trackers/.test(sec) && /report or block them in the app/.test(sec), 'legal: Security no longer says there are no passwords or analytics');
  await close();
};

tests.legalSame = async () => {
  /* the website and the phone show one text: the same LEGAL_DOCS in index.html and app/planner.js */
  const dir = process.env.APP_DIR || nodePath.resolve(nodePath.dirname(new URL(import.meta.url).pathname), '..', 'out');
  const grab = f => { const s = nodeFs.readFileSync(nodePath.join(dir, f), 'utf8'); const i = s.indexOf("var LEGAL_UPDATED='"), j = s.indexOf('var LEGAL_DOCS=', i), k = s.indexOf('\n};', j) + 3;
    const box = {}; nodeVm.runInNewContext(s.slice(i, k) + ';this.out={u:LEGAL_UPDATED,p:LEGAL_UPDATED_PRIVACY,c:LEGAL_CONTACT,d:LEGAL_DOCS};', box); return JSON.stringify(box.out); };
  const a = grab('index.html'), b = grab('app/planner.js');
  ok(a === b && /4 October 2026/.test(a), 'legal: the website and the phone carry the same text', [a.length, b.length]);
};

tests.noWebFor = async () => {
  /* nothing points at the website for something the phone does */
  const dir = process.env.APP_DIR || nodePath.resolve(nodePath.dirname(new URL(import.meta.url).pathname), '..', 'out');
  const s = nodeFs.readFileSync(nodePath.join(dir, 'app/index.html'), 'utf8');
  const gone = ["classes on ${webLink('termchamp.com', '/')} and your week", "Add past classes on ${webLink", "Import your ${esc(CFG.TERM_LABEL)} schedule on ${webLink", 'Settings & full app on termchamp.com', 'The Planner on termchamp.com has them', 'in the Planner on termchamp.com for now', 'edit yours on termchamp.com', 'add them on termchamp.com'];
  const left = gone.filter(g => s.includes(g));
  ok(!left.length, 'cleanup: no screen sends you to termchamp.com for adding classes, past classes, the Planner, Settings or editing a review', left);
  const { page, close } = await openApp({ tables: Object.assign({}, FX.TABLES, { my_sections: [], saved_classes: [] }) });
  await page.waitForFunction(() => TC.ready, null, { timeout: 8000 });
  await click(page, '[data-a="tab"][data-x="schedule"]'); await click(page, '[data-a="schedTab"][data-x="mine"]');
  const t = await text(page);
  ok(/Find your classes in Explore and tap \+ to add them/.test(t) && !/termchamp\.com/.test(t), 'cleanup: an empty My Classes says to add classes from Explore', t.slice(0, 300));
  await close();
};

/* ---- Invites open the phone app (Tate, 2026-10-04) ---- */
tests.inviteToApp = async () => {
  const AVQ = FX.FRIENDS[0], SUG = FX.SUGGESTED, STR = FX.STRANGER;
  /* the link the phone shares */
  let o = await openApp({});
  await o.page.waitForFunction(() => TC.ready, null, { timeout: 8000 });
  ok(await o.page.evaluate(() => inviteUrl()) === 'https://termchamp.com/invite?add=' + FX.ME.id + '&to=app', 'invite: the phone’s link says to=app', await o.page.evaluate(() => inviteUrl()));
  await o.close();
  /* invite.html: to=app → the phone app; without it (on a computer) → the website */
  o = await openApp({ signedIn: false, path: '/invite.html?add=' + SUG.id + '&to=app' });
  ok(/\/app\/$/.test(new URL(o.page.url()).pathname) && await o.page.evaluate(() => !!localStorage.getItem('tc_pending_add')), 'invite: a to=app link lands in the phone app, with the invite kept', o.page.url());
  await o.close();
  o = await openApp({ signedIn: false, path: '/invite.html?add=' + SUG.id, wait: 800 });
  ok(new URL(o.page.url()).pathname === '/' && await o.page.evaluate(() => sessionStorage.getItem('professify_pending_add')) === FX.SUGGESTED.id, 'invite: an invite opened on a computer still goes to the website (which takes the invite)', o.page.url());
  await o.close();
  /* signed out: the landing says who invited you; the id leaves the address bar */
  o = await openApp({ signedIn: false, path: '/app/?add=' + AVQ.id, rpc: Object.assign({}, FX.RPC, { get_inviter: [{ display_name: 'Avery Quill' }] }) });
  await tick(o.page, 600);
  const land = await o.page.locator('body').innerText();
  ok(/Avery Quill invited you to TermChamp\. Sign up and you’ll be connected\./.test(land) && !/add=/.test(o.page.url()), 'invite: the landing says who invited you, and the id leaves the address bar', { url: o.page.url(), t: land.slice(0, 200) });
  await o.close();
  /* signed in: a request to whoever invited you */
  o = await openApp({ path: '/app/?add=' + SUG.id, rpc: Object.assign({}, FX.RPC, { get_inviter: [{ display_name: SUG.display_name }] }) });
  await o.page.waitForFunction(() => TC.ready, null, { timeout: 8000 }); await tick(o.page, 600);
  let fr = o.log.writes.filter(w => w.table === 'friend_requests' && w.m === 'POST');
  ok(fr.length === 1 && fr[0].body.to_user === SUG.id && fr[0].body.from_user === FX.ME.id && fr[0].body.status === 'pending' && /Friend request sent to Pat/.test(await o.page.locator('#toast').innerText()), 'invite: signed in, a friend request goes to whoever invited you', fr);
  ok(await o.page.evaluate(() => localStorage.getItem('tc_pending_add')) === null, 'invite: …once');
  await o.close();
  /* they already asked you: accepted, not a second request */
  o = await openApp({ path: '/app/?add=' + STR.id });
  await o.page.waitForFunction(() => TC.ready, null, { timeout: 8000 }); await tick(o.page, 800);
  fr = o.log.writes.filter(w => w.table === 'friend_requests');
  ok(fr.length === 1 && fr[0].m === 'PATCH' && fr[0].body.status === 'accepted', 'invite: if they’d already asked you, it’s accepted instead', fr);
  await o.close();
  /* already friends, or your own link: nothing */
  for (const id of [AVQ.id, FX.ME.id]) {
    o = await openApp({ path: '/app/?add=' + id });
    await o.page.waitForFunction(() => TC.ready, null, { timeout: 8000 }); await tick(o.page, 600);
    ok(!o.log.writes.some(w => w.table === 'friend_requests'), 'invite: ' + (id === FX.ME.id ? 'your own link' : 'a friend’s link') + ' sends nothing');
    await o.close();
  }
};

tests.desktopWidth = async () => {
  const { page, close, log } = await openApp({ width: 1280, height: 900 });
  ok(await page.locator('.side').isVisible() && /termchamp\.com\/app/.test(await page.locator('.side').innerText()), 'desktop: side panel says to open it on a phone');
  ok(/^\d{1,2}:\d{2}$/.test((await page.locator('#status > span:first-child').innerText()).trim()) && (await page.locator('#status > span:first-child').innerText()).trim() !== '9:41', 'desktop: frame status bar shows the real time', await page.locator('#status > span:first-child').innerText());
  ok(log.errors.length === 0, 'desktop: no page errors', log.errors);
  await close();
};

/* ============ Contact email: support@termchamp.com (Tate, 2026-10-04) ============ */
/* The only address the app shows is the legal pages' contact. It was Tate's personal iCloud address;
   it is now support@termchamp.com (an alias of tatesims@ on Spacemail). Checked on all four pages as
   the phone renders them, and in the desktop's own copy, which the phone's planner.js is lifted from. */
tests.supportEmail = async () => {
  const here = nodePath.dirname(new URL(import.meta.url).pathname);
  const appDir = process.env.APP_DIR || nodePath.resolve(here, '..', 'out');
  const pl = nodeFs.readFileSync(nodePath.join(appDir, 'app', 'planner.js'), 'utf8');
  const ph = nodeFs.readFileSync(nodePath.join(appDir, 'app', 'index.html'), 'utf8');
  const df = [nodePath.resolve(here, '..', 'out', 'index.html'), nodePath.resolve(here, '..', '..', 'index.html')].find(x => nodeFs.existsSync(x));
  const dk = nodeFs.readFileSync(df, 'utf8');
  ok(dk.includes("var LEGAL_CONTACT='support@termchamp.com';") && !/tdogtate@/.test(dk), 'support email: the desktop’s legal pages name support@termchamp.com, and the personal address is gone');
  ok(pl.includes("var LEGAL_CONTACT='support@termchamp.com';") && !/tdogtate@/.test(pl) && !/tdogtate@/.test(ph), 'support email: the phone’s legal pages name support@termchamp.com, and no personal address is left');
  ok(![dk, pl, ph].some(s => /email us\b/i.test(s)) && (dk.match(/email support@termchamp\.com and we’ll do it by hand/g) || []).length === 2, 'support email: nothing says “email us” without the address (under-13 line, the desktop’s Delete account fallbacks)');
  const { page, close, log } = await openApp({});
  await click(page, '.homehdr .me-btn'); await click(page, '[data-a="openSettings"]'); await tick(page, 500);
  for (const k of ['terms', 'privacy', 'security', 'guidelines']) {
    await click(page, `[data-a="openLegal"][data-x="${k}"]`); await tick(page, 1500);
    const t = await text(page);
    const mails = [...new Set(t.match(/[\w.+-]+@[\w-]+(?:\.[\w-]+)+/g) || [])];
    ok(t.length > 1000 && mails.length === 1 && mails[0] === 'support@termchamp.com', `support email: ${k} names support@termchamp.com and no other address`, mails);
    if (k === 'privacy') ok(/under 13 has an account, email support@termchamp\.com and it will be removed/.test(t), 'support email: the under-13 line gives the address', t.slice(t.indexOf('under 13'), t.indexOf('under 13') + 120));
    await click(page, '[data-a="back"]');
  }
  ok(log.errors.length === 0, 'support email: no page errors', log.errors);
  await close();
};

/* The first class of the day doesn't touch the top (Tate, 2026-10-05): every grid keeps 6px of air above
   its first hour and below its last, outside the hour scale, so blocks keep their size. */
tests.gridEdgeGap = async () => {
  const { page, close, log } = await openApp({});
  await tick(page, 500);
  const probe = await page.evaluate(() => {
    const run = (secs, o) => { const host = document.createElement('div'); host.className = 'homepg'; host.style.cssText = 'width:390px;position:absolute;top:0;left:0'; document.body.appendChild(host);
      host.innerHTML = grid(secs, o); const body = host.querySelector('.g-body').getBoundingClientRect();
      const bs = [...host.querySelectorAll('.g-b')].map(b => b.getBoundingClientRect());
      const labs = [...host.querySelectorAll('.g-lab span')].map(l => ({ t: l.innerText, top: l.getBoundingClientRect().top, mid: (l.getBoundingClientRect().top + l.getBoundingClientRect().bottom) / 2, bot: l.getBoundingClientRect().bottom }));
      const out = { H: body.height, top: Math.min(...bs.map(b => b.top)) - body.top, bottom: body.bottom - Math.max(...bs.map(b => b.bottom)), first: labs[0] && labs[0].top - body.top, last: labs.length && body.bottom - labs[labs.length - 1].bot, h: bs.map(b => Math.round(b.height)) };
      host.remove(); return out; };
    const mk = (i, s, e, d) => ({ id: 'eg' + i, code: 'ITP ' + (4400 + i), s, e, days: d, async: false });
    const secs = [mk(1, 480, 590, 'TR'), mk(2, 600, 710, 'M'), mk(3, 780, 890, 'M'), mk(4, 1080, 1200, 'M')];   /* 8:00 … 8:00p, both on the hour */
    return { fit: run(secs, { act: 'homeDay', key: 'eg', fit: 30, H: 300 }), sched: run(secs, { act: 'schedDay', faces: true }) };
  });
  for (const k of ['fit', 'sched']) {
    const p = probe[k];
    ok(Math.abs(p.top - 6) < 0.6 && Math.abs(p.bottom - 6) < 0.6, `edge gap (${k}): a class at 8:00 sits 6px under the top, and one ending at 8:00p 6px above the bottom — the same air both ends`, p);
    ok(Math.abs(p.first - 6) < 0.6 && Math.abs(p.last - 6) < 0.6, `edge gap (${k}): the first and last hour labels move with the classes they line up with`, p);
  }
  ok(probe.fit.H === 312 && probe.fit.h[0] === Math.round(110 * 300 / 720), 'edge gap: the air sits outside the hours, so blocks keep their size (300px of hours + 12px)', probe.fit);
  ok(log.errors.length === 0, 'edge gap: no page errors', log.errors);
  await close();
};

/* Dark mode (Tate, 2026-10-05, option A "Midnight navy"). Settings › Appearance: System / Light / Dark.
   CONTRAST_SCAN walks every visible text node, blends its colour over what is really behind it and
   returns the lines under 4.5:1 (3:1 when large). */
const CONTRAST_SCAN = (min = 4.5) => {
  const parse = c => { const m = c.match(/rgba?\(([^)]+)\)/); if (!m) return null; const p = m[1].split(/[ ,\/]+/).filter(Boolean).map(Number); return { r: p[0], g: p[1], b: p[2], a: p.length > 3 ? p[3] : 1 }; };
  const lum = ({ r, g, b }) => { const f = v => { v /= 255; return v <= .03928 ? v / 12.92 : Math.pow((v + .055) / 1.055, 2.4); }; return .2126 * f(r) + .7152 * f(g) + .0722 * f(b); };
  const mix = (top, bot) => ({ r: top.r * top.a + bot.r * (1 - top.a), g: top.g * top.a + bot.g * (1 - top.a), b: top.b * top.a + bot.b * (1 - top.a), a: 1 });
  const bgOf = el => { const layers = []; for (let e = el; e && e.nodeType === 1; e = e.parentElement) { const cs = getComputedStyle(e); if (cs.backgroundImage && cs.backgroundImage !== 'none' && !/radial-gradient\(var|radial/.test(cs.backgroundImage) && e.tagName !== 'BODY') return null; const c = parse(cs.backgroundColor); if (c && c.a > 0) { layers.push(c); if (c.a >= 1) break; } }
    let out = { r: 0, g: 0, b: 0, a: 1 }; const base = layers.length && layers[layers.length - 1].a >= 1 ? layers.pop() : { r: 255, g: 255, b: 255, a: 1 }; out = base; for (let i = layers.length - 1; i >= 0; i--) out = mix(layers[i], out); return out; };
  const bad = []; const seen = new Set();
  const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
  let n; while ((n = walker.nextNode())) { const t = n.textContent.trim(); if (!t) continue; const el = n.parentElement; if (!el || seen.has(el)) continue; seen.add(el);
    const r = el.getBoundingClientRect(); if (!r.width || !r.height || r.bottom < 0 || r.top > innerHeight) continue;
    const cs = getComputedStyle(el); if (cs.visibility === 'hidden' || +cs.opacity === 0) continue;
    let op = 1; for (let e = el; e; e = e.parentElement) op *= +getComputedStyle(e).opacity; if (op < .5) continue;
    const fg = parse(cs.color), bg = bgOf(el); if (!fg || !bg) continue;
    const f = fg.a < 1 ? mix(fg, bg) : fg; const L1 = lum(f), L2 = lum(bg); const cr = (Math.max(L1, L2) + .05) / (Math.min(L1, L2) + .05);
    const big = parseFloat(cs.fontSize) >= 24 || (parseFloat(cs.fontSize) >= 18.6 && +cs.fontWeight >= 700);
    if (cr < (big ? 3 : min)) bad.push({ t: t.slice(0, 40), cr: +cr.toFixed(2), fg: cs.color, bg: `rgb(${bg.r|0},${bg.g|0},${bg.b|0})`, cls: (el.className && el.className.baseVal === undefined ? el.className : '') + ' < ' + (el.parentElement && el.parentElement.className || '') });
  }
  return bad;
};
const darkOf = p => p.evaluate(() => document.documentElement.getAttribute('data-theme'));
const bgOfPhone = p => p.evaluate(() => getComputedStyle(document.querySelector('.phone')).backgroundColor);
const DARK_SCREENS = [['home', "go('home')"], ['prof', "go('profDetail', { id: Object.keys(PROFS).find(k => ratingOf(k) != null && ratingOf(k) > 4) })"], ['class', "go('classDetail', { code: 'BUS 3431' })"],
  ['explore', "go('explore')"], ['rate', "go('rate')"], ['schedule', "go('schedule'); S.schedTab = 'mine'"], ['plans', "S.schedTab = 'plans'"], ['planner', "S.schedTab = 'planner'"], ['past', "S.schedTab = 'past'"],
  ['friends', "go('friends')"], ['friend', "go('friend', { id: TC.friends[0] })"], ['me', "go('me')"], ['settings', "go('settings')"]];
const darkScan = async (page, screens) => {
  const white = {}, low = {};
  for (const [n, js] of screens) {
    for (const top of [0, 650]) {
      await page.evaluate(([js, top]) => { if (!top) { (0, eval)(js); render(true); } document.getElementById('scroll').scrollTop = top; }, [js, top]); await tick(page, 500);
      const w = await page.evaluate(() => [...document.querySelectorAll('#scroll *, #chrome *')].filter(e => { const r = e.getBoundingClientRect(); if (!r.width || r.height < 8 || r.bottom < 0 || r.top > innerHeight) return false;
        const b = getComputedStyle(e).backgroundColor; const m = b.match(/rgba?\(([\d.]+), ([\d.]+), ([\d.]+)(?:, ([\d.]+))?\)/); return m && +m[1] > 225 && +m[2] > 225 && +m[3] > 225 && (m[4] === undefined || +m[4] >= .5) && !e.closest('.hero'); })
        .map(e => (e.className && e.className.baseVal === undefined ? e.className : e.tagName) + ' ' + (e.innerText || '').slice(0, 20)));
      if (w.length) white[n + '@' + top] = w.slice(0, 4);
      const c = await page.evaluate(scan => (new Function('return ' + scan))()(4.5).filter(x => !/\bstat\b/.test(x.cls)), CONTRAST_SCAN.toString());
      if (c.length) low[n + '@' + top] = c.slice(0, 4);
    }
  }
  return { white, low };
};
tests.darkMode = async () => {
  /* the theme is on <html> before the app runs, so a dark phone never paints white first */
  const { page, close, log } = await openApp({ init: () => { try { localStorage.setItem('tc-theme', 'dark'); } catch (e) {} document.addEventListener('DOMContentLoaded', () => { window.__firstTheme = document.documentElement.getAttribute('data-theme'); }, { once: true }); } });
  await tick(page, 600);
  ok(await page.evaluate(() => window.__firstTheme) === 'dark', 'dark: the saved theme is set before the page paints', await page.evaluate(() => window.__firstTheme));
  ok(await bgOfPhone(page) === 'rgb(10, 15, 28)', 'dark: the page is midnight navy #0A0F1C', await bgOfPhone(page));
  ok(await page.evaluate(() => getComputedStyle(document.querySelector('.fcard')).backgroundColor) === 'rgb(20, 27, 43)', 'dark: cards are #141B2B');
  ok(await page.evaluate(() => [...document.querySelectorAll('meta[name=theme-color]')].map(m => m.content).join()) === '#0A0F1C,#0A0F1C', 'dark: the browser bar colour follows (#0A0F1C)');
  ok(await page.evaluate(() => getComputedStyle(document.querySelector('.tabbar')).backgroundColor) === 'rgba(20, 27, 43, 0.94)', 'dark: the tab bar is dark glass');
  const { white, low } = await darkScan(page, DARK_SCREENS);
  ok(!Object.keys(white).length, 'dark: no white or near-white surface left on any main screen (the coloured headers excepted)', white);
  ok(!Object.keys(low).length, 'dark: every line of text is 4.5:1 (3:1 when large) on what is behind it, on every main screen', low);
  /* the sheets: only what is on the sheet counts (the page behind sits under the scrim) */
  const sheets = [['notifs', "go('home'); UI.sheet = { type: 'notifs' }"], ['story', "UI.sheet = { type: 'story', id: TC.friends[0] }"], ['newGroup', "UI.sheet = { type: 'newGroup' }"], ['invite', "UI.sheet = { type: 'invite' }"],
    ['filters', "go('explore'); UI.sheet = { type: 'filters' }"], ['champ', "UI.sheet = null; go('home'); UI.champ = true"]];
  const sw = {}, sl = {};
  for (const [n, js] of sheets) {
    await page.evaluate(js => { (0, eval)(js); render(true); }, js); await tick(page, 600);
    const root = await page.evaluate(() => document.querySelector('#sheet .sheet, #sheet > *, .champbox, #champ') ? 1 : 0);
    const w = await page.evaluate(() => [...document.querySelectorAll('#sheet *, .champ *, #champ *')].filter(e => { const r = e.getBoundingClientRect(); if (!r.width || r.height < 8) return false; const b = getComputedStyle(e).backgroundColor; const m = b.match(/rgba?\(([\d.]+), ([\d.]+), ([\d.]+)(?:, ([\d.]+))?\)/); return m && +m[1] > 225 && +m[2] > 225 && +m[3] > 225 && (m[4] === undefined || +m[4] >= .5) && !e.closest('canvas, .qr, [class*="qr"]'); }).map(e => e.className + ' ' + (e.innerText || '').slice(0, 16)));
    if (w.length) sw[n] = w.slice(0, 4);
    const c = await page.evaluate(scan => (new Function('return ' + scan))()(4.5).filter(x => { return true; }), CONTRAST_SCAN.toString());
    const inSheet = await page.evaluate(list => list.filter(x => [...document.querySelectorAll('#sheet *, .champ *, #champ *')].some(e => e.firstChild && e.textContent.trim().startsWith(x.t) && e.children.length === 0)), c);
    if (inSheet.length) sl[n] = inSheet.slice(0, 4);
    ok(root, `dark: the ${n} sheet opened`);
  }
  await page.evaluate(() => { UI.champ = false; UI.sheet = null; render(true); });
  ok(!Object.keys(sw).length, 'dark: no white surface on the sheets (the invite QR excepted)', sw);
  ok(!Object.keys(sl).length, 'dark: every line of text on the sheets is 4.5:1', sl);
  /* share pictures are other people's to look at: drawn exactly as in light */
  const pics = await page.evaluate(() => { const pk = Object.keys(PROFS).find(k => ratingOf(k) != null), un = Object.keys(PROFS).find(k => ratingOf(k) == null);
    const draw = () => [cardShCanvas('prof', pk).toDataURL(), un ? cardShCanvas('prof', un).toDataURL() : '', cardShCanvas('class', 'BUS 3431').toDataURL()];
    const d = draw(); document.documentElement.setAttribute('data-theme', 'light'); const l = draw(); document.documentElement.setAttribute('data-theme', 'dark');
    return { same: d.map((x, i) => x === l[i]), un: !!un, dark: isDark() }; });
  ok(pics.same.every(Boolean) && pics.un && pics.dark, 'dark: share pictures (rated and unrated professor, class) are drawn exactly as in light', pics);
  /* numbers in rating colours get lighter so they read; chips get a dark tint */
  const rd = await page.evaluate(() => [RATE_DARK(10), RATE_PALE(10), NOPHOTO, getComputedStyle(document.documentElement).getPropertyValue('--nophoto').trim()]);
  ok(rd[0] === 'hsl(140 75% 58%)' && rd[1] === 'hsl(140 45% 17%)' && rd[2] === 'var(--nophoto)' && rd[3] === '#3A4459', 'dark: rating numbers lighten, ★ chips go dark, the no-photo circle goes dark grey', rd);
  ok(log.errors.length === 0, 'dark: no page errors', log.errors);
  await close();
};
tests.darkLightSame = async () => {
  /* light mode must be what it was: the same scan in light finds no more than build 20:00 had (the hero tiles) */
  const { page, close } = await openApp({});
  ok(await darkOf(page) === 'light' && await bgOfPhone(page) === 'rgb(231, 236, 245)' /* Home's deeper light page since 01:15 */, 'light: a light phone gets today’s light app', [await darkOf(page), await bgOfPhone(page)]);
  ok(await page.evaluate(() => [RATE_DARK(10), RATE_PALE(10), getComputedStyle(document.documentElement).getPropertyValue('--nophoto').trim(), getComputedStyle(document.querySelector('.fcard')).backgroundColor, getComputedStyle(document.querySelector('.tabbar')).backgroundColor, getComputedStyle(document.querySelector('.tab.on')).color].join('|'))
    === '#166534|#DCFCE7|#DADDE3|rgb(255, 255, 255)|rgba(255, 255, 255, 0.96)|rgb(29, 78, 216)', 'light: rating inks, no-photo grey, white cards, the tab bar and its blue are unchanged');
  const tok = await page.evaluate(() => { const cs = getComputedStyle(document.documentElement); return ['--card', '--bg', '--line2', '--red-ink', '--purple-wash', '--track', '--glass'].map(k => cs.getPropertyValue(k).trim()).join('|'); });
  ok(tok === '#fff|#F4F6FB|#CBD5E1|#B91C1C|#F6F2FF|#EEF2F8|rgba(244,246,251,.96)', 'light: every new token holds the colour it replaced', tok);
  ok(await page.evaluate(() => getComputedStyle(document.querySelector('.who') || document.querySelector('.fhandle') || document.body).getPropertyValue('--blue-t')) === '', 'light: the accent text tokens are dark-only (light text uses the accent itself)');
  await close();
};
tests.darkSetting = async () => {
  const { page, close, log } = await openApp({});
  /* System follows the phone, live */
  await page.emulateMedia({ colorScheme: 'dark' }); await tick(page, 400);
  ok(await darkOf(page) === 'dark' && await bgOfPhone(page) === 'rgb(10, 15, 28)', 'appearance: System switches to dark the moment the phone does', [await darkOf(page), await bgOfPhone(page)]);
  const flip = await page.evaluate(() => { const st = [...document.querySelectorAll('.fcard .b, .fcard div')].find(e => /^● In /.test(e.textContent.trim()) && e.children.length === 0);
    return { st: st && getComputedStyle(st).color, meta: [...document.querySelectorAll('meta[name=theme-color]')].map(m => m.content).join() }; });
  ok(flip.st === 'rgb(110, 162, 255)' && flip.meta === '#0A0F1C,#0A0F1C', 'appearance: the screen is redrawn with dark-mode colours (status line light blue) and the browser bar follows', flip);
  await page.emulateMedia({ colorScheme: 'light' }); await tick(page, 400);
  ok(await darkOf(page) === 'light', 'appearance: and back to light');
  await page.emulateMedia({ colorScheme: 'dark' }); await tick(page, 300);
  /* Settings › Appearance */
  await page.evaluate(() => { go('settings'); render(true); }); await tick(page, 400);
  const radios = await page.evaluate(() => [...document.querySelectorAll('.thm [role=radio]')].map(b => b.innerText.trim() + ':' + b.getAttribute('aria-checked')));
  ok(radios.join() === 'System:true,Light:false,Dark:false', 'appearance: Settings has System / Light / Dark, System ticked', radios);
  await click(page, '[data-a="setTheme"][data-x="light"]');
  ok(await darkOf(page) === 'light' && await page.evaluate(() => localStorage.getItem('tc-theme')) === 'light', 'appearance: Light pins light on a dark phone and is kept', await page.evaluate(() => localStorage.getItem('tc-theme')));
  ok(await page.evaluate(() => document.activeElement && document.activeElement.dataset.x) === 'light' && await page.evaluate(() => document.querySelector('[data-x="light"]').getAttribute('aria-checked')) === 'true', 'appearance: focus stays on the picked option and it reads as checked');
  await page.emulateMedia({ colorScheme: 'light' }); await page.emulateMedia({ colorScheme: 'dark' }); await tick(page, 300);
  ok(await darkOf(page) === 'light', 'appearance: a pinned theme ignores the phone changing');
  await click(page, '[data-a="setTheme"][data-x="dark"]');
  ok(await darkOf(page) === 'dark' && await page.evaluate(() => localStorage.getItem('tc-theme')) === 'dark', 'appearance: Dark pins dark');
  await page.emulateMedia({ colorScheme: 'light' }); await tick(page, 300);
  ok(await darkOf(page) === 'dark', 'appearance: Dark stays dark on a light phone');
  await click(page, '[data-a="setTheme"][data-x="system"]');
  ok(await darkOf(page) === 'light' && await page.evaluate(() => localStorage.getItem('tc-theme')) === null, 'appearance: System forgets the pin and follows the phone again');
  ok(log.errors.length === 0, 'appearance: no page errors', log.errors);
  await close();
};
tests.darkOnboarding = async () => {
  /* sign-up and onboarding keep their light design in dark mode: every line of text has the same colour on
     the same background as on a light phone, and the strip and browser bar above them are light */
  const T = Object.assign({}, FX.TABLES, { profiles: FX.TABLES.profiles.filter(p => p.id !== FX.ME.id) });
  const look = async theme => {
    const out = {}; const init = theme === 'dark' ? () => { try { localStorage.setItem('tc-theme', 'dark'); } catch (e) {} } : null;
    const snap = p => p.evaluate(() => { const bg = e => { for (; e; e = e.parentElement) { const b = getComputedStyle(e).backgroundColor; if (!/rgba\(0, 0, 0, 0\)|transparent/.test(b)) return b; } return ''; };
      const w = document.createTreeWalker(document.getElementById('scroll'), NodeFilter.SHOW_TEXT), r = []; let n; while ((n = w.nextNode())) { const t = n.textContent.trim(); if (!t || !n.parentElement.getClientRects().length) continue; r.push(t.slice(0, 30) + ' ' + getComputedStyle(n.parentElement).color + ' on ' + bg(n.parentElement)); }
      return { r, body: getComputedStyle(document.body).backgroundColor, status: getComputedStyle(document.querySelector('.status')).backgroundColor, phone: getComputedStyle(document.querySelector('.phone')).backgroundColor, meta: [...document.querySelectorAll('meta[name=theme-color]')].map(m => m.content).join() }; });
    { const { page, close } = await openApp({ signedIn: false, init }); await tick(page, 600);
      out.landing = await snap(page); await click(page, '[data-a="siMode"][data-x="signup"]'); out.signup = await snap(page);
      out.theme = await darkOf(page); await close(); }
    { const { page, close } = await openApp({ tables: T, init }); for (let i = 0; i < 10 && !/claim your username/.test(await text(page)); i++) await tick(page, 500);
      out.setup = await snap(page); await close(); }
    return out;
  };
  const L = await look('light'), D = await look('dark');
  ok(D.theme === 'dark', 'dark onboarding: the phone really is in dark mode', D.theme);
  for (const k of ['landing', 'signup', 'setup']) {
    const diff = D[k].r.filter((x, i) => x !== L[k].r[i]);
    ok(D[k].r.length > 3 && D[k].r.length === L[k].r.length && !diff.length, `dark onboarding: ${k} looks exactly as it does in light`, diff.slice(0, 4));
    ok(D[k].status === 'rgb(244, 246, 251)' && D[k].phone === 'rgb(244, 246, 251)' && D[k].meta === '#F4F6FB,#F4F6FB', `dark onboarding: ${k} — the strip and the browser bar above it are light`, [D[k].status, D[k].phone, D[k].meta]);
    ok(D[k].body === 'rgb(244, 246, 251)', `dark onboarding: ${k} — on a phone the page behind the clock is light too (Safari paints the strip from it)`, D[k].body);
  }
};

const names = Object.keys(tests).filter(n => !only || n === only);
for (const n of names) {
  if (!quiet) console.log('#', n);
  try { await tests[n](); } catch (e) { fail++; fails.push(n + ' threw'); console.log('  FAIL', n, 'threw', e.message.split('\n').slice(0, 4).join(' | ')); }
}
console.log(`\ncheck-app: ${pass} passed, ${fail} failed`);
if (fail) { console.log('failed:', fails.join(' | ')); process.exit(1); }
