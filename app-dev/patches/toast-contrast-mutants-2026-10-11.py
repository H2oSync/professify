#!/usr/bin/env python3
"""Mutants for toast-contrast-2026-10-11.py. Usage: python3 toast-contrast-mutants-2026-10-11.py <repo>"""
import sys, pathlib, json
root = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else '.')
f = root / 'app-dev' / 'tests' / 'mutate.mjs'
s = f.read_text()
if '/* toast-contrast (2026-10-11) */' in s:
    sys.exit('already patched')
NEW = [
  ["toast: the text colour as its background again", "background:var(--toast-bg,#0F172A);color:var(--toast-ink,#fff);", "background:var(--ink);color:#fff;", "toastContrast"],
  ["toast: dark mode keeps light-mode colours", ":root[data-theme=\"dark\"]{--toast-bg:#E8EDF5;--toast-ink:#0F172A;--toast-link:#1D4ED8;", ":root[data-theme=\"dark\"]{", "toastContrast"],
  ["toast: dark Undo too light", "--toast-ink:#0F172A;--toast-link:#1D4ED8;", "--toast-ink:#0F172A;--toast-link:#93C5FD;", "toastContrast"],
  ["toast: dark mode on the light sign-up screen", ":root[data-theme=\"dark\"]:has(.onb){--toast-bg:#0F172A;", ":root[data-theme=\"dark\"]:has(.nothing){--toast-bg:#0F172A;", "toastContrast"],
  ["toast: dark pill blends into the page", ":root[data-theme=\"dark\"]{--toast-bg:#E8EDF5;--toast-ink:#0F172A;", ":root[data-theme=\"dark\"]{--toast-bg:#141B2B;--toast-ink:#E8EDF5;", "toastContrast"],
]
i = s.index('const M = ['); j = s.index('\n];\n', i)
s = s[:j + 1] + '  /* toast-contrast (2026-10-11) */\n' + ''.join('  ' + json.dumps(m, ensure_ascii=False) + ',\n' for m in NEW) + s[j + 1:]
f.write_text(s)
print('patched', f)
