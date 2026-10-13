#!/usr/bin/env python3
"""Tests for logo-image-2026-10-11.py: check-app's `wordmark` test becomes `logoImage`-style checks.
Usage: python3 logo-image-tests-2026-10-11.py app-dev/tests/check-app.mjs"""
import sys
p = sys.argv[1]; s = open(p, encoding='utf-8').read()
a = """tests.wordmark = async () => {
  const { page, close } = await openApp({});
  const t = await page.locator('.homehdr').innerText();
  ok(/^TermChamp/.test(t.trim()) && await page.locator('.homehdr img.logo').count() === 0, 'design: Home header is the TermChamp wordmark, not the tile', t);
  await close();
};"""
b = r"""tests.wordmark = async () => {
  /* Tate, 2026-10-11: his logo image, exact, in place of the typed wordmark */
  const fs = await import('node:fs'), crypto = await import('node:crypto'), pth = await import('node:path');
  const md5 = b => crypto.createHash('md5').update(b).digest('hex');
  const dir = pth.resolve(pth.dirname(new URL(import.meta.url).pathname), '../patches/logo');
  const want = { light: md5(fs.readFileSync(pth.join(dir, 'termchamp-logo-light.png'))), dark: md5(fs.readFileSync(pth.join(dir, 'termchamp-logo-dark.png'))) };
  const { page, close, log } = await openApp({});
  const look = () => page.evaluate(() => {
    const h = document.querySelector('.homehdr h1'), vis = [...h.querySelectorAll('img')].filter(i => getComputedStyle(i).display !== 'none');
    const r = vis[0] && vis[0].getBoundingClientRect();
    return { label: h.getAttribute('aria-label'), text: h.textContent.trim(), n: vis.length, src: vis[0] && vis[0].src, loaded: vis[0] && vis[0].complete && vis[0].naturalWidth > 0, nat: vis[0] && [vis[0].naturalWidth, vis[0].naturalHeight], h: r && Math.round(r.height), w: r && Math.round(r.width), alt: vis[0] && vis[0].getAttribute('alt'), tile: !!document.querySelector('.homehdr img.logo') };
  });
  const L = await look();
  const srcHash = s => s ? md5(Buffer.from(s.replace(/^data:image\/png;base64,/, ''), 'base64')) : '';
  ok(L.label === 'TermChamp' && L.text === '' && L.n === 1 && L.alt === '' && !L.tile, 'logo: Home’s header is one picture, read out as “TermChamp” (no typed wordmark, not the tile)', L);
  ok(L.loaded && srcHash(L.src) === want.light && L.nat[0] === 672 && L.nat[1] === 144, 'logo: light mode shows Tate’s logo exactly (the cut-out file, drawn from 3× pixels)', { got: srcHash(L.src), want: want.light, nat: L.nat });
  ok(L.h === 36 && Math.abs(L.w - 168) <= 1, 'logo: 36px tall, its own proportions (168px wide)', L);
  await page.evaluate(() => { try { localStorage.setItem('tc-theme', 'dark'); } catch (e) {} applyTheme(true); }); await settle(page, 300);
  const D = await look();
  ok(D.n === 1 && D.loaded && srcHash(D.src) === want.dark && D.h === 36, 'logo: dark mode shows the dark cut (Term in the dark theme’s navy so it reads on #0A0F1C)', { got: srcHash(D.src), want: want.dark });
  const lm = await page.evaluate(() => Math.round(document.querySelector('.homehdr h1').getBoundingClientRect().left));
  ok(lm === 12, 'logo: starts 12px from the screen edge, like the stories', lm);
  await page.setViewportSize({ width: 320, height: 640 }); await settle(page, 300);
  const n = await page.evaluate(() => { const h = document.querySelector('.homehdr'), bs = [...h.querySelectorAll('button')].map(b => b.getBoundingClientRect()); const i = [...h.querySelectorAll('h1 img')].find(x => getComputedStyle(x).display !== 'none').getBoundingClientRect(); return { sw: document.getElementById('scroll').scrollWidth, cw: document.getElementById('scroll').clientWidth, imgW: Math.round(i.width), imgR: Math.round(i.right), btnL: Math.round(Math.min(...bs.map(r => r.left))), btnR: Math.round(Math.max(...bs.map(r => r.right))) }; });
  ok(n.sw <= n.cw && n.imgW === 168 && n.imgR < n.btnL && n.btnR <= 320, 'logo: at 320px it keeps its size, nothing overlaps, nothing runs off the screen', n);
  const cb = await page.evaluate(() => { const i = document.querySelector('.homehdr .tc-logo-i'), c = getComputedStyle(i); return { pe: c.pointerEvents, tc: c.webkitTouchCallout || c.getPropertyValue('-webkit-touch-callout') }; });
  ok(cb.pe === 'none', 'logo: a long press doesn’t offer Save Image (it isn’t a target)', cb);
  ok(log.errors.length === 0, 'logo: no page errors', log.errors);
  await close();
  /* System theme with the phone in dark mode (nothing saved): the dark cut */
  { const s2 = await openApp({ init: () => { try { localStorage.removeItem('tc-theme'); } catch (e) {} } });
    await s2.page.emulateMedia({ colorScheme: 'dark' }); await s2.page.evaluate(() => { try { applyTheme(true); } catch (e) {} }); await settle(s2.page, 300);
    const sy = await s2.page.evaluate(() => { const v = [...document.querySelectorAll('.homehdr h1 img')].filter(i => getComputedStyle(i).display !== 'none'); return { n: v.length, dark: v[0] && v[0].classList.contains('lg-d'), theme: document.documentElement.getAttribute('data-theme') }; });
    ok(sy.n === 1 && sy.dark && sy.theme === 'dark', 'logo: System theme following a dark phone shows the dark cut', sy);
    await s2.close(); }
  /* onboarding's welcome (signed out, always light) */
  const o = await openApp({ signedIn: false });
  const w = await o.page.evaluate(() => { const d = document.querySelector('.onb .wordmark'); const i = d && d.querySelector('img'); return d && { label: d.getAttribute('aria-label'), role: d.getAttribute('role'), text: d.textContent.trim(), src: i && i.src, h: i && Math.round(i.getBoundingClientRect().height), loaded: i && i.complete && i.naturalWidth > 0 }; });
  ok(w && w.label === 'TermChamp' && w.role === 'img' && w.text === '' && w.loaded && srcHash(w.src) === want.light && w.h === 48, 'logo: the welcome screen shows the same logo, 48px tall', w && Object.assign({}, w, { src: srcHash(w.src) }));
  await o.close();
};"""
assert s.count(a) == 1, s.count(a)
s = s.replace(a, b)
open(p, 'w', encoding='utf-8').write(s)
print('tests patched')
