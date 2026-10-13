#!/usr/bin/env python3
"""Tate (2026-10-13), on My Classes showing Fall 2026 (the term you're in) with no Share: "add the share in top right like
plans shows". Since the spring wall, My Classes on the term you're in had no Share button — schShareWhat only knew the pick
term ('mine') and the plans. Now the term you're in shares too ('now'): the same blue button top right, the same sheet, the
card drawn from that term's classes (nowSecs / nowUnplaced) and labelled with that term. Replayable on 05:50.
  python3 share-now-term-2026-10-13.py <repo-dir>"""
import pathlib, sys
ROOT = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else '.')
p = ROOT / 'app/index.html'; s = p.read_text()
def rep(a, b):
    global s
    if s.count(a) != 1: sys.exit(f'share-now-term: expected 1 of {a[:80]!r}, found {s.count(a)}')
    s = s.replace(a, b)
rep("""  if (S.schedTab === 'mine') return mineTerm().code === CFG.TERM ? 'mine' : null;""",
    """  if (S.schedTab === 'mine') { const c = mineTerm().code; return c === CFG.TERM ? 'mine' : splitTerms() && c && c === nowTerm().code ? 'now' : null; }   /* (2026-10-13) the term you're in shares too */""")
rep("""  return `<button class="iconbtn schshare ${w === 'mine' ? 'dest-mine' : 'plan-' + w}" data-a="shareOpen" data-x="${w}" aria-label="${w === 'mine' ? 'Share your week' : 'Share Plan ' + w}" """,
    """  return `<button class="iconbtn schshare ${w === 'mine' || w === 'now' ? 'dest-mine' : 'plan-' + w}" data-a="shareOpen" data-x="${w}" aria-label="${w === 'mine' || w === 'now' ? 'Share your week' : 'Share Plan ' + w}" """)
rep("""  if (what === 'mine') { const secs = personSecs('me'), loose = (PEOPLE.me.unplaced || []).filter(c => !secs.some(x => x.code === c)); return { secs, loose, plan: null, title: (shFirst() ? shFirst() + '’s' : 'My') + ' week', term: CFG.TERM_LABEL }; }""",
    """  if (what === 'mine') { const secs = personSecs('me'), loose = (PEOPLE.me.unplaced || []).filter(c => !secs.some(x => x.code === c)); return { secs, loose, plan: null, title: (shFirst() ? shFirst() + '’s' : 'My') + ' week', term: CFG.TERM_LABEL }; }
  if (what === 'now') { const secs = nowSecs('me'), loose = nowUnplaced('me').filter(c => !secs.some(x => x.code === c)); return { secs, loose, plan: null, title: (shFirst() ? shFirst() + '’s' : 'My') + ' week', term: nowTerm().label }; }""")
rep("""  const w = shWhat(what), sh = UI.share = { what, plan: w.plan, sent: {}, busy: {}, state: 'draw' };""",
    """  const w = shWhat(what), sh = UI.share = { what, plan: w.plan, term: w.term, sent: {}, busy: {}, state: 'draw' };""")
rep("""  const cv = shCard({ title: w.title, sub: CFG.TERM_LABEL + ' · ' + shCount(w) + ' class' + (shCount(w) === 1 ? '' : 'es'),""",
    """  const cv = shCard({ title: w.title, sub: (w.plan ? CFG.TERM_LABEL : w.term) + ' · ' + shCount(w) + ' class' + (shCount(w) === 1 ? '' : 'es'),""")
rep("""  sh.body = (w.plan ? 'Here’s my Plan ' + w.plan + ' for ' + CFG.TERM_LABEL : 'Here’s my ' + CFG.TERM_LABEL + ' schedule');""",
    """  sh.body = (w.plan ? 'Here’s my Plan ' + w.plan + ' for ' + CFG.TERM_LABEL : 'Here’s my ' + w.term + ' schedule');""")
rep("""  if (sh.state === 'empty') return head + `<div class="empty"><b>Nothing to share yet</b>${P ? 'Add classes to Plan ' + P + ' first.' : 'Add your ' + esc(CFG.TERM_LABEL) + ' classes first.'}</div>`;""",
    """  if (sh.state === 'empty') return head + `<div class="empty"><b>Nothing to share yet</b>${P ? 'Add classes to Plan ' + P + ' first.' : 'Add your ' + esc(sh.term || CFG.TERM_LABEL) + ' classes first.'}</div>`;""")
rep("""UI.sheet = { type: 'share' }; shPrepare(what === 'mine' || /^[ABC]$/.test(what) ? what : 'mine')""",
    """UI.sheet = { type: 'share' }; shPrepare(what === 'mine' || what === 'now' || /^[ABC]$/.test(what) ? what : 'mine')""")
# the link's preview term is the card's term (a Fall share says Fall), and Share waits for that term's classes to load
rep("""function shLink(id, plan) {""", """function shLink(id, plan, term) {""")
rep("""  q += '&tm=' + encodeURIComponent(CFG.TERM_LABEL);""", """  q += '&tm=' + encodeURIComponent(term || CFG.TERM_LABEL);""")
rep("""sh.link = shLink(hit, w.plan);""", """sh.link = shLink(hit, w.plan, w.plan ? null : w.term);""")
rep("""sh.link = shLink(id, w.plan);""", """sh.link = shLink(id, w.plan, w.plan ? null : w.term);""")
rep("""'Share Plan ' + w}" ${TC.seatsLoaded ? '' : 'disabled'}>""",
    """'Share Plan ' + w}" ${TC.seatsLoaded && (w !== 'now' || (TC.nowMineRows && !TC.err.nowMine)) ? '' : 'disabled'}>""")
rep("""  shareOpen: what => { if (!TC.seatsLoaded) { toast('Still loading your classes — try again in a moment'); return; }""",
    """  shareOpen: what => { if (!TC.seatsLoaded || (what === 'now' && (!TC.nowMineRows || TC.err.nowMine))) { toast('Still loading your classes — try again in a moment'); return; }""")
p.write_text(s)
print('share-now-term: applied')
