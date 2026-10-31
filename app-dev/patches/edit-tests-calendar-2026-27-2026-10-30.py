#!/usr/bin/env python3
"""Tests for calendar-2026-27: Spring 2027 now ends May 25 (the registrar's 'End of term'), not May 21."""
import sys, pathlib
p = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else 'app-dev/tests/2026-10-30/check-hist-term-end.mjs'); s = p.read_text()
def one(a, b):
    global s
    n = s.count(a); assert n == 1, (a[:70], n); s = s.replace(a, b)
one("Spring 2027's own (May 21)", "Spring 2027's own (May 25)")
one("""  ['2027-05-24T12:00:00-07:00', false, false, 'May 24 (Spring over)'],""",
    """  ['2027-05-25T12:00:00-07:00', false, true, 'May 25 (Spring’s end of term)'],
  ['2027-05-26T12:00:00-07:00', false, false, 'May 26 (Spring over)'],""")
p.write_text(s); print(p, 'tests: Spring ends May 25')
q = pathlib.Path('app-dev/tests/2026-10-30/check-no-class-days.mjs'); s = q.read_text()
one("""  ['2026-12-23', '-08:00', 'Winter break', 'the day after Fall’s last day (Dec 22)'],""",
    """  ['2026-11-24', '-08:00', 'Thanksgiving break', 'Thanksgiving week (Fall Break, Nov 23-29)'],
  ['2026-12-10', '-08:00', null, 'Fall’s second-to-last day of classes'],
  ['2026-12-15', '-08:00', 'Finals week', 'Fall finals (Dec 12, 14-18)'],
  ['2026-12-21', '-08:00', 'Winter break', 'faculty workday after finals (Dec 21)'],
  ['2026-12-23', '-08:00', 'Winter break', 'the day after Fall’s last day (Dec 22)'],""")
one("""  ['2027-03-16', '-07:00', 'Spring break', 'Spring break'],""",
    """  ['2027-02-15', '-08:00', 'Presidents’ Day', 'Presidents’ Day'],
  ['2027-03-16', '-07:00', 'Spring break', 'Spring break'],
  ['2027-03-31', '-07:00', 'César Chávez Day', 'César Chávez Day (Farmworkers Day)'],""")
q.write_text(s); print(q, 'tests: 2026-27 no-class days')
