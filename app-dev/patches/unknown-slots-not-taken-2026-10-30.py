#!/usr/bin/env python3
"""Tate, 2026-10-30: concentration slots we can't check ("Event Planning and Management elective — Plus 6
units of approved electives") showed a "?" and were left OUT of every count, so a concentration read as
finished when it wasn't. Now a slot we can't check is NOT TAKEN by default: an empty circle, counted in
its row and in "left", and one tap ("I took this") checks it off (tap again to undo; the existing
flowchart_marks rows). Only a concentration that hasn't been chosen yet keeps its old "choose a
concentration" handling."""
import sys, pathlib
p = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else 'app/planner.js'); s = p.read_text()
def one(a, b):
    global s
    n = s.count(a); assert n == 1, (a[:70], n); s = s.replace(a, b)
one("""        if (!slotCheckable(sl)) {
          if (isConc) {
            concUnchosen++;
            if (!concNote) concNote = sl.note || '';
            if (!concLabel) { var tl = String(sl.title || ''); concLabel = /^Concentration course$/i.test(tl) ? 'Concentration' : tl.replace(/\\s*course\\s*$/i, ''); }
          } else cant.push(sl);
          return;
        }""",
"""        if (!slotCheckable(sl)) {
          /* a concentration not chosen yet: no row of its own until it is */
          if (isConc && /^Concentration course$/i.test(String(sl.title || ''))) {
            concUnchosen++;
            if (!concNote) concNote = sl.note || '';
            if (!concLabel) { var tl = String(sl.title || ''); concLabel = /^Concentration course$/i.test(tl) ? 'Concentration' : tl.replace(/\\s*course\\s*$/i, ''); }
            return;
          }
          /* (Tate, 2026-10-30) anything else we can't check is NOT taken until the student says so —
             an empty circle in its row and in "left", that one tap ("I took this") checks off */
          var rowX;
          if (isConc) { var cnX = String(sl.note || '').replace(/\\s*concentration\\s*$/i, ''); if (!rows.conc) rows.conc = { label: (cnX ? cnX + ' concentration' : 'Concentration'), f: 0, t: 0, n: 0 }; else if (rows.conc.label === 'Concentration' && cnX) rows.conc.label = cnX + ' concentration'; rowX = rows.conc; }
          else rowX = sl.type === 'ge' ? rows.ge : sl.type === 'course' ? rows.major : rows.el;
          rowX.n++; cell.state = 'need'; cell.selfMark = true;
          needU.push({ title: sl.title || '', type: sl.type, id: sl.id, ti: ti, area: null, units: sl.units, mark: true });
          return;
        }""")
p.write_text(s); print('unknown-slots-not-taken applied (planner.js)')
