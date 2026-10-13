#!/usr/bin/env python3
"""Mutants for friends-of-friend-2026-10-11.py. Usage: python3 friends-of-friend-mutants-2026-10-11.py <repo>"""
import sys, pathlib, json
root = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else '.')
f = root / 'app-dev' / 'tests' / 'mutate.mjs'
s = f.read_text()
if '/* friends-of-friend (2026-10-11) */' in s:
    sys.exit('already patched')
NEW = [
  ["fof: no row on a friend's page", "${isF && !bl ? friendBubbles(p) + fofRow(id) : ''}", "${isF && !bl ? friendBubbles(p) : ''}", "friendsOfFriend"],
  ["fof: asks about someone else", "rpc('friends_of', { p_user: id })", "rpc('friends_of', { p_user: TC.user.id })", "friendsOfFriend"],
  ["fof: asked every time", "if (!force && was && Date.now() - was.at < (was.err ? FOF_ERR_TTL : FOF_TTL)) return;", "", "friendsOfFriend"],
  ["fof: never asked again", "const FOF_TTL = 120000, FOF_ERR_TTL = 15000;", "const FOF_TTL = 1e12, FOF_ERR_TTL = 15000;", "friendsOfFriend"],
  ["fof: a failed re-ask throws the list away", "if (was && was.ids) was.at = Date.now() - FOF_TTL + FOF_ERR_TTL; else TC.fof[id] = { err: 1, at: Date.now() };", "TC.fof[id] = { err: 1, at: Date.now() };", "friendsOfFriend"],
  ["fof: a failed re-ask waits two minutes", "was.at = Date.now() - FOF_TTL + FOF_ERR_TTL;", "was.at = Date.now();", "friendsOfFriend"],
  ["fof: asked on a stranger's page", "if (TC.user && TC.friends.includes(id)) loadFof(id);", "if (TC.user) loadFof(id);", "friendsOfFriend"],
  ["fof: you on your friend's list", "if (!x || !x.id || x.id === me || x.id === id || ids.includes(x.id)) return;", "if (!x || !x.id || x.id === id || ids.includes(x.id)) return;", "friendsOfFriend"],
  ["fof: blocked people listed", "const ok = c.ids.filter(x => !isBlocked(x));", "const ok = c.ids;", "friendsOfFriend"],
  ["fof: strangers named first", "names = L.both.slice(0, 2)", "names = L.all.slice(0, 2)", "friendsOfFriend"],
  ["fof: the count counts the names twice", "more = n - names.length;", "more = n;", "friendsOfFriend"],
  ["fof: one friend is “1 friends”", "${n} friend${n === 1 ? '' : 's'}", "${n} friends", "friendsOfFriend"],
  ["fof: shared friends not A–Z", "const both = ok.filter(x => TC.relation(x) === 'friends').sort(by);", "const both = ok.filter(x => TC.relation(x) === 'friends');", "friendsOfFriend"],
  ["fof: the screen reader hears &#39;", "aria-label=\"${esc(fofLine(L, true) + '. See '", "aria-label=\"${esc(fofLine(L) + '. See '", "friendsOfFriend"],
  ["fof: the row goes nowhere", "<button class=\"fofrow\" data-a=\"openFof\"", "<button class=\"fofrow\"", "friendsOfFriend"],
  ["fof: no Add on the list", "${L.rest.map(fPersonRow).join('')}", "${L.rest.map(x => bothRow(x)).join('')}", "friendsOfFriend"],
  ["fof: shared friends don't open", "const bothRow = x => `<button class=\"li fsr\" data-a=\"openFriend\"", "const bothRow = x => `<button class=\"li fsr\"", "friendsOfFriend"],
  ["fof: not friends any more, still shown", "if (!TC.friends.includes(id) || isBlocked(id)) body = `<div class=\"empty\"><b>Only", "if (false) body = `<div class=\"empty\"><b>Only", "friendsOfFriend"],
  ["fof: a chat's placeholder name kept", "if (!PEOPLE[x.id] || !TC.relation(x.id)) PEOPLE[x.id] =", "if (!PEOPLE[x.id]) PEOPLE[x.id] =", "friendsOfFriend"],
  ["fof: Add doesn't say whom", "aria-label=\"${rel === 'sent' ? `Requested, ${esc(p.name)}. Tap to cancel` : `Add ${esc(p.name)}`}\"", "aria-label=\"Add\"", "friendsOfFriend"],
  ["fof: an empty list shows a row", "const L = fofIds(id); if (!L || !L.all.length) return '';", "const L = fofIds(id); if (!L) return '';", "friendsOfFriendStates"],
  ["fof: a missing function asked forever", "if (r.error && noRpc(r.error)) { TC.fofOff = true; delete TC.fof[id]; }", "if (false) { TC.fofOff = true; delete TC.fof[id]; }", "friendsOfFriendStates"],
  ["fof: a failed read looks like loading", "else body = `<div class=\"empty\"><b>Couldn’t load ${esc(p.short)}’s friends.</b>", "else body = loadingCard('') || `<div class=\"empty\"><b>Couldn’t load ${esc(p.short)}’s friends.</b>", "friendsOfFriendStates"],
  ["fof: Try again does nothing", "fofRetry: () => { const e = cur(); if (e && e.p && e.p.id) { loadFof(e.p.id, true); render(true); } },", "fofRetry: () => {},", "friendsOfFriendStates"],
  ["fof: no loading state", "body = loadingCard(`Loading ${p.short}’s friends…`); }", "body = ''; }", "friendsOfFriendStates"],
  ["fof: no empty message", "body = !L.all.length ? `<div class=\"empty\"><b>${esc(p.short)} isn’t friends with anyone else on TermChamp yet</b></div>`", "body = !L.all.length ? ''", "friendsOfFriendStates"],
  ["fof: one group says Others", "${L.both.length ? 'Others' : 'Their friends'} · ${L.rest.length}", "Others · ${L.rest.length}", "friendsOfFriendStates"],
]
def one(old, new):
    global s
    n = s.count(old)
    assert n == 1, (n, old[:90])
    s = s.replace(old, new)
J = lambda m: json.dumps(m, ensure_ascii=False)
one(J(["no major on a friend's page", "  ${isF && !bl ? friendBubbles(p) : ''}\n  <div class=\"fact\">", "  \n  <div class=\"fact\">", "friendMajor"]),
    J(["no major on a friend's page", "  ${isF && !bl ? friendBubbles(p) + fofRow(id) : ''}\n  <div class=\"fact\">", "  ${isF && !bl ? fofRow(id) : ''}\n  <div class=\"fact\">", "friendMajor"]))
one(J(["requester sees a major", "  ${isF && !bl ? friendBubbles(p) : ''}\n  <div class=\"fact\">", "  ${friendBubbles(p)}\n  <div class=\"fact\">", "friendMajor"]),
    J(["requester sees a major", "  ${isF && !bl ? friendBubbles(p) + fofRow(id) : ''}\n  <div class=\"fact\">", "  ${friendBubbles(p)}${isF && !bl ? fofRow(id) : ''}\n  <div class=\"fact\">", "friendMajor"]))
i = s.index('const M = ['); j = s.index('\n];\n', i)
s = s[:j + 1] + '  /* friends-of-friend (2026-10-11) */\n' + ''.join('  ' + json.dumps(m, ensure_ascii=False) + ',\n' for m in NEW) + s[j + 1:]
f.write_text(s)
print('patched', f)
