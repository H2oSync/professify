/* check-desktop-chat-cards — chat-cards (2026-10-16), run on the REAL index.html.
   Tate: "these are still sending links and not cards".
   1. Reading: a text message holding a termchamp.com/s?i=<32hex>.png link (the phone app's "Here’s my … schedule <link>") is a
      schedule card in the thread and in the chat list's preview; the long URL is not shown; the words around it stay.
      Plans say "Plan A · Spring 2027". Anything off-shape stays plain, escaped text.
   2. View opens the picture; Add asks through the existing "Add <name>?" card and writes nothing until that card's Add;
      a friend, yourself, or a link whose add= is not the sender's id gets no Add.
   3. Sending: Share schedule on a desktop shows the sheet with Send to a chat; the send waits for both uploads, posts the
      phone's body as kind 'text', and that body reads back as a card. A failed upload sends nothing and says so.
   4. Opening the link itself (/?i=<hex>.png&nm=…&add=…) lands on the schedule, and says "expired" when the week is not there.
   Run: APP_DIR=<repo> APP_PORT=8437 node check-desktop-chat-cards.mjs [--only read|add|send|open] [--quiet]  */
import path from 'node:path';
import { openApp } from './app-harness.mjs';
import * as FX from './app-fixtures.mjs';

const args = process.argv.slice(2);
const ONLY = args.includes('--only') ? args[args.indexOf('--only') + 1] : null;
const QUIET = args.includes('--quiet');
const want = n => !ONLY || ONLY === n;
let pass = 0, fail = 0;
const ok = (c, name, info) => { if (c) { pass++; if (!QUIET) console.log('  ok  ', name); } else { fail++; console.log('  FAIL', name, info !== undefined ? '→ ' + JSON.stringify(info).slice(0, 500) : ''); } };
const tick = async (p, ms = 500) => { await p.clock.runFor(ms); await p.waitForTimeout(250); };
const desk = (o = {}) => openApp(Object.assign({ path: '/', width: 1440, height: 900, wait: 4000, port: +(process.env.APP_PORT || 8437) }, o));
const clone = x => JSON.parse(JSON.stringify(x));
const ready = async page => { for (let i = 0; i < 40; i++) { if (await page.evaluate(() => typeof friendsLoaded !== 'undefined' && friendsLoaded && !frSignInBusy)) return; await tick(page, 300); } };
const ME = FX.ME, AV = FX.FRIENDS[0], SUG = FX.SUGGESTED;
const C0 = FX.CONVS[0].id, C1 = FX.CONVS[1].id;
const IMG = 'https://rqkndeqbcahozidniesn.supabase.co/storage/v1/object/public/schedule-cards/';
const H1 = 'cc68d9c41252dde55d5fb8b2211a8336', H2 = '797c01b109fbf947b4dfc83ac083c199', H3 = '0123456789abcdef0123456789abcdef';
const L = (h, q, host = 'termchamp.com', ext = 'png') => 'https://' + host + '/s?i=' + h + '.' + ext + (q ? '&' + q : '');
const msg = (id, cid, sender, body) => ({ id, conversation_id: cid, sender, kind: 'text', body, payload: null, created_at: '2026-10-15T' + String(10 + (id % 10)).padStart(2, '0') + ':00:00Z' });
const open = async (o, cid) => { await o.page.evaluate(() => show('friends')); await tick(o.page, 800); await o.page.evaluate(() => msgLoadThreads()); await tick(o.page, 800); if (cid) { await o.page.evaluate(c => msgOpen(c), cid); await tick(o.page, 800); } };
const body = page => page.evaluate(() => (document.getElementById('msgBody') || {}).innerText || '');
const cards = page => page.evaluate(() => [...document.querySelectorAll('#msgBody .ssc')].map(e => ({ title: e.querySelector('.msug-code').innerText, img: (e.querySelector('img') || {}).src || '', acts: [...e.querySelectorAll('.msug-b')].map(b => b.innerText) })));
const PNG = Buffer.from('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR4nGP4z8DwHwAFAAH/q842iQAAAABJRU5ErkJggg==', 'base64');
const pngHook = (url, m) => (m === 'GET' && /^\/storage\/v1\/object\/public\/schedule-cards\/[0-9a-f]{32}\.png$/.test(url.pathname)) ? { status: 200, contentType: 'image/png', body: PNG } : null;
const frWrites = log => log.writes.filter(w => w.table === 'friend_requests');
const msgWrites = log => log.writes.filter(w => w.table === 'messages' && w.m === 'POST');

/* a thread with the shapes below; Avery is a friend, Pat Suggestia is not */
function tables() {
  const t = clone(FX.TABLES);
  t.conversation_members.push({ conversation_id: C1, user_id: SUG.id, last_read_at: null });
  t.messages = [
    msg(11, C0, AV.id, 'Here’s my Fall 2026 schedule ' + L(H1, 'nm=Spoof&tm=Fall%202026&add=' + AV.id)),
    msg(12, C0, ME.id, 'Here’s my Fall 2026 schedule ' + L(H3, 'nm=Tate&tm=Fall%202026&add=' + ME.id)),
    msg(13, C1, SUG.id, 'Here’s my Plan A for Spring 2027 ' + L(H2, 'nm=Pat&tm=Spring%202027&add=' + SUG.id + '&pl=A')),
    msg(14, C1, AV.id, 'forwarded: ' + L(H2, 'nm=Pat&tm=Fall%202026&add=' + SUG.id)),               // add= is not the sender's id
    msg(15, C1, SUG.id, L(H1, 'nm=Pat&add=' + SUG.id)),                                                              // the link alone
  ];
  return t;
}

/* ------------------------------------------------------------------ 1. reading */
if (want('read')) {
  const o = await desk({ tables: tables(), hook: pngHook }); await ready(o.page); await open(o, C0);
  let b = await body(o.page), c = await cards(o.page);
  ok(c.length === 2, 'direct chat: both schedule messages are cards', c);
  ok(c[0] && c[0].title === 'Avery’s Fall 2026 schedule' && c[0].img === IMG + H1 + '.png', 'the card title and the bucket picture (the URL share.ts builds)', c[0]);
  ok(/Here’s my Fall 2026 schedule/.test(b) && !/https?:|termchamp\.com\/s|\?i=|&add=|cc68d9c4/.test(b), 'the words stay, the long URL is hidden', b);
  ok(c[0] && c[0].acts.join() === 'View', 'a friend’s card: View only (no Add)', c[0]);
  ok(c[1] && c[1].acts.join() === 'View' && c[1].title === 'Your Fall 2026 schedule', 'my own card: “Your Fall 2026 schedule”, View only', c[1]);
  ok(c[0] && c[0].title.indexOf('Spoof') < 0, 'a friend’s card is titled with their real name, not the link’s nm', c[0]);
  const list = await o.page.evaluate(() => [...document.querySelectorAll('.msg-trow')].map(e => e.innerText).join(' | '));
  ok(/Here’s my Fall 2026 schedule/.test(list) && !/https?:|\?i=/.test(list), 'the chat list preview shows the words, not the URL', list);
  await o.page.evaluate(c => msgOpen(c), C1); await tick(o.page, 800);
  b = await body(o.page); c = await cards(o.page);
  ok(c.length === 3, 'group chat: three cards (the plan, the forwarded link, the link alone)', c);
  ok(c[0] && c[0].title === 'Pat’s Plan A · Spring 2027' && c[0].img === IMG + H2 + '.png', 'a plan reads “Pat’s Plan A · Spring 2027”', c[0]);
  ok(c[0] && c[0].acts.join() === 'View,Add Pat', 'a stranger’s own link: View and Add Pat', c[0]);
  ok(c[1] && c[1].acts.join() === 'View' && c[1].title === 'Pat’s Fall 2026 schedule', 'a forwarded link (add= is not the sender) gets no Add and uses the link’s own nm', c[1]);
  ok(c[2] && c[2].title === 'Pat’s schedule' && c[2].acts.join() === 'View,Add Pat', 'the link alone: title without a term, Add Pat', c[2]);
  ok(/Plan A for Spring 2027/.test(b) && /forwarded:/.test(b), 'surrounding words kept in the group', b);
  ok(o.log.errors.length === 0, 'no page errors (read)', o.log.errors); await o.close();

  /* the strict shapes: each of these must stay plain, escaped text */
  const evil = '<img src=x onerror="window.__x=1">';
  const t = clone(FX.TABLES);
  const cases = [
    ['another host', 'see ' + L(H1, 'nm=A', 'evil.example')],
    ['a lookalike host', 'see ' + L(H1, 'nm=A', 'termchamp.com.evil.example')],
    ['a professor share (k=p)', 'see ' + L(H1, 'nm=A&k=p&p=ada-examplewood')],
    ['a class share (k=c)', 'see ' + L(H1, 'nm=A&k=c&c=BUS%204442')],
    ['two nm=', 'see ' + L(H1, 'nm=A&nm=B')],
    ['sched= in place of i=', 'see https://termchamp.com/s?sched=abc&nm=A'],
    ['pl=D', 'see ' + L(H1, 'nm=A&pl=D')],
    ['two i=', 'see ' + L(H1, 'i=' + H2 + '.png')],
    ['31 hex', 'see https://termchamp.com/s?i=' + H1.slice(1) + '.png&nm=A'],
    ['uppercase hex', 'see https://termchamp.com/s?i=' + H1.toUpperCase() + '.png&nm=A'],
    ['.jpg', 'see https://termchamp.com/s?i=' + H1 + '.jpg&nm=A'],
    ['http', 'see ' + L(H1, 'nm=A').replace('https', 'http')],
    ['a fragment', 'see ' + L(H1, 'nm=A') + '#x'],
    ['user@host', 'see https://x@termchamp.com/s?i=' + H1 + '.png'],
    ['a port', 'see https://termchamp.com:8443/s?i=' + H1 + '.png'],
    ['another path', 'see https://termchamp.com/x/s?i=' + H1 + '.png'],
    ['junk glued on the id', 'see https://termchamp.com/s?i=' + H1 + '.pngx'],
    ['no i=', 'see https://termchamp.com/s?nm=A&tm=Fall%202026'],
  ];
  const J = 'https://termchamp.com/s?x=1 ';
  const good = [
    msg(61, C0, AV.id, 'see ' + L(H1, 'nm=Utm&utm_source=x&v=2')),                                  // unknown params are ignored
    msg(62, C0, AV.id, 'see ' + L(H1, 'nm=Punc') + '!'),                                              // trailing punctuation
    msg(63, C0, AV.id, 'see ' + L(H1, 'nm=' + encodeURIComponent('Eve\u202Eevil\u200B\u2066'))),    // bidi / zero-width out of a name
    msg(64, C0, AV.id, 'a ' + J.repeat(4) + L(H1, 'nm=Four')),                                        // the fifth candidate is read
  ];
  const tooMany = msg(65, C0, AV.id, 'a ' + J.repeat(5) + L(H1, 'nm=Six'));                          // a sixth is not
  t.messages = cases.map((c, i) => msg(20 + i, C0, AV.id, c[1])).concat([msg(60, C0, AV.id, evil + ' ' + L(H1, 'nm=' + encodeURIComponent(evil) + '&tm=' + encodeURIComponent('<b>x</b>'))), tooMany], good);
  const o2 = await desk({ tables: t }); await ready(o2.page); await open(o2, C0);
  const c2 = await cards(o2.page);
  ok(c2.length === 5, 'only the well-formed links are cards: the markup one, utm_*, a trailing “!”, a bidi name, the fifth candidate; the off-shape ones and a sixth candidate are not', c2.map(x => x.title));
  ok(c2.some(x => x.title === 'Utm’s schedule') && c2.some(x => x.title === 'Punc’s schedule') && c2.some(x => x.title === 'Four’s schedule') && !c2.some(x => /Six/.test(x.title)), 'extra params ignored, trailing punctuation allowed, candidates capped', c2.map(x => x.title));
  ok(c2.some(x => x.title === 'Eve’s schedule') && !c2.some(x => /[\u200b-\u200f\u202a-\u202e\u2060-\u2069\ufeff]/.test(x.title)), 'bidi and zero-width characters are stripped from a name', c2.map(x => x.title));
  const once = await o2.page.evaluate(() => { const m = msgRows[msgOpenId].find(x => msgSchedOf(x)); return !!m && msgSchedOf(m) === msgSchedOf(m) && m._ss === msgSchedOf(m); });
  ok(once, 'the parse is cached on the message');
  const html = await o2.page.evaluate(() => document.getElementById('msgBody').innerHTML);
  ok(c2.some(x => /<img/.test(x.title)) && !/<img src=x/.test(html) && !/<b>x/.test(html) && !(await o2.page.evaluate(() => window.__x)), 'a name/term/text carrying markup is printed escaped, never run', c2.map(x => x.title));
  const plain = await o2.page.evaluate(() => [...document.querySelectorAll('#msgBody .msg-b')].map(e => e.innerText).join('\n'));
  ok(cases.every(c => plain.indexOf(c[1].slice(0, 40)) >= 0), 'every off-shape message is still there as text', plain);
  ok(o2.log.errors.length === 0, 'no page errors (strict shapes)', o2.log.errors); await o2.close();
}

/* ------------------------------------------------------------------ 2. view and add */
if (want('add')) {
  const o = await desk({ tables: tables(), hook: pngHook, rpc: Object.assign({}, FX.RPC, { get_inviter: [{ display_name: SUG.display_name }] }) }); await ready(o.page); await open(o, C1);
  await o.page.locator('#msgBody .ssc .msug-b:has-text("View")').first().click(); await tick(o.page, 400);
  const sheet = await o.page.evaluate(() => { const s = document.getElementById('scSheet'); return s && s.classList.contains('open') ? { h: s.querySelector('.sc-h').innerText, img: (s.querySelector('img.sc-img') || {}).src, btns: [...s.querySelectorAll('button')].map(b => b.innerText.trim()) } : null; });
  ok(sheet && sheet.h === 'Pat’s Plan A · Spring 2027' && sheet.img === IMG + H2 + '.png' && sheet.btns.includes('Add Pat'), 'View opens the picture large with Add Pat', sheet);
  await o.page.locator('#scSheet .sc-x').click(); await tick(o.page, 300);
  ok(!(await o.page.evaluate(() => document.getElementById('scSheet').classList.contains('open'))), 'the sheet closes');
  const OTHER = '44444444-4444-4444-8444-444444444444';
  await o.page.evaluate(id => pendAddSet(id), OTHER);                       // an invite from a link is already waiting
  await o.page.locator('#msgBody .ssc .msug-b:has-text("Add Pat")').first().click(); await tick(o.page, 1500);
  const card = await o.page.evaluate(() => { const e = document.querySelector('#mback.open #modal [data-pendadd]'); return e ? { id: e.getAttribute('data-pendadd'), t: e.innerText } : null; });
  ok(card && card.id === SUG.id && /Add Pat Suggestia\?/.test(card.t), 'Add asks through the invite card: “Add Pat Suggestia?”', card);
  ok(card && !/invite link/i.test(card.t) && /they choose whether to accept/.test(card.t), 'the card from a chat does not say “You opened their invite link”', card && card.t);
  ok(frWrites(o.log).length === 0, 'nothing is written to friend_requests until that card’s Add', frWrites(o.log));
  const keep = () => o.page.evaluate(() => ({ s: sessionStorage.getItem('professify_pending_add'), l: localStorage.getItem('professify_pending_add') }));
  ok(JSON.stringify(await keep()) === JSON.stringify({ s: OTHER, l: OTHER }), 'asking stored nothing and left the waiting invite alone', await keep());
  await o.page.locator('#pendAddYes').click(); await tick(o.page, 1200);
  const w = frWrites(o.log);
  ok(w.length === 1 && w[0].body.to_user === SUG.id && w[0].body.from_user === ME.id && w[0].body.status === 'pending', 'its Add writes exactly one pending request, me to them', w);
  ok(JSON.stringify(await keep()) === JSON.stringify({ s: OTHER, l: OTHER }), 'answering it did not clear the other waiting invite', await keep());
  ok(o.log.errors.length === 0, 'no page errors (add)', o.log.errors); await o.close();
  /* Not now: nothing written, nothing remembered, nothing comes back after a reload */
  {
    const o3 = await desk({ tables: tables(), hook: pngHook, rpc: Object.assign({}, FX.RPC, { get_inviter: [{ display_name: SUG.display_name }] }) }); await ready(o3.page); await open(o3, C1);
    await o3.page.locator('#msgBody .ssc .msug-b:has-text("Add Pat")').first().click(); await tick(o3.page, 1500);
    await o3.page.locator('#pendAddNo').click(); await tick(o3.page, 500);
    const st = await o3.page.evaluate(() => ({ s: sessionStorage.getItem('professify_pending_add'), l: localStorage.getItem('professify_pending_add') }));
    ok(frWrites(o3.log).length === 0 && !st.s && !st.l, 'Not now writes nothing and remembers nothing', { w: frWrites(o3.log), st });
    await o3.page.reload({ waitUntil: 'domcontentloaded' }); await tick(o3.page, 4000);
    ok(!(await o3.page.evaluate(() => !!document.querySelector('#modal [data-pendadd]'))), 'and a reload does not ask again');
    await o3.close();
  }

  /* an image that is not in the bucket: the card says so instead of showing a broken picture */
  const o2 = await desk({ tables: tables(), hook: (url) => url.pathname.startsWith('/storage/v1/object/public/') ? { status: 404, body: '{}' } : null }); await ready(o2.page); await open(o2, C0);
  await tick(o2.page, 500);
  ok(await o2.page.evaluate(() => !!document.querySelector('#msgBody .ssc-img.bad')), 'a picture that 404s turns into “Preview isn’t available”, not a broken image');
  await o2.page.locator('#msgBody .ssc .msug-b:has-text("View")').first().click(); await tick(o2.page, 400);
  ok(/isn.t available any more/.test(await o2.page.evaluate(() => document.getElementById('scSheet').innerText)), 'View says so too');
  await o2.close();
}

/* ------------------------------------------------------------------ 3. sending */
if (want('send')) {
  const run = async (failJson, last, delay) => {
    const o = await desk({ hook: (url, m) => {
        if (failJson && m === 'POST' && /schedule-cards\/[0-9a-f]{32}\.json$/.test(url.pathname)) return { status: 403, body: JSON.stringify({ statusCode: '403', error: 'Unauthorized', message: 'new row violates row-level security policy' }) };
        if (delay && m === 'POST' && url.pathname === '/rest/v1/messages') return new Promise(r => setTimeout(() => r(null), delay));
        return null; },
      init: () => { navigator.share = () => Promise.resolve(); } });
    await ready(o.page);
    await o.page.evaluate(() => show('friends')); await tick(o.page, 500); await o.page.evaluate(() => msgLoadThreads()); await tick(o.page, 500);
    ok(await o.page.evaluate(() => myClasses.length > 0 && scCanUpload() && msgOn()), 'set-up: classes, signed in, uploads and messaging on');
    await o.page.evaluate(() => shareMySchedule()); await tick(o.page, 800);
    const sh = await o.page.evaluate(() => { const s = document.getElementById('scSheet'); return s && s.classList.contains('open') ? [...s.querySelectorAll('.sc-acts > *')].map(b => b.innerText.trim()) : null; });
    ok(sh && sh.includes('Send to a chat') && sh.includes('Copy the link') && sh.includes('Share…'), 'desktop with a native share: the sheet shows Send to a chat, Copy the link and Share…', sh);
    const ups = o.log.writes.filter(w => /^storage:/.test(w.table));
    if (!failJson) ok(ups.length === 2 && ups.some(u => /\.png$/.test(u.table)) && ups.some(u => /\.json$/.test(u.table)) && ups.every(u => u.upsert !== 'true'), 'the picture and the week are uploaded (no upsert)', ups.map(u => u.table + ' ' + u.upsert));
    await o.page.locator('#scSheet .fr-chip:has-text("Send to a chat")').click(); await tick(o.page, 600);
    const pick = await o.page.evaluate(() => { const b = document.getElementById('shBack'); return b && b.classList.contains('open') ? { t: b.querySelector('.sh-title').innerText, rows: [...b.querySelectorAll('.sh-row')].map(r => r.innerText.replace(/\s+/g, ' ')) } : null; });
    ok(pick && /My Fall 2026 schedule|My .* schedule/.test(pick.t) && pick.rows.length >= 1, 'the chat picker opens', pick);
    const row = o.page.locator('#shBack .sh-row'); const rowN = last ? await row.count() - 1 : 0;
    if (delay) {
      await row.nth(rowN).click(); await o.page.waitForTimeout(100);
      const dis = await o.page.evaluate(() => [...document.querySelectorAll('#shBack .sh-row')].every(r => r.disabled));
      await o.page.evaluate(() => { try { document.querySelectorAll('#shBack .sh-row')[0].click(); shSendTo(msgThreads[0].id, null); } catch (e) {} });   // a second tap, and a second call
      await o.page.evaluate(() => shClose());                                                                       // the sheet is closed mid-send
      o.dis = dis; await o.page.waitForTimeout(delay + 400); await tick(o.page, 1200);
    } else { await row.nth(rowN).click(); await tick(o.page, 1500); }
    return o;
  };
  {
    const o = await run(false);
    const w = msgWrites(o.log);
    ok(w.length === 1 && w[0].body.kind === 'text' && w[0].body.payload == null, 'one message posted, kind text, no payload (the phone’s format; the table has no schedule kind)', w.map(x => x.body));
    const b = w[0] && w[0].body.body;
    ok(/^Here’s my Fall 2026 schedule https:\/\/termchamp\.com\/s\?i=[0-9a-f]{32}\.png&nm=[^&]+&tm=Fall%202026&add=/.test(b || ''), 'the body is “Here’s my Fall 2026 schedule <link>”, the phone’s words and link', b);
    ok(await o.page.evaluate(x => !!msgSchedParse(x) && msgSchedParse(x).add === (sbUser.id), b), 'and it reads back as a card, with my id as add=');
    ok((b || '').length < 400, 'short enough (payload and body stay small)', (b || '').length);
    ok(/Sent /.test(await o.page.evaluate(() => (document.getElementById('frToast') || {}).textContent || '')), 'Sent toast');
    ok(await o.page.evaluate(() => !!document.querySelector('#msgBody .ssc')), 'the thread it landed in shows it as a card');
    ok(o.log.errors.length === 0, 'no page errors (send)', o.log.errors); await o.close();
  }
  {
    const o = await run(true, true);
    ok(msgWrites(o.log).length === 0, 'the week failed to upload: no message is sent', msgWrites(o.log));
    ok(o.log.writes.filter(w => w.table === 'conversations' || w.table === 'conversation_members').length === 0, 'and no conversation is created for it (a friend with no chat yet was picked)', o.log.writes.map(w => w.table));
    ok(/Couldn’t get the schedule link ready\. Close this and share your schedule again/.test(await o.page.evaluate(() => (document.getElementById('frToast') || {}).textContent || '')), 'it says to share again, not “try again”');
    ok(!(await o.page.evaluate(() => document.getElementById('shBack').classList.contains('open'))), 'and the picker is closed (asking again could never succeed)');
    ok(o.log.errors.length === 0, 'no page errors (failed upload)', o.log.errors);
    await o.close();
  }
  {
    /* a slow send: rows disabled, a second tap does nothing, and closing the sheet mid-send throws nothing */
    const o = await run(false, false, 900);
    ok(o.dis === true, 'while a send is in flight the rows are disabled');
    ok(msgWrites(o.log).length === 1, 'a second tap on a row while sending sends nothing more (one message)', msgWrites(o.log).length);
    ok(o.log.errors.length === 0, 'closing the sheet mid-send throws nothing', o.log.errors);
    ok(/Sent /.test(await o.page.evaluate(() => (document.getElementById('frToast') || {}).textContent || '')) || msgWrites(o.log).length === 1, 'and the message still went out');
    await o.close();
  }
  {
    /* a phone (touch, no fine pointer) keeps the native share sheet straight away */
    const o = await openApp({ path: '/', width: 390, height: 844, wait: 4000, port: +(process.env.APP_PORT || 8437), init: () => { window.__shared = null; navigator.share = u => { window.__shared = u; return Promise.resolve(); }; } });
    await ready(o.page);
    await o.page.evaluate(() => show('friends')); await tick(o.page, 500); await o.page.evaluate(() => msgLoadThreads()); await tick(o.page, 500);
    await o.page.evaluate(() => shareMySchedule()); await tick(o.page, 600);
    const r = await o.page.evaluate(() => ({ shared: window.__shared, sheet: !!(document.getElementById('scSheet') && document.getElementById('scSheet').classList.contains('open')) }));
    ok(r.shared && /\/s\?i=[0-9a-f]{32}\.png/.test(r.shared.url || '') && !r.sheet, 'a phone: the native share sheet opens at once, as before', r);
    await o.close();
  }
}

/* ------------------------------------------------------------------ 4. opening the link itself */
if (want('open')) {
  const week = enc => ({ status: 200, contentType: 'text/plain', body: enc });
  for (const signedIn of [true, false]) {
    let enc = '';
    const pre = await desk({ signedIn, path: '/' });
    enc = await pre.page.evaluate(() => _b64urlEnc(_shEncode('Fall 2026', [{ c: 'BUS 3438', n: '', t: 'MWF 10:10AM–11:00AM', p: 'Ada Examplewood', s: '01' }, { c: 'ECON 2303', n: '', t: 'TR 1:10PM–2:30PM', p: 'Staff', s: '03' }]))); await pre.close();
    const o = await desk({ signedIn, path: '/', search: '?i=' + H1 + '.png&nm=Tate&tm=Fall%202026&add=' + SUG.id, hook: (url, m) => (m === 'GET' && url.pathname === '/storage/v1/object/public/schedule-cards/' + H1 + '.json') ? week(enc) : null, rpc: Object.assign({}, FX.RPC, { get_inviter: [{ display_name: 'Tate Sims' }] }) });
    await tick(o.page, 1200);
    const land = await o.page.evaluate(() => { const e = document.getElementById('schedLanding'); return e && e.style.display === 'flex' ? e.innerText : null; });
    ok(land && /Tate/.test(land) && /BUS 3438/.test(land) && /ECON 2303/.test(land) && /Add Tate/.test(land), (signedIn ? 'signed in' : 'signed out') + ': /?i=<hex>.png&… lands on Tate’s schedule with its classes and Add Tate', land);
    await o.close();
  }
  {
    const o = await desk({ path: '/', search: '?i=' + H1 + '.png&nm=Tate&tm=Fall%202026&add=' + SUG.id, hook: (url, m) => (m === 'GET' && url.pathname === '/storage/v1/object/public/schedule-cards/' + H1 + '.json') ? { status: 400, body: '{"statusCode":"404","error":"not_found","message":"Object not found"}' } : null });
    await tick(o.page, 1200);
    ok(/expired — ask Tate/.test(await o.page.evaluate(() => (document.getElementById('frToast') || {}).textContent || '')), 'the week is not in the bucket: “That schedule link has expired — ask Tate to send it again.”');
    await o.close();
  }
}

console.log((fail ? 'FAILED' : 'PASSED') + ': ' + pass + ' passed, ' + fail + ' failed');
process.exit(fail ? 1 : 0);
