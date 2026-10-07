/* The /s link preview (netlify/edge-functions/share.ts), run for real under Node's TypeScript
   stripping: node --experimental-strip-types check-share-edge.mjs
   It checks what iMessage will read (og:title, og:image) for a shared week and a shared plan, and
   that a crafted link can't change where the image comes from. Then it breaks the function a few
   ways and checks that these assertions notice (a verifier that cannot fail is worth nothing). */
import fs from 'node:fs'; import path from 'node:path'; import os from 'node:os'; import { pathToFileURL } from 'node:url';
const HERE = path.dirname(new URL(import.meta.url).pathname);
const SRC = process.env.SHARE_TS || path.resolve(HERE, '../../netlify/edge-functions/share.ts');
globalThis.Deno = { env: { get: () => undefined } };
const ID = 'a'.repeat(8) + '0123456789abcdef0123456789abcdef'.slice(8);
const run = async (file) => {
  const f = (await import(pathToFileURL(file).href + '?v=' + Math.random())).default;
  const get = async q => { const r = await f(new Request('https://termchamp.com/s?' + q)); const t = await r.text();
    const m = k => (new RegExp('<meta property="' + k + '"\\s+content="([^"]*)"').exec(t) || [])[1];
    return { title: m('og:title'), desc: m('og:description'), img: m('og:image'), h: m('og:image:height'), go: (/href="([^"]*)" id|id="go" href="([^"]*)"/.exec(t) || [])[2] || '', app: (/data-app="([^"]*)"/.exec(t) || [])[1] || '' }; };
  const fails = [];
  const ok = (c, n, d) => { if (!c) fails.push(n + ' → ' + JSON.stringify(d)); };
  const week = await get(`i=${ID}.png&nm=Tate&tm=Fall%202026&add=u1`);
  ok(week.title === 'Look at Tate&#39;s schedule this semester' && week.desc === 'Their Fall 2026 classes, and whether yours line up.', 'a shared week reads as before', week);
  ok(week.img === `https://rqkndeqbcahozidniesn.supabase.co/storage/v1/object/public/schedule-cards/${ID}.png`, 'the preview image is the uploaded card', week);
  const plan = await get(`i=${ID}.png&nm=Tate&tm=Fall%202026&add=u1&pl=A`);
  ok(plan.title === 'Look at Tate&#39;s Plan A' && plan.desc === 'Their Fall 2026 Plan A, and whether yours line up.', 'a shared plan says which plan', plan);
  const anon = await get(`i=${ID}.png&pl=C`);
  ok(anon.title === 'Look at my Plan C', 'a plan with no name', anon);
  const bad = await get(`i=${ID}.png&nm=Tate&tm=Fall%202026&pl=%3Cb%3E`);
  ok(bad.title === 'Look at Tate&#39;s schedule this semester', 'anything but A/B/C in pl is ignored', bad);
  const D = await get(`i=${ID}.png&nm=Tate&pl=D`);
  ok(D.title === 'Look at Tate&#39;s schedule this semester', 'pl=D is ignored', D);
  const evil = await get(`i=..%2F..%2Fsecret.png&nm=%22%3E%3Cscript%3E&pl=A`);
  ok(evil.img === 'https://termchamp.com/share-card.png' && !/<script>/.test(evil.title || ''), 'a crafted id falls back to the generic card and the name is escaped', evil);
  /* a shared professor or class (2026-10-04) */
  ok(week.h === '1200' && !week.app, 'a week stays a 1200×1200 picture with no app link', week);
  const pr = await get(`k=p&i=${ID}.png&nm=Tate&p=ryan-tully-doyle`);
  ok(pr.title === 'Tate shared a professor' && pr.img === week.img && pr.h === '630' && pr.go === '/?p=ryan-tully-doyle' && pr.app === '/app/?p=ryan-tully-doyle', 'a professor: “Tate shared a professor”, the 1200×630 card, their page (phone app on a phone)', pr);
  const cl = await get(`k=c&i=${ID}.png&nm=Tate&c=bus%204442`);
  ok(cl.title === 'Tate shared a class' && cl.h === '630' && cl.go === '/?c=BUS%204442' && cl.app === '/app/?c=BUS%204442', 'a class: “Tate shared a class”, its page', cl);
  const cn = await get(`k=c&i=${ID}.png&c=CSC%20101`);
  ok(cn.title === 'Someone shared a class', 'a class with no name', cn);
  const cx = await get(`k=p&i=${ID}.png&nm=Tate&p=%22%3E%3Cscript%3E`);
  ok(cx.title === 'Look at Tate&#39;s schedule this semester' && !/[?&;]p=|script/.test(cx.go) && !cx.app, 'a crafted professor is ignored, never written into the page', cx);
  const cy = await get(`k=c&i=${ID}.png&nm=Tate&c=..%2Fx`);
  ok(!/[?&;]c=/.test(cy.go) && !cy.app, 'a crafted class is ignored', cy);
  return fails;
};
let bad = 0;
const base = await run(SRC);
if (base.length) { bad++; console.log('FAIL (real function):\n  ' + base.join('\n  ')); } else console.log('ok   share.ts: week, plan, no-name plan, bad pl, crafted id');
const src = fs.readFileSync(SRC, 'utf8');
const MUT = [
  ['plan never read', '/^[ABC]$/.test(url.searchParams.get("pl") ?? "")', 'false'],
  ['any pl accepted', '/^[ABC]$/.test(url.searchParams.get("pl") ?? "")', '!!(url.searchParams.get("pl"))'],
  ['plan title says schedule', '? (first ? `Look at ${first}\'s Plan ${plan}` : `Look at my Plan ${plan}`)', '? (first ? `Look at ${first}\'s schedule this semester` : `Look at my Plan ${plan}`)'],
  ['professor never recognised', 'kind === "p" && /^[a-z0-9-]{2,80}$/.test(prof) ? "p"', 'false ? "p"'],
  ['any professor value accepted', '/^[a-z0-9-]{2,80}$/.test(prof)', 'true'],
  ['class goes to the home page', 'const go = thing ? "/?" + thingQ :', 'const go = false ? "/?" + thingQ :'],
  ['card picture said to be square', 'const imgH = thing ? 630 : 1200;', 'const imgH = 1200;'],
  ['professor title says class', '${thing === "p" ? "a professor" : "a class"}', '${"a class"}'],
  ['plan description drops the plan', '`Their ${term} Plan ${plan}, and whether yours line up.`', '`Their ${term} classes, and whether yours line up.`'],
];
const tmp = fs.mkdtempSync(path.join(os.tmpdir(), 'shedge-'));
let caught = 0;
for (const [name, a, b] of MUT) {
  if (src.split(a).length !== 2) { console.log('  BAD MUTANT:', name); bad++; continue; }
  const f = path.join(tmp, name.replace(/\W+/g, '-') + '.ts'); fs.writeFileSync(f, src.replace(a, b));
  const r = await run(f);
  if (r.length) { caught++; console.log('  caught  ', name); } else { bad++; console.log('  SURVIVED', name); }
}
console.log(`share-edge: ${bad ? 'FAILED' : 'passed'} · mutants ${caught}/${MUT.length} caught`);
process.exit(bad ? 1 : 0);
