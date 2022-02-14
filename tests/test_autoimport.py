from pathlib import Path

import IPython.utils.io
import IPython.testing.globalipapp
import pytest


@pytest.fixture(scope="module")
def global_ip():
    ip = IPython.testing.globalipapp.start_ipython()
    path = Path(__file__)
    ip.run_cell("import sys; sys.path[:0] = [{!r}, {!r}]".format(
        str(path.parents[1]), str(path.parents[0])))
    return ip


@pytest.fixture
def ip(global_ip):
    global_ip.run_cell("%reset -f")
    global_ip.run_cell("%load_ext ipython_autoimport")
    yield global_ip
    with IPython.utils.io.capture_output():
        global_ip.run_cell(
            "for name, mod in list(sys.modules.items()):\n"
            "    if getattr(mod, '__file__', '').startswith({!r}):\n"
            "        del sys.modules[name]"
            .format(str(Path(__file__).parent)))
    global_ip.run_cell("%unload_ext ipython_autoimport")


@pytest.mark.parametrize("name", ["a", "a.b", "a.b.c"])
def test_autoimport(ip, name):
    with IPython.utils.io.capture_output() as captured:
        ip.run_cell("{}.__name__".format(name))
    parts = name.split(".")
    assert (captured.stdout
            == "{}Out[1]: {!r}\n".format(
                "".join("Autoimport: import {}\n".format(
                    ".".join(parts[:i + 1])) for i in range(len(parts))),
                name))


def test_sub_submodule(ip):
    ip.run_cell("import a.b")
    with IPython.utils.io.capture_output() as captured:
        ip.run_cell("a.b.c.__name__")
    assert captured.stdout == "Autoimport: import a.b.c\nOut[1]: 'a.b.c'\n"


def test_no_import(ip):
    with IPython.utils.io.capture_output() as captured:
        ip.run_cell("a.not_here")
    # Exact message changes between Python versions.
    assert "has no attribute 'not_here'" in captured.stdout.splitlines()[-1]
    assert "ImportError" not in captured.stdout


def test_setattr(ip):
    with IPython.utils.io.capture_output() as captured:
        ip.run_cell("a; a.b = 42; 'b' in vars(a), a.b")
    assert captured.stdout == "Autoimport: import a\nOut[1]: (True, 42)\n"


def test_closure(ip):
    with IPython.utils.io.capture_output() as captured:
        ip.run_cell("x = 1; (lambda: x)()")
    assert captured.stdout == "Out[1]: 1\n"


def test_del(ip):
    with IPython.utils.io.capture_output() as captured:
        ip.run_cell("x = 1; del x; print('ok')")
    assert captured.stdout == "ok\n"


def test_list(ip):
    ip.run_cell("os")
    with IPython.utils.io.capture_output() as captured:
        ip.run_cell("%autoimport -l")
    assert (captured.stdout ==
            "Autoimport: the following autoimports were run:\nimport os\n")


def test_no_list(ip):
    with IPython.utils.io.capture_output() as captured:
        ip.run_cell("%autoimport -l")
    assert (captured.stdout ==
            "Autoimport: no autoimports in this session yet.\n")


def test_noclear(ip):
    with IPython.utils.io.capture_output() as captured:
        ip.run_cell("%autoimport -c ipython_autoimport_test_noclear")
    assert (
        captured.stdout ==
        "Autoimport: didn't find symbol "
        "'ipython_autoimport_test_noclear' in autoimport cache.\n"
    )


@pytest.mark.parametrize("magic", ["time", "timeit -n 1 -r 1", "prun"])
def test_magics(ip, magic):
    with IPython.utils.io.capture_output() as captured:
        ip.run_cell("{} x = 1".format(magic))
    assert "error" not in captured.stdout.lower()


def test_no_autoimport_in_time(ip):
    with IPython.utils.io.capture_output() as captured:
        ip.run_cell("%time type(get_ipython().user_ns)")
    assert "autoimport" not in captured.stdout.lower()


def test_unload(ip):
    with IPython.utils.io.capture_output() as captured:
        ip.run_cell("%unload_ext ipython_autoimport")
        ip.run_cell("try: a\nexcept NameError: print('ok')")
    assert captured.stdout == "ok\n"
