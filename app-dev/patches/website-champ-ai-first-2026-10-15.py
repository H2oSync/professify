"""Champ asks the model first, every time (2026-10-15). Run after website-champ-cards-2026-10-15.py:  python3 <this> <repo>

Owner: "send to ai every time". The cards patch answered the lookups (free time, my day, who is free, does X fit, best professor for
X) in the browser before the model was asked — which broke the site's 2026-09-23 AI-first rule. This puts the rule back:

 - Every question — typed, a chip under a card, a follow-up, a tap on a day of the week card — goes to the `ask` function first.
   The model only NAMES a tool; the card is still drawn from the site's own data (answerFromTool), nothing on it is model text.
 - The device is the FALLBACK, as before: signed out, no session, the call failing or timing out, fallback:'search', or the gate
   refusing all give null, and then the question is answered from the device — its own reading of a lookup (localIntent, which
   only ever runs as that fallback now) or the router's, whichever the old rule would have used.
 - A model that says it cannot answer, or answers go_to, still loses to the device's clean reading (pickAnswer, unchanged).
 - What stays on the device without asking, exactly as before: a refusal, a screen name, a bare course code or professor, and a
   follow-up that merges into the last search ("what about tuesday" right after a section search — Tate: follow-ups are client-side).
 - One new case: a question the device reads as a lookup is never skipped for being "out of scope" or a router refusal.
Also bumps the build stamp (PROFESSIFY_BUILD, sw.js BUILD and the three hawk ?v= digits move together).
"""
import sys, re, pathlib
root = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else '.')
js_f = root / 'hawk-ask.js'; js = js_f.read_text()
idx_f = root / 'index.html'; idx = idx_f.read_text()
sw_f = root / 'sw.js'; sw = sw_f.read_text()
def one(s, old, new):
    n = s.count(old); assert n == 1, (n, old[:90]); return s.replace(old, new)

js = one(js, """    /* The shapes that are a lookup (free time, my day, who is free, does X fit, best professor for X) are answered here, in the
       browser, before the router or the model is asked: they work offline and signed out, and the chips under a card use them. */
    var near = localIntent(q, cat);
    if (near) { readings = { local: near, model: null }; render(q, near, cat); return; }
    var result = R.route(q, cat);
    var fu = buildFollowUp(q, result) || followUp(result);
    if (fu) result = fu;

    if (skipsModel(result) || !result.in_scope || !aiUrl()) {
      readings = { local: result, model: null };
      render(q, result, cat);
      return;
    }
    var thinking = renderThinking(q);
    askModel(q).then(function (viaModel) {
      if (!thinking.isConnected) return;            // they cleared the chat meanwhile
      readings = { local: result, model: viaModel };
      render(q, pickAnswer(viaModel, result), cat, thinking);
    });
  }""", """    /* AI-FIRST (owner, 2026-10-15: "send to ai every time"). A lookup the device can read (free time, my day, who is free, does X
       fit, best professor for X — localIntent) goes to the model like any other question; the device's reading is only what is
       shown when the model cannot be used or has nothing clean to say. A follow-up that narrows the last search stays on the device. */
    var result = R.route(q, cat);
    var fu = buildFollowUp(q, result) || followUp(result);
    var near = localIntent(q, cat);
    if (near) fu = null;
    if (fu) result = fu;
    var device = near || result;
    var toModel = near ? true : !(skipsModel(result) || !result.in_scope);

    if (!toModel || !aiUrl()) {
      readings = { local: device, model: null };
      render(q, device, cat);
      return;
    }
    var thinking = renderThinking(q);
    askModel(q).then(function (viaModel) {
      if (!thinking.isConnected) return;            // they cleared the chat meanwhile
      readings = { local: device, model: viaModel };
      render(q, pickAnswer(viaModel, device), cat, thinking);
    });
  }""")
js = one(js, """  /* ---- questions answered here before the model is asked: the shape is unmistakable and the answer is a lookup
     (the phone's chIntent, 2026-10-08). They also work signed out and offline, and the chips under a card are asked
     through them, so a follow-up never needs a round trip. ---- */""", """  /* ---- the device's own reading of a lookup: the shape is unmistakable and the answer is a lookup (the phone's chIntent,
     2026-10-08). Since 2026-10-15 (AI-first) it is only the FALLBACK — what answer() shows when the model could not be asked
     (signed out, no session, the call failed, fallback:'search', the gate) — and the reading kept when the model has nothing
     clean to say. The question itself always goes to the model first. ---- */""")

STAMP = '2026-10-15 18:31'; DIGITS = re.sub(r'\D', '', STAMP)
m = re.search(r"window\.PROFESSIFY_BUILD='([0-9: -]+)';", idx); assert m
OLD = m.group(1); OLDD = re.sub(r'\D', '', OLD)
idx = one(idx, "window.PROFESSIFY_BUILD='" + OLD + "';", "window.PROFESSIFY_BUILD='" + STAMP + "';")
sw = one(sw, "const BUILD = '" + OLD + "';", "const BUILD = '" + STAMP + "';")
for a in ('hawk-ask.css', 'hawk-router.js', 'hawk-ask.js'):
    idx = one(idx, a + '?v=' + OLDD + '"', a + '?v=' + DIGITS + '"')

js_f.write_text(js)
idx_f.write_text(idx)
sw_f.write_text(sw)
