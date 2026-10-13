# The phone half of champ-help-2026-10-11.py (run by it, with ROOT, patch and TOPICS).
# app/index.html: the 16 fixed answers, the close-question matcher, app_help in answerTool, the "Did you mean" chips.

patch('app/index.html', [
# ---- HELP + helpMatch, just before answerTool
("""function answerTool(j, q) {
  const a = j.args || {};""",
 r"""/* TermChamp help (2026-10-11). The 16 questions people ask about TermChamp itself, each with ONE fixed answer
   and one button. The model only picks the topic (app_help); these words are ours, checked against the app, the
   Terms and the Privacy Policy. Keep them true when the app changes. */
const HELP = {
  what_is: { q: 'What is TermChamp?', t: 'TermChamp helps Cal Poly students plan classes with friends: professor ratings, open seats, and which friends are in each class. It’s made by students — not a Cal Poly service.', a: ['Browse classes', 'tab', 'explore'] },
  free: { q: 'Is TermChamp free?', t: 'Yes — TermChamp is free. There are no ads, and your data is never sold.', a: ['Privacy Policy', 'openLegal', 'privacy'] },
  who_sees: { q: 'Who can see my schedule?', t: 'Only friends you’ve accepted see your classes. Each plan has its own “Friends can see” switch — turn it off to keep that plan to yourself. Remove a friend and they stop seeing it.', a: ['Open Settings', 'openSettings', ''] },
  ratings_anonymous: { q: 'Are my reviews anonymous?', t: 'Yes. Your name is never shown on a review — professors and other students can’t tell it was you. You can choose to show your friends, one review at a time.', a: ['My reviews', 'openMyRatings', ''] },
  ratings_source: { q: 'Where do the ratings come from?', t: 'From PolyRatings, plus the reviews TermChamp students write here. Open a professor to see their rating.', a: ['Find a professor', 'exModeGo', 'profs'] },
  seats_source: { q: 'Where do the seat numbers come from?', t: 'From Cal Poly’s public class search, refreshed about once a day — so they can be a day old, or wrong. Always check the Cal Poly Portal before you register.', a: ['Browse classes', 'tab', 'explore'] },
  add_class: { q: 'How do I add a class?', t: 'Find it in Explore and tap + on a section, then pick where it goes. Classes you’ve already taken go in Schedule › Past classes.', a: ['Open Explore', 'tab', 'explore'] },
  plans: { q: 'What are Plans A, B and C?', t: 'Three versions of your next term. TermChamp starts A as your best fit, B as a backup — the same classes in other sections — and C with more classes your friends take. Change any of them. Ask me for your game plan to see what to register for first.', a: ['Open Plans', 'schedTabGo', 'plans'] },
  seat_alerts: { q: 'How do seat alerts work?', t: 'Tap Watch on a full section; sections you add to a plan are watched for you. With notifications on, the TermChamp iPhone app tells you when a seat opens.', a: ['Browse classes', 'tab', 'explore'] },
  degree_report: { q: 'How do I upload my degree report?', t: 'In the Cal Poly Portal: Student Center › Academic Progress › Degree Progress Report › View PDF › Download. Then tap Upload report in Schedule › Past classes. Your grades and student ID are never saved.', a: ['Open Past classes', 'schedTabGo', 'past'] },
  add_friends: { q: 'How do I add friends?', t: 'Tap Add friends and search by name or @username, or share your QR code or invite link. Once they accept, you see each other’s classes.', a: ['Add friends', 'sheet', 'addFriend'] },
  block_report: { q: 'How do I block or report someone?', t: 'Open their profile or your chat with them and tap ⋯, then Block or Report — they aren’t told. To report a review, tap the flag on it. A person looks at every report within 24 hours.', a: ['Open Friends', 'tab', 'friends'] },
  delete_account: { q: 'How do I delete my account?', t: 'Settings › Delete account. It’s hidden right away and deleted after 30 days — sign back in before then to recover it. You choose whether your reviews stay up with no name.', a: ['Open Settings', 'openSettings', ''] },
  champ: { q: 'What does Champ do and where does my information go?', t: 'Champ answers questions about classes, professors, your week, your friends and TermChamp. Each question you ask goes to Anthropic’s AI to work out what you mean — never your name or account, though a class or friend you name goes with it. Your schedule and friends stay on this phone. TermChamp keeps questions about 30 days, not linked to you, and Anthropic doesn’t train on them.', a: ['How Champ uses your questions', 'champPrivacy', ''] },
  dark_mode: { q: 'Is there a dark mode?', t: 'Yes — Settings › Appearance: System, Light or Dark.', a: ['Open Settings', 'openSettings', ''] },
  contact: { q: 'How do I contact TermChamp?', t: 'Email support@termchamp.com — for a bug, feedback, or anything else.', a: ['Copy email', 'copySupport', ''] },
};
const SUPPORT_EMAIL = 'support@termchamp.com';
const helpAns = k => ({ t: HELP[k].t, acts: [HELP[k].a], help: k });
/* A question close to one of the 16 (2026-10-11, Tate: "when someone asks a quesiton that is similar it has this show
   up … because its close to the question"). Used only when the model can't place a question or can't be reached:
   each rule is words that must ALL be there, and none of the "not" words; a topic needs a rule to fire. Up to two
   topics come back, closest first, and are OFFERED ("Did you mean …"), never answered on a guess. A question naming
   a course is never about TermChamp itself. */
const HW = { app: /\b(termchamp|term champ|this app|the app|app|this site)\b/,
  mine: /\b(my|im|i'm|i am) (schedule|classes|class list|plans?|week|timetable|courses)\b|\bclasses (im|i'm|i am) (taking|in)\b/,
  ai: /\b(champ|ai|bot|chatbot|assistant|anthropic|claude)\b/, notClass: { not: /\b(class|classes|course|courses|lab|book|books|textbook|permit|parking|tuition|units?|housing|dorm|food|gym)\b/ } };
const HELP_RULES = {
  what_is: [[3, /\b(what'?s|whats|what is|what does|what even is)\b/, /\b(termchamp|term champ|this app)\b/], [3, /\bwho\b/, /\b(made|built|makes|runs|created|owns|behind)\b/, /\b(termchamp|term champ|this app|the app|this site)\b|\b(it|this) ?$/],
    [3, /\b(affiliated|endorsed)\b/], [3, /\bofficial\b/, /\b(app|termchamp|this|cal poly)\b/, { not: /\b(transcript|records?|grades?)\b/ }],
    [2, /\b(explain|tell me about|how does|what can i do (on|with))\b/, /\b(this app|the app|termchamp)\b/]],
  free: [[3, /\b(termchamp|term champ|this app|the app) (free|cost|costs)\b/], [3, /\b(is|was) (it|this) free( to use)? ?$|\bfree to use ?$/],
    [3, /\bhow much (does|is) (it|this|termchamp|the app)\b/, HW.notClass], [3, /\b(have to|need to|do i) pay\b|\bpaywall\b|\bpremium\b|\bsubscription\b|\bcosts? money\b/, HW.notClass],
    [3, /\b(cost|costs|price|pricing|pay for)\b/, HW.app], [3, /\b(ads|adverts?|advertising|advertisements?)\b/, HW.app], [3, /\bthere ads\b|\bany ads\b/],
    [3, /\bsell\w*\b/, /\b(data|info|information)\b/]],
  who_sees: [[3, /\b(see|sees|seeing|view|views|visible|look at|access)\b/, HW.mine, /\b(who|whom|ppl|people|someone|somebody|anyone|anybody|everyone|strangers|random|others|public|friends|students|professors?)\b/],
    [3, /\b(private|public|hidden|hide|privacy)\b/, /\bmy (schedule|classes|class list|plans?|week|timetable|courses|profile|account)\b/]],
  ratings_anonymous: [[3, /\b(anonymous|anonymously|anon)\b/],
    [3, /\b(know|see|find out|figure out|tell)\b/, /\b(i|me|my)\b/, /\b(wrote|review|reviews|rated|rating|ratings)\b/, /\b(professors?|profs?|teachers?|people|ppl|friends|anyone|others|they|everyone)\b/],
    [3, /\b(figure out|find out|know|tell|see) who (posted|wrote|left|made)\b/, /\b(review|reviews|rating|ratings)\b/], [3, /\bname\b/, /\b(review|reviews|rating|ratings)\b/]],
  ratings_source: [[3, /\b(where|how)\b/, /\b(ratings?|reviews?|stars?|scores?)\b/, /\b(come from|from|calculated|work|made|get)\b/], [3, /\bpoly ?ratings\b/],
    [3, /\bhow\b/, /\b(professors?|profs?|teachers?)\b/, /\b(rated|scored|ranked)\b/], [3, /\b(ratings?|reviews?)\b/, /\b(real|accurate|legit|fake|trust|reliable|scraped|sourced)\b/],
    [3, /\bwho (writes|makes|leaves|does)\b/, /\b(the )?(ratings|reviews)\b/]],
  seats_source: [[3, /\b(seats?|seat counts?|seat numbers?|enrollment numbers?)\b/, /\b(come from|from|live|accurate|up to date|updated|update|real|real time|realtime|wrong|correct|old|stale|refresh\w*|how often|reliable)\b/],
    [3, /\bwhere (do|does) (you|u|they|termchamp|the app)\b/, /\bseats?|seat (counts?|numbers?)\b/]],
  add_class: [[3, /\b(how|where)\b/, /\b(add|adding|put|enter|import)\b/, /\b(class|classes|course|courses|schedule)\b/],
    [3, /^ (add|put in|enter) (a|my) (class|classes|course|courses)\b/], [3, /\badding (my )?classes\b/]],
  plans: [[3, /\b(what|why|how)\b/, /\b(plans a|plans? a,? b|three plans|3 plans|a plan)\b/], [3, /\bwhat (is|are) plans?\b/],
    [3, /\b(multiple|different|three|3|several|other|two) plans\b|\bplan tabs\b|\bbackup (plans?|schedules?)\b/], [3, /\b(make|switch|use|set up|create|between)\b/, /\bplans? ?[abc]\b/]],
  seat_alerts: [[3, /\b(seat alerts?|alerts?|notifications?|notified|notify|push|watch|watching|watched|watchlist)\b/, /\b(how|what|does|do|will|work|works|mean|get|set up|setup|turn on|full)\b/]],
  degree_report: [[3, /\b(dpr|degree progress report|degree progress|degree report|degree audit|academic progress)\b/, /\b(how|where|why|what|whats|what's|safe|upload|get|need|private|download|find|import|read|use|add)\b/]],
  add_friends: [[3, /\b(how|where|can)\b/, /\b(add|find|invite|friend request|connect\w*|search)\b/, /\bfriends?\b/], [3, /\bhow do(es)? (friends?|friend requests?) work\b/],
    [3, /\b(how|can i|where)\b/, /\binvite\b/, { not: /\blink\b/ }]],
  block_report: [[3, /\b(block|blocking|harass\w*|bull(y|ying|ied)|stalk\w*|abusive|inappropriate|offensive|creepy|mean to me|threaten\w*)\b/, { not: /\bblock(ing)? (off|out)\b|\b(time|class) blocks?\b|\bblock schedul/ }],
    [3, /\b(report|reporting|flag)\b/, /\b(someone|somebody|a user|user|person|people|review|reviews|message|messages|profile|group|account|him|her|them|abuse|post)\b/, { not: /\b(progress|degree|dpr|transfer)\b/ }]],
  delete_account: [[3, /\b(delete|deleting|deleted|deactivate|close|cancel|erase|wipe|remove)\b/, /\b(account|termchamp|my data|everything|my profile|the app)\b/, { not: /\b(photo|picture|pic|class|classes|friend|friends|plan)\b/ }],
    [3, /\b(recover|restore|get back|undelete)\b/, /\baccount\b/]],
  champ: [[3, HW.ai, /\b(send|sends|sent|data|info|information|privacy|private|store|stores|stored|keep|keeps|save|saves|saved|track|tracks|tracking|train|training|safe|share|shares|shared|questions?|messages?|chats?)\b/],
    [3, /\bwhat (does|is|can)\b/, /\bchamp\b/], [3, /\bwho is champ\b|\bchamp\b.*\b(real person|a person|human|a bot|ai)\b/], [3, HW.ai, /\b(see|sees|read|reads|access|know|knows)\b/, /\bmy\b/],
    [3, /\bwhere\b/, /\b(info|information|data|questions?)\b/, /\b(go|goes|going|sent|stored|kept)\b/]],
  dark_mode: [[3, /\b(dark|night|light) ?(mode|theme)\b/], [3, /\b(change|switch|customi[sz]e)\b/, /\b(colou?rs?|theme|look|looks|appearance)\b/], [3, /\bdark\b/, /\b(app|setting|settings|screen|version)\b/]],
  contact: [[3, /\b(contact|customer service|help desk|helpdesk)\b/, { not: /\b(professors?|profs?|teachers?|advisors?|instructors?|ta|department|registrar|counselor)\b/ }], [3, /\bsupport\b/, { not: /\b(class|classes|course|courses|requirements?|units|ge|major)\b/ }],
    [3, /\b(bug|bugs|glitch|glitches|crash\w*|not working|doesn'?t work|isn'?t working)\b/], [3, /\b(broken|not loading|won'?t load|keeps freezing)\b/, /\b(app|termchamp|it)\b/],
    [3, /\b(feedback|suggestion|feature request)\b/], [3, /\b(problem|issue)\b/, HW.app], [3, /\b(email|e-mail)\b/, /\b(team|termchamp|you guys|the devs?|developers?|creators?)\b/],
    [3, /\b(talk to|reach|message|email) (a )?(human|person|someone|the team|the devs?|the developers?|the creators?|you guys)\b/]],
};
/* A question that is just a topic's name ("cost?", "seat alerts", "add friend"). */
const HELP_BARE = { free: /^ (cost|price|ads|is it free|free) $/, seat_alerts: /^ (seat alerts?|alerts|watching|notifications) $/, add_friends: /^ (add|adding|find) (a )?friends? $/,
  plans: /^ (plans?|plans? [abc]|plan a b c) $/, degree_report: /^ (dpr|degree progress report|degree report) $/, dark_mode: /^ dark $/, contact: /^ (support|contact|feedback) $/ };
Object.keys(HELP_BARE).forEach(k => HELP_RULES[k].push([3, HELP_BARE[k]]));
function helpMatch(q) {
  const t = ' ' + String(q || '').toLowerCase().replace(/[’‘]/g, "'").replace(/[^a-z0-9' ]+/g, ' ').replace(/\s+/g, ' ').trim() + ' ';
  if (t.trim().length < 4 || /\b[a-z]{2,5} ?\d{3,4}[a-z]?\b/.test(t.replace(/\b(fall|winter|spring|summer|in|of|since|by|until|for|class of) (19|20)\d\d\b/g, ' '))) return [];
  return Object.keys(HELP_RULES).map(k => ({ k, s: HELP_RULES[k].reduce((n, r) => {
      const w = r[0], rs = r.slice(1), not = rs.find(x => x && x.not);
      return rs.every(x => (x && x.not) ? true : x.test(t)) && !(not && not.not.test(t)) ? n + w : n; }, 0) }))
    .filter(x => x.s >= 2).sort((x, y) => y.s - x.s).slice(0, 2).map(x => x.k);
}
const helpOffer = ks => ({ t: ks.length > 1 ? 'Did you mean one of these?' : 'Did you mean this?', follow: ks.map(k => [HELP[k].q, 'champHelp', k]) });
function answerTool(j, q) {
  const a = j.args || {};"""),
# ---- app_help in answerTool; cant_answer marks itself so a close topic can be offered instead
("""    case 'cant_answer': return { t: a.reason === 'not_about_classes'""",
 """    case 'app_help': return Object.prototype.hasOwnProperty.call(HELP, a.topic) ? helpAns(a.topic) : answerTool({ tool: 'cant_answer', args: { reason: 'ambiguous' } }, q);
    case 'cant_answer': return { cant: 1, t: a.reason === 'not_about_classes'"""),
# ---- ask(): offer the closest topics when the model can't place it, or can't be reached
("""  if (!a) a = localAnswer(q);
  if (a && a.wait)""",
 """  if (!a) a = localAnswer(q);
  if (!a || a.cant) { const hk = helpMatch(q); if (hk.length) a = helpOffer(hk); }
  if (a && a.wait)"""),
# ---- the chips: a string asks it; [label, action, arg] runs that action (the "Did you mean" topics)
("""    const follow = n === m.length - 1 && x.follow && x.follow.length ? `<div class="chfollow">${x.follow.map(f => `<button data-a="ask" data-x="${esc(f)}">${esc(f)}</button>`).join('')}</div>` : '';""",
 """    const follow = n === m.length - 1 && x.follow && x.follow.length ? `<div class="chfollow">${x.follow.map(f => Array.isArray(f) ? `<button class="chhelp" data-a="${esc(f[1])}" data-x="${esc(f[2])}">${esc(f[0])}</button>` : `<button data-a="ask" data-x="${esc(f)}">${esc(f)}</button>`).join('')}</div>` : '';"""),
(""".chfollow button{min-height:44px;padding:0 14px;border-radius:22px;border:1.5px solid var(--line2);background:var(--card);font-size:14px;font-weight:800;color:var(--ink)}""",
 """.chfollow button{min-height:44px;padding:0 14px;border-radius:22px;border:1.5px solid var(--line2);background:var(--card);font-size:14px;font-weight:800;color:var(--ink)}
.chfollow button.chhelp{text-align:left;padding:10px 14px;line-height:1.3;border-color:var(--blue);color:var(--blue-t,var(--blue))}"""),
# ---- the actions: a topic chip answers on the phone (no second question to the model); Copy email
("""  ask: q => ask(q),""",
 """  ask: q => ask(q),
  /* a "Did you mean" chip: the topic's fixed answer, from the phone — nothing is sent */
  champHelp: k => { if (!Object.prototype.hasOwnProperty.call(HELP, k)) return; S.champMsgs.push({ me: 1, t: HELP[k].q }, Object.assign({ card: null, follow: [] }, helpAns(k))); render(true); champEnd(); },
  copySupport: async () => { try { await navigator.clipboard.writeText(SUPPORT_EMAIL); toast('Email copied'); } catch (e) { toast(SUPPORT_EMAIL); } },"""),
])
_s = (ROOT / 'app/index.html').read_text()
assert all(f"  {k}: {{ q: '" in _s for k in TOPICS), 'champ-help: a topic without an answer'
print('champ-help: app/index.html (HELP, helpMatch, app_help, Did you mean chips)')
