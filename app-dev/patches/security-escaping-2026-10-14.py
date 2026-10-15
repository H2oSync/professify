#!/usr/bin/env python3
"""Website: a friend's class codes and terms can no longer break out of the page (defensive review, 2026-10-14).

THE HOLE. A friend can store up to 40 arbitrary characters in saved_classes.code, my_sections.code / class_nbr and
class_history.term / year through the API. The website's canonCode() passes an unknown code through unchanged (the
phone app's canonCode drops anything that is not  ^[A-Z&]{2,5}\\s*\\d{3,4}[A-Z]?$ ), and the website put those values
into HTML and into inline handlers three different, wrong ways:
  * `'` backslash-escaped only, inside onclick="...cbTap('...')" with NO html escaping — a `"` closes the attribute
    (friend's profile calendar: the Async rail and the Time TBA rail, index.html tapA / tapT, and escAcc(m.crn));
  * esc() / escAcc() inside a JS string in a handler — they escape the HTML but not `'`, so  ');evil;//  ends the
    string (Home chips hmClassChips, Home recs hmHomeRecsHtml, the class page's Save / Send / section buttons, the
    Watchlist and My Classes rows, ...). jsAttr() does both jobs in the right order;
  * `${t.term} ${t.year}` / `${h.year}` / `${n.year}` straight into innerHTML (the "friend took this" chip, a friend's
    Took tab, the notification "from <term> <year>").

THE FIX, TWO LAYERS.
 1. At the door. Where a friend's rows come into memory (the friends loader: saved_classes, my_sections, the
    now-term reads and class_history) a code that is not a course code is DROPPED, exactly as the phone does, and the
    rest are coerced: crn / class_nbr to digits (else none), term to Fall / Winter / Spring / Summer (else blank),
    year to a whole year (else blank). Real codes keep working, `&` subjects and letter suffixes included
    (CSC 1001L, A&B 123 ...). Legacy quarter numbers are NOT mapped here (no COURSE_EQUIV) — that is canonCode's job later.
 2. At the use. Every handler argument that carries a code / crn / id from the database is jsAttr()'d instead of
    esc / escAcc / escapeHtml (one regex sweep, count asserted, constants left alone), tapA / tapT use jsAttr, and
    term / year are escaped where they are printed.

The sweep rewrites `\\'' + esc|escAcc|escapeHtml(X) + '\\'` (an escaped quote, the literal closing, a concatenation, the
call, and the closing escaped quote — i.e. a JS string argument in an inline handler) to jsAttr(X). Left alone on
purpose: cpSetTab(k) and exSetGeArea(a.key), which only ever receive constants.

Usage: python3 security-escaping-2026-10-14.py <repo>
"""
import sys, re, pathlib
root = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else '.')
f = root / 'index.html'
s = f.read_text()
if 'security-escaping (2026-10-14)' in s:
    sys.exit('already patched')

def one(old, new, n=1):
    global s
    c = s.count(old)
    assert c == n, (c, n, old[:120])
    s = s.replace(old, new)

# ================================================================ 1. the door: strict friend data
one("""function canonCode(code){ var c=normCourse(code); return COURSE_EQUIV[c]||c; }
""", """function canonCode(code){ var c=normCourse(code); return COURSE_EQUIV[c]||c; }
/* security-escaping (2026-10-14) — what a FRIEND may put in memory. The phone's canonCode is this strict
   (^[A-Z&]{2,5}\\s*\\d{3,4}[A-Z]?$) and drops the rest; the website passed anything through, and a friend can store 40
   arbitrary characters in these columns. Anything that is not a course code is dropped at the door; crn to digits,
   term to a quarter / semester name, year to a whole year. Real codes (CSC 1001L, A&B 123) are untouched. */
function frCleanCode(c){
  var m=/^([A-Z&]{2,5})\\s*(\\d{3,4}[A-Z]?)$/.exec(normCourse(c));
  return m?(m[1]+' '+m[2]):'';
}
function frCleanCrn(n){ var t=String(n==null?'':n).trim(); return /^\\d{1,10}$/.test(t)?t:''; }
function frCleanTerm(t){
  var m=/^(fall|winter|spring|summer)$/i.exec(String(t==null?'':t).trim());
  return m?(m[1].charAt(0).toUpperCase()+m[1].slice(1).toLowerCase()):'';
}
function frCleanYear(y){ var n=Number(String(y==null?'':y).trim()); return (String(y==null?'':y).trim()!==''&&isFinite(n)&&n%1===0&&n>=1990&&n<=2100)?n:''; }
function frCleanPos(n){ if(n==null||n==='')return null; var v=Number(n); return (isFinite(v)&&v%1===0&&v>=0&&v<=9999)?v:null; }
/* a saved_classes / my_sections row: null if its code is not a course code, else a copy with a clean code and crn
   (and a waitlist spot that is a whole number or nothing) */
function frCleanRow(r){
  if(!r||typeof r!=='object')return null;
  var code=frCleanCode(r.code); if(!code)return null;
  var crn=frCleanCrn(r.class_nbr);
  var o=Object.assign({},r,{code:code,class_nbr:crn?crn:null});
  if('waitlist_pos' in r)o.waitlist_pos=frCleanPos(r.waitlist_pos);
  if('wl_pos' in r)o.wl_pos=frCleanPos(r.wl_pos);
  return o;
}
""")

# the friends loader
one("""    if(clsErr)console.error('[professify] friends saved_classes read failed:',clsErr.message);
""", """    if(clsErr)console.error('[professify] friends saved_classes read failed:',clsErr.message);
    if(Array.isArray(classes))classes=classes.map(frCleanRow).filter(Boolean);   /* security-escaping (2026-10-14) */
""")
one("""        fs.data.forEach(r=>{
          if(!r||!r.code)return;
          const arr=(secsMap[r.user_id]=secsMap[r.user_id]||[]);""", """        fs.data.map(frCleanRow).filter(Boolean).forEach(r=>{
          if(!r||!r.code)return;
          const arr=(secsMap[r.user_id]=secsMap[r.user_id]||[]);""")
one("""          _na.data.forEach(function(c){
            if(!c||!c.code)return;""", """          _na.data=_na.data.map(frCleanRow).filter(Boolean);   /* security-escaping (2026-10-14) */
          _na.data.forEach(function(c){
            if(!c||!c.code)return;""")
one("""          if(!_nb.error&&Array.isArray(_nb.data))_nb.data.forEach(function(r){""", """          if(!_nb.error&&Array.isArray(_nb.data))_nb.data.map(frCleanRow).filter(Boolean).forEach(function(r){""")
one("""    (hist||[]).forEach(h=>{(histMap[h.user_id]=histMap[h.user_id]||[]).push({code:h.code,term:h.term,year:h.year,professor:h.professor||'',at:h.created_at});});""",
    """    (hist||[]).forEach(h=>{
      const _hc=h?frCleanCode(h.code):'';   /* security-escaping (2026-10-14): not a course code → not shown */
      if(!_hc)return;
      (histMap[h.user_id]=histMap[h.user_id]||[]).push({code:_hc,term:frCleanTerm(h.term),year:frCleanYear(h.year),professor:h.professor||'',at:h.created_at});
    });""")

# ================================================================ 2. the use: term / year
one("function tookLabel(t){return `${t.term} ${t.year}`;}",
    "function tookLabel(t){return [t&&t.term,t&&t.year].filter(Boolean).join(' ');}   /* callers escape it — security-escaping (2026-10-14) */")
one("took this ${tookLabel(f.took)}${withWho}`;", "took this${tookLabel(f.took)?' '+escapeHtml(tookLabel(f.took)):''}${withWho}`;")
one("already took this — most recently ${tookLabel(first.took)}`);", "already took this${tookLabel(first.took)?' — most recently '+escapeHtml(tookLabel(first.took)):''}`);")
one("""<span class="ht">${escapeHtml(h.term)} ${h.year}</span>""", """<span class="ht">${escapeHtml([h.term,h.year].filter(Boolean).join(' '))}</span>""")
one("""` from ${escapeHtml(n.term)} ${n.year}`""", """` from ${escapeHtml(n.term)} ${escapeHtml(n.year)}`""")

# ================================================================ 3. the use: named sites
one("""        var tapA=String(m.code).replace(/'/g,"\\\\'");""", """        var tapA=jsAttr(m.code);""")
one("""        var tapT=String(m.code).replace(/'/g,"\\\\'");""", """        var tapT=jsAttr(m.code);""")
one("""<button class="sp-rgo" onclick="gotoSection(\\''+String(s.code).replace(/'/g,"\\\\'")+'\\')">""", """<button class="sp-rgo" onclick="gotoSection(\\''+jsAttr(s.code)+'\\')">""")
one("""gotoSection('${escAcc(s.code)}')">Choose a section →</a>`:'';""", """gotoSection('${jsAttr(s.code)}')">Choose a section →</a>`:'';""")
one("""onclick="removePastClass('${escapeHtml(h.code)}')">&times;</button>""", """onclick="removePastClass('${jsAttr(h.code)}')">&times;</button>""", 2)
one("""openClassFromFeed('${escapeHtml(h.code)}');frToast(""", """openClassFromFeed('${jsAttr(h.code)}');frToast(""")
one("""onclick="startRate('${pid}','${escapeHtml(h.code)}')">""", """onclick="startRate('${pid}','${jsAttr(h.code)}')">""")
one("""onclick="rlOpenProf('${id}','${escapeHtml(code||'')}')\"""", """onclick="rlOpenProf('${id}','${jsAttr(code||'')}')\"""")
one("""onclick="toggleWatchClass('${code}',event)">${on?WL_ON:WL_OFF}""", """onclick="toggleWatchClass('${jsAttr(code)}',event)">${on?WL_ON:WL_OFF}""")
one("""onclick="togglePlanCourse('${code}','${profs[0]}','Uploaded')">""", """onclick="togglePlanCourse('${jsAttr(code)}','${profs[0]}','Uploaded')">""")
one("""onclick="togglePlanCourse('${code}','${profId}','${term}')">""", """onclick="togglePlanCourse('${jsAttr(code)}','${profId}','${term}')">""")
one("""onclick="togglePlanFlex('${o.code}','${term}')">""", """onclick="togglePlanFlex('${jsAttr(o.code)}','${term}')">""")
one("""onclick="mcAskRemove(\\''+i.code+'\\',event)">&times;</button>""", """onclick="mcAskRemove(\\''+jsAttr(i.code)+'\\',event)">&times;</button>""")
one("""onclick="togglePick('${c.code}')">""", """onclick="togglePick('${jsAttr(c.code)}')">""")
one("""onclick="event.stopPropagation();openClassFromFeed(\\''+esc(c)+'\\')" style="cursor:pointer">""", """onclick="event.stopPropagation();openClassFromFeed(\\''+jsAttr(c)+'\\')" style="cursor:pointer">""")

# ================================================================ 4. the sweep: \'' + esc|escAcc|escapeHtml(X) + '\'  ->  jsAttr(X)
SKIP = {'k', 'a.key'}                       # constants: cpSetTab(k), exSetGeArea(a.key)
pat = re.compile(r"(\\'')\+(esc|escAcc|escapeHtml)\(((?:[^()]|\([^()]*\))*)\)\+'\\'")
n_all = 0; n_skip = 0
def rep(m):
    global n_all, n_skip
    n_all += 1
    if m.group(3).strip() in SKIP:
        n_skip += 1
        return m.group(0)
    return m.group(1) + "+jsAttr(" + m.group(3) + ")+'\\'"
s = pat.sub(rep, s)
print('sweep: %d handler string arguments seen, %d left (constants), %d switched to jsAttr' % (n_all, n_skip, n_all - n_skip))
assert n_skip == 2, n_skip
assert n_all == 95, n_all                   # the base commit's count; a new handler of this shape landing beside this needs a look

# ================================================================ 5. the Plans module's friends' rows, same door
one("""      friendPlans = r.data; friendPlansFor = {};
      r.data.forEach(function (row) {""", """      friendPlans = r.data; friendPlansFor = {};
      /* security-escaping (2026-10-14): a friend's plan entry is a (code, crn) pair — an entry whose code is not a course code or
         whose crn is not a number is dropped, as in the friends loader */
      r.data.forEach(function (row) { row.sections = (Array.isArray(row.sections) ? row.sections : []).map(function (x) { var c = x ? frCleanCode(x.code) : '', n = x ? frCleanCrn(x.class_nbr != null ? x.class_nbr : x.crn) : ''; return (c && n) ? Object.assign({}, x, { code: c, class_nbr: n }) : null; }).filter(Boolean); });
      r.data.forEach(function (row) {""")

f.write_text(s)
print('ok')
