#!/usr/bin/env python3
"""2026-10-30 (stuck/can't edit pass): Accept and Decline had no busy guard — a double tap sent two PATCHes (or
DELETEs) and showed two toasts. Message (openChatWith) → TC.threadWith on a double tap made two direct chats with the
same friend before either came back. Accept/Decline now ignore a second tap on the same request while the first is
out; TC.threadWith hands every caller the SAME in-flight promise per friend, and Message ignores its own second tap."""
import sys, pathlib
p = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else 'app/index.html'); s = p.read_text()
def one(a, b):
    global s
    n = s.count(a); assert n == 1, (a[:70], n); s = s.replace(a, b)
one("""  acceptReq: async id => { if (await TC.acceptRequest(id)) { toast(`You and ${PEOPLE[id].short} are now friends`); relinkPeople(); } render(true); },
  declineReq: async id => { if (await TC.declineRequest(id)) toast('Request declined'); render(true); },""",
    """  acceptReq: async id => { const k = 'rq' + id; if (UI.busy[k]) return; UI.busy[k] = 1; let okA = false; try { okA = await TC.acceptRequest(id); } finally { UI.busy[k] = 0; } if (okA) { toast(`You and ${PEOPLE[id].short} are now friends`); relinkPeople(); } render(true); },
  declineReq: async id => { const k = 'rq' + id; if (UI.busy[k]) return; UI.busy[k] = 1; let okD = false; try { okD = await TC.declineRequest(id); } finally { UI.busy[k] = 0; } if (okD) toast('Request declined'); render(true); },""")
one("""  openChatWith: async pid => { UI.champ = false; const id = await TC.threadWith(pid); if (id) A.openChat(id); },""",
    """  openChatWith: async pid => { UI.champ = false; const k = 'cw' + pid; if (UI.busy[k]) return; UI.busy[k] = 1; let id = null; try { id = await TC.threadWith(pid); } finally { UI.busy[k] = 0; } if (id) A.openChat(id); },""")
one("""/* One direct thread per pair: find it before making one. */
TC.threadWith = async function (uid) {""",
    """/* One direct thread per pair: find it before making one. Callers that ask while one is being made get that same
   one (2026-10-30: a double tap on Message made two). */
TC.threadWith = function (uid) {
  TC.thwIn = TC.thwIn || {};
  if (TC.thwIn[uid]) return TC.thwIn[uid];
  const p = TC.threadWith0(uid); TC.thwIn[uid] = p;
  const done = () => { if (TC.thwIn[uid] === p) delete TC.thwIn[uid]; }; p.then(done, done);
  return p;
};
TC.threadWith0 = async function (uid) {""")
p.write_text(s); print('friends-double-tap applied')
