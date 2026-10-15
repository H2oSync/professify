/* check-desktop-security-pass2 — security-pass2 (2026-10-15), run on the REAL index.html in Chromium with the real
   supabase-js against the PostgREST stand-in of app-harness.
   reviews  1. Home's "latest reviews" reads the public VIEW reviews_public (what a signed-out visitor may read), never the table
   signout  2. Signing out removes every professify / tc- / tc_ key from localStorage AND sessionStorage, keeps the device
               preferences, empties the in-memory lists, and signs out on the server
   push     2. ... and turns off web push first (bounded, so a hung push service cannot hold the sign-out)
   newuser  2. A different account than the last one on this browser starts clean: the last account's classes are never
               uploaded into it (at page load, and when it signs in on a page the last account left open)
   delete   3. Account deletion and the recovery sheet's "Sign out" wipe tc- and tc_ keys too
   avatars  4. Only this project's public avatars bucket is ever drawn or fetched; every avatar <img> is no-referrer
   escape   5. escapeHtml / escAcc escape '; an apostrophe in an email cannot break the code step's handler
   poly     5. A hostile PolyRatings payload (quotes, <img onerror>, entity-encoded script) runs nothing and breaks out of nothing
   cookie   6. The session fallback cookie is Secure, SameSite=Strict, path=/, 7 days
   evname   8. Analytics names a click by data-ev / id / tag, never by its text, aria-label or value
   Run: APP_DIR=<repo> node check-desktop-security-pass2.mjs [--only reviews|signout|push|newuser|delete|avatars|sites|escape|poly|cookie|evname] [--quiet]
   (APP_PORT to move off 8190) */
import { openApp } from './app-harness.mjs';
import * as FX from './app-fixtures.mjs';
import * as acorn from '/opt/npm-tools/node_modules/acorn/dist/acorn.mjs';

const args = process.argv.slice(2);
const ONLY = args.includes('--only') ? args[args.indexOf('--only') + 1] : null;
const QUIET = args.includes('--quiet');
const want = n => !ONLY || ONLY === n;
let pass = 0, fail = 0;
const ok = (c, name, info) => { if (c) { pass++; if (!QUIET) console.log('  ok  ', name); } else { fail++; console.log('  FAIL', name, info !== undefined ? '→ ' + JSON.stringify(info).slice(0, 500) : ''); } };
const tick = async (p, ms = 500) => { await p.clock.runFor(ms); await p.waitForTimeout(250); };
const desk = (o = {}) => openApp(Object.assign({ path: '/', width: 1440, height: 900, wait: 4000 }, o));
const ME = FX.ME;
const A_UID = 'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa';          // "student A", who used this browser before

/* ------------------------------------------------------------------ 1. the Home strip reads the view */
if (want('reviews')) {
  for (const signedIn of [false, true]) {
    const { page, close, log } = await desk({ signedIn });
    await tick(page, 2500);
    const rs = log.reads.filter(r => /^reviews(_public)?\?/.test(r));
    ok(rs.some(r => /^reviews_public\?select=professor_key(%2C|,)professor_name(%2C|,)department(%2C|,)course/.test(r) && /limit=24/.test(r)), (signedIn ? 'signed in' : 'signed out') + ': the latest-reviews strip reads reviews_public', log.reads.filter(r => /review/.test(r)));
    ok(!rs.some(r => /^reviews\?/.test(r)), (signedIn ? 'signed in' : 'signed out') + ': and never the reviews table for the public list', rs);
    ok(log.errors.length === 0, 'no page errors (reviews)', log.errors);
    await close();
  }
}

/* keys a person leaves behind (a sample of every family the site writes) and the device preferences that must stay */
const SEED = ({ id }) => {
  const L = {
    ['professify_my_classes']: '["BUS 3438","MATH 9999"]', ['professify_my_class_meta']: '{}', ['professify_mc_pending']: '{"MATH 9999":{"op":"add","at":1}}',
    ['professify_mc_adopted_' + id]: '1', ['professify_friends_cache_' + id + ':2268']: '{"x":1}', ['tc-audit:' + id]: '{"requirements":[]}',
    ['professify_commits_' + id]: '[]', ['professify_commits_pending_' + id]: '{}', ['professify_regday_' + id]: '{}', ['professify_watch']: '["pr_p1"]',
    ['professify_watch_classes']: '["BUS 3438"]', ['professify_watch_meta']: '{}', ['professify_groups']: '[{"id":"g1","name":"Secret group","members":[]}]',
    ['professify_rate_draft']: '{"text":"private draft"}', ['professify_appt_2268']: '2026-11-01', ['professify_friend_secs']: '{}', ['professify_profile_cache']: '{"id":"' + id + '","display_name":"Jordan"}',
    ['professify_avatar_' + id]: '{"url":"u","data":"data:image/png;base64,AAAA"}', ['professify-profile']: '{"major":"X"}', ['professify_plans_2268_' + id]: '[]',
    ['tc_champ_ai:' + id]: '1', ['tc-mc-term-view']: 'now', ['tc_custom']: '1', ['tc-custom']: '1', ['professify_notif_seen']: '2026-10-01',
    /* device preferences and public caches: these stay */
    ['professify-theme']: 'dark', ['professify_ev_salt']: 'abc123', ['professify_visits']: '3', ['professify_install_snooze']: '9', ['professify_ratesound']: '1',
    ['professify_prof_cache']: '{"ts":1,"list":[]}', ['professify_course_short']: '{"ts":1,"map":{}}', ['professify_seats_cache:2268']: '{}',
    ['hawk-pos']: '{"x":1}', ['unrelated-key']: 'mine',
  };
  for (const k in L) localStorage.setItem(k, L[k]);
  sessionStorage.setItem('professify_classmate_events', '[1]'); sessionStorage.setItem('tc_session_thing', '1'); sessionStorage.setItem('professify_pending_add', '44444444-4444-4444-8444-444444444444'); sessionStorage.setItem('other', 'x');
};
const STAY = ['professify-theme', 'professify_ev_salt', 'professify_visits', 'professify_install_snooze', 'professify_ratesound', 'professify_prof_cache', 'professify_course_short', 'professify_seats_cache:2268', 'hawk-pos', 'unrelated-key'];
const PERSONAL = k => /^(professify|tc-|tc_)/.test(k);
const snapStore = page => page.evaluate(() => ({ l: Object.keys(localStorage), s: Object.keys(sessionStorage), last: localStorage.getItem('professify_last_uid') }));

/* ------------------------------------------------------------------ 2. sign-out wipes this browser */
if (want('signout')) {
  const { page, close, log } = await desk();
  await tick(page, 1500);
  await page.evaluate(SEED, { id: ME.id });
  await page.evaluate(() => { myClasses.push('MATH 9999'); watchlist.push('pr_p1'); });
  const before = await snapStore(page);
  ok(before.l.includes('professify_my_classes') && before.l.includes('tc-audit:' + ME.id) && before.s.includes('tc_session_thing'), 'set-up: the person-keys exist before sign-out', before);
  ok(before.last === ME.id, 'the browser remembers who is signed in (professify_last_uid)', before.last);
  await page.evaluate(() => authSignOut()); await tick(page, 600);
  const after = await snapStore(page);
  const left = after.l.filter(PERSONAL).filter(k => !STAY.includes(k) && k !== 'professify_last_uid');
  ok(left.length === 0, 'after sign-out no professify / tc- / tc_ key of the person is left in localStorage', left);
  ok(after.s.filter(PERSONAL).length === 0, 'after sign-out sessionStorage has no professify / tc_ key (invite stash included)', after.s);
  ok(STAY.every(k => after.l.includes(k)), 'the device preferences and public caches stay (theme, analytics pseudonym, install counters, sound, PolyRatings / catalog / seat caches, an unrelated key)', STAY.filter(k => !after.l.includes(k)));
  ok(after.s.includes('other'), 'a sessionStorage key that is not ours is untouched');
  ok(!after.l.some(k => /^sb-.*-auth-token$/.test(k)), 'the session itself is gone too', after.l);
  ok(after.last === ME.id, 'the last user id is kept (it is how the next, different account is recognised)', after.last);
  const mem = await page.evaluate(() => ({ mc: myClasses.length, wl: watchlist.length, gp: gpList.length, pend: Object.keys(mcPending).length, signedOut: !sbUser }));
  ok(mem.mc === 0 && mem.wl === 0 && mem.gp === 0 && mem.pend === 0 && mem.signedOut, 'the page\'s own copies of My Classes, watchlist, groups and the pending queue are empty', mem);
  ok(log.writes.some(w => /^auth:logout/.test(w.table)), 'the server is told (logout)', log.writes.map(w => w.table));
  /* the next sign-in on this very page cannot upload what was there */
  ok(!log.writes.some(w => w.table === 'saved_classes' && JSON.stringify(w.body || '').includes('MATH 9999')), 'nothing of the old account was written anywhere on the way out');
  ok(log.errors.length === 0, 'no page errors (sign-out)', log.errors);
  await close();
}

/* ------------------------------------------------------------------ 2. sign-out turns off web push */
if (want('push')) {
  const GRANT = () => { try { Object.defineProperty(Notification, 'permission', { get: () => 'granted', configurable: true }); } catch (e) {} };
  /* subscribed + granted: pushDisable runs, before the session goes */
  {
    const { page, close } = await desk();
    await tick(page, 1200);
    const supported = await page.evaluate(() => pushSupported());
    ok(supported, 'set-up: this browser reports web push as supported');
    await page.evaluate(GRANT);
    await page.evaluate(() => { window.__pd = 0; window.__signedAtPd = null; window.pushDisable = async () => { window.__pd++; window.__signedAtPd = !!sbUser; return { ok: true }; }; });
    await page.evaluate(() => authSignOut()); await tick(page, 300);
    const r = await page.evaluate(() => ({ pd: window.__pd, signedAtPd: window.__signedAtPd, out: !sbUser }));
    ok(r.pd === 1 && r.signedAtPd === true && r.out, 'sign-out with notifications granted calls pushDisable once, while the session still exists, then signs out', r);
    await close();
  }
  /* never asked: nothing to turn off */
  {
    const { page, close } = await desk();
    await tick(page, 1200);
    await page.evaluate(() => { window.__pd = 0; window.pushDisable = async () => { window.__pd++; }; });
    await page.evaluate(() => authSignOut()); await tick(page, 300);
    ok((await page.evaluate(() => window.__pd)) === 0, 'sign-out with notifications never granted does not touch push');
    await close();
  }
  /* a push service that never answers does not hold the sign-out */
  {
    const { page, close } = await desk();
    await tick(page, 1200);
    await page.evaluate(GRANT);
    await page.evaluate(() => { window.__done = false; window.pushDisable = () => new Promise(() => {}); authSignOut().then(() => { window.__done = true; }); });
    await tick(page, 2600);
    const r = await page.evaluate(() => ({ done: window.__done, out: !sbUser, keys: Object.keys(localStorage).filter(k => /^sb-.*-auth-token$/.test(k)).length }));
    ok(r.done && r.out && r.keys === 0, 'a hung push service delays the sign-out by at most 2 seconds', r);
    await close();
  }
  /* it throws: still signs out */
  {
    const { page, close } = await desk();
    await tick(page, 1200);
    await page.evaluate(GRANT);
    await page.evaluate(() => { window.pushDisable = async () => { throw new Error('push service down'); }; });
    try { await page.evaluate(() => authSignOut()); } catch (e) { /* a sign-out that throws is the failure the next line reports */ } await tick(page, 300);
    ok(await page.evaluate(() => !sbUser), 'a push error does not stop the sign-out');
    await close();
  }
}

/* ------------------------------------------------------------------ 2. a different account starts clean */
if (want('newuser')) {
  /* what student A left on this browser (the init script runs before the page's own scripts) */
  const INIT_A = () => { try {
    if (!localStorage.getItem('professify_last_uid')) {
      localStorage.setItem('professify_last_uid', 'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa');
      localStorage.setItem('professify_my_classes', JSON.stringify(['BUS 3438', 'MATH 9999']));
      localStorage.setItem('professify_mc_pending', JSON.stringify({ 'MATH 9999': { op: 'add', at: Date.now() } }));
      localStorage.setItem('professify_groups', '[{"id":"g1","name":"A\'s secret group","members":[]}]');
      localStorage.setItem('professify_watch', '["pr_p1"]');
      localStorage.setItem('tc-audit:aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa', '{"requirements":[]}');
    }
  } catch (e) {} };
  const INIT_ME = () => { try {
    if (!localStorage.getItem('professify_last_uid')) {
      localStorage.setItem('professify_last_uid', '11111111-1111-4111-8111-111111111111');
      localStorage.setItem('professify_my_classes', JSON.stringify(['BUS 3438', 'MATH 9999']));
      localStorage.setItem('professify_mc_pending', JSON.stringify({ 'MATH 9999': { op: 'add', at: Date.now() } }));
    }
  } catch (e) {} };
  const pushedCodes = log => log.writes.filter(w => w.table === 'saved_classes' && w.m === 'POST').flatMap(w => [].concat(w.body || [])).map(r => r.code);

  /* B arrives on a browser that still holds A's things */
  {
    const { page, close, log } = await desk({ init: INIT_A, wait: 5000 });
    await tick(page, 2500);
    const st = await page.evaluate(() => ({ mc: JSON.parse(localStorage.getItem('professify_my_classes') || '[]'), groups: localStorage.getItem('professify_groups'), audit: localStorage.getItem('tc-audit:aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa'), watch: localStorage.getItem('professify_watch'), last: localStorage.getItem('professify_last_uid'), mem: myClasses.slice(), gp: gpList.length }));
    ok(!pushedCodes(log).includes('MATH 9999'), 'a different account signing in does NOT upload the last account\'s classes', pushedCodes(log));
    ok(!st.mc.includes('MATH 9999') && !st.mem.includes('MATH 9999'), 'A\'s class is gone from storage and from memory', st);
    ok(st.groups === null && st.audit === null && st.watch === null && st.gp === 0, 'A\'s groups, audit and watchlist are gone', st);
    ok(st.last === ME.id, 'the browser now remembers B', st.last);
    ok(log.errors.length === 0, 'no page errors (new user at load)', log.errors);
    await close();
  }
  /* the same account coming back keeps its own things: the control that proves the check above can fail */
  {
    const { page, close, log } = await desk({ init: INIT_ME, wait: 5000 });
    await tick(page, 2500);
    const mem = await page.evaluate(() => myClasses.slice());
    ok(mem.includes('MATH 9999') && pushedCodes(log).includes('MATH 9999'), 'control: the SAME account\'s unsynced class still goes up (nothing was wiped)', { mem, pushed: pushedCodes(log) });
    await close();
  }
  /* B signs in on a page A left open (session expired, nothing was stored): the wipe happens in the page */
  {
    const { page, close, log } = await desk({ signedIn: false, init: INIT_A, wait: 3000 });
    await tick(page, 1000);
    const pre = await page.evaluate(() => ({ mem: myClasses.slice(), last: localStorage.getItem('professify_last_uid') }));
    ok(pre.mem.includes('MATH 9999') && pre.last === A_UID, 'set-up: signed out, the page holds A\'s class and remembers A', pre);
    await page.evaluate(() => sb.auth.signInWithPassword({ email: 'jordan.fixture@calpoly.edu', password: 'x' }));
    await tick(page, 3000);
    const st = await page.evaluate(() => ({ mc: JSON.parse(localStorage.getItem('professify_my_classes') || '[]'), mem: myClasses.slice(), last: localStorage.getItem('professify_last_uid'), groups: localStorage.getItem('professify_groups') }));
    ok(!pushedCodes(log).includes('MATH 9999'), 'B signing in on A\'s open page does not upload A\'s class', pushedCodes(log));
    ok(!st.mc.includes('MATH 9999') && !st.mem.includes('MATH 9999') && st.groups === null && st.last === ME.id, 'and A\'s lists are gone from the page and from storage', st);
    ok(log.errors.length === 0, 'no page errors (new user in page)', log.errors);
    await close();
  }
  /* the helper itself */
  {
    const { page, close } = await desk({ wait: 1500 });
    const r = await page.evaluate(() => {
      const out = {};
      localStorage.clear(); sessionStorage.clear();
      localStorage.setItem('professify_foo', '1'); localStorage.setItem('professify_pending_add', 'p'); localStorage.setItem('professify_pending_handle', 'h'); localStorage.setItem('professify-theme', 'dark');
      out.first = tcSeeUser('u1');                                   // nothing remembered yet: a guest's data is not touched
      out.firstKeep = localStorage.getItem('professify_foo');
      out.same = tcSeeUser('u1'); out.sameKeep = localStorage.getItem('professify_foo');
      out.other = tcSeeUser('u2');                                   // a different account
      out.gone = localStorage.getItem('professify_foo'); out.pend = localStorage.getItem('professify_pending_add'); out.handle = localStorage.getItem('professify_pending_handle'); out.theme = localStorage.getItem('professify-theme'); out.last = localStorage.getItem('professify_last_uid');
      return out;
    });
    ok(r.first === false && r.firstKeep === '1' && r.same === false && r.sameKeep === '1', 'first user ever, and the same user again, wipe nothing', r);
    ok(r.other === true && r.gone === null && r.last === 'u2' && r.theme === 'dark', 'a different user wipes the person keys, keeps the theme, remembers the new id', r);
    ok(r.pend === 'p' && r.handle === 'h', 'the invite it arrived with and a half-typed signup handle survive that wipe (they are the new person\'s)', r);
    await close();
  }
}

/* ------------------------------------------------------------------ 3. account deletion and the recovery sheet */
if (want('delete')) {
  const PURGE = '2026-11-03T12:00:00.123456+00:00';
  const delHook = st => (url) => {
    const fn = url.pathname.startsWith('/rest/v1/rpc/') ? url.pathname.slice(13) : '';
    if (fn === 'my_account_deletion') return { status: 200, body: JSON.stringify(st.at ? [{ purge_after: st.at, delete_reviews: false }] : []) };
    if (fn === 'request_account_deletion') { st.at = PURGE; return { status: 200, body: JSON.stringify(PURGE) }; }
    return null;
  };
  /* the page writes its own keys again when it boots after the reload, so only keys this test made up are checked */
  const SEED_D = () => { localStorage.setItem('professify_zz_seed', '1'); localStorage.setItem('tc-zz-seed', '1'); localStorage.setItem('tc_zz_seed', '1'); localStorage.setItem('sb-zz-seed', '1'); localStorage.setItem('professify-theme', 'dark'); localStorage.setItem('unrelated-key', 'mine'); };
  const gone = page => page.evaluate(() => ({ l: Object.keys(localStorage), theme: localStorage.getItem('professify-theme') }));
  {
    const st = {};
    const { page, close } = await desk({ hook: delHook(st) });
    await tick(page, 1500);
    await page.evaluate(SEED_D);
    await page.evaluate(() => openDeleteAccount()); await tick(page, 800);
    await page.fill('#delConfirm', 'delete'); await page.evaluate(() => delValidate());
    await Promise.all([page.waitForEvent('load'), page.click('#delGo')]);
    await page.clock.runFor(2000); await page.waitForTimeout(500);
    const g = await gone(page);
    ok(!g.l.includes('professify_zz_seed') && !g.l.includes('tc-zz-seed') && !g.l.includes('tc_zz_seed') && !g.l.includes('sb-zz-seed'), 'deleting the account removes professify, sb-, tc- and tc_ keys from this device', g.l);
    ok(g.theme === 'dark' && g.l.includes('unrelated-key'), 'the theme and an unrelated key survive that wipe', g);
    await close();
  }
  {
    const st = { at: PURGE };
    const { page, close, log } = await desk({ hook: delHook(st) });
    await tick(page, 1500);
    await page.evaluate(SEED_D);
    await Promise.all([page.waitForEvent('load'), page.click('#recOut')]);
    await page.clock.runFor(2000); await page.waitForTimeout(500);
    const g = await gone(page);
    ok(log.writes.some(w => /^auth:logout/.test(w.table)) && !g.l.includes('professify_zz_seed') && !g.l.includes('tc-zz-seed') && !g.l.includes('tc_zz_seed'), '"Sign out" on the recovery sheet also leaves nothing of the account behind', g.l);
    ok(g.theme === 'dark' && g.l.includes('unrelated-key'), 'and keeps the theme', g);
    await close();
  }
}

/* ------------------------------------------------------------------ 4. avatars */
if (want('avatars')) {
  const BASE = 'https://rqkndeqbcahozidniesn.supabase.co/storage/v1/object/public/avatars/';
  const GOOD = BASE + '22222222-2222-4222-8222-222222222222/avatar.jpg?v=1760000000000';
  const BAD = {
    other: 'https://evil.example/pixel.png?who=friend', http: BASE.replace('https:', 'http:') + 'x/avatar.jpg', lookalike: 'https://rqkndeqbcahozidniesn.supabase.co.evil.example/storage/v1/object/public/avatars/x/avatar.jpg',
    otherBucket: 'https://rqkndeqbcahozidniesn.supabase.co/storage/v1/object/public/not-avatars/x/avatar.jpg', dots: BASE + '../../public/other/x.jpg', js: 'javascript:alert(1)',
    quote: BASE + 'x/a.jpg"onerror="window.__PWN=1', space: BASE + 'x/a b.jpg', rel: '/avatars/x.jpg',
  };
  const WATCH = () => {
    window.__imgs = []; window.__fetches = [];
    const note = i => { const s = i.getAttribute('src') || ''; if (!s || /brand-/.test(i.className) || s.charAt(0) === '/') return; window.__imgs.push({ src: s, rp: i.getAttribute('referrerpolicy') }); };   /* the page's own logo and icons are not avatars */
    new MutationObserver(ms => { for (const m of ms) for (const n of m.addedNodes) if (n.nodeType === 1) (n.tagName === 'IMG' ? [n] : [...n.querySelectorAll('img')]).forEach(note); }).observe(document, { childList: true, subtree: true });
    const f = window.fetch; window.fetch = function (u) { try { window.__fetches.push(String(u && u.url || u)); } catch (e) {} return f.apply(this, arguments); };
    try { localStorage.setItem('professify_profile_cache', JSON.stringify({ id: '11111111-1111-4111-8111-111111111111', display_name: 'Jordan Fixture', avatar_url: 'https://evil.example/pixel.png?who=me' })); } catch (e) {}
  };
  const profiles = FX.TABLES.profiles.map(p => p.id === ME.id ? Object.assign({}, p, { avatar_url: 'https://evil.example/pixel.png?who=me' }) : p.id === FX.FRIENDS[0].id ? Object.assign({}, p, { avatar_url: BAD.other }) : p.id === FX.FRIENDS[1].id ? Object.assign({}, p, { avatar_url: GOOD }) : p.id === FX.FRIENDS[2].id ? Object.assign({}, p, { avatar_url: BAD.lookalike }) : p);
  const { page, close, log } = await desk({ init: WATCH, tables: Object.assign({}, FX.TABLES, { profiles }) });
  await tick(page, 1500);
  await page.evaluate(() => { show('friends'); }); await tick(page, 2500);
  await page.evaluate(() => { show('home'); try { hmRenderFeed(); } catch (e) {} }); await tick(page, 1500);
  const seen = await page.evaluate(() => ({ imgs: window.__imgs, fetches: window.__fetches }));
  ok(!seen.imgs.some(i => /evil\.example/.test(String(i.src))), 'no <img> was ever drawn for a URL outside the avatars bucket (friend, look-alike host, or my own cached profile)', seen.imgs.filter(i => /evil/.test(String(i.src))));
  ok(!seen.fetches.some(u => /evil\.example/.test(u)), 'and my own avatar is not fetched from outside the bucket either', seen.fetches);
  const goodImgs = seen.imgs.filter(i => i.src === GOOD);
  ok(goodImgs.length > 0, 'a friend\'s photo in the avatars bucket IS drawn', seen.imgs.map(i => String(i.src).slice(0, 90)));
  ok(seen.imgs.length > 0 && seen.imgs.every(i => i.rp === 'no-referrer'), 'every avatar <img> carries referrerpolicy="no-referrer"', seen.imgs.filter(i => i.rp !== 'no-referrer'));
  ok(log.errors.length === 0, 'no page errors (avatars)', log.errors);
  /* the render helper, case by case */
  const cases = await page.evaluate(({ GOOD, BAD }) => {
    const r = { good: avaHtml(GOOD, 'N') };
    for (const k in BAD) r[k] = avaHtml(BAD[k], 'N');
    r.msgGood = msgAva({ avatar: GOOD, name: 'N' }); r.msgBad = msgAva({ avatar: BAD.other, name: 'N' });
    r.mine = myAvatarHtml();
    r.dataPng = avaHtml('data:image/png;base64,iVBORw0KGgo=', 'N');
    r.psGood = psugFaces([{ avatar_url: GOOD, display_name: 'Ann Bee' }]); r.psBad = psugFaces([{ avatar_url: BAD.other, display_name: 'Ann Bee' }]);
    return { r, noph: NOPH_SVG };
  }, { GOOD, BAD });
  ok(/<img /.test(cases.r.good) && /referrerpolicy="no-referrer"/.test(cases.r.good), 'avaHtml: a bucket URL becomes a no-referrer <img>', cases.r.good);
  for (const k of Object.keys(BAD)) ok(cases.r[k] === cases.noph, 'avaHtml: ' + k + ' draws the silhouette, not an <img>', cases.r[k]);
  ok(/<img /.test(cases.r.msgGood) && /no-referrer/.test(cases.r.msgGood) && !/<img/.test(cases.r.msgBad), 'messages: same rule', [cases.r.msgGood, cases.r.msgBad]);
  ok(/<img [^>]*no-referrer/.test(cases.r.psGood) && !/<img/.test(cases.r.psBad), 'the professor page\'s friend faces: same rule', [cases.r.psGood, cases.r.psBad]);
  ok(/^<img [^>]*data:image\/png/.test(cases.r.dataPng), 'a data: image (this device\'s own cached photo bytes; the test fixtures\' stand-in photos) still draws', cases.r.dataPng);
  ok(!/evil\.example/.test(cases.r.mine), 'my own header/rail photo ignores a foreign URL in my profile', cases.r.mine);
  await close();
}

/* the face builders that live inside other features' scripts (registration day, plans, the profile editor, Settings) cannot be driven from here
   without those features' own fixtures, so they are guarded at the source: each must pass its URL through tcAva() and draw no-referrer */
if (want('sites')) {
  const fs = await import('node:fs'), path = await import('node:path');
  const src = fs.readFileSync(path.join(process.env.APP_DIR || '.', 'index.html'), 'utf8');
  const MUST = [
    ['Settings account card', "var avu=tcAva((typeof myAvatarUrl==='function')?myAvatarUrl():'');"],
    ['Settings account card <img>', "<img class=\"ava-img\" src=\"'+escAcc(avu)+'\" alt=\"\" referrerpolicy=\"no-referrer\">"],
    ['header pill', "var _av=tcAva((typeof myAvatarUrl==='function')?myAvatarUrl():'');"],
    ['header pill <img>', "src=\"'+escapeHtml(_av)+'\" alt=\"\" referrerpolicy=\"no-referrer\""],
    ['first-paint pill', "av=(typeof tcAva==='function')?tcAva(av):'';"],
    ['first-paint pill <img>', "alt=\"\" referrerpolicy=\"no-referrer\""],
    ['registration day face', "var _au = tcAva(f.avatar_url);"],
    ['registration day <img>', "referrerpolicy=\"no-referrer\" onerror=\"this.outerHTML=NOPH_SVG\">' : NOPH_SVG;"],
    ['Home face row', "var inner=tcAva(p.img)\n      ? '<img src=\"'+esc2(tcAva(p.img))+'\" alt=\"\" loading=\"lazy\" referrerpolicy=\"no-referrer\">'"],
    ['plans faces', "(tcAva(f.avatar_url) ? '<img src=\"' + esc(tcAva(f.avatar_url)) + '\" alt=\"\" loading=\"lazy\" referrerpolicy=\"no-referrer\""],
    ['plan picker face', "url=tcAva(url);   /* only our own avatars bucket (security-pass2, 2026-10-15) */\n  if(url)return '<span class=\"pl-face\"><img src=\"'+attr(url)+'\" alt=\"\" loading=\"lazy\" referrerpolicy=\"no-referrer\">"],
    ['profile editor preview', "return u?tcAva(String(u)):'';"],
    ['profile editor photo probe', "var url=tcAva((myProfile&&myProfile.avatar_url)?String(myProfile.avatar_url):'');"],
    ['own photo download', "var url=tcAva((typeof myProfile!=='undefined'&&myProfile&&myProfile.avatar_url)?String(myProfile.avatar_url):'');"],
  ];
  for (const [n, s] of MUST) ok(src.includes(s), 'avatar site guarded: ' + n, s.slice(0, 120));
  const imgs = (src.match(/referrerpolicy="no-referrer"/g) || []).length;
  ok(imgs >= 11, 'every avatar <img> in the file says no-referrer (' + imgs + ' found)', imgs);
}

/* ------------------------------------------------------------------ 5. escaping */
const judge = h => {                           // does an inline handler keep the marker inside string literals?
  let ast;
  try { ast = acorn.parse('(function(){' + h + '\n})', { ecmaVersion: 'latest' }); } catch (e) { return { parses: false, err: e.message }; }
  let breakout = false; const lits = [];
  (function w(n) { if (!n || typeof n !== 'object') return; if (n.type === 'Identifier' && /PWN/.test(n.name)) breakout = true; if (n.type === 'Literal' && typeof n.value === 'string') lits.push(n.value); for (const k in n) if (k !== 'type' && k !== 'start' && k !== 'end') { const v = n[k]; if (Array.isArray(v)) v.forEach(w); else if (v && typeof v === 'object') w(v); } })(ast);
  return { parses: true, breakout, lits };
};
if (want('escape')) {
  const { page, close } = await desk({ wait: 2500 });
  const r = await page.evaluate(() => {
    authCodeStep("o'brien@calpoly.edu");
    const btn = document.getElementById('authVerifyBtn');
    return { eh: escapeHtml("a'b\"<>&"), ea: escAcc("a'b\"<>&"), click: btn ? btn.getAttribute('onclick') : null, shown: document.getElementById('authBody').innerText };
  });
  ok(r.eh === 'a&#39;b&quot;&lt;&gt;&amp;', 'escapeHtml escapes the single quote', r.eh);
  ok(r.ea === 'a&#39;b&quot;&lt;&gt;&amp;', 'escAcc escapes the single quote', r.ea);
  const j = judge(r.click || '');
  ok(j.parses && !j.breakout && j.lits.includes("o'brien@calpoly.edu"), 'an apostrophe in an email reaches the code step\'s handler as the same string, not as a breakout', { click: r.click, j });
  ok(/o'brien@calpoly\.edu/.test(r.shown), 'and the email still reads normally on the page', r.shown.slice(0, 200));
  /* a single-quoted attribute cannot be broken out of with escapeHtml any more */
  const q = await page.evaluate(() => { const d = document.createElement('div'); d.innerHTML = "<a title='" + escapeHtml("x' onmouseover='window.__PWN=1") + "'>t</a>"; return { attrs: [...d.firstChild.attributes].map(a => a.name), title: d.firstChild.title }; });
  ok(q.attrs.length === 1 && q.attrs[0] === 'title' && q.title === "x' onmouseover='window.__PWN=1", 'escapeHtml output is safe inside a single-quoted attribute', q);
  await close();
}

/* ------------------------------------------------------------------ 5. a hostile PolyRatings payload */
if (want('poly')) {
  const EVIL_ID = "e');window.__PWN=1;//\"><img src=x onerror=window.__PWN=2>&#39;);window.__PWN=3;//";
  const POLY = FX.POLY.concat([
    { id: EVIL_ID, firstName: 'Eve<img src=x onerror=window.__PWN=4>', lastName: 'Hostile"><svg onload=window.__PWN=5>', department: 'BUS', overallRating: 3.9, numEvals: 30,
      courses: ['EVL 101"><img src=x onerror=window.__PWN=6>', "EVL 202');window.__PWN=7;//", 'EVL &#39;);window.__PWN=8;// 303'] },
    { id: 'zz-dept', firstName: 'Dana', lastName: 'Deptson', department: 'BUS"><img src=x onerror=window.__PWN=9>', overallRating: 3.1, numEvals: 12, courses: [] },
  ]);
  const { page, close, log } = await desk({ poly: POLY, wait: 4500 });
  await tick(page, 1500);
  const SNAP = () => {
    const handlers = [];
    document.querySelectorAll('*').forEach(el => { for (const a of el.attributes) if (/^on/i.test(a.name) && /PWN/.test(a.value)) handlers.push({ name: a.name, tag: el.tagName.toLowerCase(), value: a.value }); });
    return { handlers, injected: document.querySelectorAll('img[src="x" i],[onerror*=PWN i],[onload*=PWN i]').length, pwn: window.__PWN === undefined ? null : window.__PWN };
  };
  const check = async (label) => {
    const s = await page.evaluate(SNAP);
    const bad = s.handlers.map(h => ({ h, j: judge(h.value) })).filter(x => !x.j.parses || x.j.breakout);
    ok(s.injected === 0 && s.pwn === null && bad.length === 0, label + ': nothing ran, nothing was injected, every handler keeps the payload inside a string', { injected: s.injected, pwn: s.pwn, bad: bad.slice(0, 3) });
  };
  const key = await page.evaluate(() => Object.keys(PROFESSORS).find(k => /Hostile/.test(PROFESSORS[k].name)) || null);
  ok(!!key && /^pr_[A-Za-z0-9_]+$/.test(key), 'the hostile PolyRatings id is stored as a plain key (only letters, digits, _)', key);
  await page.evaluate(() => { show('explore'); setExMode('professors'); const i = document.getElementById('exQuery'); i.value = 'eve'; onExSearch(); }); await tick(page, 800);
  await check('Explore, searching the hostile professor');
  await page.evaluate(() => { const i = document.getElementById('exQuery'); i.value = 'dana'; onExSearch(); }); await tick(page, 500);
  await check('Explore, searching the hostile department');
  await page.evaluate(k => { watchlist = [k, 'pr_p1']; wpCompareSet = [k, 'pr_p1']; show('watch'); renderWatch(); }, key); await tick(page, 500);
  await page.evaluate(() => { wpMode = 'compare'; renderWatch(); }); await tick(page, 500);
  await check('the watchlist and the compare view');
  /* the door: markup characters are gone before any screen can print them */
  const door = await page.evaluate(() => Object.values(PROFESSORS).filter(p => /Hostile|Deptson|Eve/.test(p.name)).map(p => ({ name: p.name, dept: p.dept, courses: p.courses })));
  ok(door.length === 2 && door.every(d => !/[<>"`]/.test(d.name + d.dept + d.courses.join('|'))), 'PolyRatings names, departments and courses arrive without < > " or `', door);
  /* the rating form's course list, with courses that bypass the door */
  const RAWC = ['EVL 101"><img src=x onerror=window.__PWN=6>', "EVL 202');window.__PWN=7;//", 'EVL &#39;);window.__PWN=8;// 303'];
  await page.evaluate(({ k, c }) => { PROFESSORS[k].courses = c; startRate(k, ''); }, { k: key, c: RAWC }); await tick(page, 800);
  const opts = await page.evaluate(() => { const s = document.getElementById('rfCourse'); return s && s.options ? [...s.options].map(o => o.textContent) : null; });
  const wantOpts = RAWC.map(c => c.toUpperCase());
  ok(opts && wantOpts.every(w => opts.includes(w)) && opts.length === RAWC.length + 1, 'the rating form lists hostile courses as plain text, one <option> each', opts);
  await check('the rating form');
  await page.evaluate(() => { try { closeModal(); } catch (e) {} openProf(Object.keys(PROFESSORS).find(k => /Hostile/.test(PROFESSORS[k].name))); }); await tick(page, 800);
  await check('the professor page');
  /* the same render paths with a key that still has quotes in it: bypass the door and prove the handlers themselves */
  const RAW = "x');window.__PWN=10;//\"><img src=x onerror=window.__PWN=11>";
  const html = await page.evaluate(RAW => {
    PROFESSORS[RAW] = { name: 'Zed Rawkey', dept: 'BUS"><img src=x onerror=window.__PWN=13>', field: 'BUS', rating: 3.3, evals: 9, live: true, courses: ['EVL 9"><img src=x onerror=window.__PWN=12>'], prId: 'raw' };
    const box = document.createElement('div'); box.id = 'rawBox'; document.body.appendChild(box);
    const parts = [];
    try { watchlist = [RAW, 'pr_p1']; wpCompareSet = [RAW, 'pr_p1']; wpMode = 'list'; renderWatch(); parts.push(document.getElementById('watchOut').innerHTML); wpMode = 'compare'; renderWatch(); parts.push(document.getElementById('watchOut').innerHTML); } catch (e) { parts.push('ERR ' + e.message); }
    try { parts.push(profSectionRow(RAW, true, 'BUS 1100', '2268')); } catch (e) { parts.push('ERR ' + e.message); }
    try { GE_COURSES.unshift({ code: 'GE 1', name: 'x', prof: RAW, workload: 'Light', area: 'A' }); parts.push(flexSlot({ label: 'Pick one', units: 4 }, '2268')); GE_COURSES.shift(); } catch (e) { parts.push('ERR ' + e.message); }
    try { parts.push(watchBtn(RAW)); } catch (e) { parts.push('ERR ' + e.message); }
    try { parts.push(miniProf(RAW)); } catch (e) { parts.push('ERR ' + e.message); }
    try { parts.push(rlProfRowHtml(RAW, PROFESSORS[RAW], '', 'BUS 1100')); } catch (e) { parts.push('ERR ' + e.message); }
    try { parts.push(myrRowsHtml([{ id: 1, professor_key: profKey(PROFESSORS[RAW]), professor_name: 'Zed Rawkey', score: 4, course: 'BUS 1100', created_at: '2026-09-01T00:00:00Z' }])); } catch (e) { parts.push('ERR ' + e.message); }
    try { startRate(RAW, ''); parts.push(document.getElementById('modal').innerHTML); closeModal(); } catch (e) { parts.push('ERR ' + e.message); }
    box.innerHTML = parts.join('\n');
    return parts.map(p => p.slice(0, 40));
  }, RAW);
  ok(!html.some(p => /^ERR/.test(p)), 'set-up: the raw-key renders ran', html);
  const rawSnap = await page.evaluate(() => { const b = document.getElementById('rawBox'); const hs = []; b.querySelectorAll('*').forEach(el => { for (const a of el.attributes) if (/^on/i.test(a.name) && /PWN/.test(a.value)) hs.push(a.value); }); return { hs, injected: b.querySelectorAll('img[src="x" i],[onerror*=PWN i],[onload*=PWN i]').length, pwn: window.__PWN === undefined ? null : window.__PWN }; });
  const rawBad = rawSnap.hs.map(h => ({ h, j: judge(h) })).filter(x => !x.j.parses || x.j.breakout);
  ok(rawSnap.hs.length >= 12 && rawBad.length === 0 && rawSnap.injected === 0 && rawSnap.pwn === null, 'a professor key with quotes in it (past the door): every handler (card, watch, compare, section row, GE option, mini row, review rows, rating form) holds it as one string', { n: rawSnap.hs.length, rawBad: rawBad.slice(0, 3), injected: rawSnap.injected, pwn: rawSnap.pwn });
  ok(rawSnap.hs.some(h => judge(h).lits.includes(RAW)), 'and the handler hands the exact key back to openProf / toggleWatch', rawSnap.hs.slice(0, 2));
  /* Explore card opens the right professor even with quotes in its key */
  await page.evaluate(() => { document.getElementById('rawBox').remove(); show('explore'); setExMode('professors'); const i = document.getElementById('exQuery'); i.value = 'zed'; onExSearch(); }); await tick(page, 800);
  await check('Explore card of a professor whose department carries markup (past the door)');
  const card = page.locator('.pcard', { hasText: 'Zed Rawkey' }).first();
  if (await card.count()) { await card.click(); await tick(page, 600); }
  const opened = await page.evaluate(() => ({ cur: typeof currentProf !== 'undefined' ? currentProf : null, pwn: window.__PWN === undefined ? null : window.__PWN }));
  ok(await card.count() > 0 && opened.cur === RAW && opened.pwn === null, 'clicking the card of a quote-laden key opens that professor and runs nothing', { count: await card.count(), opened });
  ok(log.errors.length === 0, 'no page errors (poly)', log.errors);
  await close();
}

/* ------------------------------------------------------------------ 6. the fallback session cookie */
if (want('cookie')) {
  const INIT = () => {
    window.__ck = [];
    const d = Object.getOwnPropertyDescriptor(Document.prototype, 'cookie');
    Object.defineProperty(Document.prototype, 'cookie', { configurable: true, get() { return d.get.call(this); }, set(v) { window.__ck.push(String(v)); return d.set.call(this, v); } });
    const o = Storage.prototype.setItem;
    Storage.prototype.setItem = function (k, v) { if (String(k).indexOf('sb-') === 0) throw new Error('storage blocked'); return o.apply(this, arguments); };
  };
  const { page, close } = await desk({ signedIn: false, init: INIT, wait: 3000 });
  await tick(page, 800);
  await page.evaluate(() => sb.auth.signInWithPassword({ email: 'jordan.fixture@calpoly.edu', password: 'x' })); await tick(page, 1500);
  const ck = await page.evaluate(() => window.__ck.filter(c => /^sb-/.test(c)));
  const w = ck.find(c => /auth-token=/.test(c) && !/max-age=0/.test(c)) || '';
  ok(!!w, 'set-up: with storage refusing, the session is written to the fallback cookie', ck);
  ok(/;\s*Secure/i.test(w) && /;\s*SameSite=Strict/i.test(w) && /;\s*path=\//i.test(w), 'the cookie is Secure; SameSite=Strict; path=/', w.replace(/=[^;]*/, '=…'));
  ok(/max-age=604800(;|$)/i.test(w), 'and lives 7 days, not a year', w.replace(/=[^;]*/, '=…'));
  await page.evaluate(() => sb.auth.signOut()); await tick(page, 800);
  const rm = await page.evaluate(() => window.__ck.filter(c => /^sb-.*max-age=0/.test(c)));
  ok(rm.length > 0 && rm.every(c => /Secure/i.test(c) && /SameSite=Strict/i.test(c)), 'and is removed with the same attributes on sign-out', rm);
  await close();
}

/* ------------------------------------------------------------------ 8. a click is named by data-ev / id / tag, never by text */
if (want('evname')) {
  const { page, close, log } = await desk({ wait: 3500 });
  await tick(page, 1000);
  await page.evaluate(() => {
    const h = document.createElement('div');          // appended to <body>: no ancestor with an id, so the tag fallback is what is under test
    h.setAttribute('data-test-evname', '1');
    h.innerHTML = '<button type="button" aria-label="Secret Friend Aria">Alex Chen</button>'
      + '<input type="text" aria-label="Typed box">'
      + '<a href="#" onclick="return false">Taylor Rivera</a>'
      + '<button type="button" data-ev="my-label">Morgan Lee</button>'
      + '<button type="button" id="evb-id">Casey Park</button>';
    document.body.appendChild(h);
  });
  const clicks = [['button[aria-label="Secret Friend Aria"]'], ['input[aria-label="Typed box"]', 'typed secret words'], ['a:has-text("Taylor Rivera")'], ['button[data-ev="my-label"]'], ['#evb-id']];
  for (const [sel, fill] of clicks) { if (fill) await page.fill(sel, fill); await page.click(sel); await page.waitForTimeout(150); }
  await page.evaluate(() => evFlush()); await tick(page, 600);
  const evs = log.rpcs.filter(r => r.fn === 'log_events').flatMap(r => (r.body && r.body.p_batch) || []);
  const targets = evs.filter(e => e.name === 'click').map(e => e.props && e.props.target);
  const all = JSON.stringify(evs);
  ok(!/Alex|Chen|Secret Friend|typed secret|Taylor|Rivera|Morgan|Casey|Typed box/.test(all), 'no label, aria-label, typed value or name from the page appears in any analytics event', all.match(/.{0,30}(Alex|Secret Friend|typed secret|Taylor|Morgan|Casey).{0,30}/g));
  ok(targets.includes('button') && targets.includes('input') && targets.includes('a'), 'an unlabelled button / input / link is named by its tag', targets);
  ok(targets.includes('my-label') && targets.includes('#evb-id'), 'data-ev and id still name a click', targets);
  ok(log.errors.length === 0, 'no page errors (evname)', log.errors);
  await close();
}

console.log(`\ncheck-desktop-security-pass2: ${pass} passed, ${fail} failed`);
if (fail) process.exitCode = 1;
