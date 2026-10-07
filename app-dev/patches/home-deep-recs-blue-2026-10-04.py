#!/usr/bin/env python3
"""Home: a deeper page so each friend's week stands apart, and the class suggestions get blue tops
(Tate, 2026-10-04, choosing from the "Home Feed Contrast" mockup: "sugessted classes do colored tops but only
do the blue color we use for classes. then for each friends week lets do A, make it feel deeper.").

1. Deeper page (option A). On Home only, the page behind the cards is one shade deeper, #E7ECF5 (was
   #F4F6FB), and Home's cards get a firmer shadow, so each white card has a clear edge. Nothing inside the
   cards changes (the week's day columns stay #F4F6FB). The status band, the phone strip colour
   (theme-color) and — on a phone — the page behind the clock all switch with it, so the top stays one
   colour (the 01:15 blend fix). Other tabs keep #F4F6FB. Light mode only: in dark mode Home stays the dark page.
2. Suggested classes (option C, in the class blue only). Each card has a filled top in the blue every class
   block uses (#E3ECFF, code in #1E40AF): the code large, and the friends taking it under it. The class name
   and the professor rating sit on white below. The heading is now "Classes your friends are taking" in
   normal type, with a small "Suggested" tag on the right, so it is still labelled as a suggestion.

Applies after phone-top-blend-2026-10-04.py (build 2026-10-05 01:15).
Usage: python3 home-deep-recs-blue-2026-10-04.py <repo-dir>
"""
import sys, os
p = os.path.join(sys.argv[1], 'app', 'index.html')
s = open(p, encoding='utf-8').read()
if '.rm-top{' in s: sys.exit('already patched')
DEEP = '#E7ECF5'
R = [
 # recs heading + card
 ('<div class="recs-h">Suggested · classes your friends are taking</div>',
  '<div class="recs-h"><span>Classes your friends are taking</span><span class="rs-tag">Suggested</span></div>'),
 ('<button class="card rmini" data-a="openClass" data-x="${esc(r.code)}"><span class="code">${esc(r.code)}</span>${nm ? `<span class="rm-t">${esc(nm)}</span>` : \'\'}<span class="rm-p">${avStack(r.who, 22)}<span>${r.who.length} friend${r.who.length === 1 ? \'\' : \'s\'}</span></span>${t ? ',
  '<button class="card rmini" data-a="openClass" data-x="${esc(r.code)}"><span class="rm-top"><span class="code rm-k">${esc(r.code)}</span><span class="rm-p">${avStack(r.who, 22)}<span>${r.who.length} friend${r.who.length === 1 ? \'\' : \'s\'}</span></span></span><span class="rm-bd">${nm ? `<span class="rm-t">${esc(nm)}</span>` : \'\'}${t ? '),
 ('${rt.toFixed(1)}${last ? `<span class="rm-ln">&nbsp;· ${esc(last)}</span>` : \'\'}</span>` : \'\'}</button>`;',
  '${rt.toFixed(1)}${last ? `<span class="rm-ln">&nbsp;· ${esc(last)}</span>` : \'\'}</span>` : \'\'}</span></button>`;'),
 # css
 ('.rmini .rchip{max-width:100%;white-space:nowrap}',
  '.rmini .rchip{max-width:100%;white-space:nowrap}\n'
  '/* 2026-10-04: blue tops (Tate) */\n'
  '.recs-h{display:flex;align-items:center;justify-content:space-between;gap:8px;font-size:15px;letter-spacing:0;text-transform:none;color:var(--ink);padding-bottom:9px}\n'
  '.recs-h .rs-tag{flex:none;font-size:10.5px;font-weight:900;letter-spacing:.07em;text-transform:uppercase;color:var(--blue-ink);background:var(--blue-soft);padding:3px 8px;border-radius:99px}\n'
  '.rmini{padding:0;gap:0;overflow:hidden;align-items:stretch}\n'
  '.rm-top{display:flex;flex-direction:column;align-items:flex-start;gap:7px;background:var(--blue-soft);padding:12px 12px 10px}\n'
  '.rmini .rm-k{background:none;padding:0;border-radius:0;font-size:20px;letter-spacing:-.01em;line-height:1.1;color:var(--blue-ink)}\n'
  '.rm-top .rm-p{margin-top:0;color:var(--blue-ink)}\n'
  '.rm-bd{flex:1;display:flex;flex-direction:column;align-items:flex-start;gap:8px;padding:10px 12px 12px}\n'
  '.rm-bd .rchip{margin-top:auto}\n'
  '/* 2026-10-04: Home, a deeper page (Tate) */\n'
  ':root.deep .phone,:root.deep .status{background:' + DEEP + '}\n'
  '.homepg .card{box-shadow:0 1px 0 rgba(15,23,42,.05),0 2px 4px rgba(15,23,42,.05),0 14px 30px rgba(22,51,107,.10)}\n'
  '@media (max-width:520px){html.deep,html.deep body{background:' + DEEP + '}}'),
 # render: toggle + strip colour
 ("  document.querySelectorAll('meta[name=theme-color]').forEach(m => { m.content = v.dark ? '#0F172A' : isDark() && !sc.querySelector('.onb') ? '#0A0F1C' : '#F4F6FB'; });",
  "  const deep = !v.dark && !isDark() && TC.phase === 'ok' && S.tab === 'home' && !!e && e.s === 'home'; document.documentElement.classList.toggle('deep', deep);\n"
  "  document.querySelectorAll('meta[name=theme-color]').forEach(m => { m.content = v.dark ? '#0F172A' : isDark() && !sc.querySelector('.onb') ? '#0A0F1C' : deep ? '" + DEEP + "' : '#F4F6FB'; });"),
]
for a, b in R:
    if s.count(a) != 1: sys.exit(f'anchor matched {s.count(a)}x: {a[:90]}')
    s = s.replace(a, b)
open(p, 'w', encoding='utf-8').write(s)
print('patched', p)
