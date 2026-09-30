"""Lift a top-level declaration out of the desktop index.html VERBATIM, by matching its brackets
while skipping strings, template literals and comments. Used by build.py so the phone app runs on
the desktop's own data and rules instead of a hand copy that drifts."""


def _skip_string(s, i):
    q = s[i]; i += 1
    while i < len(s):
        c = s[i]
        if c == '\\': i += 2; continue
        if q == '`' and c == '$' and s.startswith('${', i):
            i = _match(s, i + 1) + 1; continue
        if c == q: return i + 1
        i += 1
    raise ValueError('unterminated string')


def _match(s, i):
    """s[i] is an opening bracket; return the index of its partner."""
    pairs = {'{': '}', '[': ']', '(': ')'}
    stack = [pairs[s[i]]]; i += 1
    while i < len(s):
        c = s[i]
        if c in '\'"`': i = _skip_string(s, i); continue
        if s.startswith('//', i): i = s.index('\n', i); continue
        if s.startswith('/*', i): i = s.index('*/', i) + 2; continue
        if c in pairs: stack.append(pairs[c])
        elif c in ')]}':
            if c != stack[-1]: raise ValueError('bracket mismatch at %d' % i)
            stack.pop()
            if not stack: return i
        i += 1
    raise ValueError('unbalanced')


def declaration(src, head):
    """head like 'const GE_COURSES=' — returns the full statement text up to and including ';'."""
    i = src.index(head)
    assert src.count(head) == 1, head
    j = i + len(head)
    while src[j] in ' \t\n': j += 1
    end = _match(src, j) + 1
    if src[end:end + 1] == ';': end += 1
    return src[i:end]


def function(src, head):
    """head like 'function concInfo(' — returns the whole function."""
    i = src.index(head)
    assert src.count(head) == 1, head
    j = src.index('{', i)
    return src[i:_match(src, j) + 1]
