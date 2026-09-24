/* THE BRAND, AND THE 76 THINGS THAT MUST NOT MOVE WITH IT — 2026-09-16.
   Professify was renamed to TermChamp. The rename is not the risky part; what it sits next to is.

   `professify` appears in this file in three completely different roles, and only ONE of them is
   a brand:
     1. the NAME a student reads — title, wordmark, meta, legal, copy. This is what renames.
     2. 76 IDENTIFIERS — localStorage keys (professify-account, professify_my_classes, …), the
        build stamp window.PROFESSIFY_BUILD, professifyDiag(), the domain professify.app. These
        are data contracts. Renaming a storage key does not rename anything: it ABANDONS the old
        one. Every signed-in student is logged out, their cached classes, theme, dismissed cards
        and seen-notification state all read as empty, and nothing errors — the app just quietly
        behaves as though 24 people are new. That is the expensive failure, it is silent, and a
        careless find-and-replace produces it in one keystroke.
     3. COMMENTS — this project's dated record of why things are the way they are. Rewriting the
        name inside them would falsify that history, so they still say Professify, correctly.

   So this file asserts BOTH directions: the name is gone from everything a student sees, and
   every identifier is exactly where it was. The second half is the one worth keeping forever —
   it makes the next rename (CourseChamp, or back) mechanically safe instead of careful.

   Run against a mutated copy with PAGE=file:///abs/path.html node check-brand.mjs */
import {chromium} from 'playwright';
import {readFileSync,existsSync} from 'fs';
const R=[]; const ok=(c,n,d='')=>R.push({n,c:!!c,d});
/* Cowork's outputs folder when it exists, otherwise this checkout (Claude Code, a laptop). */
const HERE=new URL('.',import.meta.url).pathname;
const F=process.env.PAGE||(existsSync('/mnt/user-data/outputs/index.html')
  ?'file:///mnt/user-data/outputs/index.html':'file://'+HERE+'index.html');
const SRC=F.replace('file://','');
const NAME='TermChamp';

const src=readFileSync(SRC,'utf8');

/* ---- 1. the identifiers, which must be byte-for-byte where they were ------------------------- */
{
  /* Captured from the build that shipped immediately before the rename. Not a count — the actual
     names, because a count would pass if one key were renamed and another added. */
  const REQUIRED=['professify-account','professify-profile','professify-theme',
    'professify_avatar_','professify_class_alerts','professify_dismiss_','professify_friend_secs',
    'professify_friends_cache_','professify_frp_view','professify_my_class_meta',
    'professify_my_classes','professify_notif_cleared','professify_notif_seen',
    'professify_pending_handle','professify_prof_cache','professify_profile_cache',
    'professify_rev_times','professify_sched_done_','professify_sched_fill_','professify_sched_seen'];
  const missing=REQUIRED.filter(k=>!src.includes(k));
  ok(missing.length===0,'every known storage key survived the rename',missing.join(', '));
  const found=new Set((src.match(/professify[_-][A-Za-z0-9_-]*/g)||[]));
  ok(found.size>=70,'the identifier namespace is still populated ('+found.size+' distinct)');
  /* THE DECLARATION, not a mention. Checking `includes('window.PROFESSIFY_BUILD')` passed a
     mutation that renamed the declaration, because the console line below still referenced the
     old name — the test found the reference and called it proof. A contract is defined where it
     is ASSIGNED; everywhere else is just a reader. */
  ok(/window\.PROFESSIFY_BUILD\s*=/.test(src),
     'the build stamp is still DECLARED — sw.js BUILD and every verifier read it');
  ok(/window\.professifyDiag\s*=|function\s+professifyDiag/.test(src),
     'professifyDiag() is still DECLARED — it is a documented entry point');
  ok(src.includes('professify.app'),'the domain is untouched — it is still the real domain');
  /* The history stays honest. */
  ok((src.match(/Professify/g)||[]).length>=20,
     'the comments still say Professify — they are a dated record, not copy',
     String((src.match(/Professify/g)||[]).length));
}

/* ---- 2. the name, gone from everything a student can see ------------------------------------- */
const b=await chromium.launch();
{
  const p=await b.newPage({viewport:{width:1280,height:1000}});
  const errs=[]; p.on('pageerror',e=>errs.push(e.message));
  await p.goto(F); await p.waitForTimeout(2200);

  const head=await p.evaluate(()=>({
    title:document.title,
    og:(document.querySelector('meta[property="og:site_name"]')||{}).content,
    ogT:(document.querySelector('meta[property="og:title"]')||{}).content,
    ios:(document.querySelector('meta[name="apple-mobile-web-app-title"]')||{}).content,
    wordmark:(document.querySelector('.brand-name')||{}).innerText,
  }));
  ok(head.title.startsWith(NAME),'the page title is the new name',head.title);
  ok(head.og===NAME,'og:site_name',head.og);
  ok((head.ogT||'').startsWith(NAME),'og:title',head.ogT);
  ok(head.ios===NAME,'the iOS home-screen title',head.ios);
  ok(head.wordmark===NAME,'the wordmark in the header',head.wordmark);
  /* They must AGREE. Four places carrying the name is fine; four carrying different names is a
     brand that looks unfinished on exactly the surfaces strangers see first. */
  ok(new Set([head.og,head.ios,head.wordmark]).size===1,'and they all agree with each other',
     JSON.stringify(head));

  /* Every tab, plus the legal dialog, which is dense with the name. */
  const seen=await p.evaluate(async ()=>{
    const out={};
    for(const v of ['home','explore','sched','friends','settings']){
      try{ show(v); }catch(e){}
      await new Promise(r=>setTimeout(r,120));
      out[v]=document.body.innerText;
    }
    for(const t of ['terms','privacy','security','guidelines']){
      try{ openLegal(t); }catch(e){}
      await new Promise(r=>setTimeout(r,120));
      out['legal:'+t]=(document.getElementById('legalBody')||{}).innerText||'';
    }
    try{ closeLegal(); }catch(e){}
    return out;
  });
  for(const [where,text] of Object.entries(seen)){
    const hits=(text.match(/Professify/g)||[]).length;
    ok(hits===0,`no "Professify" left on ${where}`,hits?text.slice(text.indexOf('Professify')-60,text.indexOf('Professify')+60):'');
  }
  ok((seen.home.match(/TermChamp/g)||[]).length + (seen['legal:privacy'].match(/TermChamp/g)||[]).length > 0,
     'and the new name is actually present');
  ok(errs.length===0,'no page errors',errs.join(' | '));
  await p.close();
}
await b.close();

/* ---- 3. the manifest agrees with the app ------------------------------------------------------ */
try{
  const m=JSON.parse(readFileSync(existsSync('/home/claude/repo/manifest.webmanifest')
    ?'/home/claude/repo/manifest.webmanifest':HERE+'manifest.webmanifest','utf8'));
  ok(m.name===NAME && m.short_name===NAME,'the manifest carries the new name',JSON.stringify([m.name,m.short_name]));
  ok(Array.isArray(m.icons) && m.icons.some(i=>i.purpose==='maskable'),
     'and still ships a maskable icon — Android crops to the inner 80% and the cap sits near the edge');
}catch(e){ ok(false,'the manifest is readable',String(e).slice(0,80)); }

if(process.env.VERBOSE)for(const r of R)console.log((r.c?'  ok   ':'  FAIL ')+r.n);
const bad=R.filter(r=>!r.c);
for(const r of bad) console.log(`  FAIL ${r.n}${r.d?' — '+r.d:''}`);
console.log(`check-brand: ${R.length-bad.length} passed, ${bad.length} failed`);
process.exit(bad.length?1:0);
