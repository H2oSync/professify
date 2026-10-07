/* check-desktop-look — the website in the app's look, pass 1 (2026-10-04). Runs the REAL index.html in
   Chromium, signed in, with the real supabase-js against the same PostgREST stand-in as check-app.
   Run: APP_DIR=<repo> node check-desktop-look.mjs [--only name] [--quiet]   (APP_PORT to move off 8190)
   Every promise here is one Tate made or one the app's own look makes: light by default, dark only when
   chosen, cream gone; the app's tabs in the app's order, on the right; Nunito; the app's cards, blocks,
   chips and rating scale; and every text colour readable on its ground in BOTH themes. */
import { openApp } from './app-harness.mjs';

const args = process.argv.slice(2);
const ONLY = args.includes('--only') ? args[args.indexOf('--only') + 1] : null;
const QUIET = args.includes('--quiet');
let pass = 0, fail = 0; const fails = [];
function ok(c, name, info) {
  if (c) { pass++; if (!QUIET) console.log('  ok  ', name); }
  else { fail++; fails.push(name); console.log('  FAIL', name, info !== undefined ? '→ ' + JSON.stringify(info).slice(0, 300) : ''); }
}
const tick = async (p, ms = 400) => { await p.clock.runFor(ms); await p.waitForTimeout(250); };
const desk = (o = {}) => openApp(Object.assign({ path: '/', width: 1440, height: 900, wait: 4000 }, o));
const withTheme = t => (t == null ? `try{localStorage.removeItem('professify-theme')}catch(e){}` : `try{localStorage.setItem('professify-theme',${JSON.stringify(t)})}catch(e){}`);
const T = {};
const test = (name, fn) => { T[name] = fn; };

/* WCAG contrast of two computed colours, measured in the page */
const CONTRAST = `window.__con = function(fg, bg){
  const c = document.createElement('canvas').getContext('2d');
  const rgb = s => { c.fillStyle = '#000'; c.fillStyle = s; c.fillRect(0,0,1,1); const d = c.getImageData(0,0,1,1).data; c.clearRect(0,0,1,1); return [d[0],d[1],d[2]]; };
  const L = a => { const f = v => { v /= 255; return v <= .03928 ? v / 12.92 : Math.pow((v + .055) / 1.055, 2.4); }; return .2126*f(a[0]) + .7152*f(a[1]) + .0722*f(a[2]); };
  const a = L(rgb(fg)), b = L(rgb(bg)); return (Math.max(a,b) + .05) / (Math.min(a,b) + .05);
};
window.__var = function(name){ if (!getComputedStyle(document.documentElement).getPropertyValue(name).trim()) throw new Error('token not defined: ' + name); const e = document.createElement('span'); e.style.color = 'var(' + name + ')'; document.body.appendChild(e); const v = getComputedStyle(e).color; e.remove(); return v; };`;

test('themes', async () => {
  { const { page, close, log } = await desk({ init: withTheme(null) }); await tick(page, 1500);
    const r = await page.evaluate(() => ({ t: document.documentElement.getAttribute('data-theme'), bg: getComputedStyle(document.body).backgroundColor }));
    ok(r.t === 'light' && r.bg === 'rgb(244, 246, 251)', 'nothing saved → light, on the app\'s page grey #F4F6FB', r);
    const hd = await page.evaluate(() => { const e = document.getElementById('app-look-tokens'); return e && { inHead: e.parentElement === document.head, media: e.media, on: !e.sheet.disabled, bg: /--bg:#F4F6FB/.test(e.textContent), font: /font-family:'Nunito'/.test(e.textContent) }; });
    ok(hd && hd.inHead && !hd.media && hd.on && hd.bg && hd.font, 'the app\'s tokens and face are in the head, so the first paint is already the new look', hd);
    ok(log.errors.length === 0, 'no page errors (default)', log.errors); await close(); }
  { const { page, close } = await desk({ init: withTheme(null), port: +(process.env.APP_PORT || 8190) });
    /* a student whose OS is dark still starts light: dark is only by choice */
    await page.emulateMedia({ colorScheme: 'dark' }); await page.reload(); await tick(page, 1500);
    ok(await page.evaluate(() => document.documentElement.getAttribute('data-theme')) === 'light', 'a dark OS with nothing saved still opens light'); await close(); }
  { const { page, close } = await desk({ init: withTheme('cream') }); await tick(page, 1500);
    ok(await page.evaluate(() => document.documentElement.getAttribute('data-theme')) === 'light', 'a saved cream (retired) opens light'); await close(); }
  { const { page, close, log } = await desk({ init: withTheme('dark') }); await tick(page, 1500);
    const r = await page.evaluate(() => ({ t: document.documentElement.getAttribute('data-theme'), bg: getComputedStyle(document.body).backgroundColor, card: getComputedStyle(document.querySelector('.hm-card')).backgroundColor }));
    ok(r.t === 'dark' && r.bg === 'rgb(11, 17, 32)' && r.card === 'rgb(21, 29, 46)', 'a saved dark opens dark, on the dark palette', r);
    ok(log.errors.length === 0, 'no page errors (dark)', log.errors); await close(); }
});

test('settingsTheme', async () => {
  const { page, close } = await desk({ init: withTheme(null) }); await tick(page, 1500);
  await page.evaluate(() => openSettings()); await tick(page, 400);
  const labels = await page.evaluate(() => [...document.querySelectorAll('#setTheme button')].map(b => b.textContent.trim()));
  ok(JSON.stringify(labels) === '["Light","Dark"]', 'Settings offers Light and Dark only (no Cream)', labels);
  ok(!/Cream/.test(await page.evaluate(() => document.getElementById('st-appearance').textContent)), 'Settings never mentions Cream');
  ok(await page.evaluate(() => document.querySelector('#setTheme button.on').textContent.trim()) === 'Light', 'Light is the lit choice by default');
  await page.evaluate(() => { const b = [...document.querySelectorAll('#setTheme button')].find(x => x.textContent.trim() === 'Dark'); b.click(); }); await tick(page, 300);
  let r = await page.evaluate(() => ({ t: document.documentElement.getAttribute('data-theme'), s: localStorage.getItem('professify-theme'), on: document.querySelector('#setTheme button.on').textContent.trim(), bg: getComputedStyle(document.body).backgroundColor }));
  ok(r.t === 'dark' && r.s === 'dark' && r.on === 'Dark' && r.bg === 'rgb(11, 17, 32)', 'Dark switches the page and is remembered', r);
  await page.evaluate(() => { document.documentElement.style.setProperty('--accent', '#4CAF82'); setTheme('light'); }); await tick(page, 200);
  ok(await page.evaluate(() => document.documentElement.style.getPropertyValue('--accent')) === '', 'switching theme never leaves the school\'s green painted inline');
  await page.evaluate(() => setTheme('cream')); await tick(page, 200);
  ok(await page.evaluate(() => document.documentElement.getAttribute('data-theme')) === 'light', 'setTheme(cream) lands on light');
  await close();
});

test('topBar', async () => {
  const { page, close } = await desk({ init: withTheme(null) }); await tick(page, 1500);
  const r = await page.evaluate(() => {
    const bs = [...document.querySelectorAll('nav.tabs button')].filter(b => b.offsetWidth > 0);
    const box = e => e.getBoundingClientRect();
    return { labels: bs.map(b => [...b.querySelectorAll(':scope > span:not(.tpill)')].filter(x => !/badge/.test(x.className) && !x.hidden).pop().textContent.trim()), tabsL: box(document.querySelector('nav.tabs')).left, brandR: box(document.querySelector('.brand')).right,
      bell: box(document.querySelector('.notif-wrap')).left, tabsR: box(document.querySelector('nav.tabs')).right, vw: innerWidth,
      wm: (document.querySelector('.brand .brand-wm') || {}).textContent, aria: document.querySelector('.brand').getAttribute('aria-label') };
  });
  ok(JSON.stringify(r.labels) === '["Home","Explore","Rate","Schedule","Friends"]', 'the app\'s five tabs, in the app\'s order', r.labels);
  ok(r.tabsL - r.brandR > 120 && r.bell >= r.tabsR && r.bell - r.tabsR < 40, 'the tabs sit on the right, with the bell after them (Tate: keep the toolbar on the right)', r);
  ok(r.wm === 'TermChamp' && r.aria === 'TermChamp — go to home', 'the wordmark beside the mark; the button still names the app', r);
  const act = await page.evaluate(() => { const b = document.getElementById('tab-home'), pl = b.querySelector('.tpill'); return { c: getComputedStyle(b).color, p: pl && getComputedStyle(pl).backgroundColor, other: getComputedStyle(document.getElementById('tab-explore').querySelector('.tpill')).backgroundColor }; });
  ok(act.c === 'rgb(29, 78, 216)' && act.p === 'rgb(227, 236, 255)' && act.other === 'rgba(0, 0, 0, 0)', 'the active tab is blue in a light-blue pill, the others plain', act);
  await page.evaluate(() => show('sched')); await tick(page, 300);
  ok(await page.evaluate(() => document.getElementById('tab-sched').classList.contains('active') && !document.getElementById('tab-home').classList.contains('active')), 'the pill follows the screen');
  await page.click('#tab-rate'); await tick(page, 500);
  ok(await page.evaluate(() => { const b = document.getElementById('rlBack'); return !!b && getComputedStyle(b).display !== 'none' && b.getBoundingClientRect().height > 0; }), 'Rate opens Review a professor');
  await close();
});

test('type', async () => {
  const { page, close } = await desk({ init: withTheme(null) }); await tick(page, 1500);
  const r = await page.evaluate(async () => { await document.fonts.ready; return { ff: getComputedStyle(document.body).fontFamily, loaded: [...document.fonts].some(f => f.family.replace(/["']/g, '') === 'Nunito' && f.status === 'loaded'), h: getComputedStyle(document.querySelector('.hm-ct')).fontWeight, mono: getComputedStyle(document.documentElement).getPropertyValue('--mono').trim() }; });
  ok(/^"?Nunito/.test(r.ff) && r.loaded, 'the page is set in the app\'s Nunito, embedded (no network)', r);
  ok(+r.h >= 800, 'card titles are the app\'s heavy 800', r.h);
  ok(/^'?Nunito/.test(r.mono), 'course codes in Nunito too, like the app\'s chips', r.mono);
  await close();
});

test('cards', async () => {
  for (const th of ['light', 'dark']) {
    const { page, close } = await desk({ init: withTheme(th) }); await tick(page, 1500);
    const r = await page.evaluate(() => { const c = getComputedStyle(document.querySelector('.hm-card')); return { rad: c.borderTopLeftRadius, sh: c.boxShadow, bc: c.borderTopColor }; });
    ok(r.rad === '24px' && r.sh !== 'none' && /rgba\(0, 0, 0, 0\)|transparent/.test(r.bc), th + ': Home cards are the app\'s 24px card with a shadow and no hairline', r);
    const b = await page.evaluate(() => { const e = document.querySelector('.cal-block:not(.wl):not(.bad):not(.theirs)'); if (!e) return null; const c = getComputedStyle(e); const code = e.querySelector('.cb-code'); return { bg: c.backgroundColor, ink: getComputedStyle(code || e).color }; });
    const want = th === 'light' ? ['rgb(214, 228, 255)', 'rgb(30, 64, 175)'] : ['rgb(37, 57, 106)', 'rgb(220, 231, 255)'];
    ok(b && b.bg === want[0] && b.ink === want[1], th + ': class blocks are the app\'s soft blue with dark-blue text', b);
    await page.evaluate(CONTRAST);
    const pill = await page.evaluate(() => { const blk = document.createElement('div'); blk.className = 'cal-block'; blk.style.cssText = 'position:fixed;left:0;top:0;width:120px;height:60px';
      blk.innerHTML = '<span class="mode-pill">Async</span>'; document.body.appendChild(blk); const p = blk.querySelector('.mode-pill');
      const k = window.__con(getComputedStyle(p).color, getComputedStyle(blk).backgroundColor); blk.remove(); return +k.toFixed(2); });
    ok(pill >= 4.5, th + ': an Async / Time TBA pill on a class block reads (it was white on the old solid block)', pill);
    await close();
  }
});

test('accent', async () => {
  const { page, close } = await desk({ init: withTheme(null) }); await tick(page, 2500);
  const r = await page.evaluate(() => ({ inline: document.documentElement.style.getPropertyValue('--accent'), acc: getComputedStyle(document.documentElement).getPropertyValue('--accent').trim(), rate: getComputedStyle(document.querySelector('.hm-ratebtn')).backgroundColor }));
  ok(r.inline === '' && r.acc === '#2563EB', 'signed in, the school colour no longer paints an inline green accent', r);
  ok(r.rate === 'rgb(37, 99, 235)', 'Rate a professor is the app\'s solid blue', r.rate);
  await page.evaluate(() => { document.documentElement.style.setProperty('--accent', '#4CAF82'); applySchoolTheme('Cal Poly, San Luis Obispo'); }); await tick(page, 100);
  ok(await page.evaluate(() => document.documentElement.style.getPropertyValue('--accent')) === '', 'an old inline accent is cleared by applySchoolTheme');
  await page.evaluate(() => show('explore')); await tick(page, 500);
  const c = await page.evaluate(() => { const e = document.querySelector('.cx-badge'); return e && { bg: getComputedStyle(e).backgroundColor, c: getComputedStyle(e).color }; });
  ok(c && c.bg === 'rgb(227, 236, 255)' && c.c === 'rgb(30, 64, 175)', 'course codes are the app\'s soft-blue chip', c);
  await close();
});

test('ratings', async () => {
  const { page, close } = await desk({ init: withTheme(null) }); await tick(page, 1500);
  const r = await page.evaluate(() => ({
    five: scoreColor(4), four: scoreColor(3.2), half: scoreColor(0.4), none: scoreColor(null), three6: scoreColor(3.6 / 5 * 4),
    tint: profTintStyle(4), tintLow: profTintStyle(0.4) }));
  ok(r.five === 'var(--rt-10)' && r.four === 'var(--rt-8)' && r.half === 'var(--rt-1)' && r.none === 'var(--faint)' && r.three6 === 'var(--rt-7)', 'scoreColor follows the app\'s ten half-star steps', r);
  ok(/background:#1AA248/.test(r.tint) && /color:#052911/.test(r.tint) && /background:#E46258/.test(r.tintLow), 'professor tiles take the app\'s rating fill and ink', r);
  const num = await page.evaluate(() => { const e = document.querySelector('[style*="var(--rt-"]'); const body = getComputedStyle(document.body).color; return e && { c: getComputedStyle(e).color, s: e.getAttribute('style'), body }; });
  ok(num && /--rt-\d/.test(num.s) && num.c !== num.body, 'a rating on Home is drawn from the scale (not the body ink)', num);
  ok(await page.evaluate(() => scoreColor(4, 'fill') === 'var(--rtf-10)' && ratingTint(4) === '#1AA248' && ratingInk('#1AA248') === '#052911'), 'shapes take the bright fill; every rating tile is the app\'s fill and ink');
  const dot = await page.evaluate(() => { const box = document.createElement('div'); box.innerHTML = rateHtml(3.2); document.body.appendChild(box); const e = box.querySelector('.rd'); return e && { bg: getComputedStyle(e).backgroundColor, s: e.getAttribute('style') }; });
  ok(dot && /--rtf-\d/.test(dot.s), 'a rating\'s dot is the bright fill, not near-black ink', dot);
  await close();
  const d = await desk({ init: withTheme('dark') }); await tick(d.page, 1500);
  const dn = await d.page.evaluate(() => { const e = document.querySelector('[style*="var(--rt-"]'); return e && getComputedStyle(e).color; });
  ok(dn && dn !== 'rgb(234, 240, 248)', 'dark: ratings on Home are drawn from the dark scale', dn);
  await d.close();
});

test('contrast', async () => {
  for (const th of ['light', 'dark']) {
    const { page, close } = await desk({ init: withTheme(th) }); await tick(page, 1500);
    await page.evaluate(CONTRAST);
    const r = await page.evaluate(() => {
      const v = window.__var, k = window.__con, out = {};
      out.text = k(v('--text'), v('--panel')); out.text2 = k(v('--text-2'), v('--panel')); out.muted = k(v('--muted'), v('--panel'));
      out.mutedBg = k(v('--muted'), v('--bg')); out.acc = k(v('--accent'), v('--panel')); out.btn = k(v('--accent-ink'), v('--accent'));
      out.blk = k(v('--blk-ink'), v('--blk')); out.chip = k(v('--blue-ink'), v('--blue-soft')); out.cls = k(v('--clsblk-ink'), v('--clsblk'));
      out.good = k(v('--good'), v('--panel')); out.low = k(v('--low'), v('--panel')); out.mid = k(v('--mid'), v('--panel')); out.tab = k(v('--tab-on'), v('--blue-soft'));
      out.prof = k(v('--accent-ink'), v('--prof-fill')); out.faint = k(v('--faint'), v('--panel'));
      out.rt = []; for (let i = 1; i <= 10; i++) out.rt.push(+k(v('--rt-' + i), v('--panel')).toFixed(2));
      return out;
    });
    const low = Object.entries(r).filter(([n, x]) => n !== 'rt' && x < 4.5).map(([n, x]) => n + ' ' + x.toFixed(2));
    ok(low.length === 0, th + ': every token pair clears 4.5:1 (text, muted, accent, buttons, blocks, chips, tabs, good/mid/low)', low);
    ok(r.rt.every(x => x >= 4.5), th + ': every rating step reads at 4.5:1 on a card', r.rt);
    await close();
  }
});

test('narrow', async () => {
  /* the bar must never scroll sideways: iPad portrait, a half-screen laptop, small laptops */
  for (const w of [641, 700, 768, 820, 900, 1024, 1140, 1280, 1300, 1440]) {
    const { page, close } = await desk({ init: withTheme(null), width: w }); await tick(page, 1200);
    const r = await page.evaluate(() => ({ sw: document.documentElement.scrollWidth, vw: innerWidth, nav: document.querySelector('.nav-inner').scrollWidth, navW: document.querySelector('.nav-inner').clientWidth }));
    ok(r.sw <= r.vw && r.nav <= r.navW + 1, 'at ' + w + 'px nothing scrolls sideways and the bar fits', r);
    await close();
  }
});

test('rendered', async () => {
  /* every piece of visible text against what is really behind it, on the main screens, in both themes —
     a token pair can pass while a rule paints white on a light token. 4.5:1, or 3:1 for large text. */
  const SWEEP = `window.__sweep = function(){
    const c = document.createElement('canvas').getContext('2d');
    const rgba = s => { const m = s.match(/rgba?\\(([^)]+)\\)/); if (!m) return null; const p = m[1].split(/[ ,\\/]+/).filter(Boolean).map(Number); return [p[0], p[1], p[2], p.length > 3 ? p[3] : 1]; };
    const L = a => { const f = v => { v /= 255; return v <= .03928 ? v / 12.92 : Math.pow((v + .055) / 1.055, 2.4); }; return .2126*f(a[0]) + .7152*f(a[1]) + .0722*f(a[2]); };
    const bgOf = el => { const chain = []; for (let e = el; e; e = e.parentElement) { const cs = getComputedStyle(e); if (cs.backgroundImage !== 'none' && !/gradient/.test(cs.backgroundImage)) return null; if (/gradient/.test(cs.backgroundImage)) return null; const b = rgba(cs.backgroundColor); if (b && b[3] > 0) chain.push(b); if (b && b[3] >= 1) break; }
      let out = [255, 255, 255]; const root = rgba(getComputedStyle(document.body).backgroundColor); if (root) out = root.slice(0, 3);
      for (let i = chain.length - 1; i >= 0; i--) { const b = chain[i]; out = [0, 1, 2].map(j => b[j] * b[3] + out[j] * (1 - b[3])); } return out; };
    const bad = []; const seen = new Set();
    const w = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
    let n; while ((n = w.nextNode())) {
      const t = n.nodeValue.trim(); if (!t || t.length < 2) continue; const el = n.parentElement; if (!el || seen.has(el)) continue; seen.add(el);
      const r = el.getBoundingClientRect(); if (!r.width || !r.height || r.bottom < 0 || r.top > innerHeight * 3) continue;
      let hid = false, op = 1; for (let e = el; e; e = e.parentElement) { const cs = getComputedStyle(e); if (cs.visibility === 'hidden' || cs.display === 'none') hid = true; op *= +cs.opacity; } if (hid || op < .95) continue;
      if (el.closest('[disabled],[aria-disabled="true"],svg,.hawk-root,#hawk,.hk-root')) continue;
      if (el.closest('.ex-seg-v')) continue;   /* its highlight is a sibling element; measured on its own below */
      const cs = getComputedStyle(el); const fg = rgba(cs.color); if (!fg) continue; const bg = bgOf(el); if (!bg) continue;
      const f = [0, 1, 2].map(j => fg[j] * fg[3] + bg[j] * (1 - fg[3]));
      const a = L(f), b = L(bg); const k = (Math.max(a, b) + .05) / (Math.min(a, b) + .05);
      const px = parseFloat(cs.fontSize), wt = +cs.fontWeight; const large = px >= 24 || (px >= 18.66 && wt >= 700);
      if (k < (large ? 3 : 4.5)) bad.push((el.className && typeof el.className === 'string' ? '.' + el.className.split(' ')[0] : el.tagName) + ' "' + t.slice(0, 24) + '" ' + k.toFixed(2));
    }
    return bad;
  };`;
  const screens = [['Home', () => show('home')], ['Explore', () => show('explore')], ['class page', () => openClassPage('BUS 3438')],
    ['Schedule', () => show('sched')], ['Plans', () => { show('sched'); setSchedTab('watch'); }], ['Friends', () => show('friends')], ['Settings', () => openSettings()],
    ['a professor', () => openProf(Object.keys(PROFESSORS).find(k => /examplewood/i.test(PROFESSORS[k].name)))], ['Rate', () => openRate()]];
  for (const th of ['light', 'dark']) {
    const { page, close } = await desk({ init: withTheme(th) }); await tick(page, 1500);
    await page.evaluate(SWEEP);
    for (const [nm, fn] of screens) {
      await page.evaluate(fn); await tick(page, 700); await page.evaluate(() => scrollTo(0, 0));
      await page.waitForTimeout(1800);   /* CSS fades run on real time, not the test clock: sample when they are done */
      const bad = await page.evaluate(() => window.__sweep());
      ok(bad.length === 0, th + ': every word on ' + nm + ' reads at 4.5:1 (3:1 large) on what is behind it', bad.slice(0, 12));
    }
    await page.evaluate(() => { closeReviewLanding && closeReviewLanding(); show('explore'); }); await tick(page, 600); await page.waitForTimeout(800);
    await page.evaluate(CONTRAST);
    const seg = await page.evaluate(() => { const b = document.querySelector('.ex-seg-v button.active'), t = document.querySelector('.ex-seg-thumb'); return b && t && +window.__con(getComputedStyle(b).color, getComputedStyle(t).backgroundColor).toFixed(2); });
    ok(seg >= 4.5, th + ': Explore\'s Classes / Professors label reads on its highlight', seg);
    await close();
  }
});

/* ---- pass 2 (2026-10-04): each screen's LAYOUT in the app's, from the canvas Tate approved ---- */
test('layoutHome', async () => {
  for (const th of ['light', 'dark']) {
    const { page, close } = await desk({ init: withTheme(th) }); await tick(page, 1500); await page.waitForTimeout(1200); await tick(page, 400);
    await page.evaluate(CONTRAST);
    const r = await page.evaluate(() => {
      const w = document.querySelector('.wrap.hm-wrap'), cs = getComputedStyle(w), nav = document.querySelector('header.nav .nav-inner');
      const cols = cs.gridTemplateColumns.split(' ').map(parseFloat);
      const days = [...document.querySelectorAll('#hmFeed .cal-mini .cal-col:not(.cal-any) .cal-day')].map(e => e.offsetHeight);
      const times = [...document.querySelectorAll('#hmFeed .cal-block .cb-time')].map(e => e.textContent);
      const chips = [...document.querySelectorAll('#view-home .pr-chip')].map(e => ({ t: e.textContent, con: +window.__con(getComputedStyle(e).color, getComputedStyle(e).backgroundColor).toFixed(2) }));
      const stars = [...document.querySelectorAll('#hmRailR .hm-prow .pr-stars')].filter(e => e.offsetParent).length;
      const today = [...document.querySelectorAll('#hmFeed .cal-dh.cal-today')].map(e => e.textContent);
      const av = [...document.querySelectorAll('#hmFeed .av-line')].map(e => ({ c: e.className, dot: getComputedStyle(e, '::before').backgroundColor }));
      const rate = document.querySelector('.hm-ratebtn').offsetHeight;
      const idbg = getComputedStyle(document.querySelector('.hm-id .idhead')).backgroundColor;
      return { maxW: cs.maxWidth, cols, wl: w.getBoundingClientRect().left, nl: nav.getBoundingClientRect().left, wpad: parseFloat(getComputedStyle(w).paddingLeft), npad: parseFloat(getComputedStyle(nav).paddingLeft), days, times, chips, stars, today, av, rate, idbg };
    });
    if (th === 'light') {
      ok(r.maxW === '1240px' && Math.round(r.cols[0]) === 290 && Math.round(r.cols[2]) === 310, 'Home is the canvas\'s 1240px page in three columns, 290 / the feed / 310', r);
      ok(Math.abs((r.wl + r.wpad) - (r.nl + r.npad)) <= 1, 'the header row lines up with the page under it', r);
      ok(r.days.length >= 5 && new Set(r.days).size === 1 && r.days[0] < Math.round(15 * 60 * 0.64), 'every friend\'s week shares ONE window, fitted to the feed (shorter than 7a–10p)', r.days.slice(0, 12));
      ok(r.times.length > 0 && r.times.every(t => /^\d{1,2}:\d\d–\d{1,2}:\d\d[ap]$/.test(t)), 'blocks say their time in the app\'s "10:10–12:00p"', r.times.slice(0, 6));
      ok(r.today.length > 0 && r.today.every(t => /tu/i.test(t)), 'today (Tuesday in the fixture) carries the app\'s dot on every card', r.today);
      ok(r.av.length > 0 && r.av.every(a => /av-(class|open)/.test(a.c) && a.dot !== 'rgba(0, 0, 0, 0)'), 'the where-they-are line carries its coloured dot', r.av);
      ok(r.stars === 0, 'the five-star row under each professor is gone — the chip says it', r.stars);
      ok(r.rate === 54, 'the app\'s 54px Rate button', r.rate);
      ok(r.idbg === 'rgba(0, 0, 0, 0)', 'the profile card is white, not a blue band', r.idbg);
    }
    ok(r.chips.length >= 3 && r.chips.every(c => /^★\d\.\d$/.test(c.t) && c.con >= 4.5), th + ': professors\' scores are "★ 4.5" chips that read at 4.5:1', r.chips);
    await close();
  }
  /* every block's code and time sit whole inside it, from a phone to a wide screen (review, 2026-10-04) */
  const CLIP = () => { const bad = [];
    document.querySelectorAll('#hmFeed .cal-block:not(.narrow)').forEach(b => { const br = b.getBoundingClientRect();
      b.querySelectorAll('.cb-code,.cb-time').forEach(t => { const r = t.getBoundingClientRect();
        if (r.right > br.right + 0.5 || r.bottom > br.bottom + 0.5) bad.push(t.textContent + ' ' + Math.round(br.width) + 'x' + Math.round(br.height)); }); });
    return bad; };
  for (const w of [390, 1140, 1200, 1300, 1440]) {
    const { page, close } = await desk({ init: withTheme(null), width: w, height: 900 }); await tick(page, 1500); await page.waitForTimeout(900);
    const bad = await page.evaluate(CLIP);
    ok(bad.length === 0, 'at ' + w + 'px every feed block\'s code and time fit inside it', bad.slice(0, 8)); await close(); }
  { const { page, close } = await desk({ init: withTheme(null), width: 1140 }); await tick(page, 1500); await page.waitForTimeout(900);
    const r = await page.evaluate(() => { const c = document.querySelector('.hm-wcard .hm-ct'); return c ? { sw: c.scrollWidth, cw: c.clientWidth } : null; });
    ok(!r || r.sw <= r.cw + 1, 'at 1140px the card titles and their links fit', r); await close(); }
});

test('layoutClass', async () => {
  for (const w of [1440, 900]) {
    const { page, close } = await desk({ init: withTheme(null), width: w }); await tick(page, 1500);
    await page.evaluate(() => openClassPage('BUS 3431')); await tick(page, 800); await page.waitForTimeout(500);
    const r = await page.evaluate(() => {
      const h = document.querySelector('#view-class .cp-hero'), t = document.querySelector('#view-class .cp-title');
      const st = [...document.querySelectorAll('#view-class .cp-st')].map(e => Math.round(e.getBoundingClientRect().top));
      const side = document.querySelector('#view-class .cp-side'), main = document.querySelector('#view-class .cp-main');
      const hs = side ? [...side.querySelectorAll('.cps-h')].map(e => e.textContent) : [];
      return { bg: getComputedStyle(h).backgroundColor, fs: getComputedStyle(t).fontSize, st, hs, sl: side && side.getBoundingClientRect().left, mr: main && main.getBoundingClientRect().right, st0: side && side.getBoundingClientRect().top, mb: main && main.getBoundingClientRect().bottom, profs: side ? side.querySelectorAll('.cps-prof').length : 0 };
    });
    if (w === 1440) {
      ok(r.bg === 'rgb(37, 99, 235)' && r.fs === '40px', 'the class page opens on the app\'s blue hero with the 40px title', r);
      ok(r.st.length === 4 && new Set(r.st).size === 1, 'Units · Sections · Meets · Seats sit as four tiles in one row', r.st);
      ok(r.hs.join('|') === 'Friends taking it|Who teaches it' && r.profs === 2, 'the right column says who you know in it and who teaches it', r);
      ok(r.sl > r.mr, 'at 1440px that column is beside the sections', r);
      await page.evaluate(() => document.querySelector('#view-class .cps-prof').click()); await tick(page, 600);
      const v = await page.evaluate(() => document.querySelector('.view.active').id);
      ok(v === 'view-prof', 'a professor in the column opens their page', v);
    } else ok(r.st0 >= r.mb - 1, 'under 1140px the column drops below the sections', r);
    await close();
  }
});

test('layoutScreens', async () => {
  const { page, close } = await desk({ init: withTheme(null) }); await tick(page, 1500);
  await page.evaluate(() => show('sched')); await tick(page, 800); await page.waitForTimeout(400);
  let r = await page.evaluate(() => {
    const h = document.querySelector('#view-sched .phead.sched-tag h2'), w = document.querySelector('#view-sched > .wrap');
    const on = document.querySelector('#view-sched .wl-tab.on'), day = document.querySelector('#view-sched .cal-wrap:not(.cal-mini) .cal-col:not(.cal-any) .cal-day');
    const a = (getComputedStyle(day).backgroundColor.match(/[\d.]+/g) || []).map(Number);
    return { hl: Math.round(h.getBoundingClientRect().left), wl: Math.round(w.getBoundingClientRect().left + parseFloat(getComputedStyle(w).paddingLeft)), on: getComputedStyle(on).backgroundColor, onShadow: getComputedStyle(on).boxShadow, alpha: a.length > 3 ? a[3] : 1, maxW: getComputedStyle(w).maxWidth };
  });
  ok(Math.abs(r.hl - r.wl) <= 1 && r.maxW === '1240px', 'Schedule\'s title is the app\'s left-aligned heading on the 1240px page', r);
  ok(r.on === 'rgb(227, 236, 255)' && r.onShadow === 'none', 'its active tab is the app\'s soft-blue pill (no edge bar)', r);
  ok(r.alpha < 0.1, 'the week\'s day columns are a tint, so the professor connectors stay whole across them', r);
  await close();
  for (const w of [1000, 1100]) {
    const { page, close } = await desk({ init: withTheme(null), width: w }); await tick(page, 1500);
    await page.evaluate(() => show('sched')); await tick(page, 800); await page.waitForTimeout(400);
    const bad = await page.evaluate(() => [...document.querySelectorAll('#view-sched .cal-wrap:not(.cal-mini) .cal-block:not(.narrow) .cb-code')].filter(c => c.offsetParent && c.getBoundingClientRect().right > c.closest('.cal-block').getBoundingClientRect().right + 0.5).map(c => c.textContent));
    ok(bad.length === 0, 'at ' + w + 'px Schedule\'s course codes fit their blocks beside the professor cards', bad); await close(); }
  { const { page, close } = await desk({ init: withTheme(null) }); await tick(page, 1500);
  await page.evaluate(() => openProf(Object.keys(PROFESSORS).find(k => /examplewood/i.test(PROFESSORS[k].name)))); await tick(page, 800);
  r = await page.evaluate(() => { const h = document.querySelector('#view-prof .pp-head'); const f = document.querySelector('#view-prof .pp-score .pr-f svg path');
    return { bg: getComputedStyle(h).backgroundColor, star: f && getComputedStyle(f).fill, want: getComputedStyle(h).getPropertyValue('--rcf').trim() }; });
  const fillOf = await page.evaluate(v => { const e = document.createElement('i'); e.style.color = v; document.body.appendChild(e); const c = getComputedStyle(e).color; e.remove(); return c; }, r.want);
  ok(r.bg === 'rgb(124, 58, 237)', 'a professor opens on the app\'s purple hero', r);
  ok(r.star && r.star === fillOf && r.star !== 'rgb(232, 185, 59)', 'their stars are the rating\'s own colour, not the old gold', { star: r.star, want: fillOf });
  await page.evaluate(() => show('friends')); await tick(page, 800);
  r = await page.evaluate(() => getComputedStyle(document.querySelector('#view-friends .frv2')).backgroundColor);
  ok(r === 'rgba(0, 0, 0, 0)', 'Friends opens into the app\'s separate cards (no single panel)', r);
  await page.evaluate(() => openSettings()); await tick(page, 600);
  r = await page.evaluate(() => { const t = document.querySelector('#view-settings .st-tab.on'); return { bg: getComputedStyle(t).backgroundColor, bar: getComputedStyle(t, '::before').display }; });
  ok(r.bg === 'rgb(227, 236, 255)' && r.bar === 'none', 'Settings\' tabs are the app\'s pills', r);
  await page.evaluate(() => openRate()); await tick(page, 800);
  r = await page.evaluate(() => { const row = document.querySelector('#rlLists > div:not(.rl-term):not(:first-child)'); return row && getComputedStyle(row).backgroundColor; });
  ok(r === 'rgb(243, 238, 255)', 'the Rate sheet\'s professors are the app\'s soft-purple rows', r);
  await close();
}
});

/* 2026-10-06: ITP's plan is the catalog's undeclared roadmap, Physics (BA) is offered, EEM has its catalog name */
test('majors', async () => {
  const OLD = 'Recreation, Parks & Tourism Administration / Experience Industry Management', NEW = 'Experience & Event Management';
  const { page, close, log } = await desk({ init: `try{localStorage.setItem('professify-profile',JSON.stringify({school:'calpoly',major:${JSON.stringify(OLD)},conc:null}))}catch(e){}` }); await tick(page, 1500);
  const r = await page.evaluate(([OLD, NEW]) => {
    const opts = [...new DOMParser().parseFromString('<select>' + majorOptionsHtml('') + '</select>', 'text/html').querySelectorAll('option')].map(o => o.textContent);
    const S = n => Object.values(SCHED_MAJORS).find(m => m.name === n), sum = e => e && e.terms.map(t => t.slots.reduce((a, x) => a + x.units, 0)).join();
    const coming = (window.SCHED_COMING || []).flat();
    loadProfile();
    return { opts: ['Industrial Technology & Packaging', 'Physics (BA)', NEW].every(n => opts.includes(n)) && !opts.includes(OLD), itp: sum(S('Industrial Technology & Packaging')), ba: sum(S('Physics (BA)')),
      itpForced: /ITP 2260|ITP 3390/.test(JSON.stringify(S('Industrial Technology & Packaging'))), coming: coming.filter(n => /Industrial Technology/.test(n)), me: student.major,
      synth: Object.keys(SCHED_MAJORS).filter(k => /^syn-/.test(k) && /industrial|physics|experience/.test(k)) };
  }, [OLD, NEW]);
  ok(r.opts, 'majors: the website’s major picker offers ITP, Physics (BA) and Experience & Event Management (not the old name)', r);
  ok(r.itp === '13,16,15,15,17,15,15,12' && !r.itpForced && r.ba === '15,15,16,14,14,15,15,16' && !r.synth.length, 'majors: ITP and Physics (BA) use the catalog’s own plans (not the Industrial Technology track, not a generated plan)', r);
  ok(!r.coming.length, 'majors: ITP is no longer listed as “coming soon” next to its own plan', r.coming);
  ok(r.me === NEW, 'majors: a profile saved with the old EEM name loads as Experience & Event Management', r.me);
  ok(log.errors.length === 0, 'majors: no page errors', log.errors);
  await close();
});

const names = ONLY ? [ONLY] : Object.keys(T);
for (const n of names) {
  if (!T[n]) { console.log('no such test', n); process.exit(2); }
  if (!QUIET) console.log('\n' + n);
  try { await T[n](); } catch (e) { fail++; fails.push(n + ' threw'); console.log('  FAIL', n, 'threw', String(e).slice(0, 300)); }
}
console.log(`\ncheck-desktop-look: ${pass} passed, ${fail} failed`);
if (fail) { console.log('failed:', fails.join(' | ')); process.exit(1); }
