// ================================================================================================
// send-push — Supabase Edge Function (Deno) — the iPhone app's notifications (6 October 2026)
// ================================================================================================
// sql/termchamp-push.sql's triggers queue rows in public.push_queue and poke this function through
// pg_net (and a cron job pokes it every minute for anything delayed or retried). This claims a
// batch with push_claim(), which hands back each row WITH that student's phone tokens, sends each
// to Apple, and records what happened.
//
// SECRETS (Supabase → Edge Functions → Secrets)
//   PUSH_SECRET       the same long random string as push_config 'secret' — the trigger sends it
//                     as x-push-secret, and nothing else may run this
//   APNS_KEY_ID, APNS_TEAM_ID, APNS_PRIVATE_KEY, APNS_BUNDLE_ID   — see ../_shared/apns.ts
//
// DEPLOY
//   supabase functions deploy send-push --project-ref rqkndeqbcahozidniesn --no-verify-jwt
//   (no JWT: the caller is the database, which proves itself with PUSH_SECRET instead)
//
// WHAT EACH ROW BECOMES. title/body are the banner. `data` (where a tap goes) rides in the payload
// as `tc`, which is where the app reads it. `thread` groups banners in Notification Center.
//
// OUTCOMES
//   sent to at least one phone   → sent_at set
//   the student has no phones    → sent_at set, error 'no phones' (they signed out everywhere)
//   a phone is gone (410 / bad)  → that token is deleted from push_tokens
//   Apple refuses our key (403)  → stop this run, leave the rows for the next poke, return 500
//   anything else                → error recorded; push_claim retries it (5 tries at most)
// ================================================================================================
import { createClient } from 'jsr:@supabase/supabase-js@2';
import { apnsConfigFromEnv, apnsSend } from '../_shared/apns.ts';

const SUPABASE_URL = Deno.env.get('SUPABASE_URL')!;
const SERVICE_KEY  = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!;
const SECRET       = Deno.env.get('PUSH_SECRET') ?? '';
const APNS         = apnsConfigFromEnv((k) => Deno.env.get(k));
const BATCH        = 100;

type Row = { id: number; user_id: string; kind: string; title: string; body: string;
  data: Record<string, unknown> | null; thread: string | null; tries: number;
  tokens: Array<{ token: string; env: string | null }> };

export async function handle(req: Request, deps = { db: null as unknown, send: apnsSend }): Promise<Response> {
  if (!SECRET || (req.headers.get('x-push-secret') ?? '') !== SECRET) return new Response('no', { status: 401 });
  if (!APNS) return json({ error: 'APNS_KEY_ID, APNS_TEAM_ID, APNS_PRIVATE_KEY and APNS_BUNDLE_ID must all be set' }, 500);

  // deno-lint-ignore no-explicit-any
  const db: any = deps.db ?? createClient(SUPABASE_URL, SERVICE_KEY, { auth: { persistSession: false } });
  const out = { claimed: 0, sent: 0, no_phones: 0, failed: 0, tokens_removed: 0, error: '' };

  const { data: rows, error } = await db.rpc('push_claim', { p_limit: BATCH });
  if (error) return json({ ...out, error: 'push_claim: ' + error.message }, 500);
  out.claimed = rows?.length ?? 0;

  const dead = new Set<string>();
  for (const row of (rows ?? []) as Row[]) {
    const phones = (row.tokens ?? []).filter((t) => t && t.token && !dead.has(t.token));
    if (!phones.length) {
      await db.from('push_queue').update({ sent_at: new Date().toISOString(), error: 'no phones' }).eq('id', row.id);
      out.no_phones++; continue;
    }
    let ok = false, last = '';
    for (const ph of phones) {
      const r = await deps.send(APNS, ph.token, ph.env, {
        title: row.title, body: row.body, kind: row.kind, thread: row.thread ?? undefined,
        extra: { tc: row.data ?? {} },
      });
      if (r.ok) {
        ok = true;
        if (ph.env !== r.env) await db.from('push_tokens').update({ env: r.env }).eq('token', ph.token);
      } else {
        last = r.error;
        if (r.dead) dead.add(ph.token);
        if (r.fatal) {
          // Our key is wrong: nothing else will go either. Leave this row and the rest of the batch
          // claimed; push_claim hands them out again in 2 minutes, up to 5 tries.
          await db.from('push_queue').update({ error: r.error.slice(0, 300) }).eq('id', row.id);
          if (dead.size) await db.from('push_tokens').delete().in('token', [...dead]);
          return json({ ...out, tokens_removed: dead.size, error: 'Apple refused the push key: ' + r.error }, 500);
        }
      }
    }
    if (ok) {
      await db.from('push_queue').update({ sent_at: new Date().toISOString(), error: null }).eq('id', row.id);
      out.sent++;
    } else {
      await db.from('push_queue').update({ error: last.slice(0, 300) }).eq('id', row.id);
      out.failed++;
    }
  }
  if (dead.size) {
    await db.from('push_tokens').delete().in('token', [...dead]);
    out.tokens_removed = dead.size;
  }
  return json(out);
}

function json(body: unknown, status = 200) {
  return new Response(JSON.stringify(body, null, 1), { status, headers: { 'content-type': 'application/json' } });
}

if (import.meta.main) Deno.serve((req) => handle(req));
