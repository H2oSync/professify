#!/usr/bin/env python3
"""Mutants for me-strip-2026-10-11.py. Retires the D2 bubble mutants whose code is gone or now unused (the green
bubbles, YEAR label, no-concentration row, Add your major bubble, the dark/light green tokens, the count tiles) and
re-aims the friend strip's four onto the shared profStrip(). Usage: python3 me-strip-mutants-2026-10-11.py <repo>"""
import sys, pathlib, json
root = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else '.')
f = root / 'app-dev' / 'tests' / 'mutate.mjs'
s = f.read_text()
if '/* me-strip (2026-10-11) */' in s:
    sys.exit('already patched')
lines = s.split('\n')
RETIRE = ['d2: green bubbles a gradient', 'd2: YEAR label back', 'd2: no concentration hides the year', 'd2: no major, no way to add it',
          'd2: dark green text too dark', 'd2: light label under 4.5:1', 'me: count tiles back']
def name_of(l):
    t = l.strip()
    if not t.startswith('['): return None
    try: return json.loads(t.rstrip(',') )[0]
    except Exception: return None
out, gone = [], []
for l in lines:
    n = name_of(l)
    if n in RETIRE: gone.append(n); continue
    out.append(l)
assert sorted(gone) == sorted(RETIRE), gone
s = '\n'.join(out)
def one(old, new):
    global s
    n = s.count(old)
    assert n == 1, (n, old[:90])
    s = s.replace(old, new)
J = lambda m: json.dumps(m, ensure_ascii=False)
one(J(["friend strip: no dark fill", ":root[data-theme=\"dark\"] .fpg{--fs-bg:#1B2438;--fs-ln:#26304A;--fs-mut:#9AA6BA}", ":root[data-theme=\"dark\"] .fpg{--fs-ln:#26304A;--fs-mut:#9AA6BA}", "friendStrip"]),
    J(["friend strip: no dark fill", ":root[data-theme=\"dark\"] .meown{--fs-bg:#1B2438;--fs-ln:#26304A;--fs-mut:#9AA6BA}", ":root[data-theme=\"dark\"] .meown{--fs-ln:#26304A;--fs-mut:#9AA6BA}", "friendStrip"]))
one(J(["friend strip: year dropped", "p.standing ? cell('Year', p.standing, 'y') : ''", "''", "friendStrip"]),
    J(["friend strip: year dropped", "year ? cell('Year', year, 'y') : ''", "''", "friendStrip"]))
one(J(["friend strip: General / Open shown as a concentration", "const conc = p.conc && p.conc !== 'General / Open' ? meConc(p.conc) : '';\n  const cell", "const conc = p.conc ? meConc(p.conc) : '';\n  const cell", "friendStrip"]),
    J(["friend strip: General / Open shown as a concentration", "const conc = conc0 && conc0 !== 'General / Open' ? meConc(conc0) : '';\n  const cell", "const conc = conc0 ? meConc(conc0) : '';\n  const cell", "friendStrip"]))
one(J(["d2: concentration said twice", "const meConc = c => String(c || '').replace(/\\s+concentration\\s*$/i, '').trim();", "const meConc = c => String(c || '').trim();", "meBubbles"]),
    J(["d2: concentration said twice", "const meConc = c => String(c || '').replace(/\\s+concentration\\s*$/i, '').trim();", "const meConc = c => String(c || '').trim();", "meStrip"]))
one(J(["General / Open shown as a concentration", "p.conc && p.conc !== 'General / Open' ?", "p.conc ?", "friendMajor"]),
    J(["General / Open shown as a concentration", "conc0 && conc0 !== 'General / Open' ?", "conc0 ?", "friendMajor"]))
NEW = [
  ["me strip: no strip on my profile", "const strip = profStrip(P.major, P.concentration, P.class_standing, 'mestrip', true);", "const strip = '';", "meStrip"],
  ["me strip: no Add your major", "mine ? '<button class=\"fs-c g fs-add\"", "0 ? '<button class=\"fs-c g fs-add\"", "meStrip"],
  ["me strip: Add your major goes nowhere", "<button class=\"fs-c g fs-add\" data-a=\"openEditProfile\">", "<button class=\"fs-c g fs-add\">", "meStrip"],
  ["me strip: Add your major not blue", ".fs-add .fs-v{color:var(--blue-t,var(--blue))}", "", "meStrip"],
  ["me strip: the big photo back", "${pav('me', 46, 18)}</span><div class=\"grow\"><div class=\"mename\">${esc(PEOPLE.me.name)}", "${pav('me', 76, 26)}</span><div class=\"grow\"><div class=\"mename\">${esc(PEOPLE.me.name)}", "meStrip"],
  ["me strip: no focus ring on Add your major", ".fs-add:focus-visible{outline-offset:-3px;border-radius:16px}", "", "meStrip"],
  ["me strip: my head's gap", ".fpg .mehead,.meown .mehead{gap:12px}", ".fpg .mehead{gap:12px}", "meStrip"],
  ["me strip: my handle drops", ".fpg .mehandle,.meown .mehandle{", ".fpg .mehandle{", "meStrip"],
  ["me strip: Add your major narrow", "<button class=\"fs-c g fs-add\"", "<button class=\"fs-c fs-add\"", "meStrip"],
  ["me strip: the round pencil back", "${ic('pencil', 15, 2.4)}Edit</button>", "${ic('pencil', 19, 2.3)}</button>", "meStrip"],
  ["me strip: a 44px Edit", "gap:6px;width:auto;height:34px;padding:0 14px;border-radius:999px;font-size:13px;font-weight:900;align-self:center;color:var(--blue-ink)}", "gap:6px;width:auto;height:44px;padding:0 14px;border-radius:999px;font-size:13px;font-weight:900;align-self:center;color:var(--blue-ink)}", "meStrip"],
  ["me strip: Edit's word under 4.5:1", "align-self:center;color:var(--blue-ink)}", "align-self:center}", "meStrip"],
  ["me strip: my card not compact", ".fpg .mecard,.meown .mecard{", ".fpg .mecard{", "meStrip"],
  ["me strip: my name stays 24px", ".fpg .mename,.meown .mename{", ".fpg .mename{", "meStrip"],
  ["me strip: no light fill on my strip", ".fpg,.meown{--fs-bg:#F1F5F9;", ".fpg{--fs-bg:#F1F5F9;", "meStrip"],
  ["me strip: the friend page loses its strip", "  return profStrip(p.major, p.conc, p.standing, 'fbubs');", "  return '';", "friendStrip"],
  ["current term: amber again", ".curterm{background:var(--blue-soft);color:var(--blue-ink);", ".curterm{background:var(--amber-soft);color:var(--seat-low);", "curTermBlue"],
]
i = s.index('const M = ['); j = s.index('\n];\n', i)
s = s[:j + 1] + '  /* me-strip (2026-10-11) */\n' + ''.join('  ' + J(m) + ',\n' for m in NEW) + s[j + 1:]
f.write_text(s)
print('patched', f)
