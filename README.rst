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


API to install hooks and hook structure
---------------------------------------

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

It is possible to call `imphook.add_import_hook(hook, ext_tuple)`
multiple times to install multiple hooks. The hooks are installed
in the stack-like fashion, the last installed will be called
first. It is possible to install multiple hooks for the same file
extension, and earlier installed hooks may still be called in this
case, because a hook function may skip processing a particular
file, and let other hooks to take a chance, with default processing
happening if no hook handled the import.

The signature and template of the actual hook function is::

    def my_hook(modname, filename):
        # Return None if you don't want to handle `filename`.
        # Otherwise, load `filename`, create a Python module object,
        # with name `modname`, populate it based on the loaded file
        # contents, and return it.

The *modname* parameter is a full module name of the module to
import, in the usual dot-separated notation, e.g. ``my_module``
or ``pkg.subp.mod``. For relative imports originated from within
a package, this name is already resolved to full absolute name.
The *modname* should be used to create a module object with the
given name.

The *filename* parameter is a full pathname (with extension) of the
file which hook should import. This filename is known to exist, so
you may proceed to open it directly. You may skip processing this
file by returning ``None`` from the hook, then other hooks may be
tried, and default processing happens otherwise (e.g. ``.py`` files
are loaded as usual, or ImportError raised for non-standard
extensions). For package imports, the value of *filename* ends with
``/__init__.py``, and that is the way to distinguish module vs
package imports.

If the hook proceeds with the file, it should load it by whatever
means suitable for the file type. File types which are not natively
supported by Python would require installing and using other extension
modules (beyond ``imphook``). After loading the file, the hook should
create an empty Python module object which will be the result of the
import. There are a few ways to do that:

* The baseline is to call a module type as a constructor. To get
  a module type, just apply the usual ``type()`` function to an
  existing (imported) module. You'll definitely have ``imphook``
  itself imported, which leads us to::

    mod = type(imphook)(modname)

  The parameter to constructor is the name of module to create,
  as passed to the hook.
* If the above looks too magic for you, you can import symbolic
  name for module type from the ``types`` module::

    from types import ModuleType
    mod = ModuleType(modname)

* Finally, you may use the ``imp`` module, which may be as well
  the clearest (to the newbie) way of doing it::

    import imp
    mod = imp.new_module(modname)

  But mind that the ``imp`` module is considered deprecated.

Of the choices above, the first is the most efficient - no need
to import additional modules, and it's just one line. And once
you saw and were explained what it does, it shouldn't be a problem
to remember and recognize it later.

Once the module object is created as discussed above, you should
populate it. A way to do that is by using ``setattr()`` builtin
to set a particular attribute of a module to a particular value.
Attributes usually represent variables with data values, but
may be also functions and classes.

Finally, you just return the populated module object.

In case you want to perform custom transformation on the Python
source, the process is usually somewhat different, where you
transform a representation of the source, and then execute it
in the context of a new module, which causes it to be populated.
An example of that is provided in the latter section.


Using import hooks in your applications
---------------------------------------

There are 2 ways to use import hook(s) in you Python programs:
either preloading them before starting your program using ``imphook``
command-line runner (next section) or load them explicitly at the
startup of your application. Crucial thing to remember that import
hooks apply: a) for imports only; b) for imports appearing after
the hook was installed.

The main file of our application is normally *not imported*, but
executed directly. This leads to the following pattern in structuring
your application source files:

* Have a "startup file", which is the one which user will actually
  run, so name it appropriately. In that file, you load import hooks
  and perform other baseline system-level initialization.
* The main functionality of your application is contained in seperate
  module(s). The startup script imports such a main module and
  executes it (e.g., by calling a function from it).

You already grasped how that works - as the "main" module is
*imported*, whatever hooks the "startup" script installed, will
apply to it.

This pattern is actually officially encoded in the structure of
Python *packages*. And any non-trivial Python application will
likely be a package with a few sub-modules in it, so you can as
well structure your applications this way (as a package), even
if they start simple (only one submodule initially). So, if you
try to "run" a package, what actually gets run is ``__main__``
submodule in that package. That's exactly the "startup" file
we discussed above. It installs the import hooks, and imports
a submodule with actual application's functionality.

The actual loading of hooks is very easy: just import them in
your startup script, voila! For ``mod_conf.py`` hook module
shown in the example above that would be::

    import mod_conf

You should do that as soon as reasonably possible in your startup
file. Normally, that would be after stdlib imports, and before
imports of your app's modules. Sometimes, you may want to put
hook imports very first, even before the stdlib modules. E.g.,
if hooks implement JIT compilation, which may benefit even stdlib
modules (someone yet has to develop such hooks!). All in all,
follow the guidelines above and documentation of the particular
hooks that you use.

Finally, the pattern described above (of having "startup" and
"main" modules in your app) doesn't work too well in case your
application is a single script file, you would need to turn that
into 2 files to make the import hooks work. But that's exactly
why ``imphook`` provides command-line preloader/runner interface!


Command-line interface
----------------------

Where you would normally run a single script like:

* ``python3 script.py``, or
* ``python3 -m script``

you can run the same script/module with some import hooks preloaded
using following commands (changes comparing to the above commands
are shown in italics):

* ``python3`` *-m imphook -i <mod_hook>* ``script.py``, or
* ``python3`` *-m imphook -i <mod_hook>* ``-m script``

That's exactly how we ran ``example_conf.py`` in the Quick Start
section. You can repeat ``-i`` option multiple times. Alternatively
and more compactly, you can pass to single ``-i`` option a
comma-separated list of hook modules to import, e.g.:
``-i mod_hook1,mod_hook2,mod_hook3``. If you pass multiple hooks,
the will be handled in the same stack-like fashion as the API
call described above. In the previous example, ``mod_hook3`` will
be called first to process imports, then ``mod_hook2``, then
``mod_hook1``. Of course, this will be important only if more
than one hook handles the same file extenstion.

This stack-like order on the command-line is used for consistency
with the API, to avoid confusion between the two. But it's also
the natural order, if you think about it: we start with standard
Python import hooks (yes, Python handles all imports using hooks,
although its hooks are as simple and clear as those we build here
with ``imphook``). Then, there may be some hooks installed in
``sitecustomize`` module (that's a way to install some "persistent"
hooks for all your projects, which we don't go into, as it should
be known for any advanced user). When we get to the ``imphook``
command line, we want to be able to override either standard
Python or ``sitecustomize`` hooks, and that's why all hooks are
consistently installed in the stack-like fashion. And you should
keep in mind that if an application explicitly installs any hooks,
they will have higher priority than those passed on the command
line.

We also should again emphasize the difference between ``script.py``
and ``-m script`` forms above. In the first case, the script is
*executed directly*, and any import hooks you specified with
``-i`` **do not** apply to the script itself (but will apply to
imports performed by ``script.py``). Even want hooks to apply
to the script's source itself, you **must** run it using
``-m script`` notation (which exactly tells "import this script
as a module, don't run it directly"). Pay double attention that
when you use ``-m`` switch, you **must not** use the ``.py``
extension (if you do, you ask to import the submodule ``py`` of
package ``script``, which rarely what you want or makes sense).

Last final note is about whitespace in the command-line parameters:
they should be used exactly as shown and described: there should
always be spaces between ``-i`` and ``-m`` options and their
parameters. And vice versa, if you use comma-separated list of
import hooks, there should be no spaces in that list.


Example of Python source transformation
---------------------------------------

We started this documentation with a quick example of writing an
import hook for a simple DSL. We'd like to finish it with examples
of another expected common use of ``imphook`` - implementing
new syntactic (and semantic!) features for Python.

A common starting example is just trying to "rename" one of existing
syntactic elements, e.g. use word "function" instead of "lambda".

So, we'd like to get following source code dialect to run:

``example_funkw.py``::

    my_fun = function: print("imphook's functionality is cool!")
    my_fun()

The simplest way to do that is just to replace every occurance of
"function" in the source with "lambda" (then compile, then execute
it in the module context). We thus will come up with the following
hook implementation:

``mod_funkw_naive.py``::

    import imphook

    def hook(filename):
        with open(filename) as f:
            source = f.read()
        source = source.replace("function", "lambda")
        mod = type(imphook)("")
        exec(source, vars(mod))
        return mod

    imphook.add_import_hook(hook, (".py",))

If you read previous sections carefully, you already know that if
we want the import hook to apply to the script itself, we must
run it as module, using ``-m`` switch::

    python3 -m imphook -i mod_funkw_naive -m example_funkw

And we get::

    imphook's lambdaality is cool!

Oops! The word "lambdaality" is definitely cool, but that's not what
we expected! It happens because the code just blindly replaces
occurrances everywhere, including within string literals. We could
try to work that around by using regular expression replace and match
whole words, that would help with the case above, but would still
replace lone "function" in the strings. Which makes us conclude:
transforming surface representation of a program (i.e. a sequence
of characters) is never an adequte method. We should operate on
a more suitable program representation, and the baseline such
representation is a sequence (or stream) of tokens. Let's use it:

mod_funkw.py::

    import tokenize
    import imphook

    def hook(filename):

        def xform(token_stream):
            for t in token_stream:
                if t[0] == tokenize.NAME and t[1] == "function":
                    yield (tokenize.NAME, "lambda") + t[2:]
                else:
                    yield t

        with open(filename, "rb") as f:
            # Fairly speaking, tokenizing just to convert back to string form
            # isn't too efficient, but CPython doesn't offer us a way to parse
            # token stream so far, so we have no choice.
            source = tokenize.untokenize(xform(tokenize.tokenize(f.readline)))
        mod = type(imphook)("")
        exec(source, vars(mod))
        return mod

    imphook.add_import_hook(hook, (".py",))


Credits and licensing
---------------------

``imphook`` is (c) `Paul Sokolovsky <https://github.com/pfalcon>`_ and
is released under the MIT license.
