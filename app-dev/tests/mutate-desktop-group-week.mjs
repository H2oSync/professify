/* Mutation check for check-desktop-group-week: each mutant breaks one promise of the group page's coloured week
   (website-group-week, 2026-10-14); check-desktop-group-week must FAIL on every one.
   Run: SRC_DIR=<repo> node mutate-desktop-group-week.mjs  (MUT_ONLY="a|b") */
import fs from 'node:fs'; import path from 'node:path'; import { execFileSync } from 'node:child_process';
const SRC = process.env.SRC_DIR || path.resolve('../..');
const M = [
  ["week: the choice is not kept", "try{ localStorage.setItem(gwKey(),v==='week'?'week':'free'); }catch(e){}", "", 'switch'],
  ["week: the choice is kept for everyone, not the person", "return 'professify_group_view_'+u; }", "return 'professify_group_view'; }", 'switch'],
  ["week: it opens on the Week by default", "return localStorage.getItem(gwKey())==='week'?'week':'free';", "return localStorage.getItem(gwKey())!=='free'?'week':'free';", 'switch'],
  ["week: a shared class is a block per person", "var k=(b.cm?('cm|'+m.id+'|'+(b.cmid||'')):b.code)+'|'+s+'|'+e;", "var k=m.id+'|'+b.code+'|'+s+'|'+e;", 'blocks'],
  ["week: a block is not split into both colours", "'background:'+gwFill(b.who.map(function(m){ return m._wc; }));", "'background:'+gwFill([b.who[0]._wc]);", 'blocks'],
  ["week: the list's colours are the other view's", "(wk?m._wc:m.color))+';border-color:'+(wk?m._wc:m.color)", "m.color)+';border-color:'+m.color", 'blocks'],
  ["week: blocks are drawn from the wrong hour", "top=(b.gs-S0)*GW_PX+1,", "top=(b.gs-GP_LO)*GW_PX+1,", 'blocks'],
  ["week: a block's time is wrong (minutes dropped)", "function gwHs(m){ var h=Math.floor(m/60)%24,mm=m%60; return ((h%12)||12)+(mm?':'+(mm<10?'0':'')+mm:'')+(h>=12?'p':'a'); }", "function gwHs(m){ var h=Math.floor(m/60)%24; return ((h%12)||12)+(h>=12?'p':'a'); }", 'blocks'],
  ["week: a muted person still draws", "c.members.forEach(function(m){ if(c.muted[m.id]||m.noData)return;\n    (m._blocks||[]).forEach(function(b){\n      if(b.di!==di)return;", "c.members.forEach(function(m){ if(m.noData)return;\n    (m._blocks||[]).forEach(function(b){\n      if(b.di!==di)return;", 'mute'],
  ["week: green bands with nobody to share with", "var shared=c.active.length>1,", "var shared=true,", 'solo'],
  ["week: a band is written as only the part the grid shows", "title=\"'+escAcc('Free '+gwRange(r.s,r.e))+'\">'", "title=\"'+escAcc('Free '+gwRange(s,e))+'\">'", 'free'],
  ["week: a green band's length is the clipped one", "gpDur(r.e-r.s)+'</span>'):ht>=16", "gpDur(e-s)+'</span>'):ht>=16", 'free'],
  ["week: green where somebody is only almost free", "c.runs.filter(function(r){ return r.di===di&&r.key==='all'; })", "c.runs.filter(function(r){ return r.di===di; })", 'free'],
  ["week: the band doesn't say how long", "(ht>=30?('<span>Free<br>'+gpDur(r.e-r.s)+'</span>')", "(ht>=30?('<span>Free</span>')", 'free'],
  ["week: the key counts everyone as free", "(nCounted===N?'All '+N+' free':'Free for the '+nCounted+' counted')", "('All '+N+' free')", 'free'],
  ["week: a friend's Spring class lands on the Fall week", "    var f=frNow((typeof findFriend==='function')?findFriend(m.id):null);", "    var f=(typeof findFriend==='function')?findFriend(m.id):null;", 'fall'],
  ["week: it forgets which term it is", "escAcc((typeof mcNowLabel==='function')?mcNowLabel():'This term')", "escAcc('This term')", 'fall'],
  ["week: your Work & activities lose their name", "label=busyF?'Busy':b.code;", "label='Busy';", 'commitments'],
  ["week: a shift isn't marked as one", "cmid: b.id }); });   /* website-group-week", "cmid: b.id, cm: '' }); });   /* website-group-week", 'commitments'],
  ["week: your Busy doesn't open its editor", "(mineCm?(' data-cm-act=\"edit\" data-id=\"'+escAcc(b.cmid)+'\"'):(' onclick=\"'+act+'\"'))", "(' onclick=\"'+act+'\"')", 'commitments'],
  ["week: a friend's Busy opens nothing", "var act = busyF ? 'openFriendProfile(\\''+jsAttr(b.who[0].id)+'\\')'", "var act = busyF ? ''", 'commitments'],
  ["week: a class block opens the wrong class", ": 'openClassPage(\\''+jsAttr(b.code)+'\\',event)';", ": 'openClassPage(\\'BUS 0000\\',event)';", 'commitments'],
  ["week: overlapping blocks stack on top of each other", "lanes[l]=b.ge; b.l=l; cl.push(b);", "lanes[l]=b.ge; b.l=0; cl.push(b);", 'commitments'],
  ["week: your colour fails 4.5:1 under white", "var GW_COL=['#2F5FC4',", "var GW_COL=['#7FA0EE',", 'contrast-light'],
  ["week: the free-band text is faint in light", ".gw-free span{font-family:var(--mono);font-size:10.5px;font-weight:700;line-height:1.2;color:var(--text);", ".gw-free span{font-family:var(--mono);font-size:10.5px;font-weight:700;line-height:1.2;color:var(--faint);", 'contrast-light'],
  ["week: the hour labels vanish into the dark", ".gw-t{position:absolute;right:5px;transform:translateY(-50%);font-family:var(--mono);font-size:9.5px;line-height:10px;color:var(--faint);", ".gw-t{position:absolute;right:5px;transform:translateY(-50%);font-family:var(--mono);font-size:9.5px;line-height:10px;color:#333;", 'contrast-dark'],
];
const html = fs.readFileSync(path.join(SRC, 'index.html'), 'utf8');
const tmp = fs.mkdtempSync('/tmp/claude-0/mutgw-');
for (const e of fs.readdirSync(SRC)) if (e !== 'index.html' && e !== '.git') fs.symlinkSync(path.join(SRC, e), path.join(tmp, e));
let caught = 0; const survived = [];
const ONLY = process.env.MUT_ONLY ? process.env.MUT_ONLY.split('|') : null;
for (const [name, a, b, test] of M) {
  if (ONLY && !ONLY.includes(name)) continue;
  const n = html.split(a).length - 1;
  if (n !== 1) { console.log('  BAD MUTANT (found ' + n + '×):', name); survived.push(name + ' (bad)'); continue; }
  fs.writeFileSync(path.join(tmp, 'index.html'), html.split(a).join(b));
  let failed = false, out = '';
  try { execFileSync('node', ['check-desktop-group-week.mjs', '--quiet', '--only', test], { env: { ...process.env, APP_DIR: tmp }, stdio: 'pipe', timeout: 400000 }); }
  catch (e) { failed = true; out = String(e.stdout || '') + String(e.stderr || ''); }
  if (failed && (!/check-desktop-group-week: \d+ passed, [1-9]\d* failed/.test(out) || /EADDRINUSE/.test(out))) { console.log('  BROKE   ', name, '— the run crashed; rerun it'); survived.push(name + ' (broke)'); continue; }
  if (failed) { caught++; console.log('  caught  ', name); } else { survived.push(name); console.log('  SURVIVED', name); }
}
console.log(`\nmutations: ${caught}/${ONLY ? ONLY.length : M.length} caught`);
if (survived.length) { console.log('survived:', survived.join(' | ')); process.exit(1); }
