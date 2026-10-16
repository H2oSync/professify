#!/usr/bin/env python3
"""Re-aims the older desktop tests and the harness at website-sync-2026-10-15.py. Every edit has its reason in a comment.
 * app-harness.mjs  COL_GRANTS.profiles: pinned_friends is INSERT/UPDATE only on the live database (catalog2.json), so a
   SELECT naming it is refused (42501); concentration IS granted. The stand-in used to say the opposite.
 * app-fixtures.mjs RPC: the four server additions of sql/professify-sync-2026-10-15.sql (my_pinned_friends, set_pinned_friends,
   my_favorite_teachers, set_favorite_teacher) answer "not installed" (PGRST202) by default, which is what production answers
   today, so every older suite keeps testing the page it always tested; check-desktop-sync.mjs installs them per test.
 * check-desktop-regday.mjs / mutate-desktop-regday.mjs: the registration banner is gone from the top of every page and is a
   card on Home's right rail (#hmRegCard), so the checks that read #campusBanner read the card.
Usage: python3 edit-tests-websync-2026-10-15.py <repo>"""
import sys, pathlib
root = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else '.')
T = root / 'app-dev' / 'tests'

def patch(name, edits, marker='websync (2026-10-15)'):
    f = T / name
    s = f.read_text()
    if marker in s:
        print('already patched', name); return
    for old, new in edits:
        assert s.count(old) == 1, (name, s.count(old), old[:90])
        s = s.replace(old, new)
    f.write_text(s)
    print('patched', f)

patch('app-harness.mjs', [(
 "  profiles: ['id', 'display_name', 'username', 'avatar_url', 'major', 'class_standing', 'pinned_friends', 'instagram_handle', 'school'],",
 "  /* websync (2026-10-15): as the live catalog has it: concentration is selectable, pinned_friends is NOT (INSERT/UPDATE only; pins are read through my_pinned_friends()) */\n"
 "  profiles: ['id', 'display_name', 'username', 'avatar_url', 'major', 'class_standing', 'concentration', 'instagram_handle', 'school'],")])

patch('app-fixtures.mjs', [(
 "  unblock_user: null, username_taken: false,\n};",
 "  unblock_user: null, username_taken: false,\n"
 "  /* websync (2026-10-15): not installed yet, as on production today; check-desktop-sync.mjs installs them */\n"
 "  my_pinned_friends: { __error: { code: 'PGRST202', message: 'Could not find the function public.my_pinned_friends without parameters in the schema cache' } },\n"
 "  set_pinned_friends: { __error: { code: 'PGRST202', message: 'Could not find the function public.set_pinned_friends(p_ids) in the schema cache' } },\n"
 "  my_favorite_teachers: { __error: { code: 'PGRST202', message: 'Could not find the function public.my_favorite_teachers without parameters in the schema cache' } },\n"
 "  set_favorite_teacher: { __error: { code: 'PGRST202', message: 'Could not find the function public.set_favorite_teacher(p_key, p_on) in the schema cache' } },\n};")])


patch('check-desktop-regday.mjs', [
 ("""    ok(await page.evaluate(() => /Change your registration day/.test(document.getElementById('campusBanner').innerText)), 'banner: with a day set it says “Change your registration day”');""",
  """    /* websync (2026-10-15): the banner is a card on Home's rail now (#hmRegCard, under the greeting); the top strip is empty of it */
    ok(await page.evaluate(() => /Change your registration day/.test(document.getElementById('hmRegCard').innerText) && !/registration/i.test(document.getElementById('campusBanner').innerText)), 'banner card: with a day set it says “Change your registration day”, and nothing about it is left at the top');"""),
 ("""    ok(await page.evaluate(() => !/registration day/i.test(document.getElementById('campusBanner').innerText)), 'after Round 1: the banner has no link either');""",
  """    ok(await page.evaluate(() => !document.getElementById('hmRegCard') && !/registration day/i.test(document.getElementById('campusBanner').innerText)), 'after Round 1: the banner card is gone too');   /* websync (2026-10-15) */"""),
 ("""    ok(await page.evaluate(() => !/registration day/i.test(document.getElementById('campusBanner').innerText)), 'signed out: the banner has no link');""",
  """    ok(await page.evaluate(() => !document.getElementById('hmRegCard') && !/registration day/i.test(document.getElementById('campusBanner').innerText)), 'signed out: no banner card');   /* websync (2026-10-15) */"""),
 ("""  ok(await page.evaluate(() => document.getElementById('campusBanner').innerText.includes('Change your registration day')), 'banner: now says “Change your registration day”');""",
  """  ok(await page.evaluate(() => document.getElementById('hmRegCard').innerText.includes('Change your registration day')), 'banner card: now says “Change your registration day”');   /* websync (2026-10-15) */"""),
 ("""  await page.click('#campusBanner button:has-text("Set your registration day")'); await tick(page, 400);
  ok(await page.evaluate(() => document.getElementById('rgBack').classList.contains('open') && document.getElementById('rgTitle').textContent === 'When do you register?'), 'banner: “Set your registration day” opens the sheet');""",
  """  await page.click('#hmRegCard button:has-text("Set your registration day")'); await tick(page, 400);   /* websync (2026-10-15): the card on Home's rail */
  ok(await page.evaluate(() => document.getElementById('rgBack').classList.contains('open') && document.getElementById('rgTitle').textContent === 'When do you register?'), 'banner card: “Set your registration day” opens the sheet');"""),
 ("""  await o.page.click('#campusBanner button:has-text("Set your registration day")'); await tick(o.page, 400);
  await o.page.click('.rg-d[data-day="2026-10-22"]'); await o.page.click('[data-rg-act="save"]'); await tick(o.page, 1000);
  ok(await focusOn('#campusBanner button'), 'focus: opened from the banner, it goes back to the banner’s button');""",
  """  await o.page.click('#hmRegCard button:has-text("Set your registration day")'); await tick(o.page, 400);   /* websync (2026-10-15): the card, not the top strip */
  await o.page.click('.rg-d[data-day="2026-10-22"]'); await o.page.click('[data-rg-act="save"]'); await tick(o.page, 1000);
  ok(await focusOn('#hmRegCard button[onclick^="regDayOpen"]'), 'focus: opened from the banner card, it goes back to the card’s button');"""),
 ("""  const b = await p.page.evaluate(() => document.getElementById('campusBanner').innerText);
  ok(/opens in 5 days/.test(b), 'banner: the day count is Pacific’s (5), even in a browser that is already on the 15th', b);""",
  """  const b = await p.page.evaluate(() => document.getElementById('hmRegCard').innerText);   /* websync (2026-10-15) */
  ok(/opens in 5 days/.test(b), 'banner card: the day count is Pacific’s (5), even in a browser that is already on the 15th', b);"""),
 ("""    const before = o.log.rpcs.length;
    await o.page.clock.runFor(125000); await o.page.waitForTimeout(300);
    await o.page.click('.rg-slot[data-rg="rail"] [data-rg-act="open"]'); await tick(o.page, 800);
    ok(o.log.rpcs.length > before, 'friends refresh: opening the sheet asks the RPC again once the list is stale', { before, after: o.log.rpcs.length });""",
  """    /* websync (2026-10-15): the sign-in now also asks my_pinned_friends / my_favorite_teachers, which can land after this snapshot, so
       counting every RPC let the promise pass without the sheet asking. Count the one the promise is about. */
    const nReg = () => o.log.rpcs.filter(r => r.fn === 'friend_registration_days').length, before = nReg();
    await o.page.clock.runFor(125000); await o.page.waitForTimeout(300);
    await o.page.click('.rg-slot[data-rg="rail"] [data-rg-act="open"]'); await tick(o.page, 800);
    ok(nReg() > before, 'friends refresh: opening the sheet asks the RPC again once the list is stale', { before, after: nReg() });"""),
])

patch('mutate-desktop-regday.mjs', [
 ("""  ["regday: the banner has no link", "?'<button class=\\"btn\\" style=\\"flex:none\\" onclick=\\"regDayOpen(&quot;banner&quot;)\\">'+regDayLabel()+'</button>':''", "?'':''", 'banner'],""",
  """  /* websync (2026-10-15): the banner is the #hmRegCard on Home's rail now, so the mutants break its code */
  ["regday: the banner card has no link", "(lab?'<button type=\\"button\\" class=\\"btn\\" onclick=\\"regDayOpen(&quot;banner&quot;)\\">'+lab+'</button>':'')", "('')", 'banner'],"""),
 ("""  ["regday: the banner counts days on the browser's clock", "(typeof regPacificGap==='function'&&c.REGISTRATION_OPENS)?regPacificGap(c.REGISTRATION_OPENS):daysUntil(c.REGISTRATION_OPENS)", "daysUntil(c.REGISTRATION_OPENS)", 'a11y'],""",
  """  ["regday: the banner card counts days on the browser's clock", "var regIn=(typeof regPacificGap==='function')?regPacificGap(c.REGISTRATION_OPENS):daysUntil(c.REGISTRATION_OPENS);", "var regIn=daysUntil(c.REGISTRATION_OPENS);", 'a11y'],"""),
])

patch('check-desktop-look.mjs', [
 ("""    loadProfile();
    return { opts: ['Industrial Technology & Packaging', 'Physics (BA)', NEW].every""",
  """    /* websync (2026-10-15): the page now reads the account's major on sign-in and keeps it on this device, which overwrote the
       old-name profile this test seeded; the promise tested is loadProfile()'s rename, so the old-name profile is put back first */
    try { localStorage.setItem('professify-profile', JSON.stringify({ school: 'calpoly', major: OLD, conc: null })); } catch (e) {}
    loadProfile();
    return { opts: ['Industrial Technology & Packaging', 'Physics (BA)', NEW].every"""),
])

patch('check-desktop-builder.mjs', [
 ("""  const t = JSON.parse(JSON.stringify(FX.TABLES));
  t.course_seats = t.course_seats.concat(SPRING);
  t.degree_audit =""",
  """  const t = JSON.parse(JSON.stringify(FX.TABLES));
  /* websync (2026-10-15): the account's major and class standing are read now. These tests were written for a page with no major
     chosen and the default year (the website never read them), where the Builder ranks from the degree report alone; with the
     fixture's Business Administration / Junior the roadmap's year gate and urgency points reorder the picks. An account with neither
     is the page they were written against. */
  Object.assign(t.profiles.find(p => p.id === ME), { major: null, class_standing: null });
  t.course_seats = t.course_seats.concat(SPRING);
  t.degree_audit ="""),
])

patch('app-harness.mjs', [(
 """          if (m === 'POST') {
            const arr = (Array.isArray(body) ? body : [body]).map(r => Object.assign({ id: r.id || (table === 'conversations' ? 'c-new-' + (nextId++) : nextId++), created_at: new Date().toISOString() }, r));
            T[table] = (T[table] || []).concat(arr); rows = arr;
          }""",
 """          if (m === 'POST') {
            let arr = (Array.isArray(body) ? body : [body]).map(r => Object.assign({ id: r.id || (table === 'conversations' ? 'c-new-' + (nextId++) : nextId++), created_at: new Date().toISOString() }, r));
            /* websync (2026-10-15): an upsert (?on_conflict=a,b) updates the row that has the same a,b — or, with ignore-duplicates, leaves it —
               instead of adding a second one, as PostgREST does; push_prefs and saved_items are written twice in a row by the new tests */
            const oc = url.searchParams.get('on_conflict');
            if (oc) {
              const cols = oc.split(','), same = (a, b) => cols.every(c => String(a[c]) === String(b[c]));
              const fresh = [];
              for (const r of arr) {
                const ex = (T[table] || []).find(x => same(x, r));
                if (ex) { if (!/ignore-duplicates/.test(prefer)) Object.assign(ex, r, { id: ex.id, created_at: ex.created_at }); } else fresh.push(r);
              }
              T[table] = (T[table] || []).concat(fresh); rows = arr;
            } else { T[table] = (T[table] || []).concat(arr); rows = arr; }
          }""")], marker='an upsert (?on_conflict=a,b)')

# ONE registration card on Home (2026-10-15, second pass): while #hmRegCard shows, the rail's own day card is not drawn. These tests are about
# that older card, so they start with the compact card dismissed (its own key), and the ones about the compact card bring it back first.
patch('check-desktop-regday.mjs', [
 ("""const desk = (o = {}) => openApp(Object.assign({ path: '/', width: 1440, height: 900, wait: 4000, terms: 'live', time: NOW }, o));""",
  """/* one-card (2026-10-15): the compact "Round 1 registration opens" card hides the rail's own day card while it shows; most of these tests are about
   that day card, so the page starts with the compact card dismissed, and UNDISMISS brings it back for the tests about the compact card */
const DISMISS = () => { try { localStorage.setItem('professify_dismiss_reg_2026-10-19', '1'); } catch (e) {} };
const desk = (o = {}) => openApp(Object.assign({ path: '/', width: 1440, height: 900, wait: 4000, terms: 'live', time: NOW, init: DISMISS }, o));
const UNDISMISS = async page => { await page.evaluate(() => { localStorage.removeItem('professify_dismiss_reg_2026-10-19'); regDayRepaint(); }); await page.clock.runFor(300); await page.waitForTimeout(250); };"""),
 ("""    ok(await page.evaluate(() => /Change your registration day/.test(document.getElementById('hmRegCard').innerText)""",
  """    await UNDISMISS(page);
    ok(await page.evaluate(() => /Change your registration day/.test(document.getElementById('hmRegCard').innerText)"""),
 ("""  ok(await page.evaluate(() => document.getElementById('hmRegCard').innerText.includes('Change your registration day')""",
  """  await UNDISMISS(page);
  ok(await page.evaluate(() => document.getElementById('hmRegCard').innerText.includes('Change your registration day')"""),
 ("""  await page.click('#hmRegCard button:has-text("Set your registration day")'); await tick(page, 400);""",
  """  await UNDISMISS(page);
  await page.click('#hmRegCard button:has-text("Set your registration day")'); await tick(page, 400);"""),
 ("""  await o.page.click('#hmRegCard button:has-text("Set your registration day")'); await tick(o.page, 400);""",
  """  await UNDISMISS(o.page);
  await o.page.click('#hmRegCard button:has-text("Set your registration day")'); await tick(o.page, 400);"""),
 ("""  const b = await p.page.evaluate(() => document.getElementById('hmRegCard').innerText);""",
  """  await UNDISMISS(p.page);
  const b = await p.page.evaluate(() => document.getElementById('hmRegCard').innerText);"""),
], marker='one-card (2026-10-15)')
