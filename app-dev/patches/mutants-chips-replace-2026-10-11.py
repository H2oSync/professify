import sys
p=sys.argv[1]
s=open(p).read()
assert 'chips: 3 columns' not in s
new = r'''  ["chips: three columns instead of two", ".cchips.cgrid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr))", ".cchips.cgrid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr))", "champChips"],
  ["chips: only three questions", "const chips = `<div class=\"cchips\">${sugg.map(", "const chips = `<div class=\"cchips\">${sugg.slice(0, 3).map(", "champChips"],
  ["chips: the grid is not used on the first sheet", "${chips.replace('class=\"cchips\"', 'class=\"cchips cgrid\"')}", "${chips}", "champChips"],
  ["chips: back to the old 38px / 14px chips", ".cgrid .cchip{white-space:normal;height:auto;min-height:36px;padding:7px 8px;border-radius:18px;font-size:13px", ".cgrid .cchip{white-space:normal;height:auto;min-height:38px;padding:7px 8px;border-radius:18px;font-size:14px", "champChips"],
  ["chips: a personal first chip again", "['cc1', 'When am I free this week?']", "['cc1', 'Open CSC classes after 10am']", "champChips"],
  ["replace: a plan clash can't be replaced", "btn = go(atReplaceLabel(o.clash), 'replace'); }\n  else if (o.P && o.full)", "btn = off('Clashes — can’t add'); }\n  else if (o.P && o.full)", "clashReplace"],
  ["replace: the plan keeps the clashing class", "&& !gone.has(x)).concat(sh.id)", ").concat(sh.id)", "clashReplace"],
  ["replace: My Classes keeps the clashing class", "for (const g of gone) { if (err) break; if (g.only)", "for (const g of []) { if (err) break; if (g.only)", "clashReplace"],
  ["replace: Undo leaves the replaced class out", "for (const g of gone) { if (!e) e = await TC.restoreMyCode(g.code, g.snap, null); }", "", "clashReplace"],
  ["replace: the button doesn't name the class", "`Replace ${esc(codes[0])} with this class`", "`Replace with this class`", "clashReplace"],
  ["replace: a full plan refuses the replace", "(o.full && !rp)", "o.full", "clashReplace"],
  ["replace: a half-done replace has no undo", "if (err && half && undo) toastUndo(", "if (false) toastUndo(", "clashReplace"],
  ["replace: it drops the whole class even when it has other sections", "only: personSecs('me').filter(x => x.code === code).every(x => outs.some(y => y.id === x.id))", "only: true", "clashReplace"],
'''
i=s.index('  ["week faces: tall blocks stack them under the time again"')
s=s[:i]+new+s[i:]
open(p,'w').write(s)
