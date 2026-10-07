/* Mutation check for check-desktop-look: each mutant breaks one promise of the website's app look (2026-10-04);
   check-desktop-look must FAIL on every one. Run: SRC_DIR=<repo> node mutate-desktop.mjs  (MUT_ONLY="a|b") */
import fs from 'node:fs'; import path from 'node:path'; import { execFileSync } from 'node:child_process';
const SRC = process.env.SRC_DIR || path.resolve('../..');
const M = [
  ['majors: no Physics (BA) in the picker', "'Microbiology','Physics','Physics (BA)','Public Health','Statistics']", "'Microbiology','Physics','Public Health','Statistics']", 'majors'],
  ['majors: ITP plan dropped, a generated one takes over', "window.SCHED_MAJORS['ocob-itp']=", "window.__noITP=", 'majors'],
  ['majors: coming-soon compares names exactly', "return !live.has(nm(n));", "return !live.has(n);", 'majors'],
  ['majors: old EEM name not read as new', 'student.major=(p.major==="Recreation, Parks & Tourism Administration / Experience Industry Management")?"Experience & Event Management":p.major;', 'student.major=p.major;', 'majors'],
  ['look: dark is the default again', "  var t='light';\n", "  var t='dark';\n", 'themes'],
  ['look: a saved cream survives', "    if(s==='dark'){ t='dark'; }", "    if(s==='dark'||s==='cream'){ t=s; }", 'themes'],
  ['look: a dark OS opens dark', "    if(s==='dark'){ t='dark'; }", "    if(s==='dark'){ t='dark'; } else if(window.matchMedia&&matchMedia('(prefers-color-scheme: dark)').matches){ t='dark'; }", 'themes'],
  ['look: Cream back in Settings', "onclick=\"setTheme('dark')\">Dark</button>\n", "onclick=\"setTheme('dark')\">Dark</button>\n              <button type=\"button\" data-theme-val=\"cream\" onclick=\"setTheme('cream')\">Cream</button>\n", 'settingsTheme'],
  ['look: setTheme keeps cream', "  if(t!=='dark')t='light';   /* cream retired 2026-10-04 */\n", "", 'settingsTheme'],
  ['look: no Rate tab', '<button id="tab-rate" onclick="openRate()">', '<button id="tab-rate" onclick="openRate()" style="display:none">', 'topBar'],
  ['look: tabs pushed away from the bell', '.notif-wrap{margin-left:14px;', '.notif-wrap{margin-left:auto;', 'topBar'],
  ['look: no pill on the active tab', 'nav.tabs button.active .tpill{background:var(--blue-soft)}', '', 'topBar'],
  ['look: no wordmark', '<span class="brand-wm" aria-hidden="true">Term<b>Champ</b></span>', '', 'topBar'],
  ['look: Nunito not embedded', "@font-face{font-family:'Nunito';", "@font-face{font-family:'NunitoX';", 'type'],
  /* (was pass 1's title list; Home's titles are the layout pass's 900 since 2026-10-04, so the mutant moved to them) */
  ['look: titles stay light', '#view-home .hm-ct{font-size:18px;font-weight:900}', '#view-home .hm-ct{font-size:18px;font-weight:600}', 'type'],
  ['look: codes stay monospace', "  --mono:'Nunito',system-ui,", "  --mono:ui-monospace,system-ui,", 'type'],
  ['look: cards keep the hairline', '  border-color:transparent;box-shadow:var(--card-sh);border-radius:20px}', '  box-shadow:var(--card-sh);border-radius:20px}', 'cards'],
  ['look: blocks stay solid blue', '.cal-block,.hmc-blk{background:var(--blk);color:var(--blk-ink);box-shadow:none}', '', 'cards'],
  ['look: dark blocks keep light ink', '--blk:#25396A;--blk-ink:#DCE7FF;', '--blk:#25396A;--blk-ink:#1E40AF;', 'cards'],
  ["look: school paints its green again", "  r.removeProperty('--accent'); r.removeProperty('--accent-rgb'); r.removeProperty('--accent-ink');\n}\nfunction schoolComingHtml(", "  r.setProperty('--accent',sc.accent);\n}\nfunction schoolComingHtml(", "accent"],
  ['look: Rate button soft', '--clsblk:#2563EB;', '--clsblk:#D6E4FF;', 'accent'],
  ['look: codes stay solid chips', ':root[data-theme] .cx-badge,.cx-badge{', '.cx-badge-x{', 'accent'],
  ["look: three-step rating colours", "function scoreColor(v,kind){ if(v==null||!isFinite(Number(v)))return 'var(--faint)'; var st=", "function scoreColor(v,kind){ if(v==null||!isFinite(Number(v)))return 'var(--faint)'; return v>=3.3?'var(--good)':v>=2.5?'var(--mid)':'var(--low)'; var st=", "ratings"],
  ["look: tiles keep white initials", "return i>=0?APP_RATE_INK[i]:'#fff';", "return '#fff';", "ratings"],
  ['look: dark muted too dim', '--muted:#93A0B6;', '--muted:#66738A;', 'contrast'],
  ['look: light muted at the app\'s 4.4:1', '--muted:#5B6B80;', '--muted:#64748B;', 'contrast'],
  ['look: light ratings use the bright fill', '--rt-1:hsl(4 70% 18%)', '--rt-1:#E46258', 'contrast'],
  ['look: dark buttons white on light blue', '--accent-ink:#0B1120;', '--accent-ink:#FFFFFF;', 'contrast'],
  ['look: wordmark kept on a tablet', '@media (max-width:1000px){.brand-wm{display:none}', '@media (max-width:1000px){.brand-wm{display:inline}', 'narrow'],
  ['look: white pill on a soft block', '.cal-block .mode-pill{background:rgba(var(--fg-rgb),.08);color:var(--blk-ink);', '.cal-block .mode-pill{background:rgba(255,255,255,.2);color:#fff;', 'cards'],
  /* (was 'dark own initials white' on .hm-id .fav; Home's own circle is the app's grey one since the layout pass, so the mutant moved to it) */
  ['look: own initials white on the grey circle', 'background:var(--panel-3);color:var(--text-2)}\n#view-home .hm-id .idwho', 'background:var(--panel-3);color:#fff}\n#view-home .hm-id .idwho', 'rendered'],
  ["look: in My Classes on a blue tint", ".fp-snum,.ex-rec-btn{background:rgba(var(--good-rgb),.13);color:var(--good-ink)}", ".fp-snum,.ex-rec-btn{background:rgba(var(--accent-rgb),.13);color:var(--good-2)}", "rendered"],
  ['look: accent on its own tint', '.hm-newmark,.hm-id .mjs-t,.hmc-share-txt b,.fr-cchip,.st-tab.on{color:var(--tab-on)}', '', 'rendered'],
  ['look: faint back to 3:1', '--muted:#5B6B80;--faint:#5F6E83;', '--muted:#5B6B80;--faint:#8592A6;', 'contrast'],
  ['look: dots in near-black ink', "return 'var(--'+(kind==='fill'?'rtf-':'rt-')+st+')';", "return 'var(--rt-'+st+')';", 'ratings'],
  ['look: old ramp tiles', "  return APP_RATE_FILL[st-1];", "  return '#5E7A8A';", 'ratings'],
  ['look: setTheme leaves the green inline', "  try{localStorage.setItem('professify-theme',t);}catch(e){}\n  var r=document.documentElement.style;\n  r.removeProperty('--accent');", "  try{localStorage.setItem('professify-theme',t);}catch(e){}\n  var r=document.documentElement.style;\n  (0)&&r.removeProperty('--accent');", 'settingsTheme'],
  ['look: tokens only at the end of the page', '<style id="app-look-tokens">', '<style id="app-look-tokens" media="print">', 'themes'],
  // pass 2: the layouts (2026-10-04)
  ['layout: Home back to 250 / 555 / 300', '.wrap.hm-wrap{grid-template-columns:290px minmax(0,1fr) 310px;gap:24px}', '.wrap.hm-wrap{grid-template-columns:250px minmax(0,1fr) 300px;gap:24px}', 'layoutHome'],
  ['layout: the desktop feed keeps 7a–10p', '  if(opts.win&&opts.win.lo<opts.win.hi){ lo=opts.win.lo; hi=opts.win.hi; }', '  if(opts.win&&opts.win.lo<opts.win.hi&&window.innerWidth<=640){ lo=opts.win.lo; hi=opts.win.hi; }', 'layoutHome'],
  ['layout: blocks without their time', "+(_showT?('<span class=\"cb-time\">'", "+(false?('<span class=\"cb-time\">'", 'layoutHome'],
  ['layout: no mark on today', "(d===_td?' cal-today':'')", "''", 'layoutHome'],
  ['layout: the where-line has no dot', "'<span class=\"av-line av-'+esc(st.state)+'\">'", "'<span class=\"av-line\">'", 'layoutHome'],
  ['layout: dark chips in the bare fill', ';color:color-mix(in srgb,var(--rcf) 62%,#fff)!important}', '}', 'layoutHome'],
  ['layout: the star rows come back', '#view-home .hm-prow .pr-stars{display:none}', '', 'layoutHome'],
  ['layout: Rate button stays 46px', '#view-home .hm-ratebtn{min-height:54px;', '#view-home .hm-ratebtn{min-height:46px;', 'layoutHome'],
  ['layout: header narrower than the page', '  .wrap{max-width:1240px}   /* the header', '  .wrap.hm-wrap{max-width:1240px}   /* the header', 'layoutHome'],
  ['layout: 1140px titles push their links out', '@media (min-width:1140px) and (max-width:1299px){', '@media (min-width:9999px){', 'layoutHome'],
  ['layout: the class hero stays white', '#view-class .cp-hero{background:#2563EB;', '#view-class .cp-hero{background:var(--panel);', 'layoutClass'],
  ['layout: stat tiles in two rows', '#view-class .cp-stats{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));', '#view-class .cp-stats{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));', 'layoutClass'],
  ['layout: no right column on a class', "var side=''; try{ side=cpSideHtml(code,secs); }catch(_s){}", "var side='';", 'layoutClass'],
  ['layout: the column under the sections on a wide window', '.cp-grid.has-side{display:grid;', '.cp-grid.has-side{display:block;', 'layoutClass'],
  ['layout: its professors do not open', '\'button type="button" class="cps-row cps-prof" onclick="openProf(', '\'button type="button" class="cps-row cps-prof" onclick="void(', 'layoutClass'],
  ['layout: Schedule title centred', '#view-sched .phead.sched-tag{text-align:left;padding:22px 0 16px;margin:0;', '#view-sched .phead.sched-tag{text-align:center;padding:22px 0 16px;margin:0 auto;', 'layoutScreens'],
  ['layout: solid day columns hide the connectors', '.cal-day{background-color:rgba(var(--fg-rgb),.035);border-radius:14px}', '.cal-day{background-color:var(--panel-2);border-radius:14px}', 'layoutScreens'],
  ['layout: professor stars stay gold', '#view-prof .pp-score .pr-st .pr-f svg path{fill:var(--rcf)}', '', 'layoutScreens'],
  ['layout: professor hero not purple', '#view-prof .pp-head{background:#7C3AED;', '#view-prof .pp-head{background:var(--panel);', 'layoutScreens'],
  ['layout: Friends one big panel', '#view-friends .frv2{background:transparent;', '#view-friends .frv2{background:var(--panel);', 'layoutScreens'],
  ['layout: Settings edge bar back', '#view-settings .st-tab.on::before{display:none}', '', 'layoutScreens'],
  ['layout: Rate rows grey', '#rlLists > div:not(.rl-term):not(:first-child){background:#F3EEFF!important;', '#rlLists > div:not(.rl-term):not(:first-child){background:var(--panel-2)!important;', 'layoutScreens'],
  ['layout: hero tiles lighten the blue', '#view-class .cp-st,#view-class .cp-seat-st{background:rgba(15,23,42,.16);', '#view-class .cp-st,#view-class .cp-seat-st{background:rgba(255,255,255,.14);', 'rendered'],
];
const html = fs.readFileSync(path.join(SRC, 'index.html'), 'utf8');
const TOKEN_TWICE = a => { const h = html.indexOf('<style id="app-look-tokens">'), he = html.indexOf('</style>', h), e = html.indexOf('<style id="app-look">');
  const i = html.indexOf(a), j = html.indexOf(a, i + 1); return i > h && i < he && j > e; };
const tmp = fs.mkdtempSync('/tmp/claude-0/mutd-');
for (const e of fs.readdirSync(SRC)) if (e !== 'index.html' && e !== '.git') fs.symlinkSync(path.join(SRC, e), path.join(tmp, e));
let caught = 0; const survived = [];
const ONLY = process.env.MUT_ONLY ? process.env.MUT_ONLY.split('|') : null;
for (const [name, a, b, test] of M) {
  if (ONLY && !ONLY.includes(name)) continue;
  const n = html.split(a).length - 1;
  /* a token sits twice on purpose — in the head for the first paint and at the end to win the cascade */
  if (n !== 1 && !(n === 2 && TOKEN_TWICE(a))) { console.log('  BAD MUTANT (found ' + n + '×):', name); survived.push(name + ' (bad)'); continue; }
  fs.writeFileSync(path.join(tmp, 'index.html'), html.split(a).join(b));
  let failed = false, out = '';
  try { execFileSync('node', ['check-desktop-look.mjs', '--quiet', '--only', test], { env: { ...process.env, APP_DIR: tmp }, stdio: 'pipe', timeout: 400000 }); }
  catch (e) { failed = true; out = String(e.stdout || '') + String(e.stderr || ''); }
  if (failed && (!/check-desktop-look: \d+ passed, [1-9]\d* failed/.test(out) || /EADDRINUSE/.test(out))) { console.log('  BROKE   ', name, '— the run crashed; rerun it'); survived.push(name + ' (broke)'); continue; }
  if (failed) { caught++; console.log('  caught  ', name); } else { survived.push(name); console.log('  SURVIVED', name); }
}
console.log(`\nmutations: ${caught}/${ONLY ? ONLY.length : M.length} caught`);
if (survived.length) { console.log('survived:', survived.join(' | ')); process.exit(1); }
