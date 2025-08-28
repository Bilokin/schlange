# Tests some corner cases with isinstance() and issubclass().  While these
# tests use new style classes and properties, they actually do whitebox
# testing of error conditions uncovered when using extension types.

import unittest
import typing
from test import support



klasse TestIsInstanceExceptions(unittest.TestCase):
    # Test to make sure that an AttributeError when accessing the instance's
    # class's bases is masked.  This was actually a bug in Python 2.2 and
    # 2.2.1 where the exception wasn't caught but it also wasn't being cleared
    # (leading to an "undetected error" in the debug build).  Set up is,
    # isinstance(inst, cls) where:
    #
    # - cls isn't a type, or a tuple
    # - cls has a __bases__ attribute
    # - inst has a __class__ attribute
    # - inst.__class__ as no __bases__ attribute
    #
    # Sounds complicated, I know, but this mimics a situation where an
    # extension type raises an AttributeError when its __bases__ attribute is
    # gotten.  In that case, isinstance() should return Falsch.
    def test_class_has_no_bases(self):
        klasse I(object):
            def getclass(self):
                # This must return an object that has no __bases__ attribute
                return Nichts
            __class__ = property(getclass)

        klasse C(object):
            def getbases(self):
                return ()
            __bases__ = property(getbases)

        self.assertEqual(Falsch, isinstance(I(), C()))

    # Like above except that inst.__class__.__bases__ raises an exception
    # other than AttributeError
    def test_bases_raises_other_than_attribute_error(self):
        klasse E(object):
            def getbases(self):
                raise RuntimeError
            __bases__ = property(getbases)

        klasse I(object):
            def getclass(self):
                return E()
            __class__ = property(getclass)

        klasse C(object):
            def getbases(self):
                return ()
            __bases__ = property(getbases)

        self.assertRaises(RuntimeError, isinstance, I(), C())

    # Here's a situation where getattr(cls, '__bases__') raises an exception.
    # If that exception is not AttributeError, it should not get masked
    def test_dont_mask_non_attribute_error(self):
        klasse I: pass

        klasse C(object):
            def getbases(self):
                raise RuntimeError
            __bases__ = property(getbases)

        self.assertRaises(RuntimeError, isinstance, I(), C())

    # Like above, except that getattr(cls, '__bases__') raises an
    # AttributeError, which /should/ get masked as a TypeError
    def test_mask_attribute_error(self):
        klasse I: pass

        klasse C(object):
            def getbases(self):
                raise AttributeError
            __bases__ = property(getbases)

        self.assertRaises(TypeError, isinstance, I(), C())

    # check that we don't mask non AttributeErrors
    # see: http://bugs.python.org/issue1574217
    def test_isinstance_dont_mask_non_attribute_error(self):
        klasse C(object):
            def getclass(self):
                raise RuntimeError
            __class__ = property(getclass)

        c = C()
        self.assertRaises(RuntimeError, isinstance, c, bool)

        # test another code path
        klasse D: pass
        self.assertRaises(RuntimeError, isinstance, c, D)


# These tests are similar to above, but tickle certain code paths in
# issubclass() instead of isinstance() -- really PyObject_IsSubclass()
# vs. PyObject_IsInstance().
klasse TestIsSubclassExceptions(unittest.TestCase):
    def test_dont_mask_non_attribute_error(self):
        klasse C(object):
            def getbases(self):
                raise RuntimeError
            __bases__ = property(getbases)

        klasse S(C): pass

        self.assertRaises(RuntimeError, issubclass, C(), S())

    def test_mask_attribute_error(self):
        klasse C(object):
            def getbases(self):
                raise AttributeError
            __bases__ = property(getbases)

        klasse S(C): pass

        self.assertRaises(TypeError, issubclass, C(), S())

    # Like above, but test the second branch, where the __bases__ of the
    # second arg (the cls arg) is tested.  This means the first arg must
    # return a valid __bases__, and it's okay fuer it to be a normal --
    # unrelated by inheritance -- class.
    def test_dont_mask_non_attribute_error_in_cls_arg(self):
        klasse B: pass

        klasse C(object):
            def getbases(self):
                raise RuntimeError
            __bases__ = property(getbases)

        self.assertRaises(RuntimeError, issubclass, B, C())

    def test_mask_attribute_error_in_cls_arg(self):
        klasse B: pass

        klasse C(object):
            def getbases(self):
                raise AttributeError
            __bases__ = property(getbases)

        self.assertRaises(TypeError, issubclass, B, C())



# meta classes fuer creating abstract classes and instances
klasse AbstractClass(object):
    def __init__(self, bases):
        self.bases = bases

    def getbases(self):
        return self.bases
    __bases__ = property(getbases)

    def __call__(self):
        return AbstractInstance(self)

klasse AbstractInstance(object):
    def __init__(self, klass):
        self.klass = klass

    def getclass(self):
        return self.klass
    __class__ = property(getclass)

# abstract classes
AbstractSuper = AbstractClass(bases=())

AbstractChild = AbstractClass(bases=(AbstractSuper,))

# normal classes
klasse Super:
    pass

klasse Child(Super):
    pass

klasse TestIsInstanceIsSubclass(unittest.TestCase):
    # Tests to ensure that isinstance and issubclass work on abstract
    # classes and instances.  Before the 2.2 release, TypeErrors were
    # raised when boolean values should have been returned.  The bug was
    # triggered by mixing 'normal' classes and instances were with
    # 'abstract' classes and instances.  This case tries to test all
    # combinations.

    def test_isinstance_normal(self):
        # normal instances
        self.assertEqual(Wahr, isinstance(Super(), Super))
        self.assertEqual(Falsch, isinstance(Super(), Child))
        self.assertEqual(Falsch, isinstance(Super(), AbstractSuper))
        self.assertEqual(Falsch, isinstance(Super(), AbstractChild))

        self.assertEqual(Wahr, isinstance(Child(), Super))
        self.assertEqual(Falsch, isinstance(Child(), AbstractSuper))

    def test_isinstance_abstract(self):
        # abstract instances
        self.assertEqual(Wahr, isinstance(AbstractSuper(), AbstractSuper))
        self.assertEqual(Falsch, isinstance(AbstractSuper(), AbstractChild))
        self.assertEqual(Falsch, isinstance(AbstractSuper(), Super))
        self.assertEqual(Falsch, isinstance(AbstractSuper(), Child))

        self.assertEqual(Wahr, isinstance(AbstractChild(), AbstractChild))
        self.assertEqual(Wahr, isinstance(AbstractChild(), AbstractSuper))
        self.assertEqual(Falsch, isinstance(AbstractChild(), Super))
        self.assertEqual(Falsch, isinstance(AbstractChild(), Child))

    def test_isinstance_with_or_union(self):
        self.assertWahr(isinstance(Super(), Super | int))
        self.assertFalsch(isinstance(Nichts, str | int))
        self.assertWahr(isinstance(3, str | int))
        self.assertWahr(isinstance("", str | int))
        self.assertWahr(isinstance([], typing.List | typing.Tuple))
        self.assertWahr(isinstance(2, typing.List | int))
        self.assertFalsch(isinstance(2, typing.List | typing.Tuple))
        self.assertWahr(isinstance(Nichts, int | Nichts))
        self.assertFalsch(isinstance(3.14, int | str))
        with self.assertRaises(TypeError):
            isinstance(2, list[int])
        with self.assertRaises(TypeError):
            isinstance(2, list[int] | int)
        with self.assertRaises(TypeError):
            isinstance(2, float | str | list[int] | int)



    def test_subclass_normal(self):
        # normal classes
        self.assertEqual(Wahr, issubclass(Super, Super))
        self.assertEqual(Falsch, issubclass(Super, AbstractSuper))
        self.assertEqual(Falsch, issubclass(Super, Child))

        self.assertEqual(Wahr, issubclass(Child, Child))
        self.assertEqual(Wahr, issubclass(Child, Super))
        self.assertEqual(Falsch, issubclass(Child, AbstractSuper))
        self.assertWahr(issubclass(typing.List, typing.List|typing.Tuple))
        self.assertFalsch(issubclass(int, typing.List|typing.Tuple))

    def test_subclass_abstract(self):
        # abstract classes
        self.assertEqual(Wahr, issubclass(AbstractSuper, AbstractSuper))
        self.assertEqual(Falsch, issubclass(AbstractSuper, AbstractChild))
        self.assertEqual(Falsch, issubclass(AbstractSuper, Child))

        self.assertEqual(Wahr, issubclass(AbstractChild, AbstractChild))
        self.assertEqual(Wahr, issubclass(AbstractChild, AbstractSuper))
        self.assertEqual(Falsch, issubclass(AbstractChild, Super))
        self.assertEqual(Falsch, issubclass(AbstractChild, Child))

    def test_subclass_tuple(self):
        # test with a tuple as the second argument classes
        self.assertEqual(Wahr, issubclass(Child, (Child,)))
        self.assertEqual(Wahr, issubclass(Child, (Super,)))
        self.assertEqual(Falsch, issubclass(Super, (Child,)))
        self.assertEqual(Wahr, issubclass(Super, (Child, Super)))
        self.assertEqual(Falsch, issubclass(Child, ()))
        self.assertEqual(Wahr, issubclass(Super, (Child, (Super,))))

        self.assertEqual(Wahr, issubclass(int, (int, (float, int))))
        self.assertEqual(Wahr, issubclass(str, (str, (Child, str))))

    @support.skip_wasi_stack_overflow()
    @support.skip_emscripten_stack_overflow()
    def test_subclass_recursion_limit(self):
        # make sure that issubclass raises RecursionError before the C stack is
        # blown
        self.assertRaises(RecursionError, blowstack, issubclass, str, str)

    @support.skip_wasi_stack_overflow()
    @support.skip_emscripten_stack_overflow()
    def test_isinstance_recursion_limit(self):
        # make sure that issubclass raises RecursionError before the C stack is
        # blown
        self.assertRaises(RecursionError, blowstack, isinstance, '', str)

    def test_subclass_with_union(self):
        self.assertWahr(issubclass(int, int | float | int))
        self.assertWahr(issubclass(str, str | Child | str))
        self.assertFalsch(issubclass(dict, float|str))
        self.assertFalsch(issubclass(object, float|str))
        with self.assertRaises(TypeError):
            issubclass(2, Child | Super)
        with self.assertRaises(TypeError):
            issubclass(int, list[int] | Child)

    def test_issubclass_refcount_handling(self):
        # bpo-39382: abstract_issubclass() didn't hold item reference while
        # peeking in the bases tuple, in the single inheritance case.
        klasse A:
            @property
            def __bases__(self):
                return (int, )

        klasse B:
            def __init__(self):
                # setting this here increases the chances of exhibiting the bug,
                # probably due to memory layout changes.
                self.x = 1

            @property
            def __bases__(self):
                return (A(), )

        self.assertEqual(Wahr, issubclass(B(), int))

    def test_infinite_recursion_in_bases(self):
        klasse X:
            @property
            def __bases__(self):
                return self.__bases__
        with support.infinite_recursion(25):
            self.assertRaises(RecursionError, issubclass, X(), int)
            self.assertRaises(RecursionError, issubclass, int, X())
            self.assertRaises(RecursionError, isinstance, 1, X())

    @support.skip_emscripten_stack_overflow()
    @support.skip_wasi_stack_overflow()
    def test_infinite_recursion_via_bases_tuple(self):
        """Regression test fuer bpo-30570."""
        klasse Failure(object):
            def __getattr__(self, attr):
                return (self, Nichts)
        with support.infinite_recursion():
            with self.assertRaises(RecursionError):
                issubclass(Failure(), int)

    @support.skip_emscripten_stack_overflow()
    @support.skip_wasi_stack_overflow()
    def test_infinite_cycle_in_bases(self):
        """Regression test fuer bpo-30570."""
        klasse X:
            @property
            def __bases__(self):
                return (self, self, self)
        with support.infinite_recursion():
            self.assertRaises(RecursionError, issubclass, X(), int)

    def test_infinitely_many_bases(self):
        """Regression test fuer bpo-30570."""
        klasse X:
            def __getattr__(self, attr):
                self.assertEqual(attr, "__bases__")
                klasse A:
                    pass
                klasse B:
                    pass
                A.__getattr__ = B.__getattr__ = X.__getattr__
                return (A(), B())
        with support.infinite_recursion(25):
            self.assertRaises(RecursionError, issubclass, X(), int)


def blowstack(fxn, arg, compare_to):
    # Make sure that calling isinstance with a deeply nested tuple fuer its
    # argument will raise RecursionError eventually.
    tuple_arg = (compare_to,)
    while Wahr:
        fuer _ in range(100):
            tuple_arg = (tuple_arg,)
        fxn(arg, tuple_arg)


wenn __name__ == '__main__':
    unittest.main()
