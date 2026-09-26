/* Drives the real `ask` handler with the network stubbed: the gate, the logger and the vendor.
   Run: deno run --allow-env tests/check-ask-function.ts                                          */
let handler: (r: Request) => Promise<Response>;
(Deno as any).serve = (h: any) => { handler = h; return {} as any; };
Deno.env.set('SUPABASE_URL', 'http://sb'); Deno.env.set('SUPABASE_ANON_KEY', 'anon');
Deno.env.set('ASSISTANT_API_KEY', 'k');

let vendorReply: any = null, lastVendorBody: any = null, logs: any[] = [], gateModel = 'anthropic:claude-haiku-4-5-20251001';
(globalThis as any).fetch = async (url: string, init: any) => {
  const body = init?.body ? JSON.parse(init.body) : {};
  if (url.endsWith('/rpc/assistant_gate')) return new Response(JSON.stringify({ allowed: true, model: gateModel }));
  if (url.endsWith('/rpc/assistant_log_run')) { logs.push(body); return new Response('true'); }
  if (url.includes('api.anthropic.com')) { lastVendorBody = body; return new Response(JSON.stringify(vendorReply)); }
  throw new Error('unexpected fetch ' + url);
};
await import('../../supabase/functions/ask/index.ts');

let ok = 0, bad = 0;
const t = (name: string, cond: boolean, extra?: unknown) => {
  if (cond) { ok++; console.log('  ok  ' + name); } else { bad++; console.log('FAIL  ' + name, extra ?? ''); }
};
const call = async (b: unknown) => (await handler(new Request('http://x', {
  method: 'POST', headers: { authorization: 'Bearer abc' }, body: JSON.stringify(b) }))).json();
const tool = (name: string, input: unknown, extra: any[] = []) =>
  ({ content: [...extra, { type: 'tool_use', name, input }], usage: { input_tokens: 100, output_tokens: 20 } });

// ---- route, with a follow-up's earlier filters
vendorReply = tool('search_sections', { subject: 'BUS', days: ['Mo'], open_only: true });
let r = await call({ q: 'only open ones', term: '2268', prev: { subject: 'BUS', days: ['Mo'], junk: 'x' } });
t('route returns the validated tool', r.tool === 'search_sections' && r.args.subject === 'BUS');
t('prev reaches the model as EARLIER, validated', /^EARLIER: \{.*"subject":"BUS"/.test(lastVendorBody.messages[0].content) && !/junk/.test(lastVendorBody.messages[0].content));
t('haiku is forced to a tool', lastVendorBody.tool_choice.type === 'any' && lastVendorBody.temperature === 0);
t('route is logged with its tool', logs.at(-1).p_tool === 'search_sections');

// ---- build_term
vendorReply = tool('build_term', { units: 15, scope: 'ge_unmet', days_off: ['Fr', 'Sa'], start_after: '10:00', end_before: '25:00', sort: 'rating' });
r = await call({ q: '15 units of GEs I need, no fridays, nothing before 10, best professors' });
t('build_term validated', r.tool === 'build_term' && r.args.units === 15 && r.args.scope === 'ge_unmet'
  && JSON.stringify(r.args.days_off) === '["Fr"]' && r.args.start_after === '10:00' && !('end_before' in r.args) && r.args.sort === 'rating', r);
vendorReply = tool('build_term', { units: 99, include: ['bus 4442', 'nonsense!!'] });
r = await call({ q: 'build me a term' });
t('silly units dropped, include cleaned', !('units' in r.args) && JSON.stringify(r.args.include) === '["BUS4442"]', r);

vendorReply = tool('my_professors', { order: 'asc', junk: 1 });
r = await call({ q: 'my worst professor' });
t('my_professors validated', r.tool === 'my_professors' && r.args.order === 'asc' && !('junk' in r.args), r);

vendorReply = tool('friends_took', { scope: 'ge_unmet', course: 'bus 4442', subject: 'csc ', junk: 1 });
r = await call({ q: 'a ge my friends took' });
t('friends_took validated', r.tool === 'friends_took' && r.args.scope === 'ge_unmet' && r.args.course === 'BUS4442' && r.args.subject === 'CSC' && !('junk' in r.args), r);

// ---- game_plan (2026-09-25)
vendorReply = tool('game_plan', { plan: 'b', junk: 1 });
r = await call({ q: 'what do i register for first in plan b' });
t('game_plan validated: plan upper-cased, junk dropped', r.tool === 'game_plan' && r.args.plan === 'B' && !('junk' in r.args), r);
vendorReply = tool('game_plan', { plan: 'D' });
r = await call({ q: 'my game plan' });
t('game_plan: a plan that does not exist is dropped, not passed', r.tool === 'game_plan' && !('plan' in r.args), r);

// ---- explain
const rows = [
  { code: 'COMM 2204', title: 'Public Speaking', when: 'Tu/Th 10:00–11:15', prof: 'Dana Ruiz', rating: 4.7, seats: 6, fits: true },
  { code: 'PHIL 2020', title: 'Ethics', when: 'Online', prof: 'Sam Lee', rating: 4.5, seats: 12, fits: true, secret: 'x' },
];
vendorReply = tool('explain', { text: 'COMM 2204 with Dana Ruiz (4.7★) fits your week and still has 6 seats.' });
r = await call({ mode: 'explain', q: 'best GE for me', reading: 'GE you still need · fits your week', rows });
t('grounded explanation kept', r.tool === 'explain' && /COMM 2204/.test(r.args.text), r);
t('explain forces the explain tool on haiku', lastVendorBody.tool_choice.name === 'explain');
t('rows are cleaned before the model sees them', !/secret/.test(lastVendorBody.messages[0].content));
t('explain logged by shape, not words', logs.at(-1).p_tool === 'explain' && logs.at(-1).p_args.kept === true && !('text' in logs.at(-1).p_args));

vendorReply = tool('explain', { text: 'Take BIO 1610 instead, it is easier.' });
r = await call({ mode: 'explain', q: 'best GE for me', rows });
t('a course not on screen drops the sentence', r.tool === 'explain' && !r.args.text, r);
vendorReply = tool('explain', { text: 'See https://ratemyprofessors.com for more.' });
r = await call({ mode: 'explain', q: 'x', rows });
t('links drop the sentence', !r.args.text);
r = await call({ mode: 'explain', q: 'x', rows: [] });
t('explain without rows refused', r.error === 'rows');

// ---- adaptive model: thinking + text reply accepted for explain
gateModel = 'anthropic:claude-fable-5-1';
vendorReply = { content: [{ type: 'thinking', thinking: '...' }, { type: 'text', text: 'PHIL 2020 is online and has 12 seats.' }], usage: { input_tokens: 50, output_tokens: 30 } };
r = await call({ mode: 'explain', q: 'x', rows });
t('fable: adaptive thinking, auto tool choice', lastVendorBody.thinking?.type === 'adaptive' && lastVendorBody.tool_choice.type === 'auto' && !('temperature' in lastVendorBody));
t('fable: a plain-text explanation is still checked and kept', /PHIL 2020/.test(r.args.text || ''), r);

// ---- vendor failure
(globalThis as any).fetch = async (url: string) => url.includes('anthropic') ? new Response('{"error":{"message":"overloaded"}}', { status: 529 })
  : url.endsWith('/rpc/assistant_gate') ? new Response(JSON.stringify({ allowed: true, model: gateModel })) : (logs.push('x'), new Response('true'));
r = await call({ mode: 'explain', q: 'x', rows });
t('vendor failure falls back quietly', r.fallback === 'search' && /overloaded|529/.test(r.reason), r);

// ---- the new actions validate to what the client renders
gateModel = 'anthropic:claude-haiku-4-5-20251001';
(globalThis as any).fetch = async (url: string, init: any) => {
  const body = init?.body ? JSON.parse(init.body) : {};
  if (url.endsWith('/rpc/assistant_gate')) return new Response(JSON.stringify({ allowed: true, model: gateModel }));
  if (url.endsWith('/rpc/assistant_log_run')) { logs.push(body); return new Response('true'); }
  if (url.includes('api.anthropic.com')) { lastVendorBody = body; return new Response(JSON.stringify(vendorReply)); }
  throw new Error('unexpected fetch ' + url);
};
const cases: [string, any, (r: any) => boolean][] = [
  ['watch', { kind: 'section', course: 'bus 4442', section: '02' }, (r) => r.args.kind === 'section' && r.args.section === '2'],
  ['watch', { kind: 'professor', name: 'Beth Chance<script>', off: true }, (r) => r.args.name === 'Beth Chancescript' && r.args.off === true],
  ['add_section', { course: 'bus4442' }, (r) => r.args.course === 'BUS4442' && !('section' in r.args)],
  ['rate_professor', {}, (r) => r.tool === 'go_to' && r.args.where === 'rate'],
  ['draft_message', { friend: 'Maya', course: 'stat 2170', name: 'X' }, (r) => r.args.friend === 'Maya' && r.args.course === 'STAT2170' && !('name' in r.args)],
  ['share', { friend: 'Maya' }, (r) => r.tool === 'cant_answer'],
  ['set_theme', { theme: 'purple' }, (r) => r.tool === 'cant_answer'],
  ['go_to', { where: 'Import Schedule' }, (r) => r.args.where === 'import schedule'],
  ['go_to', { where: 'bank' }, (r) => r.tool === 'cant_answer'],
  ['compare_professors', { a: 'A B', b: 'C D' }, (r) => r.args.a === 'A B' && r.args.b === 'C D'],
];
for (const [name, input, check] of cases) {
  vendorReply = tool(name, input);
  const rr = await call({ q: 'x ' + name });
  t(`validate ${name} ${JSON.stringify(input).slice(0, 40)}`, check(rr), rr);
}

// ---- privacy guards (review, 2026-09-24)
vendorReply = tool('help', {});
logs.length = 0;
r = await call({ q: 'what can you do', nolog: true });
t('Global Privacy Control: answered, but neither the question nor its args are kept', r.tool === 'help' && logs.at(-1)?.p_q === '' && logs.at(-1)?.p_args === null, logs.at(-1));
r = await call({ q: 'what can you do' });
t('without it, the question is kept', logs.at(-1)?.p_q === 'what can you do');
gateModel = 'openai:gpt-5-mini';
r = await call({ q: 'what can you do' });
t('a non-Anthropic model in the config is refused, not called', r.fallback === 'search' && r.reason === 'vendor_not_allowed', r);
gateModel = 'gpt-5-mini';
r = await call({ q: 'what can you do' });
t('…including an unprefixed one (which would default to OpenAI)', r.reason === 'vendor_not_allowed', r);
gateModel = 'anthropic:claude-haiku-4-5-20251001';

// ---- the four lists that must agree: function tools, SQL whitelist, and the places
const src = await Deno.readTextFile(new URL('../../supabase/functions/ask/shared.ts', import.meta.url));
const toolsBlock = src.slice(src.indexOf('const TOOLS'), src.indexOf('const SYSTEM'));
const toolNames = [...toolsBlock.matchAll(/\{\s*name: '([a-z_]+)'/g)].map((m) => m[1]).concat(['explain']).sort();
const sql = await Deno.readTextFile(new URL('../../sql/professify-assistant-v6.sql', import.meta.url));
const wl = sql.slice(sql.indexOf("p_tool not in"), sql.indexOf('then\n    return false'));
const sqlNames = [...wl.matchAll(/'([a-z_]+)'/g)].map((m) => m[1]).sort();
t('SQL whitelist names every tool the function can emit', JSON.stringify(sqlNames) === JSON.stringify(toolNames), { onlyTools: toolNames.filter((x) => !sqlNames.includes(x)), onlySql: sqlNames.filter((x) => !toolNames.includes(x)) });
const serverPlaces = [...(src.match(/const PLACES = \[([^\]]*)\]/) || ['', ''])[1].matchAll(/'([^']+)'/g)].map((m) => m[1]).sort();
const router = await Deno.readTextFile(new URL('../../hawk-router.js', import.meta.url));
const routerPlaces = [...router.slice(router.indexOf('var PLACES = ['), router.indexOf('var NAV =')).matchAll(/\['([a-z ]+)',/g)].map((m) => m[1]).sort();
const client = await Deno.readTextFile(new URL('../../hawk-ask.js', import.meta.url));
const cblock = client.slice(client.indexOf('  var PLACES = {'), client.indexOf('var PLACE_KEYS'));
const clientPlaces = [...cblock.matchAll(/^\s+'([a-z ]+)':/gm)].map((m) => m[1]);
console.log('  lists:', toolNames.length, sqlNames.length, serverPlaces.length, routerPlaces.length, clientPlaces.length);
t('every place the router reads, the function allows', routerPlaces.every((p) => serverPlaces.includes(p)), routerPlaces.filter((p) => !serverPlaces.includes(p)));
t('every place the function allows, the client can open', serverPlaces.every((p) => clientPlaces.includes(p)), serverPlaces.filter((p) => !clientPlaces.includes(p)));
t('and the router reads every one of them', serverPlaces.every((p) => routerPlaces.includes(p)), serverPlaces.filter((p) => !routerPlaces.includes(p)));

console.log(`\n${ok} ok, ${bad} fail`);
if (bad) Deno.exit(1);
