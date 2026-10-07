// deno test supabase/functions/_shared/apns_test.ts
// No network: APNs is a fake fetch, the key is generated here. Proves the JWT verifies against the
// key's public half, and that each APNs answer leads to the right action.
import { apnsJwt, apnsSend, apnsPayload, type ApnsConfig } from './apns.ts';

const assert = (c: unknown, m: string) => { if (!c) throw new Error(m); };
const eq = (a: unknown, b: unknown, m: string) => assert(JSON.stringify(a) === JSON.stringify(b), `${m}: ${JSON.stringify(a)} !== ${JSON.stringify(b)}`);

async function makeCfg(): Promise<{ cfg: ApnsConfig; pub: CryptoKey }> {
  const kp = await crypto.subtle.generateKey({ name: 'ECDSA', namedCurve: 'P-256' }, true, ['sign', 'verify']);
  const der = new Uint8Array(await crypto.subtle.exportKey('pkcs8', kp.privateKey));
  let s = ''; for (const x of der) s += String.fromCharCode(x);
  const pem = `-----BEGIN PRIVATE KEY-----\n${btoa(s).replace(/(.{64})/g, '$1\n')}\n-----END PRIVATE KEY-----`;
  return { cfg: { keyId: 'ABC123DEFG', teamId: 'TEAM123456', privateKey: pem, bundleId: 'com.termchamp.app' }, pub: kp.publicKey };
}
const unb64 = (s: string) => Uint8Array.from(atob(s.replace(/-/g, '+').replace(/_/g, '/') + '==='.slice((s.length + 3) % 4)), (c) => c.charCodeAt(0));
const msg = { title: 'Seat open: BUS 3431 Sec 01', body: 'A seat just opened.', kind: 'seat_open', thread: 'seats', extra: { tc: { t: 'class', code: 'BUS 3431' } } };
const TOKEN = 'ab'.repeat(32);

function fakeFetch(answers: Record<string, { status: number; reason?: string }>) {
  const calls: Array<{ url: string; headers: Record<string, string>; body: unknown }> = [];
  const f = (async (url: string, init: RequestInit) => {
    calls.push({ url, headers: init.headers as Record<string, string>, body: JSON.parse(String(init.body)) });
    const host = url.includes('sandbox') ? 'sandbox' : 'production';
    const a = answers[host] ?? { status: 200 };
    return new Response(a.reason ? JSON.stringify({ reason: a.reason }) : '', { status: a.status });
  }) as unknown as typeof fetch;
  return { f, calls };
}

Deno.test('JWT is ES256, carries kid/iss, and verifies with the public key', async () => {
  const { cfg, pub } = await makeCfg();
  const jwt = await apnsJwt(cfg, Date.now() + 99 * 3600 * 1000);   // far future: forces a fresh one
  const [h, c, sig] = jwt.split('.');
  eq(JSON.parse(new TextDecoder().decode(unb64(h))), { alg: 'ES256', kid: 'ABC123DEFG' }, 'header');
  eq(JSON.parse(new TextDecoder().decode(unb64(c))).iss, 'TEAM123456', 'iss');
  const ok = await crypto.subtle.verify({ name: 'ECDSA', hash: 'SHA-256' }, pub, unb64(sig), new TextEncoder().encode(`${h}.${c}`));
  assert(ok, 'signature does not verify');
});

Deno.test('a working production token: one request, right headers and body', async () => {
  const { cfg } = await makeCfg();
  const { f, calls } = fakeFetch({ production: { status: 200 } });
  const r = await apnsSend(cfg, TOKEN, null, msg, f);
  eq(r, { ok: true, env: 'production' }, 'result');
  eq(calls.length, 1, 'calls');
  assert(calls[0].url === `https://api.push.apple.com/3/device/${TOKEN}`, 'url');
  eq(calls[0].headers['apns-topic'], 'com.termchamp.app', 'topic');
  eq(calls[0].headers['apns-push-type'], 'alert', 'push type');
  eq(calls[0].body, apnsPayload(msg), 'payload');
  eq((calls[0].body as { tc: unknown }).tc, { t: 'class', code: 'BUS 3431' }, 'tap target rides at the top level as tc');
  eq((calls[0].body as { aps: { 'thread-id': string } }).aps['thread-id'], 'seats', 'thread id');
  assert(!('apns-collapse-id' in calls[0].headers), 'no collapse id unless asked');
});

Deno.test('an Xcode build token: production says BadDeviceToken, sandbox works, env learned', async () => {
  const { cfg } = await makeCfg();
  const { f, calls } = fakeFetch({ production: { status: 400, reason: 'BadDeviceToken' }, sandbox: { status: 200 } });
  eq(await apnsSend(cfg, TOKEN, null, msg, f), { ok: true, env: 'sandbox' }, 'result');
  eq(calls.length, 2, 'tried both');
});

Deno.test('known sandbox token goes straight to sandbox', async () => {
  const { cfg } = await makeCfg();
  const { f, calls } = fakeFetch({ sandbox: { status: 200 } });
  eq(await apnsSend(cfg, TOKEN, 'sandbox', msg, f), { ok: true, env: 'sandbox' }, 'result');
  eq(calls.length, 1, 'one call'); assert(calls[0].url.includes('sandbox'), 'sandbox host');
});

Deno.test('uninstalled app (410) is dead, not retried', async () => {
  const { cfg } = await makeCfg();
  const { f } = fakeFetch({ production: { status: 410, reason: 'Unregistered' } });
  const r = await apnsSend(cfg, TOKEN, 'production', msg, f);
  assert(!r.ok && r.dead && !r.fatal, 'should be dead');
});

Deno.test('bad on both environments is dead', async () => {
  const { cfg } = await makeCfg();
  const { f } = fakeFetch({ production: { status: 400, reason: 'BadDeviceToken' }, sandbox: { status: 400, reason: 'BadDeviceToken' } });
  const r = await apnsSend(cfg, TOKEN, null, msg, f);
  assert(!r.ok && r.dead && !r.fatal, 'should be dead');
});

Deno.test('wrong key/team (403) is fatal for the run, and the token is kept', async () => {
  const { cfg } = await makeCfg();
  const { f } = fakeFetch({ production: { status: 403, reason: 'InvalidProviderToken' } });
  const r = await apnsSend(cfg, TOKEN, 'production', msg, f);
  assert(!r.ok && r.fatal && !r.dead, 'should be fatal, not dead');
});

Deno.test('Apple overloaded (429/503) is a retry next run', async () => {
  const { cfg } = await makeCfg();
  for (const status of [429, 503]) {
    const { f } = fakeFetch({ production: { status } });
    const r = await apnsSend(cfg, TOKEN, 'production', msg, f);
    assert(!r.ok && !r.dead && !r.fatal, `status ${status} should be transient`);
  }
});
