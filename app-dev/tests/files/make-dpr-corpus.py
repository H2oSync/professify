#!/usr/bin/env python3
"""300 SYNTHETIC Degree Progress Reports, each with its answer key (Tate, 2026-10-12: "create 300 different (artificial
ones based on the flowchart and different years and majors quarters and semester use the actual information we have
on these classes and work backward … units and transfer abroad credits as well as failing a class or classes counting
towards requirements and everything … so we know every scenario we might be up against").

Everything is invented — people, EMPLIDs, grades. The CLASSES are real: each student walks one of the app's 64
flowcharts (app/planner.js SCHED_MAJORS) year by year, takes real GE classes for each area (GE_COURSES), and a student on
a 2022–26 quarter catalog takes the quarter number of each class (the app's own crosswalk, reversed) with its
semester pair. The report is drawn in the two layouts make-dpr-stress.py / make-dpr-transfer.py draw (both read
against real reports): the older one for quarter catalogs, the 2026 one for semester catalogs.

The KEY is worked out from what the student actually did — never from what TermChamp reads — so a difference is a
finding: which lines are done (a finished passing class), being taken (this term's class), open, or unreadable; which
Course History rows are transfer credit; which classes are being taken; what Past classes should count after the save.

Scenarios mixed in (each report lists its own): every major with a flowchart and a few without; quarter catalogs
2022–2025, the 2026 semester catalog, a quarter student who switched to the semester catalog; first-years through
fifth-years; printed in October (Fall in progress) or January (Fall graded, Spring registered); community-college
transfers (new and continuing), AP/exam credit, study abroad; an F then a retake, an F never retaken, a W, a D where
C- is required, NC on a credit/no-credit class, a repeated class; a class the registrar hasn't attached yet ("late");
"1 of 2 Options" / "Choose one"; concentrations; electives; a verdict wrapped across a page break; a split code;
a registrar duplicate row; a verdict the reader can't place; a copy whose icons were lost.
Added 2026-10-12 (Tate: "also add these Not covered yet"): a class taken in a Summer term; a minor, and a second major,
each with its own section of lines; an Incomplete ("I") on a finished-term class; a semester-catalog student past the
first term (printed October 2027 / 2028, or the January after) — the key carries the clock (`clock`) for the app.
These draw from their own random stream, so the original scenarios stay as they were.

Usage:  python3 make-dpr-corpus.py <out-dir> [count=300] [seed=20261012]
        python3 make-dpr-corpus.py --fixture <pdf> | --fixture-more <pdf>   (check-app's two small reports)
Writes <out-dir>/synth-NNN.pdf and synth-NNN.key.json, and <out-dir>/index.json."""
import json, os, random, subprocess, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from make_dpr_transfer_lib import Report, courses as cnt, W

OK, IP, NO, X = 'ok', 'ip', 'no', 'xfer'
FIRST = ['Avery', 'Jordan', 'Riley', 'Casey', 'Morgan', 'Taylor', 'Quinn', 'Rowan', 'Skyler', 'Reese', 'Emerson', 'Finley', 'Harper', 'Kendall',
         'Logan', 'Parker', 'Sage', 'Blake', 'Drew', 'Jamie', 'Hayden', 'Peyton', 'Remy', 'Shea', 'Tatum', 'Arden', 'Ellis', 'Marlo', 'Noel', 'Wren']
LAST = ['Synthwood', 'Fakerson', 'Testwell', 'Mockley', 'Draftly', 'Samplebury', 'Placeholt', 'Dummond', 'Fixtureman', 'Stubbs', 'Proxley', 'Imitato']
GRADES = ['A', 'A', 'A-', 'A-', 'B+', 'B+', 'B', 'B', 'B-', 'C+', 'C']
TW = {'Fall': 'Fall', 'Wtr': 'Winter', 'Spr': 'Spring', 'Sum': 'Summer'}
ORD = {'Wtr': 1, 'Spr': 2, 'Sum': 3, 'Fall': 4}
# quarter GE areas → the semester area the app maps them to (index.html GE_QTR)
QGE = [('A1', '1C', 'ORAL COMMUNICATION COURSE', 'R70-10'), ('A2', '1A', 'WRITTEN COMMUNICATION COURSE', 'R70-20'), ('A3', '1B', 'CRITICAL THINKING COURSE', 'R70-30'),
       ('B1', '5A', 'PHYSICAL SCIENCE COURSE', 'R71-10'), ('B2', '5B', 'LIFE SCIENCE COURSE', 'R71-20'), ('B3', '5C', 'VERIFICATION OF COMPLETION OF LAB ACTIVITY IN B1 OR B2', 'R71-30'),
       ('B4', '2', 'MATHEMATICS/QUANTITATIVE REASONING COURSE', 'R71-40'), ('B UD', 'U25', 'UPPER-DIVISION SCIENTIFIC INQUIRY AND QUANTITATIVE REASONING COURSE', 'R71-50'),
       ('C1', '3A', 'ARTS COURSE', 'R72-10'), ('C2', '3B', 'HUMANITIES COURSE', 'R72-20'), ('C UD', 'UD3', 'UPPER-DIVISION ARTS & HUMANITIES COURSE', 'R72-40'),
       ('D1', '4A', 'AMERICAN INSTITUTIONS COURSE', 'R73-10'), ('D2', '4B', 'LOWER-DIVISION SOCIAL SCIENCES COURSE', 'R73-20'), ('D UD', 'UD4', 'UPPER-DIVISION SOCIAL SCIENCES COURSE', 'R73-40'),
       ('E', '4B', 'LOWER DIVISION LIFELONG LEARNING AND SELF DEVELOPMENT COURSE', 'R74-10'), ('F', '6', 'ETHNIC STUDIES COURSE', 'R75-10')]
SGE = [('1A', 'WRITTEN COMMUNICATION COURSE', 'R70-10', 'R70', 'GE AREA 1: ENGLISH COMMUNICATION AND CRITICAL THINKING'), ('1B', 'CRITICAL THINKING COURSE', 'R70-20', 'R70', None),
       ('1C', 'ORAL COMMUNICATION COURSE', 'R70-30', 'R70', None), ('2', 'MATHEMATICS AND QUANTITATIVE REASONING COURSE', 'R2570-15', 'R2570', 'GE AREA 2: MATHEMATICS & QUANTITATIVE REASONING'),
       ('3A', 'ARTS COURSE', 'R74-10', 'R74', 'GE AREA 3: ARTS & HUMANITIES'), ('3B', 'HUMANITIES COURSE -- LITERATURE, PHILOSOPHY, LANGUAGES OTHER THAN ENGLISH', 'R74-20', 'R74', None),
       ('4A', 'AMERICAN INSTITUTIONS COURSE', 'R21-10', 'R21', 'GE AREA 4: 4A AMERICAN INSTITUTIONS (TITLE 5, SECTION 40404 REQUIREMENT)'),
       ('4B', 'SOCIAL & BEHAVIORAL SCIENCES COURSE', 'R78-10', 'R78', 'GE AREA 4: 4B SOCIAL & BEHAVIORAL SCIENCES'),
       ('5A', 'PHYSICAL SCIENCES COURSE', 'R73-10', 'R73', 'GE AREA 5: PHYSICAL & LIFE SCIENCES'), ('5B', 'LIFE SCIENCES COURSE', 'R73-20', 'R73', None),
       ('5C', 'LABORATORY COURSE (Some 5A and 5B lecture/lab combo courses complete 5C)', 'R73-30', 'R73', None), ('6', 'ETHNIC STUDIES COURSE', 'R86-10', 'R86', 'GE AREA 6: ETHNIC STUDIES'),
       ('U25', 'AREA 2 or 5: UD MATH & QUANTITATIVE REASONING or PHYSICAL & LIFE SCIENCES COURSE', 'R2571-10', 'R2571', 'GE: UPPER-DIVISION AREAS'),
       ('UD3', 'AREA 3: UPPER-DIVISION ARTS & HUMANITIES COURSE', 'R2571-20', 'R2571', None), ('UD4', 'AREA 4: UPPER-DIVISION SOCIAL & BEHAVIORAL SCIENCES COURSE', 'R2571-30', 'R2571', None)]
NOFLOW = [('Recreation, Parks & Tourism Administration', 'RPTA', 'RPTA'), ('Women’s & Gender Studies', 'WGQS', 'WGQS'), ('Dance', 'DANC', 'DANC'), ('Ethnic Studies Minor Track', 'ES', 'ES')]

def load_data(root):
    out = subprocess.check_output(['node', os.path.join(HERE, 'dpr-corpus-export.mjs'), root])
    return json.loads(out)

class OldReport(Report):
    """make-dpr-stress.py's older layout: the verdict carries the requirement's words and its code on one line."""
    def old(s, v, words, code, units=None, courses=None, used=None, wrap=None, breakwrap=False, splitcode=False):
        s.need(40)
        if not wrap and len(words) + len(code) > 100:   # the report wraps a long verdict; its code ends the last line
            cut = words.rfind(' ', 0, 95)
            if cut > 20: words, wrap = words[:cut], words[cut + 1:]
        lab = {'S': 'Satisfied:', 'N': 'Not Satisfied:', 'ON': 'Overall Requirement Not Satisfied:', 'OS': 'Overall Requirement Satisfied:', 'IP': 'In Progress:'}[v]
        s.text(lab, 40, bold=True)
        if splitcode and not wrap:   # the code itself split across two lines: "(R73-" / "45)"
            a, b = code[:-3], code[-3:]
            s.text(words + ' ' + a, 40 + 4.6 * len(lab)); s.y -= 10; s.text(b, 40); s.y -= 10
        else:
            s.text(words + ('' if wrap else ' ' + code), 40 + 4.6 * len(lab)); s.y -= 10
        if wrap and breakwrap: s.new_page()
        if wrap: s.text(wrap + ' ' + code, 40); s.y -= 10
        s.y -= 4
        if units: s.text("· Units: " + units, 54); s.y -= 14
        if courses: s.text("· Courses: " + courses, 54); s.y -= 14
        if used: s.table(used)
        s.y -= 4
    def oldhead(s, t):
        s.need(30); s.text(t, 36, size=9); s.y -= 12

def u2(x): return f"{x:.2f}"

class Gen:
    def __init__(s, data, seed):
        s.D = data; s.seed = seed; s.synth = {}; s.synth_used = set()
        s.flow = data['flow']; s.names = data['names']
        for m in s.flow.values():
            for t in m['terms']:
                for sl in t['slots']:
                    if sl.get('code'): sl['code'] = ' & '.join(s.norm(x.strip()) if x.strip()[:1].isalpha() else x.strip() for x in sl['code'].split(' & '))
                    if sl.get('options'): sl['options'] = [s.norm(o) for o in sl['options']]
        s.rev = {}
        for q, sem in data['equiv'].items():
            s.rev.setdefault(sem, q)
        s.ge = {}
        for g in data['ge']:
            s.ge.setdefault(g['area'], []).append(g)
        s.genames = {g['code']: g['name'] for g in data['ge']}
        s.flownames = {}
        for m in s.flow.values():
            for t in m['terms']:
                for sl in t['slots']:
                    if sl.get('code') and sl.get('title') and ' & ' not in sl['code'] and ' or ' not in sl['code']:
                        s.flownames.setdefault(sl['code'], sl['title'])

    def title(s, code):
        return (s.names.get(code) or s.genames.get(code) or s.flownames.get(code) or 'Special Topics')[:34]

    # ---- the quarter number a class had, and whether the app's crosswalk knows it ----
    def qcode(s, sem):
        if sem in s.rev: return s.rev[sem], True
        if sem in s.synth: return s.synth[sem], False
        subj, num = sem.split(' ', 1)
        n = ''.join(ch for ch in num if ch.isdigit())
        suf = num[len(n):]
        if len(n) == 4:   # an invented quarter number — never one the crosswalk already uses for another class
            for cand in (n[0] + n[2:], n[0] + n[1] + n[3], n[0] + str((int(n[2:]) + 50) % 100).zfill(2), n[0] + str((int(n[2:]) + 77) % 100).zfill(2)):
                qc = f"{subj} {cand}{suf}"
                if qc not in s.D['equiv'] and qc not in s.synth_used: s.synth[sem] = qc; s.synth_used.add(qc); return qc, False
        return sem, False
        if False: return f"{subj} {n[0]}{n[2:]}{suf}", False
        return sem, False

    def subj_of(s, m):
        n = {}
        for t in m['terms']:
            for sl in t['slots']:
                if sl.get('type') == 'course' and sl.get('code'):
                    sj = sl['code'].split()[0]; n[sj] = n.get(sj, 0) + 1
        return max(n, key=lambda k: (n[k], k)) if n else 'GEN'

    def norm(s, code):
        if not code or '/' not in code.split(' ')[0]: return code
        subj, rest = code.split(' ', 1)
        return subj.split('/')[-1] + ' ' + rest

    def make(s, i):
        rng = random.Random(s.seed * 1000 + i)
        return Student(s, rng, i).build()

class Student:
    def __init__(s, g, rng, i):
        s.g, s.r, s.i = g, rng, i
        s.sc = []          # scenario tags
        s.hist = []        # Course History rows: dict(code, cur, term, year, title, grade, units, icon, xfer, open, now)
        s.lines = []       # requirement lines, in print order (see add_line)
        s.code_n = {}      # per-requirement line counters
        s.r2 = random.Random(g.seed * 1000 + i + 7000000)   # the 2026-10-12 additions draw from here
        s.nowy = 2026      # the Fall the report is printed in (or the January after)
        s.extra = []       # a minor / a second major: dict(kind, name, codes)

    # ---------------------------------------------------------------- who and when
    def pick_profile(s):
        r, g, i = s.r, s.g, s.i
        keys = sorted(g.flow.keys())
        if i % 25 == 24:
            s.nf = NOFLOW[(i // 25) % len(NOFLOW)]; s.major = s.nf[0]; s.mkey = None; s.msubj = s.nf[1]; s.abbr = s.nf[2]; s.sc.append('no-flowchart major')
            # a major TermChamp has no flowchart for: its own classes (invented numbers in its subject) and GE, year by year
            sj = s.msubj; terms = []
            for y in range(1, 5):
                for tw in ('Fall', 'Spring'):
                    sl = [dict(id=f'n{y}{tw}{k}', code=f"{sj} {y}{1 if tw == 'Fall' else 2}{k}{k + 1}", title=f"{sj} Studies {y}{k}", units=3, type='course') for k in range(2)]
                    sl += [dict(id=f'g{y}{tw}{k}', title='GE', units=3, type='ge') for k in range(2)]
                    terms.append(dict(year=y, term=tw, slots=sl))
            s.m = dict(name=s.major, terms=terms)
        else:
            s.nf = None; s.mkey = keys[(i * 7) % len(keys)] if i < 2 * len(keys) else r.choice(keys)
            s.m = g.flow[s.mkey]; s.major = s.m['name']; s.msubj = g.subj_of(s.m); s.abbr = s.msubj
        # catalog: quarter 2022–25 (older layout), semester 2026, or a quarter student who moved to the semester catalog
        k = r.random()
        if k < 0.42: s.cat = 'Q'; s.catyear = r.choice([2022, 2023, 2023, 2024, 2024, 2025])
        elif k < 0.90: s.cat = 'S'; s.catyear = 2026
        else: s.cat = 'SW'; s.catyear = 2026; s.sc.append('switched to the semester catalog')
        s.layout = 'old' if s.cat == 'Q' else 'new'
        s.jan = r.random() < 0.15
        if s.jan: s.sc.append('printed in January (Fall graded, Spring registered)')
        # (2026-10-12) a semester-catalog student past the first term: printed a year or two later
        if s.cat == 'S' and s.r2.random() < 0.35:
            s.nowy = 2027 if s.r2.random() < 0.7 else 2028
            s.sc.append('semester catalog, past the first term (printed %s %d)' % ('January' if s.jan else 'October', s.nowy + (1 if s.jan else 0)))
        # who they are: first-year … fifth-year, transfer
        if s.cat == 'Q': s.entry = r.choice([y for y in range(2022, 2026) if y >= s.catyear - 0] or [s.catyear])
        elif s.cat == 'SW': s.entry = r.choice([2023, 2024, 2025])
        else: s.entry = 2026
        s.entry = max(s.entry, s.catyear) if s.cat == 'Q' else s.entry
        s.xfer = None
        t = r.random()
        if s.cat == 'S' and t < 0.30: s.xfer = 'new'; s.sc.append('community-college transfer, first term')
        elif s.cat == 'Q' and t < 0.18: s.xfer = 'cont'; s.sc.append('community-college transfer, continuing')
        s.ap = r.random() < 0.25 and not s.xfer
        if s.ap: s.sc.append('AP / exam credit')
        s.abroad = r.random() < 0.12 and s.cat != 'S'
        if s.abroad: s.sc.append('study abroad')
        s.fail = r.choice(['retake', 'open', 'w', 'dmin', 'nc', 'repeat', None, None, None, None]) if (s.cat != 'S' or s.jan or s.nowy > 2026) else r.choice(['w', None, None])
        if s.fail: s.sc.append({'retake': 'an F then a retake', 'open': 'an F never retaken', 'w': 'a W', 'dmin': 'a D where C- is required', 'nc': 'NC on a credit/no-credit class', 'repeat': 'a repeated class (both passing)'}[s.fail])
        s.late = r.random() < 0.12
        s.icons = r.random() > 0.03
        if not s.icons: s.sc.append('a copy whose icons were lost')
        s.dup = r.random() < 0.05
        if s.dup: s.sc.append('a registrar duplicate row')
        s.unknown = r.random() < 0.04 and s.layout == 'old'
        if s.unknown: s.sc.append('a verdict the reader can’t place')
        s.breakwrap = s.layout == 'old' and r.random() < 0.25
        s.splitcode = s.layout == 'old' and r.random() < 0.08
        if s.splitcode: s.sc.append('a requirement code split across two lines')
        s.behind = r.random() < 0.2
        if s.behind: s.sc.append('behind the flowchart (some classes not yet taken)')
        first, last = FIRST[(s.i * 5) % len(FIRST)], LAST[(s.i * 3) % len(LAST)]
        s.who = f"{first} {last}{s.i:03d}"; s.emplid = str(9800000 + s.i * 37)

    def terms(s):
        """the terms the report covers, oldest first: (year, word) — and which is being taken now"""
        T = []
        y = s.entry
        while y < 2026:   # quarters
            T += [(y, 'Fall'), (y + 1, 'Wtr'), (y + 1, 'Spr')]; y += 1
        for yy in range(max(s.entry, 2026), s.nowy):   # (2026-10-12) semesters before the one printed in
            T += [(yy, 'Fall'), (yy + 1, 'Spr')]
        cur = [(s.nowy, 'Fall')]
        if s.jan: cur = [(s.nowy, 'Fall'), (s.nowy + 1, 'Spr')]
        return T, cur

    # ---------------------------------------------------------------- the classes
    def build(s):
        s.pick_profile()
        past, cur = s.terms()
        s.past, s.cur = past, cur
        s.now_term = cur[-1]                    # the term being taken
        graded_cur = cur[:-1]                   # January: Fall 2026 is graded
        g, r = s.g, s.r
        # years done before now, by academic year
        yrs = sorted(set(y if w == 'Fall' else y - 1 for y, w in past))
        if s.xfer == 'new': yrs_done = 2 + len(yrs)   # transferred in as a junior: two years' worth by transfer credit
        elif s.xfer == 'cont': yrs_done = len(yrs) + 2
        else: yrs_done = len(yrs)
        s.yrs_done = yrs_done
        s.standing = ['Freshman', 'Sophomore', 'Junior', 'Senior', 'Senior', 'Senior'][min(yrs_done + (1 if s.jan else 0), 5)]
        s.taken = {}   # semester code -> list of attempts dict(term, code_as_printed, grade, units, xfer, open)
        s.ge_fill = {} # semester GE area -> semester code
        s.qge_fill = {}
        flow_terms = s.m['terms']
        slots_by_year = {}
        for t in flow_terms:
            slots_by_year.setdefault(t['year'], []).extend(t['slots'])
        s.slots = [sl for t in flow_terms for sl in t['slots']]
        # walk year by year
        acad = []   # (year index from 1, [terms])
        for k in range(yrs_done):
            acad.append(k + 1)
        def term_for(k, j, n):
            """the j-th of n classes in academic year k (1-based): the term it was taken in"""
            if s.xfer == 'new' and k <= 2: return (2026, 'Fall'), 'cc'
            if s.xfer == 'cont' and k <= 2: return (s.entry, 'Fall'), 'cc'
            yk = k - (2 if s.xfer in ('cont', 'new') else 0)
            ys = sorted(set(y if w == 'Fall' else y - 1 for y, w in past))
            if yk - 1 < len(ys):
                y0 = ys[yk - 1]
                opts = [t for t in past if (t[0] == y0 and t[1] == 'Fall') or (t[0] == y0 + 1 and t[1] in ('Wtr', 'Spr'))]
                if opts: return opts[j % len(opts)], 'cp'
            return s.cur[0], 'cp'
        # LD GE areas to fill in order for generic GE slots
        lower = ['1A', '1B', '1C', '2', '3A', '3B', '4A', '4B', '5A', '5B', '5C', '6']
        upper = ['U25', 'UD3', 'UD4']
        s.elect_pool = [c for c in sorted(g.names) if c.split()[0] == s.msubj and not any(c == (sl.get('code') or '') for sl in s.slots)]
        s.conc = None; s.conc_classes = []
        if s.mkey and s.major in g.D['conc'] and r.random() < 0.85:
            s.conc = r.choice(sorted(g.D['conc'][s.major])); s.conc_classes = [c for c in g.D['conc'][s.major][s.conc] if c][:4]
            s.sc.append('concentration')
        ci = 0
        s.assign = []   # (slot, code or None) for every flowchart slot: what fills it
        for y in range(1, 9):
            ys = slots_by_year.get(y, [])
            for j, sl in enumerate(ys):
                when = None
                if y <= yrs_done:
                    if s.behind and r.random() < 0.12: when = None
                    else: when = 'past'
                elif y == yrs_done + 1:
                    # this year's first term's slots are being taken now; January: Fall done, Spring now
                    fall_slots = [x for t in flow_terms if t['year'] == y and t['term'] == 'Fall' for x in t['slots']]
                    if sl in fall_slots: when = 'graded-cur' if s.jan else 'now'
                    elif s.jan: when = 'now'
                if not when: s.assign.append((sl, None, None, None)); continue
                code = None
                if sl['type'] == 'course' and sl.get('code'): code = sl['code']
                elif sl['type'] == 'choice' and sl.get('options'):
                    code = r.choice(sl['options'])
                    if not __import__('re').match(r'^[A-Z]{2,5} \d{3,4}', code): code = None
                elif sl['type'] == 'ge':
                    area = None
                    t = sl.get('title', '')
                    for a in lower + upper:
                        if t.endswith('Area ' + a) or t.endswith(' ' + a): area = a; break
                    if not area or area in s.ge_fill:
                        pool = (upper if y >= 3 else lower) + (lower if y >= 3 else upper)
                        area = next((a for a in pool if a not in s.ge_fill), None)
                    if area:
                        cands = [x['code'] for x in g.ge.get(area, [])]
                        if s.cat != 'S' or s.xfer: cands = [c for c in cands if c in g.rev] or cands
                        code = r.choice(sorted(set(cands))) if cands else None
                        if code: s.ge_fill[area] = code
                elif sl['type'] == 'concentration':
                    if ci < len(s.conc_classes): code = s.conc_classes[ci]; ci += 1
                    elif s.elect_pool: code = r.choice(s.elect_pool)
                elif sl['type'] == 'elective':
                    if s.elect_pool: code = r.choice(s.elect_pool)
                if not code: s.assign.append((sl, None, None, None)); continue
                if when == 'now': tm, src = s.now_term, 'cp'
                elif when == 'graded-cur': tm, src = s.cur[0], 'cp'
                else: tm, src = term_for(y, j, len(ys))
                s.assign.append((sl, code, tm, src))
        # 5C lab: verified by a 5A/5B class with a lab (the same class row)
        # ---- attempts: one per assigned class (a class "& lab" is two rows) ----
        for sl, code, tm, src in s.assign:
            if not code: continue
            for c in [x.strip() for x in code.replace(' & ', '&').split('&')]:
                if not c: continue
                if not c[0].isalpha():   # "1120L" after "&": the subject of the first
                    c = code.split()[0] + ' ' + c
                s.attempt(c, tm, src, now=(tm == s.now_term))
        # extra transfer GE credit for new transfers: the lower-division GE they came with
        if s.xfer:
            tm = (2026, 'Fall') if s.xfer == 'new' else (s.entry, 'Fall')
            for a in lower:
                if a in s.ge_fill: continue
                cands = sorted(set(x['code'] for x in g.ge.get(a, [])))
                if not cands: continue
                c = r.choice(cands); s.ge_fill[a] = c; s.attempt(c, tm, 'cc')
            if r.random() < 0.6:   # articulation placeholders: a CC class with no Cal Poly number
                ph = r.choice([('BUS', '1TR', 'Bus Transfer Lower Division'), ('CSC', '1TR', 'CSC Transfer Lower Division'), ('PSY', '1T4B', 'GE4B PSY Xfer'), ('MU', '1T3A', 'GE3A MU Xfer')])
                s.hist.append(dict(code=ph[0] + ' ' + ph[1], cur=ph[0] + ' ' + ph[1], term=tm, title=ph[2], grade=r.choice(GRADES), units=3.0 if s.cat != 'Q' else 4.0, icon=X, xfer=True, open=False, unused=True))
        if s.ap:
            tm = s.past[0] if s.past else s.now_term
            for a in r.sample(['1A', '2', '4B', '3B', '5A'], 2):
                if a in s.ge_fill: continue
                cands = sorted(set(x['code'] for x in g.ge.get(a, [])))
                if not cands: continue
                c = r.choice(cands); s.ge_fill[a] = c
                s.attempt(c, tm, 'ap')
        if s.abroad and s.past:
            tm = s.past[-1] if s.past[-1][1] != 'Sum' else s.past[-2]
            s.hist.append(dict(code='TRAN 302', cur='TRAN 302', term=tm, title='Study Abroad', grade='333', units=12.0, icon=X, xfer=True, open=False, unused=True))
            a = next((a for a in ['3A', '3B', '4B'] if a not in s.ge_fill), None)
            if a:
                ph = {'3A': ('ART', '3TC1', 'Arts Transfer'), '3B': ('PORT', '1TC2', 'Portuguese Transfer'), '4B': ('DUD', '3TR', 'Social Science Transfer')}[a]
                s.hist.append(dict(code=ph[0] + ' ' + ph[1], cur=ph[0] + ' ' + ph[1], term=tm, title=ph[2], grade=r.choice(GRADES), units=4.0, icon=X, xfer=True, open=False, area=a))
                s.ge_fill[a] = ph[0] + ' ' + ph[1]
        # ---- (2026-10-12) a class taken in a Summer term ----
        if s.r2.random() < 0.15:
            cands = [h for h in s.hist if h.get('src') == 'cp' and not h['open'] and h['term'] in s.past and h['term'][1] != 'Sum']
            if cands:
                h = s.r2.choice(cands); y0 = h['term'][0] if h['term'][1] == 'Fall' else h['term'][0] - 1
                if (y0 + 1, 3) < (s.cur[0][0], 4): h['term'] = (y0 + 1, 'Sum'); s.sc.append('a Summer term')
        # ---- (2026-10-12) a minor, and a second major: their own sections, real classes from another flowchart ----
        if s.mkey:
            for kind, p, n in (('minor', 0.10, 4), ('second', 0.05, 6)):
                if s.r2.random() >= p: continue
                k2 = s.r2.choice([k for k in sorted(g.flow) if k != s.mkey and g.flow[k]['name'] != s.major])
                have = s.slot_codes() | set(h['cur'] for h in s.hist) | set(c for e in s.extra for c in e['codes'])
                cs = []
                for t in g.flow[k2]['terms']:
                    for sl in t['slots']:
                        c = sl.get('code') or ''
                        if sl.get('type') == 'course' and __import__('re').match(r'^[A-Z]{2,5} \d{4}$', c) and c not in have and c not in cs: cs.append(c)
                cs = cs[:n]
                if len(cs) < 2: continue
                s.extra.append(dict(kind=kind, name=g.flow[k2]['name'], codes=cs))
                s.sc.append('a minor' if kind == 'minor' else 'a second major')
                for c in cs:
                    x = s.r2.random()
                    if s.past and x < 0.5: s.attempt(c, s.r2.choice(s.past), 'cp')
                    elif x < 0.7: s.attempt(c, s.now_term, 'cp', now=True)
        # ---- failures, on a finished Cal Poly major class ----
        s.failed_only = []
        fin = [h for h in s.hist if not h['open'] and not h['xfer'] and h.get('src') == 'cp' and h['cur'] in s.slot_codes()]
        if s.fail and fin:
            h = r.choice(fin)
            if s.fail in ('retake', 'w', 'repeat'):
                bad = dict(h); bad['grade'] = {'retake': 'F', 'w': 'W', 'repeat': 'C-'}[s.fail]
                bad['term'] = s.prev_term(h['term']) or h['term']
                if bad['term'] == h['term']:   # nothing earlier: retake it later instead
                    h2 = dict(h); h2['term'] = s.next_term(h['term']); h['grade'] = bad['grade']
                    if h2['term'] == s.now_term: h2.update(grade='', icon=IP, open=True, now=True)   # retaking it now: no grade yet
                    s.hist.append(h2)
                else: s.hist.append(bad)
                if s.fail == 'repeat': s.sc.append('(the later attempt counts)')
            elif s.fail in ('open', 'nc'):
                h['grade'] = 'F' if s.fail == 'open' else 'NC'; h['failed'] = True; s.failed_only.append(h['cur'])
            elif s.fail == 'dmin':
                h['grade'] = 'D'; h['dmin'] = True
        # (2026-10-12) an Incomplete: "I" on a class in a finished term — not passed (yet), so not a class taken
        if s.r2.random() < 0.07:
            fin2 = [h for h in s.hist if not h['open'] and not h['xfer'] and h.get('src') == 'cp' and h['cur'] in s.slot_codes() and h['term'] in s.past + s.cur[:-1]
                    and h['grade'] in GRADES and not h.get('failed') and not h.get('dmin') and sum(1 for x in s.hist if x['cur'] == h['cur']) == 1]
            if fin2:
                h = s.r2.choice(fin2); h['grade'] = 'I'; h['failed'] = True; s.failed_only.append(h['cur']); s.sc.append('an Incomplete (I)')
        # a major class that is also a GE class counts for that area too (the catalog's "double count"), as the registrar does
        for h in list(s.hist):
            for a in [ar for ar, lst in g.ge.items() if any(x['code'] == h['cur'] for x in lst)]:
                if a not in s.ge_fill: s.ge_fill[a] = h['cur']
        if s.dup and s.hist:
            d = dict(r.choice([h for h in s.hist if not h['open']] or s.hist)); d['dup'] = True; s.hist.append(d)
        return s.finish()

    def slot_codes(s):
        out = set()
        for sl, code, tm, src in s.assign:
            if code:
                for c in [x.strip() for x in code.replace(' & ', '&').split('&')]:
                    out.add(c if c[:1].isalpha() else code.split()[0] + ' ' + c)
        return out

    def prev_term(s, tm):
        allt = sorted(set([h['term'] for h in s.hist] + s.past), key=lambda t: (t[0], ORD[t[1]]))
        allt = [t for t in s.past]
        i = allt.index(tm) if tm in allt else -1
        return allt[i - 1] if i > 0 else None

    def next_term(s, tm):
        allt = s.past + s.cur
        i = allt.index(tm) if tm in allt else -1
        return allt[i + 1] if 0 <= i < len(allt) - 1 else s.now_term

    def attempt(s, sem, tm, src, now=False):
        """one row of the Course History for the semester class `sem`, taken in term `tm`"""
        g, r = s.g, s.r
        now = now and src == 'cp'   # transfer and exam credit is posted, never "being taken"
        if any(h['cur'] == sem for h in s.hist): return   # one class, one record (a slot that repeats a class, or AP for a class already taken)
        quarter_era = (tm[0], ORD[tm[1]]) < (2026, 4) and src != 'cc' or (src == 'cc' and s.cat == 'Q')
        if src == 'cc' and s.xfer == 'new': quarter_era = False
        if src == 'ap' and s.cat == 'S' and not s.past: quarter_era = False
        if quarter_era and sem.endswith('L') and sem[-2:-1].isdigit(): return   # a semester lab: the quarter class covered it
        code, known = (g.qcode(sem) if quarter_era else (sem, True))
        if quarter_era and s.cat == 'SW' and not known:   # printed bare on a semester report: only what the crosswalk knows
            return
        units = None
        su = 3.0
        for sl in s.slots:
            if sl.get('code') == sem: su = float(sl.get('units') or 3); break
        if quarter_era: units = 4.0 if su >= 3 else su
        else: units = su
        printed_units = units
        if s.cat == 'Q' and not quarter_era: printed_units = round(units * 1.5, 2)        # semester class on a quarter report
        if s.cat == 'SW' and quarter_era: printed_units = round(units * 2 / 3, 2)         # quarter class on a semester report
        grade = '' if now else r.choice(GRADES)
        icon = IP if now else OK
        xfer = False
        if src == 'cc': icon = X; xfer = True
        if src == 'ap': grade = r.choice(['300', '400', '500']); icon = X; xfer = True
        if s.unicode_cr(src): grade = 'CR'
        s.hist.append(dict(code=code, cur=sem, term=tm, title=g.title(sem), grade=grade, units=printed_units, icon=icon, xfer=xfer, open=now, now=now,
                           src=src, pair=(quarter_era and s.cat == 'Q' and code != sem), qera=quarter_era))

    def unicode_cr(s, src): return False

    # ---------------------------------------------------------------- the report's lines and the key
    def finish(s):
        g, r = s.g, s.r
        # the class that counts for a semester code: a passing attempt, else one being taken
        def best(sem):
            atts = [h for h in s.hist if h['cur'] == sem and not h.get('dup')]
            ok = [h for h in atts if not h['open'] and h['grade'] not in ('F', 'NC', 'W', 'D', 'I') ]
            if ok: return sorted(ok, key=lambda h: (h['term'][0], ORD[h['term'][1]]))[-1], 'done'
            nw = [h for h in atts if h['open']]
            if nw: return nw[0], 'taking'
            return None, 'need'
        s.best = best
        L = s.lines
        q = s.cat == 'Q'
        total_req = 180.0 if q else 120.0
        used_units = sum(h['units'] for h in s.hist if not h['open'] and not h.get('dup') and h['grade'] not in ('F', 'NC', 'W', 'I'))
        used_units = round(min(used_units, total_req if r.random() < 0.5 else 999), 2)
        s.units = [used_units, round(max(0.0, total_req - used_units), 2), total_req]
        st = 'done' if used_units >= total_req else 'need'
        L.append(dict(sec='deg', kind='units', key='total', status=st, words="TOTAL UNITS FOR THE DEGREE ('Taken' units cap at minimum required) - %d Required" % total_req if q else 'TOTAL UNITS: MINIMUM UNIT DEGREE REQUIREMENT',
                      units=(total_req, used_units, max(0, total_req - used_units))))
        # writing requirement and USCP
        senior = s.yrs_done >= 3
        L.append(dict(sec='deg', kind='gwr', key='gwr', status='done' if senior and r.random() < 0.6 else 'need', words='GRADUATION WRITING REQUIREMENT: - Satisfactory Completion Required' if q else 'GRADUATION WRITING (GWR): CONFIRMATION OF REQUIREMENT COMPLETION'))
        f6 = s.ge_fill.get('6')
        us = [h for h in s.hist if h['cur'] == f6 and not h['open'] and h['grade'] not in ('F', 'NC', 'W', 'I')] if f6 else []
        L.append(dict(sec='deg', kind='uscp', key='uscp', status='done' if us else 'need', used=us[:1], words='U.S. CULTURAL PLURALISM COURSE - 1 Course Required' if q else 'U.S. CULTURAL PLURALISM (USCP): ONE COURSE MINIMUM REQUIREMENT'))
        # GE
        if q:
            for qa, sa, name, code in QGE:
                if qa == 'E':
                    c = s.ge_fill.get('E'); h, stt = (best(c) if c else (None, 'need'))
                else:
                    c = s.ge_fill.get(sa)
                    if sa == '5C': c = s.ge_fill.get('5C') or s.ge_fill.get('5A') or s.ge_fill.get('5B')
                    h, stt = best(c) if c else (None, 'need')
                    if c is None:
                        ph = [x for x in s.hist if x.get('area') == sa]
                        if ph: h, stt = ph[0], 'done'
                L.append(dict(sec='ge', kind='ge', key='ge-' + qa, qa=qa, status=stt, used=[h] if h else [], name=name, code=code, minc=qa in ('A1', 'A2', 'A3', 'B4')))
            L.append(dict(sec='ge', kind='ge', key='ge-cel', status='need', used=[], name='LOWER-DIVISION C ELECTIVE', code='R72-30'))
            for k in (1, 2):
                L.append(dict(sec='ge', kind='ge', key='ge-el%d' % k, status='need', used=[], name='GE ELECTIVE: AREAS B, C, AND D', code='R76-%d0' % k))
        else:
            for a, name, code, parent, phead in SGE:
                c = s.ge_fill.get(a)
                h, stt = best(c) if c else (None, 'need')
                if c is None:
                    ph = [x for x in s.hist if x.get('area') == a]
                    if ph: h, stt = ph[0], 'done'
                L.append(dict(sec='ge', kind='ge', key='ge-' + a, area=a, status=stt, used=[h] if h else [], name=name, code=code, parent=parent, phead=phead, minc=a in ('1A', '1B', '1C', '2')))
        # a D where C- is required: on a GE line with a minimum, if one is a D (else on the major line, see below)
        # major / support / concentration lines, one per flowchart slot
        seen = set()
        for sl, code, tm, src in s.assign:
            t = sl.get('type')
            if t == 'ge': continue
            if t == 'course' and sl.get('code'):
                key = 'm-' + sl['code']
                if key in seen: continue
                seen.add(key)
                parts = [x.strip() for x in sl['code'].replace(' & ', '&').split('&')]
                parts = [p if p[:1].isalpha() else sl['code'].split()[0] + ' ' + p for p in parts]
                if q and len(parts) > 1: parts = [p for p in parts if not p.endswith('L')] or parts[:1]
                res = [best(p) for p in parts]
                stt = 'done' if all(x[1] == 'done' for x in res) else ('taking' if all(x[1] in ('done', 'taking') for x in res) else 'need')
                L.append(dict(sec='major', kind='major', key=key, codes=parts, status=stt, used=[x[0] for x in res if x[0]], units=float(sl.get('units') or 3)))
            elif t == 'choice' and sl.get('options') and all(__import__('re').match(r'^[A-Z]{2,5} \d{3,4}', o) for o in sl['options']):
                key = 'c-' + '|'.join(sl['options'])
                if key in seen: continue
                seen.add(key)
                res = {o: best(o) for o in sl['options']}
                stt = 'done' if any(v[1] == 'done' for v in res.values()) else ('taking' if any(v[1] == 'taking' for v in res.values()) else 'need')
                L.append(dict(sec='major', kind='choice', key=key, codes=sl['options'], title=sl.get('title', ''), status=stt, opts=res, units=float(sl.get('units') or 3),
                              used=[v[0] for v in res.values() if v[0] and v[1] != 'need']))
        # concentration and electives: by units
        for kind, label in (('conc', (s.conc or '') + ' CONCENTRATION ELECTIVES'), ('elective', 'APPROVED MAJOR ELECTIVES')):
            sls = [(sl, code) for sl, code, tm, src in s.assign if sl.get('type') == ('concentration' if kind == 'conc' else 'elective')]
            if not sls or (kind == 'conc' and not s.conc): continue
            need = sum(float(sl.get('units') or 3) for sl, c in sls)
            cls = []
            for sl, c in sls:
                if c:
                    h, stt = best(c)
                    if h and h not in cls: cls.append(h)
            done_u = sum((h['units'] if not h['qera'] else h['units'] * 0.75) for h in cls if not h['open'])
            tak_u = sum(h['units'] for h in cls if h['open'])
            stt = 'done' if done_u >= need - 0.01 else ('taking' if done_u + tak_u >= need - 0.01 and tak_u > 0 else 'need')
            if q: need_p = round(need * 4 / 3); scale = 1
            L.append(dict(sec='conc' if kind == 'conc' else 'major', kind=kind, key=kind, label=label, status=stt, used=cls, need=need))
        # (2026-10-12) a minor / a second major: one line per class
        for e in s.extra:
            for c in e['codes']:
                h, stt = best(c)
                L.append(dict(sec=e['kind'], kind='major', key=e['kind'] + '-' + c, codes=[c], status=stt, used=[h] if h else [], units=3.0))
        # failures that land on a line: the line is open, the class listed on the Course History
        for b in L:
            for h in b.get('used', []) or []:
                if h and h.get('dmin'):
                    b['status'] = 'need'; b['dminc'] = h['cur']
        for b in L:
            b['used'] = [h for h in (b.get('used') or []) if h and not h.get('dmin') and not h.get('failed')]
            if b['status'] == 'done' and not b['used'] and b['kind'] not in ('units', 'gwr'): b['status'] = 'need'
        # a class the registrar hasn't attached yet: a major line whose class is being taken prints Not Satisfied, bare
        if s.late:
            cand = [b for b in L if b['kind'] == 'major' and b['status'] == 'taking' and len(b.get('codes', [])) == 1]
            if cand:
                b = r.choice(cand); b['late'] = True; s.sc.append('a class the registrar hasn’t attached yet')
        # the unreadable verdict
        if s.unknown:
            L.append(dict(sec='deg', kind='unknown', key='unknown', status='unknown', used=[]))
        return s

# ------------------------------------------------------------------------------------------------- drawing
def term_label(tm): return f"{tm[0]} {tm[1]}"

def nbr(h):
    subj, num = h['code'].split(' ', 1)
    if h.get('pair'): return subj, f"{num} ({h['cur'].split(' ', 1)[1]})"
    return subj, num

def urow(h, desig=''):
    subj, n = nbr(h)
    return (term_label(h['term']), subj, n, h['title'], h['grade'], u2(h['units']), desig, h['icon'])

def draw(st, path):
    s = st; g = s.g; r = random.Random(s.i * 7919 + 1)
    q = s.cat == 'Q'
    obj = f"{s.abbr} Primary B{'S' if r.random() < 0.8 else 'A'} UG Major"
    catalog = (f"Fall Quarter {s.catyear}" if q else f"Fall Semester {s.catyear}")
    printed = "January 12, %d 08:%02d" % (s.nowy + 1, s.i % 60) if s.jan else "October 9, %d %02d:%02d" % (s.nowy, 8 + s.i % 10, s.i % 60)
    R = OldReport(s.who, s.emplid, printed, obj, catalog, icons=s.icons) if q else Report(s.who, s.emplid, printed, obj, catalog, icons=s.icons)
    if s.conc:
        R.y -= 4; R.text(f"{s.conc} Concentration", 54, bold=True); R.text(catalog, 465, bold=True); R.y -= 20
    codes = {}
    L = s.lines
    vcache = {}
    def vstat(b):
        """the verdict the registrar prints for a line (decided once per line)"""
        if id(b) in vcache: return vcache[id(b)]
        stt = b['status']
        if stt == 'done': v = 'S'
        elif stt == 'taking': v = 'N' if b.get('late') else (r.choice(['N', 'IP', 'S']) if q else r.choice(['S', 'N', 'S']))
        else: v = 'N'
        vcache[id(b)] = v; return v
    def rq(vs):   # a requirement over lines: Satisfied only when every line printed Satisfied
        return 'S' if vs and all(v == 'S' for v in vs) else 'N'
    def rows_for(b):
        if b.get('late'): return []
        return [urow(h, (b.get('qa') or b.get('area') or '').replace(' ', '') if b['kind'] == 'ge' else '') for h in b.get('used', [])]
    def emit_key(code, b, v):
        codes[code] = dict(key=b['key'], kind=b['kind'], truth=b['status'], read=('need' if b.get('late') else b['status']), late=bool(b.get('late')), printed=v,
                           used=[dict(c=h['code'], t=TW[h['term'][1]] + ' ' + str(h['term'][0]), n=h['cur'] if h['cur'] != h['code'] else None, x=bool(h['xfer']), p=bool(h['open'])) for h in ([] if b.get('late') else b.get('used', []))],
                           options=b.get('codes') or [], dminc=b.get('dminc'))
    def qword(c):
        qq, known = g.qcode(c)
        return f"{qq} ({c.split(' ', 1)[1]})" if qq != c else c
    deg = {b['kind']: b for b in L if b['sec'] == 'deg'}
    ge = [x for x in L if x['sec'] == 'ge']
    maj = [x for x in L if x['sec'] in ('major', 'conc')]
    if q:
        # ================= the older layout =================
        R.oldhead("GENERAL UNDERGRADUATE DEGREE REQUIREMENTS")
        R.old('ON', "***GENERAL UNDERGRADUATE DEGREE REQUIREMENTS 2022-2026 Catalog", "(RG-0005)***")
        b = deg['units']; v = vstat(b); tr, tu, tn = b['units']
        R.oldhead("TOTAL UNITS FOR THE DEGREE"); R.old(rq([v]), "TOTAL UNITS FOR THE DEGREE", "(R-0995)")
        R.old(v, b['words'], "(R995-10)", units=f"{tr:.2f} required, {tu:.2f} used" + (f", {tn:.2f} needed" if tn > 0 else '')); emit_key('R995-10', b, v)
        b = deg['gwr']; v = vstat(b)
        R.oldhead("GRADUATION WRITING REQUIREMENT"); R.old(rq([v]), "GRADUATION WRITING REQUIREMENT", "(R-0011)")
        R.old(v, b['words'], "(R11-10)"); emit_key('R11-10', b, v)
        b = deg['uscp']; v = vstat(b)
        R.oldhead("U.S. CULTURAL PLURALISM REQUIREMENT"); R.old(rq([v]), "U.S. CULTURAL PLURALISM REQUIREMENT", "(R-0015)")
        R.old(v, b['words'], "(R15-10)", courses=cnt(1, 1) if v == 'S' else cnt(1, 0, 1), used=rows_for(b)); emit_key('R15-10', b, v)
        if 'unknown' in deg:
            b = deg['unknown']; R.oldhead("ADDITIONAL REQUIREMENT"); R.old('N', "ADDITIONAL REQUIREMENT", "(R-0019)"); R.old('N', "", "(R19-10)"); emit_key('R19-10', b, 'N')
        R.oldhead("GENERAL EDUCATION REQUIREMENTS")
        R.old('ON', "***GENERAL EDUCATION REQUIREMENTS 2022-2026 Catalog - 72 Units Required. Refer to Major/Support section for", "(RG-0006)***", wrap="courses that satisfy/double count for GE.")
        areas = [('A', 'R-0070', 'GE AREA A: ENGLISH LANGUAGE COMMUNICATION AND CRITICAL THINKING - 12 Units Required', ['A1', 'A2', 'A3']),
                 ('B', 'R-0071', 'GE AREA B: SCIENTIFIC INQUIRY AND QUANTITATIVE REASONING - 20 Units Required', ['B1', 'B2', 'B3', 'B4', 'B UD']),
                 ('C', 'R-0072', 'GE AREA C: ARTS AND HUMANITIES - 16 Units Required', ['C1', 'C2', 'cel', 'C UD']),
                 ('D', 'R-0073', 'GE AREA D: SOCIAL SCIENCES - 12 Units Required', ['D1', 'D2', 'D UD']),
                 ('E', 'R-0074', 'GE AREA E: LIFELONG LEARNING AND SELF-DEVELOPMENT - 4 Units Required', ['E']),
                 ('F', 'R-0075', 'GE AREA F: ETHNIC STUDIES - 4 Units Required', ['F']),
                 ('EL', 'R-0076', 'GE ELECTIVES IN AREAS B, C, & D', ['el1', 'el2'])]
        bykey = {b['key']: b for b in ge}
        for letter, rcode, words, ks in areas:
            kids = [bykey['ge-' + k] for k in ks if 'ge-' + k in bykey]
            vs = [vstat(b) for b in kids]
            R.oldhead("GE AREA " + letter if letter != 'EL' else "GE ELECTIVES IN AREAS B, C, & D")
            if letter == 'EL' and s.breakwrap:
                R.old(rq(vs), words, f"({rcode})", wrap="(Note: Courses must come from 2 different GE Areas) - 8 Units Required", breakwrap=True)
            else:
                R.old(rq(vs), words, f"({rcode})")
            for b, v in zip(kids, vs):
                R.oldhead(b.get('qa') or b['name'].split(':')[0])
                label = (b['qa'] + ': ' if b.get('qa') else '') + b['name'] + (' (Note: Minimum grade of C- required)' if b.get('minc') else '') + ' - 4 Units Required'
                un = "4.00 required, 4.00 used" if b['status'] == 'done' else "4.00 required, 0.00 used, 4.00 needed"
                R.old(v, label, f"({b['code']})", units=un, used=rows_for(b), splitcode=(s.splitcode and b.get('qa') == 'C2'))
                emit_key(b['code'], b, v)
        R.oldhead("MAJOR COURSES")
        R.old('ON', f"{s.major.upper()} MAJOR COURSES", "(RG-0040)")
        n = 0; rqn = 40
        for b in maj:
            n += 1; v = vstat(b)
            code = f"R{60 if b['sec'] == 'conc' else 40}-{n * 10}"
            if b['kind'] == 'major':
                words = ' & '.join(qword(c) for c in b['codes'])
                each = (b.get('units') or 3.0) / max(1, len(b['codes']))
                k = int(sum(4 if each >= 3 else max(1, round(each * 4 / 3)) for c in b['codes']))
                R.oldhead(words.split(' (')[0])
                R.old(v, f"{words} - {k} Units Required", f"({code})", units=(f"{k}.00 required, {k}.00 used" if b['status'] == 'done' else f"{k}.00 required, 0.00 used, {k}.00 needed"), used=rows_for(b))
                emit_key(code, b, v)
            elif b['kind'] == 'choice':
                opts = [qword(c) for c in b['codes']]
                rqn += 1; rcode = f"R-{rqn:04d}"
                kv = []
                for c in b['codes']:
                    h, sk = b['opts'][c]
                    kv.append('S' if sk == 'done' else ('N' if sk == 'need' else r.choice(['S', 'N', 'IP'])))
                pv = 'S' if 'S' in kv else 'N'
                R.oldhead((b.get('title') or 'OPTION').upper())
                R.old(pv, f"{(b.get('title') or 'REQUIREMENT').upper()}: {' or '.join(opts)} in 1 of {len(opts)} Options", f"({rcode})")
                for k2, c in enumerate(b['codes']):
                    h, sk = b['opts'][c]
                    R.old(kv[k2], f"{opts[k2]} - 4 Units Required (Option {k2 + 1} of {len(opts)})", f"(R{rqn}-{(k2 + 1) * 10})",
                          units=("4.00 required, 4.00 used" if sk == 'done' else "4.00 required, 0.00 used, 4.00 needed"), used=[urow(h)] if h and sk != 'need' else None)
                emit_key(rcode, b, pv)
            else:
                need = b['need']; nq = round(need * 4 / 3)
                usedq = sum(h['units'] for h in b['used'] if not h['open'])
                R.oldhead(b['label'].strip())
                R.old(v, f"{b['label'].strip()} - {nq} Units Required", f"({code})",
                      units=(f"{nq:.2f} required, {max(usedq, nq):.2f} used" if b['status'] == 'done' else f"{nq:.2f} required, {usedq:.2f} used, {max(0, nq - usedq):.2f} needed"), used=rows_for(b))
                emit_key(code, b, v)
        for e in s.extra:   # (2026-10-12) a minor / a second major, each its own group
            mn = e['kind'] == 'minor'; ln = 89 if mn else 88
            label = f"{e['name'].upper()} MINOR" if mn else f"{e['name'].upper()} MAJOR COURSES (SECOND MAJOR)"
            R.oldhead(label); R.old('ON', label, f"(RG-00{ln})")
            for n2, b in enumerate([b for b in L if b['sec'] == e['kind']], 1):
                v = vstat(b); code = f"R{ln}-{n2 * 10}"; words = qword(b['codes'][0])
                R.oldhead(words.split(' (')[0])
                R.old(v, f"{words} - 4 Units Required", f"({code})", units=("4.00 required, 4.00 used" if b['status'] == 'done' else "4.00 required, 0.00 used, 4.00 needed"), used=rows_for(b))
                emit_key(code, b, v)
        unused = [h for h in s.hist if h.get('unused') or h['grade'] in ('W',)]
        if unused:
            R.oldhead("COURSE CREDITS NOT USED"); R.old('OS', "***COURSE CREDITS NOT USED", "(RG-0008)***")
            R.text("THE FOLLOWING COURSE CREDITS HAVE NOT BEEN USED TO MEET GE, MAJOR, CONCENTRATION, SUPPORT, OR MINOR", 36); R.y -= 10
            R.text("REQUIREMENTS. See your advisor if you believe any of these should satisfy unmet requirements.(R-0030)", 36); R.y -= 14
            R.table([urow(h) for h in unused])
    else:
        # ================= the 2026 layout =================
        R.head("UNDERGRADUATE DEGREE REQUIREMENTS", size=10); R.verdict('ON', f"{s.catyear}-Current Catalog", code="(RG5)")
        b = deg['units']; v = vstat(b); tr, tu, tn = b['units']
        R.head("TOTAL UNITS: DEGREE REQUIREMENT"); R.verdict(rq([v]), "(R995)")
        R.head(b['words'], 40); R.verdict(v, "120 units", more=["Excess units not counted. Maximum 70 units from community college."], code="(R995-10)", units=f"{tr:.2f} required, {tu:.2f} used" + (f", {tn:.2f} needed" if tn > 0 else ''))
        emit_key('R995-10', b, v)
        b = deg['uscp']; v = vstat(b)
        R.head("UNITED STATES CULTURAL PLURALISM (USCP): DEGREE REQUIREMENT"); R.verdict(rq([v]), 'See "Class Schedule" for a list of approved USCP courses.', code="(R15)")
        R.head(b['words'], 40); R.verdict(v, "(R15-10)", courses=cnt(1, 1) if v == 'S' else cnt(1, 0, 1), used=rows_for(b)); emit_key('R15-10', b, v)
        b = deg['gwr']; v = vstat(b)
        R.head("GRADUATION WRITING (GWR): DEGREE REQUIREMENT"); R.verdict(rq([v]), "(R11)")
        R.head(b['words'], 40); R.verdict(v, "NOTE: Requirement may not display as completed until one week after GWR course grade is posted.", code="(R11-10)"); emit_key('R11-10', b, v)
        R.head("GPA: HIGHER EDUCATION, RESIDENCE, AND MAJOR REQUIREMENTS (2026)"); R.verdict('S', 'Requirement may display as "in progress" after unit minimum is complete.', code="(R1108)")
        R.head("GPA: HIGHER EDUCATION CUMULATIVE 2.00 MINIMUM REQUIREMENT", 40); R.verdict('S', "(R1108-10)")
        codes['R1108-10'] = dict(key='gpa', kind='gpa', truth='done', read='done', late=False, printed='S', used=[], options=[], dminc=None)
        R.head("GENERAL EDUCATION REQUIREMENTS", size=10); R.verdict('ON', f"{s.catyear}-Current Catalog", more=["43 units required", "NOTE: Some Major/Support courses also satisfy GE."], code="(RG6)")
        groups = []
        for b in ge:
            if b.get('phead'): groups.append((b['parent'], b['phead'], [b]))
            else: groups[-1][2].append(b)
        for parent, phead, kids in groups:
            vs = [vstat(b) for b in kids]
            R.head(phead); R.verdict(rq(vs), "%d units required" % (3 * len(kids)), code=f"({parent})")
            for b, v in zip(kids, vs):
                ud = b['area'] in ('U25', 'UD3', 'UD4')
                R.head(("" if ud else b['area'] + ": ") + b['name'], 40)
                R.verdict(v, "NOTE: Minimum grade of C- required" if b.get('minc') else "NOTE: Junior Standing required" if ud else "3 units",
                          more=["3 units"] if (b.get('minc') or ud) else [], code=f"({b['code']})", courses=cnt(1, 1) if v == 'S' else cnt(1, 0, 1), used=rows_for(b))
                emit_key(b['code'], b, v)
        unused = [h for h in s.hist if h.get('unused')]
        if unused:
            R.head("FREE ELECTIVES & COURSES NOT COUNTED FOR DEGREE CREDIT", size=10); R.text("(RG8)", 40); R.y -= 14
            R.head("Course credits not used for GE, MAJOR, CONCENTRATION, SUPPORT, or MINOR."); R.text("(R30)", 40); R.y -= 14
            R.head("FREE ELECTIVES", 40); R.table([urow(h) for h in unused])
        R.head(f"{s.major.upper()} MAJOR B.S. ({s.catyear}-Current Catalog)", size=10); R.verdict('ON', "(RG229)")
        core = [b for b in maj if b['kind'] == 'major']
        if core:
            vs = [vstat(b) for b in core]
            R.head("MAJOR CORE COURSES (2026)"); R.verdict(rq(vs), "(R797)")
            for n, (b, v) in enumerate(zip(core, vs), 1):
                code = f"R797-{n * 10}"
                R.head(' & '.join(b['codes']), 40)
                R.verdict(v, "%d units" % int(b['units']), code=f"({code})", courses=cnt(len(b['codes']), len(b['codes'])) if v == 'S' else cnt(len(b['codes']), 0, len(b['codes'])), used=rows_for(b))
                emit_key(code, b, v)
        for n, b in enumerate([b for b in maj if b['kind'] == 'choice'], 1):
            rqn = 2800 + n
            kv = []
            for c in b['codes']:
                h, sk = b['opts'][c]
                kv.append('S' if sk == 'done' else ('N' if sk == 'need' else r.choice(['S', 'N'])))
            pv = 'S' if 'S' in kv else 'N'
            R.head(f"{(b.get('title') or 'MAJOR CORE COURSES').upper()} - OPTION (2026)"); R.verdict(pv, "Choose one", more=["3-4 units"], code=f"(R{rqn})")
            for k2, c in enumerate(b['codes']):
                h, sk = b['opts'][c]
                R.head(c, 40); R.verdict(kv[k2], f"Option {k2 + 1} of {len(b['codes'])}", more=["3 units"], code=f"(R{rqn}-{(k2 + 1) * 10})", courses=cnt(1, 1) if kv[k2] == 'S' else cnt(1, 0, 1), used=[urow(h)] if h and sk != 'need' else None)
            emit_key(f"R{rqn}", b, pv)
        for rcode, kind, title in (('R798', 'conc', f"{(s.conc or '').upper()} CONCENTRATION (2026)"), ('R799', 'elective', "MAJOR ELECTIVES (2026)")):
            bs = [b for b in maj if b['kind'] == kind]
            if not bs: continue
            vs = [vstat(b) for b in bs]
            R.head(title); R.verdict(rq(vs), "(%s)" % rcode)
            for n, (b, v) in enumerate(zip(bs, vs), 1):
                code = f"{rcode}-{n * 10}"
                need = b['need']; usedu = sum(h['units'] for h in b['used'] if not h['open'])
                R.head(b['label'].strip(), 40)
                R.verdict(v, "%d units" % int(need), code=f"({code})", units=(f"{need:.2f} required, {max(usedu, need):.2f} used" if b['status'] == 'done' else f"{need:.2f} required, {usedu:.2f} used, {max(0, need - usedu):.2f} needed"), used=rows_for(b))
                emit_key(code, b, v)
    if not q:
        for e in s.extra:   # (2026-10-12) a minor / a second major
            mn = e['kind'] == 'minor'; rg, rq_ = ('RG250', 'R850') if mn else ('RG231', 'R851')
            R.head(f"{e['name'].upper()} {'MINOR' if mn else 'MAJOR B.S.'} ({s.catyear}-Current Catalog)", size=10); R.verdict('ON', f"({rg})")
            bs = [b for b in L if b['sec'] == e['kind']]; vs = [vstat(b) for b in bs]
            R.head("MINOR REQUIRED COURSES (2026)" if mn else "MAJOR CORE COURSES (2026)"); R.verdict(rq(vs), f"({rq_})")
            for n2, (b, v) in enumerate(zip(bs, vs), 1):
                code = f"{rq_}-{n2 * 10}"
                R.head(b['codes'][0], 40)
                R.verdict(v, "3 units", code=f"({code})", courses=cnt(1, 1) if v == 'S' else cnt(1, 0, 1), used=rows_for(b))
                emit_key(code, b, v)
    # ---- the Course History ----
    rows = sorted(s.hist, key=lambda h: (h['term'][0], ORD[h['term'][1]], h['code']))
    R.history([(term_label(h['term']),) + nbr(h) + (h['title'], h['grade'], u2(h['units']), h['icon']) for h in rows])
    R.save(path)
    return codes

# ------------------------------------------------------------------------------------------------- the key
def key_for(s, codes):
    lines = codes
    def is_total(k): return lines[k]['kind'] == 'units'
    read = dict(filled=sum(1 for v in lines.values() if v['read'] in ('done', 'taking')), left=sum(1 for v in lines.values() if v['read'] == 'need'),
                unknown=sum(1 for v in lines.values() if v['read'] == 'unknown'))
    past_filled = sum(1 for v in lines.values() if v['truth'] in ('done', 'taking') and not (v['late'] and False))
    past_left = sum(1 for k, v in lines.items() if v['truth'] == 'need' and not is_total(k))
    seen = set(); hist = []
    for h in s.hist:
        k = (h['code'], h['term'])
        if k in seen: continue
        seen.add(k); hist.append(h)
    now = s.now_term
    taking = sorted(set(h['cur'] for h in hist if h['open'] and h['term'] == now and not h['xfer']))
    done = sorted(set(h['cur'] for h in hist if not h['open'] and h['grade'] not in ('F', 'NC', 'W', 'D', 'I') and not h['cur'].endswith(('TR', 'TC1', 'TC2')) and h['cur'] != 'TRAN 302'))
    failed_only = sorted(set(h['cur'] for h in hist if h['grade'] in ('F', 'NC', 'W', 'I')) - set(done) - set(taking))
    return dict(id='synth-%03d' % s.i, major=s.major, flowchart=bool(s.mkey), conc=s.conc, catalog=('Fall Quarter %d' % s.catyear if s.cat == 'Q' else 'Fall Semester %d' % s.catyear),
                kind=s.cat, layout=s.layout, standing=s.standing, scenarios=s.sc, icons=s.icons, clock=dict(nowy=s.nowy, jan=bool(s.jan)),
                read=dict(read, transfer=sum(1 for h in hist if h['xfer']), rows=len(hist), units=s.units, taking=taking),
                lines=lines, past=dict(filled=past_filled, total=len(lines), left=past_left),
                done=done, taking=taking, failed_only=failed_only,
                transfer=sorted(set(h['cur'] for h in hist if h['xfer'])),
                secret=[s.who, s.emplid])

def fixture(path):
    """dpr-corpus-found.pdf: one small report holding each thing the 300 found (check-app's dprCorpusFound) — invented person"""
    r = OldReport("Jesse Foundcase", "9811001", "October 9, 2026 10:05", "BUS Primary BS UG Major", "Fall Quarter 2023")
    r.oldhead("GENERAL UNDERGRADUATE DEGREE REQUIREMENTS"); r.old('ON', "***GENERAL UNDERGRADUATE DEGREE REQUIREMENTS 2022-2026 Catalog", "(RG-0005)***")
    r.oldhead("MAJOR COURSES"); r.old('ON', "BUSINESS ADMINISTRATION MAJOR COURSES", "(RG-0040)")
    r.oldhead("CPE 101 (1001)")   # a subject renamed at the conversion: the crosswalk says CSC 1001
    r.old('S', "CPE 101 (1001) - 4 Units Required", "(R40-10)", units="4.00 required, 4.00 used", used=[("2024 Wtr", "CPE", "101 (1001)", "Fundamentals of Computer Science", "B", "4.00", '', OK)])
    r.oldhead("LA 222 (2212)")    # the report's own pair, where TermChamp's crosswalk would say LA 2222
    r.old('S', "LA 222 (2212) - 4 Units Required", "(R40-20)", units="4.00 required, 4.00 used", used=[("2024 Fall", "LA", "222 (2212)", "Introduction to Planting Design", "A", "4.00", '', OK)])
    r.oldhead("TECHNOLOGY MANAGEMENT COURSE")   # "1 of 2 Options" …
    r.old('S', "TECHNOLOGY MANAGEMENT COURSE: BUS 401 (4401) or BUS 411 (4411) in 1 of 2 Options", "(R-0041)")
    r.old('S', "BUS 401 (4401) - 4 Units Required (Option 1 of 2)", "(R41-10)", units="4.00 required, 4.00 used", used=[("2025 Wtr", "BUS", "401 (4401)", "General Management", "A-", "4.00", '', OK)])
    r.old('N', "BUS 411 (4411) - 4 Units Required (Option 2 of 2)", "(R41-20)", units="4.00 required, 0.00 used, 4.00 needed")
    r.oldhead("BUS 207 (2207)")   # … then a major line of its own, open: an F, never retaken
    r.old('N', "BUS 207 (2207) - 4 Units Required", "(R40-95)", units="4.00 required, 0.00 used, 4.00 needed")
    r.oldhead("MATE 430 (4300)")  # being taken; its title cut short ends in a letter
    r.old('N', "MATE 430 (4300) - 4 Units Required", "(R40-96)", units="4.00 required, 0.00 used, 4.00 needed", used=[("2026 Fall", "MATE", "4300", "Materials Selection for the Life C", "", "4.50", '', IP)])
    r.history([("2024 Wtr", "CPE", "101 (1001)", "Fundamentals of Computer Science", "B", "4.00", OK), ("2024 Fall", "LA", "222 (2212)", "Introduction to Planting Design", "A", "4.00", OK),
               ("2025 Wtr", "BUS", "401 (4401)", "General Management", "A-", "4.00", OK), ("2025 Spr", "BUS", "207 (2207)", "Legal Environment of Business", "F", "4.00", OK),
               ("2025 Spr", "BUS", "212 (2212)", "Business Statistics", "W", "4.00", OK),
               ("2026 Fall", "MATE", "4300", "Materials Selection for the Life C", "", "4.50", IP), ("2026 Fall", "BUS", "3431", "Security Analysis", "", "4.50", IP)])
    r.save(path)

def fixture_more(path):
    """dpr-corpus-more.pdf (2026-10-12): a Summer term, a minor, an Incomplete, and a class being taken whose title ends in
    "I" (Cal Poly's plain icon) — check-app's dprCorpusMore. Invented person."""
    r = OldReport("Morgan Morecase", "9811002", "October 9, 2026 10:15", "BUS Primary BS UG Major", "Fall Quarter 2023")
    r.oldhead("GENERAL UNDERGRADUATE DEGREE REQUIREMENTS"); r.old('ON', "***GENERAL UNDERGRADUATE DEGREE REQUIREMENTS 2022-2026 Catalog", "(RG-0005)***")
    r.oldhead("MAJOR COURSES"); r.old('ON', "BUSINESS ADMINISTRATION MAJOR COURSES", "(RG-0040)")
    r.oldhead("BUS 214 (2214)")   # taken in a Summer term
    r.old('S', "BUS 214 (2214) - 4 Units Required", "(R40-10)", units="4.00 required, 4.00 used", used=[("2024 Sum", "BUS", "214 (2214)", "Legal Environment", "B+", "4.00", '', OK)])
    r.oldhead("BUS 391 (3391)")   # an Incomplete in Fall 2025: open, and the report lists nothing for it
    r.old('N', "BUS 391 (3391) - 4 Units Required", "(R40-20)", units="4.00 required, 0.00 used, 4.00 needed")
    r.oldhead("BUS 392 (3392)")   # being taken; its title ends in "I"; it wears Cal Poly's plain icon, not the in-progress one
    r.old('N', "BUS 392 (3392) - 4 Units Required", "(R40-30)", units="4.00 required, 0.00 used, 4.00 needed", used=[("2026 Fall", "BUS", "3392", "Career Readiness I", "", "4.50", '', OK)])
    r.oldhead("ECONOMICS MINOR"); r.old('ON', "ECONOMICS MINOR", "(RG-0089)")   # a minor: its own group of lines
    r.oldhead("ECON 201 (2201)")
    r.old('S', "ECON 201 (2201) - 4 Units Required", "(R89-10)", units="4.00 required, 4.00 used", used=[("2025 Spr", "ECON", "201 (2201)", "Survey of Economics", "A", "4.00", '', OK)])
    r.oldhead("ECON 311 (3311)")
    r.old('N', "ECON 311 (3311) - 4 Units Required", "(R89-20)", units="4.00 required, 0.00 used, 4.00 needed")
    r.history([("2024 Sum", "BUS", "214 (2214)", "Legal Environment", "B+", "4.00", OK), ("2025 Spr", "ECON", "201 (2201)", "Survey of Economics", "A", "4.00", OK),
               ("2025 Fall", "BUS", "391 (3391)", "Career Readiness II", "I", "4.00", OK),
               ("2026 Fall", "BUS", "3392", "Career Readiness I", "", "4.50", OK), ("2026 Fall", "BUS", "3431", "Security Analysis", "", "4.50", IP)])
    r.save(path)

def main():
    if sys.argv[1] == '--fixture': fixture(sys.argv[2]); print('make-dpr-corpus: fixture', sys.argv[2]); return
    if sys.argv[1] == '--fixture-more': fixture_more(sys.argv[2]); print('make-dpr-corpus: fixture', sys.argv[2]); return
    out = sys.argv[1]; n = int(sys.argv[2]) if len(sys.argv) > 2 else 300; seed = int(sys.argv[3]) if len(sys.argv) > 3 else 20261012
    root = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
    os.makedirs(out, exist_ok=True)
    g = Gen(load_data(root), seed)
    index = []
    for i in range(n):
        s = g.make(i)
        pdf = os.path.join(out, 'synth-%03d.pdf' % i)
        codes = draw(s, pdf)
        k = key_for(s, codes)
        json.dump(k, open(os.path.join(out, 'synth-%03d.key.json' % i), 'w'), indent=1)
        index.append(dict(id=k['id'], major=k['major'], catalog=k['catalog'], standing=k['standing'], scenarios=k['scenarios']))
    json.dump(index, open(os.path.join(out, 'index.json'), 'w'), indent=1)
    print(f'make-dpr-corpus: {n} reports in {out}')

if __name__ == '__main__':
    main()
