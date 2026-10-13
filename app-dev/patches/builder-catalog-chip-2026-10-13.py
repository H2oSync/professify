#!/usr/bin/env python3
"""Tate (2026-10-13), on the Builder top card's "Fall Quarter 2023 catalog  report · Oct 8, 2026": "take this out ...
only keep 'Quarter catalog'". The chip now just says Quarter catalog (amber) or Semester catalog (blue), the same words
as the report screen's chip; the report date goes. Replayable on 06:30.
  python3 builder-catalog-chip-2026-10-13.py <repo-dir>"""
import pathlib, sys
ROOT = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else '.')
p = ROOT / 'app/index.html'; s = p.read_text()
a = """${X && TC.audit.catalog ? `<span class="pc-catc ${/quarter/i.test(TC.audit.catalog) ? 'q' : 's'}">${esc(TC.audit.catalog)} catalog</span><span>report${TC.audit.printed_on ? ' · ' + esc(pcDate(TC.audit.printed_on)) : ''}</span>` : ''}"""
b = """${X && TC.audit.catalog ? (/quarter/i.test(TC.audit.catalog) ? '<span class="pc-catc q">Quarter catalog</span>' : '<span class="pc-catc s">Semester catalog</span>') : ''}"""
if s.count(a) != 1: sys.exit(f'builder-catalog-chip: expected 1, found {s.count(a)}')
p.write_text(s.replace(a, b)); print('builder-catalog-chip: applied')
