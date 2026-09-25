#!/usr/bin/env node
/* apply-mobile-pass1.mjs — the phone port, pass 1, as a replayable patch.
 *
 *   node apply-mobile-pass1.mjs <in/index.html> <out/index.html> [<sw.js in> <sw.js out>] --build "YYYY-MM-DD HH:MM"
 *
 * Every edit is anchored on text that must occur EXACTLY ONCE in the input. If any anchor is
 * missing or ambiguous the script writes nothing and exits 1 — a half-applied patch is how a
 * single-file app loses work between two sessions (master brief §8). Re-running it on its own
 * output is refused for the same reason: the markers below are how it knows.
 *
 * Written to apply to BOTH production (2026-09-19 13:25) and the Hawk line (2026-09-21 00:16 /
 * 00:56); the two differ only in five <head> lines this patch does not touch.
 */
import fs from 'node:fs'; import path from 'node:path'; import { fileURLToPath } from 'node:url';
const HERE = path.dirname(fileURLToPath(import.meta.url));
const args = process.argv.slice(2);
const bi = args.indexOf('--build'); const BUILD = bi >= 0 ? args[bi + 1] : null;
const pos = args.filter((a, i) => !(i === bi || i === bi + 1));
const [IN, OUT, SW_IN, SW_OUT] = pos;
if (!IN || !OUT || !BUILD || !/^\d{4}-\d{2}-\d{2} \d{2}:\d{2}$/.test(BUILD)) {
  console.error('usage: apply-mobile-pass1.mjs in.html out.html [sw.in sw.out] --build "YYYY-MM-DD HH:MM"'); process.exit(2);
}
let html = fs.readFileSync(IN, 'utf8');
if (html.includes('id="mobile-pass1"')) { console.error('refusing: input already carries mobile-pass1'); process.exit(1); }

const fail = [];
function once(label, find, replace) {
  const n = html.split(find).length - 1;
  if (n !== 1) { fail.push(`${label}: anchor found ${n}×`); return; }
  html = html.replace(find, () => replace);
}
function between(label, start, end, replacement) {
  const a = html.indexOf(start), a2 = html.lastIndexOf(start);
  const b = html.indexOf(end, a);
  if (a < 0 || a !== a2 || b < 0) { fail.push(`${label}: block anchors a=${a} dup=${a !== a2} b=${b}`); return; }
  html = html.slice(0, a) + replacement + html.slice(b + end.length);
}

/* 1. viewport-fit=cover — without it every env(safe-area-inset-*) is 0. */
once('viewport', '<meta name="viewport" content="width=device-width, initial-scale=1.0">',
  '<meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover">');

/* 2. The swipe engine, with Schedule's sub-tabs as stops. Replaces the IIFE whole. */
between('swipe', "(function(){\n  if(!('ontouchstart' in window))return;",
  "                     inScroller:inScroller,blocked:blocked};\n})();",
  fs.readFileSync(path.join(HERE, 'swipe.js'), 'utf8').trimEnd());

/* 3. Home: one fitted window for the whole feed (phone). */
once('hm-win-read', '  var lo=CAL_DAY_LO, hi=CAL_DAY_HI;\n',
  `  var lo=CAL_DAY_LO, hi=CAL_DAY_HI;
  /* ONE WINDOW FOR THE WHOLE FEED, FITTED TO THE FEED — 2026-09-24 (phone). The 7AM-10PM frame
     above exists so two friends' cards can be read against each other, and cropping each card to
     its own hours broke that. But on a phone the fixed frame spends most of every card on hours
     nobody in the feed has class: a feed of 9-to-5 weeks drew ~40% empty grid per card. The
     caller now passes the span of EVERY confirmed class in the feed, so all cards still share one
     scale — just the scale this feed actually uses. The loop below still widens it for anyone
     outside it, so nothing can be cut off. */
  /* Read at DRAW time, not at feed time: hmExpandSettled redraws one card without re-running the
     feed, and a phone turned to landscape can cross 640px in between (review, 2026-09-24). */
  if(opts.win&&opts.win.lo<opts.win.hi&&window.innerWidth<=640){ lo=opts.win.lo; hi=opts.win.hi; }
`);
once('hm-win-pass', 'hmMiniWeekHtml(confirmed,{excludeId:f.id,anytime:anyt,mark:mark})',
  'hmMiniWeekHtml(confirmed,{excludeId:f.id,anytime:anyt,mark:mark,win:window._hmFeedWin||null})');
once('hm-win-compute', '  var schedUsers={};\n',
  `  var schedUsers={};
  /* The shared window hmMiniWeekHtml reads — see ONE WINDOW FOR THE WHOLE FEED. Phone only; the
     desktop keeps the fixed 7AM-10PM frame. Half an hour of air each side so the first and last
     hour labels sit inside the frame. Null when nothing in the feed has a confirmed time. */
  window._hmFeedWin=null;
  try{
    if(window.innerWidth<=640){
      var _wlo=Infinity,_whi=-Infinity;
      (friendsList||[]).forEach(function(f){
        if(!f||!f.classes||!f.classes.length)return;
        var fm=hmFriendMeets(f);
        (fm&&fm.meets||[]).forEach(function(m){ if(!m||!m.meet||m.assumed)return;
          _wlo=Math.min(_wlo,m.meet.start); _whi=Math.max(_whi,m.meet.end); });
      });
      if(isFinite(_wlo)&&isFinite(_whi)&&_whi>_wlo)
        window._hmFeedWin={lo:Math.floor(Math.max(0,_wlo-30)/60)*60, hi:Math.ceil((_whi+30)/60)*60};
    }
  }catch(e){ window._hmFeedWin=null; }
`);

/* 3b. The switch's aria-pressed. The markup promises "a screen reader gets aria-pressed", and the
   attribute was written once in the HTML and never again — Professors stayed "not pressed" to a
   screen reader however many times it was chosen. Found while making the switch horizontal. */
once('aria-pressed', "  document.getElementById('ex-profs').classList.toggle('active',m==='professors');\n",
  `  document.getElementById('ex-profs').classList.toggle('active',m==='professors');
  document.getElementById('ex-classes').setAttribute('aria-pressed',String(m==='classes'||m==='ge'));
  document.getElementById('ex-profs').setAttribute('aria-pressed',String(m==='professors'));
`);

/* 4. The phone stylesheet, last in the document so it wins at equal specificity. */
once('css', '</body>', fs.readFileSync(path.join(HERE, 'mobile.css'), 'utf8') + '</body>');

/* 5. Build stamp. */
const stampRe = /window\.PROFESSIFY_BUILD='(\d{4}-\d{2}-\d{2} \d{2}:\d{2})';/;
const m = stampRe.exec(html);
if (!m) fail.push('build stamp not found');
else { if (m[1] >= BUILD) fail.push(`new stamp ${BUILD} is not after ${m[1]}`);
       html = html.replace(stampRe, `window.PROFESSIFY_BUILD='${BUILD}';`); }

if (fail.length) { console.error('NOT WRITTEN:\n  ' + fail.join('\n  ')); process.exit(1); }
fs.writeFileSync(OUT, html);
console.log(`wrote ${OUT}  (${m[1]} → ${BUILD})`);

if (SW_IN && SW_OUT) {
  let sw = fs.readFileSync(SW_IN, 'utf8');
  const swRe = /(BUILD\s*=\s*')(\d{4}-\d{2}-\d{2} \d{2}:\d{2})(')/;
  const sm = swRe.exec(sw);
  if (!sm) { console.error('sw.js BUILD not found — index.html written, sw.js NOT'); process.exit(1); }
  if (sm[2] !== m[1]) { console.error(`sw.js BUILD ${sm[2]} did not match index ${m[1]} — refusing`); process.exit(1); }
  fs.writeFileSync(SW_OUT, sw.replace(swRe, `$1${BUILD}$3`));
  console.log(`wrote ${SW_OUT}  (${sm[2]} → ${BUILD})`);
}
