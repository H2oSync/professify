#!/usr/bin/env python3
r"""The website's report import (termchamp.com, index.html) reads transfer students' reports right too — the same rules
as the phone's build 2026-10-11 03:30 (transfer-reports-2026-10-11.py). Tate: "okay do this and upload to the index
html" (2026-10-11, on "the website's own report import still has the old bug").

The website's import (Past Classes › upload: pdfToText → dprParse → the review list → confirmDprImport) had the same
three faults the phone had: a transfer's community-college and exam credit printed as graded classes in his first
Cal Poly term was filed as Cal Poly classes; "300" / "400" where a grade goes was read as a word of the title, so
those classes were filed as THIS term's (My Classes) with "300" in their names; and nothing read the report's icons.

What this changes, in index.html only (the website has no reader v2 / counts to change):
  · pdfItemsToText(items, marks) and the DPR_* constants, dprPrinted, dprTermRunning: the phone's code, word for word
    (copied out of app/planner.js — run this AFTER transfer-reports-2026-10-11.py), so the lift stays exact.
  · dprParse: the same row rules as the phone's — the icon marks, "N00" a grade (a title word on a Cal Poly-icon row),
    no-icon credit grades, articulation numbers, a credit grade in a term still before its finals when printed (never
    a W / IC / RP, never on a Cal Poly-icon row), and posted credit with no grade is never this term's class.
  · pdfToText: pictures as plain pixels; for a Degree Progress Report, page 1's legend and the Course History pages'
    icons (dprIcons / dprLegendSig / dprMarks, copied from app/index.html), within 6 s, else the words alone.
  · the review list: a transfer row is tagged "transfer"; the transfer count is its own note (review 2026-10-11).
  · app-dev/source/build.py lifts the whole DPR_GRADE block, so a rebuilt planner.js has the new constants.

Usage: python3 transfer-reports-desktop-2026-10-11.py <repo-dir>      Replayable: every anchor must match once."""
import sys, os
D = sys.argv[1]
PD = os.path.join(D, 'index.html')
S = open(PD, encoding='utf-8').read()
P = open(os.path.join(D, 'app', 'planner.js'), encoding='utf-8').read()
A = open(os.path.join(D, 'app', 'index.html'), encoding='utf-8').read()

def rep(a, b, label):
    global S
    n = S.count(a)
    if n != 1: sys.exit(f'{label}: anchor matched {n}x')
    S = S.replace(a, b)
def between(s, a, b, label):
    if s.count(a) != 1: sys.exit(f'{label}: start matched {s.count(a)}x')
    i = s.index(a); j = s.index(b, i); return s[i:j]

# ---- the phone's blocks, word for word ----
ITEMS = between(P, 'function pdfItemsToText(items, marks){', 'function fileBytes(file){', 'phone pdfItemsToText')
CONSTS = between(P, 'var DPR_GRADE=', 'var DPR_TERM=', 'phone DPR consts')
ICONS = between(A, "/* (2026-10-11) The report's pictures.", '/* The report as text, page by page', 'phone icons')
if 'TCPL.pdfItemsToText' not in ICONS: sys.exit('phone icons: expected TCPL.pdfItemsToText')
ICONS = ICONS.replace('TCPL.pdfItemsToText', 'pdfItemsToText')

OLD_ITEMS = between(S, 'function pdfItemsToText(items){', 'function fileBytes(file){', 'website pdfItemsToText')
# the constants go up here, beside pdfItemsToText, at the top level of its <script>: pdfItemsToText needs the marks,
# and dprParse (inside a later script's closure) reads them as globals. The old DPR_GRADE line in that closure goes.
rep(OLD_ITEMS, CONSTS + ITEMS, 'items')
rep("var DPR_GRADE=/^(?:[A-D][+-]?|F|CR|NC|W|IC|RP|333)$/;\n", "/* DPR_GRADE and the 2026-10-11 constants (DPR_TEST, DPR_CREDIT, the marks, dprPrinted, dprTermRunning) are defined\n   beside pdfItemsToText, in the earlier <script>, so both can read them */\n", 'consts')

# ---- dprParse: the row rules (the same anchors and text as the phone's patch) ----
rep("""    var ln=String(lines[k]||'').trim();
    if(!ln||DPR_NOISE.test(ln))continue;
    var m=DPR_ROW.exec(ln);""", """    var ln=String(lines[k]||'').trim();
    var xmark=ln.indexOf(DPR_XMARK)>=0, bmark=ln.indexOf(DPR_BMARK)>=0, cmark=ln.indexOf(DPR_CMARK)>=0;
    if(xmark||bmark||cmark)ln=ln.split(DPR_XMARK).join('').split(DPR_BMARK).join('').split(DPR_CMARK).join('').trim();
    if(!ln||DPR_NOISE.test(ln))continue;
    var m=DPR_ROW.exec(ln);""", 'row-mark')
rep("    if(gradeTok&&!DPR_GRADE.test(gradeTok)){ title=(title+' '+gradeTok).trim(); gradeTok=''; }",
    "    if(gradeTok&&(!DPR_GRADE.test(gradeTok)||(cmark&&DPR_TEST.test(gradeTok)))){ title=(title+' '+gradeTok).trim(); gradeTok=''; }", 'title-word')
rep("    var xfer=(gradeTok==='333')||/^(TRAN|AP|DUD|PORT)$/.test(subj)||/(TC|TR)\\d*$/.test(nbr);",
    """    var xfer=xmark||(bmark&&DPR_CREDIT.test(gradeTok))||DPR_TEST.test(gradeTok)||(gradeTok==='333')||/^(TRAN|AP|DUD|PORT)$/.test(subj)||/(TC|TR)\\d*$/.test(nbr)
      /* (2026-10-11) a catalog number that isn't Cal Poly's shape is an articulation placeholder: 1TR, 1T13, 4A1, 4AA */
      ||!/^\\d{3,4}[A-Z]{0,2}$/.test(nbr);
    /* for the date rule below: a credit grade (not a mid-term W / IC / RP), and Cal Poly's own icon — facts, never the grade */
    var postable=!!gradeTok&&!/^(?:W|IC|RP)$/.test(gradeTok);""", 'xfer')
rep("      _dpr:true, _open:stillOpen, _xfer:xfer, _units:units,",
    "      _dpr:true, _open:stillOpen, _xfer:xfer, _units:units, _post:postable, _cp:cmark,", 'row-facts')
rep("""  return {ok:true, rows:out, program:prog, skipped:skipped,
          latestTerm:""", """  /* (2026-10-11) a grade on a class in a term that was still running when the report was printed is posted credit:
     a transfer's community-college and AP classes all print in their first Cal Poly term, graded */
  var printed=dprPrinted(text);
  out.forEach(function(r){ if(r._post&&!r._xfer&&!r._cp&&dprTermRunning(r.term,r.year,printed))r._xfer=true; });
  /* posted credit with no grade (a study-abroad placeholder, "AP 300") is not a class being taken */
  out.forEach(function(r){ if(r._xfer)r._now=false; });
  return {ok:true, rows:out, program:prog, skipped:skipped,
          latestTerm:""", 'date-rule')

# ---- reading the PDF: the icons, for a Degree Progress Report ----
rep("""/* Returns the whole document's text, in reading order, pages joined by a blank line. Capped at""",
    ICONS + """/* Returns the whole document's text, in reading order, pages joined by a blank line. Capped at""", 'icons')
rep("""  var doc=await lib.getDocument({data:new Uint8Array(buf)}).promise;
  var n=Math.min(doc.numPages||0,30), out=[];
  for(var p=1;p<=n;p++){
    if(typeof onPage==='function'){ try{ onPage(p,n); }catch(e){} }
    var page=await doc.getPage(p);
    var tc=await page.getTextContent();
    out.push(pdfItemsToText(tc&&tc.items));
    try{ page.cleanup(); }catch(e){}
  }
  try{ doc.destroy(); }catch(e){}
  return out.join('\\n\\n');""", """  /* pictures as plain pixels (not an ImageBitmap): a Degree Progress Report says which classes are transfer credit
     only with an icon (2026-10-11) */
  var doc=await lib.getDocument({data:new Uint8Array(buf),isOffscreenCanvasSupported:false}).promise;
  var n=Math.min(doc.numPages||0,30), pages=[];
  for(var p=1;p<=n;p++){
    if(typeof onPage==='function'){ try{ onPage(p,n); }catch(e){} }
    var page=await doc.getPage(p);
    var tc=await page.getTextContent();
    pages.push({page:page,items:(tc&&tc.items)||[]});
  }
  /* a Degree Progress Report: its icons (page 1's legend and the Course History pages), within 6 s — else the words */
  var marks=null;
  try{
    if(dprLooksLikeOne(pages.map(function(pg){ return pdfItemsToText(pg.items); }).join('\\n\\n')))
      marks=await Promise.race([dprMarks(pages).catch(function(){ return null; }), new Promise(function(res){ setTimeout(function(){ res(null); },6000); })]);
  }catch(e){ marks=null; }
  var out=pages.map(function(pg,i){ return pdfItemsToText(pg.items,(marks&&marks[i])||null); });
  pages.forEach(function(pg){ try{ pg.page.cleanup(); }catch(e){} });
  try{ doc.destroy(); }catch(e){}
  return out.join('\\n\\n');""", 'pdf-to-text')

# ---- the review list (review 2026-10-11): a transfer row says so; the transfer count is its own note ----
rep("""      +(r.already?'<span class="fr-shared">already logged</span>':'')""",
    """      +(r.already?'<span class="fr-shared">already logged</span>':'')
      +(r._dpr&&r._xfer?'<span class="fr-shared">transfer</span>':'')""", 'row-tag')
rep("""  if(nUnk&&isDpr)notes.push(nUnk+' of these aren’t Cal Poly catalog courses'
    +(nXfer?(' — '+nXfer+' are transfer, AP or study-abroad credit, which is normal'):'')+'; they’re kept as your report wrote them');""",
    """  /* (2026-10-11) transfer credit is now found by the report's own icons too, and much of it has Cal Poly catalog numbers
     (an articulated class): its count is its own note, not part of the "not in the catalog" one */
  if(isDpr&&nXfer)notes.push(nXfer+' '+(nXfer===1?'is':'are')+' transfer, AP or study-abroad credit — saved as that, with no professor to rate');
  if(nUnk&&isDpr)notes.push(nUnk+' of these aren’t Cal Poly catalog courses; they’re kept as your report wrote them');""", 'note')

open(PD, 'w', encoding='utf-8').write(S)

# ---- build.py: DPR_GRADE now opens a block that ends where pdfItemsToText begins (review 2026-10-11) ----
PB = os.path.join(D, 'app-dev', 'source', 'build.py')
B = open(PB, encoding='utf-8').read()
old = """for v in ['var DPR_GRADE=', 'var DPR_TERM=', 'var DPR_NOISE=', 'var DPR_ROW=', "const ABROAD_MARK="]:
    _a = _ix.index(v); L.append(_ix[_a:_ix.index('\\n', _a)])"""
new = """# 2026-10-11: DPR_GRADE opens a block (DPR_TEST, DPR_CREDIT, the row marks, dprPrinted, dprTermRunning) that ends where
# pdfItemsToText begins — lifted whole, or the phone's dprParse would read names that aren't there
_a = _ix.index('var DPR_GRADE='); L.append(_ix[_a:_ix.index('function pdfItemsToText(', _a)].rstrip('\\n'))
for v in ['var DPR_TERM=', 'var DPR_NOISE=', 'var DPR_ROW=', "const ABROAD_MARK="]:
    _a = _ix.index(v); L.append(_ix[_a:_ix.index('\\n', _a)])"""
if new not in B:
    if B.count(old) != 1: sys.exit('build.py: anchor matched %dx' % B.count(old))
    open(PB, 'w', encoding='utf-8').write(B.replace(old, new))
print('transfer-reports-desktop: done')
