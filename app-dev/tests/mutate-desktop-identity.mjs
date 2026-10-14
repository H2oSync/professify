/* Mutation check for check-desktop-identity: each mutant breaks one promise of the website's phone identity
   (website-identity, 2026-10-14); check-desktop-identity must FAIL on every one.
   Run: SRC_DIR=<repo> node mutate-desktop-identity.mjs  (MUT_ONLY="a|b"; APP_PORT)
   A mutant is [name, from, to, test, expected count of `from` in index.html (default 1)]. */
import fs from 'node:fs'; import path from 'node:path'; import { execFileSync } from 'node:child_process';
const SRC = process.env.SRC_DIR || path.resolve('../..');
const M = [
  ["logo: not the phone's bytes", 'class="brand-logo lg-l" src="data:image/png;base64,iVBORw0KGgo', 'class="brand-logo lg-l" src="data:image/png;base64,iVBORw0KGgp', 'logo'],
  ["logo: the dark logo is never swapped in", ':root[data-theme="dark"] .brand .brand-logo.lg-l{display:none}\n', '', 'logo'],
  ["logo: both logos shown in dark", ':root[data-theme="dark"] .brand .brand-logo.lg-d{display:block}\n', '', 'logo'],
  ["logo: the TC tile still shows beside it", '.brand .brand-tile{display:none}\n@media (max-width:760px)', '.brand .brand-tile{display:block}\n@media (max-width:760px)', 'logo'],
  ["logo: too small for the header", '.brand .brand-logo{display:block;height:36px;', '.brand .brand-logo{display:block;height:20px;', 'logo'],
  ["logo: no tile fallback when too narrow", '@media (max-width:340px){.brand img.brand-logo.lg-l,', '@media (max-width:1px){.brand img.brand-logo.lg-l,', 'logo'],
  ["logo: the logo crowds the tabs at 641-700px", '@media (min-width:641px) and (max-width:700px){.brand img.brand-logo.lg-l,', '@media (min-width:641px) and (max-width:1px){.brand img.brand-logo.lg-l,', 'logo'],
  ["logo: the typed wordmark is back", '<img class="brand-logo lg-l" src="data:image/png', '<span class="brand-wm">Term<b>Champ</b></span><img class="brand-logo lg-l" src="data:image/png', 'logo'],
  ["logo: the button loses its name", 'aria-label="TermChamp — go to home">\n      <!-- website-identity', 'aria-label="">\n      <!-- website-identity', 'logo'],
  ["nophoto: initials instead of the person", "    +' onerror=\"this.outerHTML=NOPH_SVG\">';\n  return NOPH_SVG;", "    +' onerror=\"this.outerHTML=NOPH_SVG\">';\n  return escapeHtml(initials(name||'?'));", 'nophoto'],
  ["nophoto: the old Instagram grey is back", "var AVA_GREY='var(--nophoto)';", "var AVA_GREY='#CBCBD0';", 'nophoto'],
  ["nophoto: a broken photo just disappears", 'onerror="this.outerHTML=NOPH_SVG">\';\n  return NOPH_SVG;', 'onerror="this.remove()">\';\n  return NOPH_SVG;', 'nophoto'],
  ["nophoto: not the phone's silhouette", "d='M3.2 24.5c.6-5.4 4.2-8.6 8.8-8.6s8.2 3.2 8.8 8.6z'", "d='M3.2 24.5c.9-5.4 4.2-8.6 8.8-8.6s8.2 3.2 8.8 8.6z'", 'nophoto'],
  ["nophoto: the person is not white", "<circle cx='12' cy='9.2' r='4.4' fill='#fff'/>", "<circle cx='12' cy='9.2' r='4.4' fill='#999'/>", 'nophoto'],
  ["nophoto: dark keeps the light grey", ':root[data-theme="dark"]{--nophoto:#3A4459}', ':root[data-theme="dark"]{--nophoto:#DADDE3}', 'nophoto'],
  ["nophoto: light grey is another grey", ':root{--nophoto:#DADDE3}', ':root{--nophoto:#CBCBD0}', 'nophoto'],
  ["nophoto: your own card keeps the panel colour", '#view-home .hm-id .fav:has(>svg.nophoto){background:var(--nophoto)}\n', '', 'nophoto'],
  ["nophoto: your own card shows initials", "  var n=myDisplayName();\n  return NOPH_SVG;\n}", "  var n=myDisplayName();\n  return n?escapeHtml(initials(n)):PERSON_GLYPH;\n}", 'nophoto'],
  ["nophoto: the account pill shows an initial", "      : NOPH_SVG)+'</span><span>'+escapeHtml(nm)+'</span>'; }", "      : _ini)+'</span><span>'+escapeHtml(nm)+'</span>'; }", 'nophoto'],
  ["badge: the second badge is back over the pill", '    </div>\n    <button id="settingsBtn"', '      <span id="friendsNavBadge" class="wl-navbadge" hidden>0</span>\n    </div>\n    <button id="settingsBtn"', 'badge'],
  ["badge: the Friends tab loses its badge", '<span id="friendsNavBadge2" class="wl-navbadge" hidden>0</span>', '', 'badge'],
  ["dark: the old page ground", '--bg:#0A0F1C;--panel:#141B2B;--panel-2:#1C2539;--panel-3:#27314A;', '--bg:#0B1120;--panel:#151D2E;--panel-2:#1C2639;--panel-3:#222D42;', 'dark', 2],
  ["dark: the old header bar", '--nav-bg:rgba(20,27,43,.94);', '--nav-bg:rgba(15,21,35,.94);', 'dark', 2],
];
const html = fs.readFileSync(path.join(SRC, 'index.html'), 'utf8');
const tmp = fs.mkdtempSync('/tmp/claude-0/mutid-');
for (const e of fs.readdirSync(SRC)) if (e !== 'index.html' && e !== '.git') fs.symlinkSync(path.join(SRC, e), path.join(tmp, e));
let caught = 0; const survived = [];
const ONLY = process.env.MUT_ONLY ? process.env.MUT_ONLY.split('|') : null;
let ran = 0;
for (const [name, a, b, test, want = 1] of M) {
  if (ONLY && !ONLY.includes(name)) continue;
  ran++;
  const n = html.split(a).length - 1;
  if (n !== want) { console.log('  BAD MUTANT (found ' + n + '×, want ' + want + '):', name); survived.push(name + ' (bad)'); continue; }
  fs.writeFileSync(path.join(tmp, 'index.html'), html.split(a).join(b));
  let failed = false, out = '';
  try { execFileSync('node', ['check-desktop-identity.mjs', '--quiet', '--only', test], { env: { ...process.env, APP_DIR: tmp }, stdio: 'pipe', timeout: 300000 }); }
  catch (e) { failed = true; out = String(e.stdout || '') + String(e.stderr || ''); }
  if (failed && (!/check-desktop-identity: \d+ passed, [1-9]\d* failed/.test(out) || /EADDRINUSE/.test(out))) { console.log('  BROKE   ', name, '- the run crashed; rerun it'); survived.push(name + ' (broke)'); continue; }
  if (failed) { caught++; console.log('  caught  ', name); } else { survived.push(name); console.log('  SURVIVED', name); }
}
console.log(`\nmutations: ${caught}/${ran} caught`);
if (survived.length) { console.log('survived:', survived.join(' | ')); process.exit(1); }
