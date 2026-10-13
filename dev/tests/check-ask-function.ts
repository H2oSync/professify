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
{ /* Haiku 5.5 (2026-10-11): thinking off, tool forced, no temperature; priced at its own rate */
  const SH: any = await import('../../supabase/functions/ask/shared.ts');
  const b = SH.anthropicBody('claude-haiku-5-5', { system: 's', tools: [{ name: 'x', description: 'd', parameters: { type: 'object', properties: {} } }], user: 'u' });
  t('haiku 5.5: thinking off, tool forced, no temperature, no effort', b.thinking?.type === 'disabled' && b.tool_choice?.type === 'any' && !('temperature' in b) && !b.output_config);
  const e = SH.anthropicBody('claude-haiku-5-5', { system: 's', tools: [], user: 'u', force: 'explain' });
  t('haiku 5.5: explain is forced by name', e.tool_choice?.type === 'tool' && e.tool_choice?.name === 'explain' && e.thinking?.type === 'disabled');
  const h45 = SH.anthropicBody('claude-haiku-4-5-20251001', { system: 's', tools: [], user: 'u' });
  t('haiku 4.5 unchanged: temperature 0, forced, no thinking field', h45.temperature === 0 && h45.tool_choice?.type === 'any' && !('thinking' in h45));
  const f = SH.anthropicBody('claude-sonnet-5-5', { system: 's', tools: [], user: 'u' });
  t('sonnet 5.5 stays adaptive (not the haiku-5 shape)', f.thinking?.type === 'adaptive' && f.tool_choice?.type === 'auto');
  const usd = SH.estimateUsd('claude-haiku-5-5', { in: 1_000_000, cached: 0, out: 1_000_000 });
  t('haiku 5.5 is priced at $0.10 in / $0.50 out per million', Math.abs(usd - 0.60) < 1e-9, usd);
  t('haiku 5.5 cache reads at $0.01 per million', Math.abs(SH.estimateUsd('claude-haiku-5-5', { in: 1_000_000, cached: 1_000_000, out: 0 }) - 0.01) < 1e-9);
}
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

// ---- the phone's own menu (2026-10-08): client 'app' gets APP_TOOLS + APP_SYSTEM; everyone else is unchanged
const shared = await import('../../supabase/functions/ask/shared.ts');
vendorReply = tool('friends_free_now', { junk: 1 });
r = await call({ q: 'who is free right now', client: 'app' });
const appTools = lastVendorBody.tools.map((x: any) => x.name);
t('app: the phone menu is sent — the phone\'s own five tools, then every website tool, cant_answer last',
  JSON.stringify(appTools) === JSON.stringify(['friends_free_now', 'free_with_friends', 'best_professor', 'fits_plan', 'app_help', ...shared.TOOLS.map((x: any) => x.name).filter((n: string) => n !== 'cant_answer'), 'cant_answer']), appTools);
t('app: its prompt says who-is-free means friends', /"who's free" is friends_free_now/i.test(lastVendorBody.system[0].text) && /never make up a subject code/i.test(lastVendorBody.system[0].text) && /\bbiz\b/.test(lastVendorBody.system[0].text), lastVendorBody.system[0].text.slice(0, 120));
t('app: friends_free_now validated (junk dropped) and logged', r.tool === 'friends_free_now' && JSON.stringify(r.args) === '{}' && logs.at(-1).p_tool === 'friends_free_now', r);
t('app: every phone tool keeps the website tool\'s parameters, apart from go_to and set_theme',
  shared.TOOLS.every((w: any) => ['go_to', 'set_theme'].includes(w.name) || JSON.stringify(shared.APP_TOOLS.find((x: any) => x.name === w.name).parameters) === JSON.stringify(w.parameters)));
t('app: every phone tool has its own description with an example', shared.APP_TOOLS.every((x: any) => x.name === 'cant_answer' || /E\.g\. "/.test(x.description)), shared.APP_TOOLS.filter((x: any) => x.name !== 'cant_answer' && !/E\.g\. "/.test(x.description)).map((x: any) => x.name));
const goApp = shared.APP_TOOLS.find((x: any) => x.name === 'go_to').parameters.properties.where.enum;
const srcApp = await Deno.readTextFile(new URL('../../supabase/functions/ask/shared.ts', import.meta.url));
const serverPl = [...(srcApp.match(/const PLACES = \[([^\]]*)\]/) || ['', ''])[1].matchAll(/'([^']+)'/g)].map((m) => m[1]);
t('app: every phone place is one the function allows', goApp.every((p: string) => serverPl.includes(p)), goApp.filter((p: string) => !serverPl.includes(p)));
await call({ q: 'who is free', client: 'app', term: '2268' });
t('app: the term is named for the phone too (2268 → Fall 2026)', /The current term is Fall 2026\./.test(lastVendorBody.system[0].text));
vendorReply = tool('search_sections', { subject: 'BUS' });
await call({ q: 'bus', client: 'web' });
t('web: an unknown or missing client gets the website menu and prompt, unchanged',
  JSON.stringify(lastVendorBody.tools.map((x: any) => x.name)) === JSON.stringify(shared.TOOLS.map((x: any) => x.name))
  && lastVendorBody.tools.every((x: any, i: number) => x.description === shared.TOOLS[i].description) && lastVendorBody.system[0].text === shared.SYSTEM('the current term'));
const { fingerprint } = await import('../golden/score.ts');
t('web: the website prompt and tools are exactly the 2026-09-26 ones (pinned fingerprint, not compared with themselves)',
  await fingerprint(shared.SYSTEM('Fall 2026'), shared.TOOLS) === '93863fadfa725c29', await fingerprint(shared.SYSTEM('Fall 2026'), shared.TOOLS));
await call({ q: 'bus' });
t('…and with no client at all (the live phone build)', JSON.stringify(lastVendorBody.tools.map((x: any) => x.name)) === JSON.stringify(shared.TOOLS.map((x: any) => x.name)));
const appCases: [string, any, (r: any) => boolean][] = [
  ['free_with_friends', { friend: 'Maya<b>', days: ['Tu', 'Sa', 'x'], junk: 1 }, (r) => r.args.friend === 'Mayab' && JSON.stringify(r.args.days) === '["Tu"]' && !('junk' in r.args)],
  ['free_with_friends', { rel: 'tomorrow', days: ['Mo'] }, (r) => r.args.rel === 'tomorrow' && !('days' in r.args)],
  ['free_with_friends', {}, (r) => r.tool === 'free_with_friends' && JSON.stringify(r.args) === '{}'],
  ['best_professor', { course: 'bus 3431' }, (r) => r.tool === 'best_professor' && r.args.course === 'BUS3431'],
  ['best_professor', { course: 'biz' }, (r) => r.tool === 'cant_answer'],
  ['fits_plan', { course: 'bus 4401', plan: 'a' }, (r) => r.args.course === 'BUS4401' && r.args.plan === 'A'],
  ['fits_plan', { course: 'bus4401', plan: 'Mine' }, (r) => r.args.plan === 'mine'],
  ['fits_plan', { course: 'bus4401', plan: 'D' }, (r) => r.args.course === 'BUS4401' && !('plan' in r.args)],
  ['fits_plan', { course: 'bus4401', plan: 'Plan b' }, (r) => r.args.plan === 'B'],
  ['fits_plan', { plan: 'A' }, (r) => r.tool === 'cant_answer'],
  ['app_help', { topic: 'champ', junk: 1 }, (r) => r.tool === 'app_help' && JSON.stringify(r.args) === '{"topic":"champ"}'],
  ['app_help', { topic: 'delete_account' }, (r) => r.tool === 'app_help' && r.args.topic === 'delete_account'],
  ['app_help', { topic: 'refund' }, (r) => r.tool === 'cant_answer'],
  ['app_help', { topic: 'Champ' }, (r) => r.tool === 'cant_answer'],
  ['app_help', {}, (r) => r.tool === 'cant_answer'],
];
t('app: app_help offers exactly the 16 topics the phone answers',
  JSON.stringify(shared.APP_TOOLS.find((x: any) => x.name === 'app_help').parameters.properties.topic.enum) === JSON.stringify(shared.HELP_TOPICS) && shared.HELP_TOPICS.length === 16);
t('app: the phone prompt sends questions about TermChamp to app_help, never answered in words',
  /ABOUT TermChamp or Champ[^.]*is app_help with the closest topic, however it is worded; never answer it in words/.test(shared.APP_SYSTEM('Fall 2026')));
t('web: app_help is not on the website menu', !shared.TOOLS.some((x: any) => x.name === 'app_help'));
for (const [name, input, check] of appCases) {
  vendorReply = tool(name, input);
  const rr = await call({ q: 'x ' + name, client: 'app' });
  t(`validate ${name} ${JSON.stringify(input).slice(0, 44)}`, check(rr), rr);
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
const appBlock = src.slice(src.indexOf('const APP_NEW'), src.indexOf('export const APP_NEW_NAMES'));
const appNew = [...appBlock.matchAll(/\{\s*name: '([a-z_]+)'/g)].map((m) => m[1]);
const toolNames = [...toolsBlock.matchAll(/\{\s*name: '([a-z_]+)'/g)].map((m) => m[1]).concat(['explain'], appNew).sort();
t('the phone menu adds exactly five tools', appNew.join() === 'friends_free_now,free_with_friends,best_professor,fits_plan,app_help', appNew);
const sql = await Deno.readTextFile(new URL('../../sql/professify-assistant-v8.sql', import.meta.url));
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
