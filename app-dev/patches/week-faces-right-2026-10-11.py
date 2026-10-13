#!/usr/bin/env python3
"""Friends' faces on a tapped day's class blocks: always on the right, always round (Tate, 2026-10-11).
Usage: python3 week-faces-right-2026-10-11.py app/index.html   (on the 2026-10-11 03:30 build)"""
import sys
p = sys.argv[1]; s = open(p, encoding='utf-8').read()
def one(old, new):
    global s
    assert s.count(old) == 1, (s.count(old), old[:90]); s = s.replace(old, new)
# 1. A photo clips itself to the circle (Safari does not clip an <img> to its parent's rounded corners once the
#    image is composited, so a photo face showed as a bigger rounded square)
one(".av{border-radius:50%;display:inline-grid;place-items:center;font-weight:900;color:var(--ink2);flex:none;letter-spacing:.01em}\n",
    ".av{border-radius:50%;display:inline-grid;place-items:center;font-weight:900;color:var(--ink2);flex:none;letter-spacing:.01em}\n.av img{border-radius:inherit}\n")
# 2. Tall blocks put the faces where short ones do: the right. Wide enough (a tapped day 150px+): a row at the top
#    right, on the code's line, two rows at most. Narrower (five days with classes leave the tapped day about 110px):
#    a column at the right edge, as many whole faces as the block is tall, and a count that is the true remainder.
one("@media (max-width:340px){.g-b.wide{padding:5px 4px}.g-b.wide.tight{padding:2px 4px;column-gap:3px}}\n",
    """.g-b.wide:not(.tight){display:grid;grid-template-columns:auto minmax(0,1fr);grid-template-rows:auto auto;align-content:start;align-items:start;justify-items:start;column-gap:5px;row-gap:2px}
.g-b.wide:not(.tight) .g-code{grid-column:1;grid-row:1}
.g-b.wide:not(.tight) .g-time{grid-column:1;grid-row:2}
.g-b.wide:not(.tight) .g-faces{grid-column:2;grid-row:1/3;margin:-2px -3px 0 0;padding:2px;justify-self:end;min-width:0;max-width:calc(100% + 3px);display:flex;flex-wrap:wrap;gap:2px;justify-content:flex-end;align-content:flex-start;max-height:36px;overflow:hidden}
.g-more.mv{display:none}
@container (max-width:179px){
  .g-b.wide.hasf .g-code{font-size:clamp(min(11px, (100cqi - 44px) / var(--cwl, 6.4)), min(var(--fh, 11px), (100cqi - 46px) / var(--cwl, 6.4)), 14px)}
  .g-b.wide.hasf .g-time{font-size:clamp(min(10px, (100cqi - 44px) / 6.65), min(var(--fh, 11px) * .86, (100cqi - 46px) / 6.65), 12px)}
  .g-b.wide.hasf .g-faces{flex-direction:column;flex-wrap:nowrap;align-items:flex-end;max-height:none;overflow:visible}
  .g-b.wide.hasf .g-face.hv,.g-b.wide.hasf .g-more.mh{display:none}
  .g-b.wide.hasf .g-more.mv{display:block;margin:0}
}
@media (max-width:340px){.g-b.wide{padding:5px 4px}.g-b.wide.tight{padding:2px 4px;column-gap:3px}}
""")
# 3. gridFaces: a column's count is worked out from the block's height
one("""function gridFaces(s) {""", """function gridFaces(s, room) {""")
one("""  const shown = all.slice(0, 3).map(([k, f]) => `<span class="g-face" data-in="${k}">${pav(f, 15, 6.5)}</span>`).join('');
  return `<span class="g-faces">${shown}${all.length > 3 ? `<span class="g-more">+${all.length - 3}</span>` : ''}</span>`;""",
    """  /* in a row: up to three faces, then "+N"; in a narrow tapped day's column (room = px down the block: 17 a face, 12 for the "+N"):
     every face if they all fit, else one fewer than fit, then "+N" — the count is always the true remainder */
  const n = all.length, kv = room == null || (n <= 3 && 17 * n <= room) ? Math.min(3, n) : Math.max(1, Math.min(3, Math.floor((room - 12) / 17)));
  const shown = all.slice(0, 3).map(([k, f], i) => `<span class="g-face${i >= kv ? ' hv' : ''}" data-in="${k}">${pav(f, 15, 6.5)}</span>`).join('');
  return `<span class="g-faces">${shown}${n > 3 ? `<span class="g-more mh">+${n - 3}</span>` : ''}${n > kv ? `<span class="g-more mv">+${n - kv}</span>` : ''}</span>`;""")
# 4. the block: faces are worked out once its height is known; the text no longer keeps a row under the time for them
one("""      const faces = wide && o.faces ? gridFaces(s) : '';
""", """      const hasF = wide && o.faces && gridFaces(s) !== '';
""")
one("""      const tight = wide && h < (faces ? 56 : 36);   /* no room for three rows */""",
    """      const tight = wide && h < (hasF ? 56 : 36);   /* no room for three rows */
      const faces = hasF ? gridFaces(s, h - 7) : '';""")
one("""(h - 12 - (faces ? 24 : 0)) / 1.95""", """(h - 12) / 1.95""")
one("""const cls = ['g-b', wide ? (tight ? 'wide tight' : 'wide') : '', live""", """const cls = ['g-b', wide ? (tight ? 'wide tight' : 'wide') : '', hasF && !tight ? 'hasf' : '', live""")
# 5. The now-line's time pill used to sit above its line at the right, which is where the faces are. In a tapped day
#    with faces it is placed after layout (parkNowPills): the first spot, right to left and above the line before below
#    it, where it covers no face, "+N", code or time in that day; with no such spot it is dropped (the red line stays).
one("""<span class="g-now" style="top:${Y(nowMin)}px"><i>${hs(nowMin)}</i></span>` : '';""",
    """<span class="g-now" style="top:${Y(nowMin)}px"><i${wide && o.faces ? ' class="pk"' : ''}>${hs(nowMin)}</i></span>` : '';""")
one("function render(keep) {\n", """/* Time pill of the red now-line in a tapped day with friends' faces: sits where it covers no face, "+N", code or
   time (right to left, above the line, then below it); where nothing is free it is dropped — the red line stays. */
function parkNowPills(root) {
  (root || document).querySelectorAll('.g-col.on .g-now i.pk').forEach(i => {
    i.style.right = ''; i.style.top = ''; i.style.visibility = '';
    const col = i.closest('.g-col'), ln = i.parentNode.getBoundingClientRect(), pw = i.getBoundingClientRect().width;
    const boxes = [...col.querySelectorAll('.g-b.wide .g-face,.g-b.wide .g-more,.g-b.wide .g-code,.g-b.wide .g-time')].filter(e => e.getClientRects().length).map(e => ({ e, r: e.getBoundingClientRect() }))
      .filter(({ e, r }) => { const c = e.closest('.g-faces'); if (!c || e === c) return true; const f = c.getBoundingClientRect(); return r.top >= f.top - 1 && r.bottom <= f.bottom + 1; }).map(x => x.r);
    const free = (r, t) => { i.style.right = r + 'px'; i.style.top = t + 'px'; const p = i.getBoundingClientRect(); return !boxes.some(b => p.left < b.right + 1 && b.left - 1 < p.right && p.top < b.bottom - .5 && b.top + .5 < p.bottom); };
    let at = null;
    for (const t of [-16, 3]) { for (let r = 2; r <= ln.width - pw; r += 2) if (free(r, t)) { at = [r, t]; break; } if (at) break; }
    if (!at) { i.style.visibility = 'hidden'; return; }
    i.style.right = at[0] + 'px'; i.style.top = at[1] + 'px';
  });
}
window.addEventListener('resize', () => requestAnimationFrame(() => parkNowPills()));
function render(keep) {
""")
one("  sc.innerHTML = v.body;\n", "  sc.innerHTML = v.body; parkNowPills(sc);\n")
open(p, 'w', encoding='utf-8').write(s)
