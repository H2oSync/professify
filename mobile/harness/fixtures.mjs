/* SYNTHETIC FIXTURES — invented people, invented professors. Course codes are real catalog
   codes because the planner and GE data are keyed on them; nothing here is a real student,
   a real schedule or a real rating. Every name is deliberately unlike any Cal Poly person. */

export const ME = {
  id: '11111111-1111-4111-8111-111111111111',
  email: 'jordan.fixture@calpoly.edu',
  display_name: 'Jordan Fixture', username: 'jfixture', major: 'Business Administration',
  class_standing: 'Junior', avatar_url: null, instagram_handle: null, school: 'calpoly',
};

const F = (n, id, name, user) => ({ id: `2222222${n}-2222-4222-8222-22222222222${n}`, display_name: name, username: user,
  avatar_url: null, instagram_handle: null, school: 'calpoly' });
export const FRIENDS = [
  F(1, 1, 'Avery Quill', 'aquill'),
  F(2, 2, 'Rowan Testa', 'rtesta'),
  F(3, 3, 'Sky Placeholder', 'splace'),
  F(4, 4, 'Quinn Sample', 'qsample'),
  F(5, 5, 'Harper Mock', 'hmock'),
];

/* Instructor names are invented, and the PolyRatings stand-in below rates them. */
const PROFS = [
  ['p1', 'Ada', 'Examplewood', 'BUS', 3.62, 41],
  ['p2', 'Bram', 'Fixturesen', 'BUS', 2.85, 23],
  ['p3', 'Cleo', 'Stubbington', 'ECON', 3.21, 58],
  ['p4', 'Dov', 'Mockridge', 'PHIL', 3.88, 17],
  ['p5', 'Esme', 'Samplesworth', 'STAT', 2.44, 36],
  ['p6', 'Faro', 'Dummelow', 'BUS', 3.05, 12],
];
export const POLY = PROFS.map(([id, f, l, d, r, n]) => ({ id, firstName: f, lastName: l, department: d,
  overallRating: r, numEvals: n, courses: [] }));
const name = id => { const p = PROFS.find(x => x[0] === id); return `${p[2]}, ${p[1]}`; };

/* One row per section, exactly the columns loadSeats() selects. */
let nbr = 70100;
const S = (code, title, section, prof, days, cap, enr, wl = 0, wlcap = 10) => ({
  term: '2268', course_code: code, title, section, instructor: name(prof), days,
  status: enr >= cap ? (wl > 0 ? 'Wait List' : 'Closed') : 'Open',
  capacity: cap, enrolled: enr, available: Math.max(0, cap - enr), waitlist_total: wl, waitlist_capacity: wlcap,
  class_nbr: String(nbr++), instruction_mode: 'P', location: 'Bldg 03-0112',
});
export const SEATS = [
  S('BUS 3431', 'Business Finance', '01', 'p1', 'MoWe 4:10PM - 6:00PM', 40, 40, 6),
  S('BUS 3431', 'Business Finance', '02', 'p2', 'TuTh 8:10AM - 10:00AM', 40, 31),
  S('BUS 4442', 'Investments', '01', 'p1', 'MoWe 12:10PM - 2:00PM', 35, 35, 3),
  S('BUS 4445', 'Portfolio Management', '01', 'p6', 'MoWe 2:10PM - 4:00PM', 30, 27),
  S('BUS 3438', 'Financial Markets', '01', 'p2', 'MoWe 10:10AM - 12:00PM', 40, 22),
  S('ECON 2303', 'Microeconomics', '03', 'p3', 'TuTh 10:10AM - 12:00PM', 120, 118),
  S('ECON 2303', 'Microeconomics', '04', 'p3', 'TuTh 2:10PM - 4:00PM', 120, 120, 11),
  S('PHIL 3331', 'Business Ethics', '01', 'p4', 'TuTh 9:10AM - 11:00AM', 35, 30),
  S('STAT 2170', 'Applied Statistics', '02', 'p5', 'MoWeFr 9:10AM - 10:00AM', 60, 60, 9),
  S('STAT 2170', 'Applied Statistics', '05', 'p5', 'TuTh 12:10PM - 2:00PM', 60, 44),
  /* Three of Business Administration's real core codes, so "Recommended for your major" renders. */
  S('BUS 3346', 'Principles of Marketing', '01', 'p6', 'MoWe 8:10AM - 9:30AM', 45, 30),
  S('BUS 3387', 'Organizational Behavior', '02', 'p1', 'TuTh 2:10PM - 3:30PM', 45, 45, 4),
  S('BUS 4401', 'Strategic Management', '01', 'p2', 'MoWe 10:10AM - 11:30AM', 40, 33),
];
const sec = (code, s) => SEATS.find(r => r.course_code === code && r.section === s);

const mine = (user, code, s, status = 'enrolled') => { const r = sec(code, s); return {
  user_id: user, term: '2268', code, class_nbr: r.class_nbr, section: s, instructor: r.instructor, days: r.days, status, wl_pos: null }; };

export const MY_SECTIONS = [
  mine(ME.id, 'BUS 3438', '01'), mine(ME.id, 'BUS 4442', '01'), mine(ME.id, 'BUS 4445', '01'),
  mine(ME.id, 'BUS 3431', '01'),
  mine(FRIENDS[0].id, 'BUS 4442', '01'), mine(FRIENDS[0].id, 'PHIL 3331', '01'), mine(FRIENDS[0].id, 'BUS 3431', '02'),
  mine(FRIENDS[1].id, 'BUS 4445', '01'), mine(FRIENDS[1].id, 'ECON 2303', '03'),
  mine(FRIENDS[2].id, 'STAT 2170', '05'), mine(FRIENDS[2].id, 'BUS 3438', '01'),
  mine(FRIENDS[3].id, 'PHIL 3331', '01'),
];
export const SAVED = MY_SECTIONS.map(r => ({ user_id: r.user_id, term: '2268', code: r.code, class_nbr: r.class_nbr,
  created_at: '2026-09-10T18:00:00Z', waitlist_pos: null }));
export const WATCH = [
  { user_id: ME.id, term: '2268', code: 'ECON 2303', class_nbr: sec('ECON 2303', '03').class_nbr, section: '03',
    instructor: sec('ECON 2303', '03').instructor, days: sec('ECON 2303', '03').days },
  { user_id: ME.id, term: '2268', code: 'STAT 2170', class_nbr: sec('STAT 2170', '05').class_nbr, section: '05',
    instructor: sec('STAT 2170', '05').instructor, days: sec('STAT 2170', '05').days },
  { user_id: ME.id, term: '2268', code: 'PHIL 3331', class_nbr: sec('PHIL 3331', '01').class_nbr, section: '01',
    instructor: sec('PHIL 3331', '01').instructor, days: sec('PHIL 3331', '01').days },
];
export const FRIEND_REQUESTS = FRIENDS.map((f, i) => ({ id: 900 + i, from_user: i % 2 ? ME.id : f.id,
  to_user: i % 2 ? f.id : ME.id, status: 'accepted', created_at: '2026-09-01T00:00:00Z' }));

/* course_catalog, as seats/scrape-seats.mjs upserts it. FIXTURE TEXT — written for the test, not
   Cal Poly's catalog wording. The first row leads with a prerequisite sentence on purpose: the
   short line must skip it rather than print "Prerequisite: …" as a description. */
export const CATALOG = [
  { course_code: 'BUS 3346', prereqs: 'Junior standing.', description: 'Prerequisite: Junior standing. Fixture text about markets, customers and the marketing mix. 3 lectures.' },
  { course_code: 'BUS 3387', prereqs: '', description: 'Fixture text about how people behave inside organizations, and how teams make decisions under pressure together over a long semester of case work and presentations. 3 lectures.' },
  /* The real run (09-24) found 134 rows where the scraper kept the class-search page around the text:
     the crosslisted seat table and class notes, then the page's own "Description" label. Numbers
     and codes here are invented; only the shape is Cal Poly's. */
  { course_code: 'BUS 4401', prereqs: '', description: 'Status Enrl Tot Wait Tot BUS 4401-X01 LEC (7001) Fixture Strategy Open 40 33 ZZZ 4401-X01 LEC (7002) Fixture Strategy Open 5 0 Notes Class Notes Also offered as ZZZ 4401. Description Fixture text about strategy. 3 lectures.' },
  /* The shapes a naive sentence split gets wrong: initials, a dotted abbreviation, a decimal. */
  { course_code: 'ECON 2303', prereqs: '', description: 'Fixture study of U.S. markets, e.g. prices and 2.5 other things since 1877. 3 lectures.' },
  { course_code: 'STAT 2170', prereqs: '', description: 'Prerequisite: MATH 1180. 4 lectures.' },
  /* A course level before a requirement (review, 09-24): "I." ends the sentence here. */
  { course_code: 'PHIL 3331', prereqs: '', description: 'Fixture Ethics I. Prerequisite: PHIL 1000. 3 lectures.' },
  /* A quarter-era row the table may still hold — must never attach to anything. */
  { course_code: 'BUS 346', prereqs: '', description: 'Old quarter-era fixture text that must not appear.' },
];

export const TABLES = {
  profiles: [ME, ...FRIENDS],
  my_sections: MY_SECTIONS, saved_classes: SAVED, watch_sections: WATCH,
  friend_requests: FRIEND_REQUESTS, course_seats: SEATS, course_catalog: CATALOG,
};
export const RPC = { my_private_profile: [{ ...ME }], friends_of: [], suggest_friends: [], suggest_classmates_v2: [],
  trending_profs: [], my_reviews: [], my_blocks: [], is_moderator: false, friends_reviewed: [], log_events: null };
