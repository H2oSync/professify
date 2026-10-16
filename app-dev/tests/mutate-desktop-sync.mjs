/* Mutation check for check-desktop-sync: each mutant breaks one promise of website-sync (2026-10-15); check-desktop-sync must
   FAIL on every one (run with --only <test>, so a mutant is judged by the test that owns the promise).
   Run: SRC_DIR=<repo> node mutate-desktop-sync.mjs  (MUT_ONLY="a|b"; APP_PORT to move off 8190; MUT_DRY=1 only checks that each
   mutant's text is found exactly once) */
import fs from 'node:fs'; import path from 'node:path'; import { execFileSync } from 'node:child_process';
const SRC = process.env.SRC_DIR || path.resolve('../..');
const M = [
  // ---- Task 1: the registration card on Home's rail
  ["regcard: the card is not on the rail", "  try{ out+=hmRegCardHtml('rail'); }catch(e){}", "", 'regcard'],
  ["regcard: the card shows all term", "if(regIn==null||regIn<0||regIn>7)return null;", "if(regIn==null)return null;", 'regcard'],
  ["regcard: a dismissed card comes back", "    if(campusBannerDismissed(key))return null;\n", "", 'regcard'],
  ["regcard: x does not remember", "function dismissRegCard(key){\n  try{localStorage.setItem('professify_dismiss_'+key,'1');}catch(e){}\n", "function dismissRegCard(key){\n", 'regcard'],
  ["regcard: the buttons sit side by side", ".hm-regcard .hm-reg-acts{display:flex;flex-direction:column;", ".hm-regcard .hm-reg-acts{display:flex;flex-direction:row;", 'regcard'],
  ["regcard: the top banner is back", "  const qtrIn=daysUntil(c.QUARTER_END);\n  let html='';\n  if(qtrIn!=null&&qtrIn<=7&&qtrIn>=-7){", "  const qtrIn=daysUntil(c.QUARTER_END);\n  let html='';\n  if(c.REGISTRATION_OPENS&&daysUntil(c.REGISTRATION_OPENS)>=0&&daysUntil(c.REGISTRATION_OPENS)<=7){ html='<div class=\"campus-banner\"><span>Round 1 registration opens soon</span></div>'; }else if(qtrIn!=null&&qtrIn<=7&&qtrIn>=-7){", 'regcard'],
  // ---- one registration card, and the narrow-screen copy
  ["one card: the rail's day card is drawn beside it", "    if (where === 'rail' && typeof hmRegCardOn === 'function' && hmRegCardOn()) return '';", "", 'regcard-one'],
  ["one card: dismissing does not bring the day card back", "if(typeof regDayRepaint==='function')regDayRepaint(); else hmRegCardPaint();", "hmRegCardPaint();", 'regcard-one'],
  ["one card: no day line", "+(dayLine?'<div class=\"hm-reg-day\">'+escAcc(dayLine)+'</div>':'')", "+''", 'regcard-one'],
  ["one card: narrow screens lose the card", "  #hmRegTop{display:block;margin:0 0 14px}", "  #hmRegTop{display:none;margin:0 0 14px}", 'regcard-one'],
  /* (no mutant for `#hmRailR #hmRegCard{display:none}` below 1140px: #hmRailSlot is display:none there already, so it is a guard, not behaviour) */
  ["one card: the narrow-screen copy is never drawn", "  var h=''; try{ h=hmRegCardHtml('top'); }catch(e){}\n", "  var h='';\n", 'regcard-one'],
  ["one card: the compact card is drawn outside its 7 days", "if(regIn==null||regIn<0||regIn>7)return null;", "if(regIn==null||regIn<0||regIn>14)return null;", 'regcard-one'],
  // ---- Task 2: stories
  ["stories: only inside the 7am-11pm weekday window", "var W=hmStoryWindow();", "var W=hmFreeWindow();", 'stories-order'],
  ["stories: the pinned are last", "ranked=_pinned.concat(ranked);", "ranked=ranked.concat(_pinned);", 'pins'],
  ["stories: pin order is alphabetical, not the order pinned", "_pins.forEach(function(id){ for(var i=0;i<ranked.length;i++){", "_pins.slice().sort().forEach(function(id){ for(var i=0;i<ranked.length;i++){", 'pins'],
  ["pins: the limit is two", "var PIN_MAX=3;", "var PIN_MAX=2;", 'pins'],
  ["pins: written to the column, not the RPC", "var viaRpc=!!(window.TCSYNC&&TCSYNC.pinsRpc===true), kept=null;", "var viaRpc=false, kept=null;", 'pins'],
  ["pins: the server's answer is not adopted", "if(kept&&JSON.stringify(kept)!==JSON.stringify(next)){ myProfile.pinned_friends=kept; paint(); }", "", 'pins'],
  ["pins: a refused write is not undone", "    myProfile.pinned_friends=was;\n    paint();\n    try{ frToast((window.TCSYNC", "    paint();\n    try{ frToast((window.TCSYNC", 'pins'],
  ["pins: the toast is not the phone's", "'Pinned '+first(id)+' to the front'", "'Pinned '+first(id)", 'pins'],
  ["pins: a fourth is not refused", "  else if(cur.length>=max){", "  else if(false){", 'pins'],
  ["pins: a hold does not pin", "timer=setTimeout(function(){ timer=0; fire(id); },500);", "timer=setTimeout(function(){ timer=0; fire(id); },500000);", 'pins'],
  ["pins: right-click does not pin", "    if(Date.now()-held<1500)return;                    /* the hold already did it */\n    fire(t.getAttribute('data-fid'));", "    return;", 'pins'],
  ["pins: the click ending a hold opens the profile", "if(Date.now()-held<800&&tile(e.target)){", "if(false){", 'pins'],
  ["pins: an unfriended id counts", "return friendsList.some(function(f){ return f.id===id; }); });", "return true; });", 'pins'],
  ["pins: pins are read from the column", "var r=await sb.rpc('my_pinned_friends');", "var r=await sb.from('profiles').select('pinned_friends').eq('id',uid).maybeSingle(); r.data=r.data&&r.data.pinned_friends;", 'pins'],
  // ---- gap 1
  ["profile: the account's values are not applied", "    try{ if(typeof tcApplyAccountProfile==='function')tcApplyAccountProfile(data); }catch(_a){}", "", 'profile'],
  ["profile: a change of year is not written", "window.schSyncToStudent();}catch(e){} try{syncProfileToBackend();}catch(e){} }", "window.schSyncToStudent();}catch(e){} }", 'profile'],
  ["profile: General / Open is a concentration", "function tcConcClean(c){ return (c&&c!=='General / Open')?String(c):null; }", "function tcConcClean(c){ return c||null; }", 'profile'],
  ["profile: the old major name is written", "function tcMajorNow(m){ return (m&&TC_MAJOR_RENAMED[m])||m; }", "function tcMajorNow(m){ return m; }", 'profile'],
  ["profile: onboarding has no 5th year", "<option>Senior</option><option>5th year +</option></select>", "<option>Senior</option></select>", 'profile'],
  ["profile: the account overrides an unsent change", "    if(pend){ try{ syncProfileToBackend(); }catch(e){} return; }", "", 'profile'],
  ["profile: an unsent change is not remembered", "  try{ localStorage.setItem(pk,'1'); }catch(e){}\n", "", 'profile'],
  // ---- gap 3
  ["sections: the server's list does not replace the local one", "      if(_ad){\n        Object.keys(myClassMeta||{})", "      if(false){\n        Object.keys(myClassMeta||{})", 'sections'],
  ["sections: a queued add is dropped", "return !x||!x.crn||_srv[String(x.crn)]||_pend.indexOf(String(x.crn))>=0;", "return !x||!x.crn||_srv[String(x.crn)];", 'sections'],
  ["sections: the backfill pushes everything", "(_adopt||_q.indexOf(String(rec.crn))>=0)", "true", 'sections'],
  ["sections: the adoption pass never ends", "  secAdoptSet('my');                               /* the adoption pass is done once the server has been read */\n", "", 'sections'],
  ["sections: a removed watch is put back", "    if(!_adW){\n", "    if(true){\n", 'sections'],
  // ---- gap 4
  ["visibility: never refreshes", "    if(!was||Date.now()-was<=120000)return;", "    return;", 'visibility'],
  ["visibility: refreshes after any absence", "    if(!was||Date.now()-was<=120000)return;", "    if(!was)return;", 'visibility'],
  // ---- gap 5
  ["chat: a message you hid is shown", "  if(msgX.hidden[String(m.id)])return false;                                    /* deleted for me */\n", "", 'chat'],
  ["chat: a blocked sender is shown", "  try{ if(typeof isBlocked==='function'&&isBlocked(m.sender))return false; }catch(e){}", "", 'chat'],
  ["chat: a deleted chat's old messages are shown", "  return !c||new Date(m.created_at)>new Date(c);", "  return true;", 'chat'],
  ["chat: likes are not shown", "    +((msgX.likes[String(m.id)]||[]).length?('<span class=\"msg-lk\"", "    +(false?('<span class=\"msg-lk\"", 'chat'],
  ["chat: a muted chat does not say so", "      +(msgX.mutes[String(t.id)]?'<span class=\"msg-tmute\"", "      +(false?'<span class=\"msg-tmute\"", 'chat'],
  ["chat: the list preview ignores hides", "if(!lastOf[m.conversation_id]&&msgVisible(m))lastOf", "if(!lastOf[m.conversation_id])lastOf", 'chat'],
  // ---- gap 6
  ["push: seat alerts are not mirrored to seat_open", "if('seats' in patch){ if(patch.seats)delete prefs.seat_open; else prefs.seat_open=false; }", "", 'push'],
  ["push: the phone's other switches are wiped", "Object.assign({},g.data.prefs):{};", "{}:{};", 'push'],
  ["push: the phone's seat switch is not read", "d.prefs.seat_open===false)d=", "d.prefs.seat_open===123)d=", 'push'],
  ["push: quiet hours are not mirrored", "      if('quiet_from' in patch)prefs.quiet_from=patch.quiet_from;\n", "", 'push'],
  ["push: no fallback when prefs is missing", "if(r.error&&row.prefs){ delete row.prefs;", "if(false){ delete row.prefs;", 'push'],
  // ---- gap 7
  ["saved: nothing is uploaded", "var w=await sb.from('saved_items').upsert(rows,{onConflict:'user_id,kind,key',ignoreDuplicates:true});", "var w={};", 'saved'],
  ["saved: a removal here is never sent", "if(!lc[k]){ if(base&&bc[k])delC.push(k); else if(fetchServer)addLC.push(k); }", "if(!lc[k]){ if(fetchServer)addLC.push(k); }", 'saved'],
  ["saved: a removal elsewhere comes back", "if(base&&bp[k]&&fetchServer)remLP.push(k); else insP.push(k);", "insP.push(k);", 'saved'],
  ["saved: the professor key is not the review key", "var k=profKey(p); if(k&&!o[k])o[k]=id;", "var k=String(p.name||''); if(k&&!o[k])o[k]=id;", 'saved'],
  ["saved: a missing table is not remembered", "if(r.error){ if(tcMissing(r.error))TCSYNC.savedOk=false; return; }", "if(r.error){ return; }", 'saved'],
  ["saved: the account's class is not added here", "else if(fetchServer)addLC.push(k); } });\n    Object.keys(lp)", "} });\n    Object.keys(lp)", 'saved'],
  // ---- gap 8
  ["favorites: nothing is written", "var r=await sb.rpc('set_favorite_teacher',{p_key:k,p_on:want});", "var r={};", 'favorites'],
  ["favorites: the box shows when the RPC is missing", "    if(TCSYNC.favsOk!==true)return '';", "", 'favorites'],
  ["favorites: editing a review forgets it", "  try{ if(typeof tcFavAfter==='function')tcFavAfter(p); }catch(_f){}      /* website-sync (2026-10-15) */\n", "", 'favorites'],
  ["favorites: a fourth is allowed", "full=!on&&tcFavCount()>=3;", "full=false;", 'favorites'],
  ["gameplan: the device-only appointment is still the field", "    if (rdi) h +=", "    if (false) h +=", 'gameplan'],
  // ---- gap 9
  ["review edit: `term` is sent again", "  var patch={course:v.course||null,course_key:v.courseKey||null,score:v.score,", "  var patch={course:v.course||null,course_key:v.courseKey||null,term:v.term||'',score:v.score,", 'review-edit'],
  // ---- gap 10
  ["normCode: a suffix letter is lost", "(\\d{3,4}[A-Z]?)$/);", "(\\d{3,4})$/);", 'normcode'],
  ["normCode: an ampersand is lost", "replace(/[^A-Z0-9&]/g,'').match(/^([A-Z&]{2,5})", "replace(/[^A-Z0-9]/g,'').match(/^([A-Z&]{2,5})", 'normcode'],
  ["saved_classes: codes are read raw", "const n=normCode(r.code); if(n!==r.code)", "const n=r.code; if(n!==r.code)", 'normcode'],
  ["saved_classes: the legacy spelling is not deleted", ".in('code',[code].concat((window._mcRawCode&&window._mcRawCode[code])?[window._mcRawCode[code]]:[]))", ".in('code',[code])", 'normcode'],
];
const html = fs.readFileSync(path.join(SRC, 'index.html'), 'utf8');
const tmp = fs.mkdtempSync('/tmp/claude-0/muts-');
for (const e of fs.readdirSync(SRC)) if (e !== 'index.html' && e !== '.git') fs.symlinkSync(path.join(SRC, e), path.join(tmp, e));
let caught = 0; const survived = [];
const ONLY = process.env.MUT_ONLY ? process.env.MUT_ONLY.split('|') : null;
for (const [name, a, b, test] of M) {
  if (ONLY && !ONLY.includes(name)) continue;
  const n = html.split(a).length - 1;
  if (n !== 1) { console.log('  BAD MUTANT (found ' + n + '×):', name); survived.push(name + ' (bad)'); continue; }
  if (process.env.MUT_DRY) { caught++; continue; }
  fs.writeFileSync(path.join(tmp, 'index.html'), html.split(a).join(b));
  let failed = false, out = '';
  try { execFileSync('node', ['check-desktop-sync.mjs', '--quiet', '--only', test], { env: { ...process.env, APP_DIR: tmp }, stdio: 'pipe', timeout: 400000 }); }
  catch (e) { failed = true; out = String(e.stdout || '') + String(e.stderr || ''); }
  if (failed && (!/check-desktop-sync: \d+ passed, [1-9]\d* failed/.test(out) || /EADDRINUSE/.test(out))) { console.log('  BROKE   ', name, '— the run crashed; rerun it'); survived.push(name + ' (broke)'); continue; }
  if (failed) { caught++; console.log('  caught  ', name); } else { survived.push(name); console.log('  SURVIVED', name); }
}
console.log(`\nmutations: ${caught}/${ONLY ? ONLY.length : M.length} caught`);
if (survived.length) { console.log('survived:', survived.join(' | ')); process.exit(1); }
