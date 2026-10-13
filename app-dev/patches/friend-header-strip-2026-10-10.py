#!/usr/bin/env python3
"""Friend profile header, option C (Tate, 2026-10-10): one white card with photo, name, @handle and a small
pink "Message" pill; under it ONE neutral strip: MAJOR | CONCENTRATION | YEAR (year hugs its word).
Your own profile (.mebub*) is not touched.  Usage: python3 friend-header-strip-2026-10-10.py app/index.html"""
import sys
path = sys.argv[1]
s = open(path, encoding='utf-8').read()
def one(old, new):
    global s
    assert s.count(old) == 1, ('anchor count', s.count(old), old[:80])
    s = s.replace(old, new)

# 1. header row: smaller photo, labelled Message pill
one("""${pav(id, 72, 25)}</span>""", """${pav(id, 46, 18)}</span>""")
one("""${ic('msg', 20, 2.3)}</button>""", """${ic('msg', 15, 2.4)}Message</button>""")

# 2. the strip
i = s.index("function friendBubbles(p) {")
j = s.index("/* ---- Home's feed order", i)
s = s[:i] + """function friendBubbles(p) {
  /* Tate 2026-10-10 (option C): one neutral strip. Major and concentration share the width, the year only
     takes its own word's width; words wrap at spaces; a word only breaks if it can't fit a line alone (never clipped). "General / Open" is no concentration. */
  const conc = p.conc && p.conc !== 'General / Open' ? meConc(p.conc) : '';
  const cell = (l, v, c) => `<div class="fs-c ${c}"><span class="fs-l">${l}</span><span class="fs-v">${esc(v)}</span></div>`;
  const parts = [p.major ? cell('Major', p.major, 'g') : '', conc ? cell('Concentration', conc, 'g') : '', p.standing ? cell('Year', p.standing, 'y') : ''].filter(Boolean);
  return parts.length ? `<div class="fstrip fbubs">${parts.join('')}</div>` : '';
}
""" + s[j:]

# 3. css
one(""".fpg .fmsg{display:grid;place-items:center;width:44px;height:44px;padding:0;border-radius:22px;flex:none;align-self:center}
.fpg .fmsg svg{flex:none}""", """.fpg .fmsg{display:inline-flex;align-items:center;justify-content:center;gap:6px;width:auto;height:34px;padding:0 14px;border-radius:999px;font-size:13px;font-weight:900;flex:none;align-self:center}
.fpg .fmsg svg{flex:none}
/* friend header, option C (Tate 2026-10-10): compact card + one neutral strip. Own tokens (--sb is the status-bar height). */
.fpg{--fs-bg:#F1F5F9;--fs-ln:#E2E8F0;--fs-mut:#5B6B80}
:root[data-theme="dark"] .fpg{--fs-bg:#1B2438;--fs-ln:#26304A;--fs-mut:#9AA6BA}
.fpg .mecard{padding:12px;gap:12px;border-radius:24px}
.fpg .mehead{gap:12px}
.fpg .mename{font-size:20px;line-height:1.15}
.fpg .mehandle{font-size:13px;margin-top:0}
.fstrip{display:flex;border-radius:16px;overflow:hidden;background:var(--fs-bg)}
.fs-c{display:flex;flex-direction:column;gap:4px;min-width:0;padding:11px 8px 12px;color:var(--ink);overflow-wrap:break-word;word-break:normal;hyphens:none}
.fs-c.g{flex:1 1 0}
.fs-c.y{flex:0 0 auto}
.fs-c.y .fs-v{white-space:nowrap}
.fs-c + .fs-c{border-left:1px solid var(--fs-ln)}
.fs-l{font-size:9.5px;font-weight:900;letter-spacing:.03em;text-transform:uppercase;color:var(--fs-mut);white-space:nowrap}
.fs-v{font-size:12px;font-weight:900;line-height:1.25}
@media (max-width:370px){.fs-c{padding-left:6px;padding-right:6px}}""")
open(path, 'w', encoding='utf-8').write(s)
print('patched', path)
