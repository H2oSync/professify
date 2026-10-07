#!/usr/bin/env python3
"""The top of the screen is one colour (Tate, 2026-09-30: "Color difference at the very top" — the
pick: "Make the status bar, the header and the page one continuous colour. Add a thin hairline
under the header only once you scroll").

- The strip behind the clock is the page's own colour (#F4F6FB) everywhere:
  - theme-color is set for light AND dark mode (a phone in dark mode no longer gets a dark strip
    over a light app), and color-scheme says the app is light;
  - on a phone the top safe-area strip is now drawn (it was hidden, so content slid up under the
    clock with nothing behind it); in the Desktop preview the fake status bar is solid instead of
    fading out over the content.
- A hairline appears under that strip only once the page is scrolled, and never on a screen that
  already has its own header bar (a chat), so there are never two lines.

Applies after stories-now-2026-09-30.py.
Usage: python3 top-colour-2026-09-30.py <repo-dir>   (edits <repo-dir>/app/index.html)
"""
import sys, os
p = os.path.join(sys.argv[1], 'app', 'index.html')
s = open(p, encoding='utf-8').read()
if 'function statusHair' in s: sys.exit('already patched')
R = [
 ('<meta name="theme-color" content="#F4F6FB">\n',
  '<meta name="theme-color" content="#F4F6FB" media="(prefers-color-scheme: light)">\n'
  '<meta name="theme-color" content="#F4F6FB" media="(prefers-color-scheme: dark)">\n'
  '<meta name="color-scheme" content="light">\n'),
 ('.status{background:linear-gradient(var(--bg) 75%,rgba(244,246,251,0))}\n.status.dark{color:#fff;background:#0F172A}\n',
  '.status{background:var(--bg);transition:box-shadow .2s}\n.status.scrolled{box-shadow:0 1px 0 rgba(15,23,42,.1)}\n.status.dark{color:#fff;background:#0F172A;box-shadow:none}\n'),
 ('  .status,.island,.homebar{display:none}\n',
  '  .island,.homebar{display:none}\n  .status{padding:0}\n  .status>*{visibility:hidden}\n'),
 ("  if (!sc._barsOn) { sc._barsOn = true; sc.addEventListener('scroll', onScrollBars, { passive: true }); }",
  "  if (!sc._barsOn) { sc._barsOn = true; sc.addEventListener('scroll', onScrollBars, { passive: true }); sc.addEventListener('scroll', statusHair, { passive: true }); }"),
 ("  document.getElementById('status').classList.toggle('dark', !!v.dark);\n",
  "  document.getElementById('status').classList.toggle('dark', !!v.dark);\n  document.querySelectorAll('meta[name=theme-color]').forEach(m => { m.content = v.dark ? '#0F172A' : '#F4F6FB'; });\n"),
 ("  if (v.scrollEnd && !keep) scrollEnd();\n",
  "  if (v.scrollEnd && !keep) scrollEnd();\n  statusHair();\n"),
 ("let toastT;\n",
  "/* The hairline under the top strip: only once the page has scrolled, and not over a screen's own header. */\n"
  "function statusHair() { const sc = document.getElementById('scroll'), st = document.getElementById('status'), ft = document.getElementById('fixtop'); if (sc && st) st.classList.toggle('scrolled', sc.scrollTop > 2 && !(ft && ft.innerHTML.trim())); }\n"
  "let toastT;\n"),
]
for a, b in R:
    if s.count(a) != 1: sys.exit(f'anchor matched {s.count(a)}x: {a[:80]}')
    s = s.replace(a, b)
open(p, 'w', encoding='utf-8').write(s)
print('patched', p)
