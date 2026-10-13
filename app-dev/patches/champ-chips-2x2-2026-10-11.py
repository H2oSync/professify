import sys
p=sys.argv[1] if len(sys.argv)>1 else 'repo/app/index.html'
s=open(p).read()
def rep(a,b):
    global s
    assert s.count(a)==1,(s.count(a),a[:60]); s=s.replace(a,b)
rep("""  const first = personSecs('me')[0];
  const sugg = [first ? ['cc1', 'Best professor for ' + first.code] : ['cc1', 'Open CSC classes after 10am'], ['cc2', "Who's free right now?"], ['cc3', 'My game plan for Plan A'], ['cc4', 'What’s my day look like?']];
  const chips = `<div class="cchips">${sugg.slice(0, m.length ? 4 : 3).map(""",
"""  /* Four broad questions Champ answers on the phone or through its tools (Tate, 2026-10-11): shown 2 x 2 on the first sheet. */
  const sugg = [['cc1', 'When am I free this week?'], ['cc2', "Who's free right now?"], ['cc3', 'What’s my day look like?'], ['cc4', 'My best professor']];
  const chips = `<div class="cchips">${sugg.map(""")
rep("""${chips}<div style="height:16px"></div>${input}</div>`;""","""${chips.replace('class="cchips"', 'class="cchips cgrid"')}<div style="height:16px"></div>${input}</div>`;""")
rep(""".cc1{background:var(--purple-soft)""",""".cchips.cgrid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:8px}
.cgrid .cchip{white-space:normal;height:auto;min-height:36px;padding:7px 8px;border-radius:18px;font-size:13px;line-height:1.2;text-align:center;text-wrap:balance}
.cc1{background:var(--purple-soft)""")
open(p,'w').write(s)
