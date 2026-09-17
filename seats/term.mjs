/**
 * Professify — resolving a term LABEL to PeopleSoft's term CODE, without guessing.
 * ==============================================================================
 *
 * registrar-calendar.json knows Cal Poly's dates by name ("Spring 2027"). The class search only
 * speaks STRM ("2268"). Something has to bridge them, and the tempting bridge is arithmetic:
 * CSU's convention is 2 + the term's calendar year + a season digit (2 Winter, 4 Spring,
 * 6 Summer, 8 Fall), so Fall 2026 = 2268 and Spring 2027 "must be" 2274.
 *
 * WHY THAT ARITHMETIC IS NOT ALLOWED TO BE THE ANSWER. A wrong term code does not fail. The
 * class search accepts it, finds nothing, and returns a clean empty result — indistinguishable
 * from "this subject has no sections this term". The scraper would report a green run, upsert
 * nothing, and the app would show students an empty Spring schedule on the morning registration
 * opens. A convention that has held for twenty years is still a guess, and Cal Poly has just
 * moved from quarters to semesters, which is exactly the kind of change that renumbers things.
 *
 * So the arithmetic only ever proposes CANDIDATES. A candidate becomes the answer when the live
 * page confirms it names the term we asked for — and if none does, this throws rather than
 * picking the most likely one.
 */

const SEASONS = [
  { name: 'winter', digit: '2', re: /\bwinter\b/i },
  { name: 'spring', digit: '4', re: /\bspring\b/i },
  { name: 'summer', digit: '6', re: /\bsummer\b/i },
  { name: 'fall',   digit: '8', re: /\bfall\b/i },
];

/** "Spring 2027" -> { season:'spring', year:2027 }. Returns null for anything it cannot read. */
export function parseLabel(label) {
  const s = SEASONS.find(x => x.re.test(label || ''));
  const y = String(label || '').match(/\b(20\d{2})\b/);
  return s && y ? { season: s.name, digit: s.digit, year: +y[1] } : null;
}

/**
 * Codes to try, best first. The convention's answer leads; the neighbours follow because the
 * season digit is the part most likely to differ at a university that just changed its calendar.
 */
export function termCandidates(label) {
  const p = parseLabel(label);
  if (!p) return [];
  const yy = String(p.year).slice(-2);
  const first = `2${yy}${p.digit}`;
  const others = SEASONS.filter(s => s.digit !== p.digit).map(s => `2${yy}${s.digit}`);
  /* A Fall term can also be numbered under the academic year that starts with it, so try the
     next calendar year's digits for Fall and the previous for Spring. Still only candidates. */
  const yAdj = p.season === 'fall' ? p.year + 1 : p.season === 'spring' ? p.year - 1 : p.year;
  const adj = `2${String(yAdj).slice(-2)}${p.digit}`;
  return [...new Set([first, adj, ...others])];
}

/**
 * Does this page text confirm it is showing the term we asked for?
 *
 * Both halves must be present — season AND year. "Spring" alone matches a Spring of any year,
 * and "2027" alone matches Summer 2027, and either mistake ships a whole term of wrong data.
 * The text is also required to be a term ECHO rather than the whole page, so a stray "Spring
 * 2027 schedule available" note elsewhere on the page cannot confirm a term by accident.
 */
export const ECHO_PROXIMITY = 30;

/** Every distinct "<season> <year>" a piece of text names, as normalised labels. */
export function termsNamedIn(echo) {
  const t = String(echo || '').replace(/\s+/g, ' ');
  const years = [...t.matchAll(/\b(20\d{2})\b/g)].map(m => ({ y: +m[1], at: m.index }));
  const found = new Set();
  for (const s of SEASONS) {
    for (const m of t.matchAll(new RegExp(s.re.source, 'gi'))) {
      /* A season belongs to the nearest year within a term-name's width. Further than that and
         the two are separate facts that happen to share a sentence. */
      const near = years.filter(y => Math.abs(y.at - m.index) <= ECHO_PROXIMITY)
                        .sort((a, b) => Math.abs(a.at - m.index) - Math.abs(b.at - m.index))[0];
      if (near) found.add(`${s.name} ${near.y}`);
    }
  }
  return [...found];
}

/**
 * Does this text confirm the page is showing the term we asked for?
 *
 * Three ways this has been wrong, each one shipped a whole term of misfiled data:
 *
 *   · Season alone. "Spring" matches a Spring of any year.
 *   · Year alone. "2027" matches Summer 2027 just as well.
 *   · Season AND year present ANYWHERE. This is the subtle one. The echo is read with
 *     closest('tr, .ps_box-group, div'), and `closest` with a comma selector returns the nearest
 *     ancestor matching ANY branch — so on a loose layout it can climb far enough to swallow the
 *     Registrar's own notice that "the Spring 2027 class schedule becomes available April 27",
 *     sitting on a page that still shows Fall 2026. Both words are present, and adjacent, so
 *     proximity does not save it either: "Spring 2027" really is a term name, just not THIS
 *     page's term.
 *
 * So the test is not "does it mention our term" but "does it mention ONLY our term". Text that
 * names two terms is ambiguous, and an ambiguous echo confirms nothing — resolveTerm moves on to
 * the next candidate or throws, which is a loud failure instead of a wrong semester.
 */
export function matchesTerm(echo, label) {
  const p = parseLabel(label);
  if (!p) return false;
  const named = termsNamedIn(echo);
  if (named.length !== 1) return false;          // nothing named, or more than one — refuse
  return named[0] === `${p.season} ${p.year}`;
}

/**
 * Walk the candidates against the live page.
 *
 * @param {object} io
 * @param {(code:string)=>Promise<void>}   io.setTerm   put the code in the term field and let
 *                                                      PeopleSoft validate it
 * @param {()=>Promise<string>}            io.readEcho  the term description the page now shows
 * @param {()=>Promise<number>}            io.subjectCount how many subjects the dropdown holds
 * @param {()=>Promise<string>}           [io.readField] what the term field itself now holds
 * @param {(msg:string)=>void}            [io.log]
 * @param {string} label   e.g. "Spring 2027"
 * @param {string[]} [candidates]
 * @returns {Promise<{code:string, echo:string, subjects:number}>}
 * @throws  when nothing confirms — deliberately, see the header.
 */
export async function resolveTerm(io, label, candidates = termCandidates(label)) {
  const log = io.log || (() => {});
  const tried = [];
  for (const code of candidates) {
    await io.setTerm(code);
    const echo = (await io.readEcho()) || '';
    const subjects = await io.subjectCount();
    const named = matchesTerm(echo, label);
    /* The field itself is the one signal that cannot be contaminated by neighbouring text: if it
       does not hold the code we just set, PeopleSoft rejected it and the page is still showing
       whatever it showed before — which is exactly the state that makes a stray mention of
       another term look like confirmation. */
    /* REQUIRED, not optional. Defaulting a missing readField to "it matched" silently reverts to
       the two-signal test this replaced, and no test notices because every test supplies one. */
    if (typeof io.readField !== 'function') throw new Error('resolveTerm requires io.readField — the field read-back is the one signal neighbouring text cannot contaminate');
    const held = String((await io.readField()) || '').trim();
    tried.push({ code, echo: echo.slice(0, 80), subjects, named, held });
    log(`  term candidate ${code}: field=${JSON.stringify(held)} echo=${JSON.stringify(echo.slice(0, 60))} subjects=${subjects} named=${named}`);

    /* THREE tests, not one and not two. The field holding the code proves it was accepted; the
       echo naming exactly one term, ours, proves the page understood which; a populated subject
       list proves the term actually has a schedule to search. A code can be syntactically valid
       and name a term that was never built. */
    if (held === String(code) && named && subjects > 0) return { code, echo, subjects };
  }
  const err = new Error(
    `could not confirm a PeopleSoft term code for "${label}". Tried ${candidates.join(', ')}. ` +
    `Refusing to guess — a wrong code returns an empty search that looks exactly like a term with no classes. ` +
    `Detail: ${JSON.stringify(tried)}`
  );
  err.kind = 'term-unresolved';
  err.tried = tried;
  throw err;
}
