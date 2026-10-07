#!/usr/bin/env python3
"""People without a profile photo get a light grey circle with a white person in it, like Instagram and
LinkedIn (Tate, 2026-10-03, on the Home stories' green / yellow / pink initial circles: "for people who
havent made profile pictures have them all be light gray or similar to instagram or linkenIn profiles who
havent added a photo").

- One look everywhere a person is drawn: stories, friend cards and lists, chats, faces on class blocks,
  search and suggestions, onboarding's friend suggestions, the profile button on Home and your own photo in
  Edit profile.
- A photo still shows over it; if a photo fails to load, the grey circle and the person are what's left
  (they sit underneath), never an empty coloured dot.
- Professors keep their rating-coloured initials (prof-avatar-tone); group chats keep their squares.

Applies after prof-avatar-tone-2026-10-03.py.
Usage: python3 no-photo-gray-2026-10-03.py <repo-dir>   (edits <repo-dir>/app/index.html)
"""
import sys, os
p = os.path.join(sys.argv[1], 'app', 'index.html')
s = open(p, encoding='utf-8').read()
if 'const NOPHOTO' in s: sys.exit('already patched')
SIL = ("/* No photo: a light grey circle with a white person, like Instagram and LinkedIn (Tate, 2026-10-03). */\n"
       "const NOPHOTO = '#DADDE3';\n"
       "const silhouette = (sz = '100%') => `<svg class=\"nophoto\" viewBox=\"0 0 24 24\" width=\"${sz}\" height=\"${sz}\" aria-hidden=\"true\" style=\"display:block;grid-area:1/1\"><circle cx=\"12\" cy=\"9.2\" r=\"4.4\" fill=\"#fff\"/><path d=\"M3.2 24.5c.6-5.4 4.2-8.6 8.8-8.6s8.2 3.2 8.8 8.6z\" fill=\"#fff\"/></svg>`;\n"
       "const noPhotoAv = size => `<span class=\"av noph\" style=\"width:${size}px;height:${size}px;background:${NOPHOTO};overflow:hidden\">${silhouette()}</span>`;\n")
R = [
 ("function safeImg(u) { return /^https:\\/\\//.test(String(u || '')) ? u : ''; }\n",
  "function safeImg(u) { return /^https:\\/\\//.test(String(u || '')) ? u : ''; }\n" + SIL),
 # pav: grey + person, with the photo laid over it
 ("  if (src) return `<span class=\"av\" style=\"width:${size}px;height:${size}px;background:${p.color};overflow:hidden\"><img src=\"${esc(src)}\" alt=\"\" loading=\"lazy\" referrerpolicy=\"no-referrer\" style=\"width:100%;height:100%;object-fit:cover\" onerror=\"this.remove()\"></span>`;\n  return av(p.ini, p.color, size, fs);\n",
  "  if (src) return `<span class=\"av\" style=\"width:${size}px;height:${size}px;background:${NOPHOTO};overflow:hidden\">${silhouette()}<img src=\"${esc(src)}\" alt=\"\" loading=\"lazy\" referrerpolicy=\"no-referrer\" style=\"grid-area:1/1;width:100%;height:100%;object-fit:cover\" onerror=\"this.remove()\"></span>`;\n  return noPhotoAv(size);\n"),
 # tiny faces in a stack
 ("av('', (PEOPLE[f] || {}).color || '#E6EAF1', size, size * .36)", "noPhotoAv(size)"),
 # stories
 ("${safeImg(p.avatar) ? `<span style=\"background:${p.color};overflow:hidden\"><img src=\"${esc(safeImg(p.avatar))}\" alt=\"\" style=\"width:100%;height:100%;object-fit:cover;border-radius:50%\" onerror=\"this.remove()\"></span>` : `<span style=\"background:${p.color};display:grid;place-items:center;font-weight:900;font-size:17px;color:#0F172A\">${esc(p.ini)}</span>`}",
  "${safeImg(p.avatar) ? `<span class=\"noph\" style=\"background:${NOPHOTO};overflow:hidden;display:grid\">${silhouette()}<img src=\"${esc(safeImg(p.avatar))}\" alt=\"\" style=\"grid-area:1/1;width:100%;height:100%;object-fit:cover;border-radius:50%\" onerror=\"this.remove()\"></span>` : `<span class=\"noph\" style=\"background:${NOPHOTO};overflow:hidden;display:grid\">${silhouette()}</span>`}"),
 # the profile button on Home
 ("<button class=\"me-btn\" data-a=\"openMe\" aria-label=\"Your profile\" style=\"overflow:hidden;padding:0\">${safeImg(PEOPLE.me.avatar) ? `<img src=\"${esc(safeImg(PEOPLE.me.avatar))}\" alt=\"\" style=\"width:100%;height:100%;object-fit:cover\" onerror=\"this.remove()\">` : esc(PEOPLE.me.ini)}</button>",
  "<button class=\"me-btn noph\" data-a=\"openMe\" aria-label=\"Your profile\" style=\"overflow:hidden;padding:0;background:${NOPHOTO}\">${silhouette()}${safeImg(PEOPLE.me.avatar) ? `<img src=\"${esc(safeImg(PEOPLE.me.avatar))}\" alt=\"\" style=\"grid-area:1/1;width:100%;height:100%;object-fit:cover\" onerror=\"this.remove()\">` : ''}</button>"),
 # a 1:1 chat whose other person isn't known yet
 ("${o ? pav(o, 48, 16) : av('?', '#E6EAF1', 48, 16)}", "${o ? pav(o, 48, 16) : noPhotoAv(48)}"),
 # onboarding's people (suggestions, "and N other friends", friends in your classes)
 ("  return `<div class=\"ava ${cls || ''}\" style=\"background:${ONB_COLORS[h % ONB_COLORS.length]};overflow:hidden\" aria-hidden=\"true\">${img ? `<img src=\"${esc(img)}\" alt=\"\" style=\"width:100%;height:100%;object-fit:cover\" onerror=\"this.remove()\">` : esc(initialsOf(p.name))}</div>`;",
  "  return `<div class=\"ava noph ${cls || ''}\" style=\"background:${NOPHOTO};overflow:hidden;display:grid\" aria-hidden=\"true\">${silhouette()}${img ? `<img src=\"${esc(img)}\" alt=\"\" style=\"grid-area:1/1;width:100%;height:100%;object-fit:cover\" onerror=\"this.remove()\">` : ''}</div>`;"),
 # your photo in Edit profile
 ("<span class=\"av\" style=\"width:76px;height:76px;background:${PEOPLE.me.color};overflow:hidden;font-size:24px\">${photo ? `<img src=\"${esc(photo)}\" alt=\"\" style=\"width:100%;height:100%;object-fit:cover\">` : esc(initialsOf(f.display_name || PEOPLE.me.name))}</span>",
  "<span class=\"av noph\" style=\"width:76px;height:76px;background:${NOPHOTO};overflow:hidden\">${silhouette()}${photo ? `<img src=\"${esc(photo)}\" alt=\"\" style=\"grid-area:1/1;width:100%;height:100%;object-fit:cover\">` : ''}</span>"),
]
for a, b in R:
    if s.count(a) != 1: sys.exit(f'anchor matched {s.count(a)}x: {a[:90]}')
    s = s.replace(a, b)
open(p, 'w', encoding='utf-8').write(s)
print('patched', p)
