#!/usr/bin/env python3
"""The TermChamp logo image in place of the typed wordmark (Tate, 2026-10-11: "can you replace the current one
with this exact", with the navy-Term / blue-Champ logo and its green cap). Edits app/index.html only. Run after
me-strip-2026-10-11.py.

  logo/termchamp-logo-source.png  Tate's file (2168x725, white ground)
  logo/termchamp-logo-light.png   cut from it: cropped to the artwork, white ground made transparent (every
                                  solid colour kept as it is; on white it matches the source to a mean 0.4/255),
                                  144px tall = 3x the 48px of the welcome screen (4x Home's 36px)
  logo/termchamp-logo-dark.png    the same, with the navy "Term" in the dark theme's navy text colour (#AFC3EE,
                                  what the typed wordmark used in dark) — Tate's navy is invisible on #0A0F1C.
                                  Champ, the cap and the tassel are untouched.
  Home's header shows the light one in light mode and the dark one in dark mode. Onboarding's welcome screen
  (always light) shows the light one in place of the typed "TermChamp"; its size is inline, because onboarding's
  reset layer reverts the app's classes.
"""
import base64, pathlib, sys

ROOT = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else '.')
HERE = pathlib.Path(__file__).resolve().parent
P = ROOT / 'app' / 'index.html'
s = P.read_text()
uri = lambda f: 'data:image/png;base64,' + base64.b64encode((HERE / 'logo' / f).read_bytes()).decode()
LIGHT, DARK = uri('termchamp-logo-light.png'), uri('termchamp-logo-dark.png')


def rep(a, b, n=1):
    global s
    c = s.count(a)
    if c != n:
        sys.exit(f'logo-image: expected {n} of {a[:90]!r}, found {c}')
    s = s.replace(a, b)


# the two pictures, once, as constants
rep("""function homeWeekCard(id) {""", f"""/* Tate's logo (2026-10-11), cut from his file; the dark one has "Term" in the dark theme's navy. */
const TC_LOGO = '{LIGHT}', TC_LOGO_DARK = '{DARK}';
const tcLogo = (cls, h) => `<img class="tc-logo-i lg-l ${{cls || ''}}" src="${{TC_LOGO}}" alt="" height="${{h}}" draggable="false"><img class="tc-logo-i lg-d ${{cls || ''}}" src="${{TC_LOGO_DARK}}" alt="" height="${{h}}" draggable="false">`;
function homeWeekCard(id) {{""")

# Home's header
rep("""<h1 class="tc-wordmark" aria-label="TermChamp">Term<span>Champ</span></h1>""",
    """<h1 class="tc-wordmark tc-logo" aria-label="TermChamp">${tcLogo('', 36)}</h1>""")
# onboarding's welcome (always light)
rep("""<div class="wordmark">TermChamp</div>""",
    """<div class="wordmark tc-logo" role="img" aria-label="TermChamp"><img class="tc-logo-i" src="${TC_LOGO}" alt="" height="48" draggable="false" style="display:block;height:48px;width:auto;max-width:100%;margin:0;-webkit-touch-callout:none;pointer-events:none;user-select:none"></div>""")

rep(""".tc-wordmark span{color:var(--blue-t,var(--blue))}""",
    """.tc-wordmark span{color:var(--blue-t,var(--blue))}
.tc-logo{display:flex;align-items:center;line-height:0}
.tc-logo-i{display:block;height:36px;width:auto;max-width:none;flex:none;user-select:none;-webkit-user-drag:none;-webkit-touch-callout:none;pointer-events:none}
.tc-logo .lg-d{display:none}
:root[data-theme="dark"] .homehdr .tc-logo .lg-l{display:none}
:root[data-theme="dark"] .homehdr .tc-logo .lg-d{display:block}""")

P.write_text(s)
print('logo-image-2026-10-11: ok')
