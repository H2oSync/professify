/* apply-plans.mjs — Plans A–C, the registration game plan and backup sections (2026-09-25).
   Run AFTER apply-hawk.mjs and apply-sep24.mjs, on the newest production-line index.html:

     node apply-hawk.mjs <repo> && node apply-sep24.mjs <repo> && node apply-plans.mjs <repo>

   Same contract as the others: every anchor must be found exactly once or the script refuses and
   writes nothing; a change already applied is recognised by its marker and skipped. The module
   itself (plans/plans.js + plans/plans.css) is inlined between PLANS markers and REPLACED on every
   run, so editing those two files and re-running is how the module changes.

   Design: claude/spring-plans-game-plan-design-2026-09-25.md. SQL: sql/professify-plans.sql. */
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const here = path.dirname(fileURLToPath(import.meta.url));
const root = process.argv[2] || '.';
const file = path.join(root, 'index.html');
let s = fs.readFileSync(file, 'utf8');
const done = [];

function die(m) { console.error('apply-plans: ' + m + ' Nothing written.'); process.exit(1); }
function patch(name, marker, anchor, replacement) {
  if (s.includes(marker)) { done.push('already  ' + name); return; }
  const n = s.split(anchor).length - 1;
  if (n !== 1) die(`"${name}": expected the anchor once, found ${n}. Refusing to guess.`);
  s = s.replace(anchor, () => replacement);
  if (!s.includes(marker)) die(`"${name}": marker missing after the edit.`);
  done.push('applied  ' + name);
}

/* ---- 1. the tab names (Tate, 2026-09-25: My classes · Plans · Planner) --------------------- */
patch('tab: Plans',
  '>Plans<span id="stabWatchN">',
  '>My watchlist<span id="stabWatchN">',
  '>Plans<span id="stabWatchN">');
patch('tab: Planner',
  '>Planner<span id="stabPastN">',
  '>My planner<span id="stabPastN">',
  '>Planner<span id="stabPastN">');
patch('SCHED_LABEL',
  "var SCHED_LABEL={mine:'My classes',watch:'Plans',plan:'Planner',past:'Planner'};",
  "var SCHED_LABEL={mine:'My classes',watch:'My watchlist',plan:'My planner',past:'My planner'};",
  "var SCHED_LABEL={mine:'My classes',watch:'Plans',plan:'Planner',past:'Planner'};");

/* ---- 2. the Plans pane lives where the watchlist did ------------------------------------------ */
patch('plansOut',
  '<div id="plansOut"></div>',
  '<div id="schedWatchWrap" style="display:none">',
  '<div id="schedWatchWrap" style="display:none">\n      <!-- PLANS A–C (apply-plans, 2026-09-25): drawn by plans.js. The watchlist controls below stay\n           in the DOM for every caller that still reaches them, and plans.css hides them. -->\n      <div id="plansOut"></div>');

/* ---- 2b. Planner builds the plan (redesign, Tate 2026-09-25): the builder sits first in Planner;
   the degree record and ledger follow it, behind "Show your degree progress". ------------------- */
patch('plBuilderOut',
  '<div id="plBuilderOut"></div>',
  '<div id="schedPlanWrap">',
  '<div id="schedPlanWrap" class="pl3-deg-closed">\n    <!-- PLANNER BUILDS THE PLAN (apply-plans, 2026-09-25): drawn by plans.js. Everything below it is the\n         degree record and ledger, shown by "Show your degree progress and 4-year plan". -->\n    <div id="plBuilderOut"></div>');

/* ---- 2c. the feed never folds a friend's week (Tate, 2026-09-25, feed-is-plans-stories-are-now):
   another session made this change in a build that never reached the repo, so it rides here. ---- */
patch('feed: settling off',
  'var HM_SETTLE_VIEWS=Infinity;',
  'var HM_SETTLE_VIEWS=3;',
  "var HM_SETTLE_VIEWS=Infinity;   /* Tate, 2026-09-25: \"make sure not to compress the schedules\" — settling is off; 3 brings it back */");

/* ---- 3. class page: ＋ Plan instead of ☆ Watch, and "N in plans" ------------------------------ */
const cpWatch = `acts='<button class="cp-watch'+(watching?' on':'')+'" title="'+(watching?'On your Watchlist — tap to remove':'Add this section to your Watchlist to compare it')+'" onclick="wcWatchSec(\\''+escAcc(code)+'\\',\\''+escAcc(crn)+'\\',event)">'+(watching?'✓ Watching':'☆ Watch')+'</button>'`;
patch('class page: plan button',
  "acts=(window.TCPlans?TCPlans.planBtnHtml(code,crn,'cp-watch'):",
  cpWatch,
  `acts=(window.TCPlans?TCPlans.planBtnHtml(code,crn,'cp-watch'):(${cpWatch.slice(5)}))`);
patch('class page: N in plans chip',
  "var pin=(window.TCPlans&&crn)?TCPlans.interestChip(crn):'';",
  "var frs=(typeof friendSecChip==='function')?friendSecChip(code,s):'';\n  var seatHtml;",
  "var frs=(typeof friendSecChip==='function')?friendSecChip(code,s):'';\n  var pin=(window.TCPlans&&crn)?TCPlans.interestChip(crn):'';\n  var seatHtml;");
patch('class page: chips include it',
  "+((frs||conf||pin)?('<div class=\"cp-chips\">'+frs+pin+conf+'</div>'):'')",
  "+((frs||conf)?('<div class=\"cp-chips\">'+frs+conf+'</div>'):'')",
  "+((frs||conf||pin)?('<div class=\"cp-chips\">'+frs+pin+conf+'</div>'):'')");
patch('class page: ask for counts',
  'TCPlans.askInterest(secs.map(',
  '  var secs=clsSections(code);\n  var nSec=secs.length;',
  '  var secs=clsSections(code);\n  try{ if(window.TCPlans)TCPlans.askInterest(secs.map(function(x){return x.class_nbr;})); }catch(e){}\n  var nSec=secs.length;');

/* Explore's expanded section rows carried the same ☆ Watch. */
const csWatch = `'<button class="cs-watch'+(watching?' on':'')+'" title="'+(watching?'On your Watchlist — tap to remove':'Add this section to your Watchlist to compare it')+'" onclick="wcWatchSec(\\''+escAcc(code)+'\\',\\''+escAcc(crn)+'\\',event)">'+(watching?'✓ Watching':'☆ Watch')+'</button>'`;
patch('explore rows: plan button',
  "(window.TCPlans?TCPlans.planBtnHtml(code,crn,'cs-watch'):",
  csWatch,
  `(window.TCPlans?TCPlans.planBtnHtml(code,crn,'cs-watch'):${csWatch})`);

/* ---- 4. the planner's "Add all" names where they go now -------------------------------------- */
patch('planner: save all',
  '>Save all these classes</button>',
  '>Add all to My watchlist</button>',
  '>Save all these classes</button>');
patch('planner: save all toast',
  "' to Explore › Saved'",
  "frToast(n?('Added '+n+' class'+(n===1?'':'es')+' to My watchlist'+(skipped?(' · '+skipped+' already there'):'')):'Everything here is already on your watchlist');",
  "frToast(n?('Saved '+n+' class'+(n===1?'':'es')+' to Explore › Saved'+(skipped?(' · '+skipped+' already there'):'')):'Everything here is already saved');");

/* ---- 5. the Round 1 banner opens the game plan (Tate: "Hawk + Oct 19 banner") ---------------- */
patch('banner: game plan',
  'TCPlans.fromBanner()',
  `Build your schedule now and see which of your friends are already locking in classes.</span><button class="btn primary" style="flex:none" onclick="show('sched')">Build schedule</button>`,
  `Your game plan says what to register for first, with a backup for each class.</span><button class="btn primary" style="flex:none" onclick="if(window.TCPlans)TCPlans.fromBanner();else show('sched')">Your game plan</button>`);

/* ---- 6. a friend's profile gets a Plans tab ---------------------------------------------------- */
patch('friend profile: classes tab yields',
  "profileTab!=='friends'&&profileTab!=='plans'",
  "profileTab==='classes'||(profileTab!=='took'&&profileTab!=='friends')?'on':''",
  "profileTab==='classes'||(profileTab!=='took'&&profileTab!=='friends'&&profileTab!=='plans')?'on':''");
patch('friend profile: plans tab',
  "(window.TCPlans?TCPlans.friendTabHtml(f):'')",
  '      ${fofTab}\n    </div>',
  "      ${fofTab}\n      ${(window.TCPlans?TCPlans.friendTabHtml(f):'')}\n    </div>");
patch('friend profile: plans body',
  "profileTab==='plans'&&window.TCPlans?TCPlans.friendBodyHtml(f)",
  "<div class=\"frp-body\">${profileTab==='friends'?fofBlock:(profileTab==='took'?tookBlock:classesBlock)}</div>",
  "<div class=\"frp-body\">${profileTab==='plans'&&window.TCPlans?TCPlans.friendBodyHtml(f):(profileTab==='friends'?fofBlock:(profileTab==='took'?tookBlock:classesBlock))}</div>");

/* ---- 7. the privacy policy says who sees a plan, and what is counted (review, 2026-09-25) ----- */
patch('privacy: plans line',
  '<li><b>Your plans (Plan A, B and C):</b>',
  "+'<li><b>Your past classes and watchlist:</b> only you, except where a friend shares a class with you.</li>'",
  "+'<li><b>Your past classes and saved classes:</b> only you, except where a friend shares a class with you.</li>'\n"
  + "    +'<li><b>Your plans (Plan A, B and C):</b> your accepted friends at your school, one plan at a time — each plan has a <b>Friends can see</b> switch, on until you turn it off. Nobody else sees a plan. Every section in a plan is also on your watchlist, for seat alerts.</li>'\n"
  + "    +'<li><b>How many students plan a section:</b> a section that is in anyone’s plan or watchlist is counted, and other students at your school see that count (“9 in plans”) only once at least three other students have it. The count never says who, never includes the person looking, and is worked out by the database, which sends only the number.</li>'");
patch('privacy: plans are deleted with the account',
  'sections, past classes, plans, watchlist,',
  'sections, past classes, watchlist,',
  'sections, past classes, plans, watchlist,');
patch('privacy: date',
  "var LEGAL_UPDATED_PRIVACY='25 September 2026';",
  "var LEGAL_UPDATED_PRIVACY='24 September 2026';",
  "var LEGAL_UPDATED_PRIVACY='25 September 2026';");

/* ---- 8. the module, inlined (replaced on every run) ------------------------------------------- */
const js = fs.readFileSync(path.join(here, 'plans', 'plans.js'), 'utf8');
const css = fs.readFileSync(path.join(here, 'plans', 'plans.css'), 'utf8');
if (/<\/script/i.test(js) || /<\/style/i.test(css)) die('plans.js/css contains a closing tag.');
const block = '<!-- PLANS:BEGIN (apply-plans.mjs — edit plans/plans.js and plans/plans.css, not this) -->\n'
  + '<style id="plans-css">\n' + css + '</style>\n<script id="plans-js">\n' + js + '</script>\n<!-- PLANS:END -->';
const re = /<!-- PLANS:BEGIN[\s\S]*?<!-- PLANS:END -->/;
if (re.test(s)) { s = s.replace(re, () => block); done.push('replaced module'); }
else {
  const n = s.split('</body>').length - 1;
  if (n !== 1) die(`expected one </body>, found ${n}.`);
  s = s.replace('</body>', () => block + '\n</body>');
  done.push('inserted module');
}

fs.writeFileSync(file, s);
done.forEach((d) => console.log('  ' + d));
