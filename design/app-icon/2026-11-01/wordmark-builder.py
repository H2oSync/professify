"""Header wordmark (2026-11-01, final pick): "TermChamp" set entirely in Rubik 700, tracking +0.02 em (Tate's sample:
"see how the spacing is super consistent"), brand blue #0B65FD (dark mode #3B82FF), no cap."""
from txt import text
def svg(color, H=144, track=0.02, pad=0.06):
    d, w, b = text('rubik', 700, 'TermChamp', 1000, 0, 0, track)
    p = pad * (b[3] - b[1]); vb = (b[0] - p, b[1] - p, b[2] - b[0] + 2 * p, b[3] - b[1] + 2 * p)
    W = round(H * vb[2] / vb[3])
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{vb[0]:.1f} {vb[1]:.1f} {vb[2]:.1f} {vb[3]:.1f}" width="{W}" height="{H}">'
            f'<path d="{d}" fill="{color}"/></svg>'), W
