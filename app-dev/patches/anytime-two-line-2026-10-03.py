#!/usr/bin/env python3
"""Anytime tray: codes on two lines, every class shown, no "+N" (Tate, 2026-10-03, on a tray reading
"ANYTIME  BUS 4418A  UNIV 4401  +1" next to the week's "BUS / 4404" blocks: "maybe put the class codes
under the Bus similar to how the other classes are so you can fit more on the screen i dont like the +1
option").

- Each chip shows the subject over the number, like a narrow block on the week ("BUS" / "4418A"), so a
  chip is about half as wide and more fit on a line.
- Every class is shown. If they still don't fit on one line, the tray wraps to a second line — nothing
  is hidden behind "+N", and nothing is clipped.
- The width measuring that decided how many chips fit (and its redraw on resize) is gone with "+N".

Applies after rings-free-today-2026-10-03.py.
Usage: python3 anytime-two-line-2026-10-03.py <repo-dir>   (edits <repo-dir>/app/index.html)
"""
import sys, os
p = os.path.join(sys.argv[1], 'app', 'index.html')
s = open(p, encoding='utf-8').read()
if 'const anyCode = ' in s: sys.exit('already patched')

# the fit/+N block, from the comment above the chips to the "+N" count
a = s.index("  /* The Anytime tray (option A3): codes only, on one line.")
b = s.index("  const anyMore = anyCodes.length - anyFit;\n")
b = b + len("  const anyMore = anyCodes.length - anyFit;\n")
if s.count("  /* The Anytime tray (option A3): codes only, on one line.") != 1 or b < a: sys.exit('tray block anchor')
old = s[a:b]
for need in ("const anyItems = untimed.map(", "const anyFit = (() => {", "ANY_W = (document.getElementById('scroll')"):
    if need not in old: sys.exit('tray block changed: ' + need)
s = s[:a] + (
  "  /* The Anytime tray (option A3, then Tate 2026-10-03): every class, its code on two lines like a narrow\n"
  "     block on the week (\"BUS\" over \"4418A\"); the tray wraps rather than hiding any behind \"+N\". */\n"
  "  const anyCode = c => { const i = c.indexOf(' '); return i < 0 ? `<span>${esc(c)}</span>` : `<span>${esc(c.slice(0, i))}</span><span>${esc(c.slice(i + 1))}</span>`; };\n"
  "  const anyItems = untimed.map(s => `<button class=\"any-c${ring(s.code)}\" data-a=\"secSheet\" data-x=\"${esc(s.code)}\" data-y=\"${esc(s.id)}\" title=\"${esc(s.code + ' · ' + secWhen(s))}\" aria-label=\"${esc(s.code)}\">${anyCode(s.code)}</button>`)\n"
  "    .concat(loose.map(c => `<button class=\"any-c${ring(c)}\" data-a=\"openClass\" data-x=\"${esc(c)}\" title=\"${esc(c + ' · No section')}\" aria-label=\"${esc(c)}\">${anyCode(c)}</button>`));\n"
) + s[b:]

R = [
 ("  const anyRow = anyCodes.length ? `<div class=\"anyrow\" role=\"group\" aria-label=\"Classes with no set time\"><span class=\"any-h\">Anytime</span>${anyItems.slice(0, anyFit).join('')}${anyMore ? `<button class=\"any-more\" data-a=\"${isMe ? 'tab' : 'openFriend'}\" data-x=\"${isMe ? 'schedule' : esc(id)}\" aria-label=\"${anyMore} more class${anyMore === 1 ? '' : 'es'} with no set time\">+${anyMore}</button>` : ''}</div>` : '';\n",
  "  const anyRow = anyItems.length ? `<div class=\"anyrow\" role=\"group\" aria-label=\"Classes with no set time\"><span class=\"any-h\">Anytime</span>${anyItems.join('')}</div>` : '';\n"),
 (".anyrow{display:flex;flex-wrap:nowrap;align-items:center;gap:6px;",
  ".anyrow{display:flex;flex-wrap:wrap;align-items:center;gap:6px;"),
 (".any-c{flex:none;display:inline-flex;align-items:center;min-height:42px;padding:0 12px;border-radius:10px;background:#fff;color:var(--blue-ink);font-size:13px;font-weight:900;letter-spacing:.02em;white-space:nowrap}\n",
  ".any-c{flex:none;display:inline-flex;flex-direction:column;align-items:center;justify-content:center;min-height:42px;min-width:50px;padding:4px 10px;border-radius:10px;background:#fff;color:var(--blue-ink);font-size:13px;line-height:1.15;font-weight:900;letter-spacing:.02em;white-space:nowrap}\n"),
 (".any-more{flex:none;display:grid;place-items:center;min-height:42px;min-width:42px;padding:0 10px;border-radius:10px;background:#fff;color:var(--muted);font-size:13px;font-weight:900}\n", ""),
 ("var ANY_W, anyRz;   /* var, not let: Home can draw before this line runs */\n"
  "addEventListener('resize', () => { clearTimeout(anyRz); anyRz = setTimeout(() => { const w = (document.getElementById('scroll') || {}).clientWidth; if (w && ANY_W && w !== ANY_W && document.querySelector('.anyrow')) render(true); }, 150); });\n", ""),
]
for x, y in R:
    if s.count(x) != 1: sys.exit(f'anchor matched {s.count(x)}x: {x[:80]}')
    s = s.replace(x, y)
if 'anyFit' in s or 'anyMore' in s or 'ANY_W' in s: sys.exit('left-over +N code')
open(p, 'w', encoding='utf-8').write(s)
print('patched', p)
