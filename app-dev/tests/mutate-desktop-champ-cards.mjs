/* mutate-desktop-champ-cards — each mutant plants one bug in hawk-ask.js / hawk-ask.css that breaks a promise of Champ's chat and
   cards (website-champ-cards, 2026-10-15); check-desktop-champ-cards must FAIL on every one.
   Run: SRC_DIR=<repo> node mutate-desktop-champ-cards.mjs     (MUT_ONLY="part of a name|another"; MUT_DRY=1 only checks the anchors;
   APP_PORT to move off 8190) */
import fs from 'fs'; import path from 'path'; import os from 'os'; import { execFileSync } from 'child_process';
const SRC = process.env.SRC_DIR || path.resolve('../..');
/* [name, file, anchor (must occur once), replacement, the check-desktop-champ-cards test that has to notice] */
const M = [
  // ---- the term: free time is the week you are IN, plans are the term you are choosing in
  ['free time reads the planning list (the bug: "I don\'t have any classes saved for you yet")', 'hawk-ask.js', "  function nowMeetsAll() {\n", "  function nowMeetsAll() {\n    return planBase('mine').map(function (m) { return { code: m.code, meet: m.meet }; });\n", 'week'],
  ['fit my schedule reads the Fall classes', 'hawk-ask.js', "(has('myClassMeets') ? global.myClassMeets(myClasses || [], myClassMeta || {}) : [])", "(has('myClassMeets') ? global.myClassMeets(nowMine().classes, nowMine().meta) : [])", 'planning term'],
  ['"who is free with me" ignores my own classes', 'hawk-ask.js', "var myGaps = gapsIn(dayItems(nowMeetsAll(), d), DAY_S0, TOGETHER_END)", "var myGaps = gapsIn(dayItems([], d), DAY_S0, TOGETHER_END)", 'together'],
  ['a Fall class opens its Spring page', 'hawk-ask.js', "        global.cpNow = true;\n", "        global.cpNow = false;\n", 'week'],
  // ---- the week and the day
  ['the week card says something else', 'hawk-ask.js', "'Your free time, day by day. Tap a day to see it.'", "'Here is your week.'", 'week'],
  ['tapping a day asks the next day', 'hawk-ask.js', "row.addEventListener('click', function () { answer('When am I free ' + DAY_FULL[d] + '?'); });", "row.addEventListener('click', function () { answer('When am I free ' + DAY_FULL[nextDay(d)] + '?'); });", 'week'],
  ['a class with no meeting time is silently dropped', 'hawk-ask.js', "    return u.length ? ['Not counted — no meeting time on ' + u.join(', ') + '.'] : [];", "    return [];", 'week'],
  ['a bare day name is not understood', 'hawk-ask.js', "&& daysIn(t).length === 1 && !(lastSearch", "&& false && !(lastSearch", 'ai first'],
  ['"next" is read from the wrong end of the day', 'hawk-ask.js', "next = today && l.filter(function (s) { return s.s > nm; })[0]", "next = today && l.filter(function (s) { return s.s > nm; }).pop()", 'day'],
  ['the free stretches vanish from the day card', 'hawk-ask.js', "    gapsIn(l, a, b).forEach(function (g) {\n      var open = g[1] >= b && l.length", "    [].forEach(function (g) {\n      var open = g[1] >= b && l.length", 'week'],
  ['an empty week still draws a card', 'hawk-ask.js', "    var meets = nowMeetsAll(); if (!meets.length) return emptyWeek();\n    var ds =", "    var meets = nowMeetsAll();\n    var ds =", 'the student with'],
  // ---- AI first: every question asks the function first; the device is only the fallback
  ['a lookup is answered on the device without asking (the cards patch\'s old order)', 'hawk-ask.js', "var toModel = near ? true : !(skipsModel(result) || !result.in_scope);", "var toModel = near ? false : !(skipsModel(result) || !result.in_scope);", 'ai first'],
  ['the device\'s reading is dropped when the function fails', 'hawk-ask.js', "    var device = near || result;\n", "    var device = result;\n", 'ai first'],
  ['a model that cannot answer beats the device\'s clean reading', 'hawk-ask.js', "render(q, pickAnswer(viaModel, device), cat, thinking);", "render(q, viaModel || device, cat, thinking);", 'ai first'],
  ['a follow-up that narrows the last search is sent to the model', 'hawk-ask.js', "    if (near) fu = null;\n    if (fu) result = fu;\n", "    fu = null;\n    if (fu) result = fu;\n", 'ai first'],
  ['no question is ever sent: everything is answered on the device', 'hawk-ask.js', "if (!toModel || !aiUrl()) {", "if (true) {", 'ai first'],
  // ---- friends
  ['free together sorts the shortest first', 'hawk-ask.js', "return (q.best[1] - q.best[0]) - (p.best[1] - p.best[0]) || p.best[0] - q.best[0]; });", "return (p.best[1] - p.best[0]) - (q.best[1] - q.best[0]) || p.best[0] - q.best[0]; });", 'together'],
  ['who is free now counts the busy as free', 'hawk-ask.js', "if (st.state === 'open') free++; else if (st.state === 'class') busy++;", "if (st.state === 'open' || st.state === 'class') free++; else if (st.state === 'class') busy++;", 'now'],
  ['Message opens the friend\'s page instead of a chat', 'hawk-ask.js', "top.appendChild(tap(button('hawk-act', 'Message', 'Message ' + firstName(f.name)), function () { return messageFriend(f); }));", "top.appendChild(tap(button('hawk-act', 'Message', 'Message ' + firstName(f.name)), function () { return openFriend(f); }));", 'now'],
  ['a friend row does not open the friend', 'hawk-ask.js', "    tap(main, function () { return openFriend(f); });", "    tap(main, function () { return 'Opened'; });", 'together'],
  // ---- fit
  ['"no, it clashes" says yes', 'hawk-ask.js', "return { t: 'No — every ' + code + ' section clashes with ' + L + '.',", "return { t: 'Yes — every ' + code + ' section clashes with ' + L + '.',", 'fit'],
  ['nothing ever clashes', 'hawk-ask.js', "if (x.code !== code && x.meet && overlaps(e.meet, x.meet)) out.push({ code: x.code });", "if (x.code !== code && x.meet && false) out.push({ code: x.code });", 'fit'],
  ['the add button is not the site\'s own flow', 'hawk-ask.js', "b.setAttribute('data-pl-act', 'choose'); b.setAttribute('data-code', code);", "b.setAttribute('data-pl-act', 'nothing'); b.setAttribute('data-code', code);", 'fit'],
  ['the plan chooser opens under Champ', 'hawk-ask.css', "#plChoose.pl2-choose { z-index: 9100; }", "#plChoose.pl2-choose { z-index: 100; }", 'fit'],
  ['the section would-be block is missing from the grid', 'hawk-ask.js', "    if (!inIt && s.meet) blocks.push({ code: c.code,", "    if (false && s.meet) blocks.push({ code: c.code,", 'fit'],
  ['Open › on a fit card opens Home', 'hawk-ask.js', "function () { return P === 'mine' ? goPlace('my classes') : openPlan(P); }", "function () { return goPlace('home'); }", 'fit'],
  // ---- professors, classes, search
  ['best professor sorts the worst first', 'hawk-ask.js', "return ((y.p.rating == null ? -1 : y.p.rating) - (x.p.rating == null ? -1 : x.p.rating)) || (evalsOf(y.p) - evalsOf(x.p));", "return ((x.p.rating == null ? -1 : x.p.rating) - (y.p.rating == null ? -1 : y.p.rating)) || (evalsOf(y.p) - evalsOf(x.p));", 'professors'],
  ['no "Also teaching" heading', 'hawk-ask.js', "if (big) wrap.appendChild(kicker('Also teaching ' + c.code));", "", 'professors'],
  ['a professor row does not open the professor', 'hawk-ask.js', "    return tap(b, function () { return goProfId(p.id, p.name); });\n  }\n  function cardProfs", "    return tap(b, function () { return 'Opened'; });\n  }\n  function cardProfs", 'professors'],
  ['sections show no + to add', 'hawk-ask.js', "    var add = planAddBtn(r.sec.code, r.sec.crn, 'hawk-sec__add', 'Add ' + r.code + ' to a plan');", "    var add = make('span'); add.className = 'hawk-sec__add';", 'professors'],
  ['search forgets to show the filters it understood', 'hawk-ask.js', "if (a.open_only === true) out.push('Open seats');", "", 'class and sections'],
  ['my professors rank the lowest first', 'hawk-ask.js', "return asc ? p.prof.rating - q.prof.rating : q.prof.rating - p.prof.rating; });\n    var all", "return asc ? q.prof.rating - p.prof.rating : p.prof.rating - q.prof.rating; });\n    var all", 'professors'],
  // ---- prerequisites, game plan, clashes
  ['no record: it says "yes you can" or "not yet" on nothing', 'hawk-ask.js', "if (!past && !wav && (st.state === 'unmet' || st.state === 'concurrent'))", "if (false && (st.state === 'unmet' || st.state === 'concurrent'))", 'prerequisites'],
  ['a class you are taking counts as done', 'hawk-ask.js', "else if (nw && !unknown) { ok++; dot = make('span', 'hawk-q__dot hawk-q__dot--now', '◐'); name.appendChild(make('b', '', nw)); sub = 'Taking it now'; }", "else if (nw && !unknown) { ok++; dot = make('span', 'hawk-q__dot hawk-q__dot--ok', '✓'); name.appendChild(make('b', '', nw)); sub = 'On your record'; }", 'prerequisites'],
  ['a game plan step does not open its class', 'hawk-ask.js', "sec.appendChild(tap(row, function () { return goSection(i.code, i.crn, i.label); }));", "sec.appendChild(tap(row, function () { return goPlace('home'); }));", 'game plan'],
  ['the game plan is in the wrong order', 'hawk-ask.js', "g.steps.slice(0, 8).forEach(function (st, ix) {", "g.steps.slice(0, 8).reverse().forEach(function (st, ix) {", 'game plan'],
  ['clashes are not outlined', 'hawk-ask.js', "(bad[i] ? ' hawk-wk__blk--clash' : ''), go: m.cm ? null", "'', go: m.cm ? null", 'clashes'],
  ['a clash is reported when classes only touch', 'hawk-ask.js', "if (!a.meet || !b.meet || (a.cm && b.cm) || (!a.cm && !b.cm && a.code === b.code)) continue;", "if (!a.meet || !b.meet) continue; bad[i] = 1; bad[j] = 1; continue;", 'clashes'],
  // ---- the chat
  ['the greeting does not come back after the trash can', 'hawk-ask.js', "    els.log.appendChild(hintEl());\n    stamp(); syncEmpty();", "    stamp(); syncEmpty();", 'chat'],
  ['every answer keeps its follow-ups', 'hawk-ask.js', "      if (i === all.length - 1) return;\n      Array.prototype.forEach.call(t.querySelectorAll(':scope > .hawk-follow, :scope > .hawk-notit')", "      return;\n      Array.prototype.forEach.call(t.querySelectorAll(':scope > .hawk-follow, :scope > .hawk-notit')", 'chat'],
  ['a new answer replaces the chat instead of joining it', 'hawk-ask.js', "    if (replace && replace.parentNode === els.log) els.log.replaceChild(turn, replace); else els.log.appendChild(turn);", "    if (replace && replace.parentNode === els.log) els.log.replaceChild(turn, replace); else { els.log.textContent = ''; els.log.appendChild(turn); }", 'chat'],
  ['the question bubble is on the left', 'hawk-ask.css', ".hawk-said { align-self: flex-end;", ".hawk-said { align-self: flex-start;", 'chat'],
  ['the header sub-line is the old one', 'hawk-ask.js', "'Answers from TermChamp’s real data'", "'From TermChamp’s real data'", 'chat'],
  ['the thinking line stays after the answer', 'hawk-ask.js', "render(q, pickAnswer(viaModel, device), cat, thinking);", "render(q, pickAnswer(viaModel, device), cat);", 'model path'],
  // ---- escaping
  ['a friend\'s name goes in as markup', 'hawk-ask.js', "tx.appendChild(make('b', '', firstName(f.name))); tx.appendChild(make('span', '', sub));", "var nb = make('b'); nb.innerHTML = firstName(f.name); tx.appendChild(nb); tx.appendChild(make('span', '', sub));", 'escaping'],
  ['a professor\'s name goes in as markup', 'hawk-ask.js', "var tx = make('span', 'hawk-ptop__tx'); tx.appendChild(make('b', '', p.name));", "var tx = make('span', 'hawk-ptop__tx'); var nb = make('b'); nb.innerHTML = p.name; tx.appendChild(nb);", 'escaping'],
  ['the answer line goes in as markup', 'hawk-ask.js', "    turn.appendChild(make('div', 'hawk-note', ans.t));", "    var hn = make('div', 'hawk-note'); hn.innerHTML = ans.t; turn.appendChild(hn);", 'escaping'],
  // ---- look: both themes, 340px
  ['a plan chip is unreadable in dark', 'hawk-ask.css', "  --hawk-planA: #0F766E; --hawk-planB: #C2410C; --hawk-planC: #BE185D; --hawk-planM: #2A4A8F;\n}\n:root[data-theme=\"light\"]", "  --hawk-planA: #14B8A6; --hawk-planB: #C2410C; --hawk-planC: #BE185D; --hawk-planM: #2A4A8F;\n}\n:root[data-theme=\"light\"]", 'look: dark'],
  ['the week grid is wider than the panel', 'hawk-ask.css', ".hawk-wk__row { display: grid; grid-template-columns: 30px repeat(5, minmax(0, 1fr)); gap: 3px; }", ".hawk-wk__row { display: grid; grid-template-columns: 30px repeat(5, 90px); gap: 3px; }", 'look: light'],
  ['the secondary text is too faint in light', 'hawk-ask.css', ".hawk-wrow__t { font-size: 12px; font-weight: 700; color: var(--hawk-dim); overflow-wrap: anywhere; }", ".hawk-wrow__t { font-size: 12px; font-weight: 700; color: #b0b0b0; overflow-wrap: anywhere; }", 'look: light'],
  ['icons are announced by screen readers', 'hawk-ask.js', "s.setAttribute('stroke-linecap', 'round'); s.setAttribute('stroke-linejoin', 'round'); s.setAttribute('aria-hidden', 'true');", "s.setAttribute('stroke-linecap', 'round'); s.setAttribute('stroke-linejoin', 'round');", 'keyboard'],
];
if (process.env.MUT_DRY) {
  let bad = 0;
  for (const [name, file, a] of M) { const n = fs.readFileSync(path.join(SRC, file), 'utf8').split(a).length - 1; if (n !== 1) { bad++; console.log('  BAD anchor (' + n + 'x):', name); } }
  console.log(bad ? bad + ' bad anchors' : 'all ' + M.length + ' anchors occur once'); process.exit(bad ? 1 : 0);
}
const ONLY = process.env.MUT_ONLY ? process.env.MUT_ONLY.split('|') : null;
let caught = 0, ran = 0; const survived = [];
for (const [name, file, a, b, test] of M) {
  if (ONLY && !ONLY.some(o => name.includes(o))) continue;
  ran++;
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'cpcm-'));
  for (const f of ['index.html', 'hawk-ask.js', 'hawk-router.js', 'hawk-ask.css', 'sw.js']) if (fs.existsSync(path.join(SRC, f))) fs.copyFileSync(path.join(SRC, f), path.join(dir, f));
  const txt = fs.readFileSync(path.join(dir, file), 'utf8'); const n = txt.split(a).length - 1;
  if (n !== 1) { console.log(`  BAD anchor (${n}x): ${name}`); survived.push(name + ' (bad anchor)'); continue; }
  fs.writeFileSync(path.join(dir, file), txt.replace(a, () => b));
  let failed = false, out = '';
  try { execFileSync('node', ['check-desktop-champ-cards.mjs', '--quiet', '--only', test], { env: { ...process.env, APP_DIR: dir }, stdio: 'pipe', timeout: 600000 }); }
  catch (e) { failed = true; out = String(e.stdout || '') + String(e.stderr || ''); }
  if (failed && (!/check-desktop-champ-cards: \d+ passed, [1-9]\d* failed/.test(out) || /EADDRINUSE/.test(out))) { console.log(`  BROKE    ${name} — the run crashed; rerun it`); survived.push(name + ' (crashed)'); continue; }
  console.log(`  ${failed ? 'caught  ' : 'SURVIVED'} ${name}`); if (failed) caught++; else survived.push(name);
}
console.log(`\nmutate-desktop-champ-cards: ${caught}/${ran} caught`);
if (survived.length) { console.log('survived:', survived.join(' | ')); process.exit(1); }
