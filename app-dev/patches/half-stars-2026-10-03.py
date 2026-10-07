#!/usr/bin/env python3
r"""Rate form: half stars (Tate, 2026-10-03: "make it so you can rate half stars").

The desktop already lets a student tap the left half of a star for a half (index.html, "Tap a
star — tap its left half for a half-star"), and reviews.score already holds 3.5 — the desktop
posts it. The phone only ever sent whole numbers. Now:

  · each star in the rate form is 44px wide (less on phones under 390px, so all five fit), split
    into two 22px x 44px buttons — the left half
    gives k-0.5, the right half gives k. Every half is its own labelled button ("3.5 stars"),
    so VoiceOver, Switch Control and a keyboard reach all ten values with no drag code;
  · a half value paints half a star (the coloured star is clipped over the grey one);
  · the colour is the whole-star colour it rounds up to (3.5 → the 4's lime, 4.5 → green), and
    the line under "Overall" says the number and a word: "3.5 · Good", "4.0 · Great";
  · the thanks screen, your reviews on the Me page and the reviews on a professor's page draw the
    same half stars (they rounded 4.5 up to five amber ★s — now 4½ in the form's colour);
  · a saved draft comes back snapped to a half; after a keyboard/VoiceOver tap focus returns to
    that half and the new word is announced;
  · editing a 3.5 review opens on 3.5 (it used to round to 4 and save the 4 back).

Usage: python3 half-stars-2026-10-03.py <repo-dir>. Every anchor must match exactly once.
"""
import sys, os
p = os.path.join(sys.argv[1], 'app', 'index.html')
s = open(p, encoding='utf-8').read()

def rep(a, b):
    global s
    n = s.count(a)
    if n != 1: sys.exit(f'anchor matched {n}x: {a[:90]}')
    s = s.replace(a, b)

# 1. CSS: the half-star cell and its two hit areas.
rep(".stars button:hover{transform:scale(1.15)}\n",
    ".stars button:hover{transform:scale(1.15)}\n"
    "/* Half stars (2026-10-03). A star is 44px wide; its two halves are 22px x 44px buttons. */\n"
    ".hs{position:relative;display:inline-block;flex:none;line-height:0}\n"
    ".hs>svg,.hs-on>svg{display:block}\n"
    ".hs-on{position:absolute;inset:0}\n"
    ".stars.hstars{gap:0}\n"
    "/* 44px wide on a 390px phone; narrower phones shrink the stars (41px at 375, 30px at 320) so all\n"
    "   five fit beside \"Overall\" and its word. The halves stay 44px tall. */\n"
    ".hstar{position:relative;width:clamp(30px,calc((100vw - 170px) / 5),44px);height:44px;display:grid;place-items:center;flex:none}\n"
    ".hstar .hs{max-width:100%}\n"
    ".rf-sw{white-space:nowrap}\n"
    ".stars .hh{position:absolute;top:0;width:50%;height:44px;padding:0;border:0;background:none;display:block;transition:none}\n"
    ".stars .hh:hover{transform:none}\n"
    ".stars .hh.l{left:0}.stars .hh.r{right:0}\n"
    ".stars .hh:focus-visible{outline:2px solid var(--blue);outline-offset:-2px;border-radius:6px}\n")

# 2. Helpers next to SC / STARLBL.
rep("const STARLBL=['','Awful','Meh','Okay','Great','Amazing'];",
    "const STARLBL=['','Awful','Meh','Okay','Great','Amazing'];\n"
    "/* Half stars (2026-10-03): a word for every half, the whole-star colour a half rounds up to, and\n"
    "   one star drawn k-th of five at value v — full, half (clipped) or empty. */\n"
    "const HALFLBL=['','Terrible','Awful','Bad','Meh','So-so','Okay','Good','Great','Excellent','Amazing'];\n"
    "const halfOf = v => Math.max(0, Math.min(5, Math.round((+v || 0) * 2) / 2));\n"
    "const starCol = v => SC[Math.ceil(halfOf(v))];\n"
    "const starWord = v => { const h = halfOf(v); return h ? `${h.toFixed(1)} · ${HALFLBL[h * 2]}` : ''; };\n"
    "const starAt = (sz, v, k, col, off = '#E6EAF1') => { const f = Math.max(0, Math.min(1, halfOf(v) - (k - 1)));\n"
    "  return `<span class=\"hs\" style=\"width:${sz}px;height:${sz}px\">${starI(sz, off)}${f ? `<span class=\"hs-on\" style=\"clip-path:inset(0 ${Math.round((1 - f) * 100)}% 0 0)\">${starI(sz, col)}</span>` : ''}</span>`; };\n"
    "const starRow = (sz, v, gap = 2) => `<span class=\"row\" style=\"gap:${gap}px\">${[1, 2, 3, 4, 5].map(k => starAt(sz, v, k, starCol(v))).join('')}</span>`;")

# 3. The rate form's Overall row.
rep("<span class=\"flabel\">Overall<div class=\"hint\" style=\"margin-top:2px\">${d.stars ? STARLBL[d.stars] : 'Tap to rate'}</div></span><span class=\"stars\">${[1, 2, 3, 4, 5].map(k => `<button data-a=\"draft\" data-x=\"stars\" data-y=\"${k}\" aria-label=\"${k} stars\">${starI(28, k <= d.stars ? SC[d.stars] : '#E6EAF1')}</button>`).join('')}</span>",
    "<span class=\"flabel\">Overall<div class=\"hint rf-sw\" style=\"margin-top:2px\">${d.stars ? starWord(d.stars) : 'Tap to rate'}</div></span><span class=\"stars hstars\" role=\"group\" aria-label=\"Overall rating\">${[1, 2, 3, 4, 5].map(k => `<span class=\"hstar\">${starAt(30, d.stars, k, starCol(d.stars))}<button class=\"hh l\" data-a=\"draft\" data-x=\"stars\" data-y=\"${k - 0.5}\" aria-label=\"${k - 0.5} stars\" aria-pressed=\"${d.stars === k - 0.5}\"></button><button class=\"hh r\" data-a=\"draft\" data-x=\"stars\" data-y=\"${k}\" aria-label=\"${k} star${k > 1 ? 's' : ''}\" aria-pressed=\"${d.stars === k}\"></button></span>`).join('')}</span>")

# 4. Stars are snapped to halves between 0.5 and 5 when tapped.
rep("draft: (k, v) => { const d = S.draft; const val = (k === 'stars' || k === 'diff') ? +v : v;",
    "draft: (k, v) => { const d = S.draft; const val = k === 'stars' ? Math.max(0.5, halfOf(v)) : k === 'diff' ? +v : v;")

# 5. Thanks screen.
rep("<span class=\"row\" style=\"gap:2px\">${[1, 2, 3, 4, 5].map(i => starI(15, i <= d.stars ? SC[d.stars] : '#E6EAF1')).join('')}</span>",
    "${starRow(15, d.stars)}")

# 6. Editing keeps the half.
rep("stars: Math.round(+v.score || 0),", "stars: halfOf(v.score),")

# 7. Your reviews on Me.
rep("const starsTxt = n => { const s = Math.max(0, Math.min(5, Math.round(+n || 0))); return `<span style=\"color:#F59E0B;letter-spacing:1px\">${'★'.repeat(s)}<span style=\"color:#E2E8F0\">${'★'.repeat(5 - s)}</span></span>`; };",
    "const starsTxt = n => `<span class=\"tc-revstars\" role=\"img\" aria-label=\"${halfOf(n)} of 5 stars\">${starRow(13, n, 1)}</span>`;")

# 8. A professor's page lists reviews with the same half stars (it rounded 3.5 up to four amber ★s).
rep("${reviews.slice(0, 20).map(v => { const s = Math.max(0, Math.min(5, Math.round(v.score || 0))); return `<div class=\"review\">",
    "${reviews.slice(0, 20).map(v => { return `<div class=\"review\">")
rep("<span style=\"color:#F59E0B;letter-spacing:1px\">${'★'.repeat(s)}<span style=\"color:#E2E8F0\">${'★'.repeat(5 - s)}</span></span>${v._mine ?",
    "<span class=\"tc-revstars\" role=\"img\" aria-label=\"${halfOf(v.score)} of 5 stars\">${starRow(13, v.score, 1)}</span>${v._mine ?")

# 9. A saved draft comes back snapped to a half, so what is drawn, pressed and posted agree.
rep("const kept = draftLoad(pid); if (kept) { kept.tags =",
    "const kept = draftLoad(pid); if (kept) { kept.stars = halfOf(kept.stars); kept.tags =")

# 10. After a keyboard or VoiceOver tap the form re-renders; focus goes back to the half just
#     chosen (not to the top of the page), and the word under "Overall" is announced.
rep("draft: (k, v) => { const d = S.draft; const val = k === 'stars' ? Math.max(0.5, halfOf(v)) : k === 'diff' ? +v : v;",
    "draft: (k, v) => { const d = S.draft; const val = k === 'stars' ? Math.max(0.5, halfOf(v)) : k === 'diff' ? +v : v; const hf = k === 'stars' && document.activeElement && document.activeElement.classList.contains('hh');")
rep("if (k === 'diff' && d.diff === null) d.diff = 0; d.err = ''; draftSave(); render(true); },",
    "if (k === 'diff' && d.diff === null) d.diff = 0; d.err = ''; draftSave(); render(true); if (hf) { const b = document.querySelector(`.rf .hh[data-y=\"${val}\"]`); if (b) b.focus(); } },")
rep("<div class=\"hint rf-sw\" style=\"margin-top:2px\">",
    "<div class=\"hint rf-sw\" role=\"status\" aria-live=\"polite\" style=\"margin-top:2px\">")

open(p, 'w', encoding='utf-8').write(s)
print('patched', p)
