#!/usr/bin/env python3
"""No "did well" tags on a professor's page (Tate, 2026-10-04).

"since we took these out of the rating make sure to remove it from this rating as well": 13:05 took the
"What did they do well?" chips out of the rate form, but the professor page's TermChamp reviews card still
listed the most-picked ones from older reviews ("Explains concepts clearly", "Ran engaging discussions",
…). They're gone; the count, the star bars, difficulty and "would take again" stay. Older reviews keep
their tags in the database (an edit still doesn't wipe them); nothing shows them.

Applies after support-email-2026-10-04.py (build 19:15).
Usage: python3 prof-no-tags-2026-10-04.py <repo-dir>   (edits <repo-dir>/app/index.html)
"""
import sys, os
p = os.path.join(sys.argv[1], 'app', 'index.html')
s = open(p, encoding='utf-8').read()
if '<span class="tag">' not in s: sys.exit('already patched')
R = [
 ("""
   ${st.tags.length ? `<div style="margin-top:10px">${st.tags.map(t => `<span class="tag">${esc(t)}</span>`).join('')}</div>` : ''}</div>` : `<div class="muted b" style="font-size:13px;border-top""",
  """</div>` : `<div class="muted b" style="font-size:13px;border-top"""),
 (".tag{display:inline-block;background:var(--purple-soft);color:var(--purple-ink);font-weight:900;font-size:13px;padding:7px 12px;border-radius:16px;margin:0 6px 6px 0}\n", ""),
]
for a, b in R:
    n = s.count(a)
    if n != 1: sys.exit(f'anchor matched {n}x: {a[:90]}')
    s = s.replace(a, b)
open(p, 'w', encoding='utf-8').write(s)
print('patched', p)
