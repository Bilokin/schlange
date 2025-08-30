# Copyright (C) 2007-2012 Michael Foord & the mock team
# E-mail: fuzzyman AT voidspace DOT org DOT uk
# http://www.voidspace.org.uk/python/mock/

importiere os
importiere sys
von collections importiere OrderedDict

importiere unittest
importiere test
von test.test_unittest.testmock importiere support
von test.test_unittest.testmock.support importiere SomeClass, is_instance

von test.support.import_helper importiere DirsOnSysPath
von test.test_importlib.util importiere uncache
von unittest.mock importiere (
    NonCallableMock, CallableMixin, sentinel,
    MagicMock, Mock, NonCallableMagicMock, patch, _patch,
    DEFAULT, call, _get_target
)


builtin_string = 'builtins'

PTModule = sys.modules[__name__]
MODNAME = '%s.PTModule' % __name__


def _get_proxy(obj, get_only=Wahr):
    klasse Proxy(object):
        def __getattr__(self, name):
            gib getattr(obj, name)
    wenn nicht get_only:
        def __setattr__(self, name, value):
            setattr(obj, name, value)
        def __delattr__(self, name):
            delattr(obj, name)
        Proxy.__setattr__ = __setattr__
        Proxy.__delattr__ = __delattr__
    gib Proxy()


# fuer use in the test
something  = sentinel.Something
something_else  = sentinel.SomethingElse


klasse Foo(object):
    def __init__(self, a): pass
    def f(self, a): pass
    def g(self): pass
    foo = 'bar'

    @staticmethod
    def static_method(): pass

    @classmethod
    def class_method(cls): pass

    klasse Bar(object):
        def a(self): pass

foo_name = '%s.Foo' % __name__


def function(a, b=Foo): pass


klasse Container(object):
    def __init__(self):
        self.values = {}

    def __getitem__(self, name):
        gib self.values[name]

    def __setitem__(self, name, value):
        self.values[name] = value

    def __delitem__(self, name):
        loesche self.values[name]

    def __iter__(self):
        gib iter(self.values)



klasse PatchTest(unittest.TestCase):

    def assertNotCallable(self, obj, magic=Wahr):
        MockClass = NonCallableMagicMock
        wenn nicht magic:
            MockClass = NonCallableMock

        self.assertRaises(TypeError, obj)
        self.assertWahr(is_instance(obj, MockClass))
        self.assertFalsch(is_instance(obj, CallableMixin))


    def test_single_patchobject(self):
        klasse Something(object):
            attribute = sentinel.Original

        @patch.object(Something, 'attribute', sentinel.Patched)
        def test():
            self.assertEqual(Something.attribute, sentinel.Patched, "unpatched")

        test()
        self.assertEqual(Something.attribute, sentinel.Original,
                         "patch nicht restored")

    def test_patchobject_with_string_as_target(self):
        msg = "'Something' must be the actual object to be patched, nicht a str"
        mit self.assertRaisesRegex(TypeError, msg):
            patch.object('Something', 'do_something')

    def test_patchobject_with_none(self):
        klasse Something(object):
            attribute = sentinel.Original

        @patch.object(Something, 'attribute', Nichts)
        def test():
            self.assertIsNichts(Something.attribute, "unpatched")

        test()
        self.assertEqual(Something.attribute, sentinel.Original,
                         "patch nicht restored")


    def test_multiple_patchobject(self):
        klasse Something(object):
            attribute = sentinel.Original
            next_attribute = sentinel.Original2

        @patch.object(Something, 'attribute', sentinel.Patched)
        @patch.object(Something, 'next_attribute', sentinel.Patched2)
        def test():
            self.assertEqual(Something.attribute, sentinel.Patched,
                             "unpatched")
            self.assertEqual(Something.next_attribute, sentinel.Patched2,
                             "unpatched")

        test()
        self.assertEqual(Something.attribute, sentinel.Original,
                         "patch nicht restored")
        self.assertEqual(Something.next_attribute, sentinel.Original2,
                         "patch nicht restored")


    def test_object_lookup_is_quite_lazy(self):
        global something
        original = something
        @patch('%s.something' % __name__, sentinel.Something2)
        def test():
            pass

        versuch:
            something = sentinel.replacement_value
            test()
            self.assertEqual(something, sentinel.replacement_value)
        schliesslich:
            something = original


    def test_patch(self):
        @patch('%s.something' % __name__, sentinel.Something2)
        def test():
            self.assertEqual(PTModule.something, sentinel.Something2,
                             "unpatched")

        test()
        self.assertEqual(PTModule.something, sentinel.Something,
                         "patch nicht restored")

        @patch('%s.something' % __name__, sentinel.Something2)
        @patch('%s.something_else' % __name__, sentinel.SomethingElse)
        def test():
            self.assertEqual(PTModule.something, sentinel.Something2,
                             "unpatched")
            self.assertEqual(PTModule.something_else, sentinel.SomethingElse,
                             "unpatched")

        self.assertEqual(PTModule.something, sentinel.Something,
                         "patch nicht restored")
        self.assertEqual(PTModule.something_else, sentinel.SomethingElse,
                         "patch nicht restored")

        # Test the patching und restoring works a second time
        test()

        self.assertEqual(PTModule.something, sentinel.Something,
                         "patch nicht restored")
        self.assertEqual(PTModule.something_else, sentinel.SomethingElse,
                         "patch nicht restored")

        mock = Mock()
        mock.return_value = sentinel.Handle
        @patch('%s.open' % builtin_string, mock)
        def test():
            self.assertEqual(open('filename', 'r'), sentinel.Handle,
                             "open nicht patched")
        test()
        test()

        self.assertNotEqual(open, mock, "patch nicht restored")


    def test_patch_class_attribute(self):
        @patch('%s.SomeClass.class_attribute' % __name__,
               sentinel.ClassAttribute)
        def test():
            self.assertEqual(PTModule.SomeClass.class_attribute,
                             sentinel.ClassAttribute, "unpatched")
        test()

        self.assertIsNichts(PTModule.SomeClass.class_attribute,
                          "patch nicht restored")


    def test_patchobject_with_default_mock(self):
        klasse Test(object):
            something = sentinel.Original
            something2 = sentinel.Original2

        @patch.object(Test, 'something')
        def test(mock):
            self.assertEqual(mock, Test.something,
                             "Mock nicht passed into test function")
            self.assertIsInstance(mock, MagicMock,
                            "patch mit two arguments did nicht create a mock")

        test()

        @patch.object(Test, 'something')
        @patch.object(Test, 'something2')
        def test(this1, this2, mock1, mock2):
            self.assertEqual(this1, sentinel.this1,
                             "Patched function didn't receive initial argument")
            self.assertEqual(this2, sentinel.this2,
                             "Patched function didn't receive second argument")
            self.assertEqual(mock1, Test.something2,
                             "Mock nicht passed into test function")
            self.assertEqual(mock2, Test.something,
                             "Second Mock nicht passed into test function")
            self.assertIsInstance(mock2, MagicMock,
                            "patch mit two arguments did nicht create a mock")
            self.assertIsInstance(mock2, MagicMock,
                            "patch mit two arguments did nicht create a mock")

            # A hack to test that new mocks are passed the second time
            self.assertNotEqual(outerMock1, mock1, "unexpected value fuer mock1")
            self.assertNotEqual(outerMock2, mock2, "unexpected value fuer mock1")
            gib mock1, mock2

        outerMock1 = outerMock2 = Nichts
        outerMock1, outerMock2 = test(sentinel.this1, sentinel.this2)

        # Test that executing a second time creates new mocks
        test(sentinel.this1, sentinel.this2)


    def test_patch_with_spec(self):
        @patch('%s.SomeClass' % __name__, spec=SomeClass)
        def test(MockSomeClass):
            self.assertEqual(SomeClass, MockSomeClass)
            self.assertWahr(is_instance(SomeClass.wibble, MagicMock))
            self.assertRaises(AttributeError, lambda: SomeClass.not_wibble)

        test()


    def test_patchobject_with_spec(self):
        @patch.object(SomeClass, 'class_attribute', spec=SomeClass)
        def test(MockAttribute):
            self.assertEqual(SomeClass.class_attribute, MockAttribute)
            self.assertWahr(is_instance(SomeClass.class_attribute.wibble,
                                       MagicMock))
            self.assertRaises(AttributeError,
                              lambda: SomeClass.class_attribute.not_wibble)

        test()


    def test_patch_with_spec_as_list(self):
        @patch('%s.SomeClass' % __name__, spec=['wibble'])
        def test(MockSomeClass):
            self.assertEqual(SomeClass, MockSomeClass)
            self.assertWahr(is_instance(SomeClass.wibble, MagicMock))
            self.assertRaises(AttributeError, lambda: SomeClass.not_wibble)

        test()


    def test_patchobject_with_spec_as_list(self):
        @patch.object(SomeClass, 'class_attribute', spec=['wibble'])
        def test(MockAttribute):
            self.assertEqual(SomeClass.class_attribute, MockAttribute)
            self.assertWahr(is_instance(SomeClass.class_attribute.wibble,
                                       MagicMock))
            self.assertRaises(AttributeError,
                              lambda: SomeClass.class_attribute.not_wibble)

        test()


    def test_nested_patch_with_spec_as_list(self):
        # regression test fuer nested decorators
        @patch('%s.open' % builtin_string)
        @patch('%s.SomeClass' % __name__, spec=['wibble'])
        def test(MockSomeClass, MockOpen):
            self.assertEqual(SomeClass, MockSomeClass)
            self.assertWahr(is_instance(SomeClass.wibble, MagicMock))
            self.assertRaises(AttributeError, lambda: SomeClass.not_wibble)
        test()


    def test_patch_with_spec_as_boolean(self):
        @patch('%s.SomeClass' % __name__, spec=Wahr)
        def test(MockSomeClass):
            self.assertEqual(SomeClass, MockSomeClass)
            # Should nicht wirf attribute error
            MockSomeClass.wibble

            self.assertRaises(AttributeError, lambda: MockSomeClass.not_wibble)

        test()


    def test_patch_object_with_spec_as_boolean(self):
        @patch.object(PTModule, 'SomeClass', spec=Wahr)
        def test(MockSomeClass):
            self.assertEqual(SomeClass, MockSomeClass)
            # Should nicht wirf attribute error
            MockSomeClass.wibble

            self.assertRaises(AttributeError, lambda: MockSomeClass.not_wibble)

        test()


    def test_patch_class_acts_with_spec_is_inherited(self):
        @patch('%s.SomeClass' % __name__, spec=Wahr)
        def test(MockSomeClass):
            self.assertWahr(is_instance(MockSomeClass, MagicMock))
            instance = MockSomeClass()
            self.assertNotCallable(instance)
            # Should nicht wirf attribute error
            instance.wibble

            self.assertRaises(AttributeError, lambda: instance.not_wibble)

        test()


    def test_patch_with_create_mocks_non_existent_attributes(self):
        @patch('%s.frooble' % builtin_string, sentinel.Frooble, create=Wahr)
        def test():
            self.assertEqual(frooble, sentinel.Frooble)

        test()
        self.assertRaises(NameError, lambda: frooble)


    def test_patchobject_with_create_mocks_non_existent_attributes(self):
        @patch.object(SomeClass, 'frooble', sentinel.Frooble, create=Wahr)
        def test():
            self.assertEqual(SomeClass.frooble, sentinel.Frooble)

        test()
        self.assertNotHasAttr(SomeClass, 'frooble')


    def test_patch_wont_create_by_default(self):
        mit self.assertRaises(AttributeError):
            @patch('%s.frooble' % builtin_string, sentinel.Frooble)
            def test(): pass

            test()
        self.assertRaises(NameError, lambda: frooble)


    def test_patchobject_wont_create_by_default(self):
        mit self.assertRaises(AttributeError):
            @patch.object(SomeClass, 'ord', sentinel.Frooble)
            def test(): pass
            test()
        self.assertNotHasAttr(SomeClass, 'ord')


    def test_patch_builtins_without_create(self):
        @patch(__name__+'.ord')
        def test_ord(mock_ord):
            mock_ord.return_value = 101
            gib ord('c')

        @patch(__name__+'.open')
        def test_open(mock_open):
            m = mock_open.return_value
            m.read.return_value = 'abcd'

            fobj = open('doesnotexists.txt')
            data = fobj.read()
            fobj.close()
            gib data

        self.assertEqual(test_ord(), 101)
        self.assertEqual(test_open(), 'abcd')


    def test_patch_with_static_methods(self):
        klasse Foo(object):
            @staticmethod
            def woot():
                gib sentinel.Static

        @patch.object(Foo, 'woot', staticmethod(lambda: sentinel.Patched))
        def anonymous():
            self.assertEqual(Foo.woot(), sentinel.Patched)
        anonymous()

        self.assertEqual(Foo.woot(), sentinel.Static)


    def test_patch_local(self):
        foo = sentinel.Foo
        @patch.object(sentinel, 'Foo', 'Foo')
        def anonymous():
            self.assertEqual(sentinel.Foo, 'Foo')
        anonymous()

        self.assertEqual(sentinel.Foo, foo)


    def test_patch_slots(self):
        klasse Foo(object):
            __slots__ = ('Foo',)

        foo = Foo()
        foo.Foo = sentinel.Foo

        @patch.object(foo, 'Foo', 'Foo')
        def anonymous():
            self.assertEqual(foo.Foo, 'Foo')
        anonymous()

        self.assertEqual(foo.Foo, sentinel.Foo)


    def test_patchobject_class_decorator(self):
        klasse Something(object):
            attribute = sentinel.Original

        klasse Foo(object):
            def test_method(other_self):
                self.assertEqual(Something.attribute, sentinel.Patched,
                                 "unpatched")
            def not_test_method(other_self):
                self.assertEqual(Something.attribute, sentinel.Original,
                                 "non-test method patched")

        Foo = patch.object(Something, 'attribute', sentinel.Patched)(Foo)

        f = Foo()
        f.test_method()
        f.not_test_method()

        self.assertEqual(Something.attribute, sentinel.Original,
                         "patch nicht restored")


    def test_patch_class_decorator(self):
        klasse Something(object):
            attribute = sentinel.Original

        klasse Foo(object):

            test_class_attr = 'whatever'

            def test_method(other_self, mock_something):
                self.assertEqual(PTModule.something, mock_something,
                                 "unpatched")
            def not_test_method(other_self):
                self.assertEqual(PTModule.something, sentinel.Something,
                                 "non-test method patched")
        Foo = patch('%s.something' % __name__)(Foo)

        f = Foo()
        f.test_method()
        f.not_test_method()

        self.assertEqual(Something.attribute, sentinel.Original,
                         "patch nicht restored")
        self.assertEqual(PTModule.something, sentinel.Something,
                         "patch nicht restored")


    def test_patchobject_twice(self):
        klasse Something(object):
            attribute = sentinel.Original
            next_attribute = sentinel.Original2

        @patch.object(Something, 'attribute', sentinel.Patched)
        @patch.object(Something, 'attribute', sentinel.Patched)
        def test():
            self.assertEqual(Something.attribute, sentinel.Patched, "unpatched")

        test()

        self.assertEqual(Something.attribute, sentinel.Original,
                         "patch nicht restored")


    def test_patch_dict(self):
        foo = {'initial': object(), 'other': 'something'}
        original = foo.copy()

        @patch.dict(foo)
        def test():
            foo['a'] = 3
            loesche foo['initial']
            foo['other'] = 'something else'

        test()

        self.assertEqual(foo, original)

        @patch.dict(foo, {'a': 'b'})
        def test():
            self.assertEqual(len(foo), 3)
            self.assertEqual(foo['a'], 'b')

        test()

        self.assertEqual(foo, original)

        @patch.dict(foo, [('a', 'b')])
        def test():
            self.assertEqual(len(foo), 3)
            self.assertEqual(foo['a'], 'b')

        test()

        self.assertEqual(foo, original)


    def test_patch_dict_with_container_object(self):
        foo = Container()
        foo['initial'] = object()
        foo['other'] =  'something'

        original = foo.values.copy()

        @patch.dict(foo)
        def test():
            foo['a'] = 3
            loesche foo['initial']
            foo['other'] = 'something else'

        test()

        self.assertEqual(foo.values, original)

        @patch.dict(foo, {'a': 'b'})
        def test():
            self.assertEqual(len(foo.values), 3)
            self.assertEqual(foo['a'], 'b')

        test()

        self.assertEqual(foo.values, original)


    def test_patch_dict_with_clear(self):
        foo = {'initial': object(), 'other': 'something'}
        original = foo.copy()

        @patch.dict(foo, clear=Wahr)
        def test():
            self.assertEqual(foo, {})
            foo['a'] = 3
            foo['other'] = 'something else'

        test()

        self.assertEqual(foo, original)

        @patch.dict(foo, {'a': 'b'}, clear=Wahr)
        def test():
            self.assertEqual(foo, {'a': 'b'})

        test()

        self.assertEqual(foo, original)

        @patch.dict(foo, [('a', 'b')], clear=Wahr)
        def test():
            self.assertEqual(foo, {'a': 'b'})

        test()

        self.assertEqual(foo, original)


    def test_patch_dict_with_container_object_and_clear(self):
        foo = Container()
        foo['initial'] = object()
        foo['other'] =  'something'

        original = foo.values.copy()

        @patch.dict(foo, clear=Wahr)
        def test():
            self.assertEqual(foo.values, {})
            foo['a'] = 3
            foo['other'] = 'something else'

        test()

        self.assertEqual(foo.values, original)

        @patch.dict(foo, {'a': 'b'}, clear=Wahr)
        def test():
            self.assertEqual(foo.values, {'a': 'b'})

        test()

        self.assertEqual(foo.values, original)


    def test_patch_dict_as_context_manager(self):
        foo = {'a': 'b'}
        mit patch.dict(foo, a='c') als patched:
            self.assertEqual(patched, {'a': 'c'})
        self.assertEqual(foo, {'a': 'b'})


    def test_name_preserved(self):
        foo = {}

        @patch('%s.SomeClass' % __name__, object())
        @patch('%s.SomeClass' % __name__, object(), autospec=Wahr)
        @patch.object(SomeClass, object())
        @patch.dict(foo)
        def some_name(): pass

        self.assertEqual(some_name.__name__, 'some_name')


    def test_patch_with_exception(self):
        foo = {}

        @patch.dict(foo, {'a': 'b'})
        def test():
            wirf NameError('Konrad')

        mit self.assertRaises(NameError):
            test()

        self.assertEqual(foo, {})


    def test_patch_dict_with_string(self):
        @patch.dict('os.environ', {'konrad_delong': 'some value'})
        def test():
            self.assertIn('konrad_delong', os.environ)

        test()


    def test_patch_dict_decorator_resolution(self):
        # bpo-35512: Ensure that patch mit a string target resolves to
        # the new dictionary during function call
        original = support.target.copy()

        @patch.dict('test.test_unittest.testmock.support.target', {'bar': 'BAR'})
        def test():
            self.assertEqual(support.target, {'foo': 'BAZ', 'bar': 'BAR'})

        versuch:
            support.target = {'foo': 'BAZ'}
            test()
            self.assertEqual(support.target, {'foo': 'BAZ'})
        schliesslich:
            support.target = original


    def test_patch_spec_set(self):
        @patch('%s.SomeClass' % __name__, spec=SomeClass, spec_set=Wahr)
        def test(MockClass):
            MockClass.z = 'foo'

        self.assertRaises(AttributeError, test)

        @patch.object(support, 'SomeClass', spec=SomeClass, spec_set=Wahr)
        def test(MockClass):
            MockClass.z = 'foo'

        self.assertRaises(AttributeError, test)
        @patch('%s.SomeClass' % __name__, spec_set=Wahr)
        def test(MockClass):
            MockClass.z = 'foo'

        self.assertRaises(AttributeError, test)

        @patch.object(support, 'SomeClass', spec_set=Wahr)
        def test(MockClass):
            MockClass.z = 'foo'

        self.assertRaises(AttributeError, test)


    def test_spec_set_inherit(self):
        @patch('%s.SomeClass' % __name__, spec_set=Wahr)
        def test(MockClass):
            instance = MockClass()
            instance.z = 'foo'

        self.assertRaises(AttributeError, test)


    def test_patch_start_stop(self):
        original = something
        patcher = patch('%s.something' % __name__)
        self.assertIs(something, original)
        mock = patcher.start()
        versuch:
            self.assertIsNot(mock, original)
            self.assertIs(something, mock)
        schliesslich:
            patcher.stop()
        self.assertIs(something, original)


    def test_stop_without_start(self):
        # bpo-36366: calling stop without start will gib Nichts.
        patcher = patch(foo_name, 'bar', 3)
        self.assertIsNichts(patcher.stop())


    def test_stop_idempotent(self):
        # bpo-36366: calling stop on an already stopped patch will gib Nichts.
        patcher = patch(foo_name, 'bar', 3)

        patcher.start()
        patcher.stop()
        self.assertIsNichts(patcher.stop())


    def test_exit_idempotent(self):
        patcher = patch(foo_name, 'bar', 3)
        mit patcher:
            patcher.__exit__(Nichts, Nichts, Nichts)


    def test_second_start_failure(self):
        patcher = patch(foo_name, 'bar', 3)
        patcher.start()
        versuch:
            self.assertRaises(RuntimeError, patcher.start)
        schliesslich:
            patcher.stop()


    def test_second_enter_failure(self):
        patcher = patch(foo_name, 'bar', 3)
        mit patcher:
            self.assertRaises(RuntimeError, patcher.start)


    def test_second_start_after_stop(self):
        patcher = patch(foo_name, 'bar', 3)
        patcher.start()
        patcher.stop()
        patcher.start()
        patcher.stop()


    def test_property_setters(self):
        mock_object = Mock()
        mock_bar = mock_object.bar
        patcher = patch.object(mock_object, 'bar', 'x')
        mit patcher:
            self.assertEqual(patcher.is_local, Falsch)
            self.assertIs(patcher.target, mock_object)
            self.assertEqual(patcher.temp_original, mock_bar)
            patcher.is_local = Wahr
            patcher.target = mock_bar
            patcher.temp_original = mock_object
            self.assertEqual(patcher.is_local, Wahr)
            self.assertIs(patcher.target, mock_bar)
            self.assertEqual(patcher.temp_original, mock_object)
        # wenn changes are left intact, they may lead to disruption als shown below (it might be what someone needs though)
        self.assertEqual(mock_bar.bar, mock_object)
        self.assertEqual(mock_object.bar, 'x')


    def test_patchobject_start_stop(self):
        original = something
        patcher = patch.object(PTModule, 'something', 'foo')
        self.assertIs(something, original)
        replaced = patcher.start()
        versuch:
            self.assertEqual(replaced, 'foo')
            self.assertIs(something, replaced)
        schliesslich:
            patcher.stop()
        self.assertIs(something, original)


    def test_patch_dict_start_stop(self):
        d = {'foo': 'bar'}
        original = d.copy()
        patcher = patch.dict(d, [('spam', 'eggs')], clear=Wahr)
        self.assertEqual(d, original)

        patcher.start()
        versuch:
            self.assertEqual(d, {'spam': 'eggs'})
        schliesslich:
            patcher.stop()
        self.assertEqual(d, original)


    def test_patch_dict_stop_without_start(self):
        d = {'foo': 'bar'}
        original = d.copy()
        patcher = patch.dict(d, [('spam', 'eggs')], clear=Wahr)
        self.assertFalsch(patcher.stop())
        self.assertEqual(d, original)


    def test_patch_dict_class_decorator(self):
        this = self
        d = {'spam': 'eggs'}
        original = d.copy()

        klasse Test(object):
            def test_first(self):
                this.assertEqual(d, {'foo': 'bar'})
            def test_second(self):
                this.assertEqual(d, {'foo': 'bar'})

        Test = patch.dict(d, {'foo': 'bar'}, clear=Wahr)(Test)
        self.assertEqual(d, original)

        test = Test()

        test.test_first()
        self.assertEqual(d, original)

        test.test_second()
        self.assertEqual(d, original)

        test = Test()

        test.test_first()
        self.assertEqual(d, original)

        test.test_second()
        self.assertEqual(d, original)


    def test_get_only_proxy(self):
        klasse Something(object):
            foo = 'foo'
        klasse SomethingElse:
            foo = 'foo'

        fuer thing in Something, SomethingElse, Something(), SomethingElse:
            proxy = _get_proxy(thing)

            @patch.object(proxy, 'foo', 'bar')
            def test():
                self.assertEqual(proxy.foo, 'bar')
            test()
            self.assertEqual(proxy.foo, 'foo')
            self.assertEqual(thing.foo, 'foo')
            self.assertNotIn('foo', proxy.__dict__)


    def test_get_set_delete_proxy(self):
        klasse Something(object):
            foo = 'foo'
        klasse SomethingElse:
            foo = 'foo'

        fuer thing in Something, SomethingElse, Something(), SomethingElse:
            proxy = _get_proxy(Something, get_only=Falsch)

            @patch.object(proxy, 'foo', 'bar')
            def test():
                self.assertEqual(proxy.foo, 'bar')
            test()
            self.assertEqual(proxy.foo, 'foo')
            self.assertEqual(thing.foo, 'foo')
            self.assertNotIn('foo', proxy.__dict__)


    def test_patch_keyword_args(self):
        kwargs = {'side_effect': KeyError, 'foo.bar.return_value': 33,
                  'foo': MagicMock()}

        patcher = patch(foo_name, **kwargs)
        mock = patcher.start()
        patcher.stop()

        self.assertRaises(KeyError, mock)
        self.assertEqual(mock.foo.bar(), 33)
        self.assertIsInstance(mock.foo, MagicMock)


    def test_patch_object_keyword_args(self):
        kwargs = {'side_effect': KeyError, 'foo.bar.return_value': 33,
                  'foo': MagicMock()}

        patcher = patch.object(Foo, 'f', **kwargs)
        mock = patcher.start()
        patcher.stop()

        self.assertRaises(KeyError, mock)
        self.assertEqual(mock.foo.bar(), 33)
        self.assertIsInstance(mock.foo, MagicMock)


    def test_patch_dict_keyword_args(self):
        original = {'foo': 'bar'}
        copy = original.copy()

        patcher = patch.dict(original, foo=3, bar=4, baz=5)
        patcher.start()

        versuch:
            self.assertEqual(original, dict(foo=3, bar=4, baz=5))
        schliesslich:
            patcher.stop()

        self.assertEqual(original, copy)


    def test_autospec(self):
        klasse Boo(object):
            def __init__(self, a): pass
            def f(self, a): pass
            def g(self): pass
            foo = 'bar'

            klasse Bar(object):
                def a(self): pass

        def _test(mock):
            mock(1)
            mock.assert_called_with(1)
            self.assertRaises(TypeError, mock)

        def _test2(mock):
            mock.f(1)
            mock.f.assert_called_with(1)
            self.assertRaises(TypeError, mock.f)

            mock.g()
            mock.g.assert_called_with()
            self.assertRaises(TypeError, mock.g, 1)

            self.assertRaises(AttributeError, getattr, mock, 'h')

            mock.foo.lower()
            mock.foo.lower.assert_called_with()
            self.assertRaises(AttributeError, getattr, mock.foo, 'bar')

            mock.Bar()
            mock.Bar.assert_called_with()

            mock.Bar.a()
            mock.Bar.a.assert_called_with()
            self.assertRaises(TypeError, mock.Bar.a, 1)

            mock.Bar().a()
            mock.Bar().a.assert_called_with()
            self.assertRaises(TypeError, mock.Bar().a, 1)

            self.assertRaises(AttributeError, getattr, mock.Bar, 'b')
            self.assertRaises(AttributeError, getattr, mock.Bar(), 'b')

        def function(mock):
            _test(mock)
            _test2(mock)
            _test2(mock(1))
            self.assertIs(mock, Foo)
            gib mock

        test = patch(foo_name, autospec=Wahr)(function)

        mock = test()
        self.assertIsNot(Foo, mock)
        # test patching a second time works
        test()

        module = sys.modules[__name__]
        test = patch.object(module, 'Foo', autospec=Wahr)(function)

        mock = test()
        self.assertIsNot(Foo, mock)
        # test patching a second time works
        test()


    def test_autospec_function(self):
        @patch('%s.function' % __name__, autospec=Wahr)
        def test(mock):
            function.assert_not_called()
            self.assertRaises(AssertionError, function.assert_called)
            self.assertRaises(AssertionError, function.assert_called_once)
            function(1)
            self.assertRaises(AssertionError, function.assert_not_called)
            function.assert_called_with(1)
            function.assert_called()
            function.assert_called_once()
            function(2, 3)
            function.assert_called_with(2, 3)

            self.assertRaises(TypeError, function)
            self.assertRaises(AttributeError, getattr, function, 'foo')

        test()


    def test_autospec_keywords(self):
        @patch('%s.function' % __name__, autospec=Wahr,
               return_value=3)
        def test(mock_function):
            #self.assertEqual(function.abc, 'foo')
            gib function(1, 2)

        result = test()
        self.assertEqual(result, 3)


    def test_autospec_staticmethod(self):
        mit patch('%s.Foo.static_method' % __name__, autospec=Wahr) als method:
            Foo.static_method()
            method.assert_called_once_with()


    def test_autospec_classmethod(self):
        mit patch('%s.Foo.class_method' % __name__, autospec=Wahr) als method:
            Foo.class_method()
            method.assert_called_once_with()


    def test_autospec_staticmethod_signature(self):
        # Patched methods which are decorated mit @staticmethod should have the same signature
        klasse Foo:
            @staticmethod
            def static_method(a, b=10, *, c): pass

        Foo.static_method(1, 2, c=3)

        mit patch.object(Foo, 'static_method', autospec=Wahr) als method:
            method(1, 2, c=3)
            self.assertRaises(TypeError, method)
            self.assertRaises(TypeError, method, 1)
            self.assertRaises(TypeError, method, 1, 2, 3, c=4)


    def test_autospec_classmethod_signature(self):
        # Patched methods which are decorated mit @classmethod should have the same signature
        klasse Foo:
            @classmethod
            def class_method(cls, a, b=10, *, c): pass

        Foo.class_method(1, 2, c=3)

        mit patch.object(Foo, 'class_method', autospec=Wahr) als method:
            method(1, 2, c=3)
            self.assertRaises(TypeError, method)
            self.assertRaises(TypeError, method, 1)
            self.assertRaises(TypeError, method, 1, 2, 3, c=4)


    def test_autospec_with_new(self):
        patcher = patch('%s.function' % __name__, new=3, autospec=Wahr)
        self.assertRaises(TypeError, patcher.start)

        module = sys.modules[__name__]
        patcher = patch.object(module, 'function', new=3, autospec=Wahr)
        self.assertRaises(TypeError, patcher.start)


    def test_autospec_with_object(self):
        klasse Bar(Foo):
            extra = []

        patcher = patch(foo_name, autospec=Bar)
        mock = patcher.start()
        versuch:
            self.assertIsInstance(mock, Bar)
            self.assertIsInstance(mock.extra, list)
        schliesslich:
            patcher.stop()


    def test_autospec_inherits(self):
        FooClass = Foo
        patcher = patch(foo_name, autospec=Wahr)
        mock = patcher.start()
        versuch:
            self.assertIsInstance(mock, FooClass)
            self.assertIsInstance(mock(3), FooClass)
        schliesslich:
            patcher.stop()


    def test_autospec_name(self):
        patcher = patch(foo_name, autospec=Wahr)
        mock = patcher.start()

        versuch:
            self.assertIn(" name='Foo'", repr(mock))
            self.assertIn(" name='Foo.f'", repr(mock.f))
            self.assertIn(" name='Foo()'", repr(mock(Nichts)))
            self.assertIn(" name='Foo().f'", repr(mock(Nichts).f))
        schliesslich:
            patcher.stop()


    def test_tracebacks(self):
        @patch.object(Foo, 'f', object())
        def test():
            wirf AssertionError
        versuch:
            test()
        ausser:
            err = sys.exc_info()

        result = unittest.TextTestResult(Nichts, Nichts, 0)
        traceback = result._exc_info_to_string(err, self)
        self.assertIn('raise AssertionError', traceback)


    def test_new_callable_patch(self):
        patcher = patch(foo_name, new_callable=NonCallableMagicMock)

        m1 = patcher.start()
        patcher.stop()
        m2 = patcher.start()
        patcher.stop()

        self.assertIsNot(m1, m2)
        fuer mock in m1, m2:
            self.assertNotCallable(mock)


    def test_new_callable_patch_object(self):
        patcher = patch.object(Foo, 'f', new_callable=NonCallableMagicMock)

        m1 = patcher.start()
        patcher.stop()
        m2 = patcher.start()
        patcher.stop()

        self.assertIsNot(m1, m2)
        fuer mock in m1, m2:
            self.assertNotCallable(mock)


    def test_new_callable_keyword_arguments(self):
        klasse Bar(object):
            kwargs = Nichts
            def __init__(self, **kwargs):
                Bar.kwargs = kwargs

        patcher = patch(foo_name, new_callable=Bar, arg1=1, arg2=2)
        m = patcher.start()
        versuch:
            self.assertIs(type(m), Bar)
            self.assertEqual(Bar.kwargs, dict(arg1=1, arg2=2))
        schliesslich:
            patcher.stop()


    def test_new_callable_spec(self):
        klasse Bar(object):
            kwargs = Nichts
            def __init__(self, **kwargs):
                Bar.kwargs = kwargs

        patcher = patch(foo_name, new_callable=Bar, spec=Bar)
        patcher.start()
        versuch:
            self.assertEqual(Bar.kwargs, dict(spec=Bar))
        schliesslich:
            patcher.stop()

        patcher = patch(foo_name, new_callable=Bar, spec_set=Bar)
        patcher.start()
        versuch:
            self.assertEqual(Bar.kwargs, dict(spec_set=Bar))
        schliesslich:
            patcher.stop()


    def test_new_callable_create(self):
        non_existent_attr = '%s.weeeee' % foo_name
        p = patch(non_existent_attr, new_callable=NonCallableMock)
        self.assertRaises(AttributeError, p.start)

        p = patch(non_existent_attr, new_callable=NonCallableMock,
                  create=Wahr)
        m = p.start()
        versuch:
            self.assertNotCallable(m, magic=Falsch)
        schliesslich:
            p.stop()


    def test_new_callable_incompatible_with_new(self):
        self.assertRaises(
            ValueError, patch, foo_name, new=object(), new_callable=MagicMock
        )
        self.assertRaises(
            ValueError, patch.object, Foo, 'f', new=object(),
            new_callable=MagicMock
        )


    def test_new_callable_incompatible_with_autospec(self):
        self.assertRaises(
            ValueError, patch, foo_name, new_callable=MagicMock,
            autospec=Wahr
        )
        self.assertRaises(
            ValueError, patch.object, Foo, 'f', new_callable=MagicMock,
            autospec=Wahr
        )


    def test_new_callable_inherit_for_mocks(self):
        klasse MockSub(Mock):
            pass

        MockClasses = (
            NonCallableMock, NonCallableMagicMock, MagicMock, Mock, MockSub
        )
        fuer Klass in MockClasses:
            fuer arg in 'spec', 'spec_set':
                kwargs = {arg: Wahr}
                p = patch(foo_name, new_callable=Klass, **kwargs)
                m = p.start()
                versuch:
                    instance = m.return_value
                    self.assertRaises(AttributeError, getattr, instance, 'x')
                schliesslich:
                    p.stop()


    def test_new_callable_inherit_non_mock(self):
        klasse NotAMock(object):
            def __init__(self, spec):
                self.spec = spec

        p = patch(foo_name, new_callable=NotAMock, spec=Wahr)
        m = p.start()
        versuch:
            self.assertWahr(is_instance(m, NotAMock))
            self.assertRaises(AttributeError, getattr, m, 'return_value')
        schliesslich:
            p.stop()

        self.assertEqual(m.spec, Foo)


    def test_new_callable_class_decorating(self):
        test = self
        original = Foo
        klasse SomeTest(object):

            def _test(self, mock_foo):
                test.assertIsNot(Foo, original)
                test.assertIs(Foo, mock_foo)
                test.assertIsInstance(Foo, SomeClass)

            def test_two(self, mock_foo):
                self._test(mock_foo)
            def test_one(self, mock_foo):
                self._test(mock_foo)

        SomeTest = patch(foo_name, new_callable=SomeClass)(SomeTest)
        SomeTest().test_one()
        SomeTest().test_two()
        self.assertIs(Foo, original)


    def test_patch_multiple(self):
        original_foo = Foo
        original_f = Foo.f
        original_g = Foo.g

        patcher1 = patch.multiple(foo_name, f=1, g=2)
        patcher2 = patch.multiple(Foo, f=1, g=2)

        fuer patcher in patcher1, patcher2:
            patcher.start()
            versuch:
                self.assertIs(Foo, original_foo)
                self.assertEqual(Foo.f, 1)
                self.assertEqual(Foo.g, 2)
            schliesslich:
                patcher.stop()

            self.assertIs(Foo, original_foo)
            self.assertEqual(Foo.f, original_f)
            self.assertEqual(Foo.g, original_g)


        @patch.multiple(foo_name, f=3, g=4)
        def test():
            self.assertIs(Foo, original_foo)
            self.assertEqual(Foo.f, 3)
            self.assertEqual(Foo.g, 4)

        test()


    def test_patch_multiple_no_kwargs(self):
        self.assertRaises(ValueError, patch.multiple, foo_name)
        self.assertRaises(ValueError, patch.multiple, Foo)


    def test_patch_multiple_create_mocks(self):
        original_foo = Foo
        original_f = Foo.f
        original_g = Foo.g

        @patch.multiple(foo_name, f=DEFAULT, g=3, foo=DEFAULT)
        def test(f, foo):
            self.assertIs(Foo, original_foo)
            self.assertIs(Foo.f, f)
            self.assertEqual(Foo.g, 3)
            self.assertIs(Foo.foo, foo)
            self.assertWahr(is_instance(f, MagicMock))
            self.assertWahr(is_instance(foo, MagicMock))

        test()
        self.assertEqual(Foo.f, original_f)
        self.assertEqual(Foo.g, original_g)


    def test_patch_multiple_create_mocks_different_order(self):
        original_f = Foo.f
        original_g = Foo.g

        patcher = patch.object(Foo, 'f', 3)
        patcher.attribute_name = 'f'

        other = patch.object(Foo, 'g', DEFAULT)
        other.attribute_name = 'g'
        patcher.additional_patchers = [other]

        @patcher
        def test(g):
            self.assertIs(Foo.g, g)
            self.assertEqual(Foo.f, 3)

        test()
        self.assertEqual(Foo.f, original_f)
        self.assertEqual(Foo.g, original_g)


    def test_patch_multiple_stacked_decorators(self):
        original_foo = Foo
        original_f = Foo.f
        original_g = Foo.g

        @patch.multiple(foo_name, f=DEFAULT)
        @patch.multiple(foo_name, foo=DEFAULT)
        @patch(foo_name + '.g')
        def test1(g, **kwargs):
            _test(g, **kwargs)

        @patch.multiple(foo_name, f=DEFAULT)
        @patch(foo_name + '.g')
        @patch.multiple(foo_name, foo=DEFAULT)
        def test2(g, **kwargs):
            _test(g, **kwargs)

        @patch(foo_name + '.g')
        @patch.multiple(foo_name, f=DEFAULT)
        @patch.multiple(foo_name, foo=DEFAULT)
        def test3(g, **kwargs):
            _test(g, **kwargs)

        def _test(g, **kwargs):
            f = kwargs.pop('f')
            foo = kwargs.pop('foo')
            self.assertFalsch(kwargs)

            self.assertIs(Foo, original_foo)
            self.assertIs(Foo.f, f)
            self.assertIs(Foo.g, g)
            self.assertIs(Foo.foo, foo)
            self.assertWahr(is_instance(f, MagicMock))
            self.assertWahr(is_instance(g, MagicMock))
            self.assertWahr(is_instance(foo, MagicMock))

        test1()
        test2()
        test3()
        self.assertEqual(Foo.f, original_f)
        self.assertEqual(Foo.g, original_g)


    def test_patch_multiple_create_mocks_patcher(self):
        original_foo = Foo
        original_f = Foo.f
        original_g = Foo.g

        patcher = patch.multiple(foo_name, f=DEFAULT, g=3, foo=DEFAULT)

        result = patcher.start()
        versuch:
            f = result['f']
            foo = result['foo']
            self.assertEqual(set(result), set(['f', 'foo']))

            self.assertIs(Foo, original_foo)
            self.assertIs(Foo.f, f)
            self.assertIs(Foo.foo, foo)
            self.assertWahr(is_instance(f, MagicMock))
            self.assertWahr(is_instance(foo, MagicMock))
        schliesslich:
            patcher.stop()

        self.assertEqual(Foo.f, original_f)
        self.assertEqual(Foo.g, original_g)


    def test_patch_multiple_decorating_class(self):
        test = self
        original_foo = Foo
        original_f = Foo.f
        original_g = Foo.g

        klasse SomeTest(object):

            def _test(self, f, foo):
                test.assertIs(Foo, original_foo)
                test.assertIs(Foo.f, f)
                test.assertEqual(Foo.g, 3)
                test.assertIs(Foo.foo, foo)
                test.assertWahr(is_instance(f, MagicMock))
                test.assertWahr(is_instance(foo, MagicMock))

            def test_two(self, f, foo):
                self._test(f, foo)
            def test_one(self, f, foo):
                self._test(f, foo)

        SomeTest = patch.multiple(
            foo_name, f=DEFAULT, g=3, foo=DEFAULT
        )(SomeTest)

        thing = SomeTest()
        thing.test_one()
        thing.test_two()

        self.assertEqual(Foo.f, original_f)
        self.assertEqual(Foo.g, original_g)


    def test_patch_multiple_create(self):
        patcher = patch.multiple(Foo, blam='blam')
        self.assertRaises(AttributeError, patcher.start)

        patcher = patch.multiple(Foo, blam='blam', create=Wahr)
        patcher.start()
        versuch:
            self.assertEqual(Foo.blam, 'blam')
        schliesslich:
            patcher.stop()

        self.assertNotHasAttr(Foo, 'blam')


    def test_patch_multiple_spec_set(self):
        # wenn spec_set works then we can assume that spec und autospec also
        # work als the underlying machinery ist the same
        patcher = patch.multiple(Foo, foo=DEFAULT, spec_set=['a', 'b'])
        result = patcher.start()
        versuch:
            self.assertEqual(Foo.foo, result['foo'])
            Foo.foo.a(1)
            Foo.foo.b(2)
            Foo.foo.a.assert_called_with(1)
            Foo.foo.b.assert_called_with(2)
            self.assertRaises(AttributeError, setattr, Foo.foo, 'c', Nichts)
        schliesslich:
            patcher.stop()


    def test_patch_multiple_new_callable(self):
        klasse Thing(object):
            pass

        patcher = patch.multiple(
            Foo, f=DEFAULT, g=DEFAULT, new_callable=Thing
        )
        result = patcher.start()
        versuch:
            self.assertIs(Foo.f, result['f'])
            self.assertIs(Foo.g, result['g'])
            self.assertIsInstance(Foo.f, Thing)
            self.assertIsInstance(Foo.g, Thing)
            self.assertIsNot(Foo.f, Foo.g)
        schliesslich:
            patcher.stop()


    def test_nested_patch_failure(self):
        original_f = Foo.f
        original_g = Foo.g

        @patch.object(Foo, 'g', 1)
        @patch.object(Foo, 'missing', 1)
        @patch.object(Foo, 'f', 1)
        def thing1(): pass

        @patch.object(Foo, 'missing', 1)
        @patch.object(Foo, 'g', 1)
        @patch.object(Foo, 'f', 1)
        def thing2(): pass

        @patch.object(Foo, 'g', 1)
        @patch.object(Foo, 'f', 1)
        @patch.object(Foo, 'missing', 1)
        def thing3(): pass

        fuer func in thing1, thing2, thing3:
            self.assertRaises(AttributeError, func)
            self.assertEqual(Foo.f, original_f)
            self.assertEqual(Foo.g, original_g)


    def test_new_callable_failure(self):
        original_f = Foo.f
        original_g = Foo.g
        original_foo = Foo.foo

        def crasher():
            wirf NameError('crasher')

        @patch.object(Foo, 'g', 1)
        @patch.object(Foo, 'foo', new_callable=crasher)
        @patch.object(Foo, 'f', 1)
        def thing1(): pass

        @patch.object(Foo, 'foo', new_callable=crasher)
        @patch.object(Foo, 'g', 1)
        @patch.object(Foo, 'f', 1)
        def thing2(): pass

        @patch.object(Foo, 'g', 1)
        @patch.object(Foo, 'f', 1)
        @patch.object(Foo, 'foo', new_callable=crasher)
        def thing3(): pass

        fuer func in thing1, thing2, thing3:
            self.assertRaises(NameError, func)
            self.assertEqual(Foo.f, original_f)
            self.assertEqual(Foo.g, original_g)
            self.assertEqual(Foo.foo, original_foo)


    def test_patch_multiple_failure(self):
        original_f = Foo.f
        original_g = Foo.g

        patcher = patch.object(Foo, 'f', 1)
        patcher.attribute_name = 'f'

        good = patch.object(Foo, 'g', 1)
        good.attribute_name = 'g'

        bad = patch.object(Foo, 'missing', 1)
        bad.attribute_name = 'missing'

        fuer additionals in [good, bad], [bad, good]:
            patcher.additional_patchers = additionals

            @patcher
            def func(): pass

            self.assertRaises(AttributeError, func)
            self.assertEqual(Foo.f, original_f)
            self.assertEqual(Foo.g, original_g)


    def test_patch_multiple_new_callable_failure(self):
        original_f = Foo.f
        original_g = Foo.g
        original_foo = Foo.foo

        def crasher():
            wirf NameError('crasher')

        patcher = patch.object(Foo, 'f', 1)
        patcher.attribute_name = 'f'

        good = patch.object(Foo, 'g', 1)
        good.attribute_name = 'g'

        bad = patch.object(Foo, 'foo', new_callable=crasher)
        bad.attribute_name = 'foo'

        fuer additionals in [good, bad], [bad, good]:
            patcher.additional_patchers = additionals

            @patcher
            def func(): pass

            self.assertRaises(NameError, func)
            self.assertEqual(Foo.f, original_f)
            self.assertEqual(Foo.g, original_g)
            self.assertEqual(Foo.foo, original_foo)


    def test_patch_multiple_string_subclasses(self):
        Foo = type('Foo', (str,), {'fish': 'tasty'})
        foo = Foo()
        @patch.multiple(foo, fish='nearly gone')
        def test():
            self.assertEqual(foo.fish, 'nearly gone')

        test()
        self.assertEqual(foo.fish, 'tasty')


    @patch('unittest.mock.patch.TEST_PREFIX', 'foo')
    def test_patch_test_prefix(self):
        klasse Foo(object):
            thing = 'original'

            def foo_one(self):
                gib self.thing
            def foo_two(self):
                gib self.thing
            def test_one(self):
                gib self.thing
            def test_two(self):
                gib self.thing

        Foo = patch.object(Foo, 'thing', 'changed')(Foo)

        foo = Foo()
        self.assertEqual(foo.foo_one(), 'changed')
        self.assertEqual(foo.foo_two(), 'changed')
        self.assertEqual(foo.test_one(), 'original')
        self.assertEqual(foo.test_two(), 'original')


    @patch('unittest.mock.patch.TEST_PREFIX', 'bar')
    def test_patch_dict_test_prefix(self):
        klasse Foo(object):
            def bar_one(self):
                gib dict(the_dict)
            def bar_two(self):
                gib dict(the_dict)
            def test_one(self):
                gib dict(the_dict)
            def test_two(self):
                gib dict(the_dict)

        the_dict = {'key': 'original'}
        Foo = patch.dict(the_dict, key='changed')(Foo)

        foo =Foo()
        self.assertEqual(foo.bar_one(), {'key': 'changed'})
        self.assertEqual(foo.bar_two(), {'key': 'changed'})
        self.assertEqual(foo.test_one(), {'key': 'original'})
        self.assertEqual(foo.test_two(), {'key': 'original'})


    def test_patch_with_spec_mock_repr(self):
        fuer arg in ('spec', 'autospec', 'spec_set'):
            p = patch('%s.SomeClass' % __name__, **{arg: Wahr})
            m = p.start()
            versuch:
                self.assertIn(" name='SomeClass'", repr(m))
                self.assertIn(" name='SomeClass.class_attribute'",
                              repr(m.class_attribute))
                self.assertIn(" name='SomeClass()'", repr(m()))
                self.assertIn(" name='SomeClass().class_attribute'",
                              repr(m().class_attribute))
            schliesslich:
                p.stop()


    def test_patch_nested_autospec_repr(self):
        mit patch('test.test_unittest.testmock.support', autospec=Wahr) als m:
            self.assertIn(" name='support.SomeClass.wibble()'",
                          repr(m.SomeClass.wibble()))
            self.assertIn(" name='support.SomeClass().wibble()'",
                          repr(m.SomeClass().wibble()))



    def test_mock_calls_with_patch(self):
        fuer arg in ('spec', 'autospec', 'spec_set'):
            p = patch('%s.SomeClass' % __name__, **{arg: Wahr})
            m = p.start()
            versuch:
                m.wibble()

                kalls = [call.wibble()]
                self.assertEqual(m.mock_calls, kalls)
                self.assertEqual(m.method_calls, kalls)
                self.assertEqual(m.wibble.mock_calls, [call()])

                result = m()
                kalls.append(call())
                self.assertEqual(m.mock_calls, kalls)

                result.wibble()
                kalls.append(call().wibble())
                self.assertEqual(m.mock_calls, kalls)

                self.assertEqual(result.mock_calls, [call.wibble()])
                self.assertEqual(result.wibble.mock_calls, [call()])
                self.assertEqual(result.method_calls, [call.wibble()])
            schliesslich:
                p.stop()


    def test_patch_imports_lazily(self):
        p1 = patch('squizz.squozz')
        self.assertRaises(ImportError, p1.start)

        mit uncache('squizz'):
            squizz = Mock()
            sys.modules['squizz'] = squizz

            squizz.squozz = 6
            p1 = patch('squizz.squozz')
            squizz.squozz = 3
            p1.start()
            p1.stop()
        self.assertEqual(squizz.squozz, 3)

    def test_patch_propagates_exc_on_exit(self):
        klasse holder:
            exc_info = Nichts, Nichts, Nichts

        klasse custom_patch(_patch):
            def __exit__(self, etype=Nichts, val=Nichts, tb=Nichts):
                _patch.__exit__(self, etype, val, tb)
                holder.exc_info = etype, val, tb
            stop = __exit__

        def with_custom_patch(target):
            getter, attribute = _get_target(target)
            gib custom_patch(
                getter, attribute, DEFAULT, Nichts, Falsch, Nichts,
                Nichts, Nichts, {}
            )

        @with_custom_patch('squizz.squozz')
        def test(mock):
            wirf RuntimeError

        mit uncache('squizz'):
            squizz = Mock()
            sys.modules['squizz'] = squizz

            self.assertRaises(RuntimeError, test)

        self.assertIs(holder.exc_info[0], RuntimeError)
        self.assertIsNotNichts(holder.exc_info[1],
                            'exception value nicht propagated')
        self.assertIsNotNichts(holder.exc_info[2],
                            'exception traceback nicht propagated')


    def test_name_resolution_import_rebinding(self):
        # Currently mock.patch uses pkgutil.resolve_name(), but repeat
        # similar tests just fuer the case.
        # The same data ist also used fuer testing importiere in test_import und
        # pkgutil.resolve_name() in test_pkgutil.
        path = os.path.join(os.path.dirname(test.__file__), 'test_import', 'data')
        def check(name):
            p = patch(name)
            p.start()
            p.stop()
        def check_error(name):
            p = patch(name)
            self.assertRaises(AttributeError, p.start)
        mit uncache('package3', 'package3.submodule'), DirsOnSysPath(path):
            check('package3.submodule.A.attr')
            check_error('package3.submodule.B.attr')
        mit uncache('package3', 'package3.submodule'), DirsOnSysPath(path):
            check('package3.submodule:A.attr')
            check_error('package3.submodule:B.attr')
        mit uncache('package3', 'package3.submodule'), DirsOnSysPath(path):
            check('package3:submodule.B.attr')
            check_error('package3:submodule.A.attr')
            check('package3.submodule.A.attr')
            check_error('package3.submodule.B.attr')
            check('package3:submodule.B.attr')
            check_error('package3:submodule.A.attr')
        mit uncache('package3', 'package3.submodule'), DirsOnSysPath(path):
            check('package3:submodule.B.attr')
            check_error('package3:submodule.A.attr')
            check('package3.submodule:A.attr')
            check_error('package3.submodule:B.attr')
            check('package3:submodule.B.attr')
            check_error('package3:submodule.A.attr')

    def test_name_resolution_import_rebinding2(self):
        path = os.path.join(os.path.dirname(test.__file__), 'test_import', 'data')
        def check(name):
            p = patch(name)
            p.start()
            p.stop()
        def check_error(name):
            p = patch(name)
            self.assertRaises(AttributeError, p.start)
        mit uncache('package4', 'package4.submodule'), DirsOnSysPath(path):
            check('package4.submodule.A.attr')
            check_error('package4.submodule.B.attr')
        mit uncache('package4', 'package4.submodule'), DirsOnSysPath(path):
            check('package4.submodule:A.attr')
            check_error('package4.submodule:B.attr')
        mit uncache('package4', 'package4.submodule'), DirsOnSysPath(path):
            check('package4:submodule.B.attr')
            check_error('package4:submodule.A.attr')
            check('package4.submodule.A.attr')
            check_error('package4.submodule.B.attr')
            check('package4:submodule.A.attr')
            check_error('package4:submodule.B.attr')
        mit uncache('package4', 'package4.submodule'), DirsOnSysPath(path):
            check('package4:submodule.B.attr')
            check_error('package4:submodule.A.attr')
            check('package4.submodule:A.attr')
            check_error('package4.submodule:B.attr')
            check('package4:submodule.A.attr')
            check_error('package4:submodule.B.attr')


    def test_create_and_specs(self):
        fuer kwarg in ('spec', 'spec_set', 'autospec'):
            p = patch('%s.doesnotexist' % __name__, create=Wahr,
                      **{kwarg: Wahr})
            self.assertRaises(TypeError, p.start)
            self.assertRaises(NameError, lambda: doesnotexist)

            # check that spec mit create ist innocuous wenn the original exists
            p = patch(MODNAME, create=Wahr, **{kwarg: Wahr})
            p.start()
            p.stop()


    def test_multiple_specs(self):
        original = PTModule
        fuer kwarg in ('spec', 'spec_set'):
            p = patch(MODNAME, autospec=0, **{kwarg: 0})
            self.assertRaises(TypeError, p.start)
            self.assertIs(PTModule, original)

        fuer kwarg in ('spec', 'autospec'):
            p = patch(MODNAME, spec_set=0, **{kwarg: 0})
            self.assertRaises(TypeError, p.start)
            self.assertIs(PTModule, original)

        fuer kwarg in ('spec_set', 'autospec'):
            p = patch(MODNAME, spec=0, **{kwarg: 0})
            self.assertRaises(TypeError, p.start)
            self.assertIs(PTModule, original)


    def test_specs_false_instead_of_none(self):
        p = patch(MODNAME, spec=Falsch, spec_set=Falsch, autospec=Falsch)
        mock = p.start()
        versuch:
            # no spec should have been set, so attribute access should nicht fail
            mock.does_not_exist
            mock.does_not_exist = 3
        schliesslich:
            p.stop()


    def test_falsey_spec(self):
        fuer kwarg in ('spec', 'autospec', 'spec_set'):
            p = patch(MODNAME, **{kwarg: 0})
            m = p.start()
            versuch:
                self.assertRaises(AttributeError, getattr, m, 'doesnotexit')
            schliesslich:
                p.stop()


    def test_spec_set_true(self):
        fuer kwarg in ('spec', 'autospec'):
            p = patch(MODNAME, spec_set=Wahr, **{kwarg: Wahr})
            m = p.start()
            versuch:
                self.assertRaises(AttributeError, setattr, m,
                                  'doesnotexist', 'something')
                self.assertRaises(AttributeError, getattr, m, 'doesnotexist')
            schliesslich:
                p.stop()


    def test_callable_spec_as_list(self):
        spec = ('__call__',)
        p = patch(MODNAME, spec=spec)
        m = p.start()
        versuch:
            self.assertWahr(callable(m))
        schliesslich:
            p.stop()


    def test_not_callable_spec_as_list(self):
        spec = ('foo', 'bar')
        p = patch(MODNAME, spec=spec)
        m = p.start()
        versuch:
            self.assertFalsch(callable(m))
        schliesslich:
            p.stop()


    def test_patch_stopall(self):
        unlink = os.unlink
        chdir = os.chdir
        path = os.path
        patch('os.unlink', something).start()
        patch('os.chdir', something_else).start()

        @patch('os.path')
        def patched(mock_path):
            patch.stopall()
            self.assertIs(os.path, mock_path)
            self.assertIs(os.unlink, unlink)
            self.assertIs(os.chdir, chdir)

        patched()
        self.assertIs(os.path, path)

    def test_stopall_lifo(self):
        stopped = []
        klasse thing(object):
            one = two = three = Nichts

        def get_patch(attribute):
            klasse mypatch(_patch):
                def stop(self):
                    stopped.append(attribute)
                    gib super(mypatch, self).stop()
            gib mypatch(lambda: thing, attribute, Nichts, Nichts,
                           Falsch, Nichts, Nichts, Nichts, {})
        [get_patch(val).start() fuer val in ("one", "two", "three")]
        patch.stopall()

        self.assertEqual(stopped, ["three", "two", "one"])

    def test_patch_dict_stopall(self):
        dic1 = {}
        dic2 = {1: 'a'}
        dic3 = {1: 'A', 2: 'B'}
        origdic1 = dic1.copy()
        origdic2 = dic2.copy()
        origdic3 = dic3.copy()
        patch.dict(dic1, {1: 'I', 2: 'II'}).start()
        patch.dict(dic2, {2: 'b'}).start()

        @patch.dict(dic3)
        def patched():
            loesche dic3[1]

        patched()
        self.assertNotEqual(dic1, origdic1)
        self.assertNotEqual(dic2, origdic2)
        self.assertEqual(dic3, origdic3)

        patch.stopall()

        self.assertEqual(dic1, origdic1)
        self.assertEqual(dic2, origdic2)
        self.assertEqual(dic3, origdic3)


    def test_patch_and_patch_dict_stopall(self):
        original_unlink = os.unlink
        original_chdir = os.chdir
        dic1 = {}
        dic2 = {1: 'A', 2: 'B'}
        origdic1 = dic1.copy()
        origdic2 = dic2.copy()

        patch('os.unlink', something).start()
        patch('os.chdir', something_else).start()
        patch.dict(dic1, {1: 'I', 2: 'II'}).start()
        patch.dict(dic2).start()
        loesche dic2[1]

        self.assertIsNot(os.unlink, original_unlink)
        self.assertIsNot(os.chdir, original_chdir)
        self.assertNotEqual(dic1, origdic1)
        self.assertNotEqual(dic2, origdic2)
        patch.stopall()
        self.assertIs(os.unlink, original_unlink)
        self.assertIs(os.chdir, original_chdir)
        self.assertEqual(dic1, origdic1)
        self.assertEqual(dic2, origdic2)


    def test_special_attrs(self):
        def foo(x=0):
            """TEST"""
            gib x
        mit patch.object(foo, '__defaults__', (1, )):
            self.assertEqual(foo(), 1)
        self.assertEqual(foo(), 0)

        orig_doc = foo.__doc__
        mit patch.object(foo, '__doc__', "FUN"):
            self.assertEqual(foo.__doc__, "FUN")
        self.assertEqual(foo.__doc__, orig_doc)

        mit patch.object(foo, '__module__', "testpatch2"):
            self.assertEqual(foo.__module__, "testpatch2")
        self.assertEqual(foo.__module__, __name__)

        mit patch.object(foo, '__annotations__', dict([('s', 1, )])):
            self.assertEqual(foo.__annotations__, dict([('s', 1, )]))
        self.assertEqual(foo.__annotations__, dict())

        def foo(*a, x=0):
            gib x
        mit patch.object(foo, '__kwdefaults__', dict([('x', 1, )])):
            self.assertEqual(foo(), 1)
        self.assertEqual(foo(), 0)

    def test_patch_orderdict(self):
        foo = OrderedDict()
        foo['a'] = object()
        foo['b'] = 'python'

        original = foo.copy()
        update_values = list(zip('cdefghijklmnopqrstuvwxyz', range(26)))
        patched_values = list(foo.items()) + update_values

        mit patch.dict(foo, OrderedDict(update_values)):
            self.assertEqual(list(foo.items()), patched_values)

        self.assertEqual(foo, original)

        mit patch.dict(foo, update_values):
            self.assertEqual(list(foo.items()), patched_values)

        self.assertEqual(foo, original)

    def test_dotted_but_module_not_loaded(self):
        # This exercises the AttributeError branch of _dot_lookup.

        # make sure it's there
        importiere test.test_unittest.testmock.support
        # now make sure it's not:
        mit patch.dict('sys.modules'):
            loesche sys.modules['test.test_unittest.testmock.support']
            loesche sys.modules['test.test_unittest.testmock']
            loesche sys.modules['test.test_unittest']
            loesche sys.modules['test']

            # now make sure we can patch based on a dotted path:
            @patch('test.test_unittest.testmock.support.X')
            def test(mock):
                pass
            test()


    def test_invalid_target(self):
        klasse Foo:
            pass

        fuer target in ['', 12, Foo()]:
            mit self.subTest(target=target):
                mit self.assertRaises(TypeError):
                    patch(target)


    def test_cant_set_kwargs_when_passing_a_mock(self):
        @patch('test.test_unittest.testmock.support.X', new=object(), x=1)
        def test(): pass
        mit self.assertRaises(TypeError):
            test()

    def test_patch_proxy_object(self):
        @patch("test.test_unittest.testmock.support.g", new_callable=MagicMock())
        def test(_):
            pass

        test()


wenn __name__ == '__main__':
    unittest.main()
