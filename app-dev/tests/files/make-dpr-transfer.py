#!/usr/bin/env python3
"""SYNTHETIC Degree Progress Reports for transfer students (2026-10-11) — invented names, EMPLIDs, classes and grades,
laid out the way Cal Poly's 2026-catalog report prints (read against real ones 2026-10-11; nothing of them is in
here): page furniture with the name and EMPLID on every page, the icon legend on page 1 (Cal Poly's report says which
classes are transfer credit ONLY with an icon), requirement headings with "Satisfied:" / "Not Satisfied:" verdicts and
their (R…) codes on their own lines, "· Units:" / "· Courses:" counts, "Courses Used" tables WITH GRADES and an icon on
every row, "Not Satisfied: Choose one" over "Option 1 of 2" lines, then the Course History table.

  dpr-transfer-first.pdf      a junior in his FIRST term after transferring: every community-college and exam class
                              prints in "2026 Fall" with a grade (some "300"/"400"), beside the 3 he's taking
  dpr-transfer-continuing.pdf a senior who transferred in Fall 2025: his transfer credit prints in 2025 Fall with
                              letter grades, beside the Cal Poly classes he took that term; exam credit as "CR" with no
                              icon; Cal Poly Spring 2026; 3 in progress (one clears the writing requirement); a study-
                              abroad placeholder this term (AP 300, transfer icon, no grade) that he isn't "taking"
  dpr-transfer-partial.pdf    the senior's report with Cal Poly's check drawn as a picture too big for an icon (a page
                              whose pictures can't all be matched: no row may be called "no icon")
  dpr-transfer-noicons.pdf    the first one with no pictures at all (a copy that lost them), plus a 2025 Summer
                              transfer placeholder (PHIL 1T1B)
  dpr-transfer-oddlegend.pdf  the first one with the legend's arrow one colour unit off the table's: no picture is the
                              transfer one, and none is Cal Poly's — the words decide (the date and "300"/"400")
  dpr-transfer-badlegend.pdf  the senior's report whose legend gives "Transfer/Test/Other Credit" Cal Poly's check: a
                              legend that can't be trusted is not used at all
  dpr-transfer-form.pdf       the senior's report with every page drawn inside a form XObject that has its own matrix
  dpr-fall-graded.pdf         not a transfer: a sophomore's report printed December 20, 2026, after Fall grades
                              posted — Fall 2026 is graded Cal Poly work, Spring 2027 is registered

Usage: python3 app-dev/tests/files/make-dpr-transfer.py app-dev/tests/files"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from make_dpr_transfer_lib import *   # Report, icons, courses(), W, H (split out 2026-10-11)

# ================================================================================================
# 1. A junior in his first term after transferring (Environmental Management & Protection)
# ================================================================================================
def first(path, icons=True, extra_summer=False, legend_xfer='xfer'):
    r = Report("Riley Fixture", "9876501", "October 9, 2026 17:40", "ENVM Primary BS UG Major", "Fall Semester 2026", icons, legend_xfer=legend_xfer)
    X = 'xfer'
    r.head("UNDERGRADUATE DEGREE REQUIREMENTS", size=10); r.verdict('ON', "2026-Current Catalog", code="(RG5)")
    r.head("TOTAL UNITS: DEGREE REQUIREMENT"); r.verdict('ON', "(R995)")
    r.head("TOTAL UNITS: MINIMUM UNIT DEGREE REQUIREMENT", 40); r.verdict('N', "120 units", more=["Excess units not counted. Maximum 70 units from community college."], code="(R995-10)", units="120.00 required, 80.00 used, 40.00 needed")
    r.head("UPPER DIVISION UNITS: DEGREE REQUIREMENT"); r.verdict('ON', "(R996)")
    r.head("UPPER DIVISION UNITS: MINIMUM UNIT DEGREE REQUIREMENT", 40); r.verdict('N', "40 units", more=["Excess units not counted."], code="(R996-10)", units="40.00 required, 10.00 used, 30.00 needed")
    r.head("CAL POLY RESIDENCE UNITS: DEGREE REQUIREMENTS"); r.verdict('ON', "NOTE: Unit calculation includes units completed through Cal Poly enrollment.", code="(R997)")
    r.head("RESIDENCE UNITS: CAL POLY MINIMUM UNITS REQUIREMENT", 40); r.verdict('N', "33 units", more=["Excess units not counted."], code="(R997-10)", units="33.00 required, 13.00 used, 20.00 needed")
    r.head("UNITED STATES CULTURAL PLURALISM (USCP): DEGREE REQUIREMENT"); r.verdict('N', 'See "Class Schedule" for a list of approved USCP courses.', code="(R15)")
    r.head("U.S. CULTURAL PLURALISM (USCP): ONE COURSE MINIMUM REQUIREMENT", 40); r.verdict('N', "(R15-10)", courses=courses(1, 0, 1),
        used=[("2026 Fall", "ES", "3350", "Race and the Environment", "", "3.00", "", 'ip')])
    r.head("GRADUATION WRITING (GWR): DEGREE REQUIREMENT"); r.verdict('ON', "(R11)")
    r.head("GRADUATION WRITING (GWR): CONFIRMATION OF REQUIREMENT COMPLETION", 40); r.verdict('N', "NOTE: Requirement may not display as completed until one week after GWR course grade is posted.", code="(R11-10)")
    r.head("GPA: HIGHER EDUCATION, RESIDENCE, AND MAJOR REQUIREMENTS (2026)"); r.verdict('S', 'Requirement may display as "in progress" after unit minimum is complete.', code="(R1108)")
    r.head("GPA: HIGHER EDUCATION CUMULATIVE 2.00 MINIMUM REQUIREMENT", 40); r.verdict('S', "(R1108-10)")
    r.head("GENERAL EDUCATION REQUIREMENTS", size=10); r.verdict('ON', "2026-Current Catalog", more=["43 units required", "NOTE: Some Major/Support courses also satisfy GE."], code="(RG6)")
    r.head("GE AREA 1: ENGLISH COMMUNICATION AND CRITICAL THINKING"); r.verdict('S', "9 units required", code="(R70)")
    r.head("1A: WRITTEN COMMUNICATION COURSE", 40); r.verdict('S', "NOTE: Minimum grade of C- required", more=["3 units"], code="(R70-10)", courses=courses(1, 1), used=[("2026 Fall", "ENGL", "1134", "Writing and Rhetoric", "300", "3.00", "1A", X)])
    r.head("1B: CRITICAL THINKING COURSE", 40); r.verdict('S', "NOTE: Minimum grade of C- required", more=["3 units"], code="(R70-20)", courses=courses(1, 1), used=[("2026 Fall", "ENGL", "1T13", "GE1B or 3B ENGL Xfer", "A-", "3.00", "1B", X)])
    r.head("1C: ORAL COMMUNICATION COURSE", 40); r.verdict('S', "NOTE: Minimum grade of C- required", more=["3 units"], code="(R70-30)", courses=courses(1, 1), used=[("2026 Fall", "COMS", "1102", "Public Speaking Digital Spaces", "A", "3.00", "1C", X)])
    r.head("GE AREA 2: MATHEMATICS & QUANTITATIVE REASONING"); r.verdict('S', "3 units required", code="(R2570)")
    r.head("2: MATHEMATICS AND QUANTITATIVE REASONING COURSE", 40); r.verdict('S', "NOTE: Minimum grade of C- required", more=["3 units"], code="(R2570-15)", courses=courses(1, 1), used=[("2026 Fall", "MATH", "1267", "Business Calculus", "400", "3.00", "2", X)])
    r.head("GE AREA 3: ARTS & HUMANITIES"); r.verdict('S', "6 units required", code="(R74)")
    r.head("3A: ARTS COURSE", 40); r.verdict('S', "3 units", code="(R74-10)", courses=courses(1, 1), used=[("2026 Fall", "MU", "1T3A", "GE3A MU Xfer", "A", "3.00", "3A", X)])
    r.head("3B: HUMANITIES COURSE -- LITERATURE, PHILOSOPHY, LANGUAGES OTHER THAN ENGLISH", 40); r.verdict('S', "3 units", code="(R74-20)", courses=courses(1, 1), used=[("2026 Fall", "HIST", "4A1", "HIST US-1 (40404)", "B", "3.00", "3B4B", X)])
    r.head("GE AREA 4: 4A AMERICAN INSTITUTIONS (TITLE 5, SECTION 40404 REQUIREMENT)"); r.verdict('S', "3 units required", code="(R21)")
    r.head("4A: Select from ES 1112, GOV 2200, HIST 2201, 2202, 2206, POLS 1112, or WGQS 220", 40); r.verdict('S', "3 units", code="(R21-10)", courses=courses(1, 1), used=[("2026 Fall", "POLS", "4AA", "POLS US-1&2&3 Full 40404", "B-", "3.00", "4A", X)])
    r.head("GE AREA 4: 4B SOCIAL & BEHAVIORAL SCIENCES"); r.verdict('S', "NOTE: At least two different course prefixes required in Area 4 (4A/4B/4UD)", more=["3 units required"], code="(R78)")
    r.head("4B: SOCIAL & BEHAVIORAL SCIENCES COURSE", 40); r.verdict('S', "3 units", code="(R78-10)", courses=courses(1, 1), used=[("2026 Fall", "ECON", "2030", "Microeconomics", "B+", "3.00", "4B", X)])
    r.head("GE AREA 5: PHYSICAL & LIFE SCIENCES"); r.verdict('S', "7 units required", code="(R73)")
    r.head("5A: PHYSICAL SCIENCES COURSE", 40); r.verdict('S', "3 units", code="(R73-10)", units="3.00 required, 3.00 used", used=[("2026 Fall", "5AGE", "1TR", "Physical Science", "A", "3.00", "5A", X)])
    r.head("5B: LIFE SCIENCES COURSE", 40); r.verdict('S', "3 units", code="(R73-20)", units="3.00 required, 3.00 used", used=[("2026 Fall", "BIO", "1114", "Plant Diversity and Ecology", "A", "4.00", "5B5C", X)])
    r.head("5C: LABORATORY COURSE (Some 5A and 5B lecture/lab combo courses complete 5C)", 40); r.verdict('S', "1 unit", code="(R73-30)", units="1.00 required, 1.00 used", used=[("2026 Fall", "5A5C", "1TR", "Physical Science and Lab", "A", "1.00", "5A5C", X)])
    r.head("GE AREA 6: ETHNIC STUDIES"); r.verdict('S', "3 units required", code="(R86)")
    r.head("6: ETHNIC STUDIES COURSE", 40); r.verdict('S', "3 units", code="(R86-10)", courses=courses(1, 1), used=[("2026 Fall", "ES", "4A1", "ES US-1 (40404)", "A", "3.00", "634A", X)])
    r.head("GE: UPPER-DIVISION AREAS"); r.verdict('ON', "9 units required", code="(R2571)")
    r.head("AREA 2 or 5: UD MATH & QUANTITATIVE REASONING or PHYSICAL & LIFE SCIENCES COURSE", 40); r.verdict('N', "NOTE: Junior Standing required", more=["3 units"], code="(R2571-10)", courses=courses(1, 0, 1))
    r.head("AREA 3: UPPER-DIVISION ARTS & HUMANITIES COURSE", 40); r.verdict('N', "NOTE: Junior Standing required", more=["3 units"], code="(R2571-20)", courses=courses(1, 0, 1))
    r.head("AREA 4: UPPER-DIVISION SOCIAL & BEHAVIORAL SCIENCES COURSE", 40); r.verdict('S', "NOTE: Junior Standing required.", more=["3 units"], code="(R2571-30)", courses=courses(1, 1), used=[("2026 Fall", "NR", "3308", "Fire and Society", "", "3.00", "4UD", 'ip')])
    r.head("GE: VERIFICATION OF MINIMUM UNIT REQUIREMENTS"); r.verdict('ON', "(R84)")
    r.head("GE: RESIDENCE UNITS REQUIREMENT", 40); r.verdict('N', 'Requirement may display as "in progress" after unit minimum is complete.', code="(R84-20)", units="9.00 required, 3.00 used, 6.00 needed")
    r.head("FREE ELECTIVES & COURSES NOT COUNTED FOR DEGREE CREDIT", size=10); r.text("(RG8)", 40); r.y -= 14
    r.head("Course credits not used for GE, MAJOR, CONCENTRATION, SUPPORT, or MINOR."); r.text("(R30)", 40); r.y -= 14
    r.head("FREE ELECTIVES", 40); r.table([("2026 Fall", "BUS", "1TR", "Bus Transfer Lower Division", "B", "3.00", "", X), ("2026 Fall", "CSC", "1TR", "CSC Transfer Lower Division", "A", "3.00", "", X), ("2026 Fall", "CSC", "1TR", "CSC Transfer Lower Division", "B+", "3.00", "", X)])
    r.head("ENVIRONMENTAL MANAGEMENT & PROTECTION MAJOR B.S. (2026-Current Catalog)", size=10); r.verdict('ON', "56 units required", code="(RG229)")
    r.head("MAJOR CORE COURSES (2026)"); r.verdict('ON', "31 units", code="(R797)")
    r.head("NR 1142", 40); r.verdict('S', "4 units", code="(R797-10)", courses=courses(1, 1), used=[("2026 Fall", "NR", "1142", "Environmental Management", "", "4.00", "", 'ip')])
    r.head("NR 3363", 40); r.verdict('N', "2 units", code="(R797-30)", courses=courses(1, 0, 1))
    r.head("NR 2208, BIO 2215, or BIO 2217", 40); r.verdict('N', "3 units", code="(R797-40)", courses=courses(1, 0, 1))
    r.head("MAJOR CORE COURSES - OPTION (2026)"); r.verdict('N', "Choose one", more=["3-4 units"], code="(R2865)")
    r.head("NR 3319 & 3320", 40); r.verdict('N', "Option 1 of 2", more=["3 units"], code="(R2865-10)", courses=courses(2, 0, 2))
    r.head("NR 4402, NR/SS 4421, SS 3321, or ERSC 3303", 40); r.verdict('N', "Option 2 of 2", more=["3-4 units"], code="(R2865-20)", courses=courses(1, 0, 1))
    r.head("SUPPORT COURSES (2026)"); r.verdict('ON', "18 units required", code="(R2626)")
    r.head("MATH 1264 or 1267 (GE 2)", 40); r.verdict('S', "3-4 units", code="(R2626-30)", courses=courses(1, 1), used=[("2026 Fall", "MATH", "1267", "Business Calculus", "400", "3.00", "2", X)])
    r.head("SS 1120", 40); r.verdict('N', "4 units", code="(R2626-40)", courses=courses(1, 0, 1))
    r.head("STAT 1110", 40); r.verdict('S', "3 units", code="(R2626-50)", courses=courses(1, 1), used=[("2026 Fall", "STAT", "1210", "Business Statistics I", "400", "3.00", "2", X)])
    r.head("ENVM CONCENTRATION: UNDECLARED (2026-Current Catalog)", size=10); r.verdict('N', "15 units required", code="(RG2337)", units="15.00 required, 0.00 used, 15.00 needed")
    r.head("CONCENTRATION UNDECLARED (2026)"); r.verdict('N', "(R798)")
    rows = ([("2025 Sum", "PHIL", "1T1B", "GE1B PHIL Xfer", "B", "3.00", X)] if extra_summer else []) + [
        ("2026 Fall", "1AGE", "1TR", "English Composition", "300", "1.00", X), ("2026 Fall", "5A5C", "1TR", "Physical Science and Lab", "A", "1.00", X),
        ("2026 Fall", "5AGE", "1TR", "Physical Science", "A", "3.00", X), ("2026 Fall", "BIO", "1114", "Plant Diversity and Ecology", "A", "4.00", X),
        ("2026 Fall", "BUS", "1TR", "Bus Transfer Lower Division", "B", "3.00", X), ("2026 Fall", "COMS", "1102", "Public Speaking Digital Spaces", "A", "3.00", X),
        ("2026 Fall", "CSC", "1TR", "CSC Transfer Lower Division", "A", "3.00", X), ("2026 Fall", "CSC", "1TR", "CSC Transfer Lower Division", "B+", "3.00", X),
        ("2026 Fall", "ECON", "2030", "Microeconomics", "B+", "3.00", X), ("2026 Fall", "ENGL", "1134", "Writing and Rhetoric", "300", "3.00", X),
        ("2026 Fall", "ENGL", "1T13", "GE1B or 3B ENGL Xfer", "A-", "3.00", X), ("2026 Fall", "ES", "4A1", "ES US-1 (40404)", "A", "3.00", X),
        ('designation', "634A - GE 6 or 3B or 4B or 4A partial"),
        ("2026 Fall", "HIST", "4A1", "HIST US-1 (40404)", "B", "3.00", X), ('designation', "3B4B - GE 3B or 4B"),
        ("2026 Fall", "MATH", "1267", "Business Calculus", "400", "3.00", X), ("2026 Fall", "MU", "1T3A", "GE3A MU Xfer", "A", "3.00", X),
        ("2026 Fall", "POLS", "4AA", "POLS US-1&2&3 Full 40404", "B-", "3.00", X), ("2026 Fall", "STAT", "1210", "Business Statistics I", "400", "3.00", X),
        ("2026 Fall", "ES", "3350", "Race and the Environment", "", "3.00", 'ip'), ("2026 Fall", "NR", "1142", "Environmental Management", "", "4.00", 'ip'),
        ("2026 Fall", "NR", "3308", "Fire and Society", "", "3.00", 'ip')]
    r.history(rows); r.save(path)

# ================================================================================================
# 2. A senior who transferred in Fall 2025 (Business Administration, Financial Management)
# ================================================================================================
def continuing(path, big_ok=False, legend_xfer='xfer'):
    r = Report("Casey Fixture", "9876502", "November 3, 2026 15:10", "BUS Primary BS UG Major", "Fall Semester 2025", big_ok=big_ok, legend_xfer=legend_xfer)
    X, C, P = 'xfer', 'ok', 'ip'
    r.head("UNDERGRADUATE DEGREE REQUIREMENTS", size=10); r.verdict('ON', "2025-Current Catalog", code="(RG5)")
    r.head("TOTAL UNITS: DEGREE REQUIREMENT"); r.verdict('ON', "(R995)")
    r.head("TOTAL UNITS: MINIMUM UNIT DEGREE REQUIREMENT", 40); r.verdict('N', "120 units", more=["Excess units not counted. Maximum 70 units from community college."], code="(R995-10)", units="120.00 required, 96.00 used, 24.00 needed")
    r.head("UNITED STATES CULTURAL PLURALISM (USCP): DEGREE REQUIREMENT"); r.verdict('N', 'See "Class Schedule" for a list of approved USCP courses.', code="(R15)")
    r.head("U.S. CULTURAL PLURALISM (USCP): ONE COURSE MINIMUM REQUIREMENT", 40); r.verdict('N', "(R15-10)", courses=courses(1, 0, 1))
    r.head("GRADUATION WRITING (GWR): DEGREE REQUIREMENT"); r.verdict('ON', "(R11)")
    r.head("GRADUATION WRITING (GWR): CONFIRMATION OF REQUIREMENT COMPLETION", 40); r.verdict('N', "NOTE: Requirement may not display as completed until one week after GWR course grade is posted.", code="(R11-10)",
        used=[("2026 Fall", "BUS", "4401", "General Management & Strategy", "", "4.00", "", P)])
    r.head("GPA: HIGHER EDUCATION, RESIDENCE, AND MAJOR REQUIREMENTS (2025)"); r.verdict('S', 'Requirement may display as "in progress" after unit minimum is complete.', code="(R1108)")
    r.head("GPA: HIGHER EDUCATION CUMULATIVE 2.00 MINIMUM REQUIREMENT", 40); r.verdict('S', "(R1108-10)")
    r.head("GENERAL EDUCATION REQUIREMENTS", size=10); r.verdict('ON', "2025-Current Catalog", more=["43 units required"], code="(RG6)")
    r.head("GE AREA 1: ENGLISH COMMUNICATION AND CRITICAL THINKING"); r.verdict('S', "9 units required", code="(R70)")
    r.head("1A: WRITTEN COMMUNICATION COURSE", 40); r.verdict('S', "NOTE: Minimum grade of C- required", more=["3 units"], code="(R70-10)", courses=courses(1, 1), used=[("2025 Fall", "ENGL", "1134", "Writing and Rhetoric", "400", "3.00", "1A", X)])
    r.head("1B: CRITICAL THINKING COURSE", 40); r.verdict('S', "NOTE: Minimum grade of C- required", more=["3 units"], code="(R70-20)", courses=courses(1, 1), used=[("2025 Fall", "PHIL", "1T1B", "GE1B PHIL Xfer", "A", "3.00", "1B", X)])
    r.head("1C: ORAL COMMUNICATION COURSE", 40); r.verdict('S', "NOTE: Minimum grade of C- required", more=["3 units"], code="(R70-30)", courses=courses(1, 1), used=[("2025 Fall", "COMS", "1101", "Public Speaking", "B+", "3.00", "1C", X)])
    r.head("GE AREA 2: MATHEMATICS & QUANTITATIVE REASONING"); r.verdict('S', "3 units required", code="(R2570)")
    r.head("2: MATHEMATICS AND QUANTITATIVE REASONING COURSE", 40); r.verdict('S', "NOTE: Minimum grade of C- required", more=["3 units"], code="(R2570-15)", courses=courses(1, 1), used=[("2025 Fall", "MATH", "1221", "Finite Mathematics", "A", "4.00", "2", X)])
    r.head("GE AREA 4: 4B SOCIAL & BEHAVIORAL SCIENCES"); r.verdict('S', "3 units required", code="(R78)")
    r.head("4B: SOCIAL & BEHAVIORAL SCIENCES COURSE", 40); r.verdict('S', "3 units", code="(R78-10)", courses=courses(1, 1), used=[("2025 Fall", "ECON", "2030", "Microeconomics", "CR", "3.00", "4B", None)])
    r.head("GE: UPPER-DIVISION AREAS"); r.verdict('ON', "9 units required", code="(R2571)")
    r.head("AREA 3: UPPER-DIVISION ARTS & HUMANITIES COURSE", 40); r.verdict('N', "NOTE: Junior Standing required", more=["3 units"], code="(R2571-20)", courses=courses(1, 0, 1))
    r.head("AREA 4: UPPER-DIVISION SOCIAL & BEHAVIORAL SCIENCES COURSE", 40); r.verdict('S', "NOTE: Junior Standing required.", more=["3 units"], code="(R2571-30)", courses=courses(1, 1), used=[("2026 Spr", "BUS", "3387", "Organizational Behavior", "B", "4.00", "4UD", C)])
    r.head("BUSINESS ADMINISTRATION MAJOR B.S. (2025-Current Catalog)", size=10); r.verdict('ON', "76 units required", code="(RG150)")
    r.head("BUSINESS CORE (2025)"); r.verdict('ON', "40 units", code="(R510)")
    for code, nbr, title, term, grade, ic, st in [("R510-10", "2201", "Financial Accounting", "2025 Fall", "A-", X, 'S'), ("R510-20", "2212", "Managerial Accounting", "2025 Fall", "B", C, 'S'),
                                                ("R510-30", "2207", "Legal Responsibilities of Bus", "2025 Fall", "A", C, 'S'), ("R510-40", "3346", "Principles of Marketing", "2026 Spr", "A-", C, 'S'),
                                                ("R510-50", "3387", "Organizational Behavior", "2026 Spr", "B", C, 'S'), ("R510-60", "3391", "Information Systems", "2026 Spr", "A", C, 'S')]:
        r.head("BUS " + nbr, 40); r.verdict(st, "4 units", code=f"({code})", courses=courses(1, 1), used=[(term, "BUS", nbr, title, grade, "4.00", "", ic)])
    r.head("BUS 4401", 40); r.verdict('N', "4 units", code="(R510-70)", courses=courses(1, 0, 1))
    r.head("STAT 2170", 40); r.verdict('S', "4 units", code="(R510-80)", courses=courses(1, 1), used=[("2025 Fall", "STAT", "2170", "Applied Statistics", "B+", "4.00", "", C)])
    r.head("BUSINESS ELECTIVE - OPTION (2025)"); r.verdict('N', "Choose one", more=["4 units"], code="(R511)")
    r.head("BUS 4436", 40); r.verdict('N', "Option 1 of 2", more=["4 units"], code="(R511-10)", courses=courses(1, 0, 1))
    r.head("ECON 4405 or ECON 4406", 40); r.verdict('N', "Option 2 of 2", more=["4 units"], code="(R511-20)", courses=courses(1, 0, 1))
    r.head("FINANCIAL MANAGEMENT CONCENTRATION (2025-Current Catalog)", size=10); r.verdict('ON', "20 units required", code="(RG410)")
    r.head("FINANCIAL MANAGEMENT CONCENTRATION COURSES (2025)"); r.verdict('ON', "12 units", code="(R420)")
    r.head("BUS 3431", 40); r.verdict('N', "4 units", code="(R420-10)", courses=courses(1, 0, 1), used=[("2026 Fall", "BUS", "3431", "Security Anlys & Portfolio Mgm", "", "4.00", "", P)])
    r.head("BUS 3438", 40); r.verdict('N', "4 units", code="(R420-20)", courses=courses(1, 0, 1), used=[("2026 Fall", "BUS", "3438", "Corporate Finance", "", "4.00", "", P)])
    r.head("BUS 4442", 40); r.verdict('N', "4 units", code="(R420-30)", courses=courses(1, 0, 1))
    r.history([
        ("2025 Fall", "BUS", "1TR", "Bus Transfer Lower Division", "A", "3.00", X), ("2025 Fall", "BUS", "2201", "Financial Accounting", "A-", "4.00", X),
        ("2025 Fall", "BUS", "2207", "Legal Responsibilities of Bus", "A", "4.00", C), ("2025 Fall", "BUS", "2212", "Managerial Accounting", "B", "4.00", C),
        ("2025 Fall", "COMS", "1101", "Public Speaking", "B+", "3.00", X), ("2025 Fall", "ECON", "2030", "Microeconomics", "CR", "3.00", None),
        ("2025 Fall", "ENGL", "1134", "Writing and Rhetoric", "400", "3.00", X), ("2025 Fall", "MATH", "1221", "Finite Mathematics", "A", "4.00", X),
        ("2025 Fall", "PHIL", "1T1B", "GE1B PHIL Xfer", "A", "3.00", X), ("2025 Fall", "STAT", "2170", "Applied Statistics", "B+", "4.00", C),
        ("2026 Spr", "BUS", "3346", "Principles of Marketing", "A-", "4.00", C), ("2026 Spr", "BUS", "3387", "Organizational Behavior", "B", "4.00", C),
        ("2026 Spr", "BUS", "3391", "Information Systems", "A", "4.00", C),
        ("2026 Fall", "AP", "300", "Affiliated Programs Outgoing", "", "12.00", X),
        ("2026 Fall", "BUS", "3431", "Security Anlys & Portfolio Mgm", "", "4.00", P), ("2026 Fall", "BUS", "3438", "Corporate Finance", "", "4.00", P),
        ("2026 Fall", "BUS", "4401", "General Management & Strategy", "", "4.00", P)])
    r.save(path)

# ================================================================================================
# 4. Not a transfer: printed after Fall 2026's grades posted (Business Administration sophomore)
# ================================================================================================
def fall_graded(path):
    r = Report("Jamie Fixture", "9876504", "December 20, 2026 09:15", "BUS Primary BS UG Major", "Fall Semester 2025")
    C, P = 'ok', 'ip'
    r.head("UNDERGRADUATE DEGREE REQUIREMENTS", size=10); r.verdict('ON', "2025-Current Catalog", code="(RG5)")
    r.head("TOTAL UNITS: DEGREE REQUIREMENT"); r.verdict('ON', "(R995)")
    r.head("TOTAL UNITS: MINIMUM UNIT DEGREE REQUIREMENT", 40); r.verdict('N', "120 units", code="(R995-10)", units="120.00 required, 36.00 used, 84.00 needed")
    r.head("GENERAL EDUCATION REQUIREMENTS", size=10); r.verdict('ON', "2025-Current Catalog", code="(RG6)")
    r.head("GE AREA 1: ENGLISH COMMUNICATION AND CRITICAL THINKING"); r.verdict('S', "9 units required", code="(R70)")
    r.head("1A: WRITTEN COMMUNICATION COURSE", 40); r.verdict('S', "3 units", code="(R70-10)", courses=courses(1, 1), used=[("2025 Fall", "ENGL", "1134", "Writing and Rhetoric", "B+", "3.00", "1A", C)])
    r.head("1C: ORAL COMMUNICATION COURSE", 40); r.verdict('S', "3 units", code="(R70-30)", courses=courses(1, 1), used=[("2026 Fall", "COMS", "1101", "Public Speaking", "A", "3.00", "1C", C)])
    r.head("BUSINESS ADMINISTRATION MAJOR B.S. (2025-Current Catalog)", size=10); r.verdict('ON', "76 units required", code="(RG150)")
    r.head("BUSINESS CORE (2025)"); r.verdict('ON', "40 units", code="(R510)")
    r.head("BUS 2201", 40); r.verdict('S', "4 units", code="(R510-10)", courses=courses(1, 1), used=[("2026 Fall", "BUS", "2201", "Financial Accounting", "A-", "4.00", "", C)])
    r.head("BUS 2212", 40); r.verdict('N', "4 units", code="(R510-20)", courses=courses(1, 0, 1))
    r.history([
        ("2025 Fall", "BUS", "1100", "Student Orientation & Success", "A", "2.00", C), ("2025 Fall", "ENGL", "1134", "Writing and Rhetoric", "B+", "3.00", C),
        ("2026 Spr", "ECON", "2030", "Microeconomics", "B", "3.00", C), ("2026 Spr", "STAT", "2170", "Applied Statistics", "A-", "4.00", C),
        ("2026 Fall", "BUS", "2201", "Financial Accounting", "A-", "4.00", C), ("2026 Fall", "COMS", "1101", "Public Speaking", "A", "3.00", C),
        ("2027 Spr", "BUS", "2212", "Managerial Accounting", "", "4.00", P), ("2027 Spr", "BUS", "2207", "Legal Responsibilities of Bus", "", "4.00", P)])
    r.save(path)

def wrap_in_forms(src, dst, dy=20):
    """Every page's drawing moved into a form XObject whose own /Matrix shifts it down dy, drawn shifted up dy: the
    page looks the same, but a picture's position needs the form's matrix to come out right."""
    from pypdf import PdfReader, PdfWriter
    from pypdf.generic import DecodedStreamObject, NameObject, ArrayObject, FloatObject, DictionaryObject
    rd = PdfReader(src); wr = PdfWriter()
    for pg in rd.pages:
        wp = wr.add_page(pg)
        form = DecodedStreamObject(); form.set_data(wp.get_contents().get_data())
        res = wp['/Resources'].get_object()
        form.update({NameObject('/Type'): NameObject('/XObject'), NameObject('/Subtype'): NameObject('/Form'),
                     NameObject('/BBox'): ArrayObject([FloatObject(0), FloatObject(-dy), FloatObject(W), FloatObject(H + dy)]),
                     NameObject('/Matrix'): ArrayObject([FloatObject(1), FloatObject(0), FloatObject(0), FloatObject(1), FloatObject(0), FloatObject(-dy)]),
                     NameObject('/Resources'): res})
        fref = wr._add_object(form)
        xo = DictionaryObject(res.get('/XObject', DictionaryObject()).get_object()) if '/XObject' in res else DictionaryObject()
        xo[NameObject('/TCFm')] = fref
        nres = DictionaryObject(res); nres[NameObject('/XObject')] = xo
        wp[NameObject('/Resources')] = nres
        body = DecodedStreamObject(); body.set_data(f'q 1 0 0 1 0 {dy} cm /TCFm Do Q'.encode())
        wp[NameObject('/Contents')] = wr._add_object(body)
    with open(dst, 'wb') as f: wr.write(f)

out = sys.argv[1] if len(sys.argv) > 1 else os.path.dirname(os.path.abspath(__file__))
first(os.path.join(out, 'dpr-transfer-first.pdf'))
continuing(os.path.join(out, 'dpr-transfer-continuing.pdf'))
continuing(os.path.join(out, 'dpr-transfer-partial.pdf'), big_ok=True)
first(os.path.join(out, 'dpr-transfer-noicons.pdf'), icons=False, extra_summer=True)
fall_graded(os.path.join(out, 'dpr-fall-graded.pdf'))
# the review's three (2026-10-11): a legend arrow a pixel different from the table's; a legend that gives the transfer label
# Cal Poly's own picture; and the senior's report drawn inside form XObjects with their own matrix
first(os.path.join(out, 'dpr-transfer-oddlegend.pdf'), legend_xfer='xfer2')
continuing(os.path.join(out, 'dpr-transfer-badlegend.pdf'), legend_xfer='ok')
wrap_in_forms(os.path.join(out, 'dpr-transfer-continuing.pdf'), os.path.join(out, 'dpr-transfer-form.pdf'))
print('wrote 8 synthetic reports to', out)
