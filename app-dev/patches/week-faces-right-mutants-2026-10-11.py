#!/usr/bin/env python3
"""Mutants for the faces-on-the-right change. Usage: python3 week-faces-right-mutants-2026-10-11.py app-dev/tests/mutate.mjs"""
import sys, json
p = sys.argv[1]; s = open(p, encoding='utf-8').read()
M = [
 ("week faces: tall blocks stack them under the time again", ".g-b.wide:not(.tight){display:grid;grid-template-columns:auto", ".g-b.wide:not(.tight){display:flex;grid-template-columns:auto"),
 ("week faces: tall blocks put them on the left", "padding:2px;justify-self:end;min-width:0;max-width:calc(100% + 3px)", "padding:2px;justify-self:start;min-width:0;max-width:calc(100% + 3px)"),
 ("week faces: tall blocks put them under the code", ".g-b.wide:not(.tight) .g-faces{grid-column:2;grid-row:1/3;", ".g-b.wide:not(.tight) .g-faces{grid-column:1;grid-row:3;"),
 ("week faces: a photo is not clipped round", ".av img{border-radius:inherit}\n", ".av img{border-radius:0}\n"),
 ("week faces: a square face", ".g-face .av{border-radius:50%}", ".g-face .av{border-radius:4px}"),
 ("week faces: the now-pill ignores the faces", ".g-b.wide .g-face,.g-b.wide .g-more,.g-b.wide .g-code", ".g-b.wide .g-code"),
 ("week faces: the now-pill ignores the class code and time", ",.g-b.wide .g-code,.g-b.wide .g-time')", "')"),
 ("week faces: the now-pill stays when nothing is free", "if (!at) { i.style.visibility = 'hidden'; return; }", "if (!at) return;"),
 ("week faces: the now-pill is never parked", "sc.innerHTML = v.body; parkNowPills(sc);", "sc.innerHTML = v.body;"),
 ("week faces: a wider day wraps the +N under the faces", "@container (max-width:179px)", "@container (max-width:149px)"),
 ("week faces: a narrow day loses the face column", "flex-direction:column;flex-wrap:nowrap;align-items:flex-end", "flex-direction:row;flex-wrap:nowrap;align-items:flex-end"),
 ("week faces: the +N is not the true remainder", "${n > kv ? `<span class=\"g-more mv\">+${n - kv}</span>`", "${n > kv ? `<span class=\"g-more mv\">+${n - 3}</span>`"),
]
anchor = '  ["page width: Explore back to 16"'
k = s.index(anchor) if anchor in s else s.index('];\n', s.index('const M = ['))
add = ''.join('  [%s, %s, %s, "weekFaces"],\n' % tuple(json.dumps(x) for x in m) for m in M)
s = s[:k] + add + s[k:]
open(p, 'w', encoding='utf-8').write(s)
