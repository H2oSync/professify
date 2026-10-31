/* Scale fixes, 2026-10-30. Runs the real app (and website) against the stress harness (PostgREST stand-in
   capped at 1000 rows a request, like db-max-rows). Each block fails on HEAD and passes with the patches.
   Usage: APP_DIR=<site dir> APP_PORT=87xx node scale-fixes.mjs [chat|previews|hides|clock|watch|website] */
import { openApp } from '/tmp/claude-0/stress/harness.mjs';
import { build, fid } from '/tmp/claude-0/stress/bigfx.mjs';
import * as FX from '/home/claude/tc/app-icon/app-dev/tests/app-fixtures.mjs';
const only = process.argv.slice(2);
const want = k => !only.length || only.includes(k);
let pass = 0, fail = 0;
const ok = (c, m, d) => { c ? pass++ : fail++; console.log((c ? '  ok   ' : '  FAIL ') + m + (!c && d !== undefined ? ' ' + JSON.stringify(d).slice(0, 400) : '')); };
const port = +(process.env.APP_PORT || 8721);
const ME = FX.ME.id;
const cors = { 'access-control-allow-origin': '*', 'access-control-allow-headers': '*', 'access-control-allow-methods': '*', 'access-control-expose-headers': 'content-range' };

/* 13 chats: 0 has 500 messages, 1 and 2 have 400 each (the busy ones), 3..12 have 11; every chat's newest is from the friend, all unread */
function chatTables() {
  const T = build({ friends: 20, threads: 13, perThread: 11, seatsN: 200, myHist: 0 });
  const ids = T.conversations.filter(c => c.id.startsWith('c5555555')).map(c => c.id);
  let mid = 900000; const base = Date.parse('2026-09-28T22:00:00Z');
  const add = (cid, n, end, who) => { for (let k = 0; k < n; k++) T.messages.push({ id: mid++, conversation_id: cid, sender: k % 2 ? ME : who, kind: 'text', body: `BULK ${cid.slice(-2)} #${k}${k === n - 1 ? ' NEWEST-BULK' : ''}`, payload: null, created_at: new Date(end - (n - 1 - k) * 1000).toISOString() }); };
  add(ids[0], 489, base, fid(0)); add(ids[1], 389, base - 1800e3, fid(1)); add(ids[2], 389, base - 2 * 1800e3, fid(2));
  T.conversations.forEach(c => { const m = T.messages.filter(x => x.conversation_id === c.id).sort((a, b) => a.created_at < b.created_at ? 1 : -1)[0]; if (m) c.last_at = m.created_at; });
  T.conversation_members.forEach(m => { if (m.user_id === ME && ids.includes(m.conversation_id)) m.last_read_at = '2026-09-01T00:00:00Z'; });
  return { T, ids };
}
/* the server function, as the SQL has it: newest per_conv of each chat, your hides and clears skipped */
function lastMessagesRpc(T) {
  return body => {
    const hid = new Set((T.message_hides || []).filter(h => !h.user_id || h.user_id === ME).map(h => String(h.message_id)));
    const clr = Object.fromEntries((T.conversation_clears || []).filter(c => c.user_id === ME).map(c => [c.conversation_id, c.cleared_at]));
    const mine = new Set(T.conversation_members.filter(m => m.user_id === ME).map(m => m.conversation_id));
    const n = Math.min(20, Math.max(1, +body.per_conv || 3));
    return [...new Set(body.conv_ids || [])].filter(c => mine.has(c)).flatMap(c => T.messages.filter(m => m.conversation_id === c && !hid.has(String(m.id)) && (!clr[c] || m.created_at > clr[c]))
      .sort((a, b) => a.created_at < b.created_at ? 1 : -1).slice(0, n));
  };
}

if (want('chat')) {
  console.log('chat: a 500-message chat opens on its newest, and pages back');
  const { T, ids } = chatTables();
  const { page, close, log } = await openApp({ tables: T, port, time: null });
  await page.waitForFunction(() => TC.ready, null, { timeout: 30000 });
  await page.evaluate(id => { A.tab('friends'); A.openChat(id); }, ids[0]); await page.waitForTimeout(1200);
  const s1 = await page.evaluate(id => { const sc = document.getElementById('scroll'); return { n: TC.rows[id].length, last: TC.rows[id][TC.rows[id].length - 1].body, first: TC.rows[id][0].body, shown: document.body.innerText.includes('NEWEST-BULK'), atEnd: sc.scrollHeight - sc.scrollTop - sc.clientHeight < 5, chip: !!document.querySelector('[data-a="olderMsgs"]') }; }, ids[0]);
  ok(s1.shown && /NEWEST-BULK/.test(s1.last), 'opens on the newest message', s1);
  ok(s1.n <= 200, 'reads one page (200), not 400', s1.n);
  ok(s1.atEnd, 'scrolled to the bottom on open', s1);
  ok(s1.chip, '"Load earlier messages" is offered', s1);
  /* scroll to the top, tap it: the message that was at the top stays put */
  const anchor = await page.evaluate(() => { const sc = document.getElementById('scroll'); sc.scrollTop = 0; const m = document.querySelector('#scroll .msg[data-mid]'); return { mid: m.dataset.mid, y: m.getBoundingClientRect().top }; });
  if (await page.$('[data-a="olderMsgs"]')) { await page.click('[data-a="olderMsgs"]'); await page.waitForTimeout(900); }
  const s2 = await page.evaluate(([id, a]) => { const m = document.querySelector(`#scroll .msg[data-mid="${a.mid}"]`); return { n: TC.rows[id].length, dup: TC.rows[id].length - new Set(TC.rows[id].map(x => String(x.id))).size, y: m ? m.getBoundingClientRect().top : null, sorted: TC.rows[id].every((x, i, r) => !i || r[i - 1].created_at <= x.created_at), chip: !!document.querySelector('[data-a="olderMsgs"]') }; }, [ids[0], anchor]);
  ok(s2.n > s1.n && s2.n <= 400 && s2.dup === 0 && s2.sorted, 'Load earlier adds the next page above, in order, no duplicates', s2);
  ok(s2.y !== null && Math.abs(s2.y - anchor.y) < 4, 'the message you were looking at stays where it was', { before: anchor.y, after: s2.y });
  if (await page.$('[data-a="olderMsgs"]')) { await page.click('[data-a="olderMsgs"]'); await page.waitForTimeout(900); }
  if (await page.$('[data-a="olderMsgs"]')) { await page.click('[data-a="olderMsgs"]'); await page.waitForTimeout(900); }
  const s3 = await page.evaluate(id => ({ n: TC.rows[id].length, first: TC.rows[id][0].body, chip: !!document.querySelector('[data-a="olderMsgs"]') }), ids[0]);
  const total = T.messages.filter(m => m.conversation_id === ids[0]).length;
  ok(s3.n === total && !s3.chip, 'paging reaches the first message, then the chip goes', { ...s3, total });
  /* realtime: a new message lands at the bottom and the view follows when you're at the bottom */
  await page.evaluate(() => { const sc = document.getElementById('scroll'); sc.scrollTop = sc.scrollHeight; });
  await page.evaluate(([id, who]) => TC.onMessage({ new: { id: 'rt-1', conversation_id: id, sender: who, kind: 'text', body: 'REALTIME HELLO', payload: null, created_at: new Date().toISOString() } }), [ids[0], fid(0)]);
  await page.waitForTimeout(300);
  const s4 = await page.evaluate(id => { const sc = document.getElementById('scroll'); return { last: TC.rows[id][TC.rows[id].length - 1].body, atEnd: sc.scrollHeight - sc.scrollTop - sc.clientHeight < 5, shown: document.body.innerText.includes('REALTIME HELLO') }; }, ids[0]);
  ok(s4.last === 'REALTIME HELLO' && s4.shown && s4.atEnd, 'a realtime message appends at the bottom and is scrolled to', s4);
  await page.fill('#chatin', 'scale hello'); await page.press('#chatin', 'Enter'); await page.waitForTimeout(800);
  const s5 = await page.evaluate(id => ({ last: TC.rows[id][TC.rows[id].length - 1].body, shown: document.body.innerText.includes('scale hello') }), ids[0]);
  ok(s5.last === 'scale hello' && s5.shown, 'a sent message appends at the bottom', s5);
  /* reopen: newest again, including what was just sent */
  await page.evaluate(() => A.tab('friends')); await page.evaluate(id => A.openChat(id), ids[0]); await page.waitForTimeout(1000);
  ok(await page.evaluate(() => document.body.innerText.includes('scale hello')), 'reopening shows the message just sent');
  /* a short chat: no chip */
  await page.evaluate(() => A.tab('friends')); await page.evaluate(id => A.openChat(id), ids[5]); await page.waitForTimeout(800);
  ok(!(await page.$('[data-a="olderMsgs"]')), 'a short chat shows no "Load earlier"');
  ok(log.errors.length === 0, 'chat: no page errors', log.errors);
  await close();
}

if (want('previews')) {
  for (const mode of ['rpc', 'missing', 'empty']) {
    console.log(`previews (${mode === 'rpc' ? 'last_messages() installed' : mode === 'missing' ? 'SQL not run: PGRST202' : 'stand-in answers [] for an unknown function'}): every chat keeps its preview while 3 busy chats fill 300`);
    const { T, ids } = chatTables();
    const rpc = lastMessagesRpc(T);
    const hook = (url, m, body) => {
      if (url.pathname === '/rest/v1/rpc/last_messages') {
        if (mode === 'rpc') return { status: 200, body: JSON.stringify(rpc(body)) };
        if (mode === 'missing') return { status: 404, body: JSON.stringify({ code: 'PGRST202', details: null, hint: null, message: 'Could not find the function public.last_messages(conv_ids, per_conv) in the schema cache' }) };
      }
      return null;
    };
    const { page, close, log } = await openApp({ tables: T, port, hook, time: null });
    await page.waitForFunction(() => TC.ready, null, { timeout: 30000 });
    const thr = await page.evaluate(ids => ids.map(id => { const t = TC.threads.find(x => x.id === id); return t ? (t.last ? 'L' : '-') + (isUnread(t) ? 'U' : '.') : '?'; }).join(' '), ids);
    ok(!/[-?]/.test(thr), 'every chat is listed with a last-message preview', thr);
    ok(!/\./.test(thr), 'every chat whose newest is from the friend is unread', thr);
    const right = await page.evaluate(ids => ids.slice(0, 3).every(id => { const t = TC.threads.find(x => x.id === id); return t && t.last && /NEWEST-BULK/.test(t.last.body); }), ids);
    ok(right, 'the busy chats preview their newest message');
    await page.evaluate(() => A.tab('friends')); await page.waitForTimeout(500);
    const rows = await page.evaluate(() => document.querySelectorAll('#fbody .swrow').length);
    ok(rows >= 13, 'all 13 chats are on the Chats list', rows);
    const per = log.reads.filter(r => /^messages\?/.test(r) && /conversation_id=eq/.test(r)).length;
    const big = log.reads.filter(r => /^messages\?/.test(r) && /conversation_id=in/.test(r)).length;
    const rpcN = () => log.all.filter(r => r.u.startsWith('/rest/v1/rpc/last_messages')).length, rpcs = rpcN();
    const convN = T.conversation_members.filter(m => m.user_id === ME).length;
    if (mode === 'rpc') ok(rpcs === 1 && per === 0 && big === 0, 'with the function: one call, no other message reads', { rpcs, per, big });
    if (mode === 'missing') {
      ok(rpcs === 1 && big === 1 && per >= 10 && per < convN, 'without it: the old read, then one small read for each chat it left out (10 quiet ones + the fixture\'s own)', { rpcs, big, per, convN });
      await page.evaluate(() => loadThreads()); await page.waitForTimeout(300);
      const rpcs2 = rpcN(), per2 = log.reads.filter(r => /^messages\?/.test(r) && /conversation_id=eq/.test(r)).length;
      ok(rpcs2 === 1, 'a missing function is not asked for again for 10 minutes', rpcs2);
      ok(per2 === 2 * per, 'and the fallback still fills every chat on a reload', per2 - per);
    }
    ok(log.errors.length === 0, `previews (${mode}): no page errors`, log.errors);
    await close();
  }
  { console.log('previews: a chat with no messages yet is read once, not on every load');
    const { T, ids } = chatTables();
    T.conversations.push({ id: 'c5555555-5555-4555-8555-0000000000ff', kind: 'direct', title: null, created_by: ME, last_at: '2026-09-28T23:00:00Z' });
    T.conversation_members.push({ conversation_id: 'c5555555-5555-4555-8555-0000000000ff', user_id: ME, last_read_at: '2026-09-28T23:00:00Z' }, { conversation_id: 'c5555555-5555-4555-8555-0000000000ff', user_id: fid(7), last_read_at: null });
    const rpc = lastMessagesRpc(T);
    const { page, close, log } = await openApp({ tables: T, port, time: null, hook: (url, m, body) => url.pathname === '/rest/v1/rpc/last_messages' ? { status: 200, body: JSON.stringify(rpc(body)) } : null });
    await page.waitForFunction(() => TC.ready, null, { timeout: 30000 });
    const n1 = log.reads.filter(r => /^messages\?/.test(r) && /conversation_id=eq\.c5555555-5555-4555-8555-0000000000ff/.test(r)).length;
    await page.evaluate(() => loadThreads()); await page.evaluate(() => loadThreads()); await page.waitForTimeout(300);
    const n2 = log.reads.filter(r => /^messages\?/.test(r) && /conversation_id=eq\.c5555555-5555-4555-8555-0000000000ff/.test(r)).length;
    ok(n1 === 1 && n2 === 1, 'the empty chat is read once', { n1, n2 });
    ok(await page.evaluate(() => TC.threads.some(t => t.id === 'c5555555-5555-4555-8555-0000000000ff')), 'and is still listed');
    await close();
  }
}

if (want('hides')) {
  console.log('hides: 1,500 "Delete for me" rows all count (the read stopped at 1000)');
  const { T, ids } = chatTables();
  const hideIds = T.messages.filter(m => m.conversation_id === ids[0]).slice(-1500).map(m => m.id);   /* chat 0's newest 490 … */
  const more = T.messages.filter(m => m.conversation_id !== ids[0]).slice(0, 1500 - hideIds.length).map(m => m.id);
  T.message_hides = hideIds.concat(more).sort((a, b) => b - a).map(id => ({ message_id: id, user_id: ME, created_at: '2026-09-29T00:00:00Z' }));
  const target = T.messages.filter(m => m.conversation_id === ids[1]).sort((a, b) => a.created_at < b.created_at ? 1 : -1)[0];
  T.message_hides.sort((a, b) => (a.message_id === target.id) - (b.message_id === target.id));   /* the busy chat 1's newest is the very last hide row */
  if (!T.message_hides.some(h => h.message_id === target.id)) T.message_hides.push({ message_id: target.id, user_id: ME, created_at: '2026-09-29T00:00:00Z' });
  const { page, close, log } = await openApp({ tables: T, port, time: null });
  await page.waitForFunction(() => TC.ready, null, { timeout: 30000 });
  const n = await page.evaluate(() => TC.hidden.size);
  ok(n === T.message_hides.length, 'every hidden message is known', { known: n, rows: T.message_hides.length });
  await page.evaluate(id => { A.tab('friends'); A.openChat(id); }, ids[1]); await page.waitForTimeout(1000);
  ok(!(await page.evaluate(b => document.body.innerText.includes(b), target.body)), 'a message hidden long ago stays hidden in the chat', target.body);
  ok(log.errors.length === 0, 'hides: no page errors', log.errors);
  await close();
}

if (want('clock')) {
  console.log('clock: SLO day and minute, kept once a minute, never stale');
  const { page, close } = await openApp({ port, time: '2026-09-29T23:59:20-07:00' });   /* a Tuesday, 20 s before midnight */
  await page.waitForFunction(() => TC.ready, null, { timeout: 30000 });
  const a = await page.evaluate(() => ({ d: CLOCK.day, m: CLOCK.min }));
  await page.clock.runFor(45000);
  const b = await page.evaluate(() => ({ d: CLOCK.day, m: CLOCK.min }));
  ok(a.d === 'T' && a.m === 1439, 'Tuesday 11:59 pm', a);
  ok(b.d === 'W' && b.m === 0, 'turns Wednesday 12:00 am the minute it changes', b);
  const n = await page.evaluate(() => { A.tab('home'); render(true); let n = 0; const orig = Intl.DateTimeFormat; Intl.DateTimeFormat = function (...x) { n++; return new orig(...x); }; Intl.DateTimeFormat.prototype = orig.prototype; Intl.DateTimeFormat.supportedLocalesOf = orig.supportedLocalesOf; for (let i = 0; i < 3; i++) render(true); Intl.DateTimeFormat = orig; return n; });
  ok(n === 0, 'a Home render makes no new date formatters', n);
  await close();
}

if (want('watch')) {
  console.log('watch: turning on a seat alert that is already on updates it (unique key, no primary key)');
  for (const [where, path] of [['app', '/app/'], ['website', '/']]) {
    let refused = 0;
    const T = JSON.parse(JSON.stringify(FX.TABLES)); T.watch_sections = T.watch_sections || [];
    const key = r => [r.user_id, r.class_nbr, r.term].join('|'), have = new Set(T.watch_sections.map(key));
    const hook = (url, m, body) => {   /* as production: (user_id, class_nbr, term) is UNIQUE, not a primary key — a second plain INSERT is 23505 */
      if (url.pathname !== '/rest/v1/watch_sections' || m !== 'POST') return null;
      const rows = Array.isArray(body) ? body : [body];
      if (!url.searchParams.get('on_conflict') && rows.some(r => have.has(key(r)))) { refused++; return { status: 409, body: JSON.stringify({ code: '23505', details: null, hint: null, message: 'duplicate key value violates unique constraint "watch_sections_pkey_term"' }) }; }
      rows.forEach(r => have.add(key(r))); return null;
    };
    const { page, close, log } = await openApp({ tables: T, port, hook, path, width: where === 'app' ? 390 : 1280, time: null, wait: where === 'app' ? 2500 : 4000 });
    if (where === 'app') {
      await page.waitForFunction(() => TC.ready, null, { timeout: 30000 });
      const r = await page.evaluate(async () => { const id = Object.keys(SEC)[0]; return [await TC.watch(id, true), await TC.watch(id, true)]; });
      ok(r[0] && r[1] && refused === 0, 'app: both saves succeed', { r, refused });
    } else {
      await page.waitForFunction(() => typeof sbUser !== 'undefined' && sbUser, null, { timeout: 30000 });
      await page.evaluate(async () => { const s = { class_nbr: '81234', section: '01', name: 'Mockridge, Dov', days: 'TuTh 9:10AM - 11:00AM' }; await pushWatchSecToDb('PHIL 3331', s, true); await pushWatchSecToDb('PHIL 3331', s, true); });
      ok(refused === 0, 'website: both saves succeed', { refused });
    }
    const w = log.writes.filter(x => x.table === 'watch_sections' && x.m === 'POST');
    ok(w.length === 2 && w.every(x => /on_conflict=user_id%2Cclass_nbr%2Cterm|on_conflict=user_id,class_nbr,term/.test(x.query)), `${where}: the upsert names (user_id, class_nbr, term)`, w.map(x => x.query));
    await close();
  }
}

if (want('website')) {
  console.log('website: course_equiv (3,052) and course_prereqs (1,665) load in full');
  const T = JSON.parse(JSON.stringify(FX.TABLES));
  T.course_equiv = []; for (let i = 0; i < 3052; i++) T.course_equiv.push({ legacy_code: `OLD ${1000 + i}`, current_code: `NEW ${1000 + i}` });
  T.course_prereqs = []; for (let i = 0; i < 1665; i++) T.course_prereqs.push({ course_code: `PRQ ${1000 + i}`, prereq_json: { req: [['MATH 1000']] } });
  const { page, close, log } = await openApp({ tables: T, port, path: '/', width: 1280, time: null, wait: 4000 });
  await page.waitForFunction(() => typeof sbUser !== 'undefined' && sbUser, null, { timeout: 30000 }); await page.waitForTimeout(2500);
  const r = await page.evaluate(() => ({ eq: Object.keys(COURSE_EQUIV_SEED).filter(k => /^OLD/.test(k)).length, pr: Object.keys(COURSE_PREREQS_SEED).filter(k => /^PRQ/.test(k)).length, last: COURSE_EQUIV_SEED['OLD 4051'] || null, lastPr: !!COURSE_PREREQS_SEED['PRQ 2664'] }));
  ok(r.eq === 3052 && r.last, 'every crosswalk row is loaded', r);
  ok(r.pr === 1665 && r.lastPr, 'every prerequisite row is loaded', r);
  const reads = log.reads.filter(x => /^course_(equiv|prereqs)\?/.test(x));
  ok(reads.filter(x => /^course_equiv/.test(x)).length === 4 && reads.filter(x => /^course_prereqs/.test(x)).length === 2, 'read 1000 rows at a time (4 + 2 requests)', reads.map(x => x.slice(0, 60)));
  ok(log.errors.length === 0, 'website: no page errors', log.errors);
  await close();
}
console.log(`\n${pass} ok, ${fail} failed`);
process.exit(fail ? 1 : 0);
