#!/usr/bin/env python3
"""A requirement card's foot, quieter (Tate, 2026-10-13, on "See all 4 | Mark done": "rework how this looks"; then "change it
to see more and see less"): two text links of one size on one row — "See more ›" (chevron turns up when open: "See less")
in blue, "Mark done" in grey on the right — no filled pill, no mismatched weights. Replayable on 05:30.  python3 builder-foot-2026-10-13.py <repo-dir>"""
import pathlib, sys
ROOT = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else '.')
p = ROOT / 'app/index.html'; s = p.read_text()
def rep(a, b):
    global s
    if s.count(a) != 1: sys.exit(f'builder-foot: expected 1 of {a[:80]!r}, found {s.count(a)}')
    s = s.replace(a, b)
rep(""".plq-foot{display:flex;gap:8px;align-items:center;padding:10px 0;border-top:1px solid var(--line);margin-top:4px}
.plq-more{flex:1;min-height:44px;border-radius:12px;background:var(--tint1);color:var(--blue-t,var(--blue));font-size:14px;font-weight:900}
.plq-mark{flex:none;min-height:44px;padding:0 14px;border-radius:12px;color:var(--muted);font-size:13.5px;font-weight:900}
.plq-foot .plq-mark:only-child{margin-left:auto}""",
""".plq-foot{display:flex;justify-content:space-between;align-items:center;gap:12px;padding:2px 0 0;border-top:1px solid var(--line);margin-top:4px}
.plq-more,.plq-mark{display:inline-flex;align-items:center;gap:3px;min-height:44px;padding:0 2px;font-size:13.5px;font-weight:900;background:none;border-radius:0}
.plq-more{color:var(--blue-t,var(--blue))}
.plq-more svg{width:12px;height:12px;transition:transform .15s}
.plq-more[aria-expanded="true"] svg{transform:rotate(-90deg)}
.plq-mark{color:var(--muted);margin-left:auto}""")
rep("""    const more = n > 3 ? `<button class="plq-more" data-a="plLeftOpen" data-x="${esc(q.key)}">${all ? 'Show top 3' : `See all ${Math.min(n, 12)}`}</button>` : '';""",
    """    const more = n > 3 ? `<button class="plq-more" data-a="plLeftOpen" data-x="${esc(q.key)}" aria-expanded="${all}">${all ? 'See less' : 'See more'}${ic('chevR', 12, 3)}</button>` : '';""")
p.write_text(s)
print('builder-foot: applied')
