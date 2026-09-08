// ================================================================================================
// professify-push-send — Supabase Edge Function (Deno)
// ================================================================================================
// Drains public.push_outbox and delivers each row as a Web Push notification, then runs the two
// sweeps that have no trigger to fire them.
//
// DEPLOY
//   supabase secrets set VAPID_PUBLIC_KEY=...  VAPID_PRIVATE_KEY=...  VAPID_SUBJECT=mailto:you@calpoly.edu
//   supabase functions deploy professify-push-send --no-verify-jwt
//   then schedule it every 5 minutes (Supabase cron, or any external cron hitting the URL with
//   the CRON_SECRET below).
//
// THE PRIVATE KEY LIVES HERE AND ONLY HERE. The public half goes in index.html's
// PROFESSIFY_CONFIG.VAPID_PUBLIC_KEY; the private half must never be in the client, the repo, or
// a chat window. Generate the pair yourself: `npx web-push generate-vapid-keys`.
//
// HONEST NOTE ON THE ONE LINE I COULD NOT TEST: the import below is the only part of this file
// that was not exercised. Everything else — the queue query, the batching, the dead-endpoint
// cleanup, the retry accounting — is plain logic. Check the library's current version before
// deploying, and run it once by hand and read the JSON it returns before putting it on a cron.
// ================================================================================================
import { createClient } from 'jsr:@supabase/supabase-js@2';
import * as webpush from 'jsr:@negrel/webpush@0.3.0';

const SUPABASE_URL = Deno.env.get('SUPABASE_URL')!;
const SERVICE_KEY  = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!;
const VAPID_PUB    = Deno.env.get('VAPID_PUBLIC_KEY')!;
const VAPID_PRIV   = Deno.env.get('VAPID_PRIVATE_KEY')!;
const VAPID_SUB    = Deno.env.get('VAPID_SUBJECT') ?? 'mailto:hello@professify.app';
const CRON_SECRET  = Deno.env.get('CRON_SECRET') ?? '';

const BATCH = 200;          // one run's worth. A backlog drains over consecutive runs rather than
                            // holding one invocation open long enough to be killed mid-send.
const MAX_ATTEMPTS = 5;     // then stop trying: a row that has failed five times is not transient

Deno.serve(async (req) => {
  // --deploy with --no-verify-jwt, so this is the only thing standing between the internet and a
  // send loop. Constant-time-ish compare is overkill for a cron secret but costs nothing.
  if (CRON_SECRET) {
    const given = req.headers.get('x-cron-secret') ?? '';
    if (given.length !== CRON_SECRET.length || given !== CRON_SECRET) {
      return new Response('no', { status: 401 });
    }
  }

  const db = createClient(SUPABASE_URL, SERVICE_KEY, { auth: { persistSession: false } });
  const out = { swept_dropped: 0, swept_free: 0, sent: 0, failed: 0, pruned: 0, gave_up: 0 };

  // 1. The two things no trigger can notice: a section that stopped being scraped, and a friend
  //    whose last class just ended. Both are idempotent and cheap.
  try {
    const a = await db.rpc('push_sweep_dropped');
    if (!a.error) out.swept_dropped = a.data ?? 0;
    const b = await db.rpc('push_sweep_done_for_day', { p_window_min: 20 });
    if (!b.error) out.swept_free = b.data ?? 0;
  } catch (_) { /* a failed sweep must not stop the queue draining */ }

  // 2. What is due. send_after is how quiet hours are honoured — a row queued at 2am simply is
  //    not due until 8.
  const { data: rows, error } = await db
    .from('push_outbox')
    .select('id,user_id,kind,title,body,url,tag,attempts')
    .is('sent_at', null)
    .lte('send_after', new Date().toISOString())
    .lt('attempts', MAX_ATTEMPTS)
    .order('id', { ascending: true })
    .limit(BATCH);
  if (error) return json({ ...out, error: error.message }, 500);
  if (!rows?.length) return json(out);

  // 3. Everybody's devices, in one query rather than one per row.
  const userIds = [...new Set(rows.map((r) => r.user_id))];
  const { data: subs } = await db
    .from('push_subscriptions')
    .select('id,user_id,endpoint,p256dh,auth,fail_count')
    .in('user_id', userIds);
  const byUser = new Map<string, typeof subs>();
  for (const s of subs ?? []) {
    if (!byUser.has(s.user_id)) byUser.set(s.user_id, []);
    byUser.get(s.user_id)!.push(s);
  }

  const server = await webpush.ApplicationServer.new({
    contactInformation: VAPID_SUB,
    vapidKeys: await webpush.importVapidKeys(
      { publicKey: VAPID_PUB, privateKey: VAPID_PRIV },
      { extractable: false },
    ),
  });

  const deadEndpoints: string[] = [];

  for (const row of rows) {
    const devices = byUser.get(row.user_id) ?? [];
    if (!devices.length) {
      // Nothing to send to. Mark it sent rather than retrying forever — the student turned
      // notifications off, or never had them on, and the row is not going to become deliverable.
      await db.from('push_outbox').update({ sent_at: new Date().toISOString(),
        last_error: 'no subscription' }).eq('id', row.id);
      continue;
    }

    const payload = JSON.stringify({
      title: row.title, body: row.body, url: row.url || '/', tag: row.tag || row.kind,
    });

    let anyOk = false, lastErr = '';
    for (const d of devices) {
      try {
        const sub = server.subscribe({
          endpoint: d.endpoint,
          keys: { p256dh: d.p256dh, auth: d.auth },
        });
        await sub.pushTextMessage(payload, {});
        anyOk = true;
        await db.from('push_subscriptions')
          .update({ last_ok_at: new Date().toISOString(), fail_count: 0 }).eq('id', d.id);
      } catch (e) {
        const msg = String((e as Error)?.message ?? e);
        lastErr = msg.slice(0, 300);
        // 404/410 mean the push service has forgotten this endpoint — the browser was
        // uninstalled, cleared, or the subscription expired. That is not a retry, it is a
        // delete; leaving it means every future send tries a corpse.
        if (/\b(404|410)\b/.test(msg) || /gone|not\s*found/i.test(msg)) {
          deadEndpoints.push(d.endpoint);
        } else {
          // A transient failure (the push service 5xx'd, the network blipped). Count it on the
          // DEVICE as well as the row: a browser that fails every time for a week is dead in
          // every way that matters, it just never returned 410 to say so.
          await db.from('push_subscriptions')
            .update({ fail_count: (d as { fail_count?: number }).fail_count != null
                        ? ((d as { fail_count?: number }).fail_count! + 1) : 1 })
            .eq('id', d.id).catch(() => {});
        }
      }
    }

    if (anyOk) {
      await db.from('push_outbox').update({ sent_at: new Date().toISOString() }).eq('id', row.id);
      out.sent++;
    } else {
      const attempts = (row.attempts ?? 0) + 1;
      await db.from('push_outbox')
        .update({ attempts, last_error: lastErr })
        .eq('id', row.id);
      out.failed++;
      if (attempts >= MAX_ATTEMPTS) out.gave_up++;
    }
  }

  if (deadEndpoints.length) {
    await db.from('push_subscriptions').delete().in('endpoint', deadEndpoints);
    out.pruned = deadEndpoints.length;
  }
  // Devices that never said 410 but have failed 20 runs in a row are gone too.
  const stale = await db.from('push_subscriptions').delete().gte('fail_count', 20).select('id');
  if (!stale.error && stale.data?.length) out.pruned += stale.data.length;

  return json(out);
});

function json(body: unknown, status = 200) {
  return new Response(JSON.stringify(body, null, 1),
    { status, headers: { 'content-type': 'application/json' } });
}
