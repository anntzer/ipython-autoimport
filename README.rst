ipython-autoimport
==================

|Python33| |Travis| |CodeCov|

.. |Python33| image:: https://img.shields.io/badge/python-3.3%2B-blue.svg
.. |Travis| image:: https://travis-ci.org/anntzer/mplcursors.svg?branch=master
   :target: https://travis-ci.org/anntzer/mplcursors
.. |CodeCov| image:: https://codecov.io/gh/anntzer/mplcursors/master.svg
   :target: https://codecov.io/gh/anntzer/mplcursors

Automagically import missing modules in IPython: instead of
::

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
- Learns your preferred aliases (from the history).
- Suppresses irrelevant chained tracebacks.
- Auto-imports submodules.
- ``pip``-installable.

Installation
------------

Pick one among:

.. code-block:: sh

   $ pip install ipython-autoimport  # from PyPI
   $ pip install git+https://github.com/anntzer/ipython-autoimport  # from Github

then append the output of ``python -mipython_autoimport``
to the output of ``ipython profile locate`` (typically
``~/.ipython/profile_default/ipython_config.py``).

Run tests with ``pytest`` (tests requires ``pathlib`` on Python 3.3).

Limitations
-----------

- Comprehension scopes (e.g. ``[x for x in <autoimported-module-attribute>]``)
  do not support autoimporting.  The reason for this limitation is described in
  detail as a comment to ``load_ipython_extension``.  A fix would be welcome.
