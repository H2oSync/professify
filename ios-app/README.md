# ios-app — TermChamp for iPhone

The App Store app. It is the phone app (`app/index.html` + `app/planner.js`) bundled inside a
native shell ([Capacitor 8](https://capacitorjs.com)), plus real push notifications for seat alerts.

**There is still one app.** Edit `app/index.html` like always. This folder only packages it.
`www/` and `ios/App/App/public/` are generated copies — never edit them.

## What's different from the website

Decided at runtime by `window.TC_NATIVE` (set at the top of `app/index.html`):

- Always full-screen phone layout; the desk panel ("Phone app · beta", "add it to your home screen") never shows.
- No service worker (the app has its own copy of everything).
- Seat alerts are native iOS notifications (APNs) instead of Web Push. Settings gets a **Notifications** section; the first time a student watches a section, iOS asks for permission.
- Google Analytics never loads (it only runs on termchamp.com), so the App Store privacy label has no analytics.
- iPhone only, portrait only (no iPad build).

## Build it (on a Mac)

Needs: the latest Xcode from the Mac App Store, Node 20+, and the team's Apple Developer account.

```bash
cd ios-app
npm install
npm run sync      # builds www/ from ../app, copies it into the Xcode project
npm run open      # opens Xcode
```

In Xcode:

1. Click **App** in the left sidebar → **Signing & Capabilities** → pick your Team.
   Bundle Identifier is `com.termchamp.app`; if you already registered a different one, change it here **and** in `capacitor.config.json` and the `APNS_BUNDLE_ID` secret.
2. Check that **Push Notifications** is listed under capabilities (the entitlements file is already in the project; if it's missing, click **+ Capability → Push Notifications**).
3. Plug in your iPhone, pick it at the top, press ▶ Run.

Every time `app/index.html` changes: `npm run sync`, then Run again.

## Ship a build

1. Bump **Version** (e.g. 1.0.1) and/or **Build** (must go up every upload) under App → General.
2. Top bar device: **Any iOS Device (arm64)** → **Product → Archive** → **Distribute App → App Store Connect → Upload**.
3. It shows up in App Store Connect → TestFlight in ~15–30 minutes.

## Turning on seat-alert pushes

Code is done; three switches are left (details in `supabase/functions/push-send/README.md`):

1. Run `sql/professify-push-ios.sql` in Supabase.
2. Create an APNs key in the Apple Developer account and add the four `APNS_*` secrets.
3. Deploy `push-send` and schedule it every 5 minutes.

Until then the app works normally — "Turn on" in Settings asks iOS for permission, but no alert is delivered.

## Test checklist before submitting

- [ ] Fresh install, sign in with the demo account, every tab loads.
- [ ] Explore shows PolyRatings scores. (If they're blank in the app but fine on the website, PolyRatings is blocking the app's origin — tell Claude, the fix is one config line.)
- [ ] Airplane mode on, open the app: it says you're offline instead of a blank screen.
- [ ] Settings → Notifications → Turn on → iOS permission prompt appears.
- [ ] Profile → Edit → photo: the photo picker opens (and the camera, if offered, asks permission first).
- [ ] Settings → Privacy Policy, Terms, Community Guidelines open; the support link opens Safari.
- [ ] Friend profile → ⋯ shows Remove / Report / Block.
