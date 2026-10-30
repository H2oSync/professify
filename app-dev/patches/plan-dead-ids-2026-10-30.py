#!/usr/bin/env python3
"""2026-10-30 (stuck/can't edit pass): a plan keeps class numbers that left the seat list. The plan said
"1 section in this plan is no longer in the list" with nothing to do about it, and Add to your week counted those
dead numbers toward the 12-section limit ("Plan C already has 12 sections" with 9 on screen). Now only listed
sections count, and the line has a Clear that drops the dead numbers. Both wait for the seat list: before it loads,
every number looks dead, and Clear must never empty a plan then."""
import sys, pathlib
p = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else 'app/index.html'); s = p.read_text()
def one(a, b):
    global s
    n = s.count(a); assert n == 1, (a[:70], n); s = s.replace(a, b)
one("""const planMissing = k => TC.plans[k].filter(id => !SEC[id]).length;""",
    """const planMissing = k => TC.seatsLoaded && !TC.err.seats ? TC.plans[k].filter(id => !SEC[id]).length : 0;""")
one("""    o.full = !o.inIt && !o.repl.length && ids.length >= 12;""",
    """    o.full = !o.inIt && !o.repl.length && ids.filter(x => SEC[x]).length >= 12;   /* numbers that left the list don't count (2026-10-30) */""")
one("""  ${miss ? `<div class="muted b" style="font-size:13px;padding:6px 14px">${miss} section${miss === 1 ? ' in this plan is' : 's in this plan are'} no longer in the ${esc(CFG.TERM_LABEL)} list.</div>` : ''}""",
    """  ${miss ? `<div class="muted b plan-dead" style="font-size:13px;padding:6px 14px">${miss} section${miss === 1 ? ' in this plan is' : 's in this plan are'} no longer in the ${esc(CFG.TERM_LABEL)} list. <button class="link b" style="color:var(--blue-t,var(--blue));font-size:13px;padding:10px 4px;margin:-10px 0" data-a="planClearDead" data-x="${S.plan}">Clear</button></div>` : ''}""")
one("""  removeSec: id => {""",
    """  planClearDead: k => { if (!AT_PLANS.includes(k) || !TC.seatsLoaded || TC.err.seats) return; const prev = (TC.plans[k] || []).slice(), keep = prev.filter(x => SEC[x]); if (keep.length === prev.length) return; TC.setPlan(k, keep); render(true); toastUndo(`Cleared ${prev.length - keep.length} unlisted section${prev.length - keep.length === 1 ? '' : 's'} from Plan ${k}`, () => { TC.setPlan(k, prev); render(true); toast('Undone'); }); },
  removeSec: id => {""")
p.write_text(s); print('plan-dead-ids applied')
