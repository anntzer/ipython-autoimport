import ast
from contextlib import ExitStack
import re
import token

from IPython.utils import PyColorize


def _maybe_modulename(source, name):

    class Visitor(ast.NodeVisitor):
        def visit_Attribute(self, node):
            nonlocal retval
            if isinstance(node.value, ast.Name) and node.value.id == name:
                retval = True
            return self.generic_visit(node)

    retval = False
    Visitor().visit(ast.parse(source))
    return retval


def _load_import_cache(ip):
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


_import_cache = None
_current_nameerror_stack = [...]  # Not None.

def _custom_exc(ip, etype, value, tb, tb_offset=None):
    global _import_cache

    with ExitStack() as stack:
        stack.callback(ip.showtraceback)
        # Is the innermost frame the IPython interactive environment?
        while tb.tb_next:
            tb = tb.tb_next
        if not re.match(r"\A<ipython-input-.*>\Z",
                        tb.tb_frame.f_code.co_filename):
            return
        # Are we just suppressing a context?
        @stack.callback
        def _suppress_context():
            if value.__context__ == _current_nameerror_stack[-1]:
                value.__suppress_context__ = True
        # Retrieve the missing name.
        tp_regexes = [
            (NameError, r"\Aname '(.+)' is not defined()\Z"),
            (AttributeError, r"\Amodule '(.+)' has no attribute '(.+)'\Z")]
        match = next(filter(None, (re.match(regex, str(value))
                                   if isinstance(value, tp) else None
                                   for tp, regex in tp_regexes)),
                     None)
        if not match:
            return
        name, attr = match.groups()
        (_, _, source), = ip.history_manager.get_tail(
            1, raw=False, include_latest=True)
        if not attr:  # NameError: was it used as a "module"?
            as_module = _maybe_modulename(source, name)
        else:  # AttributeError on a module.
            as_module = True
            name = "{}.{}".format(name, attr)
        # Find single matching import, if any.
        if _import_cache is None:
            _import_cache = _load_import_cache(ip)
        imports = (_import_cache.get(name, {"import {}".format(name)})
                   if as_module else
                   # If not a module, only keep "from ... import <name>".
                   {entry for entry in _import_cache.get(name, {})
                    if entry.startswith("from ")})
        if len(imports) != 1:
            return
        import_source, = imports
        cs = PyColorize.Parser().color_table[ip.colors].colors
        # Token.NUMBER: (light) cyan, looks reasonable.
        print("{}Autoimport: {}{}".format(
            cs[token.NUMBER], cs["normal"], import_source))
        try:
            _current_nameerror_stack.append(value)  # Prevent chaining.
            er = ip.run_cell(import_source)
            if er.error_in_exec:
                return
            # Anyways, success!
            stack.pop_all()
            ip.run_cell(source)
        finally:
            _current_nameerror_stack.pop()


def load_ipython_extension(ip):
    ip.set_custom_exc((Exception,), _custom_exc)


if __name__ == "__main__":
    print("""\
c.InteractiveShellApp.exec_lines.append(
    "try:\\n    %load_ext ipython_autoimport\\nexcept ImportError: pass")""")
