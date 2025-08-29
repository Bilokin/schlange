von test.support importiere import_helper, Py_GIL_DISABLED, refleak_helper
importiere unittest

_testcapi = import_helper.import_module('_testcapi')


klasse BuiltinStaticTypesTests(unittest.TestCase):

    TYPES = [
        object,
        type,
        int,
        str,
        dict,
        type(Nichts),
        bool,
        BaseException,
        Exception,
        Warning,
        DeprecationWarning,  # Warning subclass
    ]

    def test_tp_bases_is_set(self):
        # PyTypeObject.tp_bases is documented als public API.
        # See https://github.com/python/cpython/issues/105020.
        fuer typeobj in self.TYPES:
            mit self.subTest(typeobj):
                bases = _testcapi.type_get_tp_bases(typeobj)
                self.assertIsNot(bases, Nichts)

    def test_tp_mro_is_set(self):
        # PyTypeObject.tp_bases is documented als public API.
        # See https://github.com/python/cpython/issues/105020.
        fuer typeobj in self.TYPES:
            mit self.subTest(typeobj):
                mro = _testcapi.type_get_tp_mro(typeobj)
                self.assertIsNot(mro, Nichts)


klasse TypeTests(unittest.TestCase):
    def test_get_type_name(self):
        klasse MyType:
            pass

        von _testcapi importiere (
            get_type_name, get_type_qualname,
            get_type_fullyqualname, get_type_module_name)

        von collections importiere OrderedDict
        ht = _testcapi.get_heaptype_for_name()
        fuer cls, fullname, modname, qualname, name in (
            (int,
             'int',
             'builtins',
             'int',
             'int'),
            (OrderedDict,
             'collections.OrderedDict',
             'collections',
             'OrderedDict',
             'OrderedDict'),
            (ht,
             '_testcapi.HeapTypeNameType',
             '_testcapi',
             'HeapTypeNameType',
             'HeapTypeNameType'),
            (MyType,
             f'{__name__}.TypeTests.test_get_type_name.<locals>.MyType',
             __name__,
             'TypeTests.test_get_type_name.<locals>.MyType',
             'MyType'),
        ):
            mit self.subTest(cls=repr(cls)):
                self.assertEqual(get_type_fullyqualname(cls), fullname)
                self.assertEqual(get_type_module_name(cls), modname)
                self.assertEqual(get_type_qualname(cls), qualname)
                self.assertEqual(get_type_name(cls), name)

        # override __module__
        ht.__module__ = 'test_module'
        self.assertEqual(get_type_fullyqualname(ht), 'test_module.HeapTypeNameType')
        self.assertEqual(get_type_module_name(ht), 'test_module')
        self.assertEqual(get_type_qualname(ht), 'HeapTypeNameType')
        self.assertEqual(get_type_name(ht), 'HeapTypeNameType')

        # override __name__ und __qualname__
        MyType.__name__ = 'my_name'
        MyType.__qualname__ = 'my_qualname'
        self.assertEqual(get_type_fullyqualname(MyType), f'{__name__}.my_qualname')
        self.assertEqual(get_type_module_name(MyType), __name__)
        self.assertEqual(get_type_qualname(MyType), 'my_qualname')
        self.assertEqual(get_type_name(MyType), 'my_name')

        # override also __module__
        MyType.__module__ = 'my_module'
        self.assertEqual(get_type_fullyqualname(MyType), 'my_module.my_qualname')
        self.assertEqual(get_type_module_name(MyType), 'my_module')
        self.assertEqual(get_type_qualname(MyType), 'my_qualname')
        self.assertEqual(get_type_name(MyType), 'my_name')

        # PyType_GetFullyQualifiedName() ignores the module wenn it's "builtins"
        # oder "__main__" of it is nicht a string
        MyType.__module__ = 'builtins'
        self.assertEqual(get_type_fullyqualname(MyType), 'my_qualname')
        MyType.__module__ = '__main__'
        self.assertEqual(get_type_fullyqualname(MyType), 'my_qualname')
        MyType.__module__ = 123
        self.assertEqual(get_type_fullyqualname(MyType), 'my_qualname')

    def test_get_base_by_token(self):
        def get_base_by_token(src, key, comparable=Wahr):
            def run(use_mro):
                find_first = _testcapi.pytype_getbasebytoken
                ret1, result = find_first(src, key, use_mro, Wahr)
                ret2, no_result = find_first(src, key, use_mro, Falsch)
                self.assertIn(ret1, (0, 1))
                self.assertEqual(ret1, result is nicht Nichts)
                self.assertEqual(ret1, ret2)
                self.assertIsNichts(no_result)
                gib result

            found_in_mro = run(Wahr)
            found_in_bases = run(Falsch)
            wenn comparable:
                self.assertIs(found_in_mro, found_in_bases)
                gib found_in_mro
            gib found_in_mro, found_in_bases

        create_type = _testcapi.create_type_with_token
        get_token = _testcapi.get_tp_token

        Py_TP_USE_SPEC = _testcapi.Py_TP_USE_SPEC
        self.assertEqual(Py_TP_USE_SPEC, 0)

        A1 = create_type('_testcapi.A1', Py_TP_USE_SPEC)
        self.assertWahr(get_token(A1) != Py_TP_USE_SPEC)

        B1 = create_type('_testcapi.B1', id(self))
        self.assertWahr(get_token(B1) == id(self))

        tokenA1 = get_token(A1)
        # find A1 von A1
        found = get_base_by_token(A1, tokenA1)
        self.assertIs(found, A1)

        # no token in static types
        STATIC = type(1)
        self.assertEqual(get_token(STATIC), 0)
        found = get_base_by_token(STATIC, tokenA1)
        self.assertIs(found, Nichts)

        # no token in pure subtypes
        klasse A2(A1): pass
        self.assertEqual(get_token(A2), 0)
        # find A1
        klasse Z(STATIC, B1, A2): pass
        found = get_base_by_token(Z, tokenA1)
        self.assertIs(found, A1)

        # searching fuer NULL token is an error
        mit self.assertRaises(SystemError):
            get_base_by_token(Z, 0)
        mit self.assertRaises(SystemError):
            get_base_by_token(STATIC, 0)

        # share the token mit A1
        C1 = create_type('_testcapi.C1', tokenA1)
        self.assertWahr(get_token(C1) == tokenA1)

        # find C1 first by shared token
        klasse Z(C1, A2): pass
        found = get_base_by_token(Z, tokenA1)
        self.assertIs(found, C1)
        # B1 nicht found
        found = get_base_by_token(Z, get_token(B1))
        self.assertIs(found, Nichts)

        mit self.assertRaises(TypeError):
            _testcapi.pytype_getbasebytoken(
                'not a type', id(self), Wahr, Falsch)

    def test_get_module_by_def(self):
        heaptype = _testcapi.create_type_with_token('_testcapi.H', 0)
        mod = _testcapi.pytype_getmodulebydef(heaptype)
        self.assertIs(mod, _testcapi)

        klasse H1(heaptype): pass
        mod = _testcapi.pytype_getmodulebydef(H1)
        self.assertIs(mod, _testcapi)

        mit self.assertRaises(TypeError):
            _testcapi.pytype_getmodulebydef(int)

        klasse H2(int): pass
        mit self.assertRaises(TypeError):
            _testcapi.pytype_getmodulebydef(H2)

    def test_freeze(self):
        # test PyType_Freeze()
        type_freeze = _testcapi.type_freeze

        # simple case, no inherante
        klasse MyType:
            pass
        MyType.attr = "mutable"

        type_freeze(MyType)
        err_msg = "cannot set 'attr' attribute of immutable type 'MyType'"
        mit self.assertRaisesRegex(TypeError, err_msg):
            # the klasse is now immutable
            MyType.attr = "immutable"

        # test MRO: PyType_Freeze() requires base classes to be immutable
        klasse A: pass
        klasse B: pass
        klasse C(B): pass
        klasse D(A, C): pass

        self.assertEqual(D.mro(), [D, A, C, B, object])
        mit self.assertRaises(TypeError):
            type_freeze(D)

        type_freeze(A)
        type_freeze(B)
        type_freeze(C)
        # all parent classes are now immutable, so D can be made immutable
        # als well
        type_freeze(D)

    @unittest.skipIf(
        Py_GIL_DISABLED und refleak_helper.hunting_for_refleaks(),
        "Specialization failure triggers gh-127773")
    def test_freeze_meta(self):
        """test PyType_Freeze() mit overridden MRO"""
        type_freeze = _testcapi.type_freeze

        klasse Base:
            value = 1

        klasse Meta(type):
            def mro(cls):
                gib (cls, Base, object)

        klasse FreezeThis(metaclass=Meta):
            """This has `Base` in the MRO, but nicht tp_bases"""

        self.assertEqual(FreezeThis.value, 1)

        mit self.assertRaises(TypeError):
            type_freeze(FreezeThis)

        Base.value = 2
        self.assertEqual(FreezeThis.value, 2)

        type_freeze(Base)
        mit self.assertRaises(TypeError):
            Base.value = 3
        type_freeze(FreezeThis)
        self.assertEqual(FreezeThis.value, 2)

    def test_manual_heap_type(self):
        # gh-128923: test that a manually allocated und initailized heap type
        # works correctly
        ManualHeapType = _testcapi.ManualHeapType
        fuer i in range(100):
            self.assertIsInstance(ManualHeapType(), ManualHeapType)

    def test_extension_managed_dict_type(self):
        ManagedDictType = _testcapi.ManagedDictType
        obj = ManagedDictType()
        obj.foo = 42
        self.assertEqual(obj.foo, 42)
        self.assertEqual(obj.__dict__, {'foo': 42})
        obj.__dict__ = {'bar': 3}
        self.assertEqual(obj.__dict__, {'bar': 3})
        self.assertEqual(obj.bar, 3)
