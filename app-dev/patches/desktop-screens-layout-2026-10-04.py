#!/usr/bin/env python3
"""The website in the app's look, pass 2: the remaining screens' layouts — Explore, a professor's page,
Friends, the Rate sheet, Settings and the signed-out landing page (Tate, 2026-10-04: "okay get to work now on
each screens layout").

Each keeps its structure and every control; each moves to the app's layout language:
  - Explore: the app's large left-aligned question, a white 56px search bar, the filters and the
    Classes / Professors switch as the app's pill switches, each result as the app's 22px card with the
    course name in black, the right column's cards in the app's 18px titles.
  - a professor's page: the app's PURPLE hero (the app's professor colour) with the rating circle, the
    name in 32px black, and the score in a white tile whose stars are the rating's own colour (they were
    always gold); the actions as the app's pills; "Teaching this term" and the stats as app cards.
  - Friends: the one big panel opens up into the app's separate cards on the page (requests, messages,
    your friends), the title in the app's 34px black.
  - the Rate sheet: each professor as the app's soft-purple row, the name in purple, round initials.
  - Settings: the app's heading and pill tabs (the left edge bar goes, as on Schedule).
  - the landing page: the app's cards (no hairline, soft shadow, 24px), black titles.

Usage: python3 desktop-screens-layout-2026-10-04.py <repo-dir>   (after desktop-sched-layout-2026-10-04.py)
"""
import sys, os
d = sys.argv[1]
p = os.path.join(d, 'index.html')
s = open(p, encoding='utf-8').read()
if 'APP-LAYOUT-SCHED 2026-10-04' not in s: sys.exit('run desktop-sched-layout-2026-10-04.py first')
if 'APP-LAYOUT-SCREENS 2026-10-04' in s: sys.exit('already patched')

R = [
 # a professor's stars take the rating's own colour (the app's), not a fixed gold
 ("""  var head='<div class="pp-head">'
    +'<div class="pp-av" style=\"""",
  """  var head='<div class="pp-head" style="--rcf:'+((five!=null&&typeof scoreColor==='function')?scoreColor((five/5)*4,'fill'):'var(--faint)')+'">'
    +'<div class="pp-av" style=\""""),
]
for a, b in R:
    if s.count(a) != 1: sys.exit(f'anchor matched {s.count(a)}x: {a[:90]}')
    s = s.replace(a, b)

CSS = """<style id="app-layout-screens">
/* ================================================================================================
   APP-LAYOUT-SCREENS 2026-10-04 — Explore, a professor, Friends, Rate, Settings and the landing page
   in the app's layout.
   ================================================================================================ */

/* ---- Explore ---- */
#view-explore .ex-q{font-size:34px;font-weight:900;letter-spacing:-.02em;margin:22px 0 14px}
#view-explore .ex-spot{background:var(--panel);border:0;border-radius:22px;box-shadow:var(--card-sh);min-height:56px;padding:0 20px}
#view-explore .ex-spot input{font-size:16px;font-weight:700}
#view-explore .ex-gesw{background:var(--panel);border:0;border-radius:22px;padding:4px;box-shadow:var(--card-sh);gap:2px}
#view-explore .ex-gesw button{border:0;border-radius:18px;padding:7px 16px;font-size:14px;font-weight:900;color:var(--muted);background:none;box-shadow:none}
#view-explore .ex-gesw button.on{background:var(--blue-soft);color:var(--tab-on);box-shadow:none}
#view-explore .ex-seg-v{background:var(--panel);border:0;border-radius:22px;box-shadow:var(--card-sh)}
#view-explore .ex-seg-v button{font-weight:900}
#view-explore .ex-hl{font-size:12px;font-weight:900;letter-spacing:.1em;color:var(--muted)}
#view-explore .cls-row{border:0;border-radius:22px;box-shadow:var(--card-sh);padding:16px 18px}
#view-explore .cls-row .nm{font-size:16px;font-weight:900;color:var(--text)}
#view-explore .cx-facts{font-weight:700}
#view-explore .cx-foot{border-top-color:var(--line-soft)}
#view-explore .ex-mod{border:0;border-radius:24px;box-shadow:var(--card-sh);padding:18px 18px 14px}
#view-explore .exm-h h3{font-size:18px;font-weight:900}
#view-explore .exm-f{border:0;border-radius:14px;background:var(--blue-soft);color:var(--tab-on);font-weight:900;min-height:42px}

/* ---- a professor's page: the app's purple hero ---- */
#view-prof .pp-head{background:#7C3AED;color:#fff;border:0;border-radius:28px;padding:26px 28px;box-shadow:0 14px 30px rgba(124,58,237,.25);align-items:center}
:root[data-theme="dark"] #view-prof .pp-head{background:#6D28D9;box-shadow:0 14px 30px rgba(0,0,0,.4)}
#view-prof .pp-av{width:70px;height:70px;border-radius:50%;font-size:22px;font-weight:900;border:0;box-shadow:0 0 0 3px rgba(255,255,255,.35)}
#view-prof .pp-id h2{color:#fff;font-size:32px;font-weight:900;letter-spacing:-.02em}
#view-prof .pp-dept{color:#fff;opacity:.92;font-size:15px;font-weight:800}
#view-prof .pp-score{background:var(--panel);border-radius:20px;padding:14px 18px;box-shadow:0 6px 18px rgba(46,16,101,.18)}
#view-prof .pp-score .pr-st .pr-f svg path{fill:var(--rcf)}
#view-prof .pp-num{font-size:32px;font-weight:900}
#view-prof .pp-n{font-weight:800;color:var(--muted)}
#view-prof .pp-jump{font-weight:900;color:var(--tab-on)}
#view-prof .pp-none{color:var(--muted);font-weight:800}
#view-prof .pp-acts{gap:10px;margin-top:16px}
#view-prof .pp-acts .btn.primary{border-radius:99px;font-weight:900;min-height:46px;padding:0 20px}
#view-prof .pp-act,#view-prof .psug-btn{border:0;border-radius:99px;background:var(--panel);box-shadow:var(--card-sh);font-weight:900;min-height:44px;padding:0 16px}
#view-prof .pp-sec h3{font-size:18px;font-weight:900;letter-spacing:0;text-transform:none;color:var(--text)}
#view-prof .pp-secs{border:0;border-radius:22px;box-shadow:var(--card-sh);background:var(--panel);overflow:hidden}
#view-prof .pp-row{border:0;border-top:1px solid var(--line-soft);padding:14px 16px}
#view-prof .pp-row:first-child{border-top:0}
#view-prof .pp-cn{font-weight:900;color:var(--text)}
#view-prof .pp-when{font-weight:800}
#view-prof .pp-seat{font-weight:900}
#view-prof .pp-fri{border:0;border-radius:18px;box-shadow:var(--card-sh)}
#view-prof .pp-detail > div > div,#view-prof .pp-detail [style*="border:1px solid"]{border-radius:20px}

/* ---- Friends: the panel opens into the app's cards ---- */
@media (min-width:1140px){ #view-friends > .wrap{max-width:1240px} }
#view-friends .frv2{background:transparent;border:0;box-shadow:none;padding:6px 0 0}
#view-friends .frv2-head h2{font-size:34px;font-weight:900;letter-spacing:-.02em}
#view-friends .frv2-card{border:0;border-radius:22px;box-shadow:var(--card-sh);background:var(--panel)}
#view-friends .frv2-card .ini,#view-friends .fr-row .ini{font-weight:900}
#view-friends .fr-card.msg-card{border:0;border-radius:24px;box-shadow:var(--card-sh)}
#view-friends .fr-seck,#view-friends .frv2-lhk{font-size:12px;font-weight:900;letter-spacing:.1em;color:var(--muted)}
#view-friends .frv2-list{background:var(--panel);border-radius:24px;box-shadow:var(--card-sh);padding:4px 18px}
#view-friends .frv2-list .fr-row{padding:14px 0}
#view-friends .fr-rowmain .nm,#view-friends .fr-row .fr-nm,#view-friends .frv2-cmain b,#view-friends .fr-row b:first-child{font-weight:900}
#view-friends .fr-msgbtn{border:0;border-radius:99px;background:var(--blue-soft);color:var(--tab-on);font-weight:900}
#view-friends .fr-fold{font-weight:700}

/* ---- the Rate sheet: the app's soft-purple professor rows ---- */
#rlLists > div:not(.rl-term):not(:first-child){background:#F3EEFF!important;border:0!important;border-radius:18px!important}
:root[data-theme="dark"] #rlLists > div:not(.rl-term):not(:first-child){background:#271F42!important}
#rlLists > div:not(.rl-term):not(:first-child) > div:first-child > div:first-child{border-radius:50%!important;font-weight:900!important}
#rlLists > div:not(.rl-term):not(:first-child) > div:first-child > div:last-child > div:first-child{color:#5B21B6!important;font-weight:900!important;font-size:16px!important}
:root[data-theme="dark"] #rlLists > div:not(.rl-term):not(:first-child) > div:first-child > div:last-child > div:first-child{color:#CDB9FF!important}
#rlLists > div:not(.rl-term):not(:first-child) > div:first-child > div:last-child > div:last-child{font-style:normal!important;font-weight:800!important}
#rlLists > div:not(.rl-term):not(:first-child) > div:last-child > span:first-child{border-radius:99px!important;padding:5px 12px!important;font-weight:900!important}
#rlLists > div:not(.rl-term):not(:first-child) > div:last-child > span:last-child{border-radius:99px!important;font-weight:900!important;border:0!important;background:var(--panel)!important}
#rlBack .rl-filters input,#rlBack .rl-namein,#rlBack .selwrap select{border-radius:14px!important}

/* ---- Settings ---- */
#view-settings .st-nav-h{font-size:34px;font-weight:900;letter-spacing:-.02em}
#view-settings .st-tab{border-radius:16px;font-size:15px;font-weight:900;color:var(--muted)}
#view-settings .st-tab.on{background:var(--blue-soft);color:var(--tab-on)}
#view-settings .st-tab.on::before{display:none}
#view-settings .st-card{border:0;border-radius:24px;box-shadow:var(--card-sh)}
#view-settings .st-h{font-size:20px;font-weight:900}

/* ---- the landing page ---- */
#homeLanding .lp-card,#homeLanding .lp-pill{border:0;border-radius:24px;box-shadow:var(--card-sh)}
#homeLanding .lp-pill-h,#homeLanding .lp-ch{font-weight:900}
#homeLanding .lp-lrow{border-bottom-color:var(--line-soft)}
#homeLanding .lp-rate{border:0;box-shadow:var(--card-sh);background:var(--panel);font-weight:800}
</style>
"""
if s.count('</body>') != 1: sys.exit('body end')
s = s.replace('</body>', CSS + '</body>')
open(p, 'w', encoding='utf-8').write(s)
print('patched', p)
