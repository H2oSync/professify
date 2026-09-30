/* SYNTHETIC FIXTURES for the phone app — the same invented people, professors and sections the
   desktop's harness uses (mob/harness/fixtures.mjs), plus what the phone app reads that the
   desktop harness never needed: chats, TermChamp reviews, past classes, plans, suggestions.
   Nothing here is a real student, a real schedule, a real review or a real rating. */
import * as B from './base-fixtures.mjs';
export const { ME, FRIENDS, POLY } = B;

const seat = (code, s) => B.SEATS.find(r => r.course_code === code && r.section === s);
/* Two sections the base fixtures lack: one taught by a professor PolyRatings has never heard of,
   and one with no instructor and no time — the two "we don't know" cases a screen must not fill in. */
export const SEATS = B.SEATS.concat([
  { term: '2268', course_code: 'BUS 4488', title: 'Fixture Digital Marketing', section: '01', instructor: 'Unratedson, Gil', days: 'Fr 9:10AM - 12:00PM',
    status: 'Open', capacity: 30, enrolled: 12, available: 18, waitlist_total: 0, waitlist_capacity: 10, class_nbr: '70900', instruction_mode: 'P', location: 'Bldg 03-0200' },
  { term: '2268', course_code: 'BUS 4488', title: 'Fixture Digital Marketing', section: '70', instructor: 'Staff', days: 'TBA',
    status: '', capacity: null, enrolled: null, available: null, waitlist_total: 0, waitlist_capacity: 0, class_nbr: '70901', instruction_mode: 'Asynchronous', location: '' },
  { term: '2268', course_code: 'BUS 4488', title: 'Fixture Digital Marketing', section: '02', instructor: 'Unratedson, Gil', days: 'TBA',
    status: 'Closed', capacity: 30, enrolled: 30, available: 0, waitlist_total: 0, waitlist_capacity: 0, class_nbr: '70902', instruction_mode: 'In Person', location: '' },
]);

/* One friend has a class saved with no section yet (Rowan: UNIV 1101 with no my_sections row), and
   one my_sections row whose class is NOT saved (Sky: an orphaned ECON 2303 §04) — the desktop's
   rule is that the orphan must not be shown. I also have a saved class with no section (BUS 2201). */
export const SAVED = B.SAVED.concat([
  { user_id: FRIENDS[1].id, term: '2268', code: 'UNIV 1101', class_nbr: null, created_at: '2026-09-10T18:00:00Z', waitlist_pos: null },
  { user_id: ME.id, term: '2268', code: 'BUS 2201', class_nbr: null, created_at: '2026-09-10T18:00:00Z', waitlist_pos: null },
]);
export const MY_SECTIONS = B.MY_SECTIONS.concat([
  { user_id: FRIENDS[2].id, term: '2268', code: 'ECON 2303', class_nbr: seat('ECON 2303', '04').class_nbr, section: '04', instructor: seat('ECON 2303', '04').instructor, days: seat('ECON 2303', '04').days, status: 'enrolled', wl_pos: null },
]);

/* One incoming request, on top of the five accepted friends. */
export const STRANGER = { id: '33333333-3333-4333-8333-333333333331', display_name: 'Morgan Nobody', username: 'mnobody', avatar_url: null, school: 'calpoly' };
export const SUGGESTED = { id: '33333333-3333-4333-8333-333333333332', display_name: 'Pat Suggestia', username: 'psuggest', avatar_url: null, school: 'calpoly' };
export const FRIEND_REQUESTS = B.FRIEND_REQUESTS.concat([{ id: 990, from_user: STRANGER.id, to_user: ME.id, status: 'pending', created_at: '2026-09-27T00:00:00Z' }]);

export const REVIEWS = [
  { professor_key: 'ada examplewood|bus', professor_name: 'Ada Examplewood', course: 'BUS 3431', score: 5, would_again: true, tags: ['Fixture tag one'], note: 'Fixture review text, clear lectures.', created_at: '2026-09-20T00:00:00Z', difficulty: 3, grade: 'A', format: 'In person' },
  { professor_key: 'ada examplewood|bus', professor_name: 'Ada Examplewood', course: 'BUS 4442', score: 4, would_again: false, tags: [], note: null, created_at: '2026-09-18T00:00:00Z', difficulty: 4, grade: null, format: null },
  { professor_key: 'ada examplewood|bus', professor_name: 'Ada Examplewood', course: 'BUS 3431', score: 5, would_again: true, tags: [], note: null, created_at: '2026-09-17T00:00:00Z', difficulty: 2, grade: null, format: null },
  /* Two reviews only: below the desktop's floor of 3, so no percentage or average may show. */
  { professor_key: 'bram fixturesen|bus', professor_name: 'Bram Fixturesen', course: 'BUS 3438', score: 2, would_again: false, tags: [], note: 'Fixture note about Bram.', created_at: '2026-09-16T00:00:00Z', difficulty: 5, grade: null, format: null },
  { professor_key: 'bram fixturesen|bus', professor_name: 'Bram Fixturesen', course: 'BUS 3431', score: 3, would_again: false, tags: [], note: null, created_at: '2026-09-15T00:00:00Z', difficulty: 4, grade: null, format: null },
];
export const HISTORY = [
  { user_id: FRIENDS[0].id, code: 'BUS 3346', term: 'Spring', year: 2026, professor: 'Faro Dummelow' },
  { user_id: FRIENDS[3].id, code: 'BUS 2201', term: 'Winter', year: 2026, professor: null },
  { user_id: ME.id, code: 'PHIL 3331', term: 'Spring', year: 2026, professor: 'Dov Mockridge' },
];
export const CONVS = [
  { id: 'c0000000-0000-4000-8000-000000000001', kind: 'direct', title: null, created_by: ME.id, last_at: '2026-09-27T20:00:00Z' },
  { id: 'c0000000-0000-4000-8000-000000000002', kind: 'group', title: 'Fixture Study Group', created_by: FRIENDS[1].id, last_at: '2026-09-26T20:00:00Z' },
];
export const MEMBERS = [
  { conversation_id: CONVS[0].id, user_id: ME.id, last_read_at: '2026-09-27T19:00:00Z' },
  { conversation_id: CONVS[0].id, user_id: FRIENDS[0].id, last_read_at: '2026-09-27T20:00:00Z' },
  { conversation_id: CONVS[1].id, user_id: ME.id, last_read_at: '2026-09-27T00:00:00Z' },
  { conversation_id: CONVS[1].id, user_id: FRIENDS[1].id, last_read_at: null },
  { conversation_id: CONVS[1].id, user_id: FRIENDS[2].id, last_read_at: null },
];
export const MESSAGES = [
  { id: 1, conversation_id: CONVS[0].id, sender: ME.id, kind: 'text', body: 'Fixture message from me', payload: null, created_at: '2026-09-27T18:00:00Z' },
  { id: 2, conversation_id: CONVS[0].id, sender: FRIENDS[0].id, kind: 'text', body: 'Fixture reply from Avery', payload: null, created_at: '2026-09-27T20:00:00Z' },
  { id: 3, conversation_id: CONVS[1].id, sender: FRIENDS[1].id, kind: 'text', body: 'Fixture group note', payload: null, created_at: '2026-09-26T20:00:00Z' },
];
/* Avery shares Plan A (two real sections); nobody else shares a plan. */
export const FRIEND_PLANS = [{ user_id: FRIENDS[0].id, term: '2268', slot: 'A', sections: [{ code: 'BUS 3438', class_nbr: seat('BUS 3438', '01').class_nbr }, { code: 'STAT 2170', class_nbr: seat('STAT 2170', '05').class_nbr }], shared: true }];
export const PLANS = [
  { user_id: ME.id, term: '2268', slot: 'B', sections: [{ code: 'ECON 2303', class_nbr: seat('ECON 2303', '03').class_nbr }, { code: 'BUS 9999', class_nbr: '79999' }], shared: true },
];

export const TABLES = {
  profiles: [ME, ...FRIENDS, STRANGER, SUGGESTED],
  my_sections: MY_SECTIONS, saved_classes: SAVED, watch_sections: B.WATCH,
  friend_requests: FRIEND_REQUESTS, course_seats: SEATS, course_catalog: B.CATALOG,
  reviews_public: REVIEWS, class_history: HISTORY, plans: PLANS.concat(FRIEND_PLANS),
  conversations: CONVS, conversation_members: MEMBERS, messages: MESSAGES,
  course_prereqs: [{ course_code: 'STAT 1210', prereq_json: { req: [['MATH 1000']] } }], class_waivers: [{ user_id: ME.id, code: 'ENGL 1134', reason: 'ap' }], course_equiv: [],
};
export const RPC = {
  my_reviews: [], suggest_friends: [{ id: SUGGESTED.id, display_name: SUGGESTED.display_name, username: SUGGESTED.username, avatar_url: null, reason: 'Taking one of your classes', mutuals: 0, score: 10 }],
  search_people: [{ id: SUGGESTED.id, display_name: SUGGESTED.display_name, username: SUGGESTED.username, avatar_url: null }],
  find_profile_by_handle: [],
  why_cant_i_review: [{ check_name: 'signed in', ok: true, detail: '' }, { check_name: 'email claim ends in .edu', ok: true, detail: '' }, { check_name: 'account not suspended', ok: true, detail: '' }, { check_name: 'under the hourly limit', ok: true, detail: '' }],
  my_blocks: [{ id: '33333333-3333-4333-8333-333333333339', display_name: 'Blocked Fixture', username: 'bfix', avatar_url: null, created_at: '2026-09-01T00:00:00Z' }],
  unblock_user: null, username_taken: false,
};
export const MY_REVIEW = { id: 77, professor_key: 'faro dummelow|bus', professor_name: 'Faro Dummelow', course: 'BUS 4445', score: 4, difficulty: 3, would_again: true, grade: null, format: 'In person', note: 'Fixture review I wrote.', created_at: '2026-09-20T00:00:00Z', share_with_friends: false };
export const PREREQS = [{ course_code: 'STAT 1210', prereq_json: { req: [['MATH 1000']] } }, { course_code: 'BUS 1100', prereq_json: { req: [] } }];
export const WAIVERS = [{ user_id: ME.id, code: 'ENGL 1134', reason: 'ap' }];
export { seat };
