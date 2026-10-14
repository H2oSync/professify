/* check-desktop-parity2 — the website matches the phone in Friends, Plans and Schedule's tabs
   (website-friends-plans-tabs, 2026-10-14). Real index.html in Chromium, signed in, PostgREST stand-in.
   Run: APP_DIR=<repo> node check-desktop-parity2.mjs [--only name] [--quiet]   (SHOTS=<dir> also writes screenshots)
   The promises: Friends is pink (Invite pill #DB2777 + white, Accept pink, "New group" text and search icon pink,
   the request card ringed pink, the unread dot pink) with every pink text >= 4.5:1 in light and dark; Plans A/B/C
   are teal / orange / rose (the chosen pill filled, white text >= 4.5:1; the Plans card and the Builder's Filling pills
   follow); Schedule's rail reads My classes / Plans / Builder / Past classes, the title says "Builder . Spring 2027",
   Past classes is a real rail item that lands on the record, and Hawk's setSchedTab('plan'|'past'|'watch'|'mine') still land. */
import { openApp } from './app-harness.mjs';
import * as FX from './app-fixtures.mjs';

const args = process.argv.slice(2);
const ONLY = args.includes('--only') ? args[args.indexOf('--only') + 1] : null;
const QUIET = args.includes('--quiet');
const SHOTS = process.env.SHOTS || '';
let pass = 0, fail = 0; const fails = [];
function ok(c, name, info) {
  if (c) { pass++; if (!QUIET) console.log('  ok  ', name); }
  else { fail++; fails.push(name); console.log('  FAIL', name, info !== undefined ? '→ ' + JSON.stringify(info).slice(0, 600) : ''); }
}
const tick = async (p, ms = 400) => { await p.clock.runFor(ms); await p.waitForTimeout(250); };
const NOW = '2026-10-14T10:30:00-07:00';
const T = {}; const test = (n, fn) => { T[n] = fn; };
const desk = (o = {}) => openApp(Object.assign({ path: '/', width: 1440, height: 900, wait: 4000, terms: 'live', time: NOW }, o));
const theme = (page, t) => page.evaluate(t => { try { setTheme(t); } catch (e) {} document.documentElement.setAttribute('data-theme', t); }, t);
const shot = async (page, name) => { if (SHOTS) await page.screenshot({ path: `${SHOTS}/${name}.png` }); };

/* the contrast of an element's text on its effective background (in the page) */
const CR = `(el) => {
  const p = (c) => { const m = c.match(/[\\d.]+/g).map(Number); return { r: m[0], g: m[1], b: m[2], a: m[3] === undefined ? 1 : m[3] }; };
  const lum = (c) => { const f = (v) => { v /= 255; return v <= .03928 ? v / 12.92 : Math.pow((v + .055) / 1.055, 2.4); }; return .2126 * f(c.r) + .7152 * f(c.g) + .0722 * f(c.b); };
  let n = el, stack = [];
  while (n) { const c = p(getComputedStyle(n).backgroundColor); if (c.a > 0) stack.push(c); if (c.a === 1) break; n = n.parentElement; }
  let base = stack.length && stack[stack.length - 1].a === 1 ? stack.pop() : { r: 18, g: 18, b: 18, a: 1 };
  while (stack.length) { const c = stack.pop(); base = { r: c.r * c.a + base.r * (1 - c.a), g: c.g * c.a + base.g * (1 - c.a), b: c.b * c.a + base.b * (1 - c.a), a: 1 }; }
  const fg = p(getComputedStyle(el).color); const L1 = lum(fg), L2 = lum(base);
  return Math.round(((Math.max(L1, L2) + .05) / (Math.min(L1, L2) + .05)) * 100) / 100;
}`;
const rgb = (page, sel, prop = 'backgroundColor') => page.evaluate(([s, p]) => { const e = document.querySelector(s); return e ? getComputedStyle(e)[p] : null; }, [sel, prop]);
const cr = (page, sel) => page.evaluate(([s, f]) => { const e = document.querySelector(s); return e ? eval('(' + f + ')')(e) : null; }, [sel, CR]);

test('friends', async () => {
  const { page, close, log } = await desk({ tables: FX.TABLES }); await tick(page, 1500);
  await page.evaluate(() => { show('friends'); loadFriendsData(); }); await tick(page, 1800);
  await page.evaluate(() => { try { renderFriends(); } catch (e) {} }); await tick(page, 600);
  for (const th of ['light', 'dark']) {
    await theme(page, th); await tick(page, 300);
    const T2 = th + ': ';
    ok(await rgb(page, '#view-friends .frv2-invite') === 'rgb(219, 39, 119)', T2 + 'the Invite pill is #DB2777', await rgb(page, '#view-friends .frv2-invite'));
    ok(await rgb(page, '#view-friends .frv2-invite', 'color') === 'rgb(255, 255, 255)' && (await cr(page, '#view-friends .frv2-invite')) >= 4.5, T2 + 'Invite is white on pink, >= 4.5:1', await cr(page, '#view-friends .frv2-invite'));
    const have = await page.evaluate(() => ({ req: !!document.querySelector('#view-friends .frv2-card.fr-pending .frv2-go'), ng: !!document.querySelector('#view-friends .fr-secl[onclick^="msgNewConv"]'), ico: !!document.querySelector('#view-friends .frv2-findico') }));
    ok(have.req && have.ng && have.ico, T2 + 'the fixture draws a friend request, "New group" and the search icon', have);
    const accept = await rgb(page, '#view-friends .frv2-card.fr-pending .frv2-go');
    ok(accept === 'rgb(219, 39, 119)' && (await cr(page, '#view-friends .frv2-card.fr-pending .frv2-go')) >= 4.5, T2 + 'Accept is pink with white text >= 4.5:1', accept);
    const ring = await rgb(page, '#view-friends .frv2-card.fr-pending', 'boxShadow');
    ok(/\b(251, 207, 232|244, 114, 182)\b/.test(ring || ''), T2 + 'the request card has the pink ring', ring);
    const want = th === 'light' ? 'rgb(204, 31, 108)' : 'rgb(244, 114, 182)';
    const ng = '#view-friends .fr-secl[onclick^="msgNewConv"]';
    ok(await rgb(page, ng, 'color') === want && (await cr(page, ng)) >= 4.5, T2 + '"New group" is pink text >= 4.5:1', [await rgb(page, ng, 'color'), await cr(page, ng)]);
    ok(await rgb(page, '#view-friends .frv2-findico', 'color') === want, T2 + 'the search icon is pink', await rgb(page, '#view-friends .frv2-findico', 'color'));
    const eb = '#view-friends .frv2-card.fr-pending .frv2-eyebrow';
    ok(await rgb(page, eb, 'color') === want && (await cr(page, eb)) >= 4.5, T2 + 'the request eyebrow is pink text >= 4.5:1', await cr(page, eb));
    const dot = await page.evaluate(() => { const d = document.querySelector('#view-friends .msg-tdot'); return d ? getComputedStyle(d).backgroundColor : 'none'; });
    ok(dot === 'rgb(219, 39, 119)', T2 + 'the unread dot is pink', dot);
    await shot(page, `friends-${th}-1440`);
  }
  ok(await page.evaluate(() => /shareInviteLink/.test(document.getElementById('frInviteBtn').getAttribute('onclick'))), 'the Invite button still shares the link');
  ok(log.errors.length === 0, 'friends: no page errors', log.errors); await close();
});

const PLAN = { A: ['rgb(15, 118, 110)', '#0F766E'], B: ['rgb(194, 65, 12)', '#C2410C'], C: ['rgb(190, 24, 93)', '#BE185D'] };
test('plans', async () => {
  const { page, close, log } = await desk({ tables: FX.TABLES }); await tick(page, 1500);
  await page.evaluate(() => { show('sched'); setSchedTab('watch'); }); await tick(page, 1200);
  for (const th of ['light', 'dark']) {
    await theme(page, th); await tick(page, 300);
    for (const s of ['A', 'B', 'C']) {
      await page.evaluate(s => document.querySelector(`#plansOut .pl3-pill[data-slot="${s}"]`).click(), s); await tick(page, 500);
      const on = '#plansOut .pl3-pill.on';
      const bg = await rgb(page, on);
      ok(bg === PLAN[s][0], `${th}: Plan ${s}'s chosen pill is ${PLAN[s][1]}`, bg);
      ok((await cr(page, on + ' b')) >= 4.5 && (await cr(page, on + ' span')) >= 4.5, `${th}: Plan ${s}'s chosen pill reads >= 4.5:1`, [await cr(page, on + ' b'), await cr(page, on + ' span')]);
      ok(await page.evaluate(s => !!document.querySelector(`#plansOut .pl3.tcpl-${s}`), s), `${th}: the Plans tab carries Plan ${s}'s colour`);
      const off = await page.evaluate(() => { const o = getComputedStyle(document.querySelector('#plansOut .pl3-pill.on')).backgroundColor; return [...document.querySelectorAll('#plansOut .pl3-pill:not(.on)')].every(b => getComputedStyle(b).backgroundColor !== o); });
      ok(off, `${th}: the other two pills stay neutral`);
    }
    await page.evaluate(() => document.querySelector('#plansOut .pl3-pill[data-slot="B"]').click()); await tick(page, 500);
    const dots = await page.evaluate(() => [...document.querySelectorAll('#plansOut .pl3-pill b')].map(b => getComputedStyle(b, '::before').backgroundColor));
    ok(dots.length === 3 && dots[0] !== dots[1] && dots[1] !== dots[2] && dots[0] !== dots[2], `${th}: the three pills carry three different plan colours`, dots);
    await shot(page, `plans-${th}-1440`);
  }
  ok(log.errors.length === 0, 'plans: no page errors', log.errors); await close();
});

test('builder-pills', async () => {
  const { page, close, log } = await desk({ tables: FX.TABLES }); await tick(page, 1500);
  await page.evaluate(() => { show('sched'); setSchedTab('plan'); }); await tick(page, 1800);
  for (const th of ['light', 'dark']) {
    await theme(page, th); await tick(page, 300);
    for (const s of ['A', 'B', 'C']) {
      const clicked = await page.evaluate(s => { const b = [...document.querySelectorAll('#plBuilderOut .bd-slot')].find(x => x.textContent.startsWith('Plan ' + s)); if (b) b.click(); return !!b; }, s); await tick(page, 500);
      const bg = await rgb(page, '#plBuilderOut .bd-slot.on');
      ok(clicked && bg === PLAN[s][0], `${th}: the Builder's Filling pill for Plan ${s} is ${PLAN[s][1]}`, bg);
      ok((await cr(page, '#plBuilderOut .bd-slot.on')) >= 4.5, `${th}: it reads >= 4.5:1`, await cr(page, '#plBuilderOut .bd-slot.on'));
    }
    await shot(page, `builder-${th}-1440`);
  }
  ok(log.errors.length === 0, 'builder: no page errors', log.errors); await close();
});

test('tabs', async () => {
  const { page, close, log } = await desk({ tables: FX.TABLES }); await tick(page, 1500);
  await page.evaluate(() => { show('sched'); setSchedTab('mine'); }); await tick(page, 800);
  const rail = await page.evaluate(() => [...document.querySelectorAll('#view-sched .wl-tabs .wl-tab')].map(b => b.textContent.replace(/\s*\d+$/, '').trim()));
  ok(rail.join('|') === 'My classes|Plans|Builder|Past classes', 'the rail reads My classes / Plans / Builder / Past classes', rail);
  const lit = () => page.evaluate(() => ({ on: [...document.querySelectorAll('#view-sched .wl-tabs .wl-tab.on')].map(b => b.id), h: document.querySelector('#schedHero h2').textContent, plan: document.getElementById('schedPlanWrap').style.display !== 'none', mine: document.getElementById('schedMineWrap').style.display !== 'none', watch: document.getElementById('schedWatchWrap').style.display !== 'none' }));
  let r = await lit(); ok(r.on.join() === 'stab-mine' && /^My classes/.test(r.h), 'My classes lit, titled My classes', r);
  await page.evaluate(() => setSchedTab('watch')); await tick(page, 500); r = await lit();
  ok(r.on.join() === 'stab-watch' && /^Plans/.test(r.h) && r.watch && !r.plan, 'setSchedTab(watch) lights Plans', r);
  await page.click('#stab-plan'); await tick(page, 900); r = await lit();
  ok(r.on.join() === 'stab-plan' && r.plan && !r.mine && !r.watch, 'the Builder item lights alone and shows the Builder pane', r);
  ok(/^Builder/.test(r.h) && /Spring 2027/.test(r.h) && !/Planner|Planning/i.test(r.h), 'the title reads "Builder · Spring 2027" — no "Planner", no "Planning"', r.h);
  await shot(page, 'tabs-builder-1440');
  await page.click('#stab-past'); await tick(page, 1200); r = await lit();
  ok(r.on.join() === 'stab-past' && r.plan && /^Past classes$/.test(r.h.trim()), 'the Past classes item lights alone, lands on the record, titled Past classes', r);
  const rec = await page.evaluate(() => { const e = document.getElementById('plRecord'); const b = e && e.getBoundingClientRect(); return { here: !!e && !!(e.offsetParent), top: b ? Math.round(b.top) : null, vh: innerHeight, closed: document.getElementById('schedPlanWrap').classList.contains('pl3-deg-closed') }; });
  ok(rec.here && rec.top < rec.vh && !rec.closed, 'the record is open and in view', rec);
  const org = await page.evaluate(() => [cpCaptureOrigin(), pfCaptureOrigin()].map(o => o.tab + ':' + o.label));
  ok(org.every(o => o === 'past:Past Classes'), 'opening a class or professor from Past classes remembers Past classes (Back returns there)', org);
  await page.evaluate(() => setSchedTab('plan')); await tick(page, 600); r = await lit();
  ok(r.on.join() === 'stab-plan' && /^Builder/.test(r.h), 'going back to the Builder un-lights Past classes and restores the title', r);
  const org2 = await page.evaluate(() => [cpCaptureOrigin(), pfCaptureOrigin()].map(o => o.tab + ':' + o.label));
  ok(org2.every(o => o === 'plan:Builder'), 'from the Builder, Back returns to the Builder', org2);
  /* the eligible list redraws the title's term when the report/major arrives; it must not bring back "planning" */
  await page.evaluate(() => { try { student.major = 'Business Administration'; student.standing = 'Junior'; schSyncToStudent(); } catch (e) {} try { plRenderEligible(); } catch (e) {} }); await tick(page, 400);
  const ttl = await page.evaluate(() => document.querySelector('#schedHero h2').textContent.replace(/\s+/g, ' ').trim());
  ok(/^Builder/.test(ttl) && !/planning/i.test(ttl), 'the title stays "Builder · term" after the list redraws', ttl);
  /* Hawk's go_to places call setSchedTab('plan') and ('past'); the Builder's own link is unchanged */
  await page.evaluate(() => { show('home'); show('sched'); setSchedTab('past'); }); await tick(page, 900); r = await lit();
  ok(r.on.join() === 'stab-past' && r.plan, "Hawk's setSchedTab('past') still lands on Past classes", r);
  const link = await page.evaluate(() => { setSchedTab('plan'); const b = document.querySelector('#plBuilderOut .bd-past'); return b ? b.textContent : null; }); await tick(page, 600);
  ok(/Past classes/.test(link || ''), 'the Builder still has its Past classes link', link);
  const where = await page.evaluate(() => [...document.querySelectorAll('#view-sched *')].filter(e => e.children.length === 0 && /Planner/.test(e.textContent)).map(e => e.className + ':' + e.textContent.slice(0, 60)));
  ok(where.length === 0, 'no visible "Planner" left on Schedule', where);
  for (const th of ['light', 'dark']) { await theme(page, th); await tick(page, 300); await shot(page, `tabs-${th}-1440`); }
  ok(log.errors.length === 0, 'tabs: no page errors', log.errors); await close();
});

test('phone', async () => {
  const { page, close, log } = await desk({ tables: FX.TABLES, width: 390, height: 844 }); await tick(page, 1500);
  for (const th of ['light', 'dark']) {
    await theme(page, th);
    await page.evaluate(() => { show('friends'); loadFriendsData(); }); await tick(page, 1600); await shot(page, `friends-${th}-390`);
    await page.evaluate(() => { show('sched'); setSchedTab('watch'); }); await tick(page, 900); await shot(page, `plans-${th}-390`);
    await page.evaluate(() => { setSchedTab('plan'); }); await tick(page, 1200); await shot(page, `builder-${th}-390`);
    ok(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1), `${th}: no sideways scroll at 390`);
  }
  ok(log.errors.length === 0, 'phone width: no page errors', log.errors); await close();
});

const names = ONLY ? [ONLY] : Object.keys(T);
for (const n of names) {
  if (!T[n]) { console.log('no such test', n); process.exit(2); }
  if (!QUIET) console.log('\n' + n);
  try { await T[n](); } catch (e) { fail++; fails.push(n + ' threw'); console.log('  FAIL', n, 'threw', String(e).slice(0, 300)); }
}
console.log(`\ncheck-desktop-parity2: ${pass} passed, ${fail} failed`);
if (fail) { console.log('failed:', fails.join(' | ')); process.exit(1); }
