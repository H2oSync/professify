#!/usr/bin/env python3
"""Connect contacts (2026-10-30), the two existing tests it touches (app-dev/tests/check-app.mjs):
  · tests.signup walked straight from "Looks good" to People you may know; sign-up now asks for the
    phone number (optional) in between, so it sees that step, taps Skip, and checks Skip sent nothing.
  · tests.friendsSearch found "the" .invpill; the Friends header now has two (Contacts, Invite), so it
    names the Invite one. Its checks (top right, beside the title, small, 44px) are unchanged."""
import sys, pathlib
p = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else 'app-dev/tests/check-app.mjs'); s = p.read_text()
def one(a, b):
    global s
    n = s.count(a); assert n == 1, (a[:70], n); s = s.replace(a, b)
one("""'confirm: saves year and major to your profile', up && up.body);
  t = await text(page);
  ok(/People you may know/.test(t) && /Invite a friend/.test(t), 'onboard: people you may know');""",
"""'confirm: saves year and major to your profile', up && up.body);
  t = await text(page);
  ok(/Help friends find you/.test(t) && await page.locator('#ob-phone[type="tel"]').count() === 1 && await page.locator('[data-a="ctPhoneSkip"]').count() === 1, 'onboard: then the optional phone step, with Skip', t.slice(0, 200));
  await click(page, '[data-a="ctPhoneSkip"]');
  ok(!log.rpcs.some(r => r.fn === 'set_my_phone'), 'onboard: Skip sends no number');
  t = await text(page);
  ok(/People you may know/.test(t) && /Invite a friend/.test(t), 'onboard: people you may know');""")
one("""ib = await page.locator('.fhdr .invpill').boundingBox()""", """ib = await page.locator('.fhdr .invpill[data-x="invite"]').boundingBox()""")
one("""/^Invite$/.test((await page.locator('.invpill').innerText()).trim())""", """/^Invite$/.test((await page.locator('.invpill[data-x="invite"]').innerText()).trim())""")
one("""  await click(page, '.invpill');""", """  await click(page, '.invpill[data-x="invite"]');""")
p.write_text(s); print(p, 'tests: signup phone step, friendsSearch names the Invite pill')
