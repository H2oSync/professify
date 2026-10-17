/* Screenshots for chat-cards (2026-10-16): the group chat with shared schedules, dark theme.
   Run: APP_DIR=<repo> node shot-chat-cards.mjs <outdir> <label>   (APP_PORT to move off 8190) */
import fs from 'node:fs';
import { openApp } from './app-harness.mjs';
import * as FX from './app-fixtures.mjs';
const dir = process.argv[2] || '.', label = process.argv[3] || 'after';
fs.mkdirSync(dir, { recursive: true });
const port = +(process.env.APP_PORT || 8190);
const ME = FX.ME, AV = FX.FRIENDS[0], SUG = FX.SUGGESTED, C1 = FX.CONVS[1].id;
const H1 = 'cc68d9c41252dde55d5fb8b2211a8336', H2 = '797c01b109fbf947b4dfc83ac083c199';
const L = (h, q) => 'https://termchamp.com/s?i=' + h + '.png&' + q;
const mk = (id, sender, body, min) => ({ id, conversation_id: C1, sender, kind: 'text', body, payload: null, created_at: '2026-10-15T18:' + String(10 + min) + ':00Z' });
const t = JSON.parse(JSON.stringify(FX.TABLES));
t.conversation_members.push({ conversation_id: C1, user_id: SUG.id, last_read_at: null });
t.messages = [
  mk(11, ME.id, 'Here’s my Fall 2026 schedule ' + L(H1, 'nm=Tate&tm=Fall%202026&add=' + ME.id), 0),
  mk(12, AV.id, 'The link ain’t work', 1),
  mk(13, SUG.id, 'Here’s my Plan A for Spring 2027 ' + L(H2, 'nm=Sean&tm=Spring%202027&add=' + SUG.id + '&pl=A'), 2),
  mk(14, AV.id, 'these are still sending links and not cards', 3),
];
// the picture: draw it with the app's own card canvas, then serve it for every schedule-cards url
const pre = await openApp({ path: '/', width: 1300, height: 900, wait: 3000, port });
const png = await pre.page.evaluate(() => { try { return schedCardCanvas({ name: 'Tate', term: 'Fall 2026' }).toDataURL('image/png').split(',')[1]; } catch (e) { return ''; } });
await pre.close();
const buf = png ? Buffer.from(png, 'base64') : null;
const hook = (url, m) => (buf && m === 'GET' && /^\/storage\/v1\/object\/public\/schedule-cards\/[0-9a-f]{32}\.png$/.test(url.pathname)) ? { status: 200, contentType: 'image/png', body: buf } : null;
for (const [name, w, h] of [['desk', 1300, 900], ['phone', 390, 844]]) {
  const o = await openApp({ path: '/', width: w, height: h, wait: 4000, port, tables: t, hook, init: () => { try { localStorage.setItem('professify-theme', 'dark'); } catch (e) {} } });
  const tick = async ms => { await o.page.clock.runFor(ms); await o.page.waitForTimeout(250); };
  for (let i = 0; i < 20; i++) { const r = await o.page.evaluate(() => typeof friendsLoaded !== 'undefined' && friendsLoaded && !frSignInBusy); if (r) break; await tick(300); }
  await o.page.evaluate(() => show('friends')); await tick(800);
  await o.page.evaluate(() => msgLoadThreads()); await tick(800);
  await o.page.evaluate(c => msgOpen(c), C1); await tick(1200);
  await o.page.screenshot({ path: `${dir}/${label}-${name}-chat.png` });
  if (label === 'after') {
    await o.page.evaluate(() => { const b = document.querySelector('#msgBody .ssc .msug-b'); if (b) b.click(); }); await tick(500);
    await o.page.screenshot({ path: `${dir}/${label}-${name}-view.png` });
    await o.page.evaluate(() => schedCardClose());
    await o.page.evaluate(() => shareMySchedule()); await tick(800);
    await o.page.screenshot({ path: `${dir}/${label}-${name}-sendsheet.png` });
    await o.page.evaluate(() => { const b = [...document.querySelectorAll('#scSheet .fr-chip')].find(x => /Send to a chat/.test(x.innerText)); if (b) b.click(); }); await tick(600);
    await o.page.screenshot({ path: `${dir}/${label}-${name}-picker.png` });
  }
  console.log(name, 'errors', JSON.stringify(o.log.errors));
  await o.close();
}
