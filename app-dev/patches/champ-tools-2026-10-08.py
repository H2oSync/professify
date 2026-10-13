#!/usr/bin/env python3
"""Champ gets its own menu (Tate, 2026-10-08: "its not really understanding questions properly").

Run after champ-cards-2026-10-08.py. Edits app/index.html only.

What went wrong in Tate's screenshots: "Who's free right now?" was answered with HIS free week and
"best professor for BUS 3431" with his own professors. The model picked the closest tool on a menu
that had no right one. The ask function now gives the phone its own menu when the phone says
`client: 'app'` (supabase/functions/ask/shared.ts, APP_TOOLS) with four more tools; this patch:

  1. sends client: 'app' with every question;
  2. answers the four new tools with the cards that already exist —
       friends_free_now  → who's free now (the 'now' card)
       free_with_friends → free together on a day, or with ONE friend (a day, or their whole week)
       best_professor    → the top professor's card, then the others
       fits_plan         → the plan's week with the class dashed in;
  3. opens the phone's own screens for every place on the phone's go_to menu (settings, appearance,
     my reviews, the legal pages, the ledger, my QR code), so no menu place answers "couldn't find";
  4. the local reader (chIntent) answers "who's free (right now)?" itself; a named friend's free time
     with you; "mwf" / "tth" as days; never "friends free when I'm free" as the student alone; and reads
     curly apostrophes ("Who’s", as the help chip writes it);
  5. "watch professor X" says the phone's alerts are for sections and shows the professor.
"""
import pathlib, sys

ROOT = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else '.')
P = ROOT / 'app' / 'index.html'
s = P.read_text()


def rep(a, b, n=1):
    global s
    c = s.count(a)
    if c != n:
        sys.exit(f'champ-tools: expected {n} of {a[:90]!r}, found {c}')
    s = s.replace(a, b)


# 1. the phone says it is the phone
rep("""body: JSON.stringify(Object.assign({ q, term: CFG.TERM, who }, nolog ? { nolog: true } : {}))""",
    """body: JSON.stringify(Object.assign({ q, term: CFG.TERM, who, client: 'app' }, nolog ? { nolog: true } : {}))""")

# 3. every place on the phone's go_to menu opens a phone screen
rep("""account: ['sheet', 'profile'], 'edit profile': ['sheet', 'profile'], settings: ['sheet', 'profile'] };""",
    """account: ['sheet', 'profile'], 'edit profile': ['sheet', 'profile'], settings: ['sheet', 'profile'],
  /* 2026-10-08: the rest of the phone's go_to menu (APP_PLACES in the ask function) */
  ledger: ['schedTabGo', 'past'], 'my qr code': ['sheet', 'invite'], appearance: ['openSettings', ''], 'privacy settings': ['openSettings', ''],
  about: ['openSettings', ''], 'my reviews': ['openMyRatings', ''], 'privacy policy': ['openLegal', 'privacy'], terms: ['openLegal', 'terms'],
  'community guidelines': ['openLegal', 'guidelines'], security: ['openLegal', 'security'] };""")

# 2. the four new tools, answered with the cards
rep("""    case 'my_day': { const d = a.rel === 'tomorrow'""",
    """    /* the phone's own four (2026-10-08) */
    case 'friends_free_now': return ansNow();
    case 'free_with_friends': {
      const today = DAYS.includes(CLOCK.day) ? CLOCK.day : 'M', ds = (a.days || []).map(x => HDAY[x]).filter(x => DAYS.includes(x));
      const d = a.rel === 'today' ? today : a.rel === 'tomorrow' ? (DAYS[(DAYS.indexOf(CLOCK.day) + 1) % 5] || 'M') : ds[0] || null;
      if (a.friend) { const f = findFriend(a.friend); return !f ? { t: `I couldn’t find one friend named ${esc(a.friend)}.`, acts: [['Open Friends', 'fFilterGo', 'people']] }
        : !d && CH_NOWQ.test(String(q || '').toLowerCase().replace(/[’‘]/g, "'")) ? ansFriendNow(f) : ansTogetherWith(f, d); }
      return ansTogether(d || chDayOf(String(q || '').toLowerCase()));
    }
    case 'best_professor': { const c = cc(a.course); return c ? ansBest(c) : null; }
    case 'fits_plan': { const c = cc(a.course); return c ? ansFit(c, a.plan === 'mine' || AT_PLANS.includes(a.plan) ? a.plan : S.plan) : null; }
    case 'my_day': { const d = a.rel === 'tomorrow'""")

# free together with ONE friend: a day, or their week
rep("""function chTogetherCard(c) {
  const l = chTogether(c.d).slice(0, 6); if (!l.length) return '';""",
    """/* With one friend (2026-10-08): "when are Maya and I both free" — a day, or the week a day a row. */
function ansTogetherWith(f, d) {
  const nm = esc(PEOPLE[f].short);
  if (!personSecs('me').some(chTimed)) return { t: `None of your ${esc(CFG.TERM_LABEL)} classes have set times yet, so I can’t match your free time with ${nm}’s.`, acts: [['Open Schedule', 'tab', 'schedule']] };
  if (!personSecs(f).some(chTimed)) return { t: `None of ${nm}’s ${esc(CFG.TERM_LABEL)} classes have set times, so I can’t match your free time.`, acts: [['Open ' + PEOPLE[f].short, 'openFriend', f]] };
  if (d) {
    const x = chTogether(d).find(y => y.f === f);
    return x ? { t: `You and ${nm} are both free ${hs(x.best[0])}–${hs(x.best[1])} on ${DAYL[d]}${x.both.length > 1 ? `, and ${x.both.length - 1} more time${x.both.length > 2 ? 's' : ''}` : ''}.`, card: { k: 'together', d, f } }
      : { t: `You and ${nm} aren’t free at the same time on ${DAYL[d]} between ${hs(CH_S0)} and ${hs(CH_DAY_END)}. Here’s the week:`, card: { k: 'togetherWk', f } };
  }
  const n = DAYS.filter(dd => chTogether(dd).some(y => y.f === f)).length;
  return { t: n ? `You and ${nm} are both free on ${n} of 5 days.` : `You and ${nm} aren’t free at the same time on any weekday between ${hs(CH_S0)} and ${hs(CH_DAY_END)}.`, card: { k: 'togetherWk', f } };
}
/* "is Sky free (right now)?" — that friend, now: the same words as their ring and status everywhere else. */
const CH_NOWQ = /\\b(now|rn|right now|currently|at the moment)\\b|^(is|are) [a-z][a-z'-]* free\\??$/;
function ansFriendNow(f) {
  const st = status(f), sh = PEOPLE[f].short;
  return { t: `${esc(sh)}: ${esc(st.t)}.`, acts: [['Message ' + sh, 'openChatWith', f], ['Open ' + sh, 'openFriend', f]] };
}
function chTogetherWk(c) {
  const f = c.f; if (!PEOPLE[f] || !TC.friends.includes(f)) return '';
  const rows = DAYS.map(d => { const x = chTogether(d).find(y => y.f === f);
    return `<div class="chw-row"><span class="chw-d">${DAYN[d]}</span><span class="chw-m"><span class="chw-t${x ? ' chtw-ok' : ''}">${x ? `Free together ${hs(x.best[0])}–${hs(x.best[1])} · ${chLen(x.best[1] - x.best[0])}${x.both.length > 1 ? ` · +${x.both.length - 1} more` : ''}` : 'Not free at the same time'}</span></span></div>`; }).join('');
  return `<section class="chc chrows" aria-label="${esc('Free with ' + PEOPLE[f].short)}"><div class="chpp free"><div class="chpp-top"><button class="chpp-main" data-a="openFriend" data-x="${esc(f)}">${pav(f, 44)}<span class="grow"><b>${esc(PEOPLE[f].short)}</b><span>Free when you are, ${hs(CH_S0)}–${hs(CH_DAY_END)}</span></span></button><button class="act" data-a="openChatWith" data-x="${esc(f)}">Message</button></div></div>${rows}</section>`;
}
function chTogetherCard(c) {
  const l = chTogether(c.d).filter(x => !c.f || x.f === c.f).slice(0, 6); if (!l.length) return '';""")

rep("""const CH_CARDS = { fit: chFit, day: chDay, week: chWeek, together: chTogetherCard, now: chNow,""",
    """const CH_CARDS = { fit: chFit, day: chDay, week: chWeek, together: chTogetherCard, togetherWk: chTogetherWk, now: chNow,""")

rep(""".chw-ax{display:flex;justify-content:space-between;padding:2px 26px 0 44px;font-size:10.5px;font-weight:800;color:var(--muted)}""",
    """.chw-ax{display:flex;justify-content:space-between;padding:2px 26px 0 44px;font-size:10.5px;font-weight:800;color:var(--muted)}
.chw-t.chtw-ok{color:var(--ink);font-weight:900}""")

# 4. the local reader: "who's free (right now)?" on the phone; a named friend ("when are Maya and I both free") is
#    that friend's free time with you (or the model, when no friend has that name); "mwf" / "tth" are days; "friends
#    free when I'm free" is not the student alone; curly apostrophes read as straight ones. Found by the golden test
#    (champGolden): each of these gave a different answer from the right tool.
rep("""const chDaysIn = t => [...String(t).matchAll(CH_DAYW)].map(m => ({ mon: 'M', tue: 'T', wed: 'W', thu: 'R', fri: 'F' })[m[1].slice(0, 3)]);""",
    """const CH_DAYC = /\\b(mtwrf|mwf|mw|tth|tuth|tr)\\b/g, CH_DAYCM = { mtwrf: 'MTWRF', mwf: 'MWF', mw: 'MW', tth: 'TR', tuth: 'TR', tr: 'TR' };
const chDaysIn = t => { const s = String(t), out = [];
  [...s.matchAll(CH_DAYW)].forEach(m => out.push([m.index, ({ mon: 'M', tue: 'T', wed: 'W', thu: 'R', fri: 'F' })[m[1].slice(0, 3)]]));
  [...s.matchAll(CH_DAYC)].forEach(m => [...CH_DAYCM[m[1]]].forEach(d => out.push([m.index, d])));
  return out.sort((a, b) => a[0] - b[0]).map(x => x[1]); };
/* A time that isn't now, today or a weekday ("at noon", "tonight", "after class", "this weekend", "when I'm free"):
   the phone's free-time answers can't say that, so the model gets it. */
const CH_LATERQ = /\\d|\\b(when i'?m free|when i am|at|after|before|around|between|until|till|tonight|later|noon|morning|afternoon|evening|night|weekend|next|sat(urday)?|sun(day)?)\\b/;
const chLater = t => CH_LATERQ.test(t.replace(/\\bat the moment\\b/g, ''));
/* A person the question names, in the shapes "Maya and I", "me and Maya", "with Maya", "is Maya free". */
const CH_NOTNAME = /^(me|my|i|im|you|u|anyone|anybody|someone|somebody|friends?|everyone|everybody|them|him|her|us|a|an|the|class|classes|lunch|food|today|tomorrow|now|people|good|open|seats)$/;
function chNamed(t) {
  for (const p of [/\\b([a-z][a-z'-]+) and (?:i|me)\\b/, /\\b(?:me|i) and ([a-z][a-z'-]+)/, /\\bwith ([a-z][a-z'-]+)/, /\\b(?:is|when is|when's) ([a-z][a-z'-]+) free\\b/]) {
    const m = t.match(p), w = m && m[1].replace(/'s$/, '');
    if (w && !CH_NOTNAME.test(w) && !chDaysIn(w).length) return w;
  }
  return null;
}""")
rep("""  const named = t.replace(CH_CODE, ' ').replace(/[^a-z\\s'-]/g, ' ').split(/\\s+/).filter(w => w.length > 3 && !/^(best|professors?|teachers?|instructors?|which|should|easiest|highest|better|good|class|section|rated|rating|for|the)$/.test(w)).some(w => findProfKey(w));
  if (code && !named && /\\b(best|top|highest|good|better|which|who should|easiest)\\b[\\s\\S]*\\b(prof|profs|professor|professors|teacher|teachers|instructor)\\b|\\b(prof|professor|teacher)s?\\b[\\s\\S]*\\b(best|top|good)\\b/.test(t)) return ansBest(code);""",
    """  /* a named professor (3-letter surnames too: "is Lee good for BUS 3431") is the model's — professor_stats */
  const named = t.replace(CH_CODE, ' ').replace(/[^a-z\\s'-]/g, ' ').split(/\\s+/).filter(w => w.length > 2 && !/^(best|professors?|teachers?|instructors?|which|should|easiest|highest|better|good|class|section|rated|rating|for|the|who|and|can|get|bus|fit|any|are|how|why|one|two|day|you|her|his|our|top|was|has|had|not|but|all|out|its|did|see|new|way|use|now)$/.test(w)).some(w => findProfKey(w));
  if (code && !named && /\\b(best|top|highest|good|better|which|who should)\\b[\\s\\S]*\\b(prof|profs|professor|professors|teacher|teachers|instructor)\\b|\\b(prof|professor|teacher)s?\\b[\\s\\S]*\\b(best|top|good)\\b/.test(t)) return ansBest(code);""")
rep("""function chIntent(q) {
  const t = String(q || '').toLowerCase(), m = t.match(CH_CODE)""",
    """function chIntent(q) {
  const t = String(q || '').toLowerCase().replace(/[’‘]/g, "'"), m = t.match(CH_CODE)""")
rep("""  if (/\\bfree\\b[\\s\\S]*\\b(with me|same time|as me|together)\\b|\\bboth free\\b|\\bfree together\\b/.test(t)) return ansTogether(chDayOf(t));""",
    """  /* one named friend and free time: theirs and yours; a name that isn't one friend goes to the model */
  const nm = !code && chNamed(t);
  if (nm && /\\b(free|overlap|gap|break|lunch|meet up|hang out)\\b/.test(t)) {
    const f = findFriend(nm), ds = [...new Set(chDaysIn(t))];
    if (!f || ds.length > 1 || chLater(t)) return null;
    if (!ds.length && CH_NOWQ.test(t)) return ansFriendNow(f);
    return ansTogetherWith(f, ds.length || /\\b(today|tomorrow)\\b/.test(t) ? chDayOf(t) : null);
  }
  if (/\\bfree\\b[\\s\\S]*\\b(with me|same time|as me|together)\\b|\\bboth free\\b|\\bfree together\\b/.test(t)) return ansTogether(chDayOf(t));
  /* "who's free?" is about friends (2026-10-08). A day → free when you are that day; otherwise right now. A time
     ("who's free at 3") or a person goes to the model. */
  if (/^(so |ok |okay |hey |yo )?(who'?s|who is|who are|is anyone|anyone|is anybody|anybody|are any of my friends|any friends|which friends are|which of my friends are)( (even|actually|currently))? free\\b/.test(t) && !/\\d|\\bwith\\b|\\band (i|me)\\b/.test(t) && !chLater(t)) {
    const ds = chDaysIn(t);
    return ds.length || /\\b(today|tomorrow)\\b/.test(t) ? ansTogether(chDayOf(t)) : ansNow();
  }""")
rep("""  if (/\\b(when am i free|when i'?m free|my free time|am i free|free time)\\b/.test(t) && !/\\bright now\\b/.test(t)) {""",
    """  if (/\\b(when am i free|when i'?m free|my free time|am i free|free time)\\b/.test(t) && !/\\bright now\\b/.test(t) && !/\\b(friends?|anyone|anybody|who'?s?|someone)( are| is)? free\\b/.test(t)) {""")

# 5. "watch professor X": the phone's alerts are for sections, so say so and show them (the golden test found no answer)
rep("""    case 'watch': { const c = cc(a.course);""",
    """    case 'watch': { if (a.kind === 'professor') { const pk = findProfKey(a.name); return pk ? { t: `Seat alerts on the phone are for sections — here’s ${esc(profName(pk))}. Open a class they teach and watch a section.`, card: { k: 'prof', pk } } : { t: 'I couldn’t find that professor.' }; }
      const c = cc(a.course);""")

P.write_text(s)
print('champ-tools-2026-10-08: ok')
