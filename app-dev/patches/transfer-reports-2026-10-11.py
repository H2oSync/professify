#!/usr/bin/env python3
r"""Transfer students' Degree Progress Reports, read right (Tate, 2026-10-11, on a friend's real report: a
junior transfer whom the app said had "only 7 of his requirements fulfilled").

What the real report showed (read 2026-10-11; the report itself is never in the repo):
  1. Every community-college and AP class prints as "2026 Fall" — the term the registrar POSTED them in, his
     first at Cal Poly — WITH a grade, beside the four classes he's actually taking (no grade). Only the row's
     icon (the legend's "Transfer/Test/Other Credit" arrow) says it's transfer credit; the text doesn't.
  2. Transfer and exam credit can print "300" / "400" where a grade goes. The reader took that for a word of the
     title, so the row looked ungraded — and four of his transfer classes (English, Calculus, Statistics,
     Chemistry) were filed as classes he's taking THIS term (My Classes), with "300" shown in the class's name.
     (Another real report has exam credit printed "CR" with no icon at all — read now as credit too.)
  3. Because transfer rows were graded "this term", the reader's "classes being taken" (ungraded rows after
     the last graded term) came out empty, so the report's in-progress lines couldn't be seen.
  4. The 2026 catalog's "Not Satisfied: Choose one" with "Option 1 of 2" / "Option 2 of 2" lines (no brackets)
     counted every option as its own requirement (25 left instead of 23).
  5. Past classes and the profile said "N of M filled" from the FLOWCHART — which can't see transfer credit
     ("ENGL 1T13", "MU 1T3A") — while the report says 24 of 47. That was the "7".

What this changes:
  READER (app/planner.js, the lifted dprParse and its helpers — the phone's copy already carries reader v2)
    · pdfItemsToText(items, marks): a class row the app saw wearing the transfer icon ends in DPR_XMARK; one
      wearing no icon at all (on a page whose icons were all read) ends in DPR_BMARK.
    · "300"/"400" where a grade goes is a grade (transfer/exam credit prints that way), never a title word.
    · transfer = the icon; no icon with a credit grade (CR, 333, N00); "N00" (unless the row wears Cal Poly's own
      icon); "333"; TRAN/AP/DUD/PORT; a catalog number that isn't Cal Poly's shape (1TR, 1T13, 4A1, 4AA — Cal Poly's
      are NNN or NNNN with at most two letters after); or a credit GRADE (not W/IC/RP) on a class with no Cal Poly
      icon, in a term that hadn't reached its finals when the report was printed ("Date Printed").
    · posted credit with no grade isn't "being taken" (never My Classes).
    · "the classes being taken" look past transfer credit (posted credit isn't a finished term).
    · (2026 layout) "Choose one" + "Option N of M" lines count once, as one pick-1; "(2026)" off a label;
      a cross-listed subject keeps its capitals ("NR/AGB 3326", was "Nr/agb 3326").
  READING THE PDF (app/index.html): dprDocText() reads every page's text, then (within 6 s) the pictures of page 1
    and the Course History pages: page 1's legend says which picture is "Transfer/Test/Other Credit" (matched by
    pixels: pdf.js renames pictures per page), and every class row drawn with it — or with Cal Poly's own icon, or
    none — is marked. A failure or the time cap leaves the text as it was.
  COUNTS (app/index.html): once a report is in, Past classes' "N of M filled" and the profile's
    "N of M requirements filled" are the report's (auditLines — the Planner's own count). The flowchart below
    shows a spot the ledger can't fill, but the report says is Satisfied (a GE area by its area, a class by
    its code), as filled, "On your report".

Usage: python3 transfer-reports-2026-10-11.py <repo-dir>      Replayable: every anchor must match once."""
import sys, os
D = sys.argv[1]
PI = os.path.join(D, 'app', 'index.html'); PP = os.path.join(D, 'app', 'planner.js')
S = {'A': open(PI, encoding='utf-8').read(), 'P': open(PP, encoding='utf-8').read()}

def rep(which, a, b, label):
    n = S[which].count(a)
    if n != 1: sys.exit(f'{label}: anchor matched {n}x')
    S[which] = S[which].replace(a, b)

# ================================================================================================
# planner.js — the reader
# ================================================================================================
rep('P', """function pdfItemsToText(items){
  var lines=[],cur=null;
  (items||[]).forEach(function(it){
    var s=(it&&typeof it.str==='string')?it.str:'';
    var tr=(it&&it.transform)||null;
    var x=tr?(+tr[4]||0):0, y=tr?(+tr[5]||0):0, w=+((it&&it.width)||0);
    if(!cur||Math.abs(y-cur.y)>3.2){ cur={y:y,end:x,text:''}; lines.push(cur); }
    if(cur.text&&s&&(x-cur.end)>1.6&&!/\\s$/.test(cur.text)&&!/^\\s/.test(s))cur.text+=' ';
    cur.text+=s; cur.end=x+w;
    if(it&&it.hasEOL)cur=null;
  });
  return lines""", """function pdfItemsToText(items, marks){
  var lines=[],cur=null;
  (items||[]).forEach(function(it){
    var s=(it&&typeof it.str==='string')?it.str:'';
    var tr=(it&&it.transform)||null;
    var x=tr?(+tr[4]||0):0, y=tr?(+tr[5]||0):0, w=+((it&&it.width)||0);
    if(!cur||Math.abs(y-cur.y)>3.2){ cur={y:y,end:x,text:''}; lines.push(cur); }
    if(cur.text&&s&&(x-cur.end)>1.6&&!/\\s$/.test(cur.text)&&!/^\\s/.test(s))cur.text+=' ';
    cur.text+=s; cur.end=x+w;
    if(it&&it.hasEOL)cur=null;
  });
  /* (2026-10-11) the report's own icons, found by the app (dprDocText): `marks` are the pictures' centres, `t` when
     it's the one the legend calls "Transfer/Test/Other Credit", `c` when it's one the legend calls Cal Poly's ("Cal Poly
     Graded Course", "Course In Progress", "Planned"). A class row ("2026 Fall …") whose baseline sits just under one
     (measured on real reports: centre = baseline + 1.8; rows are 11.4 apart) wears it:
       the transfer icon            → the row ends in DPR_XMARK;
       one of Cal Poly's            → DPR_CMARK: a Cal Poly class, whatever its words say;
       a picture the legend doesn't → nothing (the words decide, as with no pictures at all);
       name
       none — on a page whose       → DPR_BMARK: exam credit prints that way ("CR" and no icon, read on a real report).
       pictures were all read         Only on a page where some row wore a Cal Poly icon, and never with a picture
       (marks.bare)                   within 7pt (one that sits a little off its row is still that row's).        */
  if(marks){
    var rowRe=/^\\s*\\d{4}\\s+(Fall|Wtr|Win|Winter|Spr|Spring|Sum|Summer)\\b/, hit=[], cp=false, RANK={T:3,C:2,O:1};
    marks.forEach(function(mk){
      var best=-1,bd=4;
      lines.forEach(function(l,i){ var d=Math.abs(+mk.y-(l.y+1.8)); if(d<bd&&rowRe.test(l.text)){ bd=d; best=i; } });
      if(best<0)return;
      var k=mk.t?'T':mk.c?'C':'O'; if(k==='C')cp=true;
      if(!hit[best]||RANK[k]>RANK[hit[best]])hit[best]=k;
    });
    var near=function(l){ return marks.some(function(mk){ return Math.abs(+mk.y-(l.y+1.8))<7; }); };
    lines.forEach(function(l,i){ if(!rowRe.test(l.text))return;
      if(hit[i]==='T')l.text+=' '+DPR_XMARK; else if(hit[i]==='C')l.text+=' '+DPR_CMARK; else if(!hit[i]&&marks.bare&&cp&&!near(l))l.text+=' '+DPR_BMARK; });
  }
  return lines""", 'pl-items-marks')

rep('P', "var DPR_GRADE=/^(?:[A-D][+-]?|F|CR|NC|W|IC|RP|333)$/;",
    """var DPR_GRADE=/^(?:[A-D][+-]?|F|CR|NC|W|IC|RP|333|[1-7]00)$/;
/* (2026-10-11) transfer and exam credit can print a number where a grade goes ("300", "400", read on real reports):
   it's credit earned — never a word of the title, never a class still being taken (unless the row wears Cal Poly's own
   icon: there "… 400" is the end of a title) */
var DPR_TEST=/^[1-7]00$/;
/* the grades exam and transfer credit print: what a row with NO icon must show to be called credit */
var DPR_CREDIT=/^(?:CR|333|[1-7]00)$/;
/* what the app puts on the end of a class row (never in a real report's text): the transfer icon, no icon (on a page
   whose icons were all read), Cal Poly's own icon */
var DPR_XMARK='\\uE000', DPR_BMARK='\\uE001', DPR_CMARK='\\uE002';
/* when the report was printed: "Date Printed: October 10, 2026 18:05" (the date only) — the LAST one: a report prints
   its date on every page, and when several files are read together (the website takes up to four) the Course History
   read is the last file's (review 2026-10-11) */
function dprPrinted(text){
  var re=/Date Printed\\s*:\\s*([A-Za-z]+)\\.?\\s+(\\d{1,2}),?\\s+(\\d{4})/g, t=String(text||''), m=null, x;
  while((x=re.exec(t)))m=x;
  if(!m)return null;
  var mo=['jan','feb','mar','apr','may','jun','jul','aug','sep','oct','nov','dec'].indexOf(m[1].slice(0,3).toLowerCase());
  return mo<0?null:new Date(+m[3],mo,+m[2]);
}
/* A term still short of its last weeks on that date: no Cal Poly grade can exist in it yet, so a grade on one of its
   classes is credit the registrar posted (transfer, AP/IB, exam) — the day is before any of its finals (Fall: Dec 1,
   Spring: May 1, Winter: Mar 1, Summer: Jun 1, before its first session ends), so a real grade is never taken for posted
   credit. A withdrawal or incomplete (W, IC, RP) can post mid-term, so it never counts. */
function dprTermRunning(term, year, d){
  if(!d)return false;
  var end={Fall:[11,1],Winter:[2,1],Spring:[4,1],Summer:[5,1]}[term];
  return !!end&&d<new Date(+year,end[0],end[1]);
}""", 'pl-grade-test')

rep('P', """    var ln=String(lines[k]||'').trim();
    if(!ln||DPR_NOISE.test(ln))continue;
    var m=DPR_ROW.exec(ln);""", """    var ln=String(lines[k]||'').trim();
    var xmark=ln.indexOf(DPR_XMARK)>=0, bmark=ln.indexOf(DPR_BMARK)>=0, cmark=ln.indexOf(DPR_CMARK)>=0;
    if(xmark||bmark||cmark)ln=ln.split(DPR_XMARK).join('').split(DPR_BMARK).join('').split(DPR_CMARK).join('').trim();
    if(!ln||DPR_NOISE.test(ln))continue;
    var m=DPR_ROW.exec(ln);""", 'pl-row-mark')

rep('P', "    if(gradeTok&&!DPR_GRADE.test(gradeTok)){ title=(title+' '+gradeTok).trim(); gradeTok=''; }",
    "    if(gradeTok&&(!DPR_GRADE.test(gradeTok)||(cmark&&DPR_TEST.test(gradeTok)))){ title=(title+' '+gradeTok).trim(); gradeTok=''; }", 'pl-title-word')

rep('P', "    var xfer=(gradeTok==='333')||/^(TRAN|AP|DUD|PORT)$/.test(subj)||/(TC|TR)\\d*$/.test(nbr);",
    """    var xfer=xmark||(bmark&&DPR_CREDIT.test(gradeTok))||DPR_TEST.test(gradeTok)||(gradeTok==='333')||/^(TRAN|AP|DUD|PORT)$/.test(subj)||/(TC|TR)\\d*$/.test(nbr)
      /* (2026-10-11) a catalog number that isn't Cal Poly's shape is an articulation placeholder: 1TR, 1T13, 4A1, 4AA */
      ||!/^\\d{3,4}[A-Z]{0,2}$/.test(nbr);
    /* for the date rule below: a credit grade (not a mid-term W / IC / RP), and Cal Poly's own icon — facts, never the grade */
    var postable=!!gradeTok&&!/^(?:W|IC|RP)$/.test(gradeTok);""", 'pl-xfer')

rep('P', "      _dpr:true, _open:stillOpen, _xfer:xfer, _units:units,",
    "      _dpr:true, _open:stillOpen, _xfer:xfer, _units:units, _post:postable, _cp:cmark,", 'pl-row-facts')

rep('P', """  var lastGraded=0; out.forEach(function(r){ if(!r._open){ var v=r.year*10+(ORD[r.term]||0); if(v>lastGraded)lastGraded=v; } });""",
    """  /* (2026-10-11) a grade on a class in a term that was still running when the report was printed is posted credit:
     a transfer's community-college and AP classes all print in their first Cal Poly term, graded */
  var printed=dprPrinted(text);
  out.forEach(function(r){ if(r._post&&!r._xfer&&!r._cp&&dprTermRunning(r.term,r.year,printed))r._xfer=true; });
  /* posted credit with no grade (a study-abroad placeholder, "AP 300") is not a class being taken */
  out.forEach(function(r){ if(r._xfer)r._now=false; });
  /* …and posted credit says nothing about which terms are over: it's left out of "the last graded term" */
  var lastGraded=0; out.forEach(function(r){ if(!r._open&&!r._xfer){ var v=r.year*10+(ORD[r.term]||0); if(v>lastGraded)lastGraded=v; } });""", 'pl-last-graded')

rep('P', "  var taking=[]; out.forEach(function(r){ if(r._open&&(r.year*10+(ORD[r.term]||0))>lastGraded){",
    "  var taking=[]; out.forEach(function(r){ if(r._open&&!r._xfer&&(r.year*10+(ORD[r.term]||0))>lastGraded){", 'pl-taking')

rep('P', """option:/\\(Option\\s+\\d+\\s+of\\s+\\d+\\)/i.test(src+' '+words), oneOf:/\\bin\\s+1\\s+of\\s+\\d+\\s+Options\\b/i.test(src+' '+words) };""",
    """option:/\\(Option\\s+\\d+\\s+of\\s+\\d+\\)/i.test(src+' '+words)||(NEW&&/^\\s*Option\\s+\\d+\\s+of\\s+\\d+\\b/i.test(v[2])),
              /* (2026 layout, 2026-10-11) "Not Satisfied: Choose one" over "Option 1 of 2" / "Option 2 of 2" lines */
              oneOf:/\\bin\\s+1\\s+of\\s+\\d+\\s+Options\\b/i.test(src+' '+words)||(NEW&&/^\\s*Choose\\s+one\\b/i.test(v[2])) };""", 'pl-options-2026')

rep('P', """  t=t.replace(/\\b([A-Z]{2,5})\\s+\\d{3}\\s*\\((\\d{4}[A-Z]?)\\)/g,'$1 $2').replace(/([,\\/]\\s*|\\bor\\s+)\\d{3}\\s*\\((\\d{4}[A-Z]?)\\)/g,'$1$2');""",
    """  t=t.replace(/\\b([A-Z]{2,5})\\s+\\d{3}\\s*\\((\\d{4}[A-Z]?)\\)/g,'$1 $2').replace(/([,\\/]\\s*|\\bor\\s+)\\d{3}\\s*\\((\\d{4}[A-Z]?)\\)/g,'$1$2');
  /* (2026 layout) the catalog year after a heading's words: "SUPPORT COURSES (2026)" is "Support Courses" */
  t=t.replace(/\\b([A-Za-z]{3,})\\s*\\((?:19|20)\\d\\d\\)(?=\\s*$|\\s*[-:,])/g,'$1');""", 'pl-label-year')

rep('P', "      if(/^[A-Z]{2,5}$/.test(w)&&/^\\d{3,4}/.test(a[i+1]||''))return w;             // a subject before its number",
    "      if(/^[A-Z]{2,5}(?:\\/[A-Z]{2,5})*$/.test(w)&&/^\\d{3,4}/.test(a[i+1]||''))return w;   // a subject before its number (cross-listed: NR/AGB 3326)", 'pl-label-crosslist')

rep('P', "dprLooksLikeOne: dprLooksLikeOne, dprParse: dprParse, dprAudit: dprAudit,",
    "dprLooksLikeOne: dprLooksLikeOne, dprParse: dprParse, dprAudit: dprAudit, dprPrinted: dprPrinted, dprTermRunning: dprTermRunning, dprXMark: DPR_XMARK, dprBMark: DPR_BMARK, dprCMark: DPR_CMARK,", 'pl-export')

# ================================================================================================
# app/index.html — reading the PDF: text and the transfer icon
# ================================================================================================
rep('A', "async function readDpr(file) {",
    """/* (2026-10-11) The report's pictures. Cal Poly's report says which classes are transfer, AP/IB or exam credit
   only with an icon (a green arrow) — never in words, and a transfer's credit prints in a real term with a real
   grade. Page 1's legend names each icon ("Transfer/Test/Other Credit"); pictures are matched by their pixels,
   because pdf.js names the same picture differently on different pages. Only small pictures (icons) are read. */
const dprImgSig = o => { const d = o && o.data; if (!d || !o.width || !o.height || o.width > 64 || o.height > 64) return null; let h = 2166136261; for (let k = 0; k < d.length; k++) { h ^= d[k]; h = Math.imul(h, 16777619) >>> 0; } return o.width + 'x' + o.height + ':' + o.kind + ':' + h.toString(16); };
async function dprIcons(page) {
  const OPS = window.pdfjsLib.OPS, ol = await page.getOperatorList(), out = [], st = [];
  let m = [1, 0, 0, 1, 0, 0], other = false;
  const mul = (a, b) => [a[0] * b[0] + a[2] * b[1], a[1] * b[0] + a[3] * b[1], a[0] * b[2] + a[2] * b[3], a[1] * b[2] + a[3] * b[3], a[0] * b[4] + a[2] * b[5] + a[4], a[1] * b[4] + a[3] * b[5] + a[5]];
  for (let i = 0; i < ol.fnArray.length; i++) {
    const f = ol.fnArray[i], a = ol.argsArray[i];
    if (f === OPS.save) st.push(m); else if (f === OPS.restore) m = st.pop() || m; else if (f === OPS.transform) m = mul(m, a);
    else if (f === OPS.paintFormXObjectBegin) { st.push(m); if (a && a[0] && a[0].length === 6) m = mul(m, a[0]); }
    else if (f === OPS.paintFormXObjectEnd) m = st.pop() || m;
    else if (f === OPS.paintImageXObject && a && Math.abs(m[0]) <= 24 && Math.abs(m[3]) <= 24) out.push({ id: String(a[0]), x: m[4], y: m[5] + m[3] / 2 });
    /* a picture drawn some other way can't be matched: the page's pictures aren't all read */
    else if ([OPS.paintInlineImageXObject, OPS.paintInlineImageXObjectGroup, OPS.paintImageMaskXObject, OPS.paintImageMaskXObjectGroup, OPS.paintImageMaskXObjectRepeat, OPS.paintImageXObjectRepeat, OPS.paintSolidColorImageMask].includes(f)) other = true;
  }
  const sig = {};
  for (const im of out) {
    if (!(im.id in sig)) sig[im.id] = await new Promise(res => { let done = false; const fin = v => { if (!done) { done = true; res(v); } };
      try { (im.id.startsWith('g_') ? page.commonObjs : page.objs).get(im.id, o => fin(dprImgSig(o))); } catch (e) { fin(null); } setTimeout(() => fin(null), 1500); });
    im.sig = sig[im.id];
  }
  const icons = out.filter(i => i.sig); icons.all = !other && icons.length === out.length;
  return icons;
}
/* the picture just left of a legend label, on its line */
function dprLegendSig(items, icons, re) {
  const it = (items || []).find(t => t && typeof t.str === 'string' && re.test(t.str) && t.transform); if (!it) return null;
  const x = +it.transform[4], y = +it.transform[5] + 1.8;
  const c = icons.filter(i => i.x < x && x - i.x < 60 && Math.abs(i.y - y) < 4).sort((a, b) => b.x - a.x)[0];
  return c ? c.sig : null;
}
/* Which pages' pictures to read: page 1 (its legend says which picture is transfer credit — only page 1's, and never
   the same picture as "Cal Poly Graded Course") and the Course History table (its last heading to the end), the
   only rows the reader files. Marks per page, or null. */
async function dprMarks(pages) {
  let ch = -1; pages.forEach((pg, i) => { if (TCPL.pdfItemsToText(pg.items).split('\\n').some(l => /^Course History$/i.test(l.trim()))) ch = i; });
  if (ch < 0) return null;
  const legend = await dprIcons(pages[0].page);
  const xsig = dprLegendSig(pages[0].items, legend, /Transfer\\s*\\/\\s*Test/i), gsig = dprLegendSig(pages[0].items, legend, /Cal Poly Graded/i);
  if (!xsig || xsig === gsig) return null;
  /* Cal Poly's own pictures, as the legend names them — a picture it doesn't name marks nothing (review 2026-10-11:
     a transfer arrow drawn a pixel differently from the legend's must not pass for a Cal Poly class) */
  const csig = new Set([gsig, dprLegendSig(pages[0].items, legend, /Course In Progress/i), dprLegendSig(pages[0].items, legend, /^\\s*Planned\\s*$/i)].filter(g => g && g !== xsig));
  const out = [];
  for (let i = ch; i < pages.length; i++) { const icons = i === 0 ? legend : await dprIcons(pages[i].page); const mk = icons.map(c => ({ y: c.y, t: c.sig === xsig, c: csig.has(c.sig) })); mk.bare = icons.all; out[i] = mk; }
  return out;
}
/* The report as text, page by page — the text first, then the icons (at most 6 s; past that, or on any failure, the
   text alone, which the reader handles as before). A class row drawn with the transfer icon ends in TCPL.dprXMark,
   one drawn with Cal Poly's own in TCPL.dprCMark, one with none (where every picture was read) in TCPL.dprBMark. */
async function dprDocText(doc) {
  const n = Math.min(doc.numPages || 0, 30), pages = [];
  for (let p = 1; p <= n; p++) { const page = await doc.getPage(p), tc = await page.getTextContent(); pages.push({ page, items: (tc && tc.items) || [] }); }
  let marks = null;
  try { marks = await Promise.race([dprMarks(pages).catch(() => null), new Promise(res => setTimeout(() => res(null), 6000))]); } catch (e) { marks = null; }
  const text = pages.map((pg, i) => '\\n\\n' + TCPL.pdfItemsToText(pg.items, (marks && marks[i]) || null)).join('');
  pages.forEach(pg => { try { pg.page.cleanup(); } catch (e) {} });
  return text;
}
async function readDpr(file) {""", 'ix-icons')

rep('A', """    doc = await lib.getDocument({ data: new Uint8Array(await TCPL.fileBytes(file)) }).promise;
    const n = Math.min(doc.numPages || 0, 30);
    for (let p = 1; p <= n; p++) { const page = await doc.getPage(p); const tc = await page.getTextContent(); text += '\\n\\n' + TCPL.pdfItemsToText(tc && tc.items); try { page.cleanup(); } catch (e) {} }""",
    """    /* pictures as plain pixels (not an ImageBitmap) so the transfer icon can be told from the others */
    doc = await lib.getDocument({ data: new Uint8Array(await TCPL.fileBytes(file)), isOffscreenCanvasSupported: false }).promise;
    text = await dprDocText(doc);""", 'ix-readdpr')

rep('A', """    if (x._open && k === cur) x._now = true;
    else if (x._open && k === nxt) { x._now = false; x._next = true; }""", """    if (x._open && !x._xfer && k === cur) x._now = true;
    else if (x._open && !x._xfer && k === nxt) { x._now = false; x._next = true; }""", 'ix-readdpr-xfer')

# ================================================================================================
# app/index.html — the counts: the report's, once it's in
# ================================================================================================
rep('A', """  if (window.TCPL && P.major && TC.waived && TC.myHistory && TC.marks) { plSync(); const L = TCPL.ledger(); if (L) deg = meRow('schedTabGo', 'past', 'meCheck', `${L.F} of ${L.N} requirements filled`, '', esc(L.major) + (L.T ? ` · ${L.T} in progress` : '')); }""",
    """  /* (2026-10-11) with a report in, the report's count (the Planner's): the flowchart can't see transfer credit */
  if (window.TCPL && P.major && TC.waived && TC.myHistory && TC.marks) { plSync(); const L = TCPL.ledger(), X = L && auditLines(TC.audit, L);
    if (X) deg = meRow('schedTabGo', 'past', 'meCheck', `${X.filled.length} of ${X.live.length} requirements filled`, '', esc(L.major) + (X.inprog.length ? ` · ${X.inprog.length} in progress` : ''));
    else if (L) deg = meRow('schedTabGo', 'past', 'meCheck', `${L.F} of ${L.N} requirements filled`, '', esc(L.major) + (L.T ? ` · ${L.T} in progress` : '')); }""", 'ix-me-row')

rep('A', """function pcSummary(L) {
  const pct = L.N ? Math.round(100 * L.F / L.N) : 0, X = auditLines(TC.audit, L);""",
    """/* (2026-10-11) Your report knows what the flowchart can't (transfer and exam credit): a spot the ledger leaves to do
   shows as the REPORT has it — Satisfied or In Progress, never a line you marked done or one you're taking a class for —
   "On your report". A GE spot by its area; a class spot only when every class the line names is one the spot takes
   (a "Select from …" list line doesn't fill each class it lists). A spot the ledger filled keeps its class. */
function pcByReport(L, X) {
  if (!L || !X) return L;
  const rank = { taking: 1, done: 2 }, ge = {}, lines = [];
  X.live.forEach(b => { const st = b.status === 'satisfied' ? 'done' : b.status === 'in_progress' ? 'taking' : null; if (!st) return;
    if (b.kind === 'ge' && b.ge && rank[st] > (rank[ge[b.ge]] || 0)) ge[b.ge] = st;
    const o = (b.options || []).map(pcK); if (o.length) lines.push({ o, st }); });
  const grid = L.grid.map(t => Object.assign({}, t, { slots: t.slots.map(s => {
    if (s.state !== 'need') return s;
    let st = s.type === 'ge' ? (s.area && ge[s.area]) || null : null;
    if (s.type !== 'ge') { const ok = new Set([...(s.choice || []), ...(s.codes || []), s.code].filter(Boolean).map(pcK));
      lines.forEach(l => { if (l.o.every(c => ok.has(c)) && rank[l.st] > (rank[st] || 0)) st = l.st; }); }
    return st ? Object.assign({}, s, { state: st, rep: true }) : s;
  }) }));
  return Object.assign({}, L, { grid });
}
function pcSummary(L) {
  const X = auditLines(TC.audit, L);
  /* (2026-10-11) with a report in, its count: filled of every line it prints (the Planner's count) */
  if (X) { const F = X.filled.length, N = X.live.length; L = Object.assign({}, L, { F, N }); }
  const pct = L.N ? Math.round(100 * L.F / L.N) : 0;""", 'ix-summary')

rep('A', """  return (none ? dprFirstCard() : '') + `<div class="pc-pg">${pcSummary(L) + pcYears(L) + (none ? '' : pcOther(L) + pcBtns())}</div>`;""",
    """  const LR = pcByReport(L, auditLines(TC.audit, L));
  return (none ? dprFirstCard() : '') + `<div class="pc-pg">${pcSummary(L) + pcYears(LR) + (none ? '' : pcOther(L) + pcBtns())}</div>`;""", 'ix-past-view')

rep('A', """  const line = s.mine ? '<span class="pc-pf tc-mine">Marked done by you</span>' : (s.state === 'done' || s.state === 'taking') && cls ? pcLine(pcK(cls), s.state, row) : '';""",
    """  const line = s.mine ? '<span class="pc-pf tc-mine">Marked done by you</span>' : s.rep ? '<span class="pc-pf">On your report</span>' : (s.state === 'done' || s.state === 'taking') && cls ? pcLine(pcK(cls), s.state, row) : '';""", 'ix-slot-line')

open(PI, 'w', encoding='utf-8').write(S['A']); open(PP, 'w', encoding='utf-8').write(S['P'])
print('transfer-reports: done')
