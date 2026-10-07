#!/usr/bin/env python3
r"""Group chats: two-photo avatars and "+ New group" (Tate, 2026-10-03).

  "for groups have it both profile pictures just smaller"; then, on the Group Chat Options canvas,
  option 4 ("+ New group" on the Chats label): "do this make it the same color as invite".

  · A group's picture is two of its people, smaller and overlapping (Instagram's look): the most
    recent sender in front with a white ring, another member behind. A group of you and one other
    shows them and you. Used in the chat list, the chat header and Send to a friend. No more
    coloured initials square.
  · "+ New group" sits at the right end of the CHATS label as a small pink pill — the Invite pill's
    pink and white (pink text on the page's grey is only 3.95:1; white on pink is 4.6:1). Its tap
    area is 44px. It shows once you have 2 or more friends; with no chats yet the label shows alone.
  · New group (a sheet): an optional name, the friends you've picked as chips (tap to remove), a
    search over your friends, and the list with tick circles. Create needs 2 or more friends and says
    how many people the group will have. Only accepted friends are offered — the database's own rule
    ("the creator adds friends", professify-messaging.sql / professify-safety.sql) — so nothing new
    is needed in SQL. A name with a blocked word is stopped before anything is sent.
  · Create writes the conversation (kind group, the name or null) and every member in one insert;
    a refusal says so and keeps the sheet. Success opens the new chat. Groups already show in Chats
    even before a first message.

Usage: python3 groups-2026-10-03.py <repo-dir>. Every anchor must match exactly once.
"""
import sys, os
p = os.path.join(sys.argv[1], 'app', 'index.html')
s = open(p, encoding='utf-8').read()

def rep(a, b):
    global s
    n = s.count(a)
    if n != 1: sys.exit(f'anchor matched {n}x: {a[:90]}')
    s = s.replace(a, b)

# 1. CSS.
rep(".fs-h{font-size:13px;font-weight:900;letter-spacing:.04em;text-transform:uppercase;color:var(--ink3);padding:16px 20px 8px}",
    ".fs-h{font-size:13px;font-weight:900;letter-spacing:.04em;text-transform:uppercase;color:var(--ink3);padding:16px 20px 8px}\n"
    "/* Groups (2026-10-03): two smaller photos, the newest sender in front with a white ring. */\n"
    ".gav{position:relative;display:inline-block;flex:none}\n"
    ".gav>span{position:absolute;display:grid;border-radius:50%}\n"
    ".gav .gav-b{right:0;top:0}.gav .gav-f{left:0;bottom:0;box-shadow:0 0 0 2.5px #fff}\n"
    ".gav .av{box-shadow:none;margin:0}\n"
    ".fs-hrow{display:flex;align-items:center;justify-content:space-between;padding-right:16px}\n"
    ".ngbtn{position:relative;display:inline-flex;align-items:center;gap:4px;min-height:32px;padding:0 12px 0 10px;border-radius:999px;background:var(--pink);color:#fff;font-weight:900;font-size:13.5px;letter-spacing:0;text-transform:none;box-shadow:0 3px 10px rgba(219,39,119,.22)}\n"
    ".ngbtn::after{content:'';position:absolute;inset:-6px -4px}\n"
    ".ng-chips{display:flex;flex-wrap:wrap;gap:8px;margin:10px 0 2px}\n"
    ".ng-chip{display:inline-flex;align-items:center;gap:6px;min-height:44px;padding:0 12px;border-radius:999px;background:var(--pink-soft);color:var(--pink-ink);font-weight:900;font-size:14.5px}\n"
    ".ng-row{display:flex;align-items:center;gap:14px;width:100%;min-height:60px;text-align:left;border-top:1px solid var(--line)}\n"
    ".ng-box{width:26px;height:26px;border-radius:50%;box-sizing:border-box;border:2px solid #64748B;display:grid;place-items:center;flex:none}\n"
    ".ng-row[aria-pressed=true] .ng-box{background:var(--pink);border-color:var(--pink)}\n"
    ".ng-name{display:flex;align-items:center;gap:12px;height:52px;padding:0 14px;border-radius:16px;background:var(--bg)}\n"
    ".ng-name input{flex:1;min-width:0;border:0;outline:0;background:none;font:800 16px Nunito,system-ui,sans-serif;color:var(--ink)}\n")

# 2. The two-photo avatar.
rep("function threadRow(t) {",
    "/* A group's picture: two of its people, smaller (Tate, 2026-10-03). Front = the newest sender who\n"
    "   isn't you; behind = another member, or you when it's just the two of you. */\n"
    "function groupAv(t, size) {\n"
    "  const me = TC.user.id, others = (t.members || []).filter(u => u && u !== me);\n"
    "  if (!others.length) return noPhotoAv(size);\n"
    "  const recent = [t.last && t.last.sender].concat(t.senders || []).filter(u => u && u !== me && others.includes(u));\n"
    "  const pick = [...new Set(recent.concat(others))].slice(0, 2);\n"
    "  if (pick.length < 2) pick.push('me');\n"
    "  pick.forEach(u => { if (u !== 'me' && !PEOPLE[u]) PEOPLE[u] = personFrom({ id: u, display_name: nameOf(u), avatar_url: (TC.names[u] || {}).avatar }); });\n"
    "  const s = Math.round(size * 0.68);\n"
    "  return `<span class=\"gav\" style=\"width:${size}px;height:${size}px\" aria-hidden=\"true\"><span class=\"gav-b\">${pav(pick[1], s)}</span><span class=\"gav-f\">${pav(pick[0], s)}</span></span>`;\n"
    "}\n"
    "function threadRow(t) {")
rep("  else { const nm = threadName(t); avh = `<span class=\"ringav\"><span class=\"sq\" style=\"width:48px;height:48px;background:${t.kind === 'class' ? '#D6E4FF' : colorFor(t.id)};",
    "  else if (t.kind === 'group') avh = `<span class=\"ringav\">${groupAv(t, 48)}</span>`;\n"
    "  else { const nm = threadName(t); avh = `<span class=\"ringav\"><span class=\"sq\" style=\"width:48px;height:48px;background:${t.kind === 'class' ? '#D6E4FF' : colorFor(t.id)};")
rep("  else head = `<span class=\"sq\" style=\"width:40px;height:40px;background:${t.kind === 'class' ? '#D6E4FF' : colorFor(t.id)};font-size:13px;color:var(--blue-ink)\">${esc(initialsOf(threadName(t)))}</span>",
    "  else head = `${t.kind === 'group' ? groupAv(t, 40) : `<span class=\"sq\" style=\"width:40px;height:40px;background:${t.kind === 'class' ? '#D6E4FF' : colorFor(t.id)};font-size:13px;color:var(--blue-ink)\">${esc(initialsOf(threadName(t)))}</span>`}")
rep("av: `<span class=\"sq\" style=\"width:42px;height:42px;background:${colorFor(t.id)};color:var(--ink2);font-size:14px\">${esc(initialsOf(threadName(t)))}</span>` }));",
    "av: groupAv(t, 42) }));")

# 3. "+ New group" on the Chats label.
rep("  if (!chats && !fr) return `<div class=\"empty\"><b>No friends yet</b>Search above to find classmates, or tap Invite.</div>`;\n  return `${chats ? `<div class=\"fs-h\">Chats</div>${chats}` : ''}${fr}`;",
    "  if (!chats && !fr) return `<div class=\"empty\"><b>No friends yet</b>Search above to find classmates, or tap Invite.</div>`;\n"
    "  const canGroup = TC.friends.filter(id => PEOPLE[id]).length >= 2;\n"
    "  const chatsHead = `<div class=\"fs-h fs-hrow\"><span>Chats</span>${canGroup ? `<button class=\"ngbtn\" data-a=\"newGroup\">${ic('plus', 14, 3)}New group</button>` : ''}</div>`;\n"
    "  return `${chats || canGroup ? chatsHead + chats : ''}${fr}`;")

# 4. The New group sheet.
rep("SHEETS.invite = () => {",
    "/* New group (2026-10-03): friends only — the database's own rule — 2 or more of them. */\n"
    "function ngFriends() { return TC.friends.filter(id => PEOPLE[id]).sort((a, b) => PEOPLE[a].name.localeCompare(PEOPLE[b].name)); }\n"
    "function ngList() {\n"
    "  const g = UI.ng || {}, q = String(g.q || '').trim().toLowerCase().replace(/^@/, '');\n"
    "  const ids = ngFriends().filter(id => !q || PEOPLE[id].name.toLowerCase().includes(q) || (PEOPLE[id].handle || '').toLowerCase().includes(q));\n"
    "  if (!ids.length) return `<div class=\"muted b\" style=\"padding:14px 2px\">No friend matching “${esc(g.q)}”.</div>`;\n"
    "  return ids.map(id => { const on = (g.picked || []).includes(id), p = PEOPLE[id];\n"
    "    return `<button class=\"ng-row\" data-a=\"ngPick\" data-x=\"${esc(id)}\" aria-pressed=\"${on}\">${pav(id, 42, 14)}<span class=\"grow\"><span class=\"b\" style=\"display:block;font-size:16px\">${esc(p.name)}</span>${p.handle ? `<span class=\"muted b\" style=\"display:block;font-size:13px\">@${esc(p.handle)}</span>` : ''}</span><span class=\"ng-box\">${on ? ic('check', 15, 3.4) : ''}</span></button>`; }).join('');\n"
    "}\n"
    "SHEETS.newGroup = () => {\n"
    "  const g = UI.ng || (UI.ng = { title: '', q: '', picked: [] }), n = g.picked.length, busy = !!UI.busy.ng;\n"
    "  return `<div class=\"row sb\"><h3>New group</h3><button class=\"xbtn\" data-a=\"closeSheet\" aria-label=\"Close\">${ic('x', 16, 2.4)}</button></div>\n"
    " <div class=\"muted b\" style=\"font-size:14px;margin:4px 0 12px\">Pick 2 or more of your friends. Only friends can be added.</div>\n"
    " <label class=\"ng-name\"><input id=\"ngTitle\" aria-label=\"Group name (optional)\" data-in=\"ngTitle\" maxlength=\"60\" placeholder=\"Group name (optional)\" value=\"${esc(g.title)}\" autocomplete=\"off\"></label>\n"
    " ${n ? `<div class=\"ng-chips\">${g.picked.map(id => `<button class=\"ng-chip\" data-a=\"ngPick\" data-x=\"${esc(id)}\" aria-label=\"Remove ${esc(PEOPLE[id] ? PEOPLE[id].name : 'friend')}\">${esc(PEOPLE[id] ? PEOPLE[id].short : '?')}${ic('x', 12, 3.2)}</button>`).join('')}</div>` : ''}\n"
    " <label class=\"search\" style=\"margin:12px 0 4px\"><span style=\"color:var(--pink)\">${ic('search', 20, 2.4)}</span><input id=\"ngq\" data-in=\"ngq\" type=\"search\" value=\"${esc(g.q)}\" placeholder=\"Search your friends\" aria-label=\"Search your friends\" autocomplete=\"off\" autocapitalize=\"off\" spellcheck=\"false\"></label>\n"
    " <div id=\"ngList\">${ngList()}</div>\n"
    " ${g.err ? `<div class=\"tc-err\" role=\"alert\" style=\"margin-top:10px\">${esc(g.err)}</div>` : ''}\n"
    " <button class=\"btn invshare\" style=\"margin-top:14px\" data-a=\"ngCreate\" ${n >= 2 && !busy ? '' : 'disabled'}>${busy ? 'Creating…' : n >= 2 ? `Create group · ${n + 1} people` : `Pick ${2 - n} more friend${2 - n === 1 ? '' : 's'}`}</button>`;\n"
    "};\n"
    "/* A refused member insert leaves an empty conversation only its creator can see; a retry reuses it\n"
    "   (cid) rather than making another. Members go in one insert, so it's everyone or no one. */\n"
    "TC.createGroup = async function (uids, title, cid) {\n"
    "  const sb = TC.client(); await TC.freshSession();\n"
    "  if (!cid) {\n"
    "    const c = await sb.from('conversations').insert({ kind: 'group', title: title || null, created_by: TC.user.id }).select().single();\n"
    "    if (c.error || !c.data) return { err: dbSay(c.error || NOTHING, 'Couldn’t make the group.') };\n"
    "    cid = c.data.id;\n"
    "  } else if (title !== undefined) await sb.from('conversations').update({ title: title || null }).eq('id', cid);\n"
    "  const m = await sb.from('conversation_members').insert([TC.user.id].concat(uids).map(u => ({ conversation_id: cid, user_id: u })));\n"
    "  if (m.error) return { cid, err: dbSay(m.error, 'Couldn’t add everyone, so the group wasn’t made. Someone may no longer be your friend.') };\n"
    "  await loadThreads();\n"
    "  if (!TC.threads.some(t => t.id === cid)) TC.threads.unshift({ id: cid, kind: 'group', title: title || null, last_at: new Date().toISOString(), members: [TC.user.id].concat(uids), senders: [], last: null });\n"
    "  return { id: cid };\n"
    "};\n"
    "SHEETS.invite = () => {")

# 5. Actions and typing.
rep("  openChat: id => {",
    "  newGroup: () => { UI.ng = { title: '', q: '', picked: [] }; UI.champ = false; UI.sheet = { type: 'newGroup' }; render(true); },\n"
    "  ngPick: id => { const g = UI.ng; if (!g || !TC.friends.includes(id)) return; g.picked = g.picked.includes(id) ? g.picked.filter(x => x !== id) : g.picked.concat(id); g.err = ''; render(true); },\n"
    "  ngCreate: async () => {\n"
    "    const g = UI.ng; if (!g || UI.busy.ng) return;\n"
    "    const ids = g.picked.filter(id => TC.friends.includes(id)), title = String(g.title || '').trim().slice(0, 60);\n"
    "    if (ids.length < 2) return;\n"
    "    const bad = title && wfHit(title); if (bad) { g.err = 'Group names are seen by everyone in it, so “' + bad + '” can’t be in one.'; return render(true); }\n"
    "    UI.busy.ng = 1; g.err = ''; render(true);\n"
    "    const r = await TC.createGroup(ids, title, g.cid);\n"
    "    UI.busy.ng = 0;\n"
    "    if (r.err) { g.cid = r.cid; g.err = r.err; return render(true); }\n"
    "    /* Still on the sheet: open the group. Gone elsewhere meanwhile: don't pull them away. */\n"
    "    if (UI.ng === g && UI.sheet && UI.sheet.type === 'newGroup') { UI.ng = null; UI.sheet = null; A.openChat(r.id); }\n"
    "    else { UI.ng = UI.ng === g ? null : UI.ng; toast('Group made — it’s in Chats'); render(true); }\n"
    "  },\n"
    "  openChat: id => {")
rep("  else if (k === 'review') {",
    "  else if (k === 'ngTitle') { if (UI.ng) UI.ng.title = ev.target.value; }\n"
    "  else if (k === 'ngq') { if (UI.ng) { UI.ng.q = ev.target.value; const el = document.getElementById('ngList'); if (el) el.innerHTML = ngList(); } }\n"
    "  else if (k === 'review') {")

open(p, 'w', encoding='utf-8').write(s)
print('patched', p)
