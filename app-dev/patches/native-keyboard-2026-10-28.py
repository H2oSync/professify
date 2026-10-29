#!/usr/bin/env python3
"""Tate, 2026-10-28, on the iPhone app's keyboard (Friends search): "it kind of uses safari tone is
there a way to use a better like linkin typing one". Two things made it look like Safari:
  1. WKWebView's form bar (^ v ✓) above the keyboard;
  2. the keyboard followed the phone's dark mode while the app was light.
With @capacitor/keyboard in ios-app (8.0.6; resize "native", the plugin default — the web view ends at the keyboard, so a
focused field and the chat box sit right above it), the iPhone app hides
the bar and sets the keyboard's light/dark from the app's own theme. On the web, and in an app build
without the plugin, nothing happens."""
import sys, pathlib
p = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else 'app/index.html'); s = p.read_text()
def one(a, b):
    global s
    n = s.count(a); assert n == 1, (a[:60], n); s = s.replace(a, b)
one("""  sync();
  new MutationObserver(sync).observe(document.head, { subtree: true, attributes: true, attributeFilter: ['content'] });
  } catch (e) {}
""", """  sync();
  new MutationObserver(sync).observe(document.head, { subtree: true, attributes: true, attributeFilter: ['content'] });
  } catch (e) {}
  try {
  /* The keyboard (Tate, 2026-10-28: "like linkedin", not Safari): no ^ v ✓ bar above it, and its
     light/dark follows the app's theme rather than the phone's. Needs @capacitor/keyboard in the app
     build; a build without it ignores this (every call is caught). */
  var KB = (C.Plugins && C.Plugins.Keyboard) || null, kbLast = '';
  var quiet = function (r) { if (r && typeof r.catch === 'function') r.catch(function () {}); };
  if (KB) {
    try { quiet(KB.setAccessoryBarVisible({ isVisible: false })); } catch (e) {}
    var kb = function () {
      var st = document.documentElement.getAttribute('data-theme') === 'dark' ? 'DARK' : 'LIGHT';
      if (st === kbLast) return; kbLast = st;
      try { quiet(KB.setStyle({ style: st })); } catch (e) {}
    };
    kb();
    new MutationObserver(kb).observe(document.documentElement, { attributes: true, attributeFilter: ['data-theme'] });
  }
  } catch (e) {}
""")
p.write_text(s); print('native-keyboard applied')
