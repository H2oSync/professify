/* check-app — the phone app (app/index.html) against synthetic fixtures, asserting on the RENDERED
   DOM and on the exact rows it writes. Run: node check-app.mjs [--only name] [--quiet]
   Exit code 1 on any failure. mutate.mjs runs this against deliberately broken copies. */
import { openApp } from './app-harness.mjs';
import * as FX from './app-fixtures.mjs';

const only = process.argv.includes('--only') ? process.argv[process.argv.indexOf('--only') + 1] : null;
const quiet = process.argv.includes('--quiet');
let pass = 0, fail = 0; const fails = [];
function ok(cond, name, info) { if (cond) { pass++; if (!quiet) console.log('  ok  ', name); } else { fail++; fails.push(name); console.log('  FAIL', name, info !== undefined ? '→ ' + JSON.stringify(info).slice(0, 300) : ''); } }
const text = p => p.locator('#scroll').innerText();
const settle = async (p, ms = 400) => { await p.clock.runFor(ms); await p.waitForTimeout(250); await p.clock.runFor(50); await p.waitForTimeout(100); };
const click = async (p, sel) => { await p.locator(sel).first().click(); await settle(p); };
const tick = (p, ms = 400) => settle(p, ms);
const tests = {};

/* The prototype's invented people and professors must never reach a screen. */
const PROTO = ['Garrett', 'Min Kim', 'Swstern', 'swstern', 'Maya Rios', 'Lehman', 'Greenbaum', 'Jabeast', 'Tristan', 'Surf Team', 'Finance Squad', 'Reset demo', 'Entrepreneurial Finance', 'Whitfield', 'termchamp.app/invite'];
const noProto = (t, where) => { const hit = PROTO.filter(w => t.includes(w)); ok(!hit.length, `no prototype data on ${where}`, hit); };

tests.signedOut = async () => {
  const { page, close, log } = await openApp({ signedIn: false });
  const t = await text(page);
  ok(!/Google/.test(t), 'signed out: no Google button (Google sign-in is off, as on the desktop)');
  ok(/email and password/i.test(t) && /sign-in code/i.test(t), 'signed out: email options offered');
  ok(await page.locator('.tabbar').count() === 0, 'signed out: no tab bar');
  ok(!log.reads.some(r => /^(my_sections|friend_requests|messages)/.test(r)), 'signed out: no private reads', log.reads);
  await click(page, '[data-a="siMode"][data-x="password"]');
  ok(await page.locator('#si-email').count() === 1 && await page.locator('#si-pw').count() === 1, 'password form shows');
  ok(log.errors.length === 0, 'signed out: no page errors', log.errors);
  await close();
};

tests.home = async () => {
  const { page, close, log } = await openApp({});
  const t = await text(page);
  noProto(t, 'Home');
  ok(/Your week/.test(t) && /Fall 2026 · 5 classes/.test(t), 'home: my week with 5 real classes (4 timed + 1 saved without a section)', t.slice(0, 200));
  const stories = await page.locator('.story .nm').allInnerTexts();
  ok(stories.length === 6 && stories[0] === 'You' && stories.includes('Avery') && stories.includes('Harper'), 'home: me + 5 real friends as stories', stories);
  const blocks = await page.locator('.fcard .g-b').allInnerTexts();
  ok(blocks.filter(b => b.replace(/\s/g, '') === 'BUS3438').length === 2, 'home: BUS 3438 drawn Mon+Wed', blocks);
  ok(/You might know[\s\S]*Pat Suggestia[\s\S]*Taking one of your classes/.test(t), 'home: suggestion with the server’s own reason');
  ok(/Where your friends are[\s\S]*PHIL 3331/.test(t), 'home: where friends are, from real classes');
  await click(page, '.story >> nth=1');
  const t2 = await text(page);
  ok(/Avery Quill/.test(t2) && /class(es)? with you/.test(t2), 'home: tapping a story shows that friend’s week');
  const shared = await page.locator('.fcard .g-b.shared').count();
  ok(shared >= 1, 'home: shared classes highlighted', shared);
  ok(log.errors.length === 0, 'home: no page errors', log.errors);
  await close();
};

tests.status = async () => {
  /* Monday 4:30pm Pacific: I am in BUS 3431 §01 (MoWe 4:10–6:00). */
  const { page, close } = await openApp({ time: '2026-09-28T16:30:00-07:00' });
  await click(page, '.story >> nth=0');
  const ring = await page.locator('.story').first().locator('.ring').getAttribute('style');
  ok(/#2563EB/i.test(ring), 'status: I show as in class (blue ring) at Mon 4:30p', ring);
  await close();
};

tests.explore = async () => {
  const { page, close, log } = await openApp({});
  await click(page, '[data-a="tab"][data-x="explore"]');
  let t = await text(page);
  noProto(t, 'Explore');
  const codes = await page.locator('#exlist .ccard .code').allInnerTexts();
  ok(codes.length === 11, 'explore: every fixture course listed once', codes);
  const card = n => page.locator('#exlist .ccard', { hasText: n }).first().innerText();
  ok(/BUS 3431[\s\S]*9 seats/.test(await card('BUS 3431')), 'explore: BUS 3431 shows the real open seats (9)', await card('BUS 3431'));
  ok(/Full/.test(await card('STAT 2170')) === false && /16 seats/.test(await card('STAT 2170')), 'explore: STAT 2170 counts only the open section', await card('STAT 2170'));
  ok(/Full/.test(await card('BUS 4442')), 'explore: BUS 4442 all full → Full', await card('BUS 4442'));
  await page.locator('#exq').fill('econ'); await tick(page);
  const c2 = await page.locator('#exlist .ccard .code').allInnerTexts();
  ok(c2.length === 1 && c2[0] === 'ECON 2303', 'explore: search narrows to ECON 2303', c2);
  await page.locator('#exq').fill(''); await tick(page);
  await click(page, '[data-a="exMode"][data-x="profs"]');
  const pc = await page.locator('#exlist .pcard').allInnerTexts();
  const ada = pc.find(x => /Ada Examplewood/.test(x)) || '';
  ok(/4\.5/.test(ada) && !/3\.6/.test(ada) && /41 PolyRatings/.test(ada), 'explore: Ada shows PolyRatings 3.62/4 as 4.5/5, from 41', ada);
  ok(/67% would take again/.test(ada), 'explore: Ada shows TermChamp would-again from her 3 reviews', ada);
  const bram = pc.find(x => /Bram Fixturesen/.test(x)) || '';
  ok(bram && !/would take again/.test(bram), 'explore: 2 reviews is below the floor — no percentage', bram);
  const gil = pc.find(x => /Gil Unratedson/.test(x)) || '';
  ok(gil && /Not on PolyRatings/.test(gil) && !/★|\d\.\d/.test(gil.replace(/BUS \d+/g, '')), 'explore: an unrated professor shows no number', gil);
  ok(pc[0].includes('Dov Mockridge'), 'explore: professors sorted by rating', pc[0]);
  ok(!pc.some(x => /(^|\n)Staff(\n|$)/.test(x)), 'explore: Staff is not a professor');
  ok(log.errors.length === 0, 'explore: no page errors', log.errors);
  await close();
};

tests.classDetail = async () => {
  const { page, close, log } = await openApp({});
  await click(page, '[data-a="tab"][data-x="explore"]');
  await click(page, '#exlist [data-x="BUS 4401"]');
  let t = await text(page);
  ok(/Strategic Management/.test(t), 'class: title');
  ok(/Fixture text about strategy\. 3 lectures\./.test(t) && !/Enrl Tot/.test(t), 'class: scraper chrome stripped from description', t.slice(0, 400));
  ok(/PREREQ\s*None listed/.test(t), 'class: no prereq in catalog → “None listed”');
  await click(page, '[data-a="back"]');
  await click(page, '#exlist [data-x="BUS 4488"]');
  t = await text(page);
  ok(/Instructor not assigned/.test(t), 'class: Staff section says instructor not assigned');
  ok(/Online self-paced/.test(t.replace(/\s+/g, ' ')), 'class: async section says online', t);
  ok(/Time not posted/.test(t), 'class: TBA section says time not posted');
  ok(/Seats unknown/.test(t), 'class: no seat data → “Seats unknown”, not a number');
  ok(/Not on PolyRatings/.test(t), 'class: unrated professor row has no rating');
  ok(!/NaN|undefined|null/.test(t), 'class: no NaN/undefined/null on screen', t.match(/NaN|undefined|null/));
  await click(page, '[data-a="back"]');
  await click(page, '#exlist [data-x="ECON 2303"]');
  t = await text(page);
  ok(/Waitlist · 11/.test(t) && /2 seats/.test(t), 'class: waitlist and open seat counts per section', t);
  ok(await page.locator('.wl').count() === 1, 'class: Watch offered only on the closed section');
  ok(log.errors.length === 0, 'class: no page errors', log.errors);
  await close();
};

tests.plans = async () => {
  const { page, close, log } = await openApp({});
  await click(page, '[data-a="tab"][data-x="explore"]');
  await click(page, '#exlist [data-x="PHIL 3331"]');
  await click(page, '.addbtn');
  await settle(page, 1500);
  const up = log.writes.filter(w => w.table === 'plans');
  ok(up.length === 1 && up[0].m === 'POST' && /on_conflict=user_id%2Cterm%2Cslot|on_conflict=user_id,term,slot/.test(up[0].query), 'plans: one upsert on user_id,term,slot', up);
  const b = up[0] && up[0].body;
  ok(b && b.slot === 'A' && b.term === '2268' && b.user_id === FX.ME.id && JSON.stringify(b.sections) === JSON.stringify([{ code: 'PHIL 3331', class_nbr: FX.seat('PHIL 3331', '01').class_nbr }]), 'plans: row is {slot A, term, sections:[{code,class_nbr}]}', b);
  ok(log.writes.some(w => w.table === 'watch_sections' && w.m === 'DELETE') === false, 'plans: PHIL already watched → no second watch write');
  /* a clash: BUS 3438 §01 is MoWe 10:10–12:00; STAT 2170 §02 is MoWeFr 9:10–10:00 — no clash; ECON §03 TuTh 10:10 clashes with PHIL TuTh 9:10–11:00 */
  await click(page, '[data-a="back"]');
  await click(page, '#exlist [data-x="ECON 2303"]');
  await click(page, '.addbtn >> nth=0');
  const toast = await page.locator('#toast').innerText();
  ok(/Conflicts with PHIL 3331/.test(toast), 'plans: a clash is refused with the real reason', toast);
  /* Plan B from the server: one real section and one the feed no longer has. */
  await click(page, '[data-a="tab"][data-x="schedule"]');
  await click(page, '[data-a="schedTab"][data-x="plans"]');
  await click(page, '[data-a="pickPlan"][data-x="B"]');
  const t = await text(page);
  ok(/1 class\b/.test(t) && /1 section in this plan is no longer in the Fall 2026 list/.test(t), 'plans: plan B loads from the server and says what it can’t show', t.slice(0, 400));
  ok(!/Use as my schedule|Make this my schedule/.test(t), 'plans: no register button');
  ok(log.errors.length === 0, 'plans: no page errors', log.errors);
  await close();
};

tests.autowatch = async () => {
  const { page, close, log } = await openApp({});
  await click(page, '[data-a="tab"][data-x="explore"]');
  await click(page, '#exlist [data-x="BUS 3346"]');
  await click(page, '.addbtn');
  const w = log.writes.filter(x => x.table === 'watch_sections');
  ok(w.length === 1 && w[0].m === 'POST' && w[0].body.class_nbr === FX.seat('BUS 3346', '01').class_nbr && w[0].body.term === '2268', 'autowatch: adding to a plan watches the section', w);
  await click(page, '.addbtn');
  const w2 = log.writes.filter(x => x.table === 'watch_sections');
  ok(w2.length === 2 && w2[1].m === 'DELETE', 'autowatch: removing it un-watches what the plan watched', w2.map(x => x.m));
  /* PHIL 3331 §01 was watched BEFORE it went in a plan: taking it out must leave that alone. */
  await click(page, '[data-a="back"]');
  await click(page, '#exlist [data-x="PHIL 3331"]');
  await click(page, '.addbtn'); await click(page, '.addbtn');
  const w3 = log.writes.filter(x => x.table === 'watch_sections');
  ok(w3.length === 2, 'autowatch: a section watched on its own stays watched', w3.map(x => x.m + ' ' + x.query));
  ok(log.errors.length === 0, 'autowatch: no page errors', log.errors);
  await close();
};

tests.prof = async () => {
  const { page, close, log } = await openApp({});
  await click(page, '[data-a="tab"][data-x="explore"]');
  await click(page, '[data-a="exMode"][data-x="profs"]');
  await click(page, '#exlist .pcard:has-text("Ada Examplewood")');
  await tick(page, 800);
  let t = await text(page);
  ok(/POLYRATINGS\s*★ 4\.5/.test(t) && /EVALUATIONS\s*41/.test(t), 'prof: PolyRatings rating (out of 5) + evaluations', t.slice(0, 300));
  ok(/RETAKE\s*67%/.test(t), 'prof: retake % from TermChamp reviews');
  ok(/3 reviews/.test(t) && /Difficulty 3\/5 from 3 reviews/.test(t), 'prof: difficulty says how many reviews it stands on');
  ok(await page.locator('#scroll .bars').count() === 1, 'prof: rating spread drawn at 3 reviews');
  ok(/Fixture review text, clear lectures\./.test(t), 'prof: written review shown');
  ok(/polyratings\.dev\/professor\/p1/.test(await page.locator('#scroll').innerHTML()), 'prof: links to her PolyRatings page');
  await click(page, '[data-a="back"]');
  await click(page, '#exlist .pcard:has-text("Faro Dummelow")');
  t = await text(page);
  ok(/Friends who took this professor[\s\S]*Avery Quill[\s\S]*BUS 3346 · Spring 2026/.test(t), 'prof: friends who took, from class_history', t.slice(-400));
  ok(/RETAKE\s*—/.test(t) && /No TermChamp reviews yet/.test(t), 'prof: no reviews → dashes, not numbers');
  await click(page, '[data-a="back"]');
  await click(page, '#exlist .pcard:has-text("Bram Fixturesen")');
  t = await text(page);
  ok(/RETAKE\s*—/.test(t) && /2 reviews/.test(t) && !/Difficulty/.test(t) && await page.locator('#scroll .bars').count() === 0 && /Fixture note about Bram\./.test(t), 'prof: 2 reviews → written review shown, but no %, average or spread', t.slice(0, 700));
  ok(log.errors.length === 0, 'prof: no page errors', log.errors);
  await close();
};

tests.rate = async () => {
  const { page, close, log } = await openApp({});
  await click(page, '[data-a="tab"][data-x="rate"]');
  let t = await text(page);
  ok(/Fall 2026[\s\S]*Current term/.test(t) && /Spring 2026/.test(t), 'rate: this term and past terms', t);
  ok(/Dov Mockridge[\s\S]*PHIL 3331/.test(t), 'rate: past class professor from class_history');
  ok(await page.locator('.li:has-text("Ada Examplewood")').count() === 1, 'rate: one row per professor (Ada teaches two of my classes)');
  await click(page, '.li:has-text("Ada Examplewood")');
  ok(await page.locator('.rf').count() === 1, 'rate: form opens');
  await click(page, '[data-a="draft"][data-x="stars"][data-y="4"]');
  await click(page, '[data-a="draft"][data-x="diff"][data-y="2"]');
  await click(page, '[data-a="draft"][data-x="again"][data-y="yes"]');
  await click(page, '[data-a="draftMore"]');
  await click(page, '[data-a="draft"][data-x="grade"][data-y="B+"]');
  await click(page, '[data-a="draft"][data-x="format"][data-y="Hybrid"]');
  await page.locator('#revta').fill('Fixture words from the test.');
  await click(page, '[data-a="postRating"]');
  await tick(page, 800);
  const w = log.writes.filter(x => x.table === 'reviews');
  const r = w[0] && w[0].body;
  const want = { professor_key: 'ada examplewood|bus', professor_name: 'Ada Examplewood', department: 'BUS', score: 4, difficulty: 2, format: 'Hybrid', grade: 'B+', would_again: true, note: 'Fixture words from the test.' };
  ok(w.length === 1 && r && Object.keys(want).every(k => r[k] === want[k]) && ['BUS 3431', 'BUS 4442'].includes(r.course), 'rate: inserts the desktop’s review row shape', r);
  ok(r && !('user_id' in r) && !('emplid' in r), 'rate: no user id or EMPLID in the row');
  t = await text(page);
  ok(/Thanks for your review/.test(t) && /Posted anonymously|Anonymous to everyone else/.test(t), 'rate: thanks screen');
  ok(!/Jordan, Aisha/.test(t), 'rate: no invented friends on the thanks screen');
  ok(log.errors.length === 0, 'rate: no page errors', log.errors);
  await close();
};

tests.rateOnce = async () => {
  const { page, close, log } = await openApp({ rpc: Object.assign({}, FX.RPC, { my_reviews: [{ id: 77, professor_key: 'ada examplewood|bus', score: 5, course: 'BUS 3431' }] }) });
  await click(page, '[data-a="tab"][data-x="rate"]');
  const row = await page.locator('.li:has-text("Ada Examplewood")').first().innerText();
  ok(/5\.0/.test(row) && !/Rate$/.test(row.trim()), 'rate: already-reviewed professor shows your score', row);
  await click(page, '.li:has-text("Ada Examplewood")');
  ok(await page.locator('.rf').count() === 0 && /already reviewed/.test(await page.locator('#toast').innerText()), 'rate: one review per professor');
  await close();
};

tests.schedule = async () => {
  const { page, close, log } = await openApp({});
  await click(page, '[data-a="tab"][data-x="schedule"]');
  let t = await text(page);
  ok(/My Classes/.test(t) && /5 classes/.test(t), 'schedule: my classes');
  ok(/BUS 2201[\s\S]*No section yet/.test(t), 'schedule: a saved class without a section is listed');
  ok(/Financial Markets[\s\S]*Bram Fixturesen · Mon\/Wed 10:10–12:00/.test(t), 'schedule: section line from the seat feed', t.slice(0, 600));
  ok(/Avery[\s\S]*in your section/.test(t), 'schedule: friends in my section');
  await click(page, '[data-a="schedTab"][data-x="planner"]');
  t = await text(page);
  ok(/termchamp\.com/.test(t) && !/Finance concentration|Graduating Spring 2027/.test(t), 'schedule: planner points to the web, no invented requirements');
  ok(log.errors.length === 0, 'schedule: no page errors', log.errors);
  await close();
};

tests.friends = async () => {
  const { page, close, log } = await openApp({});
  await click(page, '[data-a="tab"][data-x="friends"]');
  let t = await text(page);
  noProto(t, 'Friends');
  ok(/Avery Quill[\s\S]*Fixture reply from Avery/.test(t), 'friends: direct chat with last message', t.slice(0, 300));
  ok(/Fixture Study Group[\s\S]*Rowan: Fixture group note/.test(t), 'friends: group chat with sender');
  ok(await page.locator('.thread:has-text("Avery Quill") .udot').count() === 1 && await page.locator('.thread:has-text("Fixture Study Group") .udot').count() === 0, 'friends: unread follows last_read_at (Avery new, group already read)');
  await click(page, '.thread:has-text("Avery Quill")');
  await tick(page, 600);
  t = await text(page);
  ok(/Fixture message from me/.test(t) && /Fixture reply from Avery/.test(t), 'chat: messages load');
  ok(log.writes.some(w => w.table === 'conversation_members' && w.m === 'PATCH'), 'chat: opening marks it read');
  await page.locator('#chatin').fill('Hello from the test');
  await page.locator('#chatin').press('Enter');
  await tick(page, 600);
  const sent = log.writes.filter(w => w.table === 'messages');
  ok(sent.length === 1 && sent[0].body.body === 'Hello from the test' && sent[0].body.sender === FX.ME.id && sent[0].body.kind === 'text' && sent[0].body.conversation_id === FX.CONVS[0].id, 'chat: sends the real message row', sent[0] && sent[0].body);
  ok(/Hello from the test/.test(await text(page)), 'chat: sent message appears');
  await tick(page, 3000);
  ok(!/typing/.test(await page.locator('#scroll').innerHTML()) && await page.locator('#scroll .msg').count() === 3, 'chat: no invented reply (exactly the 3 real messages)', await page.locator('#scroll .msg').count());
  ok(log.errors.length === 0, 'friends: no page errors', log.errors);
  await close();
};

tests.requests = async () => {
  const { page, close, log } = await openApp({});
  await click(page, '[data-a="tab"][data-x="friends"]');
  await click(page, '[data-a="fFilter"][data-x="requests"]');
  ok(/Morgan Nobody/.test(await text(page)), 'requests: incoming request shown');
  await click(page, '[data-a="acceptReq"]');
  await tick(page, 600);
  const w = log.writes.filter(x => x.table === 'friend_requests');
  ok(w.length === 1 && w[0].m === 'PATCH' && w[0].body.status === 'accepted' && /id=eq\.990/.test(w[0].query), 'requests: accept updates that request by id', w);
  await click(page, '[data-a="fFilter"][data-x="all"]');
  await page.locator('.pym [data-a="addFriend"]').first().dblclick();
  await tick(page, 600);
  const w2 = log.writes.filter(x => x.table === 'friend_requests' && x.m === 'POST');
  ok(w2.length === 1 && w2[0].body.to_user === FX.SUGGESTED.id && w2[0].body.from_user === FX.ME.id && w2[0].body.status === 'pending', 'requests: Add (even double-tapped) sends ONE pending request', w2);
  ok(/Requested/.test(await page.locator('.pym').first().innerText()), 'requests: button turns to Requested');
  ok(log.errors.length === 0, 'requests: no page errors', log.errors);
  await close();
};

tests.friendProfile = async () => {
  const { page, close, log } = await openApp({});
  await click(page, '[data-a="tab"][data-x="friends"]');
  await click(page, '[data-a="fFilter"][data-x="people"]');
  await click(page, '.li:has-text("Rowan Testa")');
  let t = await text(page);
  ok(/UNIV 1101[\s\S]*No section yet/.test(t), 'friend: saved class with no section is listed, not drawn', t);
  await click(page, '[data-a="back"]');
  await click(page, '.li:has-text("Sky Placeholder")');
  t = await text(page);
  ok(/STAT 2170/.test(t) && !/ECON 2303/.test(t), 'friend: an orphaned section row (class not saved) is not shown', t);
  ok(log.errors.length === 0, 'friend: no page errors', log.errors);
  await close();
};

tests.champ = async () => {
  const asks = { 'open bus 3431 after 8': { tool: 'search_sections', args: { course: 'BUS3431', open_only: true } },
    'is ada good': { tool: 'professor_stats', args: { name: 'Ada Examplewood' } },
    'what is the weather': { tool: 'cant_answer', args: { reason: 'not_about_classes' } } };
  const { page, close, log } = await openApp({ ask: b => asks[b.q] || null });
  await click(page, '[data-a="openChamp"]');
  const say = async q => { await page.locator('#champin').fill(q); await page.locator('#champin').press('Enter'); await tick(page, 800); return (await page.locator('.bot .msg').last().innerText()); };
  let a = await say('open bus 3431 after 8');
  ok(/1 section matches/.test(a) && /§02/.test(a) && !/§01/.test(a), 'champ: search_sections answered from the real feed (open only)', a);
  ok(log.asks[0] && log.asks[0].term === '2268' && typeof log.asks[0].who === 'string' && log.asks[0].who.length === 16 && !('user_id' in log.asks[0]), 'champ: asks with term + 16-char pseudonym only', log.asks[0]);
  a = await say('is ada good');
  ok(/Ada Examplewood/.test(a) && /★4\.5 from 41 PolyRatings/.test(a) && /67% would take again/.test(a), 'champ: professor_stats from real numbers', a);
  a = await say('what is the weather');
  ok(/only know Cal Poly classes/.test(a), 'champ: out of scope is refused', a);
  a = await say('BUS 4442');     // ask stand-in returns a fallback → local answer
  ok(/BUS 4442 · Investments/.test(a) && /Every section is full/.test(a), 'champ: local fallback answers a bare code', a);
  a = await say('write me a poem');
  ok(/not sure|can’t reach/.test(a) && !/★/.test(a), 'champ: unknown question says so, invents nothing', a);
  ok(log.errors.length === 0, 'champ: no page errors', log.errors);
  await close();
};

tests.seatsFail = async () => {
  const { page, close, log } = await openApp({ hook: (url, m) => url.pathname.endsWith('/course_seats') && /offset=0/.test(url.search) && !/limit=1&/.test(url.search) ? { status: 500, body: '{}' } : null });
  await click(page, '[data-a="tab"][data-x="explore"]');
  const t = await text(page);
  ok(/Couldn’t load Fall 2026 classes/.test(t) && await page.locator('#exlist .ccard').count() === 0, 'seats: a failed feed says so and shows no classes', t);
  ok(log.errors.length === 0, 'seats: no page errors', log.errors);
  await close();
};

tests.chatFail = async () => {
  const { page, close, log } = await openApp({ hook: (url, m) => url.pathname.endsWith('/messages') && /conversation_id=eq\./.test(url.search) && m === 'GET' ? { status: 500, body: '{"message":"boom"}' } : null });
  await click(page, '[data-a="tab"][data-x="friends"]');
  await click(page, '.thread:has-text("Avery Quill")');
  const t = await text(page);
  ok(/Couldn’t load these messages/.test(t) && !/Say hi/.test(t), 'chat: a failed load says so, never “empty”', t);
  await close();
};

tests.wordFilter = async () => {
  const { page, close, log } = await openApp({});
  await click(page, '[data-a="tab"][data-x="rate"]');
  await click(page, '.li:has-text("Bram Fixturesen")');
  await click(page, '[data-a="draft"][data-x="stars"][data-y="2"]');
  await click(page, '[data-a="draftMore"]');
  await page.locator('#revta').fill('this class was sh1t honestly');
  await click(page, '[data-a="postRating"]');
  const t = await page.locator('.rf').innerText();
  ok(/Reviews are public, so “shit” can’t go in one/.test(t) && !log.writes.some(w => w.table === 'reviews'), 'rate: the desktop’s word filter refuses before posting', t.slice(-300));
  ok(await page.locator('#revta').inputValue() === 'this class was sh1t honestly', 'rate: the text is kept');
  await close();
};

tests.seatsPartial = async () => {
  /* A term bigger than one page, where page two fails: nothing is shown rather than half a term. */
  const extra = Array.from({ length: 1000 }, (_, i) => ({ term: '2268', course_code: 'ZZZ ' + (1000 + i), title: 'Synthetic ' + i, section: '01', instructor: 'Staff', days: 'TBA', status: 'Open', capacity: 10, enrolled: 1, available: 9, waitlist_total: 0, waitlist_capacity: 0, class_nbr: String(80000 + i), instruction_mode: 'In Person', location: '' }));
  const T = Object.assign({}, FX.TABLES, { course_seats: FX.TABLES.course_seats.concat(extra) });
  const { page, close, log } = await openApp({ tables: T, hook: url => url.pathname.endsWith('/course_seats') && /offset=1000/.test(url.search) ? { status: 500, body: '{}' } : null });
  await click(page, '[data-a="tab"][data-x="explore"]');
  const t = await text(page);
  ok(/Couldn’t load Fall 2026 classes/.test(t) && await page.locator('#exlist .ccard').count() === 0, 'seats: a partial term is never shown', t.slice(0, 200));
  await close();
};

tests.noPoly = async () => {
  const { page, close, log } = await openApp({ poly: null });
  await click(page, '[data-a="tab"][data-x="explore"]');
  await click(page, '#exlist [data-x="BUS 3431"]');
  const t = await text(page);
  ok(!/★\s*\d|\d\.\d/.test(t.replace(/\d{1,2}:\d{2}/g, '')), 'no PolyRatings: no ratings shown anywhere on the class', t);
  ok(log.errors.length === 0, 'noPoly: no page errors', log.errors);
  await close();
};

tests.noProfile = async () => {
  const T = Object.assign({}, FX.TABLES, { profiles: FX.TABLES.profiles.filter(p => p.id !== FX.ME.id) });
  const { page, close } = await openApp({ tables: T });
  const t = await text(page);
  ok(/Finish setting up/.test(t) && /termchamp\.com/.test(t) && await page.locator('.tabbar').count() === 0, 'no profile: sent to termchamp.com to set up', t);
  await close();
};

tests.desktopWidth = async () => {
  const { page, close, log } = await openApp({ width: 1280, height: 900 });
  ok(await page.locator('.side').isVisible() && /termchamp\.com\/app/.test(await page.locator('.side').innerText()), 'desktop: side panel says to open it on a phone');
  ok(/^\d{1,2}:\d{2}$/.test((await page.locator('#status > span:first-child').innerText()).trim()) && (await page.locator('#status > span:first-child').innerText()).trim() !== '9:41', 'desktop: frame status bar shows the real time', await page.locator('#status > span:first-child').innerText());
  ok(log.errors.length === 0, 'desktop: no page errors', log.errors);
  await close();
};

const names = Object.keys(tests).filter(n => !only || n === only);
for (const n of names) {
  if (!quiet) console.log('#', n);
  try { await tests[n](); } catch (e) { fail++; fails.push(n + ' threw'); console.log('  FAIL', n, 'threw', e.message.split('\n')[0]); }
}
console.log(`\ncheck-app: ${pass} passed, ${fail} failed`);
if (fail) { console.log('failed:', fails.join(' | ')); process.exit(1); }
