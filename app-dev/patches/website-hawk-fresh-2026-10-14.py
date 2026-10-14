"""Champ's files arrive with the page that needs them (2026-10-14).

After PR #73 went live, Tate still saw the old Hawk button after closing and reopening termchamp.com. Why:
  - sw.js serves '/hawk-ask.js', '/hawk-ask.css' and '/hawk-router.js' CACHE-FIRST (they are in PRECACHE), and it
    never calls skipWaiting(), by design. So until every termchamp.com tab is gone (including a Chrome tab the
    Claude extension keeps open, or an installed app window), the OLD worker stays in charge and keeps serving the
    OLD Hawk files out of its cache, while index.html is network-first and already new.
  - Result: a new page wearing the old assistant, for as long as any old tab lives.
Fix: the page asks for the assistant files with the build in the URL (`hawk-ask.js?v=<build>`). The old worker's
cache-first branch looks the request up with caches.match(req) — the query is part of the key — so it misses and
fetches the new file from the network (and keeps that copy for offline). New builds must bump the `?v=` with the
build stamp (it equals window.PROFESSIFY_BUILD with the space and colon removed); the check asserts they agree.
Nothing in sw.js changes, so nothing about the worker's lifecycle changes.
Run:  python3 <this> <repo>
"""
import sys, re, pathlib
f = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else '.') / 'index.html'; s = f.read_text()
build = re.search(r"window\.PROFESSIFY_BUILD='([^']+)'", s).group(1)
v = re.sub(r'[^0-9]', '', build)
for old, new in [('<link rel="stylesheet" href="hawk-ask.css">', '<link rel="stylesheet" href="hawk-ask.css?v=%s">' % v),
                 ('<script defer src="hawk-router.js"></script>', '<script defer src="hawk-router.js?v=%s"></script>' % v),
                 ('<script defer src="hawk-ask.js"></script>', '<script defer src="hawk-ask.js?v=%s"></script>' % v)]:
    n = s.count(old); assert n == 1, (n, old); s = s.replace(old, new)
f.write_text(s); print('website-hawk-fresh: applied, v=' + v)
