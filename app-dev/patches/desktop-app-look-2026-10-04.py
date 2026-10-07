#!/usr/bin/env python3
"""The website in the app's look, pass 1 (Tate, 2026-10-04).

Tate: "I want to take the UI and UX of the current app/mobile design and bring that same design language
into the desktop version. The goal is for the desktop site to feel like the same product as the app—not
like two separate designs ... just work on the index html first." Then, on the canvas "Desktop in the App's
Look": "looks good but lets keep the toolbar off to the right side where it is right now", and "build it in
light but have a dark option".

Pass 1 is the LOOK on every screen; each screen's layout follows in later passes. This patch:
  - themes: LIGHT is the default (it was dark). Dark stays as the one option. Cream is retired: a saved
    'cream' reads as light, and Settings offers Light / Dark only.
  - tokens: the app's palette (page #F4F6FB, white cards, ink #0F172A, blue #2563EB as the one action
    colour) in light, and the canvas's dark palette in dark. The per-school accent no longer writes inline
    colours over them (applySchoolTheme keeps its bookkeeping only).
  - type: Nunito (the app's own embedded face, copied from app/index.html at patch time — no network),
    600 body, 800 headings; the type-scale tokens move up half a step for Nunito's smaller x-height.
  - cards: the app's white 20px cards with a soft shadow and no border.
  - the top bar: the app's tab style (icon in a pill, light-blue pill on the active tab), in the app's
    order with Rate added — Home · Explore · Rate · Schedule · Friends — kept on the RIGHT where the
    tabs are today; the mark plus the TermChamp wordmark on the left; bell and profile after a divider.
  - class blocks: the app's soft blue with dark-blue text (--clsblk, --pl3-blk).
  - ratings: scoreColor() moves to the app's ten-step half-star scale (--rt-1..10, dark text in light,
    the bright fill in dark); professor tiles take the app's fill and ink.

Usage: python3 desktop-app-look-2026-10-04.py <repo-dir>
"""
import sys, os, re
d = sys.argv[1]
p = os.path.join(d, 'index.html')
s = open(p, encoding='utf-8').read()
if 'APP-LOOK 2026-10-04' in s: sys.exit('already patched')
app = open(os.path.join(d, 'app', 'index.html'), encoding='utf-8').read()
m = re.search(r"@font-face\{font-family:'Nunito';[^}]*\}", app)
if not m: sys.exit("app/index.html: Nunito @font-face not found")
NUNITO = m.group(0)

# The app's ten half-star steps (app/index.html RATE_FILL / RATE_INKS / RATE_HUE).
FILL = ['#E46258', '#E26D50', '#E0793E', '#DD8A2C', '#CE9A22', '#BDAD1F', '#A0B41D', '#70AF1D', '#2EA71B', '#1AA248']
INK = ['#450C08', '#491508', '#492008', '#492B08', '#453208', '#453F08', '#394007', '#223706', '#0B2E05', '#052911']
HUE = [4, 12, 22, 32, 42, 54, 68, 86, 112, 140]
def dark_text(i):  # RATE_DARK: readable on white
    h = HUE[i]
    return '#166534' if i == 9 else f'hsl({h} 70% {18 if h < 40 else 22 if h <= 90 else 24}%)'
RT_LIGHT = ';'.join(f'--rt-{i+1}:{dark_text(i)}' for i in range(10))
RT_DARK = ';'.join(f'--rt-{i+1}:{FILL[i]}' for i in range(10))
RT_FILL = ';'.join(f'--rtf-{i+1}:{FILL[i]}' for i in range(10))   # shapes (dots, strokes) in both themes

TOKENS = """
/* ================================================================================================
   APP-LOOK 2026-10-04 — the website in the phone app's design language, pass 1 (Tate: "the goal is
   for the desktop site to feel like the same product as the app"). Its own <style> element, last in
   the page, so it wins the cascade without touching the 40k lines above; a later pass moves each
   screen's LAYOUT to the app's, this one moves the look. Light is the default; dark is the option;
   cream is retired (a stored 'cream' boots as light).
   ================================================================================================ */
""" + NUNITO + """
:root,:root[data-theme="light"],:root[data-theme="cream"]{
  --bg:#F4F6FB;--panel:#FFFFFF;--panel-2:#F4F6FB;--panel-3:#EDF0F5;
  --line:#E3E8F0;--line-soft:#EDF0F5;
  --text:#0F172A;--text-2:#334155;--muted:#5B6B80;--faint:#5F6E83;
  --mark-ring:rgba(15,23,42,.10);
  --accent:#2563EB;--accent-rgb:37,99,235;--accent-ink:#FFFFFF;--accent-dim:rgba(37,99,235,.10);
  --good:#15803D;--good-2:#15803D;--good-rgb:22,163,74;--good-ink:#166534;--mid:#B45309;--low:#B91C1C;--low-rgb:185,28,28;
  --fg-rgb:15,23,42;--nav-bg:rgba(255,255,255,.96);--radius:20px;
  --blue-ink:#1E40AF;--course:#1E40AF;--prof:#7C3AED;--prof-ink:#5B21B6;
  --clsblk:#2563EB;--clsblk-rgb:37,99,235;--clsblk-ink:#FFFFFF;
  --blk:#D6E4FF;--blk-ink:#1E40AF;--pl3-blk:#D6E4FF;--pl3-blk-ink:#1E40AF;
  --blue-soft:#E3ECFF;--tab-on:#1D4ED8;--navy:#16336B;--prof-fill:#7C3AED;
  --card-sh:0 1px 2px rgba(15,23,42,.04),0 10px 30px rgba(22,51,107,.06);
  --pop-sh:0 18px 44px rgba(22,51,107,.16);
  """ + RT_LIGHT + ';' + RT_FILL + """;
  color-scheme:light;
}
:root[data-theme="dark"]{
  --bg:#0B1120;--panel:#151D2E;--panel-2:#1C2639;--panel-3:#222D42;
  --line:#243049;--line-soft:#1E2840;
  --text:#EAF0F8;--text-2:#C9D3E3;--muted:#93A0B6;--faint:#8C99B0;
  --mark-ring:rgba(255,255,255,.22);
  --accent:#6EA0FF;--accent-rgb:110,160,255;--accent-ink:#0B1120;--accent-dim:rgba(110,160,255,.16);
  --good:#4ADE80;--good-2:#86EFAC;--good-rgb:74,222,128;--good-ink:#4ADE80;--mid:#FBBF24;--low:#FCA5A5;--low-rgb:252,165,165;
  --fg-rgb:234,240,248;--nav-bg:rgba(15,21,35,.94);--radius:20px;
  --blue-ink:#AFC8FF;--course:#AFC8FF;--prof:#B794FF;--prof-ink:#CDB9FF;
  --clsblk:#6EA0FF;--clsblk-rgb:110,160,255;--clsblk-ink:#0B1120;
  --blk:#25396A;--blk-ink:#DCE7FF;--pl3-blk:#25396A;--pl3-blk-ink:#DCE7FF;
  --blue-soft:#1C2C4F;--tab-on:#8DB3FF;--navy:#E3ECFF;--prof-fill:#B794FF;
  --card-sh:0 1px 2px rgba(0,0,0,.35);
  --pop-sh:0 18px 44px rgba(0,0,0,.5);
  """ + RT_DARK + """;
  color-scheme:dark;
}
:root{
  --mono:'Nunito',system-ui,-apple-system,'Segoe UI',Roboto,sans-serif;
  --t-page:34px;--t-subject:26px;--t-lead:20px;--t-para:15px;--t-title:18px;--t-name:15.5px;--t-score:19px;
  --t-body:13.5px;--t-link:13.5px;--t-label:11px;--t-micro:9.5px;
}
body{font-family:'Nunito',system-ui,-apple-system,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;font-weight:600}
"""
CSS = """<style id="app-look">
/* APP-LOOK 2026-10-04 — the component layer; the tokens are repeated here (they also sit in the head
   for the first paint) because later blocks in the page set some of the same properties. */
""" + TOKENS.split("*/", 1)[1].replace(NUNITO, "") + """
h1,h2,h3{font-weight:800!important;letter-spacing:-.015em}
/* card and page titles: the app's heavy titles */
.hm-ct,.cp-card .cp-ct,.cp-narrow .cp-ct,.hm-nf-t,.hm-pcard .hm-pct,.hm-wcard .hm-wct,.lp-ch h3,.pl-gh h3,.pl2-title,.pl3-h,
.wl-h,.fr-no,.cp-title,.ex-q,.hm-tdg,.pl3-title,.plr-n b,.pp-id h2,.auth-h,.st-h{font-weight:800}
b,strong{font-weight:800}
/* a card title's link (Open →, View all →) never wraps under the heavier title */
.hm-ct{gap:10px;white-space:nowrap}
.hm-ct .hm-more,.hm-ct > a,.hm-ct > button{flex:none}

/* ---- cards: the app's white card, soft shadow, no hairline ---- */
.hm-card,.pcard,.cp-hero,.cp-sec,.pp-head,.trend-card,.set-panel,.lcard,.det-card,.cat,.ob-card,.rate-cta,
.friends-cta,.ex-rec-row,.schoolnote,.hz-card,.lp-card,.gp-card,.mc-card,.sl-card,.fr-connect-card,.fr-card,
.fr-profile,.fr-profile2,.fr-gate,.sched-guest,.st-card,.sc-card,.msg-thread,.ge-card,.note{
  border-color:transparent;box-shadow:var(--card-sh);border-radius:20px}
.pq-dlg,.modal,.notif-panel,.pwa-sheet,.cmdk{border-color:transparent;border-radius:24px;box-shadow:var(--pop-sh)}

/* ---- class blocks: the app's soft blue, dark-blue text (variants — waitlisted, clash, a friend's — keep theirs) ---- */
.cal-block,.hmc-blk{background:var(--blk);color:var(--blk-ink);box-shadow:none}
.hmc-blk span,.cal-block .cb-top{color:var(--blk-ink)}
.cal-block.bad{color:#fff}
.hm-id .idhead,.idhead{background:#2563EB}

/* ---- course codes: the app's soft-blue chip; open seats stay green (the old accent WAS green) ---- */
:root[data-theme] .cx-badge,.cx-badge{background:var(--blue-soft);color:var(--blue-ink);border-color:transparent;font-weight:900}
.cp-tile{background:var(--blue-soft);color:var(--blue-ink);font-weight:900;border-radius:16px}
.hm-wrow .wl-st.open,.cp-st.cp-seat-st .v.open,.cp-so.open,.msug-seat.open,.pp-seat.open{color:var(--good)}
.cls-seat.open,.wc-pick-seat.open,.mc-seat.open,.fp-seat.open{background:rgba(22,163,74,.12)}

/* ---- Explore's Classes / Professors thumb: the action colour, so its label reads in both themes ---- */
.ex-seg-thumb{background:var(--accent);border-radius:20px}
.ex-seg-v:has(#ex-profs.active) .ex-seg-thumb{background:var(--prof-fill)}
.ex-seg-v button.active{color:var(--accent-ink)}

/* ---- the top bar: the app's tabs, kept on the right (Tate) ---- */
header.nav{background:var(--nav-bg);border-bottom:1px solid var(--line)}
.nav-inner{height:76px}
.brand{gap:10px}
.brand .brand-tile{width:36px;height:36px}
.brand-wm{font-size:24px;font-weight:900;letter-spacing:-.02em;color:var(--navy);line-height:1}
.brand-wm b{font-weight:900;color:var(--tab-on)}
nav.tabs{gap:4px}
nav.tabs button{width:82px;padding:4px 0 6px;font-size:12.5px;font-weight:800;color:var(--muted);
  display:flex;flex-direction:column;align-items:center;gap:3px;position:relative}
nav.tabs button .tpill{width:56px;height:32px;border-radius:16px;display:grid;place-items:center;transition:background .2s}
nav.tabs button svg{width:22px;height:22px;stroke-width:2.1}
nav.tabs button.active{color:var(--tab-on)}
nav.tabs button.active .tpill{background:var(--blue-soft)}
nav.tabs button.active::after{display:none}
nav.tabs button[hidden]{display:none}
@media (hover:hover){nav.tabs button:hover{color:var(--tab-on)}}
.notif-wrap{margin-left:14px;padding-left:16px;border-left:1px solid var(--line)}
.notif-bell{width:44px;height:44px;border-radius:50%;border:0;background:var(--panel);box-shadow:var(--card-sh);color:var(--text-2)}
.notif-badge{background:var(--pink,#DB2777);color:#fff;border-color:var(--nav-bg)}
.auth-btn{border-radius:22px;border:0;font-weight:800}
.auth-btn.in{background:var(--panel);box-shadow:var(--card-sh)}
.theme-toggle{width:44px;height:44px;border-radius:50%;border:0;background:var(--panel);box-shadow:var(--card-sh)}

/* ---- controls: the app's pill switches, buttons and chips ---- */
.seg{background:var(--panel);border-color:transparent;border-radius:24px;padding:4px;box-shadow:var(--card-sh)}
.seg button{border-radius:20px;font-weight:800}
.seg button.on,.seg button.active{background:var(--accent);color:var(--accent-ink);box-shadow:0 4px 12px rgba(var(--accent-rgb),.3)}
.set-seg{border-color:transparent;border-radius:22px;background:var(--panel-2);padding:3px;gap:2px}
.set-seg button{border-radius:19px;font-weight:800}
.btn{border-radius:14px;font-weight:800}
.btn.primary{box-shadow:0 8px 20px rgba(var(--accent-rgb),.25)}
.code,.cls-info .code{font-weight:900}
input,select,textarea{border-radius:14px}

/* ---- pills on a class block: dark ink on the soft blue (they were white on the old solid block) ---- */
.cal-block .mode-pill{background:rgba(var(--fg-rgb),.08);color:var(--blk-ink);border-color:rgba(var(--fg-rgb),.2)}
.cal-tbablk .mode-pill{background:rgba(var(--fg-rgb),.08);color:var(--muted)}

/* ---- text that was hard-coded white on a token that is light in dark mode ---- */
.hm-id .fav,.ep-ava,.fp-addmc.on{color:var(--accent-ink)}
.exm-cta{background:var(--accent);border-color:var(--accent);color:var(--accent-ink)}
:root[data-theme="dark"] .hmc-blk.conflict b{color:#3B0A0A}

/* ---- green still means good: done, met, in My Classes, enrolled, OK — on a green tint, not the old
        accent tint (the accent was green before 2026-10-04; it is the app's blue now) ---- */
.cp-inmine,.cs-inmine,.wc-inmine,.pq-chip.pq-met,.mc-status.enr,.pl2-chip--ok,.wl-take,.sp-rnum,.fp-snum,.ex-rec-btn{background:rgba(var(--good-rgb),.13);color:var(--good-ink)}
.ex-rec-btn{border-color:rgba(var(--good-rgb),.45)}
.pl2-mini--ok{border-color:var(--good-2);color:var(--good-ink)}
.pt-chip.on .pt-sys{color:var(--tab-on)}
.wl-take{border-color:rgba(var(--good-rgb),.4)}
.pl2-callout--ok{background:rgba(var(--good-rgb),.10)}
.ge-card.done .ge-k{background:rgba(var(--good-rgb),.13);border-color:rgba(var(--good-rgb),.4)}
.sp-yearblk.done::before,.msug-fit.ok i{background:var(--good-2)}
.pf-ok,.ep-hint.good,.pl-why i.ok{color:var(--good)}
.exm-chip.green{background:rgba(var(--good-rgb),.13);color:var(--good)}
/* …and a selected chip or a watch toggle is the app's selected blue */
.rf-seg button.on,.sfy-r.on,.gp-btn.on,.sp-chip.on,.pt-chip.on,.fp-chip.on,.wl-btn.on,.cp-watch.on,.fp-watchbtn.on,
.gp-daytabs button.on,.rf-tags button.on,.sfy-tabs button.on,.pc-srcchip.on,.gp-ghead .gp-dh.on,.wc-cmp.on,.cs-frsec{
  background:var(--blue-soft);border-color:rgba(var(--accent-rgb),.45);color:var(--tab-on)}

/* ---- accent text on an accent tint is 4.25:1; the app's deeper selected blue reads ---- */
.hm-newmark,.hm-id .mjs-t,.hmc-share-txt b,.fr-cchip,.st-tab.on{color:var(--tab-on)}
.ex-top-l .ex-gesw button.on{color:var(--tab-on);background:var(--blue-soft)}
/* a person with no photo: the grey tile takes dark initials (AVA_INK), never white — white on #CBCBD0 is 1.6:1 */
.frv2-card .ini{color:#4F4F56}
.hm-id .idun{color:#fff}
.hm-id .idun-btn{background:rgba(15,23,42,.22);border-color:rgba(255,255,255,.4)}

/* ---- the website's own phone bar (narrow windows): the app's active pill ---- */
.mtab.active{color:var(--tab-on)}
.mtab.active svg{background:var(--blue-soft);border-radius:14px;padding:3px 14px;box-sizing:content-box}

/* narrower windows (iPad portrait, a half-screen laptop): the tile alone and tighter tabs, so the bar never
   scrolls sideways (review, 2026-10-04: 700 and 780px overflowed) */
@media (max-width:1000px){.brand-wm{display:none} nav.tabs button{width:66px} nav.tabs button .tpill{width:48px}
  .notif-wrap{margin-left:8px;padding-left:10px}}
@media (max-width:760px){nav.tabs{gap:0} nav.tabs button{width:58px;font-size:11.5px} nav.tabs button .tpill{width:44px}}
</style>
"""

R = [
 # theme boot: light by default; dark only when chosen; cream retired
 ("""  var t='dark';
  try{
    var s=localStorage.getItem('professify-theme');
    if(s==='light'||s==='dark'||s==='cream'){ t=s; }
    else if(window.matchMedia && window.matchMedia('(prefers-color-scheme: light)').matches){ t='light'; }
  }catch(e){}""",
  """  /* Light by default, dark only when chosen (Tate, 2026-10-04: "build it in light but have a dark
     option"). Cream is retired: a stored 'cream' reads as light. */
  var t='light';
  try{
    var s=localStorage.getItem('professify-theme');
    if(s==='dark'){ t='dark'; }
  }catch(e){}"""),
 # Settings: Light / Dark only
 ("""          <p class="st-note">Applies on this device. Cream is the warm light theme.</p>""",
  """          <p class="st-note">Applies on this device.</p>"""),
 ("""              <button type="button" data-theme-val="cream" onclick="setTheme('cream')">Cream</button>
""", ""),
 ("""var cur=document.documentElement.getAttribute('data-theme')||'dark'; if(cur!=='light'&&cur!=='cream')cur='dark';""",
  """var cur=document.documentElement.getAttribute('data-theme')==='dark'?'dark':'light';"""),
 # ratings: the app's ten half-star steps
 # the Add-to-plan chooser assumed it was 200px tall; with the app's type it is taller, so measure it
 ("""    var top = r.bottom + 6; if (top + 200 > window.innerHeight) top = Math.max(8, r.top - 190);""",
  """    var bh = box.offsetHeight || 200, top = r.bottom + 6; if (top + bh > window.innerHeight - 8) top = Math.max(8, r.top - bh - 6);"""),
 ("""function scoreColor(v){return v==null?'var(--faint)':v>=3.3?'var(--good)':v>=2.5?'var(--mid)':'var(--low)';}""",
  """/* The app's rating scale (2026-10-04): ten half-star steps, green at 5 to red at 0.5, the same
   RATE_HUE / RATE_FILL as app/index.html. --rt-N is the readable text colour for the theme (the
   dark same-hue ink on light, the bright fill on dark), defined in #app-look. */
function scoreColor(v,kind){ if(v==null||!isFinite(Number(v)))return 'var(--faint)'; var st=Math.min(10,Math.max(1,Math.round((Number(v)/4*5)*2))); return 'var(--'+(kind==='fill'?'rtf-':'rt-')+st+')'; }   /* kind 'fill': the bright fill, for dots, strokes and shapes */"""),
 ("""function profTintStyle(rating){
  var bg=ratingTint(rating);
  if(!bg)return '';""",
  """var APP_RATE_FILL=""" + repr(FILL).replace("'", '"') + """, APP_RATE_INK=""" + repr(INK).replace("'", '"') + """;
function profTintStyle(rating){
  /* the app's professor circle (2026-10-04): its rating's fill, same-hue near-black initials */
  if(rating!=null&&isFinite(Number(rating))){ var st=Math.min(10,Math.max(1,Math.round((Number(rating)/4*5)*2)));
    return 'background:'+APP_RATE_FILL[st-1]+';color:'+APP_RATE_INK[st-1]+';text-shadow:none;border-color:transparent'; }
  var bg=ratingTint(rating);
  if(!bg)return '';"""),
]
for a, b in R:
    if s.count(a) != 1: sys.exit(f'anchor matched {s.count(a)}x: {a[:90]}')
    s = s.replace(a, b)

def whole_fn(name, nxt, body):
    """Replace function NAME up to (not including) the line that starts NXT; each must be found once."""
    global s
    i = s.find('function ' + name + '('); j = s.find(nxt, i)
    if i < 0 or s.count('function ' + name + '(') != 1 or j < 0: sys.exit('function not found once: ' + name)
    s = s[:i] + body + s[j:]

# setTheme: light or dark; the accent comes from the theme tokens (#app-look), never inline any more
whole_fn('setTheme', 'function setThemeButtons(', '''function setTheme(t){
  if(t!=='dark')t='light';   /* cream retired 2026-10-04 */
  document.documentElement.setAttribute('data-theme',t);
  try{localStorage.setItem('professify-theme',t);}catch(e){}
  var r=document.documentElement.style;
  r.removeProperty('--accent'); r.removeProperty('--accent-rgb'); r.removeProperty('--accent-ink');
  setThemeButtons();
}
''')
# applySchoolTheme: keep the school bookkeeping, stop painting the school's green inline over the app's blue
whole_fn('applySchoolTheme', 'function schoolComingHtml(', '''function applySchoolTheme(name){
  const sc=SCHOOLS[name]||SCHOOLS['Cal Poly, San Luis Obispo'];
  window._schoolAccent=sc.accent; window._schoolAccentRgb=sc.accentRgb; window._schoolInk=sc.ink;
  /* 2026-10-04: the accent is the app's blue in both themes (#app-look). The school colour no longer
     paints inline over it; clear anything an older build left on <html>. */
  const r=document.documentElement.style;
  r.removeProperty('--accent'); r.removeProperty('--accent-rgb'); r.removeProperty('--accent-ink');
}
''')
# ratingTint / ratingInk: the app's ten fills and their inks, so every rating tile agrees with the app
whole_fn('ratingTint', '/* ALWAYS WHITE', '''function ratingTint(rating){
  if(rating==null||isNaN(rating))return null;
  var st=Math.min(10,Math.max(1,Math.round(((+rating)/4*5)*2)));
  return APP_RATE_FILL[st-1];   /* the app's fill (2026-10-04); was a five-stop ramp */
}
''')
whole_fn('ratingInk', '/* Inline style for a professor', '''function ratingInk(hex){ var i=APP_RATE_FILL.indexOf(hex); return i>=0?APP_RATE_INK[i]:'#fff'; }   /* the app's same-hue ink (2026-10-04) */
''')
# a rating's dot and the Schedule halo are shapes: the bright fill, not the text ink
DOTS = [
 ('<span class="rd" style="background:${scoreColor(v)}"></span>', '<span class="rd" style="background:${scoreColor(v,\'fill\')}"></span>'),
 ('<span class="rd" style="background:${scoreColor(v4)}"></span>', '<span class="rd" style="background:${scoreColor(v4,\'fill\')}"></span>'),
 ("border-radius:50%;background:'+scoreColor((r.score/5)*4)+';display:inline-block", "border-radius:50%;background:'+scoreColor((r.score/5)*4,'fill')+';display:inline-block"),
 ("    var col=(typeof scoreColor==='function')?scoreColor(t.rating):'var(--faint)';\n    t.rects.forEach(", "    var col=(typeof scoreColor==='function')?scoreColor(t.rating,'fill'):'var(--faint)';\n    t.rects.forEach("),
 # a crown's initials: the tile is the app's fill now, so the ink is its same-hue ink, not white
 ("font-weight:700;color:#fff;font-size:'+Math.round(avSize*0.36)+'px;background:'+(avatar.bg||'#5E7A8A')+'\"", "font-weight:700;color:'+((avatar.bg&&typeof ratingInk==='function')?ratingInk(avatar.bg):'#fff')+';font-size:'+Math.round(avSize*0.36)+'px;background:'+(avatar.bg||'#5E7A8A')+'\""),
 # a professor's tag chips: accent text on an accent tint was 4.2:1; the small-sample warning was a fixed gold
 ("border-radius:99px;padding:5px 13px;font-size:var(--t-body);font-weight:600;color:'+PFC.green+'\">", "border-radius:99px;padding:5px 13px;font-size:var(--t-body);font-weight:600;color:var(--tab-on)\">"),
 ('<div style="font-size:var(--t-body);color:#B7791F;margin-top:8px">Only', '<div style="font-size:var(--t-body);color:var(--mid);margin-top:8px">Only'),
 # the Rate tab's sheet: the page's own face, the app's heavy title, no italic
 ("font-family:'Inter',-apple-system,system-ui,sans-serif;color:${PFC.ink};position:relative", "font-family:inherit;color:${PFC.ink};position:relative;border-radius:24px"),
 ('<div class="rl-title" style="font-size:var(--t-title);font-weight:500;margin-bottom:2px">', '<div class="rl-title" style="font-size:var(--t-lead);font-weight:900;margin-bottom:2px">'),
 ('<div class="rl-sub" style="font-size:var(--t-body);color:${PFC.ink2};font-style:italic;margin-bottom:18px">', '<div class="rl-sub" style="font-size:var(--t-body);color:${PFC.ink2};margin-bottom:18px">'),
]
for a, b in DOTS:
    if s.count(a) != 1: sys.exit(f'anchor matched {s.count(a)}x: {a[:90]}')
    s = s.replace(a, b)

# the Plans module is re-inlined from dev/plans/plans.js by apply-plans.mjs: give it the same chooser fix
pp = os.path.join(d, 'dev', 'plans', 'plans.js')
pj = open(pp, encoding='utf-8').read()
CH = ("    var top = r.bottom + 6; if (top + 200 > window.innerHeight) top = Math.max(8, r.top - 190);",
      "    var bh = box.offsetHeight || 200, top = r.bottom + 6; if (top + bh > window.innerHeight - 8) top = Math.max(8, r.top - bh - 6);")
if pj.count(CH[0]) != 1: sys.exit('plans.js chooser anchor')
pj = pj.replace(*CH)

# the tokens and the face in the head too, so the first paint is already the app's look
HEAD = '<style id="app-look-tokens">' + TOKENS + '</style>\n'
if s.count('</head>') != 1: sys.exit('head end')
s = s.replace('</head>', HEAD + '</head>')

# the top bar: the app's order (Home · Explore · Rate · Schedule · Friends), each icon in a pill, Rate added
mt = re.search(r'    <nav class="tabs">\n(.*?)\n    </nav>', s, flags=re.S)
if not mt or s.count('    <nav class="tabs">') != 1: sys.exit('tabs nav not found once')
btns = {}
for line in mt.group(1).split('\n'):
    mid = re.search(r'id="tab-(\w+)"', line)
    if not mid: sys.exit('unexpected line in tabs: ' + line[:80])
    btns[mid.group(1)] = line
if sorted(btns) != ['explore', 'friends', 'home', 'sched']: sys.exit('tabs changed: ' + str(sorted(btns)))
def pill(line):
    return re.sub(r'(<svg .*?</svg>)', r'<span class="tpill" aria-hidden="true">\1</span>', line, count=1)
RATE = ('      <button id="tab-rate" onclick="openRate()"><span class="tpill" aria-hidden="true"><svg viewBox="0 0 24 24" fill="none" '
        'stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="m12 3 2.7 5.6 6.1.9-4.4 4.3 1 6.1L12 '
        '17l-5.4 2.9 1-6.1-4.4-4.3 6.1-.9z"/></svg></span><span>Rate</span></button>')
new_nav = '\n'.join([pill(btns['home']), pill(btns['explore']), RATE, pill(btns['sched']), pill(btns['friends'])])
s = s[:mt.start(1)] + new_nav + s[mt.end(1):]
for k in ['home', 'explore', 'sched', 'friends']:
    if s.count(f'id="tab-{k}"') != 1: sys.exit(f'tab-{k} count')

# the wordmark beside the mark
a = 'aria-label="TermChamp — go to home">\n      <img class="brand-tile"'
if s.count(a) != 1: sys.exit('brand anchor')
mb = re.search(r'(<button type="button" class="brand"[^>]*>\n      <img class="brand-tile"[^>]*>)', s)
if not mb: sys.exit('brand img not found')
s = s[:mb.end()] + '<span class="brand-wm" aria-hidden="true">Term<b>Champ</b></span>' + s[mb.end():]

# Champ / Hawk on the website: cream is retired, so it offers light and dark only
hp = os.path.join(d, 'hawk-ask.js')
h = open(hp, encoding='utf-8').read()
HA = [("    if (['dark', 'light', 'cream'].indexOf(t) < 0 || !has('setTheme')) { notFound(turn, 'I can switch between dark, light and cream.'); return; }\n    var prev = document.documentElement.getAttribute('data-theme') || 'dark';",
       "    if (['dark', 'light'].indexOf(t) < 0 || !has('setTheme')) { notFound(turn, 'I can switch between light and dark.'); return; }   /* cream retired 2026-10-04 */\n    var prev = document.documentElement.getAttribute('data-theme') === 'dark' ? 'dark' : 'light';")]
for a2, b2 in HA:
    if h.count(a2) != 1: sys.exit('hawk-ask.js anchor: ' + a2[:60])
    h = h.replace(a2, b2)

# the layer, last in the page
if s.count('</body>') != 1: sys.exit('body end')
s = s.replace('</body>', CSS + '</body>')
open(p, 'w', encoding='utf-8').write(s)
open(hp, 'w', encoding='utf-8').write(h)
open(pp, 'w', encoding='utf-8').write(pj)
print('patched', p, hp, pp)
