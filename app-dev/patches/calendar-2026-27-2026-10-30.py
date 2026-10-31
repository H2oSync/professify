#!/usr/bin/env python3
"""Cal Poly 2026-27 no-class days and Spring's end of term, read 2026-10-30 from
registrar.calpoly.edu/academic-calendar ("Academic Calendar 2026-2027, REVISED - JULY 8, 2026"):
  November 23-29  Academic holiday - Fall Break            -> 'Thanksgiving break' (Mon-Fri; weekends have no classes)
  December 12     Common final exams (optional)  + December 14-18 Final examination period  -> 'Finals week'
  December 19, 21-22  Faculty workday, no classes           -> 'Winter break' (end of term is Dec 22)
  February 15     Academic Holiday - Washington's Birthday observed -> "Presidents' Day"
  March 31        Academic Holiday - Farmworkers Day        -> 'César Chávez Day'
  May 22-25       Commencement / Faculty workday; May 25 End of term -> 'Summer break'
  May 25          End of term (Spring 2027)                  -> TERM_END_DATES '2274'"""
import sys, pathlib
p = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else 'app/index.html'); s = p.read_text()
def one(a, b):
    global s
    n = s.count(a); assert n == 1, (a[:70], n); s = s.replace(a, b)
one("""     TODO: swap in the registrar's 'End of term' row for Spring 2027 once it is read (Fall's, Dec 22, comes after its finals). */
  TERM_END_DATES: { '2268': '2026-12-22', '2274': '2027-05-21' },""",
    """     2274: 'May 25 Tuesday End of term' (registrar.calpoly.edu/academic-calendar, read 2026-10-30). */
  TERM_END_DATES: { '2268': '2026-12-22', '2274': '2027-05-25' },""")
one("""     TODO — not in the repo, add from registrar.calpoly.edu/academic-calendar, never guess: Fall 2026 Thanksgiving
     break; Fall 2026 final exams week (before Dec 22); Spring 2027 Cesar Chavez Day; any other campus holiday. */
  NO_CLASS_DAYS: [
    { from: '2026-11-11', to: '2026-11-11', t: 'Veterans Day' },
    { from: '2027-03-15', to: '2027-03-21', t: 'Spring break' },
    { from: '2027-05-15', to: '2027-05-21', t: 'Finals week' }
  ],""", """     The rest (2026-10-30) from registrar.calpoly.edu/academic-calendar, 'REVISED - JULY 8, 2026': 'November 23-29
     Academic holiday - Fall Break'; 'December 12 Common final exams', 'December 14-18 Final examination period';
     'December 19 / 21-22 Faculty workday, no classes'; 'February 15 Academic Holiday – Washington's Birthday observed';
     'March 31 Academic Holiday - Farmworkers Day'; 'May 15, 17-21 Final examination period'; 'May 24-25 Faculty
     workday', 'May 25 End of term'. Labor Day (Sep 7) has passed. */
  NO_CLASS_DAYS: [
    { from: '2026-11-11', to: '2026-11-11', t: 'Veterans Day' },
    { from: '2026-11-23', to: '2026-11-29', t: 'Thanksgiving break' },
    { from: '2026-12-12', to: '2026-12-18', t: 'Finals week' },
    { from: '2026-12-19', to: '2026-12-22', t: 'Winter break' },
    { from: '2027-02-15', to: '2027-02-15', t: 'Presidents’ Day' },
    { from: '2027-03-15', to: '2027-03-21', t: 'Spring break' },
    { from: '2027-03-31', to: '2027-03-31', t: 'César Chávez Day' },
    { from: '2027-05-15', to: '2027-05-21', t: 'Finals week' },
    { from: '2027-05-22', to: '2027-05-25', t: 'Summer break' }
  ],""")
p.write_text(s); print(p, 'calendar 2026-27 applied')
