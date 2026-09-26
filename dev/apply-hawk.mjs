/* Applies Hawk to index.html and sw.js, idempotently.
   Every change to this app belongs in a replayable script rather than an editor: two sessions edit
   the same single file, a build gets re-based onto a newer one, and a hand edit is silently absent
   when the scripts are replayed. One was lost that way on 09-19 and only a verifier caught it.

   Usage:  node apply-hawk.mjs [path-to-repo]     (default: the current directory)

   It does four things and refuses rather than guessing if any anchor is not found exactly once:
     1. adds the stylesheet and the two scripts to <head>
     2. adds both files to the service worker's cache list
     3. bumps PROFESSIFY_BUILD and sw.js BUILD to the same new stamp
     4. prints what it changed

   It does NOT touch netlify.toml — the publish allowlist is a one-line edit and doing it by hand
   means somebody reads the line that decides what the world can download. */
import fs from 'node:fs';
import path from 'node:path';

const root = process.argv[2] || '.';
const indexPath = path.join(root, 'index.html');
const swPath = path.join(root, 'sw.js');

function die(msg) { console.error('apply-hawk: ' + msg); process.exit(1); }
function once(haystack, needle, what) {
  const n = haystack.split(needle).length - 1;
  if (n !== 1) die(`expected to find ${what} exactly once, found ${n}. Refusing to guess.`);
}

if (!fs.existsSync(indexPath)) die(`no index.html at ${indexPath}`);
if (!fs.existsSync(swPath)) die(`no sw.js at ${swPath}`);

let index = fs.readFileSync(indexPath, 'utf8');
let sw = fs.readFileSync(swPath, 'utf8');
const changed = [];

/* 1. the tags */
/* RELATIVE, not absolute, and that is not a style choice.

   These were '/hawk-ask.js' and so on. Served from the site root that resolves identically — but
   opened as a local file, a leading slash means the ROOT OF THE DISK, so all three 404 and Hawk
   simply never appears. No error a person would notice: the app loads perfectly and the corner is
   empty. Tate hit exactly this opening a build from Downloads.

   Relative paths behave the same in production and survive being opened as a file, which is how
   every build gets looked at before it ships. */
const TAGS = [
  '<link rel="stylesheet" href="hawk-ask.css">',
  '<script defer src="hawk-router.js"></script>',
  '<script defer src="hawk-ask.js"></script>'
].join('\n');

if (index.includes('hawk-ask.js')) {
  changed.push('index.html already carries the Hawk tags — left alone');
} else {
  once(index, '</head>', '</head>');
  index = index.replace('</head>', TAGS + '\n</head>');
  changed.push('index.html: added the stylesheet and both scripts to <head>');
}

/* 2. the service worker cache list. Without this the palette works online and vanishes offline,
      which is the worst of both: it looks shipped and is missing exactly when the app promises to
      still work. */
if (sw.includes('hawk-ask.js')) {
  changed.push('sw.js already caches the Hawk files — left alone');
} else {
  const anchor = "'/termchamp-chat.js'";
  const fallback = "'/index.html'";
  if (sw.includes(anchor)) {
    once(sw, anchor, 'the assistant script in the cache list');
    sw = sw.replace(anchor, "'/hawk-router.js',\n  '/hawk-ask.js',\n  '/hawk-ask.css',\n  " + anchor);
  } else if (sw.includes(fallback)) {
    once(sw, fallback, "'/index.html' in the cache list");
    sw = sw.replace(fallback, fallback + ",\n  '/hawk-router.js',\n  '/hawk-ask.js',\n  '/hawk-ask.css'");
  } else if (sw.includes("'/manifest.webmanifest'\n];")) {
    /* The current worker precaches icons + manifest only (PRECACHE); the Hawk files join that list. */
    once(sw, "'/manifest.webmanifest'\n];", 'the end of the PRECACHE list');
    sw = sw.replace("'/manifest.webmanifest'\n];", "'/manifest.webmanifest',\n  '/hawk-router.js',\n  '/hawk-ask.js',\n  '/hawk-ask.css'\n];");
  } else {
    die('could not find the service-worker cache list. Add the three files by hand.');
  }
  changed.push('sw.js: added hawk-router.js, hawk-ask.js and hawk-ask.css to the cache list');
}

/* 3. the stamps, which have to agree — check-termchamp-ai.mjs asserts it and the service worker
      uses it to decide whether a returning student gets the new files at all. */
const now = new Date();
const pad = (n) => String(n).padStart(2, '0');
const stamp = `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())} `
  + `${pad(now.getHours())}:${pad(now.getMinutes())}`;

const htmlStampRe = /window\.PROFESSIFY_BUILD='([^']+)'/;
const swStampRe = /const BUILD = '([^']+)'/;
if (!htmlStampRe.test(index)) die('no PROFESSIFY_BUILD in index.html');
if (!swStampRe.test(sw)) die('no BUILD in sw.js');
const was = index.match(htmlStampRe)[1];

/* A STAMP MUST NEVER GO BACKWARDS, and this script produced one that did on its first run:
   2026-09-20 04:01 → 2026-09-20 01:06, because the machine generating it was three hours behind
   the machine that cut the previous build. The build stamp is the only version marker this app
   has — it is what tells you which of two forked copies is newer and what tells a returning
   student's service worker that anything changed. A stamp that moves backwards silently inverts
   both of those. So: take the later of "now" and "one minute after what is already there". */
function laterOf(a, b) { return a >= b ? a : b; }
function plusAMinute(s) {
  const m = /^(\d{4})-(\d{2})-(\d{2}) (\d{2}):(\d{2})$/.exec(s);
  if (!m) return s;
  const d = new Date(+m[1], +m[2] - 1, +m[3], +m[4], +m[5] + 1);
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} `
    + `${pad(d.getHours())}:${pad(d.getMinutes())}`;
}
const next = laterOf(stamp, plusAMinute(was));
if (next !== stamp) {
  console.log(`  note: this machine's clock (${stamp}) is behind the existing build (${was}).`);
  console.log(`        stamping ${next} instead, because a stamp that goes backwards is worse`);
  console.log('        than one that is wrong by three hours.');
}
index = index.replace(htmlStampRe, `window.PROFESSIFY_BUILD='${next}'`);
sw = sw.replace(swStampRe, `const BUILD = '${next}'`);
changed.push(`build stamp: ${was} → ${next} (index.html and sw.js)`);

fs.writeFileSync(indexPath, index);
fs.writeFileSync(swPath, sw);

changed.forEach((c) => console.log('  ' + c));
console.log('\nStill yours to do by hand:');
console.log('  netlify.toml — add  hawk-router.js hawk-ask.js hawk-ask.css  to the OPTIONAL publish list.');
console.log('  Without it the tags 404 in production and the palette simply never appears.');
