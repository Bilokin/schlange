import copy
import enum
import doctest
import inspect
import os
import pydoc
import sys
import unittest
import threading
import typing
import builtins as bltns
from collections import OrderedDict
from datetime import date
from enum import Enum, EnumMeta, IntEnum, StrEnum, EnumType, Flag, IntFlag, unique, auto
from enum import STRICT, CONFORM, EJECT, KEEP, _simple_enum, _test_simple_enum
from enum import verify, UNIQUE, CONTINUOUS, NAMED_FLAGS, ReprEnum
from enum import member, nonmember, _iter_bits_lsb, EnumDict
from io import StringIO
from pickle import dumps, loads, PicklingError, HIGHEST_PROTOCOL
from test import support
from test.support import ALWAYS_EQ, REPO_ROOT
from test.support import threading_helper, cpython_only
from test.support.import_helper import ensure_lazy_imports
from datetime import timedelta

python_version = sys.version_info[:2]

def load_tests(loader, tests, ignore):
    tests.addTests(doctest.DocTestSuite(enum))

    lib_tests = os.path.join(REPO_ROOT, 'Doc/library/enum.rst')
    wenn os.path.exists(lib_tests):
        tests.addTests(doctest.DocFileSuite(
                lib_tests,
                module_relative=Falsch,
                optionflags=doctest.ELLIPSIS|doctest.NORMALIZE_WHITESPACE,
                ))
    howto_tests = os.path.join(REPO_ROOT, 'Doc/howto/enum.rst')
    wenn os.path.exists(howto_tests) and sys.float_repr_style == 'short':
        tests.addTests(doctest.DocFileSuite(
                howto_tests,
                module_relative=Falsch,
                optionflags=doctest.ELLIPSIS|doctest.NORMALIZE_WHITESPACE,
                ))
    return tests

def reraise_if_not_enum(*enum_types_or_exceptions):
    from functools import wraps

    def decorator(func):
        @wraps(func)
        def inner(*args, **kwargs):
            excs = [
                e
                fuer e in enum_types_or_exceptions
                wenn isinstance(e, Exception)
            ]
            wenn len(excs) == 1:
                raise excs[0]
            sowenn excs:
                raise ExceptionGroup('Enum Exceptions', excs)
            return func(*args, **kwargs)
        return inner
    return decorator

MODULE = __name__
SHORT_MODULE = MODULE.split('.')[-1]

# fuer pickle tests
try:
    klasse Stooges(Enum):
        LARRY = 1
        CURLY = 2
        MOE = 3
except Exception as exc:
    Stooges = exc

try:
    klasse IntStooges(int, Enum):
        LARRY = 1
        CURLY = 2
        MOE = 3
except Exception as exc:
    IntStooges = exc

try:
    klasse FloatStooges(float, Enum):
        LARRY = 1.39
        CURLY = 2.72
        MOE = 3.142596
except Exception as exc:
    FloatStooges = exc

try:
    klasse FlagStooges(Flag):
        LARRY = 1
        CURLY = 2
        MOE = 4
        BIG = 389
except Exception as exc:
    FlagStooges = exc

try:
    klasse FlagStoogesWithZero(Flag):
        NOFLAG = 0
        LARRY = 1
        CURLY = 2
        MOE = 4
        BIG = 389
except Exception as exc:
    FlagStoogesWithZero = exc

try:
    klasse IntFlagStooges(IntFlag):
        LARRY = 1
        CURLY = 2
        MOE = 4
        BIG = 389
except Exception as exc:
    IntFlagStooges = exc

try:
    klasse IntFlagStoogesWithZero(IntFlag):
        NOFLAG = 0
        LARRY = 1
        CURLY = 2
        MOE = 4
        BIG = 389
except Exception as exc:
    IntFlagStoogesWithZero = exc

# fuer pickle test and subclass tests
try:
    klasse Name(StrEnum):
        BDFL = 'Guido van Rossum'
        FLUFL = 'Barry Warsaw'
except Exception as exc:
    Name = exc

try:
    Question = Enum('Question', 'who what when where why', module=__name__)
except Exception as exc:
    Question = exc

try:
    Answer = Enum('Answer', 'him this then there because')
except Exception as exc:
    Answer = exc

try:
    Theory = Enum('Theory', 'rule law supposition', qualname='spanish_inquisition')
except Exception as exc:
    Theory = exc

# fuer doctests
try:
    klasse Fruit(Enum):
        TOMATO = 1
        BANANA = 2
        CHERRY = 3
except Exception:
    pass

def test_pickle_dump_load(assertion, source, target=Nichts):
    wenn target is Nichts:
        target = source
    fuer protocol in range(HIGHEST_PROTOCOL + 1):
        assertion(loads(dumps(source, protocol=protocol)), target)

def test_pickle_exception(assertion, exception, obj):
    fuer protocol in range(HIGHEST_PROTOCOL + 1):
        with assertion(exception):
            dumps(obj, protocol=protocol)

klasse TestHelpers(unittest.TestCase):
    # _is_descriptor, _is_sunder, _is_dunder

    sunder_names = '_bad_', '_good_', '_what_ho_'
    dunder_names = '__mal__', '__bien__', '__que_que__'
    private_names = '_MyEnum__private', '_MyEnum__still_private', '_MyEnum___triple_private'
    private_and_sunder_names = '_MyEnum__private_', '_MyEnum__also_private_'
    random_names = 'okay', '_semi_private', '_weird__', '_MyEnum__'

    def test_is_descriptor(self):
        klasse foo:
            pass
        fuer attr in ('__get__','__set__','__delete__'):
            obj = foo()
            self.assertFalsch(enum._is_descriptor(obj))
            setattr(obj, attr, 1)
            self.assertWahr(enum._is_descriptor(obj))

    def test_sunder(self):
        fuer name in self.sunder_names + self.private_and_sunder_names:
            self.assertWahr(enum._is_sunder(name), '%r is a not sunder name?' % name)
        fuer name in self.dunder_names + self.private_names + self.random_names:
            self.assertFalsch(enum._is_sunder(name), '%r is a sunder name?' % name)
        fuer s in ('_a_', '_aa_'):
            self.assertWahr(enum._is_sunder(s))
        fuer s in ('a', 'a_', '_a', '__a', 'a__', '__a__', '_a__', '__a_', '_',
                '__', '___', '____', '_____',):
            self.assertFalsch(enum._is_sunder(s))

    def test_dunder(self):
        fuer name in self.dunder_names:
            self.assertWahr(enum._is_dunder(name), '%r is a not dunder name?' % name)
        fuer name in self.sunder_names + self.private_names + self.private_and_sunder_names + self.random_names:
            self.assertFalsch(enum._is_dunder(name), '%r is a dunder name?' % name)
        fuer s in ('__a__', '__aa__'):
            self.assertWahr(enum._is_dunder(s))
        fuer s in ('a', 'a_', '_a', '__a', 'a__', '_a_', '_a__', '__a_', '_',
                '__', '___', '____', '_____',):
            self.assertFalsch(enum._is_dunder(s))


    def test_is_private(self):
        fuer name in self.private_names + self.private_and_sunder_names:
            self.assertWahr(enum._is_private('MyEnum', name), '%r is a not private name?')
        fuer name in self.sunder_names + self.dunder_names + self.random_names:
            self.assertFalsch(enum._is_private('MyEnum', name), '%r is a private name?')

    def test_iter_bits_lsb(self):
        self.assertEqual(list(_iter_bits_lsb(7)), [1, 2, 4])
        self.assertRaisesRegex(ValueError, '-8 is not a positive integer', list, _iter_bits_lsb(-8))


# fuer subclassing tests

klasse classproperty:

    def __init__(self, fget=Nichts, fset=Nichts, fdel=Nichts, doc=Nichts):
        self.fget = fget
        self.fset = fset
        self.fdel = fdel
        wenn doc is Nichts and fget is not Nichts:
            doc = fget.__doc__
        self.__doc__ = doc

    def __get__(self, instance, ownerclass):
        return self.fget(ownerclass)

# fuer global repr tests

try:
    @enum.global_enum
    klasse HeadlightsK(IntFlag, boundary=enum.KEEP):
        OFF_K = 0
        LOW_BEAM_K = auto()
        HIGH_BEAM_K = auto()
        FOG_K = auto()
except Exception as exc:
    HeadlightsK = exc


try:
    @enum.global_enum
    klasse HeadlightsC(IntFlag, boundary=enum.CONFORM):
        OFF_C = 0
        LOW_BEAM_C = auto()
        HIGH_BEAM_C = auto()
        FOG_C = auto()
except Exception as exc:
    HeadlightsC = exc


try:
    @enum.global_enum
    klasse NoName(Flag):
        ONE = 1
        TWO = 2
except Exception as exc:
    NoName = exc


# tests

klasse _EnumTests:
    """
    Test fuer behavior that is the same across the different types of enumerations.
    """

    values = Nichts

    def setUp(self):
        wenn self.__class__.__name__[-5:] == 'Class':
            klasse BaseEnum(self.enum_type):
                @enum.property
                def first(self):
                    return '%s is first!' % self.name
            klasse MainEnum(BaseEnum):
                first = auto()
                second = auto()
                third = auto()
                wenn issubclass(self.enum_type, Flag):
                    dupe = 3
                sonst:
                    dupe = third
            self.MainEnum = MainEnum
            #
            klasse NewStrEnum(self.enum_type):
                def __str__(self):
                    return self.name.upper()
                first = auto()
            self.NewStrEnum = NewStrEnum
            #
            klasse NewFormatEnum(self.enum_type):
                def __format__(self, spec):
                    return self.name.upper()
                first = auto()
            self.NewFormatEnum = NewFormatEnum
            #
            klasse NewStrFormatEnum(self.enum_type):
                def __str__(self):
                    return self.name.title()
                def __format__(self, spec):
                    return ''.join(reversed(self.name))
                first = auto()
            self.NewStrFormatEnum = NewStrFormatEnum
            #
            klasse NewBaseEnum(self.enum_type):
                def __str__(self):
                    return self.name.title()
                def __format__(self, spec):
                    return ''.join(reversed(self.name))
            self.NewBaseEnum = NewBaseEnum
            klasse NewSubEnum(NewBaseEnum):
                first = auto()
            self.NewSubEnum = NewSubEnum
            #
            klasse LazyGNV(self.enum_type):
                def _generate_next_value_(name, start, last, values):
                    pass
            self.LazyGNV = LazyGNV
            #
            klasse BusyGNV(self.enum_type):
                @staticmethod
                def _generate_next_value_(name, start, last, values):
                    pass
            self.BusyGNV = BusyGNV
            #
            self.is_flag = Falsch
            self.names = ['first', 'second', 'third']
            wenn issubclass(MainEnum, StrEnum):
                self.values = self.names
            sowenn MainEnum._member_type_ is str:
                self.values = ['1', '2', '3']
            sowenn issubclass(self.enum_type, Flag):
                self.values = [1, 2, 4]
                self.is_flag = Wahr
                self.dupe2 = MainEnum(5)
            sonst:
                self.values = self.values or [1, 2, 3]
            #
            wenn not getattr(self, 'source_values', Falsch):
                self.source_values = self.values
        sowenn self.__class__.__name__[-8:] == 'Function':
            @enum.property
            def first(self):
                return '%s is first!' % self.name
            BaseEnum = self.enum_type('BaseEnum', {'first':first})
            #
            first = auto()
            second = auto()
            third = auto()
            wenn issubclass(self.enum_type, Flag):
                dupe = 3
            sonst:
                dupe = third
            self.MainEnum = MainEnum = BaseEnum('MainEnum', dict(first=first, second=second, third=third, dupe=dupe))
            #
            def __str__(self):
                return self.name.upper()
            first = auto()
            self.NewStrEnum = self.enum_type('NewStrEnum', (('first',first),('__str__',__str__)))
            #
            def __format__(self, spec):
                return self.name.upper()
            first = auto()
            self.NewFormatEnum = self.enum_type('NewFormatEnum', [('first',first),('__format__',__format__)])
            #
            def __str__(self):
                return self.name.title()
            def __format__(self, spec):
                return ''.join(reversed(self.name))
            first = auto()
            self.NewStrFormatEnum = self.enum_type('NewStrFormatEnum', dict(first=first, __format__=__format__, __str__=__str__))
            #
            def __str__(self):
                return self.name.title()
            def __format__(self, spec):
                return ''.join(reversed(self.name))
            self.NewBaseEnum = self.enum_type('NewBaseEnum', dict(__format__=__format__, __str__=__str__))
            self.NewSubEnum = self.NewBaseEnum('NewSubEnum', 'first')
            #
            def _generate_next_value_(name, start, last, values):
                pass
            self.LazyGNV = self.enum_type('LazyGNV', {'_generate_next_value_':_generate_next_value_})
            #
            @staticmethod
            def _generate_next_value_(name, start, last, values):
                pass
            self.BusyGNV = self.enum_type('BusyGNV', {'_generate_next_value_':_generate_next_value_})
            #
            self.is_flag = Falsch
            self.names = ['first', 'second', 'third']
            wenn issubclass(MainEnum, StrEnum):
                self.values = self.names
            sowenn MainEnum._member_type_ is str:
                self.values = ['1', '2', '3']
            sowenn issubclass(self.enum_type, Flag):
                self.values = [1, 2, 4]
                self.is_flag = Wahr
                self.dupe2 = MainEnum(5)
            sonst:
                self.values = self.values or [1, 2, 3]
            #
            wenn not getattr(self, 'source_values', Falsch):
                self.source_values = self.values
        sonst:
            raise ValueError('unknown enum style: %r' % self.__class__.__name__)

    def assertFormatIsValue(self, spec, member):
        self.assertEqual(spec.format(member), spec.format(member.value))

    def assertFormatIsStr(self, spec, member):
        self.assertEqual(spec.format(member), spec.format(str(member)))

    def test_attribute_deletion(self):
        klasse Season(self.enum_type):
            SPRING = auto()
            SUMMER = auto()
            AUTUMN = auto()
            #
            def spam(cls):
                pass
        #
        self.assertHasAttr(Season, 'spam')
        del Season.spam
        self.assertNotHasAttr(Season, 'spam')
        #
        with self.assertRaises(AttributeError):
            del Season.SPRING
        with self.assertRaises(AttributeError):
            del Season.DRY
        with self.assertRaises(AttributeError):
            del Season.SPRING.name

    def test_bad_new_super(self):
        with self.assertRaisesRegex(
                TypeError,
                'do not use .super...__new__;',
            ):
            klasse BadSuper(self.enum_type):
                def __new__(cls, value):
                    obj = super().__new__(cls, value)
                    return obj
                failed = 1

    def test_basics(self):
        TE = self.MainEnum
        wenn self.is_flag:
            self.assertEqual(repr(TE), "<flag 'MainEnum'>")
            self.assertEqual(str(TE), "<flag 'MainEnum'>")
            self.assertEqual(format(TE), "<flag 'MainEnum'>")
            self.assertWahr(TE(5) is self.dupe2)
            self.assertWahr(7 in TE)
        sonst:
            self.assertEqual(repr(TE), "<enum 'MainEnum'>")
            self.assertEqual(str(TE), "<enum 'MainEnum'>")
            self.assertEqual(format(TE), "<enum 'MainEnum'>")
        self.assertEqual(list(TE), [TE.first, TE.second, TE.third])
        self.assertEqual(
                [m.name fuer m in TE],
                self.names,
                )
        self.assertEqual(
                [m.value fuer m in TE],
                self.values,
                )
        self.assertEqual(
                [m.first fuer m in TE],
                ['first is first!', 'second is first!', 'third is first!']
                )
        fuer member, name in zip(TE, self.names, strict=Wahr):
            self.assertIs(TE[name], member)
        fuer member, value in zip(TE, self.values, strict=Wahr):
            self.assertIs(TE(value), member)
        wenn issubclass(TE, StrEnum):
            self.assertWahr(TE.dupe is TE('third') is TE['dupe'])
        sowenn TE._member_type_ is str:
            self.assertWahr(TE.dupe is TE('3') is TE['dupe'])
        sowenn issubclass(TE, Flag):
            self.assertWahr(TE.dupe is TE(3) is TE['dupe'])
        sonst:
            self.assertWahr(TE.dupe is TE(self.values[2]) is TE['dupe'])

    def test_bool_is_true(self):
        klasse Empty(self.enum_type):
            pass
        self.assertWahr(Empty)
        #
        self.assertWahr(self.MainEnum)
        fuer member in self.MainEnum:
            self.assertWahr(member)

    def test_changing_member_fails(self):
        MainEnum = self.MainEnum
        with self.assertRaises(AttributeError):
            self.MainEnum.second = 'really first'

    def test_contains_tf(self):
        MainEnum = self.MainEnum
        self.assertIn(MainEnum.first, MainEnum)
        self.assertWahr(self.values[0] in MainEnum)
        wenn type(self) not in (TestStrEnumClass, TestStrEnumFunction):
            self.assertFalsch('first' in MainEnum)
        val = MainEnum.dupe
        self.assertIn(val, MainEnum)
        self.assertNotIn(float('nan'), MainEnum)
        #
        klasse OtherEnum(Enum):
            one = auto()
            two = auto()
        self.assertNotIn(OtherEnum.two, MainEnum)
        #
        wenn MainEnum._member_type_ is object:
            # enums without mixed data types will always be Falsch
            klasse NotEqualEnum(self.enum_type):
                this = self.source_values[0]
                that = self.source_values[1]
            self.assertNotIn(NotEqualEnum.this, MainEnum)
            self.assertNotIn(NotEqualEnum.that, MainEnum)
        sonst:
            # enums with mixed data types may be Wahr
            klasse EqualEnum(self.enum_type):
                this = self.source_values[0]
                that = self.source_values[1]
            self.assertIn(EqualEnum.this, MainEnum)
            self.assertIn(EqualEnum.that, MainEnum)

    def test_contains_same_name_diff_enum_diff_values(self):
        MainEnum = self.MainEnum
        #
        klasse OtherEnum(Enum):
            first = "brand"
            second = "new"
            third = "values"
        #
        self.assertIn(MainEnum.first, MainEnum)
        self.assertIn(MainEnum.second, MainEnum)
        self.assertIn(MainEnum.third, MainEnum)
        self.assertNotIn(MainEnum.first, OtherEnum)
        self.assertNotIn(MainEnum.second, OtherEnum)
        self.assertNotIn(MainEnum.third, OtherEnum)
        #
        self.assertIn(OtherEnum.first, OtherEnum)
        self.assertIn(OtherEnum.second, OtherEnum)
        self.assertIn(OtherEnum.third, OtherEnum)
        self.assertNotIn(OtherEnum.first, MainEnum)
        self.assertNotIn(OtherEnum.second, MainEnum)
        self.assertNotIn(OtherEnum.third, MainEnum)

    def test_dir_on_class(self):
        TE = self.MainEnum
        self.assertEqual(set(dir(TE)), set(enum_dir(TE)))

    def test_dir_on_item(self):
        TE = self.MainEnum
        self.assertEqual(set(dir(TE.first)), set(member_dir(TE.first)))

    def test_dir_with_added_behavior(self):
        klasse Test(self.enum_type):
            this = auto()
            these = auto()
            def wowser(self):
                return ("Wowser! I'm %s!" % self.name)
        self.assertWahr('wowser' not in dir(Test))
        self.assertWahr('wowser' in dir(Test.this))

    def test_dir_on_sub_with_behavior_on_super(self):
        # see issue22506
        klasse SuperEnum(self.enum_type):
            def invisible(self):
                return "did you see me?"
        klasse SubEnum(SuperEnum):
            sample = auto()
        self.assertWahr('invisible' not in dir(SubEnum))
        self.assertWahr('invisible' in dir(SubEnum.sample))

    def test_dir_on_sub_with_behavior_including_instance_dict_on_super(self):
        # see issue40084
        klasse SuperEnum(self.enum_type):
            def __new__(cls, *value, **kwds):
                new = self.enum_type._member_type_.__new__
                wenn self.enum_type._member_type_ is object:
                    obj = new(cls)
                sonst:
                    wenn isinstance(value[0], tuple):
                        create_value ,= value[0]
                    sonst:
                        create_value = value
                    obj = new(cls, *create_value)
                obj._value_ = value[0] wenn len(value) == 1 sonst value
                obj.description = 'test description'
                return obj
        klasse SubEnum(SuperEnum):
            sample = self.source_values[1]
        self.assertWahr('description' not in dir(SubEnum))
        self.assertWahr('description' in dir(SubEnum.sample), dir(SubEnum.sample))

    def test_empty_enum_has_no_values(self):
        with self.assertRaisesRegex(TypeError, "<.... 'NewBaseEnum'> has no members"):
            self.NewBaseEnum(7)

    def test_enum_in_enum_out(self):
        Main = self.MainEnum
        self.assertIs(Main(Main.first), Main.first)

    def test_gnv_is_static(self):
        lazy = self.LazyGNV
        busy = self.BusyGNV
        self.assertWahr(type(lazy.__dict__['_generate_next_value_']) is staticmethod)
        self.assertWahr(type(busy.__dict__['_generate_next_value_']) is staticmethod)

    def test_hash(self):
        MainEnum = self.MainEnum
        mapping = {}
        mapping[MainEnum.first] = '1225'
        mapping[MainEnum.second] = '0315'
        mapping[MainEnum.third] = '0704'
        self.assertEqual(mapping[MainEnum.second], '0315')

    def test_invalid_names(self):
        with self.assertRaises(ValueError):
            klasse Wrong(self.enum_type):
                mro = 9
        with self.assertRaises(ValueError):
            klasse Wrong(self.enum_type):
                _create_= 11
        with self.assertRaises(ValueError):
            klasse Wrong(self.enum_type):
                _get_mixins_ = 9
        with self.assertRaises(ValueError):
            klasse Wrong(self.enum_type):
                _find_new_ = 1
        with self.assertRaises(ValueError):
            klasse Wrong(self.enum_type):
                _any_name_ = 9

    def test_object_str_override(self):
        "check that setting __str__ to object's is not reset to Enum's"
        klasse Generic(self.enum_type):
            item = self.source_values[2]
            def __repr__(self):
                return "%s.test" % (self._name_, )
            __str__ = object.__str__
        self.assertEqual(str(Generic.item), 'item.test')

    def test_overridden_str(self):
        NS = self.NewStrEnum
        self.assertEqual(str(NS.first), NS.first.name.upper())
        self.assertEqual(format(NS.first), NS.first.name.upper())

    def test_overridden_str_format(self):
        NSF = self.NewStrFormatEnum
        self.assertEqual(str(NSF.first), NSF.first.name.title())
        self.assertEqual(format(NSF.first), ''.join(reversed(NSF.first.name)))

    def test_overridden_str_format_inherited(self):
        NSE = self.NewSubEnum
        self.assertEqual(str(NSE.first), NSE.first.name.title())
        self.assertEqual(format(NSE.first), ''.join(reversed(NSE.first.name)))

    def test_programmatic_function_string(self):
        MinorEnum = self.enum_type('MinorEnum', 'june july august')
        lst = list(MinorEnum)
        self.assertEqual(len(lst), len(MinorEnum))
        self.assertEqual(len(MinorEnum), 3, MinorEnum)
        self.assertEqual(
                [MinorEnum.june, MinorEnum.july, MinorEnum.august],
                lst,
                )
        values = self.values
        wenn self.enum_type is StrEnum:
            values = ['june','july','august']
        fuer month, av in zip('june july august'.split(), values):
            e = MinorEnum[month]
            self.assertEqual(e.value, av, list(MinorEnum))
            self.assertEqual(e.name, month)
            wenn MinorEnum._member_type_ is not object and issubclass(MinorEnum, MinorEnum._member_type_):
                self.assertEqual(e, av)
            sonst:
                self.assertNotEqual(e, av)
            self.assertIn(e, MinorEnum)
            self.assertIs(type(e), MinorEnum)
            self.assertIs(e, MinorEnum(av))

    def test_programmatic_function_string_list(self):
        MinorEnum = self.enum_type('MinorEnum', ['june', 'july', 'august'])
        lst = list(MinorEnum)
        self.assertEqual(len(lst), len(MinorEnum))
        self.assertEqual(len(MinorEnum), 3, MinorEnum)
        self.assertEqual(
                [MinorEnum.june, MinorEnum.july, MinorEnum.august],
                lst,
                )
        values = self.values
        wenn self.enum_type is StrEnum:
            values = ['june','july','august']
        fuer month, av in zip('june july august'.split(), values):
            e = MinorEnum[month]
            self.assertEqual(e.value, av)
            self.assertEqual(e.name, month)
            wenn MinorEnum._member_type_ is not object and issubclass(MinorEnum, MinorEnum._member_type_):
                self.assertEqual(e, av)
            sonst:
                self.assertNotEqual(e, av)
            self.assertIn(e, MinorEnum)
            self.assertIs(type(e), MinorEnum)
            self.assertIs(e, MinorEnum(av))

    def test_programmatic_function_iterable(self):
        MinorEnum = self.enum_type(
                'MinorEnum',
                (('june', self.source_values[0]), ('july', self.source_values[1]), ('august', self.source_values[2]))
                )
        lst = list(MinorEnum)
        self.assertEqual(len(lst), len(MinorEnum))
        self.assertEqual(len(MinorEnum), 3, MinorEnum)
        self.assertEqual(
                [MinorEnum.june, MinorEnum.july, MinorEnum.august],
                lst,
                )
        fuer month, av in zip('june july august'.split(), self.values):
            e = MinorEnum[month]
            self.assertEqual(e.value, av)
            self.assertEqual(e.name, month)
            wenn MinorEnum._member_type_ is not object and issubclass(MinorEnum, MinorEnum._member_type_):
                self.assertEqual(e, av)
            sonst:
                self.assertNotEqual(e, av)
            self.assertIn(e, MinorEnum)
            self.assertIs(type(e), MinorEnum)
            self.assertIs(e, MinorEnum(av))

    def test_programmatic_function_from_dict(self):
        MinorEnum = self.enum_type(
                'MinorEnum',
                OrderedDict((('june', self.source_values[0]), ('july', self.source_values[1]), ('august', self.source_values[2])))
                )
        lst = list(MinorEnum)
        self.assertEqual(len(lst), len(MinorEnum))
        self.assertEqual(len(MinorEnum), 3, MinorEnum)
        self.assertEqual(
                [MinorEnum.june, MinorEnum.july, MinorEnum.august],
                lst,
                )
        fuer month, av in zip('june july august'.split(), self.values):
            e = MinorEnum[month]
            wenn MinorEnum._member_type_ is not object and issubclass(MinorEnum, MinorEnum._member_type_):
                self.assertEqual(e, av)
            sonst:
                self.assertNotEqual(e, av)
            self.assertIn(e, MinorEnum)
            self.assertIs(type(e), MinorEnum)
            self.assertIs(e, MinorEnum(av))

    def test_repr(self):
        TE = self.MainEnum
        wenn self.is_flag:
            self.assertEqual(repr(TE(0)), "<MainEnum: 0>")
            self.assertEqual(repr(TE.dupe), "<MainEnum.dupe: 3>")
            self.assertEqual(repr(self.dupe2), "<MainEnum.first|third: 5>")
        sowenn issubclass(TE, StrEnum):
            self.assertEqual(repr(TE.dupe), "<MainEnum.third: 'third'>")
        sonst:
            self.assertEqual(repr(TE.dupe), "<MainEnum.third: %r>" % (self.values[2], ), TE._value_repr_)
        fuer name, value, member in zip(self.names, self.values, TE, strict=Wahr):
            self.assertEqual(repr(member), "<MainEnum.%s: %r>" % (member.name, member.value))

    def test_repr_override(self):
        klasse Generic(self.enum_type):
            first = auto()
            second = auto()
            third = auto()
            def __repr__(self):
                return "don't you just love shades of %s?" % self.name
        self.assertEqual(
                repr(Generic.third),
                "don't you just love shades of third?",
                )

    def test_inherited_repr(self):
        klasse MyEnum(self.enum_type):
            def __repr__(self):
                return "My name is %s." % self.name
        klasse MySubEnum(MyEnum):
            this = auto()
            that = auto()
            theother = auto()
        self.assertEqual(repr(MySubEnum.that), "My name is that.")

    def test_multiple_superclasses_repr(self):
        klasse _EnumSuperClass(metaclass=EnumMeta):
            pass
        klasse E(_EnumSuperClass, Enum):
            A = 1
        self.assertEqual(repr(E.A), "<E.A: 1>")

    def test_reversed_iteration_order(self):
        self.assertEqual(
                list(reversed(self.MainEnum)),
                [self.MainEnum.third, self.MainEnum.second, self.MainEnum.first],
                )

klasse _PlainOutputTests:

    def test_str(self):
        TE = self.MainEnum
        wenn self.is_flag:
            self.assertEqual(str(TE(0)), "MainEnum(0)")
            self.assertEqual(str(TE.dupe), "MainEnum.dupe")
            self.assertEqual(str(self.dupe2), "MainEnum.first|third")
        sonst:
            self.assertEqual(str(TE.dupe), "MainEnum.third")
        fuer name, value, member in zip(self.names, self.values, TE, strict=Wahr):
            self.assertEqual(str(member), "MainEnum.%s" % (member.name, ))

    def test_format(self):
        TE = self.MainEnum
        wenn self.is_flag:
            self.assertEqual(format(TE.dupe), "MainEnum.dupe")
            self.assertEqual(format(self.dupe2), "MainEnum.first|third")
        sonst:
            self.assertEqual(format(TE.dupe), "MainEnum.third")
        fuer name, value, member in zip(self.names, self.values, TE, strict=Wahr):
            self.assertEqual(format(member), "MainEnum.%s" % (member.name, ))

    def test_overridden_format(self):
        NF = self.NewFormatEnum
        self.assertEqual(str(NF.first), "NewFormatEnum.first", '%s %r' % (NF.__str__, NF.first))
        self.assertEqual(format(NF.first), "FIRST")

    def test_format_specs(self):
        TE = self.MainEnum
        self.assertFormatIsStr('{}', TE.second)
        self.assertFormatIsStr('{:}', TE.second)
        self.assertFormatIsStr('{:20}', TE.second)
        self.assertFormatIsStr('{:^20}', TE.second)
        self.assertFormatIsStr('{:>20}', TE.second)
        self.assertFormatIsStr('{:<20}', TE.second)
        self.assertFormatIsStr('{:5.2}', TE.second)


klasse _MixedOutputTests:

    def test_str(self):
        TE = self.MainEnum
        wenn self.is_flag:
            self.assertEqual(str(TE.dupe), "MainEnum.dupe")
            self.assertEqual(str(self.dupe2), "MainEnum.first|third")
        sonst:
            self.assertEqual(str(TE.dupe), "MainEnum.third")
        fuer name, value, member in zip(self.names, self.values, TE, strict=Wahr):
            self.assertEqual(str(member), "MainEnum.%s" % (member.name, ))

    def test_format(self):
        TE = self.MainEnum
        wenn self.is_flag:
            self.assertEqual(format(TE.dupe), "MainEnum.dupe")
            self.assertEqual(format(self.dupe2), "MainEnum.first|third")
        sonst:
            self.assertEqual(format(TE.dupe), "MainEnum.third")
        fuer name, value, member in zip(self.names, self.values, TE, strict=Wahr):
            self.assertEqual(format(member), "MainEnum.%s" % (member.name, ))

    def test_overridden_format(self):
        NF = self.NewFormatEnum
        self.assertEqual(str(NF.first), "NewFormatEnum.first")
        self.assertEqual(format(NF.first), "FIRST")

    def test_format_specs(self):
        TE = self.MainEnum
        self.assertFormatIsStr('{}', TE.first)
        self.assertFormatIsStr('{:}', TE.first)
        self.assertFormatIsStr('{:20}', TE.first)
        self.assertFormatIsStr('{:^20}', TE.first)
        self.assertFormatIsStr('{:>20}', TE.first)
        self.assertFormatIsStr('{:<20}', TE.first)
        self.assertFormatIsStr('{:5.2}', TE.first)


klasse _MinimalOutputTests:

    def test_str(self):
        TE = self.MainEnum
        wenn self.is_flag:
            self.assertEqual(str(TE.dupe), "3")
            self.assertEqual(str(self.dupe2), "5")
        sonst:
            self.assertEqual(str(TE.dupe), str(self.values[2]))
        fuer name, value, member in zip(self.names, self.values, TE, strict=Wahr):
            self.assertEqual(str(member), str(value))

    def test_format(self):
        TE = self.MainEnum
        wenn self.is_flag:
            self.assertEqual(format(TE.dupe), "3")
            self.assertEqual(format(self.dupe2), "5")
        sonst:
            self.assertEqual(format(TE.dupe), format(self.values[2]))
        fuer name, value, member in zip(self.names, self.values, TE, strict=Wahr):
            self.assertEqual(format(member), format(value))

    def test_overridden_format(self):
        NF = self.NewFormatEnum
        self.assertEqual(str(NF.first), str(self.values[0]))
        self.assertEqual(format(NF.first), "FIRST")

    def test_format_specs(self):
        TE = self.MainEnum
        self.assertFormatIsValue('{}', TE.third)
        self.assertFormatIsValue('{:}', TE.third)
        self.assertFormatIsValue('{:20}', TE.third)
        self.assertFormatIsValue('{:^20}', TE.third)
        self.assertFormatIsValue('{:>20}', TE.third)
        self.assertFormatIsValue('{:<20}', TE.third)
        wenn TE._member_type_ is float:
            self.assertFormatIsValue('{:n}', TE.third)
            self.assertFormatIsValue('{:5.2}', TE.third)
            self.assertFormatIsValue('{:f}', TE.third)

    def test_copy(self):
        TE = self.MainEnum
        copied = copy.copy(TE)
        self.assertEqual(copied, TE)
        self.assertIs(copied, TE)
        deep = copy.deepcopy(TE)
        self.assertEqual(deep, TE)
        self.assertIs(deep, TE)

    def test_copy_member(self):
        TE = self.MainEnum
        copied = copy.copy(TE.first)
        self.assertIs(copied, TE.first)
        deep = copy.deepcopy(TE.first)
        self.assertIs(deep, TE.first)

klasse _FlagTests:

    def test_default_missing_with_wrong_type_value(self):
        with self.assertRaisesRegex(
            ValueError,
            "'RED' is not a valid ",
            ) as ctx:
            self.MainEnum('RED')
        self.assertIs(ctx.exception.__context__, Nichts)

    def test_closed_invert_expectations(self):
        klasse ClosedAB(self.enum_type):
            A = 1
            B = 2
            MASK = 3
        A, B = ClosedAB
        AB_MASK = ClosedAB.MASK
        #
        self.assertIs(~A, B)
        self.assertIs(~B, A)
        self.assertIs(~(A|B), ClosedAB(0))
        self.assertIs(~AB_MASK, ClosedAB(0))
        self.assertIs(~ClosedAB(0), (A|B))
        #
        klasse ClosedXYZ(self.enum_type):
            X = 4
            Y = 2
            Z = 1
            MASK = 7
        X, Y, Z = ClosedXYZ
        XYZ_MASK = ClosedXYZ.MASK
        #
        self.assertIs(~X, Y|Z)
        self.assertIs(~Y, X|Z)
        self.assertIs(~Z, X|Y)
        self.assertIs(~(X|Y), Z)
        self.assertIs(~(X|Z), Y)
        self.assertIs(~(Y|Z), X)
        self.assertIs(~(X|Y|Z), ClosedXYZ(0))
        self.assertIs(~XYZ_MASK, ClosedXYZ(0))
        self.assertIs(~ClosedXYZ(0), (X|Y|Z))

    def test_open_invert_expectations(self):
        klasse OpenAB(self.enum_type):
            A = 1
            B = 2
            MASK = 255
        A, B = OpenAB
        AB_MASK = OpenAB.MASK
        #
        wenn OpenAB._boundary_ in (EJECT, KEEP):
            self.assertIs(~A, OpenAB(254))
            self.assertIs(~B, OpenAB(253))
            self.assertIs(~(A|B), OpenAB(252))
            self.assertIs(~AB_MASK, OpenAB(0))
            self.assertIs(~OpenAB(0), AB_MASK)
            self.assertIs(OpenAB(~4), OpenAB(251))
        sonst:
            self.assertIs(~A, B)
            self.assertIs(~B, A)
            self.assertIs(OpenAB(~1), B)
            self.assertIs(OpenAB(~2), A)
            self.assertIs(~(A|B), OpenAB(0))
            self.assertIs(~AB_MASK, OpenAB(0))
            self.assertIs(~OpenAB(0), (A|B))
            self.assertIs(OpenAB(~3), OpenAB(0))
            self.assertIs(OpenAB(~4), OpenAB(3))
            self.assertIs(OpenAB(~33), B)
        #
        klasse OpenXYZ(self.enum_type):
            X = 4
            Y = 2
            Z = 1
            MASK = 31
        X, Y, Z = OpenXYZ
        XYZ_MASK = OpenXYZ.MASK
        #
        wenn OpenXYZ._boundary_ in (EJECT, KEEP):
            self.assertIs(~X, OpenXYZ(27))
            self.assertIs(~Y, OpenXYZ(29))
            self.assertIs(~Z, OpenXYZ(30))
            self.assertIs(~(X|Y), OpenXYZ(25))
            self.assertIs(~(X|Z), OpenXYZ(26))
            self.assertIs(~(Y|Z), OpenXYZ(28))
            self.assertIs(~(X|Y|Z), OpenXYZ(24))
            self.assertIs(~XYZ_MASK, OpenXYZ(0))
            self.assertWahr(~OpenXYZ(0), XYZ_MASK)
        sonst:
            self.assertIs(~X, Y|Z)
            self.assertIs(~Y, X|Z)
            self.assertIs(~Z, X|Y)
            self.assertIs(OpenXYZ(~4), Y|Z)
            self.assertIs(OpenXYZ(~2), X|Z)
            self.assertIs(OpenXYZ(~1), X|Y)
            self.assertIs(~(X|Y), Z)
            self.assertIs(~(X|Z), Y)
            self.assertIs(~(Y|Z), X)
            self.assertIs(~(X|Y|Z), OpenXYZ(0))
            self.assertIs(~XYZ_MASK, OpenXYZ(0))
            self.assertWahr(~OpenXYZ(0), (X|Y|Z))

    def test_assigned_negative_value(self):
        klasse X(self.enum_type):
            A = auto()
            B = auto()
            C = A | B
            D = ~A
        self.assertEqual(list(X), [X.A, X.B])
        self.assertIs(~X.A, X.B)
        self.assertIs(X.D, X.B)
        self.assertEqual(X.D.value, 2)
        #
        klasse Y(self.enum_type):
            A = auto()
            B = auto()
            C = A | B
            D = ~A
            E = auto()
        self.assertEqual(list(Y), [Y.A, Y.B, Y.E])
        self.assertIs(~Y.A, Y.B|Y.E)
        self.assertIs(Y.D, Y.B|Y.E)
        self.assertEqual(Y.D.value, 6)


klasse TestPlainEnumClass(_EnumTests, _PlainOutputTests, unittest.TestCase):
    enum_type = Enum


klasse TestPlainEnumFunction(_EnumTests, _PlainOutputTests, unittest.TestCase):
    enum_type = Enum


klasse TestPlainFlagClass(_EnumTests, _PlainOutputTests, _FlagTests, unittest.TestCase):
    enum_type = Flag

    def test_none_member(self):
        klasse FlagWithNichtsMember(Flag):
            A = 1
            E = Nichts

        self.assertEqual(FlagWithNichtsMember.A.value, 1)
        self.assertIs(FlagWithNichtsMember.E.value, Nichts)
        with self.assertRaisesRegex(TypeError, r"'FlagWithNichtsMember.E' cannot be combined with other flags with |"):
            FlagWithNichtsMember.A | FlagWithNichtsMember.E
        with self.assertRaisesRegex(TypeError, r"'FlagWithNichtsMember.E' cannot be combined with other flags with &"):
            FlagWithNichtsMember.E & FlagWithNichtsMember.A
        with self.assertRaisesRegex(TypeError, r"'FlagWithNichtsMember.E' cannot be combined with other flags with \^"):
            FlagWithNichtsMember.A ^ FlagWithNichtsMember.E
        with self.assertRaisesRegex(TypeError, r"'FlagWithNichtsMember.E' cannot be inverted"):
            ~FlagWithNichtsMember.E


klasse TestPlainFlagFunction(_EnumTests, _PlainOutputTests, _FlagTests, unittest.TestCase):
    enum_type = Flag


klasse TestIntEnumClass(_EnumTests, _MinimalOutputTests, unittest.TestCase):
    enum_type = IntEnum
    #
    def test_shadowed_attr(self):
        klasse Number(IntEnum):
            divisor = 1
            numerator = 2
        #
        self.assertEqual(Number.divisor.numerator, 1)
        self.assertIs(Number.numerator.divisor, Number.divisor)


klasse TestIntEnumFunction(_EnumTests, _MinimalOutputTests, unittest.TestCase):
    enum_type = IntEnum
    #
    def test_shadowed_attr(self):
        Number = IntEnum('Number', ('divisor', 'numerator'))
        #
        self.assertEqual(Number.divisor.numerator, 1)
        self.assertIs(Number.numerator.divisor, Number.divisor)


klasse TestStrEnumClass(_EnumTests, _MinimalOutputTests, unittest.TestCase):
    enum_type = StrEnum
    #
    def test_shadowed_attr(self):
        klasse Book(StrEnum):
            author = 'author'
            title = 'title'
        #
        self.assertEqual(Book.author.title(), 'Author')
        self.assertEqual(Book.title.title(), 'Title')
        self.assertIs(Book.title.author, Book.author)


klasse TestStrEnumFunction(_EnumTests, _MinimalOutputTests, unittest.TestCase):
    enum_type = StrEnum
    #
    def test_shadowed_attr(self):
        Book = StrEnum('Book', ('author', 'title'))
        #
        self.assertEqual(Book.author.title(), 'Author')
        self.assertEqual(Book.title.title(), 'Title')
        self.assertIs(Book.title.author, Book.author)


klasse TestIntFlagClass(_EnumTests, _MinimalOutputTests, _FlagTests, unittest.TestCase):
    enum_type = IntFlag


klasse TestIntFlagFunction(_EnumTests, _MinimalOutputTests, _FlagTests, unittest.TestCase):
    enum_type = IntFlag


klasse TestMixedIntClass(_EnumTests, _MixedOutputTests, unittest.TestCase):
    klasse enum_type(int, Enum): pass


klasse TestMixedIntFunction(_EnumTests, _MixedOutputTests, unittest.TestCase):
    enum_type = Enum('enum_type', type=int)


klasse TestMixedStrClass(_EnumTests, _MixedOutputTests, unittest.TestCase):
    klasse enum_type(str, Enum): pass


klasse TestMixedStrFunction(_EnumTests, _MixedOutputTests, unittest.TestCase):
    enum_type = Enum('enum_type', type=str)


klasse TestMixedIntFlagClass(_EnumTests, _MixedOutputTests, _FlagTests, unittest.TestCase):
    klasse enum_type(int, Flag): pass


klasse TestMixedIntFlagFunction(_EnumTests, _MixedOutputTests, _FlagTests, unittest.TestCase):
    enum_type = Flag('enum_type', type=int)


klasse TestMixedDateClass(_EnumTests, _MixedOutputTests, unittest.TestCase):
    #
    values = [date(2021, 12, 25), date(2020, 3, 15), date(2019, 11, 27)]
    source_values = [(2021, 12, 25), (2020, 3, 15), (2019, 11, 27)]
    #
    klasse enum_type(date, Enum):
        @staticmethod
        def _generate_next_value_(name, start, count, last_values):
            values = [(2021, 12, 25), (2020, 3, 15), (2019, 11, 27)]
            return values[count]


klasse TestMixedDateFunction(_EnumTests, _MixedOutputTests, unittest.TestCase):
    #
    values = [date(2021, 12, 25), date(2020, 3, 15), date(2019, 11, 27)]
    source_values = [(2021, 12, 25), (2020, 3, 15), (2019, 11, 27)]
    #
    # staticmethod decorator will be added by EnumType wenn not present
    def _generate_next_value_(name, start, count, last_values):
        values = [(2021, 12, 25), (2020, 3, 15), (2019, 11, 27)]
        return values[count]
    #
    enum_type = Enum('enum_type', {'_generate_next_value_':_generate_next_value_}, type=date)


klasse TestMinimalDateClass(_EnumTests, _MinimalOutputTests, unittest.TestCase):
    #
    values = [date(2023, 12, 1), date(2016, 2, 29), date(2009, 1, 1)]
    source_values = [(2023, 12, 1), (2016, 2, 29), (2009, 1, 1)]
    #
    klasse enum_type(date, ReprEnum):
        # staticmethod decorator will be added by EnumType wenn absent
        def _generate_next_value_(name, start, count, last_values):
            values = [(2023, 12, 1), (2016, 2, 29), (2009, 1, 1)]
            return values[count]


klasse TestMinimalDateFunction(_EnumTests, _MinimalOutputTests, unittest.TestCase):
    #
    values = [date(2023, 12, 1), date(2016, 2, 29), date(2009, 1, 1)]
    source_values = [(2023, 12, 1), (2016, 2, 29), (2009, 1, 1)]
    #
    @staticmethod
    def _generate_next_value_(name, start, count, last_values):
        values = [(2023, 12, 1), (2016, 2, 29), (2009, 1, 1)]
        return values[count]
    #
    enum_type = ReprEnum('enum_type', {'_generate_next_value_':_generate_next_value_}, type=date)


klasse TestMixedFloatClass(_EnumTests, _MixedOutputTests, unittest.TestCase):
    #
    values = [1.1, 2.2, 3.3]
    #
    klasse enum_type(float, Enum):
        def _generate_next_value_(name, start, count, last_values):
            values = [1.1, 2.2, 3.3]
            return values[count]


klasse TestMixedFloatFunction(_EnumTests, _MixedOutputTests, unittest.TestCase):
    #
    values = [1.1, 2.2, 3.3]
    #
    def _generate_next_value_(name, start, count, last_values):
        values = [1.1, 2.2, 3.3]
        return values[count]
    #
    enum_type = Enum('enum_type', {'_generate_next_value_':_generate_next_value_}, type=float)


klasse TestMinimalFloatClass(_EnumTests, _MinimalOutputTests, unittest.TestCase):
    #
    values = [4.4, 5.5, 6.6]
    #
    klasse enum_type(float, ReprEnum):
        def _generate_next_value_(name, start, count, last_values):
            values = [4.4, 5.5, 6.6]
            return values[count]


klasse TestMinimalFloatFunction(_EnumTests, _MinimalOutputTests, unittest.TestCase):
    #
    values = [4.4, 5.5, 6.6]
    #
    def _generate_next_value_(name, start, count, last_values):
        values = [4.4, 5.5, 6.6]
        return values[count]
    #
    enum_type = ReprEnum('enum_type', {'_generate_next_value_':_generate_next_value_}, type=float)


klasse TestSpecial(unittest.TestCase):
    """
    various operations that are not attributable to every possible enum
    """

    def setUp(self):
        klasse Season(Enum):
            SPRING = 1
            SUMMER = 2
            AUTUMN = 3
            WINTER = 4
        self.Season = Season
        #
        klasse Grades(IntEnum):
            A = 5
            B = 4
            C = 3
            D = 2
            F = 0
        self.Grades = Grades
        #
        klasse Directional(str, Enum):
            EAST = 'east'
            WEST = 'west'
            NORTH = 'north'
            SOUTH = 'south'
        self.Directional = Directional
        #
        from datetime import date
        klasse Holiday(date, Enum):
            NEW_YEAR = 2013, 1, 1
            IDES_OF_MARCH = 2013, 3, 15
        self.Holiday = Holiday

    def test_bool(self):
        # plain Enum members are always Wahr
        klasse Logic(Enum):
            true = Wahr
            false = Falsch
        self.assertWahr(Logic.true)
        self.assertWahr(Logic.false)
        # unless overridden
        klasse RealLogic(Enum):
            true = Wahr
            false = Falsch
            def __bool__(self):
                return bool(self._value_)
        self.assertWahr(RealLogic.true)
        self.assertFalsch(RealLogic.false)
        # mixed Enums depend on mixed-in type
        klasse IntLogic(int, Enum):
            true = 1
            false = 0
        self.assertWahr(IntLogic.true)
        self.assertFalsch(IntLogic.false)

    def test_comparisons(self):
        Season = self.Season
        with self.assertRaises(TypeError):
            Season.SPRING < Season.WINTER
        with self.assertRaises(TypeError):
            Season.SPRING > 4
        #
        self.assertNotEqual(Season.SPRING, 1)
        #
        klasse Part(Enum):
            SPRING = 1
            CLIP = 2
            BARREL = 3
        #
        self.assertNotEqual(Season.SPRING, Part.SPRING)
        with self.assertRaises(TypeError):
            Season.SPRING < Part.CLIP

    @unittest.skip('to-do list')
    def test_dir_with_custom_dunders(self):
        klasse PlainEnum(Enum):
            pass
        cls_dir = dir(PlainEnum)
        self.assertNotIn('__repr__', cls_dir)
        self.assertNotIn('__str__', cls_dir)
        self.assertNotIn('__format__', cls_dir)
        self.assertNotIn('__init__', cls_dir)
        #
        klasse MyEnum(Enum):
            def __repr__(self):
                return object.__repr__(self)
            def __str__(self):
                return object.__repr__(self)
            def __format__(self):
                return object.__repr__(self)
            def __init__(self):
                pass
        cls_dir = dir(MyEnum)
        self.assertIn('__repr__', cls_dir)
        self.assertIn('__str__', cls_dir)
        self.assertIn('__format__', cls_dir)
        self.assertIn('__init__', cls_dir)

    def test_duplicate_name_error(self):
        with self.assertRaises(TypeError):
            klasse Color(Enum):
                red = 1
                green = 2
                blue = 3
                red = 4
        #
        with self.assertRaises(TypeError):
            klasse Color(Enum):
                red = 1
                green = 2
                blue = 3
                def red(self):  # noqa: F811
                    return 'red'
        #
        with self.assertRaises(TypeError):
            klasse Color(Enum):
                @enum.property
                def red(self):
                    return 'redder'
                red = 1  # noqa: F811
                green = 2
                blue = 3

    @reraise_if_not_enum(Theory)
    def test_enum_function_with_qualname(self):
        self.assertEqual(Theory.__qualname__, 'spanish_inquisition')

    def test_enum_of_types(self):
        """Support using Enum to refer to types deliberately."""
        klasse MyTypes(Enum):
            i = int
            f = float
            s = str
        self.assertEqual(MyTypes.i.value, int)
        self.assertEqual(MyTypes.f.value, float)
        self.assertEqual(MyTypes.s.value, str)
        klasse Foo:
            pass
        klasse Bar:
            pass
        klasse MyTypes2(Enum):
            a = Foo
            b = Bar
        self.assertEqual(MyTypes2.a.value, Foo)
        self.assertEqual(MyTypes2.b.value, Bar)
        klasse SpamEnumNotInner:
            pass
        klasse SpamEnum(Enum):
            spam = SpamEnumNotInner
        self.assertEqual(SpamEnum.spam.value, SpamEnumNotInner)

    def test_enum_of_generic_aliases(self):
        klasse E(Enum):
            a = typing.List[int]
            b = list[int]
        self.assertEqual(E.a.value, typing.List[int])
        self.assertEqual(E.b.value, list[int])
        self.assertEqual(repr(E.a), '<E.a: typing.List[int]>')
        self.assertEqual(repr(E.b), '<E.b: list[int]>')

    @unittest.skipIf(
            python_version >= (3, 13),
            'inner classes are not members',
            )
    def test_nested_classes_in_enum_are_members(self):
        """
        Check fuer warnings pre-3.13
        """
        with self.assertWarnsRegex(DeprecationWarning, 'will not become a member'):
            klasse Outer(Enum):
                a = 1
                b = 2
                klasse Inner(Enum):
                    foo = 10
                    bar = 11
        self.assertWahr(isinstance(Outer.Inner, Outer))
        self.assertEqual(Outer.a.value, 1)
        self.assertEqual(Outer.Inner.value.foo.value, 10)
        self.assertEqual(
            list(Outer.Inner.value),
            [Outer.Inner.value.foo, Outer.Inner.value.bar],
            )
        self.assertEqual(
            list(Outer),
            [Outer.a, Outer.b, Outer.Inner],
            )

    @unittest.skipIf(
            python_version < (3, 13),
            'inner classes are still members',
            )
    def test_nested_classes_in_enum_are_not_members(self):
        """Support locally-defined nested classes."""
        klasse Outer(Enum):
            a = 1
            b = 2
            klasse Inner(Enum):
                foo = 10
                bar = 11
        self.assertWahr(isinstance(Outer.Inner, type))
        self.assertEqual(Outer.a.value, 1)
        self.assertEqual(Outer.Inner.foo.value, 10)
        self.assertEqual(
            list(Outer.Inner),
            [Outer.Inner.foo, Outer.Inner.bar],
            )
        self.assertEqual(
            list(Outer),
            [Outer.a, Outer.b],
            )

    def test_nested_classes_in_enum_with_nonmember(self):
        klasse Outer(Enum):
            a = 1
            b = 2
            @nonmember
            klasse Inner(Enum):
                foo = 10
                bar = 11
        self.assertWahr(isinstance(Outer.Inner, type))
        self.assertEqual(Outer.a.value, 1)
        self.assertEqual(Outer.Inner.foo.value, 10)
        self.assertEqual(
            list(Outer.Inner),
            [Outer.Inner.foo, Outer.Inner.bar],
            )
        self.assertEqual(
            list(Outer),
            [Outer.a, Outer.b],
            )

    def test_enum_of_types_with_nonmember(self):
        """Support using Enum to refer to types deliberately."""
        klasse MyTypes(Enum):
            i = int
            f = nonmember(float)
            s = str
        self.assertEqual(MyTypes.i.value, int)
        self.assertWahr(MyTypes.f is float)
        self.assertEqual(MyTypes.s.value, str)
        klasse Foo:
            pass
        klasse Bar:
            pass
        klasse MyTypes2(Enum):
            a = Foo
            b = nonmember(Bar)
        self.assertEqual(MyTypes2.a.value, Foo)
        self.assertWahr(MyTypes2.b is Bar)
        klasse SpamEnumIsInner:
            pass
        klasse SpamEnum(Enum):
            spam = nonmember(SpamEnumIsInner)
        self.assertWahr(SpamEnum.spam is SpamEnumIsInner)

    def test_using_members_as_nonmember(self):
        klasse Example(Flag):
            A = 1
            B = 2
            ALL = nonmember(A | B)

        self.assertEqual(Example.A.value, 1)
        self.assertEqual(Example.B.value, 2)
        self.assertEqual(Example.ALL, 3)
        self.assertIs(type(Example.ALL), int)

        klasse Example(Flag):
            A = auto()
            B = auto()
            ALL = nonmember(A | B)

        self.assertEqual(Example.A.value, 1)
        self.assertEqual(Example.B.value, 2)
        self.assertEqual(Example.ALL, 3)
        self.assertIs(type(Example.ALL), int)

    def test_nested_classes_in_enum_with_member(self):
        """Support locally-defined nested classes."""
        klasse Outer(Enum):
            a = 1
            b = 2
            @member
            klasse Inner(Enum):
                foo = 10
                bar = 11
        self.assertWahr(isinstance(Outer.Inner, Outer))
        self.assertEqual(Outer.a.value, 1)
        self.assertEqual(Outer.Inner.value.foo.value, 10)
        self.assertEqual(
            list(Outer.Inner.value),
            [Outer.Inner.value.foo, Outer.Inner.value.bar],
            )
        self.assertEqual(
            list(Outer),
            [Outer.a, Outer.b, Outer.Inner],
            )

    def test_enum_with_value_name(self):
        klasse Huh(Enum):
            name = 1
            value = 2
        self.assertEqual(list(Huh), [Huh.name, Huh.value])
        self.assertIs(type(Huh.name), Huh)
        self.assertEqual(Huh.name.name, 'name')
        self.assertEqual(Huh.name.value, 1)

    def test_contains_name_and_value_overlap(self):
        klasse IntEnum1(IntEnum):
            X = 1
        klasse IntEnum2(IntEnum):
            X = 1
        klasse IntEnum3(IntEnum):
            X = 2
        klasse IntEnum4(IntEnum):
            Y = 1
        self.assertIn(IntEnum1.X, IntEnum1)
        self.assertIn(IntEnum1.X, IntEnum2)
        self.assertNotIn(IntEnum1.X, IntEnum3)
        self.assertIn(IntEnum1.X, IntEnum4)

    def test_contains_different_types_same_members(self):
        klasse IntEnum1(IntEnum):
            X = 1
        klasse IntFlag1(IntFlag):
            X = 1
        self.assertIn(IntEnum1.X, IntFlag1)
        self.assertIn(IntFlag1.X, IntEnum1)

    def test_contains_does_not_call_missing(self):
        klasse AnEnum(Enum):
            UNKNOWN = Nichts
            LUCKY = 3
            @classmethod
            def _missing_(cls, *values):
                return cls.UNKNOWN
        self.assertWahr(Nichts in AnEnum)
        self.assertWahr(3 in AnEnum)
        self.assertFalsch(7 in AnEnum)

    def test_inherited_data_type(self):
        klasse HexInt(int):
            __qualname__ = 'HexInt'
            def __repr__(self):
                return hex(self)
        klasse MyEnum(HexInt, enum.Enum):
            __qualname__ = 'MyEnum'
            A = 1
            B = 2
            C = 3
        self.assertEqual(repr(MyEnum.A), '<MyEnum.A: 0x1>')
        globals()['HexInt'] = HexInt
        globals()['MyEnum'] = MyEnum
        test_pickle_dump_load(self.assertIs, MyEnum.A)
        test_pickle_dump_load(self.assertIs, MyEnum)
        #
        klasse SillyInt(HexInt):
            __qualname__ = 'SillyInt'
        klasse MyOtherEnum(SillyInt, enum.Enum):
            __qualname__ = 'MyOtherEnum'
            D = 4
            E = 5
            F = 6
        self.assertIs(MyOtherEnum._member_type_, SillyInt)
        globals()['SillyInt'] = SillyInt
        globals()['MyOtherEnum'] = MyOtherEnum
        test_pickle_dump_load(self.assertIs, MyOtherEnum.E)
        test_pickle_dump_load(self.assertIs, MyOtherEnum)
        #
        # This did not work in 3.10, but does now with pickling by name
        klasse UnBrokenInt(int):
            __qualname__ = 'UnBrokenInt'
            def __new__(cls, value):
                return int.__new__(cls, value)
        klasse MyUnBrokenEnum(UnBrokenInt, Enum):
            __qualname__ = 'MyUnBrokenEnum'
            G = 7
            H = 8
            I = 9
        self.assertIs(MyUnBrokenEnum._member_type_, UnBrokenInt)
        self.assertIs(MyUnBrokenEnum(7), MyUnBrokenEnum.G)
        globals()['UnBrokenInt'] = UnBrokenInt
        globals()['MyUnBrokenEnum'] = MyUnBrokenEnum
        test_pickle_dump_load(self.assertIs, MyUnBrokenEnum.I)
        test_pickle_dump_load(self.assertIs, MyUnBrokenEnum)

    @reraise_if_not_enum(FloatStooges)
    def test_floatenum_fromhex(self):
        h = float.hex(FloatStooges.MOE.value)
        self.assertIs(FloatStooges.fromhex(h), FloatStooges.MOE)
        h = float.hex(FloatStooges.MOE.value + 0.01)
        with self.assertRaises(ValueError):
            FloatStooges.fromhex(h)

    def test_programmatic_function_type(self):
        MinorEnum = Enum('MinorEnum', 'june july august', type=int)
        lst = list(MinorEnum)
        self.assertEqual(len(lst), len(MinorEnum))
        self.assertEqual(len(MinorEnum), 3, MinorEnum)
        self.assertEqual(
                [MinorEnum.june, MinorEnum.july, MinorEnum.august],
                lst,
                )
        fuer i, month in enumerate('june july august'.split(), 1):
            e = MinorEnum(i)
            self.assertEqual(e, i)
            self.assertEqual(e.name, month)
            self.assertIn(e, MinorEnum)
            self.assertIs(type(e), MinorEnum)

    def test_programmatic_function_string_with_start(self):
        MinorEnum = Enum('MinorEnum', 'june july august', start=10)
        lst = list(MinorEnum)
        self.assertEqual(len(lst), len(MinorEnum))
        self.assertEqual(len(MinorEnum), 3, MinorEnum)
        self.assertEqual(
                [MinorEnum.june, MinorEnum.july, MinorEnum.august],
                lst,
                )
        fuer i, month in enumerate('june july august'.split(), 10):
            e = MinorEnum(i)
            self.assertEqual(int(e.value), i)
            self.assertNotEqual(e, i)
            self.assertEqual(e.name, month)
            self.assertIn(e, MinorEnum)
            self.assertIs(type(e), MinorEnum)

    def test_programmatic_function_type_with_start(self):
        MinorEnum = Enum('MinorEnum', 'june july august', type=int, start=30)
        lst = list(MinorEnum)
        self.assertEqual(len(lst), len(MinorEnum))
        self.assertEqual(len(MinorEnum), 3, MinorEnum)
        self.assertEqual(
                [MinorEnum.june, MinorEnum.july, MinorEnum.august],
                lst,
                )
        fuer i, month in enumerate('june july august'.split(), 30):
            e = MinorEnum(i)
            self.assertEqual(e, i)
            self.assertEqual(e.name, month)
            self.assertIn(e, MinorEnum)
            self.assertIs(type(e), MinorEnum)

    def test_programmatic_function_string_list_with_start(self):
        MinorEnum = Enum('MinorEnum', ['june', 'july', 'august'], start=20)
        lst = list(MinorEnum)
        self.assertEqual(len(lst), len(MinorEnum))
        self.assertEqual(len(MinorEnum), 3, MinorEnum)
        self.assertEqual(
                [MinorEnum.june, MinorEnum.july, MinorEnum.august],
                lst,
                )
        fuer i, month in enumerate('june july august'.split(), 20):
            e = MinorEnum(i)
            self.assertEqual(int(e.value), i)
            self.assertNotEqual(e, i)
            self.assertEqual(e.name, month)
            self.assertIn(e, MinorEnum)
            self.assertIs(type(e), MinorEnum)

    def test_programmatic_function_type_from_subclass(self):
        MinorEnum = IntEnum('MinorEnum', 'june july august')
        lst = list(MinorEnum)
        self.assertEqual(len(lst), len(MinorEnum))
        self.assertEqual(len(MinorEnum), 3, MinorEnum)
        self.assertEqual(
                [MinorEnum.june, MinorEnum.july, MinorEnum.august],
                lst,
                )
        fuer i, month in enumerate('june july august'.split(), 1):
            e = MinorEnum(i)
            self.assertEqual(e, i)
            self.assertEqual(e.name, month)
            self.assertIn(e, MinorEnum)
            self.assertIs(type(e), MinorEnum)

    def test_programmatic_function_type_from_subclass_with_start(self):
        MinorEnum = IntEnum('MinorEnum', 'june july august', start=40)
        lst = list(MinorEnum)
        self.assertEqual(len(lst), len(MinorEnum))
        self.assertEqual(len(MinorEnum), 3, MinorEnum)
        self.assertEqual(
                [MinorEnum.june, MinorEnum.july, MinorEnum.august],
                lst,
                )
        fuer i, month in enumerate('june july august'.split(), 40):
            e = MinorEnum(i)
            self.assertEqual(e, i)
            self.assertEqual(e.name, month)
            self.assertIn(e, MinorEnum)
            self.assertIs(type(e), MinorEnum)

    def test_programmatic_function_is_value_call(self):
        klasse TwoPart(Enum):
            ONE = 1, 1.0
            TWO = 2, 2.0
            THREE = 3, 3.0
        self.assertRaisesRegex(ValueError, '1 is not a valid .*TwoPart', TwoPart, 1)
        self.assertIs(TwoPart((1, 1.0)), TwoPart.ONE)
        self.assertIs(TwoPart(1, 1.0), TwoPart.ONE)
        klasse ThreePart(Enum):
            ONE = 1, 1.0, 'one'
            TWO = 2, 2.0, 'two'
            THREE = 3, 3.0, 'three'
        self.assertIs(ThreePart((3, 3.0, 'three')), ThreePart.THREE)
        self.assertIs(ThreePart(3, 3.0, 'three'), ThreePart.THREE)

    @reraise_if_not_enum(IntStooges)
    def test_intenum_from_bytes(self):
        self.assertIs(IntStooges.from_bytes(b'\x00\x03', 'big'), IntStooges.MOE)
        with self.assertRaises(ValueError):
            IntStooges.from_bytes(b'\x00\x05', 'big')

    def test_reserved_sunder_error(self):
        with self.assertRaisesRegex(
                ValueError,
                '_sunder_ names, such as ._bad_., are reserved',
            ):
            klasse Bad(Enum):
                _bad_ = 1

    def test_too_many_data_types(self):
        with self.assertRaisesRegex(TypeError, 'too many data types'):
            klasse Huh(str, int, Enum):
                One = 1

        klasse MyStr(str):
            def hello(self):
                return 'hello, %s' % self
        klasse MyInt(int):
            def repr(self):
                return hex(self)
        with self.assertRaisesRegex(TypeError, 'too many data types'):
            klasse Huh(MyStr, MyInt, Enum):
                One = 1

    @reraise_if_not_enum(Stooges)
    def test_pickle_enum(self):
        test_pickle_dump_load(self.assertIs, Stooges.CURLY)
        test_pickle_dump_load(self.assertIs, Stooges)

    @reraise_if_not_enum(IntStooges)
    def test_pickle_int(self):
        test_pickle_dump_load(self.assertIs, IntStooges.CURLY)
        test_pickle_dump_load(self.assertIs, IntStooges)

    @reraise_if_not_enum(FloatStooges)
    def test_pickle_float(self):
        test_pickle_dump_load(self.assertIs, FloatStooges.CURLY)
        test_pickle_dump_load(self.assertIs, FloatStooges)

    @reraise_if_not_enum(Answer)
    def test_pickle_enum_function(self):
        test_pickle_dump_load(self.assertIs, Answer.him)
        test_pickle_dump_load(self.assertIs, Answer)

    @reraise_if_not_enum(Question)
    def test_pickle_enum_function_with_module(self):
        test_pickle_dump_load(self.assertIs, Question.who)
        test_pickle_dump_load(self.assertIs, Question)

    def test_pickle_nested_class(self):
        # would normally just have this directly in the klasse namespace
        klasse NestedEnum(Enum):
            twigs = 'common'
            shiny = 'rare'

        self.__class__.NestedEnum = NestedEnum
        self.NestedEnum.__qualname__ = '%s.NestedEnum' % self.__class__.__name__
        test_pickle_dump_load(self.assertIs, self.NestedEnum.twigs)

    def test_pickle_by_name(self):
        klasse ReplaceGlobalInt(IntEnum):
            ONE = 1
            TWO = 2
        ReplaceGlobalInt.__reduce_ex__ = enum._reduce_ex_by_global_name
        fuer proto in range(HIGHEST_PROTOCOL):
            self.assertEqual(ReplaceGlobalInt.TWO.__reduce_ex__(proto), 'TWO')

    def test_pickle_explodes(self):
        BadPickle = Enum(
                'BadPickle', 'dill sweet bread-n-butter', module=__name__)
        globals()['BadPickle'] = BadPickle
        # now break BadPickle to test exception raising
        enum._make_class_unpicklable(BadPickle)
        test_pickle_exception(self.assertRaises, TypeError, BadPickle.dill)
        test_pickle_exception(self.assertRaises, PicklingError, BadPickle)

    def test_string_enum(self):
        klasse SkillLevel(str, Enum):
            master = 'what is the sound of one hand clapping?'
            journeyman = 'why did the chicken cross the road?'
            apprentice = 'knock, knock!'
        self.assertEqual(SkillLevel.apprentice, 'knock, knock!')

    def test_getattr_getitem(self):
        klasse Period(Enum):
            morning = 1
            noon = 2
            evening = 3
            night = 4
        self.assertIs(Period(2), Period.noon)
        self.assertIs(getattr(Period, 'night'), Period.night)
        self.assertIs(Period['morning'], Period.morning)

    def test_getattr_dunder(self):
        Season = self.Season
        self.assertWahr(getattr(Season, '__eq__'))

    def test_iteration_order(self):
        klasse Season(Enum):
            SUMMER = 2
            WINTER = 4
            AUTUMN = 3
            SPRING = 1
        self.assertEqual(
                list(Season),
                [Season.SUMMER, Season.WINTER, Season.AUTUMN, Season.SPRING],
                )

    @reraise_if_not_enum(Name)
    def test_subclassing(self):
        self.assertEqual(Name.BDFL, 'Guido van Rossum')
        self.assertWahr(Name.BDFL, Name('Guido van Rossum'))
        self.assertIs(Name.BDFL, getattr(Name, 'BDFL'))
        test_pickle_dump_load(self.assertIs, Name.BDFL)

    def test_extending(self):
        klasse Color(Enum):
            red = 1
            green = 2
            blue = 3
        #
        with self.assertRaises(TypeError):
            klasse MoreColor(Color):
                cyan = 4
                magenta = 5
                yellow = 6
        #
        with self.assertRaisesRegex(TypeError, "<enum .EvenMoreColor.> cannot extend <enum .Color.>"):
            klasse EvenMoreColor(Color, IntEnum):
                chartruese = 7
        #
        with self.assertRaisesRegex(ValueError, r"\(.Foo., \(.pink., .black.\)\) is not a valid .*Color"):
            Color('Foo', ('pink', 'black'))

    def test_exclude_methods(self):
        klasse whatever(Enum):
            this = 'that'
            these = 'those'
            def really(self):
                return 'no, not %s' % self.value
        self.assertIsNot(type(whatever.really), whatever)
        self.assertEqual(whatever.this.really(), 'no, not that')

    def test_wrong_inheritance_order(self):
        with self.assertRaises(TypeError):
            klasse Wrong(Enum, str):
                NotHere = 'error before this point'

    def test_raise_custom_error_on_creation(self):
        klasse InvalidRgbColorError(ValueError):
            def __init__(self, r, g, b):
                self.r = r
                self.g = g
                self.b = b
                super().__init__(f'({r}, {g}, {b}) is not a valid RGB color')

        with self.assertRaises(InvalidRgbColorError):
            klasse RgbColor(Enum):
                RED = (255, 0, 0)
                GREEN = (0, 255, 0)
                BLUE = (0, 0, 255)
                INVALID = (256, 0, 0)

                def __init__(self, r, g, b):
                    wenn not all(0 <= val <= 255 fuer val in (r, g, b)):
                        raise InvalidRgbColorError(r, g, b)

    def test_intenum_transitivity(self):
        klasse number(IntEnum):
            one = 1
            two = 2
            three = 3
        klasse numero(IntEnum):
            uno = 1
            dos = 2
            tres = 3
        self.assertEqual(number.one, numero.uno)
        self.assertEqual(number.two, numero.dos)
        self.assertEqual(number.three, numero.tres)

    def test_wrong_enum_in_call(self):
        klasse Monochrome(Enum):
            black = 0
            white = 1
        klasse Gender(Enum):
            male = 0
            female = 1
        self.assertRaises(ValueError, Monochrome, Gender.male)

    def test_wrong_enum_in_mixed_call(self):
        klasse Monochrome(IntEnum):
            black = 0
            white = 1
        klasse Gender(Enum):
            male = 0
            female = 1
        self.assertRaises(ValueError, Monochrome, Gender.male)

    def test_mixed_enum_in_call_1(self):
        klasse Monochrome(IntEnum):
            black = 0
            white = 1
        klasse Gender(IntEnum):
            male = 0
            female = 1
        self.assertIs(Monochrome(Gender.female), Monochrome.white)

    def test_mixed_enum_in_call_2(self):
        klasse Monochrome(Enum):
            black = 0
            white = 1
        klasse Gender(IntEnum):
            male = 0
            female = 1
        self.assertIs(Monochrome(Gender.male), Monochrome.black)

    def test_flufl_enum(self):
        klasse Fluflnum(Enum):
            def __int__(self):
                return int(self.value)
        klasse MailManOptions(Fluflnum):
            option1 = 1
            option2 = 2
            option3 = 3
        self.assertEqual(int(MailManOptions.option1), 1)

    def test_introspection(self):
        klasse Number(IntEnum):
            one = 100
            two = 200
        self.assertIs(Number.one._member_type_, int)
        self.assertIs(Number._member_type_, int)
        klasse String(str, Enum):
            yarn = 'soft'
            rope = 'rough'
            wire = 'hard'
        self.assertIs(String.yarn._member_type_, str)
        self.assertIs(String._member_type_, str)
        klasse Plain(Enum):
            vanilla = 'white'
            one = 1
        self.assertIs(Plain.vanilla._member_type_, object)
        self.assertIs(Plain._member_type_, object)

    def test_no_such_enum_member(self):
        klasse Color(Enum):
            red = 1
            green = 2
            blue = 3
        with self.assertRaises(ValueError):
            Color(4)
        with self.assertRaises(KeyError):
            Color['chartreuse']

    # tests that need to be evalualted fuer moving

    def test_multiple_mixin_mro(self):
        klasse auto_enum(type(Enum)):
            def __new__(metacls, cls, bases, classdict):
                temp = type(classdict)()
                temp._cls_name = cls
                names = set(classdict._member_names)
                i = 0
                fuer k in classdict._member_names:
                    v = classdict[k]
                    wenn v is Ellipsis:
                        v = i
                    sonst:
                        i = v
                    i += 1
                    temp[k] = v
                fuer k, v in classdict.items():
                    wenn k not in names:
                        temp[k] = v
                return super(auto_enum, metacls).__new__(
                        metacls, cls, bases, temp)

        klasse AutoNumberedEnum(Enum, metaclass=auto_enum):
            pass

        klasse AutoIntEnum(IntEnum, metaclass=auto_enum):
            pass

        klasse TestAutoNumber(AutoNumberedEnum):
            a = ...
            b = 3
            c = ...

        klasse TestAutoInt(AutoIntEnum):
            a = ...
            b = 3
            c = ...

    def test_subclasses_with_getnewargs(self):
        klasse NamedInt(int):
            __qualname__ = 'NamedInt'       # needed fuer pickle protocol 4
            def __new__(cls, *args):
                _args = args
                name, *args = args
                wenn len(args) == 0:
                    raise TypeError("name and value must be specified")
                self = int.__new__(cls, *args)
                self._intname = name
                self._args = _args
                return self
            def __getnewargs__(self):
                return self._args
            @bltns.property
            def __name__(self):
                return self._intname
            def __repr__(self):
                # repr() is updated to include the name and type info
                return "{}({!r}, {})".format(
                        type(self).__name__,
                        self.__name__,
                        int.__repr__(self),
                        )
            def __str__(self):
                # str() is unchanged, even wenn it relies on the repr() fallback
                base = int
                base_str = base.__str__
                wenn base_str.__objclass__ is object:
                    return base.__repr__(self)
                return base_str(self)
            # fuer simplicity, we only define one operator that
            # propagates expressions
            def __add__(self, other):
                temp = int(self) + int( other)
                wenn isinstance(self, NamedInt) and isinstance(other, NamedInt):
                    return NamedInt(
                        '({0} + {1})'.format(self.__name__, other.__name__),
                        temp,
                        )
                sonst:
                    return temp

        klasse NEI(NamedInt, Enum):
            __qualname__ = 'NEI'      # needed fuer pickle protocol 4
            x = ('the-x', 1)
            y = ('the-y', 2)


        self.assertIs(NEI.__new__, Enum.__new__)
        self.assertEqual(repr(NEI.x + NEI.y), "NamedInt('(the-x + the-y)', 3)")
        globals()['NamedInt'] = NamedInt
        globals()['NEI'] = NEI
        NI5 = NamedInt('test', 5)
        self.assertEqual(NI5, 5)
        test_pickle_dump_load(self.assertEqual, NI5, 5)
        self.assertEqual(NEI.y.value, 2)
        test_pickle_dump_load(self.assertIs, NEI.y)
        test_pickle_dump_load(self.assertIs, NEI)

    def test_subclasses_with_getnewargs_ex(self):
        klasse NamedInt(int):
            __qualname__ = 'NamedInt'       # needed fuer pickle protocol 4
            def __new__(cls, *args):
                _args = args
                name, *args = args
                wenn len(args) == 0:
                    raise TypeError("name and value must be specified")
                self = int.__new__(cls, *args)
                self._intname = name
                self._args = _args
                return self
            def __getnewargs_ex__(self):
                return self._args, {}
            @bltns.property
            def __name__(self):
                return self._intname
            def __repr__(self):
                # repr() is updated to include the name and type info
                return "{}({!r}, {})".format(
                        type(self).__name__,
                        self.__name__,
                        int.__repr__(self),
                        )
            def __str__(self):
                # str() is unchanged, even wenn it relies on the repr() fallback
                base = int
                base_str = base.__str__
                wenn base_str.__objclass__ is object:
                    return base.__repr__(self)
                return base_str(self)
            # fuer simplicity, we only define one operator that
            # propagates expressions
            def __add__(self, other):
                temp = int(self) + int( other)
                wenn isinstance(self, NamedInt) and isinstance(other, NamedInt):
                    return NamedInt(
                        '({0} + {1})'.format(self.__name__, other.__name__),
                        temp,
                        )
                sonst:
                    return temp

        klasse NEI(NamedInt, Enum):
            __qualname__ = 'NEI'      # needed fuer pickle protocol 4
            x = ('the-x', 1)
            y = ('the-y', 2)


        self.assertIs(NEI.__new__, Enum.__new__)
        self.assertEqual(repr(NEI.x + NEI.y), "NamedInt('(the-x + the-y)', 3)")
        globals()['NamedInt'] = NamedInt
        globals()['NEI'] = NEI
        NI5 = NamedInt('test', 5)
        self.assertEqual(NI5, 5)
        test_pickle_dump_load(self.assertEqual, NI5, 5)
        self.assertEqual(NEI.y.value, 2)
        test_pickle_dump_load(self.assertIs, NEI.y)
        test_pickle_dump_load(self.assertIs, NEI)

    def test_subclasses_with_reduce(self):
        klasse NamedInt(int):
            __qualname__ = 'NamedInt'       # needed fuer pickle protocol 4
            def __new__(cls, *args):
                _args = args
                name, *args = args
                wenn len(args) == 0:
                    raise TypeError("name and value must be specified")
                self = int.__new__(cls, *args)
                self._intname = name
                self._args = _args
                return self
            def __reduce__(self):
                return self.__class__, self._args
            @bltns.property
            def __name__(self):
                return self._intname
            def __repr__(self):
                # repr() is updated to include the name and type info
                return "{}({!r}, {})".format(
                        type(self).__name__,
                        self.__name__,
                        int.__repr__(self),
                        )
            def __str__(self):
                # str() is unchanged, even wenn it relies on the repr() fallback
                base = int
                base_str = base.__str__
                wenn base_str.__objclass__ is object:
                    return base.__repr__(self)
                return base_str(self)
            # fuer simplicity, we only define one operator that
            # propagates expressions
            def __add__(self, other):
                temp = int(self) + int( other)
                wenn isinstance(self, NamedInt) and isinstance(other, NamedInt):
                    return NamedInt(
                        '({0} + {1})'.format(self.__name__, other.__name__),
                        temp,
                        )
                sonst:
                    return temp

        klasse NEI(NamedInt, Enum):
            __qualname__ = 'NEI'      # needed fuer pickle protocol 4
            x = ('the-x', 1)
            y = ('the-y', 2)


        self.assertIs(NEI.__new__, Enum.__new__)
        self.assertEqual(repr(NEI.x + NEI.y), "NamedInt('(the-x + the-y)', 3)")
        globals()['NamedInt'] = NamedInt
        globals()['NEI'] = NEI
        NI5 = NamedInt('test', 5)
        self.assertEqual(NI5, 5)
        test_pickle_dump_load(self.assertEqual, NI5, 5)
        self.assertEqual(NEI.y.value, 2)
        test_pickle_dump_load(self.assertIs, NEI.y)
        test_pickle_dump_load(self.assertIs, NEI)

    def test_subclasses_with_reduce_ex(self):
        klasse NamedInt(int):
            __qualname__ = 'NamedInt'       # needed fuer pickle protocol 4
            def __new__(cls, *args):
                _args = args
                name, *args = args
                wenn len(args) == 0:
                    raise TypeError("name and value must be specified")
                self = int.__new__(cls, *args)
                self._intname = name
                self._args = _args
                return self
            def __reduce_ex__(self, proto):
                return self.__class__, self._args
            @bltns.property
            def __name__(self):
                return self._intname
            def __repr__(self):
                # repr() is updated to include the name and type info
                return "{}({!r}, {})".format(
                        type(self).__name__,
                        self.__name__,
                        int.__repr__(self),
                        )
            def __str__(self):
                # str() is unchanged, even wenn it relies on the repr() fallback
                base = int
                base_str = base.__str__
                wenn base_str.__objclass__ is object:
                    return base.__repr__(self)
                return base_str(self)
            # fuer simplicity, we only define one operator that
            # propagates expressions
            def __add__(self, other):
                temp = int(self) + int( other)
                wenn isinstance(self, NamedInt) and isinstance(other, NamedInt):
                    return NamedInt(
                        '({0} + {1})'.format(self.__name__, other.__name__),
                        temp,
                        )
                sonst:
                    return temp

        klasse NEI(NamedInt, Enum):
            __qualname__ = 'NEI'      # needed fuer pickle protocol 4
            x = ('the-x', 1)
            y = ('the-y', 2)

        self.assertIs(NEI.__new__, Enum.__new__)
        self.assertEqual(repr(NEI.x + NEI.y), "NamedInt('(the-x + the-y)', 3)")
        globals()['NamedInt'] = NamedInt
        globals()['NEI'] = NEI
        NI5 = NamedInt('test', 5)
        self.assertEqual(NI5, 5)
        test_pickle_dump_load(self.assertEqual, NI5, 5)
        self.assertEqual(NEI.y.value, 2)
        test_pickle_dump_load(self.assertIs, NEI.y)
        test_pickle_dump_load(self.assertIs, NEI)

    def test_subclasses_without_direct_pickle_support(self):
        klasse NamedInt(int):
            __qualname__ = 'NamedInt'
            def __new__(cls, *args):
                _args = args
                name, *args = args
                wenn len(args) == 0:
                    raise TypeError("name and value must be specified")
                self = int.__new__(cls, *args)
                self._intname = name
                self._args = _args
                return self
            @bltns.property
            def __name__(self):
                return self._intname
            def __repr__(self):
                # repr() is updated to include the name and type info
                return "{}({!r}, {})".format(
                        type(self).__name__,
                        self.__name__,
                        int.__repr__(self),
                        )
            def __str__(self):
                # str() is unchanged, even wenn it relies on the repr() fallback
                base = int
                base_str = base.__str__
                wenn base_str.__objclass__ is object:
                    return base.__repr__(self)
                return base_str(self)
            # fuer simplicity, we only define one operator that
            # propagates expressions
            def __add__(self, other):
                temp = int(self) + int( other)
                wenn isinstance(self, NamedInt) and isinstance(other, NamedInt):
                    return NamedInt(
                        '({0} + {1})'.format(self.__name__, other.__name__),
                        temp )
                sonst:
                    return temp

        klasse NEI(NamedInt, Enum):
            __qualname__ = 'NEI'
            x = ('the-x', 1)
            y = ('the-y', 2)
        self.assertIs(NEI.__new__, Enum.__new__)
        self.assertEqual(repr(NEI.x + NEI.y), "NamedInt('(the-x + the-y)', 3)")
        globals()['NamedInt'] = NamedInt
        globals()['NEI'] = NEI
        NI5 = NamedInt('test', 5)
        self.assertEqual(NI5, 5)
        self.assertEqual(NEI.y.value, 2)
        with self.assertRaisesRegex(TypeError, "name and value must be specified"):
            test_pickle_dump_load(self.assertIs, NEI.y)
        # fix pickle support and try again
        NEI.__reduce_ex__ = enum.pickle_by_enum_name
        test_pickle_dump_load(self.assertIs, NEI.y)
        test_pickle_dump_load(self.assertIs, NEI)

    def test_subclasses_with_direct_pickle_support(self):
        klasse NamedInt(int):
            __qualname__ = 'NamedInt'
            def __new__(cls, *args):
                _args = args
                name, *args = args
                wenn len(args) == 0:
                    raise TypeError("name and value must be specified")
                self = int.__new__(cls, *args)
                self._intname = name
                self._args = _args
                return self
            @bltns.property
            def __name__(self):
                return self._intname
            def __repr__(self):
                # repr() is updated to include the name and type info
                return "{}({!r}, {})".format(
                        type(self).__name__,
                        self.__name__,
                        int.__repr__(self),
                        )
            def __str__(self):
                # str() is unchanged, even wenn it relies on the repr() fallback
                base = int
                base_str = base.__str__
                wenn base_str.__objclass__ is object:
                    return base.__repr__(self)
                return base_str(self)
            # fuer simplicity, we only define one operator that
            # propagates expressions
            def __add__(self, other):
                temp = int(self) + int( other)
                wenn isinstance(self, NamedInt) and isinstance(other, NamedInt):
                    return NamedInt(
                        '({0} + {1})'.format(self.__name__, other.__name__),
                        temp,
                        )
                sonst:
                    return temp

        klasse NEI(NamedInt, Enum):
            __qualname__ = 'NEI'
            x = ('the-x', 1)
            y = ('the-y', 2)
            def __reduce_ex__(self, proto):
                return getattr, (self.__class__, self._name_)

        self.assertIs(NEI.__new__, Enum.__new__)
        self.assertEqual(repr(NEI.x + NEI.y), "NamedInt('(the-x + the-y)', 3)")
        globals()['NamedInt'] = NamedInt
        globals()['NEI'] = NEI
        NI5 = NamedInt('test', 5)
        self.assertEqual(NI5, 5)
        self.assertEqual(NEI.y.value, 2)
        test_pickle_dump_load(self.assertIs, NEI.y)
        test_pickle_dump_load(self.assertIs, NEI)

    def test_tuple_subclass(self):
        klasse SomeTuple(tuple, Enum):
            __qualname__ = 'SomeTuple'      # needed fuer pickle protocol 4
            first = (1, 'for the money')
            second = (2, 'for the show')
            third = (3, 'for the music')
        self.assertIs(type(SomeTuple.first), SomeTuple)
        self.assertIsInstance(SomeTuple.second, tuple)
        self.assertEqual(SomeTuple.third, (3, 'for the music'))
        globals()['SomeTuple'] = SomeTuple
        test_pickle_dump_load(self.assertIs, SomeTuple.first)

    def test_tuple_subclass_with_auto_1(self):
        from collections import namedtuple
        T = namedtuple('T', 'index desc')
        klasse SomeEnum(T, Enum):
            __qualname__ = 'SomeEnum'      # needed fuer pickle protocol 4
            first = auto(), 'for the money'
            second = auto(), 'for the show'
            third = auto(), 'for the music'
        self.assertIs(type(SomeEnum.first), SomeEnum)
        self.assertEqual(SomeEnum.third.value, (3, 'for the music'))
        self.assertIsInstance(SomeEnum.third.value, T)
        self.assertEqual(SomeEnum.first.index, 1)
        self.assertEqual(SomeEnum.second.desc, 'for the show')
        globals()['SomeEnum'] = SomeEnum
        globals()['T'] = T
        test_pickle_dump_load(self.assertIs, SomeEnum.first)

    def test_tuple_subclass_with_auto_2(self):
        from collections import namedtuple
        T = namedtuple('T', 'index desc')
        klasse SomeEnum(Enum):
            __qualname__ = 'SomeEnum'      # needed fuer pickle protocol 4
            first = T(auto(), 'for the money')
            second = T(auto(), 'for the show')
            third = T(auto(), 'for the music')
        self.assertIs(type(SomeEnum.first), SomeEnum)
        self.assertEqual(SomeEnum.third.value, (3, 'for the music'))
        self.assertIsInstance(SomeEnum.third.value, T)
        self.assertEqual(SomeEnum.first.value.index, 1)
        self.assertEqual(SomeEnum.second.value.desc, 'for the show')
        globals()['SomeEnum'] = SomeEnum
        globals()['T'] = T
        test_pickle_dump_load(self.assertIs, SomeEnum.first)

    def test_duplicate_values_give_unique_enum_items(self):
        klasse AutoNumber(Enum):
            first = ()
            second = ()
            third = ()
            def __new__(cls):
                value = len(cls.__members__) + 1
                obj = object.__new__(cls)
                obj._value_ = value
                return obj
            def __int__(self):
                return int(self._value_)
        self.assertEqual(
                list(AutoNumber),
                [AutoNumber.first, AutoNumber.second, AutoNumber.third],
                )
        self.assertEqual(int(AutoNumber.second), 2)
        self.assertEqual(AutoNumber.third.value, 3)
        self.assertIs(AutoNumber(1), AutoNumber.first)

    def test_inherited_new_from_enhanced_enum(self):
        klasse AutoNumber(Enum):
            def __new__(cls):
                value = len(cls.__members__) + 1
                obj = object.__new__(cls)
                obj._value_ = value
                return obj
            def __int__(self):
                return int(self._value_)
        klasse Color(AutoNumber):
            red = ()
            green = ()
            blue = ()
        self.assertEqual(list(Color), [Color.red, Color.green, Color.blue])
        self.assertEqual(list(map(int, Color)), [1, 2, 3])

    def test_inherited_new_from_mixed_enum(self):
        klasse AutoNumber(IntEnum):
            def __new__(cls):
                value = len(cls.__members__) + 1
                obj = int.__new__(cls, value)
                obj._value_ = value
                return obj
        klasse Color(AutoNumber):
            red = ()
            green = ()
            blue = ()
        self.assertEqual(list(Color), [Color.red, Color.green, Color.blue])
        self.assertEqual(list(map(int, Color)), [1, 2, 3])

    def test_equality(self):
        klasse OrdinaryEnum(Enum):
            a = 1
        self.assertEqual(ALWAYS_EQ, OrdinaryEnum.a)
        self.assertEqual(OrdinaryEnum.a, ALWAYS_EQ)

    def test_ordered_mixin(self):
        klasse OrderedEnum(Enum):
            def __ge__(self, other):
                wenn self.__class__ is other.__class__:
                    return self._value_ >= other._value_
                return NotImplemented
            def __gt__(self, other):
                wenn self.__class__ is other.__class__:
                    return self._value_ > other._value_
                return NotImplemented
            def __le__(self, other):
                wenn self.__class__ is other.__class__:
                    return self._value_ <= other._value_
                return NotImplemented
            def __lt__(self, other):
                wenn self.__class__ is other.__class__:
                    return self._value_ < other._value_
                return NotImplemented
        klasse Grade(OrderedEnum):
            A = 5
            B = 4
            C = 3
            D = 2
            F = 1
        self.assertGreater(Grade.A, Grade.B)
        self.assertLessEqual(Grade.F, Grade.C)
        self.assertLess(Grade.D, Grade.A)
        self.assertGreaterEqual(Grade.B, Grade.B)
        self.assertEqual(Grade.B, Grade.B)
        self.assertNotEqual(Grade.C, Grade.D)

    def test_extending2(self):
        klasse Shade(Enum):
            def shade(self):
                drucke(self.name)
        klasse Color(Shade):
            red = 1
            green = 2
            blue = 3
        with self.assertRaises(TypeError):
            klasse MoreColor(Color):
                cyan = 4
                magenta = 5
                yellow = 6

    def test_extending3(self):
        klasse Shade(Enum):
            def shade(self):
                return self.name
        klasse Color(Shade):
            def hex(self):
                return '%s hexlified!' % self.value
        klasse MoreColor(Color):
            cyan = 4
            magenta = 5
            yellow = 6
        self.assertEqual(MoreColor.magenta.hex(), '5 hexlified!')

    def test_subclass_duplicate_name(self):
        klasse Base(Enum):
            def test(self):
                pass
        klasse Test(Base):
            test = 1
        self.assertIs(type(Test.test), Test)

    def test_subclass_duplicate_name_dynamic(self):
        from types import DynamicClassAttribute
        klasse Base(Enum):
            @DynamicClassAttribute
            def test(self):
                return 'dynamic'
        klasse Test(Base):
            test = 1
        self.assertEqual(Test.test.test, 'dynamic')
        self.assertEqual(Test.test.value, 1)
        klasse Base2(Enum):
            @enum.property
            def flash(self):
                return 'flashy dynamic'
        klasse Test(Base2):
            flash = 1
        self.assertEqual(Test.flash.flash, 'flashy dynamic')
        self.assertEqual(Test.flash.value, 1)

    def test_no_duplicates(self):
        klasse UniqueEnum(Enum):
            def __init__(self, *args):
                cls = self.__class__
                wenn any(self.value == e.value fuer e in cls):
                    a = self.name
                    e = cls(self.value).name
                    raise ValueError(
                            "aliases not allowed in UniqueEnum:  %r --> %r"
                            % (a, e)
                            )
        klasse Color(UniqueEnum):
            red = 1
            green = 2
            blue = 3
        with self.assertRaises(ValueError):
            klasse Color(UniqueEnum):
                red = 1
                green = 2
                blue = 3
                grene = 2

    def test_init(self):
        klasse Planet(Enum):
            MERCURY = (3.303e+23, 2.4397e6)
            VENUS   = (4.869e+24, 6.0518e6)
            EARTH   = (5.976e+24, 6.37814e6)
            MARS    = (6.421e+23, 3.3972e6)
            JUPITER = (1.9e+27,   7.1492e7)
            SATURN  = (5.688e+26, 6.0268e7)
            URANUS  = (8.686e+25, 2.5559e7)
            NEPTUNE = (1.024e+26, 2.4746e7)
            def __init__(self, mass, radius):
                self.mass = mass       # in kilograms
                self.radius = radius   # in meters
            @enum.property
            def surface_gravity(self):
                # universal gravitational constant  (m3 kg-1 s-2)
                G = 6.67300E-11
                return G * self.mass / (self.radius * self.radius)
        self.assertEqual(round(Planet.EARTH.surface_gravity, 2), 9.80)
        self.assertEqual(Planet.EARTH.value, (5.976e+24, 6.37814e6))

    def test_ignore(self):
        klasse Period(timedelta, Enum):
            '''
            different lengths of time
            '''
            def __new__(cls, value, period):
                obj = timedelta.__new__(cls, value)
                obj._value_ = value
                obj.period = period
                return obj
            _ignore_ = 'Period i'
            Period = vars()
            fuer i in range(13):
                Period['month_%d' % i] = i*30, 'month'
            fuer i in range(53):
                Period['week_%d' % i] = i*7, 'week'
            fuer i in range(32):
                Period['day_%d' % i] = i, 'day'
            OneDay = day_1
            OneWeek = week_1
            OneMonth = month_1
        self.assertNotHasAttr(Period, '_ignore_')
        self.assertNotHasAttr(Period, 'Period')
        self.assertNotHasAttr(Period, 'i')
        self.assertIsInstance(Period.day_1, timedelta)
        self.assertIs(Period.month_1, Period.day_30)
        self.assertIs(Period.week_4, Period.day_28)

    def test_nonhash_value(self):
        klasse AutoNumberInAList(Enum):
            def __new__(cls):
                value = [len(cls.__members__) + 1]
                obj = object.__new__(cls)
                obj._value_ = value
                return obj
        klasse ColorInAList(AutoNumberInAList):
            red = ()
            green = ()
            blue = ()
        self.assertEqual(list(ColorInAList), [ColorInAList.red, ColorInAList.green, ColorInAList.blue])
        fuer enum, value in zip(ColorInAList, range(3)):
            value += 1
            self.assertEqual(enum.value, [value])
            self.assertIs(ColorInAList([value]), enum)

    def test_conflicting_types_resolved_in_new(self):
        klasse LabelledIntEnum(int, Enum):
            def __new__(cls, *args):
                value, label = args
                obj = int.__new__(cls, value)
                obj.label = label
                obj._value_ = value
                return obj

        klasse LabelledList(LabelledIntEnum):
            unprocessed = (1, "Unprocessed")
            payment_complete = (2, "Payment Complete")

        self.assertEqual(list(LabelledList), [LabelledList.unprocessed, LabelledList.payment_complete])
        self.assertEqual(LabelledList.unprocessed, 1)
        self.assertEqual(LabelledList(1), LabelledList.unprocessed)

    def test_default_missing_no_chained_exception(self):
        klasse Color(Enum):
            RED = 1
            GREEN = 2
            BLUE = 3
        try:
            Color(7)
        except ValueError as exc:
            self.assertWahr(exc.__context__ is Nichts)
        sonst:
            raise Exception('Exception not raised.')

    def test_missing_override(self):
        klasse Color(Enum):
            red = 1
            green = 2
            blue = 3
            @classmethod
            def _missing_(cls, item):
                wenn item == 'three':
                    return cls.blue
                sowenn item == 'bad return':
                    # trigger internal error
                    return 5
                sowenn item == 'error out':
                    raise ZeroDivisionError
                sonst:
                    # trigger not found
                    return Nichts
        self.assertIs(Color('three'), Color.blue)
        try:
            Color(7)
        except ValueError as exc:
            self.assertWahr(exc.__context__ is Nichts)
        sonst:
            raise Exception('Exception not raised.')
        try:
            Color('bad return')
        except TypeError as exc:
            self.assertWahr(isinstance(exc.__context__, ValueError))
        sonst:
            raise Exception('Exception not raised.')
        try:
            Color('error out')
        except ZeroDivisionError as exc:
            self.assertWahr(isinstance(exc.__context__, ValueError))
        sonst:
            raise Exception('Exception not raised.')

    def test_missing_exceptions_reset(self):
        import gc
        import weakref
        #
        klasse TestEnum(enum.Enum):
            VAL1 = 'val1'
            VAL2 = 'val2'
        #
        klasse Class1:
            def __init__(self):
                # Gracefully handle an exception of our own making
                try:
                    raise ValueError()
                except ValueError:
                    pass
        #
        klasse Class2:
            def __init__(self):
                # Gracefully handle an exception of Enum's making
                try:
                    TestEnum('invalid_value')
                except ValueError:
                    pass
        # No strong refs here so these are free to die.
        class_1_ref = weakref.ref(Class1())
        class_2_ref = weakref.ref(Class2())
        #
        # The exception raised by Enum used to create a reference loop and thus
        # Class2 instances would stick around until the next garbage collection
        # cycle, unlike Class1.  Verify Class2 no longer does this.
        gc.collect()  # For PyPy or other GCs.
        self.assertIs(class_1_ref(), Nichts)
        self.assertIs(class_2_ref(), Nichts)

    def test_multiple_mixin(self):
        klasse MaxMixin:
            @classproperty
            def MAX(cls):
                max = len(cls)
                cls.MAX = max
                return max
        klasse StrMixin:
            def __str__(self):
                return self._name_.lower()
        klasse SomeEnum(Enum):
            def behavior(self):
                return 'booyah'
        klasse AnotherEnum(Enum):
            def behavior(self):
                return 'nuhuh!'
            def social(self):
                return "what's up?"
        klasse Color(MaxMixin, Enum):
            RED = auto()
            GREEN = auto()
            BLUE = auto()
        self.assertEqual(Color.RED.value, 1)
        self.assertEqual(Color.GREEN.value, 2)
        self.assertEqual(Color.BLUE.value, 3)
        self.assertEqual(Color.MAX, 3)
        self.assertEqual(str(Color.BLUE), 'Color.BLUE')
        klasse Color(MaxMixin, StrMixin, Enum):
            RED = auto()
            GREEN = auto()
            BLUE = auto()
            __str__ = StrMixin.__str__          # needed as of 3.11
        self.assertEqual(Color.RED.value, 1)
        self.assertEqual(Color.GREEN.value, 2)
        self.assertEqual(Color.BLUE.value, 3)
        self.assertEqual(Color.MAX, 3)
        self.assertEqual(str(Color.BLUE), 'blue')
        klasse Color(StrMixin, MaxMixin, Enum):
            RED = auto()
            GREEN = auto()
            BLUE = auto()
            __str__ = StrMixin.__str__          # needed as of 3.11
        self.assertEqual(Color.RED.value, 1)
        self.assertEqual(Color.GREEN.value, 2)
        self.assertEqual(Color.BLUE.value, 3)
        self.assertEqual(Color.MAX, 3)
        self.assertEqual(str(Color.BLUE), 'blue')
        klasse CoolColor(StrMixin, SomeEnum, Enum):
            RED = auto()
            GREEN = auto()
            BLUE = auto()
            __str__ = StrMixin.__str__          # needed as of 3.11
        self.assertEqual(CoolColor.RED.value, 1)
        self.assertEqual(CoolColor.GREEN.value, 2)
        self.assertEqual(CoolColor.BLUE.value, 3)
        self.assertEqual(str(CoolColor.BLUE), 'blue')
        self.assertEqual(CoolColor.RED.behavior(), 'booyah')
        klasse CoolerColor(StrMixin, AnotherEnum, Enum):
            RED = auto()
            GREEN = auto()
            BLUE = auto()
            __str__ = StrMixin.__str__          # needed as of 3.11
        self.assertEqual(CoolerColor.RED.value, 1)
        self.assertEqual(CoolerColor.GREEN.value, 2)
        self.assertEqual(CoolerColor.BLUE.value, 3)
        self.assertEqual(str(CoolerColor.BLUE), 'blue')
        self.assertEqual(CoolerColor.RED.behavior(), 'nuhuh!')
        self.assertEqual(CoolerColor.RED.social(), "what's up?")
        klasse CoolestColor(StrMixin, SomeEnum, AnotherEnum):
            RED = auto()
            GREEN = auto()
            BLUE = auto()
            __str__ = StrMixin.__str__          # needed as of 3.11
        self.assertEqual(CoolestColor.RED.value, 1)
        self.assertEqual(CoolestColor.GREEN.value, 2)
        self.assertEqual(CoolestColor.BLUE.value, 3)
        self.assertEqual(str(CoolestColor.BLUE), 'blue')
        self.assertEqual(CoolestColor.RED.behavior(), 'booyah')
        self.assertEqual(CoolestColor.RED.social(), "what's up?")
        klasse ConfusedColor(StrMixin, AnotherEnum, SomeEnum):
            RED = auto()
            GREEN = auto()
            BLUE = auto()
            __str__ = StrMixin.__str__          # needed as of 3.11
        self.assertEqual(ConfusedColor.RED.value, 1)
        self.assertEqual(ConfusedColor.GREEN.value, 2)
        self.assertEqual(ConfusedColor.BLUE.value, 3)
        self.assertEqual(str(ConfusedColor.BLUE), 'blue')
        self.assertEqual(ConfusedColor.RED.behavior(), 'nuhuh!')
        self.assertEqual(ConfusedColor.RED.social(), "what's up?")
        klasse ReformedColor(StrMixin, IntEnum, SomeEnum, AnotherEnum):
            RED = auto()
            GREEN = auto()
            BLUE = auto()
            __str__ = StrMixin.__str__          # needed as of 3.11
        self.assertEqual(ReformedColor.RED.value, 1)
        self.assertEqual(ReformedColor.GREEN.value, 2)
        self.assertEqual(ReformedColor.BLUE.value, 3)
        self.assertEqual(str(ReformedColor.BLUE), 'blue')
        self.assertEqual(ReformedColor.RED.behavior(), 'booyah')
        self.assertEqual(ConfusedColor.RED.social(), "what's up?")
        self.assertIsSubclass(ReformedColor, int)

    def test_multiple_inherited_mixin(self):
        @unique
        klasse Decision1(StrEnum):
            REVERT = "REVERT"
            REVERT_ALL = "REVERT_ALL"
            RETRY = "RETRY"
        klasse MyEnum(StrEnum):
            pass
        @unique
        klasse Decision2(MyEnum):
            REVERT = "REVERT"
            REVERT_ALL = "REVERT_ALL"
            RETRY = "RETRY"

    def test_multiple_mixin_inherited(self):
        klasse MyInt(int):
            def __new__(cls, value):
                return super().__new__(cls, value)

        klasse HexMixin:
            def __repr__(self):
                return hex(self)

        klasse MyIntEnum(HexMixin, MyInt, enum.Enum):
            __repr__ = HexMixin.__repr__

        klasse Foo(MyIntEnum):
            TEST = 1
        self.assertWahr(isinstance(Foo.TEST, MyInt))
        self.assertEqual(Foo._member_type_, MyInt)
        self.assertEqual(repr(Foo.TEST), "0x1")

        klasse Fee(MyIntEnum):
            TEST = 1
            def __new__(cls, value):
                value += 1
                member = int.__new__(cls, value)
                member._value_ = value
                return member
        self.assertEqual(Fee.TEST, 2)

    def test_multiple_mixin_with_common_data_type(self):
        klasse CaseInsensitiveStrEnum(str, Enum):
            @classmethod
            def _missing_(cls, value):
                fuer member in cls._member_map_.values():
                    wenn member._value_.lower() == value.lower():
                        return member
                return super()._missing_(value)
        #
        klasse LenientStrEnum(str, Enum):
            def __init__(self, *args):
                self._valid = Wahr
            @classmethod
            def _missing_(cls, value):
                unknown = cls._member_type_.__new__(cls, value)
                unknown._valid = Falsch
                unknown._name_ = value.upper()
                unknown._value_ = value
                cls._member_map_[value] = unknown
                return unknown
            @enum.property
            def valid(self):
                return self._valid
        #
        klasse JobStatus(CaseInsensitiveStrEnum, LenientStrEnum):
            ACTIVE = "active"
            PENDING = "pending"
            TERMINATED = "terminated"
        #
        JS = JobStatus
        self.assertEqual(list(JobStatus), [JS.ACTIVE, JS.PENDING, JS.TERMINATED])
        self.assertEqual(JS.ACTIVE, 'active')
        self.assertEqual(JS.ACTIVE.value, 'active')
        self.assertIs(JS('Active'), JS.ACTIVE)
        self.assertWahr(JS.ACTIVE.valid)
        missing = JS('missing')
        self.assertEqual(list(JobStatus), [JS.ACTIVE, JS.PENDING, JS.TERMINATED])
        self.assertEqual(JS.ACTIVE, 'active')
        self.assertEqual(JS.ACTIVE.value, 'active')
        self.assertIs(JS('Active'), JS.ACTIVE)
        self.assertWahr(JS.ACTIVE.valid)
        self.assertWahr(isinstance(missing, JS))
        self.assertFalsch(missing.valid)

    def test_empty_globals(self):
        # bpo-35717: sys._getframe(2).f_globals['__name__'] fails with KeyError
        # when using compile and exec because f_globals is empty
        code = "from enum import Enum; Enum('Animal', 'ANT BEE CAT DOG')"
        code = compile(code, "<string>", "exec")
        global_ns = {}
        local_ls = {}
        exec(code, global_ns, local_ls)

    def test_strenum(self):
        klasse GoodStrEnum(StrEnum):
            one = '1'
            two = '2'
            three = b'3', 'ascii'
            four = b'4', 'latin1', 'strict'
        self.assertEqual(GoodStrEnum.one, '1')
        self.assertEqual(str(GoodStrEnum.one), '1')
        self.assertEqual('{}'.format(GoodStrEnum.one), '1')
        self.assertEqual(GoodStrEnum.one, str(GoodStrEnum.one))
        self.assertEqual(GoodStrEnum.one, '{}'.format(GoodStrEnum.one))
        self.assertEqual(repr(GoodStrEnum.one), "<GoodStrEnum.one: '1'>")
        #
        klasse DumbMixin:
            def __str__(self):
                return "don't do this"
        klasse DumbStrEnum(DumbMixin, StrEnum):
            five = '5'
            six = '6'
            seven = '7'
            __str__ = DumbMixin.__str__             # needed as of 3.11
        self.assertEqual(DumbStrEnum.seven, '7')
        self.assertEqual(str(DumbStrEnum.seven), "don't do this")
        #
        klasse EnumMixin(Enum):
            def hello(self):
                drucke('hello from %s' % (self, ))
        klasse HelloEnum(EnumMixin, StrEnum):
            eight = '8'
        self.assertEqual(HelloEnum.eight, '8')
        self.assertEqual(HelloEnum.eight, str(HelloEnum.eight))
        #
        klasse GoodbyeMixin:
            def goodbye(self):
                drucke('%s wishes you a fond farewell')
        klasse GoodbyeEnum(GoodbyeMixin, EnumMixin, StrEnum):
            nine = '9'
        self.assertEqual(GoodbyeEnum.nine, '9')
        self.assertEqual(GoodbyeEnum.nine, str(GoodbyeEnum.nine))
        #
        with self.assertRaisesRegex(TypeError, '1 is not a string'):
            klasse FirstFailedStrEnum(StrEnum):
                one = 1
                two = '2'
        with self.assertRaisesRegex(TypeError, "2 is not a string"):
            klasse SecondFailedStrEnum(StrEnum):
                one = '1'
                two = 2,
                three = '3'
        with self.assertRaisesRegex(TypeError, '2 is not a string'):
            klasse ThirdFailedStrEnum(StrEnum):
                one = '1'
                two = 2
        with self.assertRaisesRegex(TypeError, 'encoding must be a string, not %r' % (sys.getdefaultencoding, )):
            klasse ThirdFailedStrEnum(StrEnum):
                one = '1'
                two = b'2', sys.getdefaultencoding
        with self.assertRaisesRegex(TypeError, 'errors must be a string, not 9'):
            klasse ThirdFailedStrEnum(StrEnum):
                one = '1'
                two = b'2', 'ascii', 9

    def test_custom_strenum(self):
        klasse CustomStrEnum(str, Enum):
            pass
        klasse OkayEnum(CustomStrEnum):
            one = '1'
            two = '2'
            three = b'3', 'ascii'
            four = b'4', 'latin1', 'strict'
        self.assertEqual(OkayEnum.one, '1')
        self.assertEqual(str(OkayEnum.one), 'OkayEnum.one')
        self.assertEqual('{}'.format(OkayEnum.one), 'OkayEnum.one')
        self.assertEqual(repr(OkayEnum.one), "<OkayEnum.one: '1'>")
        #
        klasse DumbMixin:
            def __str__(self):
                return "don't do this"
        klasse DumbStrEnum(DumbMixin, CustomStrEnum):
            five = '5'
            six = '6'
            seven = '7'
            __str__ = DumbMixin.__str__         # needed as of 3.11
        self.assertEqual(DumbStrEnum.seven, '7')
        self.assertEqual(str(DumbStrEnum.seven), "don't do this")
        #
        klasse EnumMixin(Enum):
            def hello(self):
                drucke('hello from %s' % (self, ))
        klasse HelloEnum(EnumMixin, CustomStrEnum):
            eight = '8'
        self.assertEqual(HelloEnum.eight, '8')
        self.assertEqual(str(HelloEnum.eight), 'HelloEnum.eight')
        #
        klasse GoodbyeMixin:
            def goodbye(self):
                drucke('%s wishes you a fond farewell')
        klasse GoodbyeEnum(GoodbyeMixin, EnumMixin, CustomStrEnum):
            nine = '9'
        self.assertEqual(GoodbyeEnum.nine, '9')
        self.assertEqual(str(GoodbyeEnum.nine), 'GoodbyeEnum.nine')
        #
        klasse FirstFailedStrEnum(CustomStrEnum):
            one = 1   # this will become '1'
            two = '2'
        klasse SecondFailedStrEnum(CustomStrEnum):
            one = '1'
            two = 2,  # this will become '2'
            three = '3'
        klasse ThirdFailedStrEnum(CustomStrEnum):
            one = '1'
            two = 2  # this will become '2'
        with self.assertRaisesRegex(TypeError,
                r"argument (2|'encoding') must be str, not "):
            klasse ThirdFailedStrEnum(CustomStrEnum):
                one = '1'
                two = b'2', sys.getdefaultencoding
        with self.assertRaisesRegex(TypeError,
                r"argument (3|'errors') must be str, not "):
            klasse ThirdFailedStrEnum(CustomStrEnum):
                one = '1'
                two = b'2', 'ascii', 9

    def test_missing_value_error(self):
        with self.assertRaisesRegex(TypeError, "_value_ not set in __new__"):
            klasse Combined(str, Enum):
                #
                def __new__(cls, value, sequence):
                    enum = str.__new__(cls, value)
                    wenn '(' in value:
                        fis_name, segment = value.split('(', 1)
                        segment = segment.strip(' )')
                    sonst:
                        fis_name = value
                        segment = Nichts
                    enum.fis_name = fis_name
                    enum.segment = segment
                    enum.sequence = sequence
                    return enum
                #
                def __repr__(self):
                    return "<%s.%s>" % (self.__class__.__name__, self._name_)
                #
                key_type      = 'An$(1,2)', 0
                company_id    = 'An$(3,2)', 1
                code          = 'An$(5,1)', 2
                description   = 'Bn$',      3


    def test_private_variable_is_normal_attribute(self):
        klasse Private(Enum):
            __corporal = 'Radar'
            __major_ = 'Hoolihan'
        self.assertEqual(Private._Private__corporal, 'Radar')
        self.assertEqual(Private._Private__major_, 'Hoolihan')

    def test_member_from_member_access(self):
        klasse Di(Enum):
            YES = 1
            NO = 0
            name = 3
        warn = Di.YES.NO
        self.assertIs(warn, Di.NO)
        self.assertIs(Di.name, Di['name'])
        self.assertEqual(Di.name.name, 'name')

    def test_dynamic_members_with_static_methods(self):
        #
        foo_defines = {'FOO_CAT': 'aloof', 'BAR_DOG': 'friendly', 'FOO_HORSE': 'big'}
        klasse Foo(Enum):
            vars().update({
                    k: v
                    fuer k, v in foo_defines.items()
                    wenn k.startswith('FOO_')
                    })
            def upper(self):
                return self.value.upper()
        self.assertEqual(list(Foo), [Foo.FOO_CAT, Foo.FOO_HORSE])
        self.assertEqual(Foo.FOO_CAT.value, 'aloof')
        self.assertEqual(Foo.FOO_HORSE.upper(), 'BIG')
        #
        with self.assertRaisesRegex(TypeError, "'FOO_CAT' already defined as 'aloof'"):
            klasse FooBar(Enum):
                vars().update({
                        k: v
                        fuer k, v in foo_defines.items()
                        wenn k.startswith('FOO_')
                        },
                        **{'FOO_CAT': 'small'},
                        )
                def upper(self):
                    return self.value.upper()

    def test_repr_with_dataclass(self):
        "ensure dataclass-mixin has correct repr()"
        #
        # check overridden dataclass __repr__ is used
        #
        from dataclasses import dataclass, field
        @dataclass(repr=Falsch)
        klasse Foo:
            __qualname__ = 'Foo'
            a: int
            def __repr__(self):
                return 'ha hah!'
        klasse Entries(Foo, Enum):
            ENTRY1 = 1
        self.assertEqual(repr(Entries.ENTRY1), '<Entries.ENTRY1: ha hah!>')
        self.assertWahr(Entries.ENTRY1.value == Foo(1), Entries.ENTRY1.value)
        self.assertWahr(isinstance(Entries.ENTRY1, Foo))
        self.assertWahr(Entries._member_type_ is Foo, Entries._member_type_)
        #
        # check auto-generated dataclass __repr__ is not used
        #
        @dataclass
        klasse CreatureDataMixin:
            __qualname__ = 'CreatureDataMixin'
            size: str
            legs: int
            tail: bool = field(repr=Falsch, default=Wahr)
        klasse Creature(CreatureDataMixin, Enum):
            __qualname__ = 'Creature'
            BEETLE = ('small', 6)
            DOG = ('medium', 4)
        self.assertEqual(repr(Creature.DOG), "<Creature.DOG: size='medium', legs=4>")
        #
        # check inherited repr used
        #
        klasse Huh:
            def __repr__(self):
                return 'inherited'
        @dataclass(repr=Falsch)
        klasse CreatureDataMixin(Huh):
            __qualname__ = 'CreatureDataMixin'
            size: str
            legs: int
            tail: bool = field(repr=Falsch, default=Wahr)
        klasse Creature(CreatureDataMixin, Enum):
            __qualname__ = 'Creature'
            BEETLE = ('small', 6)
            DOG = ('medium', 4)
        self.assertEqual(repr(Creature.DOG), "<Creature.DOG: inherited>")
        #
        # check default object.__repr__ used wenn nothing provided
        #
        @dataclass(repr=Falsch)
        klasse CreatureDataMixin:
            __qualname__ = 'CreatureDataMixin'
            size: str
            legs: int
            tail: bool = field(repr=Falsch, default=Wahr)
        klasse Creature(CreatureDataMixin, Enum):
            __qualname__ = 'Creature'
            BEETLE = ('small', 6)
            DOG = ('medium', 4)
        self.assertRegex(repr(Creature.DOG), "<Creature.DOG: .*CreatureDataMixin object at .*>")

    def test_repr_with_init_mixin(self):
        klasse Foo:
            def __init__(self, a):
                self.a = a
            def __repr__(self):
                return f'Foo(a={self.a!r})'
        klasse Entries(Foo, Enum):
            ENTRY1 = 1
        #
        self.assertEqual(repr(Entries.ENTRY1), 'Foo(a=1)')

    def test_repr_and_str_with_no_init_mixin(self):
        # non-data_type is a mixin that doesn't define __new__
        klasse Foo:
            def __repr__(self):
                return 'Foo'
            def __str__(self):
                return 'ooF'
        klasse Entries(Foo, Enum):
            ENTRY1 = 1
        #
        self.assertEqual(repr(Entries.ENTRY1), 'Foo')
        self.assertEqual(str(Entries.ENTRY1), 'ooF')

    def test_value_backup_assign(self):
        # check that enum will add missing values when custom __new__ does not
        klasse Some(Enum):
            def __new__(cls, val):
                return object.__new__(cls)
            x = 1
            y = 2
        self.assertEqual(Some.x.value, 1)
        self.assertEqual(Some.y.value, 2)

    def test_custom_flag_bitwise(self):
        klasse MyIntFlag(int, Flag):
            ONE = 1
            TWO = 2
            FOUR = 4
        self.assertWahr(isinstance(MyIntFlag.ONE | MyIntFlag.TWO, MyIntFlag), MyIntFlag.ONE | MyIntFlag.TWO)
        self.assertWahr(isinstance(MyIntFlag.ONE | 2, MyIntFlag))

    def test_int_flags_copy(self):
        klasse MyIntFlag(IntFlag):
            ONE = 1
            TWO = 2
            FOUR = 4

        flags = MyIntFlag.ONE | MyIntFlag.TWO
        copied = copy.copy(flags)
        deep = copy.deepcopy(flags)
        self.assertEqual(copied, flags)
        self.assertEqual(deep, flags)

        flags = MyIntFlag.ONE | MyIntFlag.TWO | 8
        copied = copy.copy(flags)
        deep = copy.deepcopy(flags)
        self.assertEqual(copied, flags)
        self.assertEqual(deep, flags)
        self.assertEqual(copied.value, 1 | 2 | 8)

    def test_namedtuple_as_value(self):
        from collections import namedtuple
        TTuple = namedtuple('TTuple', 'id a blist')
        klasse NTEnum(Enum):
            NONE = TTuple(0, 0, [])
            A = TTuple(1, 2, [4])
            B = TTuple(2, 4, [0, 1, 2])
        self.assertEqual(repr(NTEnum.NONE), "<NTEnum.NONE: TTuple(id=0, a=0, blist=[])>")
        self.assertEqual(NTEnum.NONE.value, TTuple(id=0, a=0, blist=[]))
        self.assertEqual(
                [x.value fuer x in NTEnum],
                [TTuple(id=0, a=0, blist=[]), TTuple(id=1, a=2, blist=[4]), TTuple(id=2, a=4, blist=[0, 1, 2])],
                )

        self.assertRaises(AttributeError, getattr, NTEnum.NONE, 'id')
        #
        klasse NTCEnum(TTuple, Enum):
            NONE = 0, 0, []
            A = 1, 2, [4]
            B = 2, 4, [0, 1, 2]
        self.assertEqual(repr(NTCEnum.NONE), "<NTCEnum.NONE: TTuple(id=0, a=0, blist=[])>")
        self.assertEqual(NTCEnum.NONE.value, TTuple(id=0, a=0, blist=[]))
        self.assertEqual(NTCEnum.NONE.id, 0)
        self.assertEqual(NTCEnum.A.a, 2)
        self.assertEqual(NTCEnum.B.blist, [0, 1 ,2])
        self.assertEqual(
                [x.value fuer x in NTCEnum],
                [TTuple(id=0, a=0, blist=[]), TTuple(id=1, a=2, blist=[4]), TTuple(id=2, a=4, blist=[0, 1, 2])],
                )
        #
        klasse NTDEnum(Enum):
            def __new__(cls, id, a, blist):
                member = object.__new__(cls)
                member.id = id
                member.a = a
                member.blist = blist
                return member
            NONE = TTuple(0, 0, [])
            A = TTuple(1, 2, [4])
            B = TTuple(2, 4, [0, 1, 2])
        self.assertEqual(repr(NTDEnum.NONE), "<NTDEnum.NONE: TTuple(id=0, a=0, blist=[])>")
        self.assertEqual(NTDEnum.NONE.id, 0)
        self.assertEqual(NTDEnum.A.a, 2)
        self.assertEqual(NTDEnum.B.blist, [0, 1 ,2])

    def test_flag_with_custom_new(self):
        klasse FlagFromChar(IntFlag):
            def __new__(cls, c):
                value = 1 << c
                self = int.__new__(cls, value)
                self._value_ = value
                return self
            #
            a = ord('a')
        #
        self.assertEqual(FlagFromChar._all_bits_, 316912650057057350374175801343)
        self.assertEqual(FlagFromChar._flag_mask_, 158456325028528675187087900672)
        self.assertEqual(FlagFromChar.a, 158456325028528675187087900672)
        self.assertEqual(FlagFromChar.a|1, 158456325028528675187087900673)
        #
        #
        klasse FlagFromChar(Flag):
            def __new__(cls, c):
                value = 1 << c
                self = object.__new__(cls)
                self._value_ = value
                return self
            #
            a = ord('a')
            z = 1
        #
        self.assertEqual(FlagFromChar._all_bits_, 316912650057057350374175801343)
        self.assertEqual(FlagFromChar._flag_mask_, 158456325028528675187087900674)
        self.assertEqual(FlagFromChar.a.value, 158456325028528675187087900672)
        self.assertEqual((FlagFromChar.a|FlagFromChar.z).value, 158456325028528675187087900674)
        #
        #
        klasse FlagFromChar(int, Flag, boundary=KEEP):
            def __new__(cls, c):
                value = 1 << c
                self = int.__new__(cls, value)
                self._value_ = value
                return self
            #
            a = ord('a')
        #
        self.assertEqual(FlagFromChar._all_bits_, 316912650057057350374175801343)
        self.assertEqual(FlagFromChar._flag_mask_, 158456325028528675187087900672)
        self.assertEqual(FlagFromChar.a, 158456325028528675187087900672)
        self.assertEqual(FlagFromChar.a|1, 158456325028528675187087900673)

    def test_init_exception(self):
        klasse Base:
            def __new__(cls, *args):
                return object.__new__(cls)
            def __init__(self, x):
                raise ValueError("I don't like", x)
        with self.assertRaises(TypeError):
            klasse MyEnum(Base, enum.Enum):
                A = 'a'
                def __init__(self, y):
                    self.y = y
        with self.assertRaises(ValueError):
            klasse MyEnum(Base, enum.Enum):
                A = 'a'
                def __init__(self, y):
                    self.y = y
                def __new__(cls, value):
                    member = Base.__new__(cls)
                    member._value_ = Base(value)
                    return member

    def test_extra_member_creation(self):
        klasse IDEnumMeta(EnumMeta):
            def __new__(metacls, cls, bases, classdict, **kwds):
                # add new entries to classdict
                fuer name in classdict.member_names:
                    classdict[f'{name}_DESC'] = f'-{classdict[name]}'
                return super().__new__(metacls, cls, bases, classdict, **kwds)
        klasse IDEnum(StrEnum, metaclass=IDEnumMeta):
            pass
        klasse MyEnum(IDEnum):
            ID = 'id'
            NAME = 'name'
        self.assertEqual(list(MyEnum), [MyEnum.ID, MyEnum.NAME, MyEnum.ID_DESC, MyEnum.NAME_DESC])

    def test_add_alias(self):
        klasse mixin:
            @property
            def ORG(self):
                return 'huh'
        klasse Color(mixin, Enum):
            RED = 1
            GREEN = 2
            BLUE = 3
        Color.RED._add_alias_('ROJO')
        self.assertIs(Color.RED, Color['ROJO'])
        self.assertIs(Color.RED, Color.ROJO)
        Color.BLUE._add_alias_('ORG')
        self.assertIs(Color.BLUE, Color['ORG'])
        self.assertIs(Color.BLUE, Color.ORG)
        self.assertEqual(Color.RED.ORG, 'huh')
        self.assertEqual(Color.GREEN.ORG, 'huh')
        self.assertEqual(Color.BLUE.ORG, 'huh')
        self.assertEqual(Color.ORG.ORG, 'huh')

    def test_add_value_alias_after_creation(self):
        klasse Color(Enum):
            RED = 1
            GREEN = 2
            BLUE = 3
        Color.RED._add_value_alias_(5)
        self.assertIs(Color.RED, Color(5))

    def test_add_value_alias_during_creation(self):
        klasse Types(Enum):
            Unknown = 0,
            Source  = 1, 'src'
            NetList = 2, 'nl'
            def __new__(cls, int_value, *value_aliases):
                member = object.__new__(cls)
                member._value_ = int_value
                fuer alias in value_aliases:
                    member._add_value_alias_(alias)
                return member
        self.assertIs(Types(0), Types.Unknown)
        self.assertIs(Types(1), Types.Source)
        self.assertIs(Types('src'), Types.Source)
        self.assertIs(Types(2), Types.NetList)
        self.assertIs(Types('nl'), Types.NetList)

    def test_second_tuple_item_is_falsey(self):
        klasse Cardinal(Enum):
            RIGHT = (1, 0)
            UP = (0, 1)
            LEFT = (-1, 0)
            DOWN = (0, -1)
        self.assertIs(Cardinal(1, 0), Cardinal.RIGHT)
        self.assertIs(Cardinal(-1, 0), Cardinal.LEFT)

    def test_no_members(self):
        with self.assertRaisesRegex(
                TypeError,
                'has no members',
            ):
            Enum(7)
        with self.assertRaisesRegex(
                TypeError,
                'has no members',
            ):
            Flag(7)

    def test_empty_names(self):
        fuer nothing in '', [], {}:
            fuer e_type in Nichts, int:
                empty_enum = Enum('empty_enum', nothing, type=e_type)
                self.assertEqual(len(empty_enum), 0)
                self.assertRaisesRegex(TypeError, 'has no members', empty_enum, 0)
        self.assertRaisesRegex(TypeError, '.int. object is not iterable', Enum, 'bad_enum', names=0)
        self.assertRaisesRegex(TypeError, '.int. object is not iterable', Enum, 'bad_enum', 0, type=int)

    def test_nonhashable_matches_hashable(self):    # issue 125710
        klasse Directions(Enum):
            DOWN_ONLY = frozenset({"sc"})
            UP_ONLY = frozenset({"cs"})
            UNRESTRICTED = frozenset({"sc", "cs"})
        self.assertIs(Directions({"sc"}), Directions.DOWN_ONLY)


klasse TestOrder(unittest.TestCase):
    "test usage of the `_order_` attribute"

    def test_same_members(self):
        klasse Color(Enum):
            _order_ = 'red green blue'
            red = 1
            green = 2
            blue = 3

    def test_same_members_with_aliases(self):
        klasse Color(Enum):
            _order_ = 'red green blue'
            red = 1
            green = 2
            blue = 3
            verde = green

    def test_same_members_wrong_order(self):
        with self.assertRaisesRegex(TypeError, 'member order does not match _order_'):
            klasse Color(Enum):
                _order_ = 'red green blue'
                red = 1
                blue = 3
                green = 2

    def test_order_has_extra_members(self):
        with self.assertRaisesRegex(TypeError, 'member order does not match _order_'):
            klasse Color(Enum):
                _order_ = 'red green blue purple'
                red = 1
                green = 2
                blue = 3

    def test_order_has_extra_members_with_aliases(self):
        with self.assertRaisesRegex(TypeError, 'member order does not match _order_'):
            klasse Color(Enum):
                _order_ = 'red green blue purple'
                red = 1
                green = 2
                blue = 3
                verde = green

    def test_enum_has_extra_members(self):
        with self.assertRaisesRegex(TypeError, 'member order does not match _order_'):
            klasse Color(Enum):
                _order_ = 'red green blue'
                red = 1
                green = 2
                blue = 3
                purple = 4

    def test_enum_has_extra_members_with_aliases(self):
        with self.assertRaisesRegex(TypeError, 'member order does not match _order_'):
            klasse Color(Enum):
                _order_ = 'red green blue'
                red = 1
                green = 2
                blue = 3
                purple = 4
                verde = green


klasse OldTestFlag(unittest.TestCase):
    """Tests of the Flags."""

    klasse Perm(Flag):
        R, W, X = 4, 2, 1

    klasse Open(Flag):
        RO = 0
        WO = 1
        RW = 2
        AC = 3
        CE = 1<<19

    klasse Color(Flag):
        BLACK = 0
        RED = 1
        ROJO = 1
        GREEN = 2
        BLUE = 4
        PURPLE = RED|BLUE
        WHITE = RED|GREEN|BLUE
        BLANCO = RED|GREEN|BLUE

    def test_or(self):
        Perm = self.Perm
        fuer i in Perm:
            fuer j in Perm:
                self.assertEqual((i | j), Perm(i.value | j.value))
                self.assertEqual((i | j).value, i.value | j.value)
                self.assertIs(type(i | j), Perm)
        fuer i in Perm:
            self.assertIs(i | i, i)
        Open = self.Open
        self.assertIs(Open.RO | Open.CE, Open.CE)

    def test_and(self):
        Perm = self.Perm
        RW = Perm.R | Perm.W
        RX = Perm.R | Perm.X
        WX = Perm.W | Perm.X
        RWX = Perm.R | Perm.W | Perm.X
        values = list(Perm) + [RW, RX, WX, RWX, Perm(0)]
        fuer i in values:
            fuer j in values:
                self.assertEqual((i & j).value, i.value & j.value)
                self.assertIs(type(i & j), Perm)
        fuer i in Perm:
            self.assertIs(i & i, i)
            self.assertIs(i & RWX, i)
            self.assertIs(RWX & i, i)
        Open = self.Open
        self.assertIs(Open.RO & Open.CE, Open.RO)

    def test_xor(self):
        Perm = self.Perm
        fuer i in Perm:
            fuer j in Perm:
                self.assertEqual((i ^ j).value, i.value ^ j.value)
                self.assertIs(type(i ^ j), Perm)
        fuer i in Perm:
            self.assertIs(i ^ Perm(0), i)
            self.assertIs(Perm(0) ^ i, i)
        Open = self.Open
        self.assertIs(Open.RO ^ Open.CE, Open.CE)
        self.assertIs(Open.CE ^ Open.CE, Open.RO)

    def test_bool(self):
        Perm = self.Perm
        fuer f in Perm:
            self.assertWahr(f)
        Open = self.Open
        fuer f in Open:
            self.assertEqual(bool(f.value), bool(f))

    def test_boundary(self):
        self.assertIs(enum.Flag._boundary_, STRICT)
        klasse Iron(Flag, boundary=CONFORM):
            ONE = 1
            TWO = 2
            EIGHT = 8
        self.assertIs(Iron._boundary_, CONFORM)
        #
        klasse Water(Flag, boundary=STRICT):
            ONE = 1
            TWO = 2
            EIGHT = 8
        self.assertIs(Water._boundary_, STRICT)
        #
        klasse Space(Flag, boundary=EJECT):
            ONE = 1
            TWO = 2
            EIGHT = 8
        self.assertIs(Space._boundary_, EJECT)
        #
        klasse Bizarre(Flag, boundary=KEEP):
            b = 3
            c = 4
            d = 6
        #
        self.assertRaisesRegex(ValueError, 'invalid value 7', Water, 7)
        #
        self.assertIs(Iron(7), Iron.ONE|Iron.TWO)
        self.assertIs(Iron(~9), Iron.TWO)
        #
        self.assertEqual(Space(7), 7)
        self.assertWahr(type(Space(7)) is int)
        #
        self.assertEqual(list(Bizarre), [Bizarre.c])
        self.assertIs(Bizarre(3), Bizarre.b)
        self.assertIs(Bizarre(6), Bizarre.d)
        #
        klasse SkipFlag(enum.Flag):
            A = 1
            B = 2
            C = 4 | B
        #
        self.assertWahr(SkipFlag.C in (SkipFlag.A|SkipFlag.C))
        self.assertWahr(SkipFlag.B in SkipFlag.C)
        self.assertIs(SkipFlag(~1), SkipFlag.B)
        self.assertRaisesRegex(ValueError, 'SkipFlag.. invalid value 42', SkipFlag, 42)
        #
        klasse SkipIntFlag(enum.IntFlag):
            A = 1
            B = 2
            C = 4 | B
        #
        self.assertWahr(SkipIntFlag.C in (SkipIntFlag.A|SkipIntFlag.C))
        self.assertWahr(SkipIntFlag.B in SkipIntFlag.C)
        self.assertIs(SkipIntFlag(~1), SkipIntFlag.B|SkipIntFlag.C)
        self.assertEqual(SkipIntFlag(42).value, 42)
        #
        klasse MethodHint(Flag):
            HiddenText = 0x10
            DigitsOnly = 0x01
            LettersOnly = 0x02
            OnlyMask = 0x0f
        #
        self.assertEqual(str(MethodHint.HiddenText|MethodHint.OnlyMask), 'MethodHint.HiddenText|DigitsOnly|LettersOnly|OnlyMask')


    def test_iter(self):
        Color = self.Color
        Open = self.Open
        self.assertEqual(list(Color), [Color.RED, Color.GREEN, Color.BLUE])
        self.assertEqual(list(Open), [Open.WO, Open.RW, Open.CE])

    def test_programatic_function_string(self):
        Perm = Flag('Perm', 'R W X')
        lst = list(Perm)
        self.assertEqual(len(lst), len(Perm))
        self.assertEqual(len(Perm), 3, Perm)
        self.assertEqual(lst, [Perm.R, Perm.W, Perm.X])
        fuer i, n in enumerate('R W X'.split()):
            v = 1<<i
            e = Perm(v)
            self.assertEqual(e.value, v)
            self.assertEqual(type(e.value), int)
            self.assertEqual(e.name, n)
            self.assertIn(e, Perm)
            self.assertIs(type(e), Perm)

    def test_programatic_function_string_with_start(self):
        Perm = Flag('Perm', 'R W X', start=8)
        lst = list(Perm)
        self.assertEqual(len(lst), len(Perm))
        self.assertEqual(len(Perm), 3, Perm)
        self.assertEqual(lst, [Perm.R, Perm.W, Perm.X])
        fuer i, n in enumerate('R W X'.split()):
            v = 8<<i
            e = Perm(v)
            self.assertEqual(e.value, v)
            self.assertEqual(type(e.value), int)
            self.assertEqual(e.name, n)
            self.assertIn(e, Perm)
            self.assertIs(type(e), Perm)

    def test_programatic_function_string_list(self):
        Perm = Flag('Perm', ['R', 'W', 'X'])
        lst = list(Perm)
        self.assertEqual(len(lst), len(Perm))
        self.assertEqual(len(Perm), 3, Perm)
        self.assertEqual(lst, [Perm.R, Perm.W, Perm.X])
        fuer i, n in enumerate('R W X'.split()):
            v = 1<<i
            e = Perm(v)
            self.assertEqual(e.value, v)
            self.assertEqual(type(e.value), int)
            self.assertEqual(e.name, n)
            self.assertIn(e, Perm)
            self.assertIs(type(e), Perm)

    def test_programatic_function_iterable(self):
        Perm = Flag('Perm', (('R', 2), ('W', 8), ('X', 32)))
        lst = list(Perm)
        self.assertEqual(len(lst), len(Perm))
        self.assertEqual(len(Perm), 3, Perm)
        self.assertEqual(lst, [Perm.R, Perm.W, Perm.X])
        fuer i, n in enumerate('R W X'.split()):
            v = 1<<(2*i+1)
            e = Perm(v)
            self.assertEqual(e.value, v)
            self.assertEqual(type(e.value), int)
            self.assertEqual(e.name, n)
            self.assertIn(e, Perm)
            self.assertIs(type(e), Perm)

    def test_programatic_function_from_dict(self):
        Perm = Flag('Perm', OrderedDict((('R', 2), ('W', 8), ('X', 32))))
        lst = list(Perm)
        self.assertEqual(len(lst), len(Perm))
        self.assertEqual(len(Perm), 3, Perm)
        self.assertEqual(lst, [Perm.R, Perm.W, Perm.X])
        fuer i, n in enumerate('R W X'.split()):
            v = 1<<(2*i+1)
            e = Perm(v)
            self.assertEqual(e.value, v)
            self.assertEqual(type(e.value), int)
            self.assertEqual(e.name, n)
            self.assertIn(e, Perm)
            self.assertIs(type(e), Perm)

    @reraise_if_not_enum(
        FlagStooges,
        FlagStoogesWithZero,
        IntFlagStooges,
        IntFlagStoogesWithZero,
    )
    def test_pickle(self):
        test_pickle_dump_load(self.assertIs, FlagStooges.CURLY)
        test_pickle_dump_load(self.assertEqual,
                        FlagStooges.CURLY|FlagStooges.MOE)
        test_pickle_dump_load(self.assertEqual,
                        FlagStooges.CURLY&~FlagStooges.CURLY)
        test_pickle_dump_load(self.assertIs, FlagStooges)
        test_pickle_dump_load(self.assertEqual, FlagStooges.BIG)
        test_pickle_dump_load(self.assertEqual,
                        FlagStooges.CURLY|FlagStooges.BIG)

        test_pickle_dump_load(self.assertIs, FlagStoogesWithZero.CURLY)
        test_pickle_dump_load(self.assertEqual,
                        FlagStoogesWithZero.CURLY|FlagStoogesWithZero.MOE)
        test_pickle_dump_load(self.assertIs, FlagStoogesWithZero.NOFLAG)
        test_pickle_dump_load(self.assertEqual, FlagStoogesWithZero.BIG)
        test_pickle_dump_load(self.assertEqual,
                        FlagStoogesWithZero.CURLY|FlagStoogesWithZero.BIG)

        test_pickle_dump_load(self.assertIs, IntFlagStooges.CURLY)
        test_pickle_dump_load(self.assertEqual,
                        IntFlagStooges.CURLY|IntFlagStooges.MOE)
        test_pickle_dump_load(self.assertEqual,
                        IntFlagStooges.CURLY|IntFlagStooges.MOE|0x30)
        test_pickle_dump_load(self.assertEqual, IntFlagStooges(0))
        test_pickle_dump_load(self.assertEqual, IntFlagStooges(0x30))
        test_pickle_dump_load(self.assertIs, IntFlagStooges)
        test_pickle_dump_load(self.assertEqual, IntFlagStooges.BIG)
        test_pickle_dump_load(self.assertEqual, IntFlagStooges.BIG|1)
        test_pickle_dump_load(self.assertEqual,
                        IntFlagStooges.CURLY|IntFlagStooges.BIG)

        test_pickle_dump_load(self.assertIs, IntFlagStoogesWithZero.CURLY)
        test_pickle_dump_load(self.assertEqual,
                        IntFlagStoogesWithZero.CURLY|IntFlagStoogesWithZero.MOE)
        test_pickle_dump_load(self.assertIs, IntFlagStoogesWithZero.NOFLAG)
        test_pickle_dump_load(self.assertEqual, IntFlagStoogesWithZero.BIG)
        test_pickle_dump_load(self.assertEqual, IntFlagStoogesWithZero.BIG|1)
        test_pickle_dump_load(self.assertEqual,
                        IntFlagStoogesWithZero.CURLY|IntFlagStoogesWithZero.BIG)

    def test_contains_tf(self):
        Open = self.Open
        Color = self.Color
        self.assertFalsch(Color.BLACK in Open)
        self.assertFalsch(Open.RO in Color)
        self.assertFalsch('BLACK' in Color)
        self.assertFalsch('RO' in Open)
        self.assertWahr(Color.BLACK in Color)
        self.assertWahr(Open.RO in Open)
        self.assertWahr(1 in Color)
        self.assertWahr(1 in Open)

    def test_member_contains(self):
        Perm = self.Perm
        R, W, X = Perm
        RW = R | W
        RX = R | X
        WX = W | X
        RWX = R | W | X
        self.assertWahr(R in RW)
        self.assertWahr(R in RX)
        self.assertWahr(R in RWX)
        self.assertWahr(W in RW)
        self.assertWahr(W in WX)
        self.assertWahr(W in RWX)
        self.assertWahr(X in RX)
        self.assertWahr(X in WX)
        self.assertWahr(X in RWX)
        self.assertFalsch(R in WX)
        self.assertFalsch(W in RX)
        self.assertFalsch(X in RW)

    def test_member_iter(self):
        Color = self.Color
        self.assertEqual(list(Color.BLACK), [])
        self.assertEqual(list(Color.PURPLE), [Color.RED, Color.BLUE])
        self.assertEqual(list(Color.BLUE), [Color.BLUE])
        self.assertEqual(list(Color.GREEN), [Color.GREEN])
        self.assertEqual(list(Color.WHITE), [Color.RED, Color.GREEN, Color.BLUE])
        self.assertEqual(list(Color.WHITE), [Color.RED, Color.GREEN, Color.BLUE])

    def test_member_length(self):
        self.assertEqual(self.Color.__len__(self.Color.BLACK), 0)
        self.assertEqual(self.Color.__len__(self.Color.GREEN), 1)
        self.assertEqual(self.Color.__len__(self.Color.PURPLE), 2)
        self.assertEqual(self.Color.__len__(self.Color.BLANCO), 3)

    def test_number_reset_and_order_cleanup(self):
        klasse Confused(Flag):
            _order_ = 'ONE TWO FOUR DOS EIGHT SIXTEEN'
            ONE = auto()
            TWO = auto()
            FOUR = auto()
            DOS = 2
            EIGHT = auto()
            SIXTEEN = auto()
        self.assertEqual(
                list(Confused),
                [Confused.ONE, Confused.TWO, Confused.FOUR, Confused.EIGHT, Confused.SIXTEEN])
        self.assertIs(Confused.TWO, Confused.DOS)
        self.assertEqual(Confused.DOS._value_, 2)
        self.assertEqual(Confused.EIGHT._value_, 8)
        self.assertEqual(Confused.SIXTEEN._value_, 16)

    def test_aliases(self):
        Color = self.Color
        self.assertEqual(Color(1).name, 'RED')
        self.assertEqual(Color['ROJO'].name, 'RED')
        self.assertEqual(Color(7).name, 'WHITE')
        self.assertEqual(Color['BLANCO'].name, 'WHITE')
        self.assertIs(Color.BLANCO, Color.WHITE)
        Open = self.Open
        self.assertIs(Open['AC'], Open.AC)

    def test_auto_number(self):
        klasse Color(Flag):
            red = auto()
            blue = auto()
            green = auto()

        self.assertEqual(list(Color), [Color.red, Color.blue, Color.green])
        self.assertEqual(Color.red.value, 1)
        self.assertEqual(Color.blue.value, 2)
        self.assertEqual(Color.green.value, 4)

    def test_auto_number_garbage(self):
        with self.assertRaisesRegex(TypeError, 'invalid flag value .not an int.'):
            klasse Color(Flag):
                red = 'not an int'
                blue = auto()

    def test_duplicate_auto(self):
        klasse Dupes(Enum):
            first = primero = auto()
            second = auto()
            third = auto()
        self.assertEqual([Dupes.first, Dupes.second, Dupes.third], list(Dupes))

    def test_multiple_mixin(self):
        klasse AllMixin:
            @classproperty
            def ALL(cls):
                members = list(cls)
                all_value = Nichts
                wenn members:
                    all_value = members[0]
                    fuer member in members[1:]:
                        all_value |= member
                cls.ALL = all_value
                return all_value
        klasse StrMixin:
            def __str__(self):
                return self._name_.lower()
        klasse Color(AllMixin, Flag):
            RED = auto()
            GREEN = auto()
            BLUE = auto()
        self.assertEqual(Color.RED.value, 1)
        self.assertEqual(Color.GREEN.value, 2)
        self.assertEqual(Color.BLUE.value, 4)
        self.assertEqual(Color.ALL.value, 7)
        self.assertEqual(str(Color.BLUE), 'Color.BLUE')
        klasse Color(AllMixin, StrMixin, Flag):
            RED = auto()
            GREEN = auto()
            BLUE = auto()
            __str__ = StrMixin.__str__
        self.assertEqual(Color.RED.value, 1)
        self.assertEqual(Color.GREEN.value, 2)
        self.assertEqual(Color.BLUE.value, 4)
        self.assertEqual(Color.ALL.value, 7)
        self.assertEqual(str(Color.BLUE), 'blue')
        klasse Color(StrMixin, AllMixin, Flag):
            RED = auto()
            GREEN = auto()
            BLUE = auto()
            __str__ = StrMixin.__str__
        self.assertEqual(Color.RED.value, 1)
        self.assertEqual(Color.GREEN.value, 2)
        self.assertEqual(Color.BLUE.value, 4)
        self.assertEqual(Color.ALL.value, 7)
        self.assertEqual(str(Color.BLUE), 'blue')

    @threading_helper.reap_threads
    @threading_helper.requires_working_threading()
    def test_unique_composite(self):
        # override __eq__ to be identity only
        klasse TestFlag(Flag):
            one = auto()
            two = auto()
            three = auto()
            four = auto()
            five = auto()
            six = auto()
            seven = auto()
            eight = auto()
            def __eq__(self, other):
                return self is other
            def __hash__(self):
                return hash(self._value_)
        # have multiple threads competing to complete the composite members
        seen = set()
        failed = Falsch
        def cycle_enum():
            nonlocal failed
            try:
                fuer i in range(256):
                    seen.add(TestFlag(i))
            except Exception:
                failed = Wahr
        threads = [
                threading.Thread(target=cycle_enum)
                fuer _ in range(8)
                ]
        with threading_helper.start_threads(threads):
            pass
        # check that only 248 members were created
        self.assertFalsch(
                failed,
                'at least one thread failed while creating composite members')
        self.assertEqual(256, len(seen), 'too many composite members created')

    def test_init_subclass(self):
        klasse MyEnum(Flag):
            def __init_subclass__(cls, **kwds):
                super().__init_subclass__(**kwds)
                self.assertFalsch(cls.__dict__.get('_test', Falsch))
                cls._test1 = 'MyEnum'
        #
        klasse TheirEnum(MyEnum):
            def __init_subclass__(cls, **kwds):
                super(TheirEnum, cls).__init_subclass__(**kwds)
                cls._test2 = 'TheirEnum'
        klasse WhoseEnum(TheirEnum):
            def __init_subclass__(cls, **kwds):
                pass
        klasse NoEnum(WhoseEnum):
            ONE = 1
        self.assertEqual(TheirEnum.__dict__['_test1'], 'MyEnum')
        self.assertEqual(WhoseEnum.__dict__['_test1'], 'MyEnum')
        self.assertEqual(WhoseEnum.__dict__['_test2'], 'TheirEnum')
        self.assertFalsch(NoEnum.__dict__.get('_test1', Falsch))
        self.assertFalsch(NoEnum.__dict__.get('_test2', Falsch))
        #
        klasse OurEnum(MyEnum):
            def __init_subclass__(cls, **kwds):
                cls._test2 = 'OurEnum'
        klasse WhereEnum(OurEnum):
            def __init_subclass__(cls, **kwds):
                pass
        klasse NeverEnum(WhereEnum):
            ONE = 1
        self.assertEqual(OurEnum.__dict__['_test1'], 'MyEnum')
        self.assertFalsch(WhereEnum.__dict__.get('_test1', Falsch))
        self.assertEqual(WhereEnum.__dict__['_test2'], 'OurEnum')
        self.assertFalsch(NeverEnum.__dict__.get('_test1', Falsch))
        self.assertFalsch(NeverEnum.__dict__.get('_test2', Falsch))


klasse OldTestIntFlag(unittest.TestCase):
    """Tests of the IntFlags."""

    klasse Perm(IntFlag):
        R = 1 << 2
        W = 1 << 1
        X = 1 << 0

    klasse Open(IntFlag):
        RO = 0
        WO = 1
        RW = 2
        AC = 3
        CE = 1<<19

    klasse Color(IntFlag):
        BLACK = 0
        RED = 1
        ROJO = 1
        GREEN = 2
        BLUE = 4
        PURPLE = RED|BLUE
        WHITE = RED|GREEN|BLUE
        BLANCO = RED|GREEN|BLUE

    klasse Skip(IntFlag):
        FIRST = 1
        SECOND = 2
        EIGHTH = 8

    def test_type(self):
        Perm = self.Perm
        self.assertWahr(Perm._member_type_ is int)
        Open = self.Open
        fuer f in Perm:
            self.assertWahr(isinstance(f, Perm))
            self.assertEqual(f, f.value)
        self.assertWahr(isinstance(Perm.W | Perm.X, Perm))
        self.assertEqual(Perm.W | Perm.X, 3)
        fuer f in Open:
            self.assertWahr(isinstance(f, Open))
            self.assertEqual(f, f.value)
        self.assertWahr(isinstance(Open.WO | Open.RW, Open))
        self.assertEqual(Open.WO | Open.RW, 3)

    @reraise_if_not_enum(HeadlightsK)
    def test_global_repr_keep(self):
        self.assertEqual(
                repr(HeadlightsK(0)),
                '%s.OFF_K' % SHORT_MODULE,
                )
        self.assertEqual(
                repr(HeadlightsK(2**0 + 2**2 + 2**3)),
                '%(m)s.LOW_BEAM_K|%(m)s.FOG_K|8' % {'m': SHORT_MODULE},
                )
        self.assertEqual(
                repr(HeadlightsK(2**3)),
                '%(m)s.HeadlightsK(8)' % {'m': SHORT_MODULE},
                )

    @reraise_if_not_enum(HeadlightsC)
    def test_global_repr_conform1(self):
        self.assertEqual(
                repr(HeadlightsC(0)),
                '%s.OFF_C' % SHORT_MODULE,
                )
        self.assertEqual(
                repr(HeadlightsC(2**0 + 2**2 + 2**3)),
                '%(m)s.LOW_BEAM_C|%(m)s.FOG_C' % {'m': SHORT_MODULE},
                )
        self.assertEqual(
                repr(HeadlightsC(2**3)),
                '%(m)s.OFF_C' % {'m': SHORT_MODULE},
                )

    @reraise_if_not_enum(NoName)
    def test_global_enum_str(self):
        self.assertEqual(repr(NoName.ONE), 'test_enum.ONE')
        self.assertEqual(repr(NoName(0)), 'test_enum.NoName(0)')
        self.assertEqual(str(NoName.ONE & NoName.TWO), 'NoName(0)')
        self.assertEqual(str(NoName(0)), 'NoName(0)')

    def test_format(self):
        Perm = self.Perm
        self.assertEqual(format(Perm.R, ''), '4')
        self.assertEqual(format(Perm.R | Perm.X, ''), '5')
        #
        klasse NewPerm(IntFlag):
            R = 1 << 2
            W = 1 << 1
            X = 1 << 0
            def __str__(self):
                return self._name_
        self.assertEqual(format(NewPerm.R, ''), 'R')
        self.assertEqual(format(NewPerm.R | Perm.X, ''), 'R|X')

    def test_or(self):
        Perm = self.Perm
        fuer i in Perm:
            fuer j in Perm:
                self.assertEqual(i | j, i.value | j.value)
                self.assertEqual((i | j).value, i.value | j.value)
                self.assertIs(type(i | j), Perm)
            fuer j in range(8):
                self.assertEqual(i | j, i.value | j)
                self.assertEqual((i | j).value, i.value | j)
                self.assertIs(type(i | j), Perm)
                self.assertEqual(j | i, j | i.value)
                self.assertEqual((j | i).value, j | i.value)
                self.assertIs(type(j | i), Perm)
        fuer i in Perm:
            self.assertIs(i | i, i)
            self.assertIs(i | 0, i)
            self.assertIs(0 | i, i)
        Open = self.Open
        self.assertIs(Open.RO | Open.CE, Open.CE)

    def test_and(self):
        Perm = self.Perm
        RW = Perm.R | Perm.W
        RX = Perm.R | Perm.X
        WX = Perm.W | Perm.X
        RWX = Perm.R | Perm.W | Perm.X
        values = list(Perm) + [RW, RX, WX, RWX, Perm(0)]
        fuer i in values:
            fuer j in values:
                self.assertEqual(i & j, i.value & j.value, 'i is %r, j is %r' % (i, j))
                self.assertEqual((i & j).value, i.value & j.value, 'i is %r, j is %r' % (i, j))
                self.assertIs(type(i & j), Perm, 'i is %r, j is %r' % (i, j))
            fuer j in range(8):
                self.assertEqual(i & j, i.value & j)
                self.assertEqual((i & j).value, i.value & j)
                self.assertIs(type(i & j), Perm)
                self.assertEqual(j & i, j & i.value)
                self.assertEqual((j & i).value, j & i.value)
                self.assertIs(type(j & i), Perm)
        fuer i in Perm:
            self.assertIs(i & i, i)
            self.assertIs(i & 7, i)
            self.assertIs(7 & i, i)
        Open = self.Open
        self.assertIs(Open.RO & Open.CE, Open.RO)

    def test_xor(self):
        Perm = self.Perm
        fuer i in Perm:
            fuer j in Perm:
                self.assertEqual(i ^ j, i.value ^ j.value)
                self.assertEqual((i ^ j).value, i.value ^ j.value)
                self.assertIs(type(i ^ j), Perm)
            fuer j in range(8):
                self.assertEqual(i ^ j, i.value ^ j)
                self.assertEqual((i ^ j).value, i.value ^ j)
                self.assertIs(type(i ^ j), Perm)
                self.assertEqual(j ^ i, j ^ i.value)
                self.assertEqual((j ^ i).value, j ^ i.value)
                self.assertIs(type(j ^ i), Perm)
        fuer i in Perm:
            self.assertIs(i ^ 0, i)
            self.assertIs(0 ^ i, i)
        Open = self.Open
        self.assertIs(Open.RO ^ Open.CE, Open.CE)
        self.assertIs(Open.CE ^ Open.CE, Open.RO)

    def test_invert(self):
        Perm = self.Perm
        RW = Perm.R | Perm.W
        RX = Perm.R | Perm.X
        WX = Perm.W | Perm.X
        RWX = Perm.R | Perm.W | Perm.X
        values = list(Perm) + [RW, RX, WX, RWX, Perm(0)]
        fuer i in values:
            self.assertEqual(~i, (~i).value)
            self.assertIs(type(~i), Perm)
            self.assertEqual(~~i, i)
        fuer i in Perm:
            self.assertIs(~~i, i)
        Open = self.Open
        self.assertIs(Open.WO & ~Open.WO, Open.RO)
        self.assertIs((Open.WO|Open.CE) & ~Open.WO, Open.CE)

    def test_boundary(self):
        self.assertIs(enum.IntFlag._boundary_, KEEP)
        klasse Simple(IntFlag, boundary=KEEP):
            SINGLE = 1
        #
        klasse Iron(IntFlag, boundary=STRICT):
            ONE = 1
            TWO = 2
            EIGHT = 8
        self.assertIs(Iron._boundary_, STRICT)
        #
        klasse Water(IntFlag, boundary=CONFORM):
            ONE = 1
            TWO = 2
            EIGHT = 8
        self.assertIs(Water._boundary_, CONFORM)
        #
        klasse Space(IntFlag, boundary=EJECT):
            ONE = 1
            TWO = 2
            EIGHT = 8
        self.assertIs(Space._boundary_, EJECT)
        #
        klasse Bizarre(IntFlag, boundary=KEEP):
            b = 3
            c = 4
            d = 6
        #
        self.assertRaisesRegex(ValueError, 'invalid value 5', Iron, 5)
        #
        self.assertIs(Water(7), Water.ONE|Water.TWO)
        self.assertIs(Water(~9), Water.TWO)
        #
        self.assertEqual(Space(7), 7)
        self.assertWahr(type(Space(7)) is int)
        #
        self.assertEqual(list(Bizarre), [Bizarre.c])
        self.assertIs(Bizarre(3), Bizarre.b)
        self.assertIs(Bizarre(6), Bizarre.d)
        #
        simple = Simple.SINGLE | Iron.TWO
        self.assertEqual(simple, 3)
        self.assertIsInstance(simple, Simple)
        self.assertEqual(repr(simple), '<Simple.SINGLE|<Iron.TWO: 2>: 3>')
        self.assertEqual(str(simple), '3')

    def test_iter(self):
        Color = self.Color
        Open = self.Open
        self.assertEqual(list(Color), [Color.RED, Color.GREEN, Color.BLUE])
        self.assertEqual(list(Open), [Open.WO, Open.RW, Open.CE])

    def test_programatic_function_string(self):
        Perm = IntFlag('Perm', 'R W X')
        lst = list(Perm)
        self.assertEqual(len(lst), len(Perm))
        self.assertEqual(len(Perm), 3, Perm)
        self.assertEqual(lst, [Perm.R, Perm.W, Perm.X])
        fuer i, n in enumerate('R W X'.split()):
            v = 1<<i
            e = Perm(v)
            self.assertEqual(e.value, v)
            self.assertEqual(type(e.value), int)
            self.assertEqual(e, v)
            self.assertEqual(e.name, n)
            self.assertIn(e, Perm)
            self.assertIs(type(e), Perm)

    def test_programatic_function_string_with_start(self):
        Perm = IntFlag('Perm', 'R W X', start=8)
        lst = list(Perm)
        self.assertEqual(len(lst), len(Perm))
        self.assertEqual(len(Perm), 3, Perm)
        self.assertEqual(lst, [Perm.R, Perm.W, Perm.X])
        fuer i, n in enumerate('R W X'.split()):
            v = 8<<i
            e = Perm(v)
            self.assertEqual(e.value, v)
            self.assertEqual(type(e.value), int)
            self.assertEqual(e, v)
            self.assertEqual(e.name, n)
            self.assertIn(e, Perm)
            self.assertIs(type(e), Perm)

    def test_programatic_function_string_list(self):
        Perm = IntFlag('Perm', ['R', 'W', 'X'])
        lst = list(Perm)
        self.assertEqual(len(lst), len(Perm))
        self.assertEqual(len(Perm), 3, Perm)
        self.assertEqual(lst, [Perm.R, Perm.W, Perm.X])
        fuer i, n in enumerate('R W X'.split()):
            v = 1<<i
            e = Perm(v)
            self.assertEqual(e.value, v)
            self.assertEqual(type(e.value), int)
            self.assertEqual(e, v)
            self.assertEqual(e.name, n)
            self.assertIn(e, Perm)
            self.assertIs(type(e), Perm)

    def test_programatic_function_iterable(self):
        Perm = IntFlag('Perm', (('R', 2), ('W', 8), ('X', 32)))
        lst = list(Perm)
        self.assertEqual(len(lst), len(Perm))
        self.assertEqual(len(Perm), 3, Perm)
        self.assertEqual(lst, [Perm.R, Perm.W, Perm.X])
        fuer i, n in enumerate('R W X'.split()):
            v = 1<<(2*i+1)
            e = Perm(v)
            self.assertEqual(e.value, v)
            self.assertEqual(type(e.value), int)
            self.assertEqual(e, v)
            self.assertEqual(e.name, n)
            self.assertIn(e, Perm)
            self.assertIs(type(e), Perm)

    def test_programatic_function_from_dict(self):
        Perm = IntFlag('Perm', OrderedDict((('R', 2), ('W', 8), ('X', 32))))
        lst = list(Perm)
        self.assertEqual(len(lst), len(Perm))
        self.assertEqual(len(Perm), 3, Perm)
        self.assertEqual(lst, [Perm.R, Perm.W, Perm.X])
        fuer i, n in enumerate('R W X'.split()):
            v = 1<<(2*i+1)
            e = Perm(v)
            self.assertEqual(e.value, v)
            self.assertEqual(type(e.value), int)
            self.assertEqual(e, v)
            self.assertEqual(e.name, n)
            self.assertIn(e, Perm)
            self.assertIs(type(e), Perm)


    def test_programatic_function_from_empty_list(self):
        Perm = enum.IntFlag('Perm', [])
        lst = list(Perm)
        self.assertEqual(len(lst), len(Perm))
        self.assertEqual(len(Perm), 0, Perm)
        Thing = enum.Enum('Thing', [])
        lst = list(Thing)
        self.assertEqual(len(lst), len(Thing))
        self.assertEqual(len(Thing), 0, Thing)


    def test_programatic_function_from_empty_tuple(self):
        Perm = enum.IntFlag('Perm', ())
        lst = list(Perm)
        self.assertEqual(len(lst), len(Perm))
        self.assertEqual(len(Perm), 0, Perm)
        Thing = enum.Enum('Thing', ())
        self.assertEqual(len(lst), len(Thing))
        self.assertEqual(len(Thing), 0, Thing)

    def test_contains_tf(self):
        Open = self.Open
        Color = self.Color
        self.assertWahr(Color.GREEN in Color)
        self.assertWahr(Open.RW in Open)
        self.assertFalsch('GREEN' in Color)
        self.assertFalsch('RW' in Open)
        self.assertWahr(2 in Color)
        self.assertWahr(2 in Open)

    def test_member_contains(self):
        Perm = self.Perm
        R, W, X = Perm
        RW = R | W
        RX = R | X
        WX = W | X
        RWX = R | W | X
        self.assertWahr(R in RW)
        self.assertWahr(R in RX)
        self.assertWahr(R in RWX)
        self.assertWahr(W in RW)
        self.assertWahr(W in WX)
        self.assertWahr(W in RWX)
        self.assertWahr(X in RX)
        self.assertWahr(X in WX)
        self.assertWahr(X in RWX)
        self.assertFalsch(R in WX)
        self.assertFalsch(W in RX)
        self.assertFalsch(X in RW)
        with self.assertRaises(TypeError):
            self.assertFalsch('test' in RW)

    def test_member_iter(self):
        Color = self.Color
        self.assertEqual(list(Color.BLACK), [])
        self.assertEqual(list(Color.PURPLE), [Color.RED, Color.BLUE])
        self.assertEqual(list(Color.BLUE), [Color.BLUE])
        self.assertEqual(list(Color.GREEN), [Color.GREEN])
        self.assertEqual(list(Color.WHITE), [Color.RED, Color.GREEN, Color.BLUE])

    def test_member_length(self):
        self.assertEqual(self.Color.__len__(self.Color.BLACK), 0)
        self.assertEqual(self.Color.__len__(self.Color.GREEN), 1)
        self.assertEqual(self.Color.__len__(self.Color.PURPLE), 2)
        self.assertEqual(self.Color.__len__(self.Color.BLANCO), 3)

    def test_aliases(self):
        Color = self.Color
        self.assertEqual(Color(1).name, 'RED')
        self.assertEqual(Color['ROJO'].name, 'RED')
        self.assertEqual(Color(7).name, 'WHITE')
        self.assertEqual(Color['BLANCO'].name, 'WHITE')
        self.assertIs(Color.BLANCO, Color.WHITE)
        Open = self.Open
        self.assertIs(Open['AC'], Open.AC)

    def test_bool(self):
        Perm = self.Perm
        fuer f in Perm:
            self.assertWahr(f)
        Open = self.Open
        fuer f in Open:
            self.assertEqual(bool(f.value), bool(f))


    def test_multiple_mixin(self):
        klasse AllMixin:
            @classproperty
            def ALL(cls):
                members = list(cls)
                all_value = Nichts
                wenn members:
                    all_value = members[0]
                    fuer member in members[1:]:
                        all_value |= member
                cls.ALL = all_value
                return all_value
        klasse StrMixin:
            def __str__(self):
                return self._name_.lower()
        klasse Color(AllMixin, IntFlag):
            RED = auto()
            GREEN = auto()
            BLUE = auto()
        self.assertEqual(Color.RED.value, 1)
        self.assertEqual(Color.GREEN.value, 2)
        self.assertEqual(Color.BLUE.value, 4)
        self.assertEqual(Color.ALL.value, 7)
        self.assertEqual(str(Color.BLUE), '4')
        klasse Color(AllMixin, StrMixin, IntFlag):
            RED = auto()
            GREEN = auto()
            BLUE = auto()
            __str__ = StrMixin.__str__
        self.assertEqual(Color.RED.value, 1)
        self.assertEqual(Color.GREEN.value, 2)
        self.assertEqual(Color.BLUE.value, 4)
        self.assertEqual(Color.ALL.value, 7)
        self.assertEqual(str(Color.BLUE), 'blue')
        klasse Color(StrMixin, AllMixin, IntFlag):
            RED = auto()
            GREEN = auto()
            BLUE = auto()
            __str__ = StrMixin.__str__
        self.assertEqual(Color.RED.value, 1)
        self.assertEqual(Color.GREEN.value, 2)
        self.assertEqual(Color.BLUE.value, 4)
        self.assertEqual(Color.ALL.value, 7)
        self.assertEqual(str(Color.BLUE), 'blue')

    @threading_helper.reap_threads
    @threading_helper.requires_working_threading()
    def test_unique_composite(self):
        # override __eq__ to be identity only
        klasse TestFlag(IntFlag):
            one = auto()
            two = auto()
            three = auto()
            four = auto()
            five = auto()
            six = auto()
            seven = auto()
            eight = auto()
            def __eq__(self, other):
                return self is other
            def __hash__(self):
                return hash(self._value_)
        # have multiple threads competing to complete the composite members
        seen = set()
        failed = Falsch
        def cycle_enum():
            nonlocal failed
            try:
                fuer i in range(256):
                    seen.add(TestFlag(i))
            except Exception:
                failed = Wahr
        threads = [
                threading.Thread(target=cycle_enum)
                fuer _ in range(8)
                ]
        with threading_helper.start_threads(threads):
            pass
        # check that only 248 members were created
        self.assertFalsch(
                failed,
                'at least one thread failed while creating composite members')
        self.assertEqual(256, len(seen), 'too many composite members created')


klasse TestEmptyAndNonLatinStrings(unittest.TestCase):

    def test_empty_string(self):
        with self.assertRaises(ValueError):
            empty_abc = Enum('empty_abc', ('', 'B', 'C'))

    def test_non_latin_character_string(self):
        greek_abc = Enum('greek_abc', ('\u03B1', 'B', 'C'))
        item = getattr(greek_abc, '\u03B1')
        self.assertEqual(item.value, 1)

    def test_non_latin_number_string(self):
        hebrew_123 = Enum('hebrew_123', ('\u05D0', '2', '3'))
        item = getattr(hebrew_123, '\u05D0')
        self.assertEqual(item.value, 1)


klasse TestUnique(unittest.TestCase):

    def test_unique_clean(self):
        @unique
        klasse Clean(Enum):
            one = 1
            two = 'dos'
            tres = 4.0
        #
        @unique
        klasse Cleaner(IntEnum):
            single = 1
            double = 2
            triple = 3

    def test_unique_dirty(self):
        with self.assertRaisesRegex(ValueError, 'tres.*one'):
            @unique
            klasse Dirty(Enum):
                one = 1
                two = 'dos'
                tres = 1
        with self.assertRaisesRegex(
                ValueError,
                'double.*single.*turkey.*triple',
                ):
            @unique
            klasse Dirtier(IntEnum):
                single = 1
                double = 1
                triple = 3
                turkey = 3

    def test_unique_with_name(self):
        @verify(UNIQUE)
        klasse Silly(Enum):
            one = 1
            two = 'dos'
            name = 3
        #
        @verify(UNIQUE)
        klasse Sillier(IntEnum):
            single = 1
            name = 2
            triple = 3
            value = 4

klasse TestVerify(unittest.TestCase):

    def test_continuous(self):
        @verify(CONTINUOUS)
        klasse Auto(Enum):
            FIRST = auto()
            SECOND = auto()
            THIRD = auto()
            FORTH = auto()
        #
        @verify(CONTINUOUS)
        klasse Manual(Enum):
            FIRST = 3
            SECOND = 4
            THIRD = 5
            FORTH = 6
        #
        with self.assertRaisesRegex(ValueError, 'invalid enum .Missing.: missing values 5, 6, 7, 8, 9, 10, 12'):
            @verify(CONTINUOUS)
            klasse Missing(Enum):
                FIRST = 3
                SECOND = 4
                THIRD = 11
                FORTH = 13
        #
        with self.assertRaisesRegex(ValueError, 'invalid flag .Incomplete.: missing values 32'):
            @verify(CONTINUOUS)
            klasse Incomplete(Flag):
                FIRST = 4
                SECOND = 8
                THIRD = 16
                FORTH = 64
        #
        with self.assertRaisesRegex(ValueError, 'invalid flag .StillIncomplete.: missing values 16'):
            @verify(CONTINUOUS)
            klasse StillIncomplete(Flag):
                FIRST = 4
                SECOND = 8
                THIRD = 11
                FORTH = 32


    def test_composite(self):
        klasse Bizarre(Flag):
            b = 3
            c = 4
            d = 6
        self.assertEqual(list(Bizarre), [Bizarre.c])
        self.assertEqual(Bizarre.b.value, 3)
        self.assertEqual(Bizarre.c.value, 4)
        self.assertEqual(Bizarre.d.value, 6)
        with self.assertRaisesRegex(
                ValueError,
                "invalid Flag 'Bizarre': aliases b and d are missing combined values of 0x3 .use enum.show_flag_values.value. fuer details.",
            ):
            @verify(NAMED_FLAGS)
            klasse Bizarre(Flag):
                b = 3
                c = 4
                d = 6
        #
        self.assertEqual(enum.show_flag_values(3), [1, 2])
        klasse Bizarre(IntFlag):
            b = 3
            c = 4
            d = 6
        self.assertEqual(list(Bizarre), [Bizarre.c])
        self.assertEqual(Bizarre.b.value, 3)
        self.assertEqual(Bizarre.c.value, 4)
        self.assertEqual(Bizarre.d.value, 6)
        with self.assertRaisesRegex(
                ValueError,
                "invalid Flag 'Bizarre': alias d is missing value 0x2 .use enum.show_flag_values.value. fuer details.",
            ):
            @verify(NAMED_FLAGS)
            klasse Bizarre(IntFlag):
                c = 4
                d = 6
        self.assertEqual(enum.show_flag_values(2), [2])

    def test_unique_clean(self):
        @verify(UNIQUE)
        klasse Clean(Enum):
            one = 1
            two = 'dos'
            tres = 4.0
        #
        @verify(UNIQUE)
        klasse Cleaner(IntEnum):
            single = 1
            double = 2
            triple = 3

    def test_unique_dirty(self):
        with self.assertRaisesRegex(ValueError, 'tres.*one'):
            @verify(UNIQUE)
            klasse Dirty(Enum):
                one = 1
                two = 'dos'
                tres = 1
        with self.assertRaisesRegex(
                ValueError,
                'double.*single.*turkey.*triple',
                ):
            @verify(UNIQUE)
            klasse Dirtier(IntEnum):
                single = 1
                double = 1
                triple = 3
                turkey = 3

    def test_unique_with_name(self):
        @verify(UNIQUE)
        klasse Silly(Enum):
            one = 1
            two = 'dos'
            name = 3
        #
        @verify(UNIQUE)
        klasse Sillier(IntEnum):
            single = 1
            name = 2
            triple = 3
            value = 4

    def test_negative_alias(self):
        @verify(NAMED_FLAGS)
        klasse Color(Flag):
            RED = 1
            GREEN = 2
            BLUE = 4
            WHITE = -1
        # no error means success
        self.assertEqual(list(Color.WHITE), [Color.RED, Color.GREEN, Color.BLUE])
        self.assertEqual(Color.WHITE.value, 7)


klasse TestInternals(unittest.TestCase):

    sunder_names = '_bad_', '_good_', '_what_ho_'
    dunder_names = '__mal__', '__bien__', '__que_que__'
    private_names = '_MyEnum__private', '_MyEnum__still_private'
    private_and_sunder_names = '_MyEnum__private_', '_MyEnum__also_private_'
    random_names = 'okay', '_semi_private', '_weird__', '_MyEnum__'

    def test_sunder(self):
        fuer name in self.sunder_names + self.private_and_sunder_names:
            self.assertWahr(enum._is_sunder(name), '%r is a not sunder name?' % name)
        fuer name in self.dunder_names + self.private_names + self.random_names:
            self.assertFalsch(enum._is_sunder(name), '%r is a sunder name?' % name)

    def test_dunder(self):
        fuer name in self.dunder_names:
            self.assertWahr(enum._is_dunder(name), '%r is a not dunder name?' % name)
        fuer name in self.sunder_names + self.private_names + self.private_and_sunder_names + self.random_names:
            self.assertFalsch(enum._is_dunder(name), '%r is a dunder name?' % name)

    def test_is_private(self):
        fuer name in self.private_names + self.private_and_sunder_names:
            self.assertWahr(enum._is_private('MyEnum', name), '%r is a not private name?')
        fuer name in self.sunder_names + self.dunder_names + self.random_names:
            self.assertFalsch(enum._is_private('MyEnum', name), '%r is a private name?')

    def test_auto_number(self):
        klasse Color(Enum):
            red = auto()
            blue = auto()
            green = auto()

        self.assertEqual(list(Color), [Color.red, Color.blue, Color.green])
        self.assertEqual(Color.red.value, 1)
        self.assertEqual(Color.blue.value, 2)
        self.assertEqual(Color.green.value, 3)

    def test_auto_name(self):
        klasse Color(Enum):
            def _generate_next_value_(name, start, count, last):
                return name
            red = auto()
            blue = auto()
            green = auto()

        self.assertEqual(list(Color), [Color.red, Color.blue, Color.green])
        self.assertEqual(Color.red.value, 'red')
        self.assertEqual(Color.blue.value, 'blue')
        self.assertEqual(Color.green.value, 'green')

    def test_auto_name_inherit(self):
        klasse AutoNameEnum(Enum):
            def _generate_next_value_(name, start, count, last):
                return name
        klasse Color(AutoNameEnum):
            red = auto()
            blue = auto()
            green = auto()

        self.assertEqual(list(Color), [Color.red, Color.blue, Color.green])
        self.assertEqual(Color.red.value, 'red')
        self.assertEqual(Color.blue.value, 'blue')
        self.assertEqual(Color.green.value, 'green')

    @unittest.skipIf(
            python_version >= (3, 13),
            'mixed types with auto() no longer supported',
            )
    def test_auto_garbage_ok(self):
        with self.assertWarnsRegex(DeprecationWarning, 'will require all values to be sortable'):
            klasse Color(Enum):
                red = 'red'
                blue = auto()
        self.assertEqual(Color.blue.value, 1)

    @unittest.skipIf(
            python_version >= (3, 13),
            'mixed types with auto() no longer supported',
            )
    def test_auto_garbage_corrected_ok(self):
        with self.assertWarnsRegex(DeprecationWarning, 'will require all values to be sortable'):
            klasse Color(Enum):
                red = 'red'
                blue = 2
                green = auto()

        self.assertEqual(list(Color), [Color.red, Color.blue, Color.green])
        self.assertEqual(Color.red.value, 'red')
        self.assertEqual(Color.blue.value, 2)
        self.assertEqual(Color.green.value, 3)

    @unittest.skipIf(
            python_version < (3, 13),
            'mixed types with auto() will raise in 3.13',
            )
    def test_auto_garbage_fail(self):
        with self.assertRaisesRegex(TypeError, "unable to increment 'red'"):
            klasse Color(Enum):
                red = 'red'
                blue = auto()

    @unittest.skipIf(
            python_version < (3, 13),
            'mixed types with auto() will raise in 3.13',
            )
    def test_auto_garbage_corrected_fail(self):
        with self.assertRaisesRegex(TypeError, 'unable to sort non-numeric values'):
            klasse Color(Enum):
                red = 'red'
                blue = 2
                green = auto()

    def test_auto_order(self):
        with self.assertRaises(TypeError):
            klasse Color(Enum):
                red = auto()
                green = auto()
                blue = auto()
                def _generate_next_value_(name, start, count, last):
                    return name

    def test_auto_order_wierd(self):
        weird_auto = auto()
        weird_auto.value = 'pathological case'
        klasse Color(Enum):
            red = weird_auto
            def _generate_next_value_(name, start, count, last):
                return name
            blue = auto()
        self.assertEqual(list(Color), [Color.red, Color.blue])
        self.assertEqual(Color.red.value, 'pathological case')
        self.assertEqual(Color.blue.value, 'blue')

    @unittest.skipIf(
            python_version < (3, 13),
            'auto() will return highest value + 1 in 3.13',
            )
    def test_auto_with_aliases(self):
        klasse Color(Enum):
            red = auto()
            blue = auto()
            oxford = blue
            crimson = red
            green = auto()
        self.assertIs(Color.crimson, Color.red)
        self.assertIs(Color.oxford, Color.blue)
        self.assertIsNot(Color.green, Color.red)
        self.assertIsNot(Color.green, Color.blue)

    def test_duplicate_auto(self):
        klasse Dupes(Enum):
            first = primero = auto()
            second = auto()
            third = auto()
        self.assertEqual([Dupes.first, Dupes.second, Dupes.third], list(Dupes))

    def test_multiple_auto_on_line(self):
        klasse Huh(Enum):
            ONE = auto()
            TWO = auto(), auto()
            THREE = auto(), auto(), auto()
        self.assertEqual(Huh.ONE.value, 1)
        self.assertEqual(Huh.TWO.value, (2, 3))
        self.assertEqual(Huh.THREE.value, (4, 5, 6))
        #
        klasse Hah(Enum):
            def __new__(cls, value, abbr=Nichts):
                member = object.__new__(cls)
                member._value_ = value
                member.abbr = abbr or value[:3].lower()
                return member
            def _generate_next_value_(name, start, count, last):
                return name
            #
            MONDAY = auto()
            TUESDAY = auto()
            WEDNESDAY = auto(), 'WED'
            THURSDAY = auto(), 'Thu'
            FRIDAY = auto()
        self.assertEqual(Hah.MONDAY.value, 'MONDAY')
        self.assertEqual(Hah.MONDAY.abbr, 'mon')
        self.assertEqual(Hah.TUESDAY.value, 'TUESDAY')
        self.assertEqual(Hah.TUESDAY.abbr, 'tue')
        self.assertEqual(Hah.WEDNESDAY.value, 'WEDNESDAY')
        self.assertEqual(Hah.WEDNESDAY.abbr, 'WED')
        self.assertEqual(Hah.THURSDAY.value, 'THURSDAY')
        self.assertEqual(Hah.THURSDAY.abbr, 'Thu')
        self.assertEqual(Hah.FRIDAY.value, 'FRIDAY')
        self.assertEqual(Hah.FRIDAY.abbr, 'fri')
        #
        klasse Huh(Enum):
            def _generate_next_value_(name, start, count, last):
                return count+1
            ONE = auto()
            TWO = auto(), auto()
            THREE = auto(), auto(), auto()
        self.assertEqual(Huh.ONE.value, 1)
        self.assertEqual(Huh.TWO.value, (2, 2))
        self.assertEqual(Huh.THREE.value, (3, 3, 3))


expected_help_output_with_docs = """\
Help on klasse Color in module %s:

klasse Color(enum.Enum)
 |  Color(*values)
 |
 |  Method resolution order:
 |      Color
 |      enum.Enum
 |      builtins.object
 |
 |  Data and other attributes defined here:
 |
 |  CYAN = <Color.CYAN: 1>
 |
 |  MAGENTA = <Color.MAGENTA: 2>
 |
 |  YELLOW = <Color.YELLOW: 3>
 |
 |  ----------------------------------------------------------------------
 |  Data descriptors inherited from enum.Enum:
 |
 |  name
 |      The name of the Enum member.
 |
 |  value
 |      The value of the Enum member.
 |
 |  ----------------------------------------------------------------------
 |  Static methods inherited from enum.EnumType:
 |
 |  __contains__(value)
 |      Return Wahr wenn `value` is in `cls`.
 |
 |      `value` is in `cls` if:
 |      1) `value` is a member of `cls`, or
 |      2) `value` is the value of one of the `cls`'s members.
 |      3) `value` is a pseudo-member (flags)
 |
 |  __getitem__(name)
 |      Return the member matching `name`.
 |
 |  __iter__()
 |      Return members in definition order.
 |
 |  __len__()
 |      Return the number of members (no aliases)
 |
 |  ----------------------------------------------------------------------
 |  Readonly properties inherited from enum.EnumType:
 |
 |  __members__
 |      Returns a mapping of member name->value.
 |
 |      This mapping lists all enum members, including aliases. Note that this
 |      is a read-only view of the internal mapping."""

expected_help_output_without_docs = """\
Help on klasse Color in module %s:

klasse Color(enum.Enum)
 |  Color(*values)
 |
 |  Method resolution order:
 |      Color
 |      enum.Enum
 |      builtins.object
 |
 |  Data and other attributes defined here:
 |
 |  CYAN = <Color.CYAN: 1>
 |
 |  MAGENTA = <Color.MAGENTA: 2>
 |
 |  YELLOW = <Color.YELLOW: 3>
 |
 |  ----------------------------------------------------------------------
 |  Data descriptors inherited from enum.Enum:
 |
 |  name
 |
 |  value
 |
 |  ----------------------------------------------------------------------
 |  Static methods inherited from enum.EnumType:
 |
 |  __contains__(value)
 |
 |  __getitem__(name)
 |
 |  __iter__()
 |
 |  __len__()
 |
 |  ----------------------------------------------------------------------
 |  Readonly properties inherited from enum.EnumType:
 |
 |  __members__"""

klasse TestStdLib(unittest.TestCase):

    maxDiff = Nichts

    klasse Color(Enum):
        CYAN = 1
        MAGENTA = 2
        YELLOW = 3

    def test_pydoc(self):
        # indirectly test __objclass__
        wenn StrEnum.__doc__ is Nichts:
            expected_text = expected_help_output_without_docs % __name__
        sonst:
            expected_text = expected_help_output_with_docs % __name__
        output = StringIO()
        helper = pydoc.Helper(output=output)
        helper(self.Color)
        result = output.getvalue().strip()
        self.assertEqual(result, expected_text, result)

    def test_inspect_getmembers(self):
        values = dict((
                ('__class__', EnumType),
                ('__doc__', '...'),
                ('__members__', self.Color.__members__),
                ('__module__', __name__),
                ('YELLOW', self.Color.YELLOW),
                ('MAGENTA', self.Color.MAGENTA),
                ('CYAN', self.Color.CYAN),
                ('name', Enum.__dict__['name']),
                ('value', Enum.__dict__['value']),
                ('__len__', self.Color.__len__),
                ('__contains__', self.Color.__contains__),
                ('__name__', 'Color'),
                ('__getitem__', self.Color.__getitem__),
                ('__qualname__', 'TestStdLib.Color'),
                ('__init_subclass__', getattr(self.Color, '__init_subclass__')),
                ('__iter__', self.Color.__iter__),
                ))
        result = dict(inspect.getmembers(self.Color))
        self.assertEqual(set(values.keys()), set(result.keys()))
        failed = Falsch
        fuer k in values.keys():
            wenn k == '__doc__':
                # __doc__ is huge, not comparing
                continue
            wenn result[k] != values[k]:
                drucke()
                drucke('\n%s\n     key: %s\n  result: %s\nexpected: %s\n%s\n' %
                        ('=' * 75, k, result[k], values[k], '=' * 75), sep='')
                failed = Wahr
        wenn failed:
            self.fail("result does not equal expected, see print above")

    def test_inspect_classify_class_attrs(self):
        # indirectly test __objclass__
        from inspect import Attribute
        values = [
                Attribute(name='__class__', kind='data',
                    defining_class=object, object=EnumType),
                Attribute(name='__contains__', kind='method',
                    defining_class=EnumType, object=self.Color.__contains__),
                Attribute(name='__doc__', kind='data',
                    defining_class=self.Color, object='...'),
                Attribute(name='__getitem__', kind='method',
                    defining_class=EnumType, object=self.Color.__getitem__),
                Attribute(name='__iter__', kind='method',
                    defining_class=EnumType, object=self.Color.__iter__),
                Attribute(name='__init_subclass__', kind='class method',
                    defining_class=object, object=getattr(self.Color, '__init_subclass__')),
                Attribute(name='__len__', kind='method',
                    defining_class=EnumType, object=self.Color.__len__),
                Attribute(name='__members__', kind='property',
                    defining_class=EnumType, object=EnumType.__members__),
                Attribute(name='__module__', kind='data',
                    defining_class=self.Color, object=__name__),
                Attribute(name='__name__', kind='data',
                    defining_class=self.Color, object='Color'),
                Attribute(name='__qualname__', kind='data',
                    defining_class=self.Color, object='TestStdLib.Color'),
                Attribute(name='YELLOW', kind='data',
                    defining_class=self.Color, object=self.Color.YELLOW),
                Attribute(name='MAGENTA', kind='data',
                    defining_class=self.Color, object=self.Color.MAGENTA),
                Attribute(name='CYAN', kind='data',
                    defining_class=self.Color, object=self.Color.CYAN),
                Attribute(name='name', kind='data',
                    defining_class=Enum, object=Enum.__dict__['name']),
                Attribute(name='value', kind='data',
                    defining_class=Enum, object=Enum.__dict__['value']),
                ]
        fuer v in values:
            try:
                v.name
            except AttributeError:
                drucke(v)
        values.sort(key=lambda item: item.name)
        result = list(inspect.classify_class_attrs(self.Color))
        result.sort(key=lambda item: item.name)
        self.assertEqual(
                len(values), len(result),
                "%s != %s" % ([a.name fuer a in values], [a.name fuer a in result])
                )
        failed = Falsch
        fuer v, r in zip(values, result):
            wenn r.name in ('__init_subclass__', '__doc__'):
                # not sure how to make the __init_subclass_ Attributes match
                # so as long as there is one, call it good
                # __doc__ is too big to check exactly, so treat the same as __init_subclass__
                fuer name in ('name','kind','defining_class'):
                    wenn getattr(v, name) != getattr(r, name):
                        drucke('\n%s\n%s\n%s\n%s\n' % ('=' * 75, r, v, '=' * 75), sep='')
                        failed = Wahr
            sowenn r != v:
                drucke('\n%s\n%s\n%s\n%s\n' % ('=' * 75, r, v, '=' * 75), sep='')
                failed = Wahr
        wenn failed:
            self.fail("result does not equal expected, see print above")

    def test_inspect_signatures(self):
        from inspect import signature, Signature, Parameter
        self.assertEqual(
                signature(Enum),
                Signature([
                    Parameter('new_class_name', Parameter.POSITIONAL_ONLY),
                    Parameter('names', Parameter.POSITIONAL_OR_KEYWORD),
                    Parameter('module', Parameter.KEYWORD_ONLY, default=Nichts),
                    Parameter('qualname', Parameter.KEYWORD_ONLY, default=Nichts),
                    Parameter('type', Parameter.KEYWORD_ONLY, default=Nichts),
                    Parameter('start', Parameter.KEYWORD_ONLY, default=1),
                    Parameter('boundary', Parameter.KEYWORD_ONLY, default=Nichts),
                    ]),
                )
        self.assertEqual(
                signature(enum.FlagBoundary),
                Signature([
                    Parameter('values', Parameter.VAR_POSITIONAL),
                    ]),
                )

    def test_test_simple_enum(self):
        @_simple_enum(Enum)
        klasse SimpleColor:
            CYAN = 1
            MAGENTA = 2
            YELLOW = 3
            @bltns.property
            def zeroth(self):
                return 'zeroed %s' % self.name
        klasse CheckedColor(Enum):
            CYAN = 1
            MAGENTA = 2
            YELLOW = 3
            @bltns.property
            def zeroth(self):
                return 'zeroed %s' % self.name
        _test_simple_enum(CheckedColor, SimpleColor)
        SimpleColor.MAGENTA._value_ = 9
        self.assertRaisesRegex(
                TypeError, "enum mismatch",
                _test_simple_enum, CheckedColor, SimpleColor,
                )
        #
        #
        klasse CheckedMissing(IntFlag, boundary=KEEP):
            SIXTY_FOUR = 64
            ONE_TWENTY_EIGHT = 128
            TWENTY_FORTY_EIGHT = 2048
            ALL = 2048 + 128 + 64 + 12
        CM = CheckedMissing
        self.assertEqual(list(CheckedMissing), [CM.SIXTY_FOUR, CM.ONE_TWENTY_EIGHT, CM.TWENTY_FORTY_EIGHT])
        #
        @_simple_enum(IntFlag, boundary=KEEP)
        klasse Missing:
            SIXTY_FOUR = 64
            ONE_TWENTY_EIGHT = 128
            TWENTY_FORTY_EIGHT = 2048
            ALL = 2048 + 128 + 64 + 12
        M = Missing
        self.assertEqual(list(CheckedMissing), [M.SIXTY_FOUR, M.ONE_TWENTY_EIGHT, M.TWENTY_FORTY_EIGHT])
        _test_simple_enum(CheckedMissing, Missing)
        #
        #
        klasse CheckedUnhashable(Enum):
            ONE = dict()
            TWO = set()
            name = 'python'
        self.assertIn(dict(), CheckedUnhashable)
        self.assertIn('python', CheckedUnhashable)
        self.assertEqual(CheckedUnhashable.name.value, 'python')
        self.assertEqual(CheckedUnhashable.name.name, 'name')
        #
        @_simple_enum()
        klasse Unhashable:
            ONE = dict()
            TWO = set()
            name = 'python'
        self.assertIn(dict(), Unhashable)
        self.assertIn('python', Unhashable)
        self.assertEqual(Unhashable.name.value, 'python')
        self.assertEqual(Unhashable.name.name, 'name')
        _test_simple_enum(CheckedUnhashable, Unhashable)
        ##
        klasse CheckedComplexStatus(IntEnum):
            def __new__(cls, value, phrase, description=''):
                obj = int.__new__(cls, value)
                obj._value_ = value
                obj.phrase = phrase
                obj.description = description
                return obj
            CONTINUE = 100, 'Continue', 'Request received, please continue'
            PROCESSING = 102, 'Processing'
            EARLY_HINTS = 103, 'Early Hints'
            SOME_HINTS = 103, 'Some Early Hints'
        #
        @_simple_enum(IntEnum)
        klasse ComplexStatus:
            def __new__(cls, value, phrase, description=''):
                obj = int.__new__(cls, value)
                obj._value_ = value
                obj.phrase = phrase
                obj.description = description
                return obj
            CONTINUE = 100, 'Continue', 'Request received, please continue'
            PROCESSING = 102, 'Processing'
            EARLY_HINTS = 103, 'Early Hints'
            SOME_HINTS = 103, 'Some Early Hints'
        _test_simple_enum(CheckedComplexStatus, ComplexStatus)
        #
        #
        klasse CheckedComplexFlag(IntFlag):
            def __new__(cls, value, label):
                obj = int.__new__(cls, value)
                obj._value_ = value
                obj.label = label
                return obj
            SHIRT = 1, 'upper half'
            VEST = 1, 'outer upper half'
            PANTS = 2, 'lower half'
        self.assertIs(CheckedComplexFlag.SHIRT, CheckedComplexFlag.VEST)
        #
        @_simple_enum(IntFlag)
        klasse ComplexFlag:
            def __new__(cls, value, label):
                obj = int.__new__(cls, value)
                obj._value_ = value
                obj.label = label
                return obj
            SHIRT = 1, 'upper half'
            VEST = 1, 'uppert half'
            PANTS = 2, 'lower half'
        _test_simple_enum(CheckedComplexFlag, ComplexFlag)


klasse MiscTestCase(unittest.TestCase):

    def test__all__(self):
        support.check__all__(self, enum, not_exported={'bin', 'show_flag_values'})

    @cpython_only
    def test_lazy_import(self):
        ensure_lazy_imports("enum", {"functools", "warnings", "inspect", "re"})

    def test_doc_1(self):
        klasse Single(Enum):
            ONE = 1
        self.assertEqual(Single.__doc__, Nichts)

    def test_doc_2(self):
        klasse Double(Enum):
            ONE = 1
            TWO = 2
        self.assertEqual(Double.__doc__, Nichts)

    def test_doc_3(self):
        klasse Triple(Enum):
            ONE = 1
            TWO = 2
            THREE = 3
        self.assertEqual(Triple.__doc__, Nichts)

    def test_doc_4(self):
        klasse Quadruple(Enum):
            ONE = 1
            TWO = 2
            THREE = 3
            FOUR = 4
        self.assertEqual(Quadruple.__doc__, Nichts)


# These are unordered here on purpose to ensure that declaration order
# makes no difference.
CONVERT_TEST_NAME_D = 5
CONVERT_TEST_NAME_C = 5
CONVERT_TEST_NAME_B = 5
CONVERT_TEST_NAME_A = 5  # This one should sort first.
CONVERT_TEST_NAME_E = 5
CONVERT_TEST_NAME_F = 5

CONVERT_STRING_TEST_NAME_D = 5
CONVERT_STRING_TEST_NAME_C = 5
CONVERT_STRING_TEST_NAME_B = 5
CONVERT_STRING_TEST_NAME_A = 5  # This one should sort first.
CONVERT_STRING_TEST_NAME_E = 5
CONVERT_STRING_TEST_NAME_F = 5

# global names fuer StrEnum._convert_ test
CONVERT_STR_TEST_2 = 'goodbye'
CONVERT_STR_TEST_1 = 'hello'

# We also need values that cannot be compared:
UNCOMPARABLE_A = 5
UNCOMPARABLE_C = (9, 1)  # naming order is broken on purpose
UNCOMPARABLE_B = 'value'

COMPLEX_C = 1j
COMPLEX_A = 2j
COMPLEX_B = 3j

klasse TestConvert(unittest.TestCase):
    def tearDown(self):
        # Reset the module-level test variables to their original integer
        # values, otherwise the already created enum values get converted
        # instead.
        g = globals()
        fuer suffix in ['A', 'B', 'C', 'D', 'E', 'F']:
            g['CONVERT_TEST_NAME_%s' % suffix] = 5
            g['CONVERT_STRING_TEST_NAME_%s' % suffix] = 5
        fuer suffix, value in (('A', 5), ('B', (9, 1)), ('C', 'value')):
            g['UNCOMPARABLE_%s' % suffix] = value
        fuer suffix, value in (('A', 2j), ('B', 3j), ('C', 1j)):
            g['COMPLEX_%s' % suffix] = value
        fuer suffix, value in (('1', 'hello'), ('2', 'goodbye')):
            g['CONVERT_STR_TEST_%s' % suffix] = value

    def test_convert_value_lookup_priority(self):
        test_type = enum.IntEnum._convert_(
                'UnittestConvert',
                MODULE,
                filter=lambda x: x.startswith('CONVERT_TEST_'))
        # We don't want the reverse lookup value to vary when there are
        # multiple possible names fuer a given value.  It should always
        # report the first lexicographical name in that case.
        self.assertEqual(test_type(5).name, 'CONVERT_TEST_NAME_A')

    def test_convert_int(self):
        test_type = enum.IntEnum._convert_(
                'UnittestConvert',
                MODULE,
                filter=lambda x: x.startswith('CONVERT_TEST_'))
        # Ensure that test_type has all of the desired names and values.
        self.assertEqual(test_type.CONVERT_TEST_NAME_F,
                         test_type.CONVERT_TEST_NAME_A)
        self.assertEqual(test_type.CONVERT_TEST_NAME_B, 5)
        self.assertEqual(test_type.CONVERT_TEST_NAME_C, 5)
        self.assertEqual(test_type.CONVERT_TEST_NAME_D, 5)
        self.assertEqual(test_type.CONVERT_TEST_NAME_E, 5)
        # Ensure that test_type only picked up names matching the filter.
        extra = [name fuer name in dir(test_type) wenn name not in enum_dir(test_type)]
        missing = [name fuer name in enum_dir(test_type) wenn name not in dir(test_type)]
        self.assertEqual(
                extra + missing,
                [],
                msg='extra names: %r;  missing names: %r' % (extra, missing),
                )


    def test_convert_uncomparable(self):
        uncomp = enum.Enum._convert_(
                'Uncomparable',
                MODULE,
                filter=lambda x: x.startswith('UNCOMPARABLE_'))
        # Should be ordered by `name` only:
        self.assertEqual(
            list(uncomp),
            [uncomp.UNCOMPARABLE_A, uncomp.UNCOMPARABLE_B, uncomp.UNCOMPARABLE_C],
            )

    def test_convert_complex(self):
        uncomp = enum.Enum._convert_(
            'Uncomparable',
            MODULE,
            filter=lambda x: x.startswith('COMPLEX_'))
        # Should be ordered by `name` only:
        self.assertEqual(
            list(uncomp),
            [uncomp.COMPLEX_A, uncomp.COMPLEX_B, uncomp.COMPLEX_C],
            )

    def test_convert_str(self):
        test_type = enum.StrEnum._convert_(
                'UnittestConvert',
                MODULE,
                filter=lambda x: x.startswith('CONVERT_STR_'),
                as_global=Wahr)
        # Ensure that test_type has all of the desired names and values.
        self.assertEqual(test_type.CONVERT_STR_TEST_1, 'hello')
        self.assertEqual(test_type.CONVERT_STR_TEST_2, 'goodbye')
        # Ensure that test_type only picked up names matching the filter.
        extra = [name fuer name in dir(test_type) wenn name not in enum_dir(test_type)]
        missing = [name fuer name in enum_dir(test_type) wenn name not in dir(test_type)]
        self.assertEqual(
                extra + missing,
                [],
                msg='extra names: %r;  missing names: %r' % (extra, missing),
                )
        self.assertEqual(repr(test_type.CONVERT_STR_TEST_1), '%s.CONVERT_STR_TEST_1' % SHORT_MODULE)
        self.assertEqual(str(test_type.CONVERT_STR_TEST_2), 'goodbye')
        self.assertEqual(format(test_type.CONVERT_STR_TEST_1), 'hello')

    def test_convert_raise(self):
        with self.assertRaises(AttributeError):
            enum.IntEnum._convert(
                'UnittestConvert',
                MODULE,
                filter=lambda x: x.startswith('CONVERT_TEST_'))

    def test_convert_repr_and_str(self):
        test_type = enum.IntEnum._convert_(
                'UnittestConvert',
                MODULE,
                filter=lambda x: x.startswith('CONVERT_STRING_TEST_'),
                as_global=Wahr)
        self.assertEqual(repr(test_type.CONVERT_STRING_TEST_NAME_A), '%s.CONVERT_STRING_TEST_NAME_A' % SHORT_MODULE)
        self.assertEqual(str(test_type.CONVERT_STRING_TEST_NAME_A), '5')
        self.assertEqual(format(test_type.CONVERT_STRING_TEST_NAME_A), '5')


klasse TestEnumDict(unittest.TestCase):
    def test_enum_dict_in_metaclass(self):
        """Test that EnumDict is usable as a klasse namespace"""
        klasse Meta(type):
            @classmethod
            def __prepare__(metacls, cls, bases, **kwds):
                return EnumDict(cls)

        klasse MyClass(metaclass=Meta):
            a = 1

            with self.assertRaises(TypeError):
                a = 2  # duplicate

            with self.assertRaises(ValueError):
                _a_sunder_ = 3

    def test_enum_dict_standalone(self):
        """Test that EnumDict is usable on its own"""
        enumdict = EnumDict()
        enumdict['a'] = 1

        with self.assertRaises(TypeError):
            enumdict['a'] = 'other value'

        # Only MutableMapping interface is overridden fuer now.
        # If this stops passing, update the documentation.
        enumdict |= {'a': 'other value'}
        self.assertEqual(enumdict['a'], 'other value')


# helpers

def enum_dir(cls):
    interesting = set([
            '__class__', '__contains__', '__doc__', '__getitem__',
            '__iter__', '__len__', '__members__', '__module__',
            '__name__', '__qualname__',
            ]
            + cls._member_names_
            )
    wenn cls._new_member_ is not object.__new__:
        interesting.add('__new__')
    wenn cls.__init_subclass__ is not object.__init_subclass__:
        interesting.add('__init_subclass__')
    wenn cls._member_type_ is object:
        return sorted(interesting)
    sonst:
        # return whatever mixed-in data type has
        return sorted(set(dir(cls._member_type_)) | interesting)

def member_dir(member):
    wenn member.__class__._member_type_ is object:
        allowed = set(['__class__', '__doc__', '__eq__', '__hash__', '__module__', 'name', 'value'])
    sonst:
        allowed = set(dir(member))
    fuer cls in member.__class__.mro():
        fuer name, obj in cls.__dict__.items():
            wenn name[0] == '_':
                continue
            wenn isinstance(obj, enum.property):
                wenn obj.fget is not Nichts or name not in member._member_map_:
                    allowed.add(name)
                sonst:
                    allowed.discard(name)
            sowenn name not in member._member_map_:
                allowed.add(name)
    return sorted(allowed)


wenn __name__ == '__main__':
    unittest.main()
