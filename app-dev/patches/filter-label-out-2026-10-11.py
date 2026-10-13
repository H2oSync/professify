#!/usr/bin/env python3
r"""Explore: beside Filters, only the term (Tate, 2026-10-11, with a screenshot of "Filters 1 · BUS · Spring 2027":
"take out when a filter is on displaying it like bus or ge here only keep the term"). The Filters chip's count already
says a filter is on. Usage: python3 filter-label-out-2026-10-11.py <repo-dir>   (replayable)"""
import sys, os
PA = os.path.join(sys.argv[1], 'app', 'index.html'); S = open(PA, encoding='utf-8').read()
a = """function exTermCtl() {
  const subj = S.subj !== 'All' ? `<span class="muted b" style="font-size:13px">${esc(subjLabel(S.subj))}</span>` : '';
  if (!(S.exMode === 'classes' && splitTerms())) return subj || `<span class="muted b" style="font-size:13px">${esc(CFG.TERM_LABEL)}</span>`;"""
b = """function exTermCtl() {
  /* only the term — the subject filter shows as the count on Filters, never as words here (Tate, 2026-10-11) */
  const subj = '';
  if (!(S.exMode === 'classes' && splitTerms())) return `<span class="muted b" style="font-size:13px">${esc(CFG.TERM_LABEL)}</span>`;"""
if S.count(a) != 1: sys.exit(f'anchor matched {S.count(a)}x')
S = S.replace(a, b); open(PA, 'w', encoding='utf-8').write(S); print('filter-label-out: done')
