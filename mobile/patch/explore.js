<script id="explore-pass2">
/* ================================================================================================
   EXPLORE, PASS 2 — 2026-09-24. Source: ~/Desktop/Term Champ Feature Map.html (09-23), which
   supersedes the 09-12 phone mock pass 1 was built from. Tate's calls on the conflicts (09-24):
   real catalog text for descriptions · Free Now stays out · Professors mode is purple (Explore
   only) · the phone header keeps the tile alone.
   ================================================================================================ */

/* ---- A real one-line description for every course the scraper has read ------------------------
   seats/scrape-seats.mjs has captured each course's description off the same PeopleSoft detail page
   it reads seats from, and upserted it into course_catalog, since before the rebrand — nothing ever
   read it. shortDesc() was written as the one seam for exactly this ("wire it here and every card
   gets it at once") and checks COURSE_SHORT. This fills COURSE_SHORT.

   The line is Cal Poly's own words, cut, never rewritten: the first sentence that is a description
   rather than a requirement ("Prerequisite: …", "3 lectures.") — at most ~96 characters, cut at a
   word with an ellipsis, trailing full stop dropped to sit in a card like a subtitle. If the table
   is missing, the column is missing, or RLS refuses the read, COURSE_SHORT stays empty and the card
   keeps its units/sections line exactly as before. Nothing is ever written in its place. */
var COURSE_SHORT=null;
var COURSE_SHORT_AT=null;
/* Sentences, the careful way (review, 09-24: a naive split turned "Study of U.S. history" into
   "Study of U"). A full stop ends a sentence only when a space and a capital or digit follow it, and
   the word before it is not an initial ("U.", "U.S."), a dotted abbreviation ("e.g", "i.e") or a
   short common one ("etc", "vs", "approx", "Dept"). A decimal never qualifies — no space follows.
   Written as a scan, not a lookbehind regex: Safari before 16.4 cannot parse one, and a syntax error
   would take this whole block down with it. */
var CS_ABBR=/^(e\.g|i\.e|etc|vs|approx|incl|esp|dept|no|nos|vol|pp|st|mr|mrs|ms|dr|prof|jr|sr|inc|co|ca|cf|fig|al)$/i;
function csSentences(t){
  var out=[], start=0;
  for(var i=0;i<t.length;i++){
    var ch=t.charAt(i); if(ch!=='.'&&ch!=='!'&&ch!=='?')continue;
    var after=t.slice(i+1);
    if(after.length&&!/^\s+[A-Z0-9("\u201c]/.test(after))continue;
    if(ch==='.'){
      var m=/([A-Za-z][A-Za-z.]*)$/.exec(t.slice(start,i)); var w=m?m[1]:'';
      /* A lone capital is an initial ("J. Smith") — except I, V and X, which in a catalog are almost
         always a course level ("Design I. Prerequisite: …"), and there the sentence really ends. */
      if((/^[A-Za-z]$/.test(w)&&!/^[IVX]$/.test(w))||/\.[A-Za-z]$/.test(w)||CS_ABBR.test(w))continue;
    }
    out.push(t.slice(start,i+1).trim()); start=i+1;
  }
  if(start<t.length&&t.slice(start).trim())out.push(t.slice(start).trim());
  return out;
}
/* Real-catalog run, 09-24 (all 2,062 rows Tate exported): 134 descriptions carry the class-search
   page around them — for a crosslisted course the scraper kept the seat table ("Status Enrl Tot Wait
   Tot ME 4404-X01 LEC (6251) … Open 32 6") and the class notes ahead of the text; selected-topics
   courses lead with a cut-off registrar link. Every one of them has the page's own "Description"
   label right before the real text. So: when the text before that label looks like the page (seat
   table, class notes, a link), keep only what follows the label that comes after all of it. A course whose text merely
   says "Hardware Description Language" has no page chrome in front and is left alone. Page chrome
   with no label to cut at shows nothing — seat numbers must never pass as a description. */
var CS_CHROME=/Enrl Tot|Wait Tot|Class Notes|Selected Topic Courses|https?:\/\//;
function csBody(t){
  if(!CS_CHROME.test(t))return t;
  /* The label that counts is the first one AFTER the last piece of page chrome — a seat row ends in
     its status and two counts ("Open 32 6"), so a crosslisted title like "Hardware Description Lang"
     inside the seat table is behind it, and a "Description" inside the real text ("Introduction to
     Hardware Description Language") is after the label we cut at, never mistaken for it (review,
     09-24: taking the LAST label silently dropped the opening words of such a description). */
  var re=/Enrl Tot|Wait Tot|Class Notes|Selected Topic Courses webpage:?|https?:\/\/\S+|(Open|Closed|Wait List) \d+ \d+/g, m, end=0;
  while((m=re.exec(t)))end=m.index+m[0].length;
  var lab=/\bDescription\s+(?=[A-Z])/g; lab.lastIndex=end;
  var l=lab.exec(t);
  if(!l)return '';
  return t.slice(l.index+l[0].length);
}
function csShortLine(desc){
  var t=csBody(String(desc||'').replace(/\s+/g,' ').trim()); if(!t)return '';
  /* The Solano note sometimes runs straight into a lower-case fragment ("Offered at Solano Campus.
     group laboratory with …"), which the splitter rightly will not break at — lift it off first. */
  t=t.replace(/^offered at solano campus\.\s*/i,''); if(!t)return '';
  var parts=csSentences(t);
  /* Not descriptions: requirements, format, and — from the real run — the Solano campus note (41
     Maritime courses open with "Offered at Solano Campus."), "Formerly …", "Also offered as …",
     "Repeatable …" and "The Class Schedule will list topic selected." */
  var skip=/^(pre|co)-?requisites?\b|^recommended\b|^concurrent\b|^\d+(\s+to\s+\d+)?\s+(lectures?|labs?|laborator(y|ies)|activit(y|ies)|seminars?|discussions?)\b|^(fulfills|satisfies)\b|^(ge|usc?p|gwr)\b|^crosslisted|^course may be|^total credit|^credit\/no credit|^not open to|^offered (at|in|only)\b|^formerly\b|^also offered as\b|^repeatable\b|^the class schedule will list\b/i;
  var keep=[];
  for(var i=0;i<parts.length;i++){ var p=parts[i].trim(); if(p&&!skip.test(p))keep.push(p); }
  if(!keep.length)return '';
  var s=keep[0].charAt(0).toUpperCase()+keep[0].slice(1);
  /* Topic-list catalogs open with a two-word fragment ("Partial derivatives." "Food marketing.").
     Alone it says little, so the next description sentences ride along, Cal Poly's own full stops
     kept between them, until the line has something to say; the 96-character cut still applies. */
  for(var k=1;k<keep.length&&s.replace(/[.\s]+$/,'').length<32;k++)s=s.replace(/\s+$/,'')+' '+keep[k];
  /* Belt and braces: if a requirement clause still rode in on a merged sentence, stop before it. */
  var rq=s.search(/[.;]\s+(pre|co)-?requisites?\b|[.;]\s+recommended\b|[.;]\s+concurrent\b/i);
  if(rq>0)s=s.slice(0,rq);
  s=s.replace(/[.\s]+$/,'');
  if(s.length>96){
    s=s.slice(0,96); var sp=s.lastIndexOf(' '); if(sp>48)s=s.slice(0,sp);
    /* Never leave a bracket hanging open ("food processing (unit conversion, mass and…"). */
    var op=s.lastIndexOf('('); if(op>s.lastIndexOf(')')&&op>=20)s=s.slice(0,op);
    s=s.replace(/[,;:(\s]+$/,'')+'…';
  }
  return s;
}
function csApply(map,ts){
  COURSE_SHORT=map||null; COURSE_SHORT_AT=ts||null;
  try{ if(typeof renderExplore==='function')renderExplore(); }catch(e){}
}
function csHydrate(){
  try{ var c=JSON.parse(localStorage.getItem('professify_course_short')||'null');
       if(c&&c.map&&typeof c.map==='object'){ csApply(c.map,c.ts); return true; } }catch(e){}
  return false;
}
async function loadCourseShort(){
  csHydrate();
  try{
    var c=window.PROFESSIFY_CONFIG||{}; if(!c.SUPABASE_URL||!c.SUPABASE_ANON_KEY)return;
    var base=c.SUPABASE_URL.replace(/\/$/,''), hdr={apikey:c.SUPABASE_ANON_KEY,Authorization:'Bearer '+c.SUPABASE_ANON_KEY};
    var map={}, n=0, complete=false;
    for(var off=0; off<20000; off+=1000){
      var res=await fetch(base+'/rest/v1/course_catalog?select=course_code,description&description=not.is.null'
        +'&order=course_code.asc&limit=1000&offset='+off,{headers:hdr});
      /* ANY failed page: publish nothing and keep the cache. A partial catalog would strip the
         descriptions off every course past the failure — the same rule loadSeats() keeps. */
      if(!res.ok)return;
      var rows=await res.json(); if(!Array.isArray(rows))return;
      rows.forEach(function(r){ var code=String(r&&r.course_code||'').replace(/\s+/g,' ').trim();
        /* Semester-shaped codes only. The scraper ran on quarter terms before Fall 2026, so the table
           may still hold "BUS 346"-style rows; those name a course that no longer exists. */
        if(!/^[A-Z]{2,5} \d{4}[A-Z]?$/.test(code))return;
        var line=csShortLine(r&&r.description);
        if(line){ map[code]=line; n++; } });
      if(rows.length<1000){ complete=true; break; }
    }
    if(!complete||!n)return;
    var ts=Date.now();
    try{ localStorage.setItem('professify_course_short',JSON.stringify({ts:ts,map:map})); }catch(e){}
    csApply(map,ts);
  }catch(e){}
}
setTimeout(loadCourseShort,1200);

/* ---- The section heading, in the map's three lines ---------------------------------------------
   Eyebrow, title, one line of why. Only the two default lists get the long form, because only they
   have a why that is true: the major's core-then-concentration list, and the major's professors
   ranked by the same shrunk score exTopProfs sorts by. On desktop the eyebrow and the why hide and
   the old label shows, so Sean's desktop Explore does not change. */
function exHeadFor(mode,label){
  var esc=(typeof escapeHtml==='function')?escapeHtml:function(x){return String(x);};
  var major=''; try{ major=(typeof student!=='undefined'&&student&&student.major)||''; }catch(e){}
  var eb='', title=label, sub='';
  if(label==='Recommended for your major'&&major){ eb='Recommended'; title='Classes for '+major; sub='Core and elective classes in your major'; }
  else if(label==='Top-rated professors in your major'&&major){ eb='Strongest reviews'; title='Professors in '+major; sub='Ranked by rating, weighted by number of ratings'; }
  return '<div class="grouphead ex-head ex-head-'+(mode==='professors'?'p':'c')+'">'
    +'<span class="ex-hl">'+esc(label)+'</span>'
    +(eb?'<span class="ex-eb">'+esc(eb)+'</span>':'')
    +'<span class="ex-ht">'+esc(title)+'</span>'
    +(sub?'<span class="ex-hs">'+esc(sub)+'</span>':'')
    +'</div>';
}

/* ---- Saved, as a chip ------------------------------------------------------------------------
   The map's third chip. It is a VIEW, not a mode: the Classes | Professors switch still says what
   you are looking at, and Saved narrows it to what you kept. Classes you saved are watchClasses;
   professors are the watchlist. setExMode clears it, so switching sides starts from your major. */
window.exSaved=false;
window.exSetSaved=function(on){ window.exSaved=!!on;
  if(on&&exMode==='ge')exMode='classes';
  try{ renderExContext(); }catch(e){} try{ renderExplore(); }catch(e){} };
function exSavedHtml(){
  /* Classes only: Saved professors are drawn by renderExplore's own professor list (patch 2g). */
  var codes=(typeof watchClasses!=='undefined'&&watchClasses)?watchClasses.slice():[];
  if(!codes.length)return exHeadFor('classes','Saved classes')
    +'<p class="ex-saved-empty">Nothing saved yet. Tap the bookmark on a class to keep it here.</p>';
  var rows=codes.map(function(code){ var ci=(typeof classInfo==='function')?classInfo(code):null;
    var nm=(ci&&ci.name)||((typeof fp_name==='function')?fp_name(code):'')||'';
    return clsRow({code:code,name:nm,prof:'__tbd',units:(ci&&ci.units!=null)?ci.units:null,type:null},{desc:true}); }).join('');
  return exHeadFor('classes','Saved classes')+'<div class="cls-list">'+rows+'</div>';
}

/* Phone placeholders (the map's): short enough to be read whole in a 220px field. */
function exPlaceholder(m){ return m==='professors'?'Search professors':(m==='ge'?'Search GEs':'Search classes'); }
(function(){ try{ if(window.innerWidth<=640){ var q=document.getElementById('exQuery');
  if(q)q.placeholder=exPlaceholder(typeof exMode!=='undefined'?exMode:'classes'); } }catch(e){} })();
</script>
