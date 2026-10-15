#!/usr/bin/env python3
"""(2026-10-15) Keeps check-app.mjs true after security-app-2026-10-15.py:
  - the invite test asserted the OLD behaviour (a request sent / an incoming request accepted with no tap). It now asserts the new one:
    the link asks, Add writes (one POST), Add on an incoming request accepts (one PATCH). Full coverage is in check-app-security-2026-10-15.mjs.
  - delete used to keep the phone-only concentration for a recovery; the wipe now removes every tc-/tc_/professify/termchamp key (a shared
    browser keeps nothing of the person who left), so the test expects it gone.
  - two tests gave a friend an avatar on photos.example.invalid / photos.test; safeImg() now accepts only our avatars bucket, so they use it.
Usage: python3 edit-tests-app-security-2026-10-15.py <repo>"""
import sys, pathlib
root = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else '.')
p = root / 'app-dev/tests/check-app.mjs'; s = p.read_text()
if 'security-app (2026-10-15)' in s: sys.exit('already edited')
def rep(a, b, n=1):
    global s
    assert s.count(a) == n, (s.count(a), a[:90]); s = s.replace(a, b)

a = s.index("  /* signed in: a request to whoever invited you */")
b = s.index("  /* already friends, or your own link: nothing */")
s = s[:a] + """  /* signed in: asked first (security-app (2026-10-15)); the request is written when Add is tapped */
  o = await openApp({ path: '/app/?add=' + SUG.id, rpc: Object.assign({}, FX.RPC, { get_inviter: [{ display_name: SUG.display_name }] }) });
  await o.page.waitForFunction(() => TC.ready, null, { timeout: 8000 }); await tick(o.page, 600);
  let fr = o.log.writes.filter(w => w.table === 'friend_requests');
  ok(fr.length === 0 && /Add Pat Suggestia\\?/.test(await o.page.locator('#sheet').innerText()), 'invite: signed in, the link ASKS “Add Pat Suggestia?” and writes nothing', fr);
  await o.page.evaluate(() => A.inviteAdd()); await tick(o.page, 800);
  fr = o.log.writes.filter(w => w.table === 'friend_requests' && w.m === 'POST');
  ok(fr.length === 1 && fr[0].body.to_user === SUG.id && fr[0].body.from_user === FX.ME.id && fr[0].body.status === 'pending' && /Friend request sent to Pat/.test(await o.page.locator('#toast').innerText()), 'invite: Add sends a friend request to whoever invited you', fr);
  ok(await o.page.evaluate(() => localStorage.getItem('tc_pending_add')) === null, 'invite: …once');
  await o.close();
  /* they already asked you: still a question; Add accepts, not a second request */
  o = await openApp({ path: '/app/?add=' + STR.id });
  await o.page.waitForFunction(() => TC.ready, null, { timeout: 8000 }); await tick(o.page, 800);
  ok(!o.log.writes.some(w => w.table === 'friend_requests'), 'invite: if they’d already asked you, the link alone accepts nothing');
  await o.page.evaluate(() => A.inviteAdd()); await tick(o.page, 800);
  fr = o.log.writes.filter(w => w.table === 'friend_requests');
  ok(fr.length === 1 && fr[0].m === 'PATCH' && fr[0].body.status === 'accepted', 'invite: …Add accepts it instead of sending a second request', fr);
  await o.close();
""" + s[b:]

rep("ok(left[0] === null && left[1] !== null, 'delete: recent searches are cleared; the concentration (phone-only) stays for a recovery', left);",
    "ok(left[0] === null && left[1] === null, 'delete: recent searches and the concentration are cleared too — a shared browser keeps nothing of the person who left (security-app (2026-10-15))', left);")

AV = "https://rqkndeqbcahozidniesn.supabase.co/storage/v1/object/public/avatars/"
rep("avatar_url: 'https://photos.example.invalid/rowan.png'", "avatar_url: '" + AV + "rowan/avatar.jpg'")
rep("PEOPLE[fr[2]].avatar = 'https://photos.test/a.png';", "PEOPLE[fr[2]].avatar = '" + AV + "a.png';")
rep("await page.route('https://photos.test/**', r =>", "await page.route('" + AV + "**', r =>")
p.write_text(s); print('edited', p)
