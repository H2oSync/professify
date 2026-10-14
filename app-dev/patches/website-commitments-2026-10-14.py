#!/usr/bin/env python3
"""Work & activities on the website (Tate, 2026-10-14: catch termchamp.com up to the phone).

The phone has had this since 2026-10-11 (app-dev/patches/commitments-2026-10-11.py and commitments-champ-addto-2026-10-11.py;
sql/professify-commitments.sql, RUN 18): log work, practice, a club or anything else you do every week, and it shows on
your week, on Home, in free time, and to friends as "Busy" (never the name). This is the same thing in index.html, against
the same table and function (commitments: owner-only; friend_busy_blocks(): accepted same-school friends, items left on,
days/start/end only, never anyone blocked either way).

- Data layer (its own <script id="cm-js">, ahead of the Plans module): yours is local-first — the change is kept on this
  device the moment you save it (professify_commits_<user>, so Delete my account clears it), goes up to commitments
  (upsert on id; delete for Delete), and until it has gone up it is marked waiting (…_pending_<user>) so a reload, a refused
  write or an offline tab never loses it: waiting ones go up again on `online`, when the tab comes back and on a slow timer,
  and win over the server's copy. The user is captured before any await, and a sign-out or an account switch drops
  everything in memory. A missing table (42P01 / PGRST205 / 42703) keeps them on this device quietly; anything else — a
  42501 included — is a failure the student is told about ("kept on this device"), never "saved". Friends' busy blocks come
  from the RPC, asked at sign-in, again after 2 minutes (15 s after a failure), 10 s timeout, and cleared on an error.
- "Work & activities" card on Schedule > My classes (both term views): "Barista · Mon Wed Fri · 4:00–8:00p · friends see
  Busy", + Add, click a row to edit, delete. The modal (openModalA11y, #cmBack): kind Work / Club / Sport / Other (stored
  work / club / practice / other, the table's check), name, M T W Th F Sa Su toggles, From / To typed like the Portal shows
  them (4pm, 4:30 pm, 16:30 — a bare "4" is not guessed; end after start), "Friends see Busy". Errors sit under the field
  that caused them (aria-invalid + aria-describedby) and the first bad field takes focus. Focus goes back to a live element.
- Hatched blocks (.cal-cm: hatch on --panel-3, text --text, both themes >= 4.5:1, never the class blue): yours on My classes
  (renderMyCalendar, both terms; click edits) and Home's "My schedule" (hmMiniCalHtml); a friend's busy on their Home card
  (hmMiniWeekHtml) and profile week (renderMyCalendar via frpCalendarHtml) as "Busy". Sat/Sun columns appear when needed.
- Free time: gpMemberBusy counts them (yours by name, a friend's as Busy); avMyMeets / avMeetsOf carry them so the status
  reads "Barista shift till 8p" (yours) and "Busy till 8p" (a friend's); only a class makes "No class till" true.
- Overlap: a section over a commitment says "Overlaps Barista Mon 4–8p" on the class page (secConflictChip, the section
  rows; scheduleOverlapHtml is the friend-overlap grid, not the class page) and My Classes gets an amber "Overlaps Barista"
  pill beside the red time-conflict one (never red).
- window.cmBlocks(who) -> meet-shaped blocks ({code, name, key, meet:{days:['Mo'..], start, end}, label, mine, cm}) for the
  Builder; who = 'me' (default) or a friend's id.

Usage: python3 website-commitments-2026-10-14.py <repo>
"""
import sys, pathlib
root = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else '.')
f = root / 'index.html'
s = f.read_text()
if 'website-commitments (2026-10-14)' in s:
    sys.exit('already patched')

def one(old, new):
    global s
    n = s.count(old)
    assert n == 1, (n, old[:120])
    s = s.replace(old, new)

# ================================================================ 1. renderMyCalendar: weekend columns, window, hatched blocks
one("""  var DAYS=['Mo','Tu','We','Th','Fr'];
  // One block PER section the student is in""", """  var DAYS=['Mo','Tu','We','Th','Fr'];
  /* website-commitments (2026-10-14): work & activities — yours by name (opts.cm 'me'), a friend's as Busy (opts.cm = their id) */
  var _cm=(typeof cmBlocks==='function'&&opts.cm)?cmBlocks(opts.cm):[];
  if(_cm.some(function(b){return b.meet.days.indexOf('Sa')>=0;}))DAYS.push('Sa');
  if(_cm.some(function(b){return b.meet.days.indexOf('Su')>=0;}))DAYS.push('Su');
  // One block PER section the student is in""")
one("""  if(_hzTight){ lo=placed[0].meet.start; hi=placed[0].meet.end; }""", """  if(_hzTight){ lo=placed[0].meet.start; hi=placed[0].meet.end; }
  _cm.forEach(function(b){ lo=Math.min(lo,b.meet.start); hi=Math.max(hi,b.meet.end); });""")
one("""    var i=0,html='';
""", """    var i=0,html=(typeof cmCalBlocksHtml==='function')?cmCalBlocksHtml(_cm,d,lo,PPM):'';
""")
one("renderMyCalendar(codes,conf)+'</div>'", "renderMyCalendar(codes,conf,undefined,{cm:'me'})+'</div>'")
one("renderMyCalendar(codes,conf,N.meta,{peopleFor:mcNowPeopleFor})+'</div>';", "renderMyCalendar(codes,conf,N.meta,{peopleFor:mcNowPeopleFor,cm:'me'})+'</div>'+((typeof cmSlotHtml==='function')?cmSlotHtml():'');")
one("peopleFor:frpPeopleFor", "peopleFor:frpPeopleFor,cm:f.id")
# the card under My classes' calendar / list
one("""    +banner+body
""", """    +banner+body+((typeof cmSlotHtml==='function')?cmSlotHtml():'')
""")
# the card is there even before you have a class in the term (the empty states return early)
one("""  if(mcTwoTerms()&&mcTermView()==='now'){ mcRenderNow(out); return; }
  renderMyClassesTerm();""", """  if(mcTwoTerms()&&mcTermView()==='now'){ mcRenderNow(out); try{ cmEnsureSlot(out); }catch(_e){} return; }
  renderMyClassesTerm(); try{ cmEnsureSlot(out); }catch(_e){}   /* website-commitments (2026-10-14) */""")
# the amber pill beside the red time-conflict one
one("""  if(!flags.length)return '';
  var openKey=null;""", """  if(surface==='mine'){ try{ var _cf=(typeof cmFlag==='function')?cmFlag(conf):null; if(_cf)flags.push(_cf); }catch(_e){} }   /* website-commitments (2026-10-14) */
  if(!flags.length)return '';
  var openKey=null;""")

# ================================================================ 2. the class page's section rows: "Overlaps Barista Mon 4–8p"
one("""function secConflictChip(code, sec){
  var hits=secTimeConflicts(code,sec); if(!hits.length)return '';""", """function secConflictChip(code, sec){
  var _cmChip=''; try{ _cmChip=(typeof cmChipHtml==='function')?cmChipHtml(sec):''; }catch(_e){}   /* website-commitments (2026-10-14): your work & activities */
  var hits=secTimeConflicts(code,sec); if(!hits.length)return _cmChip;""")
one("""⚠ Conflicts with '+escapeHtml(first)+more+'</span>';""", """⚠ Conflicts with '+escapeHtml(first)+more+'</span>'+_cmChip;""")

# ================================================================ 3. Home: yours on "My schedule", a friend's on their card
one("""  var lo=8*60, hi=18*60;
  meets.forEach(function(m){lo=Math.min(lo,m.meet.start);hi=Math.max(hi,m.meet.end);});""", """  var lo=8*60, hi=18*60;
  _cm.forEach(function(b){ lo=Math.min(lo,b.meet.start); hi=Math.max(hi,b.meet.end); });   /* website-commitments (2026-10-14) */
  meets.forEach(function(m){lo=Math.min(lo,m.meet.start);hi=Math.max(hi,m.meet.end);});""")
one("""  if(meets.some(function(m){return m.meet.days.indexOf('Sa')>=0;})){DAYS.push('Sa');DL.push('S');}
  if(meets.some(function(m){return m.meet.days.indexOf('Su')>=0;})){DAYS.push('Su');DL.push('S');}""", """  var _cm=(typeof cmBlocks==='function')?cmBlocks('me'):[];                       /* website-commitments (2026-10-14) */
  var _cmSa=_cm.some(function(b){return b.meet.days.indexOf('Sa')>=0;}), _cmSu=_cm.some(function(b){return b.meet.days.indexOf('Su')>=0;});
  if(_cmSa||meets.some(function(m){return m.meet.days.indexOf('Sa')>=0;})){DAYS.push('Sa');DL.push('S');}
  if(_cmSu||meets.some(function(m){return m.meet.days.indexOf('Su')>=0;})){DAYS.push('Su');DL.push('S');}""")
one("""    var i=0,blocks='';
""", """    var i=0,blocks=(typeof cmMiniOwnHtml==='function')?cmMiniOwnHtml(_cm,d,lo,span,H):'';
""")
one("""win:window._hmFeedWin||null}) : '';""", """win:window._hmFeedWin||null,cm:f.id}) : '';""")
one("""  var DAYS=['Mo','Tu','We','Th','Fr'];
  if(meets.some(function(m){return m.meet&&m.meet.days.indexOf('Sa')>=0;}))DAYS.push('Sa');
  if(meets.some(function(m){return m.meet&&m.meet.days.indexOf('Su')>=0;}))DAYS.push('Su');""", """  var DAYS=['Mo','Tu','We','Th','Fr'];
  var _cm=(typeof cmBlocks==='function'&&opts.cm)?cmBlocks(opts.cm):[];           /* website-commitments (2026-10-14): a friend's Busy */
  if(_cm.some(function(b){return b.meet.days.indexOf('Sa')>=0;})||meets.some(function(m){return m.meet&&m.meet.days.indexOf('Sa')>=0;}))DAYS.push('Sa');
  if(_cm.some(function(b){return b.meet.days.indexOf('Su')>=0;})||meets.some(function(m){return m.meet&&m.meet.days.indexOf('Su')>=0;}))DAYS.push('Su');""")
one("""  meets.forEach(function(m){ if(!m||!m.meet)return; lo=Math.min(lo,m.meet.start); hi=Math.max(hi,m.meet.end); });""", """  meets.forEach(function(m){ if(!m||!m.meet)return; lo=Math.min(lo,m.meet.start); hi=Math.max(hi,m.meet.end); });
  _cm.forEach(function(b){ lo=Math.min(lo,b.meet.start); hi=Math.max(hi,b.meet.end); });""")
one("""    var day=meets.filter(function(m){return m.meet&&m.meet.days.indexOf(d)>=0;});
    var html=hmLaneOut(day).map(function(e){""", """    var day=meets.filter(function(m){return m.meet&&m.meet.days.indexOf(d)>=0;});
    var html=((typeof cmCalBlocksHtml==='function')?cmCalBlocksHtml(_cm,d,lo,PPM):'')+hmLaneOut(day).map(function(e){""")

# ================================================================ 4. free time and the status line
one("""      else push(code,(typeof myClassTime==='function')?myClassTime(code,_nm.meta===NOW_MINE.meta?_nm.meta:undefined):'');
    });""", """      else push(code,(typeof myClassTime==='function')?myClassTime(code,_nm.meta===NOW_MINE.meta?_nm.meta:undefined):'');
    });
    try{ if(typeof cmPushBusy==='function')cmPushBusy(out,'me'); }catch(_e){}      /* website-commitments (2026-10-14): your work & activities */""")
one("""    (f.classes||[]).forEach(function(c){ if(!seen[c])unknown.push(c); });""", """    (f.classes||[]).forEach(function(c){ if(!seen[c])unknown.push(c); });
    try{ if(typeof cmPushBusy==='function')cmPushBusy(out,f.id); }catch(_e){}      /* a friend's Busy (never the name) */""")
one("""    return (fm.meets||[]).filter(function(m){ return m&&!m.assumed&&okMeet(m.meet); });""", """    var _o=(fm.meets||[]).filter(function(m){ return m&&!m.assumed&&okMeet(m.meet); });
    try{ if(typeof cmBlocks==='function'&&f.id)_o=_o.concat(cmBlocks(f.id)); }catch(_e){}   /* website-commitments (2026-10-14): their Busy */
    return _o;""")
one("""    return (mm||[]).filter(function(m){ return m&&okMeet(m.meet); });""", """    var _o=(mm||[]).filter(function(m){ return m&&okMeet(m.meet); });
    try{ if(typeof cmBlocks==='function')_o=_o.concat(cmBlocks('me')); }catch(_e){}   /* website-commitments (2026-10-14): yours */
    return _o;""")
one("""    out.push({code:x.code,start:m.start,end:m.end});""", """    out.push({code:x.code,start:m.start,end:m.end,cm:x.cm||''});""")
one("""  if(!meets||!meets.length)return {state:'unknown'};""", """  if(!meets||!meets.length)return {state:'unknown'};
  var _cls=meets.some(function(x){ return x&&!x.cm; });                  /* only a class makes "no class" true */""")
one("""    else if(day[i].start>t&&next==null){ next=day[i]; }""", """    else if(day[i].start>t&&next==null&&!day[i].cm){ next=day[i]; }""")
one("""    if(day[i].start<=t&&t<day[i].end){ cur=day[i]; }""", """    if(day[i].start<=t&&t<day[i].end){ if(!(cur&&!cur.cm&&day[i].cm))cur=day[i]; }   /* a class you are in wins over a busy block */""")
one("""  if(cur)return {state:'class',code:cur.code,until:cur.end};""", """  if(cur)return {state:'class',code:cur.code,until:cur.end,cm:cur.cm||''};
  if(!_cls)return {state:'unknown'};""")
one("""  if(st.state==='class')return 'In '+st.code+' till '+avHM(st.until);""", """  if(st.state==='class'&&st.cm&&typeof cmHs==='function')return st.code+' till '+cmHs(st.until);   /* "Barista shift till 8p" / "Busy till 8p" */
  if(st.state==='class')return 'In '+st.code+' till '+avHM(st.until);""")

# ================================================================ 5. sign-in / sign-out
one("""      if(uid&&(uid!==lastAuthUid||notLoaded)){lastAuthUid=uid;""", """      /* Work & activities (website-commitments, 2026-10-14) */
      try{ if(uid){ if(window._cmAsked!==uid){window._cmAsked=uid;setTimeout(function(){try{cmBoot();}catch(_e){}},0);} } else if(window._cmAsked){window._cmAsked=null;cmReset();} }catch(_e){}
      if(uid&&(uid!==lastAuthUid||notLoaded)){lastAuthUid=uid;""")

# ================================================================ 6. the module
BLOCK = r'''<!-- CM:BEGIN website-commitments (2026-10-14) — patches/website-commitments-2026-10-14.py -->
<style id="cm-css">
/* Work & activities. App tokens only; 44px targets. The hatch is the "not a class" mark everywhere:
   --panel-3 with a stripe of the text colour, text in --text (>= 4.5:1 in light and dark), never the class blue. */
.cm-slot:empty{display:none}
.cm-card{display:flex;flex-direction:column;gap:4px;margin-top:16px;padding:14px 16px 10px;background:var(--panel);border:1px solid var(--line);border-radius:14px}
.cm-h{display:flex;align-items:center;gap:10px}
.cm-h h3{flex:1;margin:0;font-size:var(--t-title);font-weight:800;color:var(--text);letter-spacing:-.01em}
.cm-btn{flex:none;min-height:44px;padding:0 16px;border-radius:999px;border:1px solid var(--line);background:var(--panel);color:var(--text);font:inherit;font-size:13.5px;font-weight:700;cursor:pointer}
@media (hover:hover){.cm-btn:hover{border-color:rgba(var(--accent-rgb),.55)}.cm-row:hover{background:var(--panel-2)}.cm-x:hover{color:var(--text);background:var(--panel-2)}}
.cm-btn:focus-visible,.cm-row:focus-visible,.cm-x:focus-visible,.cm-k:focus-visible,.cm-d:focus-visible,.cm-in:focus-visible,.cm-tog:focus-visible,.cal-cm:focus-visible{outline:2px solid var(--accent);outline-offset:2px}
.cm-list{list-style:none;margin:0;padding:0;display:flex;flex-direction:column}
.cm-li{display:flex;align-items:center;gap:4px}
.cm-row{flex:1;min-width:0;display:flex;align-items:center;gap:12px;min-height:52px;padding:6px 8px;border:0;border-radius:12px;background:none;color:var(--text);font:inherit;text-align:left;cursor:pointer}
.cm-sw{flex:none;width:26px;height:26px;border-radius:8px;border:1px solid rgba(var(--fg-rgb),.3);background:repeating-linear-gradient(135deg,rgba(var(--fg-rgb),.2) 0 3px,transparent 3px 7px),var(--panel-3)}
.cm-tx{flex:1;min-width:0;font-size:14px;font-weight:600;line-height:1.35;color:var(--text-2);overflow-wrap:anywhere}
.cm-tx b{color:var(--text);font-weight:800}
.cm-x{flex:none;width:44px;height:44px;display:flex;align-items:center;justify-content:center;border:0;border-radius:12px;background:none;color:var(--text-2);cursor:pointer}
.cm-x svg{width:18px;height:18px}
.cm-none{padding:8px;font-size:13.5px;font-weight:600;color:var(--text-2)}
.cm-note{padding:4px 8px 2px;font-size:12.5px;font-weight:600;color:var(--text-2)}
/* the blocks */
.cal-cm{position:absolute;left:2px;right:2px;box-sizing:border-box;display:flex;align-items:center;justify-content:center;overflow:hidden;padding:0 2px;border:1px solid rgba(var(--fg-rgb),.3);border-radius:6px;font:inherit;color:var(--text);
  background:repeating-linear-gradient(135deg,rgba(var(--fg-rgb),.16) 0 4px,transparent 4px 9px),var(--panel-3)}
button.cal-cm{cursor:pointer}
span.cal-cm{cursor:default}
.cal-cm>span{display:-webkit-box;-webkit-box-orient:vertical;-webkit-line-clamp:3;max-width:100%;padding:1px 3px;border-radius:4px;background:var(--panel-3);font-size:11px;font-weight:800;line-height:1.15;text-align:center;overflow:hidden;overflow-wrap:anywhere}
.cal-mini .cal-cm>span{font-size:var(--t-micro)}
@media (max-width:640px){.cal-cm>span{font-size:9.5px;padding:1px 1px;letter-spacing:-.02em;overflow-wrap:break-word}}
.hmc-cm{position:absolute;left:1px;width:calc(100% - 2px);box-sizing:border-box;border:1px solid rgba(var(--fg-rgb),.3);border-radius:4px;background:repeating-linear-gradient(135deg,rgba(var(--fg-rgb),.2) 0 3px,transparent 3px 6px),var(--panel-3)}
.cs-cm{display:inline-flex;align-items:center;gap:6px;font-size:11px;font-weight:700;color:var(--text);background:var(--panel-3);border:1px solid var(--mid);border-radius:999px;padding:2px 9px}
.cs-cm::before{content:'';width:9px;height:9px;border-radius:3px;background:repeating-linear-gradient(135deg,var(--mid) 0 2px,transparent 2px 4px)}
/* the modal */
.cm-modal{max-width:460px;position:relative}
#cmModal .mclose{position:absolute;top:14px;right:14px;left:auto;z-index:3}
.cm-m{padding:26px 24px 22px;display:flex;flex-direction:column;gap:12px}
.cm-m .rate-h{margin:0 40px 0 0}
.cm-lab{display:block;font-size:12px;font-weight:700;letter-spacing:.06em;text-transform:uppercase;color:var(--text-2);margin-bottom:6px}
.cm-kinds{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:6px}
.cm-k,.cm-d{min-height:44px;border:1px solid var(--line);border-radius:12px;background:var(--panel-2);color:var(--text);font:inherit;font-size:14px;font-weight:700;cursor:pointer}
.cm-k.on,.cm-d.on{background:var(--accent);border-color:var(--accent);color:var(--accent-ink)}
.cm-days{display:grid;grid-template-columns:repeat(7,minmax(0,1fr));gap:5px}
.cm-two{display:grid;grid-template-columns:1fr 1fr;gap:10px}
.cm-in{width:100%;box-sizing:border-box;min-height:44px;padding:0 12px;border:1px solid var(--line);border-radius:12px;background:var(--panel-2);color:var(--text);font:inherit;font-size:15px;font-weight:600}
.cm-in[aria-invalid="true"]{border-color:var(--low)}
.cm-err{margin-top:5px;font-size:12.5px;font-weight:700;color:var(--low)}
.cm-sr{display:flex;align-items:center;gap:12px;min-height:48px}
.cm-srl{flex:1;font-size:14.5px;font-weight:700;color:var(--text)}
.cm-srl em{display:block;font-style:normal;font-size:12.5px;font-weight:600;color:var(--text-2)}
.cm-tog{flex:none;width:46px;height:28px;border-radius:999px;border:0;padding:0;background:rgba(var(--fg-rgb),.22);position:relative;cursor:pointer}
.cm-tog::after{content:'';position:absolute;left:3px;top:3px;width:22px;height:22px;border-radius:50%;background:#fff;box-shadow:0 1px 3px rgba(0,0,0,.3);transition:transform .15s}
.cm-tog[aria-checked="true"]{background:var(--accent)}
.cm-tog[aria-checked="true"]::after{transform:translateX(18px)}
.cm-acts{display:flex;gap:10px;margin-top:4px}
.cm-acts .btn{flex:1;min-height:44px}
@media (prefers-reduced-motion:reduce){.cm-tog::after{transition:none}}
@media (max-width:480px){.cm-m{padding:22px 16px 18px}}
</style>
<script id="cm-js">
(function () {
  'use strict';
  /* CM.list = [{ id, kind 'work'|'club'|'practice'|'other', name, days 'MTWRFSU', s, e (minutes), busy }] — yours, every week,
     from commitments (owner-only; RUN 18) or this device. CM.fr = { [friend id]: [{ days, s, e }] } — friends' Busy times from
     friend_busy_blocks(): only items they left on, never the name or kind. */
  var CM = { list: [], fr: {}, frAt: 0, frErr: false, frBusy: 0, gap: false, uid: null, retryN: 0, retryT: null, retrying: 0, loaded: false, touched: null };
  var Q = {};                                     /* one push at a time per row: a delete can never be overtaken by an older save */
  var M = null;                                   /* the open modal: { id, kind, name, days, from, to, busy, errs, saving } */
  var KIND_LAB = { work: 'Work', club: 'Club', practice: 'Sport', other: 'Other' }, KIND_ORDER = ['work', 'club', 'practice', 'other'];
  var D2 = { M: 'Mo', T: 'Tu', W: 'We', R: 'Th', F: 'Fr', S: 'Sa', U: 'Su' }, D3 = { M: 'Mon', T: 'Tue', W: 'Wed', R: 'Thu', F: 'Fri', S: 'Sat', U: 'Sun' };
  var D3L = { M: 'Monday', T: 'Tuesday', W: 'Wednesday', R: 'Thursday', F: 'Friday', S: 'Saturday', U: 'Sunday' };
  var FR_TTL = 120000, FR_ERR_TTL = 15000, RETRY_EVERY = 60000, RETRY_MAX = 8;
  function user() { try { return (typeof sbUser !== 'undefined' && sbUser) ? sbUser : null; } catch (_) { return null; } }
  function client() { try { return (typeof sb !== 'undefined' && sb) ? sb : null; } catch (_) { return null; } }
  function esc(s) { return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]; }); }
  function key(u) { return 'professify_commits_' + u; }
  function pkey(u) { return 'professify_commits_pending_' + u; }
  var okRow = function (x) { return !!x && /^[MTWRFSU]{1,7}$/.test(String(x.days || '')) && Number.isInteger(+x.s) && Number.isInteger(+x.e) && +x.s >= 0 && +x.e <= 1440 && +x.s < +x.e; };
  var norm = function (x) { return { id: String(x.id), kind: KIND_LAB[x.kind] ? x.kind : 'other', name: String(x.name || '').slice(0, 40), days: 'MTWRFSU'.split('').filter(function (d) { return String(x.days).indexOf(d) >= 0; }).join(''), s: +x.s, e: +x.e, busy: x.busy !== false }; };
  var fromRow = function (r) { return norm({ id: r.id, kind: r.kind, name: r.name, days: r.days, s: r.start_min, e: r.end_min, busy: r.busy === true }); };
  function label(x) { return String((x && x.name) || '').trim() || (x && x.kind === 'work' ? 'Work' : x && x.kind === 'club' ? 'Club' : x && x.kind === 'practice' ? 'Sport' : 'Busy'); }
  function newId() { try { if (crypto.randomUUID) return crypto.randomUUID(); } catch (_) {} return 'xxxxxxxx-xxxx-4xxx-8xxx-xxxxxxxxxxxx'.replace(/x/g, function () { return (Math.random() * 16 | 0).toString(16); }); }
  var byStart = function (a, b) { return a.s - b.s || a.e - b.e || (a.name < b.name ? -1 : 1); };

  /* ---------------------------------------------------------------- times */
  function hs(m) { var h = Math.floor(m / 60) % 24, mm = m % 60; return ((h % 12) || 12) + (mm ? ':' + (mm < 10 ? '0' : '') + mm : '') + (h >= 12 ? 'p' : 'a'); }   /* 8p, 4:30p, 11a */
  function ap(m) { return Math.floor(m / 60) % 24 >= 12 ? 'p' : 'a'; }
  function hm(m) { var h = Math.floor(m / 60) % 24, mm = m % 60; return ((h % 12) || 12) + ':' + (mm < 10 ? '0' : '') + mm; }
  /* 4:00–8:00p · 11:00a–2:00p */
  function range(s, e) { return hm(s) + (ap(s) === ap(e) ? '' : ap(s)) + '–' + hm(e) + ap(e); }
  /* 4–8p · 11a–1p · 9:30–11a */
  function rangeShort(s, e) { var a = hs(s), b = hs(e); return ap(s) === ap(e) ? a.slice(0, -1) + '–' + b : a + '–' + b; }
  function inputTime(m) { var h = Math.floor(m / 60) % 24, mm = m % 60; return ((h % 12) || 12) + (mm ? ':' + (mm < 10 ? '0' : '') + mm : '') + (h >= 12 ? 'pm' : 'am'); }
  /* A time as people type it: 4pm · 4:30 pm · 4:30p · 4 p.m. · 16:30 · 1630 · 08:00 · noon · midnight. A bare "4" or "9:30" could be
     either half of the day, so it is not guessed. → { ok, min, why: 'empty'|'ampm'|'bad' } */
  function parseTime(raw, isEnd) {
    var s = String(raw == null ? '' : raw).toLowerCase().replace(/[\s.]/g, '');
    if (!s) return { ok: false, min: null, why: 'empty' };
    if (s === 'noon') return { ok: true, min: 720 };
    if (s === 'midnight') return { ok: true, min: isEnd ? 1440 : 0 };
    var m = /^(\d{1,2}):?(\d{2})?(am|pm|a|p)?$/.exec(s);
    if (!m) return { ok: false, min: null, why: 'bad' };
    var h = +m[1], mi = m[2] ? +m[2] : 0, a = m[3] ? m[3].charAt(0) : '';
    if (mi > 59) return { ok: false, min: null, why: 'bad' };
    if (a) { if (h < 1 || h > 12) return { ok: false, min: null, why: 'bad' }; h = (h % 12) + (a === 'p' ? 12 : 0); }
    else if (!(h >= 13 || (m[1].length === 2 && m[1].charAt(0) === '0'))) return { ok: false, min: null, why: h > 23 ? 'bad' : 'ampm' };
    if (h > 23) return { ok: false, min: null, why: 'bad' };
    var v = h * 60 + mi;
    if (isEnd && v === 0) v = 1440;
    return { ok: true, min: v };
  }
  var daysText = function (days) { return 'MTWRFSU'.split('').filter(function (d) { return days.indexOf(d) >= 0; }).map(function (d) { return D3[d]; }).join(' '); };

  /* ---------------------------------------------------------------- yours: this device first, then the account */
  function readLocal(u) { try { var a = JSON.parse(localStorage.getItem(key(u)) || '[]'); return (Array.isArray(a) ? a : []).filter(okRow).map(norm).sort(byStart); } catch (_) { return []; } }
  function writeLocal(u, list) { try { localStorage.setItem(key(u), JSON.stringify(list)); } catch (_) {} }
  function readPend(u) { try { var p = JSON.parse(localStorage.getItem(pkey(u)) || '{}'); return p && typeof p === 'object' ? p : {}; } catch (_) { return {}; } }
  function writePend(u, p) { try { if (Object.keys(p).length) localStorage.setItem(pkey(u), JSON.stringify(p)); else localStorage.removeItem(pkey(u)); } catch (_) {} }
  function pendCount() { var u = CM.uid; return u ? Object.keys(readPend(u)).length : 0; }
  /* a missing table is a gap (kept here, quietly); anything else — a 42501 too — is a failure to report */
  function gapOf(err) { var c = String((err && err.code) || ''); return c === '42P01' || c === 'PGRST205' || c === '42703'; }
  var same = function (a, b) { return !!a && !!b && JSON.stringify(a) === JSON.stringify(b); };
  var saveMsg = 'Couldn’t save that to your account yet — it’s kept on this device.';
  var dropMsg = 'Couldn’t remove that from your account yet — friends can still see it as Busy until it goes through.';

  async function load() {
    var u = user(), c = client(); if (!u || !c) return;
    var uid = u.id, r;
    CM.touched = {};                                                       /* rows saved or deleted while this read is in flight win over it */
    try { r = await c.from('commitments').select('id,kind,name,days,start_min,end_min,busy').eq('user_id', uid).order('start_min'); } catch (e) { r = { error: { message: String(e) } }; }
    var touched = CM.touched || {}; CM.touched = null;
    if (CM.uid !== uid || !user() || user().id !== uid) return;            /* signed out or switched while this was in flight */
    CM.loaded = true;
    if (r.error) { if (gapOf(r.error)) CM.gap = true; repaint(); return; }
    CM.gap = false;
    var pend = readPend(uid), cur = {}; CM.list.forEach(function (x) { cur[x.id] = x; });
    var out = (Array.isArray(r.data) ? r.data : []).filter(function (x) { return okRow({ days: x.days, s: x.start_min, e: x.end_min }); }).map(fromRow).filter(function (x) { return pend[x.id] !== 'drop' && !(touched[x.id] && !cur[x.id]); })
      .map(function (x) { return (pend[x.id] === 'save' || touched[x.id]) && cur[x.id] ? cur[x.id] : x; });
    Object.keys(cur).forEach(function (id) { if ((pend[id] === 'save' || touched[id]) && !out.some(function (o) { return o.id === id; })) out.push(cur[id]); });
    CM.list = out.sort(byStart); writeLocal(uid, CM.list);
    if (Object.keys(pend).length) { await retry(true); }
    repaint();
  }
  /* up to the account (gone: removes it). Returns what to tell the student, or null. */
  function push(uid, x, gone) {
    var k = uid + ':' + x.id, run = (Q[k] || Promise.resolve()).then(function () { return pushNow(uid, x, gone); });
    Q[k] = run.catch(function () {});
    return run;
  }
  async function pushNow(uid, x, gone) {
    if (CM.gap) return null;
    var c = client(); if (!c) return null;
    if (!gone && readPend(uid)[x.id] === 'drop') return null;               /* deleted since: do not bring it back */
    var q;
    try {
      q = gone ? await c.from('commitments').delete().eq('id', x.id).eq('user_id', uid)
        : await c.from('commitments').upsert({ id: x.id, user_id: uid, kind: x.kind, name: x.name || null, days: x.days, start_min: x.s, end_min: x.e, busy: !!x.busy }, { onConflict: 'id' });
    } catch (e) { q = { error: { message: String((e && e.message) || e) } }; }
    if (q.error) {
      if (gapOf(q.error)) { if (CM.uid === uid) CM.gap = true; return null; }
      return gone ? dropMsg : saveMsg;
    }
    /* it went up: no longer waiting — unless it was changed again meanwhile (that change has its own push) */
    var p = readPend(uid);
    if (gone ? p[x.id] === 'drop' : (p[x.id] === 'save' && same(readLocal(uid).filter(function (y) { return y.id === x.id; })[0], x))) { delete p[x.id]; writePend(uid, p); }
    return null;
  }
  async function saveMine(x) {
    var u = user(); if (!u || CM.uid !== u.id) return saveMsg;
    var uid = u.id; x = norm(x);
    if (CM.touched) CM.touched[x.id] = 1;
    var i = CM.list.findIndex(function (y) { return y.id === x.id; });
    if (i >= 0) CM.list[i] = x; else CM.list.push(x);
    CM.list.sort(byStart); writeLocal(uid, CM.list);
    var p = readPend(uid); p[x.id] = 'save'; writePend(uid, p);
    repaint();
    var e = await push(uid, x, false);
    if (e) armRetry();
    if (CM.uid === uid) repaint();
    return e;
  }
  async function dropMine(id) {
    var u = user(); if (!u || CM.uid !== u.id) return dropMsg;
    var uid = u.id, x = CM.list.filter(function (y) { return y.id === id; })[0]; if (!x) return null;
    if (CM.touched) CM.touched[id] = 1;
    CM.list = CM.list.filter(function (y) { return y.id !== id; }); writeLocal(uid, CM.list);
    var p = readPend(uid); p[id] = 'drop'; writePend(uid, p);
    repaint();
    var e = await push(uid, x, true);
    if (e) armRetry();
    if (CM.uid === uid) repaint();
    return e;
  }
  /* what is still waiting goes up when we are back online, the tab comes to the front, and on a slow timer */
  async function retry(inLoad) {
    var u = user(); if (!u || CM.uid !== u.id || CM.gap || (CM.retrying && !inLoad)) return;
    var uid = u.id, p = readPend(uid), ids = Object.keys(p); if (!ids.length) return;
    CM.retrying = 1; var failed = 0;
    try {
      for (var k = 0; k < ids.length; k++) {
        var id = ids[k], want = readPend(uid)[id], x = CM.list.filter(function (y) { return y.id === id; })[0];
        if (!want) continue;
        if (want === 'drop') x = { id: id };
        if (!x) { var pp = readPend(uid); if (pp[id] === 'save') { delete pp[id]; writePend(uid, pp); } continue; }
        if (await push(uid, x, want === 'drop')) failed++;
        if (CM.uid !== uid) return;
      }
    } finally { CM.retrying = 0; }
    if (failed) armRetry(); else if (!inLoad) repaint();
  }
  function armRetry() {
    if (CM.retryT || CM.retryN >= RETRY_MAX) return;
    CM.retryN++;
    CM.retryT = setTimeout(function () { CM.retryT = null; retry(); }, RETRY_EVERY);
  }

  /* ---------------------------------------------------------------- friends' Busy */
  async function loadFriends(force) {
    var u = user(), c = client(); if (!u || !c || CM.frBusy) return;
    if (!force && CM.frAt && Date.now() - CM.frAt < (CM.frErr ? FR_ERR_TTL : FR_TTL)) return;
    CM.frBusy = 1;
    var uid = u.id, r, timer;
    try { r = await Promise.race([c.rpc('friend_busy_blocks'), new Promise(function (_, no) { timer = setTimeout(function () { no(new Error('timeout')); }, 10000); })]); } catch (e) { r = { error: { message: String((e && e.message) || e) } }; }
    clearTimeout(timer);
    CM.frBusy = 0;
    if (CM.uid !== uid || !user() || user().id !== uid) return;
    CM.frAt = Date.now(); var wasErr = CM.frErr; CM.frErr = !!r.error;
    var out = {};
    if (!r.error) (Array.isArray(r.data) ? r.data : []).forEach(function (x) {
      if (!x || !x.user_id) return;
      var b = { days: String(x.days || ''), s: +x.start_min, e: +x.end_min };
      if (okRow(b)) (out[x.user_id] = out[x.user_id] || []).push(b);
    });
    var changed = wasErr !== CM.frErr || JSON.stringify(out) !== JSON.stringify(CM.fr);
    CM.fr = out;
    if (changed) repaint(true);
  }

  /* ---------------------------------------------------------------- the blocks the weeks draw */
  /* meet-shaped, like the sections the weeks already carry: yours by name (only you see them), a friend's as Busy. */
  function blocks(who) {
    var me = user(), isMe = !who || who === 'me' || typeof who === 'object' || (me && who === me.id);
    if (!me || CM.uid !== me.id) return [];
    if (isMe) {
      return CM.list.map(function (x) {
        var l = label(x);
        return { id: x.id, code: l, name: l, key: 'cm:' + x.id, crn: '', prof: '', label: l, mine: true, cm: 'mine', busy: x.busy, kind: x.kind,
          meet: { days: x.days.split('').map(function (d) { return D2[d]; }), start: x.s, end: x.e } };
      });
    }
    return (CM.fr[who] || []).map(function (x, i) {
      return { id: 'b' + i, code: 'Busy', name: 'Busy', key: 'cm:' + who + ':' + i, crn: '', prof: '', label: 'Busy', mine: false, cm: 'friend',
        meet: { days: x.days.split('').map(function (d) { return D2[d]; }), start: x.s, end: x.e } };
    });
  }
  function calBlocksHtml(list, d, lo, ppm) {
    return (list || []).filter(function (b) { return b.meet.days.indexOf(d) >= 0; }).map(function (b) {
      var top = (b.meet.start - lo) * ppm, h = Math.max(16, (b.meet.end - b.meet.start) * ppm);
      var al = (b.mine ? b.label : 'Busy') + ', ' + range(b.meet.start, b.meet.end), st = 'top:' + top.toFixed(1) + 'px;height:' + h.toFixed(1) + 'px';
      if (b.mine) return '<button type="button" class="cal-cm" data-cm-act="edit" data-id="' + esc(b.id) + '" style="' + st + '" aria-label="' + esc('Edit ' + al) + '" title="' + esc(al) + '"><span>' + esc(b.label) + '</span></button>';
      return '<span class="cal-cm fr" role="img" style="' + st + '" aria-label="' + esc(al) + '" title="' + esc(al) + '"><span>Busy</span></span>';
    }).join('');
  }
  /* Home's small "My schedule": hatched, no words (the column is 40px wide); the title carries them */
  function miniOwnHtml(list, d, lo, span, H) {
    return (list || []).filter(function (b) { return b.meet.days.indexOf(d) >= 0; }).map(function (b) {
      var top = ((b.meet.start - lo) / span) * H, h = Math.max(((b.meet.end - b.meet.start) / span) * H, 6), al = b.label + ', ' + range(b.meet.start, b.meet.end);
      return '<div class="hmc-cm" role="img" style="top:' + top.toFixed(1) + 'px;height:' + h.toFixed(1) + 'px" aria-label="' + esc(al) + '" title="' + esc(al) + '"></div>';
    }).join('');
  }
  function pushBusy(out, who) {
    if (!who) return;
    blocks(who).forEach(function (b) {
      b.meet.days.forEach(function (d) { var di = ['Mo', 'Tu', 'We', 'Th', 'Fr'].indexOf(d); if (di >= 0) out.push({ di: di, s: b.meet.start, e: b.meet.end, code: b.label }); });
    });
  }

  /* ---------------------------------------------------------------- overlaps */
  function hitsFor(meet) {
    var out = [];
    if (!meet || !meet.days) return out;
    blocks('me').forEach(function (b) {
      var common = meet.days.filter(function (d) { return b.meet.days.indexOf(d) >= 0; });
      if (common.length && meet.start < b.meet.end && b.meet.start < meet.end) out.push({ b: b, days: common });
    });
    return out;
  }
  var dayWords = function (days) { var inv = { Mo: 'Mon', Tu: 'Tue', We: 'Wed', Th: 'Thu', Fr: 'Fri', Sa: 'Sat', Su: 'Sun' }; return days.map(function (d) { return inv[d]; }).join('/'); };
  var hitWords = function (h) { return h.b.label + ' ' + dayWords(h.days) + ' ' + rangeShort(h.b.meet.start, h.b.meet.end); };
  function chipHtml(sec) {
    var mt = (sec && sec.days && typeof parseMeet === 'function') ? parseMeet(sec.days) : null; if (!mt) return '';
    var hits = hitsFor(mt); if (!hits.length) return '';
    var t = 'Overlaps ' + hitWords(hits[0]) + (hits.length > 1 ? ' +' + (hits.length - 1) : '');
    return '<span class="cs-cm" title="' + esc(t + ' — in Work & activities on My classes') + '">' + esc(t) + '</span>';
  }
  /* My classes' pill: the sections you are in that meet during one */
  function flag(conf) {
    var items = [], seen = {};
    ((conf && conf.meets) || []).forEach(function (m) {
      hitsFor(m.meet).forEach(function (h) { var k = m.code + '|' + h.b.id; if (seen[k]) return; seen[k] = 1; items.push({ code: m.code, h: h }); });
    });
    if (!items.length) return null;
    var labels = []; items.forEach(function (it) { if (labels.indexOf(it.h.b.label) < 0) labels.push(it.h.b.label); });
    return { key: 'cm', tone: 'note', label: labels.length === 1 ? 'Overlaps ' + labels[0] : 'Overlaps ' + labels.length + ' of your activities',
      detail: '<p>These meet during something in Work &amp; activities.</p><ul class="sf-list">' + items.map(function (it) {
        return '<li><b>' + esc(it.code) + '</b> overlaps ' + esc(hitWords(it.h)) + '</li>'; }).join('') + '</ul>' };
  }

  /* ---------------------------------------------------------------- the card */
  function cardHtml() {
    var u = user(); if (!u || CM.uid !== u.id) return '';
    var rows = CM.list.map(function (x) {
      var l = label(x), line = daysText(x.days) + ' · ' + range(x.s, x.e) + ' · ' + (x.busy ? 'friends see Busy' : 'only you');
      return '<li class="cm-li"><button type="button" class="cm-row" data-cm-act="edit" data-id="' + esc(x.id) + '" aria-label="' + esc('Edit ' + l + ', ' + line) + '">'
        + '<span class="cm-sw" aria-hidden="true"></span><span class="cm-tx"><b>' + esc(l) + '</b> · ' + esc(line) + '</span></button>'
        + '<button type="button" class="cm-x" data-cm-act="drop" data-id="' + esc(x.id) + '" aria-label="' + esc('Delete ' + l) + '" title="Delete"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M4 7h16M10 11v6M14 11v6M6 7l1 12a2 2 0 0 0 2 2h6a2 2 0 0 0 2-2l1-12M9 7V4h6v3"></path></svg></button></li>';
    }).join('');
    var n = pendCount();
    return '<section class="cm-card" data-cm-card="1" aria-label="Work &amp; activities"><div class="cm-h"><h3>Work &amp; activities</h3><button type="button" class="cm-btn cm-add" data-cm-act="add">+ Add</button></div>'
      + (rows ? '<ul class="cm-list">' + rows + '</ul>' : '<div class="cm-none">Nothing added yet</div>')
      + (n || (CM.gap && CM.list.length) ? '<div class="cm-note" data-cm-note="1">' + (CM.gap ? 'Kept on this device only.' : 'Kept on this device — not saved to your account yet.') + '</div>' : '')
      + '</section>';
  }
  function slotHtml() { return '<div class="cm-slot">' + cardHtml() + '</div>'; }
  /* draw again everywhere yours or a friend's shows */
  function repaint(friendsOnly) {
    try { if (!friendsOnly && document.getElementById('watchMineOut') && typeof renderMyClasses === 'function') renderMyClasses(); } catch (_) {}
    try { if (typeof hmRenderRailL === 'function') hmRenderRailL(); } catch (_) {}
    try { if (typeof hmRenderFeed === 'function') hmRenderFeed(); } catch (_) {}
  }
  function focusLive(id) {
    var el = (id && document.querySelector('.cm-row[data-id="' + id + '"]')) || document.querySelector('.cm-add');
    if (el) { try { el.focus({ preventScroll: true }); } catch (_) {} }
  }

  /* ---------------------------------------------------------------- the modal */
  function back() {
    var b = document.getElementById('cmBack');
    if (!b) {
      b = document.createElement('div'); b.id = 'cmBack'; b.className = 'mback';
      b.innerHTML = '<div class="modal cm-modal" id="cmModal" role="dialog" aria-modal="true" aria-labelledby="cmTitle"></div>';
      b.addEventListener('click', function (e) { if (e.target === b) closeModal(); });
      document.body.appendChild(b);
    }
    return b;
  }
  function err(id, text) { return text ? '<div class="cm-err" id="' + id + '" role="alert">' + esc(text) + '</div>' : ''; }
  function modalHtml() {
    var E = M.errs || {}, busy = !!M.saving;
    var kinds = KIND_ORDER.map(function (k) { return '<button type="button" class="cm-k' + (M.kind === k ? ' on' : '') + '" data-cm-act="kind" data-kind="' + k + '" data-cm-key="k:' + k + '" aria-pressed="' + (M.kind === k) + '">' + KIND_LAB[k] + '</button>'; }).join('');
    var days = 'MTWRFSU'.split('').map(function (d) { var on = M.days.indexOf(d) >= 0; return '<button type="button" class="cm-d' + (on ? ' on' : '') + '" data-cm-act="day" data-day="' + d + '" data-cm-key="d:' + d + '" aria-pressed="' + on + '" aria-label="' + D3L[d] + '">' + (d === 'R' ? 'Th' : d === 'S' ? 'Sa' : d === 'U' ? 'Su' : d) + '</button>'; }).join('');
    return '<button type="button" class="mclose" data-cm-act="close" aria-label="Close">&times;</button><div class="cm-m">'
      + '<h2 class="rate-h" id="cmTitle">' + (M.id ? 'Edit ' + esc(label({ name: M.name, kind: M.kind })) : 'Add work or an activity') + '</h2>'
      + '<div><span class="cm-lab" id="cmKindL">What is it</span><div class="cm-kinds" role="group" aria-labelledby="cmKindL">' + kinds + '</div></div>'
      + '<div><label class="cm-lab" for="cmName">Name (only you see it)</label><input id="cmName" class="cm-in" type="text" maxlength="40" autocomplete="off" data-cm-key="name" placeholder="' + esc(KIND_LAB[M.kind]) + '" value="' + esc(M.name) + '"></div>'
      + '<div><span class="cm-lab" id="cmDaysL">Which days</span><div class="cm-days" role="group" aria-labelledby="cmDaysL"' + (E.days ? ' aria-describedby="cmErrDays"' : '') + '>' + days + '</div>' + err('cmErrDays', E.days) + '</div>'
      + '<div class="cm-two"><div><label class="cm-lab" for="cmFrom">From</label><input id="cmFrom" class="cm-in" type="text" autocomplete="off" autocapitalize="off" spellcheck="false" data-cm-key="from" placeholder="4pm" value="' + esc(M.from) + '"' + (E.from ? ' aria-invalid="true" aria-describedby="cmErrFrom"' : '') + '>' + err('cmErrFrom', E.from) + '</div>'
      + '<div><label class="cm-lab" for="cmTo">To</label><input id="cmTo" class="cm-in" type="text" autocomplete="off" autocapitalize="off" spellcheck="false" data-cm-key="to" placeholder="8pm" value="' + esc(M.to) + '"' + (E.to ? ' aria-invalid="true" aria-describedby="cmErrTo"' : '') + '>' + err('cmErrTo', E.to) + '</div></div>'
      + '<div class="cm-sr"><span class="cm-srl" id="cmBusyL">Friends see Busy<em>They see “Busy”, never what it is</em></span><button type="button" class="cm-tog" role="switch" aria-checked="' + !!M.busy + '" aria-labelledby="cmBusyL" data-cm-act="busy" data-cm-key="busy"></button></div>'
      + '<div class="cm-acts"><button type="button" class="btn primary" data-cm-act="save" data-cm-key="save"' + (busy ? ' aria-disabled="true"' : '') + '>' + (busy ? 'Saving…' : 'Save') + '</button>'
      + (M.id ? '<button type="button" class="btn" data-cm-act="dropm" data-cm-key="dropm"' + (busy ? ' aria-disabled="true"' : '') + '>Delete</button>' : '') + '</div></div>';
  }
  function paintModal() {
    var el = document.getElementById('cmModal'); if (!el || !M) return;
    var a = document.activeElement, k = a && a.getAttribute && a.getAttribute('data-cm-key'), inside = a && el.contains(a), caret = null;
    if (inside && a.tagName === 'INPUT') { try { caret = a.selectionStart; } catch (_) {} }
    el.innerHTML = modalHtml();
    if (inside && k) { var n = el.querySelector('[data-cm-key="' + k + '"]'); if (n && !n.disabled) { n.focus({ preventScroll: true }); if (caret != null && n.tagName === 'INPUT') { try { n.setSelectionRange(caret, caret); } catch (_) {} } } }
  }
  function readFields() {
    if (!M) return;
    var g = function (id) { return document.getElementById(id); };
    if (g('cmName')) M.name = String(g('cmName').value || '').slice(0, 40);
    if (g('cmFrom')) M.from = String(g('cmFrom').value || '').slice(0, 24);
    if (g('cmTo')) M.to = String(g('cmTo').value || '').slice(0, 24);
  }
  function openModal(id) {
    var u = user(); if (!u || CM.uid !== u.id) return;
    var x = id ? CM.list.filter(function (y) { return y.id === id; })[0] : null;
    if (id && !x) return;
    M = x ? { id: x.id, kind: x.kind, name: x.name, days: x.days, from: inputTime(x.s), to: inputTime(x.e), busy: x.busy, errs: {}, saving: 0 }
          : { id: '', kind: 'work', name: '', days: '', from: '', to: '', busy: true, errs: {}, saving: 0 };
    var b = back(); paintModal();
    b.classList.add('open'); document.body.style.overflow = 'hidden';
    try { openModalA11y('cmBack'); } catch (_) {}
    setTimeout(function () { var f = document.getElementById('cmName'); if (f) { try { f.focus({ preventScroll: true }); } catch (_) {} } }, 60);
  }
  function closeModal(focusId) {
    var b = document.getElementById('cmBack'); if (b) b.classList.remove('open');
    var id = focusId !== undefined ? focusId : (M && M.id);
    M = null;
    document.body.style.overflow = document.querySelector('.mback.open') ? 'hidden' : '';
    try { closeModalA11y(); } catch (_) {}
    focusLive(id);                          /* the row you came from may have been redrawn: focus the live one */
  }
  function toast(m) { try { frToast(m); } catch (_) {} }
  async function doSave() {
    if (!M || M.saving) return;
    readFields();
    var E = {}, f = parseTime(M.from, false), t = parseTime(M.to, true);
    if (!M.days) E.days = 'Pick at least one day.';
    var why = function (p, w) { return p.why === 'empty' ? 'Add ' + w + ' time.' : p.why === 'ampm' ? 'Add am or pm, like 4pm.' : 'Try a time like 4pm, 4:30 pm or 16:30.'; };
    if (!f.ok) E.from = why(f, 'a start');
    if (!t.ok) E.to = why(t, 'an end');
    if (f.ok && t.ok && t.min <= f.min) E.to = 'End has to be after the start.';
    if (E.days || E.from || E.to) {
      M.errs = E; paintModal();
      var first = E.from ? 'cmFrom' : E.to ? 'cmTo' : null, el = first ? document.getElementById(first) : document.querySelector('#cmModal .cm-d');
      if (el) { try { el.focus({ preventScroll: true }); } catch (_) {} }
      return;
    }
    var mm = M, x = { id: M.id || newId(), kind: M.kind, name: String(M.name || '').trim(), days: M.days, s: f.min, e: t.min, busy: !!M.busy }, isNew = !M.id;
    M.errs = {}; M.saving = 1; paintModal();
    var e; try { e = await saveMine(x); } catch (z) { e = saveMsg; }
    mm.saving = 0;
    if (M === mm) closeModal(x.id);
    toast(e || (CM.gap ? 'Saved on this device' : label(x) + (isNew ? ' added' : ' saved')));
  }
  async function doDrop(id) {
    var x = CM.list.filter(function (y) { return y.id === id; })[0]; if (!x) return;
    var l = label(x), e; try { e = await dropMine(id); } catch (z) { e = dropMsg; }
    toast(e || l + ' removed');
    focusLive('');
  }
  document.addEventListener('click', function (e) {
    var t = e.target && e.target.closest ? e.target.closest('[data-cm-act]') : null; if (!t) return;
    var a = t.getAttribute('data-cm-act');
    if (a === 'add') openModal('');
    else if (a === 'edit') openModal(t.getAttribute('data-id'));
    else if (a === 'drop') doDrop(t.getAttribute('data-id'));
    else if (a === 'close') closeModal();
    else if (a === 'kind') { if (!M) return; readFields(); M.kind = t.getAttribute('data-kind'); paintModal(); }
    else if (a === 'day') { if (!M) return; readFields(); var d = t.getAttribute('data-day'); M.days = 'MTWRFSU'.split('').filter(function (c) { return c === d ? M.days.indexOf(c) < 0 : M.days.indexOf(c) >= 0; }).join(''); if (M.errs) delete M.errs.days; paintModal(); }
    else if (a === 'busy') { if (!M) return; readFields(); M.busy = !M.busy; paintModal(); }
    else if (a === 'save') doSave();
    else if (a === 'dropm') { if (!M || M.saving) return; var id = M.id; closeModal(''); doDrop(id); }
  });
  document.addEventListener('input', function (e) {
    var t = e.target; if (!M || !t || !/^cm(Name|From|To)$/.test(t.id || '')) return;
    readFields();
    var k = t.id === 'cmFrom' ? 'from' : t.id === 'cmTo' ? 'to' : '';
    if (k && M.errs && M.errs[k]) { delete M.errs[k]; t.removeAttribute('aria-invalid'); t.removeAttribute('aria-describedby'); var er = document.getElementById('cmErr' + (k === 'from' ? 'From' : 'To')); if (er) er.remove(); }
  }, true);
  document.addEventListener('keydown', function (e) {
    var b = document.getElementById('cmBack'); if (!b || !b.classList.contains('open')) return;
    if (e.key === 'Escape' || e.key === 'Esc') { e.preventDefault(); e.stopPropagation(); closeModal(); }
    else if (e.key === 'Enter' && e.target && /^cm(Name|From|To)$/.test(e.target.id || '')) { e.preventDefault(); doSave(); }
  }, true);
  window.addEventListener('online', function () { retry(); });
  document.addEventListener('visibilitychange', function () { if (document.visibilityState === 'visible') { retry(); loadFriends(false); } });
  setInterval(function () { if (document.visibilityState !== 'hidden') loadFriends(false); }, 60000);

  /* ---------------------------------------------------------------- signing in and out */
  function boot() {
    var u = user();
    if (!u) { reset(); return; }
    if (CM.uid !== u.id) { if (CM.uid) reset(); CM.uid = u.id; CM.list = readLocal(u.id); }
    repaint();
    load().then(function () { loadFriends(true); });
  }
  function reset() {
    CM.list = []; CM.fr = {}; CM.frAt = 0; CM.frErr = false; CM.frBusy = 0; CM.gap = false; CM.uid = null; CM.loaded = false; CM.retryN = 0; CM.retrying = 0;
    clearTimeout(CM.retryT); CM.retryT = null;
    M = null;
    var b = document.getElementById('cmBack'); if (b && b.classList.contains('open')) { b.classList.remove('open'); document.body.style.overflow = document.querySelector('.mback.open') ? 'hidden' : ''; try { closeModalA11y(); } catch (_) {} }
    repaint();
  }
  window.cmBoot = boot;
  window.cmReset = reset;
  window.cmBlocks = blocks;
  window.cmCalBlocksHtml = calBlocksHtml;
  window.cmMiniOwnHtml = miniOwnHtml;
  window.cmPushBusy = pushBusy;
  window.cmChipHtml = chipHtml;
  window.cmFlag = flag;
  window.cmSlotHtml = slotHtml;
  window.cmEnsureSlot = function (out) { if (out && !out.querySelector('.cm-slot')) out.insertAdjacentHTML('beforeend', slotHtml()); };
  window.cmHs = hs;
  window.TCCommit = { parseTime: parseTime, state: CM, save: saveMine, drop: dropMine, retry: retry, loadFriends: loadFriends, hitsFor: hitsFor, range: range, rangeShort: rangeShort, load: load };
}());
</script>
<!-- CM:END -->
'''
one("""<!-- PLANS:BEGIN (apply-plans.mjs""", BLOCK + """<!-- PLANS:BEGIN (apply-plans.mjs""")
f.write_text(s)
print('ok')
