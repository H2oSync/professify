/* The catalog facts make-dpr-corpus.py builds its reports from — read straight out of the app (app/planner.js and
   app/index.html), so the synthetic reports follow the same flowcharts, GE lists, crosswalk and class names TermChamp
   itself uses. Prints one JSON object.   node dpr-corpus-export.mjs <repo-dir> */
import fs from 'node:fs'; import path from 'node:path';
const root = process.argv[2] || '.';
const pl = fs.readFileSync(path.join(root, 'app/planner.js'), 'utf8'), ix = fs.readFileSync(path.join(root, 'app/index.html'), 'utf8');
function grab(s, name) {
  const i = s.indexOf(name); if (i < 0) throw new Error('not found: ' + name);
  let j = i + name.length; while (s[j] !== '{' && s[j] !== '[') j++;
  const open = s[j], close = open === '{' ? '}' : ']'; let d = 0, st = j, q = null;
  for (; j < s.length; j++) {
    const c = s[j];
    if (q) { if (c === '\\') { j++; continue; } if (c === q) q = null; continue; }
    if (c === '"' || c === "'" || c === '`') { q = c; continue; }
    if (c === open) d++; else if (c === close) { d--; if (!d) break; }
  }
  return s.slice(st, j + 1);
}
const ev = src => (0, eval)('(' + src + ')');
const flow = JSON.parse(grab(pl, 'window.SCHED_MAJORS='));
const ge = ev(grab(pl, 'const GE_COURSES='));
const equiv = ev(grab(pl, 'const COURSE_EQUIV_SEED ='));
const concCat = ev(grab(pl, 'var CONC_CATALOG='));
const concShape = ev(grab(pl, 'var CONC_SHAPE='));
const majorCat = ev(grab(pl, 'const MAJOR_CATALOG='));
const names = JSON.parse(grab(ix, 'const LIFTED_NAMES ='));
/* concentrations: name → the classes the catalog names for it (CONC_SHAPE's required ones first) */
const conc = {};
const add = (major, name, codes) => { if (!codes.length) return; const m = conc[major] = conc[major] || {}; m[name] = [...new Set((m[name] || []).concat(codes))]; };
Object.entries(concShape).forEach(([major, cs]) => Object.entries(cs).forEach(([n, v]) => add(major, n, (v.req || []).concat(...(v.one || [])))));
Object.entries(concCat).forEach(([major, v]) => (v.list || []).forEach(c => add(major, c.name, (c.classes || []).map(a => a[0]))));
Object.entries(majorCat).forEach(([major, v]) => Object.entries(v.concentrations || {}).forEach(([n, c]) => add(major, n, ((c && c.classes) || []).map(a => Array.isArray(a) ? a[0] : a.code).filter(Boolean))));
const out = { flow, ge: ge.map(g => ({ code: g.code, name: g.name, area: g.areaKey, units: g.units })), equiv, conc, names };
process.stdout.write(JSON.stringify(out));
