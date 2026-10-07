#!/usr/bin/env python3
"""Your profile in Tate's D2 look, plus My ratings and Friends as their own pages (Tate, 2026-10-06).

Canvas "Profile Header": now → A/B/C → "i like option C" → C1/C2 with My ratings, Friends and a friend
menu → D1–D4 ("bubbles") → "D2 … looks good" → "implement D2 but make all of these blue".

  · The top is one white card: photo, name, @handle and a round pencil (Edit profile). Under it the
    major and the concentration are solid green bubbles, each labelled (MAJOR, CONCENTRATION), and the
    year sits in a blue bubble beside the concentration (no "YEAR" label). No email, no Settings
    button (the gear stays top right), no "Major and concentration" row (the bubbles say it; the pencil
    edits it).
  · The rows are separate white bubbles with a blue edge and a blue icon, all blue, Friends first, text
    semi-bold: Friends · My ratings · Who sees my schedule · Name on my ratings · Degree Progress Report ·
    N of M requirements filled.
  · My ratings opens its own page (it was a section at the bottom of the profile): counts, then one card
    per review with a rating-coloured edge, the course, stars, Favorite, your words, Anonymous / Friends
    see it's yours, Edit and Delete (the same handlers as before).
  · Friends opens its own page (it was the first 8 friends at the bottom of the profile): search, then
    everyone A–Z; a row opens their page, its ⋯ opens the existing person menu — Remove friend, Report,
    Block. No friend requests here (those stay on the Friends tab).

Nothing new is stored or sent; no SQL.

Re-based 2026-10-06 onto 07:00 (planner-picks): the requirements row opens Schedule › Past classes,
as 07:00 made it.

Usage: python3 profile-d2-2026-10-06.py <repo>
"""
import sys, pathlib, re
root = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else '.')
f = root / 'app' / 'index.html'
s = f.read_text()
if '/* Your profile, Tate\'s D2' in s:
    sys.exit('already patched')

def one(old, new):
    global s
    n = s.count(old)
    assert n == 1, (n, old[:90])
    s = s.replace(old, new)

# ---- CSS -------------------------------------------------------------------------------------------
one(".tc-mval{font-size:14px;font-weight:700;color:var(--muted);max-width:52%;text-align:right;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}\n",
    ".tc-mval{font-size:14px;font-weight:700;color:var(--muted);max-width:52%;text-align:right;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}\n"
    "/* Your profile, Tate's D2 (2026-10-06): one white card on top (photo, name, @handle, pencil; major and\n"
    "   concentration in solid green bubbles, the year in a blue one), then the rows as separate blue-edged\n"
    "   bubbles. Every colour here is a token with a dark twin; text is 4.5:1+ in both themes. */\n"
    ".mepg{--mg-bg:#C6EEE4;--mg-bd:#A7E3D6;--mg-ink:#115E59;--mg-lab:#0F6B63;--ms-bg:#D6E4FF;--ms-bd:#BFD3FF;--ms-ink:#1E40AF;--mr-edge:#BFD3FF;--mr-ic:var(--blue-soft);--mr-ink:var(--blue-ink)}\n"
    ":root[data-theme=\"dark\"] .mepg{--mg-bg:#14403C;--mg-bd:#1F6B62;--mg-ink:#8FE3D8;--mg-lab:#7EDCCF;--ms-bg:#1F3562;--ms-bd:#2C4C8A;--ms-ink:#A9C6FF;--mr-edge:#2C4C8A}\n"
    ".mehd{align-items:center}\n"
    ".mehd-t{font-size:17px;font-weight:900}\n"
    ".mecard{margin:0 12px;padding:16px;border-radius:22px;display:grid;gap:14px}\n"
    ".mehead{display:flex;align-items:center;gap:14px;min-width:0}\n"
    ".mehead .grow{min-width:0}\n"
    ".mename{font-size:24px;font-weight:900;line-height:1.1;overflow-wrap:anywhere}\n"
    ".mehandle{font-size:14px;font-weight:700;color:var(--muted);margin-top:3px;overflow-wrap:anywhere}\n"
    ".meedit{width:44px;height:44px;border-radius:22px;flex:none;display:grid;place-items:center;background:var(--blue-soft);color:var(--blue-t,var(--blue))}\n"
    ".mebubs{display:grid;gap:8px}\n"
    ".mebubs .r2{display:flex;gap:8px;min-width:0}\n"
    ".mebub{display:flex;flex-direction:column;justify-content:center;gap:1px;min-width:0;flex:1 1 auto;padding:8px 14px;border-radius:16px;background:var(--mg-bg);border:1px solid var(--mg-bd);text-align:left;font:inherit;color:inherit}\n"
    ".mebub-l{font-size:11px;font-weight:800;letter-spacing:.06em;color:var(--mg-lab)}\n"
    ".mebub-v{font-size:15px;font-weight:800;line-height:1.25;color:var(--mg-ink);overflow-wrap:anywhere}\n"
    ".mebub.yr{flex:none;background:var(--ms-bg);border-color:var(--ms-bd)}\n"
    ".mebub.yr .mebub-v{color:var(--ms-ink)}\n"
    ".merows{display:grid;gap:10px;margin:12px 12px 0}\n"
    ".merow{display:flex;align-items:center;gap:12px;width:100%;min-height:58px;padding:10px 12px 10px 10px;border-radius:18px;background:var(--card);border-left:5px solid var(--mr-edge);box-shadow:0 2px 10px rgba(15,23,42,.06);color:var(--ink);font:inherit;text-align:left;cursor:pointer}\n"
    ":root[data-theme=\"dark\"] .merow{box-shadow:none}\n"
    ".merow-i{width:38px;height:38px;border-radius:19px;flex:none;display:grid;place-items:center;background:var(--mr-ic);color:var(--mr-ink)}\n"
    ".merow-t{flex:1;min-width:0;display:flex;flex-direction:column}\n"
    ".merow-l{font-size:15.5px;font-weight:600;line-height:1.25}\n"
    ".merow-s{font-size:13px;font-weight:600;color:var(--muted);overflow:hidden;text-overflow:ellipsis;white-space:nowrap}\n"
    ".merow-v{font-size:14px;font-weight:600;color:var(--muted);max-width:46%;text-align:right;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}\n"
    ".merow .chev{color:var(--muted2)}\n"
    "/* My ratings, its own page (2026-10-06): a card per review, set apart by a border, a shadow and a\n"
    "   rating-coloured edge, 14px apart. */\n"
    ".mrstats{display:flex;gap:8px;margin:0 12px 14px}\n"
    ".mrstat{flex:1 1 0;min-width:0;background:var(--card);border-radius:14px;padding:10px 12px;box-shadow:0 1px 2px rgba(15,23,42,.04)}\n"
    ".mrstat b{display:block;font-size:20px;font-weight:900}\n"
    ".mrstat span{font-size:12.5px;font-weight:700;color:var(--muted)}\n"
    "button.mrstat{text-align:left;font:inherit;color:inherit}\n"
    ".mrlist{display:grid;gap:14px;margin:0 12px}\n"
    ".mrlist>.mrcard{background:var(--card);border-radius:18px;border:1px solid var(--line2);border-left:6px solid var(--rs,var(--line2));box-shadow:0 4px 14px rgba(15,23,42,.08);padding:14px 14px 12px}\n"
    ":root[data-theme=\"dark\"] .mrcard{box-shadow:none}\n"
    ".mrcard .tc-revnote{margin:8px 0 0}\n"
    ".mrhd{display:flex;justify-content:space-between;align-items:baseline;gap:8px}\n"
    ".mrname{font-size:16px;font-weight:900;text-align:left;color:var(--ink);font-family:inherit;min-width:0;overflow-wrap:anywhere}\n"
    "button.mrname{min-height:44px}\n"
    ".mrago{font-size:12.5px;font-weight:700;color:var(--muted);white-space:nowrap}\n"
    ".mrfoot{display:flex;align-items:center;gap:8px;border-top:1px solid var(--line);padding-top:10px;margin-top:10px}\n"
    ".mrtag{border-radius:999px;padding:3px 9px;font-size:12px;font-weight:800;background:var(--fill);color:var(--ink4)}\n"
    ".mrtag.on{background:var(--blue-soft);color:var(--blue-ink)}\n"
    ".mrfoot .pbtn,.tb44{min-height:44px}\n"
    "/* Friends, its own page (2026-10-06): everyone A–Z, ⋯ for Remove / Report / Block. */\n"
    ".mfhd{display:flex;align-items:baseline;gap:8px}\n"
    ".mfhd span{font-size:17px;font-weight:800;color:var(--muted)}\n"
    ".mflist{margin:12px 12px 0}\n"
    ".mfrow{display:flex;align-items:center;gap:4px;padding-right:6px}\n"
    ".mfrow+.mfrow{border-top:1px solid var(--line)}\n"
    ".mfmain{flex:1;min-width:0;display:flex;align-items:center;gap:12px;min-height:64px;padding:10px 4px 10px 14px;text-align:left;font:inherit;color:var(--ink)}\n"
    ".mfmain .grow{min-width:0;display:flex;flex-direction:column}\n"
    ".mfmain .b{font-size:15.5px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}\n"
    ".mfmain .muted{font-size:13px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}\n"
    ".mfmore{width:44px;height:44px;border-radius:22px;flex:none;display:grid;place-items:center;color:var(--muted)}\n")

# ---- icons -----------------------------------------------------------------------------------------
one("  camera: '<path d=\"M4 8h3l2-2.5h6L17 8h3v11H4z\"/><circle cx=\"12\" cy=\"13.5\" r=\"3.5\"/>'\n});",
    "  camera: '<path d=\"M4 8h3l2-2.5h6L17 8h3v11H4z\"/><circle cx=\"12\" cy=\"13.5\" r=\"3.5\"/>',\n"
    "  /* your profile's rows (2026-10-06) */\n"
    "  meEye: '<path d=\"M2.5 12s3.5-6.5 9.5-6.5 9.5 6.5 9.5 6.5-3.5 6.5-9.5 6.5S2.5 12 2.5 12z\"/><circle cx=\"12\" cy=\"12\" r=\"3\"/>',\n"
    "  meCard: '<rect x=\"3\" y=\"5\" width=\"18\" height=\"14\" rx=\"3\"/><circle cx=\"9\" cy=\"11\" r=\"2.2\"/><path d=\"M6 16c.6-1.4 1.7-2 3-2s2.4.6 3 2M14 10h4M14 13h3\"/>',\n"
    "  meDoc: '<path d=\"M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8z\"/><path d=\"M14 3v5h5M9 13h6M9 17h4\"/>',\n"
    "  meCheck: '<path d=\"m9 11 3 3 8-8\"/><path d=\"M20 12v7a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h9\"/>',\n"
    "  dots3: '<circle cx=\"5\" cy=\"12\" r=\"1.6\"/><circle cx=\"12\" cy=\"12\" r=\"1.6\"/><circle cx=\"19\" cy=\"12\" r=\"1.6\"/>'\n});")

# ---- screens ---------------------------------------------------------------------------------------
a = s.index('SCREENS.me = () => {')
b = s.index('/* Appearance (dark mode, 2026-10-05)')
assert s.count('SCREENS.me = () => {') == 1 and a < b
NEW = r'''/* Your profile — Tate's D2 (2026-10-06). The degree row is the Planner's own ledger, so it waits for
   the same inputs (A.openMe loads them). */
const meConc = c => String(c || '').replace(/\s+concentration\s*$/i, '').trim();
const meRow = (act, x, icon, label, val, sub) => `<button class="merow" data-a="${act}"${x ? ` data-x="${x}"` : ''}><span class="merow-i">${ic(icon, 20, 2.1)}</span><span class="merow-t"><span class="merow-l">${label}</span>${sub ? `<span class="merow-s">${sub}</span>` : ''}</span>${val !== '' ? `<span class="merow-v">${val}</span>` : ''}<span class="chev">${ic('chevR', 18)}</span></button>`;
SCREENS.me = () => {
  const P = TC.profile || {};
  const revN = (TC.myReviews || []).length, sharedN = (TC.myReviews || []).filter(v => v.share_with_friends).length;
  let deg = '';
  if (window.TCPL && P.major && TC.waived && TC.myHistory) { plSync(); const L = TCPL.ledger(); if (L) deg = meRow('schedTabGo', 'past', 'meCheck', `${L.F} of ${L.N} requirements filled`, '', esc(L.major) + (L.T ? ` · ${L.T} in progress` : '')); }
  const conc = meConc(P.concentration), yr = P.class_standing ? `<div class="mebub yr"><span class="mebub-v">${esc(P.class_standing)}</span></div>` : '';
  const major = P.major ? `<div class="mebub"><span class="mebub-l">MAJOR</span><span class="mebub-v">${esc(P.major)}</span></div>`
    : `<button class="mebub" data-a="openEditProfile"><span class="mebub-l">MAJOR</span><span class="mebub-v">Add your major</span></button>`;
  const bubs = conc ? `${major}<div class="r2"><div class="mebub"><span class="mebub-l">CONCENTRATION</span><span class="mebub-v">${esc(conc)}</span></div>${yr}</div>`
    : (yr ? `<div class="r2">${major}${yr}</div>` : major);
  const rows = [
    meRow('openMyFriends', '', 'users', 'Friends', !TC.ready ? '…' : TC.err.friends && !TC.friends.length ? 'Couldn’t load' : String(TC.friends.length)),
    meRow('openMyRatings', '', 'star', 'My ratings', TC.myReviewsErr ? 'Couldn’t load' : TC.myReviews === undefined ? '…' : `${revN} posted`),
    meRow('openSettings', '', 'meEye', 'Who sees my schedule', 'Friends'),
    meRow('openMyRatings', '', 'meCard', 'Name on my ratings', TC.myReviewsErr ? 'Couldn’t load' : TC.myReviews === undefined ? '…' : sharedN ? `Friends see ${sharedN}` : 'Anonymous'),
    `<label class="merow"><span class="merow-i">${ic('meDoc', 20, 2.1)}</span><span class="merow-t"><span class="merow-l">Degree Progress Report</span></span><span class="merow-v">Import PDF</span><span class="chev">${ic('chevR', 18)}</span><input type="file" accept="application/pdf,.pdf" data-in="dprfile" hidden></label>`,
    deg
  ].join('');
  return {
    body: `<div class="mepg"><div class="topbtns mehd">${backBtn()}<div class="mehd-t">Profile</div><button class="iconbtn" data-a="openSettings" aria-label="Settings">${ic('gear', 21, 2)}</button></div>
 <div class="card mecard"><div class="mehead">${pav('me', 76, 26)}<div class="grow"><div class="mename">${esc(PEOPLE.me.name)}</div>${P.username ? `<div class="mehandle">@${esc(P.username)}</div>` : ''}</div>
  <button class="meedit" data-a="openEditProfile" aria-label="Edit profile">${ic('pencil', 19, 2.3)}</button></div>
  <div class="mebubs">${bubs}</div></div>
 <div class="merows">${rows}</div></div>
 <div class="spacer"></div>`, tabbar: true, fab: false
  };
};

/* My ratings — its own page (2026-10-06). Each review is a card set apart from the next by a border, a
   shadow and an edge in its rating's colour. Edit / Delete are the same handlers the profile used. */
/* One owner for re-reading your reviews: a busy flag (the list itself is never emptied while it runs). */
function myRevLoad() { if (UI.myRevBusy) return; UI.myRevBusy = 1; render(true);
  TC.reloadMyReviews().catch(() => { TC.myReviewsErr = true; }).then(() => { UI.myRevBusy = 0; render(true); }); }
const mrStripe = v => { const st = Math.round(halfOf(v) * 2); return st >= 1 && st <= 10 ? RATE_BRIGHT(st) : ''; };
SCREENS.myRatings = () => {
  const mine = (TC.myReviews || []).slice().sort((a, b) => String(b.created_at).localeCompare(String(a.created_at)));
  const sharedN = mine.filter(v => v.share_with_friends).length, toRate = Array.isArray(TC.myReviews) ? unrated().length : 0;
  const card = v => {
    const nm = esc(v.professor_name || String(v.professor_key || '').split('|')[0]), pk = reviewProfKey(v), rs = mrStripe(v.score);
    return `<div class="tc-rev mrcard"${rs ? ` style="--rs:${rs}"` : ''}><div class="mrhd">${pk ? `<button class="mrname" data-a="openProf" data-x="${esc(pk)}">${nm}</button>` : `<span class="mrname">${nm}</span>`}<span class="mrago">${agoText(v.created_at)}${v.edited_at ? ' · edited' : ''}</span></div>
    <div class="row" style="gap:8px;margin-top:4px;flex-wrap:wrap">${v.course ? `<span class="code" style="font-size:12px;padding:3px 8px">${esc(v.course)}</span>` : ''}${starsTxt(v.score)}${TC.myFavs && TC.myFavs.has(v.professor_key) ? `<span class="favchip">${heartI(13)}Favorite</span>` : ''}</div>
    ${v.note ? `<p class="tc-revnote">${esc(v.note)}</p>` : ''}
    ${v.id ? `<div class="mrfoot"><span class="mrtag${v.share_with_friends ? ' on' : ''}">${v.share_with_friends ? 'Friends see it’s yours' : 'Anonymous'}</span><span class="grow"></span><button class="pbtn" data-a="editReview" data-x="${esc(v.id)}">Edit</button><button class="pbtn tc-danger" data-a="askDeleteReview" data-x="${esc(v.id)}">Delete</button></div>` : ''}</div>`;
  };
  const list = UI.myRevBusy && (TC.myReviewsErr || TC.myReviews === undefined) ? loadingCard('Loading your ratings')
    : TC.myReviewsErr ? errCard('Couldn’t load your ratings', 'reloadMyRatings')
    : TC.myReviews === undefined ? loadingCard('Loading your ratings')
    : mine.length ? `<div class="mrlist">${mine.map(card).join('')}</div>`
    : `<div class="empty"><b>No ratings yet</b>${toRate ? `<a class="link" data-a="tab" data-x="rate" style="color:var(--blue-t,var(--blue))">Rate a professor</a>` : ''}</div>`;
  const stats = TC.myReviews !== undefined && !TC.myReviewsErr && mine.length ? `<div class="mrstats"><div class="mrstat"><b>${mine.length}</b><span>posted</span></div><div class="mrstat"><b>${sharedN}</b><span>friends see it’s you</span></div>${toRate ? `<button class="mrstat" data-a="tab" data-x="rate"><b>${toRate}</b><span>to rate</span></button>` : ''}</div>` : '';
  return {
    body: `<div class="topbtns">${backBtn()}${toRate ? `<button class="pbtn tb44" data-a="tab" data-x="rate">+ Rate</button>` : ''}</div><div class="title" style="margin-top:-6px">My ratings</div>
 ${stats}${list}
 <div class="spacer"></div>`, tabbar: true, fab: false
  };
};

/* Friends — its own page (2026-10-06): everyone A–Z with a search; a row opens their page, its ⋯ the
   person menu (Remove friend, Report, Block). Requests stay on the Friends tab. */
function myFriendRows() {
  const q = String(UI.myfq || '').trim().toLowerCase().replace(/^@/, '');
  const all = TC.friends.filter(id => PEOPLE[id]).sort((a, b) => String(PEOPLE[a].name).localeCompare(String(PEOPLE[b].name)));
  const ids = q ? all.filter(id => String(PEOPLE[id].name || '').toLowerCase().includes(q) || String(PEOPLE[id].handle || '').toLowerCase().includes(q)) : all;
  if (!all.length && (UI.myFrBusy || !TC.ready)) return loadingCard('Loading your friends');
  if (!all.length) return TC.err.friends ? errCard('Couldn’t load your friends', 'reloadMyFriends') : `<div class="empty"><b>No friends yet</b><a class="link" data-a="tab" data-x="friends" style="color:var(--blue-t,var(--blue))">Find friends</a></div>`;
  if (!ids.length) return `<div class="empty"><b>No friends match “${esc(UI.myfq.trim())}”</b></div>`;
  return ids.map(id => { const p = PEOPLE[id]; return `<div class="mfrow"><button class="mfmain" data-a="openFriend" data-x="${esc(id)}">${pav(id, 44, 15)}<span class="grow"><span class="b mfname">${esc(p.name)}</span>${p.major ? `<span class="muted b mfmaj">${esc(p.major)}</span>` : ''}</span></button><button class="mfmore" data-a="personMenu" data-x="${esc(id)}" aria-label="More for ${esc(p.short || p.name)}">${ic('dots3', 22, 2.4, 'currentColor')}</button></div>`; }).join('');
}
SCREENS.myFriends = () => ({
  body: `<div class="topbtns">${backBtn()}<button class="pbtn tb44" data-a="tab" data-x="friends">+ Add</button></div><div class="title mfhd" style="margin-top:-6px">Friends${TC.friends.length ? `<span>${TC.friends.length}</span>` : ''}</div>
 ${TC.friends.length ? `<label class="search"><span style="color:var(--blue-t,var(--blue))">${ic('search', 22, 2.4)}</span><input id="myfq" data-in="myfq" type="search" value="${esc(UI.myfq || '')}" placeholder="Search your friends" aria-label="Search your friends" autocomplete="off" data-1p-ignore data-lpignore="true" data-form-type="other" autocapitalize="off" autocorrect="off" spellcheck="false" enterkeyhint="search"></label>` : ''}
 <div class="card list mflist" id="mflist">${myFriendRows()}</div>
 <div class="spacer"></div>`, tabbar: true, fab: false
});

'''
s = s[:a] + NEW + s[b:]

# ---- actions ---------------------------------------------------------------------------------------
one("  openSettings: () => { TC.loadBlocks().then(() => render(true)); go('settings'); },\n",
    "  openSettings: () => { TC.loadBlocks().then(() => render(true)); go('settings'); },\n"
    "  /* 2026-10-06: My ratings and Friends are their own pages */\n"
    "  openMyRatings: () => { myRevLoad(); if (cur().s !== 'myRatings') go('myRatings'); },\n"
    "  reloadMyRatings: () => { myRevLoad(); },\n"
    "  openMyFriends: () => { UI.myfq = ''; if (cur().s !== 'myFriends') go('myFriends'); },\n"
    "  reloadMyFriends: () => { if (UI.myFrBusy || !TC.user) return; UI.myFrBusy = 1; render(true);\n"
    "    const t0 = TC.loadDone || 0; Promise.resolve(TC.load()).catch(() => {}).then(() => { UI.myFrBusy = 0; render(true); if (TC.err.friends && (TC.loadDone || 0) > t0) toast('Couldn’t load your friends — try again'); }); },\n")

# ---- a failed my_reviews read is a failure, never "none" ---------------------------------------------
one("  TC.myReviews = (!m.error && Array.isArray(m.data)) ? m.data : [];\n  await TC.loadFavs();\n",
    "  /* 2026-10-06: a failed read keeps what was known and says so (My ratings would read \"No ratings yet\") */\n"
    "  if (!m.error && Array.isArray(m.data)) { TC.myReviews = m.data; TC.myReviewsErr = false; } else { if (!Array.isArray(TC.myReviews)) TC.myReviews = []; TC.myReviewsErr = true; }\n"
    "  await TC.loadFavs();\n")
one("TC.reloadMyReviews = async function () {\n  const m = await TC.client().rpc('my_reviews');\n",
    "TC.reloadMyReviews = async function () {\n  let m; try { m = await TC.client().rpc('my_reviews'); } catch (e) { m = { error: { message: 'failed to fetch' } }; }\n")

one("    if (!m.error && Array.isArray(m.data)) { TC.myReviews = m.data; const hit = m.data.find(v => v.professor_key === row.professor_key); id = hit ? hit.id : null; }",
    "    if (!m.error && Array.isArray(m.data)) { TC.myReviews = m.data; TC.myReviewsErr = false; const hit = m.data.find(v => v.professor_key === row.professor_key); id = hit ? hit.id : null; }")

# ---- screen names for GA (names only, as for every screen) ------------------------------------------
one("me: 'Profile', settings: 'Settings',", "me: 'Profile', myRatings: 'My ratings', myFriends: 'My friends', settings: 'Settings',")

# ---- the search box --------------------------------------------------------------------------------
one("  else if (k === 'ngTitle') { if (UI.ng) UI.ng.title = ev.target.value; }\n",
    "  else if (k === 'ngTitle') { if (UI.ng) UI.ng.title = ev.target.value; }\n"
    "  else if (k === 'myfq') { UI.myfq = ev.target.value; const el = document.getElementById('mflist'); if (el) el.innerHTML = myFriendRows(); }\n")
one("document.addEventListener('keydown', ev => { if (ev.key === 'Enter' && ev.target && ev.target.id === 'fq') { ev.preventDefault(); ev.target.blur(); } });",
    "document.addEventListener('keydown', ev => { if (ev.key === 'Enter' && ev.target && (ev.target.id === 'fq' || ev.target.id === 'myfq')) { ev.preventDefault(); ev.target.blur(); } });")

f.write_text(s)
print('patched', f)
