#!/usr/bin/env python3
"""Small fixes found by LOOKING at the new surfaces (night of 2026-10-13/14), after the suites were green.

- Builder tap targets: the + on a tile was 30px, "Why it's #N" 19px, the up/down arrows 28px, the Plan A/B/C
  buttons 34px, "Past classes" 33px, Draft my plans 43px, the units box 32px. dev/check-plans.mjs ("every plan
  button ... at least 44px tall") only passed because it measured them while the Builder was hidden; measured
  properly it failed. Now: the wide controls are 44px tall, and the small ones keep their look with an invisible
  44px hit area (::after) — the check counts that.

- Replace dialog (dark): "Keep both" was the browser-grey default button (the one-off .btn had no theme on it) next
  to a blue Replace; it now takes the panel colours, like the Registration day dialog's second button.
- The enroll / Replace dialog's × (a phone-width rule makes .mclose position:relative with right:22px, so it
  slid left onto "ADD TO MY CLASSES") is back in the top-right corner.
- Plan chooser's clash panel: "Replace BUS 3438 with this class" / "Keep both" read as two lines of plain text;
  Replace now carries the accent tint and Keep both a hairline, so both read as buttons (still 44px tall).
- The test harness served .css as application/octet-stream, so hawk-ask.css never loaded in any suite and Hawk was
  only ever tested unstyled; app-dev/tests/app-harness.mjs now serves text/css.

- Home stories read window.cmBlocks(friendId) as {days:[..], s, e}; the commitments slice's cmBlocks returns the
  meet-shaped {meet:{days,start,end}} the weeks draw, so every block was skipped there (and the home test's stand-in,
  set in init, was replaced by the real one at load, so it failed on the integrated base too). The stories now read
  both shapes. (A friend's Busy also arrives through gpMemberBusy; the same stretch twice changes nothing.)

Usage: python3 website-polish-2026-10-14.py <repo>
"""
import sys, pathlib
root = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else '.')
f = root / 'index.html'
s = f.read_text()
if 'website-polish (2026-10-14)' in s:
    sys.exit('already patched')

def one(old, new):
    global s
    n = s.count(old)
    assert n == 1, (n, old[:120])
    s = s.replace(old, new)

# 1. Builder tap targets
one(".bd-more{font:inherit;font-size:13px;font-weight:700;color:var(--accent);background:none;border:0;padding:8px 0 0;cursor:pointer}",
    ".bd-more{font:inherit;font-size:13px;font-weight:700;color:var(--accent);background:none;border:0;padding:8px 0 0;cursor:pointer}\n"
    "/* website-polish (2026-10-14): 44px to touch — real height on the wide controls, an invisible hit area on the small ones */\n"
    ".bd-slot,.bd-past,.bd-go,.bd-ur select{min-height:44px}\n"
    ".bd-why,.bd-mv{position:relative}\n"
    ".bd-why::after,.bd-mv::after,.bd-add::after{content:'';position:absolute;inset:-8px}\n"
    ".bd-slot.on{color:var(--blue-ink)}\n"
    ".bd-why::after{inset:-13px -6px}\n"
    ".bd-mv::after{inset:-8px -2px}")

# 2. the Replace dialog's second button and the chooser's clash rows
one(".en-clash-acts{margin-top:14px;gap:8px;flex-wrap:wrap}",
    ".en-clash-acts{margin-top:14px;gap:8px;flex-wrap:wrap}\n"
    "/* website-polish (2026-10-14) */\n"
    ".en-clash-acts .btn:not(.primary){background:var(--panel-2);border:1px solid var(--line);color:var(--text)}\n"
    "#campusBanner .btn:not(.primary){background:var(--panel-2);border-color:var(--line);color:var(--text)}   /* the banner's second button was the browser grey in dark */\n"
    "#enrollModal{position:relative}\n"
    "#enrollModal .mclose{position:absolute;top:14px;right:14px;left:auto;z-index:3}")
one(".pl2-chi--go{white-space:normal;text-align:left;line-height:1.3;font-weight:700}",
    ".pl2-chi--go{white-space:normal;text-align:left;line-height:1.3;font-weight:700}\n"
    "#plChoose .pl2-chi--go{background:var(--accent-dim);color:var(--blue-ink)}\n"
    "#plChoose .pl2-clash ~ .pl2-chi:not(.pl2-chi--go){border:1px solid var(--line);margin-top:4px;font-weight:700}")

# 3. Home stories: a friend's commitments, in the shape cmBlocks really returns
one("      if(!b||b.s==null||b.e==null)return;\n      (b.days||[]).forEach(function(d){ if(HM_BLKDAY[d]!=null)cm.push({di:HM_BLKDAY[d],s:b.s,e:b.e}); });",
    "      var bs=b&&(b.meet?b.meet.start:b.s), be=b&&(b.meet?b.meet.end:b.e), bd=b&&(b.meet?b.meet.days:b.days);   /* website-polish (2026-10-14): both shapes */\n      if(!b||bs==null||be==null)return;\n      (bd||[]).forEach(function(d){ if(HM_BLKDAY[d]!=null)cm.push({di:HM_BLKDAY[d],s:bs,e:be}); });")
f.write_text(s)
print('ok')
