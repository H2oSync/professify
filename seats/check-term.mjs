/* RESOLVING A TERM LABEL TO PEOPLESOFT'S CODE — 2026-09-16.
   Fixture is REAL DATA, read off Cal Poly's public class search on 2026-09-16 by opening the
   Term lookup (SLO_SS_DERIVED_STRM$prompt) on
   cmsweb.pscs.calpoly.edu/psc/CSLOPRD/EMPLOYEE/SA/c/COMMUNITY_ACCESS.CLASS_SEARCH.GBL.
   The lookup returned "First 1-4 of 4":

       2268  Fall Semester 2026     2026 Fall
       2266  Summer Quarter 2026    2026 Sum
       2264  Spring Quarter 2026    2026 Spr
       2262  Winter Quarter 2026    2026 Wtr

   Two things that fixture is worth, neither of which a synthetic one could give:

   1. It VALIDATES THE CONVENTION against four live codes instead of against a belief. The season
      digits (2/4/6/8) and the calendar-year digits both hold, including across the quarter ->
      semester conversion, which is the change that could plausibly have renumbered things.

   2. It contains THE TRAP. termCandidates('Spring 2027') is
      ["2274","2264","2272","2276","2278"] — and 2264 is a REAL, POPULATED TERM: Spring Quarter
      2026. Spring 2027 does not exist in the lookup yet (its schedule publishes Oct 5), so a
      resolver walking that list reaches 2264 and finds a term that accepts the code, echoes a
      season that matches, and has a full subject list. Every signal except the YEAR says yes.
      If the year check ever weakens, the Oct 5 scrape files a whole term of Spring 2026 sections
      as Spring 2027 and the run goes green. That is the single most expensive bug available in
      this codebase, and section 2 below is built to produce it.

   SPRING 2027 CANNOT BE CONFIRMED BEFORE OCT 5 — the term is not in the public lookup, so
   discover_term has nothing to find. That is a scheduling fact, not a defect: see
   claude/term-code-2026-09-16.md. */
import {termCandidates, parseLabel, matchesTerm, termsNamedIn, resolveTerm} from '/home/claude/repo/seats/term.mjs';
const R=[]; const ok=(c,n,d='')=>R.push({n,c:!!c,d});

/* ---- 1. the convention, against four live codes --------------------------------------------- */
const LIVE=[
  {code:'2268', label:'Fall 2026',   desc:'Fall Semester 2026'},
  {code:'2266', label:'Summer 2026', desc:'Summer Quarter 2026'},
  {code:'2264', label:'Spring 2026', desc:'Spring Quarter 2026'},
  {code:'2262', label:'Winter 2026', desc:'Winter Quarter 2026'},
];
for(const t of LIVE){
  const cands=termCandidates(t.label);
  ok(cands[0]===t.code,`${t.label}: the first candidate is the real code ${t.code}`,JSON.stringify(cands));
  ok(cands.includes(t.code),`${t.label}: ${t.code} is in the candidate list at all`,JSON.stringify(cands));
  /* The echo wording CHANGED with the conversion — "Quarter" for the 2026 quarters, "Semester"
     for Fall 2026 — and the word sits BETWEEN the season and the year, which is exactly what the
     ECHO_PROXIMITY window has to absorb. A constant that silently stops spanning the gap is how
     a correct term stops confirming. */
  ok(matchesTerm(t.desc,t.label),`${t.label}: the live description confirms it ("${t.desc}")`);
}

/* ---- 2. THE TRAP: a real neighbouring term must not confirm ---------------------------------- */
{
  const cands=termCandidates('Spring 2027');
  ok(cands[0]==='2274','Spring 2027 leads with 2274',JSON.stringify(cands));
  ok(cands.includes('2264'),'and 2264 — a REAL populated term — is on the list',JSON.stringify(cands));
  /* Season matches, the code is accepted, the subject list is full. Only the year differs. */
  ok(!matchesTerm('Spring Quarter 2026','Spring 2027'),
     'Spring Quarter 2026 does NOT confirm Spring 2027');
  ok(!matchesTerm('Spring Semester 2026','Spring 2027'),'nor does Spring Semester 2026');
  ok(matchesTerm('Spring Semester 2027','Spring 2027'),'but Spring Semester 2027 does');

  /* End to end, with the world as it actually is today: 2274 does not exist, 2264 does. */
  const world={
    '2274':{held:'', echo:'', subjects:0},                                   // not built yet
    '2264':{held:'2264', echo:'Spring Quarter 2026', subjects:84},           // real and full
    '2272':{held:'', echo:'', subjects:0},
    '2276':{held:'', echo:'', subjects:0},
    '2278':{held:'', echo:'', subjects:0},
  };
  let cur=null;
  const io={
    setTerm:async c=>{ cur=world[c]||{held:'',echo:'',subjects:0}; },
    readEcho:async()=>cur.echo,
    subjectCount:async()=>cur.subjects,
    readField:async()=>cur.held,
  };
  let threw=null,got=null;
  try{ got=await resolveTerm(io,'Spring 2027'); }catch(e){ threw=e; }
  ok(!got,'it does NOT resolve Spring 2027 to a neighbouring term',JSON.stringify(got));
  ok(threw&&threw.kind==='term-unresolved','it throws term-unresolved instead',threw&&threw.kind);
  ok(threw&&/Refusing to guess/.test(threw.message),'and says it is refusing to guess');
  /* The error has to carry what it tried, or the operator cannot tell "not published yet" from
     "our candidate list is wrong". */
  ok(threw&&Array.isArray(threw.tried)&&threw.tried.length===cands.length,
     'and reports every candidate it tried',threw&&threw.tried&&threw.tried.length);
}

/* ---- 3. it DOES resolve once the term exists ------------------------------------------------- */
{
  const world={'2274':{held:'2274', echo:'Spring Semester 2027', subjects:84}};
  let cur={held:'',echo:'',subjects:0};
  const io={ setTerm:async c=>{ cur=world[c]||{held:'',echo:'',subjects:0}; },
             readEcho:async()=>cur.echo, subjectCount:async()=>cur.subjects, readField:async()=>cur.held };
  const got=await resolveTerm(io,'Spring 2027');
  ok(got&&got.code==='2274','once Spring 2027 is built, 2274 resolves',JSON.stringify(got));
}

/* ---- 4. the three signals are each load-bearing ---------------------------------------------- */
for(const [name,world] of Object.entries({
  'field not held (PeopleSoft rejected the code)': {'2274':{held:'', echo:'Spring Semester 2027', subjects:84}},
  'no subjects (term exists but was never built)': {'2274':{held:'2274', echo:'Spring Semester 2027', subjects:0}},
  'echo names two terms (ambiguous page)':         {'2274':{held:'2274', echo:'Spring Semester 2027 — Fall Semester 2026 archived', subjects:84}},
})){
  let cur={held:'',echo:'',subjects:0};
  const io={ setTerm:async c=>{ cur=world[c]||{held:'',echo:'',subjects:0}; },
             readEcho:async()=>cur.echo, subjectCount:async()=>cur.subjects, readField:async()=>cur.held };
  let threw=null; try{ await resolveTerm(io,'Spring 2027'); }catch(e){ threw=e; }
  ok(!!threw,`refuses when: ${name}`);
}

/* ---- 5. readField is REQUIRED, not optional --------------------------------------------------- */
{
  const io={ setTerm:async()=>{}, readEcho:async()=>'Spring Semester 2027', subjectCount:async()=>84 };
  let threw=null; try{ await resolveTerm(io,'Spring 2027'); }catch(e){ threw=e; }
  ok(threw&&/requires io\.readField/.test(threw.message),
     'resolveTerm refuses to run without the field read-back',threw&&threw.message.slice(0,80));
}

/* ---- 6. ambiguity and nonsense ---------------------------------------------------------------- */
ok(termsNamedIn('Spring Semester 2027').length===1,'one term named is one term');
ok(termsNamedIn('Spring 2027 and Fall 2026').length===2,'two named is ambiguous');
ok(!matchesTerm('Spring 2027 schedule available April 27','Spring 2026'),
   'a registrar notice about another term confirms nothing');
ok(parseLabel('Spring 2027')!==null&&parseLabel('nonsense')===null,'labels parse or refuse');
ok(termCandidates('nonsense').length===0,'an unparseable label yields no candidates');

if(process.env.VERBOSE)for(const r of R)console.log((r.c?'  ok   ':'  FAIL ')+r.n);
const bad=R.filter(r=>!r.c);
for(const r of bad) console.log(`  FAIL ${r.n}${r.d?' — '+r.d:''}`);
console.log(`check-term: ${R.length-bad.length} passed, ${bad.length} failed`);
process.exit(bad.length?1:0);
