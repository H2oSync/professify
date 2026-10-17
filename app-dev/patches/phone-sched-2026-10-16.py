#!/usr/bin/env python3
"""phone-sched, 2026-10-16 (index.html only; no build stamp). Schedule > My classes and Schedule > Plans on a phone (<= 640px).

My classes (the student's own week, renderMyCalendar opts.cm === 'me'): on a phone the week is a little taller (0.96 px/min,
a 50-minute class is 48px; the crop to the hours actually used stays) and each block spends its height the same way the
desktop's tall week does: the code, then as many lines of the name as fit (up to two), measured from the real code height
(the phone stacks the code in two lines). A block that is one line short goes compact (2px padding) to win the second line.
Side padding is 4px so a column of ~50px holds a word of the name; a long word breaks instead of being cut.
Plans (<= 520px): the week is hrs x 56px tall instead of a flat 440px, a block shows its code and as many lines of the name
as fit (hvFit's measurement, now also on a phone), the time stays off a phone. 521-640px already had names (64px/h).
Desktop (> 640px), a friend's week, the Home friend cards, the friend modal and the Planner's week are not touched: every
change is behind `_ph` (own week and innerWidth <= 640), the .cb-ph class, or a max-width:520px media rule on a non-edit week.
Replay: python3 phone-sched-2026-10-16.py <repo root>
"""
import sys, pathlib
root = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else '.')
f = root / 'index.html'
s = f.read_text()
if 'phone-sched (2026-10-16)' in s:
    sys.exit('already patched')


def one(old, new):
    global s
    n = s.count(old)
    assert n == 1, (n, old[:140])
    s = s.replace(old, new)


# ---- My classes: the scale and the per-block budget ----
one("""  if(_tall)PPM=0.92;
""", """  if(_tall)PPM=0.92;
  /* phone-sched (2026-10-16): on a phone the owner's own week is a little taller too (a 50-minute class = 48px), so the name has a
     line or two under the code instead of "Introdu to...". The phone stacks the code in two lines (about 22px). */
  var _ph=(opts.cm==='me'&&typeof window!=='undefined'&&window.innerWidth<=640);
  if(_ph)PPM=0.96;
""")
one("var room=h-6-(_tall?16:13);", "var room=h-6-(_ph?22:(_tall?16:13));")
one("var nmLines=Math.max(0,Math.min(2,Math.floor(room/12)));", "var nmLines=Math.max(0,Math.min(2,Math.floor(room/(_ph?11:12))));")
one("        if(nmLines===0&&(h-4-13)>=10){ tight=true; nmLines=1; }",
    "        if(_ph){ var _n2=Math.max(0,Math.min(2,Math.floor((h-4-22)/11))); if(_n2>nmLines){ tight=true; nmLines=_n2; } }   /* phone-sched: compact padding buys the second line */\n"
    "        else if(nmLines===0&&(h-4-13)>=10){ tight=true; nmLines=1; }")
one("var nmLH=tight?10:12;", "var nmLH=_ph?11:(tight?10:12);")
one("+(_tall?';line-height:12px':'')+", "+(_tall?';line-height:12px':(_ph?';line-height:11px':''))+")
one("""html+='<div class="cal-block cb-tap'+(tight?' cb-tight':'')+""", """html+='<div class="cal-block cb-tap'+(_ph?' cb-ph':'')+(tight?' cb-tight':'')+""")

# ---- Plans on a phone: measured name lines (the same fit() as a laptop) ----
one("    var phone=false; try{ phone=!!(window.matchMedia&&matchMedia('(max-width:520px)').matches); }catch(e){}\n", "")
one("      if(phone){ w.style.display=''; w.style.maxHeight=''; return; }\n", "")

# ---- CSS ----
one("""/* on a phone the columns are ~50px wide: code only, as before */
@media (max-width:520px){.pl3-blk .pl3-nmw{display:none}}
""", """/* phone-sched (2026-10-16). A phone: the columns are ~50px wide, so the Plans week is taller (the hours it uses x 56px, not a flat 440px),
   a block shows its code and as many lines of the name as fit (measured in hvFit, never guessed), and no time line (tap the class for it).
   The Planner's week (--edit) keeps its code-only blocks. */
@media (max-width:520px){
  #view-sched .pl3-week:not(.pl3-week--edit) .pl3-grid{height:calc(var(--pl3-hrs,10) * 56px)}
  #view-sched .pl3-week:not(.pl3-week--edit){padding-left:8px;padding-right:8px}
  .pl3-week:not(.pl3-week--edit) .pl3-blk{padding:3px}
  .pl3-week:not(.pl3-week--edit) .pl3-blk .pl3-nm{font-size:var(--t-micro);line-height:1.15;letter-spacing:-.01em;overflow-wrap:anywhere;hyphens:auto}
  .pl3-week:not(.pl3-week--edit) .pl3-blk b{font-size:var(--t-micro);letter-spacing:-.02em}
}
/* My classes on a phone (the block carries .cb-ph): the code at the size the budget is counted for, a little less side padding, a long word breaks */
@media (max-width:640px){
  .cal-wrap .cal-block.cb-ph{padding-left:3px;padding-right:3px}
  .cal-wrap .cal-block.cb-ph .cb-code{font-size:var(--t-micro)!important;line-height:1.12}
  .cal-wrap .cal-block.cb-ph .cb-nmc{letter-spacing:-.01em;overflow-wrap:anywhere;hyphens:auto}
}
""")

# ---- 561-640px: the Time TBA / async rail was told to take a whole row (max-width:640px) but the row only wrapped at <= 560px, so on
# a 561-640px screen the five day columns collapsed to 0 and the rail took the whole week. Wrap at the same 640 line. ----
one("""@media (max-width:560px){
  .cal-wrap{flex-wrap:wrap}""", """@media (max-width:640px){   /* phone-sched: was 560, but the rail's 100% width applies at 640 */
  .cal-wrap{flex-wrap:wrap}""")

f.write_text(s)
print('patched', f)
