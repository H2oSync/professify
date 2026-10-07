#!/usr/bin/env python3
r"""Friends: one search for everyone, an Invite friends button with a QR code, and a red request count
on the tab. (Tate, 2026-09-30.)

  "On the Friends tab, put a full-width search bar at the very top: 'Find friends by name or
   @username'. Under it, one clear 'Invite friends' button that opens the link and QR code. Show a
   red count on the Friends tab when you have requests waiting. (should we make it like instagram
   where the same search is for anyone — people who are your current friends and people you haven't
   added yet — so it's all in one."

- ONE search, Instagram-style. Typing replaces the chips and list with results in three groups:
  your friends who match (instant, on the phone), group and class chats that match, then everyone
  else on TermChamp who matches (find_people — name, @username or school email, new in
  sql/professify-find-people.sql — or, until that runs, the desktop's search_people +
  find_profile_by_handle; after 300ms and 2+ letters, giving up after 10s) with Add / Requested / Accept on each row. A friend the server also returns
  shows once, under Friends. Clearing the box brings the chips and list back.
- "Invite friends" (full width, under the search) opens a sheet with a QR code and the link, plus
  Share and Copy. The QR generator is lifted verbatim from the desktop's index.html at patch time
  (qrcode-generator 1.4.4, MIT), so it works with no CDN.
- THE LINK IS FIXED: the phone shared termchamp.com/?invite=<username>, which the desktop ignores (it
  only reads a user id), so a phone invite never sent anyone a request. It is now the desktop's own
  link, termchamp.com/invite?add=<your id>: opening it sends YOU a friend request, which you accept.
- The + button in the Friends header and the Invite card at the bottom are gone (the search and the
  button replace them). The Add friends sheet stays for "See all" suggestions and Champ.
- A search result no longer wipes a friend's loaded classes (personFrom starts them empty; the Add
  friends sheet had the same bug whenever the server returned a friend).
- Tab bar: a red count (9+ past nine) on Friends while requests are waiting; with none, the pink
  unread-messages dot as before. The tab's accessible name says how many requests.

Usage: python3 friends-search-invite-2026-09-30.py <repo-dir>   (edits <repo-dir>/app/index.html;
reads <repo-dir>/index.html for the QR generator). Every anchor must match exactly once.
"""
import sys, os, re
d = sys.argv[1]
p = os.path.join(d, 'app', 'index.html')
s = open(p, encoding='utf-8').read()
if 'SHEETS.invite' in s: sys.exit('already patched')
desk = open(os.path.join(d, 'index.html'), encoding='utf-8').read()
m = re.search(r'<script>/\* embedded-qr-generator \(qrcode-generator v1\.4\.4, MIT\)[^\n]*\n.*?\n</script>\n', desk, re.S)
if not m: sys.exit('QR generator not found in index.html')
QR = m.group(0).replace('<script>/* embedded-qr-generator', '<script>/* embedded-qr-generator, lifted verbatim from index.html by friends-search-invite-2026-09-30.py —', 1)

R = [
 # 0. the QR generator, before </head>
 ("</head>", QR + "</head>"),
 # 1. a QR icon
 (" link:'<path d=\"M10 14a4 4 0 0 0 5.7 0",
  " qr:'<rect x=\"4\" y=\"4\" width=\"6.5\" height=\"6.5\" rx=\"1.2\"/><rect x=\"13.5\" y=\"4\" width=\"6.5\" height=\"6.5\" rx=\"1.2\"/><rect x=\"4\" y=\"13.5\" width=\"6.5\" height=\"6.5\" rx=\"1.2\"/><path d=\"M13.5 13.5h2.5v2.5h-2.5zM18 18h2v2h-2zM13.5 18.5v1.5M18 13.5h2\"/>',\n link:'<path d=\"M10 14a4 4 0 0 0 5.7 0"),
 # 2. the Friends screen: search on top, Invite friends under it, then the body
 ("SCREENS.friends = () => {\n"
  "  const F = S.friendsFilter, sug = TC.suggestions.filter(id => TC.relation(id) !== 'friends');\n"
  "  return {\n"
  "    body: `<div class=\"fhdr\"><div class=\"title\">Friends</div><button class=\"plusbtn\" data-a=\"sheet\" data-x=\"addFriend\" aria-label=\"Add friend\">${ic('plus', 24, 2.6)}</button></div>\n"
  " <label class=\"search\"><span style=\"color:var(--pink)\">${ic('search', 22, 2.4)}</span><input id=\"fq\" data-in=\"fq\" value=\"${esc(S.fq)}\" placeholder=\"Search friends & chats\" autocomplete=\"off\"></label>\n",
  "/* Friends (Tate, 2026-09-30): ONE search for everyone, Instagram-style — your friends, your chats and\n"
  "   everyone else on TermChamp — and one clear Invite friends button under it (link + QR). */\n"
  "function fPersonRow(id) {\n"
  "  const p = PEOPLE[id], rel = TC.relation(id);\n"
  "  const btn = rel === 'incoming' ? `<button class=\"pbtn pink\" data-a=\"acceptReq\" data-x=\"${id}\">Accept</button>`\n"
  "    : `<button class=\"pbtn ${rel === 'sent' ? 'done' : 'pink'}\" data-a=\"addFriend\" data-x=\"${id}\">${rel === 'sent' ? 'Requested' : 'Add'}</button>`;\n"
  "  return `<div class=\"li fsr\">${pav(id, 46, 16)}<button class=\"grow fsr-who\" data-a=\"openFriend\" data-x=\"${id}\"><span class=\"fsr-nm\">${esc(p.name)}</span><span class=\"muted b fsr-sub\">${p.handle ? '@' + esc(p.handle) : esc(p.sub || '')}</span></button>${btn}</div>`;\n"
  "}\n"
  "function fSearchResults(raw) {\n"
  "  const q = raw.trim(), ql = q.toLowerCase().replace(/^@/, '');\n"
  "  const hit = id => { const p = PEOPLE[id]; return !!p && ((p.name || '').toLowerCase().includes(ql) || (p.handle || '').toLowerCase().includes(ql)); };\n"
  "  let fr = TC.friends.filter(hit);\n"
  "  const chats = TC.threads.filter(t => t.kind !== 'direct' && threadName(t).toLowerCase().includes(ql));\n"
  "  let R = UI.fPeople && UI.fPeople.q === q ? UI.fPeople : null;\n"
  "  if (q.length >= 2 && !R) { UI.fPeople = R = { q, res: 'busy' }; setTimeout(() => fPeopleRun(q), 0); }   // e.g. a search kept from last time\n"
  "  if (R && Array.isArray(R.res)) fr = fr.concat(R.res.filter(id => TC.relation(id) === 'friends' && fr.indexOf(id) < 0));   // e.g. found by school email\n  let others;\n"
  "  if (q.length < 2) others = `<div class=\"muted b fs-note\">Type 2 or more letters to search everyone on TermChamp.</div>`;\n"
  "  else if (R.res === 'busy') others = loadingCard('Searching TermChamp…');\n"
  "  else if (R.err) others = `<div class=\"tc-err\" style=\"margin:0 16px\">Couldn’t search right now — check your connection.<br><button class=\"pbtn pink\" style=\"margin-top:10px\" data-a=\"fqRetry\">Try again</button></div>`;\n"
  "  else {\n"
  "    const ids = R.res.filter(id => TC.relation(id) !== 'friends' && fr.indexOf(id) < 0);\n"
  "    others = ids.length ? `<div class=\"card list\" style=\"margin:0 16px\">${ids.map(fPersonRow).join('')}</div>`\n"
  "      : `<div class=\"empty\" style=\"padding-top:6px\"><b>${fr.length ? 'No one else' : 'No one'} matching “${esc(q)}” on TermChamp yet</b><button class=\"pbtn pink\" style=\"margin-top:10px\" data-a=\"sheet\" data-x=\"invite\">Invite them</button></div>`;\n"
  "  }\n"
  "  const friendRows = fr.map(id => { const st = status(id); return `<button class=\"li\" data-a=\"openFriend\" data-x=\"${id}\">${pav(id, 46, 16)}<div class=\"grow\"><div style=\"font-weight:900;font-size:16px\">${esc(PEOPLE[id].name)}</div><div class=\"b fsr-sub\" style=\"font-size:13px\">${PEOPLE[id].handle ? `<span class=\"muted\">@${esc(PEOPLE[id].handle)} · </span>` : ''}<span style=\"color:${st.c || 'var(--muted)'}\">${st.free === null ? esc(st.t) : '● ' + esc(st.t)}</span></div></div><span class=\"chev\">${ic('chevR', 18)}</span></button>`; }).join('');\n"
  "  return `${fr.length ? `<div class=\"fs-h\">Friends</div><div class=\"card list\" style=\"margin:0 16px\">${friendRows}</div>` : ''}\n"
  "   ${chats.length ? `<div class=\"fs-h\">Group chats</div><div class=\"card\" style=\"margin:0 16px;padding:2px 0\">${chats.map(threadRow).join('')}</div>` : ''}\n"
  "   <div class=\"fs-h\">${fr.length || chats.length ? 'More people' : 'People'}</div>${others}`;\n"
  "}\n"
  "async function fPeopleRun(q) {\n"
  "  if (S.fq.trim() !== q) return;\n"
  "  let next;\n"
  "  try { next = { q, res: await Promise.race([TC.searchPeople(q), new Promise((_, no) => setTimeout(() => no(new Error('timeout')), 10000))]) }; } catch (e) { next = { q, err: 1 }; }\n"
  "  if (UI.fPeople && UI.fPeople.q === q) { UI.fPeople = next; fRepaint(); }\n"
  "}\n"
  "function friendsBody() {\n"
  "  const F = S.friendsFilter, sug = TC.suggestions.filter(id => TC.relation(id) !== 'friends');\n"
  "  if (S.fq.trim()) return fSearchResults(S.fq);\n"
  "  return `\n"),
 (" <div id=\"flist\">${friendsList()}</div>\n",
  " <div id=\"flist\">${friendsList()}</div>\n"),
 (" ${F === 'all' ? `<div class=\"card row\" style=\"margin:14px 16px 0;padding:14px 16px\"><span class=\"sq\" style=\"width:44px;height:44px;background:var(--pink-soft);color:var(--pink)\">${ic('link', 22)}</span><div class=\"grow\"><div style=\"font-weight:900;font-size:15.5px\">Invite friends</div><div class=\"muted b\" style=\"font-size:13px\">Send them a link to TermChamp</div></div><button class=\"pbtn pink\" data-a=\"copyInvite\">Share</button></div>` : ''}\n"
  " <div class=\"spacer\"></div>`, tabbar: true, fab: true\n"
  "  };\n"
  "};",
  "`;\n"
  "}\n"
  "function fRepaint() { const el = document.getElementById('fbody'); if (el) el.innerHTML = friendsBody(); }\n"
  "SCREENS.friends = () => ({\n"
  "  body: `<div class=\"fhdr\"><div class=\"title\">Friends</div></div>\n"
  " <label class=\"search fsearch\"><span style=\"color:var(--pink)\">${ic('search', 22, 2.4)}</span><input id=\"fq\" data-in=\"fq\" type=\"search\" value=\"${esc(S.fq)}\" placeholder=\"Find friends by name or @username\" aria-label=\"Find friends by name or @username\" autocomplete=\"off\" autocapitalize=\"off\" autocorrect=\"off\" spellcheck=\"false\" enterkeyhint=\"search\"><button type=\"button\" class=\"fqx\" data-a=\"fqClear\" aria-label=\"Clear search\">${ic('x', 16, 2.6)}</button></label>\n"
  " <button class=\"btn invbtn\" data-a=\"sheet\" data-x=\"invite\">${ic('qr', 22, 2.2)}Invite friends</button>\n"
  " <div id=\"fbody\">${friendsBody()}</div>\n"
  " <div class=\"spacer\"></div>`, tabbar: true, fab: true\n"
  "});"),
 # 3. typing: repaint the body (the box keeps focus) and search everyone after 300ms
 ("  else if (k === 'fq') { S.fq = ev.target.value; document.getElementById('flist').innerHTML = friendsList(); }",
  "  else if (k === 'fq') {\n"
  "    S.fq = ev.target.value; const q = S.fq.trim(); clearTimeout(fqT);\n"
  "    if (q.length >= 2 && !(UI.fPeople && UI.fPeople.q === q && UI.fPeople.res !== 'busy')) { UI.fPeople = { q, res: 'busy' }; fqT = setTimeout(() => fPeopleRun(q), 300); }\n"
  "    fRepaint();\n"
  "  }"),
 ("let qT;", "let qT, fqT;"),
 ("document.addEventListener('keydown', ev => { if (ev.key === 'Escape' && (UI.sheet || UI.champ)) A.closeSheet(); });",
  "document.addEventListener('keydown', ev => { if (ev.key === 'Escape' && (UI.sheet || UI.champ)) A.closeSheet(); });\ndocument.addEventListener('keydown', ev => { if (ev.key === 'Enter' && ev.target && ev.target.id === 'fq') { ev.preventDefault(); ev.target.blur(); } });"),
 # 4. the invite link the desktop actually reads, and the invite sheet
 ("  copyInvite: async () => {\n"
  "    const url = WEB + '/' + (PEOPLE.me.handle ? '?invite=' + encodeURIComponent(PEOPLE.me.handle) : '');\n"
  "    try { if (navigator.share) {",
  "  fqClear: () => { S.fq = ''; UI.fPeople = null; clearTimeout(fqT); const el = document.getElementById('fq'); if (el) { el.value = ''; el.focus(); } fRepaint(); },\n  fqRetry: () => { const q = S.fq.trim(); UI.fPeople = { q, res: 'busy' }; fRepaint(); fPeopleRun(q); },\n"
  "  copyLink: async () => { const url = inviteUrl(); try { await navigator.clipboard.writeText(url); toast('Invite link copied'); } catch (e) { toast(url); } },\n"
  "  copyInvite: async () => {\n"
  "    const url = inviteUrl();\n"
  "    try { if (navigator.share) {"),
 ("SHEETS.addFriend = (o) => {",
  "/* The desktop's own invite link (qrPayloadFor in index.html): /invite carries the preview card, then\n"
  "   /?add=<id> — opening it signs the friend in and sends YOU a friend request to accept. (The phone used\n"
  "   to share /?invite=<username>, which the desktop ignores: it only reads a user id.) */\n"
  "function inviteUrl() { return String(WEB || '').replace(/\\/+$/, '') + (TC.user ? '/invite?add=' + encodeURIComponent(TC.user.id) : '/'); }\n"
  "function inviteQr(url) {\n"
  "  try { const q = qrcode(0, 'M'); q.addData(url); q.make(); return q.createSvgTag({ cellSize: 5, margin: 2, scalable: true }); } catch (e) { return ''; }\n"
  "}\n"
  "SHEETS.invite = () => {\n"
  "  const url = inviteUrl(), qr = inviteQr(url);\n"
  "  return `<div class=\"row sb\"><h3>Invite friends</h3><button class=\"xbtn\" data-a=\"closeSheet\" aria-label=\"Close\">${ic('x', 16, 2.4)}</button></div>\n"
  " <div class=\"muted b\" style=\"font-size:14px;margin:4px 0 14px\">They scan it with their phone camera, or open the link. Once they sign in, you get a friend request from them to accept.</div>\n"
  " ${qr ? `<div class=\"invqr\" role=\"img\" aria-label=\"QR code for your invite link\">${qr}</div>` : `<div class=\"tc-err\">Couldn’t draw the QR code — share the link instead.</div>`}\n"
  " <div class=\"invurl\">${esc(url)}</div>\n"
  " <div class=\"row\" style=\"gap:10px;margin-top:14px\"><button class=\"btn soft\" data-a=\"copyLink\">Copy link</button><button class=\"btn invshare\" data-a=\"copyInvite\">Share link</button></div>`;\n"
  "};\n"
  "SHEETS.addFriend = (o) => {"),
 (" <button class=\"btn soft\" style=\"margin-top:14px\" data-a=\"copyInvite\">Share an invite link</button>`;",
  " <button class=\"btn soft\" style=\"margin-top:14px\" data-a=\"sheet\" data-x=\"invite\">Invite friends — link or QR code</button>`;"),
 ("'invite link': ['copyInvite', '']", "'invite link': ['sheet', 'invite']"),
 ("${TC.friends.length ? '' : 'Tap + to find classmates.'}", "${TC.friends.length ? '' : 'Search above to find classmates, or invite them.'}"),
 # 4b. searchPeople: find_people (name, @username or school email — sql/professify-find-people.sql)
 #     first; until that SQL runs, the desktop's search_people + find_profile_by_handle. A result
 #     never wipes a friend's loaded classes (personFrom starts secs empty: the Add friends sheet
 #     showed "hasn't added classes" whenever the server returned a friend), a failed handle lookup
 #     is never read as "no one", and a stalled request gives up after 10s.
 ("TC.searchPeople = async function (q) {\n"
  "  q = String(q || '').trim(); if (q.length < 2) return [];\n"
  "  const jobs = [Promise.resolve(TC.client().rpc('search_people', { q }))];\n"
  "  const h = q.replace(/^@/, '');\n"
  "  if (/^[A-Za-z0-9._]+$/.test(h)) jobs.push(Promise.resolve(TC.client().rpc('find_profile_by_handle', { handle: h })).catch(() => ({ data: [] })));\n"
  "  const res = await Promise.all(jobs);\n"
  "  if (res[0] && res[0].error) throw res[0].error;\n"
  "  const seen = {}, out = [];\n"
  "  res.forEach(r => ((r && r.data) || []).forEach(p => {\n"
  "    if (!p || !p.id || p.id === TC.user.id || seen[p.id]) return; seen[p.id] = 1;\n"
  "    PEOPLE[p.id] = Object.assign(PEOPLE[p.id] || {}, personFrom(p)); out.push(p.id);\n"
  "  }));\n"
  "  return out;\n"
  "};",
  "const noRpc = e => !!e && (e.code === 'PGRST202' || e.code === '42883' || /could not find the function|function .* does not exist/i.test(e.message || ''));\n"
  "TC.searchPeople = async function (q) {\n"
  "  q = String(q || '').trim(); if (q.length < 2) return [];\n"
  "  const sb = TC.client(); let res;\n"
  "  if (!TC.noFindPeople) {\n"
  "    const r = await sb.rpc('find_people', { q });\n"
  "    if (!r.error) res = [r];\n"
  "    else if (noRpc(r.error)) TC.noFindPeople = true;   // the SQL hasn't run yet: use the desktop's two RPCs\n"
  "    else throw r.error;\n"
  "  }\n"
  "  if (!res) {\n"
  "    const jobs = [Promise.resolve(sb.rpc('search_people', { q }))];\n"
  "    const h = q.replace(/^@/, '');\n"
  "    if (/^[A-Za-z0-9._]+$/.test(h)) jobs.push(Promise.resolve(sb.rpc('find_profile_by_handle', { handle: h })).catch(e => ({ error: e || { message: 'failed' } })));\n"
  "    res = await Promise.all(jobs);\n"
  "    if (res[0] && res[0].error) throw res[0].error;\n"
  "  }\n"
  "  const seen = {}, out = [];\n"
  "  res.forEach(r => ((r && r.data) || []).forEach(p => {\n"
  "    if (!p || !p.id || p.id === TC.user.id || seen[p.id]) return; seen[p.id] = 1;\n"
  "    const was = PEOPLE[p.id];\n"
  "    PEOPLE[p.id] = was ? Object.assign(was, { avatar: was.avatar || p.avatar_url || '', handle: was.handle || p.username || '' }) : personFrom(p);\n"
  "    out.push(p.id);\n"
  "  }));\n"
  "  if (!out.length && res[1] && res[1].error) throw res[1].error;   // half the search failed: never read that as \"no one\"\n"
  "  return out;\n"
  "};"),
 # 5. tab bar: a red count while requests are waiting
 ("  const badge = k => k === 'friends' && (TC.requests.length + TC.threads.filter(isUnread).length) ? '<span class=\"dot\" style=\"position:absolute;top:6px;right:calc(50% - 22px)\"></span>' : '';",
  "  /* Friends: a red count while friend requests are waiting (Tate, 2026-09-30); with none, the pink dot\n"
  "     for unread messages, as before. */\n"
  "  const nReq = TC.requests.length;\n"
  "  const badge = k => k !== 'friends' ? '' : nReq ? `<span class=\"tbadge\" aria-hidden=\"true\">${nReq > 9 ? '9+' : nReq}</span>` : TC.threads.filter(isUnread).length ? '<span class=\"dot\" style=\"position:absolute;top:6px;right:calc(50% - 22px)\"></span>' : '';\n"
  "  const tabLabel = k => k === 'friends' && nReq ? ` aria-label=\"Friends, ${nReq} friend request${nReq === 1 ? '' : 's'}\"` : '';"),
 ('data-a="tab" data-x="${k}">', 'data-a="tab" data-x="${k}"${tabLabel(k)}>'),
 # 6. styles
 (".plusbtn{", ".fsearch{margin:0 16px}\n"
  ".fsearch input{flex:1;min-width:0;font-size:16px;font-weight:700;height:100%;background:none;border:0;outline:0;color:var(--ink)}\n"
  ".fsearch input::placeholder{color:var(--muted)}\n"
  ".fsearch input::-webkit-search-cancel-button{-webkit-appearance:none}\n"
  ".invbtn{display:flex;align-items:center;justify-content:center;gap:10px;margin:12px 16px 4px;width:calc(100% - 32px);background:var(--pink);box-shadow:0 8px 18px rgba(219,39,119,.28)}\n"
  ".invshare{background:var(--pink);box-shadow:0 8px 18px rgba(219,39,119,.28)}\n"
  ".fs-h{font-size:13px;font-weight:900;letter-spacing:.04em;text-transform:uppercase;color:var(--ink3);padding:16px 20px 8px}\n"
  ".fs-note{font-size:13.5px;padding:0 20px;color:var(--ink3)}\n.fsearch{position:relative}\n.fqx{width:44px;height:44px;margin-right:-12px;flex:none;display:grid;place-items:center;border:0;background:none;color:var(--muted);border-radius:50%}\n.fsearch input:placeholder-shown + .fqx{display:none}\n.fsr .pbtn,#fbody .empty .pbtn{position:relative}\n.fsr .pbtn::after,#fbody .empty .pbtn::after{content:\"\";position:absolute;inset:-4px -2px}\n"
  ".fsr .fsr-who{display:flex;flex-direction:column;align-items:flex-start;text-align:left;min-width:0;background:none;border:0;padding:0;font:inherit;color:inherit}\n"
  ".fsr-nm{font-weight:900;font-size:16px;max-width:100%;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}\n"
  ".fsr-sub{font-size:13px;max-width:100%;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}\n"
  ".linkbtn{background:none;border:0;padding:0;font:inherit;font-weight:900;color:inherit;text-decoration:underline}\n"
  ".invqr{width:220px;height:220px;margin:0 auto;background:#fff;border-radius:16px;padding:8px;box-shadow:inset 0 0 0 1.5px var(--line)}\n"
  ".invqr svg{width:100%;height:100%;display:block}\n"
  ".invurl{margin-top:12px;padding:10px 12px;border-radius:12px;background:var(--bg);font-size:12.5px;font-weight:700;color:var(--ink3);word-break:break-all;text-align:center}\n"
  ".tbadge{position:absolute;top:3px;left:calc(50% + 5px);min-width:18px;height:18px;padding:0 5px;box-sizing:border-box;border-radius:9px;background:#DC2626;color:#fff;font-size:11px;font-weight:900;line-height:18px;text-align:center;box-shadow:0 0 0 2px #fff}\n"
  ".plusbtn{"),
 (".pbtn.done{background:var(--bg);color:var(--muted)}", ".pbtn.done{background:var(--bg);color:var(--ink3)}"),   # 4.40:1 → 9.7:1
]
for a, b in R:
    n = s.count(a)
    if n != 1: sys.exit(f'anchor matched {n}x: {a[:90]}')
    s = s.replace(a, b)
open(p, 'w', encoding='utf-8').write(s)
print('patched', p)
