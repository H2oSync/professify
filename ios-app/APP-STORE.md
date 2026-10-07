# Submitting TermChamp to the App Store

Everything in the code is done on the `app-store-readiness` branch. This is the list of things only
a person with the accounts can do, in order. Roughly 1–2 hours total, plus Apple's review (usually 1–3 days).

## 1. Before you build

- [ ] **Merge the PR**, so termchamp.com/privacy, /terms, /guidelines and /support go live. App Store Connect won't accept the listing without the privacy and support URLs. Check both open in a private browser window.
- [ ] **Apple Developer Program** is active ($99/yr). Add Tate and Sean as team members if they'll upload builds.
- [ ] **PolyRatings permission.** Send the email below, so you have a written OK if Apple asks about rights to the ratings.
- [ ] **Reports get handled.** Apple requires acting on reported content within 24 hours, and `/support` promises it. Agree who checks `reports` (admin dashboard) daily, and that `support@termchamp.com` reaches a real inbox.

## 2. Demo account for Apple

Apple's reviewer can't make a Cal Poly account, and your own account shows real students' names, schedules and messages. Never give Apple a real account.

1. Supabase → **Authentication → Users → Add user → Create new user**, five times, with **Auto Confirm User** ticked:
   `reviewer@appreview.calpoly.edu`, `alex@…`, `priya@…`, `jordan@…`, `maya@…` (same domain). Give `reviewer@` a strong password and save it; the other four can have any password.
2. Supabase → **SQL editor** → paste and run `sql/professify-app-review-demo.sql`. It should end with *Demo ready*. If it errors, nothing was written; the message says what to fix.
3. In the app, sign in as `reviewer@appreview.calpoly.edu` with the password (not "Email me a code" — that address has no inbox) and click through every tab.

Everyone in it is made up; the classes are real Fall 2026 sections. It writes no reviews. To remove it later, delete the five users.

## 3. App Store Connect listing

**appstoreconnect.apple.com → My Apps → + → New App**: Platform iOS, Name **TermChamp**, Bundle ID `com.termchamp.app`, SKU `termchamp-ios`.

| Field | What to enter |
|---|---|
| Subtitle | Cal Poly classes & professors |
| Category | Education (secondary: Social Networking) |
| Privacy Policy URL | https://termchamp.com/privacy |
| Support URL | https://termchamp.com/support |
| Age rating | Answer the questionnaire honestly: user-generated content **yes**, messaging between users **yes**. Expect 13+ (matches the Terms). |
| Price | Free |
| Availability | United States only, to start |

**Description** (paste and edit):

> TermChamp helps Cal Poly students pick classes and professors in one place.
>
> • Real professor ratings from PolyRatings, plus reviews from verified Cal Poly students
> • Live seat counts for every section, and an alert when a seat opens in a class you're watching
> • See your friends' schedules and which classes you share
> • Plan A, B and C for registration, checked against your degree progress
> • Message friends and share classes in a tap
>
> Sign up with your Cal Poly email. No ads, and your data is never sold.
>
> TermChamp is an independent app built by Cal Poly students. It is not affiliated with or endorsed by Cal Poly.

**Keywords:** `cal poly,class schedule,professor ratings,polyratings,registration,college,seats,slo`

**Screenshots:** 6.9" iPhone (1320 × 2868) — at least 3, from the **demo account** only (Home, Explore with a professor, Schedule, Friends). No real students' names or photos. Easiest: the iPhone 17 Pro Max simulator in Xcode, ⌘S to save a screenshot.

## 4. App Privacy (the "nutrition label")

App Store Connect → App Privacy → Get Started. Answer **Yes, we collect data**, then:

| Data type | Collected | Linked to user | Tracking | Purpose |
|---|---|---|---|---|
| Contact Info → Email Address | Yes | Yes | No | App Functionality |
| Contact Info → Name | Yes | Yes | No | App Functionality |
| User Content → Photos | Yes (optional profile photo) | Yes | No | App Functionality |
| User Content → Other User Content (reviews, messages, class schedule) | Yes | Yes | No | App Functionality |
| Identifiers → User ID | Yes | Yes | No | App Functionality |
| Usage Data → Product Interaction (anonymous professor-page counts) | Yes | **No** | No | Analytics |

No tracking, no ads, no location, no contacts, no health, no payments. Google Analytics only runs on the website, not in the app. Champ questions sent to Anthropic are covered under Other User Content (App Functionality), and the app asks before sending any.

Double-check this against `/privacy` before submitting — the label and the policy must agree.

## 5. Build, upload, test

Follow `ios-app/README.md`: `npm run sync`, Archive, Upload. Install from TestFlight on your phones and run the test checklist there.

## 6. App Review notes

App Store Connect → the version → **App Review Information**. Sign-in required: **yes**, username `reviewer@appreview.calpoly.edu`, the password. Notes:

> TermChamp is an independent app built by Cal Poly San Luis Obispo students for the university's ~22,000 students. It is open to any Cal Poly student and is not an internal tool of the university, and is not affiliated with it.
>
> HOW TO SIGN IN: use the demo account above with "Sign in" → password (not "Email me a code"). It has sample friends, classes and a chat. Everyone in it is fictional; classes are real Fall 2026 sections.
>
> WHAT IT DOES: professor ratings (from PolyRatings' public API, used with permission, plus reviews by verified Cal Poly students), live seat counts from Cal Poly's public class search, schedule planning against degree requirements, sharing schedules with friends, and messaging between friends.
>
> NATIVE FEATURES: push notifications when a seat opens in a class the student is watching (turn on in Settings → Notifications, or by watching any section of a class). The app is bundled on the device rather than loaded from a website.
>
> SAFETY (Guideline 1.2): reviews, names and group names are filtered for objectionable words before posting. Users must agree to the Terms and Community Guidelines at sign-up. Any review can be reported ("Report this review"); any user can be reported or blocked from ⋯ on their profile or in a chat. Reports are reviewed within 24 hours, and offending content and accounts are removed. Contact: support@termchamp.com.
>
> ACCOUNT DELETION: Profile → Settings → Delete account.
>
> AI: the in-app assistant (Champ) asks the user's permission before sending a question to Anthropic's AI, and can be turned off in Settings.

Then **Submit for Review**.

## 7. If it's rejected

Apple says which guideline in **Resolution Center**. Reply there, or fix and resubmit. Paste the message to Claude with the branch name and it can make the change.

---

## Email to PolyRatings

To the maintainers listed on polyratings.dev or their GitHub (github.com/Polyratings):

> **Subject:** Permission to show PolyRatings scores in TermChamp's iPhone app
>
> Hi PolyRatings team,
>
> We're three Cal Poly students who built TermChamp (termchamp.com), a free, ad-free app for planning classes. It shows each professor's overall PolyRatings score from your public API, credits PolyRatings by name, and links to your site for the full reviews. We don't copy or store your written reviews.
>
> We're publishing TermChamp as an iPhone app, and Apple can ask for proof that we're allowed to use third-party content. Would you be OK with us continuing to show PolyRatings scores this way? A quick reply saying yes is all we'd need. If you'd like anything changed, like how we credit you or how often we call the API, we're happy to do it.
>
> Thanks for building PolyRatings — it's the reason this works.
>
> Sage Stern, Tate Sims and Sean McClure
> TermChamp · support@termchamp.com
