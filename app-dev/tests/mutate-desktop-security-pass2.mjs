/* Mutation check for check-desktop-security-pass2: each mutant puts ONE bug of security-pass2 (2026-10-15) back into a copy of
   index.html (the fix reverted, or a safety rule weakened); check-desktop-security-pass2 must FAIL, in the section named, on every one.
   Run: SRC_DIR=<repo> node mutate-desktop-security-pass2.mjs  (MUT_ONLY="name|name")   — SRC_DIR's index.html must already carry the patch.
   A mutant is [name, [[fixed text, bug text], ...], section]; every fixed text must occur exactly once. */
import fs from 'node:fs'; import path from 'node:path'; import { execFileSync } from 'node:child_process';
const SRC = process.env.SRC_DIR || path.resolve('../..');
const HERE = path.dirname(new URL(import.meta.url).pathname);
const SLUG = [".replace(/[^A-Za-z0-9_]/g,'');}", ";}"];   /* slugPR keeps only plain characters of a PolyRatings id */
const M = [
  /* ---- 1. the Home strip */
  ['reviews: Home reads the table again', [["sb.from('reviews_public').select('professor_key,professor_name,department,course,score,difficulty,would_again,tags,note,created_at')", "sb.from('reviews').select('professor_key,professor_name,department,course,score,difficulty,would_again,tags,note,created_at')"]], 'reviews'],
  /* ---- 2. sign-out */
  ['signout: the wipe is never called', [["  try{ tcWipeLocal({memory:true}); }catch(e){}\n  updateAuthUI();", "  updateAuthUI();"]], 'signout'],
  ['signout: tc- and tc_ keys are left', [["/^(professify|tc-|tc_)/.test(k)&&!tcKeepKey(k,o)", "/^(professify)/.test(k)&&!tcKeepKey(k,o)"]], 'signout'],
  ['signout: sessionStorage is left', [["['localStorage','sessionStorage'].forEach(function(n){", "['localStorage'].forEach(function(n){"]], 'signout'],
  ['signout: the in-memory lists stay', [["  if(o.memory)tcResetMemory();", ""]], 'signout'],
  ['signout: the theme is wiped', [["var TC_KEEP={'professify-theme':1,", "var TC_KEEP={"]], 'signout'],
  ['signout: the analytics pseudonym is wiped', [["'professify_ev_salt':1,", ""]], 'signout'],
  ['signout: the public PolyRatings cache is wiped', [["'professify_prof_cache':1,", ""]], 'signout'],
  ['signout: the seat cache is wiped', [["  if(k.indexOf('professify_seats_cache')===0)return true;\n", ""]], 'signout'],
  ['signout: the last user id is wiped', [["'professify_course_short':1,'professify_last_uid':1};", "'professify_course_short':1};"]], 'signout'],
  /* ---- 2. push */
  ['push: sign-out never turns push off', [["      await Promise.race([pushDisable(),new Promise(function(r){ setTimeout(r,2000); })]);", "      0;"]], 'push'],
  ['push: sign-out waits for the push service forever', [["await Promise.race([pushDisable(),new Promise(function(r){ setTimeout(r,2000); })]);", "await pushDisable();"]], 'push'],
  ['push: it turns push off when it was never granted', [["&&Notification.permission==='granted'&&typeof pushDisable==='function')", "&&typeof pushDisable==='function')"]], 'push'],
  ['push: a push error stops the sign-out', [["  try{\n    if(typeof pushSupported==='function'&&pushSupported()&&Notification.permission==='granted'", "  {\n    if(typeof pushSupported==='function'&&pushSupported()&&Notification.permission==='granted'"], ["new Promise(function(r){ setTimeout(r,2000); })]);\n  }catch(e){}\n  try{ if(sb&&sb.auth)", "new Promise(function(r){ setTimeout(r,2000); })]);\n  }\n  try{ if(sb&&sb.auth)"]], 'push'],
  /* ---- 2. a different account */
  ['newuser: a different account does not wipe', [["  if(last&&last!==uid){ tcWipeLocal({keepPending:true,memory:!!memory}); wiped=true; }", ""]], 'newuser'],
  ['newuser: the page-load check is gone', [["(function(){ try{ var u=tcStoredUid(); if(u)tcSeeUser(u,false); }catch(e){} })();", ""]], 'newuser'],
  ['newuser: the sign-in-in-the-page check is gone', [["      try{ if(session&&session.user&&typeof tcSeeUser==='function')tcSeeUser(session.user.id,true); }catch(_w){}\n", ""]], 'newuser'],
  ['newuser: the page keeps A\'s lists in memory', [["tcSeeUser(session.user.id,true)", "tcSeeUser(session.user.id,false)"]], 'newuser'],
  ['newuser: the new account is never remembered', [["  try{ localStorage.setItem('professify_last_uid',uid); }catch(e){}\n  return wiped;", "  return wiped;"]], 'newuser'],
  ['newuser: first-ever sign-in wipes a guest\'s data', [["if(last&&last!==uid){", "if(last!==uid){"]], 'newuser'],
  ['newuser: the new account\'s invite is wiped too', [["  if(o&&o.keepPending&&(k==='professify_pending_add'||k==='professify_pending_add_at'||k==='professify_pending_handle'||k==='professify_pending_phone'))return true;\n", ""]], 'newuser'],
  /* ---- 3. deletion */
  ['delete: tc- and tc_ keys survive deleting the account', [["if(/^(professify|sb-|tc-|tc_)/.test(k))localStorage.removeItem(k);", "if(/^(professify|sb-)/.test(k))localStorage.removeItem(k);"]], 'delete'],
  ['delete: the recovery sheet\'s Sign out keeps everything', [["  try{ tcWipeLocal({}); }catch(e){}   /* security-pass2 (2026-10-15): signing out here is signing out */", ""]], 'delete'],
  /* ---- 4. avatars */
  ['avatars: avaHtml draws any URL', [["  url=tcAva(url);   /* only our own avatars bucket; anything else is the silhouette (security-pass2, 2026-10-15) */\n", ""]], 'avatars'],
  ['avatars: avaHtml drops no-referrer', [["src=\"'+escapeHtml(url)+'\" alt=\"\" loading=\"lazy\" referrerpolicy=\"no-referrer\"'", "src=\"'+escapeHtml(url)+'\" alt=\"\" loading=\"lazy\"'"]], 'avatars'],
  ['avatars: any https URL is accepted', [["if(u.indexOf(TC_AVA_BASE)===0)return", "if(u.indexOf('https://')===0)return"]], 'avatars'],
  ['avatars: a look-alike host passes', [["if(u.indexOf(TC_AVA_BASE)===0)return", "if(u.indexOf('https://rqkndeqbcahozidniesn.supabase.co')===0)return"]], 'avatars'],
  ['avatars: any bucket on our host passes', [["if(u.indexOf(TC_AVA_BASE)===0)return", "if(u.indexOf('https://rqkndeqbcahozidniesn.supabase.co/storage/v1/object/public/')===0)return"]], 'avatars'],
  ['avatars: ".." is allowed', [["/[\\s\"'<>\\\\]|\\.\\./.test(u.slice(TC_AVA_BASE.length))", "/[\\s\"'<>\\\\]/.test(u.slice(TC_AVA_BASE.length))"]], 'avatars'],
  ['avatars: a URL with a quote passes', [["/[\\s\"'<>\\\\]|\\.\\./.test(u.slice(TC_AVA_BASE.length))", "/[\\s<>\\\\]|\\.\\./.test(u.slice(TC_AVA_BASE.length))"]], 'avatars'],
  ['avatars: my own photo is fetched from anywhere', [["    var url=tcAva((typeof myProfile!=='undefined'&&myProfile&&myProfile.avatar_url)?String(myProfile.avatar_url):'');   /* never fetch", "    var url=((typeof myProfile!=='undefined'&&myProfile&&myProfile.avatar_url)?String(myProfile.avatar_url):'');   /* never fetch"]], 'avatars'],
  ['avatars: the first-paint pill draws a cached foreign URL', [["      av=(typeof tcAva==='function')?tcAva(av):'';", ""]], 'avatars'],
  ['avatars: the header pill draws my foreign URL', [["var _av=tcAva((typeof myAvatarUrl==='function')?myAvatarUrl():'');", "var _av=((typeof myAvatarUrl==='function')?myAvatarUrl():'');"], ["    if(url)return tcAva(url);   /*", "    if(url)return url;   /*"]], 'avatars'],
  ['avatars: messages draw any URL', [["  p=Object.assign({},p,{avatar:tcAva(p.avatar)});   /* only our own avatars bucket (security-pass2, 2026-10-15) */\n", ""]], 'avatars'],
  ['avatars: the professor page friend faces draw any URL', [["    av=tcAva(av);   /* only our own avatars bucket (security-pass2, 2026-10-15) */\n", ""]], 'avatars'],
  ['avatars: my rail photo draws any URL', [["  var url=tcAva(myAvatarUrl());", "  var url=(myAvatarUrl());"], ["    if(url)return tcAva(url);   /*", "    if(url)return url;   /*"]], 'avatars'],
  ['avatars: Home face row draws any URL', [["var inner=tcAva(p.img)\n      ? '<img src=\"'+esc2(tcAva(p.img))+'\"", "var inner=p.img\n      ? '<img src=\"'+esc2(p.img)+'\""]], 'sites'],
  ['avatars: registration-day face draws any URL', [["var _au = tcAva(f.avatar_url);", "var _au = f.avatar_url;"]], 'sites'],
  ['avatars: plans faces draw any URL', [["(tcAva(f.avatar_url) ? '<img src=\"' + esc(tcAva(f.avatar_url)) + '\"", "(f.avatar_url ? '<img src=\"' + esc(f.avatar_url) + '\""]], 'sites'],
  ['avatars: the plan picker face draws any URL', [["  url=tcAva(url);   /* only our own avatars bucket (security-pass2, 2026-10-15) */\n  if(url)return '<span class=\"pl-face\">", "  if(url)return '<span class=\"pl-face\">"]], 'sites'],
  ['avatars: the editor probes any URL', [["var url=tcAva((myProfile&&myProfile.avatar_url)?String(myProfile.avatar_url):'');", "var url=((myProfile&&myProfile.avatar_url)?String(myProfile.avatar_url):'');"]], 'sites'],
  ['avatars: Settings draws my foreign URL', [["var avu=tcAva((typeof myAvatarUrl==='function')?myAvatarUrl():'');", "var avu=((typeof myAvatarUrl==='function')?myAvatarUrl():'');"]], 'sites'],
  ['avatars: Settings drops no-referrer', [["alt=\"\" referrerpolicy=\"no-referrer\">':escAcc(initials(nm||'?'))", "alt=\"\">':escAcc(initials(nm||'?'))"]], 'sites'],
  /* ---- 5. escaping */
  ['escape: escapeHtml leaves the quote', [["function escapeHtml(s){return String(s).replace(/[&<>\"']/g", "function escapeHtml(s){return String(s).replace(/[&<>\"]/g"]], 'escape'],
  ['escape: escAcc leaves the quote', [["function escAcc(s){return String(s==null?'':s).replace(/[&<>\"']/g", "function escAcc(s){return String(s==null?'':s).replace(/[&<>\"]/g"]], 'escape'],
  ['escape: the code step HTML-escapes then backslashes', [["  var esc=jsAttr(email);", "  var esc=escapeHtml(email).replace(/'/g,\"\\\\'\");"]], 'escape'],
  ['poly: the rating form prints a course raw', [["<option ${d.course===c?'selected':''}>${escapeHtml(c)}</option>", "<option ${d.course===c?'selected':''}>${c}</option>"]], 'poly'],
  ['poly: a department keeps its markup', [["const dep=prText(p.department,40),", "const dep=(p.department),"]], 'poly'],
  ['poly: a name keeps its markup', [["nm=prText((prText(p.firstName)+' '+prText(p.lastName)).trim(),80)||'Instructor';", "nm=((p.firstName||'')+' '+(p.lastName||'')).trim()||'Instructor';"]], 'poly'],
  ['poly: a course keeps its markup', [[".map(c=>prText(c,40)).filter(Boolean)", ""]], 'poly'],
  ['poly: the id keeps its quotes', [SLUG], 'poly'],
  ['poly: the id keeps its quotes (and the handlers print it raw)', [SLUG, ["onclick=\"openProf('${jsAttr(id)}')\">${watchBtn(id)}", "onclick=\"openProf('${id}')\">${watchBtn(id)}"]], 'poly'],
  ['poly: the Explore card prints the id raw', [["data-surface=\"explore\" onclick=\"openProf('${jsAttr(id)}')\">${watchBtn(id)}", "data-surface=\"explore\" onclick=\"openProf('${id}')\">${watchBtn(id)}"]], 'poly'],
  ['poly: the watch button prints the id raw', [["onclick=\"toggleWatch('${jsAttr(id)}',event)\">${on?WL_ON:WL_OFF}", "onclick=\"toggleWatch('${id}',event)\">${on?WL_ON:WL_OFF}"]], 'poly'],
  ['poly: the watch card prints the id raw', [["onclick=\"openWatchedProf('${jsAttr(id)}')\">", "onclick=\"openWatchedProf('${id}')\">"]], 'poly'],
  ['poly: the compare cards print the id raw', [["onclick=\"openProf(\\''+jsAttr(s.id)+'\\')\">View profile →", "onclick=\"openProf(\\''+s.id+'\\')\">View profile →"]], 'poly'],
  ['poly: the compare tray prints the id raw', [["onclick=\"wpToggleCompare('${jsAttr(id)}',event)\">✕", "onclick=\"wpToggleCompare('${id}',event)\">✕"]], 'poly'],
  ['poly: the section row prints the id raw', [["<div class=\"pm sec\" onclick=\"openProf('${jsAttr(profId)}')\">", "<div class=\"pm sec\" onclick=\"openProf('${profId}')\">"]], 'poly'],
  ['poly: the plan button prints the id raw', [["onclick=\"togglePlanCourse('${jsAttr(code)}','${jsAttr(profId)}','${jsAttr(term)}')\"", "onclick=\"togglePlanCourse('${jsAttr(code)}','${profId}','${term}')\""]], 'poly'],
  ['poly: the flex-slot option prints the id raw', [["<div class=\"pm sec\" onclick=\"openProf('${jsAttr(o.prof)}')\">", "<div class=\"pm sec\" onclick=\"openProf('${o.prof}')\">"]], 'poly'],
  ['poly: the mini professor row prints the id raw', [["<div class=\"pm\" onclick=\"openProf('${jsAttr(r.profId)}')\">", "<div class=\"pm\" onclick=\"openProf('${r.profId}')\">"]], 'poly'],
  ['poly: the review-list row prints the id raw', [["onclick=\"rlOpenProf('${jsAttr(id)}','${jsAttr(code||'')}')\"", "onclick=\"rlOpenProf('${id}','${jsAttr(code||'')}')\""]], 'poly'],
  ['poly: My reviews prints the id raw', [["onclick=\"closeMyReviews();openProf(\\''+jsAttr(id)+'\\')\"", "onclick=\"closeMyReviews();openProf(\\''+id+'\\')\""]], 'poly'],
  ['poly: the rating form prints the id raw', [["onclick=\"submitRate('${jsAttr(id)}')\">", "onclick=\"submitRate('${id}')\">"]], 'poly'],
  ['poly: the Explore department line prints raw', [["<div class=\"pd\">${escapeHtml(profDeptLabel(p))}${p.reviews!=null", "<div class=\"pd\">${profDeptLabel(p)}${p.reviews!=null"], ["const dep=prText(p.department,40),", "const dep=(p.department),"]], 'poly'],
  /* ---- 6. the cookie */
  ['cookie: not Secure', [["max-age=604800; Secure; SameSite=Strict';", "max-age=604800; SameSite=Strict';"]], 'cookie'],
  ['cookie: SameSite=Lax', [["max-age=604800; Secure; SameSite=Strict';", "max-age=604800; Secure; SameSite=Lax';"]], 'cookie'],
  ['cookie: a year again', [["max-age=604800; Secure; SameSite=Strict';", "max-age=31536000; Secure; SameSite=Strict';"]], 'cookie'],
  ['cookie: no path', [["'; path=/; max-age=604800; Secure; SameSite=Strict';", "'; max-age=604800; Secure; SameSite=Strict';"]], 'cookie'],
  ['cookie: removal drops the attributes', [["document.cookie=k+'=; path=/; max-age=0; Secure; SameSite=Strict';", "document.cookie=k+'=; path=/; max-age=0';"]], 'cookie'],
  /* ---- 8. analytics */
  ['evname: a click is named by its text again', [["      return (n.tagName || '').toLowerCase().slice(0,60);", "      var kind = (n.tagName || '').toLowerCase();\n      var label = (n.getAttribute('aria-label') || n.value || n.textContent || '').replace(/\\s+/g,' ').trim();\n      return (kind + (label ? ':' + label.slice(0,40) : '')).slice(0,60);"]], 'evname'],
  ['evname: the aria-label is used', [["      return (n.tagName || '').toLowerCase().slice(0,60);", "      return ((n.tagName || '').toLowerCase() + ':' + (n.getAttribute('aria-label') || '')).slice(0,60);"]], 'evname'],
  ['evname: the typed value is used', [["      return (n.tagName || '').toLowerCase().slice(0,60);", "      return ((n.tagName || '').toLowerCase() + ':' + (n.value || '')).slice(0,60);"]], 'evname'],
];
const html = fs.readFileSync(path.join(SRC, 'index.html'), 'utf8');
const tmp = fs.mkdtempSync('/tmp/claude-0/mutt-');
for (const e of fs.readdirSync(SRC)) if (e !== 'index.html' && e !== '.git') fs.symlinkSync(path.join(SRC, e), path.join(tmp, e));
let caught = 0, ran = 0; const survived = [];
const ONLY = process.env.MUT_ONLY ? process.env.MUT_ONLY.split('|') : null;
for (const [name, reps, test] of M) {
  if (ONLY && !ONLY.includes(name)) continue;
  ran++;
  let h = html, bad = false;
  for (const [a, b] of reps) {
    const n = h.split(a).length - 1;
    if (n !== 1) { console.log('  BAD MUTANT (found ' + n + '×):', name, '—', a.slice(0, 70)); bad = true; break; }
    h = h.split(a).join(b);
  }
  if (bad) { survived.push(name + ' (bad)'); continue; }
  fs.writeFileSync(path.join(tmp, 'index.html'), h);
  let failed = false, out = '';
  try { execFileSync('node', [path.join(HERE, 'check-desktop-security-pass2.mjs'), '--quiet', '--only', test], { env: { ...process.env, APP_DIR: tmp }, stdio: 'pipe', timeout: 400000 }); }
  catch (e) { failed = true; out = String(e.stdout || '') + String(e.stderr || ''); }
  if (failed && (!/check-desktop-security-pass2: \d+ passed, [1-9]\d* failed/.test(out) || /EADDRINUSE/.test(out))) { console.log('  BROKE   ', name, '— the run crashed; rerun it'); survived.push(name + ' (broke)'); continue; }
  if (failed) { caught++; console.log('  caught  ', name); } else { survived.push(name); console.log('  SURVIVED', name); }
}
console.log(`\nmutations: ${caught}/${ran} caught`);
if (survived.length) { console.log('survived:', survived.join(' | ')); process.exit(1); }
