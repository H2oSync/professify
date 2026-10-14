/* Mutation check for check-desktop-report: each mutant breaks one promise of the website's report flow
   (website-report-flow, 2026-10-14); check-desktop-report must FAIL on every one.
   Run: SRC_DIR=<repo> node mutate-desktop-report.mjs  (MUT_ONLY="a|b"; APP_PORT as for the suite) */
import fs from 'node:fs'; import path from 'node:path'; import { execFileSync } from 'node:child_process';
const SRC = process.env.SRC_DIR || path.resolve('../..');
const M = [
  // read: what was read, what is kept
  ['report: the counts line counts every line as left', "function rfCountsText(X){ return X.filled.length+' filled · '+X.open.length+' left'", "function rfCountsText(X){ return X.filled.length+' filled · '+X.live.length+' left'", 'read'],
  ['report: no catalog line', "    +(cat?'<div class=\"rf-cat\">'+escapeHtml(cat)+'</div>':'')", '', 'read'],
  ['report: the save sends the parsed lines raw', "  var reqs=auditStoredReqs(a);\n", "  var reqs=(a&&a.reqs)||[];\n", 'read'],
  ['report: a flagged line is still saved', "function auditStoredReqs(a){ return (a&&a.ok&&a.reqs?a.reqs:[]).filter(function(b){ return !b.flag; })", "function auditStoredReqs(a){ return (a&&a.ok&&a.reqs?a.reqs:[]).filter(function(b){ return true; })", 'read'],
  ['report: the verdicts are never saved', "  var e2=await saveAudit(M.audit,M.program); if(e2)notes.push(e2);", "  var e2=null;", 'read'],
  ['report: a new upsert per save (no onConflict)', "  var q; try{ q=await sb.from('degree_audit').upsert(up,{onConflict:'user_id'}); }", "  var q; try{ q=await sb.from('degree_audit').insert(up); }", 'read'],
  ['report: a line’s class shows no term', "function rfUsedText(e){ return e.c+(e.n&&e.n!==e.c?' → '+e.n:'')+(e.t?' · '+e.t:'')", "function rfUsedText(e){ return e.c+(e.n&&e.n!==e.c?' → '+e.n:'')", 'read'],
  ['report: a quarter catalog sees the flowchart', "  var sem=/semester/i.test(A.catalog||'');", "  var sem=true;", 'read'],
  ['report: a semester catalog never sees it', "  var sem=/semester/i.test(A.catalog||'');", "  var sem=false;", 'semester'],
  ['report: Past classes ignores the report', "  var _rf=false; try{ if(typeof rfRenderPast==='function')_rf=rfRenderPast(host,ledHtml); }catch(e){ _rf=false; }", "  var _rf=false;", 'read'],
  // wins
  ['report: “already” is by class alone', "x.already=H.some(function(h){ return h&&(rfK(h.code)===rfK(x.cur)||rfK(h.code)===rfK(x.code))&&(!h.term||!h.year||(h.term===x.term&&String(h.year)===String(x.year))); });", "x.already=H.some(function(h){ return h&&(rfK(h.code)===rfK(x.cur)||rfK(h.code)===rfK(x.code)); });", 'wins'],
  ['report: an unchecked row comes off anyway', "list=((M&&M.rc)||[]).filter(function(x){ return !(M.rcOff||{})[x.key]; });", "list=((M&&M.rc)||[]).filter(function(x){ return true; });", 'wins'],
  ['report: stale rows are never taken off', "    var _rd=await rfDropStale(); _rfDropped=_rd.n||0;", "    var _rd={n:0}; _rfDropped=0;", 'wins'],
  ['report: this term’s delete has no term', "    else q=sb.from('saved_classes').delete().eq('user_id',me).eq('term',nt).eq('code',x.raw);", "    else q=sb.from('saved_classes').delete().eq('user_id',me).eq('code',x.raw);", 'wins'],
  ['report: the Spring list is offered for removal', "    ((typeof nowMine==='function'?nowMine().classes:[])||[]).forEach(function(c){ var k=rfK(c);", "    myTakingCodes().forEach(function(c){ var k=rfK(c);", 'wins'],
  ['report: a record row in another term counts as on the report', "    if(keep.some(function(x){ return same(x,h)&&(h.term&&h.year?(x.term===h.term&&String(x.year)===String(h.year)):!(x.term&&x.year)); }))return;", "    if(keep.some(function(x){ return same(x,h); }))return;", 'wins'],
  // diff
  ['report: no diff after a new report', "  if(!d||d.same)return false;\n  var b=rfDiffEl();", "  return false;\n  var b=rfDiffEl();", 'diff'],
  ['report: “Take it out” does nothing', "TCPlans.setSections(P,secs); }catch(e){ return; }", "}catch(e){ return; }", 'diff'],
  ['report: a new upload forgets your marks', "    overrides:(old&&Array.isArray(old.overrides))?old.overrides:[] };", "    overrides:[] };", 'diff'],
  ['report: the old report is never read', "  var r; try{ r=await sb.from('degree_audit').select(", "  var r={error:{message:'x'}}; if(0)try{ r=await sb.from('degree_audit').select(", 'diff'],
  ['report: nothing to add means nothing saved', "  if(!past.length&&!now.length&&!_rfDropped&&!(window._dprMeta&&window._dprMeta.audit&&window._dprMeta.audit.ok)){", "  if(!past.length&&!now.length){", 'again'],
  ['report: amber too light to read', "':root,:root[data-theme=\"light\"]{--rf-amber:#92400E}", "':root,:root[data-theme=\"light\"]{--rf-amber:#E59A3A}", 'contrast'],
  ['report: another account’s ticks go up', "  if(owner!==uid){ try{ localStorage.setItem(flag,'1'); }catch(e){} return; }", "", 'marks'],
  // in progress now
  ['report: this term’s rows are finished', "  return row>now||(row===now&&nowTermOn());", "  return row>now;", 'inProgress'],
  ['report: taking ignores the record', "    (typeof myHistory!=='undefined'?myHistory:[]).forEach(function(h){ if(h&&h.code&&histNotDone(h)){ var c=canonCode(h.code)||h.code; if(!_k[c]){ _k[c]=1; a.push(c); } } }); }catch(e){}", "}catch(e){}", 'inProgress'],
  ['report: the term never ends', "  if(u&&d>=u&&e<u)return true;\n  return d<=e;", "  return true;", 'inProgress'],
  ['report: last term’s end applies in Spring', "  if(u&&d>=u&&e<u)return true;\n", "", 'inProgress'],
  ['report: the mirror keeps classes in progress', "      .filter(function(h){ return !(typeof histNotDone==='function'&&histNotDone(h)); })   /* website-report-flow: finished rows only */\n", "", 'inProgress'],
  ['report: transfer credit this term is in progress', "  try{ if(typeof pcReadSource==='function'){ var s=pcReadSource(h.professor); if(s&&s.src&&s.src.mark)return false; } }catch(e){}", "", 'inProgress'],
  // local
  ['report: nothing kept on the device', "function auditStoreLocal(o){ try{ localStorage.setItem(auditKey(),JSON.stringify(o)); }catch(e){} }", "function auditStoreLocal(o){}", 'local'],
  ['report: what waited never goes up', "  if(c&&c.requirements&&c.pending&&(!r.data||!r.data.read_at||(c.read_at||'')>r.data.read_at)){", "  if(false){", 'local'],
  ['report: another account’s copy is read', "function curAudit(){ return (AUDIT&&typeof sbUser!=='undefined'&&sbUser&&AUDIT_UID===sbUser.id)?AUDIT:null; }", "function curAudit(){ return AUDIT||(function(){ try{ var k=Object.keys(localStorage).find(function(x){ return /^tc-audit:/.test(x); }); return k?auditFrom(JSON.parse(localStorage.getItem(k))):null; }catch(e){ return null; } })(); }", 'local'],
  // old audit
  ['report: an old audit gets the new screen', "  if(!X.live.some(function(b){ return Array.isArray(b.used); }))return 'old';", "", 'oldAudit'],
  // concentrations
  ['report: concentrations lose their shape', "        if(!sh)return {name:k,units:0,note:'',classes:all.map(nm)};", "        return {name:k,units:0,note:'',classes:all.map(nm)};", 'conc'],
  ['report: a choice spot is not checked', "    if(mm)mm=withChoiceCodes(mm);   /* website-report-flow (2026-10-14) */", "", 'conc'],
  // marks
  ['report: device ticks never go up', "  var up=rfDeviceTicks().filter(", "  var up=[].filter(", 'marks'],
  ['report: device ticks go up every load', "  if(allOk)try{ localStorage.setItem(flag,'1'); }catch(e){}", "", 'marks'],
  ['report: coded rows go up as marks', "function rfSlotMarkable(sl){ return !!sl&&sl.id!=null&&!(sl.code&&(typeof window.plSlotCheckable!=='function'||window.plSlotCheckable(sl))); }", "function rfSlotMarkable(sl){ return !!sl&&sl.id!=null; }", 'marks'],
  ['report: the account’s marks don’t count', "    var _mk=function(sl){ try{ return typeof window.rfMarked==='function'&&window.rfMarked(mm.name,sl); }catch(e){ return false; } };", "    var _mk=function(sl){ return false; };", 'marks'],
  ['report: a mark counts on any row', "  return MY_MARKS.some(function(m){ return rfNormMajor(m.major)===mj&&m.slot===id&&m.label===w; });", "  return MY_MARKS.some(function(m){ return rfNormMajor(m.major)===mj; });", 'marks'],
];
const html = fs.readFileSync(path.join(SRC, 'index.html'), 'utf8');
fs.mkdirSync('/tmp/claude-0', { recursive: true });
const tmp = fs.mkdtempSync('/tmp/claude-0/mutr-');
for (const e of fs.readdirSync(SRC)) if (e !== 'index.html' && e !== '.git') fs.symlinkSync(path.join(SRC, e), path.join(tmp, e));
let caught = 0; const survived = [];
const ONLY = process.env.MUT_ONLY ? process.env.MUT_ONLY.split('|') : null;
for (const [name, a, b, test] of M) {
  if (ONLY && !ONLY.includes(name)) continue;
  const n = html.split(a).length - 1;
  if (n !== 1) { console.log('  BAD MUTANT (found ' + n + '×):', name); survived.push(name + ' (bad)'); continue; }
  fs.writeFileSync(path.join(tmp, 'index.html'), html.split(a).join(b));
  let failed = false, out = '';
  try { execFileSync('node', ['check-desktop-report.mjs', '--quiet', '--only', test], { env: { ...process.env, APP_DIR: tmp }, stdio: 'pipe', timeout: 600000 }); }
  catch (e) { failed = true; out = String(e.stdout || '') + String(e.stderr || ''); }
  if (failed && (!/check-desktop-report: \d+ passed, [1-9]\d* failed/.test(out) || /EADDRINUSE/.test(out))) { console.log('  BROKE   ', name, '— the run crashed; rerun it'); survived.push(name + ' (broke)'); continue; }
  if (failed) { caught++; console.log('  caught  ', name); } else { survived.push(name); console.log('  SURVIVED', name); }
}
console.log(`\nmutations: ${caught}/${ONLY ? ONLY.length : M.length} caught`);
if (survived.length) { console.log('survived:', survived.join(' | ')); process.exit(1); }
