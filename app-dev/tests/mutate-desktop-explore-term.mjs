/* Mutation check for check-desktop-explore-term: each mutant breaks one promise of Explore's Fall / Spring switch on the
   website (website-explore-term, 2026-10-14); check-desktop-explore-term must FAIL on every one.
   Run: SRC_DIR=<repo> node mutate-desktop-explore-term.mjs  (MUT_ONLY="a|b") */
import fs from 'node:fs'; import path from 'node:path'; import { execFileSync } from 'node:child_process';
const SRC = process.env.SRC_DIR || path.resolve('../..');
const M = [
  ["explore-term: Fall's feed is read for Spring too", "var FALL={term:'',sec:null,idx:null,ready:false,loading:false,err:false,on:false,c:{}};", "var FALL={term:'',sec:null,idx:null,ready:false,loading:false,err:false,on:false,c:{}}; setTimeout(function(){ try{ if(mcTwoTerms())loadFallAll(); }catch(e){} },800);", 'switch'],
  ["explore-term: Fall's rows go into Spring's SEAT_SECTIONS", "  FALL.idx=idx; FALL.sec=sec; FALL.ready=true;", "  FALL.idx=idx; FALL.sec=sec; FALL.ready=true; Object.keys(sec).forEach(function(k){ if(SEAT_SECTIONS&&!SEAT_SECTIONS[k])SEAT_SECTIONS[k]=sec[k]; });", 'switch'],
  ["explore-term: Fall's feed is cached as the seats", "  FALL.idx=idx; FALL.sec=sec; FALL.ready=true;", "  FALL.idx=idx; FALL.sec=sec; FALL.ready=true; try{ localStorage.setItem('professify_seats_cache:'+t,JSON.stringify({ts:1,idx:idx,sec:sec})); }catch(e){}", 'switch'],
  ["explore-term: the Spring globals are not given back", "    SEAT_SECTIONS=sv.ss; PROFESSIFY_SEATS=sv.ps; FRIENDS=sv.fr;", "    FRIENDS=sv.fr;", 'switch'],
  ["explore-term: Fall reads the wrong term", "course_seats?term=eq.'+encodeURIComponent(t)+'&select='+sel+'&order=course_code.asc,class_nbr.asc&limit=1000&offset='", "course_seats?term=eq.'+encodeURIComponent(mcTerm())+'&select='+sel+'&order=course_code.asc,class_nbr.asc&limit=1000&offset='", 'switch'],
  ["explore-term: Explore ignores the switch", "  if(!fallActive())return _exRender0.apply(this,arguments);", "  return _exRender0.apply(this,arguments);", 'switch'],
  ["explore-term: Fall is read again on every switch", "  if(t==='now'){ window.exSaved=false; fallEnsure(); }", "  if(t==='now'){ window.exSaved=false; FALL.ready=false; loadFallAll(); }", 'switch'],
  ["explore-term: the switch shows on the single-term site", "  if(!mcTwoTerms()){ exTermSel='spring'; return _exCtx0.apply(this,arguments); }", "", 'single'],
  ["explore-term: a Fall class page shows Spring's sections", "  inFall(function(){ return _rcp0(); });\n  out.insertAdjacentHTML", "  _rcp0();\n  out.insertAdjacentHTML", 'classPage'],
  ["explore-term: a Fall class page is not marked read-only", "<b>'+escapeHtml(mcNowLabel())+'</b> · read-only'", "<b>'+escapeHtml(mcNowLabel())+'</b>'", 'classPage'],
  ["explore-term: Add works on Fall", "    if(!fallViewing())return;\n    var t=e.target", "    return;\n    var t=e.target", 'classPage'],
  ["explore-term: the read-only message is wrong", "mcNowLabel()+' is read-only — switch to '+mcTermLabel()+' to add'", "'Not available'", 'classPage'],
  ["explore-term: the professor's teaching stays Spring's", "  return inFall(function(){ return _rpp0(); });", "  return _rpp0();", 'professor'],
  ["explore-term: a professor's Fall term is not named", "((pfNow&&mcTwoTerms())?escAcc(mcNowLabel()):'this term')", "'this term'", 'professor'],
  ["explore-term: a professor's class opens Spring from Fall", "  if(v==='prof')return pfNow;\n  if(forProf)return false;", "  if(v==='prof')return false;\n  if(forProf)return false;", 'professor'],
  ["explore-term: Home's Fall class opens Spring", "  if(v==='home'){ try{ return nowCodesWanted().indexOf(code)>=0; }catch(e){ return false; } }", "", 'home'],
  ["explore-term: Home opens every class as Fall", "  if(v==='home'){ try{ return nowCodesWanted().indexOf(code)>=0; }catch(e){ return false; } }", "  if(v==='home')return true;", 'home'],
  ["explore-term: a friend's Fall chip opens Spring", "return !!f&&frpTermOf(f)==='now';", "return false;", 'home'],
  ["explore-term: a failed Fall read loops forever", "&&!FALL.loading&&!FALL.err)loadFallAll(); }", "&&!FALL.loading)loadFallAll(); }", 'failure'],
  ["explore-term: a failed Fall read has no Retry", "<button class=\"btn primary\" onclick=\"fallRetry()\">Retry</button>", "", 'failure'],
];
const html = fs.readFileSync(path.join(SRC, 'index.html'), 'utf8');
const tmp = fs.mkdtempSync('/tmp/claude-0/mutet-');
for (const e of fs.readdirSync(SRC)) if (e !== 'index.html' && e !== '.git') fs.symlinkSync(path.join(SRC, e), path.join(tmp, e));
let caught = 0; const survived = [];
const ONLY = process.env.MUT_ONLY ? process.env.MUT_ONLY.split('|') : null;
for (const [name, a, b, test] of M) {
  if (ONLY && !ONLY.includes(name)) continue;
  const n = html.split(a).length - 1;
  if (n !== 1) { console.log('  BAD MUTANT (found ' + n + '×):', name); survived.push(name + ' (bad)'); continue; }
  fs.writeFileSync(path.join(tmp, 'index.html'), html.split(a).join(b));
  let failed = false, out = '';
  try { execFileSync('node', ['check-desktop-explore-term.mjs', '--quiet', '--only', test], { env: { ...process.env, APP_DIR: tmp }, stdio: 'pipe', timeout: 200000 }); }
  catch (e) { failed = true; out = String(e.stdout || '') + String(e.stderr || ''); }
  if (failed && (!/check-desktop-explore-term: \d+ passed, [1-9]\d* failed/.test(out) || /EADDRINUSE/.test(out))) { console.log('  BROKE   ', name, '— the run crashed/timed out; rerun it'); survived.push(name + ' (broke)'); continue; }
  if (failed) { caught++; console.log('  caught  ', name); } else { survived.push(name); console.log('  SURVIVED', name); }
}
console.log(`\nmutations: ${caught}/${ONLY ? ONLY.length : M.length} caught`);
if (survived.length) { console.log('survived:', survived.join(' | ')); process.exit(1); }
