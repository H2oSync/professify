#!/usr/bin/env python3
"""Scale (2026-10-30): the chat list read every chat's preview with ONE query — the newest 300 messages
across all chats. Two or three busy chats filled it, so quieter chats got no last message: no preview,
no unread dot, and a direct chat with no preview could vanish from the list.
Now: the server function last_messages(conv_ids, per_conv) (sql 2026-10-30-last-messages.sql) returns
the newest 3 of EACH chat. Until that SQL has run (PGRST202/404, re-tried after 10 minutes), or when it
returns nothing at all, the app reads as before, and then, for any chat still without a preview, its own newest 5 (6 chats at a time). A chat
that has no message to show is remembered by its last_at, so it is not read again until it changes.
Usage: python3 scale-thread-previews-2026-10-30.py app/index.html"""
import sys
p = sys.argv[1]; s = open(p, encoding='utf-8').read()
def one(old, new):
    global s
    assert s.count(old) == 1, (s.count(old), old[:90]); s = s.replace(old, new)

one("""/* ---- Messages. -------------------------------------------------------------------------------- */
async function loadThreads() {""",
"""/* ---- Messages. -------------------------------------------------------------------------------- */
const MSG_COLS = 'id,conversation_id,sender,kind,body,payload,created_at';
/* The newest few messages of each chat, for the list's previews and unread dots (scale, 2026-10-30).
   last_messages() gives every chat its own 3; without it (the SQL not run yet), the old one-query read. */
async function lastMsgs(sb, ids) {
  if (!TC.noLastRpc || Date.now() - TC.noLastRpc > 600000) {
    const out = []; let bad = null;
    for (let i = 0; i < ids.length && !bad; i += 300) {
      const r = await sb.rpc('last_messages', { conv_ids: ids.slice(i, i + 300), per_conv: 3 });
      if (r.error || !Array.isArray(r.data)) bad = r.error || { message: 'no rows' }; else out.push(...r.data);
    }
    if (!bad && (out.length || !ids.length)) { delete TC.noLastRpc; return out; }   /* nothing at all for a list of chats: read the old way too */
    if (bad && (syncGap(bad) || String(bad.code) === '404' || /not found/i.test(String(bad.message || '')))) TC.noLastRpc = Date.now();
  }
  const r = await sb.from('messages').select(MSG_COLS).in('conversation_id', ids).order('created_at', { ascending: false }).limit(300);
  return (r && r.data) || [];
}
/* A chat still without a preview gets its own small read; one with nothing to show is skipped until its last_at moves. */
async function fillLast(sb, convs, lastOf, take) {
  const E = TC.lastEmpty = TC.lastEmpty || {};
  const need = convs.filter(c => !lastOf[c.id] && E[c.id] !== c.last_at && !(TC.clears[c.id] && new Date(c.last_at) <= new Date(TC.clears[c.id])));
  for (let i = 0; i < need.length; i += 6) await Promise.all(need.slice(i, i + 6).map(async c => {
    const r = await sb.from('messages').select(MSG_COLS).eq('conversation_id', c.id).order('created_at', { ascending: false }).limit(5);
    if (r.error) return;
    take(r.data || []); if (!lastOf[c.id]) E[c.id] = c.last_at; else delete E[c.id];
  }));
}
async function loadThreads() {""")
one("""    sb.from('messages').select('id,conversation_id,sender,kind,body,payload,created_at').in('conversation_id', ids).order('created_at', { ascending: false }).limit(300),
    sb.from('conversation_clears').select('conversation_id,cleared_at'),""",
"""    lastMsgs(sb, ids),
    sb.from('conversation_clears').select('conversation_id,cleared_at'),""")
one("""  const lastOf = {}, spoke = {};
  ((last && last.data) || []).forEach(m => { if (!lastOf[m.conversation_id] && msgVisible(m)) lastOf[m.conversation_id] = m; if (m.sender !== me) (spoke[m.conversation_id] = spoke[m.conversation_id] || {})[m.sender] = 1; });""",
"""  const lastOf = {}, spoke = {};
  const take = rows => rows.slice().sort((a, b) => new Date(b.created_at) - new Date(a.created_at)).forEach(m => { if (!lastOf[m.conversation_id] && msgVisible(m)) lastOf[m.conversation_id] = m; if (m.sender !== me) (spoke[m.conversation_id] = spoke[m.conversation_id] || {})[m.sender] = 1; });
  take(last || []);
  await fillLast(sb, convs.data || [], lastOf, take);""")
open(p, 'w', encoding='utf-8').write(s); print(p, 'chat list: a preview for every chat')
