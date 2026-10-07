# ios-app — TermChamp for iPhone

The App Store app. It is the phone app (`app/index.html` + `app/planner.js`) bundled inside a
native shell ([Capacitor 8](https://capacitorjs.com)), plus real push notifications.

**There is still one app.** Edit `app/index.html` like always. This folder only packages it.
`www/` and `ios/App/App/public/` are generated copies — never edit them.

## What's different from the website

Decided at runtime by `window.TC_NATIVE` (set at the top of `app/index.html`):

- Always full-screen phone layout; the desk panel ("Phone app · beta", "add it to your home screen") never shows.
- No service worker (the app has its own copy of everything).
- Push notifications (APNs): open seats, plan sections filling, registration, friend requests, friends in your class, messages, likes, group adds. Settings › Notifications has a switch per kind and each chat has a mute bell. The app asks at a sensible moment (watching a seat, first message, end of onboarding), never at launch.
- Google Analytics never loads (it only runs on termchamp.com), so the App Store privacy label has no analytics.
- The status bar's clock follows each screen's top color (dark text on light screens, light on dark), using `@capacitor/status-bar`.
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

Code is done; three switches are left (click-by-click in `supabase/functions/send-push/README.md`):

1. Create an Apple push key (APNs) and add it, with a `PUSH_SECRET`, to the Supabase function secrets.
2. Deploy the `send-push` function.
3. Run `sql/termchamp-push.sql` in Supabase, then the `push_config` insert at its bottom.

Until then the app works normally — "Turn on notifications" asks iOS for permission, but nothing is delivered.

## Test checklist before submitting

- [ ] Fresh install, sign in with the demo account, every tab loads.
- [ ] Explore shows PolyRatings scores. (PolyRatings' API allows any origin, so the app can read it — checked in their open-source backend.)
- [ ] Airplane mode on, open the app: it says you're offline instead of a blank screen.
- [ ] Settings › Notifications › Turn on notifications → iOS permission prompt appears.
- [ ] Have a friend message you with the app closed: a notification arrives, and tapping it opens the chat.
- [ ] Profile → Edit → photo: the photo picker opens (and the camera, if offered, asks permission first).
- [ ] Settings → Privacy Policy, Terms, Community Guidelines open; the support link opens Safari.
- [ ] Friend profile → ⋯ shows Remove / Report / Block.
