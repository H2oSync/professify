#!/usr/bin/env python3
"""The website wears the phone's identity (Tate, 2026-10-14: an audit of phone vs website screenshots).

1. HEADER LOGO. The phone's TermChamp logo image (TC_LOGO / TC_LOGO_DARK, lifted byte for byte from app/index.html,
   patch logo-image-2026-10-11) replaces the TC tile + typed "TermChamp" in the header's .brand button. Light and dark
   variants by data-theme; 36px tall (32px under 760px). The button keeps its aria-label and click. Only under 340px,
   where the logo would crowd the account pill, does the old TC tile come back.
2. NO-PHOTO AVATARS. A person without a photo is the phone's light grey circle with a white person (--nophoto
   #DADDE3 light / #3A4459 dark, silhouette() from the phone's no-photo-gray patch), in both themes: friends, stories,
   feed cards, friend rows, notifications, faces on calendar blocks and the plan cards, your own account pill. A
   photo that fails to load falls back to the same thing. Photos are untouched; professors keep their rating-tinted
   initials (they never went through avaHtml); the Groups lane colours stay.
3. BUG. #friendsNavBadge, a second blue "1" absolutely positioned over the account pill, is removed. The Friends
   tab's own #friendsNavBadge2 (and the phone-width bar's #mFriendsBadge) are the one badge; updateFriendsBadge()
   already null-guards the missing id.
4. DARK PALETTE. bg #0B1120 -> #0A0F1C, panel #151D2E -> #141B2B, panel-2 #1C2639 -> #1C2539, panel-3 #222D42 ->
   #27314A (the phone's), in both token blocks; the header bar follows the phone's --bar (rgba(20,27,43,.94)).

Usage: python3 website-identity-2026-10-14.py <repo>   (needs <repo>/app/index.html for the logo bytes; never edits it)
"""
import sys, re, pathlib
root = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else '.')
f = root / 'index.html'
s = f.read_text()
if 'website-identity (2026-10-14)' in s:
    sys.exit('already patched')


def one(old, new, n=1):
    global s
    c = s.count(old)
    assert c == n, (c, old[:120])
    s = s.replace(old, new)


# ---------------------------------------------------------------- 1. header logo
phone = (root / 'app' / 'index.html').read_text()
m = re.search(r"const TC_LOGO = '(data:image/png;base64,[A-Za-z0-9+/=]+)', TC_LOGO_DARK = '(data:image/png;base64,[A-Za-z0-9+/=]+)';", phone)
assert m, 'phone TC_LOGO not found'
LIGHT, DARK = m.group(1), m.group(2)

btn = re.search(r'(<button type="button" class="brand" onclick="show\(\'home\'\)" aria-label="TermChamp — go to home">\n)'
                r'(      <img class="brand-tile" src="data:image/png;base64,[A-Za-z0-9+/=]+" alt="" width="128" height="128" decoding="async">)'
                r'<span class="brand-wm" aria-hidden="true">Term<b>Champ</b></span>\n(    </button>)', s)
assert btn and len(re.findall(r'class="brand" onclick', s)) == 1, 'brand button not found exactly once'
logo = ('      <img class="brand-logo lg-l" src="%s" alt="" height="36" draggable="false">'
        '<img class="brand-logo lg-d" src="%s" alt="" height="36" draggable="false">\n' % (LIGHT, DARK))
s = (s[:btn.start()] + btn.group(1)
     + '      <!-- website-identity (2026-10-14): the phone\'s logo image; the TC tile returns only under 340px -->\n'
     + logo + btn.group(2) + '\n' + btn.group(3) + s[btn.end():])

# NOPH_SVG lives in the page's first script: the first-paint account pill runs before the main script parses
NOPH = """<svg class='nophoto' viewBox='0 0 24 24' aria-hidden='true'><circle cx='12' cy='9.2' r='4.4' fill='#fff'/><path d='M3.2 24.5c.6-5.4 4.2-8.6 8.8-8.6s8.2 3.2 8.8 8.6z' fill='#fff'/></svg>"""
one("""</header>
<script>
/* ---- first-paint auth""", """</header>
<script>
/* website-identity (2026-10-14): the phone's silhouette(), as markup; the grey is the tile's --nophoto */
var NOPH_SVG=""" + '"' + NOPH + '"' + """;window.NOPH_SVG=NOPH_SVG;
</script>
<script>
/* ---- first-paint auth""")

# ---------------------------------------------------------------- 3. the duplicate badge
one('''      <span id="friendsNavBadge" class="wl-navbadge" hidden>0</span>
    </div>
    <button id="settingsBtn"''', '''    </div>
    <button id="settingsBtn"''')

# ---------------------------------------------------------------- 4. dark palette (both token blocks)
one('--bg:#0B1120;--panel:#151D2E;--panel-2:#1C2639;--panel-3:#222D42;', '--bg:#0A0F1C;--panel:#141B2B;--panel-2:#1C2539;--panel-3:#27314A;', 2)
# --faint on the lighter panel-3 would read 4.49:1; one step brighter keeps check-desktop-look's 4.5:1 (phone ink4 is #9DA9BB)
one('--muted:#93A0B6;--faint:#8C99B0;', '--muted:#93A0B6;--faint:#8F9CB3;', 2)
one('--fg-rgb:234,240,248;--nav-bg:rgba(15,21,35,.94);', '--fg-rgb:234,240,248;--nav-bg:rgba(20,27,43,.94);', 2)

# ---------------------------------------------------------------- 2. no-photo avatars
one("var AVA_GREY='#CBCBD0';        /* Instagram-light (Tate, 2026-08-25) */",
    "var AVA_GREY='var(--nophoto)';   /* the phone's no-photo grey (2026-10-14); the person on it is NOPH_SVG */")
one('''function avaHtml(url,name,cls){
  var ini=escapeHtml(initials(name||'?'));
  if(url)return '<img class="ava-img'+(cls?' '+cls:'')+'" src="'+escapeHtml(url)+'" alt="" loading="lazy"'
    +' onerror="this.replaceWith(document.createTextNode(\\''+String(ini).replace(/'/g,"")+'\\'))">';
  return ini;
}''', '''/* website-identity (2026-10-14): no photo = the phone's light grey circle with a white person (silhouette() in
   app/index.html). The grey is the tile's background (colorForId() -> var(--nophoto)); the person is NOPH_SVG,
   defined in the first script on the page (the first-paint account pill needs it). */
function avaHtml(url,name,cls){
  if(url)return '<img class="ava-img'+(cls?' '+cls:'')+'" src="'+escapeHtml(url)+'" alt="" loading="lazy"'
    +' onerror="this.outerHTML=NOPH_SVG">';
  return NOPH_SVG;
}''')
one("  return n?escapeHtml(initials(n)):PERSON_GLYPH;\n}", "  return NOPH_SVG;\n}")
# the account pill (two writers) and the header's settings avatar
one('''          +' onerror="this.parentNode.textContent=\\''+iniSafe+'\\'">'
        : iniSafe)+'</span>''', '''          +' onerror="this.parentNode.innerHTML=NOPH_SVG">'
        : NOPH_SVG)+'</span>''')
one('''      ? '<img class="ava-img" src="'+escapeHtml(_av)+'" alt="" onerror="this.parentNode.textContent='
        +JSON.stringify(_ini).replace(/"/g,'&quot;')+'">'
      : _ini)+'</span>''', '''      ? '<img class="ava-img" src="'+escapeHtml(_av)+'" alt="" onerror="this.parentNode.innerHTML=NOPH_SVG">'
      : NOPH_SVG)+'</span>''')
one("av.textContent=(a.handle[0]||'?').toUpperCase(); av.style.display='flex';", "av.innerHTML=NOPH_SVG; av.style.display='flex';")
# the plans module's face, the registration card's face, the plan card's faces, the calendar-block faces
one('''  return '<span class="pl-face" style="background:'+((typeof colorForId==='function')?colorForId(f.id):'#5E7A8A')+'">'+esc(ini)+'</span>';''',
    '''  return '<span class="pl-face" style="background:var(--nophoto)">'+NOPH_SVG+'</span>';''')
one('''    var img = f.avatar_url ? '<img src="' + esc(f.avatar_url) + '" alt="" loading="lazy">' : esc(String(ini).slice(0, 2));
    return '<span class="rg-face" style="background:' + esc(bg) + '" aria-hidden="true">' + img + '</span>';''',
    '''    var img = f.avatar_url ? '<img src="' + esc(f.avatar_url) + '" alt="" loading="lazy" onerror="this.outerHTML=NOPH_SVG">' : NOPH_SVG;
    return '<span class="rg-face" style="background:' + (f.avatar_url ? esc(bg) : 'var(--nophoto)') + '" aria-hidden="true">' + img + '</span>';''')
one('''      var col = has('hmFriendColor') ? hmFriendColor(f) : '#5E7A8A';
      return '<span class="pl2-face" style="background:' + esc(col) + '">' + esc(ini) + '</span>';''',
    '''      return '<span class="pl2-face" style="background:var(--nophoto)">' + (f.avatar_url ? '<img src="' + esc(f.avatar_url) + '" alt="" loading="lazy" onerror="this.outerHTML=NOPH_SVG" style="width:100%;height:100%;object-fit:cover;border-radius:50%;display:block">' : NOPH_SVG) + '</span>';''')
one('''      : esc2(String(p.ini||'?').slice(0,2));
    return '<i class="qw-face'+(p.me?' me':'')+'" style="background:'+esc2(p.bg||'#5E7A8A')+'" title="''', '''      : NOPH_SVG;
    return '<i class="qw-face'+(p.me?' me':'')+'" style="background:'+(p.img?esc2(p.bg||'#5E7A8A'):'var(--nophoto)')+'" title="''')

# the group rows' member stack (Friends): a member's face, not initials
one("""      return '<span class="fr-gav" style="background:'+((f&&f.color)||'#5E7A8A')+'">'
        +escAcc((typeof initials==='function'&&nm2)?initials(nm2):'?')+'</span>';""",
    """      return '<span class="fr-gav" style="background:var(--nophoto)">'
        +((typeof faceHtml==='function'&&f)?faceHtml(f):NOPH_SVG)+'</span>';""")

# the look: --nophoto, the svg, the tile around it, the logo
one('''.brand{gap:10px}
.brand .brand-tile{width:36px;height:36px}
.brand-wm{font-size:24px;font-weight:900;letter-spacing:-.02em;color:var(--navy);line-height:1}
.brand-wm b{font-weight:900;color:var(--tab-on)}
''', '''.brand{gap:10px}
.brand .brand-tile{width:36px;height:36px}
/* website-identity (2026-10-14): the phone's logo image in the header, one variant per theme; the TC tile is the
   fallback for a window too narrow for the logo beside the account pill */
.brand .brand-logo{display:block;height:36px;width:auto;max-width:none;flex:none;user-select:none;-webkit-user-drag:none}
.brand .brand-logo.lg-d{display:none}
:root[data-theme="dark"] .brand .brand-logo.lg-l{display:none}
:root[data-theme="dark"] .brand .brand-logo.lg-d{display:block}
.brand .brand-tile{display:none}
@media (max-width:760px){.brand .brand-logo{height:32px}}
/* 641-700px still carries the five tabs: the logo would push the account pill off the edge, so the tile stays */
@media (min-width:641px) and (max-width:700px){.brand img.brand-logo.lg-l,.brand img.brand-logo.lg-d,:root[data-theme] .brand img.brand-logo.lg-l,:root[data-theme] .brand img.brand-logo.lg-d{display:none}.brand .brand-tile{display:block}}
@media (max-width:340px){.brand img.brand-logo.lg-l,.brand img.brand-logo.lg-d,:root[data-theme] .brand img.brand-logo.lg-l,:root[data-theme] .brand img.brand-logo.lg-d{display:none}.brand .brand-tile{display:block}}
/* the phone's no-photo look: a light grey circle with a white person, both themes */
:root{--nophoto:#DADDE3}
:root[data-theme="dark"]{--nophoto:#3A4459}
svg.nophoto{display:block;width:100%;height:100%}
:root[data-theme="dark"] svg.nophoto circle,:root[data-theme="dark"] svg.nophoto path{opacity:.9}
:root [class]:has(>svg.nophoto){background:var(--nophoto);overflow:hidden}
#view-home .hm-id .fav:has(>svg.nophoto){background:var(--nophoto)}
''')

f.write_text(s)

# the old look suite read the typed wordmark; it now reads the logo image
t = root / 'app-dev' / 'tests' / 'check-desktop-look.mjs'
if t.exists():
    x = t.read_text()
    a = "wm: (document.querySelector('.brand .brand-wm') || {}).textContent,"
    b = "wm: (document.querySelector('.brand .brand-logo') ? 'TermChamp' : ''),"
    if a in x:
        x = x.replace("r.bg === 'rgb(11, 17, 32)' && r.card === 'rgb(21, 29, 46)'", "r.bg === 'rgb(10, 15, 28)' && r.card === 'rgb(20, 27, 43)'", 1)
        x = x.replace("r.on === 'Dark' && r.bg === 'rgb(11, 17, 32)'", "r.on === 'Dark' && r.bg === 'rgb(10, 15, 28)'", 1)
        t.write_text(x.replace(a, b, 1).replace("'the wordmark beside the mark; the button still names the app'",
                                                "'the logo image sits in the header; the button still names the app'", 1))
# the single-term Home test compared #hmFeed byte for byte with the old commit's; the only legitimate difference is now
# the faces, so both sides are read with the no-photo tile normalised (everything else must still match)
t = root / 'app-dev' / 'tests' / 'check-desktop-home.mjs'
if t.exists():
    x = t.read_text()
    a = "const b = await get(tmp), p = await get(repo);"
    n = (a + "\n"
         "  /* website-identity (2026-10-14): a person with no photo is the grey person now, not initials; read both sides alike */\n"
         "  const NF = h => h.replace(/<svg class=\"nophoto\"[\\s\\S]*?<\\/svg>/g, '@@NOPH@@').replace(/background:var\\(--nophoto\\)/g, 'background:#CBCBD0')\n"
         "    .replace(/onerror=\"this\\.(replaceWith\\(document\\.createTextNode\\('[A-Z?]*'\\)\\)|outerHTML=NOPH_SVG)\"/g, 'onerror=\"@@\"')\n"
         "    .replace(/(style=\"background:#CBCBD0\">)[A-Z?]{1,3}(<\\/)/g, '$1@@NOPH@@$2');\n"
         "  b.feed = NF(b.feed); p.feed = NF(p.feed);")
    if a in x and 'const NF = ' not in x:
        t.write_text(x.replace(a, n, 1))
print('website-identity: ok')
