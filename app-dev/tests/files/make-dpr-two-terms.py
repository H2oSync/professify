#!/usr/bin/env python3
"""A synthetic Degree Progress Report for the website's two terms (website-spring-wall, 2026-10-14). Invented person,
classes and grades. A sophomore's report printed October 25, 2026 — after Spring 2027 registration opened:
  Fall 2026: BUS 2201 and COMS 1101 in progress (no grade)      -> the term you are in now
  Spring 2027: BUS 2212 and BUS 2207 registered (no grade)       -> the term you are choosing in
  2025 Fall / 2026 Spring: graded                                -> finished
Before the wall, "this term" was the newest term on the report (Spring), so Fall's two in-progress classes were filed
as FINISHED. Usage: python3 make-dpr-two-terms.py <out dir>"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from make_dpr_transfer_lib import *

def two_terms(path):
    r = Report("Casey Fixture", "9876505", "October 25, 2026 10:05", "BUS Primary BS UG Major", "Fall Semester 2025")
    C, P = 'ok', 'ip'
    r.head("UNDERGRADUATE DEGREE REQUIREMENTS", size=10); r.verdict('ON', "2025-Current Catalog", code="(RG5)")
    r.head("TOTAL UNITS: DEGREE REQUIREMENT"); r.verdict('ON', "(R995)")
    r.head("TOTAL UNITS: MINIMUM UNIT DEGREE REQUIREMENT", 40); r.verdict('N', "120 units", code="(R995-10)", units="120.00 required, 12.00 used, 108.00 needed")
    r.head("BUSINESS ADMINISTRATION MAJOR B.S. (2025-Current Catalog)", size=10); r.verdict('ON', "76 units required", code="(RG150)")
    r.head("BUSINESS CORE (2025)"); r.verdict('ON', "40 units", code="(R510)")
    r.head("BUS 2212", 40); r.verdict('N', "4 units", code="(R510-20)", courses=courses(1, 0, 1))
    r.history([
        ("2025 Fall", "BUS", "1100", "Student Orientation & Success", "A", "2.00", C), ("2025 Fall", "ENGL", "1134", "Writing and Rhetoric", "B+", "3.00", C),
        ("2026 Spr", "ECON", "2030", "Microeconomics", "B", "3.00", C), ("2026 Spr", "STAT", "2170", "Applied Statistics", "A-", "4.00", C),
        ("2026 Fall", "BUS", "2201", "Financial Accounting", "", "4.00", P), ("2026 Fall", "COMS", "1101", "Public Speaking", "", "3.00", P),
        ("2027 Spr", "BUS", "2212", "Managerial Accounting", "", "4.00", P), ("2027 Spr", "BUS", "2207", "Legal Responsibilities of Bus", "", "4.00", P)])
    r.save(path)

out = sys.argv[1] if len(sys.argv) > 1 else '.'
two_terms(os.path.join(out, 'dpr-two-terms.pdf'))
print('wrote', os.path.join(out, 'dpr-two-terms.pdf'))
