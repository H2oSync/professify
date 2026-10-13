#!/usr/bin/env python3
"""A friend's page looks like your own profile (Tate, 2026-10-08: "lets change friends profiles to look
similar to how the personal profile looks", with screenshots of his D2 profile card and Sage's page).

The top of a friend's page is now the same white card as yours: their photo (with the status ring)
on the left, name and "@handle · status" beside it, and the pin button where your pencil sits. Under
that, MAJOR and CONCENTRATION in the same green bubbles and their year in the blue one (friends only,
as before: a pending request or a stranger shows no major). Then Message, full width, inside the card.
Blocked, request and add-friend states keep their buttons in the same place. The week below is
unchanged.

Usage: python3 friend-profile-like-mine-2026-10-08.py <repo>
"""
import sys, pathlib
root = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else '.')
f = root / 'app' / 'index.html'
s = f.read_text()
if 'friend-profile-like-mine (2026-10-08)' in s:
    sys.exit('already patched')

def one(old, new):
    global s
    n = s.count(old)
    assert n == 1, (n, old[:90])
    s = s.replace(old, new)

# the header: same card as SCREENS.me
old_start = """    body: `<div class="topbtns"><button class="iconbtn" data-a="back" aria-label="Back">${ic('chevL', 22, 2.4)}</button><button class="iconbtn" data-a="personMenu" data-x="${id}" aria-label="More for ${esc(p.short)}: report or block">${ic('dots', 20, 2, 'currentColor')}</button></div>
 <div style="text-align:center;padding:0 16px"><span class="ringav" """
i = s.index(old_start)
j = s.index("</div></div>\n ${bl ? `<div class=\"empty\" style=\"margin-top:20px\"><b>You blocked", i)
old = s[i:j + len("</div></div>\n")]
assert s.count(old) == 1
new = """    body: `<div class="mepg fpg"><div class="topbtns mehd"><button class="iconbtn" data-a="back" aria-label="Back">${ic('chevL', 22, 2.4)}</button><div class="mehd-t">Profile</div><button class="iconbtn" data-a="personMenu" data-x="${id}" aria-label="More for ${esc(p.short)}: report or block">${ic('dots', 20, 2, 'currentColor')}</button></div>
 <div class="card mecard"><div class="mehead"><span class="ringav" style="--rc:${(st && (st.rc || st.c)) || 'transparent'};padding:3px">${pav(id, 72, 25)}</span><div class="grow"><div class="mename">${esc(p.name)}</div>${p.handle ? `<div class="mehandle fhandle">@${esc(p.handle)}</div>` : ''}${st && st.free !== null ? `<div class="mestatus" style="color:${st.c || 'var(--muted)'}">${esc(st.t)}</div>` : ''}</div>${isF && !bl ? pinBtn(id, 'fpin mepin') : ''}</div>
  ${isF && !bl ? friendBubbles(p) : ''}
  <div class="fact">${bl ? `<button class="pbtn" data-a="unblock" data-x="${id}">Unblock</button>` : isF ? `<button class="pbtn pink" data-a="openChatWith" data-x="${id}">Message</button>` : rel === 'incoming' ? `<button class="pbtn pink" data-a="acceptReq" data-x="${id}">Accept request</button>` : `<button class="pbtn ${rel === 'sent' ? 'done' : 'pink'}" data-a="addFriend" data-x="${id}">${rel === 'sent' ? 'Requested' : 'Add friend'}</button>`}</div></div></div>
"""
s = s[:i] + new + s[i + len(old):]

# the bubbles: your profile's, for a friend
one("""function majorBlock(p) {""", """/* A friend's major, concentration and year as your own profile's bubbles (friend-profile-like-mine (2026-10-08)).
   "General / Open" is no concentration; a stored "… concentration" isn't said twice. Nothing set → nothing. */
function friendBubbles(p) {
  const conc = p.conc && p.conc !== 'General / Open' ? meConc(p.conc) : '';
  const yr = p.standing ? `<div class="mebub yr"><span class="mebub-v">${esc(p.standing)}</span></div>` : '';
  const major = p.major ? `<div class="mebub"><span class="mebub-l">MAJOR</span><span class="mebub-v">${esc(p.major)}</span></div>` : '';
  const cb = conc ? `<div class="mebub"><span class="mebub-l">CONCENTRATION</span><span class="mebub-v">${esc(conc)}</span></div>` : '';
  if (!major && !cb && !yr) return '';
  const r2 = cb || yr ? `<div class="r2">${cb}${yr}</div>` : '';
  return `<div class="mebubs fbubs">${major && !cb ? `<div class="r2">${major}${yr}</div>` : major + r2}</div>`;
}
function majorBlock(p) {""")

one(""".merows{display:grid;gap:10px;margin:12px 12px 0}""", """.merows{display:grid;gap:10px;margin:12px 12px 0}
.fpg .mecard{margin-bottom:4px}
.fpg .pinbtn.mepin{width:44px;height:44px;background:var(--blue-soft);color:var(--blue-t,var(--blue));box-shadow:none}
.fpg .pinbtn.mepin.on{background:var(--blue);color:#fff}
.mestatus{font-size:13.5px;font-weight:800;margin-top:2px;line-height:1.3;overflow-wrap:anywhere}
.fact{display:flex}
.fact .pbtn{flex:1;height:46px;border-radius:23px;font-size:15px}""")
# majorBlock (the old centred pill) has no caller left
i = s.index('function majorBlock(p) {'); j = s.index('\n}\n', i) + 3
s = s[:i] + s[j:]
assert 'majorBlock(' not in s
f.write_text(s)
print('patched', f)
