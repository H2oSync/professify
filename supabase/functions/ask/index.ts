/* ================================================================================================
   ask — the model tier for Hawk
   ================================================================================================
   Phase 1 of `cheap-assistant-build-plan-2026-09-20.md`. The pre-router in the browser answers the
   questions it is sure about for nothing; this is what the rest go to.

   THE MODEL'S ONLY JOB IS TO PICK A TOOL AND FILL ITS ARGUMENTS. It never writes a sentence about a
   class. Its entire legal output is one tool call with typed arguments and no free-text field, so
   there is no channel through which it can state a fact, invent a seat count, or answer a question
   about Germany. That is not a prompt instruction — it is the shape of the response, enforced here
   by validation before anything reaches the client.

   THIS FUNCTION NEVER TOUCHES DATA. It has no service-role key and cannot read any table but its
   own counters, through two SECURITY DEFINER functions the signed-in student is allowed to call. It
   returns a tool call; the CLIENT runs the query with its own session, under its own RLS, exactly
   as it does when a student taps a filter. Nothing about the student, their friends, their schedule
   or their classes is in this file's outbound request. The vendor gets the static prefix and the
   question, and nothing else.

   WHAT GOES OUT                          WHAT NEVER GOES OUT
   the system prompt + tool schemas        any row from any table
   the current term                        the JWT, the user id, the pseudonym
   the student's question (≤300 chars)     friends, schedules, reviews, ratings, seat counts

   Deploy:  supabase functions deploy ask
   Secret:  supabase secrets set ASSISTANT_API_KEY=...        ← Tate's to run. Never through chat.
   Switch on: two updates in assistant_config (model, enabled). It ships off.
   ============================================================================================== */

import {
  MAX_Q, TIMEOUT_MS, CORS, TOOLS, SYSTEM, EXPLAIN_SYSTEM, EXPLAIN_TOOLS, cleanRows, groundedText,
  splitModel, callVendor, estimateUsd, validate, type Spec,
} from './shared.ts';

const ALLOWED_VENDORS = ['anthropic'];

Deno.serve(async (req: Request) => {
  if (req.method === 'OPTIONS') return new Response('ok', { headers: CORS });
  const json = (body: unknown, status = 200) =>
    new Response(JSON.stringify(body), { status, headers: { ...CORS, 'content-type': 'application/json' } });

  if (req.method !== 'POST') return json({ error: 'method' }, 405);

  const auth = req.headers.get('authorization') || '';
  if (!/^Bearer\s+\S+/i.test(auth)) return json({ error: 'auth', fallback: 'search' }, 401);

  let body: any = {};
  try { body = await req.json(); } catch (_) { return json({ error: 'body' }, 400); }
  const q = String(body?.q ?? '').trim().slice(0, MAX_Q);
  const term = String(body?.term ?? '').slice(0, 20) || 'the current term';
  const who = String(body?.who ?? '').slice(0, 32);
  const mode = body?.mode === 'explain' ? 'explain' : 'route';
  /* Global Privacy Control, sent by the browser as nolog: the question is still answered, but the
     run is logged without its words OR its arguments (which can repeat them — a name, a subject).
     What remains is that a question was asked, which tool, and what it cost. */
  const keepQ = body?.nolog === true ? '' : q;
  if (!q) return json({ error: 'empty' }, 400);

  /* Route: the question, plus the last search's filters when the browser thinks this is a
     follow-up — only the filter object, never results or the student's classes.
     Explain: the question, what Hawk read it as, and the public catalog rows already on screen. */
  let spec: Spec;
  let rows: Record<string, unknown>[] = [];
  if (mode === 'explain') {
    rows = cleanRows(body?.rows);
    if (!rows.length) return json({ error: 'rows' }, 400);
    const reading = String(body?.reading ?? '').slice(0, 160);
    spec = {
      system: EXPLAIN_SYSTEM, tools: EXPLAIN_TOOLS, force: 'explain',
      user: `QUESTION: ${q}\nREAD AS: ${reading || '(same)'}\nROWS: ${JSON.stringify(rows)}`,
    };
  } else {
    let prev = '';
    if (body?.prev && typeof body.prev === 'object') {
      const p = validate('search_sections', body.prev);
      if (p?.tool === 'search_sections' && Object.keys(p.args || {}).length) prev = JSON.stringify(p.args).slice(0, 400);
    }
    spec = { system: SYSTEM(term), tools: TOOLS, user: prev ? `EARLIER: ${prev}\nQUESTION: ${q}` : q };
  }

  const SUPABASE_URL = Deno.env.get('SUPABASE_URL') ?? '';
  const ANON = Deno.env.get('SUPABASE_ANON_KEY') ?? '';
  const KEY = Deno.env.get('ASSISTANT_API_KEY') ?? '';

  const rpc = (fn: string, args: unknown) =>
    fetch(`${SUPABASE_URL}/rest/v1/rpc/${fn}`, {
      method: 'POST',
      headers: { 'content-type': 'application/json', apikey: ANON, authorization: auth },
      body: JSON.stringify(args),
    });

  /* THE GATE RESERVES BEFORE THE MODEL IS CALLED, NOT AFTER. If the vendor times out or this
     process dies, the student has still spent their slot — because counting afterwards makes every
     crash a free retry, and a crash loop is exactly the shape of the runaway the cap exists to
     stop. */
  let gate: any = null;
  try {
    const g = await rpc('assistant_gate', {});
    gate = await g.json();
  } catch (_) {
    return json({ fallback: 'search', reason: 'gate_unreachable' }, 200);
  }
  if (!gate?.allowed) {
    return json({ fallback: 'search', reason: gate?.reason ?? 'disabled' }, 200);
  }
  if (!KEY) {
    /* Enabled in the database but no key in the secrets: a configuration mistake, and the student
       gets the ordinary search rather than a spinner that dies. */
    return json({ fallback: 'search', reason: 'no_key' }, 200);
  }

  const { vendor, model } = splitModel(String(gate.model || ''));
  /* ONLY ANTHROPIC, ON PURPOSE. shared.ts can still talk to other vendors, but the Privacy Policy
     names Anthropic as the one company that receives Hawk questions — so a one-row change to
     assistant_config must not be able to send them anywhere else without the policy changing
     first (review, 2026-09-24). To add a vendor: change the policy, then add it here. */
  if (!ALLOWED_VENDORS.includes(vendor)) {
    return json({ fallback: 'search', reason: 'vendor_not_allowed' }, 200);
  }
  const started = Date.now();
  const ctl = new AbortController();
  const timer = setTimeout(() => ctl.abort(), TIMEOUT_MS);

  let picked, usage = { in: 0, cached: 0, out: 0 }, failed = '';
  try {
    const r: any = await callVendor(vendor, model, KEY, spec, ctl.signal);
    usage = r.usage;
    if (mode === 'explain') {
      const raw = r.name === 'explain' ? String(r.args?.text ?? '') : String(r.text ?? '');
      const text = groundedText(raw, rows);
      picked = { tool: 'explain', args: text ? { text } : {} };
    } else {
      picked = validate(r.name, r.args);
    }
  } catch (e) {
    failed = (e instanceof Error ? e.message : 'error').slice(0, 200);
  } finally {
    clearTimeout(timer);
  }
  const ms = Date.now() - started;

  if (failed) {
    try {
      await rpc('assistant_log_run', {
        p_who: who, p_q: keepQ, p_tool: mode === 'explain' ? 'explain' : 'cant_answer',
        p_reason: mode === 'explain' ? null : 'ambiguous',
        p_model: gate.model, p_ms: ms, p_fallback: true, p_usd: 0,
      });
    } catch (_) { /* logging must never be why a student sees an error */ }
    return json({ fallback: 'search', reason: failed }, 200);
  }

  const usd = estimateUsd(model, usage);
  try {
    await rpc('assistant_log_run', {
      p_who: who, p_q: keepQ, p_tool: picked!.tool,
      /* An explanation is logged by length and whether it survived the check, not by its words:
         the words are about the rows, and the rows can be rebuilt from the question. */
      p_args: keepQ === '' ? null : (mode === 'explain' ? { rows: rows.length, kept: !!(picked!.args as any).text } : picked!.args),
      p_reason: picked!.tool === 'cant_answer' ? (picked!.args as any).reason : null,
      p_model: gate.model, p_in: usage.in, p_cached: usage.cached, p_out: usage.out,
      p_ms: ms, p_prerouted: false, p_fallback: false, p_usd: usd,
    });
  } catch (_) { /* same */ }

  return json({ ...picked, model: gate.model, usage, ms });
});
