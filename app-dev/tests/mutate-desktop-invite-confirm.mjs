/* Mutation check for check-desktop-invite-confirm: each mutant breaks one promise of the client hardening
   (security-client-hardening, 2026-10-14); check-desktop-invite-confirm must FAIL on every one.
   Run: SRC_DIR=<repo> node mutate-desktop-invite-confirm.mjs  (MUT_ONLY="a|b"; APP_PORT to move off 8190) */
import fs from 'node:fs'; import path from 'node:path'; import { execFileSync } from 'node:child_process';
const SRC = process.env.SRC_DIR || path.resolve('../..');
const HERE = path.dirname(new URL(import.meta.url).pathname);
const I = 'index.html', S = 'sw.js';
const M = [
  ['invite: opening the link sends the request again', I, "  if(pendAddBlocked()){ pendAddLater(); return; }\n  pendAddPaint(id,name);\n}", "  if(pendAddBlocked()){ pendAddLater(); return; }\n  sendFriendRequest(id);\n}", 'card'],
  ['invite: Not now does not clear the invite', I, "if(!yes){ pendAddClear(); closeModal(); return; }", "if(!yes){ closeModal(); return; }", 'card'],
  ['invite: Not now sends the request', I, "  if(!yes){ pendAddClear(); closeModal(); return; }                       /* Not now: answered, nothing written */\n", "", 'card'],
  ['invite: Add leaves the invite behind', I, "  pendAddClear();\n  closeModal();\n  show('friends');", "  closeModal();\n  show('friends');", 'card'],
  ['invite: two taps, two requests', I, "  if(window._pendAddBusy)return;\n", "", 'card'],
  ['invite: a failed send throws the invite away', I, "/* sendFriendRequest said why; the invite stays */\n    if(btn){ btn.disabled=false; btn.textContent='Add'; }\n    return;", "/* sendFriendRequest said why; the invite stays */\n    pendAddClear(); closeModal(); return;", 'card'],
  ['invite: the card forgets the invite as it opens', I, "  pendAddPaint(id,name);\n}\n", "  pendAddClear();\n  pendAddPaint(id,name);\n}\n", 'card'],
  ['invite: the name is never shown', I, "var who=name?escapeHtml(name):'this person';", "var who='this person';", 'card'],
  ['invite: the name is not escaped', I, "var who=name?escapeHtml(name):'this person';", "var who=name?name:'this person';", 'card'],
  ['invite: friends are asked about again', I, "if(st==='friends'||st==='sent'){ pendAddClear(); return; }", "if(false){ pendAddClear(); return; }", 'card'],
  ['invite: your own link is a question', I, "if(!id||id===sbUser.id){ pendAddClear(); return; }", "if(!id){ pendAddClear(); return; }", 'card'],
  ['invite: the date is not kept', I, "st.setItem('professify_pending_add',id); st.setItem('professify_pending_add_at',now);", "st.setItem('professify_pending_add',id);", 'card'],
  ['invite: not kept for the new tab', I, "  try{ if(window.localStorage)out.push(window.localStorage); }catch(e){}\n", "", 'card'],
  ['invite: kept forever', I, "if(!UUID_RE.test(id)||Date.now()-at>TTL){", "if(!UUID_RE.test(id)){", 'expiry'],
  ['invite: kept one day', I, "var TTL=14*86400000,", "var TTL=1*86400000,", 'expiry'],
  ['invite: an undated invite is dropped', I, "if(!at){ at=Date.now(); st.setItem('professify_pending_add_at',String(at)); }", "if(!at){ st.removeItem('professify_pending_add'); return; }", 'expiry'],
  ['invite: the card opens under the shared-schedule page', I, "  if(window._schedLandingOpen)return true;", "", 'landing'],
  ['invite: the signed-out welcome blocks the card after sign-in', I, "if(window._inviteLandingOpen){ window._inviteLandingOpen=false;", "if(false){ window._inviteLandingOpen=false;", 'signedout'],
  ['pdf: isEvalSupported is left on', I, "isOffscreenCanvasSupported:false,isEvalSupported:false}", "isOffscreenCanvasSupported:false}", 'pdf'],
  ['sri: lazyScript sets no integrity', I, "      if(integrity){ el.integrity=integrity; el.crossOrigin='anonymous'; }\n", "", 'sri'],
  ['sri: no crossorigin', I, "el.integrity=integrity; el.crossOrigin='anonymous';", "el.integrity=integrity;", 'sri'],
  ['sri: tesseract floats on @5', I, "tesseract.js@5.1.1/dist/tesseract.min.js','Tesseract'", "tesseract.js@5/dist/tesseract.min.js','Tesseract'", 'sri'],
  ['sri: tesseract has no hash', I, "'Tesseract',45000,'sha384-GJqSu7vueQ9qN0E9yLPb3Wtpd7OrgK8KmYzC8T1IysG1bcvxvIO4qtYR/D3A991F')", "'Tesseract',45000)", 'sri'],
  ['sri: the qrcode hash is wrong', I, "sha384-8FWZA6BGMXhsfO+", "sha384-8FWZA6BGMYhsfO+", 'sri'],
  ['sri: pdf.js has no hash', I, "'pdfjsLib',45000,'sha384-OemFRmhjDZwhIKuUld0HJozkF2YErsgDaCL41trxGQZt4/WgnopJQqQl2DvDZ07Z')", "'pdfjsLib',45000)", 'sri'],
  ['sw: back to “starts with /”', S, "data: { url: safePushUrl(d.url) }", "data: { url: typeof d.url === 'string' && d.url.charAt(0) === '/' ? d.url : '/' }", 'sw'],
  ['sw: the origin is not compared', S, "    if (x.origin !== self.location.origin) return '/';\n", "", 'sw'],
  ['sw: the click trusts what was stored', S, "const target = safePushUrl(e.notification.data && e.notification.data.url);", "const target = (e.notification.data && e.notification.data.url) || '/';", 'sw'],
];
const files = { [I]: fs.readFileSync(path.join(SRC, I), 'utf8'), [S]: fs.readFileSync(path.join(SRC, S), 'utf8') };
const tmp = fs.mkdtempSync('/tmp/claude-0/mutt-');
for (const e of fs.readdirSync(SRC)) if (e !== I && e !== S && e !== '.git') fs.symlinkSync(path.join(SRC, e), path.join(tmp, e));
let caught = 0, ran = 0; const survived = [];
const ONLY = process.env.MUT_ONLY ? process.env.MUT_ONLY.split('|') : null;
for (const [name, file, a, b, test] of M) {
  if (ONLY && !ONLY.includes(name)) continue;
  ran++;
  const n = files[file].split(a).length - 1;
  if (n !== 1) { console.log('  BAD MUTANT (found ' + n + '×):', name); survived.push(name + ' (bad)'); continue; }
  for (const f of [I, S]) fs.writeFileSync(path.join(tmp, f), f === file ? files[f].split(a).join(b) : files[f]);
  let failed = false, out = '';
  try { execFileSync('node', [path.join(HERE, 'check-desktop-invite-confirm.mjs'), '--quiet', '--only', test], { env: { ...process.env, APP_DIR: tmp }, stdio: 'pipe', timeout: 400000 }); }
  catch (e) { failed = true; out = String(e.stdout || '') + String(e.stderr || ''); }
  if (failed && (!/check-desktop-invite-confirm: \d+ passed, [1-9]\d* failed/.test(out) || /EADDRINUSE/.test(out))) { console.log('  BROKE   ', name, '— the run crashed; rerun it'); survived.push(name + ' (broke)'); continue; }
  if (failed) { caught++; console.log('  caught  ', name); } else { survived.push(name); console.log('  SURVIVED', name); }
}
console.log(`\nmutations: ${caught}/${ran} caught`);
if (survived.length) { console.log('survived:', survived.join(' | ')); process.exit(1); }
