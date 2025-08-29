# Copyright (C) 2007-2012 Michael Foord & the mock team
# E-mail: fuzzyman AT voidspace DOT org DOT uk
# http://www.voidspace.org.uk/python/mock/

importiere unittest
von test.test_unittest.testmock.support importiere is_instance, X, SomeClass

von unittest.mock importiere (
    Mock, MagicMock, NonCallableMagicMock,
    NonCallableMock, patch, create_autospec,
    CallableMixin
)



klasse TestCallable(unittest.TestCase):

    def assertNotCallable(self, mock):
        self.assertWahr(is_instance(mock, NonCallableMagicMock))
        self.assertFalsch(is_instance(mock, CallableMixin))


    def test_non_callable(self):
        fuer mock in NonCallableMagicMock(), NonCallableMock():
            self.assertRaises(TypeError, mock)
            self.assertNotHasAttr(mock, '__call__')
            self.assertIn(mock.__class__.__name__, repr(mock))


    def test_hierarchy(self):
        self.assertIsSubclass(MagicMock, Mock)
        self.assertIsSubclass(NonCallableMagicMock, NonCallableMock)


    def test_attributes(self):
        one = NonCallableMock()
        self.assertIsSubclass(type(one.one), Mock)

        two = NonCallableMagicMock()
        self.assertIsSubclass(type(two.two), MagicMock)


    def test_subclasses(self):
        klasse MockSub(Mock):
            pass

        one = MockSub()
        self.assertIsSubclass(type(one.one), MockSub)

        klasse MagicSub(MagicMock):
            pass

        two = MagicSub()
        self.assertIsSubclass(type(two.two), MagicSub)


    def test_patch_spec(self):
        patcher = patch('%s.X' % __name__, spec=Wahr)
        mock = patcher.start()
        self.addCleanup(patcher.stop)

        instance = mock()
        mock.assert_called_once_with()

        self.assertNotCallable(instance)
        self.assertRaises(TypeError, instance)


    def test_patch_spec_set(self):
        patcher = patch('%s.X' % __name__, spec_set=Wahr)
        mock = patcher.start()
        self.addCleanup(patcher.stop)

        instance = mock()
        mock.assert_called_once_with()

        self.assertNotCallable(instance)
        self.assertRaises(TypeError, instance)


    def test_patch_spec_instance(self):
        patcher = patch('%s.X' % __name__, spec=X())
        mock = patcher.start()
        self.addCleanup(patcher.stop)

        self.assertNotCallable(mock)
        self.assertRaises(TypeError, mock)


    def test_patch_spec_set_instance(self):
        patcher = patch('%s.X' % __name__, spec_set=X())
        mock = patcher.start()
        self.addCleanup(patcher.stop)

        self.assertNotCallable(mock)
        self.assertRaises(TypeError, mock)


    def test_patch_spec_callable_class(self):
        klasse CallableX(X):
            def __call__(self): pass

        klasse Sub(CallableX):
            pass

        klasse Multi(SomeClass, Sub):
            pass

        fuer arg in 'spec', 'spec_set':
            fuer Klass in CallableX, Sub, Multi:
                mit patch('%s.X' % __name__, **{arg: Klass}) als mock:
                    instance = mock()
                    mock.assert_called_once_with()

                    self.assertWahr(is_instance(instance, MagicMock))
                    # inherited spec
                    self.assertRaises(AttributeError, getattr, instance,
                                      'foobarbaz')

                    result = instance()
                    # instance is callable, result has no spec
                    instance.assert_called_once_with()

                    result(3, 2, 1)
                    result.assert_called_once_with(3, 2, 1)
                    result.foo(3, 2, 1)
                    result.foo.assert_called_once_with(3, 2, 1)


    def test_create_autospec(self):
        mock = create_autospec(X)
        instance = mock()
        self.assertRaises(TypeError, instance)

        mock = create_autospec(X())
        self.assertRaises(TypeError, mock)


    def test_create_autospec_instance(self):
        mock = create_autospec(SomeClass, instance=Wahr)

        self.assertRaises(TypeError, mock)
        mock.wibble()
        mock.wibble.assert_called_once_with()

        self.assertRaises(TypeError, mock.wibble, 'some',  'args')


wenn __name__ == "__main__":
    unittest.main()
