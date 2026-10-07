# push-send

Drains `push_outbox` and delivers each row to every device the student has:

- **Web Push** to `push_subscriptions` (browsers), and
- **APNs** to `push_devices` (the iPhone app — added 2026-10-06, see `apns.ts`).

Either half runs without the other. Missing VAPID keys turn off Web Push; missing `APNS_*` secrets
turn off iOS. The JSON each run returns says which halves are on (`web_push`, `apns`).

Written 2026-09-08, **not yet deployed** — there is no Supabase CLI on the machine this was written from.

## Deploy

1. Run `sql/professify-push-ios.sql` in the Supabase SQL editor (adds `push_devices`; the self-check at the end should be all `ok`).
2. Deploy the function:

   ```
   supabase functions deploy push-send --project-ref rqkndeqbcahozidniesn --no-verify-jwt
   ```

3. In the Supabase dashboard under **Edge Functions → Secrets**, set:

| Secret | Value |
|---|---|
| `CRON_SECRET` | any long random string; the scheduler sends it as `x-cron-secret` |
| `APNS_KEY_ID` | Key ID of the APNs key (developer.apple.com → Certificates, IDs & Profiles → Keys → **+** → tick *Apple Push Notifications service*) |
| `APNS_TEAM_ID` | your 10-character Team ID (developer.apple.com → Membership details) |
| `APNS_PRIVATE_KEY` | the full text of the downloaded `AuthKey_XXXXXXXXXX.p8`, including the BEGIN/END lines. Apple lets you download it **once** — paste it here, then delete the file |
| `APNS_BUNDLE_ID` | `com.termchamp.app` (must match Xcode exactly) |
| `VAPID_PUBLIC_KEY` | *(web only)* `BMVQLxL6nyuF6f3RAg16OgyYezAgGBKYqTVFsZbu-dvLuf-G1o1jTrJ0BKbMfHzUkx4UZDuxmOMH0cf4Di8rMt4` (the same key `index.html` ships) |
| `VAPID_PRIVATE_KEY` | *(web only)* from `~/Downloads/professify-VAPID-PRIVATE-KEY.txt` — **paste it into the dashboard, then delete that file** |

4. Schedule it every 5 minutes (Supabase → Integrations → Cron, an HTTP request to the function URL with the `x-cron-secret` header).

5. Before scheduling: invoke it once by hand and read the JSON. `apns` should say `on`. If it says `error: production 403 ...`, the key ID, team ID or `.p8` text is wrong.

## Tests

```
deno test supabase/functions/push-send/apns_test.ts
```

No network: a fake APNs and a key generated in the test. It checks the JWT verifies, and that each APNs answer (200, BadDeviceToken → sandbox retry, 410, 403, 429/503) leads to the right action.

One line in here has never run: the `jsr:@negrel/webpush@0.3.0` import. Check the version resolves
before scheduling it, or the first run fails on the import rather than on anything it does.
