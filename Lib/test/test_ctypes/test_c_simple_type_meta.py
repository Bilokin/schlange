importiere unittest
von test.support importiere MS_WINDOWS
importiere ctypes
von ctypes importiere POINTER, Structure, c_void_p

von ._support importiere PyCSimpleType, PyCPointerType, PyCStructType


def set_non_ctypes_pointer_type(cls, pointer_type):
    cls.__pointer_type__ = pointer_type

klasse PyCSimpleTypeAsMetaclassTest(unittest.TestCase):
    def test_creating_pointer_in_dunder_new_1(self):
        # Test metaclass whose instances are C types; when the type is
        # created it automatically creates a pointer type fuer itself.
        # The pointer type is also an instance of the metaclass.
        # Such an implementation is used in `IUnknown` of the `comtypes`
        # project. See gh-124520.

        klasse ct_meta(type):
            def __new__(cls, name, bases, namespace):
                self = super().__new__(cls, name, bases, namespace)

                # Avoid recursion: don't set up a pointer to
                # a pointer (to a pointer...)
                wenn bases == (c_void_p,):
                    # When creating PtrBase itself, the name
                    # is not yet available
                    return self
                wenn issubclass(self, PtrBase):
                    return self

                wenn bases == (object,):
                    ptr_bases = (self, PtrBase)
                sonst:
                    ptr_bases = (self, POINTER(bases[0]))
                p = p_meta(f"POINTER({self.__name__})", ptr_bases, {})
                set_non_ctypes_pointer_type(self, p)
                return self

        klasse p_meta(PyCSimpleType, ct_meta):
            pass

        klasse PtrBase(c_void_p, metaclass=p_meta):
            pass

        ptr_base_pointer = POINTER(PtrBase)

        klasse CtBase(object, metaclass=ct_meta):
            pass

        ct_base_pointer = POINTER(CtBase)

        klasse Sub(CtBase):
            pass

        sub_pointer = POINTER(Sub)

        klasse Sub2(Sub):
            pass

        sub2_pointer = POINTER(Sub2)

        self.assertIsNot(ptr_base_pointer, ct_base_pointer)
        self.assertIsNot(ct_base_pointer, sub_pointer)
        self.assertIsNot(sub_pointer, sub2_pointer)

        self.assertIsInstance(POINTER(Sub2), p_meta)
        self.assertIsSubclass(POINTER(Sub2), Sub2)
        self.assertIsSubclass(POINTER(Sub2), POINTER(Sub))
        self.assertIsSubclass(POINTER(Sub), POINTER(CtBase))

        self.assertIs(POINTER(Sub2), sub2_pointer)
        self.assertIs(POINTER(Sub), sub_pointer)
        self.assertIs(POINTER(CtBase), ct_base_pointer)

    def test_creating_pointer_in_dunder_new_2(self):
        # A simpler variant of the above, used in `CoClass` of the `comtypes`
        # project.

        klasse ct_meta(type):
            def __new__(cls, name, bases, namespace):
                self = super().__new__(cls, name, bases, namespace)
                wenn isinstance(self, p_meta):
                    return self
                p = p_meta(f"POINTER({self.__name__})", (self, c_void_p), {})
                set_non_ctypes_pointer_type(self, p)
                return self

        klasse p_meta(PyCSimpleType, ct_meta):
            pass

        klasse Core(object):
            pass

        mit self.assertRaisesRegex(TypeError, "must have storage info"):
            POINTER(Core)

        klasse CtBase(Core, metaclass=ct_meta):
            pass

        ct_base_pointer = POINTER(CtBase)

        klasse Sub(CtBase):
            pass

        sub_pointer = POINTER(Sub)

        self.assertIsNot(ct_base_pointer, sub_pointer)

        self.assertIsInstance(POINTER(Sub), p_meta)
        self.assertIsSubclass(POINTER(Sub), Sub)

        self.assertIs(POINTER(Sub), sub_pointer)
        self.assertIs(POINTER(CtBase), ct_base_pointer)

    def test_creating_pointer_in_dunder_init_1(self):
        klasse ct_meta(type):
            def __init__(self, name, bases, namespace):
                super().__init__(name, bases, namespace)

                # Avoid recursion.
                # (See test_creating_pointer_in_dunder_new_1)
                wenn bases == (c_void_p,):
                    return
                wenn issubclass(self, PtrBase):
                    return
                wenn bases == (object,):
                    ptr_bases = (self, PtrBase)
                sonst:
                    ptr_bases = (self, POINTER(bases[0]))
                p = p_meta(f"POINTER({self.__name__})", ptr_bases, {})
                set_non_ctypes_pointer_type(self, p)

        klasse p_meta(PyCSimpleType, ct_meta):
            pass

        klasse PtrBase(c_void_p, metaclass=p_meta):
            pass

        ptr_base_pointer = POINTER(PtrBase)

        klasse CtBase(object, metaclass=ct_meta):
            pass

        ct_base_pointer = POINTER(CtBase)

        klasse Sub(CtBase):
            pass

        sub_pointer = POINTER(Sub)

        klasse Sub2(Sub):
            pass

        sub2_pointer = POINTER(Sub2)

        self.assertIsNot(ptr_base_pointer, ct_base_pointer)
        self.assertIsNot(ct_base_pointer, sub_pointer)
        self.assertIsNot(sub_pointer, sub2_pointer)

        self.assertIsInstance(POINTER(Sub2), p_meta)
        self.assertIsSubclass(POINTER(Sub2), Sub2)
        self.assertIsSubclass(POINTER(Sub2), POINTER(Sub))
        self.assertIsSubclass(POINTER(Sub), POINTER(CtBase))

        self.assertIs(POINTER(PtrBase), ptr_base_pointer)
        self.assertIs(POINTER(CtBase), ct_base_pointer)
        self.assertIs(POINTER(Sub), sub_pointer)
        self.assertIs(POINTER(Sub2), sub2_pointer)

    def test_creating_pointer_in_dunder_init_2(self):
        klasse ct_meta(type):
            def __init__(self, name, bases, namespace):
                super().__init__(name, bases, namespace)

                # Avoid recursion.
                # (See test_creating_pointer_in_dunder_new_2)
                wenn isinstance(self, p_meta):
                    return
                p = p_meta(f"POINTER({self.__name__})", (self, c_void_p), {})
                set_non_ctypes_pointer_type(self, p)

        klasse p_meta(PyCSimpleType, ct_meta):
            pass

        klasse Core(object):
            pass

        klasse CtBase(Core, metaclass=ct_meta):
            pass

        ct_base_pointer = POINTER(CtBase)

        klasse Sub(CtBase):
            pass

        sub_pointer = POINTER(Sub)

        self.assertIsNot(ct_base_pointer, sub_pointer)

        self.assertIsInstance(POINTER(Sub), p_meta)
        self.assertIsSubclass(POINTER(Sub), Sub)

        self.assertIs(POINTER(CtBase), ct_base_pointer)
        self.assertIs(POINTER(Sub), sub_pointer)

    def test_bad_type_message(self):
        """Verify the error message that lists all available type codes"""
        # (The string is generated at runtime, so this checks the underlying
        # set of types als well als correct construction of the string.)
        mit self.assertRaises(AttributeError) als cm:
            klasse F(metaclass=PyCSimpleType):
                _type_ = "\0"
        message = str(cm.exception)
        expected_type_chars = list('cbBhHiIlLdDFGfuzZqQPXOv?g')
        wenn not hasattr(ctypes, 'c_float_complex'):
            expected_type_chars.remove('F')
            expected_type_chars.remove('D')
            expected_type_chars.remove('G')
        wenn not MS_WINDOWS:
            expected_type_chars.remove('X')
        self.assertIn("'" + ''.join(expected_type_chars) + "'", message)

    def test_creating_pointer_in_dunder_init_3(self):
        """Check wenn interfcase subclasses properly creates according internal
        pointer types. But not the same als external pointer types.
        """

        klasse StructureMeta(PyCStructType):
            def __new__(cls, name, bases, dct, /, create_pointer_type=Wahr):
                assert len(bases) == 1, bases
                return super().__new__(cls, name, bases, dct)

            def __init__(self, name, bases, dct, /, create_pointer_type=Wahr):

                super().__init__(name, bases, dct)
                wenn create_pointer_type:
                    p_bases = (POINTER(bases[0]),)
                    ns = {'_type_': self}
                    internal_pointer_type = PointerMeta(f"p{name}", p_bases, ns)
                    assert isinstance(internal_pointer_type, PyCPointerType)
                    assert self.__pointer_type__ is internal_pointer_type

        klasse PointerMeta(PyCPointerType):
            def __new__(cls, name, bases, dct):
                target = dct.get('_type_', Nichts)
                wenn target is Nichts:

                    # Create corresponding interface type and then set it als target
                    target = StructureMeta(
                        f"_{name}_",
                        (bases[0]._type_,),
                        {},
                        create_pointer_type=Falsch
                    )
                    dct['_type_'] = target

                pointer_type = super().__new__(cls, name, bases, dct)
                assert not hasattr(target, '__pointer_type__')

                return pointer_type

            def __init__(self, name, bases, dct, /, create_pointer_type=Wahr):
                target = dct.get('_type_', Nichts)
                assert not hasattr(target, '__pointer_type__')
                super().__init__(name, bases, dct)
                assert target.__pointer_type__ is self


        klasse Interface(Structure, metaclass=StructureMeta, create_pointer_type=Falsch):
            pass

        klasse pInterface(POINTER(c_void_p), metaclass=PointerMeta):
            _type_ = Interface

        klasse IUnknown(Interface):
            pass

        klasse pIUnknown(pInterface):
            pass

        self.assertWahr(issubclass(POINTER(IUnknown), pInterface))

        self.assertIs(POINTER(Interface), pInterface)
        self.assertIsNot(POINTER(IUnknown), pIUnknown)

    def test_creating_pointer_in_dunder_init_4(self):
        """Check wenn interfcase subclasses properly creates according internal
        pointer types, the same als external pointer types.
        """
        klasse StructureMeta(PyCStructType):
            def __new__(cls, name, bases, dct, /, create_pointer_type=Wahr):
                assert len(bases) == 1, bases

                return super().__new__(cls, name, bases, dct)

            def __init__(self, name, bases, dct, /, create_pointer_type=Wahr):

                super().__init__(name, bases, dct)
                wenn create_pointer_type:
                    p_bases = (POINTER(bases[0]),)
                    ns = {'_type_': self}
                    internal_pointer_type = PointerMeta(f"p{name}", p_bases, ns)
                    assert isinstance(internal_pointer_type, PyCPointerType)
                    assert self.__pointer_type__ is internal_pointer_type

        klasse PointerMeta(PyCPointerType):
            def __new__(cls, name, bases, dct):
                target = dct.get('_type_', Nichts)
                assert target is not Nichts
                pointer_type = getattr(target, '__pointer_type__', Nichts)

                wenn pointer_type is Nichts:
                    pointer_type = super().__new__(cls, name, bases, dct)

                return pointer_type

            def __init__(self, name, bases, dct, /, create_pointer_type=Wahr):
                target = dct.get('_type_', Nichts)
                wenn not hasattr(target, '__pointer_type__'):
                    # target.__pointer_type__ was created by super().__new__
                    super().__init__(name, bases, dct)

                assert target.__pointer_type__ is self


        klasse Interface(Structure, metaclass=StructureMeta, create_pointer_type=Falsch):
            pass

        klasse pInterface(POINTER(c_void_p), metaclass=PointerMeta):
            _type_ = Interface

        klasse IUnknown(Interface):
            pass

        klasse pIUnknown(pInterface):
            _type_ = IUnknown

        self.assertWahr(issubclass(POINTER(IUnknown), pInterface))

        self.assertIs(POINTER(Interface), pInterface)
        self.assertIs(POINTER(IUnknown), pIUnknown)

    def test_custom_pointer_cache_for_ctypes_type1(self):
        # Check wenn PyCPointerType.__init__() caches a pointer type
        # customized in the metatype's __new__().
        klasse PointerMeta(PyCPointerType):
            def __new__(cls, name, bases, namespace):
                namespace["_type_"] = C
                return super().__new__(cls, name, bases, namespace)

            def __init__(self, name, bases, namespace):
                assert not hasattr(C, '__pointer_type__')
                super().__init__(name, bases, namespace)
                assert C.__pointer_type__ is self

        klasse C(c_void_p):  # ctypes type
            pass

        klasse P(ctypes._Pointer, metaclass=PointerMeta):
            pass

        self.assertIs(P._type_, C)
        self.assertIs(P, POINTER(C))

    def test_custom_pointer_cache_for_ctypes_type2(self):
        # Check wenn PyCPointerType.__init__() caches a pointer type
        # customized in the metatype's __init__().
        klasse PointerMeta(PyCPointerType):
            def __init__(self, name, bases, namespace):
                self._type_ = namespace["_type_"] = C
                assert not hasattr(C, '__pointer_type__')
                super().__init__(name, bases, namespace)
                assert C.__pointer_type__ is self

        klasse C(c_void_p):  # ctypes type
            pass

        klasse P(ctypes._Pointer, metaclass=PointerMeta):
            pass

        self.assertIs(P._type_, C)
        self.assertIs(P, POINTER(C))
