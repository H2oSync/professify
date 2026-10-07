#!/usr/bin/env node
// ================================================================================================
// Build ios-app/www — the web half of the iPhone app — from the real phone app.
// ================================================================================================
// The App Store build carries its own copy of the app instead of loading termchamp.com/app, so it
// opens with no signal and is a real app rather than a website in a frame (Apple guideline 4.2).
// There is still ONE source: app/index.html and app/planner.js. Never edit www/ by hand — it is
// regenerated on every `npm run sync` and is gitignored.
//
// What changes on the way in, and only these:
//   1. supabase-js is loaded from this folder instead of cdn.jsdelivr.net, so a cold start without
//      signal still boots far enough to say "you're offline". The file is the same pinned 2.112.4,
//      and its sha256 must match the integrity hash app/index.html already pins, or this stops.
//   2. The PWA manifest link is dropped (an installed app has no "add to home screen").
// Everything else — including the html.native switch — is decided at runtime inside the page.
// ================================================================================================
import { readFileSync, writeFileSync, mkdirSync, rmSync, copyFileSync, existsSync } from 'node:fs';
import { createHash } from 'node:crypto';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = dirname(fileURLToPath(import.meta.url));
const IOS = join(HERE, '..');
const REPO = join(IOS, '..');
const WWW = join(IOS, 'www');

const die = m => { console.error('copy-web: ' + m); process.exit(1); };

rmSync(WWW, { recursive: true, force: true });
mkdirSync(WWW, { recursive: true });

let html = readFileSync(join(REPO, 'app', 'index.html'), 'utf8');

// ---- 1. supabase-js, local and verified --------------------------------------------------------
const tagRe = /<script defer\s+src="https:\/\/cdn\.jsdelivr\.net\/npm\/@supabase\/supabase-js@([\d.]+)\/dist\/umd\/supabase\.js"\s+integrity="sha256-([A-Za-z0-9+/=]+)"\s+crossorigin="anonymous"\s+onerror="window\.__sbScriptFailed=1"><\/script>/;
const tag = html.match(tagRe);
if (!tag) die('could not find the supabase-js <script> tag in app/index.html — has it changed?');
const [, ver, pinned] = tag;
const local = join(IOS, 'node_modules', '@supabase', 'supabase-js', 'dist', 'umd', 'supabase.js');
if (!existsSync(local)) die('node_modules/@supabase/supabase-js is missing — run `npm install` in ios-app first');
const pkgVer = JSON.parse(readFileSync(join(IOS, 'node_modules', '@supabase', 'supabase-js', 'package.json'), 'utf8')).version;
if (pkgVer !== ver) die(`app/index.html pins supabase-js ${ver} but ios-app has ${pkgVer}. Set the same version in ios-app/package.json and npm install.`);
const got = createHash('sha256').update(readFileSync(local)).digest('base64');
if (got !== pinned) die(`supabase.js ${ver} from npm does not match the integrity hash in app/index.html (got ${got}).`);
copyFileSync(local, join(WWW, 'supabase.js'));
html = html.replace(tagRe, `<script defer src="supabase.js" integrity="sha256-${pinned}" onerror="window.__sbScriptFailed=1"></script>`);

// ---- 2. no PWA manifest inside an installed app --------------------------------------------------
html = html.replace(/<link rel="manifest"[^>]*>\n?/, '');

writeFileSync(join(WWW, 'index.html'), html);

// ---- 3. the files the page loads by relative path ------------------------------------------------
copyFileSync(join(REPO, 'app', 'planner.js'), join(WWW, 'planner.js'));
for (const f of ['apple-touch-icon.png', 'icon-192.png', 'icon-512.png']) {
  if (existsSync(join(REPO, f))) copyFileSync(join(REPO, f), join(WWW, f));
}

console.log(`copy-web: www/ built from app/index.html (${(html.length / 1024).toFixed(0)} KB), planner.js, supabase-js ${ver} (hash verified)`);
