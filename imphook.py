# imphook - Simple and clear import hooks for Python
#
# This module is part of Pycopy https://github.com/pfalcon/pycopy
# project.
#
# Copyright (c) 2020 Paul Sokolovsky
#
# The MIT License
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

import sys
try:
    sys.setimphook
    has_setimphook = True
except AttributeError:
    has_setimphook = False

__all__ = ("add_import_hook",)


if has_setimphook:

    import os.path

    _old_hook = ...
    _hooks = []

    def _hook_dispatch(modname, path):
        for hook, exts in _hooks:
            for ext in exts:
                f = path + ext
                if os.path.isfile(f):
                    mod = hook(modname, f)
                    if mod is not None:
                        return mod
        if _old_hook:
            return _old_hook(path)

    def add_import_hook(hook, exts):
        global _old_hook
        _hooks.insert(0, (hook, exts))
        old = sys.setimphook(_hook_dispatch, exts)
        if _old_hook is ...:
            _old_hook = old

else:

    from collections import defaultdict
    import warnings
    import importlib

    _imphook_exts = []
    _ext2hook = defaultdict(list)

    class ImphookFileLoader(importlib._bootstrap_external.FileLoader):

        def create_module(self, spec):
            #print("create_module", spec)
            ext = "." + spec.origin.rsplit(".", 1)[1]
            for h in _ext2hook[ext]:
                m = h(spec.name, spec.origin)
                if m:
                    return m

        def exec_module(self, mod):
            # Module is fully populated in create_module
            pass


    def add_import_hook(hook, exts):
        _imphook_exts.extend(exts)
        for ext in exts:
            _ext2hook[ext].insert(0, hook)

        for i, el in enumerate(sys.path_hooks):
            if not isinstance(el, type):
                # Assume it's a type wrapped in a closure,
                # as is the case for FileFinder.
                el = type(el("."))
            if el is importlib._bootstrap_external.FileFinder:
                sys.path_hooks.pop(i)
                insert_pos = i
                break
        else:
            warnings.warn("Could not find existing FileFinder to replace, installing ours as the first to use")
            insert_pos = 0

        # Mirrors what's done by importlib._bootstrap_external._install(importlib._bootstrap)
        loaders = [(ImphookFileLoader, _imphook_exts)] + importlib._bootstrap_external._get_supported_file_loaders()
        # path_hook closure captures supported_loaders in itself, all instances
        # of FileFinder class will be created with it.
        sys.path_hooks.insert(insert_pos, importlib._bootstrap_external.FileFinder.path_hook(*loaders))
        sys.path_importer_cache.clear()


if __name__ == "__main__":
    sys.argv.pop(0)

    while len(sys.argv) >= 2 and sys.argv[0] == "-i":
        sys.argv.pop(0)
        mod_name = sys.argv.pop(0)
        __import__(mod_name)

    if not sys.argv or sys.argv[0].startswith("-") and sys.argv[0] != "-m":
        print("""\
usage: python3 -m imphook (-i <module>)+ (<script.py>|-m <main_module>) <arg>*

Preloads import hook module(s) and executes a Python script/module as usual.
https://github.com/pfalcon/python-imphook
""")
        sys.exit(1)

    if sys.argv[0] == "-m":
        sys.argv.pop(0)
        main_mod = sys.argv[0]
        try:
            import importlib.util
            importlib.util.find_spec
        except:
            # We don't try to patch sys.argv[0], because native Pycopy's -m
            # sets just the module name there.
            # Magic __import__ for Pycopy which sets up __main__ name.
            __import__(main_mod, None, None, False)
        else:
            # All this stuff is to set nodule name as __main__ before its
            # top-level code gets executed. Otherwise, we could just use
            # __import__(sys.argv[0])
            spec = importlib.util.find_spec(main_mod, package=None)
            loader = spec.loader
            if not loader:
                print("imphook: No module named %s" % main_mod, file=sys.stderr)
                sys.exit(1)
            loader.name = "__main__"
            sys.argv[0] = loader.path
            mod = loader.create_module(spec)
            if not mod:
                mod = type(sys)("__main__")
            loader.exec_module(mod)
    else:
        try:
            with open(sys.argv[0]) as f:
                s = f.read()
        except Exception as e:
            print("imphook: can't open file: %s" % e, file=sys.stderr)
            sys.exit(2)
        exec(s)
