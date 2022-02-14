from pathlib import Path
import tokenize
from unittest import TestCase

import IPython.utils.io
import IPython.testing.globalipapp
import ipython_autoimport


class TestAutoimport(TestCase):
    @classmethod
    def setUpClass(cls):
        ip = IPython.testing.globalipapp.start_ipython()
        path = Path(__file__)
        ip.run_cell("import sys; sys.path[:0] = [{!r}, {!r}]".format(
            str(path.parents[1]), str(path.parents[0])))
        cls.ip = ip

    def setUp(self):
        self.ip.run_cell("%reset -f")
        self.ip.run_cell("%load_ext ipython_autoimport")

    def tearDown(self):
        with IPython.utils.io.capture_output():
            self.ip.run_cell(
                "for name, mod in list(sys.modules.items()):\n"
                "    if getattr(mod, '__file__', '').startswith({!r}):\n"
                "        del sys.modules[name]"
                .format(str(Path(__file__).parent)))
        self.ip.run_cell("%unload_ext ipython_autoimport")

    def test_autoimport(self):
        for name in ["a", "a.b", "a.b.c"]:
            with IPython.utils.io.capture_output() as captured:
                self.ip.run_cell("{}.__name__".format(name))
            parts = name.split(".")
            self.assertEqual(
                captured.stdout,
                "{}Out[1]: {!r}\n".format(
                    "".join("Autoimport: import {}\n".format(
                        ".".join(parts[:i + 1])) for i in range(len(parts))),
                    name))

    def test_sub_submodule(self):
        self.ip.run_cell("import a.b")
        with IPython.utils.io.capture_output() as captured:
            self.ip.run_cell("a.b.c.__name__")
        self.assertEqual(captured.stdout,
                         "Autoimport: import a.b.c\nOut[1]: 'a.b.c'\n")

    def test_no_import(self):
        with IPython.utils.io.capture_output() as captured:
            self.ip.run_cell("a.not_here")
        # Exact message changes between Python versions.
        self.assertIn("has no attribute 'not_here'",
                      captured.stdout.splitlines()[-1])
        self.assertNotIn("ImportError", captured.stdout)

    def test_setattr(self):
        with IPython.utils.io.capture_output() as captured:
            self.ip.run_cell("a; a.b = 42; 'b' in vars(a), a.b")
        self.assertEqual(captured.stdout,
                         "Autoimport: import a\nOut[1]: (True, 42)\n")

    def test_closure(self):
        with IPython.utils.io.capture_output() as captured:
            self.ip.run_cell("x = 1; (lambda: x)()")
        self.assertEqual(captured.stdout, "Out[1]: 1\n")

    def test_del(self):
        with IPython.utils.io.capture_output() as captured:
            self.ip.run_cell("x = 1; del x; print('ok')")
        self.assertEqual(captured.stdout, "ok\n")

    def test_list(self):
        self.ip.run_cell("os")
        with IPython.utils.io.capture_output() as captured:
            self.ip.run_cell("%autoimport -l")
        self.assertEqual(
            captured.stdout,
            "Autoimport: the following autoimports were run:\nimport os\n")

    def test_no_list(self):
        with IPython.utils.io.capture_output() as captured:
            self.ip.run_cell("%autoimport -l")
        self.assertEqual(captured.stdout,
                         "Autoimport: no autoimports in this session yet.\n")

    def test_noclear(self):
        with IPython.utils.io.capture_output() as captured:
            self.ip.run_cell("%autoimport -c ipython_autoimport_test_noclear")
        self.assertEqual(
            captured.stdout,
            "Autoimport: didn't find symbol "
            "'ipython_autoimport_test_noclear' in autoimport cache.\n")

    def test_magics(self):
        for magic in ["time", "timeit -n 1 -r 1", "prun"]:
            with IPython.utils.io.capture_output() as captured:
                self.ip.run_cell("{} x = 1".format(magic))
            self.assertNotIn("error", captured.stdout.lower())

    def test_no_autoimport_in_time(self):
        with IPython.utils.io.capture_output() as captured:
            self.ip.run_cell("%time type(get_ipython().user_ns)")
        self.assertNotIn("autoimport", captured.stdout.lower())

    def test_unload(self):
        with IPython.utils.io.capture_output() as captured:
            self.ip.run_cell("%unload_ext ipython_autoimport")
            self.ip.run_cell("try: a\nexcept NameError: print('ok')")
        self.assertEqual(captured.stdout, "ok\n")


class TestStyle:
    def _iter_stripped_lines(self):
        for path in [ipython_autoimport.__file__, __file__]:
            with tokenize.open(path) as src:
                for i, line in enumerate(src, 1):
                    yield "{}:{}".format(path, i), line.rstrip("\n")

    def test_line_length(self):
        for name, line in self._iter_stripped_lines():
            assert len(line) <= 79, f"{name} is too long"

    def test_trailing_whitespace(self):
        for name, line in self._iter_stripped_lines():
            assert not (line and line[-1].isspace()), \
                f"{name} has trailing whitespace"
