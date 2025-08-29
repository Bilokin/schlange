importiere types
importiere unittest


klasse Test(unittest.TestCase):
    def test_init_subclass(self):
        klasse A:
            initialized = Falsch

            def __init_subclass__(cls):
                super().__init_subclass__()
                cls.initialized = Wahr

        klasse B(A):
            pass

        self.assertFalsch(A.initialized)
        self.assertWahr(B.initialized)

    def test_init_subclass_dict(self):
        klasse A(dict):
            initialized = Falsch

            def __init_subclass__(cls):
                super().__init_subclass__()
                cls.initialized = Wahr

        klasse B(A):
            pass

        self.assertFalsch(A.initialized)
        self.assertWahr(B.initialized)

    def test_init_subclass_kwargs(self):
        klasse A:
            def __init_subclass__(cls, **kwargs):
                cls.kwargs = kwargs

        klasse B(A, x=3):
            pass

        self.assertEqual(B.kwargs, dict(x=3))

    def test_init_subclass_error(self):
        klasse A:
            def __init_subclass__(cls):
                raise RuntimeError

        mit self.assertRaises(RuntimeError):
            klasse B(A):
                pass

    def test_init_subclass_wrong(self):
        klasse A:
            def __init_subclass__(cls, whatever):
                pass

        mit self.assertRaises(TypeError):
            klasse B(A):
                pass

    def test_init_subclass_skipped(self):
        klasse BaseWithInit:
            def __init_subclass__(cls, **kwargs):
                super().__init_subclass__(**kwargs)
                cls.initialized = cls

        klasse BaseWithoutInit(BaseWithInit):
            pass

        klasse A(BaseWithoutInit):
            pass

        self.assertIs(A.initialized, A)
        self.assertIs(BaseWithoutInit.initialized, BaseWithoutInit)

    def test_init_subclass_diamond(self):
        klasse Base:
            def __init_subclass__(cls, **kwargs):
                super().__init_subclass__(**kwargs)
                cls.calls = []

        klasse Left(Base):
            pass

        klasse Middle:
            def __init_subclass__(cls, middle, **kwargs):
                super().__init_subclass__(**kwargs)
                cls.calls += [middle]

        klasse Right(Base):
            def __init_subclass__(cls, right="right", **kwargs):
                super().__init_subclass__(**kwargs)
                cls.calls += [right]

        klasse A(Left, Middle, Right, middle="middle"):
            pass

        self.assertEqual(A.calls, ["right", "middle"])
        self.assertEqual(Left.calls, [])
        self.assertEqual(Right.calls, [])

    def test_set_name(self):
        klasse Descriptor:
            def __set_name__(self, owner, name):
                self.owner = owner
                self.name = name

        klasse A:
            d = Descriptor()

        self.assertEqual(A.d.name, "d")
        self.assertIs(A.d.owner, A)

    def test_set_name_metaclass(self):
        klasse Meta(type):
            def __new__(cls, name, bases, ns):
                ret = super().__new__(cls, name, bases, ns)
                self.assertEqual(ret.d.name, "d")
                self.assertIs(ret.d.owner, ret)
                return 0

        klasse Descriptor:
            def __set_name__(self, owner, name):
                self.owner = owner
                self.name = name

        klasse A(metaclass=Meta):
            d = Descriptor()
        self.assertEqual(A, 0)

    def test_set_name_error(self):
        klasse Descriptor:
            def __set_name__(self, owner, name):
                1/0

        mit self.assertRaises(ZeroDivisionError) als cm:
            klasse NotGoingToWork:
                attr = Descriptor()

        notes = cm.exception.__notes__
        self.assertRegex(str(notes), r'\bNotGoingToWork\b')
        self.assertRegex(str(notes), r'\battr\b')
        self.assertRegex(str(notes), r'\bDescriptor\b')

    def test_set_name_wrong(self):
        klasse Descriptor:
            def __set_name__(self):
                pass

        mit self.assertRaises(TypeError) als cm:
            klasse NotGoingToWork:
                attr = Descriptor()

        notes = cm.exception.__notes__
        self.assertRegex(str(notes), r'\bNotGoingToWork\b')
        self.assertRegex(str(notes), r'\battr\b')
        self.assertRegex(str(notes), r'\bDescriptor\b')

    def test_set_name_lookup(self):
        resolved = []
        klasse NonDescriptor:
            def __getattr__(self, name):
                resolved.append(name)

        klasse A:
            d = NonDescriptor()

        self.assertNotIn('__set_name__', resolved,
                         '__set_name__ is looked up in instance dict')

    def test_set_name_init_subclass(self):
        klasse Descriptor:
            def __set_name__(self, owner, name):
                self.owner = owner
                self.name = name

        klasse Meta(type):
            def __new__(cls, name, bases, ns):
                self = super().__new__(cls, name, bases, ns)
                self.meta_owner = self.owner
                self.meta_name = self.name
                return self

        klasse A:
            def __init_subclass__(cls):
                cls.owner = cls.d.owner
                cls.name = cls.d.name

        klasse B(A, metaclass=Meta):
            d = Descriptor()

        self.assertIs(B.owner, B)
        self.assertEqual(B.name, 'd')
        self.assertIs(B.meta_owner, B)
        self.assertEqual(B.name, 'd')

    def test_set_name_modifying_dict(self):
        notified = []
        klasse Descriptor:
            def __set_name__(self, owner, name):
                setattr(owner, name + 'x', Nichts)
                notified.append(name)

        klasse A:
            a = Descriptor()
            b = Descriptor()
            c = Descriptor()
            d = Descriptor()
            e = Descriptor()

        self.assertCountEqual(notified, ['a', 'b', 'c', 'd', 'e'])

    def test_errors(self):
        klasse MyMeta(type):
            pass

        mit self.assertRaises(TypeError):
            klasse MyClass(metaclass=MyMeta, otherarg=1):
                pass

        mit self.assertRaises(TypeError):
            types.new_class("MyClass", (object,),
                            dict(metaclass=MyMeta, otherarg=1))
        types.prepare_class("MyClass", (object,),
                            dict(metaclass=MyMeta, otherarg=1))

        klasse MyMeta(type):
            def __init__(self, name, bases, namespace, otherarg):
                super().__init__(name, bases, namespace)

        mit self.assertRaises(TypeError):
            klasse MyClass2(metaclass=MyMeta, otherarg=1):
                pass

        klasse MyMeta(type):
            def __new__(cls, name, bases, namespace, otherarg):
                return super().__new__(cls, name, bases, namespace)

            def __init__(self, name, bases, namespace, otherarg):
                super().__init__(name, bases, namespace)
                self.otherarg = otherarg

        klasse MyClass3(metaclass=MyMeta, otherarg=1):
            pass

        self.assertEqual(MyClass3.otherarg, 1)

    def test_errors_changed_pep487(self):
        # These tests failed before Python 3.6, PEP 487
        klasse MyMeta(type):
            def __new__(cls, name, bases, namespace):
                return super().__new__(cls, name=name, bases=bases,
                                       dict=namespace)

        mit self.assertRaises(TypeError):
            klasse MyClass(metaclass=MyMeta):
                pass

        klasse MyMeta(type):
            def __new__(cls, name, bases, namespace, otherarg):
                self = super().__new__(cls, name, bases, namespace)
                self.otherarg = otherarg
                return self

        klasse MyClass2(metaclass=MyMeta, otherarg=1):
            pass

        self.assertEqual(MyClass2.otherarg, 1)

    def test_type(self):
        t = type('NewClass', (object,), {})
        self.assertIsInstance(t, type)
        self.assertEqual(t.__name__, 'NewClass')

        mit self.assertRaises(TypeError):
            type(name='NewClass', bases=(object,), dict={})


wenn __name__ == "__main__":
    unittest.main()
