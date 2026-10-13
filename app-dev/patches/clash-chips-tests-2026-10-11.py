import sys
p=sys.argv[1] if len(sys.argv)>1 else 'check-app.mjs'
s=open(p).read()
def rep(a,b):
    global s
    assert s.count(a)==1,(s.count(a),a[:70]); s=s.replace(a,b)
rep('&& await page.locator(\'#sheet [data-a="atGo"]\').count() === 0 && await page.locator(\'#sheet .at-cta button[disabled]\').count() === 1, \'picker: a clash in a plan names the class and can’t be added\', b);','&& /Replace ECON 2303 with this class/.test(await page.locator(\'#sheet [data-a="atGo"]\').innerText()) && await page.locator(\'#sheet .at-cta button[disabled]\').count() === 0, \'picker: a clash in a plan names the class and offers to replace it\', b);')
rep('/Add anyway/.test(await page.locator(\'#sheet [data-a="atGo"]\').innerText()) && await page.locator(\'#sheet .g-b.clashb\').count() === 2, \'mine: a clash warns, marks the class, and offers Add anyway\', cn);','/Replace BUS 3438 with this class/.test(await page.locator(\'#sheet [data-a="atGo"]\').first().innerText()) && /Add anyway/.test(await page.locator(\'#sheet [data-a="atGo"][data-x="anyway"]\').innerText()) && await page.locator(\'#sheet .g-b.clashb\').count() === 2, \'mine: a clash warns, marks the class, offers Replace and Add anyway\', cn);')
rep("  const m3 = W('my_sections').length;\n  await atGo(page);",'  const m3 = W(\'my_sections\').length;\n  await click(page, \'#sheet [data-a="atGo"][data-x="anyway"]\'); await settle(page, 700); await settle(page, 1100);')
rep('&& await page.locator(\'#sheet [data-a="atGo"]\').count() === 0 && await page.locator(\'#sheet .at-cta button[disabled]\').count() === 1, \'plans: a clash is shown with the real reason and can’t be added\', clashSheet);','&& /Replace PHIL 3331 with this class/.test(await page.locator(\'#sheet [data-a="atGo"]\').innerText()) && await page.locator(\'#sheet .at-cta button[disabled]\').count() === 0, \'plans: a clash is shown with the real reason and offers to replace it\', clashSheet);')
anchor='const names = Object.keys(tests).filter(n => !only || n === only);'
assert s.count(anchor)==1 and 'tests.clashReplace' not in s
blk=r'''/* A clash offers "Replace <the class it clashes with> with this class" (Tate, 2026-10-11), in a plan and in My Classes, with Undo. */
tests.clashReplace = async () => {
  let failDel = false;
  const { page, close, log } = await openApp({ hook: (url, m) => failDel && m === 'DELETE' && url.pathname.endsWith('/saved_classes') ? { status: 400, body: JSON.stringify({ code: '23514', message: 'nope' }) } : null });
  await page.waitForFunction(() => TC.ready && TC.seatsLoaded, null, { timeout: 8000 });
  const W = t => log.writes.filter(w => w.table === t);
  const codes = P => page.evaluate(P => (TC.plans[P] || []).map(i => SEC[i] && SEC[i].code).sort().join(), P);
  /* a plan: PHIL 3331 in Plan A, ECON 2303 §03 clashes with it */
  await page.evaluate(() => { const ph = Object.values(SEC).find(x => x.code === 'PHIL 3331'); TC.setPlan('A', [ph.id]); S.plan = 'A'; render(true); });
  await page.evaluate(() => A.openClass('ECON 2303')); await settle(page, 500);
  await click(page, '.secrow .addbtn >> nth=0');
  if (await page.locator('#sheet [data-a="atGroup"][data-x="plans"][aria-pressed="false"]').count()) await click(page, '#sheet [data-a="atGroup"][data-x="plans"]');
  await click(page, '#sheet [data-a="atPick"][data-x="A"]');
  const b0 = await page.locator('#sheet .at-cta').innerText();
  ok(/Replace PHIL 3331 with this class/.test(b0) && await page.locator('#sheet .g-b.clashb').count() >= 1 && await codes('A') === 'PHIL 3331', 'replace: plan clash — the button names the clashing class; nothing changed yet', b0);
  await atGo(page);
  ok(await codes('A') === 'ECON 2303', 'replace: Plan A now has ECON 2303 and no PHIL 3331', await codes('A'));
  ok(/Replaced PHIL 3331 with ECON 2303 in Plan A/.test(await page.locator('#toast').innerText()), 'replace: the toast says what was replaced', await page.locator('#toast').innerText());
  await click(page, '#toast [data-a="toastUndo"]'); await settle(page, 600);
  ok(await codes('A') === 'PHIL 3331', 'replace: Undo brings PHIL 3331 back and ECON 2303 out', await codes('A'));
  /* My Classes: BUS 4401 §01 clashes with BUS 3438 */
  await page.evaluate(() => { UI.sheet = null; S.stack[S.tab] = []; render(true); });
  await page.evaluate(() => A.openClass('BUS 4401')); await settle(page, 500);
  await click(page, '.secrow .addbtn');
  if (await page.locator('#sheet [data-a="atGroup"][data-x="classes"][aria-pressed="false"]').count()) await click(page, '#sheet [data-a="atGroup"][data-x="classes"]');
  const m0 = await page.evaluate(() => [...myCodes()].sort().join()), w0 = W('my_sections').length, s0 = W('saved_classes').length;
  ok(/Replace BUS 3438 with this class/.test(await page.locator('#sheet .at-cta').innerText()) && /BUS 3438/.test(m0) && !/BUS 4401/.test(m0), 'replace: My Classes clash — Replace is the main button, Add anyway the quiet one', m0);
  await atGo(page);
  const m1 = await page.evaluate(() => [...myCodes()].sort().join());
  const mw = W('my_sections').slice(w0), sw = W('saved_classes').slice(s0);
  ok(/BUS 4401/.test(m1) && !/BUS 3438/.test(m1), 'replace: BUS 4401 is in My Classes and BUS 3438 is out', m1);
  ok(mw.some(w => w.m === 'POST' && w.body.code === 'BUS 4401') && sw.some(w => w.m === 'DELETE' && /BUS(\+|%20)3438/.test(w.query)) && !mw.some(w => w.m === 'DELETE' && /BUS(\+|%20)4401/.test(w.query)), 'replace: saves the new section, takes the old class out, touches nothing else', { mw: mw.map(w => w.m + ' ' + (w.body ? w.body.code : w.query)), sw: sw.map(w => w.m + ' ' + (w.query || '')) });
  ok(/Replaced BUS 3438 with BUS 4401/.test(await page.locator('#toast').innerText()), 'replace: the toast says what was replaced');
  await click(page, '#toast [data-a="toastUndo"]'); await settle(page, 900);
  const m2 = await page.evaluate(() => [...myCodes()].sort().join());
  ok(/BUS 3438/.test(m2) && !/BUS 4401/.test(m2) && m2 === m0, 'replace: Undo puts BUS 3438 back and takes BUS 4401 out', { m0, m2 });
  /* a replace whose removal fails after the new class went in keeps an Undo, and Undo puts everything back */
  await page.evaluate(() => { UI.sheet = null; S.stack[S.tab] = []; render(true); });
  await page.evaluate(() => A.openClass('BUS 4401')); await settle(page, 500);
  await click(page, '.secrow .addbtn');
  if (await page.locator('#sheet [data-a="atGroup"][data-x="classes"][aria-pressed="false"]').count()) await click(page, '#sheet [data-a="atGroup"][data-x="classes"]');
  failDel = true; await atGo(page); failDel = false;
  const tt = await page.locator('#toast').innerText();
  ok(/Undo/.test(tt) && await page.locator('#toast [data-a="toastUndo"]').count() === 1 && await page.locator('#sheet .at-note.bad').count() === 1, 'replace: a half-done replace says so and keeps an Undo', tt);
  await click(page, '#toast [data-a="toastUndo"]'); await settle(page, 900);
  const m3 = await page.evaluate(() => [...myCodes()].sort().join());
  ok(m3 === m0 && /BUS 3438/.test(m3) && !/BUS 4401/.test(m3), 'replace: Undo after a half-done replace restores BUS 3438 and drops BUS 4401', { m0, m3 });
  /* a full plan: replacing never makes it bigger, so it still works */
  await page.evaluate(() => { UI.sheet = null; S.stack[S.tab] = []; render(true); });
  await page.evaluate(() => { const ph = Object.values(SEC).find(x => x.code === 'PHIL 3331'), ids = [ph.id]; for (let i = 0; i < 11; i++) { SEC['ZF' + i] = Object.assign({}, ph, { id: 'ZF' + i, code: 'ZZZ 10' + i, async: true, s: null, e: null, days: [] }); ids.push('ZF' + i); } TC.setPlan('A', ids); S.plan = 'A'; render(true); });
  await page.evaluate(() => A.openClass('ECON 2303')); await settle(page, 500);
  await click(page, '.secrow .addbtn >> nth=0');
  if (await page.locator('#sheet [data-a="atGroup"][data-x="plans"][aria-pressed="false"]').count()) await click(page, '#sheet [data-a="atGroup"][data-x="plans"]');
  await click(page, '#sheet [data-a="atPick"][data-x="A"]');
  await atGo(page);
  const full = await page.evaluate(() => (TC.plans.A || []).map(i => SEC[i] && SEC[i].code));
  ok(full.length === 12 && full.includes('ECON 2303') && !full.includes('PHIL 3331'), 'replace: a plan with 12 sections still replaces the clashing one', full);
  /* a class with two sections where only one clashes: just that section goes, the class stays */
  await page.evaluate(() => { UI.sheet = null; S.stack[S.tab] = []; render(true); });
  await page.evaluate(() => { const b = PEOPLE.me.secs.find(x => x.code === 'BUS 3438'); PEOPLE.me.secs.push(Object.assign({}, b, { id: '999001', days: ['T'], s: 840, e: 900 })); });
  await page.evaluate(() => A.openClass('BUS 4401')); await settle(page, 500);
  await click(page, '.secrow .addbtn');
  if (await page.locator('#sheet [data-a="atGroup"][data-x="classes"][aria-pressed="false"]').count()) await click(page, '#sheet [data-a="atGroup"][data-x="classes"]');
  const w1 = W('my_sections').length, s1 = W('saved_classes').length, clashNbr = await page.evaluate(() => String(PEOPLE.me.secs.find(x => x.code === 'BUS 3438' && x.id !== '999001').id));
  ok(/Replace BUS 3438 with this class/.test(await page.locator('#sheet .at-cta').innerText()), 'replace: a class with a second section that doesn’t clash still offers Replace');
  await atGo(page);
  const mw2 = W('my_sections').slice(w1), sw2 = W('saved_classes').slice(s1);
  ok(mw2.some(w => w.m === 'DELETE' && new RegExp('class_nbr=eq\\.' + clashNbr).test(w.query) && /BUS(\+|%20)3438/.test(w.query)) && !sw2.some(w => w.m === 'DELETE' && /BUS(\+|%20)3438/.test(w.query)), 'replace: only the clashing section is removed; the class stays in My Classes', { mw: mw2.map(w => w.m + ' ' + (w.body ? w.body.class_nbr : w.query)), sw: sw2.map(w => w.m + ' ' + (w.query || '')) });
  ok(log.errors.length === 0, 'replace: no page errors', log.errors);
  await close();
};

/* Champ's first sheet: four broad questions in a 2 x 2 grid, a little smaller than the old stack of three (Tate, 2026-10-11). */
tests.champChips = async () => {
  const WANT = ['When am I free this week?', "Who's free right now?", 'What’s my day look like?', 'My best professor'];
  for (const [w, th] of [[320, 'light'], [360, 'light'], [390, 'dark'], [430, 'light'], [390, 'light']]) {
    const tag = `${w}px ${th}`;
    const { page, close, log } = await openApp({ width: w, height: 780, init: th === 'dark' ? () => { try { localStorage.setItem('tc-theme', 'dark'); } catch (e) {} } : null, ask: b => b.q === 'When am I free this week?' ? null : null });
    await page.waitForFunction(() => TC.ready, null, { timeout: 8000 });
    await click(page, '[data-a="openChamp"]');
    await tick(page, 500);
    const m = await page.evaluate(() => {
      const R = e => { const r = e.getBoundingClientRect(); return { l: r.left, r: r.right, t: r.top, b: r.bottom, w: r.width, h: r.height }; };
      const sh = document.querySelector('#sheet'), g = sh.querySelector('.cchips'), cs = [...sh.querySelectorAll('.cchip')];
      return { grid: g ? getComputedStyle(g).display : null, cls: g ? g.className : '', texts: cs.map(c => c.dataset.x), shown: cs.map(c => c.innerText.trim()), r: cs.map(R), g: g ? R(g) : null, sh: R(sh), fs: cs.map(c => parseFloat(getComputedStyle(c).fontSize)), sw: document.documentElement.scrollWidth, cw: document.documentElement.clientWidth, over: cs.map(c => c.scrollWidth > c.clientWidth + 1), col: g ? getComputedStyle(g).gridTemplateColumns : '', clipped: cs.filter(c => { const q = R(c), s = R(sh); return q.l < s.l - 0.5 || q.r > s.r + 0.5; }).length };
    });
    ok(m.grid === 'grid' && /cgrid/.test(m.cls) && m.r.length === 4, `chips ${tag}: four chips in a grid`, m);
    ok(JSON.stringify(m.texts) === JSON.stringify(WANT) && JSON.stringify(m.shown) === JSON.stringify(WANT), `chips ${tag}: the four broad questions, in order`, m.texts);
    const xs = [...new Set(m.r.map(r => Math.round(r.l)))], ys = [...new Set(m.r.map(r => Math.round(r.t)))];
    ok(xs.length === 2 && ys.length === 2, `chips ${tag}: 2 columns x 2 rows`, { xs, ys });
    ok(m.r[0].t === m.r[1].t && m.r[2].t === m.r[3].t && m.r[0].l === m.r[2].l && m.r[1].l === m.r[3].l && m.r[2].t > m.r[0].b, `chips ${tag}: rows line up, row 2 below row 1`, m.r);
    ok(Math.abs(m.r[0].w - m.r[1].w) < 1 && Math.abs(m.r[2].w - m.r[3].w) < 1 && Math.abs(m.r[0].h - m.r[1].h) < 1 && Math.abs(m.r[2].h - m.r[3].h) < 1, `chips ${tag}: the two in a row match`, m.r);
    ok(m.clipped === 0 && m.over.every(x => !x) && m.sw <= m.cw, `chips ${tag}: inside the sheet, no text clipped, no sideways scroll`, m);
    ok(m.fs.every(f => f < 14) && m.r.every(r => r.h <= 52 && r.h >= 34), `chips ${tag}: smaller than the old 14px / 38px chips`, { fs: m.fs, h: m.r.map(r => r.h) });
    ok(Math.abs((m.r[0].l - m.g.l) - (m.g.r - m.r[1].r)) < 1, `chips ${tag}: grid is centred`, m);
    if (w === 390 && th === 'light') {
      await click(page, '#sheet .cchip >> nth=1'); await tick(page, 900);
      ok(log.asks.length === 0 && await page.locator('#sheet .bot .msg').count() === 1, `chips ${tag}: tapping one is answered on the phone, nothing sent`, log.asks);
      ok(/Who's free right now\?/.test(await page.locator('#sheet .msg.me').first().innerText()), `chips ${tag}: the question is posted`);
      const bar = await page.evaluate(() => { const g = document.querySelector('#sheet .cchips'); return { cls: g.className, n: g.querySelectorAll('.cchip').length, d: getComputedStyle(g).display }; });
      ok(!/cgrid/.test(bar.cls) && bar.n === 4 && bar.d === 'flex', `chips ${tag}: in a conversation the strip stays a scrolling row`, bar);
    }
    ok(log.errors.length === 0, `chips ${tag}: no page errors`, log.errors);
    await close();
  }
};

'''
s=s.replace(anchor,blk+anchor)
open(p,'w').write(s)
