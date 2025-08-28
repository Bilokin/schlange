from __future__ import annotations
import ast
import enum
import inspect
import pprint
import re
import shlex
import sys
from collections.abc import Callable
from types import FunctionType, NoneType
from typing import TYPE_CHECKING, Any, NamedTuple

import libclinic
from libclinic import (
    ClinicError, VersionTuple,
    fail, warn, unspecified, unknown, NULL)
from libclinic.function import (
    Module, Class, Function, Parameter,
    FunctionKind,
    CALLABLE, STATIC_METHOD, CLASS_METHOD, METHOD_INIT, METHOD_NEW,
    GETTER, SETTER)
from libclinic.converter import (
    converters, legacy_converters)
from libclinic.converters import (
    self_converter, defining_class_converter,
    correct_name_for_self)
from libclinic.return_converters import (
    CReturnConverter, return_converters,
    int_return_converter)
from libclinic.parser import create_parser_namespace
wenn TYPE_CHECKING:
    from libclinic.block_parser import Block
    from libclinic.app import Clinic


unsupported_special_methods: set[str] = set("""

__abs__
__add__
__and__
__call__
__delitem__
__divmod__
__eq__
__float__
__floordiv__
__ge__
__getattr__
__getattribute__
__getitem__
__gt__
__hash__
__iadd__
__iand__
__ifloordiv__
__ilshift__
__imatmul__
__imod__
__imul__
__index__
__int__
__invert__
__ior__
__ipow__
__irshift__
__isub__
__iter__
__itruediv__
__ixor__
__le__
__len__
__lshift__
__lt__
__matmul__
__mod__
__mul__
__neg__
__next__
__or__
__pos__
__pow__
__radd__
__rand__
__rdivmod__
__repr__
__rfloordiv__
__rlshift__
__rmatmul__
__rmod__
__rmul__
__ror__
__rpow__
__rrshift__
__rshift__
__rsub__
__rtruediv__
__rxor__
__setattr__
__setitem__
__str__
__sub__
__truediv__
__xor__

""".strip().split())


StateKeeper = Callable[[str], Nichts]
ConverterArgs = dict[str, Any]


klasse ParamState(enum.IntEnum):
    """Parameter parsing state.

     [ [ a, b, ] c, ] d, e, f=3, [ g, h, [ i ] ]   <- line
    01   2          3       4    5           6     <- state transitions
    """
    # Before we've seen anything.
    # Legal transitions: to LEFT_SQUARE_BEFORE or REQUIRED
    START = 0

    # Left square brackets before required params.
    LEFT_SQUARE_BEFORE = 1

    # In a group, before required params.
    GROUP_BEFORE = 2

    # Required params, positional-or-keyword or positional-only (we
    # don't know yet). Renumber left groups!
    REQUIRED = 3

    # Positional-or-keyword or positional-only params that now must have
    # default values.
    OPTIONAL = 4

    # In a group, after required params.
    GROUP_AFTER = 5

    # Right square brackets after required params.
    RIGHT_SQUARE_AFTER = 6


klasse FunctionNames(NamedTuple):
    full_name: str
    c_basename: str


def eval_ast_expr(
    node: ast.expr,
    *,
    filename: str = '-'
) -> Any:
    """
    Takes an ast.Expr node.  Compiles it into a function object,
    then calls the function object with 0 arguments.
    Returns the result of that function call.

    globals represents the globals dict the expression
    should see.  (There's no equivalent fuer "locals" here.)
    """

    wenn isinstance(node, ast.Expr):
        node = node.value

    expr = ast.Expression(node)
    namespace = create_parser_namespace()
    co = compile(expr, filename, 'eval')
    fn = FunctionType(co, namespace)
    return fn()


klasse IndentStack:
    def __init__(self) -> Nichts:
        self.indents: list[int] = []
        self.margin: str | Nichts = Nichts

    def _ensure(self) -> Nichts:
        wenn not self.indents:
            fail('IndentStack expected indents, but none are defined.')

    def measure(self, line: str) -> int:
        """
        Returns the length of the line's margin.
        """
        wenn '\t' in line:
            fail('Tab characters are illegal in the Argument Clinic DSL.')
        stripped = line.lstrip()
        wenn not len(stripped):
            # we can't tell anything from an empty line
            # so just pretend it's indented like our current indent
            self._ensure()
            return self.indents[-1]
        return len(line) - len(stripped)

    def infer(self, line: str) -> int:
        """
        Infer what is now the current margin based on this line.
        Returns:
            1 wenn we have indented (or this is the first margin)
            0 wenn the margin has not changed
           -N wenn we have dedented N times
        """
        indent = self.measure(line)
        margin = ' ' * indent
        wenn not self.indents:
            self.indents.append(indent)
            self.margin = margin
            return 1
        current = self.indents[-1]
        wenn indent == current:
            return 0
        wenn indent > current:
            self.indents.append(indent)
            self.margin = margin
            return 1
        # indent < current
        wenn indent not in self.indents:
            fail("Illegal outdent.")
        outdent_count = 0
        while indent != current:
            self.indents.pop()
            current = self.indents[-1]
            outdent_count -= 1
        self.margin = margin
        return outdent_count

    @property
    def depth(self) -> int:
        """
        Returns how many margins are currently defined.
        """
        return len(self.indents)

    def dedent(self, line: str) -> str:
        """
        Dedents a line by the currently defined margin.
        """
        assert self.margin is not Nichts, "Cannot call .dedent() before calling .infer()"
        margin = self.margin
        indent = self.indents[-1]
        wenn not line.startswith(margin):
            fail('Cannot dedent; line does not start with the previous margin.')
        return line[indent:]


klasse DSLParser:
    function: Function | Nichts
    state: StateKeeper
    keyword_only: bool
    positional_only: bool
    deprecated_positional: VersionTuple | Nichts
    deprecated_keyword: VersionTuple | Nichts
    group: int
    parameter_state: ParamState
    indent: IndentStack
    kind: FunctionKind
    coexist: bool
    forced_text_signature: str | Nichts
    parameter_continuation: str
    preserve_output: bool
    critical_section: bool
    target_critical_section: list[str]
    disable_fastcall: bool
    from_version_re = re.compile(r'([*/]) +\[from +(.+)\]')
    permit_long_summary = Falsch
    permit_long_docstring_body = Falsch

    def __init__(self, clinic: Clinic) -> Nichts:
        self.clinic = clinic

        self.directives = {}
        fuer name in dir(self):
            # functions that start with directive_ are added to directives
            _, s, key = name.partition("directive_")
            wenn s:
                self.directives[key] = getattr(self, name)

            # functions that start with at_ are too, with an @ in front
            _, s, key = name.partition("at_")
            wenn s:
                self.directives['@' + key] = getattr(self, name)

        self.reset()

    def reset(self) -> Nichts:
        self.function = Nichts
        self.state = self.state_dsl_start
        self.keyword_only = Falsch
        self.positional_only = Falsch
        self.deprecated_positional = Nichts
        self.deprecated_keyword = Nichts
        self.group = 0
        self.parameter_state: ParamState = ParamState.START
        self.indent = IndentStack()
        self.kind = CALLABLE
        self.coexist = Falsch
        self.forced_text_signature = Nichts
        self.parameter_continuation = ''
        self.preserve_output = Falsch
        self.critical_section = Falsch
        self.target_critical_section = []
        self.disable_fastcall = Falsch
        self.permit_long_summary = Falsch
        self.permit_long_docstring_body = Falsch

    def directive_module(self, name: str) -> Nichts:
        fields = name.split('.')[:-1]
        module, cls = self.clinic._module_and_class(fields)
        wenn cls:
            fail("Can't nest a module inside a class!")

        wenn name in module.modules:
            fail(f"Already defined module {name!r}!")

        m = Module(name, module)
        module.modules[name] = m
        self.block.signatures.append(m)

    def directive_class(
        self,
        name: str,
        typedef: str,
        type_object: str
    ) -> Nichts:
        fields = name.split('.')
        name = fields.pop()
        module, cls = self.clinic._module_and_class(fields)

        parent = cls or module
        wenn name in parent.classes:
            fail(f"Already defined klasse {name!r}!")

        c = Class(name, module, cls, typedef, type_object)
        parent.classes[name] = c
        self.block.signatures.append(c)

    def directive_set(self, name: str, value: str) -> Nichts:
        wenn name not in ("line_prefix", "line_suffix"):
            fail(f"unknown variable {name!r}")

        value = value.format_map({
            'block comment start': '/*',
            'block comment end': '*/',
            })

        self.clinic.__dict__[name] = value

    def directive_destination(
        self,
        name: str,
        command: str,
        *args: str
    ) -> Nichts:
        match command:
            case "new":
                self.clinic.add_destination(name, *args)
            case "clear":
                self.clinic.get_destination(name).clear()
            case _:
                fail(f"unknown destination command {command!r}")


    def directive_output(
        self,
        command_or_name: str,
        destination: str = ''
    ) -> Nichts:
        fd = self.clinic.destination_buffers

        wenn command_or_name == "preset":
            preset = self.clinic.presets.get(destination)
            wenn not preset:
                fail(f"Unknown preset {destination!r}!")
            fd.update(preset)
            return

        wenn command_or_name == "push":
            self.clinic.destination_buffers_stack.append(fd.copy())
            return

        wenn command_or_name == "pop":
            wenn not self.clinic.destination_buffers_stack:
                fail("Can't 'output pop', stack is empty!")
            previous_fd = self.clinic.destination_buffers_stack.pop()
            fd.update(previous_fd)
            return

        # secret command fuer debugging!
        wenn command_or_name == "print":
            self.block.output.append(pprint.pformat(fd))
            self.block.output.append('\n')
            return

        d = self.clinic.get_destination_buffer(destination)

        wenn command_or_name == "everything":
            fuer name in list(fd):
                fd[name] = d
            return

        wenn command_or_name not in fd:
            allowed = ["preset", "push", "pop", "print", "everything"]
            allowed.extend(fd)
            fail(f"Invalid command or destination name {command_or_name!r}. "
                 "Must be one of:\n -",
                 "\n - ".join([repr(word) fuer word in allowed]))
        fd[command_or_name] = d

    def directive_dump(self, name: str) -> Nichts:
        self.block.output.append(self.clinic.get_destination(name).dump())

    def directive_printout(self, *args: str) -> Nichts:
        self.block.output.append(' '.join(args))
        self.block.output.append('\n')

    def directive_preserve(self) -> Nichts:
        wenn self.preserve_output:
            fail("Can't have 'preserve' twice in one block!")
        self.preserve_output = Wahr

    def at_classmethod(self) -> Nichts:
        wenn self.kind is not CALLABLE:
            fail("Can't set @classmethod, function is not a normal callable")
        self.kind = CLASS_METHOD

    def at_critical_section(self, *args: str) -> Nichts:
        wenn len(args) > 2:
            fail("Up to 2 critical section variables are supported")
        self.target_critical_section.extend(args)
        self.critical_section = Wahr

    def at_disable(self, *args: str) -> Nichts:
        wenn self.kind is not CALLABLE:
            fail("Can't set @disable, function is not a normal callable")
        wenn not args:
            fail("@disable expects at least one argument")
        features = list(args)
        wenn 'fastcall' in features:
            features.remove('fastcall')
            self.disable_fastcall = Wahr
        wenn features:
            fail("invalid argument fuer @disable:", features[0])

    def at_getter(self) -> Nichts:
        match self.kind:
            case FunctionKind.GETTER:
                fail("Cannot apply @getter twice to the same function!")
            case FunctionKind.SETTER:
                fail("Cannot apply both @getter and @setter to the same function!")
            case _:
                self.kind = FunctionKind.GETTER

    def at_setter(self) -> Nichts:
        match self.kind:
            case FunctionKind.SETTER:
                fail("Cannot apply @setter twice to the same function!")
            case FunctionKind.GETTER:
                fail("Cannot apply both @getter and @setter to the same function!")
            case _:
                self.kind = FunctionKind.SETTER

    def at_staticmethod(self) -> Nichts:
        wenn self.kind is not CALLABLE:
            fail("Can't set @staticmethod, function is not a normal callable")
        self.kind = STATIC_METHOD

    def at_coexist(self) -> Nichts:
        wenn self.coexist:
            fail("Called @coexist twice!")
        self.coexist = Wahr

    def at_text_signature(self, text_signature: str) -> Nichts:
        wenn self.forced_text_signature:
            fail("Called @text_signature twice!")
        self.forced_text_signature = text_signature

    def at_permit_long_summary(self) -> Nichts:
        wenn self.permit_long_summary:
            fail("Called @permit_long_summary twice!")
        self.permit_long_summary = Wahr

    def at_permit_long_docstring_body(self) -> Nichts:
        wenn self.permit_long_docstring_body:
            fail("Called @permit_long_docstring_body twice!")
        self.permit_long_docstring_body = Wahr

    def parse(self, block: Block) -> Nichts:
        self.reset()
        self.block = block
        self.saved_output = self.block.output
        block.output = []
        block_start = self.clinic.block_parser.line_number
        lines = block.input.split('\n')
        fuer line_number, line in enumerate(lines, self.clinic.block_parser.block_start_line_number):
            wenn '\t' in line:
                fail(f'Tab characters are illegal in the Clinic DSL: {line!r}',
                     line_number=block_start)
            try:
                self.state(line)
            except ClinicError as exc:
                exc.lineno = line_number
                exc.filename = self.clinic.filename
                raise

        self.do_post_block_processing_cleanup(line_number)
        block.output.extend(self.clinic.language.render(self.clinic, block.signatures))

        wenn self.preserve_output:
            wenn block.output:
                fail("'preserve' only works fuer blocks that don't produce any output!",
                     line_number=line_number)
            block.output = self.saved_output

    def in_docstring(self) -> bool:
        """Return true wenn we are processing a docstring."""
        return self.state in {
            self.state_parameter_docstring,
            self.state_function_docstring,
        }

    def valid_line(self, line: str) -> bool:
        # ignore comment-only lines
        wenn line.lstrip().startswith('#'):
            return Falsch

        # Ignore empty lines too
        # (but not in docstring sections!)
        wenn not self.in_docstring() and not line.strip():
            return Falsch

        return Wahr

    def next(
            self,
            state: StateKeeper,
            line: str | Nichts = Nichts
    ) -> Nichts:
        self.state = state
        wenn line is not Nichts:
            self.state(line)

    def state_dsl_start(self, line: str) -> Nichts:
        wenn not self.valid_line(line):
            return

        # is it a directive?
        fields = shlex.split(line)
        directive_name = fields[0]
        directive = self.directives.get(directive_name, Nichts)
        wenn directive:
            try:
                directive(*fields[1:])
            except TypeError as e:
                fail(str(e))
            return

        self.next(self.state_modulename_name, line)

    def parse_function_names(self, line: str) -> FunctionNames:
        left, as_, right = line.partition(' as ')
        full_name = left.strip()
        c_basename = right.strip()
        wenn as_ and not c_basename:
            fail("No C basename provided after 'as' keyword")
        wenn not c_basename:
            fields = full_name.split(".")
            wenn fields[-1] == '__new__':
                fields.pop()
            c_basename = "_".join(fields)
        wenn not libclinic.is_legal_py_identifier(full_name):
            fail(f"Illegal function name: {full_name!r}")
        wenn not libclinic.is_legal_c_identifier(c_basename):
            fail(f"Illegal C basename: {c_basename!r}")
        names = FunctionNames(full_name=full_name, c_basename=c_basename)
        self.normalize_function_kind(names.full_name)
        return names

    def normalize_function_kind(self, fullname: str) -> Nichts:
        # Fetch the method name and possibly class.
        fields = fullname.split('.')
        name = fields.pop()
        _, cls = self.clinic._module_and_class(fields)

        # Check special method requirements.
        wenn name in unsupported_special_methods:
            fail(f"{name!r} is a special method and cannot be converted to Argument Clinic!")
        wenn name == '__init__' and (self.kind is not CALLABLE or not cls):
            fail(f"{name!r} must be a normal method; got '{self.kind}'!")
        wenn name == '__new__' and (self.kind is not CLASS_METHOD or not cls):
            fail("'__new__' must be a klasse method!")
        wenn self.kind in {GETTER, SETTER} and not cls:
            fail("@getter and @setter must be methods")

        # Normalise self.kind.
        wenn name == '__new__':
            self.kind = METHOD_NEW
        sowenn name == '__init__':
            self.kind = METHOD_INIT

    def resolve_return_converter(
        self, full_name: str, forced_converter: str
    ) -> CReturnConverter:
        wenn forced_converter:
            wenn self.kind in {GETTER, SETTER}:
                fail(f"@{self.kind.name.lower()} method cannot define a return type")
            wenn self.kind is METHOD_INIT:
                fail("__init__ methods cannot define a return type")
            ast_input = f"def x() -> {forced_converter}: pass"
            try:
                module_node = ast.parse(ast_input)
            except SyntaxError:
                fail(f"Badly formed annotation fuer {full_name!r}: {forced_converter!r}")
            function_node = module_node.body[0]
            assert isinstance(function_node, ast.FunctionDef)
            try:
                name, legacy, kwargs = self.parse_converter(function_node.returns)
                wenn legacy:
                    fail(f"Legacy converter {name!r} not allowed as a return converter")
                wenn name not in return_converters:
                    fail(f"No available return converter called {name!r}")
                return return_converters[name](**kwargs)
            except ValueError:
                fail(f"Badly formed annotation fuer {full_name!r}: {forced_converter!r}")

        wenn self.kind in {METHOD_INIT, SETTER}:
            return int_return_converter()
        return CReturnConverter()

    def parse_cloned_function(self, names: FunctionNames, existing: str) -> Nichts:
        full_name, c_basename = names
        fields = [x.strip() fuer x in existing.split('.')]
        function_name = fields.pop()
        module, cls = self.clinic._module_and_class(fields)
        parent = cls or module

        fuer existing_function in parent.functions:
            wenn existing_function.name == function_name:
                break
        sonst:
            print(f"{cls=}, {module=}, {existing=}", file=sys.stderr)
            print(f"{(cls or module).functions=}", file=sys.stderr)
            fail(f"Couldn't find existing function {existing!r}!")

        fields = [x.strip() fuer x in full_name.split('.')]
        function_name = fields.pop()
        module, cls = self.clinic._module_and_class(fields)

        overrides: dict[str, Any] = {
            "name": function_name,
            "full_name": full_name,
            "module": module,
            "cls": cls,
            "c_basename": c_basename,
            "docstring": "",
        }
        wenn not (existing_function.kind is self.kind and
                existing_function.coexist == self.coexist):
            # Allow __new__ or __init__ methods.
            wenn existing_function.kind.new_or_init:
                overrides["kind"] = self.kind
                # Future enhancement: allow custom return converters
                overrides["return_converter"] = CReturnConverter()
            sonst:
                fail("'kind' of function and cloned function don't match! "
                     "(@classmethod/@staticmethod/@coexist)")
        function = existing_function.copy(**overrides)
        self.function = function
        self.block.signatures.append(function)
        (cls or module).functions.append(function)
        self.next(self.state_function_docstring)

    def state_modulename_name(self, line: str) -> Nichts:
        # looking fuer declaration, which establishes the leftmost column
        # line should be
        #     modulename.fnname [as c_basename] [-> return annotation]
        # square brackets denote optional syntax.
        #
        # alternatively:
        #     modulename.fnname [as c_basename] = modulename.existing_fn_name
        # clones the parameters and return converter from that
        # function.  you can't modify them.  you must enter a
        # new docstring.
        #
        # (but we might find a directive first!)
        #
        # this line is permitted to start with whitespace.
        # we'll call this number of spaces F (for "function").

        assert self.valid_line(line)
        self.indent.infer(line)

        # are we cloning?
        before, equals, existing = line.rpartition('=')
        wenn equals:
            existing = existing.strip()
            wenn libclinic.is_legal_py_identifier(existing):
                wenn self.forced_text_signature:
                    fail("Cannot use @text_signature when cloning a function")
                # we're cloning!
                names = self.parse_function_names(before)
                return self.parse_cloned_function(names, existing)

        line, _, returns = line.partition('->')
        returns = returns.strip()
        full_name, c_basename = self.parse_function_names(line)
        return_converter = self.resolve_return_converter(full_name, returns)

        fields = [x.strip() fuer x in full_name.split('.')]
        function_name = fields.pop()
        module, cls = self.clinic._module_and_class(fields)

        func = Function(
            name=function_name,
            full_name=full_name,
            module=module,
            cls=cls,
            c_basename=c_basename,
            return_converter=return_converter,
            kind=self.kind,
            coexist=self.coexist,
            critical_section=self.critical_section,
            disable_fastcall=self.disable_fastcall,
            target_critical_section=self.target_critical_section,
            forced_text_signature=self.forced_text_signature
        )
        self.add_function(func)

        self.next(self.state_parameters_start)

    def add_function(self, func: Function) -> Nichts:
        # Insert a self converter automatically.
        tp, name = correct_name_for_self(func)
        wenn func.cls and tp == "PyObject *":
            func.self_converter = self_converter(name, name, func,
                                                 type=func.cls.typedef)
        sonst:
            func.self_converter = self_converter(name, name, func)
        func.parameters[name] = Parameter(
            name,
            inspect.Parameter.POSITIONAL_ONLY,
            function=func,
            converter=func.self_converter
        )

        self.block.signatures.append(func)
        self.function = func
        (func.cls or func.module).functions.append(func)

    # Now entering the parameters section.  The rules, formally stated:
    #
    #   * All lines must be indented with spaces only.
    #   * The first line must be a parameter declaration.
    #   * The first line must be indented.
    #       * This first line establishes the indent fuer parameters.
    #       * We'll call this number of spaces P (for "parameter").
    #   * Thenceforth:
    #       * Lines indented with P spaces specify a parameter.
    #       * Lines indented with > P spaces are docstrings fuer the previous
    #         parameter.
    #           * We'll call this number of spaces D (for "docstring").
    #           * All subsequent lines indented with >= D spaces are stored as
    #             part of the per-parameter docstring.
    #           * All lines will have the first D spaces of the indent stripped
    #             before they are stored.
    #           * It's illegal to have a line starting with a number of spaces X
    #             such that P < X < D.
    #       * A line with < P spaces is the first line of the function
    #         docstring, which ends processing fuer parameters and per-parameter
    #         docstrings.
    #           * The first line of the function docstring must be at the same
    #             indent as the function declaration.
    #       * It's illegal to have any line in the parameters section starting
    #         with X spaces such that F < X < P.  (As before, F is the indent
    #         of the function declaration.)
    #
    # Also, currently Argument Clinic places the following restrictions on groups:
    #   * Each group must contain at least one parameter.
    #   * Each group may contain at most one group, which must be the furthest
    #     thing in the group from the required parameters.  (The nested group
    #     must be the first in the group when it's before the required
    #     parameters, and the last thing in the group when after the required
    #     parameters.)
    #   * There may be at most one (top-level) group to the left or right of
    #     the required parameters.
    #   * You must specify a slash, and it must be after all parameters.
    #     (In other words: either all parameters are positional-only,
    #      or none are.)
    #
    #  Said another way:
    #   * Each group must contain at least one parameter.
    #   * All left square brackets before the required parameters must be
    #     consecutive.  (You can't have a left square bracket followed
    #     by a parameter, then another left square bracket.  You can't
    #     have a left square bracket, a parameter, a right square bracket,
    #     and then a left square bracket.)
    #   * All right square brackets after the required parameters must be
    #     consecutive.
    #
    # These rules are enforced with a single state variable:
    # "parameter_state".  (Previously the code was a miasma of ifs and
    # separate boolean state variables.)  The states are defined in the
    # ParamState class.

    def state_parameters_start(self, line: str) -> Nichts:
        wenn not self.valid_line(line):
            return

        # wenn this line is not indented, we have no parameters
        wenn not self.indent.infer(line):
            return self.next(self.state_function_docstring, line)

        assert self.function is not Nichts
        wenn self.function.kind in {GETTER, SETTER}:
            getset = self.function.kind.name.lower()
            fail(f"@{getset} methods cannot define parameters")

        self.parameter_continuation = ''
        return self.next(self.state_parameter, line)


    def to_required(self) -> Nichts:
        """
        Transition to the "required" parameter state.
        """
        wenn self.parameter_state is not ParamState.REQUIRED:
            self.parameter_state = ParamState.REQUIRED
            assert self.function is not Nichts
            fuer p in self.function.parameters.values():
                p.group = -p.group

    def state_parameter(self, line: str) -> Nichts:
        assert isinstance(self.function, Function)

        wenn not self.valid_line(line):
            return

        wenn self.parameter_continuation:
            line = self.parameter_continuation + ' ' + line.lstrip()
            self.parameter_continuation = ''

        assert self.indent.depth == 2
        indent = self.indent.infer(line)
        wenn indent == -1:
            # we outdented, must be to definition column
            return self.next(self.state_function_docstring, line)

        wenn indent == 1:
            # we indented, must be to new parameter docstring column
            return self.next(self.state_parameter_docstring_start, line)

        line = line.rstrip()
        wenn line.endswith('\\'):
            self.parameter_continuation = line[:-1]
            return

        line = line.lstrip()
        version: VersionTuple | Nichts = Nichts
        match = self.from_version_re.fullmatch(line)
        wenn match:
            line = match[1]
            version = self.parse_version(match[2])

        func = self.function
        match line:
            case '*':
                self.parse_star(func, version)
            case '[':
                self.parse_opening_square_bracket(func)
            case ']':
                self.parse_closing_square_bracket(func)
            case '/':
                self.parse_slash(func, version)
            case param:
                self.parse_parameter(param)

    def parse_parameter(self, line: str) -> Nichts:
        assert self.function is not Nichts

        match self.parameter_state:
            case ParamState.START | ParamState.REQUIRED:
                self.to_required()
            case ParamState.LEFT_SQUARE_BEFORE:
                self.parameter_state = ParamState.GROUP_BEFORE
            case ParamState.GROUP_BEFORE:
                wenn not self.group:
                    self.to_required()
            case ParamState.GROUP_AFTER | ParamState.OPTIONAL:
                pass
            case st:
                fail(f"Function {self.function.name} has an unsupported group configuration. (Unexpected state {st}.a)")

        # handle "as" fuer  parameters too
        c_name = Nichts
        m = re.match(r'(?:\* *)?\w+( +as +(\w+))', line)
        wenn m:
            c_name = m[2]
            line = line[:m.start(1)] + line[m.end(1):]

        try:
            ast_input = f"def x({line}\n): pass"
            module = ast.parse(ast_input)
        except SyntaxError:
            fail(f"Function {self.function.name!r} has an invalid parameter declaration: {line!r}")

        function = module.body[0]
        assert isinstance(function, ast.FunctionDef)
        function_args = function.args

        wenn len(function_args.args) > 1:
            fail(f"Function {self.function.name!r} has an "
                 f"invalid parameter declaration (comma?): {line!r}")
        wenn function_args.kwarg:
            fail(f"Function {self.function.name!r} has an "
                 f"invalid parameter declaration (**kwargs?): {line!r}")

        wenn function_args.vararg:
            self.check_previous_star()
            self.check_remaining_star()
            is_vararg = Wahr
            parameter = function_args.vararg
        sonst:
            is_vararg = Falsch
            parameter = function_args.args[0]

        parameter_name = parameter.arg
        name, legacy, kwargs = self.parse_converter(parameter.annotation)
        wenn is_vararg:
            name = 'varpos_' + name

        value: object
        wenn not function_args.defaults:
            wenn is_vararg:
                value = NULL
            sonst:
                wenn self.parameter_state is ParamState.OPTIONAL:
                    fail(f"Can't have a parameter without a default ({parameter_name!r}) "
                          "after a parameter with a default!")
                value = unspecified
            wenn 'py_default' in kwargs:
                fail("You can't specify py_default without specifying a default value!")
        sonst:
            expr = function_args.defaults[0]
            default = ast_input[expr.col_offset: expr.end_col_offset].strip()

            wenn self.parameter_state is ParamState.REQUIRED:
                self.parameter_state = ParamState.OPTIONAL
            bad = Falsch
            try:
                wenn 'c_default' not in kwargs:
                    # we can only represent very simple data values in C.
                    # detect whether default is okay, via a denylist
                    # of disallowed ast nodes.
                    klasse DetectBadNodes(ast.NodeVisitor):
                        bad = Falsch
                        def bad_node(self, node: ast.AST) -> Nichts:
                            self.bad = Wahr

                        # inline function call
                        visit_Call = bad_node
                        # inline wenn statement ("x = 3 wenn y sonst z")
                        visit_IfExp = bad_node

                        # comprehensions and generator expressions
                        visit_ListComp = visit_SetComp = bad_node
                        visit_DictComp = visit_GeneratorExp = bad_node

                        # literals fuer advanced types
                        visit_Dict = visit_Set = bad_node
                        visit_List = visit_Tuple = bad_node

                        # "starred": "a = [1, 2, 3]; *a"
                        visit_Starred = bad_node

                    denylist = DetectBadNodes()
                    denylist.visit(expr)
                    bad = denylist.bad
                sonst:
                    # wenn they specify a c_default, we can be more lenient about the default value.
                    # but at least make an attempt at ensuring it's a valid expression.
                    code = compile(ast.Expression(expr), '<expr>', 'eval')
                    try:
                        value = eval(code)
                    except NameError:
                        pass # probably a named constant
                    except Exception as e:
                        fail("Malformed expression given as default value "
                             f"{default!r} caused {e!r}")
                    sonst:
                        wenn value is unspecified:
                            fail("'unspecified' is not a legal default value!")
                wenn bad:
                    fail(f"Unsupported expression as default value: {default!r}")

                # mild hack: explicitly support NULL as a default value
                c_default: str | Nichts
                wenn isinstance(expr, ast.Name) and expr.id == 'NULL':
                    value = NULL
                    py_default = '<unrepresentable>'
                    c_default = "NULL"
                sowenn (isinstance(expr, ast.BinOp) or
                    (isinstance(expr, ast.UnaryOp) and
                     not (isinstance(expr.operand, ast.Constant) and
                          type(expr.operand.value) in {int, float, complex})
                    )):
                    c_default = kwargs.get("c_default")
                    wenn not (isinstance(c_default, str) and c_default):
                        fail(f"When you specify an expression ({default!r}) "
                             f"as your default value, "
                             f"you MUST specify a valid c_default.",
                             ast.dump(expr))
                    py_default = default
                    value = unknown
                sowenn isinstance(expr, ast.Attribute):
                    a = []
                    n: ast.expr | ast.Attribute = expr
                    while isinstance(n, ast.Attribute):
                        a.append(n.attr)
                        n = n.value
                    wenn not isinstance(n, ast.Name):
                        fail(f"Unsupported default value {default!r} "
                             "(looked like a Python constant)")
                    a.append(n.id)
                    py_default = ".".join(reversed(a))

                    c_default = kwargs.get("c_default")
                    wenn not (isinstance(c_default, str) and c_default):
                        fail(f"When you specify a named constant ({py_default!r}) "
                             "as your default value, "
                             "you MUST specify a valid c_default.")

                    try:
                        value = eval(py_default)
                    except NameError:
                        value = unknown
                sonst:
                    value = ast.literal_eval(expr)
                    py_default = repr(value)
                    wenn isinstance(value, (bool, NoneType)):
                        c_default = "Py_" + py_default
                    sowenn isinstance(value, str):
                        c_default = libclinic.c_repr(value)
                    sonst:
                        c_default = py_default

            except (ValueError, AttributeError):
                value = unknown
                c_default = kwargs.get("c_default")
                py_default = default
                wenn not (isinstance(c_default, str) and c_default):
                    fail("When you specify a named constant "
                         f"({py_default!r}) as your default value, "
                         "you MUST specify a valid c_default.")

            kwargs.setdefault('c_default', c_default)
            kwargs.setdefault('py_default', py_default)

        dict = legacy_converters wenn legacy sonst converters
        legacy_str = "legacy " wenn legacy sonst ""
        wenn name not in dict:
            fail(f'{name!r} is not a valid {legacy_str}converter')
        # wenn you use a c_name fuer the parameter, we just give that name to the converter
        # but the parameter object gets the python name
        converter = dict[name](c_name or parameter_name, parameter_name, self.function, value, **kwargs)

        kind: inspect._ParameterKind
        wenn is_vararg:
            kind = inspect.Parameter.VAR_POSITIONAL
        sowenn self.keyword_only:
            kind = inspect.Parameter.KEYWORD_ONLY
        sonst:
            kind = inspect.Parameter.POSITIONAL_OR_KEYWORD

        wenn isinstance(converter, self_converter):
            wenn len(self.function.parameters) == 1:
                wenn self.parameter_state is not ParamState.REQUIRED:
                    fail("A 'self' parameter cannot be marked optional.")
                wenn value is not unspecified:
                    fail("A 'self' parameter cannot have a default value.")
                wenn self.group:
                    fail("A 'self' parameter cannot be in an optional group.")
                kind = inspect.Parameter.POSITIONAL_ONLY
                self.parameter_state = ParamState.START
                self.function.parameters.clear()
            sonst:
                fail("A 'self' parameter, wenn specified, must be the "
                     "very first thing in the parameter block.")

        wenn isinstance(converter, defining_class_converter):
            _lp = len(self.function.parameters)
            wenn _lp == 1:
                wenn self.parameter_state is not ParamState.REQUIRED:
                    fail("A 'defining_class' parameter cannot be marked optional.")
                wenn value is not unspecified:
                    fail("A 'defining_class' parameter cannot have a default value.")
                wenn self.group:
                    fail("A 'defining_class' parameter cannot be in an optional group.")
                wenn self.function.cls is Nichts:
                    fail("A 'defining_class' parameter cannot be defined at module level.")
                kind = inspect.Parameter.POSITIONAL_ONLY
            sonst:
                fail("A 'defining_class' parameter, wenn specified, must either "
                     "be the first thing in the parameter block, or come just "
                     "after 'self'.")


        p = Parameter(parameter_name, kind, function=self.function,
                      converter=converter, default=value, group=self.group,
                      deprecated_positional=self.deprecated_positional)

        names = [k.name fuer k in self.function.parameters.values()]
        wenn parameter_name in names[1:]:
            fail(f"You can't have two parameters named {parameter_name!r}!")
        sowenn names and parameter_name == names[0] and c_name is Nichts:
            fail(f"Parameter {parameter_name!r} requires a custom C name")

        key = f"{parameter_name}_as_{c_name}" wenn c_name sonst parameter_name
        self.function.parameters[key] = p

        wenn is_vararg:
            self.keyword_only = Wahr

    @staticmethod
    def parse_converter(
        annotation: ast.expr | Nichts
    ) -> tuple[str, bool, ConverterArgs]:
        match annotation:
            case ast.Constant(value=str() as value):
                return value, Wahr, {}
            case ast.Name(name):
                return name, Falsch, {}
            case ast.Call(func=ast.Name(name)):
                kwargs: ConverterArgs = {}
                fuer node in annotation.keywords:
                    wenn not isinstance(node.arg, str):
                        fail("Cannot use a kwarg splat in a function-call annotation")
                    kwargs[node.arg] = eval_ast_expr(node.value)
                return name, Falsch, kwargs
            case _:
                fail(
                    "Annotations must be either a name, a function call, or a string."
                )

    def parse_version(self, thenceforth: str) -> VersionTuple:
        """Parse Python version in `[from ...]` marker."""
        assert isinstance(self.function, Function)

        try:
            major, minor = thenceforth.split(".")
            return int(major), int(minor)
        except ValueError:
            fail(
                f"Function {self.function.name!r}: expected format '[from major.minor]' "
                f"where 'major' and 'minor' are integers; got {thenceforth!r}"
            )

    def parse_star(self, function: Function, version: VersionTuple | Nichts) -> Nichts:
        """Parse keyword-only parameter marker '*'.

        The 'version' parameter signifies the future version from which
        the marker will take effect (Nichts means it is already in effect).
        """
        wenn version is Nichts:
            self.check_previous_star()
            self.check_remaining_star()
            self.keyword_only = Wahr
        sonst:
            wenn self.keyword_only:
                fail(f"Function {function.name!r}: '* [from ...]' must precede '*'")
            wenn self.deprecated_positional:
                wenn self.deprecated_positional == version:
                    fail(f"Function {function.name!r} uses '* [from "
                         f"{version[0]}.{version[1]}]' more than once.")
                wenn self.deprecated_positional < version:
                    fail(f"Function {function.name!r}: '* [from "
                         f"{version[0]}.{version[1]}]' must precede '* [from "
                         f"{self.deprecated_positional[0]}.{self.deprecated_positional[1]}]'")
        self.deprecated_positional = version

    def parse_opening_square_bracket(self, function: Function) -> Nichts:
        """Parse opening parameter group symbol '['."""
        match self.parameter_state:
            case ParamState.START | ParamState.LEFT_SQUARE_BEFORE:
                self.parameter_state = ParamState.LEFT_SQUARE_BEFORE
            case ParamState.REQUIRED | ParamState.GROUP_AFTER:
                self.parameter_state = ParamState.GROUP_AFTER
            case st:
                fail(f"Function {function.name!r} "
                     f"has an unsupported group configuration. "
                     f"(Unexpected state {st}.b)")
        self.group += 1
        function.docstring_only = Wahr

    def parse_closing_square_bracket(self, function: Function) -> Nichts:
        """Parse closing parameter group symbol ']'."""
        wenn not self.group:
            fail(f"Function {function.name!r} has a ']' without a matching '['.")
        wenn not any(p.group == self.group fuer p in function.parameters.values()):
            fail(f"Function {function.name!r} has an empty group. "
                 "All groups must contain at least one parameter.")
        self.group -= 1
        match self.parameter_state:
            case ParamState.LEFT_SQUARE_BEFORE | ParamState.GROUP_BEFORE:
                self.parameter_state = ParamState.GROUP_BEFORE
            case ParamState.GROUP_AFTER | ParamState.RIGHT_SQUARE_AFTER:
                self.parameter_state = ParamState.RIGHT_SQUARE_AFTER
            case st:
                fail(f"Function {function.name!r} "
                     f"has an unsupported group configuration. "
                     f"(Unexpected state {st}.c)")

    def parse_slash(self, function: Function, version: VersionTuple | Nichts) -> Nichts:
        """Parse positional-only parameter marker '/'.

        The 'version' parameter signifies the future version from which
        the marker will take effect (Nichts means it is already in effect).
        """
        wenn version is Nichts:
            wenn self.deprecated_keyword:
                fail(f"Function {function.name!r}: '/' must precede '/ [from ...]'")
            wenn self.deprecated_positional:
                fail(f"Function {function.name!r}: '/' must precede '* [from ...]'")
            wenn self.keyword_only:
                fail(f"Function {function.name!r}: '/' must precede '*'")
            wenn self.positional_only:
                fail(f"Function {function.name!r} uses '/' more than once.")
        sonst:
            wenn self.deprecated_keyword:
                wenn self.deprecated_keyword == version:
                    fail(f"Function {function.name!r} uses '/ [from "
                         f"{version[0]}.{version[1]}]' more than once.")
                wenn self.deprecated_keyword > version:
                    fail(f"Function {function.name!r}: '/ [from "
                         f"{version[0]}.{version[1]}]' must precede '/ [from "
                         f"{self.deprecated_keyword[0]}.{self.deprecated_keyword[1]}]'")
            wenn self.deprecated_positional:
                fail(f"Function {function.name!r}: '/ [from ...]' must precede '* [from ...]'")
            wenn self.keyword_only:
                fail(f"Function {function.name!r}: '/ [from ...]' must precede '*'")
        self.positional_only = Wahr
        self.deprecated_keyword = version
        wenn version is not Nichts:
            found = Falsch
            fuer p in reversed(function.parameters.values()):
                found = p.kind is inspect.Parameter.POSITIONAL_OR_KEYWORD
                break
            wenn not found:
                fail(f"Function {function.name!r} specifies '/ [from ...]' "
                     f"without preceding parameters.")
        # REQUIRED and OPTIONAL are allowed here, that allows positional-only
        # without option groups to work (and have default values!)
        allowed = {
            ParamState.REQUIRED,
            ParamState.OPTIONAL,
            ParamState.RIGHT_SQUARE_AFTER,
            ParamState.GROUP_BEFORE,
        }
        wenn (self.parameter_state not in allowed) or self.group:
            fail(f"Function {function.name!r} has an unsupported group configuration. "
                 f"(Unexpected state {self.parameter_state}.d)")
        # fixup preceding parameters
        fuer p in function.parameters.values():
            wenn p.kind is inspect.Parameter.POSITIONAL_OR_KEYWORD:
                wenn version is Nichts:
                    p.kind = inspect.Parameter.POSITIONAL_ONLY
                sowenn p.deprecated_keyword is Nichts:
                    p.deprecated_keyword = version

    def state_parameter_docstring_start(self, line: str) -> Nichts:
        assert self.indent.margin is not Nichts, "self.margin.infer() has not yet been called to set the margin"
        self.parameter_docstring_indent = len(self.indent.margin)
        assert self.indent.depth == 3
        return self.next(self.state_parameter_docstring, line)

    def docstring_append(self, obj: Function | Parameter, line: str) -> Nichts:
        """Add a rstripped line to the current docstring."""
        # gh-80282: We filter out non-ASCII characters from the docstring,
        # since historically, some compilers may balk on non-ASCII input.
        # If you're using Argument Clinic in an external project,
        # you may not need to support the same array of platforms as CPython,
        # so you may be able to remove this restriction.
        matches = re.finditer(r'[^\x00-\x7F]', line)
        wenn offending := ", ".join([repr(m[0]) fuer m in matches]):
            warn("Non-ascii characters are not allowed in docstrings:",
                 offending)

        docstring = obj.docstring
        wenn docstring:
            docstring += "\n"
        wenn stripped := line.rstrip():
            docstring += self.indent.dedent(stripped)
        obj.docstring = docstring

    # every line of the docstring must start with at least F spaces,
    # where F > P.
    # these F spaces will be stripped.
    def state_parameter_docstring(self, line: str) -> Nichts:
        wenn not self.valid_line(line):
            return

        indent = self.indent.measure(line)
        wenn indent < self.parameter_docstring_indent:
            self.indent.infer(line)
            assert self.indent.depth < 3
            wenn self.indent.depth == 2:
                # back to a parameter
                return self.next(self.state_parameter, line)
            assert self.indent.depth == 1
            return self.next(self.state_function_docstring, line)

        assert self.function and self.function.parameters
        last_param = next(reversed(self.function.parameters.values()))
        self.docstring_append(last_param, line)

    # the final stanza of the DSL is the docstring.
    def state_function_docstring(self, line: str) -> Nichts:
        assert self.function is not Nichts

        wenn self.group:
            fail(f"Function {self.function.name!r} has a ']' without a matching '['.")

        wenn not self.valid_line(line):
            return

        self.docstring_append(self.function, line)

    @staticmethod
    def format_docstring_signature(
        f: Function, parameters: list[Parameter]
    ) -> str:
        lines = []
        lines.append(f.displayname)
        wenn f.forced_text_signature:
            lines.append(f.forced_text_signature)
        sowenn f.kind in {GETTER, SETTER}:
            # @getter and @setter do not need signatures like a method or a function.
            return ''
        sonst:
            lines.append('(')

            # populate "right_bracket_count" field fuer every parameter
            assert parameters, "We should always have a self parameter. " + repr(f)
            assert isinstance(parameters[0].converter, self_converter)
            # self is always positional-only.
            assert parameters[0].is_positional_only()
            assert parameters[0].right_bracket_count == 0
            positional_only = Wahr
            fuer p in parameters[1:]:
                wenn not p.is_positional_only():
                    positional_only = Falsch
                sonst:
                    assert positional_only
                wenn positional_only:
                    p.right_bracket_count = abs(p.group)
                sonst:
                    # don't put any right brackets around non-positional-only parameters, ever.
                    p.right_bracket_count = 0

            right_bracket_count = 0

            def fix_right_bracket_count(desired: int) -> str:
                nonlocal right_bracket_count
                s = ''
                while right_bracket_count < desired:
                    s += '['
                    right_bracket_count += 1
                while right_bracket_count > desired:
                    s += ']'
                    right_bracket_count -= 1
                return s

            need_slash = Falsch
            added_slash = Falsch
            need_a_trailing_slash = Falsch

            # we only need a trailing slash:
            #   * wenn this is not a "docstring_only" signature
            #   * and wenn the last *shown* parameter is
            #     positional only
            wenn not f.docstring_only:
                fuer p in reversed(parameters):
                    wenn not p.converter.show_in_signature:
                        continue
                    wenn p.is_positional_only():
                        need_a_trailing_slash = Wahr
                    break


            added_star = Falsch

            first_parameter = Wahr
            last_p = parameters[-1]
            line_length = len(''.join(lines))
            indent = " " * line_length
            def add_parameter(text: str) -> Nichts:
                nonlocal line_length
                nonlocal first_parameter
                wenn first_parameter:
                    s = text
                    first_parameter = Falsch
                sonst:
                    s = ' ' + text
                    wenn line_length + len(s) >= 72:
                        lines.extend(["\n", indent])
                        line_length = len(indent)
                        s = text
                line_length += len(s)
                lines.append(s)

            fuer p in parameters:
                wenn not p.converter.show_in_signature:
                    continue
                assert p.name

                is_self = isinstance(p.converter, self_converter)
                wenn is_self and f.docstring_only:
                    # this isn't a real machine-parsable signature,
                    # so let's not print the "self" parameter
                    continue

                wenn p.is_positional_only():
                    need_slash = not f.docstring_only
                sowenn need_slash and not (added_slash or p.is_positional_only()):
                    added_slash = Wahr
                    add_parameter('/,')

                wenn p.is_keyword_only() and not added_star:
                    added_star = Wahr
                    add_parameter('*,')

                p_lines = [fix_right_bracket_count(p.right_bracket_count)]

                wenn isinstance(p.converter, self_converter):
                    # annotate first parameter as being a "self".
                    #
                    # wenn inspect.Signature gets this function,
                    # and it's already bound, the self parameter
                    # will be stripped off.
                    #
                    # wenn it's not bound, it should be marked
                    # as positional-only.
                    #
                    # note: we don't print "self" fuer __init__,
                    # because this isn't actually the signature
                    # fuer __init__.  (it can't be, __init__ doesn't
                    # have a docstring.)  wenn this is an __init__
                    # (or __new__), then this signature is for
                    # calling the klasse to construct a new instance.
                    p_lines.append('$')

                wenn p.is_vararg():
                    p_lines.append("*")
                    added_star = Wahr

                name = p.converter.signature_name or p.name
                p_lines.append(name)

                wenn not p.is_vararg() and p.converter.is_optional():
                    p_lines.append('=')
                    value = p.converter.py_default
                    wenn not value:
                        value = repr(p.converter.default)
                    p_lines.append(value)

                wenn (p != last_p) or need_a_trailing_slash:
                    p_lines.append(',')

                p_output = "".join(p_lines)
                add_parameter(p_output)

            lines.append(fix_right_bracket_count(0))
            wenn need_a_trailing_slash:
                add_parameter('/')
            lines.append(')')

        # PEP 8 says:
        #
        #     The Python standard library will not use function annotations
        #     as that would result in a premature commitment to a particular
        #     annotation style. Instead, the annotations are left fuer users
        #     to discover and experiment with useful annotation styles.
        #
        # therefore this is commented out:
        #
        # wenn f.return_converter.py_default:
        #     lines.append(' -> ')
        #     lines.append(f.return_converter.py_default)

        wenn not f.docstring_only:
            lines.append("\n" + libclinic.SIG_END_MARKER + "\n")

        signature_line = "".join(lines)

        # now fix up the places where the brackets look wrong
        return signature_line.replace(', ]', ',] ')

    @staticmethod
    def format_docstring_parameters(params: list[Parameter]) -> str:
        """Create substitution text fuer {parameters}"""
        return "".join(p.render_docstring() + "\n" fuer p in params wenn p.docstring)

    def format_docstring(self) -> str:
        assert self.function is not Nichts
        f = self.function
        # For the following special cases, it does not make sense to render a docstring.
        wenn f.kind in {METHOD_INIT, METHOD_NEW, GETTER, SETTER} and not f.docstring:
            return f.docstring

        # Enforce the summary line!
        # The first line of a docstring should be a summary of the function.
        # It should fit on one line (80 columns? 79 maybe?) and be a paragraph
        # by itself.
        #
        # Argument Clinic enforces the following rule:
        #  * either the docstring is empty,
        #  * or it must have a summary line.
        #
        # Guido said Clinic should enforce this:
        # http://mail.python.org/pipermail/python-dev/2013-June/127110.html

        lines = f.docstring.split('\n')
        wenn len(lines) >= 2:
            wenn lines[1]:
                fail(f"Docstring fuer {f.full_name!r} does not have a summary line!\n"
                     "Every non-blank function docstring must start with "
                     "a single line summary followed by an empty line.")
        sowenn len(lines) == 1:
            # the docstring is only one line right now--the summary line.
            # add an empty line after the summary line so we have space
            # between it and the {parameters} we're about to add.
            lines.append('')

        # Fail wenn the summary line is too long.
        # Warn wenn any of the body lines are too long.
        # Existing violations are recorded in OVERLONG_{SUMMARY,BODY}.
        max_width = f.docstring_line_width
        summary_len = len(lines[0])
        max_body = max(map(len, lines[1:]))
        wenn summary_len > max_width:
            wenn not self.permit_long_summary:
                fail(f"Summary line fuer {f.full_name!r} is too long!\n"
                     f"The summary line must be no longer than {max_width} characters.")
        sonst:
            wenn self.permit_long_summary:
                warn("Remove the @permit_long_summary decorator from "
                     f"{f.full_name!r}!\n")

        wenn max_body > max_width:
            wenn not self.permit_long_docstring_body:
                warn(f"Docstring lines fuer {f.full_name!r} are too long!\n"
                     f"Lines should be no longer than {max_width} characters.")
        sonst:
            wenn self.permit_long_docstring_body:
                warn("Remove the @permit_long_docstring_body decorator from "
                     f"{f.full_name!r}!\n")

        parameters_marker_count = len(f.docstring.split('{parameters}')) - 1
        wenn parameters_marker_count > 1:
            fail('You may not specify {parameters} more than once in a docstring!')

        # insert signature at front and params after the summary line
        wenn not parameters_marker_count:
            lines.insert(2, '{parameters}')
        lines.insert(0, '{signature}')

        # finalize docstring
        params = f.render_parameters
        parameters = self.format_docstring_parameters(params)
        signature = self.format_docstring_signature(f, params)
        docstring = "\n".join(lines)
        return libclinic.linear_format(docstring,
                                       signature=signature,
                                       parameters=parameters).rstrip()

    def check_remaining_star(self, lineno: int | Nichts = Nichts) -> Nichts:
        assert isinstance(self.function, Function)

        wenn self.keyword_only:
            symbol = '*'
        sowenn self.deprecated_positional:
            symbol = '* [from ...]'
        sonst:
            return

        fuer p in reversed(self.function.parameters.values()):
            wenn self.keyword_only:
                wenn (p.kind == inspect.Parameter.KEYWORD_ONLY or
                    p.kind == inspect.Parameter.VAR_POSITIONAL):
                    return
            sowenn self.deprecated_positional:
                wenn p.deprecated_positional == self.deprecated_positional:
                    return
            break

        fail(f"Function {self.function.name!r} specifies {symbol!r} "
             f"without following parameters.", line_number=lineno)

    def check_previous_star(self) -> Nichts:
        assert isinstance(self.function, Function)

        wenn self.keyword_only:
            fail(f"Function {self.function.name!r} uses '*' more than once.")


    def do_post_block_processing_cleanup(self, lineno: int) -> Nichts:
        """
        Called when processing the block is done.
        """
        wenn not self.function:
            return

        self.check_remaining_star(lineno)
        try:
            self.function.docstring = self.format_docstring()
        except ClinicError as exc:
            exc.lineno = lineno
            exc.filename = self.clinic.filename
            raise
