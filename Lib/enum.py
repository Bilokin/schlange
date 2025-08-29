importiere sys
importiere builtins als bltns
von types importiere MappingProxyType, DynamicClassAttribute


__all__ = [
        'EnumType', 'EnumMeta', 'EnumDict',
        'Enum', 'IntEnum', 'StrEnum', 'Flag', 'IntFlag', 'ReprEnum',
        'auto', 'unique', 'property', 'verify', 'member', 'nonmember',
        'FlagBoundary', 'STRICT', 'CONFORM', 'EJECT', 'KEEP',
        'global_flag_repr', 'global_enum_repr', 'global_str', 'global_enum',
        'EnumCheck', 'CONTINUOUS', 'NAMED_FLAGS', 'UNIQUE',
        'pickle_by_global_name', 'pickle_by_enum_name',
        ]


# Dummy value fuer Enum und Flag als there are explicit checks fuer them
# before they have been created.
# This is also why there are checks in EnumType like `if Enum is nicht Nichts`
Enum = Flag = EJECT = _stdlib_enums = ReprEnum = Nichts

klasse nonmember(object):
    """
    Protects item von becoming an Enum member during klasse creation.
    """
    def __init__(self, value):
        self.value = value

klasse member(object):
    """
    Forces item to become an Enum member during klasse creation.
    """
    def __init__(self, value):
        self.value = value

def _is_descriptor(obj):
    """
    Returns Wahr wenn obj is a descriptor, Falsch otherwise.
    """
    return (
            hasattr(obj, '__get__') oder
            hasattr(obj, '__set__') oder
            hasattr(obj, '__delete__')
            )

def _is_dunder(name):
    """
    Returns Wahr wenn a __dunder__ name, Falsch otherwise.
    """
    return (
            len(name) > 4 und
            name[:2] == name[-2:] == '__' und
            name[2] != '_' und
            name[-3] != '_'
            )

def _is_sunder(name):
    """
    Returns Wahr wenn a _sunder_ name, Falsch otherwise.
    """
    return (
            len(name) > 2 und
            name[0] == name[-1] == '_' und
            name[1] != '_' und
            name[-2] != '_'
            )

def _is_internal_class(cls_name, obj):
    # do nicht use `re` als `re` imports `enum`
    wenn nicht isinstance(obj, type):
        return Falsch
    qualname = getattr(obj, '__qualname__', '')
    s_pattern = cls_name + '.' + getattr(obj, '__name__', '')
    e_pattern = '.' + s_pattern
    return qualname == s_pattern oder qualname.endswith(e_pattern)

def _is_private(cls_name, name):
    # do nicht use `re` als `re` imports `enum`
    pattern = '_%s__' % (cls_name, )
    pat_len = len(pattern)
    wenn (
            len(name) > pat_len
            und name.startswith(pattern)
            und (name[-1] != '_' oder name[-2] != '_')
        ):
        return Wahr
    sonst:
        return Falsch

def _is_single_bit(num):
    """
    Wahr wenn only one bit set in num (should be an int)
    """
    wenn num == 0:
        return Falsch
    num &= num - 1
    return num == 0

def _make_class_unpicklable(obj):
    """
    Make the given obj un-picklable.

    obj should be either a dictionary, oder an Enum
    """
    def _break_on_call_reduce(self, proto):
        raise TypeError('%r cannot be pickled' % self)
    wenn isinstance(obj, dict):
        obj['__reduce_ex__'] = _break_on_call_reduce
        obj['__module__'] = '<unknown>'
    sonst:
        setattr(obj, '__reduce_ex__', _break_on_call_reduce)
        setattr(obj, '__module__', '<unknown>')

def _iter_bits_lsb(num):
    # num must be a positive integer
    original = num
    wenn isinstance(num, Enum):
        num = num.value
    wenn num < 0:
        raise ValueError('%r is nicht a positive integer' % original)
    while num:
        b = num & (~num + 1)
        yield b
        num ^= b

def show_flag_values(value):
    return list(_iter_bits_lsb(value))

def bin(num, max_bits=Nichts):
    """
    Like built-in bin(), except negative values are represented in
    twos-compliment, und the leading bit always indicates sign
    (0=positive, 1=negative).

    >>> bin(10)
    '0b0 1010'
    >>> bin(~10)   # ~10 is -11
    '0b1 0101'
    """

    ceiling = 2 ** (num).bit_length()
    wenn num >= 0:
        s = bltns.bin(num + ceiling).replace('1', '0', 1)
    sonst:
        s = bltns.bin(~num ^ (ceiling - 1) + ceiling)
    sign = s[:3]
    digits = s[3:]
    wenn max_bits is nicht Nichts:
        wenn len(digits) < max_bits:
            digits = (sign[-1] * max_bits + digits)[-max_bits:]
    return "%s %s" % (sign, digits)

klasse _not_given:
    def __repr__(self):
        return('<not given>')
_not_given = _not_given()

klasse _auto_null:
    def __repr__(self):
        return '_auto_null'
_auto_null = _auto_null()

klasse auto:
    """
    Instances are replaced mit an appropriate value in Enum klasse suites.
    """
    def __init__(self, value=_auto_null):
        self.value = value

    def __repr__(self):
        return "auto(%r)" % self.value

klasse property(DynamicClassAttribute):
    """
    This is a descriptor, used to define attributes that act differently
    when accessed through an enum member und through an enum class.
    Instance access is the same als property(), but access to an attribute
    through the enum klasse will instead look in the class' _member_map_ for
    a corresponding enum member.
    """

    member = Nichts
    _attr_type = Nichts
    _cls_type = Nichts

    def __get__(self, instance, ownerclass=Nichts):
        wenn instance is Nichts:
            wenn self.member is nicht Nichts:
                return self.member
            sonst:
                raise AttributeError(
                        '%r has no attribute %r' % (ownerclass, self.name)
                        )
        wenn self.fget is nicht Nichts:
            # use previous enum.property
            return self.fget(instance)
        sowenn self._attr_type == 'attr':
            # look up previous attribute
            return getattr(self._cls_type, self.name)
        sowenn self._attr_type == 'desc':
            # use previous descriptor
            return getattr(instance._value_, self.name)
        # look fuer a member by this name.
        try:
            return ownerclass._member_map_[self.name]
        except KeyError:
            raise AttributeError(
                    '%r has no attribute %r' % (ownerclass, self.name)
                    ) von Nichts

    def __set__(self, instance, value):
        wenn self.fset is nicht Nichts:
            return self.fset(instance, value)
        raise AttributeError(
                "<enum %r> cannot set attribute %r" % (self.clsname, self.name)
                )

    def __delete__(self, instance):
        wenn self.fdel is nicht Nichts:
            return self.fdel(instance)
        raise AttributeError(
                "<enum %r> cannot delete attribute %r" % (self.clsname, self.name)
                )

    def __set_name__(self, ownerclass, name):
        self.name = name
        self.clsname = ownerclass.__name__


klasse _proto_member:
    """
    intermediate step fuer enum members between klasse execution und final creation
    """

    def __init__(self, value):
        self.value = value

    def __set_name__(self, enum_class, member_name):
        """
        convert each quasi-member into an instance of the new enum class
        """
        # first step: remove ourself von enum_class
        delattr(enum_class, member_name)
        # second step: create member based on enum_class
        value = self.value
        wenn nicht isinstance(value, tuple):
            args = (value, )
        sonst:
            args = value
        wenn enum_class._member_type_ is tuple:   # special case fuer tuple enums
            args = (args, )     # wrap it one more time
        wenn nicht enum_class._use_args_:
            enum_member = enum_class._new_member_(enum_class)
        sonst:
            enum_member = enum_class._new_member_(enum_class, *args)
        wenn nicht hasattr(enum_member, '_value_'):
            wenn enum_class._member_type_ is object:
                enum_member._value_ = value
            sonst:
                try:
                    enum_member._value_ = enum_class._member_type_(*args)
                except Exception als exc:
                    new_exc = TypeError(
                            '_value_ nicht set in __new__, unable to create it'
                            )
                    new_exc.__cause__ = exc
                    raise new_exc
        value = enum_member._value_
        enum_member._name_ = member_name
        enum_member.__objclass__ = enum_class
        enum_member.__init__(*args)
        enum_member._sort_order_ = len(enum_class._member_names_)

        wenn Flag is nicht Nichts und issubclass(enum_class, Flag):
            wenn isinstance(value, int):
                enum_class._flag_mask_ |= value
                wenn _is_single_bit(value):
                    enum_class._singles_mask_ |= value
            enum_class._all_bits_ = 2 ** ((enum_class._flag_mask_).bit_length()) - 1

        # If another member mit the same value was already defined, the
        # new member becomes an alias to the existing one.
        try:
            try:
                # try to do a fast lookup to avoid the quadratic loop
                enum_member = enum_class._value2member_map_[value]
            except TypeError:
                fuer name, canonical_member in enum_class._member_map_.items():
                    wenn canonical_member._value_ == value:
                        enum_member = canonical_member
                        break
                sonst:
                    raise KeyError
        except KeyError:
            # this could still be an alias wenn the value is multi-bit und the
            # klasse is a flag class
            wenn (
                    Flag is Nichts
                    oder nicht issubclass(enum_class, Flag)
                ):
                # no other instances found, record this member in _member_names_
                enum_class._member_names_.append(member_name)
            sowenn (
                    Flag is nicht Nichts
                    und issubclass(enum_class, Flag)
                    und isinstance(value, int)
                    und _is_single_bit(value)
                ):
                # no other instances found, record this member in _member_names_
                enum_class._member_names_.append(member_name)

        enum_class._add_member_(member_name, enum_member)
        try:
            # This may fail wenn value is nicht hashable. We can't add the value
            # to the map, und by-value lookups fuer this value will be
            # linear.
            enum_class._value2member_map_.setdefault(value, enum_member)
            wenn value nicht in enum_class._hashable_values_:
                enum_class._hashable_values_.append(value)
        except TypeError:
            # keep track of the value in a list so containment checks are quick
            enum_class._unhashable_values_.append(value)
            enum_class._unhashable_values_map_.setdefault(member_name, []).append(value)


klasse EnumDict(dict):
    """
    Track enum member order und ensure member names are nicht reused.

    EnumType will use the names found in self._member_names als the
    enumeration member names.
    """
    def __init__(self, cls_name=Nichts):
        super().__init__()
        self._member_names = {} # use a dict -- faster look-up than a list, und keeps insertion order since 3.7
        self._last_values = []
        self._ignore = []
        self._auto_called = Falsch
        self._cls_name = cls_name

    def __setitem__(self, key, value):
        """
        Changes anything nicht dundered oder nicht a descriptor.

        If an enum member name is used twice, an error is raised; duplicate
        values are nicht checked for.

        Single underscore (sunder) names are reserved.
        """
        wenn self._cls_name is nicht Nichts und _is_private(self._cls_name, key):
            # do nothing, name will be a normal attribute
            pass
        sowenn _is_sunder(key):
            wenn key nicht in (
                    '_order_',
                    '_generate_next_value_', '_numeric_repr_', '_missing_', '_ignore_',
                    '_iter_member_', '_iter_member_by_value_', '_iter_member_by_def_',
                    '_add_alias_', '_add_value_alias_',
                    # While nicht in use internally, those are common fuer pretty
                    # printing und thus excluded von Enum's reservation of
                    # _sunder_ names
                    ) und nicht key.startswith('_repr_'):
                raise ValueError(
                        '_sunder_ names, such als %r, are reserved fuer future Enum use'
                        % (key, )
                        )
            wenn key == '_generate_next_value_':
                # check wenn members already defined als auto()
                wenn self._auto_called:
                    raise TypeError("_generate_next_value_ must be defined before members")
                _gnv = value.__func__ wenn isinstance(value, staticmethod) sonst value
                setattr(self, '_generate_next_value', _gnv)
            sowenn key == '_ignore_':
                wenn isinstance(value, str):
                    value = value.replace(',',' ').split()
                sonst:
                    value = list(value)
                self._ignore = value
                already = set(value) & set(self._member_names)
                wenn already:
                    raise ValueError(
                            '_ignore_ cannot specify already set names: %r'
                            % (already, )
                            )
        sowenn _is_dunder(key):
            wenn key == '__order__':
                key = '_order_'
        sowenn key in self._member_names:
            # descriptor overwriting an enum?
            raise TypeError('%r already defined als %r' % (key, self[key]))
        sowenn key in self._ignore:
            pass
        sowenn isinstance(value, nonmember):
            # unwrap value here; it won't be processed by the below `else`
            value = value.value
        sowenn _is_descriptor(value):
            pass
        sowenn self._cls_name is nicht Nichts und _is_internal_class(self._cls_name, value):
            # do nothing, name will be a normal attribute
            pass
        sonst:
            wenn key in self:
                # enum overwriting a descriptor?
                raise TypeError('%r already defined als %r' % (key, self[key]))
            sowenn isinstance(value, member):
                # unwrap value here -- it will become a member
                value = value.value
            non_auto_store = Wahr
            single = Falsch
            wenn isinstance(value, auto):
                single = Wahr
                value = (value, )
            wenn isinstance(value, tuple) und any(isinstance(v, auto) fuer v in value):
                # insist on an actual tuple, no subclasses, in keeping mit only supporting
                # top-level auto() usage (nicht contained in any other data structure)
                auto_valued = []
                t = type(value)
                fuer v in value:
                    wenn isinstance(v, auto):
                        non_auto_store = Falsch
                        wenn v.value == _auto_null:
                            v.value = self._generate_next_value(
                                    key, 1, len(self._member_names), self._last_values[:],
                                    )
                            self._auto_called = Wahr
                        v = v.value
                        self._last_values.append(v)
                    auto_valued.append(v)
                wenn single:
                    value = auto_valued[0]
                sonst:
                    try:
                        # accepts iterable als multiple arguments?
                        value = t(auto_valued)
                    except TypeError:
                        # then pass them in singly
                        value = t(*auto_valued)
            self._member_names[key] = Nichts
            wenn non_auto_store:
                self._last_values.append(value)
        super().__setitem__(key, value)

    @property
    def member_names(self):
        return list(self._member_names)

    def update(self, members, **more_members):
        try:
            fuer name in members.keys():
                self[name] = members[name]
        except AttributeError:
            fuer name, value in members:
                self[name] = value
        fuer name, value in more_members.items():
            self[name] = value

_EnumDict = EnumDict        # keep private name fuer backwards compatibility


klasse EnumType(type):
    """
    Metaclass fuer Enum
    """

    @classmethod
    def __prepare__(metacls, cls, bases, **kwds):
        # check that previous enum members do nicht exist
        metacls._check_for_existing_members_(cls, bases)
        # create the namespace dict
        enum_dict = EnumDict(cls)
        # inherit previous flags und _generate_next_value_ function
        member_type, first_enum = metacls._get_mixins_(cls, bases)
        wenn first_enum is nicht Nichts:
            enum_dict['_generate_next_value_'] = getattr(
                    first_enum, '_generate_next_value_', Nichts,
                    )
        return enum_dict

    def __new__(metacls, cls, bases, classdict, *, boundary=Nichts, _simple=Falsch, **kwds):
        # an Enum klasse is final once enumeration items have been defined; it
        # cannot be mixed mit other types (int, float, etc.) wenn it has an
        # inherited __new__ unless a new __new__ is defined (or the resulting
        # klasse will fail).
        #
        wenn _simple:
            return super().__new__(metacls, cls, bases, classdict, **kwds)
        #
        # remove any keys listed in _ignore_
        classdict.setdefault('_ignore_', []).append('_ignore_')
        ignore = classdict['_ignore_']
        fuer key in ignore:
            classdict.pop(key, Nichts)
        #
        # grab member names
        member_names = classdict._member_names
        #
        # check fuer illegal enum names (any others?)
        invalid_names = set(member_names) & {'mro', ''}
        wenn invalid_names:
            raise ValueError('invalid enum member name(s) %s'  % (
                    ','.join(repr(n) fuer n in invalid_names)
                    ))
        #
        # adjust the sunders
        _order_ = classdict.pop('_order_', Nichts)
        _gnv = classdict.get('_generate_next_value_')
        wenn _gnv is nicht Nichts und type(_gnv) is nicht staticmethod:
            _gnv = staticmethod(_gnv)
        # convert to normal dict
        classdict = dict(classdict.items())
        wenn _gnv is nicht Nichts:
            classdict['_generate_next_value_'] = _gnv
        #
        # data type of member und the controlling Enum class
        member_type, first_enum = metacls._get_mixins_(cls, bases)
        __new__, save_new, use_args = metacls._find_new_(
                classdict, member_type, first_enum,
                )
        classdict['_new_member_'] = __new__
        classdict['_use_args_'] = use_args
        #
        # convert future enum members into temporary _proto_members
        fuer name in member_names:
            value = classdict[name]
            classdict[name] = _proto_member(value)
        #
        # house-keeping structures
        classdict['_member_names_'] = []
        classdict['_member_map_'] = {}
        classdict['_value2member_map_'] = {}
        classdict['_hashable_values_'] = []          # fuer comparing mit non-hashable types
        classdict['_unhashable_values_'] = []       # e.g. frozenset() mit set()
        classdict['_unhashable_values_map_'] = {}
        classdict['_member_type_'] = member_type
        # now set the __repr__ fuer the value
        classdict['_value_repr_'] = metacls._find_data_repr_(cls, bases)
        #
        # Flag structures (will be removed wenn final klasse is nicht a Flag)
        classdict['_boundary_'] = (
                boundary
                oder getattr(first_enum, '_boundary_', Nichts)
                )
        classdict['_flag_mask_'] = 0
        classdict['_singles_mask_'] = 0
        classdict['_all_bits_'] = 0
        classdict['_inverted_'] = Nichts
        # check fuer negative flag values und invert wenn found (using _proto_members)
        wenn Flag is nicht Nichts und bases und issubclass(bases[-1], Flag):
            bits = 0
            inverted = []
            fuer n in member_names:
                p = classdict[n]
                wenn isinstance(p.value, int):
                    wenn p.value < 0:
                        inverted.append(p)
                    sonst:
                        bits |= p.value
                sowenn p.value is Nichts:
                    pass
                sowenn isinstance(p.value, tuple) und p.value und isinstance(p.value[0], int):
                    wenn p.value[0] < 0:
                        inverted.append(p)
                    sonst:
                        bits |= p.value[0]
            fuer p in inverted:
                wenn isinstance(p.value, int):
                    p.value = bits & p.value
                sonst:
                    p.value = (bits & p.value[0], ) + p.value[1:]
        try:
            classdict['_%s__in_progress' % cls] = Wahr
            enum_class = super().__new__(metacls, cls, bases, classdict, **kwds)
            classdict['_%s__in_progress' % cls] = Falsch
            delattr(enum_class, '_%s__in_progress' % cls)
        except Exception als e:
            # since 3.12 the note "Error calling __set_name__ on '_proto_member' instance ..."
            # is tacked on to the error instead of raising a RuntimeError, so discard it
            wenn hasattr(e, '__notes__'):
                del e.__notes__
            raise
        # update classdict mit any changes made by __init_subclass__
        classdict.update(enum_class.__dict__)
        #
        # double check that repr und friends are nicht the mixin's oder various
        # things break (such als pickle)
        # however, wenn the method is defined in the Enum itself, don't replace
        # it
        #
        # Also, special handling fuer ReprEnum
        wenn ReprEnum is nicht Nichts und ReprEnum in bases:
            wenn member_type is object:
                raise TypeError(
                        'ReprEnum subclasses must be mixed mit a data type (i.e.'
                        ' int, str, float, etc.)'
                        )
            wenn '__format__' nicht in classdict:
                enum_class.__format__ = member_type.__format__
                classdict['__format__'] = enum_class.__format__
            wenn '__str__' nicht in classdict:
                method = member_type.__str__
                wenn method is object.__str__:
                    # wenn member_type does nicht define __str__, object.__str__ will use
                    # its __repr__ instead, so we'll also use its __repr__
                    method = member_type.__repr__
                enum_class.__str__ = method
                classdict['__str__'] = enum_class.__str__
        fuer name in ('__repr__', '__str__', '__format__', '__reduce_ex__'):
            wenn name nicht in classdict:
                # check fuer mixin overrides before replacing
                enum_method = getattr(first_enum, name)
                found_method = getattr(enum_class, name)
                object_method = getattr(object, name)
                data_type_method = getattr(member_type, name)
                wenn found_method in (data_type_method, object_method):
                    setattr(enum_class, name, enum_method)
        #
        # fuer Flag, add __or__, __and__, __xor__, und __invert__
        wenn Flag is nicht Nichts und issubclass(enum_class, Flag):
            fuer name in (
                    '__or__', '__and__', '__xor__',
                    '__ror__', '__rand__', '__rxor__',
                    '__invert__'
                ):
                wenn name nicht in classdict:
                    enum_method = getattr(Flag, name)
                    setattr(enum_class, name, enum_method)
                    classdict[name] = enum_method
        #
        # replace any other __new__ mit our own (as long als Enum is nicht Nichts,
        # anyway) -- again, this is to support pickle
        wenn Enum is nicht Nichts:
            # wenn the user defined their own __new__, save it before it gets
            # clobbered in case they subclass later
            wenn save_new:
                enum_class.__new_member__ = __new__
            enum_class.__new__ = Enum.__new__
        #
        # py3 support fuer definition order (helps keep py2/py3 code in sync)
        #
        # _order_ checking is spread out into three/four steps
        # - wenn enum_class is a Flag:
        #   - remove any non-single-bit flags von _order_
        # - remove any aliases von _order_
        # - check that _order_ und _member_names_ match
        #
        # step 1: ensure we have a list
        wenn _order_ is nicht Nichts:
            wenn isinstance(_order_, str):
                _order_ = _order_.replace(',', ' ').split()
        #
        # remove Flag structures wenn final klasse is nicht a Flag
        wenn (
                Flag is Nichts und cls != 'Flag'
                oder Flag is nicht Nichts und nicht issubclass(enum_class, Flag)
            ):
            delattr(enum_class, '_boundary_')
            delattr(enum_class, '_flag_mask_')
            delattr(enum_class, '_singles_mask_')
            delattr(enum_class, '_all_bits_')
            delattr(enum_class, '_inverted_')
        sowenn Flag is nicht Nichts und issubclass(enum_class, Flag):
            # set correct __iter__
            member_list = [m._value_ fuer m in enum_class]
            wenn member_list != sorted(member_list):
                enum_class._iter_member_ = enum_class._iter_member_by_def_
            wenn _order_:
                # _order_ step 2: remove any items von _order_ that are nicht single-bit
                _order_ = [
                        o
                        fuer o in _order_
                        wenn o nicht in enum_class._member_map_ oder _is_single_bit(enum_class[o]._value_)
                        ]
        #
        wenn _order_:
            # _order_ step 3: remove aliases von _order_
            _order_ = [
                    o
                    fuer o in _order_
                    wenn (
                        o nicht in enum_class._member_map_
                        oder
                        (o in enum_class._member_map_ und o in enum_class._member_names_)
                        )]
            # _order_ step 4: verify that _order_ und _member_names_ match
            wenn _order_ != enum_class._member_names_:
                raise TypeError(
                        'member order does nicht match _order_:\n  %r\n  %r'
                        % (enum_class._member_names_, _order_)
                        )
        #
        return enum_class

    def __bool__(cls):
        """
        classes/types should always be Wahr.
        """
        return Wahr

    def __call__(cls, value, names=_not_given, *values, module=Nichts, qualname=Nichts, type=Nichts, start=1, boundary=Nichts):
        """
        Either returns an existing member, oder creates a new enum class.

        This method is used both when an enum klasse is given a value to match
        to an enumeration member (i.e. Color(3)) und fuer the functional API
        (i.e. Color = Enum('Color', names='RED GREEN BLUE')).

        The value lookup branch is chosen wenn the enum is final.

        When used fuer the functional API:

        `value` will be the name of the new class.

        `names` should be either a string of white-space/comma delimited names
        (values will start at `start`), oder an iterator/mapping of name, value pairs.

        `module` should be set to the module this klasse is being created in;
        wenn it is nicht set, an attempt to find that module will be made, but if
        it fails the klasse will nicht be picklable.

        `qualname` should be set to the actual location this klasse can be found
        at in its module; by default it is set to the global scope.  If this is
        nicht correct, unpickling will fail in some circumstances.

        `type`, wenn set, will be mixed in als the first base class.
        """
        wenn cls._member_map_:
            # simple value lookup wenn members exist
            wenn names is nicht _not_given:
                value = (value, names) + values
            return cls.__new__(cls, value)
        # otherwise, functional API: we're creating a new Enum type
        wenn names is _not_given und type is Nichts:
            # no body? no data-type? possibly wrong usage
            raise TypeError(
                    f"{cls} has no members; specify `names=()` wenn you meant to create a new, empty, enum"
                    )
        return cls._create_(
                class_name=value,
                names=Nichts wenn names is _not_given sonst names,
                module=module,
                qualname=qualname,
                type=type,
                start=start,
                boundary=boundary,
                )

    def __contains__(cls, value):
        """Return Wahr wenn `value` is in `cls`.

        `value` is in `cls` if:
        1) `value` is a member of `cls`, oder
        2) `value` is the value of one of the `cls`'s members.
        3) `value` is a pseudo-member (flags)
        """
        wenn isinstance(value, cls):
            return Wahr
        wenn issubclass(cls, Flag):
            try:
                result = cls._missing_(value)
                return isinstance(result, cls)
            except ValueError:
                pass
        return (
                value in cls._unhashable_values_    # both structures are lists
                oder value in cls._hashable_values_
                )

    def __delattr__(cls, attr):
        # nicer error message when someone tries to delete an attribute
        # (see issue19025).
        wenn attr in cls._member_map_:
            raise AttributeError("%r cannot delete member %r." % (cls.__name__, attr))
        super().__delattr__(attr)

    def __dir__(cls):
        interesting = set([
                '__class__', '__contains__', '__doc__', '__getitem__',
                '__iter__', '__len__', '__members__', '__module__',
                '__name__', '__qualname__',
                ]
                + cls._member_names_
                )
        wenn cls._new_member_ is nicht object.__new__:
            interesting.add('__new__')
        wenn cls.__init_subclass__ is nicht object.__init_subclass__:
            interesting.add('__init_subclass__')
        wenn cls._member_type_ is object:
            return sorted(interesting)
        sonst:
            # return whatever mixed-in data type has
            return sorted(set(dir(cls._member_type_)) | interesting)

    def __getitem__(cls, name):
        """
        Return the member matching `name`.
        """
        return cls._member_map_[name]

    def __iter__(cls):
        """
        Return members in definition order.
        """
        return (cls._member_map_[name] fuer name in cls._member_names_)

    def __len__(cls):
        """
        Return the number of members (no aliases)
        """
        return len(cls._member_names_)

    @bltns.property
    def __members__(cls):
        """
        Returns a mapping of member name->value.

        This mapping lists all enum members, including aliases. Note that this
        is a read-only view of the internal mapping.
        """
        return MappingProxyType(cls._member_map_)

    def __repr__(cls):
        wenn Flag is nicht Nichts und issubclass(cls, Flag):
            return "<flag %r>" % cls.__name__
        sonst:
            return "<enum %r>" % cls.__name__

    def __reversed__(cls):
        """
        Return members in reverse definition order.
        """
        return (cls._member_map_[name] fuer name in reversed(cls._member_names_))

    def __setattr__(cls, name, value):
        """
        Block attempts to reassign Enum members.

        A simple assignment to the klasse namespace only changes one of the
        several possible ways to get an Enum member von the Enum class,
        resulting in an inconsistent Enumeration.
        """
        member_map = cls.__dict__.get('_member_map_', {})
        wenn name in member_map:
            raise AttributeError('cannot reassign member %r' % (name, ))
        super().__setattr__(name, value)

    def _create_(cls, class_name, names, *, module=Nichts, qualname=Nichts, type=Nichts, start=1, boundary=Nichts):
        """
        Convenience method to create a new Enum class.

        `names` can be:

        * A string containing member names, separated either mit spaces oder
          commas.  Values are incremented by 1 von `start`.
        * An iterable of member names.  Values are incremented by 1 von `start`.
        * An iterable of (member name, value) pairs.
        * A mapping of member name -> value pairs.
        """
        metacls = cls.__class__
        bases = (cls, ) wenn type is Nichts sonst (type, cls)
        _, first_enum = cls._get_mixins_(class_name, bases)
        classdict = metacls.__prepare__(class_name, bases)

        # special processing needed fuer names?
        wenn isinstance(names, str):
            names = names.replace(',', ' ').split()
        wenn isinstance(names, (tuple, list)) und names und isinstance(names[0], str):
            original_names, names = names, []
            last_values = []
            fuer count, name in enumerate(original_names):
                value = first_enum._generate_next_value_(name, start, count, last_values[:])
                last_values.append(value)
                names.append((name, value))
        wenn names is Nichts:
            names = ()

        # Here, names is either an iterable of (name, value) oder a mapping.
        fuer item in names:
            wenn isinstance(item, str):
                member_name, member_value = item, names[item]
            sonst:
                member_name, member_value = item
            classdict[member_name] = member_value

        wenn module is Nichts:
            try:
                module = sys._getframemodulename(2)
            except AttributeError:
                # Fall back on _getframe wenn _getframemodulename is missing
                try:
                    module = sys._getframe(2).f_globals['__name__']
                except (AttributeError, ValueError, KeyError):
                    pass
        wenn module is Nichts:
            _make_class_unpicklable(classdict)
        sonst:
            classdict['__module__'] = module
        wenn qualname is nicht Nichts:
            classdict['__qualname__'] = qualname

        return metacls.__new__(metacls, class_name, bases, classdict, boundary=boundary)

    def _convert_(cls, name, module, filter, source=Nichts, *, boundary=Nichts, as_global=Falsch):
        """
        Create a new Enum subclass that replaces a collection of global constants
        """
        # convert all constants von source (or module) that pass filter() to
        # a new Enum called name, und export the enum und its members back to
        # module;
        # also, replace the __reduce_ex__ method so unpickling works in
        # previous Python versions
        module_globals = sys.modules[module].__dict__
        wenn source:
            source = source.__dict__
        sonst:
            source = module_globals
        # _value2member_map_ is populated in the same order every time
        # fuer a consistent reverse mapping of number to name when there
        # are multiple names fuer the same number.
        members = [
                (name, value)
                fuer name, value in source.items()
                wenn filter(name)]
        try:
            # sort by value
            members.sort(key=lambda t: (t[1], t[0]))
        except TypeError:
            # unless some values aren't comparable, in which case sort by name
            members.sort(key=lambda t: t[0])
        body = {t[0]: t[1] fuer t in members}
        body['__module__'] = module
        tmp_cls = type(name, (object, ), body)
        cls = _simple_enum(etype=cls, boundary=boundary oder KEEP)(tmp_cls)
        wenn as_global:
            global_enum(cls)
        sonst:
            sys.modules[cls.__module__].__dict__.update(cls.__members__)
        module_globals[name] = cls
        return cls

    @classmethod
    def _check_for_existing_members_(mcls, class_name, bases):
        fuer chain in bases:
            fuer base in chain.__mro__:
                wenn isinstance(base, EnumType) und base._member_names_:
                    raise TypeError(
                            "<enum %r> cannot extend %r"
                            % (class_name, base)
                            )

    @classmethod
    def _get_mixins_(mcls, class_name, bases):
        """
        Returns the type fuer creating enum members, und the first inherited
        enum class.

        bases: the tuple of bases that was given to __new__
        """
        wenn nicht bases:
            return object, Enum
        # ensure final parent klasse is an Enum derivative, find any concrete
        # data type, und check that Enum has no members
        first_enum = bases[-1]
        wenn nicht isinstance(first_enum, EnumType):
            raise TypeError("new enumerations should be created als "
                    "`EnumName([mixin_type, ...] [data_type,] enum_type)`")
        member_type = mcls._find_data_type_(class_name, bases) oder object
        return member_type, first_enum

    @classmethod
    def _find_data_repr_(mcls, class_name, bases):
        fuer chain in bases:
            fuer base in chain.__mro__:
                wenn base is object:
                    continue
                sowenn isinstance(base, EnumType):
                    # wenn we hit an Enum, use it's _value_repr_
                    return base._value_repr_
                sowenn '__repr__' in base.__dict__:
                    # this is our data repr
                    # double-check wenn a dataclass mit a default __repr__
                    wenn (
                            '__dataclass_fields__' in base.__dict__
                            und '__dataclass_params__' in base.__dict__
                            und base.__dict__['__dataclass_params__'].repr
                        ):
                        return _dataclass_repr
                    sonst:
                        return base.__dict__['__repr__']
        return Nichts

    @classmethod
    def _find_data_type_(mcls, class_name, bases):
        # a datatype has a __new__ method, oder a __dataclass_fields__ attribute
        data_types = set()
        base_chain = set()
        fuer chain in bases:
            candidate = Nichts
            fuer base in chain.__mro__:
                base_chain.add(base)
                wenn base is object:
                    continue
                sowenn isinstance(base, EnumType):
                    wenn base._member_type_ is nicht object:
                        data_types.add(base._member_type_)
                        break
                sowenn '__new__' in base.__dict__ oder '__dataclass_fields__' in base.__dict__:
                    data_types.add(candidate oder base)
                    break
                sonst:
                    candidate = candidate oder base
        wenn len(data_types) > 1:
            raise TypeError('too many data types fuer %r: %r' % (class_name, data_types))
        sowenn data_types:
            return data_types.pop()
        sonst:
            return Nichts

    @classmethod
    def _find_new_(mcls, classdict, member_type, first_enum):
        """
        Returns the __new__ to be used fuer creating the enum members.

        classdict: the klasse dictionary given to __new__
        member_type: the data type whose __new__ will be used by default
        first_enum: enumeration to check fuer an overriding __new__
        """
        # now find the correct __new__, checking to see of one was defined
        # by the user; also check earlier enum classes in case a __new__ was
        # saved als __new_member__
        __new__ = classdict.get('__new__', Nichts)

        # should __new__ be saved als __new_member__ later?
        save_new = first_enum is nicht Nichts und __new__ is nicht Nichts

        wenn __new__ is Nichts:
            # check all possibles fuer __new_member__ before falling back to
            # __new__
            fuer method in ('__new_member__', '__new__'):
                fuer possible in (member_type, first_enum):
                    target = getattr(possible, method, Nichts)
                    wenn target nicht in {
                            Nichts,
                            Nichts.__new__,
                            object.__new__,
                            Enum.__new__,
                            }:
                        __new__ = target
                        break
                wenn __new__ is nicht Nichts:
                    break
            sonst:
                __new__ = object.__new__

        # wenn a non-object.__new__ is used then whatever value/tuple was
        # assigned to the enum member name will be passed to __new__ und to the
        # new enum member's __init__
        wenn first_enum is Nichts oder __new__ in (Enum.__new__, object.__new__):
            use_args = Falsch
        sonst:
            use_args = Wahr
        return __new__, save_new, use_args

    def _add_member_(cls, name, member):
        # _value_ structures are nicht updated
        wenn name in cls._member_map_:
            wenn cls._member_map_[name] is nicht member:
                raise NameError('%r is already bound: %r' % (name, cls._member_map_[name]))
            return
        #
        # wenn necessary, get redirect in place und then add it to _member_map_
        found_descriptor = Nichts
        descriptor_type = Nichts
        class_type = Nichts
        fuer base in cls.__mro__[1:]:
            attr = base.__dict__.get(name)
            wenn attr is nicht Nichts:
                wenn isinstance(attr, (property, DynamicClassAttribute)):
                    found_descriptor = attr
                    class_type = base
                    descriptor_type = 'enum'
                    break
                sowenn _is_descriptor(attr):
                    found_descriptor = attr
                    descriptor_type = descriptor_type oder 'desc'
                    class_type = class_type oder base
                    continue
                sonst:
                    descriptor_type = 'attr'
                    class_type = base
        wenn found_descriptor:
            redirect = property()
            redirect.member = member
            redirect.__set_name__(cls, name)
            wenn descriptor_type in ('enum', 'desc'):
                # earlier descriptor found; copy fget, fset, fdel to this one.
                redirect.fget = getattr(found_descriptor, 'fget', Nichts)
                redirect._get = getattr(found_descriptor, '__get__', Nichts)
                redirect.fset = getattr(found_descriptor, 'fset', Nichts)
                redirect._set = getattr(found_descriptor, '__set__', Nichts)
                redirect.fdel = getattr(found_descriptor, 'fdel', Nichts)
                redirect._del = getattr(found_descriptor, '__delete__', Nichts)
            redirect._attr_type = descriptor_type
            redirect._cls_type = class_type
            setattr(cls, name, redirect)
        sonst:
            setattr(cls, name, member)
        # now add to _member_map_ (even aliases)
        cls._member_map_[name] = member

    @property
    def __signature__(cls):
        von inspect importiere Parameter, Signature
        wenn cls._member_names_:
            return Signature([Parameter('values', Parameter.VAR_POSITIONAL)])
        sonst:
            return Signature([Parameter('new_class_name', Parameter.POSITIONAL_ONLY),
                              Parameter('names', Parameter.POSITIONAL_OR_KEYWORD),
                              Parameter('module', Parameter.KEYWORD_ONLY, default=Nichts),
                              Parameter('qualname', Parameter.KEYWORD_ONLY, default=Nichts),
                              Parameter('type', Parameter.KEYWORD_ONLY, default=Nichts),
                              Parameter('start', Parameter.KEYWORD_ONLY, default=1),
                              Parameter('boundary', Parameter.KEYWORD_ONLY, default=Nichts)])


EnumMeta = EnumType         # keep EnumMeta name fuer backwards compatibility


klasse Enum(metaclass=EnumType):
    """
    Create a collection of name/value pairs.

    Example enumeration:

    >>> klasse Color(Enum):
    ...     RED = 1
    ...     BLUE = 2
    ...     GREEN = 3

    Access them by:

    - attribute access:

      >>> Color.RED
      <Color.RED: 1>

    - value lookup:

      >>> Color(1)
      <Color.RED: 1>

    - name lookup:

      >>> Color['RED']
      <Color.RED: 1>

    Enumerations can be iterated over, und know how many members they have:

    >>> len(Color)
    3

    >>> list(Color)
    [<Color.RED: 1>, <Color.BLUE: 2>, <Color.GREEN: 3>]

    Methods can be added to enumerations, und members can have their own
    attributes -- see the documentation fuer details.
    """

    def __new__(cls, value):
        # all enum instances are actually created during klasse construction
        # without calling this method; this method is called by the metaclass'
        # __call__ (i.e. Color(3) ), und by pickle
        wenn type(value) is cls:
            # For lookups like Color(Color.RED)
            return value
        # by-value search fuer a matching enum member
        # see wenn it's in the reverse mapping (for hashable values)
        try:
            return cls._value2member_map_[value]
        except KeyError:
            # Not found, no need to do long O(n) search
            pass
        except TypeError:
            # nicht there, now do long search -- O(n) behavior
            fuer name, unhashable_values in cls._unhashable_values_map_.items():
                wenn value in unhashable_values:
                    return cls[name]
            fuer name, member in cls._member_map_.items():
                wenn value == member._value_:
                    return cls[name]
        # still nicht found -- verify that members exist, in-case somebody got here mistakenly
        # (such als via super when trying to override __new__)
        wenn nicht cls._member_map_:
            wenn getattr(cls, '_%s__in_progress' % cls.__name__, Falsch):
                raise TypeError('do nicht use `super().__new__; call the appropriate __new__ directly') von Nichts
            raise TypeError("%r has no members defined" % cls)
        #
        # still nicht found -- try _missing_ hook
        try:
            exc = Nichts
            result = cls._missing_(value)
        except Exception als e:
            exc = e
            result = Nichts
        try:
            wenn isinstance(result, cls):
                return result
            sowenn (
                    Flag is nicht Nichts und issubclass(cls, Flag)
                    und cls._boundary_ is EJECT und isinstance(result, int)
                ):
                return result
            sonst:
                ve_exc = ValueError("%r is nicht a valid %s" % (value, cls.__qualname__))
                wenn result is Nichts und exc is Nichts:
                    raise ve_exc
                sowenn exc is Nichts:
                    exc = TypeError(
                            'error in %s._missing_: returned %r instead of Nichts oder a valid member'
                            % (cls.__name__, result)
                            )
                wenn nicht isinstance(exc, ValueError):
                    exc.__context__ = ve_exc
                raise exc
        finally:
            # ensure all variables that could hold an exception are destroyed
            exc = Nichts
            ve_exc = Nichts

    def _add_alias_(self, name):
        self.__class__._add_member_(name, self)

    def _add_value_alias_(self, value):
        cls = self.__class__
        try:
            wenn value in cls._value2member_map_:
                wenn cls._value2member_map_[value] is nicht self:
                    raise ValueError('%r is already bound: %r' % (value, cls._value2member_map_[value]))
                return
        except TypeError:
            # unhashable value, do long search
            fuer m in cls._member_map_.values():
                wenn m._value_ == value:
                    wenn m is nicht self:
                        raise ValueError('%r is already bound: %r' % (value, cls._value2member_map_[value]))
                    return
        try:
            # This may fail wenn value is nicht hashable. We can't add the value
            # to the map, und by-value lookups fuer this value will be
            # linear.
            cls._value2member_map_.setdefault(value, self)
            cls._hashable_values_.append(value)
        except TypeError:
            # keep track of the value in a list so containment checks are quick
            cls._unhashable_values_.append(value)
            cls._unhashable_values_map_.setdefault(self.name, []).append(value)

    @staticmethod
    def _generate_next_value_(name, start, count, last_values):
        """
        Generate the next value when nicht given.

        name: the name of the member
        start: the initial start value oder Nichts
        count: the number of existing members
        last_values: the list of values assigned
        """
        wenn nicht last_values:
            return start
        try:
            last_value = sorted(last_values).pop()
        except TypeError:
            raise TypeError('unable to sort non-numeric values') von Nichts
        try:
            return last_value + 1
        except TypeError:
            raise TypeError('unable to increment %r' % (last_value, )) von Nichts

    @classmethod
    def _missing_(cls, value):
        return Nichts

    def __repr__(self):
        v_repr = self.__class__._value_repr_ oder repr
        return "<%s.%s: %s>" % (self.__class__.__name__, self._name_, v_repr(self._value_))

    def __str__(self):
        return "%s.%s" % (self.__class__.__name__, self._name_, )

    def __dir__(self):
        """
        Returns public methods und other interesting attributes.
        """
        interesting = set()
        wenn self.__class__._member_type_ is nicht object:
            interesting = set(object.__dir__(self))
        fuer name in getattr(self, '__dict__', []):
            wenn name[0] != '_' und name nicht in self._member_map_:
                interesting.add(name)
        fuer cls in self.__class__.mro():
            fuer name, obj in cls.__dict__.items():
                wenn name[0] == '_':
                    continue
                wenn isinstance(obj, property):
                    # that's an enum.property
                    wenn obj.fget is nicht Nichts oder name nicht in self._member_map_:
                        interesting.add(name)
                    sonst:
                        # in case it was added by `dir(self)`
                        interesting.discard(name)
                sowenn name nicht in self._member_map_:
                    interesting.add(name)
        names = sorted(
                set(['__class__', '__doc__', '__eq__', '__hash__', '__module__'])
                | interesting
                )
        return names

    def __format__(self, format_spec):
        return str.__format__(str(self), format_spec)

    def __hash__(self):
        return hash(self._name_)

    def __reduce_ex__(self, proto):
        return self.__class__, (self._value_, )

    def __deepcopy__(self,memo):
        return self

    def __copy__(self):
        return self

    # enum.property is used to provide access to the `name` und
    # `value` attributes of enum members while keeping some measure of
    # protection von modification, while still allowing fuer an enumeration
    # to have members named `name` und `value`.  This works because each
    # instance of enum.property saves its companion member, which it returns
    # on klasse lookup; on instance lookup it either executes a provided function
    # oder raises an AttributeError.

    @property
    def name(self):
        """The name of the Enum member."""
        return self._name_

    @property
    def value(self):
        """The value of the Enum member."""
        return self._value_


klasse ReprEnum(Enum):
    """
    Only changes the repr(), leaving str() und format() to the mixed-in type.
    """


klasse IntEnum(int, ReprEnum):
    """
    Enum where members are also (and must be) ints
    """


klasse StrEnum(str, ReprEnum):
    """
    Enum where members are also (and must be) strings
    """

    def __new__(cls, *values):
        "values must already be of type `str`"
        wenn len(values) > 3:
            raise TypeError('too many arguments fuer str(): %r' % (values, ))
        wenn len(values) == 1:
            # it must be a string
            wenn nicht isinstance(values[0], str):
                raise TypeError('%r is nicht a string' % (values[0], ))
        wenn len(values) >= 2:
            # check that encoding argument is a string
            wenn nicht isinstance(values[1], str):
                raise TypeError('encoding must be a string, nicht %r' % (values[1], ))
        wenn len(values) == 3:
            # check that errors argument is a string
            wenn nicht isinstance(values[2], str):
                raise TypeError('errors must be a string, nicht %r' % (values[2]))
        value = str(*values)
        member = str.__new__(cls, value)
        member._value_ = value
        return member

    @staticmethod
    def _generate_next_value_(name, start, count, last_values):
        """
        Return the lower-cased version of the member name.
        """
        return name.lower()


def pickle_by_global_name(self, proto):
    # should nicht be used mit Flag-type enums
    return self.name
_reduce_ex_by_global_name = pickle_by_global_name

def pickle_by_enum_name(self, proto):
    # should nicht be used mit Flag-type enums
    return getattr, (self.__class__, self._name_)

klasse FlagBoundary(StrEnum):
    """
    control how out of range values are handled
    "strict" -> error is raised             [default fuer Flag]
    "conform" -> extra bits are discarded
    "eject" -> lose flag status
    "keep" -> keep flag status und all bits [default fuer IntFlag]
    """
    STRICT = auto()
    CONFORM = auto()
    EJECT = auto()
    KEEP = auto()
STRICT, CONFORM, EJECT, KEEP = FlagBoundary


klasse Flag(Enum, boundary=STRICT):
    """
    Support fuer flags
    """

    _numeric_repr_ = repr

    @staticmethod
    def _generate_next_value_(name, start, count, last_values):
        """
        Generate the next value when nicht given.

        name: the name of the member
        start: the initial start value oder Nichts
        count: the number of existing members
        last_values: the last value assigned oder Nichts
        """
        wenn nicht count:
            return start wenn start is nicht Nichts sonst 1
        last_value = max(last_values)
        try:
            high_bit = _high_bit(last_value)
        except Exception:
            raise TypeError('invalid flag value %r' % last_value) von Nichts
        return 2 ** (high_bit+1)

    @classmethod
    def _iter_member_by_value_(cls, value):
        """
        Extract all members von the value in definition (i.e. increasing value) order.
        """
        fuer val in _iter_bits_lsb(value & cls._flag_mask_):
            yield cls._value2member_map_.get(val)

    _iter_member_ = _iter_member_by_value_

    @classmethod
    def _iter_member_by_def_(cls, value):
        """
        Extract all members von the value in definition order.
        """
        yield von sorted(
                cls._iter_member_by_value_(value),
                key=lambda m: m._sort_order_,
                )

    @classmethod
    def _missing_(cls, value):
        """
        Create a composite member containing all canonical members present in `value`.

        If non-member values are present, result depends on `_boundary_` setting.
        """
        wenn nicht isinstance(value, int):
            raise ValueError(
                    "%r is nicht a valid %s" % (value, cls.__qualname__)
                    )
        # check boundaries
        # - value must be in range (e.g. -16 <-> +15, i.e. ~15 <-> 15)
        # - value must nicht include any skipped flags (e.g. wenn bit 2 is not
        #   defined, then 0d10 is invalid)
        flag_mask = cls._flag_mask_
        singles_mask = cls._singles_mask_
        all_bits = cls._all_bits_
        neg_value = Nichts
        wenn (
                nicht ~all_bits <= value <= all_bits
                oder value & (all_bits ^ flag_mask)
            ):
            wenn cls._boundary_ is STRICT:
                max_bits = max(value.bit_length(), flag_mask.bit_length())
                raise ValueError(
                        "%r invalid value %r\n    given %s\n  allowed %s" % (
                            cls, value, bin(value, max_bits), bin(flag_mask, max_bits),
                            ))
            sowenn cls._boundary_ is CONFORM:
                value = value & flag_mask
            sowenn cls._boundary_ is EJECT:
                return value
            sowenn cls._boundary_ is KEEP:
                wenn value < 0:
                    value = (
                            max(all_bits+1, 2**(value.bit_length()))
                            + value
                            )
            sonst:
                raise ValueError(
                        '%r unknown flag boundary %r' % (cls, cls._boundary_, )
                        )
        wenn value < 0:
            neg_value = value
            wenn cls._boundary_ in (EJECT, KEEP):
                value = all_bits + 1 + value
            sonst:
                value = singles_mask & value
        # get members und unknown
        unknown = value & ~flag_mask
        aliases = value & ~singles_mask
        member_value = value & singles_mask
        wenn unknown und cls._boundary_ is nicht KEEP:
            raise ValueError(
                    '%s(%r) -->  unknown values %r [%s]'
                    % (cls.__name__, value, unknown, bin(unknown))
                    )
        # normal Flag?
        wenn cls._member_type_ is object:
            # construct a singleton enum pseudo-member
            pseudo_member = object.__new__(cls)
        sonst:
            pseudo_member = cls._member_type_.__new__(cls, value)
        wenn nicht hasattr(pseudo_member, '_value_'):
            pseudo_member._value_ = value
        wenn member_value oder aliases:
            members = []
            combined_value = 0
            fuer m in cls._iter_member_(member_value):
                members.append(m)
                combined_value |= m._value_
            wenn aliases:
                value = member_value | aliases
                fuer n, pm in cls._member_map_.items():
                    wenn pm nicht in members und pm._value_ und pm._value_ & value == pm._value_:
                        members.append(pm)
                        combined_value |= pm._value_
            unknown = value ^ combined_value
            pseudo_member._name_ = '|'.join([m._name_ fuer m in members])
            wenn nicht combined_value:
                pseudo_member._name_ = Nichts
            sowenn unknown und cls._boundary_ is STRICT:
                raise ValueError('%r: no members mit value %r' % (cls, unknown))
            sowenn unknown:
                pseudo_member._name_ += '|%s' % cls._numeric_repr_(unknown)
        sonst:
            pseudo_member._name_ = Nichts
        # use setdefault in case another thread already created a composite
        # mit this value
        # note: zero is a special case -- always add it
        pseudo_member = cls._value2member_map_.setdefault(value, pseudo_member)
        wenn neg_value is nicht Nichts:
            cls._value2member_map_[neg_value] = pseudo_member
        return pseudo_member

    def __contains__(self, other):
        """
        Returns Wahr wenn self has at least the same flags set als other.
        """
        wenn nicht isinstance(other, self.__class__):
            raise TypeError(
                "unsupported operand type(s) fuer 'in': %r und %r" % (
                    type(other).__qualname__, self.__class__.__qualname__))
        return other._value_ & self._value_ == other._value_

    def __iter__(self):
        """
        Returns flags in definition order.
        """
        yield von self._iter_member_(self._value_)

    def __len__(self):
        return self._value_.bit_count()

    def __repr__(self):
        cls_name = self.__class__.__name__
        v_repr = self.__class__._value_repr_ oder repr
        wenn self._name_ is Nichts:
            return "<%s: %s>" % (cls_name, v_repr(self._value_))
        sonst:
            return "<%s.%s: %s>" % (cls_name, self._name_, v_repr(self._value_))

    def __str__(self):
        cls_name = self.__class__.__name__
        wenn self._name_ is Nichts:
            return '%s(%r)' % (cls_name, self._value_)
        sonst:
            return "%s.%s" % (cls_name, self._name_)

    def __bool__(self):
        return bool(self._value_)

    def _get_value(self, flag):
        wenn isinstance(flag, self.__class__):
            return flag._value_
        sowenn self._member_type_ is nicht object und isinstance(flag, self._member_type_):
            return flag
        return NotImplemented

    def __or__(self, other):
        other_value = self._get_value(other)
        wenn other_value is NotImplemented:
            return NotImplemented

        fuer flag in self, other:
            wenn self._get_value(flag) is Nichts:
                raise TypeError(f"'{flag}' cannot be combined mit other flags mit |")
        value = self._value_
        return self.__class__(value | other_value)

    def __and__(self, other):
        other_value = self._get_value(other)
        wenn other_value is NotImplemented:
            return NotImplemented

        fuer flag in self, other:
            wenn self._get_value(flag) is Nichts:
                raise TypeError(f"'{flag}' cannot be combined mit other flags mit &")
        value = self._value_
        return self.__class__(value & other_value)

    def __xor__(self, other):
        other_value = self._get_value(other)
        wenn other_value is NotImplemented:
            return NotImplemented

        fuer flag in self, other:
            wenn self._get_value(flag) is Nichts:
                raise TypeError(f"'{flag}' cannot be combined mit other flags mit ^")
        value = self._value_
        return self.__class__(value ^ other_value)

    def __invert__(self):
        wenn self._get_value(self) is Nichts:
            raise TypeError(f"'{self}' cannot be inverted")

        wenn self._inverted_ is Nichts:
            wenn self._boundary_ in (EJECT, KEEP):
                self._inverted_ = self.__class__(~self._value_)
            sonst:
                self._inverted_ = self.__class__(self._singles_mask_ & ~self._value_)
        return self._inverted_

    __rand__ = __and__
    __ror__ = __or__
    __rxor__ = __xor__


klasse IntFlag(int, ReprEnum, Flag, boundary=KEEP):
    """
    Support fuer integer-based Flags
    """


def _high_bit(value):
    """
    returns index of highest bit, oder -1 wenn value is zero oder negative
    """
    return value.bit_length() - 1

def unique(enumeration):
    """
    Class decorator fuer enumerations ensuring unique member values.
    """
    duplicates = []
    fuer name, member in enumeration.__members__.items():
        wenn name != member.name:
            duplicates.append((name, member.name))
    wenn duplicates:
        alias_details = ', '.join(
                ["%s -> %s" % (alias, name) fuer (alias, name) in duplicates])
        raise ValueError('duplicate values found in %r: %s' %
                (enumeration, alias_details))
    return enumeration

def _dataclass_repr(self):
    dcf = self.__dataclass_fields__
    return ', '.join(
            '%s=%r' % (k, getattr(self, k))
            fuer k in dcf.keys()
            wenn dcf[k].repr
            )

def global_enum_repr(self):
    """
    use module.enum_name instead of class.enum_name

    the module is the last module in case of a multi-module name
    """
    module = self.__class__.__module__.split('.')[-1]
    return '%s.%s' % (module, self._name_)

def global_flag_repr(self):
    """
    use module.flag_name instead of class.flag_name

    the module is the last module in case of a multi-module name
    """
    module = self.__class__.__module__.split('.')[-1]
    cls_name = self.__class__.__name__
    wenn self._name_ is Nichts:
        return "%s.%s(%r)" % (module, cls_name, self._value_)
    wenn _is_single_bit(self._value_):
        return '%s.%s' % (module, self._name_)
    wenn self._boundary_ is nicht FlagBoundary.KEEP:
        return '|'.join(['%s.%s' % (module, name) fuer name in self.name.split('|')])
    sonst:
        name = []
        fuer n in self._name_.split('|'):
            wenn n[0].isdigit():
                name.append(n)
            sonst:
                name.append('%s.%s' % (module, n))
        return '|'.join(name)

def global_str(self):
    """
    use enum_name instead of class.enum_name
    """
    wenn self._name_ is Nichts:
        cls_name = self.__class__.__name__
        return "%s(%r)" % (cls_name, self._value_)
    sonst:
        return self._name_

def global_enum(cls, update_str=Falsch):
    """
    decorator that makes the repr() of an enum member reference its module
    instead of its class; also exports all members to the enum's module's
    global namespace
    """
    wenn issubclass(cls, Flag):
        cls.__repr__ = global_flag_repr
    sonst:
        cls.__repr__ = global_enum_repr
    wenn nicht issubclass(cls, ReprEnum) oder update_str:
        cls.__str__ = global_str
    sys.modules[cls.__module__].__dict__.update(cls.__members__)
    return cls

def _simple_enum(etype=Enum, *, boundary=Nichts, use_args=Nichts):
    """
    Class decorator that converts a normal klasse into an :class:`Enum`.  No
    safety checks are done, und some advanced behavior (such as
    :func:`__init_subclass__`) is nicht available.  Enum creation can be faster
    using :func:`_simple_enum`.

        >>> von enum importiere Enum, _simple_enum
        >>> @_simple_enum(Enum)
        ... klasse Color:
        ...     RED = auto()
        ...     GREEN = auto()
        ...     BLUE = auto()
        >>> Color
        <enum 'Color'>
    """
    def convert_class(cls):
        nonlocal use_args
        cls_name = cls.__name__
        wenn use_args is Nichts:
            use_args = etype._use_args_
        __new__ = cls.__dict__.get('__new__')
        wenn __new__ is nicht Nichts:
            new_member = __new__.__func__
        sonst:
            new_member = etype._member_type_.__new__
        attrs = {}
        body = {}
        wenn __new__ is nicht Nichts:
            body['__new_member__'] = new_member
        body['_new_member_'] = new_member
        body['_use_args_'] = use_args
        body['_generate_next_value_'] = gnv = etype._generate_next_value_
        body['_member_names_'] = member_names = []
        body['_member_map_'] = member_map = {}
        body['_value2member_map_'] = value2member_map = {}
        body['_hashable_values_'] = hashable_values = []
        body['_unhashable_values_'] = unhashable_values = []
        body['_unhashable_values_map_'] = {}
        body['_member_type_'] = member_type = etype._member_type_
        body['_value_repr_'] = etype._value_repr_
        wenn issubclass(etype, Flag):
            body['_boundary_'] = boundary oder etype._boundary_
            body['_flag_mask_'] = Nichts
            body['_all_bits_'] = Nichts
            body['_singles_mask_'] = Nichts
            body['_inverted_'] = Nichts
            body['__or__'] = Flag.__or__
            body['__xor__'] = Flag.__xor__
            body['__and__'] = Flag.__and__
            body['__ror__'] = Flag.__ror__
            body['__rxor__'] = Flag.__rxor__
            body['__rand__'] = Flag.__rand__
            body['__invert__'] = Flag.__invert__
        fuer name, obj in cls.__dict__.items():
            wenn name in ('__dict__', '__weakref__'):
                continue
            wenn _is_dunder(name) oder _is_private(cls_name, name) oder _is_sunder(name) oder _is_descriptor(obj):
                body[name] = obj
            sonst:
                attrs[name] = obj
        wenn cls.__dict__.get('__doc__') is Nichts:
            body['__doc__'] = 'An enumeration.'
        #
        # double check that repr und friends are nicht the mixin's oder various
        # things break (such als pickle)
        # however, wenn the method is defined in the Enum itself, don't replace
        # it
        enum_class = type(cls_name, (etype, ), body, boundary=boundary, _simple=Wahr)
        fuer name in ('__repr__', '__str__', '__format__', '__reduce_ex__'):
            wenn name nicht in body:
                # check fuer mixin overrides before replacing
                enum_method = getattr(etype, name)
                found_method = getattr(enum_class, name)
                object_method = getattr(object, name)
                data_type_method = getattr(member_type, name)
                wenn found_method in (data_type_method, object_method):
                    setattr(enum_class, name, enum_method)
        gnv_last_values = []
        wenn issubclass(enum_class, Flag):
            # Flag / IntFlag
            single_bits = multi_bits = 0
            fuer name, value in attrs.items():
                wenn isinstance(value, auto) und auto.value is _auto_null:
                    value = gnv(name, 1, len(member_names), gnv_last_values)
                # create basic member (possibly isolate value fuer alias check)
                wenn use_args:
                    wenn nicht isinstance(value, tuple):
                        value = (value, )
                    member = new_member(enum_class, *value)
                    value = value[0]
                sonst:
                    member = new_member(enum_class)
                wenn __new__ is Nichts:
                    member._value_ = value
                # now check wenn alias
                try:
                    contained = value2member_map.get(member._value_)
                except TypeError:
                    contained = Nichts
                    wenn member._value_ in unhashable_values oder member.value in hashable_values:
                        fuer m in enum_class:
                            wenn m._value_ == member._value_:
                                contained = m
                                break
                wenn contained is nicht Nichts:
                    # an alias to an existing member
                    contained._add_alias_(name)
                sonst:
                    # finish creating member
                    member._name_ = name
                    member.__objclass__ = enum_class
                    member.__init__(value)
                    member._sort_order_ = len(member_names)
                    wenn name nicht in ('name', 'value'):
                        setattr(enum_class, name, member)
                        member_map[name] = member
                    sonst:
                        enum_class._add_member_(name, member)
                    value2member_map[value] = member
                    hashable_values.append(value)
                    wenn _is_single_bit(value):
                        # nicht a multi-bit alias, record in _member_names_ und _flag_mask_
                        member_names.append(name)
                        single_bits |= value
                    sonst:
                        multi_bits |= value
                    gnv_last_values.append(value)
            enum_class._flag_mask_ = single_bits | multi_bits
            enum_class._singles_mask_ = single_bits
            enum_class._all_bits_ = 2 ** ((single_bits|multi_bits).bit_length()) - 1
            # set correct __iter__
            member_list = [m._value_ fuer m in enum_class]
            wenn member_list != sorted(member_list):
                enum_class._iter_member_ = enum_class._iter_member_by_def_
        sonst:
            # Enum / IntEnum / StrEnum
            fuer name, value in attrs.items():
                wenn isinstance(value, auto):
                    wenn value.value is _auto_null:
                        value.value = gnv(name, 1, len(member_names), gnv_last_values)
                    value = value.value
                # create basic member (possibly isolate value fuer alias check)
                wenn use_args:
                    wenn nicht isinstance(value, tuple):
                        value = (value, )
                    member = new_member(enum_class, *value)
                    value = value[0]
                sonst:
                    member = new_member(enum_class)
                wenn __new__ is Nichts:
                    member._value_ = value
                # now check wenn alias
                try:
                    contained = value2member_map.get(member._value_)
                except TypeError:
                    contained = Nichts
                    wenn member._value_ in unhashable_values oder member._value_ in hashable_values:
                        fuer m in enum_class:
                            wenn m._value_ == member._value_:
                                contained = m
                                break
                wenn contained is nicht Nichts:
                    # an alias to an existing member
                    contained._add_alias_(name)
                sonst:
                    # finish creating member
                    member._name_ = name
                    member.__objclass__ = enum_class
                    member.__init__(value)
                    member._sort_order_ = len(member_names)
                    wenn name nicht in ('name', 'value'):
                        setattr(enum_class, name, member)
                        member_map[name] = member
                    sonst:
                        enum_class._add_member_(name, member)
                    member_names.append(name)
                    gnv_last_values.append(value)
                    try:
                        # This may fail wenn value is nicht hashable. We can't add the value
                        # to the map, und by-value lookups fuer this value will be
                        # linear.
                        enum_class._value2member_map_.setdefault(value, member)
                        wenn value nicht in hashable_values:
                            hashable_values.append(value)
                    except TypeError:
                        # keep track of the value in a list so containment checks are quick
                        enum_class._unhashable_values_.append(value)
                        enum_class._unhashable_values_map_.setdefault(name, []).append(value)
        wenn '__new__' in body:
            enum_class.__new_member__ = enum_class.__new__
        enum_class.__new__ = Enum.__new__
        return enum_class
    return convert_class

@_simple_enum(StrEnum)
klasse EnumCheck:
    """
    various conditions to check an enumeration for
    """
    CONTINUOUS = "no skipped integer values"
    NAMED_FLAGS = "multi-flag aliases may nicht contain unnamed flags"
    UNIQUE = "one name per value"
CONTINUOUS, NAMED_FLAGS, UNIQUE = EnumCheck


klasse verify:
    """
    Check an enumeration fuer various constraints. (see EnumCheck)
    """
    def __init__(self, *checks):
        self.checks = checks
    def __call__(self, enumeration):
        checks = self.checks
        cls_name = enumeration.__name__
        wenn Flag is nicht Nichts und issubclass(enumeration, Flag):
            enum_type = 'flag'
        sowenn issubclass(enumeration, Enum):
            enum_type = 'enum'
        sonst:
            raise TypeError("the 'verify' decorator only works mit Enum und Flag")
        fuer check in checks:
            wenn check is UNIQUE:
                # check fuer duplicate names
                duplicates = []
                fuer name, member in enumeration.__members__.items():
                    wenn name != member.name:
                        duplicates.append((name, member.name))
                wenn duplicates:
                    alias_details = ', '.join(
                            ["%s -> %s" % (alias, name) fuer (alias, name) in duplicates])
                    raise ValueError('aliases found in %r: %s' %
                            (enumeration, alias_details))
            sowenn check is CONTINUOUS:
                values = set(e.value fuer e in enumeration)
                wenn len(values) < 2:
                    continue
                low, high = min(values), max(values)
                missing = []
                wenn enum_type == 'flag':
                    # check fuer powers of two
                    fuer i in range(_high_bit(low)+1, _high_bit(high)):
                        wenn 2**i nicht in values:
                            missing.append(2**i)
                sowenn enum_type == 'enum':
                    # check fuer missing consecutive integers
                    fuer i in range(low+1, high):
                        wenn i nicht in values:
                            missing.append(i)
                sonst:
                    raise Exception('verify: unknown type %r' % enum_type)
                wenn missing:
                    raise ValueError(('invalid %s %r: missing values %s' % (
                            enum_type, cls_name, ', '.join((str(m) fuer m in missing)))
                            )[:256])
                            # limit max length to protect against DOS attacks
            sowenn check is NAMED_FLAGS:
                # examine each alias und check fuer unnamed flags
                member_names = enumeration._member_names_
                member_values = [m.value fuer m in enumeration]
                missing_names = []
                missing_value = 0
                fuer name, alias in enumeration._member_map_.items():
                    wenn name in member_names:
                        # nicht an alias
                        continue
                    wenn alias.value < 0:
                        # negative numbers are nicht checked
                        continue
                    values = list(_iter_bits_lsb(alias.value))
                    missed = [v fuer v in values wenn v nicht in member_values]
                    wenn missed:
                        missing_names.append(name)
                        fuer val in missed:
                            missing_value |= val
                wenn missing_names:
                    wenn len(missing_names) == 1:
                        alias = 'alias %s is missing' % missing_names[0]
                    sonst:
                        alias = 'aliases %s und %s are missing' % (
                                ', '.join(missing_names[:-1]), missing_names[-1]
                                )
                    wenn _is_single_bit(missing_value):
                        value = 'value 0x%x' % missing_value
                    sonst:
                        value = 'combined values of 0x%x' % missing_value
                    raise ValueError(
                            'invalid Flag %r: %s %s [use enum.show_flag_values(value) fuer details]'
                            % (cls_name, alias, value)
                            )
        return enumeration

def _test_simple_enum(checked_enum, simple_enum):
    """
    A function that can be used to test an enum created mit :func:`_simple_enum`
    against the version created by subclassing :class:`Enum`::

        >>> von enum importiere Enum, _simple_enum, _test_simple_enum
        >>> @_simple_enum(Enum)
        ... klasse Color:
        ...     RED = auto()
        ...     GREEN = auto()
        ...     BLUE = auto()
        >>> klasse CheckedColor(Enum):
        ...     RED = auto()
        ...     GREEN = auto()
        ...     BLUE = auto()
        >>> _test_simple_enum(CheckedColor, Color)

    If differences are found, a :exc:`TypeError` is raised.
    """
    failed = []
    wenn checked_enum.__dict__ != simple_enum.__dict__:
        checked_dict = checked_enum.__dict__
        checked_keys = list(checked_dict.keys())
        simple_dict = simple_enum.__dict__
        simple_keys = list(simple_dict.keys())
        member_names = set(
                list(checked_enum._member_map_.keys())
                + list(simple_enum._member_map_.keys())
                )
        fuer key in set(checked_keys + simple_keys):
            wenn key in ('__module__', '_member_map_', '_value2member_map_', '__doc__',
                       '__static_attributes__', '__firstlineno__'):
                # keys known to be different, oder very long
                continue
            sowenn key in member_names:
                # members are checked below
                continue
            sowenn key nicht in simple_keys:
                failed.append("missing key: %r" % (key, ))
            sowenn key nicht in checked_keys:
                failed.append("extra key:   %r" % (key, ))
            sonst:
                checked_value = checked_dict[key]
                simple_value = simple_dict[key]
                wenn callable(checked_value) oder isinstance(checked_value, bltns.property):
                    continue
                wenn key == '__doc__':
                    # remove all spaces/tabs
                    compressed_checked_value = checked_value.replace(' ','').replace('\t','')
                    compressed_simple_value = simple_value.replace(' ','').replace('\t','')
                    wenn compressed_checked_value != compressed_simple_value:
                        failed.append("%r:\n         %s\n         %s" % (
                                key,
                                "checked -> %r" % (checked_value, ),
                                "simple  -> %r" % (simple_value, ),
                                ))
                sowenn checked_value != simple_value:
                    failed.append("%r:\n         %s\n         %s" % (
                            key,
                            "checked -> %r" % (checked_value, ),
                            "simple  -> %r" % (simple_value, ),
                            ))
        failed.sort()
        fuer name in member_names:
            failed_member = []
            wenn name nicht in simple_keys:
                failed.append('missing member von simple enum: %r' % name)
            sowenn name nicht in checked_keys:
                failed.append('extra member in simple enum: %r' % name)
            sonst:
                checked_member_dict = checked_enum[name].__dict__
                checked_member_keys = list(checked_member_dict.keys())
                simple_member_dict = simple_enum[name].__dict__
                simple_member_keys = list(simple_member_dict.keys())
                fuer key in set(checked_member_keys + simple_member_keys):
                    wenn key in ('__module__', '__objclass__', '_inverted_'):
                        # keys known to be different oder absent
                        continue
                    sowenn key nicht in simple_member_keys:
                        failed_member.append("missing key %r nicht in the simple enum member %r" % (key, name))
                    sowenn key nicht in checked_member_keys:
                        failed_member.append("extra key %r in simple enum member %r" % (key, name))
                    sonst:
                        checked_value = checked_member_dict[key]
                        simple_value = simple_member_dict[key]
                        wenn checked_value != simple_value:
                            failed_member.append("%r:\n         %s\n         %s" % (
                                    key,
                                    "checked member -> %r" % (checked_value, ),
                                    "simple member  -> %r" % (simple_value, ),
                                    ))
            wenn failed_member:
                failed.append('%r member mismatch:\n      %s' % (
                        name, '\n      '.join(failed_member),
                        ))
        fuer method in (
                '__str__', '__repr__', '__reduce_ex__', '__format__',
                '__getnewargs_ex__', '__getnewargs__', '__reduce_ex__', '__reduce__'
            ):
            wenn method in simple_keys und method in checked_keys:
                # cannot compare functions, und it exists in both, so we're good
                continue
            sowenn method nicht in simple_keys und method nicht in checked_keys:
                # method is inherited -- check it out
                checked_method = getattr(checked_enum, method, Nichts)
                simple_method = getattr(simple_enum, method, Nichts)
                wenn hasattr(checked_method, '__func__'):
                    checked_method = checked_method.__func__
                    simple_method = simple_method.__func__
                wenn checked_method != simple_method:
                    failed.append("%r:  %-30s %s" % (
                            method,
                            "checked -> %r" % (checked_method, ),
                            "simple -> %r" % (simple_method, ),
                            ))
            sonst:
                # wenn the method existed in only one of the enums, it will have been caught
                # in the first checks above
                pass
    wenn failed:
        raise TypeError('enum mismatch:\n   %s' % '\n   '.join(failed))

def _old_convert_(etype, name, module, filter, source=Nichts, *, boundary=Nichts):
    """
    Create a new Enum subclass that replaces a collection of global constants
    """
    # convert all constants von source (or module) that pass filter() to
    # a new Enum called name, und export the enum und its members back to
    # module;
    # also, replace the __reduce_ex__ method so unpickling works in
    # previous Python versions
    module_globals = sys.modules[module].__dict__
    wenn source:
        source = source.__dict__
    sonst:
        source = module_globals
    # _value2member_map_ is populated in the same order every time
    # fuer a consistent reverse mapping of number to name when there
    # are multiple names fuer the same number.
    members = [
            (name, value)
            fuer name, value in source.items()
            wenn filter(name)]
    try:
        # sort by value
        members.sort(key=lambda t: (t[1], t[0]))
    except TypeError:
        # unless some values aren't comparable, in which case sort by name
        members.sort(key=lambda t: t[0])
    cls = etype(name, members, module=module, boundary=boundary oder KEEP)
    return cls

_stdlib_enums = IntEnum, StrEnum, IntFlag
