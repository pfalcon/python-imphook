imphook - Simple and clear import hooks for Python
==================================================

The ``imphook`` module allows to easily define per file type import
hooks, i.e. overload or extend import processing for particular file
types, without affecting processing of other file types, and at the
same time, while ensuring that new processing integrates as seamlessly
as possible with normal Python import rules.

Besides the Python-level API to install import hooks, the module also
provides command-line interface to run an existing Python script or
module with one or more import hooks preloaded (i.e. without modifying
existing script source code).

Some but not all things you can easily do using ``imphook`` (most
of these require additional modules to do the heavy lifting,
``imphook`` just allows to plug it seamlessly into the Python import
system):

* Override importing of (all or some) .py files, to support new
  syntax or semantics in them.
* Import files written using a DSL (domain-specific language)
  as if they were Python modules. E.g., config or data files.
* Import modules written in other language(s), assuming you have
  an interpreter(s) for them.
* Import binary files, e.g. Java or LLVM bytecode.

``imphook`` works both with new, lightweight legacy-free Python
API, as promoted by the `Pycopy <https://github.com/pfalcon/pycopy>`_
Python dialect (the original source of the "easy import hooks" idea),
and CPython (the older, reference Python implementation), and with
other Python implementations which are CPython-compatible.

Quick Start
-----------

Make sure that you already installed ``imphook`` using::

    pip3 install -U imphook

Below is a complete example of an import hook module to load
``key = value`` style config files::

    import imphook

    def hook(modname, filename):
        with open(filename) as f:
            # Create a module object which will be the result of import.
            mod = type(imphook)(modname)
            for l in f:
                k, v = [x.strip() for x in l.split("=", 1)]
                setattr(mod, k, v)
            return mod

    imphook.add_import_hook(hook, (".conf",))

Save this as the ``mod_conf.py`` file, and add the two following
files to test it:

``example_settings.conf``::

    var1 = 123
    var2 = hello

``example_conf.py``::

    import example_settings as settings

    print(settings.var1)
    print(settings.var2)

Now run::

    python3 -m imphook -i mod_conf example_conf.py

As you can see, the ``example_conf.py`` is able to import
``example_settings.conf`` as if it were a normal Python module.

Besides copy-pasting the above and other examples, you can also
clone the Git repository of ``imphook``, which contains various
ready-to-use examples::

    git clone https://github.com/pfalcon/python-imphook


API to install hooks
--------------------

The API of the module consists of one function:
`imphook.add_import_hook(hook, ext_tuple)`. *hook* is a name of
hook function. *ext_tuple* is a tuple of file extensions
the hook function should handle (the leading dot should be included).
More often than not, you will want to handle just one extension,
so don't forget to use the usual Python syntax with a trailing
comma for 1-element tuple, e.g.: ``(".ext",)``. Python modules may
not contain a dot (``"."``) in their names (they are used to separate
subpackages), so the extension you register may contain multiple
dots, e.g. ``".foo.bar"``, with filename ``my_module.foo.bar``
matching it.


Credits and licensing
---------------------

``imphook`` is (c) `Paul Sokolovsky <https://github.com/pfalcon>`_ and
is released under the MIT license.
