#!/usr/bin/env python3
"""Mutants for logo-image-2026-10-11.py. Usage: python3 logo-image-mutants-2026-10-11.py app-dev/tests/mutate.mjs"""
import json, sys
p = sys.argv[1]; s = open(p, encoding='utf-8').read()
M = [
  ["logo: typed wordmark back on Home", "<h1 class=\"tc-wordmark tc-logo\" aria-label=\"TermChamp\">${tcLogo('', 36)}</h1>", "<h1 class=\"tc-wordmark\" aria-label=\"TermChamp\">Term<span>Champ</span></h1>"],
  ["logo: dark mode shows the light cut", ":root[data-theme=\"dark\"] .homehdr .tc-logo .lg-l{display:none}\n:root[data-theme=\"dark\"] .homehdr .tc-logo .lg-d{display:block}", ""],
  ["logo: both cuts showing", ".tc-logo .lg-d{display:none}\n", ""],
  ["logo: the dark cut in light mode too", "<img class=\"tc-logo-i lg-l ${cls || ''}\" src=\"${TC_LOGO}\"", "<img class=\"tc-logo-i lg-l ${cls || ''}\" src=\"${TC_LOGO_DARK}\""],
  ["logo: the welcome logo isn't named", "<div class=\"wordmark tc-logo\" role=\"img\" aria-label=\"TermChamp\">", "<div class=\"wordmark tc-logo\">"],
  ["logo: long press offers Save Image", "-webkit-touch-callout:none;pointer-events:none}", "-webkit-touch-callout:none}"],
  ["logo: squashed on a narrow phone", ".tc-logo-i{display:block;height:36px;width:auto;max-width:none;flex:none;", ".tc-logo-i{display:block;height:36px;width:auto;max-width:120px;flex:none;"],
  ["logo: stretched", ".tc-logo-i{display:block;height:36px;width:auto;", ".tc-logo-i{display:block;height:36px;width:200px;"],
  ["logo: typed wordmark back on the welcome screen", "<div class=\"wordmark tc-logo\" role=\"img\" aria-label=\"TermChamp\"><img class=\"tc-logo-i\" src=\"${TC_LOGO}\" alt=\"\" height=\"48\" draggable=\"false\" style=\"display:block;height:48px;width:auto;max-width:100%;margin:0;-webkit-touch-callout:none;pointer-events:none;user-select:none\"></div>", "<div class=\"wordmark\">TermChamp</div>"],
  ["logo: no name read out", "<h1 class=\"tc-wordmark tc-logo\" aria-label=\"TermChamp\">", "<h1 class=\"tc-wordmark tc-logo\">"],
]
a = "const M = [\n"
assert s.count(a) == 1
s = s.replace(a, a + "  /* Tate's logo image (2026-10-11) */\n" + "".join("  " + json.dumps([m[0], m[1], m[2], "wordmark"], ensure_ascii=False) + ",\n" for m in M))
open(p, 'w', encoding='utf-8').write(s)
print('mutants patched')
