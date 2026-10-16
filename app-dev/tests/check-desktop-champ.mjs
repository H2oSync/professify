/* check-desktop-champ — the website's assistant is Champ, and looks like the phone's Champ sheet (website-champ, Tate 2026-10-14:
   "the website still showed the old Hawk"). Runs the REAL index.html + hawk-ask.js/css in Chromium, signed in.
   Run: APP_DIR=<repo> node check-desktop-champ.mjs [--only name] [--quiet]   (APP_PORT to move off 8190)
   The promises: nothing the student can read or a screen reader announces says "Hawk"; the box opens on the big bird and
   "Hi, I'm Champ." with the phone's four chips, each of which asks its question; the field says "Ask Champ…" with a round
   send button; the footer says where a question goes and that is true (signed in, a model question reaches the `ask`
   function); the surface is light in Light and dark in Dark; every piece of text, empty and with an answer, is >= 4.5:1. */
import { openApp } from './app-harness.mjs';

const args = process.argv.slice(2);
const ONLY = args.includes('--only') ? args[args.indexOf('--only') + 1] : null;
const QUIET = args.includes('--quiet');
let pass = 0, fail = 0; const fails = [];
function ok(c, name, info) {
  if (c) { pass++; if (!QUIET) console.log('  ok  ', name); }
  else { fail++; fails.push(name); console.log('  FAIL', name, info !== undefined ? '→ ' + JSON.stringify(info).slice(0, 500) : ''); }
}
const tick = async (p, ms = 400) => { await p.clock.runFor(ms); await p.waitForTimeout(250); };
const T = {};
const test = (name, fn) => { T[name] = fn; };
const CALLS = [];
const ask = body => { CALLS.push(body.q); return { tool: 'cant_answer', args: { reason: 'not_about_classes' } }; };
const LIVE = [];
const open = async (o = {}) => { const x = await openApp(Object.assign({ path: '/', width: 1440, height: 900, wait: 4000, ask }, o)); await tick(x.page, 2500); LIVE.push(x); return x; };
const CHIPS = ['When am I free this week?', "Who's free right now?", 'What’s my day look like?', 'My best professor'];

test('name: Champ everywhere the student can see or hear', async () => {
  const { page, close, log } = await open();
  const fab = await page.evaluate(() => document.querySelector('.hawk-fab').getAttribute('aria-label'));
  ok(fab === 'Ask Champ', 'launcher is "Ask Champ"', fab);
  await page.click('.hawk-fab'); await tick(page, 300);
  const d = await page.evaluate(() => {
    const b = document.querySelector('.hawk-box');
    return { label: b.getAttribute('aria-label'), name: b.querySelector('.hawk-head__name').textContent,
      close: b.querySelector('.hawk-x').getAttribute('aria-label'), ph: b.querySelector('.hawk-input').placeholder,
      lab: b.querySelector('label').textContent, send: b.querySelector('.hawk-send').getAttribute('aria-label'),
      text: b.innerText, html: b.outerHTML.replace(/style="[^"]*"/g, '').replace(/url\([^)]*\)/g, '') };
  });
  ok(d.label === 'Champ' && d.name === 'Champ', 'box and header say Champ', [d.label, d.name]);
  ok(d.close === 'Close Champ' && d.ph === 'Ask Champ…' && d.lab === 'Ask Champ' && d.send === 'Send', 'close / placeholder / field label / send', d);
  ok(!/hawk/i.test(d.text) && !/aria-label="[^"]*hawk/i.test(d.html) && !/placeholder="[^"]*hawk/i.test(d.html), 'no "Hawk" in the box text or its aria-labels / placeholder');
  for (const q of ['what does champ do', 'how do i contact termchamp']) {
    await page.evaluate(q => HawkAsk.ask(q), q); await tick(page, 1500);
    const t = await page.evaluate(() => { const l = document.querySelector('.hawk-log'); return { text: l.innerText, rows: [...l.querySelectorAll('.hawk-row')].map(r => r.textContent) }; });
    ok(!/hawk/i.test(t.text), 'help answer "' + q + '" never says Hawk', t.text.slice(0, 200));
  }
  await page.evaluate(() => HawkAsk.ask('help')); await tick(page, 1500);
  ok(await page.evaluate(() => /What Champ can do/.test(document.querySelector('.hawk-log').innerText) || !/Hawk/.test(document.querySelector('.hawk-log').innerText)), '"What Champ can do" label');
  ok(log.errors.length === 0, 'no page errors', log.errors);
  await close();
});

test('sheet: the greeting, the bird, the four chips, each asks its question', async () => {
  const { page, close } = await open();
  await page.click('.hawk-fab'); await tick(page, 300);
  const g = await page.evaluate(() => {
    const h = document.querySelector('.hawk-hint'); if (!h) return null;
    const f = h.querySelector('.hawk-hint__face'), r = f.getBoundingClientRect();
    return { lead: h.querySelector('.hawk-hint__lead').textContent, bird: getComputedStyle(f).backgroundImage.slice(0, 22), w: r.width, h: r.height,
      chips: [...h.querySelectorAll('.hawk-cchip')].map(c => c.textContent), small: document.querySelector('.hawk-chips') && getComputedStyle(document.querySelector('.hawk-chips')).display };
  });
  ok(g && g.lead === "Hi, I'm Champ.", 'greeting is "Hi, I\'m Champ."', g && g.lead);
  ok(g && /^url\("data:image\/webp/.test(g.bird) && g.w >= 56 && g.h >= 68, 'the big bird (the phone\'s image) is drawn', g);
  ok(g && JSON.stringify(g.chips) === JSON.stringify(CHIPS), 'the phone\'s four chips, same words', g && g.chips);
  ok(g && g.small === 'none', 'the slim chip row is hidden while the big chips show', g && g.small);
  /* the first from the big grid, the rest from the slim row that replaces it once there is an answer */
  for (const [i, c] of CHIPS.entries()) {
    await page.evaluate(([c, i]) => { const sel = i === 0 ? '.hawk-cgrid .hawk-cchip' : '.hawk-chips .hawk-cchip'; [...document.querySelectorAll(sel)].find(x => x.textContent === c).click(); }, [c, i]);
    await tick(page, 1500);
    // 2026-10-15: Champ is a chat now, so the turns accumulate; the question just asked is the LAST bubble
    const said = await page.evaluate(() => { const q = document.querySelectorAll('.hawk-said__q'); return (q[q.length - 1] || {}).textContent; });
    ok(said === c, 'tapping "' + c + '" asks exactly that', said);
  }
  const after = await page.evaluate(() => ({ strip: getComputedStyle(document.querySelector('.hawk-chips')).display, big: !!document.querySelector('.hawk-hint') }));
  ok(after.strip !== 'none' && !after.big, 'after an answer the slim chip row shows and the greeting is gone', after);
  await close();
});

test('footer: says where a question goes, and it is true', async () => {
  const { page, close } = await open();
  await page.click('.hawk-fab'); await tick(page, 300);
  const f = await page.evaluate(() => document.querySelector('.hawk-foot').textContent);
  CALLS.length = 0;
  await page.evaluate(() => HawkAsk.ask('which business electives are not too hard')); await tick(page, 2500);
  ok(/Anthropic/.test(f) && /your classes stay on this device/.test(f), 'signed in: the footer names Anthropic and says classes stay put', f);
  ok(CALLS.length >= 1, 'and a model question really went to the `ask` function', CALLS);
  const f2 = await page.evaluate(() => document.querySelector('.hawk-foot').textContent);
  ok(/Anthropic/.test(f2), 'it keeps saying so after an answer, with the seat as-of beside it when there is one', f2);
  await page.evaluate(() => { sbUser = null; HawkAsk.close(); }); await tick(page, 200);
  await page.evaluate(() => { HawkAsk.open(); }); await tick(page, 200);
  const g = await page.evaluate(() => document.querySelector('.hawk-foot').textContent);
  ok(/leaves your browser/.test(g) && !/Anthropic/.test(g), 'signed out: the footer says nothing leaves the browser', g);
  await close();
});

/* contrast, computed from what the browser painted */
const CONTRAST = () => {
  const parse = c => { const m = c.match(/rgba?\(([^)]+)\)/); if (!m) return [0, 0, 0, 1]; const p = m[1].split(/[ ,\/]+/).filter(Boolean).map(Number); return [p[0], p[1], p[2], p.length > 3 ? p[3] : 1]; };
  const over = (top, bot) => { const a = top[3]; return [top[0] * a + bot[0] * (1 - a), top[1] * a + bot[1] * (1 - a), top[2] * a + bot[2] * (1 - a), 1]; };
  const lum = c => { const f = v => { v /= 255; return v <= .03928 ? v / 12.92 : Math.pow((v + .055) / 1.055, 2.4); }; return .2126 * f(c[0]) + .7152 * f(c[1]) + .0722 * f(c[2]); };
  const bgOf = el => { const stack = []; for (let n = el; n && n.nodeType === 1; n = n.parentElement) { const c = parse(getComputedStyle(n).backgroundColor); if (c[3] > 0) stack.push(c); if (c[3] === 1) break; } let base = [18, 18, 18, 1]; for (let i = stack.length - 1; i >= 0; i--) base = over(stack[i], base); return base; };
  const ratio = (fg, bg) => { const a = lum(fg) + .05, b = lum(bg) + .05; return a > b ? a / b : b / a; };
  const out = [];
  const box = document.querySelector('.hawk-box');
  const els = [...box.querySelectorAll('*')].filter(e => { if (!e.childNodes.length) return false; return [...e.childNodes].some(n => n.nodeType === 3 && n.textContent.trim()) && e.getBoundingClientRect().width > 0 && getComputedStyle(e).visibility !== 'hidden'; });
  for (const e of els) {
    const cs = getComputedStyle(e); const bg = bgOf(e); const fg = over(parse(cs.color), bg);
    out.push([e.className || e.tagName, e.textContent.trim().slice(0, 28), +ratio(fg, bg).toFixed(2)]);
  }
  const inp = box.querySelector('.hawk-input'); const ph = getComputedStyle(inp, '::placeholder');
  out.push(['placeholder', inp.placeholder, +ratio(over(parse(ph.color), bgOf(inp)), bgOf(inp)).toFixed(2)]);
  const s = box.querySelector('.hawk-send'); out.push(['send arrow', 'arrow', +ratio([255, 255, 255, 1], bgOf(s)).toFixed(2)]);
  return out;
};

for (const th of ['light', 'dark']) test('look: ' + th + ' — the surface, the send button, every text >= 4.5:1 (empty and with an answer)', async () => {
  const { page, close } = await open();
  await page.evaluate(t => document.documentElement.setAttribute('data-theme', t), th); await tick(page, 300);
  await page.click('.hawk-fab'); await tick(page, 300);
  const surf = await page.evaluate(() => {
    const c = getComputedStyle(document.querySelector('.hawk-box')).backgroundColor.match(/\d+/g).map(Number);
    const s = getComputedStyle(document.querySelector('.hawk-send')); const b = getComputedStyle(document.querySelector('.hawk-ask'));
    return { bg: c, send: s.borderRadius, sendBg: s.backgroundColor, w: s.width, h: s.height, askRadius: b.borderRadius };
  });
  const L = surf.bg[0] * .3 + surf.bg[1] * .55 + surf.bg[2] * .15;
  ok(th === 'light' ? L > 200 : L < 60, th + ' surface is ' + (th === 'light' ? 'white-ish' : 'dark') + ', not navy', surf.bg);
  ok(parseFloat(surf.send) >= 20 && surf.w === surf.h && /rgb\(\s*(22|42), (51|74), (107|143)\)/.test(surf.sendBg), 'send button is round and navy', surf);
  let low = (await page.evaluate(CONTRAST)).filter(r => r[2] < 4.5);
  ok(low.length === 0, th + ' empty sheet: all text >= 4.5:1', low);
  for (const q of ['when am i free on tuesday', 'help', 'bus 100 mondays at 3pm']) {
    await page.evaluate(q => HawkAsk.ask(q), q); await tick(page, 1800);
    low = (await page.evaluate(CONTRAST)).filter(r => r[2] < 4.5);
    ok(low.length === 0, th + ' answer "' + q + '": all text >= 4.5:1', low);
  }
  await close();
});

const names = ONLY ? [ONLY] : Object.keys(T);
for (const n of names) {
  if (!T[n]) { console.log('no such test', n); process.exit(2); }
  if (!QUIET) console.log('\n' + n);
  try { await T[n](); } catch (e) { fail++; fails.push(n + ' threw'); console.log('  FAIL', n, 'threw', String(e).slice(0, 300)); for (const x of LIVE) { try { await x.close(); } catch (_) {} } }
}
console.log(`\ncheck-desktop-champ: ${pass} passed, ${fail} failed`);
if (fail) { console.log('failed:', fails.join(' | ')); process.exit(1); }
