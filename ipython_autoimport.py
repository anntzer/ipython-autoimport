"""Automagically import missing modules in IPython.

To activate, pip-install and append the output of `python -mipython_autoimport`
to `~/.ipython/profile_default/ipython_config.py`.
"""

import ast
import builtins
from collections import ChainMap
import copy
import functools
import importlib
import os
import sys
import token
from types import ModuleType

from IPython.utils import PyColorize


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


class SubmoduleAutoImport(ModuleType):
    """Wrapper module type that automatically imports submodules.
    """

    def __getattr__(self, name):
        try:
            return importlib.import_module("{}.{}".format(self.__name__, name))
        except Exception:
            raise AttributeError("module {!r} has no attribute {!r}"
                                 .format(self.__name__, name)) from None


class AutoImportMap(ChainMap):
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
            _report(_ipython, import_source)
            try:
                exec(import_source, self.maps[0])  # exec wants a dict.
            except Exception as import_error:
                raise key_error
            else:
                value = super().__getitem__(name)
        if isinstance(value, ModuleType):
            wrapper = SubmoduleAutoImport(value.__name__)
            vars(wrapper).update(vars(value))
            return wrapper
        else:
            return value


def load_ipython_extension(ipython):
    global _ipython
    _ipython = ipython
    _ipython.user_ns = AutoImportMap(_ipython.user_ns, vars(builtins))


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
