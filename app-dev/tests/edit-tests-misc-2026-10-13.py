#!/usr/bin/env python3
"""(2026-10-13) tests for three small asks: Share on My Classes for the term you're in (share-now-term), notifications that
stay once seen (notifs-stay), and the "all caught up" line without its dash (caught-up-line).
Run after edit-tests-builder-top-ledger-2026-10-13.py:  python3 edit-tests-misc-2026-10-13.py <repo>"""
import sys, pathlib
root = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else '.')
p = root / 'app-dev/tests/check-app.mjs'; s = p.read_text()
m = root / 'app-dev/tests/mutate.mjs'; ms = m.read_text()
def rep(a, b, n=1):
    global s
    assert s.count(a) == n, (s.count(a), a[:90]); s = s.replace(a, b)

# My Classes on Fall (the term you're in) shares like Plans do — the card is Fall's classes, labelled Fall
rep("""  ok(a.on.join('|') === 'Fall 2026*|Spring 2027' && a.blocks.includes('BUS 3438'), 'my classes: with no Spring classes yet it opens on Fall (what you’re in), read from Fall', a);""",
    """  ok(a.on.join('|') === 'Fall 2026*|Spring 2027' && a.blocks.includes('BUS 3438'), 'my classes: with no Spring classes yet it opens on Fall (what you’re in), read from Fall', a);
  /* (2026-10-13, Tate) Share top right on Fall too, like Plans: the card is Fall's classes, labelled Fall */
  const sb = await page.evaluate(() => { const b = document.querySelector('#scroll .schhdr .schshare'); return b ? { x: b.dataset.x, lab: b.getAttribute('aria-label'), mine: b.classList.contains('dest-mine') } : null; });
  ok(sb && sb.x === 'now' && sb.lab === 'Share your week' && sb.mine, 'my classes (Fall): the blue Share button sits top right, like Plans (Tate 2026-10-13)', sb);
  await page.evaluate(() => { const c = TC.client(); c.storage.from = () => ({ upload: () => Promise.resolve({}) }); });
  await shareOpenAndWait(page, 'now');
  const sv = await page.evaluate(() => ({ what: UI.share.what, term: UI.share.term, state: UI.share.state, body: UI.share.body, alt: UI.share.alt, head: (document.querySelector('.sheet h3') || {}).textContent || '', codes: nowSecs('me').map(x => x.code), spring: personSecs('me').map(x => x.code) }));
  ok(sv.what === 'now' && sv.state === 'ready' && sv.term === 'Fall 2026' && sv.body === 'Here’s my Fall 2026 schedule' && sv.head === 'Share your week' && sv.codes.every(c => sv.alt.includes(c)) && !sv.spring.length, 'my classes (Fall): Share draws Fall’s classes and says “Here’s my Fall 2026 schedule” — not the empty Spring', sv);
  await page.evaluate(() => { UI.sheet = null; UI.share = null; render(true); });""")

# notifications stay once seen: New (unread, a dot) then Earlier (read, a chevron); the bell's dot is still new things only
rep("""tests.springDpr = async () => {""",
    """tests.notifsStay = async () => {   /* (2026-10-13, Tate) "once you've viewed it have them stay there like instagram" */
  const { page, close, log } = await openApp({});
  await page.waitForFunction(() => TC.ready, null, { timeout: 8000 }); await settle(page, 400);
  const rd = () => page.evaluate(() => ({ labels: [...document.querySelectorAll('.sheet .ntf-l')].map(e => e.textContent), rows: [...document.querySelectorAll('.sheet .ntf')].map(e => ({ cls: e.className, t: e.innerText.replace(/\\s+/g, ' ').trim(), dot: !!e.querySelector('.ntf-dot'), chev: !!e.querySelector('.chev'), a: e.dataset.a || '' })), empty: (document.querySelector('.sheet .empty') || {}).textContent || '', bell: !!document.querySelector('[data-x="notifs"] .dot') }));
  const th = await page.evaluate(() => TC.threads.filter(t => t.last && t.last.sender !== TC.user.id).map(t => t.id));
  ok(th.length >= 2, 'notifs: the fixture has two threads with a message from someone else', th);
  await page.evaluate(ids => { TC.threads.forEach(t => { if (t.id === ids[0]) t.last_read_at = null; if (t.id === ids[1]) t.last_read_at = new Date(Date.now() + 1e6).toISOString(); }); S.notifSeen = ''; render(true); }, th);
  const bellBefore = await page.evaluate(() => !!document.querySelector('[data-x="notifs"] .dot'));
  await page.evaluate(() => A.sheet('notifs')); await settle(page, 300);
  let v = await rd();
  const fresh = v.rows.filter(r => /\\bnew\\b/.test(r.cls)), seen = v.rows.filter(r => !/\\bnew\\b/.test(r.cls));
  ok(bellBefore && v.labels.join('|') === 'New|Earlier' && fresh.length >= 1 && seen.length >= 1 && fresh.every(r => r.dot || /friend request/.test(r.t)) && seen.every(r => r.chev && !r.dot && r.a === 'openChatTab') && !v.empty, 'notifs: New (the unread message, a dot; a friend request) then Earlier (the one you’ve read, with a chevron) — read ones stay', v);
  ok(v.rows.findIndex(r => !/\\bnew\\b/.test(r.cls)) > v.rows.findIndex(r => /\\bnew\\b/.test(r.cls)), 'notifs: every New row sits above Earlier', v.rows.map(r => r.cls));
  /* read the unread one: it moves to Earlier instead of vanishing */
  await page.evaluate(ids => { TC.threads.forEach(t => { if (t.id === ids[0]) t.last_read_at = new Date(Date.now() + 1e6).toISOString(); }); TC.requests = []; render(true); }, th);
  v = await rd();
  ok(!v.labels.length && v.rows.length >= 2 && v.rows.every(r => !/\\bnew\\b/.test(r.cls) && r.chev) && !v.empty && !v.bell, 'notifs: once everything’s seen the rows stay (no New / Earlier split, no dot on the bell), not “Nothing new”', v);
  await page.evaluate(() => { TC.threads = []; render(true); }); v = await rd();
  ok(/^Nothing new/.test(v.empty) && !v.rows.length, 'notifs: “Nothing new” only with nothing at all', v);
  ok(log.errors.length === 0, 'notifs: no page errors', log.errors);
  await close();
};
tests.springDpr = async () => {""")

# the all-caught-up line, no dash
rep("""  ok(/You’re all caught up/.test(a.msg) &&""", """  ok(/You’re all caught up\\. Every class on this report/.test(a.msg) && !/caught up —/.test(a.msg) &&""")
p.write_text(s)

def mrep(a, b, n=1):
    global ms
    assert ms.count(a) == n, (ms.count(a), a[:90]); ms = ms.replace(a, b)
mrep("""  ["foot: the pill back",""",
     """  ["share: no Share on the term you’re in", "return c === CFG.TERM ? 'mine' : splitTerms() && c && c === nowTerm().code ? 'now' : null;", "return c === CFG.TERM ? 'mine' : null;", "springMine"],
  ["share: the Fall card drawn from Spring’s classes", "if (what === 'now') { const secs = nowSecs('me'), loose = nowUnplaced('me')", "if (what === 'now') { const secs = personSecs('me'), loose = nowUnplaced('me')", "springMine"],
  ["share: the Fall card says Spring", "'Here’s my ' + w.term + ' schedule'", "'Here’s my ' + CFG.TERM_LABEL + ' schedule'", "springMine"],
  ["notifs: read messages vanish again", "seen = th.filter(t => !isUnread(t)).slice(0, 30).map(msg);", "seen = [];", "notifsStay"],
  ["notifs: no New / Earlier split", "fresh.length && seen.length ? sec('New', fresh) + sec('Earlier', seen) :", "false ? '' :", "notifsStay"],
  ["notifs: read rows keep the dot", "${un ? '<span class=\\"ntf-dot\\" role=\\"img\\" aria-label=\\"New\\"></span>' : `<span class=\\"chev\\">${ic('chevR', 18)}</span>`}", "<span class=\\"ntf-dot\\" role=\\"img\\" aria-label=\\"New\\"></span>", "notifsStay"],
  ["caught up: the dash back", "You’re all caught up. Every class on this report is already in TermChamp.", "You’re all caught up — every class on this report is already in TermChamp.", "dprAllIn"],
  ["foot: the pill back",""")
m.write_text(ms)
print('edit-tests-misc: applied')

# --- review round (2026-10-13): the Fall link's preview term, and the three older Share mutants whose lines changed ---
s = p.read_text(); ms = m.read_text()
rep("""  ok(sv.what === 'now' && sv.state === 'ready' && sv.term === 'Fall 2026' && sv.body""",
    """  sv.tm = await page.evaluate(() => new URL(UI.share.link).searchParams.get('tm'));
  ok(sv.what === 'now' && sv.state === 'ready' && sv.term === 'Fall 2026' && sv.tm === 'Fall 2026' && sv.body""")
rep("""  await page.evaluate(() => { const c = TC.client(); c.storage.from = () => ({ upload: () => Promise.resolve({}) }); });
  await shareOpenAndWait(page, 'now');""",
    """  const dis = await page.evaluate(() => { const was = TC.nowMineRows; TC.nowMineRows = null; render(true); const b = document.querySelector('#scroll .schhdr .schshare'), d = !!(b && b.disabled); TC.nowMineRows = was; render(true); return d; });
  ok(dis, 'my classes (Fall): Share waits for Fall’s classes (disabled while they load)', dis);
  await page.evaluate(() => { const c = TC.client(); c.storage.from = () => ({ upload: () => Promise.resolve({}) }); });
  await shareOpenAndWait(page, 'now');""")
p.write_text(s)
for old, new in (('"${w === \'mine\' ? \'dest-mine\' : \'plan-\' + w}"', '"${w === \'mine\' || w === \'now\' ? \'dest-mine\' : \'plan-\' + w}"'),
                 ('"if (S.schedTab === \'mine\') return mineTerm().code === CFG.TERM ? \'mine\' : null;"', '"if (S.schedTab === \'mine\') { const c = mineTerm().code; return c === CFG.TERM ? \'mine\' : splitTerms() && c && c === nowTerm().code ? \'now\' : null; }"'),
                 ('"aria-label=\\"${w === \'mine\' ? \'Share your week\' : \'Share Plan \' + w}\\""', '"aria-label=\\"${w === \'mine\' || w === \'now\' ? \'Share your week\' : \'Share Plan \' + w}\\""')):
    mrep(old, new)
mrep('''  ["foot: the pill back",''', '''  ["share: the Fall link previews as Spring", "q += '&tm=' + encodeURIComponent(term || CFG.TERM_LABEL);", "q += '&tm=' + encodeURIComponent(CFG.TERM_LABEL);", "springMine"],
  ["share: Fall's Share live before Fall's classes load", "(w !== 'now' || (TC.nowMineRows && !TC.err.nowMine))", "true", "springMine"],
  ["foot: the pill back",''')
m.write_text(ms)
print('edit-tests-misc (review round): applied')
