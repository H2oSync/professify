/* Mutation check for check-desktop-parity2 (website-friends-plans-tabs, 2026-10-14): each mutant breaks one promise;
   check-desktop-parity2 must FAIL on the test named with it.   Run: SRC_DIR=<repo> node mutate-desktop-parity2.mjs  (MUT_ONLY="a|b") */
import fs from 'node:fs'; import path from 'node:path'; import { execFileSync } from 'node:child_process';
const SRC = process.env.SRC_DIR || path.resolve('../..');
const M = [
  ["friends: Invite is the blue accent again", "#view-friends .frv2-invite{background:var(--frp);", "#view-friends .frv2-invite{background:var(--accent);", 'friends'],
  ["friends: Accept is blue again", "#view-friends .frv2-cact .frv2-go{background:var(--frp);color:#fff}", "", 'friends'],
  ["friends: dark pink text is the light one (3:1)", ':root[data-theme="dark"] #view-friends{--frp-t:#F472B6;', ':root[data-theme="dark"] #view-friends{--frp-t:#CC1F6C;', 'friends'],
  ["friends: the search icon is grey again", "#view-friends .frv2-findico{color:var(--frp-t)}", "", 'friends'],
  ["friends: the request card has no pink ring", "#view-friends .frv2-card.fr-pending{box-shadow:0 0 0 2px var(--frp-ring)}", "", 'friends'],
  ["friends: the unread dot is blue again", "#view-friends .msg-tdot{background:var(--frp)}", "", 'friends'],
  ["friends: New group is not pink", '#view-friends .fr-secl[onclick^="msgNewConv"]{color:var(--frp-t);font-weight:900}', "", 'friends'],
  ["plans: the pills carry no plan class", `class="pl3-pill tcpl-' + s + (on ? ' on' : '')`, `class="pl3-pill' + (on ? ' on' : '')`, 'plans'],
  ["plans: Plan B is blue", ".tcpl-B{--pc:#C2410C;--pc-t:#C2410C;", ".tcpl-B{--pc:#2563EB;--pc-t:#2563EB;", 'plans'],
  ["plans: the Plans tab carries no plan colour", `'<div class="pl3 tcpl-' + slot + '">'`, `'<div class="pl3">'`, 'plans'],
  ["plans: a chosen pill's text is grey", '#view-sched .pl3-pill.on[class*="tcpl-"] b,#view-sched .pl3-pill.on[class*="tcpl-"] span{color:#fff}', '#view-sched .pl3-pill.on[class*="tcpl-"] b,#view-sched .pl3-pill.on[class*="tcpl-"] span{color:var(--muted)}', 'plans'],
  ["builder: the Filling pills carry no plan class", `class="bd-slot tcpl-' + sl + (sl === cur ? ' on' : '')`, `class="bd-slot' + (sl === cur ? ' on' : '')`, 'builder-pills'],
  ["builder: the chosen Filling pill is not filled", '.bd-slot.on[class*="tcpl-"]{background:var(--pc);border-color:var(--pc);color:#fff}', "", 'builder-pills'],
  ["tabs: the rail still says Planner", `onclick="setSchedTab('plan')">Builder</button>`, `onclick="setSchedTab('plan')">Planner</button>`, 'tabs'],
  ["tabs: Past classes opens the Builder, not the record", `onclick="setSchedTab('past')">Past classes<span`, `onclick="setSchedTab('plan')">Past classes<span`, 'tabs'],
  ["tabs: the title says Planning again", "lbl=window.plPlanningLabel();", "lbl='planning '+window.plPlanningLabel();", 'tabs'],
  ["tabs: Builder stays lit under Past classes", "(t===x[0]&&!(x[0]==='plan'&&_toRecord))", "t===x[0]", 'tabs'],
  ["tabs: the record flag never clears", "window.schedRecord=_toRecord;", "window.schedRecord=window.schedRecord||_toRecord;", 'tabs'],
  ["tabs: Back from a class returns to the Builder, not Past classes", "if(t==='plan'&&window.schedRecord===true)t='past';   /* Back returns to Past classes */\n      return {kind:'sched',tab:t,label:({mine:'My Classes',watch:'Watchlist',past:'Past Classes',\n              planner:'Builder'", "\n      return {kind:'sched',tab:t,label:({mine:'My Classes',watch:'Watchlist',past:'Past Classes',\n              planner:'Builder'", 'tabs'],
  ["tabs: the empty-state copy says Planner", "<span>Builder shows the classes you need", "<span>Planner shows the classes you need", 'tabs'],
];
const html = fs.readFileSync(path.join(SRC, 'index.html'), 'utf8');
const tmp = fs.mkdtempSync('/tmp/claude-0/mutp2-');
for (const e of fs.readdirSync(SRC)) if (e !== 'index.html' && e !== '.git') fs.symlinkSync(path.join(SRC, e), path.join(tmp, e));
let caught = 0; const survived = [];
const ONLY = process.env.MUT_ONLY ? process.env.MUT_ONLY.split('|') : null;
for (const [name, a, b, test] of M) {
  if (ONLY && !ONLY.includes(name)) continue;
  const n = html.split(a).length - 1;
  if (n !== 1) { console.log('  BAD MUTANT (found ' + n + 'x):', name); survived.push(name + ' (bad)'); continue; }
  fs.writeFileSync(path.join(tmp, 'index.html'), html.split(a).join(b));
  let failed = false, out = '';
  try { execFileSync('node', ['check-desktop-parity2.mjs', '--quiet', '--only', test], { env: { ...process.env, APP_DIR: tmp }, stdio: 'pipe', timeout: 400000 }); }
  catch (e) { failed = true; out = String(e.stdout || '') + String(e.stderr || ''); }
  if (failed && (!/check-desktop-parity2: \d+ passed, [1-9]\d* failed/.test(out) || /EADDRINUSE/.test(out))) { console.log('  BROKE   ', name, '- the run crashed; rerun it'); survived.push(name + ' (broke)'); continue; }
  if (failed) { caught++; console.log('  caught  ', name); } else { survived.push(name); console.log('  SURVIVED', name); }
}
console.log(`\nmutations: ${caught}/${ONLY ? ONLY.length : M.length} caught`);
if (survived.length) { console.log('survived:', survived.join(' | ')); process.exit(1); }
