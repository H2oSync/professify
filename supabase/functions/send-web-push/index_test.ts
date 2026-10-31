// Run: SEND_WEB_PUSH_TEST=1 deno test -A functions/send-web-push/index_test.ts
// No network: every push service is a fake fetch. The crypto is checked for real — the body the
// function produces is DECRYPTED with an independent RFC 8188 implementation (npm:http_ece) using
// a browser-side key pair, and the VAPID JWT signature is verified with WebCrypto.
import nodeAssert from 'node:assert/strict';
// node:assert instead of jsr:@std/assert so the test also runs where jsr.io is unreachable.
const assert = (v: unknown, msg?: string) => nodeAssert.ok(v, msg);
const assertEquals = (a: unknown, b: unknown) => nodeAssert.deepStrictEqual(a, b);
const assertMatch = (s: string, re: RegExp) => nodeAssert.match(s, re);
import ece from 'npm:http_ece@1.2.1';
import webpush from 'npm:web-push@3.6.7';
import { createECDH, randomBytes } from 'node:crypto';
import { Buffer } from 'node:buffer';
import { buildPayload, classify, handle, sameSecret, sendOne, sendOptions, vapidProblem, type Row, type Sub } from './index.ts';

const b64u = (b: Uint8Array) => Buffer.from(b).toString('base64').replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
const unb64u = (s: string) => new Uint8Array(Buffer.from(s.replace(/-/g, '+').replace(/_/g, '/'), 'base64'));

const V = webpush.generateVAPIDKeys();
const vapid = { subject: 'mailto:hello@termchamp.com', publicKey: V.publicKey, privateKey: V.privateKey };

function browser() {   // what a browser's pushManager.subscribe() produces
  const ecdh = createECDH('prime256v1'); ecdh.generateKeys();
  const auth = randomBytes(16);
  return { ecdh, auth, keys: { p256dh: b64u(ecdh.getPublicKey()), auth: b64u(auth) } };
}

Deno.test('payload matches what sw.js reads', () => {
  const p = JSON.parse(buildPayload({ kind: 'seat_open', title: 'CSC 357 §02 has a seat', body: 'One seat just opened.', url: '/?tab=sched', tag: 'seat-4021' }));
  assertEquals(p, { title: 'CSC 357 §02 has a seat', body: 'One seat just opened.', url: '/?tab=sched', tag: 'seat-4021', kind: 'seat_open', renotify: true });
  assertEquals(JSON.parse(buildPayload({ kind: 'moved', title: '', body: '', url: '//evil.example', tag: null })).url, '/');
  assertEquals(JSON.parse(buildPayload({ kind: 'moved', title: '', body: '', url: 'https://evil.example', tag: null })).tag, 'moved');
  assert(buildPayload({ kind: 'x', title: 'a'.repeat(999), body: 'b'.repeat(9999), url: '/', tag: 't' }).length < 1000);
});

Deno.test('send options: urgency, TTL, topic sanitised', () => {
  const a = sendOptions({ kind: 'seat_open', tag: 'seat-4021' }, vapid);
  assertEquals([a.urgency, a.TTL, (a as { topic?: string }).topic], ['high', 21600, 'seat-4021']);
  const b = sendOptions({ kind: 'moved', tag: 'moved-§ 12/3' + 'x'.repeat(60) }, vapid);
  assertEquals(b.urgency, 'normal'); assertEquals(b.TTL, 86400);
  assertMatch((b as { topic?: string }).topic!, /^[A-Za-z0-9_-]{1,32}$/);
});

Deno.test('status classification', () => {
  assertEquals(classify(201, '').ok, true);
  for (const s of [404, 410]) { const r = classify(s, 'gone'); assert(!r.ok && r.dead && !r.auth); }
  for (const s of [401, 403]) { const r = classify(s, ''); assert(!r.ok && r.auth && !r.dead); }
  for (const s of [400, 413, 429, 500, 503]) { const r = classify(s, ''); assert(!r.ok && !r.dead && !r.auth); }
});

Deno.test('secret compare', () => {
  assert(sameSecret('abc', 'abc')); assert(!sameSecret('abc', 'abd')); assert(!sameSecret('', ''));
  assert(!sameSecret('abc', 'abc ')); assert(!sameSecret('abc\n', 'abc'));
});

Deno.test('VAPID config checks name the problem', () => {
  assertEquals(vapidProblem(vapid, V.publicKey), null);
  assertMatch(vapidProblem(vapid)!, /does not match the key in index.html/);           // real site key
  const other = webpush.generateVAPIDKeys();
  assertMatch(vapidProblem({ ...vapid, privateKey: other.privateKey }, V.publicKey)!, /does not pair/);
  assertMatch(vapidProblem({ ...vapid, privateKey: V.privateKey + ' ' }, V.publicKey)!, /whitespace/);
  assertMatch(vapidProblem({ ...vapid, subject: 'hello' }, V.publicKey)!, /VAPID_SUBJECT/);
  assertMatch(vapidProblem({ ...vapid, privateKey: '' }, V.publicKey)!, /must both be set/);
});

Deno.test('sendOne: body decrypts in the browser, VAPID JWT verifies', async () => {
  const br = browser();
  const sub: Sub = { id: 1, endpoint: 'https://fcm.googleapis.com/fcm/send/abc123', ...br.keys };
  const payload = buildPayload({ kind: 'seat_open', title: 'T', body: 'B', url: '/?tab=sched', tag: 'seat-1' });
  let seen: { url: string; headers: Headers; body: Uint8Array } | null = null;
  const fake = (async (url: string, init: RequestInit) => {
    seen = { url, headers: new Headers(init.headers), body: new Uint8Array(init.body as ArrayBuffer) };
    return new Response(null, { status: 201 });
  }) as unknown as typeof fetch;
  const r = await sendOne(sub, payload, sendOptions({ kind: 'seat_open', tag: 'seat-1' }, vapid), fake);
  assert(r.ok);
  const s = seen!;
  assertEquals(s.url, sub.endpoint);
  assertEquals(s.headers.get('content-encoding'), 'aes128gcm');
  assertEquals(s.headers.get('urgency'), 'high');
  assertEquals(s.headers.get('ttl'), '21600');
  assertEquals(s.headers.get('topic'), 'seat-1');
  // Decrypt exactly as the browser would.
  const plain = ece.decrypt(Buffer.from(s.body), { version: 'aes128gcm', privateKey: br.ecdh, authSecret: br.auth });
  assertEquals(plain.toString('utf8'), payload);
  // Authorization: vapid t=<jwt>, k=<our public key>
  const m = /^vapid t=([^,]+), k=(.+)$/.exec(s.headers.get('authorization') ?? '');
  assert(m, 'vapid authorization header');
  assertEquals(m![2], V.publicKey);
  const [h, c, sig] = m![1].split('.');
  const claims = JSON.parse(new TextDecoder().decode(unb64u(c)));
  assertEquals(claims.aud, 'https://fcm.googleapis.com'); assertEquals(claims.sub, vapid.subject);
  assert(claims.exp > Date.now() / 1000 && claims.exp <= Date.now() / 1000 + 24 * 3600 + 5);
  const key = await crypto.subtle.importKey('raw', unb64u(V.publicKey), { name: 'ECDSA', namedCurve: 'P-256' }, false, ['verify']);
  assert(await crypto.subtle.verify({ name: 'ECDSA', hash: 'SHA-256' }, key, unb64u(sig), new TextEncoder().encode(`${h}.${c}`)));
});

Deno.test('sendOne refuses non-push-service endpoints and bad keys without fetching', async () => {
  let calls = 0; const fake = (async () => { calls++; return new Response(null, { status: 201 }); }) as unknown as typeof fetch;
  const br = browser();
  for (const ep of ['https://attacker.example/x', 'http://fcm.googleapis.com/fcm/send/a', 'https://fcm.googleapis.com.evil.io/a', 'https://169.254.169.254/latest']) {
    const r = await sendOne({ id: 1, endpoint: ep, ...br.keys }, '{}', sendOptions({ kind: 'moved', tag: null }, vapid), fake);
    assert(!r.ok && r.dead, ep);
  }
  const r = await sendOne({ id: 1, endpoint: 'https://web.push.apple.com/abc', p256dh: 'nope', auth: 'x' }, '{}', sendOptions({ kind: 'moved', tag: null }, vapid), fake);
  assert(!r.ok && r.dead);
  assertEquals(calls, 0);
});

// ---- handler with a fake database -----------------------------------------------------------------
function fakeDb(rows: Row[]) {
  const log: Array<{ table: string; op: string; vals?: unknown; where: Array<[string, string, unknown]> }> = [];
  let rpcCalls = 0;
  const builder = (table: string) => {
    const e = { table, op: '', vals: undefined as unknown, where: [] as Array<[string, string, unknown]> };
    const b: Record<string, unknown> = {
      update(v: unknown) { e.op = 'update'; e.vals = v; log.push(e); return b; },
      delete() { e.op = 'delete'; log.push(e); return b; },
      select() { if (!e.op) { e.op = 'select'; log.push(e); } return b; },
      eq(c: string, v: unknown) { e.where.push(['eq', c, v]); return b; },
      in(c: string, v: unknown) { e.where.push(['in', c, v]); return b; },
      gte(c: string, v: unknown) { e.where.push(['gte', c, v]); return b; },
      is(c: string, v: unknown) { e.where.push(['is', c, v]); return b; },
      then(res: (x: unknown) => void) { res({ data: [], error: null, count: 7 }); },
    };
    return b;
  };
  return { log, get rpcCalls() { return rpcCalls; },
    rpc: async (name: string, args: { p_limit: number }) => { rpcCalls++; assertEquals(name, 'push_web_claim_subs'); assertEquals(args.p_limit, 100); return { data: rows, error: null }; },
    from: builder };
}
const envFor = (pub = V.publicKey) => (k: string) => ({ PUSH_SECRET: 's3cret', VAPID_PUBLIC_KEY: pub, VAPID_PRIVATE_KEY: V.privateKey, VAPID_SUBJECT: 'mailto:hello@termchamp.com' } as Record<string, string>)[k];
const req = (secret = 's3cret', body = '{}') => new Request('http://x/', { method: 'POST', headers: { 'x-push-secret': secret }, body });

// handle() checks against SITE_VAPID_PUBLIC (the real site key), so for handler tests stub the
// check by giving the env the real site public key and expect the pairing check to fail — and
// separately run the happy path through a module-level override below.
Deno.test('handler: 401 on wrong/missing secret, 500 on VAPID mismatch BEFORE claiming', async () => {
  const db = fakeDb([]);
  assertEquals((await handle(req('wrong'), { db, env: envFor() })).status, 401);
  assertEquals((await handle(new Request('http://x/', { method: 'POST' }), { db, env: envFor() })).status, 401);
  const r = await handle(req(), { db, env: envFor() });          // our test private key != site key
  assertEquals(r.status, 500);
  assertMatch((await r.json()).error, /does not match the key in index.html/);
  assertEquals(db.rpcCalls, 0);
});

Deno.test('handler: sent / dead (deleted) / transient / no-subscription rows recorded correctly', async () => {
  const b1 = browser(), b2 = browser(), b3 = browser();
  const ok: Sub = { id: 11, endpoint: 'https://fcm.googleapis.com/fcm/send/ok', ...b1.keys, fail_count: 2 };
  const gone: Sub = { id: 12, endpoint: 'https://updates.push.services.mozilla.com/wpush/v2/gone', ...b2.keys, fail_count: 0 };
  const flaky: Sub = { id: 13, endpoint: 'https://web.push.apple.com/flaky', ...b3.keys, fail_count: 4 };
  const base = { user_id: 'u', title: 't', body: 'b', url: '/?tab=sched', attempts: 1 };
  const rows: Row[] = [
    { ...base, id: 1, kind: 'seat_open', tag: 'seat-1', subs: [ok, gone] },   // ok + dead -> sent, gone deleted
    { ...base, id: 2, kind: 'waitlist', tag: 'wl-1', subs: [gone] },          // gone already dead -> no subscription
    { ...base, id: 3, kind: 'moved', tag: 'moved-1', subs: [flaky] },         // 503 -> failed, retried later
    { ...base, id: 4, kind: 'moved', tag: 'moved-2', subs: [] },              // no subs
  ];
  const status: Record<string, number> = { [ok.endpoint]: 201, [gone.endpoint]: 410, [flaky.endpoint]: 503 };
  const hits: string[] = [];
  const fake = (async (url: string) => { hits.push(url); return new Response('x', { status: status[url] }); }) as unknown as typeof fetch;
  const db = fakeDb(rows);
  const r = await handle(req(), { db, env: envFor(), fetch: fake, sitePublic: V.publicKey });
  const out = await r.json();
  assertEquals(r.status, 200);
  assertEquals(out, { claimed: 4, sent: 1, failed: 1, no_subscription: 2, subs_removed: 1, error: '' });
  assertEquals(hits, [ok.endpoint, gone.endpoint, flaky.endpoint]);    // dead endpoint not retried for row 2
  const upd = (t: string, id: number) => db.log.find((e) => e.table === t && e.op === 'update' && e.where.some((w) => w[1] === 'id' && w[2] === id));
  assertEquals((upd('push_outbox', 1)!.vals as { last_error: unknown }).last_error, null);
  assert((upd('push_outbox', 1)!.vals as { sent_at?: string }).sent_at);
  assertMatch((upd('push_outbox', 2)!.vals as { last_error: string }).last_error, /no subscription/);
  const u3 = upd('push_outbox', 3)!.vals as { sent_at?: string; last_error: string };
  assertEquals(u3.sent_at, undefined); assertMatch(u3.last_error, /^503/);
  assertMatch((upd('push_outbox', 4)!.vals as { last_error: string }).last_error, /no subscription/);
  assertEquals((upd('push_subscriptions', 11)!.vals as { fail_count: number }).fail_count, 0);
  assertEquals((upd('push_subscriptions', 13)!.vals as { fail_count: number }).fail_count, 5);
  const del = db.log.find((e) => e.table === 'push_subscriptions' && e.op === 'delete' && e.where[0][1] === 'id')!;
  assertEquals(del.where[0][2], [12]);
});

Deno.test('handler: repeated 401/403 with nothing sent stops the run and returns 500', async () => {
  const subs = [1, 2, 3, 4, 5].map((i) => ({ id: i, endpoint: 'https://fcm.googleapis.com/fcm/send/' + i, ...browser().keys }));
  const rows: Row[] = subs.map((s, i) => ({ id: i + 1, user_id: 'u', kind: 'seat_open', title: 't', body: 'b', url: '/', tag: 's', attempts: 1, subs: [s] }));
  let n = 0;
  const fake = (async () => { n++; return new Response('bad jwt', { status: 403 }); }) as unknown as typeof fetch;
  const r = await handle(req(), { db: fakeDb(rows), env: envFor(), fetch: fake, sitePublic: V.publicKey });
  assertEquals(r.status, 500);
  assertMatch((await r.json()).error, /VAPID key/);
  assertEquals(n, 3);
});

Deno.test('handler: dry_run checks config and claims nothing', async () => {
  const db = fakeDb([]);
  const r = await handle(req('s3cret', '{"dry_run":true}'), { db, env: envFor(), sitePublic: V.publicKey });
  assertEquals((await r.json()), { dry_run: true, vapid: 'ok', unsent_rows: 7, error: '' });
  assertEquals(db.rpcCalls, 0);
});

Deno.test('handler: a secret saved with a trailing space is named, not silently 401', async () => {
  const env = (k: string) => k === 'PUSH_SECRET' ? 's3cret ' : envFor()(k);
  const r = await handle(req('s3cret '), { db: fakeDb([]), env, sitePublic: V.publicKey });
  assertEquals(r.status, 500); assertMatch((await r.json()).error, /whitespace/);
});
