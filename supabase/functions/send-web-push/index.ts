// ================================================================================================
// send-web-push — Supabase Edge Function (Deno) — the WEBSITE's notifications (drafted 2026-10-30)
// ================================================================================================
// The website twin of send-push (which does the iPhone app through push_queue + APNs).
// course_seats' trigger push_seat_change -> push_enqueue writes public.push_outbox. Every minute
// cron job 'termchamp-web-push-due' runs push_web_kick_due(), which POSTs here with x-push-secret
// when something is due. This claims a batch with push_web_claim_subs() — each row comes WITH that
// student's browser subscriptions — encrypts each one for each browser (RFC 8291 aes128gcm, VAPID
// RFC 8292, via npm:web-push's generateRequestDetails), POSTs it with fetch, and records what
// happened. sw.js's 'push' handler shows it.
//
// SECRETS (Supabase -> Edge Functions -> Secrets; secrets are project-wide)
//   PUSH_SECRET        ALREADY SET for send-push. Same value as push_config 'secret'. Reused here.
//   VAPID_PUBLIC_KEY   must equal PROFESSIFY_CONFIG.VAPID_PUBLIC_KEY in index.html (checked below)
//   VAPID_PRIVATE_KEY  the private half of that pair. Never in the repo, the page, or a chat.
//   VAPID_SUBJECT      optional, default mailto:hello@termchamp.com
//   SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY are provided by Supabase.
//
// DEPLOY
//   supabase functions deploy send-web-push --project-ref rqkndeqbcahozidniesn --no-verify-jwt
//   (no JWT: the caller is the database, which proves itself with PUSH_SECRET instead)
//
// OUTCOMES per outbox row
//   reached at least one browser          -> sent_at = now(), last_error = null
//   every browser is gone (404/410)       -> those subscriptions deleted; sent_at set, 'all subscriptions gone'
//   no subscriptions left                 -> sent_at set, 'no subscription'
//   anything else (429, 5xx, network ...) -> last_error recorded; push_web_claim_subs hands it out
//                                            again after 10 minutes, 5 tries at most
//   push services refuse our VAPID key    -> stop the run, return 500 (every other send would fail too)
// ================================================================================================

import { createClient } from 'jsr:@supabase/supabase-js@2';
import webpush from 'npm:web-push@3.6.7';
import { createECDH } from 'node:crypto';
import { Buffer } from 'node:buffer';

// The public key the live site subscribes browsers with (index.html PROFESSIFY_CONFIG). A private
// key that does not pair with THIS key produces subscriptions that every push service rejects.
export const SITE_VAPID_PUBLIC =
  'BMVQLxL6nyuF6f3RAg16OgyYezAgGBKYqTVFsZbu-dvLuf-G1o1jTrJ0BKbMfHzUkx4UZDuxmOMH0cf4Di8rMt4';

const BATCH = 100;
// Same rule as the 2026-10-14 CHECK constraint push_subs_endpoint_is_push_service. Defence in depth:
// this function signs requests with our VAPID key, so it must never POST anywhere else.
const PUSH_HOST = /^https:\/\/(fcm\.googleapis\.com|updates\.push\.services\.mozilla\.com|web\.push\.apple\.com|([a-z0-9-]+\.)+push\.apple\.com|([a-z0-9-]+\.)+notify\.windows\.com)\/[^\s\\]*$/i;

export type Sub = { id: number; endpoint: string; p256dh: string; auth: string; fail_count?: number };
export type Row = { id: number; user_id: string; kind: string; title: string; body: string;
  url: string | null; tag: string | null; attempts: number; subs: Sub[] | null };
export type Vapid = { subject: string; publicKey: string; privateKey: string };
export type SendResult = { ok: true; status: number }
  | { ok: false; status: number; dead: boolean; auth: boolean; error: string };

// ---- pure helpers (unit-tested) -----------------------------------------------------------------
export function buildPayload(row: Pick<Row, 'kind' | 'title' | 'body' | 'url' | 'tag'>): string {
  const p = {
    title: String(row.title || 'TermChamp').slice(0, 120),
    body: String(row.body || '').slice(0, 200),
    url: typeof row.url === 'string' && row.url.startsWith('/') && !row.url.startsWith('//') ? row.url : '/',
    tag: String(row.tag || row.kind || 'termchamp').slice(0, 80),
    kind: row.kind,
    renotify: row.kind === 'seat_open',          // a second seat in the same section should buzz again
  };
  return JSON.stringify(p);                       // <= ~600 bytes; push services allow ~4 KB
}

export function sendOptions(row: Pick<Row, 'kind' | 'tag'>, vapid: Vapid) {
  const urgent = row.kind === 'seat_open' || row.kind === 'waitlist';
  // Topic: a newer message with the same topic replaces an undelivered older one at the push
  // service (phone asleep). Must be <= 32 chars of URL-safe base64 or web-push throws.
  const topic = String(row.tag || '').replace(/[^A-Za-z0-9_-]/g, '').slice(0, 32);
  return {
    vapidDetails: vapid,
    TTL: urgent ? 6 * 3600 : 24 * 3600,           // a seat alert older than 6h is noise
    urgency: urgent ? 'high' : 'normal',
    contentEncoding: 'aes128gcm',
    ...(topic ? { topic } : {}),
  };
}

export function classify(status: number, text: string): SendResult {
  if (status >= 200 && status < 300) return { ok: true, status };
  const error = `${status} ${text}`.trim().slice(0, 300);
  return { ok: false, status, error,
    dead: status === 404 || status === 410,      // the browser unsubscribed / expired: delete it
    auth: status === 401 || status === 403 };     // our VAPID JWT refused (or sub made with another key)
}

const b64urlToBuf = (s: string) => Buffer.from(s.replace(/-/g, '+').replace(/_/g, '/'), 'base64');
const bufToB64url = (b: Uint8Array) => Buffer.from(b).toString('base64')
  .replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');

/** null when the configuration is usable, otherwise a message that names the problem (never a value). */
export function vapidProblem(v: Partial<Vapid>, sitePublic = SITE_VAPID_PUBLIC): string | null {
  if (!v.publicKey || !v.privateKey) return 'VAPID_PUBLIC_KEY and VAPID_PRIVATE_KEY must both be set';
  if (v.publicKey !== v.publicKey.trim() || v.privateKey !== v.privateKey.trim())
    return 'a VAPID secret has leading/trailing whitespace';
  if (v.publicKey !== sitePublic) return 'VAPID_PUBLIC_KEY does not match the key in index.html';
  try {
    const ecdh = createECDH('prime256v1');
    ecdh.setPrivateKey(b64urlToBuf(v.privateKey));
    if (bufToB64url(ecdh.getPublicKey()) !== v.publicKey) return 'VAPID_PRIVATE_KEY does not pair with VAPID_PUBLIC_KEY';
  } catch (_) { return 'VAPID_PRIVATE_KEY is not a base64url P-256 private key'; }
  if (!/^(mailto:|https:\/\/)/.test(v.subject ?? '')) return 'VAPID_SUBJECT must start with mailto: or https://';
  return null;
}

// ---- one send ------------------------------------------------------------------------------------
export async function sendOne(sub: Sub, payload: string, opts: ReturnType<typeof sendOptions>,
  fetchFn: typeof fetch = fetch): Promise<SendResult> {
  if (!PUSH_HOST.test(sub.endpoint) || sub.endpoint.length > 2048)
    return { ok: false, status: 0, dead: true, auth: false, error: 'endpoint is not a push service' };
  let det: { method: string; headers: Record<string, string | number>; body: Uint8Array; endpoint: string };
  try {
    det = webpush.generateRequestDetails(
      { endpoint: sub.endpoint, keys: { p256dh: sub.p256dh, auth: sub.auth } }, payload, opts);
  } catch (e) {
    // Bad p256dh/auth (wrong length, not base64url): this subscription can never work.
    return { ok: false, status: 0, dead: true, auth: false, error: 'bad keys: ' + String((e as Error)?.message ?? e).slice(0, 200) };
  }
  const headers = new Headers();
  for (const [k, v] of Object.entries(det.headers)) if (k.toLowerCase() !== 'content-length') headers.set(k, String(v));
  try {
    const res = await fetchFn(det.endpoint, { method: 'POST', headers, body: new Uint8Array(det.body),
      signal: AbortSignal.timeout(10_000) });
    let text = '';
    if (res.status >= 300) { try { text = (await res.text()).slice(0, 200); } catch (_) { /* empty */ } }
    else { try { await res.body?.cancel(); } catch (_) { /* fine */ } }
    return classify(res.status, text);
  } catch (e) {
    return { ok: false, status: 0, dead: false, auth: false, error: 'network: ' + String((e as Error)?.message ?? e).slice(0, 200) };
  }
}

// ---- the handler -------------------------------------------------------------------------------
export function sameSecret(a: string, b: string): boolean {
  if (!a || a.length !== b.length) return false;
  let d = 0; for (let i = 0; i < a.length; i++) d |= a.charCodeAt(i) ^ b.charCodeAt(i);
  return d === 0;
}

type Deps = { db?: unknown; env?: (k: string) => string | undefined; fetch?: typeof fetch; sitePublic?: string };

export async function handle(req: Request, deps: Deps = {}): Promise<Response> {
  const env = deps.env ?? ((k: string) => Deno.env.get(k));
  const SECRET = env('PUSH_SECRET') ?? '';
  // Checked first: HTTP strips a header's surrounding whitespace, so such a secret could never match
  // and every call would be a silent 401 (the 2026-10-28 send-push outage). Says nothing about the value.
  if (SECRET !== SECRET.trim()) return json({ error: 'PUSH_SECRET has leading/trailing whitespace' }, 500);
  if (!SECRET || !sameSecret(req.headers.get('x-push-secret') ?? '', SECRET)) return new Response('no', { status: 401 });

  const vapid: Vapid = { subject: env('VAPID_SUBJECT') || 'mailto:hello@termchamp.com',
    publicKey: env('VAPID_PUBLIC_KEY') ?? '', privateKey: env('VAPID_PRIVATE_KEY') ?? '' };
  const problem = vapidProblem(vapid, deps.sitePublic ?? SITE_VAPID_PUBLIC);   // sitePublic: tests only
  if (problem) return json({ error: problem }, 500);          // before claiming: no tries are burnt

  // deno-lint-ignore no-explicit-any
  const db: any = deps.db ?? createClient(env('SUPABASE_URL')!, env('SUPABASE_SERVICE_ROLE_KEY')!,
    { auth: { persistSession: false } });
  const out = { claimed: 0, sent: 0, failed: 0, no_subscription: 0, subs_removed: 0, error: '' };

  let dry = false;
  try { dry = !!(await req.clone().json())?.dry_run; } catch (_) { /* no body */ }
  if (dry) {
    const { count, error } = await db.from('push_outbox').select('id', { count: 'exact', head: true }).is('sent_at', null);
    return json({ dry_run: true, vapid: 'ok', unsent_rows: count ?? null, error: error?.message ?? '' });
  }

  const { data: rows, error } = await db.rpc('push_web_claim_subs', { p_limit: BATCH });
  if (error) return json({ ...out, error: 'push_web_claim_subs: ' + error.message }, 500);
  out.claimed = rows?.length ?? 0;

  const dead = new Set<number>();        // subscription ids to delete
  const okSubs = new Set<number>();
  const failSubs = new Map<number, number>();   // id -> fail_count seen at claim
  let authFails = 0;
  const now = () => new Date().toISOString();

  for (const row of (rows ?? []) as Row[]) {
    const subs = (row.subs ?? []).filter((s) => s && s.endpoint && !dead.has(s.id));
    if (!subs.length) {
      await db.from('push_outbox').update({ sent_at: now(), last_error: 'no subscription' }).eq('id', row.id);
      out.no_subscription++; continue;
    }
    const payload = buildPayload(row);
    const opts = sendOptions(row, vapid);
    let ok = false, allDead = true, last = '';
    for (const s of subs) {
      const r = await sendOne(s, payload, opts, deps.fetch ?? fetch);
      if (r.ok) { ok = true; allDead = false; okSubs.add(s.id); failSubs.delete(s.id); continue; }
      last = r.error;
      if (r.dead) { dead.add(s.id); continue; }
      allDead = false;
      if (!okSubs.has(s.id)) failSubs.set(s.id, s.fail_count ?? 0);
      if (r.auth) authFails++;
    }
    if (ok) {
      await db.from('push_outbox').update({ sent_at: now(), last_error: null }).eq('id', row.id);
      out.sent++;
    } else if (allDead) {
      await db.from('push_outbox').update({ sent_at: now(), last_error: 'all subscriptions gone: ' + last.slice(0, 200) }).eq('id', row.id);
      out.no_subscription++;
    } else {
      await db.from('push_outbox').update({ last_error: last.slice(0, 300) }).eq('id', row.id);
      out.failed++;
    }
    if (authFails >= 3 && out.sent === 0) {
      out.error = 'push services refused our VAPID key (401/403) — check VAPID_PRIVATE_KEY/VAPID_SUBJECT: ' + last.slice(0, 120);
      break;   // the rest stay claimed and are handed out again in 10 minutes
    }
  }

  for (const id of okSubs) await db.from('push_subscriptions').update({ last_ok_at: now(), fail_count: 0 }).eq('id', id);
  for (const [id, fc] of failSubs) await db.from('push_subscriptions').update({ fail_count: fc + 1 }).eq('id', id);
  if (dead.size) {
    await db.from('push_subscriptions').delete().in('id', [...dead]);
    out.subs_removed = dead.size;
  }
  // A browser that has failed 20 runs in a row without ever saying 410 is gone in every way that matters.
  const stale = await db.from('push_subscriptions').delete().gte('fail_count', 20).select('id');
  if (!stale?.error && stale?.data?.length) out.subs_removed += stale.data.length;

  return json(out, out.error ? 500 : 200);
}

function json(body: unknown, status = 200) {
  return new Response(JSON.stringify(body, null, 1), { status, headers: { 'content-type': 'application/json' } });
}

// Tests import this file with SEND_WEB_PUSH_TEST=1 so no server starts.
if (!Deno.env.get('SEND_WEB_PUSH_TEST')) Deno.serve((req) => handle(req));
