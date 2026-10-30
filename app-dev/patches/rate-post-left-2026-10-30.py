#!/usr/bin/env python3
"""2026-10-30 (stuck/can't edit pass): Post rating replaced whatever was on top of the open tab with the Thanks page,
even when the student had already left the form while it posted (X, swipe back, another tab) — the professor page
they went back to turned into Thanks, or another tab's page did. Now Thanks replaces only the form itself, while
it is still the screen showing; otherwise a "Rating posted." toast and the stale form leaves its stack. Saving an
EDIT went back() unconditionally and popped whatever page the student had moved to: it now leaves only its own form.
The form's X is disabled while it posts."""
import sys, pathlib
p = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else 'app/index.html'); s = p.read_text()
def one(a, b):
    global s
    n = s.count(a); assert n == 1, (a[:70], n); s = s.replace(a, b)
# the X
one("""<button class="xbtn" data-a="back" aria-label="Cancel">${ic('x', 18, 2.4)}</button></div>
  <div class="fcardx">""",
    """<button class="xbtn" data-a="back" aria-label="Cancel" ${UI.busy.rate ? 'disabled aria-disabled="true"' : ''}>${ic('x', 18, 2.4)}</button></div>
  <div class="fcardx">""")
# a new rating
one("""    UI.busy.rate = 1; render(true);
    const r = await TC.postReview(d.prof, d);
    UI.busy.rate = 0;
    if (r.err) { d.err = r.err; render(true); return; }
    draftClear(d.prof);
    S.lastRated = Object.assign({}, d, { reviewId: r.id, share: false });
    const st = S.stack[S.tab]; st[st.length - 1] = { s: 'rateThanks', p: {} }; render();""",
    """    const tab0 = S.tab, st = S.stack[tab0], form = st[st.length - 1];   /* the form this post belongs to (2026-10-30) */
    UI.busy.rate = 1; render(true);
    const r = await TC.postReview(d.prof, d);
    UI.busy.rate = 0;
    if (r.err) { d.err = r.err; render(true); return; }
    draftClear(d.prof);
    S.lastRated = Object.assign({}, d, { reviewId: r.id, share: false });
    if (S.tab === tab0 && cur() === form && form && form.s === 'rateForm') { st[st.length - 1] = { s: 'rateThanks', p: {} }; render(); }
    else { const i = st.indexOf(form); if (i > 0 && form.s === 'rateForm') st.splice(i, 1); if (S.draft === d) S.draft = null; toast('Rating posted.'); render(true); }""")
# an edit
one("""  const d = S.draft; if (!d || !d.editing) return _post();
  if (!d.stars || !d.code || UI.busy.rate) return;""",
    """  const d = S.draft; if (!d || !d.editing) return _post();
  if (!d.stars || !d.code || UI.busy.rate) return;
  const tab0 = S.tab, st0 = S.stack[tab0], form = st0[st0.length - 1];   /* (2026-10-30) */""")
one("""  S.draft = null; toast(fe ? 'Review updated. ' + fe : 'Review updated'); loadReviews().then(() => render(true)); back();""",
    """  S.draft = null; toast(fe ? 'Review updated. ' + fe : 'Review updated'); loadReviews().then(() => render(true));
  if (S.tab === tab0 && cur() === form) back(); else { const i = st0.indexOf(form); if (i > 0 && form.s === 'rateForm') st0.splice(i, 1); render(true); }""")
p.write_text(s); print('rate-post-left applied')
