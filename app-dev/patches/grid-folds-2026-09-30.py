#!/usr/bin/env python3
r"""Home week cards: fold long empty stretches, and give back-to-back classes room.
(Tate, 2026-09-30, on Tjudd's card — 8a–8p with PSY 3323 at 8:00–8:50 and 9:00–10:50, squeezed to
25px an hour by the 300px cap: "it looks a little cramped for the first two classes maybe we need to
make when someone has classes this close back to back or something we can fix or solve this")

In fitted grids (o.fit, the Home cards):
- Every stretch of 2+ whole hours with no class on ANY day folds into an 18px "No classes 2p–6p"
  band, so the hours that have classes get the room.
- When a class starts within 70 minutes of the one before it on the same day, those two get at least
  36px from start to start (still never taller than o.H). Clashing sections under 30 minutes apart don't count.
- A block's minimum height never pushes it under a fold band: it sits up against the band instead.
In every grid: a block's minimum height never runs into the next class on its day (1px kept).

Usage: python3 grid-folds-2026-09-30.py <repo-dir>   (edits <repo-dir>/app/index.html)
Applied in order; every anchor must match exactly once at its turn, or nothing is written.
"""
import sys, os
p = os.path.join(sys.argv[1], 'app', 'index.html')
s = open(p, encoding='utf-8').read()
if 'class="g-fold"' in s: sys.exit('already patched')
R = [
 ("  const base = o.fit ? Math.min(o.H || 300, Math.round((S1 - S0) / 60 * o.fit)) : (o.H || 320);\n"
  "  const H = base;   /* focusing a day never changes the height (Tate, 2026-09-30) */\n"
  "  const k = H / (S1 - S0);",
  "  /* Fitted cards (Home) fold every stretch of 2+ whole hours with no class on any day into a thin\n"
  "     \"No classes\" band, and give back-to-back classes room: when the next class on a day starts within\n"
  "     70 minutes, the two get at least 36px from start to start. (Tate, 2026-09-30: Tjudd's 8a–8p card\n"
  "     with 8:00 and 9:00 classes was squeezed to 25px an hour.) */\n"
  "  const FOLD = 18, folds = [];\n"
  "  if (o.fit) { const iv = secs.filter(timed).map(s => [s.s, s.e]).sort((x, y) => x[0] - y[0]); let end = iv.length ? iv[0][1] : S0;\n"
  "    for (let i = 1; i < iv.length; i++) { const a = Math.ceil(end / 60) * 60, b = Math.floor(iv[i][0] / 60) * 60; if (b - a >= 120) folds.push([a, b]); end = Math.max(end, iv[i][1]); } }\n"
  "  const vis = S1 - S0 - folds.reduce((t, [a, b]) => t + b - a, 0);\n"
  "  let pxm = o.fit ? o.fit / 60 : 0;\n"
  "  if (o.fit) DAYS.forEach(d => { const ds = secs.filter(s => timed(s) && s.days.includes(d)).sort((x, y) => x.s - y.s); for (let i = 1; i < ds.length; i++) { const dt = ds[i].s - ds[i - 1].s; if (dt >= 30 && dt <= 70) pxm = Math.max(pxm, 36 / dt); } });\n"
  "  const base = o.fit ? Math.min(o.H || 300, Math.round(vis * pxm + folds.length * FOLD)) : (o.H || 320);\n"
  "  const H = base;   /* focusing a day never changes the height (Tate, 2026-09-30) */\n"
  "  const k = (H - folds.length * FOLD) / vis;\n"
  "  /* minute -> px down the body; each fold is FOLD px tall (nothing is ever drawn inside one) */\n"
  "  const Y = m => { let y = (m - S0) * k; for (const [a, b] of folds) if (m >= b) y += FOLD - (b - a) * k; return y; };"),
 ("  const span = S1 - S0, STEPS = [60, 120, 180, 240];", "  const span = vis, STEPS = [60, 120, 180, 240];"),
 ("  const ms = []; for (let m = S0; m <= S1; m += step) ms.push(m);\n",
  "  const ms = []; for (let m = S0; m <= S1; m += step) ms.push(m);\n"
  "  /* with folds: label each stretch on the same step, and always label both edges of a fold */\n"
  "  if (folds.length) { ms.length = 0; let a0 = S0; folds.concat([[S1, S1]]).forEach(([a, b]) => { for (let m = a0; m <= a; m += step) ms.push(m); if (a < S1 && ms[ms.length - 1] !== a) ms.push(a); a0 = b; }); }\n"),
 ("<span style=\"top:${(m - S0) * k}px;transform:${m === S0 ? 'none' : m === S1 ? 'translateY(-100%)' : 'translateY(-50%)'}\">${hs(m)}</span>",
  "<span style=\"top:${Y(m)}px;transform:${m === S0 || folds.some(f => f[1] === m) ? 'none' : m === S1 || folds.some(f => f[0] === m) ? 'translateY(-100%)' : 'translateY(-50%)'}\">${hs(m)}</span>"),
 ("    const blocks = secs.filter(s => timed(s) && s.days.includes(d)).map(s => {",
  "    const dayS = secs.filter(s => timed(s) && s.days.includes(d)), blocks = dayS.map(s => {"),
 ("      const h = Math.max((s.e - s.s) * k, o.fit ? 26 : (o.one ? 30 : 24));",
  "      /* ...but a minimum never runs into the next class that day (1px kept between them) */\n"
  "      const nx = dayS.reduce((n, x) => x !== s && x.s > s.s && x.s < n ? x.s : n, Infinity);\n"
  "      const h = Math.max((s.e - s.s) * k, Math.min(o.fit ? 26 : (o.one ? 30 : 24), nx < Infinity ? Y(nx) - Y(s.s) - 1 : 99));"),
 ("      const top = Math.max(0, Math.min((s.s - S0) * k, H - h));",
  "      /* a block stops at the bottom of the card, or at the top of the next fold band below it */\n"
  "      const fb = folds.find(([a]) => a >= s.e), lim = fb ? Y(fb[0]) : H;\n"
  "      const top = Math.max(0, Math.min(Y(s.s), lim - h));"),
 ("    const now = (wide && d === today && nowMin >= S0 && nowMin <= S1) ? `<span class=\"g-now\" style=\"top:${(nowMin - S0) * k}px\">",
  "    const now = (wide && d === today && nowMin >= S0 && nowMin <= S1 && !folds.some(([a, b]) => nowMin > a && nowMin < b)) ? `<span class=\"g-now\" style=\"top:${Y(nowMin)}px\">"),
 ("<div class=\"g-lab\">${labels.join('')}</div>${cols}</div></div>`;",
  "<div class=\"g-lab\">${labels.join('')}</div>${cols}${folds.map(([a, b]) => `<div class=\"g-fold\" style=\"top:${Y(a)}px;height:${FOLD}px\"><span>No classes ${hs(a)}–${hs(b)}</span></div>`).join('')}</div></div>`;"),
 (".g-col.on{background:var(--blue-soft)}",
  ".g-col.on{background:var(--blue-soft)}\n"
  "/* a folded stretch with no classes on any day (Home cards, 2026-09-30) */\n"
  ".g-fold{position:absolute;left:calc(var(--glab,30px) + var(--ggap,6px));right:0;z-index:2;display:flex;align-items:center;justify-content:center;background:#fff;border-top:1.5px dashed var(--line);border-bottom:1.5px dashed var(--line);pointer-events:none}\n"
  ".g-fold span{font-size:9.5px;font-weight:800;color:var(--muted2);letter-spacing:.02em;white-space:nowrap}"),
]
for a, b in R:
    n = s.count(a)
    if n != 1: sys.exit(f'anchor matched {n}x: {a[:90]}')
    s = s.replace(a, b)
open(p, 'w', encoding='utf-8').write(s)
print('patched', p)
