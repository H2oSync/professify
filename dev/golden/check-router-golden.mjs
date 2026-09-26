/* The router's golden set: every phrasing here must route exactly as recorded. Add a line for every
   miss you fix (from "Not it?" / hawk_miss_fixed), so the fix can never quietly regress.
   Usage: node golden/check-router-golden.mjs            tool: null means "must go to the model". */
import fs from 'node:fs'; import { createRequire } from 'node:module';
const require = createRequire(import.meta.url);
const R = require('../../hawk-router.js');
const g = JSON.parse(fs.readFileSync(new URL('./router-golden.json', import.meta.url)));
let bad = 0;
for (const c of g.cases) {
  const r = R.route(c.q, g.catalog);
  const tool = r.prerouted ? r.tool : null, args = r.prerouted ? r.args : null;
  if (tool !== c.tool || JSON.stringify(args) !== JSON.stringify(c.args)) {
    bad++; console.log('FAIL', JSON.stringify(c.q), '\n  want', c.tool, JSON.stringify(c.args), '\n  got ', tool, JSON.stringify(args));
  }
}
console.log(`${g.cases.length - bad}/${g.cases.length} golden phrasings route as recorded`);
process.exit(bad ? 1 : 0);
