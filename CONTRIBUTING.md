# Contributing to Professify

Thanks for helping build this. The #1 rule: **don't break the live site.** These steps make that basically impossible.

## The golden rule: never push to `main` directly

`main` is what's live at professify.app. All work happens on a **branch**, goes through a **pull request (PR)**, and only gets merged after the Netlify preview looks right.

## Setup (once)

```bash
git clone https://github.com/YOUR-USERNAME/professify.git
cd professify
```

Open `index.html` in your browser to see it. That's the whole app.

## Making a change

```bash
git checkout main
git pull                       # get the latest
git checkout -b my-change      # make a branch, name it for what you're doing

# ...edit index.html...

git add index.html
git commit -m "Add Marketing concentration courses for Business"
git push -u origin my-change
```

Then on GitHub, click **"Compare & pull request."** Netlify automatically builds a **preview link** for your PR — open it, click around, make sure nothing's broken. When it looks good, merge the PR. Netlify deploys `main` to professify.app within a minute.

## What's safe to work on

- **Data** (safest): adding courses to `MAJOR_CATALOG` / concentrations, adding confirmed instructors to `CONFIRMED_SECTIONS`, adding a school to `SCHOOLS` + `SCHOOL_COURSES`. These are just data objects near the top/middle of the file.
- **Copy & styling:** text, labels, colors.
- **Features:** anything in the JS — but test hard in your preview first.

## House rules

1. **Real data only.** Never invent a course code, a professor, or a future teaching assignment. If you can't confirm it from Cal Poly's catalog or class schedule, don't add it. Fake data is worse than missing data.
2. **One year at a time.** We only name an instructor when we actually know who's teaching (a confirmed section). Otherwise we show the top-rated professor in the department and label it as such.
3. **Keep it one file.** Everything lives in `index.html` — inline CSS and JS, no build step, no external framework. Please keep it that way.
4. **Test on your phone.** Most students use Professify on mobile. Check your change there via the Netlify preview.
5. **Small PRs.** One concentration, one fix, one feature per PR — easier to review, easier to undo.

## If something does break

Because every change is a separate commit on `main`, you can always roll back: on GitHub, revert the offending PR (one click), and Netlify redeploys the previous good version. Nothing is ever lost.

## Good first tasks

- Fill in a Business or CS concentration's courses from the catalog.
- Add confirmed Fall instructors for high-enrollment intro courses.
- QA a few majors and file issues for anything wrong.
