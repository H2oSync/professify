#!/usr/bin/env python3
"""Class blocks: the text fills the block as far as it can before it looks crowded (Tate, 2026-09-30:
"lets fill as much before it looks crowded the squares so the text is easier to read").

Before: every narrow block was 10px text (9px beside a tapped day) whatever its size, and a tapped
day's block was 11px code over 10px time — so a 50px-wide, 60px-tall block held a tiny "BUS / 3348".
Now each block's text is the largest that fits BOTH ways, with air left over, capped at 14px:
  - width: the column is a size container (cqi), and each block carries its own text width in em
    (--cw: the wider of "BUS" / "3348"; --cwl: the whole "BUS 3348" of a tapped day), from a table of
    Nunito 900 glyph widths measured in the app — so "BUS" gets bigger than "WGQS" in the same column,
    each with ~3px either side (2px beside a tapped day);
  - height: the grid knows each block's height, and passes --fh = what two lines fit with ~3px
    above and below (2px in a block at the old 26px minimum, which keeps its old look; a tapped day's block: code + time, plus the faces row when it has one).
Browsers without container units keep the old fixed sizes (each rule states them first).
The floors are the old sizes (10 / 9 / 11+10), so no block's text ever gets smaller than it was —
except text that used to spill out of a very narrow column (WGQS in a 32px column; a tapped day's
"WGQS 3500" or "12:10–12:50p" under the 110px floor on a tiny phone), which now shrinks just enough to show
whole (6.65em is the widest time, "12:10–12:50p" at 700 with its letter-spacing). The small-phone
(≤340px) rule that pinned a tapped day's code and time at 10.5 / 9px goes too: the width terms already
size them to the column;
short "tight" blocks keep their fixed small sizes.

Applies after home-card-trim-2026-09-30.py.
Usage: python3 grid-text-fill-2026-09-30.py <repo-dir>   (edits <repo-dir>/app/index.html)
"""
import sys, os
p = os.path.join(sys.argv[1], 'app', 'index.html')
s = open(p, encoding='utf-8').read()
if '--fh' in s: sys.exit('already patched')
R = [
 (".g-col{position:relative;border-radius:12px;background:var(--bg)}",
  ".g-col{position:relative;border-radius:12px;background:var(--bg);container-type:inline-size}"),
 ("color:var(--blue-ink);font-size:10px;font-weight:900;line-height:1.08;display:grid;",
  "color:var(--blue-ink);font-size:10px;font-size:clamp(min(10px, (100cqi - 8px) / var(--cw, 2.5)), min((100cqi - 12px) / var(--cw, 2.5), var(--fh, 10px)), 14px);font-weight:900;line-height:1.04;display:grid;"),
 (".grid.focused .g-col:not(.on) .g-b{font-size:9px;letter-spacing:0;left:2px;right:2px}",
  ".grid.focused .g-col:not(.on) .g-b{font-size:9px;font-size:clamp(min(9px, (100cqi - 6px) / var(--cw, 2.5)), min((100cqi - 8px) / var(--cw, 2.5), var(--fh, 9px)), 14px);letter-spacing:0;left:2px;right:2px}"),
 (".g-b.wide .g-code{font-size:11px;white-space:nowrap}",
  ".g-b.wide .g-code{font-size:11px;font-size:clamp(min(11px, (100cqi - 22px) / var(--cwl, 6.4)), min(var(--fh, 11px), (100cqi - 24px) / var(--cwl, 6.4)), 14px);white-space:nowrap}"),
 ("@media (max-width:340px){.g-b.wide{padding:5px 4px}.g-b.wide.tight{padding:2px 4px;column-gap:3px}.g-b.wide .g-time{font-size:9px}.g-b.wide .g-code{font-size:10.5px}}",
  "@media (max-width:340px){.g-b.wide{padding:5px 4px}.g-b.wide.tight{padding:2px 4px;column-gap:3px}}"),
 (".g-b.wide .g-time{font-size:10px;font-weight:700;opacity:.9;white-space:nowrap}",
  ".g-b.wide .g-time{font-size:10px;font-size:clamp(min(10px, (100cqi - 22px) / 6.65), min(var(--fh, 11px) * .86, (100cqi - 24px) / 6.65), 12px);font-weight:700;opacity:.9;white-space:nowrap}"),
 ("      const tight = wide && h < (faces ? 56 : 36);   /* no room for three rows */\n",
  "      const tight = wide && h < (faces ? 56 : 36);   /* no room for three rows */\n"
  "      /* the tallest text the block holds with air around it: two lines in a narrow block; code + time\n"
  "         (+ the faces row) in a tapped day's. Width is the CSS's half of it (cqi). Tight blocks keep fixed sizes. */\n"
  "      const fh = tight ? 0 : wide ? (h - 12 - (faces ? 24 : 0)) / 1.95 : (h - 4) / 2.08;\n"
  "      const cw = Math.max(textEm(s.code.split(' ')[0]), textEm(s.code.split(' ')[1] || '')).toFixed(2), cwl = textEm(s.code).toFixed(2);\n"),
 ("      return `<button class=\"${cls}\" style=\"top:${top}px;height:${h}px\" data-a=",
  "      return `<button class=\"${cls}\" style=\"top:${top}px;height:${h}px;--cw:${cw};--cwl:${cwl}${fh > 0 ? `;--fh:${fh.toFixed(1)}px` : ''}\" data-a="),
 ("function grid(secs, o) {\n",
  "/* Nunito 900 glyph widths in em, measured in the app (2026-09-30), plus the blocks' .02em letter-spacing:\n"
  "   how wide a block's text is, so its size can fill the block without spilling. Unknown glyphs count wide. */\n"
  "const GLYPH_EM = {\"0\":.6,\"1\":.6,\"2\":.6,\"3\":.6,\"4\":.6,\"5\":.6,\"6\":.6,\"7\":.6,\"8\":.6,\"9\":.6,A:.76,B:.7,C:.69,D:.79,E:.61,F:.57,G:.75,H:.78,I:.3,J:.39,K:.71,L:.58,M:.89,N:.76,O:.82,P:.67,Q:.82,R:.7,S:.65,T:.65,U:.75,V:.74,W:1.13,X:.7,Y:.65,Z:.63,\" \":.29};\n"
  "const textEm = t => [...String(t)].reduce((a, c) => a + (GLYPH_EM[c] || 1.13) + .02, 0);\n"
  "function grid(secs, o) {\n"),
]
for a, b in R:
    if s.count(a) != 1: sys.exit(f'anchor matched {s.count(a)}x: {a[:70]}')
    s = s.replace(a, b)
open(p, 'w', encoding='utf-8').write(s)
print('patched', p)
