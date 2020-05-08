"""
Automagically import missing modules in IPython.

To activate, pip-install and append the output of `python -m ipython_autoimport`
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

from IPython.core import magic
from IPython.core.error import UsageError
from IPython.core.magic import register_line_magic
from IPython.core.magic_arguments import (argument, magic_arguments, 
                                          parse_argstring)
from IPython.core.magics.execution import ExecutionMagics
from IPython.utils import PyColorize

try:
    import importlib.metadata as importlib_metadata
except ImportError:
    try:
        import importlib_metadata
    except ImportError:
        importlib_metadata = None
try:
    __version__ = importlib_metadata.version("ipython-autoimport")
except (AttributeError, ImportError):  # AttrError if i_m is missing.
    __version__ = "(unknown version)"


def _get_import_cache(ipython):
    """
    Load a mapping of names to import statements from the IPython history.
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
            ipython.history_manager.get_tail(
                ipython.history_load_length, raw=True)):
        if entry.startswith("%autoimport"):
            try:
                args = parse_argstring(autoimport, entry[len("%autoimport"):])
                if args.clear:
                    import_cache.pop(args.clear, None)
            except UsageError:
                pass
        else:
            try:
                parsed = ast.parse(entry)
            except SyntaxError:
                continue
            Visitor().visit(parsed)

    return import_cache


def _report(ipython, msg):
    """Output a message prepended by a colored `Autoimport:` tag."""
    # Tell prompt_toolkit to pass ANSI escapes through (PTK#187); harmless on
    # pre-PTK versions.
    try:
        sys.stdout._raw = True
    except AttributeError:
        pass
    cs = PyColorize.Parser().color_table[ipython.colors].colors
    # Token.NUMBER: bright blue (cyan), looks reasonable.
    print("{}Autoimport:{} {}".format(cs[token.NUMBER], cs["normal"], msg))


def _make_submodule_autoimporter_module(ipython, module):
    """
    Return a module sub-instance that automatically imports submodules.

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
                    value = _make_submodule_autoimporter_module(ipython,
                                                                value)
                return value
            except AttributeError:
                import_target = "{}.{}".format(self.__name__, name)
                try:
                    submodule = importlib.import_module(import_target)
                except getattr(builtins, "ModuleNotFoundError",
                               ImportError):  # Py<3.6.
                    pass
                else:
                    _report(ipython, "import {}".format(import_target))
                    return _make_submodule_autoimporter_module(
                        ipython, submodule)
                raise  # Raise AttributeError without chaining ImportError.

    sai_module = SubmoduleAutoImporterModule(module.__name__)
    # Apparently, `module?` does not trigger descriptors, so we need to
    # set the docstring explicitly (on the instance, not on the class).
    # Then then only difference in the output of `module?` becomes the type
    # (`SubmoduleAutoImportModule` instead of `module`), which we should keep
    # for clarity.
    ModuleType.__setattr__(sai_module, "__doc__", module.__doc__)
    return sai_module


class _AutoImporterMap(dict):
    """Mapping that attempts to resolve missing keys through imports."""

    def __init__(self, ipython):
        super().__init__(ipython.user_ns)
        self._ipython = ipython
        self._import_cache = _get_import_cache(ipython)
        self._imported = []

    def __getitem__(self, name):
        try:
            value = super().__getitem__(name)
        except KeyError as key_error:
            # First try to resolve through builtins, so that local directories
            # (e.g., "bin") do not override them (by being misinterpreted as
            # a namespace package).  In this case, we do not need to check
            # whether we got a module.
            try:
                return getattr(builtins, name)
            except AttributeError:
                pass
            # Find single matching import, if any.
            imports = self._import_cache.get(name, {"import {}".format(name)})
            if len(imports) != 1:
                if len(imports) > 1:
                    _report(self._ipython,
                            "multiple imports available for {!r}:\n"
                            "{}\n"
                            "'%autoimport --clear {}' "
                            "can be used to clear the cache for this symbol."
                            .format(name, "\n".join(imports), name))
                raise key_error
            import_source, = imports
            try:
                exec(import_source, self)  # exec recasts self as a dict.
            except Exception:  # Normally, ImportError.
                raise key_error
            else:
                self._imported.append(import_source)
                _report(self._ipython, import_source)
                value = super().__getitem__(name)
        if isinstance(value, ModuleType):
            return _make_submodule_autoimporter_module(self._ipython, value)
        else:
            return value

    # Ensure that closures that attempt to resolve into globals get the right
    # values.

    def __setitem__(self, name, value):
        super().__setitem__(name, value)
        setattr(self._ipython.user_module, name, value)

    def __delitem__(self, name):
        super().__delitem__(name)
        delattr(self._ipython.user_module, name)


def _patch_magic(func):
    @functools.wraps(func)
    def magic(self, *args, **kwargs):
        _uninstall_namespace(self.shell)
        try:
            return func(self, *args, **kwargs)
        finally:
            _install_namespace(self.shell)

    return magic


@magic.magics_class
class _PatchedMagics(ExecutionMagics):
    time = magic.line_cell_magic(_patch_magic(ExecutionMagics.time))
    timeit = magic.line_cell_magic(_patch_magic(ExecutionMagics.timeit))
    prun = magic.line_cell_magic(_patch_magic(ExecutionMagics.prun))


@magic.magics_class
class _UnpatchedMagics(ExecutionMagics):
    time = magic.line_cell_magic(ExecutionMagics.time)
    timeit = magic.line_cell_magic(ExecutionMagics.timeit)
    prun = magic.line_cell_magic(ExecutionMagics.prun)


def _install_namespace(ipython):
    # `Completer.namespace` needs to be overriden too, for completion to work
    # (both with and without Jedi).
    ipython.user_ns = ipython.Completer.namespace = (
        _AutoImporterMap(ipython))


def _uninstall_namespace(ipython):
    ipython.user_ns = ipython.Completer.namespace = dict(ipython.user_ns)


@magic_arguments()
@argument("-c", "--clear", type=str, help="Clear cache for this symbol")
@argument("-l", "--list", dest="list", action="store_const",
          const=True, default=False,
          help="Show autoimports from this session")
def autoimport(arg):
    ipython = get_ipython()
    args = parse_argstring(autoimport, arg)

    if args.clear:
        if ipython.user_ns._import_cache.pop(args.clear, None):
            _report(ipython,
                    "cleared symbol '{}' from autoimport cache."
                    .format(args.clear))
        else:
            _report(ipython, 
                    "didn't find symbol '{}' in autoimport cache."
                    .format(args.clear))

    if args.list:
        if ipython.user_ns._imported:
            _report(ipython, 
                    "the following autoimports were run:\n{}".format(
                        "\n".join(ipython.user_ns._imported)
                    ))
        else:
            _report(ipython, "no autoimports in this session yet.")


def load_ipython_extension(ipython):
    _install_namespace(ipython)
    # Add warning to timing magics.
    ipython.register_magics(_PatchedMagics)

    register_line_magic(autoimport)


def unload_ipython_extension(ipython):
    _uninstall_namespace(ipython)
    # Unpatch timing magics.
    ipython.register_magics(_UnpatchedMagics)


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
