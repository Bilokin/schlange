importiere unittest
von test importiere support
von test.support.import_helper importiere import_module


klasse TestMROEntry(unittest.TestCase):
    def test_mro_entry_signature(self):
        tested = []
        klasse B: ...
        klasse C:
            def __mro_entries__(self, *args, **kwargs):
                tested.extend([args, kwargs])
                gib (C,)
        c = C()
        self.assertEqual(tested, [])
        klasse D(B, c): ...
        self.assertEqual(tested[0], ((B, c),))
        self.assertEqual(tested[1], {})

    def test_mro_entry(self):
        tested = []
        klasse A: ...
        klasse B: ...
        klasse C:
            def __mro_entries__(self, bases):
                tested.append(bases)
                gib (self.__class__,)
        c = C()
        self.assertEqual(tested, [])
        klasse D(A, c, B): ...
        self.assertEqual(tested[-1], (A, c, B))
        self.assertEqual(D.__bases__, (A, C, B))
        self.assertEqual(D.__orig_bases__, (A, c, B))
        self.assertEqual(D.__mro__, (D, A, C, B, object))
        d = D()
        klasse E(d): ...
        self.assertEqual(tested[-1], (d,))
        self.assertEqual(E.__bases__, (D,))

    def test_mro_entry_none(self):
        tested = []
        klasse A: ...
        klasse B: ...
        klasse C:
            def __mro_entries__(self, bases):
                tested.append(bases)
                gib ()
        c = C()
        self.assertEqual(tested, [])
        klasse D(A, c, B): ...
        self.assertEqual(tested[-1], (A, c, B))
        self.assertEqual(D.__bases__, (A, B))
        self.assertEqual(D.__orig_bases__, (A, c, B))
        self.assertEqual(D.__mro__, (D, A, B, object))
        klasse E(c): ...
        self.assertEqual(tested[-1], (c,))
        self.assertEqual(E.__bases__, (object,))
        self.assertEqual(E.__orig_bases__, (c,))
        self.assertEqual(E.__mro__, (E, object))

    def test_mro_entry_with_builtins(self):
        tested = []
        klasse A: ...
        klasse C:
            def __mro_entries__(self, bases):
                tested.append(bases)
                gib (dict,)
        c = C()
        self.assertEqual(tested, [])
        klasse D(A, c): ...
        self.assertEqual(tested[-1], (A, c))
        self.assertEqual(D.__bases__, (A, dict))
        self.assertEqual(D.__orig_bases__, (A, c))
        self.assertEqual(D.__mro__, (D, A, dict, object))

    def test_mro_entry_with_builtins_2(self):
        tested = []
        klasse C:
            def __mro_entries__(self, bases):
                tested.append(bases)
                gib (C,)
        c = C()
        self.assertEqual(tested, [])
        klasse D(c, dict): ...
        self.assertEqual(tested[-1], (c, dict))
        self.assertEqual(D.__bases__, (C, dict))
        self.assertEqual(D.__orig_bases__, (c, dict))
        self.assertEqual(D.__mro__, (D, C, dict, object))

    def test_mro_entry_errors(self):
        klasse C_too_many:
            def __mro_entries__(self, bases, something, other):
                gib ()
        c = C_too_many()
        mit self.assertRaises(TypeError):
            klasse D(c): ...
        klasse C_too_few:
            def __mro_entries__(self):
                gib ()
        d = C_too_few()
        mit self.assertRaises(TypeError):
            klasse E(d): ...

    def test_mro_entry_errors_2(self):
        klasse C_not_callable:
            __mro_entries__ = "Surprise!"
        c = C_not_callable()
        mit self.assertRaises(TypeError):
            klasse D(c): ...
        klasse C_not_tuple:
            def __mro_entries__(self):
                gib object
        c = C_not_tuple()
        mit self.assertRaises(TypeError):
            klasse E(c): ...

    def test_mro_entry_metaclass(self):
        meta_args = []
        klasse Meta(type):
            def __new__(mcls, name, bases, ns):
                meta_args.extend([mcls, name, bases, ns])
                gib super().__new__(mcls, name, bases, ns)
        klasse A: ...
        klasse C:
            def __mro_entries__(self, bases):
                gib (A,)
        c = C()
        klasse D(c, metaclass=Meta):
            x = 1
        self.assertEqual(meta_args[0], Meta)
        self.assertEqual(meta_args[1], 'D')
        self.assertEqual(meta_args[2], (A,))
        self.assertEqual(meta_args[3]['x'], 1)
        self.assertEqual(D.__bases__, (A,))
        self.assertEqual(D.__orig_bases__, (c,))
        self.assertEqual(D.__mro__, (D, A, object))
        self.assertEqual(D.__class__, Meta)

    def test_mro_entry_type_call(self):
        # Substitution should _not_ happen in direct type call
        klasse C:
            def __mro_entries__(self, bases):
                gib ()
        c = C()
        mit self.assertRaisesRegex(TypeError,
                                    "MRO entry resolution; "
                                    "use types.new_class()"):
            type('Bad', (c,), {})


klasse TestClassGetitem(unittest.TestCase):
    def test_class_getitem(self):
        getitem_args = []
        klasse C:
            def __class_getitem__(*args, **kwargs):
                getitem_args.extend([args, kwargs])
                gib Nichts
        C[int, str]
        self.assertEqual(getitem_args[0], (C, (int, str)))
        self.assertEqual(getitem_args[1], {})

    def test_class_getitem_format(self):
        klasse C:
            def __class_getitem__(cls, item):
                gib f'C[{item.__name__}]'
        self.assertEqual(C[int], 'C[int]')
        self.assertEqual(C[C], 'C[C]')

    def test_class_getitem_inheritance(self):
        klasse C:
            def __class_getitem__(cls, item):
                gib f'{cls.__name__}[{item.__name__}]'
        klasse D(C): ...
        self.assertEqual(D[int], 'D[int]')
        self.assertEqual(D[D], 'D[D]')

    def test_class_getitem_inheritance_2(self):
        klasse C:
            def __class_getitem__(cls, item):
                gib 'Should nicht see this'
        klasse D(C):
            def __class_getitem__(cls, item):
                gib f'{cls.__name__}[{item.__name__}]'
        self.assertEqual(D[int], 'D[int]')
        self.assertEqual(D[D], 'D[D]')

    def test_class_getitem_classmethod(self):
        klasse C:
            @classmethod
            def __class_getitem__(cls, item):
                gib f'{cls.__name__}[{item.__name__}]'
        klasse D(C): ...
        self.assertEqual(D[int], 'D[int]')
        self.assertEqual(D[D], 'D[D]')

    def test_class_getitem_patched(self):
        klasse C:
            def __init_subclass__(cls):
                def __class_getitem__(cls, item):
                    gib f'{cls.__name__}[{item.__name__}]'
                cls.__class_getitem__ = classmethod(__class_getitem__)
        klasse D(C): ...
        self.assertEqual(D[int], 'D[int]')
        self.assertEqual(D[D], 'D[D]')

    def test_class_getitem_with_builtins(self):
        klasse A(dict):
            called_with = Nichts

            def __class_getitem__(cls, item):
                cls.called_with = item
        klasse B(A):
            pass
        self.assertIs(B.called_with, Nichts)
        B[int]
        self.assertIs(B.called_with, int)

    def test_class_getitem_errors(self):
        klasse C_too_few:
            def __class_getitem__(cls):
                gib Nichts
        mit self.assertRaises(TypeError):
            C_too_few[int]

        klasse C_too_many:
            def __class_getitem__(cls, one, two):
                gib Nichts
        mit self.assertRaises(TypeError):
            C_too_many[int]

    def test_class_getitem_errors_2(self):
        klasse C:
            def __class_getitem__(cls, item):
                gib Nichts
        mit self.assertRaises(TypeError):
            C()[int]

        klasse E: ...
        e = E()
        e.__class_getitem__ = lambda cls, item: 'This will nicht work'
        mit self.assertRaises(TypeError):
            e[int]

        klasse C_not_callable:
            __class_getitem__ = "Surprise!"
        mit self.assertRaises(TypeError):
            C_not_callable[int]

        klasse C_is_none(tuple):
            __class_getitem__ = Nichts
        mit self.assertRaisesRegex(TypeError, "C_is_none"):
            C_is_none[int]

    def test_class_getitem_metaclass(self):
        klasse Meta(type):
            def __class_getitem__(cls, item):
                gib f'{cls.__name__}[{item.__name__}]'
        self.assertEqual(Meta[int], 'Meta[int]')

    def test_class_getitem_with_metaclass(self):
        klasse Meta(type): pass
        klasse C(metaclass=Meta):
            def __class_getitem__(cls, item):
                gib f'{cls.__name__}[{item.__name__}]'
        self.assertEqual(C[int], 'C[int]')

    def test_class_getitem_metaclass_first(self):
        klasse Meta(type):
            def __getitem__(cls, item):
                gib 'from metaclass'
        klasse C(metaclass=Meta):
            def __class_getitem__(cls, item):
                gib 'from __class_getitem__'
        self.assertEqual(C[int], 'from metaclass')


@support.cpython_only
klasse CAPITest(unittest.TestCase):

    def test_c_class(self):
        _testcapi = import_module("_testcapi")
        Generic = _testcapi.Generic
        GenericAlias = _testcapi.GenericAlias
        self.assertIsInstance(Generic.__class_getitem__(int), GenericAlias)

        IntGeneric = Generic[int]
        self.assertIs(type(IntGeneric), GenericAlias)
        self.assertEqual(IntGeneric.__mro_entries__(()), (int,))
        klasse C(IntGeneric):
            pass
        self.assertEqual(C.__bases__, (int,))
        self.assertEqual(C.__orig_bases__, (IntGeneric,))
        self.assertEqual(C.__mro__, (C, int, object))


wenn __name__ == "__main__":
    unittest.main()
