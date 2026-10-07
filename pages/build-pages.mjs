#!/usr/bin/env node
// ================================================================================================
// PUBLIC LEGAL + SUPPORT PAGES — 6 October 2026
// ================================================================================================
// The App Store needs a Privacy Policy URL and a Support URL that load in a plain browser, with no
// sign-in. Until now the policies only existed inside the app (LEGAL_DOCS in app/planner.js), so
// termchamp.com/privacy, /terms and /support were all 404s.
//
// This builds them from the SAME text the app shows, at deploy time, so there is one copy of the
// policies and the public pages can never drift from the in-app ones:
//
//   /privacy      LEGAL_DOCS.privacy
//   /terms        LEGAL_DOCS.terms
//   /guidelines   LEGAL_DOCS.guidelines
//   /security     LEGAL_DOCS.security
//   /support      written below (contact, report, delete account, data requests)
//
// Run by netlify.toml's build command:  node pages/build-pages.mjs public
// Run locally to look at them:          node pages/build-pages.mjs /tmp/out && open /tmp/out/privacy/index.html
//
// It reads ONLY the legal block of planner.js (from `var LEGAL_UPDATED=` to the end of
// `var LEGAL_DOCS={...};`), not the whole file, so nothing else in planner.js has to run in Node.
// ================================================================================================
import { readFileSync, mkdirSync, writeFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import vm from 'node:vm';

const ROOT = join(dirname(fileURLToPath(import.meta.url)), '..');
const OUT = process.argv[2] || join(ROOT, 'public');

// ---- 1. the legal text, from the file the app itself loads ------------------------------------
export function loadLegal(src) {
  const start = src.indexOf('var LEGAL_UPDATED=');
  const docs = src.indexOf('var LEGAL_DOCS={', start);
  if (start < 0 || docs < 0) throw new Error('planner.js: legal block not found (var LEGAL_UPDATED / var LEGAL_DOCS)');
  // the object ends at the first line that is exactly "};" after it opens
  const endRe = /\n\};?[ \t]*\n/g;
  endRe.lastIndex = docs;
  const m = endRe.exec(src);
  if (!m) throw new Error('planner.js: end of LEGAL_DOCS not found');
  const block = src.slice(start, m.index + m[0].length);
  const ctx = {};
  vm.runInNewContext(block + '\n;this.__docs = LEGAL_DOCS; this.__contact = LEGAL_CONTACT; this.__updated = LEGAL_UPDATED;', ctx, { timeout: 2000 });
  const d = ctx.__docs;
  for (const k of ['privacy', 'terms', 'guidelines', 'security']) {
    if (!d[k] || typeof d[k].html !== 'string' || d[k].html.length < 200) throw new Error(`LEGAL_DOCS.${k} is missing or empty`);
  }
  return { docs: d, contact: ctx.__contact, updated: ctx.__updated };
}

// ---- 2. one plain, readable page shell ----------------------------------------------------------
const esc = s => String(s).replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
const NAV = [['privacy', 'Privacy'], ['terms', 'Terms'], ['guidelines', 'Community Guidelines'], ['security', 'Security'], ['support', 'Support']];

export function page({ slug, title, body, description }) {
  const nav = NAV.map(([s, t]) => `<a href="/${s}"${s === slug ? ' aria-current="page"' : ''}>${t}</a>`).join('');
  return `<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>${esc(title)} · TermChamp</title>
<meta name="description" content="${esc(description || title + ' for TermChamp, the class and professor app for Cal Poly students.')}">
<link rel="canonical" href="https://termchamp.com/${slug}">
<link rel="icon" href="/icon-192.png">
<link rel="apple-touch-icon" href="/apple-touch-icon.png">
<meta name="color-scheme" content="light dark">
<style>
:root{--ink:#0F172A;--ink2:#1E293B;--muted:#64748B;--line:#E2E8F0;--bg:#F4F6FB;--card:#fff;--blue:#2563EB;--navy:#16336B;--key:#E3ECFF}
@media (prefers-color-scheme:dark){:root{--ink:#F1F5F9;--ink2:#CBD5E1;--muted:#94A3B8;--line:#1E293B;--bg:#0A0F1C;--card:#111827;--blue:#7AA2FF;--navy:#BFD3FF;--key:#16233F}}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink2);font:16px/1.6 system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;-webkit-font-smoothing:antialiased}
header{max-width:760px;margin:0 auto;padding:22px 16px 6px;display:flex;align-items:center;gap:10px}
header a.brand{display:flex;align-items:center;gap:10px;text-decoration:none;color:var(--navy);font-weight:900;font-size:20px}
header img{width:34px;height:34px;border-radius:10px}
nav{max-width:760px;margin:0 auto;padding:4px 16px 0;display:flex;flex-wrap:wrap;gap:6px 16px;font-size:14px;font-weight:700}
nav a{color:var(--muted);text-decoration:none;padding:4px 0}
nav a[aria-current]{color:var(--blue);border-bottom:2px solid var(--blue)}
main{max-width:760px;margin:14px auto 40px;padding:24px 20px;background:var(--card);border-radius:18px;box-shadow:0 1px 3px rgba(15,23,42,.08)}
@media (max-width:600px){main{margin:12px 12px 32px;padding:18px 16px}}
h1{font-size:28px;line-height:1.2;color:var(--ink);margin:0 0 6px}
h2,h3,h4{color:var(--ink);line-height:1.3;margin:22px 0 6px}
h4{font-size:17px}
p,ul,ol{margin:0 0 12px}ul,ol{padding-left:22px}li{margin:3px 0}
a{color:var(--blue)}
.lg-date{font-size:13px;color:var(--muted);margin-bottom:14px}
.lg-key{background:var(--key);border-radius:12px;padding:12px 14px;margin:0 0 16px;color:var(--ink)}
footer{max-width:760px;margin:0 auto 40px;padding:0 16px;font-size:13px;color:var(--muted)}
</style>
</head>
<body>
<header><a class="brand" href="/"><img src="/icon-192.png" alt="">TermChamp</a></header>
<nav aria-label="Legal and support">${nav}</nav>
<main>
<h1>${esc(title)}</h1>
${body}
</main>
<footer>TermChamp is an independent app built by Cal Poly students. It is not affiliated with, endorsed by, or operated by California Polytechnic State University.</footer>
</body>
</html>
`;
}

// ---- 3. the support page -------------------------------------------------------------------------
export function supportBody(contact) {
  const mail = `<a href="mailto:${esc(contact)}">${esc(contact)}</a>`;
  return `<div class="lg-key">Email ${mail}. TermChamp is run by Cal Poly students, and we read every message.</div>
<h4>Get help with your account</h4>
<ul>
<li><b>Can’t sign in?</b> TermChamp signs you in with your school email. Use “Email me a code,” or set a password in Settings → Account once you’re in.</li>
<li><b>Wrong class, professor, or seat count?</b> Email us the course and section. Seat counts come from Cal Poly’s public class search and refresh through the day.</li>
<li><b>Something broken?</b> Tell us what you tapped, what you expected, and what happened. A screenshot helps.</li>
</ul>
<h4>Report a review, message, or person</h4>
<ul>
<li><b>A review:</b> open it and tap <b>Report this review</b>.</li>
<li><b>A person or a chat:</b> tap <b>⋯</b> on their profile or in your chat with them, then <b>Report</b> or <b>Block</b>. Blocking is immediate and they aren’t told.</li>
<li><b>Professors and staff:</b> if a review about you breaks the <a href="/guidelines">Community Guidelines</a>, email ${mail} with the course and what it says. We review every report within 24 hours and remove content that breaks the rules.</li>
</ul>
<h4>Delete your account</h4>
<p>In the app: <b>Profile → Settings → Delete account</b>. Your account is hidden right away and permanently deleted after 30 days. Details are in the <a href="/privacy">Privacy Policy</a>. If you can’t sign in anymore, email ${mail} from your school address and we’ll delete it for you.</p>
<h4>Your data</h4>
<p>For a copy of your data or a correction, email ${mail}. See the <a href="/privacy">Privacy Policy</a> for what is collected and who can see it.</p>`;
}

// ---- 4. write them ---------------------------------------------------------------------------------
function main() {
  const src = readFileSync(join(ROOT, 'app', 'planner.js'), 'utf8');
  const { docs, contact } = loadLegal(src);
  const pages = [
    { slug: 'privacy', title: 'Privacy Policy', body: docs.privacy.html, description: 'What TermChamp collects, who can see it, and how to delete it.' },
    { slug: 'terms', title: 'Terms of Service', body: docs.terms.html },
    { slug: 'guidelines', title: 'Community Guidelines', body: docs.guidelines.html, description: 'The rules for reviews and messages on TermChamp.' },
    { slug: 'security', title: 'Security', body: docs.security.html },
    { slug: 'support', title: 'Support', body: supportBody(contact || 'support@termchamp.com'), description: 'Get help with TermChamp, report content, or delete your account.' },
  ];
  for (const p of pages) {
    const dir = join(OUT, p.slug);
    mkdirSync(dir, { recursive: true });
    writeFileSync(join(dir, 'index.html'), page(p));
    console.log(`published  /${p.slug}`);
  }
}

if (process.argv[1] && fileURLToPath(import.meta.url) === process.argv[1]) main();
