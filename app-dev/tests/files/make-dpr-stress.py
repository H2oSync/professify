#!/usr/bin/env python3
"""SYNTHETIC Degree Progress Reports that try to BREAK the flow (Tate, 2026-10-11: "run a good amount of fake dprs …
to try and find breaks in the flow of the system from past classes, planner to plans"). Invented people, EMPLIDs,
classes and grades. Two layouts, both read against real reports (nothing of them is in here): the older one
(2022–26 quarter catalogs: "Satisfied: A1: ORAL COMMUNICATION COURSE … - 4 Units Required (R70-10)" on one line,
quarter course numbers with their semester pair "BUS 214 (2214)") and the 2026 one (make-dpr-transfer.py's).

  dpr-stress-quarter.pdf    a senior on the Fall Quarter 2023 catalog, Financial Management: every GE area lettered
                            (A1 … F, B UD / C UD / D UD, a lower-division C elective, two "GE Elective: Areas B, C, and
                            D" lines, Area E satisfied), quarter numbers everywhere (BUS 214 (2214)), a transfer class
                            and a study-abroad placeholder, a class on the Course History the report LISTS for an open
                            line but didn't count (BUS 3306 listed under "Career Readiness III", not counted — a conflict
                            to flag; BUS 4442 listed under the Approved Elective and being taken — not a conflict, in
                            progress), semester classes in progress printed in quarter-equivalent units (6.00, 4.50), a repeated class (two attempts of BUS 207), a "1 of 2 Options" requirement, a requirement's verdict
                            wrapping across a page break (its code on the next page, after the furniture), the
                            closing "COURSE CREDITS NOT USED" table (BUS 100: units only), two classes in progress
  dpr-stress-mixed.pdf      a junior on the Fall Quarter 2024 catalog in Fall 2026: quarter classes through Spring 2026,
                            semester classes in progress now, printed in QUARTER-EQUIVALENT units (a 3-unit semester
                            class prints 4.50 — read on a real quarter-catalog report, 2026-10-11); Area E still OPEN (needs an extra 4B), the C elective
                            open, "C UD" open, D UD in progress by a class being taken; a line the reader can't place
                            (a verdict with no words)
  dpr-stress-mixed-v2.pdf   the same junior's report printed in January 2027: Fall 2026 grades posted (D UD and C UD now
                            Satisfied, BUS 3387 a late add now graded — a class the student had put in a plan — E still
                            open), Spring 2027 registered, one NEW line the first didn't print — for the re-upload diff
  dpr-stress-nomajor.pdf    a semester-catalog student in a major the app has no flowchart for (Dance, "DANC"): the
                            report must still be the whole Past classes screen
  dpr-stress-dupes.pdf      a sophomore who moved to the semester catalog: Spring 2026 quarter classes printed bare
                            ("MATH 221", no pair — as a real semester-catalog report prints them) in semester-equivalent
                            units (2.67), the same class printed twice in one term (a registrar duplicate), a class used
                            by two requirement lines (counted once on the record), "Choose one" with Option 2 in progress, the closing "FREE ELECTIVES" block (no verdict; PSY 200 used for nothing)

Usage: python3 app-dev/tests/files/make-dpr-stress.py app-dev/tests/files"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from make_dpr_transfer_lib import Report, courses, W   # the drawing code, shared with make-dpr-transfer.py

OK, IP, NO, X = 'ok', 'ip', 'no', 'xfer'

class OldReport(Report):
    """The older layout: the verdict carries the requirement's words and its code on one line."""
    def old(s, v, words, code, units=None, courses=None, used=None, wrap=None, breakwrap=False):
        s.need(40)
        lab = {'S': 'Satisfied:', 'N': 'Not Satisfied:', 'ON': 'Overall Requirement Not Satisfied:', 'OS': 'Overall Requirement Satisfied:', 'IP': 'In Progress:'}[v]
        s.text(lab, 40, bold=True); s.text(words + ('' if wrap else ' ' + code), 40 + 4.6 * len(lab)); s.y -= 10
        if wrap and breakwrap: s.new_page()   # the verdict's last words and its code on the NEXT page, after its furniture
        if wrap: s.text(wrap + ' ' + code, 40); s.y -= 10
        s.y -= 4
        if units: s.text("· Units: " + units, 54); s.y -= 14
        if courses: s.text("· Courses: " + courses, 54); s.y -= 14
        if used: s.table(used)
        s.y -= 4
    def oldhead(s, t):
        s.need(30); s.text(t, 36, size=9); s.y -= 12

def row(term, subj, nbr, title, grade, units, ic, desig=''):
    return (term, subj, nbr, title, grade, units, desig, ic)

# ================================================================================================
# 1. A senior on the Fall Quarter 2023 catalog (the older layout)
# ================================================================================================
def quarter(path):
    r = OldReport("Quinn Stressquarter", "9711001", "October 9, 2026 09:12", "BUS Primary BS UG Major", "Fall Quarter 2023")
    r.y -= 4
    r.text("Financial Management Concentration", 54, bold=True); r.text("Fall Quarter 2023", 465, bold=True); r.y -= 20
    r.oldhead("GENERAL UNDERGRADUATE DEGREE REQUIREMENTS")
    r.old('ON', "***GENERAL UNDERGRADUATE DEGREE REQUIREMENTS 2022-2026 Catalog", "(RG-0005)***")
    r.oldhead("TOTAL UNITS FOR THE DEGREE")
    r.old('S', "TOTAL UNITS FOR THE DEGREE", "(R-0995)")
    r.old('S', "TOTAL UNITS FOR THE DEGREE ('Taken' units cap at minimum required) - 180 Required", "(R995-10)", units="180.00 required, 180.00 used")
    r.oldhead("GRADUATION WRITING REQUIREMENT")
    r.old('ON', "GRADUATION WRITING REQUIREMENT", "(R-0011)")
    r.old('N', "GRADUATION WRITING REQUIREMENT: - Satisfactory Completion Required", "(R11-10)",
          used=[row("2026 Fall", "UNIV", "4401", "GWR Portfolio", "", "0.00", IP)])
    r.oldhead("U.S. CULTURAL PLURALISM REQUIREMENT")
    r.old('S', "U.S. CULTURAL PLURALISM COURSE - 1 Course Required", "(R15-10)", courses=courses(1, 1),
          used=[row("2024 Wtr", "FSN", "250", "Food & Nutr: Culture & Customs", "A-", "4.00", OK, "EU")])
    r.oldhead("GENERAL EDUCATION REQUIREMENTS")
    r.old('S', "***GENERAL EDUCATION REQUIREMENTS 2022-2026 Catalog - 72 Units Required. Refer to Major/Support section for", "(RG-0006)***", wrap="courses that satisfy/double count for GE.")
    r.oldhead("GE AREA A")
    r.old('S', "GE AREA A: ENGLISH LANGUAGE COMMUNICATION AND CRITICAL THINKING - 12 Units Required", "(R-0070)")
    ge = [("A1", "ORAL COMMUNICATION COURSE", "R70-10", "2024 Spr", "COMS", "101 (1101)", "Public Speaking", "B+", OK),
          ("A2", "WRITTEN COMMUNICATION COURSE", "R70-20", "2024 Wtr", "ENGL", "134 (1134)", "Writing and Rhetoric", "A", OK),
          ("A3", "CRITICAL THINKING COURSE", "R70-30", "2024 Spr", "PHIL", "126 (1126)", "Critical Thinking", "B", OK),
          ("B1", "PHYSICAL SCIENCE COURSE", "R71-10", "2025 Spr", "ASTR", "102 (1102)", "Astronomy", "A-", OK),
          ("B2", "LIFE SCIENCE COURSE", "R71-20", "2023 Fall", "BIO", "161 (1151)", "Intro to Cell Biology", "B", OK),
          ("B3", "VERIFICATION OF COMPLETION OF LAB ACTIVITY IN B1 OR B2", "R71-30", "2023 Fall", "BIO", "161 (1151)", "Intro to Cell Biology", "B", OK),
          ("B4", "MATHEMATICS/QUANTITATIVE REASONING COURSE", "R71-40", "2023 Fall", "MATH", "118 (1006)", "Precalculus Algebra", "A", OK),
          ("B UD", "UPPER-DIVISION SCIENTIFIC INQUIRY AND QUANTITATIVE REASONING COURSE", "R71-50", "2026 Spr", "CM", "317 (3317)", "Energy and Resources", "A-", OK),
          ("C1", "ARTS COURSE", "R72-10", "2025 Fall", "ART", "3TC1", "Arts Transfer", "A", X),
          ("C2", "HUMANITIES COURSE", "R72-20", "2025 Spr", "PHIL", "230 (2230)", "Philosophical Classics", "B+", OK),
          ("C UD", "UPPER-DIVISION ARTS & HUMANITIES COURSE", "R72-40", "2026 Spr", "PHIL", "331 (3331)", "Ethics", "A", OK),
          ("D1", "AMERICAN INSTITUTIONS COURSE", "R73-10", "2024 Fall", "POLS", "112 (1112)", "American Government", "B", OK),
          ("D2", "LOWER-DIVISION SOCIAL SCIENCES COURSE", "R73-20", "2024 Wtr", "ECON", "222 (2040)", "Macroeconomics", "A-", OK),
          ("D UD", "UPPER-DIVISION SOCIAL SCIENCES COURSE", "R73-40", "2025 Fall", "DUD", "3TR", "UD D Transfer", "B", X),
          ("E", "LOWER DIVISION LIFELONG LEARNING AND SELF DEVELOPMENT COURSE", "R74-10", "2024 Wtr", "FSN", "250", "Food & Nutr: Culture & Customs", "A-", OK),
          ("F", "ETHNIC STUDIES COURSE", "R75-10", "2024 Wtr", "ES", "255 (2255)", "Ethnic Studies", "A", OK)]
    for area, name, code, term, subj, nbr, title, grade, ic in ge:
        r.oldhead(area)
        r.old('S', f"{area}: {name} - 4 Units Required", f"({code})", units="4.00 required, 4.00 used", used=[row(term, subj, nbr, title, grade, "4.00", ic, area.replace(' ', ''))])
    r.oldhead("LOWER-DIVISION C ELECTIVE")
    r.old('S', "LOWER-DIVISION C ELECTIVE - 4 Units Required", "(R72-30)", units="4.00 required, 4.00 used", used=[row("2025 Fall", "PORT", "1TC2", "Portuguese Transfer", "A", "4.00", X, "C2")])
    r.oldhead("GE ELECTIVES IN AREAS B, C, & D")
    # (stress run, 2026-10-11) a requirement whose verdict wraps across a page break: its code is on the next page
    r.old('S', "GE ELECTIVES IN AREAS B, C, & D", "(R-0076)", wrap="(Note: Courses must come from 2 different GE Areas) - 8 Units Required", breakwrap=True)
    r.old('S', "GE ELECTIVE: AREAS B, C, AND D - 4 Units Required", "(R76-10)", units="4.00 required, 4.00 used", used=[row("2024 Fall", "STAT", "251 (1210)", "Statistical Inference I", "B", "4.00", OK, "B4")])
    r.old('S', "GE ELECTIVE: AREAS B, C, AND D - 4 Units Required", "(R76-20)", units="4.00 required, 4.00 used", used=[row("2026 Sum", "SOC", "110 (1110)", "Comparative Social Institutions", "A", "4.00", OK, "D2")])
    r.oldhead("MAJOR COURSES")
    r.old('ON', "BUSINESS ADMINISTRATION MAJOR COURSES", "(RG-0040)")
    maj = [("BUS 206 (2206)", "R40-10", "2025 Spr", "BUS", "206 (2206)", "Business Law", "B+"),
           ("BUS 207 (2207)", "R40-20", "2024 Fall", "BUS", "207 (2207)", "Legal Environment", "C"),
           ("BUS 214 (2214)", "R40-30", "2025 Wtr", "BUS", "214 (2214)", "Financial Accounting", "A-"),
           ("BUS 215 (2215)", "R40-40", "2025 Spr", "BUS", "215 (2215)", "Managerial Accounting", "B"),
           ("BUS 346 (3346)", "R40-50", "2024 Fall", "BUS", "346 (3346)", "Principles of Marketing", "A"),
           ("BUS 387 (3387)", "R40-60", "2026 Wtr", "BUS", "387 (3387)", "Organizational Behavior", "A-"),
           ("BUS 391 (3391)", "R40-70", "2025 Spr", "BUS", "391 (3391)", "Information Systems", "B+")]
    for words, code, term, subj, nbr, title, grade in maj:
        r.oldhead(words.split(' (')[0])
        r.old('S', f"{words} - 4 Units Required", f"({code})", units="4.00 required, 4.00 used", used=[row(term, subj, nbr, title, grade, "4.00", OK)])
    r.oldhead("BUS 401 (4401) OR BUS 411 (4411)")
    r.old('S', "BUS 401 (4401)/411 (4411) - 4 Units Required", "(R40-80)", units="4.00 required, 4.00 used", used=[row("2025 Fall", "BUS", "401 (4401)", "General Management Transfer", "B", "4.00", X)])
    r.oldhead("CAREER READINESS III")
    r.old('N', "CAREER READINESS III: BUS 306 (3306) - 1 Unit Required", "(R40-90)", units="1.00 required, 0.00 used, 1.00 needed")
    r.oldhead("TECHNOLOGY MANAGEMENT COURSE")
    r.old('N', "TECHNOLOGY MANAGEMENT COURSE: ITP 371 (3371) or BUS 310 (3310) in 1 of 2 Options", "(R-0041)")
    r.old('N', "ITP 371 (3371) - 4 Units Required (Option 1 of 2)", "(R41-10)", units="4.00 required, 0.00 used, 4.00 needed")
    r.old('S', "BUS 310 (3310) - 4 Units Required (Option 2 of 2)", "(R41-20)", units="4.00 required, 4.00 used", used=[row("2026 Wtr", "BUS", "310 (3310)", "Intro to Entrepreneurship", "A", "4.00", OK)])
    r.oldhead("BUSINESS MAJOR SENIOR PROJECT")
    r.old('N', "BUSINESS MAJOR SENIOR PROJECT: BUS 463 (4463) or BUS 464 (4464) - 4 Units Required", "(R40-95)", units="4.00 required, 0.00 used, 4.00 needed")
    r.oldhead("CONCENTRATION")
    r.old('ON', "FINANCIAL MANAGEMENT CONCENTRATION", "(RG-0060)")
    for words, code, term, nbr, title, grade, ic in [("BUS 431 (3431)", "R60-10", "2026 Fall", "431 (3431)", "Security Analysis", "", IP), ("BUS 438 (3438)", "R60-20", "2026 Fall", "438 (3438)", "Corporate Finance", "", IP), ("BUS 439 (4439)", "R60-30", "2026 Spr", "439 (4439)", "Fixed Income", "A-", OK)]:
        r.oldhead(words.split(' (')[0]); r.old('S' if grade else 'IP', f"{words} - 4 Units Required", f"({code})", units="4.00 required, 4.00 used", used=[row(term, "BUS", nbr, title, grade, "4.00", ic)])
    r.oldhead("APPROVED ELECTIVE")
    r.old('N', "APPROVED ELECTIVE: BUS 442 (4442) or BUS 445 (4445) - 4 Units Required", "(R60-40)", units="4.00 required, 0.00 used, 4.00 needed")   # BUS 4442 is being taken, not yet attached
    r.oldhead("SUPPORT COURSES")
    r.old('OS', "BUSINESS ADMINISTRATION SUPPORT COURSES", "(RG-0050)")
    r.old('S', "ECON 221 (2030) - 4 Units Required", "(R50-10)", units="4.00 required, 4.00 used", used=[row("2024 Spr", "ECON", "221 (2030)", "Microeconomics", "B", "4.00", OK)])
    r.old('S', "MATH 221 (1267) - 4 Units Required", "(R50-20)", units="4.00 required, 4.00 used", used=[row("2025 Wtr", "MATH", "221 (1267)", "Calculus for Business", "B+", "4.00", OK)])
    r.oldhead("COURSE CREDITS NOT USED")
    r.old('OS', "***COURSE CREDITS NOT USED", "(RG-0008)***")
    r.text("THE FOLLOWING COURSE CREDITS HAVE NOT BEEN USED TO MEET GE, MAJOR, CONCENTRATION, SUPPORT, OR MINOR", 36); r.y -= 10
    r.text("REQUIREMENTS. See your advisor if you believe any of these should satisfy unmet requirements.(R-0030)", 36); r.y -= 14
    r.text("COURSE CREDITS NOT USED (Counted)", 36); r.y -= 12
    r.table([row("2023 Fall", "BUS", "100", "Business Orientation", "A", "1.00", OK), row("2024 Wtr", "BUS", "207 (2207)", "Legal Environment", "W", "4.00", OK),
             row("2026 Spr", "BUS", "306 (3306)", "Career Readiness III", "A", "1.00", OK)])
    hist = [("2023 Fall", "BIO", "161 (1151)", "Intro to Cell Biology", "B", "4.00", OK), ("2023 Fall", "BUS", "100", "Business Orientation", "A", "1.00", OK), ("2023 Fall", "MATH", "118 (1006)", "Precalculus Algebra", "A", "4.00", OK),
            ("2024 Wtr", "BUS", "207 (2207)", "Legal Environment", "W", "4.00", OK), ("2024 Wtr", "ECON", "222 (2040)", "Macroeconomics", "A-", "4.00", OK), ("2024 Wtr", "ENGL", "134 (1134)", "Writing and Rhetoric", "A", "4.00", OK), ("2024 Wtr", "ES", "255 (2255)", "Ethnic Studies", "A", "4.00", OK), ("2024 Wtr", "FSN", "250", "Food & Nutr: Culture & Customs", "A-", "4.00", OK),
            ("2024 Spr", "COMS", "101 (1101)", "Public Speaking", "B+", "4.00", OK), ("2024 Spr", "ECON", "221 (2030)", "Microeconomics", "B", "4.00", OK), ("2024 Spr", "PHIL", "126 (1126)", "Critical Thinking", "B", "4.00", OK),
            ("2024 Fall", "BUS", "207 (2207)", "Legal Environment", "C", "4.00", OK), ("2024 Fall", "BUS", "346 (3346)", "Principles of Marketing", "A", "4.00", OK), ("2024 Fall", "POLS", "112 (1112)", "American Government", "B", "4.00", OK), ("2024 Fall", "STAT", "251 (1210)", "Statistical Inference I", "B", "4.00", OK),
            ("2025 Wtr", "BUS", "214 (2214)", "Financial Accounting", "A-", "4.00", OK), ("2025 Wtr", "MATH", "221 (1267)", "Calculus for Business", "B+", "4.00", OK),
            ("2025 Spr", "ASTR", "102 (1102)", "Astronomy", "A-", "4.00", OK), ("2025 Spr", "BUS", "206 (2206)", "Business Law", "B+", "4.00", OK), ("2025 Spr", "BUS", "215 (2215)", "Managerial Accounting", "B", "4.00", OK), ("2025 Spr", "BUS", "391 (3391)", "Information Systems", "B+", "4.00", OK), ("2025 Spr", "PHIL", "230 (2230)", "Philosophical Classics", "B+", "4.00", OK),
            ("2025 Fall", "ART", "3TC1", "Arts Transfer", "A", "4.00", X), ("2025 Fall", "BUS", "401 (4401)", "General Management Transfer", "B", "4.00", X), ("2025 Fall", "DUD", "3TR", "UD D Transfer", "B", "4.00", X), ("2025 Fall", "PORT", "1TC2", "Portuguese Transfer", "A", "4.00", X), ("2025 Fall", "TRAN", "302", "Study Abroad", "333", "12.00", X),
            ("2026 Wtr", "BUS", "310 (3310)", "Intro to Entrepreneurship", "A", "4.00", OK), ("2026 Wtr", "BUS", "387 (3387)", "Organizational Behavior", "A-", "4.00", OK),
            ("2026 Spr", "BUS", "306 (3306)", "Career Readiness III", "A", "1.00", OK), ("2026 Spr", "BUS", "439 (4439)", "Fixed Income", "A-", "4.00", OK), ("2026 Spr", "CM", "317 (3317)", "Energy and Resources", "A-", "4.00", OK), ("2026 Spr", "PHIL", "331 (3331)", "Ethics", "A", "4.00", OK),
            ("2026 Sum", "SOC", "110 (1110)", "Comparative Social Institutions", "A", "4.00", OK),
            ("2026 Fall", "BUS", "3431", "Security Analysis", "", "6.00", IP), ("2026 Fall", "BUS", "3438", "Corporate Finance", "", "6.00", IP), ("2026 Fall", "BUS", "4442", "Intro to Futures & Options", "", "4.50", IP), ("2026 Fall", "UNIV", "4401", "GWR Portfolio", "", "0.00", IP)]
    r.history(hist)
    r.save(path)

# ================================================================================================
# 2. A junior on the Fall Quarter 2024 catalog, in Fall 2026 (quarter past, semester present) — and v2 in January
# ================================================================================================
def mixed(path, v2=False):
    r = OldReport("Morgan Stressmixed", "9711002", "January 12, 2027 08:40" if v2 else "October 9, 2026 09:20", "BUS Primary BS UG Major", "Fall Quarter 2024")
    r.y -= 4
    r.text("Marketing Management Concentration", 54, bold=True); r.text("Fall Quarter 2024", 465, bold=True); r.y -= 20
    r.oldhead("GENERAL UNDERGRADUATE DEGREE REQUIREMENTS")
    r.old('ON', "***GENERAL UNDERGRADUATE DEGREE REQUIREMENTS 2022-2026 Catalog", "(RG-0005)***")
    r.old('N', "TOTAL UNITS FOR THE DEGREE ('Taken' units cap at minimum required) - 180 Required", "(R995-10)", units="180.00 required, 112.00 used, 68.00 needed" if v2 else "180.00 required, 96.00 used, 84.00 needed")
    r.oldhead("GENERAL EDUCATION REQUIREMENTS")
    r.old('ON', "***GENERAL EDUCATION REQUIREMENTS 2022-2026 Catalog - 72 Units Required", "(RG-0006)***")
    for area, name, code, term, subj, nbr, title, grade in [("A1", "ORAL COMMUNICATION COURSE", "R70-10", "2025 Spr", "COMS", "101 (1101)", "Public Speaking", "A"), ("A2", "WRITTEN COMMUNICATION COURSE", "R70-20", "2024 Fall", "ENGL", "134 (1134)", "Writing and Rhetoric", "B+"), ("A3", "CRITICAL THINKING COURSE", "R70-30", "2025 Wtr", "PHIL", "126 (1126)", "Critical Thinking", "A-"),
                                                            ("B4", "MATHEMATICS/QUANTITATIVE REASONING COURSE", "R71-40", "2024 Fall", "MATH", "221 (1267)", "Calculus for Business", "B"), ("D2", "LOWER-DIVISION SOCIAL SCIENCES COURSE", "R73-20", "2025 Wtr", "ECON", "222 (2040)", "Macroeconomics", "B+"), ("F", "ETHNIC STUDIES COURSE", "R75-10", "2025 Spr", "ES", "255 (2255)", "Ethnic Studies", "A")]:
        r.oldhead(area); r.old('S', f"{area}: {name} - 4 Units Required", f"({code})", units="4.00 required, 4.00 used", used=[row(term, subj, nbr, title, grade, "4.00", OK, area)])
    r.oldhead("C UD")
    if v2: r.old('S', "C UD: UPPER-DIVISION ARTS & HUMANITIES COURSE - 4 Units Required", "(R72-40)", units="4.00 required, 4.50 used", used=[row("2026 Fall", "PHIL", "3331", "Ethics", "A-", "4.50", OK, "UD3")])
    else: r.old('N', "C UD: UPPER-DIVISION ARTS & HUMANITIES COURSE - 4 Units Required", "(R72-40)", units="4.00 required, 0.00 used, 4.00 needed")
    r.oldhead("D UD")
    if v2: r.old('S', "D UD: UPPER-DIVISION SOCIAL SCIENCES COURSE - 4 Units Required", "(R73-40)", units="4.00 required, 4.50 used", used=[row("2026 Fall", "NR", "3308", "Fire and Society", "B+", "4.50", OK, "UD4")])
    else: r.old('N', "D UD: UPPER-DIVISION SOCIAL SCIENCES COURSE - 4 Units Required", "(R73-40)", units="4.00 required, 0.00 used, 4.00 needed", used=[row("2026 Fall", "NR", "3308", "Fire and Society", "", "4.50", IP, "UD4")])
    r.oldhead("E")
    r.old('N', "E: LOWER DIVISION LIFELONG LEARNING AND SELF DEVELOPMENT COURSE - 4 Units Required", "(R74-10)", units="4.00 required, 0.00 used, 4.00 needed")
    r.oldhead("LOWER-DIVISION C ELECTIVE")
    r.old('N', "LOWER-DIVISION C ELECTIVE - 4 Units Required", "(R72-30)", units="4.00 required, 0.00 used, 4.00 needed")
    r.oldhead("MAJOR COURSES")
    r.old('ON', "BUSINESS ADMINISTRATION MAJOR COURSES", "(RG-0040)")
    for words, code, term, nbr, title, grade in [("BUS 214 (2214)", "R40-30", "2025 Spr", "214 (2214)", "Financial Accounting", "A"), ("BUS 346 (3346)", "R40-50", "2025 Fall", "346 (3346)", "Principles of Marketing", "A-")]:
        r.oldhead(words.split(' (')[0]); r.old('S', f"{words} - 4 Units Required", f"({code})", units="4.00 required, 4.00 used", used=[row(term, "BUS", nbr, title, grade, "4.00", OK)])
    r.oldhead("BUS 215")
    r.old('N', "BUS 215 (2215) - 4 Units Required", "(R40-40)", units="4.00 required, 0.00 used, 4.00 needed")
    r.oldhead("BUS 387")
    if v2: r.old('S', "BUS 387 (3387) - 4 Units Required", "(R40-60)", units="4.00 required, 4.50 used", used=[row("2026 Fall", "BUS", "3387", "Organizational Behavior", "B", "4.50", OK)])
    else: r.old('N', "BUS 387 (3387) - 4 Units Required", "(R40-60)", units="4.00 required, 0.00 used, 4.00 needed")   # v1: not yet taken (the student plans it); v2: a late add, graded
    r.oldhead("BUS 391")
    r.old('N', "BUS 391 (3391) - 4 Units Required", "(R40-70)", units="4.00 required, 0.00 used, 4.00 needed")
    if v2:
        r.oldhead("CAREER READINESS II")
        r.old('N', "CAREER READINESS II: BUS 305 (3305) - 1 Unit Required", "(R40-85)", units="1.00 required, 0.00 used, 1.00 needed")
    r.oldhead("GRADUATION WRITING REQUIREMENT")
    r.old('N', "", "(R11-10)")   # a verdict with no words: the reader can't place it
    hist = [("2024 Fall", "ENGL", "134 (1134)", "Writing and Rhetoric", "B+", "4.00", OK), ("2024 Fall", "MATH", "221 (1267)", "Calculus for Business", "B", "4.00", OK),
            ("2025 Wtr", "ECON", "222 (2040)", "Macroeconomics", "B+", "4.00", OK), ("2025 Wtr", "PHIL", "126 (1126)", "Critical Thinking", "A-", "4.00", OK),
            ("2025 Spr", "BUS", "214 (2214)", "Financial Accounting", "A", "4.00", OK), ("2025 Spr", "COMS", "101 (1101)", "Public Speaking", "A", "4.00", OK), ("2025 Spr", "ES", "255 (2255)", "Ethnic Studies", "A", "4.00", OK),
            ("2025 Fall", "BUS", "346 (3346)", "Principles of Marketing", "A-", "4.00", OK),
            ("2026 Fall", "NR", "3308", "Fire and Society", "B+" if v2 else "", "4.50", OK if v2 else IP)]
    if v2: hist += [("2026 Fall", "BUS", "3387", "Organizational Behavior", "B", "4.50", OK), ("2026 Fall", "PHIL", "3331", "Ethics", "A-", "4.50", OK), ("2027 Spr", "BUS", "2215", "Managerial Accounting", "", "4.50", IP), ("2027 Spr", "BUS", "3391", "Information Systems", "", "4.50", IP)]
    r.history(hist)
    r.save(path)

# ================================================================================================
# 3. A semester-catalog student in a major the app has no flowchart for
# ================================================================================================
def nomajor(path):
    r = Report("Dana Stressnomajor", "9711003", "October 9, 2026 09:30", "DANC Primary BA UG Major", "Fall Semester 2026")
    r.head("GENERAL EDUCATION (2026)", size=10); r.verdict('ON', "(RG6)")
    r.head("1A: WRITTEN COMMUNICATION COURSE", 40); r.verdict('S', "NOTE: Minimum grade of C- required", more=["3 units"], code="(R70-10)", courses=courses(1, 1), used=[row("2026 Fall", "ENGL", "1134", "Writing and Rhetoric", "A", "3.00", OK, "1A")])
    r.head("1B: CRITICAL THINKING COURSE", 40); r.verdict('N', "3 units", code="(R70-20)", courses=courses(1, 0, 1))
    r.head("2: MATHEMATICS AND QUANTITATIVE REASONING COURSE", 40); r.verdict('N', "3 units", code="(R71-10)", courses=courses(1, 0, 1))
    r.head("DANCE MAJOR COURSES (2026)", size=10); r.verdict('ON', "(RG40)")
    r.head("DANC 1100", 40); r.verdict('S', "2 units", code="(R40-10)", courses=courses(1, 1), used=[row("2026 Fall", "DANC", "1100", "Dance Technique I", "A", "2.00", OK)])
    r.head("DANC 2200", 40); r.verdict('N', "2 units", code="(R40-20)", courses=courses(1, 0, 1))
    r.history([("2026 Fall", "DANC", "1100", "Dance Technique I", "A", "2.00", OK), ("2026 Fall", "ENGL", "1134", "Writing and Rhetoric", "A", "3.00", OK), ("2026 Fall", "DANC", "1110", "Dance Appreciation", "", "3.00", IP)])
    r.save(path)

# ================================================================================================
# 4. A semester sophomore: a duplicated row, a class two lines use, "Choose one" with Option 2 in progress, the closing "FREE ELECTIVES" block (no verdict; PSY 200 used for nothing)
# ================================================================================================
def dupes(path):
    r = Report("Sam Stressdupes", "9711004", "October 9, 2026 09:40", "BUS Primary BS UG Major", "Fall Semester 2026")
    r.y -= 4; r.text("Financial Management Concentration", 54, bold=True); r.text("Fall Semester 2026", 465, bold=True); r.y -= 20
    r.head("GENERAL EDUCATION (2026)", size=10); r.verdict('ON', "(RG6)")
    r.head("2: MATHEMATICS AND QUANTITATIVE REASONING COURSE", 40); r.verdict('S', "3 units", code="(R71-10)", courses=courses(1, 1), used=[row("2026 Spr", "MATH", "221", "Calculus for Business", "B", "2.67", OK, "B4")])
    r.head("4B: SOCIAL & BEHAVIORAL SCIENCES COURSE", 40); r.verdict('S', "3 units", code="(R73-20)", courses=courses(1, 1), used=[row("2026 Spr", "ECON", "222", "Macroeconomics", "A", "2.67", OK, "D2")])
    r.head("3A: ARTS COURSE", 40); r.verdict('N', "3 units", code="(R72-10)", courses=courses(1, 0, 1))
    r.head("BUSINESS MAJOR COURSES (2026)", size=10); r.verdict('ON', "(RG40)")
    r.head("MATH 1267 (GE 2)", 40); r.verdict('S', "4 units", code="(R40-10)", courses=courses(1, 1), used=[row("2026 Spr", "MATH", "221", "Calculus for Business", "B", "2.67", OK)])
    r.head("ECON 2040 (GE 4B)", 40); r.verdict('S', "3 units", code="(R40-20)", courses=courses(1, 1), used=[row("2026 Spr", "ECON", "222", "Macroeconomics", "A", "2.67", OK)])
    r.head("BUS 2214", 40); r.verdict('N', "3 units", code="(R40-30)", courses=courses(1, 0, 1))
    r.head("STATISTICS - OPTION (2026)"); r.verdict('N', "Choose one", more=["3-4 units"], code="(R45)")
    r.head("STAT 2510", 40); r.verdict('N', "Option 1 of 2", more=["3 units"], code="(R45-10)", courses=courses(1, 0, 1))
    r.head("STAT 1210", 40); r.verdict('N', "Option 2 of 2", more=["4 units"], code="(R45-20)", courses=courses(1, 0, 1), used=[row("2026 Fall", "STAT", "1210", "Statistics", "", "4.00", IP)])
    # the closing block: no verdict, its code on a line of its own — its table is NO line's classes
    r.head("FREE ELECTIVES & COURSES NOT COUNTED FOR DEGREE CREDIT", size=10); r.text("(RG8)", 36); r.y -= 12
    r.text("Course credits not used for GE, MAJOR, CONCENTRATION, SUPPORT, or MINOR.", 36); r.y -= 12; r.text("(R30)", 36); r.y -= 12; r.text("FREE ELECTIVES", 36); r.y -= 12
    r.table([row("2026 Spr", "PSY", "200", "General Psychology", "A", "2.67", OK)])
    # the same Spring class printed twice (a registrar duplicate): one record row, never two
    r.history([("2026 Spr", "ECON", "222", "Macroeconomics", "A", "2.67", OK), ("2026 Spr", "MATH", "221", "Calculus for Business", "B", "2.67", OK), ("2026 Spr", "MATH", "221", "Calculus for Business", "B", "2.67", OK), ("2026 Spr", "PSY", "200", "General Psychology", "A", "2.67", OK),
               ("2026 Fall", "STAT", "1210", "Statistics", "", "4.00", IP), ("2026 Fall", "BUS", "1342", "Business Communications", "", "3.00", IP)])
    r.save(path)

if __name__ == '__main__':
    out = sys.argv[1]
    quarter(os.path.join(out, 'dpr-stress-quarter.pdf'))
    mixed(os.path.join(out, 'dpr-stress-mixed.pdf')); mixed(os.path.join(out, 'dpr-stress-mixed-v2.pdf'), v2=True)
    nomajor(os.path.join(out, 'dpr-stress-nomajor.pdf'))
    dupes(os.path.join(out, 'dpr-stress-dupes.pdf'))
    print('make-dpr-stress: 5 reports')
