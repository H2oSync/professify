#!/usr/bin/env python3
"""Friends is one list, and a chat opens on its newest message (Tate, 2026-10-03).

Tate, on the Friends tab: "take out class chat i also want to make sure i can easily see request.
combine so chats and friends are in the same thing so chats are just the friends youve chatted and
then friends are below all those chats. also lets move the massive invite friends to maybe top right
or something, i dont like that its below the search." Then, on an open chat: "when i click on a chat
it shouldnt take me to the top of the page it should take to the most recent message".

Friends tab
- No filter chips (Chats / Friends / Groups / Class chats / Requests are gone).
- Friend requests come first, in their own card with a red count, Accept and ✕ right there.
- Then **Chats**: every conversation you are in, newest first (1:1s and group chats). A 1:1 that never
  had a message is not a chat.
- Then **Friends**: the friends you haven't chatted with, A–Z. Nobody appears twice.
- People you might know stays at the bottom.
- Invite is a small pink "Invite" button at the top right, beside the title (it was a full-width
  button under the search). It opens the same Invite sheet (link + QR).
- The search is unchanged.

Chats
- A chat opens on its newest message. Before, it opened at the end of the "Loading messages…" page,
  and when the messages arrived the page kept that place — the top of the conversation.
- While you are at the bottom, a new message keeps you there. If you have scrolled up to read, nothing
  moves under you.

Applies after sec-sheet-links-2026-10-03.py (build 2026-10-03 05:00).
Usage: python3 friends-one-list-2026-10-03.py <repo-dir>   (edits <repo-dir>/app/index.html)
"""
import sys, os
p = os.path.join(sys.argv[1], 'app', 'index.html')
s = open(p, encoding='utf-8').read()
if 'function fRequests' in s: sys.exit('already patched')

NEW_LIST = r"""/* Friends (Tate, 2026-10-03): ONE list. Requests first; then your chats, newest first (1:1s and group
   chats); then the friends you haven't chatted with, A–Z. No filter chips; nobody twice. */
function fFriendRow(id) {
  const st = status(id);
  return `<button class="li" data-a="openFriend" data-x="${id}">${pav(id, 46, 16)}<div class="grow"><div style="font-weight:900;font-size:16px">${esc(PEOPLE[id].name)}</div><div class="b" style="font-size:13px;color:${st.c || 'var(--muted)'}">${st.free === null ? esc(st.t) : '● ' + esc(st.t)}</div></div><span class="chev">${ic('chevR', 18)}</span></button>`;
}
function fRequests() {
  const rq = TC.requests.filter(id => PEOPLE[id]);
  if (!rq.length) return '';
  return `<div class="fs-h freq-h">Friend requests<span class="n">${rq.length}</span></div><div class="card list freq" style="margin:0 16px">${rq.map(id => `<div class="li">${pav(id, 46, 16)}<div class="grow"><div style="font-weight:900;font-size:16px">${esc(PEOPLE[id].name)}</div><div class="muted b" style="font-size:13.5px">${PEOPLE[id].handle ? '@' + esc(PEOPLE[id].handle) : 'Wants to be friends'}</div></div><button class="pbtn pink" data-a="acceptReq" data-x="${id}">Accept</button><button class="xbtn" data-a="declineReq" data-x="${id}" aria-label="Decline">${ic('x', 16, 2.4)}</button></div>`).join('')}</div>`;
}
function friendsList() {
  const ts = TC.threads.filter(t => t.last || t.kind !== 'direct');      // a 1:1 that never had a message isn't a chat
  const chatted = new Set(ts.filter(t => t.kind === 'direct').map(threadOther).filter(Boolean));
  const rest = TC.friends.filter(id => PEOPLE[id] && !chatted.has(id)).sort((a, b) => PEOPLE[a].name.localeCompare(PEOPLE[b].name));
  let chats = '';
  if (TC.err.threads && !TC.threads.length) chats = errCard('Couldn’t load your chats.', 'refresh');
  else if (!TC.ready && !ts.length) chats = loadingCard('Loading chats…');
  else if (ts.length) chats = `<div class="card" style="margin:0 16px;padding:2px 0">${ts.map(threadRow).join('')}</div>`;
  const fr = rest.length ? `<div class="fs-h">Friends</div><div class="card list" style="margin:0 16px">${rest.map(fFriendRow).join('')}</div>` : '';
  if (!chats && !fr) return `<div class="empty"><b>No friends yet</b>Search above to find classmates, or tap Invite.</div>`;
  return `${chats ? `<div class="fs-h">Chats</div>${chats}` : ''}${fr}`;
}
"""

a = s.index('function friendsList() {\n')
b = s.index('/* Friends (Tate, 2026-09-30): ONE search for everyone')
if s.count('function friendsList() {\n') != 1 or b < a: sys.exit('friendsList anchor')
s = s[:a] + NEW_LIST + s[b:]

R = [
 # no chips; requests first; suggestions always at the bottom
 ("  const F = S.friendsFilter, sug = TC.suggestions.filter(id => TC.relation(id) !== 'friends');\n",
  "  const sug = TC.suggestions.filter(id => TC.relation(id) !== 'friends');\n"),
 (" <div class=\"chips\">${[['all', 'Chats'], ['people', 'Friends'], ['groups', 'Groups'], ['class', 'Class chats'], ['requests', 'Requests']].map(([k, l]) => `<button class=\"chip ${F === k ? 'on' : ''}\" data-a=\"fFilter\" data-x=\"${k}\">${l}${k === 'requests' && TC.requests.length ? `<span class=\"n\">${TC.requests.length}</span>` : k === 'people' && TC.friends.length ? `<span class=\"n\" style=\"background:var(--muted2)\">${TC.friends.length}</span>` : ''}</button>`).join('')}</div>\n",
  " ${fRequests()}\n"),
 (" ${F === 'all' && sug.length ? `<div class=\"sec-h\" style=\"padding-left:20px\"><span>People you might know</span>",
  " ${sug.length ? `<div class=\"sec-h\" style=\"padding-left:20px\"><span>People you might know</span>"),
 # Invite: a small button at the top right, not a full-width one under the search
 ("  body: `<div class=\"fhdr\"><div class=\"title\">Friends</div></div>\n",
  "  body: `<div class=\"fhdr\"><div class=\"title\">Friends</div><button class=\"invpill\" data-a=\"sheet\" data-x=\"invite\" aria-label=\"Invite friends\">${ic('qr', 18, 2.4)}Invite</button></div>\n"),
 (" <button class=\"btn invbtn\" data-a=\"sheet\" data-x=\"invite\">${ic('qr', 22, 2.2)}Invite friends</button>\n", ""),
 (".invbtn{display:flex;align-items:center;justify-content:center;gap:10px;margin:12px 16px 4px;width:calc(100% - 32px);background:var(--pink);box-shadow:0 8px 18px rgba(219,39,119,.28)}\n",
  ".invpill{display:inline-flex;align-items:center;gap:6px;min-height:44px;padding:0 16px;border-radius:999px;background:var(--pink);color:#fff;font-weight:900;font-size:15px;box-shadow:0 4px 12px rgba(219,39,119,.25);flex:none}\n"
  ".fhdr+.fsearch{margin-top:2px}\n"
  ".freq-h{display:flex;align-items:center;gap:8px;color:var(--ink)}\n"
  ".freq-h .n{display:inline-grid;place-items:center;min-width:22px;height:22px;padding:0 6px;border-radius:11px;background:#DC2626;color:#fff;font-size:12.5px;letter-spacing:0}\n"
  ".freq{box-shadow:0 0 0 2px #FBCFE8}\n"),
 # a chat opens on its newest message, and stays there while you are at the bottom
 ("  const y = sc.scrollTop, champY = (document.getElementById('champscroll') || {}).scrollTop;\n",
  "  const y = sc.scrollTop, champY = (document.getElementById('champscroll') || {}).scrollTop, atEnd = sc.scrollHeight - y - sc.clientHeight < 120;\n"),
 ("  if (v.scrollEnd && !keep) scrollEnd();\n",
  "  if (v.scrollEnd && (!keep || atEnd)) scrollEnd();   /* opened, or already at the newest message: show the newest */\n"),
]
for x, y in R:
    if s.count(x) != 1: sys.exit(f'anchor matched {s.count(x)}x: {x[:80]}')
    s = s.replace(x, y)
open(p, 'w', encoding='utf-8').write(s)
print('patched', p)
