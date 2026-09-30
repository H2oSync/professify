/* ================================================================================================
   ONBOARDING — Sean's design (2026-09-29), on the real backend
   ------------------------------------------------------------------------------------------------
   Sean's 20-screen onboarding ("TermChamp onboarding" PDF + walkthrough), wired into the phone app.
   His styles are used as he wrote them (build/sean/sean-onboarding.css, scoped under .onb by
   build/sean/scope_css.py); his bird is swapped for our hawk (CHAMP). What runs underneath is the
   app's real sign-in and data, and Tate's calls (2026-09-29):
     · Reviews stay anonymous. "Who took this before you" and "Classmates" show FRIENDS only.
     · No age question — the school email and the year in school are enough (Tate). Password: 8+.
     · Username is required.
     · No "Graduating" (no column) and no notifications step until push alerts are live.
   Screens → where they live:
     01 landing · 02 sign up · 03 code · 20 log in · waitlist   → signed out (onbSignin)
     04 name + username (makes the profile row)                  → the noprofile phase
     05 this term · 06 DPR · 07 confirm · 08 add manually ·
     09 people · 11 "you're in"                                  → SCREENS.onb, inside the app
   ================================================================================================ */
const ONB_I = {
  back: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M15 5l-7 7 7 7"/></svg>',
  check: '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M5 12.5l4.5 4.5L19 7.5"/></svg>',
  checkW: '<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="3.4" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M5 12.5l4.5 4.5L19 7.5"/></svg>',
  chev: '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M9 6l6 6-6 6"/></svg>',
  mail: '<svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="3" y="5" width="18" height="14" rx="3"/><path d="M3.5 6.5l8.5 6.5 8.5-6.5"/></svg>',
  lock: '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="5" y="11" width="14" height="9" rx="2"/><path d="M8 11V8a4 4 0 0 1 8 0v3"/></svg>',
  file: '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8z"/><path d="M14 3v5h5"/></svg>',
  out: '<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M7 17L17 7M9 7h8v8"/></svg>',
  search: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#64748B" stroke-width="2.4" stroke-linecap="round" aria-hidden="true"><circle cx="11" cy="11" r="7"/><path d="m20 20-3.2-3.2"/></svg>',
  plus: '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" aria-hidden="true"><path d="M12 5v14M5 12h14"/></svg>'
};
/* Our hawk where Sean's sketch had a bird (Tate). */
const onbHawk = size => `<img class="onb-hawk" src="${CHAMP}" alt="" width="${size}" height="${Math.round(size * 1.17)}" style="width:${size}px;height:${Math.round(size * 1.17)}px;object-fit:contain;flex-shrink:0">`;
function onbTop(o) {
  o = o || {};
  const bar = o.progress ? `<div class="progress" role="progressbar" aria-label="Setup progress" aria-valuemin="0" aria-valuemax="4" aria-valuenow="${o.progress}">${[1, 2, 3, 4].map(n => `<i class="${n <= o.progress ? 'on' : ''}"></i>`).join('')}</div>` : '<div class="sp"></div>';
  return `<div class="top">${o.back === false ? '' : `<button type="button" class="back" data-a="onbBack">${ONB_I.back}Back</button>`}${bar}${o.right || ''}</div>`;
}
const onbMask = e => { const p = String(e || '').split('@'); return (p[0] || '').slice(0, 2) + '***@' + (p[1] || ''); };
const onbSchool = email => { const k = schoolForEmail(email || ''); return k ? Object.values(SCHOOLS).find(x => x.key === k) : null; };
const ONB_COLORS = ['#BFDBFE', '#FFD8B5', '#BBF7D0', '#DDD6FE', '#FDE68A', '#FBCFE8', '#C7F0F5'];
function onbAva(id, cls) {
  const p = PEOPLE[id] || { name: '?' }, img = safeImg(p.avatar);
  let h = 0; String(id).split('').forEach(c => { h = (h * 31 + c.charCodeAt(0)) >>> 0; });
  return `<div class="ava ${cls || ''}" style="background:${ONB_COLORS[h % ONB_COLORS.length]};overflow:hidden" aria-hidden="true">${img ? `<img src="${esc(img)}" alt="" style="width:100%;height:100%;object-fit:cover" onerror="this.remove()">` : esc(initialsOf(p.name))}</div>`;
}

/* ================================ signed out ================================ */
function onbSignin() {
  const si = UI.signin;
  if (TC.phase === 'noprofile') return onbUsername();
  if (TC.phase === 'otherschool') return onbWaitlist((TC.user && TC.user.email) || '', true);
  if (si.mode === 'signup') return onbSignup();
  if (si.mode === 'suVerify' || si.mode === 'verify') return onbVerify();
  if (si.mode === 'password') return onbLogin();
  if (si.mode === 'code') return onbCodeLogin();
  if (si.mode === 'waitlist') return onbWaitlist(si.email, false);
  if (si.mode === 'legal') return onbLegal();
  return `<div class="onb"><div class="scr landing"><div class="body">${onbHawk(76)}
    <div class="wordmark">TermChamp</div><h1 class="bigh">Plan your next term, stress-free.</h1>
    <p class="lead">See which friends took your classes before you, and who’s in them now.</p></div>
    <div class="foot">${si.err ? `<div class="hint bad" role="alert" style="justify-content:center">${esc(si.err)}</div>` : ''}
    <button type="button" class="btn" data-a="siMode" data-x="signup">Get started</button>
    <button type="button" class="ghost" data-a="siMode" data-x="password">I already have an account</button></div></div></div>`;
}
function onbEmailHint(email, touched) {
  const e = String(email || '').trim(), sc = onbSchool(e);
  if (sc && sc.key === 'calpoly') return { cls: 'ok', html: ONB_I.check + 'Student email recognized · Cal Poly', ok: true };
  if (sc) return { cls: '', html: esc(sc.short) + ' is coming soon — continue to join the list', ok: true };
  if (e && (touched || /@.+\..+/.test(e))) return { cls: 'bad', html: /\.edu$/i.test(e) ? 'TermChamp isn’t at your school yet. Right now it’s at Cal Poly.' : 'Use your school email. It ends in .edu.', ok: false };
  return { cls: '', html: '', ok: false };
}
function onbSignup() {
  const si = UI.signin, h = onbEmailHint(si.email, false), pwOk = String(si.pw || '').length >= 8;
  return `<div class="onb"><form class="scr" data-submit="signup" novalidate>${onbTop()}<div class="body">
    <div class="stack"><div class="kicker">Create your account</div><h1>Sign up with your school email</h1></div>
    <div class="field"><label class="label" for="su-email">School email</label><input class="input" id="su-email" data-su="email" type="email" inputmode="email" autocomplete="email" autocapitalize="off" spellcheck="false" placeholder="you@calpoly.edu" value="${esc(si.email)}"><div class="hint ${h.cls}" id="su-emailhint" aria-live="polite">${h.html}</div></div>
    <div class="field"><label class="label" for="su-pw">Password</label><div class="pwwrap"><input class="input" id="su-pw" data-su="pw" type="${si.showPw ? 'text' : 'password'}" autocomplete="new-password" placeholder="Make it memorable" value="${esc(si.pw || '')}"><button type="button" class="pill-pink showpw" data-a="suEye" aria-controls="su-pw" aria-pressed="${!!si.showPw}">${si.showPw ? 'Hide' : 'Show'}</button></div></div>
    <div class="card rules" aria-label="Password rules"><div style="font-weight:800;color:var(--ink)">Password must have:</div>
     <div class="rule ${pwOk ? 'ok' : ''}" id="su-r1"><i>${pwOk ? ONB_I.checkW : ''}</i>8 or more characters</div></div>
    <label class="check"><input type="checkbox" id="su-agree" data-su="agree" ${si.agree ? 'checked' : ''}><span>I agree to the <button type="button" class="plink" data-a="siLegal" data-x="terms">Terms</button>, <button type="button" class="plink" data-a="siLegal" data-x="privacy">Privacy Policy</button> and <button type="button" class="plink" data-a="siLegal" data-x="guidelines">Community Guidelines</button>.</span></label>
    <div class="hint bad" id="suErr" role="alert">${esc(si.err || '')}</div></div>
    <div class="foot"><button class="btn" id="su-go" type="submit" ${onbSignupReady() && !UI.busy.signin ? '' : 'disabled'}>${UI.busy.signin ? 'Sending…' : 'Send my code'}</button>
    <div class="ghost">Have an account? <button type="button" class="plink" data-a="siMode" data-x="password">Log in</button></div></div></form></div>`;
}
function onbSignupReady() { const si = UI.signin; return onbEmailHint(si.email, true).ok && String(si.pw || '').length >= 8 && !!si.agree; }
function onbVerify() {
  const si = UI.signin, login = si.mode === 'verify';
  return `<div class="onb"><form class="scr" data-submit="${login ? 'verify' : 'suVerify'}" novalidate>${onbTop()}<div class="body"><div class="tile">${ONB_I.mail}</div>
    <div class="stack"><h1>Check your email</h1><p class="lead">We sent a 6-digit code to <span style="color:var(--ink);font-weight:800">${esc(onbMask(si.email))}</span></p><div><button type="button" class="pill-pink" data-a="onbBack">Edit email</button></div></div>
    <div class="code6 ${si.err ? 'bad' : ''}" id="code6" role="group" aria-label="6-digit code">${[0, 1, 2, 3, 4, 5].map(i => `<input inputmode="numeric" pattern="[0-9]*" maxlength="${i === 0 ? 6 : 1}" aria-label="Digit ${i + 1}" value="${esc(String(si.code || '')[i] || '')}" ${i === 0 ? 'autocomplete="one-time-code"' : 'autocomplete="off"'}>`).join('')}</div>
    <div class="hint bad" id="codeErr" role="alert">${esc(si.err || '')}</div>
    ${si.note ? `<div class="hint ok" role="status">${esc(si.note)}</div>` : ''}
    <div id="resend" class="hint">${onbResendHtml()}</div>
    <div class="champrow">${onbHawk(52)}<div class="bubble">You’re almost there!</div></div></div>
    <div class="foot"><button type="submit" class="btn" id="code-go" ${String(si.code || '').length === 6 && !UI.busy.signin ? '' : 'disabled'}>${UI.busy.signin ? 'Checking…' : 'Verify'}</button></div></form></div>`;
}
function onbResendHtml() {
  const left = Math.max(0, Math.ceil(((UI.signin.resendAt || 0) - Date.now()) / 1000));
  return left ? `Didn’t get it? Resend in 0:${String(left).padStart(2, '0')}` : 'Didn’t get it? <button type="button" class="plink" data-a="suResend">Resend code</button>';
}
function onbLogin() {
  const si = UI.signin;
  return `<div class="onb"><form class="scr" data-submit="pw" novalidate>${onbTop()}<div class="body">
    <div class="stack"><div class="kicker">Welcome back</div><h1>Log in</h1></div>
    <div class="field"><label class="label" for="si-email">School email</label><input class="input" id="si-email" data-si="email" type="email" inputmode="email" autocomplete="email" autocapitalize="off" spellcheck="false" placeholder="you@calpoly.edu" value="${esc(si.email)}"></div>
    <div class="field"><label class="label" for="si-pw">Password</label><div class="pwwrap"><input class="input" id="si-pw" type="${si.showPw ? 'text' : 'password'}" autocomplete="current-password"><button type="button" class="pill-pink showpw" data-a="suEye" aria-controls="si-pw" aria-pressed="${!!si.showPw}">${si.showPw ? 'Hide' : 'Show'}</button></div></div>
    <div><button type="button" class="plink" data-a="siMode" data-x="code">Forgot password, or never set one? Email me a code</button></div>
    <div class="hint bad" role="alert">${esc(si.err || '')}</div></div>
    <div class="foot"><button class="btn" type="submit" ${UI.busy.signin ? 'disabled' : ''}>${UI.busy.signin ? 'Logging in…' : 'Log in'}</button>
    <div class="ghost">New here? <button type="button" class="plink" data-a="siMode" data-x="signup">Create an account</button></div></div></form></div>`;
}
function onbCodeLogin() {
  const si = UI.signin;
  return `<div class="onb"><form class="scr" data-submit="sendCode" novalidate>${onbTop()}<div class="body">
    <div class="stack"><div class="kicker">Welcome back</div><h1>Email me a code</h1><p class="lead">We’ll send a 6-digit code — no password needed. Set one later in Settings.</p></div>
    <div class="field"><label class="label" for="si-email">School email</label><input class="input" id="si-email" data-si="email" type="email" inputmode="email" autocomplete="email" autocapitalize="off" spellcheck="false" placeholder="you@calpoly.edu" value="${esc(si.email)}"></div>
    <div class="hint bad" role="alert">${esc(si.err || '')}</div></div>
    <div class="foot"><button class="btn" type="submit" ${UI.busy.signin ? 'disabled' : ''}>${UI.busy.signin ? 'Sending…' : 'Send my code'}</button>
    <div class="ghost">New here? <button type="button" class="plink" data-a="siMode" data-x="signup">Create an account</button></div></div></form></div>`;
}
function onbLegal() {
  const si = UI.signin, d = window.TCPL && TCPL.legal[si.doc];
  return `<div class="onb"><div class="scr">${onbTop()}<div class="body"><div class="card pad tc-legal" style="font-weight:600">${d ? `<h2 style="margin-top:0">${esc(d.title)}</h2>${d.html}` : si.legalFail ? `<div class="empty"><b>Couldn’t load that page.</b> Check your connection — it’s also linked at the bottom of ${webLink('termchamp.com', '/')}. <button type="button" class="plink" data-a="siLegal" data-x="${esc(si.doc)}">Try again</button></div>` : '<div class="empty" role="status">Loading…</div>'}</div></div></div></div>`;
}
/* SDSU and UCSB: "we're bringing TermChamp to your school" instead of a dead end. */
function onbWaitlist(email, signedIn) {
  const sc = onbSchool(email) || { short: 'your school' }, w = UI.wl || {}, done = w.for === email && w.ok;
  return `<div class="onb"><div class="scr landing">${signedIn ? '' : onbTop()}<div class="body">${onbHawk(64)}
    <h1>TermChamp is coming to ${esc(sc.short)}</h1>
    ${done ? `<div class="banner" role="status">${ONB_I.check}<span>${w.ok === 'already' ? 'You’re already on the list.' : 'You’re on the list!'} We’ll email ${esc(email)} when TermChamp opens at ${esc(sc.short)}.</span></div>`
      : `<p class="lead">We’re in the middle of bringing TermChamp to ${esc(sc.short)} — real ratings, open seats and your friends’ schedules. Want us to email you when it’s ready?</p>
      ${w.err && w.for === email ? `<div class="hint bad" role="alert">${esc(w.err)}</div>` : ''}`}
    <div class="lock"><span class="dot">${ONB_I.lock}</span><span>We’ll use <b>${esc(email)}</b> for that one email and nothing else.</span></div></div>
    <div class="foot">${done ? '' : `<button type="button" class="btn" data-a="joinWaitlist" ${UI.busy.wl ? 'disabled' : ''}>${UI.busy.wl ? 'Adding you…' : 'Join the list'}</button>`}
    <div class="ghost" style="font-size:13.5px">${signedIn ? 'Your account still works on' : 'Already have a TermChamp account? It still works on'} ${webLink('termchamp.com', '/')}.</div>
    ${signedIn ? '<button type="button" class="ghost" data-a="signOut">Sign out</button>' : ''}</div></div></div>`;
}

/* ============================ 04 · name + username ============================ */
function onbUsername() {
  const f = UI.ob = UI.ob || { first: '', last: '', username: '' }, m = f.userMsg;
  const ready = f.first.trim() && f.last.trim() && f.okFor && f.okFor === f.username && !UI.busy.ob;
  return `<div class="onb"><form class="scr" data-submit="onboard" novalidate><div class="top"></div><div class="body">
    <div class="stack"><div class="kicker teal">Email verified ✓</div><h1>Next, claim your username</h1><p class="lead">It’s how friends find and add you.</p></div>
    <div class="two"><div class="field"><label class="label" for="ob-first">First name</label><input class="input" id="ob-first" data-ob="first" autocomplete="given-name" value="${esc(f.first)}"></div>
    <div class="field"><label class="label" for="ob-last">Last name</label><input class="input" id="ob-last" data-ob="last" autocomplete="family-name" value="${esc(f.last)}"></div></div>
    <div class="field"><label class="label" for="ob-user">Username</label><div class="unwrap"><span class="at" aria-hidden="true">@</span><input class="input" id="ob-user" data-ob="username" autocapitalize="off" autocomplete="off" spellcheck="false" maxlength="20" value="${esc(f.username)}"><span class="st" id="ob-userst">${m && m.good ? ONB_I.check : ''}</span></div>
    <div class="hint ${m && m.bad ? 'bad' : m && m.good ? 'ok' : ''}" id="ob-usermsg" aria-live="polite">${m ? m.html || esc(m.t) : ''}</div><div class="hint">3–20 characters. Letters, numbers and underscores.</div></div>
    <div class="hint bad" id="ob-err" role="alert">${esc(f.err || '')}</div></div>
    <div class="foot"><button class="btn" id="ob-go" type="submit" ${ready ? '' : 'disabled'}>${UI.busy.ob ? 'Saving…' : 'Continue'}</button>
    <button type="button" class="ghost" data-a="signOut">Not you? Sign out</button></div></form></div>`;
}
function onbUserCheck() {
  const f = UI.ob; if (!f) return;
  const v = f.username, shape = userShape(v), msg = document.getElementById('ob-usermsg'), st = document.getElementById('ob-userst');
  const show = m => { f.userMsg = m; if (msg) { msg.innerHTML = m.html || esc(m.t); msg.className = 'hint ' + (m.bad ? 'bad' : m.good ? 'ok' : ''); } if (st) st.innerHTML = m.good ? ONB_I.check : ''; onbUserGate(); };
  clearTimeout(onbUserCheck.t); f.okFor = null;
  if (!v) return show({ t: '' });
  if (!shape.ok) return show({ t: shape.msg, bad: 1 });
  show({ t: 'Checking…' });
  onbUserCheck.t = setTimeout(async () => {
    const tk = await TC.usernameTaken(v); if (!UI.ob || UI.ob.username !== v) return;
    if (tk === true) {
      const alts = [v + '2', v.slice(0, 17) + '_tc', v + '27'].filter(a => a.length <= 20 && userShape(a).ok).slice(0, 2);
      show({ bad: 1, html: '@' + esc(v) + ' is taken. Try ' + alts.map(a => `<button type="button" class="plink" data-a="onbUseName" data-x="${esc(a)}">@${esc(a)}</button>`).join(' or ') });
    } else if (tk === null) { f.okFor = v; show({ t: 'Couldn’t check that one — we’ll check when you continue.' }); }
    else { f.okFor = v; show({ t: '@' + v + ' is available', good: 1 }); }
  }, 400);
}
function onbUserGate() { const f = UI.ob, b = document.getElementById('ob-go'); if (b && f) b.disabled = !(f.first.trim() && f.last.trim() && f.okFor && f.okFor === f.username && !UI.busy.ob); }

/* ============================ inside the app: 05–11 ============================ */
const ONB_TERMS = ['Summer 2026', 'Spring 2026', 'Winter 2026', 'Fall 2025', 'Summer 2025', 'Spring 2025', 'Winter 2025', 'Fall 2024', 'Summer 2024', 'Spring 2024', 'Winter 2024', 'Fall 2023', 'Spring 2023', 'Winter 2023', 'Fall 2022', 'Spring 2022', 'Winter 2022', 'Fall 2021'];
/* Onboarding survives closing the app: the step is remembered per account until "Start planning". */
const ONB_KEY = 'termchamp_app_onb';
function onbRemember(step) { try { if (step) localStorage.setItem(ONB_KEY, JSON.stringify({ u: TC.user.id, step })); else localStorage.removeItem(ONB_KEY); } catch (e) {} }
function onbResume() {
  let m = null; try { m = JSON.parse(localStorage.getItem(ONB_KEY) || 'null'); } catch (e) {}
  if (!m || !TC.user || m.u !== TC.user.id || !m.step) return;
  const st = S.stack.home; if (st.some(x => x.s === 'onb')) return;
  S.tab = 'home'; S.stack.home = [{ s: 'home' }, { s: 'onb', p: { step: m.step } }];
}
function onbGo(step) { onbRemember(step); const st = S.stack[S.tab], top = st[st.length - 1]; if (top && top.s === 'onb') top.p = { step }; else st.push({ s: 'onb', p: { step } }); UI.onbSheet = null; render(); const sc = document.getElementById('scroll'); if (sc) sc.scrollTop = 0; }
function onbMine() { return (TC.mineRows && TC.mineRows.saved) || []; }
function onbSecOf(code) { const r = ((TC.mineRows && TC.mineRows.secs) || []).find(x => canonCode(x.code) === code); return r ? r.section : ''; }
SCREENS.onb = ({ step }) => {
  const body = step === 'degree' ? onbDegree() : step === 'confirm' ? onbConfirm() : step === 'manual' ? onbManual() : step === 'people' ? onbPeople() : step === 'payoff' ? onbPayoff() : onbSchedule();
  return { body: `<div class="onb">${body}${UI.onbSheet ? onbSheet() : ''}</div>`, tabbar: false, fab: false };
};
/* 05 — no screenshot reader on the phone yet, so the classes go in by search (08), and the
   PASS screenshot import stays on termchamp.com for now. */
function onbSchedule() {
  const n = onbMine().length;
  return `<div class="scr">${onbTop({ progress: 1, back: false })}<div class="body">
    <div class="stack"><div class="kicker">Step 1 of 2 · About 30 sec</div><h1>Add this term’s schedule</h1><p class="lead">Add the classes you’re taking in ${esc(CFG.TERM_LABEL)}, then we show which friends are in them.</p></div>
    ${n ? `<div class="banner">${ONB_I.check}${n} ${n === 1 ? 'class' : 'classes'} already on your account</div>` : ''}
    <div class="card steps"><div class="label">Two ways</div>
     <div class="row"><div class="stepn">1</div><div><b style="font-weight:900">Search your classes</b> and pick your sections — takes a minute.</div></div>
     <div class="row"><div class="stepn">2</div><div>Or import a <b style="font-weight:900">schedule screenshot</b> on termchamp.com.</div></div>
     <a class="portal" href="${WEB}/" target="_blank" rel="noopener">Open termchamp.com${ONB_I.out}</a></div>
    <div class="lock"><span class="dot">${ONB_I.lock}</span>Only friends see your schedule.</div></div>
    <div class="foot"><button type="button" class="btn" data-a="onbStep" data-x="manual">${ONB_I.plus}Add my classes</button>
    <button type="button" class="ghost pink" data-a="onbStep" data-x="degree">${n ? 'Next' : 'Skip for now'}</button></div></div>`;
}
function onbDegree() {
  const n = onbMine().length, calpoly = schoolForEmail((TC.user && TC.user.email) || '') === 'calpoly';
  return `<div class="scr">${onbTop({ progress: 2 })}<div class="body">
    ${n ? `<div class="banner">${ONB_I.check}${n} ${n === 1 ? 'class' : 'classes'} this term</div>` : ''}
    <div class="stack"><div class="kicker">Step 2 of 2 · Recommended</div><h1>Add your Degree Progress Report</h1><p class="lead">This fills in the classes you’ve already taken, so we can help you pick what’s next.</p></div>
    <div class="card pad col"><div class="label">In Cal Poly’s portal</div><div class="crumbs"><span>Student Center</span><b>›</b><span>Academic Progress</span><b>›</b><span>DPR</span><b>›</b><span>Download PDF</span></div></div>
    <div class="lock"><span class="dot">${ONB_I.lock}</span>We read your classes on this phone. Your student ID and grades are never kept, and friends never see your grades.</div></div>
    <div class="foot">${calpoly ? `<label class="btn" style="cursor:pointer">${ONB_I.file}Upload PDF<input type="file" accept="application/pdf,.pdf" data-in="dprfile" hidden></label>` : ''}
    <button type="button" class="ghost" data-a="onbStep" data-x="confirm">Do this later</button></div></div>`;
}
function onbConfirm() {
  const P = TC.profile || {}, prog = UI.onbProgram || {}, live = window.TCPL;
  const majors = live ? TCPL.majors : [];
  const pre = (UI.onbPre = UI.onbPre || {});
  if (!('major' in pre)) { pre.major = P.major || (prog.major && majors.includes(prog.major) ? prog.major : ''); pre.fromDpr = !P.major && !!pre.major; }
  if (!('standing' in pre)) pre.standing = P.class_standing || '';
  if (!('conc' in pre)) pre.conc = P.concentration || '';
  const concs = live && pre.major ? TCPL.concInfo(pre.major) : { list: [] };
  const row = (k, label, v, required) => { const none = k === 'conc' && pre.major && !concs.list.length;
    const shown = none ? 'None for this major' : v || (k === 'conc' ? 'Not sure yet' : 'Pick one'), miss = !v && required;
    return `<button type="button" class="prow ${miss ? 'miss' : ''}" data-a="onbPick" data-x="${k}" ${none ? 'aria-disabled="true" disabled' : ''}><span class="k">${label}</span><span class="v">${esc(shown)}</span>${none ? '' : ONB_I.chev}</button>`; };
  const mine = onbMine(), past = (TC.myHistory || []).length, need = !(pre.standing && pre.major);
  if (!live && !UI.onbPlLoading && !UI.onbPlFail) { UI.onbPlLoading = 1; TC.loadPlanner().then(ok => { UI.onbPlLoading = 0; UI.onbPlFail = !ok; render(true); }); if (TC.myHistory === undefined) TC.reloadHistory().then(() => render(true)); }
  if (!live && UI.onbPlFail) return `<div class="scr">${onbTop({ progress: 2 })}<div class="body"><div class="stack"><h1>Does this look right?</h1></div>
    <div class="card empty" role="alert">The major list didn’t load — check your connection.<div style="height:10px"></div><button type="button" class="dash" data-a="onbRetryPl">Try again</button></div></div>
    <div class="foot"><button type="button" class="ghost" data-a="onbStep" data-x="people">Skip — add your major later in Settings</button></div></div>`;
  return `<div class="scr">${onbTop({ progress: 2 })}<div class="body">
    <div class="stack"><h1>Does this look right?</h1><p class="lead">${pre.fromDpr ? 'Your major is from your report. Tap anything to fix it.' : 'Fill these in so we can show the right classes.'}</p></div>
    <div class="card" style="overflow:hidden">${row('standing', 'Year', pre.standing, true)}${row('major', 'Major', pre.major, true)}${row('conc', 'Concentration', pre.conc, false)}</div>
    <div class="col"><div class="between"><div class="label row">This term${mine.length ? ' · ' + mine.length : ''} <span class="chip blue" style="letter-spacing:0;text-transform:none">${esc(CFG.TERM_LABEL)}</span></div><button type="button" class="dash" data-a="onbStep" data-x="manual">＋ Add</button></div>
    ${mine.length ? `<div class="clist">${mine.map(code => { const sec = onbSecOf(code); return `<div class="crow"><span class="code">${esc(code)}</span><span class="ct">${esc(course(code).title || '')}</span>${sec ? `<span class="s">Sec ${esc(sec)}</span>` : ''}<button type="button" class="x" data-a="onbRm" data-x="${esc(code)}" aria-label="Remove ${esc(code)}">×</button></div>`; }).join('')}</div>`
      : '<div class="card empty">No classes yet. Add them so friends in them can find you.</div>'}
    ${past ? `<div class="s" style="padding-left:4px">+ ${past} past ${past === 1 ? 'class' : 'classes'} on your record</div>` : ''}</div>
    <div class="hint bad" role="alert">${esc(UI.onbErr || '')}</div></div>
    <div class="foot">${need ? '<div class="hint" style="justify-content:center;padding-bottom:6px">Pick your year and major to continue.</div>' : ''}
    <button type="button" class="btn" data-a="onbConfirmDone" ${need || UI.busy.onb ? 'disabled' : ''}>${UI.busy.onb ? 'Saving…' : 'Looks good'}</button></div></div>`;
}
function onbSheet() {
  const sh = UI.onbSheet, pre = UI.onbPre || {};
  let opts = [], title = '';
  if (sh === 'standing') { title = 'Year in school'; opts = STANDINGS.map(v => [v, v]); }
  if (sh === 'major') { title = 'Major'; opts = (window.TCPL ? TCPL.majors : []).map(v => [v, v]); }
  if (sh === 'conc') { const c = window.TCPL && pre.major ? TCPL.concInfo(pre.major) : { list: [] }; title = 'Concentration'; opts = [['', 'Not sure yet']].concat(c.list.map(x => [x.name, x.name])); }
  const cur = sh === 'standing' ? pre.standing : sh === 'major' ? pre.major : pre.conc;
  return `<div class="scrim" data-a="onbPick" data-x=""></div><div class="sheet" role="dialog" aria-modal="true" aria-labelledby="onbShT"><div class="grab" aria-hidden="true"></div>
    <div class="sb"><h2 id="onbShT">${esc(title)}</h2><div class="opts ${sh === 'major' ? 'majorlist' : ''}" role="radiogroup">${opts.map(([v, l]) => `<button type="button" class="opt" role="radio" aria-checked="${v === cur}" data-a="onbSet" data-x="${esc(sh)}" data-y="${esc(v)}"><span class="rad"></span>${esc(l)}</button>`).join('')}</div></div>
    <div class="sf"><button type="button" class="ghost" data-a="onbPick" data-x="">Cancel</button></div></div>`;
}
/* 08 — search this term's real sections (the seat feed). Taking now writes saved_classes (+ the
   section to my_sections); Took before writes class_history, and asks when, because the row needs
   a term. Friend counts are friends only. */
function onbManualResults() {
  const now = (UI.onbTab || 'now') === 'now', q = String(UI.onbQ || '').trim().toLowerCase(), flat = q.replace(/\s+/g, '');
  const mine = new Set(onbMine()), took = new Set((TC.myHistory || []).map(h => canonCode(h.code)));
  const list = q ? Object.keys(COURSES).filter(c => c.toLowerCase().replace(/\s+/g, '').includes(flat) || String(COURSES[c].title || '').toLowerCase().includes(q)).sort().slice(0, 25) : [];
  const fr = (code, id) => TC.friends.filter(f => personSecs(f).some(s => id ? s.id === id : s.code === code)).length;
  const rows = list.map(code => {
    const have = now ? mine.has(code) : took.has(code), open = UI.onbExpand === code && !have;
    const right = have ? `<span class="chip soft">${ONB_I.check}${now ? (onbSecOf(code) ? ' Sec ' + esc(onbSecOf(code)) : ' Added') : ' Added'}</span>` : '<span class="plus" aria-hidden="true">＋</span>';
    const head = `<button type="button" class="rrow" data-a="onbExpand" data-x="${esc(code)}" ${have ? 'aria-disabled="true"' : ''} aria-expanded="${open}"><div><div class="t" style="font-size:15px;${open ? 'color:var(--coral)' : ''}">${esc(code)}</div><div class="s">${esc(COURSES[code].title || '')}</div></div>${right}</button>`;
    if (!open) return head;
    if (!now) return head + `<div class="secs"><div class="s">When did you take it?</div><div class="segpick">${ONB_TERMS.map(t => `<button type="button" data-a="onbTook" data-x="${esc(code)}" data-y="${t}">${t}</button>`).join('')}</div></div>`;
    const ss = secsOf(code);
    return head + `<div class="secs"><div class="s">Pick your section</div>${ss.map(s => { const n = fr(code, s.id);
      return `<button type="button" class="secbtn" data-a="onbAdd" data-x="${esc(code)}" data-y="${esc(s.id)}"><span><b style="font-weight:900">${esc(s.sec || '—')}</b> · ${esc(s.async ? 'Online' : s.noTime ? 'Time TBA' : daysLabel(s.days) + ' ' + range(s))}</span>${n ? `<span style="color:var(--teal);font-weight:800">${n} ${n === 1 ? 'friend' : 'friends'}</span>` : (s.status === 'full' || s.status === 'wait' ? `<span class="s">${s.status === 'wait' ? 'Waitlist' : 'Full'}</span>` : '')}</button>`; }).join('')}
      <button type="button" class="secbtn" data-a="onbAdd" data-x="${esc(code)}" data-y=""><span>Add without a section</span></button></div>`;
  }).join('');
  return !TC.seatsLoaded ? '<div class="card empty" role="status">Loading this term’s classes…</div>' : !q ? `<div class="card empty">Search by code or name${now ? ` — every ${esc(CFG.TERM_LABEL)} class is here` : ''}.</div>` : list.length ? `<div class="card res">${rows}</div>` : `<div class="card empty">No classes match “${esc(UI.onbQ)}”. Check the code, like ECON 2303.</div>`;
}
function onbManual() {
  const now = (UI.onbTab || 'now') === 'now', mine = new Set(onbMine());
  const added = now ? [...mine].map(c => [c, c + (onbSecOf(c) ? ' · ' + onbSecOf(c) : '')]) : (TC.myHistory || []).map(h => [canonCode(h.code), canonCode(h.code) + ' · ' + [h.term, h.year].filter(Boolean).join(' ')]);
  const n = mine.size;
  return `<div class="scr">${onbTop({ progress: 2 })}<div class="body">
    <div class="stack"><h1>Add your classes</h1><p class="lead">So friends in them can find you, and your planner fills in.</p></div>
    <div class="seg" role="tablist" aria-label="When"><button type="button" role="tab" aria-selected="${now}" data-a="onbTab" data-x="now">Taking now</button><button type="button" role="tab" aria-selected="${!now}" data-a="onbTab" data-x="took">Took before</button></div>
    <div class="search">${ONB_I.search}<input class="input" id="onb-q" data-onbq="1" type="search" aria-label="Search classes" placeholder="Search a class, like ECON 2303" value="${esc(UI.onbQ || '')}" autocomplete="off" enterkeyhint="search"></div>
    <div id="onb-results">${onbManualResults()}</div>
    ${UI.onbErr ? `<div class="hint bad" role="alert">${esc(UI.onbErr)}</div>` : ''}
    ${added.length ? `<div><div class="label" style="margin-bottom:8px">Added · ${added.length}</div><div class="addchips">${added.map(([c, l]) => `<span class="achip">${esc(l)}<button type="button" data-a="${now ? 'onbRm' : 'onbRmTook'}" data-x="${esc(c)}" aria-label="Remove ${esc(c)}">×</button></span>`).join('')}</div></div>` : ''}</div>
    <div class="foot"><button type="button" class="btn" data-a="onbStep" data-x="confirm">${n ? `Done · ${n} ${n === 1 ? 'class' : 'classes'}` : 'Done'}</button>
    <button type="button" class="ghost pink" data-a="onbStep" data-x="degree">Upload DPR too</button></div></div>`;
}
/* 09 — the app's own friend suggestions (suggest_friends; the server writes each reason). */
function onbPeople() {
  const sug = (TC.suggestions || []).filter(id => TC.relation(id) !== 'friends').slice(0, 8);
  const cls = sug.filter(id => /class|section/i.test(PEOPLE[id].sub || '')), rest = sug.filter(id => cls.indexOf(id) < 0);
  const row = id => { const p = PEOPLE[id], rel = TC.relation(id);
    return `<div class="li">${onbAva(id)}<div class="main"><div class="t">${esc(p.name)}</div>${p.sub ? `<div class="s ${cls.includes(id) ? 'blue' : ''}">${esc(p.sub)}</div>` : ''}</div>
      ${rel === 'sent' ? `<button type="button" class="done" data-a="addFriend" data-x="${id}" aria-label="Cancel friend request">${ONB_I.check}Requested</button>` : rel === 'incoming' ? `<button type="button" class="done" data-a="acceptReq" data-x="${id}">Accept</button>` : `<button type="button" class="dash" data-a="addFriend" data-x="${id}">＋ Add</button>`}</div>`; };
  return `<div class="scr">${onbTop({ progress: 3 })}<div class="body"><div class="stack"><h1>People you may know</h1><p class="lead">From your classes and your friends’ friends. They see your full schedule only once you’re friends.</p></div>
    ${cls.length ? `<div class="col"><div class="label">In your classes</div><div class="card list">${cls.map(row).join('')}</div></div>` : ''}
    ${rest.length ? `<div class="col"><div class="label">People you may know</div><div class="card list">${rest.map(row).join('')}</div></div>` : ''}
    ${!sug.length ? `<div class="card empty">No suggestions yet — they show up once classmates join. <div style="height:10px"></div><button type="button" class="dash" data-a="sheet" data-x="addFriend">Search by name or @username</button></div>` : ''}
    <div class="col"><button type="button" class="btn soft" data-a="copyInvite">Invite a friend</button></div></div>
    <div class="foot"><button type="button" class="btn" data-a="onbStep" data-x="payoff">Continue</button></div></div>`;
}
/* 11 — friends only (Tate): friends who took your classes, and friends in them this term. */
function onbPayoff() {
  const first = String((TC.profile && TC.profile.display_name) || '').split(/\s+/)[0] || 'there', mine = onbMine();
  const tookBy = TC.tookCode || {};
  const cards = mine.map(code => ({ code, who: (tookBy[code] || []).filter(id => TC.friends.includes(id)) })).filter(c => c.who.length).sort((a, b) => b.who.length - a.who.length).slice(0, 3);
  const mySec = {}; mine.forEach(c => { mySec[c] = onbSecOf(c); });
  const mates = []; TC.friends.forEach(f => { const s = personSecs(f).find(x => mine.includes(x.code)); if (s && mates.length < 4) mates.push({ id: f, code: s.code, same: !!mySec[s.code] && s.sec === mySec[s.code] }); });
  return `<div class="scr"><div class="top"></div><div class="body"><h1>You’re in, ${esc(first)}!</h1>
    <div class="col"><div class="label">Friends who took your classes</div>
    ${cards.length ? cards.map(c => { const lead = c.who[0], others = c.who.length - 1; return `<div class="card hcard"><div class="between"><button type="button" class="codechip" data-a="onbClass" data-x="${esc(c.code)}">${esc(c.code)}</button><span class="s">${esc(course(c.code).short || '')}</span></div>
      <div class="row">${onbAva(lead, 'sm')}<div style="flex:1;font-size:14.5px"><b style="font-weight:900">${esc(PEOPLE[lead].name)}</b>${others ? ` <span class="s" style="font-size:14.5px">and ${others} other ${others === 1 ? 'friend' : 'friends'}</span>` : ''}</div><span class="chip teal">Took it</span></div>
      <div class="between hfoot"><span class="s" style="font-size:14px">Ask them about it</span><button type="button" class="plink" style="min-height:36px" data-a="onbClass" data-x="${esc(c.code)}">See the class</button></div></div>`; }).join('')
      : `<div class="card empty">${TC.friends.length ? 'None of your friends has logged these classes yet.' : 'Once you and your friends connect, you’ll see who took your classes before you.'}</div>`}</div>
    ${mates.length ? `<div class="col"><div class="label">Friends in your classes</div><div class="card list">${mates.map(m => `<div class="li">${onbAva(m.id, 'sm')}<div class="main"><div class="t">${esc(PEOPLE[m.id].name)}</div><div class="s">${esc(m.code)} · ${m.same ? 'same section' : 'your class'}</div></div><span class="chip blue">Taking</span></div>`).join('')}</div></div>` : ''}
    <div class="row" style="align-items:flex-end"><button type="button" class="addcard" data-a="onbFinish" data-x="planner"><span class="pl">＋</span><span><span class="t" style="font-size:14.5px;display:block">Build my next term</span><span class="s">Prereqs, times and your friends</span></span></button>
    <div style="display:flex;flex-direction:column;align-items:center;gap:4px;flex-shrink:0"><span class="bubble" style="font-size:13px;padding:6px 12px;border-radius:14px 14px 4px 14px">Let’s go!</span>${onbHawk(48)}</div></div></div>
    <div class="foot"><button type="button" class="btn" data-a="onbFinish" data-x="home">Start planning!</button></div></div>`;
}

/* ================================ actions ================================ */
Object.assign(A, {
  onbBack: () => {
    const si = UI.signin;
    if (TC.phase !== 'ok') { si.err = ''; si.note = ''; si.mode = si.mode === 'suVerify' ? 'signup' : si.mode === 'verify' ? 'code' : si.mode === 'legal' ? 'signup' : si.mode === 'code' ? 'password' : 'start'; return render(); }
    const st = S.stack[S.tab], top = st[st.length - 1], order = ['schedule', 'degree', 'confirm', 'people', 'payoff'];
    const step = top && top.p && top.p.step; UI.onbErr = '';
    if (step === 'manual') return onbGo('confirm');
    onbGo(order[Math.max(0, order.indexOf(step) - 1)] || 'schedule');
  },
  siLegal: async doc => {
    UI.signin.mode = 'legal'; UI.signin.doc = doc; UI.signin.legalFail = false; render();
    if (!window.TCPL) { const ok = await TC.loadPlanner(); UI.signin.legalFail = !ok; render(); }
  },
  suEye: () => {
    UI.signin.showPw = !UI.signin.showPw;
    ['su-pw', 'si-pw'].forEach(id => { const el = document.getElementById(id); if (el) el.type = UI.signin.showPw ? 'text' : 'password'; });
    document.querySelectorAll('.onb .showpw').forEach(b => { b.textContent = UI.signin.showPw ? 'Hide' : 'Show'; b.setAttribute('aria-pressed', String(!!UI.signin.showPw)); });
  },
  suResend: async () => {
    const si = UI.signin, wait = Math.ceil(((si.resendAt || 0) - Date.now()) / 1000);
    if (wait > 0) { si.err = `Wait ${wait}s before asking for another code — there’s an hourly limit.`; si.note = ''; return render(); }
    si.err = ''; si.note = ''; UI.busy.signin = 1; render();
    const err = await TC.sendCode(si.email, si.mode === 'suVerify'); UI.busy.signin = 0;
    if (err) si.err = authFriendlyErr(err); else { si.note = 'New code sent. The older one stops working.'; si.resendAt = Date.now() + 60000; }
    render();
  },
  joinWaitlist: async () => {
    const email = TC.phase === 'otherschool' ? (TC.user && TC.user.email) || '' : UI.signin.email;
    if (UI.busy.wl) return; UI.busy.wl = 1; render();
    const r = await TC.joinWaitlist(email); UI.busy.wl = 0;
    UI.wl = { for: email, ok: r.ok || '', err: r.err || '' }; render();
  },
  onbUseName: v => { if (!UI.ob) return; UI.ob.username = v; const el = document.getElementById('ob-user'); if (el) el.value = v; onbUserCheck(); },
  onbStep: step => { UI.onbErr = ''; onbGo(step); },
  onbRetryPl: () => { UI.onbPlFail = false; render(true); },
  onbPick: k => { UI.onbSheet = k || null; render(true); },
  onbSet: (k, v) => { const pre = UI.onbPre = UI.onbPre || {}; if (k === 'major') { if (pre.major !== v) pre.conc = ''; pre.major = v; pre.fromDpr = false; } else if (k === 'standing') pre.standing = v; else pre.conc = v; UI.onbSheet = null; render(true); },
  onbConfirmDone: async () => {
    const pre = UI.onbPre || {}; if (UI.busy.onb || !pre.standing || !pre.major) return;
    UI.busy.onb = 1; UI.onbErr = ''; render(true);
    const patch = { class_standing: pre.standing, major: pre.major }; if (pre.conc) patch.concentration = pre.conc;
    const e = await TC.updateProfileFields(patch); UI.busy.onb = 0;
    if (e) { UI.onbErr = e; return render(true); }
    UI.pl = null; onbGo('people');
  },
  onbTab: t => { UI.onbTab = t; UI.onbExpand = null; render(true); },
  onbExpand: code => { UI.onbExpand = UI.onbExpand === code ? null : code; render(true); },
  onbAdd: async (code, secId) => { if (UI.busy.onb) return; UI.busy.onb = 1; UI.onbErr = ''; const e = await TC.addMyClass(code, secId || null); UI.busy.onb = 0; UI.onbErr = e || ''; UI.onbExpand = null; if (!e) toast(`Added ${code}`); render(true); },
  onbRm: async code => { if (UI.busy.onb) return; UI.busy.onb = 1; const e = await TC.removeMyClass(code); UI.busy.onb = 0; UI.onbErr = e || ''; render(true); },
  onbTook: async (code, when) => { const [term, year] = String(when).split(' '); if (UI.busy.onb) return; UI.busy.onb = 1; const e = await TC.addHistory(code, term, +year, null); UI.busy.onb = 0; UI.onbErr = e || ''; UI.onbExpand = null; if (!e) toast(`${code} added to your past classes`); render(true); },
  onbRmTook: async code => { if (UI.busy.onb) return; UI.busy.onb = 1; const e = await TC.removeHistory(code); UI.busy.onb = 0; UI.onbErr = e || ''; render(true); },
  onbClass: code => { S.stack.home = [{ s: 'home' }]; S.tab = 'explore'; S.stack.explore = [{ s: 'explore' }]; save(); A.openClass(code); },
  onbFinish: where => {
    onbRemember(null); S.stack.home = [{ s: 'home' }]; UI.onbPre = null; UI.onbProgram = null;
    if (where === 'planner') { S.tab = 'schedule'; S.schedTab = 'planner'; } else S.tab = 'home';
    save(); render();
  }
});
/* The report's sheet is the app's own; when it's saved during onboarding, carry on to "confirm". */
const onbDprSave = A.dprSave;
A.dprSave = async () => {
  const prog = UI.dpr && UI.dpr.program;
  await onbDprSave();
  const top = cur();
  if (!UI.sheet && top && top.s === 'onb' && top.p && top.p.step === 'degree') { UI.onbProgram = prog || null; if (UI.onbPre && !TC.profile.major) delete UI.onbPre.major; onbGo('confirm'); }
};

Object.assign(SUBMIT, {
  signup: async form => {
    const si = UI.signin;
    si.email = (form.querySelector('#su-email').value || '').trim(); si.pw = form.querySelector('#su-pw').value || ''; si.agree = form.querySelector('#su-agree').checked;
    const email = si.email;
    /* SDSU / UCSB: the phone app has only Cal Poly's classes — the waitlist, never an account. */
    if (eduOk(email) && schoolForEmail(email) !== 'calpoly') { si.mode = 'waitlist'; si.pw = ''; si.err = ''; return render(); }
    si.err = !eduOk(email) ? 'Use your Cal Poly email — that’s how we keep ratings real.'
      : si.pw.length < 8 ? `Your password needs ${8 - si.pw.length} more character${8 - si.pw.length === 1 ? '' : 's'}.`
      : !si.agree ? 'Tick the box to agree to the Terms, Privacy Policy and Community Guidelines.' : '';
    if (si.err) return render();
    /* Back from the code screen with the same address: the code already sent still works, and a
       second request inside the limit would only be refused. */
    if (si.sentTo === email && Date.now() - (si.sentAt || 0) < 10 * 60 * 1000) { Object.assign(si, { mode: 'suVerify', err: '', note: 'Use the code we already sent — it still works.' }); return render(); }
    UI.busy.signin = 1; render();
    const err = await TC.sendCode(email, true); UI.busy.signin = 0;
    if (err) { si.err = authFriendlyErr(err); return render(); }
    Object.assign(si, { mode: 'suVerify', err: '', note: '', code: '', sentTo: email, sentAt: Date.now(), resendAt: Date.now() + 60000 });
    render();
  },
  suVerify: async form => {
    const si = UI.signin, code = onbCode(form);
    if (code.length < 6 || UI.busy.signin) return;
    UI.busy.signin = 1; si.err = ''; si.note = ''; render();
    const pw = si.pw; si.pw = '';                     // out of memory the moment it's handed over
    const r = await TC.signUpVerify(si.email, code, pw); UI.busy.signin = 0;
    if (r.err) { si.pw = pw; si.code = ''; si.err = /expired|invalid|token/i.test(r.err) ? 'That code is wrong or expired. Check your newest email or resend it.' : authFriendlyErr(r.err); return render(); }
    if (r.pwNote) toast(r.pwNote);
  },
  onboard: async form => {
    const f = UI.ob; if (!f || UI.busy.ob) return;
    f.first = form.querySelector('#ob-first').value.trim(); f.last = form.querySelector('#ob-last').value.trim(); f.username = form.querySelector('#ob-user').value.trim().replace(/^@/, '').toLowerCase();
    const name = (f.first + ' ' + f.last).replace(/\s+/g, ' ').trim(), bad = wfHit(name), shape = userShape(f.username);
    f.err = !f.first || !f.last ? 'Add your first and last name — it’s what friends see.'
      : bad ? '“' + bad + '” can’t be in your name — it shows next to you everywhere in the app.'
      : !f.username ? 'Pick a username — it’s how friends find you.'
      : !shape.ok ? shape.msg : '';
    if (f.err) return render();
    UI.busy.ob = 1; render();
    const tk = await TC.usernameTaken(f.username);
    if (tk === true) { UI.busy.ob = 0; f.err = '@' + f.username + ' is taken — pick another.'; f.okFor = null; return render(); }
    const err = await TC.createProfile({ display_name: name, username: f.username });
    UI.busy.ob = 0;
    if (err) { f.err = err; return render(); }
    UI.ob = null; UI.onbPre = null;
    S.tab = 'home'; S.stack.home = [{ s: 'home' }, { s: 'onb', p: { step: 'schedule' } }]; onbRemember('schedule');
    TC._loading = null; TC.load();
  }
});
function onbCode(form) { const c = [...(form || document).querySelectorAll('.code6 input')].map(i => i.value).join('').replace(/\D/g, '').slice(0, 6); UI.signin.code = c; return c; }

/* ---- live form behaviour (no re-render, so the caret stays put) ---- */
document.addEventListener('input', ev => {
  const t = ev.target;
  if (t.dataset.si === 'email') { UI.signin.email = t.value.trim(); return; }
  if (t.dataset.su) {
    const si = UI.signin, k = t.dataset.su;
    if (k === 'agree') si.agree = t.checked; else si[k] = k === 'email' ? t.value.trim() : t.value;
    const h = document.getElementById('su-emailhint'), hint = onbEmailHint(si.email, false);
    if (h && k === 'email') { h.innerHTML = hint.html; h.className = 'hint ' + hint.cls; }
    const r = document.getElementById('su-r1'), ok = String(si.pw || '').length >= 8;
    if (r) { r.classList.toggle('ok', ok); r.querySelector('i').innerHTML = ok ? ONB_I.checkW : ''; }
    const b = document.getElementById('su-go'); if (b) b.disabled = !onbSignupReady() || !!UI.busy.signin;
    return;
  }
  if (t.dataset.ob && UI.ob) {
    const k = t.dataset.ob, f = UI.ob;
    if (k === 'username') { const c = t.value.toLowerCase().replace(/^@/, '').replace(/\s/g, ''); if (c !== t.value) t.value = c; f.username = c; f.typed = true; onbUserCheck(); }
    else { f[k] = t.value; if (!f.typed) { f.username = (f.first + f.last).toLowerCase().replace(/[^a-z0-9_]/g, '').slice(0, 20); const u = document.getElementById('ob-user'); if (u) u.value = f.username; onbUserCheck(); } }
    onbUserGate(); return;
  }
  if (t.dataset.onbq) { UI.onbQ = t.value; UI.onbExpand = null; clearTimeout(onbQT); onbQT = setTimeout(() => { const r = document.getElementById('onb-results'); if (r) r.innerHTML = onbManualResults(); }, 150); return; }   // the input stays put, so the keyboard does too
  if (t.closest && t.closest('.code6')) {
    const box = [...t.closest('.code6').querySelectorAll('input')], i = box.indexOf(t), d = t.value.replace(/\D/g, '');
    const err = document.getElementById('codeErr'); if (err) err.textContent = ''; t.closest('.code6').classList.remove('bad');
    if (d.length > 1 && i === 0 && d.length >= 4) { box.forEach(b => { b.value = ''; }); d.slice(0, 6).split('').forEach((x, k) => { if (box[k]) box[k].value = x; }); (box[Math.min(d.length, 5)] || t).focus(); }   // autofill / a pasted code
    else if (d.length > 1) { t.value = d.slice(-1); if (box[i + 1]) box[i + 1].focus(); }
    else { t.value = d; if (d && box[i + 1]) box[i + 1].focus(); }
    onbCodeSync(t.closest('form'));
  }
});
let onbQT;
function onbCodeSync(form) {
  const b = document.getElementById('code-go'), n = onbCode(form).length; if (b) b.disabled = n !== 6 || !!UI.busy.signin;
  if (n === 6 && form && !UI.busy.signin) { const h = SUBMIT[form.dataset.submit]; if (h) h(form); }
}
/* Android keyboards report Backspace as "Unidentified", so the empty-box step back also listens
   for beforeinput's deleteContentBackward. */
document.addEventListener('beforeinput', ev => {
  const t = ev.target; if (!(t.closest && t.closest('.code6')) || ev.inputType !== 'deleteContentBackward' || t.value) return;
  const box = [...t.closest('.code6').querySelectorAll('input')], i = box.indexOf(t);
  if (box[i - 1]) { box[i - 1].value = ''; box[i - 1].focus(); ev.preventDefault(); onbCodeSync(t.closest('form')); }
});
document.addEventListener('focusin', ev => { const t = ev.target; if (t.closest && t.closest('.code6') && t.value) try { t.select(); } catch (e) {} });   // type over a filled box
document.addEventListener('keydown', ev => {
  if (ev.key === 'Escape' && UI.onbSheet) { UI.onbSheet = null; render(true); return; }
  const t = ev.target; if (!(t.closest && t.closest('.code6')) || ev.key !== 'Backspace' || t.value) return;
  const box = [...t.closest('.code6').querySelectorAll('input')], i = box.indexOf(t);
  if (box[i - 1]) { box[i - 1].value = ''; box[i - 1].focus(); ev.preventDefault(); onbCodeSync(t.closest('form')); }
});
document.addEventListener('paste', ev => {
  const t = ev.target; if (!(t.closest && t.closest('.code6'))) return;
  const d = ((ev.clipboardData && ev.clipboardData.getData('text')) || '').replace(/\D/g, ''); if (!d) return;
  ev.preventDefault(); const box = [...t.closest('.code6').querySelectorAll('input')];
  box.forEach(b => { b.value = ''; }); d.slice(0, 6).split('').forEach((x, k) => { if (box[k]) box[k].value = x; }); (box[Math.min(d.length, 5)] || t).focus(); onbCodeSync(t.closest('form'));
});
/* The resend countdown ticks without re-rendering the code boxes. */
setInterval(() => { const r = document.getElementById('resend'); if (r && (UI.signin.mode === 'suVerify' || UI.signin.mode === 'verify')) r.innerHTML = onbResendHtml(); }, 1000);
