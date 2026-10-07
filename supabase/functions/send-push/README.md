# send-push

Sends the iPhone app's notifications. `sql/termchamp-push.sql` queues rows in `push_queue` and pokes
this function through `pg_net`; it claims a batch (each row comes with that student's phone tokens),
sends them to Apple, and records the result. A cron job in the same SQL pokes it every minute for
anything delayed or retried.

(`push-send` is the separate, older Web Push sender for the website.)

## Set up, once

1. **Apple push key.** developer.apple.com → Certificates, IDs & Profiles → **Keys** → **+** → name it, tick **Apple Push Notifications service (APNs)** → Continue → Register → **Download** the `AuthKey_XXXXXXXXXX.p8` file (Apple lets you download it once). Note the **Key ID** and your **Team ID** (Membership details).
2. **Secrets.** Supabase → Edge Functions → Secrets:

   | Secret | Value |
   |---|---|
   | `PUSH_SECRET` | a long random string (also goes in `push_config`, step 4) |
   | `APNS_KEY_ID` | the Key ID |
   | `APNS_TEAM_ID` | the Team ID |
   | `APNS_PRIVATE_KEY` | the whole text of the `.p8` file, BEGIN/END lines included — then delete the file |
   | `APNS_BUNDLE_ID` | `com.termchamp.app` |

3. **Deploy.**
   ```
   supabase functions deploy send-push --project-ref rqkndeqbcahozidniesn --no-verify-jwt
   ```
   (No JWT on purpose: the caller is your database, which proves itself with `PUSH_SECRET`.)
   No CLI installed? It runs straight from npm: `npx supabase login`, then `npx supabase functions deploy send-push --project-ref rqkndeqbcahozidniesn --no-verify-jwt` from the repo folder. It uploads `../_shared/apns.ts` with it.
4. **SQL.** Run `sql/termchamp-push.sql`, then the `insert into public.push_config` at its bottom with the function URL, the same `PUSH_SECRET`, and the registration date/term. The self-check at the end should be all `ok`.

## Check it works

Install the TestFlight build, turn on notifications, and have a friend send you a message. Supabase → Table Editor → `push_queue`: the row should get `sent_at`. If `error` says `production 403 ...`, the key ID, team ID or `.p8` text is wrong.

## Tests

```
deno test --allow-env supabase/functions/send-push/index_test.ts supabase/functions/_shared/apns_test.ts
```
No network: a fake database and a fake Apple.
