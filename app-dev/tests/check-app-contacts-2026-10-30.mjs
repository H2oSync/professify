/* Tate, 2026-10-30: Connect contacts (the signed-off mockups). Friends header pill, the Connect sheet,
   results (On TermChamp / Invite), Add and Add all, the Messages invite, the one-time pop-up (after
   onboarding behind the push ask; existing students on a later open; Not now = 30 days), the sign-up
   phone step, the results-sheet "add your number" row, Settings › Contacts, the fallback before the SQL
   has run, the website, a fake native plugin (granted / limited / denied), light + dark, 375px.
   Run from app-dev/tests: APP_DIR=<site> APP_PORT=89xx node check-app-contacts-2026-10-30.mjs */
import { openApp } from './app-harness.mjs';
import * as FX from './app-fixtures.mjs';
import { createHash } from 'node:crypto';
let pass = 0, fail = 0; const ok = (c, m, d) => { if (c) { pass++; console.log('  ok  ', m); } else { fail++; console.log('  FAIL', m, JSON.stringify(d)); } };
const SHOTS = process.env.SHOTS || '/tmp/claude-0/fix/contacts/shots';
const sha = t => createHash('sha256').update(t).digest('hex');
const settle = async (p, ms = 400) => { await p.clock.runFor(ms); await p.waitForTimeout(250); await p.clock.runFor(50); await p.waitForTimeout(100); };
const click = async (p, sel) => { await p.locator(sel).first().click(); await settle(p); };
const sheetText = p => p.locator('#sheet').innerText();
const NEWBIE = { id: '44444444-4444-4444-8444-444444444441', display_name: 'Jordan Rivera', username: 'jrivera', avatar_url: null };
const NEWBIE2 = { id: '44444444-4444-4444-8444-444444444442', display_name: 'Priya Patel', username: 'ppatel', avatar_url: null };
/* the preview's sample book: Jordan (805) 555-0101 and Priya 805-555-0102 are on TermChamp; so are a friend and Morgan (asked me) */
const MATCHES = [
  Object.assign({}, NEWBIE, { matched: [sha('+18055550101')] }), Object.assign({}, NEWBIE2, { matched: [sha('+18055550102')] }),
  { id: FX.FRIENDS[0].id, display_name: FX.FRIENDS[0].display_name, username: FX.FRIENDS[0].username, avatar_url: null, matched: [sha('+18055550103')] },
  { id: FX.STRANGER.id, display_name: FX.STRANGER.display_name, username: FX.STRANGER.username, avatar_url: null, matched: [] }];
const rpcWith = extra => Object.assign({}, FX.RPC, { match_contacts: MATCHES, my_phone_saved: false, set_my_phone: true }, extra || {});
const missing = fn => (url, m) => url.pathname === '/rest/v1/rpc/' + fn ? { status: 404, body: JSON.stringify({ code: 'PGRST202', details: null, hint: null, message: `Could not find the function public.${fn} in the schema cache` }) } : null;
const st = p => p.evaluate(() => ctState());
const noOverflow = p => p.evaluate(() => { const w = document.documentElement.clientWidth; const bad = [...document.querySelectorAll('#sheet *, .fhdr *')].filter(e => { const r = e.getBoundingClientRect(); return r.width && (r.right > w + 0.5 || r.left < -0.5); }).map(e => e.className || e.tagName); return { sw: document.documentElement.scrollWidth, w, bad: bad.slice(0, 5) }; });

/* ---------- 1. Friends header, the Connect sheet, results, Add / Add all, Invite (phone preview, 375px) */
{
  const { page, close, log } = await openApp({ width: 375, height: 812, rpc: rpcWith() });
  await click(page, '[data-a="tab"][data-x="friends"]');
  const hdr = await page.evaluate(() => { const b = [...document.querySelectorAll('.fhdr .invpill')]; return b.map(x => ({ a: x.dataset.a, x: x.dataset.x || '', t: x.textContent.trim(), bg: getComputedStyle(x).backgroundColor, left: x.getBoundingClientRect().left, svg: !!x.querySelector('svg') })); });
  ok(hdr.length === 2 && hdr[0].t === 'Contacts' && hdr[0].a === 'ctOpen' && hdr[1].t === 'Invite' && hdr[1].x === 'invite' && hdr[0].left < hdr[1].left, 'header: blue Contacts pill to the LEFT of Invite; Invite unchanged', hdr);
  ok(hdr[0].bg === 'rgb(37, 99, 235)' && hdr[1].bg !== hdr[0].bg && hdr[0].svg, 'header: Contacts is blue with the people icon, Invite stays pink', hdr);
  ok((await noOverflow(page)).sw <= 375, 'header: fits 375px', await noOverflow(page));
  await page.locator('.fhdr').screenshot({ path: SHOTS + '/friends-header-light.png' });
  await click(page, '[data-a="ctOpen"]');
  let t = await sheetText(page);
  ok(/Connect contacts/.test(t) && /Find your friends/.test(t) && /See who in your contacts is already on TermChamp\./.test(t) && /You can turn this off any time in Settings\./.test(t), 'connect sheet: title, line, fine print', t);
  ok(!/hash|scrambl/i.test(t) && !/Not now/.test(t) && await page.locator('#sheet .ct-tile').count() === 1 && await page.locator('#sheet .btn[data-a="ctConnect"]').count() === 1, 'connect sheet: no hashing talk, no Not now from the pill, the 72px tile and the blue button', t);
  ok(await page.evaluate(() => { const e = document.querySelector('#sheet .ct-tile'); const r = e.getBoundingClientRect(); return r.width === 72 && r.height === 72; }), 'connect sheet: the tile is 72px');
  await page.locator('#sheet .sheet').screenshot({ path: SHOTS + '/connect-sheet-light.png' });
  await click(page, '[data-a="ctConnect"]'); await settle(page, 800);
  t = await sheetText(page);
  const sent = log.rpcs.filter(r => r.fn === 'match_contacts');
  const hashes = sent.flatMap(r => r.body.hashes);
  ok(sent.length === 1 && hashes.length === 9 && hashes.every(h => /^[0-9a-f]{64}$/.test(h)), 'connect: one call, 9 hashes (the sample book), all SHA-256 hex', { n: sent.length, h: hashes.length });
  ok(['+18055550101', '+18055550103', '+16195550105', '+17605550106', '+18585550107'].every(e => hashes.includes(sha(e))), 'connect: (805) 555-0101, +1 805 555 0103, 760.555.0106, 1 (858) 555-0107 → E.164 before hashing');
  ok(!/555|Jordan|Priya|Rivera/.test(JSON.stringify(sent)), 'connect: no number or name leaves the phone');
  ok(/Your contacts/.test(t) && /On TermChamp · 4/.test(t) && /Invite · 6/.test(t), 'results: On TermChamp · 4 and Invite · 6 (matched people left out of Invite)', t);
  ok(/@jrivera/.test(t) && /Friends/.test(t) && /Accept/.test(t) && await page.locator('#sheet [data-a="addFriend"]').count() === 2 && await page.locator('#sheet [data-a="ctAddAll"]').count() === 1, 'results: Add ×2, Friends, Accept, and Add all', t);
  ok(await page.locator('#sheet [data-a="ctInvite"]').count() === 5 && /See all 6/.test(t), 'results: 5 to invite, then See all 6', t);
  ok(await page.locator('#sheet .ct-mine').count() === 1 && /Add your number so friends can find you too/.test(t), 'results: number not added → the one small row', t);
  await page.locator('#sheet .sheet').screenshot({ path: SHOTS + '/results-sheet-light.png' });
  ok((await noOverflow(page)).bad.length === 0, 'results: nothing wider than 375px', await noOverflow(page));
  await click(page, '#sheet [data-a="ctAll"]');
  ok(await page.locator('#sheet [data-a="ctInvite"]').count() === 6 && !/See all/.test(await sheetText(page)), 'See all shows all 6');
  /* Add one, then Add all */
  await click(page, `#sheet [data-a="addFriend"][data-x="${NEWBIE.id}"]`); await settle(page, 500);
  let fr = log.writes.filter(w => w.table === 'friend_requests' && w.m === 'POST');
  ok(fr.length === 1 && fr[0].body.to_user === NEWBIE.id && fr[0].body.from_user === FX.ME.id && fr[0].body.status === 'pending', 'Add: one pending friend request', fr.map(x => x.body));
  ok(/Requested/.test(await page.locator(`#sheet .ct-row:has([data-x="${NEWBIE.id}"])`).innerText()), 'Add: turns to Requested');
  ok(await page.locator('#sheet [data-a="ctAddAll"]').count() === 0, 'Add all hides when only one is left to add');
  await page.evaluate(() => { UI.ct.rows.push('33333333-3333-4333-8333-333333333332'); PEOPLE['33333333-3333-4333-8333-333333333332'] = PEOPLE['33333333-3333-4333-8333-333333333332'] || personFrom({ id: '33333333-3333-4333-8333-333333333332', display_name: 'Pat Suggestia', username: 'psuggest' }); render(true); });
  await click(page, '#sheet [data-a="ctAddAll"]'); await settle(page, 800);
  fr = log.writes.filter(w => w.table === 'friend_requests' && w.m === 'POST');
  ok(fr.length === 3 && fr.slice(1).map(x => x.body.to_user).sort().join() === [NEWBIE2.id, FX.SUGGESTED.id].sort().join() && !fr.some(x => x.body.to_user === FX.FRIENDS[0].id || x.body.to_user === FX.STRANGER.id), 'Add all: requests the two left, never a friend or someone who asked me', fr.map(x => x.body.to_user));
  /* Invite → Messages */
  await page.evaluate(() => { window.__go = []; TC.ctGo = u => window.__go.push(u); });
  await click(page, '#sheet [data-a="ctInvite"]');
  let go = await page.evaluate(() => window.__go);
  const body = 'Hey! I’m using TermChamp to plan classes and see when friends are free. Add me: ' + await page.evaluate(() => inviteUrl());
  ok(go.length === 1 && go[0] === 'sms:+18585550107?body=' + encodeURIComponent(body), 'Invite (not iOS): sms:<E.164>?body=<the text + invite link>', go);
  ok(/Invited/.test(await page.locator('#sheet .ct-row:has([data-a="ctInvite"])').first().innerText()), 'Invite: the button says Invited after');
  ok(log.errors.length === 0, 'part 1: no page errors', log.errors);
  await close();
}
/* ---------- 2. iPhone: sms: with &body=, fake native plugin (permission prompt, re-read each time, limited, denied) */
{
  const init = () => {
    Object.defineProperty(navigator, 'userAgent', { get: () => 'Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148' });
    window.__ct = { perm: 'prompt', ask: 0, reads: 0, grant: 'granted' };
    const C = { checkPermissions: () => Promise.resolve({ contacts: __ct.perm }), requestPermissions: () => { __ct.ask++; __ct.perm = __ct.grant; return Promise.resolve({ contacts: __ct.perm }); },
      getContacts: o => { __ct.reads++; __ct.proj = o.projection; return Promise.resolve({ contacts: [
        { contactId: 'a', name: { display: 'Jordan Rivera' }, phones: [{ number: '(805) 555-0101' }], emails: [{ address: ' JR@Example.COM ' }] },
        { contactId: 'b', name: { given: 'Quinn', family: 'Ashby' }, phones: [{ number: '805.555.0199 ext 4' }, { number: '+44 20 7946 0958' }], emails: [] },
        { contactId: 'c', name: { display: 'No Number' }, phones: [], emails: [{ address: 'nonum@calpoly.edu' }] },
        { contactId: 'd', name: { display: 'Junk' }, phones: [{ number: '911' }], emails: [{ address: 'not an email' }] }] }); } };
    window.Capacitor = { isNativePlatform: () => true, getPlatform: () => 'ios', Plugins: { Contacts: C, StatusBar: { setStyle: () => Promise.resolve() },
      PushNotifications: { checkPermissions: () => Promise.resolve({ receive: 'granted' }), register: () => Promise.resolve(), addListener: () => {} } } };
  };
  const { page, close, log } = await openApp({ init, rpc: rpcWith({ match_contacts: [Object.assign({}, NEWBIE, { matched: [sha('jr@example.com')] })], my_phone_saved: true }) });
  await page.evaluate(() => { TC.ctPreview = () => false; });
  await click(page, '[data-a="tab"][data-x="friends"]'); await click(page, '[data-a="ctOpen"]'); await click(page, '[data-a="ctConnect"]'); await settle(page, 800);
  let n = await page.evaluate(() => window.__ct);
  const hashes = log.rpcs.filter(r => r.fn === 'match_contacts').flatMap(r => r.body.hashes);
  ok(n.ask === 1 && n.reads === 1 && n.proj.phones && n.proj.emails && n.proj.name && !n.proj.image, 'native: asks iOS once, then reads names, numbers and emails (no photos)', n);
  ok(hashes.length === 5 && [sha('+18055550101'), sha('jr@example.com'), sha('+18055550199'), sha('+442079460958'), sha('nonum@calpoly.edu')].every(h => hashes.includes(h)), 'native: ext dropped, +44 kept, email lower-cased + trimmed, 911 and junk email dropped', hashes.length);
  let t = await sheetText(page);
  ok(/On TermChamp · 1/.test(t) && /Invite · 1/.test(t) && /Quinn Ashby/.test(t) && !/No Number/.test(t), 'native: Jordan matched by email; Quinn to invite; an email-only contact can’t get a text', t);
  ok(await page.locator('#sheet .ct-mine').count() === 0, 'number already saved → no "add your number" row');
  await page.evaluate(() => { window.__go = []; TC.ctGo = u => window.__go.push(u); });
  await click(page, '#sheet [data-a="ctInvite"]');
  const go = await page.evaluate(() => window.__go);
  ok(go.length === 1 && go[0].startsWith('sms:+18055550199&body=Hey!%20I%E2%80%99m%20using%20TermChamp') && go[0].includes(encodeURIComponent('/invite?add=' + FX.ME.id)), 'iPhone: sms:<number>&body=… with the invite link', go);
  await click(page, '#sheet .xbtn[data-a="closeSheet"]');
  await click(page, '[data-a="ctOpen"]'); await settle(page, 800);
  n = await page.evaluate(() => window.__ct);
  ok(await page.evaluate(() => UI.sheet && UI.sheet.type) === 'ctResults' && n.reads === 2 && n.ask === 1, 'connected: Contacts opens the results directly and reads the book again (no second ask)', n);
  /* iOS 18 limited access */
  await page.evaluate(() => { __ct.perm = 'limited'; }); await click(page, '#sheet .xbtn[data-a="closeSheet"]'); await click(page, '[data-a="ctOpen"]'); await settle(page, 800);
  ok(/You shared some of your contacts/.test(await sheetText(page)), 'limited access: works, with a line on changing which');
  /* turned off in iPhone Settings */
  await page.evaluate(() => { __ct.perm = 'denied'; }); await click(page, '#sheet .xbtn[data-a="closeSheet"]'); await click(page, '[data-a="ctOpen"]'); await settle(page, 800);
  t = await sheetText(page);
  ok(/Contacts are off for TermChamp/.test(t) && /Connect contacts/.test(t) && !(await st(page)).on, 'denied later: back to Connect with how to turn it on', t);
  await page.evaluate(() => { __ct.grant = 'denied'; }); await click(page, '[data-a="ctConnect"]');
  ok(/Contacts are off for TermChamp/.test(await sheetText(page)) && await page.evaluate(() => UI.sheet.type) === 'ctConnect', 'denied at the prompt: stays on Connect and says so');
  ok(log.errors.length === 0, 'part 2: no page errors', log.errors);
  await close();
}
/* ---------- 3. before the SQL has run; the real website */
{
  let nMatch = 0;
  const { page, close, log } = await openApp({ hook: (u, m) => { if (u.pathname === '/rest/v1/rpc/match_contacts') nMatch++; return missing('match_contacts')(u, m) || missing('my_phone_saved')(u, m); } });
  await click(page, '[data-a="tab"][data-x="friends"]'); await click(page, '[data-a="ctOpen"]'); await click(page, '[data-a="ctConnect"]'); await settle(page, 800);
  const t = await sheetText(page);
  ok(/Contact matching isn’t available yet\./.test(t) && /Invite · 9/.test(t) && !/On TermChamp/.test(t) && !/Couldn’t/.test(t), 'RPC missing (404 PGRST202): "isn’t available yet", and the Invite list still works', t);
  ok(await page.locator('#sheet .ct-mine').count() === 0, 'RPC missing: no "add your number" row either');
  await page.evaluate(() => { TC.ctPreview = () => false; ctSet({ on: false }); UI.sheet = { type: 'ctConnect' }; render(true); });
  await settle(page);
  await click(page, '[data-a="ctConnect"]');
  ok(/Contacts sync is in the iPhone app\./.test(await sheetText(page)) && nMatch === 1, 'website: Connect says it’s in the iPhone app, and reads nothing');
  ok(await page.evaluate(() => ctAsk('later')) === false, 'website: never pops up');
  ok(log.errors.length === 0, 'part 3: no page errors', log.errors);
  await close();
}
/* ---------- 4. the pop-up: after onboarding, behind the push ask */
{
  const init = () => { window.__push = 'prompt';
    window.Capacitor = { isNativePlatform: () => true, getPlatform: () => 'ios', Plugins: { StatusBar: { setStyle: () => Promise.resolve() },
      Contacts: { checkPermissions: () => Promise.resolve({ contacts: 'prompt' }), requestPermissions: () => Promise.resolve({ contacts: 'granted' }), getContacts: () => Promise.resolve({ contacts: [] }) },
      PushNotifications: { checkPermissions: () => Promise.resolve({ receive: window.__push }), requestPermissions: () => new Promise(r => setTimeout(() => { window.__push = 'granted'; r({ receive: 'granted' }); }, 3000)), register: () => Promise.resolve(), addListener: () => {} } } }; };
  const { page, close, log } = await openApp({ init, rpc: rpcWith() });
  await page.evaluate(() => { S.stack.home.push({ s: 'onb', p: { step: 'payoff' } }); render(); }); await settle(page, 400);
  await click(page, '[data-a="onbFinish"][data-x="home"]'); await settle(page, 1200);
  ok(await page.evaluate(() => UI.sheet && UI.sheet.type) === 'pushAsk' && await page.evaluate(() => UI.sheetNext) === 'ctAsk', 'after onboarding: the push ask first, contacts queued behind it (not stacked)');
  await click(page, '[data-a="pushAllow"]'); await settle(page, 1500);
  ok(await page.evaluate(() => !UI.sheet && UI.sheetNext === 'ctAsk'), 'while iOS’s own notification prompt is up, contacts waits');
  await settle(page, 2500); await settle(page, 600);
  let sh = await page.evaluate(() => UI.sheet);
  ok(sh && sh.type === 'ctConnect' && sh.pop, 'then the contacts pop-up', sh);
  const t = await sheetText(page);
  ok(/Find your friends/.test(t) && /Not now/.test(t) && /Connect contacts/.test(t) && !t.split('Find your friends')[0].includes('Connect contacts'), 'pop-up: the same sheet plus Not now', t);
  await page.locator('#sheet .sheet').screenshot({ path: SHOTS + '/popup-sheet-light.png' });
  await click(page, '[data-a="ctNotNow"]');
  const s1 = await st(page), now = await page.evaluate(() => Date.now());
  ok(!(await page.evaluate(() => UI.sheet)) && s1.snooze - now > 29.9 * 864e5 && s1.snooze - now <= 30 * 864e5, 'Not now: closes, and not again for 30 days', s1);
  ok(await page.evaluate(() => ctAsk('later')) === false, 'Not now: a later ask does nothing');
  await page.evaluate(() => ctSet({ snooze: Date.now() - 1 }));
  ok(await page.evaluate(() => ctAsk('later')) === true, '30 days later it may ask once more');
  await click(page, '[data-a="ctConnect"]'); await settle(page, 600);
  ok((await st(page)).on === true && await page.evaluate(() => UI.sheet.type) === 'ctResults', 'Connect from the pop-up: results');
  await page.evaluate(() => { UI.sheet = null; render(true); ctSet({ snooze: 0 }); });
  ok(await page.evaluate(() => ctAsk('later')) === false, 'connected: never asks again');
  ok(log.errors.length === 0, 'part 4: no page errors', log.errors);
  await close();
}
/* ---------- 5. the pop-up for students who already have an account: 2nd open, on Home */
{
  const { page, ctx, close, log } = await openApp({ rpc: rpcWith() });
  ok(!(await page.evaluate(() => UI.sheet)) && (await st(page)).n === 1, 'existing student, 1st open: counted, no pop-up', await st(page));
  await page.reload(); await settle(page, 2500); await settle(page, 2600); await settle(page, 400);
  let sh = await page.evaluate(() => UI.sheet);
  ok(sh && sh.type === 'ctConnect' && sh.pop && (await st(page)).n === 2, '2nd open, on Home: the pop-up', { sh, st: await st(page) });
  await page.locator('#sheet .scrim').click({ position: { x: 10, y: 10 } }); await settle(page);
  await page.reload(); await settle(page, 2500); await settle(page, 2600);
  ok(!(await page.evaluate(() => UI.sheet)), 'closed without choosing (scrim): counts as Not now — 3rd open, nothing');
  /* not on Home → waits */
  await page.evaluate(() => ctSet({ snooze: 0 }));
  await page.reload(); await page.clock.runFor(1200); await page.waitForTimeout(150);
  await page.evaluate(() => setTab('explore')); await settle(page, 2600); await settle(page, 2600);
  { const z = await st(page); ok(!(await page.evaluate(() => UI.sheet && UI.sheet.type === 'ctConnect')) && !z.snooze && z.n === 4, 'not on Home: no pop-up (4th open counted, never shown)', z); }
  /* another sheet open → no stacking */
  await page.evaluate(() => { S.tab = 'home'; save(); }); await page.reload(); await page.clock.runFor(1500); await page.waitForTimeout(200);
  await page.evaluate(() => { UI.sheet = { type: 'invite' }; render(true); }); await settle(page, 2000); await settle(page, 600);
  ok(await page.evaluate(() => UI.sheet.type) === 'invite', 'another sheet open: the pop-up never covers it');
  ok(log.errors.length === 0, 'part 5: no page errors', log.errors);
  await close();
}
/* ---------- 6. sign-up: the phone step after year/major; Settings › Contacts; the results row */
{
  const { page, close, log } = await openApp({ rpc: rpcWith() });
  await page.evaluate(() => { S.stack.home.push({ s: 'onb', p: { step: 'confirm' } }); UI.onbPre = { major: 'Business Administration', standing: 'Junior', conc: '' }; render(); }); await settle(page, 1500);
  await click(page, '[data-a="onbConfirmDone"]'); await settle(page, 800);
  let t = await page.locator('#scroll').innerText();
  ok(/Help friends find you/.test(t) && /Friends who have your number saved will see you on TermChamp\./.test(t) && /Only used to find friends\. Never shown on your profile\./.test(t) && /Continue/.test(t) && /Skip/.test(t), 'sign-up: "Help friends find you" right after year and major', t.slice(0, 400));
  const inp = await page.evaluate(() => { const i = document.getElementById('ob-phone'); return i && { type: i.type, im: i.inputMode, ac: i.autocomplete, cc: i.parentElement.querySelector('.at').textContent }; });
  ok(inp && inp.type === 'tel' && inp.im === 'tel' && inp.ac === 'tel' && inp.cc === '+1', 'phone field: +1, type/inputmode/autocomplete tel', inp);
  await page.screenshot({ path: SHOTS + '/onboarding-phone-step-light.png' });
  ok(await page.evaluate(() => JSON.parse(localStorage.getItem('termchamp_app_onb')).step) === 'phone', 'the step is remembered if the app closes');
  await page.locator('#ob-phone').fill('805 55'); await click(page, '.onb .foot .btn');
  ok(/Enter a 10-digit US number/.test(await page.locator('#ob-phoneerr').innerText()) && !log.rpcs.some(r => r.fn === 'set_my_phone'), 'a short number: says so, sends nothing');
  await page.locator('#ob-phone').fill('(805) 555-0134'); await click(page, '.onb .foot .btn'); await settle(page, 600);
  const set = log.rpcs.filter(r => r.fn === 'set_my_phone');
  ok(set.length === 1 && set[0].body.p_hash === sha('+18055550134') && !/555/.test(JSON.stringify(set[0].body)), 'Continue: set_my_phone gets only the SHA-256 of +18055550134', set.map(x => x.body));
  ok(/People you may know/.test(await page.locator('#scroll').innerText()), 'Continue: on to People you may know');
  await click(page, '[data-a="onbBack"]');
  ok(/Your number is saved/.test(await page.locator('#scroll').innerText()), 'Back: the step shows the number is saved');
  await click(page, '[data-a="onbBack"]');
  ok(/Does this look right\?/.test(await page.locator('#scroll').innerText()), 'Back again: year and major');
  await page.evaluate(() => { TC.phoneSaved = false; }); await click(page, '[data-a="onbConfirmDone"]'); await settle(page, 800);
  await click(page, '[data-a="ctPhoneSkip"]');
  ok(/People you may know/.test(await page.locator('#scroll').innerText()) && log.rpcs.filter(r => r.fn === 'set_my_phone').length === 1, 'Skip: on to People, nothing sent');
  /* Settings › Contacts */
  await page.evaluate(() => { onbRemember(null); S.stack.home = [{ s: 'home' }]; S.tab = 'home'; render(); TC.phoneSaved = undefined; });
  log.rpcs.length = 0;
  await page.evaluate(() => A.openSettings()); await settle(page, 800);
  t = await page.locator('#scroll').innerText();
  ok(/CONTACTS/i.test(t) && /Your phone number\s*Not added/.test(t) && /Find friends from contacts\s*Not connected/.test(t) && log.rpcs.some(r => r.fn === 'my_phone_saved'), 'Settings › Contacts: number not added, not connected', t.slice(t.search(/contacts/i), t.search(/contacts/i) + 200));
  await click(page, '.ct-set [data-a="ctPhoneSheet"]');
  t = await sheetText(page);
  ok(/Help friends find you/.test(t) && /Skip/.test(t) && await page.locator('#ctPhoneIn[type="tel"][autocomplete="tel"][inputmode="tel"]').count() === 1, 'Settings › Add: the same step as a sheet', t);
  await page.locator('#ctPhoneIn').fill('+1 (805) 555-0177'); await click(page, '#sheet .btn:not(.ghost)'); await settle(page, 600);
  ok(log.rpcs.filter(r => r.fn === 'set_my_phone').pop().body.p_hash === sha('+18055550177') && !(await page.evaluate(() => UI.sheet)), 'sheet: saves the hash and closes');
  ok(/Your phone number\s*Added · ending in 0177/.test(await page.locator('#scroll').innerText()), 'Settings: "Added · ending in 0177"');
  await click(page, '.ct-set [data-a="ctPhoneRemove"]'); await settle(page, 600);
  ok(log.rpcs.filter(r => r.fn === 'set_my_phone').pop().body.p_hash === '' && /Your phone number\s*Not added/.test(await page.locator('#scroll').innerText()), 'Settings › Remove: set_my_phone(\'\') and back to Not added');
  /* the results row opens the same step, and comes back to the results */
  await click(page, '.ct-set [data-a="ctOpen"]'); await click(page, '[data-a="ctConnect"]'); await settle(page, 800);
  await click(page, '#sheet .ct-mine');
  ok(await page.evaluate(() => UI.sheet.type === 'ctPhone' && UI.sheet.ret === 'ctResults'), 'results row: opens the phone sheet');
  await click(page, '#sheet .btn.ghost[data-a="ctPhoneBack"]');
  ok(await page.evaluate(() => UI.sheet.type) === 'ctResults', 'Skip there: back to the results');
  await click(page, '#sheet .xbtn[data-a="closeSheet"]');
  await page.evaluate(() => A.openSettings()); await settle(page, 400);
  ok(/Find friends from contacts\s*Connected on this phone/.test(await page.locator('#scroll').innerText()), 'Settings: Connected on this phone');
  await click(page, '.ct-set [data-a="ctForget"]');
  ok(/Find friends from contacts\s*Not connected/.test(await page.locator('#scroll').innerText()) && !(await st(page)).on, 'Settings › Turn off: not connected');
  ok(log.errors.length === 0, 'part 6: no page errors', log.errors);
  await close();
}
{
  const { page, close, log } = await openApp({ hook: u => u.pathname === '/rest/v1/rpc/set_my_phone' ? { status: 409, body: JSON.stringify({ code: '23505', message: 'That number is already on another TermChamp account.', details: null, hint: null }) } : null, rpc: rpcWith() });
  await page.evaluate(() => { UI.sheet = { type: 'ctPhone' }; render(true); }); await settle(page);
  await page.locator('#ctPhoneIn').fill('8055550134'); await click(page, '#sheet .btn:not(.ghost)'); await settle(page, 400);
  ok(/already on another TermChamp account/.test(await sheetText(page)) && await page.evaluate(() => UI.sheet.type) === 'ctPhone', 'a number on another account: says so, stays open');
  ok(log.errors.length === 0, 'part 7: no page errors', log.errors);
  await close();
}
/* ---------- 8. dark mode, 375px: the same screens */
{
  const init = () => { try { localStorage.setItem('tc-theme', 'dark'); } catch (e) {} };
  const { page, close, log } = await openApp({ init, width: 375, height: 812, rpc: rpcWith() });
  ok(await page.evaluate(() => document.documentElement.getAttribute('data-theme')) === 'dark', 'dark: on');
  await click(page, '[data-a="tab"][data-x="friends"]');
  await page.locator('.fhdr').screenshot({ path: SHOTS + '/friends-header-dark.png' });
  await click(page, '[data-a="ctOpen"]');
  const cs = await page.evaluate(() => { const t = document.querySelector('#sheet .ct-tile'), b = document.querySelector('#sheet .sheet'); return { tile: getComputedStyle(t).backgroundColor, sheet: getComputedStyle(b).backgroundColor, ink: getComputedStyle(document.querySelector('#sheet h3')).color }; });
  ok(cs.tile !== 'rgb(227, 236, 255)' && cs.sheet !== 'rgb(255, 255, 255)', 'dark: the tile and sheet follow dark tokens', cs);
  await page.locator('#sheet .sheet').screenshot({ path: SHOTS + '/connect-sheet-dark.png' });
  await click(page, '[data-a="ctConnect"]'); await settle(page, 800);
  ok((await noOverflow(page)).bad.length === 0 && (await noOverflow(page)).sw <= 375, 'dark 375px: results fit', await noOverflow(page));
  await page.locator('#sheet .sheet').screenshot({ path: SHOTS + '/results-sheet-dark.png' });
  await page.evaluate(() => { UI.sheet = null; S.stack.home.push({ s: 'onb', p: { step: 'phone' } }); S.tab = 'home'; render(); }); await settle(page, 600);
  ok(/Help friends find you/.test(await page.locator('#scroll').innerText()) && (await page.evaluate(() => document.documentElement.scrollWidth)) <= 375, 'dark 375px: the phone step (onboarding stays light, as all of it does)');
  await page.screenshot({ path: SHOTS + '/onboarding-phone-step-375-dark.png' });
  ok(log.errors.length === 0, 'part 8: no page errors', log.errors);
  await close();
}
console.log(`contacts: ${pass} passed, ${fail} failed`);
process.exit(fail ? 1 : 0);
