#!/usr/bin/env python3
"""The website in the app's look, pass 2: Schedule's layout (Tate, 2026-10-04: "okay get to work now on each
screens layout"). The canvas's Schedule artboard, within what Schedule already promises.

What stays, on purpose: the left column. Tate asked for professors on BOTH sides of the week (2026-09-10:
"put some professors on the left (under my planner) to space them out"), and those cards stand in the empty
part of the tab column — so the tabs stay a column rather than becoming the canvas's underline row, which
would take the left lane away. Everything else moves to the app:

  - the title is the app's large left-aligned heading; the column's tabs are the app's pills (the active one
    in the soft blue the top bar uses), lined up with the page edge now that the page is 1240px.
  - List / Schedule is the app's segmented switch; "Add a class" is a soft pill and "Share schedule" the
    solid one.
  - the week is the app's card: white, rounded, soft day columns with a gap between them (the faint hour
    rules stay — on a full week they are how you read a time), the app's heavy day labels.
  - the professor cards beside the week are the app's cards with the app's rating circles.

Usage: python3 desktop-sched-layout-2026-10-04.py <repo-dir>   (after desktop-class-layout-2026-10-04.py)
"""
import sys, os
d = sys.argv[1]
p = os.path.join(d, 'index.html')
s = open(p, encoding='utf-8').read()
if 'APP-LAYOUT-CLASS 2026-10-04' not in s: sys.exit('run desktop-class-layout-2026-10-04.py first')
if 'APP-LAYOUT-SCHED 2026-10-04' in s: sys.exit('already patched')

CSS = """<style id="app-layout-sched">
/* ================================================================================================
   APP-LAYOUT-SCHED 2026-10-04 — Schedule in the app's layout (the canvas's Schedule artboard).
   ================================================================================================ */
#view-sched .phead.sched-tag{text-align:left;padding:22px 0 16px;margin:0;justify-self:stretch;width:auto}
#view-sched .phead.sched-tag h2{font-size:34px;font-weight:900;letter-spacing:-.02em;color:var(--text)}
#view-sched .sched-term{font-size:14px;font-weight:900;letter-spacing:.04em;color:var(--muted)}
@media (min-width:900px){
  #view-sched > .wrap > .wl-tabs{margin-left:0;gap:4px}
  #view-sched > .wrap > .wl-tabs .wl-tab{padding:12px 14px;border-radius:16px;font-size:16px;font-weight:900;color:var(--muted)}
  #view-sched > .wrap > .wl-tabs .wl-tab.on{background:var(--blue-soft);color:var(--tab-on);box-shadow:none}
  #view-sched > .wrap > .wl-tabs .wl-tab.on span{background:var(--panel);color:var(--tab-on)}
}
@media (max-width:899px){
  #view-sched .wl-tab{font-weight:900}
  #view-sched .wl-tab.on{color:var(--tab-on);border-bottom-color:var(--accent);border-bottom-width:3px}
}

/* the switch and the two actions */
#view-sched .mc-viewtog{background:var(--panel);border:0;border-radius:22px;padding:4px;box-shadow:var(--card-sh);gap:2px}
#view-sched .mc-viewtog button{height:36px;padding:0 16px;border:0;border-radius:18px;font-size:14px;font-weight:900;color:var(--muted);background:none}
#view-sched .mc-viewtog button.on{background:var(--clsblk);color:var(--clsblk-ink);box-shadow:0 4px 12px rgba(37,99,235,.25)}
#view-sched .mc-act{height:40px;padding:0 16px;border:0;border-radius:99px;font-size:14px;font-weight:900;background:var(--blue-soft);color:var(--tab-on);box-shadow:none}
#view-sched .mc-act:not(.mc-addbtn){background:var(--clsblk);color:var(--clsblk-ink);box-shadow:0 6px 16px rgba(37,99,235,.25)}
:root[data-theme="dark"] #view-sched .mc-act:not(.mc-addbtn),:root[data-theme="dark"] #view-sched .mc-viewtog button.on{box-shadow:none}

/* the week: the app's card, soft day columns */
#view-sched .cal-wrap:not(.cal-mini){border:0;border-radius:24px;background:var(--panel);box-shadow:var(--card-sh);padding:14px 16px 16px;gap:8px}
#view-sched .cal-wrap:not(.cal-mini) .cal-times{border:0}
#view-sched .cal-wrap:not(.cal-mini) .cal-col{border:0}
#view-sched .cal-wrap:not(.cal-mini) .cal-dh{background:none;border:0;font-size:13px;font-weight:900;letter-spacing:.06em;color:var(--muted)}
#view-sched .cal-wrap:not(.cal-mini) .cal-hr{font-size:12px;font-weight:800;color:var(--faint)}
/* a tint, not a fill: the professor connectors run UNDER the day columns and must stay whole across them */
#view-sched .cal-wrap:not(.cal-mini) .cal-day{background-color:rgba(var(--fg-rgb),.035);border-radius:14px}
#view-sched .cal-wrap:not(.cal-mini) .cal-any{border:0;background:none}
#view-sched .cal-wrap:not(.cal-mini) .cal-anyday{background-color:transparent}
#view-sched .cal-wrap:not(.cal-mini) .cal-block{border-radius:10px;box-shadow:none}
#view-sched .cal-wrap:not(.cal-mini) .cal-block .cb-code{font-weight:900}
#view-sched .cal-wrap:not(.cal-mini) .cal-block .cb-nm{font-weight:800}
#view-sched .cal-key{font-size:13px;font-weight:700}
/* between 900 and 1139px the professor cards stand beside a narrower week: give the days the room back */
@media (max-width:1139px){
  #view-sched .cal-wrap:not(.cal-mini){padding:12px 8px 12px;gap:2px}
  #view-sched .cal-wrap:not(.cal-mini) .cal-block .cb-code{font-size:12px}
}

/* the professor cards beside the week */
#view-sched .hz-card{border:0;border-radius:18px;box-shadow:var(--card-sh)}
#view-sched .hz-av{border-radius:50%;font-weight:900}
#view-sched .hz-nm{font-weight:900}
#view-sched .hz-dept{font-weight:800;color:var(--muted)}

/* the notes under it */
#view-sched .wl-insight{border:0;border-radius:20px;background:var(--panel);box-shadow:var(--card-sh)}
#view-sched .mc-reimport{font-weight:900;color:var(--tab-on)}

/* Plans and Planner (the Plans module): the same card, columns and pills */
#view-sched .pl3-pill{border:0;border-radius:18px;background:var(--panel);box-shadow:var(--card-sh)}
#view-sched .pl3-pill b{font-weight:900}
#view-sched .pl3-pill.on{background:var(--blue-soft);box-shadow:inset 0 0 0 2px var(--accent)}
#view-sched .pl3-pill.on b{color:var(--tab-on)}
#view-sched .pl3-week{background:var(--panel);border-radius:24px;box-shadow:var(--card-sh);padding:14px 16px 16px}
#view-sched .pl3-head,#view-sched .pl3-grid{gap:8px}
#view-sched .pl3-head span{font-size:13px;font-weight:900;letter-spacing:.06em;text-transform:uppercase;color:var(--muted)}
#view-sched .pl3-gut span{font-size:12px;font-weight:800;color:var(--faint)}
#view-sched .pl3-col{border:0;border-radius:14px;background:rgba(var(--fg-rgb),.035)}
#view-sched .pl3-line{border-top-color:rgba(var(--fg-rgb),.06)}
#view-sched .pl3-need,#view-sched .pl3-search input{border:0;border-radius:16px;box-shadow:var(--card-sh)}
#view-sched .pl3-need.on{box-shadow:inset 0 0 0 2px var(--accent)}
</style>
"""
if s.count('</body>') != 1: sys.exit('body end')
s = s.replace('</body>', CSS + '</body>')
open(p, 'w', encoding='utf-8').write(s)
print('patched', p)
