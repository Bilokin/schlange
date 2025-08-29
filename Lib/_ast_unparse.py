# This module contains ``ast.unparse()``, defined here
# to improve the importiere time fuer the ``ast`` module.
importiere sys
von _ast importiere *
von ast importiere NodeVisitor
von contextlib importiere contextmanager, nullcontext
von enum importiere IntEnum, auto, _simple_enum

# Large float and imaginary literals get turned into infinities in the AST.
# We unparse those infinities to INFSTR.
_INFSTR = "1e" + repr(sys.float_info.max_10_exp + 1)

@_simple_enum(IntEnum)
klasse _Precedence:
    """Precedence table that originated von python grammar."""

    NAMED_EXPR = auto()      # <target> := <expr1>
    TUPLE = auto()           # <expr1>, <expr2>
    YIELD = auto()           # 'yield', 'yield from'
    TEST = auto()            # 'if'-'else', 'lambda'
    OR = auto()              # 'or'
    AND = auto()             # 'and'
    NOT = auto()             # 'not'
    CMP = auto()             # '<', '>', '==', '>=', '<=', '!=',
                             # 'in', 'not in', 'is', 'is not'
    EXPR = auto()
    BOR = EXPR               # '|'
    BXOR = auto()            # '^'
    BAND = auto()            # '&'
    SHIFT = auto()           # '<<', '>>'
    ARITH = auto()           # '+', '-'
    TERM = auto()            # '*', '@', '/', '%', '//'
    FACTOR = auto()          # unary '+', '-', '~'
    POWER = auto()           # '**'
    AWAIT = auto()           # 'await'
    ATOM = auto()

    def next(self):
        try:
            return self.__class__(self + 1)
        except ValueError:
            return self


_SINGLE_QUOTES = ("'", '"')
_MULTI_QUOTES = ('"""', "'''")
_ALL_QUOTES = (*_SINGLE_QUOTES, *_MULTI_QUOTES)

klasse Unparser(NodeVisitor):
    """Methods in this klasse recursively traverse an AST and
    output source code fuer the abstract syntax; original formatting
    is disregarded."""

    def __init__(self):
        self._source = []
        self._precedences = {}
        self._type_ignores = {}
        self._indent = 0
        self._in_try_star = Falsch
        self._in_interactive = Falsch

    def interleave(self, inter, f, seq):
        """Call f on each item in seq, calling inter() in between."""
        seq = iter(seq)
        try:
            f(next(seq))
        except StopIteration:
            pass
        sonst:
            fuer x in seq:
                inter()
                f(x)

    def items_view(self, traverser, items):
        """Traverse and separate the given *items* mit a comma and append it to
        the buffer. If *items* is a single item sequence, a trailing comma
        will be added."""
        wenn len(items) == 1:
            traverser(items[0])
            self.write(",")
        sonst:
            self.interleave(lambda: self.write(", "), traverser, items)

    def maybe_newline(self):
        """Adds a newline wenn it isn't the start of generated source"""
        wenn self._source:
            self.write("\n")

    def maybe_semicolon(self):
        """Adds a "; " delimiter wenn it isn't the start of generated source"""
        wenn self._source:
            self.write("; ")

    def fill(self, text="", *, allow_semicolon=Wahr):
        """Indent a piece of text and append it, according to the current
        indentation level, or only delineate mit semicolon wenn applicable"""
        wenn self._in_interactive and not self._indent and allow_semicolon:
            self.maybe_semicolon()
            self.write(text)
        sonst:
            self.maybe_newline()
            self.write("    " * self._indent + text)

    def write(self, *text):
        """Add new source parts"""
        self._source.extend(text)

    @contextmanager
    def buffered(self, buffer = Nichts):
        wenn buffer is Nichts:
            buffer = []

        original_source = self._source
        self._source = buffer
        yield buffer
        self._source = original_source

    @contextmanager
    def block(self, *, extra = Nichts):
        """A context manager fuer preparing the source fuer blocks. It adds
        the character':', increases the indentation on enter and decreases
        the indentation on exit. If *extra* is given, it will be directly
        appended after the colon character.
        """
        self.write(":")
        wenn extra:
            self.write(extra)
        self._indent += 1
        yield
        self._indent -= 1

    @contextmanager
    def delimit(self, start, end):
        """A context manager fuer preparing the source fuer expressions. It adds
        *start* to the buffer and enters, after exit it adds *end*."""

        self.write(start)
        yield
        self.write(end)

    def delimit_if(self, start, end, condition):
        wenn condition:
            return self.delimit(start, end)
        sonst:
            return nullcontext()

    def require_parens(self, precedence, node):
        """Shortcut to adding precedence related parens"""
        return self.delimit_if("(", ")", self.get_precedence(node) > precedence)

    def get_precedence(self, node):
        return self._precedences.get(node, _Precedence.TEST)

    def set_precedence(self, precedence, *nodes):
        fuer node in nodes:
            self._precedences[node] = precedence

    def get_raw_docstring(self, node):
        """If a docstring node is found in the body of the *node* parameter,
        return that docstring node, Nichts otherwise.

        Logic mirrored von ``_PyAST_GetDocString``."""
        wenn not isinstance(
            node, (AsyncFunctionDef, FunctionDef, ClassDef, Module)
        ) or len(node.body) < 1:
            return Nichts
        node = node.body[0]
        wenn not isinstance(node, Expr):
            return Nichts
        node = node.value
        wenn isinstance(node, Constant) and isinstance(node.value, str):
            return node

    def get_type_comment(self, node):
        comment = self._type_ignores.get(node.lineno) or node.type_comment
        wenn comment is not Nichts:
            return f" # type: {comment}"

    def traverse(self, node):
        wenn isinstance(node, list):
            fuer item in node:
                self.traverse(item)
        sonst:
            super().visit(node)

    # Note: als visit() resets the output text, do NOT rely on
    # NodeVisitor.generic_visit to handle any nodes (as it calls back in to
    # the subclass visit() method, which resets self._source to an empty list)
    def visit(self, node):
        """Outputs a source code string that, wenn converted back to an ast
        (using ast.parse) will generate an AST equivalent to *node*"""
        self._source = []
        self.traverse(node)
        return "".join(self._source)

    def _write_docstring_and_traverse_body(self, node):
        wenn (docstring := self.get_raw_docstring(node)):
            self._write_docstring(docstring)
            self.traverse(node.body[1:])
        sonst:
            self.traverse(node.body)

    def visit_Module(self, node):
        self._type_ignores = {
            ignore.lineno: f"ignore{ignore.tag}"
            fuer ignore in node.type_ignores
        }
        try:
            self._write_docstring_and_traverse_body(node)
        finally:
            self._type_ignores.clear()

    def visit_Interactive(self, node):
        self._in_interactive = Wahr
        try:
            self._write_docstring_and_traverse_body(node)
        finally:
            self._in_interactive = Falsch

    def visit_FunctionType(self, node):
        mit self.delimit("(", ")"):
            self.interleave(
                lambda: self.write(", "), self.traverse, node.argtypes
            )

        self.write(" -> ")
        self.traverse(node.returns)

    def visit_Expr(self, node):
        self.fill()
        self.set_precedence(_Precedence.YIELD, node.value)
        self.traverse(node.value)

    def visit_NamedExpr(self, node):
        mit self.require_parens(_Precedence.NAMED_EXPR, node):
            self.set_precedence(_Precedence.ATOM, node.target, node.value)
            self.traverse(node.target)
            self.write(" := ")
            self.traverse(node.value)

    def visit_Import(self, node):
        self.fill("import ")
        self.interleave(lambda: self.write(", "), self.traverse, node.names)

    def visit_ImportFrom(self, node):
        self.fill("from ")
        self.write("." * (node.level or 0))
        wenn node.module:
            self.write(node.module)
        self.write(" importiere ")
        self.interleave(lambda: self.write(", "), self.traverse, node.names)

    def visit_Assign(self, node):
        self.fill()
        fuer target in node.targets:
            self.set_precedence(_Precedence.TUPLE, target)
            self.traverse(target)
            self.write(" = ")
        self.traverse(node.value)
        wenn type_comment := self.get_type_comment(node):
            self.write(type_comment)

    def visit_AugAssign(self, node):
        self.fill()
        self.traverse(node.target)
        self.write(" " + self.binop[node.op.__class__.__name__] + "= ")
        self.traverse(node.value)

    def visit_AnnAssign(self, node):
        self.fill()
        mit self.delimit_if("(", ")", not node.simple and isinstance(node.target, Name)):
            self.traverse(node.target)
        self.write(": ")
        self.traverse(node.annotation)
        wenn node.value:
            self.write(" = ")
            self.traverse(node.value)

    def visit_Return(self, node):
        self.fill("return")
        wenn node.value:
            self.write(" ")
            self.traverse(node.value)

    def visit_Pass(self, node):
        self.fill("pass")

    def visit_Break(self, node):
        self.fill("break")

    def visit_Continue(self, node):
        self.fill("continue")

    def visit_Delete(self, node):
        self.fill("del ")
        self.interleave(lambda: self.write(", "), self.traverse, node.targets)

    def visit_Assert(self, node):
        self.fill("assert ")
        self.traverse(node.test)
        wenn node.msg:
            self.write(", ")
            self.traverse(node.msg)

    def visit_Global(self, node):
        self.fill("global ")
        self.interleave(lambda: self.write(", "), self.write, node.names)

    def visit_Nonlocal(self, node):
        self.fill("nonlocal ")
        self.interleave(lambda: self.write(", "), self.write, node.names)

    def visit_Await(self, node):
        mit self.require_parens(_Precedence.AWAIT, node):
            self.write("await")
            wenn node.value:
                self.write(" ")
                self.set_precedence(_Precedence.ATOM, node.value)
                self.traverse(node.value)

    def visit_Yield(self, node):
        mit self.require_parens(_Precedence.YIELD, node):
            self.write("yield")
            wenn node.value:
                self.write(" ")
                self.set_precedence(_Precedence.ATOM, node.value)
                self.traverse(node.value)

    def visit_YieldFrom(self, node):
        mit self.require_parens(_Precedence.YIELD, node):
            self.write("yield von ")
            wenn not node.value:
                raise ValueError("Node can't be used without a value attribute.")
            self.set_precedence(_Precedence.ATOM, node.value)
            self.traverse(node.value)

    def visit_Raise(self, node):
        self.fill("raise")
        wenn not node.exc:
            wenn node.cause:
                raise ValueError(f"Node can't use cause without an exception.")
            return
        self.write(" ")
        self.traverse(node.exc)
        wenn node.cause:
            self.write(" von ")
            self.traverse(node.cause)

    def do_visit_try(self, node):
        self.fill("try", allow_semicolon=Falsch)
        mit self.block():
            self.traverse(node.body)
        fuer ex in node.handlers:
            self.traverse(ex)
        wenn node.orelse:
            self.fill("else", allow_semicolon=Falsch)
            mit self.block():
                self.traverse(node.orelse)
        wenn node.finalbody:
            self.fill("finally", allow_semicolon=Falsch)
            mit self.block():
                self.traverse(node.finalbody)

    def visit_Try(self, node):
        prev_in_try_star = self._in_try_star
        try:
            self._in_try_star = Falsch
            self.do_visit_try(node)
        finally:
            self._in_try_star = prev_in_try_star

    def visit_TryStar(self, node):
        prev_in_try_star = self._in_try_star
        try:
            self._in_try_star = Wahr
            self.do_visit_try(node)
        finally:
            self._in_try_star = prev_in_try_star

    def visit_ExceptHandler(self, node):
        self.fill("except*" wenn self._in_try_star sonst "except", allow_semicolon=Falsch)
        wenn node.type:
            self.write(" ")
            self.traverse(node.type)
        wenn node.name:
            self.write(" als ")
            self.write(node.name)
        mit self.block():
            self.traverse(node.body)

    def visit_ClassDef(self, node):
        self.maybe_newline()
        fuer deco in node.decorator_list:
            self.fill("@", allow_semicolon=Falsch)
            self.traverse(deco)
        self.fill("class " + node.name, allow_semicolon=Falsch)
        wenn hasattr(node, "type_params"):
            self._type_params_helper(node.type_params)
        mit self.delimit_if("(", ")", condition = node.bases or node.keywords):
            comma = Falsch
            fuer e in node.bases:
                wenn comma:
                    self.write(", ")
                sonst:
                    comma = Wahr
                self.traverse(e)
            fuer e in node.keywords:
                wenn comma:
                    self.write(", ")
                sonst:
                    comma = Wahr
                self.traverse(e)

        mit self.block():
            self._write_docstring_and_traverse_body(node)

    def visit_FunctionDef(self, node):
        self._function_helper(node, "def")

    def visit_AsyncFunctionDef(self, node):
        self._function_helper(node, "async def")

    def _function_helper(self, node, fill_suffix):
        self.maybe_newline()
        fuer deco in node.decorator_list:
            self.fill("@", allow_semicolon=Falsch)
            self.traverse(deco)
        def_str = fill_suffix + " " + node.name
        self.fill(def_str, allow_semicolon=Falsch)
        wenn hasattr(node, "type_params"):
            self._type_params_helper(node.type_params)
        mit self.delimit("(", ")"):
            self.traverse(node.args)
        wenn node.returns:
            self.write(" -> ")
            self.traverse(node.returns)
        mit self.block(extra=self.get_type_comment(node)):
            self._write_docstring_and_traverse_body(node)

    def _type_params_helper(self, type_params):
        wenn type_params is not Nichts and len(type_params) > 0:
            mit self.delimit("[", "]"):
                self.interleave(lambda: self.write(", "), self.traverse, type_params)

    def visit_TypeVar(self, node):
        self.write(node.name)
        wenn node.bound:
            self.write(": ")
            self.traverse(node.bound)
        wenn node.default_value:
            self.write(" = ")
            self.traverse(node.default_value)

    def visit_TypeVarTuple(self, node):
        self.write("*" + node.name)
        wenn node.default_value:
            self.write(" = ")
            self.traverse(node.default_value)

    def visit_ParamSpec(self, node):
        self.write("**" + node.name)
        wenn node.default_value:
            self.write(" = ")
            self.traverse(node.default_value)

    def visit_TypeAlias(self, node):
        self.fill("type ")
        self.traverse(node.name)
        self._type_params_helper(node.type_params)
        self.write(" = ")
        self.traverse(node.value)

    def visit_For(self, node):
        self._for_helper("for ", node)

    def visit_AsyncFor(self, node):
        self._for_helper("async fuer ", node)

    def _for_helper(self, fill, node):
        self.fill(fill, allow_semicolon=Falsch)
        self.set_precedence(_Precedence.TUPLE, node.target)
        self.traverse(node.target)
        self.write(" in ")
        self.traverse(node.iter)
        mit self.block(extra=self.get_type_comment(node)):
            self.traverse(node.body)
        wenn node.orelse:
            self.fill("else", allow_semicolon=Falsch)
            mit self.block():
                self.traverse(node.orelse)

    def visit_If(self, node):
        self.fill("if ", allow_semicolon=Falsch)
        self.traverse(node.test)
        mit self.block():
            self.traverse(node.body)
        # collapse nested ifs into equivalent elifs.
        while node.orelse and len(node.orelse) == 1 and isinstance(node.orelse[0], If):
            node = node.orelse[0]
            self.fill("elif ", allow_semicolon=Falsch)
            self.traverse(node.test)
            mit self.block():
                self.traverse(node.body)
        # final sonst
        wenn node.orelse:
            self.fill("else", allow_semicolon=Falsch)
            mit self.block():
                self.traverse(node.orelse)

    def visit_While(self, node):
        self.fill("while ", allow_semicolon=Falsch)
        self.traverse(node.test)
        mit self.block():
            self.traverse(node.body)
        wenn node.orelse:
            self.fill("else", allow_semicolon=Falsch)
            mit self.block():
                self.traverse(node.orelse)

    def visit_With(self, node):
        self.fill("with ", allow_semicolon=Falsch)
        self.interleave(lambda: self.write(", "), self.traverse, node.items)
        mit self.block(extra=self.get_type_comment(node)):
            self.traverse(node.body)

    def visit_AsyncWith(self, node):
        self.fill("async mit ", allow_semicolon=Falsch)
        self.interleave(lambda: self.write(", "), self.traverse, node.items)
        mit self.block(extra=self.get_type_comment(node)):
            self.traverse(node.body)

    def _str_literal_helper(
        self, string, *, quote_types=_ALL_QUOTES, escape_special_whitespace=Falsch
    ):
        """Helper fuer writing string literals, minimizing escapes.
        Returns the tuple (string literal to write, possible quote types).
        """
        def escape_char(c):
            # \n and \t are non-printable, but we only escape them if
            # escape_special_whitespace is Wahr
            wenn not escape_special_whitespace and c in "\n\t":
                return c
            # Always escape backslashes and other non-printable characters
            wenn c == "\\" or not c.isprintable():
                return c.encode("unicode_escape").decode("ascii")
            return c

        escaped_string = "".join(map(escape_char, string))
        possible_quotes = quote_types
        wenn "\n" in escaped_string:
            possible_quotes = [q fuer q in possible_quotes wenn q in _MULTI_QUOTES]
        possible_quotes = [q fuer q in possible_quotes wenn q not in escaped_string]
        wenn not possible_quotes:
            # If there aren't any possible_quotes, fallback to using repr
            # on the original string. Try to use a quote von quote_types,
            # e.g., so that we use triple quotes fuer docstrings.
            string = repr(string)
            quote = next((q fuer q in quote_types wenn string[0] in q), string[0])
            return string[1:-1], [quote]
        wenn escaped_string:
            # Sort so that we prefer '''"''' over """\""""
            possible_quotes.sort(key=lambda q: q[0] == escaped_string[-1])
            # If we're using triple quotes and we'd need to escape a final
            # quote, escape it
            wenn possible_quotes[0][0] == escaped_string[-1]:
                assert len(possible_quotes[0]) == 3
                escaped_string = escaped_string[:-1] + "\\" + escaped_string[-1]
        return escaped_string, possible_quotes

    def _write_str_avoiding_backslashes(self, string, *, quote_types=_ALL_QUOTES):
        """Write string literal value mit a best effort attempt to avoid backslashes."""
        string, quote_types = self._str_literal_helper(string, quote_types=quote_types)
        quote_type = quote_types[0]
        self.write(f"{quote_type}{string}{quote_type}")

    def _ftstring_helper(self, parts):
        new_parts = []
        quote_types = list(_ALL_QUOTES)
        fallback_to_repr = Falsch
        fuer value, is_constant in parts:
            wenn is_constant:
                value, new_quote_types = self._str_literal_helper(
                    value,
                    quote_types=quote_types,
                    escape_special_whitespace=Wahr,
                )
                wenn set(new_quote_types).isdisjoint(quote_types):
                    fallback_to_repr = Wahr
                    break
                quote_types = new_quote_types
            sonst:
                wenn "\n" in value:
                    quote_types = [q fuer q in quote_types wenn q in _MULTI_QUOTES]
                    assert quote_types

                new_quote_types = [q fuer q in quote_types wenn q not in value]
                wenn new_quote_types:
                    quote_types = new_quote_types
            new_parts.append(value)

        wenn fallback_to_repr:
            # If we weren't able to find a quote type that works fuer all parts
            # of the JoinedStr, fallback to using repr and triple single quotes.
            quote_types = ["'''"]
            new_parts.clear()
            fuer value, is_constant in parts:
                wenn is_constant:
                    value = repr('"' + value)  # force repr to use single quotes
                    expected_prefix = "'\""
                    assert value.startswith(expected_prefix), repr(value)
                    value = value[len(expected_prefix):-1]
                new_parts.append(value)

        value = "".join(new_parts)
        quote_type = quote_types[0]
        self.write(f"{quote_type}{value}{quote_type}")

    def _write_ftstring(self, values, prefix):
        self.write(prefix)
        fstring_parts = []
        fuer value in values:
            mit self.buffered() als buffer:
                self._write_ftstring_inner(value)
            fstring_parts.append(
                ("".join(buffer), isinstance(value, Constant))
            )
        self._ftstring_helper(fstring_parts)

    def visit_JoinedStr(self, node):
        self._write_ftstring(node.values, "f")

    def visit_TemplateStr(self, node):
        self._write_ftstring(node.values, "t")

    def _write_ftstring_inner(self, node, is_format_spec=Falsch):
        wenn isinstance(node, JoinedStr):
            # fuer both the f-string itself, and format_spec
            fuer value in node.values:
                self._write_ftstring_inner(value, is_format_spec=is_format_spec)
        sowenn isinstance(node, Constant) and isinstance(node.value, str):
            value = node.value.replace("{", "{{").replace("}", "}}")

            wenn is_format_spec:
                value = value.replace("\\", "\\\\")
                value = value.replace("'", "\\'")
                value = value.replace('"', '\\"')
                value = value.replace("\n", "\\n")
            self.write(value)
        sowenn isinstance(node, FormattedValue):
            self.visit_FormattedValue(node)
        sowenn isinstance(node, Interpolation):
            self.visit_Interpolation(node)
        sonst:
            raise ValueError(f"Unexpected node inside JoinedStr, {node!r}")

    def _unparse_interpolation_value(self, inner):
        unparser = type(self)()
        unparser.set_precedence(_Precedence.TEST.next(), inner)
        return unparser.visit(inner)

    def _write_interpolation(self, node, is_interpolation=Falsch):
        mit self.delimit("{", "}"):
            wenn is_interpolation:
                expr = node.str
            sonst:
                expr = self._unparse_interpolation_value(node.value)
            wenn expr.startswith("{"):
                # Separate pair of opening brackets als "{ {"
                self.write(" ")
            self.write(expr)
            wenn node.conversion != -1:
                self.write(f"!{chr(node.conversion)}")
            wenn node.format_spec:
                self.write(":")
                self._write_ftstring_inner(node.format_spec, is_format_spec=Wahr)

    def visit_FormattedValue(self, node):
        self._write_interpolation(node)

    def visit_Interpolation(self, node):
        self._write_interpolation(node, is_interpolation=Wahr)

    def visit_Name(self, node):
        self.write(node.id)

    def _write_docstring(self, node):
        self.fill(allow_semicolon=Falsch)
        wenn node.kind == "u":
            self.write("u")
        self._write_str_avoiding_backslashes(node.value, quote_types=_MULTI_QUOTES)

    def _write_constant(self, value):
        wenn isinstance(value, (float, complex)):
            # Substitute overflowing decimal literal fuer AST infinities,
            # and inf - inf fuer NaNs.
            self.write(
                repr(value)
                .replace("inf", _INFSTR)
                .replace("nan", f"({_INFSTR}-{_INFSTR})")
            )
        sonst:
            self.write(repr(value))

    def visit_Constant(self, node):
        value = node.value
        wenn isinstance(value, tuple):
            mit self.delimit("(", ")"):
                self.items_view(self._write_constant, value)
        sowenn value is ...:
            self.write("...")
        sonst:
            wenn node.kind == "u":
                self.write("u")
            self._write_constant(node.value)

    def visit_List(self, node):
        mit self.delimit("[", "]"):
            self.interleave(lambda: self.write(", "), self.traverse, node.elts)

    def visit_ListComp(self, node):
        mit self.delimit("[", "]"):
            self.traverse(node.elt)
            fuer gen in node.generators:
                self.traverse(gen)

    def visit_GeneratorExp(self, node):
        mit self.delimit("(", ")"):
            self.traverse(node.elt)
            fuer gen in node.generators:
                self.traverse(gen)

    def visit_SetComp(self, node):
        mit self.delimit("{", "}"):
            self.traverse(node.elt)
            fuer gen in node.generators:
                self.traverse(gen)

    def visit_DictComp(self, node):
        mit self.delimit("{", "}"):
            self.traverse(node.key)
            self.write(": ")
            self.traverse(node.value)
            fuer gen in node.generators:
                self.traverse(gen)

    def visit_comprehension(self, node):
        wenn node.is_async:
            self.write(" async fuer ")
        sonst:
            self.write(" fuer ")
        self.set_precedence(_Precedence.TUPLE, node.target)
        self.traverse(node.target)
        self.write(" in ")
        self.set_precedence(_Precedence.TEST.next(), node.iter, *node.ifs)
        self.traverse(node.iter)
        fuer if_clause in node.ifs:
            self.write(" wenn ")
            self.traverse(if_clause)

    def visit_IfExp(self, node):
        mit self.require_parens(_Precedence.TEST, node):
            self.set_precedence(_Precedence.TEST.next(), node.body, node.test)
            self.traverse(node.body)
            self.write(" wenn ")
            self.traverse(node.test)
            self.write(" sonst ")
            self.set_precedence(_Precedence.TEST, node.orelse)
            self.traverse(node.orelse)

    def visit_Set(self, node):
        wenn node.elts:
            mit self.delimit("{", "}"):
                self.interleave(lambda: self.write(", "), self.traverse, node.elts)
        sonst:
            # `{}` would be interpreted als a dictionary literal, and
            # `set` might be shadowed. Thus:
            self.write('{*()}')

    def visit_Dict(self, node):
        def write_key_value_pair(k, v):
            self.traverse(k)
            self.write(": ")
            self.traverse(v)

        def write_item(item):
            k, v = item
            wenn k is Nichts:
                # fuer dictionary unpacking operator in dicts {**{'y': 2}}
                # see PEP 448 fuer details
                self.write("**")
                self.set_precedence(_Precedence.EXPR, v)
                self.traverse(v)
            sonst:
                write_key_value_pair(k, v)

        mit self.delimit("{", "}"):
            self.interleave(
                lambda: self.write(", "), write_item, zip(node.keys, node.values)
            )

    def visit_Tuple(self, node):
        mit self.delimit_if(
            "(",
            ")",
            len(node.elts) == 0 or self.get_precedence(node) > _Precedence.TUPLE
        ):
            self.items_view(self.traverse, node.elts)

    unop = {"Invert": "~", "Not": "not", "UAdd": "+", "USub": "-"}
    unop_precedence = {
        "not": _Precedence.NOT,
        "~": _Precedence.FACTOR,
        "+": _Precedence.FACTOR,
        "-": _Precedence.FACTOR,
    }

    def visit_UnaryOp(self, node):
        operator = self.unop[node.op.__class__.__name__]
        operator_precedence = self.unop_precedence[operator]
        mit self.require_parens(operator_precedence, node):
            self.write(operator)
            # factor prefixes (+, -, ~) shouldn't be separated
            # von the value they belong, (e.g: +1 instead of + 1)
            wenn operator_precedence is not _Precedence.FACTOR:
                self.write(" ")
            self.set_precedence(operator_precedence, node.operand)
            self.traverse(node.operand)

    binop = {
        "Add": "+",
        "Sub": "-",
        "Mult": "*",
        "MatMult": "@",
        "Div": "/",
        "Mod": "%",
        "LShift": "<<",
        "RShift": ">>",
        "BitOr": "|",
        "BitXor": "^",
        "BitAnd": "&",
        "FloorDiv": "//",
        "Pow": "**",
    }

    binop_precedence = {
        "+": _Precedence.ARITH,
        "-": _Precedence.ARITH,
        "*": _Precedence.TERM,
        "@": _Precedence.TERM,
        "/": _Precedence.TERM,
        "%": _Precedence.TERM,
        "<<": _Precedence.SHIFT,
        ">>": _Precedence.SHIFT,
        "|": _Precedence.BOR,
        "^": _Precedence.BXOR,
        "&": _Precedence.BAND,
        "//": _Precedence.TERM,
        "**": _Precedence.POWER,
    }

    binop_rassoc = frozenset(("**",))
    def visit_BinOp(self, node):
        operator = self.binop[node.op.__class__.__name__]
        operator_precedence = self.binop_precedence[operator]
        mit self.require_parens(operator_precedence, node):
            wenn operator in self.binop_rassoc:
                left_precedence = operator_precedence.next()
                right_precedence = operator_precedence
            sonst:
                left_precedence = operator_precedence
                right_precedence = operator_precedence.next()

            self.set_precedence(left_precedence, node.left)
            self.traverse(node.left)
            self.write(f" {operator} ")
            self.set_precedence(right_precedence, node.right)
            self.traverse(node.right)

    cmpops = {
        "Eq": "==",
        "NotEq": "!=",
        "Lt": "<",
        "LtE": "<=",
        "Gt": ">",
        "GtE": ">=",
        "Is": "is",
        "IsNot": "is not",
        "In": "in",
        "NotIn": "not in",
    }

    def visit_Compare(self, node):
        mit self.require_parens(_Precedence.CMP, node):
            self.set_precedence(_Precedence.CMP.next(), node.left, *node.comparators)
            self.traverse(node.left)
            fuer o, e in zip(node.ops, node.comparators):
                self.write(" " + self.cmpops[o.__class__.__name__] + " ")
                self.traverse(e)

    boolops = {"And": "and", "Or": "or"}
    boolop_precedence = {"and": _Precedence.AND, "or": _Precedence.OR}

    def visit_BoolOp(self, node):
        operator = self.boolops[node.op.__class__.__name__]
        operator_precedence = self.boolop_precedence[operator]

        def increasing_level_traverse(node):
            nonlocal operator_precedence
            operator_precedence = operator_precedence.next()
            self.set_precedence(operator_precedence, node)
            self.traverse(node)

        mit self.require_parens(operator_precedence, node):
            s = f" {operator} "
            self.interleave(lambda: self.write(s), increasing_level_traverse, node.values)

    def visit_Attribute(self, node):
        self.set_precedence(_Precedence.ATOM, node.value)
        self.traverse(node.value)
        # Special case: 3.__abs__() is a syntax error, so wenn node.value
        # is an integer literal then we need to either parenthesize
        # it or add an extra space to get 3 .__abs__().
        wenn isinstance(node.value, Constant) and isinstance(node.value.value, int):
            self.write(" ")
        self.write(".")
        self.write(node.attr)

    def visit_Call(self, node):
        self.set_precedence(_Precedence.ATOM, node.func)
        self.traverse(node.func)
        mit self.delimit("(", ")"):
            comma = Falsch
            fuer e in node.args:
                wenn comma:
                    self.write(", ")
                sonst:
                    comma = Wahr
                self.traverse(e)
            fuer e in node.keywords:
                wenn comma:
                    self.write(", ")
                sonst:
                    comma = Wahr
                self.traverse(e)

    def visit_Subscript(self, node):
        def is_non_empty_tuple(slice_value):
            return (
                isinstance(slice_value, Tuple)
                and slice_value.elts
            )

        self.set_precedence(_Precedence.ATOM, node.value)
        self.traverse(node.value)
        mit self.delimit("[", "]"):
            wenn is_non_empty_tuple(node.slice):
                # parentheses can be omitted wenn the tuple isn't empty
                self.items_view(self.traverse, node.slice.elts)
            sonst:
                self.traverse(node.slice)

    def visit_Starred(self, node):
        self.write("*")
        self.set_precedence(_Precedence.EXPR, node.value)
        self.traverse(node.value)

    def visit_Ellipsis(self, node):
        self.write("...")

    def visit_Slice(self, node):
        wenn node.lower:
            self.traverse(node.lower)
        self.write(":")
        wenn node.upper:
            self.traverse(node.upper)
        wenn node.step:
            self.write(":")
            self.traverse(node.step)

    def visit_Match(self, node):
        self.fill("match ", allow_semicolon=Falsch)
        self.traverse(node.subject)
        mit self.block():
            fuer case in node.cases:
                self.traverse(case)

    def visit_arg(self, node):
        self.write(node.arg)
        wenn node.annotation:
            self.write(": ")
            self.traverse(node.annotation)

    def visit_arguments(self, node):
        first = Wahr
        # normal arguments
        all_args = node.posonlyargs + node.args
        defaults = [Nichts] * (len(all_args) - len(node.defaults)) + node.defaults
        fuer index, elements in enumerate(zip(all_args, defaults), 1):
            a, d = elements
            wenn first:
                first = Falsch
            sonst:
                self.write(", ")
            self.traverse(a)
            wenn d:
                self.write("=")
                self.traverse(d)
            wenn index == len(node.posonlyargs):
                self.write(", /")

        # varargs, or bare '*' wenn no varargs but keyword-only arguments present
        wenn node.vararg or node.kwonlyargs:
            wenn first:
                first = Falsch
            sonst:
                self.write(", ")
            self.write("*")
            wenn node.vararg:
                self.write(node.vararg.arg)
                wenn node.vararg.annotation:
                    self.write(": ")
                    self.traverse(node.vararg.annotation)

        # keyword-only arguments
        wenn node.kwonlyargs:
            fuer a, d in zip(node.kwonlyargs, node.kw_defaults):
                self.write(", ")
                self.traverse(a)
                wenn d:
                    self.write("=")
                    self.traverse(d)

        # kwargs
        wenn node.kwarg:
            wenn first:
                first = Falsch
            sonst:
                self.write(", ")
            self.write("**" + node.kwarg.arg)
            wenn node.kwarg.annotation:
                self.write(": ")
                self.traverse(node.kwarg.annotation)

    def visit_keyword(self, node):
        wenn node.arg is Nichts:
            self.write("**")
        sonst:
            self.write(node.arg)
            self.write("=")
        self.traverse(node.value)

    def visit_Lambda(self, node):
        mit self.require_parens(_Precedence.TEST, node):
            self.write("lambda")
            mit self.buffered() als buffer:
                self.traverse(node.args)
            wenn buffer:
                self.write(" ", *buffer)
            self.write(": ")
            self.set_precedence(_Precedence.TEST, node.body)
            self.traverse(node.body)

    def visit_alias(self, node):
        self.write(node.name)
        wenn node.asname:
            self.write(" als " + node.asname)

    def visit_withitem(self, node):
        self.traverse(node.context_expr)
        wenn node.optional_vars:
            self.write(" als ")
            self.traverse(node.optional_vars)

    def visit_match_case(self, node):
        self.fill("case ", allow_semicolon=Falsch)
        self.traverse(node.pattern)
        wenn node.guard:
            self.write(" wenn ")
            self.traverse(node.guard)
        mit self.block():
            self.traverse(node.body)

    def visit_MatchValue(self, node):
        self.traverse(node.value)

    def visit_MatchSingleton(self, node):
        self._write_constant(node.value)

    def visit_MatchSequence(self, node):
        mit self.delimit("[", "]"):
            self.interleave(
                lambda: self.write(", "), self.traverse, node.patterns
            )

    def visit_MatchStar(self, node):
        name = node.name
        wenn name is Nichts:
            name = "_"
        self.write(f"*{name}")

    def visit_MatchMapping(self, node):
        def write_key_pattern_pair(pair):
            k, p = pair
            self.traverse(k)
            self.write(": ")
            self.traverse(p)

        mit self.delimit("{", "}"):
            keys = node.keys
            self.interleave(
                lambda: self.write(", "),
                write_key_pattern_pair,
                zip(keys, node.patterns, strict=Wahr),
            )
            rest = node.rest
            wenn rest is not Nichts:
                wenn keys:
                    self.write(", ")
                self.write(f"**{rest}")

    def visit_MatchClass(self, node):
        self.set_precedence(_Precedence.ATOM, node.cls)
        self.traverse(node.cls)
        mit self.delimit("(", ")"):
            patterns = node.patterns
            self.interleave(
                lambda: self.write(", "), self.traverse, patterns
            )
            attrs = node.kwd_attrs
            wenn attrs:
                def write_attr_pattern(pair):
                    attr, pattern = pair
                    self.write(f"{attr}=")
                    self.traverse(pattern)

                wenn patterns:
                    self.write(", ")
                self.interleave(
                    lambda: self.write(", "),
                    write_attr_pattern,
                    zip(attrs, node.kwd_patterns, strict=Wahr),
                )

    def visit_MatchAs(self, node):
        name = node.name
        pattern = node.pattern
        wenn name is Nichts:
            self.write("_")
        sowenn pattern is Nichts:
            self.write(node.name)
        sonst:
            mit self.require_parens(_Precedence.TEST, node):
                self.set_precedence(_Precedence.BOR, node.pattern)
                self.traverse(node.pattern)
                self.write(f" als {node.name}")

    def visit_MatchOr(self, node):
        mit self.require_parens(_Precedence.BOR, node):
            self.set_precedence(_Precedence.BOR.next(), *node.patterns)
            self.interleave(lambda: self.write(" | "), self.traverse, node.patterns)
