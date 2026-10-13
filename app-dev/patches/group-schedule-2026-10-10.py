#!/usr/bin/env python3
"""Group schedule (Tate, 2026-10-10), from the Group Schedule View canvas, design A as refined:
"lets create a group schedule view where its simple but you see whoever is in the group and at the same time
when they are free", then "dont hae any writing on anything until you click the specific day and then
everything should shrink to lines on the others and compress so the day clicked is large and has visible
information", then "show profile photos just have the color as a ball next to the profile pic. also spread
it out horizontally a little more and for the tapped version dont have the lines so scrambled drop the green
free … on compresses".

- A group chat's header gets a calendar button, and its "people and options" sheet a row, that open the
  group's week. (A long group name in the header now stops at two lines.)
- The members across the top: each person's photo with their colour as a small ball on it. You first.
- One Mon–Fri week of the term people are in now, 0.8px a minute (8a–6p is 480px; wider for an earlier or
  later class). Every class is a block in its person's colour; a class two people are in together is one
  block split into both colours. Classes at the same time sit side by side. Green bands mark when everyone is
  free (Champ's rule: 30 minutes or more). A red line marks now on today. Nothing is written on the week.
- Tap a day: it opens wide (the others slide down to 12px) and shows, as room allows, each class's code, time
  and faces (a block opens its section preview, which knows Fall from Spring), the free times in the green
  bands, and the hour axis. Every other day is ONE centred line: the times someone's in class, in their
  colours, side by side where people overlap. No green on them. Tap the open day again to close it.
- Above the week while a day is open: "TODAY · EVERYONE FREE" (today, only times that haven't ended), the
  times, and Send to chat, which posts "Everyone's free Thursday before 10:10a and after 2p" and goes back.
- Honest about who's counted: classes are friends-only (my_sections RLS), so a member you aren't friends
  with shows greyed, "Not friends" (or "Blocked"), with no colour; a friend with no class times says "No
  classes" or "No times". Free times count only people whose times are known, and the page and the message
  say "everyone" only when that's the whole group ("FREE TOGETHER", "Rowan, Sky and I are free …"
  otherwise), with a line saying who's left out and why.

Usage: python3 group-schedule-2026-10-10.py <repo>
"""
import sys, pathlib
root = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else '.')
f = root / 'app' / 'index.html'
s = f.read_text()
if 'group-schedule (2026-10-10)' in s:
    sys.exit('already patched')

def one(old, new):
    global s
    n = s.count(old)
    assert n == 1, (n, old[:90])
    s = s.replace(old, new)

# 1. the group chat's header: a calendar button before Mute
one("""}</button>${head}${muteBtn(id)}</div>`, padTop: 64,""",
    """}</button>${head}${t.kind === 'group' ? `<button class="iconbtn gwbtn" data-a="openGroupWeek" data-x="${esc(String(id))}" aria-label="See when everyone’s free">${ic('cal', 20, 2.3)}</button>` : ''}${muteBtn(id)}</div>`, padTop: 64,""")

# 2. the chat's "people and options" sheet: the same, as the first row for a group
one(""" ${people}<div class="card list mact">${o && TC.friends.includes(o) ?""",
    """ ${people}<div class="card list mact">${t.kind === 'group' ? `<button class="li" data-a="openGroupWeek" data-x="${esc(cid)}">${ic('cal', 20, 2.2)}<span class="grow b">See when everyone’s free</span>${ic('chevR', 18)}</button>` : ''}${o && TC.friends.includes(o) ?""")

# 3. the page
one('''/* A friend's Plans A–C — only what they chose to share (RLS returns a plan only while its "friends''',
    r'''/* ================= group schedule (2026-10-10) =================
   Tate: "lets create a group schedule view where its simple but you see whoever is in the group and at the
   same time when they are free"; "dont hae any writing on anything until you click the specific day"; "show
   profile photos just have the color as a ball next to the profile pic". One week of the term people are in
   now (nowSecs), everyone in their own colour. Free times follow Champ (chGaps: 30 minutes or more; a day of
   8a–6p, wider when a class is earlier or later). Classes are friends-only (my_sections), so a member you
   aren't friends with is shown but has no classes here. The free times count only people whose class times
   are known, and say "everyone" only when that's everybody in the group. */
const GW_COL = ['#2F5FC4', '#B8541A', '#B53A72', '#1B7F74', '#7A4FD0', '#8A6A00', '#56698A', '#8B5A3C'];
const GW_PX = 0.8;   /* px a minute: a 50-minute class is 38px, room for its code and time */
/* You first, then the others in the order they joined; a colour for each person whose classes you can see */
function gwPeople(t) {
  const me = TC.user.id, others = [...new Set((t.members || []).filter(u => u && u !== me))];
  others.forEach(u => ensurePerson(u));
  const list = [{ k: 'me', name: 'You', seen: true }].concat(others.map(u => ({ k: u, name: (PEOPLE[u] && PEOPLE[u].short) || 'Someone', seen: TC.friends.includes(u) && !isBlocked(u) })));
  let c = 0; list.forEach(p => { p.col = p.seen ? GW_COL[c++ % GW_COL.length] : null; });
  return list;
}
const gwTimed = (p, d) => nowSecs(p.k).filter(s => chTimed(s) && s.days.includes(d));
/* the hours the week covers: 8a–6p, wider when someone's class starts earlier or ends later */
function gwSpan(seen) {
  const all = seen.flatMap(p => DAYS.flatMap(d => gwTimed(p, d)));
  if (!all.length) return [CH_S0, CH_DAY_END];
  const a = Math.floor(Math.min(...all.map(s => s.s)) / 60) * 60, b = Math.ceil(Math.max(...all.map(s => s.e)) / 60) * 60;
  return [Math.max(0, Math.min(CH_S0, a)), Math.min(1440, Math.max(CH_DAY_END, b))];
}
/* One day: a block per class (people in the same class at the same time share one; it keeps a section to
   open, yours when you're in it), lanes for overlaps, and the stretches everyone with known times is free. */
function gwDayData(seen, known, d, S0, S1) {
  const by = new Map();
  seen.forEach(p => gwTimed(p, d).forEach(s => {
    const key = s.code + '|' + s.s + '|' + s.e;
    if (!by.has(key)) by.set(key, { code: s.code, s: s.s, e: s.e, id: s.id, who: [] });
    const b = by.get(key); if (!b.who.includes(p)) b.who.push(p);
  }));
  const blocks = [...by.values()].sort((x, y) => x.s - y.s || y.e - x.e || (x.code < y.code ? -1 : x.code > y.code ? 1 : 0));
  let lanes = [], cl = [], end = -1;
  const flush = () => { const n = lanes.length; cl.forEach(b => { b.n = n; }); cl = []; lanes = []; end = -1; };
  blocks.forEach(b => {
    if (cl.length && b.s >= end) flush();
    let l = lanes.findIndex(x => x <= b.s); if (l < 0) { l = lanes.length; lanes.push(0); }
    lanes[l] = b.e; b.l = l; cl.push(b); end = Math.max(end, b.e);
  });
  if (cl.length) flush();
  return { blocks, free: known.length > 1 ? chGaps(blocks, S0, S1) : [] };
}
/* everything the page and the message need, worked out once */
function gwModel(t) {
  const ppl = gwPeople(t), seen = ppl.filter(x => x.seen), hid = ppl.filter(x => !x.seen);
  const known = seen.filter(x => nowSecs(x.k).some(chTimed)), unk = seen.filter(x => !known.includes(x));
  const [S0, S1] = gwSpan(seen), days = {};
  DAYS.forEach(d => { days[d] = gwDayData(seen, known, d, S0, S1); });
  return { ppl, seen, hid, known, unk, everyone: !hid.length && !unk.length, S0, S1, days };
}
/* today, only the free times that haven't ended */
const gwLive = (g, d) => d === CLOCK.day ? g.filter(x => x[1] > CLOCK.min) : g;
/* a shrunk day is ONE line: each stretch someone's in class, in the colours of who's in class then */
function gwSegs(blocks, seen) {
  const cuts = [...new Set(blocks.flatMap(b => [b.s, b.e]))].sort((a, b) => a - b), out = [];
  for (let j = 0; j < cuts.length - 1; j++) {
    const a = cuts[j], z = cuts[j + 1], who = seen.filter(p => blocks.some(b => b.s <= a && b.e >= z && b.who.includes(p)));
    if (!who.length) continue;
    const last = out[out.length - 1];
    if (last && last.e === a && last.who.map(p => p.k).join() === who.map(p => p.k).join()) last.e = z; else out.push({ s: a, e: z, who });
  }
  return out;
}
const gwFill = who => who.length === 1 ? who[0].col : `linear-gradient(90deg,${who.map((p, i) => `${p.col} ${(i * 100 / who.length).toFixed(2)}% ${((i + 1) * 100 / who.length).toFixed(2)}%`).join(',')})`;
const gwCap = w => w.charAt(0).toUpperCase() + w.slice(1);
const gwList = a => a.length <= 2 ? a.join(' and ') : a.slice(0, -1).join(', ') + ' and ' + a[a.length - 1];
const gwHour = m => m >= 1440 ? '12a' : hs(m);
/* how wide a block's time is, in em (Nunito 800, measured in the app), so it can shrink to fit a narrow lane */
const GW_TEM = { ':': .26, '–': .5, a: .56, p: .61 };
const gwTimeEm = t => [...String(t)].reduce((a, c) => a + (GW_TEM[c] || .6), 0);
function gwSendText(p) {
  const t = TC.threads.find(x => x.id === p.id); if (!t || t.kind !== 'group' || !DAYS.includes(p.d)) return '';
  const M = gwModel(t); if (M.known.length < 2) return '';
  const g = gwLive(M.days[p.d].free, p.d); if (!g.length) return '';
  const when = p.d === CLOCK.day ? 'today' : DAYL[p.d], words = chFreeWords(g, M.S0, M.S1);
  if (M.everyone) return `Everyone’s free ${when} ${words}`;
  return `${gwList(M.known.filter(x => x.k !== 'me').map(x => x.name).concat(M.known.some(x => x.k === 'me') ? ['I'] : []))} are free ${when} ${words}`;
}
SCREENS.groupWeek = p => {
  const t = TC.threads.find(x => x.id === p.id);
  if (!t || t.kind !== 'group') return missingScreen('Chat not found.');
  const M = gwModel(t), { ppl, seen, hid, known, unk, everyone, S0, S1 } = M;
  const open = DAYS.includes(p.d) ? p.d : null, today = CLOCK.day, nowMin = CLOCK.min;
  const head = `<div class="gwhd"><button class="iconbtn" data-a="back" aria-label="Back to the chat">${ic('chevL', 22, 2.4)}</button><div class="grow"><div class="gwt">${esc(threadName(t))}</div><div class="gwsub">${esc(nowTerm().label)}</div></div></div>`;
  const tag = x => !x.seen ? (isBlocked(x.k) ? 'Blocked' : 'Not friends') : known.includes(x) ? '' : nowSecs(x.k).length || nowUnplaced(x.k).length ? 'No times' : 'No classes';
  const mem = `<div class="gwmem">${ppl.map(x => {
    const tg = tag(x), nm = x.k === 'me' ? 'You' : nameOf(x.k), pic = `<span class="gwpic">${pav(x.k, 48, 16)}${x.col ? `<span class="gwball" style="background:${x.col}"></span>` : ''}</span><small>${esc(x.name)}</small>${tg ? `<em>${tg}</em>` : ''}`;
    return x.k === 'me' ? `<div class="gwm">${pic}</div>` : `<button class="gwm${x.seen ? '' : ' off'}" data-a="openFriend" data-x="${esc(x.k)}" aria-label="${esc(nm + (tg ? ' · ' + tg : ''))}">${pic}</button>`; }).join('')}</div>`;
  const notes = [];
  if (hid.length) notes.push(seen.length < 2 ? 'You’re not friends with anyone else here, so only your classes show. Classes are shared between friends.'
    : `You’re not friends with ${gwList(hid.map(x => esc(nameOf(x.k).split(' ')[0])))}, so their classes don’t show and the free times leave them out.`);
  if (unk.length && seen.length > 1) {
    const meU = unk.some(x => x.k === 'me'), nms = unk.filter(x => x.k !== 'me').map(x => esc(x.name)).concat(meU ? ['you'] : []);
    notes.push(`${gwCap(gwList(nms))} ${nms.length === 1 && !meU ? 'hasn’t' : 'haven’t'} added class times yet, so the free times don’t count ${meU ? (nms.length === 1 ? 'you' : 'any of you') : 'them'}.`);
  }
  const note = notes.length ? `<div class="gwnote">${notes.join(' ')}</div>` : '';
  const myErr = splitTerms() ? TC.err.nowMine : TC.err.mine;
  let main;
  if (!TC.ready) main = loadingCard('Loading everyone’s classes…');
  else if (TC.err.friends || TC.err.friendSecs || myErr) main = errCard('Couldn’t load everyone’s classes.', 'refresh');
  else {
    const H = Math.round((S1 - S0) * GW_PX), Y = m => Math.round((m - S0) * GW_PX), ax = [];
    if (open) for (let m = S0; m <= S1; m += 120) ax.push(`<span style="top:${Y(m)}px;transform:${m === S0 ? 'none' : m === S1 ? 'translateY(-100%)' : 'translateY(-50%)'}">${gwHour(m)}</span>`);
    const hdr = DAYS.map(d => { const on = d === open, thin = !!open && !on;
      return `<button class="gwdh${on ? ' on' : ''}${!open && d === today ? ' gwtd' : ''}${thin ? ' thin' : ''}" data-gw="h${d}" data-a="gwDay" data-x="${d}" aria-pressed="${on}" aria-label="${on ? DAYL[d] + ', open. Tap to close' : 'Open ' + DAYL[d]}">${on ? DAYL[d].toUpperCase() : thin ? DAYN[d][0] : DAYN[d].toUpperCase()}</button>`; }).join('');
    const freeWord = everyone ? 'Everyone free' : 'Free together';
    const cols = DAYS.map(d => {
      const on = d === open, thin = !!open && !on, { blocks, free } = M.days[d];
      let inner;
      if (thin) {
        const sg = gwSegs(blocks, seen);
        inner = sg.map((g, j) => { const up = j > 0 && sg[j - 1].e === g.s, dn = j < sg.length - 1 && sg[j + 1].s === g.e, r = (a, b) => `${a ? 0 : 3}px ${a ? 0 : 3}px ${b ? 0 : 3}px ${b ? 0 : 3}px`;
          return `<span class="gwseg" style="top:${Y(g.s) + (up ? 0 : 1)}px;height:${Math.max(2, Y(g.e) - Y(g.s) - (up ? 0 : 1) - (dn ? 0 : 1))}px;background:${gwFill(g.who)};border-radius:${r(up, dn)}"></span>`; }).join('');
      } else {
        /* today, a free time that's over is dimmed and says nothing */
        inner = free.map(g => { const past = d === today && g[1] <= nowMin;
          return `<span class="gwfree${past ? ' past' : ''}" style="top:${Y(g[0]) + 1}px;height:${Math.max(2, Y(g[1]) - Y(g[0]) - 2)}px">${on && !past ? `<span>${freeWord}<br>${esc(gwCap(chFreeWords([g], S0, S1)))}</span>` : ''}</span>`; }).join('')
          + blocks.map(b => {
            const top = Y(b.s) + 1, h = Math.max(4, Y(b.e) - Y(b.s) - 2), W = `(100% - ${8 + (b.n - 1) * 4}px)`;
            const st = `top:${top}px;height:${h}px;left:calc(4px + ${W} * ${b.l} / ${b.n} + ${b.l * 4}px);width:calc(${W} / ${b.n});background:${gwFill(b.who)}`;
            const sz = `;--cw:${textEm(b.code).toFixed(2)};--tw:${gwTimeEm(gridTime(b)).toFixed(2)}`;
            if (!on) return `<span class="gwb" style="${st}"></span>`;
            const you = b.who.length > 1 && b.who.some(x => x.k === 'me'), code = `<b>${esc(b.code)}</b>`, tm = `<i>${gridTime(b)}</i>`;
            /* as many faces as the lane has room for; the rest as +N */
            const fc = (px, max) => { if (!max) return ''; const w = b.who, sh = w.length <= max ? w : w.slice(0, max - 1);
              return `<span class="gwfc${px < 18 ? ' in' : ''}">${sh.map(x => pav(x.k, px, px * .36)).join('')}${sh.length < w.length ? `<span class="gwmore" style="height:${px}px">+${w.length - sh.length}</span>` : ''}</span>`; };
            /* what fits: code, time and faces stacked; code and faces, then the time; code and time on one line; colour only */
            const [k, inner2] = h >= 61 ? ['tall', code + tm + fc(18, b.n === 1 ? 5 : b.n === 2 ? 3 : 2)] : h >= 38 ? ['mid', `<span class="gwl1">${code}${fc(16, b.n === 1 ? 3 : b.n === 2 ? 1 : 0)}</span>${tm}`] : h >= 19 ? ['short', `<span class="gwl1">${code}${tm}</span>`] : ['tiny', ''];
            return `<button class="gwb ${k}${you ? ' you' : ''}" style="${st}${sz}" data-a="secSheet" data-x="${esc(b.code)}" data-y="${esc(String(b.id))}" aria-label="${esc(b.code + ' · ' + gridTime(b) + ' · ' + gwList(b.who.map(x => x.k === 'me' ? 'you' : x.name)))}">${inner2}</button>`;
          }).join('');
      }
      const now = !thin && d === today && nowMin >= S0 && nowMin <= S1 ? `<span class="gwnow" style="top:${Y(nowMin)}px"></span>` : '';
      return `<div class="gwc${on ? ' on' : ''}${thin ? ' thin' : ''}" data-gw="c${d}" data-a="gwDay" data-x="${d}">${inner}${now}</div>`;
    }).join('');
    let sum = '';
    if (open && known.length > 1) {
      const all = M.days[open].free, g = gwLive(all, open), lead = open === today ? 'TODAY' : DAYL[open].toUpperCase();
      sum = g.length ? `<div class="gwsum"><div class="grow"><div class="gwsum-t">${lead} · ${everyone ? 'EVERYONE FREE' : 'FREE TOGETHER'}</div><div class="gwsum-f">${esc(g.map(x => gwCap(chFreeWords([x], S0, S1))).join(' · '))}</div></div><button class="gwsend" data-a="gwSend"${UI.busy.gwSend ? ' disabled' : ''}>${UI.busy.gwSend ? 'Sending…' : 'Send to chat'}</button></div>`
        : `<div class="gwsum none"><div class="grow"><div class="gwsum-t">${lead}</div><div class="gwsum-f">${all.length ? 'No more free time together today' : 'No free time together'}</div></div></div>`;
    }
    const gut = open ? 30 : 0;
    main = `<div data-gw="sum">${sum}</div><div class="card gwcard"><div class="gwhr" data-gw="hr" style="padding-left:${gut}px">${hdr}</div><div class="gwbody" style="height:${H}px"><div class="gwax" data-gw="ax">${ax.join('')}</div><div class="gwcols" data-gw="cols" style="left:${gut}px">${cols}</div></div></div><div class="gwhint" data-gw="hint">${open ? '' : 'Tap a day to see who’s where'}</div>`;
  }
  return { body: `<div class="gwpg" id="gw" data-id="${esc(String(t.id))}">${head}${mem}${note}${main}</div><div style="height:48px"></div>`, tabbar: false, fab: false };
};
/* Tapping a day changes the page in place, so days slide open and shut instead of the page being redrawn:
   the parts that change carry data-gw, and each takes the new page's attribute values (every keyed part always
   has the same attributes) and, when nothing keyed is inside it, its contents. Anything else — a load
   finishing, another page — redraws as usual. */
function gwMorph() {
  const e = cur(), live = document.getElementById('gw');
  if (!e || e.s !== 'groupWeek' || !live || live.dataset.id !== String(e.p.id)) return render(true);
  const tpl = document.createElement('template'); tpl.innerHTML = SCREENS.groupWeek(e.p).body;
  const next = tpl.content.getElementById('gw');
  const a = [...live.querySelectorAll('[data-gw]')], b = next ? [...next.querySelectorAll('[data-gw]')] : [];
  if (!a.length || a.length !== b.length || a.some((x, i) => x.dataset.gw !== b[i].dataset.gw)) return render(true);
  a.forEach((x, i) => {
    const y = b[i];
    [...y.attributes].forEach(at => { if (x.getAttribute(at.name) !== at.value) x.setAttribute(at.name, at.value); });
    if (!y.querySelector('[data-gw]') && x.innerHTML !== y.innerHTML) x.innerHTML = y.innerHTML;
  });
}

/* A friend's Plans A–C — only what they chose to share (RLS returns a plan only while its "friends''')

# 4. actions
one("""  chatMenu: cid => { UI.sheet = { type: 'chatAct', cid }; render(true); },""",
    """  chatMenu: cid => { UI.sheet = { type: 'chatAct', cid }; render(true); },
  /* group schedule (2026-10-10) */
  openGroupWeek: cid => {
    /* keep a half-typed message: go() draws the new page before render() would save it */
    const ci = document.getElementById('chatin'), fm = ci && ci.closest('form'); if (fm && fm.dataset.x === String(cid)) UI.prefill = { id: cid, text: ci.value };
    go('groupWeek', { id: cid, d: null });   /* go() closes the sheet and Champ */
  },
  gwDay: d => { const e = cur(); if (!e || e.s !== 'groupWeek' || !DAYS.includes(d)) return; e.p.d = e.p.d === d ? null : d; gwMorph(); },
  gwSend: async () => {
    const e = cur(); if (!e || e.s !== 'groupWeek' || UI.busy.gwSend) return;
    const txt = gwSendText(e.p); if (!txt) return;
    UI.busy.gwSend = 1; gwMorph();
    let ok = false;
    try { ok = await TC.send(e.p.id, txt); } catch (err) { toast('Couldn’t send — try again'); } finally { UI.busy.gwSend = 0; }
    if (!ok) return gwMorph();   /* TC.send says why */
    toast('Sent to the chat');
    if (onPage('groupWeek', e.p.id)) A.openChat(e.p.id); else render(true);
    TC.pushAsk('chat');
  },""")

# 5. styles
one(""".chathdr{display:flex;align-items:center;gap:10px;padding:8px 14px 10px;background:var(--glass2);backdrop-filter:blur(10px);border-bottom:1px solid var(--line)}""",
    """.chathdr{display:flex;align-items:center;gap:10px;padding:8px 14px 10px;background:var(--glass2);backdrop-filter:blur(10px);border-bottom:1px solid var(--line)}
/* group schedule (2026-10-10) */
.chathdr .gwbtn{width:40px;height:40px;flex:none;color:var(--blue-t,var(--blue))}
.chathdr [data-a="chatMenu"]{min-width:0}
.chathdr [data-a="chatMenu"] > div:first-child{display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden;overflow-wrap:anywhere}
.gwpg{padding:0 10px}
.gwhd{display:flex;align-items:center;gap:12px;padding:10px 6px 16px}
.gwhd .grow{min-width:0}
.gwt{font-size:19px;font-weight:900;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.gwsub{font-size:12.5px;font-weight:800;color:var(--muted)}
.gwmem{display:grid;grid-auto-flow:column;grid-auto-columns:minmax(58px,1fr);overflow-x:auto;scrollbar-width:none;padding:2px 0 4px;margin-bottom:14px}
.gwmem::-webkit-scrollbar{display:none}
.gwm{display:flex;flex-direction:column;align-items:center;gap:6px;min-width:0;padding:0 2px}
.gwpic{position:relative;flex:none;display:block;width:48px;height:48px}
.gwball{position:absolute;right:-3px;bottom:-1px;width:15px;height:15px;border-radius:50%;box-shadow:0 0 0 3px var(--bg)}
.gwm small{font-size:12px;font-weight:800;color:var(--ink3);max-width:100%;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.gwm em{font-style:normal;font-size:10.5px;font-weight:800;color:var(--ink3);margin-top:-4px;white-space:nowrap}
.gwm.off .gwpic{opacity:.5}
.gwnote{font-size:12.5px;font-weight:800;color:var(--muted);margin:-4px 6px 14px;line-height:1.4}
.gwsum{display:flex;align-items:center;gap:10px;background:var(--green-wash);border-radius:18px;padding:10px 10px 10px 14px;margin-bottom:12px}
.gwsum .grow{min-width:0}
.gwsum-t{font-size:11px;font-weight:900;color:var(--green-ink2);letter-spacing:.06em}
.gwsum-f{font-size:15px;font-weight:900;color:var(--ink)}
.gwsum.none{background:var(--card)}
.gwsum.none .gwsum-t{color:var(--muted)}
.gwsend{flex:none;height:40px;padding:0 14px;border-radius:12px;background:#15803D;color:#fff;font-weight:900;font-size:13.5px}
.gwsend:disabled{opacity:.6}
.gwcard{padding:14px 8px 12px}
.gwhr{display:flex;gap:6px;transition:padding-left .25s ease}
.gwdh{flex:1 1 0;min-width:0;height:24px;padding:0;text-align:center;font-size:11px;font-weight:900;letter-spacing:.06em;color:var(--muted);overflow:hidden;white-space:nowrap;transition:flex .25s ease}
.gwdh.thin{flex:0 0 12px;letter-spacing:0;position:relative;overflow:visible}
.gwdh.thin::after,.gwc.thin::after{content:'';position:absolute;top:0;bottom:0;left:-3px;right:-3px}
.gwdh.on,.gwdh.gwtd{color:var(--blue-t,var(--blue))}
.gwbody{position:relative;margin-top:10px}
.gwax span{position:absolute;left:0;width:26px;text-align:right;font-size:10px;font-weight:800;color:var(--muted)}
.gwcols{position:absolute;right:0;top:0;bottom:0;display:flex;gap:6px;transition:left .25s ease}
.gwc{position:relative;flex:1 1 0;min-width:0;border-radius:12px;background:var(--bg);cursor:pointer;transition:flex .25s ease,background .25s ease}
.gwc.thin{flex:0 0 12px;background:transparent}
.gwb{position:absolute;border-radius:8px;overflow:hidden;color:#fff;box-sizing:border-box}
button.gwb{container-type:inline-size;display:flex;flex-direction:column;align-items:stretch;justify-content:flex-start;gap:2px;padding:5px 8px;text-align:left}
button.gwb.mid{gap:1px;padding:4px 8px}
button.gwb.short{padding:0 8px;justify-content:center}
button.gwb.tiny{padding:0}
.gwl1{display:flex;align-items:center;gap:6px;min-width:0}
.gwl1 b{flex:0 0 auto;max-width:100%}
.gwl1 i{flex:1 1 auto;min-width:0}
.gwb b{display:block;font-size:13.5px;font-size:clamp(9px,(100cqi - 16px) / var(--cw,6),13.5px);font-weight:900;line-height:1.1;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.gwb i{display:block;font-style:normal;font-size:12px;font-size:clamp(9px,(100cqi - 16px) / var(--tw,6.5),12px);font-weight:800;line-height:1.15;color:#fff;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.gwb.you{box-shadow:inset 0 0 0 2px #FACC15}
.gwfc{display:flex;gap:4px;margin-top:auto;flex:none;overflow:hidden}
.gwfc.in{margin:0 0 0 auto;gap:3px;flex:0 1 auto;min-width:0}
.gwmore{flex:none;display:inline-grid;place-items:center;min-width:18px;padding:0 4px;box-sizing:border-box;border-radius:999px;background:rgba(10,15,28,.35);color:#fff;font-size:10px;font-weight:900}
.gwfree{position:absolute;left:4px;right:4px;border-radius:8px;background:var(--green-wash);display:flex;align-items:center;justify-content:center;text-align:center;overflow:hidden}
.gwfree span{font-size:13px;font-weight:900;color:var(--green-ink2);line-height:1.25}
.gwfree.past{opacity:.4}
.gwseg{position:absolute;left:calc(50% - 3px);width:6px}
.gwnow{position:absolute;left:0;right:0;height:2px;background:#DC2626;z-index:3;pointer-events:none}
.gwhint{text-align:center;font-size:13px;font-weight:800;color:var(--muted);margin-top:12px}
.gwhint:empty{display:none}
@media (prefers-reduced-motion:reduce){.gwc,.gwdh,.gwhr,.gwcols{transition:none}}""")

f.write_text(s)
print('patched', f)
