/* Drives Plans A–C, the registration game plan and backups inside the REAL index.html.
   Usage: (cd <build dir> && node /home/claude/assistant/check-plans.mjs)
   The seat feed and the network are blocked, so a fixture term is installed in their place — the
   app's own clsSections, parseMeet, meetsOverlap, secSeat, wcWatchSec and enroll dialog still do
   all the work. A plan asserted only in source is a plan nobody has ever made. */
import { chromium } from 'playwright';
import http from 'node:http'; import fs from 'node:fs'; import path from 'node:path';
const T = { '.html': 'text/html', '.js': 'text/javascript', '.css': 'text/css' };
const PORT = 8131;
const srv = http.createServer((q, r) => {
  const u = q.url.split('?')[0]; const f = path.join(process.cwd(), u === '/' ? 'index.html' : u);
  if (!f.startsWith(process.cwd()) || !fs.existsSync(f) || fs.statSync(f).isDirectory()) { r.writeHead(404); return r.end(); }
  r.writeHead(200, { 'content-type': T[path.extname(f)] || 'application/octet-stream' }); fs.createReadStream(f).pipe(r);
});
await new Promise((r) => srv.listen(PORT, r));
const b = await chromium.launch({ executablePath: process.env.PW_CHROME || '/opt/pw-browsers/chromium-1194/chrome-linux/chrome' });
const results = []; const ok = (n, c, d = '') => results.push({ n, c: !!c, d });

/* The fixture term. Class numbers and codes are invented; the shapes are the live feed's. */
const FIXTURE = `(() => {
  /* Synthetic professors only — never a real person's name against a made-up rating. */
  PROFESSORS['tst-hi'] = { name: 'Ada Hilltop', rating: 3.8, dept: 'TEST' };
  PROFESSORS['tst-mid'] = { name: 'Ben Midway', rating: 3.0, dept: 'TEST' };
  PROFESSORS['tst-lo'] = { name: 'Cy Lowland', rating: 2.2, dept: 'TEST' };
  try { _profByName = null; } catch (e) {}
  const HI = 'Ada Hilltop', MID = 'Ben Midway', LO = 'Cy Lowland';
  const row = (nbr, sec, instr, days, cap, avail, extra) => Object.assign({ class_nbr: nbr, section: sec, instructor: instr, days: days,
    status: avail > 0 ? 'Open' : 'Closed', capacity: cap, enrolled: cap - avail, available: avail, waitlist_total: 0, waitlist_capacity: 20, course_code: '' }, extra || {});
  window.SEAT_SECTIONS = {
    'BUS 4442': [ row('11111', 'S01-LEC Regular', MID, 'MoWe 10:10AM - 11:00AM', 40, 12) ],
    'ECON 2001': [ row('22221', 'S01-LEC Regular', HI, 'TuTh 8:10AM - 9:30AM', 35, 10),
                   row('22223', 'S03-LEC Regular', LO, 'TuTh 11:10AM - 12:30PM', 30, 4),
                   row('22225', 'S05-LEC Regular', LO, 'TuTh 2:10PM - 3:30PM', 30, 9) ],
    'HIST 2230': [ row('33331', 'S01-LEC Regular', HI, 'MoWe 10:10AM - 11:00AM', 45, 20),
                   row('33332', 'S02-LEC Regular', MID, 'MoWe 2:10PM - 3:00PM', 45, 20),
                   row('33334', 'S04-LEC Regular', HI, 'MoWe 4:10PM - 5:00PM', 45, 0) ],
    'PSY 2010':  [ row('44445', 'S05-LEC Regular', LO, '', 180, 60, { instruction_mode: 'Asynchronous' }),
                   row('44447', 'S07-LEC Regular', HI, '', 150, 40, { instruction_mode: 'Asynchronous' }) ],
    'CHEM 1110': [ row('55551', 'S01-LEC Regular', LO, 'MoWeFr 9:10AM - 10:00AM', 90, 30),
                   row('55552', 'S02-LEC Regular', HI, 'MoWeFr 1:10PM - 2:00PM', 90, 30),
                   row('55561', 'S11-LAB Regular', MID, 'Tu 1:10PM - 4:00PM', 24, 5) ]
  };
  const units = { 'BUS 4442': 4, 'ECON 2001': 4, 'HIST 2230': 4, 'PSY 2010': 4, 'CHEM 1110': 4 };
  const orig = window.classInfo;
  window.classInfo = function (code) { const r = orig.apply(this, arguments) || {}; if (units[code]) r.units = units[code]; return r; };
  return { HI, LO, MID };
})()`;

for (const [w, h, label] of [[1280, 900, 'desktop'], [390, 800, 'phone']]) {
  const ctx = await b.newContext({ viewport: { width: w, height: h }, hasTouch: label === 'phone', isMobile: label === 'phone' });
  await ctx.route('**', (r) => r.request().url().startsWith('http://localhost:' + PORT) ? r.continue() : r.abort());
  const p = await ctx.newPage(); const errs = []; p.on('pageerror', (e) => errs.push(e.message));
  await p.goto('http://localhost:' + PORT + '/', { waitUntil: 'domcontentloaded' });
  await p.waitForTimeout(3500);
  const names = await p.evaluate(FIXTURE);
  await p.evaluate(() => { try { localStorage.removeItem('professify_plans_' + mcTerm()); } catch (e) {} });

  ok(`${label}: the module loaded`, await p.evaluate(() => !!window.TCPlans && !!document.getElementById('plans-js')));
  ok(`${label}: tabs read My classes · Plans · Planner`, await p.evaluate(() =>
    document.getElementById('stab-watch').textContent.trim().startsWith('Plans') && document.getElementById('stab-plan').textContent.trim().startsWith('Planner')));

  const HOVER = label === 'desktop';
  const pick = async (code) => {                         // point at (desktop) or tap (phone) a class in Planner
    const sel = `#plBuilderOut .pl3-need[data-code="${code}"]`;
    if (HOVER) { await p.hover(sel); await p.waitForTimeout(330); } else { await p.tap(sel); await p.waitForTimeout(120); }
  };
  const ghosts = () => p.evaluate(() => [...new Set([...document.querySelectorAll('#pl3BWeek .pl3-ghost')].map((g) => g.getAttribute('data-crn')))].sort());

  /* ---- Plans: an empty plan is an empty week with one button ------------------------------------ */
  await p.evaluate(() => { show('sched'); setSchedTab('watch'); });
  await p.waitForTimeout(200);
  ok(`${label}: Plans shows three plan buttons, an empty week and ONE action`, await p.evaluate(() => {
    const o = document.getElementById('plansOut');
    return o && o.offsetParent !== null && o.querySelectorAll('.pl3-pill').length === 3 && /Nothing in Plan A yet/.test(o.textContent)
      && o.querySelectorAll('.pl3-col').length === 5 && o.querySelectorAll('.btn.primary').length === 1 && /Build Plan A/.test(o.querySelector('.btn.primary').textContent);
  }));
  ok(`${label}: the old watchlist controls are hidden, not drawn over`, await p.evaluate(() =>
    getComputedStyle(document.querySelector('#schedWatchWrap .wl-hdr')).display === 'none' && getComputedStyle(document.getElementById('watchClassSec')).display === 'none'));
  ok(`${label}: signed out, it says plans are kept on this device`, await p.evaluate(() => /kept on this device/.test(document.getElementById('plansOut').textContent)));

  /* ---- Build Plan A → Planner --------------------------------------------------------------- */
  await p.click('#plansOut [data-pl-act="edit"]');
  await p.waitForTimeout(150);
  ok(`${label}: "Build Plan A" opens Planner, building Plan A, degree tucked away`, await p.evaluate(() => {
    const w = document.getElementById('schedPlanWrap'), bo = document.getElementById('plBuilderOut');
    return w.style.display !== 'none' && /Building Plan A/.test(bo.textContent) && getComputedStyle(document.getElementById('plRecord')).display === 'none'
      && /Classes you need/.test(bo.textContent) && document.getElementById('stab-plan').classList.contains('on');
  }));
  ok(`${label}: with no major it says how to fill the list, and search still works`, await p.evaluate(() => /Add your major in Settings/.test(document.getElementById('plBuilderOut').textContent)));
  await p.fill('#plBuilderOut input[data-pl-act="q"]', 'econ');
  await p.waitForTimeout(120);
  ok(`${label}: searching "econ" lists ECON 2001, and the box keeps focus while typing`, await p.evaluate(() =>
    !!document.querySelector('#plBuilderOut .pl3-need[data-code="ECON 2001"]') && document.activeElement && document.activeElement.getAttribute('data-pl-act') === 'q'));
  await pick('ECON 2001');
  ok(`${label}: ${HOVER ? 'hovering' : 'tapping'} a class draws every section that fits as a green block`, JSON.stringify(await ghosts()) === JSON.stringify(['22221', '22223', '22225']), JSON.stringify(await ghosts()));
  ok(`${label}: ${HOVER ? 'pointing' : 'ONE tap'} is enough — the phone's first tap is not undone by focus`, (await ghosts()).length === 3);
  if (HOVER) {
    /* crossing another class on the way to a green block must not change the preview */
    await p.fill('#plBuilderOut input[data-pl-act="q"]', '');
    await p.waitForTimeout(100);
    await p.fill('#plBuilderOut input[data-pl-act="q"]', 'e');
    await p.waitForTimeout(100);
    const codes = await p.evaluate(() => [...document.querySelectorAll('#plBuilderOut .pl3-need')].map((x) => x.getAttribute('data-code')));
    const other = codes.find((c) => c !== 'ECON 2001');
    await p.hover('#plBuilderOut .pl3-need[data-code="ECON 2001"]'); await p.waitForTimeout(330);
    if (other) { await p.hover(`#plBuilderOut .pl3-need[data-code="${other}"]`); await p.waitForTimeout(60); }
    await p.hover('#pl3BWeek .pl3-col:nth-of-type(3)'); await p.waitForTimeout(400);
    /* the gap between the list and the week takes longer than the rest time: still no switch */
    if (other) { await p.hover(`#plBuilderOut .pl3-need[data-code="${other}"]`); await p.waitForTimeout(60); await p.mouse.move(640, 5); await p.waitForTimeout(500); await p.hover('#pl3BWeek .pl3-col:nth-of-type(3)'); await p.waitForTimeout(100); }
    ok(`${label}: sweeping past another class on the way to the week keeps the preview`, JSON.stringify(await ghosts()) === JSON.stringify(['22221', '22223', '22225']), JSON.stringify({ other, g: await ghosts() }));
    await p.fill('#plBuilderOut input[data-pl-act="q"]', 'econ');
    await p.waitForTimeout(100);
    await pick('ECON 2001');
  }
  ok(`${label}: …and says so in one line`, await p.evaluate(() => /ECON 2001 fits in 3 spots/.test(document.querySelector('#plBuilderOut .pl3-hint').textContent)));
  if (HOVER) {
    /* the keyboard path: Enter on a class moves focus to its first green block; Enter adds it */
    await p.focus('#plBuilderOut .pl3-need[data-code="ECON 2001"]');
    await p.keyboard.press('Enter'); await p.waitForTimeout(120);
    const kf = await p.evaluate(() => { const a = document.activeElement; return a && a.classList.contains('pl3-ghost') ? a.getAttribute('data-crn') : null; });
    ok(`${label}: keyboard: Enter on a class moves focus to a green block`, !!kf, String(kf));
    await p.evaluate(() => { const g = document.querySelector('#pl3BWeek .pl3-ghost[data-crn="22223"]'); g.focus(); });
    await p.keyboard.press('Enter'); await p.waitForTimeout(150);
    ok(`${label}: keyboard: Enter on the block adds it, and focus stays in the Planner`, await p.evaluate(() =>
      TCPlans.get('A').sections.some((x) => x.class_nbr === '22223') && document.getElementById('plBuilderOut').contains(document.activeElement)));
  } else {
    await p.tap('#pl3BWeek .pl3-ghost[data-crn="22223"]');
    await p.waitForTimeout(150);
  }
  ok(`${label}: clicking a green block adds that section to the plan, and watches it`, await p.evaluate(() =>
    TCPlans.get('A').sections.some((x) => x.class_nbr === '22223') && isWatchedSec('ECON 2001', '22223') && document.querySelectorAll('#pl3BWeek .pl3-blk').length === 2));
  await p.evaluate(() => { TCPlans.add('A', 'BUS 4442', '11111'); TCPlans.add('A', 'PSY 2010', '44445'); });
  ok(`${label}: search still finds a class that's already in the plan, and says so`, await p.evaluate(() =>
    /In Plan A/.test((document.querySelector('#plBuilderOut .pl3-need[data-code="ECON 2001"]') || {}).textContent || '')));
  ok(`${label}: a class with no times posted says so — not "doesn't fit"`, await p.evaluate(() => {
    SEAT_SECTIONS['ART 1010'] = [{ class_nbr: '77701', section: 'S01-LEC Regular', instructor: 'Cy Lowland', days: 'TBA', status: 'Open', capacity: 20, enrolled: 0, available: 20 }];
    const q = document.querySelector('#plBuilderOut input[data-pl-act="q"]'); q.value = 'art 1010'; q.dispatchEvent(new Event('input', { bubbles: true }));
    document.querySelector('#plBuilderOut .pl3-need[data-code="ART 1010"]').click();
    const h = document.querySelector('#plBuilderOut .pl3-hint').textContent, row = document.querySelector('#plBuilderOut .pl3-need[data-code="ART 1010"]').textContent;
    delete SEAT_SECTIONS['ART 1010'];
    return /no meeting times posted yet/.test(h) && /no time yet/.test(row) && !/fits around/.test(h);
  }));
  ok(`${label}: sections at the very same time become one green block (the best-rated), not slivers`, await p.evaluate(() => {
    SEAT_SECTIONS['ECON 2002'] = ['1', '2', '3', '4'].map((n) => ({ class_nbr: '8880' + n, section: 'S0' + n + '-LEC Regular', instructor: n === '3' ? 'Ada Hilltop' : 'Cy Lowland', days: 'Fr 9:10AM - 10:00AM', status: 'Open', capacity: 30, enrolled: 5, available: 25 }));
    const q = document.querySelector('#plBuilderOut input[data-pl-act="q"]'); q.value = 'econ 2002'; q.dispatchEvent(new Event('input', { bubbles: true }));
    document.querySelector('#plBuilderOut .pl3-need[data-code="ECON 2002"]').click();
    const gs = [...document.querySelectorAll('#pl3BWeek .pl3-ghost')];
    const r = gs.length === 1 && gs[0].getAttribute('data-crn') === '88803' && /\+3/.test(gs[0].textContent);
    delete SEAT_SECTIONS['ECON 2002']; q.value = ''; q.dispatchEvent(new Event('input', { bubbles: true }));
    return r;
  }));
  await p.fill('#plBuilderOut input[data-pl-act="q"]', 'hist');
  await p.waitForTimeout(120);
  await pick('HIST 2230');
  ok(`${label}: a section that clashes with the plan, or is full, is never offered`, JSON.stringify(await ghosts()) === JSON.stringify(['33332']), JSON.stringify(await ghosts()));
  await p.click('#pl3BWeek .pl3-ghost[data-crn="33332"]');
  await p.waitForTimeout(150);
  await p.fill('#plBuilderOut input[data-pl-act="q"]', '');
  await p.waitForTimeout(100);

  /* ---- remove in Planner, and Undo ---------------------------------------------------------- */
  await p.click('#pl3BWeek .pl3-rm[data-crn="33332"]');
  await p.waitForTimeout(120);
  const rm = await p.evaluate(() => ({ n: TCPlans.get('A').sections.length, undo: !!document.querySelector('#plBuilderOut .pl3-note--undo'), w: isWatchedSec('HIST 2230', '33332') }));
  ok(`${label}: × removes the section, offers Undo, and un-watches what the plan watched`, rm.n === 3 && rm.undo && !rm.w, JSON.stringify(rm));
  await p.click('#plBuilderOut [data-pl-act="undo"]');
  await p.waitForTimeout(120);
  ok(`${label}: Undo puts it back, watched again`, await p.evaluate(() => TCPlans.get('A').sections.length === 4 && isWatchedSec('HIST 2230', '33332')));

  /* ---- the degree section, and Done ---------------------------------------------------------- */
  await p.click('#plBuilderOut [data-pl-act="degree"]');
  ok(`${label}: "Show your degree progress" brings the ledger back`, await p.evaluate(() => getComputedStyle(document.getElementById('plRecord')).display !== 'none'));
  await p.click('#plBuilderOut [data-pl-act="degree"]');
  ok(`${label}: Past classes still lands on the record (degree opened)`, await p.evaluate(() => { setSchedTab('past'); const r = getComputedStyle(document.getElementById('plRecord')).display !== 'none'; plansOpenDegree(); return r; }));
  await p.evaluate(() => { TCPlans.renderBuilder(); });
  await p.click('#plBuilderOut [data-pl-act="done"]');
  await p.waitForTimeout(150);

  /* ---- Plans: the plan is a week ------------------------------------------------------------- */
  const a = await p.evaluate(() => {
    const o = document.getElementById('plansOut');
    return { vis: document.getElementById('schedWatchWrap').style.display !== 'none', sum: (o.querySelector('.pl3-sum') || {}).textContent || '',
      blocks: o.querySelectorAll('.pl3-blk').length, loose: [...o.querySelectorAll('.pl3-lchip')].map((x) => x.textContent).join('|'),
      pill: o.querySelector('.pl3-pill.on span').textContent, prim: [...o.querySelectorAll('.btn.primary')].map((x) => x.textContent),
      watched: ['11111', '22223', '33332', '44445'].every((n, i) => isWatchedSec(['BUS 4442', 'ECON 2001', 'HIST 2230', 'PSY 2010'][i], n)),
      count: document.getElementById('stabWatchN').textContent.trim() };
  });
  ok(`${label}: Done returns to Plans, where Plan A is its week`, a.vis && a.blocks === 6 && /PSY 2010-05 · Online/.test(a.loose), JSON.stringify(a));
  ok(`${label}: one line says what the plan is`, a.sum === '4 classes · 16 units · no clashes · Fri free', a.sum);
  ok(`${label}: one primary action (Game plan); every class is watched; the tab counts plans`, a.prim.join() === 'Game plan' && a.watched && a.pill === '16 units' && a.count === '(1)', JSON.stringify(a));
  await p.evaluate(() => { const b = document.querySelector('#plansOut .pl3-blk[data-crn="22223"]'); b.click(); });
  await p.waitForTimeout(150);
  ok(`${label}: tapping a class on the week opens that class`, await p.evaluate(() => document.getElementById('view-class').classList.contains('active') && cpCode === 'ECON 2001'));

  await p.evaluate(() => { TCPlans.add('B', 'HIST 2230', '33331'); TCPlans.add('B', 'BUS 4442', '11111'); });
  ok(`${label}: a clash inside a plan is named and outlined`, await p.evaluate(() => {
    TCPlans.setCur('B'); const o = document.getElementById('plansOut');
    const r = /1 clash/.test(o.querySelector('.pl3-sum').textContent) && o.querySelectorAll('.pl3-blk--clash').length === 4; TCPlans.setCur('A'); return r;
  }));

  /* a section the student watched on their own survives leaving a plan */
  await p.evaluate(() => { wcWatchSec('ECON 2001', '22225', null, true); TCPlans.add('C', 'ECON 2001', '22225'); TCPlans.remove('C', '22225'); });
  ok(`${label}: a section watched BEFORE it joined a plan stays watched when it leaves`, await p.evaluate(() => isWatchedSec('ECON 2001', '22225')));
  await p.evaluate(() => TCPlans.add('C', 'ECON 2001', '22225'));

  ok(`${label}: with a major, "Classes you need" lists what the ledger still needs, and only if it is offered`, await p.evaluate(() => {
    const was = student.major; student.major = 'Business Administration';
    const L = plLedgerCompute(); const need = [];
    (L && L.led && L.led.need || []).forEach((sl) => (sl.codes || []).forEach((c) => need.push(c)));
    const code = need.find((c) => !SEAT_SECTIONS[c]);
    SEAT_SECTIONS[code] = [{ class_nbr: '66601', section: 'S01-LEC Regular', instructor: 'Ada Hilltop', days: 'Fr 9:10AM - 12:00PM', status: 'Open', capacity: 30, enrolled: 10, available: 20 }];
    const G = TCPlans.needGroups('B'); const major = G.groups.find((g) => g.title === 'Your major');
    const ok1 = !!major && major.rows.some((r) => r.code === code && r.fit.list.length === 1);
    const other = need.find((c) => c !== code && !SEAT_SECTIONS[c]);
    const ok2 = !major.rows.some((r) => r.code === other);          // not offered this term → not listed
    delete SEAT_SECTIONS[code]; student.major = was;
    return ok1 && ok2;
  }));

  /* ---- CONTRAST AND SIZE, measured on the rendered screens, in all three themes (Tate) -------- */
  const cr = await p.evaluate(() => {
    const parse = (c) => { const m = c.match(/rgba?\(([^)]+)\)/); if (!m) return null; const v = m[1].split(/[ ,\/]+/).filter(Boolean).map(Number); return [v[0], v[1], v[2], v.length > 3 ? v[3] : 1]; };
    const over = (f, b) => [0, 1, 2].map((i) => f[i] * f[3] + b[i] * (1 - f[3])).concat(1);
    const bgOf = (el) => { const stack = []; for (let n = el; n; n = n.parentElement) { const c = parse(getComputedStyle(n).backgroundColor); if (c && c[3] > 0) { stack.push(c); if (c[3] >= 1) break; } }
      let b = [255, 255, 255, 1]; if (stack.length && stack[stack.length - 1][3] >= 1) b = stack.pop(); else { const r = parse(getComputedStyle(document.body).backgroundColor); if (r) b = r; }
      while (stack.length) b = over(stack.pop(), b); return b; };
    const lum = (c) => { const f = (v) => { v /= 255; return v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4); }; return 0.2126 * f(c[0]) + 0.7152 * f(c[1]) + 0.0722 * f(c[2]); };
    const ratio = (el) => { const b = bgOf(el), f = over(parse(getComputedStyle(el).color), b); const l1 = lum(f), l2 = lum(b); return (Math.max(l1, l2) + 0.05) / (Math.min(l1, l2) + 0.05); };
    const out = {};
    const was = document.documentElement.getAttribute('data-theme');
    for (const th of ['dark', 'light', 'cream']) {
      if (typeof setTheme === 'function') setTheme(th); else document.documentElement.setAttribute('data-theme', th);
      show('sched'); setSchedTab('plan'); TCPlans.renderBuilder();
      const sel = document.querySelector('#plBuilderOut .pl3-need'); if (sel) sel.click();
      const worst = {}; let small = [];
      const check = (root) => root.querySelectorAll('*').forEach((el) => {
        if (!el.childNodes.length || ![...el.childNodes].some((n) => n.nodeType === 3 && n.textContent.trim())) return;
        if (el.offsetParent === null) return;
        const k = el.className || el.tagName; const r = ratio(el);
        if (!(k in worst) || r < worst[k]) worst[k] = Math.round(r * 100) / 100;
        if (parseFloat(getComputedStyle(el).fontSize) < 10.5) small.push(k);
      });
      check(document.getElementById('plBuilderOut'));
      setSchedTab('watch'); check(document.getElementById('plansOut'));
      const low = Object.keys(worst).filter((k) => worst[k] < 4.5).map((k) => k + ' ' + worst[k]);
      out[th] = { low, small: [...new Set(small)] };
    }
    if (typeof setTheme === 'function') setTheme(was || 'dark'); else document.documentElement.setAttribute('data-theme', was || 'dark');
    return out;
  });
  for (const th of ['dark', 'light', 'cream']) {
    ok(`${label}: every piece of text on Plans and Planner is ≥4.5:1 in ${th}`, cr[th].low.length === 0, JSON.stringify(cr[th].low));
    ok(`${label}: nothing on Plans and Planner is smaller than 10.5px in ${th}`, cr[th].small.length === 0, JSON.stringify(cr[th].small));
  }
  ok(`${label}: every plan button, class row and main button is at least 44px tall`, await p.evaluate(() => {
    setSchedTab('plan'); TCPlans.renderBuilder();
    const els = [...document.querySelectorAll('#plBuilderOut .pl3-pill, #plBuilderOut .pl3-need, #plBuilderOut .btn, #plBuilderOut .pl3-degree, #plBuilderOut input')];
    setSchedTab('watch'); const e2 = [...document.querySelectorAll('#plansOut .pl3-pill, #plansOut .btn, #plansOut .pl3-share')];
    return els.length > 4 && els.concat(e2).every((x) => x.getBoundingClientRect().height >= 44 || x.offsetParent === null);
  }));
  await p.evaluate(() => { show('sched'); setSchedTab('watch'); });

  /* ---- the class page -------------------------------------------------------------------------- */
  await p.evaluate(() => { openClassPage('ECON 2001'); });
  await p.waitForTimeout(250);
  const cp = await p.evaluate(() => [...document.querySelectorAll('#cpOut .pl2-cpbtn')].map((x) => x.getAttribute('data-crn') + ':' + x.textContent));
  ok(`${label}: class page: each section says which plan it is in, or ＋ Plan`, cp.includes('22223:In Plan A') && cp.includes('22221:＋ Plan') && cp.includes('22225:In Plan C'), JSON.stringify(cp));
  await p.click('#cpOut .pl2-cpbtn[data-crn="22221"]');
  await p.waitForTimeout(100);
  ok(`${label}: ＋ Plan opens a chooser with A, B and C`, await p.evaluate(() => document.querySelectorAll('#plChoose [data-pl-act="chtoggle"]').length === 3));
  await p.click('#plChoose [data-slot="B"]');
  await p.waitForTimeout(150);
  ok(`${label}: choosing B adds it to Plan B, watches it, and the button updates at once`, await p.evaluate(() =>
    TCPlans.slotsHaving('22221').join() === 'B' && isWatchedSec('ECON 2001', '22221')
    && /In Plan B/.test(document.querySelector('#cpOut .pl2-cpbtn[data-crn="22221"]').textContent) && !document.getElementById('plChoose')));

  await p.evaluate(() => TCPlans._setInterest({ '22223': 9, '22221': 2 }));
  await p.evaluate(() => renderClassPage());
  const chips = await p.evaluate(() => [...document.querySelectorAll('#cpOut .cp-sec')].map((r) => r.textContent.match(/(\d+) in plans/)?.[1] || '-'));
  ok(`${label}: "N in plans" shows 9, and never a 2`, chips.includes('9') && !chips.includes('2'), JSON.stringify(chips));

  /* ---- backups (item 2) ---------------------------------------------------------------------- */
  const bk = await p.evaluate(() => {
    const o = {};
    const e = TCPlans.backupFor('A', '22223'); o.econ = e && e.best && e.best.crn;
    const h = TCPlans.backupFor('A', '33332'); o.hist = h && h.best ? h.best.crn : null;
    const s = TCPlans.backupFor('A', '44445'); o.psy = s && s.best && s.best.crn;
    return o;
  });
  ok(`${label}: backup = the best-rated other section that fits the week`, bk.econ === '22221', JSON.stringify(bk));
  ok(`${label}: a section that clashes with the plan, or is full, is never the backup`, bk.hist === null, JSON.stringify(bk));
  ok(`${label}: an async class's backup is another async section`, bk.psy === '44447', JSON.stringify(bk));

  /* ---- the game plan (item 1) ---------------------------------------------------------------- */
  await p.evaluate(() => TCPlans.add('A', 'CHEM 1110', '55551'));
  const g = await p.evaluate(() => {
    const x = TCPlans.gamePlan('A');
    return { order: x.steps.map((s) => s.i.code), first: x.steps[0].reasons[0].t, rounds: x.steps.map((s) => s.round), split: x.split,
      r1: x.r1Units, preview: x.preview, chem: (x.steps.find((s) => s.i.code === 'CHEM 1110').backup || {}).needsLab };
  });
  ok(`${label}: the only section that fits the week is registered first`, g.order[0] === 'BUS 4442' && g.first === 'Only section that fits your week', JSON.stringify(g));
  ok(`${label}: 20 units → the first 16 in Round 1, the rest in Round 2`, g.split && g.r1 === 16 && g.rounds.filter((r) => r === 2).length === 1 && g.rounds[g.rounds.length - 1] === 2, JSON.stringify(g));
  ok(`${label}: a lecture with a lab says "pick a lab too"`, g.chem === true, JSON.stringify(g));
  ok(`${label}: when the only other fitting section is full, it says "only OPEN section" — and has no backup`, await p.evaluate(() => {
    const st = TCPlans.gamePlan('A').steps.find((x) => x.i.code === 'HIST 2230');
    return st.reasons[0].t === 'Only open section that fits your week' && !(st.backup && st.backup.best);
  }));
  ok(`${label}: Fall sections while registering for Spring → labelled a preview`, g.preview === true);

  await p.evaluate(() => { closeClassPage && closeClassPage(); } ).catch(() => {});
  await p.evaluate(() => TCPlans.openGamePlan('A'));
  await p.waitForTimeout(200);
  const gp = await p.evaluate(() => {
    const m = document.getElementById('plGpModal');
    return { open: document.getElementById('plGpBack').classList.contains('open'), steps: m.querySelectorAll('.pl2-step').length,
      sep: !!m.querySelector('.pl2-roundsep'), prev: /preview/.test(m.querySelector('h2').textContent) && /treat it as a preview/.test(m.textContent),
      cap: /16 units and waitlist 12/.test(m.textContent), none: /None fits/.test(m.textContent), lab: /pick a lab too/.test(m.textContent),
      honest: /can’t see anyone’s appointment time/.test(m.textContent), round: /Round 1 opens/.test(m.textContent) };
  });
  ok(`${label}: the game plan opens with every section as a step`, gp.open && gp.steps === 5, JSON.stringify(gp));
  ok(`${label}: it shows the Round 1 cap, a Round 2 divider and the round dates`, gp.cap && gp.sep && gp.round, JSON.stringify(gp));
  ok(`${label}: "None fits" and "pick a lab too" appear where they are true`, gp.none && gp.lab, JSON.stringify(gp));
  ok(`${label}: it says it is a preview, and that it cannot see appointments`, gp.prev && gp.honest, JSON.stringify(gp));
  if (label === 'phone') ok(`${label}: no sideways scroll in the game plan`, await p.evaluate(() => {
    const m = document.getElementById('plGpModal'); return m.scrollWidth <= m.clientWidth + 1 && document.documentElement.scrollWidth <= window.innerWidth + 1;
  }));

  await p.fill('#plGpModal input[type="datetime-local"]', '2030-10-19T09:30');
  await p.waitForTimeout(150);
  ok(`${label}: an appointment time is kept and counted down`, await p.evaluate(() => /in \d+ days?/.test(document.querySelector('#plGpModal .pl2-appt').textContent) && !!localStorage.getItem('professify_appt_' + mcTerm())));

  await p.click('#plGpModal [data-pl-act="usebackup"][data-crn="22223"]');
  await p.waitForTimeout(150);
  ok(`${label}: "Use backup" swaps the section in the plan and keeps the modal open`, await p.evaluate(() =>
    TCPlans.slotsHaving('22221').includes('A') && !TCPlans.slotsHaving('22223').includes('A') && document.getElementById('plGpBack').classList.contains('open')));

  await p.click('#plGpModal [data-pl-act="waitlisted"][data-crn="11111"]');
  await p.waitForTimeout(200);
  ok(`${label}: "Waitlisted" opens the app's own enroll dialog, set to waitlist`, await p.evaluate(() =>
    document.getElementById('enrollBack').classList.contains('open') && /⏳ Waitlist/.test(document.querySelector('#enrollModal .si-seg.wl.on')?.textContent || '')
    && !document.getElementById('plGpBack').classList.contains('open')));
  await p.evaluate(() => enConfirm());
  await p.waitForTimeout(150);
  await p.evaluate(() => TCPlans.openGamePlan('A'));
  await p.waitForTimeout(150);
  ok(`${label}: after confirming, the step reads Waitlisted and the plan still holds it`, await p.evaluate(() =>
    /⏳ Waitlisted/.test(document.getElementById('plGpModal').textContent) && TCPlans.slotsHaving('11111').includes('A')));
  await p.evaluate(() => TCPlans.closeGamePlan());

  /* the same term being registered for: no preview */
  ok(`${label}: when the term IS the registration term, it is not a preview`, await p.evaluate(() => {
    const was = PROFESSIFY_CONFIG.REGISTRATION_TERM; PROFESSIFY_CONFIG.REGISTRATION_TERM = mcTermLabel();
    const r = TCPlans.gamePlan('A').preview === false; PROFESSIFY_CONFIG.REGISTRATION_TERM = was; return r;
  }));

  /* ---- the banner ---------------------------------------------------------------------------- */
  const bn = await p.evaluate(() => {
    const d = new Date(Date.now() + 3 * 864e5); const ymd = d.toISOString().slice(0, 10);
    const was = PROFESSIFY_CONFIG.REGISTRATION_OPENS; PROFESSIFY_CONFIG.REGISTRATION_OPENS = ymd;
    try { localStorage.removeItem('professify_dismiss_reg_' + ymd); } catch (e) {}
    renderCampusBanner();
    const btn = [...document.querySelectorAll('#campusBanner button')].find((x) => /game plan/i.test(x.textContent));
    const text = document.getElementById('campusBanner').textContent;
    if (btn) btn.click();
    const opened = document.getElementById('plGpBack').classList.contains('open');
    TCPlans.closeGamePlan(); PROFESSIFY_CONFIG.REGISTRATION_OPENS = was; renderCampusBanner();
    return { btn: !!btn, opened, text };
  });
  ok(`${label}: the Round 1 banner's button opens the game plan`, bn.btn && bn.opened && !/locking in/.test(bn.text), JSON.stringify(bn));

  /* ---- Hawk ---------------------------------------------------------------------------------- */
  await p.evaluate(() => { show('home'); window.HawkAsk.ask('what do i register for first'); });
  await p.waitForTimeout(1500);
  const hk = await p.evaluate(() => {
    const t = [...document.querySelectorAll('.hawk-box .hawk-turn, .hawk-box [class*="turn"]')].pop() || document.querySelector('.hawk-box');
    return { text: t ? t.textContent : '', open: [...document.querySelectorAll('.hawk-box .hawk-row')].some((r) => /Open the full game plan/.test(r.textContent)) };
  });
  ok(`${label}: Hawk answers "what do I register for first" from Plan A, in order`, /game plan · Plan A/.test(hk.text) && /1\. BUS 4442-01/.test(hk.text) && hk.open, hk.text.slice(0, 300));
  await p.evaluate(() => { const r = [...document.querySelectorAll('.hawk-box .hawk-row')].find((x) => /Open the full game plan/.test(x.textContent)); r && r.click(); });
  await p.waitForTimeout(200);
  ok(`${label}: …and "Open the full game plan" opens it`, await p.evaluate(() => document.getElementById('plGpBack').classList.contains('open')));
  await p.evaluate(() => TCPlans.closeGamePlan());

  await p.evaluate(() => { TCPlans.setSections('C', []); window.HawkAsk.ask('build me a 12 unit schedule with hist 2230'); });
  await p.waitForFunction(() => !!document.querySelector('.hawk-plansave'), null, { timeout: 8000 }).catch(() => {});
  const bs = await p.evaluate(() => {
    const box = [...document.querySelectorAll('.hawk-plansave')].pop();
    return box ? [...box.querySelectorAll('.hawk-plansave__btn')].map((x) => x.textContent) : null;
  });
  ok(`${label}: Build my term offers Replace A / Replace B / Save as C`, bs && bs.join('|') === 'Replace A|Replace B|Save as C', JSON.stringify(bs) + ' ' + (await p.evaluate(() => (document.querySelector('.hawk-box') || {}).innerText || 'nobox')).slice(0, 400));
  const before = await p.evaluate(() => JSON.stringify(TCPlans.get('C').sections));
  await p.evaluate(() => { const box = [...document.querySelectorAll('.hawk-plansave')].pop(); if (box) [...box.querySelectorAll('.hawk-plansave__btn')][2].click(); });
  await p.waitForTimeout(150);
  const saved = await p.evaluate(() => ({ n: TCPlans.get('C').sections.length, all: TCPlans.get('C').sections.every((x) => isWatchedSec(x.code, x.class_nbr)),
    msg: ([...document.querySelectorAll('.hawk-plansave__done')].pop() || {}).textContent || '' }));
  ok(`${label}: Save as C stores the option, watches every class, and says so`, saved.n > 0 && saved.all && /Saved as Plan C/.test(saved.msg), JSON.stringify(saved));
  await p.evaluate(() => { const u = [...document.querySelectorAll('.hawk-plansave__undo')].find((x) => x.textContent === 'Undo'); if (u) u.click(); });
  ok(`${label}: Undo puts Plan C back as it was`, await p.evaluate((b) => JSON.stringify(TCPlans.get('C').sections) === b, before));
  await p.evaluate(() => { try { window.HawkAsk.close(); } catch (e) {} });

  /* ---- a friend's plans ------------------------------------------------------------------------ */
  const fr = await p.evaluate(() => {
    FRIENDS.push({ id: 'f-maya', name: 'Maya Ortiz', ini: 'MO', classes: [], history: [] });
    friendsList.push({ id: 'f-maya', name: 'Maya Ortiz', classes: [], crns: [], secs: [], history: [], wl: {}, color: '#f0b37e' });
    TCPlans._setFriendPlans([
      { user_id: 'f-maya', slot: 'A', sections: [{ code: 'ECON 2001', class_nbr: '22221' }, { code: 'CHEM 1110', class_nbr: '55552' }] },
      { user_id: 'f-maya', slot: 'B', sections: [{ code: 'PSY 2010', class_nbr: '44447' }] },
      { user_id: 'someone-not-a-friend', slot: 'A', sections: [{ code: 'BUS 4442', class_nbr: '11111' }] }]);
    openFriendProfile('f-maya', 'plans');
    const m = document.getElementById('frpModal');
    return { tab: /Plans \(2\)/.test(m.textContent), same: /Same section · your Plan A, B/.test(m.textContent) || /Same section · your Plan A/.test(m.textContent),
      add: m.querySelectorAll('.pl2-cpbtn').length, shares: /Maya shares 2 plans/.test(m.textContent) };
  });
  ok(`${label}: a friend's profile has a Plans tab with their shared plans`, fr.tab && fr.shares, JSON.stringify(fr));
  ok(`${label}: overlap is marked, and the rest offer ＋ Plan`, fr.same && fr.add === 1, JSON.stringify(fr));
  ok(`${label}: opening straight onto Plans shows the Plans tab on screen`, await p.evaluate(() => {
    const t = document.querySelector('#frpModal .frp-tabs .wl-tab.on'); const row = t && t.parentElement.getBoundingClientRect(); const r = t && t.getBoundingClientRect();
    return !!t && /Plans/.test(t.textContent) && r.left >= row.left - 1 && r.right <= row.right + 1;
  }));
  await p.evaluate(() => { const b = document.querySelector('#frpModal [data-pl-act="fpslot"][data-slot="B"]'); b && b.click(); });
  await p.waitForTimeout(100);
  ok(`${label}: switching to their Plan B shows it`, await p.evaluate(() => /PSY 2010-07/.test(document.getElementById('frpModal').textContent)));
  ok(`${label}: the Plans tab stays simple — no faces, chips or counts on the week`, await p.evaluate(() => {
    closeFriendProfile(); show('sched'); setSchedTab('watch'); TCPlans.setCur('A'); TCPlans.render();
    const o = document.getElementById('plansOut'); return !o.querySelector('.pl2-face, .pl2-chip, .pl3-tag') && o.querySelectorAll('.pl3-blk').length > 0;
  }));

  if (label === 'phone') ok(`${label}: no sideways scroll on Plans`, await p.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth + 1));
  ok(`${label}: plans survive a reload (kept on the device, per term)`, await (async () => {
    const want = await p.evaluate(() => JSON.stringify(TCPlans.get('A').sections));
    await p.reload({ waitUntil: 'domcontentloaded' }); await p.waitForTimeout(2500);
    return await p.evaluate((w) => JSON.stringify(TCPlans.get('A').sections) === w, want);
  })());
  /* ---- review fixes (2026-09-25) ------------------------------------------------------------- */
  await p.evaluate(FIXTURE);   // the reload above dropped the fixture term
  ok(`${label}: the privacy policy says who sees a plan and how counts work, dated 25 September`, await p.evaluate(() => {
    openLegal('privacy'); const h = (document.getElementById('legalBody') || {}).innerHTML || ''; try { closeLegal(); } catch (e) {}
    return /Your plans \(Plan A, B and C\)/.test(h) && /Friends can see/.test(h) && /at least three other students/.test(h)
      && /never includes the person looking/.test(h) && /past classes, plans, watchlist/.test(h) && /Last updated 25 September 2026/.test(h) && !/past classes and watchlist:/.test(h);
  }));
  ok(`${label}: a LAB's backup is checked against the plan's own lecture`, await p.evaluate(() => {
    TCPlans.setSections('C', [{ code: 'CHEM 1110', class_nbr: '55552' }, { code: 'CHEM 1110', class_nbr: '55561' }]);
    // a second lab that overlaps lecture 55552 (MoWeFr 1:10) must not be offered as the lab's backup
    SEAT_SECTIONS['CHEM 1110'].push({ class_nbr: '55562', section: 'S12-LAB Regular', instructor: 'Ada Hilltop', days: 'Mo 1:10PM - 4:00PM', status: 'Open', capacity: 24, enrolled: 10, available: 14, waitlist_total: 0, waitlist_capacity: 10 });
    const b = TCPlans.backupFor('C', '55561'); return !(b && b.best && b.best.crn === '55562');
  }));
  ok(`${label}: a sibling with no time on record makes it "no other section with a set time", not "only"`, await p.evaluate(() => {
    SEAT_SECTIONS['BUS 4442'].push({ class_nbr: '11113', section: 'S03-LEC Regular', instructor: 'Cy Lowland', days: 'TBA', status: 'Open', capacity: 40, enrolled: 0, available: 40 });
    const st = TCPlans.gamePlan('A').steps.find((x) => x.i.code === 'BUS 4442');
    SEAT_SECTIONS['BUS 4442'].pop();
    return st.reasons[0].t === 'No other section with a set time fits';
  }));
  ok(`${label}: an interleaved split (4,5,4,4,3 units → rounds 1,1,1,2,1) never draws a Round 1 class under Round 2`, await p.evaluate(() => {
    const orig = window.classInfo; window.classInfo = function (c) { const r = orig.apply(this, arguments); if (c === 'HIST 2230') r.units = 5; if (c === 'ECON 2001') r.units = 3; return r; };
    const was = TCPlans.get('A').sections.slice();
    TCPlans.setSections('A', [{ code: 'BUS 4442', class_nbr: '11111' }, { code: 'ECON 2001', class_nbr: '22223' }, { code: 'PSY 2010', class_nbr: '44445' },
      { code: 'HIST 2230', class_nbr: '33332' }, { code: 'CHEM 1110', class_nbr: '55551' }]);
    const g = TCPlans.gamePlan('A'); const rounds = g.steps.map((s) => s.round);
    TCPlans.openGamePlan('A');
    const lis = [...document.querySelectorAll('#plGpModal .pl2-steps > li')]; const sepAt = lis.findIndex((li) => li.classList.contains('pl2-roundsep'));
    const after = lis.slice(sepAt + 1).map((li) => li.querySelector('.pl2-code') && li.querySelector('.pl2-code').textContent);
    const r2codes = g.steps.filter((s) => s.round === 2).map((s) => s.i.label);
    TCPlans.closeGamePlan(); TCPlans.setSections('A', was); window.classInfo = orig;
    return rounds.join('') === [...rounds].sort().join('') && rounds.includes(2) && JSON.stringify(after) === JSON.stringify(r2codes);
  }));
  ok(`${label}: a class with no unit count → the split is not stated`, await p.evaluate(() => {
    const orig = window.classInfo; window.classInfo = function (c) { const r = orig.apply(this, arguments); if (c === 'PSY 2010') r.units = null; return r; };
    TCPlans.openGamePlan('A'); const t = document.getElementById('plGpModal').textContent; TCPlans.closeGamePlan(); window.classInfo = orig;
    return /no unit count on record/.test(t) && !/all of it goes in Round 1/.test(t);
  }));
  const acct = await p.evaluate(() => {
    const o = {};
    const anonA = JSON.stringify(TCPlans.get('A').sections);
    sbUser = { id: 'u-test-1' };                                  // "sign in" (no backend: nothing is sent)
    o.fresh = TCPlans.get('A').sections.length === 0;           // the account does not inherit the device's signed-out plans
    TCPlans.render(); o.asks = /Keep them in your account\?/.test(document.getElementById('plansOut').textContent);
    TCPlans.add('A', 'PSY 2010', '44447');
    o.keyed = !!localStorage.getItem('professify_plans_' + mcTerm() + '_u-test-1');
    sbUser = { id: 'u-test-2' };                                  // someone else signs in on this device
    o.other = TCPlans.get('A').sections.length === 0;
    sbUser = null;
    o.anonBack = JSON.stringify(TCPlans.get('A').sections) === anonA;
    return o;
  });
  ok(`${label}: plans are per account — a new account starts empty and is ASKED about the signed-out ones`, acct.fresh && acct.asks && acct.keyed, JSON.stringify(acct));
  ok(`${label}: another account on the same device never sees the first one's plans`, acct.other && acct.anonBack, JSON.stringify(acct));
  ok(`${label}: signing out removes the account's plans from the device`, await p.evaluate(async () => {
    sbUser = { id: 'u-test-1' }; TCPlans.get('A');
    await authSignOut();
    return !localStorage.getItem('professify_plans_' + mcTerm() + '_u-test-1') && sbUser === null;
  }));

  /* ---- signed in: the merge with the account (a stand-in for the database, in the page) ------- */
  const sync = await p.evaluate(async () => {
    const o = {}, M = { rows: {}, fail: false, pushes: 0 };
    const q = (res) => { const pr = Promise.resolve(res); const c = { eq: () => c, neq: () => c, select: () => c, order: () => c, limit: () => c, then: (a, b) => pr.then(a, b) }; return c; };
    const realSb = sb;
    sb = {
      from(t) {
        if (t !== 'plans') return { select: () => q({ data: [], error: null }), upsert: () => q({ error: null }), delete: () => q({ error: null }) };
        return {
          select: () => q({ data: Object.values(M.rows).map((r) => JSON.parse(JSON.stringify(r))), error: null }),
          upsert: (row) => { M.pushes++; if (M.fail) return q({ error: { code: '500', message: 'boom' } }); M.rows[row.slot] = { slot: row.slot, sections: row.sections, shared: row.shared }; return q({ error: null }); },
          delete: () => { const c = { eq: (k, v) => { if (k === 'slot') delete M.rows[v]; return c; }, then: (a, b) => Promise.resolve({ error: null }).then(a, b) }; return c; }
        };
      },
      rpc: () => q({ data: [], error: null }), auth: realSb && realSb.auth
    };
    sbUser = { id: 'u-sync' };
    M.rows = { A: { slot: 'A', sections: [{ code: 'BUS 4442', class_nbr: '11111' }], shared: true },
               B: { slot: 'B', sections: [{ code: 'ECON 2001', class_nbr: '22221' }], shared: false } };
    if (isWatchedSec('BUS 4442', '11111')) wcWatchSec('BUS 4442', '11111', null, true);
    await TCPlans.load();
    o.loaded = TCPlans.get('A').sections.length === 1 && TCPlans.get('B').shared === false;
    o.gated = !isWatchedSec('BUS 4442', '11111');                 // not before the account's own watches arrive
    await loadWatchSectionsFromDb(); await new Promise((r) => setTimeout(r, 50));
    o.watched = isWatchedSec('BUS 4442', '11111');
    M.fail = true; TCPlans.add('A', 'HIST 2230', '33332');
    await new Promise((r) => setTimeout(r, 600));
    o.failNote = /couldn’t be saved to your account/.test(document.getElementById('plansOut').textContent);
    M.fail = false; delete M.rows.B;                              // B was emptied on another device
    await TCPlans.load(); await new Promise((r) => setTimeout(r, 50));
    o.dirtyWon = TCPlans.get('A').sections.length === 2 && (M.rows.A.sections || []).length === 2;
    o.noResurrect = TCPlans.get('B').sections.length === 0 && !M.rows.B;
    sb = realSb; sbUser = null;
    return o;
  });
  ok(`${label}: signed in, the account's plans load (sharing switch included)`, sync.loaded, JSON.stringify(sync));
  ok(`${label}: nothing is watched on the plan's behalf until the account's own watches have loaded`, sync.gated && sync.watched, JSON.stringify(sync));
  ok(`${label}: a failed save says so, and the next load pushes it instead of overwriting it`, sync.failNote && sync.dirtyWon, JSON.stringify(sync));
  ok(`${label}: a plan emptied on another device does not come back`, sync.noResurrect, JSON.stringify(sync));

  ok(`${label}: no page errors`, errs.length === 0, errs.join(' | '));
  await ctx.close();
}
await b.close(); srv.close();
let bad = 0;
for (const r of results) { if (!r.c) bad++; console.log((r.c ? '  ok   ' : 'FAIL   ') + r.n + (r.c || !r.d ? '' : '\n         ' + r.d)); }
console.log(`\n${results.length - bad}/${results.length} passed`);
process.exit(bad ? 1 : 0);
