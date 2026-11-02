#!/usr/bin/env python3
"""Tests for contacts-v2-2026-10-31 (Tate's 1a / 1b / list A): the older checks that pinned the old copy and layout.
  check-app-contacts-2026-10-30: the results are a full page now ("Contacts", "On TermChamp" + a count chip,
    "Invite to TermChamp" A to Z, every contact listed, no "See all"); the sign-up step's new copy and "Not now".
  check-app (onboard): the sign-up step's new title and "Not now"; dprStressQuarter (reloads mid-test) marks the new pop-up done.
  check-push-popup-2026-10-30: these tests are about notifications, so the new "Add your number" pop-up is done
    (as they already do for "Connect contacts").
Run from the site root: python3 edit-tests-contacts-v2-2026-10-31.py [app-dev/tests]"""
import sys, pathlib
d = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else 'app-dev/tests')
def edit(name, pairs):
    p = d / name; s = p.read_text()
    for a, b in pairs:
        n = s.count(a); assert n == 1, (name, a[:80], n); s = s.replace(a, b)
    p.write_text(s); print(p, len(pairs), 'edits')

edit('check-app-contacts-2026-10-30.mjs', [
    ("""  ok(/Your contacts/.test(t) && /On TermChamp · 4/.test(t) && /Invite · 6/.test(t), 'results: On TermChamp · 4 and Invite · 6 (matched people left out of Invite)', t);""",
     """  ok(/^Contacts/.test(t) && /On TermChamp\\s*4/.test(t) && /Invite to TermChamp/.test(t) && await page.locator('#sheet [data-a="ctInvite"]').count() === 6, 'results (2026-10-31, list A): On TermChamp 4 and 6 to invite (matched people left out of Invite)', t);"""),
    ("""  ok(await page.locator('#sheet [data-a="ctInvite"]').count() === 5 && /See all 6/.test(t), 'results: 5 to invite, then See all 6', t);""",
     """  ok(await page.locator('#sheet [data-a="ctInvite"]').count() === 6 && !/See all/.test(t), 'results (2026-10-31): every contact to invite, A to Z (no See all)', t);"""),
    ("""  await page.locator('#sheet .sheet').screenshot({ path: SHOTS + '/results-sheet-light.png' });""",
     """  await page.locator('#sheet .fullpg').screenshot({ path: SHOTS + '/results-sheet-light.png' });"""),
    ("""  await click(page, '#sheet [data-a="ctAll"]');
  ok(await page.locator('#sheet [data-a="ctInvite"]').count() === 6 && !/See all/.test(await sheetText(page)), 'See all shows all 6');""",
     """  ok(await page.locator('#sheet [data-a="ctInvite"]').count() === 6 && !/See all/.test(await sheetText(page)), 'all 6 listed without a See all');"""),
    ("""  ok(/On TermChamp · 1/.test(t) && /Invite · 1/.test(t) && /Quinn Ashby/.test(t) && !/No Number/.test(t), 'native: Jordan matched by email; Quinn to invite; an email-only contact can’t get a text', t);""",
     """  ok(/On TermChamp\\s*1/.test(t) && await page.locator('#sheet [data-a="ctInvite"]').count() === 1 && /Quinn Ashby/.test(t) && !/No Number/.test(t), 'native: Jordan matched by email; Quinn to invite; an email-only contact can’t get a text', t);"""),
    ("""  ok(/Contact matching isn’t available yet\\./.test(t) && /Invite · 9/.test(t) && !/On TermChamp/.test(t) && !/Couldn’t/.test(t), 'RPC missing (404 PGRST202): "isn’t available yet", and the Invite list still works', t);""",
     """  ok(/Contact matching isn’t available yet\\./.test(t) && await page.locator('#sheet [data-a="ctInvite"]').count() === 9 && /Invite to TermChamp/.test(t) && !/On TermChamp/.test(t) && !/Couldn’t/.test(t), 'RPC missing (404 PGRST202): "isn’t available yet", and the Invite list still works', t);"""),
    ("""  ok(/Help friends find you/.test(t) && /Friends who have your number saved will see you on TermChamp\\./.test(t) && /Only used to find friends\\. Never shown on your profile\\./.test(t) && /Continue/.test(t) && /Skip/.test(t), 'sign-up: "Help friends find you" right after year and major', t.slice(0, 400));""",
     """  ok(/What’s your number\\?/.test(t) && /Friends who have you saved will find you on TermChamp\\. It’s never shown on your profile\\./.test(t) && /Continue/.test(t) && /Not now/.test(t) && !/Skip/.test(t), 'sign-up (2026-10-31, 1a): "What’s your number?" right after year and major, Continue + Not now', t.slice(0, 400));"""),
    ("""  ok(inp && inp.type === 'tel' && inp.im === 'tel' && inp.ac === 'tel' && inp.cc === '+1', 'phone field: +1, type/inputmode/autocomplete tel', inp);""",
     """  ok(inp && inp.type === 'tel' && inp.im === 'tel' && inp.ac === 'tel' && /\\+1$/.test(inp.cc), 'phone field: +1, type/inputmode/autocomplete tel', inp);"""),
    ("""  await page.locator('#sheet .sheet').screenshot({ path: SHOTS + '/results-sheet-dark.png' });""",
     """  await page.locator('#sheet .fullpg').screenshot({ path: SHOTS + '/results-sheet-dark.png' });"""),
    ("""  ok(/Help friends find you/.test(await page.locator('#scroll').innerText()) && (await page.evaluate(() => document.documentElement.scrollWidth)) <= 375, 'dark 375px: the phone step (onboarding stays light, as all of it does)');""",
     """  ok(/What’s your number\\?/.test(await page.locator('#scroll').innerText()) && (await page.evaluate(() => document.documentElement.scrollWidth)) <= 375, 'dark 375px: the phone step (onboarding stays light, as all of it does)');"""),
])
edit('check-app.mjs', [
    ("""  ok(/Help friends find you/.test(t) && await page.locator('#ob-phone[type="tel"]').count() === 1 && await page.locator('[data-a="ctPhoneSkip"]').count() === 1, 'onboard: then the optional phone step, with Skip', t.slice(0, 200));""",
     """  ok(/What’s your number\\?/.test(t) && await page.locator('#ob-phone[type="tel"]').count() === 1 && /Not now/.test(await page.locator('[data-a="ctPhoneSkip"]').innerText()), 'onboard: then the optional phone step, with Not now (2026-10-31)', t.slice(0, 200));"""),
    # dprStressQuarter reloads mid-test: its "contacts done" init now also marks "Add your number" done
    ("""localStorage.setItem('tc_ct:' + s0.user.id, JSON.stringify({ on: true })); } catch (e) {} });""",
     """localStorage.setItem('tc_ct:' + s0.user.id, JSON.stringify({ on: true, phOk: 1 })); } catch (e) {} });"""),
])
edit('check-push-popup-2026-10-30.mjs', [
    ("""localStorage.setItem('tc_ct:' + s0.user.id, JSON.stringify({ on: true })); } catch (e) {}""",
     """localStorage.setItem('tc_ct:' + s0.user.id, JSON.stringify({ on: true, phOk: 1 })); } catch (e) {}   /* (2026-10-31) and "Add your number" is done */"""),
    ("""localStorage.setItem('tc_ct:'+s.user.id,JSON.stringify({on:true}));}catch(e){}" });""",
     """localStorage.setItem('tc_ct:'+s.user.id,JSON.stringify({on:true,phOk:1}));}catch(e){}" });"""),
])
