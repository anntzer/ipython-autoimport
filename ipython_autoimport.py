"""Automagically import missing modules in IPython.

To activate, pip-install and append the output of `python -mipython_autoimport`
to `~/.ipython/profile_default/ipython_config.py`.
"""

import ast
import builtins
import functools
import importlib
import os
import sys
import token
from types import ModuleType

from IPython.utils import PyColorize

try:
    import _ipython_autoimport_version
except ImportError:
    from pip._vendor import pkg_resources
    __version__ = pkg_resources.get_distribution("ipython-autoimport").version
else:
    __version__ = _ipython_autoimport_version.get_versions()["version"]


@functools.lru_cache(1)
def _get_import_cache(ip):
    """Load a mapping of names to import statements from the IPython history.
    """

    import_cache = {}

    def _format_alias(alias):
        return ("import {0.name} as {0.asname}" if alias.asname
                else "import {0.name}").format(alias)

    class Visitor(ast.NodeVisitor):
        def visit_Import(self, node):
            for alias in node.names:
                (import_cache.setdefault(alias.asname or alias.name, set())
                 .add(_format_alias(alias)))

        def visit_ImportFrom(self, node):
            if node.level:  # Skip relative imports.
                return
            for alias in node.names:
                (import_cache.setdefault(alias.asname or alias.name, set())
                 .add("from {} {}".format(node.module, _format_alias(alias))))

    for _, _, entry in (
            ip.history_manager.get_tail(ip.history_load_length, raw=False)):
        try:
            parsed = ast.parse(entry)
        except SyntaxError:
            continue
        Visitor().visit(parsed)

    return import_cache


def _report(ip, msg):
    """Output a message prepended by a colored `Autoimport:` tag.
    """
    cs = PyColorize.Parser().color_table[ip.colors].colors
    # Token.NUMBER: (light) cyan, looks reasonable.
    print("{}Autoimport:{} {}".format(cs[token.NUMBER], cs["normal"], msg))


def _make_submodule_autoimporter_module(module):
    """Return a module sub-instance that automatically imports submodules.

    Implemented as a factory function to close over the real module.
    """

    if not hasattr(module, "__path__"):  # We only need to wrap packages.
        return module

    class SubmoduleAutoImporterModule(ModuleType):
        @property
        def __dict__(self):
            return module.__dict__

        # Overriding __setattr__ is needed even when __dict__ is overridden.
        def __setattr__(self, name, value):
            setattr(module, name, value)

        def __getattr__(self, name):
            try:
                value = getattr(module, name)
                if isinstance(value, ModuleType):
                    value = _make_submodule_autoimporter_module(value)
                return value
            except AttributeError:
                import_target = "{}.{}".format(self.__name__, name)
                try:
                    submodule = importlib.import_module(import_target)
                except Exception:
                    pass
                else:
                    _report(_ipython, "import {}".format(import_target))
                    return _make_submodule_autoimporter_module(submodule)
                raise  # Raise AttributeError without chaining ImportError.

    return SubmoduleAutoImporterModule(module.__name__)



class AutoImporterMap(dict):
    """Mapping that attempts to resolve missing keys through imports.
    """

    def __getitem__(self, name):
        try:
            value = super().__getitem__(name)
        except KeyError as key_error:
            # Find single matching import, if any.
            imports = _get_import_cache(_ipython).get(
                name, {"import {}".format(name)})
            if len(imports) != 1:
                if len(imports) > 1:
                    _report(_ipython,
                            "multiple imports available for {!r}".format(name))
                return
            import_source, = imports
            try:
                exec(import_source, self)  # exec recasts self as a dict.
            except Exception as import_error:
                raise key_error
            else:
                _report(_ipython, import_source)
                value = super().__getitem__(name)
        if isinstance(value, ModuleType):
            return _make_submodule_autoimporter_module(value)
        else:
            return value


def load_ipython_extension(ipython):
    # We would prefer patching `user_module` (the `__main__` module) as
    # IPython passes the `__dict__` of that module as globals -- this would be
    # necessary to support autoimport in comprehension scopes such as `[x for x
    # in <autoimported-module-attribute>]` (as the comprehension scope directly
    # tries resolves into the globals).
    #
    # Unfortunately this seems impossible(?) as `exec` requires its `globals`
    # argument (and only it) to be exactly a dict (and does not care about
    # overridden methods in subclasses).
    #
    # `Completer.namespace` needs to be overriden too, for completion to work
    # (both with and without Jedi).
    global _ipython
    _ipython = ipython
    _ipython.user_ns = _ipython.Completer.namespace = (
        AutoImporterMap(_ipython.user_ns))


if __name__ == "__main__":
    if os.isatty(sys.stdout.fileno()):
        print("""\
# Please append the output of this command to the
# output of `ipython profile locate` (typically
# `~/.ipython/profile_default/ipython_config.py`)
""")
    print("""\
c.InteractiveShellApp.exec_lines.append(
    "try:\\n    %load_ext ipython_autoimport\\nexcept ImportError: pass")""")
