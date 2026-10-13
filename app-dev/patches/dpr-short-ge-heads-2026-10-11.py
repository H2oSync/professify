#!/usr/bin/env python3
"""The reader: a GE line under a short heading (a friend's real report, printed 2026-10-11: "B2", "C Elect LD",
"F (ES)", "GE Elect: Elective in Area B/c/d") takes its name from the verdict ("Not Satisfied: B2: LIFE SCIENCE
COURSE - 4 Units Required (R73-20)"), so the app knows its GE area: the Builder offers B2 classes, a class you're
taking can put it in progress, and Past classes says "B2: Life Science Course", not "B2".
Usage: python3 dpr-short-ge-heads-2026-10-11.py <repo-dir>   (replayable)"""
import sys, os
PP = os.path.join(sys.argv[1], 'app', 'planner.js'); S = open(PP, encoding='utf-8').read()
a = """      if(/general education/i.test(courseLine?((group&&group.label)||''):gl)||(!courseLine&&/\\bGE\\b/.test(b.label))||/^GE\\b/i.test(ctx)){ b.kind='ge'; if(gm)b.ge=gm[1].toUpperCase().replace(/\\s+/g,''); }"""
b = """      if(/general education/i.test(courseLine?((group&&group.label)||''):gl)||(!courseLine&&/\\bGE\\b/.test(b.label))||/^GE\\b/i.test(ctx)){ b.kind='ge';
        /* (2026-10-11) a short heading over a verdict that names the area ("B2" over "B2: LIFE SCIENCE COURSE - …"): the verdict's name */
        if(head&&words&&!courseLine){ var wl=dprTidyLabel(words);
          if(wl&&wl!==b.label&&/^(?:(?:[A-F](?:[1-5]|\\s?UD)?|[1-6][A-F]?)\\s*(?:\\((?:Qtr|Sem)\\)\\s*)?:|Lower[- ]division C Elective\\b|GE Electives?\\b)/i.test(wl)){ b.label=wl;
            gm=/^([A-F](?:[1-5]|\\s?UD)?|[1-6][A-F]?)\\s*(?:\\((?:Qtr|Sem)\\)\\s*)?:/i.exec(wl)||gm; } }
        if(gm)b.ge=gm[1].toUpperCase().replace(/\\s+/g,''); }"""
if S.count(a) != 1: sys.exit(f'ge heads: anchor matched {S.count(a)}x')
S = S.replace(a, b)
open(PP, 'w', encoding='utf-8').write(S); print('dpr-short-ge-heads: done')
