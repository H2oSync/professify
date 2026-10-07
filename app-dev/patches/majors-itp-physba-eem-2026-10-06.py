#!/usr/bin/env python3
"""The phone's major list gets Industrial Technology and Packaging and Physics (BA); Experience and Event
Management gets its current name (Tate, 2026-10-05/06: "ITP is missing from major list is there anything else
that missing?" → "okay add these make sure we have their flowcharts updated and prerecs").

Checked against Cal Poly's 2026–28 catalog (Programs A–Z), San Luis Obispo programs only (the five Solano /
Maritime programs are out: the app takes SLO students):

1. Industrial Technology & Packaging (BS). The website already had it, as a hand-written plan appended after
   the main SCHED_MAJORS line — but the phone's planner.js lifts only that main line (app-dev/source/build.py),
   so the phone never had it. The website's plan was also the *Industrial Technology concentration's* roadmap
   presented as everyone's (ITP 2260, 3390, 4403, 4410, 4415, 4428, 4496, 4497 as required for all, its approved
   electives labelled "Concentration course"). It is now the catalog's "Concentration Not Yet Declared" roadmap,
   word for word: the shared core, with Concentration Course slots where either concentration's classes go
   (MAJOR_CATALOG already lists both concentrations' required classes). Math and statistics "or" rows are
   choice slots; the business-calculus path is "MATH 1267 & 1277", so its option is MATH 1277 (the workshop
   taken with 1267) — MATH 1267 alone must not fill the slot. Ranged units take the lower number (Free Elective 2–3 → 2); Year 4 Spring's 0–2 unit free
   elective is left out (it can be zero).
2. Physics (BA) — new, from the catalog's four-year plan, row for row (the app's "Physics" is the BS). Named
   "Physics (BA)" so it can't be mistaken for the BS in a picker.
3. Experience & Event Management (BS) — the catalog's current name for what the app called "Recreation, Parks &
   Tourism Administration / Experience Industry Management" (the EIM course requisites name both majors). Its
   flowchart matched the catalog's General/Undeclared roadmap except Year 2 Spring, one 3-unit GE short (now 16
   units, as the catalog has it). The name changes everywhere it is a key (MAJOR_CATALOG, CONC_CATALOG, SCHED_MAJORS, the website's COLLEGES list). A profile still saved with the
   old name is read as the new one on both apps (MAJOR_RENAMED), so nobody's plan disappears before the
   one-line SQL in sql/professify-new-majors-prereqs.sql renames stored profiles.

Also: the website's "coming soon" list compared names exactly, so "Industrial Technology and Packaging" stayed
listed as coming next to the live "Industrial Technology & Packaging"; it now compares them the way majorFor does.

Edits index.html, app/planner.js, app/index.html and app-dev/source/build.py.
Applies after review-fixes-0115-2026-10-05.py (build 2026-10-06 06:25).
Usage: python3 majors-itp-physba-eem-2026-10-06.py <repo-dir>
"""
import sys, os, json

R = sys.argv[1]
OLD = 'Recreation, Parks & Tourism Administration / Experience Industry Management'
NEW = 'Experience & Event Management'


def ge(t):
    return {'title': t, 'units': 3, 'type': 'ge'}


def c(code, title, units):
    return {'code': code, 'title': title, 'units': units, 'type': 'course'}


def ch(title, units, options):
    return {'title': title, 'units': units, 'type': 'choice', 'options': options}


CONC = {'title': 'Concentration Course', 'units': 3, 'type': 'concentration'}

ITP_TERMS = [
    (1, 'Fall', [c('ITP 1100', 'Student Orientation, College Success, and Career Readiness', 1),
                 c('ITP 1125', 'Introduction to Industrial Technology and Packaging', 1),
                 ch('Calculus I, or Business Calculus with its workshop (MATH 1267 & 1277)', 4, ['MATH 1261', 'MATH 1277']),
                 c('PHYS 1121', 'College Physics I', 4),
                 ge('GE · Area 1A')]),
    (1, 'Spring', [c('ITP 1150', 'Power Systems and Renewable Energy', 3),
                   c('ITP 2233', 'Product Modeling and Communication', 3),
                   c('CHEM 1120', 'Fundamentals of Chemical Structure and Properties', 4),
                   ch('Applied Statistical Concepts and Methods or Business Statistics I', 3, ['STAT 1110', 'STAT 1210']),
                   ge('GE · Area 1C')]),
    (2, 'Fall', [c('ITP 3330', 'Packaging Fundamentals', 3),
                 c('ITP 3371', 'Supply Chain Management in Manufacturing and Services', 3),
                 c('ECON 2001', 'Survey of Economics', 3),
                 dict(CONC), ge('GE · Area 1B')]),
    (2, 'Spring', [c('ITP 3303', 'Lean Six Sigma Green Belt', 3),
                   c('ITP 3326', 'Product Design and Development', 3),
                   c('BUS 3391', 'Information Systems', 3),
                   dict(CONC), ge('GE · Area 3A')]),
    (3, 'Fall', [c('ITP 4409', 'Packaging Machinery and Processes', 3),
                 c('BUS 3346', 'Principles of Marketing', 3),
                 dict(CONC), ge('GE · Area 4A'), ge('GE · Area 6'),
                 {'title': 'Free Elective (2-3 units, use lower)', 'units': 2, 'type': 'elective'}]),
    (3, 'Spring', [c('ITP 3341', 'Packaging Polymers and Processing', 3),
                   dict(CONC), dict(CONC), ge('GE · Area 3B'), ge('GE · Area 5B')]),
    (4, 'Fall', [c('ITP 4411', 'Packaging Sustainability', 3),
                 dict(CONC), dict(CONC), dict(CONC), ge('GE · Upper-Division 3')]),
    (4, 'Spring', [c('ITP 4464', 'Senior Project', 3),
                   dict(CONC, title='Concentration Course (3-4 units, use lower)'),
                   dict(CONC, title='Concentration Course (3-4 units, use lower)'),
                   ge('GE · Upper-Division 4')]),
]

G = 'GE · General Education Requirement'
FE = lambda u: {'title': 'Free Elective', 'units': u, 'type': 'elective'}
PHYSBA_TERMS = [
    (1, 'Fall', [c('PHYS 1100', 'Introduction to the Physics Major', 1),
                 c('CHEM 1120', 'Fundamentals of Chemical Structure and Properties', 4),
                 c('MATH 1261', 'Calculus I', 4), ge('GE · Area 1A'), ge('GE · Area 1C')]),
    (1, 'Spring', [c('PHYS 1141', 'General Physics I', 4),
                   c('CSC 1001', 'Fundamentals of Computer Science and Laboratory (CSC 1001 & 1001L)', 4),
                   c('MATH 1262', 'Calculus II', 4), ge('GE · Area 1B')]),
    (2, 'Fall', [c('PHYS 1143', 'General Physics II', 4), c('MATH 2263', 'Calculus III', 3), ge(G), ge(G), ge(G)]),
    (2, 'Spring', [c('PHYS 2211', 'General Physics III: Modern Physics', 4), c('MATH 2341', 'Linear Analysis', 4), ge(G), ge(G)]),
    (3, 'Fall', [c('PHYS 3305', 'Classical Mechanics I', 3),
                 c('PHYS 3316', 'Instrumentation and Techniques of Experimental Physics', 4),
                 c('PHYS 3320', 'Methods of Theoretical Physics', 4), ge(G)]),
    (3, 'Spring', [c('PHYS 3301', 'Statistical Mechanics', 3), c('PHYS 3339', 'Communicating Physics', 1),
                   c('PHYS 3340', 'Quantum Physics Laboratory I', 1),
                   c('PHYS 4408', 'Electromagnetic Fields and Waves I', 3), ge(G), FE(4)]),
    (4, 'Fall', [c('PHYS 3341', 'Quantum Physics Laboratory II', 1), c('PHYS 4405', 'Quantum Mechanics I', 3),
                 c('PHYS 4461', 'Senior Project I (or Senior Project I and II)', 2), ge(G), FE(3), FE(3)]),
    (4, 'Spring', [FE(4), FE(4), FE(4), FE(4)]),
]


def entry(name, degree, college, src, terms):
    out = []
    for i, (yr, tm, slots) in enumerate(terms):
        out.append({'year': yr, 'term': tm, 'slots': [dict({'id': 't%ds%d' % (i, j)}, **s) for j, s in enumerate(slots)]})
    return {'name': name, 'degree': degree, 'college': college, 'conc': None, 'src': src, 'terms': out}


ITP = entry('Industrial Technology & Packaging', 'BS', 'Orfalea College of Business',
            'https://catalog.calpoly.edu/business/undergraduate/industrial-technology-packaging-bs/', ITP_TERMS)
PHYSBA = entry('Physics (BA)', 'BA', 'Bailey College of Science & Mathematics',
               'https://catalog.calpoly.edu/science-mathematics/physics/physics-ba/', PHYSBA_TERMS)
# the catalog's own term totals, checked here so a slip in the table above can't ship
for e, want in ((ITP, [13, 16, 15, 15, 17, 15, 15, 12]), (PHYSBA, [15, 15, 16, 14, 14, 15, 15, 16])):
    got = [sum(s['units'] for s in t['slots']) for t in e['terms']]
    assert got == want, (e['name'], got, want)
LINES = ("/* Industrial Technology & Packaging and Physics (BA): the Cal Poly 2026–28 catalog's own four-year plans "
         "(2026-10-06; ITP is the undeclared-concentration roadmap). */\n"
         "window.SCHED_MAJORS['ocob-itp']=" + json.dumps(ITP, ensure_ascii=False, separators=(',', ':')) + ";\n"
         "window.SCHED_MAJORS['m-physicsba']=" + json.dumps(PHYSBA, ensure_ascii=False, separators=(',', ':')) + ";")
ALIAS_JS = "const MAJOR_RENAMED = {" + json.dumps(OLD) + ": " + json.dumps(NEW) + "};\nconst majorNow = m => (m && MAJOR_RENAMED[m]) || m;\n"


def rw(path, fn):
    p = os.path.join(R, path)
    s = open(p, encoding='utf-8').read()
    t = fn(s)
    open(p, 'w', encoding='utf-8').write(t)


def one(s, a, b, n=1):
    if s.count(a) != n:
        sys.exit(f'anchor matched {s.count(a)}x (want {n}): {a[:90]}')
    return s.replace(a, b)


def eem_y2s(s):
    """EEM's Year 2 Spring had two GE slots; the catalog's General/Undeclared roadmap has three (3, 3 and 1 units,
    term total 16). The missing 3-unit one goes in as t3s5, before the 1-unit one."""
    i = s.index('"m-recreationparksandtourismadministrationexperienceindustry')
    j = s.index('"year":3,"term":"Fall"', i)
    a = '{"id":"t3s3","title":"GE Requirement","units":3,"type":"ge"},{"id":"t3s4","title":"GE Requirement","units":1,"type":"ge"}]}'
    if s[i:j].count(a) != 1:
        sys.exit('EEM Year 2 Spring anchor not found')
    b = '{"id":"t3s3","title":"GE Requirement","units":3,"type":"ge"},{"id":"t3s5","title":"GE Requirement","units":3,"type":"ge"},{"id":"t3s4","title":"GE Requirement","units":1,"type":"ge"}]}'
    return s[:i] + s[i:j].replace(a, b) + s[j:]


def desktop(s):
    if "window.SCHED_MAJORS['m-physicsba']" in s:
        sys.exit('already patched')
    a = s.index("/* Industrial Technology & Packaging — real term-by-term plan from the official")
    b = s.index("/* ===== Real-course full-plan generator for every remaining Cal Poly major =====")
    old = s[a:b]
    assert old.count("window.SCHED_MAJORS['ocob-itp']=") == 1 and old.rstrip().endswith(']};'), old[-80:]
    s = s[:a] + LINES + '\n' + s[b:]
    s = eem_y2s(s)
    s = one(s, OLD, NEW, 5)
    s = one(s, "'Microbiology','Physics','Public Health','Statistics']", "'Microbiology','Physics','Physics (BA)','Public Health','Statistics']")
    s = one(s, "(function(){var live=new Set(Object.values(window.SCHED_MAJORS).map(function(m){return m.name;}));"
               "window.SCHED_COMING=(window.SCHED_COMING||[]).map(function(g){return [g[0]].concat(g.slice(1).filter(function(n){return !live.has(n);}));})",
            "(function(){var nm=function(s){return String(s||'').toLowerCase().replace(/&/g,'and').replace(/[^a-z0-9]+/g,'');};"
            "var live=new Set(Object.values(window.SCHED_MAJORS).map(function(m){return nm(m.name);}));"
            "window.SCHED_COMING=(window.SCHED_COMING||[]).map(function(g){return [g[0]].concat(g.slice(1).filter(function(n){return !live.has(nm(n));}));})")
    # a profile saved under the old name reads as the new one
    s = one(s, "  if(!p||!p.major)return false;\n  student.major=p.major;",
            "  if(!p||!p.major)return false;\n  student.major=(p.major===" + json.dumps(OLD) + ")?" + json.dumps(NEW) + ":p.major;   /* renamed 2026-10-06 */")
    return s


def planner(s):
    if "window.SCHED_MAJORS['m-physicsba']" in s:
        sys.exit('already patched')
    a = s.index('window.SCHED_MAJORS={"')
    e = s.index('\n', a)
    s = s[:e + 1] + LINES + '\n' + s[e + 1:]
    s = eem_y2s(s)
    return one(s, OLD, NEW, 3)


def phone(s):
    if 'const MAJOR_RENAMED' in s:
        sys.exit('already patched')
    s = one(s, "  TC.profile = p.data || null;\n",
            "  TC.profile = p.data || null;\n  if (TC.profile && TC.profile.major) TC.profile.major = majorNow(TC.profile.major);\n")
    s = one(s, "{ major: p.major || '', standing: p.class_standing || ''",
            "{ major: majorNow(p.major) || '', standing: p.class_standing || ''")
    s = one(s, "function concRemember(", ALIAS_JS + "function concRemember(")
    # the concentration kept on this phone is stored beside the major it was picked for; an old-name entry
    # still belongs to the renamed major (Sonnet review)
    s = one(s, "if (d && d.major && d.major === p.major && d.conc", "if (d && d.major && majorNow(d.major) === p.major && d.conc")
    s = one(s, "m.u === (TC.user && TC.user.id) && m.major === p.major && m.conc", "m.u === (TC.user && TC.user.id) && majorNow(m.major) === p.major && m.conc")
    s = one(s, "if (d && d.major && d.major === major) { d.conc = conc || null;", "if (d && d.major && majorNow(d.major) === major) { d.major = major; d.conc = conc || null;")
    return s


def build(s):
    a = "_a = _ix.index('window.SCHED_MAJORS={\"'); L.append(_ix[_a:_ix.index('\\n', _a)])\n"
    b = (a + "# 2026-10-06: majors written as their own lines after it (ITP, Physics BA) come along too\n"
         "_a = _ix.index(\"window.SCHED_MAJORS['ocob-itp']=\"); L.append(_ix[_a:_ix.index('\\n', _ix.index(\"window.SCHED_MAJORS['m-physicsba']=\"))])\n")
    return one(s, a, b)


rw('index.html', desktop)
rw('app/planner.js', planner)
rw('app/index.html', phone)
rw('app-dev/source/build.py', build)
print('patched')
