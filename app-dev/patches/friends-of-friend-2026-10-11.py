#!/usr/bin/env python3
"""Who your friends are friends with, on the phone (Tate, 2026-10-11: "lets bring back the feature for the app
that shows who your friends are friends with"). The website has had it since 2026-08-27 (a Friends tab on a
friend's profile); the phone app never did.

- It reads friends_of(p_user) (sql/professify-friends-of.sql, live since 2026-09-02): SECURITY DEFINER, and it
  answers only when you are that person's ACCEPTED friend, so it only ever runs on a friend's page. Nothing
  new in the database.
- A friend's page: under the Major · Concentration · Year strip, one row — their first faces and "Friends with
  Avery, Quinn and 10 more" (your own friends named first, since those are the names that mean something), or
  "12 friends" when you know none of them. Tap → their list. No row while it loads, when they have no other
  friends, or when the function isn't there.
- Their list ("Sage's friends"): "You're both friends with" first (tap to open their page), then everyone else
  with Add / Requested / Accept, the same row as Friends › search. Blocked people and you are never listed. A
  failed read says so with Try again.
- Asked once per friend per session (re-asked when you open their page after 2 minutes, keeping the old list
  on screen meanwhile; a failed re-ask keeps it too and tries again after 15 seconds). 10-second timeout.
- With sql/professify-friends-of-blocks.sql (RUN 16) the list also leaves out anyone who blocked you or whom you
  blocked; until it runs, the app already leaves out people you blocked.

Usage: python3 friends-of-friend-2026-10-11.py <repo>
"""
import sys, pathlib
root = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else '.')
f = root / 'app' / 'index.html'
s = f.read_text()
if 'friends-of-friend (2026-10-11)' in s:
    sys.exit('already patched')

def one(old, new):
    global s
    n = s.count(old)
    assert n == 1, (n, old[:90])
    s = s.replace(old, new)

# 1. the row on a friend's page
one("""  ${isF && !bl ? friendBubbles(p) : ''}""", """  ${isF && !bl ? friendBubbles(p) + fofRow(id) : ''}""")

# 2. loading, the row, the list page
one("""SCREENS.friend = ({ id }) => {""", r'''/* ================= friends-of-friend (2026-10-11) =================
   Who a friend is friends with. friends_of() (sql/professify-friends-of.sql, live) is SECURITY DEFINER and
   answers only to that person's accepted friends; it returns { id, display_name, username, avatar_url, mutual }.
   TC.fof[id] = { ids, at } | { err, at } | 'busy'; TC.fofOff once the function turns out not to exist. */
TC.fof = {}; TC.fofBusy = {};
const FOF_TTL = 120000, FOF_ERR_TTL = 15000;
async function loadFof(id, force) {
  if (!TC.user || !id || TC.fofOff || TC.fofBusy[id]) return;
  const was = TC.fof[id];
  if (!force && was && Date.now() - was.at < (was.err ? FOF_ERR_TTL : FOF_TTL)) return;
  TC.fofBusy[id] = 1;   /* asking again leaves the list you have on screen */
  let r;
  try { r = await Promise.race([TC.client().rpc('friends_of', { p_user: id }), new Promise((_, no) => setTimeout(() => no(new Error('timeout')), 10000))]); }
  catch (e) { r = { error: { message: String((e && e.message) || e) } }; }
  delete TC.fofBusy[id];
  if (r.error && noRpc(r.error)) { TC.fofOff = true; delete TC.fof[id]; }
  else if (r.error) {
    /* a failed read never throws away a good list: keep it, and ask again on the next open after 15 seconds */
    if (was && was.ids) was.at = Date.now() - FOF_TTL + FOF_ERR_TTL; else TC.fof[id] = { err: 1, at: Date.now() };
  } else {
    const me = TC.user.id, ids = [];
    (Array.isArray(r.data) ? r.data : []).forEach(x => {
      if (!x || !x.id || x.id === me || x.id === id || ids.includes(x.id)) return;
      /* someone you're not connected to gets this read's name and photo (a placeholder from a chat is replaced) */
      if (!PEOPLE[x.id] || !TC.relation(x.id)) PEOPLE[x.id] = Object.assign(PEOPLE[x.id] || {}, personFrom({ id: x.id, display_name: x.display_name, username: x.username, avatar_url: x.avatar_url }), { thin: false });
      if (!TC.names[x.id]) TC.names[x.id] = { name: PEOPLE[x.id].name, avatar: PEOPLE[x.id].avatar };
      ids.push(x.id);
    });
    TC.fof[id] = { ids, at: Date.now() };
  }
  const e = cur();
  if (e && e.p && e.p.id === id && (e.s === 'friend' || e.s === 'fof')) render(true);
}
/* their list as it stands now: never someone you blocked; your friends first, A–Z within each */
function fofIds(id) {
  const c = TC.fof[id]; if (!c || !c.ids) return null;
  const by = (a, b) => String(PEOPLE[a].name || '').localeCompare(String(PEOPLE[b].name || ''), undefined, { sensitivity: 'base' });
  const ok = c.ids.filter(x => !isBlocked(x));
  const both = ok.filter(x => TC.relation(x) === 'friends').sort(by);
  const rest = ok.filter(x => TC.relation(x) !== 'friends').sort(by);
  return { both, rest, all: both.concat(rest) };
}
/* "Friends with Avery, Quinn and 10 more" · "Friends with Avery" · "12 friends" (plain: no markup, for aria-label) */
function fofLine(L, plain) {
  const n = L.all.length, nm = x => plain ? PEOPLE[x].short : `<b>${esc(PEOPLE[x].short)}</b>`, names = L.both.slice(0, 2).map(nm), more = n - names.length;
  if (!names.length) return `${n} friend${n === 1 ? '' : 's'}`;
  return `Friends with ${names.join(more ? ', ' : ' and ')}${more ? ` and ${more}${plain ? ' ' : '&nbsp;'}more` : ''}`;
}
function fofRow(id) {
  if (TC.fof[id] === undefined && !TC.fofOff && !TC.fofBusy[id]) setTimeout(() => loadFof(id), 0);
  const L = fofIds(id); if (!L || !L.all.length) return '';
  const lead = L.all.slice(0, 3);
  return `<button class="fofrow" data-a="openFof" data-x="${esc(id)}" aria-label="${esc(fofLine(L, true) + '. See ' + PEOPLE[id].short + '’s friends')}">${avStack(lead, 26)}<span class="grow">${fofLine(L)}</span><span class="chev">${ic('chevR', 16)}</span></button>`;
}
SCREENS.fof = ({ id }) => {
  const p = PEOPLE[id]; if (!p) return missingScreen('Not found.');
  const head = `<div class="topbtns mehd"><button class="iconbtn" data-a="back" aria-label="Back">${ic('chevL', 22, 2.4)}</button><div class="mehd-t">${esc(p.short)}’s friends</div><span style="width:44px"></span></div>`;
  const c = TC.fof[id], L = fofIds(id);
  let body;
  if (!TC.friends.includes(id) || isBlocked(id)) body = `<div class="empty"><b>Only ${esc(p.short)}’s friends can see who they’re friends with</b></div>`;
  else if (L) {
    const bothRow = x => `<button class="li fsr" data-a="openFriend" data-x="${esc(x)}">${pav(x, 46, 16)}<span class="grow fsr-who"><span class="fsr-nm">${esc(PEOPLE[x].name)}</span><span class="muted b fsr-sub">${PEOPLE[x].handle ? '@' + esc(PEOPLE[x].handle) : ''}</span></span><span class="fofst">Friends</span></button>`;
    body = !L.all.length ? `<div class="empty"><b>${esc(p.short)} isn’t friends with anyone else on TermChamp yet</b></div>`
      : `${L.both.length ? `<div class="fs-h">You’re both friends with · ${L.both.length}</div><div class="card list fof-l">${L.both.map(bothRow).join('')}</div>` : ''}
        ${L.rest.length ? `<div class="fs-h">${L.both.length ? 'Others' : 'Their friends'} · ${L.rest.length}</div><div class="card list fof-l">${L.rest.map(fPersonRow).join('')}</div>` : ''}`;
  } else if (TC.fofOff) body = `<div class="empty"><b>Not available yet</b></div>`;
  else if (TC.fofBusy[id] || c === undefined) { if (c === undefined && !TC.fofBusy[id]) setTimeout(() => loadFof(id), 0); body = loadingCard(`Loading ${p.short}’s friends…`); }
  else body = `<div class="empty"><b>Couldn’t load ${esc(p.short)}’s friends.</b><button class="pbtn pink" style="margin-top:10px" data-a="fofRetry">Try again</button></div>`;
  return { body: `<div class="mepg fofpg">${head}${body}</div><div class="spacer"></div>`, tabbar: true, fab: true };
};

SCREENS.friend = ({ id }) => {''')

# 2b. Add / Accept / Requested say whom (here and in Friends › search)
one('''  const btn = rel === 'incoming' ? `<button class="pbtn pink" data-a="acceptReq" data-x="${id}">Accept</button>`
    : `<button class="pbtn ${rel === 'sent' ? 'done' : 'pink'}" data-a="addFriend" data-x="${id}">${rel === 'sent' ? 'Requested' : 'Add'}</button>`;''',
    '''  const btn = rel === 'incoming' ? `<button class="pbtn pink" data-a="acceptReq" data-x="${id}" aria-label="Accept ${esc(p.name)}">Accept</button>`
    : `<button class="pbtn ${rel === 'sent' ? 'done' : 'pink'}" data-a="addFriend" data-x="${id}" aria-label="${rel === 'sent' ? `Requested, ${esc(p.name)}. Tap to cancel` : `Add ${esc(p.name)}`}">${rel === 'sent' ? 'Requested' : 'Add'}</button>`;''')

# 3. actions
one("""  openFriend: id => { UI.champ = false; if (!id) return; if (id === 'me') return setTab('schedule'); if (onPage('friend', id)) { UI.sheet = null; return render(true); } if (TC.user) loadFriendPlans(); go('friend', { id }); },""",
    """  openFriend: id => { UI.champ = false; if (!id) return; if (id === 'me') return setTab('schedule'); if (onPage('friend', id)) { UI.sheet = null; return render(true); } if (TC.user) loadFriendPlans(); if (TC.user && TC.friends.includes(id)) loadFof(id); go('friend', { id }); },
  /* friends-of-friend (2026-10-11) */
  openFof: id => { if (!id) return; if (TC.fof[id] && TC.fof[id].err) loadFof(id, true); go('fof', { id }); },
  fofRetry: () => { const e = cur(); if (e && e.p && e.p.id) { loadFof(e.p.id, true); render(true); } },""")

# 4. styles
one(""".fstrip{display:flex;border-radius:16px;overflow:hidden;background:var(--fs-bg)}""",
    """.fstrip{display:flex;border-radius:16px;overflow:hidden;background:var(--fs-bg)}
/* friends-of-friend (2026-10-11): "Friends with Avery, Quinn and 10 more" under the strip */
.fofrow{display:flex;align-items:center;gap:10px;width:100%;min-height:44px;padding:8px 10px 8px 12px;border-radius:16px;background:var(--fs-bg);color:var(--ink);font-size:13px;font-weight:700;line-height:1.3;text-align:left}
.fofrow .grow{min-width:0}
.fofrow b{font-weight:900}
.fofrow .stack .av{box-shadow:0 0 0 2px var(--fs-bg)}
.fofrow .chev{flex:none;color:var(--muted);display:inline-flex}
.fof-l{margin:0 12px}
.fofpg{--fs-bg:#F1F5F9;--fs-mut:#5B6B80}
:root[data-theme="dark"] .fofpg{--fs-bg:#1B2438;--fs-mut:#9AA6BA}
.fofst{flex:none;font-size:12.5px;font-weight:900;color:var(--fs-mut);padding:6px 10px;border-radius:999px;background:var(--fs-bg)}""")

f.write_text(s)
print('patched', f)
