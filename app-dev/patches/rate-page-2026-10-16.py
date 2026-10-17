#!/usr/bin/env python3
"""WEBSITE, 2026-10-16: the Rate tab is a real page (marker 'rate-page (2026-10-16)'). It was the "Review a professor" modal.
Owner-approved mockup: scratchpad/batch1016/mockups, section 3 option A.

THE PAGE (#view-rate): title "Rate" and a line; "N of M rated" with a thin bar (M = your professors, past and current, that the
modal listed); search (a name, or a course as prefix + number) with "Narrow by course" (Your major / Change, course prefix,
course number - the modal's three fields and the same finding code: rlMyProfs, rlMyProfGroups, rlScopedProfs, rlNameHits);
"Taking now . Fall 2026" with Rate buttons and scores, then Past terms (6 shown, "Show N more"); "Reviewed" badges stay.
Rate opens the EXISTING review form (renderRateForm / submitRate / rfSaveEdit, unchanged) under the professor's row; on a
phone (<=640px) it is a bottom sheet. Right rail: Your reviews (Edit = the existing myrEdit), the helpful-votes count
(window.MY_IMPACT, which loadMyReviews already sets), and "Latest reviews at Cal Poly" only when Home's feed data
(HM_RECENTS, reviews_public) has 8 or more. No streak. Signed out: a sign-in card; the search still works and Rate runs the
same verify-then-resume gate as before. No new server call: loadMyReviewed / loadMyHistory / loadMyReviews are the modal's.

HOW THE FORM MOVES: renderRateForm and renderThanks wrote to #modal; they write to rfHost(), which is the row's box while the Rate
page is open with a form and #modal everywhere else. startRate decides: on the Rate page it is inline, anywhere else the old modal.

ENTRY POINTS (each kept working):
  top Rate tab, phone Rate tab, command palette "Rate a professor", Home "Rate a professor" + the landing's "Rate them", finals-week
  banner, Champ's "rate" place, ?tab=rate, a sign-in started for rating (authHandoff 'rate') ..... openRate() -> the Rate page.
  a professor's page (Leave a review, the unlock card), Past classes' Rate buttons, Home's Rate on a professor row (hmRateInstructor),
  Champ's "rate <professor>" action (startRate), "Review someone else" on the unlock card (the old picker), Settings > Your
  reviews > Edit (myrEdit) .... startRate from anywhere but the Rate page: the existing form in a modal, in place, as before.
  On the Rate page: Rate buttons, the thank-you's "Your other professors", Edit in the rail, the sign-in resume ..... inline.
  Notifications: the website's bell has no rating items, so nothing to route.

Usage: python3 rate-page-2026-10-16.py <repo>      (no build stamp - the coordinator stamps at merge)
"""
import sys, os, pathlib
root = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else '.')
f = root / 'index.html'
s = f.read_text()
if 'rate-page (2026-10-16)' in s:
    sys.exit('already patched')


def one(old, new):
    global s
    n = s.count(old)
    assert n == 1, (n, old[:140])
    s = s.replace(old, new)


# ---------------------------------------------------------------- the page's markup, before the old picker
one("""<!-- ============ REVIEW-A-PROFESSOR PICKER ============ -->""",
    """<!-- rate-page (2026-10-16): the Rate tab is a page now -->
<main class="view" id="view-rate">
  <div class="wrap">
    <div class="rt-head">
      <div><h2 class="rt-title">Rate</h2><p class="rt-sub">Your reviews help the next student pick the right professor.</p></div>
      <div class="rt-prog" id="rtProg"></div>
    </div>
    <div class="rt-grid">
      <div class="rt-main" id="rtMain"></div>
      <aside class="rt-rail" id="rtRail" aria-label="Your reviews"></aside>
    </div>
  </div>
  <div class="rt-scrim" onclick="rtClose()"></div>
</main>

<!-- ============ REVIEW-A-PROFESSOR PICKER ============ -->""")

# ---------------------------------------------------------------- show(): the tab, history (it goes through show), leaving
one("""const map={home:'tab-home',sched:'tab-sched',explore:'tab-explore',watch:'tab-watch',friends:'tab-friends','class':'tab-explore',prof:'tab-explore'};""",
    """const map={home:'tab-home',sched:'tab-sched',explore:'tab-explore',watch:'tab-watch',friends:'tab-friends',rate:'tab-rate','class':'tab-explore',prof:'tab-explore'};""")
one("""const mmap={home:'mtab-home',sched:'mtab-sched',explore:'mtab-explore',watch:'mtab-watch',friends:'mtab-friends',past:'mtab-friends','class':'mtab-explore',prof:'mtab-explore'};""",
    """const mmap={home:'mtab-home',sched:'mtab-sched',explore:'mtab-explore',watch:'mtab-watch',friends:'mtab-friends',rate:'mtab-rate',past:'mtab-friends','class':'mtab-explore',prof:'mtab-explore'};""")
one("""  if(v==='friends'&&typeof renderFriends==='function')renderFriends();
  if(v==='past'){""",
    """  if(v==='friends'&&typeof renderFriends==='function')renderFriends();
  if(v==='rate'&&typeof rtEnter==='function')rtEnter();   /* rate-page (2026-10-16) */
  if(v==='past'){""")
one("""  /* Past Classes + Watchlist now live inside the Schedule hub */
  /* These two delegate""",
    """  /* rate-page (2026-10-16): leaving the Rate page puts away an open review form (its draft is saved by the form itself) */
  if(v!=='rate'&&typeof rtLeave==='function'){ try{ rtLeave(); }catch(e){} }
  /* Past Classes + Watchlist now live inside the Schedule hub */
  /* These two delegate""")

# ---------------------------------------------------------------- openRate: the page (the old picker stays as the fallback)
one("""  // The picker modal is the purpose-built path; fall back to Explore search if
  // it's somehow unavailable.
  if(typeof openReviewLanding""",
    """  /* rate-page (2026-10-16): the Rate tab is a page (#view-rate). The picker modal below is only the fallback now. */
  if(document.getElementById('view-rate')){ show('rate'); return; }
  // The picker modal is the purpose-built path; fall back to Explore search if
  // it's somehow unavailable.
  if(typeof openReviewLanding""")

# ---------------------------------------------------------------- startRate: inline on the Rate page, the modal everywhere else
one("""  var _mb=document.getElementById('mback');
  if(_mb&&!_mb.classList.contains('open')){_mb.classList.add('open');document.body.style.overflow='hidden';}
  if(!eduVerified){rateAuthGate(id,course);return;}""",
    """  var _inl=(typeof rtWantInline==='function')&&rtWantInline(id);   /* rate-page (2026-10-16): on the Rate page the form opens under the row */
  var _mb=document.getElementById('mback');
  if(!_inl&&_mb&&!_mb.classList.contains('open')){_mb.classList.add('open');document.body.style.overflow='hidden';}
  if(!eduVerified){rateAuthGate(id,course);return;}
  if(_inl)rtOpenInline(id,course);""")

# ---------------------------------------------------------------- the form and its thank-you draw into rfHost()
one("""  document.getElementById('modal').innerHTML=`<div class="rate-wrap"><button class="mclose" onclick="rateExit()">&times;</button>""",
    """  rfHost().innerHTML=`<div class="rate-wrap"><button class="mclose" onclick="rateExit()" aria-label="Close">&times;</button>""")
one("""  document.getElementById('modal').innerHTML=`<div class="rate-wrap"><div class="rate-step center">""",
    """  rfHost().innerHTML=`<div class="rate-wrap"><div class="rate-step center">""")
one("""    <button class="rate-skip" onclick="closeModal()">Done</button></div></div>`;
}""",
    """    <button class="rate-skip" onclick="rateDone()">Done</button></div></div>`;
  try{ if(typeof rtOn==='function'&&rtOn())rtAfterPost(); }catch(e){}   /* rate-page (2026-10-16) */
}""")
one("""function rateExit(){
  closeModal(); modalMode='profile';""",
    """function rateExit(){
  if(typeof rtOn==='function'&&rtOn()){ rtClose(); return; }   /* rate-page (2026-10-16): the form is in the Rate page's row */
  closeModal(); modalMode='profile';""")
one("""function goProfFromRate(){
  closeModal(); modalMode='profile';""",
    """function goProfFromRate(){
  if(typeof rtOn==='function'&&rtOn())rtClose(true);   /* rate-page (2026-10-16) */
  closeModal(); modalMode='profile';""")

# ---------------------------------------------------------------- ?tab=rate, analytics surface, auth repaint, Home's recent reviews
one("""var allowed=['home','sched','explore','friends','past','watch','settings'];""",
    """var allowed=['home','sched','explore','friends','rate','past','watch','settings'];""")
one("""past:'Past classes','class':'Class',prof:'Professor',settings:'Settings'};""",
    """past:'Past classes','class':'Class',prof:'Professor',settings:'Settings',rate:'Rate'};""")
one("""  /* Delete-account only exists for a signed-in account; sign out and it goes away. */
  try{ if(typeof refreshDangerZone==='function')refreshDangerZone(); }catch(e){}""",
    """  /* Delete-account only exists for a signed-in account; sign out and it goes away. */
  try{ if(typeof refreshDangerZone==='function')refreshDangerZone(); }catch(e){}
  try{ if(typeof rtAuthChanged==='function')rtAuthChanged(); }catch(e){}   /* rate-page (2026-10-16) */""")
one("""window.hmRenderFeed=hmRenderFeed; window.hmRetryFeed=hmRetryFeed; window.hmArmFeedTimeout=hmArmFeedTimeout;""",
    """window.hmRenderFeed=hmRenderFeed; window.hmRetryFeed=hmRetryFeed; window.hmArmFeedTimeout=hmArmFeedTimeout;
    window.hmRecentsGet=function(){ return HM_RECENTS; };   /* rate-page (2026-10-16): the Rate page's "Latest reviews" reads what Home already loaded */""")

# ---------------------------------------------------------------- the block: CSS + the page's script
BLOCK = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'rate-page-2026-10-16.block.html')).read()
one("</body>", BLOCK + "</body>")

f.write_text(s)
print('patched', f)
