#!/usr/bin/env python3
"""Scale (2026-10-30): PostgREST returns at most 1000 rows a request (db-max-rows) and says nothing when it
cuts a read short. Four reads in the phone app could pass that and lost rows silently:
  * loadFriends: friends' my_sections, saved_classes and class_history, one .in('user_id', <every friend>)
    read each — with 150 friends a third of them showed no classes, and the URL was ~6,000 characters;
  * loadReviews: asked for 2000 reviews and got 1000, so the oldest professors lost all their reviews;
  * loadThreads: message_hides .limit(5000) — 1000 at most, so older "Delete for me" came back.
Each is now read a page at a time with .range() (pagedAll, like planner.js all()), in a fixed order so pages
don't overlap; friends' reads go 50 friends per request, the chunks side by side. A page that fails fails the
read (as before: TC.err.friendSecs / TC.err.reviews), rather than passing off part of it as all of it.
Usage: python3 scale-paged-reads-2026-10-30.py app/index.html"""
import sys
p = sys.argv[1]; s = open(p, encoding='utf-8').read()
def one(old, new):
    global s
    assert s.count(old) == 1, (s.count(old), old[:90]); s = s.replace(old, new)

one("""function schemaGap(err) {""",
"""/* Every row, a page at a time (scale, 2026-10-30): PostgREST stops at 1000 rows a request without saying so.
   mk() builds the query afresh for each page (a supabase-js query runs once); give it an order so pages don't overlap. */
async function pagedAll(mk, max) {
  const out = [];
  for (let off = 0; off < (max || 50000); off += 1000) {
    const r = await mk().range(off, off + 999);
    if (r.error) return { data: out, error: r.error };
    const d = Array.isArray(r.data) ? r.data : []; out.push(...d);
    if (d.length < 1000) break;
  }
  return { data: out, error: null };
}
/* The same, for a list of ids too long for one URL: n ids a request, the chunks side by side. */
async function pagedIn(ids, mk, n) {
  const ch = []; for (let i = 0; i < ids.length; i += (n || 50)) ch.push(ids.slice(i, i + (n || 50)));
  const rs = await Promise.all(ch.map(c => pagedAll(() => mk(c))));
  const bad = rs.find(r => r.error);
  return { data: rs.flatMap(r => r.data), error: bad ? bad.error : null };
}
function schemaGap(err) {""")
one("""    const [secs, saved, hist] = await Promise.all([
      byTerm(sb.from('my_sections').select('user_id,code,class_nbr,section,instructor,days,status' + (split ? ',term' : '')).in('user_id', ids)),
      byTerm(sb.from('saved_classes').select('user_id,code' + (split ? ',term' : '')).in('user_id', ids)),
      sb.from('class_history').select('user_id,code,term,year,professor').in('user_id', ids)
    ]);""",
"""    const [secs, saved, hist] = await Promise.all([
      pagedIn(ids, c => byTerm(sb.from('my_sections').select('user_id,code,class_nbr,section,instructor,days,status' + (split ? ',term' : '')).in('user_id', c)).order('user_id').order('class_nbr').order('term')),
      pagedIn(ids, c => byTerm(sb.from('saved_classes').select('user_id,code' + (split ? ',term' : '')).in('user_id', c)).order('user_id').order('code').order('term')),
      pagedIn(ids, c => sb.from('class_history').select('user_id,code,term,year,professor').in('user_id', c).order('user_id').order('code').order('year').order('term').order('professor'))
    ]);""")
one("""  let r = await sb.from('reviews_public').select(cols).order('created_at', { ascending: false }).limit(2000);
  if (r.error && schemaGap(r.error)) r = await sb.from('reviews_public').select(cols.replace(',grade', '')).order('created_at', { ascending: false }).limit(2000);""",
"""  const rv = c => pagedAll(() => sb.from('reviews_public').select(c).order('created_at', { ascending: false }).order('id', { ascending: false }), 20000);
  let r = await rv(cols);
  if (r.error && schemaGap(r.error)) r = await rv(cols.replace(',grade', ''));""")
one("""    sb.from('message_hides').select('message_id').limit(5000),""",
"""    pagedAll(() => sb.from('message_hides').select('message_id').order('message_id')),""")
open(p, 'w', encoding='utf-8').write(s); print(p, 'paged: friends x3 (50 a request), reviews, message_hides')
