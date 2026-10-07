#!/usr/bin/env python3
"""A story opens the friend's day in the schedule look (Tate, 2026-10-05).

"when i click on someones story i want to see the day but in the schedule look … a little bit larger
with more detail" → canvas **Story Day View**, option C, edited with Tate until "okay implement in C.
it looks good":

  * one tall column for today, hours down the left, the red now-line — the schedule look, bigger;
  * each class is a block to scale; inside it a blue box holds the code and the time on top and the
    class name on one line under it (the whole box opens the class);
  * under that a purple pill holds the professor with their rating chip inside it (opens the
    professor), "No ratings yet" inside it when there is none;
  * small faces of who you know in that class at the right; a class you share has the yellow ring
    and "With you";
  * no green for free time: the status line is grey, the ring neutral, no "Free 11:50a–1:30p" rows;
  * no Message / Full week buttons and no ‹ › arrows (the name and photo open their page instead).

Two classes that overlap sit side by side. A short class keeps the box and the professor and drops
the name line; a very short one keeps only the box. The Anytime line stays under the day.

Usage: python3 story-day-big-2026-10-05.py <repo>
"""
import sys, pathlib
root = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else '.')
f = root / 'app' / 'index.html'
s = f.read_text()
if 'class="stday"' in s:
    sys.exit('already patched')

def one(old, new):
    global s
    n = s.count(old)
    assert n == 1, (n, old[:90])
    s = s.replace(old, new)

def between(a, b, new):
    """replace from the start of a through the end of b (each once, b after a)"""
    global s
    assert s.count(a) == 1 and s.count(b) == 1, (s.count(a), s.count(b), a[:60], b[:60])
    i = s.index(a); j = s.index(b, i) + len(b)
    s = s[:i] + new + s[j:]

# ---- the sheet ----
between(
    "  const ord = storyOrder(), i = ord.indexOf(id), prev = ord[i - 1], next = ord[i + 1];\n",
    "aria-label=\"${next ? esc('Next: ' + PEOPLE[next].short) : 'No next story'}\">${ic('chevR', 20, 2.4)}</button></div>`;\n",
    r"""  /* the rating chip sits inside the professor's purple pill (Tate, 2026-10-05) */
  const rateChip = pk => { const r = ratingOf(pk), t = rateTone(r); return t ? `<span class="rc" style="background:${t.bg};color:${t.ink}">${starI(11, t.ink)}${r.toFixed(1)}</span>` : '<span class="rc no">No ratings yet</span>'; };
  const withThem = x => { const w = friendsInSec(x.id).filter(f => f !== id), me = mine.some(y => y.id === x.id); const nm = (me ? ['You'] : []).concat(w.map(f => PEOPLE[f].short));
    return { me, html: nm.length ? `<span class="stfaces${me ? ' me' : ''}" role="img" aria-label="${esc('With them: ' + nm.slice(0, 3).join(', ') + (nm.length > 3 ? ' +' + (nm.length - 3) : ''))}">${avStack((me ? ['me'] : []).concat(w), 24)}</span>` : '' }; };
  /* Today in the schedule look: one column, hours down the left, every class to scale. The scale is set
     so the shortest class today is about 100px tall (64–116px an hour; a 50-minute class is 95px), which leaves room for the box
     and the professor in it. */
  let day = '';
  if (today.length) {
    const S0 = Math.floor(today[0].s / 60) * 60, S1 = Math.max(S0 + 120, Math.ceil(Math.max(...today.map(x => x.e)) / 60) * 60);
    const minD = Math.max(15, Math.min(...today.map(x => x.e - x.s))), PH = Math.round(Math.min(116, Math.max(64, 100 * 60 / minD))), PAD = 8;
    const Y = m => PAD + (m - S0) * PH / 60, H = Math.round(Y(S1) + PAD);
    /* classes that overlap (a clash they haven't sorted out) sit side by side, never on top of each other */
    const lane = [], cols = []; let grp = [], end = -1;
    const flush = () => { const n = Math.max(...grp.map(i => lane[i])) + 1; grp.forEach(i => { cols[i] = n; }); grp = []; end = -1; };
    today.forEach((x, i) => { if (grp.length && x.s >= end) flush(); const used = grp.filter(j => today[j].e > x.s).map(j => lane[j]); let l = 0; while (used.includes(l)) l++; lane[i] = l; grp.push(i); end = Math.max(end, x.e); });
    if (grp.length) flush();
    const blocks = today.map((x, i) => {
      const top = Math.round(Y(x.s) + 1), h = Math.max(36, Math.round((x.e - x.s) * PH / 60 - 2)), n = cols[i], w = 100 / n;
      const t = course(x.code).title, nm = t && t !== x.code ? t : '', wt = withThem(x), isNow = x.s <= now && now < x.e;
      const lvl = (h >= 88 ? '' : h >= 64 ? ' mid' : ' tight') + (n > 1 ? ' half' : '');
      const prof = x.prof && PROFS[x.prof] ? `<button class="stpp" data-a="openProf" data-x="${esc(x.prof)}"><span class="pn">${esc(profName(x.prof))}</span>${rateChip(x.prof)}</button>` : '<span class="stpp none">Instructor not assigned</span>';
      return `<div class="stb${wt.me ? ' shared' : ''}${isNow ? ' now' : ''}${lvl}" style="top:${top}px;height:${h}px;left:calc(${lane[i] * w}% + ${lane[i] ? 2 : 0}px);width:calc(${w}% - ${n > 1 ? 2 : 0}px)">
  <button class="stbox" data-a="openClass" data-x="${esc(x.code)}"><span class="r1"><b>${esc(x.code)}</b><span class="tm">${gridTime(x)}</span></span>${nm || wt.me ? `<span class="r2"><span class="nm">${esc(nm)}</span>${wt.me ? '<span class="wy">With you</span>' : ''}</span>` : ''}</button>
  <div class="stb-f">${prof}${wt.html}</div></div>`;
    }).join('');
    let ax = '', ln = '';
    for (let m = S0; m <= S1; m += 60) { ax += `<span style="top:${Math.round(Y(m))}px">${hs(m)}</span>`; ln += `<i class="stday-ln" style="top:${Math.round(Y(m))}px"></i>`; }
    const nowL = now >= S0 && now <= S1 ? `<span class="g-now" style="top:${Math.round(Y(now))}px"><i>${hs(now)}</i></span>` : '';
    day = `<div class="stday"><div class="stday-ax" style="height:${H}px" aria-hidden="true">${ax}</div><div class="stday-bd" style="height:${H}px">${ln}${blocks}${nowL}</div></div>`;
  }
  const body = !ntimed && !anyC.length ? `<div class="empty"><b>${esc(p.short)} hasn’t added classes</b></div>`
    : today.length ? day
    : !ntimed ? `<div class="empty"><b>No set class times</b>${esc(p.short)}’s classes are all anytime.</div>`
    : `<div class="empty"><b>No classes today</b>${esc(p.short)} is free all ${esc(DAYL[CLOCK.day] || 'day')}.</div>`;
  /* No green for free time, and no Message / Full week / ‹ › (Tate, 2026-10-05): the photo and name open their page. */
  return `<div class="row sb"><button class="sthead" data-a="openFriend" data-x="${esc(id)}"><span class="ringav" style="--rc:var(--line2)">${pav(id, 52, 18)}</span><span style="display:block;min-width:0">
<span style="display:block;font-weight:900;font-size:19px">${esc(p.name)}</span>${st.free !== null || st.t ? `<span class="b" style="display:block;font-size:13.5px;color:var(--muted)">${esc(st.t)}</span>` : ''}</span></button><span class="row" style="gap:8px;flex:none">${pinBtn(id, 'stpin')}<button class="xbtn" data-a="closeSheet" aria-label="Close">${ic('x', 16, 2.4)}</button></span></div>
 <div class="flabel" style="margin:16px 0 8px">${esc(DAYL[CLOCK.day] || 'Today')} · today</div>
 ${body}
 ${anyC.length ? `<div class="stonl">Anytime: ${anyC.map(c => esc(c)).join(', ')}</div>` : ''}`;
""")
# ---- CSS: the list view's rules out, the day's in ----
between(".strow{display:flex;gap:12px;padding:12px 0;border-top:1px solid var(--line)}\n",
        ".stnav .iconbtn[disabled]{opacity:.35}\n",
        """/* a story's day in the schedule look (2026-10-05) */
.sthead{display:flex;align-items:center;gap:12px;min-width:0;text-align:left;border-radius:18px}
.stday{display:flex;gap:8px;background:var(--bg);border-radius:18px;padding:10px 10px 10px 6px;--dbox-ink:#1E3A8A;--pp-bg:#E4D7FF;--pp-ink:#5B21B6;--ax-ink:#5B6678;--none-ink:#4B5567}
:root[data-theme="dark"] .stday{--dbox-ink:#EEF3FF;--pp-bg:#3B2A6E;--pp-ink:#E2D6FF;--ax-ink:var(--muted);--none-ink:#9DA9BB}
.stday-ax{width:30px;flex:none;position:relative;font-size:11px;font-weight:800;color:var(--ax-ink);text-align:right}
.stday-ax span{position:absolute;right:0;line-height:14px;margin-top:-7px;white-space:nowrap}
.stday-bd{flex:1;min-width:0;position:relative}
.stday-ln{position:absolute;left:0;right:0;border-top:1px solid var(--line)}
.stb{position:absolute;box-sizing:border-box;border-radius:12px;background:var(--blue-soft);padding:7px;display:flex;flex-direction:column;gap:6px;overflow:hidden;z-index:1}
:root[data-theme="dark"] .stb{background:var(--blue-soft2)}
.stb.shared{box-shadow:inset 0 0 0 2px var(--yellow)}
.stbox{display:flex;flex-direction:column;gap:1px;width:100%;min-width:0;text-align:left;background:var(--blue-mid);color:var(--dbox-ink);border-radius:10px;padding:5px 10px;flex:none}
.stbox .r1,.stbox .r2{display:flex;justify-content:space-between;align-items:baseline;gap:8px;min-width:0}
.stbox b{font-size:16px;font-weight:900;white-space:nowrap}
.stbox .tm{font-size:12.5px;font-weight:800;white-space:nowrap;flex:none}
.stbox .nm{font-size:13.5px;font-weight:800;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;min-width:0}
.stbox .wy{font-size:12px;font-weight:900;color:var(--amber-ink);white-space:nowrap;flex:none}
.stb-f{display:flex;align-items:center;gap:6px;min-width:0;margin-top:auto}
.stpp{display:inline-flex;align-items:center;gap:6px;min-width:0;max-width:100%;min-height:26px;background:var(--pp-bg);color:var(--pp-ink);border-radius:999px;padding:3px 3px 3px 10px;font-size:12.5px;font-weight:800;text-align:left;position:relative}
/* a 44px tap area around the 26px pill */
button.stpp::after{content:"";position:absolute;left:0;right:0;top:-9px;bottom:-9px}
.stpp .pn{white-space:nowrap;overflow:hidden;text-overflow:ellipsis;min-width:0}
.stpp .rc{flex:none;display:inline-flex;align-items:center;gap:3px;border-radius:999px;padding:1px 7px;font-weight:900;white-space:nowrap}
.stpp .rc.no{background:var(--card);color:var(--muted);font-weight:800}
.stpp.none{background:transparent;color:var(--none-ink);padding:3px 2px}
.stfaces{margin-left:auto;flex:none;display:flex}
.stfaces.me .stack>.av:first-child{box-shadow:0 0 0 2px var(--yellow)}
.stb.mid .r2{display:none}
.stb.tight .stb-f{display:none}
/* side by side: the time goes under the code, and the faces make room for the professor */
.stb.half{padding:5px}
.stb.half .stbox{padding:4px 7px}
.stb.half .r1{flex-wrap:wrap;column-gap:6px;row-gap:0}
.stb.half .stbox b{font-size:14.5px}
.stb.half .stfaces{display:none}
.stonl{padding:10px 0 0;font-size:13px;font-weight:800;color:var(--muted)}
/* the now-line's time reads 4.5:1 on dark (it was #DC2626 on navy, 3.6:1) */
:root[data-theme="dark"] .g-now i{color:var(--red-ink);border-color:#7F1D1D}
""")
f.write_text(s)
print('patched', f)
