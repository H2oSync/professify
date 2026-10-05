/* The seat rows that reach Supabase — 2026-10-04.
   From 2026-09-17 to 2026-10-04 every scrape lane was refused by Postgres (23502: null "term" in
   course_seats) because a refactor dropped the line that stamps term, status and updated_at on
   every row, and course_seats froze at 2026-09-16. This checks the stamp is back and that rows.mjs
   refuses an unstamped row with a plain reason. No browser, no network: node seats/check-rows.mjs */
import { buildUpsertRows, dedupeByClassNbr } from './rows.mjs';
import { readFileSync } from 'node:fs';
let pass = 0, fail = 0;
const ok = (c, n) => { if (c) { pass++; console.log('  ok  ', n); } else { fail++; console.log('  FAIL', n); } };
const base = { class_nbr: '5120', subject: 'EE', course_code: 'EE 1111', title: 'Intro', section: 'S01-LEC Regular', instructor: 'X',
  days: 'Fr 9:00AM - 9:50AM', dates: '08/24/2026 - 12/11/2026', status_raw: 'Open',
  capacity: 230, enrolled: 228, available: 2, waitlist_capacity: 99, waitlist_total: 0, _enriched: true };
const refused = (row, re) => { try { buildUpsertRows([row], { withCounts: true }); return false; } catch (e) { return re.test(e.message); } };
ok(refused({ ...base }, /has no term/), 'a row with no term is refused with a plain reason (was a bare 23502 from Postgres)');
ok(refused({ ...base, term: '2268' }, /has no updated_at/), 'a row with no updated_at is refused too');
const x = { ...base, status: 'Open', term: '2268', updated_at: new Date().toISOString() };
const rows = buildUpsertRows([x], { withCounts: true });
ok(rows.length === 1 && rows[0].term === '2268' && rows[0].status === 'Open' && !!rows[0].updated_at, 'a stamped row carries term, status and updated_at');
ok(rows[0].capacity === 230 && rows[0].available === 2 && rows[0].waitlist_capacity === 99, 'counts are sent when counts are on');
ok(!('capacity' in buildUpsertRows([x], { withCounts: false })[0]), 'list-only still omits the count columns');
ok(dedupeByClassNbr([...rows, ...rows]).length === 1, 'dedupe by term|class_nbr still collapses');
const src = readFileSync(new URL('./scrape-seats.mjs', import.meta.url), 'utf8');
const stamp = 'list.forEach(x => { x.status = statusBadge(x.status_raw); x.term = CFG.TERM; x.updated_at = new Date().toISOString(); });';
const i = src.indexOf('all.push(...list);');
ok(i > 0 && src.slice(Math.max(0, i - 600), i).includes(stamp), 'scrape-seats.mjs stamps every row of the normal path right before all.push(...list)');
console.log(`check-rows: ${pass} passed, ${fail} failed`);
process.exit(fail ? 1 : 0);
