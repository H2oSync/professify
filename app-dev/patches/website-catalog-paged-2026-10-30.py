#!/usr/bin/env python3
"""Scale (2026-10-30), website: loadCoursePrereqData() read course_equiv (3,052 rows) and course_prereqs (1,665)
in one request each. PostgREST stops at 1000 rows without saying so, so two thirds of the legacy-code crosswalk
and 665 classes' prerequisites never loaded ("no prerequisites" where there are some). Both are now read a
page at a time with .range(), in a fixed order, like app/planner.js loadCatalogTables() all(). A failed page
keeps what came before it (as planner.js does) and the seed indexes are rebuilt from it.
Usage: python3 website-catalog-paged-2026-10-30.py index.html"""
import sys
p = sys.argv[1]; s = open(p, encoding='utf-8').read()
def one(old, new):
    global s
    assert s.count(old) == 1, (s.count(old), old[:90]); s = s.replace(old, new)
one("""    var eq=await sb.from('course_equiv').select('legacy_code,current_code');
    if(eq&&!eq.error&&Array.isArray(eq.data)&&eq.data.length){""",
"""    /* paged (scale, 2026-10-30): both tables are bigger than one 1000-row PostgREST page */
    async function catAll(table,cols,ord){ var out=[],err=null; for(var off=0;off<40000;off+=1000){ var q=sb.from(table).select(cols); ord.forEach(function(c){ q=q.order(c); }); var r=await q.range(off,off+999); if(!r||r.error||!Array.isArray(r.data)){ err=(r&&r.error)||{message:'no rows'}; break; } out=out.concat(r.data); if(r.data.length<1000)break; } return {data:out,error:out.length?null:err}; }
    var eq=await catAll('course_equiv','legacy_code,current_code',['legacy_code','current_code']);
    if(eq&&!eq.error&&Array.isArray(eq.data)&&eq.data.length){""")
one("""    var pr=await sb.from('course_prereqs').select('course_code,prereq_json');""",
"""    var pr=await catAll('course_prereqs','course_code,prereq_json',['course_code']);""")
open(p, 'w', encoding='utf-8').write(s); print(p, 'website: course_equiv + course_prereqs paged')
