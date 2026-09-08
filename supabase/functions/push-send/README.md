# push-send

Drains `push_outbox` and delivers Web Push. Written 2026-09-08, **not yet deployed** — there is no
Supabase CLI on the machine this was written from.

To deploy:

```
supabase functions deploy push-send --project-ref rqkndeqbcahozidniesn
```

Then, in the Supabase dashboard under **Edge Functions → Secrets**, set:

| Secret | Value |
|---|---|
| `VAPID_PUBLIC_KEY`  | `BMVQLxL6nyuF6f3RAg16OgyYezAgGBKYqTVFsZbu-dvLuf-G1o1jTrJ0BKbMfHzUkx4UZDuxmOMH0cf4Di8rMt4` (the same key `index.html` ships) |
| `VAPID_PRIVATE_KEY` | from `~/Downloads/professify-VAPID-PRIVATE-KEY.txt` — **paste it into the dashboard, then delete that file** |

Schedule it every 5 minutes.

One line in here has never run: the `jsr:@negrel/webpush@0.3.0` import. Check the version resolves
before scheduling it, or the first run fails on the import rather than on anything it does.
