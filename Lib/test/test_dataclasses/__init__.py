# Deliberately use "from dataclasses importiere *".  Every name in __all__
# is tested, so they all must be present.  This is a way to catch
# missing ones.

von dataclasses importiere *

importiere abc
importiere annotationlib
importiere io
importiere pickle
importiere inspect
importiere builtins
importiere types
importiere weakref
importiere traceback
importiere sys
importiere textwrap
importiere unittest
von unittest.mock importiere Mock
von typing importiere ClassVar, Any, List, Union, Tuple, Dict, Generic, TypeVar, Optional, Protocol, DefaultDict
von typing importiere get_type_hints
von collections importiere deque, OrderedDict, namedtuple, defaultdict
von copy importiere deepcopy
von functools importiere total_ordering, wraps

importiere typing       # Needed fuer the string "typing.ClassVar[int]" to work als an annotation.
importiere dataclasses  # Needed fuer the string "dataclasses.InitVar[int]" to work als an annotation.

von test importiere support
von test.support importiere import_helper

# Just any custom exception we can catch.
klasse CustomError(Exception): pass

klasse TestCase(unittest.TestCase):
    def test_no_fields(self):
        @dataclass
        klasse C:
            pass

        o = C()
        self.assertEqual(len(fields(C)), 0)

    def test_no_fields_but_member_variable(self):
        @dataclass
        klasse C:
            i = 0

        o = C()
        self.assertEqual(len(fields(C)), 0)

    def test_one_field_no_default(self):
        @dataclass
        klasse C:
            x: int

        o = C(42)
        self.assertEqual(o.x, 42)

    def test_field_default_default_factory_error(self):
        msg = "cannot specify both default und default_factory"
        mit self.assertRaisesRegex(ValueError, msg):
            @dataclass
            klasse C:
                x: int = field(default=1, default_factory=int)

    def test_field_repr(self):
        int_field = field(default=1, init=Wahr, repr=Falsch, doc='Docstring')
        int_field.name = "id"
        repr_output = repr(int_field)
        expected_output = "Field(name='id',type=Nichts," \
                           f"default=1,default_factory={MISSING!r}," \
                           "init=Wahr,repr=Falsch,hash=Nichts," \
                           "compare=Wahr,metadata=mappingproxy({})," \
                           f"kw_only={MISSING!r}," \
                           "doc='Docstring'," \
                           "_field_type=Nichts)"

        self.assertEqual(repr_output, expected_output)

    def test_field_recursive_repr(self):
        rec_field = field()
        rec_field.type = rec_field
        rec_field.name = "id"
        repr_output = repr(rec_field)

        self.assertIn(",type=...,", repr_output)

    def test_recursive_annotation(self):
        klasse C:
            pass

        @dataclass
        klasse D:
            C: C = field()

        self.assertIn(",type=...,", repr(D.__dataclass_fields__["C"]))

    def test_dataclass_params_repr(self):
        # Even though this is testing an internal implementation detail,
        # it's testing a feature we want to make sure is correctly implemented
        # fuer the sake of dataclasses itself
        @dataclass(slots=Wahr, frozen=Wahr)
        klasse Some: pass

        repr_output = repr(Some.__dataclass_params__)
        expected_output = "_DataclassParams(init=Wahr,repr=Wahr," \
                          "eq=Wahr,order=Falsch,unsafe_hash=Falsch,frozen=Wahr," \
                          "match_args=Wahr,kw_only=Falsch," \
                          "slots=Wahr,weakref_slot=Falsch)"
        self.assertEqual(repr_output, expected_output)

    def test_dataclass_params_signature(self):
        # Even though this is testing an internal implementation detail,
        # it's testing a feature we want to make sure is correctly implemented
        # fuer the sake of dataclasses itself
        @dataclass
        klasse Some: pass

        fuer param in inspect.signature(dataclass).parameters:
            wenn param == 'cls':
                weiter
            self.assertHasAttr(Some.__dataclass_params__, param)

    def test_named_init_params(self):
        @dataclass
        klasse C:
            x: int

        o = C(x=32)
        self.assertEqual(o.x, 32)

    def test_two_fields_one_default(self):
        @dataclass
        klasse C:
            x: int
            y: int = 0

        o = C(3)
        self.assertEqual((o.x, o.y), (3, 0))

        # Non-defaults following defaults.
        mit self.assertRaisesRegex(TypeError,
                                    "non-default argument 'y' follows "
                                    "default argument 'x'"):
            @dataclass
            klasse C:
                x: int = 0
                y: int

        # A derived klasse adds a non-default field after a default one.
        mit self.assertRaisesRegex(TypeError,
                                    "non-default argument 'y' follows "
                                    "default argument 'x'"):
            @dataclass
            klasse B:
                x: int = 0

            @dataclass
            klasse C(B):
                y: int

        # Override a base klasse field und add a default to
        #  a field which didn't use to have a default.
        mit self.assertRaisesRegex(TypeError,
                                    "non-default argument 'y' follows "
                                    "default argument 'x'"):
            @dataclass
            klasse B:
                x: int
                y: int

            @dataclass
            klasse C(B):
                x: int = 0

    def test_overwrite_hash(self):
        # Test that declaring this klasse isn't an error.  It should
        #  use the user-provided __hash__.
        @dataclass(frozen=Wahr)
        klasse C:
            x: int
            def __hash__(self):
                gib 301
        self.assertEqual(hash(C(100)), 301)

        # Test that declaring this klasse isn't an error.  It should
        #  use the generated __hash__.
        @dataclass(frozen=Wahr)
        klasse C:
            x: int
            def __eq__(self, other):
                gib Falsch
        self.assertEqual(hash(C(100)), hash((100,)))

        # But this one should generate an exception, because with
        #  unsafe_hash=Wahr, it's an error to have a __hash__ defined.
        mit self.assertRaisesRegex(TypeError,
                                    'Cannot overwrite attribute __hash__'):
            @dataclass(unsafe_hash=Wahr)
            klasse C:
                def __hash__(self):
                    pass

        # Creating this klasse should nicht generate an exception,
        #  because even though __hash__ exists before @dataclass is
        #  called, (due to __eq__ being defined), since it's Nichts
        #  that's okay.
        @dataclass(unsafe_hash=Wahr)
        klasse C:
            x: int
            def __eq__(self):
                pass
        # The generated hash function works als we'd expect.
        self.assertEqual(hash(C(10)), hash((10,)))

        # Creating this klasse should generate an exception, because
        #  __hash__ exists und is nicht Nichts, which it would be wenn it
        #  had been auto-generated due to __eq__ being defined.
        mit self.assertRaisesRegex(TypeError,
                                    'Cannot overwrite attribute __hash__'):
            @dataclass(unsafe_hash=Wahr)
            klasse C:
                x: int
                def __eq__(self):
                    pass
                def __hash__(self):
                    pass

    def test_overwrite_fields_in_derived_class(self):
        # Note that x von C1 replaces x in Base, but the order remains
        #  the same als defined in Base.
        @dataclass
        klasse Base:
            x: Any = 15.0
            y: int = 0

        @dataclass
        klasse C1(Base):
            z: int = 10
            x: int = 15

        o = Base()
        self.assertEqual(repr(o), 'TestCase.test_overwrite_fields_in_derived_class.<locals>.Base(x=15.0, y=0)')

        o = C1()
        self.assertEqual(repr(o), 'TestCase.test_overwrite_fields_in_derived_class.<locals>.C1(x=15, y=0, z=10)')

        o = C1(x=5)
        self.assertEqual(repr(o), 'TestCase.test_overwrite_fields_in_derived_class.<locals>.C1(x=5, y=0, z=10)')

    def test_field_named_self(self):
        @dataclass
        klasse C:
            self: str
        c=C('foo')
        self.assertEqual(c.self, 'foo')

        # Make sure the first parameter is nicht named 'self'.
        sig = inspect.signature(C.__init__)
        first = next(iter(sig.parameters))
        self.assertNotEqual('self', first)

        # But we do use 'self' wenn no field named self.
        @dataclass
        klasse C:
            selfx: str

        # Make sure the first parameter is named 'self'.
        sig = inspect.signature(C.__init__)
        first = next(iter(sig.parameters))
        self.assertEqual('self', first)

    def test_field_named_object(self):
        @dataclass
        klasse C:
            object: str
        c = C('foo')
        self.assertEqual(c.object, 'foo')

    def test_field_named_object_frozen(self):
        @dataclass(frozen=Wahr)
        klasse C:
            object: str
        c = C('foo')
        self.assertEqual(c.object, 'foo')

    def test_field_named_BUILTINS_frozen(self):
        # gh-96151
        @dataclass(frozen=Wahr)
        klasse C:
            BUILTINS: int
        c = C(5)
        self.assertEqual(c.BUILTINS, 5)

    def test_field_with_special_single_underscore_names(self):
        # gh-98886

        @dataclass
        klasse X:
            x: int = field(default_factory=lambda: 111)
            _dflt_x: int = field(default_factory=lambda: 222)

        X()

        @dataclass
        klasse Y:
            y: int = field(default_factory=lambda: 111)
            _HAS_DEFAULT_FACTORY: int = 222

        assert Y(y=222).y == 222

    def test_field_named_like_builtin(self):
        # Attribute names can shadow built-in names
        # since code generation is used.
        # Ensure that this is nicht happening.
        exclusions = {'Nichts', 'Wahr', 'Falsch'}
        builtins_names = sorted(
            b fuer b in builtins.__dict__.keys()
            wenn nicht b.startswith('__') und b nicht in exclusions
        )
        attributes = [(name, str) fuer name in builtins_names]
        C = make_dataclass('C', attributes)

        c = C(*[name fuer name in builtins_names])

        fuer name in builtins_names:
            self.assertEqual(getattr(c, name), name)

    def test_field_named_like_builtin_frozen(self):
        # Attribute names can shadow built-in names
        # since code generation is used.
        # Ensure that this is nicht happening
        # fuer frozen data classes.
        exclusions = {'Nichts', 'Wahr', 'Falsch'}
        builtins_names = sorted(
            b fuer b in builtins.__dict__.keys()
            wenn nicht b.startswith('__') und b nicht in exclusions
        )
        attributes = [(name, str) fuer name in builtins_names]
        C = make_dataclass('C', attributes, frozen=Wahr)

        c = C(*[name fuer name in builtins_names])

        fuer name in builtins_names:
            self.assertEqual(getattr(c, name), name)

    def test_0_field_compare(self):
        # Ensure that order=Falsch is the default.
        @dataclass
        klasse C0:
            pass

        @dataclass(order=Falsch)
        klasse C1:
            pass

        fuer cls in [C0, C1]:
            mit self.subTest(cls=cls):
                self.assertEqual(cls(), cls())
                fuer idx, fn in enumerate([lambda a, b: a < b,
                                          lambda a, b: a <= b,
                                          lambda a, b: a > b,
                                          lambda a, b: a >= b]):
                    mit self.subTest(idx=idx):
                        mit self.assertRaisesRegex(TypeError,
                                                    f"not supported between instances of '{cls.__name__}' und '{cls.__name__}'"):
                            fn(cls(), cls())

        @dataclass(order=Wahr)
        klasse C:
            pass
        self.assertLessEqual(C(), C())
        self.assertGreaterEqual(C(), C())

    def test_1_field_compare(self):
        # Ensure that order=Falsch is the default.
        @dataclass
        klasse C0:
            x: int

        @dataclass(order=Falsch)
        klasse C1:
            x: int

        fuer cls in [C0, C1]:
            mit self.subTest(cls=cls):
                self.assertEqual(cls(1), cls(1))
                self.assertNotEqual(cls(0), cls(1))
                fuer idx, fn in enumerate([lambda a, b: a < b,
                                          lambda a, b: a <= b,
                                          lambda a, b: a > b,
                                          lambda a, b: a >= b]):
                    mit self.subTest(idx=idx):
                        mit self.assertRaisesRegex(TypeError,
                                                    f"not supported between instances of '{cls.__name__}' und '{cls.__name__}'"):
                            fn(cls(0), cls(0))

        @dataclass(order=Wahr)
        klasse C:
            x: int
        self.assertLess(C(0), C(1))
        self.assertLessEqual(C(0), C(1))
        self.assertLessEqual(C(1), C(1))
        self.assertGreater(C(1), C(0))
        self.assertGreaterEqual(C(1), C(0))
        self.assertGreaterEqual(C(1), C(1))

    def test_simple_compare(self):
        # Ensure that order=Falsch is the default.
        @dataclass
        klasse C0:
            x: int
            y: int

        @dataclass(order=Falsch)
        klasse C1:
            x: int
            y: int

        fuer cls in [C0, C1]:
            mit self.subTest(cls=cls):
                self.assertEqual(cls(0, 0), cls(0, 0))
                self.assertEqual(cls(1, 2), cls(1, 2))
                self.assertNotEqual(cls(1, 0), cls(0, 0))
                self.assertNotEqual(cls(1, 0), cls(1, 1))
                fuer idx, fn in enumerate([lambda a, b: a < b,
                                          lambda a, b: a <= b,
                                          lambda a, b: a > b,
                                          lambda a, b: a >= b]):
                    mit self.subTest(idx=idx):
                        mit self.assertRaisesRegex(TypeError,
                                                    f"not supported between instances of '{cls.__name__}' und '{cls.__name__}'"):
                            fn(cls(0, 0), cls(0, 0))

        @dataclass(order=Wahr)
        klasse C:
            x: int
            y: int

        fuer idx, fn in enumerate([lambda a, b: a == b,
                                  lambda a, b: a <= b,
                                  lambda a, b: a >= b]):
            mit self.subTest(idx=idx):
                self.assertWahr(fn(C(0, 0), C(0, 0)))

        fuer idx, fn in enumerate([lambda a, b: a < b,
                                  lambda a, b: a <= b,
                                  lambda a, b: a != b]):
            mit self.subTest(idx=idx):
                self.assertWahr(fn(C(0, 0), C(0, 1)))
                self.assertWahr(fn(C(0, 1), C(1, 0)))
                self.assertWahr(fn(C(1, 0), C(1, 1)))

        fuer idx, fn in enumerate([lambda a, b: a > b,
                                  lambda a, b: a >= b,
                                  lambda a, b: a != b]):
            mit self.subTest(idx=idx):
                self.assertWahr(fn(C(0, 1), C(0, 0)))
                self.assertWahr(fn(C(1, 0), C(0, 1)))
                self.assertWahr(fn(C(1, 1), C(1, 0)))

    def test_compare_subclasses(self):
        # Comparisons fail fuer subclasses, even wenn no fields
        #  are added.
        @dataclass
        klasse B:
            i: int

        @dataclass
        klasse C(B):
            pass

        fuer idx, (fn, expected) in enumerate([(lambda a, b: a == b, Falsch),
                                              (lambda a, b: a != b, Wahr)]):
            mit self.subTest(idx=idx):
                self.assertEqual(fn(B(0), C(0)), expected)

        fuer idx, fn in enumerate([lambda a, b: a < b,
                                  lambda a, b: a <= b,
                                  lambda a, b: a > b,
                                  lambda a, b: a >= b]):
            mit self.subTest(idx=idx):
                mit self.assertRaisesRegex(TypeError,
                                            "not supported between instances of 'B' und 'C'"):
                    fn(B(0), C(0))

    def test_eq_order(self):
        # Test combining eq und order.
        fuer (eq,    order, result   ) in [
            (Falsch, Falsch, 'neither'),
            (Falsch, Wahr,  'exception'),
            (Wahr,  Falsch, 'eq_only'),
            (Wahr,  Wahr,  'both'),
        ]:
            mit self.subTest(eq=eq, order=order):
                wenn result == 'exception':
                    mit self.assertRaisesRegex(ValueError, 'eq must be true wenn order is true'):
                        @dataclass(eq=eq, order=order)
                        klasse C:
                            pass
                sonst:
                    @dataclass(eq=eq, order=order)
                    klasse C:
                        pass

                    wenn result == 'neither':
                        self.assertNotIn('__eq__', C.__dict__)
                        self.assertNotIn('__lt__', C.__dict__)
                        self.assertNotIn('__le__', C.__dict__)
                        self.assertNotIn('__gt__', C.__dict__)
                        self.assertNotIn('__ge__', C.__dict__)
                    sowenn result == 'both':
                        self.assertIn('__eq__', C.__dict__)
                        self.assertIn('__lt__', C.__dict__)
                        self.assertIn('__le__', C.__dict__)
                        self.assertIn('__gt__', C.__dict__)
                        self.assertIn('__ge__', C.__dict__)
                    sowenn result == 'eq_only':
                        self.assertIn('__eq__', C.__dict__)
                        self.assertNotIn('__lt__', C.__dict__)
                        self.assertNotIn('__le__', C.__dict__)
                        self.assertNotIn('__gt__', C.__dict__)
                        self.assertNotIn('__ge__', C.__dict__)
                    sonst:
                        assert Falsch, f'unknown result {result!r}'

    def test_field_no_default(self):
        @dataclass
        klasse C:
            x: int = field()

        self.assertEqual(C(5).x, 5)

        mit self.assertRaisesRegex(TypeError,
                                    r"__init__\(\) missing 1 required "
                                    "positional argument: 'x'"):
            C()

    def test_field_default(self):
        default = object()
        @dataclass
        klasse C:
            x: object = field(default=default)

        self.assertIs(C.x, default)
        c = C(10)
        self.assertEqual(c.x, 10)

        # If we delete the instance attribute, we should then see the
        #  klasse attribute.
        del c.x
        self.assertIs(c.x, default)

        self.assertIs(C().x, default)

    def test_not_in_repr(self):
        @dataclass
        klasse C:
            x: int = field(repr=Falsch)
        mit self.assertRaises(TypeError):
            C()
        c = C(10)
        self.assertEqual(repr(c), 'TestCase.test_not_in_repr.<locals>.C()')

        @dataclass
        klasse C:
            x: int = field(repr=Falsch)
            y: int
        c = C(10, 20)
        self.assertEqual(repr(c), 'TestCase.test_not_in_repr.<locals>.C(y=20)')

    def test_not_in_compare(self):
        @dataclass
        klasse C:
            x: int = 0
            y: int = field(compare=Falsch, default=4)

        self.assertEqual(C(), C(0, 20))
        self.assertEqual(C(1, 10), C(1, 20))
        self.assertNotEqual(C(3), C(4, 10))
        self.assertNotEqual(C(3, 10), C(4, 10))

    def test_no_unhashable_default(self):
        # See bpo-44674.
        klasse Unhashable:
            __hash__ = Nichts

        unhashable_re = 'mutable default .* fuer field a is nicht allowed'
        mit self.assertRaisesRegex(ValueError, unhashable_re):
            @dataclass
            klasse A:
                a: dict = {}

        mit self.assertRaisesRegex(ValueError, unhashable_re):
            @dataclass
            klasse A:
                a: Any = Unhashable()

        # Make sure that the machinery looking fuer hashability is using the
        # class's __hash__, nicht the instance's __hash__.
        mit self.assertRaisesRegex(ValueError, unhashable_re):
            unhashable = Unhashable()
            # This shouldn't make the variable hashable.
            unhashable.__hash__ = lambda: 0
            @dataclass
            klasse A:
                a: Any = unhashable

    def test_hash_field_rules(self):
        # Test all 6 cases of:
        #  hash=Wahr/Falsch/Nichts
        #  compare=Wahr/Falsch
        fuer (hash_,    compare, result  ) in [
            (Wahr,     Falsch,   'field' ),
            (Wahr,     Wahr,    'field' ),
            (Falsch,    Falsch,   'absent'),
            (Falsch,    Wahr,    'absent'),
            (Nichts,     Falsch,   'absent'),
            (Nichts,     Wahr,    'field' ),
            ]:
            mit self.subTest(hash=hash_, compare=compare):
                @dataclass(unsafe_hash=Wahr)
                klasse C:
                    x: int = field(compare=compare, hash=hash_, default=5)

                wenn result == 'field':
                    # __hash__ contains the field.
                    self.assertEqual(hash(C(5)), hash((5,)))
                sowenn result == 'absent':
                    # The field is nicht present in the hash.
                    self.assertEqual(hash(C(5)), hash(()))
                sonst:
                    assert Falsch, f'unknown result {result!r}'

    def test_init_false_no_default(self):
        # If init=Falsch und no default value, then the field won't be
        #  present in the instance.
        @dataclass
        klasse C:
            x: int = field(init=Falsch)

        self.assertNotIn('x', C().__dict__)

        @dataclass
        klasse C:
            x: int
            y: int = 0
            z: int = field(init=Falsch)
            t: int = 10

        self.assertNotIn('z', C(0).__dict__)
        self.assertEqual(vars(C(5)), {'t': 10, 'x': 5, 'y': 0})

    def test_class_marker(self):
        @dataclass
        klasse C:
            x: int
            y: str = field(init=Falsch, default=Nichts)
            z: str = field(repr=Falsch)

        the_fields = fields(C)
        # the_fields is a tuple of 3 items, each value
        #  is in __annotations__.
        self.assertIsInstance(the_fields, tuple)
        fuer f in the_fields:
            self.assertIs(type(f), Field)
            self.assertIn(f.name, C.__annotations__)

        self.assertEqual(len(the_fields), 3)

        self.assertEqual(the_fields[0].name, 'x')
        self.assertEqual(the_fields[0].type, int)
        self.assertNotHasAttr(C, 'x')
        self.assertWahr (the_fields[0].init)
        self.assertWahr (the_fields[0].repr)
        self.assertEqual(the_fields[1].name, 'y')
        self.assertEqual(the_fields[1].type, str)
        self.assertIsNichts(getattr(C, 'y'))
        self.assertFalsch(the_fields[1].init)
        self.assertWahr (the_fields[1].repr)
        self.assertEqual(the_fields[2].name, 'z')
        self.assertEqual(the_fields[2].type, str)
        self.assertNotHasAttr(C, 'z')
        self.assertWahr (the_fields[2].init)
        self.assertFalsch(the_fields[2].repr)

    def test_field_order(self):
        @dataclass
        klasse B:
            a: str = 'B:a'
            b: str = 'B:b'
            c: str = 'B:c'

        @dataclass
        klasse C(B):
            b: str = 'C:b'

        self.assertEqual([(f.name, f.default) fuer f in fields(C)],
                         [('a', 'B:a'),
                          ('b', 'C:b'),
                          ('c', 'B:c')])

        @dataclass
        klasse D(B):
            c: str = 'D:c'

        self.assertEqual([(f.name, f.default) fuer f in fields(D)],
                         [('a', 'B:a'),
                          ('b', 'B:b'),
                          ('c', 'D:c')])

        @dataclass
        klasse E(D):
            a: str = 'E:a'
            d: str = 'E:d'

        self.assertEqual([(f.name, f.default) fuer f in fields(E)],
                         [('a', 'E:a'),
                          ('b', 'B:b'),
                          ('c', 'D:c'),
                          ('d', 'E:d')])

    def test_class_attrs(self):
        # We only have a klasse attribute wenn a default value is
        #  specified, either directly oder via a field mit a default.
        default = object()
        @dataclass
        klasse C:
            x: int
            y: int = field(repr=Falsch)
            z: object = default
            t: int = field(default=100)

        self.assertNotHasAttr(C, 'x')
        self.assertNotHasAttr(C, 'y')
        self.assertIs   (C.z, default)
        self.assertEqual(C.t, 100)

    def test_disallowed_mutable_defaults(self):
        # For the known types, don't allow mutable default values.
        fuer typ, empty, non_empty in [(list, [], [1]),
                                      (dict, {}, {0:1}),
                                      (set, set(), set([1])),
                                      ]:
            mit self.subTest(typ=typ):
                # Can't use a zero-length value.
                mit self.assertRaisesRegex(ValueError,
                                            f'mutable default {typ} fuer field '
                                            'x is nicht allowed'):
                    @dataclass
                    klasse Point:
                        x: typ = empty


                # Nor a non-zero-length value
                mit self.assertRaisesRegex(ValueError,
                                            f'mutable default {typ} fuer field '
                                            'y is nicht allowed'):
                    @dataclass
                    klasse Point:
                        y: typ = non_empty

                # Check subtypes also fail.
                klasse Subclass(typ): pass

                mit self.assertRaisesRegex(ValueError,
                                            "mutable default .*Subclass'>"
                                            " fuer field z is nicht allowed"
                                            ):
                    @dataclass
                    klasse Point:
                        z: typ = Subclass()

                # Because this is a ClassVar, it can be mutable.
                @dataclass
                klasse UsesMutableClassVar:
                    z: ClassVar[typ] = typ()

                # Because this is a ClassVar, it can be mutable.
                @dataclass
                klasse UsesMutableClassVarWithSubType:
                    x: ClassVar[typ] = Subclass()

    def test_deliberately_mutable_defaults(self):
        # If a mutable default isn't in the known list of
        #  (list, dict, set), then it's okay.
        klasse Mutable:
            def __init__(self):
                self.l = []

        @dataclass
        klasse C:
            x: Mutable

        # These 2 instances will share this value of x.
        lst = Mutable()
        o1 = C(lst)
        o2 = C(lst)
        self.assertEqual(o1, o2)
        o1.x.l.extend([1, 2])
        self.assertEqual(o1, o2)
        self.assertEqual(o1.x.l, [1, 2])
        self.assertIs(o1.x, o2.x)

    def test_no_options(self):
        # Call mit dataclass().
        @dataclass()
        klasse C:
            x: int

        self.assertEqual(C(42).x, 42)

    def test_not_tuple(self):
        # Make sure we can't be compared to a tuple.
        @dataclass
        klasse Point:
            x: int
            y: int
        self.assertNotEqual(Point(1, 2), (1, 2))

        # And that we can't compare to another unrelated dataclass.
        @dataclass
        klasse C:
            x: int
            y: int
        self.assertNotEqual(Point(1, 3), C(1, 3))

    def test_not_other_dataclass(self):
        # Test that some of the problems mit namedtuple don't happen
        #  here.
        @dataclass
        klasse Point3D:
            x: int
            y: int
            z: int

        @dataclass
        klasse Date:
            year: int
            month: int
            day: int

        self.assertNotEqual(Point3D(2017, 6, 3), Date(2017, 6, 3))
        self.assertNotEqual(Point3D(1, 2, 3), (1, 2, 3))

        # Make sure we can't unpack.
        mit self.assertRaisesRegex(TypeError, 'unpack'):
            x, y, z = Point3D(4, 5, 6)

        # Make sure another klasse mit the same field names isn't
        #  equal.
        @dataclass
        klasse Point3Dv1:
            x: int = 0
            y: int = 0
            z: int = 0
        self.assertNotEqual(Point3D(0, 0, 0), Point3Dv1())

    def test_function_annotations(self):
        # Some dummy klasse und instance to use als a default.
        klasse F:
            pass
        f = F()

        def validate_class(cls):
            # First, check __annotations__, even though they're not
            #  function annotations.
            self.assertEqual(cls.__annotations__['i'], int)
            self.assertEqual(cls.__annotations__['j'], str)
            self.assertEqual(cls.__annotations__['k'], F)
            self.assertEqual(cls.__annotations__['l'], float)
            self.assertEqual(cls.__annotations__['z'], complex)

            # Verify __init__.

            signature = inspect.signature(cls.__init__)
            # Check the gib type, should be Nichts.
            self.assertIs(signature.return_annotation, Nichts)

            # Check each parameter.
            params = iter(signature.parameters.values())
            param = next(params)
            # This is testing an internal name, und probably shouldn't be tested.
            self.assertEqual(param.name, 'self')
            param = next(params)
            self.assertEqual(param.name, 'i')
            self.assertIs   (param.annotation, int)
            self.assertEqual(param.default, inspect.Parameter.empty)
            self.assertEqual(param.kind, inspect.Parameter.POSITIONAL_OR_KEYWORD)
            param = next(params)
            self.assertEqual(param.name, 'j')
            self.assertIs   (param.annotation, str)
            self.assertEqual(param.default, inspect.Parameter.empty)
            self.assertEqual(param.kind, inspect.Parameter.POSITIONAL_OR_KEYWORD)
            param = next(params)
            self.assertEqual(param.name, 'k')
            self.assertIs   (param.annotation, F)
            # Don't test fuer the default, since it's set to MISSING.
            self.assertEqual(param.kind, inspect.Parameter.POSITIONAL_OR_KEYWORD)
            param = next(params)
            self.assertEqual(param.name, 'l')
            self.assertIs   (param.annotation, float)
            # Don't test fuer the default, since it's set to MISSING.
            self.assertEqual(param.kind, inspect.Parameter.POSITIONAL_OR_KEYWORD)
            self.assertRaises(StopIteration, next, params)


        @dataclass
        klasse C:
            i: int
            j: str
            k: F = f
            l: float=field(default=Nichts)
            z: complex=field(default=3+4j, init=Falsch)

        validate_class(C)

        # Now repeat mit __hash__.
        @dataclass(frozen=Wahr, unsafe_hash=Wahr)
        klasse C:
            i: int
            j: str
            k: F = f
            l: float=field(default=Nichts)
            z: complex=field(default=3+4j, init=Falsch)

        validate_class(C)

    def test_missing_default(self):
        # Test that MISSING works the same als a default nicht being
        #  specified.
        @dataclass
        klasse C:
            x: int=field(default=MISSING)
        mit self.assertRaisesRegex(TypeError,
                                    r'__init__\(\) missing 1 required '
                                    'positional argument'):
            C()
        self.assertNotIn('x', C.__dict__)

        @dataclass
        klasse D:
            x: int
        mit self.assertRaisesRegex(TypeError,
                                    r'__init__\(\) missing 1 required '
                                    'positional argument'):
            D()
        self.assertNotIn('x', D.__dict__)

    def test_missing_default_factory(self):
        # Test that MISSING works the same als a default factory not
        #  being specified (which is really the same als a default not
        #  being specified, too).
        @dataclass
        klasse C:
            x: int=field(default_factory=MISSING)
        mit self.assertRaisesRegex(TypeError,
                                    r'__init__\(\) missing 1 required '
                                    'positional argument'):
            C()
        self.assertNotIn('x', C.__dict__)

        @dataclass
        klasse D:
            x: int=field(default=MISSING, default_factory=MISSING)
        mit self.assertRaisesRegex(TypeError,
                                    r'__init__\(\) missing 1 required '
                                    'positional argument'):
            D()
        self.assertNotIn('x', D.__dict__)

    def test_missing_repr(self):
        self.assertIn('MISSING_TYPE object', repr(MISSING))

    def test_dont_include_other_annotations(self):
        @dataclass
        klasse C:
            i: int
            def foo(self) -> int:
                gib 4
            @property
            def bar(self) -> int:
                gib 5
        self.assertEqual(list(C.__annotations__), ['i'])
        self.assertEqual(C(10).foo(), 4)
        self.assertEqual(C(10).bar, 5)
        self.assertEqual(C(10).i, 10)

    def test_post_init(self):
        # Just make sure it gets called
        @dataclass
        klasse C:
            def __post_init__(self):
                wirf CustomError()
        mit self.assertRaises(CustomError):
            C()

        @dataclass
        klasse C:
            i: int = 10
            def __post_init__(self):
                wenn self.i == 10:
                    wirf CustomError()
        mit self.assertRaises(CustomError):
            C()
        # post-init gets called, but doesn't raise. This is just
        #  checking that self is used correctly.
        C(5)

        # If there's nicht an __init__, then post-init won't get called.
        @dataclass(init=Falsch)
        klasse C:
            def __post_init__(self):
                wirf CustomError()
        # Creating the klasse won't wirf
        C()

        @dataclass
        klasse C:
            x: int = 0
            def __post_init__(self):
                self.x *= 2
        self.assertEqual(C().x, 0)
        self.assertEqual(C(2).x, 4)

        # Make sure that wenn we're frozen, post-init can't set
        #  attributes.
        @dataclass(frozen=Wahr)
        klasse C:
            x: int = 0
            def __post_init__(self):
                self.x *= 2
        mit self.assertRaises(FrozenInstanceError):
            C()

    def test_post_init_super(self):
        # Make sure super() post-init isn't called by default.
        klasse B:
            def __post_init__(self):
                wirf CustomError()

        @dataclass
        klasse C(B):
            def __post_init__(self):
                self.x = 5

        self.assertEqual(C().x, 5)

        # Now call super(), und it will raise.
        @dataclass
        klasse C(B):
            def __post_init__(self):
                super().__post_init__()

        mit self.assertRaises(CustomError):
            C()

        # Make sure post-init is called, even wenn nicht defined in our
        #  class.
        @dataclass
        klasse C(B):
            pass

        mit self.assertRaises(CustomError):
            C()

    def test_post_init_staticmethod(self):
        flag = Falsch
        @dataclass
        klasse C:
            x: int
            y: int
            @staticmethod
            def __post_init__():
                nonlocal flag
                flag = Wahr

        self.assertFalsch(flag)
        c = C(3, 4)
        self.assertEqual((c.x, c.y), (3, 4))
        self.assertWahr(flag)

    def test_post_init_classmethod(self):
        @dataclass
        klasse C:
            flag = Falsch
            x: int
            y: int
            @classmethod
            def __post_init__(cls):
                cls.flag = Wahr

        self.assertFalsch(C.flag)
        c = C(3, 4)
        self.assertEqual((c.x, c.y), (3, 4))
        self.assertWahr(C.flag)

    def test_post_init_not_auto_added(self):
        # See bpo-46757, which had proposed always adding __post_init__.  As
        # Raymond Hettinger pointed out, that would be a breaking change.  So,
        # add a test to make sure that the current behavior doesn't change.

        @dataclass
        klasse A0:
            pass

        @dataclass
        klasse B0:
            b_called: bool = Falsch
            def __post_init__(self):
                self.b_called = Wahr

        @dataclass
        klasse C0(A0, B0):
            c_called: bool = Falsch
            def __post_init__(self):
                super().__post_init__()
                self.c_called = Wahr

        # Since A0 has no __post_init__, und one wasn't automatically added
        # (because that's the rule: it's never added by @dataclass, it's only
        # the klasse author that can add it), then B0.__post_init__ is called.
        # Verify that.
        c = C0()
        self.assertWahr(c.b_called)
        self.assertWahr(c.c_called)

        ######################################
        # Now, the same thing, ausser A1 defines __post_init__.
        @dataclass
        klasse A1:
            def __post_init__(self):
                pass

        @dataclass
        klasse B1:
            b_called: bool = Falsch
            def __post_init__(self):
                self.b_called = Wahr

        @dataclass
        klasse C1(A1, B1):
            c_called: bool = Falsch
            def __post_init__(self):
                super().__post_init__()
                self.c_called = Wahr

        # This time, B1.__post_init__ isn't being called.  This mimics what
        # would happen wenn A1.__post_init__ had been automatically added,
        # instead of manually added als we see here.  This test isn't really
        # needed, but I'm including it just to demonstrate the changed
        # behavior when A1 does define __post_init__.
        c = C1()
        self.assertFalsch(c.b_called)
        self.assertWahr(c.c_called)

    def test_class_var(self):
        # Make sure ClassVars are ignored in __init__, __repr__, etc.
        @dataclass
        klasse C:
            x: int
            y: int = 10
            z: ClassVar[int] = 1000
            w: ClassVar[int] = 2000
            t: ClassVar[int] = 3000
            s: ClassVar      = 4000

        c = C(5)
        self.assertEqual(repr(c), 'TestCase.test_class_var.<locals>.C(x=5, y=10)')
        self.assertEqual(len(fields(C)), 2)                 # We have 2 fields.
        self.assertEqual(len(C.__annotations__), 6)         # And 4 ClassVars.
        self.assertEqual(c.z, 1000)
        self.assertEqual(c.w, 2000)
        self.assertEqual(c.t, 3000)
        self.assertEqual(c.s, 4000)
        C.z += 1
        self.assertEqual(c.z, 1001)
        c = C(20)
        self.assertEqual((c.x, c.y), (20, 10))
        self.assertEqual(c.z, 1001)
        self.assertEqual(c.w, 2000)
        self.assertEqual(c.t, 3000)
        self.assertEqual(c.s, 4000)

    def test_class_var_no_default(self):
        # If a ClassVar has no default value, it should nicht be set on the class.
        @dataclass
        klasse C:
            x: ClassVar[int]

        self.assertNotIn('x', C.__dict__)

    def test_class_var_default_factory(self):
        # It makes no sense fuer a ClassVar to have a default factory. When
        #  would it be called? Call it yourself, since it's class-wide.
        mit self.assertRaisesRegex(TypeError,
                                    'cannot have a default factory'):
            @dataclass
            klasse C:
                x: ClassVar[int] = field(default_factory=int)

            self.assertNotIn('x', C.__dict__)

    def test_class_var_with_default(self):
        # If a ClassVar has a default value, it should be set on the class.
        @dataclass
        klasse C:
            x: ClassVar[int] = 10
        self.assertEqual(C.x, 10)

        @dataclass
        klasse C:
            x: ClassVar[int] = field(default=10)
        self.assertEqual(C.x, 10)

    def test_class_var_frozen(self):
        # Make sure ClassVars work even wenn we're frozen.
        @dataclass(frozen=Wahr)
        klasse C:
            x: int
            y: int = 10
            z: ClassVar[int] = 1000
            w: ClassVar[int] = 2000
            t: ClassVar[int] = 3000

        c = C(5)
        self.assertEqual(repr(C(5)), 'TestCase.test_class_var_frozen.<locals>.C(x=5, y=10)')
        self.assertEqual(len(fields(C)), 2)                 # We have 2 fields
        self.assertEqual(len(C.__annotations__), 5)         # And 3 ClassVars
        self.assertEqual(c.z, 1000)
        self.assertEqual(c.w, 2000)
        self.assertEqual(c.t, 3000)
        # We can still modify the ClassVar, it's only instances that are
        #  frozen.
        C.z += 1
        self.assertEqual(c.z, 1001)
        c = C(20)
        self.assertEqual((c.x, c.y), (20, 10))
        self.assertEqual(c.z, 1001)
        self.assertEqual(c.w, 2000)
        self.assertEqual(c.t, 3000)

    def test_init_var_no_default(self):
        # If an InitVar has no default value, it should nicht be set on the class.
        @dataclass
        klasse C:
            x: InitVar[int]

        self.assertNotIn('x', C.__dict__)

    def test_init_var_default_factory(self):
        # It makes no sense fuer an InitVar to have a default factory. When
        #  would it be called? Call it yourself, since it's class-wide.
        mit self.assertRaisesRegex(TypeError,
                                    'cannot have a default factory'):
            @dataclass
            klasse C:
                x: InitVar[int] = field(default_factory=int)

            self.assertNotIn('x', C.__dict__)

    def test_init_var_with_default(self):
        # If an InitVar has a default value, it should be set on the class.
        @dataclass
        klasse C:
            x: InitVar[int] = 10
        self.assertEqual(C.x, 10)

        @dataclass
        klasse C:
            x: InitVar[int] = field(default=10)
        self.assertEqual(C.x, 10)

    def test_init_var(self):
        @dataclass
        klasse C:
            x: int = Nichts
            init_param: InitVar[int] = Nichts

            def __post_init__(self, init_param):
                wenn self.x is Nichts:
                    self.x = init_param*2

        c = C(init_param=10)
        self.assertEqual(c.x, 20)

    def test_init_var_preserve_type(self):
        self.assertEqual(InitVar[int].type, int)

        # Make sure the repr is correct.
        self.assertEqual(repr(InitVar[int]), 'dataclasses.InitVar[int]')
        self.assertEqual(repr(InitVar[List[int]]),
                         'dataclasses.InitVar[typing.List[int]]')
        self.assertEqual(repr(InitVar[list[int]]),
                         'dataclasses.InitVar[list[int]]')
        self.assertEqual(repr(InitVar[int|str]),
                         'dataclasses.InitVar[int | str]')

    def test_init_var_inheritance(self):
        # Note that this deliberately tests that a dataclass need not
        #  have a __post_init__ function wenn it has an InitVar field.
        #  It could just be used in a derived class, als shown here.
        @dataclass
        klasse Base:
            x: int
            init_base: InitVar[int]

        # We can instantiate by passing the InitVar, even though
        #  it's nicht used.
        b = Base(0, 10)
        self.assertEqual(vars(b), {'x': 0})

        @dataclass
        klasse C(Base):
            y: int
            init_derived: InitVar[int]

            def __post_init__(self, init_base, init_derived):
                self.x = self.x + init_base
                self.y = self.y + init_derived

        c = C(10, 11, 50, 51)
        self.assertEqual(vars(c), {'x': 21, 'y': 101})

    def test_init_var_name_shadowing(self):
        # Because dataclasses rely exclusively on `__annotations__` for
        # handling InitVar und `__annotations__` preserves shadowed definitions,
        # you can actually shadow an InitVar mit a method oder property.
        #
        # This only works when there is no default value; `dataclasses` uses the
        # actual name (which will be bound to the shadowing method) fuer default
        # values.
        @dataclass
        klasse C:
            shadowed: InitVar[int]
            _shadowed: int = field(init=Falsch)

            def __post_init__(self, shadowed):
                self._shadowed = shadowed * 2

            @property
            def shadowed(self):
                gib self._shadowed * 3

        c = C(5)
        self.assertEqual(c.shadowed, 30)

    def test_default_factory(self):
        # Test a factory that returns a new list.
        @dataclass
        klasse C:
            x: int
            y: list = field(default_factory=list)

        c0 = C(3)
        c1 = C(3)
        self.assertEqual(c0.x, 3)
        self.assertEqual(c0.y, [])
        self.assertEqual(c0, c1)
        self.assertIsNot(c0.y, c1.y)
        self.assertEqual(astuple(C(5, [1])), (5, [1]))

        # Test a factory that returns a shared list.
        l = []
        @dataclass
        klasse C:
            x: int
            y: list = field(default_factory=lambda: l)

        c0 = C(3)
        c1 = C(3)
        self.assertEqual(c0.x, 3)
        self.assertEqual(c0.y, [])
        self.assertEqual(c0, c1)
        self.assertIs(c0.y, c1.y)
        self.assertEqual(astuple(C(5, [1])), (5, [1]))

        # Test various other field flags.
        # repr
        @dataclass
        klasse C:
            x: list = field(default_factory=list, repr=Falsch)
        self.assertEqual(repr(C()), 'TestCase.test_default_factory.<locals>.C()')
        self.assertEqual(C().x, [])

        # hash
        @dataclass(unsafe_hash=Wahr)
        klasse C:
            x: list = field(default_factory=list, hash=Falsch)
        self.assertEqual(astuple(C()), ([],))
        self.assertEqual(hash(C()), hash(()))

        # init (see also test_default_factory_with_no_init)
        @dataclass
        klasse C:
            x: list = field(default_factory=list, init=Falsch)
        self.assertEqual(astuple(C()), ([],))

        # compare
        @dataclass
        klasse C:
            x: list = field(default_factory=list, compare=Falsch)
        self.assertEqual(C(), C([1]))

    def test_default_factory_with_no_init(self):
        # We need a factory mit a side effect.
        factory = Mock()

        @dataclass
        klasse C:
            x: list = field(default_factory=factory, init=Falsch)

        # Make sure the default factory is called fuer each new instance.
        C().x
        self.assertEqual(factory.call_count, 1)
        C().x
        self.assertEqual(factory.call_count, 2)

    def test_default_factory_not_called_if_value_given(self):
        # We need a factory that we can test wenn it's been called.
        factory = Mock()

        @dataclass
        klasse C:
            x: int = field(default_factory=factory)

        # Make sure that wenn a field has a default factory function,
        #  it's nicht called wenn a value is specified.
        C().x
        self.assertEqual(factory.call_count, 1)
        self.assertEqual(C(10).x, 10)
        self.assertEqual(factory.call_count, 1)
        C().x
        self.assertEqual(factory.call_count, 2)

    def test_default_factory_derived(self):
        # See bpo-32896.
        @dataclass
        klasse Foo:
            x: dict = field(default_factory=dict)

        @dataclass
        klasse Bar(Foo):
            y: int = 1

        self.assertEqual(Foo().x, {})
        self.assertEqual(Bar().x, {})
        self.assertEqual(Bar().y, 1)

        @dataclass
        klasse Baz(Foo):
            pass
        self.assertEqual(Baz().x, {})

    def test_intermediate_non_dataclass(self):
        # Test that an intermediate klasse that defines
        #  annotations does nicht define fields.

        @dataclass
        klasse A:
            x: int

        klasse B(A):
            y: int

        @dataclass
        klasse C(B):
            z: int

        c = C(1, 3)
        self.assertEqual((c.x, c.z), (1, 3))

        # .y was nicht initialized.
        mit self.assertRaisesRegex(AttributeError,
                                    'object has no attribute'):
            c.y

        # And wenn we again derive a non-dataclass, no fields are added.
        klasse D(C):
            t: int
        d = D(4, 5)
        self.assertEqual((d.x, d.z), (4, 5))

    def test_classvar_default_factory(self):
        # It's an error fuer a ClassVar to have a factory function.
        mit self.assertRaisesRegex(TypeError,
                                    'cannot have a default factory'):
            @dataclass
            klasse C:
                x: ClassVar[int] = field(default_factory=int)

    def test_is_dataclass(self):
        klasse NotDataClass:
            pass

        self.assertFalsch(is_dataclass(0))
        self.assertFalsch(is_dataclass(int))
        self.assertFalsch(is_dataclass(NotDataClass))
        self.assertFalsch(is_dataclass(NotDataClass()))

        @dataclass
        klasse C:
            x: int

        @dataclass
        klasse D:
            d: C
            e: int

        c = C(10)
        d = D(c, 4)

        self.assertWahr(is_dataclass(C))
        self.assertWahr(is_dataclass(c))
        self.assertFalsch(is_dataclass(c.x))
        self.assertWahr(is_dataclass(d.d))
        self.assertFalsch(is_dataclass(d.e))

    def test_is_dataclass_when_getattr_always_returns(self):
        # See bpo-37868.
        klasse A:
            def __getattr__(self, key):
                gib 0
        self.assertFalsch(is_dataclass(A))
        a = A()

        # Also test fuer an instance attribute.
        klasse B:
            pass
        b = B()
        b.__dataclass_fields__ = []

        fuer obj in a, b:
            mit self.subTest(obj=obj):
                self.assertFalsch(is_dataclass(obj))

                # Indirect tests fuer _is_dataclass_instance().
                mit self.assertRaisesRegex(TypeError, 'should be called on dataclass instances'):
                    asdict(obj)
                mit self.assertRaisesRegex(TypeError, 'should be called on dataclass instances'):
                    astuple(obj)
                mit self.assertRaisesRegex(TypeError, 'should be called on dataclass instances'):
                    replace(obj, x=0)

    def test_is_dataclass_genericalias(self):
        @dataclass
        klasse A(types.GenericAlias):
            origin: type
            args: type
        self.assertWahr(is_dataclass(A))
        a = A(list, int)
        self.assertWahr(is_dataclass(type(a)))
        self.assertWahr(is_dataclass(a))

    def test_is_dataclass_inheritance(self):
        @dataclass
        klasse X:
            y: int

        klasse Z(X):
            pass

        self.assertWahr(is_dataclass(X), "X should be a dataclass")
        self.assertWahr(
            is_dataclass(Z),
            "Z should be a dataclass because it inherits von X",
        )
        z_instance = Z(y=5)
        self.assertWahr(
            is_dataclass(z_instance),
            "z_instance should be a dataclass because it is an instance of Z",
        )

    def test_helper_fields_with_class_instance(self):
        # Check that we can call fields() on either a klasse oder instance,
        #  und get back the same thing.
        @dataclass
        klasse C:
            x: int
            y: float

        self.assertEqual(fields(C), fields(C(0, 0.0)))

    def test_helper_fields_exception(self):
        # Check that TypeError is raised wenn nicht passed a dataclass oder
        #  instance.
        mit self.assertRaisesRegex(TypeError, 'dataclass type oder instance'):
            fields(0)

        klasse C: pass
        mit self.assertRaisesRegex(TypeError, 'dataclass type oder instance'):
            fields(C)
        mit self.assertRaisesRegex(TypeError, 'dataclass type oder instance'):
            fields(C())

    def test_clean_traceback_from_fields_exception(self):
        stdout = io.StringIO()
        versuch:
            fields(object)
        ausser TypeError als exc:
            traceback.print_exception(exc, file=stdout)
        printed_traceback = stdout.getvalue()
        self.assertNotIn("AttributeError", printed_traceback)
        self.assertNotIn("__dataclass_fields__", printed_traceback)

    def test_helper_asdict(self):
        # Basic tests fuer asdict(), it should gib a new dictionary.
        @dataclass
        klasse C:
            x: int
            y: int
        c = C(1, 2)

        self.assertEqual(asdict(c), {'x': 1, 'y': 2})
        self.assertEqual(asdict(c), asdict(c))
        self.assertIsNot(asdict(c), asdict(c))
        c.x = 42
        self.assertEqual(asdict(c), {'x': 42, 'y': 2})
        self.assertIs(type(asdict(c)), dict)

    def test_helper_asdict_raises_on_classes(self):
        # asdict() should wirf on a klasse object.
        @dataclass
        klasse C:
            x: int
            y: int
        mit self.assertRaisesRegex(TypeError, 'dataclass instance'):
            asdict(C)
        mit self.assertRaisesRegex(TypeError, 'dataclass instance'):
            asdict(int)

    def test_helper_asdict_copy_values(self):
        @dataclass
        klasse C:
            x: int
            y: List[int] = field(default_factory=list)
        initial = []
        c = C(1, initial)
        d = asdict(c)
        self.assertEqual(d['y'], initial)
        self.assertIsNot(d['y'], initial)
        c = C(1)
        d = asdict(c)
        d['y'].append(1)
        self.assertEqual(c.y, [])

    def test_helper_asdict_nested(self):
        @dataclass
        klasse UserId:
            token: int
            group: int
        @dataclass
        klasse User:
            name: str
            id: UserId
        u = User('Joe', UserId(123, 1))
        d = asdict(u)
        self.assertEqual(d, {'name': 'Joe', 'id': {'token': 123, 'group': 1}})
        self.assertIsNot(asdict(u), asdict(u))
        u.id.group = 2
        self.assertEqual(asdict(u), {'name': 'Joe',
                                     'id': {'token': 123, 'group': 2}})

    def test_helper_asdict_builtin_containers(self):
        @dataclass
        klasse User:
            name: str
            id: int
        @dataclass
        klasse GroupList:
            id: int
            users: List[User]
        @dataclass
        klasse GroupTuple:
            id: int
            users: Tuple[User, ...]
        @dataclass
        klasse GroupDict:
            id: int
            users: Dict[str, User]
        a = User('Alice', 1)
        b = User('Bob', 2)
        gl = GroupList(0, [a, b])
        gt = GroupTuple(0, (a, b))
        gd = GroupDict(0, {'first': a, 'second': b})
        self.assertEqual(asdict(gl), {'id': 0, 'users': [{'name': 'Alice', 'id': 1},
                                                         {'name': 'Bob', 'id': 2}]})
        self.assertEqual(asdict(gt), {'id': 0, 'users': ({'name': 'Alice', 'id': 1},
                                                         {'name': 'Bob', 'id': 2})})
        self.assertEqual(asdict(gd), {'id': 0, 'users': {'first': {'name': 'Alice', 'id': 1},
                                                         'second': {'name': 'Bob', 'id': 2}}})

    def test_helper_asdict_builtin_object_containers(self):
        @dataclass
        klasse Child:
            d: object

        @dataclass
        klasse Parent:
            child: Child

        self.assertEqual(asdict(Parent(Child([1]))), {'child': {'d': [1]}})
        self.assertEqual(asdict(Parent(Child({1: 2}))), {'child': {'d': {1: 2}}})

    def test_helper_asdict_factory(self):
        @dataclass
        klasse C:
            x: int
            y: int
        c = C(1, 2)
        d = asdict(c, dict_factory=OrderedDict)
        self.assertEqual(d, OrderedDict([('x', 1), ('y', 2)]))
        self.assertIsNot(d, asdict(c, dict_factory=OrderedDict))
        c.x = 42
        d = asdict(c, dict_factory=OrderedDict)
        self.assertEqual(d, OrderedDict([('x', 42), ('y', 2)]))
        self.assertIs(type(d), OrderedDict)

    def test_helper_asdict_namedtuple(self):
        T = namedtuple('T', 'a b c')
        @dataclass
        klasse C:
            x: str
            y: T
        c = C('outer', T(1, C('inner', T(11, 12, 13)), 2))

        d = asdict(c)
        self.assertEqual(d, {'x': 'outer',
                             'y': T(1,
                                    {'x': 'inner',
                                     'y': T(11, 12, 13)},
                                    2),
                             }
                         )

        # Now mit a dict_factory.  OrderedDict is convenient, but
        # since it compares to dicts, we also need to have separate
        # assertIs tests.
        d = asdict(c, dict_factory=OrderedDict)
        self.assertEqual(d, {'x': 'outer',
                             'y': T(1,
                                    {'x': 'inner',
                                     'y': T(11, 12, 13)},
                                    2),
                             }
                         )

        # Make sure that the returned dicts are actually OrderedDicts.
        self.assertIs(type(d), OrderedDict)
        self.assertIs(type(d['y'][1]), OrderedDict)

    def test_helper_asdict_namedtuple_key(self):
        # Ensure that a field that contains a dict which has a
        # namedtuple als a key works mit asdict().

        @dataclass
        klasse C:
            f: dict
        T = namedtuple('T', 'a')

        c = C({T('an a'): 0})

        self.assertEqual(asdict(c), {'f': {T(a='an a'): 0}})

    def test_helper_asdict_namedtuple_derived(self):
        klasse T(namedtuple('Tbase', 'a')):
            def my_a(self):
                gib self.a

        @dataclass
        klasse C:
            f: T

        t = T(6)
        c = C(t)

        d = asdict(c)
        self.assertEqual(d, {'f': T(a=6)})
        # Make sure that t has been copied, nicht used directly.
        self.assertIsNot(d['f'], t)
        self.assertEqual(d['f'].my_a(), 6)

    def test_helper_asdict_defaultdict(self):
        # Ensure asdict() does nicht throw exceptions when a
        # defaultdict is a member of a dataclass
        @dataclass
        klasse C:
            mp: DefaultDict[str, List]

        dd = defaultdict(list)
        dd["x"].append(12)
        c = C(mp=dd)
        d = asdict(c)

        self.assertEqual(d, {"mp": {"x": [12]}})
        self.assertWahr(d["mp"] is nicht c.mp)  # make sure defaultdict is copied

    def test_helper_astuple(self):
        # Basic tests fuer astuple(), it should gib a new tuple.
        @dataclass
        klasse C:
            x: int
            y: int = 0
        c = C(1)

        self.assertEqual(astuple(c), (1, 0))
        self.assertEqual(astuple(c), astuple(c))
        self.assertIsNot(astuple(c), astuple(c))
        c.y = 42
        self.assertEqual(astuple(c), (1, 42))
        self.assertIs(type(astuple(c)), tuple)

    def test_helper_astuple_raises_on_classes(self):
        # astuple() should wirf on a klasse object.
        @dataclass
        klasse C:
            x: int
            y: int
        mit self.assertRaisesRegex(TypeError, 'dataclass instance'):
            astuple(C)
        mit self.assertRaisesRegex(TypeError, 'dataclass instance'):
            astuple(int)

    def test_helper_astuple_copy_values(self):
        @dataclass
        klasse C:
            x: int
            y: List[int] = field(default_factory=list)
        initial = []
        c = C(1, initial)
        t = astuple(c)
        self.assertEqual(t[1], initial)
        self.assertIsNot(t[1], initial)
        c = C(1)
        t = astuple(c)
        t[1].append(1)
        self.assertEqual(c.y, [])

    def test_helper_astuple_nested(self):
        @dataclass
        klasse UserId:
            token: int
            group: int
        @dataclass
        klasse User:
            name: str
            id: UserId
        u = User('Joe', UserId(123, 1))
        t = astuple(u)
        self.assertEqual(t, ('Joe', (123, 1)))
        self.assertIsNot(astuple(u), astuple(u))
        u.id.group = 2
        self.assertEqual(astuple(u), ('Joe', (123, 2)))

    def test_helper_astuple_builtin_containers(self):
        @dataclass
        klasse User:
            name: str
            id: int
        @dataclass
        klasse GroupList:
            id: int
            users: List[User]
        @dataclass
        klasse GroupTuple:
            id: int
            users: Tuple[User, ...]
        @dataclass
        klasse GroupDict:
            id: int
            users: Dict[str, User]
        a = User('Alice', 1)
        b = User('Bob', 2)
        gl = GroupList(0, [a, b])
        gt = GroupTuple(0, (a, b))
        gd = GroupDict(0, {'first': a, 'second': b})
        self.assertEqual(astuple(gl), (0, [('Alice', 1), ('Bob', 2)]))
        self.assertEqual(astuple(gt), (0, (('Alice', 1), ('Bob', 2))))
        self.assertEqual(astuple(gd), (0, {'first': ('Alice', 1), 'second': ('Bob', 2)}))

    def test_helper_astuple_builtin_object_containers(self):
        @dataclass
        klasse Child:
            d: object

        @dataclass
        klasse Parent:
            child: Child

        self.assertEqual(astuple(Parent(Child([1]))), (([1],),))
        self.assertEqual(astuple(Parent(Child({1: 2}))), (({1: 2},),))

    def test_helper_astuple_factory(self):
        @dataclass
        klasse C:
            x: int
            y: int
        NT = namedtuple('NT', 'x y')
        def nt(lst):
            gib NT(*lst)
        c = C(1, 2)
        t = astuple(c, tuple_factory=nt)
        self.assertEqual(t, NT(1, 2))
        self.assertIsNot(t, astuple(c, tuple_factory=nt))
        c.x = 42
        t = astuple(c, tuple_factory=nt)
        self.assertEqual(t, NT(42, 2))
        self.assertIs(type(t), NT)

    def test_helper_astuple_namedtuple(self):
        T = namedtuple('T', 'a b c')
        @dataclass
        klasse C:
            x: str
            y: T
        c = C('outer', T(1, C('inner', T(11, 12, 13)), 2))

        t = astuple(c)
        self.assertEqual(t, ('outer', T(1, ('inner', (11, 12, 13)), 2)))

        # Now, using a tuple_factory.  list is convenient here.
        t = astuple(c, tuple_factory=list)
        self.assertEqual(t, ['outer', T(1, ['inner', T(11, 12, 13)], 2)])

    def test_helper_astuple_defaultdict(self):
        # Ensure astuple() does nicht throw exceptions when a
        # defaultdict is a member of a dataclass
        @dataclass
        klasse C:
            mp: DefaultDict[str, List]

        dd = defaultdict(list)
        dd["x"].append(12)
        c = C(mp=dd)
        t = astuple(c)

        self.assertEqual(t, ({"x": [12]},))
        self.assertWahr(t[0] is nicht dd) # make sure defaultdict is copied

    def test_dynamic_class_creation(self):
        cls_dict = {'__annotations__': {'x': int, 'y': int},
                    }

        # Create the class.
        cls = type('C', (), cls_dict)

        # Make it a dataclass.
        cls1 = dataclass(cls)

        self.assertEqual(cls1, cls)
        self.assertEqual(asdict(cls(1, 2)), {'x': 1, 'y': 2})

    def test_dynamic_class_creation_using_field(self):
        cls_dict = {'__annotations__': {'x': int, 'y': int},
                    'y': field(default=5),
                    }

        # Create the class.
        cls = type('C', (), cls_dict)

        # Make it a dataclass.
        cls1 = dataclass(cls)

        self.assertEqual(cls1, cls)
        self.assertEqual(asdict(cls1(1)), {'x': 1, 'y': 5})

    def test_init_in_order(self):
        @dataclass
        klasse C:
            a: int
            b: int = field()
            c: list = field(default_factory=list, init=Falsch)
            d: list = field(default_factory=list)
            e: int = field(default=4, init=Falsch)
            f: int = 4

        calls = []
        def setattr(self, name, value):
            calls.append((name, value))

        C.__setattr__ = setattr
        c = C(0, 1)
        self.assertEqual(('a', 0), calls[0])
        self.assertEqual(('b', 1), calls[1])
        self.assertEqual(('c', []), calls[2])
        self.assertEqual(('d', []), calls[3])
        self.assertNotIn(('e', 4), calls)
        self.assertEqual(('f', 4), calls[4])

    def test_items_in_dicts(self):
        @dataclass
        klasse C:
            a: int
            b: list = field(default_factory=list, init=Falsch)
            c: list = field(default_factory=list)
            d: int = field(default=4, init=Falsch)
            e: int = 0

        c = C(0)
        # Class dict
        self.assertNotIn('a', C.__dict__)
        self.assertNotIn('b', C.__dict__)
        self.assertNotIn('c', C.__dict__)
        self.assertIn('d', C.__dict__)
        self.assertEqual(C.d, 4)
        self.assertIn('e', C.__dict__)
        self.assertEqual(C.e, 0)
        # Instance dict
        self.assertIn('a', c.__dict__)
        self.assertEqual(c.a, 0)
        self.assertIn('b', c.__dict__)
        self.assertEqual(c.b, [])
        self.assertIn('c', c.__dict__)
        self.assertEqual(c.c, [])
        self.assertNotIn('d', c.__dict__)
        self.assertIn('e', c.__dict__)
        self.assertEqual(c.e, 0)

    def test_alternate_classmethod_constructor(self):
        # Since __post_init__ can't take params, use a classmethod
        #  alternate constructor.  This is mostly an example to show
        #  how to use this technique.
        @dataclass
        klasse C:
            x: int
            @classmethod
            def from_file(cls, filename):
                # In a real example, create a new instance
                #  und populate 'x' von contents of a file.
                value_in_file = 20
                gib cls(value_in_file)

        self.assertEqual(C.from_file('filename').x, 20)

    def test_field_metadata_default(self):
        # Make sure the default metadata is read-only und of
        #  zero length.
        @dataclass
        klasse C:
            i: int

        self.assertFalsch(fields(C)[0].metadata)
        self.assertEqual(len(fields(C)[0].metadata), 0)
        mit self.assertRaisesRegex(TypeError,
                                    'does nicht support item assignment'):
            fields(C)[0].metadata['test'] = 3

    def test_field_metadata_mapping(self):
        # Make sure only a mapping can be passed als metadata
        #  zero length.
        mit self.assertRaises(TypeError):
            @dataclass
            klasse C:
                i: int = field(metadata=0)

        # Make sure an empty dict works.
        d = {}
        @dataclass
        klasse C:
            i: int = field(metadata=d)
        self.assertFalsch(fields(C)[0].metadata)
        self.assertEqual(len(fields(C)[0].metadata), 0)
        # Update should work (see bpo-35960).
        d['foo'] = 1
        self.assertEqual(len(fields(C)[0].metadata), 1)
        self.assertEqual(fields(C)[0].metadata['foo'], 1)
        mit self.assertRaisesRegex(TypeError,
                                    'does nicht support item assignment'):
            fields(C)[0].metadata['test'] = 3

        # Make sure a non-empty dict works.
        d = {'test': 10, 'bar': '42', 3: 'three'}
        @dataclass
        klasse C:
            i: int = field(metadata=d)
        self.assertEqual(len(fields(C)[0].metadata), 3)
        self.assertEqual(fields(C)[0].metadata['test'], 10)
        self.assertEqual(fields(C)[0].metadata['bar'], '42')
        self.assertEqual(fields(C)[0].metadata[3], 'three')
        # Update should work.
        d['foo'] = 1
        self.assertEqual(len(fields(C)[0].metadata), 4)
        self.assertEqual(fields(C)[0].metadata['foo'], 1)
        mit self.assertRaises(KeyError):
            # Non-existent key.
            fields(C)[0].metadata['baz']
        mit self.assertRaisesRegex(TypeError,
                                    'does nicht support item assignment'):
            fields(C)[0].metadata['test'] = 3

    def test_field_metadata_custom_mapping(self):
        # Try a custom mapping.
        klasse SimpleNameSpace:
            def __init__(self, **kw):
                self.__dict__.update(kw)

            def __getitem__(self, item):
                wenn item == 'xyzzy':
                    gib 'plugh'
                gib getattr(self, item)

            def __len__(self):
                gib self.__dict__.__len__()

        @dataclass
        klasse C:
            i: int = field(metadata=SimpleNameSpace(a=10))

        self.assertEqual(len(fields(C)[0].metadata), 1)
        self.assertEqual(fields(C)[0].metadata['a'], 10)
        mit self.assertRaises(AttributeError):
            fields(C)[0].metadata['b']
        # Make sure we're still talking to our custom mapping.
        self.assertEqual(fields(C)[0].metadata['xyzzy'], 'plugh')

    def test_generic_dataclasses(self):
        T = TypeVar('T')

        @dataclass
        klasse LabeledBox(Generic[T]):
            content: T
            label: str = '<unknown>'

        box = LabeledBox(42)
        self.assertEqual(box.content, 42)
        self.assertEqual(box.label, '<unknown>')

        # Subscripting the resulting klasse should work, etc.
        Alias = List[LabeledBox[int]]

    def test_generic_extending(self):
        S = TypeVar('S')
        T = TypeVar('T')

        @dataclass
        klasse Base(Generic[T, S]):
            x: T
            y: S

        @dataclass
        klasse DataDerived(Base[int, T]):
            new_field: str
        Alias = DataDerived[str]
        c = Alias(0, 'test1', 'test2')
        self.assertEqual(astuple(c), (0, 'test1', 'test2'))

        klasse NonDataDerived(Base[int, T]):
            def new_method(self):
                gib self.y
        Alias = NonDataDerived[float]
        c = Alias(10, 1.0)
        self.assertEqual(c.new_method(), 1.0)

    def test_generic_dynamic(self):
        T = TypeVar('T')

        @dataclass
        klasse Parent(Generic[T]):
            x: T
        Child = make_dataclass('Child', [('y', T), ('z', Optional[T], Nichts)],
                               bases=(Parent[int], Generic[T]), namespace={'other': 42})
        self.assertIs(Child[int](1, 2).z, Nichts)
        self.assertEqual(Child[int](1, 2, 3).z, 3)
        self.assertEqual(Child[int](1, 2, 3).other, 42)
        # Check that type aliases work correctly.
        Alias = Child[T]
        self.assertEqual(Alias[int](1, 2).x, 1)
        # Check MRO resolution.
        self.assertEqual(Child.__mro__, (Child, Parent, Generic, object))

    def test_dataclasses_pickleable(self):
        global P, Q, R
        @dataclass
        klasse P:
            x: int
            y: int = 0
        @dataclass
        klasse Q:
            x: int
            y: int = field(default=0, init=Falsch)
        @dataclass
        klasse R:
            x: int
            y: List[int] = field(default_factory=list)
        q = Q(1)
        q.y = 2
        samples = [P(1), P(1, 2), Q(1), q, R(1), R(1, [2, 3, 4])]
        fuer sample in samples:
            fuer proto in range(pickle.HIGHEST_PROTOCOL + 1):
                mit self.subTest(sample=sample, proto=proto):
                    new_sample = pickle.loads(pickle.dumps(sample, proto))
                    self.assertEqual(sample.x, new_sample.x)
                    self.assertEqual(sample.y, new_sample.y)
                    self.assertIsNot(sample, new_sample)
                    new_sample.x = 42
                    another_new_sample = pickle.loads(pickle.dumps(new_sample, proto))
                    self.assertEqual(new_sample.x, another_new_sample.x)
                    self.assertEqual(sample.y, another_new_sample.y)

    def test_dataclasses_qualnames(self):
        @dataclass(order=Wahr, unsafe_hash=Wahr, frozen=Wahr)
        klasse A:
            x: int
            y: int

        self.assertEqual(A.__init__.__name__, "__init__")
        fuer function in (
            '__eq__',
            '__lt__',
            '__le__',
            '__gt__',
            '__ge__',
            '__hash__',
            '__init__',
            '__repr__',
            '__setattr__',
            '__delattr__',
        ):
            self.assertEqual(getattr(A, function).__qualname__, f"TestCase.test_dataclasses_qualnames.<locals>.A.{function}")

        mit self.assertRaisesRegex(TypeError, r"A\.__init__\(\) missing"):
            A()


klasse TestFieldNoAnnotation(unittest.TestCase):
    def test_field_without_annotation(self):
        mit self.assertRaisesRegex(TypeError,
                                    "'f' is a field but has no type annotation"):
            @dataclass
            klasse C:
                f = field()

    def test_field_without_annotation_but_annotation_in_base(self):
        @dataclass
        klasse B:
            f: int

        mit self.assertRaisesRegex(TypeError,
                                    "'f' is a field but has no type annotation"):
            # This is still an error: make sure we don't pick up the
            #  type annotation in the base class.
            @dataclass
            klasse C(B):
                f = field()

    def test_field_without_annotation_but_annotation_in_base_not_dataclass(self):
        # Same test, but mit the base klasse nicht a dataclass.
        klasse B:
            f: int

        mit self.assertRaisesRegex(TypeError,
                                    "'f' is a field but has no type annotation"):
            # This is still an error: make sure we don't pick up the
            #  type annotation in the base class.
            @dataclass
            klasse C(B):
                f = field()


klasse TestDocString(unittest.TestCase):
    def assertDocStrEqual(self, a, b):
        # Because 3.6 und 3.7 differ in how inspect.signature work
        #  (see bpo #32108), fuer the time being just compare them with
        #  whitespace stripped.
        self.assertEqual(a.replace(' ', ''), b.replace(' ', ''))

    @support.requires_docstrings
    def test_existing_docstring_not_overridden(self):
        @dataclass
        klasse C:
            """Lorem ipsum"""
            x: int

        self.assertEqual(C.__doc__, "Lorem ipsum")

    def test_docstring_no_fields(self):
        @dataclass
        klasse C:
            pass

        self.assertDocStrEqual(C.__doc__, "C()")

    def test_docstring_one_field(self):
        @dataclass
        klasse C:
            x: int

        self.assertDocStrEqual(C.__doc__, "C(x:int)")

    def test_docstring_two_fields(self):
        @dataclass
        klasse C:
            x: int
            y: int

        self.assertDocStrEqual(C.__doc__, "C(x:int, y:int)")

    def test_docstring_three_fields(self):
        @dataclass
        klasse C:
            x: int
            y: int
            z: str

        self.assertDocStrEqual(C.__doc__, "C(x:int, y:int, z:str)")

    def test_docstring_one_field_with_default(self):
        @dataclass
        klasse C:
            x: int = 3

        self.assertDocStrEqual(C.__doc__, "C(x:int=3)")

    def test_docstring_one_field_with_default_none(self):
        @dataclass
        klasse C:
            x: Union[int, type(Nichts)] = Nichts

        self.assertDocStrEqual(C.__doc__, "C(x:int|Nichts=Nichts)")

    def test_docstring_list_field(self):
        @dataclass
        klasse C:
            x: List[int]

        self.assertDocStrEqual(C.__doc__, "C(x:List[int])")

    def test_docstring_list_field_with_default_factory(self):
        @dataclass
        klasse C:
            x: List[int] = field(default_factory=list)

        self.assertDocStrEqual(C.__doc__, "C(x:List[int]=<factory>)")

    def test_docstring_deque_field(self):
        @dataclass
        klasse C:
            x: deque

        self.assertDocStrEqual(C.__doc__, "C(x:collections.deque)")

    def test_docstring_deque_field_with_default_factory(self):
        @dataclass
        klasse C:
            x: deque = field(default_factory=deque)

        self.assertDocStrEqual(C.__doc__, "C(x:collections.deque=<factory>)")

    def test_docstring_undefined_name(self):
        @dataclass
        klasse C:
            x: undef

        self.assertDocStrEqual(C.__doc__, "C(x:undef)")

    def test_docstring_with_unsolvable_forward_ref_in_init(self):
        # See: https://github.com/python/cpython/issues/128184
        ns = {}
        exec(
            textwrap.dedent(
                """
                von dataclasses importiere dataclass

                @dataclass
                klasse C:
                    def __init__(self, x: X, num: int) -> Nichts: ...
                """,
            ),
            ns,
        )

        self.assertDocStrEqual(ns['C'].__doc__, "C(x:X,num:int)")

    def test_docstring_with_no_signature(self):
        # See https://github.com/python/cpython/issues/103449
        klasse Meta(type):
            __call__ = dict
        klasse Base(metaclass=Meta):
            pass

        @dataclass
        klasse C(Base):
            pass

        self.assertDocStrEqual(C.__doc__, "C")


klasse TestInit(unittest.TestCase):
    def test_base_has_init(self):
        klasse B:
            def __init__(self):
                self.z = 100

        # Make sure that declaring this klasse doesn't wirf an error.
        #  The issue is that we can't override __init__ in our class,
        #  but it should be okay to add __init__ to us wenn our base has
        #  an __init__.
        @dataclass
        klasse C(B):
            x: int = 0
        c = C(10)
        self.assertEqual(c.x, 10)
        self.assertNotIn('z', vars(c))

        # Make sure that wenn we don't add an init, the base __init__
        #  gets called.
        @dataclass(init=Falsch)
        klasse C(B):
            x: int = 10
        c = C()
        self.assertEqual(c.x, 10)
        self.assertEqual(c.z, 100)

    def test_no_init(self):
        @dataclass(init=Falsch)
        klasse C:
            i: int = 0
        self.assertEqual(C().i, 0)

        @dataclass(init=Falsch)
        klasse C:
            i: int = 2
            def __init__(self):
                self.i = 3
        self.assertEqual(C().i, 3)

    def test_overwriting_init(self):
        # If the klasse has __init__, use it no matter the value of
        #  init=.

        @dataclass
        klasse C:
            x: int
            def __init__(self, x):
                self.x = 2 * x
        self.assertEqual(C(3).x, 6)

        @dataclass(init=Wahr)
        klasse C:
            x: int
            def __init__(self, x):
                self.x = 2 * x
        self.assertEqual(C(4).x, 8)

        @dataclass(init=Falsch)
        klasse C:
            x: int
            def __init__(self, x):
                self.x = 2 * x
        self.assertEqual(C(5).x, 10)

    def test_inherit_from_protocol(self):
        # Dataclasses inheriting von protocol should preserve their own `__init__`.
        # See bpo-45081.

        klasse P(Protocol):
            a: int

        @dataclass
        klasse C(P):
            a: int

        self.assertEqual(C(5).a, 5)

        @dataclass
        klasse D(P):
            def __init__(self, a):
                self.a = a * 2

        self.assertEqual(D(5).a, 10)


klasse TestRepr(unittest.TestCase):
    def test_repr(self):
        @dataclass
        klasse B:
            x: int

        @dataclass
        klasse C(B):
            y: int = 10

        o = C(4)
        self.assertEqual(repr(o), 'TestRepr.test_repr.<locals>.C(x=4, y=10)')

        @dataclass
        klasse D(C):
            x: int = 20
        self.assertEqual(repr(D()), 'TestRepr.test_repr.<locals>.D(x=20, y=10)')

        @dataclass
        klasse C:
            @dataclass
            klasse D:
                i: int
            @dataclass
            klasse E:
                pass
        self.assertEqual(repr(C.D(0)), 'TestRepr.test_repr.<locals>.C.D(i=0)')
        self.assertEqual(repr(C.E()), 'TestRepr.test_repr.<locals>.C.E()')

    def test_no_repr(self):
        # Test a klasse mit no __repr__ und repr=Falsch.
        @dataclass(repr=Falsch)
        klasse C:
            x: int
        self.assertIn(f'{__name__}.TestRepr.test_no_repr.<locals>.C object at',
                      repr(C(3)))

        # Test a klasse mit a __repr__ und repr=Falsch.
        @dataclass(repr=Falsch)
        klasse C:
            x: int
            def __repr__(self):
                gib 'C-class'
        self.assertEqual(repr(C(3)), 'C-class')

    def test_overwriting_repr(self):
        # If the klasse has __repr__, use it no matter the value of
        #  repr=.

        @dataclass
        klasse C:
            x: int
            def __repr__(self):
                gib 'x'
        self.assertEqual(repr(C(0)), 'x')

        @dataclass(repr=Wahr)
        klasse C:
            x: int
            def __repr__(self):
                gib 'x'
        self.assertEqual(repr(C(0)), 'x')

        @dataclass(repr=Falsch)
        klasse C:
            x: int
            def __repr__(self):
                gib 'x'
        self.assertEqual(repr(C(0)), 'x')


klasse TestEq(unittest.TestCase):
    def test_recursive_eq(self):
        # Test a klasse mit recursive child
        @dataclass
        klasse C:
            recursive: object = ...
        c = C()
        c.recursive = c
        self.assertEqual(c, c)

    def test_no_eq(self):
        # Test a klasse mit no __eq__ und eq=Falsch.
        @dataclass(eq=Falsch)
        klasse C:
            x: int
        self.assertNotEqual(C(0), C(0))
        c = C(3)
        self.assertEqual(c, c)

        # Test a klasse mit an __eq__ und eq=Falsch.
        @dataclass(eq=Falsch)
        klasse C:
            x: int
            def __eq__(self, other):
                gib other == 10
        self.assertEqual(C(3), 10)

    def test_overwriting_eq(self):
        # If the klasse has __eq__, use it no matter the value of
        #  eq=.

        @dataclass
        klasse C:
            x: int
            def __eq__(self, other):
                gib other == 3
        self.assertEqual(C(1), 3)
        self.assertNotEqual(C(1), 1)

        @dataclass(eq=Wahr)
        klasse C:
            x: int
            def __eq__(self, other):
                gib other == 4
        self.assertEqual(C(1), 4)
        self.assertNotEqual(C(1), 1)

        @dataclass(eq=Falsch)
        klasse C:
            x: int
            def __eq__(self, other):
                gib other == 5
        self.assertEqual(C(1), 5)
        self.assertNotEqual(C(1), 1)


klasse TestOrdering(unittest.TestCase):
    def test_functools_total_ordering(self):
        # Test that functools.total_ordering works mit this class.
        @total_ordering
        @dataclass
        klasse C:
            x: int
            def __lt__(self, other):
                # Perform the test "backward", just to make
                #  sure this is being called.
                gib self.x >= other

        self.assertLess(C(0), -1)
        self.assertLessEqual(C(0), -1)
        self.assertGreater(C(0), 1)
        self.assertGreaterEqual(C(0), 1)

    def test_no_order(self):
        # Test that no ordering functions are added by default.
        @dataclass(order=Falsch)
        klasse C:
            x: int
        # Make sure no order methods are added.
        self.assertNotIn('__le__', C.__dict__)
        self.assertNotIn('__lt__', C.__dict__)
        self.assertNotIn('__ge__', C.__dict__)
        self.assertNotIn('__gt__', C.__dict__)

        # Test that __lt__ is still called
        @dataclass(order=Falsch)
        klasse C:
            x: int
            def __lt__(self, other):
                gib Falsch
        # Make sure other methods aren't added.
        self.assertNotIn('__le__', C.__dict__)
        self.assertNotIn('__ge__', C.__dict__)
        self.assertNotIn('__gt__', C.__dict__)

    def test_overwriting_order(self):
        mit self.assertRaisesRegex(TypeError,
                                    'Cannot overwrite attribute __lt__'
                                    '.*using functools.total_ordering'):
            @dataclass(order=Wahr)
            klasse C:
                x: int
                def __lt__(self):
                    pass

        mit self.assertRaisesRegex(TypeError,
                                    'Cannot overwrite attribute __le__'
                                    '.*using functools.total_ordering'):
            @dataclass(order=Wahr)
            klasse C:
                x: int
                def __le__(self):
                    pass

        mit self.assertRaisesRegex(TypeError,
                                    'Cannot overwrite attribute __gt__'
                                    '.*using functools.total_ordering'):
            @dataclass(order=Wahr)
            klasse C:
                x: int
                def __gt__(self):
                    pass

        mit self.assertRaisesRegex(TypeError,
                                    'Cannot overwrite attribute __ge__'
                                    '.*using functools.total_ordering'):
            @dataclass(order=Wahr)
            klasse C:
                x: int
                def __ge__(self):
                    pass

klasse TestHash(unittest.TestCase):
    def test_unsafe_hash(self):
        @dataclass(unsafe_hash=Wahr)
        klasse C:
            x: int
            y: str
        self.assertEqual(hash(C(1, 'foo')), hash((1, 'foo')))

    def test_hash_rules(self):
        def non_bool(value):
            # Map to something sonst that's Wahr, but nicht a bool.
            wenn value is Nichts:
                gib Nichts
            wenn value:
                gib (3,)
            gib 0

        def test(case, unsafe_hash, eq, frozen, with_hash, result):
            mit self.subTest(case=case, unsafe_hash=unsafe_hash, eq=eq,
                              frozen=frozen):
                wenn result != 'exception':
                    wenn with_hash:
                        @dataclass(unsafe_hash=unsafe_hash, eq=eq, frozen=frozen)
                        klasse C:
                            def __hash__(self):
                                gib 0
                    sonst:
                        @dataclass(unsafe_hash=unsafe_hash, eq=eq, frozen=frozen)
                        klasse C:
                            pass

                # See wenn the result matches what's expected.
                wenn result == 'fn':
                    # __hash__ contains the function we generated.
                    self.assertIn('__hash__', C.__dict__)
                    self.assertIsNotNichts(C.__dict__['__hash__'])

                sowenn result == '':
                    # __hash__ is nicht present in our class.
                    wenn nicht with_hash:
                        self.assertNotIn('__hash__', C.__dict__)

                sowenn result == 'none':
                    # __hash__ is set to Nichts.
                    self.assertIn('__hash__', C.__dict__)
                    self.assertIsNichts(C.__dict__['__hash__'])

                sowenn result == 'exception':
                    # Creating the klasse should cause an exception.
                    #  This only happens mit with_hash==Wahr.
                    assert(with_hash)
                    mit self.assertRaisesRegex(TypeError, 'Cannot overwrite attribute __hash__'):
                        @dataclass(unsafe_hash=unsafe_hash, eq=eq, frozen=frozen)
                        klasse C:
                            def __hash__(self):
                                gib 0

                sonst:
                    assert Falsch, f'unknown result {result!r}'

        # There are 8 cases of:
        #  unsafe_hash=Wahr/Falsch
        #  eq=Wahr/Falsch
        #  frozen=Wahr/Falsch
        # And fuer each of these, a different result if
        #  __hash__ is defined oder not.
        fuer case, (unsafe_hash,  eq,    frozen, res_no_defined_hash, res_defined_hash) in enumerate([
                  (Falsch,        Falsch, Falsch,  '',                  ''),
                  (Falsch,        Falsch, Wahr,   '',                  ''),
                  (Falsch,        Wahr,  Falsch,  'none',              ''),
                  (Falsch,        Wahr,  Wahr,   'fn',                ''),
                  (Wahr,         Falsch, Falsch,  'fn',                'exception'),
                  (Wahr,         Falsch, Wahr,   'fn',                'exception'),
                  (Wahr,         Wahr,  Falsch,  'fn',                'exception'),
                  (Wahr,         Wahr,  Wahr,   'fn',                'exception'),
                  ], 1):
            test(case, unsafe_hash, eq, frozen, Falsch, res_no_defined_hash)
            test(case, unsafe_hash, eq, frozen, Wahr,  res_defined_hash)

            # Test non-bool truth values, too.  This is just to
            #  make sure the data-driven table in the decorator
            #  handles non-bool values.
            test(case, non_bool(unsafe_hash), non_bool(eq), non_bool(frozen), Falsch, res_no_defined_hash)
            test(case, non_bool(unsafe_hash), non_bool(eq), non_bool(frozen), Wahr,  res_defined_hash)


    def test_eq_only(self):
        # If a klasse defines __eq__, __hash__ is automatically added
        #  und set to Nichts.  This is normal Python behavior, not
        #  related to dataclasses.  Make sure we don't interfere with
        #  that (see bpo=32546).

        @dataclass
        klasse C:
            i: int
            def __eq__(self, other):
                gib self.i == other.i
        self.assertEqual(C(1), C(1))
        self.assertNotEqual(C(1), C(4))

        # And make sure things work in this case wenn we specify
        #  unsafe_hash=Wahr.
        @dataclass(unsafe_hash=Wahr)
        klasse C:
            i: int
            def __eq__(self, other):
                gib self.i == other.i
        self.assertEqual(C(1), C(1.0))
        self.assertEqual(hash(C(1)), hash(C(1.0)))

        # And check that the classes __eq__ is being used, despite
        #  specifying eq=Wahr.
        @dataclass(unsafe_hash=Wahr, eq=Wahr)
        klasse C:
            i: int
            def __eq__(self, other):
                gib self.i == 3 und self.i == other.i
        self.assertEqual(C(3), C(3))
        self.assertNotEqual(C(1), C(1))
        self.assertEqual(hash(C(1)), hash(C(1.0)))

    def test_0_field_hash(self):
        @dataclass(frozen=Wahr)
        klasse C:
            pass
        self.assertEqual(hash(C()), hash(()))

        @dataclass(unsafe_hash=Wahr)
        klasse C:
            pass
        self.assertEqual(hash(C()), hash(()))

    def test_1_field_hash(self):
        @dataclass(frozen=Wahr)
        klasse C:
            x: int
        self.assertEqual(hash(C(4)), hash((4,)))
        self.assertEqual(hash(C(42)), hash((42,)))

        @dataclass(unsafe_hash=Wahr)
        klasse C:
            x: int
        self.assertEqual(hash(C(4)), hash((4,)))
        self.assertEqual(hash(C(42)), hash((42,)))

    def test_hash_no_args(self):
        # Test dataclasses mit no hash= argument.  This exists to
        #  make sure that wenn the @dataclass parameter name is changed
        #  oder the non-default hashing behavior changes, the default
        #  hashability keeps working the same way.

        klasse Base:
            def __hash__(self):
                gib 301

        # If frozen oder eq is Nichts, then use the default value (do not
        #  specify any value in the decorator).
        fuer frozen, eq,    base,   expected       in [
            (Nichts,  Nichts,  object, 'unhashable'),
            (Nichts,  Nichts,  Base,   'unhashable'),
            (Nichts,  Falsch, object, 'object'),
            (Nichts,  Falsch, Base,   'base'),
            (Nichts,  Wahr,  object, 'unhashable'),
            (Nichts,  Wahr,  Base,   'unhashable'),
            (Falsch, Nichts,  object, 'unhashable'),
            (Falsch, Nichts,  Base,   'unhashable'),
            (Falsch, Falsch, object, 'object'),
            (Falsch, Falsch, Base,   'base'),
            (Falsch, Wahr,  object, 'unhashable'),
            (Falsch, Wahr,  Base,   'unhashable'),
            (Wahr,  Nichts,  object, 'tuple'),
            (Wahr,  Nichts,  Base,   'tuple'),
            (Wahr,  Falsch, object, 'object'),
            (Wahr,  Falsch, Base,   'base'),
            (Wahr,  Wahr,  object, 'tuple'),
            (Wahr,  Wahr,  Base,   'tuple'),
            ]:

            mit self.subTest(frozen=frozen, eq=eq, base=base, expected=expected):
                # First, create the class.
                wenn frozen is Nichts und eq is Nichts:
                    @dataclass
                    klasse C(base):
                        i: int
                sowenn frozen is Nichts:
                    @dataclass(eq=eq)
                    klasse C(base):
                        i: int
                sowenn eq is Nichts:
                    @dataclass(frozen=frozen)
                    klasse C(base):
                        i: int
                sonst:
                    @dataclass(frozen=frozen, eq=eq)
                    klasse C(base):
                        i: int

                # Now, make sure it hashes als expected.
                wenn expected == 'unhashable':
                    c = C(10)
                    mit self.assertRaisesRegex(TypeError, 'unhashable type'):
                        hash(c)

                sowenn expected == 'base':
                    self.assertEqual(hash(C(10)), 301)

                sowenn expected == 'object':
                    # I'm nicht sure what test to use here.  object's
                    #  hash isn't based on id(), so calling hash()
                    #  won't tell us much.  So, just check the
                    #  function used is object's.
                    self.assertIs(C.__hash__, object.__hash__)

                sowenn expected == 'tuple':
                    self.assertEqual(hash(C(42)), hash((42,)))

                sonst:
                    assert Falsch, f'unknown value fuer expected={expected!r}'


klasse TestFrozen(unittest.TestCase):
    def test_frozen(self):
        @dataclass(frozen=Wahr)
        klasse C:
            i: int

        c = C(10)
        self.assertEqual(c.i, 10)
        mit self.assertRaises(FrozenInstanceError):
            c.i = 5
        self.assertEqual(c.i, 10)

    def test_frozen_empty(self):
        @dataclass(frozen=Wahr)
        klasse C:
            pass

        c = C()
        self.assertNotHasAttr(c, 'i')
        mit self.assertRaises(FrozenInstanceError):
            c.i = 5
        self.assertNotHasAttr(c, 'i')
        mit self.assertRaises(FrozenInstanceError):
            del c.i

    def test_inherit(self):
        @dataclass(frozen=Wahr)
        klasse C:
            i: int

        @dataclass(frozen=Wahr)
        klasse D(C):
            j: int

        d = D(0, 10)
        mit self.assertRaises(FrozenInstanceError):
            d.i = 5
        mit self.assertRaises(FrozenInstanceError):
            d.j = 6
        self.assertEqual(d.i, 0)
        self.assertEqual(d.j, 10)

    def test_inherit_nonfrozen_from_empty_frozen(self):
        @dataclass(frozen=Wahr)
        klasse C:
            pass

        mit self.assertRaisesRegex(TypeError,
                                    'cannot inherit non-frozen dataclass von a frozen one'):
            @dataclass
            klasse D(C):
                j: int

    def test_inherit_frozen_mutliple_inheritance(self):
        @dataclass
        klasse NotFrozen:
            pass

        @dataclass(frozen=Wahr)
        klasse Frozen:
            pass

        klasse NotDataclass:
            pass

        fuer bases in (
            (NotFrozen, Frozen),
            (Frozen, NotFrozen),
            (Frozen, NotDataclass),
            (NotDataclass, Frozen),
        ):
            mit self.subTest(bases=bases):
                mit self.assertRaisesRegex(
                    TypeError,
                    'cannot inherit non-frozen dataclass von a frozen one',
                ):
                    @dataclass
                    klasse NotFrozenChild(*bases):
                        pass

        fuer bases in (
            (NotFrozen, Frozen),
            (Frozen, NotFrozen),
            (NotFrozen, NotDataclass),
            (NotDataclass, NotFrozen),
        ):
            mit self.subTest(bases=bases):
                mit self.assertRaisesRegex(
                    TypeError,
                    'cannot inherit frozen dataclass von a non-frozen one',
                ):
                    @dataclass(frozen=Wahr)
                    klasse FrozenChild(*bases):
                        pass

    def test_inherit_frozen_mutliple_inheritance_regular_mixins(self):
        @dataclass(frozen=Wahr)
        klasse Frozen:
            pass

        klasse NotDataclass:
            pass

        klasse C1(Frozen, NotDataclass):
            pass
        self.assertEqual(C1.__mro__, (C1, Frozen, NotDataclass, object))

        klasse C2(NotDataclass, Frozen):
            pass
        self.assertEqual(C2.__mro__, (C2, NotDataclass, Frozen, object))

        @dataclass(frozen=Wahr)
        klasse C3(Frozen, NotDataclass):
            pass
        self.assertEqual(C3.__mro__, (C3, Frozen, NotDataclass, object))

        @dataclass(frozen=Wahr)
        klasse C4(NotDataclass, Frozen):
            pass
        self.assertEqual(C4.__mro__, (C4, NotDataclass, Frozen, object))

    def test_multiple_frozen_dataclasses_inheritance(self):
        @dataclass(frozen=Wahr)
        klasse FrozenA:
            pass

        @dataclass(frozen=Wahr)
        klasse FrozenB:
            pass

        klasse C1(FrozenA, FrozenB):
            pass
        self.assertEqual(C1.__mro__, (C1, FrozenA, FrozenB, object))

        klasse C2(FrozenB, FrozenA):
            pass
        self.assertEqual(C2.__mro__, (C2, FrozenB, FrozenA, object))

        @dataclass(frozen=Wahr)
        klasse C3(FrozenA, FrozenB):
            pass
        self.assertEqual(C3.__mro__, (C3, FrozenA, FrozenB, object))

        @dataclass(frozen=Wahr)
        klasse C4(FrozenB, FrozenA):
            pass
        self.assertEqual(C4.__mro__, (C4, FrozenB, FrozenA, object))

    def test_inherit_nonfrozen_from_empty(self):
        @dataclass
        klasse C:
            pass

        @dataclass
        klasse D(C):
            j: int

        d = D(3)
        self.assertEqual(d.j, 3)
        self.assertIsInstance(d, C)

    # Test both ways: mit an intermediate normal (non-dataclass)
    #  klasse und without an intermediate class.
    def test_inherit_nonfrozen_from_frozen(self):
        fuer intermediate_class in [Wahr, Falsch]:
            mit self.subTest(intermediate_class=intermediate_class):
                @dataclass(frozen=Wahr)
                klasse C:
                    i: int

                wenn intermediate_class:
                    klasse I(C): pass
                sonst:
                    I = C

                mit self.assertRaisesRegex(TypeError,
                                            'cannot inherit non-frozen dataclass von a frozen one'):
                    @dataclass
                    klasse D(I):
                        pass

    def test_inherit_frozen_from_nonfrozen(self):
        fuer intermediate_class in [Wahr, Falsch]:
            mit self.subTest(intermediate_class=intermediate_class):
                @dataclass
                klasse C:
                    i: int

                wenn intermediate_class:
                    klasse I(C): pass
                sonst:
                    I = C

                mit self.assertRaisesRegex(TypeError,
                                            'cannot inherit frozen dataclass von a non-frozen one'):
                    @dataclass(frozen=Wahr)
                    klasse D(I):
                        pass

    def test_inherit_from_normal_class(self):
        fuer intermediate_class in [Wahr, Falsch]:
            mit self.subTest(intermediate_class=intermediate_class):
                klasse C:
                    pass

                wenn intermediate_class:
                    klasse I(C): pass
                sonst:
                    I = C

                @dataclass(frozen=Wahr)
                klasse D(I):
                    i: int

            d = D(10)
            mit self.assertRaises(FrozenInstanceError):
                d.i = 5

    def test_non_frozen_normal_derived(self):
        # See bpo-32953.

        @dataclass(frozen=Wahr)
        klasse D:
            x: int
            y: int = 10

        klasse S(D):
            pass

        s = S(3)
        self.assertEqual(s.x, 3)
        self.assertEqual(s.y, 10)
        s.cached = Wahr

        # But can't change the frozen attributes.
        mit self.assertRaises(FrozenInstanceError):
            s.x = 5
        mit self.assertRaises(FrozenInstanceError):
            s.y = 5
        self.assertEqual(s.x, 3)
        self.assertEqual(s.y, 10)
        self.assertEqual(s.cached, Wahr)

        mit self.assertRaises(FrozenInstanceError):
            del s.x
        self.assertEqual(s.x, 3)
        mit self.assertRaises(FrozenInstanceError):
            del s.y
        self.assertEqual(s.y, 10)
        del s.cached
        self.assertNotHasAttr(s, 'cached')
        mit self.assertRaises(AttributeError) als cm:
            del s.cached
        self.assertNotIsInstance(cm.exception, FrozenInstanceError)

    def test_non_frozen_normal_derived_from_empty_frozen(self):
        @dataclass(frozen=Wahr)
        klasse D:
            pass

        klasse S(D):
            pass

        s = S()
        self.assertNotHasAttr(s, 'x')
        s.x = 5
        self.assertEqual(s.x, 5)

        del s.x
        self.assertNotHasAttr(s, 'x')
        mit self.assertRaises(AttributeError) als cm:
            del s.x
        self.assertNotIsInstance(cm.exception, FrozenInstanceError)

    def test_overwriting_frozen(self):
        # frozen uses __setattr__ und __delattr__.
        mit self.assertRaisesRegex(TypeError,
                                    'Cannot overwrite attribute __setattr__'):
            @dataclass(frozen=Wahr)
            klasse C:
                x: int
                def __setattr__(self):
                    pass

        mit self.assertRaisesRegex(TypeError,
                                    'Cannot overwrite attribute __delattr__'):
            @dataclass(frozen=Wahr)
            klasse C:
                x: int
                def __delattr__(self):
                    pass

        @dataclass(frozen=Falsch)
        klasse C:
            x: int
            def __setattr__(self, name, value):
                self.__dict__['x'] = value * 2
        self.assertEqual(C(10).x, 20)

    def test_frozen_hash(self):
        @dataclass(frozen=Wahr)
        klasse C:
            x: Any

        # If x is immutable, we can compute the hash.  No exception is
        # raised.
        hash(C(3))

        # If x is mutable, computing the hash is an error.
        mit self.assertRaisesRegex(TypeError, 'unhashable type'):
            hash(C({}))

    def test_frozen_deepcopy_without_slots(self):
        # see: https://github.com/python/cpython/issues/89683
        @dataclass(frozen=Wahr, slots=Falsch)
        klasse C:
            s: str

        c = C('hello')
        self.assertEqual(deepcopy(c), c)

    def test_frozen_deepcopy_with_slots(self):
        # see: https://github.com/python/cpython/issues/89683
        mit self.subTest('generated __slots__'):
            @dataclass(frozen=Wahr, slots=Wahr)
            klasse C:
                s: str

            c = C('hello')
            self.assertEqual(deepcopy(c), c)

        mit self.subTest('user-defined __slots__ und no __{get,set}state__'):
            @dataclass(frozen=Wahr, slots=Falsch)
            klasse C:
                __slots__ = ('s',)
                s: str

            # mit user-defined slots, __getstate__ und __setstate__ are not
            # automatically added, hence the error
            err = r"^cannot\ assign\ to\ field\ 's'$"
            self.assertRaisesRegex(FrozenInstanceError, err, deepcopy, C(''))

        mit self.subTest('user-defined __slots__ und __{get,set}state__'):
            @dataclass(frozen=Wahr, slots=Falsch)
            klasse C:
                __slots__ = ('s',)
                __getstate__ = dataclasses._dataclass_getstate
                __setstate__ = dataclasses._dataclass_setstate

                s: str

            c = C('hello')
            self.assertEqual(deepcopy(c), c)


klasse TestSlots(unittest.TestCase):
    def test_simple(self):
        @dataclass
        klasse C:
            __slots__ = ('x',)
            x: Any

        # There was a bug where a variable in a slot was assumed to
        #  also have a default value (of type
        #  types.MemberDescriptorType).
        mit self.assertRaisesRegex(TypeError,
                                    r"__init__\(\) missing 1 required positional argument: 'x'"):
            C()

        # We can create an instance, und assign to x.
        c = C(10)
        self.assertEqual(c.x, 10)
        c.x = 5
        self.assertEqual(c.x, 5)

        # We can't assign to anything else.
        mit self.assertRaisesRegex(AttributeError, "'C' object has no attribute 'y'"):
            c.y = 5

    def test_derived_added_field(self):
        # See bpo-33100.
        @dataclass
        klasse Base:
            __slots__ = ('x',)
            x: Any

        @dataclass
        klasse Derived(Base):
            x: int
            y: int

        d = Derived(1, 2)
        self.assertEqual((d.x, d.y), (1, 2))

        # We can add a new field to the derived instance.
        d.z = 10

    def test_generated_slots(self):
        @dataclass(slots=Wahr)
        klasse C:
            x: int
            y: int

        c = C(1, 2)
        self.assertEqual((c.x, c.y), (1, 2))

        c.x = 3
        c.y = 4
        self.assertEqual((c.x, c.y), (3, 4))

        mit self.assertRaisesRegex(AttributeError, "'C' object has no attribute 'z'"):
            c.z = 5

    def test_add_slots_when_slots_exists(self):
        mit self.assertRaisesRegex(TypeError, '^C already specifies __slots__$'):
            @dataclass(slots=Wahr)
            klasse C:
                __slots__ = ('x',)
                x: int

    def test_generated_slots_value(self):

        klasse Root:
            __slots__ = {'x'}

        klasse Root2(Root):
            __slots__ = {'k': '...', 'j': ''}

        klasse Root3(Root2):
            __slots__ = ['h']

        klasse Root4(Root3):
            __slots__ = 'aa'

        @dataclass(slots=Wahr)
        klasse Base(Root4):
            y: int
            j: str
            h: str

        self.assertEqual(Base.__slots__, ('y',))

        @dataclass(slots=Wahr)
        klasse Derived(Base):
            aa: float
            x: str
            z: int
            k: str
            h: str

        self.assertEqual(Derived.__slots__, ('z',))

        @dataclass
        klasse AnotherDerived(Base):
            z: int

        self.assertNotIn('__slots__', AnotherDerived.__dict__)

    def test_slots_with_docs(self):
        klasse Root:
            __slots__ = {'x': 'x'}

        @dataclass(slots=Wahr)
        klasse Base(Root):
            y1: int = field(doc='y1')
            y2: int

        self.assertEqual(Base.__slots__, {'y1': 'y1', 'y2': Nichts})

        @dataclass(slots=Wahr)
        klasse Child(Base):
            z1: int = field(doc='z1')
            z2: int

        self.assertEqual(Child.__slots__, {'z1': 'z1', 'z2': Nichts})

    def test_cant_inherit_from_iterator_slots(self):

        klasse Root:
            __slots__ = iter(['a'])

        klasse Root2(Root):
            __slots__ = ('b', )

        mit self.assertRaisesRegex(
           TypeError,
            "^Slots of 'Root' cannot be determined"
        ):
            @dataclass(slots=Wahr)
            klasse C(Root2):
                x: int

    def test_returns_new_class(self):
        klasse A:
            x: int

        B = dataclass(A, slots=Wahr)
        self.assertIsNot(A, B)

        self.assertNotHasAttr(A, "__slots__")
        self.assertHasAttr(B, "__slots__")

    # Can't be local to test_frozen_pickle.
    @dataclass(frozen=Wahr, slots=Wahr)
    klasse FrozenSlotsClass:
        foo: str
        bar: int

    @dataclass(frozen=Wahr)
    klasse FrozenWithoutSlotsClass:
        foo: str
        bar: int

    def test_frozen_pickle(self):
        # bpo-43999

        self.assertEqual(self.FrozenSlotsClass.__slots__, ("foo", "bar"))
        fuer proto in range(pickle.HIGHEST_PROTOCOL + 1):
            mit self.subTest(proto=proto):
                obj = self.FrozenSlotsClass("a", 1)
                p = pickle.loads(pickle.dumps(obj, protocol=proto))
                self.assertIsNot(obj, p)
                self.assertEqual(obj, p)

                obj = self.FrozenWithoutSlotsClass("a", 1)
                p = pickle.loads(pickle.dumps(obj, protocol=proto))
                self.assertIsNot(obj, p)
                self.assertEqual(obj, p)

    @dataclass(frozen=Wahr, slots=Wahr)
    klasse FrozenSlotsGetStateClass:
        foo: str
        bar: int

        getstate_called: bool = field(default=Falsch, compare=Falsch)

        def __getstate__(self):
            object.__setattr__(self, 'getstate_called', Wahr)
            gib [self.foo, self.bar]

    @dataclass(frozen=Wahr, slots=Wahr)
    klasse FrozenSlotsSetStateClass:
        foo: str
        bar: int

        setstate_called: bool = field(default=Falsch, compare=Falsch)

        def __setstate__(self, state):
            object.__setattr__(self, 'setstate_called', Wahr)
            object.__setattr__(self, 'foo', state[0])
            object.__setattr__(self, 'bar', state[1])

    @dataclass(frozen=Wahr, slots=Wahr)
    klasse FrozenSlotsAllStateClass:
        foo: str
        bar: int

        getstate_called: bool = field(default=Falsch, compare=Falsch)
        setstate_called: bool = field(default=Falsch, compare=Falsch)

        def __getstate__(self):
            object.__setattr__(self, 'getstate_called', Wahr)
            gib [self.foo, self.bar]

        def __setstate__(self, state):
            object.__setattr__(self, 'setstate_called', Wahr)
            object.__setattr__(self, 'foo', state[0])
            object.__setattr__(self, 'bar', state[1])

    def test_frozen_slots_pickle_custom_state(self):
        fuer proto in range(pickle.HIGHEST_PROTOCOL + 1):
            mit self.subTest(proto=proto):
                obj = self.FrozenSlotsGetStateClass('a', 1)
                dumped = pickle.dumps(obj, protocol=proto)

                self.assertWahr(obj.getstate_called)
                self.assertEqual(obj, pickle.loads(dumped))

        fuer proto in range(pickle.HIGHEST_PROTOCOL + 1):
            mit self.subTest(proto=proto):
                obj = self.FrozenSlotsSetStateClass('a', 1)
                obj2 = pickle.loads(pickle.dumps(obj, protocol=proto))

                self.assertWahr(obj2.setstate_called)
                self.assertEqual(obj, obj2)

        fuer proto in range(pickle.HIGHEST_PROTOCOL + 1):
            mit self.subTest(proto=proto):
                obj = self.FrozenSlotsAllStateClass('a', 1)
                dumped = pickle.dumps(obj, protocol=proto)

                self.assertWahr(obj.getstate_called)

                obj2 = pickle.loads(dumped)
                self.assertWahr(obj2.setstate_called)
                self.assertEqual(obj, obj2)

    def test_slots_with_default_no_init(self):
        # Originally reported in bpo-44649.
        @dataclass(slots=Wahr)
        klasse A:
            a: str
            b: str = field(default='b', init=Falsch)

        obj = A("a")
        self.assertEqual(obj.a, 'a')
        self.assertEqual(obj.b, 'b')

    def test_slots_with_default_factory_no_init(self):
        # Originally reported in bpo-44649.
        @dataclass(slots=Wahr)
        klasse A:
            a: str
            b: str = field(default_factory=lambda:'b', init=Falsch)

        obj = A("a")
        self.assertEqual(obj.a, 'a')
        self.assertEqual(obj.b, 'b')

    def test_slots_no_weakref(self):
        @dataclass(slots=Wahr)
        klasse A:
            # No weakref.
            pass

        self.assertNotIn("__weakref__", A.__slots__)
        a = A()
        mit self.assertRaisesRegex(TypeError,
                                    "cannot create weak reference"):
            weakref.ref(a)
        mit self.assertRaises(AttributeError):
            a.__weakref__

    def test_slots_weakref(self):
        @dataclass(slots=Wahr, weakref_slot=Wahr)
        klasse A:
            a: int

        self.assertIn("__weakref__", A.__slots__)
        a = A(1)
        a_ref = weakref.ref(a)

        self.assertIs(a.__weakref__, a_ref)

    def test_slots_weakref_base_str(self):
        klasse Base:
            __slots__ = '__weakref__'

        @dataclass(slots=Wahr)
        klasse A(Base):
            a: int

        # __weakref__ is in the base class, nicht A.  But an A is still weakref-able.
        self.assertIn("__weakref__", Base.__slots__)
        self.assertNotIn("__weakref__", A.__slots__)
        a = A(1)
        weakref.ref(a)

    def test_slots_weakref_base_tuple(self):
        # Same als test_slots_weakref_base, but use a tuple instead of a string
        # in the base class.
        klasse Base:
            __slots__ = ('__weakref__',)

        @dataclass(slots=Wahr)
        klasse A(Base):
            a: int

        # __weakref__ is in the base class, nicht A.  But an A is still
        # weakref-able.
        self.assertIn("__weakref__", Base.__slots__)
        self.assertNotIn("__weakref__", A.__slots__)
        a = A(1)
        weakref.ref(a)

    def test_weakref_slot_without_slot(self):
        mit self.assertRaisesRegex(TypeError,
                                    "weakref_slot is Wahr but slots is Falsch"):
            @dataclass(weakref_slot=Wahr)
            klasse A:
                a: int

    def test_weakref_slot_make_dataclass(self):
        A = make_dataclass('A', [('a', int),], slots=Wahr, weakref_slot=Wahr)
        self.assertIn("__weakref__", A.__slots__)
        a = A(1)
        weakref.ref(a)

        # And make sure wenn raises wenn slots=Wahr is nicht given.
        mit self.assertRaisesRegex(TypeError,
                                    "weakref_slot is Wahr but slots is Falsch"):
            B = make_dataclass('B', [('a', int),], weakref_slot=Wahr)

    def test_weakref_slot_subclass_weakref_slot(self):
        @dataclass(slots=Wahr, weakref_slot=Wahr)
        klasse Base:
            field: int

        # A *can* also specify weakref_slot=Wahr wenn it wants to (gh-93521)
        @dataclass(slots=Wahr, weakref_slot=Wahr)
        klasse A(Base):
            ...

        # __weakref__ is in the base class, nicht A.  But an instance of A
        # is still weakref-able.
        self.assertIn("__weakref__", Base.__slots__)
        self.assertNotIn("__weakref__", A.__slots__)
        a = A(1)
        a_ref = weakref.ref(a)
        self.assertIs(a.__weakref__, a_ref)

    def test_weakref_slot_subclass_no_weakref_slot(self):
        @dataclass(slots=Wahr, weakref_slot=Wahr)
        klasse Base:
            field: int

        @dataclass(slots=Wahr)
        klasse A(Base):
            ...

        # __weakref__ is in the base class, nicht A.  Even though A doesn't
        # specify weakref_slot, it should still be weakref-able.
        self.assertIn("__weakref__", Base.__slots__)
        self.assertNotIn("__weakref__", A.__slots__)
        a = A(1)
        a_ref = weakref.ref(a)
        self.assertIs(a.__weakref__, a_ref)

    def test_weakref_slot_normal_base_weakref_slot(self):
        klasse Base:
            __slots__ = ('__weakref__',)

        @dataclass(slots=Wahr, weakref_slot=Wahr)
        klasse A(Base):
            field: int

        # __weakref__ is in the base class, nicht A.  But an instance of
        # A is still weakref-able.
        self.assertIn("__weakref__", Base.__slots__)
        self.assertNotIn("__weakref__", A.__slots__)
        a = A(1)
        a_ref = weakref.ref(a)
        self.assertIs(a.__weakref__, a_ref)

    def test_dataclass_derived_weakref_slot(self):
        klasse A:
            pass

        @dataclass(slots=Wahr, weakref_slot=Wahr)
        klasse B(A):
            pass

        self.assertEqual(B.__slots__, ())
        B()

    def test_dataclass_derived_generic(self):
        T = typing.TypeVar('T')

        @dataclass(slots=Wahr, weakref_slot=Wahr)
        klasse A(typing.Generic[T]):
            pass
        self.assertEqual(A.__slots__, ('__weakref__',))
        self.assertWahr(A.__weakref__)
        A()

        @dataclass(slots=Wahr, weakref_slot=Wahr)
        klasse B[T2]:
            pass
        self.assertEqual(B.__slots__, ('__weakref__',))
        self.assertWahr(B.__weakref__)
        B()

    def test_dataclass_derived_generic_from_base(self):
        T = typing.TypeVar('T')

        klasse RawBase: ...

        @dataclass(slots=Wahr, weakref_slot=Wahr)
        klasse C1(typing.Generic[T], RawBase):
            pass
        self.assertEqual(C1.__slots__, ())
        self.assertWahr(C1.__weakref__)
        C1()
        @dataclass(slots=Wahr, weakref_slot=Wahr)
        klasse C2(RawBase, typing.Generic[T]):
            pass
        self.assertEqual(C2.__slots__, ())
        self.assertWahr(C2.__weakref__)
        C2()

        @dataclass(slots=Wahr, weakref_slot=Wahr)
        klasse D[T2](RawBase):
            pass
        self.assertEqual(D.__slots__, ())
        self.assertWahr(D.__weakref__)
        D()

    def test_dataclass_derived_generic_from_slotted_base(self):
        T = typing.TypeVar('T')

        klasse WithSlots:
            __slots__ = ('a', 'b')

        @dataclass(slots=Wahr, weakref_slot=Wahr)
        klasse E1(WithSlots, Generic[T]):
            pass
        self.assertEqual(E1.__slots__, ('__weakref__',))
        self.assertWahr(E1.__weakref__)
        E1()
        @dataclass(slots=Wahr, weakref_slot=Wahr)
        klasse E2(Generic[T], WithSlots):
            pass
        self.assertEqual(E2.__slots__, ('__weakref__',))
        self.assertWahr(E2.__weakref__)
        E2()

        @dataclass(slots=Wahr, weakref_slot=Wahr)
        klasse F[T2](WithSlots):
            pass
        self.assertEqual(F.__slots__, ('__weakref__',))
        self.assertWahr(F.__weakref__)
        F()

    def test_dataclass_derived_generic_from_slotted_base_with_weakref(self):
        T = typing.TypeVar('T')

        klasse WithWeakrefSlot:
            __slots__ = ('__weakref__',)

        @dataclass(slots=Wahr, weakref_slot=Wahr)
        klasse G1(WithWeakrefSlot, Generic[T]):
            pass
        self.assertEqual(G1.__slots__, ())
        self.assertWahr(G1.__weakref__)
        G1()
        @dataclass(slots=Wahr, weakref_slot=Wahr)
        klasse G2(Generic[T], WithWeakrefSlot):
            pass
        self.assertEqual(G2.__slots__, ())
        self.assertWahr(G2.__weakref__)
        G2()

        @dataclass(slots=Wahr, weakref_slot=Wahr)
        klasse H[T2](WithWeakrefSlot):
            pass
        self.assertEqual(H.__slots__, ())
        self.assertWahr(H.__weakref__)
        H()

    def test_dataclass_slot_dict(self):
        klasse WithDictSlot:
            __slots__ = ('__dict__',)

        @dataclass(slots=Wahr)
        klasse A(WithDictSlot): ...

        self.assertEqual(A.__slots__, ())
        self.assertEqual(A().__dict__, {})
        A()

    @support.cpython_only
    def test_dataclass_slot_dict_ctype(self):
        # https://github.com/python/cpython/issues/123935
        # Skips test wenn `_testcapi` is nicht present:
        _testcapi = import_helper.import_module('_testcapi')

        @dataclass(slots=Wahr)
        klasse HasDictOffset(_testcapi.HeapCTypeWithDict):
            __dict__: dict = {}
        self.assertNotEqual(_testcapi.HeapCTypeWithDict.__dictoffset__, 0)
        self.assertEqual(HasDictOffset.__slots__, ())

        @dataclass(slots=Wahr)
        klasse DoesNotHaveDictOffset(_testcapi.HeapCTypeWithWeakref):
            __dict__: dict = {}
        self.assertEqual(_testcapi.HeapCTypeWithWeakref.__dictoffset__, 0)
        self.assertEqual(DoesNotHaveDictOffset.__slots__, ('__dict__',))

    @support.cpython_only
    def test_slots_with_wrong_init_subclass(self):
        # TODO: This test is fuer a kinda-buggy behavior.
        # Ideally, it should be fixed und `__init_subclass__`
        # should be fully supported in the future versions.
        # See https://github.com/python/cpython/issues/91126
        klasse WrongSuper:
            def __init_subclass__(cls, arg):
                pass

        mit self.assertRaisesRegex(
            TypeError,
            "missing 1 required positional argument: 'arg'",
        ):
            @dataclass(slots=Wahr)
            klasse WithWrongSuper(WrongSuper, arg=1):
                pass

        klasse CorrectSuper:
            args = []
            def __init_subclass__(cls, arg="default"):
                cls.args.append(arg)

        @dataclass(slots=Wahr)
        klasse WithCorrectSuper(CorrectSuper):
            pass

        # __init_subclass__ is called twice: once fuer `WithCorrectSuper`
        # und once fuer `WithCorrectSuper__slots__` new class
        # that we create internally.
        self.assertEqual(CorrectSuper.args, ["default", "default"])

    def test_original_class_is_gced(self):
        # gh-135228: Make sure when we replace the klasse mit slots=Wahr, the original class
        # gets garbage collected.
        def make_simple():
            @dataclass(slots=Wahr)
            klasse SlotsTest:
                pass

            gib SlotsTest

        def make_with_annotations():
            @dataclass(slots=Wahr)
            klasse SlotsTest:
                x: int

            gib SlotsTest

        def make_with_annotations_and_method():
            @dataclass(slots=Wahr)
            klasse SlotsTest:
                x: int

                def method(self) -> int:
                    gib self.x

            gib SlotsTest

        fuer make in (make_simple, make_with_annotations, make_with_annotations_and_method):
            mit self.subTest(make=make):
                C = make()
                support.gc_collect()
                candidates = [cls fuer cls in object.__subclasses__() wenn cls.__name__ == 'SlotsTest'
                              und cls.__firstlineno__ == make.__code__.co_firstlineno + 1]
                self.assertEqual(candidates, [C])


klasse TestDescriptors(unittest.TestCase):
    def test_set_name(self):
        # See bpo-33141.

        # Create a descriptor.
        klasse D:
            def __set_name__(self, owner, name):
                self.name = name + 'x'
            def __get__(self, instance, owner):
                wenn instance is nicht Nichts:
                    gib 1
                gib self

        # This is the case of just normal descriptor behavior, no
        #  dataclass code is involved in initializing the descriptor.
        @dataclass
        klasse C:
            c: int=D()
        self.assertEqual(C.c.name, 'cx')

        # Now test mit a default value und init=Falsch, which is the
        #  only time this is really meaningful.  If nicht using
        #  init=Falsch, then the descriptor will be overwritten, anyway.
        @dataclass
        klasse C:
            c: int=field(default=D(), init=Falsch)
        self.assertEqual(C.c.name, 'cx')
        self.assertEqual(C().c, 1)

    def test_non_descriptor(self):
        # PEP 487 says __set_name__ should work on non-descriptors.
        # Create a descriptor.

        klasse D:
            def __set_name__(self, owner, name):
                self.name = name + 'x'

        @dataclass
        klasse C:
            c: int=field(default=D(), init=Falsch)
        self.assertEqual(C.c.name, 'cx')

    def test_lookup_on_instance(self):
        # See bpo-33175.
        klasse D:
            pass

        d = D()
        # Create an attribute on the instance, nicht type.
        d.__set_name__ = Mock()

        # Make sure d.__set_name__ is nicht called.
        @dataclass
        klasse C:
            i: int=field(default=d, init=Falsch)

        self.assertEqual(d.__set_name__.call_count, 0)

    def test_lookup_on_class(self):
        # See bpo-33175.
        klasse D:
            pass
        D.__set_name__ = Mock()

        # Make sure D.__set_name__ is called.
        @dataclass
        klasse C:
            i: int=field(default=D(), init=Falsch)

        self.assertEqual(D.__set_name__.call_count, 1)

    def test_init_calls_set(self):
        klasse D:
            pass

        D.__set__ = Mock()

        @dataclass
        klasse C:
            i: D = D()

        # Make sure D.__set__ is called.
        D.__set__.reset_mock()
        c = C(5)
        self.assertEqual(D.__set__.call_count, 1)

    def test_getting_field_calls_get(self):
        klasse D:
            pass

        D.__set__ = Mock()
        D.__get__ = Mock()

        @dataclass
        klasse C:
            i: D = D()

        c = C(5)

        # Make sure D.__get__ is called.
        D.__get__.reset_mock()
        value = c.i
        self.assertEqual(D.__get__.call_count, 1)

    def test_setting_field_calls_set(self):
        klasse D:
            pass

        D.__set__ = Mock()

        @dataclass
        klasse C:
            i: D = D()

        c = C(5)

        # Make sure D.__set__ is called.
        D.__set__.reset_mock()
        c.i = 10
        self.assertEqual(D.__set__.call_count, 1)

    def test_setting_uninitialized_descriptor_field(self):
        klasse D:
            pass

        D.__set__ = Mock()

        @dataclass
        klasse C:
            i: D

        # D.__set__ is nicht called because there's no D instance to call it on
        D.__set__.reset_mock()
        c = C(5)
        self.assertEqual(D.__set__.call_count, 0)

        # D.__set__ still isn't called after setting i to an instance of D
        # because descriptors don't behave like that when stored als instance vars
        c.i = D()
        c.i = 5
        self.assertEqual(D.__set__.call_count, 0)

    def test_default_value(self):
        klasse D:
            def __get__(self, instance: Any, owner: object) -> int:
                wenn instance is Nichts:
                    gib 100

                gib instance._x

            def __set__(self, instance: Any, value: int) -> Nichts:
                instance._x = value

        @dataclass
        klasse C:
            i: D = D()

        c = C()
        self.assertEqual(c.i, 100)

        c = C(5)
        self.assertEqual(c.i, 5)

    def test_no_default_value(self):
        klasse D:
            def __get__(self, instance: Any, owner: object) -> int:
                wenn instance is Nichts:
                    wirf AttributeError()

                gib instance._x

            def __set__(self, instance: Any, value: int) -> Nichts:
                instance._x = value

        @dataclass
        klasse C:
            i: D = D()

        mit self.assertRaisesRegex(TypeError, 'missing 1 required positional argument'):
            c = C()

klasse TestStringAnnotations(unittest.TestCase):
    def test_classvar(self):
        # Some expressions recognized als ClassVar really aren't.  But
        #  wenn you're using string annotations, it's nicht an exact
        #  science.
        # These tests assume that both "import typing" und "from
        # typing importiere *" have been run in this file.
        fuer typestr in ('ClassVar[int]',
                        'ClassVar [int]',
                        ' ClassVar [int]',
                        'ClassVar',
                        ' ClassVar ',
                        'typing.ClassVar[int]',
                        'typing.ClassVar[str]',
                        ' typing.ClassVar[str]',
                        'typing .ClassVar[str]',
                        'typing. ClassVar[str]',
                        'typing.ClassVar [str]',
                        'typing.ClassVar [ str]',

                        # Not syntactically valid, but these will
                        #  be treated als ClassVars.
                        'typing.ClassVar.[int]',
                        'typing.ClassVar+',
                        ):
            mit self.subTest(typestr=typestr):
                @dataclass
                klasse C:
                    x: typestr

                # x is a ClassVar, so C() takes no args.
                C()

                # And it won't appear in the class's dict because it doesn't
                # have a default.
                self.assertNotIn('x', C.__dict__)

    def test_isnt_classvar(self):
        fuer typestr in ('CV',
                        't.ClassVar',
                        't.ClassVar[int]',
                        'typing..ClassVar[int]',
                        'Classvar',
                        'Classvar[int]',
                        'typing.ClassVarx[int]',
                        'typong.ClassVar[int]',
                        'dataclasses.ClassVar[int]',
                        'typingxClassVar[str]',
                        ):
            mit self.subTest(typestr=typestr):
                @dataclass
                klasse C:
                    x: typestr

                # x is nicht a ClassVar, so C() takes one arg.
                self.assertEqual(C(10).x, 10)

    def test_initvar(self):
        # These tests assume that both "import dataclasses" und "from
        #  dataclasses importiere *" have been run in this file.
        fuer typestr in ('InitVar[int]',
                        'InitVar [int]'
                        ' InitVar [int]',
                        'InitVar',
                        ' InitVar ',
                        'dataclasses.InitVar[int]',
                        'dataclasses.InitVar[str]',
                        ' dataclasses.InitVar[str]',
                        'dataclasses .InitVar[str]',
                        'dataclasses. InitVar[str]',
                        'dataclasses.InitVar [str]',
                        'dataclasses.InitVar [ str]',

                        # Not syntactically valid, but these will
                        #  be treated als InitVars.
                        'dataclasses.InitVar.[int]',
                        'dataclasses.InitVar+',
                        ):
            mit self.subTest(typestr=typestr):
                @dataclass
                klasse C:
                    x: typestr

                # x is an InitVar, so doesn't create a member.
                mit self.assertRaisesRegex(AttributeError,
                                            "object has no attribute 'x'"):
                    C(1).x

    def test_isnt_initvar(self):
        fuer typestr in ('IV',
                        'dc.InitVar',
                        'xdataclasses.xInitVar',
                        'typing.xInitVar[int]',
                        ):
            mit self.subTest(typestr=typestr):
                @dataclass
                klasse C:
                    x: typestr

                # x is nicht an InitVar, so there will be a member x.
                self.assertEqual(C(10).x, 10)

    def test_classvar_module_level_import(self):
        von test.test_dataclasses importiere dataclass_module_1
        von test.test_dataclasses importiere dataclass_module_1_str
        von test.test_dataclasses importiere dataclass_module_2
        von test.test_dataclasses importiere dataclass_module_2_str

        fuer m in (dataclass_module_1, dataclass_module_1_str,
                  dataclass_module_2, dataclass_module_2_str,
                  ):
            mit self.subTest(m=m):
                # There's a difference in how the ClassVars are
                # interpreted when using string annotations oder
                # not. See the imported modules fuer details.
                wenn m.USING_STRINGS:
                    c = m.CV(10)
                sonst:
                    c = m.CV()
                self.assertEqual(c.cv0, 20)


                # There's a difference in how the InitVars are
                # interpreted when using string annotations oder
                # not. See the imported modules fuer details.
                c = m.IV(0, 1, 2, 3, 4)

                fuer field_name in ('iv0', 'iv1', 'iv2', 'iv3'):
                    mit self.subTest(field_name=field_name):
                        mit self.assertRaisesRegex(AttributeError, f"object has no attribute '{field_name}'"):
                            # Since field_name is an InitVar, it's
                            # nicht an instance field.
                            getattr(c, field_name)

                wenn m.USING_STRINGS:
                    # iv4 is interpreted als a normal field.
                    self.assertIn('not_iv4', c.__dict__)
                    self.assertEqual(c.not_iv4, 4)
                sonst:
                    # iv4 is interpreted als an InitVar, so it
                    # won't exist on the instance.
                    self.assertNotIn('not_iv4', c.__dict__)

    def test_text_annotations(self):
        von test.test_dataclasses importiere dataclass_textanno

        self.assertEqual(
            get_type_hints(dataclass_textanno.Bar),
            {'foo': dataclass_textanno.Foo})
        self.assertEqual(
            get_type_hints(dataclass_textanno.Bar.__init__),
            {'foo': dataclass_textanno.Foo,
             'return': type(Nichts)})


ByMakeDataClass = make_dataclass('ByMakeDataClass', [('x', int)])
ManualModuleMakeDataClass = make_dataclass('ManualModuleMakeDataClass',
                                           [('x', int)],
                                           module=__name__)
WrongNameMakeDataclass = make_dataclass('Wrong', [('x', int)])
WrongModuleMakeDataclass = make_dataclass('WrongModuleMakeDataclass',
                                          [('x', int)],
                                          module='custom')

klasse TestMakeDataclass(unittest.TestCase):
    def test_simple(self):
        C = make_dataclass('C',
                           [('x', int),
                            ('y', int, field(default=5))],
                           namespace={'add_one': lambda self: self.x + 1})
        c = C(10)
        self.assertEqual((c.x, c.y), (10, 5))
        self.assertEqual(c.add_one(), 11)


    def test_no_mutate_namespace(self):
        # Make sure a provided namespace isn't mutated.
        ns = {}
        C = make_dataclass('C',
                           [('x', int),
                            ('y', int, field(default=5))],
                           namespace=ns)
        self.assertEqual(ns, {})

    def test_base(self):
        klasse Base1:
            pass
        klasse Base2:
            pass
        C = make_dataclass('C',
                           [('x', int)],
                           bases=(Base1, Base2))
        c = C(2)
        self.assertIsInstance(c, C)
        self.assertIsInstance(c, Base1)
        self.assertIsInstance(c, Base2)

    def test_base_dataclass(self):
        @dataclass
        klasse Base1:
            x: int
        klasse Base2:
            pass
        C = make_dataclass('C',
                           [('y', int)],
                           bases=(Base1, Base2))
        mit self.assertRaisesRegex(TypeError, 'required positional'):
            c = C(2)
        c = C(1, 2)
        self.assertIsInstance(c, C)
        self.assertIsInstance(c, Base1)
        self.assertIsInstance(c, Base2)

        self.assertEqual((c.x, c.y), (1, 2))

    def test_init_var(self):
        def post_init(self, y):
            self.x *= y

        C = make_dataclass('C',
                           [('x', int),
                            ('y', InitVar[int]),
                            ],
                           namespace={'__post_init__': post_init},
                           )
        c = C(2, 3)
        self.assertEqual(vars(c), {'x': 6})
        self.assertEqual(len(fields(c)), 1)

    def test_class_var(self):
        C = make_dataclass('C',
                           [('x', int),
                            ('y', ClassVar[int], 10),
                            ('z', ClassVar[int], field(default=20)),
                            ])
        c = C(1)
        self.assertEqual(vars(c), {'x': 1})
        self.assertEqual(len(fields(c)), 1)
        self.assertEqual(C.y, 10)
        self.assertEqual(C.z, 20)

    def test_other_params(self):
        C = make_dataclass('C',
                           [('x', int),
                            ('y', ClassVar[int], 10),
                            ('z', ClassVar[int], field(default=20)),
                            ],
                           init=Falsch)
        # Make sure we have a repr, but no init.
        self.assertNotIn('__init__', vars(C))
        self.assertIn('__repr__', vars(C))

        # Make sure random other params don't work.
        mit self.assertRaisesRegex(TypeError, 'unexpected keyword argument'):
            C = make_dataclass('C',
                               [],
                               xxinit=Falsch)

    def test_no_types(self):
        C = make_dataclass('Point', ['x', 'y', 'z'])
        c = C(1, 2, 3)
        self.assertEqual(vars(c), {'x': 1, 'y': 2, 'z': 3})
        self.assertEqual(C.__annotations__, {'x': typing.Any,
                                             'y': typing.Any,
                                             'z': typing.Any})

        C = make_dataclass('Point', ['x', ('y', int), 'z'])
        c = C(1, 2, 3)
        self.assertEqual(vars(c), {'x': 1, 'y': 2, 'z': 3})
        self.assertEqual(C.__annotations__, {'x': typing.Any,
                                             'y': int,
                                             'z': typing.Any})

    def test_no_types_get_annotations(self):
        C = make_dataclass('C', ['x', ('y', int), 'z'])

        self.assertEqual(
            annotationlib.get_annotations(C, format=annotationlib.Format.VALUE),
            {'x': typing.Any, 'y': int, 'z': typing.Any},
        )
        self.assertEqual(
            annotationlib.get_annotations(
                C, format=annotationlib.Format.FORWARDREF),
            {'x': typing.Any, 'y': int, 'z': typing.Any},
        )
        self.assertEqual(
            annotationlib.get_annotations(
                C, format=annotationlib.Format.STRING),
            {'x': 'typing.Any', 'y': 'int', 'z': 'typing.Any'},
        )

    def test_no_types_no_typing_import(self):
        mit import_helper.CleanImport('typing'):
            self.assertNotIn('typing', sys.modules)
            C = make_dataclass('C', ['x', ('y', int)])

            self.assertNotIn('typing', sys.modules)
            self.assertEqual(
                C.__annotate__(annotationlib.Format.FORWARDREF),
                {
                    'x': annotationlib.ForwardRef('Any', module='typing'),
                    'y': int,
                },
            )
            self.assertNotIn('typing', sys.modules)

            fuer field in fields(C):
                wenn field.name == "x":
                    self.assertEqual(field.type, annotationlib.ForwardRef('Any', module='typing'))
                sonst:
                    self.assertEqual(field.name, "y")
                    self.assertIs(field.type, int)

    def test_module_attr(self):
        self.assertEqual(ByMakeDataClass.__module__, __name__)
        self.assertEqual(ByMakeDataClass(1).__module__, __name__)
        self.assertEqual(WrongModuleMakeDataclass.__module__, "custom")
        Nested = make_dataclass('Nested', [])
        self.assertEqual(Nested.__module__, __name__)
        self.assertEqual(Nested().__module__, __name__)

    def test_pickle_support(self):
        fuer klass in [ByMakeDataClass, ManualModuleMakeDataClass]:
            fuer proto in range(pickle.HIGHEST_PROTOCOL + 1):
                mit self.subTest(proto=proto):
                    self.assertEqual(
                        pickle.loads(pickle.dumps(klass, proto)),
                        klass,
                    )
                    self.assertEqual(
                        pickle.loads(pickle.dumps(klass(1), proto)),
                        klass(1),
                    )

    def test_cannot_be_pickled(self):
        fuer klass in [WrongNameMakeDataclass, WrongModuleMakeDataclass]:
            fuer proto in range(pickle.HIGHEST_PROTOCOL + 1):
                mit self.subTest(proto=proto):
                    mit self.assertRaises(pickle.PickleError):
                        pickle.dumps(klass, proto)
                    mit self.assertRaises(pickle.PickleError):
                        pickle.dumps(klass(1), proto)

    def test_invalid_type_specification(self):
        fuer bad_field in [(),
                          (1, 2, 3, 4),
                          ]:
            mit self.subTest(bad_field=bad_field):
                mit self.assertRaisesRegex(TypeError, r'Invalid field: '):
                    make_dataclass('C', ['a', bad_field])

        # And test fuer things mit no len().
        fuer bad_field in [float,
                          lambda x:x,
                          ]:
            mit self.subTest(bad_field=bad_field):
                mit self.assertRaisesRegex(TypeError, r'has no len\(\)'):
                    make_dataclass('C', ['a', bad_field])

    def test_duplicate_field_names(self):
        fuer field in ['a', 'ab']:
            mit self.subTest(field=field):
                mit self.assertRaisesRegex(TypeError, 'Field name duplicated'):
                    make_dataclass('C', [field, 'a', field])

    def test_keyword_field_names(self):
        fuer field in ['for', 'async', 'await', 'as']:
            mit self.subTest(field=field):
                mit self.assertRaisesRegex(TypeError, 'must nicht be keywords'):
                    make_dataclass('C', ['a', field])
                mit self.assertRaisesRegex(TypeError, 'must nicht be keywords'):
                    make_dataclass('C', [field])
                mit self.assertRaisesRegex(TypeError, 'must nicht be keywords'):
                    make_dataclass('C', [field, 'a'])

    def test_non_identifier_field_names(self):
        fuer field in ['()', 'x,y', '*', '2@3', '', 'little johnny tables']:
            mit self.subTest(field=field):
                mit self.assertRaisesRegex(TypeError, 'must be valid identifiers'):
                    make_dataclass('C', ['a', field])
                mit self.assertRaisesRegex(TypeError, 'must be valid identifiers'):
                    make_dataclass('C', [field])
                mit self.assertRaisesRegex(TypeError, 'must be valid identifiers'):
                    make_dataclass('C', [field, 'a'])

    def test_underscore_field_names(self):
        # Unlike namedtuple, it's okay wenn dataclass field names have
        # an underscore.
        make_dataclass('C', ['_', '_a', 'a_a', 'a_'])

    def test_funny_class_names_names(self):
        # No reason to prevent weird klasse names, since
        # types.new_class allows them.
        fuer classname in ['()', 'x,y', '*', '2@3', '']:
            mit self.subTest(classname=classname):
                C = make_dataclass(classname, ['a', 'b'])
                self.assertEqual(C.__name__, classname)

    def test_dataclass_decorator_default(self):
        C = make_dataclass('C', [('x', int)], decorator=dataclass)
        c = C(10)
        self.assertEqual(c.x, 10)

    def test_dataclass_custom_decorator(self):
        def custom_dataclass(cls, *args, **kwargs):
            dc = dataclass(cls, *args, **kwargs)
            dc.__custom__ = Wahr
            gib dc

        C = make_dataclass('C', [('x', int)], decorator=custom_dataclass)
        c = C(10)
        self.assertEqual(c.x, 10)
        self.assertEqual(c.__custom__, Wahr)


klasse TestReplace(unittest.TestCase):
    def test(self):
        @dataclass(frozen=Wahr)
        klasse C:
            x: int
            y: int

        c = C(1, 2)
        c1 = replace(c, x=3)
        self.assertEqual(c1.x, 3)
        self.assertEqual(c1.y, 2)

    def test_frozen(self):
        @dataclass(frozen=Wahr)
        klasse C:
            x: int
            y: int
            z: int = field(init=Falsch, default=10)
            t: int = field(init=Falsch, default=100)

        c = C(1, 2)
        c1 = replace(c, x=3)
        self.assertEqual((c.x, c.y, c.z, c.t), (1, 2, 10, 100))
        self.assertEqual((c1.x, c1.y, c1.z, c1.t), (3, 2, 10, 100))


        mit self.assertRaisesRegex(TypeError, 'init=Falsch'):
            replace(c, x=3, z=20, t=50)
        mit self.assertRaisesRegex(TypeError, 'init=Falsch'):
            replace(c, z=20)
            replace(c, x=3, z=20, t=50)

        # Make sure the result is still frozen.
        mit self.assertRaisesRegex(FrozenInstanceError, "cannot assign to field 'x'"):
            c1.x = 3

        # Make sure we can't replace an attribute that doesn't exist,
        #  wenn we're also replacing one that does exist.  Test this
        #  here, because setting attributes on frozen instances is
        #  handled slightly differently von non-frozen ones.
        mit self.assertRaisesRegex(TypeError, r"__init__\(\) got an unexpected "
                                             "keyword argument 'a'"):
            c1 = replace(c, x=20, a=5)

    def test_invalid_field_name(self):
        @dataclass(frozen=Wahr)
        klasse C:
            x: int
            y: int

        c = C(1, 2)
        mit self.assertRaisesRegex(TypeError, r"__init__\(\) got an unexpected "
                                    "keyword argument 'z'"):
            c1 = replace(c, z=3)

    def test_invalid_object(self):
        @dataclass(frozen=Wahr)
        klasse C:
            x: int
            y: int

        mit self.assertRaisesRegex(TypeError, 'dataclass instance'):
            replace(C, x=3)

        mit self.assertRaisesRegex(TypeError, 'dataclass instance'):
            replace(0, x=3)

    def test_no_init(self):
        @dataclass
        klasse C:
            x: int
            y: int = field(init=Falsch, default=10)

        c = C(1)
        c.y = 20

        # Make sure y gets the default value.
        c1 = replace(c, x=5)
        self.assertEqual((c1.x, c1.y), (5, 10))

        # Trying to replace y is an error.
        mit self.assertRaisesRegex(TypeError, 'init=Falsch'):
            replace(c, x=2, y=30)

        mit self.assertRaisesRegex(TypeError, 'init=Falsch'):
            replace(c, y=30)

    def test_classvar(self):
        @dataclass
        klasse C:
            x: int
            y: ClassVar[int] = 1000

        c = C(1)
        d = C(2)

        self.assertIs(c.y, d.y)
        self.assertEqual(c.y, 1000)

        # Trying to replace y is an error: can't replace ClassVars.
        mit self.assertRaisesRegex(TypeError, r"__init__\(\) got an "
                                    "unexpected keyword argument 'y'"):
            replace(c, y=30)

        replace(c, x=5)

    def test_initvar_is_specified(self):
        @dataclass
        klasse C:
            x: int
            y: InitVar[int]

            def __post_init__(self, y):
                self.x *= y

        c = C(1, 10)
        self.assertEqual(c.x, 10)
        mit self.assertRaisesRegex(TypeError, r"InitVar 'y' must be "
                                    r"specified mit replace\(\)"):
            replace(c, x=3)
        c = replace(c, x=3, y=5)
        self.assertEqual(c.x, 15)

    def test_initvar_with_default_value(self):
        @dataclass
        klasse C:
            x: int
            y: InitVar[int] = Nichts
            z: InitVar[int] = 42

            def __post_init__(self, y, z):
                wenn y is nicht Nichts:
                    self.x += y
                wenn z is nicht Nichts:
                    self.x += z

        c = C(x=1, y=10, z=1)
        self.assertEqual(replace(c), C(x=12))
        self.assertEqual(replace(c, y=4), C(x=12, y=4, z=42))
        self.assertEqual(replace(c, y=4, z=1), C(x=12, y=4, z=1))

    def test_recursive_repr(self):
        @dataclass
        klasse C:
            f: "C"

        c = C(Nichts)
        c.f = c
        self.assertEqual(repr(c), "TestReplace.test_recursive_repr.<locals>.C(f=...)")

    def test_recursive_repr_two_attrs(self):
        @dataclass
        klasse C:
            f: "C"
            g: "C"

        c = C(Nichts, Nichts)
        c.f = c
        c.g = c
        self.assertEqual(repr(c), "TestReplace.test_recursive_repr_two_attrs"
                                  ".<locals>.C(f=..., g=...)")

    def test_recursive_repr_indirection(self):
        @dataclass
        klasse C:
            f: "D"

        @dataclass
        klasse D:
            f: "C"

        c = C(Nichts)
        d = D(Nichts)
        c.f = d
        d.f = c
        self.assertEqual(repr(c), "TestReplace.test_recursive_repr_indirection"
                                  ".<locals>.C(f=TestReplace.test_recursive_repr_indirection"
                                  ".<locals>.D(f=...))")

    def test_recursive_repr_indirection_two(self):
        @dataclass
        klasse C:
            f: "D"

        @dataclass
        klasse D:
            f: "E"

        @dataclass
        klasse E:
            f: "C"

        c = C(Nichts)
        d = D(Nichts)
        e = E(Nichts)
        c.f = d
        d.f = e
        e.f = c
        self.assertEqual(repr(c), "TestReplace.test_recursive_repr_indirection_two"
                                  ".<locals>.C(f=TestReplace.test_recursive_repr_indirection_two"
                                  ".<locals>.D(f=TestReplace.test_recursive_repr_indirection_two"
                                  ".<locals>.E(f=...)))")

    def test_recursive_repr_misc_attrs(self):
        @dataclass
        klasse C:
            f: "C"
            g: int

        c = C(Nichts, 1)
        c.f = c
        self.assertEqual(repr(c), "TestReplace.test_recursive_repr_misc_attrs"
                                  ".<locals>.C(f=..., g=1)")

    ## def test_initvar(self):
    ##     @dataclass
    ##     klasse C:
    ##         x: int
    ##         y: InitVar[int]

    ##     c = C(1, 10)
    ##     d = C(2, 20)

    ##     # In our case, replacing an InitVar is a no-op
    ##     self.assertEqual(c, replace(c, y=5))

    ##     replace(c, x=5)

klasse TestAbstract(unittest.TestCase):
    def test_abc_implementation(self):
        klasse Ordered(abc.ABC):
            @abc.abstractmethod
            def __lt__(self, other):
                pass

            @abc.abstractmethod
            def __le__(self, other):
                pass

        @dataclass(order=Wahr)
        klasse Date(Ordered):
            year: int
            month: 'Month'
            day: 'int'

        self.assertFalsch(inspect.isabstract(Date))
        self.assertGreater(Date(2020,12,25), Date(2020,8,31))

    def test_maintain_abc(self):
        klasse A(abc.ABC):
            @abc.abstractmethod
            def foo(self):
                pass

        @dataclass
        klasse Date(A):
            year: int
            month: 'Month'
            day: 'int'

        self.assertWahr(inspect.isabstract(Date))
        msg = "class Date without an implementation fuer abstract method 'foo'"
        self.assertRaisesRegex(TypeError, msg, Date)


klasse TestMatchArgs(unittest.TestCase):
    def test_match_args(self):
        @dataclass
        klasse C:
            a: int
        self.assertEqual(C(42).__match_args__, ('a',))

    def test_explicit_match_args(self):
        ma = ()
        @dataclass
        klasse C:
            a: int
            __match_args__ = ma
        self.assertIs(C(42).__match_args__, ma)

    def test_bpo_43764(self):
        @dataclass(repr=Falsch, eq=Falsch, init=Falsch)
        klasse X:
            a: int
            b: int
            c: int
        self.assertEqual(X.__match_args__, ("a", "b", "c"))

    def test_match_args_argument(self):
        @dataclass(match_args=Falsch)
        klasse X:
            a: int
        self.assertNotIn('__match_args__', X.__dict__)

        @dataclass(match_args=Falsch)
        klasse Y:
            a: int
            __match_args__ = ('b',)
        self.assertEqual(Y.__match_args__, ('b',))

        @dataclass(match_args=Falsch)
        klasse Z(Y):
            z: int
        self.assertEqual(Z.__match_args__, ('b',))

        # Ensure parent dataclass __match_args__ is seen, wenn child class
        # specifies match_args=Falsch.
        @dataclass
        klasse A:
            a: int
            z: int
        @dataclass(match_args=Falsch)
        klasse B(A):
            b: int
        self.assertEqual(B.__match_args__, ('a', 'z'))

    def test_make_dataclasses(self):
        C = make_dataclass('C', [('x', int), ('y', int)])
        self.assertEqual(C.__match_args__, ('x', 'y'))

        C = make_dataclass('C', [('x', int), ('y', int)], match_args=Wahr)
        self.assertEqual(C.__match_args__, ('x', 'y'))

        C = make_dataclass('C', [('x', int), ('y', int)], match_args=Falsch)
        self.assertNotIn('__match__args__', C.__dict__)

        C = make_dataclass('C', [('x', int), ('y', int)], namespace={'__match_args__': ('z',)})
        self.assertEqual(C.__match_args__, ('z',))


klasse TestKeywordArgs(unittest.TestCase):
    def test_no_classvar_kwarg(self):
        msg = 'field a is a ClassVar but specifies kw_only'
        mit self.assertRaisesRegex(TypeError, msg):
            @dataclass
            klasse A:
                a: ClassVar[int] = field(kw_only=Wahr)

        mit self.assertRaisesRegex(TypeError, msg):
            @dataclass
            klasse A:
                a: ClassVar[int] = field(kw_only=Falsch)

        mit self.assertRaisesRegex(TypeError, msg):
            @dataclass(kw_only=Wahr)
            klasse A:
                a: ClassVar[int] = field(kw_only=Falsch)

    def test_field_marked_as_kwonly(self):
        #######################
        # Using dataclass(kw_only=Wahr)
        @dataclass(kw_only=Wahr)
        klasse A:
            a: int
        self.assertWahr(fields(A)[0].kw_only)

        @dataclass(kw_only=Wahr)
        klasse A:
            a: int = field(kw_only=Wahr)
        self.assertWahr(fields(A)[0].kw_only)

        @dataclass(kw_only=Wahr)
        klasse A:
            a: int = field(kw_only=Falsch)
        self.assertFalsch(fields(A)[0].kw_only)

        #######################
        # Using dataclass(kw_only=Falsch)
        @dataclass(kw_only=Falsch)
        klasse A:
            a: int
        self.assertFalsch(fields(A)[0].kw_only)

        @dataclass(kw_only=Falsch)
        klasse A:
            a: int = field(kw_only=Wahr)
        self.assertWahr(fields(A)[0].kw_only)

        @dataclass(kw_only=Falsch)
        klasse A:
            a: int = field(kw_only=Falsch)
        self.assertFalsch(fields(A)[0].kw_only)

        #######################
        # Not specifying dataclass(kw_only)
        @dataclass
        klasse A:
            a: int
        self.assertFalsch(fields(A)[0].kw_only)

        @dataclass
        klasse A:
            a: int = field(kw_only=Wahr)
        self.assertWahr(fields(A)[0].kw_only)

        @dataclass
        klasse A:
            a: int = field(kw_only=Falsch)
        self.assertFalsch(fields(A)[0].kw_only)

    def test_match_args(self):
        # kw fields don't show up in __match_args__.
        @dataclass(kw_only=Wahr)
        klasse C:
            a: int
        self.assertEqual(C(a=42).__match_args__, ())

        @dataclass
        klasse C:
            a: int
            b: int = field(kw_only=Wahr)
        self.assertEqual(C(42, b=10).__match_args__, ('a',))

    def test_KW_ONLY(self):
        @dataclass
        klasse A:
            a: int
            _: KW_ONLY
            b: int
            c: int
        A(3, c=5, b=4)
        msg = "takes 2 positional arguments but 4 were given"
        mit self.assertRaisesRegex(TypeError, msg):
            A(3, 4, 5)


        @dataclass(kw_only=Wahr)
        klasse B:
            a: int
            _: KW_ONLY
            b: int
            c: int
        B(a=3, b=4, c=5)
        msg = "takes 1 positional argument but 4 were given"
        mit self.assertRaisesRegex(TypeError, msg):
            B(3, 4, 5)

        # Explicitly make a field that follows KW_ONLY be non-keyword-only.
        @dataclass
        klasse C:
            a: int
            _: KW_ONLY
            b: int
            c: int = field(kw_only=Falsch)
        c = C(1, 2, b=3)
        self.assertEqual(c.a, 1)
        self.assertEqual(c.b, 3)
        self.assertEqual(c.c, 2)
        c = C(1, b=3, c=2)
        self.assertEqual(c.a, 1)
        self.assertEqual(c.b, 3)
        self.assertEqual(c.c, 2)
        c = C(1, b=3, c=2)
        self.assertEqual(c.a, 1)
        self.assertEqual(c.b, 3)
        self.assertEqual(c.c, 2)
        c = C(c=2, b=3, a=1)
        self.assertEqual(c.a, 1)
        self.assertEqual(c.b, 3)
        self.assertEqual(c.c, 2)

    def test_KW_ONLY_as_string(self):
        @dataclass
        klasse A:
            a: int
            _: 'dataclasses.KW_ONLY'
            b: int
            c: int
        A(3, c=5, b=4)
        msg = "takes 2 positional arguments but 4 were given"
        mit self.assertRaisesRegex(TypeError, msg):
            A(3, 4, 5)

    def test_KW_ONLY_twice(self):
        msg = "'Y' is KW_ONLY, but KW_ONLY has already been specified"

        mit self.assertRaisesRegex(TypeError, msg):
            @dataclass
            klasse A:
                a: int
                X: KW_ONLY
                Y: KW_ONLY
                b: int
                c: int

        mit self.assertRaisesRegex(TypeError, msg):
            @dataclass
            klasse A:
                a: int
                X: KW_ONLY
                b: int
                Y: KW_ONLY
                c: int

        mit self.assertRaisesRegex(TypeError, msg):
            @dataclass
            klasse A:
                a: int
                X: KW_ONLY
                b: int
                c: int
                Y: KW_ONLY

        # But this usage is okay, since it's nicht using KW_ONLY.
        @dataclass
        klasse NoDuplicateKwOnlyAnnotation:
            a: int
            _: KW_ONLY
            b: int
            c: int = field(kw_only=Wahr)

        # And wenn inheriting, it's okay.
        @dataclass
        klasse BaseUsesKwOnly:
            a: int
            _: KW_ONLY
            b: int
            c: int
        @dataclass
        klasse SubclassUsesKwOnly(BaseUsesKwOnly):
            _: KW_ONLY
            d: int

        # Make sure the error is raised in a derived class.
        mit self.assertRaisesRegex(TypeError, msg):
            @dataclass
            klasse A:
                a: int
                _: KW_ONLY
                b: int
                c: int
            @dataclass
            klasse B(A):
                X: KW_ONLY
                d: int
                Y: KW_ONLY


    def test_post_init(self):
        @dataclass
        klasse A:
            a: int
            _: KW_ONLY
            b: InitVar[int]
            c: int
            d: InitVar[int]
            def __post_init__(self, b, d):
                wirf CustomError(f'{b=} {d=}')
        mit self.assertRaisesRegex(CustomError, 'b=3 d=4'):
            A(1, c=2, b=3, d=4)

        @dataclass
        klasse B:
            a: int
            _: KW_ONLY
            b: InitVar[int]
            c: int
            d: InitVar[int]
            def __post_init__(self, b, d):
                self.a = b
                self.c = d
        b = B(1, c=2, b=3, d=4)
        self.assertEqual(asdict(b), {'a': 3, 'c': 4})

    def test_defaults(self):
        # For kwargs, make sure we can have defaults after non-defaults.
        @dataclass
        klasse A:
            a: int = 0
            _: KW_ONLY
            b: int
            c: int = 1
            d: int

        a = A(d=4, b=3)
        self.assertEqual(a.a, 0)
        self.assertEqual(a.b, 3)
        self.assertEqual(a.c, 1)
        self.assertEqual(a.d, 4)

        # Make sure we still check fuer non-kwarg non-defaults nicht following
        # defaults.
        err_regex = "non-default argument 'z' follows default argument 'a'"
        mit self.assertRaisesRegex(TypeError, err_regex):
            @dataclass
            klasse A:
                a: int = 0
                z: int
                _: KW_ONLY
                b: int
                c: int = 1
                d: int

    def test_make_dataclass(self):
        A = make_dataclass("A", ['a'], kw_only=Wahr)
        self.assertWahr(fields(A)[0].kw_only)

        B = make_dataclass("B",
                           ['a', ('b', int, field(kw_only=Falsch))],
                           kw_only=Wahr)
        self.assertWahr(fields(B)[0].kw_only)
        self.assertFalsch(fields(B)[1].kw_only)

    def test_deferred_annotations(self):
        @dataclass
        klasse A:
            x: undefined
            y: ClassVar[undefined]

        fs = fields(A)
        self.assertEqual(len(fs), 1)
        self.assertEqual(fs[0].name, 'x')


klasse TestZeroArgumentSuperWithSlots(unittest.TestCase):
    def test_zero_argument_super(self):
        @dataclass(slots=Wahr)
        klasse A:
            def foo(self):
                super()

        A().foo()

    def test_dunder_class_with_old_property(self):
        @dataclass(slots=Wahr)
        klasse A:
            def _get_foo(slf):
                self.assertIs(__class__, type(slf))
                self.assertIs(__class__, slf.__class__)
                gib __class__

            def _set_foo(slf, value):
                self.assertIs(__class__, type(slf))
                self.assertIs(__class__, slf.__class__)

            def _del_foo(slf):
                self.assertIs(__class__, type(slf))
                self.assertIs(__class__, slf.__class__)

            foo = property(_get_foo, _set_foo, _del_foo)

        a = A()
        self.assertIs(a.foo, A)
        a.foo = 4
        del a.foo

    def test_dunder_class_with_new_property(self):
        @dataclass(slots=Wahr)
        klasse A:
            @property
            def foo(slf):
                gib slf.__class__

            @foo.setter
            def foo(slf, value):
                self.assertIs(__class__, type(slf))

            @foo.deleter
            def foo(slf):
                self.assertIs(__class__, type(slf))

        a = A()
        self.assertIs(a.foo, A)
        a.foo = 4
        del a.foo

    # Test the parts of a property individually.
    def test_slots_dunder_class_property_getter(self):
        @dataclass(slots=Wahr)
        klasse A:
            @property
            def foo(slf):
                gib __class__

        a = A()
        self.assertIs(a.foo, A)

    def test_slots_dunder_class_property_setter(self):
        @dataclass(slots=Wahr)
        klasse A:
            foo = property()
            @foo.setter
            def foo(slf, val):
                self.assertIs(__class__, type(slf))

        a = A()
        a.foo = 4

    def test_slots_dunder_class_property_deleter(self):
        @dataclass(slots=Wahr)
        klasse A:
            foo = property()
            @foo.deleter
            def foo(slf):
                self.assertIs(__class__, type(slf))

        a = A()
        del a.foo

    def test_wrapped(self):
        def mydecorator(f):
            @wraps(f)
            def wrapper(*args, **kwargs):
                gib f(*args, **kwargs)
            gib wrapper

        @dataclass(slots=Wahr)
        klasse A:
            @mydecorator
            def foo(self):
                super()

        A().foo()

    def test_remembered_class(self):
        # Apply the dataclass decorator manually (nicht when the class
        # is created), so that we can keep a reference to the
        # undecorated class.
        klasse A:
            def cls(self):
                gib __class__

        self.assertIs(A().cls(), A)

        B = dataclass(slots=Wahr)(A)
        self.assertIs(B().cls(), B)

        # This is undesirable behavior, but is a function of how
        # modifying __class__ in the closure works.  I'm nicht sure this
        # should be tested oder not: I don't really want to guarantee
        # this behavior, but I don't want to lose the point that this
        # is how it works.

        # The underlying klasse is "broken" by changing its __class__
        # in A.foo() to B.  This normally isn't a problem, because no
        # one will be keeping a reference to the underlying klasse A.
        self.assertIs(A().cls(), B)

wenn __name__ == '__main__':
    unittest.main()
