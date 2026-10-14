/* screenshots for the identity look: APP_DIR=<repo> node shot-identity.mjs <outdir>  (not part of the suite) */
import { openApp } from './app-harness.mjs';
const out = process.argv[2] || '/tmp/claude-0/shots-identity';
const tick = async (p, ms = 400) => { await p.clock.runFor(ms); await p.waitForTimeout(250); };
for (const [w, h] of [[1440, 900], [390, 844]]) for (const th of ['light', 'dark']) {
  const { page, close } = await openApp({ path: '/', width: w, height: h, wait: 4000 });
  await page.evaluate(t => { try { setTheme(t); } catch (e) {} }, th); await tick(page, 1500);
  await page.screenshot({ path: `${out}/home-${w}-${th}.png` });
  await page.evaluate(() => { show('friends'); }); await tick(page, 1500);
  await page.screenshot({ path: `${out}/friends-${w}-${th}.png` });
  await close();
}
console.log('done');
