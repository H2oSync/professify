/* Tate, 2026-10-31: contacts v2, the designs he picked in mock/contacts.html.
   1a  the sign-up phone step ("What's your number?", Continue, a quiet "Not now" that sends nothing)
   1b  students already signed up with no number (TC.phoneSaved === false): a small "Add your number" pop-up
       through the pop-up queue: Home only, never in onboarding, the day's one pop-up, twice in all, 7+ days
       apart, after "Connect contacts" and before notifications; never when the server can't say (null) or
       the number is saved (true); Save calls set_my_phone with the hash only.
   A   the synced list: a full page, search (both sections), On TermChamp (Add / Requested / Friends / Accept),
       Invite to TermChamp A to Z (case and accents ignored) with number-only contacts last under "Other
       numbers", duplicates listed once, sticky letters, the A-Z scrubber (tap, drag, empty letters dimmed and
       skipped), 1,500 contacts fast, light + dark at 390px with readable contrast.
   Run from app-dev/tests: APP_DIR=<site> APP_PORT=97xx node check-contacts-v2-2026-10-31.mjs */
import { openApp } from './app-harness.mjs';
import * as FX from './app-fixtures.mjs';
import { createHash } from 'node:crypto';
import fs from 'node:fs';
let pass = 0, fail = 0; const ok = (c, m, d) => { if (c) { pass++; console.log('  ok  ', m); } else { fail++; console.log('  FAIL', m, d === undefined ? '' : JSON.stringify(d)); } };
const SHOTS = process.env.SHOTS || '/tmp/claude-0/ct2/shots/test'; fs.mkdirSync(SHOTS, { recursive: true });
const PORT = +(process.env.APP_PORT || 9760);
const sha = t => createHash('sha256').update(t).digest('hex');
const DAY = 864e5, T0 = Date.parse('2026-09-29T10:30:00-07:00');   /* the harness's page clock at launch */
const run = (p, ms) => p.clock.runFor(ms);
const settle = async (p, ms = 400) => { await run(p, ms); await p.waitForTimeout(250); await run(p, 50); await p.waitForTimeout(100); };
const click = async (p, sel) => { await p.locator(sel).first().click(); await settle(p); };
const sheetType = p => p.evaluate(() => UI.sheet && UI.sheet.type);
async function readyOf(page) { for (let i = 0; i < 100; i++) { if (await page.evaluate(() => { try { return !!TC.ready; } catch (e) { return false; } }).catch(() => false)) return true; await run(page, 100); await page.waitForTimeout(30); } return false; }
/* an app open: wait for the queue (1.2 s after the first load) and its my_phone_saved read */
async function waitPop(page, ms = 6000) { for (let t = 0; t < ms; t += 250) { await run(page, 250); await page.waitForTimeout(60); if (await sheetType(page)) break; } await page.waitForTimeout(150); return sheetType(page); }
async function relaunch(page) { await page.reload(); await readyOf(page); return waitPop(page); }
const st = p => p.evaluate(() => ctState());

/* ---------- a 40-card address book: names with accents and odd case, single names, "#" names, bare numbers
   (handed over first, as iOS can), a bare copy of a named number, and the same person saved twice */
const NAMES = ['Abby Wachter', 'Adrien', 'Alex Brooks', 'Ávila Santos', 'andrea lópez', 'Brynn Winter', 'Bobby G.', 'Caleb Ortiz', 'Chloé Martin', 'Dana Reyes', 'Ethan Park', 'Émile Durand', 'Fiona Walsh', 'Grace Liu', 'Hannah Cho', 'Isaac Newton', 'Jacob Longoria', 'Kai Nakamura', 'Liam Patel', 'Maya Rodriguez', 'Mia Chen', 'Noah Kim', 'Olivia Grant', 'Priya Patel', 'Quinn Ashby', 'Riley Morgan', 'Sam Kim', 'Taylor Brooks', 'Uma Shah', 'Victor Hugo', 'Will Turner', 'Zoe Adams', '123 Pizza', 'Dr. Ölsen', '"Coach" Reed'];
const num = n => `(805) 555-${String(1000 + NAMES.indexOf(n) * 7).padStart(4, '0')}`;
const e164 = n => '+1' + num(n).replace(/\D/g, '');
const BARE = ['(619) 555-0111', '(415) 555-0177', '(805) 555-0999', '+1 213 555 0123', '(760) 555-0144'];
function book() {
  const out = NAMES.map((n, i) => ({ contactId: 'n' + i, name: { display: n }, phones: [{ number: num(n) }], emails: [] }));
  BARE.forEach((ph, i) => out.unshift({ contactId: 'u' + i, name: {}, phones: [{ number: ph }], emails: [] }));
  out.unshift({ contactId: 'dup0', name: { display: '  ' }, phones: [{ number: '805.555.1000' }], emails: [] });   /* Abby's number, no name, before her card */
  out.push({ contactId: 'dup1', name: { display: 'Abby Wachter' }, phones: [{ number: '+1 805 555 1000' }], emails: [] });   /* Abby saved twice */
  return out;
}
const ON = [['55555555-5555-4555-8555-555555555551', 'Maya Rodriguez', 'mayar'], ['55555555-5555-4555-8555-555555555552', 'Jacob Longoria', 'jlongo'], ['55555555-5555-4555-8555-555555555553', 'Sam Kim', 'samk']]
  .map(([id, n, u]) => ({ id, display_name: n, username: u, avatar_url: null, matched: [sha(e164(n))] }))
  .concat([{ id: FX.FRIENDS[0].id, display_name: FX.FRIENDS[0].display_name, username: FX.FRIENDS[0].username, avatar_url: null, matched: [] },
           { id: FX.STRANGER.id, display_name: FX.STRANGER.display_name, username: FX.STRANGER.username, avatar_url: null, matched: [] }]);
const nativeInit = (B, extra = '') => `(${(B) => {
  window.__ct = { reads: 0 };
  window.Capacitor = { isNativePlatform: () => true, getPlatform: () => 'ios', Plugins: { StatusBar: { setStyle: () => Promise.resolve() },
    Contacts: { checkPermissions: () => Promise.resolve({ contacts: 'granted' }), requestPermissions: () => Promise.resolve({ contacts: 'granted' }), getContacts: () => { __ct.reads++; return Promise.resolve({ contacts: B }); } },
    PushNotifications: { checkPermissions: () => Promise.resolve({ receive: 'granted' }), register: () => Promise.resolve(), addListener: () => {} } } };
  try { const s0 = JSON.parse(localStorage.getItem('sb-rqkndeqbcahozidniesn-auth-token') || 'null'); if (s0 && s0.user && !localStorage.getItem('tc_ct:' + s0.user.id)) localStorage.setItem('tc_ct:' + s0.user.id, JSON.stringify({ on: true, phOk: 1 })); } catch (e) {}
}})(${JSON.stringify(B)});${extra}`;
const rpcWith = extra => Object.assign({}, FX.RPC, { match_contacts: ON, my_phone_saved: false, set_my_phone: true }, extra || {});
const DARK = `try { localStorage.setItem('tc-theme', 'dark'); } catch (e) {}`;
/* the list as shown: [{ L, names[] }] in DOM order */
const groups = p => p.evaluate(() => [...document.querySelectorAll('#sheet .ct-grp[data-l]')].map(g => ({ L: g.dataset.l, h: g.querySelector('.ct-lh').textContent, names: [...g.querySelectorAll('.ct-row .nm')].map(n => n.textContent), subs: [...g.querySelectorAll('.ct-row')].map(r => (r.querySelector('.sub') || {}).textContent || '') })));
/* the first invite row under the sticky top */
const topRow = p => p.evaluate(() => { const fp = document.querySelector('#sheet .fullpg'), b = fp.querySelector('.ctp-top').getBoundingClientRect().bottom; const r = [...fp.querySelectorAll('.ct-grp[data-l] .ct-row')].find(x => x.getBoundingClientRect().top >= b + 27); return r ? r.querySelector('.nm').textContent : null; });
const typeQ = async (p, v) => { await p.locator('#ctQ').fill(v); await p.waitForTimeout(80); };
/* WCAG contrast of an element's text on what is behind it */
const contrast = (p, sel) => p.evaluate(sel => {
  const els = [...document.querySelectorAll(sel)]; if (!els.length) return null;
  const rgb = s => { const m = String(s).match(/[\d.]+/g) || []; return m.slice(0, 4).map(Number); };
  const lum = ([r, g, b]) => { const f = c => { c /= 255; return c <= .03928 ? c / 12.92 : Math.pow((c + .055) / 1.055, 2.4); }; return .2126 * f(r) + .7152 * f(g) + .0722 * f(b); };
  const bgOf = e => { for (let n = e; n; n = n.parentElement) { const c = rgb(getComputedStyle(n).backgroundColor); if (c.length >= 3 && (c[3] === undefined || c[3] > .5)) return c; } return [255, 255, 255]; };
  return Math.min(...els.slice(0, 6).map(e => { const cs = getComputedStyle(e), fg = rgb(cs.color), op = +cs.opacity || 1, bg = bgOf(e); const mix = fg.slice(0, 3).map((v, i) => v * op + bg[i] * (1 - op)); const a = lum(mix), b = lum(bg); return +((Math.max(a, b) + .05) / (Math.min(a, b) + .05)).toFixed(2); }));
}, sel);

/* ================= A: the synced list (light, 390px) */
console.log('# A: the list');
{
  const { page, close, log } = await openApp({ port: PORT, init: nativeInit(book()), rpc: rpcWith() });
  await page.evaluate(() => { TC.ctPreview = () => false; });
  await click(page, '[data-a="tab"][data-x="friends"]');
  const hdr = await page.evaluate(() => [...document.querySelectorAll('.fhdr .invpill')].map(b => b.textContent.trim()));
  ok(hdr.join() === 'Contacts,Invite', 'Friends header unchanged: Contacts + Invite', hdr);
  await click(page, '[data-a="ctOpen"]'); await settle(page, 1200);
  ok(await sheetType(page) === 'ctResults' && await page.locator('#sheet .fullpg .ctp').count() === 1, 'connected: Contacts opens the list as a full page');
  const top = await page.evaluate(() => ({ t: document.querySelector('#sheet .ctp-t').textContent, x: !!document.querySelector('#sheet .ctp-top .xbtn[data-a="closeSheet"]'), q: (document.getElementById('ctQ') || {}).placeholder, pos: getComputedStyle(document.querySelector('#sheet .ctp-top')).position }));
  ok(top.t === 'Contacts' && top.x && top.q === 'Search contacts' && top.pos === 'sticky', 'header: "Contacts" + close, a "Search contacts" box, both stay at the top', top);
  const secs = await page.evaluate(() => [...document.querySelectorAll('#sheet .ct-sec')].map(s => s.innerText.replace(/\s+/g, ' ').trim()));
  ok(secs.length === 2 && /^On TermChamp 5\b/.test(secs[0]) && secs[1] === 'Invite to TermChamp', 'sections: On TermChamp (count 5) then Invite to TermChamp (no count)', secs);
  /* On TermChamp */
  const on = await page.evaluate(() => [...document.querySelectorAll('#sheet #ctBody > .ct-row')].map(r => ({ nm: r.querySelector('.nm').textContent, sub: (r.querySelector('.sub') || {}).textContent || '', b: (r.querySelector('.pbtn') || {}).textContent, bg: getComputedStyle(r.querySelector('.pbtn')).backgroundColor, av: !!r.querySelector('.ct-av') })));
  const maya = on.find(r => r.nm === 'Maya Rodriguez');
  ok(on.length === 5 && maya && maya.sub === '@mayar' && maya.b === 'Add' && maya.bg === 'rgb(37, 99, 235)' && on.every(r => r.av), 'On TermChamp: avatar, name, @handle, a blue Add', on);
  ok(on.some(r => r.b === 'Friends') && on.some(r => r.b === 'Accept'), 'On TermChamp: Friends and Accept states as before', on.map(r => r.b));
  await page.evaluate(() => { PEOPLE['55555555-5555-4555-8555-555555555551'].major = 'Business Administration'; TC.fof[TC.friends[0]] = { ids: ['55555555-5555-4555-8555-555555555552'], at: Date.now() }; TC.fof[TC.friends[1]] = { ids: ['55555555-5555-4555-8555-555555555552'], at: Date.now() }; render(true); });
  const subs = await page.evaluate(() => Object.fromEntries([...document.querySelectorAll('#sheet #ctBody > .ct-row')].map(r => [r.querySelector('.nm').textContent, (r.querySelector('.sub') || {}).textContent])));
  ok(subs['Maya Rodriguez'] === '@mayar · Business Administration' && subs['Jacob Longoria'] === '@jlongo · 2 mutual', '@handle · major, or · N mutual when known', subs);
  await click(page, '#sheet [data-a="addFriend"][data-x="55555555-5555-4555-8555-555555555551"]'); await settle(page, 500);
  const fr = log.writes.filter(w => w.table === 'friend_requests' && w.m === 'POST');
  ok(fr.length === 1 && fr[0].body.to_user === '55555555-5555-4555-8555-555555555551' && /Requested/.test(await page.locator('#sheet .ct-row:has([data-x="55555555-5555-4555-8555-555555555551"])').innerText()), 'Add: one friend request, then Requested', fr.map(x => x.body));
  /* Invite to TermChamp: the order (the bug: bare numbers came first) */
  const G = await groups(page), names = G.flatMap(g => g.names);
  const L = G.map(g => g.L).join('');
  ok(L === 'ABCDEFGHIKLMNOPQRTUVWZ#~', 'letters A to Z (only ones with someone), then #, then Other numbers last', L);
  ok(G[G.length - 1].h === 'Other numbers' && G[G.length - 1].names.join('|') === '(213) 555-0123|(415) 555-0177|(619) 555-0111|(760) 555-0144|(805) 555-0999', 'number-only contacts last, under "Other numbers", in number order', G[G.length - 1]);
  const firstBare = names.findIndex(n => /^\(\d{3}\)/.test(n)), lastNamed = names.length - 1 - [...names].reverse().findIndex(n => !/^\(\d{3}\)/.test(n));
  ok(firstBare > lastNamed && firstBare === names.length - 5, 'every named contact before every bare number (the reported bug)', { firstBare, lastNamed });
  ok(G[0].names.join('|') === 'Abby Wachter|Adrien|Alex Brooks|andrea lópez|Ávila Santos', 'A: case and accents ignored (andrea lópez, Ávila sort as a, A), single names fit in', G[0].names);
  ok(G.find(g => g.L === 'E').names.join('|') === 'Émile Durand|Ethan Park' && G.find(g => g.L === 'D').names.join('|') === 'Dana Reyes|Dr. Ölsen', 'É files under E, Ö inside a name sorts as O', [G.find(g => g.L === 'E').names, G.find(g => g.L === 'D').names]);
  ok(G.find(g => g.L === 'C').names.join('|') === 'Caleb Ortiz|Chloé Martin|"Coach" Reed' && G.find(g => g.L === '#').names.join('|') === '123 Pizza', 'a leading quote is skipped for the letter; a name starting with a digit goes under #', [G.find(g => g.L === 'C').names, G.find(g => g.L === '#').names]);
  ok(names.filter(n => n === 'Abby Wachter').length === 1 && !names.includes('(805) 555-1000') && names.length === NAMES.length - 3 + BARE.length, 'duplicates listed once: Abby saved twice, and her number saved bare too', { abby: names.filter(n => n === 'Abby Wachter').length, n: names.length });
  ok(!names.includes('Maya Rodriguez') && !names.includes('Sam Kim') && !names.includes('Jacob Longoria'), 'people on TermChamp aren’t in the invite list');
  ok(G[0].subs[0] === '(805) 555-1000' && G[G.length - 1].subs.every(s => s === ''), 'the number sits under the name (bare numbers show it once, as the name)', [G[0].subs[0], G[G.length - 1].subs]);
  const inv = await page.evaluate(() => { const b = document.querySelector('#sheet [data-a="ctInvite"]'), cs = getComputedStyle(b); return { t: b.textContent, bg: cs.backgroundColor, sh: cs.boxShadow, h: b.getBoundingClientRect().height }; });
  ok(inv.t === 'Invite' && inv.bg === 'rgba(0, 0, 0, 0)' && /inset/.test(inv.sh) && inv.h <= 34, 'Invite: a quiet outlined pill', inv);
  ok(await page.evaluate(() => getComputedStyle(document.querySelector('#sheet .ct-lh')).position) === 'sticky' && await page.evaluate(() => getComputedStyle(document.querySelector('#sheet .ct-grp')).contentVisibility) === 'auto', 'letter headers stick; groups off screen aren’t laid out (content-visibility)');
  /* the scrubber */
  const idx = await page.evaluate(() => [...document.querySelectorAll('#sheet .ct-idx button')].map(b => b.textContent + (b.classList.contains('off') ? '-' : '')).join(' '));
  ok(idx === 'A B C D E F G H I J- K L M N O P Q R S- T U V W X- Y- Z #', 'scrubber: A to Z and #, letters with nobody dimmed', idx);
  const ib = await page.evaluate(() => { const r = document.querySelector('#sheet .ct-idx').getBoundingClientRect(); return { right: r.right, w: innerWidth, top: r.top, bottom: r.bottom, h: innerHeight }; });
  ok(ib.right <= ib.w && ib.right >= ib.w - 4 && ib.bottom <= ib.h, 'scrubber on the right edge, on screen', ib);
  await page.locator('#sheet .ct-idx button[data-x="M"]').click(); await page.waitForTimeout(150);
  ok(await page.evaluate(() => UI.sheet && UI.sheet.type) === 'ctResults' && await topRow(page) === 'Mia Chen', 'tap M: Mia Chen at the top', await topRow(page));
  ok(await page.evaluate(() => { const fp = document.querySelector('#sheet .fullpg'), t = fp.querySelector('.ctp-top').getBoundingClientRect(), h = [...fp.querySelectorAll('.ct-lh')].find(x => x.textContent === 'M').getBoundingClientRect(); return Math.abs(h.top - t.bottom) < 2; }), 'the M header sits right under the search box');
  await page.locator('#sheet .ct-idx button[data-x="S"]').click(); await page.waitForTimeout(150);
  ok(await topRow(page) === 'Taylor Brooks', 'tap S (nobody): the next letter with someone, T', await topRow(page));
  await page.locator('#sheet .ct-idx button[data-x="#"]').click(); await page.waitForTimeout(150);
  ok(await page.evaluate(() => { const fp = document.querySelector('#sheet .fullpg'); return fp.scrollTop + fp.clientHeight >= fp.scrollHeight - 2; }), 'tap #: to the end (#, then Other numbers)');
  /* drag along it */
  const pos = L => page.evaluate(L => { const r = document.querySelector(`#sheet .ct-idx button[data-x="${L}"]`).getBoundingClientRect(); return { x: r.left + r.width / 2, y: r.top + r.height / 2 }; }, L);
  const a = await pos('A'), c = await pos('C'), w = await pos('R');
  await page.mouse.move(a.x, a.y); await page.mouse.down(); await page.waitForTimeout(50);
  ok(await page.evaluate(() => document.querySelector('#sheet .fullpg').scrollTop) >= 0, 'drag starts');
  await page.mouse.move(c.x, c.y, { steps: 3 }); await page.waitForTimeout(80);
  const midDrag = await topRow(page);
  await page.mouse.move(w.x, w.y, { steps: 6 }); await page.waitForTimeout(80);
  const endDrag = await topRow(page); await page.mouse.up(); await page.waitForTimeout(100);
  ok(midDrag === 'Caleb Ortiz' && endDrag === 'Riley Morgan', 'drag down the scrubber: C (Caleb), then R (Riley) at the top', { midDrag, endDrag });
  ok(await sheetType(page) === 'ctResults', 'dragging the scrubber doesn’t close the page');
  /* search */
  await typeQ(page, 'chlo');
  let g2 = await groups(page);
  ok(g2.flatMap(g => g.names).join() === 'Chloé Martin' && await page.locator('#sheet #ctBody > .ct-row').count() === 0, 'search "chlo": Chloé (accent ignored), nobody on TermChamp', g2);
  ok(await page.evaluate(() => getComputedStyle(document.querySelector('#sheet .ct-idx')).display) === 'none' && await page.evaluate(() => document.activeElement && document.activeElement.id) === 'ctQ', 'searching: the scrubber hides, the box keeps focus');
  await typeQ(page, 'ANDREA LOPEZ'); ok((await groups(page)).flatMap(g => g.names).join() === 'andrea lópez', 'search: case and accents ignored, every word', await groups(page));
  await typeQ(page, '555-0177'); ok((await groups(page)).flatMap(g => g.names).join() === '(415) 555-0177', 'search: by number (digits)', await groups(page));
  await typeQ(page, 'maya'); ok(await page.locator('#sheet #ctBody > .ct-row').count() === 1 && /Maya Rodriguez/.test(await page.locator('#sheet #ctBody').innerText()) && (await groups(page)).length === 0 && !/Invite to TermChamp/.test(await page.locator('#sheet #ctBody').innerText()), 'search "maya": filters On TermChamp too; no empty Invite section');
  await typeQ(page, 'mayar'); ok(await page.locator('#sheet #ctBody > .ct-row').count() === 1, 'search: by @handle');
  await typeQ(page, 'zzzz'); ok(/No contacts match “zzzz”\./.test(await page.locator('#sheet #ctBody').innerText()), 'search: nothing found says so');
  await typeQ(page, ''); ok((await groups(page)).flatMap(g => g.names).length === names.length && await page.evaluate(() => getComputedStyle(document.querySelector('#sheet .ct-idx')).display) !== 'none', 'cleared: the whole list and the scrubber are back');
  await typeQ(page, 'brooks');
  await page.evaluate(() => { window.__go = []; TC.ctGo = u => window.__go.push(u); });
  await click(page, '#sheet [data-a="ctInvite"]');
  const go = await page.evaluate(() => window.__go);
  ok(go.length === 1 && go[0].startsWith('sms:' + e164('Alex Brooks')), 'Invite (from a search): Messages to that number', go);
  ok(/Invited/.test(await page.locator('#sheet .ct-row:has([data-a="ctInvite"])').first().innerText()) && await page.evaluate(() => document.getElementById('ctQ').value) === 'brooks', 'Invite: says Invited, the search stays');
  ok(log.errors.length === 0, 'A: no page errors', log.errors);
  await close();
}
/* ================= A: 1,500 contacts */
console.log('# A: 1,500 contacts');
{
  const FIRST = ['Ava', 'Ben', 'Cleo', 'Dev', 'Eli', 'Faye', 'Gus', 'Hal', 'Ivy', 'Jo', 'Kit', 'Lu', 'Max', 'Nia', 'Oz', 'Pia', 'Quin', 'Rae', 'Sol', 'Tia', 'Ugo', 'Val', 'Wes', 'Xan', 'Yui', 'Zed'];
  const big = []; for (let i = 0; i < 1500; i++) big.push(i % 10 === 9 ? { contactId: 'b' + i, name: {}, phones: [{ number: '(805) 6' + String(100000 + i).slice(-6) }], emails: [] }
    : { contactId: 'b' + i, name: { display: FIRST[(i * 7) % 26] + ' ' + FIRST[(i * 11) % 26] + 'son ' + i }, phones: [{ number: '(805) 7' + String(100000 + i).slice(-6) }], emails: [] });
  const { page, close, log } = await openApp({ port: PORT, init: nativeInit(big), rpc: rpcWith({ match_contacts: [] }) });
  await page.evaluate(() => { TC.ctPreview = () => false; });
  await page.evaluate(() => { ctSet({ on: true }); A.ctOpen(); }); await settle(page, 2500);
  const n = await page.locator('#sheet [data-a="ctInvite"]').count();
  ok(n === 1500, 'all 1,500 listed', n);
  const t = await page.evaluate(() => { const r = []; for (let i = 0; i < 5; i++) { const t0 = performance.now(); render(true); r.push(performance.now() - t0); } return r.sort((a, b) => a - b)[2]; });
  ok(t < 250, `a re-render with the list open: ${t.toFixed(1)} ms (median of 5)`, t);
  const s = await page.evaluate(() => { const i = document.getElementById('ctQ'); i.focus(); const r = []; for (const v of ['a', 'av', 'ava', 'ava b', '']) { const t0 = performance.now(); i.value = v; i.dispatchEvent(new Event('input', { bubbles: true })); r.push(performance.now() - t0); } return Math.max(...r); });
  ok(s < 250, `a search keystroke: ${s.toFixed(1)} ms at worst`, s);
  await page.locator('#sheet .ct-idx button[data-x="Z"]').click(); await page.waitForTimeout(150);
  ok(/^Zed /.test(await topRow(page) || ''), 'tap Z in 1,500: lands on the Z names', await topRow(page));
  const last = await page.evaluate(() => { const g = [...document.querySelectorAll('#sheet .ct-grp')].pop(); return [g.dataset.l, g.querySelectorAll('.ct-row').length]; });
  ok(last[0] === '~' && last[1] === 150, 'the 150 bare numbers are last', last);
  ok(log.errors.length === 0, '1,500: no page errors', log.errors);
  await close();
}
/* ================= 1a: the sign-up step */
console.log('# 1a: sign-up');
{
  const { page, close, log } = await openApp({ port: PORT, rpc: rpcWith() });
  await page.evaluate(() => { S.stack.home.push({ s: 'onb', p: { step: 'confirm' } }); UI.onbPre = { major: 'Business Administration', standing: 'Junior', conc: '' }; render(); }); await settle(page, 1500);
  await click(page, '[data-a="onbConfirmDone"]'); await settle(page, 800);
  const t = await page.locator('#scroll').innerText();
  ok(/What’s your number\?/.test(t) && /Friends who have you saved will find you on TermChamp\. It’s never shown on your profile\./.test(t), '1a: "What’s your number?" and the copy from the mockup', t.slice(0, 300));
  const ui = await page.evaluate(() => { const g = s => document.querySelector(s); const c = g('.onb .foot .btn'), n = g('[data-a="ctPhoneSkip"]'); return { prog: !!g('.onb .progress'), ico: !!g('.onb .onb-ico.ct-ph svg'), cc: g('.onb .unwrap .at').textContent, ph: g('#ob-phone').placeholder, lab: g('#ob-phone').getAttribute('aria-label'), cont: c.textContent, contH: c.getBoundingClientRect().height, contBg: getComputedStyle(c).backgroundColor, not: n.textContent, notFs: parseFloat(getComputedStyle(n).fontSize), notBg: getComputedStyle(n).backgroundColor, notInk: getComputedStyle(n).color, notH: n.getBoundingClientRect().height, below: n.getBoundingClientRect().top > c.getBoundingClientRect().bottom }; });
  ok(ui.prog && ui.ico && /\+1$/.test(ui.cc) && ui.ph === '(805) 555-0134' && ui.lab === 'Phone number', '1a: progress bar, the phone tile, a +1 field (labelled)', ui);
  ok(ui.cont === 'Continue' && ui.contH >= 48 && ui.contBg === 'rgb(37, 99, 235)' && ui.not === 'Not now' && ui.notFs <= 14.5 && ui.notBg === 'rgba(0, 0, 0, 0)' && ui.notInk !== ui.contBg && ui.notInk !== 'rgb(15, 23, 42)' && ui.notH >= 40 && ui.below, '1a: a big blue Continue; a small grey "Not now" text button under it (no Skip)', ui);
  await page.screenshot({ path: SHOTS + '/1a-light.png' });
  await click(page, '[data-a="ctPhoneSkip"]');
  ok(/People you may know/.test(await page.locator('#scroll').innerText()) && !log.rpcs.some(r => r.fn === 'set_my_phone'), '1a: Not now goes on and sends nothing');
  const s1 = await st(page), now = await page.evaluate(() => Date.now());
  ok(s1.phSkip && now - s1.phSkip < 5000 && !s1.pk, '1a: Not now is remembered (the 1b pop-up waits 7 days), and isn’t one of 1b’s two asks', s1);
  await click(page, '[data-a="onbBack"]');
  await page.locator('#ob-phone').fill('805 55'); await click(page, '.onb .foot .btn');
  ok(/Enter a 10-digit US number/.test(await page.locator('#ob-phoneerr').innerText()) && !log.rpcs.some(r => r.fn === 'set_my_phone'), '1a: a short number says so, sends nothing');
  await page.locator('#ob-phone').fill('(805) 555-0134'); await click(page, '.onb .foot .btn'); await settle(page, 600);
  const set = log.rpcs.filter(r => r.fn === 'set_my_phone');
  ok(set.length === 1 && set[0].body.p_hash === sha('+18055550134') && /People you may know/.test(await page.locator('#scroll').innerText()), '1a: Continue saves only the hash and goes on', set.map(x => x.body));
  ok(log.errors.length === 0, '1a: no page errors', log.errors);
  await close();
}
/* ================= 1b: the pop-up for students already signed up */
console.log('# 1b: existing students');
const OLD = (o = {}) => `try { const k = 'sb-rqkndeqbcahozidniesn-auth-token', s = JSON.parse(localStorage.getItem(k)); s.user.created_at = '2026-01-01T00:00:00Z'; localStorage.setItem(k, JSON.stringify(s));
  if (!sessionStorage.getItem('__once')) { sessionStorage.setItem('__once', '1'); localStorage.setItem('tc_ct:' + s.user.id, ${JSON.stringify(JSON.stringify(o))}); } } catch (e) {}`;
{
  const { page, close, log } = await openApp({ port: PORT, init: OLD({ on: true }), rpc: rpcWith(), wait: 200 });
  await readyOf(page);
  ok(await waitPop(page) === 'ctPhonePop', '1b: phoneSaved false, an account from before, on Home: the pop-up on this open');
  const t = await page.locator('#sheet .sheet').innerText();
  ok(/Add your number/.test(t) && /So friends can find you/.test(t) && /Save/.test(t) && /Not now/.test(t) && await page.locator('#sheet #ctPopIn[type="tel"][autocomplete="tel"]').count() === 1 && /\+1/.test(await page.locator('#sheet .ct-tel .cc').innerText()), '1b: "Add your number · So friends can find you", +1 field, Save, Not now', t);
  ok(await page.evaluate(() => document.activeElement && document.activeElement.id) !== 'ctPopIn', '1b: no keyboard on its own (the field isn’t focused for them)');
  ok(log.rpcs.filter(r => r.fn === 'my_phone_saved').length === 1, '1b: asked the server once');
  let s = await st(page);
  ok(s.pk === 1 && s.pat > 0 && await page.evaluate(() => popDayUsed()), '1b: counted (1 of 2) and it is the day’s one pop-up', s);
  ok(await page.evaluate(() => TC.popQueue('open')) === false, '1b: nothing else this app open');
  await page.locator('#sheet .sheet').screenshot({ path: SHOTS + '/1b-light.png' });
  /* Save: empty, bad, good */
  await click(page, '#sheet .btn:not(.ghost)');
  ok(/Enter your number, or tap Not now\./.test(await page.locator('#sheet').innerText()) && !log.rpcs.some(r => r.fn === 'set_my_phone'), 'Save with nothing: says so, sends nothing');
  await page.locator('#ctPopIn').fill('555'); await click(page, '#sheet .btn:not(.ghost)');
  ok(/Enter a 10-digit US number/.test(await page.locator('#sheet').innerText()) && !log.rpcs.some(r => r.fn === 'set_my_phone'), 'Save a short number: says so, sends nothing');
  await page.locator('#ctPopIn').fill('(805) 555-0177'); await click(page, '#sheet .btn:not(.ghost)'); await settle(page, 600);
  const set = log.rpcs.filter(r => r.fn === 'set_my_phone');
  ok(set.length === 1 && set[0].body.p_hash === sha('+18055550177') && !/555/.test(JSON.stringify(set[0].body)) && await sheetType(page) === null && (await st(page)).phOk === 1, 'Save: set_my_phone gets only the hash, the pop-up closes, never asks again', set.map(x => x.body));
  ok(/Number saved/.test(await page.locator('#toast').innerText()), 'Save: a toast says so');
  await page.evaluate(() => { localStorage.removeItem('tc_pop_day'); ctSet({ pat: Date.now() - 30 * 864e5 }); TC.phoneSaved = false; });
  ok(await relaunch(page) === null, 'saved: no pop-up again, even 30 days on');
  ok(log.errors.length === 0, '1b save: no page errors', log.errors);
  await close();
}
{
  const { page, close, log } = await openApp({ port: PORT, init: OLD({ on: true }), rpc: rpcWith(), wait: 200 });
  await readyOf(page);
  ok(await waitPop(page) === 'ctPhonePop', '1b again: shows');
  await click(page, '#sheet [data-a="closeSheet"].ctpp-no');
  ok(await sheetType(page) === null && !log.rpcs.some(r => r.fn === 'set_my_phone'), 'Not now: closes, sends nothing');
  ok(await relaunch(page) === null, 'same day, another open: nothing (one a day)');
  await page.evaluate(() => localStorage.removeItem('tc_pop_day'));
  ok(await relaunch(page) === null, 'next day, inside 7 days: nothing', await st(page));
  await page.evaluate(() => { localStorage.removeItem('tc_pop_day'); ctSet({ pat: Date.now() - 7 * 864e5 - 1000 }); });
  ok(await relaunch(page) === 'ctPhonePop' && (await st(page)).pk === 2, '7 days on: asks the second time');
  await page.locator('#sheet .scrim').click({ position: { x: 10, y: 10 } }); await settle(page);
  ok(await sheetType(page) === null, 'closing with the scrim counts as Not now');
  await page.evaluate(() => { localStorage.removeItem('tc_pop_day'); ctSet({ pat: Date.now() - 60 * 864e5 }); });
  ok(await relaunch(page) === null, 'asked twice: never again, even 60 days on', await st(page));
  ok(/Your phone number\s*Not added/.test(await (async () => { await page.evaluate(() => A.openSettings()); await settle(page, 600); return page.locator('#scroll').innerText(); })()) && await page.locator('.ct-set [data-a="ctPhoneSheet"]').count() === 1, 'Settings › Contacts still has Add');
  ok(log.errors.length === 0, '1b caps: no page errors', log.errors);
  await close();
}
/* never when the server can't say, or the number is there */
for (const [what, opt] of [['saved (true)', { rpc: rpcWith({ my_phone_saved: true }) }],
  ['SQL not run (404 → null)', { rpc: rpcWith(), hook: u => u.pathname === '/rest/v1/rpc/my_phone_saved' ? { status: 404, body: JSON.stringify({ code: 'PGRST202', details: null, hint: null, message: 'Could not find the function public.my_phone_saved in the schema cache' }) } : null }],
  ['read failed (500)', { rpc: rpcWith(), hook: u => u.pathname === '/rest/v1/rpc/my_phone_saved' ? { status: 500, body: JSON.stringify({ code: 'XX000', message: 'boom', details: null, hint: null }) } : null }]]) {
  const { page, close, log } = await openApp(Object.assign({ port: PORT, init: OLD({ on: true }), wait: 200 }, opt));
  await readyOf(page);
  ok(await waitPop(page) === null && log.rpcs.filter(r => r.fn === 'my_phone_saved').length + (opt.hook ? 1 : 0) >= 1, `1b: ${what}: no pop-up`, await page.evaluate(() => TC.phoneSaved));
  const s = await st(page);
  ok(!s.pk && (what.startsWith('saved') ? s.phOk === 1 : !s.phOk), `1b: ${what}: not counted${what.startsWith('saved') ? '; remembered as saved' : ''}`, s);
  ok(log.errors.length === 0, `1b ${what}: no page errors`, log.errors);
  await close();
}
/* not off Home, not in onboarding, not right after sign-up's Not now, contacts first, then notifications */
{
  const { page, close, log } = await openApp({ port: PORT, init: OLD({ on: true, pat: T0 }), rpc: rpcWith(), wait: 200 });
  await readyOf(page);
  ok(await waitPop(page, 3000) === null, 'asked today already (pat = now): nothing on this open');
  await page.evaluate(() => { POPQ.shown = -1; ctSet({ pk: 0, pat: 0 }); });
  await page.evaluate(() => setTab('explore')); await settle(page);
  ok(await page.evaluate(() => TC.popQueue('open')) !== 'phone' && await sheetType(page) === null, 'not on Explore');
  await page.evaluate(() => { setTab('home'); S.stack.home.push({ s: 'onb', p: { step: 'people' } }); render(); }); await settle(page);
  ok(await page.evaluate(() => TC.popQueue('open')) !== 'phone' && await page.evaluate(() => TC.pops.find(k => k.kind === 'phone').due('onboarding')) === null, 'not during onboarding (nor at its end)');
  await page.evaluate(() => { S.stack.home = [{ s: 'home' }]; render(); ctSet({ phSkip: Date.now() - 2 * 864e5 }); }); await settle(page);
  ok(await page.evaluate(() => TC.popQueue('open')) === false, 'Not now at sign-up 2 days ago: waits');
  await page.evaluate(() => { ctSet({ phSkip: Date.now() - 8 * 864e5 }); POPQ.shown = -1; });
  ok(await page.evaluate(() => TC.popQueue('open')) === 'phone', '8 days after sign-up’s Not now: asks');
  await page.evaluate(() => { UI.sheet = null; render(true); });
  ok(await page.evaluate(() => TC.pops.map(k => k.kind).join()) === 'contacts,phone,push', 'queue order: contacts, then this, then notifications');
  /* iPhone (here the preview): "Connect contacts" has its turn first */
  await page.evaluate(() => { localStorage.removeItem('tc_pop_day'); POPQ.shown = -1; ctSet({ on: false, k: 0, n: 5, snooze: 0, pk: 0, pat: 0, phSkip: 0 }); });
  ok(await page.evaluate(() => TC.popQueue('open')) === 'contacts', 'contacts never asked: Connect contacts first');
  await page.evaluate(() => { UI.sheet = null; render(true); localStorage.removeItem('tc_pop_day'); POPQ.shown = -1; });
  ok(await page.evaluate(() => TC.popQueue('open')) === 'phone', 'contacts asked (Not now, snoozed): then Add your number, on another day');
  await page.evaluate(() => { UI.sheet = null; render(true); localStorage.removeItem('tc_pop_day'); POPQ.shown = -1; ctSet({ on: false, k: 0, pk: 0, pat: 0 }); TC.ctPreview = () => false; });
  ok(await page.evaluate(() => TC.popQueue('open')) === 'phone', 'the website (no contacts there): Add your number on its own');
  await page.evaluate(() => { UI.sheet = null; render(true); });
  ok(log.errors.length === 0, '1b order: no page errors', log.errors);
  await close();
}
{ /* ahead of notifications: an iPhone that hasn't been asked about notifications yet */
  const init = OLD({ on: true }) + `;window.__push = 'prompt'; window.Capacitor = { isNativePlatform: () => true, getPlatform: () => 'ios', Plugins: { StatusBar: { setStyle: () => Promise.resolve() },
    PushNotifications: { checkPermissions: () => Promise.resolve({ receive: window.__push }), requestPermissions: () => Promise.resolve({ receive: 'granted' }), register: () => Promise.resolve(), addListener: () => {} } } };`;
  const { page, close, log } = await openApp({ port: PORT, init, rpc: rpcWith(), wait: 200 });
  await readyOf(page);
  ok(await waitPop(page) === 'ctPhonePop', 'iPhone, notifications never asked: Add your number comes first');
  await click(page, '#sheet .ctpp-no');
  await page.evaluate(() => localStorage.removeItem('tc_pop_day'));
  ok(await relaunch(page) === 'pushAsk', 'the next day: the notifications pop-up');
  ok(log.errors.length === 0, '1b vs push: no page errors', log.errors);
  await close();
}
/* ================= dark mode, 390px: the list, 1b, 1a */
console.log('# dark');
{
  const { page, close, log } = await openApp({ port: PORT, init: nativeInit(book(), DARK), rpc: rpcWith() });
  await page.evaluate(() => { TC.ctPreview = () => false; });
  ok(await page.evaluate(() => document.documentElement.getAttribute('data-theme')) === 'dark', 'dark: on');
  await page.evaluate(() => { ctSet({ on: true }); A.ctOpen(); }); await settle(page, 1500); await page.waitForTimeout(500);
  const bg = await page.evaluate(() => [getComputedStyle(document.querySelector('#sheet .ctp')).backgroundColor, getComputedStyle(document.querySelector('#sheet .ctp-top')).backgroundColor, getComputedStyle(document.querySelector('#sheet .ct-lh')).backgroundColor, getComputedStyle(document.getElementById('status')).backgroundColor]);
  ok(bg[0] === 'rgb(10, 15, 28)' && bg.every(x => x === bg[0]), 'dark: the page, its sticky top, the letter headers and the status bar are one dark colour', bg);
  const C = {};
  for (const [k, sel] of [['name', '#sheet .ct-grp .nm'], ['number', '#sheet .ct-grp .sub'], ['letter', '#sheet .ct-lh'], ['invite', '#sheet .ct-inv'], ['section', '#sheet .ct-sec'], ['scrubber', '#sheet .ct-idx button:not(.off)'], ['search', '#ctQ'], ['tcSub', '#sheet #ctBody > .ct-row .sub'], ['add', '#sheet [data-a="addFriend"]'], ['title', '#sheet .ctp-t']]) C[k] = await contrast(page, sel);
  ok(Object.values(C).every(v => v >= 4.5), 'dark: every text ≥ 4.5:1 on its background', C);
  const ivEdge = await page.evaluate(() => getComputedStyle(document.querySelector('#sheet .ct-inv')).boxShadow);
  ok(/rgb\(58, 70, 96\)/.test(ivEdge), 'dark: Invite’s outline uses the dark line colour', ivEdge);
  const ov = await page.evaluate(() => ({ sw: document.documentElement.scrollWidth, bad: [...document.querySelectorAll('#sheet *')].filter(e => { const r = e.getBoundingClientRect(); return r.width && (r.right > innerWidth + .5 || r.left < -.5); }).length }));
  ok(ov.sw <= 390 && ov.bad === 0, 'dark 390px: nothing wider than the screen', ov);
  await page.screenshot({ path: SHOTS + '/list-dark.png' });
  await page.evaluate(() => { UI.sheet = null; render(true); TC.phoneSaved = false; ctPhonePop(); }); await settle(page, 600); await page.waitForTimeout(400);
  const D = { title: await contrast(page, '#sheet .ctpp-hd h3'), sub: await contrast(page, '#sheet .ctpp-hd .muted'), notNow: await contrast(page, '#sheet .ctpp-no'), field: await contrast(page, '#ctPopIn') };
  ok(Object.values(D).every(v => v >= 4.5) && await page.evaluate(() => getComputedStyle(document.querySelector('#sheet .sheet')).backgroundColor) !== 'rgb(255, 255, 255)', 'dark 1b: a dark sheet, text ≥ 4.5:1', D);
  await page.screenshot({ path: SHOTS + '/1b-dark.png' });
  await page.evaluate(() => { UI.sheet = null; S.stack.home.push({ s: 'onb', p: { step: 'phone' } }); render(); }); await settle(page, 600);
  ok(/What’s your number\?/.test(await page.locator('#scroll').innerText()) && await contrast(page, '.onb [data-a="ctPhoneSkip"]') >= 4.5, 'dark: the sign-up step stays light (as all of onboarding), Not now readable');
  await page.screenshot({ path: SHOTS + '/1a-dark.png' });
  ok(log.errors.length === 0, 'dark: no page errors', log.errors);
  await close();
}
{ /* light contrast too */
  const { page, close } = await openApp({ port: PORT, init: nativeInit(book()), rpc: rpcWith() });
  await page.evaluate(() => { TC.ctPreview = () => false; ctSet({ on: true }); A.ctOpen(); }); await settle(page, 1500); await page.waitForTimeout(500);
  const C = {}; for (const [k, sel] of [['name', '#sheet .ct-grp .nm'], ['number', '#sheet .ct-grp .sub'], ['letter', '#sheet .ct-lh'], ['invite', '#sheet .ct-inv'], ['scrubber', '#sheet .ct-idx button:not(.off)'], ['add', '#sheet [data-a="addFriend"]']]) C[k] = await contrast(page, sel);
  ok(Object.values(C).every(v => v >= 4.5), 'light: every text ≥ 4.5:1 on its background', C);
  await page.screenshot({ path: SHOTS + '/list-light.png' });
  await close();
}
console.log(`contacts-v2: ${pass} passed, ${fail} failed`);
process.exit(fail ? 1 : 0);
