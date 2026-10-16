/* Screenshots of Home (desktop) for the websync change: the registration banner/card and the stories strip.
   Run: APP_DIR=<repo> node shot-websync.mjs <out.png> [--pins] [--w=1440]   (APP_PORT to move off 8190) */
import { openApp } from './app-harness.mjs';
import * as FX from './app-fixtures.mjs';
const out = process.argv[2] || '/tmp/claude-0/sec/shots/websync-shot.png';
const pins = process.argv.includes('--pins');
const W = +((process.argv.find(a => a.startsWith('--w=')) || '--w=1440').slice(4));
const t = JSON.parse(JSON.stringify(FX.TABLES));
const FR = FX.FRIENDS;
const rpc = Object.assign({}, FX.RPC, pins ? { my_pinned_friends: [FR[3].id, FR[0].id], set_pinned_friends: [] } : {});
const o = await openApp({ path: '/', width: W, height: 1000, wait: 4000, terms: 'live', time: '2026-10-14T10:30:00-07:00', tables: t, rpc });
for (let i = 0; i < 20; i++) { await o.page.clock.runFor(300); await o.page.waitForTimeout(150); }
await o.page.evaluate(() => { try { show('home'); renderHome(); } catch (e) {} });
await o.page.clock.runFor(800); await o.page.waitForTimeout(400);
await o.page.screenshot({ path: out });
console.log('saved', out, 'errors', JSON.stringify(o.log.errors));
await o.close();
