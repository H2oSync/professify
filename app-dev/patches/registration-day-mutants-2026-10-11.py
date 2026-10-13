#!/usr/bin/env python3
"""Mutants for registration-day-2026-10-11.py. Usage: python3 registration-day-mutants-2026-10-11.py <repo>"""
import sys, pathlib, json
root = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else '.')
f = root / 'app-dev' / 'tests' / 'mutate.mjs'
s = f.read_text()
if '/* reg-day (2026-10-11) */' in s:
    sys.exit('already patched')
R, St = 'registrationDay', 'registrationDayStates'
NEW = [
  ["regday: your day never shows", "  if (m) {\n    const n = regGap(today, m.day), t = regTimeText(m.time);", "  if (false) {\n    const n = regGap(today, m.day), t = regTimeText(m.time);", R],
  ["regday: a day off in the countdown", "· in ${n} days`;", "· in ${n + 1} days`;", R],
  ["regday: tomorrow never says tomorrow", "else if (n === 1) txt = `You register tomorrow", "else if (n === 0) txt = `You register tomorrow", St],
  ["regday: minutes not cut to the hour", "${left % 60}m`", "${left}m`", St],
  ["regday: opened never says so", "left > 0 ? `You register today at", "left > -9999 ? `You register today at", St],
  ["regday: a day that's over keeps counting", "m = mine && mine.day >= today ? mine : null;", "m = mine;", St],
  ["regday: after your day the amber line comes back", "} else if (!mine && today <= regEnd()) {", "} else if (today <= regEnd() && !(mine && mine.day >= today)) {", St],
  ["regday: after Round 1 the amber line stays", "} else if (!mine && today <= regEnd()) {", "} else if (!mine) {", St],
  ["regday: someone you blocked is counted", "!isBlocked(x.id) && PEOPLE[x.id]).sort(", "PEOPLE[x.id]).sort(", R],
  ["regday: a stranger is counted", "F.rows.filter(x => TC.friends.includes(x.id) && ", "F.rows.filter(x => ", R],
  ["regday: a friend twice counts twice", "!seen.has(x.user_id) && seen.add(x.user_id)", "true", R],
  ["regday: a nonsense day is kept", "x.user_id && regDayOk(x.day) && !seen", "x.user_id && !seen", R],
  ["regday: the list isn't by day", "list.map(row).join('')", "list.slice().reverse().map(row).join('')", R],
  ["regday: same day counted as before", "up.filter(x => x.day < m.day).length, 'before you']", "up.filter(x => x.day <= m.day).length, 'before you']", R],
  ["regday: before and after swapped", "d < 0 ? regPlural(-d, 'day') + ' before you'", "d > 0 ? regPlural(d, 'day') + ' before you'", R],
  ["regday: friends who added theirs miscounted", "`${regPlural(up.length, 'friend')} added their day`", "`${regPlural(up.length + 1, 'friend')} added their day`", R],
  ["regday: upsert on the wrong key", "{ onConflict: 'user_id,term' }", "{ onConflict: 'user_id' }", R],
  ["regday: sharing off isn't saved", "shared: !!v.shared, updated_at", "shared: true, updated_at", R],
  ["regday: saved under the term in session", "term: CFG.REGISTRATION_TERM_CODE, day: v.day", "term: CFG.NOW_TERM, day: v.day", R],
  ["regday: remove deletes every term", ".delete().eq('user_id', TC.user.id).eq('term', CFG.REGISTRATION_TERM_CODE)", ".delete().eq('user_id', TC.user.id)", R],
  ["regday: sharing off by default", "shared: m ? m.shared !== false : true };", "shared: m ? m.shared !== false : false };", R],
  ["regday: picking a day loses the time typed", "regReadTime(sh); sh.day = d; sh.err = null;", "sh.day = d; sh.err = null;", R],
  ["regday: a day that's over can be picked", "!regRoundDays().includes(d) || d < sloISO()) return;", "!regRoundDays().includes(d)) return;", St],
  ["regday: a day kept on the phone never goes up", "if (loc && loc.pending && (!row", "if (false && loc && loc.pending && (!row", St],
  ["regday: the phone's older day beats the server's", "|| Date.parse(row.updated_at) < (+loc.at || 0)))", "|| true))", St],
  ["regday: a refused save says nothing", "    const say = dbSay(q.error, 'Couldn’t save that — it’s kept on this phone for now.');", "    const say = null;", St],
  ["regday: a failed list has no Try again", "data-a=\"regDaysRetry\"", "data-a=\"back\"", St],
  ["regday: no row on a friend's page", "friendBubbles(p) + regFriendRow(id) + fofRow(id)", "friendBubbles(p) + fofRow(id)", R],
  ["regday: a name isn't escaped", "${me ? 'You' : esc(PEOPLE[x.id].name)}", "${me ? 'You' : PEOPLE[x.id].name}", R],
  ["regday: shown while planning another term", "const regWhen = () => !!TC.user && CFG.TERM_LABEL === CFG.REGISTRATION_TERM && ", "const regWhen = () => !!TC.user && ", St],
  ["regday: the amber line's spoken name doesn't start with what it shows", "aria-label=\"${esc(txt)} · Add your day${n > 0 ? `. Registration opens ${regOpensText()}` : ''}\"", "aria-label=\"Add your registration day. ${esc(txt)}\"", R],
  ["regday: friends line too faint", "background:none;color:var(--ink3);font:inherit;font-size:13px;font-weight:800;", "background:none;color:var(--muted2);font:inherit;font-size:13px;font-weight:800;", R],
  ["regday: the line under 44px", "button.pla-reg{width:calc(100% - 32px);min-height:44px;", "button.pla-reg{width:calc(100% - 32px);min-height:30px;", R],
  ["regday: 1 friend haven't", "${missing === 1 ? 'hasn’t' : 'haven’t'}", "haven’t", R],
  ["regday: the phone's copy stays pending", "  regKeep(v, false); return null;\n}", "  return null;\n}", R],
  ["regday: friends not asked again after a save", "render(true); loadRegFriends(true);\n  },", "render(true);\n  },", R],
  ["regday: a load that lands after a save undoes it", "  if (TC.regGen !== gen) return;   /* a save while this was in flight: that one stands */\n", "", St],
  ["regday: back online, nothing retried", "window.addEventListener('online', () => { regRetry(); });", "", St],
  ["regday: a typed time lost on a redraw", "if (t && t.id === 'rd-time' && UI.sheet && UI.sheet.type === 'regDay') UI.sheet.time", "if (false) UI.sheet.time", R],
  ["regday: a failed Remove says it's kept", "return !v || !v.shared ? 'Not done yet — friends can still see your day until it goes through. It’ll try again when you’re back online.' : say;", "return say;", St],
  ["regday: a failed unshare says it's kept", "return !v || !v.shared ? 'Not done yet", "return !v ? 'Not done yet", St],
  ["regday: the switch's tap area gone", ".rd-row .toggle::after{content:'';position:absolute;left:-6px;right:-6px;top:-6px;bottom:-6px}", "", R],
  ["regday: the tiles back", "<div class=\"card pl-card pla plan-${k}\">${head}${week || tray ?", "<div class=\"card pl-card pla plan-${k}\">${head}<div class=\"pla-stats\"><div class=\"pla-stat\"><span>Classes</span><b>${st.n}</b></div></div>${week || tray ?", R],
]
# the tiles' 320px mutant has nothing left to break (Tate took the tiles out)
old = '  ["card A: Professors spills at 320px", ".pla-stat .pla-wide{display:none}.pla-stat .pla-narrow{display:inline}", "", "springCardA"],\n'
assert s.count(old) == 1
s = s.replace(old, '')
# older mutants whose code this change moved: re-aimed at where it is now, or retired where the promise changed
REAIM = {
  "reg: the registration line for any term": ["reg: the registration line for any term", "const regWhen = () => !!TC.user && CFG.TERM_LABEL === CFG.REGISTRATION_TERM && ", "const regWhen = () => !!TC.user && ", "plannerRegOpen"],
  "reg: the registration line stays once it opens": None,   # by design now: "Registration is open · Add your day" until Round 1 ends
  "delete: the report, the answers and the drafts stay on the phone": ["delete: the report, the answers and the drafts stay on the phone", ", AUDIT_KEY(), PREFS_KEY(), PLDRAFT_KEY(), plSkipKey(), MARKS_KEY(), REG_KEY()].forEach", ", MARKS_KEY(), REG_KEY()].forEach", "deleteAccount"],
  "marks: delete account keeps them on the phone": ["marks: delete account keeps them on the phone", "plSkipKey(), MARKS_KEY(), REG_KEY()]", "plSkipKey(), REG_KEY()]", "deleteAccount"],
  "no major on a friend's page": ["no major on a friend's page", "  ${isF && !bl ? friendBubbles(p) + regFriendRow(id) + fofRow(id) : ''}\n  <div class=\"fact\">", "  ${isF && !bl ? regFriendRow(id) + fofRow(id) : ''}\n  <div class=\"fact\">", "friendMajor"],
  "requester sees a major": ["requester sees a major", "  ${isF && !bl ? friendBubbles(p) + regFriendRow(id) + fofRow(id) : ''}\n  <div class=\"fact\">", "  ${friendBubbles(p)}${isF && !bl ? regFriendRow(id) + fofRow(id) : ''}\n  <div class=\"fact\">", "friendMajor"],
  "card A: no tiles": None,   # the tiles are gone (Tate, 2026-10-11); "regday: the tiles back" guards that
  "fof: no row on a friend's page": ["fof: no row on a friend's page", "+ regFriendRow(id) + fofRow(id) : ''}", "+ regFriendRow(id) : ''}", "friendsOfFriend"],
  "fof: asked on a stranger's page": ["fof: asked on a stranger's page", "if (TC.user && TC.friends.includes(id)) { loadFof(id); loadRegFriends(); }", "if (TC.user) { loadFof(id); loadRegFriends(); }", "friendsOfFriend"],
}
lines = s.split('\n')
for k, v in REAIM.items():
    hit = [n for n, l in enumerate(lines) if l is not None and l.startswith('  [' + json.dumps(k, ensure_ascii=False) + ',')]
    assert len(hit) == 1, (k, len(hit))
    if v is None: lines[hit[0]] = None
    else: lines[hit[0]] = '  ' + json.dumps(v, ensure_ascii=False) + ','
s = '\n'.join(l for l in lines if l is not None)
i = s.index('const M = ['); j = s.index('\n];\n', i)
s = s[:j + 1] + '  /* reg-day (2026-10-11) */\n' + ''.join('  ' + json.dumps(m, ensure_ascii=False) + ',\n' for m in NEW) + s[j + 1:]
f.write_text(s)
print('patched', f)
