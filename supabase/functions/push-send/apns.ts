// ================================================================================================
// APNs — the iPhone app's half of push-send (6 October 2026)
// ================================================================================================
// The App Store app gets an APNs device token instead of a Web Push subscription
// (sql/professify-push-ios.sql). This sends to it with Apple's token-based auth: one .p8 key from
// the Apple Developer account signs a short-lived JWT, and every request carries it.
//
// SECRETS (Supabase → Edge Functions → Secrets). All four, or iOS sends are skipped and said so:
//   APNS_KEY_ID       the 10-character Key ID shown next to the key in developer.apple.com
//   APNS_TEAM_ID      the 10-character Team ID (Membership details)
//   APNS_PRIVATE_KEY  the whole contents of AuthKey_XXXXXXXXXX.p8, BEGIN/END lines included
//   APNS_BUNDLE_ID    com.termchamp.app (must match the Xcode bundle identifier exactly)
//
// SANDBOX VS PRODUCTION. A build run straight from Xcode gets a sandbox token; TestFlight and the
// App Store get production ones. The app cannot tell which it is, so it does not try: the first
// send goes to production, and a BadDeviceToken there is retried once on sandbox. Whichever works
// is written to push_devices.apns_env and used from then on.
// ================================================================================================

export type ApnsConfig = { keyId: string; teamId: string; privateKey: string; bundleId: string };
export type ApnsMessage = { title: string; body: string; url: string; tag: string; kind: string };
export type ApnsResult =
  | { ok: true; env: 'production' | 'sandbox' }
  | { ok: false; dead: boolean; fatal: boolean; error: string };

const HOST = { production: 'https://api.push.apple.com', sandbox: 'https://api.sandbox.push.apple.com' } as const;

export function apnsConfigFromEnv(get: (k: string) => string | undefined): ApnsConfig | null {
  const keyId = (get('APNS_KEY_ID') ?? '').trim();
  const teamId = (get('APNS_TEAM_ID') ?? '').trim();
  const privateKey = (get('APNS_PRIVATE_KEY') ?? '').trim();
  const bundleId = (get('APNS_BUNDLE_ID') ?? '').trim();
  return keyId && teamId && privateKey && bundleId ? { keyId, teamId, privateKey, bundleId } : null;
}

// ---- the JWT -------------------------------------------------------------------------------------
// Apple wants it reused, not minted per request, and refuses one older than an hour. 40 minutes
// sits safely inside both rules.
let cached: { jwt: string; at: number; keyId: string; pk: string } | null = null;

const b64url = (b: ArrayBuffer | Uint8Array | string) => {
  const bytes = typeof b === 'string' ? new TextEncoder().encode(b) : new Uint8Array(b);
  let s = ''; for (const x of bytes) s += String.fromCharCode(x);
  return btoa(s).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
};

async function signingKey(pem: string): Promise<CryptoKey> {
  const body = pem.replace(/-----(BEGIN|END) PRIVATE KEY-----/g, '').replace(/\s+/g, '');
  const der = Uint8Array.from(atob(body), (c) => c.charCodeAt(0));
  return await crypto.subtle.importKey('pkcs8', der, { name: 'ECDSA', namedCurve: 'P-256' }, false, ['sign']);
}

export async function apnsJwt(cfg: ApnsConfig, now = Date.now()): Promise<string> {
  if (cached && cached.keyId === cfg.keyId && cached.pk === cfg.privateKey && now >= cached.at && now - cached.at < 40 * 60 * 1000) return cached.jwt;
  const head = b64url(JSON.stringify({ alg: 'ES256', kid: cfg.keyId }));
  const claims = b64url(JSON.stringify({ iss: cfg.teamId, iat: Math.floor(now / 1000) }));
  // WebCrypto's ECDSA signature is already the raw r||s form a JWT wants (not DER).
  const sig = await crypto.subtle.sign({ name: 'ECDSA', hash: 'SHA-256' }, await signingKey(cfg.privateKey),
    new TextEncoder().encode(`${head}.${claims}`));
  const jwt = `${head}.${claims}.${b64url(sig)}`;
  cached = { jwt, at: now, keyId: cfg.keyId, pk: cfg.privateKey };
  return jwt;
}

// ---- one send ------------------------------------------------------------------------------------
export function apnsPayload(m: ApnsMessage) {
  return {
    aps: { alert: { title: m.title, body: m.body }, sound: 'default', 'thread-id': m.kind },
    url: m.url || '/',   // the app reads this on tap: /?tab=sched → Schedule, /?tab=friends → Friends
  };
}

async function sendOnce(cfg: ApnsConfig, env: 'production' | 'sandbox', token: string, m: ApnsMessage, fetchFn: typeof fetch) {
  const res = await fetchFn(`${HOST[env]}/3/device/${token}`, {
    method: 'POST',
    headers: {
      authorization: `bearer ${await apnsJwt(cfg)}`,
      'apns-topic': cfg.bundleId,
      'apns-push-type': 'alert',
      'apns-priority': '10',
      // same tag replaces the earlier banner instead of stacking a second one (64-byte limit)
      'apns-collapse-id': (m.tag || m.kind).slice(0, 64),
      'content-type': 'application/json',
    },
    body: JSON.stringify(apnsPayload(m)),
  });
  let reason = '';
  if (res.status !== 200) { try { reason = (await res.json())?.reason ?? ''; } catch (_) { /* empty body */ } }
  return { status: res.status, reason };
}

export async function apnsSend(cfg: ApnsConfig, token: string, knownEnv: string | null, m: ApnsMessage,
  fetchFn: typeof fetch = fetch): Promise<ApnsResult> {
  const first: 'production' | 'sandbox' = knownEnv === 'sandbox' ? 'sandbox' : 'production';
  const order: Array<'production' | 'sandbox'> = knownEnv ? [first] : ['production', 'sandbox'];
  let last = '';
  for (const env of order) {
    let r: { status: number; reason: string };
    try { r = await sendOnce(cfg, env, token, m, fetchFn); }
    catch (e) { return { ok: false, dead: false, fatal: false, error: 'network: ' + String((e as Error)?.message ?? e).slice(0, 200) }; }
    if (r.status === 200) return { ok: true, env };
    last = `${env} ${r.status} ${r.reason}`;
    // Wrong environment for this token: try the other one (only when we didn't already know).
    if (r.status === 400 && (r.reason === 'BadDeviceToken' || r.reason === 'DeviceTokenNotForTopic') && order.length > 1 && env === 'production') continue;
    // The phone uninstalled the app or turned the token over. Not a retry — a delete.
    if (r.status === 410 || (r.status === 400 && (r.reason === 'BadDeviceToken' || r.reason === 'DeviceTokenNotForTopic'))) return { ok: false, dead: true, fatal: false, error: last };
    // Our key, team or bundle id is wrong. Every other send this run would fail the same way.
    if (r.status === 403 || (r.status === 400 && ['TopicDisallowed', 'BadTopic', 'MissingTopic'].includes(r.reason))) {
      cached = null;
      return { ok: false, dead: false, fatal: true, error: last };
    }
    return { ok: false, dead: false, fatal: false, error: last };   // 429, 5xx, anything else: try next run
  }
  return { ok: false, dead: true, fatal: false, error: last };      // bad on both environments
}
