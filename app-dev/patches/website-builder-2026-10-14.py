#!/usr/bin/env python3
"""The website's Planner tab becomes the phone's Builder (Tate, 2026-10-14: the Builder REPLACES "My planner").

The phone is the spec (planner-picks 2026-10-06, my-classes-builder 2026-10-11, builder-* 2026-10-12/13):
- "What matters most to you?" — Requirements · Professors · Friends ranked 1-2-3 with up/down buttons, and
  units per term 12-20 (default 16). Saved to planner_prefs {user_id, priority, units, ranking} (upsert on
  user_id) with this device's copy as the fallback; without RUN 19's `ranking` column it is written without
  it and the order stays on this device (the phone's prefsNoRank); without the table, on this device only.
- planRank + the draft engine with the website's data names and the phone's constants verbatim:
  Requirements 40 · Urgency 30 · Professor 15 · Friends 10 · Seats 5; weights 1.5 / 1.0 / 0.6 by the ranking
  (Requirements counts for requirements + urgency, as on the phone). Candidates come from the report's open
  lines (by class and by GE area) when there is a report on the account, else from the flowchart. Never a class
  that's done, being taken, not offered in Spring (no row in this term's seat feed), whose prerequisites aren't
  met, or HNRS without an Honors line.
- The Builder screen, inside #plBuilderOut where "Building Plan A" was: "Spring 2027" with the report's catalog
  chip; one term card (your registration day line, the units in the plan you're filling against your target,
  what matters most, Draft my plans); requirement cards with their best options as tiles (code, name, the best
  section's time, its professor ★, friends' faces, seat state), "See more", "Mark done" (a report line, kept on
  degree_audit.overrides like the Report screen does); "Why it's #N" lists the score parts; a tile's + adds that
  section to the plan you're filling (TCPlans: Plans A-C, term-scoped, as everywhere else).
- Draft my plans fills A (the best combination), B (A's classes, an at-risk section swapped for an open one once
  registration is open, else another section), C (friends ×2.5) — no clashes, never over the units target or a
  class per 3 units, never over a commitment (window.cmBlocks, when that slice is there). A plan the student
  changed (it no longer holds exactly what was drafted into it) is never re-drafted without asking.
- Nothing left → the done view. No report and no flowchart → "Upload your Degree Progress Report" (dprPick()).
- The old planner's "What you can take" / "Planning" / tray and "Create my perfect next term" are gone; the old
  code stays inert behind its own null checks. Past classes (#plRecord) stays where it is ("Past classes").

Usage: python3 website-builder-2026-10-14.py <repo>
"""
import sys, pathlib
root = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else '.')
f = root / 'index.html'
s = f.read_text()
if 'website-builder (2026-10-14)' in s:
    sys.exit('already patched')

def one(old, new):
    global s
    n = s.count(old)
    assert n == 1, (n, old[:120])
    s = s.replace(old, new)

# 1. the old planner's DOM goes
a = s.index('  <section class="pl-card" id="plPlanning">')
b_ = s.index('<button type="button" class="pl-go" onclick="plBuild()">Create my perfect next term &rarr;</button>\n  </div>\n', a)
b_ += len('<button type="button" class="pl-go" onclick="plBuild()">Create my perfect next term &rarr;</button>\n  </div>\n')
old = s[a:b_]
assert s.count(old) == 1 and old.count('id="plTray"') == 1
s = s[:a] + '  <!-- website-builder (2026-10-14): "Planning", "What you can take" and the tray were here; the Builder (#plBuilderOut) replaces them. -->\n' + s[b_:]
one('<button class="sp-btn" id="schBuildBtn" type="button">Create my perfect next term &rarr;</button>',
    '<!-- "Create my perfect next term" was here (website-builder 2026-10-14: Draft my plans replaces it) -->')
one('    <div class="sp-build">\n      <div class="sp-buildsel">', '    <div class="sp-build" style="display:none">\n      <div class="sp-buildsel">')
one("    document.getElementById('schBuildBtn').onclick=build;",
    "    var _sbb=document.getElementById('schBuildBtn'); if(_sbb)_sbb.onclick=build;")

# 2. the flowchart's rows, for the Builder when there's no report
one("window.plPlanningLabel=planningLabel;",
    "window.plPlanningLabel=planningLabel;\ntry{ window.plFlowRows=rows; window.plSlotAreaKey=slotAreaKey; window.plFlowMajor=major; }catch(e){}   /* website-builder (2026-10-14) */")
one("window.plRenderEligible=function(){\n  var host=document.getElementById('plEligible'); if(!host)return;",
    "window.plRenderEligible=function(){\n  try{ if(typeof window.tcBuilderRender==='function')window.tcBuilderRender(); }catch(e){}\n  var host=document.getElementById('plEligible'); if(!host)return;")

one("try{ Object.assign(window,{auditLines:auditLines,", "try{ Object.assign(window,{auditTag:auditTag,auditNum:auditNum,plGeBar:plGeBar}); }catch(e){}   /* website-builder (2026-10-14) */\ntry{ Object.assign(window,{auditLines:auditLines,")

# 3. TCPlans draws the Builder where "Building Plan A" was
one("    var k = fkey(document.activeElement), inside = out.contains(document.activeElement);\n    try { out.innerHTML = builderHtml(); paintBuilder(); } catch (e) {",
    "    if (typeof window.tcBuilderRender === 'function') { try { window.tcBuilderRender(); } catch (e) { out.innerHTML = '<p class=\"pl3-quiet\">Planner couldn’t be drawn just now.</p>'; } return; }\n    var k = fkey(document.activeElement), inside = out.contains(document.activeElement);\n    try { out.innerHTML = builderHtml(); paintBuilder(); } catch (e) {")
one("    if (bw && bw.style.display !== 'none') paintBuilder();",
    "    if (bw && bw.style.display !== 'none') { if (typeof window.tcBuilderRender === 'function') { try { window.tcBuilderRender(); } catch (_) {} } else paintBuilder(); }")

CSS = r'''
<style id="tc-builder-css">
/* website-builder (2026-10-14) */
.bd{display:block;max-width:100%}
.bd-head{display:flex;align-items:center;gap:10px;flex-wrap:wrap;margin:2px 0 14px}
.bd-head h2{margin:0;font-size:24px;letter-spacing:-.01em;color:var(--text)}
.bd-chip{font-size:12.5px;font-weight:700;color:var(--text-2);background:var(--panel-3);border-radius:999px;padding:4px 10px}
.bd-past{margin-left:auto;font:inherit;font-size:13.5px;font-weight:700;color:var(--accent);background:none;border:0;cursor:pointer;padding:6px 4px}
.bd-grid{display:grid;grid-template-columns:minmax(0,1fr);gap:16px;align-items:start}
.bd-term{order:-1}
@media (min-width:1140px){.bd-grid{grid-template-columns:minmax(0,1fr) 320px}.bd-term{position:sticky;top:90px;order:2}.bd-main{order:1}}
.bd-card{background:var(--panel);border:1px solid var(--line);border-radius:16px;padding:14px 16px;box-shadow:var(--card-sh);margin-bottom:12px;min-width:0}
.bd-term .bd-card{margin-bottom:0}
.bd-th{font-size:12px;font-weight:800;letter-spacing:.06em;text-transform:uppercase;color:var(--muted);margin:12px 0 6px}
.bd-th:first-child{margin-top:0}
.bd-units{font-size:15px;color:var(--text)}
.bd-units b{font-size:20px}
.bd-units.over b{color:var(--low)}
.bd-slots{display:flex;gap:6px;margin-top:8px}
.bd-slot{flex:1;font:inherit;font-size:13px;font-weight:700;border:1px solid var(--line);background:var(--panel-2);color:var(--text-2);border-radius:10px;padding:6px 4px;cursor:pointer}
.bd-slot.on{border-color:var(--accent);background:var(--accent-dim);color:var(--accent)}
.bd-rank{list-style:none;margin:0;padding:0}
.bd-rank li{display:flex;align-items:center;gap:8px;padding:5px 0;font-size:14.5px;color:var(--text)}
.bd-rank .n{width:22px;height:22px;border-radius:50%;background:var(--panel-3);color:var(--text-2);font-size:12px;font-weight:800;display:inline-flex;align-items:center;justify-content:center;flex:none}
.bd-rank .l{flex:1;font-weight:600}
.bd-mv{font:inherit;width:28px;height:28px;border-radius:8px;border:1px solid var(--line);background:var(--panel);color:var(--text-2);cursor:pointer;font-size:13px}
.bd-mv:disabled{opacity:.35;cursor:default}
.bd-ur{display:flex;align-items:center;gap:8px;font-size:14px;color:var(--text-2)}
.bd-ur{white-space:nowrap}
.bd-ur select{width:auto;min-width:72px;font:inherit;padding:4px 8px;border-radius:8px;border:1px solid var(--line);background:var(--panel);color:var(--text)}
.bd-go{display:block;width:100%;margin-top:14px;font:inherit;font-size:15px;font-weight:800;border:0;border-radius:12px;padding:11px;background:var(--accent);color:var(--accent-ink);cursor:pointer}
.bd-note{font-size:12.5px;color:var(--muted);margin-top:6px}
.bd-rq{display:flex;align-items:center;gap:8px;flex-wrap:wrap}
.bd-rq .t{font-size:16px;font-weight:800;color:var(--text);flex:1;min-width:0}
.bd-rq .s{font-size:12.5px;color:var(--muted);width:100%}
.bd-mark{font:inherit;font-size:12.5px;font-weight:700;color:var(--text-2);background:var(--panel-2);border:1px solid var(--line);border-radius:999px;padding:4px 10px;cursor:pointer}
.bd-tiles{display:grid;grid-template-columns:repeat(auto-fill,minmax(230px,1fr));gap:10px;margin-top:10px}
.bd-tile{position:relative;border:1px solid var(--line);border-radius:12px;padding:10px 12px;background:var(--panel-2);min-width:0}
.bd-tile .c{font-weight:800;color:var(--course);font-size:14.5px;display:flex;align-items:center;gap:6px}
.bd-tile .nm{font-size:13px;color:var(--text-2);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.bd-tile .w{font-size:12.5px;color:var(--text-2);margin-top:4px}
.bd-tile .p{font-size:12.5px;color:var(--text);margin-top:2px}
.bd-tile .st{font-size:12px;font-weight:700;margin-top:4px;color:var(--muted)}
.bd-tile .st.open{color:var(--good-ink)}
.bd-tile .st.full{color:var(--low)}
.bd-tile .st.wait{color:var(--mid)}
.bd-faces{display:flex;gap:2px;margin-top:5px;align-items:center;font-size:12px;color:var(--muted)}
.bd-faces .fc{width:22px;height:22px;border-radius:50%;overflow:hidden;display:inline-flex;align-items:center;justify-content:center;background:var(--panel-3);font-size:10px;font-weight:800;color:var(--text-2)}
.bd-faces .fc img{width:100%;height:100%;object-fit:cover}
.bd-add{position:absolute;top:8px;right:8px;font:inherit;font-weight:800;font-size:16px;width:30px;height:30px;border-radius:9px;border:1px solid var(--accent);background:var(--panel);color:var(--accent);cursor:pointer;line-height:1}
.bd-add.in{background:var(--accent);color:var(--accent-ink)}
.bd-why{font:inherit;font-size:12px;font-weight:700;color:var(--accent);background:none;border:0;padding:0;margin-top:6px;cursor:pointer}
.bd-pop{margin-top:6px;border-top:1px solid var(--line);padding-top:6px;font-size:12.5px;color:var(--text-2)}
.bd-pop div{display:flex;justify-content:space-between;gap:8px}
.bd-pop .tot{font-weight:800;color:var(--text);border-top:1px solid var(--line);margin-top:4px;padding-top:4px}
.bd-more{font:inherit;font-size:13px;font-weight:700;color:var(--accent);background:none;border:0;padding:8px 0 0;cursor:pointer}
.bd-none{font-size:13px;color:var(--muted);margin-top:6px}
.bd-empty h3{margin:0 0 6px;font-size:18px;color:var(--text)}
.bd-empty p{margin:0 0 12px;color:var(--text-2);font-size:14px}
.bd-empty .bd-go{width:auto;display:inline-block;padding:10px 18px}
</style>
'''

JS = r'''
<script id="tc-builder">
/* website-builder (2026-10-14): the phone's Builder (planRank, the draft engine, the term card, requirement cards
   with option tiles) with the website's data names. The phone's constants, verbatim. */
(function () {
  'use strict';
  var PREF_ORDER = { degree: ['degree', 'professors', 'friends'], professors: ['professors', 'degree', 'friends'], friends: ['friends', 'degree', 'professors'] };
  var PREF_LABEL = { degree: 'Requirements', professors: 'Professors', friends: 'Friends' };
  var PL_YEAR = { Freshman: 1, Sophomore: 2, Junior: 3, Senior: 4, '5th year +': 5 };
  var PL_PARTS = [['req', 'Requirements', 40], ['urg', 'Urgency', 30], ['prof', 'Professor', 15], ['fr', 'Friends', 10], ['seat', 'Seats', 5]];
  var SLOTS = ['A', 'B', 'C'];
  var UI = { more: {}, why: null, prefsFor: null, prefsErr: null, noRank: false, R: null };
  var P = null;   /* {priority, units, order, local} */

  function esc(x) { return (typeof escapeHtml === 'function') ? escapeHtml(x == null ? '' : String(x)) : String(x == null ? '' : x); }
  /* a value inside onclick="…('x')": JS-escaped, then HTML-escaped for the attribute */
  function ja(x) { return esc(String(x).replace(/\\/g, '\\\\').replace(/'/g, "\\'").replace(/[\r\n]/g, ' ')); }
  function uid() { try { return (typeof sbUser !== 'undefined' && sbUser) ? String(sbUser.id) : ''; } catch (e) { return ''; } }
  function k(c) { try { return canonCode(c) || c; } catch (e) { return c; } }
  function termLabel() { try { return mcTermLabel(); } catch (e) { return 'Spring 2027'; } }
  function toast(m) { try { frToast(m); } catch (e) {} }
  function prefOk(o) { return Array.isArray(o) && o.length === 3 && ['degree', 'professors', 'friends'].every(function (x) { return o.indexOf(x) >= 0; }); }
  function prefsKey() { return 'professify_prefs_' + (uid() || 'anon'); }
  function prefOrder() { return P && prefOk(P.order) ? P.order : PREF_ORDER[(P && P.priority) || 'degree'] || PREF_ORDER.degree; }
  function plWeights() { var w = {}; prefOrder().forEach(function (x, i) { w[x] = [1.5, 1.0, 0.6][i]; }); return w; }
  function plUnitsTarget() { return Math.min(20, Math.max(12, (P && +P.units) || 16)); }
  function plClassCap() { return Math.max(3, Math.round(plUnitsTarget() / 3)); }

  /* ---- prefs: planner_prefs, this device's copy as the fallback (phone loadPrefs / TC.savePrefs) ---- */
  function readLocalPrefs() {
    try { var c = JSON.parse(localStorage.getItem(prefsKey()) || 'null'); if (c && PREF_ORDER[c.priority]) return { priority: c.priority, units: +c.units || 16, order: prefOk(c.order) && c.order[0] === c.priority ? c.order : null, local: true }; } catch (e) {}
    return null;
  }
  var saveSeq = 0, saveChain = Promise.resolve();
  async function loadPrefs() {
    var u = uid(), seq0 = saveSeq; UI.prefsFor = u || 'anon';
    P = readLocalPrefs();
    if (!u || typeof sb === 'undefined' || !sb) return;
    var lo = P && P.order;
    var sel = function (cols) { return sb.from('planner_prefs').select(cols).eq('user_id', u).maybeSingle(); };
    var r;
    try { r = await sel('priority,units,ranking'); if (r.error && /ranking/.test(r.error.message || '')) { UI.noRank = true; r = await sel('priority,units'); } } catch (e) { r = { error: { message: String(e) } }; }
    if (uid() !== u || saveSeq !== seq0) return;   /* you changed something while it loaded: yours wins */
    if (r.error) { UI.prefsErr = (typeof schemaGap === 'function' && schemaGap(r.error)) ? 'missing' : (r.error.message || 'error'); return; }
    UI.prefsErr = null;
    if (r.data && PREF_ORDER[r.data.priority]) {
      var ro = r.data.ranking ? String(r.data.ranking).split(',') : null;
      P = { priority: r.data.priority, units: +r.data.units || 16, order: prefOk(ro) && ro[0] === r.data.priority ? ro : (lo && lo[0] === r.data.priority ? lo : null), local: false };
    }
  }
  function savePrefs(order, units) { saveSeq++; var run = saveChain.then(function () { return savePrefs1(order, units); }); saveChain = run.catch(function () {}); return run; }
  async function savePrefs1(order, units) {
    order = prefOk(order) ? order.slice() : PREF_ORDER.degree.slice();
    var priority = order[0];
    units = Math.min(20, Math.max(12, +units || 16));
    P = { priority: priority, units: units, order: order, local: true };
    try { localStorage.setItem(prefsKey(), JSON.stringify({ priority: priority, units: units, order: order })); } catch (e) {}
    var u = uid();
    if (!u || typeof sb === 'undefined' || !sb || UI.prefsErr === 'missing') return null;
    var row = { user_id: u, priority: priority, units: units, updated_at: new Date().toISOString() };
    if (!UI.noRank) row.ranking = order.join(',');
    var q;
    try { q = await sb.from('planner_prefs').upsert(row, { onConflict: 'user_id' }); } catch (e) { q = { error: { message: String(e) } }; }
    if (q.error && row.ranking && /ranking/.test(q.error.message || '')) { UI.noRank = true; delete row.ranking; try { q = await sb.from('planner_prefs').upsert(row, { onConflict: 'user_id' }); } catch (e) { q = { error: { message: String(e) } }; } }
    if (q.error) { if (typeof schemaGap === 'function' && schemaGap(q.error)) { UI.prefsErr = 'missing'; return null; } return 'Couldn’t save that — it’s kept on this device for now.'; }
    if (P && P.order && P.order.join() === order.join() && P.units === units) P.local = false;
    return null;
  }

  /* ---- sections, the website's way ---- */
  var SC = {};
  function secsOf(code) {
    if (SC[code]) return SC[code];
    var out = [];
    try { out = clsSections(code).filter(function (s) { return s && s.class_nbr; }).map(function (s) {
      var m = null; try { m = parseMeet(s.days); } catch (e) {}
      return { code: code, id: String(s.class_nbr), s: s, prof: s.name || '', pid: s.pid, rating: s.rating, days: s.days || '', meet: m, async: /async/i.test(String(s.instruction_mode || '')), status: s.seat ? s.seat.cls : 'unknown', seats: s.seat && s.seat.cls === 'open' ? (s.seat.n || 0) : 0 };
    }); } catch (e) {}
    SC[code] = out; return out;
  }
  function secById(code, id) { return secsOf(code).filter(function (x) { return x.id === String(id); })[0] || null; }
  function secClash(a, b) { if (!a || !b || a.async || b.async) return false; try { return meetsOverlap(a.meet, b.meet); } catch (e) { return false; } }
  function ratingOf(s) { return s && s.rating != null ? to5(s.rating) : null; }
  function regOpen() { try { var d = (cfg() || {}).REGISTRATION_OPENS; return !!d && new Date() >= new Date(d + 'T00:00:00'); } catch (e) { return false; } }
  function friendsIn(code) { try { return friendsInClass(code) || []; } catch (e) { return []; } }
  function friendsInSec(code, id) { return friendsIn(code).filter(function (f) { return (f.crns || []).map(String).indexOf(String(id)) >= 0; }); }
  function offered(code) { try { return !!(SEAT_SECTIONS && SEAT_SECTIONS[code] && SEAT_SECTIONS[code].length); } catch (e) { return false; } }
  function unitsOf(code) {
    try { var u = auditUnitsOf(code, flowMajor()); if (u != null) return u; } catch (e) {}
    try { var c = Number((classInfo(code) || {}).units); if (c > 0) return c; } catch (e) {}
    return null;
  }
  function flowMajor() { try { return typeof window.plFlowMajor === 'function' ? window.plFlowMajor() : null; } catch (e) { return null; } }
  function commits() {
    var c = null;
    try { if (typeof window.cmBlocks === 'function') c = window.cmBlocks(); else if (Array.isArray(window.cmBlocks)) c = window.cmBlocks; } catch (e) {}
    /* a block is a meeting ({days:[..], start, end} minutes, as parseMeet gives) or carries one as .meet; anything else is skipped */
    return (Array.isArray(c) ? c : []).map(function (b) { var m = b && (b.meet || b); return (typeof okMeet === 'function' && okMeet(m)) ? { meet: m, async: false } : null; }).filter(Boolean);
  }
  /* your Spring classes you're registered for: their sections count toward units and clashes */
  function regSecs() {
    var out = [];
    try { (typeof myClasses !== 'undefined' ? myClasses : []).forEach(function (code) {
      var m = (typeof myClassMeta !== 'undefined') ? myClassMeta[code] : null;
      var s = m && Array.isArray(m.secs) && m.secs.length ? secById(code, m.secs[0].crn) : null;
      out.push(s || { code: code, id: null, async: true });
    }); } catch (e) {}
    return out;
  }
  function honors() { var A = curAudit(); return !!(A && (A.reqs || []).some(function (b) { return /honors/i.test(b.label || ''); })); }
  function plansSecs(slot) { try { return (TCPlans.get(slot).sections || []).map(function (x) { return secById(x.code, x.class_nbr) || { code: x.code, id: String(x.class_nbr), async: true }; }); } catch (e) { return []; } }
  function inPlanSlots(code) { var o = []; SLOTS.forEach(function (sl) { try { if ((TCPlans.get(sl).sections || []).some(function (x) { return x.code === code; })) o.push(sl); } catch (e) {} }); return o; }

  /* ---- the flowchart's needs (when there's a flowchart) ---- */
  function flow() {
    /* the flowchart is yours only once your major is set (the hidden select otherwise sits on its first option) */
    try { if (typeof student === 'undefined' || !student.major) return null; } catch (e) { return null; }
    var d = null; try { d = typeof window.plFlowRows === 'function' ? window.plFlowRows() : null; } catch (e) {}
    if (!d) return null;
    var need = [], needU = [];
    (d.eligible || []).forEach(function (r) {
      var codes = (r.codes || []).filter(Boolean);
      if (codes.length) need.push({ codes: codes, year: r.year || 0, term: r.term || '', choice: codes.length > 1, group: r.type === 'conc' ? 'conc' : '', title: r.title || '' });
      else if (r.type === 'ge') { var a = null; try { a = window.plSlotAreaKey(r.title); } catch (e) {} if (a) needU.push({ type: 'ge', area: a, year: r.year || 0, title: r.title }); }
    });
    return { need: need, needU: needU, blocked: (d.blocked || []).length, raw: d };
  }

  /* ---- planRank (phone planRank, 2026-10-12) ---- */
  function prereqOk(code) {
    var rec = null; try { rec = coursePrereqs(code); } catch (e) {}
    if (!rec || !rec.req || !rec.req.length) return { ok: true, st: rec ? 'none' : null };
    var done = completedCodes(), st;
    try {
      var taking = myTakingCodes(), spring = (typeof myClasses !== 'undefined' ? myClasses : []);
      /* two terms: a Fall class you're taking is finished by Spring (taken before); a Spring class is in progress */
      st = (typeof mcTwoTerms === 'function' && mcTwoTerms()) ? prereqStatus(code, done, taking.filter(function (c) { return spring.indexOf(c) < 0; }), spring) : prereqStatus(code, done, [], taking);
    } catch (e) { st = { state: 'none' }; }
    return { ok: st.state === 'met' || st.state === 'concurrent' || st.state === 'none', st: st.state };
  }
  function reqPts(b) { return b.kind === 'ge' ? 5 : b.kind === 'conc' ? 8 : (b.kind === 'units' && /upper/i.test(b.label || '')) ? 6 : (b.oneOf || (b.courses && b.courses.req === 1 && (b.options || []).length > 1)) ? 8 : b.kind === 'elective' ? 2 : 10; }
  function planRank(opt) {
    opt = opt || {}; SC = {};
    var Y = PL_YEAR[(typeof student !== 'undefined' && student.standing) || ''] || 0;
    var done = completedCodes(), doneSet = {}, mine = myTakingCodes(), mineSet = {};
    done.forEach(function (c) { doneSet[k(c)] = 1; }); mine.forEach(function (c) { mineSet[k(c)] = 1; });
    var L = flow() || { need: [], needU: [] };
    var needOf = {}; L.need.forEach(function (n) { n.codes.forEach(function (c) { if (!needOf[k(c)]) needOf[k(c)] = n; }); });
    var geNeed = {}; L.needU.forEach(function (n) { if (n.area && !geNeed[n.area]) geNeed[n.area] = n; });
    var GE = plGeMap(), geOf = function (c) { return GE.get(k(c)) || []; };
    var termNow = String(termLabel()).split(' ')[0].toLowerCase();
    var W = opt.weights || plWeights(), frX = opt.friendsX || 1;
    var A = curAudit(), X = A ? auditLines(A, flowMajor()) : null, audit = X ? A : null, auditOpen = X ? X.open : [];
    var byClass = {}, byArea = {};
    auditOpen.forEach(function (b) { (b.options || []).forEach(function (c) { (byClass[k(c)] = byClass[k(c)] || []).push(b); }); plGeArea(b).forEach(function (a) { (byArea[a] = byArea[a] || []).push(b); }); });
    var unl = {};
    L.need.forEach(function (n2) { var seen = {}; n2.codes.forEach(function (c2) {
      var rec = null; try { rec = coursePrereqs(c2); } catch (e) {} if (!rec || !rec.req) return;
      rec.req.forEach(function (g) { if (g.some(function (x) { return doneSet[k(x)] || mineSet[k(x)]; })) return;
        g.forEach(function (x) { var kx = k(x); if (needOf[kx] && needOf[kx] !== n2 && !seen[kx]) { seen[kx] = 1; (unl[kx] = unl[kx] || []).push(c2); } }); });
    }); });
    var cands = [], seen = {};
    function consider(code) {
      var kc = k(code); if (seen[kc]) return; seen[kc] = 1;
      if (doneSet[kc] || mineSet[kc] || !offered(code) || !secsOf(code).length) return;
      if (/^HNRS\b/.test(code) && !honors()) return;
      var r = prereqOk(code); if (!r.ok) return;
      var n = needOf[kc] || null, fills = [], geA = [];
      if (audit) {
        fills = (byClass[kc] || []).slice();
        geOf(code).forEach(function (a) { var ok = (byArea[a] || []).filter(function (b) { return !plGeBar(b, code); }); ok.forEach(function (b) { if (fills.indexOf(b) < 0) fills.push(b); }); if (geA.indexOf(a) < 0 && ok.length) geA.push(a); });
        if (!fills.length) return;
      } else {
        geA = geOf(code).filter(function (a) { return geNeed[a]; });
        if (!n && !geA.length) return;
      }
      var ys = geA.map(function (a) { return geNeed[a] ? geNeed[a].year : 0; }).filter(Boolean);
      var yr = n ? (n.year || 0) : (ys.length ? Math.min.apply(null, ys) : 0);
      if (Y && yr > Y + 1) return;
      var best = bestSec(code), rt = best ? ratingOf(best) : null;
      var fr = friendsIn(code), frSec = best ? friendsInSec(code, best.id) : [], un = n ? (unl[kc] || []) : [];
      var behind = Y && yr ? Math.max(0, Y - yr) : 0;
      var onTerm = !!(n && n.term && String(n.term).toLowerCase() === termNow && yr === Y), onYear = !!(n && yr === Y);
      var ss = secsOf(code), open = ss.some(function (s) { return s.status === 'open'; }), openN = Math.max.apply(null, [0].concat(ss.map(function (s) { return s.status === 'open' ? (s.seats || 0) : 0; }))), waits = ss.some(function (s) { return s.status === 'wait'; });
      var req = Math.min(40, audit ? fills.reduce(function (a, b) { return a + reqPts(b); }, 0) : ((n ? (n.group === 'conc' ? 8 : n.choice ? 8 : 10) : 0) + geA.length * 5));
      var urg = Math.min(30, Math.min(24, behind * 12) + (onTerm ? 10 : onYear ? 6 : 0) + Math.min(12, un.length * 4));
      var prof = rt == null ? 5 : Math.max(0, Math.min(15, Math.round((rt - 2.5) / 2.5 * 15)));
      var frP = Math.min(10, fr.length * 4 + (frSec.length ? 2 : 0));
      var seat = !regOpen() ? 0 : openN >= 10 ? 5 : open ? 3 : waits ? 1 : 0;
      var parts = { req: req, urg: urg, prof: prof, fr: frP, seat: seat }, score = req + urg + prof + frP + seat;
      var wscore = (req + urg) * W.degree + prof * W.professors + frP * W.friends * frX + seat;
      var key = audit ? 'a:' + fills.map(function (b) { return A.reqs.indexOf(b); }).sort().join('+') : (n ? 'n:' + L.need.indexOf(n) : 'ge:' + geA.slice().sort().join('+'));
      cands.push({ code: code, n: n, geA: geA, fills: fills, yr: yr, Y: Y, behind: behind, onTerm: onTerm, best: best, rt: rt, fr: fr, un: un, parts: parts, score: score, wscore: wscore, key: key, units: unitsOf(code), prereq: r.st });
    }
    if (audit) { Object.keys(byClass).forEach(function (c) { consider(c); }); Object.keys(SEAT_SECTIONS || {}).forEach(function (c) { if (geOf(c).some(function (a) { return byArea[a]; })) consider(c); }); }
    else { L.need.forEach(function (n) { n.codes.forEach(function (c) { consider(c); }); }); Object.keys(SEAT_SECTIONS || {}).forEach(function (c) { if (!needOf[k(c)] && geOf(c).some(function (a) { return geNeed[a]; })) consider(c); }); }
    cands.sort(function (a, b) { return b.wscore - a.wscore || b.score - a.score || a.code.localeCompare(b.code); });
    var allDone = X ? (!X.open.some(function (b) { return !auditIsTotal(b); }) && !X.unknown.length) : (!L.need.length && !L.needU.length && !(L.blocked));
    return { all: cands, audit: !!audit, X: X, L: L, done: allDone, hasFlow: !!flow() };
  }
  /* the section a tile shows: an open seat first once registration is open, then one that fits, then the best-rated professor */
  function bestSec(code, avoid, strict) {
    var ss = secsOf(code);
    var clash = function (s) { return (avoid || []).some(function (t) { return secClash(s, t); }); };
    if (strict) ss = ss.filter(function (s) { return !clash(s); });
    if (!ss.length) return null;
    var tier = function (s) { return (regOpen() ? (s.status === 'full' ? 0 : s.status === 'wait' ? 2 : 4) : 4) + (clash(s) ? 0 : 1); };
    return ss.slice().sort(function (a, b) { return tier(b) - tier(a) || (ratingOf(b) || 0) - (ratingOf(a) || 0) || a.id.localeCompare(b.id); })[0];
  }

  /* ---- the draft (phone plDraftSec / planDraft / planDraftB) ---- */
  function draftSec(code, have, used) {
    var W = plWeights(), cm = commits();
    var ss = secsOf(code).filter(function (s) { return !(have || []).some(function (t) { return secClash(s, t); }) && !cm.some(function (t) { return secClash(s, t); }); });
    if (!ss.length) return null;
    var sc = function (s) { var r = ratingOf(s); return (regOpen() ? (s.status === 'full' ? -8 : s.status === 'wait' ? -2 : 0) : 0) + ((r == null ? 3 : r) - 3) * 2 * W.professors + friendsInSec(code, s.id).length * 1.5 * W.friends; };
    var fresh = ss.filter(function (s) { return !(used || {})[s.id] && !(regOpen() && s.status === 'full'); });
    return (fresh.length ? fresh : ss).slice().sort(function (a, b) { return sc(b) - sc(a) || a.id.localeCompare(b.id); })[0];
  }
  function planDraft(R, prev) {
    var target = plUnitsTarget(), cap = plClassCap(), used = {}, usedN = {};
    (prev || []).forEach(function (ids) { (ids || []).forEach(function (x) { used[x.id] = 1; usedN[x.code] = (usedN[x.code] || 0) + 1; }); });
    var adj = function (c) { return c.wscore * (1 - 0.12 * (usedN[c.code] || 0)); };
    var list = R.all.slice().sort(function (a, b) { return (b.onTerm ? 1 : 0) - (a.onTerm ? 1 : 0) || adj(b) - adj(a) || b.score - a.score || a.code.localeCompare(b.code); });
    var chosen = [], keys = {}, codes = {}, got = new Map();
    var take = function (c) { (c && c.fills || []).forEach(function (b) { got.set(b, (got.get(b) || 0) + 1); }); };
    var room = function (b) { return Math.max(1, Math.round((b.courses && +b.courses.need) || (b.units && +b.units.need >= 6 ? Math.floor(+b.units.need / 3) : 0) || 1)); };
    var units = 0, reg = regSecs();
    reg.forEach(function (s) { codes[s.code] = 1; var u = unitsOf(s.code); if (u != null) units += u; var c = R.all.filter(function (x) { return x.code === s.code; })[0]; if (c) { keys[c.key] = 1; take(c); } });
    var regTimed = reg.filter(function (s) { return s.id && !s.async; });
    for (var i = 0; i < list.length; i++) {
      var c = list[i];
      if (units >= target || chosen.length + reg.length >= cap) break;
      if ((keys[c.key] && !(c.fills && c.fills.some(function (b) { return (got.get(b) || 0) < room(b); }))) || codes[c.code]) continue;
      if (c.fills && c.fills.length && c.fills.every(function (b) { return (got.get(b) || 0) >= room(b); })) continue;
      var u = c.units;
      if (u != null && units + u > target) continue;
      var sec = draftSec(c.code, chosen.concat(regTimed), used); if (!sec) continue;
      chosen.push(sec); keys[c.key] = 1; codes[c.code] = 1; take(c); if (u != null) units += u;
    }
    return chosen;
  }
  function planDraftB(aSecs) {
    var have = [], out = [], codes = {}, cm = commits();
    regSecs().forEach(function (s) { if (s.id && !s.async) have.push(s); });
    var byProf = function (a, b) { return (ratingOf(b) || 0) - (ratingOf(a) || 0) || a.id.localeCompare(b.id); };
    aSecs.forEach(function (s) {
      if (codes[s.code]) return;
      var fits = function (t) { return !have.some(function (h) { return secClash(t, h); }) && !cm.some(function (h) { return secClash(t, h); }); };
      var alt = secsOf(s.code).filter(function (t) { return t.id !== s.id && fits(t); });
      var risky = regOpen() && (s.status === 'full' || s.status === 'wait');
      var pick = null;
      if (risky) pick = alt.filter(function (t) { return t.status === 'open'; }).sort(byProf)[0] || null;
      if (!pick) pick = alt.filter(function (t) { return !regOpen() || t.status !== 'full'; }).sort(byProf)[0] || null;
      if (!pick && fits(s)) pick = s;
      if (!pick) return;
      out.push(pick); have.push(pick); codes[s.code] = 1;
    });
    return out;
  }
  /* what this device drafted, per account and term: {A:[crns],B:[...],C:[...]} — a plan is untouched while it holds exactly that */
  function dKey() { var t = ''; try { t = mcTerm(); } catch (e) {} return 'professify_drafted_' + (uid() || 'anon') + '_' + t; }
  function drafted() { try { return JSON.parse(localStorage.getItem(dKey()) || 'null') || {}; } catch (e) { return {}; } }
  function untouched(sl, d) {
    var cur = (TCPlans.get(sl).sections || []).map(function (x) { return String(x.class_nbr); });
    if (!cur.length) return true;
    var was = (d[sl] || []).map(String);
    return was.length === cur.length && cur.every(function (x) { return was.indexOf(x) >= 0; });
  }
  function draftAll() {
    if (!window.TCPlans) return;
    var R = planRank(), d = drafted();
    var changed = SLOTS.filter(function (sl) { return !untouched(sl, d); });
    var skip = {};
    if (changed.length) {
      var ok = false; try { ok = window.confirm((changed.length === 1 ? 'Plan ' + changed[0] + ' has' : 'Plans ' + changed.join(' and ') + ' have') + ' classes you chose. Replace ' + (changed.length === 1 ? 'it' : 'them') + ' with a draft?'); } catch (e) {}
      if (!ok) changed.forEach(function (sl) { skip[sl] = 1; });
    }
    var A = planDraft(R, []);
    if (!A.length) { toast('Nothing to draft yet — no class you still need fits ' + termLabel()); return; }
    var B = planDraftB(A);
    var Rc = planRank({ friendsX: 2.5 });
    var C = planDraft(Rc, [A, B]);
    var out = { A: A, B: B, C: C }, n = 0;
    SLOTS.forEach(function (sl) {
      if (skip[sl]) return;
      var list = out[sl].map(function (s) { return { code: s.code, class_nbr: s.id }; });
      d[sl] = list.map(function (x) { return x.class_nbr; });
      TCPlans.setSections(sl, list, 'draft'); n++;
    });
    d.at = Date.now();
    try { localStorage.setItem(dKey(), JSON.stringify(d)); } catch (e) {}
    toast(n ? 'Drafted ' + (n === 3 ? 'Plans A, B and C' : SLOTS.filter(function (sl) { return !skip[sl]; }).map(function (x) { return 'Plan ' + x; }).join(' and ')) : 'Your plans are as you left them');
    render();
  }

  /* ---- the screen ---- */
  function seatHtml(s) {
    if (!s || !s.s || !s.s.seat) return '<div class="st">Seats not posted</div>';
    var t = ''; try { var sp = seatParts(s.s.seat); t = sp.unknown ? '' : sp.open; } catch (e) {}
    return t ? '<div class="st ' + esc(s.status) + '">' + esc(t) + '</div>' : '<div class="st">Seats not posted</div>';
  }
  function faces(list) {
    if (!list.length) return '';
    var h = list.slice(0, 4).map(function (f) { var fc = ''; try { fc = faceHtml(f); } catch (e) { fc = esc((f.name || '?')[0]); } return '<span class="fc" title="' + esc(f.name || '') + '">' + fc + '</span>'; }).join('');
    return '<div class="bd-faces">' + h + (list.length > 4 ? '<span>+' + (list.length - 4) + '</span>' : '') + '<span style="margin-left:4px">' + (list.length === 1 ? esc(String(list[0].name || '').split(' ')[0]) : list.length + ' friends') + '</span></div>';
  }
  function tileHtml(c, rank) {
    var s = c.best, nm = ''; try { nm = fp_name(c.code) || ((classInfo(c.code) || {}).name) || ''; } catch (e) {}
    var cur = TCPlans.cur(), inCur = s && TCPlans.slotsHaving(s.id).indexOf(cur) >= 0, slots = inPlanSlots(c.code);
    var rt = s ? ratingOf(s) : null;
    var pop = UI.why === c.code ? '<div class="bd-pop" role="note">' + PL_PARTS.map(function (p) { return '<div><span>' + p[1] + '</span><b>' + c.parts[p[0]] + ' / ' + p[2] + '</b></div>'; }).join('') + '<div class="tot"><span>Score, by what matters to you</span><span>' + Math.round(c.wscore) + '</span></div></div>' : '';
    return '<div class="bd-tile" data-code="' + esc(c.code) + '" data-rank="' + rank + '">'
      + '<div class="c">' + esc(c.code) + (slots.length ? '<span class="bd-chip" style="padding:1px 7px;font-size:11px">Plan ' + slots.join(', ') + '</span>' : '') + '</div>'
      + '<div class="nm">' + esc(nm) + '</div>'
      + (s ? '<div class="w">' + esc(s.days || (s.async ? 'No set meeting time' : 'Time not posted')) + '</div>' : '')
      + (s ? '<div class="p">' + esc(s.prof || 'Staff') + (rt != null ? ' <b style="color:' + (typeof scoreColor === 'function' ? scoreColor(s.rating) : 'inherit') + '">' + rt.toFixed(1) + ' ★</b>' : '') + '</div>' : '')
      + faces(c.fr) + seatHtml(s)
      + '<button type="button" class="bd-why" onclick="TCBuilder.why(\'' + ja(c.code) + '\')" aria-expanded="' + (UI.why === c.code) + '">Why it’s #' + rank + '</button>' + pop
      + (s ? '<button type="button" class="bd-add' + (inCur ? ' in' : '') + '" title="' + (inCur ? 'In Plan ' + cur : 'Add to Plan ' + cur) + '" aria-label="' + (inCur ? 'In Plan ' + cur : 'Add ' + esc(c.code) + ' to Plan ' + cur) + '" onclick="TCBuilder.add(\'' + ja(c.code) + '\',\'' + ja(s.id) + '\')">' + (inCur ? '✓' : '+') + '</button>' : '')
      + '</div>';
  }
  function reqCards(R) {
    var rank = {}; R.all.forEach(function (c, i) { rank[c.code] = i + 1; });
    var groups = [];
    if (R.audit) {
      R.X.open.filter(function (b) { return !auditIsTotal(b); }).forEach(function (b) {
        var opts = R.all.filter(function (c) { return c.fills.indexOf(b) >= 0; });
        groups.push({ b: b, key: 'a' + curAudit().reqs.indexOf(b), title: b.label || 'Requirement', tag: auditTag(b), opts: opts,
          sub: [b.units && b.units.need != null ? auditNum(b.units.need) + ' units' : b.courses && b.courses.need != null ? auditNum(b.courses.need) + ' class' + (+b.courses.need === 1 ? '' : 'es') : ''].filter(Boolean).join(' · ') });
      });
    } else {
      var by = {};
      R.all.forEach(function (c) { var key = c.key; if (!by[key]) { by[key] = { key: key, title: c.n ? (c.n.choice ? 'Pick 1: ' + c.n.codes.join(', ') : (c.n.title || c.code)) : 'GE Area ' + c.geA.join(', '), tag: '', opts: [] }; groups.push(by[key]); } by[key].opts.push(c); });
    }
    groups.sort(function (a, b) { var x = a.opts[0] ? rank[a.opts[0].code] : 1e9, y = b.opts[0] ? rank[b.opts[0].code] : 1e9; return x - y; });
    return groups.map(function (g) {
      var all = UI.more[g.key], shown = all ? g.opts : g.opts.slice(0, 3);
      var idx = g.b ? curAudit().reqs.indexOf(g.b) : -1;
      return '<section class="bd-card bd-req" data-req="' + esc(g.title) + '"><div class="bd-rq">' + (g.tag || '') + '<span class="t">' + esc(g.title) + '</span>'
        + (idx >= 0 ? '<button type="button" class="bd-mark" onclick="TCBuilder.markDone(' + idx + ')">Mark done</button>' : '')
        + (g.sub ? '<span class="s">' + esc(g.sub) + '</span>' : '') + '</div>'
        + (shown.length ? '<div class="bd-tiles">' + shown.map(function (c) { return tileHtml(c, rank[c.code]); }).join('') + '</div>' : '<div class="bd-none">None of its classes is offered ' + esc(termLabel()) + ' that you can take yet.</div>')
        + (g.opts.length > 3 ? '<button type="button" class="bd-more" onclick="TCBuilder.more(\'' + ja(g.key) + '\')">' + (all ? 'Show fewer' : 'See more · ' + (g.opts.length - 3)) + '</button>' : '')
        + '</section>';
    }).join('');
  }
  function termCard() {
    var cur = TCPlans.cur(), secs = plansSecs(cur), units = 0, unk = 0;
    secs.forEach(function (s) { var u = unitsOf(s.code); if (u == null) unk++; else units += u; });
    regSecs().forEach(function (s) { var u = unitsOf(s.code); if (u != null) units += u; });
    var tgt = plUnitsTarget(), o = prefOrder();
    var reg = ''; try { if (typeof regSlotHtml === 'function') reg = regSlotHtml('builder'); } catch (e) {}
    return '<aside class="bd-term"><div class="bd-card bd-tc">' + reg
      + '<div class="bd-th">Filling</div><div class="bd-slots">' + SLOTS.map(function (sl) { var n = (TCPlans.get(sl).sections || []).length; return '<button type="button" class="bd-slot' + (sl === cur ? ' on' : '') + '" aria-pressed="' + (sl === cur) + '" onclick="TCBuilder.slot(\'' + sl + '\')">Plan ' + sl + (n ? ' · ' + n : '') + '</button>'; }).join('') + '</div>'
      + '<div class="bd-units' + (units > tgt ? ' over' : '') + '" style="margin-top:10px"><b>' + units + '</b> of ' + tgt + ' units' + (unk ? ' · ' + unk + ' unknown' : '') + '</div>'
      + '<div class="bd-th">What matters most to you?</div><ol class="bd-rank">' + o.map(function (x, i) { return '<li data-pref="' + x + '"><span class="n">' + (i + 1) + '</span><span class="l">' + PREF_LABEL[x] + '</span><button type="button" class="bd-mv" aria-label="Move ' + PREF_LABEL[x] + ' up" onclick="TCBuilder.move(\'' + x + '\',-1)"' + (i === 0 ? ' disabled' : '') + '>▲</button><button type="button" class="bd-mv" aria-label="Move ' + PREF_LABEL[x] + ' down" onclick="TCBuilder.move(\'' + x + '\',1)"' + (i === 2 ? ' disabled' : '') + '>▼</button></li>'; }).join('') + '</ol>'
      + '<label class="bd-ur" style="margin-top:8px">Units per term <select id="bdUnits" onchange="TCBuilder.units(this.value)">' + [12, 13, 14, 15, 16, 17, 18, 19, 20].map(function (u) { return '<option' + (u === tgt ? ' selected' : '') + '>' + u + '</option>'; }).join('') + '</select></label>'
      + (UI.prefsErr === 'missing' || (P && P.local && uid()) ? '<div class="bd-note">Kept on this device for now.</div>' : '')
      + '<button type="button" class="bd-go" id="bdDraft" onclick="TCBuilder.draft()">Draft my plans</button>'
      + '</div></aside>';
  }
  function render() {
    var out = document.getElementById('plBuilderOut'); if (!out) return;
    if (!window.TCPlans) return;
    if (UI.prefsFor !== (uid() || 'anon')) { loadPrefs().then(function () { render(); }, function () {}); P = readLocalPrefs(); UI.prefsFor = uid() || 'anon'; }
    var A = curAudit(), R = null;
    try { R = planRank(); } catch (e) { R = null; try { if (typeof trackError === 'function') trackError('builder rank: ' + (e && e.message)); } catch (_) {} }
    UI.R = R;
    var cat = A && A.catalog ? '<span class="bd-chip" title="The catalog on your Degree Progress Report">' + esc(A.catalog) + ' catalog</span>' : '';
    var head = '<div class="bd-head"><h2>' + esc(termLabel()) + '</h2>' + cat + '<button type="button" class="bd-past" onclick="TCBuilder.past()">Past classes →</button></div>';
    var body;
    if (!A && !(R && R.hasFlow)) {
      body = '<section class="bd-card bd-empty bd-upload"><h3>Upload your Degree Progress Report</h3><p>TermChamp reads what you still need and picks your ' + esc(termLabel()) + ' classes from it.</p><button type="button" class="bd-go" onclick="dprPick()">Upload report</button></section>';
    } else if (R && R.done) {
      body = '<section class="bd-card bd-empty bd-done"><h3>Nothing left to plan</h3><p>' + (R.audit ? 'Every line on your report is filled or in progress.' : 'Everything on your flowchart is done or in progress.') + '</p></section>';
    } else if (R) {
      body = (reqCards(R) || '<section class="bd-card bd-none">Nothing you still need is offered ' + esc(termLabel()) + ' that you can take yet.</section>');
    } else body = '<p class="pl3-quiet">Planner couldn’t be drawn just now.</p>';
    var fa = document.activeElement, fk = fa && out.contains(fa) ? (fa.id ? '#' + fa.id : fa.getAttribute('aria-label') ? '[aria-label="' + String(fa.getAttribute('aria-label')).replace(/"/g, '\\"') + '"]' : '') : '';
    /* the same screen is never redrawn: a redraw under the pointer would eat a click */
    var html = '<div class="bd">' + head + '<div class="bd-grid"><div class="bd-main">' + body + '</div>' + termCard() + '</div></div>';
    if (html === out.__bdHtml && out.querySelector('.bd')) return;
    out.__bdHtml = html; out.innerHTML = html;
    if (fk) { try { var el = out.querySelector(fk); if (el && !el.disabled) el.focus({ preventScroll: true }); } catch (e) {} }
  }
  /* from outside (plans saved, the record loaded, the tab opened): once per burst, and only while the Planner shows */
  var schedT = null;
  window.tcBuilderRender = function () {
    clearTimeout(schedT);
    schedT = setTimeout(function () { var wr = document.getElementById('schedPlanWrap'); if (wr && wr.style.display === 'none') return; try { render(); } catch (e) {} }, 30);
  };
  window.TCBuilder = {
    rank: function (o) { return planRank(o); }, render: render, prefs: function () { return { order: prefOrder(), units: plUnitsTarget(), local: !!(P && P.local) }; },
    draft: draftAll, draftOnly: function () { var R = planRank(), A = planDraft(R, []), B = planDraftB(A), C = planDraft(planRank({ friendsX: 2.5 }), [A, B]); return { A: A, B: B, C: C }; },
    add: function (code, id) { var cur = TCPlans.cur(), had = (TCPlans.get(cur).sections || []).filter(function (x) { return x.code === code; })[0];
      if (TCPlans.slotsHaving(id).indexOf(cur) >= 0) { TCPlans.remove(cur, id); }
      else if (had) { TCPlans.replace(cur, had.class_nbr, code, id); toast(code + ' switched to this section in Plan ' + cur); }
      else if (TCPlans.add(cur, code, id)) toast(code + ' added to Plan ' + cur);
      render(); },
    slot: function (sl) { if (SLOTS.indexOf(sl) >= 0) TCPlans.setCur(sl); render(); },
    why: function (code) { UI.why = UI.why === code ? null : code; render(); },
    more: function (key) { UI.more[key] = !UI.more[key]; render(); },
    move: async function (x, d) { var o = prefOrder().slice(), i = o.indexOf(x), j = i + d; if (i < 0 || j < 0 || j > 2) return; o[i] = o[j]; o[j] = x; var e = savePrefs(o, plUnitsTarget()); render(); e = await e; if (e) toast(e); render(); },
    units: async function (v) { var e = await savePrefs(prefOrder(), +v); if (e) toast(e); render(); },
    markDone: async function (i) { var A = curAudit(); var b = A && A.reqs[i]; if (!b) return; var list = auditOverrides().concat([{ code: b.code || null, label: b.label || '' }]); var e = await auditSaveOverrides(list); if (e) toast(e); else toast('Marked done: ' + (b.label || 'requirement')); render(); },
    past: function () { try { TCPlans.openDegree(); var r = document.getElementById('plRecord'); if (r) r.scrollIntoView({ behavior: 'smooth', block: 'start' }); } catch (e) {} }
  };
}());
</script>
'''

one('<!-- PLANS:END -->\n<style id="app-look">', '<!-- PLANS:END -->\n' + CSS + JS + '<style id="app-look">')
f.write_text(s)
print('ok')
