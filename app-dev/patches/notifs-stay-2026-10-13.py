#!/usr/bin/env python3
"""Tate (2026-10-13), on the Notifications sheet reading "Nothing new": "for notifications once you've viewed it have them
stay there like instagram". The sheet used to list only pending friend requests and unread threads, so a message vanished
from it the moment you'd read it. Now it keeps them: friend requests and unread messages under "New" (bold, a pink dot),
then the messages you've already read under "Earlier" (the latest 30), newest first — like Instagram's activity feed.
The bell's dot is unchanged (new things only). "Nothing new" stays for a sheet with nothing at all. Replayable on 05:50.
  python3 notifs-stay-2026-10-13.py <repo-dir>"""
import pathlib, sys
ROOT = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else '.')
p = ROOT / 'app/index.html'; s = p.read_text()
def rep(a, b):
    global s
    if s.count(a) != 1: sys.exit(f'notifs-stay: expected 1 of {a[:80]!r}, found {s.count(a)}')
    s = s.replace(a, b)
rep("""SHEETS.notifs = () => {
  const reqs = TC.requests, un = TC.threads.filter(isUnread);
  const rows = [
    ...reqs.map(id => `<div class="row" style="width:100%;padding:12px 0;border-top:1px solid var(--line)">${pav(id, 42, 14)}<div class="grow"><div class="b" style="font-size:15px">${esc(PEOPLE[id].name)} sent you a friend request</div></div><button class="pbtn pink" data-a="acceptReq" data-x="${id}">Accept</button></div>`),
    ...un.map(t => `<button class="row" style="width:100%;padding:12px 0;border-top:1px solid var(--line)" data-a="openChatTab" data-x="${t.id}"><span class="sq" style="width:42px;height:42px;background:var(--rose-soft);color:var(--pink-t,#DB2777);border-radius:14px">${ic('msg', 20)}</span><div class="grow"><div class="b" style="font-size:15px">${esc(threadName(t))}</div><div class="muted b" style="font-size:13px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis">${esc(msgText(t.last))} · ${agoText(t.last.created_at)}</div></div><span class="chev">${ic('chevR', 18)}</span></button>`)
  ];
  return `<div class="row sb"><h3>Notifications</h3><button class="xbtn" data-a="closeSheet">${ic('x', 16, 2.4)}</button></div>
 ${rows.length ? rows.join('') : '<div class="empty"><b>Nothing new</b>Friend requests and new messages show up here.</div>'}`;
};""",
"""/* (2026-10-13, Tate) like Instagram: what you've already seen stays, under Earlier — the sheet is a feed, not an inbox count */
SHEETS.notifs = () => {
  const reqs = TC.requests, th = TC.threads.filter(t => t.last && t.last.sender !== TC.user.id).sort((a, b) => new Date(b.last.created_at) - new Date(a.last.created_at));
  const msg = t => { const un = isUnread(t); return `<button class="row ntf${un ? ' new' : ''}" data-a="openChatTab" data-x="${t.id}"><span class="sq" style="width:42px;height:42px;background:var(--rose-soft);color:var(--pink-t,#DB2777);border-radius:14px">${ic('msg', 20)}</span><div class="grow" style="min-width:0"><div class="b" style="font-size:15px">${esc(threadName(t))}</div><div class="${un ? '' : 'muted '}b ntf-sub">${esc(msgText(t.last))} · ${agoText(t.last.created_at)}</div></div>${un ? '<span class="ntf-dot" role="img" aria-label="New"></span>' : `<span class="chev">${ic('chevR', 18)}</span>`}</button>`; };
  const fresh = [
    ...reqs.map(id => `<div class="row ntf new">${pav(id, 42, 14)}<div class="grow"><div class="b" style="font-size:15px">${esc(PEOPLE[id].name)} sent you a friend request</div></div><button class="pbtn pink" data-a="acceptReq" data-x="${id}">Accept</button></div>`),
    ...th.filter(isUnread).map(msg)
  ], seen = th.filter(t => !isUnread(t)).slice(0, 30).map(msg);
  const sec = (label, rows) => rows.length ? `<div class="flabel ntf-l">${label}</div>${rows.join('')}` : '';
  return `<div class="row sb"><h3>Notifications</h3><button class="xbtn" data-a="closeSheet">${ic('x', 16, 2.4)}</button></div>
 ${fresh.length && seen.length ? sec('New', fresh) + sec('Earlier', seen) : fresh.length || seen.length ? (fresh.length ? fresh : seen).join('') : '<div class="empty"><b>Nothing new</b>Friend requests and new messages show up here.</div>'}`;
};""")
rep(""".flabel{font-weight:900;font-size:15px}""",
    """.flabel{font-weight:900;font-size:15px}
.ntf{width:100%;padding:12px 0;border-top:1px solid var(--line);text-align:left}
.ntf-l{margin:14px 0 2px}.ntf-l + .ntf{border-top:0}
.ntf-sub{font-size:13px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.ntf-dot{width:9px;height:9px;border-radius:50%;background:var(--pink-t,#DB2777);flex:none;margin:0 8px}""")
p.write_text(s)
print('notifs-stay: applied')
