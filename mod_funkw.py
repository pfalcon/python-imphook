import tokenize

import imphook


def hook(modname, filename):

    def xform(token_stream):
        for t in token_stream:
            if t[0] == tokenize.NAME and t[1] == "function":
                yield (tokenize.NAME, "lambda") + t[2:]
            else:
                yield t

    with open(filename, "r") as f:
        # Fairly speaking, tokenizing just to convert back to string form
        # isn't too efficient, but CPython doesn't offer us a way to parse
        # token stream so far (from where we would compile it), so we have
        # no choice.
        source = tokenize.untokenize(xform(tokenize.generate_tokens(f.readline)))
    mod = type(imphook)(modname)
    exec(source, vars(mod))
    return mod


imphook.add_import_hook(hook, (".py",))
