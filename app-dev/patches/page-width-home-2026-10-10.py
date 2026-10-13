#!/usr/bin/env python3
"""Explore, Rate, Planner / Past classes and Friends at Home's page width (Tate, 2026-10-10): cards, search, chips and
lists 12px from the screen edge (were 16), like Home; titles and small labels keep their 4px inset (16), as on Home.
Usage: python3 page-width-home-2026-10-10.py app/index.html"""
import sys
path = sys.argv[1]
s = open(path, encoding='utf-8').read()
def one(old, new):
    global s
    assert s.count(old) == 1, ('anchor count', s.count(old), old[:90])
    s = s.replace(old, new)
def span(a, b):
    i = s.index(a); j = s.index(b, i); return i, j

# --- markup: a .w12 wrapper on each screen
one('body: `<div class="title">Explore</div>', 'body: `<div class="w12"><div class="title">Explore</div>')
one('<div class="pad" id="exlist">${exploreList()}</div><div class="spacer"></div>', '<div class="pad" id="exlist">${exploreList()}</div></div><div class="spacer"></div>')

i, j = span('SCREENS.rate = () => {', '\n};')
blk = s[i:j]
assert blk.count('body: `<div class="title">Rate</div>') == 1 and blk.count('\n <div class="spacer"></div>`') == 1
blk = blk.replace('body: `<div class="title">Rate</div>', 'body: `<div class="w12"><div class="title">Rate</div>')
blk = blk.replace('\n <div class="spacer"></div>`', '\n</div><div class="spacer"></div>`')
assert blk.count('margin:0 16px') == 1 and blk.count('padding:0 20px') == 1
blk = blk.replace('margin:0 16px', 'margin:0 12px').replace('padding:0 20px', 'padding:0 16px')
s = s[:i] + blk + s[j:]

# friends: the screen and the three bodies that draw cards at 16px
one('body: `<div class="fhdr"><div class="title">Friends</div>', 'body: `<div class="w12"><div class="fhdr"><div class="title">Friends</div>')
one('<div id="fbody">${friendsBody()}</div>\n <div class="spacer"></div>`', '<div id="fbody">${friendsBody()}</div>\n</div><div class="spacer"></div>`')
i, j = span('function fRequests() {', 'function fRepaint()')
blk = s[i:j]
n = blk.count('margin:0 16px'); assert n >= 3, n
blk = blk.replace('margin:0 16px', 'margin:0 12px')
assert blk.count('padding-left:20px') == 1
blk = blk.replace('padding-left:20px', 'padding-left:16px')
s = s[:i] + blk + s[j:]
# the search results
i, j = span('function fSearchResults', '\nfunction ')
blk = s[i:j]; print('search results 16px margins:', blk.count('margin:0 16px'))
blk = blk.replace('margin:0 16px', 'margin:0 12px')
s = s[:i] + blk + s[j:]

# schedule: Planner and Past classes
one("${t === 'planner' || t === 'past' ? inner : `<div class=\"schpg\">${inner}</div>`}", "${t === 'planner' || t === 'past' ? `<div class=\"w12\">${inner}</div>` : `<div class=\"schpg\">${inner}</div>`}")

# --- css
one(".schpg .regbar{margin-left:14px;margin-right:14px}\n", """.schpg .regbar{margin-left:14px;margin-right:14px}
/* Explore, Rate, Planner, Past classes and Friends at Home's page width (Tate, 2026-10-10): cards, search, chips and lists
   12px from the edge; titles and small labels 16px, i.e. 4px inside the cards, exactly as on Home */
.w12 .pad,.w12 .frow,.w12 .hscroll{padding-left:12px;padding-right:12px}
.w12 .search,.w12 .fsearch,.w12 .tc-sec,.w12 .pl-card,.w12 .pla-reg,.w12 .pl-picks,.w12 .pl-done,.w12 .pk-empty{margin-left:12px;margin-right:12px}
.w12 .term,.w12 .fs-h,.w12 .sec-h,.w12 .fs-note,.w12 .pk-note{padding-left:16px;padding-right:16px}
""")
open(path, 'w', encoding='utf-8').write(s)
print('patched', path)
