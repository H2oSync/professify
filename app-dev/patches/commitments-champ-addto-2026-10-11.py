#!/usr/bin/env python3
r"""Work & activities, round 2 (Tate, 2026-10-11): "fix these … Adding a class from Explore doesn't warn you if it
overlaps your work or practice. (adding a class should show it intersecting and pose a question or express that it
conflics) · Champ doesn't know about them."

Add to your week:
  · the week in the sheet draws your work, practice and the rest (hatched, by name, not tappable here); one the new
    section overlaps is outlined in red;
  · the note says so and asks: "Overlaps your Barista shift · Tue/Thu 4–8p. Add it anyway?" — the button reads
    "Add anyway" (a plan: "Add to Plan A anyway"), with "Edit Barista shift" under it. A section that also clashes
    with a class keeps that note and adds "It also overlaps your Barista shift."
Champ (the answers are the phone's own, so this is where it learns them):
  · your day and free time count them ("When am I free Tuesday?", "What's my day look like?"): the day card draws
    them hatched (tap to edit), the free stretches go around them, and "You're in …" reads "Barista shift until 8p";
  · free with friends goes around yours and a friend's Busy times;
  · "Does BUS 3431 fit my schedule / Plan A?" counts an overlap with them as a clash ("Clashes with Barista shift");
    every section over them → "No — every BUS 3431 section overlaps your work.";
  · "My conflicts" counts a class over one;
  · new: "When do I work?", "my practice schedule", "what are my shifts" → your list (tap to see or edit), or how to
    add one.
Run AFTER commitments-2026-10-11.py.  Usage: python3 commitments-champ-addto-2026-10-11.py <repo-dir>   (replayable)"""
import sys, os
PA = os.path.join(sys.argv[1], 'app', 'index.html'); S = open(PA, encoding='utf-8').read()
def rep(a, b, label, n=1):
    global S
    if S.count(a) != n: sys.exit(f'{label}: anchor matched {S.count(a)}x')
    S = S.replace(a, b)

# ---------- the grid: a read-only way to draw them (the Add sheet), and a hit outline
rep("""      return x.mine ? `<button class="g-cm" style="top:${top}px;height:${h}px" data-a="cmOpen" data-x="${esc(x.id)}" aria-label="${esc(al)}"><span>${esc(x.label)}</span></button>` : `<span class="g-cm fr" style="top:${top}px;height:${h}px" role="img" aria-label="${esc(al)}"><span>Busy</span></span>`; }).join('');""",
    """      if (x.ro) return `<span class="g-cm ro${x.hit ? ' hit' : ''}" style="top:${top}px;height:${h}px" role="img" aria-label="${esc(al + (x.hit ? ' — overlaps' : ''))}"><span>${esc(x.label)}</span></span>`;
      return x.mine ? `<button class="g-cm" style="top:${top}px;height:${h}px" data-a="cmOpen" data-x="${esc(x.id)}" aria-label="${esc(al)}"><span>${esc(x.label)}</span></button>` : `<span class="g-cm fr" style="top:${top}px;height:${h}px" role="img" aria-label="${esc(al)}"><span>Busy</span></span>`; }).join('');""", 'grid ro')

# ---------- Add to your week
rep("""  const spot = !o.other && !o.inIt && !added;""", """  const spot = !o.other && !o.inIt && !added;
  /* (2026-10-11) your work, practice and the rest: drawn on this week, and the ones this section would overlap */
  const cmHit = !o.other && !o.inIt && !added && chTimed(s) ? TC.commits.filter(c => secClash(s, c)) : [];
  const cmEx = o.other ? [] : TC.commits.map(c => ({ id: c.id, days: c.days, s: c.s, e: c.e, label: cmLabel(c), ro: true, hit: cmHit.includes(c) }));""", 'addto hit')
rep("""clashIds: new Set(spot ? o.clash.map(x => x.id) : []), hiDays: s.async || s.s == null ? [] : [...s.days], one: true, fit: 30, H: 300 })""",
    """clashIds: new Set(spot ? o.clash.map(x => x.id) : []), hiDays: s.async || s.s == null ? [] : [...s.days], one: true, fit: 30, H: 300, extra: cmEx })""", 'addto grid')
rep("""  if (sh.err && !adding) { note = esc(sh.err); tn = 'bad'; }
  const cls = ['addto',""", """  /* (2026-10-11) over your work or practice: say so and ask; with a class clash too, say both */
  if (cmHit.length && !adding && !sh.err) {
    const w = cmHit.map(c => `${esc(cmLabel(c))} · ${esc(daysLabel(c.days))} ${hs(c.s)}–${hs(c.e)}`).join(', ');
    if (tn === 'ok') { note = `Overlaps your ${w}. Add it anyway?`; tn = 'warn'; btn = go(o.mine ? 'Add anyway' : `Add to Plan ${o.P} anyway`); alt = `<button class="at-alt" data-a="cmOpen" data-x="${esc(cmHit[0].id)}">Edit ${esc(cmLabel(cmHit[0]))}</button>`; }
    else note += ` It also overlaps your ${w}.`;
  }
  if (sh.err && !adding) { note = esc(sh.err); tn = 'bad'; }
  const cls = ['addto',""", 'addto note')

# ---------- Champ: the day, free time, together, fits, conflicts, and "when do I work?"
rep("""function chDaySecs(id, d) { return nowSecs(id).filter(s => chTimed(s) && s.days.includes(d)).sort((a, b) => a.s - b.s); }""",
    """function chDaySecs(id, d) {
  /* (2026-10-11) work, practice and the rest fill the day too: yours by name, a friend's as Busy */
  const c = cmBlocks(id).filter(x => x.days.includes(d)).map(x => ({ code: x.label, s: x.s, e: x.e, days: x.days, busy: true, cmId: x.mine ? x.id : '' }));
  return nowSecs(id).filter(s => chTimed(s) && s.days.includes(d)).concat(c).sort((a, b) => a.s - b.s);
}""", 'chDaySecs')
rep("""function ansDayCard(d, mode) {
  if (!nowSecs('me').some(chTimed)) return""", """function ansDayCard(d, mode) {
  if (!nowSecs('me').some(chTimed) && !TC.commits.length) return""", 'day no classes')
rep("""  return { t: today ? [now ? `You’re in ${esc(now.code)} until ${hs(now.e)}.` : '', next ? `Next: ${esc(next.code)} at ${hs(next.s)}.` : 'Nothing else today.'].filter(Boolean).join(' ') : `${l.length} class${l.length === 1 ? '' : 'es'} ${DAYL[d]}, ${hs(l[0].s)}–${hs(l[l.length - 1].e)}.`, card: { k: 'day', d }, follow };""",
    """  const nc = l.filter(s => !s.busy).length, cw = cmDayWords(d);
  return { t: today ? [now ? (now.busy ? `${esc(now.code)} until ${hs(now.e)}.` : `You’re in ${esc(now.code)} until ${hs(now.e)}.`) : '', next ? `Next: ${esc(next.code)} at ${hs(next.s)}.` : 'Nothing else today.'].filter(Boolean).join(' ') : `${[nc ? `${nc} class${nc === 1 ? '' : 'es'}` : '', cw ? esc(cw) : ''].filter(Boolean).join(' and ')} ${DAYL[d]}, ${hs(l[0].s)}–${hs(l[l.length - 1].e)}.`, card: { k: 'day', d }, follow };""", 'day text')
rep("""  const blocks = l.map(s => `<button class="chd-b" style="top:${(y(s.s) + 1).toFixed(1)}px;height:${bh(s).toFixed(1)}px" data-a="openClass" data-x="${esc(s.code)}" data-y="${esc(s.id || '')}">""",
    """  const blocks = l.map(s => s.busy ? `<button class="chd-b chd-cm" style="top:${(y(s.s) + 1).toFixed(1)}px;height:${bh(s).toFixed(1)}px" data-a="cmOpen" data-x="${esc(s.cmId)}"><b>${esc(s.code)}</b><span>${hs(s.s)}–${hs(s.e)}</span></button>` : `<button class="chd-b" style="top:${(y(s.s) + 1).toFixed(1)}px;height:${bh(s).toFixed(1)}px" data-a="openClass" data-x="${esc(s.code)}" data-y="${esc(s.id || '')}">""", 'day blocks')
rep("""${chChip(l.length + ' class' + (l.length === 1 ? '' : 'es'), 'blue')}<button class="chc-open" data-a="schedTabGo" data-x="mine">Week ›</button></div><div class="chd">""",
    """${chChip(l.filter(s => !s.busy).length + ' class' + (l.filter(s => !s.busy).length === 1 ? '' : 'es'), 'blue')}${cmDayWords(d) ? chChip(esc(cmDayWords(d))) : ''}<button class="chc-open" data-a="schedTabGo" data-x="mine">Week ›</button></div><div class="chd">""", 'day chip')
rep("""function ansFreeWeek(days) {
  if (!nowSecs('me').some(chTimed)) return""", """function ansFreeWeek(days) {
  if (!nowSecs('me').some(chTimed) && !TC.commits.length) return""", 'week no classes')
rep("""  if (!nowSecs('me').some(chTimed)) return { t: `Add your ${esc(nowTerm().label)} classes and I can match your free time with friends’.`""",
    """  if (!nowSecs('me').some(chTimed) && !TC.commits.length) return { t: `Add your ${esc(nowTerm().label)} classes and I can match your free time with friends’.`""", 'together no classes')
# fits: an overlap with them is a clash
rep("""  const clashOf = s => !chTimed(s) ? [] : P === 'mine' ? clashWithMine(s) : conflicts(ids, s);""",
    """  /* (2026-10-11) your work, practice and the rest count as clashes too */
  const cmOf = s => TC.commits.filter(c => secClash(s, c)).map(c => ({ code: cmLabel(c), id: 'cm:' + c.id, days: c.days, s: c.s, e: c.e, cm: true }));
  const clashOf = s => !chTimed(s) ? [] : (P === 'mine' ? clashWithMine(s) : conflicts(ids, s)).concat(cmOf(s));""", 'fit clash')
rep("""  return { t: `No — every ${esc(code)} section clashes with ${L}.`, card: { k: 'fit', code, P, id: s.id }, follow: [`Other ${code} sections?`].concat(follow.slice(1)) };""",
    """  if (f.best.cl.every(x => x.cm)) return { t: `No — every ${esc(code)} section overlaps your ${esc(cmWords())}.`, card: { k: 'fit', code, P, id: s.id }, follow: [`Other ${code} sections?`].concat(follow.slice(1)) };
  return { t: `No — every ${esc(code)} section clashes with ${L}.`, card: { k: 'fit', code, P, id: s.id }, follow: [`Other ${code} sections?`].concat(follow.slice(1)) };""", 'fit text')
rep("""  if (P === 'mine' && !personSecs('me').some(chTimed)) return""", """  if (P === 'mine' && !personSecs('me').some(chTimed) && !TC.commits.length) return""", 'fit nothing timed')
# conflicts: a class over one of them
rep("""  m.forEach((s, i) => m.slice(i + 1).forEach(t => { if (chTimed(s) && chTimed(t) && s.code !== t.code && [...s.days].some(d => t.days.includes(d)) && s.s < t.e && t.s < s.e) { ids.add(s.id); ids.add(t.id); } }));
  return ids;""", """  m.forEach((s, i) => m.slice(i + 1).forEach(t => { if (chTimed(s) && chTimed(t) && s.code !== t.code && [...s.days].some(d => t.days.includes(d)) && s.s < t.e && t.s < s.e) { ids.add(s.id); ids.add(t.id); } }));
  m.forEach(s => { if (chTimed(s) && TC.commits.some(c => secClash(s, c))) ids.add(s.id); });   /* (2026-10-11) over your work or practice */
  return ids;""", 'conflicts')
# "when do I work?"
rep("""function chIntent(q) {
  const t = String(q || '').toLowerCase().replace(/[’‘]/g, "'"), m = t.match(CH_CODE), c0 = m ? cc(m[1] + ' ' + m[2]) : null, code = c0 && COURSES[c0] ? c0 : null;""",
    """/* (2026-10-11) "when do I work?", "my practice schedule", "what are my shifts": your list, from this phone */
const CH_CMQ = /\\b(when do i (work|have (work|practice|club|my shift))|when am i (working|at work|at practice)|what are my (shifts|work hours|practice times)|my (work|job|shift|practice|club) (schedule|hours|times|days)|my (shifts|work hours|practice times)|do i (work|have work|have practice) (today|tomorrow|on))\\b/;
function ansCommits() {
  if (!TC.commits.length) return { t: 'You haven’t added work or practice yet. Add it and the Builder keeps your plans clear of it.', acts: [['Add work', 'cmAdd', 'work'], ['Add practice', 'cmAdd', 'practice']] };
  return { t: TC.commits.map(x => `${esc(cmLabel(x))}: ${esc(cmDaysText(x.days))} ${hs(x.s)}–${hs(x.e)}`).join(' · ') + '.', acts: [['See or edit', 'sheet', 'cmList']], follow: ['When am I free this week?'] };
}
function chIntent(q) {
  const t = String(q || '').toLowerCase().replace(/[’‘]/g, "'"), m = t.match(CH_CODE), c0 = m ? cc(m[1] + ' ' + m[2]) : null, code = c0 && COURSES[c0] ? c0 : null;
  if (CH_CMQ.test(t)) return ansCommits();""", 'intent')
rep(""".cm-vb{""", """.g-cm.ro{cursor:default}.g-cm.hit{border:2px solid var(--red-ink);color:var(--red-ink)}
.chd-cm{background:repeating-linear-gradient(135deg,var(--fill2) 0 5px,var(--fill) 5px 10px)!important;border:1px solid var(--line2)!important;color:var(--ink3)!important}
.cm-vb{""", 'css')
open(PA, 'w', encoding='utf-8').write(S); print('commitments-champ-addto: done')
