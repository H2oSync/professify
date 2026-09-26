/* The ask function's prompt, tools, vendor calls, validation and pricing — shared by the function
   (index.ts) and by the model comparison (golden/check-models.ts), so the models are scored on the
   EXACT prompt and tools students get. A second copy would drift, and then the score would be for
   a Hawk nobody uses. Moved out of index.ts unchanged on 2026-09-24. */
export const MAX_Q = 300;
export const TIMEOUT_MS = 8000;
export const MAX_OUT = 200;

export const CORS = {
  'access-control-allow-origin': '*',
  'access-control-allow-headers': 'authorization, content-type',
  'access-control-allow-methods': 'POST, OPTIONS',
};

/* ------------------------------------------------------------------------------------------------
   The tools. Descriptions are tokens on every single call, so every line here is paid for on every
   question a student asks. They are terse on purpose.
   ------------------------------------------------------------------------------------------------ */
export const TOOLS = [
  {
    name: 'search_sections',
    description: 'Find sections in the current term.',
    parameters: {
      type: 'object',
      properties: {
        subject: { type: 'string', description: 'Subject code, e.g. CSC' },
        course: { type: 'string', description: 'Course code, e.g. CSC1001 or BUS4442' },
        days: { type: 'array', items: { type: 'string', enum: ['Mo', 'Tu', 'We', 'Th', 'Fr', 'Sa', 'Su'] } },
        at_time: { type: 'string', description: 'HH:MM 24h, sections starting near this time' },
        start_after: { type: 'string', description: 'HH:MM 24h' },
        end_before: { type: 'string', description: 'HH:MM 24h' },
        open_only: { type: 'boolean', description: 'Only sections with seats' },
        min_rating: { type: 'number', description: 'Professor rating floor, 1-5' },
        instruction_mode: { type: 'string', enum: ['in_person', 'hybrid', 'async', 'sync_online'] },
        ge_area: { type: 'string', description: '2026 GE area: 1A 1B 1C 2 3A 3B 4A 4B 5A 5B 5C 6 UD3 UD4 U25' },
        component: { type: 'string', enum: ['LEC', 'LAB', 'ACT', 'SEM'] },
        fits_my_schedule: { type: 'boolean', description: 'Only sections that do not clash with the student’s saved classes' },
        sort: { type: 'string', enum: ['rating', 'seats', 'easiest'], description: 'rating = best-rated professor first' },
        scope: { type: 'string', enum: ['ge_unmet', 'required'], description: 'ge_unmet = GE areas the student still needs; required = everything their major still requires' },
      },
    },
  },
  {
    name: 'open_class',
    description: 'Open one course’s page.',
    parameters: { type: 'object', required: ['course'], properties: { course: { type: 'string' } } },
  },
  {
    name: 'open_professor',
    description: 'Open one professor’s page.',
    parameters: { type: 'object', required: ['name'], properties: { name: { type: 'string' } } },
  },
  /* Phase 2, and they cost nothing to add here because the CLIENT resolves "my" — the model only
     names the intent, and the student's own device reads their own week. */
  { name: 'my_free', description: 'Show when the student is free.', parameters: { type: 'object', properties: { days: { type: 'array', items: { type: 'string', enum: ['Mo', 'Tu', 'We', 'Th', 'Fr'] } } } } },
  { name: 'my_conflicts', description: 'Show time clashes in the student’s own schedule.', parameters: { type: 'object', properties: {} } },
  { name: 'my_day', description: 'The student’s own classes on a day.', parameters: { type: 'object', properties: { days: { type: 'array', items: { type: 'string', enum: ['Mo', 'Tu', 'We', 'Th', 'Fr'] } }, rel: { type: 'string', enum: ['today', 'tomorrow'] } } } },
  { name: 'my_units', description: 'How many units the student is taking.', parameters: { type: 'object', properties: {} } },
  { name: 'my_professors', description: 'The professors teaching the student’s own classes, ranked by rating. For "which of my professors is best/worst rated", "who are my professors".', parameters: { type: 'object', properties: { order: { type: 'string', enum: ['desc', 'asc'], description: 'asc for lowest/worst first' } } } },
  { name: 'my_requirements', description: 'What the student still needs for their degree.', parameters: { type: 'object', properties: {} } },
  { name: 'prereqs', description: 'Whether the student has met a course’s prerequisites.', parameters: { type: 'object', required: ['course'], properties: { course: { type: 'string' } } } },
  { name: 'fit_pair', description: 'Whether two courses can be taken together this term.', parameters: { type: 'object', required: ['a', 'b'], properties: { a: { type: 'string' }, b: { type: 'string' } } } },
  { name: 'swap_section', description: 'Other sections of a class the student is already in.', parameters: { type: 'object', required: ['course'], properties: { course: { type: 'string' }, prefer: { type: 'string', enum: ['later', 'earlier'] } } } },
  { name: 'friends_took', description: 'Classes the student’s friends have already taken (their past classes), optionally only ones the student still needs, one course, or one subject. For "a class my friends took", "have my friends taken X".', parameters: { type: 'object', properties: { scope: { type: 'string', enum: ['ge_unmet', 'required'] }, course: { type: 'string' }, subject: { type: 'string' } } } },
  { name: 'friends_in', description: 'Which of the student’s friends are in a course.', parameters: { type: 'object', required: ['course'], properties: { course: { type: 'string' } } } },
  { name: 'when_registration', description: 'When registration opens.', parameters: { type: 'object', properties: {} } },
  /* 2026-09-25: the registration game plan. The CLIENT reads the student's own Plans A–C; the model
     only names which plan, if the student said one. */
  { name: 'game_plan', description: 'The order to register for the classes in one of the student’s plans, with a backup section for each. For "what do I register for first", "my game plan", "backups for plan B".', parameters: { type: 'object', properties: { plan: { type: 'string', enum: ['A', 'B', 'C'] } } } },
  { name: 'go_to', description: 'Open a screen of the app. ONLY when the student asks to open, find or change something on a screen ("where do I change my password" → account, "how do I import my schedule" → import schedule), never as a stand-in for an answer.', parameters: { type: 'object', required: ['where'], properties: { where: { type: 'string', enum: ['home', 'explore', 'explore professors', 'ge browser', 'find professor', 'schedule', 'my classes', 'week view', 'watchlist', 'watched professors', 'compare professors', 'planner', 'ledger', 'past classes', 'add past class', 'add past term', 'import schedule', 'share my schedule', 'friends', 'groups', 'messages', 'new message', 'add friend', 'my qr code', 'invite link', 'settings', 'appearance', 'account', 'privacy settings', 'about', 'edit profile', 'notifications', 'rate', 'my reviews', 'privacy policy', 'terms', 'community guidelines', 'security'] } } } },
  { name: 'help', description: 'What Hawk can do ("help", "what can you do").', parameters: { type: 'object', properties: {} } },
  { name: 'set_theme', description: 'Switch the app theme.', parameters: { type: 'object', required: ['theme'], properties: { theme: { type: 'string', enum: ['dark', 'light', 'cream'] } } } },
  { name: 'watch', description: 'Watch or stop watching a class, one section, or a professor (seat alerts, watchlist). "alert me when BUS4442 opens", "add X to my watchlist", "stop watching X".', parameters: { type: 'object', required: ['kind'], properties: { kind: { type: 'string', enum: ['class', 'section', 'professor'] }, course: { type: 'string' }, section: { type: 'string', description: 'section number, e.g. 2' }, name: { type: 'string', description: 'professor name' }, off: { type: 'boolean', description: 'true to stop watching' } } } },
  { name: 'open_section', description: 'One section of a course, e.g. "BUS4442-02", "BUS 4442 section 2".', parameters: { type: 'object', required: ['course', 'section'], properties: { course: { type: 'string' }, section: { type: 'string' } } } },
  { name: 'add_section', description: 'Add a class (optionally one section) to the student’s own classes. The student confirms in the app.', parameters: { type: 'object', required: ['course'], properties: { course: { type: 'string' }, section: { type: 'string' } } } },
  { name: 'rate_professor', description: 'Open the review form for a professor, or for the professor of one of the student’s courses. The student submits it.', parameters: { type: 'object', properties: { name: { type: 'string' }, course: { type: 'string' } } } },
  { name: 'draft_message', description: 'Open a chat with one of the student’s friends with a question typed in, about a course or professor. Never sends.', parameters: { type: 'object', required: ['friend'], properties: { friend: { type: 'string', description: 'the friend’s name as the student wrote it' }, course: { type: 'string' }, name: { type: 'string', description: 'a professor to ask about' } } } },
  { name: 'share', description: 'Send a class or a professor to a friend through the share sheet. The student picks who and sends.', parameters: { type: 'object', properties: { course: { type: 'string' }, name: { type: 'string', description: 'professor' }, friend: { type: 'string' } } } },
  { name: 'add_friend', description: 'Find a person to add as a friend.', parameters: { type: 'object', properties: { person: { type: 'string' } } } },
  { name: 'friend_profile', description: 'One friend’s current classes, past classes, or friends ("what is Maya taking", "Maya’s schedule").', parameters: { type: 'object', required: ['friend'], properties: { friend: { type: 'string' }, tab: { type: 'string', enum: ['classes', 'took', 'friends'] } } } },
  { name: 'professor_stats', description: 'A professor’s rating, number of ratings, would-take-again, hours, difficulty ("how hard is X", "would people take X again").', parameters: { type: 'object', required: ['name'], properties: { name: { type: 'string' } } } },
  { name: 'compare_professors', description: 'Compare two professors.', parameters: { type: 'object', required: ['a', 'b'], properties: { a: { type: 'string' }, b: { type: 'string' } } } },
  {
    name: 'build_term',
    description: 'Build complete class schedules for a term from the student’s constraints.',
    parameters: {
      type: 'object',
      properties: {
        units: { type: 'number', description: 'Target units, e.g. 15' },
        scope: { type: 'string', enum: ['ge_unmet', 'required'], description: 'Fill it from GE the student still needs, or everything their major still requires' },
        include: { type: 'array', items: { type: 'string' }, description: 'Course codes that must be in it' },
        days_off: { type: 'array', items: { type: 'string', enum: ['Mo', 'Tu', 'We', 'Th', 'Fr'] } },
        start_after: { type: 'string', description: 'HH:MM 24h, nothing earlier' },
        end_before: { type: 'string', description: 'HH:MM 24h, nothing later' },
        open_only: { type: 'boolean' },
        sort: { type: 'string', enum: ['rating', 'seats'] },
      },
    },
  },
  {
    name: 'cant_answer',
    description: 'Use when no other tool fits.',
    parameters: {
      type: 'object', required: ['reason'],
      properties: { reason: { type: 'string', enum: ['not_about_classes', 'needs_judgment', 'needs_private_data', 'ambiguous'] } },
    },
  },
];

export const SYSTEM = (term: string) =>
  `You route a Cal Poly student's question to one tool. Pick exactly one. The current term is ${term}. `
  + `Course codes are SUBJECT+NUMBER (BUS4442). Times are 24-hour. "Open" means seats available. `
  + `If the question is not about finding classes, sections or professors, or needs an opinion, `
  + `call cant_answer. Questions about the student's own classes, day, units, `
  + `requirements, professors, friends or prerequisites have their own tools; answer them with those, not go_to. Never guess a course that was not named. `
  + `For a recommendation, use search_sections and fill EVERY constraint the student gave at once: `
  + `scope for "GE I still need" or "for my major", fits_my_schedule, days, times, open_only, sort. `
  + `To plan a whole term ("build me a schedule", "15 units no Fridays"), use build_term. What to register for first, or backups, is game_plan. `
  + `Actions (watch, add_section, rate_professor, draft_message, share, add_friend, set_theme) only OPEN things for the student to finish; use them when asked. `
  + `If EARLIER is given, the question may be a follow-up: keep those filters unless the student changes them. `
  + `Reply only with a tool call, never with text.`;

/* ------------------------------------------------------------------------------------------------
   EXPLAIN — the second job, and the only place the model writes words a student reads.

   It is handed the rows the student is ALREADY looking at and asked for one or two sentences
   pointing at the best one and why. It is never asked a question it could answer from its own
   knowledge. Its sentences are checked twice before anyone reads them — here, and again in the
   browser against the rows on screen — and any course code, number or name that is not in those
   rows drops the whole sentence. A missing explanation costs nothing; a wrong one is the product
   stating a fact it cannot back.
   ------------------------------------------------------------------------------------------------ */
export const EXPLAIN_SYSTEM =
  `You help a Cal Poly student act on the search results TermChamp is showing them. `
  + `Write one or two short sentences, at most 45 words, in plain friendly English. `
  + `Use ONLY facts in ROWS. Every course code, time, name and number you write must appear in ROWS. `
  + `Do not describe how a professor teaches; you may mention their rating. `
  + `Point to the row that best answers the question and say why using its fields: fits their week, `
  + `rating, open seats, time, GE area. If the best-rated row does not fit their week, say so. `
  + `Reply only with the explain tool.`;

export const EXPLAIN_TOOLS = [{
  name: 'explain',
  description: 'The sentence or two to show the student.',
  parameters: { type: 'object', required: ['text'], properties: { text: { type: 'string' } } },
}];

export const ROW_KEYS = ['code', 'title', 'when', 'prof', 'rating', 'seats', 'tag', 'fits', 'yours'];
export function cleanRows(raw: any): Record<string, unknown>[] {
  if (!Array.isArray(raw)) return [];
  return raw.slice(0, 8).map((r: any) => {
    const o: Record<string, unknown> = {};
    for (const k of ROW_KEYS) {
      const v = r?.[k];
      if (typeof v === 'string') o[k] = v.slice(0, 90);
      else if (typeof v === 'number' || typeof v === 'boolean') o[k] = v;
    }
    return o;
  }).filter((o) => Object.keys(o).length);
}

/* The server's half of the grounding check. Every course code in the sentence must be in the rows. */
export function groundedText(text: string, rows: Record<string, unknown>[]): string | null {
  const t = String(text || '').replace(/\s+/g, ' ').trim();
  if (!t || t.length > 320 || /https?:|www\./i.test(t)) return null;
  const hay = JSON.stringify(rows).toUpperCase();
  const codes = t.toUpperCase().match(/\b[A-Z]{2,4}\s?\d{3,4}(?:-\d+)?\b/g) || [];
  for (const c of codes) {
    const bare = c.replace(/\s+/, ' ').replace(/-\d+$/, '');
    if (!hay.includes(bare)) return null;
  }
  return t;
}

/* ------------------------------------------------------------------------------------------------
   Vendor adapters.

   THE MODEL STRING PICKS THE VENDOR: "openai:gpt-5.6-luna", "anthropic:claude-haiku-4.5",
   "gemini:gemini-2.5-flash". One config row therefore chooses both, and swapping vendors is an
   UPDATE rather than a deploy — which matters, because the build plan's own conclusion is that the
   golden set picks the model, and that answer is not known until it has been run.
   ------------------------------------------------------------------------------------------------ */
/* The status alone — "vendor_400" — says a request was refused and nothing about why, which is
   what turned a one-line fix into a round trip through a redeploy. The vendor's own message is
   short, has no secret in it, and names the offending field. It is trimmed to a size the log
   column holds. */
export function vendorErr(status: number, j: any): string {
  const msg = j?.error?.message ?? j?.error?.status ?? j?.message ?? '';
  return ('vendor_' + status + (msg ? ': ' + String(msg).replace(/\s+/g, ' ').slice(0, 160) : ''));
}

export function splitModel(raw: string): { vendor: string; model: string } {
  const i = raw.indexOf(':');
  if (i < 0) return { vendor: 'openai', model: raw };
  return { vendor: raw.slice(0, i).toLowerCase(), model: raw.slice(i + 1) };
}

/* TWO KINDS OF CLAUDE, AND THE REQUEST HAS TO KNOW WHICH.

   The Claude 5 generation (Fable, Mythos, Opus 5, Sonnet 5) thinks by default and cannot be told
   not to: `thinking.type.disabled` is refused outright — the API's own words, read off a 400 on
   2026-09-24. What it accepts is `adaptive` thinking steered by `output_config.effort`, and with
   thinking on it also refuses `temperature: 0` and a FORCED tool choice. So those models get
   `effort: low` (the doc: "at lower levels, Claude can skip thinking entirely for simpler
   problems"), `tool_choice: auto`, and the system prompt does the forcing — a reply with no tool
   call is caught by validate() and becomes cant_answer.

   Haiku 4.5 is the other way round: no adaptive mode, no effort parameter, and it takes
   `temperature: 0` with `tool_choice: any` exactly as the plan assumed. The classic shape.

   The two are told apart by name. `tokens_out` in assistant_runs is what proves the effort
   setting is actually keeping thinking small — the doc calls effort "a behavioral signal, not a
   strict token budget", which is a sentence to measure rather than trust. */
export type Spec = { system: string; tools: any[]; user: string; force?: string };

export function anthropicBody(model: string, spec: Spec) {
  const adaptive = /fable|mythos|opus-5|sonnet-5/.test(model);
  const shared = {
    model, max_tokens: MAX_OUT,
    system: [{ type: 'text', text: spec.system, cache_control: { type: 'ephemeral' } }],
    tools: spec.tools.map((t) => ({ name: t.name, description: t.description, input_schema: t.parameters })),
    messages: [{ role: 'user', content: spec.user }],
  };
  if (adaptive) {
    return {
      ...shared,
      /* Thinking tokens count against max_tokens. 200 would cut a thought off before the tool
         call and every answer would arrive as cant_answer. 800 is headroom, not a budget — the
         cap and tokens_out are what bound it. */
      max_tokens: 800,
      thinking: { type: 'adaptive' },
      output_config: { effort: 'low' },
      tool_choice: { type: 'auto' },
    };
  }
  return { ...shared, temperature: 0,
           tool_choice: spec.force ? { type: 'tool', name: spec.force } : { type: 'any' } };
}

export async function callVendor(vendor: string, model: string, key: string, spec: Spec, signal: AbortSignal) {
  if (vendor === 'anthropic') {
    const r = await fetch('https://api.anthropic.com/v1/messages', {
      method: 'POST', signal,
      headers: { 'content-type': 'application/json', 'x-api-key': key, 'anthropic-version': '2023-06-01' },
      body: JSON.stringify(anthropicBody(model, spec)),
    });
    const j = await r.json();
    if (!r.ok) throw new Error(vendorErr(r.status, j));
    const block = (j.content || []).find((c: any) => c.type === 'tool_use');
    const text = (j.content || []).filter((c: any) => c.type === 'text').map((c: any) => c.text).join(' ').trim();
    return {
      name: block?.name, args: block?.input ?? {}, text,
      /* input_tokens EXCLUDES the tokens written to the cache; those arrive in
         cache_creation_input_tokens and are billed at 1.25x input. Left out, the estimate the daily
         cap runs on was missing the whole prefix on every first call. */
      usage: {
        in: (j.usage?.input_tokens ?? 0) + Math.round((j.usage?.cache_creation_input_tokens ?? 0) * 1.25),
        cached: j.usage?.cache_read_input_tokens ?? 0,
        out: j.usage?.output_tokens ?? 0,
      },
    };
  }

  if (vendor === 'gemini') {
    const r = await fetch(
      `https://generativelanguage.googleapis.com/v1beta/models/${encodeURIComponent(model)}:generateContent?key=${encodeURIComponent(key)}`,
      {
        method: 'POST', signal, headers: { 'content-type': 'application/json' },
        body: JSON.stringify({
          systemInstruction: { parts: [{ text: spec.system }] },
          contents: [{ role: 'user', parts: [{ text: spec.user }] }],
          tools: [{ functionDeclarations: spec.tools }],
          toolConfig: { functionCallingConfig: { mode: 'ANY' } },
          generationConfig: { temperature: 0, maxOutputTokens: MAX_OUT },
        }),
      },
    );
    const j = await r.json();
    if (!r.ok) throw new Error(vendorErr(r.status, j));
    const part = (j.candidates?.[0]?.content?.parts || []).find((p: any) => p.functionCall);
    return {
      name: part?.functionCall?.name, args: part?.functionCall?.args ?? {},
      usage: { in: j.usageMetadata?.promptTokenCount ?? 0, cached: j.usageMetadata?.cachedContentTokenCount ?? 0, out: j.usageMetadata?.candidatesTokenCount ?? 0 },
    };
  }

  // default: OpenAI chat completions with forced tool choice
  const r = await fetch('https://api.openai.com/v1/chat/completions', {
    method: 'POST', signal,
    headers: { 'content-type': 'application/json', authorization: `Bearer ${key}` },
    body: JSON.stringify({
      model, temperature: 0, max_tokens: MAX_OUT,
      tools: spec.tools.map((t) => ({ type: 'function', function: t })),
      tool_choice: 'required',
      messages: [{ role: 'system', content: spec.system }, { role: 'user', content: spec.user }],
    }),
  });
  const j = await r.json();
  if (!r.ok) throw new Error(vendorErr(r.status, j));
  const call = j.choices?.[0]?.message?.tool_calls?.[0];
  let args = {};
  try { args = call ? JSON.parse(call.function.arguments || '{}') : {}; } catch (_) { args = {}; }
  return {
    name: call?.function?.name, args,
    usage: { in: j.usage?.prompt_tokens ?? 0, cached: j.usage?.prompt_tokens_details?.cached_tokens ?? 0, out: j.usage?.completion_tokens ?? 0 },
  };
}

/* Keyed on the EXACT API model id, because that is what the config row holds. The first draft
   keyed on marketing names — 'claude-haiku-4.5' — which matched nothing, so every real model fell
   through to UNKNOWN_RATE, and UNKNOWN_RATE was set below Fable's actual price. The cap would have
   counted Fable at half its cost and tripped late. Prices per million tokens, read from
   platform.claude.com/docs/en/about-claude/pricing on 2026-09-23; re-check when a model changes. */
export const RATES: Record<string, [number, number, number]> = {   // [in, cache read, out]
  'claude-fable-5-1':          [10.00, 0.25, 50.00],
  'claude-opus-5':             [5.00, 0.50, 25.00],
  'claude-sonnet-5':           [2.00, 0.20, 10.00],
  'claude-haiku-4-5-20251001': [1.00, 0.10, 5.00],
  'claude-haiku-4-5':          [1.00, 0.10, 5.00],
  'gpt-5.6-luna':              [0.20, 0.02, 1.20],
  'gemini-2.5-flash':          [0.075, 0.075, 0.30],
  'gemini-3.1-flash-lite':     [0.25, 0.025, 1.50],
};
/* At or above the priciest model this table knows. A model this table has not heard of must never
   be counted cheaper than one it has. */
export const UNKNOWN_RATE: [number, number, number] = [10.00, 1.00, 50.00];

export function estimateUsd(model: string, u: { in: number; cached: number; out: number }) {
  const [ri, rc, ro] = RATES[model] ?? UNKNOWN_RATE;
  const fresh = Math.max(0, (u.in ?? 0) - (u.cached ?? 0));
  return (fresh * ri + (u.cached ?? 0) * rc + (u.out ?? 0) * ro) / 1_000_000;
}

/* ------------------------------------------------------------------------------------------------
   Validation. The model's output is never trusted to be well-formed — anything that does not match
   the schema exactly becomes cant_answer rather than reaching the client as a half-filled filter.
   ------------------------------------------------------------------------------------------------ */
export const HHMM = /^([01]\d|2[0-3]):[0-5]\d$/;
export const DAYS = ['Mo', 'Tu', 'We', 'Th', 'Fr', 'Sa', 'Su'];
export const MODES = ['in_person', 'hybrid', 'async', 'sync_online'];
export const COMPONENTS = ['LEC', 'LAB', 'ACT', 'SEM'];
export const REASONS = ['not_about_classes', 'needs_judgment', 'needs_private_data', 'ambiguous'];
export const NAMES = TOOLS.map((t) => t.name);

export function cantAnswer(reason = 'ambiguous') {
  return { tool: 'cant_answer', args: { reason } };
}

export function validate(name: string | undefined, raw: any) {
  if (!name || !NAMES.includes(name)) return cantAnswer();
  const a = (raw && typeof raw === 'object') ? raw : {};

  if (name === 'cant_answer') {
    return cantAnswer(REASONS.includes(a.reason) ? a.reason : 'ambiguous');
  }
  if (name === 'open_class') {
    const c = String(a.course ?? '').toUpperCase().replace(/\s+/g, '');
    if (!/^[A-Z]{2,4}\d{3,4}$/.test(c)) return cantAnswer();
    return { tool: 'open_class', args: { course: c } };
  }
  if (name === 'open_professor') {
    const n = String(a.name ?? '').trim().slice(0, 80);
    if (!n) return cantAnswer();
    return { tool: 'open_professor', args: { name: n } };
  }
  if (name === 'my_professors') {
    return { tool: 'my_professors', args: a.order === 'asc' ? { order: 'asc' } : {} };
  }
  if (name === 'my_conflicts' || name === 'my_units' || name === 'my_requirements' || name === 'when_registration') {
    return { tool: name, args: {} };
  }
  if (name === 'game_plan') {
    const p = String(a.plan ?? '').toUpperCase();
    return { tool: 'game_plan', args: ['A', 'B', 'C'].includes(p) ? { plan: p } : {} };
  }
  const course = (v: any) => {
    const c = String(v ?? '').toUpperCase().replace(/\s+/g, '');
    return /^[A-Z]{2,4}\d{3,4}$/.test(c) ? c : null;
  };
  if (name === 'friends_took') {
    const out: Record<string, unknown> = {};
    if (a.scope === 'ge_unmet' || a.scope === 'required') out.scope = a.scope;
    const c = course(a.course); if (c) out.course = c;
    if (typeof a.subject === 'string' && /^[A-Za-z]{2,4}$/.test(a.subject.trim())) out.subject = a.subject.trim().toUpperCase();
    return { tool: 'friends_took', args: out };
  }
  const person = (v: any) => { const t = String(v ?? '').replace(/[^\p{L}\p{M}' .-]/gu, '').trim().slice(0, 60); return t || null; };
  const secNo = (v: any) => { const n = parseInt(String(v ?? ''), 10); return n >= 1 && n <= 99 ? String(n) : null; };
  if (name === 'help') return { tool: 'help', args: {} };
  if (name === 'set_theme') {
    return ['dark', 'light', 'cream'].includes(a.theme) ? { tool: 'set_theme', args: { theme: a.theme } } : cantAnswer();
  }
  if (name === 'watch') {
    const out: Record<string, unknown> = {};
    const c = course(a.course), n = person(a.name), sec = secNo(a.section);
    if (a.kind === 'professor' && n) { out.kind = 'professor'; out.name = n; }
    else if (c && sec && a.kind !== 'class') { out.kind = 'section'; out.course = c; out.section = sec; }
    else if (c) { out.kind = 'class'; out.course = c; }
    else return cantAnswer();
    if (a.off === true) out.off = true;
    return { tool: 'watch', args: out };
  }
  if (name === 'open_section') {
    const c = course(a.course), sec = secNo(a.section);
    return c && sec ? { tool: 'open_section', args: { course: c, section: sec } } : cantAnswer();
  }
  if (name === 'add_section') {
    const c = course(a.course), sec = secNo(a.section);
    if (!c) return cantAnswer();
    return { tool: 'add_section', args: sec ? { course: c, section: sec } : { course: c } };
  }
  if (name === 'rate_professor') {
    const out: Record<string, unknown> = {};
    const n = person(a.name), c = course(a.course);
    if (n) out.name = n; if (c) out.course = c;
    return Object.keys(out).length ? { tool: 'rate_professor', args: out } : { tool: 'go_to', args: { where: 'rate' } };
  }
  if (name === 'draft_message') {
    const f = person(a.friend); if (!f) return cantAnswer();
    const out: Record<string, unknown> = { friend: f };
    const c = course(a.course), n = person(a.name);
    if (c) out.course = c; else if (n) out.name = n;
    return { tool: 'draft_message', args: out };
  }
  if (name === 'share') {
    const c = course(a.course), n = person(a.name), f = person(a.friend);
    if (!c && !n) return cantAnswer();
    const out: Record<string, unknown> = c ? { course: c } : { name: n };
    if (f) out.friend = f;
    return { tool: 'share', args: out };
  }
  if (name === 'add_friend') { const p = person(a.person); return { tool: 'add_friend', args: p ? { person: p } : {} }; }
  if (name === 'friend_profile') {
    const f = person(a.friend); if (!f) return cantAnswer();
    return { tool: 'friend_profile', args: { friend: f, tab: ['classes', 'took', 'friends'].includes(a.tab) ? a.tab : 'classes' } };
  }
  if (name === 'professor_stats') { const n = person(a.name); return n ? { tool: 'professor_stats', args: { name: n } } : cantAnswer(); }
  if (name === 'compare_professors') {
    const x = person(a.a), y = person(a.b);
    return x && y ? { tool: 'compare_professors', args: { a: x, b: y } } : cantAnswer();
  }
  if (name === 'prereqs' || name === 'friends_in') {
    const c = course(a.course); if (!c) return cantAnswer();
    return { tool: name, args: { course: c } };
  }
  if (name === 'swap_section') {
    const c = course(a.course); if (!c) return cantAnswer();
    const out: Record<string, unknown> = { course: c };
    if (a.prefer === 'later' || a.prefer === 'earlier') out.prefer = a.prefer;
    return { tool: 'swap_section', args: out };
  }
  if (name === 'fit_pair') {
    const x = course(a.a), y = course(a.b);
    if (!x || !y || x === y) return cantAnswer();
    return { tool: 'fit_pair', args: { a: x, b: y } };
  }
  if (name === 'my_day') {
    const out: Record<string, unknown> = {};
    if (a.rel === 'today' || a.rel === 'tomorrow') out.rel = a.rel;
    else if (Array.isArray(a.days)) { const d = a.days.filter((x: any) => DAYS.includes(x)); if (d.length) out.days = d; }
    return { tool: 'my_day', args: out };
  }
  if (name === 'build_term') {
    const out: Record<string, unknown> = {};
    if (typeof a.units === 'number' && a.units >= 3 && a.units <= 24) out.units = Math.round(a.units);
    if (a.scope === 'ge_unmet' || a.scope === 'required') out.scope = a.scope;
    if (Array.isArray(a.include)) { const inc = a.include.map(course).filter(Boolean).slice(0, 6); if (inc.length) out.include = inc; }
    if (Array.isArray(a.days_off)) { const d = a.days_off.filter((x: any) => ['Mo', 'Tu', 'We', 'Th', 'Fr'].includes(x)); if (d.length) out.days_off = d; }
    for (const k of ['start_after', 'end_before']) if (typeof a[k] === 'string' && HHMM.test(a[k])) out[k] = a[k];
    if (typeof a.open_only === 'boolean') out.open_only = a.open_only;
    if (a.sort === 'rating' || a.sort === 'seats') out.sort = a.sort;
    return { tool: 'build_term', args: out };
  }
  if (name === 'go_to') {
    const PLACES = ['home', 'explore', 'explore professors', 'ge browser', 'find professor', 'schedule', 'my classes', 'week view', 'watchlist', 'watched professors', 'compare professors', 'planner', 'ledger', 'past classes', 'add past class', 'add past term', 'import schedule', 'share my schedule', 'friends', 'groups', 'messages', 'new message', 'add friend', 'my qr code', 'invite link', 'settings', 'appearance', 'account', 'privacy settings', 'about', 'edit profile', 'notifications', 'rate', 'my reviews', 'privacy policy', 'terms', 'community guidelines', 'security'];
    const w = String(a.where ?? '').toLowerCase().trim();
    if (!PLACES.includes(w)) return cantAnswer();
    return { tool: 'go_to', args: { where: w } };
  }
  if (name === 'my_free') {
    const d = Array.isArray(a.days) ? a.days.filter((x: any) => DAYS.includes(x)) : [];
    return { tool: 'my_free', args: d.length ? { days: d } : {} };
  }

  // search_sections — copy only what is well-formed, drop the rest silently rather than guess
  const out: Record<string, unknown> = {};
  if (typeof a.subject === 'string' && /^[A-Za-z]{2,4}$/.test(a.subject)) out.subject = a.subject.toUpperCase();
  if (typeof a.course === 'string') {
    const c = a.course.toUpperCase().replace(/\s+/g, '');
    if (/^[A-Z]{2,4}\d{3,4}$/.test(c)) out.course = c;
  }
  if (Array.isArray(a.days)) {
    const d = a.days.filter((x: any) => DAYS.includes(x));
    if (d.length) out.days = d;
  }
  for (const k of ['at_time', 'start_after', 'end_before']) {
    if (typeof a[k] === 'string' && HHMM.test(a[k])) out[k] = a[k];
  }
  if (typeof a.open_only === 'boolean') out.open_only = a.open_only;
  if (typeof a.fits_my_schedule === 'boolean') out.fits_my_schedule = a.fits_my_schedule;
  if (typeof a.min_rating === 'number' && a.min_rating >= 1 && a.min_rating <= 5) out.min_rating = a.min_rating;
  if (MODES.includes(a.instruction_mode)) out.instruction_mode = a.instruction_mode;
  if (COMPONENTS.includes(a.component)) out.component = a.component;
  if (a.sort === 'rating' || a.sort === 'seats' || a.sort === 'easiest') out.sort = a.sort;
  if (typeof a.ge_area === 'string' && /^(1[ABC]|[2-6][ABC]?|UD[34]|U25|USCP|GWR)$/i.test(a.ge_area.replace(/\s+/g, ''))) out.ge_area = a.ge_area.replace(/\s+/g, '').toUpperCase();
  if (a.scope === 'ge_unmet' || a.scope === 'required') out.scope = a.scope;

  /* A search with nothing in it is not a search. It is the model having produced the right tool
     name and no usable arguments, which is a failure to understand, not an instruction to show
     every class at Cal Poly. */
  if (!Object.keys(out).length) return cantAnswer();
  return { tool: 'search_sections', args: out };
}

/* ------------------------------------------------------------------------------------------------ */
