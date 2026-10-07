#!/usr/bin/env python3
"""Tap anywhere in a day to widen it (Tate, 2026-10-03: "when you click anywhere on a specific day that it
does the widening so its not just the day text its the whole area except when you click the class it
shows the class view of course"), plus the second-model review's fixes for build 06:00.

- Every week grid with a day picker (Home cards, a friend's week and plans, Schedule, Plans): the whole
  day column toggles that day, exactly like its header. A class block still opens the class/section,
  because the tap lands on the block first. The header stays the button for keyboards and screen readers.
- Review fixes:
  - a new message arriving by realtime no longer pulls you to the bottom while you have scrolled up to
    read (render() now decides: only if you were already at the newest);
  - the story order reads busyToday() like status(), so a future work shift orders stories too;
  - chat rows give a friend with no classes added the same grey ring as the stories;
  - stale comments about the old "+N" tray are updated.

Applies after anytime-two-line-2026-10-03.py.
Usage: python3 day-column-tap-2026-10-03.py <repo-dir>   (edits <repo-dir>/app/index.html)
"""
import sys, os
p = os.path.join(sys.argv[1], 'app', 'index.html')
s = open(p, encoding='utf-8').read()
if 'class="g-col ${wide ? \'on\' : \'\'}"${o.act' in s: sys.exit('already patched')
R = [
 # the whole column is the day's toggle
 ("    return `<div class=\"g-col ${wide ? 'on' : ''}\">${blocks}${now}</div>`;\n",
  "    /* the whole day toggles it, like its header; a class block inside still opens the class */\n"
  "    return `<div class=\"g-col ${wide ? 'on' : ''}\"${o.act ? ` data-a=\"${o.act}\" data-x=\"${d}\"${o.key != null ? ` data-y=\"${esc(o.key)}\"` : ''}` : ''}>${blocks}${now}</div>`;\n"),
 (".g-col{position:relative;border-radius:12px;background:var(--bg);container-type:inline-size}\n",
  ".g-col{position:relative;border-radius:12px;background:var(--bg);container-type:inline-size}\n.g-col[data-a]{cursor:pointer;-webkit-tap-highlight-color:transparent}\n"),
 # review: realtime never yanks you down while reading (the handler gets a name so it can be tested)
 ("    TC.rt = sb.channel('termchamp-app-messages').on('postgres_changes', { event: 'INSERT', schema: 'public', table: 'messages' }, payload => {\n",
  "    TC.rt = sb.channel('termchamp-app-messages').on('postgres_changes', { event: 'INSERT', schema: 'public', table: 'messages' }, TC.onMessage = payload => {\n"),
 ("      render(true); if (cur().s === 'chat') scrollEnd();\n    }).subscribe();",
  "      render(true);   /* render() keeps you at the newest message only if you were already there */\n    }).subscribe();"),
 # review: the story order reads the same day as status()
 ("  const st = status(id), now = CLOCK.min, today = todaySecs(id);\n",
  "  const st = status(id), now = CLOCK.min, today = busyToday(id);\n"),
 # review: chat rows use the same ring as the stories
 ("style=\"--rc:${o && TC.friends.includes(o) ? status(o).c || 'transparent' : 'transparent'}\"",
  "style=\"--rc:${o && TC.friends.includes(o) ? status(o).rc || status(o).c || 'transparent' : 'transparent'}\""),
 # review: stale comments
 ("/* the \"No set time\" row under a Home week: online sections, unposted times, classes with no section */\n"
  "/* Anytime tray (Tate, 2026-09-30, option A3): a soft grey tray set apart from the week, \"ANYTIME\" on the\n"
  "   left, white chips with just the code, one line, \"+N\" for the rest. */\n",
  "/* Anytime tray under a Home week (Tate, 2026-09-30 option A3; 2026-10-03): online sections, unposted times\n"
  "   and classes with no section, as white chips with the code on two lines; it wraps, nothing is hidden. */\n"),
 ("/* The Anytime tray counts how many chips fit the card's width (homeWeekCard). When that width changes,\n"
  "   draw again so the line is never clipped or left short. */\n", ""),
]
for a, b in R:
    if s.count(a) != 1: sys.exit(f'anchor matched {s.count(a)}x: {a[:80]}')
    s = s.replace(a, b)
open(p, 'w', encoding='utf-8').write(s)
print('patched', p)
