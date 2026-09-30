#!/usr/bin/env node
/* Focused day in the phone week grid (2026-09-30).
   Tate, on the mockup (today-in-week-grid-mockup-2026-09-30): build "the one that is the same as A,
   but it's any day": nothing is expanded until a day is tapped; the tapped day widens and shows the
   full course code, the exact time and the friends in that class; the red now line only appears when
   the tapped day IS today; days with no classes drop out while a day is focused; no room, no class
   number; and the course subject ("BUS" in "BUS 3438") must never be cut off.
   Also: the time axis is cropped to the hours the student's sections use (the mockup's 8a–4p),
   instead of a fixed 6a–10p, which is what left 50-minute classes 20px tall and cut "BUS" off.
   Replayable: every anchor must match EXACTLY once or the script exits non-zero and writes nothing.
   Run:  node apply-focusday.mjs <repo-dir>   (edits app/index.html and sw.js in place, in a copy)  */
import fs from 'node:fs';
import path from 'node:path';

const [,, DIR, STAMP = '2026-09-30 01:00'] = process.argv;
if (!DIR) { console.error('usage: apply-focusday.mjs <repo-dir> [build-stamp]'); process.exit(2); }
const APP = path.join(DIR, 'app', 'index.html'), SW = path.join(DIR, 'sw.js');
let app = fs.readFileSync(APP, 'utf8'), sw = fs.readFileSync(SW, 'utf8');
const edits = [];
function sub(label, find, repl) {
  const n = app.split(find).length - 1;
  if (n !== 1) { console.error(`FAIL  ${label}: anchor matched ${n} times, expected 1`); process.exit(1); }
  app = app.replace(find, () => repl); edits.push(label);
}

/* ---- A. the grid ---------------------------------------------------------------------- */
sub('A grid(): focused day, cropped axis, now line, full codes',
`function grid(secs, o) {
  const H = o.H || 320, S0 = 360, S1 = 1320, k = H / (S1 - S0);
  const head = \`<div class="g-head"><span></span>\${DAYS.map(d => \`<button class="g-day \${d === o.sel ? 'on' : ''}" data-a="\${o.act}" data-x="\${d}">\${DAYN[d].toUpperCase()}</button>\`).join('')}</div>\`;
  const labels = [[360, '6a'], [600, '10a'], [840, '2p'], [1080, '6p'], [1320, '10p']].map(([m, l]) => \`<span style="top:\${(m - S0) * k}px">\${l}</span>\`).join('');
  const cols = DAYS.map(d => {
    const blocks = secs.filter(s => !s.async && s.s != null && s.days.includes(d)).map(s => {
      const top = Math.max(0, (s.s - S0) * k), h = Math.max((s.e - s.s) * k, o.one ? 30 : 20);
      const two = h >= 28;
      const cls = ['g-b', d === o.sel ? 'sel' : '', o.shared && o.shared.has(s.code) ? 'shared' : '', two ? '' : 'one'].join(' ');
      const [subj, num] = s.code.split(' ');
      return \`<button class="\${cls}" style="top:\${top}px;height:\${h}px" data-a="\${o.blockAct || 'openClass'}" data-x="\${s.code}" data-y="\${esc(s.id)}" title="\${esc(s.code + ' · ' + course(s.code).title)}">\${two ? subj + '<br>' + num : num}</button>\`;
    }).join('');
    return \`<div class="g-col \${d === o.sel ? 'on' : ''}">\${blocks}</div>\`;
  }).join('');
  return \`<div class="grid">\${head}<div class="g-body" style="height:\${H}px"><div class="g-lab">\${labels}</div>\${cols}</div></div>\`;
}`,
`/* The week grid. Tap a day header to focus it: the column widens and its blocks show the full
   course code, the exact time and the friends in the class. Nothing is focused until tapped, and
   tapping the focused day again clears it. The red now line draws only when the focused day is today
   (SLO time). While a day is focused, days with no classes drop out of the grid. (2026-09-30) */
function gridSpan(secs) {
  /* The hours the axis covers: from the earliest start to the latest end among these sections,
     rounded out to the hour, and never less than six hours. A fixed 6a–10p left 50-minute classes
     20px tall, which is what cut "BUS" off "BUS 3438". */
  const t = secs.filter(s => !s.async && s.s != null && s.e != null);
  if (!t.length) return [480, 1080];
  let a = Math.floor(Math.min(...t.map(s => s.s)) / 60) * 60, b = Math.ceil(Math.max(...t.map(s => s.e)) / 60) * 60;
  if (b - a < 360) { b = Math.min(a + 360, 1440); a = b - 360; }
  return [a, b];
}
function gridTime(s) {
  /* "10:10–11:30a", "1:40–3:00p": minutes always, the a/p once. */
  const f = m => { let h = Math.floor(m / 60) % 12 || 12; return h + ':' + String(m % 60).padStart(2, '0'); };
  return f(s.s) + '–' + f(s.e) + (s.e >= 720 ? 'p' : 'a');
}
function gridFaces(s) {
  /* Square = same section, round = same class in another section: the rule the desktop uses. */
  const same = friendsInSec(s.id), other = friendsIn(s.code).filter(f => !same.includes(f));
  const all = same.map(f => ['sq', f]).concat(other.map(f => ['ci', f]));
  if (!all.length) return '';
  const shown = all.slice(0, 3).map(([k, f]) => \`<span class="g-face \${k}">\${pav(f, 15, 6.5)}</span>\`).join('');
  return \`<span class="g-faces">\${shown}\${all.length > 3 ? \`<span class="g-more">+\${all.length - 3}</span>\` : ''}</span>\`;
}
function grid(secs, o) {
  const timed = s => !s.async && s.s != null && s.e != null;
  const [S0, S1] = gridSpan(secs);
  const has = d => secs.some(s => timed(s) && s.days.includes(d));
  const focus = o.sel && DAYS.includes(o.sel) ? o.sel : null;
  /* A focused day gets a taller body when its shortest class would otherwise be under 40px, so
     back-to-back classes on a long day never overlap. */
  const dur = focus ? secs.filter(s => timed(s) && s.days.includes(focus)).map(s => s.e - s.s) : [];
  const need = o.faces ? 52 : 40;   /* a wide block needs this much for code + time (+ faces) */
  const H = dur.length ? Math.min(900, Math.max(o.H || 320, Math.ceil(need * (S1 - S0) / Math.min(...dur)))) : (o.H || 320);
  const k = H / (S1 - S0);
  const days = focus ? DAYS.filter(d => d === focus || has(d)) : DAYS;
  const tmpl = focus ? \`grid-template-columns:30px \${days.map(d => d === focus ? 'minmax(0,1fr)' : '32px').join(' ')}\` : '';
  const today = CLOCK.day, nowMin = CLOCK.min;   /* read once, so the line and the live block agree */
  const head = \`<div class="g-head" style="\${tmpl}"><span></span>\${days.map(d => \`<button class="g-day \${d === focus ? 'on' : ''} \${d === today ? 'g-today' : ''}" data-a="\${o.act}" data-x="\${d}" aria-pressed="\${d === focus}">\${DAYN[d].toUpperCase()}</button>\`).join('')}</div>\`;
  const step = S1 - S0 > 480 ? 180 : 120;
  /* Hour labels every 2h (3h past an 8-hour span), always ending on the last hour of the axis. */
  const ms = []; for (let m = S0; m < S1; m += step) ms.push(m);
  if (S1 - ms[ms.length - 1] < step / 2) ms.pop(); ms.push(S1);
  const labels = ms.map(m => \`<span style="top:\${(m - S0) * k}px;transform:\${m === S0 ? 'none' : m === S1 ? 'translateY(-100%)' : 'translateY(-50%)'}">\${hs(m)}</span>\`);
  const cols = days.map(d => {
    const wide = d === focus;
    const blocks = secs.filter(s => timed(s) && s.days.includes(d)).map(s => {
      const faces = wide && o.faces ? gridFaces(s) : '';
      /* Minimum heights: two lines of code always fit (24), a wide block fits code + time (34), and
         code + time + a row of faces (52). */
      const top = Math.max(0, (s.s - S0) * k), h = Math.max((s.e - s.s) * k, wide ? (faces ? 52 : 34) : (o.one ? 30 : 24));
      const live = wide && d === today && s.s <= nowMin && nowMin < s.e;
      const [subj, num] = s.code.split(' ');
      const cls = ['g-b', wide ? 'wide' : '', live ? 'live' : '', o.shared && o.shared.has(s.code) ? 'shared' : ''].join(' ');
      let inner;
      if (wide) inner = \`<span class="g-code">\${esc(s.code)}</span><span class="g-time">\${gridTime(s)}</span>\${faces}\`;
      else inner = \`\${esc(subj)}<br>\${esc(num)}\`;   /* always both lines: the subject is never dropped */
      return \`<button class="\${cls}" style="top:\${top}px;height:\${h}px" data-a="\${o.blockAct || 'openClass'}" data-x="\${s.code}" data-y="\${esc(s.id)}" title="\${esc(s.code + ' · ' + course(s.code).title)}">\${inner}</button>\`;
    }).join('');
    const now = (wide && d === today && nowMin >= S0 && nowMin <= S1) ? \`<span class="g-now" style="top:\${(nowMin - S0) * k}px"><i>\${hs(nowMin)}</i></span>\` : '';
    return \`<div class="g-col \${wide ? 'on' : ''}">\${blocks}\${now}</div>\`;
  }).join('');
  return \`<div class="grid \${focus ? 'focused' : ''}">\${head}<div class="g-body" style="height:\${H}px;\${tmpl}"><div class="g-lab">\${labels.join('')}</div>\${cols}</div></div>\`;
}`);

/* ---- B. nothing focused until tapped ------------------------------------------------- */
sub('B default: no focused day',
`S.homeDay = S.schedDay = DAYS.indexOf(CLOCK.day) >= 0 ? CLOCK.day : 'M';`,
`S.homeDay = S.schedDay = null; /* nothing is focused until a day is tapped (2026-09-30) */`);

/* ---- C. tapping the focused day clears it ------------------------------------------- */
sub('C day taps toggle',
`  homeDay: d => { S.homeDay = d; render(true); }, schedDay: d => { S.schedDay = d; render(true); },`,
`  homeDay: d => { S.homeDay = S.homeDay === d ? null : d; render(true); }, schedDay: d => { S.schedDay = S.schedDay === d ? null : d; render(true); },`);

/* ---- D. faces on My classes only ------------------------------------------------------ */
sub('D My classes grid shows faces (timed)',
`grid(timed, { sel: S.schedDay, act: 'schedDay', blockAct: 'secSheet', H: 330 })`,
`grid(timed, { sel: S.schedDay, act: 'schedDay', blockAct: 'secSheet', H: 330, faces: true })`);
sub('D My classes grid shows faces (secs)',
`grid(secs, { sel: S.schedDay, act: 'schedDay', blockAct: 'secSheet', H: 330 })`,
`grid(secs, { sel: S.schedDay, act: 'schedDay', blockAct: 'secSheet', H: 330, faces: true })`);

/* ---- E. styles ----------------------------------------------------------------------- */
sub('E grid CSS',
`.g-b.one{font-size:9.5px;white-space:nowrap}`,
`/* focused day (2026-09-30). Every block is two lines, subject over number, so nothing is ever cut to "3438". */
.grid.focused .g-col:not(.on) .g-b{font-size:9px;letter-spacing:0;left:2px;right:2px}
.g-day.g-today:not(.on){color:var(--blue-ink)}
.g-day.g-today:not(.on)::after{content:"";position:absolute;left:50%;bottom:4px;width:5px;height:5px;border-radius:50%;background:var(--blue);transform:translateX(-50%)}
.grid.focused .g-day:not(.on){font-size:10.5px;letter-spacing:.02em}
.g-b.wide{display:flex;flex-direction:column;align-items:flex-start;justify-content:flex-start;gap:2px;text-align:left;padding:5px 7px;left:4px;right:4px}
.g-b.wide .g-code{font-size:11px;white-space:nowrap}
.g-b.wide .g-time{font-size:10px;font-weight:700;opacity:.9;white-space:nowrap}
.g-b.wide .g-row{display:flex;align-items:center;justify-content:space-between;width:100%;gap:4px}
.g-faces{display:inline-flex;align-items:center;gap:2px}
.g-face .av{box-shadow:0 0 0 1.5px rgba(255,255,255,.9)}
.g-face.sq .av{border-radius:4px}
.g-more{font-size:8.5px;font-weight:900;opacity:.9;margin-left:1px}
.g-b.live{background:var(--blue);color:#fff;box-shadow:0 4px 10px rgba(37,99,235,.3)}
.g-b.live .g-face .av{box-shadow:0 0 0 1.5px var(--blue)}
.g-b.live.shared{box-shadow:0 0 0 2.5px var(--yellow),0 4px 10px rgba(37,99,235,.3)}
.g-b.wide .g-faces{margin-top:1px}
@media (max-width:340px){.g-b.wide{padding:5px 4px}.g-b.wide .g-time{font-size:9px}.g-b.wide .g-code{font-size:10.5px}}
.g-now{position:absolute;left:0;right:0;height:2px;background:#DC2626;z-index:3;pointer-events:none}
.g-now::before{content:"";position:absolute;left:-1px;top:-4px;width:10px;height:10px;border-radius:50%;background:#DC2626}
.g-now i{position:absolute;right:2px;top:-16px;font-style:normal;font-size:9px;font-weight:900;color:#DC2626;background:#fff;border:1px solid #FCA5A5;border-radius:6px;padding:1px 5px;line-height:1.2}`);


/* ---- E2. plan colours for the live block ---------------------------------------------- */
sub('E2 plancol live',
`.plancol .g-day.on::after{background:var(--pc)}`,
`.plancol .g-day.on::after{background:var(--pc)}
.plancol .g-b.live{background:var(--pc);color:#fff;box-shadow:0 4px 10px var(--pc-glow)}
.plancol .g-b.live.shared{box-shadow:0 0 0 2.5px var(--yellow),0 4px 10px var(--pc-glow)}
.plancol .g-b.live .g-face .av{box-shadow:0 0 0 1.5px var(--pc)}`);

/* ---- F. build stamps ------------------------------------------------------------------ */
const oldStamp = (app.match(/window\.TERMCHAMP_APP_BUILD = '([^']+)'/) || [])[1];
if (!oldStamp) { console.error('FAIL  no TERMCHAMP_APP_BUILD'); process.exit(1); }
app = app.split(`'${oldStamp}'`).join(`'${STAMP}'`);
const swOld = (sw.match(/const BUILD = '([^']+)'/) || [])[1];
if (!swOld) { console.error('FAIL  no sw.js BUILD'); process.exit(1); }
sw = sw.replace(`const BUILD = '${swOld}'`, `const BUILD = '${STAMP}'`);
edits.push(`F build stamps ${oldStamp} → ${STAMP}`);

fs.writeFileSync(APP, app); fs.writeFileSync(SW, sw);
console.log('OK  ' + edits.length + ' edits applied:\n  - ' + edits.join('\n  - '));
