import imphook


def hook(modname, filename):
    with open(filename) as f:
        source = f.read()
    source = source.replace("function", "lambda")
    mod = type(imphook)(modname)
    exec(source, vars(mod))
    return mod


imphook.add_import_hook(hook, (".py",))
