#!/usr/bin/env python3
"""Assemble app/index.html (App 2.0 wired to TermChamp) and the two files it touches at the root.

    python3 build.py STAMP        e.g. python3 build.py "2026-09-28 01:00"

Outputs into ../out/: app/index.html, app/manifest.webmanifest, sw.js, netlify.toml, index.html
(main's index.html with only the PROFESSIFY_BUILD stamp changed, so it matches sw.js).
"""
import os, re, sys, json

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(ROOT, 'out')
STAMP = sys.argv[1] if len(sys.argv) > 1 else '2026-09-28 01:00'

src = open(os.path.join(ROOT, 'app.js')).read().split('\n')
# lines are 1-indexed in the designer file: 2-4 assets, 6-40 helpers
assets = '\n'.join(src[1:4])
helpers = src[5:40]
keep = []
for ln in helpers:
    if ln.startswith('const CLOCK=') or ln.startswith('const HER='):
        continue
    keep.append(ln)
helpers = '\n'.join(keep)
helpers = helpers.replace("const DAYN={M:'Mon',T:'Tue',W:'Wed',R:'Thu',F:'Fri'};", "const DAYN={M:'Mon',T:'Tue',W:'Wed',R:'Thu',F:'Fri',S:'Sat',U:'Sun'};")
helpers = helpers.replace("const DAYL={M:'Monday',T:'Tuesday',W:'Wednesday',R:'Thursday',F:'Friday'};", "const DAYL={M:'Monday',T:'Tuesday',W:'Wednesday',R:'Thursday',F:'Friday',S:'Saturday',U:'Sunday'};")
assert "S:'Sat'" in helpers and "U:'Sunday'" in helpers
assert 'seatBadge' not in helpers and 'CLOCK' not in helpers

core = open(os.path.join(HERE, 'core.js')).read()

# The word filter is NOT hand-copied: it is lifted verbatim out of main's index.html at build time,
# so the phone app refuses exactly the words the desktop (and the database trigger) refuse.
_ix = open(os.path.join(ROOT, 'main', 'index.html')).read()
# Names and reviews use wfHit; usernames use wfHitTight and wfReserved — all three, as on the desktop.
_i = _ix.index('var WF_WORDS=['); _j = _ix.index('\n', _ix.index('function wfReserved(t){') + 30)
_j = _ix.index('}', _ix.index('function wfReserved(t){')) + 1
wordfilter = _ix[_i:_j]
assert 'function wfHit(t){' in wordfilter and 'function wfHitTight(t){' in wordfilter and 'function wfReserved(t){' in wordfilter and "'nigger'" in wordfilter
core = core.replace('/* @@WORDFILTER@@ */', '/* ---- word filter, lifted verbatim from index.html by build.py ---- */\n' + wordfilter)
assert 'function wfHit(t){' in core
# Who can sign up is the desktop's rule, lifted verbatim: SCHOOLS (the three served domains),
# schoolForEmail/eduOk (the same anchored match as school_from_email() in SQL), the 13+ age floor
# and the auth-error wording. The phone app never keeps its own copy of any of them.
import jsextract as X
_sch = X.declaration(_ix, 'const SCHOOLS=')
assert "domain:'calpoly.edu'" in _sch and "domain:'sdsu.edu'" in _sch and "domain:'ucsb.edu'" in _sch
_age = _ix[_ix.index('var AUTH_MIN_AGE='):_ix.index('\n', _ix.index('var AUTH_MIN_AGE='))]
assert _age.strip() == 'var AUTH_MIN_AGE=13;', _age
schools = '\n'.join([_sch, X.function(_ix, 'function schoolForEmail('), X.function(_ix, 'function eduOk('), _age, X.function(_ix, 'function authFriendlyErr(')])
assert core.count('/* @@SCHOOLS@@ */') == 1
core = core.replace('/* @@SCHOOLS@@ */', '/* ---- who can sign up: lifted verbatim from index.html by build.py ---- */\n' + schools)
ui = open(os.path.join(HERE, 'ui.js')).read()
champ = open(os.path.join(HERE, 'champ.js')).read()
me = open(os.path.join(HERE, 'me.js')).read()
signup = open(os.path.join(HERE, 'onboard.js')).read()   # Sean's onboarding, wired (was signup.js)
_a = _ix.index('var EP_MAX=512'); _b = X_match_end = None
import jsextract as X
_fn = X.function(_ix, 'function epEncodeSquare(')
avatar = _ix[_a:_ix.index('\n', _a)] + '\n' + _fn
assert 'toBlob' in avatar
me = me.replace('/* @@AVATAR@@ */', avatar)
import subprocess
# Sean's onboarding CSS, exactly as he wrote it, scoped under .onb at build time.
onbcss = subprocess.run([sys.executable, os.path.join(HERE, 'sean', 'scope_css.py'), os.path.join(HERE, 'sean', 'sean-onboarding.css')], capture_output=True, text=True, check=True).stdout
assert '.onb .btn{' in onbcss and '.onb .code6' in onbcss
# The app's CSS goes in a cascade layer, and a reset layer above it returns every element inside
# .onb to the browser's defaults before Sean's (unlayered) rules apply — so class names the two
# share (.btn, .card, .dot, .li, .top …) can't leak the app's look into his screens. SVG is left
# alone: its fill/stroke attributes are presentational hints, which a revert would drop.
css = ('@layer app, onbreset;\n@layer app{\n' + open(os.path.join(ROOT, 'app.css')).read() + open(os.path.join(HERE, 'extra.css')).read()
       + '\n}\n@layer onbreset{.onb *:not(svg):not(svg *){all:revert}}\n' + onbcss)
skel = open(os.path.join(HERE, 'skeleton.html')).read()

js = f"""
window.TERMCHAMP_APP_BUILD = '{STAMP}';
/* ================================================================================================
   TERMCHAMP — THE PHONE APP (termchamp.com/app)
   ------------------------------------------------------------------------------------------------
   App 2.0's design (Tate's, 2026-09) with TermChamp's real backend underneath. One file, like the
   desktop index.html: edit it, upload it to app/index.html, and Netlify publishes it at /app/.
   Order in this script: the designer's images and small helpers, then THE BACKEND (every read
   and write), then THE SCREENS, then Champ, actions and rendering.
   ================================================================================================ */
{assets}

/* ================= helpers (the designer's) ================= */
{helpers}

{core}

{ui}

{champ}

{me}

{signup}
"""

head = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>TermChamp</title>
<meta name="description" content="Your Cal Poly classes, real professor ratings, live seats and your friends' weeks.">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="default">
<meta name="apple-mobile-web-app-title" content="TermChamp">
<meta name="theme-color" content="#F4F6FB">
<link rel="apple-touch-icon" href="/apple-touch-icon.png">
<link rel="icon" href="/icon-192.png">
<link rel="manifest" href="/app/manifest.webmanifest">
<!-- The same pinned supabase-js the desktop loads (see the note in index.html for how the hash
     was checked). It is deferred, so the app boots on DOMContentLoaded, after it has run. -->
<script defer
        src="https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2.112.4/dist/umd/supabase.js"
        integrity="sha256-+M5/q3ma8ZFgGcvQtIWzm7gNvbxtwGKQmnUcnlGY4Ew="
        crossorigin="anonymous"
        onerror="window.__sbScriptFailed=1"></script>
<style>
{css}
</style>
</head>
<body>
"""
for _t in ['Explains concepts clearly', 'Gave timely, useful feedback', 'Ran engaging discussions', 'Graded fairly &amp; transparently',
           'Helpful in office hours', 'Explained exam results well', 'Approachable & responsive', 'Used real-world examples', 'Made expectations clear', 'Genuinely cares about students']:
    assert _t in _ix, 'rate tag no longer on the desktop: ' + _t
html = head + skel + "\n<script>\n" + js + "\n</script>\n</body>\n</html>\n"
os.makedirs(os.path.join(OUT, 'app'), exist_ok=True)
open(os.path.join(OUT, 'app', 'index.html'), 'w').write(html)

# ---- app/planner.js: the desktop's degree data and rules, lifted verbatim ----
import jsextract as X
def near(src, head, after):
    i = src.index(head, src.index(after))
    j = src.index('{', i)
    return src[i:X._match(src, j) + 1]
L = []
_a = _ix.index('const COURSE_EQUIV_SEED ='); _b = _ix.index('\n', _ix.index('function coursePrereqs(code){'))
L.append(_ix[_a:_b])
for f in ['function enrolledNowCodes(', 'function prereqStatus(', 'function completedCodes(']:
    L.append(X.function(_ix, f))
L.append('buildEquivIndex(); buildPrereqIndex();')
L.append(X.declaration(_ix, 'var WAIVE_REASONS='))
L.append(X.function(_ix, 'function waiveReasonLabel('))
for d in ['const GE_COURSES=', 'const MAJOR_CATALOG=', 'var CONC_CATALOG=', 'var CONC_REQS=']:
    L.append(X.declaration(_ix, d))
L.append(X.function(_ix, 'function concInfo('))
_a = _ix.index('window.SCHED_MAJORS={"'); L.append(_ix[_a:_ix.index('\n', _a)])
# 2026-10-06: majors written as their own lines after it (ITP, Physics BA) come along too
_a = _ix.index("window.SCHED_MAJORS['ocob-itp']="); L.append(_ix[_a:_ix.index('\n', _ix.index("window.SCHED_MAJORS['m-physicsba']="))])
_a = _ix.index('window.schSlotCodes=function(raw){'); L.append(_ix[_a:X._match(_ix, _ix.index('{', _a)) + 1] + ';')
L.append(X.function(_ix, 'function schConcClasses('))
L.append(X.function(_ix, 'function schExpandConc('))
PB = 'MY PLANNER · WHAT YOU CAN TAKE — 2026-09-03'
for f in ['function canon(c){', 'function slotCodes(s){', 'function geAreaOf(', 'function slotAreaKey(']:
    L.append(near(_ix, f, PB))
L.append('var _subjCache=null;')
for f in ['function knownSubjects(', 'function electiveRule(', 'function uncodedSatisfied(', 'function slotCheckable(']:
    L.append(near(_ix, f, PB))
for v in ["var LEGAL_UPDATED='", "var LEGAL_UPDATED_PRIVACY='", "var LEGAL_CONTACT='"]:
    _a = _ix.index(v); L.append(_ix[_a:_ix.index('\n', _a)])
L.append(X.declaration(_ix, 'var LEGAL_DOCS='))
# The Degree Progress Report reader and the PDF text join, exactly as the desktop runs them.
for f in ['function pdfItemsToText(', 'function fileBytes(']:
    L.append(X.function(_ix, f))
for v in ['var DPR_GRADE=', 'var DPR_TERM=', 'var DPR_NOISE=', 'var DPR_ROW=', "const ABROAD_MARK="]:
    _a = _ix.index(v); L.append(_ix[_a:_ix.index('\n', _a)])
for f in ['function dprLooksLikeOne(', 'function dprScrub(', 'function dprCrosswalk(', 'function dprProgram(', 'function dprParse(']:
    L.append(X.function(_ix, f))
_a = _ix.index("var PDFJS_BASE='"); L.append(_ix[_a:_ix.index('\n', _a)])
psrc = open(os.path.join(HERE, 'planner-src.js')).read()
psrc = psrc.replace('  /* @@LIFTED:BEGIN */\n  /* @@LIFTED:END */', '  /* @@LIFTED:BEGIN */\n' + '\n'.join(L) + '\n  /* @@LIFTED:END */')
assert 'function uncodedSatisfied(' in psrc and 'window.SCHED_MAJORS=' in psrc
open(os.path.join(OUT, 'app', 'planner.js'), 'w').write('window.TERMCHAMP_PLANNER_BUILD = ' + json.dumps(STAMP) + ';\n' + psrc)

manifest = {
    "name": "TermChamp", "short_name": "TermChamp",
    "description": "Your Cal Poly classes, real professor ratings, live seats and your friends' weeks.",
    "id": "/app/", "start_url": "/app/", "scope": "/app/", "display": "standalone",
    "orientation": "portrait", "background_color": "#F4F6FB", "theme_color": "#F4F6FB", "lang": "en-US",
    "icons": [
        {"src": "/icon-192.png", "sizes": "192x192", "type": "image/png", "purpose": "any"},
        {"src": "/icon-512.png", "sizes": "512x512", "type": "image/png", "purpose": "any"},
        {"src": "/icon-maskable-512.png", "sizes": "512x512", "type": "image/png", "purpose": "maskable"}]}
open(os.path.join(OUT, 'app', 'manifest.webmanifest'), 'w').write(json.dumps(manifest, indent=2) + '\n')

# ---- sw.js: one cached copy per app, not one for the whole site ----
sw = open(os.path.join(ROOT, 'main', 'sw.js')).read()
old_build = re.search(r"const BUILD = '([^']*)';", sw).group(1)
sw = sw.replace(f"const BUILD = '{old_build}';", f"const BUILD = '{STAMP}';", 1)
a = """  /* The document. Network first, 4.5s, then whatever we have. */
  if (req.mode === 'navigate') {
    e.respondWith((async () => {
      try {
        const fresh = await timed(req, 4500);
        if (fresh && fresh.ok) {
          const c = await caches.open(SHELL);
          c.put('/', fresh.clone()).catch(() => {});   // key on '/' so ?tab=… all share one copy
        }
        return fresh;
      } catch (_) {
        const hit = await caches.match('/', { ignoreSearch: true });"""
b = """  /* The document. Network first, 4.5s, then whatever we have.
     TWO DOCUMENTS, TWO KEYS — 2026-09-28. The phone app lives at /app/ on the same origin, under
     this same worker. With one '/' key, opening /app/ overwrote the desktop's offline copy with the
     phone app and the other way round, so going offline showed whichever was opened last. Each
     now keeps its own copy; everything else still shares '/' (so ?tab=… is still one copy). */
  if (req.mode === 'navigate') {
    const docKey = (url.pathname === '/app' || url.pathname.indexOf('/app/') === 0) ? '/app/' : '/';
    e.respondWith((async () => {
      try {
        const fresh = await timed(req, 4500);
        if (fresh && fresh.ok) {
          const c = await caches.open(SHELL);
          c.put(docKey, fresh.clone()).catch(() => {});
        }
        return fresh;
      } catch (_) {
        const hit = await caches.match(docKey, { ignoreSearch: true });"""
if 'docKey' not in sw:          # main before PR 1; after it, main already carries the fix
    assert sw.count(a) == 1
    sw = sw.replace(a, b)
open(os.path.join(OUT, 'sw.js'), 'w').write(sw)

# ---- index.html: only the build stamp, so it matches sw.js ----
ix = open(os.path.join(ROOT, 'main', 'index.html')).read()
n = ix.count(f"PROFESSIFY_BUILD='{old_build}'")
assert n == 1, n
ix = ix.replace(f"PROFESSIFY_BUILD='{old_build}'", f"PROFESSIFY_BUILD='{STAMP}'")
open(os.path.join(OUT, 'index.html'), 'w').write(ix)

# ---- netlify.toml: publish app/ (index.html, planner.js, manifest) ----
nt = open(os.path.join(ROOT, 'main', 'netlify.toml')).read()
APP_BLOCK = """# App 2.0, the phone app — its own folder, published at /app/ (2026-09-28). Missing is not fatal:
# the desktop site does not depend on it.
if [ -f app/index.html ]; then
  mkdir -p public/app
  for f in index.html planner.js manifest.webmanifest; do
    if [ -f "app/$f" ]; then cp "app/$f" public/app/; echo "published  app/$f"
    else echo "MISSING    app/$f"; fi
  done
else
  echo "MISSING    app/index.html  (the phone app at /app/ will 404)"
fi
"""
anchor = 'echo "--- not published (present in the repo root, deliberately not served) ---"'
if '# App 2.0, the phone app' in nt:
    i0 = nt.index('# App 2.0, the phone app'); i1 = nt.index(anchor)
    nt = nt[:i0] + APP_BLOCK + nt[i1:]
else:
    assert nt.count(anchor) == 1
    nt = nt.replace(anchor, APP_BLOCK + anchor)
if ' app " in' not in nt:
    a = 'case " $REQUIRED $OPTIONAL public netlify netlify.toml " in'
    assert nt.count(a) == 1
    nt = nt.replace(a, 'case " $REQUIRED $OPTIONAL public netlify netlify.toml app " in')
if 'for = "/app/*"' not in nt:
    a = '[[headers]]\n  for = "/sw.js"'
    assert nt.count(a) == 1
    nt = nt.replace(a, """[[headers]]
  for = "/app/*"
  [headers.values]
    Cache-Control = "public, max-age=0, must-revalidate"
[[headers]]
  for = "/app/manifest.webmanifest"
  [headers.values]
    Content-Type = "application/manifest+json; charset=utf-8"
""" + a)
open(os.path.join(OUT, 'netlify.toml'), 'w').write(nt)
print('built', STAMP, len(html), 'bytes', '(sw was', old_build + ')')
