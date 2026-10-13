#!/usr/bin/env python3
"""Your own profile gets the friend page's header (Tate, 2026-10-11: "change the profile that we made friends
profile into and build it into the my profile"), and the Rate tab's "Current term" badge turns blue ("make
current term. blue as well").

- My profile's top card is now the friend page's card (friend-header-strip, option C): one white card (24px
  corners, 12px padding), the 46px photo in the same 3px ring box (no ring colour), the name at 20px, @handle at 13px, and on the right a 34px "Edit" pill
  (pencil + word, on the blue-soft the round pencil had, in blue ink so the word is 4.5:1+; still "Edit profile" to a screen reader) where the
  friend page has Message.
- Under it the same neutral strip, MAJOR · CONCENTRATION · YEAR: muted caps labels, plain-ink values, no green or
  blue; major and concentration share the width, the year only its word's; words wrap at spaces. A cell shows only
  when it has a value; "General / Open" is no concentration (the friend rule); a stored "… concentration" isn't said
  twice. With no major the Major cell is a button, "Add your major" in blue, that opens Edit profile.
- The rows under the card (Friends, My ratings, …) are unchanged. The old .mebub styles stay in the file unused.
- Rate › "Current term": blue-soft with blue ink (light #E3ECFF / #1E40AF, dark #172748 / #A9C6FF) instead of amber.

Usage: python3 me-strip-2026-10-11.py <repo>
"""
import sys, pathlib
root = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else '.')
f = root / 'app' / 'index.html'
s = f.read_text()
if 'me-strip (2026-10-11)' in s:
    sys.exit('already patched')

def one(old, new):
    global s
    n = s.count(old)
    assert n == 1, (n, old[:90])
    s = s.replace(old, new)

# 1. the strip: one helper for both pages (the friend page's cells, unchanged)
one("""  const conc = p.conc && p.conc !== 'General / Open' ? meConc(p.conc) : '';
  const cell = (l, v, c) => `<div class="fs-c ${c}"><span class="fs-l">${l}</span><span class="fs-v">${esc(v)}</span></div>`;
  const parts = [p.major ? cell('Major', p.major, 'g') : '', conc ? cell('Concentration', conc, 'g') : '', p.standing ? cell('Year', p.standing, 'y') : ''].filter(Boolean);
  return parts.length ? `<div class="fstrip fbubs">${parts.join('')}</div>` : '';
}""", """  return profStrip(p.major, p.conc, p.standing, 'fbubs');
}
/* me-strip (2026-10-11): the friend page's strip, shared with your own profile. mine: a missing major is
   a button, "Add your major", that opens Edit profile. */
function profStrip(major, conc0, year, cls, mine) {
  const conc = conc0 && conc0 !== 'General / Open' ? meConc(conc0) : '';
  const cell = (l, v, c) => `<div class="fs-c ${c}"><span class="fs-l">${l}</span><span class="fs-v">${esc(v)}</span></div>`;
  const parts = [major ? cell('Major', major, 'g') : mine ? '<button class="fs-c g fs-add" data-a="openEditProfile"><span class="fs-l">Major</span><span class="fs-v">Add your major</span></button>' : '',
    conc ? cell('Concentration', conc, 'g') : '', year ? cell('Year', year, 'y') : ''].filter(Boolean);
  return parts.length ? `<div class="fstrip ${cls}">${parts.join('')}</div>` : '';
}""")

# 2. your profile's card
one("""  const conc = meConc(P.concentration), yr = P.class_standing ? `<div class="mebub yr"><span class="mebub-v">${esc(P.class_standing)}</span></div>` : '';
  const major = P.major ? `<div class="mebub"><span class="mebub-l">MAJOR</span><span class="mebub-v">${esc(P.major)}</span></div>`
    : `<button class="mebub" data-a="openEditProfile"><span class="mebub-l">MAJOR</span><span class="mebub-v">Add your major</span></button>`;
  const bubs = conc ? `${major}<div class="r2"><div class="mebub"><span class="mebub-l">CONCENTRATION</span><span class="mebub-v">${esc(conc)}</span></div>${yr}</div>`
    : (yr ? `<div class="r2">${major}${yr}</div>` : major);
""", """  const strip = profStrip(P.major, P.concentration, P.class_standing, 'mestrip', true);
""")
one("""    body: `<div class="mepg"><div class="topbtns mehd">${backBtn()}<div class="mehd-t">Profile</div><button class="iconbtn" data-a="openSettings" aria-label="Settings">${ic('gear', 21, 2)}</button></div>
 <div class="card mecard"><div class="mehead">${pav('me', 76, 26)}<div class="grow"><div class="mename">${esc(PEOPLE.me.name)}</div>${P.username ? `<div class="mehandle">@${esc(P.username)}</div>` : ''}</div>
  <button class="meedit" data-a="openEditProfile" aria-label="Edit profile">${ic('pencil', 19, 2.3)}</button></div>
  <div class="mebubs">${bubs}</div></div>""",
    """    body: `<div class="mepg meown"><div class="topbtns mehd">${backBtn()}<div class="mehd-t">Profile</div><button class="iconbtn" data-a="openSettings" aria-label="Settings">${ic('gear', 21, 2)}</button></div>
 <div class="card mecard"><div class="mehead"><span class="ringav" style="--rc:transparent;padding:3px">${pav('me', 46, 18)}</span><div class="grow"><div class="mename">${esc(PEOPLE.me.name)}</div>${P.username ? `<div class="mehandle">@${esc(P.username)}</div>` : ''}</div>
  <button class="meedit" data-a="openEditProfile" aria-label="Edit profile">${ic('pencil', 15, 2.4)}Edit</button></div>
  ${strip}</div>""")

# 3. styles: the friend card's rules cover your card too
one(""".fpg{--fs-bg:#F1F5F9;--fs-ln:#E2E8F0;--fs-mut:#5B6B80}
:root[data-theme="dark"] .fpg{--fs-bg:#1B2438;--fs-ln:#26304A;--fs-mut:#9AA6BA}
.fpg .mecard{padding:12px;gap:12px;border-radius:24px}
.fpg .mehead{gap:12px}
.fpg .mename{font-size:20px;line-height:1.15}
.fpg .mehandle{font-size:13px;margin-top:0}""",
    """.fpg,.meown{--fs-bg:#F1F5F9;--fs-ln:#E2E8F0;--fs-mut:#5B6B80}
:root[data-theme="dark"] .fpg,:root[data-theme="dark"] .meown{--fs-bg:#1B2438;--fs-ln:#26304A;--fs-mut:#9AA6BA}
.fpg .mecard,.meown .mecard{padding:12px;gap:12px;border-radius:24px}
.fpg .mehead,.meown .mehead{gap:12px}
.fpg .mename,.meown .mename{font-size:20px;line-height:1.15}
.fpg .mehandle,.meown .mehandle{font-size:13px;margin-top:0}
/* me-strip (2026-10-11): your Edit is the friend page's Message pill, in the pencil's blue */
.meown .meedit{display:inline-flex;align-items:center;justify-content:center;gap:6px;width:auto;height:34px;padding:0 14px;border-radius:999px;font-size:13px;font-weight:900;align-self:center;color:var(--blue-ink)}
.meown .meedit svg{flex:none}
.fs-add{border:0;background:none;font:inherit;text-align:left;cursor:pointer}
.fs-add .fs-v{color:var(--blue-t,var(--blue))}
.fs-add:focus-visible{outline-offset:-3px;border-radius:16px}""")

# 4. Rate's "Current term" badge: blue
one(""".curterm{background:var(--amber-soft);color:var(--seat-low);""", """.curterm{background:var(--blue-soft);color:var(--blue-ink);""")

f.write_text(s)
print('patched', f)
