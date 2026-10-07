#!/usr/bin/env python3
"""Remove a friend, discreetly (Tate, 2026-10-04: "we need to make a remove friend and it has to be discrete").

- Tucked away: in the ⋯ at the top right of a person's page (18:00's Report / Block menu), a friend gets one
  more row first, "Remove friend · <name> isn't told". Nothing on the Friends list, Home or chats changes.
- One confirm: "Remove Avery?" — "We won't tell Avery. You'll stop seeing each other's classes and plans, and
  Avery leaves your Friends list. Any chat you have stays." Remove (red) / Cancel.
- Quiet on their side: the friendship row is deleted (both directions), the same delete the desktop's
  removeFriend() makes; the database sends no notification for it (no trigger on friend_requests), so the other
  person is never told. They simply stop seeing your classes and plans, which RLS already ties to friendship.
- After removing: back to where you came from, a short "Removed" toast; Home, stories and the Friends list
  update from a fresh friends read. If the delete didn't take (offline, refused), the friend stays and it says so.
- No SQL: the existing "fr_delete_either_side" policy allows it (professify-lockdown.sql).

Applies after add-to-week-2026-10-04.py, on the 18:00 line (block-report-leave-2026-10-04.py), build 2026-10-04 18:15.
Usage: python3 remove-friend-2026-10-04.py <repo-dir>   (edits <repo-dir>/app/index.html)
"""
import sys, os
p = os.path.join(sys.argv[1], 'app', 'index.html')
s = open(p, encoding='utf-8').read()
if 'TC.removeFriend' in s: sys.exit('already patched')
R = [
 # the backend call
 ("const noRpc = e => !!e && (e.code === 'PGRST202'",
  "/* Remove a friend (Tate, 2026-10-04): delete the friendship row in either direction — the desktop's removeFriend()\n"
  "   does the same. Nothing notifies the other person. Success = they are no longer a friend after a fresh read. */\n"
  "TC.removeFriend = async function (id) {\n"
  "  const me = TC.user && TC.user.id;\n"
  "  if (!me || !/^[0-9a-f-]{36}$/i.test(String(id))) { toast('Couldn’t remove — try again'); return false; }\n"
  "  const r = await TC.client().from('friend_requests').delete().in('from_user', [me, id]).in('to_user', [me, id]).select('id');\n"
  "  if (r.error) { toast('Couldn’t remove — check your connection'); return false; }\n"
  "  await loadFriends();\n"
  "  if (TC.err.friends) { TC.friends = TC.friends.filter(x => x !== id); return true; }   /* removed; the refresh after it failed */\n"
  "  if (TC.friends.includes(id)) { toast('Couldn’t remove — try again'); return false; }\n"
  "  return true;\n"
  "};\n"
  "const noRpc = e => !!e && (e.code === 'PGRST202'", 1),
 # an icon for it
 ("const I={\n", "const I={\n unfriend:'<circle cx=\"9\" cy=\"8\" r=\"4\"/><path d=\"M2 21v-1a7 7 0 0 1 14 0v1\"/><path d=\"M16 11h6\"/>',\n", 1),
 # first row of a person's ⋯, friends only
 (" <div class=\"card list mact\"><button class=\"li danger\" data-a=\"reportAsk\" data-x=\"user\" data-y=\"${esc(uid)}\">",
  " <div class=\"card list mact\">${TC.friends.includes(uid) ? `<button class=\"li\" data-a=\"friendRmAsk\" data-x=\"${esc(uid)}\">${ic('unfriend', 20, 2.2)}<span class=\"grow\"><span class=\"b\" style=\"display:block\">Remove friend</span><span class=\"muted b\" style=\"font-size:12.5px\">${f} isn’t told</span></span></button>` : ''}<button class=\"li danger\" data-a=\"reportAsk\" data-x=\"user\" data-y=\"${esc(uid)}\">", 1),
 # the two sheets
 ("SHEETS.sendCard = ({ kind, ref }) => {",
  "/* Remove a friend, discreetly (Tate, 2026-10-04). */\n"
  "SHEETS.friendRm = ({ id }) => {\n"
  "  const p = PEOPLE[id]; if (!p) return '';\n"
  "  const f = esc(p.short);\n"
  "  return `<h3>Remove ${f}?</h3>\n"
  " <div class=\"muted b\" style=\"font-size:14.5px;margin:8px 0 16px;line-height:1.4\">We won’t tell ${f}. You’ll stop seeing each other’s classes and plans, and ${f} leaves your Friends list. Any chat you have stays.</div>\n"
  " <div style=\"display:grid;gap:8px\"><button class=\"btn\" style=\"background:#DC2626\" data-a=\"rmFriend\" data-x=\"${esc(id)}\"${UI.busy.rmFriend ? ' disabled' : ''}>Remove</button><button class=\"btn soft\" data-a=\"closeSheet\">Cancel</button></div>`;\n"
  "};\n"
  "SHEETS.sendCard = ({ kind, ref }) => {", 1),
 # actions
 ("  chatDelAsk: cid => { UI.sheet = { type: 'chatDel', cid }; render(true); },\n",
  "  chatDelAsk: cid => { UI.sheet = { type: 'chatDel', cid }; render(true); },\n"
  "  friendRmAsk: id => { UI.sheet = { type: 'friendRm', id }; render(true); },\n"
  "  rmFriend: async id => {\n"
  "    if (UI.busy.rmFriend) return; UI.busy.rmFriend = 1; render(true);\n"
  "    let ok = false; try { ok = await TC.removeFriend(id); } catch (e) { toast('Couldn’t remove — try again'); } finally { UI.busy.rmFriend = 0; }\n"
  "    if (!ok) { render(true); return; }\n"
  "    UI.sheet = null;\n"
  "    if (cur().s === 'friend' && cur().p && cur().p.id === id) back(); else render(true);\n"
  "    toast('Removed');\n"
  "  },\n", 1),
]
for a, b, n in R:
    if s.count(a) != n: sys.exit(f'anchor matched {s.count(a)}x (want {n}): {a[:90]}')
    s = s.replace(a, b)
open(p, 'w', encoding='utf-8').write(s)
print('patched', p)
