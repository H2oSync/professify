#!/usr/bin/env node
/* check-mobile — the phone port, pass 1. Drives the REAL index.html, signed in, offline, through
 * harness/harness.mjs (real supabase-js, synthetic PostgREST far end). Asserts on the rendered
 * page at 390px and at 1280px; nothing here asserts that CSS or a function merely exists.
 *
 *   node check-mobile.mjs [file.html]          default build.html
 */
import { openApp, linkFonts } from './harness/harness.mjs';
const PB = +(process.env.PORT_BASE || 0);
const FILE = process.argv[2] || 'build.html';
linkFonts(process.cwd());
const R = []; const ok = (n, c, d = '') => R.push({ n, c: !!c, d: String(d) });

/* A real swipe, as touch events on the element under the finger — the engine listens on
   document and reads target, touches and changedTouches exactly as a phone delivers them. */
async function swipe(page, dx, { y = 'auto', dy = 0, steps = 8, ms = 180 } = {}) {
  await page.evaluate(async ({ dx, dy, y, steps, ms }) => {
    const x0 = dx < 0 ? 300 : 90, W = window.innerWidth;
    /* 'auto': the first point down the screen that is NOT inside a sideways scroller — those own
       their gesture by design (asserted separately below), so a swipe test has to start clear. */
    if (y === 'auto') { y = 260;
      for (let yy = 180; yy < innerHeight - 120; yy += 20) { const e = document.elementFromPoint(x0, yy);
        if (e && !window.__swipeNav.inScroller(e)) { y = yy; break; } } }
    const el = document.elementFromPoint(x0, y) || document.body;
    const mk = (x, yy) => new Touch({ identifier: 7, target: el, clientX: x, clientY: yy, pageX: x, pageY: yy });
    const fire = (type, t, list) => el.dispatchEvent(new TouchEvent(type, { bubbles: true, cancelable: true,
      touches: list, targetTouches: list, changedTouches: [t] }));
    let t = mk(x0, y); fire('touchstart', t, [t]);
    for (let i = 1; i <= steps; i++) { await new Promise(r => setTimeout(r, ms / steps));
      t = mk(x0 + dx * i / steps, y + dy * i / steps); fire('touchmove', t, [t]); }
    fire('touchend', t, []);
  }, { dx, dy, y, steps, ms });
  await page.waitForTimeout(650);
}
const where = page => page.evaluate(() => {
  const v = document.querySelector('.view.active'); const n = v ? v.id.replace('view-', '') : '';
  return n === 'sched' ? 'sched:' + (window.schedTab === 'past' ? 'plan' : window.schedTab) : n;
});
const visiblePane = page => page.evaluate(() => ['schedMineWrap', 'schedWatchWrap', 'schedPlanWrap']
  .filter(id => { const e = document.getElementById(id); return e && e.offsetParent !== null; }).join(','));

/* ============================== PHONE ============================== */
{
  const { page, ctx, close, log } = await openApp({ file: FILE, port: 8141 + PB });

  /* ---- safe areas ---- */
  ok('viewport asks for viewport-fit=cover',
    await page.evaluate(() => /viewport-fit\s*=\s*cover/.test(document.querySelector('meta[name=viewport]').content)));
  const cdp = await ctx.newCDPSession(page);
  await cdp.send('Emulation.setSafeAreaInsetsOverride', { insets: { top: 47, bottom: 34, left: 0, right: 0 } });
  await page.waitForTimeout(300);
  const sa = await page.evaluate(() => ({
    brand: document.querySelector('.brand').getBoundingClientRect().top,
    pill: (document.querySelector('.prof-wrap, #authBtn') || document.body).getBoundingClientRect().top,
    tab: (() => { const t = document.querySelector('.mtabbar .mtab'); const r = t.getBoundingClientRect(); return innerHeight - r.bottom; })(),
  }));
  ok('under a 47px status bar, the brand clears it', sa.brand >= 47, `brand top ${sa.brand}`);
  ok('under a 47px status bar, the account pill clears it', sa.pill >= 47, `pill top ${sa.pill}`);
  ok('above a 34px home indicator, the tab labels clear it', sa.tab >= 34, `gap ${sa.tab}`);
  /* Everything else pinned to the top of the screen, under a Dynamic-Island-sized 59px inset. Each is
     opened through the app's own opener and measured where its content actually starts. */
  await cdp.send('Emulation.setSafeAreaInsetsOverride', { insets: { top: 59, bottom: 34, left: 0, right: 0 } });
  await page.waitForTimeout(200);
  const tops = {};
  await page.evaluate(() => { try { closeModal && closeModal(); } catch (e) {} }).catch(() => {});
  /* Notifications — a panel pinned under the header. Its gap to the header must be the SAME with an
     inset as without one: the header grew by the inset, so the panel has to move by exactly that. */
  const notifGap = async () => { await page.evaluate(() => openNotifs()); await page.waitForTimeout(400);
    const g = await page.evaluate(() => { const n = document.getElementById('notifPanel'), h = document.querySelector('header.nav');
      return n && !n.hidden ? Math.round(n.getBoundingClientRect().top - h.getBoundingClientRect().bottom) : null; });
    await page.evaluate(() => closeNotifs()); return g; };
  const gap59 = await notifGap();
  await cdp.send('Emulation.setSafeAreaInsetsOverride', { insets: { top: 0, bottom: 0, left: 0, right: 0 } }); await page.waitForTimeout(200);
  const gap0 = await notifGap();
  await cdp.send('Emulation.setSafeAreaInsetsOverride', { insets: { top: 59, bottom: 34, left: 0, right: 0 } }); await page.waitForTimeout(200);
  tops.notif = { gap59, gap0 };
  /* The backend-down banner. It is built in JS with an inline top:12px; this is that exact element,
     id and inline style copied from the code that builds it, so the stylesheet is what is tested. */
  tops.banner = await page.evaluate(() => { const b = document.createElement('div'); b.id = 'sbDeadBanner';
    b.style.cssText = 'position:fixed;left:12px;right:12px;top:12px;z-index:9999;padding:10px'; b.textContent = 'x';
    document.body.appendChild(b); const t = Math.round(b.getBoundingClientRect().top); b.remove(); return t; });
  /* A bottom sheet (the rate form) ends above the home indicator. */
  await page.evaluate(() => openRate()); await page.waitForTimeout(600);
  tops.sheetPad = await page.evaluate(() => { const m = document.querySelector('.mback.open .modal, .mback[style*="flex"] .modal');
    return m ? parseFloat(getComputedStyle(m).paddingBottom) : null; });
  await page.keyboard.press('Escape'); await page.waitForTimeout(300);
  ok('Notifications panel keeps its place under the header when the header grows', tops.notif.gap59 !== null && tops.notif.gap59 === tops.notif.gap0, JSON.stringify(tops.notif));
  ok('The backend-down banner clears the status bar', tops.banner >= 59, tops.banner);
  ok('A bottom sheet pads past the home indicator', tops.sheetPad >= 34, tops.sheetPad);
  await cdp.send('Emulation.setSafeAreaInsetsOverride', { insets: { top: 0, bottom: 0, left: 0, right: 0 } });
  await page.waitForTimeout(200);

  /* ---- Explore, per the 09-23 map (pass 2) ---- */
  await page.evaluate(() => show('explore')); await page.waitForTimeout(1200);
  const ex = await page.evaluate(() => {
    const r = s => { const e = document.querySelector(s); return e ? e.getBoundingClientRect() : null; };
    const chips = [...document.querySelectorAll('#exContext .ex-gesw button')];
    const cards = [...document.querySelectorAll('#exOut .cls-teaser')].slice(0, 4).map(c => {
      const t = c.querySelector('.ct').getBoundingClientRect(), s = c.querySelector('.save-ico').getBoundingClientRect();
      const nm = c.querySelector('.ct .nm'); const lh = parseFloat(getComputedStyle(nm).lineHeight);
      return { code: c.dataset.code, h: c.getBoundingClientRect().height, saveRightOfTitle: s.left >= t.right - 2 || s.left > t.left + t.width * 0.6,
               saveBesideTitle: s.top < t.bottom && s.bottom > t.top, nmLines: Math.round(nm.getBoundingClientRect().height / lh),
               desc: (c.querySelector('.cx-desc') || {}).textContent || '', facts: !!c.querySelector('.cx-facts') };
    });
    const head = document.querySelector('#exOut .ex-head');
    return { search: r('.ex-top .ex-spot'), classes: r('#ex-classes'), profs: r('#ex-profs'), seg: r('.ex-seg-v'),
             chips: chips.map(c => ({ t: c.textContent.trim(), top: c.getBoundingClientRect().top, h: c.getBoundingClientRect().height, p: c.getAttribute('aria-pressed') })),
             cards, vw: innerWidth, scrollW: document.documentElement.scrollWidth, ph: document.getElementById('exQuery').placeholder,
             head: head && { eb: (head.querySelector('.ex-eb') || {}).textContent, ht: (head.querySelector('.ex-ht') || {}).textContent,
               hs: (head.querySelector('.ex-hs') || {}).textContent, ebShown: head.querySelector('.ex-eb') && getComputedStyle(head.querySelector('.ex-eb')).display !== 'none',
               hlShown: getComputedStyle(head.querySelector('.ex-hl')).display !== 'none' },
             thumb: getComputedStyle(document.querySelector('.ex-seg-thumb')).backgroundColor,
             course: getComputedStyle(document.documentElement).getPropertyValue('--course').trim() };
  });
  ok('Explore: the question line gives its height back on a phone', await page.evaluate(() => document.querySelector('.ex-q').getBoundingClientRect().height <= 1));
  ok('Explore: …but stays a heading a screen reader can reach', await page.evaluate(() => {
    const q = document.querySelector('.ex-q'); return q.tagName === 'H2' && getComputedStyle(q).display !== 'none' && getComputedStyle(q).visibility !== 'hidden'; }));
  ok('Explore: the switch sits to the right of the search, on the same row', ex.seg.left >= ex.search.right - 1 && ex.seg.top < ex.search.bottom, `search ${Math.round(ex.search.right)} seg ${Math.round(ex.seg.left)}`);
  ok('Explore: Classes over Professors, one tall tile', ex.profs.top >= ex.classes.bottom - 2 && Math.abs(ex.profs.left - ex.classes.left) < 2);
  ok('Explore: the switch is tap-sized', ex.classes.height >= 42 && ex.profs.height >= 42, `${ex.classes.height} / ${ex.profs.height}`);
  ok('Explore: the search field is at least 200px', ex.search.width >= 200, ex.search.width);
  ok('Explore: the phone placeholder is read whole', ex.ph === 'Search classes', ex.ph);
  ok('Explore: chips are GEs · My major · Saved', ex.chips.map(c => c.t).join('|') === 'GEs|My major|Saved', ex.chips.map(c => c.t).join('|'));
  ok('Explore: chips sit on one line under the search', ex.chips.every(c => Math.abs(c.top - ex.chips[0].top) < 2) && ex.chips[0].top >= ex.search.bottom, ex.chips.map(c => Math.round(c.top)));
  ok('Explore: chips are tap-sized', ex.chips.every(c => c.h >= 42), ex.chips.map(c => Math.round(c.h)));
  ok('Explore: "My major" is the lit chip by default, and says so', ex.chips[1].p === 'true' && ex.chips[0].p === 'false' && ex.chips[2].p === 'false', ex.chips.map(c => c.p));
  ok('Explore: the Classes side is the course blue', ex.thumb !== 'rgba(0, 0, 0, 0)' && ex.thumb === await page.evaluate(c => { const d = document.createElement('i'); d.style.color = c; document.body.appendChild(d); const v = getComputedStyle(d).color; d.remove(); return v; }, ex.course), ex.thumb);
  ok('Explore: the heading is eyebrow · title · why', ex.head && ex.head.eb === 'Recommended' && ex.head.ht === 'Classes for Business Administration' && /Core and elective/.test(ex.head.hs), JSON.stringify(ex.head));
  ok('Explore: on a phone the long heading shows and the one-line label hides', ex.head && ex.head.ebShown && !ex.head.hlShown);
  ok('Explore: at least three class cards rendered', ex.cards.length >= 3, ex.cards.length);
  ok('Explore: the save mark sits beside the title', ex.cards.every(c => c.saveRightOfTitle && c.saveBesideTitle), JSON.stringify(ex.cards.map(c => [c.saveRightOfTitle, c.saveBesideTitle])));
  ok('Explore: a title gets at most two lines', ex.cards.every(c => c.nmLines <= 2), ex.cards.map(c => c.nmLines));
  ok('Explore: a card is a glance (≤ 170px)', ex.cards.every(c => c.h <= 170), ex.cards.map(c => Math.round(c.h)));
  ok('Explore: no sideways scroll at 390px', ex.scrollW <= ex.vw, `${ex.scrollW} vs ${ex.vw}`);
  /* The catalog line: Cal Poly's own sentence, the requirement sentence skipped, no full stop,
     a long one cut at a word — and a course with no catalog row keeps its units/sections line. */
  const cd = Object.fromEntries(ex.cards.map(c => [c.code, c]));
  ok('Catalog: the first descriptive sentence, not the prerequisite', cd['BUS 3346'] && cd['BUS 3346'].desc === 'Fixture text about markets, customers and the marketing mix', cd['BUS 3346'] && cd['BUS 3346'].desc);
  ok('Catalog: a long sentence is cut at a word with an ellipsis', cd['BUS 3387'] && /\S…$/.test(cd['BUS 3387'].desc) && cd['BUS 3387'].desc.length <= 97, cd['BUS 3387'] && cd['BUS 3387'].desc);
  ok('Catalog: a described card drops the units/sections line', cd['BUS 4401'] && cd['BUS 4401'].desc && !cd['BUS 4401'].facts, JSON.stringify(cd['BUS 4401']));
  ok('Catalog: the page\'s seat table and class notes are cut away; only the text after "Description" shows', cd['BUS 4401'] && cd['BUS 4401'].desc === 'Fixture text about strategy', cd['BUS 4401'] && cd['BUS 4401'].desc);
  ok('Catalog: a card with no catalog row keeps it', await page.evaluate(() => { const c = document.querySelector('#exOut .cls-teaser[data-code="BUS 3438"]');
    return !!c && !c.querySelector('.cx-desc') && !!c.querySelector('.cx-facts'); }));
  /* Saved is a view; switching sides clears it. */
  await page.evaluate(() => [...document.querySelectorAll('#exContext .ex-gesw button')].find(b => b.textContent.trim() === 'Saved').click()); await page.waitForTimeout(500);
  const sv = await page.evaluate(() => ({ head: (document.querySelector('#exOut .ex-head .ex-ht') || {}).textContent,
    codes: [...document.querySelectorAll('#exOut .cls-teaser')].map(c => c.dataset.code), want: watchClasses.slice(),
    pressed: [...document.querySelectorAll('#exContext .ex-gesw button')].map(b => b.getAttribute('aria-pressed')) }));
  ok('Saved: shows exactly the classes you saved', sv.head === 'Saved classes' && sv.codes.length === sv.want.length && sv.want.every(c => sv.codes.includes(c)), JSON.stringify(sv));
  ok('Saved: its chip is the pressed one', sv.pressed.join() === 'false,false,true', sv.pressed.join());
  const svc = await page.evaluate(() => Object.fromEntries([...document.querySelectorAll('#exOut .cls-teaser')].map(c =>
    [c.dataset.code, { desc: (c.querySelector('.cx-desc') || {}).textContent || '', facts: !!c.querySelector('.cx-facts') }])));
  ok('Catalog: initials, "e.g." and a decimal survive — the whole first sentence', svc['ECON 2303'] && svc['ECON 2303'].desc === 'Fixture study of U.S. markets, e.g. prices and 2.5 other things since 1877', JSON.stringify(svc['ECON 2303']));
  ok('Catalog: a description that is only requirements prints nothing, and the facts line stays', svc['STAT 2170'] && !svc['STAT 2170'].desc && svc['STAT 2170'].facts, JSON.stringify(svc['STAT 2170']));
  ok('Catalog: "I." before a prerequisite ends the sentence; the prerequisite never reaches the card', svc['PHIL 3331'] && svc['PHIL 3331'].desc === 'Fixture Ethics I', JSON.stringify(svc['PHIL 3331']));
  /* The splitter itself, through the shipped function: each of its two guards on its own. */
  const cs = await page.evaluate(() => [csShortLine('Design I. 3 lectures. Prerequisite: ZZZ 1000.'),
    csShortLine('Work by J. Smith and others. 3 lectures.'), csShortLine('Methods, e.g. surveys; Prerequisite: STAT 2170.')]);
  ok('Catalog: a course level "I." ends the sentence', cs[0] === 'Design I', cs[0]);
  ok('Catalog: a real initial does not', cs[1] === 'Work by J. Smith and others', cs[1]);
  ok('Catalog: a requirement clause inside a sentence is cut off', cs[2] === 'Methods, e.g. surveys', cs[2]);
  /* The shapes the real catalog run turned up (09-24, all 2,062 rows). Fixture wording, real shapes. */
  const rr = await page.evaluate(() => [
    csShortLine('Status Enrl Tot Wait Tot ZZZ 4404-X01 LEC (1234) Fixture Analysis Open 30 2'),
    csShortLine('Introduction to Hardware Description Language concepts. 1 laboratory.'),
    csShortLine('of the topic selected for this course can be found on the Selected Topic Courses webpage: https://example.edu/x Description Directed fixture study of special topics. The Class Schedule will list topic selected. Repeatable up to 6 units.'),
    csShortLine('Offered at Solano Campus. group fixture laboratory with advisors. 1 laboratory. Formerly ZZZ 492L.'),
    csShortLine('Partial fixtures. Multiple fixture integrals. Line integrals of fixture fields and many other long fixture topics.'),
    csShortLine('Writing fixture nonfiction (the memoir, the nature essay, the personal narrative, cultural criticism and more besides).'),
    csShortLine('1 laboratory. Prerequisite: ZZZ 1000.'),
    csShortLine('Formerly ZZZ 100. Fixture text after the old number.'),
    csShortLine('Status Enrl Tot Wait Tot ZZZ 1000-X01 LEC (1) Fixture Open 3 0 Description Fixture Class Notes Open 30 2 Enrl Tot.'),
    csShortLine('Status Enrl Tot Wait Tot ZZZ 2301-X01 LEC (1) Fixture Hardware Description Lang Open 5 0 Description Fixture hardware text for the card. 3 lectures.'),
    csShortLine('Status Enrl Tot Wait Tot ZZZ 2301-X01 LEC (1) Fixture Open 5 0 Notes Class Notes Also offered as ZZZ 2301. Description Introduction to Hardware Description Language concepts. Signals and gates. 3 lectures.'),
  ]);
  ok('Catalog: seat-table text with no "Description" label prints nothing', rr[0] === '', rr[0]);
  ok('Catalog: "Description" inside a real sentence is left alone', rr[1] === 'Introduction to Hardware Description Language concepts', rr[1]);
  ok('Catalog: selected-topics link and "Class Schedule will list" are cut away', rr[2] === 'Directed fixture study of special topics', rr[2]);
  ok('Catalog: the Solano campus note is lifted off, and the fragment starts with a capital', rr[3] === 'Group fixture laboratory with advisors', rr[3]);
  ok('Catalog: a two-word opening fragment takes the next sentence with it', rr[4] === 'Partial fixtures. Multiple fixture integrals', rr[4]);
  ok('Catalog: a cut never leaves a bracket open', rr[5] === 'Writing fixture nonfiction…', rr[5]);
  ok('Catalog: "1 laboratory" is format, not a description', rr[6] === '', rr[6]);
  ok('Catalog: "Formerly …" is skipped', rr[7] === 'Fixture text after the old number', rr[7]);
  ok('Catalog: page chrome after the label still prints nothing', rr[8] === '', rr[8]);
  ok('Catalog: a "Description" inside a seat-table title is not the label', rr[9] === 'Fixture hardware text for the card', rr[9]);
  ok('Catalog: a "Description" inside the real text never moves the cut (opening words kept)', rr[10] === 'Introduction to Hardware Description Language concepts', rr[10]);
  ok('Catalog: a quarter-era row attaches to nothing', await page.evaluate(() => !!COURSE_SHORT && !('BUS 346' in COURSE_SHORT)));
  /* Typing while Saved is on searches everything, and the chips say so. */
  await page.fill('#exQuery', 'BUS 3346'); await page.evaluate(() => onExSearch()); await page.waitForTimeout(500);
  const ty = await page.evaluate(() => ({ saved: window.exSaved, pressed: [...document.querySelectorAll('#exContext .ex-gesw button')].map(b => b.getAttribute('aria-pressed')).join(),
    row: (() => { const r = document.querySelector('#exOut .cls-row[data-code="BUS 3346"]'); return r ? { desc: !!r.querySelector('.cx-desc'), facts: !!r.querySelector('.cx-facts') } : null; })() }));
  ok('Saved: typing turns it off, and the chip stops saying it is on', ty.saved === false && !/true,?$/.test(ty.pressed.split(',').pop()), JSON.stringify(ty));
  ok('Search rows keep their facts line and carry no description', ty.row && !ty.row.desc && ty.row.facts, JSON.stringify(ty.row));
  await page.fill('#exQuery', ''); await page.evaluate(() => onExSearch()); await page.waitForTimeout(300);
  /* Saved back on, THEN change sides — switching must clear it. */
  await page.evaluate(() => exSetSaved(true)); await page.waitForTimeout(300);
  await page.click('#ex-profs'); await page.waitForTimeout(600);
  const pv = await page.evaluate(() => ({ saved: window.exSaved, chips: [...document.querySelectorAll('#exContext .ex-gesw button')].map(b => b.textContent.trim()),
    pressed: document.getElementById('ex-profs').getAttribute('aria-pressed'), head: (document.querySelector('#exOut .ex-head .ex-eb') || {}).textContent,
    ebColor: document.querySelector('#exOut .ex-head .ex-eb') && getComputedStyle(document.querySelector('#exOut .ex-head .ex-eb')).color,
    thumb: getComputedStyle(document.querySelector('.ex-seg-thumb')).backgroundColor,
    prof: (() => { const d = document.createElement('i'); d.style.color = getComputedStyle(document.documentElement).getPropertyValue('--prof'); document.body.appendChild(d); const v = getComputedStyle(d).color; d.remove(); return v; })(),
    ph: document.getElementById('exQuery').placeholder }));
  ok('Professors: switching sides clears Saved', pv.saved === false, pv.saved);
  ok('Professors: chips are My major · Saved', pv.chips.join('|') === 'My major|Saved', pv.chips.join('|'));
  ok('Professors: the switch reports Professors as pressed', pv.pressed === 'true', pv.pressed);
  ok('Professors: the tile turns purple', pv.thumb === pv.prof, `${pv.thumb} vs ${pv.prof}`);
  ok('Professors: the heading is "Strongest reviews", in the purple ink', pv.head === 'Strongest reviews' && pv.ebColor !== ex.thumb, `${pv.head} ${pv.ebColor}`);
  ok('Professors: placeholder follows the side', pv.ph === 'Search professors', pv.ph);
  await page.evaluate(() => { watchlist.length = 0; exSetSaved(true); }); await page.waitForTimeout(400);
  const pe = await page.evaluate(() => (document.querySelector('#exOut') || {}).textContent);
  ok('Professors: an empty Saved says how to fill it, not "no match"', /Nothing saved yet/.test(pe) && !/No professors match/.test(pe), pe.slice(0, 120));
  /* A saved professor is drawn by the real professor list: same card, same impression hook. */
  await page.evaluate(() => { const id = Object.keys(PROFESSORS).find(k => PROFESSORS[k].live); toggleWatch(id); exSetSaved(true); }); await page.waitForTimeout(500);
  const ps = await page.evaluate(() => { const c = [...document.querySelectorAll('#exOut .pcard')];
    return { n: c.length, pk: c.every(x => x.dataset.pk), head: (document.querySelector('#exOut .ex-head .ex-ht') || {}).textContent }; });
  ok('Professors: Saved shows the saved professor on the real card (data-pk for impressions)', ps.n === 1 && ps.pk && ps.head === 'Saved professors', JSON.stringify(ps));
  await page.click('#ex-classes'); await page.waitForTimeout(300);

  /* ---- Home: one window for the whole feed ---- */
  await page.evaluate(() => show('home')); await page.waitForTimeout(1200);
  const hm = await page.evaluate(() => {
    const cards = [...document.querySelectorAll('#hmFeed .cal-wrap, #hmFeed .cal-grid')];
    const grids = [...document.querySelectorAll('#hmFeed .cal-day')].map(d => d.getBoundingClientRect().height);
    const labs = [...(document.querySelector('#hmFeed') || document).querySelectorAll('.cal-hr')].map(e => e.textContent.trim());
    return { win: window._hmFeedWin, grids: [...new Set(grids.map(Math.round))], first: labs[0], labs: [...new Set(labs)] };
  });
  ok('Home: a feed window was computed from the feed', hm.win && hm.win.lo < hm.win.hi, JSON.stringify(hm.win));
  /* Fixtures: friends' earliest confirmed class starts 8:10am and their latest ends 4:00pm (the
     6pm class is MINE, not a friend's, and the feed only draws friends) → 7:40 → 7AM, 4:30 → 5PM. */
  ok('Home: the window is the feed\'s hours, not the clock\'s', hm.win && hm.win.lo === 7 * 60 && hm.win.hi === 17 * 60, JSON.stringify(hm.win));
  ok('Home: no 9 PM row on a feed whose last class ends at 4', !hm.labs.includes('9 PM') && !hm.labs.includes('7 PM'), hm.labs.join(' '));
  ok('Home: every card in the feed shares one scale', hm.grids.length === 1, hm.grids.join(','));
  /* Turned to landscape past 640px, a single-card redraw (hmExpandSettled's path, not the feed's)
     must not keep the phone window. */
  await page.setViewportSize({ width: 900, height: 390 }); await page.waitForTimeout(300);
  const land = await page.evaluate(() => { const f = (friendsList || []).find(x => x.classes && x.classes.length);
    const html = hmFriendSchedCard(f, { force: true }); return { hasWin: !!window._hmFeedWin, nine: /9 PM/.test(html) }; });
  ok('Home: past 640px a redrawn card goes back to the 7AM–10PM frame', land.nine, JSON.stringify(land));
  await page.setViewportSize({ width: 390, height: 844 }); await page.waitForTimeout(300);

  /* ---- Schedule: the sub-tabs swipe ---- */
  await page.evaluate(() => { show('sched'); setSchedTab('mine'); window.scrollTo(0, 0); }); await page.waitForTimeout(700);
  ok('Swipe: the engine knows six stops', await page.evaluate(() => window.__swipeNav && !!window.__swipeNav.stops && window.__swipeNav.stops().length === 6),
     await page.evaluate(() => window.__swipeNav && window.__swipeNav.stops ? window.__swipeNav.stops().map(s => s.t ? s.v + ':' + s.t : s.v).join(' ') : 'no stops()'));
  /* Mid-drag between two sub-tabs: the PANE follows the finger, and the title and tab row do not —
     it reads as turning a page inside Schedule, not leaving it. Checked with the finger still down. */
  const mid = await page.evaluate(async () => {
    let y = 260; for (let yy = 180; yy < innerHeight - 120; yy += 20) { const e = document.elementFromPoint(300, yy);
      if (e && !window.__swipeNav.inScroller(e)) { y = yy; break; } }
    const el = document.elementFromPoint(300, y);
    const mk = x => new Touch({ identifier: 9, target: el, clientX: x, clientY: y, pageX: x, pageY: y });
    const fire = (type, t, list) => el.dispatchEvent(new TouchEvent(type, { bubbles: true, cancelable: true, touches: list, targetTouches: list, changedTouches: [t] }));
    let t = mk(300); fire('touchstart', t, [t]);
    for (let i = 1; i <= 5; i++) { await new Promise(r => setTimeout(r, 20)); t = mk(300 - 16 * i); fire('touchmove', t, [t]); }
    const pane = document.getElementById('schedMineWrap'), row = document.getElementById('stab-mine').parentElement,
          view = document.getElementById('view-sched');
    const out = { pane: pane.style.transform, row: getComputedStyle(row).transform, view: view.style.transform };
    fire('touchcancel', t, []); return out;
  });
  ok('Mid-drag between sub-tabs: the pane moves', /translateX\(-/.test(mid.pane), mid.pane);
  ok('Mid-drag between sub-tabs: the tab row and the view stay put', mid.row === 'none' && !mid.view, JSON.stringify(mid));
  await swipe(page, -220); ok('Swipe left on My classes → My watchlist', (await where(page)) === 'sched:watch', await where(page));
  ok('…and the watchlist pane is the one on screen', (await visiblePane(page)) === 'schedWatchWrap', await visiblePane(page));
  ok('…and its tab is the lit one', await page.evaluate(() => document.getElementById('stab-watch').classList.contains('on')));
  await swipe(page, -220); ok('Swipe left on My watchlist → My planner', (await where(page)) === 'sched:plan', await where(page));
  await swipe(page, -220); ok('Swipe left on My planner → Friends', (await where(page)) === 'friends', await where(page));
  await swipe(page, 220);  ok('Swipe right on Friends → back into Schedule at My planner', (await where(page)) === 'sched:plan', await where(page));
  await swipe(page, 220); await swipe(page, 220);
  ok('Two more right → My classes', (await where(page)) === 'sched:mine', await where(page));
  await swipe(page, 220);  ok('Right again → Explore', (await where(page)) === 'explore', await where(page));
  await page.evaluate(() => { window.__stCalls = []; const o = window.setSchedTab; window.setSchedTab = function (t) { window.__stCalls.push(t); return o.apply(this, arguments); }; window.__stOrig = o; });
  await swipe(page, -220); ok('Left from Explore → Schedule at My classes', (await where(page)) === 'sched:mine', await where(page));
  ok('…rendering Schedule once, not twice', await page.evaluate(() => window.__stCalls.length === 1), await page.evaluate(() => JSON.stringify(window.__stCalls)));
  await page.evaluate(() => { window.setSchedTab = window.__stOrig; });
  /* A sideways-scrolling calendar owns its own gesture: dragging ON it scrolls it and does not turn
     the page. (The watchlist week is wider than a phone.) */
  await page.evaluate(() => { try { watchLandOn('classes'); } catch (e) {} setSchedTab('watch'); }); await page.waitForTimeout(500);
  const scroller = await page.evaluate(() => { for (let y = 200; y < innerHeight - 100; y += 10) {
      const e = document.elementFromPoint(300, y); if (e && window.__swipeNav.inScroller(e)) return y; } return null; });
  ok('Fixture: the watchlist week is a sideways scroller at 390px', scroller !== null, scroller);
  if (scroller !== null) { await swipe(page, -220, { y: scroller });
    ok('Swiping ON that scroller does not change tab', (await where(page)) === 'sched:watch', await where(page)); }
  await page.evaluate(() => setSchedTab('mine')); await page.waitForTimeout(400);
  await swipe(page, -130, { dy: 420 }); ok('A mostly-vertical drag changes nothing, even one long enough to commit sideways', (await where(page)) === 'sched:mine', await where(page));
  await swipe(page, -60, { ms: 900 }); ok('A short slow drag springs back', (await where(page)) === 'sched:mine', await where(page));
  ok('…and leaves nothing half-slid', await page.evaluate(() =>
    [...document.querySelectorAll('.view, .swp')].every(e => !e.style.transform && !e.classList.contains('sw-drag'))));
  await page.evaluate(() => show('home')); await page.waitForTimeout(500);
  await swipe(page, 220); ok('Right on Home goes nowhere (no wrap)', (await where(page)) === 'home', await where(page));
  /* …and it does not even start to move: at the end of the row the page stays still under the finger,
     which is how "there is nothing there" reads without a bounce animation saying it. */
  const endDrag = await page.evaluate(async () => {
    const y = 400, el = document.elementFromPoint(120, y);
    const mk = x => new Touch({ identifier: 11, target: el, clientX: x, clientY: y, pageX: x, pageY: y });
    const fire = (type, t, list) => el.dispatchEvent(new TouchEvent(type, { bubbles: true, cancelable: true, touches: list, targetTouches: list, changedTouches: [t] }));
    let t = mk(120); fire('touchstart', t, [t]);
    for (let i = 1; i <= 5; i++) { await new Promise(r => setTimeout(r, 20)); t = mk(120 + 20 * i); fire('touchmove', t, [t]); }
    const tr = document.getElementById('view-home').style.transform; fire('touchcancel', t, []); return tr;
  });
  ok('Mid-drag past the first stop: Home does not move', !endDrag, endDrag);
  /* The buttons are still the primary control. */
  await page.evaluate(() => show('sched')); await page.waitForTimeout(400);
  await page.click('#stab-plan'); await page.waitForTimeout(500);
  ok('Tapping a sub-tab still works', (await where(page)) === 'sched:plan', await where(page));

  ok('Phone: no page errors', log.errors.length === 0, log.errors.slice(0, 3).join(' | '));
  await close();
}

/* ============================== CATALOG, PARTIAL READ ============================== */
{
  /* 1,001 rows: the first page of 1,000 arrives, the second fails. Publishing the first page would
     strip descriptions from every course past it, so nothing may be published at all. */
  const FX = await import('./harness/fixtures.mjs');
  const many = Array.from({ length: 1001 }, (_, i) => ({ course_code: 'ZZZ ' + (1000 + i), description: 'Fixture padding row ' + i + '.' }));
  const { page, close } = await openApp({ file: FILE, port: 8144 + PB, tables: { ...FX.TABLES, course_catalog: [...FX.CATALOG, ...many] },
    hook: (url) => (url.pathname === '/rest/v1/course_catalog' && +url.searchParams.get('offset') >= 1000) ? { status: 500, body: '{}' } : null });
  await page.waitForTimeout(2500);
  const r = await page.evaluate(() => ({ short: COURSE_SHORT, cache: localStorage.getItem('professify_course_short') }));
  ok('Catalog: a read that fails on page two publishes nothing', r.short === null && r.cache === null, JSON.stringify(r).slice(0, 120));
  await close();
}

/* ============================== SIGN-IN, KEYBOARD UP ============================== */
{
  /* The first screen a new student sees, at the height it has with the keyboard open (390×430),
     under a 59px status bar: the card must start below the bar and its last button must be
     reachable by scrolling inside the card. */
  const { page, ctx, close, log } = await openApp({ file: FILE, port: 8143 + PB, signedIn: false, height: 430 });
  const cdp = await ctx.newCDPSession(page);
  await cdp.send('Emulation.setSafeAreaInsetsOverride', { insets: { top: 59, bottom: 0, left: 0, right: 0 } });
  await page.evaluate(() => openAuth()); await page.waitForTimeout(600);
  const a = await page.evaluate(() => { const p = document.querySelector('.auth-panel'); p.scrollTop = 1e6;
    const r = p.getBoundingClientRect(); const btns = [...p.querySelectorAll('button')].filter(b => b.offsetParent);
    const last = btns[btns.length - 1].getBoundingClientRect();
    return { top: Math.round(r.top), lastBottom: Math.round(last.bottom), vh: innerHeight }; });
  ok('Sign-in (keyboard up): the card starts below a 59px status bar', a.top >= 59, JSON.stringify(a));
  ok('Sign-in (keyboard up): its last button is reachable', a.lastBottom <= a.vh, JSON.stringify(a));
  ok('Sign-in: no page errors', log.errors.length === 0, log.errors.slice(0, 3).join(' | '));
  await close();
}

/* ============================== DESKTOP ============================== */
{
  const { page, close, log } = await openApp({ file: FILE, width: 1280, height: 900, port: 8142 + PB });
  await page.evaluate(() => show('explore')); await page.waitForTimeout(900);
  const d = await page.evaluate(() => {
    const c = document.getElementById('ex-classes').getBoundingClientRect(), p = document.getElementById('ex-profs').getBoundingClientRect();
    const q = document.querySelector('.ex-q');
    return { stacked: p.top >= c.bottom - 2, q: q && q.getBoundingClientRect().height,
             padTop: getComputedStyle(document.querySelector('header.nav')).paddingTop };
  });
  ok('Desktop: Explore keeps its vertical switch', d.stacked);
  ok('Desktop: Explore keeps its question line', d.q > 0, d.q);
  ok('Desktop: the heading keeps its one-line label', await page.evaluate(() => { const h = document.querySelector('#exOut .ex-head');
    return !!h && getComputedStyle(h.querySelector('.ex-hl')).display !== 'none' && getComputedStyle(h.querySelector('.ex-ht')).display === 'none'; }));
  ok('Desktop: the header gains no padding with no inset', d.padTop === '0px', d.padTop);
  await page.evaluate(() => show('home')); await page.waitForTimeout(1200);
  const w = await page.evaluate(() => ({ win: window._hmFeedWin, labs: [...new Set([...document.querySelectorAll('#hmFeed .cal-hr')].map(e => e.textContent.trim()))] }));
  ok('Desktop: the feed keeps the fixed 7AM–10PM frame', !w.win && w.labs[0] === '7 AM' && w.labs.includes('9 PM'), JSON.stringify(w));
  ok('Desktop: no page errors', log.errors.length === 0, log.errors.slice(0, 3).join(' | '));
  await close();
}

const bad = R.filter(r => !r.c);
for (const r of R) console.log(`${r.c ? '  ok ' : 'FAIL '} ${r.n}${r.c ? '' : '  — ' + r.d}`);
console.log(bad.length ? `\nFAIL check-mobile: ${R.length - bad.length} passed, ${bad.length} failed`
                       : `\ncheck-mobile: ${R.length} passed, 0 failed`);
process.exit(bad.length ? 1 : 0);
