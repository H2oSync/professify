#!/usr/bin/env python3
"""term-fix, 2026-10-16 (index.html only): the semester transition (Cal Poly moved from quarters to semesters at Fall 2026).

BUG  Explore's right rail ("Saved classes", "Still need") listed every Spring 2027 class as "0 left" in red.
     Root cause: the seat feed's course total was built as `a.seats += Math.max(0, r.available || 0)`. Spring 2027
     registration has not opened and part of the Spring scrape carries a status ("Open") but NO seat counts (available is
     NULL), and `null || 0` is 0. realSeat() then said {cls:'open', n:0}, which exSeatNum printed as "0 left". The terms were
     right (the feed is Spring's, mcTerm()); the number was an absence turned into a printed zero.
     Fix: the aggregate remembers how many of its open sections really had a count (a.avN); realSeat() gives a number only
     when every open section had one, otherwise n is null and the row says "open". An Open section whose available count is
     0 contradicts itself, so it is also "count unknown" (secSeat). seatBadge says "Open" instead of "0 open" for it. A class
     with no section in the term's feed says "Not offered Spring 2027" (muted) in the rail, never "0 left".
AUDIT (user-visible, fixed here)
     * the concentration availability line said "... · Fall 2026" for a Spring 2027 count (hard-coded label)
     * rateTermOptions() stepped back through Winter/Spring/Summer/Fall, so once Spring 2027 is the term it offered
       "Winter 2027" (there is no Winter in the semester calendar); it steps like termPrev() now
     * the Still need card said "offered next term" / "this term" (wrong once Spring is the term you are in)
     * the finals-week banner said "this quarter's ... next quarter's"
     * About / flowchart notes named "Fall 2026" as the term of the sections shown
     * NO WINTER AFTER 2026: one helper (termOk/termSeasons/termFixSelect) - the manual past-class form, the "I took it" dialog,
       the capture strip, the transcript import rows offer no Winter for 2027+, and every submit (incl. the DPR and term import)
       refuses it; termLastDone moves on at Fall 2026 Dec 22 and Spring 2027 May 14
Usage: python3 term-fix-2026-10-16.py <repo>
"""
import sys, pathlib
root = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else '.')
f = root / 'index.html'
s = f.read_text()
if 'term-fix (2026-10-16)' in s:
    sys.exit('already patched')


def one(old, new):
    global s
    n = s.count(old)
    assert n == 1, (n, old[:140])
    s = s.replace(old, new)


# ---- seat aggregates: remember how many OPEN sections really reported a count ------------------------------------
one("if(_st==='open')a.open++;else if(_st==='wait')a.wait++;",
    "if(_st==='open'){a.open++;if(r.available!=null&&+r.available>0)a.avN=(a.avN||0)+1;}else if(_st==='wait')a.wait++;   /* term-fix (2026-10-16): avN = open sections that carry a count */")
one("if(st==='open')a.open++;else if(st==='wait')a.wait++;",
    "if(st==='open'){a.open++;if(r.available!=null&&+r.available>0)a.avN=(a.avN||0)+1;}else if(st==='wait')a.wait++;")

one("""  if(a.open>0)return{label:'Open',cls:'open',n:a.seats,wl:a.wl,cap:cap,wlcap:wlcap,real:true};""",
    """  /* term-fix (2026-10-16): a total only when EVERY open section carried a count. A listing-only scrape (status, no seats)
     summed to 0 here and read "0 left" in red for a class that had not opened. No count is n:null, which says "open". */
  if(a.open>0)return{label:'Open',cls:'open',n:(((a.avN||0)===a.open&&a.seats>0)?a.seats:null),wl:a.wl,cap:cap,wlcap:wlcap,real:true};""")

one("""  return{label:'Open',cls:'open',n:(r.available==null?null:av),""",
    """  /* term-fix (2026-10-16): "Open" with 0 available contradicts itself; it is a count we do not have, not "0 left" */
  return{label:'Open',cls:'open',n:((r.available==null||av===0)?null:av),""")

one("""  var openPart=(cap!=null)?(av+'/'+cap+' open'):(av+' open');""",
    """  var openPart=(s.cls==='open'&&s.n==null)?'Open':((cap!=null)?(av+'/'+cap+' open'):(av+' open'));   /* term-fix (2026-10-16): no count is "Open", not "0 open" */""")

# ---- the rail ------------------------------------------------------------------------------------------------------
one("""  if(s.cls==='open')return (s.n!=null)?{t:s.n+' left',c:(s.n<=10?'red':'green')}:{t:'open',c:'green'};""",
    """  if(s.cls==='open')return (s.n!=null&&s.n>0)?{t:s.n+' left',c:(s.n<=10?'red':'green')}:{t:'open',c:'green'};   /* term-fix (2026-10-16): never "0 left" for an open class */""")

one("""  var num=exSeatNum(s), fill=showMeter?exSeatFill(s):null;
  var nm=exCourseName(code);""",
    """  var num=exSeatNum(s), fill=showMeter?exSeatFill(s):null;
  /* term-fix (2026-10-16): a class with no section in the chosen term's feed is not offered that term. It is not "0 left". */
  if(!s&&typeof seatFeedLoaded==='function'&&seatFeedLoaded())num={t:'Not offered '+mcTermLabel(),c:'faint'};
  var nm=exCourseName(code);""")

one(""".exm-rt .num.mid{color:var(--mid)}""",
    """.exm-rt .num.mid{color:var(--mid)}
.exm-rt .num.faint{color:var(--faint);font-weight:500}""")

one("""(offered+' of '+sn.coded+' with a course code are offered next term'""",
    """(offered+' of '+sn.coded+' with a course code are offered in '+mcTermLabel()""")
one("""'None of the '+left+' you still need have sections in our scrape this term. Cal Poly may still be running one — check the class schedule.'""",
    """'None of the '+left+' you still need have sections for '+mcTermLabel()+' in our scrape. Cal Poly may still be running one — check the class schedule.'""")

# ---- audit fixes -----------------------------------------------------------------------------------------------------
one("""return '<span class="classno" style="color:#6f9e6a" title="From the live class schedule (current term)">'+escapeHtml(t)+' · Fall 2026</span>'; }""",
    """return '<span class="classno" style="color:#6f9e6a" title="From the class schedule for the term you are choosing in">'+escapeHtml(t)+' · '+escapeHtml(mcTermLabel())+'</span>'; }   /* term-fix (2026-10-16): the label was a literal 'Fall 2026' */""")

one("""  var qi=QUARTER_SEQ.indexOf(m[1]), yr=parseInt(m[2],10);
  if(qi<0)return [];
  var out=[];
  for(var k=0;k<(n||4);k++){ out.push(QUARTER_SEQ[qi]+' '+yr); qi--; if(qi<0){qi=QUARTER_SEQ.length-1;yr--;} }
  return out;""",
    """  var tm=m[1], yr=parseInt(m[2],10);
  if(QUARTER_SEQ.indexOf(tm)<0)return [];
  var out=[];
  /* term-fix (2026-10-16): step back the way the calendar ran. Winter exists only through Winter 2026 (the last quarter year);
     Spring 2027 is preceded by Fall 2026, never a "Winter 2027". */
  for(var k=0;k<(n||4);k++){
    out.push(tm+' '+yr);
    if(tm==='Fall')tm='Summer';
    else if(tm==='Summer')tm='Spring';
    else if(tm==='Spring'){ if(yr>SEM_FIRST_FALL_Y){ tm='Fall'; yr--; } else tm='Winter'; }
    else { tm='Fall'; yr--; }
  }
  return out;""")

one("""<b>Finals week — rate this quarter's professors.</b> Takes 20 seconds and helps next quarter's students pick well.""",
    """<b>Finals week — rate this semester's professors.</b> Takes 20 seconds and helps next semester's students pick well.""")

one("""Real Cal Poly professors and confirmed Fall 2026 instructors, with ratings""",
    """Real Cal Poly professors and confirmed instructors for each semester, with ratings""")
one("""(not a confirmed Fall 2026 section).';""", """(not a confirmed section).';""")
one("""The <b style="color:var(--text-2)">exact Fall 2026 section instructor is not confirmed yet</b>""",
    """The <b style="color:var(--text-2)">exact section instructor is not confirmed yet</b>""")

one("""  if(!year||year<2015||year>thisYear+1){err.textContent=`Enter a year between 2015 and ${thisYear+1}.`;return;}
  const {error}=await sb.from('class_history')""",
    """  if(!year||year<2015||year>thisYear+1){err.textContent=`Enter a year between 2015 and ${thisYear+1}.`;return;}
  if(!termOk(term,year)){err.textContent=termNoWinterMsg();return;}   /* term-fix (2026-10-16) */
  const {error}=await sb.from('class_history')""")

# ---- NO WINTER AFTER 2026: one helper, every past-class / term entry path ------------------------------------------
one("""function termSystemWord(t){ return termIsSemester(t.term,t.year)?'semester':'quarter'; }""",
    """function termSystemWord(t){ return termIsSemester(t.term,t.year)?'semester':'quarter'; }
/* term-fix (2026-10-16): Cal Poly has no Winter term after Winter 2026 (the last quarter year). ONE rule for every picker that
   lets a student say when they took a class: the picker does not offer Winter for 2027+, and a submit refuses it. */
function termOk(season,year){ return !(season==='Winter'&&(+year)>SEM_FIRST_FALL_Y); }
function termSeasons(year){ return termOk('Winter',year)?['Fall','Winter','Spring','Summer']:['Fall','Spring','Summer']; }
function termNoWinterMsg(){ return 'Cal Poly has no Winter term since it moved to semesters in Fall 2026 — pick Fall, Spring or Summer.'; }
function termRowsBad(rows){ return (rows||[]).some(function(r){ return r&&!termOk(r.term,r.year); }); }
/* rebuild a season <select> for the year now chosen; keeps the pick when it is still offered */
function termFixSelect(sel,year,fallback){
  if(!sel)return;
  var want=termSeasons(year), have=[].map.call(sel.options,function(o){ return o.value||o.text; });
  if(have.join()===want.join())return;
  var cur=sel.value;
  sel.innerHTML=want.map(function(x){ return '<option>'+x+'</option>'; }).join('');
  sel.value=want.indexOf(cur)>=0?cur:(want.indexOf(fallback)>=0?fallback:want[0]);
}
/* the transcript-import row: its year select sits right after its season select */
function tiFixTerm(yearSel,i){
  var ts=yearSel&&yearSel.previousElementSibling; if(!ts)return;
  termFixSelect(ts,yearSel.value,'Spring');
  try{ if(typeof tiRows!=='undefined'&&tiRows[i])tiRows[i].term=ts.value; }catch(e){}
}""")

# manual add form (Past Classes)
one("""<input id="histYear" class="rate-input" style="margin:0" type="number" placeholder="2025\"""",
    """<input id="histYear" class="rate-input" style="margin:0" type="number" oninput="termFixSelect(document.getElementById('histTerm'),this.value)" placeholder="2025\"""")

# "I took it" dialog (pq)
one("""        <select id="pqYear"></select></div>""",
    """        <select id="pqYear" onchange="termFixSelect(document.getElementById('pqTerm'),this.value,'Spring')"></select></div>""")
one("""  y.innerHTML=h;
  document.getElementById('pqBack').classList.add('open');""",
    """  y.innerHTML=h;
  termFixSelect(document.getElementById('pqTerm'),y.value,'Spring');   /* term-fix (2026-10-16): no Winter for 2027+ */
  document.getElementById('pqBack').classList.add('open');""")
one("""  var term=document.getElementById('pqTerm').value, year=parseInt(document.getElementById('pqYear').value,10);
""",
    """  var term=document.getElementById('pqTerm').value, year=parseInt(document.getElementById('pqYear').value,10);
  if(!termOk(term,year)){ try{frToast(termNoWinterMsg());}catch(e){} return; }   /* term-fix (2026-10-16) */
""")

# capture strip "other term"
one("""    w.innerHTML='<select data-f="term">'+['Fall','Winter','Spring','Summer'].map(function(t){""",
    """    w.innerHTML='<select data-f="term">'+termSeasons(h.year).map(function(t){""")
one("""      +'<select data-f="year">'+yo+'</select><button type="button">Use this</button>';""",
    """      +'<select data-f="year" onchange="termFixSelect(this.parentNode.querySelector(\\'[data-f=term]\\'),this.value,\\'Spring\\')">'+yo+'</select><button type="button">Use this</button>';""")
one("""      h.term=w.querySelector('[data-f="term"]').value; h.year=+w.querySelector('[data-f="year"]').value;""",
    """      var _t2=w.querySelector('[data-f="term"]').value, _y2=+w.querySelector('[data-f="year"]').value;
      if(!termOk(_t2,_y2)){ try{frToast(termNoWinterMsg());}catch(e){} return; }   /* term-fix (2026-10-16) */
      h.term=_t2; h.year=_y2;""")
one("""  if(typeof sbUser==='undefined'||!sbUser||!sb||!code||!term||!year)return;
  var who=""",
    """  if(typeof sbUser==='undefined'||!sbUser||!sb||!code||!term||!year||!termOk(term,year))return;   /* term-fix (2026-10-16) */
  var who=""")

# transcript import: the row's season list follows its year; submits refuse
one("""+'<select onchange="tiRows['+i+'].term=this.value">'+TERMS.map(function(t){return '<option'+(t===r.term?' selected':'')+'>'+t+'</option>';}).join('')+'</select>'""",
    """+'<select onchange="tiRows['+i+'].term=this.value">'+(termOk(r.term,r.year)?'':'<option selected disabled>Term?</option>')+termSeasons(r.year).map(function(t){return '<option'+(t===r.term?' selected':'')+'>'+t+'</option>';}).join('')+'</select>'""")
one("""+'<select onchange="tiRows['+i+'].year=+this.value">'""",
    """+'<select onchange="tiRows['+i+'].year=+this.value;tiFixTerm(this,'+i+')">'""")
one("""    var res=await sb.from('class_history').upsert(rows);
    if(res.error)throw res.error;
    closeTranscriptImport();""",
    """    if(termRowsBad(rows)){ try{frToast(termNoWinterMsg());}catch(e){} return; }   /* term-fix (2026-10-16) */
    var res=await sb.from('class_history').upsert(rows);
    if(res.error)throw res.error;
    closeTranscriptImport();""")
one("""        var res=await sb.from('class_history').upsert(rows);
        if(res.error)throw res.error;
        savedPast=rows.length;""",
    """        if(termRowsBad(rows))throw new Error(termNoWinterMsg());   /* term-fix (2026-10-16) */
        var res=await sb.from('class_history').upsert(rows);
        if(res.error)throw res.error;
        savedPast=rows.length;""")
one("""    var res=await sb.from('class_history').upsert(rows);
    if(res.error)throw res.error;
    closeTermImport();""",
    """    if(termRowsBad(rows)){ try{frToast(termNoWinterMsg());}catch(e){} return; }   /* term-fix (2026-10-16) */
    var res=await sb.from('class_history').upsert(rows);
    if(res.error)throw res.error;
    closeTermImport();""")

# termLastDone: a term is done from its last day of instruction (Fall 2026: Dec 22 = TERM_ENDS; Spring 2027: May 14)
one("""  if(mo>=5)return {term:'Spring',year:y};                                    /* Jun onward */""",
    """  /* term-fix (2026-10-16): a semester is finished from its last day — Fall on Dec 22 (the config's TERM_ENDS for Fall 2026),
     Spring on May 14 (Spring 2027's last day of instruction). It said Spring of the same year for the rest of December and
     kept saying Fall until June. Quarter-era May 2026 is untouched (Spring 2026 ran to June). */
  if(y>=SEM_FIRST_FALL_Y&&mo===11&&now.getDate()>=22)return {term:'Fall',year:y};
  if(y>SEM_FIRST_FALL_Y&&mo===4&&now.getDate()>=14)return {term:'Spring',year:y};
  if(mo>=5)return {term:'Spring',year:y};                                    /* Jun onward */""")

f.write_text(s)
print('term-fix patch applied')
