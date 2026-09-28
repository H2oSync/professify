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
_i = _ix.index('var WF_WORDS=['); _j = _ix.index('function wfHitTight(t){')
wordfilter = _ix[_i:_j]
_k = wordfilter.index('var WF_TIGHT=['); _l = wordfilter.index('function wfLeet(t){')
wordfilter = wordfilter[:_k] + wordfilter[_l:]          # drop the username-only lists
assert 'function wfHit(t){' in wordfilter and "'nigger'" in wordfilter and 'WF_TIGHT' not in wordfilter
core = core.replace('/* @@WORDFILTER@@ */', '/* ---- word filter, lifted verbatim from index.html by build.py ---- */\n' + wordfilter)
assert 'function wfHit(t){' in core
ui = open(os.path.join(HERE, 'ui.js')).read()
champ = open(os.path.join(HERE, 'champ.js')).read()
css = open(os.path.join(ROOT, 'app.css')).read() + open(os.path.join(HERE, 'extra.css')).read()
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
html = head + skel + "\n<script>\n" + js + "\n</script>\n</body>\n</html>\n"
os.makedirs(os.path.join(OUT, 'app'), exist_ok=True)
open(os.path.join(OUT, 'app', 'index.html'), 'w').write(html)

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
assert sw.count(a) == 1
sw = sw.replace(a, b)
open(os.path.join(OUT, 'sw.js'), 'w').write(sw)

# ---- index.html: only the build stamp, so it matches sw.js ----
ix = open(os.path.join(ROOT, 'main', 'index.html')).read()
n = ix.count(f"PROFESSIFY_BUILD='{old_build}'")
assert n == 1, n
ix = ix.replace(f"PROFESSIFY_BUILD='{old_build}'", f"PROFESSIFY_BUILD='{STAMP}'")
open(os.path.join(OUT, 'index.html'), 'w').write(ix)

# ---- netlify.toml: publish app/ ----
nt = open(os.path.join(ROOT, 'main', 'netlify.toml')).read()
a = 'echo "--- not published (present in the repo root, deliberately not served) ---"'
assert nt.count(a) == 1
b = '''# App 2.0, the phone app — its own folder, published at /app/ (2026-09-28). Missing is not fatal:
# the desktop site does not depend on it.
if [ -f app/index.html ]; then
  mkdir -p public/app
  cp app/index.html public/app/
  echo "published  app/index.html"
  if [ -f app/manifest.webmanifest ]; then
    cp app/manifest.webmanifest public/app/
    echo "published  app/manifest.webmanifest"
  fi
else
  echo "MISSING    app/index.html  (the phone app at /app/ will 404)"
fi
''' + a
nt = nt.replace(a, b)
a = 'case " $REQUIRED $OPTIONAL public netlify netlify.toml " in'
assert nt.count(a) == 1
nt = nt.replace(a, 'case " $REQUIRED $OPTIONAL public netlify netlify.toml app " in')
a = '''[[headers]]
  for = "/sw.js"'''
assert nt.count(a) == 1
nt = nt.replace(a, '''[[headers]]
  for = "/app/*"
  [headers.values]
    Cache-Control = "public, max-age=0, must-revalidate"
[[headers]]
  for = "/app/manifest.webmanifest"
  [headers.values]
    Content-Type = "application/manifest+json; charset=utf-8"
''' + a)
open(os.path.join(OUT, 'netlify.toml'), 'w').write(nt)
print('built', STAMP, len(html), 'bytes', '(sw was', old_build + ')')
