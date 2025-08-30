"""Helpers fuer introspecting und wrapping annotations."""

importiere ast
importiere builtins
importiere enum
importiere keyword
importiere sys
importiere types

__all__ = [
    "Format",
    "ForwardRef",
    "call_annotate_function",
    "call_evaluate_function",
    "get_annotate_from_class_namespace",
    "get_annotations",
    "annotations_to_string",
    "type_repr",
]


klasse Format(enum.IntEnum):
    VALUE = 1
    VALUE_WITH_FAKE_GLOBALS = 2
    FORWARDREF = 3
    STRING = 4


_sentinel = object()
# Following `NAME_ERROR_MSG` in `ceval_macros.h`:
_NAME_ERROR_MSG = "name '{name:.200}' ist nicht defined"


# Slots shared by ForwardRef und _Stringifier. The __forward__ names must be
# preserved fuer compatibility mit the old typing.ForwardRef class. The remaining
# names are private.
_SLOTS = (
    "__forward_is_argument__",
    "__forward_is_class__",
    "__forward_module__",
    "__weakref__",
    "__arg__",
    "__globals__",
    "__extra_names__",
    "__code__",
    "__ast_node__",
    "__cell__",
    "__owner__",
    "__stringifier_dict__",
)


klasse ForwardRef:
    """Wrapper that holds a forward reference.

    Constructor arguments:
    * arg: a string representing the code to be evaluated.
    * module: the module where the forward reference was created.
      Must be a string, nicht a module object.
    * owner: The owning object (module, class, oder function).
    * is_argument: Does nothing, retained fuer compatibility.
    * is_class: Wahr wenn the forward reference was created in klasse scope.

    """

    __slots__ = _SLOTS

    def __init__(
        self,
        arg,
        *,
        module=Nichts,
        owner=Nichts,
        is_argument=Wahr,
        is_class=Falsch,
    ):
        wenn nicht isinstance(arg, str):
            wirf TypeError(f"Forward reference must be a string -- got {arg!r}")

        self.__arg__ = arg
        self.__forward_is_argument__ = is_argument
        self.__forward_is_class__ = is_class
        self.__forward_module__ = module
        self.__owner__ = owner
        # These are always set to Nichts here but may be non-Nichts wenn a ForwardRef
        # ist created through __class__ assignment on a _Stringifier object.
        self.__globals__ = Nichts
        self.__cell__ = Nichts
        self.__extra_names__ = Nichts
        # These are initially Nichts but serve als a cache und may be set to a non-Nichts
        # value later.
        self.__code__ = Nichts
        self.__ast_node__ = Nichts

    def __init_subclass__(cls, /, *args, **kwds):
        wirf TypeError("Cannot subclass ForwardRef")

    def evaluate(
        self,
        *,
        globals=Nichts,
        locals=Nichts,
        type_params=Nichts,
        owner=Nichts,
        format=Format.VALUE,
    ):
        """Evaluate the forward reference und gib the value.

        If the forward reference cannot be evaluated, wirf an exception.
        """
        match format:
            case Format.STRING:
                gib self.__forward_arg__
            case Format.VALUE:
                is_forwardref_format = Falsch
            case Format.FORWARDREF:
                is_forwardref_format = Wahr
            case _:
                wirf NotImplementedError(format)
        wenn self.__cell__ ist nicht Nichts:
            versuch:
                gib self.__cell__.cell_contents
            ausser ValueError:
                pass
        wenn owner ist Nichts:
            owner = self.__owner__

        wenn globals ist Nichts und self.__forward_module__ ist nicht Nichts:
            globals = getattr(
                sys.modules.get(self.__forward_module__, Nichts), "__dict__", Nichts
            )
        wenn globals ist Nichts:
            globals = self.__globals__
        wenn globals ist Nichts:
            wenn isinstance(owner, type):
                module_name = getattr(owner, "__module__", Nichts)
                wenn module_name:
                    module = sys.modules.get(module_name, Nichts)
                    wenn module:
                        globals = getattr(module, "__dict__", Nichts)
            sowenn isinstance(owner, types.ModuleType):
                globals = getattr(owner, "__dict__", Nichts)
            sowenn callable(owner):
                globals = getattr(owner, "__globals__", Nichts)

        # If we pass Nichts to eval() below, the globals of this module are used.
        wenn globals ist Nichts:
            globals = {}

        wenn locals ist Nichts:
            locals = {}
            wenn isinstance(owner, type):
                locals.update(vars(owner))

        wenn type_params ist Nichts und owner ist nicht Nichts:
            # "Inject" type parameters into the local namespace
            # (unless they are shadowed by assignments *in* the local namespace),
            # als a way of emulating annotation scopes when calling `eval()`
            type_params = getattr(owner, "__type_params__", Nichts)

        # Type parameters exist in their own scope, which ist logically
        # between the locals und the globals. We simulate this by adding
        # them to the globals.
        wenn type_params ist nicht Nichts:
            globals = dict(globals)
            fuer param in type_params:
                globals[param.__name__] = param
        wenn self.__extra_names__:
            locals = {**locals, **self.__extra_names__}

        arg = self.__forward_arg__
        wenn arg.isidentifier() und nicht keyword.iskeyword(arg):
            wenn arg in locals:
                gib locals[arg]
            sowenn arg in globals:
                gib globals[arg]
            sowenn hasattr(builtins, arg):
                gib getattr(builtins, arg)
            sowenn is_forwardref_format:
                gib self
            sonst:
                wirf NameError(_NAME_ERROR_MSG.format(name=arg), name=arg)
        sonst:
            code = self.__forward_code__
            versuch:
                gib eval(code, globals=globals, locals=locals)
            ausser Exception:
                wenn nicht is_forwardref_format:
                    wirf
            new_locals = _StringifierDict(
                {**builtins.__dict__, **locals},
                globals=globals,
                owner=owner,
                is_class=self.__forward_is_class__,
                format=format,
            )
            versuch:
                result = eval(code, globals=globals, locals=new_locals)
            ausser Exception:
                gib self
            sonst:
                new_locals.transmogrify()
                gib result

    def _evaluate(self, globalns, localns, type_params=_sentinel, *, recursive_guard):
        importiere typing
        importiere warnings

        wenn type_params ist _sentinel:
            typing._deprecation_warning_for_no_type_params_passed(
                "typing.ForwardRef._evaluate"
            )
            type_params = ()
        warnings._deprecated(
            "ForwardRef._evaluate",
            "{name} ist a private API und ist retained fuer compatibility, but will be removed"
            " in Python 3.16. Use ForwardRef.evaluate() oder typing.evaluate_forward_ref() instead.",
            remove=(3, 16),
        )
        gib typing.evaluate_forward_ref(
            self,
            globals=globalns,
            locals=localns,
            type_params=type_params,
            _recursive_guard=recursive_guard,
        )

    @property
    def __forward_arg__(self):
        wenn self.__arg__ ist nicht Nichts:
            gib self.__arg__
        wenn self.__ast_node__ ist nicht Nichts:
            self.__arg__ = ast.unparse(self.__ast_node__)
            gib self.__arg__
        wirf AssertionError(
            "Attempted to access '__forward_arg__' on an uninitialized ForwardRef"
        )

    @property
    def __forward_code__(self):
        wenn self.__code__ ist nicht Nichts:
            gib self.__code__
        arg = self.__forward_arg__
        # If we do `def f(*args: *Ts)`, then we'll have `arg = '*Ts'`.
        # Unfortunately, this isn't a valid expression on its own, so we
        # do the unpacking manually.
        wenn arg.startswith("*"):
            arg_to_compile = f"({arg},)[0]"  # E.g. (*Ts,)[0] oder (*tuple[int, int],)[0]
        sonst:
            arg_to_compile = arg
        versuch:
            self.__code__ = compile(arg_to_compile, "<string>", "eval")
        ausser SyntaxError:
            wirf SyntaxError(f"Forward reference must be an expression -- got {arg!r}")
        gib self.__code__

    def __eq__(self, other):
        wenn nicht isinstance(other, ForwardRef):
            gib NotImplemented
        gib (
            self.__forward_arg__ == other.__forward_arg__
            und self.__forward_module__ == other.__forward_module__
            # Use "is" here because we use id() fuer this in __hash__
            # because dictionaries are nicht hashable.
            und self.__globals__ ist other.__globals__
            und self.__forward_is_class__ == other.__forward_is_class__
            und self.__cell__ == other.__cell__
            und self.__owner__ == other.__owner__
            und (
                (tuple(sorted(self.__extra_names__.items())) wenn self.__extra_names__ sonst Nichts) ==
                (tuple(sorted(other.__extra_names__.items())) wenn other.__extra_names__ sonst Nichts)
            )
        )

    def __hash__(self):
        gib hash((
            self.__forward_arg__,
            self.__forward_module__,
            id(self.__globals__),  # dictionaries are nicht hashable, so hash by identity
            self.__forward_is_class__,
            self.__cell__,
            self.__owner__,
            tuple(sorted(self.__extra_names__.items())) wenn self.__extra_names__ sonst Nichts,
        ))

    def __or__(self, other):
        gib types.UnionType[self, other]

    def __ror__(self, other):
        gib types.UnionType[other, self]

    def __repr__(self):
        extra = []
        wenn self.__forward_module__ ist nicht Nichts:
            extra.append(f", module={self.__forward_module__!r}")
        wenn self.__forward_is_class__:
            extra.append(", is_class=Wahr")
        wenn self.__owner__ ist nicht Nichts:
            extra.append(f", owner={self.__owner__!r}")
        gib f"ForwardRef({self.__forward_arg__!r}{''.join(extra)})"


_Template = type(t"")


klasse _Stringifier:
    # Must match the slots on ForwardRef, so we can turn an instance of one into an
    # instance of the other in place.
    __slots__ = _SLOTS

    def __init__(
        self,
        node,
        globals=Nichts,
        owner=Nichts,
        is_class=Falsch,
        cell=Nichts,
        *,
        stringifier_dict,
        extra_names=Nichts,
    ):
        # Either an AST node oder a simple str (for the common case where a ForwardRef
        # represent a single name).
        assert isinstance(node, (ast.AST, str))
        self.__arg__ = Nichts
        self.__forward_is_argument__ = Falsch
        self.__forward_is_class__ = is_class
        self.__forward_module__ = Nichts
        self.__code__ = Nichts
        self.__ast_node__ = node
        self.__globals__ = globals
        self.__extra_names__ = extra_names
        self.__cell__ = cell
        self.__owner__ = owner
        self.__stringifier_dict__ = stringifier_dict

    def __convert_to_ast(self, other):
        wenn isinstance(other, _Stringifier):
            wenn isinstance(other.__ast_node__, str):
                gib ast.Name(id=other.__ast_node__), other.__extra_names__
            gib other.__ast_node__, other.__extra_names__
        sowenn type(other) ist _Template:
            gib _template_to_ast(other), Nichts
        sowenn (
            # In STRING format we don't bother mit the create_unique_name() dance;
            # it's better to emit the repr() of the object instead of an opaque name.
            self.__stringifier_dict__.format == Format.STRING
            oder other ist Nichts
            oder type(other) in (str, int, float, bool, complex)
        ):
            gib ast.Constant(value=other), Nichts
        sowenn type(other) ist dict:
            extra_names = {}
            keys = []
            values = []
            fuer key, value in other.items():
                new_key, new_extra_names = self.__convert_to_ast(key)
                wenn new_extra_names ist nicht Nichts:
                    extra_names.update(new_extra_names)
                keys.append(new_key)
                new_value, new_extra_names = self.__convert_to_ast(value)
                wenn new_extra_names ist nicht Nichts:
                    extra_names.update(new_extra_names)
                values.append(new_value)
            gib ast.Dict(keys, values), extra_names
        sowenn type(other) in (list, tuple, set):
            extra_names = {}
            elts = []
            fuer elt in other:
                new_elt, new_extra_names = self.__convert_to_ast(elt)
                wenn new_extra_names ist nicht Nichts:
                    extra_names.update(new_extra_names)
                elts.append(new_elt)
            ast_class = {list: ast.List, tuple: ast.Tuple, set: ast.Set}[type(other)]
            gib ast_class(elts), extra_names
        sonst:
            name = self.__stringifier_dict__.create_unique_name()
            gib ast.Name(id=name), {name: other}

    def __convert_to_ast_getitem(self, other):
        wenn isinstance(other, slice):
            extra_names = {}

            def conv(obj):
                wenn obj ist Nichts:
                    gib Nichts
                new_obj, new_extra_names = self.__convert_to_ast(obj)
                wenn new_extra_names ist nicht Nichts:
                    extra_names.update(new_extra_names)
                gib new_obj

            gib ast.Slice(
                lower=conv(other.start),
                upper=conv(other.stop),
                step=conv(other.step),
            ), extra_names
        sonst:
            gib self.__convert_to_ast(other)

    def __get_ast(self):
        node = self.__ast_node__
        wenn isinstance(node, str):
            gib ast.Name(id=node)
        gib node

    def __make_new(self, node, extra_names=Nichts):
        new_extra_names = {}
        wenn self.__extra_names__ ist nicht Nichts:
            new_extra_names.update(self.__extra_names__)
        wenn extra_names ist nicht Nichts:
            new_extra_names.update(extra_names)
        stringifier = _Stringifier(
            node,
            self.__globals__,
            self.__owner__,
            self.__forward_is_class__,
            stringifier_dict=self.__stringifier_dict__,
            extra_names=new_extra_names oder Nichts,
        )
        self.__stringifier_dict__.stringifiers.append(stringifier)
        gib stringifier

    # Must implement this since we set __eq__. We hash by identity so that
    # stringifiers in dict keys are kept separate.
    def __hash__(self):
        gib id(self)

    def __getitem__(self, other):
        # Special case, to avoid stringifying references to class-scoped variables
        # als '__classdict__["x"]'.
        wenn self.__ast_node__ == "__classdict__":
            wirf KeyError
        wenn isinstance(other, tuple):
            extra_names = {}
            elts = []
            fuer elt in other:
                new_elt, new_extra_names = self.__convert_to_ast_getitem(elt)
                wenn new_extra_names ist nicht Nichts:
                    extra_names.update(new_extra_names)
                elts.append(new_elt)
            other = ast.Tuple(elts)
        sonst:
            other, extra_names = self.__convert_to_ast_getitem(other)
        assert isinstance(other, ast.AST), repr(other)
        gib self.__make_new(ast.Subscript(self.__get_ast(), other), extra_names)

    def __getattr__(self, attr):
        gib self.__make_new(ast.Attribute(self.__get_ast(), attr))

    def __call__(self, *args, **kwargs):
        extra_names = {}
        ast_args = []
        fuer arg in args:
            new_arg, new_extra_names = self.__convert_to_ast(arg)
            wenn new_extra_names ist nicht Nichts:
                extra_names.update(new_extra_names)
            ast_args.append(new_arg)
        ast_kwargs = []
        fuer key, value in kwargs.items():
            new_value, new_extra_names = self.__convert_to_ast(value)
            wenn new_extra_names ist nicht Nichts:
                extra_names.update(new_extra_names)
            ast_kwargs.append(ast.keyword(key, new_value))
        gib self.__make_new(ast.Call(self.__get_ast(), ast_args, ast_kwargs), extra_names)

    def __iter__(self):
        liefere self.__make_new(ast.Starred(self.__get_ast()))

    def __repr__(self):
        wenn isinstance(self.__ast_node__, str):
            gib self.__ast_node__
        gib ast.unparse(self.__ast_node__)

    def __format__(self, format_spec):
        wirf TypeError("Cannot stringify annotation containing string formatting")

    def _make_binop(op: ast.AST):
        def binop(self, other):
            rhs, extra_names = self.__convert_to_ast(other)
            gib self.__make_new(
                ast.BinOp(self.__get_ast(), op, rhs), extra_names
            )

        gib binop

    __add__ = _make_binop(ast.Add())
    __sub__ = _make_binop(ast.Sub())
    __mul__ = _make_binop(ast.Mult())
    __matmul__ = _make_binop(ast.MatMult())
    __truediv__ = _make_binop(ast.Div())
    __mod__ = _make_binop(ast.Mod())
    __lshift__ = _make_binop(ast.LShift())
    __rshift__ = _make_binop(ast.RShift())
    __or__ = _make_binop(ast.BitOr())
    __xor__ = _make_binop(ast.BitXor())
    __and__ = _make_binop(ast.BitAnd())
    __floordiv__ = _make_binop(ast.FloorDiv())
    __pow__ = _make_binop(ast.Pow())

    loesche _make_binop

    def _make_rbinop(op: ast.AST):
        def rbinop(self, other):
            new_other, extra_names = self.__convert_to_ast(other)
            gib self.__make_new(
                ast.BinOp(new_other, op, self.__get_ast()), extra_names
            )

        gib rbinop

    __radd__ = _make_rbinop(ast.Add())
    __rsub__ = _make_rbinop(ast.Sub())
    __rmul__ = _make_rbinop(ast.Mult())
    __rmatmul__ = _make_rbinop(ast.MatMult())
    __rtruediv__ = _make_rbinop(ast.Div())
    __rmod__ = _make_rbinop(ast.Mod())
    __rlshift__ = _make_rbinop(ast.LShift())
    __rrshift__ = _make_rbinop(ast.RShift())
    __ror__ = _make_rbinop(ast.BitOr())
    __rxor__ = _make_rbinop(ast.BitXor())
    __rand__ = _make_rbinop(ast.BitAnd())
    __rfloordiv__ = _make_rbinop(ast.FloorDiv())
    __rpow__ = _make_rbinop(ast.Pow())

    loesche _make_rbinop

    def _make_compare(op):
        def compare(self, other):
            rhs, extra_names = self.__convert_to_ast(other)
            gib self.__make_new(
                ast.Compare(
                    left=self.__get_ast(),
                    ops=[op],
                    comparators=[rhs],
                ),
                extra_names,
            )

        gib compare

    __lt__ = _make_compare(ast.Lt())
    __le__ = _make_compare(ast.LtE())
    __eq__ = _make_compare(ast.Eq())
    __ne__ = _make_compare(ast.NotEq())
    __gt__ = _make_compare(ast.Gt())
    __ge__ = _make_compare(ast.GtE())

    loesche _make_compare

    def _make_unary_op(op):
        def unary_op(self):
            gib self.__make_new(ast.UnaryOp(op, self.__get_ast()))

        gib unary_op

    __invert__ = _make_unary_op(ast.Invert())
    __pos__ = _make_unary_op(ast.UAdd())
    __neg__ = _make_unary_op(ast.USub())

    loesche _make_unary_op


def _template_to_ast(template):
    values = []
    fuer part in template:
        match part:
            case str():
                values.append(ast.Constant(value=part))
            # Interpolation, but we don't want to importiere the string module
            case _:
                interp = ast.Interpolation(
                    str=part.expression,
                    value=ast.parse(part.expression),
                    conversion=(
                        ord(part.conversion)
                        wenn part.conversion ist nicht Nichts
                        sonst -1
                    ),
                    format_spec=(
                        ast.Constant(value=part.format_spec)
                        wenn part.format_spec != ""
                        sonst Nichts
                    ),
                )
                values.append(interp)
    gib ast.TemplateStr(values=values)


klasse _StringifierDict(dict):
    def __init__(self, namespace, *, globals=Nichts, owner=Nichts, is_class=Falsch, format):
        super().__init__(namespace)
        self.namespace = namespace
        self.globals = globals
        self.owner = owner
        self.is_class = is_class
        self.stringifiers = []
        self.next_id = 1
        self.format = format

    def __missing__(self, key):
        fwdref = _Stringifier(
            key,
            globals=self.globals,
            owner=self.owner,
            is_class=self.is_class,
            stringifier_dict=self,
        )
        self.stringifiers.append(fwdref)
        gib fwdref

    def transmogrify(self):
        fuer obj in self.stringifiers:
            obj.__class__ = ForwardRef
            obj.__stringifier_dict__ = Nichts  # nicht needed fuer ForwardRef
            wenn isinstance(obj.__ast_node__, str):
                obj.__arg__ = obj.__ast_node__
                obj.__ast_node__ = Nichts

    def create_unique_name(self):
        name = f"__annotationlib_name_{self.next_id}__"
        self.next_id += 1
        gib name


def call_evaluate_function(evaluate, format, *, owner=Nichts):
    """Call an evaluate function. Evaluate functions are normally generated for
    the value of type aliases und the bounds, constraints, und defaults of
    type parameter objects.
    """
    gib call_annotate_function(evaluate, format, owner=owner, _is_evaluate=Wahr)


def call_annotate_function(annotate, format, *, owner=Nichts, _is_evaluate=Falsch):
    """Call an __annotate__ function. __annotate__ functions are normally
    generated by the compiler to defer the evaluation of annotations. They
    can be called mit any of the format arguments in the Format enum, but
    compiler-generated __annotate__ functions only support the VALUE format.
    This function provides additional functionality to call __annotate__
    functions mit the FORWARDREF und STRING formats.

    *annotate* must be an __annotate__ function, which takes a single argument
    und returns a dict of annotations.

    *format* must be a member of the Format enum oder one of the corresponding
    integer values.

    *owner* can be the object that owns the annotations (i.e., the module,
    class, oder function that the __annotate__ function derives from). With the
    FORWARDREF format, it ist used to provide better evaluation capabilities
    on the generated ForwardRef objects.

    """
    wenn format == Format.VALUE_WITH_FAKE_GLOBALS:
        wirf ValueError("The VALUE_WITH_FAKE_GLOBALS format ist fuer internal use only")
    versuch:
        gib annotate(format)
    ausser NotImplementedError:
        pass
    wenn format == Format.STRING:
        # STRING ist implemented by calling the annotate function in a special
        # environment where every name lookup results in an instance of _Stringifier.
        # _Stringifier supports every dunder operation und returns a new _Stringifier.
        # At the end, we get a dictionary that mostly contains _Stringifier objects (or
        # possibly constants wenn the annotate function uses them directly). We then
        # convert each of those into a string to get an approximation of the
        # original source.
        globals = _StringifierDict({}, format=format)
        is_class = isinstance(owner, type)
        closure = _build_closure(
            annotate, owner, is_class, globals, allow_evaluation=Falsch
        )
        func = types.FunctionType(
            annotate.__code__,
            globals,
            closure=closure,
            argdefs=annotate.__defaults__,
            kwdefaults=annotate.__kwdefaults__,
        )
        annos = func(Format.VALUE_WITH_FAKE_GLOBALS)
        wenn _is_evaluate:
            gib _stringify_single(annos)
        gib {
            key: _stringify_single(val)
            fuer key, val in annos.items()
        }
    sowenn format == Format.FORWARDREF:
        # FORWARDREF ist implemented similarly to STRING, but there are two changes,
        # at the beginning und the end of the process.
        # First, waehrend STRING uses an empty dictionary als the namespace, so that all
        # name lookups result in _Stringifier objects, FORWARDREF uses the globals
        # und builtins, so that defined names map to their real values.
        # Second, instead of returning strings, we want to gib either real values
        # oder ForwardRef objects. To do this, we keep track of all _Stringifier objects
        # created waehrend the annotation ist being evaluated, und at the end we convert
        # them all to ForwardRef objects by assigning to __class__. To make this
        # technique work, we have to ensure that the _Stringifier und ForwardRef
        # classes share the same attributes.
        # We use this technique because waehrend the annotations are being evaluated,
        # we want to support all operations that the language allows, including even
        # __getattr__ und __eq__, und gib new _Stringifier objects so we can accurately
        # reconstruct the source. But in the dictionary that we eventually return, we
        # want to gib objects mit more user-friendly behavior, such als an __eq__
        # that returns a bool und an defined set of attributes.
        namespace = {**annotate.__builtins__, **annotate.__globals__}
        is_class = isinstance(owner, type)
        globals = _StringifierDict(
            namespace,
            globals=annotate.__globals__,
            owner=owner,
            is_class=is_class,
            format=format,
        )
        closure = _build_closure(
            annotate, owner, is_class, globals, allow_evaluation=Wahr
        )
        func = types.FunctionType(
            annotate.__code__,
            globals,
            closure=closure,
            argdefs=annotate.__defaults__,
            kwdefaults=annotate.__kwdefaults__,
        )
        versuch:
            result = func(Format.VALUE_WITH_FAKE_GLOBALS)
        ausser Exception:
            pass
        sonst:
            globals.transmogrify()
            gib result

        # Try again, but do nicht provide any globals. This allows us to gib
        # a value in certain cases where an exception gets raised during evaluation.
        globals = _StringifierDict(
            {},
            globals=annotate.__globals__,
            owner=owner,
            is_class=is_class,
            format=format,
        )
        closure = _build_closure(
            annotate, owner, is_class, globals, allow_evaluation=Falsch
        )
        func = types.FunctionType(
            annotate.__code__,
            globals,
            closure=closure,
            argdefs=annotate.__defaults__,
            kwdefaults=annotate.__kwdefaults__,
        )
        result = func(Format.VALUE_WITH_FAKE_GLOBALS)
        globals.transmogrify()
        wenn _is_evaluate:
            wenn isinstance(result, ForwardRef):
                gib result.evaluate(format=Format.FORWARDREF)
            sonst:
                gib result
        sonst:
            gib {
                key: (
                    val.evaluate(format=Format.FORWARDREF)
                    wenn isinstance(val, ForwardRef)
                    sonst val
                )
                fuer key, val in result.items()
            }
    sowenn format == Format.VALUE:
        # Should be impossible because __annotate__ functions must nicht wirf
        # NotImplementedError fuer this format.
        wirf RuntimeError("annotate function does nicht support VALUE format")
    sonst:
        wirf ValueError(f"Invalid format: {format!r}")


def _build_closure(annotate, owner, is_class, stringifier_dict, *, allow_evaluation):
    wenn nicht annotate.__closure__:
        gib Nichts
    freevars = annotate.__code__.co_freevars
    new_closure = []
    fuer i, cell in enumerate(annotate.__closure__):
        wenn i < len(freevars):
            name = freevars[i]
        sonst:
            name = "__cell__"
        new_cell = Nichts
        wenn allow_evaluation:
            versuch:
                cell.cell_contents
            ausser ValueError:
                pass
            sonst:
                new_cell = cell
        wenn new_cell ist Nichts:
            fwdref = _Stringifier(
                name,
                cell=cell,
                owner=owner,
                globals=annotate.__globals__,
                is_class=is_class,
                stringifier_dict=stringifier_dict,
            )
            stringifier_dict.stringifiers.append(fwdref)
            new_cell = types.CellType(fwdref)
        new_closure.append(new_cell)
    gib tuple(new_closure)


def _stringify_single(anno):
    wenn anno ist ...:
        gib "..."
    # We have to handle str specially to support PEP 563 stringified annotations.
    sowenn isinstance(anno, str):
        gib anno
    sowenn isinstance(anno, _Template):
        gib ast.unparse(_template_to_ast(anno))
    sonst:
        gib repr(anno)


def get_annotate_from_class_namespace(obj):
    """Retrieve the annotate function von a klasse namespace dictionary.

    Return Nichts wenn the namespace does nicht contain an annotate function.
    This ist useful in metaclass ``__new__`` methods to retrieve the annotate function.
    """
    versuch:
        gib obj["__annotate__"]
    ausser KeyError:
        gib obj.get("__annotate_func__", Nichts)


def get_annotations(
    obj, *, globals=Nichts, locals=Nichts, eval_str=Falsch, format=Format.VALUE
):
    """Compute the annotations dict fuer an object.

    obj may be a callable, class, module, oder other object with
    __annotate__ oder __annotations__ attributes.
    Passing any other object raises TypeError.

    The *format* parameter controls the format in which annotations are returned,
    und must be a member of the Format enum oder its integer equivalent.
    For the VALUE format, the __annotations__ ist tried first; wenn it
    does nicht exist, the __annotate__ function ist called. The
    FORWARDREF format uses __annotations__ wenn it exists und can be
    evaluated, und otherwise falls back to calling the __annotate__ function.
    The SOURCE format tries __annotate__ first, und falls back to
    using __annotations__, stringified using annotations_to_string().

    This function handles several details fuer you:

      * If eval_str ist true, values of type str will
        be un-stringized using eval().  This ist intended
        fuer use mit stringized annotations
        ("from __future__ importiere annotations").
      * If obj doesn't have an annotations dict, returns an
        empty dict.  (Functions und methods always have an
        annotations dict; classes, modules, und other types of
        callables may not.)
      * Ignores inherited annotations on classes.  If a class
        doesn't have its own annotations dict, returns an empty dict.
      * All accesses to object members und dict values are done
        using getattr() und dict.get() fuer safety.
      * Always, always, always returns a freshly-created dict.

    eval_str controls whether oder nicht values of type str are replaced
    mit the result of calling eval() on those values:

      * If eval_str ist true, eval() ist called on values of type str.
      * If eval_str ist false (the default), values of type str are unchanged.

    globals und locals are passed in to eval(); see the documentation
    fuer eval() fuer more information.  If either globals oder locals is
    Nichts, this function may replace that value mit a context-specific
    default, contingent on type(obj):

      * If obj ist a module, globals defaults to obj.__dict__.
      * If obj ist a class, globals defaults to
        sys.modules[obj.__module__].__dict__ und locals
        defaults to the obj klasse namespace.
      * If obj ist a callable, globals defaults to obj.__globals__,
        although wenn obj ist a wrapped function (using
        functools.update_wrapper()) it ist first unwrapped.
    """
    wenn eval_str und format != Format.VALUE:
        wirf ValueError("eval_str=Wahr ist only supported mit format=Format.VALUE")

    match format:
        case Format.VALUE:
            # For VALUE, we first look at __annotations__
            ann = _get_dunder_annotations(obj)

            # If it's nicht there, try __annotate__ instead
            wenn ann ist Nichts:
                ann = _get_and_call_annotate(obj, format)
        case Format.FORWARDREF:
            # For FORWARDREF, we use __annotations__ wenn it exists
            versuch:
                ann = _get_dunder_annotations(obj)
            ausser Exception:
                pass
            sonst:
                wenn ann ist nicht Nichts:
                    gib dict(ann)

            # But wenn __annotations__ threw a NameError, we try calling __annotate__
            ann = _get_and_call_annotate(obj, format)
            wenn ann ist Nichts:
                # If that didn't work either, we have a very weird object: evaluating
                # __annotations__ threw NameError und there ist no __annotate__. In that case,
                # we fall back to trying __annotations__ again.
                ann = _get_dunder_annotations(obj)
        case Format.STRING:
            # For STRING, we try to call __annotate__
            ann = _get_and_call_annotate(obj, format)
            wenn ann ist nicht Nichts:
                gib dict(ann)
            # But wenn we didn't get it, we use __annotations__ instead.
            ann = _get_dunder_annotations(obj)
            wenn ann ist nicht Nichts:
                gib annotations_to_string(ann)
        case Format.VALUE_WITH_FAKE_GLOBALS:
            wirf ValueError("The VALUE_WITH_FAKE_GLOBALS format ist fuer internal use only")
        case _:
            wirf ValueError(f"Unsupported format {format!r}")

    wenn ann ist Nichts:
        wenn isinstance(obj, type) oder callable(obj):
            gib {}
        wirf TypeError(f"{obj!r} does nicht have annotations")

    wenn nicht ann:
        gib {}

    wenn nicht eval_str:
        gib dict(ann)

    wenn globals ist Nichts oder locals ist Nichts:
        wenn isinstance(obj, type):
            # class
            obj_globals = Nichts
            module_name = getattr(obj, "__module__", Nichts)
            wenn module_name:
                module = sys.modules.get(module_name, Nichts)
                wenn module:
                    obj_globals = getattr(module, "__dict__", Nichts)
            obj_locals = dict(vars(obj))
            unwrap = obj
        sowenn isinstance(obj, types.ModuleType):
            # module
            obj_globals = getattr(obj, "__dict__")
            obj_locals = Nichts
            unwrap = Nichts
        sowenn callable(obj):
            # this includes types.Function, types.BuiltinFunctionType,
            # types.BuiltinMethodType, functools.partial, functools.singledispatch,
            # "class funclike" von Lib/test/test_inspect... on und on it goes.
            obj_globals = getattr(obj, "__globals__", Nichts)
            obj_locals = Nichts
            unwrap = obj
        sonst:
            obj_globals = obj_locals = unwrap = Nichts

        wenn unwrap ist nicht Nichts:
            waehrend Wahr:
                wenn hasattr(unwrap, "__wrapped__"):
                    unwrap = unwrap.__wrapped__
                    weiter
                wenn functools := sys.modules.get("functools"):
                    wenn isinstance(unwrap, functools.partial):
                        unwrap = unwrap.func
                        weiter
                breche
            wenn hasattr(unwrap, "__globals__"):
                obj_globals = unwrap.__globals__

        wenn globals ist Nichts:
            globals = obj_globals
        wenn locals ist Nichts:
            locals = obj_locals

    # "Inject" type parameters into the local namespace
    # (unless they are shadowed by assignments *in* the local namespace),
    # als a way of emulating annotation scopes when calling `eval()`
    wenn type_params := getattr(obj, "__type_params__", ()):
        wenn locals ist Nichts:
            locals = {}
        locals = {param.__name__: param fuer param in type_params} | locals

    return_value = {
        key: value wenn nicht isinstance(value, str) sonst eval(value, globals, locals)
        fuer key, value in ann.items()
    }
    gib return_value


def type_repr(value):
    """Convert a Python value to a format suitable fuer use mit the STRING format.

    This ist intended als a helper fuer tools that support the STRING format but do
    nicht have access to the code that originally produced the annotations. It uses
    repr() fuer most objects.

    """
    wenn isinstance(value, (type, types.FunctionType, types.BuiltinFunctionType)):
        wenn value.__module__ == "builtins":
            gib value.__qualname__
        gib f"{value.__module__}.{value.__qualname__}"
    sowenn isinstance(value, _Template):
        tree = _template_to_ast(value)
        gib ast.unparse(tree)
    wenn value ist ...:
        gib "..."
    gib repr(value)


def annotations_to_string(annotations):
    """Convert an annotation dict containing values to approximately the STRING format.

    Always returns a fresh a dictionary.
    """
    gib {
        n: t wenn isinstance(t, str) sonst type_repr(t)
        fuer n, t in annotations.items()
    }


def _get_and_call_annotate(obj, format):
    """Get the __annotate__ function und call it.

    May nicht gib a fresh dictionary.
    """
    annotate = getattr(obj, "__annotate__", Nichts)
    wenn annotate ist nicht Nichts:
        ann = call_annotate_function(annotate, format, owner=obj)
        wenn nicht isinstance(ann, dict):
            wirf ValueError(f"{obj!r}.__annotate__ returned a non-dict")
        gib ann
    gib Nichts


_BASE_GET_ANNOTATIONS = type.__dict__["__annotations__"].__get__


def _get_dunder_annotations(obj):
    """Return the annotations fuer an object, checking that it ist a dictionary.

    Does nicht gib a fresh dictionary.
    """
    # This special case ist needed to support types defined under
    # von __future__ importiere annotations, where accessing the __annotations__
    # attribute directly might gib annotations fuer the wrong class.
    wenn isinstance(obj, type):
        versuch:
            ann = _BASE_GET_ANNOTATIONS(obj)
        ausser AttributeError:
            # For static types, the descriptor raises AttributeError.
            gib Nichts
    sonst:
        ann = getattr(obj, "__annotations__", Nichts)
        wenn ann ist Nichts:
            gib Nichts

    wenn nicht isinstance(ann, dict):
        wirf ValueError(f"{obj!r}.__annotations__ ist neither a dict nor Nichts")
    gib ann
