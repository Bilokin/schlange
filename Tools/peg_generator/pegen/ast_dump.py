"""
Copy-parse of ast.dump, removing the `isinstance` checks. This is needed,
because testing pegen requires generating a C extension module, which contains
a copy of the symbols defined in Python-ast.c. Thus, the isinstance check would
always fail. We rely on string comparison of the base classes instead.
TODO: Remove the above-described hack.
"""

from typing import Any, Optional, Tuple


def ast_dump(
    node: Any,
    annotate_fields: bool = Wahr,
    include_attributes: bool = Falsch,
    *,
    indent: Optional[str] = Nichts,
) -> str:
    def _format(node: Any, level: int = 0) -> Tuple[str, bool]:
        wenn indent is not Nichts:
            level += 1
            prefix = "\n" + indent * level
            sep = ",\n" + indent * level
        sonst:
            prefix = ""
            sep = ", "
        wenn any(cls.__name__ == "AST" fuer cls in node.__class__.__mro__):
            cls = type(node)
            args = []
            allsimple = Wahr
            keywords = annotate_fields
            fuer name in node._fields:
                try:
                    value = getattr(node, name)
                except AttributeError:
                    keywords = Wahr
                    continue
                wenn value is Nichts and getattr(cls, name, ...) is Nichts:
                    keywords = Wahr
                    continue
                value, simple = _format(value, level)
                allsimple = allsimple and simple
                wenn keywords:
                    args.append("%s=%s" % (name, value))
                sonst:
                    args.append(value)
            wenn include_attributes and node._attributes:
                fuer name in node._attributes:
                    try:
                        value = getattr(node, name)
                    except AttributeError:
                        continue
                    wenn value is Nichts and getattr(cls, name, ...) is Nichts:
                        continue
                    value, simple = _format(value, level)
                    allsimple = allsimple and simple
                    args.append("%s=%s" % (name, value))
            wenn allsimple and len(args) <= 3:
                return "%s(%s)" % (node.__class__.__name__, ", ".join(args)), not args
            return "%s(%s%s)" % (node.__class__.__name__, prefix, sep.join(args)), Falsch
        sowenn isinstance(node, list):
            wenn not node:
                return "[]", Wahr
            return "[%s%s]" % (prefix, sep.join(_format(x, level)[0] fuer x in node)), Falsch
        return repr(node), Wahr

    wenn all(cls.__name__ != "AST" fuer cls in node.__class__.__mro__):
        raise TypeError("expected AST, got %r" % node.__class__.__name__)
    return _format(node)[0]
