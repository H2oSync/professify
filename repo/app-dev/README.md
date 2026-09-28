# app-dev — how the phone app (app/index.html) was built and is checked

**`app/index.html` is the real file.** Edit it directly, the same way as the desktop `index.html`, and upload it. Nothing here is published: netlify.toml publishes only `app/index.html` and `app/manifest.webmanifest`.

- `source/` holds the pieces PR 1 was assembled from. `build.py` joins the designer's CSS and images, `core.js` (every read and write), `ui.js` (screens) and `champ.js` (Champ, actions, rendering). It also patches `sw.js`, `netlify.toml` and the build stamp. Once `app/index.html` has been edited by hand, these pieces are out of date. Treat them as history, not as the thing to edit.
- `tests/check-app.mjs` runs the real `app/index.html` in Chromium with the real supabase-js 2.112.4 against a PostgREST stand-in, using synthetic fixtures only. It asserts on the rendered DOM and on the exact rows the app writes. `tests/mutate.mjs` breaks one promise at a time and requires check-app to fail on each.
  They were written for the Cowork dev container. They expect Playwright at `/opt/node-tools`, and the supabase-js tarball, and they read the page from `../out/` (or `APP_DIR`).
