#!/usr/bin/env python3
"""Dark mode for the phone app (Tate, 2026-10-05: "lets make a dark mode for the app").

Light mode is unchanged: every colour this patch turns into a token keeps its old value as the token's
light value. Dark mode only redefines the tokens (:root[data-theme="dark"]) and switches the few colours
that are computed in JavaScript (rating text and chips, the empty star, the no-photo grey).

Setting: Settings > Appearance — System (default) / Light / Dark, kept on this phone
(localStorage 'tc-theme'). System follows the phone and changes live when the phone does.
Onboarding and the share pictures stay light (the pictures are images other people see).

Usage: python3 dark-mode-2026-10-05.py <repo>
"""
import re, sys, pathlib

root = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else '.')
f = root / 'app' / 'index.html'
s = f.read_text()
if 'data-theme="dark"' in s or "tc-theme" in s:
    sys.exit('already patched')


def one(old, new, count=1):
    global s
    n = s.count(old)
    assert n == count, (n, old[:120])
    s = s.replace(old, new)


# ---------- 1. the CSS: literal colours -> tokens (light values unchanged) ----------
a = s.index('<style>')
b = s.index('</style>', a)
css = s[a:b]
before = css


def sub(pat, rep, css, want=None):
    new, n = re.subn(pat, rep, css)
    if want is not None:
        assert n == want, (pat, n, want)
    return new


# Onboarding keeps its own light tokens; leave its CSS alone (it starts at the first ".onb{").
oi = css.index('.onb{--desk')
head, onb = css[:oi], css[oi:]
head = sub(r'background:#(?:fff|FFF|FFFFFF)\b', 'background:var(--card)', head)
head = sub(r'(0 0 0 [\d.]+px) #fff\b', r'\1 var(--card)', head)
head = sub(r'color:#B91C1C\b', 'color:var(--red-ink)', head)
head = sub(r'background:#FEE2E2\b', 'background:var(--red-soft)', head)
head = sub(r'background:#FEF2F2\b', 'background:var(--red-soft2)', head)
head = sub(r'background:#CBD5E1\b', 'background:var(--line2)', head)
head = sub(r'background:#E2E8F0\b', 'background:var(--fill2)', head)
head = sub(r'background:#F1F5F9\b', 'background:var(--fill)', head)
head = sub(r'background:#F4F6FB\b', 'background:var(--bg)', head)
head = sub(r'background:#FCE7F3\b', 'background:var(--rose-soft)', head)
head = sub(r'(border(?:-bottom)?:[\d.]+px (?:solid|dashed)) #CBD5E1\b', r'\1 var(--line2)', head)
head = sub(r'(border(?:-bottom)?:[\d.]+px (?:solid|dashed)) #E2E8F0\b', r'\1 var(--fill2)', head)
head = sub(r'(border(?:-bottom)?:[\d.]+px (?:solid|dashed)) #94A3B8\b', r'\1 var(--muted2)', head)
head = sub(r'(border(?:-bottom)?:[\d.]+px (?:solid|dashed)) #64748B\b', r'\1 var(--muted)', head)
head = sub(r'(?<![-\w])color:#64748B\b', 'color:var(--muted)', head)
head = sub(r'(?<![-\w])color:#94A3B8\b', 'color:var(--muted2)', head)
head = sub(r'(?<![-\w])color:#475569\b', 'color:var(--ink4)', head)
head = sub(r'background:var\(--navy\);color:#fff', 'background:var(--navy-fill);color:#fff', head)
head = sub(r'background:rgba\(255,255,255,\.96\)', 'background:var(--bar)', head, 1)
# one-off tints and inks: each gets its own token so light stays byte-for-byte the same colour
ONE_OFF = [  # (hex, properties it is replaced in, token, dark value)
    ('F6F2FF', 'background', '--purple-wash', '#221A3B'),
    ('ECEFF4', 'background', '--dim', '#1F2840'),
    ('A0ABBB', 'color', '--dim-ink', '#56627A'),
    ('E9EDF5', 'background', '--seg', '#1C2539'),
    ('F1F3F7', 'background', '--dim-col', '#161E30'),
    ('EEF2F8', 'background', '--track', '#27314A'),
    ('BFD3FF', 'background', '--blue-mid', '#2C4C8A'),
    ('ECFDF5', 'background', '--ok-soft', '#0D2A22'),
    ('047857', 'color', '--ok-ink', '#4ADE9F'),
    ('99D5CC', 'background', '--teal-mid', '#1F6B62'),
    ('FFE4E6', 'background', '--fav-soft', '#3B1720'),
    ('9F1239', 'color', '--fav-ink', '#FDA4B8'),
    ('FEF3C7', 'background', '--amber-wash', '#33270C'),
    ('78350F', 'color', '--amber-ink2', '#FCD38A'),
    ('DCFCE7', 'background', '--green-wash', '#0F2E1C'),
    ('14532D', 'color', '--green-ink2', '#86EFAC'),
    ('7F1D1D', 'color', '--red-ink2', '#FCA5A5'),
    ('15803D', 'color', '--green-ink3', '#4ADE80'),
    ('9A3412', 'color', '--orange-ink', '#FDBA8C'),
    ('BE185D', 'color', '--rose-ink', '#F9A8D4'),
    ('CC1F6C', 'color', '--pink-text', '#F472B6'),
    ('B45309', 'color', '--seat-low', None),
]
light_tok, dark_tok = [], []
for hx, prop, tok, dk in ONE_OFF:
    head = sub(r'(?<![-\w])(%s):#%s\b' % (prop, hx), r'\1:var(%s)' % tok, head)
    if dk:
        light_tok.append('%s:#%s;' % (tok, hx)); dark_tok.append('%s:%s;' % (tok, dk))
# see-through bars and fades over the page grey
head = sub(r'background:rgba\(244,246,251,\.96\)', 'background:var(--glass)', head, 2)
head = sub(r'background:rgba\(244,246,251,\.95\)', 'background:var(--glass2)', head, 1)
head = sub(r'linear-gradient\(rgba\(244,246,251,0\),', 'linear-gradient(var(--bg0),', head, 2)
head = sub(r'box-shadow:0 0 0 1\.5px rgba\(255,255,255,\.9\)', 'box-shadow:0 0 0 1.5px var(--ring)', head, 1)
light_tok.append('--glass:rgba(244,246,251,.96);--glass2:rgba(244,246,251,.95);--bg0:rgba(244,246,251,0);--ring:rgba(255,255,255,.9);')
dark_tok.append('--glass:rgba(10,15,28,.96);--glass2:rgba(10,15,28,.95);--bg0:rgba(10,15,28,0);--ring:rgba(20,27,43,.9);')
css = head + onb

# the desk behind the phone frame (Desktop preview) and the frame itself
css = sub(r'body\{background:#E9EEF8 radial-gradient\(rgba\(22,51,107,\.09\)', 'body{background:var(--desk) radial-gradient(var(--desk-dot)', css, 1)

# new tokens next to the old ones (light values = the literals they replace)
css = sub(r'(--sb:54px;--tb:86px;\n\})', r'''--ink4:#475569;--line2:#CBD5E1;--fill:#F1F5F9;--fill2:#E2E8F0;--bar:rgba(255,255,255,.96);--navy-fill:#16336B;
  --red-ink:#B91C1C;--red-soft:#FEE2E2;--red-soft2:#FEF2F2;--rose-soft:#FCE7F3;--seat-low:#B45309;--desk:#E9EEF8;--desk-dot:rgba(22,51,107,.09);--nophoto:#DADDE3;--tab-ink:#1D4ED8;
  ''' + ''.join(light_tok) + r'''
  \1''', css, 1)

DARK = '''
/* ---------- dark mode (2026-10-05) ----------
   Only tokens change. Text keeps 4.5:1 on --card and --bg; a soft tint keeps its ink at 4.5:1. */
:root[data-theme="dark"]{color-scheme:dark;
  --ink:#E8EDF5;--ink2:#D5DCE7;--ink3:#B6C1D1;--ink4:#9DA9BB;--muted:#8F9BAE;--muted2:#7E8AA2;--line:#232D42;--line2:#3A4660;
  --bg:#0A0F1C;--card:#141B2B;--fill:#1C2539;--fill2:#27314A;--bar:rgba(20,27,43,.94);--desk:#05080F;--desk-dot:rgba(148,163,184,.08);--nophoto:#3A4459;
  --blue:#2563EB;--blue-t:#6EA2FF;--blue-ink:#A9C6FF;--blue-soft:#172748;--blue-soft2:#1F3562;--navy:#AFC3EE;--navy-fill:#2A4A8F;
  --purple:#7C3AED;--purple-t:#B9A1FF;--purple-soft:#271C45;--purple-ink:#CDBEFF;--amber:#F59E0B;--amber-soft:#33250D;--amber-ink:#FCD38A;
  --teal:#0F766E;--teal-t:#3CC9B8;--teal-soft:#0E2D2B;--pink:#DB2777;--pink-t:#F472B6;--pink-soft:#3A1529;--pink-ink:#F9B4D6;--green:#16A34A;--green-t:#4ADE80;--yellow:#FACC15;
  --red-ink:#FF8A8A;--red-soft:#3B171B;--red-soft2:#3B171B;--rose-soft:#3A1529;--seat-low:#FBBF24;--tab-ink:#A9C6FF;
  ''' + ''.join(dark_tok) + '''}
:root[data-theme="dark"] .dest-mine{--pc-t:#6EA2FF;--pc:#2563EB;--pc-soft:#172748;--pc-soft2:#1F3562;--pc-ink:#A9C6FF;--pc-glow:rgba(59,130,246,.35)}
:root[data-theme="dark"] .plan-A{--pc-t:#3CC9B8;--pc:#0F766E;--pc-soft:#0E2D2B;--pc-soft2:#14403C;--pc-ink:#8FE3D8;--pc-glow:rgba(20,163,148,.35)}
:root[data-theme="dark"] .plan-B{--pc-t:#FB9A5B;--pc:#C2410C;--pc-soft:#35200F;--pc-soft2:#4A2B13;--pc-ink:#FDBA8C;--pc-glow:rgba(234,106,42,.35)}
:root[data-theme="dark"] .plan-C{--pc-t:#F47BA8;--pc:#BE185D;--pc-soft:#3A1529;--pc-soft2:#521D39;--pc-ink:#F9B4D6;--pc-glow:rgba(224,69,126,.35)}
:root[data-theme="dark"] img.nophoto,:root[data-theme="dark"] .nophoto circle,:root[data-theme="dark"] .nophoto path{opacity:.9}
:root[data-theme="light"]{color-scheme:light}
:root[data-theme="dark"] .status.scrolled:not(.dark){box-shadow:0 1px 0 rgba(255,255,255,.08)}
/* sign-up and onboarding keep their light design, so the strip above them stays light too */
:root[data-theme="dark"] .phone:has(.onb){background:#F4F6FB}
:root[data-theme="dark"] .phone:has(.onb) .status{background:#F4F6FB;color:#0F172A}
:root[data-theme="dark"] .phone{box-shadow:0 0 0 1.5px #2A3550,0 0 0 9px #111827,0 0 0 10.5px #2A3550,0 40px 90px rgba(0,0,0,.5)}
/* the theme picker in Settings */
.thm{display:grid;grid-template-columns:repeat(3,1fr);gap:6px;background:var(--fill);border-radius:14px;padding:4px}
.thm button{height:40px;border-radius:11px;font-weight:900;font-size:14px;color:var(--muted);display:flex;align-items:center;justify-content:center;gap:6px}
.thm button.on{background:var(--card);color:var(--ink);box-shadow:0 1px 3px rgba(15,23,42,.14)}
'''
# the dark block goes at the end of @layer app, so it cascades like the rest of the app's CSS
lay = '\n}\n@layer onbreset{'
assert css.count(lay) == 1
css = css.replace(lay, DARK + lay, 1)
# Onboarding and sign-up keep their light design: on .onb every app token is set back to its light
# value (onboarding's own tokens, declared after this, still win), and the dark-only accent text
# tokens point back at the accents.
mroot = re.search(r':root\{\n(.*?)\n\}', css, re.S)
light_root = mroot.group(1).replace('--sb:54px;--tb:86px;', '')
ONB_LIGHT = '/* dark mode: onboarding stays light */\n.onb{' + light_root.strip() + '\n  --blue-t:var(--blue);--pink-t:var(--pink);--purple-t:var(--purple);--teal-t:var(--teal);--green-t:var(--green);--pc-t:var(--pc);color-scheme:light}\n'
css = css.replace('.onb{--desk', ONB_LIGHT + '.onb{--desk', 1)
assert css.count(':root[data-theme="dark"]{') == 1
s = s[:a] + css + s[b:]

# ---------- 2. <head>: the browser's own colours follow the theme ----------
# <meta name=color-scheme> stays "light": the CSS sets color-scheme per theme on <html>, before the first paint
# set the theme before anything paints, so a dark phone never flashes white
one('<style>\n@layer app, onbreset;',
    '''<script>/* theme before first paint (dark mode, 2026-10-05) */
(function () { var t = 'system'; try { t = localStorage.getItem('tc-theme') || 'system'; } catch (e) {}
  var d = t === 'dark' || (t !== 'light' && window.matchMedia && matchMedia('(prefers-color-scheme: dark)').matches);
  document.documentElement.setAttribute('data-theme', d ? 'dark' : 'light');
  if (d) document.querySelectorAll('meta[name=theme-color]').forEach(function (m) { m.content = '#0A0F1C'; }); })();</script>
<style>
@layer app, onbreset;''')

# ---------- 3. colours computed in JavaScript ----------
# text in an accent colour reads the accent's text token, which only dark mode defines
s, n = re.subn(r'(?<![-\w])color:var\(--(blue|pink|purple|teal|green|pc)\)', r'color:var(--\1-t,var(--\1))', s)
assert n >= 60, n
one("const RATE_DARK = s => { const h = RATE_HUE[s]; return s === 10 ? '#166534' : `hsl(${h} 70% ${h < 40 ? 18 : h <= 90 ? 22 : 24}%)`; };",
    "const RATE_DARK = s => { const h = RATE_HUE[s]; if (isDark()) return `hsl(${h} 75% ${h < 40 ? 72 : h <= 90 ? 62 : 58}%)`; return s === 10 ? '#166534' : `hsl(${h} 70% ${h < 40 ? 18 : h <= 90 ? 22 : 24}%)`; };")
one("const RATE_PALE = s => s === 10 ? '#DCFCE7' : `hsl(${RATE_HUE[s]} 85% 90%)`;",
    "const RATE_PALE = s => isDark() ? `hsl(${RATE_HUE[s]} 45% 17%)` : s === 10 ? '#DCFCE7' : `hsl(${RATE_HUE[s]} 85% 90%)`;")
# isDark lives right above the rating scale so everything after can use it
one("const RATE_HUE = [null, 4, 12, 22, 32, 42, 54, 68, 86, 112, 140];",
    "let LIGHT_ONLY = 0;   /* > 0 while a share picture is drawn: those are always light */\nconst isDark = () => !LIGHT_ONLY && document.documentElement.getAttribute('data-theme') === 'dark';\nconst RATE_HUE = [null, 4, 12, 22, 32, 42, 54, 68, 86, 112, 140];")
one("const starCol = v => { const h = halfOf(v); return h ? RATE_BRIGHT(h * 2) : '#E6EAF1'; };",
    "const starCol = v => { const h = halfOf(v); return h ? RATE_BRIGHT(h * 2) : (isDark() ? '#2C3650' : '#E6EAF1'); };")
one("const starAt = (sz, v, k, col, off = '#E6EAF1') =>", "const starAt = (sz, v, k, col, off = isDark() ? '#2C3650' : '#E6EAF1') =>")
one("const NOPHOTO = '#DADDE3';", "const NOPHOTO = 'var(--nophoto)';")
one("if (typeof r !== 'number' || !isFinite(r) || r <= 0) return { bg: '#E6EAF1', ink: '#475569', step: null };",
    "if (typeof r !== 'number' || !isFinite(r) || r <= 0) return isDark() ? { bg: '#27314A', ink: '#9DA9BB', step: null } : { bg: '#E6EAF1', ink: '#475569', step: null };")
one("background:#FCE7F3;color:var(--pink-ink)\">Full</span>", "background:var(--rose-soft);color:var(--pink-ink)\">Full</span>")
one("<span class=\"st\" style=\"background:#FCE7F3;color:var(--pink-ink)\">Needs", "<span class=\"st\" style=\"background:var(--rose-soft);color:var(--pink-ink)\">Needs")
one("style=\"color:${s.seats <= 5 ? '#B45309' : 'var(--teal)'};", "style=\"color:${s.seats <= 5 ? 'var(--seat-low)' : 'var(--teal-t,var(--teal))'};")
one("color:${c.open <= 5 ? 'var(--amber-ink)' : 'var(--teal)'}", "color:${c.open <= 5 ? 'var(--amber-ink)' : 'var(--teal-t,var(--teal))'}")
one('color:#B91C1C" data-a="signOut"', 'color:var(--red-ink)" data-a="signOut"', 2)
one('color:#B91C1C" data-a="removeSec"', 'color:var(--red-ink)" data-a="removeSec"')
one("t.kind === 'class' ? '#D6E4FF' : colorFor(t.id)", "t.kind === 'class' ? 'var(--blue-soft2)' : colorFor(t.id)", 2)
# white on the coloured heroes in both themes, so their ink is pinned to the light value
one('<span class="hchip" style="background:#fff;color:var(--blue-ink)">', '<span class="hchip" style="background:#fff;color:#1E40AF">')
one('<button class="btn" style="background:#fff;color:var(--purple-ink);', '<button class="btn" style="background:#fff;color:#5B21B6;')
one("rc: '#CBD5E1', t:", "rc: isDark() ? '#3A4660' : '#CBD5E1', t:")
one("sc.innerHTML = signinView(); sc.style.paddingTop = ''; sc.style.background = '';",
    "sc.innerHTML = signinView(); sc.style.paddingTop = ''; sc.style.background = ''; document.querySelectorAll('meta[name=theme-color]').forEach(m => { m.content = '#F4F6FB'; });")
one("if (inc) return { c: '#2563EB', t: `In ${inc.code}", "if (inc) return { c: isDark() ? '#6EA2FF' : '#2563EB', t: `In ${inc.code}")
# the tab bar's colours
m = re.search(r"const TABS = \[.*?\];", s)
assert m
tabs = m.group(0)
assert tabs.count("'#1D4ED8', '#E3ECFF'") >= 3, tabs[:200]
s = s.replace(tabs, tabs.replace("'#1D4ED8'", "'var(--tab-ink)'").replace("'#E3ECFF'", "'var(--blue-soft)'"), 1)
# the browser chrome colour on screens that set it
one("document.querySelectorAll('meta[name=theme-color]').forEach(m => { m.content = v.dark ? '#0F172A' : '#F4F6FB'; });",
    "document.querySelectorAll('meta[name=theme-color]').forEach(m => { m.content = v.dark ? '#0F172A' : isDark() && !sc.querySelector('.onb') ? '#0A0F1C' : '#F4F6FB'; });")

one("function cardShCanvas(kind, ref) {\n", "function cardShCanvas(kind, ref) { LIGHT_ONLY++; try { return cardShCanvasLight(kind, ref); } finally { LIGHT_ONLY--; } }\nfunction cardShCanvasLight(kind, ref) {\n")
one("background:#FCE7F3;color:#DB2777;border-radius:14px", "background:var(--rose-soft);color:var(--pink-t,#DB2777);border-radius:14px")

# ---------- 4. the setting ----------
one("SCREENS.settings = () => {",
    """/* Appearance (dark mode, 2026-10-05): System follows the phone; Light / Dark pin it on this phone. */
const THEME_KEY = 'tc-theme';
let themeMem = null;   /* set when this phone refuses to keep the pick (private mode): it then lasts this visit */
const themePref = () => { let t = themeMem; if (t === null) { try { t = localStorage.getItem(THEME_KEY); } catch (e) { t = null; } } return t === 'light' || t === 'dark' ? t : 'system'; };
const themeMQ = window.matchMedia ? matchMedia('(prefers-color-scheme: dark)') : null;
function applyTheme(redraw) {
  const p = themePref(), d = p === 'dark' || (p === 'system' && !!(themeMQ && themeMQ.matches)), was = isDark();
  document.documentElement.setAttribute('data-theme', d ? 'dark' : 'light');
  document.querySelectorAll('meta[name=theme-color]').forEach(m => { m.content = d && !document.querySelector('#scroll .onb') ? '#0A0F1C' : '#F4F6FB'; });
  if (redraw && was !== d) render(true);
}
if (themeMQ) { const fn = () => { if (themePref() === 'system') applyTheme(true); }; themeMQ.addEventListener ? themeMQ.addEventListener('change', fn) : themeMQ.addListener && themeMQ.addListener(fn); }
const themeRow = () => { const p = themePref();
  return `<div class="thm" role="radiogroup" aria-label="Appearance">${[['system', 'System'], ['light', 'Light'], ['dark', 'Dark']].map(([k, l]) => `<button role="radio" aria-checked="${p === k}" class="${p === k ? 'on' : ''}" data-a="setTheme" data-x="${k}">${l}</button>`).join('')}</div><div class="muted b" style="font-size:12.5px;margin-top:8px">${p === 'system' ? 'Follows your phone’s setting.' : 'Kept on this phone.'}</div>`; };
SCREENS.settings = () => {""")
one(" ${sectionCard('Who sees your plans',", " ${sectionCard('Appearance', themeRow())}\n ${sectionCard('Who sees your plans',")

# the action, next to togglePlanShare in the Settings actions
one("  togglePlanShare: async k => {",
    """  setTheme: k => { themeMem = null; try { if (k === 'system') localStorage.removeItem(THEME_KEY); else localStorage.setItem(THEME_KEY, k); } catch (e) { themeMem = k; }
    applyTheme(false); render(true); const b = document.querySelector(`[data-a="setTheme"][data-x="${k}"]`); if (b) b.focus(); },
  togglePlanShare: async k => {""")

f.write_text(s)
print('patched', f)
