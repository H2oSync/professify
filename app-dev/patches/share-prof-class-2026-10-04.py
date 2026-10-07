#!/usr/bin/env python3
r"""Share a professor or a class by iMessage, with a preview (Tate, 2026-10-04: "make it so you can share a
professor and class on imessage and a small preview of the class or professor pops up and something like
blank shared a professor or class").

- The share button on a professor's or a class's page (the sheet that already sends a card inside TermChamp)
  now starts with a picture and "Send a link". The picture is drawn on the phone from what the page shows —
  real PolyRatings rating and count, department, the classes they teach this term; or the class's code, name,
  term, number of sections and who teaches it with their real ratings. No seat numbers (they go stale in a
  thread) and nothing about you or your friends: anyone with the link can see it.
- It goes up to the share-card bucket under a random name (insert only, as a shared week does), and "Send a
  link" stays disabled until it's up, because iMessage keeps the first preview it fetches for good.
- The link is termchamp.com/s?k=p|c&i=<id>.png&nm=<first name>&p=<professor>|c=<class>. /s writes
  "Tate shared a professor" / "Tate shared a class" as the preview's title (iMessage shows the title only)
  and the 1200×630 picture, then opens the page: the phone app (/app/?p= or ?c=) on a phone, the website's
  own ?p= / ?c= deep link anywhere else.
- `k` comes first in the query on purpose: a chat message carrying one of these links is not mistaken for a
  shared week (SH_RE wants /s?i=… right after /s?).
- The phone app opens ?p= / ?c= itself now: once you're in and the data is there, it opens that professor
  or class (after signing in, too). A professor or class it can't find says so.

Applies after schedule-share-top-2026-10-04.py. Also edits netlify/edge-functions/share.ts.
Usage: python3 share-prof-class-2026-10-04.py <repo-dir>
"""
import sys, os
root = sys.argv[1]
p = os.path.join(root, 'app', 'index.html')
s = open(p, encoding='utf-8').read()
if 'cardShPrepare' in s: sys.exit('already patched')

CODE = r'''/* ---- Share a professor or a class by link, with a picture (Tate, 2026-10-04) ------------------------ */
const dlSlug = x => String(x || '').toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '');
function cardShLink(kind, ref, id) {
  let q = 'k=' + (kind === 'class' ? 'c' : 'p') + '&i=' + id + '.png';
  const f = shFirst(); if (f) q += '&nm=' + encodeURIComponent(f);
  q += kind === 'class' ? '&c=' + encodeURIComponent(ref) : '&p=' + encodeURIComponent(dlSlug(PROFS[ref] ? PROFS[ref].name : ref));
  return String(WEB).replace(/\/+$/, '') + '/s?' + q;
}
/* 1200×630: iMessage draws it as a short card. Only what the page itself shows, from live data. */
function cardShCanvas(kind, ref) {
  const W = 1200, H = 630, cv = document.createElement('canvas'); cv.width = W; cv.height = H; const g = cv.getContext('2d');
  const F = (w, px) => w + ' ' + px + 'px Nunito, system-ui, -apple-system, sans-serif';
  const clip = (t, max) => { t = String(t); if (g.measureText(t).width <= max) return t; while (t.length > 1 && g.measureText(t + '…').width > max) t = t.slice(0, -1); return t + '…'; };
  const rr = (x, y, w, h, r) => { g.beginPath(); g.moveTo(x + r, y); g.arcTo(x + w, y, x + w, y + h, r); g.arcTo(x + w, y + h, x, y + h, r); g.arcTo(x, y + h, x, y, r); g.arcTo(x, y, x + w, y, r); g.closePath(); };
  const wrap2 = (t, max) => { const w = String(t).split(/\s+/); let a = ''; while (w.length && g.measureText((a ? a + ' ' : '') + w[0]).width <= max) a = (a ? a + ' ' : '') + w.shift(); if (!a) a = clip(w.shift() || '', max); const b = w.length ? clip(w.join(' '), max) : ''; return [a, b]; };
  const star = (cx, cy, R, col) => { g.beginPath(); for (let i = 0; i < 10; i++) { const a = -Math.PI / 2 + i * Math.PI / 5, r = i % 2 ? R * 0.45 : R; g.lineTo(cx + r * Math.cos(a), cy + r * Math.sin(a)); } g.closePath(); g.fillStyle = col; g.fill(); };
  g.fillStyle = '#F4F6FB'; g.fillRect(0, 0, W, H);
  g.font = F(900, 36); g.fillStyle = '#16336B'; g.fillText('Term', 64, 78); g.fillStyle = '#2563EB'; g.fillText('Champ', 64 + g.measureText('Term').width, 78);
  g.fillStyle = '#FFFFFF'; rr(48, 112, W - 96, H - 176, 40); g.fill();
  g.fillStyle = '#94A3B8'; g.font = F(800, 24); g.textAlign = 'right'; g.fillText('termchamp.com', W - 64, H - 26); g.textAlign = 'left';
  if (kind === 'class') {
    const c = course(ref), n = secsOf(ref).length, ps = courseProfs(ref).filter(Boolean).sort((a, b) => (ratingOf(b) ?? -1) - (ratingOf(a) ?? -1));
    g.font = F(900, 40); const cw = g.measureText(ref).width + 44;
    g.fillStyle = '#D6E4FF'; rr(104, 156, cw, 64, 20); g.fill(); g.fillStyle = '#1D4ED8'; g.fillText(ref, 126, 202);
    g.fillStyle = '#0F172A'; g.font = F(900, 54); const [l1, l2] = wrap2(courseName(ref) || c.title || ref, W - 220);
    g.fillText(l1, 104, 296); if (l2) g.fillText(l2, 104, 360);
    g.fillStyle = '#64748B'; g.font = F(800, 30); g.fillText(clip(CFG.TERM_LABEL + ' · ' + n + ' section' + (n === 1 ? '' : 's'), W - 220), 104, l2 ? 416 : 356);
    let x = 104; const y = l2 ? 482 : 430; g.font = F(800, 28);
    const more = ps.length - 3;
    ps.slice(0, 3).forEach((pk, i) => {
      const r = ratingOf(pk), nm = profName(pk), t = (i ? ' · ' : '') + nm;
      if (x > W - 260) return;
      g.fillStyle = '#334155'; g.fillText(clip(t, W - 120 - x), x, y); x += g.measureText(clip(t, W - 120 - x)).width;
      if (r != null && x < W - 200) { x += 10; star(x + 12, y - 10, 14, rateTone(r).ink); x += 28; g.fillStyle = rateTone(r).ink; g.font = F(900, 28); g.fillText(r.toFixed(1), x, y); x += g.measureText(r.toFixed(1)).width; g.font = F(800, 28); }
    });
    if (more > 0 && x < W - 260) { g.fillStyle = '#64748B'; g.fillText(' · +' + more + ' more', x, y); }
  } else {
    const P = PROFS[ref] || { name: ref, ini: '?' }, r = ratingOf(ref), t = profTone(r), teach = profCourses(ref);
    g.beginPath(); g.arc(196, 300, 100, 0, Math.PI * 2); g.fillStyle = t.bg; g.fill();
    g.fillStyle = t.ink; g.font = F(900, 72); g.textAlign = 'center'; g.fillText(P.ini || initialsOf(P.name), 196, 326); g.textAlign = 'left';
    g.fillStyle = '#0F172A'; g.font = F(900, 60); g.fillText(clip(P.name, W - 450), 336, 236);
    g.fillStyle = '#64748B'; g.font = F(800, 30); if (P.dept) g.fillText(clip(P.dept, W - 450), 336, 284);
    if (r != null) {
      const tn = rateTone(r); star(358, 352, 26, tn.ink); g.fillStyle = tn.ink; g.font = F(1000, 56); g.fillText(r.toFixed(1), 394, 372);
      const w = g.measureText(r.toFixed(1)).width; g.fillStyle = '#64748B'; g.font = F(800, 30); g.fillText(' · ' + nRatings(P.count), 400 + w, 370);
    } else { g.fillStyle = '#64748B'; g.font = F(800, 34); g.fillText('Not on PolyRatings yet', 336, 370); }
    if (teach.length) { g.fillStyle = '#334155'; g.font = F(800, 28); g.fillText(clip('Teaching ' + CFG.TERM_LABEL + ': ' + teach.join(', '), W - 440), 336, 440); }
  }
  return cv;
}
function cardShAlt(kind, ref) {
  if (kind === 'class') { const n = secsOf(ref).length, ps = courseProfs(ref).filter(Boolean).sort((a, b) => (ratingOf(b) ?? -1) - (ratingOf(a) ?? -1));
    return ref + ' · ' + (courseName(ref) || course(ref).title || '') + ' · ' + CFG.TERM_LABEL + ' · ' + n + ' section' + (n === 1 ? '' : 's') + ps.map(pk => ' · ' + profName(pk) + (ratingOf(pk) != null ? ' ' + ratingOf(pk).toFixed(1) : '')).join(''); }
  const P = PROFS[ref] || { name: ref }, r = ratingOf(ref);
  return P.name + (P.dept ? ' · ' + P.dept : '') + (r != null ? ' · ' + r.toFixed(1) + ' out of 5 from ' + nRatings(P.count) : ' · not on PolyRatings yet');
}
async function cardShPrepare(sc) {
  if (sc.ln && sc.ln.url) { try { URL.revokeObjectURL(sc.ln.url); } catch (e) {} }
  const ln = sc.ln = { state: 'draw' };
  /* never draw a rating that hasn't loaded yet: wait for PolyRatings (up to 15 s), and if it failed, say so */
  for (let i = 0; i < 60 && !TC.profsLoaded && !TC.err.poly; i++) { await new Promise(r => setTimeout(r, 250)); if (UI.card !== sc) return; }
  if (!TC.profsLoaded) { ln.state = 'err'; ln.why = 'Ratings didn’t load, so there’s no picture to send yet.'; render(true); return; }
  try { await Promise.race([document.fonts && document.fonts.load ? document.fonts.load('900 40px Nunito') : null, new Promise(r => setTimeout(r, 800))]); } catch (e) {}
  if (UI.card !== sc) return;
  const cv = cardShCanvas(sc.kind, sc.ref);
  const blob = await new Promise(r => { try { cv.toBlob(r, 'image/png'); } catch (e) { r(null); } });
  if (UI.card !== sc) return;
  ln.url = blob ? URL.createObjectURL(blob) : ''; ln.alt = cardShAlt(sc.kind, sc.ref);
  const key = 'card|' + sc.kind + '|' + sc.ref + '|' + ln.alt, hit = UI.shareCache[key];
  if (hit) { ln.id = hit; ln.link = cardShLink(sc.kind, sc.ref, hit); ln.state = 'ready'; render(true); return; }
  if (!blob) { ln.state = 'err'; render(true); return; }
  const id = shToken(); ln.id = id; ln.link = cardShLink(sc.kind, sc.ref, id); ln.state = 'up'; render(true);
  /* insert only, as a shared week: the bucket has no update policy */
  const r = await TC.client().storage.from(SC_BUCKET).upload(id + '.png', blob, { contentType: 'image/png' }).catch(e => ({ error: e }));
  if (UI.card !== sc) return;
  if (r && r.error) { try { console.warn('[share] card upload failed:', (r.error && r.error.message) || r.error); } catch (_) {} ln.state = 'err'; }
  else { UI.shareCache[key] = id; ln.state = 'ready'; }
  render(true);
}
/* ?p= / ?c= (a shared professor or class): open it once you're in and the data has loaded. */
const DL = (() => {
  let d = null;
  try { const q = new URLSearchParams(location.search), pp = q.get('p'), cc = q.get('c'); if (pp || cc) { d = { p: pp ? String(pp).slice(0, 80) : '', c: cc ? String(cc).slice(0, 16) : '' }; sessionStorage.setItem('tc-dl', JSON.stringify(d)); history.replaceState(null, '', location.pathname); } } catch (e) {}
  if (!d) { try { d = JSON.parse(sessionStorage.getItem('tc-dl') || 'null'); } catch (e) {} }
  return d && (d.p || d.c) ? d : null;
})();
let dlLeft = DL;
function dlTry() {
  const d = dlLeft; if (!d || !TC.ready) return;
  if (d.c) {
    if (!TC.seatsLoaded) return;
    dlLeft = null; try { sessionStorage.removeItem('tc-dl'); } catch (e) {}
    const code = canonCode(d.c);
    if (code && COURSES[code]) A.openClass(code); else toast('Couldn’t find that class in ' + CFG.TERM_LABEL);
    return;
  }
  if (!TC.profsLoaded && !TC.seatsLoaded) return;
  const want = dlSlug(d.p), key = Object.prototype.hasOwnProperty.call(PROFS, d.p) ? d.p : Object.keys(PROFS).find(k => dlSlug(k) === want || dlSlug(PROFS[k].name) === want);
  if (!key && !TC.profsLoaded && !TC.err.poly) return;   /* PolyRatings may still bring them */
  dlLeft = null; try { sessionStorage.removeItem('tc-dl'); } catch (e) {}
  if (key) A.openProf(key); else toast('Couldn’t find that professor — search for them in Explore');
}
'''

R = [
 ("SHEETS.sendCard = ({ kind, ref }) => {",
  CODE + "SHEETS.sendCard = ({ kind, ref }) => {"),
 # the sheet: picture + Send a link first, then TermChamp
 (" return `<div class=\"row sb\"><h3>Send ${esc(label)}</h3><button class=\"xbtn\" data-a=\"closeSheet\" aria-label=\"Close\">${ic('x', 16, 2.4)}</button></div>\n <div class=\"muted b\" style=\"font-size:14px;margin:4px 0 10px\">It shows in the chat as a card with ${isC ? 'the class and its seats' : 'their rating'}, read when it’s opened.</div>",
  " const ln = sc.ln || {}, off = !ln.link || ln.state !== 'ready';\n"
  " return `<div class=\"row sb\"><h3>Share ${esc(label)}</h3><button class=\"xbtn\" data-a=\"closeSheet\" aria-label=\"Close\">${ic('x', 16, 2.4)}</button></div>\n"
  " ${ln.url ? `<img class=\"shimg shwide\" src=\"${ln.url}\" alt=\"${esc(ln.alt || '')}\">` : `<div class=\"shimg shwide shwait\">${loadingCard('Drawing the preview…')}</div>`}\n"
  " ${ln.state === 'err' ? `<div class=\"tc-err\" style=\"margin:0 0 10px\">${esc(ln.why || 'Couldn’t get the link ready.')} <button class=\"link b\" style=\"color:var(--blue)\" data-a=\"cardLinkRetry\">Try again</button></div>` : ''}\n"
  " <button class=\"btn shgo\" data-a=\"cardLink\" ${off ? 'disabled' : ''}>${ic('share', 20, 2.4)}${navigator.share ? 'Send a link' : 'Copy the link'}</button>\n"
  " <div class=\"hint\" style=\"margin:8px 2px 0\">In iMessage it shows this picture and “${esc(shFirst() || 'Someone')} shared ${isC ? 'a class' : 'a professor'}”.</div>\n"
  " <div class=\"flabel\" style=\"margin:20px 0 4px\">Send to a friend in TermChamp</div>\n"
  " <div class=\"muted b\" style=\"font-size:14px;margin:4px 0 10px\">It shows in the chat as a card with ${isC ? 'the class and its seats' : 'their rating'}, read when it’s opened.</div>"),
 # open = prepare
 ("  sendCard: (kind, ref) => { if (!TC.user) return; UI.card = { kind, ref, sent: {}, busy: {} }; UI.sheet = { type: 'sendCard', kind, ref }; render(true); },",
  "  sendCard: (kind, ref) => { if (!TC.user) return; if (UI.card && UI.card.ln && UI.card.ln.url) { try { URL.revokeObjectURL(UI.card.ln.url); } catch (e) {} }\n"
  "    const sc = UI.card = { kind, ref, sent: {}, busy: {} }; UI.sheet = { type: 'sendCard', kind, ref }; render(true); cardShPrepare(sc); },\n"
  "  cardLink: () => { const ln = UI.card && UI.card.ln; if (!ln || !ln.link || ln.state !== 'ready') return;\n"
  "    if (navigator.share) { navigator.share({ url: ln.link }).catch(() => {}); return; }\n"
  "    try { navigator.clipboard.writeText(ln.link).then(() => toast('Link copied'), () => toast(ln.link)); } catch (e) { toast(ln.link); } },\n"
  "  cardLinkRetry: () => { const sc = UI.card; if (sc && sc.ln && sc.ln.state === 'err') cardShPrepare(sc); },"),
 (".shimg{display:block;width:100%;aspect-ratio:1/1;",
  ".shimg.shwide{aspect-ratio:1200/630}\n.shimg{display:block;width:100%;aspect-ratio:1/1;"),
 # deep link: try when the data lands
 ("  UI.storyOrder = null; TC.ready = true; TC.loadDone = Date.now(); render(true);\n",
  "  UI.storyOrder = null; TC.ready = true; TC.loadDone = Date.now(); render(true);\n  dlTry();\n"),
 ("  TC.seatsLoaded = true;\n}\nfunction shortTitle(",
  "  TC.seatsLoaded = true;\n  setTimeout(dlTry, 0);\n}\nfunction shortTitle("),
 ("  TC.profsLoaded = true;\n}\n",
  "  TC.profsLoaded = true;\n  setTimeout(dlTry, 0);\n}\n"),
]
for a, b in R:
    if s.count(a) != 1: sys.exit(f'anchor matched {s.count(a)}x: {a[:100]}')
    s = s.replace(a, b)
open(p, 'w', encoding='utf-8').write(s)

# ---- /s: a professor or class link gets its own title, picture size and destination ----
q = os.path.join(root, 'netlify', 'edge-functions', 'share.ts')
t = open(q, encoding='utf-8').read()
T = [
 ('  const plan = /^[ABC]$/.test(url.searchParams.get("pl") ?? "") ? (url.searchParams.get("pl") as string) : "";\n',
  '  const plan = /^[ABC]$/.test(url.searchParams.get("pl") ?? "") ? (url.searchParams.get("pl") as string) : "";\n'
  '  /* A shared PROFESSOR or CLASS (the phone app, 2026-10-04) carries k=p|c and p=<name slug> or c=<code>.\n'
  '     Both are matched against a shape: they only ever become ?p= / ?c= for the app, never markup. */\n'
  '  const kind = url.searchParams.get("k") === "p" ? "p" : url.searchParams.get("k") === "c" ? "c" : "";\n'
  '  const prof = (url.searchParams.get("p") ?? "").toLowerCase();\n'
  '  const cls  = (url.searchParams.get("c") ?? "").toUpperCase().replace(/\\s+/g, " ").trim();\n'
  '  const thing = kind === "p" && /^[a-z0-9-]{2,80}$/.test(prof) ? "p" : kind === "c" && /^[A-Z]{2,5} \\d{3,4}[A-Z]?$/.test(cls) ? "c" : "";\n'),
 ('  const title = plan\n',
  '  const title = thing\n'
  '    ? `${first || "Someone"} shared ${thing === "p" ? "a professor" : "a class"}`\n'
  '    : plan\n'),
 ('  const desc  = plan\n',
  '  const desc  = thing === "p"\n'
  '    ? "Their rating and the classes they teach, on TermChamp."\n'
  '    : thing === "c"\n'
  '    ? "Its sections, professors and seats, on TermChamp."\n'
  '    : plan\n'),
 ('  const go = "/" + (onward.toString() ? "?" + onward.toString() : "");\n',
  '  /* a professor or class goes to that page: the phone app on a phone, the website\'s own ?p= / ?c= elsewhere */\n'
  '  const thingQ = thing === "p" ? "p=" + encodeURIComponent(prof) : thing === "c" ? "c=" + encodeURIComponent(cls) : "";\n'
  '  const go = thing ? "/?" + thingQ : "/" + (onward.toString() ? "?" + onward.toString() : "");\n'
  '  const goApp = thing ? "/app/?" + thingQ : "";\n'
  '  const imgH = thing ? 630 : 1200;\n'
  '  const imgAlt = thing === "p" ? "A professor and their rating." : thing === "c" ? "A class and who teaches it." : "A week of classes with times and professors.";\n'),
 ('<meta property="og:image:height" content="1200">', '<meta property="og:image:height" content="${imgH}">'),
 ('<meta property="og:image:alt"    content="A week of classes with times and professors.">', '<meta property="og:image:alt"    content="${esc(imgAlt)}">'),
 ('    <a id="go" href="${esc(go)}">Open in TermChamp</a>', '    <a id="go" href="${esc(go)}"${goApp ? ` data-app="${esc(goApp)}"` : ""}>Open in TermChamp</a>'),
 ("  if(framed){ if(a)a.setAttribute('target','_top'); return; }\n",
  "  if(framed){ if(a)a.setAttribute('target','_top'); return; }\n"
  "  /* a phone opens a shared professor or class in the phone app */\n"
  "  var app=a&&a.getAttribute('data-app');\n"
  "  if(app&&/iPhone|iPod|Android.+Mobile|Mobile.+Safari/i.test(navigator.userAgent||'')) a.setAttribute('href',app);\n"),
]
if 'thingQ' in t: sys.exit('share.ts already patched')
for a, b in T:
    if t.count(a) != 1: sys.exit(f'share.ts anchor matched {t.count(a)}x: {a[:90]}')
    t = t.replace(a, b)
open(q, 'w', encoding='utf-8').write(t)
print('patched', p, 'and', q)
