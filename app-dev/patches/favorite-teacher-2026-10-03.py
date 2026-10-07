#!/usr/bin/env python3
r"""Rate form: no "What did they do well?", no "In person + Online = hybrid" line, and a
Favorite teacher pick — three per student (Tate, 2026-10-03: "take the in person + online = hybrid
text out. also take out what did they do well"; "lets add in a favorite teacher badge so it will
give the professor a favorite teacher students only get 3 of these").

  · the ten "did well" chips are gone from + Add detail. A new review posts tags: []. A draft saved
    before this build comes back without its chips. Editing an older review keeps the tags it had
    (the edit sends what it read), and a professor's page still lists tags already posted;
  · Format keeps its three chips (In person + Online still saves "Hybrid"); only the hint line goes;
  · **Favorite teacher** sits under "Take again?": a heart button, "N of 3 left" beside it,
    "All 3 used" (button disabled) when the student has three elsewhere. It's saved after the review
    posts, through set_favorite_teacher() (sql/professify-favorite-teachers.sql), which enforces the
    3, needs the student's own review of that professor, and refuses with a sentence the app shows.
    Editing a review shows the heart as saved and can take it back, freeing a slot;
  · a professor's page shows "♥ Favorite teacher of N students" (your school, counts only);
    your reviews on Me carry a ♥ Favorite chip; the thanks screen says FAVORITE · Yes. The count
    only comes back at 3 or more students (the app's floor for any number built on reviews), so a
    badge never points at one reviewer;
  · the pick is kept in a saved draft; it's saved after the thanks screen is up; an edit that opened
    before the favorites loaded picks them up; the button keeps one name ("Favorite teacher") and
    says on/off with aria-pressed, focus stays on it, and "N of 3 left" is announced;
  · until the SQL runs (the function is missing), none of this shows — no button, no badge.

Usage: python3 favorite-teacher-2026-10-03.py <repo-dir>. Every anchor must match exactly once.
"""
import sys, os
p = os.path.join(sys.argv[1], 'app', 'index.html')
s = open(p, encoding='utf-8').read()

def rep(a, b):
    global s
    n = s.count(a)
    if n != 1: sys.exit(f'anchor matched {n}x: {a[:90]}')
    s = s.replace(a, b)

# 1. CSS.
rep(".tc-tags button.on{",
    ".favbtn{display:inline-flex;align-items:center;gap:7px;height:44px;padding:0 16px;border-radius:999px;background:var(--bg);border:1.5px solid transparent;font-weight:900;font-size:15px;color:var(--ink3);flex:none}\n"
    ".favbtn.on{background:#FFE4E6;border-color:#E11D48;color:#9F1239}\n"
    ".favbtn:disabled{opacity:.5}\n"
    ".favbadge{display:inline-flex;align-items:center;gap:6px;margin-top:12px;padding:7px 12px;border-radius:999px;background:#fff;color:#9F1239;font-weight:900;font-size:13.5px}\n"
    ".favchip{display:inline-flex;align-items:center;gap:4px;color:#9F1239;font-weight:900;font-size:12.5px}\n"
    ".tc-tags button.on{")

# 2. The hint line under Format, and the "did well" chips.
rep("<span class=\"hint\" style=\"color:var(--muted)\">In person + Online = hybrid</span>", "")
rep("   <div class=\"frow2\"><div class=\"row sb\" style=\"margin-bottom:10px\"><span class=\"flabel\">What did they do well?</span><span class=\"hint\">Pick any</span></div><div class=\"tc-tags\">${RATE_TAGS.map(t => `<button class=\"${(d.tags || []).includes(t) ? 'on' : ''}\" data-a=\"draftTag\" data-x=\"${esc(t)}\" aria-pressed=\"${(d.tags || []).includes(t)}\">${esc(t)}</button>`).join('')}</div></div>\n", "")
rep("kept.tags = Array.isArray(kept.tags) ? kept.tags.filter(t => RATE_TAGS.includes(t)) : [];", "kept.tags = [];")

# 3. Favorite teacher: helpers, loading, saving.
rep("function wordCount(t) {",
    "/* Favorite teacher (2026-10-03): three per student, enforced by set_favorite_teacher(). */\n"
    "const FAV_MAX = 3;\n"
    "const heartI = (s = 16, on = true) => `<svg width=\"${s}\" height=\"${s}\" viewBox=\"0 0 24 24\" aria-hidden=\"true\" fill=\"${on ? '#E11D48' : 'none'}\" stroke=\"${on ? '#E11D48' : 'currentColor'}\" stroke-width=\"2.2\" stroke-linejoin=\"round\"><path d=\"M12 20.5s-7.5-4.6-9.3-9.2C1.4 7.9 3.6 4.5 7 4.5c2 0 3.6 1.1 5 3 1.4-1.9 3-3 5-3 3.4 0 5.6 3.4 4.3 6.8-1.8 4.6-9.3 9.2-9.3 9.2z\"/></svg>`;\n"
    "const favOthers = key => [...(TC.myFavs || [])].filter(k => k !== key).length;\n"
    "function favRow(d) {\n"
    "  if (!TC.favOn) return '';\n"
    "  const key = d.favKey || reviewKeyOf(d.prof), others = favOthers(key), full = !d.fav && others >= FAV_MAX, left = Math.max(0, FAV_MAX - others - (d.fav ? 1 : 0));\n"
    "  return `<div class=\"frow2 row sb\"><span class=\"flabel\">Favorite teacher<div class=\"hint rf-fh\" role=\"status\" aria-live=\"polite\" style=\"margin-top:2px\">${full ? 'All 3 used' : `${left} of ${FAV_MAX} left`}</div></span><button class=\"favbtn ${d.fav ? 'on' : ''}\" data-a=\"favTog\" aria-label=\"Favorite teacher\" aria-pressed=\"${!!d.fav}\" ${full ? 'disabled' : ''}>${heartI(18, !!d.fav)}${d.fav ? 'Favorite' : 'Pick'}</button></div>`;\n"
    "}\n"
    "function favBadge(pk) { const n = TC.favCounts && TC.favCounts[reviewKeyOf(pk)]; return n ? `<div class=\"favbadge\">${heartI(15)}Favorite teacher of ${n} student${n === 1 ? '' : 's'}</div>` : ''; }\n"
    "function wordCount(t) {")
rep("  TC.myReviews = (!m.error && Array.isArray(m.data)) ? m.data : [];\n}",
    "  TC.myReviews = (!m.error && Array.isArray(m.data)) ? m.data : [];\n  await TC.loadFavs();\n}\n"
    "/* Favorites: off only when the functions aren't there yet (the SQL hasn't run). A failed read\n"
    "   otherwise keeps what was known, so a hiccup never hides the button mid-form. */\n"
    "TC.loadFavs = async function () {\n"
    "  const sb = TC.client(); let fv, fc;\n"
    "  try { [fv, fc] = await Promise.all([sb.rpc('my_favorite_teachers'), sb.rpc('favorite_teacher_counts')]); } catch (e) { return; }\n"
    "  if (fv.error) { if (/PGRST202|42883/.test(String(fv.error.code || '')) || /could not find the function|does not exist/i.test(fv.error.message || '')) TC.favOn = false; }\n"
    "  else { TC.favOn = true; TC.myFavs = new Set((fv.data || []).map(x => typeof x === 'string' ? x : x && (x.my_favorite_teachers || x.professor_key)).filter(Boolean));\n"
    "    const d = S.draft; if (d && d.editing && !d.favTouched) d.fav = d.fav0 = TC.myFavs.has(d.favKey); }\n"
    "  if (!fc.error) { const m = {}; (fc.data || []).forEach(x => { if (x && x.professor_key) m[x.professor_key] = +x.n || 0; }); TC.favCounts = m; }\n"
    "};\n"
    "TC.setFav = async function (key, on) {\n"
    "  const r = await TC.client().rpc('set_favorite_teacher', { p_key: key, p_on: !!on });\n"
    "  if (r.error) return dbSay(r.error, 'Your favorite teacher didn’t save.');\n"
    "  TC.myFavs = TC.myFavs || new Set(); if (on) TC.myFavs.add(key); else TC.myFavs.delete(key);\n"
    "  await TC.loadFavs(); return null;\n"
    "};")

# 4. The row in the form, the draft fields, the tap.
rep("   <div class=\"frow2 row sb\"><span class=\"flabel\">Take again?</span><div style=\"width:190px\">${sg('again', ['yes', 'no'], ['Yes', 'No'])}</div></div>\n",
    "   <div class=\"frow2 row sb\"><span class=\"flabel\">Take again?</span><div style=\"width:190px\">${sg('again', ['yes', 'no'], ['Yes', 'No'])}</div></div>\n"
    "   ${favRow(d)}\n")
rep("more: false, grade: null, format: null, review: '', err: '' };",
    "more: false, grade: null, format: null, review: '', err: '', fav: false, favKey: reviewKeyOf(pid) };")
rep("tags: (v.tags || []).slice(), err: '', editing: v.id };",
    "tags: (v.tags || []).slice(), err: '', editing: v.id, favKey: v.professor_key, fav: !!(TC.myFavs && TC.myFavs.has(v.professor_key)), fav0: !!(TC.myFavs && TC.myFavs.has(v.professor_key)) };")
rep("  draftMore: () => { S.draft.more = !S.draft.more; render(true); },",
    "  draftMore: () => { S.draft.more = !S.draft.more; render(true); },\n"
    "  favTog: () => { const d = S.draft; if (!d || !TC.favOn) return; if (!d.fav && favOthers(d.favKey || reviewKeyOf(d.prof)) >= FAV_MAX) return; d.fav = !d.fav; d.favTouched = true; d.err = ''; draftSave(); const hf = document.activeElement && document.activeElement.classList.contains('favbtn'); render(true); if (hf) { const b = document.querySelector('.rf .favbtn'); if (b) b.focus(); } },")

# 5. Saving it: after a new review posts, and after an edit saves.
rep("    S.lastRated = Object.assign({}, d, { reviewId: r.id, share: false });\n    const st = S.stack[S.tab]; st[st.length - 1] = { s: 'rateThanks', p: {} }; render();\n",
    "    S.lastRated = Object.assign({}, d, { reviewId: r.id, share: false });\n    const st = S.stack[S.tab]; st[st.length - 1] = { s: 'rateThanks', p: {} }; render();\n"
    "    /* The favorite is saved once the review exists (the server needs it), after the thanks screen\n"
    "       is up, so a slow call never leaves the student waiting on the form. */\n"
    "    if (d.fav && TC.favOn) { const L = S.lastRated, fe = await TC.setFav(d.favKey || reviewKeyOf(d.prof), true); if (fe) toast('Rating posted. ' + fe); else if (S.lastRated === L) { L.favSaved = true; if (cur() && cur().s === 'rateThanks') render(true); } }\n"
    "    else if (TC.favOn) TC.loadFavs();\n")
rep("  if (e) { d.err = e; return render(true); }\n  S.draft = null; toast('Review updated');",
    "  if (e) { d.err = e; return render(true); }\n"
    "  let fe = null; if (TC.favOn && !!d.fav !== !!d.fav0) fe = await TC.setFav(d.favKey, !!d.fav);\n"
    "  S.draft = null; toast(fe ? 'Review updated. ' + fe : 'Review updated');")

rep("tags: d.tags || [], more: d.more, at: Date.now() }", "tags: d.tags || [], fav: !!d.fav, more: d.more, at: Date.now() }")
rep("more: !!(v.grade || v.format || v.note || (v.tags || []).length)", "more: !!(v.format || v.note)")

# 6. Where it shows: thanks screen, a professor's page, your reviews on Me.
rep("...(d.format ? [['FORMAT', d.format]] : [])];",
    "...(d.format ? [['FORMAT', d.format]] : []), ...(d.favSaved ? [['FAVORITE', '♥ Yes']] : [])];")
rep("<button class=\"btn\" style=\"background:#fff;color:var(--purple-ink);margin-top:14px;box-shadow:none;height:48px\" data-a=\"rateProf\"",
    "${favBadge(id)}<button class=\"btn\" style=\"background:#fff;color:var(--purple-ink);margin-top:14px;box-shadow:none;height:48px\" data-a=\"rateProf\"")
rep("${starsTxt(v.score)}<span class=\"muted b\" style=\"font-size:12.5px\">${agoText(v.created_at)}",
    "${starsTxt(v.score)}${TC.myFavs && TC.myFavs.has(v.professor_key) ? `<span class=\"favchip\">${heartI(13)}Favorite</span>` : ''}<span class=\"muted b\" style=\"font-size:12.5px\">${agoText(v.created_at)}")

open(p, 'w', encoding='utf-8').write(s)
print('patched', p)
