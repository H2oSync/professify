#!/usr/bin/env python3
"""Mutants for the option-C friend header. Usage: python3 friend-header-strip-mutants-2026-10-10.py app-dev/tests/mutate.mjs"""
import sys, json
p = sys.argv[1]; s = open(p, encoding='utf-8').read()
def one(old, new):
    global s
    assert s.count(old) == 1, (s.count(old), old[:90]); s = s.replace(old, new)
J = json.dumps
# the two old Message mutants named the 44px round button
one('''"${ic('msg', 20, 2.3)}</button>` : ''}</div>", "${ic('msg', 20, 2.3)}</button>${pinBtn(id, 'fpin')}` : ''}</div>", "storyPins"],''',
    '''"${ic('msg', 15, 2.4)}Message</button>` : ''}</div>", "${ic('msg', 15, 2.4)}Message</button>${pinBtn(id, 'fpin')}` : ''}</div>", "storyPins"],''')
i = s.index('  ["friend page: Message full width again"'); j = s.index('\n', i)
M = [
 ("friend page: Message full width again", ".fpg .fmsg{display:inline-flex;align-items:center;justify-content:center;gap:6px;width:auto;height:34px;", ".fpg .fmsg{display:inline-flex;align-items:center;justify-content:center;gap:6px;width:300px;height:34px;", "friendMajor"),
 ("friend page: Message back to a big round icon", "height:34px;padding:0 14px;border-radius:999px;font-size:13px;font-weight:900;flex:none;align-self:center}", "height:44px;padding:0 14px;border-radius:999px;font-size:13px;font-weight:900;flex:none;align-self:center}", "friendMajor"),
 ("friend page: Message loses its word", "${ic('msg', 15, 2.4)}Message</button>` : ''}</div>\n  ${isF", "${ic('msg', 15, 2.4)}</button>` : ''}</div>\n  ${isF", "friendMajor"),
 ("friend strip: year as wide as the others", ".fs-c.y{flex:0 0 auto}", ".fs-c.y{flex:1 1 0}", "friendStrip"),
 ("friend strip: words break mid-word", "overflow-wrap:break-word;word-break:normal;hyphens:none}", "overflow-wrap:anywhere;word-break:break-all;hyphens:none}", "friendStrip"),
 ("friend strip: green again", ".fstrip{display:flex;border-radius:16px;overflow:hidden;background:var(--fs-bg)}", ".fstrip{display:flex;border-radius:16px;overflow:hidden;background:var(--mg-bg)}", "friendStrip"),
 ("friend strip: no dark fill", ':root[data-theme="dark"] .fpg{--fs-bg:#1B2438;--fs-ln:#26304A;--fs-mut:#9AA6BA}', ':root[data-theme="dark"] .fpg{--fs-ln:#26304A;--fs-mut:#9AA6BA}', "friendStrip"),
 ("friend strip: year dropped", "p.standing ? cell('Year', p.standing, 'y') : ''", "''", "friendStrip"),
 ("friend strip: General / Open shown as a concentration", "const conc = p.conc && p.conc !== 'General / Open' ? meConc(p.conc) : '';\n  const cell", "const conc = p.conc ? meConc(p.conc) : '';\n  const cell", "friendStrip"),
 ("friend strip: long word clipped instead of broken", "overflow-wrap:break-word;word-break:normal;hyphens:none}", "overflow-wrap:normal;word-break:normal;hyphens:none}", "friendStrip"),
]
lines = '\n'.join('  [%s, %s, %s, %s],' % (J(a, ensure_ascii=False), J(b, ensure_ascii=False), J(c, ensure_ascii=False), J(d)) for a, b, c, d in M)
s = s[:i] + lines + s[j:]
open(p, 'w', encoding='utf-8').write(s); print('mutants patched')
