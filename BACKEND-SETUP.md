# Professify — Turn on real, persistent, verified reviews

Right now reviews work in "demo mode" — they're saved in the browser for the session and disappear on refresh. This makes them **real and permanent**, and gates rating behind a verified **.edu email** (a 6-digit code, no password). It's free and takes about 15 minutes.

The code is already wired in. It stays completely dormant until you fill in three values — nothing changes on your live site until then.

---

## Step 1 — Create a free Supabase project

1. Go to **supabase.com** → sign up (free tier is plenty to launch).
2. **New project.** Pick a name (e.g. `professify`), a strong database password (save it), and a region near you (US West).
3. Wait ~2 minutes for it to spin up.

## Step 2 — Create the reviews table

1. In your project, open **SQL Editor** (left sidebar) → **New query**.
2. Open `professify-supabase-setup.sql` (delivered alongside this file), copy all of it, paste it in, and click **Run**.
3. You should see "Success." That created the `reviews` table, security rules (so students can only post as themselves, only from a .edu email, and everyone can read), and a stats view.

## Step 3 — Make sign-in send a 6-digit code

Professify verifies students with a code emailed to their .edu address.

1. Go to **Authentication → Providers → Email** and make sure **Email** is enabled (it is by default). Leave "Confirm email" on.
2. Go to **Authentication → Emails → Templates** → **Magic Link**.
3. Make sure the template includes the code token. Add this line if it's not there:

   ```
   Your Professify verification code is: {{ .Token }}
   ```

   (Supabase sends both a link and a code; this line makes the 6-digit code visible, which is what the app asks for.)

## Step 4 — Point auth at your site

Go to **Authentication → URL Configuration** and set:
- **Site URL:** `https://professify.app`
- Add `https://professify.app` under **Redirect URLs** too.

## Step 5 — Copy your two keys into Professify

1. In Supabase, go to **Project Settings → API**.
2. Copy the **Project URL** and the **anon public** key. (The anon key is safe to put in your site — the security rules protect the data. Never paste the `service_role` key.)
3. Open `index.html`, find this block near the top:

   ```js
   window.PROFESSIFY_CONFIG = {
     SUPABASE_URL: '',
     SUPABASE_ANON_KEY: '',
     EMAIL_DOMAIN: ''
   };
   ```

4. Paste your values:

   ```js
   window.PROFESSIFY_CONFIG = {
     SUPABASE_URL: 'https://YOURPROJECT.supabase.co',
     SUPABASE_ANON_KEY: 'eyJhbGciOi...your-anon-key...',
     EMAIL_DOMAIN: 'calpoly.edu'   // optional — lock sign-in to one school. Leave '' for any .edu
   };
   ```

5. Re-deploy: drag the updated `index.html` into your Netlify **Deploys** tab.

## Step 6 — Test it

1. Open professify.app, find any professor, click **Rate this professor**.
2. Enter your `@calpoly.edu` email → **Email me a code**.
3. Check your inbox, type the 6-digit code, verify, and post a review.
4. Refresh the page and reopen that professor — your review is still there. 🎉

---

## Good to know

- **Free-tier email is rate-limited** (only a few sign-in emails per hour by default). That's fine for testing. Before a real launch, set up custom email under **Authentication → Emails → SMTP Settings** using a free sender like **Resend** or **SendGrid** — this lets you send far more and lands in inboxes reliably.
- **Cal-Poly-only vs any .edu:** setting `EMAIL_DOMAIN: 'calpoly.edu'` limits the app's input to Cal Poly. For hard enforcement at the database level too, change `'%.edu'` to `'%@calpoly.edu'` in the SQL policy `reviews_insert_own_edu` and re-run that one policy.
- **The anon key is meant to be public.** Your data is safe because Row Level Security only lets students read reviews and write their own. Keep the `service_role` key secret (never in the site).
- **Nothing breaks if you skip this.** With the config blank, Professify runs exactly as it does now (session-only reviews). You can turn the backend on any time.

## What you get once it's live

- Reviews persist forever and show for every visitor.
- Only verified .edu students can post (your trust moat vs. RateMyProfessors).
- One review per student per class, enforced by the database.
- A `professor_review_stats` view you can later use to show Professify's own average alongside PolyRatings.
