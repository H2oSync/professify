#!/usr/bin/env python3
"""Scale (2026-10-30): a chat with more than 400 messages opened on its OLDEST 400 — openThread read
ascending with limit 400, so the newest messages (and anything just sent) were never shown. Now it
reads the newest 200 (descending), shows them oldest-first, and a "Load earlier messages" chip at the
top pages back 200 at a time. The older page is read by time (created_at <= the oldest shown, ids
already on screen dropped), not by offset, so messages arriving meanwhile never shift the page.
The scroll position is kept when older messages are put above; opening still lands on the newest;
realtime and sent messages still append. Likes are read for each older page too.
Usage: python3 scale-chat-newest-2026-10-30.py app/index.html"""
import sys
p = sys.argv[1]; s = open(p, encoding='utf-8').read()
def one(old, new):
    global s
    assert s.count(old) == 1, (s.count(old), old[:90]); s = s.replace(old, new)

# 1. newest first, a page of 200; anything that came in by realtime while the read was out is kept
one("""TC.openThread = async function (cid) {
  const r = await TC.client().from('messages').select('*').eq('conversation_id', cid).order('created_at', { ascending: true }).limit(400);""",
"""const CHAT_PAGE = 200;
TC.rowsMore = {};
TC.openThread = async function (cid) {
  const r = await TC.client().from('messages').select('*').eq('conversation_id', cid).order('created_at', { ascending: false }).order('id', { ascending: false }).limit(CHAT_PAGE);""")
one("""  delete TC.rowsErr[cid];
  TC.rows[cid] = r.data || [];
  loadLikes(cid);""",
"""  delete TC.rowsErr[cid];
  { const got = (r.data || []).slice().reverse(), ids = new Set(got.map(x => String(x.id))), top = got.length ? Date.parse(got[got.length - 1].created_at) : -Infinity;
    const late = (TC.rows[cid] || []).filter(x => !ids.has(String(x.id)) && Date.parse(x.created_at) > top);   /* a realtime echo or a send that beat this read */
    TC.rows[cid] = got.concat(late); TC.rowsMore[cid] = (r.data || []).length >= CHAT_PAGE; }
  loadLikes(cid);""")
# 2. the next page back
one("""TC.send = async function (cid, body, kind, payload) {""",
"""TC.olderMessages = async function (cid) {
  const rows = TC.rows[cid]; if (!rows || !rows.length) return false;
  const sb = TC.client();
  const r = await sb.from('messages').select('*').eq('conversation_id', cid).lte('created_at', rows[0].created_at).order('created_at', { ascending: false }).order('id', { ascending: false }).limit(CHAT_PAGE);
  if (r.error) { toast('Couldn’t load earlier messages'); return false; }
  const have = new Set(rows.map(x => String(x.id))), add = (r.data || []).filter(x => !have.has(String(x.id))).reverse();
  TC.rows[cid] = add.concat(TC.rows[cid] || []);
  TC.rowsMore[cid] = (r.data || []).length >= CHAT_PAGE && add.length > 0;
  if (add.length && TC.chatX.on !== false) {   /* their likes, merged into what's known */
    for (let i = 0; i < add.length; i += 100) {
      const l = await sb.from('message_likes').select('message_id,user_id').in('message_id', add.slice(i, i + 100).map(m => m.id));
      if (l.error) break;
      const L = TC.likes[cid] = TC.likes[cid] || {}; (l.data || []).forEach(x => { const k = String(x.message_id); if (UI.busy['lk' + k]) return; (L[k] = L[k] || []).includes(x.user_id) || L[k].push(x.user_id); });
    }
  }
  return add.length > 0;
};
TC.send = async function (cid, body, kind, payload) {""")
# 3. the chip, above the oldest message shown
one("""    body: `<div class="msgs">${rows ? blockedNote(rows) +""",
"""    body: `<div class="msgs">${rows && TC.rowsMore && TC.rowsMore[id] ? `<button class="chip olderbtn" data-a="olderMsgs" data-x="${esc(String(id))}"${UI.busy.older ? ' disabled' : ''}>${UI.busy.older ? 'Loading…' : 'Load earlier messages'}</button>` : ''}${rows ? blockedNote(rows) +""")
one(""".msgs{padding:14px 14px 20px;display:flex;flex-direction:column;gap:6px}
""", """.msgs{padding:14px 14px 20px;display:flex;flex-direction:column;gap:6px}
.msgs .olderbtn{align-self:center;margin:0 0 8px;font-size:13.5px}
""")
# 4. the action: keeps the message you were looking at where it was
one("""  retryChat: () => { const e = cur(); if (e.p && e.p.id) TC.openThread(e.p.id); },""",
"""  retryChat: () => { const e = cur(); if (e.p && e.p.id) TC.openThread(e.p.id); },
  olderMsgs: async id => {
    if (UI.busy.older) return; UI.busy.older = 1; render(true);
    let ok = false; try { ok = await TC.olderMessages(id); } finally { UI.busy.older = 0; }
    const sc = document.getElementById('scroll'), e = cur(), here = e && e.s === 'chat' && e.p && String(e.p.id) === String(id);
    const h0 = sc ? sc.scrollHeight : 0, y0 = sc ? sc.scrollTop : 0;
    render(true);
    if (ok && here && sc) sc.scrollTop = y0 + (sc.scrollHeight - h0);
  },""")
open(p, 'w', encoding='utf-8').write(s); print(p, 'chat: newest 200 + Load earlier messages')
