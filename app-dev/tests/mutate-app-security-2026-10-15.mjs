/* Mutation check for check-app-security-2026-10-15: each mutant reverts or breaks ONE promise of security-app-2026-10-15.py in a
   temporary copy of app/index.html; check-app-security-2026-10-15 must FAIL (in the named section) on every one.
   Run: SRC_DIR=<repo root> node mutate-app-security-2026-10-15.mjs   (MUT_ONLY="name|name"; APP_PORT to move off 8190) */
import fs from 'node:fs'; import path from 'node:path'; import { execFileSync } from 'node:child_process';
const SRC = process.env.SRC_DIR || path.resolve('../..');
const HERE = path.dirname(new URL(import.meta.url).pathname);
const I = 'app/index.html';
const M = [
  /* 1. pdf.js */
  ['pdf: isEvalSupported is left on', "isOffscreenCanvasSupported: false, isEvalSupported: false })", "isOffscreenCanvasSupported: false })", 'pdf'],
  ['pdf: the script loses its integrity', "s.integrity = 'sha384-OemFRmhjDZwhIKuUld0HJozkF2YErsgDaCL41trxGQZt4/WgnopJQqQl2DvDZ07Z'; s.crossOrigin = 'anonymous';", "", 'pdf'],
  /* 2. invite */
  ['invite: opening the link sends the request again', "  UI.sheet = { type: 'inviteAsk', id, name, err: '', busy: false }; render(true);\n};", "  TC._inviteAsked = true; await TC.sendRequest(id);\n};", 'invite'],
  ['invite: an incoming request is accepted by the link', "  TC._inviteAsked = true; TC._inviteTries = 0;\n  UI.sheet = { type: 'inviteAsk'", "  TC._inviteAsked = true; TC._inviteTries = 0;\n  if (rel === 'incoming') { await TC.acceptRequest(id); try { localStorage.removeItem(INVITE_KEY); } catch (e) {} return; }\n  UI.sheet = { type: 'inviteAsk'", 'invite'],
  ['invite: Add on an incoming request sends a second request', "rel === 'incoming' ? await TC.acceptRequest(id) : await TC.sendRequest(id)", "await TC.sendRequest(id)", 'invite'],
  ['invite: Not now leaves the invite', "  inviteNo: () => {   /* Not now: answered, nothing written */\n    try { localStorage.removeItem(INVITE_KEY); } catch (e) {}\n", "  inviteNo: () => {   /* Not now: answered, nothing written */\n", 'invite'],
  ['invite: Add leaves the invite behind', "    try { localStorage.removeItem(INVITE_KEY); } catch (e) {}\n    const first =", "    const first =", 'invite'],
  ['invite: a failed send throws the invite away', "if (!ok) { if (UI.sheet === sh) { sh.err = 'Couldn’t add them. Check your connection and try again.'; render(true); } return; }", "if (!ok) { try { localStorage.removeItem(INVITE_KEY); } catch (e) {} A.closeSheet(); return; }", 'invite'],
  ['invite: the name is not escaped', "const who = name ? esc(name) : 'this person'", "const who = name ? name : 'this person'", 'invite'],
  ['invite: the name is never shown', "const who = name ? esc(name) : 'this person'", "const who = 'this person'", 'invite'],
  ['invite: friends are asked about again', [["if (rel0 === 'friends' || rel0 === 'sent') { drop(); return; }", "if (false) { drop(); return; }"], ["if (rel === 'friends' || rel === 'sent') { drop(); return; }\n  if (UI.sheet", "if (false) { drop(); return; }\n  if (UI.sheet"]], null, 'invite'],
  ['invite: your own link is a question', "if (id === TC.user.id || isBlocked(id)) { drop(); return; }", "if (isBlocked(id)) { drop(); return; }", 'invite'],
  ['invite: two taps, two requests', "if (!sh || sh.type !== 'inviteAsk' || sh.busy) return;", "if (!sh || sh.type !== 'inviteAsk') return;", 'invite'],
  ['invite: a refresh asks again', [["  if (TC._inviteAsked || !TC.user) return;\n  const id = pendingInvite();", "  if (!TC.user) return;\n  const id = pendingInvite();"], ["  if (TC._inviteAsked || !TC.user || pendingInvite() !== id) return;", "  if (!TC.user || pendingInvite() !== id) return;"]], null, 'invite'],
  ['invite: kept forever', "Date.now() - (+v.at || 0) < 14 * 864e5", "true", 'invite'],
  ['invite: kept one day', "Date.now() - (+v.at || 0) < 14 * 864e5", "Date.now() - (+v.at || 0) < 1 * 864e5", 'invite'],
  /* 3. wipe */
  ['wipe: sign-out wipes nothing', "await TC.pushForget(false); TC.wipeDevice(); try { await TC.client().auth.signOut(); } catch (e) {} TC.wipeDevice(true);", "await TC.pushForget(false); try { await TC.client().auth.signOut(); } catch (e) {}", 'wipe'],
  ['wipe: sign-out does not wipe again after the server call (session keys survive a failed sign-out)', "catch (e) {} TC.wipeDevice(true); location.replace", "catch (e) {} location.replace", 'wipe'],
  ['wipe: delete wipes nothing', [["  TC.wipeDevice();   /* security-app (2026-10-15): everything of theirs", "  /* security-app (2026-10-15): everything of theirs"], ["catch (e) {}\n  TC.wipeDevice(true);", "catch (e) {}"]], null, 'wipe'],
  ['wipe: delete forgets the second wipe', "catch (e) {}\n  TC.wipeDevice(true);", "catch (e) {}", 'wipe'],
  ['wipe: tc- keys are not wiped', "const WIPE_PREFIXES = ['tc-', 'tc_', 'professify', 'termchamp'];", "const WIPE_PREFIXES = ['tc_', 'professify', 'termchamp'];", 'wipe'],
  ['wipe: tc_ keys are not wiped', "const WIPE_PREFIXES = ['tc-', 'tc_', 'professify', 'termchamp'];", "const WIPE_PREFIXES = ['tc-', 'professify', 'termchamp'];", 'wipe'],
  ['wipe: professify keys are not wiped', "const WIPE_PREFIXES = ['tc-', 'tc_', 'professify', 'termchamp'];", "const WIPE_PREFIXES = ['tc-', 'tc_', 'termchamp'];", 'wipe'],
  ['wipe: termchamp keys are not wiped', "const WIPE_PREFIXES = ['tc-', 'tc_', 'professify', 'termchamp'];", "const WIPE_PREFIXES = ['tc-', 'tc_', 'professify'];", 'wipe'],
  ['wipe: sessionStorage is skipped', "[['localStorage'], ['sessionStorage']].forEach", "[['localStorage']].forEach", 'wipe'],
  ['wipe: the theme is wiped too', "const WIPE_KEEP = ['tc-theme', 'termchamp_app_seats_v1', 'professify_prof_cache', 'tc_deleted'];", "const WIPE_KEEP = ['termchamp_app_seats_v1', 'professify_prof_cache', 'tc_deleted'];", 'wipe'],
  ['wipe: the public caches are wiped too', "const WIPE_KEEP = ['tc-theme', 'termchamp_app_seats_v1', 'professify_prof_cache', 'tc_deleted'];", "const WIPE_KEEP = ['tc-theme', 'tc_deleted'];", 'wipe'],
  ['wipe: the deletion note is wiped (the sign-in screen forgets to say)', "const WIPE_KEEP = ['tc-theme', 'termchamp_app_seats_v1', 'professify_prof_cache', 'tc_deleted'];", "const WIPE_KEEP = ['tc-theme', 'termchamp_app_seats_v1', 'professify_prof_cache'];", 'wipe'],
  ['wipe: the auth keys are never removed', "(auth && /^sb-.*-(auth-token|code-verifier)/.test(k))", "false", 'wipe'],
  ['wipe: other sites’ keys are wiped too', "if (WIPE_PREFIXES.some(p => k.indexOf(p) === 0) ||", "if (true ||", 'wipe'],
  /* 4. avatars */
  ['avatar: any https URL again', "  if (u.indexOf(AVATAR_BASE) !== 0) return '';\n  try {", "  if (/^https:\\/\\//.test(u)) return u;\n  try {", 'avatar'],
  ['avatar: no check after normalisation', "return new URL(u).href.indexOf(AVATAR_BASE) === 0 ? u : '';", "return u;", 'avatar'],
  ['avatar: svg data URLs allowed', "/^data:image\\/(png|jpe?g|webp|gif);base64,", "/^data:image\\/(png|jpe?g|webp|gif|svg\\+xml);base64,", 'avatar'],
  ['avatar: no data: preview', "  if (/^data:image\\/(png|jpe?g|webp|gif);base64,[A-Za-z0-9+\\/=]+$/.test(u)) return u;\n", "", 'avatar'],
  ['avatar: the bucket is any storage path', "const AVATAR_BASE = 'https://rqkndeqbcahozidniesn.supabase.co/storage/v1/object/public/avatars/';", "const AVATAR_BASE = 'https://rqkndeqbcahozidniesn.supabase.co/storage/v1/object/public/';", 'avatar'],
  ['avatar: no-referrer dropped from the avatar image', "alt=\"\" loading=\"lazy\" referrerpolicy=\"no-referrer\" style=\"grid-area:1/1;width:100%;height:100%;object-fit:cover\" onerror=\"this.remove()\">", "alt=\"\" loading=\"lazy\" style=\"grid-area:1/1;width:100%;height:100%;object-fit:cover\" onerror=\"this.remove()\">", 'avatar'],
  /* 5. auth */
  ['auth: back to the implicit flow', "    flowType: 'pkce' } });", "    flowType: 'implicit' } });", 'auth'],
  ['auth: no flowType (the old default)', ",\n    /* security-app (2026-10-15): PKCE, like the website.", ",\n    /* security-app (2026-10-15): PKCE, like the website.", 'auth', 'special-noflow'],
];
const orig = fs.readFileSync(path.join(SRC, I), 'utf8');
const tmp = fs.mkdtempSync('/tmp/claude-0/mutt-app-');
for (const e of fs.readdirSync(SRC)) if (e !== 'app' && e !== '.git') fs.symlinkSync(path.join(SRC, e), path.join(tmp, e));
fs.mkdirSync(path.join(tmp, 'app'));
for (const e of fs.readdirSync(path.join(SRC, 'app'))) if (e !== 'index.html') fs.symlinkSync(path.join(SRC, 'app', e), path.join(tmp, 'app', e));
let caught = 0, ran = 0; const survived = [];
const ONLY = process.env.MUT_ONLY ? process.env.MUT_ONLY.split('|') : null;
for (const [name, a, b, test, special] of M) {
  if (ONLY && !ONLY.includes(name)) continue;
  ran++;
  let src;
  if (special === 'special-noflow') {
    /* drop the flowType property altogether */
    const x = "detectSessionInUrl: true,\n    /* security-app (2026-10-15): PKCE, like the website."; const y = "    flowType: 'pkce' } });";
    if (orig.split(x).length !== 2 || orig.split(y).length !== 2) { console.log('  BAD MUTANT:', name); survived.push(name + ' (bad)'); continue; }
    src = orig.replace(y, "    } });");
  } else {
    const pairs = Array.isArray(a) ? a : [[a, b]]; src = orig; let bad = false;
    for (const [x, y] of pairs) { const n = src.split(x).length - 1; if (n !== 1) { console.log('  BAD MUTANT (found ' + n + '×):', name, x.slice(0, 60)); bad = true; break; } src = src.split(x).join(y); }
    if (bad) { survived.push(name + ' (bad)'); continue; }
  }
  fs.writeFileSync(path.join(tmp, I), src);
  let failed = false, out = '';
  try { execFileSync('node', [path.join(HERE, 'check-app-security-2026-10-15.mjs'), '--quiet', '--only', test], { env: { ...process.env, APP_DIR: tmp }, stdio: 'pipe', timeout: 400000 }); }
  catch (e) { failed = true; out = String(e.stdout || '') + String(e.stderr || ''); }
  if (failed && (!/check-app-security-2026-10-15: \d+ passed, [1-9]\d* failed/.test(out) || /EADDRINUSE/.test(out))) { console.log('  BROKE   ', name, '— the run crashed; rerun it'); survived.push(name + ' (broke)'); continue; }
  if (failed) { caught++; console.log('  caught  ', name); } else { survived.push(name); console.log('  SURVIVED', name); }
}
console.log(`\nmutations: ${caught}/${ran} caught`);
if (survived.length) { console.log('survived:', survived.join(' | ')); process.exit(1); }
