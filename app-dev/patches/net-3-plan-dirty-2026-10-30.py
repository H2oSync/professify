#!/usr/bin/env python3
"""Network resilience 3/4 (2026-10-30, stress test s3 P2): a plan edit made offline was lost. The toast said "Couldn't
save Plan B", nothing ever tried again, and the next foreground refresh (loadPlans) put the server's old plan back.

- TC.setPlan marks the slot unsaved at once, on the phone (localStorage tc_plan_dirty: uid, term and the plan's rows
  as they go up, {code, class_nbr}, so it can be sent again before the seat feed has loaded). wipeDevice clears it
  with every other tc_ key on sign-out.
- pushPlan clears the mark only when the save lands and nothing was edited meanwhile; a failure keeps it and says so.
- The unsaved slots go up again when the phone is back online, when the app comes back to the front, and after every
  plans read (regRetry's pattern).
- loadPlans never overwrites an unsaved slot, nor one edited while its read was out; after a restart the unsaved
  plan is what the student sees.

Usage: python3 net-3-plan-dirty-2026-10-30.py app/index.html"""
import sys
p = sys.argv[1]; s = open(p, encoding='utf-8').read()
def one(old, new):
    global s
    assert s.count(old) == 1, (s.count(old), old[:90]); s = s.replace(old, new)

one("""async function loadPlans() {
  TC.plansLoaded = false;
  try { const c = JSON.parse(localStorage.getItem(PLAN_LOCAL) || 'null'); if (c && c.uid === TC.user.id && c.term === CFG.TERM) TC.autoWatch = c.autoWatch || {}; } catch (e) {}
  const r = await TC.client().from('plans').select('slot,sections,shared').eq('user_id', TC.user.id).eq('term', CFG.TERM);
  if (r.error) { TC.err.plans = schemaGap(r.error) ? 'missing' : r.error.message; return; }
  delete TC.err.plans;
  TC.plans = { A: [], B: [], C: [] }; TC.plansLoaded = true;""", """/* (2026-10-30) A plan edit that hasn't reached the server is kept on the phone (rows as they go up, so it can be sent
   again before the seat feed loads) until a save lands; loadPlans never overwrites it, and it goes up again when the
   phone is back online or the app comes back to the front. */
const PLAN_DIRTY = 'tc_plan_dirty';
TC.planSeq = TC.planSeq || {};
function planDirtyRead() { try { const d = JSON.parse(localStorage.getItem(PLAN_DIRTY) || 'null'); if (d && d.slots && TC.user && d.uid === TC.user.id && d.term === CFG.TERM) return d; } catch (e) {} return null; }
function planDirtySet(slot, rows) {
  if (!TC.user) return;
  const d = planDirtyRead() || { uid: TC.user.id, term: CFG.TERM, slots: {} };
  if (rows) d.slots[slot] = rows; else delete d.slots[slot];
  try { if (Object.keys(d.slots).length) localStorage.setItem(PLAN_DIRTY, JSON.stringify(d)); else localStorage.removeItem(PLAN_DIRTY); } catch (e) {}
}
let planRetrying = false;
async function planRetry() {
  if (!TC.user || !TC.plansLoaded || planRetrying) return;
  const d = planDirtyRead(); if (!d) return;
  planRetrying = true;
  try { for (const k of Object.keys(d.slots)) { if (!TC.plans[k]) continue; clearTimeout(planTimers[k]); await pushPlan(k, true); } } finally { planRetrying = false; }
}
window.addEventListener('online', () => { planRetry(); });
document.addEventListener('visibilitychange', () => { if (document.visibilityState === 'visible') planRetry(); });
async function loadPlans() {
  TC.plansLoaded = false;
  try { const c = JSON.parse(localStorage.getItem(PLAN_LOCAL) || 'null'); if (c && c.uid === TC.user.id && c.term === CFG.TERM) TC.autoWatch = c.autoWatch || {}; } catch (e) {}
  const seq0 = Object.assign({}, TC.planSeq), d0 = planDirtyRead();
  const r = await TC.client().from('plans').select('slot,sections,shared').eq('user_id', TC.user.id).eq('term', CFG.TERM);
  if (r.error) { TC.err.plans = schemaGap(r.error) ? 'missing' : r.error.message; return; }
  delete TC.err.plans;
  const prevPlans = TC.plans || {}, d1 = planDirtyRead();
  TC.plans = { A: [], B: [], C: [] }; TC.plansLoaded = true;""")

one("""    TC.planShared[row.slot] = row.shared !== false;
  });
}""", """    TC.planShared[row.slot] = row.shared !== false;
  });
  /* an unsaved slot, or one edited while this read was out, stays as the phone has it */
  ['A', 'B', 'C'].forEach(k => {
    const ds = (d1 && d1.slots[k]) || (d0 && d0.slots[k]);
    if ((TC.planSeq[k] || 0) !== (seq0[k] || 0)) TC.plans[k] = (prevPlans[k] || []).slice();
    else if (Array.isArray(ds)) { TC.plans[k] = ds.map(x => String(x && x.class_nbr)).filter(x => x && x !== 'undefined'); ds.forEach(x => { if (x && x.class_nbr != null && !PLAN_RAW[String(x.class_nbr)]) PLAN_RAW[String(x.class_nbr)] = x; }); }
  });
  if (d1) setTimeout(planRetry, 0);
}""")

one("""  const touched = [...new Set(before.concat(TC.plans[slot]))];
  touched.forEach(syncPlanWatch);
  clearTimeout(planTimers[slot]);""", """  const touched = [...new Set(before.concat(TC.plans[slot]))];
  TC.planSeq[slot] = (TC.planSeq[slot] || 0) + 1; planDirtySet(slot, planList(slot));
  touched.forEach(syncPlanWatch);
  clearTimeout(planTimers[slot]);""")

one("""async function pushPlan(slot) {
  const sb = TC.client(); if (!sb || !TC.user) return;
  const list = planList(slot);""", """async function pushPlan(slot, quiet) {
  const sb = TC.client(); if (!sb || !TC.user) return;
  const list = planList(slot), seq = TC.planSeq[slot] || 0;""")

one("""  const r = await q;
  if (r.error) toast('Couldn’t save Plan ' + slot + ' — check your connection');
}""", """  let r; try { r = await q; } catch (e) { r = { error: e }; }
  if (r.error) { if (!quiet) toast('Couldn’t save Plan ' + slot + ' — it’s kept on this phone and will save when you’re back online'); return false; }
  if ((TC.planSeq[slot] || 0) === seq) planDirtySet(slot, null);
  return true;
}""")
open(p, 'w', encoding='utf-8').write(s); print(p, 'net-3 plan dirty: ok')
