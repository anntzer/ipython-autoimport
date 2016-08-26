ipython-autoimport
==================

Automagically import missing modules in IPython: instead of
```
In [1]: plt.plot([1, 2], [3, 4])
---------------------------------------------------------------------------
NameError                                 Traceback (most recent call last)
<ipython-input-1-994ba2bf13c0> in <module>()
----> 1 plt.plot([1, 2], [3, 4])

NameError: name 'plt' is not defined

In [2]: from matplotlib import pyplot as plt

In [3]: plt.plot([1, 2], [3, 4])
Out[3]: [<matplotlib.lines.Line2D at 0x7f73f0179198>]
```
do what I mean:
```
In [1]: plt.plot([1, 2], [3, 4])
Autoimport: from matplotlib import pyplot as plt
Out[1]: [<matplotlib.lines.Line2D at 0x7f7e253552b0>]
```

Heavily inspired from @OrangeFlash81's [version](http://github.com/OrangeFlash81/ipython-aut-import), with a few improvements:
- Learns your preferred aliases.
- Suppresses irrelevant chained tracebacks.
- Import submodules.
- `pip`-installable.

Installation
------------

```
$ pip install git+https://github.com/anntzer/ipython-autoimport
```
then append the output of `python -mipython_autoimport`
to the output of `ipython profile locate` (typically
`~/.ipython/profile_default/ipython_config.py`).
