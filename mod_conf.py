# Import hook to load simple "key = value" config files. Note that value
# is always string in this simple implementation. See example_conf.py
# for the example of using this import hook.
import imphook


def hook(modname, filename):
    with open(filename) as f:
        # Create a module object which will be result of the import.
        mod = type(imphook)(modname)
        for l in f:
            k, v = [x.strip() for x in l.split("=", 1)]
            setattr(mod, k, v)
        return mod


imphook.add_import_hook(hook, (".conf",))
