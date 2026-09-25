/* THE GE BROWSER — Explore's third door. 2026-08-31.
   Tate: "when you are on explore under classes have a toggle to show GEs i dont know the best
   way to do this but lots of people want easy GEs to take with their friends so make it simple
   not too complicated and easy to just find the GEs that you need to fulfill."

   The thing that can go wrong here is not layout. It is the app telling a student an area is
   DONE. How many courses an area needs varies by catalog year and we hold the course-to-area
   map, not the unit rules — so every assertion below that looks like copy-checking is really
   checking that the screen counts what it knows and stops there. */
import {chromium} from 'playwright';
import fs from 'fs';
const SRC=fs.readFileSync('/mnt/user-data/outputs/index.html','utf8');
const R=[]; const ok=(n,c,d='')=>R.push({n,c:!!c,d});
const b=await chromium.launch();
const errs=[];
const p=await b.newPage({viewport:{width:1400,height:1100}});
p.on('pageerror',e=>errs.push(e.message));
await p.goto(process.env.PAGE||'file:///mnt/user-data/outputs/index.html');   /* PAGE= points a mutation run at a broken copy */
await p.waitForFunction(()=>!!window.PROFESSIFY_BUILD,{timeout:20000});
await p.waitForTimeout(1900);

/* ---- the door ---------------------------------------------------------------------------- */
/* REVERSED 2026-09-01: "put GEs under classes. Not its own section" (Tate). It shipped as a
   third segment beside Classes and Professors, on the reasoning that you BROWSE a GE rather
   than search for one. But the control above asks what you are looking for, and the answer is
   still a class — a GE is a kind of class, not a third kind of thing. It is a filter on the
   Classes results now, in the slot directly beneath, and Classes stays lit while it is open. */
const door=await p.evaluate(()=>{
  show('explore'); setExMode('classes');
  /* .ex-seg-v since Sean's top row landed 2026-09-15: the horizontal segment under a centred
     hero became a vertical toggle standing beside the search box. The DOCTRINE is unchanged and
     is what this file actually guards — Explore asks ONE question and offers TWO answers — so
     only the selector moves. The thumb is a <span>, so querying buttons still yields exactly
     the two answers. */
  const seg=document.querySelector('#view-explore .ex-seg-v');
  const btns=[...seg.querySelectorAll('button')].map(b=>b.textContent.trim());
  const swOf=()=>[...document.querySelectorAll('#exContext .ex-gesw button')]
    .map(b=>b.textContent.trim()+(b.classList.contains('on')?'*':''));
  const onClasses=swOf();
  setExMode('ge');
  return {btns, onClasses, onGe:swOf(),
    classesStaysLit:document.getElementById('ex-classes').classList.contains('active'),
    profsOff:!document.getElementById('ex-profs').classList.contains('active'),
    noThirdSegment:!document.getElementById('ex-ge'),
    placeholder:document.getElementById('exQuery').placeholder,
    grid:!!document.querySelector('.ge-grid'),
    /* The centred hero is GONE, not merely restyled (Tate, 2026-09-15: "implement this explore
       look and take the current one away"). It cost ~700px above the first result. */
    noHero:!document.querySelector('#view-explore .ex-hero'),
    /* REVERSED 2026-09-16. This asserted the QUESTION was gone. Tate put it back — "put the what
       are you looking for above the search" — and he is right that the two are separable: what
       cost ~700px was a 44px line CENTRED over a 620px box, with an eyebrow above and a centred
       segment below. The sentence was never the expensive part. So the invariant is not "no
       question", it is "no HERO": the question may exist, but left-aligned with the search field
       and off the display size. Asserting its absence would now block the design Tate asked for,
       which is the same mistake the "all three legal docs share one date" test made. */
    q:(function(){
      var q=document.querySelector('#view-explore .ex-q');
      var sp=document.querySelector('#view-explore .ex-top .ex-spot');
      if(!q||!sp)return {present:!!q};
      var a=q.getBoundingClientRect(), c=sp.getBoundingClientRect();
      var cs=getComputedStyle(q);
      return {present:true, text:q.innerText.trim(),
              size:parseFloat(cs.fontSize),
              display:parseFloat(getComputedStyle(document.documentElement).getPropertyValue('--t-display'))||44,
              alignedLeft:Math.abs(a.left-c.left)<2,
              above:a.bottom<=c.top+1,
              centred:cs.textAlign==='center'};
    })(),
    searchIsLeftOfToggle:(function(){
      var q=document.getElementById('exQuery'), g=document.querySelector('.ex-seg-v');
      if(!q||!g)return false;
      return q.getBoundingClientRect().left < g.getBoundingClientRect().left;
    })()};
});
ok('exploreAsksOneQuestionWithTwoAnswers', door.btns.join('|')==='Classes|Professors', door.btns.join('|'));
ok('geIsNoLongerAThirdSegment', door.noThirdSegment);
/* 2026-09-24: the chip row follows the 09-23 feature map — GEs · My major (All classes with no
   major on file) · Saved. The doctrine is unchanged: GEs is a filter UNDER Classes, one lit at a time. */
ok('itIsAFilterUnderClasses',
   door.onClasses.join('|')==='GEs|All classes*|Saved' && door.onGe.join('|')==='GEs*|All classes|Saved',
   JSON.stringify({onClasses:door.onClasses,onGe:door.onGe}));
ok('andClassesStaysLitWhileBrowsingGes', door.classesStaysLit && door.profsOff,
   'a GE is a kind of class — the segment above should still say so');
ok('andTheSearchBoxSaysWhatItSearchesNow', /GE/i.test(door.placeholder), door.placeholder);
ok('itOpensOnTheGridOfAreas', door.grid);
ok('theCentredHeroIsGone', door.noHero,
   'the eyebrow + 44px centred question + 620px box were the ~700px above the first result');
ok('theQuestionIsStillAsked', door.q && door.q.present && /What are you looking for/.test(door.q.text||''),
   JSON.stringify(door.q));
ok('butLeftAlignedWithTheSearchBoxNotCentred', door.q && door.q.alignedLeft && !door.q.centred,
   JSON.stringify(door.q));
ok('andAboveIt', door.q && door.q.above, JSON.stringify(door.q));
ok('andOffTheDisplaySize', door.q && door.q.size < door.q.display,
   'the display token is the hero size; a page subject is not a hero — ' + JSON.stringify(door.q));
ok('theSearchSitsLeftOfTheToggle', door.searchIsLeftOfToggle,
   'Sean\u2019s row is a left column of search+filters with the toggle standing beside it');

/* ---- every area, with what you have logged in it ------------------------------------------ */
const grid=await p.evaluate(()=>{
  myHistory.length=0; myClasses.length=0;
  /* one logged, one being taken now, in two different areas */
  myHistory.push({code:'ENGL 1132',term:'Fall',year:2024,professor:'X'});
  const inArts=GE_COURSES.filter(c=>/Arts \(3A\)/.test(c.area))[0];
  myClasses.push(inArts.code);
  setExMode('ge');
  const cards=[...document.querySelectorAll('.ge-card')];
  const read=c=>({key:c.querySelector('.ge-k').textContent.trim(),
                  lbl:c.querySelector('.ge-lbl').textContent.trim(),
                  tk:c.querySelector('.ge-tk').textContent.trim(),
                  done:c.classList.contains('done'),
                  clipped:c.querySelector('.ge-lbl').scrollWidth>c.querySelector('.ge-lbl').clientWidth+1});
  const all=cards.map(read);
  return {n:cards.length, all, keys:all.map(a=>a.key),
          note:(document.querySelector('.ge-note')||{}).textContent||'',
          head:(document.querySelector('.grouphead')||{}).textContent||''};
});
ok('everyAreaIsOnTheGrid', grid.n===15, grid.n+' cards');
ok('eachCardLeadsWithItsAreaKey', grid.keys.includes('1A')&&grid.keys.includes('4B')&&grid.keys.includes('UD3'),
   'a student told "you owe a 4B" is looking for those two characters');
ok('noAreaNameIsTruncated', grid.all.every(a=>!a.clipped),
   'the area name is what the key means — an ellipsis makes the grid something you decode');
ok('itCountsWhatYouHaveLogged',
   grid.all.filter(a=>a.done).length===2
   && grid.all.filter(a=>a.done).every(a=>/1 taken/.test(a.tk)),
   'one from Past Classes and one from My Classes: '+grid.all.filter(a=>a.done).map(a=>a.key+' '+a.tk).join(', '));
ok('andSaysNothingYetForTheRest',
   grid.all.filter(a=>!a.done).every(a=>/none yet/.test(a.tk)));

/* THE claim. */
ok('itNeverSaysAnAreaIsComplete',
   !/\b(complete|completed|done|satisfied|fulfilled|requirement met)\b/i.test(grid.note+' '+grid.head+' '+grid.all.map(a=>a.tk).join(' ')),
   'areas take different numbers of courses by catalog year; we hold the course map, not the unit rules');
ok('andSaysWhereTheRealAnswerIs', /degree audit/i.test(grid.note), grid.note.slice(0,90));
ok('andSaysWhatItIsCounting', /Past Classes/i.test(grid.note)&&/taking now/i.test(grid.note));

/* ---- one area ----------------------------------------------------------------------------- */
const area=await p.evaluate(()=>{
  exSetGeArea('3B');
  const rows=[...document.querySelectorAll('.cls-list .cls-row')];
  const codes=rows.map(r=>(r.querySelector('.code')||r).textContent.trim().split(/\s{2,}|\n/)[0]);
  /* every course listed really is in this area, per the app's own map */
  const label=GE_AREAS.filter(a=>a.key==='3B')[0].label;
  const allInArea=codes.every(c=>{
    const m=/^([A-Z]+\s*\d+[A-Z]?)/.exec(c); const code=m?m[1].replace(/\s+/g,' ').trim():c;
    return geAreasFor(code).indexOf(label)>=0;
  });
  return {rows:rows.length, allInArea, back:!!document.querySelector('.ge-back'),
    head:(document.querySelector('.grouphead')||{}).textContent||'',
    note:(document.querySelector('.ge-note')||{}).textContent||''};
});
ok('anAreaListsItsCourses', area.rows>0, area.rows+' rows');
ok('andOnlyItsCourses', area.allInArea,
   'a list under an area heading is a claim that every row counts for it');
ok('withAWayBackToTheGrid', area.back);
ok('theHeadingNamesTheArea', /Humanities/i.test(area.head), area.head);
ok('andSaysHowItIsSorted', /best-rated professor/i.test(area.note), area.note.slice(0,80));

/* ordering: best professor first, unrated last and never as zero */
const order=await p.evaluate(()=>{
  const rows=[...document.querySelectorAll('.cls-list .cls-row')];
  const codes=rows.map(r=>{const t=r.textContent; const m=/^\s*([A-Z]+\s+\d+[A-Z]?)/.exec(t); return m?m[1]:'';});
  const rated=codes.map(c=>{try{return geBestRating(c);}catch(e){return null;}});
  let lastReal=-1, firstNull=-1;
  rated.forEach((v,i)=>{ if(v!=null)lastReal=i; if(v==null&&firstNull<0)firstNull=i; });
  return {anyRated:rated.some(v=>v!=null), unratedAllAtTheEnd:(firstNull<0)||(lastReal<firstNull)};
});
ok('unratedCoursesSortLastNotAsZero', order.unratedAllAtTheEnd,
   'a course nobody has rated is not a bad course, and must not be shown as one');

/* ---- leaving and coming back -------------------------------------------------------------- */
const leave=await p.evaluate(()=>{
  setExMode('classes');
  const o={leftGe:!document.querySelector('.ge-grid')&&!document.querySelector('.ge-back')};
  setExMode('ge');
  o.backAtTheTop=!!document.querySelector('.ge-grid');
  return o;
});
ok('switchingAwayLeavesTheBrowser', leave.leftGe);
ok('andComingBackStartsAtTheTop', leave.backAtTheTop,
   'not three areas deep in wherever you were last week');

ok('noPageErrors', errs.length===0, errs.slice(0,3).join(' | '));
await b.close();
const bad=R.filter(x=>!x.c);
R.forEach(x=>console.log((x.c?'  ok  ':'  FAIL')+' '+x.n+(x.d?('   '+(x.c?'':'<< ')+x.d):'')));
console.log(`\n${R.length-bad.length}/${R.length} passed`);
process.exit(bad.length?1:0);
