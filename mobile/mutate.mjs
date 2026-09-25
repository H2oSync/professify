import fs from 'node:fs'; import { execFileSync } from 'node:child_process';
const src = fs.readFileSync('build.html', 'utf8');
const M = [
  ['M01 viewport-fit dropped', 'initial-scale=1.0, viewport-fit=cover">', 'initial-scale=1.0">'],
  ['M02 header ignores the status bar', 'header.nav{padding-top:env(safe-area-inset-top)}', 'header.nav{}'],
  ['P01 switch stacked under the search', '.ex-top{flex-direction:row;align-items:stretch;gap:10px;margin:12px 0 10px}', '.ex-top{flex-direction:column;align-items:stretch;gap:10px;margin:12px 0 10px}'],
  ['P02 chips back to 34px', '.ex-top-l .ex-gesw button{height:42px;', '.ex-top-l .ex-gesw button{height:34px;'],
  ['P03 facts line kept beside a description', "${(desc&&!seatFrag)?'':facts}", '${facts}'],
  ['P04 prerequisite sentence printed as the description', 'var skip=/^(pre|co)-?requisites?\\b|', 'var skip=/^zzz|'],
  ['P05 long descriptions never cut', 'if(s.length>96){', 'if(s.length>9999){'],
  ['P06 trailing full stop kept', "s=s.replace(/[.\\s]+$/,'');", ''],
  ['P07 Saved view never shown', "if(window.exSaved&&exMode!=='professors'&&!(exQuery||'').trim()&&typeof exSavedHtml==='function'){ out.innerHTML=exSavedHtml(); return; }", ''],
  ['P08 switching sides keeps Saved', 'function setExMode(m){\n  exMode=m;\n  window.exSaved=false;\n', 'function setExMode(m){\n  exMode=m;\n'],
  ['P09 Professors not purple', '.ex-seg-v:has(#ex-profs.active) .ex-seg-thumb{background:var(--prof)}', ''],
  ['P10 long heading never used', "if(label==='Recommended for your major'&&major){", "if(label==='zzz'&&major){"],
  ['P11 long heading leaks to desktop', '.ex-head .ex-eb,.ex-head .ex-ht,.ex-head .ex-hs{display:none}', ''],
  ['P12 chips never report pressed', "aria-pressed=\"'+on+'\"", 'aria-pressed="false"'],
  ['P13 long placeholder on a phone', "(typeof exPlaceholder==='function'&&window.innerWidth<=640) ?", "(false) ?"],
  ['P14 My major never lit', "_chip(exMode==='classes'&&!_sv,", '_chip(false,'],
  ['P15 catalog read ignored', 'if(line){ map[code]=line; n++; }', ''],
  ['R1 naive sentence split', 'var parts=csSentences(t);', "var parts=t.split('. ');"],
  ['R2 descriptions on every row', "const desc=(opts&&opts.desc)?shortDesc(c.code):'';", 'const desc=shortDesc(c.code);'],
  ['R3 partial catalog published', 'if(!res.ok)return;', 'if(!res.ok){complete=true;break;}'],
  ['R4 quarter-era rows accepted', "if(!/^[A-Z]{2,5} \\d{4}[A-Z]?$/.test(code))return;", ''],
  ['R5 typing keeps Saved lit', "if(window.exSaved&&exQuery.trim()){window.exSaved=false;try{renderExContext();}catch(e){}}", ''],
  ['R7 Roman numeral read as an initial', "(/^[A-Za-z]$/.test(w)&&!/^[IVX]$/.test(w))", '(/^[A-Za-z]$/.test(w))'],
  ['R8 requirement clause not cut', 'if(rq>0)s=s.slice(0,rq);', ''],
  ['R9 page chrome kept', 'if(!CS_CHROME.test(t))return t;', 'return t;'],
  ['R10 chrome with no label shown', "if(!l)return '';", 'if(!l)return t;'],
  ['R11 last label taken', 'var l=lab.exec(t);', 'var l=null,x; while((x=lab.exec(t)))l=x;'],
  ['R11b label searched from the start', 'lab.lastIndex=end;', ''],
  ['R11c seat-row status not chrome', '|(Open|Closed|Wait List) \\d+ \\d+/g, m, end=0;', '/g, m, end=0;'],
  ['R12 Solano note not lifted', "t=t.replace(/^offered at solano campus\\.\\s*/i,'');", ''],
  ['R13 Formerly/Solano/Repeatable not skipped', '|^offered (at|in|only)\\b|^formerly\\b|^also offered as\\b|^repeatable\\b|^the class schedule will list\\b', ''],
  ['R14 "1 laboratory" not skipped', 'laborator(y|ies)|activit(y|ies)', 'laborator|activit'],
  ['R15 short fragment stands alone', 'for(var k=1;k<keep.length&&', 'for(var k=1;false&&k<keep.length&&'],
  ['R16 bracket left open', "var op=s.lastIndexOf('('); if(op>s.lastIndexOf(')')&&op>=20)s=s.slice(0,op);", ''],
  ['R17 lower-case start kept', 'var s=keep[0].charAt(0).toUpperCase()+keep[0].slice(1);', 'var s=keep[0];'],
  ['R6 Saved professors not drawn', '    if(_svP){\n      list=', '    if(false){\n      list='],
  ['M09 aria-pressed never written', "document.getElementById('ex-profs').setAttribute('aria-pressed',String(m==='professors'));", ''],
  ['M10 feed window ignored', 'if(opts.win&&opts.win.lo<opts.win.hi&&window.innerWidth<=640){ lo=opts.win.lo; hi=opts.win.hi; }', ''],
  ['M10b feed window read without the width check', 'if(opts.win&&opts.win.lo<opts.win.hi&&window.innerWidth<=640){', 'if(opts.win&&opts.win.lo<opts.win.hi){'],
  ['M11 feed window leaks to desktop', 'if(window.innerWidth<=640){\n      var _wlo', 'if(true){\n      var _wlo'],
  ['M12 no air around the window', 'Math.floor(Math.max(0,_wlo-30)/60)*60, hi:Math.ceil((_whi+30)/60)*60', 'Math.floor(Math.max(0,_wlo-0)/60)*60, hi:Math.ceil((_whi+120)/60)*60'],
  ['M13 sub-tabs are not stops', "var SCHED_SUB=['mine','watch','plan'];", "var SCHED_SUB=['mine'];"],
  ['M14 arriving from Friends lands on My classes', "if(next.t&&typeof setSchedTab==='function'&&subNow()!==next.t)setSchedTab(next.t);", "if(next.t&&typeof setSchedTab==='function'&&subNow()!==next.t)setSchedTab('mine');"],
  ['M14b double render on entry', "if(next.t&&typeof setSchedTab==='function'&&subNow()!==next.t)setSchedTab(next.t);", "if(next.t&&typeof setSchedTab==='function')setSchedTab(next.t);"],
  ['M19 sign-in dialog ignores the inset', '.auth-back{padding-top:max(24px,calc(env(safe-area-inset-top) + 10px));', '.auth-back{'],
  ['M20 notif panel ignores the inset', '.notif-panel{top:calc(64px + env(safe-area-inset-top))}', '.notif-panel{}'],
  ['M21 banner ignores the inset', '#sbDeadBanner{top:calc(12px + env(safe-area-inset-top))!important}', ''],
  ['M22 sheet ends under the home indicator', '.mback .modal{padding-bottom:env(safe-area-inset-bottom)}', ''],
  ['M24 sign-in cap ignores the inset', '.auth-panel{max-height:calc(100dvh - max(24px,calc(env(safe-area-inset-top) + 10px)) - max(24px,calc(env(safe-area-inset-bottom) + 10px)))}', ''],
  ['M23 heading removed from the rotor', '.ex-q{position:absolute!important;width:1px;height:1px;', '.ex-q{display:none;width:1px;height:1px;'],
  ['M15 scrollers do not own their gesture', 'if(blocked(e.target)||inScroller(e.target))return;\n    if(stopIndex()<0)return;', 'if(blocked(e.target))return;\n    if(stopIndex()<0)return;'],
  ['M16 vertical drags read as sideways', 'var AXIS_BIAS=1.4;', 'var AXIS_BIAS=0.05;'],
  ['M17 whole view moves between sub-tabs', "var p=document.getElementById(PANE[S[i].t]); if(p){ p.classList.add('swp'); return p; }", ''],
  ['M18 wrap-around at the ends', "if((dx<0&&i>=n-1)||(dx>0&&i<=0&&!fromEdge)){ if(tgt){ clearFx(tgt); tgt=null; } return; }", ''],
];
let caught = 0;
for (const [name, a, b] of M) {
  const n = src.split(a).length - 1;
  if (n !== 1) { console.log(`SKIP ${name} — anchor ×${n}`); continue; }
  fs.writeFileSync('mut.html', src.replace(a, b));
  let rc = 0; try { execFileSync('node', ['check-mobile.mjs', 'mut.html'], { stdio: 'pipe', timeout: 300000 }); } catch (e) { rc = e.status || 1; }
  console.log(`${rc ? 'CAUGHT ' : 'MISSED '} ${name}`); if (rc) caught++;
}
console.log(`\n${caught}/${M.length} caught`);
