/* apply-sep24.mjs — three fixes to index.html, replayable and idempotent (2026-09-24).
   Run AFTER apply-hawk.mjs, on whatever the newest production-line index.html is:

     node apply-hawk.mjs <repo> && node apply-sep24.mjs <repo>

   Every anchor must be found exactly once or the script refuses and changes nothing. A change that
   is already applied is recognised by its marker and skipped, so running it twice is harmless.

   1. THE LEDGER READ THE WRONG MAJOR ("Plant Sciences" for a Business Administration student).
      plLedgerCompute() takes the degree from the planner's <select id="schMajorSel">, not from the
      student's profile. schInit fills that select at page load and preselects the student's major
      with `window.student` — but `student` is a top-level `const`, which never lands on window, so
      the preselect always missed and fell to Object.keys(SCHED_MAJORS)[0], which is Plant Sciences.
      The select only caught up when the student opened My planner (schSyncToStudent). Until then,
      anything else that read the ledger — Hawk's "GE I still need", Build my term, and on a fresh
      load Explore's "Still need" — was computing Plant Sciences.
      Fix: read `student` as a bare name in schInit; have plLedgerCompute sync the select to the
      profile first (plMajorSync); and compute a ledger only when the select's major IS the
      profile's. No major on the profile, or one the planner has no flowchart for, gets no ledger
      at all — never the first one in the list.

   2. THE PRIVACY POLICY SAYS WHAT HAWK SENDS. New "Hawk, the assistant" section; Anthropic added to
      "Who else is involved"; retention; and the Counting paragraph no longer says TermChamp never
      records what you type — Hawk questions are the exception. LEGAL_UPDATED_PRIVACY moves to
      24 September 2026.

   3. THE REGISTRATION DATES, quoted from the registrar (registrar.calpoly.edu/spring-semester-
      planning-calendar, read 2026-09-24): "October 19 | Monday | Round 1 Registration opens for
      registration appointment rotations", "November 4 | Wednesday | Round 2 Registration begins",
      "November 18 | Wednesday | Open Enrollment begins". The campus banner said "Priority
      registration", which is not what Cal Poly calls it; it now says Round 1. */
import fs from 'node:fs';
import path from 'node:path';

const root = process.argv[2] || '.';
const file = path.join(root, 'index.html');
let s = fs.readFileSync(file, 'utf8');
const done = [];

function patch(name, marker, anchor, replacement) {
  if (s.includes(marker)) { done.push('already  ' + name); return; }
  const n = s.split(anchor).length - 1;
  if (n !== 1) { console.error(`apply-sep24: "${name}": expected the anchor once, found ${n}. Refusing to guess; nothing written.`); process.exit(1); }
  s = s.replace(anchor, replacement);
  if (!s.includes(marker)) { console.error(`apply-sep24: "${name}": marker missing after the edit.`); process.exit(1); }
  done.push('applied  ' + name);
}

/* ---- 1. the ledger's major ------------------------------------------------------------------ */
patch('schInit reads the lexical student',
  "sm=(typeof student!=='undefined'&&student.major)||''; }catch(e){} /* schInit: student is a const",
  "var sm=''; try{ sm=(window.student&&student.major)||''; }catch(e){}",
  "var sm=''; try{ sm=(typeof student!=='undefined'&&student.major)||''; }catch(e){} /* schInit: student is a const, never on window — see apply-sep24 */");

patch('plMajorSync',
  'window.plMajorSync=function(){',
  'window.plLedgerCompute=function(){',
  `/* THE PLANNER'S SELECT IS NOT THE STUDENT'S MAJOR UNTIL SOMETHING SYNCS IT (2026-09-24).
   Everything that reads the ledger calls this first, so the answer is the student's own degree
   whether or not My planner has been opened. (The select is headless — the major comes from the
   profile — so there is no hand-picked choice to protect; review, 2026-09-24.) */
window.plMajorNorm=function(x){return String(x||'').toLowerCase().replace(/&/g,'and').replace(/[^a-z0-9]/g,'');};
window.plMajorSync=function(){
  var sel=document.getElementById('schMajorSel'); if(!sel||typeof SCHED_MAJORS==='undefined')return;
  if(window._plSyncing)return;
  var sm=''; try{ sm=(typeof student!=='undefined'&&student.major)||''; }catch(e){}
  if(!sm)return;
  var norm=window.plMajorNorm;
  var cur=SCHED_MAJORS[sel.value];
  if(cur&&norm(cur.name)===norm(sm))return;
  var key=Object.keys(SCHED_MAJORS).find(function(k){return norm(SCHED_MAJORS[k].name)===norm(sm);});
  if(!key)return;
  window._plSyncing=true;
  try{
    if(typeof window.schSyncToStudent==='function')window.schSyncToStudent();
    if(sel.value!==key){ sel.value=key; if(typeof sel.onchange==='function')sel.onchange(); }
  }catch(e){}
  window._plSyncing=false;
};
window.plLedgerCompute=function(){`);

patch('plLedgerCompute syncs first',
  "try{ if(typeof window.plMajorSync==='function')window.plMajorSync(); }catch(_e){} /* apply-sep24 */",
  "    majorName=(typeof student!=='undefined'&&student.major)||'';",
  "    majorName=(typeof student!=='undefined'&&student.major)||'';\n    try{ if(typeof window.plMajorSync==='function')window.plMajorSync(); }catch(_e){} /* apply-sep24 */");

patch('no major, no ledger',
  "/* apply-sep24: a ledger only for the student's OWN major",
  "    var mk=document.getElementById('schMajorSel'); mm=(mk&&typeof SCHED_MAJORS!=='undefined')?SCHED_MAJORS[mk.value]:null;",
  "    var mk=document.getElementById('schMajorSel'); mm=(mk&&typeof SCHED_MAJORS!=='undefined')?SCHED_MAJORS[mk.value]:null;\n"
  + "    /* apply-sep24: a ledger only for the student's OWN major. No major on the profile, or one the planner\n"
  + "       has no flowchart for, is no ledger at all — never the select's default (the FIRST major in the list). */\n"
  + "    if(mm&&(!majorName||(typeof window.plMajorNorm==='function'&&window.plMajorNorm(mm.name)!==window.plMajorNorm(majorName))))mm=null;");

/* ---- 2. the privacy policy ------------------------------------------------------------------ */
patch('privacy date',
  "LEGAL_UPDATED_PRIVACY='24 September 2026'",
  "LEGAL_UPDATED_PRIVACY='18 September 2026'",
  "LEGAL_UPDATED_PRIVACY='24 September 2026'");

patch('counting paragraph',
  'except the questions you ask Hawk',
  "the whole list of what TermChamp itself records: not what you type, not what you read, not how '",
  "the whole list of what TermChamp itself records: not what you type (except the questions you ask Hawk, below), not what you read, not how '");

patch('summary line',
  'and sends the questions you ask Hawk to <b>Anthropic</b>',
  "TermChamp does not sell your data, does not run ads, and loads no third-party trackers \\u2014 no Google, no Meta, nothing that follows you off this site. It does count which professor pages get opened, without recording who opened them. <b>Counting</b>, below, says exactly how.</div>'",
  "TermChamp does not sell your data and does not run ads. It counts which professor pages get opened without recording who opened them, uses <b>Google Analytics</b> to see how many people visit and come back, and sends the questions you ask Hawk to <b>Anthropic</b>\\u2019s AI. None of them is given your name or your account. <b>Counting</b>, <b>Google Analytics</b> and <b>Hawk</b>, below, say exactly what and how.</div>'");

patch('Hawk section',
  "+'<h4>Hawk, the assistant</h4>'",
  "+'<h4>Who can see what</h4>'",
  "+'<h4>Hawk, the assistant</h4>'\n"
  + "    +'<p>Hawk answers the questions you type into the box in the corner. Many answers are worked out '\n"
  + "    +'in your browser. When you are signed in, questions that need more than a simple lookup are sent, '\n"
  + "    +'through TermChamp\\u2019s server, to <b>Anthropic</b>, the company that makes the Claude AI models, '\n"
  + "    +'so a model can work out what you are asking for. When you are signed out, nothing you type into Hawk '\n"
  + "    +'leaves your browser.</p>'\n"
  + "    +'<p><b>What is sent to Anthropic:</b> the words you typed and the current term \\u2014 never your name, '\n"
  + "    +'email or account. When Hawk writes a short explanation under a list of classes, the classes on screen '\n"
  + "    +'are sent too: course, title, meeting time, professor and rating, open seats, whether each one fits '\n"
  + "    +'your week, and whether it is one of your GE areas or major requirements. The line that says how Hawk '\n"
  + "    +'read your question goes with them, and it can name the GE areas you still need.</p>'\n"
  + "    +'<p><b>What TermChamp\\u2019s own server sees:</b> that you are signed in, because only signed-in '\n"
  + "    +'students can use the AI. It counts how many Hawk questions, and how many Not it? taps, each account '\n"
  + "    +'makes per hour and per day, so costs and misuse cannot run away; those counts are all it keeps against '\n"
  + "    +'your account. The questions themselves '\n"
  + "    +'are stored only under the browser pseudonym described under Counting, never next to your account.</p>'\n"
  + "    +'<p><b>What is never sent:</b> your saved classes and schedule, your friends, your past classes, and '\n"
  + "    +'your degree record itself. Hawk works out anything about those in your browser. Words you type are sent '\n"
  + "    +'as typed, though \\u2014 so a friend\\u2019s name in a question goes with the question.</p>'\n"
  + "    +'<p><b>What is kept:</b> each question sent to Anthropic (its first 300 characters), what Hawk did with '\n"
  + "    +'it and what it cost, for about <b>30 days</b>. Old questions are cleared as Hawk is used, so in a quiet '\n"
  + "    +'week one can stay a few days longer. If you tap <b>Not it?</b>, or pick one of Hawk\\u2019s suggestions '\n"
  + "    +'after it was unsure, that question and what Hawk did with it are kept the same way, so we can fix the '\n"
  + "    +'mistake. Hawk\\u2019s explanations are not kept. If your browser sends Global Privacy Control, Hawk still '\n"
  + "    +'answers \\u2014 the question has to reach the model for that \\u2014 but TermChamp keeps no record of what '\n"
  + "    +'you asked, only that a question was asked and what it cost. '\n"
  + "    +'Anthropic handles questions under its commercial terms, which do not let it train its models on them.</p>'\n"
  + "    +'<h4>Who can see what</h4>'");

patch('Anthropic in who else',
  "+'<li><b>Anthropic</b>",
  "    +'<li><b>jsDelivr and Google Fonts</b>",
  "    +'<li><b>Anthropic</b> \\u2014 the AI model behind Hawk. It receives the questions you ask Hawk while signed in, as described under <b>Hawk</b> above.</li>'\n"
  + "    +'<li><b>jsDelivr and Google Fonts</b>");

patch('Hawk retention',
  "<b>Hawk questions:</b>",
  "    +'<p><b>Messages specifically:</b>",
  "    +'<p><b>Hawk questions:</b> about 30 days (see <b>Hawk</b>), under a pseudonym that is not attached to your account \\u2014 so deleting your account cannot find them, and does not need to.</p>'\n"
  + "    +'<p><b>Messages specifically:</b>");

/* ---- 3. registration ----------------------------------------------------------------------- */
patch('registration dates',
  "REGISTRATION_OPENS: '2026-10-19',",
  "  REGISTRATION_OPENS: '',",
  "  /* Spring 2027, quoted from registrar.calpoly.edu/spring-semester-planning-calendar (read 2026-09-24):\n"
  + "     \"October 19 | Monday | Round 1 Registration opens for registration appointment rotations\"\n"
  + "     \"November 4 | Wednesday | Round 2 Registration begins\"\n"
  + "     \"November 18 | Wednesday | Open Enrollment begins\". Update each term from that page. */\n"
  + "  REGISTRATION_OPENS: '2026-10-19',\n"
  + "  REGISTRATION_ROUND2: '2026-11-04',\n"
  + "  OPEN_ENROLLMENT: '2026-11-18',\n"
  + "  REGISTRATION_TERM: 'Spring 2027',");

patch('stale comment',
  'REGISTRATION_OPENS (in PROFESSIFY_CONFIG) sat',
  'REGISTRATION_OPENS two lines above is an\n         empty string, and has been since the field was added.',
  'REGISTRATION_OPENS (in PROFESSIFY_CONFIG) sat\n         empty from when the field was added until 2026-09-24, and is set by hand each term.');

patch('banner says Round 1',
  '<b>Round 1 registration opens ${when}.</b>',
  '<b>Priority registration opens ${when}.</b>',
  '<b>Round 1 registration opens ${when}.</b>');

fs.writeFileSync(file, s);
done.forEach((d) => console.log('  ' + d));
