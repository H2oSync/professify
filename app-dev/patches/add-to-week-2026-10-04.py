#!/usr/bin/env python3
r"""Add to your week: one full-screen place to add a section to My Classes or Plan A–C, with the
class going in lit and the rest of that week greyed out (Tate, 2026-10-04).

  Tate: "lets rework how add to plan works also we need to be able to easily add to My Classes fall and
  spring. When adding a class it should be kind of animated where everything else on the schedule is dark
  and this is the light ... make sure the size of the schedule is right horizontally ... make sure the colors
  are right for plans. also clean up the top where it says the class day time and professor."
  Canvas "Add a Class Options" → "i like how option 2 looks and feels. but lets keep the light theme"
  → "okay implment it". Then his five add-ons ("do these"):
    1. Undo, not Done: after it drops in, the screen closes by itself with "Added to Plan A · Undo".
    2. My Classes asks Enrolled or Waitlisted on a full section (+ an optional waitlist spot), and a
       waitlisted class is a dashed gold block, as on the desktop (`status:'waitlisted'`, `wl_pos`).
    3. Clashes: a plan refuses one (as before); My Classes warns and offers "Add anyway".
    4. Friends in that section under the class ("Avery and Sky are in this section").
    5. It opens where the section already is (with Remove), else where you last added.
  And it honours Reduce Motion.

  · Replaces SHEETS.addPlan. The class page's + still calls addPlanSheet(id).
  · My Classes = this term (CFG.TERM). Another term's chip shows but can't take a section from this
    term ("This is a Fall 2026 section…" / "…sections aren't posted yet").
  · A same-class section already in My Classes: "Swap for Sec 02", or "Keep both" (a lecture + lab are
    the same code). A swap writes the new row first, then deletes the old class number.
  · Undo for My Classes puts back that class's own rows exactly as they were (TC.restoreMyCode).
  · The week is at Home's width (12 / 8 / 26 / 5). Colours: the place's own — Plan A teal, B orange,
    C rose, My Classes blue.
  · Animations play once per change (`seq`), not again when a background load redraws the screen.

Usage: python3 add-to-week-2026-10-04.py <repo-dir>. Every anchor must match exactly once.
"""
import sys, os, re
p = os.path.join(sys.argv[1], 'app', 'index.html')
s = open(p, encoding='utf-8').read()

def rep(a, b):
    global s
    n = s.count(a)
    if n != 1: sys.exit(f'anchor matched {n}x: {a[:90]}')
    s = s.replace(a, b)

# ---------------------------------------------------------------- CSS
rep(".ap-note{margin-top:10px;font-size:14px;font-weight:800;color:var(--muted)}\n",
""".ap-note{margin-top:10px;font-size:14px;font-weight:800;color:var(--muted)}
/* ---- Add to your week (2026-10-04): a full screen over the app, in the light theme ---- */
.dest-mine{--pc:#2563EB;--pc-soft:#E3ECFF;--pc-soft2:#D6E4FF;--pc-ink:#1E40AF;--pc-glow:rgba(37,99,235,.3)}
.fullpg{position:absolute;inset:0;z-index:35;background:var(--bg);overflow-y:auto;overscroll-behavior:contain;animation:atEnter .42s cubic-bezier(.2,.8,.2,1) both}
.fullpg.re{animation:none}
.addto{display:flex;flex-direction:column;min-height:100%;padding-top:calc(var(--sb) + 2px)}
.at-top{display:flex;align-items:center;justify-content:space-between;padding:0 12px 0 20px;min-height:48px}
.at-kick{font-size:12px;font-weight:900;letter-spacing:.1em;color:var(--muted)}
.at-head{padding:2px 20px 0}
.at-code{display:flex;align-items:baseline;gap:10px;flex-wrap:wrap;font-size:26px;font-weight:900;letter-spacing:-.01em;color:var(--ink);line-height:1.15}
.at-sec{font-size:15px;font-weight:900;padding:3px 9px;border-radius:9px;background:var(--blue-soft);color:var(--blue-ink)}
.at-title{font-size:17px;font-weight:800;margin-top:3px;color:var(--ink2)}
.at-facts{display:flex;flex-wrap:wrap;align-items:center;gap:2px 6px;margin-top:6px;font-size:14px;font-weight:800;color:#475569}
.at-ppl{display:flex;align-items:center;gap:8px;margin-top:10px;font-size:14px;font-weight:800;color:var(--ink3)}
.at-ppl b{font-weight:900;color:var(--ink)}
.at-pick{padding:0 12px;margin-top:16px}
.at-seg{display:flex;padding:4px;border-radius:999px;background:#E9EDF5}
.at-seg button{flex:1;display:flex;align-items:center;justify-content:center;text-align:center;height:40px;border-radius:999px;border:0;background:transparent;font-weight:900;font-size:14.5px;color:var(--muted);transition:background .25s,color .25s,box-shadow .25s}
.at-seg button.on{background:#fff;color:var(--ink);box-shadow:0 2px 8px rgba(15,23,42,.1)}
.at-chips{display:flex;gap:8px;margin-top:10px}
.at-chip{flex:1;min-width:0;display:flex;align-items:center;justify-content:center;gap:6px;height:44px;padding:0 8px;border-radius:999px;border:0;background:#fff;color:var(--ink3);font-weight:900;font-size:14.5px;white-space:nowrap;box-shadow:0 1px 2px rgba(15,23,42,.06);transition:background .3s,color .3s,box-shadow .3s}
.at-chip .pdot{margin-right:0;flex:none}
.at-chip.on{background:var(--pc);color:#fff;box-shadow:0 6px 16px var(--pc-glow)}
.at-chip.on .pdot{background:#fff}
.at-chip.dis{color:var(--muted)}
.at-chip.dis .pdot{background:#CBD5E1}
.at-chip.on.dis{background:#E2E8F0;color:var(--ink3);box-shadow:none}
.at-chip svg{flex:none}
.at-status{display:flex;align-items:center;flex-wrap:wrap;gap:8px 10px;margin:12px 4px 0;font-size:14px;font-weight:800;color:var(--ink3)}
.at-status .at-seg{flex:1;min-width:210px}
.at-status .at-seg button{height:36px;font-size:14px}
.at-wl{display:flex;align-items:center;gap:6px;font-size:14px;font-weight:800;color:var(--muted)}
.at-wl input{width:64px;height:40px;border-radius:12px;border:1.5px solid #CBD5E1;background:#fff;text-align:center;font:800 16px Nunito,system-ui,sans-serif;color:var(--ink)}
.at-week{margin:14px 12px 0;padding:12px 0 10px;border-radius:24px;background:var(--card);box-shadow:0 1px 2px rgba(15,23,42,.04),0 8px 24px rgba(22,51,107,.07)}
.at-week .empty{padding:28px 18px}
.addto .grid{padding:0 8px;--glab:26px;--ggap:5px}
.addto .g-b{background:var(--pc-soft2);color:var(--pc-ink)}
.addto .g-col{transition:background .45s ease}
.addto.spot .g-col{background:#F1F3F7}
.addto.spot .g-day.hi{color:var(--pc)}
.addto.spot .g-b:not(.ghost):not(.clashb):not(.repl){background:#ECEFF4;color:#A0ABBB;box-shadow:none;border-color:transparent}
.addto .g-b.clashb{background:#FEE2E2;color:#B91C1C;box-shadow:inset 0 0 0 2px #DC2626}
.addto .g-b.repl{background:transparent;color:#64748B;border:2px dashed #94A3B8;box-shadow:none}
.addto .g-b.ghost{background:var(--pc);color:#fff;box-shadow:0 0 0 2.5px #fff,0 6px 18px var(--pc-glow);border:0;opacity:1;overflow:visible;z-index:3}
.addto.spot .g-b.ghost.clash{background:#DC2626;color:#fff;box-shadow:0 0 0 2.5px #fff,0 6px 18px rgba(220,38,38,.35)}
.addto.done .g-b.ghost{background:var(--pc-soft2);color:var(--pc-ink);box-shadow:inset 0 0 0 2px var(--pc)}
.addto.spot:not(.adding) .g-b.ghost:not(.clash)::before{content:'';position:absolute;inset:-3px;border-radius:10px;border:2px solid var(--pc);pointer-events:none;animation:atHalo 1.6s cubic-bezier(.2,.8,.2,1) .45s infinite}
.addto.spot .g-col:has(> .g-b.ghost:not(.clash))::before{content:'';position:absolute;inset:0;border-radius:inherit;pointer-events:none;background:linear-gradient(180deg,transparent 0%,color-mix(in srgb,var(--pc) 7%,transparent) 24%,color-mix(in srgb,var(--pc) 15%,transparent) 42%,color-mix(in srgb,var(--pc) 7%,transparent) 62%,transparent 84%);transform-origin:50% 42%}
.addto.added .g-b.ghost::after{content:'';position:absolute;top:-6px;right:-6px;width:16px;height:16px;border-radius:50%;background:#16A34A url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%23fff' stroke-width='4' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='m5 12 5 5 9-10'/%3E%3C/svg%3E") center/9px no-repeat;box-shadow:0 0 0 2px #fff}
.addto.fx.spot:not(.adding) .g-b.ghost{animation:atLit .6s cubic-bezier(.2,.8,.2,1) both}
.addto.fx.spot .g-b:not(.ghost):not(.clashb):not(.repl){animation:atDim .45s ease both}
.addto.fx.spot .g-col:has(> .g-b.ghost:not(.clash))::before{animation:atBeam .6s cubic-bezier(.2,.8,.2,1) both}
.addto.fx.adding .g-b.ghost{animation:atDrop .6s cubic-bezier(.2,.8,.2,1) both}
.addto.fx.adding .g-b.repl{animation:atOut .4s ease both}
.addto.fx.added .g-b.ghost{animation:atPop .45s cubic-bezier(.2,.8,.2,1) both}
.addto.fx.added .g-b.ghost::after{animation:atCheck .4s cubic-bezier(.2,.8,.2,1) .1s both}
.addto.fx.added .g-b:not(.ghost){animation:atUndim .6s ease both}
.at-note{padding:0 20px;margin-top:12px;min-height:22px;font-size:14px;font-weight:800;line-height:1.35}
.at-note.ok{color:#15803D}.at-note.bad{color:#B91C1C}.at-note.warn{color:#9A3412}.at-note.muted{color:var(--muted)}
.at-foot{padding:6px 20px 0;font-size:13px;font-weight:800;color:var(--muted)}
.at-cta{position:sticky;bottom:0;margin-top:auto;padding:16px 12px max(env(safe-area-inset-bottom),18px);background:linear-gradient(rgba(244,246,251,0),var(--bg) 26%)}
.at-go{background:var(--pc);box-shadow:0 10px 24px var(--pc-glow);transition:background .3s,box-shadow .3s}
.addto .btn:disabled{background:#E2E8F0;color:#64748B;box-shadow:none}
.addto .at-go:disabled{background:var(--pc);color:#fff;opacity:1;box-shadow:none}
.addto .at-rm:disabled{background:#FEE2E2;color:#B91C1C}
.at-go.ok{background:#15803D;box-shadow:0 10px 24px rgba(21,128,61,.28)}
.at-rm{background:#FEE2E2;color:#B91C1C;box-shadow:none}
.at-alt{display:block;width:100%;min-height:44px;margin-top:6px;border:0;background:none;color:var(--blue-ink);font-weight:900;font-size:14.5px}
.g-b.wlist{background:var(--amber-soft);color:var(--amber-ink);border:1.5px dashed var(--amber);box-shadow:none}
.addto .g-b.wlist{background:var(--amber-soft);color:var(--amber-ink)}
#toast.act{pointer-events:auto;display:flex;align-items:center;gap:14px;text-align:left}
#toast .tundo{border:0;background:none;color:#93C5FD;font:900 14px Nunito,system-ui,sans-serif;min-height:32px;padding:0 2px}
@keyframes atEnter{from{opacity:0;transform:translateY(28px)}to{opacity:1;transform:none}}
@keyframes atLit{0%{transform:scale(.5);opacity:0}60%{transform:scale(1.1);opacity:1}100%{transform:none;opacity:1}}
@keyframes atHalo{0%{transform:scale(1);opacity:.9}100%{transform:scale(1.4,1.2);opacity:0}}
@keyframes atDrop{0%{transform:translateY(-40px) scale(1.22)}65%{transform:translateY(3px) scale(.96)}100%{transform:none}}
@keyframes atPop{0%{transform:scale(1)}40%{transform:scale(1.1)}100%{transform:scale(1)}}
@keyframes atCheck{0%{transform:scale(0)}70%{transform:scale(1.25)}100%{transform:scale(1)}}
@keyframes atDim{from{background:var(--pc-soft2);color:var(--pc-ink)}}
@keyframes atUndim{from{background:#ECEFF4;color:#A0ABBB}}
@keyframes atBeam{from{opacity:0;transform:scaleY(.5)}}
@keyframes atOut{to{opacity:0;transform:scale(.85)}}
@media (prefers-reduced-motion: reduce){.fullpg,.addto *,.addto *::before,.addto *::after{animation:none!important;transition:none!important}}
""")

# ---------------------------------------------------------------- grid: lit days, per-block marks, waitlisted blocks
rep("<button class=\"g-day ${d === focus ? 'on' : ''} ${d === today ? 'g-today' : ''}\"",
    "<button class=\"g-day ${d === focus ? 'on' : ''} ${d === today ? 'g-today' : ''}${o.hiDays && o.hiDays.includes(d) ? ' hi' : ''}\"")
rep("o.ghost === s.id ? (o.clash ? 'ghost clash' : 'ghost') : ''].join(' ');",
    "o.ghost === s.id ? (o.clash ? 'ghost clash' : 'ghost') : '', o.repl && o.repl.has(s.id) ? 'repl' : '', o.clashIds && o.clashIds.has(s.id) ? 'clashb' : '', s.mineWl ? 'wlist' : ''].join(' ');")

# a waitlisted row is that person's own copy of the section (SEC is shared), marked mineWl
rep("if (nbr && SEC[nbr]) { out.push(SEC[nbr]); return; }",
    "if (nbr && SEC[nbr]) { out.push(r.status === 'waitlisted' ? Object.assign({}, SEC[nbr], { mineWl: true, wlPos: r.wl_pos == null ? null : r.wl_pos }) : SEC[nbr]); return; }")
rep("async: false, seats: null, status: 'unknown', offFeed: true }); return; }",
    "async: false, seats: null, status: 'unknown', offFeed: true, mineWl: r.status === 'waitlisted', wlPos: r.wl_pos == null ? null : r.wl_pos }); return; }")

# My Classes cards say "Waitlist #N"
rep("""${ss.map(s => `<div class="muted b" style="font-size:14px">${esc(profName(s.prof))} · ${secWhen(s)}</div>`).join('')}""",
    """${ss.map(s => `<div class="muted b" style="font-size:14px">${esc(profName(s.prof))} · ${secWhen(s)}${s.mineWl ? ` · <span style="color:var(--amber-ink);font-weight:900">Waitlist${s.wlPos ? ' #' + esc(String(s.wlPos)) : ''}</span>` : ''}</div>`).join('')}""")

# ---------------------------------------------------------------- state: where you last added
rep("schedDay: null, mineTerm: null,", "schedDay: null, mineTerm: null, addDest: null,")
rep("'notifSeen', 'mineTerm']", "'notifSeen', 'mineTerm', 'addDest']")
rep("mineTerm: S.mineTerm }", "mineTerm: S.mineTerm, addDest: S.addDest }")

# ---------------------------------------------------------------- writes
rep("TC.removeMyClass = async function (code) {",
    """/* Add to your week (2026-10-04): one section into My Classes, enrolled or waitlisted — the desktop's
   own row shape (status 'waitlisted' + wl_pos). A swap saves the new row first, then drops the old
   class number, so a failure never leaves the class with no section. */
TC.addMySection = async function (s, o) {
  const sb = TC.client(), me = TC.user.id; o = o || {};
  let r = await sb.from('saved_classes').upsert({ user_id: me, term: CFG.TERM, code: s.code });
  if (r.error) return dbSay(r.error, 'Couldn’t add ' + s.code + '.');
  const wl = o.status === 'waitlisted';
  r = await sb.from('my_sections').upsert({ user_id: me, term: CFG.TERM, code: s.code, class_nbr: String(s.id), section: s.sec || null, instructor: s.instructor || null, days: s.rawDays || null, status: wl ? 'waitlisted' : 'enrolled', wl_pos: wl && o.wlPos ? o.wlPos : null });
  if (r.error) {
    /* the class wasn't saved before: take the new saved row back too, so it never shows as "No section yet" */
    if (o.hadSaved === false) await sb.from('saved_classes').delete().eq('user_id', me).eq('term', CFG.TERM).eq('code', s.code);
    await loadMine(); return dbSay(r.error, 'Couldn’t save that section.');
  }
  for (const nbr of (o.swap || [])) {
    const d = await sb.from('my_sections').delete().eq('user_id', me).eq('term', CFG.TERM).eq('code', s.code).eq('class_nbr', String(nbr));
    if (d.error) { await loadMine(); return dbSay(d.error, 'Added, but the old section is still there — remove it from My Classes.'); }
  }
  await loadMine(); return null;
};
TC.removeMySection = async function (code, nbr) {
  const sb = TC.client(), me = TC.user.id;
  const r = await sb.from('my_sections').delete().eq('user_id', me).eq('term', CFG.TERM).eq('code', code).eq('class_nbr', String(nbr));
  if (r.error) return dbSay(r.error, 'Couldn’t remove that section.');
  await loadMine(); return null;
};
/* Undo: one class's rows put back as they were (snapshot from mineSnap). The old rows go back FIRST and
   only the number the add put there comes out, so a failed undo never leaves the class with less than
   it had; rows with no class number (never touched by add/remove here) are left alone. */
TC.restoreMyCode = async function (code, snap, added) {
  const sb = TC.client(), me = TC.user.id;
  const back = snap.rows.filter(x => x.class_nbr != null && String(x.class_nbr) !== '');
  let r = { error: null };
  for (const x of back) {
    r = await sb.from('my_sections').upsert({ user_id: me, term: CFG.TERM, code: x.code, class_nbr: String(x.class_nbr), section: x.section == null ? null : x.section, instructor: x.instructor == null ? null : x.instructor, days: x.days == null ? null : x.days, status: x.status || 'enrolled', wl_pos: x.wl_pos == null ? null : x.wl_pos });
    if (r.error) break;
  }
  if (!r.error && added && !back.some(x => String(x.class_nbr) === String(added))) r = await sb.from('my_sections').delete().eq('user_id', me).eq('term', CFG.TERM).eq('code', code).eq('class_nbr', String(added));
  if (!r.error) r = snap.saved ? await sb.from('saved_classes').upsert({ user_id: me, term: CFG.TERM, code }) : await sb.from('saved_classes').delete().eq('user_id', me).eq('term', CFG.TERM).eq('code', code);
  await loadMine(); return r.error ? dbSay(r.error, 'Couldn’t undo that.') : null;
};
function mineSnap(code) {
  const M = TC.mineRows || { secs: [], saved: [] };
  return { saved: (M.saved || []).includes(code), rows: (M.secs || []).filter(r => canonCode(r.code) === code).map(r => Object.assign({}, r)) };
}
TC.removeMyClass = async function (code) {""")

rep("else if (k === 'ngTitle') { if (UI.ng) UI.ng.title = ev.target.value; }",
    "else if (k === 'ngTitle') { if (UI.ng) UI.ng.title = ev.target.value; }\n  else if (k === 'atwl') { if (UI.sheet && UI.sheet.type === 'addTo') { const v = ev.target.value.replace(/\\D/g, '').slice(0, 3); UI.sheet.wlPos = v; if (ev.target.value !== v) ev.target.value = v; } }")

# ---------------------------------------------------------------- toast with Undo
rep("function toast(m) { const t = document.getElementById('toast'); if (!t) return; t.textContent = m; t.classList.add('on');",
    "function toast(m) { const t = document.getElementById('toast'); if (!t) return; t.classList.remove('act'); UI.undo = null; t.textContent = m; t.classList.add('on');")
rep("let toastT;\n",
    """let toastT;
/* A toast that can take it back (Add to your week, 2026-10-04): 5 seconds, then the Undo is gone. */
function toastUndo(m, fn) {
  const t = document.getElementById('toast'); if (!t) return;
  t.innerHTML = `<span>${esc(m)}</span><button class="tundo" data-a="toastUndo">Undo</button>`; t.classList.add('on', 'act'); UI.undo = fn || null;
  clearTimeout(toastT); toastT = setTimeout(() => { t.classList.remove('on', 'act'); UI.undo = null; }, 5000);
}
""")

# ---------------------------------------------------------------- the class page's +: lit when the section is anywhere of yours
rep("const inP = ['A', 'B', 'C'].some(k => (TC.plans[k] || []).includes(s.id)), w = !!TC.watches[s.id], closed",
    "const inP = ['A', 'B', 'C'].some(k => (TC.plans[k] || []).includes(s.id)) || personSecs('me').some(x => x.id === s.id), w = !!TC.watches[s.id], closed")
rep("<button class=\"addbtn ${inP ? 'in' : ''}\" data-a=\"addPlanSheet\" data-x=\"${esc(s.id)}\" aria-label=\"${inP ? 'In a plan — change' : 'Add to a plan'}\">",
    "<button class=\"addbtn ${inP ? 'in' : ''}\" data-a=\"addPlanSheet\" data-x=\"${esc(s.id)}\" aria-label=\"${inP ? 'In your week — change' : 'Add to your week'}\">")

# ---------------------------------------------------------------- full-screen sheets
rep("""  else if (UI.sheet) { const again = sh.dataset.open === UI.sheet.type, ob = sh.querySelector('.sbody'), oy = again && ob ? ob.scrollTop : 0;
    sh.innerHTML = `""",
    """  else if (UI.sheet) { const full = !!(SHEETS[UI.sheet.type] && SHEETS[UI.sheet.type].full), again = sh.dataset.open === UI.sheet.type, ob = sh.querySelector(full ? '.fullpg' : '.sbody'), oy = again && ob ? ob.scrollTop : 0;
    const fa = full && document.activeElement && sh.contains(document.activeElement) && document.activeElement.dataset ? [document.activeElement.dataset.a, document.activeElement.dataset.x] : null;
    if (full) sh.innerHTML = `<div class="fullpg${again ? ' re' : ''}" role="dialog" aria-modal="true" aria-label="${esc(SHEETS[UI.sheet.type].label || '')}">${SHEETS[UI.sheet.type](UI.sheet)}</div>`;
    else sh.innerHTML = `""")
rep("if (again) { const nb = sh.querySelector('.sbody'); if (nb) nb.scrollTop = oy; }",
    "if (again) { const nb = sh.querySelector(full ? '.fullpg' : '.sbody'); if (nb) nb.scrollTop = oy; }\n    if (full) { const t = fa && fa[0] ? [...sh.querySelectorAll('[data-a]')].find(x => x.dataset.a === fa[0] && (x.dataset.x || '') === (fa[1] || '')) : null; const f = t || (!again ? sh.querySelector('.xbtn') : null); if (f && !focusId) try { f.focus({ preventScroll: true }); } catch (e) {} }")

rep("  else sh.innerHTML = '';\n  if (UI.champ || !UI.sheet) delete sh.dataset.open;",
    "  else sh.innerHTML = '';\n  if (UI.champ || !UI.sheet) delete sh.dataset.open;\n  /* the app behind a full screen can't be reached by Tab or VoiceOver */\n  { const fullOpen = !UI.champ && UI.sheet && SHEETS[UI.sheet.type] && SHEETS[UI.sheet.type].full; ['scroll', 'fixtop', 'fixbot', 'chrome'].forEach(i => { const el = document.getElementById(i); if (el) el.inert = !!fullOpen; }); }")

# ---------------------------------------------------------------- the screen (replaces SHEETS.addPlan)
a = s.index('/* "Add to a plan" (2026-09-30)')
b = s.index('\n};\n', s.index('SHEETS.addPlan = ', a)) + 4
s = s[:a] + r'''/* ---- Add to your week (Tate, 2026-10-04; canvas "Add a Class Options", option 2 in the light theme) ----
   One screen for My Classes (this term) and Plans A–C. The section going in is lit in the place's own
   colour while the rest of that week goes grey; Add drops it in, the week lights back up, and the screen
   closes with an Undo. sh.seq changes on every pick/phase, and an animation plays only on the first draw
   of a seq, so a background reload never replays it. */
const AT_PLANS = ['A', 'B', 'C'];
function atOverlaps(list, sec) { return list.filter(x => !x.async && !sec.async && x.s != null && sec.s != null && x.code !== sec.code && [...x.days].some(d => sec.days.includes(d)) && x.s < sec.e && sec.s < x.e); }
function atNbr(x) { return x.offFeed ? String(x.id).split(':').pop() : String(x.id); }
function atNames(ids) { const n = ids.map(f => esc((PEOPLE[f] || {}).short || 'A friend')); return n.length <= 2 ? n.join(' and ') : n.slice(0, 2).join(', ') + ' and ' + (n.length - 2) + ' more'; }
function openAddTo(id) {
  const s = SEC[id];
  const inPlan = AT_PLANS.find(k => (TC.plans[k] || []).includes(id)), inMine = personSecs('me').some(x => x.id === id);
  const last = AT_PLANS.includes(S.addDest) || S.addDest === 'mine' ? S.addDest : null;
  const dest = inPlan || (inMine ? 'mine' : last || (AT_PLANS.includes(S.plan) ? S.plan : 'A'));
  UI.sheet = { type: 'addTo', id, dest, phase: 'preview', status: null, wlPos: '', keepBoth: false, err: null, seq: 1 };
  S.homeDays.addto = null; UI.champ = false; render(true);
  return !!s;
}
/* What adding this section to `dest` would do. */
function atPlanOf(sh, s) {
  const P = AT_PLANS.includes(sh.dest) ? sh.dest : null, mine = sh.dest === 'mine';
  const o = { P, mine, other: !P && !mine, inIt: false, base: [], repl: [], clash: [], full: false, where: P ? 'Plan ' + P : 'My Classes' };
  if (P) {
    const ids = TC.plans[P] || [], others = ids.map(x => SEC[x]).filter(Boolean).filter(x => x.id !== sh.id);
    o.inIt = ids.includes(sh.id);
    o.repl = o.inIt ? [] : others.filter(x => x.code === s.code);
    o.base = others.filter(x => x.code !== s.code || o.inIt);
    o.clash = o.inIt ? [] : conflicts(o.base.map(x => x.id), s);
    o.full = !o.inIt && !o.repl.length && ids.length >= 12;
  } else if (mine) {
    const my = personSecs('me'), others = my.filter(x => x.id !== sh.id);
    o.inIt = my.some(x => x.id === sh.id);
    o.repl = o.inIt || sh.keepBoth ? [] : others.filter(x => x.code === s.code && atNbr(x));
    o.base = others.filter(x => !o.repl.includes(x));
    o.clash = o.inIt ? [] : atOverlaps(o.base, s);
    o.needStatus = !o.inIt && (s.status === 'full' || s.status === 'wait') && !sh.status;
  }
  return o;
}
SHEETS.addTo = sh => {
  const s = SEC[sh.id];
  const top = `<div class="at-top"><span class="at-kick">ADD TO YOUR WEEK</span><button class="xbtn" data-a="closeSheet" aria-label="Close">${ic('x', 16, 2.4)}</button></div>`;
  if (!s) return `<div class="addto dest-mine done">${top}<div class="empty"><b>That section is no longer listed.</b></div></div>`;
  const fx = sh.fxSeen !== sh.seq; sh.fxSeen = sh.seq;
  const o = atPlanOf(sh, s), terms = myTerms(), otherT = o.other ? terms.find(t => 'term:' + t.label === sh.dest) : null;
  const nm = x => esc(x.code) + (secLabel(x.sec) ? ' ' + esc(secLabel(x.sec)) : '');
  const when = x => x.async ? 'Online · self-paced' : x.noTime ? 'Time not posted' : `${daysLabel(x.days)} · ${range(x)}`;
  /* the top: code + section, the name, when + seats, the professor, friends in it */
  const r = ratingOf(s.prof), tone = rateTone(r);
  const who = secPeople(s.code, sh.id), fr = who.here.filter(f => f !== 'me' && PEOPLE[f]), oth = who.other.filter(f => f !== 'me' && PEOPLE[f]);
  const ppl = fr.length ? `<div class="at-ppl">${avStack(fr, 24)}<span><b>${atNames(fr)}</b> ${fr.length === 1 ? 'is' : 'are'} in this section</span></div>`
    : oth.length ? `<div class="at-ppl">${avStack(oth, 24)}<span><b>${atNames(oth)}</b> ${oth.length === 1 ? 'is' : 'are'} in another section</span></div>` : '';
  const head = `<div class="at-head">
  <div class="at-code"><span>${esc(s.code)}</span>${secLabel(s.sec) ? `<span class="at-sec">${esc(secLabel(s.sec))}</span>` : ''}</div>
  <div class="at-title">${esc(courseName(s.code) || course(s.code).title)}</div>
  <div class="at-facts"><span>${when(s)}</span><span aria-hidden="true">·</span>${secSeatText(s)}</div>
  <div class="at-facts"><span>${esc(profName(s.prof))}</span>${tone ? `<span style="color:${tone.ink};font-weight:900">★ ${r.toFixed(1)}</span>` : ''}</div>
  ${ppl}</div>`;
  /* where it goes: My Classes | Plans, then the terms or the plans */
  const grp = AT_PLANS.includes(sh.dest) ? 'plans' : 'classes';
  const chk = on => on ? ic('check', 14, 3) : '';
  const chips = grp === 'plans'
    ? AT_PLANS.map(k => { const on = sh.dest === k, has = (TC.plans[k] || []).includes(sh.id); return `<button class="at-chip plan-${k} ${on ? 'on' : ''}" data-a="atPick" data-x="${k}" aria-pressed="${on}"${has ? ` aria-label="Plan ${k}, has this section"` : ''}><i class="pdot"></i>Plan ${k}${chk(has)}</button>`; }).join('')
    : terms.map(t => { const d = t.code === CFG.TERM ? 'mine' : 'term:' + t.label, on = sh.dest === d, dis = d !== 'mine', has = d === 'mine' && personSecs('me').some(x => x.id === sh.id);
        return `<button class="at-chip dest-mine ${on ? 'on' : ''} ${dis ? 'dis' : ''}" data-a="atPick" data-x="${esc(d)}" aria-pressed="${on}"${dis ? ` aria-label="${esc(t.label)} — needs a ${esc(t.label)} section"` : ''}><i class="pdot"></i>${esc(t.label)}${chk(has)}</button>`; }).join('');
  const status = o.mine && !o.inIt && (s.status === 'full' || s.status === 'wait')
    ? `<div class="at-status"><span>Did you get a seat?</span><div class="at-seg" role="group" aria-label="Enrolled or waitlisted">${[['enrolled', 'Enrolled'], ['waitlisted', 'Waitlisted']].map(([k, l]) => `<button class="${sh.status === k ? 'on' : ''}" data-a="atStatus" data-x="${k}" aria-pressed="${sh.status === k}">${l}</button>`).join('')}</div>
     ${sh.status === 'waitlisted' ? `<label class="at-wl">Spot #<input id="atwl" data-in="atwl" inputmode="numeric" pattern="[0-9]*" maxlength="3" value="${esc(sh.wlPos || '')}" placeholder="?" aria-label="Your waitlist spot (optional)"></label>` : ''}</div>` : '';
  const pick = `<div class="at-pick"><div class="at-seg" role="group" aria-label="Add to">${[['classes', 'My Classes'], ['plans', 'Plans']].map(([k, l]) => `<button class="${grp === k ? 'on' : ''}" data-a="atGroup" data-x="${k}" aria-pressed="${grp === k}">${l}</button>`).join('')}</div>
  <div class="at-chips">${chips}</div>${status}</div>`;
  /* the week */
  const adding = sh.phase === 'adding', added = sh.phase === 'done';
  const secs = o.other ? [] : o.base.concat(o.repl).concat([s]);
  const timed = secs.some(x => !x.async && x.s != null && x.e != null);
  const spot = !o.other && !o.inIt && !added;
  const week = o.other ? `<div class="empty"><b>${otherT && otherT.code ? `This is a ${esc(CFG.TERM_LABEL)} section` : `${esc(otherT ? otherT.label : 'That term')} isn’t posted yet`}</b>${otherT && otherT.code ? `Find the ${esc(otherT.label)} section of ${esc(s.code)} to add it there.` : `Once Cal Poly posts it, add your ${esc(otherT ? otherT.label : '')} classes here.`}</div>`
    : timed ? grid(secs, { sel: S.homeDays.addto, act: 'homeDay', key: 'addto', blockAct: 'none', ghost: sh.id, clash: o.clash.length > 0 && !o.inIt, repl: new Set(o.repl.map(x => x.id)), clashIds: new Set(spot ? o.clash.map(x => x.id) : []), hiDays: s.async || s.s == null ? [] : [...s.days], one: true, fit: 30, H: 300 })
    : `<div class="empty"><b>Nothing to draw yet</b>${s.async || s.noTime ? 'This section has no set time.' : ''}</div>`;
  const foot = timed && (s.async || s.noTime) ? `<div class="at-foot">${esc(s.code)} has no set time, so it isn’t drawn.</div>` : '';
  /* what it says, and the button */
  const off = (t) => `<button class="btn" disabled aria-disabled="true">${t}</button>`;
  const go = (t, mode) => `<button class="btn at-go" data-a="atGo" data-x="${mode || 'add'}">${t}</button>`;
  let note = '', tn = 'muted', btn = '', alt = '';
  if (o.other) { note = otherT && otherT.code ? `A ${esc(CFG.TERM_LABEL)} section can’t go in ${esc(otherT.label)}.` : `${esc(otherT ? otherT.label : 'That term')} sections aren’t posted yet.`; btn = off(`Pick a ${esc(otherT ? otherT.label : '')} section`); }
  else if (added) { note = `Added to ${o.where}.`; tn = 'ok'; btn = `<button class="btn at-go ok" data-a="closeSheet">✓ Added to ${o.where}</button>`; }
  else if (adding) { note = o.repl.length ? `Swapping in ${nm(s)}…` : `Adding ${nm(s)}…`; btn = `<button class="btn at-go" disabled aria-disabled="true">Adding…</button>`; }
  else if (o.inIt) { note = `${nm(s)} is in ${o.where}.`; btn = sh.removing ? `<button class="btn at-rm" disabled aria-disabled="true">Removing…</button>` : `<button class="btn at-rm" data-a="atRemove">Remove from ${o.where}</button>`; }
  else if (o.P && o.clash.length) { note = `Clashes with ${o.clash.map(c => `${nm(c)} · ${daysLabel(c.days)} ${range(c)}`).join(', ')}`; tn = 'bad'; btn = off('Clashes — can’t add'); }
  else if (o.P && o.full) { note = `Plan ${o.P} already has 12 sections.`; btn = off(`Plan ${o.P} is full`); }
  else if (o.P && o.repl.length) { note = `Swaps out ${nm(o.repl[0])} (${secWhen(o.repl[0])}).`; tn = 'warn'; btn = go(`Swap into Plan ${o.P}`, 'swap'); }
  else if (o.mine && o.needStatus) { note = 'This section is full — are you in it, or on the waitlist?'; btn = off('Enrolled or waitlisted?'); }
  else if (o.mine && o.repl.length) { note = `You have ${o.repl.map(x => `${nm(x)} (${secWhen(x)})`).join(' and ')}. Swap ${o.repl.length > 1 ? 'them' : 'it'}, or keep both if one is a lab.${o.clash.length ? ` It also clashes with ${o.clash.map(c => `${nm(c)} · ${daysLabel(c.days)} ${range(c)}`).join(', ')}.` : ''}`; tn = o.clash.length ? 'bad' : 'warn'; btn = go(`Swap for ${esc(secLabel(s.sec) || 'this section')}`, 'swap'); alt = `<button class="at-alt" data-a="atBoth">Keep both — add as another section</button>`; }
  else if (o.mine && o.clash.length) { note = `Clashes with ${o.clash.map(c => `${nm(c)} · ${daysLabel(c.days)} ${range(c)}`).join(', ')}. Add it anyway if that’s really your schedule.`; tn = 'bad'; btn = go('Add anyway', 'anyway'); }
  else { note = o.mine ? 'Fits your week.' : `Fits Plan ${o.P}.`; tn = 'ok'; btn = go(`Add to ${o.where}`); }
  if (sh.err && !adding) { note = esc(sh.err); tn = 'bad'; }
  const cls = ['addto', o.P ? 'plan-' + o.P : 'dest-mine', spot ? 'spot' : 'done', adding ? 'adding' : '', added ? 'added' : '', fx ? 'fx' : ''].filter(Boolean).join(' ');
  return `<div class="${cls}">${top}${head}${pick}
 <div class="at-week">${week}${foot}</div>
 <div class="at-note ${tn}" role="status">${note}</div>
 <div class="at-cta">${btn}${alt}</div></div>`;
};
SHEETS.addTo.full = true;
SHEETS.addTo.label = 'Add to your week';
''' + s[b:]

# ---------------------------------------------------------------- actions
rep("  addPlanPick: k =>", r"""  atGroup: k => { const sh = UI.sheet; if (!sh || sh.type !== 'addTo' || sh.phase !== 'preview') return;
    if (k === 'plans' && !AT_PLANS.includes(sh.dest)) sh.dest = AT_PLANS.find(x => (TC.plans[x] || []).includes(sh.id)) || (AT_PLANS.includes(S.addDest) ? S.addDest : AT_PLANS.includes(S.plan) ? S.plan : 'A');
    else if (k === 'classes' && AT_PLANS.includes(sh.dest)) sh.dest = 'mine';
    else return;
    sh.seq++; sh.err = null; sh.keepBoth = false; S.homeDays.addto = null; render(true); },
  atPick: d => { const sh = UI.sheet; if (!sh || sh.type !== 'addTo' || sh.phase !== 'preview' || sh.dest === d) return; sh.dest = d; sh.seq++; sh.err = null; sh.keepBoth = false; S.homeDays.addto = null; render(true); },
  atStatus: v => { const sh = UI.sheet; if (!sh || sh.type !== 'addTo' || sh.phase !== 'preview') return; sh.status = v === 'waitlisted' ? 'waitlisted' : 'enrolled'; render(true); },
  atBoth: () => { const sh = UI.sheet; if (!sh || sh.type !== 'addTo' || sh.phase !== 'preview') return; sh.keepBoth = true; sh.seq++; render(true); },
  atGo: async mode => {
    const sh = UI.sheet; if (!sh || sh.type !== 'addTo' || sh.phase !== 'preview' || UI.busy.at) return;
    const s = SEC[sh.id]; if (!s) return;
    const o = atPlanOf(sh, s);
    if (o.other || o.inIt || (o.P && (o.clash.length || o.full)) || (o.mine && o.needStatus)) return;
    UI.busy.at = true; sh.phase = 'adding'; sh.seq++; sh.err = null; render(true);
    const t0 = Date.now(); let err = null, undo = null, msg = '';
    try { try {
      if (o.P) {
        const prev = (TC.plans[o.P] || []).slice(), had = prev.some(x => SEC[x] && SEC[x].code === s.code);
        TC.setPlan(o.P, prev.filter(x => !(SEC[x] && SEC[x].code === s.code)).concat(sh.id)); S.plan = o.P;
        msg = (had ? 'Swapped ' : 'Added ') + s.code + (had ? ' in Plan ' : ' to Plan ') + o.P;
        undo = () => { TC.setPlan(o.P, prev); render(true); toast('Undone'); };
      } else {
        const snap = mineSnap(s.code), swap = o.repl.map(atNbr).filter(Boolean);
        err = await TC.addMySection(s, { status: sh.status || 'enrolled', wlPos: sh.status === 'waitlisted' ? (parseInt(sh.wlPos, 10) || null) : null, swap, hadSaved: snap.saved });
        msg = (swap.length ? 'Swapped ' : 'Added ') + s.code + (swap.length ? ' in My Classes' : ' to My Classes');
        undo = async () => { const e = await TC.restoreMyCode(s.code, snap, String(s.id)); render(true); toast(e || 'Undone'); };
      }
    } catch (e) { err = 'Couldn’t add that — check your connection.'; }
    if (!err) { S.addDest = sh.dest; save(); try { gaEvent('add_to_week', { kind: o.P ? 'plan' : 'mine' }); } catch (e) {} }
    await new Promise(res => setTimeout(res, Math.max(0, 560 - (Date.now() - t0))));
    } finally { UI.busy.at = false; }
    if (UI.sheet !== sh) { if (err) toast(err); else toastUndo(msg, undo); render(true); return; }
    if (err) { sh.phase = 'preview'; sh.err = err; sh.seq++; render(true); return; }
    sh.phase = 'done'; sh.seq++; render(true);
    setTimeout(() => { if (UI.sheet === sh) { UI.sheet = null; render(true); setBars(false); } toastUndo(msg, undo); }, 900);
  },
  atRemove: async () => {
    const sh = UI.sheet; if (!sh || sh.type !== 'addTo' || sh.phase !== 'preview' || UI.busy.at) return;
    const s = SEC[sh.id]; if (!s) return;
    const o = atPlanOf(sh, s); if (!o.inIt) return;
    UI.busy.at = true; sh.removing = true; render(true); let err = null, undo = null;
    try {
      if (o.P) { const prev = (TC.plans[o.P] || []).slice(); TC.setPlan(o.P, prev.filter(x => x !== sh.id)); undo = () => { TC.setPlan(o.P, prev); render(true); toast('Undone'); }; }
      else {
        const snap = mineSnap(s.code), n = personSecs('me').filter(x => x.code === s.code).length;
        err = n > 1 ? await TC.removeMySection(s.code, sh.id) : await TC.removeMyClass(s.code);
        undo = async () => { const e = await TC.restoreMyCode(s.code, snap, null); render(true); toast(e || 'Undone'); };
      }
    } catch (e) { err = 'Couldn’t remove that — check your connection.'; }
    finally { UI.busy.at = false; sh.removing = false; }
    if (err) { if (UI.sheet === sh) { sh.err = err; render(true); } else toast(err); return; }
    if (UI.sheet === sh) UI.sheet = null;
    render(true); setBars(false); toastUndo(`Removed ${s.code} from ${o.where}`, undo);
  },
  toastUndo: () => { const f = UI.undo; UI.undo = null; const t = document.getElementById('toast'); if (t) t.classList.remove('on', 'act'); clearTimeout(toastT); if (f) f(); },
  addPlanPick: k =>""")
rep("  addPlanSheet: id => { const hold = ['A', 'B', 'C'].find(x => (TC.plans[x] || []).includes(id)); UI.sheet = { type: 'addPlan', id, k: hold || (['A', 'B', 'C'].includes(S.plan) ? S.plan : 'A') }; S.homeDays.addprev = null; render(true); },",
    "  addPlanSheet: id => { openAddTo(id); },")
# the old sheet's two actions go with it
s2 = re.sub(r"  addPlanPick: k => \{ if \(UI\.sheet && UI\.sheet\.type === 'addPlan'\) \{[^\n]*\n", "", s, count=1)
if s2 == s: sys.exit('addPlanPick not removed')
s = s2
s2 = re.sub(r"  addPlanGo: \(\) => \{ const sh = UI\.sheet; if \(!sh \|\| sh\.type !== 'addPlan'\) return;[^\n]*\n", "", s, count=1)
if s2 == s: sys.exit('addPlanGo not removed')
s = s2

# GA: the event name is enumerated
if "add_to_week" not in s: sys.exit('ga event missing')

open(p, 'w', encoding='utf-8').write(s)
print('patched', p)
