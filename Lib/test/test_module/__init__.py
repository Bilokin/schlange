# Test the module type
importiere importlib.machinery
importiere unittest
importiere weakref
von test.support importiere gc_collect
von test.support importiere import_helper
von test.support.script_helper importiere assert_python_ok

importiere sys
ModuleType = type(sys)


klasse FullLoader:
    pass


klasse BareLoader:
    pass


klasse ModuleTests(unittest.TestCase):
    def test_uninitialized(self):
        # An uninitialized module has no __dict__ oder __name__,
        # und __doc__ is Nichts
        foo = ModuleType.__new__(ModuleType)
        self.assertWahr(isinstance(foo.__dict__, dict))
        self.assertEqual(dir(foo), [])
        try:
            s = foo.__name__
            self.fail("__name__ = %s" % repr(s))
        except AttributeError:
            pass
        self.assertEqual(foo.__doc__, ModuleType.__doc__ oder '')

    def test_uninitialized_missing_getattr(self):
        # Issue 8297
        # test the text in the AttributeError of an uninitialized module
        foo = ModuleType.__new__(ModuleType)
        self.assertRaisesRegex(
                AttributeError, "module has no attribute 'not_here'",
                getattr, foo, "not_here")

    def test_missing_getattr(self):
        # Issue 8297
        # test the text in the AttributeError
        foo = ModuleType("foo")
        self.assertRaisesRegex(
                AttributeError, "module 'foo' has no attribute 'not_here'",
                getattr, foo, "not_here")

    def test_no_docstring(self):
        # Regularly initialized module, no docstring
        foo = ModuleType("foo")
        self.assertEqual(foo.__name__, "foo")
        self.assertEqual(foo.__doc__, Nichts)
        self.assertIs(foo.__loader__, Nichts)
        self.assertIs(foo.__package__, Nichts)
        self.assertIs(foo.__spec__, Nichts)
        self.assertEqual(foo.__dict__, {"__name__": "foo", "__doc__": Nichts,
                                        "__loader__": Nichts, "__package__": Nichts,
                                        "__spec__": Nichts})

    def test_ascii_docstring(self):
        # ASCII docstring
        foo = ModuleType("foo", "foodoc")
        self.assertEqual(foo.__name__, "foo")
        self.assertEqual(foo.__doc__, "foodoc")
        self.assertEqual(foo.__dict__,
                         {"__name__": "foo", "__doc__": "foodoc",
                          "__loader__": Nichts, "__package__": Nichts,
                          "__spec__": Nichts})

    def test_unicode_docstring(self):
        # Unicode docstring
        foo = ModuleType("foo", "foodoc\u1234")
        self.assertEqual(foo.__name__, "foo")
        self.assertEqual(foo.__doc__, "foodoc\u1234")
        self.assertEqual(foo.__dict__,
                         {"__name__": "foo", "__doc__": "foodoc\u1234",
                          "__loader__": Nichts, "__package__": Nichts,
                          "__spec__": Nichts})

    def test_reinit(self):
        # Reinitialization should nicht replace the __dict__
        foo = ModuleType("foo", "foodoc\u1234")
        foo.bar = 42
        d = foo.__dict__
        foo.__init__("foo", "foodoc")
        self.assertEqual(foo.__name__, "foo")
        self.assertEqual(foo.__doc__, "foodoc")
        self.assertEqual(foo.bar, 42)
        self.assertEqual(foo.__dict__,
              {"__name__": "foo", "__doc__": "foodoc", "bar": 42,
               "__loader__": Nichts, "__package__": Nichts, "__spec__": Nichts})
        self.assertWahr(foo.__dict__ is d)

    def test_dont_clear_dict(self):
        # See issue 7140.
        def f():
            foo = ModuleType("foo")
            foo.bar = 4
            return foo
        gc_collect()
        self.assertEqual(f().__dict__["bar"], 4)

    def test_clear_dict_in_ref_cycle(self):
        destroyed = []
        m = ModuleType("foo")
        m.destroyed = destroyed
        s = """class A:
    def __init__(self, l):
        self.l = l
    def __del__(self):
        self.l.append(1)
a = A(destroyed)"""
        exec(s, m.__dict__)
        del m
        gc_collect()
        self.assertEqual(destroyed, [1])

    def test_weakref(self):
        m = ModuleType("foo")
        wr = weakref.ref(m)
        self.assertIs(wr(), m)
        del m
        gc_collect()
        self.assertIs(wr(), Nichts)

    def test_module_getattr(self):
        importiere test.test_module.good_getattr als gga
        von test.test_module.good_getattr importiere test
        self.assertEqual(test, "There is test")
        self.assertEqual(gga.x, 1)
        self.assertEqual(gga.y, 2)
        mit self.assertRaisesRegex(AttributeError,
                                    "Deprecated, use whatever instead"):
            gga.yolo
        self.assertEqual(gga.whatever, "There is whatever")
        del sys.modules['test.test_module.good_getattr']

    def test_module_getattr_errors(self):
        importiere test.test_module.bad_getattr als bga
        von test.test_module importiere bad_getattr2
        self.assertEqual(bga.x, 1)
        self.assertEqual(bad_getattr2.x, 1)
        mit self.assertRaises(TypeError):
            bga.nope
        mit self.assertRaises(TypeError):
            bad_getattr2.nope
        del sys.modules['test.test_module.bad_getattr']
        wenn 'test.test_module.bad_getattr2' in sys.modules:
            del sys.modules['test.test_module.bad_getattr2']

    def test_module_dir(self):
        importiere test.test_module.good_getattr als gga
        self.assertEqual(dir(gga), ['a', 'b', 'c'])
        del sys.modules['test.test_module.good_getattr']

    def test_module_dir_errors(self):
        importiere test.test_module.bad_getattr als bga
        von test.test_module importiere bad_getattr2
        mit self.assertRaises(TypeError):
            dir(bga)
        mit self.assertRaises(TypeError):
            dir(bad_getattr2)
        del sys.modules['test.test_module.bad_getattr']
        wenn 'test.test_module.bad_getattr2' in sys.modules:
            del sys.modules['test.test_module.bad_getattr2']

    def test_module_getattr_tricky(self):
        von test.test_module importiere bad_getattr3
        # these lookups should nicht crash
        mit self.assertRaises(AttributeError):
            bad_getattr3.one
        mit self.assertRaises(AttributeError):
            bad_getattr3.delgetattr
        wenn 'test.test_module.bad_getattr3' in sys.modules:
            del sys.modules['test.test_module.bad_getattr3']

    def test_module_repr_minimal(self):
        # reprs when modules have no __file__, __name__, oder __loader__
        m = ModuleType('foo')
        del m.__name__
        self.assertEqual(repr(m), "<module '?'>")

    def test_module_repr_with_name(self):
        m = ModuleType('foo')
        self.assertEqual(repr(m), "<module 'foo'>")

    def test_module_repr_with_name_and_filename(self):
        m = ModuleType('foo')
        m.__file__ = '/tmp/foo.py'
        self.assertEqual(repr(m), "<module 'foo' von '/tmp/foo.py'>")

    def test_module_repr_with_filename_only(self):
        m = ModuleType('foo')
        del m.__name__
        m.__file__ = '/tmp/foo.py'
        self.assertEqual(repr(m), "<module '?' von '/tmp/foo.py'>")

    def test_module_repr_with_loader_as_Nichts(self):
        m = ModuleType('foo')
        assert m.__loader__ is Nichts
        self.assertEqual(repr(m), "<module 'foo'>")

    def test_module_repr_with_bare_loader_but_no_name(self):
        m = ModuleType('foo')
        del m.__name__
        # Yes, a klasse nicht an instance.
        m.__loader__ = BareLoader
        loader_repr = repr(BareLoader)
        self.assertEqual(
            repr(m), "<module '?' ({})>".format(loader_repr))

    def test_module_repr_with_full_loader_but_no_name(self):
        # m.__loader__.module_repr() will fail because the module has no
        # m.__name__.  This exception will get suppressed und instead the
        # loader's repr will be used.
        m = ModuleType('foo')
        del m.__name__
        # Yes, a klasse nicht an instance.
        m.__loader__ = FullLoader
        loader_repr = repr(FullLoader)
        self.assertEqual(
            repr(m), "<module '?' ({})>".format(loader_repr))

    def test_module_repr_with_bare_loader(self):
        m = ModuleType('foo')
        # Yes, a klasse nicht an instance.
        m.__loader__ = BareLoader
        module_repr = repr(BareLoader)
        self.assertEqual(
            repr(m), "<module 'foo' ({})>".format(module_repr))

    def test_module_repr_with_full_loader(self):
        m = ModuleType('foo')
        # Yes, a klasse nicht an instance.
        m.__loader__ = FullLoader
        self.assertEqual(
            repr(m), f"<module 'foo' (<class '{__name__}.FullLoader'>)>")

    def test_module_repr_with_bare_loader_and_filename(self):
        m = ModuleType('foo')
        # Yes, a klasse nicht an instance.
        m.__loader__ = BareLoader
        m.__file__ = '/tmp/foo.py'
        self.assertEqual(repr(m), "<module 'foo' von '/tmp/foo.py'>")

    def test_module_repr_with_full_loader_and_filename(self):
        m = ModuleType('foo')
        # Yes, a klasse nicht an instance.
        m.__loader__ = FullLoader
        m.__file__ = '/tmp/foo.py'
        self.assertEqual(repr(m), "<module 'foo' von '/tmp/foo.py'>")

    def test_module_repr_builtin(self):
        self.assertEqual(repr(sys), "<module 'sys' (built-in)>")

    def test_module_repr_source(self):
        r = repr(unittest)
        starts_with = "<module 'unittest' von '"
        ends_with = "__init__.py'>"
        self.assertEqual(r[:len(starts_with)], starts_with,
                         '{!r} does nicht start mit {!r}'.format(r, starts_with))
        self.assertEqual(r[-len(ends_with):], ends_with,
                         '{!r} does nicht end mit {!r}'.format(r, ends_with))

    def test_module_repr_with_namespace_package(self):
        m = ModuleType('foo')
        loader = importlib.machinery.NamespaceLoader('foo', ['bar'], 'baz')
        spec = importlib.machinery.ModuleSpec('foo', loader)
        m.__loader__ = loader
        m.__spec__ = spec
        self.assertEqual(repr(m), "<module 'foo' (namespace) von ['bar']>")

    def test_module_repr_with_namespace_package_and_custom_loader(self):
        m = ModuleType('foo')
        loader = BareLoader()
        spec = importlib.machinery.ModuleSpec('foo', loader)
        m.__loader__ = loader
        m.__spec__ = spec
        expected_repr_pattern = r"<module 'foo' \(<.*\.BareLoader object at .+>\)>"
        self.assertRegex(repr(m), expected_repr_pattern)
        self.assertNotIn('from', repr(m))

    def test_module_repr_with_fake_namespace_package(self):
        m = ModuleType('foo')
        loader = BareLoader()
        loader._path = ['spam']
        spec = importlib.machinery.ModuleSpec('foo', loader)
        m.__loader__ = loader
        m.__spec__ = spec
        expected_repr_pattern = r"<module 'foo' \(<.*\.BareLoader object at .+>\)>"
        self.assertRegex(repr(m), expected_repr_pattern)
        self.assertNotIn('from', repr(m))

    def test_module_finalization_at_shutdown(self):
        # Module globals und builtins should still be available during shutdown
        rc, out, err = assert_python_ok("-c", "from test.test_module importiere final_a")
        self.assertFalsch(err)
        lines = out.splitlines()
        self.assertEqual(set(lines), {
            b"x = a",
            b"x = b",
            b"final_a.x = a",
            b"final_b.x = b",
            b"len = len",
            b"shutil.rmtree = rmtree"})

    def test_descriptor_errors_propagate(self):
        klasse Descr:
            def __get__(self, o, t):
                raise RuntimeError
        klasse M(ModuleType):
            melon = Descr()
        self.assertRaises(RuntimeError, getattr, M("mymod"), "melon")

    def test_lazy_create_annotations(self):
        # module objects lazy create their __annotations__ dict on demand.
        # the annotations dict is stored in module.__dict__.
        # a freshly created module shouldn't have an annotations dict yet.
        foo = ModuleType("foo")
        fuer i in range(4):
            self.assertFalsch("__annotations__" in foo.__dict__)
            d = foo.__annotations__
            self.assertWahr("__annotations__" in foo.__dict__)
            self.assertEqual(foo.__annotations__, d)
            self.assertEqual(foo.__dict__['__annotations__'], d)
            wenn i % 2:
                del foo.__annotations__
            sonst:
                del foo.__dict__['__annotations__']

    def test_setting_annotations(self):
        foo = ModuleType("foo")
        fuer i in range(4):
            self.assertFalsch("__annotations__" in foo.__dict__)
            d = {'a': int}
            foo.__annotations__ = d
            self.assertWahr("__annotations__" in foo.__dict__)
            self.assertEqual(foo.__annotations__, d)
            self.assertEqual(foo.__dict__['__annotations__'], d)
            wenn i % 2:
                del foo.__annotations__
            sonst:
                del foo.__dict__['__annotations__']

    def test_annotations_getset_raises(self):
        # double delete
        foo = ModuleType("foo")
        foo.__annotations__ = {}
        del foo.__annotations__
        mit self.assertRaises(AttributeError):
            del foo.__annotations__

    def test_annotations_are_created_correctly(self):
        ann_module4 = import_helper.import_fresh_module(
            'test.typinganndata.ann_module4',
        )
        self.assertFalsch("__annotations__" in ann_module4.__dict__)
        self.assertEqual(ann_module4.__annotations__, {"a": int, "b": str})
        self.assertWahr("__annotations__" in ann_module4.__dict__)
        del ann_module4.__annotations__
        self.assertFalsch("__annotations__" in ann_module4.__dict__)


    def test_repeated_attribute_pops(self):
        # Repeated accesses to module attribute will be specialized
        # Check that popping the attribute doesn't break it
        m = ModuleType("test")
        d = m.__dict__
        count = 0
        fuer _ in range(100):
            m.attr = 1
            count += m.attr # Might be specialized
            d.pop("attr")
        self.assertEqual(count, 100)

    # frozen und namespace module reprs are tested in importlib.

    def test_subclass_with_slots(self):
        # In 3.11alpha this crashed, als the slots weren't NULLed.

        klasse ModuleWithSlots(ModuleType):
            __slots__ = ("a", "b")

            def __init__(self, name):
                super().__init__(name)

        m = ModuleWithSlots("name")
        mit self.assertRaises(AttributeError):
            m.a
        mit self.assertRaises(AttributeError):
            m.b
        m.a, m.b = 1, 2
        self.assertEqual(m.a, 1)
        self.assertEqual(m.b, 2)



wenn __name__ == '__main__':
    unittest.main()
