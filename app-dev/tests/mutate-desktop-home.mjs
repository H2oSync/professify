/* Mutation check for check-desktop-home: each mutant breaks one promise of the website's Home at the phone's level
   (website-home-catchup, 2026-10-14); check-desktop-home must FAIL on every one.
   Run: SRC_DIR=<repo> node mutate-desktop-home.mjs  (MUT_ONLY="a|b"; APP_PORT to move off 8190) */
import fs from 'node:fs'; import path from 'node:path'; import { execFileSync } from 'node:child_process';
const SRC = process.env.SRC_DIR || path.resolve('../..');
const M = [
  ["home: Spring classes lose to the week now", "if((f.classes||[]).length)return Object.assign({},f,{_hm:'next'", "if(false)return Object.assign({},f,{_hm:'next'", "cards"],
  ["home: the LAST shared plan is shown, not the first", "return a.slot < b.slot ? -1 : a.slot > b.slot ? 1 : 0; }); }\n  function friendById", "return a.slot < b.slot ? 1 : a.slot > b.slot ? -1 : 0; }); }\n  function friendById", "cards"],
  ["home: Plan B is not orange", ".hm-plan-B{--pc:#C2410C;--pc-soft:#FFEDD5;--pc-soft2:#FED7AA;--pc-ink:#9A3412}", ".hm-plan-B{--pc:#0F766E;--pc-soft:#DDF5F1;--pc-soft2:#BDEBE2;--pc-ink:#115E59}", "cards"],
  ["home: a Fall-only friend has no card", "return Object.assign({},frNow(f),{_hm:'now'});", "return Object.assign({},f,{_hm:'now'});", "cards"],
  ["home: “Taking” for plans too", "(now?'Taking ':'Planning ')", "('Taking ')", "cards"],
  ["home: the Fall tag names Spring", "('Now · '+mcNowLabel())", "('Now · '+mcTermLabel())", "cards"],
  ["home: the plan tag has no plan name", "('Plan '+k+' · '+mcTermLabel())", "('Plan · '+mcTermLabel())", "cards"],
  ["home: a Spring card is counted against your Fall week", "  if(hmViewIsNow(f))return hmOverlap(f&&f.classes);\n  var n=0;", "  if(true)return hmOverlap(f&&f.classes);\n  var n=0;", "cards"],
  ["home: a plan only draws sections the feed never offered", "if(!inf||inf.missing||!inf.row)return;\n        seen[crn]=1;", "if(!inf)return;\n        seen[crn]=1;", "cards"],
  ["home: single-term count line changed", "return 'Taking '+n+' class'+(n===1?'':'es')+' this term'+ovh;", "return 'Taking '+n+' class'+(n===1?'':'es')+ovh;", "single"],
  ["home: the row shows on the single-term site", "if(!mcTwoTerms()||!window._myHistOk)return null;", "if(!window._myHistOk)return null;", "single"],
  ["lift: what you saw is never remembered", "HM_SEEN[key]={t:now,n:1,d:today,g:sig};", "", "lift"],
  ["lift: the changed friend is not first", "    if(!!a.lift!==!!b.lift)return a.lift?-1:1;\n", "", "lift"],
  ["lift: a plan says it is Spring classes", "ids[fr.id]=(v._hm==='next')?'next':'plan'", "ids[fr.id]='next'", "lift"],
  ["lift: it waits for nothing (a visit-old cache counts)", "||window._friendsFresh!==sbUser.id)return {};", ")return {};", "lift"],
  ["lift: a friend's first sight is news", "if(sig!=='now'&&prev&&typeof prev==='object'&&typeof prev.g==='string'&&prev.g!==sig)", "if(sig!=='now'&&(!prev||typeof prev!=='object'||prev.g!==sig))", "lift"],
  ["lift: spent by a feed nobody looked at", "    if(!hmFeedVisible())return {};            /* a render nobody looked at must not spend the lift */\n", "", "liftHidden"],
  ["recs: after the 2nd card", "out.splice(Math.min(3,out.length),0,_rc)", "out.splice(Math.min(2,out.length),0,_rc)", "recs"],
  ["recs: your own Spring classes are suggested", "if(!k||mine[k]||took[k])return;", "if(!k||took[k])return;", "recs"],
  ["recs: classes on your record are suggested", "if(!k||mine[k]||took[k])return;", "if(!k||mine[k])return;", "recs"],
  ["recs: no fallback to “taking”", "    if(!planning){\n      fr.forEach", "    if(false){\n      fr.forEach", "recs"],
  ["recs: shared plans are not counted", "if(window.TCPlans&&TCPlans.friendPlansOf)TCPlans.friendPlansOf(x.id).forEach(function(row){\n        (row.sections", "if(false)TCPlans.friendPlansOf(x.id).forEach(function(row){\n        (row.sections", "recs"],
  ["recs: most friends do not come first", ".sort(function(a,b){ return b.who.length-a.who.length||(a.code<b.code?-1:a.code>b.code?1:0); })", ".sort(function(a,b){ return (a.code<b.code?-1:a.code>b.code?1:0); })", "recs"],
  ["recs: the chip is the first friend's professor", "var lead=(ps.length&&(ps.length===1||ps[0][1]>ps[1][1])&&ps[0][1]*2>e.who.length)?ps[0][0]:null;", "var lead=ps.length?ps[ps.length-1][0]:null;", "recs"],
  ["recs: a card opens another class", "onclick=\"openClassFromFeed(\\''+escAcc(x.code)+'\\')\">'", "onclick=\"openClassFromFeed(\\'BUS 4401\\')\">'", "recs"],
  ["stories: in class, out LAST first", "return {rank:[3,t],state:'in'", "return {rank:[3,-t],state:'in'", "stories"],
  ["stories: not set up is first", "return {rank:[4,0],state:'none'", "return {rank:[-1,0],state:'none'", "stories"],
  ["stories: done for the day is last", "return {rank:[1,0],state:'now',label:' — done for the day'}", "return {rank:[5,0],state:'now',label:' — done for the day'}", "stories"],
  ["stories: no classes today is not first", "return {rank:[0,0],state:'now',label:' — no classes today'}", "return {rank:[1,0],state:'now',label:' — no classes today'}", "stories"],
  ["stories: in class has a green ring", "return {rank:[3,t],state:'in'", "return {rank:[3,t],state:'now'", "stories"],
  ["stories: other commitments are ignored", "var today=busy.concat(cm).filter", "var today=busy.filter", "stories"],
  ["stories: other commitments alone do not set a schedule up", "if(!busy.length&&!cm.length)return", "if(!busy.length)return", "stories"],
  ["stories: the unset ring is not grey", "#view-home .hm-fitem.hm-unset:not(.hm-fadd) .ring{border-color:#CBD5E1}", "#view-home .hm-fitem.hm-unset:not(.hm-fadd) .ring{border-color:var(--clsblk)}", "stories"],
  ["stories: ranking is not applied", "if(W)ranked.sort(hmStoryCmp);", "", "stories"],
];
const html = fs.readFileSync(path.join(SRC, 'index.html'), 'utf8');
const tmp = fs.mkdtempSync('/tmp/claude-0/mutr-');
for (const e of fs.readdirSync(SRC)) if (e !== 'index.html' && e !== '.git') fs.symlinkSync(path.join(SRC, e), path.join(tmp, e));
let caught = 0; const survived = [];
const ONLY = process.env.MUT_ONLY ? process.env.MUT_ONLY.split('|') : null;
const PART = process.env.MUT_PART ? process.env.MUT_PART.split('/').map(Number) : null;   /* "i/n": every n-th mutant from i, to run in parallel on different ports */
for (const [mi, [name, a, b, test]] of M.entries()) {
  if (ONLY && !ONLY.includes(name)) continue;
  if (PART && mi % PART[1] !== PART[0]) continue;
  const n = html.split(a).length - 1;
  if (n !== 1) { console.log('  BAD MUTANT (found ' + n + '×):', name); survived.push(name + ' (bad)'); continue; }
  fs.writeFileSync(path.join(tmp, 'index.html'), html.split(a).join(b));
  let failed = false, out = '';
  try { execFileSync('node', ['check-desktop-home.mjs', '--quiet', '--only', test], { env: { ...process.env, APP_DIR: tmp, SRC_DIR: SRC }, stdio: 'pipe', timeout: 400000 }); }
  catch (e) { failed = true; out = String(e.stdout || '') + String(e.stderr || ''); }
  if (failed && (!/check-desktop-home: \d+ passed, [1-9]\d* failed/.test(out) || /EADDRINUSE/.test(out))) { console.log('  BROKE   ', name, '— the run crashed; rerun it'); survived.push(name + ' (broke)'); continue; }
  if (failed) { caught++; console.log('  caught  ', name); } else { survived.push(name); console.log('  SURVIVED', name); }
}
console.log(`\nmutations: ${caught}/${caught + survived.length} caught`);
if (survived.length) { console.log('survived:', survived.join(' | ')); process.exit(1); }
