#!/usr/bin/env python3
"""Two small fixes (Tate, 2026-10-08).

1. Friends' faces on a tapped day of My Classes / Plans: "fix this … where the friends profile
   pictures arent all circluar and even one is square and further down". A friend in your exact
   section was drawn as a rounded square (class "sq"), and the app-wide `.sq{display:grid;
   border-radius:16px}` rule made that face's box a grid while the round ones were plain blocks, so it
   sat lower on the line. Every face is now a circle in the same inline box. Friends in your section
   still come first; the face carries data-in="same|other" instead of the sq/ci classes.

2. Plans no longer say "Plans use Fall 2026 sections. Once Spring 2027 is in TermChamp, plan with
   those. Sections in a plan get seat alerts." (Tate: "get rid of this message").

Usage: python3 faces-round-no-term-note-2026-10-08.py <repo>
"""
import sys, pathlib
root = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else '.')
f = root / 'app' / 'index.html'
s = f.read_text()
if 'faces-round-no-term-note (2026-10-08)' in s:
    sys.exit('already patched')

def one(old, new):
    global s
    n = s.count(old)
    assert n == 1, (n, old[:90])
    s = s.replace(old, new)

one("""  /* Square = same section, round = same class in another section: the rule the desktop uses. */
  const same = friendsInSec(s.id), other = friendsIn(s.code).filter(f => !same.includes(f));
  const all = same.map(f => ['sq', f]).concat(other.map(f => ['ci', f]));
  if (!all.length) return '';
  const shown = all.slice(0, 3).map(([k, f]) => `<span class="g-face ${k}">${pav(f, 15, 6.5)}</span>`).join('');""",
"""  /* Every face is a circle (faces-round-no-term-note (2026-10-08)): friends in your exact section
     first, then the same class in another section. No "sq" class: the app-wide .sq rule would turn
     that face's box into a grid and drop it below the others. */
  const same = friendsInSec(s.id), other = friendsIn(s.code).filter(f => !same.includes(f));
  const all = same.map(f => ['same', f]).concat(other.map(f => ['other', f]));
  if (!all.length) return '';
  const shown = all.slice(0, 3).map(([k, f]) => `<span class="g-face" data-in="${k}">${pav(f, 15, 6.5)}</span>`).join('');""")

one(""".g-face.sq .av{border-radius:4px}
""", """.g-face{display:inline-grid;place-items:center;flex:none;line-height:0}
.g-face .av{border-radius:50%}
""")

one("""
  <div class="muted b" style="font-size:12.5px;padding:12px 16px 0;line-height:1.45">Plans use ${esc(CFG.TERM_LABEL)} sections. Once ${esc(CFG.REGISTRATION_TERM)} is in TermChamp, plan with those. Sections in a plan get seat alerts.</div>`;""", "`;")

f.write_text(s)
print('patched', f)

# 3. The DPR sheet when everything on the report is already in TermChamp (Tate, 2026-10-08: "when i
#    upload my dpr i can't select anything"). Every row was "already logged" / "already in My Classes",
#    so every box was disabled and the button said a greyed-out "Nothing selected", which read as
#    broken. Now it says so plainly, and the button is Done.
s = f.read_text()
old = """  const n = r.rows.filter(x => x.pick && !x.already && !x.skip).length;
  return `<div class="row sb"><h3>Degree Progress Report</h3>"""
new = """  const n = r.rows.filter(x => x.pick && !x.already && !x.skip).length;
  const allIn = r.rows.length > 0 && r.rows.every(x => x.already || x.skip);   /* nothing left to add */
  return `<div class="row sb"><h3>Degree Progress Report</h3>"""
assert s.count(old) == 1; s = s.replace(old, new)
old = """  <button class="btn" style="margin-top:12px" data-a="dprSave" ${n && !UI.busy.dpr ? '' : 'disabled'}>${UI.busy.dpr ? 'Saving…' : n ? `Add ${n} class${n === 1 ? '' : 'es'}` : 'Nothing selected'}</button>`;"""
new = """  ${allIn ? `<div class="tc-dprall b" style="font-size:14px;line-height:1.45;margin-top:12px;padding:10px 12px;border-radius:12px;background:var(--blue-soft)">${r.rows.every(x => x.already) ? 'You’re all caught up. Every class on this report is already in TermChamp.' : 'Nothing new to add from this report.'}</div>
  <button class="btn" style="margin-top:10px" data-a="closeSheet">Done</button>` : `<button class="btn" style="margin-top:12px" data-a="dprSave" ${n && !UI.busy.dpr ? '' : 'disabled'}>${UI.busy.dpr ? 'Saving…' : n ? `Add ${n} class${n === 1 ? '' : 'es'}` : 'Nothing selected'}</button>`}`;"""
assert s.count(old) == 1; s = s.replace(old, new)
f.write_text(s)
print('dpr: all-caught-up state')
