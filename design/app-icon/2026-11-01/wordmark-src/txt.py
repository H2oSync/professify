"""Text → SVG path outlines (HarfBuzz shaping, so real kerning), for wordmarks that render the same everywhere."""
import io, uharfbuzz as hb
from fontTools.ttLib import TTFont
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.pens.boundsPen import BoundsPen

FS = '/tmp/lf/node_modules/@fontsource/'
_cache = {}

def font(name, weight, style='normal'):
    key = (name, weight, style)
    if key not in _cache:
        tt = TTFont(f'{FS}{name}/files/{name}-latin-{weight}-{style}.woff')
        tt.flavor = None
        buf = io.BytesIO(); tt.save(buf); data = buf.getvalue()
        hbf = hb.Font(hb.Face(data))
        _cache[key] = (TTFont(io.BytesIO(data)), hbf)
    return _cache[key]

def text(name, weight, s, size, x=0, y=0, track=0.0, style='normal', features=None):
    """Returns (svg path d, width, (x0,y0,x1,y1) ink bounds). y = baseline. track in em."""
    tt, hbf = font(name, weight, style)
    upm = tt['head'].unitsPerEm; k = size / upm
    buf = hb.Buffer(); buf.add_str(s); buf.guess_segment_properties()
    hb.shape(hbf, buf, features or {'kern': True, 'liga': True})
    gs = tt.getGlyphSet(); order = tt.getGlyphOrder()
    sp = SVGPathPen(gs); bp = BoundsPen(gs)
    pen_x = 0.0
    for info, pos in zip(buf.glyph_infos, buf.glyph_positions):
        g = gs[order[info.codepoint]]
        t = (k, 0, 0, -k, x + (pen_x + pos.x_offset) * k, y - pos.y_offset * k)
        g.draw(TransformPen(sp, t)); g.draw(TransformPen(bp, t))
        pen_x += pos.x_advance + track * upm
    w = (pen_x - track * upm) * k
    return sp.getCommands(), w, bp.bounds
