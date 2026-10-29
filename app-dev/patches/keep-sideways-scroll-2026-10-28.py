#!/usr/bin/env python3
"""Tate, 2026-10-29 (screen recording): scroll along the stories or "People you might know", open a
story or add someone, close it — and the row jumps back to the start. Every redraw rebuilt those rows
at scrollLeft 0. Now each sideways row keeps where you left it: across a redraw of the same screen
(a sheet opening or closing, adding a friend, data landing), and when you come back to a screen."""
import sys, pathlib
p = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else 'app/index.html'); s = p.read_text()
def one(a, b):
    global s
    n = s.count(a); assert n == 1, (a[:60], n); s = s.replace(a, b)
one("""function render(keep) {
  const sc = document.getElementById('scroll'); if (!sc) return;""", """/* Sideways rows keep their place (Tate, 2026-10-29). Keyed by the row's first class and its order
   among rows of that class, so a redraw puts each row back where it was. */
const HX = '.stories,.recs-row,.hscroll,.chips,.pk-concrow,.gwmem';
function hxSave(root) {
  const m = {}, n = {};
  if (root) root.querySelectorAll(HX).forEach(el => { const c = el.classList[0], i = n[c] = (n[c] || 0) + 1; if (el.scrollLeft > 0) m[c + ':' + i] = el.scrollLeft; });
  return m;
}
function hxRestore(root, m) {
  if (!root || !m) return; const n = {};
  root.querySelectorAll(HX).forEach(el => { const c = el.classList[0], i = n[c] = (n[c] || 0) + 1, v = m[c + ':' + i]; if (v) el.scrollLeft = v; });
}
function render(keep) {
  const sc = document.getElementById('scroll'); if (!sc) return;""")
one("""  sc.innerHTML = v.body; parkNowPills(sc);""", """  if (UI._rendE) UI._rendE.hx = hxSave(sc);
  sc.innerHTML = v.body; parkNowPills(sc);
  hxRestore(sc, e.hx); UI._rendE = e;""")
one("""function fRepaint() { const el = document.getElementById('fbody'); if (el) el.innerHTML = friendsBody(); }""",
    """function fRepaint() { const el = document.getElementById('fbody'); if (el) { const m = hxSave(el); el.innerHTML = friendsBody(); hxRestore(el, m); } }""")
p.write_text(s); print('keep-sideways-scroll applied')
