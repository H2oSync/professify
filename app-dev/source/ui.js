/* =================================================================================================
   THE SCREENS — App 2.0's design, drawn from the real data in the TERMCHAMP BACKEND block above.
   The layout, classes and flow are the designer's. What changed is where every value comes from,
   and what happens when a value doesn't exist: the element says so, or isn't drawn.
   ================================================================================================= */

/* The real clock (the prototype's was fixed at Tuesday 9:41). */
/* In San Luis Obispo's time, not the phone's: classes meet in Pacific time wherever the student
   (or their phone's clock setting) happens to be. */
function slo() {
  try {
    const p = {}; new Intl.DateTimeFormat('en-US', { timeZone: 'America/Los_Angeles', weekday: 'short', hour: 'numeric', minute: 'numeric', hourCycle: 'h23' }).formatToParts(new Date()).forEach(x => { p[x.type] = x.value; });
    return { wd: p.weekday, min: (+p.hour % 24) * 60 + (+p.minute) };
  } catch (e) { const d = new Date(); return { wd: ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'][d.getDay()], min: d.getHours() * 60 + d.getMinutes() }; }
}
const CLOCK = {
  get day() { return { Sun: 'U', Mon: 'M', Tue: 'T', Wed: 'W', Thu: 'R', Fri: 'F', Sat: 'S' }[slo().wd] || 'M'; },
  get min() { return slo().min; }
};
function nowLabel() { return slo().wd + ' ' + hs(CLOCK.min); }

/* Seats. A section's seat count is shown only when the feed gave one. */
function secSeatText(s) {
  if (s.status === 'full') return `<span style="color:var(--pink-ink);font-weight:900">Full</span>`;
  if (s.status === 'wait') return `<span style="color:var(--pink-ink);font-weight:900">Waitlist${s.wl ? ' · ' + s.wl : ''}</span>`;
  if (s.status === 'open' && typeof s.seats === 'number') return `<span style="color:${s.seats <= 5 ? '#B45309' : 'var(--teal)'};font-weight:900">${s.seats} seat${s.seats === 1 ? '' : 's'}</span>`;
  if (s.status === 'open') return `<span style="color:var(--teal);font-weight:900">Open</span>`;
  return `<span class="muted b">Seats unknown</span>`;
}
function courseSeats(code) {
  const ss = secsOf(code); let open = 0, anyOpen = false, known = 0;
  ss.forEach(s => { if (s.status === 'open') { anyOpen = true; if (typeof s.seats === 'number') open += s.seats; } if (s.status !== 'unknown') known++; });
  return { open, anyOpen, allFull: ss.length > 0 && known === ss.length && !anyOpen, unknown: known === 0 };
}
function courseBadge(code) {
  const c = courseSeats(code);
  if (c.anyOpen && c.open > 0) return `<span class="seat" style="background:${c.open <= 5 ? 'var(--amber-soft)' : 'var(--teal-soft)'};color:${c.open <= 5 ? 'var(--amber-ink)' : 'var(--teal)'}">${c.open} seat${c.open === 1 ? '' : 's'}</span>`;
  if (c.anyOpen) return `<span class="seat" style="background:var(--teal-soft);color:var(--teal)">Open</span>`;
  if (c.allFull) return `<span class="seat" style="background:#FCE7F3;color:var(--pink-ink)">Full</span>`;
  return `<span class="seat" style="background:var(--bg);color:var(--muted)">Seats unknown</span>`;
}
function secWhen(s) {
  if (s.async) return 'Online · self-paced';
  if (s.noTime || s.s == null) return 'Time not posted';
  return daysLabel(s.days) + ' ' + range(s);
}
const course = code => COURSES[code] || { title: code, short: code, desc: null, prereq: null };
const profName = pk => pk && PROFS[pk] ? PROFS[pk].name : 'Instructor not assigned';
const ratingOf = pk => (pk && PROFS[pk] && typeof PROFS[pk].r === 'number') ? PROFS[pk].r : null;
const rTxt = pk => { const r = ratingOf(pk); return r == null ? 'No rating' : '★ ' + r.toFixed(1); };

/* A person's picture when they have a real one, their initials when they don't. */
function safeImg(u) { return /^https:\/\//.test(String(u || '')) ? u : ''; }
function pav(id, size = 44, fs) {
  const p = PEOPLE[id] || { ini: '?', color: '#E6EAF1' };
  const src = safeImg(p.avatar);
  if (src) return `<span class="av" style="width:${size}px;height:${size}px;background:${p.color};overflow:hidden"><img src="${esc(src)}" alt="" loading="lazy" referrerpolicy="no-referrer" style="width:100%;height:100%;object-fit:cover" onerror="this.remove()"></span>`;
  return av(p.ini, p.color, size, fs);
}
const profAv = (pk, size, fs) => avL(PROFS[pk] ? PROFS[pk].ini : '?', size, fs);

/* ================= preferences (this phone only — never data) ================= */
const KEY = 'termchamp-app-v1';
function initialState() {
  return {
    tab: 'home', stack: { home: [{ s: 'home' }], explore: [{ s: 'explore' }], rate: [{ s: 'rate' }], schedule: [{ s: 'schedule' }], friends: [{ s: 'friends' }] },
    homeFriend: 'me', homeDay: null,
    exMode: 'classes', q: '', subj: 'All', openOnly: false, savedOnly: false, saved: [], exLimit: 40,
    plan: 'A', schedTab: 'mine', schedDay: null,
    draft: null, lastRated: null,
    friendsFilter: 'all', fq: '', notifSeen: '', champMsgs: []
  };
}
let S = initialState();
try { const raw = JSON.parse(localStorage.getItem(KEY) || 'null'); if (raw) ['exMode', 'subj', 'openOnly', 'saved', 'plan', 'schedTab', 'notifSeen'].forEach(k => { if (raw[k] !== undefined) S[k] = raw[k]; }); } catch (e) {}
S.homeDay = S.schedDay = DAYS.indexOf(CLOCK.day) >= 0 ? CLOCK.day : 'M';
let UI = { sheet: null, champ: false, typing: null, busy: {}, signin: { mode: 'start', email: '', err: '' } };
function save() { try { localStorage.setItem(KEY, JSON.stringify({ exMode: S.exMode, subj: S.subj, openOnly: S.openOnly, saved: S.saved, plan: S.plan, schedTab: S.schedTab, notifSeen: S.notifSeen })); } catch (e) {} }

const cur = () => { const st = S.stack[S.tab]; return st[st.length - 1]; };
function go(s, p) { saveScroll(); S.stack[S.tab].push({ s, p: p || {} }); UI.sheet = null; UI.champ = false; render(); }
function back() { saveScroll(); const st = S.stack[S.tab]; if (st.length > 1) st.pop(); render(); }
function saveScroll() { const e = cur(); if (e) e.y = document.getElementById('scroll').scrollTop; }
function setTab(t) { if (S.tab === t) { S.stack[t] = [S.stack[t][0]]; S.stack[t][0].y = 0; } else saveScroll(); S.tab = t; UI.sheet = null; render(); }

/* ================= derived ================= */
const secsOf = code => SECS_BY_CODE[code] || [];
const personSecs = id => (PEOPLE[id] && PEOPLE[id].secs) || [];
const myCodes = () => new Set(personSecs('me').map(s => s.code).concat(PEOPLE.me.unplaced || []));
function status(id) {
  const today = personSecs(id).filter(s => !s.async && s.s != null && s.days.includes(CLOCK.day)).sort((a, b) => a.s - b.s);
  const now = CLOCK.min;
  if (!personSecs(id).length) return { c: null, t: (PEOPLE[id] && (PEOPLE[id].unplaced || []).length) ? 'Class times not added' : 'No classes added', free: null };
  const inc = today.find(s => s.s <= now && now < s.e);
  if (inc) return { c: '#2563EB', t: `In ${inc.code} till ${hs(inc.e)}`, free: false };
  const nx = today.find(s => s.s > now);
  if (nx && nx.s - now <= 30) return { c: '#F97316', t: `${nx.code} at ${hs(nx.s)}`, free: nx.s - now > 15 };
  if (nx) return { c: '#16A34A', t: `Free till ${hs(nx.s)}`, free: true };
  if (today.length) return { c: '#16A34A', t: 'Done for the day', free: true };
  return { c: null, t: 'No classes today', free: true };
}
const friendsIn = code => TC.friends.filter(f => personSecs(f).some(s => s.code === code) || (PEOPLE[f].unplaced || []).includes(code));
const friendsInSec = id => TC.friends.filter(f => personSecs(f).some(s => s.id === id));
const profCourses = pk => [...new Set(SECTIONS.filter(s => s.prof === pk).map(s => s.code))];
const courseProfs = code => [...new Set(secsOf(code).map(s => s.prof))];
const isSaved = k => S.saved.includes(k);
const avStack = (ids, size = 26) => ids.length ? `<span class="stack">${ids.slice(0, 3).map(f => size < 26 && !safeImg((PEOPLE[f] || {}).avatar) ? av('', (PEOPLE[f] || {}).color || '#E6EAF1', size, size * .36) : pav(f, size, size * .36)).join('')}</span>` : '';
function unrated() { const out = []; TC.rateList.forEach(t => t.items.forEach(([p, c]) => { if (!iReviewed(p)) out.push([p, c, t.term]); })); return out; }
const planSecs = k => TC.plans[k].map(id => SEC[id]).filter(Boolean);
const planMissing = k => TC.plans[k].filter(id => !SEC[id]).length;

/* ================= grid ================= */
function grid(secs, o) {
  const H = o.H || 320, S0 = 360, S1 = 1320, k = H / (S1 - S0);
  const head = `<div class="g-head"><span></span>${DAYS.map(d => `<button class="g-day ${d === o.sel ? 'on' : ''}" data-a="${o.act}" data-x="${d}">${DAYN[d].toUpperCase()}</button>`).join('')}</div>`;
  const labels = [[360, '6a'], [600, '10a'], [840, '2p'], [1080, '6p'], [1320, '10p']].map(([m, l]) => `<span style="top:${(m - S0) * k}px">${l}</span>`).join('');
  const cols = DAYS.map(d => {
    const blocks = secs.filter(s => !s.async && s.s != null && s.days.includes(d)).map(s => {
      const top = Math.max(0, (s.s - S0) * k), h = Math.max((s.e - s.s) * k, o.one ? 30 : 20);
      const two = h >= 28;
      const cls = ['g-b', d === o.sel ? 'sel' : '', o.shared && o.shared.has(s.code) ? 'shared' : '', two ? '' : 'one'].join(' ');
      const [subj, num] = s.code.split(' ');
      return `<button class="${cls}" style="top:${top}px;height:${h}px" data-a="${o.blockAct || 'openClass'}" data-x="${s.code}" data-y="${esc(s.id)}" title="${esc(s.code + ' · ' + course(s.code).title)}">${two ? subj + '<br>' + num : num}</button>`;
    }).join('');
    return `<div class="g-col ${d === o.sel ? 'on' : ''}">${blocks}</div>`;
  }).join('');
  return `<div class="grid">${head}<div class="g-body" style="height:${H}px"><div class="g-lab">${labels}</div>${cols}</div></div>`;
}

/* ================= states the prototype never needed ================= */
function loadingCard(t) { return `<div class="empty"><b>${esc(t)}</b><span class="tc-spin"></span></div>`; }
function errCard(t, act) { return `<div class="empty"><b>${esc(t)}</b>${act ? `<a class="link" data-a="${act}" style="color:var(--blue)">Try again</a>` : ''}</div>`; }
const WEB = CFG.SITE_URL;
const webLink = (label, path) => `<a class="link b" href="${WEB}${path || '/'}" target="_blank" rel="noopener" style="color:var(--blue)">${esc(label)}</a>`;

/* ================= sign in ================= */
function signinView() {
  const si = UI.signin;
  if (TC.phase === 'boot') return `<div class="tc-signin"><img class="tc-logo" src="${LOGO}" alt="Term Champ"><div class="tc-spin big"></div></div>`;
  if (TC.phase === 'offline') return `<div class="tc-signin"><img class="tc-logo" src="${LOGO}" alt="Term Champ"><h1>Can’t reach TermChamp</h1><p>Check your connection, then try again.</p><button class="btn" data-a="reload">Try again</button></div>`;
  if (TC.phase === 'noprofile') return `<div class="tc-signin"><img class="tc-logo" src="${LOGO}" alt="Term Champ"><h1>Finish setting up</h1>
    <p>You’re signed in as <b>${esc((TC.user && TC.user.email) || '')}</b>, but this account hasn’t been set up yet. Pick your school, major and username on termchamp.com, then come back.</p>
    <a class="btn tc-a" href="${WEB}/" target="_blank" rel="noopener">Set up on termchamp.com</a>
    <button class="btn soft" style="margin-top:10px" data-a="reload">I’ve finished — reload</button>
    <button class="btn ghost" style="margin-top:4px" data-a="signOut">Use a different account</button></div>`;
  const err = si.err ? `<div class="tc-err" role="alert">${esc(si.err)}</div>` : '';
  if (si.mode === 'password') return `<div class="tc-signin"><img class="tc-logo" src="${LOGO}" alt="Term Champ"><h1>Sign in</h1>
    <form data-submit="pw" class="tc-form"><label>Email<input id="si-email" type="email" autocomplete="email" required value="${esc(si.email)}"></label>
    <label>Password<input id="si-pw" type="password" autocomplete="current-password" required></label>${err}
    <button class="btn" ${UI.busy.signin ? 'disabled' : ''}>${UI.busy.signin ? 'Signing in…' : 'Sign in'}</button></form>
    <button class="btn ghost" data-a="siMode" data-x="start">Back</button></div>`;
  if (si.mode === 'code') return `<div class="tc-signin"><img class="tc-logo" src="${LOGO}" alt="Term Champ"><h1>Email me a code</h1>
    <form data-submit="sendCode" class="tc-form"><label>Email<input id="si-email" type="email" autocomplete="email" required value="${esc(si.email)}"></label>${err}
    <button class="btn" ${UI.busy.signin ? 'disabled' : ''}>${UI.busy.signin ? 'Sending…' : 'Send code'}</button></form>
    <button class="btn ghost" data-a="siMode" data-x="start">Back</button></div>`;
  if (si.mode === 'verify') return `<div class="tc-signin"><img class="tc-logo" src="${LOGO}" alt="Term Champ"><h1>Check your email</h1>
    <p>We sent a code to <b>${esc(si.email)}</b>.</p>
    <form data-submit="verify" class="tc-form"><label>Code<input id="si-code" inputmode="numeric" autocomplete="one-time-code" required maxlength="10"></label>${err}
    <button class="btn" ${UI.busy.signin ? 'disabled' : ''}>${UI.busy.signin ? 'Checking…' : 'Sign in'}</button></form>
    <button class="btn ghost" data-a="siMode" data-x="code">Send a new code</button></div>`;
  return `<div class="tc-signin"><img class="tc-logo" src="${LOGO}" alt="Term Champ"><img class="tc-champ" src="${CHAMP}" alt="">
    <h1>Your classes, your friends, one app.</h1><p>Sign in with your TermChamp account.</p>${err}
    ${CFG.GOOGLE_SIGNIN_ENABLED ? '<button class="btn" data-a="google" style="margin-bottom:10px">Continue with Google</button>' : ''}
    <button class="btn" data-a="siMode" data-x="password">Sign in with email and password</button>
    <button class="btn ghost" style="margin-top:4px" data-a="siMode" data-x="code">Email me a sign-in code</button>
    <p class="tc-fine">New to TermChamp? ${webLink('Create your account on termchamp.com', '/')} first.</p></div>`;
}

/* ================= screens ================= */
const SCREENS = {};

SCREENS.home = () => {
  const ids = ['me', ...TC.friends];
  const f = ids.indexOf(S.homeFriend) >= 0 ? S.homeFriend : 'me', isMe = f === 'me', P = PEOPLE[f];
  const secs = personSecs(f), mine = myCodes();
  const shared = new Set(isMe ? [] : secs.map(s => s.code).filter(c => mine.has(c)));
  const stories = ids.map(id => { const p = PEOPLE[id], st = status(id); return `<button class="story ${id === f ? 'on' : ''}" data-a="homeFriend" data-x="${id}"><span class="ring" style="--rc:${st.c || 'transparent'}">${safeImg(p.avatar) ? `<span style="background:${p.color};overflow:hidden"><img src="${esc(safeImg(p.avatar))}" alt="" style="width:100%;height:100%;object-fit:cover;border-radius:50%" onerror="this.remove()"></span>` : `<span style="background:${p.color};display:grid;place-items:center;font-weight:900;font-size:17px;color:#0F172A">${esc(p.ini)}</span>`}</span><span class="nm">${esc(id === 'me' ? 'You' : p.short)}</span></button>`; }).join('');
  const sug = TC.suggestions.find(x => !TC.relation(x));
  const where = {}; TC.friends.forEach(fr => [...new Set(personSecs(fr).map(s => s.code).concat(PEOPLE[fr].unplaced || []))].forEach(c => { if (!mine.has(c)) (where[c] = where[c] || new Set()).add(fr); }));
  const whereList = Object.entries(where).map(([c, set]) => [c, [...set]]).sort((a, b) => b[1].length - a[1].length || a[0].localeCompare(b[0])).slice(0, 4);
  const st = isMe ? null : status(f);
  const unplaced = P.unplaced || [];
  const nClasses = secs.length ? new Set(secs.map(s => s.code)).size + unplaced.filter(c => !secs.some(s => s.code === c)).length : unplaced.length;
  const unread = TC.requests.length + TC.threads.filter(isUnread).length;
  const bellKey = TC.requests.join(',') + '|' + TC.threads.filter(isUnread).map(t => t.id + (t.last && t.last.created_at)).join(',');
  let week;
  if (!TC.ready && !TC.mineRows) week = loadingCard('Loading your week…');
  else if (isMe && TC.err.mine) week = errCard('Couldn’t load your classes.', 'refresh');
  else if (!nClasses) week = `<div class="empty"><b>${isMe ? 'No classes yet' : esc(P.short) + ' hasn’t added classes'}</b>${isMe ? `Add your ${esc(CFG.TERM_LABEL)} classes on ${webLink('termchamp.com', '/')} and your week shows up here.` : ''}</div>`;
  else week = grid(secs, { sel: S.homeDay, act: 'homeDay', shared, one: true, H: 300 }) + (unplaced.length ? `<div class="foot">No times yet for ${unplaced.map(esc).join(', ')}</div>` : '');
  return {
    body: `
 <div class="homehdr"><img class="logo" src="${LOGO}" alt="Term Champ"><div class="grow"></div>
  <button class="iconbtn" data-a="sheet" data-x="notifs" aria-label="Notifications">${ic('bell', 22)}${unread && S.notifSeen !== bellKey ? '<span class="dot"></span>' : ''}</button>
  <button class="me-btn" data-a="sheet" data-x="profile" aria-label="Your profile" style="overflow:hidden;padding:0">${safeImg(PEOPLE.me.avatar) ? `<img src="${esc(safeImg(PEOPLE.me.avatar))}" alt="" style="width:100%;height:100%;object-fit:cover" onerror="this.remove()">` : esc(PEOPLE.me.ini)}</button></div>
 <div class="stories">${stories}${TC.friends.length ? '' : `<button class="story" data-a="sheet" data-x="addFriend"><span class="ring" style="--rc:transparent"><span style="background:var(--pink-soft);display:grid;place-items:center;color:var(--pink)">${ic('plus', 22, 2.6)}</span></span><span class="nm">Add</span></button>`}</div>
 <div class="card fcard">
  <button class="top" data-a="${isMe ? 'tab' : 'openFriend'}" data-x="${isMe ? 'schedule' : f}">
   ${pav(f, 50, 17)}
   <div class="grow"><div style="font-weight:900;font-size:18px">${isMe ? 'Your week' : esc(P.name)}</div>
    <span class="pillchip">${isMe ? `${esc(CFG.TERM_LABEL)} · ${nClasses} class${nClasses === 1 ? '' : 'es'}` : `${shared.size} class${shared.size === 1 ? '' : 'es'} with you`}</span>
    ${st && st.free !== null ? `<div style="font-size:12.5px;font-weight:800;color:${st.c || 'var(--muted)'};margin-top:5px">● ${esc(st.t)}</div>` : ''}</div>
   <span class="chev">${ic('chevR', 20)}</span></button>
  ${week}
  ${nClasses && shared.size ? '<div class="foot"><span style="color:#A16207">yellow = shared</span></div>' : ''}
 </div>
 ${sug ? `<div class="mightknow"><div class="mk-t">You might know</div>
  <div class="row">${pav(sug, 52, 17)}<div class="grow"><div style="font-weight:900;font-size:17px">${esc(PEOPLE[sug].name)}</div>
   ${PEOPLE[sug].sub ? `<div class="muted b" style="font-size:13px;margin-top:3px">${esc(PEOPLE[sug].sub)}</div>` : ''}</div>
   <button class="pbtn pink" data-a="addFriend" data-x="${sug}">Add</button></div></div>` : ''}
 ${whereList.length ? `<div class="sec-h">Where your friends are</div>
 <div class="card where" style="margin:0 16px">${whereList.map(([c, fs]) => `<button class="li" data-a="openClass" data-x="${c}"><span class="code">${c}</span><span class="grow b" style="font-size:15px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis">${esc(course(c).short || c)}</span>${avStack(fs, 24)}<span style="font-weight:900;font-size:15px;color:var(--blue-ink);min-width:14px;text-align:right">${fs.length}</span></button>`).join('')}</div>` : ''}
 ${TC.ready && !TC.friends.length ? `<div class="card row" style="margin:14px 16px 0;padding:14px 16px"><span class="sq" style="width:44px;height:44px;background:var(--pink-soft);color:var(--pink)">${ic('users', 22)}</span><div class="grow"><div style="font-weight:900;font-size:15.5px">See your friends’ weeks</div><div class="muted b" style="font-size:13px">Add friends and their classes show up here.</div></div><button class="pbtn pink" data-a="sheet" data-x="addFriend">Add</button></div>` : ''}
 <div class="spacer"></div>`, tabbar: true, fab: true
  };
};

/* ---- Explore ---------------------------------------------------------------------------------- */
function qMatch(hay, q) { return hay.toLowerCase().includes(q) || hay.replace(/\s/g, '').toLowerCase().includes(q.replace(/\s/g, '')); }
function passClass(code) {
  const c = course(code), q = S.q.trim().toLowerCase();
  if (S.savedOnly && !isSaved('c:' + code)) return false;
  if (S.subj !== 'All' && code.split(' ')[0] !== S.subj) return false;
  if (S.openOnly && !courseSeats(code).anyOpen) return false;
  if (q && !(qMatch(code, q) || c.title.toLowerCase().includes(q) || courseProfs(code).some(p => p && profName(p).toLowerCase().includes(q)))) return false;
  return true;
}
function passProf(pk) {
  const p = PROFS[pk], q = S.q.trim().toLowerCase();
  if (!p.teaches) return false;
  if (S.savedOnly && !isSaved('p:' + pk)) return false;
  if (S.subj !== 'All' && !profCourses(pk).some(c => c.split(' ')[0] === S.subj)) return false;
  if (q && !(p.name.toLowerCase().includes(q) || (p.dept || '').toLowerCase().includes(q) || profCourses(pk).some(c => qMatch(c, q)))) return false;
  return true;
}
function classCard(code) {
  const c = course(code), ss = secsOf(code), ps = courseProfs(code).filter(Boolean), fr = friendsIn(code);
  return `<button class="card ccard" data-a="openClass" data-x="${code}">
  <div class="row sb"><span class="code">${code}</span>${courseBadge(code)}</div>
  <div class="ctitle">${esc(c.title)}</div>
  <div class="row sb"><span class="muted b" style="font-size:14.5px">${ss.length} section${ss.length === 1 ? '' : 's'}${ps.length ? ` · ${ps.length} professor${ps.length === 1 ? '' : 's'}` : ''}</span><span class="row" style="gap:6px">${avStack(fr, 24)}<span class="chev">${ic('chevR', 18)}</span></span></div></button>`;
}
function profCard(pk) {
  const p = PROFS[pk], r = ratingOf(pk), st = reviewStats(pk), took = (TC.took && TC.took[pk] || []).map(t => t.uid).filter((u, i, a) => a.indexOf(u) === i && TC.friends.includes(u));
  const line = [p.count ? `${p.count} PolyRatings evaluation${p.count === 1 ? '' : 's'}` : (r == null ? 'Not on PolyRatings' : ''), st && st.again != null ? `${st.again}% would take again` : ''].filter(Boolean).join(' · ');
  return `<button class="card pcard" data-a="openProf" data-x="${esc(pk)}">
  <div class="row">${profAv(pk, 44, 15)}<div class="grow"><div style="font-weight:900;font-size:17px">${esc(p.name)}</div>${p.dept ? `<div class="muted b" style="font-size:13.5px">${esc(p.dept)}</div>` : ''}</div>${r != null ? `<span class="rchip">${starI(13)} ${r.toFixed(1)}</span>` : ''}</div>
  ${line ? `<div class="muted b" style="font-size:13.5px;margin:10px 0">${line}</div>` : '<div style="height:10px"></div>'}
  <div class="row sb"><span class="row" style="gap:6px;flex-wrap:wrap">${profCourses(pk).slice(0, 4).map(c => `<span class="code" style="font-size:12px;padding:4px 8px">${c}</span>`).join('')}</span>${took.length ? `<span class="row" style="gap:6px">${avStack(took, 22)}<span class="muted b" style="font-size:13px">${took.length} took</span></span>` : ''}</div></button>`;
}
function exploreRows() {
  if (S.exMode === 'classes') {
    const fc = c => friendsIn(c).length;
    const l = Object.keys(COURSES).filter(passClass);
    const q = S.q.trim().toLowerCase().replace(/\s/g, '');
    return l.sort((a, b) => (q ? (b.replace(' ', '').toLowerCase().startsWith(q) - a.replace(' ', '').toLowerCase().startsWith(q)) : 0) || fc(b) - fc(a) || a.localeCompare(b, undefined, { numeric: true }));
  }
  return Object.keys(PROFS).filter(passProf).sort((a, b) => ((ratingOf(b) ?? -1) - (ratingOf(a) ?? -1)) || (PROFS[b].count - PROFS[a].count));
}
function exploreList() {
  if (!TC.seatsLoaded) return TC.err.seats ? errCard(`Couldn’t load ${CFG.TERM_LABEL} classes.`, 'retrySeats') : loadingCard(`Loading ${CFG.TERM_LABEL} classes…`);
  const rows = exploreRows();
  if (!rows.length) return emptyEx();
  const shown = rows.slice(0, S.exLimit);
  return shown.map(S.exMode === 'classes' ? classCard : profCard).join('') +
    (rows.length > shown.length ? `<button class="btn soft" style="margin:4px 0 8px" data-a="more">Show more (${rows.length - shown.length} left)</button>` : '') +
    (S.exMode === 'profs' && TC.err.poly ? `<div class="muted b" style="font-size:12.5px;text-align:center;padding:6px 0">PolyRatings didn’t load, so ratings are missing.</div>` : '');
}
function emptyEx() { return S.savedOnly ? `<div class="empty"><b>Nothing saved yet</b>Tap the bookmark on any class or professor to save it here.</div>` : `<div class="empty"><b>No matches</b>Try another search or <a class="link" data-a="clearFilters" style="color:var(--blue)">clear filters</a>.</div>`; }
SCREENS.explore = () => {
  const nf = (S.subj !== 'All' ? 1 : 0) + (S.openOnly ? 1 : 0);
  return {
    body: `<div class="title">Explore</div>
 <label class="search"><span style="color:var(--purple)">${ic('search', 22, 2.4)}</span><input id="exq" data-in="q" value="${esc(S.q)}" placeholder="Search classes or professors" autocomplete="off" enterkeyhint="search">${S.q ? `<button data-a="clearQ" class="chev">${ic('x', 18)}</button>` : ''}</label>
 <div class="pad" style="margin-top:14px"><div class="seg ${S.exMode === 'profs' ? 'purple' : ''}"><button class="${S.exMode === 'classes' ? 'on' : ''}" data-a="exMode" data-x="classes">Classes</button><button class="${S.exMode === 'profs' ? 'on' : ''}" data-a="exMode" data-x="profs">Professors</button></div></div>
 <div class="frow"><button class="fchip" data-a="sheet" data-x="filters">${ic('filter', 18, 2.4)} Filters ${nf ? `<span class="n">${nf}</span>` : ''}</button>
  <div class="row" style="gap:8px">${S.subj !== 'All' ? `<span class="muted b" style="font-size:13px">${esc(S.subj)}</span>` : `<span class="muted b" style="font-size:13px">${esc(CFG.TERM_LABEL)}</span>`}<button class="iconbtn ${S.savedOnly ? 'on' : ''}" data-a="savedOnly" aria-label="Saved">${ic('bm', 20, 2.2, S.savedOnly ? 'currentColor' : 'none')}</button></div></div>
 <div class="pad" id="exlist">${exploreList()}</div><div class="spacer"></div>`, tabbar: true, fab: true
  };
};

SCREENS.classDetail = ({ code }) => {
  if (!COURSES[code]) return missingScreen(TC.seatsLoaded ? `${code} isn’t offered in ${CFG.TERM_LABEL}.` : `Loading ${code}…`);
  const c = course(code), ps = courseProfs(code), fr = friendsIn(code), plan = TC.plans[S.plan], cs = courseSeats(code);
  const order = ps.slice().sort((a, b) => (!a) - (!b) || ((ratingOf(b) ?? -1) - (ratingOf(a) ?? -1)));
  const profBlocks = order.map(pid => {
    const ss = secsOf(code).filter(s => s.prof === pid).sort((a, b) => String(a.sec).localeCompare(String(b.sec), undefined, { numeric: true }));
    const pf = TC.friends.filter(f => ss.some(s => personSecs(f).some(x => x.id === s.id)));
    const head = pid
      ? `<button class="profrow" data-a="openProf" data-x="${esc(pid)}">${profAv(pid, 44, 15)}<div class="grow"><div class="nm">${esc(profName(pid))}</div><div class="row b" style="gap:4px;font-size:14px">${ratingOf(pid) != null ? starI(13, '#D97706') + ratingOf(pid).toFixed(1) + `<span class="muted" style="font-weight:700">&nbsp;· ${PROFS[pid].count} eval${PROFS[pid].count === 1 ? '' : 's'}</span>` : '<span class="muted">Not on PolyRatings</span>'}</div></div>${avStack(pf, 26)}<span style="color:var(--purple)">${ic('chevR', 20)}</span></button>`
      : `<div class="profrow">${avL('?', 44, 15)}<div class="grow"><div class="nm">Instructor not assigned</div><div class="muted b" style="font-size:13px">Listed as Staff for now</div></div>${avStack(pf, 26)}</div>`;
    return `<div class="card" style="margin:0 16px 12px;padding:12px">${head}
   ${ss.map(s => {
      const inP = plan.includes(s.id), w = !!TC.watches[s.id], closed = s.status === 'full' || s.status === 'wait';
      return `<div class="secrow"><span class="t"><b>${s.sec ? '§' + esc(s.sec) + ' ' : ''}${s.async ? 'Online' : s.noTime ? '' : daysLabel(s.days)}</b> ${s.async ? 'self-paced' : s.noTime ? 'Time not posted' : range(s)}</span>${secSeatText(s)}
    ${closed ? `<button class="wl ${w ? 'in' : ''}" data-a="watch" data-x="${esc(s.id)}" aria-label="${w ? 'Stop seat alerts' : 'Alert me when a seat opens'}">${w ? 'Watching' : 'Watch'}</button>` : ''}<button class="addbtn ${inP ? 'in' : ''}" data-a="addSec" data-x="${esc(s.id)}" aria-label="${inP ? 'Remove from' : 'Add to'} Plan ${S.plan}">${ic(inP ? 'check' : 'plus', 20, 2.6)}</button></div>`;
    }).join('')}
  </div>`;
  }).join('');
  const seatsStat = cs.anyOpen ? (cs.open ? cs.open : 'Open') : cs.allFull ? 'Full' : '—';
  const prereq = c.prereq || (TC.catalogLoaded ? 'None listed' : '—');
  return {
    body: `<div class="topbtns"><button class="iconbtn" data-a="back" aria-label="Back">${ic('chevL', 22, 2.4)}</button><button class="iconbtn ${isSaved('c:' + code) ? 'on' : ''}" data-a="save" data-x="c:${code}" aria-label="Save">${ic('bm', 20, 2.2, isSaved('c:' + code) ? 'currentColor' : 'none')}</button></div>
 <div class="hero blue"><div class="row" style="gap:8px;flex-wrap:wrap"><span class="hchip" style="background:#fff;color:var(--blue-ink)">${code}</span><span class="hchip" style="border:1.5px solid rgba(255,255,255,.5)">${esc(CFG.TERM_LABEL)}</span>${myCodes().has(code) ? `<span class="hchip" style="border:1.5px solid rgba(255,255,255,.5)">${ic('check', 14, 3)} Your class</span>` : ''}</div>
  <h1 style="margin-top:12px">${esc(c.title)}</h1>${c.desc ? `<p class="tc-desc">${esc(c.desc)}</p>` : `<p style="opacity:.8">${TC.catalogLoaded ? 'No catalog description on file.' : ''}</p>`}
  <div class="stats"><div class="stat"><small>SECTIONS</small><b>${secsOf(code).length}</b></div><div class="stat"><small>PREREQ</small><b style="font-size:${prereq.length > 9 ? 12 : 16}px;line-height:1.2">${esc(prereq.length > 60 ? prereq.slice(0, 57) + '…' : prereq)}</b></div><div class="stat"><small>OPEN SEATS</small><b>${seatsStat}</b></div></div></div>
 ${fr.length ? `<div class="card row" style="margin:14px 16px 0;padding:12px 14px">${avStack(fr, 30)}<span class="b" style="font-size:14px">${fr.slice(0, 2).map(f => esc(PEOPLE[f].short)).join(', ')}${fr.length > 2 ? ` + ${fr.length - 2} more` : ''} ${fr.length > 1 ? 'are' : 'is'} taking this</span></div>` : ''}
 <div class="sec-h" style="padding-left:18px"><span>Sections</span><span class="planpick">${['A', 'B', 'C'].map(k => `<button class="${S.plan === k ? 'on' : ''}" data-a="pickPlan" data-x="${k}">Plan ${k}</button>`).join('')}</span></div>
 <div class="muted b" style="font-size:13px;padding:0 18px 10px">Tap + to add a section to Plan ${S.plan}${TC.seatsAt ? ` · seats as of ${agoText(new Date(TC.seatsAt).toISOString()) === 'now' ? 'just now' : agoText(new Date(TC.seatsAt).toISOString()) + ' ago'}` : ''}</div>
 ${profBlocks}<div class="spacer"></div>`, tabbar: true, fab: true
  };
};
function missingScreen(t) { return { body: `<div class="topbtns"><button class="iconbtn" data-a="back" aria-label="Back">${ic('chevL', 22, 2.4)}</button></div><div class="empty" style="margin-top:80px"><b>${esc(t)}</b></div>`, tabbar: true, fab: true }; }

SCREENS.profDetail = ({ id }) => {
  const p = PROFS[id]; if (!p) return missingScreen(TC.seatsLoaded ? 'Professor not found.' : 'Loading…');
  if (!p._loadedReviews) { p._loadedReviews = true; TC.loadProfReviews(id); }
  const r = ratingOf(id), st = reviewStats(id), mine = iReviewed(id);
  const took = (TC.took && TC.took[id] || []).filter(t => TC.friends.includes(t.uid));
  const barC = ['#16A34A', '#84CC16', '#EAB308', '#F97316', '#DC2626'];
  const reviews = tcReviewsFor(id).filter(v => v.note);
  const prUrl = p.prId ? 'https://polyratings.dev/professor/' + encodeURIComponent(p.prId) : null;
  return {
    body: `<div class="topbtns"><button class="iconbtn" data-a="back" aria-label="Back">${ic('chevL', 22, 2.4)}</button><button class="iconbtn ${isSaved('p:' + id) ? 'on' : ''}" data-a="save" data-x="p:${esc(id)}" aria-label="Save">${ic('bm', 20, 2.2, isSaved('p:' + id) ? 'currentColor' : 'none')}</button></div>
 <div class="hero purple"><div class="row" style="gap:16px"><span class="av" style="width:70px;height:70px;background:#EDE9FE;color:#3B0764;font-size:22px;box-shadow:0 0 0 3px #fff">${esc(p.ini)}</span><div><h1>${esc(p.name)}</h1>${p.dept ? `<div style="font-weight:800;font-size:15px;margin-top:2px">${esc(p.dept)}</div>` : ''}</div></div>
  <div class="stats"><div class="stat"><small>POLYRATINGS</small><b>${r != null ? '★ ' + r.toFixed(1) : '—'}</b></div><div class="stat"><small>EVALUATIONS</small><b>${p.count || '—'}</b></div><div class="stat"><small>RETAKE</small><b>${st && st.again != null ? st.again + '%' : '—'}</b></div></div>
  <button class="btn" style="background:#fff;color:var(--purple-ink);margin-top:14px;box-shadow:none;height:48px" data-a="rateProf" data-x="${esc(id)}" ${mine ? 'disabled' : ''}><span style="color:#D97706">★</span>&nbsp; ${mine ? 'You’ve reviewed ' + esc(p.name.split(' ')[0]) : 'Rate ' + esc(p.name)}</button></div>
 <div class="card" style="margin:14px 16px 0;padding:18px 16px 12px">
  ${r != null ? `<div class="row" style="gap:18px;align-items:center"><div style="text-align:center;width:80px"><div style="font-size:44px;font-weight:1000;line-height:1">${r.toFixed(1)}</div><div class="muted b" style="font-size:12.5px;margin-top:4px">${p.count} on PolyRatings</div></div>
   <div class="grow muted b" style="font-size:13.5px;line-height:1.45">Overall rating from PolyRatings, Cal Poly’s student-run rating site.${prUrl ? `<br><a class="link" href="${esc(prUrl)}" target="_blank" rel="noopener" style="color:var(--purple)">Read their reviews ›</a>` : ''}</div></div>`
      : `<div class="muted b" style="font-size:14px">${TC.profsLoaded ? 'This professor isn’t on PolyRatings yet.' : TC.err.poly ? 'PolyRatings didn’t load.' : 'Loading PolyRatings…'}</div>`}
  ${st ? `<div style="border-top:1px solid var(--line);margin-top:14px;padding-top:12px"><div class="row sb"><span class="b" style="font-size:14px">TermChamp reviews</span><span class="muted b" style="font-size:13px">${st.n} review${st.n === 1 ? '' : 's'}</span></div>
   ${st.n >= STAT_MIN ? `<div class="bars" style="margin-top:8px">${st.dist.map((v, i) => `<div class="bar">${5 - i}<i><u style="width:${Math.max(v, 2)}%;background:${barC[i]}"></u></i></div>`).join('')}</div>` : ''}
   ${st.diff != null ? `<div class="muted b" style="font-size:13px;margin-top:8px">Difficulty ${st.diff}/5 from ${st.diffN} review${st.diffN === 1 ? '' : 's'}${st.again != null ? ` · ${st.again}% of ${st.againN} would take again` : ''}</div>` : ''}
   ${st.tags.length ? `<div style="margin-top:10px">${st.tags.map(t => `<span class="tag">${esc(t)}</span>`).join('')}</div>` : ''}</div>` : `<div class="muted b" style="font-size:13px;border-top:1px solid var(--line);margin-top:14px;padding-top:12px">No TermChamp reviews yet.${mine ? '' : ' Be the first.'}</div>`}</div>
 ${profCourses(id).length ? `<div class="card" style="margin:14px 16px 0;padding:16px"><div style="font-weight:900;font-size:17px">Teaching ${esc(CFG.TERM_LABEL)}</div>
  ${profCourses(id).map(c => { const n = SECTIONS.filter(s => s.prof === id && s.code === c).length; return `<button class="teach" data-a="openClass" data-x="${c}"><span class="code">${c}</span><span class="grow b" style="font-size:15px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis">${esc(course(c).short)}</span><span class="muted b" style="font-size:13px">${n} sec</span><span class="chev">${ic('chevR', 18)}</span></button>`; }).join('')}</div>` : ''}
 ${took.length ? `<div class="card" style="margin:14px 16px 0;padding:16px"><div class="row sb"><span style="font-weight:900;font-size:17px">Friends who took this professor</span><span class="muted b">${new Set(took.map(t => t.uid)).size}</span></div>
  ${took.slice(0, 8).map(t => `<button class="row" style="width:100%;padding:10px 0 2px" data-a="openFriend" data-x="${t.uid}">${pav(t.uid, 38, 13)}<div class="grow"><div class="b" style="font-size:15px">${esc(PEOPLE[t.uid].name)}</div><div class="muted b" style="font-size:13px">${t.code}${t.when ? ' · ' + esc(t.when) : ''}</div></div><span class="chev">${ic('chevR', 18)}</span></button>`).join('')}</div>` : ''}
 ${reviews.length ? `<div class="card" style="margin:14px 16px 0;padding:6px 16px"><div class="row sb" style="padding:12px 0 4px"><span style="font-weight:900;font-size:17px">What students wrote</span><span class="muted b" style="font-size:13px">${reviews.length}</span></div>
  ${reviews.slice(0, 20).map(v => { const s = Math.max(0, Math.min(5, Math.round(v.score || 0))); return `<div class="review"><div class="row sb"><span class="row" style="gap:8px">${v.course ? `<span class="code" style="font-size:12px;padding:4px 8px">${esc(v.course)}</span>` : ''}<span style="color:#F59E0B;letter-spacing:1px">${'★'.repeat(s)}<span style="color:#E2E8F0">${'★'.repeat(5 - s)}</span></span>${v._mine ? '<span class="mine">You</span>' : ''}</span><span class="muted b" style="font-size:13px">${agoText(v.created_at)}</span></div><p>${esc(v.note)}</p></div>`; }).join('')}</div>` : ''}
 <div class="spacer"></div>`, tabbar: true, fab: true
  };
};

/* ---- Rate ------------------------------------------------------------------------------------- */
SCREENS.rate = () => {
  const left = unrated().length;
  const list = TC.rateList;
  return {
    body: `<div class="title">Rate</div>
 <div class="muted b" style="padding:0 20px;font-size:14px;margin-top:-6px">${!TC.ready ? 'Loading your professors…' : !list.length ? '' : left ? `${left} professor${left > 1 ? 's' : ''} waiting on your rating` : 'All caught up. Thanks for helping other students pick classes!'}</div>
 ${TC.ready && !list.length ? `<div class="empty"><b>No professors to rate yet</b>Your professors show up here from your ${esc(CFG.TERM_LABEL)} classes and your past classes. Add past classes on ${webLink('termchamp.com', '/')}.</div>` : ''}
 ${list.map(t => `<div class="term">${esc(t.term)}${t.current ? '<span class="curterm">Current term</span>' : ''}</div>
  <div class="card list" style="margin:0 16px">${t.items.map(([pid, code]) => { const p = PROFS[pid], r = iReviewed(pid); return `<button class="li" data-a="rateProf" data-x="${esc(pid)}" data-y="${code}">${profAv(pid, 46, 16)}<div class="grow"><div style="font-weight:900;font-size:16.5px">${esc(p.name)}</div><div class="muted b" style="font-size:14px">${code}</div></div>${r ? `<span class="rscore">${starI(17, '#F59E0B')} ${(+r.score).toFixed(1)}</span>` : '<span class="pbtn">Rate</span>'}</button>`; }).join('')}</div>`).join('')}
 <div class="spacer"></div>`, tabbar: true, fab: true
  };
};

const GRADES = ['A', 'A-', 'B+', 'B', 'B-', 'C+', 'C', 'C-', 'D', 'F', 'P/CR'];
SCREENS.rateForm = () => {
  const d = S.draft, p = PROFS[d.prof];
  const sg = (key, vals, labels, wrap) => `<div class="sg${wrap ? ' tc-wrap' : ''}">${vals.map((v, i) => `<button class="${d[key] === v ? 'on' : ''}" data-a="draft" data-x="${key}" data-y="${esc(v)}">${labels ? labels[i] : esc(v)}</button>`).join('')}</div>`;
  const codes = d.codes || [];
  return {
    dark: true, body: `<div class="rf"><div class="rf-sheet"><div class="grab" style="margin-top:0"></div>
  <div class="rf-head">${profAv(d.prof, 48, 16)}<div class="grow"><div class="eyebrow">RATE A PROFESSOR</div><div style="font-size:24px;font-weight:900;line-height:1.15">${esc(p.name)}</div></div><button class="xbtn" data-a="back" aria-label="Cancel">${ic('x', 18, 2.4)}</button></div>
  <div class="fcardx">
   <div class="frow2">${codes.length > 1 ? `<div class="flabel" style="margin-bottom:10px">Class</div>${sg('code', codes, null, true)}` : `<div class="row sb"><span class="flabel">Class</span><span class="b" style="color:var(--ink3)">${esc(d.code || '')}${d.term ? ' · ' + esc(d.term) : ''}</span></div>`}</div>
   <div class="frow2 row sb"><span class="flabel">Overall<div class="hint" style="margin-top:2px">${d.stars ? STARLBL[d.stars] : 'Tap to rate'}</div></span><span class="stars">${[1, 2, 3, 4, 5].map(k => `<button data-a="draft" data-x="stars" data-y="${k}" aria-label="${k} stars">${starI(28, k <= d.stars ? SC[d.stars] : '#E6EAF1')}</button>`).join('')}</span></div>
   <div class="frow2"><div class="row sb" style="margin-bottom:10px"><span class="flabel">Difficulty</span><span class="hint">${['', 'Very easy', 'Pretty easy', 'Moderate', 'Hard', 'Very hard'][d.diff] || ''}</span></div>${sg('diff', [1, 2, 3, 4, 5])}<div class="row sb hint" style="margin-top:8px;padding:0 6px"><span>Easy</span><span>Hard</span></div></div>
   <div class="frow2 row sb"><span class="flabel">Take again?</span><div style="width:190px">${sg('again', ['yes', 'no'], ['Yes', 'No'])}</div></div>
   <div class="frow2 row sb"><button class="b" style="color:var(--blue);font-size:17px;font-weight:900" data-a="draftMore">${d.more ? '− Hide detail' : '+ Add detail'}</button><span class="hint" style="font-size:14px">Optional</span></div>
   ${d.more ? `
   <div class="frow2"><div class="row sb" style="margin-bottom:10px"><span class="flabel">Your grade</span><span class="hint">Never shown with your name</span></div>${sg('grade', GRADES, null, true)}</div>
   <div class="frow2"><div class="flabel" style="margin-bottom:10px">Format</div>${sg('format', ['In person', 'Hybrid', 'Online'])}</div>
   <div class="frow2"><div class="row sb"><span class="flabel">Review</span><span class="hint" id="revcount">${wordCount(d.review)}/300 words</span></div><textarea class="ta" id="revta" data-in="review" placeholder="What should other students know? Workload, exams, tips…">${esc(d.review || '')}</textarea></div>` : ''}
   ${d.err ? `<div class="frow2"><div class="tc-err" role="alert">${esc(d.err)}</div></div>` : ''}
  </div></div></div>`,
    bot: `<div class="bottombar"><button class="btn" data-a="postRating" ${d.stars && d.code && !UI.busy.rate ? '' : 'disabled'}>${UI.busy.rate ? 'Posting…' : !d.code ? 'Pick the class' : d.stars ? 'Post rating' : 'Tap a star to rate'}</button></div>`, tabbar: false, fab: false
  };
};
function wordCount(t) { return String(t || '').trim().split(/\s+/).filter(Boolean).length; }

SCREENS.rateThanks = () => {
  const d = S.lastRated; if (!d) return missingScreen('');
  const p = PROFS[d.prof];
  const kv = [['DIFFICULTY', d.diff ? d.diff + ' / 5' : '—'], ['TAKE AGAIN', d.again ? (d.again === 'yes' ? 'Yes' : 'No') : '—'], ...(d.format ? [['FORMAT', d.format]] : [])];
  const sf = !!d.share;
  return {
    dark: true, body: `<div class="rf"><div class="rf-sheet" style="padding-bottom:40px"><div class="grab" style="margin-top:0"></div>
  <div class="okcircle">${ic('check', 32, 3)}</div>
  <div style="text-align:center;font-size:26px;font-weight:900">Thanks for your review!</div>
  <p class="muted b" style="text-align:center;font-size:15.5px;line-height:1.45;margin:8px 20px 18px">Your rating of ${esc(p.name)} helps other students pick the right classes.</p>
  <div class="fcardx" style="padding:16px">
   <div class="row">${profAv(d.prof, 40, 14)}<div class="grow"><div style="font-weight:900;font-size:16px">${esc(p.name)}</div><div class="muted b" style="font-size:13.5px">${esc(d.code)}${d.term ? ' · ' + esc(d.term) : ''}</div></div><span class="row" style="gap:2px">${[1, 2, 3, 4, 5].map(i => starI(15, i <= d.stars ? SC[d.stars] : '#E6EAF1')).join('')}</span></div>
   <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:8px;margin-top:14px">${kv.map(([a, b]) => `<div class="kv"><small>${a}</small><b>${esc(b)}</b></div>`).join('')}</div>
   ${d.review ? `<p style="font-size:15px;font-weight:600;color:var(--ink3);line-height:1.45;margin-top:12px">“${esc(d.review)}”</p>` : ''}</div>
  ${d.reviewId ? `<div class="fcardx" style="margin-top:12px"><div class="row" style="padding:14px 16px;gap:12px"><div class="grow"><div style="font-weight:900;font-size:15px">Show friends it was my review</div><div class="muted b" style="font-size:13px">${sf ? 'Your friends see your name on it' : 'Off — friends see it as anonymous too'}</div></div><button class="toggle ${sf ? 'on' : 'off'}" data-a="toggleShow" aria-label="Show friends"><i></i></button></div>
   <div class="row muted b" style="gap:8px;padding:10px 16px 12px;border-top:1px solid var(--line);font-size:13.5px">${ic('lock', 16)} Anonymous to everyone else</div></div>`
      : `<div class="row muted b" style="gap:8px;padding:12px 4px;font-size:13.5px">${ic('lock', 16)} Posted anonymously</div>`}
  <button class="btn" style="margin-top:18px" data-a="rateDone">Done</button>
  ${unrated().length ? `<button class="btn ghost" style="margin-top:6px" data-a="rateAnother">Rate another professor</button>` : ''}
 </div></div>`, tabbar: false, fab: false
  };
};

/* ---- Schedule --------------------------------------------------------------------------------- */
SCREENS.schedule = () => {
  const t = S.schedTab;
  let inner = '';
  if (t === 'plans') {
    const secs = planSecs(S.plan), timed = secs.filter(s => !s.async && s.s != null), any = secs.filter(s => s.async || s.s == null), miss = planMissing(S.plan);
    const days = DAYS.map(d => [d, timed.filter(s => s.days.includes(d)).sort((a, b) => a.s - b.s)]).filter(x => x[1].length);
    inner = `<div class="pad" style="margin-top:14px"><div class="seg">${['A', 'B', 'C'].map(k => `<button class="${S.plan === k ? 'on' : ''}" data-a="pickPlan" data-x="${k}">Plan ${k}</button>`).join('')}</div></div>
  <div class="regbar"><span>${secs.length} class${secs.length === 1 ? '' : 'es'}</span><span class="regbadge" style="background:var(--bg);color:var(--muted)">${TC.planShared[S.plan] !== false ? 'Friends can see' : 'Only you'}</span></div>
  ${TC.err.plans ? `<div class="muted b" style="font-size:13px;padding:6px 18px">${TC.err.plans === 'missing' ? 'Plans aren’t set up on this server yet.' : 'Couldn’t load your plans — changes may not save.'}</div>` : ''}
  ${miss ? `<div class="muted b" style="font-size:13px;padding:6px 18px">${miss} section${miss === 1 ? ' in this plan is' : 's in this plan are'} no longer in the ${esc(CFG.TERM_LABEL)} list.</div>` : ''}
  <div class="card" style="margin:10px 16px 0;padding:14px 0 12px">${!TC.seatsLoaded ? loadingCard('Loading sections…') : timed.length ? grid(timed, { sel: S.schedDay, act: 'schedDay', blockAct: 'secSheet', H: 330 }) : '<div class="empty"><b>No timed classes</b>Add classes from Explore.</div>'}</div>
  ${any.length ? `<div class="card anytime"><span style="font-weight:900;font-size:16px;margin-right:4px">No set time</span>${any.map(s => `<button class="code" style="font-size:14px;padding:7px 12px" data-a="secSheet" data-x="${s.code}" data-y="${esc(s.id)}">${s.code}</button>`).join('')}</div>` : ''}
  ${days.map(([d, list]) => `<div class="card agenda"><h4>${DAYL[d]}${d === CLOCK.day ? '<span class="today">Today</span>' : ''}</h4>
   ${list.map(s => { const fr = friendsInSec(s.id); return `<button class="arow" data-a="secSheet" data-x="${s.code}" data-y="${esc(s.id)}"><span class="tm">${hs(s.s)}<small>${hs(s.e)}</small></span><span class="vb"></span><span class="grow"><span style="font-weight:900;font-size:16px">${s.code}</span><span class="muted b" style="display:block;font-size:14px">${esc(profName(s.prof))} · ${secSeatText(s)}</span></span>${avStack(fr, 26)}</button>`; }).join('')}</div>`).join('')}
  <div class="pad" style="margin-top:14px"><button class="btn soft" data-a="tab" data-x="explore">+ Add a class from Explore</button></div>
  <div class="muted b" style="font-size:12.5px;padding:12px 20px 0;line-height:1.45">Plans use ${esc(CFG.TERM_LABEL)} sections. Once the ${esc(CFG.REGISTRATION_TERM)} schedule is posted, plan with those. Sections in a plan get seat alerts.</div>`;
  } else if (t === 'mine') {
    const secs = personSecs('me'), unplaced = PEOPLE.me.unplaced || [];
    const byCode = {}; secs.forEach(s => { (byCode[s.code] = byCode[s.code] || []).push(s); });
    inner = `<div class="regbar" style="margin-top:14px"><span>${esc(CFG.TERM_LABEL)}</span><span class="regbadge">${Object.keys(byCode).length + unplaced.length} classes</span></div>
  ${TC.err.mine ? errCard('Couldn’t load your classes.', 'refresh') : !TC.mineRows ? loadingCard('Loading your classes…') : ''}
  ${TC.mineRows && !secs.length && !unplaced.length ? `<div class="empty"><b>No classes yet</b>Import your ${esc(CFG.TERM_LABEL)} schedule on ${webLink('termchamp.com', '/')} and it shows up here.</div>` : ''}
  ${secs.length ? `<div class="card" style="margin:10px 16px 0;padding:14px 0 12px">${grid(secs, { sel: S.schedDay, act: 'schedDay', blockAct: 'secSheet', H: 330 })}</div>` : ''}
  ${Object.keys(byCode).map(code => { const ss = byCode[code], c = course(code), fr = TC.friends.filter(f => personSecs(f).some(x => ss.some(s => s.id === x.id))); return `<button class="card ccard" style="margin:12px 16px 0;width:calc(100% - 32px)" data-a="openClass" data-x="${code}">
   <div class="row sb"><span class="code">${code}</span>${ss[0].sec ? `<span class="muted b" style="font-size:13px">§${esc(ss[0].sec)}</span>` : ''}</div>
   <div class="ctitle" style="margin:8px 0 4px">${esc(c.title)}</div>
   ${ss.map(s => `<div class="muted b" style="font-size:14px">${esc(profName(s.prof))} · ${secWhen(s)}</div>`).join('')}
   ${fr.length ? `<div class="row" style="gap:8px;margin-top:10px">${avStack(fr, 24)}<span class="b" style="font-size:13px;color:var(--ink3)">${fr.map(f => esc(PEOPLE[f].short)).slice(0, 3).join(', ')} in your section</span></div>` : ''}</button>`; }).join('')}
  ${unplaced.map(code => `<button class="card ccard" style="margin:12px 16px 0;width:calc(100% - 32px)" data-a="openClass" data-x="${code}"><div class="row sb"><span class="code">${code}</span><span class="muted b" style="font-size:13px">No section yet</span></div><div class="ctitle" style="margin:8px 0 0">${esc(course(code).title)}</div></button>`).join('')}`;
  } else {
    inner = `<div class="card" style="margin:14px 16px 0;padding:18px 16px"><div class="row" style="gap:12px"><span class="sq" style="width:44px;height:44px;background:var(--teal-soft);color:var(--teal)">${ic('grad', 24)}</span><div class="grow"><div style="font-weight:900;font-size:17px">Your degree planner</div><div class="muted b" style="font-size:13.5px">Requirements, GEs and past classes</div></div></div>
   <p class="muted b" style="font-size:14px;line-height:1.5;margin:12px 0 14px">The full Planner — what your major still needs, your GE areas and the classes you’ve already taken — lives on termchamp.com for now. It’s coming to the phone app next.</p>
   <a class="btn tc-a" href="${WEB}/" target="_blank" rel="noopener">Open the Planner on termchamp.com</a></div>`;
  }
  return {
    body: `<div class="title">Schedule</div>
 <div class="stabs">${[['mine', 'My Classes'], ['plans', 'Plans'], ['planner', 'Planner']].map(([k, l]) => `<button class="${t === k ? 'on' : ''}" data-a="schedTab" data-x="${k}">${l}</button>`).join('')}</div>
 ${inner}<div class="spacer"></div>`, tabbar: true, fab: true
  };
};

/* ---- Friends & chats -------------------------------------------------------------------------- */
function threadName(t) {
  if (t.kind === 'direct') { const o = threadOther(t); return o ? nameOf(o) : 'Chat'; }
  if (t.title) return t.title;
  return t.members.filter(u => u !== TC.user.id).map(u => nameOf(u).split(' ')[0]).slice(0, 3).join(', ') || 'Group';
}
function msgText(m) {
  if (!m) return '';
  if (m.body) return m.body;
  if (m.kind && m.kind !== 'text') return 'Shared ' + String(m.kind).replace(/_/g, ' ');
  return '';
}
function threadRow(t) {
  const last = t.last, unread = isUnread(t);
  let avh;
  if (t.kind === 'direct') { const o = threadOther(t); if (o && !PEOPLE[o]) PEOPLE[o] = Object.assign(personFrom({ id: o, display_name: nameOf(o), avatar_url: (TC.names[o] || {}).avatar }), {}); avh = `<span class="ringav" style="--rc:${o && TC.friends.includes(o) ? status(o).c || 'transparent' : 'transparent'}">${o ? pav(o, 48, 16) : av('?', '#E6EAF1', 48, 16)}</span>`; }
  else { const nm = threadName(t); avh = `<span class="ringav"><span class="sq" style="width:48px;height:48px;background:${t.kind === 'class' ? '#D6E4FF' : colorFor(t.id)};color:${t.kind === 'class' ? 'var(--blue-ink)' : 'var(--ink2)'};font-size:${t.kind === 'class' ? 13 : 16}px">${esc(t.kind === 'class' ? (nm.split(' ')[1] || nm).slice(0, 5) : initialsOf(nm))}</span></span>`; }
  const who = last ? (last.sender === TC.user.id ? 'You: ' : (t.kind !== 'direct' ? nameOf(last.sender).split(' ')[0] + ': ' : '')) : '';
  return `<button class="thread" data-a="openChat" data-x="${t.id}">${avh}<div class="grow"><div class="nm">${esc(threadName(t))}</div><div class="pv ${unread ? '' : 'read'}">${esc(last ? who + msgText(last) : 'No messages yet')}</div></div><div class="tm">${last ? agoText(last.created_at) : ''}${unread ? '<span class="udot"></span>' : '<span style="height:10px"></span>'}</div></button>`;
}
function friendsList() {
  const q = S.fq.trim().toLowerCase(), F = S.friendsFilter;
  if (F === 'requests') {
    return TC.requests.length ? `<div class="card list" style="margin:0 16px">${TC.requests.map(id => `<div class="li">${pav(id, 46, 16)}<div class="grow"><div style="font-weight:900;font-size:16px">${esc(PEOPLE[id].name)}</div><div class="muted b" style="font-size:13.5px">${PEOPLE[id].handle ? '@' + esc(PEOPLE[id].handle) : 'Wants to be friends'}</div></div><button class="pbtn pink" data-a="acceptReq" data-x="${id}">Accept</button><button class="xbtn" data-a="declineReq" data-x="${id}" aria-label="Decline">${ic('x', 16, 2.4)}</button></div>`).join('')}</div>` : `<div class="empty"><b>No requests</b>You’re all caught up.</div>`;
  }
  if (F === 'people') {
    const l = TC.friends.filter(id => !q || PEOPLE[id].name.toLowerCase().includes(q) || (PEOPLE[id].handle || '').toLowerCase().includes(q));
    return l.length ? `<div class="card list" style="margin:0 16px">${l.map(id => { const st = status(id); return `<button class="li" data-a="openFriend" data-x="${id}">${pav(id, 46, 16)}<div class="grow"><div style="font-weight:900;font-size:16px">${esc(PEOPLE[id].name)}</div><div class="b" style="font-size:13px;color:${st.c || 'var(--muted)'}">${st.free === null ? esc(st.t) : '● ' + esc(st.t)}</div></div><span class="chev">${ic('chevR', 18)}</span></button>`; }).join('')}</div>` : `<div class="empty"><b>${TC.friends.length ? 'No one by that name' : 'No friends yet'}</b>${TC.friends.length ? '' : 'Tap + to find classmates.'}</div>`;
  }
  if (TC.err.threads && !TC.threads.length) return errCard('Couldn’t load your chats.', 'refresh');
  let ts = TC.threads.filter(t => F === 'all' || (F === 'groups' && t.kind === 'group') || (F === 'class' && t.kind === 'class'));
  if (q) ts = ts.filter(t => threadName(t).toLowerCase().includes(q) || (t.last && msgText(t.last).toLowerCase().includes(q)));
  if (!TC.ready && !ts.length) return loadingCard('Loading chats…');
  return ts.length ? `<div class="card" style="margin:0 16px;padding:2px 0">${ts.map(threadRow).join('')}</div>` : `<div class="empty"><b>${q ? 'No chats found' : 'No chats yet'}</b>${q ? 'Try a different name.' : TC.friends.length ? 'Open a friend and tap Message.' : ''}</div>`;
}
SCREENS.friends = () => {
  const F = S.friendsFilter, sug = TC.suggestions.filter(id => TC.relation(id) !== 'friends');
  return {
    body: `<div class="fhdr"><div class="title">Friends</div><button class="plusbtn" data-a="sheet" data-x="addFriend" aria-label="Add friend">${ic('plus', 24, 2.6)}</button></div>
 <label class="search"><span style="color:var(--pink)">${ic('search', 22, 2.4)}</span><input id="fq" data-in="fq" value="${esc(S.fq)}" placeholder="Search friends & chats" autocomplete="off"></label>
 <div class="chips">${[['all', 'Chats'], ['people', 'Friends'], ['groups', 'Groups'], ['class', 'Class chats'], ['requests', 'Requests']].map(([k, l]) => `<button class="chip ${F === k ? 'on' : ''}" data-a="fFilter" data-x="${k}">${l}${k === 'requests' && TC.requests.length ? `<span class="n">${TC.requests.length}</span>` : k === 'people' && TC.friends.length ? `<span class="n" style="background:var(--muted2)">${TC.friends.length}</span>` : ''}</button>`).join('')}</div>
 <div id="flist">${friendsList()}</div>
 ${F === 'all' && sug.length ? `<div class="sec-h" style="padding-left:20px"><span>People you might know</span><a data-a="sheet" data-x="addFriend">See all</a></div>
 <div class="hscroll">${sug.map(id => { const p = PEOPLE[id], rq = TC.relation(id) === 'sent'; return `<div class="card pym"><div style="display:flex;justify-content:center">${pav(id, 56, 18)}</div><div class="nm">${esc(p.name)}</div><div class="sub">${esc(p.sub || '')}</div><button class="pbtn ${rq ? 'done' : 'pink'}" data-a="addFriend" data-x="${id}">${rq ? 'Requested' : 'Add'}</button></div>`; }).join('')}</div>` : ''}
 ${F === 'all' ? `<div class="card row" style="margin:14px 16px 0;padding:14px 16px"><span class="sq" style="width:44px;height:44px;background:var(--pink-soft);color:var(--pink)">${ic('link', 22)}</span><div class="grow"><div style="font-weight:900;font-size:15.5px">Invite friends</div><div class="muted b" style="font-size:13px">Send them a link to TermChamp</div></div><button class="pbtn pink" data-a="copyInvite">Share</button></div>` : ''}
 <div class="spacer"></div>`, tabbar: true, fab: true
  };
};

SCREENS.chat = ({ id }) => {
  const t = TC.threads.find(x => x.id === id);
  if (!t) return missingScreen('Chat not found.');
  const rows = TC.rows[id];
  let head;
  if (t.kind === 'direct') { const o = threadOther(t), st = o && TC.friends.includes(o) ? status(o) : null; head = `${o ? pav(o, 40, 14) : ''}<button class="grow" style="text-align:left" data-a="openFriend" data-x="${o || ''}"><div style="font-weight:900;font-size:16.5px">${esc(threadName(t))}</div>${st && st.free !== null ? `<div class="b" style="font-size:12.5px;color:${st.c || 'var(--muted)'}">● ${esc(st.t)}</div>` : ''}</button>`; }
  else head = `<span class="sq" style="width:40px;height:40px;background:${t.kind === 'class' ? '#D6E4FF' : colorFor(t.id)};font-size:13px;color:var(--blue-ink)">${esc(initialsOf(threadName(t)))}</span><div class="grow"><div style="font-weight:900;font-size:16.5px">${esc(threadName(t))}</div><div class="muted b" style="font-size:12.5px">${t.members.length} member${t.members.length === 1 ? '' : 's'}</div></div>`;
  let prev = null, prevDay = '';
  const msgs = (rows || []).map(m => {
    const mine = m.sender === TC.user.id, showWho = t.kind !== 'direct' && !mine && m.sender !== prev; prev = m.sender;
    const dl = new Date(m.created_at).toDateString(); const sep = dl !== prevDay ? `<div class="muted b" style="text-align:center;font-size:12px;margin:6px 0">${dl === new Date().toDateString() ? 'Today' : esc(new Date(m.created_at).toLocaleDateString(undefined, { weekday: 'short', month: 'short', day: 'numeric' }))}</div>` : ''; prevDay = dl;
    return `${sep}<div class="msg ${mine ? 'me' : ''}">${showWho ? `<span class="who">${esc(nameOf(m.sender).split(' ')[0])}</span>` : ''}${esc(msgText(m))}</div>`;
  }).join('');
  return {
    top: `<div class="chathdr"><button class="iconbtn" style="width:38px;height:38px" data-a="back" aria-label="Back">${ic('chevL', 20, 2.4)}</button>${head}</div>`, padTop: 64,
    body: `<div class="msgs">${rows ? (msgs || '<div class="muted b" style="text-align:center;font-size:13px;margin-top:20px">Say hi 👋</div>') : (TC.rowsErr && TC.rowsErr[id]) ? errCard('Couldn’t load these messages.', 'retryChat') : loadingCard('Loading messages…')}</div><div style="height:100px"></div>`,
    bot: `<form class="composer" data-submit="send" data-x="${id}"><input id="chatin" placeholder="Message…" autocomplete="off" maxlength="2000" value="${esc(UI.prefill && UI.prefill.id === id ? UI.prefill.text : '')}"><button class="sendbtn pink" aria-label="Send">${ic('arrow', 20, 2.6)}</button></form>`, tabbar: false, fab: false, scrollEnd: true
  };
};

SCREENS.friend = ({ id }) => {
  const p = PEOPLE[id]; if (!p) return missingScreen('Not found.');
  const secs = personSecs(id), mine = myCodes(), shared = new Set(secs.map(s => s.code).concat(p.unplaced || []).filter(c => mine.has(c))), rel = TC.relation(id), isF = rel === 'friends';
  const st = isF ? status(id) : null;
  const codes = [...new Set(secs.map(s => s.code))];
  return {
    body: `<div class="topbtns"><button class="iconbtn" data-a="back" aria-label="Back">${ic('chevL', 22, 2.4)}</button></div>
 <div style="text-align:center;padding:0 16px"><span class="ringav" style="--rc:${(st && st.c) || 'transparent'};display:inline-block;padding:4px">${pav(id, 84, 28)}</span>
  <div style="font-size:26px;font-weight:900;margin-top:8px">${esc(p.name)}</div>${p.handle ? `<div class="muted b" style="font-size:14px">@${esc(p.handle)}</div>` : ''}${st && st.free !== null ? `<div class="b" style="color:${st.c || 'var(--muted)'};font-size:14px">● ${esc(st.t)}</div>` : ''}
  <div class="row" style="justify-content:center;margin-top:14px;gap:10px">${isF ? `<button class="pbtn pink" style="height:42px;padding:0 22px" data-a="openChatWith" data-x="${id}">Message</button>` : rel === 'incoming' ? `<button class="pbtn pink" data-a="acceptReq" data-x="${id}">Accept request</button>` : `<button class="pbtn ${rel === 'sent' ? 'done' : 'pink'}" data-a="addFriend" data-x="${id}">${rel === 'sent' ? 'Requested' : 'Add friend'}</button>`}${isF ? `<span class="pillchip" style="margin:0">${shared.size} class${shared.size === 1 ? '' : 'es'} with you</span>` : ''}</div></div>
 ${isF ? `${secs.length ? `<div class="card" style="margin:18px 16px 0;padding:14px 0 12px">${grid(secs, { sel: S.homeDay, act: 'homeDay', shared, one: true, H: 280 })}</div>` : ''}
 <div class="card list" style="margin:12px 16px 0">${codes.map(code => { const s = secs.find(x => x.code === code); return `<button class="li" data-a="openClass" data-x="${code}"><span class="code">${code}</span><span class="grow"><span class="b" style="font-size:15px;display:block">${esc(course(code).short)}</span><span class="muted b" style="font-size:12.5px">${secWhen(s)}</span></span>${shared.has(code) ? '<span class="st" style="background:#FEF9C3;color:#A16207">Shared</span>' : ''}</button>`; }).join('')}
  ${(p.unplaced || []).map(code => `<button class="li" data-a="openClass" data-x="${code}"><span class="code">${code}</span><span class="grow"><span class="b" style="font-size:15px;display:block">${esc(course(code).short)}</span><span class="muted b" style="font-size:12.5px">No section yet</span></span>${shared.has(code) ? '<span class="st" style="background:#FEF9C3;color:#A16207">Shared</span>' : ''}</button>`).join('')}
  ${!codes.length && !(p.unplaced || []).length ? `<div class="empty"><b>No ${esc(CFG.TERM_LABEL)} classes added</b></div>` : ''}</div>`
      : `<div class="empty" style="margin-top:20px"><b>Classes are shared between friends</b>Once you’re friends you’ll see each other’s weeks.</div>`}
 <div class="spacer"></div>`, tabbar: true, fab: true
  };
};

/* ================= sheets ================= */
const SHEETS = {};
SHEETS.notifs = () => {
  const reqs = TC.requests, un = TC.threads.filter(isUnread);
  const rows = [
    ...reqs.map(id => `<div class="row" style="width:100%;padding:12px 0;border-top:1px solid var(--line)">${pav(id, 42, 14)}<div class="grow"><div class="b" style="font-size:15px">${esc(PEOPLE[id].name)} sent you a friend request</div></div><button class="pbtn pink" data-a="acceptReq" data-x="${id}">Accept</button></div>`),
    ...un.map(t => `<button class="row" style="width:100%;padding:12px 0;border-top:1px solid var(--line)" data-a="openChatTab" data-x="${t.id}"><span class="sq" style="width:42px;height:42px;background:#FCE7F3;color:#DB2777;border-radius:14px">${ic('msg', 20)}</span><div class="grow"><div class="b" style="font-size:15px">${esc(threadName(t))}</div><div class="muted b" style="font-size:13px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis">${esc(msgText(t.last))} · ${agoText(t.last.created_at)}</div></div><span class="chev">${ic('chevR', 18)}</span></button>`)
  ];
  return `<div class="row sb"><h3>Notifications</h3><button class="xbtn" data-a="closeSheet">${ic('x', 16, 2.4)}</button></div>
 ${rows.length ? rows.join('') : '<div class="empty"><b>Nothing new</b>Friend requests and new messages show up here.</div>'}`;
};
SHEETS.profile = () => {
  const P = TC.profile || {};
  return `<div class="row sb"><span></span><button class="xbtn" data-a="closeSheet">${ic('x', 16, 2.4)}</button></div>
 <div style="text-align:center;margin-top:-10px">${pav('me', 76, 24)}<div style="font-size:22px;font-weight:900;margin-top:10px">${esc(PEOPLE.me.name)}</div>${P.username ? `<div class="muted b">@${esc(P.username)}</div>` : ''}${P.major ? `<div class="muted b">${esc(P.major)}${P.class_standing ? ' · ' + esc(P.class_standing) : ''}</div>` : ''}</div>
 <div class="know" style="margin:18px 0"><div><small>CLASSES</small><b>${myCodes().size}</b></div><div><small>FRIENDS</small><b>${TC.friends.length}</b></div><div><small>REVIEWS</small><b>${TC.myReviews.length}</b></div></div>
 <a class="btn soft tc-a" href="${WEB}/" target="_blank" rel="noopener">Settings & full app on termchamp.com</a>
 <button class="btn ghost" style="margin-top:6px;color:#B91C1C" data-a="signOut">Sign out</button>`;
};
function subjectsForFilter() {
  const count = {};
  [...myCodes()].concat(...TC.friends.map(f => personSecs(f).map(s => s.code))).forEach(c => { const s = c.split(' ')[0]; count[s] = (count[s] || 0) + 1; });
  const l = Object.keys(count).sort((a, b) => count[b] - count[a]).slice(0, 10);
  if (S.subj !== 'All' && l.indexOf(S.subj) < 0) l.unshift(S.subj);
  return ['All', ...l];
}
SHEETS.filters = () => `<div class="row sb"><h3>Filters</h3><button class="xbtn" data-a="closeSheet">${ic('x', 16, 2.4)}</button></div>
 <div class="flabel" style="margin:14px 0 10px">Subject</div>
 <div style="display:flex;flex-wrap:wrap;gap:8px">${subjectsForFilter().map(c => `<button class="chip ${S.subj === c ? 'on' : ''}" style="${S.subj === c ? 'background:var(--blue)' : 'background:var(--bg)'}" data-a="setSubj" data-x="${c}">${esc(c)}</button>`).join('')}</div>
 <div class="hint" style="margin-top:8px">Or type any subject, like CSC, in the search box.</div>
 <div class="row sb" style="margin:20px 0 6px"><div><div class="flabel">Open seats only</div><div class="hint">Hide classes with no open section</div></div><button class="toggle ${S.openOnly ? 'on' : 'off'}" data-a="openOnly"><i></i></button></div>
 <div class="row" style="gap:10px;margin-top:20px"><button class="btn soft" data-a="clearFilters">Clear</button><button class="btn" data-a="closeSheet">Show results</button></div>`;
SHEETS.addFriend = (o) => {
  const sug = TC.suggestions;
  const res = UI.peopleRes;
  const row = id => { const p = PEOPLE[id], rel = TC.relation(id); return `<div class="row" style="padding:10px 0;border-top:1px solid var(--line)">${pav(id, 44, 15)}<div class="grow"><div class="b" style="font-size:15.5px">${esc(p.name)}</div><div class="muted b" style="font-size:13px">${esc(p.sub || (p.handle ? '@' + p.handle : ''))}</div></div>${rel === 'friends' ? '<span class="pbtn done">Friends</span>' : rel === 'incoming' ? `<button class="pbtn pink" data-a="acceptReq" data-x="${id}">Accept</button>` : `<button class="pbtn ${rel === 'sent' ? 'done' : 'pink'}" data-a="addFriend" data-x="${id}">${rel === 'sent' ? 'Requested' : 'Add'}</button>`}</div>`; };
  return `<div class="row sb"><h3>Add friends</h3><button class="xbtn" data-a="closeSheet">${ic('x', 16, 2.4)}</button></div>
 <form data-submit="people" class="search" style="margin:10px 0 6px"><span style="color:var(--pink)">${ic('search', 20, 2.4)}</span><input id="pq" value="${esc(UI.peopleQ || '')}" placeholder="Name, email or @username" autocomplete="off" enterkeyhint="search"></form>
 <div id="pres">${res === 'busy' ? loadingCard('Searching…') : res && res.err ? `<div class="tc-err">${esc(res.err)}</div>` : Array.isArray(res) ? (res.length ? res.map(row).join('') : `<div class="muted b" style="padding:10px 0">No one matching “${esc(UI.peopleQ)}” is on TermChamp yet.</div>`) : ''}</div>
 ${sug.length ? `<div class="muted b" style="font-size:14px;margin:14px 0 4px">People you might know</div>${sug.map(row).join('')}` : ''}
 <button class="btn soft" style="margin-top:14px" data-a="copyInvite">Share an invite link</button>`;
};
SHEETS.sec = ({ code, id }) => {
  const s = SEC[id] || personSecs('me').find(x => x.id === id); if (!s) return '';
  const c = course(code), fr = friendsInSec(id), inP = TC.plans[S.plan].includes(id), w = !!TC.watches[id];
  return `<div class="row sb"><span class="code">${code}${s.sec ? ' §' + esc(s.sec) : ''}</span><button class="xbtn" data-a="closeSheet">${ic('x', 16, 2.4)}</button></div>
 <h3 style="margin-top:10px">${esc(c.title)}</h3><div class="muted b">${esc(profName(s.prof))} · ${secWhen(s)}</div>
 <div class="b" style="margin-top:6px;font-size:14px">${secSeatText(s)}${s.location ? ` <span class="muted">· ${esc(s.location)}</span>` : ''}</div>
 ${fr.length ? `<div class="row" style="margin-top:12px;gap:8px">${avStack(fr, 28)}<span class="b" style="font-size:14px">${fr.map(f => esc(PEOPLE[f].short)).join(', ')}</span></div>` : ''}
 <div style="display:grid;gap:8px;margin-top:18px"><button class="btn" data-a="openClass" data-x="${code}">View class</button>
 ${SEC[id] ? `<button class="btn soft" data-a="watch" data-x="${esc(id)}">${w ? 'Stop seat alerts' : 'Alert me about seats'}</button>` : ''}
 ${inP ? `<button class="btn soft" style="color:#B91C1C" data-a="removeSec" data-x="${esc(id)}">Remove from Plan ${S.plan}</button>` : ''}</div>`;
};

function champView() {
  const m = S.champMsgs;
  const first = personSecs('me')[0];
  const sugg = [first ? ['cc1', 'Best professor for ' + first.code] : ['cc1', 'Open CSC classes after 10am'], ['cc2', "Who's free right now?"], ['cc3', 'My game plan for Plan A'], ['cc4', 'What’s my day look like?']];
  const chips = `<div class="cchips">${sugg.slice(0, m.length ? 4 : 3).map(([c, t]) => `<button class="cchip ${c}" data-a="ask" data-x="${esc(t)}">${esc(t)}</button>`).join('')}</div>`;
  /* The same disclosure the desktop's Hawk carries, and the privacy policy's Hawk section describes. */
  const input = `<form class="cinput" data-submit="champ"><input id="champin" placeholder="Ask Champ…" autocomplete="off" maxlength="300"><button class="sendbtn" aria-label="Send">${ic('arrow', 20, 2.6)}</button></form><div class="muted b" style="font-size:11.5px;text-align:center;margin-top:6px">Questions are read by AI · your classes stay on this phone</div>`;
  if (!m.length) return `<div class="champ-hero"><img src="${CHAMP}" alt="Champ"></div><button class="xbtn" style="position:absolute;right:16px;top:16px" data-a="closeSheet" aria-label="Close">${ic('x', 16, 2.4)}</button>
  <div class="sbody" style="padding-top:14px"><div class="ctitle2">Hi, I'm Champ.</div><p class="muted b" style="text-align:center;font-size:16px;margin:4px 0 18px">Ask about ${esc(CFG.TERM_LABEL)} classes, professors, your week or your friends.</p>${chips}<div style="height:16px"></div>${input}</div>`;
  const msgs = m.map(x => x.me ? `<div class="msg me">${esc(x.t)}</div>` : `<div class="bot"><img src="${CHAMP}" alt=""><div class="msg">${x.t}${x.acts && x.acts.length ? `<div class="acts">${x.acts.map((a, i) => `<button class="act ${i === 0 ? 'primary' : ''}" data-a="${a[1]}" data-x="${esc(a[2])}" ${a[3] ? `data-y="${esc(a[3])}"` : ''}>${esc(a[0])}</button>`).join('')}</div>` : ''}</div></div>`).join('');
  return `<div class="row" style="padding:14px 16px 10px;border-bottom:1px solid var(--line)"><img src="${CHAMP}" alt="" style="width:34px;height:40px;object-fit:contain"><div class="grow"><div style="font-weight:900;font-size:17px;color:var(--navy)">Champ</div><div class="muted b" style="font-size:12px">Answers from TermChamp’s real data</div></div><button class="xbtn" data-a="champClear" title="New chat" aria-label="New chat">${ic('trash', 16)}</button><button class="xbtn" data-a="closeSheet" aria-label="Close">${ic('x', 16, 2.4)}</button></div>
 <div class="sbody" id="champscroll" style="padding:14px 14px 8px;flex:1"><div class="msgs" style="padding:0">${msgs}${UI.typing === 'champ' ? '<div class="bot"><img src="' + CHAMP + '" alt=""><div class="msg typing"><i></i><i></i><i></i></div></div>' : ''}</div></div>
 <div style="padding:8px 14px 14px;border-top:1px solid var(--line)"><div class="cchips" style="justify-content:flex-start;flex-wrap:nowrap;overflow-x:auto;padding-bottom:8px;scrollbar-width:none">${chips.replace('<div class="cchips">', '').replace(/<\/div>$/, '')}</div>${input}</div>`;
}
