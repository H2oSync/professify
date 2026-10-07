#!/usr/bin/env python3
"""On a phone the app always fills the screen — never the desktop's phone frame (Tate, 2026-10-06: an
iPhone screenshot of Home shrunk into the middle of the screen, the frame and the grey desk around it:
"don't let it do this").

Phone mode used to be decided only by the page's CSS width (@media (max-width:520px)). When a phone's
page is wider than that in CSS pixels — Safari's page zoom (aA → 50%/75%…), Request Desktop Website, a
web view that lays out wider than the screen — the app fell back to the desktop preview: a 402×874 phone
frame centred on the desk colour, i.e. a small app in the middle of the phone.

Now a script in <head>, before the first paint, marks a real phone: a coarse (touch) pointer and a screen
whose short side is ≤ 520px (`screen.*` is the device, whatever the page width). `html.pm` gets every
full-bleed rule the 520px media query has. When the page is wider than the screen (page zoom, desktop
mode), `html.pz` scales the app back up with CSS zoom (`--pz` = page width ÷ screen width, re-measured on
resize and rotation) so it looks the size it is meant to and still fills the screen. Desktops, iPads and
the Desktop phone preview are unchanged.

Usage: python3 phone-full-bleed-2026-10-06.py <repo>
"""
import sys, pathlib
root = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else '.')
f = root / 'app' / 'index.html'
s = f.read_text()
if '/* phone mode by device (2026-10-06)' in s:
    sys.exit('already patched')

def one(old, new):
    global s
    n = s.count(old)
    assert n == 1, (n, old[:90])
    s = s.replace(old, new)

one("""  if (d) document.querySelectorAll('meta[name=theme-color]').forEach(function (m) { m.content = '#0A0F1C'; }); })();</script>
""", """  if (d) document.querySelectorAll('meta[name=theme-color]').forEach(function (m) { m.content = '#0A0F1C'; }); })();</script>
<script>/* phone mode by device (2026-10-06): a touch screen whose short side is a phone's always gets the
   full-screen app, even when the page is wider than 520 CSS px (page zoom, Request Desktop Website);
   then --pz scales it back to the screen's own size */
(function () { try {
  var W = screen.width || 0, H = screen.height || 0, sw = Math.min(W, H), h = document.documentElement;
  if (!(sw && sw <= 520 && ((window.matchMedia && matchMedia('(pointer:coarse)').matches) || navigator.maxTouchPoints > 0))) return;
  h.classList.add('pm');
  var fitPz = function () {
    var dw = innerWidth > innerHeight ? Math.max(W, H) : sw, z = innerWidth > dw * 1.04 ? innerWidth / dw : 1;
    h.style.setProperty('--pz', String(z)); h.classList.toggle('pz', z > 1); window.__pz = z;
  };
  fitPz(); addEventListener('resize', fitPz); addEventListener('orientationchange', fitPz);
} catch (e) {} })();</script>
""")

one("""  .sheet{bottom:max(env(safe-area-inset-bottom),8px)}
  .side{display:none!important}
}
""", """  .sheet{bottom:max(env(safe-area-inset-bottom),8px)}
  .side{display:none!important}
}
/* the same rules, for a phone whose page is wider than 520px (html.pm is set in <head>). :where() keeps
   each one's specificity and place exactly as in the media block above, so a phone looks the same
   either way. */
:root:where(.pm){--sb:max(env(safe-area-inset-top),14px)}
:where(html.pm) .stage{padding:0}
:where(html.pm) .phone-wrap{width:100vw;height:100dvh}
:where(html.pm) .phone{width:100vw;height:100dvh;border-radius:0;transform:none;box-shadow:none}
:where(html.pm),:where(html.pm) body{background:var(--bg)}
html:where(.pm):has(.onb),html:where(.pm):has(.onb) body{background:#F4F6FB}
:where(html.pm) .island,:where(html.pm) .homebar{display:none}
:where(html.pm) .status{padding:0}
:where(html.pm) .status>*{visibility:hidden}
:where(html.pm) .tabbar{padding-bottom:max(env(safe-area-inset-bottom),10px)!important}
:where(html.pm) .composer input,:where(html.pm) .ta,:where(html.pm) .cinput input,:where(html.pm) .search input{font-size:16px}
:where(html.pm) .composer{padding-bottom:max(env(safe-area-inset-bottom),12px)}
:where(html.pm) .blockbar{padding-bottom:max(env(safe-area-inset-bottom),12px)}
:where(html.pm) .bottombar{padding-bottom:max(env(safe-area-inset-bottom),16px)}
:where(html.pm) .sheet{bottom:max(env(safe-area-inset-bottom),8px)}
:where(html.pm) .side{display:none!important}
:where(html.pm.deep),:where(html.pm.deep) body{background:#E7ECF5}
/* html.pz: the page is wider than the phone's screen (page zoom, desktop mode): the app is scaled back
   up with zoom. Inside a zoomed box vw/vh and the safe-area insets count zoomed, so the few rules that
   use them are divided by --pz here. */
html.pz .phone{zoom:var(--pz,1);width:calc(100vw / var(--pz,1));height:calc(100dvh / var(--pz,1))}
html.pz{--sb:max(calc(env(safe-area-inset-top) / var(--pz,1)),14px)}
html.pz .tabbar{padding-bottom:max(calc(env(safe-area-inset-bottom) / var(--pz,1)),10px)!important}
html.pz .at-cta{padding-bottom:max(calc(env(safe-area-inset-bottom) / var(--pz,1)),18px)}
html.pz #chrome.bars-hid .fab{transform:translate(30px,calc(var(--tb) - 14px - env(safe-area-inset-bottom,0px) / var(--pz,1))) rotate(-12deg)}
html.pz .hstar{width:clamp(30px,calc((100vw / var(--pz,1) - 170px) / 5),44px)}
html.pz .onb .majorlist{max-height:calc(46vh / var(--pz,1))!important}
""")
one(":root[data-theme=\"dark\"] .phone{", ":root[data-theme=\"dark\"] .phone{")  # anchor check only

# gestures: a finger's travel is measured in screen px; inside the zoomed app a px is --pz screen px,
# so every pointer coordinate is read through pzNow() (1 everywhere but html.pz)
import re
n0 = s.count('.clientX') + s.count('.clientY')
s, n = re.subn(r'((?:e\.touches\[0\]|e)\.client([XY]))\b', r'(\1 / pzNow())', s)
assert n == n0 and n >= 14, (n, n0)
one("function fit() {", "/* the app's zoom on a phone whose page is wider than its screen (phone-full-bleed, 2026-10-06) */\nfunction pzNow() { return window.__pz || 1; }\nfunction fit() {")
f.write_text(s)
print('patched', f)
