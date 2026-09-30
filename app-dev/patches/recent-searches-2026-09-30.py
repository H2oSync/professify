#!/usr/bin/env python3
"""Recent searches on Explore, each with a small x (Tate, 2026-09-30).

"have recently searched when your searching a class or professor and a small x to delete it"

- A class or professor opened from Explore while a search is typed is remembered (newest first,
  at most 8, classes and professors together). Tapping a recent opens it again and moves it to
  the top.
- Tapping into the empty search box shows "Recent" instead of the browse list, like Instagram.
  Each row has a small x that removes just that one; "Clear all" removes the lot.
- Kept on this phone only (localStorage), per account; a different account never sees another's.
  Nothing is sent anywhere. Rows whose class or professor isn't in this term's data are skipped.

Run from the repo root (idempotent; each anchor must match once).
"""
import sys, pathlib
P = pathlib.Path('app/index.html'); s = P.read_text()
MARK = '/* ---- Recent searches (2026-09-30)'
if MARK in s: print('already applied'); sys.exit(0)
def sub(a, b):
    global s
    n = s.count(a)
    if n != 1: sys.exit(f'anchor matched {n} times: {a[:80]!r}')
    s = s.replace(a, b)

sub("function exploreList() {\n  if (!TC.seatsLoaded)",
r"""/* ---- Recent searches (2026-09-30): on this phone only, per account, newest first, at most 8. ---- */
const RECENT_KEY = 'termchamp_app_recent', RECENT_MAX = 8;
function recentAll() {
  try { const m = JSON.parse(localStorage.getItem(RECENT_KEY) || 'null'); if (m && TC.user && m.u === TC.user.id && Array.isArray(m.items)) return m.items.filter(i => i && (i.k === 'c' || i.k === 'p') && typeof i.x === 'string'); } catch (e) {}
  return [];
}
function recentSave(items) { try { if (TC.user) localStorage.setItem(RECENT_KEY, JSON.stringify({ u: TC.user.id, items: items.slice(0, RECENT_MAX) })); } catch (e) {} }
function recentAdd(k, x) { if (!x) return; recentSave([{ k, x }].concat(recentAll().filter(i => !(i.k === k && i.x === x)))); }
/* Only rows this term's data can draw are shown; the rest stay stored (they come back if the data does). */
const recentShown = () => recentAll().filter(i => i.k === 'c' ? !!COURSES[i.x] : !!PROFS[i.x]);
function recentPanel() {
  const rows = recentShown(); if (!rows.length) return '';
  const row = i => {
    const key = i.k + ':' + i.x;
    const main = i.k === 'c'
      ? `<span class="code">${esc(i.x)}</span><span class="grow b" style="min-width:0;font-size:15px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis">${esc(course(i.x).title)}</span>`
      : `${profAv(i.x, 34, 12)}<span class="grow" style="min-width:0"><span class="b" style="display:block;font-size:15px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis">${esc(PROFS[i.x].name)}</span>${PROFS[i.x].dept ? `<span class="muted b" style="font-size:12.5px">${esc(PROFS[i.x].dept)}</span>` : ''}</span>`;
    return `<div class="rs-row"><button class="rs-open" data-a="recentOpen" data-x="${esc(key)}"><span class="rs-ico">${ic('clock', 18, 2.2)}</span>${main}</button><button class="rs-x" data-a="recentDel" data-x="${esc(key)}" aria-label="Remove ${esc(i.k === 'c' ? i.x : PROFS[i.x].name)} from recent">${ic('x', 14, 2.6)}</button></div>`;
  };
  return `<div class="card rs"><div class="row sb rs-h"><span class="b" style="font-size:16px">Recent</span><button class="link b" data-a="recentClear" style="color:var(--blue);font-size:13.5px;min-height:44px">Clear all</button></div>${rows.map(row).join('')}</div>`;
}
function exploreList() {
  if (!S.q.trim() && UI.exFocus && recentShown().length) return recentPanel();
  if (!TC.seatsLoaded)""")

sub("""  openClass: code => { UI.champ = false; go('classDetail', { code }); },
  openProf: id => { UI.champ = false; go('profDetail', { id }); },""",
"""  openClass: (code, y, el) => { if (el && el.closest && el.closest('#exlist') && S.q.trim()) recentAdd('c', code); UI.champ = false; go('classDetail', { code }); },
  openProf: (id, y, el) => { if (el && el.closest && el.closest('#exlist') && S.q.trim()) recentAdd('p', id); UI.champ = false; go('profDetail', { id }); },
  recentOpen: key => { const k = key.slice(0, 1), x = key.slice(2); recentAdd(k, x); UI.exFocus = false; UI.champ = false; go(k === 'c' ? 'classDetail' : 'profDetail', k === 'c' ? { code: x } : { id: x }); },
  recentDel: key => { const k = key.slice(0, 1), x = key.slice(2); recentSave(recentAll().filter(i => !(i.k === k && i.x === x))); UI.exFocus = true; exRepaint(); const q = document.getElementById('exq'); if (q) q.focus(); },
  recentClear: () => { recentSave([]); UI.exFocus = false; exRepaint(); },""")

sub("let qT;\ndocument.addEventListener('input', ev => {",
"""let qT;
function exRepaint() { const el = document.getElementById('exlist'); if (el) el.innerHTML = exploreList(); }
/* The empty search box shows Recent while it has focus. Losing focus waits a moment, so a tap on a
   recent row (which blurs the box first) still lands on the row. */
let exBlurT;
document.addEventListener('focusin', ev => { if (ev.target && ev.target.id === 'exq') { clearTimeout(exBlurT); if (!UI.exFocus) { UI.exFocus = true; exRepaint(); } } });
document.addEventListener('focusout', ev => { if (ev.target && ev.target.id === 'exq') { clearTimeout(exBlurT); exBlurT = setTimeout(() => { const a = document.activeElement; if (a && a.id === 'exq') return; UI.exFocus = false; exRepaint(); }, 300); } });
document.addEventListener('input', ev => {""")

# Styles, next to the scroll-hide rules.
sub("/* ---------- tab bar + Champ hide on scroll (2026-09-30) ---------- */",
""".rs{padding:4px 14px 6px;margin-bottom:12px}
.rs-h{min-height:44px}
.rs-row{display:flex;align-items:center;gap:4px;border-top:1px solid var(--line)}
.rs-open{flex:1;min-width:0;display:flex;align-items:center;gap:10px;min-height:52px;text-align:left;color:inherit}
.rs-ico{color:var(--muted);flex:none;display:grid;place-items:center}
.rs-x{width:44px;height:44px;flex:none;display:grid;place-items:center;color:var(--muted);border-radius:50%}
/* ---------- tab bar + Champ hide on scroll (2026-09-30) ---------- */""")
# The Recent panel follows real focus: every render re-reads it, so a stale flag can't show the
# panel under an unfocused box (tab away and back, or the clear-search x).
sub("""  const y = sc.scrollTop, champY = (document.getElementById('champscroll') || {}).scrollTop;""",
    """  UI.exFocus = focusId === 'exq';
  const y = sc.scrollTop, champY = (document.getElementById('champscroll') || {}).scrollTop;""")
# Pressing a Recent row doesn't take focus from the box, so a long press can't lose the tap.
sub("let exBlurT;\n", "let exBlurT;\ndocument.addEventListener('mousedown', ev => { if (ev.target.closest && ev.target.closest('.rs')) ev.preventDefault(); });\n")
P.write_text(s); print('applied')
