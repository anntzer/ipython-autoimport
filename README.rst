ipython-autoimport
==================

| |GitHub| |PyPI| |Build|

.. |GitHub|
   image:: https://img.shields.io/badge/github-anntzer%2Fdefopt-brightgreen
   :target: https://github.com/anntzer/ipython-autoimport
.. |PyPI|
   image:: https://img.shields.io/pypi/v/ipython-autoimport.svg?color=brightgreen
   :target: https://pypi.python.org/pypi/ipython-autoimport
.. |Build|
   image:: https://img.shields.io/github/actions/workflow/status/anntzer/ipython-autoimport/build.yml?branch=main
   :target: https://github.com/anntzer/ipython-autoimport/actions

Automagically import missing modules in IPython: instead of ::

   In [1]: plt.plot([1, 2], [3, 4])
   ---------------------------------------------------------------------------
   NameError                                 Traceback (most recent call last)
   <ipython-input-1-994ba2bf13c0> in <module>()
   ----> 1 plt.plot([1, 2], [3, 4])

   NameError: name 'plt' is not defined

   In [2]: from matplotlib import pyplot as plt

   In [3]: plt.plot([1, 2], [3, 4])
   Out[3]: [<matplotlib.lines.Line2D at 0x7f73f0179198>]

do what I mean::

   In [1]: plt.plot([1, 2], [3, 4])
   Autoimport: from matplotlib import pyplot as plt
   Out[1]: [<matplotlib.lines.Line2D at 0x7f7e253552b0>]

Inspired from @OrangeFlash81's `version
<https://github.com/OrangeFlash81/ipython-auto-import>`_, with many
improvements:

- Does not rely on re-execution, but instead hooks the user namespace; thus,
  safe even in the presence of side effects, and works for tab completion and
  magics too.
- Learns your preferred aliases from the history -- ``plt`` is not hardcoded to
  alias ``matplotlib.pyplot``, just found because you previously imported
  ``pyplot`` under this alias.
- Suppresses irrelevant chained tracebacks.
- Auto-imports submodules.
- ``pip``-installable.

To see auto imports from the current session: ``%autoimport -l``

To clear the cache for a symbol with multiple possible imports: ``%autoimport -c SYMBOL``

Installation
------------

As usual, install using pip:

.. code-block:: sh

   $ pip install ipython-autoimport  # from PyPI
   $ pip install git+https://github.com/anntzer/ipython-autoimport  # from Github

Then, append the output of ``python -m ipython_autoimport`` to the
``ipython_config.py`` file in the directory printed by ``ipython profile
locate`` (typically ``~/.ipython/profile_default/``).  If you don't have such a
file at all, first create it with ``ipython profile create``.

When using Spyder, the above registration method will not work; instead, add
``%load_ext ipython_autoimport`` to the
``Preferences → IPython console → Startup → Run code`` option.

Note that upon loading, ``ipython_autoimport`` will register its submodule
auto-importer to IPython's "limited evalutation" completer policy (on IPython
versions that support it).

Run tests with ``pytest``.

Limitations
-----------

Constructs such as ::

   class C:
      auto_imported_value

will not work, because they are run using the class locals (rather than the
patched locals); patching globals would not work because ``LOAD_NAME`` queries
globals using ``PyDict_GetItem`` exactly (note that it queries locals using
``PyObject_GetItem``; also, ``LOAD_GLOBALS`` queries *both* globals and
builtins using ``PyObject_GetItem`` so we could possibly get away with patching
the builtins dict instead, but that seems a bit too invasive...).

When using Jedi autocompletion (the default if Jedi is installed as of IPython
7.2), trying to tab-complete not-yet-imported global names to trigger an import
failure, because Jedi purposefully converts the global dict to a namespace
object and looks up attributes using ``getattr_static``.  Jedi can be disabled
by adding ``c.Completer.use_jedi = False`` to the ``ipython_config.py`` file.

Changelog
---------

v0.5.1 (2025-03-11)
~~~~~~~~~~~~~~~~~~~
- Fix compatibility with IPython 9's new theme system.

v0.5 (2024-08-20)
~~~~~~~~~~~~~~~~~
- Avoid erroring when exiting IPython≥8.15.
