/* check-desktop-chat-links — chat-links (2026-10-16), run on the REAL index.html.
   1. A message bubble's http(s) links are clickable: only http: and https:, everything escaped, the href is URL.href, text shown
      cut when long, trailing . , ) ! ? not part of the link, many links in one message, a schedule link is still a card, the
      chat list preview stays plain text. Attacker text (javascript:, data:, "><img onerror>, lookalikes, 3000 characters) makes no
      script, no extra element, no on* attribute and no non-http link. A termchamp.com ?p= / ?c= link opens inside the site.
   2. Rate page on a phone: Back closes the review sheet and stays on the page; closing the sheet any other way leaves no extra
      history entry; a desktop is unchanged.
   Run: APP_DIR=<repo> node check-desktop-chat-links.mjs [--only links|thread|site|sheet|desktop] [--quiet] [--shots dir] */
import path from 'node:path';
import { openApp } from './app-harness.mjs';
import * as FX from './app-fixtures.mjs';

const args = process.argv.slice(2);
const ONLY = args.includes('--only') ? args[args.indexOf('--only') + 1] : null;
const QUIET = args.includes('--quiet');
const SHOTS = args.includes('--shots') ? args[args.indexOf('--shots') + 1] : null;
const want = n => !ONLY || ONLY === n;
let pass = 0, fail = 0;
const ok = (c, name, info) => { if (c) { pass++; if (!QUIET) console.log('  ok  ', name); } else { fail++; console.log('  FAIL', name, info !== undefined ? '→ ' + JSON.stringify(info).slice(0, 600) : ''); } };
const PORT0 = +(process.env.APP_PORT || (8300 + Math.floor(Math.random() * 600)));
let portN = 0;
const tick = async (p, ms = 500) => { await p.clock.runFor(ms); await p.waitForTimeout(250); };
const until = async (p, fn, arg, max = 40) => { for (let i = 0; i < max; i++) { if (await p.evaluate(fn, arg).catch(() => false)) return true; await tick(p, 250); } return false; };
const clone = x => JSON.parse(JSON.stringify(x));
const desk = (o = {}) => openApp(Object.assign({ path: '/', width: 1440, height: 900, wait: 4000, port: PORT0 + (portN++), init: `try{localStorage.setItem('professify-theme','dark')}catch(e){}` }, o));
const ready = async page => { for (let i = 0; i < 40; i++) { if (await page.evaluate(() => typeof friendsLoaded !== 'undefined' && friendsLoaded && !frSignInBusy)) return; await tick(page, 300); } };
const ME = FX.ME, AV = FX.FRIENDS[0];
const C0 = FX.CONVS[0].id;
const H1 = 'cc68d9c41252dde55d5fb8b2211a8336';
const msg = (id, cid, sender, body) => ({ id, conversation_id: cid, sender, kind: 'text', body, payload: null, created_at: '2026-10-15T' + String(10 + (id % 10)).padStart(2, '0') + ':00:00Z' });
const openChat = async (o, cid) => { await o.page.evaluate(() => show('friends')); await tick(o.page, 800); await o.page.evaluate(() => msgLoadThreads()); await tick(o.page, 800); if (cid) { await o.page.evaluate(c => msgOpen(c), cid); await tick(o.page, 800); } };
const ProfId = p => p.evaluate(() => Object.keys(PROFESSORS).find(i => /Ada Examplewood/.test(PROFESSORS[i].name)));

/* msgLinkHtml, parsed back into a DOM in a sandbox page: what elements/attributes did a text turn into? */
const parse = (page, text) => page.evaluate(t => {
  const html = msgLinkHtml(t);
  const d = new DOMParser().parseFromString('<body><div id=r>' + html + '</div></body>', 'text/html').getElementById('r');
  const els = [...d.querySelectorAll('*')];
  return { html, text: d.textContent, tags: els.map(e => e.tagName), anchors: [...d.querySelectorAll('a')].map(a => ({ href: a.getAttribute('href'), text: a.textContent, target: a.getAttribute('target'), rel: a.getAttribute('rel'), cls: a.className, attrs: [...a.attributes].map(x => x.name) })),
    on: els.some(e => [...e.attributes].some(a => /^on/i.test(a.name))), roundtrip: d.textContent === t.replace(/\u0000/g, '') };
}, text);

if (want('links')) {
  const o = await desk(); await ready(o.page); const p = o.page;
  const one = async (t) => parse(p, t);
  let r = await one('see https://example.com/a?b=1&c=2 ok');
  ok(r.anchors.length === 1 && r.anchors[0].href === 'https://example.com/a?b=1&c=2' && r.anchors[0].text === 'https://example.com/a?b=1&c=2' && r.tags.join() === 'A' && r.roundtrip, 'a plain https link is one anchor with the same text', r);
  ok(r.anchors[0].target === '_blank' && r.anchors[0].rel === 'noopener noreferrer nofollow ugc' && r.anchors[0].cls === 'msg-link', 'target=_blank and rel="noopener noreferrer nofollow ugc"', r.anchors[0]);
  r = await one('go http://example.org/x now');
  ok(r.anchors.length === 1 && r.anchors[0].href === 'http://example.org/x', 'http links work too', r);
  r = await one('HTTPS://EXAMPLE.com/Path');
  ok(r.anchors.length === 1 && r.anchors[0].href === 'https://example.com/Path', 'upper-case scheme and host: href comes from new URL()', r.anchors);
  for (const [t, href] of [['look https://example.com/a.', 'https://example.com/a'], ['(see https://example.com/a)', 'https://example.com/a'], ['wow https://example.com/a!', 'https://example.com/a'], ['really https://example.com/a?', 'https://example.com/a'], ['a, https://example.com/a, b', 'https://example.com/a'], ['https://example.com/a).', 'https://example.com/a'], ['https://example.com/a!?.,', 'https://example.com/a'], ['https://example.com/wiki/Foo_(bar)', 'https://example.com/wiki/Foo_(bar)'], ['(https://example.com/wiki/Foo_(bar))', 'https://example.com/wiki/Foo_(bar)']]) {
    r = await one(t);
    ok(r.anchors.length === 1 && r.anchors[0].href === href && r.roundtrip, 'trailing punctuation: ' + t, r.anchors);
  }
  r = await one('a https://a.example/1 b https://b.example/2, c (https://c.example/3) d https://d.example/4.');
  ok(r.anchors.map(a => a.href).join(' ') === 'https://a.example/1 https://b.example/2 https://c.example/3 https://d.example/4' && r.roundtrip, 'several links in one message are all links', r.anchors);
  r = await one(Array.from({ length: 30 }, (_, i) => 'https://x' + i + '.example/').join(' '));
  ok(r.anchors.length === 10 && r.roundtrip, 'at most 10 links per message, the rest stay text', r.anchors.length);
  /* long */
  const long = 'https://example.com/' + 'a'.repeat(2980);
  r = await one('read ' + long + ' now');
  ok(r.anchors.length === 1 && r.anchors[0].href === long && r.anchors[0].text.length === 56 && r.anchors[0].text.endsWith('…') && r.html.length < 6500, 'a 3000-character URL: one link, the whole href, the text cut to 56 with an ellipsis', { n: r.anchors[0] && r.anchors[0].text.length, hl: r.html.length });
  /* speed: a pathological message is linear */
  const t0 = Date.now();
  await one('http://' + 'a.'.repeat(20000) + ' ' + 'https://'.repeat(5000) + ' ' + '(('.repeat(10000) + ')'.repeat(30000));
  await one('http://a.b/' + ')'.repeat(100000));
  await one('x'.repeat(200000) + 'https://' + '!'.repeat(100000));
  ok(Date.now() - t0 < 3000, 'pathological text is handled in linear time', Date.now() - t0);
  /* XSS and the like */
  const evil = [
    'javascript:alert(1)', 'JaVaScRiPt:alert(1)', 'see javascript://example.com/%0aalert(1)', 'data:text/html,<script>alert(1)</script>', 'vbscript:msgbox(1)', 'file:///etc/passwd', 'ftp://example.com/x', 'blob:https://example.com/x',
    '"><img src=x onerror=alert(1)>', '<img src=x onerror=alert(1)>', '<a href="javascript:alert(1)">x</a>', '[click](javascript:alert(1))', 'https://example.com/"><img src=x onerror=alert(1)>',
    'https://example.com/"onmouseover="alert(1)', "https://example.com/'onmouseover='alert(1)", 'https://example.com/<script>alert(1)</script>', 'https://example.com/`onerror=alert(1)`',
    'https://user:pw@example.com/', 'https://termchamp.com@evil.example/', 'https://localhost/', 'https://nodot/', 'https://example./', 'http://', 'https://', 'https:// example.com', 'https:///example.com',
    'https://ex​ample.com/', 'https://example.com‮/gpj.exe', 'java\nscript:alert(1)', 'https://example.com/&quot;&gt;', 'HTTP://\u0000example.com'];
  for (const t of evil) {
    r = await one(t);
    const bad = r.anchors.filter(a => !/^https?:\/\//i.test(a.href) || a.attrs.some(x => !['class', 'href', 'target', 'rel', 'title', 'data-site', 'data-v'].includes(x)));
    ok(!r.on && r.tags.every(x => x === 'A') && bad.length === 0 && r.roundtrip, 'attacker text: ' + JSON.stringify(t).slice(0, 70), r);
  }
  /* what stays plain */
  for (const t of ['javascript:alert(1)', 'data:text/html,hi', 'https://user:pw@example.com/', 'https://nodot/', 'ftp://example.com/x', 'https://termchamp.com@evil.example/']) {
    r = await one(t); ok(r.anchors.length === 0, 'not linked: ' + t, r.anchors);
  }
  /* the dangerous half of a "link": text stops at the quote, the link is only the safe part, markup stays text */
  r = await one('https://example.com/a"><img src=x onerror=alert(1)>');
  ok(r.anchors.length === 1 && r.anchors[0].href === 'https://example.com/a' && r.text === 'https://example.com/a"><img src=x onerror=alert(1)>' && r.tags.join() === 'A', 'a quote ends the link; the markup after it is text', r);
  /* lookalike hosts: shown as the real (punycode) address */
  r = await one('https://аpple.com/login');
  ok(r.anchors.length === 1 && /^https:\/\/xn--/.test(r.anchors[0].href) && /^https:\/\/xn--/.test(r.anchors[0].text), 'a Cyrillic lookalike host is shown as its punycode address', r.anchors);
  r = await one('https://exａmple.com/');
  ok(r.anchors.length === 1 && r.anchors[0].text === r.anchors[0].href && /^[\x21-\x7e]+$/.test(r.anchors[0].text), 'a full-width letter is shown as the normalised address', r.anchors);
  /* no change to ordinary text */
  for (const t of ['hello <b>world</b> & "co"', "it's // fine", '', 'a//b http:/x https:/', 'termchamp.com/s?x']) { r = await one(t); ok(r.anchors.length === 0 && r.roundtrip && r.tags.length === 0, 'no link, text untouched: ' + JSON.stringify(t), r); }
  ok(await p.evaluate(() => msgLinkHtml(null) === '' && msgLinkHtml(undefined) === '' && msgLinkHtml(12) === '12'), 'null / undefined / number are safe');
  ok(o.log.errors.length === 0, 'no page errors', o.log.errors); await o.close();
}

if (want('thread')) {
  const t = clone(FX.TABLES);
  const SCHED = 'https://termchamp.com/s?i=' + H1 + '.png&nm=Avery&tm=Fall%202026&add=' + AV.id;
  t.messages = [
    msg(11, C0, AV.id, 'check https://example.com/a?x=1&y=2. thanks'),
    msg(12, C0, ME.id, 'mine: https://example.org/b and javascript:alert(1)'),
    msg(13, C0, AV.id, 'Here’s my Fall 2026 schedule ' + SCHED),
    msg(14, C0, AV.id, 'also ' + SCHED + ' and https://example.net/c'),
    msg(15, C0, AV.id, '"><img src=x onerror="window.__x=1"> https://example.com/q'),
    msg(16, C0, AV.id, 'https://example.com/' + 'z'.repeat(3000)),
  ];
  const o = await desk({ tables: t, hook: (url, m) => (m === 'GET' && /schedule-cards/.test(url.pathname)) ? { status: 404, body: '{}' } : null }); await ready(o.page); await openChat(o, C0);
  const p = o.page;
  const d = await p.evaluate(() => ({ links: [...document.querySelectorAll('#msgBody .msg-b a.msg-link')].map(a => ({ h: a.href, t: a.textContent, inMe: !!a.closest('.msg-b.me'), target: a.target, rel: a.rel })),
    cards: document.querySelectorAll('#msgBody .ssc').length, imgs: [...document.querySelectorAll('#msgBody img')].filter(i => i.getAttribute('onerror') && /__x/.test(i.getAttribute('onerror'))).length, x: window.__x === undefined,
    text: document.getElementById('msgBody').innerText, anyJs: [...document.querySelectorAll('#msgBody a')].some(a => !/^https?:/.test(a.href)) }));
  ok(d.links.length === 5, 'the thread has five plain links (two in single messages, one beside a card, one after markup text, the long one)', d.links.map(l => l.h.slice(0, 50)));
  ok(d.links[0].h === 'https://example.com/a?x=1&y=2' && d.links[0].t === 'https://example.com/a?x=1&y=2' && / thanks/.test(d.text), 'a link followed by a full stop: the stop and the words stay outside the link', d.links[0]);
  ok(d.links[1].inMe && d.links[1].h === 'https://example.org/b' && !d.links.some(l => /alert/.test(l.h)), 'my own bubble links too; the javascript: text is not a link', d.links[1]);
  ok(d.cards === 2 && !/termchamp\.com\/s\?i=/.test(d.text), 'schedule links are still cards (two), their URL is not shown', { cards: d.cards });
  ok(d.links[2].h === 'https://example.net/c', 'a plain link beside a schedule link is a link next to the card', d.links[2]);
  ok(d.imgs === 0 && d.x && !d.anyJs, 'the "><img onerror> message made no image and ran nothing', d);
  ok(/"><img src=x onerror="window\.__x=1"> /.test(d.text), 'its markup shows as text', d.text.slice(0, 400));
  ok(d.links[4].t.length === 56 && d.links[4].h.length === 3020, 'the 3000-character link is cut to 56 characters and links the whole address', { t: d.links[4].t.length, h: d.links[4].h.length });
  ok(d.links.every(l => l.target === '_blank' && l.rel === 'noopener noreferrer nofollow ugc'), 'every link opens a new tab with rel noopener noreferrer nofollow ugc', d.links);
  const list = await p.evaluate(() => [...document.querySelectorAll('.msg-trow')].map(e => ({ t: e.innerText, a: e.querySelectorAll('a').length })));
  ok(list.every(r => r.a === 0), 'the chat list preview has no links (plain text)', list);
  /* a click on a link opens it in a new tab and does not leave the page */
  const [pop] = await Promise.all([p.context().waitForEvent('page', { timeout: 4000 }).catch(() => null), p.click('#msgBody a.msg-link >> nth=0')]);
  ok(!!pop, 'clicking a link opens a new tab'); if (pop) await pop.close().catch(() => {});
  ok(await p.evaluate(() => !!document.getElementById('msgBody') && /friends/.test((document.querySelector('.view.active') || {}).id || '')), 'the chat is still open');
  if (SHOTS) { await p.screenshot({ path: path.join(SHOTS, 'chat-desktop-dark.png') }); }
  ok(o.log.errors.length === 0, 'no page errors', o.log.errors); await o.close();
  if (SHOTS) {
    const o2 = await desk({ tables: t, width: 390, height: 844, hook: (url, m) => (m === 'GET' && /schedule-cards/.test(url.pathname)) ? { status: 404, body: '{}' } : null }); await ready(o2.page); await openChat(o2, C0);
    await o2.page.screenshot({ path: path.join(SHOTS, 'chat-phone-dark.png') }); await o2.close();
  }
}

if (want('site')) {
  const S = 'https://termchamp.com/';
  const t = clone(FX.TABLES);
  t.messages = [msg(31, C0, AV.id, 'prof ' + S + '?p=ada-examplewood'), msg(32, C0, AV.id, 'class ' + S + '?c=BUS%204442'), msg(33, C0, AV.id, 'other ' + S + '?tab=rate and ' + S + '?p=a&add=x and ' + S + 'about'), msg(34, C0, AV.id, 'nobody ' + S + '?p=nobody-here-at-all')];
  const o = await desk({ tables: t }); await ready(o.page); await openChat(o, C0); const p = o.page;
  const a = await p.evaluate(() => [...document.querySelectorAll('#msgBody a.msg-link')].map(a => ({ t: a.textContent, site: a.getAttribute('data-site'), v: a.getAttribute('data-v'), target: a.getAttribute('target') })));
  ok(a[0].site === 'p' && a[0].target === null && a[1].site === 'c' && a[1].v === 'BUS 4442' && a[1].target === null, 'a termchamp.com ?p= and ?c= link are same-tab site links', a);
  ok(a.slice(2, 5).every(x => x.site === null && x.target === '_blank'), 'other termchamp.com links (?tab=, ?p= with more params, another path) are ordinary new-tab links', a);
  const href0 = await p.evaluate(() => location.href);
  await p.click('#msgBody a.msg-link >> nth=0'); await tick(p, 900);
  const r1 = await p.evaluate(() => ({ href: location.href, cur: typeof currentProf !== 'undefined' ? currentProf : null, view: (document.querySelector('.view.active') || {}).id, txt: document.body.innerText.includes('Ada Examplewood'), open: [...document.querySelectorAll('.open')].map(e => e.id) }));
  ok(r1.href === href0 && r1.cur === 'pr_p1', 'clicking the professor link opens that professor inside the site, no reload', r1);
  await p.evaluate(() => { try { closeModal(); } catch (e) {} try { navCloseAll(); } catch (e) {} }); await tick(p, 300);
  await openChat(o, C0);
  await p.click('#msgBody a.msg-link >> nth=1'); await tick(p, 900);
  const r2 = await p.evaluate(() => ({ href: location.href, view: (document.querySelector('.view.active') || {}).id, q: (document.getElementById('exQuery') || {}).value }));
  ok(r2.href === href0 && r2.view === 'view-explore' && /BUS 4442/i.test(r2.q), 'the class link opens Explore on that class, no reload', r2);
  ok(o.log.errors.length === 0, 'no page errors', o.log.errors); await o.close();
}

/* ------------------------------------------------------------------ 2. Back with the Rate sheet open */
const hist = p => p.evaluate(() => ({ len: history.length, st: history.state, view: (document.querySelector('.view.active') || {}).id, sheet: document.getElementById('view-rate').classList.contains('rt-sheet'), form: !!document.querySelector('#rtLists .rt-item.open #rfSubmit'), nav: !!window._rtNav, loc: location.pathname + location.search }));
const rateReady = async (o) => { await until(o.page, () => { try { return !!sbUser && nowMine().classes.length > 0; } catch (e) { return false; } }); await o.page.evaluate(() => openRate()); await tick(o.page, 900); };
const openFirst = async p => { await p.evaluate(() => { const b = document.querySelector('#rtLists .rt-item .rt-rate'); b.click(); }); await tick(p, 700); };

if (want('sheet')) {
  { /* Back closes the sheet, not the page */
    const o = await desk({ width: 390, height: 844 }); const p = o.page; await rateReady(o);
    const h0 = await hist(p);
    ok(h0.view === 'view-rate' && !h0.sheet, 'phone: on the Rate page, no sheet', h0);
    await openFirst(p); const h1 = await hist(p);
    ok(h1.sheet && h1.form && h1.nav && h1.len === h0.len + 1 && h1.st && h1.st.kind === 'rtsheet', 'opening the sheet pushes exactly one history entry', { h0, h1 });
    if (SHOTS) await p.screenshot({ path: path.join(SHOTS, 'sheet-phone-open.png') });
    await p.goBack(); await tick(p, 700);
    const h2 = await hist(p);
    ok(h2.view === 'view-rate' && !h2.sheet && !h2.form && !h2.nav, 'Back closes the sheet and stays on the Rate page', h2);
    ok(h2.st && h2.st.kind === 'view' && h2.len === h1.len, 'the entry we came back to is the page’s own', h2);
    await p.goBack(); await tick(p, 700);
    const h3 = await hist(p);
    ok(h3.view !== 'view-rate' || h3.st == null || h3.st.val !== 'rate', 'a second Back then does what it did before (leaves the Rate page)', h3);
    ok(o.log.errors.length === 0, 'no page errors', o.log.errors); await o.close();
  }
  { /* closing the sheet by other means takes its entry off again */
    const closers = {
      'Escape': p => p.keyboard.press('Escape'),
      'tapping outside': p => p.mouse.click(195, 30),
      'rtClose()': p => p.evaluate(() => rtClose()),
      'rateDone()': p => p.evaluate(() => rateDone()),
    };
    for (const [name, fn] of Object.entries(closers)) {
      const o = await desk({ width: 390, height: 844 }); const p = o.page; await rateReady(o);
      const h0 = await hist(p); await openFirst(p); const h1 = await hist(p);
      await fn(p); await tick(p, 900);
      const h2 = await hist(p);
      ok(h1.sheet && !h2.sheet && !h2.nav && h2.len === h1.len && h2.st && h2.st.kind === 'view' && h2.view === 'view-rate', 'closing with ' + name + ': the sheet’s entry is gone (we stand on the page’s own entry)', { h0, h1, h2 });
      await p.goBack(); await tick(p, 700);
      const h3 = await hist(p);
      ok(!h3.sheet && h3.nav === false, 'closing with ' + name + ': one Back afterwards does not reopen or break anything', h3);
      ok(o.log.errors.length === 0, name + ': no page errors', o.log.errors); await o.close();
    }
  }
  { /* open, close, open again, Back */
    const o = await desk({ width: 390, height: 844 }); const p = o.page; await rateReady(o);
    const h0 = await hist(p);
    await openFirst(p); await p.keyboard.press('Escape'); await tick(p, 500); await openFirst(p);
    const h1 = await hist(p);
    ok(h1.sheet && h1.len <= h0.len + 1, 'open, close, open: at most one entry on top of where we began', { h0, h1 });
    await p.goBack(); await tick(p, 700);
    const h2 = await hist(p);
    ok(h2.view === 'view-rate' && !h2.sheet, 'Back closes the second opening too', h2);
    await o.close();
  }
  { /* leaving the page while the sheet is open (a tab tap): no stray entry, Back goes where it always went */
    const o = await desk({ width: 390, height: 844 }); const p = o.page; await rateReady(o);
    const h0 = await hist(p); await openFirst(p);
    await p.evaluate(() => show('home')); await tick(p, 900);
    const h2 = await hist(p);
    ok(h2.view === 'view-home' && !h2.sheet && !h2.nav && h2.len === h0.len + 1 && h2.st && h2.st.kind === 'view' && h2.st.val === 'home', 'tapping another tab with the sheet open: the sheet’s entry becomes the new page’s entry', { h0, h2 });
    await p.goBack(); await tick(p, 700);
    const h3 = await hist(p);
    ok(h3.view === 'view-rate' && !h3.sheet, 'Back from there returns to the Rate page, sheet closed', h3);
    ok(o.log.errors.length === 0, 'no page errors', o.log.errors); await o.close();
  }
  { /* the sheet, then the window grows to a desktop */
    const o = await desk({ width: 390, height: 844 }); const p = o.page; await rateReady(o);
    const h0 = await hist(p); await openFirst(p);
    await p.setViewportSize({ width: 1300, height: 900 }); await tick(p, 900);
    const h2 = await hist(p);
    ok(!h2.sheet && h2.form && !h2.nav && h2.len === h0.len + 1 && h2.st && h2.st.kind === 'view', 'phone to desktop: the form stays, the sheet’s entry is taken off', { h0, h2 });
    await o.close();
  }
  { /* signing out with the sheet open */
    const o = await desk({ width: 390, height: 844 }); const p = o.page; await rateReady(o);
    const h0 = await hist(p); await openFirst(p);
    await p.evaluate(() => { sbUser = null; updateAuthUI(); }); await tick(p, 900);
    const h2 = await hist(p);
    ok(!h2.sheet && !h2.form && h2.len === h0.len + 1 && h2.st && h2.st.kind === 'view', 'signing out closes the sheet and its entry', { h0, h2 });
    await o.close();
  }
}

if (want('desktop')) {
  const o = await desk({ width: 1300, height: 900 }); const p = o.page; await rateReady(o);
  const h0 = await hist(p); await openFirst(p); const h1 = await hist(p);
  ok(h1.form && !h1.sheet && h1.len === h0.len && !h1.nav, 'desktop: the form opens in the row and pushes no history entry', { h0, h1 });
  await p.goBack(); await tick(p, 700);
  const h2 = await hist(p);
  ok(h2.view !== 'view-rate' || h2.st == null || h2.st.val !== 'rate', 'desktop: Back leaves the Rate page as before', h2);
  await o.close();
}

console.log((fail ? 'FAILED' : 'PASSED') + ': ' + pass + ' passed, ' + fail + ' failed');
process.exit(fail ? 1 : 0);
