#!/usr/bin/env python3
"""A SYNTHETIC Degree Progress Report — Jordan Fixture, EMPLID 9876543, invented verdicts and grades — laid out the
way Cal Poly's real report prints (PeopleSoft advisement, read on a real report 2026-10-08): page furniture with the
name and EMPLID on every page, "For <name>", the program lines, requirement groups (RG-…), requirements (R-…) and
lines (R70-10) each with a "Satisfied:" / "Not Satisfied:" verdict whose words can wrap, "· Units:" / "· Courses:"
counts, "Courses Used" tables WITH GRADES, a "1 of 2 Options" requirement, a repeat-code note, a "directed to this
line" note, and a bare 7-digit number in brackets — then the Course History table the 2026-09-01 reader reads.
Every one of those is something the app must read, or must never read. No real student's data is in here.
Usage: python3 app-dev/tests/files/make-dpr-fixture.py app-dev/tests/files/dpr-fixture.pdf"""
import sys
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

def furniture(n, of):
    return [f"Page {n} of {of}", "Name: Jordan Fixture", "EMPLID: 9876543", "Date Printed: September 28, 2026 10:00"]

USED = ["Courses Used", "Term Subject Catalog Nbr Course Title Grade Units Requirement", "Designation", "Status"]
PAGE1 = furniture(1, 3) + [
 "Degree Progress Report",
 "For Jordan Fixture",
 "Current Academic Objective Requirement (Catalog) Term",
 "BUS Primary BS UG Major Fall Semester 2024",
 "Financial Management Concentration Fall Semester 2024",
 "Degree Audit Icons Course Icons",
 "Requirement Satisfied Cal Poly Graded Course",
 "Requirement Not Satisfied Course In Progress",
 "In Progress Planned",
 "DEGREE PROGRESS REPORT",
 "GENERAL UNDERGRADUATE DEGREE REQUIREMENTS",
 "Overall Requirement Not Satisfied: ***GENERAL UNDERGRADUATE DEGREE REQUIREMENTS 2026-2028 Catalog (RG-0005)***",
 "TOTAL UNITS FOR THE DEGREE",
 "Overall Requirement Not Satisfied: TOTAL UNITS FOR THE DEGREE (R-0995)",
 "TOTAL UNITS FOR THE DEGREE (120)",
 "Not Satisfied: TOTAL UNITS FOR THE DEGREE ('Taken' units cap at minimum required. Only 70 units from community college can",
 "count toward totals.) - 120 Required",
 "· Units: 120.00 required, 71.00 used, 49.00 needed",
 "GRADUATION WRITING REQUIREMENT",
 "Overall Requirement Not Satisfied: GRADUATION WRITING REQUIREMENT (R-0011)",
 "GRADUATION WRITING REQUIREMENT",
 "Not Satisfied: GRADUATION WRITING REQUIREMENT: - Satisfactory Completion Required",
 "If enrolled in a GWR eligible course, allow a week after grades are finalized before the GWR shows as satisfied in this",
 "section. (R11-10)",
 "GENERAL EDUCATION REQUIREMENTS",
 "Not Satisfied: ***GENERAL EDUCATION REQUIREMENTS 2026-2028 Catalog - 48 Units Required. Refer to Major/Support section for",
 "courses that satisfy/double count for GE. (RG-0006)***",
 "GE AREA 1",
 "Satisfied: GE AREA 1: ENGLISH COMMUNICATION AND CRITICAL THINKING - 3 Units Required (R-0070)",
 "1A",
 "Satisfied: 1A: WRITTEN COMMUNICATION COURSE (Note: A minimum grade of C- is required) - 3 Units Required (R70-10)",
 "· Units: 3.00 required, 3.00 used",
] + USED + [
 "2024 Fall ENGL 1134 Writing and Rhetoric B+ 3.00 1A",
 "GE AREA 4",
 "Not Satisfied: GE AREA 4: SOCIAL AND BEHAVIORAL SCIENCES - 3 Units Required (R-0078)",
 "4B",
 "Not Satisfied: 4B: LOWER-DIVISION SOCIAL SCIENCES COURSE - 3 Units Required (R78-",
 "20)",
 "· Units: 3.00 required, 0.00 used, 3.00 needed",
 "GE AREA 5",
 "Not Satisfied: GE AREA 5: SCIENTIFIC INQUIRY - 1 Unit Required (R-0073)",
 "5C",
 "Not Satisfied: 5C: LABORATORY ACTIVITY - 1 Unit Required (R73-30)",
 "· Units: 1.00 required, 0.00 used, 1.00 needed",
]
PAGE2 = furniture(2, 3) + [
 "BUSINESS PRIMARY MAJOR",
 "Overall Requirement Not Satisfied: ***BUSINESS PRIMARY MAJOR B.S. 2026-2028 Catalog - 60 Minimum Units Required (RG-0010)***",
 "BUSINESS MAJOR SPECIFIED COURSES",
 "Overall Requirement Not Satisfied: BUSINESS MAJOR SPECIFIED COURSES - 9 Units Required (R-0035)",
 "BUS 214 (2214)",
 "Satisfied: BUS 214 (2214) - 3 Units Required (R35-30)",
 "· Units: 3.00 required, 3.00 used",
] + USED + [
 "2024 Fall BUS 214 Financial Accounting A- 3.00",
 " Repeat Code: RFLG - Flag - Informational only",
 "BUS 3346",
 "Not Satisfied: BUS 3346 - 3 Units Required (R35-60)",
 "· Units: 3.00 required, 0.00 used, 3.00 needed",
 "BUS 3438",
 "Satisfied: BUS 3438 - 3 Units Required (R35-70)",
 "· Units: 3.00 required, 3.00 used",
] + USED + [
 "2026 Fall BUS 3438 Financial Markets 3.00",
 "BUSINESS MAJOR FINANCE COURSE",
 "Not Satisfied: BUSINESS MAJOR FINANCE COURSE - 3 Units Required in 1 of 2 Options (R-0036)",
 "BUS 3387 (OPT 1)",
 "Not Satisfied: BUS 3387 - 3 Units Required (Option 1 of 2) (R36-10)",
 "· Units: 3.00 required, 0.00 used, 3.00 needed",
 "BUS 4401 (OPT 2)",
 "Not Satisfied: BUS 4401 - 3 Units Required (Option 2 of 2) (R36-20)",
 "· Units: 3.00 required, 0.00 used, 3.00 needed",
 "BUSINESS CONCENTRATION: FINANCIAL MANAGEMENT",
 "Not Satisfied: ***BUSINESS CONCENTRATION: FINANCIAL MANAGEMENT 2026-2028 Catalog - 9 Minimum Units Required (RG-",
 "0020)***",
 "· Units: 9.00 required, 0.00 used, 9.00 needed",
 "FINANCIAL MANAGEMENT CONCENTRATION CORE COURSES",
 "Overall Requirement Not Satisfied: FINANCIAL MANAGEMENT CONCENTRATION CORE COURSES - 3 Units Required (R-0099)",
 "BUS 4431",
 "Not Satisfied: BUS 4431 - 3 Units Required (R99-10)",
 "· Units: 3.00 required, 0.00 used, 3.00 needed",
 "APPROVED ELECTIVES",
 "Not Satisfied: APPROVED ELECTIVES: Select From the Following: BUS 4436, 4437, or ECON 2303 - 6 Units Required (R2178-10)",
 "· Units: 6.00 required, 3.00 used, 3.00 needed",
] + USED + [
 "2026 Spr BUS 4488 Fixture Digital Marketing C+ 3.00",
 "   BUS 4488 has been directed to this line.",
 "   (1234567)",
]
PAGE3 = furniture(3, 3) + [
 "Course History",
 "Term Subject Catalog Title Grade Units",
 "2024 Fall BUS 214 (2214) Financial Accounting A- 4.00",
 "2025 Spr PHIL 3331 Business Ethics B+ 3.00",
 "2025 Sum AP 300 Advanced Placement 333 4.00",
 "2026 Spr ECON 2001 Survey of Economics C+ 3.00",
 "2026 Fall BUS 3438 Financial Markets 3.00",
 "2026 Fall BUS 4488 Fixture Digital Marketing 3.00",
 "2027 Spr BUS 4401 Strategic Management 3.00",
]

def page(c, lines):
    y = 760
    for ln in lines:
        c.setFont('Helvetica', 8); c.drawString(30, y, ln); y -= 11
    c.showPage()

c = canvas.Canvas(sys.argv[1], pagesize=letter)
for p in (PAGE1, PAGE2, PAGE3): page(c, p)
c.save()
print('wrote', sys.argv[1])
