#!/usr/bin/env python3
"""Swipe a chat left to Pin or Delete it; no ⋯ in a chat (Tate, 2026-10-04, on the Friends tab's Chats list:
"you can pin and delete chats by swiping to the left on these take out the 3 dots in the chat").

- Swipe a row in Chats to the left and two buttons slide out from the right edge: Pin (blue) and Delete (red),
  like Messages / Instagram. Past halfway it stays open; a tap anywhere else, or swiping back, closes it.
  A tap on an open row only closes it, it never opens the chat. Vertical scrolling still works (pan-y).
  Works with a mouse drag too, for the Desktop preview.
- Pin: the chat moves to the top of Chats and keeps a small pin by its time; up to 3 pinned, in the order pinned.
  Pins are kept on this phone, per account (like recent searches) — nothing is sent to the server, no SQL.
  Unpin from the same swipe ("Unpin").
- Delete opens the same "Delete this chat?" confirm as before (for you only; it comes back with a new message).
  Without the chat SQL, the row shows only Pin.
- Holding a chat still opens its menu (See their page / Pin / Delete) — the way in for a keyboard or VoiceOver.
- In a chat, the ⋯ at the top right is gone. Tapping the name opens the person's page in a 1:1 (Report, Block,
  Remove friend in its ⋯) and the group's sheet in a group (who's in it, Pin, Delete, Leave, Report the name).
  Holding a chat in the list opens the same sheet.

Applies after remove-friend-2026-10-04.py (on the 18:00 line).
Usage: python3 chat-swipe-2026-10-04.py <repo-dir>   (edits <repo-dir>/app/index.html)
"""
import sys, os
p = os.path.join(sys.argv[1], 'app', 'index.html')
s = open(p, encoding='utf-8').read()
if 'function swipeRow' in s: sys.exit('already patched')
R = [
 # CSS
 (".thread+.thread{border-top:1px solid var(--line)}\n",
  ".thread+.thread{border-top:1px solid var(--line)}\n"
  "/* swipe a chat left: Pin / Delete (Tate, 2026-10-04) */\n"
  ".swrow{position:relative;overflow:hidden}\n"
  ".swrow+.swrow{border-top:1px solid var(--line)}\n"
  ".swrow:first-child{border-radius:24px 24px 0 0}.swrow:last-child{border-radius:0 0 24px 24px}.swrow:only-child{border-radius:24px}\n"
  ".swrow > .thread{position:relative;z-index:1;background:#fff;touch-action:pan-y;transition:transform .22s cubic-bezier(.2,.8,.2,1)}\n"
  ".swrow.drag > .thread{transition:none}\n"
  ".swacts{position:absolute;top:0;right:0;bottom:0;display:flex}\n"
  ".swacts button{width:76px;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:4px;color:#fff;font-weight:800;font-size:13px}\n"
  ".swacts .swpin{background:#2563EB}.swacts .swdel{background:#DC2626}\n"
  ".thread .tmt{display:inline-flex;align-items:center;gap:4px}\n"
  ".thread .pinm{display:inline-flex;color:var(--muted)}\n", 1),
 # time column gets the pin mark
 ("<div class=\"tm\">${last ? agoText(last.created_at) : ''}",
  "<div class=\"tm\"><span class=\"tmt\">${chatPinned(t.id) ? `<span class=\"pinm\" role=\"img\" aria-label=\"Pinned\">${ic('pin', 12, 2.4)}</span>` : ''}${last ? agoText(last.created_at) : ''}</span>", 1),
 # Chats list: pinned first, each row swipeable
 ("  else if (ts.length) chats = `<div class=\"card\" style=\"margin:0 16px;padding:2px 0\">${ts.map(threadRow).join('')}</div>`;",
  "  else if (ts.length) { const pr = t => { const i = chatPins().indexOf(String(t.id)); return i < 0 ? 99 : i; }; chats = `<div class=\"card\" style=\"margin:0 16px;padding:0\">${ts.slice().sort((a, b) => pr(a) - pr(b)).map(swipeRow).join('')}</div>`; }", 1),
 # helpers before threadRow
 ("function threadRow(t) {\n",
  "/* Pinned chats (Tate, 2026-10-04): kept on this phone, per account, in the order pinned, up to 3. */\n"
  "const CHAT_PIN_MAX = 3;\n"
  "function chatPinKey() { return 'tc-chat-pins-' + (TC.user ? TC.user.id : ''); }\n"
  "function chatPins() { try { const v = JSON.parse(localStorage.getItem(chatPinKey()) || '[]'); return Array.isArray(v) ? v.map(String) : []; } catch (e) { return []; } }\n"
  "function chatPinned(id) { return chatPins().includes(String(id)); }\n"
  "/* pins of chats that are still in your Chats list (a deleted or vanished chat's pin doesn't count) */\n"
  "function chatPinsLive() { const live = new Set(TC.threads.filter(t => !chatCleared(t)).map(t => String(t.id))); return chatPins().filter(x => live.has(x)); }\n"
  "function chatPinSet(list) { try { localStorage.setItem(chatPinKey(), JSON.stringify(list)); return true; } catch (e) { return false; } }\n"
  "/* A chat row you can swipe left for Pin / Delete. */\n"
  "const SW = { el: null, x0: 0, y0: 0, dx: 0, dir: null, base: 0, open: null, until: 0 };\n"
  "function swipeRow(t) {\n"
  "  const pinned = chatPinned(t.id), del = TC.chatX.on !== false;\n"
  "  return `<div class=\"swrow\" data-cid=\"${esc(String(t.id))}\" data-w=\"${del ? 152 : 76}\"><div class=\"swacts\"><button class=\"swpin\" data-a=\"pinChat\" data-x=\"${esc(String(t.id))}\" tabindex=\"-1\" aria-label=\"${pinned ? 'Unpin' : 'Pin'} ${esc(threadName(t))}\">${ic('pin', 20, 2.2)}${pinned ? 'Unpin' : 'Pin'}</button>${del ? `<button class=\"swdel\" data-a=\"swDelChat\" data-x=\"${esc(String(t.id))}\" tabindex=\"-1\" aria-label=\"Delete ${esc(threadName(t))}\">${ic('trash', 20, 2.2)}Delete</button>` : ''}</div>${threadRow(t)}</div>`;\n"
  "}\n"
  "function swSet(row, x, anim) { const th = row && row.querySelector(':scope > .thread'); if (!th) return; row.classList.toggle('drag', !anim); th.style.transform = x ? `translateX(${x}px)` : ''; }\n"
  "/* close the open row; true only when one was really open on screen (a re-render drops the slide) */\n"
  "function swClose() { if (!SW.open) return false; const row = document.querySelector(`#fbody .swrow[data-cid=\"${CSS.escape(SW.open)}\"]`), th = row && row.querySelector(':scope > .thread'); SW.open = null; if (!th || !th.style.transform) return false; swSet(row, 0, true); return true; }\n"
  "function threadRow(t) {\n", 1),
 # with the ⋯ gone, a group's name opens its sheet (who's in it, Pin, Delete, Leave, Report the name) —
 # the iMessage / Instagram way; a 1:1's name already opens the person's page (Report, Block, Remove friend there)
 ("<div class=\"grow\"><div style=\"font-weight:900;font-size:16.5px\">${esc(threadName(t))}</div><div class=\"muted b\" style=\"font-size:12.5px\">${t.members.length} member${t.members.length === 1 ? '' : 's'}</div></div>`;",
  "<button class=\"grow\" style=\"text-align:left\" data-a=\"chatMenu\" data-x=\"${esc(id)}\" aria-label=\"${esc(threadName(t))}: people and options\"><div style=\"font-weight:900;font-size:16.5px\">${esc(threadName(t))}</div><div class=\"muted b\" style=\"font-size:12.5px\">${t.members.length} member${t.members.length === 1 ? '' : 's'} ›</div></button>`;", 1),
 # chat header loses its ⋯
 ("${head}<button class=\"iconbtn\" style=\"width:38px;height:38px;flex:none\" data-a=\"chatMenu\" data-x=\"${esc(id)}\" aria-label=\"Chat options\">${ic('dots', 20, 2, 'currentColor')}</button></div>`",
  "${head}</div>`", 1),
 # a deleted chat drops its pin
 ("    TC.clears[cid] = at; t.last = null; UI.sheet = null;\n",
  "    TC.clears[cid] = at; t.last = null; UI.sheet = null;\n    if (chatPinned(cid)) chatPinSet(chatPins().filter(x => x !== String(cid)));\n", 1),
 # the held-chat menu gets Pin / Unpin too
 (" ${TC.chatX.on !== false ? `<button class=\"li danger\" data-a=\"chatDelAsk\" data-x=\"${esc(cid)}\">",
  " <button class=\"li\" data-a=\"pinChat\" data-x=\"${esc(cid)}\">${ic('pin', 20, 2.2)}<span class=\"grow b\">${chatPinned(cid) ? 'Unpin chat' : 'Pin chat'}</span></button>\n"
  " ${TC.chatX.on !== false ? `<button class=\"li danger\" data-a=\"chatDelAsk\" data-x=\"${esc(cid)}\">", 1),
 # actions
 ("  chatDelAsk: cid => { UI.sheet = { type: 'chatDel', cid }; render(true); },\n",
  "  chatDelAsk: cid => { UI.sheet = { type: 'chatDel', cid }; render(true); },\n"
  "  pinChat: cid => {\n"
  "    cid = String(cid); const list = chatPinsLive(), on = list.includes(cid);\n"
  "    if (!on && list.length >= CHAT_PIN_MAX) { toast(`You can pin up to ${CHAT_PIN_MAX} chats`); swClose(); return; }\n"
  "    if (!chatPinSet(on ? list.filter(x => x !== cid) : list.concat([cid]))) { toast('Couldn’t pin on this phone'); return; }\n"
  "    SW.open = null; if (UI.sheet && UI.sheet.type === 'chatAct') UI.sheet = null; render(true); toast(on ? 'Unpinned' : 'Pinned');\n"
  "  },\n"
  "  swDelChat: cid => { SW.open = null; UI.sheet = { type: 'chatDel', cid }; render(true); },\n", 1),
 # gesture handling (pointer events: touch and mouse), before the stories block
 ("/* ================= stories: today, most free first (Tate, 2026-09-30) ================= */\n",
  "/* Swipe a chat left (Tate, 2026-10-04). Horizontal drags on a Chats row slide it; past half the buttons'\n"
  "   width it stays open. A drag cancels a hold; the click a drag ends with is not a tap. */\n"
  "(function () {\n"
  "  const sc = document.getElementById('scroll'); if (!sc) return;\n"
  "  const rowOf = el => el && el.closest ? el.closest('#fbody .swrow') : null;\n"
  "  sc.addEventListener('pointerdown', e => {\n"
  "    if (e.pointerType === 'mouse' && e.button !== 0) return;\n"
  "    const row = rowOf(e.target); if (!row || (e.target.closest && e.target.closest('.swacts'))) { SW.el = null; return; }\n"
  "    /* start from where the row is drawn: a redraw (a new message, the minute tick) closes an open row */\n"
  "    const m = /translateX\\((-?[\\d.]+)px\\)/.exec((row.querySelector(':scope > .thread') || {}).style ? row.querySelector(':scope > .thread').style.transform : '');\n"
  "    SW.el = row; SW.x0 = e.clientX; SW.y0 = e.clientY; SW.dx = 0; SW.dir = null; SW.base = m ? Number(m[1]) : 0;\n"
  "    if (!SW.base && SW.open === row.dataset.cid) SW.open = null;\n"
  "  }, { passive: true });\n"
  "  const move = e => {\n"
  "    const row = SW.el; if (!row) return;\n"
  "    if (e.pointerType === 'mouse' && !(e.buttons & 1)) return end();\n"
  "    const dx = e.clientX - SW.x0, dy = e.clientY - SW.y0;\n"
  "    if (!SW.dir) { if (Math.abs(dx) < 8 && Math.abs(dy) < 8) return; SW.dir = Math.abs(dx) > Math.abs(dy) ? 'h' : 'v'; if (SW.dir === 'h') { clearTimeout(LP.t); LP.el = null; if (SW.open && SW.open !== row.dataset.cid) swClose(); } }\n"
  "    if (SW.dir !== 'h') return;\n"
  "    const w = Number(row.dataset.w); SW.dx = dx; swSet(row, Math.max(-w - 24, Math.min(0, SW.base + dx)), false);\n"
  "  };\n"
  "  const end = () => {\n"
  "    const row = SW.el; SW.el = null; if (!row || SW.dir !== 'h') return;\n"
  "    const w = Number(row.dataset.w), x = Math.max(-w, Math.min(0, SW.base + SW.dx)), open = x < -w / 2;\n"
  "    SW.open = open ? row.dataset.cid : (SW.open === row.dataset.cid ? null : SW.open); swSet(row, open ? -w : 0, true); SW.until = Date.now() + 350;\n"
  "  };\n"
  "  document.addEventListener('pointermove', move, { passive: true });\n"
  "  document.addEventListener('pointerup', end); document.addEventListener('pointercancel', end);\n"
  "  /* while a row is open, a tap elsewhere only closes it; the click a drag ends with is not a tap */\n"
  "  window.addEventListener('click', e => {\n"
  "    const inActs = e.target.closest && e.target.closest('#fbody .swacts');\n"
  "    if (Date.now() < SW.until && !inActs) { e.stopImmediatePropagation(); e.preventDefault(); return; }\n"
  "    if (SW.open && !inActs && swClose()) { e.stopImmediatePropagation(); e.preventDefault(); }\n"
  "  }, true);\n"
  "})();\n"
  "/* ================= stories: today, most free first (Tate, 2026-09-30) ================= */\n", 1),
]
# the pin icon: reuse the stories' pin when a build has one (17:00 added it), so the two pins match and the
# icon table never has the key twice
_ib = s.index('const I={'); _ie = s.index('\n};', _ib)
if "\n pin:'" not in s[_ib:_ie]:
    R.insert(0, ("const I={\n", "const I={\n pin:'<path d=\"M12 16.5V22\"/><path d=\"M8.5 3h7l-1 6.5 3.5 3.5V15h-12v-2l3.5-3.5z\"/>',\n", 1))
for a, b, n in R:
    if s.count(a) != n: sys.exit(f'anchor matched {s.count(a)}x (want {n}): {a[:90]}')
    s = s.replace(a, b)
open(p, 'w', encoding='utf-8').write(s)
print('patched', p)
