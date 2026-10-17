#!/usr/bin/env python3
"""sem-left, 2026-10-16 (index.html only): two semester-transition leftovers.

1. The synthesized four-year plan (the generator that builds a plan for every major without a hand-authored one; it feeds
   Schedule > Plans, the Builder's major plan and the degree-progress ledger) padded each term to 13 units with 4-unit GE
   slots - quarter arithmetic. A semester term is ~15 units of 3-unit classes (full time is 12-18). It now pads Year 1 and
   Years 2-4 up to ~15 units with 3-unit slots, and a concentration course is 3 units. Only Fall and Spring are generated
   (the generator never made Winter or Summer terms; nothing about quarter-era history changes - those are the logged classes,
   not this plan). Every total (term units, year units, 'N courses - U units', the category bars) sums the slot units,
   so they follow.
2. Explore on Fall 2026 (the current term, read only): the right rail ("Still need", "Saved classes", "Where your friends are")
   is about the NEXT term - you can no longer register for Fall. It stays about Spring 2027 and now says so: its line starts
   "For Spring 2027". Its rows open the Spring 2027 class page (they used to open the Fall page, because Explore was on Fall).
   Also: the config comment that said "quarter-end dates" says term-end dates (the QUARTER_END key itself stays).
Usage: python3 sem-left-2026-10-16.py <repo>
"""
import sys, pathlib
root = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else '.')
f = root / 'index.html'
s = f.read_text()
if 'sem-left (2026-10-16)' in s:
    sys.exit('already patched')


def one(old, new):
    global s
    n = s.count(old)
    assert n == 1, (n, old[:140])
    s = s.replace(old, new)


# ---- 1. the synthesized plan: semester units -------------------------------------------------------------------------
one("""        while(uu(slots)<13&&slots.length<5){var un=uu(slots)<=11?4:3;slots.push({id:mkId('ge1'+tm+'p'+slots.length),title:'GE',units:un,type:'ge'});}""",
    """        /* sem-left (2026-10-16): a semester term is ~15 units of 3-unit classes (12-18 is full time), not 13 units of 4-unit slots */
        while(uu(slots)<=12&&slots.length<6){slots.push({id:mkId('ge1'+tm+'p'+slots.length),title:'GE',units:3,type:'ge'});}""")
one("""title:'Concentration course',units:4,type:'concentration'""",
    """title:'Concentration course',units:3,type:'concentration'""")
one("""          while(uu(slots)<13&&pad<2){var un=uu(slots)<=11?4:3;slots.push({id:mkId('ge'+yr+tm+pad),title:""",
    """          while(uu(slots)<=12&&pad<5){var un=3;slots.push({id:mkId('ge'+yr+tm+pad),title:""")

# ---- config comment ---------------------------------------------------------------------------------------------------
one("""  // quarter-end dates to turn it on.""", """  // term-end dates to turn it on (the key is still called QUARTER_END).""")

# ---- 2. Explore on Fall: the rail is about Spring and says so --------------------------------------------------------
one(""".exm-h p{margin:2px 0 0;font-size:var(--t-body);color:var(--faint);line-height:1.35}""",
    """.exm-h p{margin:2px 0 0;font-size:var(--t-body);color:var(--faint);line-height:1.35}
.exm-h p .exm-for{color:var(--text-2);font-weight:650}   /* sem-left (2026-10-16) */""")

one("""function exRailClassRow(code,showMeter,seat,group){""",
    """/* sem-left (2026-10-16): while Explore shows Fall 2026 (read only) the rail beside it is still about the term you can register for.
   It says so, and its rows open that term's class page (not Fall's, which is what Explore being on Fall would otherwise pick). */
function exRailFor(){
  try{
    if(typeof fallActive==='function'&&fallActive()&&typeof fallViewId==='function'&&fallViewId()==='explore')
      return '<span class="exm-for">For '+escapeHtml(mcTermLabel())+'</span> \\u00b7 ';
  }catch(e){}
  return '';
}
function exRailOpen(code,ev){
  window._exSpringLens=true;
  try{ openClassPage(code,ev); }finally{ window._exSpringLens=false; }
}
function exRailClassRow(code,showMeter,seat,group){""")
one("""  return '<button type="button" class="exm-row" onclick="openClassPage(\\''+jsAttr(code)+'\\',event)">'
    +'<span class="exm-rt"><b>'+escapeHtml(code)+'</b>'+exNeedTag(group)""",
    """  return '<button type="button" class="exm-row" onclick="exRailOpen(\\''+jsAttr(code)+'\\',event)">'
    +'<span class="exm-rt"><b>'+escapeHtml(code)+'</b>'+exNeedTag(group)""")
one("""  return '<button type="button" class="exm-row exm-row-fr" onclick="openClassPage(\\''+jsAttr(w.code)+'\\',event)">'""",
    """  return '<button type="button" class="exm-row exm-row-fr" onclick="exRailOpen(\\''+jsAttr(w.code)+'\\',event)">'""")
one("""function fallLensForOpen(code,forProf){
  if(!mcTwoTerms())return false;""",
    """function fallLensForOpen(code,forProf){
  if(!mcTwoTerms())return false;
  if(window._exSpringLens)return false;   /* sem-left (2026-10-16): a row of Explore's rail is about the term you can register for */""")
one("""      var rows=sn.items.slice(0,3).map(function(it){ return exRailClassRow(it.code,false,undefined,it.group); });""",
    """      if(exRailFor())sub=exRailFor()+sub.replace(' are offered in '+mcTermLabel(),' are offered');   /* sem-left (2026-10-16): on Fall, "For Spring 2027 - 3 of 4 ... are offered" (the term is named once) */
      var rows=sn.items.slice(0,3).map(function(it){ return exRailClassRow(it.code,false,undefined,it.group); });""")
one("""    return exMod('blue','Where your friends are',fr.length+' friend'+(fr.length===1?'':'s')+' on TermChamp',""",
    """    return exMod('blue','Where your friends are',exRailFor()+fr.length+' friend'+(fr.length===1?'':'s')+' on TermChamp',""")
one("""  return exMod('blue','Where your friends are',wf.length+' class'+(wf.length===1?'':'es')+' you\\u2019re not in yet',""",
    """  return exMod('blue','Where your friends are',exRailFor()+wf.length+' class'+(wf.length===1?'':'es')+' you\\u2019re not in yet',""")
one("""      saved.length?(saved.length+' on your list'):'Nothing on your list yet',
      saved.length
        ? '<div class="exm-b">'+saved.slice(0,5).map(function(c){ return exRailClassRow(c,false); })""",
    """      saved.length?(exRailFor()+saved.length+' on your list'):'Nothing on your list yet',
      saved.length
        ? '<div class="exm-b">'+saved.slice(0,5).map(function(c){ return exRailClassRow(c,false); })""")

f.write_text(s)
print('ok')
