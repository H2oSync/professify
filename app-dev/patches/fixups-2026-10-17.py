"""Review fixups 2026-10-17 (exact anchors, replayable after the 4 batch patches)."""
import sys
P='index.html'
s=open(P,encoding='utf-8').read()
if 'fixups-2026-10-17' in s: print('already patched'); sys.exit(0)
def one(old,new):
    global s
    assert s.count(old)==1,(old[:70],s.count(old)); s=s.replace(old,new)
# 1. a chat link like ?p=constructor must not match Object.prototype keys
one("  if(PROFESSORS[key])return key;                                   // exact id",
    "  if(Object.prototype.hasOwnProperty.call(PROFESSORS,key))return key; // exact id (own keys only: fixups-2026-10-17)")
one("    var p=PROFESSORS[id]; if(!p)continue;\n    if(dlSlug(id)===want",
    "    if(!Object.prototype.hasOwnProperty.call(PROFESSORS,id))continue;\n    var p=PROFESSORS[id]; if(!p)continue;\n    if(dlSlug(id)===want")
# 2. cap how much of a message the linkifier scans
one("  if(text.indexOf('//')<0)return msgEsc(text);\n  var re=new RegExp(MSG_URL_RE.source,'gi')",
    "  if(text.indexOf('//')<0)return msgEsc(text);\n  if(text.length>8000)return msgEsc(text);   /* fixups-2026-10-17: very long bodies stay plain text */\n  var re=new RegExp(MSG_URL_RE.source,'gi')")
# 3. shared-week id must be a card id before it becomes a storage path
one("  if(!base||!id)return '';\n  return base+'/storage/v1/object/public/'+SC_BUCKET+'/'",
    "  if(!base||!id)return '';\n  if(!/^[a-z0-9-]{16,64}(\\.png|\\.json)?$/.test(String(id)))return '';   /* fixups-2026-10-17 */\n  return base+'/storage/v1/object/public/'+SC_BUCKET+'/'")
open(P,'w',encoding='utf-8').write(s); print('patched index.html')
