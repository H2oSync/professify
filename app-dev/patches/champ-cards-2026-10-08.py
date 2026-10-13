#!/usr/bin/env python3
"""Champ answers as previews you can tap (Tate, 2026-10-08, canvas "Champ Answers With Previews", pick B).

Every Champ answer is one short line plus, when there is something to see, a full-width card drawn from the
app's own data at render time (seats and ratings are always current) that opens the real screen, and a row of
follow-up questions. Answers:
  - does X fit my Plan A / my schedule  -> the plan's week with X's best section dashed in, verdict, Add / Open
  - when am I free <day>                -> the day as a timeline: classes, and free stretches of 30+ minutes
  - when am I free (week)               -> a row per day with its classes and free stretches
  - who's free with me <day>            -> friends free at the same time as you, longest overlap first
  - best professor for X                -> the top professor's card (the professor page's look) + the others
  - a professor                         -> their card; a class -> its card with its best sections
  - open sections / swap                -> section cards with fits/clashes and +
  - prerequisites                       -> a checklist with what's done, taking, missing
  - game plan                           -> the plan's classes scarcest first with a seat bar and a backup
  - who's free now                      -> free friends with their day strip, then who's in class
The model still only names a tool; nothing on a card comes from it.

Usage: python3 champ-cards-2026-10-08.py <repo-dir>   (after native-review-polish-2026-10-07.py)
"""
import sys, os
d = sys.argv[1]
p = os.path.join(d, 'app', 'index.html')
s = open(p, encoding='utf-8').read()

def rep(a, b, n=1):
    global s
    c = s.count(a)
    if c != n:
        sys.exit(f'anchor matched {c}x (want {n}): {a[:90]!r}')
    s = s.replace(a, b)

def between(start, end, body):
    """Replace from `start` (inclusive) up to `end` (exclusive)."""
    global s
    i = s.find(start)
    j = s.find(end, i + 1)
    if i < 0 or j < 0 or s.count(start) != 1:
        sys.exit(f'region not found: {start[:60]!r} .. {end[:60]!r}')
    s = s[:i] + body + s[j:]

# ---- CSS -------------------------------------------------------------------------------------------------
CSS = r""".act.primary{background:var(--blue);color:#fff}
/* ---- Champ answer cards (Tate, 2026-10-08) ---- */
.sheet.champ #champscroll{background:var(--bg)}
.sheet.champ .bot .msg{background:var(--card);box-shadow:0 1px 2px rgba(15,23,42,.06)}
.chc-wrap{align-self:stretch;display:flex;flex-direction:column;gap:8px;margin:0 0 2px}
.chc{background:var(--card);border-radius:22px;padding:12px;box-shadow:0 1px 2px rgba(15,23,42,.04),0 10px 26px rgba(22,51,107,.07)}
.chc-h{display:flex;align-items:center;gap:8px;padding:0 2px 6px}
.chc-t{font-size:16px;font-weight:900;flex:1;min-width:0}
.chc-open{min-height:44px;padding:0 4px;font-size:14px;font-weight:900;color:var(--blue-t,var(--blue))}
.chchip{display:inline-flex;align-items:center;gap:4px;font-size:12.5px;font-weight:800;padding:4px 10px;border-radius:99px;background:var(--fill);color:var(--ink3);white-space:nowrap}
.chchip.ok{background:var(--ok-soft);color:var(--ok-ink)}
.chchip.bad{background:var(--red-soft);color:var(--red-ink)}
.chchip.blue{background:var(--blue-soft);color:var(--blue-ink)}
.chchip .stack{margin-right:2px}
.chc-facts{display:flex;flex-wrap:wrap;gap:6px;margin-top:10px}
.chc-btns{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:8px;margin-top:12px}
.chc-btns .btn{height:46px;font-size:15px}
.chplan{flex:none;font-size:13px;font-weight:900;padding:5px 11px;border-radius:99px;background:var(--pc,var(--blue));color:#fff}
.chc .g-b.ghost{background:color-mix(in srgb,var(--blue) 14%,var(--card));color:var(--blue-ink);outline:2px dashed var(--blue);outline-offset:-2px;box-shadow:none}
.chc .g-b.ghost.clash{background:#DC2626;color:#fff;outline-color:#DC2626}
.chc .g-b.clashb{background:var(--red-soft);color:var(--red-ink);box-shadow:inset 0 0 0 2px #DC2626}
.chk{display:block;font-size:11.5px;font-weight:900;letter-spacing:.08em;color:var(--ink4);text-transform:uppercase}
.chbad{color:var(--red-ink);font-weight:900}
.chd{display:grid;grid-template-columns:30px minmax(0,1fr);gap:6px}
.chd-lab{position:relative;font-size:10.5px;font-weight:800;color:var(--muted)}
.chd-lab span{position:absolute;left:0;transform:translateY(-50%)}
.chd-lab span:first-child{transform:none}
.chd-col{position:relative;border-radius:12px;background:var(--bg)}
.chd-b{position:absolute;left:4px;right:4px;border-radius:10px;background:var(--blue-soft2);color:var(--blue-ink);display:flex;flex-wrap:wrap;align-items:center;align-content:center;gap:2px 8px;padding:0 8px 0 10px;font-size:13px;text-align:left;overflow:hidden}
.chd-b b{font-weight:900;white-space:nowrap}
.chd-b>span{font-weight:800;white-space:nowrap}
.chd-b .chchip{margin-left:auto;padding:2px 7px;font-size:11.5px}
.chd-f{position:absolute;left:4px;right:4px;border-radius:10px;border:2px dashed var(--line2);background:var(--card);display:flex;flex-direction:column;justify-content:center;padding:0 12px;font-size:13px;overflow:hidden}
.chd-f b{font-weight:900}
.chd-f.one{flex-direction:row;align-items:center;gap:8px}
.chd-f span{font-size:12px;font-weight:800;color:var(--muted)}
.chd-now{position:absolute;left:0;right:0;height:2px;background:#DC2626;pointer-events:none}
.chw-row{display:flex;align-items:center;gap:10px;width:100%;min-height:54px;border-bottom:1px solid var(--line);text-align:left}
.chw-row:last-of-type{border-bottom:0}
.chw-d{flex:none;width:34px;font-weight:900;font-size:14px}
.chw-m{flex:1;min-width:0;display:flex;flex-direction:column;gap:5px}
.chw-bar{position:relative;display:block;height:10px;border-radius:5px;background:var(--fill)}
.chw-bar i{position:absolute;top:0;bottom:0;border-radius:5px;background:var(--blue-mid)}
.chw-t{font-size:12.5px;font-weight:800;color:var(--ink3)}
.chw-ax{display:flex;justify-content:space-between;padding:2px 26px 0 44px;font-size:10.5px;font-weight:800;color:var(--muted)}
.chp{padding:0;overflow:hidden}
.chp-top{display:flex;align-items:center;gap:12px;width:100%;padding:14px;background:var(--purple);color:#fff;text-align:left}
.chp-top b{display:block;font-size:18px;font-weight:900}
.chp-top .grow>span{display:block;font-size:13px;font-weight:800;opacity:.92}
.chp-avg{flex:none;text-align:right}
.chp-avg b{font-size:26px;line-height:1}
.chp-avg span{font-size:10.5px;font-weight:900;letter-spacing:.06em;opacity:.92}
.chp-tiles{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:8px;padding:12px 14px 0}
.chp-tiles div{background:var(--bg);border-radius:14px;padding:8px 10px}
.chp-tiles b{display:block;font-size:17px;font-weight:900}
.chp-tiles span{font-size:11.5px;font-weight:800;color:var(--ink4)}
.chp-secs{padding:10px 14px 14px;display:flex;flex-direction:column;gap:8px}
.chp-sec{display:flex;align-items:center;gap:10px;width:100%;min-height:56px;padding:8px 10px 8px 12px;border-radius:14px;background:var(--bg);text-align:left}
.chp-sec b{display:block;font-size:14px;font-weight:900}
.chp-sec .grow>span{display:block;font-size:12.5px;font-weight:800;color:var(--ink4)}
.chp-plus{flex:none;width:36px;height:36px;border-radius:50%;background:var(--blue);color:#fff;display:grid;place-items:center}
.chp-teach{display:flex;flex-wrap:wrap;gap:6px;align-items:center;padding:12px 14px 14px}
.chp-teach .chk{width:100%}
.chp-teach button{min-height:44px;padding:0 14px;border-radius:22px;background:var(--blue-soft);color:var(--blue-ink);font-size:13.5px;font-weight:900}
.chrows{padding:2px 12px}
.chr{display:flex;align-items:center;gap:10px;width:100%;min-height:62px;text-align:left;border-bottom:1px solid var(--line)}
.chr:last-child{border-bottom:0}
.chr b{display:block;font-size:15px;font-weight:900}
.chr .grow>span{display:block;font-size:12.5px;font-weight:800;color:var(--muted)}
.chc-cls{display:flex;align-items:center;gap:8px;width:100%;min-height:44px;text-align:left}
.chc-cls b{flex:1;min-width:0;font-size:15.5px;font-weight:900}
.chc-more{display:block;margin:4px auto 0;min-height:44px;font-size:14px;font-weight:900;color:var(--blue-t,var(--blue))}
.chs{display:grid;grid-template-columns:minmax(0,1fr) auto;gap:6px 10px;align-items:start;padding:10px 0 2px;border-top:1px solid var(--line)}
.chc>.chs:first-child{border-top:0;padding-top:0}
.chs-main{text-align:left;min-height:44px;display:flex;flex-direction:column;gap:2px}
.chs-h{font-size:13.5px}
.chs-h b{font-weight:900}
.chs-t{font-size:15px;font-weight:900}
.chs-w{font-size:13px;font-weight:800;color:var(--ink3)}
.chs-add{width:44px;height:44px;border-radius:50%;background:var(--blue);color:#fff;display:grid;place-items:center}
.chs-f{grid-column:1/-1;display:flex;flex-wrap:wrap;gap:6px;padding-bottom:6px}
.chpp{padding:8px 0;border-bottom:1px solid var(--line)}
.chpp:last-child{border-bottom:0}
.chpp-top{display:flex;align-items:center;gap:10px}
.chpp-main{display:flex;align-items:center;gap:12px;flex:1;min-width:0;text-align:left;min-height:48px}
.chpp-main b{display:block;font-size:15.5px;font-weight:900}
.chpp-main .grow>span{display:block;font-size:12.5px;font-weight:800;color:var(--muted)}
.chpp.free .av{box-shadow:0 0 0 2px var(--card),0 0 0 4px var(--green)}
.chpp-top .act{height:44px;padding:0 14px;border-radius:22px}
.chpp-bar{position:relative;display:block;height:12px;border-radius:6px;background:var(--fill);margin:6px 0 2px 56px}
.chpp-bar i{position:absolute;top:2px;bottom:2px;border-radius:4px;background:var(--blue-mid)}
.chpp-bar em{position:absolute;top:-2px;bottom:-2px;width:2px;background:#DC2626}
.chq-bar{height:8px;border-radius:4px;background:var(--fill);margin:4px 0 6px;overflow:hidden}
.chq-bar i{display:block;height:100%;background:var(--blue);border-radius:4px}
.chq{display:flex;gap:12px;align-items:flex-start;padding:10px 0;border-top:1px solid var(--line)}
.chq-dot{flex:none;width:28px;height:28px;border-radius:50%;display:grid;place-items:center;font-weight:900;font-size:14px}
.chq-dot.ok{background:var(--teal-soft);color:var(--teal-t,var(--teal))}
.chq-dot.now{background:var(--blue-soft);color:var(--blue-ink)}
.chq-dot.need{box-shadow:inset 0 0 0 2px var(--line2)}
.chq-dot.unk{color:var(--ink4);background:var(--fill)}
.chq b{display:block;font-size:15px;font-weight:900}
.chq .grow>span{display:block;font-size:12.5px;font-weight:800;color:var(--muted)}
.chq-links{display:flex;flex-wrap:wrap;gap:6px;margin-top:6px}
.chq-links button{min-height:44px;padding:0 14px;border-radius:22px;background:var(--blue-soft);color:var(--blue-ink);font-size:13.5px;font-weight:900}
.chg{display:flex;gap:12px;align-items:flex-start;width:100%;padding:10px 0;border-top:1px solid var(--line);text-align:left}
.chg-n{flex:none;width:28px;height:28px;border-radius:50%;display:grid;place-items:center;font-size:13px;font-weight:900}
.chg-n.hot{background:var(--red-soft);color:var(--red-ink)}
.chg-n.mid{background:var(--amber-soft);color:var(--amber-ink)}
.chg-n.ok{background:var(--teal-soft);color:var(--teal-t,var(--teal))}
.chg-n.unk{background:var(--fill);color:var(--ink4)}
.chg b{font-size:15px;font-weight:900}
.chg .w{font-size:12.5px;font-weight:800;color:var(--muted);margin-left:6px}
.chg-bar{display:flex;align-items:center;gap:8px;margin-top:6px}
.chg-bar>span:first-child{flex:1;height:7px;border-radius:4px;background:var(--fill);overflow:hidden}
.chg-bar i{display:block;height:100%;border-radius:4px}
.chg-bar>span:last-child{font-size:12px;font-weight:900;white-space:nowrap}
.chg-bk{font-size:12px;font-weight:800;color:var(--muted);margin-top:4px}
.chfollow{display:flex;gap:8px;flex-wrap:wrap;margin:2px 0 4px}
.chfollow button{min-height:44px;padding:0 14px;border-radius:22px;border:1.5px solid var(--line2);background:var(--card);font-size:14px;font-weight:800;color:var(--ink)}
"""
rep(".act.primary{background:var(--blue);color:#fff}\n", CSS)

# ---- the answers -----------------------------------------------------------------------------------------
JS = r"""/* ================= Champ answer cards (Tate, 2026-10-08: "the AI kind of fills in an image") =================
   An answer is { t: one short line, card: { k, …ids }, acts, follow }. The card is drawn when the chat
   renders, from the app's data at that moment (seats and ratings are always current), and every part of it
   opens the real screen. follow = questions the student can tap next. Nothing on a card comes from the model. */
const CH_S0 = 480;                                   /* a day card starts at 8a */
const chTimed = s => !!s && !s.async && s.s != null && s.e != null;
const chRank = s => s.status === 'open' ? 0 : s.status === 'wait' ? 1 : s.status === 'unknown' ? 2 : 3;
const chLen = m => { const h = Math.floor(m / 60), r = m % 60; return (h ? h + 'h' : '') + (h && r ? ' ' : '') + (r ? r + 'm' : ''); };
const chChip = (html, cls) => `<span class="chchip${cls ? ' ' + cls : ''}">${html}</span>`;
const chLast = pk => PROFS[pk] ? PROFS[pk].name.split(' ').slice(-1)[0] : '';
const chStar = (r, who) => { const t = rateTone(r); return t ? `<span class="chchip" style="background:${t.bg};color:${t.ink}">${starI(12, t.star)} ${r.toFixed(1)}${who ? ' ' + esc(who) : ''}</span>` : chChip('No ratings yet' + (who ? ' · ' + esc(who) : '')); };
const chProfChip = s => s.prof && PROFS[s.prof] ? chStar(ratingOf(s.prof), chLast(s.prof)) : chChip('Instructor not assigned');
const chPlanLabel = P => P === 'mine' ? 'your classes' : 'Plan ' + P;
function chDaySecs(id, d) { return personSecs(id).filter(s => chTimed(s) && s.days.includes(d)).sort((a, b) => a.s - b.s); }
/* Free stretches of 30 minutes or more from a to b around a day's classes (a 10-minute walk isn't free time). */
function chGaps(list, a, b) {
  const out = []; let t = a;
  list.forEach(s => { if (s.s > t && Math.min(s.s, b) - t >= 30) out.push([t, Math.min(s.s, b)]); t = Math.max(t, s.e); });
  if (b - t >= 30) out.push([t, b]);
  return out;
}
const chDayStart = list => Math.min(CH_S0, list.length ? Math.floor(list[0].s / 60) * 60 : CH_S0);
const chDayEnd = list => Math.min(1440, Math.max(1080, list.length ? Math.ceil((list[list.length - 1].e + 60) / 60) * 60 : 0));
function chFreeWords(gaps, S0, S1) {
  const w = g => g[0] <= S0 && g[1] >= S1 ? 'all day' : g[0] <= S0 ? 'before ' + hs(g[1]) : g[1] >= S1 ? 'after ' + hs(g[0]) : hs(g[0]) + '–' + hs(g[1]);
  const ws = gaps.map(w);
  return ws.length <= 2 ? ws.join(' and ') : ws.slice(0, -1).join(', ') + ' and ' + ws[ws.length - 1];
}
const CH_DAYW = /\b(mon(?:day)?|tues?(?:day)?|wed(?:nesday|s)?|thu(?:rs?)?(?:day)?|fri(?:day)?)\b/g;
const chDaysIn = t => [...String(t).matchAll(CH_DAYW)].map(m => ({ mon: 'M', tue: 'T', wed: 'W', thu: 'R', fri: 'F' })[m[1].slice(0, 3)]);
const chDayOf = t => { const ds = chDaysIn(t); if (ds.length) return ds[ds.length - 1];
  if (/\btomorrow\b/.test(t)) return DAYS[(DAYS.indexOf(CLOCK.day) + 1) % 5] || 'M';
  return DAYS.includes(CLOCK.day) ? CLOCK.day : 'M'; };
const chNextDay = d => DAYS[(DAYS.indexOf(d) + 1) % 5];

/* ---- does a class fit a plan (or your classes)? ---- */
function chFitCalc(code, P) {
  const base = P === 'mine' ? personSecs('me') : planSecs(P), ids = base.map(s => s.id);
  const inIt = base.find(s => s.code === code) || null;
  const clashOf = s => !chTimed(s) ? [] : P === 'mine' ? clashWithMine(s) : conflicts(ids, s);
  const sc = secsOf(code).map(s => ({ s, cl: clashOf(s) }))
    .sort((a, b) => a.cl.length - b.cl.length || chRank(a.s) - chRank(b.s) || ((ratingOf(b.s.prof) ?? -1) - (ratingOf(a.s.prof) ?? -1)));
  return { base, ids, inIt, best: sc[0] || null, fits: sc.filter(x => !x.cl.length).length, n: sc.length, clashOf };
}
function ansFit(code, P) {
  P = P === 'mine' || AT_PLANS.includes(P) ? P : S.plan;
  if (!TC.seatsLoaded) return { t: 'Classes are still loading — ask again in a moment.' };
  if (!COURSES[code] || !secsOf(code).length) return { t: `${esc(code)} isn’t offered in ${esc(CFG.TERM_LABEL)}.` };
  if (P === 'mine' && !personSecs('me').some(chTimed)) return { t: `You haven’t added ${esc(CFG.TERM_LABEL)} classes with times yet, so anything fits.`, card: { k: 'cls', code }, acts: [['Open Schedule', 'tab', 'schedule']] };
  const f = chFitCalc(code, P), L = chPlanLabel(P);
  const follow = [P === 'mine' ? `Does ${code} fit my Plan ${S.plan}?` : `Does ${code} fit my schedule?`, `Best professor for ${code}?`];
  if (f.inIt) return { t: `${esc(code)} is already in ${L}.`, card: { k: 'fit', code, P, id: f.inIt.id }, follow };
  const s = f.best.s;
  if (!chTimed(s)) return { t: `Yes — ${esc(secLabel(s.sec))} has no set time, so it fits ${L}.`, card: { k: 'fit', code, P, id: s.id }, follow };
  if (!f.best.cl.length) return { t: `Yes — ${esc(secLabel(s.sec))} fits ${L}${f.fits > 1 ? ` (${f.fits} of ${f.n} sections do)` : ''}.`, card: { k: 'fit', code, P, id: s.id }, follow };
  return { t: `No — every ${esc(code)} section clashes with ${L}.`, card: { k: 'fit', code, P, id: s.id }, follow: [`Other ${code} sections?`].concat(follow.slice(1)) };
}
function chFit(c) {
  const f = chFitCalc(c.code, c.P), s = SEC[c.id] || (f.best && f.best.s); if (!s) return '';
  const inIt = f.inIt && f.inIt.id === s.id, cl = inIt ? [] : f.clashOf(s), P = c.P;
  const secs = inIt ? f.base : f.base.filter(x => x.code !== s.code).concat([s]);
  const wk = secs.some(chTimed) ? `<div class="${P === 'mine' ? '' : 'plancol plan-' + P}" style="margin:0 -6px">${grid(secs, { sel: S.homeDays['ch:' + c.n], act: 'homeDay', key: 'ch:' + c.n, blockAct: 'openClass', ghost: inIt ? null : s.id, clash: cl.length > 0, clashIds: new Set(cl.map(x => x.id)), noNow: true, one: true, fit: 26, H: 250 })}</div>` : '';
  const verdict = inIt ? chChip('In ' + esc(chPlanLabel(P)), 'blue') : cl.length ? chChip('Clashes with ' + esc(cl.map(x => x.code).join(', ')), 'bad') : chChip('✓ No clashes', 'ok');
  const open = P === 'mine' ? `<button class="chc-open" data-a="schedTabGo" data-x="mine">Open ›</button>` : `<button class="chc-open" data-a="champPlan" data-x="${P}">Open ›</button>`;
  const head = `<div class="chc-h ${P === 'mine' ? 'dest-mine' : 'plan-' + P}"><span class="chplan">${P === 'mine' ? 'My Classes' : 'Plan ' + P}</span><span class="chc-t" style="font-size:14px;color:var(--muted)">${esc(s.code)} ${esc(secLabel(s.sec))}</span>${open}</div>`;
  const add = inIt ? '' : `<button class="btn" data-a="champAddTo" data-x="${esc(s.id)}" data-y="${P}">${P === 'mine' ? 'Add it' : 'Add to Plan ' + P}</button>`;
  return `<section class="chc" aria-label="${esc(s.code + ' in ' + chPlanLabel(P))}">${head}${wk}<div class="chc-facts">${verdict}${chChip(esc(secWhen(s)))}${chProfChip(s)}${chChip(secSeatText(s))}</div><div class="chc-btns">${add}<button class="btn soft" data-a="openClass" data-x="${esc(s.code)}" ${add ? '' : 'style="grid-column:1/-1"'}>Open ${esc(s.code)}</button></div></section>`;
}

/* ---- your day, and your week's free time ---- */
function ansDayCard(d, mode) {
  if (!personSecs('me').some(chTimed)) return { t: `You haven’t added ${esc(CFG.TERM_LABEL)} classes with times yet.`, acts: [['Open Schedule', 'tab', 'schedule']] };
  const l = chDaySecs('me', d), S0 = chDayStart(l), S1 = chDayEnd(l), gaps = chGaps(l, S0, S1);
  const follow = [`When am I free ${DAYL[chNextDay(d)]}?`, `Who’s free with me ${DAYL[d]}?`];
  if (!l.length) return { t: `No classes ${DAYL[d]} — the whole day is yours.`, card: { k: 'day', d }, follow };
  if (mode === 'free') return { t: gaps.length ? esc('Free ' + chFreeWords(gaps, S0, S1) + '.') : `No free stretch of 30 minutes or more between ${hs(S0)} and ${hs(l[l.length - 1].e)}.`, card: { k: 'day', d }, follow };
  const today = d === CLOCK.day, now = today && l.find(s => s.s <= CLOCK.min && CLOCK.min < s.e), next = today && l.find(s => s.s > CLOCK.min);
  return { t: today ? [now ? `You’re in ${esc(now.code)} until ${hs(now.e)}.` : '', next ? `Next: ${esc(next.code)} at ${hs(next.s)}.` : 'Nothing else today.'].filter(Boolean).join(' ') : `${l.length} class${l.length === 1 ? '' : 'es'} ${DAYL[d]}, ${hs(l[0].s)}–${hs(l[l.length - 1].e)}.`, card: { k: 'day', d }, follow };
}
/* The day, 54px an hour so a 50-minute class is a 44px+ button; it runs from 8a (or the first class's hour) to an
   hour after the last class (6p at least), and the stretch after it is "Free after …", not an invented end. */
function chDay(c) {
  const d = c.d, l = chDaySecs('me', d), S0 = chDayStart(l), S1 = chDayEnd(l), span = S1 - S0, H = Math.round(span / 60 * 54), y = m => (m - S0) / span * H;
  const labs = []; for (let m = S0; m < S1; m += 120) labs.push(`<span style="top:${y(m).toFixed(1)}px">${hs(m)}</span>`);
  const bh = s => Math.max(44, (s.e - s.s) / span * H - 2), bot = {};
  l.forEach(s => { bot[s.e] = Math.max(bot[s.e] || 0, y(s.s) + 1 + bh(s)); });
  const blocks = l.map(s => `<button class="chd-b" style="top:${(y(s.s) + 1).toFixed(1)}px;height:${bh(s).toFixed(1)}px" data-a="openClass" data-x="${esc(s.code)}"><b>${esc(s.code)}</b><span>${hs(s.s)}–${hs(s.e)}</span>${s.prof && ratingOf(s.prof) != null ? chStar(ratingOf(s.prof)) : ''}</button>`).join('');
  /* a stretch starts under the block before it (a short class's block is taller than its time) */
  const free = chGaps(l, S0, S1).map(g => { const open = g[1] >= S1 && l.length, top = Math.max(y(g[0]) + 2, (bot[g[0]] || 0) + 2), h = Math.max(24, y(g[1]) - 2 - top);
    return `<div class="chd-f${h < 40 ? ' one' : ''}" style="top:${top.toFixed(1)}px;height:${h.toFixed(1)}px"><b>${open ? 'Free after ' + hs(g[0]) : g[0] <= S0 && g[1] >= S1 ? 'Free all day' : 'Free ' + hs(g[0]) + '–' + hs(g[1])}</b>${open ? '' : `<span>${chLen(g[1] - g[0])}</span>`}</div>`; }).join('');
  const now = d === CLOCK.day && CLOCK.min > S0 && CLOCK.min < S1 ? `<span class="chd-now" style="top:${y(CLOCK.min).toFixed(1)}px" aria-label="Now"></span>` : '';
  return `<section class="chc" aria-label="Your ${DAYL[d]}"><div class="chc-h"><span class="chc-t">${DAYL[d]}</span>${chChip(l.length + ' class' + (l.length === 1 ? '' : 'es'), 'blue')}<button class="chc-open" data-a="schedTabGo" data-x="mine">Week ›</button></div><div class="chd"><div class="chd-lab" style="height:${H}px">${labs.join('')}</div><div class="chd-col" style="height:${H}px">${free}${blocks}${now}</div></div></section>`;
}
function ansFreeWeek(days) {
  if (!personSecs('me').some(chTimed)) return { t: `You haven’t added ${esc(CFG.TERM_LABEL)} classes with times yet.`, acts: [['Open Schedule', 'tab', 'schedule']] };
  const ds = days && days.length ? days : DAYS;
  return { t: 'Your free time, day by day. Tap a day to see it.', card: { k: 'week', days: ds }, follow: ds.length > 1 ? [`Who’s free with me ${DAYL[DAYS.includes(CLOCK.day) ? CLOCK.day : 'M']}?`] : [] };
}
function chWeek(c) {
  const ds = (c.days || DAYS).filter(d => DAYS.includes(d)), lists = ds.map(d => chDaySecs('me', d));
  const S0 = Math.min(...lists.map(chDayStart)), S1 = Math.max(...lists.map(chDayEnd)), span = S1 - S0, pc = m => ((m - S0) / span * 100).toFixed(1);
  const rows = ds.map((d, i) => { const l = lists[i], g = chGaps(l, S0, S1);
    return `<button class="chw-row" data-a="ask" data-x="${esc('When am I free ' + DAYL[d] + '?')}"><span class="chw-d">${DAYN[d]}</span><span class="chw-m"><span class="chw-bar" aria-hidden="true">${l.map(s => `<i style="left:${pc(s.s)}%;width:${((s.e - s.s) / span * 100).toFixed(1)}%"></i>`).join('')}</span><span class="chw-t">${l.length ? (g.length ? 'Free ' + esc(chFreeWords(g, S0, S1)) : 'Booked ' + hs(S0) + '–' + hs(l[l.length - 1].e)) : 'No classes'}</span></span>${ic('chevR', 16)}</button>`; }).join('');
  return `<section class="chc" aria-label="Your free time"><div class="chc-h"><span class="chc-t">Your week</span><button class="chc-open" data-a="schedTabGo" data-x="mine">Week ›</button></div>${rows}<div class="chw-ax" aria-hidden="true"><span>${hs(S0)}</span><span>${hs(S1)}</span></div></section>`;
}

/* ---- friends free at the same time as you ---- */
const CH_DAY_END = 1080;                             /* "free together" looks at the class day, 8a–6p */
function chTogether(d) {
  const mine = chDaySecs('me', d), S1 = CH_DAY_END, myGaps = chGaps(mine, CH_S0, S1);
  return TC.friends.filter(f => personSecs(f).some(chTimed)).map(f => {
    const theirs = chGaps(chDaySecs(f, d), CH_S0, S1), both = [];
    myGaps.forEach(a => theirs.forEach(b => { const x = Math.max(a[0], b[0]), y = Math.min(a[1], b[1]); if (y - x >= 30) both.push([x, y]); }));
    both.sort((a, b) => (b[1] - b[0]) - (a[1] - a[0]));
    return { f, both, best: both[0] };
  }).filter(x => x.best).sort((a, b) => (b.best[1] - b.best[0]) - (a.best[1] - a.best[0]) || a.best[0] - b.best[0]);
}
function ansTogether(d) {
  if (!TC.friends.length) return { t: 'Add friends and I can find when you’re both free.', acts: [['Add friends', 'sheet', 'addFriend']] };
  if (!personSecs('me').some(chTimed)) return { t: `Add your ${esc(CFG.TERM_LABEL)} classes and I can match your free time with friends’.`, acts: [['Open Schedule', 'tab', 'schedule']] };
  const l = chTogether(d);
  if (!l.length) return { t: TC.friends.some(f => personSecs(f).some(chTimed)) ? `None of your friends is free at the same time as you on ${DAYL[d]} between ${hs(CH_S0)} and ${hs(CH_DAY_END)}.` : 'None of your friends has added classes with times yet.', follow: [`Who’s free with me ${DAYL[chNextDay(d)]}?`] };
  const names = l.slice(0, 2).map(x => esc(PEOPLE[x.f].short));
  return { t: `${l.length > 2 ? names.join(', ') + ` and ${l.length - 2} more` : names.join(' and ')} ${l.length === 1 ? 'is' : 'are'} free when you are on ${DAYL[d]}.`, card: { k: 'together', d }, follow: [`When am I free ${DAYL[d]}?`, `Who’s free with me ${DAYL[chNextDay(d)]}?`] };
}
function chTogetherCard(c) {
  const l = chTogether(c.d).slice(0, 6); if (!l.length) return '';
  return `<section class="chc chrows" aria-label="Free with you ${DAYL[c.d]}">${l.map(x => `<div class="chpp free"><div class="chpp-top"><button class="chpp-main" data-a="openFriend" data-x="${esc(x.f)}">${pav(x.f, 44)}<span class="grow"><b>${esc(PEOPLE[x.f].short)}</b><span>Free together ${hs(x.best[0])}–${hs(x.best[1])} · ${chLen(x.best[1] - x.best[0])}${x.both.length > 1 ? ` · +${x.both.length - 1} more` : ''}</span></span></button><button class="act" data-a="openChatWith" data-x="${esc(x.f)}">Message</button></div></div>`).join('')}</section>`;
}

/* ---- who's free right now ---- */
function ansNow() {
  if (!TC.friends.length) return { t: 'Add friends and I can tell you who’s free.', acts: [['Add friends', 'sheet', 'addFriend']] };
  const fl = TC.friends.filter(f => status(f).free === true);
  return { t: fl.length ? `${fl.length} friend${fl.length === 1 ? ' is' : 's are'} free · ${esc(nowLabel())}` : `None of your friends with class times are free right now · ${esc(nowLabel())}`, card: { k: 'now' }, follow: [`Who’s free with me ${DAYL[DAYS.includes(CLOCK.day) ? CLOCK.day : 'M']}?`] };
}
function chNow() {
  const fl = TC.friends.filter(f => status(f).free === true), busy = TC.friends.filter(f => status(f).free === false);
  if (!fl.length && !busy.length) return '';
  const span = 1200 - CH_S0, pc = m => (Math.max(0, Math.min(span, m - CH_S0)) / span * 100).toFixed(1), day = CLOCK.day;
  const strip = f => `<span class="chpp-bar" aria-hidden="true">${chDaySecs(f, day).map(s => `<i style="left:${pc(s.s)}%;width:${(pc(s.e) - pc(s.s)).toFixed(1)}%"></i>`).join('')}<em style="left:${pc(CLOCK.min)}%"></em></span>`;
  const row = (f, free) => `<div class="chpp${free ? ' free' : ''}"><div class="chpp-top"><button class="chpp-main" data-a="openFriend" data-x="${esc(f)}">${pav(f, free ? 44 : 36)}<span class="grow"><b>${esc(PEOPLE[f].short)}</b><span>${esc(status(f).t)}</span></span></button>${free ? `<button class="act" data-a="openChatWith" data-x="${esc(f)}">Message</button>` : ''}</div>${free ? strip(f) : ''}</div>`;
  return `<section class="chc chrows" aria-label="Who’s free">${fl.slice(0, 6).map(f => row(f, true)).join('')}${busy.length ? `<span class="chk" style="padding:10px 0 2px">Busy</span>${busy.slice(0, 4).map(f => row(f, false)).join('')}` : ''}</section>`;
}

/* ---- professors ---- */
function chProfsFor(code) {
  return courseProfs(code).filter(pk => pk && PROFS[pk]).sort((a, b) => (ratingOf(b) ?? -1) - (ratingOf(a) ?? -1) || (PROFS[b].count || 0) - (PROFS[a].count || 0));
}
function chProfBig(pk, code) {
  const P0 = PROFS[pk]; if (!P0) return '';
  const r = ratingOf(pk), st = reviewStats(pk), fav = TC.favCounts && TC.favCounts[reviewKeyOf(pk)];
  const tiles = [st && st.again != null ? [st.again + '%', 'take again'] : null, st && st.diff != null ? [st.diff, 'difficulty'] : null, fav ? ['♥ ' + fav, 'favorite'] : null].filter(Boolean);
  const secs = code ? secsOf(code).filter(s => s.prof === pk).sort((a, b) => chRank(a) - chRank(b)) : [];
  const secRows = secs.slice(0, 2).map(s => { const mine = personSecs('me').some(x => x.id === s.id), cl = chTimed(s) && !mine ? clashWithMine(s) : [], fr = TC.friends.filter(f => personSecs(f).some(x => x.id === s.id));
    return `<button class="chp-sec" data-x="${esc(s.id)}" data-a="addPlanSheet" aria-label="${esc((mine ? 'Change ' : 'Add ') + s.code + ' ' + secLabel(s.sec) + (mine ? ' in your week' : ' to your week'))}"><span class="grow"><b>${esc(secLabel(s.sec) + ' · ' + secWhen(s))}</b><span>${secSeatText(s)}${mine ? ' · <span style="color:var(--blue-ink);font-weight:900">in your classes</span>' : chTimed(s) && personSecs('me').some(chTimed) ? (cl.length ? ` · <span class="chbad">Clashes with ${esc(cl[0].code)}</span>` : ' · fits your week') : ''}${fr.length ? ` · ${esc(fr.map(f => PEOPLE[f].short).slice(0, 2).join(', '))} ${fr.length === 1 ? 'is' : 'are'} in it` : ''}</span></span>${avStack(fr, 24)}<span class="chp-plus" aria-hidden="true">${ic('plus', 16, 2.8)}</span></button>`; }).join('');
  const teaches = !code ? profCourses(pk) : [];
  const teach = !code ? (teaches.length ? `<div class="chp-teach"><span class="chk">Teaching ${esc(CFG.TERM_LABEL)}</span>${teaches.slice(0, 4).map(cd => `<button data-a="openClass" data-x="${esc(cd)}">${esc(cd)}</button>`).join('')}</div>` : `<div class="chp-teach"><span class="chk">Not teaching in ${esc(CFG.TERM_LABEL)}</span></div>`) : '';
  return `<section class="chc chp" aria-label="${esc(P0.name)}"><button class="chp-top" data-a="openProf" data-x="${esc(pk)}" aria-label="${esc('Open ' + P0.name)}">${profAv(pk, 54, 19)}<span class="grow"><b>${esc(P0.name)}</b><span>${esc([P0.dept, P0.count ? nRatings(P0.count) : 'No ratings yet'].filter(Boolean).join(' · '))}</span></span>${r != null ? `<span class="chp-avg"><b>${r.toFixed(1)}</b><br><span>AVERAGE</span></span>` : ''}</button>${tiles.length ? `<div class="chp-tiles">${tiles.map(t => `<div><b>${esc(String(t[0]))}</b><span>${t[1]}</span></div>`).join('')}</div>` : ''}${secRows ? `<div class="chp-secs">${secRows}</div>` : tiles.length && !teach ? '<div style="height:14px"></div>' : ''}${teach}</section>`;
}
function chProfRow(pk, code) {
  const s = code ? secsOf(code).filter(x => x.prof === pk).sort((a, b) => chRank(a) - chRank(b))[0] : null;
  return `<button class="chr" data-a="openProf" data-x="${esc(pk)}">${profAv(pk, 40, 14)}<span class="grow"><b>${esc(profName(pk))}</b><span>${s ? esc(secLabel(s.sec) + ' · ' + secWhen(s)) + ' · ' + secSeatText(s) : esc(PROFS[pk].count ? nRatings(PROFS[pk].count) : 'No ratings yet')}</span></span>${chStar(ratingOf(pk))}</button>`;
}
function chProfs(c) {
  const list = c.pks ? c.pks.filter(pk => PROFS[pk]) : chProfsFor(c.code); if (!list.length) return '';
  const big = c.pks ? null : list[0], rest = big ? list.slice(1) : list;
  return (big ? chProfBig(big, c.code) : '') + (rest.length ? `${big ? `<span class="chk" style="padding:4px 6px 0">Also teaching ${esc(c.code)}</span>` : ''}<section class="chc chrows">${rest.map(pk => chProfRow(pk, c.code)).join('')}</section>` : '');
}
function ansBest(code) {
  if (!COURSES[code]) return ansClass(code);
  const ps = chProfsFor(code), rated = ps.filter(p => ratingOf(p) != null);
  const follow = [`Does ${code} fit my schedule?`, `Who’s in ${code}?`];
  if (!ps.length) return { t: `No professor is assigned to ${esc(code)} yet.`, card: { k: 'cls', code }, follow };
  const top = ps[0];
  if (!rated.length) return { t: `None of the ${esc(code)} professors have ratings yet.`, card: { k: 'profs', code }, follow };
  return { t: ps.length === 1 ? `Only ${esc(profName(top))} teaches ${esc(code)}.` : `${esc(profName(top))} — top rated of ${ps.length}.`, card: { k: 'profs', code }, follow };
}
function ansProf(pk) {
  if (!pk) return { t: 'I couldn’t find that professor.' };
  const r = ratingOf(pk), cs = profCourses(pk);
  return { t: r != null ? `${esc(profName(pk))} · ★ ${r.toFixed(1)} from ${nRatings(PROFS[pk].count)}.` : `${esc(profName(pk))} has no ratings yet.`, card: { k: 'prof', pk }, follow: cs.length ? [`Best professor for ${cs[0]}?`] : [] };
}

/* ---- classes and sections ---- */
function ansClass(code) {
  if (!COURSES[code]) return { t: TC.seatsLoaded ? `${esc(code)} isn’t offered in ${esc(CFG.TERM_LABEL)}.` : 'Classes are still loading — ask again in a moment.' };
  const fr = friendsIn(code);
  return { t: `${esc(code)} · ${esc(course(code).title)}${fr.length ? ` · ${esc(fr.map(f => PEOPLE[f].short).slice(0, 2).join(' and '))}${fr.length > 2 ? ` +${fr.length - 2}` : ''} ${fr.length === 1 ? 'is' : 'are'} in it` : ''}`, card: { k: 'cls', code }, follow: [`Best professor for ${code}?`, `Does ${code} fit my schedule?`] };
}
function chSecRow(s, inClass) {
  const mine = personSecs('me').some(x => x.id === s.id), cl = chTimed(s) && !mine ? clashWithMine(s) : [];
  const fit = mine ? chChip('In your classes', 'blue') : !chTimed(s) || !personSecs('me').some(chTimed) ? '' : cl.length ? chChip('Clashes with ' + esc(cl[0].code), 'bad') : chChip('✓ Fits your week', 'ok');
  return `<div class="chs"><button class="chs-main" data-a="openClass" data-x="${esc(s.code)}"><span class="chs-h">${inClass ? '' : `<span class="code">${esc(s.code)}</span> `}<b>${esc(secLabel(s.sec))}</b></span>${inClass ? '' : `<span class="chs-t">${esc(course(s.code).title)}</span>`}<span class="chs-w">${esc(secWhen(s))}</span></button><button class="chs-add" data-x="${esc(s.id)}" data-a="addPlanSheet" aria-label="${esc('Add ' + s.code + ' ' + secLabel(s.sec) + ' to your week')}">${ic('plus', 18, 2.8)}</button><div class="chs-f">${chProfChip(s)}${chChip(secSeatText(s))}${fit}</div></div>`;
}
function chClass(c) {
  const code = c.code; if (!COURSES[code]) return '';
  const ss = secsOf(code).slice().sort((a, b) => chRank(a) - chRank(b) || ((ratingOf(b.prof) ?? -1) - (ratingOf(a.prof) ?? -1))), fr = friendsIn(code), cs = courseSeats(code);
  return `<section class="chc" aria-label="${esc(code)}"><button class="chc-cls" data-a="openClass" data-x="${esc(code)}"><span class="code">${esc(code)}</span><b>${esc(course(code).title)}</b><span class="chev">${ic('chevR', 18)}</span></button><div class="chc-facts" style="margin:6px 0 4px">${chChip(ss.length + ' section' + (ss.length === 1 ? '' : 's'))}${cs.anyOpen ? chChip(cs.open ? cs.open + ' open seats' : 'Open sections', 'ok') : cs.allFull ? chChip('Every section is full', 'bad') : ''}${fr.length ? chChip(avStack(fr, 20) + ' ' + fr.length + ' friend' + (fr.length === 1 ? '' : 's')) : ''}</div>${ss.slice(0, 3).map(s => chSecRow(s, true)).join('')}${ss.length > 3 ? `<button class="chc-more" data-a="openClass" data-x="${esc(code)}">All ${ss.length} sections ›</button>` : ''}</section>`;
}
function chSecs(c) {
  const ss = (c.ids || []).map(id => SEC[id]).filter(Boolean); if (!ss.length) return '';
  return `${c.chips && c.chips.length ? `<div class="chc-facts" style="margin:0 2px">${c.chips.map(t => chChip(esc(t), 'blue')).join('')}</div>` : ''}${ss.map(s => `<section class="chc">${chSecRow(s, false)}</section>`).join('')}`;
}
function ansSearch(a) {
  if (!TC.seatsLoaded) return { t: 'Classes are still loading — ask again in a moment.' };
  if (a.ge_area || a.scope) return { t: 'Your GE areas and major requirements are in Schedule › Past classes. The Planner picks what to take next.', acts: [['Open Past classes', 'schedTabGo', 'past'], ['Open Planner', 'schedTabGo', 'planner']] };
  const code = cc(a.course), subj = String(a.subject || '').toUpperCase().trim();
  const days = (a.days || []).map(d => HDAY[d]).filter(Boolean);
  const at = toMin(a.at_time), sa = toMin(a.start_after), eb = toMin(a.end_before);
  let l = SECTIONS.filter(s => {
    if (code && s.code !== code) return false;
    if (!code && subj && s.code.split(' ')[0] !== subj) return false;
    if (a.open_only && s.status !== 'open') return false;
    if (a.instruction_mode === 'async' && !s.async) return false;
    if (a.instruction_mode === 'in_person' && s.async) return false;
    if (a.min_rating && !(ratingOf(s.prof) >= a.min_rating)) return false;
    if ((days.length || at != null || sa != null || eb != null) && (s.async || s.s == null)) return false;
    if (days.length && ![...s.days].every(d => days.includes(d))) return false;
    if (at != null && Math.abs(s.s - at) > 30) return false;
    if (sa != null && s.s < sa) return false;
    if (eb != null && s.e > eb) return false;
    if (a.fits_my_schedule && clashWithMine(s).length) return false;
    return true;
  });
  if (!code && !subj && !a.min_rating && !days.length && at == null && sa == null && eb == null) return { t: 'Which class or subject? Try “open CSC classes after 10am”.' };
  if (!l.length) return { t: 'No sections match all of that. Try loosening one thing — a later end time, or any day.' };
  const byR = (x, y) => ((ratingOf(y.prof) ?? -1) - (ratingOf(x.prof) ?? -1));
  l.sort(a.sort === 'seats' ? (x, y) => (y.seats || 0) - (x.seats || 0) : a.sort === 'rating' ? byR : (x, y) => (y.status === 'open') - (x.status === 'open') || byR(x, y));
  const fitN = l.filter(s => chTimed(s) && !clashWithMine(s).length).length;
  const chips = [code || subj, a.open_only ? 'Open seats' : '', days.length ? daysLabel(days.join('')) + ' only' : '', sa != null ? 'After ' + hs(sa) : '', eb != null ? 'Done by ' + hs(eb) : '', at != null ? 'Around ' + hs(at) : '', a.min_rating ? '★ ' + a.min_rating + '+' : '', a.fits_my_schedule ? 'Fits my week' : '', a.instruction_mode === 'async' ? 'Online' : a.instruction_mode === 'in_person' ? 'In person' : ''].filter(Boolean);
  return { t: `${l.length} match${l.length === 1 ? '' : 'es'}${personSecs('me').some(chTimed) ? ` · ${fitN} fit${fitN === 1 ? 's' : ''} your week` : ''}${l.length > 5 ? ' · the top 5' : ''}`, card: { k: 'secs', ids: l.slice(0, 5).map(s => s.id), chips }, acts: l.length > 5 ? [['Open Explore', 'tab', 'explore']] : [] };
}

/* ---- prerequisites ---- */
function ansPrereq(c) {
  ensurePrereqs(); const r = prereqCheck(c), go = [['Show in Planner', 'prereqGo', c]];
  const follow = [`Does ${c} fit my schedule?`];
  if (r.k === 'met') return { t: `Yes — you’ve got the prerequisites for ${esc(c)}.`, card: { k: 'prereq', code: c }, follow };
  if (r.k === 'metnote') return { t: `You’ve got the classes ${esc(c)} needs. Cal Poly also lists: ${esc(r.text)}.`, card: { k: 'prereq', code: c }, follow };
  if (r.k === 'norecord') return { t: `I can’t tell yet — nothing’s logged in your past classes.`, card: { k: 'prereq', code: c }, acts: go };
  if (r.k === 'unmet') { const n = r.st.missing.length; return { t: `Not yet — ${n === 1 ? 'one class' : n + ' classes'} to go: ${esc(r.st.missing.map(g => pqGroup(g).join(' or ')).join(', '))}.`, card: { k: 'prereq', code: c }, acts: go }; }
  if (r.k === 'inprogress') return { t: `You’re taking the prerequisite for ${esc(c)} now.`, card: { k: 'prereq', code: c }, acts: go };
  if (r.k === 'concurrent') return { t: `${esc(c)} needs ${esc(r.st.concurrent.map(g => pqGroup(g).join(' or ')).join(', '))} in the same term.`, card: { k: 'prereq', code: c }, acts: go };
  if (r.k === 'none') return { t: `The catalog lists no prerequisite for ${esc(c)}.` };
  if (r.k === 'wait') return { t: `Still loading your record. The Planner will show it for ${esc(c)}.`, acts: go, wait: c };
  return { t: r.text ? `${esc(c)} prerequisite: ${esc(r.text)}.<br>I can’t check that one against your record.` : 'I can’t check that one against your record right now.' };
}
function chPrereq(c) {
  const code = c.code, r = prereqCheck(code); if (!r.rec || !r.rec.req || !r.st) return '';
  const unknown = r.k === 'norecord';   /* nothing logged: we can't say what's done, so nothing reads as done or not */
  const done = new Set(TCPL.completed().map(x => TCPL.canon(x) || x)), now = new Set([...myCodes()].map(x => TCPL.canon(x) || x));
  let ok = 0;
  const rows = r.rec.req.map(g0 => {
    const g = pqGroup(g0), dn = g.find(x => done.has(x)), nw = !dn && g.find(x => now.has(x));
    if (dn && !unknown) { ok++; return `<div class="chq"><span class="chq-dot ok" aria-hidden="true">✓</span><span class="grow"><b>${esc(dn)}</b><span>On your record</span></span></div>`; }
    if (nw && !unknown) { ok++; return `<div class="chq"><span class="chq-dot now" aria-hidden="true">◐</span><span class="grow"><b>${esc(nw)}</b><span>Taking it now</span></span></div>`; }
    const conc = r.st.concurrent.some(x => pqGroup(x).join() === g.join()), offered = g.filter(x => COURSES[x]);
    return `<div class="chq"><span class="chq-dot ${unknown ? 'unk' : 'need'}" aria-hidden="true">${unknown ? '?' : ''}</span><span class="grow"><b>${g.map(esc).join(' <span style="color:var(--muted);font-weight:800">or</span> ')}</b><span>${conc ? 'Take it the same term' : offered.length ? (offered.length === g.length ? 'Offered ' + esc(CFG.TERM_LABEL) : esc(offered.join(', ')) + ' offered ' + esc(CFG.TERM_LABEL)) : (g.length > 1 ? 'Neither is' : 'Not') + ' offered ' + esc(CFG.TERM_LABEL)}</span><span class="chq-links">${g.map(x => `<button data-a="${COURSES[x] ? 'openClass' : 'plCourse'}" data-x="${esc(x)}">${esc(x)} ›</button>`).join('')}</span></span></div>`;
  }).join('');
  const n = r.rec.req.length;
  return `<section class="chc" aria-label="${esc('Prerequisites for ' + code)}"><button class="chc-cls" data-a="${COURSES[code] ? 'openClass' : 'plCourse'}" data-x="${esc(code)}"><span class="code">${esc(code)}</span><b>${esc(course(code).title)}</b>${unknown ? chChip('Can’t check') : chChip(ok + ' of ' + n, ok === n ? 'ok' : 'bad')}</button>${unknown ? '<div class="chq-bar" aria-hidden="true"></div>' : `<div class="chq-bar" aria-hidden="true"><i style="width:${Math.round(100 * ok / n)}%"></i></div>`}${rows}<div class="chc-btns" style="grid-template-columns:1fr"><button class="btn" data-a="prereqGo" data-x="${esc(code)}">Show in Planner</button></div></section>`;
}

/* ---- the registration game plan ---- */
function chGameOrder(P) {
  const secs = planSecs(P), rank = s => s.status === 'open' ? (typeof s.seats === 'number' ? s.seats : 999) : s.status === 'unknown' ? 1000 : -1;
  return secs.slice().sort((x, y) => rank(x) - rank(y));
}
function ansGamePlan(slot) {
  slot = AT_PLANS.includes(String(slot || '').toUpperCase()) ? String(slot).toUpperCase() : S.plan;
  const order = chGameOrder(slot);
  if (!order.length) return { t: `Plan ${slot} is empty. Add sections from Explore and I’ll order them.`, acts: [['Explore', 'tab', 'explore']] };
  const f = order[0], why = f.status === 'full' ? 'it’s full' : f.status === 'wait' ? 'it’s waitlisted' : typeof f.seats === 'number' ? `${f.seats} seat${f.seats === 1 ? '' : 's'} left` : '';
  return { t: why ? `Grab ${esc(f.code)} first — ${why}.` : `Plan ${slot}, in the order to register. Seat counts aren’t posted for all of them.`, card: { k: 'game', P: slot }, follow: AT_PLANS.filter(x => x !== slot && TC.plans[x].length).slice(0, 1).map(x => `My game plan for Plan ${x}`) };
}
function chGame(c) {
  const P = c.P, order = chGameOrder(P); if (!order.length) return '';
  const others = id => TC.plans[P].filter(x => x !== id);
  const rows = order.map((s, i) => {
    const pct = s.status === 'open' ? (typeof s.seats === 'number' && s.cap ? Math.max(4, Math.round(100 * (s.cap - s.seats) / s.cap)) : null) : s.status === 'unknown' ? null : 100;
    const tone = s.status === 'unknown' ? 'unk' : s.status !== 'open' || (typeof s.seats === 'number' && s.seats <= 5) ? 'hot' : typeof s.seats === 'number' && s.cap && s.seats / s.cap <= .25 ? 'mid' : 'ok';
    const col = tone === 'hot' ? '#DC2626' : tone === 'mid' ? 'var(--amber)' : 'var(--green)';
    const left = s.status === 'full' ? 'Full' : s.status === 'wait' ? 'Waitlist' + (s.wl ? ' · ' + s.wl : '') : typeof s.seats === 'number' ? s.seats + ' left' : s.status === 'open' ? 'Open' : 'Seats unknown';
    const bk = secsOf(s.code).filter(b => b.id !== s.id && b.status === 'open' && !conflicts(others(s.id), b).length).sort((x, y) => ((ratingOf(y.prof) ?? -1) - (ratingOf(x.prof) ?? -1)))[0];
    return `<button class="chg" data-a="openClass" data-x="${esc(s.code)}"><span class="chg-n ${tone}">${i + 1}</span><span class="grow"><b>${esc(s.code)}</b><span class="w">${esc(secWhen(s))}</span><span class="chg-bar"><span>${pct == null ? '' : `<i style="width:${pct}%;background:${col}"></i>`}</span><span style="color:${tone === 'hot' ? 'var(--red-ink)' : tone === 'mid' ? 'var(--amber-ink)' : tone === 'unk' ? 'var(--ink4)' : 'var(--ok-ink)'}">${left}</span></span><span class="chg-bk" style="display:block">${bk ? 'Backup: ' + esc(secLabel(bk.sec) + ' · ' + secWhen(bk)) : (s.status === 'full' || s.status === 'wait' ? 'No other open section fits — the waitlist is the way in' : 'No other open section fits')}</span></span></button>`;
  }).join('');
  const open = new Date(CFG.REGISTRATION_OPENS + 'T12:00:00');
  return `<section class="chc" aria-label="${esc('Plan ' + P + ' game plan')}"><div class="chc-h plan-${P}"><span class="chplan">Plan ${P}</span><span class="chc-t" style="font-size:13px;color:var(--muted)">${order.length} class${order.length === 1 ? '' : 'es'} · registration opens ${esc(open.toLocaleDateString(undefined, { month: 'short', day: 'numeric' }))}</span><button class="chc-open" data-a="champPlan" data-x="${P}">Open ›</button></div>${rows}</section>`;
}

/* ---- your clashes ---- */
function chClashes() {
  const m = personSecs('me'), ids = new Set();
  m.forEach((s, i) => m.slice(i + 1).forEach(t => { if (chTimed(s) && chTimed(t) && s.code !== t.code && [...s.days].some(d => t.days.includes(d)) && s.s < t.e && t.s < s.e) { ids.add(s.id); ids.add(t.id); } }));
  return ids;
}
function chMine(c) {
  const m = personSecs('me'); if (!m.some(chTimed)) return '';
  return `<section class="chc" aria-label="Your classes"><div class="chc-h dest-mine"><span class="chplan">My Classes</span><span class="chc-t"></span><button class="chc-open" data-a="schedTabGo" data-x="mine">Open ›</button></div><div style="margin:0 -6px">${grid(m, { sel: S.homeDays['ch:' + c.n], act: 'homeDay', key: 'ch:' + c.n, blockAct: 'openClass', clashIds: chClashes(), noNow: true, one: true, fit: 26, H: 250 })}</div></section>`;
}

function ansRate() {
  const u = unrated(); if (!u.length) return { t: TC.rateList.length ? 'You’ve rated every professor on your list. Legend.' : 'Once your classes are on TermChamp, your professors show up to rate.' };
  return { t: `You have ${u.length} professor${u.length > 1 ? 's' : ''} to rate. It takes about 20 seconds and helps other students pick classes.`, acts: [['Rate ' + profName(u[0][0]), 'rateProf', u[0][0], u[0][1]], ['Open Rate', 'tab', 'rate']] };
}
const ansFree = ansNow;
const CH_CARDS = { fit: chFit, day: chDay, week: chWeek, together: chTogetherCard, now: chNow, profs: chProfs, prof: c => chProfBig(c.pk, null), cls: chClass, secs: chSecs, prereq: chPrereq, game: chGame, mine: chMine };
function chCard(c) { try { const f = c && CH_CARDS[c.k]; return f ? f(c) || '' : ''; } catch (e) { return ''; } }

/* Questions answered here without the model: the shape is unmistakable and the answer is a lookup, and these
   are the ones the model kept sending to the wrong tool (2026-10-08). */
const CH_CODE = /\b([a-z&]{2,5})\s*-?\s*(\d{3,4}[a-z]?)\b/i;
function chIntent(q) {
  const t = String(q || '').toLowerCase(), m = t.match(CH_CODE), c0 = m ? cc(m[1] + ' ' + m[2]) : null, code = c0 && COURSES[c0] ? c0 : null;
  const named = t.replace(CH_CODE, ' ').replace(/[^a-z\s'-]/g, ' ').split(/\s+/).filter(w => w.length > 3 && !/^(best|professors?|teachers?|instructors?|which|should|easiest|highest|better|good|class|section|rated|rating|for|the)$/.test(w)).some(w => findProfKey(w));
  if (code && !named && /\b(best|top|highest|good|better|which|who should|easiest)\b[\s\S]*\b(prof|profs|professor|professors|teacher|teachers|instructor)\b|\b(prof|professor|teacher)s?\b[\s\S]*\b(best|top|good)\b/.test(t)) return ansBest(code);
  if (code && /\b(fit|fits|work with|works with|clash|clashes|conflict|go with|room for)\b/.test(t) && /\bplan\s*[abc]\b|\bmy (plan|schedule|week|classes)\b|\bplan\b/.test(t)) {
    const p = t.match(/\bplan\s*([abc])\b/);
    return ansFit(code, p ? p[1].toUpperCase() : /\bmy (schedule|week|classes)\b/.test(t) ? 'mine' : S.plan);
  }
  if (/\bfree\b[\s\S]*\b(with me|same time|as me|together)\b|\bboth free\b|\bfree together\b/.test(t)) return ansTogether(chDayOf(t));
  if (/\b(when am i free|when i'?m free|my free time|am i free|free time)\b/.test(t) && !/\bright now\b/.test(t)) {
    const days = [...new Set(chDaysIn(t))];
    if (days.length === 1 || /\b(today|tomorrow)\b/.test(t)) return ansDayCard(days[0] || chDayOf(t), 'free');
    return ansFreeWeek(days);
  }
  return null;
}
const GOTO = """

# Everything from ansClass to just before GOTO is replaced by the block above (which ends by re-opening GOTO).
between("function ansClass(code) {", "const GOTO = ", JS)
rep("const GOTO = const GOTO = ", "const GOTO = ")

# ---- answerTool: the same tools, answered as cards -------------------------------------------------------------
TOOL = r"""function answerTool(j, q) {
  const a = j.args || {};
  switch (j.tool) {
    case 'open_class': { const c = cc(a.course); return c ? ansClass(c) : null; }
    case 'open_professor': case 'professor_stats': return ansProf(findProfKey(a.name));
    case 'compare_professors': { const x = findProfKey(a.a), y = findProfKey(a.b); if (!x || !y) return { t: 'I couldn’t find both of those professors.' }; const rt = pk => ratingOf(pk) != null ? '★ ' + ratingOf(pk).toFixed(1) : 'no ratings yet'; return { t: `${esc(profName(x))} ${rt(x)} · ${esc(profName(y))} ${rt(y)}`, card: { k: 'profs', pks: [x, y] } }; }
    case 'open_section': { const c = cc(a.course), s = secFind(secsOf(c), a.section); return s ? { t: `${esc(s.code)} ${esc(secLabel(s.sec))}`, card: { k: 'secs', ids: [s.id] } } : c ? ansClass(c) : null; }
    case 'search_sections': {
      if (a.course && /best|who should|which prof|easiest|good prof/i.test(q)) return ansBest(cc(a.course));
      return ansSearch(a);
    }
    case 'my_day': { const d = a.rel === 'tomorrow' ? DAYS[(DAYS.indexOf(CLOCK.day) + 1) % 5] || 'M' : (a.days && HDAY[a.days[0]]) || (DAYS.includes(CLOCK.day) ? CLOCK.day : 'M'); return ansDayCard(d, /\bfree\b/i.test(q) ? 'free' : 'day'); }
    case 'my_free': { const ds = (a.days || []).map(d => HDAY[d]).filter(Boolean); return ds.length === 1 ? ansDayCard(ds[0], 'free') : ansFreeWeek(ds); }
    case 'my_conflicts': { const ids = chClashes(); return ids.size ? { t: `${ids.size} of your classes overlap — they’re outlined in red.`, card: { k: 'mine' } } : { t: 'No time clashes in your classes.' }; }
    case 'my_professors': { const ps = [...new Set(personSecs('me').map(s => s.prof).filter(pk => pk && PROFS[pk]))].sort((x, y) => a.order === 'asc' ? ((ratingOf(x) ?? 9) - (ratingOf(y) ?? 9)) : ((ratingOf(y) ?? -1) - (ratingOf(x) ?? -1))); return ps.length ? { t: `Your ${ps.length} professor${ps.length === 1 ? '' : 's'}, ${a.order === 'asc' ? 'lowest' : 'best'} rated first.`, card: { k: 'profs', pks: ps } } : { t: 'None of your classes have a named professor yet.' }; }
    case 'friends_in': { const c = cc(a.course); if (!c) return null; const fr = friendsIn(c); return { t: fr.length ? `${fr.map(f => esc(PEOPLE[f].name)).join(', ')} ${fr.length > 1 ? 'are' : 'is'} in ${esc(c)}.` : `None of your friends are in ${esc(c)}.`, card: { k: 'cls', code: c } }; }
    case 'friends_took': { const c = cc(a.course), out = []; Object.keys(TC.took || {}).forEach(pk => TC.took[pk].forEach(t => { if (TC.friends.includes(t.uid) && (!c || t.code === c) && (!a.subject || t.code.startsWith(String(a.subject).toUpperCase() + ' '))) out.push(`• ${esc(PEOPLE[t.uid].short)}: ${t.code} with ${esc(profName(pk))}${t.when ? ' (' + esc(t.when) + ')' : ''}`); })); return { t: out.length ? out.slice(0, 10).join('<br>') : 'None of your friends have that in their past classes.' }; }
    case 'friend_profile': { const f = findFriend(a.friend); return f ? { t: `${esc(PEOPLE[f].name)}: ${[...new Set(personSecs(f).map(s => s.code).concat(PEOPLE[f].unplaced || []))].join(', ') || 'no classes added'}.`, acts: [['Open ' + PEOPLE[f].short, 'openFriend', f]] } : { t: 'I couldn’t find a friend by that name.' }; }
    case 'draft_message': { const f = findFriend(a.friend); if (!f) return { t: 'I couldn’t find a friend by that name.' }; const about = cc(a.course) || (a.name ? profName(findProfKey(a.name)) : ''); return { t: `Opening a chat with ${esc(PEOPLE[f].short)} — nothing is sent until you tap send.`, acts: [['Message ' + PEOPLE[f].short, 'draftTo', f, about ? `Have you taken ${about}? How was it?` : '']] }; }
    case 'add_friend': { UI.peopleQ = a.person || ''; return { t: 'Find them here:', acts: [['Add friends', 'sheet', 'addFriend']] }; }
    case 'rate_professor': { const pk = findProfKey(a.name) || (cc(a.course) && (personSecs('me').find(s => s.code === cc(a.course)) || {}).prof); return pk ? { t: `Rate ${esc(profName(pk))}:`, acts: [['Rate ' + profName(pk), 'rateProf', pk, cc(a.course) || '']] } : ansRate(); }
    case 'watch': { const c = cc(a.course); if (a.kind === 'section' && c) { const s = secFind(secsOf(c), a.section); if (s) return { t: `${a.off ? 'Stop' : 'Get'} seat alerts for ${c} ${esc(secLabel(s.sec))}?`, acts: [[a.off ? 'Stop alerts' : 'Watch it', 'watch', s.id]] }; } return c ? { t: `Pick a section of ${c} to watch — tap Watch next to it.`, acts: [['Open ' + c, 'openClass', c]] } : null; }
    case 'add_section': { const c = cc(a.course); if (!c) return null; const s = a.section ? secFind(secsOf(c), a.section) : null; if (!s) return ansFit(c, S.plan); const f = chFitCalc(c, S.plan), cl = f.clashOf(s); return { t: cl.length ? `${esc(c)} ${esc(secLabel(s.sec))} clashes with ${esc(cl.map(x => x.code).join(', '))} in Plan ${S.plan}.` : `${esc(c)} ${esc(secLabel(s.sec))} fits Plan ${S.plan}.`, card: { k: 'fit', code: c, P: S.plan, id: s.id } }; }
    case 'fit_pair': { const x = cc(a.a), y = cc(a.b); if (!x || !y) return null; const ok = secsOf(x).some(s => secsOf(y).some(t => !(s.s != null && t.s != null && [...s.days].some(d => t.days.includes(d)) && s.s < t.e && t.s < s.e))); return { t: secsOf(x).length && secsOf(y).length ? (ok ? `Yes — at least one section of ${x} and one of ${y} don’t overlap.` : `Every section of ${x} overlaps every section of ${y}.`) : `One of those isn’t offered in ${esc(CFG.TERM_LABEL)}.` }; }
    case 'swap_section': { const c = cc(a.course); if (!c) return null; const mine = personSecs('me').find(s => s.code === c); const l = secsOf(c).filter(s => !mine || s.id !== mine.id).filter(s => !clashWithMine(s).length).filter(s => !a.prefer || !mine || s.s == null || mine.s == null || (a.prefer === 'later' ? s.s > mine.s : s.s < mine.s)); return l.length ? { t: `${l.length} other ${esc(c)} section${l.length === 1 ? '' : 's'} fit${l.length === 1 ? 's' : ''} your week.`, card: { k: 'secs', ids: l.slice(0, 5).map(s => s.id) } } : { t: `No other ${esc(c)} section fits your week.`, acts: [['Open ' + c, 'openClass', c]] }; }
    case 'prereqs': { const c = cc(a.course); return c ? ansPrereq(c) : null; }
    case 'game_plan': return ansGamePlan(a.plan);
    case 'when_registration': return { t: `${esc(CFG.REGISTRATION_TERM)} registration starts ${esc(new Date(CFG.REGISTRATION_OPENS + 'T12:00:00').toLocaleDateString(undefined, { weekday: 'long', month: 'long', day: 'numeric' }))}. Your exact appointment is in the Cal Poly Portal.` };
    case 'my_units': case 'my_requirements': return { t: 'Units and requirements are in Schedule › Past classes.', acts: [['Open Past classes', 'schedTabGo', 'past']] };
    case 'build_term': return { t: 'TermChamp’s picks in the Planner are the classes to take next.', acts: [['Open Planner', 'schedTabGo', 'planner']] };
"""
between("function answerTool(j, q) {", "    case 'go_to': {", TOOL)

# who's free now, and the help line
rep("""    case 'help': return { t: 'I can find the best-rated professor for a class, search open sections (“open CSC after 10am, no Fridays”), show your day or when you’re free, say who’s free now, order a plan for registration, and open anything in the app.' };""",
    """    case 'help': return { t: 'Ask me things like these — I answer with what you’d see in the app:', follow: ['Best professor for BUS 3431?', 'When am I free Monday?', `Does BUS 4401 fit my Plan ${S.plan}?`, 'Who’s free right now?'] };""")

LOCAL = r"""function localAnswer(q) {
  const t = q.toLowerCase();
  const m = t.match(/\b([a-z&]{2,5})\s*-?\s*(\d{3,4}[a-z]?)\b/i); const code = m ? cc(m[1] + ' ' + m[2]) : null;
  if (/\bfree\b.*\b(now|right now)\b|who('?s| is) free/.test(t)) return ansNow();
  if (/game ?plan|register.*first|backup/.test(t)) { const p = t.match(/plan\s*([abc])\b/); return ansGamePlan(p ? p[1].toUpperCase() : null); }
  if (code && COURSES[code] && /\bprereq|can i take\b/.test(t)) return ansPrereq(code);
  if (code && COURSES[code]) return ansClass(code);
  if (/today|my day|next class|tomorrow/.test(t)) return ansDayCard(chDayOf(t), 'day');
  if (/\b(rate|review)\b/.test(t)) return ansRate();
  const words = t.replace(/[^a-z\s'-]/g, ' ').split(/\s+/).filter(w => w.length > 3);
  const pk = words.map(w => findProfKey(w)).find(Boolean); if (pk && /prof|teach|how is|rating|dr\b/.test(t)) return ansProf(pk);
  return null;
}
"""
between("function localAnswer(q) {", "async function ask(q) {", LOCAL)
# "who's free right now" from the model's tool for it, if it ever names one; and keep ansFree callers working

# ---- ask(): the unmistakable lookups first, then the model; answers keep their card and follow-ups --------------
rep("""  S.champMsgs.push({ me: 1, t: q }); UI.typing = 'champ'; render(true); champEnd();
  let a = null;
  const j = await TC.ask(q);
  if (j && j.tool) { try { a = answerTool(j, q); } catch (e) { a = null; } }
  if (!a) a = localAnswer(q);""",
"""  S.champMsgs.push({ me: 1, t: q }); UI.typing = 'champ'; render(true); champEnd();
  let a = null, j = null;
  try { a = chIntent(q); } catch (e) { a = null; }
  if (!a) {
    j = await TC.ask(q);
    if (j && j.tool) { try { a = answerTool(j, q); } catch (e) { a = null; } }
  }
  if (!a) a = localAnswer(q);
  if (a && a.wait) { const c = a.wait; ensurePrereqs(); for (let i = 0; i < 40 && prereqCheck(c).k === 'wait'; i++) await new Promise(r => setTimeout(r, 200)); a = ansPrereq(c); delete a.wait; }""")
rep("""  UI.typing = null; S.champMsgs.push({ t: a.t, acts: a.acts || [] }); render(true); champEnd();""",
    """  UI.typing = null; S.champMsgs.push({ t: a.t, acts: a.acts || [], card: a.card || null, follow: a.follow || [] }); render(true); champEnd();""")

# ---- the chat draws the card under Champ's line, and the newest answer's follow-ups ----------------------------
rep("""  const msgs = m.map(x => x.me ? `<div class="msg me">${esc(x.t)}</div>` : `<div class="bot"><img src="${CHAMP}" alt=""><div class="msg">${x.t}${x.acts && x.acts.length ? `<div class="acts">${x.acts.map((a, i) => `<button class="act ${i === 0 ? 'primary' : ''}" data-a="${a[1]}" data-x="${esc(a[2])}" ${a[3] ? `data-y="${esc(a[3])}"` : ''}>${esc(a[0])}</button>`).join('')}</div>` : ''}</div></div>`).join('');""",
"""  const msgs = m.map((x, n) => { if (x.me) return `<div class="msg me">${esc(x.t)}</div>`;
    const card = x.card ? chCard(Object.assign({ n }, x.card)) : '';
    const acts = x.acts && x.acts.length ? `<div class="acts">${x.acts.map((a, i) => `<button class="act ${i === 0 ? 'primary' : ''}" data-a="${a[1]}" data-x="${esc(a[2])}" ${a[3] ? `data-y="${esc(a[3])}"` : ''}>${esc(a[0])}</button>`).join('')}</div>` : '';
    const follow = n === m.length - 1 && x.follow && x.follow.length ? `<div class="chfollow">${x.follow.map(f => `<button data-a="ask" data-x="${esc(f)}">${esc(f)}</button>`).join('')}</div>` : '';
    return `<div class="bot"><img src="${CHAMP}" alt=""><div class="msg">${x.t}${acts}</div></div>${card ? `<div class="chc-wrap">${card}</div>` : ''}${follow}`; }).join('');""")

# ---- actions ------------------------------------------------------------------------------------------------
rep("""  champAdd: id => {""", """  /* a card's Add: the Add to your week screen, opened on the plan (or My Classes) the answer was about */
  champAddTo: (id, P) => { if (!SEC[id]) return; openAddTo(id); const sh = UI.sheet; if (sh && sh.type === 'addTo' && (P === 'mine' || AT_PLANS.includes(P)) && sh.dest !== P) { sh.dest = P; sh.seq++; render(true); } },
  champPlan: P => { if (AT_PLANS.includes(P)) { S.plan = P; save(); } A.schedTabGo('plans'); },
  champAdd: id => {""")

# a new chat starts with no day focused on its cards
rep("  champClear: () => { S.champMsgs = []; render(true); },", "  champClear: () => { S.champMsgs = []; Object.keys(S.homeDays).forEach(k => { if (k.slice(0, 3) === 'ch:') delete S.homeDays[k]; }); render(true); },")
open(p, 'w', encoding='utf-8').write(s)
print('patched', p)
