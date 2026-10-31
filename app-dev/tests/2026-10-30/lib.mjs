/* shared bits for the 2026-10-30 date/term fixes' tests (same idioms as check-app.mjs) */
import * as FX from '/home/claude/tc/app-icon/app-dev/tests/app-fixtures.mjs';
export { FX };
export let pass = 0, fail = 0; export const fails = [];
export function ok(cond, name, info) { if (cond) { pass++; console.log('  ok  ', name); } else { fail++; fails.push(name); console.log('  FAIL', name, info !== undefined ? '→ ' + JSON.stringify(info).slice(0, 400) : ''); } }
export const tick = async (p, ms = 400) => { await p.clock.runFor(ms); await p.waitForTimeout(250); await p.clock.runFor(50); await p.waitForTimeout(100); };
/* the fixtures (one term, 2268) copied into Spring 2027 (2274) too, so both terms have the same classes */
export function liveTables() {
  const T = JSON.parse(JSON.stringify(FX.TABLES));
  for (const k of ['course_seats', 'my_sections', 'saved_classes']) T[k] = (T[k] || []).concat((T[k] || []).filter(r => r.term === '2268').map(r => Object.assign({}, r, { term: '2274' })));
  T.planner_prefs = [{ user_id: FX.ME.id, priority: 'degree', units: 12 }];
  return T;
}
export function done(label) { console.log(`\n${label}: ${pass} passed, ${fail} failed`); if (fail) { console.log('failed:\n  ' + fails.join('\n  ')); process.exit(1); } }
let port = +(process.env.APP_PORT || 8560);
export const nextPort = () => port++;
