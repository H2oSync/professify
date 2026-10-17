#!/usr/bin/env python3
"""(2026-10-16) Keeps the older desktop checks true after reg-timeline-2026-10-16.py (website; marker 'reg-timeline (2026-10-16)'):
  Home's registration card is the Spring 2027 timeline (not the "Round 1 registration opens" card), the rail's own day card is gone,
  and the friends' days moved from the Schedule page's registration card to a strip on the Friends tab (#frRegStrip).
  check-desktop-regday.mjs         Home's rail: timeline pencil / "+ Add" instead of the rail slot; the friends tests read the strip;
                                   after Round 1 your own days are still read (for the timeline), friends' Round 1 days are not.
  check-desktop-sync.mjs           the two "regcard" tests are about the timeline card now.
  (check-desktop-home / -look / -friend-regday need no edit.)
Usage: python3 edit-tests-reg-timeline-2026-10-16.py <repo>"""
import sys, pathlib
root = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else '.')
MARK = 'reg-timeline (2026-10-16)'


def load(name):
    p = root / 'app-dev/tests' / name
    s = p.read_text()
    if MARK in s:
        sys.exit('already edited ' + name)
    return p, s


def one(s, a, b):
    assert s.count(a) == 1, (s.count(a), a[:120])
    return s.replace(a, b)


def span(s, start, end, new):
    assert s.count(start) == 1, (s.count(start), start[:100])
    i = s.index(start)
    j = s.index(end, i + len(start))
    return s[:i] + new + s[j:]


# =============================================================================================================== regday
p, s = load('check-desktop-regday.mjs')
s = one(s, "const UNDISMISS = async page => {", "const R1BTN = '#hmRegCard [data-tl-key=\"pen1\"], #hmRegCard [data-tl-key=\"add1\"]';   /* reg-timeline (2026-10-16): Home's one card is the timeline; Round 1's pencil / + Add opens the same sheet */\nconst UNDISMISS = async page => {")
s = one(s, "const UNDISMISS = async page => { await page.evaluate(() => { localStorage.removeItem('professify_dismiss_reg_2026-10-19'); regDayRepaint(); }); await page.clock.runFor(300); await page.waitForTimeout(250); };",
        "const UNDISMISS = async page => {};   /* reg-timeline (2026-10-16): the timeline card is not hidden by the old key */")
# every "open the sheet from Home's rail" click
n = s.count("'.rg-slot[data-rg=\"rail\"] [data-rg-act=\"open\"]'")
assert n >= 10, n
s = s.replace("'.rg-slot[data-rg=\"rail\"] [data-rg-act=\"open\"]'", "R1BTN")
s = s.replace("(await slots(o.page)).rail", "(await slots(o.page)).plans")
# cards
s = one(s, "ok(s.rail && s.rail.has && s.rail.state === 'none' && s.rail.head === 'Set your registration day', 'none: Home’s rail says it too (Round 1 is 5 days away)', s.rail);",
        "ok(await page.evaluate(() => { const c = document.getElementById('hmRegCard'); return !!c && /Spring 2027/.test(c.innerText) && !!c.querySelector('[data-tl-key=\"add1\"]') && /Opens Oct 19/.test(c.innerText); }), 'none: Home’s card is the Spring 2027 timeline, with “+ Add” on Your Round 1 (Round 1 opens Oct 19)');")
s = one(s, "ok(s.rail.head === 'Register Wed, Oct 21, 11a' && s.rail.sub === 'in 7 days', 'set: …and on Home’s rail', s.rail);",
        "ok(await page.evaluate(() => { const r = document.querySelector('#hmRegCard [data-tl-row=\"r1\"]'); return !!r && /Wed, Oct 21 · 11:00 AM/.test(r.innerText) && /in 7 days/.test(r.innerText); }), 'set: …and Home’s timeline says Wed, Oct 21 · 11:00 AM, in 7 days');")
s = one(s, """    /* websync (2026-10-15): the banner is a card on Home's rail now (#hmRegCard, under the greeting); the top strip is empty of it */
    await UNDISMISS(page);
    ok(await page.evaluate(() => /Change your registration day/.test(document.getElementById('hmRegCard').innerText) && !/registration/i.test(document.getElementById('campusBanner').innerText)), 'banner card: with a day set it says “Change your registration day”, and nothing about it is left at the top');
""", """    /* reg-timeline (2026-10-16): the old green “Your day…” line and the grey “Change your registration day” button are gone; the top strip has nothing */
    ok(await page.evaluate(() => !/Change your registration day|Your day:/.test(document.getElementById('hmRegCard').innerText) && !document.querySelector('#hmRegCard .hm-reg-day') && !/registration/i.test(document.getElementById('campusBanner').innerText)), 'timeline: no “Your day…” line, no “Change your registration day” button, nothing at the top');
""")
s = one(s, "&& s.rail.has, 'running: Round 1 is open, ends Nov 3 — card and rail still there', s);",
        "&& await page.evaluate(() => !!document.getElementById('hmRegCard')), 'running: Round 1 is open, ends Nov 3 — Plans card and Home’s timeline still there', s);")
s = one(s, "ok(s.plans.has && !s.rail.has, '18 days out: Plans has the card, Home’s rail does not', s);",
        "ok(s.plans.has && await a.page.evaluate(() => !document.getElementById('hmRegCard')), '18 days out: Plans has the card, Home’s timeline does not', s);")
s = one(s, "ok(s2.plans.has && s2.rail.has, '14 days out: Home’s rail has it too', s2);",
        "ok(s2.plans.has && await b.page.evaluate(() => !!document.getElementById('hmRegCard')), '14 days out: Home’s timeline has it too', s2);")
s = one(s, "ok(!s.plans.has && !s.rail.has, 'after Round 1 (Nov 4): no card anywhere', s);",
        "ok(!s.plans.has && await page.evaluate(() => { const c = document.getElementById('hmRegCard'); return !!c && /Your Round 1/.test(c.innerText) && !c.querySelector('[data-tl-key=\"pen1\"]'); }), 'after Round 1 (Nov 4): the Schedule card is gone; Home’s timeline stays, Round 1 done with no pencil', s);")
s = one(s, "    ok(await page.evaluate(() => !document.getElementById('hmRegCard') && !/registration day/i.test(document.getElementById('campusBanner').innerText)), 'after Round 1: the banner card is gone too');   /* websync (2026-10-15) */\n", "")
s = one(s, "ok(!log.reads.some(r => /registration/.test(r)), 'after Round 1: registration_days and the RPC are never asked', log.reads.filter(r => /registration/.test(r)));",
        "ok(!log.reads.some(r => r === 'rpc:friend_registration_days') && log.reads.some(r => /^registration_days\\?/.test(r)), 'after Round 1: friends’ Round 1 days (the RPC) are never asked; your own rows are still read for the timeline', log.reads.filter(r => /registration/.test(r)));")
s = one(s, "ok(!s.plans.has && !s.rail.has, 'signed out: no card', s);", "ok(!s.plans.has, 'signed out: no card', s);")
s = one(s, "ok(!s.plans.has && !s.rail.has && !log.reads.some(r => /registration/.test(r)), 'a site choosing in another term (Fall 2026) shows no card and asks nothing', s);",
        "ok(!s.plans.has && !log.reads.some(r => /registration/.test(r)), 'a site choosing in another term (Fall 2026) shows no card and asks nothing', s);")
s = one(s, "&& s.rail.head === 'Register Thu, Oct 22, 2:30p', 'save: the cards say Thu, Oct 22, 2:30p', s);",
        "&& await page.evaluate(() => /Thu, Oct 22 · 2:30 PM/.test(document.getElementById('hmRegCard').innerText)), 'save: the cards say Thu, Oct 22, 2:30p', s);")
s = one(s, """  await UNDISMISS(page);
  ok(await page.evaluate(() => document.getElementById('hmRegCard').innerText.includes('Change your registration day')), 'banner card: now says “Change your registration day”');   /* websync (2026-10-15) */
""", "")
s = one(s, """  await UNDISMISS(page);
  await page.click('#hmRegCard button:has-text("Set your registration day")'); await tick(page, 400);   /* websync (2026-10-15): the card on Home's rail */""",
        """  await page.click('#hmRegCard [data-tl-key="add1"]'); await tick(page, 400);   /* reg-timeline: Round 1's “+ Add” on Home's card */""")
s = one(s, """  await UNDISMISS(o.page);
  await o.page.click('#hmRegCard button:has-text("Set your registration day")'); await tick(o.page, 400);   /* websync (2026-10-15): the card, not the top strip */
""", """  await o.page.click('#hmRegCard [data-tl-key="add1"]'); await tick(o.page, 400);
""")
s = one(s, "ok(await focusOn('#hmRegCard button[onclick^=\"regDayOpen\"]'), 'focus: opened from the banner card, it goes back to the card’s button');",
        "ok(await focusOn('#hmRegCard [data-tl-key=\"pen1\"]'), 'focus: opened from the timeline’s “+ Add”, it goes back to the row’s pencil');")
s = one(s, """  const p = await desk({ tables: withDay(null), tz: 'Pacific/Auckland' }); await tick(p.page, 1500);
  await UNDISMISS(p.page);
  const b = await p.page.evaluate(() => document.getElementById('hmRegCard').innerText);   /* websync (2026-10-15) */
  ok(/opens in 5 days/.test(b), 'banner card: the day count is Pacific’s (5), even in a browser that is already on the 15th', b);""",
        """  const p = await desk({ tables: withDay({ day: '2026-10-21' }), tz: 'Pacific/Auckland' }); await tick(p.page, 1500);
  const b = await p.page.evaluate(() => document.getElementById('hmRegCard').innerText);
  ok(/in 7 days/.test(b), 'timeline: the day count is Pacific’s (7), even in a browser that is already on the 15th', b);""")

# the friends' days are the Friends tab's strip now
s = one(s, "const frRowsOf = page => page.evaluate(() => [...document.querySelectorAll('.rg-slot[data-rg=\"plans\"] .rg-f')].map(b => b.querySelector('.rg-fn').textContent));",
        """/* reg-timeline (2026-10-16): friends' days are the strip above Messages on the Friends tab (#frRegStrip), not a list in the Schedule card */
const stripOf = page => page.evaluate(() => {
  const e = document.getElementById('frRegStrip'), n = t => (t || '').replace(/\\s+/g, ' ').trim();
  return { rows: [...(e ? e.querySelectorAll('.rs-row') : [])].map(r => ({ label: n([...r.querySelector('.rs-d').children].map(c => c.textContent).join(' ')), names: n(r.querySelector('.rs-n').textContent), rel: n(r.querySelector('.rs-rel').textContent), me: r.classList.contains('rs-me') })),
    miss: n((e && e.querySelector('.rs-ft span') || {}).textContent), text: n(e ? e.innerText : ''), round: n((e && e.querySelector('.rs-rnd') || {}).textContent) };
});
const frRowsOf = async page => (await stripOf(page)).rows.map(r => r.names);""")
s = one(s, """  const s = await slots(page);
  ok(s.plans.miss === '3 friends haven’t set theirs', 'blocked: …and is not counted among those who haven’t set theirs', s.plans.miss);""",
        """  const s = await stripOf(page);
  ok(s.miss === '3 friends haven’t set theirs', 'blocked: …and is not counted among those who haven’t set theirs', s.miss);""")
new_friends = r"""test('friends', async () => {
  const rows = [
    { user_id: F[0], day: '2026-10-21', at_time: '08:00:00' },       /* Avery: Wed 8a */
    { user_id: F[1], day: '2026-10-19', at_time: null },             /* Rowan: Mon, no time */
    { user_id: F[2], day: '2026-10-21', at_time: '14:30:00' },       /* Sky: Wed 2:30p */
    { user_id: '33333333-3333-4333-8333-333333333399', day: '2026-10-19', at_time: '07:00:00' },   /* not a friend: never shown */
    { user_id: F[2], day: '2026-10-30', at_time: '09:00:00' },       /* a duplicate id: the first stands */
  ];
  /* mine: Wed Oct 21 11a. Friends: Quinn and Harper have not set theirs */
  { const { page, close, log } = await desk({ tables: withDay({ day: '2026-10-21', at_time: '11:00:00' }), rpc: rpcWith(rows) }); await tick(page, 1500);
    const calls = log.rpcs.filter(r => r.fn === 'friend_registration_days');
    ok(calls.length >= 1 && calls.every(c => c.body && c.body.p_term === '2274'), 'friends: the RPC is asked for term 2274', calls);
    const s = await stripOf(page);
    const want = ['Mon Oct 19|Rowan Testa|2 days before you', 'Wed Oct 21 8a|Avery Quill|same day as you', 'Wed Oct 21 11a|You|your day', 'Wed Oct 21 2:30p|Sky Placeholder|same day as you'];
    ok(JSON.stringify(s.rows.map(r => r.label + '|' + r.names + '|' + r.rel)) === JSON.stringify(want), 'friends: soonest first (by day, then time), friends only, yours in its place, each with how far from yours', s.rows);
    ok(s.rows.filter(r => r.me).length === 1 && s.rows[2].me, 'friends: your own row is the highlighted one', s.rows);
    ok(s.miss === '2 friends haven’t set theirs' && s.round === 'Round 1 · Oct 19–Nov 3', 'friends: “2 friends haven’t set theirs”, Round 1 · Oct 19–Nov 3', s);
    await page.evaluate(() => show('friends')); await tick(page, 500);
    await page.click('#frRegStrip .rs-fb[data-id="' + F[1] + '"]'); await tick(page, 600);
    ok(await page.evaluate(() => document.getElementById('frpBack').classList.contains('open') && /Rowan/.test(document.getElementById('frpBack').innerText)), 'friends: tapping a face opens their page');
    ok(log.errors.length === 0, 'friends: no page errors', log.errors);
    await close(); }
  /* nothing set by me: no “before you”, and the strip still lists them */
  { const { page, close } = await desk({ tables: withDay(null), rpc: rpcWith(rows) }); await tick(page, 1500);
    const s = await stripOf(page);
    ok(s.rows.length === 3 && s.rows.every(r => r.rel === '' && !r.me) && /^Mon Oct 19/.test(s.rows[0].label), 'friends: with no day of yours there is no “before you”, no row of yours', s.rows);
    await close(); }
  /* a friend whose day has passed is not “to come”; the ones who haven't set theirs are still counted */
  { const r = [{ user_id: F[1], day: '2026-10-19', at_time: null }, { user_id: F[0], day: '2026-10-22', at_time: '09:00:00' }];
    const { page, close } = await desk({ tables: withDay(null), rpc: rpcWith(r), time: '2026-10-21T10:00:00-07:00' }); await tick(page, 1500);
    const s = await stripOf(page);
    ok(s.rows.length === 1 && /Avery/.test(s.rows[0].names) && s.miss === '3 friends haven’t set theirs', 'friends: a day already gone is not listed (and that friend is not “unset”)', s);
    await close(); }
  /* nobody shared: with a day of yours the strip is your row and “5 friends haven’t set theirs”; with none, no strip at all */
  { const { page, close } = await desk({ tables: withDay({ day: '2026-10-21' }), rpc: rpcWith([]) }); await tick(page, 1500);
    const s = await stripOf(page);
    ok(s.rows.length === 1 && s.rows[0].me && s.miss === '5 friends haven’t set theirs', 'friends: nobody shared → just your row and “5 friends haven’t set theirs”', s);
    await close(); }
  { const { page, close } = await desk({ tables: withDay(null), rpc: rpcWith([]) }); await tick(page, 1500);
    ok((await stripOf(page)).text === '', 'friends: nobody shared and no day of yours → no strip at all');
    await close(); }
  /* only non-friends shared: still nothing of theirs */
  { const { page, close } = await desk({ tables: withDay({ day: '2026-10-21' }), rpc: rpcWith([rows[3]]) }); await tick(page, 1500);
    ok(await page.evaluate(() => !document.querySelector('#frRegStrip [data-id="33333333-3333-4333-8333-333333333399"]') && document.querySelectorAll('#frRegStrip .rs-row').length === 1), 'friends: a day from someone who is not your friend is never drawn');
    await close(); }
  /* the RPC fails: no strip, no error text, no crash, and your own card is left alone */
  { const hook = url => url.pathname === '/rest/v1/rpc/friend_registration_days' ? { status: 500, body: JSON.stringify({ code: 'XX000', message: 'down' }) } : null;
    const { page, close, log } = await desk({ tables: withDay({ day: '2026-10-21' }), hook }); await tick(page, 1500);
    const s = await slots(page);
    ok(s.plans.has && s.plans.head === 'Register Wed, Oct 21' && (await stripOf(page)).text === '' && log.errors.length === 0, 'friends: a failing RPC leaves your card alone and shows no strip', { s: s.plans, e: log.errors });
    await close(); }
  /* the Schedule card no longer lists friends */
  { const { page, close } = await desk({ tables: withDay({ day: '2026-10-21' }), rpc: rpcWith(rows) }); await tick(page, 1500);
    ok(await page.evaluate(() => !document.querySelector('.rg-fr') && !document.querySelector('.rg-slot .rg-f')), 'friends: the Schedule card has no friends’ list any more');
    await close(); }
  /* five days fit; a sixth day is behind “+1 more day” */
  { const many = FX.FRIENDS.slice(0, 5).map((f, i) => ({ user_id: f.id, day: '2026-10-2' + i, at_time: null }));
    const a = await desk({ tables: withDay(null), rpc: rpcWith(many) }); await tick(a.page, 1500);
    ok(await a.page.evaluate(() => document.querySelectorAll('#frRegStrip .rs-row').length === 5 && !document.querySelector('#frRegStrip .rs-more')), 'friends: five days are all there, no “more”');
    await a.close();
    const b = await desk({ tables: withDay({ day: '2026-10-26' }), rpc: rpcWith(many) }); await tick(b.page, 1500);
    await b.page.evaluate(() => show('friends')); await tick(b.page, 500);
    const hid = () => b.page.evaluate(() => [...document.querySelectorAll('#frRegStrip .rs-row')].map(r => r.offsetParent !== null));
    ok(JSON.stringify(await hid()) === '[true,true,true,true,true,false]' && /\+1 more day/.test(await b.page.evaluate(() => document.querySelector('#frRegStrip .rs-more').textContent)), 'friends: a sixth day waits behind “+1 more day”', await hid());
    await b.page.click('#frRegStrip .rs-more'); await tick(b.page, 300);
    ok((await hid()).every(Boolean), 'friends: “+1 more day” shows it');
    await b.close(); }
});

"""
s = one(s, "const o = await desk({ tables: withDay({ day: '2026-10-21' }), rpc, hook });", "const o = await desk({ tables: withDay(null), rpc, hook });")
s = span(s, "test('friends', async () => {", "test('parse', async () => {", new_friends)
s = s.rstrip('\n') + "\n/* " + MARK + ": this file was updated by edit-tests-reg-timeline-2026-10-16.py */\n"
p.write_text(s)
print('edited', p)

# ================================================================================================================ sync
p, s = load('check-desktop-sync.mjs')
new_sync = r"""test('regcard', async () => {
  /* reg-timeline (2026-10-16): the card is the Spring 2027 timeline (it was the "Round 1 registration opens" card, website-sync 2026-10-15) */
  const o = await live({ tables: clone(FX.TABLES) }); const { page } = o; await tick(page, 1500);
  const r = await page.evaluate(() => {
    const c = document.getElementById('hmRegCard'), td = document.querySelector('#hmRailR .hm-td'), rail = document.getElementById('hmRailR');
    const btns = c ? [...c.querySelectorAll('.tl-go, .tl-all')] : [];
    return { has: !!c, inRail: !!c && !!rail && rail.contains(c), after: !!c && !!td && td.nextElementSibling === c, text: c ? c.innerText.replace(/\s+/g, ' ').trim() : '',
      rows: c ? c.querySelectorAll('.tl-li').length : 0, btns: btns.map(b => b.textContent.replace(/\s+/g, ' ').trim()),
      w: c ? Math.round(c.getBoundingClientRect().width) : 0, rw: rail ? Math.round(rail.getBoundingClientRect().width) : 0, card: !!(c && c.classList.contains('hm-card')),
      top: document.getElementById('campusBanner').innerText.trim() };
  });
  ok(r.has && r.inRail && r.after, 'the card is on Home’s right rail, directly under the greeting card', r);
  ok(/^×? ?📅 Spring 2027/.test(r.text) && /Your Round 1/.test(r.text) && /Your Round 2/.test(r.text) && /Classes begin/.test(r.text) && /Last day to add/.test(r.text) && /Last day to drop/.test(r.text) && /Last day to withdraw/.test(r.text) && r.rows === 6, 'it is the Spring 2027 timeline: six rows — Round 1, Round 2, classes begin, last day to add, drop, withdraw', r);
  ok(JSON.stringify(r.btns) === '["Your game plan →","All dates"]', 'one primary button, “Your game plan”, and a quiet “All dates”', r.btns);
  ok(r.card && r.w <= r.rw && r.w > 150, 'it is a normal rail card, no wider than the rail', r);
  ok(r.top === '', 'nothing about registration is left in the strip at the top of the page', r.top);
  /* every other page: the strip stays empty of it */
  const tops = [];
  for (const v of ['sched', 'explore', 'friends']) { await page.evaluate(x => show(x), v); await tick(page, 500); tops.push(await page.evaluate(() => document.getElementById('campusBanner').innerText.trim())); }
  ok(tops.every(t => t === ''), 'Schedule, Explore and Friends have no registration banner either', tops);
  await page.evaluate(() => { show('sched'); if (typeof setSchedTab === 'function') setSchedTab('plans'); }); await tick(page, 800);
  ok(await page.evaluate(() => !!document.querySelector('.rg-slot[data-rg="plans"] .rg-card')), 'Schedule › Plans keeps its registration card');
  /* the x */
  await page.evaluate(() => show('home')); await tick(page, 500);
  await page.click('#hmRegCard .hm-regx'); await tick(page, 300);
  const d = await page.evaluate(() => ({ gone: !document.getElementById('hmRegCard'), ls: localStorage.getItem('professify_dismiss_regtl_' + sbUser.id + '_2274'), rg: !!document.querySelector('#hmRailR .rg-slot .rg-card') }));
  ok(d.gone && d.ls === '1', 'x dismisses it, remembered under the card’s own key (regtl_<user id>_2274)', d);
  ok(!d.rg, 'the rail’s own day card is gone for good — the pencils on the timeline replace it');
  await page.evaluate(() => renderHome()); await tick(page, 600);
  ok(await page.evaluate(() => !document.getElementById('hmRegCard')), 'a re-render does not bring it back');
  ok(o.log.errors.length === 0, 'no page errors', o.log.errors); await o.close();
  /* the buttons */
  const p = await live({ tables: clone(FX.TABLES) }); await tick(p.page, 1500);
  await p.page.click('#hmRegCard [data-tl-key="add1"]'); await tick(p.page, 400);
  ok(await p.page.evaluate(() => document.getElementById('rgBack').classList.contains('open')), 'Round 1’s “+ Add” opens the registration-day sheet');
  await p.page.keyboard.press('Escape'); await tick(p.page, 300);
  await p.page.evaluate(() => { window.__fb = 0; TCPlans.fromBanner = function () { window.__fb++; }; });
  await p.page.click('#hmRegCard .tl-go'); await tick(p.page, 300);
  ok(await p.page.evaluate(() => window.__fb) === 1, '“Your game plan” goes to the game plan');
  await p.close();
  /* not before 14 days, never signed out, and not after the term's last day of instruction (May 14) */
  for (const [t, si, why, want] of [['2026-10-01T10:30:00-07:00', true, 'eighteen days out', false], ['2026-10-05T10:30:00-07:00', true, 'fourteen days out', true], ['2026-10-20T10:30:00-07:00', true, 'the day after Round 1 opened', true],
    ['2027-01-27T10:30:00-08:00', true, 'once classes have begun', true], ['2027-05-15T10:30:00-07:00', true, 'the day after the last day of classes', false], [LIVE_NOW, false, 'signed out', false]]) {
    const q = await live({ time: t, signedIn: si, tables: clone(FX.TABLES) }); await tick(q.page, 1200);
    ok(await q.page.evaluate(() => !!document.getElementById('hmRegCard')) === want, (want ? 'the card shows ' : 'no card ') + why);
    await q.close();
  }
  /* the finals-week banner is not touched */
  const f = await live({ tables: clone(FX.TABLES), terms: { TERM: '2274', TERM_LABEL: 'Spring 2027', NOW_TERM: '2268', NOW_LABEL: 'Fall 2026', REGISTRATION_OPENS: '2027-01-01', QUARTER_END: '2026-10-17' } }); await tick(f.page, 1500);
  const fw = await f.page.evaluate(() => document.getElementById('campusBanner').innerText);
  ok(/Finals week/.test(fw), 'the finals-week banner still shows at the top', fw);
  await f.close();
});

/* ONE registration card on Home (the timeline), on the rail or, below 1140px, at the top of the main column */
test('regcard-one', async () => {
  const day = row => { const t = clone(FX.TABLES); t.registration_days = row ? [Object.assign({ user_id: ME, term: '2274', shared: true, updated_at: '2026-10-13T00:00:00Z' }, row)] : []; return t; };
  const cards = page => page.evaluate(() => {
    const vis = e => !!e && e.offsetParent !== null;
    return { compact: [...document.querySelectorAll('.hm-regcard')].filter(vis).length, old: [...document.querySelectorAll('.rg-slot[data-rg="rail"] .rg-card')].filter(vis).length,
      txt: (document.querySelector('#hmRegCard') || {}).innerText || '', day: (document.querySelector('#hmRegCard .hm-reg-day') || {}).textContent || null,
      btns: [...document.querySelectorAll('#hmRegCard .tl-go, #hmRegCard .tl-all')].map(b => b.textContent.replace(/\s+/g, ' ').trim()) };
  });
  /* no day set */
  let o = await live({ tables: day(null) }); await tick(o.page, 1500);
  let c = await cards(o.page);
  ok(c.compact === 1 && c.old === 0, 'one card on the rail, not two', c);
  ok(JSON.stringify(c.btns) === '["Your game plan →","All dates"]' && c.day === null && /Your Round 1 Opens Oct 19 \+ Add/.test(c.txt.replace(/\s+/g, ' ')), 'no day set: Round 1 says “+ Add · Opens Oct 19”, and there is no green day line', c);
  await o.page.click('#hmRegCard [data-tl-key="add1"]'); await tick(o.page, 400);
  ok(await o.page.evaluate(() => document.getElementById('rgBack').classList.contains('open')), 'it opens the same registration-day sheet');
  await o.page.keyboard.press('Escape'); await tick(o.page, 300);
  /* dismiss: nothing else takes its place on the rail */
  await o.page.click('#hmRegCard .hm-regx'); await tick(o.page, 400);
  c = await cards(o.page);
  ok(c.compact === 0 && c.old === 0, 'dismissed: no registration card on the rail at all', c);
  ok(o.log.errors.length === 0, 'one card: no page errors', o.log.errors); await o.close();
  /* a day set */
  o = await live({ tables: day({ day: '2026-10-21', at_time: '11:00:00' }) }); await tick(o.page, 1500);
  c = await cards(o.page);
  ok(c.compact === 1 && c.old === 0 && c.day === null && !/Change your registration day/.test(c.txt), 'a day set: one card, no “Change your registration day” button, no green day line', c);
  ok(/Your Round 1\s+Wed, Oct 21 · 11:00 AM\s+in 7 days/.test(c.txt.replace(/\n+/g, ' ').replace(/\s+/g, ' ')) || /Wed, Oct 21 · 11:00 AM/.test(c.txt), 'a day set: Round 1 says “Wed, Oct 21 · 11:00 AM · in 7 days”', c.txt);
  await o.page.click('#hmRegCard [data-tl-key="pen1"]'); await tick(o.page, 400);
  ok(await o.page.evaluate(() => document.getElementById('rgBack').classList.contains('open') && !!document.querySelector('.rg-d.on[data-day="2026-10-21"]')), 'the pencil opens the same sheet, on that day');
  await o.close();
  /* below 1140px the rail is hidden: the card is at the top of the main column */
  o = await live({ tables: day(null), width: 900 }); await tick(o.page, 1500);
  const n = await o.page.evaluate(() => {
    const t = document.getElementById('hmRegCardN'), feed = document.getElementById('hmFeed'), r = t ? t.getBoundingClientRect() : null, rail = document.getElementById('hmRegCard');
    return { has: !!t, shown: !!t && t.offsetParent !== null, top: r ? Math.round(r.top) : null, aboveFeed: !!t && !!feed && r.top < feed.getBoundingClientRect().top, railCopyHidden: !rail || rail.offsetParent === null,
      txt: t ? t.innerText.replace(/\s+/g, ' ').trim() : '', old: [...document.querySelectorAll('.rg-slot[data-rg="rail"] .rg-card')].filter(e => e.offsetParent !== null).length, within: !!t && r.right <= innerWidth && r.left >= 0 };
  });
  ok(n.has && n.shown && n.aboveFeed && n.within && n.railCopyHidden && n.old === 0, 'at 900px: the card is at the top of Home’s main column (above the feed), once', n);
  ok(/Spring 2027/.test(n.txt) && /Your game plan/.test(n.txt) && /Your Round 1/.test(n.txt), 'at 900px: the same content', n.txt);
  await o.page.click('#hmRegCardN .hm-regx'); await tick(o.page, 400);
  ok(await o.page.evaluate(() => !document.getElementById('hmRegCardN') && !document.getElementById('hmRegCard') && localStorage.getItem('professify_dismiss_regtl_' + sbUser.id + '_2274') === '1'), 'at 900px: x dismisses it for good');
  await o.close();
  /* a phone-width window: still one visible card, no sideways scroll */
  o = await live({ tables: day(null), width: 390, height: 844 }); await tick(o.page, 1500);
  c = await cards(o.page);
  ok(c.compact === 1 && c.old === 0 && await o.page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), 'at 390px: one card, at the top, no sideways scroll', c);
  await o.close();
  /* at 1440 the top copy is not shown */
  o = await live({ tables: day(null) }); await tick(o.page, 1500);
  ok(await o.page.evaluate(() => { const t = document.getElementById('hmRegCardN'); return !t || t.offsetParent === null; }), 'at 1440px the narrow-screen copy is not shown');
  ok(await o.page.evaluate(() => { const t = document.getElementById('hmRegCardN'); return !t || t.offsetParent === null; }) && (await cards(o.page)).compact === 1, 'at 1440px there is exactly one visible card');
  await o.close();
});

"""
s = span(s, "test('regcard', async () => {", "/* ======================================================================================================== TASK 2 */", new_sync)
s = s.rstrip('\n') + "\n/* " + MARK + ": this file was updated by edit-tests-reg-timeline-2026-10-16.py */\n"
p.write_text(s)
print('edited', p)
