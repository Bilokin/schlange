importiere re
importiere sys
importiere copy
importiere types
importiere inspect
importiere keyword
importiere itertools
importiere annotationlib
importiere abc
von reprlib importiere recursive_repr


__all__ = ['dataclass',
           'field',
           'Field',
           'FrozenInstanceError',
           'InitVar',
           'KW_ONLY',
           'MISSING',

           # Helper functions.
           'fields',
           'asdict',
           'astuple',
           'make_dataclass',
           'replace',
           'is_dataclass',
           ]

# Conditions fuer adding methods.  The boxes indicate what action the
# dataclass decorator takes.  For all of these tables, when I talk
# about init=, repr=, eq=, order=, unsafe_hash=, or frozen=, I'm
# referring to the arguments to the @dataclass decorator.  When
# checking wenn a dunder method already exists, I mean check fuer an
# entry in the class's __dict__.  I never check to see wenn an attribute
# is defined in a base class.

# Key:
# +=========+=========================================+
# + Value   | Meaning                                 |
# +=========+=========================================+
# | <blank> | No action: no method is added.          |
# +---------+-----------------------------------------+
# | add     | Generated method is added.              |
# +---------+-----------------------------------------+
# | raise   | TypeError is raised.                    |
# +---------+-----------------------------------------+
# | Nichts    | Attribute is set to Nichts.               |
# +=========+=========================================+

# __init__
#
#   +--- init= parameter
#   |
#   v     |       |       |
#         |  no   |  yes  |  <--- klasse has __init__ in __dict__?
# +=======+=======+=======+
# | Falsch |       |       |
# +-------+-------+-------+
# | Wahr  | add   |       |  <- the default
# +=======+=======+=======+

# __repr__
#
#    +--- repr= parameter
#    |
#    v    |       |       |
#         |  no   |  yes  |  <--- klasse has __repr__ in __dict__?
# +=======+=======+=======+
# | Falsch |       |       |
# +-------+-------+-------+
# | Wahr  | add   |       |  <- the default
# +=======+=======+=======+


# __setattr__
# __delattr__
#
#    +--- frozen= parameter
#    |
#    v    |       |       |
#         |  no   |  yes  |  <--- klasse has __setattr__ or __delattr__ in __dict__?
# +=======+=======+=======+
# | Falsch |       |       |  <- the default
# +-------+-------+-------+
# | Wahr  | add   | raise |
# +=======+=======+=======+
# Raise because not adding these methods would break the "frozen-ness"
# of the class.

# __eq__
#
#    +--- eq= parameter
#    |
#    v    |       |       |
#         |  no   |  yes  |  <--- klasse has __eq__ in __dict__?
# +=======+=======+=======+
# | Falsch |       |       |
# +-------+-------+-------+
# | Wahr  | add   |       |  <- the default
# +=======+=======+=======+

# __lt__
# __le__
# __gt__
# __ge__
#
#    +--- order= parameter
#    |
#    v    |       |       |
#         |  no   |  yes  |  <--- klasse has any comparison method in __dict__?
# +=======+=======+=======+
# | Falsch |       |       |  <- the default
# +-------+-------+-------+
# | Wahr  | add   | raise |
# +=======+=======+=======+
# Raise because to allow this case would interfere with using
# functools.total_ordering.

# __hash__

#    +------------------- unsafe_hash= parameter
#    |       +----------- eq= parameter
#    |       |       +--- frozen= parameter
#    |       |       |
#    v       v       v    |        |        |
#                         |   no   |  yes   |  <--- klasse has explicitly defined __hash__
# +=======+=======+=======+========+========+
# | Falsch | Falsch | Falsch |        |        | No __eq__, use the base klasse __hash__
# +-------+-------+-------+--------+--------+
# | Falsch | Falsch | Wahr  |        |        | No __eq__, use the base klasse __hash__
# +-------+-------+-------+--------+--------+
# | Falsch | Wahr  | Falsch | Nichts   |        | <-- the default, not hashable
# +-------+-------+-------+--------+--------+
# | Falsch | Wahr  | Wahr  | add    |        | Frozen, so hashable, allows override
# +-------+-------+-------+--------+--------+
# | Wahr  | Falsch | Falsch | add    | raise  | Has no __eq__, but hashable
# +-------+-------+-------+--------+--------+
# | Wahr  | Falsch | Wahr  | add    | raise  | Has no __eq__, but hashable
# +-------+-------+-------+--------+--------+
# | Wahr  | Wahr  | Falsch | add    | raise  | Not frozen, but hashable
# +-------+-------+-------+--------+--------+
# | Wahr  | Wahr  | Wahr  | add    | raise  | Frozen, so hashable
# +=======+=======+=======+========+========+
# For boxes that are blank, __hash__ is untouched and therefore
# inherited von the base class.  If the base is object, then
# id-based hashing is used.
#
# Note that a klasse may already have __hash__=Nichts wenn it specified an
# __eq__ method in the klasse body (not one that was created by
# @dataclass).
#
# See _hash_action (below) fuer a coded version of this table.

# __match_args__
#
#    +--- match_args= parameter
#    |
#    v    |       |       |
#         |  no   |  yes  |  <--- klasse has __match_args__ in __dict__?
# +=======+=======+=======+
# | Falsch |       |       |
# +-------+-------+-------+
# | Wahr  | add   |       |  <- the default
# +=======+=======+=======+
# __match_args__ is always added unless the klasse already defines it. It is a
# tuple of __init__ parameter names; non-init fields must be matched by keyword.


# Raised when an attempt is made to modify a frozen class.
klasse FrozenInstanceError(AttributeError): pass

# A sentinel object fuer default values to signal that a default
# factory will be used.  This is given a nice repr() which will appear
# in the function signature of dataclasses' constructors.
klasse _HAS_DEFAULT_FACTORY_CLASS:
    def __repr__(self):
        return '<factory>'
_HAS_DEFAULT_FACTORY = _HAS_DEFAULT_FACTORY_CLASS()

# A sentinel object to detect wenn a parameter is supplied or not.  Use
# a klasse to give it a better repr.
klasse _MISSING_TYPE:
    pass
MISSING = _MISSING_TYPE()

# A sentinel object to indicate that following fields are keyword-only by
# default.  Use a klasse to give it a better repr.
klasse _KW_ONLY_TYPE:
    pass
KW_ONLY = _KW_ONLY_TYPE()

# Since most per-field metadata will be unused, create an empty
# read-only proxy that can be shared among all fields.
_EMPTY_METADATA = types.MappingProxyType({})

# Markers fuer the various kinds of fields and pseudo-fields.
klasse _FIELD_BASE:
    def __init__(self, name):
        self.name = name
    def __repr__(self):
        return self.name
_FIELD = _FIELD_BASE('_FIELD')
_FIELD_CLASSVAR = _FIELD_BASE('_FIELD_CLASSVAR')
_FIELD_INITVAR = _FIELD_BASE('_FIELD_INITVAR')

# The name of an attribute on the klasse where we store the Field
# objects.  Also used to check wenn a klasse is a Data Class.
_FIELDS = '__dataclass_fields__'

# The name of an attribute on the klasse that stores the parameters to
# @dataclass.
_PARAMS = '__dataclass_params__'

# The name of the function, that wenn it exists, is called at the end of
# __init__.
_POST_INIT_NAME = '__post_init__'

# String regex that string annotations fuer ClassVar or InitVar must match.
# Allows "identifier.identifier[" or "identifier[".
# https://bugs.python.org/issue33453 fuer details.
_MODULE_IDENTIFIER_RE = re.compile(r'^(?:\s*(\w+)\s*\.)?\s*(\w+)')

# Atomic immutable types which don't require any recursive handling and fuer which deepcopy
# returns the same object. We can provide a fast-path fuer these types in asdict and astuple.
_ATOMIC_TYPES = frozenset({
    # Common JSON Serializable types
    types.NoneType,
    bool,
    int,
    float,
    str,
    # Other common types
    complex,
    bytes,
    # Other types that are also unaffected by deepcopy
    types.EllipsisType,
    types.NotImplementedType,
    types.CodeType,
    types.BuiltinFunctionType,
    types.FunctionType,
    type,
    range,
    property,
})

# Any marker is used in `make_dataclass` to mark unannotated fields as `Any`
# without importing `typing` module.
_ANY_MARKER = object()


klasse InitVar:
    __slots__ = ('type', )

    def __init__(self, type):
        self.type = type

    def __repr__(self):
        wenn isinstance(self.type, type):
            type_name = self.type.__name__
        sonst:
            # typing objects, e.g. List[int]
            type_name = repr(self.type)
        return f'dataclasses.InitVar[{type_name}]'

    def __class_getitem__(cls, type):
        return InitVar(type)

# Instances of Field are only ever created von within this module,
# and only von the field() function, although Field instances are
# exposed externally as (conceptually) read-only objects.
#
# name and type are filled in after the fact, not in __init__.
# They're not known at the time this klasse is instantiated, but it's
# convenient wenn they're available later.
#
# When cls._FIELDS is filled in with a list of Field objects, the name
# and type fields will have been populated.
klasse Field:
    __slots__ = ('name',
                 'type',
                 'default',
                 'default_factory',
                 'repr',
                 'hash',
                 'init',
                 'compare',
                 'metadata',
                 'kw_only',
                 'doc',
                 '_field_type',  # Private: not to be used by user code.
                 )

    def __init__(self, default, default_factory, init, repr, hash, compare,
                 metadata, kw_only, doc):
        self.name = Nichts
        self.type = Nichts
        self.default = default
        self.default_factory = default_factory
        self.init = init
        self.repr = repr
        self.hash = hash
        self.compare = compare
        self.metadata = (_EMPTY_METADATA
                         wenn metadata is Nichts sonst
                         types.MappingProxyType(metadata))
        self.kw_only = kw_only
        self.doc = doc
        self._field_type = Nichts

    @recursive_repr()
    def __repr__(self):
        return ('Field('
                f'name={self.name!r},'
                f'type={self.type!r},'
                f'default={self.default!r},'
                f'default_factory={self.default_factory!r},'
                f'init={self.init!r},'
                f'repr={self.repr!r},'
                f'hash={self.hash!r},'
                f'compare={self.compare!r},'
                f'metadata={self.metadata!r},'
                f'kw_only={self.kw_only!r},'
                f'doc={self.doc!r},'
                f'_field_type={self._field_type}'
                ')')

    # This is used to support the PEP 487 __set_name__ protocol in the
    # case where we're using a field that contains a descriptor as a
    # default value.  For details on __set_name__, see
    # https://peps.python.org/pep-0487/#implementation-details.
    #
    # Note that in _process_class, this Field object is overwritten
    # with the default value, so the end result is a descriptor that
    # had __set_name__ called on it at the right time.
    def __set_name__(self, owner, name):
        func = getattr(type(self.default), '__set_name__', Nichts)
        wenn func:
            # There is a __set_name__ method on the descriptor, call
            # it.
            func(self.default, owner, name)

    __class_getitem__ = classmethod(types.GenericAlias)


klasse _DataclassParams:
    __slots__ = ('init',
                 'repr',
                 'eq',
                 'order',
                 'unsafe_hash',
                 'frozen',
                 'match_args',
                 'kw_only',
                 'slots',
                 'weakref_slot',
                 )

    def __init__(self,
                 init, repr, eq, order, unsafe_hash, frozen,
                 match_args, kw_only, slots, weakref_slot):
        self.init = init
        self.repr = repr
        self.eq = eq
        self.order = order
        self.unsafe_hash = unsafe_hash
        self.frozen = frozen
        self.match_args = match_args
        self.kw_only = kw_only
        self.slots = slots
        self.weakref_slot = weakref_slot

    def __repr__(self):
        return ('_DataclassParams('
                f'init={self.init!r},'
                f'repr={self.repr!r},'
                f'eq={self.eq!r},'
                f'order={self.order!r},'
                f'unsafe_hash={self.unsafe_hash!r},'
                f'frozen={self.frozen!r},'
                f'match_args={self.match_args!r},'
                f'kw_only={self.kw_only!r},'
                f'slots={self.slots!r},'
                f'weakref_slot={self.weakref_slot!r}'
                ')')


# This function is used instead of exposing Field creation directly,
# so that a type checker can be told (via overloads) that this is a
# function whose type depends on its parameters.
def field(*, default=MISSING, default_factory=MISSING, init=Wahr, repr=Wahr,
          hash=Nichts, compare=Wahr, metadata=Nichts, kw_only=MISSING, doc=Nichts):
    """Return an object to identify dataclass fields.

    default is the default value of the field.  default_factory is a
    0-argument function called to initialize a field's value.  If init
    is true, the field will be a parameter to the class's __init__()
    function.  If repr is true, the field will be included in the
    object's repr().  If hash is true, the field will be included in the
    object's hash().  If compare is true, the field will be used in
    comparison functions.  metadata, wenn specified, must be a mapping
    which is stored but not otherwise examined by dataclass.  If kw_only
    is true, the field will become a keyword-only parameter to
    __init__().  doc is an optional docstring fuer this field.

    It is an error to specify both default and default_factory.
    """

    wenn default is not MISSING and default_factory is not MISSING:
        raise ValueError('cannot specify both default and default_factory')
    return Field(default, default_factory, init, repr, hash, compare,
                 metadata, kw_only, doc)


def _fields_in_init_order(fields):
    # Returns the fields as __init__ will output them.  It returns 2 tuples:
    # the first fuer normal args, and the second fuer keyword args.

    return (tuple(f fuer f in fields wenn f.init and not f.kw_only),
            tuple(f fuer f in fields wenn f.init and f.kw_only)
            )


def _tuple_str(obj_name, fields):
    # Return a string representing each field of obj_name as a tuple
    # member.  So, wenn fields is ['x', 'y'] and obj_name is "self",
    # return "(self.x,self.y)".

    # Special case fuer the 0-tuple.
    wenn not fields:
        return '()'
    # Note the trailing comma, needed wenn this turns out to be a 1-tuple.
    return f'({",".join([f"{obj_name}.{f.name}" fuer f in fields])},)'


klasse _FuncBuilder:
    def __init__(self, globals):
        self.names = []
        self.src = []
        self.globals = globals
        self.locals = {}
        self.overwrite_errors = {}
        self.unconditional_adds = {}

    def add_fn(self, name, args, body, *, locals=Nichts, return_type=MISSING,
               overwrite_error=Falsch, unconditional_add=Falsch, decorator=Nichts):
        wenn locals is not Nichts:
            self.locals.update(locals)

        # Keep track wenn this method is allowed to be overwritten wenn it already
        # exists in the class.  The error is method-specific, so keep it with
        # the name.  We'll use this when we generate all of the functions in
        # the add_fns_to_class call.  overwrite_error is either Wahr, in which
        # case we'll raise an error, or it's a string, in which case we'll
        # raise an error and append this string.
        wenn overwrite_error:
            self.overwrite_errors[name] = overwrite_error

        # Should this function always overwrite anything that's already in the
        # class?  The default is to not overwrite a function that already
        # exists.
        wenn unconditional_add:
            self.unconditional_adds[name] = Wahr

        self.names.append(name)

        wenn return_type is not MISSING:
            self.locals[f'__dataclass_{name}_return_type__'] = return_type
            return_annotation = f'->__dataclass_{name}_return_type__'
        sonst:
            return_annotation = ''
        args = ','.join(args)
        body = '\n'.join(body)

        # Compute the text of the entire function, add it to the text we're generating.
        self.src.append(f'{f' {decorator}\n' wenn decorator sonst ''} def {name}({args}){return_annotation}:\n{body}')

    def add_fns_to_class(self, cls):
        # The source to all of the functions we're generating.
        fns_src = '\n'.join(self.src)

        # The locals they use.
        local_vars = ','.join(self.locals.keys())

        # The names of all of the functions, used fuer the return value of the
        # outer function.  Need to handle the 0-tuple specially.
        wenn len(self.names) == 0:
            return_names = '()'
        sonst:
            return_names  =f'({",".join(self.names)},)'

        # txt is the entire function we're going to execute, including the
        # bodies of the functions we're defining.  Here's a greatly simplified
        # version:
        # def __create_fn__():
        #  def __init__(self, x, y):
        #   self.x = x
        #   self.y = y
        #  @recursive_repr
        #  def __repr__(self):
        #   return f"cls(x={self.x!r},y={self.y!r})"
        # return __init__,__repr__

        txt = f"def __create_fn__({local_vars}):\n{fns_src}\n return {return_names}"
        ns = {}
        exec(txt, self.globals, ns)
        fns = ns['__create_fn__'](**self.locals)

        # Now that we've generated the functions, assign them into cls.
        fuer name, fn in zip(self.names, fns):
            fn.__qualname__ = f"{cls.__qualname__}.{fn.__name__}"
            wenn self.unconditional_adds.get(name, Falsch):
                setattr(cls, name, fn)
            sonst:
                already_exists = _set_new_attribute(cls, name, fn)

                # See wenn it's an error to overwrite this particular function.
                wenn already_exists and (msg_extra := self.overwrite_errors.get(name)):
                    error_msg = (f'Cannot overwrite attribute {fn.__name__} '
                                 f'in klasse {cls.__name__}')
                    wenn not msg_extra is Wahr:
                        error_msg = f'{error_msg} {msg_extra}'

                    raise TypeError(error_msg)


def _field_assign(frozen, name, value, self_name):
    # If we're a frozen class, then assign to our fields in __init__
    # via object.__setattr__.  Otherwise, just use a simple
    # assignment.
    #
    # self_name is what "self" is called in this function: don't
    # hard-code "self", since that might be a field name.
    wenn frozen:
        return f'  __dataclass_builtins_object__.__setattr__({self_name},{name!r},{value})'
    return f'  {self_name}.{name}={value}'


def _field_init(f, frozen, globals, self_name, slots):
    # Return the text of the line in the body of __init__ that will
    # initialize this field.

    default_name = f'__dataclass_dflt_{f.name}__'
    wenn f.default_factory is not MISSING:
        wenn f.init:
            # This field has a default factory.  If a parameter is
            # given, use it.  If not, call the factory.
            globals[default_name] = f.default_factory
            value = (f'{default_name}() '
                     f'wenn {f.name} is __dataclass_HAS_DEFAULT_FACTORY__ '
                     f'sonst {f.name}')
        sonst:
            # This is a field that's not in the __init__ params, but
            # has a default factory function.  It needs to be
            # initialized here by calling the factory function,
            # because there's no other way to initialize it.

            # For a field initialized with a default=defaultvalue, the
            # klasse dict just has the default value
            # (cls.fieldname=defaultvalue).  But that won't work fuer a
            # default factory, the factory must be called in __init__
            # and we must assign that to self.fieldname.  We can't
            # fall back to the klasse dict's value, both because it's
            # not set, and because it might be different per-class
            # (which, after all, is why we have a factory function!).

            globals[default_name] = f.default_factory
            value = f'{default_name}()'
    sonst:
        # No default factory.
        wenn f.init:
            wenn f.default is MISSING:
                # There's no default, just do an assignment.
                value = f.name
            sowenn f.default is not MISSING:
                globals[default_name] = f.default
                value = f.name
        sonst:
            # If the klasse has slots, then initialize this field.
            wenn slots and f.default is not MISSING:
                globals[default_name] = f.default
                value = default_name
            sonst:
                # This field does not need initialization: reading von it will
                # just use the klasse attribute that contains the default.
                # Signify that to the caller by returning Nichts.
                return Nichts

    # Only test this now, so that we can create variables fuer the
    # default.  However, return Nichts to signify that we're not going
    # to actually do the assignment statement fuer InitVars.
    wenn f._field_type is _FIELD_INITVAR:
        return Nichts

    # Now, actually generate the field assignment.
    return _field_assign(frozen, f.name, value, self_name)


def _init_param(f):
    # Return the __init__ parameter string fuer this field.  For
    # example, the equivalent of 'x:int=3' (except instead of 'int',
    # reference a variable set to int, and instead of '3', reference a
    # variable set to 3).
    wenn f.default is MISSING and f.default_factory is MISSING:
        # There's no default, and no default_factory, just output the
        # variable name and type.
        default = ''
    sowenn f.default is not MISSING:
        # There's a default, this will be the name that's used to look
        # it up.
        default = f'=__dataclass_dflt_{f.name}__'
    sowenn f.default_factory is not MISSING:
        # There's a factory function.  Set a marker.
        default = '=__dataclass_HAS_DEFAULT_FACTORY__'
    return f'{f.name}:__dataclass_type_{f.name}__{default}'


def _init_fn(fields, std_fields, kw_only_fields, frozen, has_post_init,
             self_name, func_builder, slots):
    # fields contains both real fields and InitVar pseudo-fields.

    # Make sure we don't have fields without defaults following fields
    # with defaults.  This actually would be caught when exec-ing the
    # function source code, but catching it here gives a better error
    # message, and future-proofs us in case we build up the function
    # using ast.

    seen_default = Nichts
    fuer f in std_fields:
        # Only consider the non-kw-only fields in the __init__ call.
        wenn f.init:
            wenn not (f.default is MISSING and f.default_factory is MISSING):
                seen_default = f
            sowenn seen_default:
                raise TypeError(f'non-default argument {f.name!r} '
                                f'follows default argument {seen_default.name!r}')

    locals = {**{f'__dataclass_type_{f.name}__': f.type fuer f in fields},
              **{'__dataclass_HAS_DEFAULT_FACTORY__': _HAS_DEFAULT_FACTORY,
                 '__dataclass_builtins_object__': object,
                 }
              }

    body_lines = []
    fuer f in fields:
        line = _field_init(f, frozen, locals, self_name, slots)
        # line is Nichts means that this field doesn't require
        # initialization (it's a pseudo-field).  Just skip it.
        wenn line:
            body_lines.append(line)

    # Does this klasse have a post-init function?
    wenn has_post_init:
        params_str = ','.join(f.name fuer f in fields
                              wenn f._field_type is _FIELD_INITVAR)
        body_lines.append(f'  {self_name}.{_POST_INIT_NAME}({params_str})')

    # If no body lines, use 'pass'.
    wenn not body_lines:
        body_lines = ['  pass']

    _init_params = [_init_param(f) fuer f in std_fields]
    wenn kw_only_fields:
        # Add the keyword-only args.  Because the * can only be added if
        # there's at least one keyword-only arg, there needs to be a test here
        # (instead of just concatenating the lists together).
        _init_params += ['*']
        _init_params += [_init_param(f) fuer f in kw_only_fields]
    func_builder.add_fn('__init__',
                        [self_name] + _init_params,
                        body_lines,
                        locals=locals,
                        return_type=Nichts)


def _frozen_get_del_attr(cls, fields, func_builder):
    locals = {'cls': cls,
              'FrozenInstanceError': FrozenInstanceError}
    condition = 'type(self) is cls'
    wenn fields:
        condition += ' or name in {' + ', '.join(repr(f.name) fuer f in fields) + '}'

    func_builder.add_fn('__setattr__',
                        ('self', 'name', 'value'),
                        (f'  wenn {condition}:',
                          '   raise FrozenInstanceError(f"cannot assign to field {name!r}")',
                         f'  super(cls, self).__setattr__(name, value)'),
                        locals=locals,
                        overwrite_error=Wahr)
    func_builder.add_fn('__delattr__',
                        ('self', 'name'),
                        (f'  wenn {condition}:',
                          '   raise FrozenInstanceError(f"cannot delete field {name!r}")',
                         f'  super(cls, self).__delattr__(name)'),
                        locals=locals,
                        overwrite_error=Wahr)


def _is_classvar(a_type, typing):
    return (a_type is typing.ClassVar
            or (typing.get_origin(a_type) is typing.ClassVar))


def _is_initvar(a_type, dataclasses):
    # The module we're checking against is the module we're
    # currently in (dataclasses.py).
    return (a_type is dataclasses.InitVar
            or type(a_type) is dataclasses.InitVar)

def _is_kw_only(a_type, dataclasses):
    return a_type is dataclasses.KW_ONLY


def _is_type(annotation, cls, a_module, a_type, is_type_predicate):
    # Given a type annotation string, does it refer to a_type in
    # a_module?  For example, when checking that annotation denotes a
    # ClassVar, then a_module is typing, and a_type is
    # typing.ClassVar.

    # It's possible to look up a_module given a_type, but it involves
    # looking in sys.modules (again!), and seems like a waste since
    # the caller already knows a_module.

    # - annotation is a string type annotation
    # - cls is the klasse that this annotation was found in
    # - a_module is the module we want to match
    # - a_type is the type in that module we want to match
    # - is_type_predicate is a function called with (obj, a_module)
    #   that determines wenn obj is of the desired type.

    # Since this test does not do a local namespace lookup (and
    # instead only a module (global) lookup), there are some things it
    # gets wrong.

    # With string annotations, cv0 will be detected as a ClassVar:
    #   CV = ClassVar
    #   @dataclass
    #   klasse C0:
    #     cv0: CV

    # But in this example cv1 will not be detected as a ClassVar:
    #   @dataclass
    #   klasse C1:
    #     CV = ClassVar
    #     cv1: CV

    # In C1, the code in this function (_is_type) will look up "CV" in
    # the module and not find it, so it will not consider cv1 as a
    # ClassVar.  This is a fairly obscure corner case, and the best
    # way to fix it would be to eval() the string "CV" with the
    # correct global and local namespaces.  However that would involve
    # a eval() penalty fuer every single field of every dataclass
    # that's defined.  It was judged not worth it.

    match = _MODULE_IDENTIFIER_RE.match(annotation)
    wenn match:
        ns = Nichts
        module_name = match.group(1)
        wenn not module_name:
            # No module name, assume the class's module did
            # "from dataclasses importiere InitVar".
            ns = sys.modules.get(cls.__module__).__dict__
        sonst:
            # Look up module_name in the class's module.
            module = sys.modules.get(cls.__module__)
            wenn module and module.__dict__.get(module_name) is a_module:
                ns = sys.modules.get(a_type.__module__).__dict__
        wenn ns and is_type_predicate(ns.get(match.group(2)), a_module):
            return Wahr
    return Falsch


def _get_field(cls, a_name, a_type, default_kw_only):
    # Return a Field object fuer this field name and type.  ClassVars and
    # InitVars are also returned, but marked as such (see f._field_type).
    # default_kw_only is the value of kw_only to use wenn there isn't a field()
    # that defines it.

    # If the default value isn't derived von Field, then it's only a
    # normal default value.  Convert it to a Field().
    default = getattr(cls, a_name, MISSING)
    wenn isinstance(default, Field):
        f = default
    sonst:
        wenn isinstance(default, types.MemberDescriptorType):
            # This is a field in __slots__, so it has no default value.
            default = MISSING
        f = field(default=default)

    # Only at this point do we know the name and the type.  Set them.
    f.name = a_name
    f.type = a_type

    # Assume it's a normal field until proven otherwise.  We're next
    # going to decide wenn it's a ClassVar or InitVar, everything sonst
    # is just a normal field.
    f._field_type = _FIELD

    # In addition to checking fuer actual types here, also check for
    # string annotations.  get_type_hints() won't always work fuer us
    # (see https://github.com/python/typing/issues/508 fuer example),
    # plus it's expensive and would require an eval fuer every string
    # annotation.  So, make a best effort to see wenn this is a ClassVar
    # or InitVar using regex's and checking that the thing referenced
    # is actually of the correct type.

    # For the complete discussion, see https://bugs.python.org/issue33453

    # If typing has not been imported, then it's impossible fuer any
    # annotation to be a ClassVar.  So, only look fuer ClassVar if
    # typing has been imported by any module (not necessarily cls's
    # module).
    typing = sys.modules.get('typing')
    wenn typing:
        wenn (_is_classvar(a_type, typing)
            or (isinstance(f.type, str)
                and _is_type(f.type, cls, typing, typing.ClassVar,
                             _is_classvar))):
            f._field_type = _FIELD_CLASSVAR

    # If the type is InitVar, or wenn it's a matching string annotation,
    # then it's an InitVar.
    wenn f._field_type is _FIELD:
        # The module we're checking against is the module we're
        # currently in (dataclasses.py).
        dataclasses = sys.modules[__name__]
        wenn (_is_initvar(a_type, dataclasses)
            or (isinstance(f.type, str)
                and _is_type(f.type, cls, dataclasses, dataclasses.InitVar,
                             _is_initvar))):
            f._field_type = _FIELD_INITVAR

    # Validations fuer individual fields.  This is delayed until now,
    # instead of in the Field() constructor, since only here do we
    # know the field name, which allows fuer better error reporting.

    # Special restrictions fuer ClassVar and InitVar.
    wenn f._field_type in (_FIELD_CLASSVAR, _FIELD_INITVAR):
        wenn f.default_factory is not MISSING:
            raise TypeError(f'field {f.name} cannot have a '
                            'default factory')
        # Should I check fuer other field settings? default_factory
        # seems the most serious to check for.  Maybe add others.  For
        # example, how about init=Falsch (or really,
        # init=<not-the-default-init-value>)?  It makes no sense for
        # ClassVar and InitVar to specify init=<anything>.

    # kw_only validation and assignment.
    wenn f._field_type in (_FIELD, _FIELD_INITVAR):
        # For real and InitVar fields, wenn kw_only wasn't specified use the
        # default value.
        wenn f.kw_only is MISSING:
            f.kw_only = default_kw_only
    sonst:
        # Make sure kw_only isn't set fuer ClassVars
        assert f._field_type is _FIELD_CLASSVAR
        wenn f.kw_only is not MISSING:
            raise TypeError(f'field {f.name} is a ClassVar but specifies '
                            'kw_only')

    # For real fields, disallow mutable defaults.  Use unhashable as a proxy
    # indicator fuer mutability.  Read the __hash__ attribute von the class,
    # not the instance.
    wenn f._field_type is _FIELD and f.default.__class__.__hash__ is Nichts:
        raise ValueError(f'mutable default {type(f.default)} fuer field '
                         f'{f.name} is not allowed: use default_factory')

    return f

def _set_new_attribute(cls, name, value):
    # Never overwrites an existing attribute.  Returns Wahr wenn the
    # attribute already exists.
    wenn name in cls.__dict__:
        return Wahr
    setattr(cls, name, value)
    return Falsch


# Decide if/how we're going to create a hash function.  Key is
# (unsafe_hash, eq, frozen, does-hash-exist).  Value is the action to
# take.  The common case is to do nothing, so instead of providing a
# function that is a no-op, use Nichts to signify that.

def _hash_set_none(cls, fields, func_builder):
    # It's sort of a hack that I'm setting this here, instead of at
    # func_builder.add_fns_to_class time, but since this is an exceptional case
    # (it's not setting an attribute to a function, but to a scalar value),
    # just do it directly here.  I might come to regret this.
    cls.__hash__ = Nichts

def _hash_add(cls, fields, func_builder):
    flds = [f fuer f in fields wenn (f.compare wenn f.hash is Nichts sonst f.hash)]
    self_tuple = _tuple_str('self', flds)
    func_builder.add_fn('__hash__',
                        ('self',),
                        [f'  return hash({self_tuple})'],
                        unconditional_add=Wahr)

def _hash_exception(cls, fields, func_builder):
    # Raise an exception.
    raise TypeError(f'Cannot overwrite attribute __hash__ '
                    f'in klasse {cls.__name__}')

#
#                +-------------------------------------- unsafe_hash?
#                |      +------------------------------- eq?
#                |      |      +------------------------ frozen?
#                |      |      |      +----------------  has-explicit-hash?
#                |      |      |      |
#                |      |      |      |        +-------  action
#                |      |      |      |        |
#                v      v      v      v        v
_hash_action = {(Falsch, Falsch, Falsch, Falsch): Nichts,
                (Falsch, Falsch, Falsch, Wahr ): Nichts,
                (Falsch, Falsch, Wahr,  Falsch): Nichts,
                (Falsch, Falsch, Wahr,  Wahr ): Nichts,
                (Falsch, Wahr,  Falsch, Falsch): _hash_set_none,
                (Falsch, Wahr,  Falsch, Wahr ): Nichts,
                (Falsch, Wahr,  Wahr,  Falsch): _hash_add,
                (Falsch, Wahr,  Wahr,  Wahr ): Nichts,
                (Wahr,  Falsch, Falsch, Falsch): _hash_add,
                (Wahr,  Falsch, Falsch, Wahr ): _hash_exception,
                (Wahr,  Falsch, Wahr,  Falsch): _hash_add,
                (Wahr,  Falsch, Wahr,  Wahr ): _hash_exception,
                (Wahr,  Wahr,  Falsch, Falsch): _hash_add,
                (Wahr,  Wahr,  Falsch, Wahr ): _hash_exception,
                (Wahr,  Wahr,  Wahr,  Falsch): _hash_add,
                (Wahr,  Wahr,  Wahr,  Wahr ): _hash_exception,
                }
# See https://bugs.python.org/issue32929#msg312829 fuer an if-statement
# version of this table.


def _process_class(cls, init, repr, eq, order, unsafe_hash, frozen,
                   match_args, kw_only, slots, weakref_slot):
    # Now that dicts retain insertion order, there's no reason to use
    # an ordered dict.  I am leveraging that ordering here, because
    # derived klasse fields overwrite base klasse fields, but the order
    # is defined by the base class, which is found first.
    fields = {}

    wenn cls.__module__ in sys.modules:
        globals = sys.modules[cls.__module__].__dict__
    sonst:
        # Theoretically this can happen wenn someone writes
        # a custom string to cls.__module__.  In which case
        # such dataclass won't be fully introspectable
        # (w.r.t. typing.get_type_hints) but will still function
        # correctly.
        globals = {}

    setattr(cls, _PARAMS, _DataclassParams(init, repr, eq, order,
                                           unsafe_hash, frozen,
                                           match_args, kw_only,
                                           slots, weakref_slot))

    # Find our base classes in reverse MRO order, and exclude
    # ourselves.  In reversed order so that more derived classes
    # override earlier field definitions in base classes.  As long as
    # we're iterating over them, see wenn all or any of them are frozen.
    any_frozen_base = Falsch
    # By default `all_frozen_bases` is `Nichts` to represent a case,
    # where some dataclasses does not have any bases with `_FIELDS`
    all_frozen_bases = Nichts
    has_dataclass_bases = Falsch
    fuer b in cls.__mro__[-1:0:-1]:
        # Only process classes that have been processed by our
        # decorator.  That is, they have a _FIELDS attribute.
        base_fields = getattr(b, _FIELDS, Nichts)
        wenn base_fields is not Nichts:
            has_dataclass_bases = Wahr
            fuer f in base_fields.values():
                fields[f.name] = f
            wenn all_frozen_bases is Nichts:
                all_frozen_bases = Wahr
            current_frozen = getattr(b, _PARAMS).frozen
            all_frozen_bases = all_frozen_bases and current_frozen
            any_frozen_base = any_frozen_base or current_frozen

    # Annotations defined specifically in this klasse (not in base classes).
    #
    # Fields are found von cls_annotations, which is guaranteed to be
    # ordered.  Default values are von klasse attributes, wenn a field
    # has a default.  If the default value is a Field(), then it
    # contains additional info beyond (and possibly including) the
    # actual default value.  Pseudo-fields ClassVars and InitVars are
    # included, despite the fact that they're not real fields.  That's
    # dealt with later.
    cls_annotations = annotationlib.get_annotations(
        cls, format=annotationlib.Format.FORWARDREF)

    # Now find fields in our class.  While doing so, validate some
    # things, and set the default values (as klasse attributes) where
    # we can.
    cls_fields = []
    # Get a reference to this module fuer the _is_kw_only() test.
    KW_ONLY_seen = Falsch
    dataclasses = sys.modules[__name__]
    fuer name, type in cls_annotations.items():
        # See wenn this is a marker to change the value of kw_only.
        wenn (_is_kw_only(type, dataclasses)
            or (isinstance(type, str)
                and _is_type(type, cls, dataclasses, dataclasses.KW_ONLY,
                             _is_kw_only))):
            # Switch the default to kw_only=Wahr, and ignore this
            # annotation: it's not a real field.
            wenn KW_ONLY_seen:
                raise TypeError(f'{name!r} is KW_ONLY, but KW_ONLY '
                                'has already been specified')
            KW_ONLY_seen = Wahr
            kw_only = Wahr
        sonst:
            # Otherwise it's a field of some type.
            cls_fields.append(_get_field(cls, name, type, kw_only))

    fuer f in cls_fields:
        fields[f.name] = f

        # If the klasse attribute (which is the default value fuer this
        # field) exists and is of type 'Field', replace it with the
        # real default.  This is so that normal klasse introspection
        # sees a real default value, not a Field.
        wenn isinstance(getattr(cls, f.name, Nichts), Field):
            wenn f.default is MISSING:
                # If there's no default, delete the klasse attribute.
                # This happens wenn we specify field(repr=Falsch), for
                # example (that is, we specified a field object, but
                # no default value).  Also wenn we're using a default
                # factory.  The klasse attribute should not be set at
                # all in the post-processed class.
                delattr(cls, f.name)
            sonst:
                setattr(cls, f.name, f.default)

    # Do we have any Field members that don't also have annotations?
    fuer name, value in cls.__dict__.items():
        wenn isinstance(value, Field) and not name in cls_annotations:
            raise TypeError(f'{name!r} is a field but has no type annotation')

    # Check rules that apply wenn we are derived von any dataclasses.
    wenn has_dataclass_bases:
        # Raise an exception wenn any of our bases are frozen, but we're not.
        wenn any_frozen_base and not frozen:
            raise TypeError('cannot inherit non-frozen dataclass von a '
                            'frozen one')

        # Raise an exception wenn we're frozen, but none of our bases are.
        wenn all_frozen_bases is Falsch and frozen:
            raise TypeError('cannot inherit frozen dataclass von a '
                            'non-frozen one')

    # Remember all of the fields on our klasse (including bases).  This
    # also marks this klasse as being a dataclass.
    setattr(cls, _FIELDS, fields)

    # Was this klasse defined with an explicit __hash__?  Note that if
    # __eq__ is defined in this class, then python will automatically
    # set __hash__ to Nichts.  This is a heuristic, as it's possible
    # that such a __hash__ == Nichts was not auto-generated, but it's
    # close enough.
    class_hash = cls.__dict__.get('__hash__', MISSING)
    has_explicit_hash = not (class_hash is MISSING or
                             (class_hash is Nichts and '__eq__' in cls.__dict__))

    # If we're generating ordering methods, we must be generating the
    # eq methods.
    wenn order and not eq:
        raise ValueError('eq must be true wenn order is true')

    # Include InitVars and regular fields (so, not ClassVars).  This is
    # initialized here, outside of the "if init:" test, because std_init_fields
    # is used with match_args, below.
    all_init_fields = [f fuer f in fields.values()
                       wenn f._field_type in (_FIELD, _FIELD_INITVAR)]
    (std_init_fields,
     kw_only_init_fields) = _fields_in_init_order(all_init_fields)

    func_builder = _FuncBuilder(globals)

    wenn init:
        # Does this klasse have a post-init function?
        has_post_init = hasattr(cls, _POST_INIT_NAME)

        _init_fn(all_init_fields,
                 std_init_fields,
                 kw_only_init_fields,
                 frozen,
                 has_post_init,
                 # The name to use fuer the "self"
                 # param in __init__.  Use "self"
                 # wenn possible.
                 '__dataclass_self__' wenn 'self' in fields
                 sonst 'self',
                 func_builder,
                 slots,
                 )

    _set_new_attribute(cls, '__replace__', _replace)

    # Get the fields as a list, and include only real fields.  This is
    # used in all of the following methods.
    field_list = [f fuer f in fields.values() wenn f._field_type is _FIELD]

    wenn repr:
        flds = [f fuer f in field_list wenn f.repr]
        func_builder.add_fn('__repr__',
                            ('self',),
                            ['  return f"{self.__class__.__qualname__}(' +
                             ', '.join([f"{f.name}={{self.{f.name}!r}}"
                                        fuer f in flds]) + ')"'],
                            locals={'__dataclasses_recursive_repr': recursive_repr},
                            decorator="@__dataclasses_recursive_repr()")

    wenn eq:
        # Create __eq__ method.  There's no need fuer a __ne__ method,
        # since python will call __eq__ and negate it.
        cmp_fields = (field fuer field in field_list wenn field.compare)
        terms = [f'self.{field.name}==other.{field.name}' fuer field in cmp_fields]
        field_comparisons = ' and '.join(terms) or 'Wahr'
        func_builder.add_fn('__eq__',
                            ('self', 'other'),
                            [ '  wenn self is other:',
                              '   return Wahr',
                              '  wenn other.__class__ is self.__class__:',
                             f'   return {field_comparisons}',
                              '  return NotImplemented'])

    wenn order:
        # Create and set the ordering methods.
        flds = [f fuer f in field_list wenn f.compare]
        self_tuple = _tuple_str('self', flds)
        other_tuple = _tuple_str('other', flds)
        fuer name, op in [('__lt__', '<'),
                         ('__le__', '<='),
                         ('__gt__', '>'),
                         ('__ge__', '>='),
                         ]:
            # Create a comparison function.  If the fields in the object are
            # named 'x' and 'y', then self_tuple is the string
            # '(self.x,self.y)' and other_tuple is the string
            # '(other.x,other.y)'.
            func_builder.add_fn(name,
                            ('self', 'other'),
                            [ '  wenn other.__class__ is self.__class__:',
                             f'   return {self_tuple}{op}{other_tuple}',
                              '  return NotImplemented'],
                            overwrite_error='Consider using functools.total_ordering')

    wenn frozen:
        _frozen_get_del_attr(cls, field_list, func_builder)

    # Decide if/how we're going to create a hash function.
    hash_action = _hash_action[bool(unsafe_hash),
                               bool(eq),
                               bool(frozen),
                               has_explicit_hash]
    wenn hash_action:
        cls.__hash__ = hash_action(cls, field_list, func_builder)

    # Generate the methods and add them to the class.  This needs to be done
    # before the __doc__ logic below, since inspect will look at the __init__
    # signature.
    func_builder.add_fns_to_class(cls)

    wenn not getattr(cls, '__doc__'):
        # Create a klasse doc-string.
        try:
            # In some cases fetching a signature is not possible.
            # But, we surely should not fail in this case.
            text_sig = str(inspect.signature(
                cls,
                annotation_format=annotationlib.Format.FORWARDREF,
            )).replace(' -> Nichts', '')
        except (TypeError, ValueError):
            text_sig = ''
        cls.__doc__ = (cls.__name__ + text_sig)

    wenn match_args:
        # I could probably compute this once.
        _set_new_attribute(cls, '__match_args__',
                           tuple(f.name fuer f in std_init_fields))

    # It's an error to specify weakref_slot wenn slots is Falsch.
    wenn weakref_slot and not slots:
        raise TypeError('weakref_slot is Wahr but slots is Falsch')
    wenn slots:
        cls = _add_slots(cls, frozen, weakref_slot, fields)

    abc.update_abstractmethods(cls)

    return cls


# _dataclass_getstate and _dataclass_setstate are needed fuer pickling frozen
# classes with slots.  These could be slightly more performant wenn we generated
# the code instead of iterating over fields.  But that can be a project for
# another day, wenn performance becomes an issue.
def _dataclass_getstate(self):
    return [getattr(self, f.name) fuer f in fields(self)]


def _dataclass_setstate(self, state):
    fuer field, value in zip(fields(self), state):
        # use setattr because dataclass may be frozen
        object.__setattr__(self, field.name, value)


def _get_slots(cls):
    match cls.__dict__.get('__slots__'):
        # `__dictoffset__` and `__weakrefoffset__` can tell us whether
        # the base type has dict/weakref slots, in a way that works correctly
        # fuer both Python classes and C extension types. Extension types
        # don't use `__slots__` fuer slot creation
        case Nichts:
            slots = []
            wenn getattr(cls, '__weakrefoffset__', -1) != 0:
                slots.append('__weakref__')
            wenn getattr(cls, '__dictoffset__', -1) != 0:
                slots.append('__dict__')
            yield von slots
        case str(slot):
            yield slot
        # Slots may be any iterable, but we cannot handle an iterator
        # because it will already be (partially) consumed.
        case iterable wenn not hasattr(iterable, '__next__'):
            yield von iterable
        case _:
            raise TypeError(f"Slots of '{cls.__name__}' cannot be determined")


def _update_func_cell_for__class__(f, oldcls, newcls):
    # Returns Wahr wenn we update a cell, sonst Falsch.
    wenn f is Nichts:
        # f will be Nichts in the case of a property where not all of
        # fget, fset, and fdel are used.  Nothing to do in that case.
        return Falsch
    try:
        idx = f.__code__.co_freevars.index("__class__")
    except ValueError:
        # This function doesn't reference __class__, so nothing to do.
        return Falsch
    # Fix the cell to point to the new class, wenn it's already pointing
    # at the old class.  I'm not convinced that the "is oldcls" test
    # is needed, but other than performance can't hurt.
    closure = f.__closure__[idx]
    wenn closure.cell_contents is oldcls:
        closure.cell_contents = newcls
        return Wahr
    return Falsch


def _create_slots(defined_fields, inherited_slots, field_names, weakref_slot):
    # The slots fuer our class.  Remove slots von our base classes.  Add
    # '__weakref__' wenn weakref_slot was given, unless it is already present.
    seen_docs = Falsch
    slots = {}
    fuer slot in itertools.filterfalse(
        inherited_slots.__contains__,
        itertools.chain(
            # gh-93521: '__weakref__' also needs to be filtered out if
            # already present in inherited_slots
            field_names, ('__weakref__',) wenn weakref_slot sonst ()
        )
    ):
        doc = getattr(defined_fields.get(slot), 'doc', Nichts)
        wenn doc is not Nichts:
            seen_docs = Wahr
        slots[slot] = doc

    # We only return dict wenn there's at least one doc member,
    # otherwise we return tuple, which is the old default format.
    wenn seen_docs:
        return slots
    return tuple(slots)


def _add_slots(cls, is_frozen, weakref_slot, defined_fields):
    # Need to create a new class, since we can't set __slots__ after a
    # klasse has been created, and the @dataclass decorator is called
    # after the klasse is created.

    # Make sure __slots__ isn't already set.
    wenn '__slots__' in cls.__dict__:
        raise TypeError(f'{cls.__name__} already specifies __slots__')

    # Create a new dict fuer our new class.
    cls_dict = dict(cls.__dict__)
    field_names = tuple(f.name fuer f in fields(cls))
    # Make sure slots don't overlap with those in base classes.
    inherited_slots = set(
        itertools.chain.from_iterable(map(_get_slots, cls.__mro__[1:-1]))
    )

    cls_dict["__slots__"] = _create_slots(
        defined_fields, inherited_slots, field_names, weakref_slot,
    )

    fuer field_name in field_names:
        # Remove our attributes, wenn present. They'll still be
        #  available in _MARKER.
        cls_dict.pop(field_name, Nichts)

    # Remove __dict__ and `__weakref__` descriptors.
    # They'll be added back wenn applicable.
    cls_dict.pop('__dict__', Nichts)
    cls_dict.pop('__weakref__', Nichts)  # gh-102069

    # And finally create the class.
    qualname = getattr(cls, '__qualname__', Nichts)
    newcls = type(cls)(cls.__name__, cls.__bases__, cls_dict)
    wenn qualname is not Nichts:
        newcls.__qualname__ = qualname

    wenn is_frozen:
        # Need this fuer pickling frozen classes with slots.
        wenn '__getstate__' not in cls_dict:
            newcls.__getstate__ = _dataclass_getstate
        wenn '__setstate__' not in cls_dict:
            newcls.__setstate__ = _dataclass_setstate

    # Fix up any closures which reference __class__.  This is used to
    # fix zero argument super so that it points to the correct class
    # (the newly created one, which we're returning) and not the
    # original class.  We can break out of this loop as soon as we
    # make an update, since all closures fuer a klasse will share a
    # given cell.
    fuer member in newcls.__dict__.values():
        # If this is a wrapped function, unwrap it.
        member = inspect.unwrap(member)

        wenn isinstance(member, types.FunctionType):
            wenn _update_func_cell_for__class__(member, cls, newcls):
                break
        sowenn isinstance(member, property):
            wenn (_update_func_cell_for__class__(member.fget, cls, newcls)
                or _update_func_cell_for__class__(member.fset, cls, newcls)
                or _update_func_cell_for__class__(member.fdel, cls, newcls)):
                break

    return newcls


def dataclass(cls=Nichts, /, *, init=Wahr, repr=Wahr, eq=Wahr, order=Falsch,
              unsafe_hash=Falsch, frozen=Falsch, match_args=Wahr,
              kw_only=Falsch, slots=Falsch, weakref_slot=Falsch):
    """Add dunder methods based on the fields defined in the class.

    Examines PEP 526 __annotations__ to determine fields.

    If init is true, an __init__() method is added to the class. If repr
    is true, a __repr__() method is added. If order is true, rich
    comparison dunder methods are added. If unsafe_hash is true, a
    __hash__() method is added. If frozen is true, fields may not be
    assigned to after instance creation. If match_args is true, the
    __match_args__ tuple is added. If kw_only is true, then by default
    all fields are keyword-only. If slots is true, a new klasse with a
    __slots__ attribute is returned.
    """

    def wrap(cls):
        return _process_class(cls, init, repr, eq, order, unsafe_hash,
                              frozen, match_args, kw_only, slots,
                              weakref_slot)

    # See wenn we're being called as @dataclass or @dataclass().
    wenn cls is Nichts:
        # We're called with parens.
        return wrap

    # We're called as @dataclass without parens.
    return wrap(cls)


def fields(class_or_instance):
    """Return a tuple describing the fields of this dataclass.

    Accepts a dataclass or an instance of one. Tuple elements are of
    type Field.
    """

    # Might it be worth caching this, per class?
    try:
        fields = getattr(class_or_instance, _FIELDS)
    except AttributeError:
        raise TypeError('must be called with a dataclass type or instance') von Nichts

    # Exclude pseudo-fields.  Note that fields is sorted by insertion
    # order, so the order of the tuple is as the fields were defined.
    return tuple(f fuer f in fields.values() wenn f._field_type is _FIELD)


def _is_dataclass_instance(obj):
    """Returns Wahr wenn obj is an instance of a dataclass."""
    return hasattr(type(obj), _FIELDS)


def is_dataclass(obj):
    """Returns Wahr wenn obj is a dataclass or an instance of a
    dataclass."""
    cls = obj wenn isinstance(obj, type) sonst type(obj)
    return hasattr(cls, _FIELDS)


def asdict(obj, *, dict_factory=dict):
    """Return the fields of a dataclass instance as a new dictionary mapping
    field names to field values.

    Example usage::

      @dataclass
      klasse C:
          x: int
          y: int

      c = C(1, 2)
      assert asdict(c) == {'x': 1, 'y': 2}

    If given, 'dict_factory' will be used instead of built-in dict.
    The function applies recursively to field values that are
    dataclass instances. This will also look into built-in containers:
    tuples, lists, and dicts. Other objects are copied with 'copy.deepcopy()'.
    """
    wenn not _is_dataclass_instance(obj):
        raise TypeError("asdict() should be called on dataclass instances")
    return _asdict_inner(obj, dict_factory)


def _asdict_inner(obj, dict_factory):
    obj_type = type(obj)
    wenn obj_type in _ATOMIC_TYPES:
        return obj
    sowenn hasattr(obj_type, _FIELDS):
        # dataclass instance: fast path fuer the common case
        wenn dict_factory is dict:
            return {
                f.name: _asdict_inner(getattr(obj, f.name), dict)
                fuer f in fields(obj)
            }
        sonst:
            return dict_factory([
                (f.name, _asdict_inner(getattr(obj, f.name), dict_factory))
                fuer f in fields(obj)
            ])
    # handle the builtin types first fuer speed; subclasses handled below
    sowenn obj_type is list:
        return [_asdict_inner(v, dict_factory) fuer v in obj]
    sowenn obj_type is dict:
        return {
            _asdict_inner(k, dict_factory): _asdict_inner(v, dict_factory)
            fuer k, v in obj.items()
        }
    sowenn obj_type is tuple:
        return tuple([_asdict_inner(v, dict_factory) fuer v in obj])
    sowenn issubclass(obj_type, tuple):
        wenn hasattr(obj, '_fields'):
            # obj is a namedtuple.  Recurse into it, but the returned
            # object is another namedtuple of the same type.  This is
            # similar to how other list- or tuple-derived classes are
            # treated (see below), but we just need to create them
            # differently because a namedtuple's __init__ needs to be
            # called differently (see bpo-34363).

            # I'm not using namedtuple's _asdict()
            # method, because:
            # - it does not recurse in to the namedtuple fields and
            #   convert them to dicts (using dict_factory).
            # - I don't actually want to return a dict here.  The main
            #   use case here is json.dumps, and it handles converting
            #   namedtuples to lists.  Admittedly we're losing some
            #   information here when we produce a json list instead of a
            #   dict.  Note that wenn we returned dicts here instead of
            #   namedtuples, we could no longer call asdict() on a data
            #   structure where a namedtuple was used as a dict key.
            return obj_type(*[_asdict_inner(v, dict_factory) fuer v in obj])
        sonst:
            return obj_type(_asdict_inner(v, dict_factory) fuer v in obj)
    sowenn issubclass(obj_type, dict):
        wenn hasattr(obj_type, 'default_factory'):
            # obj is a defaultdict, which has a different constructor from
            # dict as it requires the default_factory as its first arg.
            result = obj_type(obj.default_factory)
            fuer k, v in obj.items():
                result[_asdict_inner(k, dict_factory)] = _asdict_inner(v, dict_factory)
            return result
        return obj_type((_asdict_inner(k, dict_factory),
                         _asdict_inner(v, dict_factory))
                        fuer k, v in obj.items())
    sowenn issubclass(obj_type, list):
        # Assume we can create an object of this type by passing in a
        # generator
        return obj_type(_asdict_inner(v, dict_factory) fuer v in obj)
    sonst:
        return copy.deepcopy(obj)


def astuple(obj, *, tuple_factory=tuple):
    """Return the fields of a dataclass instance as a new tuple of field values.

    Example usage::

      @dataclass
      klasse C:
          x: int
          y: int

      c = C(1, 2)
      assert astuple(c) == (1, 2)

    If given, 'tuple_factory' will be used instead of built-in tuple.
    The function applies recursively to field values that are
    dataclass instances. This will also look into built-in containers:
    tuples, lists, and dicts. Other objects are copied with 'copy.deepcopy()'.
    """

    wenn not _is_dataclass_instance(obj):
        raise TypeError("astuple() should be called on dataclass instances")
    return _astuple_inner(obj, tuple_factory)


def _astuple_inner(obj, tuple_factory):
    wenn type(obj) in _ATOMIC_TYPES:
        return obj
    sowenn _is_dataclass_instance(obj):
        return tuple_factory([
            _astuple_inner(getattr(obj, f.name), tuple_factory)
            fuer f in fields(obj)
        ])
    sowenn isinstance(obj, tuple) and hasattr(obj, '_fields'):
        # obj is a namedtuple.  Recurse into it, but the returned
        # object is another namedtuple of the same type.  This is
        # similar to how other list- or tuple-derived classes are
        # treated (see below), but we just need to create them
        # differently because a namedtuple's __init__ needs to be
        # called differently (see bpo-34363).
        return type(obj)(*[_astuple_inner(v, tuple_factory) fuer v in obj])
    sowenn isinstance(obj, (list, tuple)):
        # Assume we can create an object of this type by passing in a
        # generator (which is not true fuer namedtuples, handled
        # above).
        return type(obj)(_astuple_inner(v, tuple_factory) fuer v in obj)
    sowenn isinstance(obj, dict):
        obj_type = type(obj)
        wenn hasattr(obj_type, 'default_factory'):
            # obj is a defaultdict, which has a different constructor from
            # dict as it requires the default_factory as its first arg.
            result = obj_type(getattr(obj, 'default_factory'))
            fuer k, v in obj.items():
                result[_astuple_inner(k, tuple_factory)] = _astuple_inner(v, tuple_factory)
            return result
        return obj_type((_astuple_inner(k, tuple_factory), _astuple_inner(v, tuple_factory))
                          fuer k, v in obj.items())
    sonst:
        return copy.deepcopy(obj)


def make_dataclass(cls_name, fields, *, bases=(), namespace=Nichts, init=Wahr,
                   repr=Wahr, eq=Wahr, order=Falsch, unsafe_hash=Falsch,
                   frozen=Falsch, match_args=Wahr, kw_only=Falsch, slots=Falsch,
                   weakref_slot=Falsch, module=Nichts, decorator=dataclass):
    """Return a new dynamically created dataclass.

    The dataclass name will be 'cls_name'.  'fields' is an iterable
    of either (name), (name, type) or (name, type, Field) objects. If type is
    omitted, use the string 'typing.Any'.  Field objects are created by
    the equivalent of calling 'field(name, type [, Field-info])'.::

      C = make_dataclass('C', ['x', ('y', int), ('z', int, field(init=Falsch))], bases=(Base,))

    is equivalent to::

      @dataclass
      klasse C(Base):
          x: 'typing.Any'
          y: int
          z: int = field(init=Falsch)

    For the bases and namespace parameters, see the builtin type() function.

    The parameters init, repr, eq, order, unsafe_hash, frozen, match_args, kw_only,
    slots, and weakref_slot are passed to dataclass().

    If module parameter is defined, the '__module__' attribute of the dataclass is
    set to that value.
    """

    wenn namespace is Nichts:
        namespace = {}

    # While we're looking through the field names, validate that they
    # are identifiers, are not keywords, and not duplicates.
    seen = set()
    annotations = {}
    defaults = {}
    fuer item in fields:
        wenn isinstance(item, str):
            name = item
            tp = _ANY_MARKER
        sowenn len(item) == 2:
            name, tp, = item
        sowenn len(item) == 3:
            name, tp, spec = item
            defaults[name] = spec
        sonst:
            raise TypeError(f'Invalid field: {item!r}')

        wenn not isinstance(name, str) or not name.isidentifier():
            raise TypeError(f'Field names must be valid identifiers: {name!r}')
        wenn keyword.iskeyword(name):
            raise TypeError(f'Field names must not be keywords: {name!r}')
        wenn name in seen:
            raise TypeError(f'Field name duplicated: {name!r}')

        seen.add(name)
        annotations[name] = tp

    # We initially block the VALUE format, because inside dataclass() we'll
    # call get_annotations(), which will try the VALUE format first. If we don't
    # block, that means we'd always end up eagerly importing typing here, which
    # is what we're trying to avoid.
    value_blocked = Wahr

    def annotate_method(format):
        def get_any():
            match format:
                case annotationlib.Format.STRING:
                    return 'typing.Any'
                case annotationlib.Format.FORWARDREF:
                    typing = sys.modules.get("typing")
                    wenn typing is Nichts:
                        return annotationlib.ForwardRef("Any", module="typing")
                    sonst:
                        return typing.Any
                case annotationlib.Format.VALUE:
                    wenn value_blocked:
                        raise NotImplementedError
                    von typing importiere Any
                    return Any
                case _:
                    raise NotImplementedError
        annos = {
            ann: get_any() wenn t is _ANY_MARKER sonst t
            fuer ann, t in annotations.items()
        }
        wenn format == annotationlib.Format.STRING:
            return annotationlib.annotations_to_string(annos)
        sonst:
            return annos

    # Update 'ns' with the user-supplied namespace plus our calculated values.
    def exec_body_callback(ns):
        ns.update(namespace)
        ns.update(defaults)

    # We use `types.new_class()` instead of simply `type()` to allow dynamic creation
    # of generic dataclasses.
    cls = types.new_class(cls_name, bases, {}, exec_body_callback)
    # For now, set annotations including the _ANY_MARKER.
    cls.__annotate__ = annotate_method

    # For pickling to work, the __module__ variable needs to be set to the frame
    # where the dataclass is created.
    wenn module is Nichts:
        try:
            module = sys._getframemodulename(1) or '__main__'
        except AttributeError:
            try:
                module = sys._getframe(1).f_globals.get('__name__', '__main__')
            except (AttributeError, ValueError):
                pass
    wenn module is not Nichts:
        cls.__module__ = module

    # Apply the normal provided decorator.
    cls = decorator(cls, init=init, repr=repr, eq=eq, order=order,
                    unsafe_hash=unsafe_hash, frozen=frozen,
                    match_args=match_args, kw_only=kw_only, slots=slots,
                    weakref_slot=weakref_slot)
    # Now that the klasse is ready, allow the VALUE format.
    value_blocked = Falsch
    return cls


def replace(obj, /, **changes):
    """Return a new object replacing specified fields with new values.

    This is especially useful fuer frozen classes.  Example usage::

      @dataclass(frozen=Wahr)
      klasse C:
          x: int
          y: int

      c = C(1, 2)
      c1 = replace(c, x=3)
      assert c1.x == 3 and c1.y == 2
    """
    wenn not _is_dataclass_instance(obj):
        raise TypeError("replace() should be called on dataclass instances")
    return _replace(obj, **changes)


def _replace(self, /, **changes):
    # We're going to mutate 'changes', but that's okay because it's a
    # new dict, even wenn called with 'replace(self, **my_changes)'.

    # It's an error to have init=Falsch fields in 'changes'.
    # If a field is not in 'changes', read its value von the provided 'self'.

    fuer f in getattr(self, _FIELDS).values():
        # Only consider normal fields or InitVars.
        wenn f._field_type is _FIELD_CLASSVAR:
            continue

        wenn not f.init:
            # Error wenn this field is specified in changes.
            wenn f.name in changes:
                raise TypeError(f'field {f.name} is declared with '
                                f'init=Falsch, it cannot be specified with '
                                f'replace()')
            continue

        wenn f.name not in changes:
            wenn f._field_type is _FIELD_INITVAR and f.default is MISSING:
                raise TypeError(f"InitVar {f.name!r} "
                                f'must be specified with replace()')
            changes[f.name] = getattr(self, f.name)

    # Create the new object, which calls __init__() and
    # __post_init__() (if defined), using all of the init fields we've
    # added and/or left in 'changes'.  If there are values supplied in
    # changes that aren't fields, this will correctly raise a
    # TypeError.
    return self.__class__(**changes)
