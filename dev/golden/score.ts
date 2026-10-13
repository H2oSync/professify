/* How a golden case is scored — one copy, used by the model run (check-models-v3.ts, with the key)
   and by the offline check that runs on every build (check-golden.ts, no key). Same rules as
   check-models-v2.ts (2026-09-26):
     args are PARTIAL — every key listed must match; {"$in": [..]} lists acceptable values;
     {"$any": true} means present with any value; a friend matches on first name, a professor on
     either name containing the other; alt = other acceptable answers; forbid = keys that must NOT
     be set. compare/fit_pair's a and b may come in either order. */
const NAMEISH = new Set(['friend', 'name', 'person', 'a', 'b']);
const lc = (v: unknown) => String(v ?? '').toLowerCase().trim();

export function valOk(k: string, want: any, got: any): boolean {
  if (want && typeof want === 'object' && !Array.isArray(want)) {
    if (want.$any) return got !== undefined && got !== null && got !== '';
    if (want.$in) return want.$in.some((w: any) => valOk(k, w, got));
  }
  if (Array.isArray(want)) return Array.isArray(got) && want.length === got.length && want.every((w: any) => got.includes(w));
  if (NAMEISH.has(k)) {
    const w = lc(want), g = lc(got);
    if (!g) return false;
    return k === 'friend' ? g.split(/\s+/)[0] === w.split(/\s+/)[0] : (g === w || g.includes(w) || w.includes(g));
  }
  if (typeof want === 'number') return Number(got) === want;
  if (typeof want === 'string') return lc(want) === lc(got);
  return want === got;
}

/* null = wrong tool; [] = right; ['x', '!y'] = the args that are wrong, and the forbidden ones that are set. */
export function matches(exp: any, got: any, forbid: string[] = []): string[] | null {
  if (!got || got.tool !== exp.tool) return null;
  let g = { ...(got.args || {}) };
  const e = exp.args || {};
  if ('a' in e && 'b' in e && valOk('a', e.a, g.b) && valOk('b', e.b, g.a)) g = { ...g, a: g.b, b: g.a };
  const bad = Object.keys(e).filter((k) => !valOk(k, e[k], (g as any)[k]));
  forbid.forEach((k) => { if (k in g) bad.push('!' + k); });
  return bad;
}

export function expectations(c: any) { return [{ tool: c.tool, args: c.args || {} }, ...(c.alt || [])]; }

export function passes(c: any, picked: any): boolean {
  return expectations(c).some((e) => { const b = matches(e, picked, c.forbid); return b !== null && b.length === 0; });
}

/* An expectation turned into the call a model would make: $in → its first value, $any → a value of
   the right kind for that argument. */
const ANY_SAMPLE: Record<string, unknown> = { start_after: '12:00', end_before: '12:00', at_time: '12:00', min_rating: 4, units: 15, section: '1' };
export function concrete(args: any) {
  return Object.fromEntries(Object.entries(args || {}).map(([k, v]: any) =>
    [k, v && typeof v === 'object' && !Array.isArray(v) ? (v.$in ? v.$in[0] : (k in ANY_SAMPLE ? ANY_SAMPLE[k] : 'x')) : v]));
}

/* The menu's fingerprint: the phone's prompt and tools plus the whole text of shared.ts (routeSpec,
   validate, the request body). Change one character there and the scored baseline no longer describes
   what students get. The file's TEXT, not String(fn), so two Deno versions agree. */
export async function fingerprint(system: string, tools: unknown, sharedText = ''): Promise<string> {
  const buf = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(system + '\n' + JSON.stringify(tools) + '\n' + sharedText));
  return Array.from(new Uint8Array(buf)).map((x) => x.toString(16).padStart(2, '0')).join('').slice(0, 16);
}
