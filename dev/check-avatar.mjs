/* THE PHOTO ENCODER, AFTER IT WAS LOST ONCE — 2026-09-18
   The sharper-photos change (build 2026-09-17 00:20, PR #55) was silently reverted by a build
   made from an older copy of the file: EP_MAX went back to 256, epEncodeSquare disappeared, and
   nothing failed. This file is what makes that loud next time. It drives the real
   epProcessImage() in a real browser on synthetic images, and asserts the OUTPUT, not the source.
   PAGE=/abs/path/index.html node check-avatar.mjs                                              */
import {chromium} from 'playwright';
import {readFileSync} from 'fs';
import {createServer} from 'https';
const SRC = process.env.PAGE || new URL('./index.html', import.meta.url).pathname;
const R=[]; const ok=(c,n,d='')=>R.push({n,c:!!c,d});
const html = readFileSync(SRC,'utf8');
const server = createServer({key:readFileSync(new URL('./key.pem',import.meta.url).pathname),
                             cert:readFileSync(new URL('./cert.pem',import.meta.url).pathname)},
  (q,r)=>{ r.writeHead(200,{'Content-Type':'text/html; charset=utf-8'}); r.end(html); });
await new Promise(r=>server.listen(443,'127.0.0.1',r));
const browser = await chromium.launch({executablePath:'/opt/pw-browsers/chromium',
  args:['--host-resolver-rules=MAP termchamp.com 127.0.0.1','--ignore-certificate-errors','--no-proxy-server']});
const ctx = await browser.newContext({ignoreHTTPSErrors:true});
const page = await ctx.newPage();
await page.route('**/*', r=>{ const u=r.request().url();
  return (u.startsWith('https://termchamp.com/')||u.startsWith('blob:')||u.startsWith('data:')) ? r.continue() : r.abort(); });
await page.goto('https://termchamp.com/',{waitUntil:'domcontentloaded'});
await page.waitForTimeout(600);

/* Drive the REAL path a student takes: epPickFile -> epCropOpen -> epCropUse. epProcessImage
   itself lives inside the app's IIFE and is not reachable from here, which is as it should be —
   testing a copy of the encoder would prove nothing about the one that runs. The encoded square
   comes back as the preview's background image, so it can be measured by loading it. */
const run = (w,h) => page.evaluate(async ([w,h])=>{
  const c=document.createElement('canvas'); c.width=w; c.height=h;
  const x=c.getContext('2d');
  for(let i=0;i<w;i+=8){ x.fillStyle=(i/8)%2?'#154734':'#FEFDF9'; x.fillRect(i,0,8,h); }
  const src=await new Promise(res=>c.toBlob(res,'image/png'));
  const file=new File([src],'p.png',{type:'image/png'});
  if(typeof window.epCropOpen!=='function'||typeof window.epCropUse!=='function')
    throw new Error('the crop entry points are gone');
  /* Each run must start clean, or the cropper still holds the previous image and the second
     measurement is just the first one encoded twice — which is how this test first lied. */
  const before=(document.getElementById('epAva')||{style:{}}).style.backgroundImage||'';
  try{ window.epCropCancel(); }catch(e){}
  if(window._epC) window._epC.img=null;
  window.epCropOpen(file);
  for(let i=0;i<100 && !(window._epC&&window._epC.img);i++) await new Promise(r=>setTimeout(r,50));
  if(!(window._epC&&window._epC.img)) throw new Error('the image never loaded into the cropper');
  window.epCropUse();
  const hintEl=document.getElementById('epPhotoHint');
  for(let i=0;i<100;i++){ if(hintEl && /Ready to save|read that image/.test(hintEl.textContent||'')) break; await new Promise(r=>setTimeout(r,50)); }
  const hint=(hintEl&&hintEl.textContent)||'';
  let bg='';
  for(let i=0;i<100;i++){
    bg=(document.getElementById('epAva')||{style:{}}).style.backgroundImage||'';
    if(bg && bg!==before) break;
    await new Promise(r=>setTimeout(r,50));
  }
  if(bg===before) throw new Error('the preview never changed — nothing new was encoded: '+hint);
  const url=(bg.match(/url\("?([^")]+)"?\)/)||[])[1];
  if(!url) throw new Error('nothing was produced: '+hint);
  const img=await new Promise((res,rej)=>{ const i=new Image(); i.onload=()=>res(i); i.onerror=rej; i.src=url; });
  /* The hint the student reads is also the size report, so it doubles as the assertion source
     and no extra fetch of the blob is needed (CSP and the test's own routing both block that). */
  const kb=parseInt((hint.match(/(\d+)KB/)||[])[1]||'0',10);
  return {kb, w:img.naturalWidth, h:img.naturalHeight, hint};
},[w,h]);

{
  const big = await run(3000,2000);
  ok(big.w===512 && big.h===512,'a 3000x2000 photo encodes to a 512px square (was 256 before the revert)', big.w+'x'+big.h);
  ok(big.kb>0 && big.kb<=220,'and it is re-encoded down if it would exceed 220KB', big.kb+'KB');
}
{
  const small = await run(300,300);
  ok(small.w===300,'a 300px photo is not blown up past its own size', small.w+'x'+small.h);
}
{
  const tiny = await run(120,120);
  ok(tiny.w===256,'a tiny photo still gets the 256px floor', tiny.w+'x'+tiny.h);
}
await browser.close(); server.close();
const bad=R.filter(r=>!r.c);
for(const r of R) console.log((r.c?'  ok  ':'  FAIL')+'  '+r.n+(r.d?'   ['+r.d+']':''));
console.log('\n'+(R.length-bad.length)+'/'+R.length+' assertions'+(bad.length?'  — '+bad.length+' FAILED':''));
process.exit(bad.length?1:0);
