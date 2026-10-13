#!/usr/bin/env python3
r"""The Planner becomes the Builder (Tate, 2026-10-11): "lets also change planner to be called builder. and it doesnt need
the schedule look instead it just displays the recommended classes to take. It should be able to show something like
recommended for plan A, vs B, C and that allows our tool to make sure no classes in a Plan that we recommend overlap
but classes can be at different times in different plans. it pretty much sculpts the perfect scenario 3 times. I dont
like the best fit, backup and friends. instead do the A is best combination of fulfilling their flowchart and degree
combined with best professors and friends each Plan should be the best combination of these but different so if one
class fill up or a friend is in a different section it can provide agility to switch between them but they should all
have this same goal."

  · Schedule's fourth tab reads "Builder" (the key stays 'planner'); the words "Planner" the student reads say Builder.
  · The plan card is "Recommended for Plan A" — no week grid, no Anytime strip: each recommended class with its time,
    why it counts, its professor's rating and the friends in that section; a line of units · rating · friends.
  · The tabs are Plan A · Plan B · Plan C — no "Best fit / Backup / Friends".
  · Drafting: all three plans have the same goal — the picks' own ranking (degree first by your priority, professors,
    friends) — and none overlaps inside itself. A is the best combination. B, then C, are the next-best combination
    built to differ: a class already in an earlier plan takes another section when one fits (ranked by professor and
    friends in it, never a full one once registration is open), and a pick already in earlier plans is ranked a little
    lower so a near-equal class can take its place. Required classes still stay — only the sections move.
    (Supersedes 2026-10-11's "Keep C as it is": C is no longer friends ×2.5, and B is no longer A's classes in other
    sections only.)
Usage: python3 builder-2026-10-11.py <repo-dir>   (replayable)"""
import sys, os
PA = os.path.join(sys.argv[1], 'app', 'index.html'); S = open(PA, encoding='utf-8').read()
def rep(a, b, label, n=1):
    global S
    if S.count(a) != n: sys.exit(f'{label}: anchor matched {S.count(a)}x')
    S = S.replace(a, b)

# --- the name
rep("""['planner', 'Planner'], ['past', 'Past classes']""", """['planner', 'Builder'], ['past', 'Past classes']""", 'tab')
rep("""go = [['Show in Planner', 'prereqGo', c]];""", """go = [['Show in Builder', 'prereqGo', c]];""", 'prereq go')
rep("""The Planner will show it for ${esc(c)}.""", """The Builder will show it for ${esc(c)}.""", 'prereq wait')
rep("""The Planner picks what to take next.', acts: [['Open Past classes', 'schedTabGo', 'past'], ['Open Planner', 'schedTabGo', 'planner']]""",
    """The Builder picks what to take next.', acts: [['Open Past classes', 'schedTabGo', 'past'], ['Open Builder', 'schedTabGo', 'planner']]""", 'champ scope')
rep("""case 'build_term': return { t: 'TermChamp’s picks in the Planner are the classes to take next.', acts: [['Open Planner', 'schedTabGo', 'planner']] };""",
    """case 'build_term': return { t: 'TermChamp’s picks in the Builder are the classes to take next.', acts: [['Open Builder', 'schedTabGo', 'planner']] };""", 'champ build')
rep("""errCard('Couldn’t load the planner.', 'retryPlanner')""", """errCard('Couldn’t load the Builder.', 'retryPlanner')""", 'err')
rep("""<p class="lead">Your Planner builds everything from it.</p>""", """<p class="lead">The Builder works out everything from it.</p>""", 'onb')
rep("""So friends in them can find you, and your planner fills in.""", """So friends in them can find you, and the Builder fills in.""", 'onb2')
rep("""planner: ['schedTabGo', 'planner'],""", """planner: ['schedTabGo', 'planner'], builder: ['schedTabGo', 'planner'],""", 'goto')
rep("""t: 'Three versions of your next term. TermChamp starts A as your best fit, B as a backup — the same classes in other sections — and C with more classes your friends take. Change any of them.""",
    """t: 'Three versions of your next term, built in Schedule › Builder. All three aim for the same thing — the classes your degree needs, with the best professors and your friends — in different sections or classes, so if one fills up or a friend is in another section you can switch. Change any of them.""", 'help plans')

# --- the tabs: Plan A · Plan B · Plan C
rep("""const PL_NAME = { A: 'Best fit', B: 'Backup', C: 'Friends' };""", """const PL_NAME = { A: 'Plan A', B: 'Plan B', C: 'Plan C' };""", 'names')
rep(""">${x} · ${PL_NAME[x]}</button>""", """>${PL_NAME[x]}</button>""", 'tab words')

# --- drafting: one goal, three different combinations
rep("""function planDraft(R, mode, L, keep) {
  keep = (keep || []).filter(Boolean);
  const target = plUnitsTarget(), cap = plClassCap();
  const list = (mode === 'C' ? planRank(L, { friendsX: 2.5 }) : R).all.slice();
  if (mode !== 'C') list.sort((a, b) => (b.onTerm ? 1 : 0) - (a.onTerm ? 1 : 0) || b.wscore - a.wscore || b.score - a.score || a.code.localeCompare(b.code));""",
    """/* (2026-10-11, the Builder) A section for a draft: none that clashes with the plan so far; ranked by its professor and the
   friends in it (by your priorities), never a full one once registration is open if another fits; a section an earlier
   plan already uses only when no other fits — so B and C give you somewhere to switch to. */
function plDraftSec(code, have, used) {
  const W = plWeights(), ss = secsOf(code).filter(s => s && s.id && SEC[s.id] && !(have || []).some(t => secClash(s, t)));
  if (!ss.length) return null;
  const sc = s => (regOpen() ? (s.status === 'full' ? -8 : s.status === 'wait' ? -2 : 0) : 0) + ((ratingOf(s.prof) == null ? 3 : ratingOf(s.prof)) - 3) * 2 * W.professors + friendsInSec(s.id).length * 1.5 * W.friends;
  const fresh = ss.filter(s => !(used || new Set()).has(String(s.id)) && !(regOpen() && s.status === 'full'));
  return (fresh.length ? fresh : ss).slice().sort((a, b) => sc(b) - sc(a) || String(a.id).localeCompare(String(b.id)))[0];
}
/* `prev`: the plans drafted before this one (A for B; A and B for C) — what this one should differ from */
function planDraft(R, mode, L, keep, prev) {
  keep = (keep || []).filter(Boolean);
  const target = plUnitsTarget(), cap = plClassCap();
  const used = new Set(), usedN = {};
  (prev || []).forEach(ids => (ids || []).forEach(id => { const s = SEC[id]; if (!s) return; used.add(String(id)); usedN[s.code] = (usedN[s.code] || 0) + 1; }));
  /* the same goal for every plan; a pick an earlier plan already has is ranked a little lower (a near-equal class can step in) */
  const adj = c => c.wscore * (1 - 0.12 * (usedN[c.code] || 0));
  const list = R.all.slice();
  list.sort((a, b) => (b.onTerm ? 1 : 0) - (a.onTerm ? 1 : 0) || adj(b) - adj(a) || b.score - a.score || a.code.localeCompare(b.code));""", 'draft head')
rep("""    const sec = plBestSec(c.code, chosen.map(x => x.sec).concat(reg.filter(x => !x.noTime && !x.async)), true); if (!sec) continue;""",
    """    const sec = plDraftSec(c.code, chosen.map(x => x.sec).concat(reg.filter(x => !x.noTime && !x.async)), used); if (!sec) continue;""", 'draft sec')
rep("""  const ids = k === 'B' ? planDraftB((TC.plans.A || []).length ? TC.plans.A.slice() : planDraft(R, 'A', L).ids, keep) : planDraft(R, k, L, keep).ids;""",
    """  /* A is the best combination; B differs from A, C from A and B — the same goal each time */
  const prev = AT_PLANS.slice(0, AT_PLANS.indexOf(k)).map(x => (TC.plans[x] || []).map(String));
  const ids = planDraft(R, k, L, keep, prev).ids;""", 'draft slot')

# --- the card: recommended classes, no schedule look
rep("""  const timed = secs.filter(plOnWeek), any = secs.filter(s => !plOnWeek(s));
  /* the week: Mon–Fri over the hours the plan uses (at least four), each class a labelled block */
  let week = '';
  if (timed.length) {""", """  const timed = secs.filter(plOnWeek), any = secs.filter(s => !plOnWeek(s));
  /* (2026-10-11, the Builder) no week grid here — Plans shows the schedule; the Builder lists what it recommends */
  let week = '';
  if (false) {""", 'no week')
rep("""  const tray = trayItems.length ? `<div class="pla-any">""", """  const tray = false ? `<div class="pla-any">""", 'no tray')
rep("""    return `<button class="pl-row" data-a="secSheet" data-x="${esc(x.code)}" data-y="${esc(x.id)}"><span class="code pla-code">${esc(x.code)}</span><span class="pl-t"><span class="pl-n">${esc(courseName(x.code) || course(x.code).title)}</span><span class="pl-m">${x.async ? 'Online · anytime' : x.s == null ? 'Time not posted' : `${daysLabel(x.days)} ${hs(x.s)}`}${ge ? ` · GE ${esc(ge.ge)}` : ''}${regOpen() ? ' · ' + secSeatText(x) : ''}</span></span>${right}</button>`;""",
    """    const why = c ? pickReason(c) : null, fr = friendsInSec(x.id);
    return `<button class="pl-row" data-a="secSheet" data-x="${esc(x.code)}" data-y="${esc(x.id)}"><span class="code pla-code">${esc(x.code)}</span><span class="pl-t"><span class="pl-n">${esc(courseName(x.code) || course(x.code).title)}</span><span class="pl-m">${x.async ? 'Online · anytime' : x.s == null ? 'Time not posted' : `${daysLabel(x.days)} ${hs(x.s)}`}${ge ? ` · GE ${esc(ge.ge)}` : ''}${regOpen() ? ' · ' + secSeatText(x) : ''}</span>${why && why.t !== 'Pick' ? `<span class="pl-why"><span class="pk-tag ${why.k}">${esc(why.t)}</span>${fr.length ? `<span class="pl-fr">${avStack(fr, 20)}</span>` : ''}</span>` : fr.length ? `<span class="pl-why"><span class="pl-fr">${avStack(fr, 20)}</span></span>` : ''}</span>${right}</button>`;""", 'row why')
rep("""  return `<div class="card pl-card pla plan-${k}">${head}${week || tray ? `<div>${week}${tray}</div>` : ''}<div class="pl-rows">${rows}</div>""",
    """  const sum = [planUnitsChip(st), st.avg != null ? `★ ${st.avg.toFixed(1)} professors` : '', st.friends ? `${st.friends} friend${st.friends === 1 ? '' : 's'} in your sections` : ''].filter(Boolean).join(' · ');
  return `<div class="card pl-card pla plan-${k}">${head}<div class="pl-rech">Recommended for Plan ${k}</div><div class="pl-recs">${esc(sum)}</div>${k !== 'A' && (TC.plans.A || []).length && sameIds((TC.plans[k] || []).map(String), TC.plans.A.map(String)) ? `<div class="pl-same">Same as Plan A — these classes have no other section that fits.</div>` : ''}<div class="pl-rows">${rows}</div>""", 'card head')
rep(""".pl-term{""", """.pl-rech{font-size:17px;font-weight:900;margin:12px 0 2px}.pl-recs{font-size:13px;font-weight:800;color:var(--muted);margin-bottom:6px}
.pl-same{font-size:13px;font-weight:800;color:var(--ink4);background:var(--bg);border-radius:10px;padding:8px 10px;margin:4px 0 6px}
.pl-why{display:flex;align-items:center;gap:6px;margin-top:4px}.pl-why .pk-tag{font-size:11px}
.pl-term{""", 'css')
open(PA, 'w', encoding='utf-8').write(S); print('builder: done')
