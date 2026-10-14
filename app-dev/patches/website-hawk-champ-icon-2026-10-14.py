"""The website's Hawk button becomes the phone's Champ: the blue bird in glasses with "Ask Me!" (2026-10-14).

Tate, on a screenshot of termchamp.com's bottom-right corner (the old headset-hawk face in a navy circle):
"you didnt change the hawk icon". The phone's launcher (app/index.html `.fab`, `CHAMP`) is the full blue bird,
no circle, under a small "Ask Me!" bubble, drifting gently (`soar`). The website now draws the same:
  - The bird is the phone's own image, lifted byte for byte from `const CHAMP` (webp data URI) into
    `--hawk-champ` in hawk-ask.css. The old `--hawk-face` stays defined (unused) so nothing else breaks.
  - The button keeps its name ("Ask Hawk"), its place, its click, its focus ring and aria-expanded. The bubble and the
    bird are decorative spans (aria-hidden); the bubble hides while the box is open, so the box sits just above the bird.
  - Bubble in the phone's colours, light and dark (white card, navy #16336B border/text; dark: panel and #AFC3EE).
  - The drift stops under prefers-reduced-motion, as on the phone.
  - The box's greeting face (`.hawk-hint__face`) shows the same bird, uncropped.
Run after website-hawk-help-chips-2026-10-14.py:  python3 <this> <repo>
"""
import sys, re, pathlib
root = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else '.')
app = (root / 'app' / 'index.html').read_text()
champ = re.search(r"const CHAMP='(data:image/webp;base64,[^']+)'", app).group(1)

css_f = root / 'hawk-ask.css'; css = css_f.read_text()
js_f = root / 'hawk-ask.js'; js = js_f.read_text()
def one(s, old, new):
    n = s.count(old); assert n == 1, (n, old[:90]); return s.replace(old, new)

css = one(css, """  /* Hawk's face, once.""", """  /* Champ, the phone app's bird (app/index.html CHAMP), byte for byte: the launcher and the greeting draw it. */
  --hawk-champ: url("%s");
  /* Hawk's face, once.""" % champ)
css = one(css, """.hawk-fab {
  position: fixed;
  right: 14px;
  bottom: calc(14px + env(safe-area-inset-bottom, 0px));
  z-index: 9000;
  width: 52px;
  height: 52px;
  padding: 0;
  border: 2px solid rgba(255, 255, 255, .22);
  border-radius: 999px;
  background-color: var(--hawk-navy);
  background-image: var(--hawk-face);
  background-size: cover;
  background-position: center;
  cursor: pointer;
  box-shadow: 0 8px 22px rgba(4, 12, 36, .34);
}
.hawk-fab:hover { border-color: rgba(255, 255, 255, .45); }""", """/* The phone's Champ (2026-10-14): the bird under an "Ask Me!" bubble, no circle, drifting gently. */
.hawk-fab {
  position: fixed;
  right: 12px;
  bottom: calc(10px + env(safe-area-inset-bottom, 0px));
  z-index: 9000;
  width: 68px;
  padding: 0;
  border: 0;
  border-radius: 14px;
  background: none;
  display: flex;
  flex-direction: column;
  align-items: center;
  cursor: pointer;
  -webkit-tap-highlight-color: transparent;
}
.hawk-fab__bub {
  background: #fff;
  border: 2px solid #16336B;
  color: #16336B;
  font: 900 11px/1.2 Nunito, system-ui, sans-serif;
  padding: 3px 9px;
  border-radius: 13px;
  position: relative;
  white-space: nowrap;
  box-shadow: 0 4px 10px rgba(22, 51, 107, .15);
}
.hawk-fab__bub::after {
  content: "";
  position: absolute;
  left: 50%;
  bottom: -6px;
  width: 8px;
  height: 8px;
  background: #fff;
  border: 2px solid #16336B;
  border-top: 0;
  border-left: 0;
  transform: translateX(-50%) rotate(45deg);
}
.hawk-fab__bird {
  display: block;
  width: 50px;
  height: 60px;
  margin-top: 3px;
  background: var(--hawk-champ) center / contain no-repeat;
  filter: drop-shadow(0 8px 10px rgba(22, 51, 107, .28));
  animation: hawk-soar 4.8s ease-in-out infinite;
}
@keyframes hawk-soar { 0%, 100% { transform: translateY(0) rotate(0); } 30% { transform: translateY(-6px) rotate(-2.5deg); } 65% { transform: translateY(-2px) rotate(2deg); } }
@media (prefers-reduced-motion: reduce) { .hawk-fab__bird { animation: none; } }
.hawk-fab[aria-expanded="true"] .hawk-fab__bub { display: none; }
:root[data-theme="dark"] .hawk-fab__bub, :root[data-theme="dark"] .hawk-fab__bub::after { background: var(--panel, #141B2B); border-color: #AFC3EE; color: #AFC3EE; }
@media (prefers-color-scheme: dark) { :root:not([data-theme="light"]):not([data-theme]) .hawk-fab__bub, :root:not([data-theme="light"]):not([data-theme]) .hawk-fab__bub::after { background: var(--panel, #141B2B); border-color: #AFC3EE; color: #AFC3EE; } }
.hawk-fab:hover .hawk-fab__bird { filter: drop-shadow(0 10px 12px rgba(22, 51, 107, .38)); }""")
css = one(css, """  bottom: calc(14px + env(safe-area-inset-bottom, 0px)); }""" if False else """  .hawk-fab { bottom: calc(var(--hawk-navclear, 74px) + env(safe-area-inset-bottom, 0px)); }""",
          """  .hawk-fab { bottom: calc(var(--hawk-navclear, 74px) - 6px + env(safe-area-inset-bottom, 0px)); }""")
# the box opens just above the bird (the bubble hides while it is open): 10 + 63 + 10
css = one(css, """  bottom: calc(76px + env(safe-area-inset-bottom, 0px));
  width: 340px;""", """  bottom: calc(84px + env(safe-area-inset-bottom, 0px));
  width: 340px;""")
css = one(css, """    bottom: calc(var(--hawk-navclear, 74px) + 62px + env(safe-area-inset-bottom, 0px));""",
          """    bottom: calc(var(--hawk-navclear, 74px) + 68px + env(safe-area-inset-bottom, 0px));""")
css = one(css, """  border-radius: 999px;
  background-size: cover;
  background-position: center;
  background-image: var(--hawk-face);
}""", """  background: var(--hawk-champ) center / contain no-repeat;
}""")

js = one(js, """    fab.setAttribute('aria-expanded', 'false');
""", """    fab.setAttribute('aria-expanded', 'false');
    /* The phone's Champ (2026-10-14): "Ask Me!" over the bird. Decorative; the button's name is its label. */
    var bub = make('span', 'hawk-fab__bub', 'Ask Me!'); bub.setAttribute('aria-hidden', 'true');
    var bird = make('span', 'hawk-fab__bird'); bird.setAttribute('aria-hidden', 'true');
    fab.appendChild(bub); fab.appendChild(bird);
""")
css_f.write_text(css); js_f.write_text(js)
print('website-hawk-champ-icon: applied')
