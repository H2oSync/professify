/* check-desktop-group-week — the group page's coloured week as a SECOND view (website-group-week, Tate 2026-10-14: "the
   group schedule coloured week view is added as a second view"). Runs the REAL index.html in Chromium, signed in, against
   the PostgREST stand-in; the groups flag is switched on after load (it ships dark).
   Run: APP_DIR=<repo> node check-desktop-group-week.mjs [--only name] [--quiet]   (APP_PORT to move off 8190)
   The promises (phone spec: group-schedule 2026-10-10): a "Free time | Week" switch, remembered per signed-in person; the week
   draws each person's classes of the term people are in NOW as blocks in their own colour, a class two people share as ONE
   block split into both colours, overlapping ones side by side; Work & activities draw too (yours by its name, a friend's as
   "Busy" with no name); the stretches everyone counted is free are green bands that say how long; someone who shared nothing
   draws nothing and is not counted; muting leaves the week; every block opens its class page / friend / editor; a Spring
   class never lands on the Fall week; text holds 4.5:1 in light and dark. */
import { openApp } from './app-harness.mjs';
import * as FX from './app-fixtures.mjs';

const args = process.argv.slice(2);
const ONLY = args.includes('--only') ? args[args.indexOf('--only') + 1] : null;
const QUIET = args.includes('--quiet');
let pass = 0, fail = 0; const fails = [];
function ok(c, name, info) {
  if (c) { pass++; if (!QUIET) console.log('  ok  ', name); }
  else { fail++; fails.push(name); console.log('  FAIL', name, info !== undefined ? '→ ' + JSON.stringify(info).slice(0, 700) : ''); }
}
const tick = async (p, ms = 400) => { await p.clock.runFor(ms); await p.waitForTimeout(250); };
const NOW = '2026-10-14T10:30:00-07:00';           /* a Wednesday */
let portN = 0; const BASE = +(process.env.APP_PORT || 8190);
const ME = FX.ME.id, [AVERY, ROWAN, SKY, QUINN, HARPER] = FX.FRIENDS.map(f => f.id);
const GROUP = { id: 'g1', name: 'Study crew', members: [AVERY, ROWAN, SKY, HARPER] };
const seed = (extra = '') => `try{localStorage.setItem('professify_groups',${JSON.stringify(JSON.stringify([GROUP]))});}catch(e){}` + extra;
const withTheme = t => `try{localStorage.setItem('professify-theme',${JSON.stringify(t)})}catch(e){}`;
const open = [];
const desk = async (o = {}) => { const a = await openApp(Object.assign({ path: '/', width: 1440, height: 900, wait: 4000, time: NOW, port: BASE + (portN++ % 3), init: seed() }, o)); open.push(a); return a; };
const T = {};
const test = (name, fn) => { T[name] = fn; };
/* Harper has shared nothing: she has no my_sections / saved_classes rows in the fixtures. */
const CM_ID = 'c0000000-0000-4000-8000-0000000000a1';
const withCm = () => { const t = JSON.parse(JSON.stringify(FX.TABLES)); t.commitments = [{ id: CM_ID, user_id: ME, kind: 'work', name: 'Barista', days: 'MWF', start_min: 960, end_min: 1200, busy: true }]; return t; };
const rpcBusy = Object.assign({}, FX.RPC, { friend_busy_blocks: [{ user_id: AVERY, days: 'TR', start_min: 600, end_min: 720 }] });

async function openGroup(page, view) {
  await page.evaluate(v => { try { if (v) localStorage.setItem('professify_group_view_' + sbUser.id, v); } catch (e) {} PROFESSIFY_FLAGS.groups = true; show('friends'); gpSetTab('groups'); gpOpenGroup('g1'); }, view || null);
  await tick(page, 600);
}
const switchState = page => page.evaluate(() => [...document.querySelectorAll('.gw-sb')].map(b => b.textContent + ':' + b.getAttribute('aria-pressed')).join());
/* every block of one day column (0 = Monday): text, fills, box */
const dayBlocks = (page, di) => page.evaluate(di => [...document.querySelectorAll('.gw-gb > .gw-day')[di].querySelectorAll('.gw-b')].map(b => {
  const r = b.getBoundingClientRect();
  return { label: b.getAttribute('aria-label'), text: b.innerText.replace(/\s+/g, ' ').trim(), bg: b.style.background || b.style.backgroundColor, bgi: getComputedStyle(b, '::before').backgroundImage, l: r.left, w: r.width, t: r.top, h: r.height, cm: b.classList.contains('cm'), onclick: b.getAttribute('onclick') || '', dcm: b.getAttribute('data-cm-act') };
}), di);
const hex2rgb = h => { const n = parseInt(h.slice(1), 16); return `rgb(${n >> 16}, ${(n >> 8) & 255}, ${n & 255})`; };

test('switch', async () => {
  const { page, close, log } = await desk(); await tick(page, 1500);
  await openGroup(page);
  ok(await switchState(page) === 'Free time:true,Week:false' && !!(await page.$('.gp-grid')) && !(await page.$('.gw-wk')), 'opens on Free time (the lanes grid), Week not pressed');
  await page.click('.gw-sb:nth-child(2)'); await tick(page, 300);
  ok(await switchState(page) === 'Free time:false,Week:true' && !!(await page.$('.gw-wk')) && !(await page.$('.gp-grid')), 'Week: the coloured week replaces the lanes grid, Week pressed');
  const kv = await page.evaluate(() => localStorage.getItem('professify_group_view_' + sbUser.id));
  ok(kv === 'week', 'the choice is kept for this person on this device', kv);
  /* the members list and the ranked times stay on the page in both views */
  ok(await page.evaluate(() => !!document.querySelector('.gp-side') && !!document.querySelector('.gp-times')), 'members and the ranked free times stay beside / under the week');
  await page.reload(); await tick(page, 2500);
  await page.evaluate(() => { PROFESSIFY_FLAGS.groups = true; show('friends'); gpSetTab('groups'); gpOpenGroup('g1'); }); await tick(page, 600);
  ok(await switchState(page) === 'Free time:false,Week:true' && !!(await page.$('.gw-wk')), 'after a reload the group opens on the Week again');
  await page.click('.gw-sb:nth-child(1)'); await tick(page, 300);
  ok(await switchState(page) === 'Free time:true,Week:false' && !!(await page.$('.gp-grid')), 'Free time brings the lanes grid back');
  /* the choice belongs to the person, not the browser */
  const other = await page.evaluate(() => localStorage.getItem('professify_group_view_someone-else'));
  ok(other === null, 'nothing is kept for anyone else');
  ok(log.errors.length === 0, 'no page errors', log.errors);
  await close();
});

test('blocks', async () => {
  const { page, close, log } = await desk(); await tick(page, 1500);
  await openGroup(page, 'week');
  const col = await page.evaluate(() => GW_COL.slice());
  const mon = await dayBlocks(page, 0);
  const codes = mon.map(b => b.label.split(',')[0]).sort();
  ok(codes.join() === 'BUS 3431,BUS 3438,BUS 4442,BUS 4445', 'Monday: one block per class, a shared class once (not once per person)', codes);
  const by = c => mon.find(b => b.label.startsWith(c));
  /* members are coloured in the order of the list: you, Avery, Rowan, Sky, Harper */
  ok(by('BUS 3431').bg.includes(hex2rgb(col[0])) && !by('BUS 3431').bg.includes('linear'), 'your own class is one solid block in your colour', by('BUS 3431'));
  const mix = (c, a, b) => { const x = by(c).bg; return x.includes('linear-gradient') && x.includes(hex2rgb(col[a])) && x.includes(hex2rgb(col[b])); };
  ok(mix('BUS 4442', 0, 1), 'BUS 4442 (you + Avery) is ONE block split into both colours');
  ok(mix('BUS 4445', 0, 2), 'BUS 4445 (you + Rowan) is split you + Rowan');
  ok(mix('BUS 3438', 0, 3), 'BUS 3438 (you + Sky) is split you + Sky');
  ok(by('BUS 4442').text === 'BUS 4442 12:10p–2p', 'a block says its code and time, as the Portal writes them', by('BUS 4442').text);
  ok(/you, Avery/.test(by('BUS 4442').label), 'its label says who is in it', by('BUS 4442').label);
  /* height is time: two 120-minute classes are as tall as each other, and 12:10 sits 2h10m under 10:10 */
  ok(Math.abs(by('BUS 4442').h - by('BUS 4445').h) < 0.6 && Math.abs((by('BUS 4442').t - by('BUS 3438').t) - 120 * 0.72) < 1.5, 'blocks are drawn to scale in time', [by('BUS 4442').h, by('BUS 4445').h, by('BUS 4442').t - by('BUS 3438').t]);
  /* ...and sits at its own time on the hour axis: 10:10a is 10 minutes under the 10am rule */
  const rule = await page.evaluate(() => { const rs = [...document.querySelectorAll('.gw-gb > .gw-day')[0].querySelectorAll('.gw-rule')]; return rs[1].getBoundingClientRect().top; });
  ok(Math.abs(by('BUS 3438').t - rule - (10 * 0.72 + 1)) < 1.5, 'BUS 3438 (10:10a) sits ten minutes under the 10am line', [by('BUS 3438').t, rule]);
  /* Harper shared nothing: none of her colour anywhere, and she is not counted */
  const all = await page.evaluate(() => [...document.querySelectorAll('.gw-b')].map(b => b.style.background).join('|'));
  ok(!all.includes(hex2rgb(col[4])), 'Harper (nothing shared) draws no block in her colour');
  const side = await page.evaluate(() => document.querySelector('.gp-side').innerText.replace(/\s+/g, ' '));
  ok(/Harper Mock no schedule shared/.test(side), 'and the list says “no schedule shared” beside her', side);
  /* Tuesday / Thursday carry Avery's PHIL and BUS 3431 §02 (8:10) and Sky's / Rowan's */
  const tue = (await dayBlocks(page, 1)).map(b => b.label.split(',')[0]).sort();
  ok(tue.join() === 'BUS 3431,ECON 2303,PHIL 3331,STAT 2170', 'Tuesday: Avery’s BUS 3431 §02 and PHIL 3331, Rowan’s ECON 2303, Sky’s STAT 2170 (Sky’s unsaved ECON §04 is not drawn)', tue);
  ok((await dayBlocks(page, 4)).length === 0, 'Friday has nothing, so it draws nothing (no invented class)');
  /* the legend: a ball per person in their colour; Harper dimmed */
  const key = await page.evaluate(() => [...document.querySelectorAll('.gw-key .gw-k')].map(k => k.innerText.trim() + '|' + (k.querySelector('.gw-ball') ? k.querySelector('.gw-ball').style.background : '') + '|' + k.classList.contains('off')));
  ok(key.length === 6 && key[0].startsWith('You|' + hex2rgb(col[0])) && key[1].startsWith('Avery|' + hex2rgb(col[1])) && key[4].startsWith('Harper|') && key[4].endsWith('|true'), 'legend: you, Avery, Rowan, Sky, Harper (dimmed) and the green key', key);
  const av = await page.evaluate(() => [...document.querySelectorAll('.gp-mem .gp-av')].slice(0, 2).map(a => a.style.background));
  ok(av[0].includes(hex2rgb(col[0])) && av[1].includes(hex2rgb(col[1])), 'the members list carries the same colours', av);
  ok(log.errors.length === 0, 'no page errors', log.errors);
  await close();
});

test('free', async () => {
  const { page, close } = await desk(); await tick(page, 1500);
  await openGroup(page, 'week');
  /* Monday: you, Rowan (2:10-4), Sky (10:10-12) are in class 10:10-6 (a 30-minute slot is busy if any of it is), so the
     only shared stretch inside 8a-6p is 8a-10a. Harper is not counted, nobody is invented. */
  const mon = await page.evaluate(() => [...document.querySelectorAll('.gw-gb > .gw-day')[0].querySelectorAll('.gw-free')].map(f => ({ title: f.title, text: f.innerText.replace(/\s+/g, ' ').trim(), top: f.getBoundingClientRect().top })));
  ok(mon.length === 1 && mon[0].title === 'Free 7a–10a' && mon[0].text === 'Free 3h', 'Monday: one green band, written as it really is (7a–10a, 3h) though the grid starts at 8a', mon);
  const tue = await page.evaluate(() => [...document.querySelectorAll('.gw-gb > .gw-day')[1].querySelectorAll('.gw-free')].map(f => f.title));
  ok(tue.includes('Free 2p–10p'), 'Tuesday: free from 2p (Sky’s STAT ends at 2; her unsaved ECON §04 is not counted)', tue);
  const fr = await page.evaluate(() => [...document.querySelectorAll('.gw-gb > .gw-day')[4].querySelectorAll('.gw-free')].map(f => f.title));
  ok(fr.length === 1 && fr[0] === 'Free 7a–10p', 'Friday: everyone is free all day, and it says 7a–10p, not just the part the grid shows', fr);
  const key = await page.evaluate(() => document.querySelector('.gw-key').innerText.replace(/\s+/g, ' '));
  ok(/All 5 free$/.test(key) === false && /Free for the 4 counted$/.test(key), 'the key says how many are counted (4: Harper shared nothing)', key);
  /* a band never sits under a class */
  const over = await page.evaluate(() => { let n = 0; document.querySelectorAll('.gw-day').forEach(d => { const fs = [...d.querySelectorAll('.gw-free')].map(f => f.getBoundingClientRect()); d.querySelectorAll('.gw-b').forEach(b => { const r = b.getBoundingClientRect(); fs.forEach(f => { if (r.top < f.bottom - 1 && r.bottom > f.top + 1) n++; }); }); }); return n; });
  ok(over === 0, 'no green band under any class', over);
  /* the lanes view and the week agree: the ranked list (shared by both views) is still there */
  ok(await page.evaluate(() => /Monday/.test(document.querySelector('.gp-times').innerText)), 'the ranked free times are still listed');
  await close();
});

test('solo', async () => {
  /* a group where nobody else has shared anything: only your own classes, and nothing is called "free together" */
  const { page, close } = await desk({ init: `try{localStorage.setItem('professify_groups',${JSON.stringify(JSON.stringify([{ id: 'g1', name: 'Quiet', members: [HARPER] }]))});}catch(e){}` }); await tick(page, 1500);
  await openGroup(page, 'week');
  ok((await dayBlocks(page, 0)).length === 4 && !(await page.$('.gw-free')), 'only you counted: your four classes draw and there is no green band (nobody to be free with)');
  const key = await page.evaluate(() => document.querySelector('.gw-key').innerText.replace(/\s+/g, ' '));
  ok(!/free/i.test(key), 'and the key does not claim anyone is free', key);
  await close();
});

test('mute', async () => {
  const { page, close } = await desk(); await tick(page, 1500);
  await openGroup(page, 'week');
  const before = (await dayBlocks(page, 0)).find(b => b.label.startsWith('BUS 4445'));
  ok(before.bg.includes('linear-gradient'), 'before: BUS 4445 is split you + Rowan');
  await page.click(`.gp-mem[onclick*="${ROWAN}"]`); await tick(page, 300);
  const after = (await dayBlocks(page, 0)).find(b => b.label.startsWith('BUS 4445'));
  const col = await page.evaluate(() => GW_COL.slice());
  ok(!after.bg.includes('linear-gradient') && after.bg.includes(hex2rgb(col[0])) && !/Rowan/.test(after.label), 'muting Rowan takes him out of the block: it is just yours', after);
  const tue = (await dayBlocks(page, 1)).map(b => b.label.split(',')[0]);
  ok(!(tue.includes('ECON 2303') && (await dayBlocks(page, 1)).filter(b => b.label.startsWith('ECON 2303')).length > 1), 'and his Tuesday ECON 2303 leaves the week', tue);
  const key = await page.evaluate(() => document.querySelector('.gw-key').innerText.replace(/\s+/g, ' '));
  ok(/Free for the 3 counted$/.test(key), 'the key recounts (3)', key);
  await close();
});

test('commitments', async () => {
  const { page, close, log } = await desk({ tables: withCm(), rpc: rpcBusy }); await tick(page, 1800);
  await openGroup(page, 'week');
  await page.evaluate(() => TCCommit.loadFriends(true)); await tick(page, 800);
  await page.evaluate(() => gpRenderDetail()); await tick(page, 300);
  const col = await page.evaluate(() => GW_COL.slice());
  const mon = await dayBlocks(page, 0);
  const bar = mon.find(b => b.cm);
  ok(bar && /^Barista/.test(bar.label) && /only you see this/.test(bar.label) && bar.text.startsWith('Barista') && bar.bgi.includes('repeating-linear-gradient') && bar.dcm === 'edit', 'your Work & activities draws by its name, hatched, and opens its editor', bar);
  const c31 = mon.find(b => b.label.startsWith('BUS 3431'));
  ok(bar && c31 && Math.abs(bar.w - c31.w) < 2 && Math.abs(bar.l - c31.l) > 20 && bar.w < 90, 'Barista (4–8p) and BUS 3431 (4:10–6p) overlap: they sit side by side, half a column each', [bar && bar.l, bar && bar.w, c31 && c31.l, c31 && c31.w]);
  const tue = await dayBlocks(page, 1);
  const busy = tue.find(b => b.cm);
  ok(busy && busy.text.startsWith('Busy') && /^Busy, 10a–12p, Avery/.test(busy.label) && busy.bg.includes(hex2rgb(col[1])), 'Avery’s shared Busy draws as “Busy” in Avery’s colour (label names whose, the block does not)', busy);
  const html = await page.evaluate(() => document.querySelector('.gw-wk').innerHTML);
  ok(!/Barista/.test(await page.evaluate(() => [...document.querySelectorAll('.gw-day')].filter((d, i) => i === 1).map(d => d.innerHTML).join())), 'your commitment’s name appears nowhere on a friend’s Busy', null);
  /* clicking */
  await page.locator('.gw-gb > .gw-day').nth(0).locator('.gw-b.cm').first().click(); await tick(page, 500);
  ok(await page.evaluate(() => document.getElementById('cmBack').classList.contains('open') && /Barista/.test(document.getElementById('cmName').value)), 'your Barista block opens it in Work & activities', null);
  await page.keyboard.press('Escape'); await tick(page, 300);
  await page.locator('.gw-gb > .gw-day').nth(1).locator('.gw-b.cm').first().click(); await tick(page, 600);
  const pf = await page.evaluate(() => ({ open: document.getElementById('frpBack').classList.contains('open'), id: profileFriendId }));
  ok(pf.open && pf.id === AVERY, 'Avery’s Busy block opens Avery’s page', pf);
  await page.evaluate(() => { document.getElementById('frpBack').classList.remove('open'); document.body.style.overflow = ''; }); await tick(page, 200);
  await page.evaluate(() => { PROFESSIFY_FLAGS.groups = true; show('friends'); gpSetTab('groups'); gpOpenGroup('g1'); }); await tick(page, 400);
  await page.locator('.gw-gb > .gw-day').nth(0).locator('.gw-b[onclick*="BUS 4442"]').click(); await tick(page, 700);
  const cp = await page.evaluate(() => ({ code: cpCode, view: [...document.querySelectorAll('.view.active, [id^="view-"].active')].map(v => v.id).join() }));
  ok(cp.code === 'BUS 4442', 'a class block opens that class’s page', cp);
  ok(log.errors.length === 0, 'no page errors', log.errors);
  await close();
});

const SPRING_CFG = { TERM: '2274', TERM_LABEL: 'Spring 2027', NOW_TERM: '2268', NOW_LABEL: 'Fall 2026', NOW_UNTIL: '2027-01-25' };
test('fall', async () => {
  const T2 = JSON.parse(JSON.stringify(FX.TABLES));
  const ph = T2.course_seats.find(r => r.course_code === 'BUS 4442');
  const sp = Object.assign({}, ph, { term: '2274', course_code: 'BUS 4401', days: 'FrSa 6:10PM - 9:00PM', class_nbr: '77001', section: '01' });
  T2.course_seats.push(sp);
  for (const uid of [ME, AVERY]) {
    T2.saved_classes.push({ user_id: uid, term: '2274', code: 'BUS 4401', class_nbr: sp.class_nbr, created_at: '2026-10-20T00:00:00Z', waitlist_pos: null });
    T2.my_sections.push({ user_id: uid, term: '2274', code: 'BUS 4401', class_nbr: sp.class_nbr, section: '01', instructor: sp.instructor, days: sp.days, status: 'enrolled', wl_pos: null });
  }
  const { page, close, log } = await desk({ terms: SPRING_CFG, tables: T2 }); await tick(page, 1800);
  await openGroup(page, 'week');
  const labels = await page.evaluate(() => [...document.querySelectorAll('.gw-b')].map(b => b.getAttribute('aria-label')));
  ok(labels.length > 8 && !labels.some(l => /BUS 4401/.test(l)), 'the week is the term people are in now (Fall): a Spring class never lands on it', labels.filter(l => /4401/.test(l)));
  ok(await page.evaluate(() => document.querySelector('.gw-cap').textContent) === 'Fall 2026', 'the week says which term it is (Fall 2026)');
  ok(labels.some(l => /^BUS 4442, 12:10p–2p/.test(l)), 'Fall times are the Fall section’s', labels.filter(l => /4442/.test(l)));
  ok(log.errors.length === 0, 'no page errors', log.errors);
  await close();
});

/* WCAG contrast of text on what is really behind it (the block's own colours, theme tokens under translucent fills) */
const CONTRAST = `window.__rgb = s => { const c = document.createElement('canvas').getContext('2d'); c.fillStyle = '#000'; c.fillStyle = s; c.fillRect(0,0,1,1); const d = c.getImageData(0,0,1,1).data; return [d[0],d[1],d[2],d[3]/255]; };
window.__L = a => { const f = v => { v /= 255; return v <= .03928 ? v / 12.92 : Math.pow((v + .055) / 1.055, 2.4); }; return .2126*f(a[0]) + .7152*f(a[1]) + .0722*f(a[2]); };
window.__ratio = (a, b) => { const x = __L(a), y = __L(b); return (Math.max(x,y)+.05)/(Math.min(x,y)+.05); };
window.__behind = el => { let layers = []; for (let n = el; n; n = n.parentElement) { const bg = getComputedStyle(n).backgroundColor; const c = __rgb(bg); if (c[3] > 0) { layers.push(c); if (c[3] >= 1) break; } } let base = [255,255,255]; layers.reverse().forEach(c => { base = base.map((v, i) => Math.round(c[i] * c[3] + v * (1 - c[3]))); }); return base; };`;
for (const theme of ['light', 'dark']) {
  test('contrast-' + theme, async () => {
    const { page, close } = await desk({ tables: withCm(), rpc: rpcBusy, init: seed(withTheme(theme)) }); await tick(page, 1800);
    await openGroup(page, 'week'); await page.evaluate(() => TCCommit.loadFriends(true)); await tick(page, 700); await page.evaluate(() => { gpRenderDetail(); }); await tick(page, 300);
    await page.evaluate(CONTRAST);
    ok(await page.evaluate(() => document.documentElement.getAttribute('data-theme')) === theme, theme + ': the page is in the theme');
    const r = await page.evaluate(() => {
      const out = { cols: [], texts: [] };
      GW_COL.forEach(c => { out.cols.push([c, +__ratio(__rgb('#fff'), __rgb(c)).toFixed(2)]); });
      /* each real block: its first colour stop under its white text, with the hatch darkening it */
      document.querySelectorAll('.gw-b').forEach(b => {
        const cols = (b.style.background.match(/rgb\([^)]*\)/g) || []);
        cols.forEach(c => { const rg = __rgb(c); const worst = b.classList.contains('cm') ? rg.map(v => Math.round(v * .8)) : rg; out.texts.push(['block ' + b.getAttribute('aria-label').slice(0, 20), +__ratio(__rgb('#fff'), worst).toFixed(2)]); });
      });
      const t = (sel, name) => document.querySelectorAll(sel).forEach(e => { const fg = __rgb(getComputedStyle(e).color); out.texts.push([name, +__ratio(fg, __behind(e)).toFixed(2)]); });
      t('.gw-dh', 'day heading'); t('.gw-dh.td', 'today'); t('.gw-t', 'hour label'); t('.gw-free span', 'free band'); t('.gw-key', 'key'); t('.gw-cap', 'term caption'); t('.gw-sb', 'switch'); t('.gw-sb.on', 'switch on');
      document.querySelectorAll('.gp-mem .gp-av').forEach(e => { const fg = __rgb(getComputedStyle(e).color); out.texts.push(['legend initials', +__ratio(fg, __behind(e)).toFixed(2)]); });
      return out;
    });
    const bad = r.cols.concat(r.texts).filter(x => x[1] < 4.5);
    ok(bad.length === 0 && r.texts.length > 20, theme + ': every colour holds 4.5:1 under its text (' + r.texts.length + ' checked)', bad.slice(0, 6));
    await close();
  });
}

const names = ONLY ? [ONLY] : Object.keys(T);
for (const n of names) {
  if (!T[n]) { console.log('no such test', n); process.exit(2); }
  if (!QUIET) console.log('\n' + n);
  try { await T[n](); } catch (e) { fail++; fails.push(n + ' threw'); console.log('  FAIL', n, 'threw', String(e).slice(0, 300)); }
  for (const a of open.splice(0)) { try { await a.close(); } catch (e) {} }
}
console.log(`\ncheck-desktop-group-week: ${pass} passed, ${fail} failed`);
if (fail) { console.log('failed:', fails.join(' | ')); process.exit(1); }
