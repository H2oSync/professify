/* GOOGLE ANALYTICS, AND THE FOUR THINGS IT MUST NOT DO — 2026-09-18
   ------------------------------------------------------------------------------------------------
   A tag that loads is not a tag that is wired, and "it appears in Realtime" would pass every one
   of these tests while still leaking a professor's name. So this file drives the real app in a
   real browser, at the real host, and reads what was actually queued for Google.

   THE HOST IS THE AWKWARD PART, and it is also rule 3. The app refuses to load GA unless
   location.host equals siteHost() over https, which is what keeps Downloads copies and deploy
   previews out of production. So a file:// test could only ever prove the tag is OFF. Instead:
   a local https server on 443 with a self-signed cert, Chromium launched with
   --host-resolver-rules=MAP termchamp.com 127.0.0.1, so the page genuinely believes it is
   https://termchamp.com/ while never leaving this container.

   gtag.js itself is stubbed, not fetched: what matters is what the app PUSHED, and reading
   dataLayer is exact where a network trace is inference.

   PAGE=/abs/path/index.html node check-ga.mjs         (defaults to ./index.html)                */
import {chromium} from 'playwright';
import {readFileSync} from 'fs';
import {createServer} from 'https';

const SRC = process.env.PAGE || new URL('./index.html', import.meta.url).pathname;
const TEST_ID = 'G-TEST12345';
const R=[]; const ok=(c,n,d='')=>R.push({n,c:!!c,d});

const html = readFileSync(SRC,'utf8');
/* Three versions of the same file, differing in one string, so the suite proves what the config
   value does rather than what today's value happens to be: the real one, a blank one and a test
   one. Reading the current value with a regex instead of matching a literal is what keeps this
   working after the id is filled in. */
const CUR = (html.match(/GA_MEASUREMENT_ID: '([^']*)'/)||[])[0];
if (!CUR) { console.log('FATAL: the GA_MEASUREMENT_ID config line moved'); process.exit(1); }
const shipped = (CUR.match(/'([^']*)'/)||[])[1];
const withId  = html.replace(CUR, `GA_MEASUREMENT_ID: '${TEST_ID}'`);
const blank   = html.replace(CUR, "GA_MEASUREMENT_ID: ''");
/* A fork of this file with the domain blanked out. siteHost() then answers with whatever host is
   serving it, so the host gate would compare a value to itself and pass anywhere. */
const noSite = withId.replace("SITE_URL: 'https://termchamp.com'", "SITE_URL: ''");
if (noSite === withId) { console.log('FATAL: SITE_URL line moved'); process.exit(1); }

const server = createServer(
  {key: readFileSync(new URL('./key.pem', import.meta.url).pathname),
   cert: readFileSync(new URL('./cert.pem', import.meta.url).pathname)},
  (req,res)=>{
    const body = req.url.startsWith('/blank') ? blank
               : req.url.startsWith('/nosite') ? noSite
               : withId;
    res.writeHead(200,{'Content-Type':'text/html; charset=utf-8'});
    res.end(body);
  });
await new Promise(r=>server.listen(443,'127.0.0.1',r));

const browser = await chromium.launch({
  executablePath:'/opt/pw-browsers/chromium',
  args:['--host-resolver-rules=MAP termchamp.com 127.0.0.1','--ignore-certificate-errors','--no-proxy-server']
});

/* One visit. Returns what the app queued for Google plus whether gtag.js was requested. */
async function visit({url='https://termchamp.com/', init=null, steps=[]}={}) {
  const ctx = await browser.newContext({ignoreHTTPSErrors:true});
  const page = await ctx.newPage();
  const tagRequests=[];
  await page.route('**/*', route=>{
    const u=route.request().url();
    if(u.includes('googletagmanager.com')){ tagRequests.push(u); return route.fulfill({status:200,contentType:'application/javascript',body:'/* stub */'}); }
    if(u.startsWith('https://termchamp.com/')||u.startsWith('https://127.0.0.1/')) return route.continue();
    return route.abort();                       /* supabase, polyratings, fonts: not this test's business */
  });
  if(init) await page.addInitScript(init);
  await page.goto(url,{waitUntil:'domcontentloaded'}).catch(()=>{});
  await page.waitForTimeout(600);
  for(const s of steps){ await page.evaluate(s); await page.waitForTimeout(120); }
  const layer = await page.evaluate(()=>{
    try{ return (window.dataLayer||[]).map(a=>JSON.parse(JSON.stringify(Array.from(a)))); }catch(e){ return null; }
  });
  const gaOn = await page.evaluate(()=>{ try{ return !!window.gaAllowed && !!window.gaAllowed(); }catch(e){ return null; } });
  await ctx.close();
  return {layer: layer||[], tagRequests, gaOn};
}
const views = l => l.filter(a=>a[0]==='event'&&a[1]==='page_view').map(a=>a[2]||{});

/* ---- 0. the value that will actually ship ---------------------------------------------------- */
ok(/^G-[A-Z0-9]{6,}$/.test(shipped),
   'the shipped GA_MEASUREMENT_ID is a real measurement id — production sends nothing without it', shipped);

/* ---- 1. a blank id loads nothing at all ------------------------------------------------------ */
{
  const v = await visit({url:'https://termchamp.com/blank'});
  ok(v.tagRequests.length===0,'a blank GA_MEASUREMENT_ID never requests gtag.js');
  ok(v.layer.length===0,'a blank id queues nothing for Google');
}

/* ---- 2. with an id: the tag loads, configured the way the comment claims --------------------- */
let base;
{
  base = await visit({});
  ok(base.tagRequests.length===1,'gtag.js is requested exactly once', String(base.tagRequests.length));
  ok(base.tagRequests[0].includes('id='+TEST_ID),'it is requested with OUR measurement id');
  const consent = base.layer.find(a=>a[0]==='consent');
  ok(!!consent,'consent defaults are set');
  ok(consent && consent[2] && consent[2].ad_storage==='denied' && consent[2].ad_user_data==='denied'
     && consent[2].ad_personalization==='denied','all three ad consents are denied');
  const cfg = base.layer.find(a=>a[0]==='config');
  ok(!!cfg && cfg[1]===TEST_ID,'config names the measurement id');
  ok(cfg && cfg[2] && cfg[2].send_page_view===false,'send_page_view is off — show() owns page views');
  ok(cfg && cfg[2] && cfg[2].allow_google_signals===false,'Google Signals is off');
  /* The tag's OWN events — session_start, scroll, outbound click — take page_location from the
     browser, and the browser's URL is /?add=<invite uuid> for anyone arriving on an invite link.
     A default in config is what stops those reaching Google. */
  ok(cfg && cfg[2] && cfg[2].page_location==='https://termchamp.com/',
     'config pins page_location to the bare origin — no ?add=, ?p= or ?c= can ride along', cfg&&cfg[2]&&cfg[2].page_location);
  /* Order matters: consent AFTER config is consent that arrived too late. */
  ok(base.layer.indexOf(consent) < base.layer.indexOf(cfg),'consent is set BEFORE config');
}

/* ---- 3. the surfaces, which is the whole reason for the manual page_view --------------------- */
{
  const v = await visit({steps:[
    "show('explore')", "show('explore')",      /* the second is a re-render, not a visit */
    "show('sched')", "show('friends')", "show('home')"
  ]});
  const got = views(v.layer).map(p=>p.page_location.split('?tab=')[1]);
  ok(got[0]==='home','the first page_view is the surface the app opened on', got.join(','));
  ok(got.join(',')==='home,explore,sched,friends,home',
     'every tab change is one page_view, and a repeat of the same surface is not counted', got.join(','));
  const ex = views(v.layer).find(p=>p.page_location.endsWith('=explore'));
  ok(ex && ex.page_title==='TermChamp — Explore','the title is the surface name, not the raw key', ex&&ex.page_title);
}

/* ---- 3b. the surfaces that reach Schedule by delegation -------------------------------------- */
{
  /* show('watch') and show('past') hand off to show('sched') and return BEFORE the hook at the
     bottom of show(), so both used to arrive in GA as "Schedule" and their own names were dead
     code. Found in review rather than by this suite, which is why it is a test now.

     Past Classes is account data: a signed-out visitor gets the sign-in prompt instead of the
     screen, so for a guest it is correctly not a surface at all. That is asserted too — it is
     the difference between "we don't count it" and "we count it as Schedule". */
  const v = await visit({steps:["show('watch')","show('sched')","show('past')"]});
  const got = views(v.layer).map(p=>p.page_location.split('?tab=')[1]);
  ok(got.join(',')==='home,watch,sched',
     'Watchlist reports as itself, not as Schedule, and a gated Past Classes reports nothing', got.join(','));
  const w = views(v.layer).find(p=>p.page_location.endsWith('=watch'));
  ok(w && w.page_title==='TermChamp — Watchlist','Watchlist gets its own title', w&&w.page_title);
}

/* ---- 3c. a ?tab= deep link is the arrival, and must not be preceded by a phantom Home -------- */
{
  /* The install shortcut, every notification tap and every shared link lands with ?tab=. The tab
     is applied on window load, so a page_view sent during boot counts Home first and calls the
     real surface a second visit — which is wrong in exactly the landing and funnel reports this
     tag exists for. */
  const v = await visit({url:'https://termchamp.com/?tab=friends'});
  const got = views(v.layer).map(p=>p.page_location.split('?tab=')[1]);
  ok(got.length===1,'a deep link produces exactly one landing page_view', got.join(','));
  ok(got[0]==='friends','and it names the surface the link asked for, not Home', got.join(','));
}

/* ---- 3d. an invite link must not put its uuid anywhere in what Google receives -------------- */
{
  const v = await visit({url:'https://termchamp.com/?add=11111111-2222-3333-4444-555555555555&ref=tate'});
  const blob = JSON.stringify(v.layer);
  ok(!blob.includes('11111111-2222'),'an invite uuid appears nowhere in what was queued');
  ok(!blob.includes('ref=tate'),'nor does the referrer handle');
  ok(!/add=/.test(blob),'nor the parameter itself');
}

/* ---- 3e. the bridge: every first-party event reaches GA, minus what names anyone ------------ */
{
  /* track() is the app's own recorder and is exposed as window.track. Driving IT rather than
     gaEvent is the point: if the bridge is ever unhooked, these go silent. */
  const v = await visit({steps:[
    "track('prof_view','Jim Mueller|MATH','explore')",
    "track('click',null,'home',{target:'a:Jim Mueller'})",
    "track('review_submit',null,'rate',{kind:'new'})",
    "track('push_permission',null,'settings',{result:'granted'})",
    "track('import_result',null,'past',{kind:'paste',rows:41,reason:'ok',secret:'do-not-send'})"
  ]});
  const evs = v.layer.filter(a=>a[0]==='event').map(a=>({name:a[1], p:a[2]||{}}));
  const names = evs.map(e=>e.name);
  ok(names.includes('prof_view'),'a professor view reaches GA as an event', names.join(','));
  ok(names.includes('review_submit') && names.includes('push_permission') && names.includes('import_result'),
     'the funnel events reach GA', names.join(','));
  const blob = JSON.stringify(evs);
  ok(!blob.includes('Jim Mueller'),'the professor name is nowhere in what Google receives');
  ok(!blob.includes('do-not-send'),'an unlisted property is dropped rather than forwarded');
  const pv = evs.find(e=>e.name==='prof_view');
  ok(pv && Object.keys(pv.p).join(',')==='surface','a professor view carries the surface and nothing else',
     pv && Object.keys(pv.p).join(','));
  ok(pv && pv.p.surface==='explore','and the surface is the one it happened on', pv&&pv.p.surface);
  ok(names.includes('ui_click') && !names.includes('click'),
     "our click is renamed ui_click so it cannot mix with GA's own click event", names.join(','));
  const imp = evs.find(e=>e.name==='import_result');
  ok(imp && imp.p.rows===41 && imp.p.kind==='paste' && imp.p.reason==='ok',
     'the enumerated properties do come through — rows, kind, reason', JSON.stringify(imp&&imp.p));
}

/* ---- 3f. where the visit came from is GA's own business, not ours to forward ---------------- */
{
  /* app_open is the one event that puts something OTHER than a tab in the surface slot: the
     referrer's hostname. The props whitelist never saw that argument, so it went to Google
     verbatim until review caught it. This drives the real boot path with a referrer set. */
  const v = await visit({init:()=>{ Object.defineProperty(document,'referrer',{get:()=>'https://www.reddit.com/r/CalPoly/'}); },
                         steps:["toggleWatch('sp:test-prof')","toggleWatch('sp:test-prof')"]});
  const blob = JSON.stringify(v.layer);
  ok(!/reddit/i.test(blob),'the referrer hostname never reaches Google through the surface slot');
  const evs = v.layer.filter(a=>a[0]==='event').map(a=>({name:a[1], p:a[2]||{}}));
  ok(!evs.some(e=>e.name==='app_open'),
     'app_open fires before the tag boots and is simply not mirrored — GA counts session_start itself');
  /* The guard itself, driven directly: anything that is not one of show()'s tab names becomes
     "app". This is the assertion that fails if the surface slot ever stops being fail-closed. */
  const g = await visit({steps:["track('app_open',null,'reddit.com',{mode:'browser'})"]});
  const go = g.layer.filter(a=>a[0]==='event').map(a=>({name:a[1],p:a[2]||{}})).find(e=>e.name==='app_open');
  ok(go && go.p.surface==='app','an unknown surface falls back to "app" rather than passing through',
     go && go.p.surface);
  ok(!JSON.stringify(g.layer).includes('reddit'),'and the hostname it carried is gone');
  /* toggleWatch is the real function a student's tap calls — not a hand-made track() call. */
  const w = evs.filter(e=>e.name==='watch_toggle');
  ok(w.length===2,'watching and unwatching a professor are two events', String(w.length));
  ok(w[0] && w[0].p.kind==='prof' && w[0].p.on===true && w[1] && w[1].p.on===false,
     'and they record the direction, never which professor', JSON.stringify(w.map(x=>x.p)));
  ok(!JSON.stringify(w).includes('test-prof'),'the watched id is not sent');
}

/* ---- 3g. the refusals that cannot be driven from here --------------------------------------- */
{
  /* THIS ONE IS A SOURCE CHECK AND SAYS SO. Two of the three review refusals need a signed-in
     session and a real professor to reach, which this harness deliberately does not have. The
     point of the funnel is that no refusal shape is invisible, so each branch is asserted to
     carry its own reason — including "already-reviewed", which is the client-side guard and in
     practice the most common one. A source check is weaker than driving the code; it is here
     because the alternative was no check at all, and a missing branch is exactly the failure
     this funnel exists to prevent. */
  const reasons = (html.match(/track\('review_refused'[^)]*reason:\s*'?([a-z-]+)'?/g)||[])
    .map(m=>(m.match(/reason:\s*'?([a-z-]+)/)||[])[1]);
  ok(reasons.includes('already-reviewed'),'the client-side "you already reviewed them" refusal is counted', reasons.join(','));
  ok(reasons.includes('hourly-cap'),'the hourly cap refusal is counted', reasons.join(','));
  ok(/track\('review_refused', null, 'rate', \{reason:String\(_why\)/.test(html),
     'and the server refusal carries the shape the server gave, not its sentence');
  ok(/track\('review_submit', null, 'rate'/.test(html),'a successful review is counted');
}

/* ---- 4. rule 1: nothing that identifies a person, a professor or a class --------------------- */
{
  const v = await visit({steps:["show('prof')","show('class')"]});
  const blob = JSON.stringify(v.layer);
  ok(/\?tab=prof\b/.test(blob),'a professor page still counts as a surface');
  ok(!/@/.test(blob),'no email address anywhere in what was queued');
  ok(!/user_id|client_id|profKey|currentProf/.test(blob),'no identifier fields are sent');
  const p = views(v.layer).find(x=>x.page_location.endsWith('=prof'));
  ok(p && Object.keys(p).sort().join(',')==='page_location,page_title',
     'a page_view carries exactly two fields: title and location', p&&Object.keys(p).join(','));
  ok(p && p.page_location==='https://termchamp.com/?tab=prof',
     'the location names the tab and nothing else — no professor, no query, no path', p&&p.page_location);
}

/* ---- 5. rule 2: GPC and DNT switch it off entirely ------------------------------------------- */
{
  const gpc = await visit({init:()=>{ Object.defineProperty(navigator,'globalPrivacyControl',{get:()=>true}); }});
  ok(gpc.tagRequests.length===0,'Global Privacy Control: gtag.js is never requested');
  ok(gpc.layer.length===0,'Global Privacy Control: nothing is queued');
  const dnt = await visit({init:()=>{ Object.defineProperty(navigator,'doNotTrack',{get:()=>'1'}); }});
  ok(dnt.tagRequests.length===0,'Do Not Track: gtag.js is never requested');
  ok(dnt.layer.length===0,'Do Not Track: nothing is queued');
}

/* ---- 6. rule 3: only the real host ------------------------------------------------------------ */
{
  const v = await visit({url:'https://127.0.0.1/'});
  ok(v.tagRequests.length===0,'served from another host (a preview, a local copy): no tag');
  ok(v.gaOn===false,'gaAllowed() says no when the host is not the declared one');
  const f = await visit({url:'https://termchamp.com/nosite'});
  ok(f.tagRequests.length===0,'a copy with SITE_URL blanked out loads no tag either');
}

await browser.close();
server.close();

const bad=R.filter(r=>!r.c);
for(const r of R) console.log((r.c?'  ok  ':'  FAIL')+'  '+r.n+(r.d?'   ['+r.d+']':''));
console.log('\n'+(R.length-bad.length)+'/'+R.length+' assertions'+(bad.length?'  — '+bad.length+' FAILED':''));
process.exit(bad.length?1:0);
