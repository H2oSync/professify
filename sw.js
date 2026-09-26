/* ================================================================================================
   PROFESSIFY SERVICE WORKER
   ------------------------------------------------------------------------------------------------
   Two jobs, and it is worth being precise about which, because the wrong caching strategy here is
   how a static site starts serving last week's app to everybody.

     1. Make the app open with no signal, or on the kind of dorm Wi-Fi that resolves DNS and then
        stalls. Professify is one 2.7 MB HTML file; on a bad connection that is the difference
        between a usable app and a white screen.
     2. Be the thing that can receive a push. On iOS a web push only works once the app is on the
        home screen, and only a service worker can wake for it. The sending half is not built yet
        — see the push handler at the bottom.

   NETWORK FIRST, NOT CACHE FIRST, and that is the whole design. The obvious PWA recipe precaches
   index.html and serves it from cache. For this app that would mean a deploy reaches nobody until
   the service worker happens to update — and stale production is the exact problem this project
   already has, with the live site running an eleven-hour-old build while the work sat undeployed.
   So: always try the network, fall back to cache only when the network actually fails or hangs.
   The cost is one round trip on every launch. The benefit is that what a student sees is what was
   deployed.

   WHAT IS NEVER CACHED. Only same-origin GETs go through this at all. Supabase and PolyRatings are
   left completely alone: seat counts, ratings and messages are live data, and a cached seat count
   is a wrong seat count. This app's first rule is that it never shows a number it cannot stand
   behind, and a stale cache is a quiet way to break that.
   ================================================================================================ */

/* Bumped by the deploy. The build stamp is written in by hand alongside window.PROFESSIFY_BUILD,
   so a new build gets a new cache and the old one is deleted on activate. */
const BUILD = '2026-09-25 15:35';
const SHELL = 'professify-shell-' + BUILD;

/* ================================================================================================
   THE RETIRED ORIGIN — 2026-09-16
   ================================================================================================
   The app moved from professify.app to termchamp.com. professify.app stays assigned to the site as
   a domain alias and 301s everything, and a navigation survives that fine: a navigation request
   carries redirect:"manual", so fetch() hands back an opaqueredirect whose .ok is false, the cache
   write below is skipped, and returning it lets the browser follow the redirect. That part needs no
   help.

   What needs help is what the worker keeps doing AFTERWARDS. It stays installed on the old origin
   with a full copy of the app in its cache, and the moment the network is slow or absent it serves
   that copy — so a student on bad Wi-Fi gets a frozen build of the old app on the old domain and is
   never redirected anywhere. It also holds ~3 MB of cache on their device for a site that no longer
   exists. Neither is an error. Nothing logs. It would simply go on being subtly wrong.

   So on a retired origin this worker does nothing at all: it stops intercepting, drops its caches
   and unregisters itself, which leaves the browser to follow the 301 every time.

   The hosts are listed rather than inferred from "not termchamp.com" on purpose. A rule like that
   would also fire on localhost and on Netlify deploy previews, where the worker is exactly what we
   are trying to test.

   This only reaches a device if the browser can still FETCH this file from the old origin, which
   means /sw.js must answer 200 there rather than 301 — see the two rules in netlify.toml. If that
   is ever not the case the old worker simply stays as it was, which is the behaviour described in
   the first paragraph: redirects work, staleness persists. Degraded, not broken.                */
const RETIRED_HOSTS = ['professify.app', 'www.professify.app'];
const RETIRED = RETIRED_HOSTS.indexOf(self.location.hostname) >= 0;

/* Small, immutable, and needed before the first paint of an installed app. The 2.7 MB document is
   deliberately NOT here: precaching it would download the whole app a second time at install,
   right after the browser has just fetched it. It gets cached opportunistically on the first
   successful navigation instead, which is a request that was going to happen anyway. */
const PRECACHE = [
  '/icon-192.png',
  '/icon-512.png',
  '/icon-maskable-512.png',
  '/apple-touch-icon.png',
  '/manifest.webmanifest',
  '/hawk-router.js',
  '/hawk-ask.js',
  '/hawk-ask.css'
];

self.addEventListener('install', (e) => {
  /* On the retired origin, skipWaiting IS right: the whole point is to replace the worker that is
     still serving a cached copy of the old app, and there is nothing to interrupt. */
  if (RETIRED) { self.skipWaiting(); return; }
  /* addAll fails the whole install if ONE file 404s, which would leave the app with no service
     worker at all over a missing icon. Each is added on its own and a miss is logged. */
  e.waitUntil((async () => {
    const c = await caches.open(SHELL);
    await Promise.all(PRECACHE.map(u =>
      c.add(u).catch(err => console.warn('[sw] precache miss', u, err && err.message))));
  })());
  /* No skipWaiting(). A new worker taking over mid-session can swap the logic under a page that
     is in the middle of something — and because the document is network-first, the CONTENT is
     already fresh on every launch. Only the worker itself lands one launch late, which is the
     right thing to trade for not interrupting somebody writing a review. */
});

self.addEventListener('activate', (e) => {
  if (RETIRED) {
    e.waitUntil((async () => {
      /* Every cache this origin holds, not just this project's prefix — the origin is retired. */
      const keys = await caches.keys();
      await Promise.all(keys.map(k => caches.delete(k)));
      await self.clients.claim();
      /* Last, so the two above are not racing a worker that has already been torn down. */
      await self.registration.unregister();
    })());
    return;
  }
  e.waitUntil((async () => {
    const keys = await caches.keys();
    await Promise.all(keys
      .filter(k => k.startsWith('professify-shell-') && k !== SHELL)
      .map(k => caches.delete(k)));
    /* claim() so the FIRST install controls the page it was registered from. Without it, offline
       does not work until the second launch, which is exactly when a student would have decided
       the app is broken. */
    await self.clients.claim();
  })());
});

/* Give the network a bounded amount of time before falling back. A hung request is worse than a
   failed one: fetch() will sit there for the browser's own timeout — tens of seconds — showing
   nothing, which is the campus-Wi-Fi failure mode this exists for. */
function timed(request, ms) {
  return new Promise((resolve, reject) => {
    const t = setTimeout(() => reject(new Error('sw-timeout')), ms);
    fetch(request).then(r => { clearTimeout(t); resolve(r); },
                        e => { clearTimeout(t); reject(e); });
  });
}

self.addEventListener('fetch', (e) => {
  /* Before anything else. Not responding at all is what lets the 301 happen natively, every time,
     including when the network is slow enough that the branch below would have served the cache. */
  if (RETIRED) return;
  const req = e.request;
  if (req.method !== 'GET') return;

  let url;
  try { url = new URL(req.url); } catch (_) { return; }
  if (url.origin !== self.location.origin) return;   // Supabase, PolyRatings, fonts, CDN: untouched

  /* The document. Network first, 4.5s, then whatever we have. */
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
        const hit = await caches.match('/', { ignoreSearch: true });
        if (hit) return hit;
        /* Nothing cached and no network: say so in a sentence, rather than handing the browser
           its own dinosaur. This is the only HTML this worker ever authors. */
        return new Response(
          '<!doctype html><meta charset="utf-8">' +
          '<meta name="viewport" content="width=device-width,initial-scale=1">' +
          '<title>TermChamp — offline</title>' +
          '<style>html{background:#183178;color:#fff;font:16px/1.5 -apple-system,BlinkMacSystemFont,' +
          '"Segoe UI",sans-serif}body{margin:0;display:grid;place-items:center;min-height:100vh;' +
          'padding:24px;text-align:center}h1{font-size:20px;margin:0 0 8px}p{margin:0;opacity:.8;max-width:34ch}</style>' +
          '<body><div><h1>You’re offline</h1>' +
          '<p>TermChamp needs a connection the first time it loads. Open it once with signal and ' +
          'it will work without one after that.</p></div>',
          { status: 503, headers: { 'Content-Type': 'text/html; charset=utf-8' } });
      }
    })());
    return;
  }

  /* Icons and the manifest: cache first, they do not change within a build. */
  if (PRECACHE.indexOf(url.pathname) >= 0) {
    e.respondWith((async () => {
      const hit = await caches.match(req);
      if (hit) return hit;
      try {
        const fresh = await fetch(req);
        if (fresh && fresh.ok) (await caches.open(SHELL)).put(req, fresh.clone()).catch(() => {});
        return fresh;
      } catch (err) { return new Response('', { status: 504 }); }
    })());
  }
  /* Everything else same-origin falls through to the network untouched. */
});

/* ------------------------------------------------------------------------------------------------
   PUSH. The receiving half only. Nothing sends one yet: that needs a VAPID key pair, a
   push_subscriptions table and an edge function, and none of those exist. It is here now because
   this file is the ONLY place a push can be handled, and adding it later would cost another
   deploy — on iOS, where a push only arrives for an app already on the home screen, the install
   and the worker have to be in place before anything can be sent at all.

   The payload is written by our own edge function, but it arrives as text over the wire, so it is
   parsed defensively and every field has a fallback: a push that throws in here is a push the
   student never sees, and the browser shows its own "This site has been updated in the
   background" notice instead, which is worse than nothing.
   ------------------------------------------------------------------------------------------------ */
self.addEventListener('push', (e) => {
  let d = {};
  try { d = e.data ? e.data.json() : {}; } catch (_) {
    try { d = { body: e.data ? e.data.text() : '' }; } catch (__) { d = {}; }
  }
  const title = String(d.title || 'TermChamp');
  e.waitUntil(self.registration.showNotification(title, {
    body: String(d.body || ''),
    icon: '/icon-192.png',
    badge: '/icon-192.png',
    tag: String(d.tag || 'professify'),      /* same tag replaces, so ten seat changes are one row */
    renotify: !!d.renotify,
    data: { url: typeof d.url === 'string' && d.url.charAt(0) === '/' ? d.url : '/' }
  }));
});

self.addEventListener('notificationclick', (e) => {
  e.notification.close();
  const target = (e.notification.data && e.notification.data.url) || '/';
  e.waitUntil((async () => {
    /* Focus the app if it is already open rather than stacking a second window — on Android a
       fresh openWindow() every time is how you end up with six copies of the app in the switcher. */
    const all = await self.clients.matchAll({ type: 'window', includeUncontrolled: true });
    for (const c of all) {
      if (new URL(c.url).origin === self.location.origin && 'focus' in c) {
        try { await c.navigate(target); } catch (_) {}
        return c.focus();
      }
    }
    if (self.clients.openWindow) return self.clients.openWindow(target);
  })());
});
