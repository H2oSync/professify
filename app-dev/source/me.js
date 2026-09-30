/* =================================================================================================
   YOU, SETTINGS AND THE PLANNER — PR 2 (2026-09-28)
   -------------------------------------------------------------------------------------------------
   · Your profile (tap your picture anywhere): photo, name, @username, major, your reviews with Edit
     and Delete, your friends, your degree at a glance.
   · Settings: edit profile (photo, name, username, major, concentration, year), password, plan
     sharing, blocked people, the legal pages, sign out.
   · Planner (Schedule › Planner): the desktop's requirements ledger for your major, what you still
     need with whether you can take it now, GE areas with this term's classes, and your past classes.
   The degree rules and data come from app/planner.js, which build.py lifts out of the desktop's
   index.html verbatim, so the two apps can never disagree about a degree.
   ================================================================================================= */
Object.assign(I, {
  gear: '<circle cx="12" cy="12" r="3.2"/><path d="M19.4 15a1.7 1.7 0 0 0 .3 1.8l.1.1a2 2 0 1 1-2.8 2.8l-.1-.1a1.7 1.7 0 0 0-1.8-.3 1.7 1.7 0 0 0-1 1.5V21a2 2 0 1 1-4 0v-.1a1.7 1.7 0 0 0-1.1-1.5 1.7 1.7 0 0 0-1.8.3l-.1.1a2 2 0 1 1-2.8-2.8l.1-.1a1.7 1.7 0 0 0 .3-1.8 1.7 1.7 0 0 0-1.5-1H3a2 2 0 1 1 0-4h.1a1.7 1.7 0 0 0 1.5-1.1 1.7 1.7 0 0 0-.3-1.8l-.1-.1a2 2 0 1 1 2.8-2.8l.1.1a1.7 1.7 0 0 0 1.8.3H9a1.7 1.7 0 0 0 1-1.5V3a2 2 0 1 1 4 0v.1a1.7 1.7 0 0 0 1 1.5 1.7 1.7 0 0 0 1.8-.3l.1-.1a2 2 0 1 1 2.8 2.8l-.1.1a1.7 1.7 0 0 0-.3 1.8V9a1.7 1.7 0 0 0 1.5 1H21a2 2 0 1 1 0 4h-.1a1.7 1.7 0 0 0-1.5 1z"/>',
  pencil: '<path d="M4 20h4L19 9l-4-4L4 16z"/><path d="m13.5 6.5 4 4"/>',
  camera: '<path d="M4 8h3l2-2.5h6L17 8h3v11H4z"/><circle cx="12" cy="13.5" r="3.5"/>'
});

/* ---- avatar encoder, lifted verbatim from index.html by build.py (the same 512px square) ---- */
/* @@AVATAR@@ */

/* ================= backend: you ================= */
const STANDINGS = ['Freshman', 'Sophomore', 'Junior', 'Senior', '5th year +'];
TC.email = () => (TC.user && TC.user.email) || '';
TC.loadWaivers = async function () {
  const r = await TC.client().from('class_waivers').select('code,reason').eq('user_id', TC.user.id);
  TC.waived = {};
  TC.wavErr = !!r.error && !schemaGap(r.error);
  if (!r.error) (r.data || []).forEach(w => { TC.waived[w.code] = w.reason || 'waived'; });
};
TC.reloadHistory = async function () {
  const r = await TC.client().from('class_history').select('code,term,year,professor').eq('user_id', TC.user.id);
  if (r.error) { TC.err.history = r.error.message; return false; }
  delete TC.err.history; TC.myHistory = r.data || []; return true;
};
TC.addHistory = async function (code, term, year, professor) {
  if (window.TCPL) { const cur = TCPL.canon(code); if (cur) code = cur; }
  const row = { user_id: TC.user.id, code, term, year, professor: professor || null };
  const r = await TC.client().from('class_history').upsert(row);
  if (r.error) return dbSay(r.error, 'Couldn’t save that class.');
  await TC.reloadHistory(); loadRateList(); return null;
};
TC.removeHistory = async function (code) {
  const r = await TC.client().from('class_history').delete().eq('user_id', TC.user.id).eq('code', code);
  if (r.error) return dbSay(r.error, 'Couldn’t remove that class.');
  await TC.reloadHistory(); loadRateList(); return null;
};
/* The desktop's dbFriendlyErr, in short: our own sentences through, raw database text never. */
function dbSay(e, generic) {
  const m = String((e && e.message) || ''), c = String((e && e.code) || '');
  try { console.error('[termchamp app]', c, m, e); } catch (x) {}
  if (c === 'P0001' && m) return m.charAt(0).toUpperCase() + m.slice(1);
  if (/failed to fetch|network|load failed|timeout/i.test(m)) return 'Couldn’t reach TermChamp — check your connection and try again.';
  if (c === '23505' || /duplicate|unique/i.test(m)) return 'That’s already there.';
  if (isJwtErr(e)) return 'Your sign-in expired. Sign out and back in, then try again.';
  return generic + ' (code ' + (c || 'unknown') + ')';
}
/* A write RLS refuses doesn't error — it changes nothing and says so by returning no rows. Every
   write here asks for the row back, and "nothing came back" is a refusal, never a success. */
const NOTHING = { code: 'no-rows', message: 'no rows changed' };
TC.updateReview = async function (id, patch) {
  await TC.freshSession();
  let r = await TC.client().from('reviews').update(patch).eq('id', id).select('id');
  if (r.error && /grade/i.test(r.error.message || '') && schemaGap(r.error)) { const p2 = Object.assign({}, patch); delete p2.grade; r = await TC.client().from('reviews').update(p2).eq('id', id).select('id'); }
  if (!r.error && !(r.data || []).length) r = { error: NOTHING };
  if (r.error) {
    if (/duplicate|unique/i.test(r.error.message || '')) return 'You already have a review for that class. Delete one of them, or point this one at the class you actually took.';
    if (r.error.code === '42501' || /row-level security/i.test(r.error.message || '')) return 'That edit was refused. Nothing you wrote has been lost — sign out and back in, then try again.';
    return dbSay(r.error, 'That edit didn’t save. Nothing you wrote has been lost.');
  }
  await TC.reloadMyReviews(); return null;
};
TC.deleteReview = async function (id) {
  await TC.freshSession();
  let r = await TC.client().from('reviews').delete().eq('id', id).select('id');
  if (!r.error && !(r.data || []).length) r = { error: NOTHING };
  if (r.error) return dbSay(r.error, 'Couldn’t delete that review — it’s still there.');
  await TC.reloadMyReviews(); return null;
};
TC.reloadMyReviews = async function () {
  const m = await TC.client().rpc('my_reviews');
  if (!m.error && Array.isArray(m.data)) TC.myReviews = m.data;
  TC.myReviewsErr = !!m.error;
};
TC.usernameTaken = async function (u) {
  let r = await TC.client().rpc('username_taken', { u });
  if (!r.error) return !!r.data;
  if (/function|schema cache|does not exist/i.test(r.error.message || '')) {
    r = await TC.client().from('profiles').select('id').ilike('username', u).limit(1);
    if (!r.error) return (r.data || []).some(x => x.id !== TC.user.id);
  }
  return null;       // couldn't check
};
function userShape(v) {
  if (!v) return { ok: true, msg: 'Optional — but it’s how friends find you.' };
  if (v.length < 3) return { ok: false, msg: 'At least 3 characters.' };
  if (v.length > 20) return { ok: false, msg: '20 characters max.' };
  if (!/^[A-Za-z0-9_]+$/.test(v)) return { ok: false, msg: 'Letters, numbers and underscores only.' };
  if (wfReserved(v)) return { ok: false, msg: 'That one’s reserved — it reads like an official account.' };
  const bad = wfHitTight(v); if (bad) return { ok: false, msg: 'Your username is on every review you post — “' + bad + '” can’t be in it.' };
  return { ok: true, msg: '' };
}
TC.saveProfile = async function (f) {
  f = Object.assign({}, f, { display_name: String(f.display_name || '').trim(), username: String(f.username || '').trim().replace(/^@/, '') });
  await TC.freshSession();
  const nameBad = wfHit(f.display_name || ''); if (nameBad) return '“' + nameBad + '” can’t be in your name — it shows next to you everywhere in the app.';
  const shape = userShape(f.username || ''); if (!shape.ok) return shape.msg;
  if (f.username && f.username.toLowerCase() !== String((TC.profile && TC.profile.username) || '').toLowerCase()) {
    const taken = await TC.usernameTaken(f.username); if (taken === true) return '@' + f.username + ' is taken — pick another.';
  }
  const patch = { display_name: f.display_name || null, username: f.username || null, major: f.major || null, concentration: f.concentration || null, class_standing: f.class_standing || null };
  if (f.photo === 'remove') { patch.avatar_url = null; try { await TC.client().storage.from('avatars').remove([TC.user.id + '/avatar.jpg']); } catch (e) {} }
  else if (f.photo && f.photo.blob) {
    const path = TC.user.id + '/avatar.jpg';
    const up = await TC.client().storage.from('avatars').upload(path, f.photo.blob, { upsert: true, contentType: 'image/jpeg', cacheControl: '3600' });
    if (up.error) return dbSay(up.error, 'Couldn’t upload that photo — nothing else was saved.');
    const pub = TC.client().storage.from('avatars').getPublicUrl(path);
    patch.avatar_url = ((pub && pub.data && pub.data.publicUrl) || '') + '?v=' + Date.now();
  }
  let r = await TC.client().from('profiles').update(patch).eq('id', TC.user.id).select('id');
  if (r.error && schemaGap(r.error)) { delete patch.concentration; r = await TC.client().from('profiles').update(patch).eq('id', TC.user.id).select('id'); }
  if (!r.error && !(r.data || []).length) r = { error: NOTHING };
  if (r.error) return /duplicate|unique/i.test(r.error.message || '') ? 'That username was just taken — pick another.' : dbSay(r.error, 'Couldn’t save your profile.');
  Object.assign(TC.profile, patch);
  concRemember(TC.profile.major, TC.profile.concentration);
  const nm = TC.profile.display_name || TC.profile.username || 'You';
  Object.assign(PEOPLE.me, { name: nm, short: nm.split(/\s+/)[0], ini: initialsOf(nm), avatar: TC.profile.avatar_url || '', handle: TC.profile.username || '' });
  return null;
};
TC.setPassword = async function (pw) {
  if (String(pw || '').length < 8) return 'At least 8 characters.';
  const r = await TC.client().auth.updateUser({ password: pw });
  if (r.error) return /same|different from the old/i.test(r.error.message || '') ? 'That’s already your password.' : /weak|short|characters/i.test(r.error.message || '') ? 'Pick a stronger password — longer, with a mix of letters and numbers.' : 'Couldn’t change your password — try again.';
  return null;
};
TC.setPlanShared = async function (slot, on) {
  if (!TC.plans[slot].length) return 'Add a class to Plan ' + slot + ' first.';
  TC.planShared[slot] = !!on;
  const list = TC.plans[slot].map(id => { const s = SEC[id]; return s ? { code: s.code, class_nbr: id } : null; }).filter(Boolean);
  const r = await TC.client().from('plans').upsert({ user_id: TC.user.id, term: CFG.TERM, slot, sections: list, shared: !!on }, { onConflict: 'user_id,term,slot' });
  return r.error ? dbSay(r.error, 'Couldn’t change that.') : null;
};
TC.loadBlocks = async function () {
  const r = await TC.client().rpc('my_blocks');
  TC.blocks = (!r.error && Array.isArray(r.data)) ? r.data : [];
  TC.blocksErr = !!r.error;
};
TC.unblock = async function (id) {
  const r = await TC.client().rpc('unblock_user', { p_target: id });
  if (r.error) return 'Couldn’t unblock — try again.';
  TC.blocks = (TC.blocks || []).filter(b => b.id !== id); return null;
};

/* ---- the planner module (app/planner.js), loaded on first use ---- */
TC.loadPlanner = function () {
  if (window.TCPL) return Promise.resolve(true);
  if (TC._plLoading) return TC._plLoading;
  TC._plLoading = new Promise(res => {
    const s = document.createElement('script');
    s.src = 'planner.js?v=' + encodeURIComponent(window.TERMCHAMP_APP_BUILD || '');
    s.onload = () => res(!!window.TCPL); s.onerror = () => { TC._plLoading = null; res(false); };
    document.head.appendChild(s);
  });
  return TC._plLoading;
};
function plSync() {
  if (!window.TCPL) return;
  const idx = {}, names = {}; Object.keys(COURSES).forEach(c => { idx[c] = 1; names[c] = COURSES[c].title; });
  TCPL.set({ student: { major: (TC.profile && TC.profile.major) || '', conc: (TC.profile && TC.profile.concentration) || '', standing: (TC.profile && TC.profile.class_standing) || '' },
    history: TC.myHistory || [], classes: [...myCodes()], waived: TC.waived || {}, index: idx, names });
}
async function openPlanner() {
  UI.pl = UI.pl || { state: 'loading' };
  const pl = UI.pl;
  if (pl.state === 'ready' || pl.opening) return;
  pl.opening = true;
  const ok = await TC.loadPlanner();
  if (!ok) { pl.state = 'failed'; pl.opening = false; render(true); return; }
  await Promise.all([TC.myHistory ? null : TC.reloadHistory(), TC.waived ? null : TC.loadWaivers()]);
  pl.opening = false; pl.state = 'ready'; render(true);
  if (!TC._plTables) TC._plTables = TCPL.loadCatalogTables(TC.client());
  TC._plTables.then(r => { if (UI.pl) UI.pl.prereqs = !!(r && r.prereqs); render(true); });
}

/* ---- Degree Progress Report: read on the phone, with the desktop's own reader ----------------
   The report's text lives only inside readDpr(). It carries the student's EMPLID on every page and
   a grade on every row; dprParse() scrubs the EMPLID first and keeps only "finished or not", and
   nothing but course codes and terms leaves this function. */
function loadPdfJs() {
  if (window.pdfjsLib) return Promise.resolve(window.pdfjsLib);
  return new Promise((res, rej) => {
    const s = document.createElement('script'); s.src = TCPL.pdfBase + 'pdf.min.js';
    /* Pinned like supabase-js: this script reads the report's raw text, so it must be exactly the
       file we checked (sha384 of pdfjs-dist@3.11.174 legacy/build/pdf.min.js). */
    s.integrity = 'sha384-OemFRmhjDZwhIKuUld0HJozkF2YErsgDaCL41trxGQZt4/WgnopJQqQl2DvDZ07Z'; s.crossOrigin = 'anonymous';
    s.onload = () => { try { window.pdfjsLib.GlobalWorkerOptions.workerSrc = TCPL.pdfBase + 'pdf.worker.min.js'; } catch (e) {} res(window.pdfjsLib); };
    s.onerror = () => rej(new Error('pdf')); document.head.appendChild(s);
  });
}
async function readDpr(file) {
  const lib = await loadPdfJs();
  let doc = null, text = '';
  try {
    doc = await lib.getDocument({ data: new Uint8Array(await TCPL.fileBytes(file)) }).promise;
    const n = Math.min(doc.numPages || 0, 30);
    for (let p = 1; p <= n; p++) { const page = await doc.getPage(p); const tc = await page.getTextContent(); text += '\n\n' + TCPL.pdfItemsToText(tc && tc.items); try { page.cleanup(); } catch (e) {} }
  } catch (e) {
    return { err: /password/i.test((e && e.name) + ' ' + (e && e.message)) ? 'That PDF is password-protected. Save the report again without a password.' : 'Couldn’t read that PDF — it may be damaged. Download the report again from the Cal Poly Portal.' };
  } finally { try { if (doc) doc.destroy(); } catch (e) {} }   // the file's bytes (EMPLID included) don't outlive the read
  if (!text.trim()) return { err: 'That PDF has no text in it — it looks scanned. Download the report again from the Cal Poly Portal as a PDF.' };
  if (!TCPL.dprLooksLikeOne(text)) return { err: 'That isn’t a Degree Progress Report. In the Cal Poly Portal, open your Degree Progress Report and save it as a PDF.' };
  plSync();
  const r = TCPL.dprParse(text); text = '';
  if (!r.ok || !r.rows.length) return { err: 'Couldn’t find the Course History table in that report.' };
  /* An ungraded row is only ever a finished class when its term is BEFORE this one (AP and
     study-abroad placeholders). Ungraded this term = My Classes; ungraded in a later term (after
     Oct 5, next term's registered classes) = not added. The desktop reads "newest term" instead,
     which after registration would file this term's classes as finished (review, 2026-09-28). */
  const ORD = { Winter: 1, Spring: 2, Summer: 3, Fall: 4 }, key = (t, y) => (+y) * 10 + (ORD[t] || 0);
  const [ct, cy] = CFG.TERM_LABEL.split(' '), cur = key(ct, cy);
  r.rows.forEach(x => {
    const k = key(x.term, x.year);
    if (x._open && k === cur) x._now = true;
    else if (x._open && k > cur) { x._now = false; x.skip = 'registered for ' + x.term + ' ' + x.year + ' — not a finished class'; x.pick = false; }
    else if (x._now) x._now = false;           // ungraded, older: treated as finished, as on the desktop
    if (x._now && myCodes().has(x.cur)) { x.already = true; x.pick = false; }
  });
  r.latestTerm = CFG.TERM_LABEL;
  return r;
}
TC.saveDpr = async function (r) {
  const pick = r.rows.filter(x => x.pick && !x.already && !x.skip);
  const past = pick.filter(x => !x._now), now = pick.filter(x => x._now);
  await TC.freshSession();
  if (past.length) {
    const seen = {}, rows = [];
    past.forEach(x => { const k = x.cur + '|' + x.term + '|' + x.year; if (seen[k]) return; seen[k] = 1;
      rows.push({ user_id: TC.user.id, code: x.cur, term: x.term, year: x.year, professor: x._xfer ? TCPL.abroadMark : null }); });
    const q = await TC.client().from('class_history').upsert(rows);
    if (q.error) return dbSay(q.error, 'Couldn’t save your past classes — nothing was added.');
  }
  if (now.length) {
    const q = await TC.client().from('saved_classes').upsert(now.map(x => ({ user_id: TC.user.id, term: CFG.TERM, code: x.cur })));
    if (q.error) { await TC.reloadHistory(); return dbSay(q.error, 'Past classes saved, but this term’s classes didn’t — add them on termchamp.com.'); }
  }
  await Promise.all([TC.reloadHistory(), loadMine()]); loadRateList();
  toast((past.length ? past.length + ' past class' + (past.length === 1 ? '' : 'es') : '') + (past.length && now.length ? ' and ' : '') + (now.length ? now.length + ' class' + (now.length === 1 ? '' : 'es') + ' this term' : '') + ' added');
  return null;
};

/* ================= screens ================= */
function meBtn() {
  return `<button class="me-btn" data-a="openMe" aria-label="Your profile" style="overflow:hidden;padding:0">${safeImg(PEOPLE.me.avatar) ? `<img src="${esc(safeImg(PEOPLE.me.avatar))}" alt="" style="width:100%;height:100%;object-fit:cover" onerror="this.remove()">` : esc(PEOPLE.me.ini)}</button>`;
}
const backBtn = () => `<button class="iconbtn" data-a="back" aria-label="Back">${ic('chevL', 22, 2.4)}</button>`;
const sectionCard = (title, body, right) => `<div class="card tc-sec"><div class="tc-sech"><span>${title}</span>${right || ''}</div>${body}</div>`;
const starsTxt = n => { const s = Math.max(0, Math.min(5, Math.round(+n || 0))); return `<span style="color:#F59E0B;letter-spacing:1px">${'★'.repeat(s)}<span style="color:#E2E8F0">${'★'.repeat(5 - s)}</span></span>`; };
function reviewProfKey(v) { const nm = String(v.professor_key || '').split('|')[0]; return Object.keys(PROFS).find(k => String(PROFS[k].name).toLowerCase() === nm) || null; }

SCREENS.me = () => {
  const P = TC.profile || {}, n = myCodes().size;
  const mine = (TC.myReviews || []).slice().sort((a, b) => String(b.created_at).localeCompare(String(a.created_at)));
  const revRows = mine.map(v => `<div class="tc-rev"><div class="row sb"><div class="grow" style="min-width:0"><div class="b" style="font-size:15.5px">${esc(v.professor_name || String(v.professor_key || '').split('|')[0])}</div>
    <div class="row" style="gap:8px;margin-top:3px">${v.course ? `<span class="code" style="font-size:12px;padding:3px 8px">${esc(v.course)}</span>` : ''}${starsTxt(v.score)}<span class="muted b" style="font-size:12.5px">${agoText(v.created_at)}${v.edited_at ? ' · edited' : ''}</span></div></div></div>
    ${v.note ? `<p class="tc-revnote">${esc(v.note)}</p>` : ''}
    ${v.id ? `<div class="row" style="gap:8px;margin-top:8px"><button class="pbtn" data-a="editReview" data-x="${esc(v.id)}">Edit</button><button class="pbtn tc-danger" data-a="askDeleteReview" data-x="${esc(v.id)}">Delete</button>${v.share_with_friends ? '<span class="muted b" style="font-size:12.5px">Friends see it’s yours</span>' : ''}</div>` : ''}</div>`).join('');
  const fr = TC.friends.slice(0, 8);
  let deg = '';
  if (window.TCPL && P.major && TC.waived && TC.myHistory) { plSync(); const L = TCPL.ledger(); if (L) deg = `<button class="li" data-a="schedTabGo" data-x="planner"><span class="sq" style="width:40px;height:40px;background:var(--teal-soft);color:var(--teal)">${ic('grad', 22)}</span><span class="grow"><span class="b" style="display:block;font-size:15px">${L.F} of ${L.N} requirements filled</span><span class="muted b" style="font-size:13px">${esc(L.major)}${L.T ? ` · ${L.T} in progress` : ''}</span></span><span class="chev">${ic('chevR', 18)}</span></button>`; }
  const email = TC.email();
  const majorLine = P.major ? esc(P.major) + (P.concentration ? ' · ' + esc(P.concentration) + (/concentration/i.test(P.concentration) ? '' : ' concentration') : '') : 'Add your major';
  /* "Free right now" counts only friends whose class times we have — a friend with none added is
     unknown, not free. status() is on San Luis Obispo time. */
  const timed = TC.friends.filter(f => status(f).free !== null), freeN = timed.filter(f => status(f).free === true).length;
  const freeLine = !TC.friends.length ? 'Add friends' : !timed.length ? 'No class times added yet' : `${freeN} free right now`;
  const revN = (TC.myReviews || []).length, sharedN = (TC.myReviews || []).filter(v => v.share_with_friends).length;
  const mrow = (act, x, label, val) => `<button class="li tc-mrow" data-a="${act}"${x ? ` data-x="${x}"` : ''}><span class="grow b">${label}</span><span class="tc-mval">${val}</span><span class="chev">${ic('chevR', 18)}</span></button>`;
  const rows = [
    mrow('scrollTo', 'tcMyRevs', 'My ratings', TC.myReviewsErr ? 'Couldn’t load' : TC.myReviews === undefined ? '…' : `${revN} posted`),
    mrow('openSettings', '', 'Who sees my schedule', 'Friends'),
    mrow('scrollTo', 'tcMyRevs', 'Name on my ratings', TC.myReviews === undefined ? '…' : sharedN ? `Friends see ${sharedN}` : 'Anonymous'),
    `<label class="li tc-mrow" style="cursor:pointer"><span class="grow b">Degree Progress Report</span><span class="tc-mval">Import PDF</span><span class="chev">${ic('chevR', 18)}</span><input type="file" accept="application/pdf,.pdf" data-in="dprfile" hidden></label>`,
    deg ? deg.replace('<button class="li"', '<button class="li tc-mrow"') : '',
    mrow('openEditProfile', '', 'Major and concentration', P.major ? esc(P.major) + (P.concentration ? ' · ' + esc(P.concentration) : '') : 'Add')
  ].join('');
  return {
    body: `<div class="topbtns">${backBtn()}<button class="iconbtn" data-a="openSettings" aria-label="Settings">${ic('gear', 21, 2)}</button></div>
 <div class="tc-mehead">${pav('me', 76, 26)}<div class="grow" style="min-width:0">
  <div class="tc-mename">${esc(PEOPLE.me.name)}</div>
  ${P.username ? `<div class="muted b" style="font-size:13.5px">@${esc(P.username)}</div>` : ''}
  <div class="b" style="font-size:14.5px;color:var(--ink3);margin-top:3px">${majorLine}</div>
  <div class="muted b" style="font-size:13px;margin-top:1px;overflow-wrap:anywhere">${[P.class_standing, email].filter(Boolean).map(esc).join(' · ')}</div></div></div>
 <div class="tc-mebtns"><button class="btn" data-a="openEditProfile">Edit profile</button><button class="btn soft" data-a="openSettings">Settings</button></div>
 <div class="tc-mestats"><button class="card tc-stat" data-a="tab" data-x="schedule"><span><b>${n}</b> ${n === 1 ? 'class' : 'classes'}</span><small>${esc(CFG.TERM_LABEL)}</small></button>
  <button class="card tc-stat" data-a="fFilterGo" data-x="people"><span><b>${TC.friends.length}</b> ${TC.friends.length === 1 ? 'friend' : 'friends'}</span><small>${esc(freeLine)}</small></button></div>
 <div class="card list tc-mlist">${rows}</div>
 <div id="tcMyRevs">${sectionCard('Your reviews', TC.myReviewsErr ? '<div class="muted b" style="padding:6px 0 12px">Couldn’t load your reviews — pull down to try again.</div>' : (revRows || `<div class="muted b" style="font-size:14px;padding:4px 0 12px">No reviews yet. ${unrated().length ? `<a class="link" data-a="tab" data-x="rate" style="color:var(--blue)">Rate a professor</a>` : ''}</div>`), `<span class="muted b" style="font-size:13px">Anonymous unless you share one</span>`)}</div>
 ${sectionCard('Friends', fr.length ? fr.map(id => `<button class="li" data-a="openFriend" data-x="${id}">${pav(id, 40, 14)}<span class="grow b" style="font-size:15px">${esc(PEOPLE[id].name)}</span><span class="chev">${ic('chevR', 18)}</span></button>`).join('') : '<div class="muted b" style="padding:4px 0 12px">No friends yet.</div>', TC.friends.length > 8 ? `<a class="link b" data-a="fFilterGo" data-x="people" style="color:var(--blue)">See all ${TC.friends.length}</a>` : '')}
 <div class="spacer"></div>`, tabbar: true, fab: false
  };
};

SCREENS.settings = () => {
  const blocks = TC.blocks;
  /* An empty plan has no row to hold the choice, so it isn't offered until the plan has a class —
     a switch that quietly reverts on reload is worse than none. */
  const shareRow = k => TC.plans[k].length
    ? `<div class="row sb tc-row"><div><div class="b" style="font-size:15px">Plan ${k}</div><div class="muted b" style="font-size:12.5px">${TC.plans[k].length} section${TC.plans[k].length === 1 ? '' : 's'}</div></div><button class="toggle ${TC.planShared[k] !== false ? 'on' : 'off'}" data-a="togglePlanShare" data-x="${k}" aria-label="Friends can see Plan ${k}"><i></i></button></div>`
    : `<div class="row sb tc-row"><div><div class="b" style="font-size:15px">Plan ${k}</div><div class="muted b" style="font-size:12.5px">Empty — add a class, then choose who sees it</div></div></div>`;
  const legal = ['terms', 'privacy', 'security', 'guidelines'].map(k => `<button class="li" data-a="openLegal" data-x="${k}"><span class="grow b" style="font-size:15px">${{ terms: 'Terms of Service', privacy: 'Privacy Policy', security: 'Security', guidelines: 'Community Guidelines' }[k]}</span><span class="chev">${ic('chevR', 18)}</span></button>`).join('');
  return {
    body: `<div class="topbtns">${backBtn()}</div><div class="title" style="margin-top:-6px">Settings</div>
 ${sectionCard('Profile', `<button class="li" data-a="openEditProfile">${pav('me', 40, 14)}<span class="grow"><span class="b" style="display:block;font-size:15px">${esc(PEOPLE.me.name)}</span><span class="muted b" style="font-size:13px">Photo, name, username, major, year</span></span><span class="chev">${ic('chevR', 18)}</span></button>`)}
 ${sectionCard('Account', `<div class="tc-row"><div class="muted b" style="font-size:13px">Signed in as</div><div class="b" style="font-size:15px;word-break:break-all">${esc(TC.email())}</div></div>
  <form class="tc-form" data-submit="setPw" style="margin-top:6px"><label>New password<input id="setpw" type="password" autocomplete="new-password" placeholder="At least 8 characters"></label>${UI.pwMsg ? `<div class="${UI.pwMsg.ok ? 'tc-ok' : 'tc-err'}">${esc(UI.pwMsg.t)}</div>` : ''}<button class="btn soft" ${UI.busy.pw ? 'disabled' : ''}>${UI.busy.pw ? 'Saving…' : 'Change password'}</button></form>`)}
 ${sectionCard('Who sees your plans', `<div class="muted b" style="font-size:13px;margin-bottom:4px">Friends can see a plan unless you turn it off.</div>${['A', 'B', 'C'].map(shareRow).join('')}`)}
 ${sectionCard('Blocked people', blocks === undefined ? loadingCard('Loading…') : TC.blocksErr ? '<div class="muted b">Couldn’t load that list.</div>' : blocks.length ? blocks.map(b => `<div class="row sb tc-row"><span class="b">${esc(b.display_name || b.username || 'Someone')}</span><button class="pbtn" data-a="unblock" data-x="${esc(b.id)}">Unblock</button></div>`).join('') : '<div class="muted b" style="padding:2px 0 10px">Nobody. Block someone from their profile on termchamp.com.</div>')}
 ${sectionCard('Legal', legal)}
 ${sectionCard('About', `<div class="muted b" style="font-size:13.5px;line-height:1.5">TermChamp phone app · build ${esc(window.TERMCHAMP_APP_BUILD || '')}<br>Ratings from PolyRatings and TermChamp students. Seats from Cal Poly’s public class search.</div>
  <a class="btn soft tc-a" style="margin-top:12px" href="${WEB}/" target="_blank" rel="noopener">Open TermChamp on the web</a>`)}
 <div class="pad" style="margin-top:16px;display:grid;gap:8px"><button class="btn soft" style="color:#B91C1C" data-a="signOut">Sign out</button>
  <div class="muted b" style="font-size:12.5px;text-align:center;line-height:1.45">To delete your account, use Settings on ${webLink('termchamp.com', '/')} — it shows exactly what gets deleted first.</div></div>
 <div class="spacer"></div>`, tabbar: true, fab: false
  };
};

SCREENS.legal = ({ which }) => {
  const d = window.TCPL && TCPL.legal[which];
  return { body: `<div class="topbtns">${backBtn()}</div><div class="title" style="margin-top:-6px">${esc(d ? d.title : 'Legal')}</div>
    <div class="card tc-legal">${d ? d.html : loadingCard('Loading…')}</div><div class="spacer"></div>`, tabbar: true, fab: false };
};

SCREENS.editProfile = () => {
  const f = UI.ep; const majors = window.TCPL ? TCPL.majors : [];
  const conc = (window.TCPL && f.major) ? TCPL.concInfo(f.major) : { known: false, list: [] };
  const opt = (v, cur, label) => `<option value="${esc(v)}" ${v === cur ? 'selected' : ''}>${esc(label || v)}</option>`;
  const photo = f.photo === 'remove' ? '' : f.photo && f.photo.url ? f.photo.url : safeImg(PEOPLE.me.avatar);
  return {
    body: `<div class="topbtns">${backBtn()}</div><div class="title" style="margin-top:-6px">Edit profile</div>
 <div class="card tc-sec"><div class="row" style="gap:16px">
   <span class="av" style="width:76px;height:76px;background:${PEOPLE.me.color};overflow:hidden;font-size:24px">${photo ? `<img src="${esc(photo)}" alt="" style="width:100%;height:100%;object-fit:cover">` : esc(initialsOf(f.display_name || PEOPLE.me.name))}</span>
   <div style="display:grid;gap:8px"><label class="pbtn pink" style="display:inline-grid;place-items:center;cursor:pointer">${photo ? 'Change photo' : 'Add a photo'}<input id="epfile" type="file" accept="image/png,image/jpeg,image/webp" data-in="epfile" hidden></label>${photo ? '<button class="pbtn" data-a="epRemovePhoto">Remove</button>' : ''}</div></div>
   ${f.photoErr ? `<div class="tc-err">${esc(f.photoErr)}</div>` : ''}</div>
 <form class="card tc-sec tc-form" data-submit="saveProfile" style="margin-top:12px">
  <label>Name<input id="ep-name" data-in="ep" data-k="display_name" value="${esc(f.display_name)}" maxlength="60" autocomplete="name"></label>
  <label>Username<input id="ep-user" data-in="ep" data-k="username" value="${esc(f.username)}" maxlength="20" autocapitalize="off" autocorrect="off" spellcheck="false"><span id="ep-usermsg" class="tc-hint ${f.userMsg && f.userMsg.bad ? 'bad' : f.userMsg && f.userMsg.good ? 'good' : ''}">${esc((f.userMsg && f.userMsg.t) || 'Letters, numbers and underscores · how friends find you')}</span></label>
  <label>Major<select data-in="ep" data-k="major">${opt('', f.major, 'Choose your major')}${f.major && majors.indexOf(f.major) < 0 ? opt(f.major, f.major) : ''}${majors.map(m => opt(m, f.major)).join('')}</select>${!window.TCPL ? '<span class="tc-hint">Loading the list of majors…</span>' : ''}</label>
  ${conc.list.length ? `<label>Concentration<select data-in="ep" data-k="concentration">${opt('', f.concentration, 'Not sure yet')}${conc.list.map(c => opt(c.name, f.concentration)).join('')}</select></label>` : ''}
  <label>Year<select data-in="ep" data-k="class_standing">${opt('', f.class_standing, 'Choose')}${STANDINGS.map(s => opt(s, f.class_standing)).join('')}</select></label>
  ${f.err ? `<div class="tc-err" role="alert">${esc(f.err)}</div>` : ''}
  <button class="btn" ${UI.busy.ep ? 'disabled' : ''}>${UI.busy.ep ? 'Saving…' : 'Save profile'}</button></form>
 <div class="spacer"></div>`, tabbar: true, fab: false
  };
};

/* ---- Planner ---- */
function yearTerm(n) { return n.year ? 'Year ' + n.year + (n.term ? ' · ' + n.term : '') : ''; }
function prereqBadge(code) {
  if (!UI.pl || !UI.pl.prereqs) return '';
  /* No record in course_prereqs is not the same as "no prerequisites" — say nothing then. */
  const rec = TCPL.coursePrereqs(code);
  if (!rec) return '';
  if (!rec.req || !rec.req.length) return '<span class="st" style="background:var(--bg);color:var(--muted)">No prerequisites</span>';
  const st = TCPL.prereqStatus(code, TCPL.completed(), [], [...myCodes()]);
  if (st.state === 'met') return '<span class="st" style="background:var(--teal-soft);color:var(--teal)">Ready to take</span>';
  if (st.state === 'inprogress') return '<span class="st" style="background:var(--blue-soft);color:var(--blue-ink)">After this term</span>';
  if (st.state === 'concurrent') return '<span class="st" style="background:var(--amber-soft);color:var(--amber-ink)">Take with a coreq</span>';
  return `<span class="st" style="background:#FCE7F3;color:var(--pink-ink)">Needs ${esc(st.missing.map(g => g.join(' or ')).slice(0, 2).join(', '))} first</span>`;
}
function plannerView() {
  const P = TC.profile || {};
  if (!UI.pl || UI.pl.state === 'loading') { openPlanner(); return loadingCard('Loading your degree…'); }
  if (UI.pl.state === 'failed') return errCard('Couldn’t load the planner.', 'retryPlanner');
  if (!P.major) return `<div class="card tc-sec" style="margin-top:14px"><div class="b" style="font-size:17px">Add your major</div><p class="muted b" style="font-size:14px;margin:6px 0 12px;line-height:1.45">Your requirements, what you still need and what you can take next all come from your major’s flowchart.</p><button class="btn" data-a="openEditProfile">Add your major</button></div>`;
  plSync();
  /* Every input the count depends on has to have arrived, or the number is wrong without looking it. */
  const missing = [TC.myHistory === undefined || TC.err.history ? 'your past classes' : '', TC.wavErr ? 'what you didn’t have to take' : '', TC.err.mine ? 'this term’s classes' : ''].filter(Boolean);
  if (missing.length) return errCard('Couldn’t load ' + missing.join(' and ') + ', so your requirements can’t be counted right now.', 'retryPlanner');
  const L = TCPL.ledger();
  if (!L) return `<div class="card tc-sec" style="margin-top:14px"><div class="b" style="font-size:17px">${esc(P.major)}</div><p class="muted b" style="font-size:14px;margin-top:6px;line-height:1.45">We don’t have this major’s flowchart yet, so we can’t check your requirements. Your past classes are below.</p></div>${historyCard()}`;
  const bar = r => { const pf = r.n ? Math.round(100 * r.f / r.n) : 0, pt = r.n ? Math.round(100 * r.t / r.n) : 0; return `<div class="tc-lrow"><span class="grow b">${esc(r.label)}</span><span class="b"><b style="font-size:16px">${r.f}</b> / ${r.n}${r.t ? `<small class="muted"> · ${r.t} in progress</small>` : ''}</span><span class="tc-lbar"><i style="width:${pf}%"></i><i class="now" style="width:${pt}%"></i></span></div>`; };
  const cantN = L.cant.length + L.concUnchosen;
  const conc = TCPL.concInfo(L.major);
  const concPick = L.concUnchosen && conc.list.length ? `<div class="tc-concpick"><div class="b" style="font-size:14.5px;margin-bottom:8px">Pick your concentration to load its classes</div><div style="display:flex;flex-wrap:wrap;gap:8px">${conc.list.map(c => `<button class="chip" style="background:var(--bg)" data-a="pickConc" data-x="${esc(c.name)}">${esc(c.name)}</button>`).join('')}</div></div>` : '';
  const needRows = L.need.map(n => {
    const code = n.codes.find(c => COURSES[c]) || n.codes[0];
    const offered = !!COURSES[code];
    return `<button class="li" data-a="${offered ? 'openClass' : 'plCourse'}" data-x="${esc(code)}"><span class="code">${esc(code)}</span><span class="grow" style="min-width:0"><span class="b" style="display:block;font-size:14.5px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis">${esc(n.title || course(code).title)}</span><span class="muted b" style="font-size:12.5px">${esc(yearTerm(n))} · ${offered ? 'offered ' + esc(CFG.TERM_LABEL) : 'not offered ' + esc(CFG.TERM_LABEL)}</span>${prereqBadge(code) ? `<span style="display:block;margin-top:5px">${prereqBadge(code)}</span>` : ''}</span>${offered ? `<span class="chev">${ic('chevR', 18)}</span>` : ''}</button>`;
  }).join('');
  const geRows = L.needU.map(n => n.type === 'ge'
    ? `<button class="li" data-a="plGe" data-x="${esc(n.area || '')}"><span class="code" style="background:var(--purple-soft);color:var(--purple-ink)">GE</span><span class="grow b" style="font-size:14.5px">${esc(n.title)}</span><span class="chev">${ic('chevR', 18)}</span></button>`
    : `<div class="li"><span class="code" style="background:var(--bg);color:var(--muted)">EL</span><span class="grow b" style="font-size:14.5px">${esc(n.title)}</span></div>`).join('');
  return `<div class="card tc-sec" style="margin-top:14px">
   <div class="muted b" style="font-size:13px">${esc(L.major)}${L.degree ? ', ' + esc(L.degree) : ''}${P.concentration ? ' · ' + esc(P.concentration) : ''}</div>
   <div style="margin:4px 0 10px"><span style="font-size:30px;font-weight:1000">${L.F} of ${L.N}</span> <span class="b">requirements filled</span></div>
   <div class="muted b" style="font-size:13px;margin:-6px 0 10px">${L.T ? L.T + ' in progress' : ''}${L.T && cantN ? ' · ' : ''}${cantN ? cantN + ' we can’t check' : ''}</div>
   ${L.rows.map(bar).join('')}
   ${cantN ? `<details class="tc-cant"><summary class="b">We can’t check ${cantN} from your record</summary><ul>${L.concUnchosen ? `<li><b>${esc(L.concLabel)} · ${L.concUnchosen} course${L.concUnchosen === 1 ? '' : 's'}</b>${L.concNote ? ' — ' + esc(L.concNote) : ''}</li>` : ''}${L.cant.map(sl => `<li>${esc(sl.title || 'Untitled requirement')}${sl.units != null ? ` <small>· ${esc(sl.units)} units</small>` : ''}</li>`).join('')}</ul></details>` : ''}
   ${concPick}
   <div class="muted b" style="font-size:12px;line-height:1.5;margin-top:10px">Filled means a course on your record is placed against a requirement — Cal Poly’s degree audit decides what’s complete.${L.src ? ` <a class="link" href="${esc(L.src)}" target="_blank" rel="noopener" style="color:var(--blue)">Official requirements</a>` : ''}</div></div>
  ${needRows ? sectionCard('Still need', needRows + (UI.pl.prereqs === false ? '<div class="muted b" style="font-size:12.5px;padding:8px 0">Prerequisites didn’t load, so readiness isn’t shown.</div>' : ''), `<span class="muted b" style="font-size:13px">${L.need.length}</span>`) : ''}
  ${geRows ? sectionCard('GE areas and electives', geRows, `<span class="muted b" style="font-size:13px">${L.needU.length}</span>`) : ''}
  ${gridCard(L)}
  ${historyCard()}`;
}
/* ---- the year-by-year grid: the flowchart, every slot in the state the ledger gave it ---- */
const CELL = { done: ['✓', 'var(--teal)', 'var(--teal-soft)', 'Done'], taking: ['◐', 'var(--blue-ink)', 'var(--blue-soft)', 'In progress'], need: ['', 'var(--muted)', 'var(--bg)', 'To do'], cant: ['?', 'var(--muted2)', 'var(--bg)', 'Can’t check'] };
function gridCard(L) {
  UI.plYears = UI.plYears || {};
  const years = [];
  L.grid.forEach(t => { let y = years.find(x => x.year === t.year); if (!y) years.push(y = { year: t.year, terms: [] }); y.terms.push(t); });
  const firstOpen = (years.find(y => y.terms.some(t => t.slots.some(s => s.state === 'need' || s.state === 'taking'))) || {}).year;
  const cell = s => {
    const c = CELL[s.state] || CELL.need, code = s.code ? (s.by || (s.codes && s.codes[0]) || s.code) : '';
    const act = s.state === 'need' && s.code ? `data-a="plLogSlot" data-x="${esc((s.codes && s.codes[0]) || s.code)}"`
      : s.state === 'need' && s.type === 'ge' ? `data-a="plGe" data-x="${esc(s.area || '')}"`
      : s.state === 'taking' && code && COURSES[code] ? `data-a="openClass" data-x="${esc(code)}"` : '';
    return `<${act ? 'button' : 'div'} class="tc-cell ${s.state}" ${act}><span class="tc-dot" style="color:${c[1]};background:${c[2]}" aria-label="${c[3]}">${c[0]}</span>
      <span class="grow" style="min-width:0"><span class="b tc-ctitle">${code ? `<span class="tc-ccode">${esc(code)}</span>` : ''}${esc(s.title)}</span>${s.state === 'cant' && s.note ? `<span class="muted b" style="font-size:12px;display:block">${esc(s.note)}</span>` : ''}</span>
      <span class="muted b" style="font-size:12px;flex:none">${s.units != null ? esc(s.units) + 'u' : ''}</span></${act ? 'button' : 'div'}>`;
  };
  const body = years.map(y => {
    const slots = y.terms.flatMap(t => t.slots), done = slots.filter(s => s.state === 'done').length, units = slots.reduce((a, s) => a + (+s.units || 0), 0);
    const cant = slots.filter(s => s.state === 'cant').length, judged = slots.length - cant;   // the same denominator as the ledger
    const open = UI.plYears[y.year] !== undefined ? UI.plYears[y.year] : y.year === firstOpen;
    return `<div class="tc-year"><button class="tc-yearh" data-a="plYear" data-x="${y.year}" aria-expanded="${open}"><span class="b" style="font-size:16px">Year ${y.year}</span><span class="grow muted b" style="font-size:13px;text-align:right">${done} of ${judged} done${cant ? ` · ${cant} can’t check` : ''} · ${units} units</span><span class="chev" style="transform:rotate(${open ? 90 : 0}deg)">${ic('chevR', 18)}</span></button>
      ${open ? y.terms.map(t => `<div class="tc-hterm">${esc(t.term)}</div>${t.slots.map(cell).join('')}`).join('') : ''}</div>`;
  }).join('');
  return sectionCard('Your flowchart', `<div class="muted b" style="font-size:12.5px;margin-bottom:6px">Tap a class you’ve taken to log it; tap a GE area to see this term’s classes for it.</div>${body}`);
}
function historyCard() {
  const h = (TC.myHistory || []).slice();
  const TO = { Winter: 0, Spring: 1, Summer: 2, Fall: 3 };
  h.sort((a, b) => (b.year || 0) - (a.year || 0) || (TO[b.term] || 0) - (TO[a.term] || 0));
  const groups = []; h.forEach(r => { const k = [r.term, r.year].filter(Boolean).join(' ') || 'Earlier'; const g = groups.find(x => x.k === k); if (g) g.rows.push(r); else groups.push({ k, rows: [r] }); });
  const w = Object.keys(TC.waived || {});
  const body = (TC.err.history ? '<div class="muted b">Couldn’t load your past classes.</div>' : '') +
    (groups.length ? groups.map(g => `<div class="tc-hterm">${esc(g.k)}</div>` + g.rows.map(r => `<div class="li"><span class="code">${esc(r.code)}</span><span class="grow" style="min-width:0"><span class="b" style="display:block;font-size:14.5px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis">${esc(course(canonCode(r.code) || r.code).title !== r.code ? course(canonCode(r.code) || r.code).title : '')}</span>${r.professor ? `<span class="muted b" style="font-size:12.5px">${esc(r.professor)}</span>` : ''}</span><button class="xbtn" data-a="askRemoveHistory" data-x="${esc(r.code)}" aria-label="Remove ${esc(r.code)}">${ic('x', 14, 2.4)}</button></div>`).join('')).join('') : '<div class="muted b" style="font-size:14px;padding:2px 0 10px">Nothing logged yet. Your past classes fill requirements here and bring those professors to Rate.</div>') +
    (w.length ? `<div class="tc-hterm">Didn’t have to take</div>` + w.map(c => `<div class="li"><span class="code">${esc(c)}</span><span class="grow muted b" style="font-size:13px">${esc(window.TCPL ? TCPL.waiveLabel(TC.waived[c]) : String(TC.waived[c]))}</span></div>`).join('') : '') +
    `<div class="row" style="gap:8px;margin-top:10px"><button class="btn soft grow" data-a="sheet" data-x="logClass">+ Log a class</button>
     <label class="btn soft grow tc-a" style="cursor:pointer">Import Degree Progress Report<input type="file" accept="application/pdf,.pdf" data-in="dprfile" hidden></label></div>
     <div class="muted b" style="font-size:12px;margin-top:6px;line-height:1.45">The PDF from the Cal Poly Portal. It’s read on your phone; only class codes and terms are saved — never your EMPLID or grades.</div>`;
  return sectionCard('Past classes', body, `<span class="muted b" style="font-size:13px">${h.length}</span>`);
}

/* ---- sheets ---- */
SHEETS.dpr = () => {
  const r = UI.dpr; if (!r) return '';
  if (r.busy) return `<h3>Degree Progress Report</h3>${loadingCard(r.busy)}`;
  if (r.err) return `<div class="row sb"><h3>Degree Progress Report</h3><button class="xbtn" data-a="closeSheet">${ic('x', 16, 2.4)}</button></div><div class="tc-err" style="margin-top:10px">${esc(r.err)}</div>`;
  const row = (x, i) => `<label class="tc-dprrow ${x.already ? 'dim' : ''}"><input type="checkbox" data-in="dprpick" data-i="${i}" ${x.pick ? 'checked' : ''} ${x.already || x.skip ? 'disabled' : ''}>
    <span class="code">${esc(x.cur)}</span><span class="grow" style="min-width:0"><span class="b" style="display:block;font-size:14px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis">${esc(String(x.name || x._title || '').replace(/^\(\d{4}\)\s*/, ''))}</span><span class="muted b" style="font-size:12px">${esc(x.term + ' ' + x.year)}${x.already ? (x._now ? ' · already in My Classes' : ' · already logged') : x.skip ? ' · ' + esc(x.skip) : ''}${x._xfer ? ' · transfer / AP' : ''}</span></span></label>`;
  const past = r.rows.map((x, i) => [x, i]).filter(([x]) => !x._now && !(x.skip && x._open)), now = r.rows.map((x, i) => [x, i]).filter(([x]) => x._now), later = r.rows.map((x, i) => [x, i]).filter(([x]) => x.skip && x._open);
  const n = r.rows.filter(x => x.pick && !x.already && !x.skip).length;
  return `<div class="row sb"><h3>Degree Progress Report</h3><button class="xbtn" data-a="closeSheet">${ic('x', 16, 2.4)}</button></div>
  <div class="muted b" style="font-size:13.5px;line-height:1.45;margin:4px 0 10px">Read straight from the PDF, so these are exact. Uncheck anything you don’t want.${r.program && r.program.major ? ` Your report lists <b>${esc(r.program.major)}</b>${r.program.conc ? ' · ' + esc(r.program.conc) : ''}.` : ''}</div>
  ${past.length ? `<div class="tc-hterm">Past classes · ${past.length}</div>${past.map(([x, i]) => row(x, i)).join('')}` : ''}
  ${now.length ? `<div class="tc-hterm">In progress · ${esc(r.latestTerm || '')}</div>${now.map(([x, i]) => row(x, i)).join('')}` : ''}
  ${later.length ? `<div class="tc-hterm">Registered for a later term · not added</div>${later.map(([x, i]) => row(x, i)).join('')}` : ''}
  ${r.skipped ? `<div class="muted b" style="font-size:12.5px;margin-top:8px">${r.skipped} row${r.skipped === 1 ? '' : 's'} on the report couldn’t be read and were left out.</div>` : ''}
  ${r.saveErr ? `<div class="tc-err">${esc(r.saveErr)}</div>` : ''}
  <button class="btn" style="margin-top:12px" data-a="dprSave" ${n && !UI.busy.dpr ? '' : 'disabled'}>${UI.busy.dpr ? 'Saving…' : n ? `Add ${n} class${n === 1 ? '' : 'es'}` : 'Nothing selected'}</button>`;
};
SHEETS.logClass = () => {
  const y = new Date().getFullYear(), f = UI.lc || {};
  return `<div class="row sb"><h3>Log a class</h3><button class="xbtn" data-a="closeSheet">${ic('x', 16, 2.4)}</button></div>
 <form class="tc-form" data-submit="logClass" style="margin-top:10px">
  <label>Class code<input id="lc-code" placeholder="e.g. BUS 3431" value="${esc(f.code || '')}" autocapitalize="characters" autocomplete="off" required></label>
  <div class="row" style="gap:10px"><label class="grow">Term<select id="lc-term">${['Fall', 'Winter', 'Spring', 'Summer'].map(t => `<option ${t === (f.term || 'Spring') ? 'selected' : ''}>${t}</option>`).join('')}</select></label>
  <label class="grow">Year<select id="lc-year">${Array.from({ length: 8 }, (_, i) => y + 1 - i).filter(v => v >= 2015).map(v => `<option ${v === (f.year || y) ? 'selected' : ''}>${v}</option>`).join('')}</select></label></div>
  <label>Professor <span class="muted" style="font-weight:600">(optional)</span><input id="lc-prof" value="${esc(f.prof || '')}" autocomplete="off" placeholder="First and last name"></label>
  ${f.err ? `<div class="tc-err">${esc(f.err)}</div>` : ''}
  <button class="btn" ${UI.busy.lc ? 'disabled' : ''}>${UI.busy.lc ? 'Saving…' : 'Add to past classes'}</button></form>`;
};
SHEETS.geArea = ({ area }) => {
  const list = (TCPL.geCourses || []).filter(g => g.areaKey === area);
  const label = list[0] && list[0].area ? list[0].area : 'GE Area ' + area;
  const offered = list.filter(g => COURSES[TCPL.canon(g.code)] || COURSES[g.code]);
  const rowOf = g => { const c = COURSES[TCPL.canon(g.code)] ? TCPL.canon(g.code) : g.code; const best = courseProfs(c).filter(p => ratingOf(p) != null).sort((a, b) => ratingOf(b) - ratingOf(a))[0];
    return `<button class="row" style="width:100%;padding:10px 0;border-top:1px solid var(--line)" data-a="openClass" data-x="${esc(c)}"><span class="code">${esc(c)}</span><span class="grow" style="min-width:0;text-align:left"><span class="b" style="display:block;font-size:14.5px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis">${esc(g.name || course(c).title)}</span><span class="muted b" style="font-size:12.5px">${best ? esc(profName(best)) + ' ★' + ratingOf(best).toFixed(1) : 'No rated professor'}</span></span>${courseBadge(c)}</button>`; };
  return `<div class="row sb"><h3>${esc(label)}</h3><button class="xbtn" data-a="closeSheet">${ic('x', 16, 2.4)}</button></div>
 <div class="muted b" style="font-size:13.5px;margin:4px 0 6px">${offered.length} of ${list.length} classes in this area are offered ${esc(CFG.TERM_LABEL)}.</div>
 ${offered.map(rowOf).join('') || '<div class="muted b" style="padding:8px 0">None offered this term.</div>'}`;
};
SHEETS.plCourse = ({ code }) => {
  const st = UI.pl && UI.pl.prereqs ? TCPL.prereqStatus(code, TCPL.completed(), [], [...myCodes()]) : null;
  const p = TCPL.coursePrereqs(code);
  return `<div class="row sb"><span class="code">${esc(code)}</span><button class="xbtn" data-a="closeSheet">${ic('x', 16, 2.4)}</button></div>
 <h3 style="margin-top:10px">${esc(course(code).title !== code ? course(code).title : code)}</h3>
 <div class="muted b" style="margin-top:6px">Not offered ${esc(CFG.TERM_LABEL)}. Next term’s classes post before registration.</div>
 ${p && p.req && p.req.length ? `<div class="b" style="margin-top:12px">Prerequisites: ${p.req.map(g => esc(g.join(' or '))).join('; ')}</div>` : st ? '<div class="b" style="margin-top:12px">No prerequisites.</div>' : ''}
 ${st && st.state === 'unmet' ? `<div class="muted b" style="margin-top:6px">Still needed: ${esc(st.missing.map(g => g.join(' or ')).join(', '))}</div>` : ''}`;
};
SHEETS.confirm = ({ title, body, yes, act, x }) => `<h3>${esc(title)}</h3><p class="muted b" style="font-size:14.5px;line-height:1.45;margin:8px 0 16px">${esc(body)}</p>
 <div class="row" style="gap:10px"><button class="btn soft" data-a="closeSheet">Cancel</button><button class="btn" style="background:#DC2626;box-shadow:none" data-a="${act}" data-x="${esc(x)}">${esc(yes)}</button></div>`;

/* ================= actions ================= */
Object.assign(A, {
  openMe: () => {
    UI.sheet = null; UI.champ = false;
    /* The degree line on this page is the same ledger the Planner shows, so it waits for the same
       inputs (waivers included) rather than showing a different number first. */
    Promise.all([TC.reloadMyReviews(), TC.loadPlanner(), TC.waived ? null : TC.loadWaivers(), TC.myHistory ? null : TC.reloadHistory()]).then(() => render(true));
    if (cur().s !== 'me') go('me');
  },
  openSettings: () => { TC.loadBlocks().then(() => render(true)); go('settings'); },
  openLegal: w => { TC.loadPlanner().then(() => render(true)); go('legal', { which: w }); },
  openEditProfile: () => {
    const P = TC.profile || {};
    UI.ep = { display_name: P.display_name || '', username: P.username || '', major: P.major || '', concentration: P.concentration || '', class_standing: P.class_standing || '', photo: null, err: '' };
    TC.loadPlanner().then(() => render(true)); go('editProfile');
  },
  epRemovePhoto: () => { UI.ep.photo = 'remove'; render(true); },
  scrollTo: id => { const el = document.getElementById(id); if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' }); },
  togglePlanShare: async k => { const on = TC.planShared[k] === false; const err = await TC.setPlanShared(k, on); if (err) { TC.planShared[k] = !on; toast(err); } else toast(on ? `Friends can see Plan ${k}` : `Plan ${k} is just yours`); render(true); },
  unblock: async id => { const e = await TC.unblock(id); toast(e || 'Unblocked'); render(true); },
  retryPlanner: () => { UI.pl = null; TC.myHistory = undefined; TC.waived = undefined; render(true); },
  pickConc: async name => {
    /* Just the one column — re-sending (and re-checking) the whole profile could fail over an old
       name the word filter now catches, with a message about something the student didn't touch. */
    const r = await TC.client().from('profiles').update({ concentration: name }).eq('id', TC.user.id).select('id');
    const e = r.error ? dbSay(r.error, 'Couldn’t save that.') : !(r.data || []).length ? 'Couldn’t save that — sign out and back in, then try again.' : null;
    if (!e) { TC.profile.concentration = name; concRemember(TC.profile.major, name); }
    toast(e || `Concentration set to ${name}`); render(true);
  },
  plGe: area => { if (!area) return toast('Any GE area counts for this one — see Explore'); UI.sheet = { type: 'geArea', area }; render(true); },
  plCourse: code => { UI.sheet = { type: 'plCourse', code }; render(true); },
  plYear: y => { UI.plYears = UI.plYears || {}; const cur = UI.plYears[y]; const el = document.querySelector(`[data-a="plYear"][data-x="${y}"]`); UI.plYears[y] = cur !== undefined ? !cur : !(el && el.getAttribute('aria-expanded') === 'true'); render(true); },
  plLogSlot: code => { UI.lc = { code }; UI.sheet = { type: 'logClass' }; render(true); },
  dprSave: async () => { if (UI.busy.dpr) return; UI.busy.dpr = 1; render(true); const e = await TC.saveDpr(UI.dpr); UI.busy.dpr = 0; if (e) { UI.dpr.saveErr = e; return render(true); } UI.sheet = null; UI.pl = null; render(true); },
  askRemoveHistory: code => { UI.sheet = { type: 'confirm', title: 'Remove ' + code + '?', body: 'It comes off your past classes and stops counting toward your requirements.', yes: 'Remove', act: 'removeHistory', x: code }; render(true); },
  removeHistory: async code => { UI.sheet = null; const e = await TC.removeHistory(code); toast(e || `Removed ${code}`); render(true); },
  editReview: id => {
    const v = (TC.myReviews || []).find(x => String(x.id) === String(id)); if (!v) return;
    let pk = reviewProfKey(v);
    if (!pk) { pk = profKeyOf(v.professor_name || String(v.professor_key).split('|')[0]); ensureProf(pk, v.professor_name); }
    const codes = v.course ? [v.course] : [];
    S.draft = { prof: pk, code: v.course || null, codes, term: '', stars: Math.round(+v.score || 0), diff: +v.difficulty || 0, again: v.would_again === true ? 'yes' : v.would_again === false ? 'no' : null,
      more: !!(v.grade || v.format || v.note || (v.tags || []).length), grade: v.grade || null, format: v.format || null, review: v.note || '', tags: (v.tags || []).slice(), err: '', editing: v.id };
    go('rateForm');
  },
  askDeleteReview: id => { const v = (TC.myReviews || []).find(x => String(x.id) === String(id)); UI.sheet = { type: 'confirm', title: 'Delete your review?', body: 'Your review of ' + ((v && v.professor_name) || 'this professor') + ' is removed for everyone. This can’t be undone.', yes: 'Delete', act: 'deleteReview', x: id }; render(true); },
  deleteReview: async id => { UI.sheet = null; const e = await TC.deleteReview(id); toast(e || 'Review deleted'); loadReviews().then(() => render(true)); render(true); }
});
/* Posting an EDIT reuses the rate form (the desktop's rule: the heading and button say which job). */
const _post = A.postRating;
A.postRating = async () => {
  const d = S.draft; if (!d || !d.editing) return _post();
  if (!d.stars || !d.code || UI.busy.rate) return;
  const words = wordCount(d.review); if (words > 300) { d.err = 'That’s ' + words + ' words — the limit is 300.'; return render(true); }
  const bad = wfHit(d.review || ''); if (bad) { d.err = 'Reviews are public, so “' + bad + '” can’t go in one.'; return render(true); }
  UI.busy.rate = 1; render(true);
  /* The class is fixed on an edit (the row's course_key moves with it on the desktop, and the phone
     doesn't write course_key), and a blank "take again" stays blank rather than becoming a no. */
  const patch = { score: d.stars, difficulty: d.diff || null, format: d.format || null, grade: d.grade || null, tags: (d.tags || []), note: (d.review || '').trim() || null };
  if (d.again === 'yes' || d.again === 'no') patch.would_again = d.again === 'yes';
  const e = await TC.updateReview(d.editing, patch);
  UI.busy.rate = 0;
  if (e) { d.err = e; return render(true); }
  S.draft = null; toast('Review updated'); loadReviews().then(() => render(true)); back();
};
Object.assign(SUBMIT, {
  setPw: async form => {
    const v = form.querySelector('#setpw').value; UI.busy.pw = 1; UI.pwMsg = null; render(true);
    const e = await TC.setPassword(v); UI.busy.pw = 0;
    UI.pwMsg = e ? { t: e } : { ok: 1, t: 'Password changed. Use it next time you sign in.' }; render(true);
  },
  saveProfile: async () => {
    const f = UI.ep; UI.busy.ep = 1; f.err = ''; render(true);
    const e = await TC.saveProfile(f); UI.busy.ep = 0;
    if (e) { f.err = e; return render(true); }
    UI.pl = null; toast('Profile saved'); back();
  },
  logClass: async form => {
    const code = canonCode(form.querySelector('#lc-code').value), term = form.querySelector('#lc-term').value, year = parseInt(form.querySelector('#lc-year').value, 10), prof = form.querySelector('#lc-prof').value.trim();
    UI.lc = { code: form.querySelector('#lc-code').value, term, year, prof, err: '' };
    if (!code) { UI.lc.err = 'Enter a class code like BUS 3431.'; return render(true); }
    UI.busy.lc = 1; render(true);
    const e = await TC.addHistory(code, term, year, prof); UI.busy.lc = 0;
    if (e) { UI.lc.err = e; return render(true); }
    UI.lc = null; UI.sheet = null; toast(`Added ${code}`); render(true);
  }
});

/* Edit profile: live field state, username availability, and the photo encoder. */
let epT;
document.addEventListener('input', ev => {
  const t = ev.target;
  if (t.dataset.in === 'ep' && UI.ep) {
    UI.ep[t.dataset.k] = t.value;
    if (t.dataset.k === 'major') { UI.ep.concentration = ''; render(true); }
    if (t.dataset.k === 'username') {
      const v = t.value.trim().replace(/^@/, ''), shape = userShape(v), msg = document.getElementById('ep-usermsg');
      const show = m => { UI.ep.userMsg = m; if (msg) { msg.textContent = m.t; msg.className = 'tc-hint ' + (m.bad ? 'bad' : m.good ? 'good' : ''); } };
      clearTimeout(epT);
      if (!shape.ok || !v) return show({ t: shape.msg, bad: !shape.ok });
      if (v.toLowerCase() === String((TC.profile && TC.profile.username) || '').toLowerCase()) return show({ t: 'This is your username.' });
      show({ t: 'Checking…' });
      epT = setTimeout(async () => { const tk = await TC.usernameTaken(v); if ((UI.ep.username || '').trim() !== v) return; show(tk === null ? { t: 'Couldn’t check that one — try saving.' } : tk ? { t: '@' + v + ' is taken.', bad: 1 } : { t: '@' + v + ' is available.', good: 1 }); }, 420);
    }
  }
});
document.addEventListener('change', async ev => {
  const t = ev.target;
  if (t.dataset.in === 'dprpick' && UI.dpr) { const x = UI.dpr.rows[+t.dataset.i]; if (x) x.pick = t.checked; render(true); return; }
  if (t.dataset.in === 'dprfile' && t.files && t.files[0]) {
    const file = t.files[0]; t.value = '';
    UI.dpr = { busy: 'Reading your report…' }; UI.sheet = { type: 'dpr' }; render(true);
    try { if (!await TC.loadPlanner()) throw new Error('pdf reader (planner) did not load'); if (TC.myHistory === undefined) await TC.reloadHistory(); UI.dpr = await readDpr(file); } catch (e) { UI.dpr = { err: /pdf/.test(String(e && e.message)) ? 'The PDF reader didn’t load — check your connection and try again.' : 'Couldn’t read that PDF. Download the report again from the Cal Poly Portal.' }; }
    render(true); return;
  } if (t.dataset.in === 'ep' && UI.ep && t.tagName === 'SELECT') { UI.ep[t.dataset.k] = t.value; if (t.dataset.k === 'major') UI.ep.concentration = ''; render(true); return; }
  if (t.dataset.in !== 'epfile' || !t.files || !t.files[0] || !UI.ep) return;
  const file = t.files[0];
  if (!/^image\/(png|jpe?g|webp)$/i.test(file.type || '')) { UI.ep.photoErr = 'Use a JPG, PNG or WebP photo.'; return render(true); }
  UI.ep.photoErr = '';
  try {
    const url = URL.createObjectURL(file);
    const img = await new Promise((res, rej) => { const i = new Image(); i.onload = () => res(i); i.onerror = rej; i.src = url; });
    const side = Math.min(img.naturalWidth, img.naturalHeight);
    const blob = await epEncodeSquare(img, (img.naturalWidth - side) / 2, (img.naturalHeight - side) / 2, side);   // centred square
    URL.revokeObjectURL(url);
    if (UI.ep.photo && UI.ep.photo.url) try { URL.revokeObjectURL(UI.ep.photo.url); } catch (x) {}
    UI.ep.photo = { blob, url: URL.createObjectURL(blob) };
  } catch (e) { UI.ep.photoErr = 'Couldn’t read that image — try another.'; }
  render(true);
});
