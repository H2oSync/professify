// deno test --allow-env supabase/functions/send-push/index_test.ts
// A fake database and a fake Apple. Proves: the secret is required, each queued row reaches every
// phone with its tap target, dead phones are removed, a bad key stops the run, no-phone rows close.
Deno.env.set('SUPABASE_URL', 'http://x'); Deno.env.set('SUPABASE_SERVICE_ROLE_KEY', 'k'); Deno.env.set('PUSH_SECRET', 'sekrit');
Deno.env.set('APNS_KEY_ID', 'ABC123DEFG'); Deno.env.set('APNS_TEAM_ID', 'TEAM123456'); Deno.env.set('APNS_PRIVATE_KEY', 'x'); Deno.env.set('APNS_BUNDLE_ID', 'com.termchamp.app');
const { handle } = await import('./index.ts');

const assert = (c: unknown, m: string) => { if (!c) throw new Error(m); };
const req = (secret = 'sekrit') => new Request('http://x/send-push', { method: 'POST', headers: { 'x-push-secret': secret } });

function fakeDb(rows: unknown[]) {
  const log: Array<{ table: string; op: string; val?: unknown; key?: unknown }> = [];
  const table = (name: string) => ({
    update: (val: unknown) => ({ eq: (_c: string, key: unknown) => { log.push({ table: name, op: 'update', val, key }); return Promise.resolve({}); } }),
    delete: () => ({ in: (_c: string, key: unknown) => { log.push({ table: name, op: 'delete', key }); return Promise.resolve({}); } }),
  });
  return { log, db: { rpc: (_fn: string) => Promise.resolve({ data: rows, error: null }), from: table } };
}
const row = (id: number, tokens: Array<{ token: string; env: string | null }>) =>
  ({ id, user_id: 'u' + id, kind: 'dm', title: 'Alex', body: 'hey', data: { t: 'chat', id: 'c1' }, thread: 'chat:c1', tries: 1, tokens });

Deno.test('no secret, no run', async () => {
  const { db } = fakeDb([]);
  assert((await handle(req('wrong'), { db, send: () => { throw new Error('sent'); } })).status === 401, 'should be 401');
});

Deno.test('sends to every phone with the tap target, learns env, closes the row', async () => {
  const { db, log } = fakeDb([row(1, [{ token: 'a1', env: null }, { token: 'b2', env: 'production' }])]);
  const sent: Array<{ token: string; extra: unknown; thread?: string }> = [];
  const send = (_c: unknown, token: string, _env: string | null, m: { extra?: unknown; thread?: string }) => {
    sent.push({ token, extra: m.extra, thread: m.thread });
    return Promise.resolve({ ok: true as const, env: token === 'a1' ? 'sandbox' as const : 'production' as const });
  };
  const res = await (await handle(req(), { db, send })).json();
  assert(res.sent === 1 && sent.length === 2, 'both phones, one row ' + JSON.stringify(res));
  assert(JSON.stringify(sent[0].extra) === JSON.stringify({ tc: { t: 'chat', id: 'c1' } }) && sent[0].thread === 'chat:c1', 'tc + thread');
  assert(log.some((l) => l.table === 'push_tokens' && l.op === 'update' && l.key === 'a1'), 'env learned for a1 only');
  assert(!log.some((l) => l.table === 'push_tokens' && l.op === 'update' && l.key === 'b2'), 'b2 env unchanged');
  assert(log.some((l) => l.table === 'push_queue' && (l.val as { sent_at?: string }).sent_at && l.key === 1), 'row 1 sent');
});

Deno.test('a gone phone is deleted; a row with no phones is closed', async () => {
  const { db, log } = fakeDb([row(1, [{ token: 'dead', env: 'production' }]), row(2, [])]);
  const send = () => Promise.resolve({ ok: false as const, dead: true, fatal: false, error: 'production 410 Unregistered' });
  const res = await (await handle(req(), { db, send })).json();
  assert(res.failed === 1 && res.no_phones === 1 && res.tokens_removed === 1, JSON.stringify(res));
  assert(log.some((l) => l.table === 'push_tokens' && l.op === 'delete' && JSON.stringify(l.key) === '["dead"]'), 'token deleted');
  assert(log.some((l) => l.table === 'push_queue' && l.key === 2 && (l.val as { error?: string }).error === 'no phones'), 'row 2 closed');
});

Deno.test('Apple refuses our key: stop, 500, rows left for retry', async () => {
  const { db, log } = fakeDb([row(1, [{ token: 'a', env: null }]), row(2, [{ token: 'b', env: null }])]);
  let calls = 0;
  const send = () => { calls++; return Promise.resolve({ ok: false as const, dead: false, fatal: true, error: 'production 403 InvalidProviderToken' }); };
  const r = await handle(req(), { db, send });
  assert(r.status === 500 && calls === 1, 'stopped after the first refusal');
  assert(!log.some((l) => l.table === 'push_queue' && (l.val as { sent_at?: string }).sent_at), 'nothing marked sent');
});
