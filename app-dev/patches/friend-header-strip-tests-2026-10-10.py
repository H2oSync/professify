#!/usr/bin/env python3
"""Tests for the option-C friend header. Usage: python3 friend-header-strip-tests-2026-10-10.py app-dev/tests/check-app.mjs"""
import sys
p = sys.argv[1]; s = open(p, encoding='utf-8').read()
def one(old, new):
    global s
    assert s.count(old) == 1, (s.count(old), old[:90]); s = s.replace(old, new)

# friendMajor: read the strip instead of the bubbles
one("""const b = [...document.querySelectorAll('.fbubs .mebub')]; const v = l => { const x = b.find(e => (e.querySelector('.mebub-l') || {}).textContent === l); return x ? x.querySelector('.mebub-v').textContent : null; }; const y = b.find(e => e.classList.contains('yr')); const sub = [v('CONCENTRATION') ? v('CONCENTRATION') + ' concentration' : '', y ? y.textContent : ''].filter(Boolean).join(' · '); return { pill: v('MAJOR'), sub: sub || null }; });""",
"""const b = [...document.querySelectorAll('.fstrip .fs-c')]; const v = l => { const x = b.find(e => (e.querySelector('.fs-l') || {}).textContent === l); return x ? x.querySelector('.fs-v').textContent : null; }; const sub = [v('Concentration') ? v('Concentration') + ' concentration' : '', v('Year')].filter(Boolean).join(' · '); return { pill: v('Major'), sub: sub || null }; });""")
one("""small: b.width === 44 && b.height === 44 && /Message/.test(bt[0].getAttribute('aria-label') || '')""",
    """small: b.height === 34 && b.width > 60 && b.width < 120 && bt[0].textContent.trim() === 'Message' && /Message/.test(bt[0].getAttribute('aria-label') || '')""")
one("""'friend major: Message is a round 44px button where your pencil is (no pin, no full-width button), bubbles under it (Tate 2026-10-08)'""",
    """'friend major: Message is a small labelled pink pill on the right of the header (no pin, no full-width button), the strip under it (Tate 2026-10-10)'""")

# new test, inserted before friendMajor
new = r"""tests.friendStrip = async () => {
  /* Tate 2026-10-10, option C: one neutral strip (Major | Concentration | Year); the year only as wide as its word,
     words never break mid-word, no green/blue, light and dark; your own profile keeps its coloured bubbles. */
  const T = JSON.parse(JSON.stringify(FX.TABLES));
  Object.assign(T.profiles[1], { major: 'Business Administration', class_standing: 'Sophomore', concentration: 'Marketing Management' });
  Object.assign(T.profiles[2], { major: 'Computer Science', class_standing: 'Senior', concentration: 'General / Open' });
  Object.assign(T.profiles[3], { major: 'Architecture', class_standing: null, concentration: null });
  Object.assign(T.profiles[4], { major: 'Entrepreneurship', class_standing: 'Freshman', concentration: 'Communications' });
  const ids = T.profiles.slice(1, 4).map(p => p.id);
  for (const theme of ['light', 'dark']) {
    const init = theme === 'dark' ? () => { try { localStorage.setItem('tc-theme', 'dark'); } catch (e) {} } : null;
    const o = await openApp({ tables: T, grants: { profiles: ['concentration'] }, init });
    await o.page.waitForFunction(() => TC.ready && document.querySelectorAll('.hfeed .fcard').length === 5, null, { timeout: 8000 });
    await o.page.evaluate(id => A.openFriend(id), ids[0]); await settle(o.page);
    const a = await o.page.evaluate(() => { const st = document.querySelector('.fstrip'); if (!st) return null; const cs = [...st.querySelectorAll('.fs-c')], r = e => e.getBoundingClientRect(), y = cs.find(c => c.classList.contains('y')), card = r(document.querySelector('.fpg .mecard')), sr = r(st);
      const mid = cs.every(c => { const v = c.querySelector('.fs-v'); const rg = document.createRange(); const words = v.textContent.split(' '); const tn = v.firstChild; let pos = 0; const tops = []; for (const w of words) { rg.setStart(tn, pos); rg.setEnd(tn, pos + w.length); const rs = [...rg.getClientRects()]; tops.push(new Set(rs.map(x => Math.round(x.top))).size); pos += w.length + 1; } return tops.every(n => n === 1); });
      const col = e => getComputedStyle(e).color, bg = getComputedStyle(st).backgroundColor;
      return { n: cs.length, labels: cs.map(c => c.querySelector('.fs-l').textContent), midWord: mid, yearW: Math.round(r(y).width), majW: Math.round(r(cs[0]).width), conW: Math.round(r(cs[1]).width), fits: sr.left >= card.left && sr.right <= card.right + 0.5, bg, cols: cs.map(c => col(c.querySelector('.fs-v'))), mut: col(cs[0].querySelector('.fs-l')), mebub: document.querySelectorAll('.fpg .mebub').length, ink: col(document.querySelector('.fpg .mename')) }; });
    ok(a && a.n === 3 && a.labels.join() === 'Major,Concentration,Year', `friend strip (${theme}): Major, Concentration, Year in one strip`, a);
    ok(a && a.midWord, `friend strip (${theme}): no word breaks in the middle`, a);
    ok(a && a.yearW < a.majW && a.yearW < a.conW && a.yearW <= 100 && Math.abs(a.majW - a.conW) <= 2, `friend strip (${theme}): the year is only as wide as its word; major and concentration split the rest`, a);
    ok(a && a.fits && a.bg === (theme === 'dark' ? 'rgb(27, 36, 56)' : 'rgb(241, 245, 249)'), `friend strip (${theme}): inside the card, neutral ${theme} fill`, a);
    ok(a && a.cols.every(c => c === a.ink) && a.mebub === 0, `friend strip (${theme}): values are plain ink (no green or blue), the old coloured bubbles are gone`, a);
    /* only a major + a year (General / Open), and only a major */
    await click(o.page, '[data-a="back"]'); await settle(o.page);
    for (const [i, want] of [[1, 'Major,Year'], [2, 'Major']]) {
      await o.page.evaluate(id => A.openFriend(id), ids[i]); await settle(o.page);
      const l = await o.page.evaluate(() => [...document.querySelectorAll('.fstrip .fs-l')].map(e => e.textContent).join());
      ok(l === want, `friend strip (${theme}): ${want.replace(',', ' + ').toLowerCase()} only when that is all they set`, l);
      await click(o.page, '[data-a="back"]'); await settle(o.page);
    }
    await o.page.evaluate(id => A.openFriend(id), T.profiles[4].id); await settle(o.page);
    const lw = await o.page.evaluate(() => [...document.querySelectorAll('.fstrip .fs-c')].map(c => [...c.children].every(e => e.scrollWidth <= e.clientWidth + 0.5) && c.scrollWidth <= c.clientWidth + 0.5));
    ok(lw.length === 3 && lw.every(Boolean), `friend strip (${theme}): long single words (Entrepreneurship, Communications) fit their cells, nothing clipped`, lw);
    await o.page.screenshot({ path: process.env.SHOT_DIR ? process.env.SHOT_DIR + `/strip-${theme}.png` : '/dev/null' }).catch(() => {});
    await click(o.page, '[data-a="back"]'); await settle(o.page);
    ok(o.log.errors.length === 0, `friend strip (${theme}): no page errors`, o.log.errors);
    await o.close();
  }
  /* a 360px phone: the longest single words still fit next to a Sophomore year cell */
  Object.assign(T.profiles[4], { major: 'Entrepreneurship', class_standing: 'Sophomore', concentration: 'Communications' });
  { const o = await openApp({ tables: T, grants: { profiles: ['concentration'] }, width: 360 });
    await o.page.waitForFunction(() => TC.ready && document.querySelectorAll('.hfeed .fcard').length === 5, null, { timeout: 8000 });
    await o.page.evaluate(id => A.openFriend(id), T.profiles[4].id); await settle(o.page);
    const lw = await o.page.evaluate(() => [...document.querySelectorAll('.fstrip .fs-c')].map(c => { const v = c.querySelector('.fs-v'); return v.scrollWidth <= v.clientWidth + 0.5 && c.scrollWidth <= c.clientWidth + 0.5 && v.getBoundingClientRect().right <= document.querySelector('.fstrip').getBoundingClientRect().right + 0.5; }));
    ok(lw.length === 3 && lw.every(Boolean), 'friend strip (360px): Entrepreneurship | Communications | Sophomore: nothing is cut off', lw);
    await o.close(); }
  /* 375px (iPhone mini): ordinary majors and concentrations never break inside a word */
  { const o = await openApp({ tables: T, grants: { profiles: ['concentration'] }, width: 375 });
    await o.page.waitForFunction(() => TC.ready && document.querySelectorAll('.hfeed .fcard').length === 5, null, { timeout: 8000 });
    const bad = [];
    for (const [m, c, y] of [['Business Administration', 'Marketing Management', 'Sophomore'], ['Computer Science', 'Software Engineering', 'Sophomore'], ['Communication Studies', 'Public Relations', 'Freshman'], ['Mechanical Engineering', 'General Engineering', 'Junior']]) {
      await o.page.evaluate(([id, m, c, y]) => { Object.assign(PEOPLE[id], { major: m, conc: c, standing: y }); A.openFriend(id); render(true); }, [T.profiles[4].id, m, c, y]); await settle(o.page);
      const br = await o.page.evaluate(() => [...document.querySelectorAll('.fstrip .fs-v')].flatMap(v => { const tn = v.firstChild, rg = document.createRange(); let pos = 0; return v.textContent.split(' ').filter(wd => { rg.setStart(tn, pos); rg.setEnd(tn, pos + wd.length); pos += wd.length + 1; return new Set([...rg.getClientRects()].map(x => Math.round(x.top))).size > 1; }); }));
      if (br.length) bad.push([m, c, br]);
    }
    ok(!bad.length, 'friend strip (375px): Business Administration, Marketing Management, Software Engineering… never break inside a word', bad);
    await o.close(); }
  /* your own profile keeps its coloured bubbles (the real screen, computed styles) */
  { const o = await openApp({ tables: T });
    await o.page.waitForFunction(() => TC.ready, null, { timeout: 8000 });
    await click(o.page, '.homehdr .me-btn'); await settle(o.page);
    const m = await o.page.evaluate(() => { const b = document.querySelector('.mepg .mebub'); if (!b) return null; const cs = getComputedStyle(b); return { pad: cs.padding, bg: cs.backgroundColor, strip: !!document.querySelector('.fstrip') }; });
    ok(m && m.pad === '8px 14px' && m.bg === 'rgb(198, 238, 228)' && !m.strip, 'friend strip: your own profile keeps its green bubbles, untouched', m);
    await o.close(); }
};

tests.friendMajor = async () => {"""
one("tests.friendMajor = async () => {", new)
open(p, 'w', encoding='utf-8').write(s); print('tests patched')
