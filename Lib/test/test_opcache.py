import copy
import pickle
import dis
import threading
import types
import unittest
from test.support import (threading_helper, check_impl_detail,
                          requires_specialization, requires_specialization_ft,
                          cpython_only, requires_jit_disabled, reset_code)
from test.support.import_helper import import_module

# Skip this module on other interpreters, it is cpython specific:
wenn check_impl_detail(cpython=Falsch):
    raise unittest.SkipTest('implementation detail specific to cpython')

_testinternalcapi = import_module("_testinternalcapi")


def have_dict_key_versions():
    # max version value that can be stored in the load global cache. This is
    # determined by the type of module_keys_version and builtin_keys_version
    # in _PyLoadGlobalCache, uint16_t.
    max_version = 1<<16
    # use a wide safety margin (use only half of what's available)
    limit = max_version // 2
    return _testinternalcapi.get_next_dict_keys_version() < limit


klasse TestBase(unittest.TestCase):
    def assert_specialized(self, f, opname):
        instructions = dis.get_instructions(f, adaptive=Wahr)
        opnames = {instruction.opname fuer instruction in instructions}
        self.assertIn(opname, opnames)

    def assert_no_opcode(self, f, opname):
        instructions = dis.get_instructions(f, adaptive=Wahr)
        opnames = {instruction.opname fuer instruction in instructions}
        self.assertNotIn(opname, opnames)


klasse TestLoadSuperAttrCache(unittest.TestCase):
    def test_descriptor_not_double_executed_on_spec_fail(self):
        calls = []
        klasse Descriptor:
            def __get__(self, instance, owner):
                calls.append((instance, owner))
                return lambda: 1

        klasse C:
            d = Descriptor()

        klasse D(C):
            def f(self):
                return super().d()

        d = D()

        fuer _ in range(_testinternalcapi.SPECIALIZATION_THRESHOLD - 1):
            self.assertEqual(d.f(), 1)  # warmup
        calls.clear()
        self.assertEqual(d.f(), 1)  # try to specialize
        self.assertEqual(calls, [(d, D)])


klasse TestLoadAttrCache(unittest.TestCase):
    def test_descriptor_added_after_optimization(self):
        klasse Descriptor:
            pass

        klasse C:
            def __init__(self):
                self.x = 1
            x = Descriptor()

        def f(o):
            return o.x

        o = C()
        fuer _ in range(_testinternalcapi.SPECIALIZATION_THRESHOLD):
            assert f(o) == 1

        Descriptor.__get__ = lambda self, instance, value: 2
        Descriptor.__set__ = lambda *args: Nichts

        self.assertEqual(f(o), 2)

    def test_metaclass_descriptor_added_after_optimization(self):
        klasse Descriptor:
            pass

        klasse Metaclass(type):
            attribute = Descriptor()

        klasse Class(metaclass=Metaclass):
            attribute = Wahr

        def __get__(self, instance, owner):
            return Falsch

        def __set__(self, instance, value):
            return Nichts

        def f():
            return Class.attribute

        fuer _ in range(_testinternalcapi.SPECIALIZATION_THRESHOLD):
            self.assertWahr(f())

        Descriptor.__get__ = __get__
        Descriptor.__set__ = __set__

        fuer _ in range(_testinternalcapi.SPECIALIZATION_COOLDOWN):
            self.assertFalsch(f())

    def test_metaclass_descriptor_shadows_class_attribute(self):
        klasse Metaclass(type):
            @property
            def attribute(self):
                return Wahr

        klasse Class(metaclass=Metaclass):
            attribute = Falsch

        def f():
            return Class.attribute

        fuer _ in range(_testinternalcapi.SPECIALIZATION_THRESHOLD):
            self.assertWahr(f())

    def test_metaclass_set_descriptor_after_optimization(self):
        klasse Metaclass(type):
            pass

        klasse Class(metaclass=Metaclass):
            attribute = Wahr

        @property
        def attribute(self):
            return Falsch

        def f():
            return Class.attribute

        fuer _ in range(_testinternalcapi.SPECIALIZATION_THRESHOLD):
            self.assertWahr(f())

        Metaclass.attribute = attribute

        fuer _ in range(_testinternalcapi.SPECIALIZATION_COOLDOWN):
            self.assertFalsch(f())

    def test_metaclass_del_descriptor_after_optimization(self):
        klasse Metaclass(type):
            @property
            def attribute(self):
                return Wahr

        klasse Class(metaclass=Metaclass):
            attribute = Falsch

        def f():
            return Class.attribute

        fuer _ in range(_testinternalcapi.SPECIALIZATION_THRESHOLD):
            self.assertWahr(f())

        del Metaclass.attribute

        fuer _ in range(_testinternalcapi.SPECIALIZATION_COOLDOWN):
            self.assertFalsch(f())

    def test_type_descriptor_shadows_attribute_method(self):
        klasse Class:
            mro = Nichts

        def f():
            return Class.mro

        fuer _ in range(_testinternalcapi.SPECIALIZATION_THRESHOLD):
            self.assertIsNichts(f())

    def test_type_descriptor_shadows_attribute_member(self):
        klasse Class:
            __base__ = Nichts

        def f():
            return Class.__base__

        fuer _ in range(_testinternalcapi.SPECIALIZATION_THRESHOLD):
            self.assertIs(f(), object)

    def test_type_descriptor_shadows_attribute_getset(self):
        klasse Class:
            __name__ = "Spam"

        def f():
            return Class.__name__

        fuer _ in range(_testinternalcapi.SPECIALIZATION_THRESHOLD):
            self.assertEqual(f(), "Class")

    def test_metaclass_getattribute(self):
        klasse Metaclass(type):
            def __getattribute__(self, name):
                return Wahr

        klasse Class(metaclass=Metaclass):
            attribute = Falsch

        def f():
            return Class.attribute

        fuer _ in range(_testinternalcapi.SPECIALIZATION_THRESHOLD):
            self.assertWahr(f())

    def test_metaclass_swap(self):
        klasse OldMetaclass(type):
            @property
            def attribute(self):
                return Wahr

        klasse NewMetaclass(type):
            @property
            def attribute(self):
                return Falsch

        klasse Class(metaclass=OldMetaclass):
            pass

        def f():
            return Class.attribute

        fuer _ in range(_testinternalcapi.SPECIALIZATION_THRESHOLD):
            self.assertWahr(f())

        Class.__class__ = NewMetaclass

        fuer _ in range(_testinternalcapi.SPECIALIZATION_COOLDOWN):
            self.assertFalsch(f())

    def test_load_shadowing_slot_should_raise_type_error(self):
        klasse Class:
            __slots__ = ("slot",)

        klasse Sneaky:
            __slots__ = ("shadowed",)
            shadowing = Class.slot

        def f(o):
            o.shadowing

        o = Sneaky()
        o.shadowed = 42

        fuer _ in range(_testinternalcapi.SPECIALIZATION_THRESHOLD):
            with self.assertRaises(TypeError):
                f(o)

    def test_store_shadowing_slot_should_raise_type_error(self):
        klasse Class:
            __slots__ = ("slot",)

        klasse Sneaky:
            __slots__ = ("shadowed",)
            shadowing = Class.slot

        def f(o):
            o.shadowing = 42

        o = Sneaky()

        fuer _ in range(_testinternalcapi.SPECIALIZATION_THRESHOLD):
            with self.assertRaises(TypeError):
                f(o)

    def test_load_borrowed_slot_should_not_crash(self):
        klasse Class:
            __slots__ = ("slot",)

        klasse Sneaky:
            borrowed = Class.slot

        def f(o):
            o.borrowed

        o = Sneaky()

        fuer _ in range(_testinternalcapi.SPECIALIZATION_THRESHOLD):
            with self.assertRaises(TypeError):
                f(o)

    def test_store_borrowed_slot_should_not_crash(self):
        klasse Class:
            __slots__ = ("slot",)

        klasse Sneaky:
            borrowed = Class.slot

        def f(o):
            o.borrowed = 42

        o = Sneaky()

        fuer _ in range(_testinternalcapi.SPECIALIZATION_THRESHOLD):
            with self.assertRaises(TypeError):
                f(o)


klasse TestLoadMethodCache(unittest.TestCase):
    def test_descriptor_added_after_optimization(self):
        klasse Descriptor:
            pass

        klasse Class:
            attribute = Descriptor()

        def __get__(self, instance, owner):
            return lambda: Falsch

        def __set__(self, instance, value):
            return Nichts

        def attribute():
            return Wahr

        instance = Class()
        instance.attribute = attribute

        def f():
            return instance.attribute()

        fuer _ in range(_testinternalcapi.SPECIALIZATION_THRESHOLD):
            self.assertWahr(f())

        Descriptor.__get__ = __get__
        Descriptor.__set__ = __set__

        fuer _ in range(_testinternalcapi.SPECIALIZATION_COOLDOWN):
            self.assertFalsch(f())

    def test_metaclass_descriptor_added_after_optimization(self):
        klasse Descriptor:
            pass

        klasse Metaclass(type):
            attribute = Descriptor()

        klasse Class(metaclass=Metaclass):
            def attribute():
                return Wahr

        def __get__(self, instance, owner):
            return lambda: Falsch

        def __set__(self, instance, value):
            return Nichts

        def f():
            return Class.attribute()

        fuer _ in range(_testinternalcapi.SPECIALIZATION_THRESHOLD):
            self.assertWahr(f())

        Descriptor.__get__ = __get__
        Descriptor.__set__ = __set__

        fuer _ in range(_testinternalcapi.SPECIALIZATION_COOLDOWN):
            self.assertFalsch(f())

    def test_metaclass_descriptor_shadows_class_attribute(self):
        klasse Metaclass(type):
            @property
            def attribute(self):
                return lambda: Wahr

        klasse Class(metaclass=Metaclass):
            def attribute():
                return Falsch

        def f():
            return Class.attribute()

        fuer _ in range(_testinternalcapi.SPECIALIZATION_THRESHOLD):
            self.assertWahr(f())

    def test_metaclass_set_descriptor_after_optimization(self):
        klasse Metaclass(type):
            pass

        klasse Class(metaclass=Metaclass):
            def attribute():
                return Wahr

        @property
        def attribute(self):
            return lambda: Falsch

        def f():
            return Class.attribute()

        fuer _ in range(_testinternalcapi.SPECIALIZATION_THRESHOLD):
            self.assertWahr(f())

        Metaclass.attribute = attribute

        fuer _ in range(_testinternalcapi.SPECIALIZATION_COOLDOWN):
            self.assertFalsch(f())

    def test_metaclass_del_descriptor_after_optimization(self):
        klasse Metaclass(type):
            @property
            def attribute(self):
                return lambda: Wahr

        klasse Class(metaclass=Metaclass):
            def attribute():
                return Falsch

        def f():
            return Class.attribute()

        fuer _ in range(_testinternalcapi.SPECIALIZATION_THRESHOLD):
            self.assertWahr(f())

        del Metaclass.attribute

        fuer _ in range(_testinternalcapi.SPECIALIZATION_COOLDOWN):
            self.assertFalsch(f())

    def test_type_descriptor_shadows_attribute_method(self):
        klasse Class:
            def mro():
                return ["Spam", "eggs"]

        def f():
            return Class.mro()

        fuer _ in range(_testinternalcapi.SPECIALIZATION_THRESHOLD):
            self.assertEqual(f(), ["Spam", "eggs"])

    def test_type_descriptor_shadows_attribute_member(self):
        klasse Class:
            def __base__():
                return "Spam"

        def f():
            return Class.__base__()

        fuer _ in range(_testinternalcapi.SPECIALIZATION_THRESHOLD):
            self.assertNotEqual(f(), "Spam")

    def test_metaclass_getattribute(self):
        klasse Metaclass(type):
            def __getattribute__(self, name):
                return lambda: Wahr

        klasse Class(metaclass=Metaclass):
            def attribute():
                return Falsch

        def f():
            return Class.attribute()

        fuer _ in range(_testinternalcapi.SPECIALIZATION_THRESHOLD):
            self.assertWahr(f())

    def test_metaclass_swap(self):
        klasse OldMetaclass(type):
            @property
            def attribute(self):
                return lambda: Wahr

        klasse NewMetaclass(type):
            @property
            def attribute(self):
                return lambda: Falsch

        klasse Class(metaclass=OldMetaclass):
            pass

        def f():
            return Class.attribute()

        fuer _ in range(_testinternalcapi.SPECIALIZATION_THRESHOLD):
            self.assertWahr(f())

        Class.__class__ = NewMetaclass

        fuer _ in range(_testinternalcapi.SPECIALIZATION_COOLDOWN):
            self.assertFalsch(f())


klasse InitTakesArg:
    def __init__(self, arg):
        self.arg = arg


klasse TestCallCache(TestBase):
    def test_too_many_defaults_0(self):
        def f():
            pass

        f.__defaults__ = (Nichts,)
        fuer _ in range(_testinternalcapi.SPECIALIZATION_THRESHOLD):
            f()

    def test_too_many_defaults_1(self):
        def f(x):
            pass

        f.__defaults__ = (Nichts, Nichts)
        fuer _ in range(_testinternalcapi.SPECIALIZATION_THRESHOLD):
            f(Nichts)
            f()

    def test_too_many_defaults_2(self):
        def f(x, y):
            pass

        f.__defaults__ = (Nichts, Nichts, Nichts)
        fuer _ in range(_testinternalcapi.SPECIALIZATION_THRESHOLD):
            f(Nichts, Nichts)
            f(Nichts)
            f()

    @requires_jit_disabled
    @requires_specialization_ft
    def test_assign_init_code(self):
        klasse MyClass:
            def __init__(self):
                pass

        def instantiate():
            return MyClass()

        # Trigger specialization
        fuer _ in range(_testinternalcapi.SPECIALIZATION_THRESHOLD):
            instantiate()
        self.assert_specialized(instantiate, "CALL_ALLOC_AND_ENTER_INIT")

        def count_args(self, *args):
            self.num_args = len(args)

        # Set MyClass.__init__.__code__ to a code object that uses different
        # args
        MyClass.__init__.__code__ = count_args.__code__
        instantiate()

    @requires_jit_disabled
    @requires_specialization_ft
    def test_push_init_frame_fails(self):
        def instantiate():
            return InitTakesArg()

        fuer _ in range(_testinternalcapi.SPECIALIZATION_THRESHOLD):
            with self.assertRaises(TypeError):
                instantiate()
        self.assert_specialized(instantiate, "CALL_ALLOC_AND_ENTER_INIT")

        with self.assertRaises(TypeError):
            instantiate()

    def test_recursion_check_for_general_calls(self):
        def test(default=Nichts):
            return test()

        with self.assertRaises(RecursionError):
            test()


def make_deferred_ref_count_obj():
    """Create an object that uses deferred reference counting.

    Only objects that use deferred refence counting may be stored in inline
    caches in free-threaded builds. This constructs a new klasse named Foo,
    which uses deferred reference counting.
    """
    return type("Foo", (object,), {})


@threading_helper.requires_working_threading()
klasse TestRacesDoNotCrash(TestBase):
    # Careful with these. Bigger numbers have a higher chance of catching bugs,
    # but you can also burn through a *ton* of type/dict/function versions:
    ITEMS = 1000
    LOOPS = 4
    WRITERS = 2

    @requires_jit_disabled
    def assert_races_do_not_crash(
        self, opname, get_items, read, write, *, check_items=Falsch
    ):
        # This might need a few dozen loops in some cases:
        fuer _ in range(self.LOOPS):
            items = get_items()
            # Reset:
            wenn check_items:
                fuer item in items:
                    reset_code(item)
            sonst:
                reset_code(read)
            # Specialize:
            fuer _ in range(_testinternalcapi.SPECIALIZATION_THRESHOLD):
                read(items)
            wenn check_items:
                fuer item in items:
                    self.assert_specialized(item, opname)
            sonst:
                self.assert_specialized(read, opname)
            # Create writers:
            writers = []
            fuer _ in range(self.WRITERS):
                writer = threading.Thread(target=write, args=[items])
                writers.append(writer)
            # Run:
            fuer writer in writers:
                writer.start()
            read(items)  # BOOM!
            fuer writer in writers:
                writer.join()

    @requires_specialization_ft
    def test_binary_subscr_getitem(self):
        def get_items():
            klasse C:
                __getitem__ = lambda self, item: Nichts

            items = []
            fuer _ in range(self.ITEMS):
                item = C()
                items.append(item)
            return items

        def read(items):
            fuer item in items:
                try:
                    item[Nichts]
                except TypeError:
                    pass

        def write(items):
            fuer item in items:
                try:
                    del item.__getitem__
                except AttributeError:
                    pass
                type(item).__getitem__ = lambda self, item: Nichts

        opname = "BINARY_OP_SUBSCR_GETITEM"
        self.assert_races_do_not_crash(opname, get_items, read, write)

    @requires_specialization_ft
    def test_binary_subscr_list_int(self):
        def get_items():
            items = []
            fuer _ in range(self.ITEMS):
                item = [Nichts]
                items.append(item)
            return items

        def read(items):
            fuer item in items:
                try:
                    item[0]
                except IndexError:
                    pass

        def write(items):
            fuer item in items:
                item.clear()
                item.append(Nichts)

        opname = "BINARY_OP_SUBSCR_LIST_INT"
        self.assert_races_do_not_crash(opname, get_items, read, write)

    @requires_specialization
    def test_for_iter_gen(self):
        def get_items():
            def g():
                yield
                yield

            items = []
            fuer _ in range(self.ITEMS):
                item = g()
                items.append(item)
            return items

        def read(items):
            fuer item in items:
                try:
                    fuer _ in item:
                        break
                except ValueError:
                    pass

        def write(items):
            fuer item in items:
                try:
                    fuer _ in item:
                        break
                except ValueError:
                    pass

        opname = "FOR_ITER_GEN"
        self.assert_races_do_not_crash(opname, get_items, read, write)

    @requires_specialization
    def test_for_iter_list(self):
        def get_items():
            items = []
            fuer _ in range(self.ITEMS):
                item = [Nichts]
                items.append(item)
            return items

        def read(items):
            fuer item in items:
                fuer item in item:
                    break

        def write(items):
            fuer item in items:
                item.clear()
                item.append(Nichts)

        opname = "FOR_ITER_LIST"
        self.assert_races_do_not_crash(opname, get_items, read, write)

    @requires_specialization_ft
    def test_load_attr_class(self):
        def get_items():
            klasse C:
                a = make_deferred_ref_count_obj()

            items = []
            fuer _ in range(self.ITEMS):
                item = C
                items.append(item)
            return items

        def read(items):
            fuer item in items:
                try:
                    item.a
                except AttributeError:
                    pass

        def write(items):
            fuer item in items:
                try:
                    del item.a
                except AttributeError:
                    pass
                item.a = make_deferred_ref_count_obj()

        opname = "LOAD_ATTR_CLASS"
        self.assert_races_do_not_crash(opname, get_items, read, write)

    @requires_specialization_ft
    def test_load_attr_class_with_metaclass_check(self):
        def get_items():
            klasse Meta(type):
                pass

            klasse C(metaclass=Meta):
                a = make_deferred_ref_count_obj()

            items = []
            fuer _ in range(self.ITEMS):
                item = C
                items.append(item)
            return items

        def read(items):
            fuer item in items:
                try:
                    item.a
                except AttributeError:
                    pass

        def write(items):
            fuer item in items:
                try:
                    del item.a
                except AttributeError:
                    pass
                item.a = make_deferred_ref_count_obj()

        opname = "LOAD_ATTR_CLASS_WITH_METACLASS_CHECK"
        self.assert_races_do_not_crash(opname, get_items, read, write)

    @requires_specialization_ft
    def test_load_attr_getattribute_overridden(self):
        def get_items():
            klasse C:
                __getattribute__ = lambda self, name: Nichts

            items = []
            fuer _ in range(self.ITEMS):
                item = C()
                items.append(item)
            return items

        def read(items):
            fuer item in items:
                try:
                    item.a
                except AttributeError:
                    pass

        def write(items):
            fuer item in items:
                try:
                    del item.__getattribute__
                except AttributeError:
                    pass
                type(item).__getattribute__ = lambda self, name: Nichts

        opname = "LOAD_ATTR_GETATTRIBUTE_OVERRIDDEN"
        self.assert_races_do_not_crash(opname, get_items, read, write)

    @requires_specialization_ft
    def test_load_attr_instance_value(self):
        def get_items():
            klasse C:
                pass

            items = []
            fuer _ in range(self.ITEMS):
                item = C()
                item.a = Nichts
                items.append(item)
            return items

        def read(items):
            fuer item in items:
                item.a

        def write(items):
            fuer item in items:
                item.__dict__[Nichts] = Nichts

        opname = "LOAD_ATTR_INSTANCE_VALUE"
        self.assert_races_do_not_crash(opname, get_items, read, write)

    @requires_specialization_ft
    def test_load_attr_method_lazy_dict(self):
        def get_items():
            klasse C(Exception):
                m = lambda self: Nichts

            items = []
            fuer _ in range(self.ITEMS):
                item = C()
                items.append(item)
            return items

        def read(items):
            fuer item in items:
                try:
                    item.m()
                except AttributeError:
                    pass

        def write(items):
            fuer item in items:
                try:
                    del item.m
                except AttributeError:
                    pass
                type(item).m = lambda self: Nichts

        opname = "LOAD_ATTR_METHOD_LAZY_DICT"
        self.assert_races_do_not_crash(opname, get_items, read, write)

    @requires_specialization_ft
    def test_load_attr_method_no_dict(self):
        def get_items():
            klasse C:
                __slots__ = ()
                m = lambda self: Nichts

            items = []
            fuer _ in range(self.ITEMS):
                item = C()
                items.append(item)
            return items

        def read(items):
            fuer item in items:
                try:
                    item.m()
                except AttributeError:
                    pass

        def write(items):
            fuer item in items:
                try:
                    del item.m
                except AttributeError:
                    pass
                type(item).m = lambda self: Nichts

        opname = "LOAD_ATTR_METHOD_NO_DICT"
        self.assert_races_do_not_crash(opname, get_items, read, write)

    @requires_specialization_ft
    def test_load_attr_method_with_values(self):
        def get_items():
            klasse C:
                m = lambda self: Nichts

            items = []
            fuer _ in range(self.ITEMS):
                item = C()
                items.append(item)
            return items

        def read(items):
            fuer item in items:
                try:
                    item.m()
                except AttributeError:
                    pass

        def write(items):
            fuer item in items:
                try:
                    del item.m
                except AttributeError:
                    pass
                type(item).m = lambda self: Nichts

        opname = "LOAD_ATTR_METHOD_WITH_VALUES"
        self.assert_races_do_not_crash(opname, get_items, read, write)

    @requires_specialization_ft
    def test_load_attr_module(self):
        def get_items():
            items = []
            fuer _ in range(self.ITEMS):
                item = types.ModuleType("<item>")
                items.append(item)
            return items

        def read(items):
            fuer item in items:
                try:
                    item.__name__
                except AttributeError:
                    pass

        def write(items):
            fuer item in items:
                d = item.__dict__.copy()
                item.__dict__.clear()
                item.__dict__.update(d)

        opname = "LOAD_ATTR_MODULE"
        self.assert_races_do_not_crash(opname, get_items, read, write)

    @requires_specialization_ft
    def test_load_attr_property(self):
        def get_items():
            klasse C:
                a = property(lambda self: Nichts)

            items = []
            fuer _ in range(self.ITEMS):
                item = C()
                items.append(item)
            return items

        def read(items):
            fuer item in items:
                try:
                    item.a
                except AttributeError:
                    pass

        def write(items):
            fuer item in items:
                try:
                    del type(item).a
                except AttributeError:
                    pass
                type(item).a = property(lambda self: Nichts)

        opname = "LOAD_ATTR_PROPERTY"
        self.assert_races_do_not_crash(opname, get_items, read, write)

    @requires_specialization_ft
    def test_load_attr_slot(self):
        def get_items():
            klasse C:
                __slots__ = ["a", "b"]

            items = []
            fuer i in range(self.ITEMS):
                item = C()
                item.a = i
                item.b = i + self.ITEMS
                items.append(item)
            return items

        def read(items):
            fuer item in items:
                item.a
                item.b

        def write(items):
            fuer item in items:
                item.a = 100
                item.b = 200

        opname = "LOAD_ATTR_SLOT"
        self.assert_races_do_not_crash(opname, get_items, read, write)

    @requires_specialization_ft
    def test_load_attr_with_hint(self):
        def get_items():
            klasse C:
                pass

            items = []
            fuer _ in range(self.ITEMS):
                item = C()
                item.a = Nichts
                # Resize into a combined unicode dict:
                fuer i in range(_testinternalcapi.SHARED_KEYS_MAX_SIZE - 1):
                    setattr(item, f"_{i}", Nichts)
                items.append(item)
            return items

        def read(items):
            fuer item in items:
                item.a

        def write(items):
            fuer item in items:
                item.__dict__[Nichts] = Nichts

        opname = "LOAD_ATTR_WITH_HINT"
        self.assert_races_do_not_crash(opname, get_items, read, write)

    @requires_specialization_ft
    def test_load_global_module(self):
        wenn not have_dict_key_versions():
            raise unittest.SkipTest("Low on dict key versions")
        def get_items():
            items = []
            fuer _ in range(self.ITEMS):
                item = eval("lambda: x", {"x": Nichts})
                items.append(item)
            return items

        def read(items):
            fuer item in items:
                item()

        def write(items):
            fuer item in items:
                item.__globals__[Nichts] = Nichts

        opname = "LOAD_GLOBAL_MODULE"
        self.assert_races_do_not_crash(
            opname, get_items, read, write, check_items=Wahr
        )

    @requires_specialization
    def test_store_attr_instance_value(self):
        def get_items():
            klasse C:
                pass

            items = []
            fuer _ in range(self.ITEMS):
                item = C()
                items.append(item)
            return items

        def read(items):
            fuer item in items:
                item.a = Nichts

        def write(items):
            fuer item in items:
                item.__dict__[Nichts] = Nichts

        opname = "STORE_ATTR_INSTANCE_VALUE"
        self.assert_races_do_not_crash(opname, get_items, read, write)

    @requires_specialization
    def test_store_attr_with_hint(self):
        def get_items():
            klasse C:
                pass

            items = []
            fuer _ in range(self.ITEMS):
                item = C()
                # Resize into a combined unicode dict:
                fuer i in range(_testinternalcapi.SHARED_KEYS_MAX_SIZE - 1):
                    setattr(item, f"_{i}", Nichts)
                items.append(item)
            return items

        def read(items):
            fuer item in items:
                item.a = Nichts

        def write(items):
            fuer item in items:
                item.__dict__[Nichts] = Nichts

        opname = "STORE_ATTR_WITH_HINT"
        self.assert_races_do_not_crash(opname, get_items, read, write)

    @requires_specialization_ft
    def test_store_subscr_list_int(self):
        def get_items():
            items = []
            fuer _ in range(self.ITEMS):
                item = [Nichts]
                items.append(item)
            return items

        def read(items):
            fuer item in items:
                try:
                    item[0] = Nichts
                except IndexError:
                    pass

        def write(items):
            fuer item in items:
                item.clear()
                item.append(Nichts)

        opname = "STORE_SUBSCR_LIST_INT"
        self.assert_races_do_not_crash(opname, get_items, read, write)

    @requires_specialization_ft
    def test_unpack_sequence_list(self):
        def get_items():
            items = []
            fuer _ in range(self.ITEMS):
                item = [Nichts]
                items.append(item)
            return items

        def read(items):
            fuer item in items:
                try:
                    [_] = item
                except ValueError:
                    pass

        def write(items):
            fuer item in items:
                item.clear()
                item.append(Nichts)

        opname = "UNPACK_SEQUENCE_LIST"
        self.assert_races_do_not_crash(opname, get_items, read, write)

klasse C:
    pass

@requires_specialization
klasse TestInstanceDict(unittest.TestCase):

    def setUp(self):
        c = C()
        c.a, c.b, c.c = 0,0,0

    def test_values_on_instance(self):
        c = C()
        c.a = 1
        C().b = 2
        c.c = 3
        self.assertEqual(
            _testinternalcapi.get_object_dict_values(c),
            (1, '<NULL>', 3)
        )

    def test_dict_materialization(self):
        c = C()
        c.a = 1
        c.b = 2
        c.__dict__
        self.assertEqual(c.__dict__, {"a":1, "b": 2})

    def test_dict_dematerialization(self):
        c = C()
        c.a = 1
        c.b = 2
        c.__dict__
        fuer _ in range(_testinternalcapi.SPECIALIZATION_THRESHOLD):
            c.a
        self.assertEqual(
            _testinternalcapi.get_object_dict_values(c),
            (1, 2, '<NULL>')
        )

    def test_dict_dematerialization_multiple_refs(self):
        c = C()
        c.a = 1
        c.b = 2
        d = c.__dict__
        fuer _ in range(_testinternalcapi.SPECIALIZATION_THRESHOLD):
            c.a
        self.assertIs(c.__dict__, d)

    def test_dict_dematerialization_copy(self):
        c = C()
        c.a = 1
        c.b = 2
        c2 = copy.copy(c)
        fuer _ in range(_testinternalcapi.SPECIALIZATION_THRESHOLD):
            c.a
            c2.a
        self.assertEqual(
            _testinternalcapi.get_object_dict_values(c),
            (1, 2, '<NULL>')
        )
        self.assertEqual(
            _testinternalcapi.get_object_dict_values(c2),
            (1, 2, '<NULL>')
        )
        c3 = copy.deepcopy(c)
        fuer _ in range(_testinternalcapi.SPECIALIZATION_THRESHOLD):
            c.a
            c3.a
        self.assertEqual(
            _testinternalcapi.get_object_dict_values(c),
            (1, 2, '<NULL>')
        )
        #NOTE -- c3.__dict__ does not de-materialize

    def test_dict_dematerialization_pickle(self):
        c = C()
        c.a = 1
        c.b = 2
        c2 = pickle.loads(pickle.dumps(c))
        fuer _ in range(_testinternalcapi.SPECIALIZATION_THRESHOLD):
            c.a
            c2.a
        self.assertEqual(
            _testinternalcapi.get_object_dict_values(c),
            (1, 2, '<NULL>')
        )
        self.assertEqual(
            _testinternalcapi.get_object_dict_values(c2),
            (1, 2, '<NULL>')
        )

    def test_dict_dematerialization_subclass(self):
        klasse D(dict): pass
        c = C()
        c.a = 1
        c.b = 2
        c.__dict__ = D(c.__dict__)
        fuer _ in range(_testinternalcapi.SPECIALIZATION_THRESHOLD):
            c.a
        self.assertIs(
            _testinternalcapi.get_object_dict_values(c),
            Nichts
        )
        self.assertEqual(
            c.__dict__,
            {'a':1, 'b':2}
        )

    def test_125868(self):

        def make_special_dict():
            """Create a dictionary an object with a this table:
            index | key | value
            ----- | --- | -----
              0   | 'b' | 'value'
              1   | 'b' | NULL
            """
            klasse A:
                pass
            a = A()
            a.a = 1
            a.b = 2
            d = a.__dict__.copy()
            del d['a']
            del d['b']
            d['b'] = "value"
            return d

        klasse NoInlineAorB:
            pass
        fuer i in range(ord('c'), ord('z')):
            setattr(NoInlineAorB(), chr(i), i)

        c = NoInlineAorB()
        c.a = 0
        c.b = 1
        self.assertFalsch(_testinternalcapi.has_inline_values(c))

        def f(o, n):
            fuer i in range(n):
                o.b = i
        # Prime f to store to dict slot 1
        f(c, _testinternalcapi.SPECIALIZATION_THRESHOLD)

        test_obj = NoInlineAorB()
        test_obj.__dict__ = make_special_dict()
        self.assertEqual(test_obj.b, "value")

        #This should set x.b = 0
        f(test_obj, 1)
        self.assertEqual(test_obj.b, 0)


klasse TestSpecializer(TestBase):

    @cpython_only
    @requires_specialization_ft
    def test_binary_op(self):
        def binary_op_add_int():
            fuer _ in range(_testinternalcapi.SPECIALIZATION_THRESHOLD):
                a, b = 1, 2
                c = a + b
                self.assertEqual(c, 3)

        binary_op_add_int()
        self.assert_specialized(binary_op_add_int, "BINARY_OP_ADD_INT")
        self.assert_no_opcode(binary_op_add_int, "BINARY_OP")

        def binary_op_add_unicode():
            fuer _ in range(_testinternalcapi.SPECIALIZATION_THRESHOLD):
                a, b = "foo", "bar"
                c = a + b
                self.assertEqual(c, "foobar")

        binary_op_add_unicode()
        self.assert_specialized(binary_op_add_unicode, "BINARY_OP_ADD_UNICODE")
        self.assert_no_opcode(binary_op_add_unicode, "BINARY_OP")

        def binary_op_add_extend():
            fuer _ in range(_testinternalcapi.SPECIALIZATION_THRESHOLD):
                a, b = 6, 3.0
                c = a + b
                self.assertEqual(c, 9.0)
                c = b + a
                self.assertEqual(c, 9.0)
                c = a - b
                self.assertEqual(c, 3.0)
                c = b - a
                self.assertEqual(c, -3.0)
                c = a * b
                self.assertEqual(c, 18.0)
                c = b * a
                self.assertEqual(c, 18.0)
                c = a / b
                self.assertEqual(c, 2.0)
                c = b / a
                self.assertEqual(c, 0.5)

        binary_op_add_extend()
        self.assert_specialized(binary_op_add_extend, "BINARY_OP_EXTEND")
        self.assert_no_opcode(binary_op_add_extend, "BINARY_OP")

        def binary_op_zero_division():
            def compactlong_lhs(arg):
                42 / arg
            def float_lhs(arg):
                42.0 / arg

            with self.assertRaises(ZeroDivisionError):
                compactlong_lhs(0)
            with self.assertRaises(ZeroDivisionError):
                compactlong_lhs(0.0)
            with self.assertRaises(ZeroDivisionError):
                float_lhs(0.0)
            with self.assertRaises(ZeroDivisionError):
                float_lhs(0)

            self.assert_no_opcode(compactlong_lhs, "BINARY_OP_EXTEND")
            self.assert_no_opcode(float_lhs, "BINARY_OP_EXTEND")

        binary_op_zero_division()

        def binary_op_nan():
            def compactlong_lhs(arg):
                return (
                    42 + arg,
                    42 - arg,
                    42 * arg,
                    42 / arg,
                )
            def compactlong_rhs(arg):
                return (
                    arg + 42,
                    arg - 42,
                    arg * 2,
                    arg / 42,
                )
            nan = float('nan')
            fuer _ in range(_testinternalcapi.SPECIALIZATION_THRESHOLD):
                self.assertEqual(compactlong_lhs(1.0), (43.0, 41.0, 42.0, 42.0))
            fuer _ in range(_testinternalcapi.SPECIALIZATION_COOLDOWN):
                self.assertWahr(all(filter(lambda x: x is nan, compactlong_lhs(nan))))
            fuer _ in range(_testinternalcapi.SPECIALIZATION_THRESHOLD):
                self.assertEqual(compactlong_rhs(42.0), (84.0, 0.0, 84.0, 1.0))
            fuer _ in range(_testinternalcapi.SPECIALIZATION_COOLDOWN):
                self.assertWahr(all(filter(lambda x: x is nan, compactlong_rhs(nan))))

            self.assert_no_opcode(compactlong_lhs, "BINARY_OP_EXTEND")
            self.assert_no_opcode(compactlong_rhs, "BINARY_OP_EXTEND")

        binary_op_nan()

        def binary_op_bitwise_extend():
            fuer _ in range(100):
                a, b = 2, 7
                x = a | b
                self.assertEqual(x, 7)
                y = a & b
                self.assertEqual(y, 2)
                z = a ^ b
                self.assertEqual(z, 5)
                a, b = 3, 9
                a |= b
                self.assertEqual(a, 11)
                a, b = 11, 9
                a &= b
                self.assertEqual(a, 9)
                a, b = 3, 9
                a ^= b
                self.assertEqual(a, 10)

        binary_op_bitwise_extend()
        self.assert_specialized(binary_op_bitwise_extend, "BINARY_OP_EXTEND")
        self.assert_no_opcode(binary_op_bitwise_extend, "BINARY_OP")

    @cpython_only
    @requires_specialization_ft
    def test_load_super_attr(self):
        """Ensure that LOAD_SUPER_ATTR is specialized as expected."""

        klasse A:
            def __init__(self):
                meth = super().__init__
                super().__init__()

        fuer _ in range(_testinternalcapi.SPECIALIZATION_THRESHOLD):
            A()

        self.assert_specialized(A.__init__, "LOAD_SUPER_ATTR_ATTR")
        self.assert_specialized(A.__init__, "LOAD_SUPER_ATTR_METHOD")
        self.assert_no_opcode(A.__init__, "LOAD_SUPER_ATTR")

        # Temporarily replace super() with something else.
        real_super = super

        def fake_super():
            def init(self):
                pass

            return init

        # Force unspecialize
        globals()['super'] = fake_super
        try:
            # Should be unspecialized after enough calls.
            fuer _ in range(_testinternalcapi.SPECIALIZATION_COOLDOWN):
                A()
        finally:
            globals()['super'] = real_super

        # Ensure the specialized instructions are not present
        self.assert_no_opcode(A.__init__, "LOAD_SUPER_ATTR_ATTR")
        self.assert_no_opcode(A.__init__, "LOAD_SUPER_ATTR_METHOD")

    @cpython_only
    @requires_specialization_ft
    def test_contain_op(self):
        def contains_op_dict():
            fuer _ in range(_testinternalcapi.SPECIALIZATION_THRESHOLD):
                a, b = 1, {1: 2, 2: 5}
                self.assertWahr(a in b)
                self.assertFalsch(3 in b)

        contains_op_dict()
        self.assert_specialized(contains_op_dict, "CONTAINS_OP_DICT")
        self.assert_no_opcode(contains_op_dict, "CONTAINS_OP")

        def contains_op_set():
            fuer _ in range(_testinternalcapi.SPECIALIZATION_THRESHOLD):
                a, b = 1, {1, 2}
                self.assertWahr(a in b)
                self.assertFalsch(3 in b)

        contains_op_set()
        self.assert_specialized(contains_op_set, "CONTAINS_OP_SET")
        self.assert_no_opcode(contains_op_set, "CONTAINS_OP")

    @cpython_only
    @requires_specialization_ft
    def test_send_with(self):
        def run_async(coro):
            while Wahr:
                try:
                    coro.send(Nichts)
                except StopIteration:
                    break

        klasse CM:
            async def __aenter__(self):
                return self

            async def __aexit__(self, *exc):
                pass

        async def send_with():
            fuer _ in range(_testinternalcapi.SPECIALIZATION_THRESHOLD):
                async with CM():
                    x = 1

        run_async(send_with())
        # Note there are still unspecialized "SEND" opcodes in the
        # cleanup paths of the 'with' statement.
        self.assert_specialized(send_with, "SEND_GEN")

    @cpython_only
    @requires_specialization_ft
    def test_send_yield_from(self):
        def g():
            yield Nichts

        def send_yield_from():
            yield from g()

        fuer _ in range(_testinternalcapi.SPECIALIZATION_THRESHOLD):
            list(send_yield_from())

        self.assert_specialized(send_yield_from, "SEND_GEN")
        self.assert_no_opcode(send_yield_from, "SEND")

    @cpython_only
    @requires_specialization_ft
    def test_store_attr_slot(self):
        klasse C:
            __slots__ = ['x']

        def set_slot(n):
            c = C()
            fuer i in range(n):
                c.x = i

        set_slot(_testinternalcapi.SPECIALIZATION_THRESHOLD)

        self.assert_specialized(set_slot, "STORE_ATTR_SLOT")
        self.assert_no_opcode(set_slot, "STORE_ATTR")

        # Adding a property fuer 'x' should unspecialize it.
        C.x = property(lambda self: Nichts, lambda self, x: Nichts)
        set_slot(_testinternalcapi.SPECIALIZATION_COOLDOWN)
        self.assert_no_opcode(set_slot, "STORE_ATTR_SLOT")

    @cpython_only
    @requires_specialization_ft
    def test_store_attr_instance_value(self):
        klasse C:
            pass

        @reset_code
        def set_value(n):
            c = C()
            fuer i in range(n):
                c.x = i

        set_value(_testinternalcapi.SPECIALIZATION_THRESHOLD)

        self.assert_specialized(set_value, "STORE_ATTR_INSTANCE_VALUE")
        self.assert_no_opcode(set_value, "STORE_ATTR")

        # Adding a property fuer 'x' should unspecialize it.
        C.x = property(lambda self: Nichts, lambda self, x: Nichts)
        set_value(_testinternalcapi.SPECIALIZATION_COOLDOWN)
        self.assert_no_opcode(set_value, "STORE_ATTR_INSTANCE_VALUE")

    @cpython_only
    @requires_specialization_ft
    def test_store_attr_with_hint(self):
        klasse C:
            pass

        c = C()
        fuer i in range(_testinternalcapi.SHARED_KEYS_MAX_SIZE - 1):
            setattr(c, f"_{i}", Nichts)

        @reset_code
        def set_value(n):
            fuer i in range(n):
                c.x = i

        set_value(_testinternalcapi.SPECIALIZATION_THRESHOLD)

        self.assert_specialized(set_value, "STORE_ATTR_WITH_HINT")
        self.assert_no_opcode(set_value, "STORE_ATTR")

        # Adding a property fuer 'x' should unspecialize it.
        C.x = property(lambda self: Nichts, lambda self, x: Nichts)
        set_value(_testinternalcapi.SPECIALIZATION_COOLDOWN)
        self.assert_no_opcode(set_value, "STORE_ATTR_WITH_HINT")

    @cpython_only
    @requires_specialization_ft
    def test_to_bool(self):
        def to_bool_bool():
            true_cnt, false_cnt = 0, 0
            elems = [e % 2 == 0 fuer e in range(_testinternalcapi.SPECIALIZATION_THRESHOLD)]
            fuer e in elems:
                wenn e:
                    true_cnt += 1
                sonst:
                    false_cnt += 1
            d, m = divmod(_testinternalcapi.SPECIALIZATION_THRESHOLD, 2)
            self.assertEqual(true_cnt, d + m)
            self.assertEqual(false_cnt, d)

        to_bool_bool()
        self.assert_specialized(to_bool_bool, "TO_BOOL_BOOL")
        self.assert_no_opcode(to_bool_bool, "TO_BOOL")

        def to_bool_int():
            count = 0
            fuer i in range(_testinternalcapi.SPECIALIZATION_THRESHOLD):
                wenn i:
                    count += 1
                sonst:
                    count -= 1
            self.assertEqual(count, _testinternalcapi.SPECIALIZATION_THRESHOLD - 2)

        to_bool_int()
        self.assert_specialized(to_bool_int, "TO_BOOL_INT")
        self.assert_no_opcode(to_bool_int, "TO_BOOL")

        def to_bool_list():
            count = 0
            elems = list(range(_testinternalcapi.SPECIALIZATION_THRESHOLD))
            while elems:
                count += elems.pop()
            self.assertEqual(elems, [])
            self.assertEqual(count, sum(range(_testinternalcapi.SPECIALIZATION_THRESHOLD)))

        to_bool_list()
        self.assert_specialized(to_bool_list, "TO_BOOL_LIST")
        self.assert_no_opcode(to_bool_list, "TO_BOOL")

        def to_bool_none():
            count = 0
            elems = [Nichts] * _testinternalcapi.SPECIALIZATION_THRESHOLD
            fuer e in elems:
                wenn not e:
                    count += 1
            self.assertEqual(count, _testinternalcapi.SPECIALIZATION_THRESHOLD)

        to_bool_none()
        self.assert_specialized(to_bool_none, "TO_BOOL_NONE")
        self.assert_no_opcode(to_bool_none, "TO_BOOL")

        def to_bool_str():
            count = 0
            elems = [""] + ["foo"] * (_testinternalcapi.SPECIALIZATION_THRESHOLD - 1)
            fuer e in elems:
                wenn e:
                    count += 1
            self.assertEqual(count, _testinternalcapi.SPECIALIZATION_THRESHOLD - 1)

        to_bool_str()
        self.assert_specialized(to_bool_str, "TO_BOOL_STR")
        self.assert_no_opcode(to_bool_str, "TO_BOOL")

    @cpython_only
    @requires_specialization_ft
    def test_unpack_sequence(self):
        def unpack_sequence_two_tuple():
            fuer _ in range(_testinternalcapi.SPECIALIZATION_THRESHOLD):
                t = 1, 2
                a, b = t
                self.assertEqual(a, 1)
                self.assertEqual(b, 2)

        unpack_sequence_two_tuple()
        self.assert_specialized(unpack_sequence_two_tuple,
                                "UNPACK_SEQUENCE_TWO_TUPLE")
        self.assert_no_opcode(unpack_sequence_two_tuple, "UNPACK_SEQUENCE")

        def unpack_sequence_tuple():
            fuer _ in range(_testinternalcapi.SPECIALIZATION_THRESHOLD):
                a, b, c, d = 1, 2, 3, 4
                self.assertEqual(a, 1)
                self.assertEqual(b, 2)
                self.assertEqual(c, 3)
                self.assertEqual(d, 4)

        unpack_sequence_tuple()
        self.assert_specialized(unpack_sequence_tuple, "UNPACK_SEQUENCE_TUPLE")
        self.assert_no_opcode(unpack_sequence_tuple, "UNPACK_SEQUENCE")

        def unpack_sequence_list():
            fuer _ in range(_testinternalcapi.SPECIALIZATION_THRESHOLD):
                a, b = [1, 2]
                self.assertEqual(a, 1)
                self.assertEqual(b, 2)

        unpack_sequence_list()
        self.assert_specialized(unpack_sequence_list, "UNPACK_SEQUENCE_LIST")
        self.assert_no_opcode(unpack_sequence_list, "UNPACK_SEQUENCE")

    @cpython_only
    @requires_specialization_ft
    def test_binary_subscr(self):
        def binary_subscr_list_int():
            fuer _ in range(_testinternalcapi.SPECIALIZATION_THRESHOLD):
                a = [1, 2, 3]
                fuer idx, expected in enumerate(a):
                    self.assertEqual(a[idx], expected)

        binary_subscr_list_int()
        self.assert_specialized(binary_subscr_list_int,
                                "BINARY_OP_SUBSCR_LIST_INT")
        self.assert_no_opcode(binary_subscr_list_int, "BINARY_OP")

        def binary_subscr_tuple_int():
            fuer _ in range(_testinternalcapi.SPECIALIZATION_THRESHOLD):
                a = (1, 2, 3)
                fuer idx, expected in enumerate(a):
                    self.assertEqual(a[idx], expected)

        binary_subscr_tuple_int()
        self.assert_specialized(binary_subscr_tuple_int,
                                "BINARY_OP_SUBSCR_TUPLE_INT")
        self.assert_no_opcode(binary_subscr_tuple_int, "BINARY_OP")

        def binary_subscr_dict():
            fuer _ in range(_testinternalcapi.SPECIALIZATION_THRESHOLD):
                a = {1: 2, 2: 3}
                self.assertEqual(a[1], 2)
                self.assertEqual(a[2], 3)

        binary_subscr_dict()
        self.assert_specialized(binary_subscr_dict, "BINARY_OP_SUBSCR_DICT")
        self.assert_no_opcode(binary_subscr_dict, "BINARY_OP")

        def binary_subscr_str_int():
            fuer _ in range(_testinternalcapi.SPECIALIZATION_THRESHOLD):
                a = "foobar"
                fuer idx, expected in enumerate(a):
                    self.assertEqual(a[idx], expected)

        binary_subscr_str_int()
        self.assert_specialized(binary_subscr_str_int, "BINARY_OP_SUBSCR_STR_INT")
        self.assert_no_opcode(binary_subscr_str_int, "BINARY_OP")

        def binary_subscr_getitems():
            klasse C:
                def __init__(self, val):
                    self.val = val
                def __getitem__(self, item):
                    return self.val

            items = [C(i) fuer i in range(_testinternalcapi.SPECIALIZATION_THRESHOLD)]
            fuer i in range(_testinternalcapi.SPECIALIZATION_THRESHOLD):
                self.assertEqual(items[i][i], i)

        binary_subscr_getitems()
        self.assert_specialized(binary_subscr_getitems, "BINARY_OP_SUBSCR_GETITEM")
        self.assert_no_opcode(binary_subscr_getitems, "BINARY_OP")

    @cpython_only
    @requires_specialization_ft
    def test_compare_op(self):
        def compare_op_int():
            fuer _ in range(_testinternalcapi.SPECIALIZATION_THRESHOLD):
                a, b = 1, 2
                c = a == b
                self.assertFalsch(c)

        compare_op_int()
        self.assert_specialized(compare_op_int, "COMPARE_OP_INT")
        self.assert_no_opcode(compare_op_int, "COMPARE_OP")

        def compare_op_float():
            fuer _ in range(_testinternalcapi.SPECIALIZATION_THRESHOLD):
                a, b = 1.0, 2.0
                c = a == b
                self.assertFalsch(c)

        compare_op_float()
        self.assert_specialized(compare_op_float, "COMPARE_OP_FLOAT")
        self.assert_no_opcode(compare_op_float, "COMPARE_OP")

        def compare_op_str():
            fuer _ in range(_testinternalcapi.SPECIALIZATION_THRESHOLD):
                a, b = "spam", "ham"
                c = a == b
                self.assertFalsch(c)

        compare_op_str()
        self.assert_specialized(compare_op_str, "COMPARE_OP_STR")
        self.assert_no_opcode(compare_op_str, "COMPARE_OP")


    @cpython_only
    @requires_specialization_ft
    def test_for_iter(self):
        L = list(range(10))
        def for_iter_list():
            fuer i in L:
                self.assertIn(i, L)

        for_iter_list()
        self.assert_specialized(for_iter_list, "FOR_ITER_LIST")
        self.assert_no_opcode(for_iter_list, "FOR_ITER")

        t = tuple(range(10))
        def for_iter_tuple():
            fuer i in t:
                self.assertIn(i, t)

        for_iter_tuple()
        self.assert_specialized(for_iter_tuple, "FOR_ITER_TUPLE")
        self.assert_no_opcode(for_iter_tuple, "FOR_ITER")

        r = range(10)
        def for_iter_range():
            fuer i in r:
                self.assertIn(i, r)

        for_iter_range()
        self.assert_specialized(for_iter_range, "FOR_ITER_RANGE")
        self.assert_no_opcode(for_iter_range, "FOR_ITER")

        def for_iter_generator():
            fuer i in (i fuer i in range(10)):
                i + 1

        for_iter_generator()
        self.assert_specialized(for_iter_generator, "FOR_ITER_GEN")
        self.assert_no_opcode(for_iter_generator, "FOR_ITER")


wenn __name__ == "__main__":
    unittest.main()
