#!/usr/bin/env python3
"""Registration day, review fixes (follow-up to website-registration-day-2026-10-14.py; applies on f72f221).

1. Friends' days refresh: loadFriends() (TTL 2 min, 15 s after a failure) is now asked from repaint, from the tab
   coming back, when the sheet opens, and whenever the card is drawn; a failed load tries again by itself (15 s, up to
   six times). Before, a failed first load was never asked again and a loaded list never aged out.
2. retry() no longer pushes a stale local change over a newer row from another device: it runs loadMine() first, which
   compares the account's updated_at with when this device made the change (the same rule as sign-in).
3. A finished push only marks what is still current as saved. A newer save that began while it was in flight (RG.gen
   moved) or another account (reset) is left alone, and the storage key is captured before the await.
4. Focus: after Save / Clear it goes to the new "Change" / "Set day" button in the slot the sheet was opened from (or the
   banner's), not the detached one it left. reset() closes through closeModal (→ closeModalA11y). The sheet is no longer
   a dialog inside a dialog: #rgBack is the dialog (openModalA11y), labelled by the title.
5. Writes: only "the table/column isn't there" (42P01, PGRST205, 42703, PGRST204) is a schema gap. A 42501 / policy
   refusal is a failure: "Couldn’t save …" / "Not done yet — friends can still see your day …", never "cleared" or "saved".
   (Reads and the RPC keep the phone's wider schemaGap / rpcMissing fallbacks.)
6. Nits: a push that worked neither burns a RETRY_MAX slot nor leaves retryN counting; the time error is tied to the
   input (aria-invalid + aria-describedby; a missing day to the day group); the campus banner's "opens in N days" uses
   the same Pacific day as the card.

Usage: python3 website-registration-day-fixes-2026-10-14.py <repo>
"""
import sys, pathlib
root = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else '.')
f = root / 'index.html'
s = f.read_text()
if 'regday-fixes (2026-10-14)' in s:
    sys.exit('already patched')

def one(old, new):
    global s
    n = s.count(old)
    assert n == 1, (n, old[:120])
    s = s.replace(old, new)

def span(start, end, new):
    global s
    assert s.count(start) == 1 and s.count(end) == 1, (s.count(start), s.count(end), start[:60])
    a = s.index(start); b = s.index(end, a)
    s = s[:a] + new + s[b:]

# ---- state: friends' retry counter
one("var RG = { day: null, fr: null, frBusy: 0, gen: 0,", "var RG = { day: null, fr: null, frBusy: 0, frN: 0, gen: 0,")

# ---- keep(): the key can be captured before an await (regday-fixes (2026-10-14))
span("  function keep(v, pending) {\n", "  function readLocal() {", """  /* regday-fixes (2026-10-14): k is the key captured BEFORE an await, so an account switch mid-push never writes under the wrong one */
  function keep(v, pending, k) {
    k = k || key();
    try {
      if (!pending) { if (v) localStorage.setItem(k, JSON.stringify({ day: v.day, time: v.time, shared: v.shared })); else localStorage.removeItem(k); }
      else localStorage.setItem(k, JSON.stringify(v ? { day: v.day, time: v.time, shared: v.shared, at: Date.now(), pending: true } : { gone: true, at: Date.now(), pending: true }));
    } catch (_) {}
  }
""")

# ---- loadMine: a push that worked does not arm the retry timer
one("{ await push(loc.gone ? null : RG.day); armRetry(); repaint(); return; }",
    "{ var e0 = await push(loc.gone ? null : RG.day); if (e0) armRetry(); repaint(); return; }")

# ---- push: what counts as "the table isn't there" for a write, and only the current value is marked saved
span("  async function push(v) {\n", "  async function saveMine(v) {", """  /* a WRITE that says the table or a column is not there (RUN 17 not run). A 42501 / policy refusal is not that: it failed. */
  function writeGap(err) {
    var c = String((err && err.code) || '');
    return c === '42P01' || c === 'PGRST205' || c === '42703' || c === 'PGRST204';
  }
  async function push(v) {
    if (RG.gap) return null;
    var c = client(), u = user(); if (!c || !u) return null;
    var gen = RG.gen, k = key(), term = code(), q;
    try {
      q = v ? await c.from('registration_days').upsert({ user_id: u.id, term: term, day: v.day, at_time: v.time || null, shared: !!v.shared, updated_at: new Date().toISOString() }, { onConflict: 'user_id,term' })
        : await c.from('registration_days').delete().eq('user_id', u.id).eq('term', term);
    } catch (e) { q = { error: { message: String((e && e.message) || e) } }; }
    if (q.error) {
      if (writeGap(q.error)) { RG.gap = true; return null; }
      /* taking it away or hiding it: until it goes through, friends still see it — say so, never "saved" */
      return (!v || !v.shared) ? 'Not done yet — friends can still see your day until it goes through.' : 'Couldn’t save that to your account yet — it’s kept on this device.';
    }
    RG.retryN = 0;
    /* only what is still current is marked as saved: a newer save that began while this was in flight stays pending */
    var current = RG.gen === gen && !!user() && user().id === u.id && (v ? RG.day === v : !RG.day);
    if (current) { if (v) v.local = false; keep(v, false, k); }
    return null;
  }
""")

# ---- retry: look at the account first
span("  async function retry() {\n", "  function armRetry() {", """  async function retry() {
    if (!active() || RG.retrying || RG.gap) return;
    var loc = readLocal();
    if (!loc || !loc.pending) return;
    RG.retrying = 1;
    try {
      /* loadMine first: a newer day saved on another device wins over this device's older change, and it pushes ours when ours is newer */
      await loadMine();
      var l2 = readLocal();
      if (l2 && l2.pending && !RG.gap) armRetry(); else loadFriends(true);
      repaint();
    } finally { RG.retrying = 0; }
  }
""")

# ---- friends: a failed load tries again, a loaded list ages out
one("    else if (r.error) { if (was && was.rows) was.at = Date.now() - REG_TTL + REG_ERR_TTL; else RG.fr = { err: 1, at: Date.now() }; }",
    "    else if (r.error) {\n      if (was && was.rows) was.at = Date.now() - REG_TTL + REG_ERR_TTL; else RG.fr = { err: 1, at: Date.now() };\n      if (++RG.frN <= 6) setTimeout(function () { loadFriends(); }, REG_ERR_TTL + 250);\n    }")
one("      var seen = {};\n      RG.fr = { rows:", "      var seen = {}; RG.frN = 0;\n      RG.fr = { rows:")
one("    if (!RG.fr && !RG.frBusy) setTimeout(function () { loadFriends(); }, 0);", "    if (!RG.frBusy) setTimeout(function () { loadFriends(); }, 0);")
span("  function repaint() {\n", "\n  /* ---------------------------------------------------------------- the modal */", """  /* drawing the cards again must not drop the keyboard: the focused button (a card's, or the banner's) is found again */
  function focusKey() {
    var a = document.activeElement; if (!a || !a.closest) return null;
    var sl = a.closest('.rg-slot'); if (sl) return { slot: sl.getAttribute('data-rg'), act: a.getAttribute('data-rg-act'), id: a.getAttribute('data-id') };
    if (a.closest('#campusBanner') && /^regDayOpen/.test(a.getAttribute('onclick') || '')) return { banner: 1 };
    return null;
  }
  function refocus(k) {
    if (!k) return;
    var all = k.banner ? document.querySelectorAll('#campusBanner button[onclick^="regDayOpen"]') : document.querySelectorAll('.rg-slot[data-rg="' + k.slot + '"] [data-rg-act="' + k.act + '"]');
    for (var i = 0; i < all.length; i++) if (k.banner || (all[i].getAttribute('data-id') || null) === (k.id || null)) { try { all[i].focus({ preventScroll: true }); } catch (_) {} return; }
  }
  function repaint() {
    var fk = focusKey();
    try { var els = document.querySelectorAll('.rg-slot'); for (var i = 0; i < els.length; i++) els[i].innerHTML = cardHtml(els[i].getAttribute('data-rg')); } catch (_) {}
    try { if (typeof renderCampusBanner === 'function') renderCampusBanner(); } catch (_) {}
    try { if (M) paintModal(); } catch (_) {}
    refocus(fk);
    try { loadFriends(); } catch (_) {}
  }
""")
one("document.addEventListener('visibilitychange', function () { if (document.visibilityState === 'visible') retry(); });",
    "document.addEventListener('visibilitychange', function () { if (document.visibilityState === 'visible') { retry(); loadFriends(); } });")

# ---- Home / Plans drawing the whole rail or pane again (not only ours) must not drop the focused button either
one("  function slotHtml(where) { return '<div class=\"rg-slot\" data-rg=\"' + where + '\">' + cardHtml(where) + '</div>'; }",
    "  function slotHtml(where) {\n    var fk = focusKey(); if (fk && fk.slot === where) setTimeout(function () { refocus(fk); }, 0);   /* the caller is about to replace the node that holds focus */\n    return '<div class=\"rg-slot\" data-rg=\"' + where + '\">' + cardHtml(where) + '</div>';\n  }")

# ---- the sheet: one dialog, opened from somewhere, focus comes back
one("""      b.innerHTML = '<div class="modal rg-modal" id="rgModal" role="dialog" aria-modal="true" aria-labelledby="rgTitle"></div>';""",
    """      b.innerHTML = '<div class="modal rg-modal" id="rgModal"></div>';
      b.setAttribute('aria-labelledby', 'rgTitle');      /* #rgBack is the dialog (openModalA11y); the sheet inside is not a second one */""")
one("  function openModal() {\n    if (!active()) return;", "  function openModal(from) {\n    if (!active()) return;")
one("shared: m ? m.shared !== false : true, err: '', busy: 0 };",
    "shared: m ? m.shared !== false : true, err: '', errField: '', busy: 0, from: typeof from === 'string' ? from : '' };\n    loadFriends();")
one("if (f) setTimeout(function () { try { f.focus({ preventScroll: true }); } catch (_) {} }, 60);",
    "if (f) setTimeout(function () { if (!M) return; try { f.focus({ preventScroll: true }); } catch (_) {} }, 60);")
one("    if (a === 'open') openModal();", "    if (a === 'open') { var sl = t.closest('.rg-slot'); openModal(sl ? sl.getAttribute('data-rg') : ''); }")
one("  function toast(m) { try { frToast(m); } catch (_) {} }", """  function toast(m) { try { frToast(m); } catch (_) {} }
  /* the card was drawn again while the sheet was open, so the button the sheet came from is gone: focus its replacement */
  function restoreFocus(from) {
    try {
      var a = document.activeElement; if (a && a !== document.body && a.isConnected) return;
      var sel = from === 'banner' ? '#campusBanner button[onclick^="regDayOpen"]' : from ? '.rg-slot[data-rg="' + from + '"] [data-rg-act="open"]' : '[data-rg-act="open"]';
      var all = document.querySelectorAll(sel);
      for (var i = 0; i < all.length; i++) if (all[i].offsetParent !== null) { all[i].focus({ preventScroll: true }); return; }
    } catch (_) {}
  }""")
one("    var mm = M; M.busy = 1; M.err = ''; paintModal();", "    var mm = M, from = M.from; M.busy = 1; M.err = ''; M.errField = ''; paintModal();")
one("    repaint(); loadFriends(true);\n  }", "    repaint(); loadFriends(true); restoreFocus(from);\n  }")
one("    var mm = M; M.busy = 1; paintModal();\n    var e; try { e = await saveMine(null);", "    var mm = M, from = M.from; M.busy = 1; paintModal();\n    var e; try { e = await saveMine(null);")
one("    toast(e || 'Your registration day is cleared'); repaint();", "    toast(e || 'Your registration day is cleared'); repaint(); restoreFocus(from);")
one("{ M.err = 'Pick your day first.'; return paintModal(); }", "{ M.err = 'Pick your day first.'; M.errField = 'day'; return paintModal(); }")
one("{ M.err = 'That time doesn’t look right — try 11a or 2:30p.'; return paintModal(); }", "{ M.err = 'That time doesn’t look right — try 11a or 2:30p.'; M.errField = 'time'; return paintModal(); }")
one("""role="group" aria-label="Your day">""", """role="group" aria-label="Your day"' + (M.err && M.errField === 'day' ? ' aria-describedby="rgErr"' : '') + '>""")
one("""data-rg-key="time" placeholder="11a" value="' + esc(M.time) + '">""", """data-rg-key="time" placeholder="11a" value="' + esc(M.time) + '"' + (M.err && M.errField === 'time' ? ' aria-invalid="true" aria-describedby="rgErr"' : '') + '>""")

# ---- sign-out / account switch: the sheet closes the ordinary way
one("    clearTimeout(RG.retryT); RG.retryT = null; M = null;\n    var b = document.getElementById('rgBack'); if (b && b.classList.contains('open')) { b.classList.remove('open'); document.body.style.overflow = document.querySelector('.mback.open') ? 'hidden' : ''; }\n    repaint();",
    "    clearTimeout(RG.retryT); RG.retryT = null; RG.frN = 0;\n    var b = document.getElementById('rgBack'); if (b && b.classList.contains('open')) closeModal(); else M = null;\n    repaint();")

# ---- the banner: the same Pacific day as the card, and its button says where the sheet came from
one("  window.regDayBoot = boot;", "  window.regPacificGap = function (d) { return gap(today(), d); };\n  window.regDayBoot = boot;")
one("""onclick="regDayOpen()">'+regDayLabel()""", """onclick="regDayOpen(&quot;banner&quot;)">'+regDayLabel()""")
one("  const regIn=daysUntil(c.REGISTRATION_OPENS);", "  const regIn=(typeof regPacificGap==='function'&&c.REGISTRATION_OPENS)?regPacificGap(c.REGISTRATION_OPENS):daysUntil(c.REGISTRATION_OPENS);   /* regday-fixes (2026-10-14): Pacific, like the card */")

f.write_text(s)
print('patched', f)
