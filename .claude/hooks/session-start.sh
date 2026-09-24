#!/bin/bash
# Makes check-brand.mjs, check-gebrowse.mjs and seats/*.mjs runnable in Claude Code on the web.
# The app itself needs nothing — it is one static index.html. Only the Playwright checks do.
set -euo pipefail

if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
  exit 0
fi

cd "$CLAUDE_PROJECT_DIR"

# Use the container's preinstalled Playwright rather than `npm install`: it is the build that
# matches the browsers already in $PLAYWRIGHT_BROWSERS_PATH, and a newer one from npm looks for a
# chromium that is not there. Symlinked into the root and seats/ because ESM ignores NODE_PATH.
GLOBAL="$(npm root -g)"
if [ -d "$GLOBAL/playwright" ]; then
  for dir in node_modules seats/node_modules; do
    mkdir -p "$dir"
    ln -sfn "$GLOBAL/playwright" "$dir/playwright"
    if [ -d "$GLOBAL/playwright-core" ]; then ln -sfn "$GLOBAL/playwright-core" "$dir/playwright-core"; fi
  done
else
  (cd seats && npm install --no-audit --no-fund)
  npx --prefix seats playwright install chromium
  mkdir -p node_modules
  ln -sfn "$CLAUDE_PROJECT_DIR/seats/node_modules/playwright" node_modules/playwright
  ln -sfn "$CLAUDE_PROJECT_DIR/seats/node_modules/playwright-core" node_modules/playwright-core
fi
