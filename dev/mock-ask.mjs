/* A stand-in for the `ask` Edge Function, so the whole model path can be driven before a vendor
   account exists, a key is set, or a cent is spent.

   IT IS NOT A TEST OF THE MODEL and does not pretend to be. It returns fixed tool calls for a
   handful of questions, which proves exactly one thing: that the CLIENT half — the call, the
   token, the timeout, the render, and every fallback — is wired correctly. Whether a real model
   picks the right tool is what the golden set measures, and that needs a real key.

   The distinction matters because a mock that looks like a passing test is how a system gets
   declared working before anything real has run through it.

   Usage:  node mock-ask.mjs [port]        (default 8787)
           Then point PROFESSIFY_CONFIG.SUPABASE_URL at http://localhost:8787
*/
import http from 'node:http';

const PORT = Number(process.argv[2] || 8787);

/* Deliberately questions the pre-router CANNOT place, because those are the only ones that ever
   reach this tier. Each is a shape the free router gives up on for a different reason. */
const CANNED = [
  [/\b(?:build|make|plan)\b.*\b(?:schedule|term)\b|\d+\s*units?\b/i, 'BUILD'],
  /* The live miss of 2026-09-23, reproduced: the model answered this with a My classes button. */
  [/professor of mine/i, { tool: 'go_to', args: { where: 'my classes' } }],
  [/easiest|easier|better|worth|should i/i, { tool: 'cant_answer', args: { reason: 'needs_judgment' } }],
  [/friend|roommate|who.?s in/i, { tool: 'cant_answer', args: { reason: 'needs_private_data' } }],
  [/something.*morning|anything.*morning/i, { tool: 'search_sections', args: { end_before: '12:00', open_only: true } }],
  [/lab.*(evening|night)/i, { tool: 'search_sections', args: { component: 'LAB', start_after: '17:00' } }],
  [/free|busy|when am i/i, { tool: 'my_free', args: {} }],
  [/clash|conflict|overlap/i, { tool: 'my_conflicts', args: {} }],
  [/\b([a-z]{2,4})\s?(\d{3,4})\b/i, null],   // resolved below into open_class
];

function decide(q) {
  for (const [re, out] of CANNED) {
    const m = re.exec(q);
    if (!m) continue;
    if (out === 'BUILD') {
      const u = /(\d{1,2})\s*units?/i.exec(q);
      const a = { sort: 'rating' };
      if (u) a.units = Number(u[1]);
      if (/\bge/i.test(q)) a.scope = 'ge_unmet';
      if (/no\s+fridays?/i.test(q)) a.days_off = ['Fr'];
      return { tool: 'build_term', args: a };
    }
    if (out) return out;
    return { tool: 'open_class', args: { course: (m[1] + m[2]).toUpperCase() } };
  }
  return { tool: 'cant_answer', args: { reason: 'ambiguous' } };
}

const srv = http.createServer((req, res) => {
  const cors = {
    'access-control-allow-origin': '*',
    'access-control-allow-headers': 'authorization, content-type',
    'access-control-allow-methods': 'POST, OPTIONS',
  };
  if (req.method === 'OPTIONS') { res.writeHead(204, cors); return res.end(); }
  if (!/\/functions\/v1\/ask$/.test(req.url.split('?')[0])) { res.writeHead(404, cors); return res.end('{}'); }

  let body = '';
  req.on('data', (c) => { body += c; });
  req.on('end', () => {
    let q = '', parsed = {};
    try { parsed = JSON.parse(body || '{}'); q = String(parsed.q || ''); } catch (_) {}
    const auth = req.headers.authorization || '';

    /* The real function refuses without a session, so the mock does too — otherwise the signed-out
       path would go untested and the first student to hit it would find out for us. */
    if (!/^Bearer\s+\S+/i.test(auth)) {
      res.writeHead(401, { ...cors, 'content-type': 'application/json' });
      return res.end(JSON.stringify({ error: 'auth', fallback: 'search' }));
    }

    /* EXPLAIN: echo a sentence built from the first row — and, when the question asks for it, one
       that names a class NOT in the rows, so the browser's check is seen to drop it. */
    if (parsed.mode === 'explain') {
      const r0 = (parsed.rows || [])[0] || {};
      const text = /lie/i.test(q)
        ? 'Take BIO 1610 with Dr. Nobody, it is the easiest.'
        : `${String(r0.code || '').replace(/-\d+$/, '')} with ${r0.prof || 'Staff'} is the top pick${r0.rating != null ? ` at ${r0.rating}★` : ''}.`;
      console.log(`  explain  "${q}"  ->  ${text}`);
      res.writeHead(200, { ...cors, 'content-type': 'application/json' });
      return res.end(JSON.stringify({ tool: 'explain', args: { text }, model: 'mock:fixed-answers', usage: { in: 300, cached: 0, out: 30 }, ms: 20 }));
    }
    const picked = decide(q);
    const out = { ...picked, model: 'mock:fixed-answers', usage: { in: 1200, cached: 1100, out: 60 }, ms: 40 };
    console.log(`  ask  "${q}"  ->  ${picked.tool} ${JSON.stringify(picked.args)}`);
    setTimeout(() => {
      res.writeHead(200, { ...cors, 'content-type': 'application/json' });
      res.end(JSON.stringify(out));
    }, 250);   // a plausible round trip, so the "Working that out…" state is actually exercised
  });
});

srv.listen(PORT, () => {
  console.log(`mock ask listening on http://localhost:${PORT}/functions/v1/ask`);
  console.log('point PROFESSIFY_CONFIG.SUPABASE_URL at it, sign in, and ask something the router cannot place.');
});
