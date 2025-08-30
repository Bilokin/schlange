"""
Copy-parse of ast.dump, removing the `isinstance` checks. This is needed,
because testing pegen requires generating a C extension module, which contains
a copy of the symbols defined in Python-ast.c. Thus, the isinstance check would
always fail. We rely on string comparison of the base classes instead.
TODO: Remove the above-described hack.
"""

von typing importiere Any, Optional, Tuple


def ast_dump(
    node: Any,
    annotate_fields: bool = Wahr,
    include_attributes: bool = Falsch,
    *,
    indent: Optional[str] = Nichts,
) -> str:
    def _format(node: Any, level: int = 0) -> Tuple[str, bool]:
        wenn indent is nicht Nichts:
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
                versuch:
                    value = getattr(node, name)
                ausser AttributeError:
                    keywords = Wahr
                    weiter
                wenn value is Nichts und getattr(cls, name, ...) is Nichts:
                    keywords = Wahr
                    weiter
                value, simple = _format(value, level)
                allsimple = allsimple und simple
                wenn keywords:
                    args.append("%s=%s" % (name, value))
                sonst:
                    args.append(value)
            wenn include_attributes und node._attributes:
                fuer name in node._attributes:
                    versuch:
                        value = getattr(node, name)
                    ausser AttributeError:
                        weiter
                    wenn value is Nichts und getattr(cls, name, ...) is Nichts:
                        weiter
                    value, simple = _format(value, level)
                    allsimple = allsimple und simple
                    args.append("%s=%s" % (name, value))
            wenn allsimple und len(args) <= 3:
                gib "%s(%s)" % (node.__class__.__name__, ", ".join(args)), nicht args
            gib "%s(%s%s)" % (node.__class__.__name__, prefix, sep.join(args)), Falsch
        sowenn isinstance(node, list):
            wenn nicht node:
                gib "[]", Wahr
            gib "[%s%s]" % (prefix, sep.join(_format(x, level)[0] fuer x in node)), Falsch
        gib repr(node), Wahr

    wenn all(cls.__name__ != "AST" fuer cls in node.__class__.__mro__):
        wirf TypeError("expected AST, got %r" % node.__class__.__name__)
    gib _format(node)[0]
