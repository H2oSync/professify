#!/usr/bin/env python3
"""The "No set time" row becomes the Anytime tray (Tate, 2026-09-30, option A3 of the Anytime mockup:
"I like A3").

Before: a wrapping row under the week — "NO SET TIME" then chips with notes ("Online", "Sat",
"Sec 70") — that sat right under the grid and read as cluttered.
Now: a soft grey tray, set apart from the week, with "ANYTIME" on the left and white chips holding just
the class code, on ONE line. Chips that don't fit are counted in a "+N" chip at the end, which opens
the friend's page (their full class list) — or Schedule, on your own week. No icons, no notes, no dashed
outlines (dashed means waitlisted). Why a class has no time is one tap away: a chip opens the section
preview ("Online · self-paced", "Time not posted", "Saturday …"), exactly as before; a class saved with
no section opens the class.

How many fit is worked out from the card's real width and the app's own glyph-width table (textEm), so
the line never wraps and never clips a code in half.

Applies after no-grid-folds-2026-09-30.py (build 17:30).
Usage: python3 anytime-tray-2026-09-30.py <repo-dir>   (edits <repo-dir>/app/index.html)
"""
import sys, os
p = os.path.join(sys.argv[1], 'app', 'index.html')
s = open(p, encoding='utf-8').read()
if 'any-more' in s: sys.exit('already patched')
R = [
 # 1. CSS: the tray
 (""".anyrow{display:flex;flex-wrap:wrap;align-items:center;gap:6px;padding:12px 16px 0}
.homepg .fcard .anyrow{padding:10px 8px 0}
.any-h{font-size:11px;font-weight:900;letter-spacing:.06em;text-transform:uppercase;color:var(--muted);margin-right:2px}
.any-c{display:inline-flex;align-items:center;gap:5px;min-height:42px;padding:8px 11px;border-radius:8px;background:var(--blue-soft2);color:var(--blue-ink);font-size:13px;font-weight:900;letter-spacing:.02em;white-space:nowrap}
.any-c small{font-size:11px;font-weight:700;opacity:.8;letter-spacing:0}
.any-c.shared{box-shadow:0 0 0 2.5px var(--yellow)}""",
  """/* Anytime tray (Tate, 2026-09-30, option A3): a soft grey tray set apart from the week, "ANYTIME" on the
   left, white chips with just the code, one line, "+N" for the rest. */
.anyrow{display:flex;flex-wrap:nowrap;align-items:center;gap:6px;margin:12px 16px 0;padding:8px;border-radius:14px;background:var(--bg);overflow:hidden}
.homepg .fcard .anyrow{margin:12px 8px 0}
.any-h{flex:none;font-size:10.5px;font-weight:900;letter-spacing:.06em;text-transform:uppercase;color:var(--muted2);padding:0 4px}
.any-c{flex:none;display:inline-flex;align-items:center;min-height:42px;padding:0 12px;border-radius:10px;background:#fff;color:var(--blue-ink);font-size:13px;font-weight:900;letter-spacing:.02em;white-space:nowrap}
.any-c.shared{box-shadow:inset 0 0 0 2.5px var(--yellow)}
.any-more{flex:none;display:grid;place-items:center;min-height:42px;min-width:42px;padding:0 10px;border-radius:10px;background:#fff;color:var(--muted);font-size:13px;font-weight:900}
.anyrow button:focus-visible{outline:2.5px solid var(--blue);outline-offset:-3px}"""),
 # 1b. drop the "drawn" set (only the removed notes used it)
 ("  const onGrid = s => !s.async && s.s != null && s.e != null && [...s.days].some(d => DAYS.includes(d)), drawn = new Set(secs.filter(onGrid).map(s => s.code));",
  "  const onGrid = s => !s.async && s.s != null && s.e != null && [...s.days].some(d => DAYS.includes(d));"),
 # 2. the renderer: codes only, one line, +N
 ("""  /* what the chip can truthfully add: online; a weekend day; the section, when the same class is also on the week */
  const note = s => [s.async ? 'Online' : '', !s.async && s.s != null && s.days ? daysLabel(s.days) : '', drawn.has(s.code) && s.sec ? secLabel(s.sec) : ''].filter(Boolean).join(' · ');
  const ring = c => !isMe && mine.has(c) ? ' shared' : '';
  const anyRow = untimed.length || loose.length ? `<div class="anyrow"><span class="any-h">No set time</span>${untimed.map(s => `<button class="any-c${ring(s.code)}" data-a="secSheet" data-x="${esc(s.code)}" data-y="${esc(s.id)}" title="${esc(s.code + ' · ' + secWhen(s))}"><b>${esc(s.code)}</b>${note(s) ? `<small>${esc(note(s))}</small>` : ''}</button>`).join('')}${loose.map(c => `<button class="any-c${ring(c)}" data-a="openClass" data-x="${esc(c)}"><b>${esc(c)}</b><small>No section</small></button>`).join('')}</div>` : '';""",
  """  const ring = c => !isMe && mine.has(c) ? ' shared' : '';
  /* The Anytime tray (option A3): codes only, on one line. How many fit comes from the card's real width
     and the app's glyph widths; the rest are counted in "+N", which opens the full class list. */
  const anyItems = untimed.map(s => `<button class="any-c${ring(s.code)}" data-a="secSheet" data-x="${esc(s.code)}" data-y="${esc(s.id)}" title="${esc(s.code + ' · ' + secWhen(s))}">${esc(s.code)}</button>`)
    .concat(loose.map(c => `<button class="any-c${ring(c)}" data-a="openClass" data-x="${esc(c)}" title="${esc(c + ' · No section')}">${esc(c)}</button>`));
  const anyCodes = untimed.map(s => s.code).concat(loose);
  const anyFit = (() => {
    ANY_W = (document.getElementById('scroll') || {}).clientWidth || 0;
    const W = (ANY_W || Math.min(innerWidth, 402)) - 2 * 12 - 2 * 8 - 2 * 8;   /* card edge, tray margin, tray padding */
    const room0 = W - (textEm('ANYTIME') * 10.5 + 7 * .63 + 8) - 6;   /* the label, its letter-spacing and padding, one gap */
    const w = c => textEm(c) * 13 + 7 * .26 + 24 + 6;   /* chip: code at 13px, letter-spacing, padding, gap */
    let n = 0, used = 0;
    for (; n < anyCodes.length; n++) {
      const rest = anyCodes.length - n - 1, need = w(anyCodes[n]) + (rest ? 48 : 0);   /* leave room for "+N" if any follow */
      if (used + need > room0) break;
      used += w(anyCodes[n]);
    }
    return n;   /* at a very narrow width that can be 0: just "+N", never a clipped chip */
  })();
  const anyMore = anyCodes.length - anyFit;
  const anyRow = anyCodes.length ? `<div class="anyrow" role="group" aria-label="Classes with no set time"><span class="any-h">Anytime</span>${anyItems.slice(0, anyFit).join('')}${anyMore ? `<button class="any-more" data-a="${isMe ? 'tab' : 'openFriend'}" data-x="${isMe ? 'schedule' : esc(id)}" aria-label="${anyMore} more class${anyMore === 1 ? '' : 'es'} with no set time">+${anyMore}</button>` : ''}</div>` : '';"""),

 # 3. the fit depends on the width: when the screen width changes (rotate, resize), draw Home again
 ("addEventListener('resize', fit); fit();",
  """addEventListener('resize', fit); fit();
/* The Anytime tray counts how many chips fit the card's width (homeWeekCard). When that width changes,
   draw again so the line is never clipped or left short. */
var ANY_W, anyRz;   /* var, not let: Home can draw before this line runs */
addEventListener('resize', () => { clearTimeout(anyRz); anyRz = setTimeout(() => { const w = (document.getElementById('scroll') || {}).clientWidth; if (w && ANY_W && w !== ANY_W && document.querySelector('.anyrow')) render(true); }, 150); });"""),
]
for a, b in R:
    n = s.count(a)
    if n != 1: sys.exit(f'anchor matched {n}x: {a[:80]}')
    s = s.replace(a, b)
open(p, 'w', encoding='utf-8').write(s)
print('patched', p)
