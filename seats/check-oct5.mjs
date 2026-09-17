/* THE OCT 5 COLD START — 2026-09-16.
   Spring 2027's schedule publishes on 5 October and its PeopleSoft term code does not exist
   before then (verified against the live Term lookup on 09-16: four terms, none of them Spring).
   So the first time the pipeline ever meets Spring 2027 is the morning it matters, and there is
   no way to rehearse that one variable. Everything AROUND it can be rehearsed, and this is that.

   The sequence this file pins, at the real dates, against the real calendar:

     Oct 4   Spring is dark. Nothing asks for it. Fall runs.
     Oct 5   Spring flips to quiet/discovery. It has no code. `blocked` is EMPTY — blocked only
             counts terms in an ENROLMENT phase — so the run would be green but for the
             autodiscover job. needs_term_discovery must be true AND discover_labels must name
             Spring, because a boolean can be branched on but not acted on.
     Oct 19  Spring reaches appointments at a ten-minute cadence. Now blocked fills and guard
             fires. This is the day that must never be the first time anyone finds out.

   And the half that matters just as much: once the code is committed, ALL of that goes quiet and
   Spring dispatches. A gate that fires correctly but never clears is a gate nobody can satisfy. */
import {execFileSync} from 'child_process';
import {writeFileSync, readFileSync, mkdtempSync} from 'fs';
import {tmpdir} from 'os';
import {join} from 'path';
const R=[]; const ok=(c,n,d='')=>R.push({n,c:!!c,d});
const SEATS='/home/claude/repo/seats';

function planAt(when, calendar){
  const env={...process.env};
  if(calendar) env.CP_CALENDAR=calendar;
  let stdout='', code=0;
  try{ stdout=execFileSync('node',['plan.mjs','--at',when],{cwd:SEATS,env,encoding:'utf8'}); }
  catch(e){ stdout=(e.stdout||'')+(e.stderr||''); code=e.status; }
  const m=stdout.match(/\noutputs: (\{.*\})/);
  return {out:m?JSON.parse(m[1]):null, stdout, code};
}

/* ---- 1. the three dates, with the calendar as it stands (Spring has no code) ----------------- */
{
  const d4=planAt('2026-10-04T14:00:00Z');
  ok(d4.out && d4.out.needs_term_discovery==='false','Oct 4: nothing needs discovering yet',d4.out&&d4.out.needs_term_discovery);
  ok(d4.out && d4.out.discover_labels==='','Oct 4: and no term is named',d4.out&&d4.out.discover_labels);
  ok(/Spring 2027\s+dark/.test(d4.stdout),'Oct 4: Spring is dark');
  ok(d4.out && d4.out.scrape==='true' && /"2268"/.test(d4.out.terms),'Oct 4: Fall still runs');

  const d5=planAt('2026-10-05T14:00:00Z');
  ok(d5.out && d5.out.needs_term_discovery==='true','Oct 5: discovery is needed');
  /* THE ONE THAT MAKES THE JOB POSSIBLE. A boolean can be branched on; only a label can be
     resolved. Without this the only automatic response available on Oct 5 is a warning. */
  ok(d5.out && d5.out.discover_labels==='Spring 2027','Oct 5: and it NAMES Spring 2027',d5.out&&d5.out.discover_labels);
  ok(d5.out && d5.out.blocked==='','Oct 5: blocked is still empty — this is why guard alone is not enough',d5.out&&d5.out.blocked);
  ok(d5.code===0,'Oct 5: plan still exits 0 so Fall is not held hostage',String(d5.code));
  ok(d5.out && /"2268"/.test(d5.out.terms),'Oct 5: Fall still dispatches');
  ok(!/"2274"|"227\d"/.test(d5.out.terms),'Oct 5: and Spring is NOT dispatched with a guessed code',d5.out&&d5.out.terms);

  const d19=planAt('2026-10-19T14:00:00Z');
  ok(d19.out && /Spring 2027/.test(d19.out.blocked),'Oct 19: blocked now names Spring',d19.out&&d19.out.blocked);
  ok(d19.out && d19.out.needs_term_discovery==='true','Oct 19: still needs discovery');
  ok(/every 10m/.test(d19.stdout),'Oct 19: Spring would be on the opening-day 10-minute cadence');
  ok(d19.out && /"2268"/.test(d19.out.terms),'Oct 19: Fall still runs rather than the whole run dying');
}

/* ---- 2. THE GATE CLEARS once the code is committed -------------------------------------------- */
{
  const dir=mkdtempSync(join(tmpdir(),'cal-'));
  const cal=JSON.parse(readFileSync(join(SEATS,'registrar-calendar.json'),'utf8'));
  const sp=cal.terms.find(t=>/Spring 2027/.test(t.label));
  ok(!!sp,'the fixture calendar has a Spring 2027 term to fill in');
  sp.term_code='2274';
  sp.term_code_confirmed='FIXTURE ONLY — check-oct5.mjs. Not a real confirmation.';
  const p=join(dir,'cal.json'); writeFileSync(p,JSON.stringify(cal));

  const d5=planAt('2026-10-05T14:00:00Z',p);
  ok(d5.out && d5.out.needs_term_discovery==='false','with the code committed, Oct 5 needs nothing',d5.out&&d5.out.needs_term_discovery);
  ok(d5.out && d5.out.discover_labels==='','and names no term',d5.out&&d5.out.discover_labels);
  ok(d5.out && /"2274"/.test(d5.out.terms),'and Spring 2027 now dispatches',d5.out&&d5.out.terms);
  ok(d5.out && /"2268"/.test(d5.out.terms),'alongside Fall — both terms at once, which is the point',d5.out&&d5.out.terms);

  const d19=planAt('2026-10-19T14:00:00Z',p);
  ok(d19.out && d19.out.blocked==='','and Oct 19 is no longer blocked',d19.out&&d19.out.blocked);
  ok(d19.out && /"2274"/.test(d19.out.terms),'Spring runs on registration morning',d19.out&&d19.out.terms);
  ok(d19.code===0,'and the run is green',String(d19.code));
}

/* ---- 3. the workflow is actually wired to it -------------------------------------------------- */
{
  const wf=readFileSync('/home/claude/repo/.github/workflows/update-seats.yml','utf8');
  ok(/needs_discovery:\s*\$\{\{\s*steps\.clock\.outputs\.needs_term_discovery/.test(wf),
     'the plan job exposes needs_discovery');
  ok(/discover_labels:\s*\$\{\{\s*steps\.clock\.outputs\.discover_labels/.test(wf),
     'and exposes discover_labels — without it autodiscover has nothing to resolve');
  ok(/^\s{2}autodiscover:/m.test(wf),'the autodiscover job exists');
  const job=wf.split(/^\s{2}autodiscover:/m)[1].split(/^\s{2}\w[\w-]*:/m)[0];
  ok(/needs\.plan\.outputs\.needs_discovery == 'true'/.test(job),'it fires on needs_discovery');
  ok(/needs\.plan\.outputs\.discover_labels != ''/.test(job),'and only when a term is actually named');
  ok(/CP_DISCOVER_TERM:\s*'1'/.test(job),'it runs the discover path, not a scrape');
  ok(/CP_TERM_LABEL:\s*\$\{\{\s*needs\.plan\.outputs\.discover_labels/.test(job),
     'against the label the planner named');
  ok(/exit 1/.test(job),'and it FAILS the run — a found code that nobody commits is still no code');
  /* The rule that must survive automation: looking the code up is automatic, writing it down is not. */
  ok(!/git (commit|push)/.test(job),'it does NOT commit the code — that still gets a human’s eyes');
}

if(process.env.VERBOSE)for(const r of R)console.log((r.c?'  ok   ':'  FAIL ')+r.n);
const bad=R.filter(r=>!r.c);
for(const r of bad) console.log(`  FAIL ${r.n}${r.d?' — '+r.d:''}`);
console.log(`check-oct5: ${R.length-bad.length} passed, ${bad.length} failed`);
process.exit(bad.length?1:0);
