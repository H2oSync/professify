/* Mutation check for check-desktop-terms: each mutant breaks one promise of the website's two-term wall
   (website-spring-wall, 2026-10-14); check-desktop-terms must FAIL on every one.
   Run: SRC_DIR=<repo> node mutate-desktop-terms.mjs  (MUT_ONLY="a|b") */
import fs from 'node:fs'; import path from 'node:path'; import { execFileSync } from 'node:child_process';
const SRC = process.env.SRC_DIR || path.resolve('../..');
const M = [
  ["terms: a friend's sections read with no term", "        .select('user_id,code,class_nbr,section,instructor,days,status,wl_pos')\n        .in('user_id',friendIds).eq('term',mcTerm());", "        .select('user_id,code,class_nbr,section,instructor,days,status,wl_pos')\n        .in('user_id',friendIds);", 'wall'],
  ["terms: who's in class reads this term", "hmFriendMeets(frNow(f)):{meets:[]};", "hmFriendMeets(f):{meets:[]};", 'wall'],
  ["terms: Home's friend card reads this term", "  f=frNow(f);                       /* Home shows where they are now", "  /* Home shows where they are now", 'wall'],
  ["terms: group free time reads this term", "    var f=frNow((typeof findFriend==='function')?findFriend(m.id):null);", "    var f=(typeof findFriend==='function')?findFriend(m.id):null;", 'wall'],
  ["terms: your week now is My Classes", "    var _nm=nowMine(), mm=(typeof myClassMeets==='function')?myClassMeets(_nm.classes,_nm.meta):[];", "    var mm=(typeof myClassMeets==='function')?myClassMeets(myClasses):[];", 'wall'],
  ["terms: Home's My schedule is My Classes", "  var _nm=nowMine(), codes=_nm.classes;      /* the week you are in", "  var _nm={classes:myClasses,meta:myClassMeta}, codes=_nm.classes;      /* the week you are in", 'wall'],
  ["terms: Rate's current professors are Spring's", "    var _nm=nowMine();                  /* the now-term", "    var _nm={classes:myClasses,meta:myClassMeta};                  /* the now-term", 'wall'],
  ["terms: Fall's seats read for the whole term", "+'&course_code=in.'+encodeURIComponent(list)", "+''", 'wall'],
  ["terms: My Classes has no Fall view", "  if(mcTwoTerms()&&mcTermView()==='now'){ mcRenderNow(out); return; }", "", 'wall'],
  ["terms: a friend's page opens on this term", "  var n=frNow(f0); return (!(n.classes||[]).length&&(f0.classes||[]).length)?'term':'now';", "  return 'term';", 'wall'],
  ["terms: a Fall class takes Spring's time", "  if(meta===NOW_MINE.meta&&mcTwoTerms()){", "  if(false){", 'nowTimes'],
  ["terms: the section lookup ignores its source", "function secByCrn(code,crn,src){var list=(typeof clsSections==='function')?clsSections(code,src):[];", "function secByCrn(code,crn,src){var list=(typeof clsSections==='function')?clsSections(code):[];", 'nowTimes'],
  ["terms: one set of local keys for every term", "return t==='2268'?k:(k+':'+t); };", "return k; };", 'staleLocal'],
  ["terms: Spring's local keys renamed for Fall too", "return t==='2268'?k:(k+':'+t); };", "return k+':'+t; };", 'staleLocal'],
  ["terms: together tomorrow from Spring", "    f=frNow(f); var _nm=nowMine();      /* \"together tomorrow\"", "    var _nm={classes:myClasses,meta:myClassMeta};      /* \"together tomorrow\"", 'wall'],
  ["terms: taking is Spring only", "    if(mcTwoTerms())lists.push({codes:NOW_MINE.classes,meta:NOW_MINE.meta});", "", 'wall'],
  ["terms: the waitlist write has no term", "upsert({user_id:sbUser.id,term:mcTerm(),code:code,waitlist_pos:pos})", "upsert({user_id:sbUser.id,code:code,waitlist_pos:pos})", 'wall'],
  ["terms: a report's registered Spring isn't Spring", "      else if(lab===_tl){ r._now=false; r._reg=true; }\n", "", 'dprReport'],
  ["terms: a report's Fall is the newest term again", "      if(lab===_nl){ r._now=true; r._reg=false; }\n", "", 'dprReport'],
  ["terms: the report's in-progress Fall goes to Spring", "  if(typeof mcTwoTerms==='function'&&mcTwoTerms()){\n    var _nowRows=", "  if(false){\n    var _nowRows=", 'dprTwoTerms'],
  ["terms: registered Spring filed as finished", "  var past=tiRows.filter(function(r){return r.pick&&!r._now&&!r._reg&&!r._later&&!r.already;});", "  var past=tiRows.filter(function(r){return r.pick&&!r._now&&!r.already;});", 'dprTwoTerms'],
  ["terms: now never ends", "  if(u&&mcPacificDay()>=u)return mcTerm();", "", 'nowUntil'],
  ["terms: now ends a day early (UTC)", "  if(u&&mcPacificDay()>=u)return mcTerm();", "  if(u&&new Date().toISOString().slice(0,10)>=u)return mcTerm();", 'nowUntil'],
  ["terms: the shipped term is still Fall", "  TERM: '2274',\n  TERM_LABEL: 'Spring 2027',", "  TERM: '2268',\n  TERM_LABEL: 'Fall 2026',", 'shipped'],
  ["terms: the config isn't merged", "}, window.PROFESSIFY_CONFIG || {});", "}, {});", 'single'],
];
const html = fs.readFileSync(path.join(SRC, 'index.html'), 'utf8');
const tmp = fs.mkdtempSync('/tmp/claude-0/mutt-');
for (const e of fs.readdirSync(SRC)) if (e !== 'index.html' && e !== '.git') fs.symlinkSync(path.join(SRC, e), path.join(tmp, e));
let caught = 0; const survived = [];
const ONLY = process.env.MUT_ONLY ? process.env.MUT_ONLY.split('|') : null;
for (const [name, a, b, test] of M) {
  if (ONLY && !ONLY.includes(name)) continue;
  const n = html.split(a).length - 1;
  if (n !== 1) { console.log('  BAD MUTANT (found ' + n + '×):', name); survived.push(name + ' (bad)'); continue; }
  fs.writeFileSync(path.join(tmp, 'index.html'), html.split(a).join(b));
  let failed = false, out = '';
  try { execFileSync('node', ['check-desktop-terms.mjs', '--quiet', '--only', test], { env: { ...process.env, APP_DIR: tmp }, stdio: 'pipe', timeout: 400000 }); }
  catch (e) { failed = true; out = String(e.stdout || '') + String(e.stderr || ''); }
  if (failed && (!/check-desktop-terms: \d+ passed, [1-9]\d* failed/.test(out) || /EADDRINUSE/.test(out))) { console.log('  BROKE   ', name, '— the run crashed; rerun it'); survived.push(name + ' (broke)'); continue; }
  if (failed) { caught++; console.log('  caught  ', name); } else { survived.push(name); console.log('  SURVIVED', name); }
}
console.log(`\nmutations: ${caught}/${ONLY ? ONLY.length : M.length} caught`);
if (survived.length) { console.log('survived:', survived.join(' | ')); process.exit(1); }
