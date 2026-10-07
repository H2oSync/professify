#!/usr/bin/env python3
r"""Block, Report and Leave group in the phone app (App Store chunk 3, 2026-10-04).

Apple 1.2 (apps with content people post): a way to report it, a way to block abusive people, and
a filter. Messages could already be reported (12:00). This adds the rest, with no SQL: block_user(),
unblock_user(), my_blocks(), the reports table and the "you can leave" policy on
conversation_members are all live (professify-safety.sql, professify-messaging.sql).

  · A person's page has ⋯ top right: Report <name> · Block <name> (or Unblock). A blocked person's
    page says "You blocked <name>" with Unblock, never Message or Add friend.
  · A chat's ⋯: a 1:1 adds Report <name> · Block <name>. A group lists who's in it (each opens their
    page, where they can be reported or blocked), then Delete chat · Leave group · Report this
    group's name (only a group someone else named).
  · Holding someone's message adds Block <name> under Report.
  · Block asks first and says what it does: no messages or friend requests either way, you stop
    being friends, nobody in a group you share can be sent to by either of you (the live insert
    policy), and they aren't told. block_user() ends the friendship in the same transaction.
  · A chat with someone you blocked shows "You blocked <name>" with Unblock instead of the composer.
  · Blocked people are left out of search and People you might know (the database already stops
    every request and message; this keeps them off your screen).
  · Report a person (kind user, target the person), a review (kind review, its id; the writer stays
    anonymous) or a group's name (kind user against whoever named it, target "group:<id>", the
    name in the note, since reports_kind_ck has no 'group'). One tap on a reason sends it.
  · Leave group deletes your own conversation_members row; a delete that removes nothing is said.
  · Settings' Blocked people no longer sends you to termchamp.com.

Runs after delete-30-days-2026-10-04.py. Usage: python3 block-report-leave-2026-10-04.py <repo-dir>.
"""
import sys, os
p = os.path.join(sys.argv[1], 'app', 'index.html')
s = open(p, encoding='utf-8').read()

def rep(a, b, label):
    global s
    n = s.count(a)
    if n != 1: sys.exit(f'{label}: anchor matched {n}x')
    s = s.replace(a, b)

# 1. Icons: a "no" circle for Block, a door for Leave.
rep(""" link:'<path d="M10 14a4 4 0 0 0 5.7 0l3-3a4 4 0 0 0-5.7-5.7l-1 1"/><path d="M14 10a4 4 0 0 0-5.7 0l-3 3a4 4 0 0 0 5.7 5.7l1-1"/>'
};""",
    """ link:'<path d="M10 14a4 4 0 0 0 5.7 0l3-3a4 4 0 0 0-5.7-5.7l-1 1"/><path d="M14 10a4 4 0 0 0-5.7 0l-3 3a4 4 0 0 0 5.7 5.7l1-1"/>',
 ban:'<circle cx="12" cy="12" r="8.5"/><path d="m6 6 12 12"/>',
 leave:'<path d="M13.5 4.5h4a1.5 1.5 0 0 1 1.5 1.5v12a1.5 1.5 0 0 1-1.5 1.5h-4"/><path d="m10 8-4 4 4 4M6 12h9.5"/>'
};""",
    'icons')

# 2. CSS
rep(".li.danger{color:#B91C1C}\n",
    ".li.danger{color:#B91C1C}\n"
    "/* Block, Report, Leave group (2026-10-04) */\n"
    ".revflag{display:inline-grid;place-items:center;width:40px;height:40px;margin:-12px -12px -12px -6px;border-radius:50%;color:#94A3B8}\n"
    ".revflag:active{background:#F1F5F9;color:#B91C1C}\n"
    ".blockbar{display:flex;gap:12px;align-items:center;padding:12px 14px 30px;background:rgba(244,246,251,.96);backdrop-filter:blur(10px);border-top:1px solid var(--line);font-size:14px;line-height:1.4}\n"
    ".tc-people{font-size:12.5px;margin:2px 4px 6px}\n"
    ".blockbar.col{flex-direction:column;align-items:stretch;gap:10px}\n"
    ".pbtn.ghost{background:#fff;color:var(--ink);box-shadow:inset 0 0 0 1.5px var(--line)}\n"
    ".blknote{text-align:center;font-size:12.5px;line-height:1.4;margin:8px 20px 10px}\n",
    'css')
rep("  .composer{padding-bottom:max(env(safe-area-inset-bottom),12px)}\n",
    "  .composer{padding-bottom:max(env(safe-area-inset-bottom),12px)}\n"
    "  .blockbar{padding-bottom:max(env(safe-area-inset-bottom),12px)}\n",
    'css-safe-area')

# 3. Who you blocked is known from the start (it was only read when Settings opened).
rep("  await Promise.all([loadMine(), loadFriends(), loadPlans(), loadWatches(), loadReviews(), loadThreads()]);",
    "  const blk = TC.loadBlocks().catch(() => {});   /* blocks first: they decide which messages a chat shows */\n"
    "  await Promise.all([loadMine(), loadFriends(), loadPlans(), loadWatches(), loadReviews(), blk.then(() => loadThreads())]);",
    'boot-blocks')
rep("""TC.loadBlocks = async function () {
  const r = await TC.client().rpc('my_blocks');
  TC.blocks = (!r.error && Array.isArray(r.data)) ? r.data : [];
  TC.blocksErr = !!r.error;
};""",
    """TC.loadBlocks = async function () {
  const r = await TC.client().rpc('my_blocks');
  if (!r.error && Array.isArray(r.data)) { TC.blocks = r.data; TC.blocksErr = false; return; }
  /* a failed read keeps the list you had: a network blip never brings a blocked person back on screen */
  if (!Array.isArray(TC.blocks)) TC.blocks = [];
  TC.blocksErr = true;
};
/* Someone you blocked. The database refuses their requests and messages whatever this says; this
   only keeps them off your screen. */
function isBlocked(id) { return !!id && Array.isArray(TC.blocks) && TC.blocks.some(b => b && b.id === id); }
/* Someone met in a chat (a group member, a sender) may not be a friend yet: give them a page. A
   name not loaded yet is filled in once it is, never kept as a placeholder. */
function ensurePerson(uid) {
  if (!uid) return null;
  const n = TC.names[uid];
  if (!PEOPLE[uid]) PEOPLE[uid] = Object.assign(personFrom({ id: uid, display_name: n && n.name, avatar_url: n && n.avatar }), { thin: !n });
  else if (PEOPLE[uid].thin && n) Object.assign(PEOPLE[uid], personFrom({ id: uid, display_name: n.name, avatar_url: n.avatar }), { thin: false });
  return PEOPLE[uid];
}
/* A blocked person's messages are hidden (old ones too: no new ones can arrive). Said once, at the top. */
function blockedNote(rows) {
  const who = [...new Set((rows || []).filter(m => isBlocked(m.sender) && !TC.hidden.has(String(m.id))).map(m => m.sender))];
  if (!who.length) return '';
  const names = who.map(u => esc(nameOf(u).split(' ')[0]));
  return `<div class="muted b blknote" role="note">Messages from ${names.length > 2 ? names.slice(0, 2).join(', ') + ' and others' : names.join(' and ')} are hidden because you blocked them.</div>`;
}
/* What a report refusal means: only the hourly limit is a row-security refusal; a lost session is
   "permission denied" (42501 too) and must not be called a limit. */
function reportErrSay(e) {
  const t = String((e && e.code) || '') + ' ' + String((e && e.message) || '');
  if (/row-level/i.test(t)) return 'You’ve sent a lot of reports this hour — try again later';
  if (isJwtErr(e) || /42501|permission denied/i.test(t)) return 'Your sign-in expired. Sign out and back in, then try again.';
  if (/failed to fetch|network|load failed|timeout/i.test(t)) return 'Couldn’t reach TermChamp — check your connection and try again';
  return 'Couldn’t send the report — try again';
}""",
    'is-blocked')

# 4. Blocked people stay out of suggestions and search.
rep("      const id = x.id || x.user_id; if (!id || id === TC.user.id || TC.friends.indexOf(id) >= 0) return;",
    "      const id = x.id || x.user_id; if (!id || id === TC.user.id || TC.friends.indexOf(id) >= 0 || isBlocked(id)) return;",
    'suggestions')
rep("    if (!p || !p.id || p.id === TC.user.id || seen[p.id]) return; seen[p.id] = 1;",
    "    if (!p || !p.id || p.id === TC.user.id || seen[p.id] || isBlocked(p.id)) return; seen[p.id] = 1;",
    'search')

# 5. Threads remember who made them (whoever named a group is who a name report is about).
rep("  TC.threads = (convs.data || []).map(c => ({ id: c.id, kind: c.kind, title: c.title, last_at: c.last_at,",
    "  TC.threads = (convs.data || []).map(c => ({ id: c.id, kind: c.kind, title: c.title, created_by: c.created_by, last_at: c.last_at,",
    'threads-creator')
rep("TC.threads.unshift({ id: cid, kind: 'group', title: title || null, last_at:",
    "TC.threads.unshift({ id: cid, kind: 'group', title: title || null, created_by: TC.user.id, last_at:",
    'new-group-creator')

# 6. Reviews carry their id, so one can be reported (both reads that fill TC.reviewsByName: all
#    reviews at boot, and one professor's on their page). The desktop reads id from this view too.
_c = "  const cols = 'professor_key,professor_name,course,score,would_again,tags,note,created_at,difficulty,grade,format';"
if s.count(_c) != 2: sys.exit(f'review-id: anchor matched {s.count(_c)}x, expected 2')
s = s.replace(_c, "  const cols = 'id,professor_key,professor_name,course,score,would_again,tags,note,created_at,difficulty,grade,format';")
rep("""${v._mine ? '<span class="mine">You</span>' : ''}</span><span class="muted b" style="font-size:13px">${agoText(v.created_at)}</span></div><p>${esc(v.note)}</p></div>`; }).join('')}""",
    """${v._mine ? '<span class="mine">You</span>' : ''}</span><span class="row" style="gap:2px"><span class="muted b" style="font-size:13px">${agoText(v.created_at)}</span>${revReportable(v) ? `<button class="revflag" data-a="reportAsk" data-x="review" data-y="${esc(String(v.id))}" aria-label="Report this review">${ic('flag', 15, 2.2)}</button>` : ''}</span></div><p>${esc(v.note)}</p></div>`; }).join('')}""",
    'review-flag')
# The page ends with the reviews, and Champ's button floats over the bottom right (180px up from the
# bottom, tab bar included): a deeper end lets the last review's flag scroll clear of it.
rep(""" <div class="spacer"></div>`, tabbar: true, fab: true
  };
};

/* ---- Rate""",
    """ <div class="spacer" style="height:200px"></div>`, tabbar: true, fab: true
  };
};

/* ---- Rate""",
    'prof-spacer')
rep("""function iReviewed(pk) {""",
    """/* Anyone's review but your own, once it has an id to point at. */
function revReportable(v) { return !!v && v.id != null && !v._mine && !(TC.myReviews || []).some(x => x && String(x.id) === String(v.id)); }
function reviewById(id) { return Object.values(TC.reviewsByName || {}).reduce((a, l) => a.concat(l || []), []).find(v => v && v.id != null && String(v.id) === String(id)) || null; }
function iReviewed(pk) {""",
    'review-helpers')

# 7. A person's page: ⋯ (Report, Block), and what a blocked person's page says.
rep("""  const st = isF ? status(id) : null;
  return {
    body: `<div class="topbtns"><button class="iconbtn" data-a="back" aria-label="Back">${ic('chevL', 22, 2.4)}</button></div>""",
    """  const bl = isBlocked(id), st = isF && !bl ? status(id) : null;
  return {
    body: `<div class="topbtns"><button class="iconbtn" data-a="back" aria-label="Back">${ic('chevL', 22, 2.4)}</button><button class="iconbtn" data-a="personMenu" data-x="${id}" aria-label="More for ${esc(p.short)}: report or block">${ic('dots', 20, 2, 'currentColor')}</button></div>""",
    'friend-menu')
rep("""  <div class="row" style="justify-content:center;margin-top:14px;gap:10px">${isF ? `<button class="pbtn pink" style="height:42px;width:200px" data-a="openChatWith\"""",
    """  <div class="row" style="justify-content:center;margin-top:14px;gap:10px">${bl ? `<button class="pbtn" style="height:42px;width:200px" data-a="unblock" data-x="${id}">Unblock</button>` : isF ? `<button class="pbtn pink" style="height:42px;width:200px" data-a="openChatWith\"""",
    'friend-unblock')
rep(""" ${isF ? friendWeek(id, secs, shared)""",
    """ ${bl ? `<div class="empty" style="margin-top:20px"><b>You blocked ${esc(p.short)}</b>You can’t message each other or send friend requests. ${esc(p.short)} isn’t told.</div>`
      : isF ? friendWeek(id, secs, shared)""",
    'friend-blocked')

# 8. Holding someone's message: Block them, under Report.
rep("""${!mine ? `<button class="li danger" data-a="reportMsg" data-x="${k}">${ic('flag', 20, 2.2)}<span class="grow b">Report</span></button>` : ''}</div>`;""",
    """${!mine ? `<button class="li danger" data-a="reportMsg" data-x="${k}">${ic('flag', 20, 2.2)}<span class="grow b">Report</span></button>` : ''}
 ${!mine && m.sender && !isBlocked(m.sender) ? `<button class="li danger" data-a="blockAsk" data-x="${esc(m.sender)}">${ic('ban', 20, 2.2)}<span class="grow b">Block ${esc(nameOf(m.sender).split(' ')[0])}</span></button>` : ''}</div>`;""",
    'msg-block')

# 9. The chat menu.
rep("""SHEETS.chatAct = ({ cid }) => {
  const t = chatOf(cid); if (!t) return '';
  return `<div class="row sb"><h3>${esc(threadName(t))}</h3><button class="xbtn" data-a="closeSheet" aria-label="Close">${ic('x', 16, 2.4)}</button></div>
 <div class="card list mact">${t.kind === 'direct' && threadOther(t) && TC.friends.includes(threadOther(t)) ? `<button class="li" data-a="openFriend" data-x="${esc(threadOther(t))}">${pav(threadOther(t), 28, 10)}<span class="grow b">See ${esc(nameOf(threadOther(t)).split(' ')[0])}’s page</span>${ic('chevR', 18)}</button>` : ''}
 ${TC.chatX.on !== false ? `<button class="li danger" data-a="chatDelAsk" data-x="${esc(cid)}">${ic('trash', 20, 2.2)}<span class="grow b">Delete chat</span></button>` : '<div class="muted b" style="font-size:13.5px;padding:12px 14px">Deleting chats isn’t switched on yet.</div>'}</div>`;
};""",
    """SHEETS.chatAct = ({ cid }) => {
  const t = chatOf(cid); if (!t) return '';
  const me = TC.user.id, o = t.kind === 'direct' ? threadOther(t) : null, of = o ? esc(nameOf(o).split(' ')[0]) : '';
  const others = t.kind === 'group' ? t.members.filter(u => u && u !== me) : [];
  others.forEach(ensurePerson);
  /* who's in a group, so any of them can be opened, then reported or blocked from their page */
  const people = others.length ? `<div class="muted b tc-people">In this group · ${others.length + 1} people</div><div class="card list mact" style="margin-bottom:12px">${others.map(u => `<button class="li" data-a="openFriend" data-x="${esc(u)}">${pav(u, 32, 11)}<span class="grow b">${esc(nameOf(u))}</span>${isBlocked(u) ? '<span class="muted b" style="font-size:12.5px">Blocked</span>' : ''}${ic('chevR', 18)}</button>`).join('')}</div>` : '';
  return `<div class="row sb"><h3>${esc(threadName(t))}</h3><button class="xbtn" data-a="closeSheet" aria-label="Close">${ic('x', 16, 2.4)}</button></div>
 ${people}<div class="card list mact">${o && TC.friends.includes(o) ? `<button class="li" data-a="openFriend" data-x="${esc(o)}">${pav(o, 28, 10)}<span class="grow b">See ${of}’s page</span>${ic('chevR', 18)}</button>` : ''}
 ${TC.chatX.on !== false ? `<button class="li danger" data-a="chatDelAsk" data-x="${esc(cid)}">${ic('trash', 20, 2.2)}<span class="grow b">Delete chat</span></button>` : '<div class="muted b" style="font-size:13.5px;padding:12px 14px">Deleting chats isn’t switched on yet.</div>'}
 ${t.kind === 'group' ? `<button class="li danger" data-a="leaveAsk" data-x="${esc(cid)}">${ic('leave', 20, 2.2)}<span class="grow b">Leave group</span></button>` : ''}
 ${t.kind === 'group' && t.title && t.created_by && t.created_by !== me ? `<button class="li danger" data-a="reportAsk" data-x="group" data-y="${esc(cid)}">${ic('flag', 20, 2.2)}<span class="grow b">Report this group’s name</span></button>` : ''}
 ${o ? `<button class="li danger" data-a="reportAsk" data-x="user" data-y="${esc(o)}">${ic('flag', 20, 2.2)}<span class="grow b">Report ${of}</span></button>
 ${isBlocked(o) ? `<button class="li" data-a="unblock" data-x="${esc(o)}">${ic('ban', 20, 2.2)}<span class="grow b">Unblock ${of}</span></button>` : `<button class="li danger" data-a="blockAsk" data-x="${esc(o)}">${ic('ban', 20, 2.2)}<span class="grow b">Block ${of}</span></button>`}` : ''}</div>`;
};
/* A person's page ⋯ */
SHEETS.personAct = ({ uid }) => {
  const p = PEOPLE[uid]; if (!p) return '';
  const f = esc(p.short);
  return `<div class="row sb"><h3>${esc(p.name)}</h3><button class="xbtn" data-a="closeSheet" aria-label="Close">${ic('x', 16, 2.4)}</button></div>
 <div class="card list mact"><button class="li danger" data-a="reportAsk" data-x="user" data-y="${esc(uid)}">${ic('flag', 20, 2.2)}<span class="grow b">Report ${f}</span></button>
 ${isBlocked(uid) ? `<button class="li" data-a="unblock" data-x="${esc(uid)}">${ic('ban', 20, 2.2)}<span class="grow b">Unblock ${f}</span></button>`
      : `<button class="li danger" data-a="blockAsk" data-x="${esc(uid)}">${ic('ban', 20, 2.2)}<span class="grow"><span class="b" style="display:block">Block ${f}</span><span class="muted b" style="font-size:12.5px">${f} isn’t told</span></span></button>`}</div>`;
};
/* Block asks first: what it does is more than the word says (it ends a friendship, and it stops a
   shared group for both of you — the live insert policy on messages). */
SHEETS.blockAsk = ({ uid }) => {
  const p = PEOPLE[uid]; if (!p) return '';
  const f = esc(p.short), busy = !!UI.busy.block;
  return `<h3>Block ${esc(p.name)}?</h3>
 <div class="muted b" style="font-size:14.5px;margin:8px 0 16px;line-height:1.45">You won’t be able to message each other or send friend requests, and ${f} won’t show up in your search or suggestions.${TC.friends.includes(uid) ? ` You stop being friends, so ${f} no longer sees your classes or plans.` : ''} In a group chat you’re both in, neither of you can send messages. ${f} isn’t told. You can unblock in Settings.</div>
 ${UI.blockErr ? `<div class="tc-err" role="alert" style="margin-bottom:10px">${esc(UI.blockErr)}</div>` : ''}
 <div style="display:grid;gap:8px"><button class="btn" style="background:#DC2626" data-a="blockGo" data-x="${esc(uid)}"${busy ? ' disabled' : ''}>${busy ? 'Blocking…' : 'Block ' + f}</button><button class="btn soft" data-a="closeSheet">Cancel</button></div>`;
};
SHEETS.leaveAsk = ({ cid }) => {
  const t = chatOf(cid); if (!t) return '';
  return `<h3>Leave ${esc(threadName(t))}?</h3>
 <div class="muted b" style="font-size:14.5px;margin:8px 0 16px;line-height:1.45">You’ll stop getting its messages and it leaves your chats. Everyone else stays in the group.</div>
 <div style="display:grid;gap:8px"><button class="btn" style="background:#DC2626" data-a="leaveGo" data-x="${esc(cid)}"${UI.busy.leave ? ' disabled' : ''}>${UI.busy.leave ? 'Leaving…' : 'Leave group'}</button><button class="btn soft" data-a="closeSheet">Cancel</button></div>`;
};
/* Report a person, a review or a group's name. What a moderator gets goes in the note, as it was
   when it was reported (a name or a review can be changed or deleted afterwards). */
const REPORT_FOR = {
  user: [['harassment', 'Harassment or bullying'], ['hate', 'Hate or slurs'], ['threat', 'A threat'], ['impersonation', 'Pretending to be someone else'], ['sexual', 'Sexual content'], ['private_info', 'Private information'], ['spam', 'Spam'], ['other', 'Something else']],
  review: [['not_about_teaching', 'Not about the class or teaching'], ['harassment', 'Harassment or bullying'], ['hate', 'Hate or slurs'], ['private_info', 'Names a student or shares private information'], ['sexual', 'Sexual content'], ['spam', 'Spam'], ['other', 'Something else']],
  group: [['harassment', 'Harassment or bullying'], ['hate', 'Hate or slurs'], ['threat', 'A threat'], ['sexual', 'Sexual content'], ['private_info', 'Private information'], ['spam', 'Spam'], ['other', 'Something else']]
};
function reportTarget(kind, ref) {
  if (kind === 'user') {
    const p = PEOPLE[ref]; if (!p || ref === TC.user.id) return null;
    return { h: 'Report ' + p.name, sub: `A moderator will see ${esc(p.short)}’s profile. ${esc(p.short)} won’t know it was you.`,
      row: { kind: 'user', target_id: ref, target_user: ref, note: 'Profile: ' + p.name + (p.handle ? ' (@' + p.handle + ')' : '') } };
  }
  if (kind === 'review') {
    const v = reviewById(ref); if (!v || !revReportable(v)) return null;
    return { h: 'Report this review', sub: 'A moderator will read it. Whoever wrote it won’t know it was you.',
      row: { kind: 'review', target_id: String(v.id), target_user: null, note: String(v.note || '').slice(0, 2000) || null } };
  }
  if (kind === 'group') {
    const t = chatOf(ref); if (!t || !t.title || !t.created_by || t.created_by === TC.user.id) return null;
    return { h: 'Report this group’s name', sub: `A moderator will see the name “${esc(t.title)}” and who gave it. They won’t know it was you.`,
      row: { kind: 'user', target_id: 'group:' + t.id, target_user: t.created_by, note: 'Group chat name: “' + t.title + '”' } };
  }
  return null;
}
SHEETS.report = ({ kind, ref }) => {
  const g = reportTarget(kind, ref); if (!g) return '';
  return `<div class="row sb"><h3>${esc(g.h)}</h3><button class="xbtn" data-a="closeSheet" aria-label="Close">${ic('x', 16, 2.4)}</button></div>
 <div class="muted b" style="font-size:14px;margin:4px 0 12px">${g.sub}</div>
 <div class="card list">${(REPORT_FOR[kind] || []).map(([k, l]) => `<button class="li" data-a="sendReportX" data-x="${k}"${UI.busy.report ? ' disabled' : ''}><span class="grow b">${l}</span>${ic('chevR', 18)}</button>`).join('')}</div>
 <div class="muted b" style="font-size:12.5px;margin-top:10px">If someone is in danger, call 911. TermChamp is not an emergency service.</div>`;
};
/* "You blocked …" in place of the composer. A group with someone you blocked can't take messages
   from either of you (the insert policy), so the box isn't offered there either. */
function chatBlockedBar(t) {
  const me = TC.user.id, who = (t.members || []).filter(u => u && u !== me).find(isBlocked) || (t.kind === 'direct' && isBlocked(threadOther(t)) ? threadOther(t) : null);
  if (!who) return '';
  const f = esc(nameOf(who).split(' ')[0]);
  if (t.kind === 'direct') return `<div class="blockbar" role="status"><span class="grow b">You blocked ${f}.</span><button class="pbtn" data-a="unblock" data-x="${esc(who)}">Unblock</button></div>`;
  return `<div class="blockbar col" role="status"><span class="b">You blocked ${f}, who’s in this group. Neither of you can send messages here.</span><span class="row" style="gap:8px;justify-content:flex-end"><button class="pbtn ghost" data-a="leaveAsk" data-x="${esc(t.id)}">Leave group</button><button class="pbtn" data-a="unblock" data-x="${esc(who)}">Unblock</button></span></div>`;
}""",
    'chat-menu')

# 10. The chat screen: the blocked bar instead of the composer.
rep("""    bot: `<form class="composer" data-submit="send" data-x="${id}">""",
    """    bot: chatBlockedBar(t) || `<form class="composer" data-submit="send" data-x="${id}">""",
    'composer')

# 11. Actions.
rep("""  unblock: async id => { const e = await TC.unblock(id); toast(e || 'Unblocked'); render(true); },""",
    """  unblock: async id => {
    if (!id || UI.busy['ub' + id]) return; UI.busy['ub' + id] = 1;
    let e; try { e = await TC.unblock(id); } catch (x) { e = 'Couldn’t unblock — try again.'; }
    UI.busy['ub' + id] = 0;
    if (!e && UI.sheet && /^(personAct|chatAct)$/.test(UI.sheet.type)) UI.sheet = null;
    toast(e || 'Unblocked'); render(true);
    if (!e && TC.user) loadThreads().then(() => render(true), () => {});   /* their messages are previews again */
  },
  personMenu: uid => { if (!uid || !PEOPLE[uid]) return; UI.sheet = { type: 'personAct', uid }; render(true); },
  blockAsk: uid => { if (!uid || !TC.user || uid === TC.user.id) return; ensurePerson(uid); UI.blockErr = ''; UI.sheet = { type: 'blockAsk', uid }; render(true); },
  blockGo: async uid => {
    if (!uid || UI.busy.block) return; UI.busy.block = 1; UI.blockErr = ''; render(true);
    let r; try { r = await TC.client().rpc('block_user', { p_target: uid }); } catch (e) { r = { error: { message: 'failed to fetch' } }; }
    UI.busy.block = 0;
    if (r.error) { UI.blockErr = dbSay(r.error, 'Couldn’t block them — try again.'); return render(true); }
    const p = PEOPLE[uid] || {};
    TC.blocks = [{ id: uid, display_name: p.name || 'Someone', username: p.handle || null, avatar_url: p.avatar || null, created_at: new Date().toISOString() }].concat((Array.isArray(TC.blocks) ? TC.blocks : []).filter(b => b && b.id !== uid));
    /* block_user() ended the friendship and any request in the same transaction */
    TC.friends = TC.friends.filter(x => x !== uid); TC.requests = TC.requests.filter(x => x !== uid); TC.sent = TC.sent.filter(x => x !== uid);
    TC.suggestions = TC.suggestions.filter(x => x !== uid);
    if (UI.fPeople && Array.isArray(UI.fPeople.res)) UI.fPeople.res = UI.fPeople.res.filter(x => x !== uid);
    if (UI.sheet && UI.sheet.type === 'blockAsk' && UI.sheet.uid === uid) UI.sheet = null;
    TC.threads.forEach(t => { if (t.last && isBlocked(t.last.sender)) t.last = lastVisible(t.id); });
    render(true); toast(p.short ? 'Blocked ' + p.short : 'Blocked');
    /* the server's view: the friendship is gone, chat previews skip their messages, the full list */
    Promise.all([loadFriends().catch(() => {}), loadThreads().catch(() => {}), TC.loadBlocks().catch(() => {})]).then(() => render(true));
  },
  reportAsk: (kind, ref) => { if (!TC.user || !ref) return; if (kind === 'user') ensurePerson(ref); UI.sheet = { type: 'report', kind, ref }; render(true); },
  sendReportX: async reason => {
    const sh = UI.sheet; if (!sh || sh.type !== 'report' || UI.busy.report) return;
    const g = reportTarget(sh.kind, sh.ref); if (!g) return;
    UI.busy.report = 1; render(true);
    let r; try { r = await TC.client().from('reports').insert(Object.assign({ reporter: TC.user.id, reason }, g.row)); } catch (e) { r = { error: { message: 'failed to fetch' } }; }
    UI.busy.report = 0;
    const mine = UI.sheet === sh;
    if (r.error) {
      const t = String(r.error.code || '') + ' ' + String(r.error.message || '');
      if (/23505|duplicate|one_per/.test(t)) { if (mine) UI.sheet = null; render(true); toast('You already reported this — it’s with a moderator'); return; }
      toast(reportErrSay(r.error)); render(true); return;
    }
    if (mine) UI.sheet = null; render(true); toast('Reported. A moderator will look at it.');
  },
  leaveAsk: cid => { if (!chatOf(cid)) return; UI.sheet = { type: 'leaveAsk', cid }; render(true); },
  leaveGo: async cid => {
    const t = chatOf(cid); if (!t || t.kind !== 'group' || UI.busy.leave) return; UI.busy.leave = 1; render(true);
    /* asks for the row back: a delete RLS refuses removes nothing and says nothing */
    let r; try { r = await TC.client().from('conversation_members').delete().eq('conversation_id', cid).eq('user_id', TC.user.id).select('conversation_id'); } catch (e) { r = { error: { message: 'failed to fetch' } }; }
    UI.busy.leave = 0;
    if (r.error || !(r.data || []).length) { toast(r.error ? 'Couldn’t leave the group — try again' : 'Couldn’t leave the group — you’re still in it'); render(true); return; }
    const name = threadName(t);
    TC.threads = TC.threads.filter(x => x.id !== cid); delete TC.rows[cid];
    if (UI.sheet && (UI.sheet.cid === cid)) UI.sheet = null;
    if (cur().s === 'chat' && cur().p && cur().p.id === cid) back(); else render(true);
    toast('You left ' + name);
  },""",
    'actions')

# 12. Settings no longer sends you to the website to block someone.
rep("""'<div class="muted b" style="padding:2px 0 10px">Nobody. Block someone from their profile on termchamp.com.</div>'""",
    """'<div class="muted b" style="padding:2px 0 10px;line-height:1.45">Nobody. To block someone, tap ⋯ on their page or in your chat with them. They aren’t told.</div>'""",
    'settings-text')

# 13. A blocked person's messages are hidden everywhere a message shows (the chat, its preview, unread).
rep("function msgVisible(m) { if (TC.hidden.has(String(m.id))) return false;",
    "function msgVisible(m) { if (TC.hidden.has(String(m.id)) || isBlocked(m.sender)) return false;",
    'msg-visible')
rep("""body: `<div class="msgs">${rows ? (msgs || '<div class="muted b" style="text-align:center;font-size:13px;margin-top:20px">Say hi 👋</div>')""",
    """body: `<div class="msgs">${rows ? blockedNote(rows) + (msgs || (chatBlockedBar(t) ? '' : '<div class="muted b" style="text-align:center;font-size:13px;margin-top:20px">Say hi 👋</div>'))""",
    'chat-note')
rep("""<div style="height:100px"></div>`,""",
    """<div style="height:${chatBlockedBar(t) ? 160 : 100}px"></div>`,""",
    'chat-end-room')
# 14. Likes: refused by the database in a chat with someone you blocked, so not offered there.
rep("""<div class="card list mact">${on ? `<button class="li" data-a="likeMsg\"""",
    """<div class="card list mact">${on && !(t && chatBlockedBar(t)) ? `<button class="li" data-a="likeMsg\"""",
    'like-row')
rep("""    if (how === 'dbl' && had) return;                    // a double-tap only ever likes""",
    """    if (how === 'dbl' && had) return;                    // a double-tap only ever likes
    if (!had && chatOf(cid) && chatBlockedBar(chatOf(cid))) return;   // refused with someone blocked here (unliking still works)""",
    'like-guard')
# 15. The message report says what a refusal means, like the others.
rep("""      toast(/row-level|42501/.test(t) ? 'You’ve sent a lot of reports this hour — try again later' : 'Couldn’t send the report — try again'); render(true); return;""",
    """      toast(reportErrSay(r.error)); render(true); return;""",
    'msg-report-err')

open(p, 'w', encoding='utf-8').write(s)
print('patched', p)
