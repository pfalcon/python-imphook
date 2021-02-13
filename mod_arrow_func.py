# This imphook module implements "arrow functions", similar to JavaScript.
# (a, b) => a + b   --->   lambda a, b: a + b

import tokenize

import imphook


class TokBuf:
    def __init__(self):
        self.tokens = []

    def append(self, t):
        self.tokens.append(t)

    def clear(self):
        self.tokens.clear()

    def empty(self):
        return not self.tokens

    def spool(self):
        yield from self.tokens
        self.clear()


def xform(token_stream):
    tokbuf = TokBuf()
    for t in token_stream:
        if t[1] == "(":
            # We're interested only in the deepest parens.
            if not tokbuf.empty():
                yield from tokbuf.spool()
            tokbuf.append(t)
        elif t[1] == ")":
            nt1 = next(token_stream)
            nt2 = next(token_stream)
            if nt1[1] == "=" and nt2[1] == ">":
                yield (tokenize.NAME, "lambda")
                yield from tokbuf.tokens[1:]
                tokbuf.clear()
                yield (tokenize.OP, ":")
            else:
                yield from tokbuf.spool()
                yield t
                yield nt1
                yield nt2
        elif not tokbuf.empty():
            tokbuf.append(t)
        else:
            yield t


def hook(modname, filename):
    with open(filename, "r") as f:
        # Fairly speaking, tokenizing just to convert back to string form
        # isn't too efficient, but CPython doesn't offer us a way to parse
        # token stream so far, so we have no choice.
        source = tokenize.untokenize(xform(tokenize.generate_tokens(f.readline)))
    mod = type(imphook)(modname)
    exec(source, vars(mod))
    return mod


imphook.add_import_hook(hook, (".py",))
