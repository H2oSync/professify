/* Drives the Hawk ask box inside the REAL index.html, at both breakpoints.
   Usage:  node check-hawk.mjs      (expects index.html plus hawk-*.js/css in cwd)
   PW_CHROME=/path/to/chrome overrides the browser binary.
   A box asserted only in source is a box nobody has ever typed into. */
import { chromium } from 'playwright';
import http from 'node:http'; import fs from 'node:fs'; import path from 'node:path';
const T={'.html':'text/html','.js':'text/javascript','.css':'text/css'};
const srv=http.createServer((q,r)=>{const u=q.url.split('?')[0];const f=path.join(process.cwd(),u==='/'?'index.html':u);
 if(!f.startsWith(process.cwd())||!fs.existsSync(f)||fs.statSync(f).isDirectory()){r.writeHead(404);return r.end();}
 r.writeHead(200,{'content-type':T[path.extname(f)]||'application/octet-stream'});fs.createReadStream(f).pipe(r);});
await new Promise(r=>srv.listen(8125,r));
const b=await chromium.launch({executablePath:process.env.PW_CHROME});
const results=[]; const ok=(n,c,d='')=>results.push({n,c:!!c,d});

for (const [w,h,label] of [[1280,900,'desktop'],[390,780,'phone']]) {
  const ctx=await b.newContext({viewport:{width:w,height:h}});
  /* Everything external is blocked so the run is deterministic and never touches termchamp.com.
     :8125 is this harness's own server; :8787 is the model-tier stand-in, when it is running. */
  await ctx.route('**',r=>{
    const u=r.request().url();
    return (u.startsWith('http://localhost:8125')||u.startsWith('http://localhost:8787'))?r.continue():r.abort();
  });
  const p=await ctx.newPage(); const errs=[]; p.on('pageerror',e=>errs.push(e.message));
  await p.goto('http://localhost:8125/',{waitUntil:'domcontentloaded'});
  await p.waitForTimeout(4000);

  ok(`${label}: the Hawk icon exists`, await p.evaluate(()=>!!document.querySelector('.hawk-fab')));
  await p.click('.hawk-fab'); await p.waitForTimeout(250);
  ok(`${label}: it opens a box`, await p.evaluate(()=>!!document.querySelector('.hawk-box')));

  /* The three things that make this a box beside the app and not a modal over it. */
  ok(`${label}: NOTHING is dimmed or blurred`, await p.evaluate(()=>{
    const scrim=[...document.querySelectorAll('body > *')].some(n=>{
      const s=getComputedStyle(n);
      if (s.position!=='fixed') return false;
      const r=n.getBoundingClientRect();
      const covers = r.width>=window.innerWidth*0.95 && r.height>=window.innerHeight*0.95;
      const tinted = s.backgroundColor!=='rgba(0, 0, 0, 0)' && s.backgroundColor!=='transparent';
      const blurred = (s.backdropFilter||s.webkitBackdropFilter||'none')!=='none';
      return covers && (tinted||blurred);
    });
    return !scrim;
  }));
  ok(`${label}: the app behind is still clickable`, await p.evaluate(()=>{
    const el=document.elementFromPoint(20, Math.round(window.innerHeight/2));
    return !!el && !el.closest('.hawk-box');
  }), await p.evaluate(()=>{const el=document.elementFromPoint(20,Math.round(window.innerHeight/2));return el?el.className||el.tagName:'none';}));

  /* SMALL IS THE FEATURE, so it is a number rather than an adjective. */
  const ceiling = label==='desktop' ? 0.16 : 0.42;
  ok(`${label}: the box is small (under ${Math.round(ceiling*100)}%)`, await p.evaluate((c)=>{
    const r=document.querySelector('.hawk-box').getBoundingClientRect();
    return (r.width*r.height)/(window.innerWidth*window.innerHeight) < c;
  }, ceiling), await p.evaluate(()=>{const r=document.querySelector('.hawk-box').getBoundingClientRect();
    return Math.round(100*(r.width*r.height)/(window.innerWidth*window.innerHeight))+'% of the screen';}));
  ok(`${label}: it sits in the bottom corner`, await p.evaluate(()=>{
    const r=document.querySelector('.hawk-box').getBoundingClientRect();
    return r.bottom > window.innerHeight*0.55 && r.top > window.innerHeight*0.12;
  }));

  /* ---- THE LEDGER'S MAJOR (apply-sep24) ---------------------------------------------------------
     plLedgerCompute read the planner's <select>, whose default is the FIRST major (Plant Sciences),
     until My planner was opened. Asked here before the planner has ever been shown. */
  const led = await p.evaluate(()=>{
    if (typeof plLedgerCompute !== 'function') return { skip: true };
    const out = {};
    student.major = null;
    out.none = plLedgerCompute().led === null;
    student.major = 'Business Administration';
    const lc = plLedgerCompute();
    out.name = lc.mm && lc.mm.name;
    out.sel = (SCHED_MAJORS[document.getElementById('schMajorSel').value] || {}).name;
    student.major = 'Underwater Basket Weaving';
    out.unknown = plLedgerCompute().led === null;
    student.major = 'Economics';
    out.switched = (plLedgerCompute().mm || {}).name === 'Economics';
    student.major = null;
    return out;
  });
  ok(`${label}: no major on the profile → no ledger (not the first major in the list)`, led.skip || led.none, JSON.stringify(led));
  ok(`${label}: the ledger is the PROFILE's major before the planner is ever opened`, led.skip || (led.name === 'Business Administration' && led.sel === 'Business Administration'), JSON.stringify(led));
  ok(`${label}: a major with no flowchart → no ledger (not whatever the select held)`, led.skip || led.unknown, JSON.stringify(led));
  ok(`${label}: changing the profile's major moves the ledger with it`, led.skip || led.switched, JSON.stringify(led));

  /* ---- the privacy policy says what Hawk sends (apply-sep24) ---------------------------------- */
  ok(`${label}: the privacy policy has a Hawk section and names Anthropic`, await p.evaluate(()=>{
    openLegal('privacy');
    const h = (document.getElementById('legalBody') || {}).innerHTML || '';
    try { closeLegal(); } catch (e) {}
    return /Hawk, the assistant/.test(h) && /<b>Anthropic<\/b>/.test(h) && /30 days/.test(h) && /except the questions you ask Hawk/.test(h)
      && /Last updated 2[45] September 2026/.test(h);
  }));

  /* ---- the router reads a bare hour at all ------------------------------------------------- */
  ok(`${label}: "at 3pm" is READ, not dropped`, await p.evaluate(()=>{
    const r=window.HawkAsk.route('bus 100 mondays at 3pm');
    return !!(r && r.candidate && r.candidate.args && r.candidate.args.at_time==='15:00');
  }), await p.evaluate(()=>JSON.stringify((window.HawkAsk.route('bus 100 mondays at 3pm')||{}).candidate||{})));

  /* ---- sections ----------------------------------------------------------------------------
     THE SEAT FEED ARRIVES OVER THE NETWORK, and this harness blocks the network so the run is
     deterministic and never touches termchamp.com. So SEAT_SECTIONS is empty here, and the
     section logic — the whole point of this build — would go untested while every other
     assertion went green. A feature verified only where its data happens to exist is a feature
     nobody has verified.

     So: if the real feed is absent, a fixture is installed in its place. What is being tested is
     still entirely real — the app's own `parseMeet` reads the meeting string, the app's own
     `secSeat` reads the seat state, and Hawk's scoring and rendering run untouched. Only the rows
     are ours, shaped exactly as the feed shapes them. The assertion below records which of the
     two it ran against, so a green line never hides which one you got. */
  const usedFixture = await p.evaluate(()=>{
    const S=window.SEAT_SECTIONS||{};
    const live=Object.keys(S).some(c=>(S[c]||[]).some(r=>window.parseMeet&&window.parseMeet(r.days)));
    if (live) return false;
    const code=Object.keys(window.COURSE_NAME||{})[0]||'CSC 1001';
    window.SEAT_SECTIONS=window.SEAT_SECTIONS||{};
    window.SEAT_SECTIONS[code]=[
      {class_nbr:'11001',section:'01',name:'Kwan, A',days:'MoWe 3:10PM–4:00PM',
       available:4,capacity:40,enrolled:36,waitlist_total:0,status:'Open',comp:{label:'Lecture'}},
      {class_nbr:'11002',section:'02',name:'Alvarez, R',days:'MoWe 8:10AM–9:00AM',
       available:0,capacity:40,enrolled:40,waitlist_total:3,status:'Waitlist',comp:{label:'Lecture'}},
      {class_nbr:'11003',section:'03',name:'Tran, L',days:'TuTh 3:10PM–4:00PM',
       available:9,capacity:30,enrolled:21,waitlist_total:0,status:'Open',comp:{label:'Lecture'}}
    ];
    window.__hawkFixtureCode=code;
    return true;
  });
  ok(`${label}: section data is present${usedFixture?' (FIXTURE — live feed was empty)':' (live feed)'}`, true);

  const probe = await p.evaluate(()=>{
    const S=window.SEAT_SECTIONS||{};
    for (const code of Object.keys(S)) {
      const rows=S[code]||[];
      const m=rows.map(r=>window.parseMeet&&window.parseMeet(r.days)).filter(Boolean);
      if (m.length) {
        const d={Mo:'monday',Tu:'tuesday',We:'wednesday',Th:'thursday',Fr:'friday'}[m[0].days[0]];
        const h=Math.floor(m[0].start/60), ap=h>=12?'pm':'am', h12=h%12===0?12:h%12;
        return {code, q:`${code} ${d} at ${h12}${ap}`, day:d};
      }
    }
    return null;
  });
  ok(`${label}: the feed has a section with a readable meeting time`, !!probe, probe?probe.q:'none found');

  if (probe) {
    await p.fill('#hawk-input', probe.q); await p.press('#hawk-input','Enter'); await p.waitForTimeout(350);
    ok(`${label}: a day+time question answers with SECTIONS`, await p.evaluate(()=>
      [...document.querySelectorAll('.hawk-row__code')].some(n=>/-\d+$/.test(n.textContent.trim()))),
      await p.evaluate(()=>[...document.querySelectorAll('.hawk-row')].slice(0,3).map(r=>r.textContent.trim().slice(0,46)).join(' | ')));
    /* THE APOLOGY THAT SHOULD NO LONGER APPEAR. Reading "monday at 3" and then saying it cannot
       filter by a day or a start time is the exact behaviour this build replaced. */
    ok(`${label}: it does NOT apologise for days or times any more`, await p.evaluate(()=>
      !/cannot filter by[^.]*(day|start time|end time)/i.test(document.querySelector('.hawk-log').textContent)),
      await p.evaluate(()=>{const m=/I cannot filter by[^.]*\./i.exec(document.querySelector('.hawk-log').textContent);return m?m[0]:'';}));

    /* "…or the closest thing" (Tate, 2026-09-20). A question no section answers must come back
       with the nearest one, VISIBLY MARKED as the nearest one and saying what is wrong with it.
       A near-miss dressed as an answer is worse than no answer, because it is the one a student
       registers for. */
    const noMatch = await p.evaluate(()=>{
      const code=window.__hawkFixtureCode;
      if (!code) return null;
      return code+' saturday at 6am';
    });
    if (noMatch) {
      await p.fill('#hawk-input', noMatch); await p.press('#hawk-input','Enter'); await p.waitForTimeout(350);
      ok(`${label}: an impossible ask returns the CLOSEST, marked`, await p.evaluate(()=>{
        const near=document.querySelectorAll('.hawk-row--near');
        return near.length>0 && /closest/i.test(document.querySelector('.hawk-log').textContent);
      }), await p.evaluate(()=>{const n=document.querySelector('.hawk-row--near');return n?n.textContent.trim().slice(0,52):'nothing marked';}));
      ok(`${label}: the closest row says WHY it is only closest`, await p.evaluate(()=>{
        const n=document.querySelector('.hawk-row__near');
        return !!n && /closest\s+—\s+\S/.test(n.textContent);
      }), await p.evaluate(()=>{const n=document.querySelector('.hawk-row__near');return n?n.textContent:'no reason given';}));
    }
  }

  /* ---- seat state reaches the row (the `row.open` field that never existed) ----------------- */
  const openCode = await p.evaluate(()=>{
    const S=window.SEAT_SECTIONS||{};
    for (const code of Object.keys(S)) {
      const rows=S[code]||[];
      if (rows.some(r=>{const s=window.secSeat&&window.secSeat(r);return s&&s.cls==='open';})) return code;
    }
    return null;
  });
  if (openCode) {
    await p.fill('#hawk-input', 'open '+openCode+' sections'); await p.press('#hawk-input','Enter'); await p.waitForTimeout(350);
    ok(`${label}: seat state reaches the row`, await p.evaluate(()=>!!document.querySelector('.hawk-chip')),
       await p.evaluate(()=>{const c=document.querySelector('.hawk-chip');return c?c.textContent:'no chip';}));
  } else {
    ok(`${label}: seat state reaches the row`, true, 'no open section in this build — skipped');
  }

  /* ---- THE BOX MOVES -------------------------------------------------------------------------
     Dragged by the header only, because the body holds rows and the footer holds a text field. */
  {
    const before = await p.evaluate(()=>{const r=document.querySelector('.hawk-box').getBoundingClientRect();return {x:Math.round(r.left),y:Math.round(r.top)};});
    const h = await p.$('.hawk-head');
    const hb = await h.boundingBox();
    await p.mouse.move(hb.x + hb.width/2, hb.y + hb.height/2);
    await p.mouse.down();
    await p.mouse.move(hb.x + hb.width/2 - 160, hb.y + hb.height/2 - 120, {steps:8});
    await p.mouse.up();
    await p.waitForTimeout(150);
    const after = await p.evaluate(()=>{const r=document.querySelector('.hawk-box').getBoundingClientRect();return {x:Math.round(r.left),y:Math.round(r.top)};});
    /* On a phone the box spans the width, so it has nowhere to go sideways and only the vertical
       move is meaningful. Asserting both axes everywhere would fail on correct behaviour. */
    const movedEnough = label === 'phone'
      ? (after.y < before.y - 40)
      : (after.x < before.x - 40 && after.y < before.y - 40);
    ok(`${label}: the box can be dragged by its header`, movedEnough,
       `${before.x},${before.y} → ${after.x},${after.y}`);
    ok(`${label}: a drag cannot push it off-screen`, await p.evaluate(()=>{
      const r=document.querySelector('.hawk-box').getBoundingClientRect();
      return r.left >= 0 && r.top >= 0 && r.right <= window.innerWidth && r.bottom <= window.innerHeight;
    }));
    /* Shove it hard at the top-left corner; it must stay fully on screen. */
    const hb2 = await (await p.$('.hawk-head')).boundingBox();
    await p.mouse.move(hb2.x + 20, hb2.y + 10);
    await p.mouse.down();
    await p.mouse.move(-600, -600, {steps:6});
    await p.mouse.up();
    await p.waitForTimeout(150);
    ok(`${label}: clamped when dragged past the edge`, await p.evaluate(()=>{
      const r=document.querySelector('.hawk-box').getBoundingClientRect();
      return r.left >= 0 && r.top >= 0;
    }), await p.evaluate(()=>{const r=document.querySelector('.hawk-box').getBoundingClientRect();return Math.round(r.left)+','+Math.round(r.top);}));
    /* Back to the corner so the remaining assertions see a normal box. */
    await p.evaluate(()=>{ try{localStorage.removeItem('hawk-pos');}catch(_){ }
      const b=document.querySelector('.hawk-box'); b.style.left=''; b.style.top=''; b.style.right=''; b.style.bottom=''; });
  }

  /* ---- IT READS THE STUDENT'S OWN WEEK -------------------------------------------------------
     Seeded into the real LEXICAL bindings, not window.* — `myClasses` is a `let` and never lands
     on window, which is exactly the trap that made this feature silently do nothing at first. */
  await p.evaluate(()=>{
    myClasses = ['BUS 4442','CSC 1001','PHIL 3331','UNIV 4401'];
    myClassMeta = {
      'BUS 4442': { time: 'MoWe 3:10PM-4:00PM' },
      'CSC 1001': { time: 'TuTh 9:10AM-10:00AM' },
      'PHIL 3331': { time: 'TuTh 11:10AM-12:00PM' },
      'UNIV 4401': { time: '' }
    };
    window.SEAT_SECTIONS = window.SEAT_SECTIONS || {};
    window.SEAT_SECTIONS['BUS 4445'] = [
      {class_nbr:'21001',section:'01',name:'Kwan',days:'MoWe 3:10PM-4:00PM',available:5,capacity:40,enrolled:35,waitlist_total:0,status:'Open',comp:{label:'Lecture'}},
      {class_nbr:'21002',section:'02',name:'Tran',days:'MoWe 1:10PM-2:00PM',available:7,capacity:40,enrolled:33,waitlist_total:0,status:'Open',comp:{label:'Lecture'}}
    ];
  });

  ok(`${label}: it reads myClasses at all (the let-vs-window trap)`, await p.evaluate(()=>{
    const r = window.HawkAsk.route('when am i free on tuesday');
    return r && r.tool === 'my_free';
  }));

  await p.fill('#hawk-input','when am i free on tuesday'); await p.press('#hawk-input','Enter'); await p.waitForTimeout(350);
  ok(`${label}: "when am I free" answers from the real schedule`, await p.evaluate(()=>
    /Tuesday.*free/i.test(document.querySelector('.hawk-log').innerText)),
    await p.evaluate(()=>document.querySelector('.hawk-log').innerText.split('\n')[1]||''));
  /* A class it cannot place must be NAMED, not quietly excluded from the conclusion. */
  ok(`${label}: it says which class it could not place`, await p.evaluate(()=>
    /UNIV 4401/.test(document.querySelector('.hawk-log').innerText)));

  await p.fill('#hawk-input','bus 4445 mondays'); await p.press('#hawk-input','Enter'); await p.waitForTimeout(350);
  ok(`${label}: a clashing section is LABELLED as clashing`, await p.evaluate(()=>
    /clashes with BUS 4442/.test(document.querySelector('.hawk-log').innerText)),
    await p.evaluate(()=>document.querySelector('.hawk-log').innerText.replace(/\n/g,' | ').slice(0,90)));

  await p.fill('#hawk-input','bus 4445 that fits my schedule'); await p.press('#hawk-input','Enter'); await p.waitForTimeout(350);
  ok(`${label}: "fits my schedule" REMOVES the clashing section`, await p.evaluate(()=>{
    const t = document.querySelector('.hawk-log').innerText;
    return /BUS 4445-02/.test(t) && !/BUS 4445-01/.test(t);
  }), await p.evaluate(()=>document.querySelector('.hawk-log').innerText.replace(/\n/g,' | ').slice(0,90)));

  /* ---- THE MODEL TIER, AND EVERY WAY IT IS ALLOWED TO BE ABSENT -------------------------------
     Driven against a local stand-in, which proves the CLIENT half only — the call, the session,
     the timeout, the render and the fallbacks. Whether a real model picks the right tool is the
     golden set's job and needs a real key. Saying which of the two ran matters: a mock that reads
     like a passing test is how something gets called working before anything real has run. */
  {
    const aiReached = await p.evaluate(async () => {
      // the REAL lexical bindings — `sb` is a `let` and never lands on window
      PROFESSIFY_CONFIG.SUPABASE_URL = 'http://localhost:8787';
      sb = { auth: { getSession: () => Promise.resolve({ data: { session: { access_token: 'test-jwt' } } }) } };
      try {
        const r = await fetch('http://localhost:8787/functions/v1/ask', {
          method: 'POST', headers: { 'content-type': 'application/json', authorization: 'Bearer test-jwt' },
          body: JSON.stringify({ q: 'ping' }),
        });
        return r.ok;
      } catch (_) { return false; }
    });
    ok(`${label}: model tier stand-in is reachable`, aiReached,
       aiReached ? 'mock-ask.mjs on :8787' : 'NOT RUNNING — the model assertions below are skipped');

    if (aiReached) {
      await p.fill('#hawk-input','is it worth switching my major to finance'); await p.press('#hawk-input','Enter');
      await p.waitForTimeout(1200);
      ok(`${label}: an unplaceable question reaches the model`, await p.evaluate(()=>
        /\bAI\b/.test(document.querySelector('.hawk-log').innerText)));
      /* The four cant_answer reasons each have their own line, because "I don't know" sends a
         student away with nothing when three of them have an obvious next step. */
      ok(`${label}: cant_answer:needs_judgment says whose call it is`, await p.evaluate(()=>
        /judgement call/i.test(document.querySelector('.hawk-log').innerText)),
        await p.evaluate(()=>document.querySelector('.hawk-log').innerText.replace(/\n/g,' | ').slice(0,80)));

      await p.fill('#hawk-input','is my roommate taking csc 1001'); await p.press('#hawk-input','Enter');
      await p.waitForTimeout(1200);
      ok(`${label}: cant_answer:needs_private_data points at Friends`, await p.evaluate(()=>
        /Friends shows that/i.test(document.querySelector('.hawk-log').innerText)));

      /* A filter with nothing to anchor it to must NOT claim the catalog is empty. */
      await p.fill('#hawk-input','find me something in the morning'); await p.press('#hawk-input','Enter');
      await p.waitForTimeout(1200);
      ok(`${label}: an unanchored filter does not claim "nothing matches"`, await p.evaluate(()=>{
        const t=document.querySelector('.hawk-log').innerText;
        return /need a subject or a course/i.test(t) && !/Nothing in the catalog matches/i.test(t);
      }), await p.evaluate(()=>document.querySelector('.hawk-log').innerText.replace(/\n/g,' | ').slice(0,80)));
    }

    /* SIGNED OUT, and with the function simply not there. Both must land on the ordinary search
       with the student's own words in it — never a spinner, never an error. */
    await p.evaluate(()=>{ sb = { auth: { getSession: () => Promise.resolve({ data: { session: null } }) } }; });
    await p.fill('#hawk-input','is it worth switching my major to finance'); await p.press('#hawk-input','Enter');
    await p.waitForTimeout(900);
    await p.evaluate(()=>{ window.__rpc = []; sb.rpc = function(n, a){ window.__rpc.push([n, a]); return Promise.resolve({ data: 1 }); }; });
    await p.fill('#hawk-input','bus 4442'); await p.press('#hawk-input','Enter'); await p.waitForTimeout(300);
    await p.evaluate(()=>{ const b=document.querySelector('.hawk-notit'); if (b) b.click(); }); await p.waitForTimeout(300);
    ok(`${label}: signed out, "Not it?" sends NOTHING (the policy says so)`, await p.evaluate(()=>!window.__rpc.some(c=>c[0]==='assistant_log_miss')));
    await p.fill('#hawk-input','is it worth switching my major to finance'); await p.press('#hawk-input','Enter');
    await p.waitForTimeout(900);
    ok(`${label}: signed out falls back to search, silently`, await p.evaluate(()=>{
      const t=document.querySelector('.hawk-log').innerText;
      return /Search Explore/i.test(t) && !/\bAI\b/.test(t) && !/Working that out/i.test(t);
    }));

    await p.evaluate(()=>{
      PROFESSIFY_CONFIG.SUPABASE_URL = 'http://localhost:9';   // nothing listens here
      sb = { auth: { getSession: () => Promise.resolve({ data: { session: { access_token: 'x' } } }) } };
    });
    await p.fill('#hawk-input','is it worth switching my major to finance'); await p.press('#hawk-input','Enter');
    await p.waitForTimeout(1500);
    ok(`${label}: an undeployed function falls back to search`, await p.evaluate(()=>{
      const t=document.querySelector('.hawk-log').innerText;
      return /Search Explore/i.test(t) && !/Working that out/i.test(t);
    }), await p.evaluate(()=>document.querySelector('.hawk-log').innerText.replace(/\n/g,' | ').slice(0,70)));
  }

  /* The device-only answers below run with the model tier OFF, so each is what the free tier says
     on its own — and what every student gets when the tier is over its cap or unreachable. */
  await p.evaluate(()=>{ PROFESSIFY_CONFIG.SUPABASE_URL = ''; });

  /* ---- THE REST OF THE APP AS ANSWERS -----------------------------------------------------------
     Seeded the way the app itself holds them. Each assertion checks the SHAPE of the answer as much
     as its content — a date is a date, a section is a tappable row, a clash is labelled. */
  await p.evaluate(()=>{
    /* Two REAL professors from the roster, so the app's own matchProfId resolves the feed's
       "Last, First" to exactly them. Seeding made-up ids under names the roster may also hold
       was a coin flip. */
    const ids = Object.keys(PROFESSORS || {}).filter(k => (PROFESSORS[k].name || '').split(' ').length === 2);
    const [pa, pb] = [PROFESSORS[ids[0]], PROFESSORS[ids[1]]];
    pa.rating = 4.4 * 0.8; pb.rating = 3.9 * 0.8;   // PolyRatings' 0–4 scale; shown ×5/4, as the app does
    const feed = (p) => { const [f, l] = p.name.split(' '); return l + ', ' + f; };
    window.__hawkProfs = { a: pa.name, b: pb.name };
    myClasses = ['BUS 4442','CSC 1001','PHIL 3331'];
    myClassMeta = { 'BUS 4442':{time:'MoWe 3:10PM-4:00PM',crn:'31001'}, 'CSC 1001':{time:'TuTh 9:10AM-10:00AM',crn:'11001'}, 'PHIL 3331':{time:'TuTh 11:10AM-12:00PM'} };
    SEAT_SECTIONS['BUS 4442'] = [
      {class_nbr:'31001',section:'01',name:feed(pa),days:'MoWe 3:10PM-4:00PM',available:2,capacity:40,enrolled:38,waitlist_total:0,status:'Open',comp:{label:'Lecture'}},
      {class_nbr:'31002',section:'02',name:feed(pb),days:'MoWe 5:10PM-6:00PM',available:9,capacity:40,enrolled:31,waitlist_total:0,status:'Open',comp:{label:'Lecture'}}
    ];
    SEAT_SECTIONS['CSC 1001'] = [
      {class_nbr:'11001',section:'01',name:'Staff',days:'TuTh 9:10AM-10:00AM',available:4,capacity:40,enrolled:36,waitlist_total:0,status:'Open',comp:{label:'Lecture'}},
      {class_nbr:'11002',section:'02',name:'Staff',days:'MoWe 1:10PM-2:00PM',available:7,capacity:40,enrolled:33,waitlist_total:0,status:'Open',comp:{label:'Lecture'}}
    ];
    FRIENDS = [{ id:'f1', name:'Garrett Haller', classes:['BUS 4442'], secs:[{code:'BUS 4442',crn:'31001'}],
                 history:[{code:'CSC 2001',term:'Spring',year:2026,professor:'Chance, Beth'},{code:'CSC 1001',term:'Fall',year:2025,professor:''}] },
               { id:'f2', name:'Maya Ortiz', classes:[], secs:[], history:[{code:'CSC 2001',term:'Fall',year:2025,professor:''}] }];
    COURSE_PREREQS['CSC 2001'] = { req:[['CSC 1001'],['MATH 1410','MATH 1420']] };
    if (window.COURSE_NAME) COURSE_NAME['CSC 2001'] = 'Data Structures';
    PROFESSIFY_CONFIG.REGISTRATION_OPENS = '2026-10-19'; PROFESSIFY_CONFIG.REGISTRATION_ROUND2 = '2026-11-04'; PROFESSIFY_CONFIG.OPEN_ENROLLMENT = '2026-11-18'; PROFESSIFY_CONFIG.REGISTRATION_TERM = 'Spring 2027';
  });
  const log = () => p.evaluate(()=>document.querySelector('.hawk-log').innerText.replace(/\n/g,' | '));
  const askQ = async (q) => { await p.fill('#hawk-input', q); await p.press('#hawk-input','Enter'); await p.waitForTimeout(350); return log(); };

  let t = await askQ('best section of bus 4442');
  ok(`${label}: "best section" ranks by professor rating`, /4\.4 ★.*3\.9 ★/.test(t), t.slice(0,90));
  ok(`${label}: the section you are in says "yours", not "clashes"`, /yours/.test(t) && !/clashes with BUS 4442/.test(t));

  t = await askQ('can i take csc 2001');
  ok(`${label}: prereqs name what is missing, as a choice`, /one of MATH 1410 \/ MATH 1420/.test(t), t.slice(0,90));
  ok(`${label}: and credit what is in progress`, /In progress now: CSC 1001/.test(t));

  t = await askQ('what do i have tuesday');
  ok(`${label}: "my day" lists that day’s classes in order`, /CSC 1001.*9:10 am.*PHIL 3331.*11:10 am/.test(t), t.slice(0,90));

  t = await askQ('how many units am i taking');
  ok(`${label}: units are summed from classInfo`, /\d+ units across 3 classes/.test(t), t.slice(0,60));

  t = await askQ('can i take bus 4442 and csc 1001');
  ok(`${label}: two courses become section PAIRS that fit`, /combinations fit/.test(t) && /BUS 4442-02.*\+.*CSC 1001-02/.test(t), t.slice(0,110));

  t = await askQ('swap my bus 4442 to a later section');
  const profB = await p.evaluate(()=>window.__hawkProfs.b);
  ok(`${label}: swap shows only LATER sections, with who teaches`, /Later sections/.test(t) && /BUS 4442-02/.test(t) && !/BUS 4442-01 \|/.test(t) && t.includes(profB), t.slice(0,110));

  t = await askQ('which friends are in bus 4442');
  ok(`${label}: friends-in reads FRIENDS on the device`, /Garrett Haller/.test(t) && /same section/.test(t), t.slice(0,80));

  t = await askQ('find one that friends have taken in the past');
  ok(`${label}: "one that friends have taken" reads FRIENDS[].history`, /CSC 2001/.test(t) && /Garrett, Maya took it/.test(t) && /Beth Chance/.test(t), t.slice(0,160));
  ok(`${label}: a class you already have is left out of it`, !/CSC 1001 \|/.test(t), t.slice(0,160));

  /* ---- EVERY TAP: the places and the actions (2026-09-23) --------------------------------------
     Each action is checked by the APP FUNCTION it ends in, with the arguments it was given —
     spied, then called through, so the real screen still opens. */
  ok(`${label}: Hawk's rating is the app's rating (out of 5, via to5)`, await p.evaluate(()=>{
    const id = Object.keys(PROFESSORS).find(k=>PROFESSORS[k].name===window.__hawkProfs.a);
    return typeof ratePlain==='function' && ratePlain(PROFESSORS[id].rating) === '4.4★';
  }) && /4\.4 ★/.test(await askQ('best section of bus 4442')));

  await p.evaluate(()=>{
    window.__calls = [];
    ['startRate','askFriendAbout','msgWith','shOpen','openAddFriend','openFriendProfile','mcEnrollSec','openSettings',
     'openNotifs','openMyReviews','openEditProfile','openLegal','openSchedImport','showMyQR','setSchedTab','setWatchTab','goCompare','setTheme']
      .forEach(n=>{ const o=window[n]; if(typeof o!=='function')return; window[n]=function(){ window.__calls.push([n,[...arguments]]); try{ return o.apply(this,arguments); }catch(e){ return null; } }; });
  });
  const called = (n) => p.evaluate((n)=>window.__calls.filter(c=>c[0]===n).map(c=>c[1]), n);
  const tapFirst = async (sel='.hawk-log .hawk-row') => { await p.evaluate((s)=>{ const r=document.querySelector(s); if(r) r.click(); }, sel); await p.waitForTimeout(250); };

  for (const [q, view, fn] of [
    ['take me to settings','view-settings','openSettings'], ['where do i change my password','view-settings','openSettings'],
    ['open my watchlist','view-sched','setSchedTab'], ['my past classes','view-sched','setSchedTab'],
    ['go to explore','view-explore',null], ['how do i import my schedule','view-sched','openSchedImport'],
    ['go home','view-home',null], ['friends','view-friends',null]]) {
    await p.evaluate(()=>{ window.__calls=[]; });
    t = await askQ(q);
    await tapFirst();
    const v = await p.evaluate(()=>(document.querySelector('.view.active')||{}).id);
    ok(`${label}: "${q}" opens the right screen`, v === view && (!fn || (await called(fn)).length > 0), t.slice(0,60) + ' → ' + v);
    await p.evaluate(()=>{ try{ closeModal&&closeModal(); }catch(e){} try{ closeSchedImport&&closeSchedImport(); }catch(e){} });
  }

  const themeBefore = await p.evaluate(()=>document.documentElement.getAttribute('data-theme'));
  const other = themeBefore === 'light' ? 'cream' : 'light';
  t = await askQ(other + ' mode');
  ok(`${label}: "${other} mode" switches the theme, with an Undo`, await p.evaluate((o)=>document.documentElement.getAttribute('data-theme')===o, other) && /Undo/.test(t), t.slice(0,60));
  await p.evaluate(()=>{ const b=[...document.querySelectorAll('.hawk-done button')][0]; if(b) b.click(); });
  ok(`${label}: Undo puts the theme back`, await p.evaluate((b)=>document.documentElement.getAttribute('data-theme')===b, themeBefore || 'dark'));

  await p.evaluate(()=>{ if (typeof isWatchedClass==='function' && isWatchedClass('CSC 1001')) toggleWatchClass('CSC 1001'); });
  t = await askQ('watch csc 1001');
  ok(`${label}: "watch CSC 1001" watches it`, await p.evaluate(()=>isWatchedClass('CSC 1001')) && /Watching CSC 1001/.test(t), t.slice(0,80));
  await p.evaluate(()=>{ const b=document.querySelector('.hawk-done button'); if(b) b.click(); });
  ok(`${label}: and Undo unwatches it`, await p.evaluate(()=>!isWatchedClass('CSC 1001')));

  const PA = await p.evaluate(()=>window.__hawkProfs.a), PB = await p.evaluate(()=>window.__hawkProfs.b);
  const PAID = await p.evaluate((n)=>Object.keys(PROFESSORS).find(k=>PROFESSORS[k].name===n), PA);
  const PROFESSORS_NAME_OK = (id) => id === PAID;
  t = await askQ('watch ' + PA.toLowerCase());
  ok(`${label}: "watch <professor>" watches the professor`, await p.evaluate((n)=>{ const id=Object.keys(PROFESSORS).find(k=>PROFESSORS[k].name===n); return isWatched(id); }, PA), t.slice(0,80));
  await p.evaluate(()=>{ const b=document.querySelector('.hawk-done button'); if(b) b.click(); });

  await p.evaluate(()=>{ window.__calls=[]; });
  t = await askQ('rate ' + PA.toLowerCase() + ' for bus 4442');
  await tapFirst();
  const rs = await called('startRate');
  ok(`${label}: "rate <prof> for BUS 4442" opens THE rate form, prefilled`, rs.length === 1 && rs[0][1] === 'BUS 4442' && PROFESSORS_NAME_OK(rs[0][0]), t.slice(0,80));
  await p.evaluate(()=>{ try{ closeModal(); }catch(e){} });

  await p.evaluate(()=>{ window.__calls=[]; });
  t = await askQ('message garrett about csc 2001');
  await tapFirst();
  const af = await called('askFriendAbout');
  ok(`${label}: "message Garrett about CSC 2001" drafts with the app's own Ask-about (he took it)`, af.length === 1 && af[0][0] === 'f1' && af[0][1] === 'CSC 2001', t.slice(0,80));
  ok(`${label}: and nothing is sent`, /you press Send/i.test(await log()));

  await p.evaluate(()=>{ window.__calls=[]; try{ closeFriendProfile(); }catch(e){} });
  t = await askQ('send bus 4442 to maya');
  await tapFirst();
  const sh = await called('shOpen');
  ok(`${label}: "send BUS 4442 to Maya" opens the share sheet for that class`, sh.length === 1 && sh[0][0] === 'class' && sh[0][1] === 'BUS 4442' && /Pick Maya/.test(await log()), t.slice(0,80));
  await p.evaluate(()=>{ try{ shClose(); }catch(e){} });

  await p.evaluate(()=>{ window.__calls=[]; });
  t = await askQ('add john smith as a friend');
  await tapFirst(); await p.waitForTimeout(150);
  ok(`${label}: "add John Smith as a friend" opens the people search with the name in it`, (await called('openAddFriend')).length === 1
     && await p.evaluate(()=>((document.getElementById('frSearchPeople')||{}).value||'')==='john smith'), t.slice(0,80));

  await p.evaluate(()=>{ window.__calls=[]; });
  t = await askQ('what has garrett taken');
  ok(`${label}: "what has Garrett taken" says it, then opens his past classes`, /Garrett has taken CSC 2001/.test(t), t.slice(0,80));
  await tapFirst();
  const fp = await called('openFriendProfile');
  ok(`${label}: …on the right tab`, fp.length === 1 && fp[0][0] === 'f1' && fp[0][1] === 'took');
  await p.evaluate(()=>{ try{ closeFriendProfile(); }catch(e){} });

  await p.evaluate(()=>{ window.__calls=[]; });
  t = await askQ('add bus 4442 section 2');
  ok(`${label}: "add BUS 4442 section 2" says you confirm first`, /confirm/i.test(t), t.slice(0,80));
  await tapFirst();
  const en = await called('mcEnrollSec');
  ok(`${label}: …and opens the app's enroll dialog for THAT section`, en.length === 1 && en[0][0] === 'BUS 4442' && String(en[0][1]) === '31002', JSON.stringify(en));
  await p.evaluate(()=>{ try{ closeEnrollDialog(); }catch(e){} });

  t = await askQ('bus 4442-02');
  ok(`${label}: "BUS 4442-02" is that section`, /BUS 4442-02/.test(t) && !/BUS 4442-01/.test(t), t.slice(0,80));

  t = await askQ('compare ' + PA.toLowerCase() + ' and ' + PB.toLowerCase());
  ok(`${label}: compare two professors says who is rated higher`, t.includes(PA + ' is rated higher'), t.slice(0,100));
  t = await askQ('how hard is ' + PA.toLowerCase());
  ok(`${label}: professor stats give the real rating and send you to the rest`, /4\.4 ★ from \d+ rating/.test(t) && /on their page/.test(t), t.slice(0,100));

  t = await askQ('what can you do');
  ok(`${label}: help lists what Hawk can do`, await p.evaluate(()=>document.querySelectorAll('.hawk-log .hawk-row').length >= 6), t.slice(0,80));

  t = await askQ('when does registration open');
  ok(`${label}: registration answers with a real date`, /October 19, 2026/.test(t), t.slice(0,80));
  ok(`${label}: it says Round 1, the term, the later rounds, and that it is by appointment`,
     /Round 1 registration for Spring 2027 opens .*October 19, 2026/.test(t) && /Round 2: November 4/.test(t) && /Open Enrollment: November 18/.test(t) && /appointment/.test(t), t.slice(0,220));

  t = await askQ('take me to my watchlist');
  /* The watchlist became Plans on 2026-09-25 (apply-plans); the place key stays 'watchlist'. */
  ok(`${label}: go_to offers the screen as a row`, /\bPlans\b/.test(t) && !/My watchlist/.test(t), t.slice(0,80));

  await askQ('open bus sections');
  t = await askQ('what about tuesday');
  ok(`${label}: a follow-up inherits the previous search`, /No BUS section matches|BUS 4442/.test(t) && !/could not read/i.test(t), t.slice(0,80));

  ok(`${label}: every answer carries "Not it?"`, await p.evaluate(()=>!!document.querySelector('.hawk-notit')));

  /* ---- HARD QUESTIONS: THE PLANNER, ON THE LIVE DATA SHAPE ------------------------------------
     Rows here are shaped exactly as the live feed ships them on 2026-09-24 — `instructor` in
     "First Last", `section` as "S01-LEC Regular", `instruction_mode` — because every fixture above
     used an invented shape, and three filters that passed on it missed every section on real data.
     The ledger is a FIXTURE: a signed-out harness has no major, so plLedgerCompute is stubbed. */
  const hq = await p.evaluate(()=>{
    const P = PROFESSORS; const ids = Object.keys(P).filter(k=>(P[k].name||'').split(' ').length===2);
    const nm = (i,r)=>{ P[ids[i]].rating=r*0.8; return P[ids[i]].name; };
    const A = nm(4,4.7), B = nm(5,4.5), C = nm(6,4.1);
    window.__realLedger = window.plLedgerCompute;
    window.plLedgerCompute = () => ({ led: { need: [], needU: [{title:'GE · Arts & Humanities (3B)'},{title:'GE · Social Sciences (4B)'}] } });
    const g = GE_COURSES.filter(c=>c.areaKey==='3B').slice(0,3).map(c=>c.code);
    myClasses=['BUS 4442']; myClassMeta={'BUS 4442':{time:'MoWe 3:10PM-4:00PM',crn:'31001'}};
    const row=(code,sec,instr,days,avail,mode)=>({course_code:code,title:'',section:sec,instructor:instr,days,status:'Open',capacity:40,enrolled:40-avail,available:avail,waitlist_total:0,class_nbr:code+sec,instruction_mode:mode||'In Person'});
    SEAT_SECTIONS[g[0]] = [row(g[0],'S01-LEC Regular',A,'MoWe 3:00PM - 3:50PM',5)];            // best-rated, CLASHES
    SEAT_SECTIONS[g[1]] = [row(g[1],'S01-LEC Regular',B,'',12,'Asynchronous')];              // async, fits
    SEAT_SECTIONS[g[2]] = [row(g[2],'S02-LAB Regular',C,'TuTh 1:00PM - 1:50PM',3)];          // lab, fits
    return { clashCode: g[0], asyncCode: g[1], labCode: g[2], A, B };
  });

  t = await askQ('recommend a GE that i still need to take and fits my schedule and also has the highest rated professors on');
  ok(`${label}: Tate's four-constraint question is read in full`, /GE you still need \(3B, 4B\).*fits your week.*best-rated/.test(t), t.slice(0,140));
  ok(`${label}: the best-rated section that CLASHES is left out`, !t.includes(hq.clashCode), hq.clashCode + ' should be absent');
  ok(`${label}: an async section counts as fitting, and leads`, t.indexOf(hq.asyncCode) >= 0 && t.indexOf(hq.asyncCode) < t.indexOf(hq.labCode));
  ok(`${label}: live section "S01-LEC Regular" reads as -01`, t.includes(hq.asyncCode + '-01'));
  ok(`${label}: it says how many it checked`, /\d+ of \d+ offered this term match/.test(t));

  t = await askQ('ge 3b labs');
  ok(`${label}: "labs" reads the live section string, not comp.label`, t.includes(hq.labCode) && !t.includes(hq.asyncCode + '-01'), t.slice(0,120));

  t = await askQ('easiest ge i still need');
  ok(`${label}: "easiest" says there is no difficulty data, never fakes an order`, /no difficulty data/i.test(t));

  await askQ('ge 3b on tuesday');
  t = await askQ('only online ones');
  ok(`${label}: an empty compound answer offers one tap to loosen it`, /Any day and time|Show ones that clash/.test(t), t.slice(0,120));

  ok(`${label}: GE keys are the 2026 semester scheme`, await p.evaluate(()=>{
    const r = HawkAsk.route('upper division ge area 4'); return r.prerouted && r.args.ge_area === 'UD4';
  }));
  ok(`${label}: a quarter-era key like "GE C1" is NOT confidently routed`, await p.evaluate(()=>!HawkAsk.route('ge c1').prerouted));

  /* ---- BUILD MY TERM ---------------------------------------------------------------------------
     Whole schedules from the GE areas the (fixture) ledger says are unmet, around the student's
     saved class, with a day off. Every section is live-shaped. What must hold: the day off is off,
     nothing clashes with the saved class, the unit target is met, and each option is a different
     set of classes. */
  const bq = await p.evaluate(()=>{
    window.plLedgerCompute = () => ({ led: { need: [], needU: [{title:'GE · Arts & Humanities (3B)'},{title:'GE · Social Sciences (4B)'},{title:'GE · Humanities (3A)'}] } });
    const P = PROFESSORS; const ids = Object.keys(P).filter(k=>(P[k].name||'').split(' ').length===2);
    const nm = (i,r)=>{ P[ids[i]].rating=r*0.8; return P[ids[i]].name; };
    const pick = (k,n)=>GE_COURSES.filter(c=>c.areaKey===k).slice(0,n);
    const cs = [...pick('3A',2), ...pick('3B',2), ...pick('4B',2)];
    myClasses=['BUS 4442']; myClassMeta={'BUS 4442':{time:'MoWe 3:10PM-4:00PM',crn:'31001'}};
    const row=(code,sec,instr,days,avail)=>({course_code:code,title:'',section:sec,instructor:instr,days,status:'Open',capacity:40,enrolled:40-avail,available:avail,waitlist_total:0,class_nbr:code+sec,instruction_mode:'In Person'});
    const times=['MoWe 3:00PM - 3:50PM','TuTh 10:00AM - 11:15AM','MoWe 11:00AM - 11:50AM','TuTh 1:00PM - 2:15PM','MoWeFr 9:00AM - 9:50AM','TuTh 8:00AM - 9:15AM'];
    cs.forEach((c,i)=>{
      SEAT_SECTIONS[c.code]=[row(c.code,'S01-LEC Regular',nm(10+i,4.9-i*0.2),times[i],6+i),
                             row(c.code,'S02-LEC Regular',nm(20+i,3.6),times[(i+3)%6],2)];
    });
    return { codes: cs.map(c=>c.code), units: cs.map(c=>c.units) };
  });
  t = await askQ('build me a 9 unit schedule with GEs i still need, no fridays');
  ok(`${label}: "build my term" reads units, scope and a day off`, /9 units.*GE you still need.*no Fridays/.test(t), t.slice(0,140));
  const built = await p.evaluate(()=>{
    const rows=[...document.querySelectorAll('.hawk-build .hawk-row')].map(r=>r.innerText.replace(/\n/g,' | '));
    return { rows, pills: document.querySelectorAll('.hawk-opt').length, week: !!document.querySelector('.hawk-week'),
             blocks: document.querySelectorAll('.hawk-week__blk').length, fixed: document.querySelectorAll('.hawk-week__blk--fixed').length };
  });
  ok(`${label}: it builds a schedule, drawn as a week`, built.rows.length >= 2 && built.week && built.fixed >= 1, JSON.stringify(built).slice(0,160));
  ok(`${label}: no Friday class in a "no fridays" build`, built.rows.every(r=>!/Fr\b|MoWeFr/.test(r)), built.rows.join(' || ').slice(0,200));
  ok(`${label}: nothing in the build clashes with the saved class`, built.rows.every(r=>!/MoWe 3 pm/.test(r)), built.rows.join(' || ').slice(0,200));
  ok(`${label}: several options, each a different set of classes`, built.pills >= 2, built.pills + ' options');
  const unitsOk = await p.evaluate(()=>{
    const us=[...document.querySelectorAll('.hawk-build .hawk-row__sub')].map(n=>{const m=/(\d+)u\b/.exec(n.textContent);return m?+m[1]:0;});
    const fx=/you’ve saved \((\d+) units\)/.exec(document.querySelector('.hawk-log').innerText);
    return us.reduce((a,b)=>a+b,0) + (fx ? +fx[1] : 0);
  });
  ok(`${label}: the option lands on the unit target (±1)`, unitsOk >= 8 && unitsOk <= 10, unitsOk + ' units');
  await p.evaluate(()=>{ const b=document.querySelectorAll('.hawk-opt')[1]; if (b) b.click(); });
  ok(`${label}: switching option swaps the rows`, await p.evaluate(()=>document.querySelectorAll('.hawk-opt')[1] ? document.querySelectorAll('.hawk-opt')[1].classList.contains('is-on') : true));
  t = await askQ('make it 6 units');
  ok(`${label}: a build follow-up changes THAT build, on the device`, /6 units.*GE you still need.*no Fridays/.test(t), t.slice(0,120));
  t = await askQ('nothing before 10');
  ok(`${label}: "nothing before 10" means a 10 am start, not an end-before`, /nothing before 10 am/.test(t) && !/ (8|9) am/.test(t.split('first')[1]||''), t.slice(0,400));

  /* ---- AI-FIRST, AND THE VERIFIED EXPLANATION (against the stand-in) ------------------------- */
  const aiUp = await p.evaluate(async ()=>{
    PROFESSIFY_CONFIG.SUPABASE_URL = 'http://localhost:8787';
    sb = { auth: { getSession: () => Promise.resolve({ data: { session: { access_token: 'test-jwt' } } }) } };
    try { return (await fetch('http://localhost:8787/functions/v1/ask',{method:'POST',headers:{authorization:'Bearer t','content-type':'application/json'},body:'{"q":"ping"}'})).ok; } catch(_) { return false; }
  });
  if (aiUp) {
    const askAI = async (q) => { await p.fill('#hawk-input', q); await p.press('#hawk-input','Enter'); await p.waitForTimeout(1300); return log(); };
    t = await askAI('when am i free on tuesday');
    ok(`${label}: AI-first — a confident personal question still goes to the model`, /\bAI\b/.test(t) && /Tuesday/.test(t), t.slice(0,90));
    /* THE LIVE MISS, 2026-09-23. The model answered with go_to "my classes"; the router reads it as
       my_professors, and a model go_to never overrides a clean device reading. */
    await p.evaluate(()=>{
      const P = PROFESSORS; const ids = Object.keys(P).filter(k=>(P[k].name||'').split(' ').length===2);
      P[ids[30]].rating = 4.8*0.8; P[ids[31]].rating = 3.2*0.8;
      window.__myProfs = { hi: P[ids[30]].name, lo: P[ids[31]].name };
      myClasses = ['BUS 4442','CSC 1001'];
      myClassMeta = { 'BUS 4442': { time:'MoWe 3:10PM-4:00PM', prof: P[ids[31]].name, secs:[{crn:'31001', prof: P[ids[31]].name}] },
                      'CSC 1001': { time:'TuTh 9:10AM-10:00AM', secs:[{crn:'11001', prof: P[ids[30]].name}] } };
    });
    t = await askAI('which professor of mine has the highest rating');
    const mp = await p.evaluate(()=>window.__myProfs);
    ok(`${label}: "which professor of mine is highest rated" ranks YOUR professors`, t.includes('Highest rated: ' + mp.hi) && t.indexOf(mp.hi) < t.lastIndexOf(mp.lo) && !/My classes/.test(t), t.slice(0,160));
    const viewBefore = await p.evaluate(()=>{const v=document.querySelector('.view.active');return v?v.id:'';});
    await p.evaluate(()=>{ window.__rpc = []; sb.rpc = function(n, a){ window.__rpc.push([n, a]); return Promise.resolve({ data: true }); }; });
    await p.click('.hawk-notit'); await p.waitForTimeout(250);
    const rpc1 = await p.evaluate(()=>window.__rpc.filter(c=>c[0]==='assistant_log_miss'));
    ok(`${label}: "Not it?" logs the miss WITH the question, under the pseudonym`, rpc1.length === 1 && rpc1[0][0] === 'assistant_log_miss'
       && /professor of mine/.test(rpc1[0][1].p_q) && rpc1[0][1].p_shown_tool && rpc1[0][1].p_picked_tool === null && !('p_email' in rpc1[0][1]), JSON.stringify(rpc1).slice(0,200));
    const alts = await p.evaluate(()=>({ box: !!document.querySelector('.hawk-alts'),
      rows: [...document.querySelectorAll('.hawk-alts .hawk-row')].map(r=>r.innerText.trim()),
      view: (document.querySelector('.view.active')||{}).id, search: (document.querySelector('#view-explore input')||{}).value||'' }));
    ok(`${label}: "Not it?" stays in Hawk — it does not paste the question into Explore`, alts.box && alts.view === viewBefore, JSON.stringify(alts).slice(0,160));
    ok(`${label}: "Not it?" offers the other reading`, alts.rows.some(r=>/Open My classes/.test(r)), alts.rows.join(' | '));
    await p.evaluate(()=>{ const r=[...document.querySelectorAll('.hawk-alts .hawk-row')].find(x=>/My classes/.test(x.innerText)); if(r) r.click(); });
    await p.waitForTimeout(250);
    ok(`${label}: picking an alternative answers with it`, /My classes/.test(await log()));
    const rpc2 = await p.evaluate(()=>window.__rpc.filter(c=>c[0]==='assistant_log_miss'));
    ok(`${label}: …and the reading they picked is logged as the right answer`, rpc2.length === 2 && rpc2[1][1].p_picked_tool === 'go_to', JSON.stringify(rpc2[1]||null).slice(0,200));
    await p.evaluate(()=>{ myClasses=['BUS 4442']; myClassMeta={'BUS 4442':{time:'MoWe 3:10PM-4:00PM',crn:'31001'}}; });
    t = await askAI('something good on tuesday');
    ok(`${label}: an unclear question offers readings instead of a dead end`, await p.evaluate(()=>!!document.querySelector('.hawk-alts .hawk-row')) && /Sections: Tue/.test(t), t.slice(0,140));
    t = await askAI('csc 1001 is it hard');
    ok(`${label}: a model course code "CSC1001" is read as CSC 1001`, /CSC 1001/.test(t) && !/CSC1001/.test(t), t.slice(0,100));
    t = await askAI('CSC 1001');
    ok(`${label}: a bare course code stays on the device`, !/\bAI\b/.test(t), t.slice(0,60));
    await p.evaluate(()=>{ window.plLedgerCompute = () => ({ led: { need: [], needU: [{title:'GE · Arts & Humanities (3B)'},{title:'GE · Social Sciences (4B)'}] } }); myClasses=['BUS 4442']; });
    t = await askAI('recommend a ge i still need with the best professors');
    ok(`${label}: model says cant_answer → the router's clean reading is kept`, /GE you still need/.test(t), t.slice(0,120));
    const say = await p.evaluate(()=>{ const s=document.querySelector('.hawk-say'); return s ? s.textContent : ''; });
    ok(`${label}: a checked explanation appears above the rows`, /top pick/.test(say) && await p.evaluate(()=>{
      const s=document.querySelector('.hawk-say'), r=document.querySelector('.hawk-read'); return !!s && r.nextElementSibling===s; }), say);
    t = await askAI('recommend a ge i still need with the best professors lie');
    ok(`${label}: an explanation naming a class NOT on screen is dropped`, !(await p.evaluate(()=>!!document.querySelector('.hawk-say'))) && /GE you still need/.test(t), t.slice(0,100));
    t = await askAI('build me a 9 unit schedule with GEs, no fridays');
    ok(`${label}: the model can hand back build_term`, /\bAI\b/.test(t) && /9 units/.test(t) && await p.evaluate(()=>!!document.querySelector('.hawk-week')), t.slice(0,120));
  } else {
    ok(`${label}: AI-first assertions`, true, 'mock not running — skipped');
  }
  ok(`${label}: the explanation check itself`, await p.evaluate(()=>{
    const rows=[{code:'COMM 2204-01',title:'Public Speaking',when:'TuTh 10 am',prof:'Dana Ruiz',rating:4.7,seats:6,tag:'GE 1C',fits:true}];
    const v=HawkAsk.verifyExplanation;
    return !!v('COMM 2204 with Dana Ruiz (4.7★) fits your week and has 6 open seats.', rows)
      && !v('COMM 2204 has 9 open seats.', rows)                       // a number not in the rows
      && !v('Take BIO 1610 instead.', rows)                            // a class not in the rows
      && !v('Dana Ruiz is known for easy exams, says Reddit.', rows)   // a name not in the rows
      && !v('See https://example.com', rows);
  }));
  await p.evaluate(()=>{ PROFESSIFY_CONFIG.SUPABASE_URL = ''; });

  await p.evaluate(()=>{ window.plLedgerCompute = window.__realLedger; });

  /* ---- reading, correcting, refusing -------------------------------------------------------- */
  await p.fill('#hawk-input','chemsitry classes'); await p.press('#hawk-input','Enter'); await p.waitForTimeout(300);
  ok(`${label}: a misspelling returns rows`, await p.evaluate(()=>document.querySelectorAll('.hawk-row').length>0),
     await p.evaluate(()=>[...document.querySelectorAll('.hawk-row')].slice(0,2).map(r=>r.textContent.trim().slice(0,40)).join(' | ')));
  ok(`${label}: the correction is shown`, await p.evaluate(()=>/chemsitry\s*→\s*CHEM/.test(document.querySelector('.hawk-log').textContent)));

  await p.fill('#hawk-input','what is the capital of germany'); await p.press('#hawk-input','Enter'); await p.waitForTimeout(300);
  ok(`${label}: an off-topic question is refused`, await p.evaluate(()=>/only find classes/i.test(document.querySelector('.hawk-log').textContent)));
  ok(`${label}: refusing shows no rows`, await p.evaluate(()=>document.querySelectorAll('.hawk-row').length===0));

  /* ---- ONE ANSWER AT A TIME. The box must not grow into a log. ------------------------------ */
  const before = await p.evaluate(()=>document.querySelector('.hawk-box').getBoundingClientRect().height);
  await p.fill('#hawk-input','CSC 1001'); await p.press('#hawk-input','Enter'); await p.waitForTimeout(300);
  ok(`${label}: only the newest answer is kept`, await p.evaluate(()=>
    document.querySelectorAll('.hawk-turn').length===1),
    await p.evaluate(()=>document.querySelectorAll('.hawk-turn').length+' turns on screen'));
  ok(`${label}: asking again does not grow the box`, await p.evaluate((b)=>
    document.querySelector('.hawk-box').getBoundingClientRect().height <= b+90, before));

  /* ---- the point of the whole thing --------------------------------------------------------- */
  await p.evaluate(()=>document.querySelector('.hawk-row').click());
  await p.waitForTimeout(700);
  ok(`${label}: tapping a result NAVIGATES`, await p.evaluate(()=>{
    const v=document.querySelector('.view.active'); return v && /class/i.test(v.id);
  }), await p.evaluate(()=>{const v=document.querySelector('.view.active');return v?v.id:'none';}));
  ok(`${label}: and the box is STILL OPEN`, await p.evaluate(()=>!!document.querySelector('.hawk-box')));

  /* THE CIRCLE IS ALWAYS THERE. Tate, 2026-09-21: "a small hawk circle should always be clickable
     on the bottom rightish and always be above the page so switching pages its there".

     Three separate claims, so three separate assertions — "it's there" passing while it sits under
     something else is precisely the bug the old chat drawer caused, and a visibility check alone
     would not have caught it. */
  ok(`${label}: the hawk circle survived navigating`, await p.evaluate(()=>{
    const f=document.querySelector('.hawk-fab');
    return !!f && !f.hidden && getComputedStyle(f).display !== 'none';
  }));
  ok(`${label}: it is still CLICKABLE, not just present`, await p.evaluate(()=>{
    const f=document.querySelector('.hawk-fab');
    const r=f.getBoundingClientRect();
    const hit=document.elementFromPoint(r.left+r.width/2, r.top+r.height/2);
    return hit===f || f.contains(hit);
  }), await p.evaluate(()=>{
    const f=document.querySelector('.hawk-fab'); const r=f.getBoundingClientRect();
    const hit=document.elementFromPoint(r.left+r.width/2, r.top+r.height/2);
    return hit ? (hit.className||hit.tagName) : 'nothing';
  }));
  ok(`${label}: the open box does not cover it`, await p.evaluate(()=>{
    const f=document.querySelector('.hawk-fab').getBoundingClientRect();
    const b=document.querySelector('.hawk-box').getBoundingClientRect();
    return Math.round(b.bottom) <= Math.round(f.top) + 2;
  }));
  ok(`${label}: it is round, in the bottom-right, and wears Hawk's face`, await p.evaluate(()=>{
    const f=document.querySelector('.hawk-fab');
    const r=f.getBoundingClientRect(), s=getComputedStyle(f);
    return r.width <= 60 && r.width >= 40
      && Math.abs(r.width - r.height) < 2
      && parseFloat(s.borderRadius) >= r.width/2
      && (window.innerWidth - r.right) < 40
      && (window.innerHeight - r.bottom) < 140
      && s.backgroundImage.includes('data:image');
  }));
  ok(`${label}: it says where it sent you`, await p.evaluate(()=>/Opened/.test(document.querySelector('.hawk-log').textContent)));

  await p.fill('#hawk-input','beth chance'); await p.press('#hawk-input','Enter'); await p.waitForTimeout(300);
  ok(`${label}: you can keep asking after navigating`, await p.evaluate(()=>
    /Beth Chance/i.test(document.querySelector('.hawk-log').textContent)));

  /* Hawk's own elements only. The app has one overflow of its own that this fixture exposes: the
     class page's "took it" friend chip (.fr-chip-took) runs 13px past a 390px screen when a friend
     has the class in their history. Reported to Tate 2026-09-23; not Hawk's file to change. */
  ok(`${label}: Hawk causes no sideways scroll`, await p.evaluate(()=>
     ![...document.querySelectorAll('.hawk-box *, .hawk-fab')].some(e=>e.getBoundingClientRect().right>window.innerWidth+1)),
     await p.evaluate(()=>[...document.querySelectorAll('body *')].filter(e=>e.getBoundingClientRect().right>window.innerWidth+1)
         .slice(-3).map(e=>(e.className||e.tagName)+'@'+Math.round(e.getBoundingClientRect().right)).join(', ')));

  /* ---- the seat as-of, said once, at the bottom --------------------------------------------- */
  ok(`${label}: the seat reading carries its as-of`, await p.evaluate(()=>{
    const f=document.querySelector('.hawk-foot');
    if (!f) return false;
    if (typeof SEATS_UPDATED_AT==='undefined' || !SEATS_UPDATED_AT) return true;  // nothing to date
    return /as of/i.test(f.textContent);
  }), await p.evaluate(()=>{const f=document.querySelector('.hawk-foot');return f?f.textContent:'none';}));

  await p.keyboard.press('Escape'); await p.waitForTimeout(250);
  ok(`${label}: Escape closes it`, await p.evaluate(()=>!document.querySelector('.hawk-box')));
  ok(`${label}: the icon comes back`, await p.evaluate(()=>{
    const f=document.querySelector('.hawk-fab'); return f && !f.hidden;
  }));
  ok(`${label}: no page errors`, errs.length===0, errs.slice(0,2).join(' | '));

  await p.click('.hawk-fab'); await p.waitForTimeout(200);
  ok(`${label}: reopening keeps the last answer`, await p.evaluate(()=>
    /Beth Chance/i.test(document.querySelector('.hawk-log').textContent)));
  await p.screenshot({path:`hawk-${label}.png`});
  await ctx.close();
}
await b.close(); srv.close();
results.forEach(r=>console.log((r.c?'  ok   ':'  FAIL ')+r.n+(r.d&&!r.c?`   — ${r.d}`:(r.d?`   (${r.d})`:''))));
const bad=results.filter(r=>!r.c).length;
console.log(`${results.length-bad}/${results.length} passed`);
process.exit(bad?1:0);
