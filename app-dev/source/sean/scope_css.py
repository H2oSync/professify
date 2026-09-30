"""Scope Sean's onboarding CSS (written for a shadow root) under .onb for the phone app.
   :host -> .onb, every selector gets a '.onb ' prefix, keyframes get an 'onb-' prefix,
   and his overlay chrome (.stage, .phone, #screen) is dropped: the app's own screen hosts it."""
import re, sys
src = open(sys.argv[1]).read()
src = re.sub(r'/\*.*?\*/', '', src, flags=re.S)
KF = ['shake', 'fill', 'fade', 'up', 'drop']
def blocks(s):
    i, out = 0, []
    while i < len(s):
        j = s.find('{', i)
        if j < 0: break
        head = s[i:j].strip(); depth = 1; k = j + 1
        while depth:
            if s[k] == '{': depth += 1
            elif s[k] == '}': depth -= 1
            k += 1
        out.append((head, s[j + 1:k - 1])); i = k
    return out
DROP = {'.stage', '.phone', '#screen'}
def pre(sel):
    parts = []
    for p in sel.split(','):
        p = p.strip()
        if not p: continue
        if p in DROP or p.startswith('.stage') or p.startswith('.phone') or p.startswith('#screen'): continue
        if p == ':host': parts.append('.onb'); continue
        if p == '*': parts.append('.onb *'); continue
        parts.append('.onb ' + p)
    return ','.join(parts)
def conv(s, inner=False):
    out = []
    for head, body in blocks(s):
        if head.startswith('@keyframes'):
            name = head.split()[1]; out.append('@keyframes onb-' + name + '{' + body + '}'); continue
        if head.startswith('@media') or head.startswith('@container'):
            inner_css = conv(body, True)
            if inner_css: out.append(head + '{' + inner_css + '}')
            continue
        sel = pre(head)
        if not sel: continue
        out.append(sel + '{' + body.strip() + '}')
    return '\n'.join(out)
css = conv(src)
for k in KF: css = re.sub(r'(animation:[^;}]*?)\b' + k + r'\b', r'\1onb-' + k, css)
host = ('.onb{position:relative;height:100%;min-height:100%;display:flex;flex-direction:column;background:var(--bg);color:var(--ink);'
        'font:700 15px/1.45 var(--font);-webkit-font-smoothing:antialiased;text-align:left;letter-spacing:normal;container:phone / size}\n')
print('/* Sean\'s onboarding styles (2026-09-29), scoped under .onb by build/sean/scope_css.py. Do not edit by hand. */\n' + host + css)
