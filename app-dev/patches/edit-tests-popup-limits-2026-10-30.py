#!/usr/bin/env python3
"""Tests for popup-limits-2026-10-30: the "a week / 30 days later" steps now also start a new day
(clear tc_pop_day), plus checks for one-a-day, the contacts cap (3) and the "Notifications are off" cap (2)."""
import sys, pathlib
d = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else 'app-dev/tests')
def edit(name, pairs):
    p = d / name; s = p.read_text()
    for a, b in pairs:
        n = s.count(a); assert n == 1, (name, a[:70], n); s = s.replace(a, b)
    p.write_text(s)
edit('check-push-popup-2026-10-30.mjs', [
("""  for (const n of [2, 3]) {
    await page.evaluate(() => localStorage.setItem('tc_push_snooze', String(Date.now() - 1000)));   // the week is up
    await relaunch(page);""",
"""  await page.evaluate(() => localStorage.setItem('tc_push_snooze', String(Date.now() - 1000)));   // the week is up, but it's the same day
  await relaunch(page);
  ok(await sheetType(page) === null, 'one pop-up a day: not again the same day, even on another open');
  for (const n of [2, 3]) {
    await page.evaluate(() => { localStorage.setItem('tc_push_snooze', String(Date.now() - 1000)); localStorage.removeItem('tc_pop_day'); });   // the week is up
    await relaunch(page);"""),
("""  await page.evaluate(() => localStorage.setItem('tc_push_snooze', String(Date.now() - 1000)));
  await relaunch(page);
  ok(await sheetType(page) === null, 'after 3 shows in all: never again');
  await page.evaluate(() => localStorage.setItem('tc_push_ask_n', '2'));""",
"""  await page.evaluate(() => { localStorage.setItem('tc_push_snooze', String(Date.now() - 1000)); localStorage.removeItem('tc_pop_day'); });
  await relaunch(page);
  ok(await sheetType(page) === null, 'after 3 shows in all: never again');
  await page.evaluate(() => { localStorage.setItem('tc_push_ask_n', '2'); localStorage.removeItem('tc_pop_day'); });"""),
("""  ok(await sheetType(page) === null && await page.evaluate(() => Date.now() - +localStorage.getItem('tc_push_off_at') < 60000), 'shown again: the 30-day clock restarts; Not now closes');
  await relaunch(page);
  ok(await sheetType(page) === null, 'next open: not again');
  await close();
}""",
"""  ok(await sheetType(page) === null && await page.evaluate(() => Date.now() - +localStorage.getItem('tc_push_off_at') < 60000), 'shown again: the 30-day clock restarts; Not now closes');
  ok(await ls(page, 'tc_push_off_n') === '1', '"Notifications are off": counted (1 of 2)');
  await relaunch(page);
  ok(await sheetType(page) === null, 'next open: not again');
  await close();
}
{
  // "Notifications are off" has been shown twice already: never again, on an open or after a tap
  const { page, close } = await openApp({ port: +(process.env.APP_PORT || 9061), init: shim('denied', { createdDaysAgo: 40, ls: { tc_push_off_at: -61 * DAY } }) + "localStorage.setItem('tc_push_off_n', '2');" });
  await readyOf(page); await run(page, 2500);
  ok(await sheetType(page) === null, '"Notifications are off": after 2 shows in all, never again on an open');
  await page.evaluate(() => TC.pushAsk('chat')); await run(page, 300);
  ok(await sheetType(page) === null, '"Notifications are off": nor after sending a chat');
  await close();
}"""),
])
edit('check-app-contacts-2026-10-30.mjs', [
("""  await page.evaluate(() => ctSet({ snooze: Date.now() - 1 }));
  ok(await page.evaluate(() => ctAsk('later')) === true, '30 days later it may ask once more');""",
"""  await page.evaluate(() => ctSet({ snooze: Date.now() - 1 }));
  ok(await page.evaluate(() => ctAsk('later')) === false, 'one pop-up a day: not again the same day');
  await page.evaluate(() => localStorage.removeItem('tc_pop_day'));
  ok(await page.evaluate(() => ctAsk('later')) === true, '30 days later it may ask once more');"""),
("""  ok(await page.evaluate(() => ctAsk('later')) === false, 'connected: never asks again');""",
"""  ok(await page.evaluate(() => ctAsk('later')) === false, 'connected: never asks again');
  await page.evaluate(() => { localStorage.removeItem('tc_pop_day'); ctSet({ on: false, snooze: 0, k: 3 }); });
  ok(await page.evaluate(() => ctAsk('later')) === false && await page.evaluate(() => TC.pops[0].due('open')) === null, 'asked 3 times in all: never again');
  await page.evaluate(() => { ctSet({ k: 2 }); localStorage.setItem('tc_pop_day', popToday()); });
  ok(await page.evaluate(() => ctAsk('onboarding')) === true, 'end of sign-up: may follow the notifications pop-up the same day');
  await page.evaluate(() => { UI.sheet = null; render(true); });"""),
])
print('tests: popup limits')
