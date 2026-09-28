/* ================= Champ = Hawk =================
   Champ asks the same `ask` function the desktop's Hawk uses. The model never writes an answer:
   it names ONE tool, and the code below answers that tool from the data this app loaded. So
   every class, seat, time and rating Champ says is one the student could find on the screens.
   When the model can't be reached (signed out, the daily budget, offline), Champ answers the
   simple questions itself from the same data, and says so for the rest. */
const HDAY = { Mo: 'M', Tu: 'T', We: 'W', Th: 'R', Fr: 'F', Sa: 'S', Su: 'U' };
const toMin = t => { const m = /^(\d{1,2}):(\d{2})$/.exec(String(t || '')); return m ? (+m[1]) * 60 + (+m[2]) : null; };
function findProfKey(name) {
  if (!name) return null;
  const k = profKeyOf(name); if (k && PROFS[k]) return k;
  const q = String(name).toLowerCase().replace(/^(prof(essor)?|dr)\.?\s+/, '').trim();
  const hits = Object.keys(PROFS).filter(pk => { const n = PROFS[pk].name.toLowerCase(); return n === q || n.split(' ').pop() === q || n.startsWith(q + ' '); });
  return hits.length === 1 ? hits[0] : (hits.find(pk => PROFS[pk].teaches) || hits[0] || null);
}
function findFriend(name) {
  const q = String(name || '').toLowerCase().trim(); if (!q) return null;
  const all = TC.friends.filter(id => { const p = PEOPLE[id]; return p.name.toLowerCase() === q || p.name.toLowerCase().split(' ')[0] === q || (p.handle || '').toLowerCase() === q.replace(/^@/, ''); });
  return all.length === 1 ? all[0] : null;
}
const cc = c => canonCode(c);
const pl = pk => pk ? `<b>${esc(profName(pk))}</b> (${ratingOf(pk) != null ? `★${ratingOf(pk).toFixed(1)} from ${PROFS[pk].count} PolyRatings` : 'not on PolyRatings'})` : '<b>Instructor not assigned</b>';
const secLine = s => `<b>${s.code}${s.sec ? ' §' + esc(s.sec) : ''}</b> ${secWhen(s)} · ${esc(profName(s.prof))}${ratingOf(s.prof) != null ? ' ★' + ratingOf(s.prof).toFixed(1) : ''} · ${secSeatText(s)}`;
function conflicts(planIds, sec) { return planIds.map(i => SEC[i]).filter(Boolean).filter(s => !s.async && !sec.async && s.s != null && sec.s != null && s.code !== sec.code && [...s.days].some(d => sec.days.includes(d)) && s.s < sec.e && sec.s < s.e); }
function clashWithMine(sec) { return personSecs('me').filter(s => s.s != null && sec.s != null && !sec.async && s.code !== sec.code && [...s.days].some(d => sec.days.includes(d)) && s.s < sec.e && sec.s < s.e); }

function ansClass(code) {
  if (!COURSES[code]) return { t: TC.seatsLoaded ? `${code} isn’t offered in ${esc(CFG.TERM_LABEL)}.` : 'Classes are still loading — ask again in a moment.' };
  const c = course(code), cs = courseSeats(code), fr = friendsIn(code);
  const t = `<b>${code} · ${esc(c.title)}</b><br>${courseProfs(code).map(p => '• ' + pl(p)).join('<br>')}<br><br>${cs.anyOpen ? (cs.open ? cs.open + ' open seats' : 'Has open sections') : cs.allFull ? 'Every section is full' : 'Seat counts aren’t posted'}${fr.length ? ` · ${fr.map(f => esc(PEOPLE[f].short)).join(', ')} ${fr.length > 1 ? 'are' : 'is'} in it` : ''}.`;
  return { t, acts: [['Open ' + code, 'openClass', code]] };
}
function ansProf(pk) {
  if (!pk) return { t: 'I couldn’t find that professor.' };
  const st = reviewStats(pk), cs = profCourses(pk);
  let t = pl(pk);
  t += cs.length ? ` teaches ${cs.join(', ')} in ${esc(CFG.TERM_LABEL)}.` : ` isn’t teaching in ${esc(CFG.TERM_LABEL)}.`;
  if (st) t += `<br>TermChamp reviews (${st.n}): ${st.again != null ? st.again + '% would take again' : ''}${st.again != null && st.diff != null ? ', ' : ''}${st.diff != null ? 'difficulty ' + st.diff + '/5' : ''}.`;
  return { t, acts: [['View ' + profName(pk).split(' ')[0], 'openProf', pk]] };
}
function ansBest(code) {
  if (!COURSES[code]) return ansClass(code);
  const ps = courseProfs(code).filter(Boolean);
  const rated = ps.filter(p => ratingOf(p) != null).sort((a, b) => ratingOf(b) - ratingOf(a));
  if (!rated.length) return { t: `None of the ${code} professors ${ps.length ? 'are on PolyRatings yet' : 'have been assigned yet'}, so I can’t rank them.`, acts: [['Open ' + code, 'openClass', code]] };
  const best = rated[0], open = secsOf(code).filter(s => s.prof === best && s.status === 'open');
  let t = rated.length === 1 && ps.length === 1 ? `Only ${pl(best)} teaches ${code}.` : `Highest rated for ${code}: ${pl(best)}.${rated[1] ? ` Next is ${pl(rated[1])}.` : ''}`;
  t += open.length ? `<br>${open.length} of their sections ${open.length === 1 ? 'has' : 'have'} open seats.` : secsOf(code).some(s => s.prof === best) ? `<br>Their sections have no open seats right now.` : '';
  const fr = (TC.took && TC.took[best] || []).filter(x => TC.friends.includes(x.uid));
  if (fr.length) t += `<br>${[...new Set(fr.map(x => PEOPLE[x.uid].short))].slice(0, 3).map(esc).join(', ')} took them before.`;
  return { t, acts: [['View ' + profName(best).split(' ')[0], 'openProf', best], ['Open ' + code, 'openClass', code]] };
}
function ansFree() {
  const fl = TC.friends.filter(f => status(f).free === true);
  if (!TC.friends.length) return { t: 'Add friends and I can tell you who’s free.', acts: [['Add friends', 'sheet', 'addFriend']] };
  if (!fl.length) return { t: 'None of your friends with class times are free right now.' };
  const top = fl.slice(0, 5);
  return { t: `It’s ${nowLabel()}. Free right now:<br>${top.map(f => `• <b>${esc(PEOPLE[f].short)}</b>, ${esc(status(f).t.charAt(0).toLowerCase() + status(f).t.slice(1))}`).join('<br>')}${fl.length > 5 ? `<br>+ ${fl.length - 5} more` : ''}`, acts: top.slice(0, 2).map(f => ['Message ' + PEOPLE[f].short, 'openChatWith', f]) };
}
function ansDay(day) {
  const l = personSecs('me').filter(s => !s.async && s.s != null && s.days.includes(day)).sort((a, b) => a.s - b.s);
  if (!personSecs('me').length) return { t: `You haven’t added ${esc(CFG.TERM_LABEL)} classes with times yet.`, acts: [['Open Schedule', 'tab', 'schedule']] };
  if (!l.length) return { t: `No classes on ${DAYL[day] || 'that day'}.` };
  const today = day === CLOCK.day, now = today && l.find(s => s.s <= CLOCK.min && CLOCK.min < s.e), next = today && l.find(s => s.s > CLOCK.min);
  return { t: `${DAYL[day]}:<br>${l.map(s => `• ${hs(s.s)}–${hs(s.e)} <b>${s.code}</b> with ${esc(profName(s.prof))}`).join('<br>')}${today ? `<br><br>${now ? `You’re in ${now.code} until ${hs(now.e)}. ` : ''}${next ? `Next up: ${next.code} at ${hs(next.s)}.` : 'Nothing else today.'}` : ''}`, acts: [['Open Schedule', 'tab', 'schedule']] };
}
function ansMyFree(days) {
  const ds = days && days.length ? days : DAYS;
  const out = ds.map(d => {
    const l = personSecs('me').filter(s => !s.async && s.s != null && s.days.includes(d)).sort((a, b) => a.s - b.s);
    if (!l.length) return `• ${DAYN[d]}: no classes`;
    const gaps = []; let t = 480;
    l.forEach(s => { if (s.s - t >= 30) gaps.push(hs(t) + '–' + hs(s.s)); t = Math.max(t, s.e); });
    if (1080 - t >= 30) gaps.push(hs(t) + '–6p');
    return `• ${DAYN[d]}: ${gaps.length ? gaps.join(', ') : 'booked 8a–6p'}`;
  });
  if (!personSecs('me').length) return { t: `You haven’t added ${esc(CFG.TERM_LABEL)} classes with times yet.` };
  return { t: `When you’re free between 8a and 6p:<br>${out.join('<br>')}` };
}
function ansRate() {
  const u = unrated(); if (!u.length) return { t: TC.rateList.length ? 'You’ve rated every professor on your list. Legend.' : 'Once your classes are on TermChamp, your professors show up to rate.' };
  return { t: `You have ${u.length} professor${u.length > 1 ? 's' : ''} to rate. It takes about 20 seconds and helps other students pick classes.`, acts: [['Rate ' + profName(u[0][0]), 'rateProf', u[0][0], u[0][1]], ['Open Rate', 'tab', 'rate']] };
}
function ansSearch(a) {
  if (!TC.seatsLoaded) return { t: 'Classes are still loading — ask again in a moment.' };
  if (a.ge_area || a.scope) return { t: 'GE areas and major requirements aren’t in the phone app yet. The Planner on termchamp.com has them.', acts: [['Open Planner', 'schedTabGo', 'planner']] };
  const code = cc(a.course), subj = String(a.subject || '').toUpperCase().trim();
  const days = (a.days || []).map(d => HDAY[d]).filter(Boolean);
  const at = toMin(a.at_time), sa = toMin(a.start_after), eb = toMin(a.end_before);
  let l = SECTIONS.filter(s => {
    if (code && s.code !== code) return false;
    if (!code && subj && s.code.split(' ')[0] !== subj) return false;
    if (a.open_only && s.status !== 'open') return false;
    if (a.instruction_mode === 'async' && !s.async) return false;
    if (a.instruction_mode === 'in_person' && s.async) return false;
    if (a.min_rating && !(ratingOf(s.prof) >= a.min_rating)) return false;
    if ((days.length || at != null || sa != null || eb != null) && (s.async || s.s == null)) return false;
    if (days.length && ![...s.days].every(d => days.includes(d))) return false;
    if (at != null && Math.abs(s.s - at) > 30) return false;
    if (sa != null && s.s < sa) return false;
    if (eb != null && s.e > eb) return false;
    if (a.fits_my_schedule && clashWithMine(s).length) return false;
    return true;
  });
  if (!code && !subj && !a.min_rating && !days.length && at == null && sa == null && eb == null) return { t: 'Which class or subject? Try “open CSC classes after 10am”.' };
  if (!l.length) return { t: 'No sections match all of that. Try loosening one thing — a later end time, or any day.' };
  const byR = (x, y) => ((ratingOf(y.prof) ?? -1) - (ratingOf(x.prof) ?? -1));
  l.sort(a.sort === 'seats' ? (x, y) => (y.seats || 0) - (x.seats || 0) : a.sort === 'rating' ? byR : (x, y) => (y.status === 'open') - (x.status === 'open') || byR(x, y));
  const top = l.slice(0, 5);
  return { t: `${l.length} section${l.length === 1 ? '' : 's'} match${l.length === 1 ? 'es' : ''}${l.length > 5 ? ' — the top 5' : ''}:<br>${top.map(s => '• ' + secLine(s)).join('<br>')}`, acts: top.slice(0, 2).map(s => ['Open ' + s.code, 'openClass', s.code]) };
}
function ansGamePlan(slot) {
  slot = ['A', 'B', 'C'].includes(String(slot || '').toUpperCase()) ? String(slot).toUpperCase() : S.plan;
  const secs = planSecs(slot);
  if (!secs.length) return { t: `Plan ${slot} is empty. Add sections from Explore and I’ll order them.`, acts: [['Explore', 'tab', 'explore']] };
  const others = id => TC.plans[slot].filter(x => x !== id);
  /* Register the scarcest first: full or waitlisted sections, then the fewest open seats. */
  const rank = s => s.status === 'open' ? (typeof s.seats === 'number' ? s.seats : 999) : s.status === 'unknown' ? 1000 : -1;
  const order = secs.slice().sort((x, y) => rank(x) - rank(y));
  const lines = order.map((s, i) => {
    const bk = secsOf(s.code).filter(b => b.id !== s.id && b.status === 'open' && !conflicts(others(s.id), b).length).sort((x, y) => ((ratingOf(y.prof) ?? -1) - (ratingOf(x.prof) ?? -1)))[0];
    return `${i + 1}. ${secLine(s)}${bk ? `<br>&nbsp;&nbsp;&nbsp;Backup: §${esc(bk.sec)} ${secWhen(bk)}` : '<br>&nbsp;&nbsp;&nbsp;No open backup section that fits.'}`;
  });
  return { t: `Plan ${slot}, scarcest first:<br>${lines.join('<br>')}<br><br><span style="opacity:.75">Uses ${esc(CFG.TERM_LABEL)} seats.</span>`, acts: [['Open Plans', 'schedTabGo', 'plans']] };
}
const GOTO = { home: ['tab', 'home'], explore: ['tab', 'explore'], 'explore professors': ['exModeGo', 'profs'], 'find professor': ['exModeGo', 'profs'], schedule: ['tab', 'schedule'], 'my classes': ['schedTabGo', 'mine'], 'week view': ['schedTabGo', 'mine'], planner: ['schedTabGo', 'planner'], friends: ['fFilterGo', 'people'], messages: ['fFilterGo', 'all'], groups: ['fFilterGo', 'groups'], 'new message': ['fFilterGo', 'people'], 'add friend': ['sheet', 'addFriend'], 'invite link': ['copyInvite', ''], notifications: ['sheet', 'notifs'], rate: ['tab', 'rate'], account: ['sheet', 'profile'], 'edit profile': ['sheet', 'profile'], settings: ['sheet', 'profile'] };
function answerTool(j, q) {
  const a = j.args || {};
  switch (j.tool) {
    case 'open_class': { const c = cc(a.course); return c ? ansClass(c) : null; }
    case 'open_professor': case 'professor_stats': return ansProf(findProfKey(a.name));
    case 'compare_professors': { const x = findProfKey(a.a), y = findProfKey(a.b); if (!x || !y) return { t: 'I couldn’t find both of those professors.' }; return { t: `• ${pl(x)}<br>• ${pl(y)}`, acts: [['View ' + profName(x).split(' ')[0], 'openProf', x], ['View ' + profName(y).split(' ')[0], 'openProf', y]] }; }
    case 'open_section': { const c = cc(a.course), s = secsOf(c).find(x => String(+x.sec) === String(+a.section)); return s ? { t: secLine(s), acts: [['Open ' + c, 'openClass', c]] } : c ? ansClass(c) : null; }
    case 'search_sections': {
      if (a.course && /best|who should|which prof|easiest|good prof/i.test(q) && Object.keys(a).length === 1) return ansBest(cc(a.course));
      return ansSearch(a);
    }
    case 'my_day': { const d = a.rel === 'tomorrow' ? DAYS[(DAYS.indexOf(CLOCK.day) + 1) % 5] || 'M' : (a.days && HDAY[a.days[0]]) || (DAYS.includes(CLOCK.day) ? CLOCK.day : 'M'); return ansDay(d); }
    case 'my_free': return ansMyFree((a.days || []).map(d => HDAY[d]).filter(Boolean));
    case 'my_conflicts': { const m = personSecs('me'), out = []; m.forEach((s, i) => m.slice(i + 1).forEach(t => { if (s.s != null && t.s != null && s.code !== t.code && [...s.days].some(d => t.days.includes(d)) && s.s < t.e && t.s < s.e) out.push(`• ${s.code} and ${t.code} (${daysLabel(s.days)} ${range(s)})`); })); return { t: out.length ? 'These overlap:<br>' + out.join('<br>') : 'No time clashes in your classes.' }; }
    case 'my_professors': { const ps = [...new Set(personSecs('me').map(s => s.prof).filter(Boolean))].sort((x, y) => a.order === 'asc' ? ((ratingOf(x) ?? 9) - (ratingOf(y) ?? 9)) : ((ratingOf(y) ?? -1) - (ratingOf(x) ?? -1))); return { t: ps.length ? 'Your professors:<br>' + ps.map(p => '• ' + pl(p)).join('<br>') : 'None of your classes have a named professor yet.' }; }
    case 'friends_in': { const c = cc(a.course); if (!c) return null; const fr = friendsIn(c); return { t: fr.length ? `${fr.map(f => esc(PEOPLE[f].name)).join(', ')} ${fr.length > 1 ? 'are' : 'is'} in ${c}.` : `None of your friends are in ${c}.`, acts: [['Open ' + c, 'openClass', c]] }; }
    case 'friends_took': { const c = cc(a.course), out = []; Object.keys(TC.took || {}).forEach(pk => TC.took[pk].forEach(t => { if (TC.friends.includes(t.uid) && (!c || t.code === c) && (!a.subject || t.code.startsWith(String(a.subject).toUpperCase() + ' '))) out.push(`• ${esc(PEOPLE[t.uid].short)}: ${t.code} with ${esc(profName(pk))}${t.when ? ' (' + esc(t.when) + ')' : ''}`); })); return { t: out.length ? out.slice(0, 10).join('<br>') : 'None of your friends have that in their past classes.' }; }
    case 'friend_profile': { const f = findFriend(a.friend); return f ? { t: `${esc(PEOPLE[f].name)}: ${[...new Set(personSecs(f).map(s => s.code).concat(PEOPLE[f].unplaced || []))].join(', ') || 'no classes added'}.`, acts: [['Open ' + PEOPLE[f].short, 'openFriend', f]] } : { t: 'I couldn’t find a friend by that name.' }; }
    case 'draft_message': { const f = findFriend(a.friend); if (!f) return { t: 'I couldn’t find a friend by that name.' }; const about = cc(a.course) || (a.name ? profName(findProfKey(a.name)) : ''); return { t: `Opening a chat with ${esc(PEOPLE[f].short)} — nothing is sent until you tap send.`, acts: [['Message ' + PEOPLE[f].short, 'draftTo', f, about ? `Have you taken ${about}? How was it?` : '']] }; }
    case 'add_friend': { UI.peopleQ = a.person || ''; return { t: 'Find them here:', acts: [['Add friends', 'sheet', 'addFriend']] }; }
    case 'rate_professor': { const pk = findProfKey(a.name) || (cc(a.course) && (personSecs('me').find(s => s.code === cc(a.course)) || {}).prof); return pk ? { t: `Rate ${esc(profName(pk))}:`, acts: [['Rate ' + profName(pk), 'rateProf', pk, cc(a.course) || '']] } : ansRate(); }
    case 'watch': { const c = cc(a.course); if (a.kind === 'section' && c) { const s = secsOf(c).find(x => String(+x.sec) === String(+a.section)); if (s) return { t: `${a.off ? 'Stop' : 'Get'} seat alerts for ${c} §${esc(s.sec)}?`, acts: [[a.off ? 'Stop alerts' : 'Watch it', 'watch', s.id]] }; } return c ? { t: `Pick a section of ${c} to watch — tap Watch next to it.`, acts: [['Open ' + c, 'openClass', c]] } : null; }
    case 'add_section': { const c = cc(a.course); if (!c) return null; const s = a.section ? secsOf(c).find(x => String(+x.sec) === String(+a.section)) : null; return s ? { t: secLine(s), acts: [[`Add to Plan ${S.plan}`, 'champAdd', s.id], ['Open ' + c, 'openClass', c]] } : ansClass(c); }
    case 'fit_pair': { const x = cc(a.a), y = cc(a.b); if (!x || !y) return null; const ok = secsOf(x).some(s => secsOf(y).some(t => !(s.s != null && t.s != null && [...s.days].some(d => t.days.includes(d)) && s.s < t.e && t.s < s.e))); return { t: secsOf(x).length && secsOf(y).length ? (ok ? `Yes — at least one section of ${x} and one of ${y} don’t overlap.` : `Every section of ${x} overlaps every section of ${y}.`) : `One of those isn’t offered in ${esc(CFG.TERM_LABEL)}.` }; }
    case 'swap_section': { const c = cc(a.course); if (!c) return null; const mine = personSecs('me').find(s => s.code === c); const l = secsOf(c).filter(s => !mine || s.id !== mine.id).filter(s => !clashWithMine(s).length).filter(s => !a.prefer || !mine || s.s == null || mine.s == null || (a.prefer === 'later' ? s.s > mine.s : s.s < mine.s)); return { t: l.length ? `Other ${c} sections that fit your week:<br>${l.slice(0, 5).map(s => '• ' + secLine(s)).join('<br>')}` : `No other ${c} section fits your week.`, acts: [['Open ' + c, 'openClass', c]] }; }
    case 'prereqs': { const c = cc(a.course); if (!c) return null; const p = course(c).prereq; return { t: p ? `${c} prerequisite: ${esc(p)}.<br>I can’t check your past classes against it here yet.` : TC.catalogLoaded ? `The catalog lists no prerequisite for ${c}.` : 'The catalog is still loading.' }; }
    case 'game_plan': return ansGamePlan(a.plan);
    case 'when_registration': return { t: `${esc(CFG.REGISTRATION_TERM)} registration starts ${esc(new Date(CFG.REGISTRATION_OPENS + 'T12:00:00').toLocaleDateString(undefined, { weekday: 'long', month: 'long', day: 'numeric' }))}. Your exact appointment is in the Cal Poly Portal.` };
    case 'my_units': case 'my_requirements': case 'build_term': return { t: 'Units, requirements and whole-term building are in the Planner on termchamp.com for now.', acts: [['Open Planner', 'schedTabGo', 'planner']] };
    case 'go_to': { const g = GOTO[a.where]; return g ? { t: 'Here you go.', acts: [['Open ' + a.where, g[0], g[1]]] } : { t: `That’s on termchamp.com for now.`, acts: [['Open termchamp.com', 'web', '/']] }; }
    case 'set_theme': return { t: 'The phone app has one look for now.' };
    case 'share': { const c = cc(a.course), pk = findProfKey(a.name); return c ? ansClass(c) : pk ? ansProf(pk) : null; }
    case 'help': return { t: 'I can find the best-rated professor for a class, search open sections (“open CSC after 10am, no Fridays”), show your day or when you’re free, say who’s free now, order a plan for registration, and open anything in the app.' };
    case 'cant_answer': return { t: a.reason === 'not_about_classes' ? 'I only know Cal Poly classes, professors, your schedule and your friends.' : a.reason === 'needs_judgment' ? 'That one’s your call — I can show you ratings, seats and times to decide with.' : a.reason === 'ambiguous' ? 'Can you say that another way? A class code or a professor’s name helps.' : 'I can’t see that.' };
  }
  return null;
}
/* Without the model: only the shapes that are unmistakable. */
function localAnswer(q) {
  const t = q.toLowerCase();
  const m = t.match(/\b([a-z&]{2,5})\s*-?\s*(\d{3,4}[a-z]?)\b/i); const code = m ? cc(m[1] + ' ' + m[2]) : null;
  const dm = t.match(/\b(mon|tue|wed|thu|fri)/), day = dm ? { mon: 'M', tue: 'T', wed: 'W', thu: 'R', fri: 'F' }[dm[1]] : (DAYS.includes(CLOCK.day) ? CLOCK.day : 'M');
  if (/\bfree\b.*\b(now|right now)\b|who('?s| is) free/.test(t)) return ansFree();
  if (/game ?plan|register.*first|backup/.test(t)) { const p = t.match(/plan\s*([abc])\b/); return ansGamePlan(p ? p[1].toUpperCase() : null); }
  if (code && COURSES[code] && /best|who should|which prof|easiest|good prof/.test(t)) return ansBest(code);
  if (code && COURSES[code]) return ansClass(code);
  if (/today|my day|next class|tomorrow/.test(t)) return ansDay(/tomorrow/.test(t) ? (DAYS[(DAYS.indexOf(CLOCK.day) + 1) % 5] || 'M') : day);
  if (/\b(rate|review)\b/.test(t)) return ansRate();
  const words = t.replace(/[^a-z\s'-]/g, ' ').split(/\s+/).filter(w => w.length > 3);
  const pk = words.map(w => findProfKey(w)).find(Boolean); if (pk && /prof|teach|how is|rating|dr\b/.test(t)) return ansProf(pk);
  return null;
}
async function ask(q) {
  q = String(q || '').trim().slice(0, 300); if (!q) return;
  S.champMsgs.push({ me: 1, t: q }); UI.typing = 'champ'; render(true); champEnd();
  let a = null;
  const j = await TC.ask(q);
  if (j && j.tool) { try { a = answerTool(j, q); } catch (e) { a = null; } }
  if (!a) a = localAnswer(q);
  if (!a) a = { t: j === null && !TC.user ? 'Sign in and I can answer that.' : j === null ? 'I can’t reach TermChamp’s assistant right now, so I can only do simple questions — try a class code like <b>CSC 1001</b>.' : 'I’m not sure how to answer that one. Try a class code, a professor’s name, or “who’s free right now?”.' };
  UI.typing = null; S.champMsgs.push({ t: a.t, acts: a.acts || [] }); render(true); champEnd();
}
function champEnd() { const el = document.getElementById('champscroll'); if (el) el.scrollTop = el.scrollHeight; }

/* ================= plan helpers ================= */
function addSec(id) {
  const sec = SEC[id]; if (!sec) return false;
  const plan = TC.plans[S.plan];
  if (plan.includes(id)) { TC.setPlan(S.plan, plan.filter(x => x !== id)); toast(`Removed ${sec.code} from Plan ${S.plan}`); render(true); return true; }
  const c = conflicts(plan, sec);
  if (c.length) { toast(`Conflicts with ${c[0].code} (${daysLabel(c[0].days)} ${range(c[0])})`); return false; }
  const had = plan.some(x => SEC[x] && SEC[x].code === sec.code);
  const next = plan.filter(x => !(SEC[x] && SEC[x].code === sec.code)).concat(id);
  if (next.length > 12) { toast('A plan holds up to 12 sections'); return false; }
  TC.setPlan(S.plan, next);
  toast(had ? `Switched to this ${sec.code} section` : `Added ${sec.code} to Plan ${S.plan}`); render(true); return true;
}

/* ================= actions ================= */
const A = {
  back, tab: t => { UI.champ = false; UI.sheet = null; setTab(t); },
  reload: () => location.reload(),
  refresh: () => { TC.refresh(); toast('Refreshing…'); },
  retrySeats: () => { delete TC.err.seats; render(true); loadSeats(); },
  google: () => TC.signInGoogle(),
  siMode: m => { UI.signin.mode = m; UI.signin.err = ''; render(); },
  signOut: () => { UI.sheet = null; TC.signOut(); },
  web: p => { window.open(WEB + (p || '/'), '_blank', 'noopener'); },
  homeFriend: id => { S.homeFriend = id; render(true); },
  homeDay: d => { S.homeDay = d; render(true); }, schedDay: d => { S.schedDay = d; render(true); },
  openClass: code => { UI.champ = false; go('classDetail', { code }); },
  openProf: id => { UI.champ = false; go('profDetail', { id }); },
  openFriend: id => { UI.champ = false; if (!id) return; if (id === 'me') return setTab('schedule'); go('friend', { id }); },
  sheet: type => { UI.sheet = { type }; UI.champ = false; if (type === 'notifs') { S.notifSeen = TC.requests.join(',') + '|' + TC.threads.filter(isUnread).map(t => t.id + (t.last && t.last.created_at)).join(','); save(); } if (type === 'addFriend' && UI.peopleQ) runPeople(UI.peopleQ); render(true); },
  closeSheet: () => { UI.sheet = null; UI.champ = false; render(true); },
  exMode: m => { S.exMode = m; S.exLimit = 40; save(); render(true); },
  exModeGo: m => { UI.champ = false; S.exMode = m; save(); setTab('explore'); },
  clearQ: () => { S.q = ''; S.exLimit = 40; render(true); },
  more: () => { S.exLimit += 40; render(true); },
  savedOnly: () => { S.savedOnly = !S.savedOnly; render(true); },
  setSubj: c => { S.subj = c; S.exLimit = 40; save(); render(true); }, openOnly: () => { S.openOnly = !S.openOnly; save(); render(true); },
  clearFilters: () => { S.subj = 'All'; S.openOnly = false; S.savedOnly = false; S.q = ''; UI.sheet = null; save(); render(true); },
  save: k => { const on = isSaved(k); S.saved = on ? S.saved.filter(x => x !== k) : [...S.saved, k]; toast(on ? 'Removed from saved' : 'Saved on this phone'); save(); render(true); },
  pickPlan: k => { S.plan = k; save(); render(true); },
  addSec: id => addSec(id),
  watch: async id => { if (UI.busy['w' + id]) return; UI.busy['w' + id] = 1; const on = !TC.watches[id]; const ok = await TC.watch(id, on); UI.busy['w' + id] = 0; if (ok) { if (!on) delete TC.autoWatch[id]; toast(on ? 'We’ll alert you when a seat opens' : 'Seat alerts off'); } render(true); },
  secSheet: (code, id) => { UI.sheet = { type: 'sec', code, id }; render(true); },
  removeSec: id => { TC.setPlan(S.plan, TC.plans[S.plan].filter(x => x !== id)); UI.sheet = null; toast(`Removed ${(SEC[id] || {}).code || 'it'} from Plan ${S.plan}`); render(true); },
  schedTab: t => { S.schedTab = t; save(); render(); },
  schedTabGo: t => { UI.champ = false; S.schedTab = t; save(); setTab('schedule'); },
  rateProf: (pid, code) => {
    if (!PROFS[pid]) return;
    if (iReviewed(pid)) { toast('You’ve already reviewed ' + profName(pid)); return; }
    const item = TC.rateList.flatMap(t => t.items.map(i => [...i, t.term])).find(i => i[0] === pid && (!code || i[1] === code));
    /* The classes this student actually took with them — this term's and past ones. Only when we
       know of none is the list what they teach, and then the student picks. */
    const taken = [...new Set(personSecs('me').filter(s => s.prof === pid).map(s => s.code).concat((TC.myHistory || []).filter(h => profKeyOf(h.professor) === pid).map(h => canonCode(h.code)).filter(Boolean)))];
    const codes = taken.length ? taken : profCourses(pid);
    code = (codes.length === 1 ? codes[0] : null) || (code && codes.includes(code) ? code : null);
    S.draft = { prof: pid, code, codes, term: item ? item[2] : '', stars: 0, diff: 0, again: null, more: false, grade: null, format: null, review: '', err: '' };
    UI.champ = false; UI.sheet = null; go('rateForm');
  },
  draft: (k, v) => { const d = S.draft; const val = (k === 'stars' || k === 'diff') ? +v : v; d[k] = d[k] === val && k !== 'stars' && k !== 'code' ? null : val; if (k === 'diff' && d.diff === null) d.diff = 0; d.err = ''; render(true); },
  draftMore: () => { S.draft.more = !S.draft.more; render(true); },
  postRating: async () => {
    const d = S.draft; if (!d || !d.stars || !d.code || UI.busy.rate) return;
    UI.busy.rate = 1; render(true);
    const r = await TC.postReview(d.prof, d);
    UI.busy.rate = 0;
    if (r.err) { d.err = r.err; render(true); return; }
    S.lastRated = Object.assign({}, d, { reviewId: r.id, share: false });
    const st = S.stack[S.tab]; st[st.length - 1] = { s: 'rateThanks', p: {} }; render();
  },
  toggleShow: async () => { const d = S.lastRated; if (!d || !d.reviewId) return; const next = !d.share; if (await TC.setShare(d.reviewId, next)) { d.share = next; } else toast('Couldn’t change that — try again'); render(true); },
  rateDone: () => { const st = S.stack[S.tab]; st.pop(); if (!st.length) st.push({ s: S.tab }); render(); },
  rateAnother: () => { const u = unrated(); const st = S.stack[S.tab]; st.pop(); if (!st.length) st.push({ s: S.tab }); if (u.length) A.rateProf(u[0][0], u[0][1]); else render(); },
  fFilter: f => { S.friendsFilter = f; render(true); },
  fFilterGo: f => { UI.champ = false; S.friendsFilter = f; setTab('friends'); },
  openChat: id => { UI.champ = false; TC.openThread(id); go('chat', { id }); },
  retryChat: () => { const e = cur(); if (e.p && e.p.id) TC.openThread(e.p.id); },
  openChatTab: id => { UI.sheet = null; S.tab = 'friends'; S.stack.friends = [{ s: 'friends' }]; A.openChat(id); },
  openChatWith: async pid => { UI.champ = false; const id = await TC.threadWith(pid); if (id) A.openChat(id); },
  draftTo: async (pid, text) => { UI.champ = false; const id = await TC.threadWith(pid); if (!id) return; UI.prefill = { id, text: text || '' }; A.openChat(id); },
  addFriend: async id => {
    if (UI.busy['f' + id]) return; UI.busy['f' + id] = 1;
    if (TC.relation(id) === 'sent') { if (await TC.cancelRequest(id)) toast('Request canceled'); }
    else if (await TC.sendRequest(id)) toast(`Request sent to ${PEOPLE[id].short}`);
    UI.busy['f' + id] = 0; render(true);
  },
  acceptReq: async id => { if (await TC.acceptRequest(id)) { toast(`You and ${PEOPLE[id].short} are now friends`); relinkPeople(); } render(true); },
  declineReq: async id => { if (await TC.declineRequest(id)) toast('Request declined'); render(true); },
  copyInvite: async () => {
    const url = WEB + '/' + (PEOPLE.me.handle ? '?invite=' + encodeURIComponent(PEOPLE.me.handle) : '');
    try { if (navigator.share) { await navigator.share({ title: 'TermChamp', text: 'See who’s in your classes on TermChamp', url }); return; } } catch (e) { return; }
    try { await navigator.clipboard.writeText(url); toast('Invite link copied'); } catch (e) { toast(url); }
  },
  openChamp: () => { UI.champ = true; UI.sheet = null; render(true); champEnd(); },
  ask: q => ask(q),
  champClear: () => { S.champMsgs = []; render(true); },
  champAdd: id => { const ok = addSec(id); if (ok) { S.champMsgs.push({ t: `Done. ${SEC[id].code} is in Plan ${S.plan}.`, acts: [['Open Plans', 'schedTabGo', 'plans']] }); render(true); champEnd(); } }
};
async function runPeople(q) {
  UI.peopleQ = q; if (String(q).trim().length < 2) { UI.peopleRes = null; render(true); return; }
  UI.peopleRes = 'busy'; render(true);
  try { const r = await TC.searchPeople(q); if (UI.peopleQ === q) UI.peopleRes = r; }
  catch (e) { UI.peopleRes = { err: 'Couldn’t search right now — try again.' }; }
  render(true);
}
const SUBMIT = {
  send: async form => {
    const inp = form.querySelector('input'), v = inp.value.trim(); if (!v || UI.busy.send) return;
    const id = form.dataset.x; UI.busy.send = 1; inp.value = ''; UI.prefill = null;
    const ok = await TC.send(id, v); UI.busy.send = 0;
    if (!ok) inp.value = v;
    render(true); scrollEnd();
  },
  champ: form => { const inp = form.querySelector('input'); const v = inp.value; inp.value = ''; ask(v); },
  people: form => runPeople(form.querySelector('input').value),
  pw: async form => {
    const e = form.querySelector('#si-email').value.trim(), p = form.querySelector('#si-pw').value;
    UI.signin.email = e; UI.busy.signin = 1; UI.signin.err = ''; render();
    const err = await TC.signInPassword(e, p); UI.busy.signin = 0;
    if (err) { UI.signin.err = /invalid/i.test(err) ? 'That email and password don’t match. If you signed up with Google, use Continue with Google.' : err; render(); }
  },
  sendCode: async form => {
    const e = form.querySelector('#si-email').value.trim(); UI.signin.email = e; UI.busy.signin = 1; UI.signin.err = ''; render();
    const err = await TC.sendCode(e); UI.busy.signin = 0;
    if (err) { UI.signin.err = /signups? not allowed|not found|user/i.test(err) ? 'No TermChamp account uses that email. Create one on termchamp.com first.' : err; render(); return; }
    UI.signin.mode = 'verify'; render();
  },
  verify: async form => {
    const c = form.querySelector('#si-code').value.trim(); UI.busy.signin = 1; UI.signin.err = ''; render();
    const err = await TC.verifyCode(UI.signin.email, c); UI.busy.signin = 0;
    if (err) { UI.signin.err = /expired|invalid/i.test(err) ? 'That code didn’t work or has expired. Send a new one.' : err; render(); }
  }
};
function scrollEnd() { const sc = document.getElementById('scroll'); sc.scrollTop = sc.scrollHeight; }

/* ================= render ================= */
const TABS = [['home', 'Home', 'home', '#1D4ED8', '#E3ECFF'], ['explore', 'Explore', 'search', '#7C3AED', '#EFE7FF'], ['rate', 'Rate', 'star', '#D97706', '#FEF1DC'], ['schedule', 'Schedule', 'cal', '#0F766E', '#DDF5F1'], ['friends', 'Friends', 'users', '#DB2777', '#FCE4F0']];
function render(keep) {
  const sc = document.getElementById('scroll'); if (!sc) return;
  const ae = document.activeElement, focusId = ae && ae.id && (ae.tagName === 'INPUT' || ae.tagName === 'TEXTAREA') ? ae.id : null, sel = focusId ? [ae.selectionStart, ae.selectionEnd, ae.value] : null;
  const y = sc.scrollTop, champY = (document.getElementById('champscroll') || {}).scrollTop;
  const sh = document.getElementById('sheet');
  if (TC.phase !== 'ok') {
    sc.innerHTML = signinView(); sc.style.paddingTop = ''; sc.style.background = '';
    ['fixtop', 'fixbot', 'chrome'].forEach(i => { document.getElementById(i).innerHTML = ''; });
    sh.innerHTML = ''; document.getElementById('status').classList.remove('dark');
    if (focusId) { const el = document.getElementById(focusId); if (el) { el.focus(); if (el.value === sel[2]) try { el.setSelectionRange(sel[0], sel[1]); } catch (_) {} } }
    return;
  }
  const e = cur(); let v;
  try { v = SCREENS[e.s](e.p || {}); } catch (err) { console.error('[termchamp app]', err); v = missingScreen('Something went wrong on this screen.'); }
  sc.innerHTML = v.body;
  sc.style.paddingTop = v.padTop ? `calc(var(--sb) + ${v.padTop}px)` : '';
  document.getElementById('fixtop').innerHTML = v.top || '';
  document.getElementById('fixbot').innerHTML = v.bot || '';
  document.getElementById('status').classList.toggle('dark', !!v.dark);
  sc.style.background = v.dark ? 'linear-gradient(#0F172A 0 50%,var(--bg) 50%)' : '';
  const onTab = S.tab;
  const badge = k => k === 'friends' && (TC.requests.length + TC.threads.filter(isUnread).length) ? '<span class="dot" style="position:absolute;top:6px;right:calc(50% - 22px)"></span>' : '';
  document.getElementById('chrome').innerHTML = (v.tabbar ? `<nav class="tabbar">${TABS.map(([k, l, i, ac, acs]) => `<button class="tab ${onTab === k ? 'on' : ''}" style="--ac:${ac};--acs:${acs};position:relative" data-a="tab" data-x="${k}"><span class="pill">${ic(i, 23, 2.1, onTab === k && k === 'rate' ? 'currentColor' : 'none')}</span>${l}${badge(k)}</button>`).join('')}</nav>` : '') +
    (v.fab && !UI.champ ? `<button class="fab" data-a="openChamp" aria-label="Ask Champ"><span class="bub">Ask Me!</span><img src="${CHAMP}" alt=""></button>` : '');
  if (UI.champ) sh.innerHTML = `<div class="scrim" data-a="closeSheet"></div><div class="sheet champ" style="${S.champMsgs.length ? 'height:calc(100% - var(--sb) - 16px)' : ''}">${champView()}</div>`;
  else if (UI.sheet) sh.innerHTML = `<div class="scrim" data-a="closeSheet"></div><div class="sheet"><div class="grab"></div><div class="sbody">${SHEETS[UI.sheet.type](UI.sheet)}</div></div>`;
  else sh.innerHTML = '';
  if (keep) sc.scrollTop = y; else sc.scrollTop = e.y || 0;
  if (v.scrollEnd && !keep) scrollEnd();
  const cs = document.getElementById('champscroll'); if (cs && champY != null) cs.scrollTop = champY;
  if (focusId) { const el = document.getElementById(focusId); if (el) { el.focus(); if (el.value === sel[2]) try { el.setSelectionRange(sel[0], sel[1]); } catch (_) {} } }
}
let toastT;
function toast(m) { const t = document.getElementById('toast'); if (!t) return; t.textContent = m; t.classList.add('on'); clearTimeout(toastT); toastT = setTimeout(() => t.classList.remove('on'), 2400); }

/* ================= events ================= */
document.addEventListener('click', ev => {
  const el = ev.target.closest('[data-a]'); if (!el) return;
  const f = A[el.dataset.a]; if (!f) return; ev.preventDefault();
  f(el.dataset.x, el.dataset.y, el);
});
document.addEventListener('submit', ev => { const f = ev.target.closest('[data-submit]'); if (!f) return; ev.preventDefault(); const h = SUBMIT[f.dataset.submit]; if (h) h(f); });
let qT;
document.addEventListener('input', ev => {
  const k = ev.target.dataset.in; if (!k) return;
  if (k === 'q') { S.q = ev.target.value; S.exLimit = 40; clearTimeout(qT); qT = setTimeout(() => { const el = document.getElementById('exlist'); if (el) el.innerHTML = exploreList(); }, 120); }
  else if (k === 'fq') { S.fq = ev.target.value; document.getElementById('flist').innerHTML = friendsList(); }
  else if (k === 'review') { S.draft.review = ev.target.value; const n = wordCount(ev.target.value), c = document.getElementById('revcount'); if (c) { c.textContent = n + '/300 words'; c.style.color = n > 300 ? '#B91C1C' : ''; } }
});
document.addEventListener('keydown', ev => { if (ev.key === 'Escape' && (UI.sheet || UI.champ)) A.closeSheet(); });
function fit() { const s = Math.min(1, (innerHeight - 32) / 874, (innerWidth - 32) / 402); document.documentElement.style.setProperty('--s', s); }
addEventListener('resize', fit); fit();
/* The phone frame's status bar shows the real time (on a real phone it is hidden). */
function tickClock() { const el = document.querySelector('#status > span'); if (el) { const d = new Date(); el.textContent = (d.getHours() % 12 || 12) + ':' + String(d.getMinutes()).padStart(2, '0'); } }
tickClock(); setInterval(() => { tickClock(); if (TC.phase === 'ok' && !document.activeElement.matches('input,textarea') && !UI.champ) render(true); }, 60000);
/* Coming back to the app after a while: pick up new messages, requests and seats. */
document.addEventListener('visibilitychange', () => { if (document.visibilityState === 'visible' && TC.ready && Date.now() - (TC.loadedAt || 0) > 120000) { TC.loadedAt = Date.now(); TC.refresh(); loadSeats(); } });
render();
if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', () => TC.boot()); else TC.boot();
