/* Screenshots for Tate: Home on a normal Fall day vs. Thanksgiving week. */
import { openApp } from '/home/claude/tc/app-icon/app-dev/tests/app-harness.mjs';
import { tick, liveTables, nextPort } from './lib.mjs';
const OUT = process.env.SHOTS || '/tmp/claude-0/shots';
for (const [name, at] of [['normal-tue-nov-17', '2026-11-17T10:40:00-08:00'], ['thanksgiving-tue-nov-24', '2026-11-24T10:40:00-08:00'], ['finals-tue-dec-15', '2026-12-15T10:40:00-08:00']]) {
  const { page, close } = await openApp({ terms: 'live', tables: liveTables(), time: at, port: nextPort() });
  await page.waitForFunction(() => TC.ready, null, { timeout: 10000 }).catch(() => {});
  await page.clock.runFor(61000); await page.evaluate(() => render(true)); await tick(page, 600);
  await page.screenshot({ path: `${OUT}/${name}.png`, clip: { x: 0, y: 0, width: 390, height: 360 } });
  await page.locator('.stories .story', { hasText: 'Avery' }).first().click().catch(() => {}); await tick(page, 900);
  await page.screenshot({ path: `${OUT}/${name}-story.png` });
  await close();
}
console.log('shots done');
