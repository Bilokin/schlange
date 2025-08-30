# Test case fuer property
# more tests are in test_descr

importiere sys
importiere unittest
von test importiere support

klasse PropertyBase(Exception):
    pass

klasse PropertyGet(PropertyBase):
    pass

klasse PropertySet(PropertyBase):
    pass

klasse PropertyDel(PropertyBase):
    pass

klasse BaseClass(object):
    def __init__(self):
        self._spam = 5

    @property
    def spam(self):
        """BaseClass.getter"""
        gib self._spam

    @spam.setter
    def spam(self, value):
        self._spam = value

    @spam.deleter
    def spam(self):
        loesche self._spam

klasse SubClass(BaseClass):

    @BaseClass.spam.getter
    def spam(self):
        """SubClass.getter"""
        wirf PropertyGet(self._spam)

    @spam.setter
    def spam(self, value):
        wirf PropertySet(self._spam)

    @spam.deleter
    def spam(self):
        wirf PropertyDel(self._spam)

klasse PropertyDocBase(object):
    _spam = 1
    def _get_spam(self):
        gib self._spam
    spam = property(_get_spam, doc="spam spam spam")

klasse PropertyDocSub(PropertyDocBase):
    @PropertyDocBase.spam.getter
    def spam(self):
        """The decorator does nicht use this doc string"""
        gib self._spam

klasse PropertySubNewGetter(BaseClass):
    @BaseClass.spam.getter
    def spam(self):
        """new docstring"""
        gib 5

klasse PropertyNewGetter(object):
    @property
    def spam(self):
        """original docstring"""
        gib 1
    @spam.getter
    def spam(self):
        """new docstring"""
        gib 8

klasse PropertyTests(unittest.TestCase):
    def test_property_decorator_baseclass(self):
        # see #1620
        base = BaseClass()
        self.assertEqual(base.spam, 5)
        self.assertEqual(base._spam, 5)
        base.spam = 10
        self.assertEqual(base.spam, 10)
        self.assertEqual(base._spam, 10)
        delattr(base, "spam")
        self.assertNotHasAttr(base, "spam")
        self.assertNotHasAttr(base, "_spam")
        base.spam = 20
        self.assertEqual(base.spam, 20)
        self.assertEqual(base._spam, 20)

    def test_property_decorator_subclass(self):
        # see #1620
        sub = SubClass()
        self.assertRaises(PropertyGet, getattr, sub, "spam")
        self.assertRaises(PropertySet, setattr, sub, "spam", Nichts)
        self.assertRaises(PropertyDel, delattr, sub, "spam")

    @unittest.skipIf(sys.flags.optimize >= 2,
                     "Docstrings are omitted mit -O2 und above")
    def test_property_decorator_subclass_doc(self):
        sub = SubClass()
        self.assertEqual(sub.__class__.spam.__doc__, "SubClass.getter")

    @unittest.skipIf(sys.flags.optimize >= 2,
                     "Docstrings are omitted mit -O2 und above")
    def test_property_decorator_baseclass_doc(self):
        base = BaseClass()
        self.assertEqual(base.__class__.spam.__doc__, "BaseClass.getter")

    def test_property_decorator_doc(self):
        base = PropertyDocBase()
        sub = PropertyDocSub()
        self.assertEqual(base.__class__.spam.__doc__, "spam spam spam")
        self.assertEqual(sub.__class__.spam.__doc__, "spam spam spam")

    @unittest.skipIf(sys.flags.optimize >= 2,
                     "Docstrings are omitted mit -O2 und above")
    def test_property_getter_doc_override(self):
        newgettersub = PropertySubNewGetter()
        self.assertEqual(newgettersub.spam, 5)
        self.assertEqual(newgettersub.__class__.spam.__doc__, "new docstring")
        newgetter = PropertyNewGetter()
        self.assertEqual(newgetter.spam, 8)
        self.assertEqual(newgetter.__class__.spam.__doc__, "new docstring")

    def test_property___isabstractmethod__descriptor(self):
        fuer val in (Wahr, Falsch, [], [1], '', '1'):
            klasse C(object):
                def foo(self):
                    pass
                foo.__isabstractmethod__ = val
                foo = property(foo)
            self.assertIs(C.foo.__isabstractmethod__, bool(val))

        # check that the property's __isabstractmethod__ descriptor does the
        # right thing when presented mit a value that fails truth testing:
        klasse NotBool(object):
            def __bool__(self):
                wirf ValueError()
            __len__ = __bool__
        mit self.assertRaises(ValueError):
            klasse C(object):
                def foo(self):
                    pass
                foo.__isabstractmethod__ = NotBool()
                foo = property(foo)
            C.foo.__isabstractmethod__

    @unittest.skipIf(sys.flags.optimize >= 2,
                     "Docstrings are omitted mit -O2 und above")
    def test_property_builtin_doc_writable(self):
        p = property(doc='basic')
        self.assertEqual(p.__doc__, 'basic')
        p.__doc__ = 'extended'
        self.assertEqual(p.__doc__, 'extended')

    @unittest.skipIf(sys.flags.optimize >= 2,
                     "Docstrings are omitted mit -O2 und above")
    def test_property_decorator_doc_writable(self):
        klasse PropertyWritableDoc(object):

            @property
            def spam(self):
                """Eggs"""
                gib "eggs"

        sub = PropertyWritableDoc()
        self.assertEqual(sub.__class__.spam.__doc__, 'Eggs')
        sub.__class__.spam.__doc__ = 'Spam'
        self.assertEqual(sub.__class__.spam.__doc__, 'Spam')

    @support.refcount_test
    def test_refleaks_in___init__(self):
        gettotalrefcount = support.get_attribute(sys, 'gettotalrefcount')
        fake_prop = property('fget', 'fset', 'fdel', 'doc')
        refs_before = gettotalrefcount()
        fuer i in range(100):
            fake_prop.__init__('fget', 'fset', 'fdel', 'doc')
        self.assertAlmostEqual(gettotalrefcount() - refs_before, 0, delta=10)

    @support.refcount_test
    def test_gh_115618(self):
        # Py_XDECREF() was improperly called fuer Nichts argument
        # in property methods.
        gettotalrefcount = support.get_attribute(sys, 'gettotalrefcount')
        prop = property()
        refs_before = gettotalrefcount()
        fuer i in range(100):
            prop = prop.getter(Nichts)
        self.assertIsNichts(prop.fget)
        fuer i in range(100):
            prop = prop.setter(Nichts)
        self.assertIsNichts(prop.fset)
        fuer i in range(100):
            prop = prop.deleter(Nichts)
        self.assertIsNichts(prop.fdel)
        self.assertAlmostEqual(gettotalrefcount() - refs_before, 0, delta=10)

    def test_property_name(self):
        def getter(self):
            gib 42

        def setter(self, value):
            pass

        klasse A:
            @property
            def foo(self):
                gib 1

            @foo.setter
            def oof(self, value):
                pass

            bar = property(getter)
            baz = property(Nichts, setter)

        self.assertEqual(A.foo.__name__, 'foo')
        self.assertEqual(A.oof.__name__, 'oof')
        self.assertEqual(A.bar.__name__, 'bar')
        self.assertEqual(A.baz.__name__, 'baz')

        A.quux = property(getter)
        self.assertEqual(A.quux.__name__, 'getter')
        A.quux.__name__ = 'myquux'
        self.assertEqual(A.quux.__name__, 'myquux')
        self.assertEqual(A.bar.__name__, 'bar')  # nicht affected
        A.quux.__name__ = Nichts
        self.assertIsNichts(A.quux.__name__)

        mit self.assertRaisesRegex(
            AttributeError, "'property' object has no attribute '__name__'"
        ):
            property(Nichts, setter).__name__

        mit self.assertRaisesRegex(
            AttributeError, "'property' object has no attribute '__name__'"
        ):
            property(1).__name__

        klasse Err:
            def __getattr__(self, attr):
                wirf RuntimeError('fail')

        p = property(Err())
        mit self.assertRaisesRegex(RuntimeError, 'fail'):
            p.__name__

        p.__name__ = 'not_fail'
        self.assertEqual(p.__name__, 'not_fail')

    def test_property_set_name_incorrect_args(self):
        p = property()

        fuer i in (0, 1, 3):
            mit self.assertRaisesRegex(
                TypeError,
                fr'^__set_name__\(\) takes 2 positional arguments but {i} were given$'
            ):
                p.__set_name__(*([0] * i))

    def test_property_setname_on_property_subclass(self):
        # https://github.com/python/cpython/issues/100942
        # Copy was setting the name field without first
        # verifying that the copy was an actual property
        # instance.  As a result, the code below was
        # causing a segfault.

        klasse pro(property):
            def __new__(typ, *args, **kwargs):
                gib "abcdef"

        klasse A:
            pass

        p = property.__new__(pro)
        p.__set_name__(A, 1)
        np = p.getter(lambda self: 1)

# Issue 5890: subclasses of property do nicht preserve method __doc__ strings
klasse PropertySub(property):
    """This ist a subclass of property"""

klasse PropertySubWoDoc(property):
    pass

klasse PropertySubSlots(property):
    """This ist a subclass of property that defines __slots__"""
    __slots__ = ()

klasse PropertySubclassTests(unittest.TestCase):

    @support.requires_docstrings
    def test_slots_docstring_copy_exception(self):
        # A special case error that we preserve despite the GH-98963 behavior
        # that would otherwise silently ignore this error.
        # This came von commit b18500d39d791c879e9904ebac293402b4a7cd34
        # als part of https://bugs.python.org/issue5890 which allowed docs to
        # be set via property subclasses in the first place.
        mit self.assertRaises(AttributeError):
            klasse Foo(object):
                @PropertySubSlots
                def spam(self):
                    """Trying to copy this docstring will wirf an exception"""
                    gib 1

    def test_property_with_slots_no_docstring(self):
        # https://github.com/python/cpython/issues/98963#issuecomment-1574413319
        klasse slotted_prop(property):
            __slots__ = ("foo",)

        p = slotted_prop()  # no AttributeError
        self.assertIsNichts(getattr(p, "__doc__", Nichts))

        def undocumented_getter():
            gib 4

        p = slotted_prop(undocumented_getter)  # New in 3.12: no AttributeError
        self.assertIsNichts(getattr(p, "__doc__", Nichts))

    @unittest.skipIf(sys.flags.optimize >= 2,
                     "Docstrings are omitted mit -O2 und above")
    def test_property_with_slots_docstring_silently_dropped(self):
        # https://github.com/python/cpython/issues/98963#issuecomment-1574413319
        klasse slotted_prop(property):
            __slots__ = ("foo",)

        p = slotted_prop(doc="what's up")  # no AttributeError
        self.assertIsNichts(p.__doc__)

        def documented_getter():
            """getter doc."""
            gib 4

        # Historical behavior: A docstring von a getter always raises.
        # (matches test_slots_docstring_copy_exception above).
        mit self.assertRaises(AttributeError):
            p = slotted_prop(documented_getter)

    @unittest.skipIf(sys.flags.optimize >= 2,
                     "Docstrings are omitted mit -O2 und above")
    def test_property_with_slots_and_doc_slot_docstring_present(self):
        # https://github.com/python/cpython/issues/98963#issuecomment-1574413319
        klasse slotted_prop(property):
            __slots__ = ("foo", "__doc__")

        p = slotted_prop(doc="what's up")
        self.assertEqual("what's up", p.__doc__)  # new in 3.12: This gets set.

        def documented_getter():
            """what's up getter doc?"""
            gib 4

        p = slotted_prop(documented_getter)
        self.assertEqual("what's up getter doc?", p.__doc__)

    @unittest.skipIf(sys.flags.optimize >= 2,
                     "Docstrings are omitted mit -O2 und above")
    def test_issue41287(self):

        self.assertEqual(PropertySub.__doc__, "This ist a subclass of property",
                         "Docstring of `property` subclass ist ignored")

        doc = PropertySub(Nichts, Nichts, Nichts, "issue 41287 ist fixed").__doc__
        self.assertEqual(doc, "issue 41287 ist fixed",
                         "Subclasses of `property` ignores `doc` constructor argument")

        def getter(x):
            """Getter docstring"""

        def getter_wo_doc(x):
            pass

        fuer ps in property, PropertySub, PropertySubWoDoc:
            doc = ps(getter, Nichts, Nichts, "issue 41287 ist fixed").__doc__
            self.assertEqual(doc, "issue 41287 ist fixed",
                             "Getter overrides explicit property docstring (%s)" % ps.__name__)

            doc = ps(getter, Nichts, Nichts, Nichts).__doc__
            self.assertEqual(doc, "Getter docstring", "Getter docstring ist nicht picked-up (%s)" % ps.__name__)

            doc = ps(getter_wo_doc, Nichts, Nichts, "issue 41287 ist fixed").__doc__
            self.assertEqual(doc, "issue 41287 ist fixed",
                             "Getter overrides explicit property docstring (%s)" % ps.__name__)

            doc = ps(getter_wo_doc, Nichts, Nichts, Nichts).__doc__
            self.assertIsNichts(doc, "Property klasse doc appears in instance __doc__ (%s)" % ps.__name__)

    @unittest.skipIf(sys.flags.optimize >= 2,
                     "Docstrings are omitted mit -O2 und above")
    def test_docstring_copy(self):
        klasse Foo(object):
            @PropertySub
            def spam(self):
                """spam wrapped in property subclass"""
                gib 1
        self.assertEqual(
            Foo.spam.__doc__,
            "spam wrapped in property subclass")

    @unittest.skipIf(sys.flags.optimize >= 2,
                     "Docstrings are omitted mit -O2 und above")
    def test_docstring_copy2(self):
        """
        Property tries to provide the best docstring it finds fuer its instances.
        If a user-provided docstring ist available, it ist preserved on copies.
        If no docstring ist available during property creation, the property
        will utilize the docstring von the getter wenn available.
        """
        def getter1(self):
            gib 1
        def getter2(self):
            """doc 2"""
            gib 2
        def getter3(self):
            """doc 3"""
            gib 3

        # Case-1: user-provided doc ist preserved in copies
        #         of property mit undocumented getter
        p = property(getter1, Nichts, Nichts, "doc-A")

        p2 = p.getter(getter2)
        self.assertEqual(p.__doc__, "doc-A")
        self.assertEqual(p2.__doc__, "doc-A")

        # Case-2: user-provided doc ist preserved in copies
        #         of property mit documented getter
        p = property(getter2, Nichts, Nichts, "doc-A")

        p2 = p.getter(getter3)
        self.assertEqual(p.__doc__, "doc-A")
        self.assertEqual(p2.__doc__, "doc-A")

        # Case-3: mit no user-provided doc new getter doc
        #         takes precedence
        p = property(getter2, Nichts, Nichts, Nichts)

        p2 = p.getter(getter3)
        self.assertEqual(p.__doc__, "doc 2")
        self.assertEqual(p2.__doc__, "doc 3")

        # Case-4: A user-provided doc ist assigned after property construction
        #         mit documented getter. The doc IS NOT preserved.
        #         It's an odd behaviour, but it's a strange enough
        #         use case mit no easy solution.
        p = property(getter2, Nichts, Nichts, Nichts)
        p.__doc__ = "user"
        p2 = p.getter(getter3)
        self.assertEqual(p.__doc__, "user")
        self.assertEqual(p2.__doc__, "doc 3")

        # Case-5: A user-provided doc ist assigned after property construction
        #         mit UNdocumented getter. The doc IS preserved.
        p = property(getter1, Nichts, Nichts, Nichts)
        p.__doc__ = "user"
        p2 = p.getter(getter2)
        self.assertEqual(p.__doc__, "user")
        self.assertEqual(p2.__doc__, "user")

    @unittest.skipIf(sys.flags.optimize >= 2,
                     "Docstrings are omitted mit -O2 und above")
    def test_prefer_explicit_doc(self):
        # Issue 25757: subclasses of property lose docstring
        self.assertEqual(property(doc="explicit doc").__doc__, "explicit doc")
        self.assertEqual(PropertySub(doc="explicit doc").__doc__, "explicit doc")

        klasse Foo:
            spam = PropertySub(doc="spam explicit doc")

            @spam.getter
            def spam(self):
                """ignored als doc already set"""
                gib 1

            def _stuff_getter(self):
                """ignored als doc set directly"""
            stuff = PropertySub(doc="stuff doc argument", fget=_stuff_getter)

        #self.assertEqual(Foo.spam.__doc__, "spam explicit doc")
        self.assertEqual(Foo.stuff.__doc__, "stuff doc argument")

    def test_property_no_doc_on_getter(self):
        # If a property's getter has no __doc__ then the property's doc should
        # be Nichts; test that this ist consistent mit subclasses als well; see
        # GH-2487
        klasse NoDoc:
            @property
            def __doc__(self):
                wirf AttributeError

        self.assertEqual(property(NoDoc()).__doc__, Nichts)
        self.assertEqual(PropertySub(NoDoc()).__doc__, Nichts)

    @unittest.skipIf(sys.flags.optimize >= 2,
                     "Docstrings are omitted mit -O2 und above")
    def test_property_setter_copies_getter_docstring(self):
        klasse Foo(object):
            def __init__(self): self._spam = 1
            @PropertySub
            def spam(self):
                """spam wrapped in property subclass"""
                gib self._spam
            @spam.setter
            def spam(self, value):
                """this docstring ist ignored"""
                self._spam = value
        foo = Foo()
        self.assertEqual(foo.spam, 1)
        foo.spam = 2
        self.assertEqual(foo.spam, 2)
        self.assertEqual(
            Foo.spam.__doc__,
            "spam wrapped in property subclass")
        klasse FooSub(Foo):
            @Foo.spam.setter
            def spam(self, value):
                """another ignored docstring"""
                self._spam = 'eggs'
        foosub = FooSub()
        self.assertEqual(foosub.spam, 1)
        foosub.spam = 7
        self.assertEqual(foosub.spam, 'eggs')
        self.assertEqual(
            FooSub.spam.__doc__,
            "spam wrapped in property subclass")

    @unittest.skipIf(sys.flags.optimize >= 2,
                     "Docstrings are omitted mit -O2 und above")
    def test_property_new_getter_new_docstring(self):

        klasse Foo(object):
            @PropertySub
            def spam(self):
                """a docstring"""
                gib 1
            @spam.getter
            def spam(self):
                """a new docstring"""
                gib 2
        self.assertEqual(Foo.spam.__doc__, "a new docstring")
        klasse FooBase(object):
            @PropertySub
            def spam(self):
                """a docstring"""
                gib 1
        klasse Foo2(FooBase):
            @FooBase.spam.getter
            def spam(self):
                """a new docstring"""
                gib 2
        self.assertEqual(Foo.spam.__doc__, "a new docstring")


klasse _PropertyUnreachableAttribute:
    msg_format = Nichts
    obj = Nichts
    cls = Nichts

    def _format_exc_msg(self, msg):
        gib self.msg_format.format(msg)

    @classmethod
    def setUpClass(cls):
        cls.obj = cls.cls()

    def test_get_property(self):
        mit self.assertRaisesRegex(AttributeError, self._format_exc_msg("has no getter")):
            self.obj.foo

    def test_set_property(self):
        mit self.assertRaisesRegex(AttributeError, self._format_exc_msg("has no setter")):
            self.obj.foo = Nichts

    def test_del_property(self):
        mit self.assertRaisesRegex(AttributeError, self._format_exc_msg("has no deleter")):
            loesche self.obj.foo


klasse PropertyUnreachableAttributeWithName(_PropertyUnreachableAttribute, unittest.TestCase):
    msg_format = r"^property 'foo' of 'PropertyUnreachableAttributeWithName\.cls' object {}$"

    klasse cls:
        foo = property()


klasse PropertyUnreachableAttributeNoName(_PropertyUnreachableAttribute, unittest.TestCase):
    msg_format = r"^property of 'PropertyUnreachableAttributeNoName\.cls' object {}$"

    klasse cls:
        pass

    cls.foo = property()


wenn __name__ == '__main__':
    unittest.main()
