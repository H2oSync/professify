#!/usr/bin/env python3
"""(2026-10-16) Keeps the older desktop checks true after friend-polish-2026-10-16.py (website; marker 'friend-polish (2026-10-16)'):
  check-desktop-home.mjs   a Home friend card names the plan/term ONCE in its header line ("Plan B . Spring 2027 . 3 classes"), has no second chip, "New" is one
                           small marker, and a Spring / plan card has no free-today line (cardOf gains chips / line / head);
  check-desktop-terms.mjs  a friend's term control is one switch button (data-term), not two pills;
  check-desktop-sync.mjs   a pinned story carries a pin before the name, not a badge on the ring.
Usage: python3 edit-tests-friend-polish-2026-10-16.py <repo>"""
import sys, pathlib
root = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else '.')
def edit(name, pairs):
    p = root / 'app-dev/tests' / name; s = p.read_text()
    if 'friend-polish (2026-10-16)' in s: sys.exit('already edited ' + name)
    for a, b in pairs:
        assert s.count(a) == 1, (name, s.count(a), a[:100]); s = s.replace(a, b)
    s = s.rstrip('\n') + '\n/* friend-polish (2026-10-16): this file was updated by edit-tests-friend-polish-2026-10-16.py */\n'
    p.write_text(s); print('edited', p)

edit('check-desktop-home.mjs', [
 ("""    ctx: (a.querySelector('.ctx') || {}).textContent || '', txt: a.innerText,""",
  """    ctx: (a.querySelector('.ctx') || {}).textContent || '', txt: a.innerText, chips: a.querySelectorAll('.hm-fview').length, line: (a.querySelector('.av-line') || {}).textContent || null,
    head: (a.querySelector('.fhead-t') || {}).innerText || '',"""),
 ("""ok(av && av.view === 'next' && av.tag === 'Spring 2027 classes' && /^Planning 4 classes · Spring 2027/.test(av.ctx), 'Avery (Spring classes): tag “Spring 2027 classes”, “Planning 4 classes · Spring 2027”', av && { v: av.view, t: av.tag, c: av.ctx });""",
  """ok(av && av.view === 'next' && av.chips === 0 && /^Spring 2027 · 4 classes/.test(av.ctx) && (av.head.match(/Spring 2027/g) || []).length === 1, 'Avery (Spring classes): the header says “Spring 2027 · 4 classes” once, no second chip', av && { v: av.view, c: av.ctx, h: av.head });
  ok([av, ro].every(x => x && x.line === null && !/left today|both open|No class till/.test(x.txt)), 'a Spring / plan card has no free-today line (“No class left today · both open …”)', [av && av.line, ro && ro.line]);"""),
 ("""ok(ro && ro.view === 'B' && ro.tag === 'Plan B · Spring 2027' && /^Planning 3 classes · Spring 2027/.test(ro.ctx), 'Rowan (only a shared Spring plan): the first shared plan — “Plan B · Spring 2027”, “Planning 3 classes”', ro && { v: ro.view, t: ro.tag, c: ro.ctx });""",
  """ok(ro && ro.view === 'B' && ro.chips === 0 && /^Plan B · Spring 2027 · 3 classes/.test(ro.ctx) && (ro.head.match(/Spring 2027/g) || []).length === 1 && (ro.head.match(/Plan/g) || []).length === 1, 'Rowan (only a shared Spring plan): the first shared plan — one line, “Plan B · Spring 2027 · 3 classes”', ro && { v: ro.view, c: ro.ctx, h: ro.head });"""),
 ("""ok(ro && /hm-plan-B/.test(ro.cls) && ro.tagColor === 'rgb(154, 52, 18)', 'Rowan: the card and tag are in Plan B’s colour (orange ink #9A3412)', ro && { c: ro.cls, col: ro.tagColor });""",
  """ok(ro && /hm-plan-B/.test(ro.cls), 'Rowan: the card is in Plan B’s colour (hm-plan-B)', ro && ro.cls);"""),
 ("""ok(sk && sk.view === 'now' && sk.tag === 'Now · Fall 2026' && /^Taking 2 classes · Fall 2026/.test(sk.ctx), 'Sky (Fall only): her week now — “Now · Fall 2026”, “Taking 2 classes · Fall 2026”', sk && { t: sk.tag, c: sk.ctx });""",
  """ok(sk && sk.view === 'now' && sk.chips === 0 && /^Taking 2 classes · Fall 2026/.test(sk.ctx) && (sk.head.match(/Fall 2026/g) || []).length === 1, 'Sky (Fall only): her week now — “Taking 2 classes · Fall 2026”, said once', sk && { c: sk.ctx, h: sk.head });"""),
 ("""ok(qu && qu.view === 'now' && qu.tag === 'Now · Fall 2026' && /^Taking 1 class · Fall 2026/.test(qu.ctx),""",
  """ok(qu && qu.view === 'now' && /^Taking 1 class · Fall 2026/.test(qu.ctx),"""),
 ("""ok(ro && ro.fresh === 'New plan' && ro.view === 'A' && ro.tag === 'Plan A · Spring 2027', 'Rowan: “New plan” on Plan A', ro && { f: ro.fresh, t: ro.tag });""",
  """ok(ro && ro.fresh === 'New' && ro.view === 'A' && ro.chips === 0 && /^Plan A · Spring 2027 · \\d class(?:es)?New$/.test(ro.ctx) && (ro.head.match(/Spring 2027/g) || []).length === 1, 'Rowan: one small “New” on Plan A, the plan and term said once', ro && { f: ro.fresh, c: ro.ctx, h: ro.head });"""),
 ("""ok(sk && sk.fresh === 'Spring classes added' && sk.tag === 'Spring 2027 classes', 'Sky: “Spring classes added” on her Spring classes', sk && { f: sk.fresh, t: sk.tag });""",
  """ok(sk && sk.fresh === 'New' && sk.chips === 0 && /^Spring 2027 · \\d class(?:es)?New$/.test(sk.ctx), 'Sky: one small “New” on her Spring classes', sk && { f: sk.fresh, c: sk.ctx });"""),
])

edit('check-desktop-terms.mjs', [
 ("""  let fp = await page.evaluate(() => ({ chips: [...document.querySelectorAll('.frp-terms button')].map(b => b.textContent + (b.getAttribute('aria-pressed') === 'true' ? '*' : '')), txt""",
  """  let fp = await page.evaluate(() => ({ chips: [...document.querySelectorAll('.frp-terms button')].map(b => b.textContent.trim() + '*'), txt"""),
 ("""  fp = await page.evaluate(() => ({ chips: [...document.querySelectorAll('.frp-terms button')].map(b => b.textContent + (b.getAttribute('aria-pressed') === 'true' ? '*' : '')), txt""",
  """  fp = await page.evaluate(() => ({ chips: [...document.querySelectorAll('.frp-terms button')].map(b => b.textContent.trim() + '*'), txt"""),
 ("""ok(fp.chips.join('|') === 'Fall 2026*|Spring 2027' && !/BUS 4401/.test(fp.txt), 'friend page: Fall 2026 · Spring 2027, open on their week now (no Spring class on it)', fp.chips);""",
  """ok(fp.chips.join('|') === 'Fall 2026*' && !/BUS 4401/.test(fp.txt), 'friend page: one term switch (the phone’s look) showing Fall 2026, open on their week now (no Spring class on it)', fp.chips);"""),
 ("""ok(fp.chips.join('|') === 'Fall 2026|Spring 2027*' && /BUS 4401/.test(fp.txt), 'friend page: Spring shows their Spring classes', fp.chips);""",
  """ok(fp.chips.join('|') === 'Spring 2027*' && /BUS 4401/.test(fp.txt), 'friend page: Spring shows their Spring classes', fp.chips);"""),
])

edit('check-desktop-sync.mjs', [
 ("""badge: !!b.querySelector('.hm-pinbadge'),""", """badge: !!b.querySelector('.hm-pinmark') && !b.querySelector('.hm-pinbadge'),"""),
 ("""'a pinned story wears the pin badge'""", """'a pinned story wears a small pin before its name (no badge on the ring)'"""),
])
