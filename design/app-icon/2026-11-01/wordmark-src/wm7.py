"""Final header wordmark (2026-11-01): wm6 option A (icon T + C, Rubik 700 lowercase), then
(1) the h's ascender trimmed to the cap height so every tall letter tops out on one line, and
(2) every letter pair re-spaced to the same optical gap (equal white area in the x-height band)."""
import numpy as np
from shapely import affinity
from shapely.ops import transform, unary_union
import wm6, space
from link import to_d
CAP = 700
def level_h(p):
    top = p.bounds[1]; d = -CAP - top               # +10: pull the ascender down to the cap line
    def f(x, y, z=None):
        y = np.asarray(y, float); w = np.clip((-y - 560) / 40, 0, 1)   # only points above the x-height move
        return x, y + d * w
    return transform(f, p)
def build(target=None, D=90, **kw):
    g = space.glyphs(wm6.build(**kw)); g[5] = level_h(g[5])
    gaps = [space.optical(g[i], g[i + 1], -525, -5, D)[0] for i in range(len(g) - 1)]
    target = target or float(np.mean(gaps[1:])); shift = 0.0; out = [g[0]]
    for i in range(1, len(g)):
        if i > 1: shift += target - gaps[i - 1]          # T-e keeps Rubik's own kern (the bar overhangs the e)
        out.append(affinity.translate(g[i], shift, 0))
    return unary_union(out), gaps, target
def svg(color, H=144, pad=0.06, **kw):
    s = build(**kw)[0]; x0, y0, x1, y1 = s.bounds; p = pad * (y1 - y0)
    vb = (x0 - p, y0 - p, x1 - x0 + 2 * p, y1 - y0 + 2 * p); W = round(H * vb[2] / vb[3])
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{vb[0]:.1f} {vb[1]:.1f} {vb[2]:.1f} {vb[3]:.1f}" width="{W}" height="{H}">'
            f'<path d="{to_d(s)}" fill="{color}" fill-rule="evenodd"/></svg>'), W
if __name__ == '__main__':
    s, gaps, t = build()
    print('before', [round(x) for x in gaps], 'target', round(t))
    print('after', [(a, round(space.optical(p, q, -525, -5, 90)[0]), round(q.bounds[0]-p.bounds[2])) for a, p, q in zip(['Te','er','rm','mC','Ch','ha','am','mp'], space.glyphs(s), space.glyphs(s)[1:])])
    for n, p in zip('TermChamp', space.glyphs(s)): print(n, [round(v) for v in p.bounds])

def svg_final(color, H=144, pad=0.06):
    """same vertical frame as the previous Rubik wordmark (-710..190), so the header height and baseline don't move"""
    s = build()[0]; x0, _, x1, _ = s.bounds; y0, y1 = -710, 190; p = pad * (y1 - y0)
    vb = (x0 - p, y0 - p, x1 - x0 + 2 * p, y1 - y0 + 2 * p); W = round(H * vb[2] / vb[3])
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{vb[0]:.1f} {vb[1]:.1f} {vb[2]:.1f} {vb[3]:.1f}" width="{W}" height="{H}">'
            f'<path d="{to_d(s)}" fill="{color}" fill-rule="evenodd"/></svg>'), W
