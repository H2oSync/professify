/* check-desktop-identity — the website wears the phone's identity (website-identity, Tate 2026-10-14: an audit of phone vs
   website screenshots). Runs the REAL index.html in Chromium, signed in, against the PostgREST stand-in.
   Run: APP_DIR=<repo> node check-desktop-identity.mjs [--only name] [--quiet]   (APP_PORT to move off 8190)
   The promises: the header shows the phone's logo image, byte for byte, one variant per theme, and still goes home;
   a person with no photo is the phone's light grey circle with a white person in BOTH themes (professors keep rating
   colours, photos are untouched, a photo that fails falls back to the same grey person); one friends badge, on the
   Friends tab, never over the account pill; the dark palette is the phone's. */
import fs from 'node:fs'; import path from 'node:path';
import { openApp } from './app-harness.mjs';

const args = process.argv.slice(2);
const ONLY = args.includes('--only') ? args[args.indexOf('--only') + 1] : null;
const QUIET = args.includes('--quiet');
let pass = 0, fail = 0; const fails = [];
function ok(c, name, info) {
  if (c) { pass++; if (!QUIET) console.log('  ok  ', name); }
  else { fail++; fails.push(name); console.log('  FAIL', name, info !== undefined ? '→ ' + JSON.stringify(info).slice(0, 400) : ''); }
}
const tick = async (p, ms = 400) => { await p.clock.runFor(ms); await p.waitForTimeout(250); };
const desk = (o = {}) => openApp(Object.assign({ path: '/', width: 1440, height: 900, wait: 4000 }, o));
const T = {}; const test = (name, fn) => { T[name] = fn; };
const theme = async (page, t) => { await page.evaluate(x => setTheme(x), t); await tick(page, 300); };

/* the phone's own bytes, read from app/index.html next to the page under test */
const APP = fs.readFileSync(path.join(process.env.APP_DIR || path.resolve('..', '..'), 'app', 'index.html'), 'utf8');
const PM = APP.match(/const TC_LOGO = '(data:image\/png;base64,[A-Za-z0-9+/=]+)', TC_LOGO_DARK = '(data:image\/png;base64,[A-Za-z0-9+/=]+)';/);
const PHONE_LIGHT = PM && PM[1], PHONE_DARK = PM && PM[2];
const SIL = APP.match(/const silhouette = .*?<circle cx="12" cy="9.2" r="4.4" fill="#fff"\/><path d="([^"]+)" fill="#fff"\/>/);
const PHONE_PATH = SIL && SIL[1];

const BOXES = `window.__box = e => { const r = e.getBoundingClientRect(); return { l: r.left, t: r.top, r: r.right, b: r.bottom, w: r.width, h: r.height }; };
  window.__vis = e => { if (!e) return false; const cs = getComputedStyle(e); const r = e.getBoundingClientRect(); return cs.display !== 'none' && cs.visibility !== 'hidden' && r.width > 0 && r.height > 0 && !e.hidden; };`;

test('logo', async () => {
  ok(!!PHONE_LIGHT && !!PHONE_DARK && PHONE_LIGHT !== PHONE_DARK, 'the phone logo bytes were found in app/index.html', { l: !!PHONE_LIGHT });
  const { page, close, log } = await desk(); await page.evaluate(BOXES); await tick(page, 1000);
  const q = () => page.evaluate(() => {
    const L = document.querySelector('.brand .brand-logo.lg-l'), D = document.querySelector('.brand .brand-logo.lg-d'), tile = document.querySelector('.brand .brand-tile');
    return { l: L && L.getAttribute('src'), d: D && D.getAttribute('src'), lv: __vis(L), dv: __vis(D), tv: __vis(tile), lb: L && __box(L), db: D && __box(D),
      aria: document.querySelector('.brand').getAttribute('aria-label'), typed: !!document.querySelector('.brand-wm'), text: document.querySelector('.brand').innerText.trim(),
      pill: __box(document.getElementById('authBtn')), brand: __box(document.querySelector('.brand')), tabsL: __box(document.querySelector('nav.tabs')).l };
  });
  let r = await q();
  ok(r.l === PHONE_LIGHT && r.d === PHONE_DARK, "the header's two logo images are the phone's TC_LOGO / TC_LOGO_DARK, byte for byte", { l: r.l && r.l.length, d: r.d && r.d.length });
  ok(r.lv && !r.dv && !r.tv, 'light theme: the light logo shows, not the dark one, not the tile', r);
  ok(r.lb.h >= 32 && r.lb.h <= 36.5 && r.lb.w > 80, 'the logo is 32-36px tall, with its own width (not squeezed)', r.lb);
  ok(!r.typed && r.text === '', 'the typed "TermChamp" wordmark is gone', r.text);
  ok(r.aria === 'TermChamp — go to home', 'the button still names the app', r.aria);
  await theme(page, 'dark'); r = await q();
  ok(!r.lv && r.dv && !r.tv, 'dark theme: the dark logo shows, not the light one', r);
  await theme(page, 'light');
  await page.evaluate(() => show('friends')); await tick(page, 400);
  await page.click('.brand'); await tick(page, 400);
  ok(await page.evaluate(() => !!document.querySelector('#page-home.active, #home.active, section.active#home') || (document.getElementById('tab-home') || {}).className.includes('on') || /active|on/.test((document.getElementById('tab-home') || {}).className)), 'clicking the logo goes home', await page.evaluate(() => (document.getElementById('tab-home') || {}).className));
  ok(log.errors.length === 0, 'logo: no page errors', log.errors);
  await close();
  /* a phone-width window: the logo fits beside the account pill; a very narrow one falls back to the tile */
  for (const th of ['light', 'dark']) {
    const m = await desk({ width: 390, height: 844 }); await m.page.evaluate(BOXES); await theme(m.page, th);
    const x = await q.call(null).catch(() => null);
    const y = await m.page.evaluate(() => { const v = document.querySelector('.brand .brand-logo:not([style*="none"])'); const logos = [...document.querySelectorAll('.brand .brand-logo')].filter(__vis);
      return { n: logos.length, b: logos[0] && __box(logos[0]), pill: __box(document.getElementById('authBtn')), tile: __vis(document.querySelector('.brand .brand-tile')), vw: innerWidth, sw: document.documentElement.scrollWidth }; });
    ok(y.n === 1 && !y.tile && y.b.r <= y.pill.l - 4 && y.b.h >= 30, `390 ${th}: one logo image fits left of the account pill`, y);
    ok(y.sw <= y.vw, `390 ${th}: the header never scrolls the page sideways`, y);
    await m.close();
  }
  for (const [w, h, why] of [[660, 800, '660px (five tabs still shown): the tile, so the bar fits and nothing scrolls sideways'], [330, 700, '330px: too narrow for the logo, so the TC tile is kept']]) for (const th of ['light', 'dark']) {
    const m = await desk({ width: w, height: h }); await m.page.evaluate(BOXES); await theme(m.page, th);
    const y = await m.page.evaluate(() => ({ logos: [...document.querySelectorAll('.brand .brand-logo')].filter(__vis).length, tile: __vis(document.querySelector('.brand .brand-tile')), sw: document.documentElement.scrollWidth, vw: innerWidth }));
    ok(y.logos === 0 && y.tile && y.sw <= y.vw, why + ' (' + th + ')', y); await m.close();
  }
});

test('nophoto', async () => {
  const { page, close, log } = await desk(); await page.evaluate(BOXES); await tick(page, 1200);
  const GREY = { light: 'rgb(218, 221, 227)', dark: 'rgb(58, 68, 89)' };
  for (const th of ['light', 'dark']) {
    await theme(page, th);
    /* the helpers every surface goes through */
    let r = await page.evaluate(() => { const d = document.createElement('div'); d.id = '__t'; d.style.cssText = 'position:fixed;left:0;top:0;width:60px;height:60px;z-index:99999';
      d.innerHTML = '<span id="__a" style="display:block;width:44px;height:44px;border-radius:50%;background:' + colorForId('x') + '">' + avaHtml('', 'Pat Suggestia') + '</span>'
        + '<span id="__b" style="display:block;width:44px;height:44px;border-radius:50%;background:' + colorForId('x') + '">' + faceHtml({ id: 'x', name: 'Pat Suggestia' }) + '</span>';
      document.body.appendChild(d);
      const a = document.getElementById('__a'), s = a.querySelector('svg.nophoto');
      return { bg: getComputedStyle(a).backgroundColor, svg: !!s, text: a.textContent.trim(), fills: s ? [...s.querySelectorAll('circle,path')].map(e => e.getAttribute('fill')) : [], d: s ? s.querySelector('path').getAttribute('d') : '',
        box: s && __box(s), faceSvg: !!document.getElementById('__b').querySelector('svg.nophoto'), faceText: document.getElementById('__b').textContent.trim() }; });
    ok(r.bg === GREY[th] && r.svg && r.text === '' && r.fills.length === 2 && r.fills.every(f => f === '#fff'), `${th}: no photo = the grey circle (${GREY[th]}) with a white person, no initials`, r);
    ok(r.d === PHONE_PATH, `${th}: the person is the phone's silhouette path`, { site: r.d, phone: PHONE_PATH });
    ok(r.box.w === 44 && r.box.h === 44 && r.faceSvg && r.faceText === '', `${th}: it fills its circle; faceHtml() gives the same`, r);
    await page.evaluate(() => document.getElementById('__t').remove());
    /* Home: your own card and the friends' week cards */
    r = await page.evaluate(() => { const out = {}; const me = document.querySelector('.hm-id .fav'); out.me = me && { svg: !!me.querySelector('svg.nophoto'), text: me.textContent.trim(), bg: getComputedStyle(me).backgroundColor };
      out.pill = (() => { const a = document.querySelector('#authBtn .auth-ava'); return a && { svg: !!a.querySelector('svg.nophoto'), text: a.textContent.trim(), bg: getComputedStyle(a).backgroundColor }; })();
      out.favs = [...document.querySelectorAll('.hm-fhead .fav, .hm-fitem .fav, .hm-avstack .sav')].map(e => ({ svg: !!e.querySelector('svg.nophoto'), img: !!e.querySelector('img'), text: e.textContent.trim(), bg: getComputedStyle(e).backgroundColor }));
      return out; });
    ok(r.me && r.me.svg && r.me.text === '' && r.me.bg === GREY[th], `${th}: your own card on Home is the grey person`, r.me);
    ok(r.pill && r.pill.svg && r.pill.text === '' && r.pill.bg === GREY[th], `${th}: the account pill's avatar is the grey person`, r.pill);
    r.favs = r.favs.filter(f => f.text !== '+');
    ok(r.favs.length > 0 && r.favs.every(f => f.img || (f.svg && f.text === '' && f.bg === GREY[th])), `${th}: every friend face on Home is a photo or the grey person (${r.favs.length} faces)`, r.favs);
    /* Friends: requests, suggestions, rows */
    await page.evaluate(() => show('friends')); await tick(page, 900);
    r = await page.evaluate(() => [...document.querySelectorAll('#page-friends .ini, #friends .ini, .fr-card .ini, .fr-row .ini, .frv2-card .ini')].map(e => ({ svg: !!e.querySelector('svg.nophoto'), img: !!e.querySelector('img'), text: e.textContent.trim(), bg: getComputedStyle(e).backgroundColor })));
    ok(r.length >= 3 && r.every(f => f.img || (f.svg && f.text === '' && f.bg === GREY[th])), `${th}: every person on Friends is a photo or the grey person (${r.length} tiles)`, r);
    await page.evaluate(() => show('home')); await tick(page, 600);
  }
  /* photos untouched; a photo that fails becomes the grey person; professors keep their rating colour and initials */
  await theme(page, 'light');
  const r = await page.evaluate(async () => { const d = document.createElement('div'); d.id = '__t2'; d.innerHTML = '<span id="__p">' + avaHtml('data:image/svg+xml;utf8,<svg xmlns=%22http://www.w3.org/2000/svg%22 width=%224%22 height=%224%22><rect width=%224%22 height=%224%22 fill=%22red%22/></svg>', 'Photo Person') + '</span>'
      + '<span id="__f">' + avaHtml('https://example.invalid/none.jpg', 'Broken Photo') + '</span>';
    document.body.appendChild(d); await new Promise(r => setTimeout(r, 800));
    const p = document.getElementById('__p'), f = document.getElementById('__f');
    return { photo: !!p.querySelector('img.ava-img'), photoSvg: !!p.querySelector('svg.nophoto'), broken: !!f.querySelector('svg.nophoto'), brokenImg: !!f.querySelector('img'), brokenText: f.textContent.trim(),
      profs: [...document.querySelectorAll('.pr-av, .pcard .ini')].map(e => ({ text: e.textContent.trim(), svg: !!e.querySelector('svg.nophoto') })) }; });
  ok(r.photo && !r.photoSvg, 'a photo is still a photo', r);
  ok(r.broken && !r.brokenImg && r.brokenText === '', 'a photo that fails to load falls back to the grey person (no broken icon, no initials)', r);
  ok(r.profs.length > 0 && r.profs.every(x => x.text.length >= 1 && !x.svg), 'professors keep their initials', r.profs);
  ok(log.errors.length === 0, 'nophoto: no page errors', log.errors);
  await close();
});

test('badge', async () => {
  const { page, close, log } = await desk(); await page.evaluate(BOXES); await tick(page, 1200);
  let r = await page.evaluate(() => ({ old: !!document.getElementById('friendsNavBadge'), tab: __vis(document.getElementById('friendsNavBadge2')), txt: (document.getElementById('friendsNavBadge2') || {}).textContent,
    visible: [...document.querySelectorAll('.wl-navbadge')].filter(__vis).map(e => e.id), pill: __box(document.getElementById('authBtn')), tb: __box(document.getElementById('friendsNavBadge2')),
    tabBtn: __box(document.getElementById('tab-friends')), bell: !!document.getElementById('notifBtn') }));
  ok(!r.old, 'there is no second friends badge in the account area (#friendsNavBadge)', r);
  ok(r.tab && r.txt === '1' && r.visible.length === 1 && r.visible[0] === 'friendsNavBadge2', 'exactly one friends badge shows, on the Friends tab, saying 1', r);
  ok(r.tb.r <= r.pill.l || r.tb.l >= r.pill.r || r.tb.b <= r.pill.t || r.tb.t >= r.pill.b, 'the badge does not overlap the account pill', r);
  ok(r.tb.l >= r.tabBtn.l && r.tb.r <= r.tabBtn.r + 2, 'the badge sits on the Friends tab', r);
  const e = await page.evaluate(() => { try { updateFriendsBadge(); return null; } catch (x) { return String(x); } });
  ok(e === null, 'updateFriendsBadge() still runs with the old badge gone', e);
  await close();
  /* a phone-width window: the pill is clear, the bar's badge is the one */
  const m = await desk({ width: 390, height: 844 }); await m.page.evaluate(BOXES); await tick(m.page, 1200);
  r = await m.page.evaluate(() => { const vis = [...document.querySelectorAll('.wl-navbadge, #mFriendsBadge, .nav-badge')].filter(__vis);
    const pill = __box(document.getElementById('authBtn')); return { vis: vis.map(e => ({ id: e.id, txt: e.textContent, over: (() => { const b = __box(e); return !(b.r <= pill.l || b.l >= pill.r || b.b <= pill.t || b.t >= pill.b); })() })), pill }; });
  ok(r.vis.length === 1 && r.vis[0].id === 'mFriendsBadge' && r.vis[0].txt === '1' && !r.vis[0].over, '390: one badge, on the bottom bar Friends tab, nowhere near the pill', r);
  await m.close();
});

test('dark', async () => {
  const { page, close, log } = await desk(); await tick(page, 1000);
  const q = () => page.evaluate(() => { const cs = getComputedStyle(document.documentElement); const v = n => cs.getPropertyValue(n).trim().toUpperCase();
    const hdr = getComputedStyle(document.querySelector('header.nav')).backgroundColor;
    return { bg: v('--bg'), panel: v('--panel'), p2: v('--panel-2'), p3: v('--panel-3'), body: getComputedStyle(document.body).backgroundColor, hdr, card: (() => { const c = document.querySelector('.hm-card'); return c ? getComputedStyle(c).backgroundColor : null; })(), nophoto: v('--nophoto') }; });
  await theme(page, 'dark'); let r = await q();
  ok(r.bg === '#0A0F1C' && r.panel === '#141B2B' && r.p2 === '#1C2539' && r.p3 === '#27314A', "dark tokens are the phone's (#0A0F1C / #141B2B / #1C2539 / #27314A)", r);
  ok(r.body === 'rgb(10, 15, 28)' && (r.card === null || r.card === 'rgb(20, 27, 43)'), "the page and a card are painted with them", r);
  ok(/rgba\(20, 27, 43/.test(r.hdr), "the header bar is the phone's bar colour", r.hdr);
  ok(r.nophoto === '#3A4459', "dark's no-photo grey is the phone's #3A4459", r);
  await theme(page, 'light'); r = await q();
  ok(r.bg === '#F4F6FB' && r.panel === '#FFFFFF' && r.nophoto === '#DADDE3', 'light tokens are unchanged, with the phone\'s #DADDE3 no-photo grey', r);
  ok(log.errors.length === 0, 'dark: no page errors', log.errors);
  await close();
});

const names = ONLY ? [ONLY] : Object.keys(T);
for (const n of names) {
  if (!T[n]) { console.log('no such test', n); process.exit(2); }
  if (!QUIET) console.log('\n' + n);
  try { await T[n](); } catch (e) { fail++; fails.push(n + ' threw'); console.log('  FAIL', n, 'threw', String(e).slice(0, 300)); }
}
console.log(`\ncheck-desktop-identity: ${pass} passed, ${fail} failed`);
if (fail) { console.log('failed:', fails.join(' | ')); process.exit(1); }
