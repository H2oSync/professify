/* ---- Reader v2 (2026-10-08): the report's OWN verdicts, requirement by requirement ---------------------
   Cal Poly's Degree Progress Report (PeopleSoft advisement, "Oracle Analytics Publisher") prints, above its
   Course History table, every requirement with the registrar's verdict. Read on a real report (2026-10-08),
   as pdf.js gives it, one line each:
       GE AREA A                                                  ← a short heading (ignored: the verdict line has the words)
       Satisfied: GE AREA A: ENGLISH LANGUAGE … - 12 Units Required (R-0070)
       A1
       Satisfied: A1: ORAL COMMUNICATION COURSE (Note: …) - 4 Units Required (R70-10)
       · Units: 4.00 required, 4.00 used                         ("…, 22.00 needed" when open; sometimes only "8.00 used")
       · Courses: 2.00 required, 1.00 used, 1.00 needed
       Courses Used / Term Subject Catalog Nbr … / 2024 Wtr COMS 101 Public Speaking <grade> 4.00 A1   ← NEVER read
       Not Satisfied: BUS 416 (4412), 463 (4414), 464 (4464), or ECON 464 (4460) - 4 Units Required (Option 2 of 2) (R37-20)
   The code at the end says the level: (RG-0006) a group, (R-0070) a requirement, (R70-10) a line inside R-0070; a
   verdict with no code is a line of the requirement above it. A verdict's words can wrap onto the next lines
   (sometimes the code itself: "(R73-" / "45)"). "Overall Requirement Not Satisfied:" is the same verdict.
   COUNTED: every line, and a requirement with no lines; a group never. A requirement met by "1 of N Options"
   counts once, with every option's classes as its options, and its option lines don't count.
   NEVER READ: a "Courses Used" or Course History row (term, course, GRADE, units), a repeat-code note, a
   "directed to this line" note, the name, the EMPLID. Only a verdict line's own words become a label, and a
   label that still looks like it carries an ID or a grade beside a units value is dropped. Options are course
   CODES only, written in a verdict ("BUS 401 (4401)/411 (4411)", "ITP 303 (3303), 326 (3326)" — a bare number
   takes the subject before it), translated through the report's own (NNNN) pair, then the crosswalk.
   THE 2026 CATALOG'S REPORT (semester catalog, read on a real one 2026-10-09) prints the same verdicts another way:
       1A: WRITTEN COMMUNICATION COURSE                         ← the heading IS the requirement's name
       Satisfied: NOTE: Minimum grade of C- required            ← the verdict's words are notes and counts
       3 units
       (R70-10)                                                 ← the code on its own line, no dash for a group
       · Courses: 1.00 required, 1.00 used                        or requirement: (RG6), (R70), (R70-10)
   so there the label is the heading line just above the verdict, its classes come from the heading ("ITP 3390",
   "STAT 1110 or 1210", "4A: Select from ES 1112, GOV 2200, …"), and the verdict runs on until its code. A report
   is read one way or the other as a whole: any code without a dash ("(RG6)", "(R70)") means the 2026 layout. */
var DPR_VERDICT=/^(?:Overall\s+Requirement\s+)?(Not\s+Satisfied|Satisfied|In\s+Progress)\s*:\s*(.*)$/i;
/* (RG-0006) / (RG6) a group · (R70-10) a line · (R-0070) / (R70) a requirement */
var DPR_RCODE=/\((?:(RG)-?\s*(\d+)|R(\d+)-\s*(\d+)|R-?\s*(\d+))\)\**/i;
function dprCode(w){ var m=DPR_RCODE.exec(w); if(!m)return null; return m[1]?{level:'RG',code:'RG-'+m[2]}:m[3]?{level:'LN',code:'R'+m[3]+'-'+m[4]}:{level:'RQ',code:'R-'+m[5]}; }
/* the page furniture repeated at every page break — never a label, never part of one */
var DPR_FURN=/^(Page \d+ of \d+|Name\s*:|EMPLID\s*:|Date Printed\s*:|Degree Progress Report\s*$|For\s)/i;
/* every grade the report can print (the same set dprParse knows), beside a units value: a course row's tail */
var DPR_GRADEUNITS=/(?:^|\s)(?:[A-DF][+-]?|CR|NC|W|WU|IC|I|RP|AU|P|NP|IP|RD|NG)\s+\d+\.\d{2}\b/;
var DPR_UNITLINE=/^\s*[·•]?\s*(Units|Courses)\s*:\s*(.*)$/i;
var DPR_SKIP=/^(Page \d+ of \d+|Name\s*:|EMPLID\s*:|Date Printed\s*:|For\s|Degree Progress Report|\**DEGREE PROGRESS REPORT|Current Academic Objective|Degree Audit Icons|Requirement Satisfied|Requirement Not Satisfied|In Progress\s+Planned|Planned\b|Exception Made|Courses Used|Course History|Term\s+Subject|Designation|Status\s*$|Repeat Code|.*has been directed to this line|\(?\s*\d{5,}\s*\)?\s*$|<mark>|NOTE\s*:)/i;
var DPR_ROWISH=/^\d{4}\s+(Fall|Wtr|Win|Winter|Spr|Spring|Sum|Summer)\b/;
var DPR_TERMOF={Fall:'Fall',Wtr:'Winter',Win:'Winter',Winter:'Winter',Spr:'Spring',Spring:'Spring',Sum:'Summer',Summer:'Summer'};
function dprNum(s){ var v=parseFloat(s); return isFinite(v)?v:null; }
function dprCounts3(s){
  var o={req:null,used:null,need:null},m;
  if((m=/(\d+(?:\.\d+)?)\s*required/i.exec(s)))o.req=dprNum(m[1]);
  if((m=/(\d+(?:\.\d+)?)\s*used/i.exec(s)))o.used=dprNum(m[1]);
  if((m=/(\d+(?:\.\d+)?)\s*needed/i.exec(s)))o.need=dprNum(m[1]);
  if(o.need==null&&o.req!=null&&o.used!=null)o.need=Math.max(0,o.req-o.used);
  return o;
}
/* course codes in a verdict's words: "SUBJ NNN (NNNN)", and a bare "NNN (NNNN)" after "," "/" "or" "and" takes the subject before it */
var DPR_NOTSUBJ={GE:1,UD:1,LD:1,OPT:1,AND:1,THE:1,FOR:1,MAJ:1,SPEC:1,AREA:1,UNITS:1,CAL:1,BS:1,BA:1,UG:1,OR:1,OF:1,IN:1,TO:1,ALL:1,ONE:1,TWO:1,NOTE:1,UNIT:1,ELECT:1};
function dprCodesIn(s, cross){
  var out=[], subj='', m, re=/(?:\b([A-Z]{2,5})\s+|(?:,|\/|\bor\b|\band\b)\s*)(\d{3,4}[A-Z]?)\b(?:\s*\((\d{4}[A-Z]?)\))?/g;
  var t=String(s||'').replace(DPR_RCODE,' ').replace(/\b(19|20)\d\d-(19|20)\d\d\b/g,' ');
  while((m=re.exec(t))){
    if(m[1]){ if(DPR_NOTSUBJ[m[1]])continue; subj=m[1]; }
    else if(!subj) continue;
    var old=subj+' '+m[2], now=m[3]?(subj+' '+m[3]):((cross&&cross[old])||null);
    var canon=null; try{ canon=(typeof canonCode==='function')?canonCode(now||old):null; }catch(e){}
    var c=canon||now||old;
    if(out.indexOf(c)<0)out.push(c);
  }
  return out;
}
function dprTidyLabel(s){
  var t=String(s||'').replace(DPR_RCODE,'').replace(/\*+/g,'').replace(/\((?:W|\d{4}-Current Catalog)\)/gi,'').replace(/^\s*\(R\d+\)\s*/,'').replace(/\s+/g,' ').trim();
  /* the report's old number with its new one in brackets reads as today's number */
  t=t.replace(/\b([A-Z]{2,5})\s+\d{3}\s*\((\d{4}[A-Z]?)\)/g,'$1 $2').replace(/([,\/]\s*|\bor\s+)\d{3}\s*\((\d{4}[A-Z]?)\)/g,'$1$2');
  /* the words before " - N Units Required" (or "- Select …") are the requirement; the count is printed again below */
  var cut=t.search(/\s+-\s+(?:\d+(?:\.\d+)?(?:\s*to\s*\d+)?\s*(?:\(\*?\d+\))?\s*(?:Minimum\s+)?(?:Units?|Courses?)\b|Satisfactory Completion|\d+(?:\.\d+)?\s+(?:Minimum\s+)?Required|Select\b)|:\s+Select\b/i);
  if(cut>=3)t=t.slice(0,cut);
  t=t.replace(/\s*\((?:Note|Because|Relevant|'Taken'|`Taken'|Excess|Minimum|See|Option\s+\d)[^)]*\)?/gi,'').replace(/\s*[:.-]\s*$/,'').trim();
  var up=(t.match(/[A-Z]/g)||[]).length, low=(t.match(/[a-z]/g)||[]).length;
  if(up>3&&low<up/4){
    /* SHOUTED → Title case, keeping course codes, area codes and a few initialisms */
    t=t.split(' ').map(function(w,i,a){
      if(/^[A-Z]{2,5}$/.test(w)&&/^\d{3,4}/.test(a[i+1]||''))return w;             // a subject before its number
      if(/^([A-F][1-5]?|[1-6][A-F]?|[1-6]?[A-F]?UD|GE|UD|LD|GWR|GPA|USCP|ITP|II|III|IV|U\.S\.|B\.S\.|B\.A\.)$/.test(w.replace(/^[("]+|[)":,]+$/g,'')))return w;
      if(/\d/.test(w))return w;
      var l=w.toLowerCase(); if(i>0&&/^(of|and|or|the|for|in|to|a|an|from|through|with)$/.test(l))return l;
      return l.replace(/^([("'`]?)([a-z])/,function(_,p,c){return p+c.toUpperCase();});
    }).join(' ');
  }
  /* an ID, a name line or a grade next to a units value never becomes a label */
  if(/\d{7,}|EMPLID|Name\s*:/i.test(t)||DPR_GRADEUNITS.test(t)) return '';
  return t.slice(0,140);
}
/* `taking`: the classes the student is in now (dprParse's ungraded rows after the last graded term) — a
   "Not Satisfied" line whose own "Courses Used" table lists one of them is in progress, not left (the
   registrar's note on the writing requirement: "allow a week after grades are finalized"). Only a row's
   SUBJECT and NUMBER are looked at for this; never its grade. */
function dprAudit(text, cross, taking){
  var lines=String(text||'').split('\n'), end=lines.length;
  for(var i=lines.length-1;i>=0;i--){ if(/^Course History\s*$/i.test(String(lines[i]||'').trim())){ end=i; break; } }
  var blocks=[], cur=null, group=null, req=null, lastEnd=-1;
  /* `taking` entries are "SUBJ NNNN|Term Year": a row counts only in the term it's being taken (a graded
     earlier attempt of the same class is not "taking") */
  var now={}; (taking||[]).forEach(function(c){ now[c]=1; });
  var isNow=function(c,term){ var k=null; try{ k=(typeof canonCode==='function')?canonCode(c):null; }catch(e){} return !!(now[c+'|'+term]||(k&&now[k+'|'+term])); };
  /* the student's name as the report prints it — "Name: …" in the page header, and "For …" on the line after the
     report's title (2–4 words, letters only): any label with it, or a word of it, is dropped — kept in memory
     only while reading */
  var who=[], addWho=function(n){ n=String(n||'').trim(); if(!n)return; who.push(n); n.split(/[\s,]+/).forEach(function(w){ if(/^[\p{L}'.-]{3,}$/u.test(w))who.push(w); }); };
  for(var wi=0, lastTitle=-9; wi<end; wi++){
    var wl=String(lines[wi]||'').trim(); if(!wl)continue;
    var nm=/^Name\s*:\s*(.+?)(?:\s+EMPLID\b.*)?$/i.exec(wl); if(nm){ addWho(nm[1]); continue; }
    if(/^Degree Progress Report\s*$/i.test(wl)){ lastTitle=wi; continue; }
    var fm=/^For\s+((?:[\p{L}'.-]+\s+){1,3}[\p{L}'.-]+)$/u.exec(wl); if(fm&&wi-lastTitle<=2)addWho(fm[1]);
  }
  who=who.filter(function(w,i){ return w&&who.indexOf(w)===i&&!/^(the|and|for|degree|progress|report)$/i.test(w); });
  var hasWho=function(t){ t=String(t||''); return who.some(function(w){ return new RegExp('(^|[^\\p{L}])'+w.replace(/[.*+?^${}()|[\]\\]/g,'\\$&')+'($|[^\\p{L}])','iu').test(t); }); };
  /* the 2026 catalog's layout: a group or requirement code with no dash anywhere */
  var NEW=/\((?:RG\d+|R\d+)\)/i.test(lines.slice(0,end).join('\n'));
  /* (2026 layout) the heading just above a verdict — past page furniture and notes, never back past the
     previous block, a course table or a code line */
  var headingBefore=function(k){
    for(var i=k-1,n=0;i>lastEnd&&n<10;i--,n++){
      var s=String(lines[i]||'').trim();
      if(!s||DPR_FURN.test(s)||/^NOTE\s*:/i.test(s))continue;
      if(DPR_VERDICT.test(s)||DPR_UNITLINE.test(s)||DPR_ROWISH.test(s)||/^\(R/i.test(s)||DPR_SKIP.test(s)||DPR_GRADEUNITS.test(s)||hasWho(s))return '';
      return s;
    }
    return '';
  };
  for(var k=0;k<end;k++){
    var ln=String(lines[k]||'').trim();
    if(!ln)continue;
    var v=DPR_VERDICT.exec(ln);
    if(v&&!/^In\s+Progress\s+Planned/i.test(ln)){
      var k0=k, head=NEW?headingBefore(k):'';
      /* the verdict's words, with any wrapped continuation, up to its code (2026 layout: the code always
         closes the block — "3 units required" doesn't) */
      var words=v[2], j=k, extra=0;
      var done=NEW?function(w){ return DPR_RCODE.test(w); }:function(w){ return DPR_RCODE.test(w)||/(Required\)?\.?|\*{3})\s*$/i.test(w); };
      while(!done(words)&&j+1<end&&extra<(NEW?6:3)){
        var nx=String(lines[j+1]||'').trim();
        if(NEW&&(!nx||DPR_FURN.test(nx))){ j++; continue; }
        if(NEW&&DPR_SKIP.test(nx)&&!/^NOTE\s*:/i.test(nx))break;
        if(!nx||DPR_VERDICT.test(nx)||DPR_UNITLINE.test(nx)||DPR_ROWISH.test(nx))break;
        if(NEW?/^(Courses Used|Course History|Term\s+Subject)\b/i.test(nx):(DPR_SKIP.test(nx)||/\b\d+\.\d{2}\b/.test(nx)))break;
        words+=' '+nx; j++; extra++;
      }
      if(NEW&&!done(words)){ words=v[2]; j=k; }   /* no code within reach: the next lines aren't this verdict's */
      /* (older layout) the words can end on "… Required" with the code a line or two further on, after a
         sentence of advice: "If enrolled in a GWR eligible course, … in this" / "section. (R11-10)" */
      if(!NEW&&!DPR_RCODE.test(words)){
        for(var pk=j+1;pk<=j+2&&pk<end;pk++){
          var pl=String(lines[pk]||'').trim();
          if(!pl||DPR_VERDICT.test(pl)||DPR_UNITLINE.test(pl)||DPR_ROWISH.test(pl)||DPR_SKIP.test(pl))break;
          if(DPR_RCODE.test(pl)){ for(var q=j+1;q<=pk;q++)words+=' '+String(lines[q]||'').trim(); j=pk; break; }
        }
      }
      k=j; lastEnd=j;
      var w=v[1].toLowerCase().replace(/\s+/g,' '), cd=dprCode(words);
      var level=cd?cd.level:'LN';
      var src=head||words;
      var b={ label:dprTidyLabel(src), status:w==='not satisfied'?'not':w==='in progress'?'in_progress':'satisfied', level:level,
              code:cd?cd.code:null, units:null, courses:null, options:dprCodesIn(head?head:words,cross),
              ge:null, kind:'major', option:/\(Option\s+\d+\s+of\s+\d+\)/i.test(src+' '+words), oneOf:/\bin\s+1\s+of\s+\d+\s+Options\b/i.test(src+' '+words) };
      if(hasWho(b.label)||hasWho(src))b.label='';
      if(!b.label){ b.status='unknown'; b.label='A requirement the app couldn’t read'; }
      if(level==='RG'){ group=b; req=null; }
      else if(level==='RQ'){ req=b; }
      b.parent=level==='LN'?req:null;
      /* the requirement above lends its words to a line's kind only when the line is its own: R11-10 under
         R-0011 / R11 — a line whose number differs (a new section the reader saw no heading code for) doesn't */
      var own=!(cd&&cd.level==='LN'&&req&&req.code)||(+String(req.code).replace(/^R-?/,''))===(+String(cd.code).replace(/^R(\d+)-.*$/,'$1'));
      var gl=((group&&group.label)||'')+' '+b.label, ctx=own?((req&&req.label)||''):'';
      var gm=/(?:^|\bGE\s+(?:AREA\s+)?)([A-F](?:[1-5]|\s?UD)?|[1-6][A-F]?)\s*(?:\((?:Qtr|Sem)\)\s*)?:/i.exec(b.label) || /\bGE\s+(?:AREA\s+)?([A-F][1-5]?|[1-6][A-F]?)\b/i.exec(b.label);
      var courseLine=/^[A-Z]{2,5} \d{3,4}/.test(b.label);
      if(/general education/i.test(courseLine?((group&&group.label)||''):gl)||(!courseLine&&/\bGE\b/.test(b.label))||/^GE\b/i.test(ctx)){ b.kind='ge'; if(gm)b.ge=gm[1].toUpperCase().replace(/\s+/g,''); }
      else if(/concentration/i.test(gl)) b.kind='conc';
      else if(/upper[- ]division units|units for the degree|units in residence|residence units|total units/i.test(b.label+' '+ctx)||(/\bunits\b/i.test(b.label)&&!/^[A-Z]{2,5} \d{3,4}/.test(b.label))) b.kind='units';
      else if(/writing requirement|\bGWR\b/i.test(b.label+' '+ctx)) b.kind='gwr';
      else if(/cultural pluralism|\bUSCP\b/i.test(b.label+' '+ctx)) b.kind='uscp';
      else if(/\bGPA\b/i.test(b.label+' '+ctx)) b.kind='gpa';
      else if(/elective/i.test(b.label)) b.kind='elective';
      blocks.push(b); cur=b; continue;
    }
    if(cur){
      var u=DPR_UNITLINE.exec(ln);
      if(u){ var c3=dprCounts3(u[2]); if(/^units/i.test(u[1]))cur.units=c3; else cur.courses=c3; lastEnd=k; continue; }
      /* a row of the line's "Courses Used" table: only whether it's a class you're taking now — and for that
         row, which has no grade yet, its units (the first "N.NN" after the class) */
      var rw=/^\d{4}\s+(?:Fall|Wtr|Spr|Sum)\s+([A-Z]{2,5})\s+(\d{3,4}[A-Z]?)\b/.exec(ln);
      if(rw){ var rt=/^(\d{4})\s+(\w+)/.exec(ln); if(rt&&isNow(rw[1]+' '+rw[2], (DPR_TERMOF[rt[2]]||rt[2])+' '+rt[1])&&(cur.nowc=cur.nowc||[]).indexOf(rw[1]+' '+rw[2])<0){ (cur.nowc=cur.nowc||[]).push(rw[1]+' '+rw[2]); var um=/\b(\d+\.\d{2})\b/.exec(ln.slice(rw[0].length)); (cur.now=cur.now||[]).push(um?+um[1]:null); } continue; }
    }
    /* anything else — a heading, a Courses Used row, a note — is not read */
  }
  /* what counts: lines, and requirements with no lines; "1 of N Options" counts once with all its options */
  blocks.forEach(function(b){ b.atomic=false; });
  blocks.forEach(function(b,i){
    if(b.level==='RG')return;
    if(b.level==='RQ'){
      var kids=blocks.filter(function(x){ return x.parent===b; });
      if(!kids.length){ b.atomic=true; return; }
      /* the requirement says Not Satisfied but none of its lines does (a minimum across them, say): it counts,
         as itself — never dropped, or the Planner could say everything's filled */
      if(b.status==='not'&&!b.oneOf&&!kids.some(function(x){ return x.status!=='satisfied'; })){ b.atomic=true; kids.forEach(function(x){ x.inOption=true; }); return; }
      var opt=kids.filter(function(x){ return x.option; });
      if(b.oneOf||(opt.length&&opt.length===kids.length)){
        b.atomic=true; kids.forEach(function(x){ x.inOption=true; x.options.forEach(function(c){ if(b.options.indexOf(c)<0)b.options.push(c); }); });
        if(b.status!=='satisfied'&&kids.some(function(x){ return x.status==='satisfied'; }))b.status='satisfied';
        return;
      }
      /* (2026 layout) "MATH 1261 (Option 1 of 2)" / "MATH 1221 (Option 2 of 2)" among a requirement's other lines:
         the options count once, as one pick-1 line; the other lines count as themselves */
      if(opt.length){
        var rep=opt[0]; opt.forEach(function(x){ if(x!==rep)x.inOption=true; x.options.forEach(function(c){ if(rep.options.indexOf(c)<0)rep.options.push(c); }); });
        rep.oneOf=true; rep.label=rep.options.length>1?rep.options.join(' or '):rep.label;
        rep.status=opt.some(function(x){ return x.status==='satisfied'; })?'satisfied':opt.some(function(x){ return x.status==='in_progress'; })?'in_progress':rep.status;
      }
      return;
    }
    if(b.level==='LN'&&!b.inOption) b.atomic=true;
  });
  /* units for the degree, from the report (never computed) */
  var tot=blocks.filter(function(b){ return b.kind==='units'&&/total units/i.test(b.label)&&b.units&&b.units.req!=null; })[0];
  /* in progress: a Not Satisfied line (or an option of one) whose table lists classes you're taking now that
     cover what it still needs — enough classes for "· Courses: … needed", enough units for "· Units: … needed" */
  var inNow=function(b){ var n=b.now||[]; if(!n.length)return false;
    /* a line that prints no counts: only one that a single class settles (the writing requirement, USCP,
       a one-class line) — "Not Satisfied: 8 units" with no counts printed could need two */
    if(!b.courses&&!b.units&&!(b.kind==='gwr'||b.kind==='uscp'||b.options.length===1))return false;
    if(b.courses&&b.courses.need!=null&&n.length<b.courses.need)return false;
    if(b.units&&b.units.need!=null&&b.units.need>0){ var u=0; for(var i=0;i<n.length;i++){ if(n[i]==null)return false; u+=n[i]; } if(u<b.units.need)return false; }
    return true; };
  blocks.forEach(function(b){ if(b.status==='not'&&inNow(b))b.status='in_progress'; });
  blocks.forEach(function(b){ if(b.atomic&&b.level==='RQ'&&b.status==='not'&&blocks.some(function(x){ return x.parent===b&&x.inOption&&x.status==='in_progress'; }))b.status='in_progress'; });
  var reqs=blocks.filter(function(b){ return b.atomic; }).map(function(b){
    return { label:b.label, status:b.status, kind:b.kind, ge:b.ge, level:b.level, code:b.code, units:b.units, courses:b.courses, options:b.options.slice(0,60),
             group:b.parent?b.parent.label:null, oneOf:!!b.oneOf };
  });
  var n={satisfied:0,not:0,in_progress:0,unknown:0};
  reqs.forEach(function(b){ n[b.status]=(n[b.status]||0)+1; });
  return { ok:reqs.length>0, reqs:reqs, counts:n, blocks:blocks.length,
           units_used:tot&&tot.units?tot.units.used:null, units_needed:tot&&tot.units?tot.units.need:null, units_required:tot&&tot.units?tot.units.req:null };
}
