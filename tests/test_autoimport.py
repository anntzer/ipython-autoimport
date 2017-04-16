from pathlib import Path

import IPython.utils.io
import IPython.testing.globalipapp
import pytest


@pytest.fixture(scope="module")
def ip():
    ip = IPython.testing.globalipapp.start_ipython()
    path = Path(__file__)
    ip.run_cell("import sys; sys.path[:0] = [{!r}, {!r}]".format(
        str(path.parents[1]), str(path.parents[0])))
    ip.run_cell("%load_ext ipython_autoimport")
    return ip


@pytest.mark.parametrize("name", ["a", "a.b", "a.b.c"])
def test_autoimport(ip, name):
    with IPython.utils.io.capture_output() as captured:
        ip.run_cell("{}.__name__".format(name))
    assert (captured.stdout
            == "Autoimport: import {0}\nOut[1]: {0!r}\n".format(name))
