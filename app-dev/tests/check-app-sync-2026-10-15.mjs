/* check-app-sync — the PHONE app (app/index.html) against app-dev/patches/sync-app-2026-10-15.py: the student's data is the same on the phone and the website.
   conc   Gap 1   profiles.concentration is read and wins over the device copy; 'General / Open' = none; uploaded once; unreadable => today's behaviour; edits write profiles
   pins   Gap 2   story pins <-> my_pinned_friends / set_pinned_friends; one-time upload; max 3; toasts unchanged; not installed => local; failed write => retried
   cm     Gap 3   commitments are re-uploaded only once per account
   saved  Gap 7   Explore bookmarks <-> saved_items (class 'BUS 3431', prof review key), one-time upload, removal deletes the account's row
   chat   Gap 8   chat pins <-> conversation_members.pinned_at, one-time upload, order kept; not installed => local
   plan   Gap 10  a plan keeps the class numbers the seat feed doesn't have
   push   Gap 6   the seat-alert switch <-> push_prefs.seats (both read, both written)
   Run: APP_DIR=<repo root> node check-app-sync-2026-10-15.mjs [--only conc|pins|cm|saved|chat|plan|push] [--quiet]   (APP_PORT to move off 8190) */
import { openApp } from './app-harness.mjs';
import * as FX from './app-fixtures.mjs';

const args = process.argv.slice(2);
const ONLY = args.includes('--only') ? args[args.indexOf('--only') + 1] : null;
const QUIET = args.includes('--quiet');
const want = n => !ONLY || ONLY === n;
let pass = 0, fail = 0;
const ok = (c, name, info) => { if (c) { pass++; if (!QUIET) console.log('  ok  ', name); } else { fail++; console.log('  FAIL', name, info !== undefined ? '→ ' + JSON.stringify(info).slice(0, 600) : ''); } };
const tick = async (p, ms = 500) => { await p.clock.runFor(ms); await p.waitForTimeout(250); };
const ME = FX.ME, F = FX.FRIENDS.map(f => f.id);
const J = JSON.stringify;
const res = (body, status = 200) => ({ status, body: J(body) });
const gapFn = { status: 404, body: J({ code: 'PGRST202', message: 'Could not find the function public.x in the schema cache', details: null, hint: null }) };
const gapTable = { status: 404, body: J({ code: 'PGRST205', message: "Could not find the table 'public.saved_items' in the schema cache", details: null, hint: null }) };
const gapCol = { status: 400, body: J({ code: '42703', message: 'column conversation_members.pinned_at does not exist', details: null, hint: null }) };
const boom = { status: 500, body: J({ code: 'XX000', message: 'server fell over' }) };
/* run a seed as the page starts (once per tab, so a reload keeps what the app has written since) */
const seed = (pairs) => `try{ if (!sessionStorage.getItem('__seeded')) { sessionStorage.setItem('__seeded','1'); const p = ${J(pairs)}; for (const k in p) localStorage.setItem(k, typeof p[k] === 'string' ? p[k] : JSON.stringify(p[k])); } }catch(e){}`;
const app = async (o = {}) => { const a = await openApp(Object.assign({ path: '/app/' }, o)); try { await a.page.waitForFunction(() => TC.ready, null, { timeout: 12000 }); } catch (e) { ok(false, 'the app did not finish loading'); } await tick(a.page, 800); return a; };
const reload = async a => { const ld = await a.page.evaluate(() => TC.loadDone); await a.page.evaluate(() => TC.refresh()); for (let i = 0; i < 20 && (await a.page.evaluate(() => TC.loadDone)) === ld; i++) await tick(a.page, 500); await tick(a.page, 1500); };
const wr = (a, table, m) => a.log.writes.filter(w => w.table === table && (!m || w.m === m));
const dq = q => decodeURIComponent(String(q).replace(/\+/g, ' '));
const flag = (page, k) => page.evaluate(k => localStorage.getItem(k + ':' + TC.user.id), k);
const toastText = page => page.locator('#toast').innerText();
const GRANT = { profiles: ['concentration'] };
const CONC_LOCAL = { termchamp_app_conc: { u: ME.id, major: 'Business Administration', conc: 'Entrepreneurship' } };
const withTables = (extra) => Object.assign({}, FX.TABLES, extra);
const withMe = (patch) => withTables({ profiles: [Object.assign({}, ME, patch), ...FX.TABLES.profiles.slice(1)] });

/* ------------------------------------------------------------------ 1. concentration */
if (want('conc')) try {
  /* the database value wins over this device's copy, and it is asked for */
  {
    const a = await app({ grants: GRANT, tables: withMe({ concentration: 'Marketing' }), init: seed(CONC_LOCAL) });
    const st = await a.page.evaluate(() => ({ c: TC.profile && TC.profile.concentration, phase: TC.phase, loc: JSON.parse(localStorage.getItem('termchamp_app_conc') || 'null') }));
    ok(a.log.reads.some(r => /^profiles\?/.test(r) && /select=[^&]*concentration/.test(decodeURIComponent(r))), 'conc: your own profile is read WITH concentration', a.log.reads.filter(r => /^profiles/.test(r)).slice(0, 3));
    ok(st.phase === 'ok' && st.c === 'Marketing', 'conc: the account’s concentration (Marketing) wins over the phone’s own copy (Entrepreneurship)', st);
    ok(st.loc && st.loc.conc === 'Marketing', 'conc: …and becomes the device copy', st.loc);
    ok(wr(a, 'profiles').length === 0, 'conc: reading it writes nothing', wr(a, 'profiles'));
    ok(a.log.errors.length === 0, 'conc: no page errors', a.log.errors);
    await a.close();
  }
  /* the website’s word for none */
  {
    const a = await app({ grants: GRANT, tables: withMe({ concentration: 'General / Open' }), init: seed({}) });
    const c = await a.page.evaluate(() => TC.profile.concentration);
    ok(c === null && wr(a, 'profiles').length === 0, '“General / Open” (the website’s none) is no concentration here', { c, w: wr(a, 'profiles') });
    await a.close();
  }
  /* the account has none, this phone has one it never uploaded: up once, then the account is the truth */
  {
    const a = await app({ grants: GRANT, tables: withMe({ concentration: null }), init: seed(CONC_LOCAL) });
    const w = wr(a, 'profiles', 'PATCH');
    ok(w.length === 1 && J(w[0].body) === J({ concentration: 'Entrepreneurship' }), 'conc: a phone-only concentration is uploaded once (one column)', w);
    ok(await flag(a.page, 'tc-conc-migrated') === '1' && await a.page.evaluate(() => TC.profile.concentration) === 'Entrepreneurship', 'conc: …flag set once it landed; still shown', await flag(a.page, 'tc-conc-migrated'));
    /* the student clears it on the website: the account says none, the phone follows and does not upload it again */
    a.tables.profiles.find(p => p.id === ME.id).concentration = null;
    const n0 = wr(a, 'profiles', 'PATCH').length;
    await reload(a);
    const c = await a.page.evaluate(() => ({ c: TC.profile.concentration, loc: JSON.parse(localStorage.getItem('termchamp_app_conc') || 'null') }));
    ok(c.c === null && wr(a, 'profiles', 'PATCH').length === n0, 'conc: cleared on the website => cleared here, and not uploaded again', { c, n: wr(a, 'profiles', 'PATCH').length });
    ok(!c.loc || !c.loc.conc, 'conc: …and the device copy is cleared too', c.loc);
    await a.close();
  }
  /* a database that does not grant the column (the live one does; this models an older one): the app still opens
     and uses the device copy. The harness grants concentration by default now, so the refusal is made here. */
  {
    const refused = [];
    const hook = (url, m) => {
      if (m === 'GET' && /\/rest\/v1\/profiles$/.test(url.pathname) && /concentration/.test(decodeURIComponent(url.search)) && url.search.includes(ME.id)) {
        refused.push(1);
        return { status: 401, body: JSON.stringify({ code: '42501', message: 'permission denied for table profiles' }) };
      }
      return null;
    };
    const a = await app({ hook, tables: withMe({ concentration: 'Marketing' }), init: seed(CONC_LOCAL) });
    const st = await a.page.evaluate(() => ({ c: TC.profile.concentration, phase: TC.phase }));
    ok(st.phase === 'ok' && st.c === 'Entrepreneurship', 'conc: column not granted (42501) => the profile still loads, with this phone’s own concentration', st);
    ok(wr(a, 'profiles').length === 0, 'conc: …and nothing is written', wr(a, 'profiles'));
    const own = () => a.log.reads.filter(r => /^profiles\?/.test(r) && r.includes(ME.id)).map(r => /concentration/.test(decodeURIComponent(r)));
    const n0 = own().length, r0 = refused.length;
    await reload(a);
    ok(r0 === 1 && refused.length === r0 && J(own().slice(n0)) === J([false]), 'conc: …a refused column is not asked for again on the next load (one extra read, once)', { refused: refused.length, r0, own: own() });
    await a.close();
  }
  /* edits write profiles: major, standing (incl. 5th year +), concentration */
  {
    const a = await app({ grants: GRANT, tables: withMe({ concentration: 'Marketing' }), init: seed({}) });
    const e = await a.page.evaluate(() => TC.saveProfile({ display_name: 'Jordan Fixture', username: 'jfixture', major: 'Finance', concentration: 'Financial Management', class_standing: '5th year +' }));
    const w = wr(a, 'profiles', 'PATCH').filter(x => 'major' in x.body);
    ok(!e && w.length === 1 && w[0].body.major === 'Finance' && w[0].body.class_standing === '5th year +' && w[0].body.concentration === 'Financial Management', 'conc: Edit profile writes major, year (5th year +) and concentration to profiles', { e, w: w.map(x => x.body) });
    const e2 = await a.page.evaluate(() => TC.updateProfileFields({ class_standing: 'Senior' }));
    const w2 = wr(a, 'profiles', 'PATCH').filter(x => J(x.body) === J({ class_standing: 'Senior' }));
    ok(!e2 && w2.length === 1, 'conc: a year-only change writes profiles too', { e2, w2 });
    await a.page.evaluate(() => A.pickConc('Banking')); await tick(a.page, 500);
    const w3 = wr(a, 'profiles', 'PATCH').filter(x => J(x.body) === J({ concentration: 'Banking' }));
    ok(w3.length === 1, 'conc: picking a concentration writes profiles', w3);
    await a.close();
  }
} catch (e) { ok(false, 'section crashed: ' + e.message); }

/* ------------------------------------------------------------------ 2. story pins */
if (want('pins')) try {
  const PK = ME.id;
  const pinsNow = page => page.evaluate(() => ({ list: pinsGet(), raw: JSON.parse(localStorage.getItem('tc-story-pins:' + TC.user.id) || '[]') }));
  const calls = a => a.log.rpcs.filter(r => r.fn === 'set_pinned_friends').map(r => r.body.p_ids);
  /* the server list is empty and this phone has pins: they go up once */
  {
    const a = await app({ init: seed({ ['tc-story-pins:' + PK]: [F[0], F[1]] }) });
    ok(a.log.rpcs.some(r => r.fn === 'my_pinned_friends'), 'pins: the account’s pins are read with my_pinned_friends');
    ok(J(calls(a)) === J([[F[0], F[1]]]), 'pins: server empty + pins on this phone => uploaded once, in order', calls(a));
    ok(await flag(a.page, 'tc-pins-migrated') === '1', 'pins: …flag tc-pins-migrated set');
    await reload(a);
    ok(calls(a).length === 1, 'pins: …and not again on the next load', calls(a));
    await a.close();
  }
  /* the server has pins: it wins over the phone’s */
  {
    const a = await app({ rpc: Object.assign({}, FX.RPC, { my_pinned_friends: [F[2], F[3]] }), init: seed({ ['tc-story-pins:' + PK]: [F[0]] }) });
    const p = await pinsNow(a.page);
    ok(J(p.list) === J([F[2], F[3]]) && J(p.raw) === J([F[2], F[3]]), 'pins: the account’s pins (not the phone’s) are what shows, and the phone keeps them as its cache', p);
    ok(calls(a).length === 0, 'pins: …nothing is uploaded', calls(a));
    const order = await a.page.evaluate(() => storyOrder().slice(0, 2));
    ok(J(order) === J([F[2], F[3]]), 'pins: the stories row leads with them', order);
    await a.close();
  }
  /* the account has none because it was cleared on the website: the phone does not put its old ones back */
  {
    const a = await app({ init: seed({ ['tc-story-pins:' + PK]: [F[0]], ['tc-pins-migrated:' + PK]: '1' }) });
    const p = await pinsNow(a.page);
    ok(calls(a).length === 0 && p.list.length === 0 && p.raw.length === 0, 'pins: already migrated + server empty => cleared here, never re-uploaded', { c: calls(a), p });
    await a.close();
  }
  /* pin, the fourth, unpin: toasts unchanged; the account is told */
  {
    const a = await app({ init: seed({}) });
    await a.page.evaluate(id => A.togglePin(id), F[0]); await tick(a.page, 400);
    ok(/Pinned Avery to the front/.test(await toastText(a.page)) && J(calls(a)) === J([[F[0]]]), 'pins: pin => “Pinned Avery to the front” and set_pinned_friends([Avery])', { t: await toastText(a.page), c: calls(a) });
    await a.page.evaluate(id => A.togglePin(id), F[1]); await a.page.evaluate(id => A.togglePin(id), F[2]); await tick(a.page, 400);
    ok(J(calls(a).at(-1)) === J([F[0], F[1], F[2]]), 'pins: three pinned, in order', calls(a));
    const n = calls(a).length;
    await a.page.evaluate(id => A.togglePin(id), F[3]); await tick(a.page, 400);
    ok(/3 pinned already — unpin Avery, Rowan or Sky first/.test(await toastText(a.page)) && calls(a).length === n, 'pins: a fourth => the same toast, and nothing is sent', { t: await toastText(a.page), n: calls(a).length - n });
    await a.page.evaluate(id => A.togglePin(id), F[1]); await tick(a.page, 400);
    ok(/Unpinned Rowan/.test(await toastText(a.page)) && J(calls(a).at(-1)) === J([F[0], F[2]]), 'pins: unpin => “Unpinned Rowan”, and the account follows', { t: await toastText(a.page), c: calls(a).at(-1) });
    await reload(a);
    const p = await pinsNow(a.page);
    ok(J(p.list) === J([F[0], F[2]]), 'pins: after a reload the account’s pins are the same', p);
    await a.close();
  }
  /* the server keeps fewer than asked (only friends): the phone follows what it kept */
  {
    const a = await app({ init: seed({}), hook: (url, m, body) => url.pathname.endsWith('/rpc/set_pinned_friends') ? res((body.p_ids || []).filter(x => x !== F[1])) : null });
    await a.page.evaluate(id => A.togglePin(id), F[0]); await a.page.evaluate(id => A.togglePin(id), F[1]); await tick(a.page, 600);
    const p = await pinsNow(a.page);
    ok(J(p.list) === J([F[0]]), 'pins: what the server kept is what shows', p);
    await a.close();
  }
  /* SQL not installed yet: pins work on this phone exactly as before, no error, no retry flag */
  {
    const a = await app({ init: seed({ ['tc-story-pins:' + PK]: [F[0]] }), hook: (url) => /\/rpc\/(my|set)_pinned_friends/.test(url.pathname) ? gapFn : null });
    await a.page.evaluate(id => A.togglePin(id), F[1]); await tick(a.page, 400);
    const p = await pinsNow(a.page);
    ok(/Pinned Rowan/.test(await toastText(a.page)) && J(p.list) === J([F[0], F[1]]) && await flag(a.page, 'tc-pins-dirty') === null, 'pins: functions missing (PGRST202) => pins still work on this phone, nothing flagged', { p, d: await flag(a.page, 'tc-pins-dirty') });
    ok(a.log.errors.length === 0, 'pins: …no page errors', a.log.errors);
    await a.close();
  }
  /* only the write function is missing: the same, nothing flagged */
  {
    const a = await app({ init: seed({}), hook: (url) => url.pathname.endsWith('/rpc/set_pinned_friends') ? gapFn : null });
    await a.page.evaluate(id => A.togglePin(id), F[1]); await tick(a.page, 400);
    ok(/Pinned Rowan/.test(await toastText(a.page)) && await flag(a.page, 'tc-pins-dirty') === null, 'pins: only set_pinned_friends missing => still local, nothing flagged', { d: await flag(a.page, 'tc-pins-dirty') });
    await a.close();
  }
  /* a write that fails on the network is kept and goes up next load instead of being read over */
  {
    let down = true;
    const a = await app({ init: seed({ ['tc-pins-migrated:' + PK]: '1' }), hook: (url) => down && url.pathname.endsWith('/rpc/set_pinned_friends') ? boom : null });
    await a.page.evaluate(id => A.togglePin(id), F[0]); await tick(a.page, 400);
    ok(await flag(a.page, 'tc-pins-dirty') === '1', 'pins: a failed write leaves tc-pins-dirty', await flag(a.page, 'tc-pins-dirty'));
    down = false; await reload(a);
    const p = await pinsNow(a.page);
    ok(J(calls(a).at(-1)) === J([F[0]]) && J(p.list) === J([F[0]]) && await flag(a.page, 'tc-pins-dirty') === null, 'pins: …next load pushes the phone’s pin (it is not overwritten by the older, empty server list)', { c: calls(a), p });
    await a.close();
  }
} catch (e) { ok(false, 'section crashed: ' + e.message); }

/* ------------------------------------------------------------------ 3. commitments */
if (want('cm')) try {
  const CM = [{ id: '5d6f1c1e-0000-4000-8000-000000000001', kind: 'work', name: 'Fixture shift', days: 'MW', s: 600, e: 720, busy: true }];
  const up = a => wr(a, 'commitments', 'POST');
  {
    const a = await app({ init: seed({ ['tc-commits:' + ME.id]: CM }) });
    ok(up(a).length === 1 && up(a)[0].body.id === CM[0].id, 'commitments: server empty + commitments on this phone, first time => uploaded once', up(a));
    ok(await flag(a.page, 'tc-commits-migrated') === '1', 'commitments: …flag tc-commits-migrated set');
    await a.close();
  }
  {
    const a = await app({ init: seed({ ['tc-commits:' + ME.id]: CM, ['tc-commits-migrated:' + ME.id]: '1' }) });
    const st = await a.page.evaluate(() => ({ n: TC.commits.length, raw: localStorage.getItem('tc-commits:' + TC.user.id) }));
    ok(up(a).length === 0 && st.n === 0, 'commitments: already migrated + server empty (deleted on the website) => NOT re-uploaded, and gone here', { up: up(a).length, st });
    await a.close();
  }
  {
    const a = await app({ tables: withTables({ commitments: [{ id: 'srv-1', user_id: ME.id, kind: 'practice', name: 'Rowing', days: 'TR', start_min: 360, end_min: 450, busy: true }] }), init: seed({ ['tc-commits:' + ME.id]: CM }) });
    const st = await a.page.evaluate(() => TC.commits.map(c => c.id));
    ok(up(a).length === 0 && J(st) === J(['srv-1']) && await flag(a.page, 'tc-commits-migrated') === '1', 'commitments: the server has rows => theirs show, nothing is uploaded, and the migration is over', { up: up(a).length, st });
    await a.close();
  }
} catch (e) { ok(false, 'section crashed: ' + e.message); }

/* ------------------------------------------------------------------ 4. Explore bookmarks */
if (want('saved')) try {
  const UI0 = (saved) => ({ 'termchamp-app-v1': { saved } });
  const SV = (kind, key) => ({ user_id: ME.id, kind, key, created_at: '2026-09-20T00:00:00Z' });
  const ins = a => wr(a, 'saved_items', 'POST').flatMap(w => Array.isArray(w.body) ? w.body : [w.body]);
  const saved = page => page.evaluate(() => S.saved.slice());
  /* first load: the account's bookmarks show, this phone's go up once with the right keys */
  {
    const a = await app({ tables: withTables({ saved_items: [SV('class', 'BUS 4442'), SV('prof', 'ada examplewood|business')] }), init: seed(UI0(['c:BUS 3431', 'p:bram fixturesen'])) });
    const s = await saved(a.page);
    ok(J(ins(a).map(r => [r.kind, r.key]).sort()) === J([['class', 'BUS 3431'], ['prof', 'bram fixturesen|bus']]), 'saved: the phone’s bookmarks go up once — class “BUS 3431”, professor by review key “bram fixturesen|bus”', ins(a));
    ok(ins(a).every(r => !('user_id' in r)), 'saved: …the server stamps who (no user_id sent)', ins(a));
    ok(['c:BUS 4442', 'p:ada examplewood', 'c:BUS 3431', 'p:bram fixturesen'].every(k => s.includes(k)) && s.length === 4, 'saved: …and the account’s bookmarks show too (class and professor)', s);
    ok(await flag(a.page, 'tc-saved-migrated') === '1', 'saved: …flag set');
    const n = ins(a).length;
    /* removed on the website: gone here, not put back */
    a.tables.saved_items = a.tables.saved_items.filter(r => r.key !== 'BUS 4442');
    await reload(a);
    const s2 = await saved(a.page);
    ok(!s2.includes('c:BUS 4442') && ins(a).length === n, 'saved: a bookmark removed on the website goes here and is not re-uploaded', { s2, n: ins(a).length - n });
    /* toggle */
    await a.page.evaluate(() => A.save('c:BUS 3438')); await tick(a.page, 300);
    ok(ins(a).at(-1) && ins(a).at(-1).kind === 'class' && ins(a).at(-1).key === 'BUS 3438', 'saved: bookmarking a class inserts (class, “BUS 3438”)', ins(a).at(-1));
    await a.page.evaluate(() => A.save('c:BUS 3438')); await tick(a.page, 300);
    const d = wr(a, 'saved_items', 'DELETE').at(-1);
    ok(d && /kind=eq\.class/.test(dq(d.query)) && /key=eq\.BUS 3438/.test(dq(d.query)) && /user_id=eq\./.test(d.query), 'saved: removing it deletes that row (own rows)', d && d.query);
    await a.page.evaluate(() => A.save('p:ada examplewood')); await tick(a.page, 300);
    const d2 = wr(a, 'saved_items', 'DELETE').at(-1);
    ok(d2 && /key=eq\.ada examplewood\|business$/.test(dq(d2.query)), 'saved: removing a professor deletes the account’s own key (“ada examplewood|business”, not the phone’s guess)', d2 && dq(d2.query));
    await a.page.evaluate(() => A.save('p:cleo stubbington')); await tick(a.page, 300);
    ok(ins(a).at(-1).kind === 'prof' && ins(a).at(-1).key === 'cleo stubbington|econ', 'saved: bookmarking a professor inserts the review key', ins(a).at(-1));
    ok(/Saved on this phone/.test('Saved on this phone') && a.log.errors.length === 0, 'saved: no page errors', a.log.errors);
    await a.close();
  }
  /* SQL not installed: bookmarks stay on this phone */
  {
    const a = await app({ init: seed(UI0(['c:BUS 3431'])), hook: (url) => /\/rest\/v1\/saved_items/.test(url.pathname) ? gapTable : null });
    await a.page.evaluate(() => A.save('c:BUS 3438')); await tick(a.page, 300);
    const s = await saved(a.page);
    ok(J(s) === J(['c:BUS 3431', 'c:BUS 3438']) && await flag(a.page, 'tc-saved-dirty') === null && await flag(a.page, 'tc-saved-migrated') === null, 'saved: table missing (PGRST205) => bookmarks work on this phone, nothing flagged', { s });
    ok(a.log.errors.length === 0, 'saved: …no page errors', a.log.errors);
    await a.close();
  }
  /* only writes are refused as "missing": the same, nothing flagged */
  {
    const a = await app({ tables: withTables({ saved_items: [] }), init: seed(UI0([])), hook: (url, m) => m !== 'GET' && /saved_items/.test(url.pathname) ? gapTable : null });
    await a.page.evaluate(() => A.save('c:BUS 3431')); await tick(a.page, 300);
    ok(J(await saved(a.page)) === J(['c:BUS 3431']) && await flag(a.page, 'tc-saved-dirty') === null, 'saved: writes answer “table missing” => still local, nothing flagged', { d: await flag(a.page, 'tc-saved-dirty') });
    await a.close();
  }
  /* a toggle that failed is not overwritten by the older server list */
  {
    let down = true;
    const a = await app({ tables: withTables({ saved_items: [] }), init: seed(Object.assign(UI0([]), { ['tc-saved-migrated:' + ME.id]: '1' })), hook: (url, m) => down && m === 'POST' && /saved_items/.test(url.pathname) ? boom : null });
    await a.page.evaluate(() => A.save('c:BUS 3431')); await tick(a.page, 300);
    ok(await flag(a.page, 'tc-saved-dirty') === '1', 'saved: a failed save leaves tc-saved-dirty', await flag(a.page, 'tc-saved-dirty'));
    down = false; await reload(a);
    ok(J(await saved(a.page)) === J(['c:BUS 3431']) && ins(a).filter(r => r.key === 'BUS 3431').length === 1 && await flag(a.page, 'tc-saved-dirty') === null, 'saved: …next load pushes it (this phone wins) instead of reading over it', { s: await saved(a.page), i: ins(a) });
    await a.close();
  }
} catch (e) { ok(false, 'section crashed: ' + e.message); }

/* ------------------------------------------------------------------ 5. chat pins */
if (want('chat')) try {
  const C = FX.CONVS.map(c => c.id);
  const pinW = a => wr(a, 'conversation_members', 'PATCH').filter(w => w.body && 'pinned_at' in w.body);
  const cid = w => /conversation_id=eq\.([^&]+)/.exec(dq(w.query))[1];
  const pins = page => page.evaluate(() => chatPins());
  {
    const a = await app({ init: seed({ ['tc-chat-pins-' + ME.id]: [C[1]] }) });
    const w = pinW(a);
    ok(w.length === 1 && cid(w[0]) === C[1] && /^\d{4}-\d\d-\d\dT/.test(w[0].body.pinned_at) && /user_id=eq\./.test(w[0].query), 'chat pins: a pin kept on this phone is stamped on the account once (pinned_at, own row)', w.map(x => [x.query, x.body]));
    ok(await flag(a.page, 'tc-chatpins-migrated') === '1', 'chat pins: …flag set');
    await reload(a);
    ok(pinW(a).length === 1 && J(await pins(a.page)) === J([C[1]]), 'chat pins: …and not again; the account’s pin is what the phone shows', pinW(a).length);
    /* pin the other chat from the phone: stamped; then unpin: null */
    await a.page.evaluate(id => A.pinChat(id), C[0]); await tick(a.page, 400);
    const w2 = pinW(a).at(-1);
    ok(cid(w2) === C[0] && typeof w2.body.pinned_at === 'string' && /Pinned/.test(await toastText(a.page)), 'chat pins: pinning from the phone stamps pinned_at', { w2, t: await toastText(a.page) });
    await a.page.evaluate(id => A.pinChat(id), C[0]); await tick(a.page, 400);
    const w3 = pinW(a).at(-1);
    ok(cid(w3) === C[0] && w3.body.pinned_at === null && /Unpinned/.test(await toastText(a.page)), 'chat pins: unpinning sets pinned_at to null', w3);
    await a.close();
  }
  /* the account has pins: they win, in the order they were pinned */
  {
    const m = FX.MEMBERS.map(r => r.user_id === ME.id ? Object.assign({}, r, r.conversation_id === C[0] ? { pinned_at: '2026-09-30T10:00:00Z' } : { pinned_at: '2026-09-29T10:00:00Z' }) : r);
    const a = await app({ tables: withTables({ conversation_members: m }), init: seed({ ['tc-chat-pins-' + ME.id]: [C[1]], ['tc-chatpins-migrated:' + ME.id]: '1' }) });
    ok(J(await pins(a.page)) === J([C[1], C[0]]) && pinW(a).length === 0, 'chat pins: the account’s pins win and keep their order (oldest pin first); nothing is written', { p: await pins(a.page), w: pinW(a).length });
    await a.close();
  }
  /* unpinned elsewhere + already migrated: the phone drops its old pin */
  {
    const a = await app({ init: seed({ ['tc-chat-pins-' + ME.id]: [C[1]], ['tc-chatpins-migrated:' + ME.id]: '1' }) });
    ok((await pins(a.page)).length === 0 && pinW(a).length === 0, 'chat pins: migrated + none on the account => the phone’s old pin is dropped, not re-uploaded', { p: await pins(a.page), w: pinW(a).length });
    await a.close();
  }
  /* column missing / not granted: local only, as before — whether the read or the write says so */
  for (const [what, hk] of [['the read', (url, m) => m === 'GET' && /pinned_at/.test(dq(url.search)) ? gapCol : null], ['the write', (url, m, body) => m === 'PATCH' && body && 'pinned_at' in body ? gapCol : null]]) {
    const a = await app({ init: seed({ ['tc-chat-pins-' + ME.id]: [C[1]] }), hook: hk });
    await a.page.evaluate(id => A.pinChat(id), C[0]); await tick(a.page, 400);
    ok(J(await pins(a.page)) === J([C[1], C[0]]) && /Pinned/.test(await toastText(a.page)) && await flag(a.page, 'tc-chatpins-dirty') === null, 'chat pins: pinned_at missing (42703) on ' + what + ' => pins work on this phone, nothing flagged', { p: await pins(a.page), d: await flag(a.page, 'tc-chatpins-dirty') });
    ok(a.log.errors.length === 0, 'chat pins: …no page errors (' + what + ')', a.log.errors);
    await a.close();
  }
  /* a write that fails on the network is remembered and goes up next load */
  {
    let down = true;
    const a = await app({ init: seed({ ['tc-chatpins-migrated:' + ME.id]: '1' }), hook: (url, m, body) => down && m === 'PATCH' && body && 'pinned_at' in body ? boom : null });
    await a.page.evaluate(id => A.pinChat(id), C[0]); await tick(a.page, 400);
    ok(await flag(a.page, 'tc-chatpins-dirty') === '1', 'chat pins: a failed write leaves tc-chatpins-dirty', await flag(a.page, 'tc-chatpins-dirty'));
    down = false; await reload(a);
    ok(pinW(a).length === 1 && cid(pinW(a)[0]) === C[0] && J(await pins(a.page)) === J([C[0]]) && await flag(a.page, 'tc-chatpins-dirty') === null, 'chat pins: …next load pushes the phone’s pin instead of reading the older list over it', { w: pinW(a).length, p: await pins(a.page) });
    await a.close();
  }
} catch (e) { ok(false, 'section crashed: ' + e.message); }

/* ------------------------------------------------------------------ 6. plans keep unknown class numbers */
if (want('plan')) try {
  const a = await app({ init: seed({}) });
  const planW = () => wr(a, 'plans', 'POST');
  const known = await a.page.evaluate(() => TC.plans.B.slice());
  ok(known.length === 2 && known.includes('79999'), 'plan: set-up — Plan B holds a real class and 79999 (BUS 9999), which the seat feed does not have', known);
  await a.page.evaluate(() => TC.setPlan('B', TC.plans.B.concat([])) ); await tick(a.page, 800);
  let w = planW().at(-1);
  ok(w && w.body.sections.some(s => s.class_nbr === '79999' && s.code === 'BUS 9999') && w.body.sections.length === 2, 'plan: saving the plan keeps the class number the seat feed doesn’t have (original object)', w && w.body);
  const real = known.find(x => x !== '79999');
  await a.page.evaluate(id => TC.setPlan('B', TC.plans.B.filter(x => x !== id)), real); await tick(a.page, 800);
  w = planW().at(-1);
  ok(w && J(w.body.sections) === J([{ code: 'BUS 9999', class_nbr: '79999' }]), 'plan: removing the known class sends only what is left — the unknown one stays', w && w.body);
  await a.page.evaluate(() => TC.setPlanShared('B', false)); await tick(a.page, 500);
  w = planW().at(-1);
  ok(w && w.body.shared === false && w.body.sections.some(s => s.class_nbr === '79999'), 'plan: the share switch keeps it too', w && w.body);
  await a.close();
} catch (e) { ok(false, 'section crashed: ' + e.message); }

/* ------------------------------------------------------------------ 7. push settings */
if (want('push')) try {
  const PP = (seats, prefs) => withTables({ push_prefs: [{ user_id: ME.id, prefs: prefs || {}, seats }] });
  const pp = a => wr(a, 'push_prefs').filter(w => w.body && w.body.prefs);
  {
    const a = await app({ tables: PP(false, {}), init: seed({}) });
    const st = await a.page.evaluate(() => ({ on: pushPrefOn('seat_open'), prefs: TC.push.prefs }));
    ok(a.log.reads.some(r => /^push_prefs\?/.test(r) && /select=prefs(,|%2C)seats/.test(r)), 'push: both the per-kind choices and the website’s seats column are read', a.log.reads.filter(r => /push_prefs/.test(r)));
    ok(st.on === false, 'push: the website turned seat alerts OFF => the phone shows A seat opens off', st);
    await a.page.evaluate(() => A.pushPref('seat_open')); await tick(a.page, 500);
    const w = pp(a).at(-1);
    ok(w && w.body.seats === true && !('seat_open' in w.body.prefs), 'push: switching it ON writes prefs (no seat_open) AND seats:true', w && w.body);
    await a.page.evaluate(() => A.pushPref('seat_open')); await tick(a.page, 500);
    const w2 = pp(a).at(-1);
    ok(w2 && w2.body.seats === false && w2.body.prefs.seat_open === false, 'push: switching it OFF writes prefs.seat_open:false AND seats:false', w2 && w2.body);
    await a.page.evaluate(() => A.pushPref('dm')); await tick(a.page, 500);
    const w3 = pp(a).at(-1);
    ok(w3 && !('seats' in w3.body) && w3.body.prefs.dm === false, 'push: another switch (messages) does not touch the website’s seats column', w3 && w3.body);
    await a.close();
  }
  {
    const a = await app({ tables: PP(true, { seat_open: false }), init: seed({}) });
    ok(await a.page.evaluate(() => pushPrefOn('seat_open')) === false, 'push: off on the phone (prefs) is off here, whatever seats says (never turns an alert back on)');
    await a.close();
  }
  {
    const a = await app({ tables: PP(true, {}), init: seed({}) });
    ok(await a.page.evaluate(() => pushPrefOn('seat_open')) === true && pp(a).length === 0, 'push: both on => on, and loading writes nothing');
    await a.close();
  }
} catch (e) { ok(false, 'section crashed: ' + e.message); }

console.log(`\ncheck-app-sync-2026-10-15: ${pass} passed, ${fail} failed`);
process.exit(fail ? 1 : 0);
