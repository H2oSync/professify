/* Mutation check for check-desktop-escaping: each mutant reverts ONE fix of security-escaping (2026-10-14); check-desktop-escaping must FAIL on every one.
   Run: SRC_DIR=<repo> node mutate-desktop-escaping.mjs  (MUT_ONLY="a|b")   — SRC_DIR's index.html must already carry the patch. */
import fs from 'node:fs'; import path from 'node:path'; import { execFileSync } from 'node:child_process';
const SRC = process.env.SRC_DIR || path.resolve('../..');
const M = [
  /* ---- the use: handlers */
  ["use: tapA (Async rail) escapes only the quote", "        var tapA=jsAttr(m.code);", "        var tapA=String(m.code).replace(/'/g,\"\\\\'\");", 'profileRails'],
  ["use: tapT (Time TBA rail) escapes only the quote", "        var tapT=jsAttr(m.code);", "        var tapT=String(m.code).replace(/'/g,\"\\\\'\");", 'profileRails'],
  ["use: Async rail crn is escAcc in a JS string", "cbTap(\\''+tapA+'\\',\\''+jsAttr(m.crn||'')+'\\'", "cbTap(\\''+tapA+'\\',\\''+escAcc(m.crn||'')+'\\'", 'myCalendar'],
  ["use: Time TBA rail crn is escAcc in a JS string", "cbTap(\\''+tapT+'\\',\\''+jsAttr(m.crn||'')+'\\'", "cbTap(\\''+tapT+'\\',\\''+escAcc(m.crn||'')+'\\'", 'myCalendar'],
  ["use: timed block code (already jsAttr) reverts", "var tapCode=jsAttr(m.code);\n        /* The block names", "var tapCode=escAcc(m.code);\n        /* The block names", 'myCalendar'],
  ["use: timed block crn is escAcc in a JS string", "cbTap(\\''+tapCode+'\\',\\''+jsAttr(m.crn||'')+'\\','+(_own?1:0)+')\" onkeydown", "cbTap(\\''+tapCode+'\\',\\''+escAcc(m.crn||'')+'\\','+(_own?1:0)+')\" onkeydown", 'myCalendar'],
  ["use: Home chips use esc() in a JS string", "openClassFromFeed(\\''+jsAttr(c)+'\\')\" style=\"cursor:pointer\">", "openClassFromFeed(\\''+esc(c)+'\\')\" style=\"cursor:pointer\">", 'home'],
  ["use: Home recs use escAcc() in a JS string", "onclick=\"openClassFromFeed(\\''+jsAttr(x.code)+'\\')\">", "onclick=\"openClassFromFeed(\\''+escAcc(x.code)+'\\')\">", 'home'],
  ["use: class page Save uses escAcc() in a JS string", "toggleSaveClass(\\''+jsAttr(code)+'\\');renderClassPage()", "toggleSaveClass(\\''+escAcc(code)+'\\');renderClassPage()", 'classPage'],
  ["use: class page Send uses escAcc() in a JS string", "shOpen(\\'class\\',\\''+jsAttr(code)+'\\',event)\">'+CP_SEND", "shOpen(\\'class\\',\\''+escAcc(code)+'\\',event)\">'+CP_SEND", 'classPage'],
  ["use: class page 'I'm in this' crn uses escAcc()", "class=\"cp-enroll\" title=\"Cal Poly has you enrolled or waitlisted in this section? Add it to My Classes.\" onclick=\"mcEnrollSec(\\''+jsAttr(code)+'\\',\\''+jsAttr(crn)+'\\'", "class=\"cp-enroll\" title=\"Cal Poly has you enrolled or waitlisted in this section? Add it to My Classes.\" onclick=\"mcEnrollSec(\\''+jsAttr(code)+'\\',\\''+escAcc(crn)+'\\'", 'classPage'],
  ["use: My Classes raw code in the remove button", "onclick=\"mcAskRemove(\\''+jsAttr(i.code)+'\\',event)\">&times;</button>", "onclick=\"mcAskRemove(\\''+i.code+'\\',event)\">&times;</button>", 'myClasses'],
  ["use: My Classes waitlist button uses escAcc()", "onclick=\"event.stopPropagation();wlOpen(\\''+jsAttr(i.code)+'\\')\">⏳ '+(sec.wlPos", "onclick=\"event.stopPropagation();wlOpen(\\''+escAcc(i.code)+'\\')\">⏳ '+(sec.wlPos", 'myClasses'],
  ["use: My Classes remove uses escAcc()", "('mcAskRemove(\\''+jsAttr(i.code)+'\\',event)'))", "('mcAskRemove(\\''+escAcc(i.code)+'\\',event)'))", 'myClasses'],
  ["use: My Classes class link uses escAcc()", " onclick=\"event.stopPropagation();gotoSection(\\''+jsAttr(i.code)+'\\')\"'", " onclick=\"event.stopPropagation();gotoSection(\\''+escAcc(i.code)+'\\')\"'", 'myClasses'],
  /* ---- the use: term / year */
  ["use: 'friend took this' prints the label raw", "took this${tookLabel(f.took)?' '+escapeHtml(tookLabel(f.took)):''}${withWho}`;", "took this${tookLabel(f.took)?' '+tookLabel(f.took):''}${withWho}`;", 'history'],
  ["use: 'most recently' prints the label raw", "most recently '+escapeHtml(tookLabel(first.took)):''}`);", "most recently '+tookLabel(first.took):''}`);", 'history'],
  ["use: a friend's Took tab prints term/year raw", "<span class=\"ht\">${escapeHtml([h.term,h.year].filter(Boolean).join(' '))}</span>", "<span class=\"ht\">${h.term} ${h.year}</span>", 'history'],
  ["use: the notification prints the year raw", "` from ${escapeHtml(n.term)} ${escapeHtml(n.year)}`", "` from ${escapeHtml(n.term)} ${n.year}`", 'history'],
  /* ---- the door */
  ["door: saved_classes rows are not cleaned", "    if(Array.isArray(classes))classes=classes.map(frCleanRow).filter(Boolean);", "", 'door'],
  ["door: my_sections rows are not cleaned", "        fs.data.map(frCleanRow).filter(Boolean).forEach(r=>{", "        fs.data.forEach(r=>{", 'door'],
  ["door: the now-term saved_classes are not cleaned", "          _na.data=_na.data.map(frCleanRow).filter(Boolean);", "", 'doorNow'],
  ["door: the now-term my_sections are not cleaned", "_nb.data.map(frCleanRow).filter(Boolean).forEach(function(r){", "_nb.data.forEach(function(r){", 'doorNow'],
  ["door: history code is not checked", "const _hc=h?frCleanCode(h.code):'';", "const _hc=h?String(h.code):'';", 'door'],
  ["door: history term is not coerced", "term:frCleanTerm(h.term),year:frCleanYear(h.year),professor:h.professor||''", "term:h.term,year:frCleanYear(h.year),professor:h.professor||''", 'door'],
  ["door: history year is not coerced", "term:frCleanTerm(h.term),year:frCleanYear(h.year),professor:h.professor||''", "term:frCleanTerm(h.term),year:h.year,professor:h.professor||''", 'door'],
  ["door: a hostile crn is kept", "function frCleanCrn(n){ var t=String(n==null?'':n).trim(); return /^\\d{1,10}$/.test(t)?t:''; }", "function frCleanCrn(n){ var t=String(n==null?'':n).trim(); return t; }", 'door'],
  ["door: any code is a code", "  return m?(m[1]+' '+m[2]):'';\n}", "  return normCourse(c);\n}", 'door'],
  ["door: & subjects are refused", "var m=/^([A-Z&]{2,5})\\s*(\\d{3,4}[A-Z]?)$/.exec(normCourse(c));", "var m=/^([A-Z]{2,5})\\s*(\\d{3,4}[A-Z]?)$/.exec(normCourse(c));", 'door'],
  ["door: letter-suffix codes are refused", "var m=/^([A-Z&]{2,5})\\s*(\\d{3,4}[A-Z]?)$/.exec(normCourse(c));", "var m=/^([A-Z&]{2,5})\\s*(\\d{3,4})$/.exec(normCourse(c));", 'door'],
  ["door: a hostile waitlist spot is kept", "  if('wl_pos' in r)o.wl_pos=frCleanPos(r.wl_pos);", "", 'door'],
  ["door: a friend's shared plan is not cleaned", "      r.data.forEach(function (row) { row.sections = (Array.isArray(row.sections)", "      r.data.forEach(function (row) { row.sections = (Array.isArray(row.sections) && false", 'doorNow'],
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
  try { execFileSync('node', ['check-desktop-escaping.mjs', '--quiet', '--only', test], { env: { ...process.env, APP_DIR: tmp }, stdio: 'pipe', timeout: 400000 }); }
  catch (e) { failed = true; out = String(e.stdout || '') + String(e.stderr || ''); }
  if (failed && (!/check-desktop-escaping: \d+ passed, [1-9]\d* failed/.test(out) || /EADDRINUSE/.test(out))) { console.log('  BROKE   ', name, '— the run crashed; rerun it'); survived.push(name + ' (broke)'); continue; }
  if (failed) { caught++; console.log('  caught  ', name); } else { survived.push(name); console.log('  SURVIVED', name); }
}
console.log(`\nmutations: ${caught}/${ONLY ? ONLY.length : M.length} caught`);
if (survived.length) { console.log('survived:', survived.join(' | ')); process.exit(1); }
