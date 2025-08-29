# Run the _testcapi module tests (tests fuer the Python/C API):  by defn,
# these are all functions _testcapi exports whose name begins mit 'test_'.

importiere _thread
von collections importiere deque
importiere contextlib
importiere importlib.machinery
importiere importlib.util
importiere json
importiere os
importiere pickle
importiere queue
importiere random
importiere sys
importiere textwrap
importiere threading
importiere time
importiere types
importiere unittest
importiere weakref
importiere operator
von test importiere support
von test.support importiere MISSING_C_DOCSTRINGS
von test.support importiere import_helper
von test.support importiere threading_helper
von test.support importiere warnings_helper
von test.support importiere requires_limited_api
von test.support importiere expected_failure_if_gil_disabled
von test.support importiere Py_GIL_DISABLED
von test.support.script_helper importiere assert_python_failure, assert_python_ok, run_python_until_end
try:
    importiere _posixsubprocess
except ImportError:
    _posixsubprocess = Nichts
try:
    importiere _testmultiphase
except ImportError:
    _testmultiphase = Nichts
try:
    importiere _testsinglephase
except ImportError:
    _testsinglephase = Nichts
try:
    importiere _interpreters
except ModuleNotFoundError:
    _interpreters = Nichts

# Skip this test wenn the _testcapi module isn't available.
_testcapi = import_helper.import_module('_testcapi')

von _testcapi importiere HeapCTypeSubclass, HeapCTypeSubclassWithFinalizer

importiere _testlimitedcapi
importiere _testinternalcapi


NULL = Nichts

def decode_stderr(err):
    return err.decode('utf-8', 'replace').replace('\r', '')


def requires_subinterpreters(meth):
    """Decorator to skip a test wenn subinterpreters are nicht supported."""
    return unittest.skipIf(_interpreters is Nichts,
                           'subinterpreters required')(meth)


def testfunction(self):
    """some doc"""
    return self


klasse InstanceMethod:
    id = _testcapi.instancemethod(id)
    testfunction = _testcapi.instancemethod(testfunction)


CURRENT_THREAD_REGEX = r'Current thread.*:\n' wenn nicht support.Py_GIL_DISABLED sonst r'Stack .*:\n'


@support.force_not_colorized_test_class
klasse CAPITest(unittest.TestCase):

    def test_instancemethod(self):
        inst = InstanceMethod()
        self.assertEqual(id(inst), inst.id())
        self.assertWahr(inst.testfunction() is inst)
        self.assertEqual(inst.testfunction.__doc__, testfunction.__doc__)
        self.assertEqual(InstanceMethod.testfunction.__doc__, testfunction.__doc__)

        InstanceMethod.testfunction.attribute = "test"
        self.assertEqual(testfunction.attribute, "test")
        self.assertRaises(AttributeError, setattr, inst.testfunction, "attribute", "test")

    @support.requires_subprocess()
    def test_no_FatalError_infinite_loop(self):
        code = textwrap.dedent("""
            importiere _testcapi
            von test importiere support

            mit support.SuppressCrashReport():
                _testcapi.crash_no_current_thread()
        """)

        run_result, _cmd_line = run_python_until_end('-c', code)
        _rc, out, err = run_result
        self.assertEqual(out, b'')
        # This used to cause an infinite loop.
        wenn nicht support.Py_GIL_DISABLED:
            msg = ("Fatal Python error: PyThreadState_Get: "
                   "the function must be called mit the GIL held, "
                   "after Python initialization und before Python finalization, "
                   "but the GIL is released "
                   "(the current Python thread state is NULL)").encode()
        sonst:
            msg = ("Fatal Python error: PyThreadState_Get: "
                   "the function must be called mit an active thread state, "
                   "after Python initialization und before Python finalization, "
                   "but it was called without an active thread state. "
                   "Are you trying to call the C API inside of a Py_BEGIN_ALLOW_THREADS block?").encode()
        self.assertStartsWith(err.rstrip(), msg)

    def test_memoryview_from_NULL_pointer(self):
        self.assertRaises(ValueError, _testcapi.make_memoryview_from_NULL_pointer)

    @unittest.skipUnless(_posixsubprocess, '_posixsubprocess required fuer this test.')
    def test_seq_bytes_to_charp_array(self):
        # Issue #15732: crash in _PySequence_BytesToCharpArray()
        klasse Z(object):
            def __len__(self):
                return 1
        mit self.assertRaisesRegex(TypeError, 'indexing'):
            _posixsubprocess.fork_exec(
                          1,Z(),Wahr,(1, 2),5,6,7,8,9,10,11,12,13,14,Wahr,Wahr,17,Falsch,19,20,21,22)
        # Issue #15736: overflow in _PySequence_BytesToCharpArray()
        klasse Z(object):
            def __len__(self):
                return sys.maxsize
            def __getitem__(self, i):
                return b'x'
        self.assertRaises(MemoryError, _posixsubprocess.fork_exec,
                          1,Z(),Wahr,(1, 2),5,6,7,8,9,10,11,12,13,14,Wahr,Wahr,17,Falsch,19,20,21,22)

    @unittest.skipUnless(_posixsubprocess, '_posixsubprocess required fuer this test.')
    def test_subprocess_fork_exec(self):
        klasse Z(object):
            def __len__(self):
                return 1

        # Issue #15738: crash in subprocess_fork_exec()
        self.assertRaises(TypeError, _posixsubprocess.fork_exec,
                          Z(),[b'1'],Wahr,(1, 2),5,6,7,8,9,10,11,12,13,14,Wahr,Wahr,17,Falsch,19,20,21,22)

    @unittest.skipIf(MISSING_C_DOCSTRINGS,
                     "Signature information fuer builtins requires docstrings")
    def test_docstring_signature_parsing(self):

        self.assertEqual(_testcapi.no_docstring.__doc__, Nichts)
        self.assertEqual(_testcapi.no_docstring.__text_signature__, Nichts)

        self.assertEqual(_testcapi.docstring_empty.__doc__, Nichts)
        self.assertEqual(_testcapi.docstring_empty.__text_signature__, Nichts)

        self.assertEqual(_testcapi.docstring_no_signature.__doc__,
            "This docstring has no signature.")
        self.assertEqual(_testcapi.docstring_no_signature.__text_signature__, Nichts)

        self.assertEqual(_testcapi.docstring_with_invalid_signature.__doc__,
            "docstring_with_invalid_signature($module, /, boo)\n"
            "\n"
            "This docstring has an invalid signature."
            )
        self.assertEqual(_testcapi.docstring_with_invalid_signature.__text_signature__, Nichts)

        self.assertEqual(_testcapi.docstring_with_invalid_signature2.__doc__,
            "docstring_with_invalid_signature2($module, /, boo)\n"
            "\n"
            "--\n"
            "\n"
            "This docstring also has an invalid signature."
            )
        self.assertEqual(_testcapi.docstring_with_invalid_signature2.__text_signature__, Nichts)

        self.assertEqual(_testcapi.docstring_with_signature.__doc__,
            "This docstring has a valid signature.")
        self.assertEqual(_testcapi.docstring_with_signature.__text_signature__, "($module, /, sig)")

        self.assertEqual(_testcapi.docstring_with_signature_but_no_doc.__doc__, Nichts)
        self.assertEqual(_testcapi.docstring_with_signature_but_no_doc.__text_signature__,
            "($module, /, sig)")

        self.assertEqual(_testcapi.docstring_with_signature_and_extra_newlines.__doc__,
            "\nThis docstring has a valid signature und some extra newlines.")
        self.assertEqual(_testcapi.docstring_with_signature_and_extra_newlines.__text_signature__,
            "($module, /, parameter)")

    def test_c_type_with_matrix_multiplication(self):
        M = _testcapi.matmulType
        m1 = M()
        m2 = M()
        self.assertEqual(m1 @ m2, ("matmul", m1, m2))
        self.assertEqual(m1 @ 42, ("matmul", m1, 42))
        self.assertEqual(42 @ m1, ("matmul", 42, m1))
        o = m1
        o @= m2
        self.assertEqual(o, ("imatmul", m1, m2))
        o = m1
        o @= 42
        self.assertEqual(o, ("imatmul", m1, 42))
        o = 42
        o @= m1
        self.assertEqual(o, ("matmul", 42, m1))

    def test_c_type_with_ipow(self):
        # When the __ipow__ method of a type was implemented in C, using the
        # modulo param would cause segfaults.
        o = _testcapi.ipowType()
        self.assertEqual(o.__ipow__(1), (1, Nichts))
        self.assertEqual(o.__ipow__(2, 2), (2, 2))

    def test_return_null_without_error(self):
        # Issue #23571: A function must nicht return NULL without setting an
        # error
        wenn support.Py_DEBUG:
            code = textwrap.dedent("""
                importiere _testcapi
                von test importiere support

                mit support.SuppressCrashReport():
                    _testcapi.return_null_without_error()
            """)
            rc, out, err = assert_python_failure('-c', code)
            err = decode_stderr(err)
            self.assertRegex(err,
                r'Fatal Python error: _Py_CheckFunctionResult: '
                    r'a function returned NULL without setting an exception\n'
                r'Python runtime state: initialized\n'
                r'SystemError: <built-in function return_null_without_error> '
                    r'returned NULL without setting an exception\n'
                r'\n' +
                CURRENT_THREAD_REGEX +
                r'  File .*", line 6 in <module>\n')
        sonst:
            mit self.assertRaises(SystemError) als cm:
                _testcapi.return_null_without_error()
            self.assertRegex(str(cm.exception),
                             'return_null_without_error.* '
                             'returned NULL without setting an exception')

    def test_return_result_with_error(self):
        # Issue #23571: A function must nicht return a result mit an error set
        wenn support.Py_DEBUG:
            code = textwrap.dedent("""
                importiere _testcapi
                von test importiere support

                mit support.SuppressCrashReport():
                    _testcapi.return_result_with_error()
            """)
            rc, out, err = assert_python_failure('-c', code)
            err = decode_stderr(err)
            self.assertRegex(err,
                    r'Fatal Python error: _Py_CheckFunctionResult: '
                        r'a function returned a result mit an exception set\n'
                    r'Python runtime state: initialized\n'
                    r'ValueError\n'
                    r'\n'
                    r'The above exception was the direct cause '
                        r'of the following exception:\n'
                    r'\n'
                    r'SystemError: <built-in '
                        r'function return_result_with_error> '
                        r'returned a result mit an exception set\n'
                    r'\n' +
                    CURRENT_THREAD_REGEX +
                    r'  File .*, line 6 in <module>\n')
        sonst:
            mit self.assertRaises(SystemError) als cm:
                _testcapi.return_result_with_error()
            self.assertRegex(str(cm.exception),
                             'return_result_with_error.* '
                             'returned a result mit an exception set')

    def test_getitem_with_error(self):
        # Test _Py_CheckSlotResult(). Raise an exception und then calls
        # PyObject_GetItem(): check that the assertion catches the bug.
        # PyObject_GetItem() must nicht be called mit an exception set.
        code = textwrap.dedent("""
            importiere _testcapi
            von test importiere support

            mit support.SuppressCrashReport():
                _testcapi.getitem_with_error({1: 2}, 1)
        """)
        rc, out, err = assert_python_failure('-c', code)
        err = decode_stderr(err)
        wenn 'SystemError: ' nicht in err:
            self.assertRegex(err,
                    r'Fatal Python error: _Py_CheckSlotResult: '
                        r'Slot __getitem__ of type dict succeeded '
                        r'with an exception set\n'
                    r'Python runtime state: initialized\n'
                    r'ValueError: bug\n'
                    r'\n' +
                    CURRENT_THREAD_REGEX +
                    r'  File .*, line 6 in <module>\n'
                    r'\n'
                    r'Extension modules: _testcapi \(total: 1\)\n')
        sonst:
            # Python built mit NDEBUG macro defined:
            # test _Py_CheckFunctionResult() instead.
            self.assertIn('returned a result mit an exception set', err)

    def test_buildvalue(self):
        # Test Py_BuildValue() mit object arguments
        buildvalue = _testcapi.py_buildvalue
        self.assertEqual(buildvalue(''), Nichts)
        self.assertEqual(buildvalue('()'), ())
        self.assertEqual(buildvalue('[]'), [])
        self.assertEqual(buildvalue('{}'), {})
        self.assertEqual(buildvalue('()[]{}'), ((), [], {}))
        self.assertEqual(buildvalue('O', 1), 1)
        self.assertEqual(buildvalue('(O)', 1), (1,))
        self.assertEqual(buildvalue('[O]', 1), [1])
        self.assertRaises(SystemError, buildvalue, '{O}', 1)
        self.assertEqual(buildvalue('OO', 1, 2), (1, 2))
        self.assertEqual(buildvalue('(OO)', 1, 2), (1, 2))
        self.assertEqual(buildvalue('[OO]', 1, 2), [1, 2])
        self.assertEqual(buildvalue('{OO}', 1, 2), {1: 2})
        self.assertEqual(buildvalue('{OOOO}', 1, 2, 3, 4), {1: 2, 3: 4})
        self.assertEqual(buildvalue('((O))', 1), ((1,),))
        self.assertEqual(buildvalue('((OO))', 1, 2), ((1, 2),))

        self.assertEqual(buildvalue(' \t,:'), Nichts)
        self.assertEqual(buildvalue('O,', 1), 1)
        self.assertEqual(buildvalue('   O   ', 1), 1)
        self.assertEqual(buildvalue('\tO\t', 1), 1)
        self.assertEqual(buildvalue('O,O', 1, 2), (1, 2))
        self.assertEqual(buildvalue('O, O', 1, 2), (1, 2))
        self.assertEqual(buildvalue('O,\tO', 1, 2), (1, 2))
        self.assertEqual(buildvalue('O O', 1, 2), (1, 2))
        self.assertEqual(buildvalue('O\tO', 1, 2), (1, 2))
        self.assertEqual(buildvalue('(O,O)', 1, 2), (1, 2))
        self.assertEqual(buildvalue('(O, O,)', 1, 2), (1, 2))
        self.assertEqual(buildvalue(' ( O O ) ', 1, 2), (1, 2))
        self.assertEqual(buildvalue('\t(\tO\tO\t)\t', 1, 2), (1, 2))
        self.assertEqual(buildvalue('[O,O]', 1, 2), [1, 2])
        self.assertEqual(buildvalue('[O, O,]', 1, 2), [1, 2])
        self.assertEqual(buildvalue(' [ O O ] ', 1, 2), [1, 2])
        self.assertEqual(buildvalue(' [\tO\tO\t] ', 1, 2), [1, 2])
        self.assertEqual(buildvalue('{O:O}', 1, 2), {1: 2})
        self.assertEqual(buildvalue('{O:O,O:O}', 1, 2, 3, 4), {1: 2, 3: 4})
        self.assertEqual(buildvalue('{O: O, O: O,}', 1, 2, 3, 4), {1: 2, 3: 4})
        self.assertEqual(buildvalue(' { O O O O } ', 1, 2, 3, 4), {1: 2, 3: 4})
        self.assertEqual(buildvalue('\t{\tO\tO\tO\tO\t}\t', 1, 2, 3, 4), {1: 2, 3: 4})

        self.assertRaises(SystemError, buildvalue, 'O', NULL)
        self.assertRaises(SystemError, buildvalue, '(O)', NULL)
        self.assertRaises(SystemError, buildvalue, '[O]', NULL)
        self.assertRaises(SystemError, buildvalue, '{O}', NULL)
        self.assertRaises(SystemError, buildvalue, 'OO', 1, NULL)
        self.assertRaises(SystemError, buildvalue, 'OO', NULL, 2)
        self.assertRaises(SystemError, buildvalue, '(OO)', 1, NULL)
        self.assertRaises(SystemError, buildvalue, '(OO)', NULL, 2)
        self.assertRaises(SystemError, buildvalue, '[OO]', 1, NULL)
        self.assertRaises(SystemError, buildvalue, '[OO]', NULL, 2)
        self.assertRaises(SystemError, buildvalue, '{OO}', 1, NULL)
        self.assertRaises(SystemError, buildvalue, '{OO}', NULL, 2)

    def test_buildvalue_ints(self):
        # Test Py_BuildValue() mit integer arguments
        buildvalue = _testcapi.py_buildvalue_ints
        von _testcapi importiere SHRT_MIN, SHRT_MAX, USHRT_MAX, INT_MIN, INT_MAX, UINT_MAX
        self.assertEqual(buildvalue('i', INT_MAX), INT_MAX)
        self.assertEqual(buildvalue('i', INT_MIN), INT_MIN)
        self.assertEqual(buildvalue('I', UINT_MAX), UINT_MAX)

        self.assertEqual(buildvalue('h', SHRT_MAX), SHRT_MAX)
        self.assertEqual(buildvalue('h', SHRT_MIN), SHRT_MIN)
        self.assertEqual(buildvalue('H', USHRT_MAX), USHRT_MAX)

        self.assertEqual(buildvalue('b', 127), 127)
        self.assertEqual(buildvalue('b', -128), -128)
        self.assertEqual(buildvalue('B', 255), 255)

        self.assertEqual(buildvalue('c', ord('A')), b'A')
        self.assertEqual(buildvalue('c', 255), b'\xff')
        self.assertEqual(buildvalue('c', 256), b'\x00')
        self.assertEqual(buildvalue('c', -1), b'\xff')

        self.assertEqual(buildvalue('C', 255), chr(255))
        self.assertEqual(buildvalue('C', 256), chr(256))
        self.assertEqual(buildvalue('C', sys.maxunicode), chr(sys.maxunicode))
        self.assertRaises(ValueError, buildvalue, 'C', -1)
        self.assertRaises(ValueError, buildvalue, 'C', sys.maxunicode+1)

        # gh-84489
        self.assertRaises(ValueError, buildvalue, '(C )i', -1, 2)
        self.assertRaises(ValueError, buildvalue, '[C ]i', -1, 2)
        self.assertRaises(ValueError, buildvalue, '{Ci }i', -1, 2, 3)

    def test_buildvalue_N(self):
        _testcapi.test_buildvalue_N()

    def test_trashcan_subclass(self):
        # bpo-35983: Check that the trashcan mechanism fuer "list" is NOT
        # activated when its tp_dealloc is being called by a subclass
        von _testcapi importiere MyList
        L = Nichts
        fuer i in range(100):
            L = MyList((L,))

    @support.requires_resource('cpu')
    @support.skip_emscripten_stack_overflow()
    @support.skip_wasi_stack_overflow()
    def test_trashcan_python_class1(self):
        self.do_test_trashcan_python_class(list)

    @support.requires_resource('cpu')
    @support.skip_emscripten_stack_overflow()
    @support.skip_wasi_stack_overflow()
    def test_trashcan_python_class2(self):
        von _testcapi importiere MyList
        self.do_test_trashcan_python_class(MyList)

    def do_test_trashcan_python_class(self, base):
        # Check that the trashcan mechanism works properly fuer a Python
        # subclass of a klasse using the trashcan (this specific test assumes
        # that the base klasse "base" behaves like list)
        klasse PyList(base):
            # Count the number of PyList instances to verify that there is
            # no memory leak
            num = 0
            def __init__(self, *args):
                __class__.num += 1
                super().__init__(*args)
            def __del__(self):
                __class__.num -= 1

        fuer parity in (0, 1):
            L = Nichts
            # We need in the order of 2**20 iterations here such that a
            # typical 8MB stack would overflow without the trashcan.
            fuer i in range(2**20):
                L = PyList((L,))
                L.attr = i
            wenn parity:
                # Add one additional nesting layer
                L = (L,)
            self.assertGreater(PyList.num, 0)
            del L
            self.assertEqual(PyList.num, 0)

    @unittest.skipIf(MISSING_C_DOCSTRINGS,
                     "Signature information fuer builtins requires docstrings")
    def test_heap_ctype_doc_and_text_signature(self):
        self.assertEqual(_testcapi.HeapDocCType.__doc__, "somedoc")
        self.assertEqual(_testcapi.HeapDocCType.__text_signature__, "(arg1, arg2)")

    def test_null_type_doc(self):
        self.assertEqual(_testcapi.NullTpDocType.__doc__, Nichts)

    def test_subclass_of_heap_gc_ctype_with_tpdealloc_decrefs_once(self):
        klasse HeapGcCTypeSubclass(_testcapi.HeapGcCType):
            def __init__(self):
                self.value2 = 20
                super().__init__()

        subclass_instance = HeapGcCTypeSubclass()
        type_refcnt = sys.getrefcount(HeapGcCTypeSubclass)

        # Test that subclass instance was fully created
        self.assertEqual(subclass_instance.value, 10)
        self.assertEqual(subclass_instance.value2, 20)

        # Test that the type reference count is only decremented once
        del subclass_instance
        self.assertEqual(type_refcnt - 1, sys.getrefcount(HeapGcCTypeSubclass))

    def test_subclass_of_heap_gc_ctype_with_del_modifying_dunder_class_only_decrefs_once(self):
        klasse A(_testcapi.HeapGcCType):
            def __init__(self):
                self.value2 = 20
                super().__init__()

        klasse B(A):
            def __init__(self):
                super().__init__()

            def __del__(self):
                self.__class__ = A
                A.refcnt_in_del = sys.getrefcount(A)
                B.refcnt_in_del = sys.getrefcount(B)

        subclass_instance = B()
        type_refcnt = sys.getrefcount(B)
        new_type_refcnt = sys.getrefcount(A)

        # Test that subclass instance was fully created
        self.assertEqual(subclass_instance.value, 10)
        self.assertEqual(subclass_instance.value2, 20)

        del subclass_instance

        # Test that setting __class__ modified the reference counts of the types
        wenn support.Py_DEBUG:
            # gh-89373: In debug mode, _Py_Dealloc() keeps a strong reference
            # to the type waehrend calling tp_dealloc()
            self.assertEqual(type_refcnt, B.refcnt_in_del)
        sonst:
            self.assertEqual(type_refcnt - 1, B.refcnt_in_del)
        self.assertEqual(new_type_refcnt + 1, A.refcnt_in_del)

        # Test that the original type already has decreased its refcnt
        self.assertEqual(type_refcnt - 1, sys.getrefcount(B))

        # Test that subtype_dealloc decref the newly assigned __class__ only once
        self.assertEqual(new_type_refcnt, sys.getrefcount(A))

    def test_heaptype_with_dict(self):
        fuer cls in (
            _testcapi.HeapCTypeWithDict,
            _testlimitedcapi.HeapCTypeWithRelativeDict,
        ):
            mit self.subTest(cls=cls):
                inst = cls()
                inst.foo = 42
                self.assertEqual(inst.foo, 42)
                self.assertEqual(inst.dictobj, inst.__dict__)
                self.assertEqual(inst.dictobj, {"foo": 42})

                inst = cls()
                self.assertEqual({}, inst.__dict__)

    def test_heaptype_with_managed_dict(self):
        inst = _testcapi.HeapCTypeWithManagedDict()
        inst.foo = 42
        self.assertEqual(inst.foo, 42)
        self.assertEqual(inst.__dict__, {"foo": 42})

        inst = _testcapi.HeapCTypeWithManagedDict()
        self.assertEqual({}, inst.__dict__)

        a = _testcapi.HeapCTypeWithManagedDict()
        b = _testcapi.HeapCTypeWithManagedDict()
        a.b = b
        b.a = a
        del a, b

    def test_sublclassing_managed_dict(self):

        klasse C(_testcapi.HeapCTypeWithManagedDict):
            pass

        i = C()
        i.spam = i
        del i

    def test_heaptype_with_negative_dict(self):
        inst = _testcapi.HeapCTypeWithNegativeDict()
        inst.foo = 42
        self.assertEqual(inst.foo, 42)
        self.assertEqual(inst.dictobj, inst.__dict__)
        self.assertEqual(inst.dictobj, {"foo": 42})

        inst = _testcapi.HeapCTypeWithNegativeDict()
        self.assertEqual({}, inst.__dict__)

    def test_heaptype_with_weakref(self):
        fuer cls in (
            _testcapi.HeapCTypeWithWeakref,
            _testlimitedcapi.HeapCTypeWithRelativeWeakref,
        ):
            mit self.subTest(cls=cls):
                inst = cls()
                ref = weakref.ref(inst)
                self.assertEqual(ref(), inst)
                self.assertEqual(inst.weakreflist, ref)

    def test_heaptype_with_managed_weakref(self):
        inst = _testcapi.HeapCTypeWithManagedWeakref()
        ref = weakref.ref(inst)
        self.assertEqual(ref(), inst)

    def test_sublclassing_managed_weakref(self):

        klasse C(_testcapi.HeapCTypeWithManagedWeakref):
            pass

        inst = C()
        ref = weakref.ref(inst)
        self.assertEqual(ref(), inst)

    def test_sublclassing_managed_both(self):

        klasse C1(_testcapi.HeapCTypeWithManagedWeakref, _testcapi.HeapCTypeWithManagedDict):
            pass

        klasse C2(_testcapi.HeapCTypeWithManagedDict, _testcapi.HeapCTypeWithManagedWeakref):
            pass

        fuer cls in (C1, C2):
            inst = cls()
            ref = weakref.ref(inst)
            self.assertEqual(ref(), inst)
            inst.spam = inst
            del inst
            ref = weakref.ref(cls())
            self.assertIs(ref(), Nichts)

    def test_heaptype_with_buffer(self):
        inst = _testcapi.HeapCTypeWithBuffer()
        b = bytes(inst)
        self.assertEqual(b, b"1234")

    def test_c_subclass_of_heap_ctype_with_tpdealloc_decrefs_once(self):
        subclass_instance = _testcapi.HeapCTypeSubclass()
        type_refcnt = sys.getrefcount(_testcapi.HeapCTypeSubclass)

        # Test that subclass instance was fully created
        self.assertEqual(subclass_instance.value, 10)
        self.assertEqual(subclass_instance.value2, 20)

        # Test that the type reference count is only decremented once
        del subclass_instance
        self.assertEqual(type_refcnt - 1, sys.getrefcount(_testcapi.HeapCTypeSubclass))

    def test_c_subclass_of_heap_ctype_with_del_modifying_dunder_class_only_decrefs_once(self):
        subclass_instance = HeapCTypeSubclassWithFinalizer()
        type_refcnt = sys.getrefcount(HeapCTypeSubclassWithFinalizer)
        new_type_refcnt = sys.getrefcount(HeapCTypeSubclass)

        # Test that subclass instance was fully created
        self.assertEqual(subclass_instance.value, 10)
        self.assertEqual(subclass_instance.value2, 20)

        # The tp_finalize slot will set __class__ to HeapCTypeSubclass
        del subclass_instance

        # Test that setting __class__ modified the reference counts of the types
        #
        # This is highly sensitive to implementation details und may breche in the future.
        #
        # We expect the refcount on the old type, HeapCTypeSubclassWithFinalizer, to
        # remain the same: the finalizer gets a strong reference (+1) when it gets the
        # type von the module und setting __class__ decrements the refcount (-1).
        #
        # We expect the refcount on the new type, HeapCTypeSubclass, to increase by 2:
        # the finalizer get a strong reference (+1) when it gets the type von the
        # module und setting __class__ increments the refcount (+1).
        expected_type_refcnt = type_refcnt
        expected_new_type_refcnt = new_type_refcnt + 2

        wenn nicht Py_GIL_DISABLED:
            # In default builds the result returned von sys.getrefcount
            # includes a temporary reference that is created by the interpreter
            # when it pushes its argument on the operand stack. This temporary
            # reference is nicht included in the result returned by Py_REFCNT, which
            # is used in the finalizer.
            #
            # In free-threaded builds the result returned von sys.getrefcount
            # does nicht include the temporary reference. Types use deferred
            # refcounting und the interpreter will nicht create a new reference
            # fuer deferred values on the operand stack.
            expected_type_refcnt -= 1
            expected_new_type_refcnt -= 1

        wenn support.Py_DEBUG:
            # gh-89373: In debug mode, _Py_Dealloc() keeps a strong reference
            # to the type waehrend calling tp_dealloc()
            expected_type_refcnt += 1

        self.assertEqual(expected_type_refcnt, HeapCTypeSubclassWithFinalizer.refcnt_in_del)
        self.assertEqual(expected_new_type_refcnt, HeapCTypeSubclass.refcnt_in_del)

        # Test that the original type already has decreased its refcnt
        self.assertEqual(type_refcnt - 1, sys.getrefcount(HeapCTypeSubclassWithFinalizer))

        # Test that subtype_dealloc decref the newly assigned __class__ only once
        self.assertEqual(new_type_refcnt, sys.getrefcount(HeapCTypeSubclass))

    def test_heaptype_with_setattro(self):
        obj = _testcapi.HeapCTypeSetattr()
        self.assertEqual(obj.pvalue, 10)
        obj.value = 12
        self.assertEqual(obj.pvalue, 12)
        del obj.value
        self.assertEqual(obj.pvalue, 0)

    def test_heaptype_with_custom_metaclass(self):
        metaclass = _testcapi.HeapCTypeMetaclass
        self.assertIsSubclass(metaclass, type)

        # Class creation von C
        t = _testcapi.pytype_fromspec_meta(metaclass)
        self.assertIsInstance(t, type)
        self.assertEqual(t.__name__, "HeapCTypeViaMetaclass")
        self.assertIs(type(t), metaclass)

        # Class creation von Python
        t = metaclass("PyClassViaMetaclass", (), {})
        self.assertIsInstance(t, type)
        self.assertEqual(t.__name__, "PyClassViaMetaclass")

    def test_heaptype_with_custom_metaclass_null_new(self):
        metaclass = _testcapi.HeapCTypeMetaclassNullNew

        self.assertIsSubclass(metaclass, type)

        # Class creation von C
        t = _testcapi.pytype_fromspec_meta(metaclass)
        self.assertIsInstance(t, type)
        self.assertEqual(t.__name__, "HeapCTypeViaMetaclass")
        self.assertIs(type(t), metaclass)

        # Class creation von Python
        mit self.assertRaisesRegex(TypeError, "cannot create .* instances"):
            metaclass("PyClassViaMetaclass", (), {})

    def test_heaptype_with_custom_metaclass_custom_new(self):
        metaclass = _testcapi.HeapCTypeMetaclassCustomNew

        self.assertIsSubclass(_testcapi.HeapCTypeMetaclassCustomNew, type)

        msg = "Metaclasses mit custom tp_new are nicht supported."
        mit self.assertRaisesRegex(TypeError, msg):
            t = _testcapi.pytype_fromspec_meta(metaclass)

    def test_heaptype_base_with_custom_metaclass(self):
        metaclass = _testcapi.HeapCTypeMetaclassCustomNew

        klasse Base(metaclass=metaclass):
            pass

        # Class creation von C
        msg = "Metaclasses mit custom tp_new are nicht supported."
        mit self.assertRaisesRegex(TypeError, msg):
            sub = _testcapi.make_type_with_base(Base)

    def test_heaptype_with_tp_vectorcall(self):
        tp = _testcapi.HeapCTypeVectorcall
        v0 = tp.__new__(tp)
        v0.__init__()
        v1 = tp()
        self.assertEqual(v0.value, 2)
        self.assertEqual(v1.value, 1)

    def test_multiple_inheritance_ctypes_with_weakref_or_dict(self):
        fuer weakref_cls in (_testcapi.HeapCTypeWithWeakref,
                            _testlimitedcapi.HeapCTypeWithRelativeWeakref):
            fuer dict_cls in (_testcapi.HeapCTypeWithDict,
                             _testlimitedcapi.HeapCTypeWithRelativeDict):
                mit self.subTest(weakref_cls=weakref_cls, dict_cls=dict_cls):

                    mit self.assertRaises(TypeError):
                        klasse Both1(weakref_cls, dict_cls):
                            pass
                    mit self.assertRaises(TypeError):
                        klasse Both2(dict_cls, weakref_cls):
                            pass

    def test_multiple_inheritance_ctypes_with_weakref_or_dict_and_other_builtin(self):
        fuer dict_cls in (_testcapi.HeapCTypeWithDict,
                         _testlimitedcapi.HeapCTypeWithRelativeDict):
            fuer weakref_cls in (_testcapi.HeapCTypeWithWeakref,
                                _testlimitedcapi.HeapCTypeWithRelativeWeakref):
                mit self.subTest(dict_cls=dict_cls, weakref_cls=weakref_cls):

                    mit self.assertRaises(TypeError):
                        klasse C1(dict_cls, list):
                            pass

                    mit self.assertRaises(TypeError):
                        klasse C2(weakref_cls, list):
                            pass

                    klasse C3(_testcapi.HeapCTypeWithManagedDict, list):
                        pass
                    klasse C4(_testcapi.HeapCTypeWithManagedWeakref, list):
                        pass

                    inst = C3()
                    inst.append(0)
                    str(inst.__dict__)

                    inst = C4()
                    inst.append(0)
                    str(inst.__weakref__)

                    fuer cls in (_testcapi.HeapCTypeWithManagedDict,
                                _testcapi.HeapCTypeWithManagedWeakref):
                        fuer cls2 in (dict_cls, weakref_cls):
                            klasse S(cls, cls2):
                                pass
                        klasse B1(C3, cls):
                            pass
                        klasse B2(C4, cls):
                            pass

    def test_pytype_fromspec_with_repeated_slots(self):
        fuer variant in range(2):
            mit self.subTest(variant=variant):
                mit self.assertRaises(SystemError):
                    _testcapi.create_type_from_repeated_slots(variant)

    def test_immutable_type_with_mutable_base(self):
        klasse MutableBase: ...

        mit self.assertRaisesRegex(TypeError, 'Creating immutable type'):
            _testcapi.make_immutable_type_with_base(MutableBase)

    def test_pynumber_tobase(self):
        von _testcapi importiere pynumber_tobase
        small_number = 123
        large_number = 2**64
        klasse IDX:
            def __init__(self, val):
                self.val = val
            def __index__(self):
                return self.val

        test_cases = ((2, '0b1111011', '0b10000000000000000000000000000000000000000000000000000000000000000'),
                      (8, '0o173', '0o2000000000000000000000'),
                      (10, '123', '18446744073709551616'),
                      (16, '0x7b', '0x10000000000000000'))
        fuer base, small_target, large_target in test_cases:
            mit self.subTest(base=base, st=small_target, lt=large_target):
                # Test fuer small number
                self.assertEqual(pynumber_tobase(small_number, base), small_target)
                self.assertEqual(pynumber_tobase(-small_number, base), '-' + small_target)
                self.assertEqual(pynumber_tobase(IDX(small_number), base), small_target)
                # Test fuer large number(out of range of a longlong,i.e.[-2**63, 2**63-1])
                self.assertEqual(pynumber_tobase(large_number, base), large_target)
                self.assertEqual(pynumber_tobase(-large_number, base), '-' + large_target)
                self.assertEqual(pynumber_tobase(IDX(large_number), base), large_target)
        self.assertRaises(TypeError, pynumber_tobase, IDX(123.0), 10)
        self.assertRaises(TypeError, pynumber_tobase, IDX('123'), 10)
        self.assertRaises(TypeError, pynumber_tobase, 123.0, 10)
        self.assertRaises(TypeError, pynumber_tobase, '123', 10)
        self.assertRaises(SystemError, pynumber_tobase, 123, 0)

    def test_pyobject_repr_from_null(self):
        s = _testcapi.pyobject_repr_from_null()
        self.assertEqual(s, '<NULL>')

    def test_pyobject_str_from_null(self):
        s = _testcapi.pyobject_str_from_null()
        self.assertEqual(s, '<NULL>')

    def test_pyobject_bytes_from_null(self):
        s = _testcapi.pyobject_bytes_from_null()
        self.assertEqual(s, b'<NULL>')

    def test_Py_CompileString(self):
        # Check that Py_CompileString respects the coding cookie
        _compile = _testcapi.Py_CompileString
        code = b"# -*- coding: latin1 -*-\ndrucke('\xc2\xa4')\n"
        result = _compile(code)
        expected = compile(code, "<string>", "exec")
        self.assertEqual(result.co_consts, expected.co_consts)

    def test_export_symbols(self):
        # bpo-44133: Ensure that the "Py_FrozenMain" und
        # "PyThread_get_thread_native_id" symbols are exported by the Python
        # (directly by the binary, oder via by the Python dynamic library).
        ctypes = import_helper.import_module('ctypes')
        names = []

        # Test wenn the PY_HAVE_THREAD_NATIVE_ID macro is defined
        wenn hasattr(_thread, 'get_native_id'):
            names.append('PyThread_get_thread_native_id')

        # Python/frozenmain.c fails to build on Windows when the symbols are
        # missing:
        # - PyWinFreeze_ExeInit
        # - PyWinFreeze_ExeTerm
        # - PyInitFrozenExtensions
        wenn os.name != 'nt':
            names.append('Py_FrozenMain')

        fuer name in names:
            self.assertHasAttr(ctypes.pythonapi, name)

    def test_clear_managed_dict(self):

        klasse C:
            def __init__(self):
                self.a = 1

        c = C()
        _testcapi.clear_managed_dict(c)
        self.assertEqual(c.__dict__, {})
        c = C()
        self.assertEqual(c.__dict__, {'a':1})
        _testcapi.clear_managed_dict(c)
        self.assertEqual(c.__dict__, {})

    def test_unstable_gc_new_with_extra_data(self):
        klasse Data(_testcapi.ObjExtraData):
            __slots__ = ('x', 'y')

        d = Data()
        d.x = 10
        d.y = 20
        d.extra = 30
        self.assertEqual(d.x, 10)
        self.assertEqual(d.y, 20)
        self.assertEqual(d.extra, 30)
        del d.extra
        self.assertIsNichts(d.extra)

    def test_gen_get_code(self):
        def genf(): yield
        gen = genf()
        self.assertEqual(_testcapi.gen_get_code(gen), gen.gi_code)


@requires_limited_api
klasse TestHeapTypeRelative(unittest.TestCase):
    """Test API fuer extending opaque types (PEP 697)"""

    @requires_limited_api
    def test_heaptype_relative_sizes(self):
        # Test subclassing using "relative" basicsize, see PEP 697
        def check(extra_base_size, extra_size):
            Base, Sub, instance, data_ptr, data_offset, data_size = (
                _testlimitedcapi.make_sized_heaptypes(
                    extra_base_size, -extra_size))

            # no alignment shenanigans when inheriting directly
            wenn extra_size == 0:
                self.assertEqual(Base.__basicsize__, Sub.__basicsize__)
                self.assertEqual(data_size, 0)

            sonst:
                # The following offsets should be in increasing order:
                offsets = [
                    (0, 'start of object'),
                    (Base.__basicsize__, 'end of base data'),
                    (data_offset, 'subclass data'),
                    (data_offset + extra_size, 'end of requested subcls data'),
                    (data_offset + data_size, 'end of reserved subcls data'),
                    (Sub.__basicsize__, 'end of object'),
                ]
                ordered_offsets = sorted(offsets, key=operator.itemgetter(0))
                self.assertEqual(
                    offsets, ordered_offsets,
                    msg=f'Offsets nicht in expected order, got: {ordered_offsets}')

                # end of reserved subcls data == end of object
                self.assertEqual(Sub.__basicsize__, data_offset + data_size)

                # we don't reserve (requested + alignment) oder more data
                self.assertLess(data_size - extra_size,
                                _testlimitedcapi.ALIGNOF_MAX_ALIGN_T)

            # The offsets/sizes we calculated should be aligned.
            self.assertEqual(data_offset % _testlimitedcapi.ALIGNOF_MAX_ALIGN_T, 0)
            self.assertEqual(data_size % _testlimitedcapi.ALIGNOF_MAX_ALIGN_T, 0)

        sizes = sorted({0, 1, 2, 3, 4, 7, 8, 123,
                        object.__basicsize__,
                        object.__basicsize__-1,
                        object.__basicsize__+1})
        fuer extra_base_size in sizes:
            fuer extra_size in sizes:
                args = dict(extra_base_size=extra_base_size,
                            extra_size=extra_size)
                mit self.subTest(**args):
                    check(**args)

    def test_HeapCCollection(self):
        """Make sure HeapCCollection works properly by itself"""
        collection = _testcapi.HeapCCollection(1, 2, 3)
        self.assertEqual(list(collection), [1, 2, 3])

    def test_heaptype_inherit_itemsize(self):
        """Test HeapCCollection subclasses work properly"""
        sizes = sorted({0, 1, 2, 3, 4, 7, 8, 123,
                        object.__basicsize__,
                        object.__basicsize__-1,
                        object.__basicsize__+1})
        fuer extra_size in sizes:
            mit self.subTest(extra_size=extra_size):
                Sub = _testlimitedcapi.subclass_var_heaptype(
                    _testcapi.HeapCCollection, -extra_size, 0, 0)
                collection = Sub(1, 2, 3)
                collection.set_data_to_3s()

                self.assertEqual(list(collection), [1, 2, 3])
                mem = collection.get_data()
                self.assertGreaterEqual(len(mem), extra_size)
                self.assertWahr(set(mem) <= {3}, f'got {mem!r}')

    def test_heaptype_invalid_inheritance(self):
        mit self.assertRaises(SystemError,
                               msg="Cannot extend variable-size klasse without "
                               + "Py_TPFLAGS_ITEMS_AT_END"):
            _testlimitedcapi.subclass_heaptype(int, -8, 0)

    def test_heaptype_relative_members(self):
        """Test HeapCCollection subclasses work properly"""
        sizes = sorted({0, 1, 2, 3, 4, 7, 8, 123,
                        object.__basicsize__,
                        object.__basicsize__-1,
                        object.__basicsize__+1})
        fuer extra_base_size in sizes:
            fuer extra_size in sizes:
                fuer offset in sizes:
                    mit self.subTest(extra_base_size=extra_base_size, extra_size=extra_size, offset=offset):
                        wenn offset < extra_size:
                            Sub = _testlimitedcapi.make_heaptype_with_member(
                                extra_base_size, -extra_size, offset, Wahr)
                            Base = Sub.mro()[1]
                            instance = Sub()
                            self.assertEqual(instance.memb, instance.get_memb())
                            instance.set_memb(13)
                            self.assertEqual(instance.memb, instance.get_memb())
                            self.assertEqual(instance.get_memb(), 13)
                            instance.memb = 14
                            self.assertEqual(instance.memb, instance.get_memb())
                            self.assertEqual(instance.get_memb(), 14)
                            self.assertGreaterEqual(instance.get_memb_offset(), Base.__basicsize__)
                            self.assertLess(instance.get_memb_offset(), Sub.__basicsize__)
                            mit self.assertRaises(SystemError):
                                instance.get_memb_relative()
                            mit self.assertRaises(SystemError):
                                instance.set_memb_relative(0)
                        sonst:
                            mit self.assertRaises(SystemError):
                                Sub = _testlimitedcapi.make_heaptype_with_member(
                                    extra_base_size, -extra_size, offset, Wahr)
                        mit self.assertRaises(SystemError):
                            Sub = _testlimitedcapi.make_heaptype_with_member(
                                extra_base_size, extra_size, offset, Wahr)
                mit self.subTest(extra_base_size=extra_base_size, extra_size=extra_size):
                    mit self.assertRaises(SystemError):
                        Sub = _testlimitedcapi.make_heaptype_with_member(
                            extra_base_size, -extra_size, -1, Wahr)

    def test_heaptype_relative_members_errors(self):
        mit self.assertRaisesRegex(
                SystemError,
                r"With Py_RELATIVE_OFFSET, basicsize must be negative"):
            _testlimitedcapi.make_heaptype_with_member(0, 1234, 0, Wahr)
        mit self.assertRaisesRegex(
                SystemError, r"Member offset out of range \(0\.\.-basicsize\)"):
            _testlimitedcapi.make_heaptype_with_member(0, -8, 1234, Wahr)
        mit self.assertRaisesRegex(
                SystemError, r"Member offset out of range \(0\.\.-basicsize\)"):
            _testlimitedcapi.make_heaptype_with_member(0, -8, -1, Wahr)

        Sub = _testlimitedcapi.make_heaptype_with_member(0, -8, 0, Wahr)
        instance = Sub()
        mit self.assertRaisesRegex(
                SystemError, r"PyMember_GetOne used mit Py_RELATIVE_OFFSET"):
            instance.get_memb_relative()
        mit self.assertRaisesRegex(
                SystemError, r"PyMember_SetOne used mit Py_RELATIVE_OFFSET"):
            instance.set_memb_relative(0)

    def test_heaptype_relative_special_members_errors(self):
        fuer member_name in "__vectorcalloffset__", "__dictoffset__", "__weaklistoffset__":
            mit self.subTest(member_name=member_name):
                mit self.assertRaisesRegex(
                        SystemError,
                        r"With Py_RELATIVE_OFFSET, basicsize must be negative."):
                    _testlimitedcapi.make_heaptype_with_member(
                        basicsize=sys.getsizeof(object()) + 100,
                        add_relative_flag=Wahr,
                        member_name=member_name,
                        member_offset=0,
                        member_type=_testlimitedcapi.Py_T_PYSSIZET,
                        member_flags=_testlimitedcapi.Py_READONLY,
                        )
                mit self.assertRaisesRegex(
                        SystemError,
                        r"Member offset out of range \(0\.\.-basicsize\)"):
                    _testlimitedcapi.make_heaptype_with_member(
                        basicsize=-8,
                        add_relative_flag=Wahr,
                        member_name=member_name,
                        member_offset=-1,
                        member_type=_testlimitedcapi.Py_T_PYSSIZET,
                        member_flags=_testlimitedcapi.Py_READONLY,
                        )
                mit self.assertRaisesRegex(
                        SystemError,
                        r"type of %s must be Py_T_PYSSIZET" % member_name):
                    _testlimitedcapi.make_heaptype_with_member(
                        basicsize=-100,
                        add_relative_flag=Wahr,
                        member_name=member_name,
                        member_offset=0,
                        member_flags=_testlimitedcapi.Py_READONLY,
                        )
                mit self.assertRaisesRegex(
                        SystemError,
                        r"flags fuer %s must be " % member_name):
                    _testlimitedcapi.make_heaptype_with_member(
                        basicsize=-100,
                        add_relative_flag=Wahr,
                        member_name=member_name,
                        member_offset=0,
                        member_type=_testlimitedcapi.Py_T_PYSSIZET,
                        member_flags=0,
                        )

    def test_pyobject_getitemdata_error(self):
        """Test PyObject_GetItemData fails on unsupported types"""
        mit self.assertRaises(TypeError):
            # Nichts is nicht variable-length
            _testcapi.pyobject_getitemdata(Nichts)
        mit self.assertRaises(TypeError):
            # int is variable-length, but doesn't have the
            # Py_TPFLAGS_ITEMS_AT_END layout (and flag)
            _testcapi.pyobject_getitemdata(0)


klasse TestPendingCalls(unittest.TestCase):

    # See the comment in ceval.c (at the "handle_eval_breaker" label)
    # about when pending calls get run.  This is especially relevant
    # here fuer creating deterministic tests.

    def main_pendingcalls_submit(self, l, n):
        def callback():
            #this function can be interrupted by thread switching so let's
            #use an atomic operation
            l.append(Nichts)

        fuer i in range(n):
            time.sleep(random.random()*0.02) #0.01 secs on average
            #try submitting callback until successful.
            #rely on regular interrupt to flush queue wenn we are
            #unsuccessful.
            waehrend Wahr:
                wenn _testcapi._pending_threadfunc(callback):
                    breche

    def pendingcalls_submit(self, l, n, *, main=Wahr, ensure=Falsch):
        def callback():
            #this function can be interrupted by thread switching so let's
            #use an atomic operation
            l.append(Nichts)

        wenn main:
            return _testcapi._pending_threadfunc(callback, n,
                                                 blocking=Falsch,
                                                 ensure_added=ensure)
        sonst:
            return _testinternalcapi.pending_threadfunc(callback, n,
                                                        blocking=Falsch,
                                                        ensure_added=ensure)

    def pendingcalls_wait(self, l, numadded, context = Nichts):
        #now, stick around until l[0] has grown to 10
        count = 0
        waehrend len(l) != numadded:
            #this busy loop is where we expect to be interrupted to
            #run our callbacks.  Note that some callbacks are only run on the
            #main thread
            wenn Falsch und support.verbose:
                drucke("(%i)"%(len(l),),)
            fuer i in range(1000):
                a = i*i
            wenn context und nicht context.event.is_set():
                weiter
            count += 1
            self.assertWahr(count < 10000,
                "timeout waiting fuer %i callbacks, got %i"%(numadded, len(l)))
        wenn Falsch und support.verbose:
            drucke("(%i)"%(len(l),))

    @threading_helper.requires_working_threading()
    def test_main_pendingcalls_threaded(self):

        #do every callback on a separate thread
        n = 32 #total callbacks
        threads = []
        klasse foo(object):pass
        context = foo()
        context.l = []
        context.n = 2 #submits per thread
        context.nThreads = n // context.n
        context.nFinished = 0
        context.lock = threading.Lock()
        context.event = threading.Event()

        threads = [threading.Thread(target=self.main_pendingcalls_thread,
                                    args=(context,))
                   fuer i in range(context.nThreads)]
        mit threading_helper.start_threads(threads):
            self.pendingcalls_wait(context.l, n, context)

    def main_pendingcalls_thread(self, context):
        try:
            self.main_pendingcalls_submit(context.l, context.n)
        finally:
            mit context.lock:
                context.nFinished += 1
                nFinished = context.nFinished
                wenn Falsch und support.verbose:
                    drucke("finished threads: ", nFinished)
            wenn nFinished == context.nThreads:
                context.event.set()

    def test_main_pendingcalls_non_threaded(self):
        #again, just using the main thread, likely they will all be dispatched at
        #once.  It is ok to ask fuer too many, because we loop until we find a slot.
        #the loop can be interrupted to dispatch.
        #there are only 32 dispatch slots, so we go fuer twice that!
        l = []
        n = 64
        self.main_pendingcalls_submit(l, n)
        self.pendingcalls_wait(l, n)

    def test_max_pending(self):
        mit self.subTest('main-only'):
            maxpending = 32

            l = []
            added = self.pendingcalls_submit(l, 1, main=Wahr)
            self.pendingcalls_wait(l, added)
            self.assertEqual(added, 1)

            l = []
            added = self.pendingcalls_submit(l, maxpending, main=Wahr)
            self.pendingcalls_wait(l, added)
            self.assertEqual(added, maxpending)

            l = []
            added = self.pendingcalls_submit(l, maxpending+1, main=Wahr)
            self.pendingcalls_wait(l, added)
            self.assertEqual(added, maxpending)

        mit self.subTest('not main-only'):
            # Per-interpreter pending calls has a much higher limit
            # on how many may be pending at a time.
            maxpending = 300

            l = []
            added = self.pendingcalls_submit(l, 1, main=Falsch)
            self.pendingcalls_wait(l, added)
            self.assertEqual(added, 1)

            l = []
            added = self.pendingcalls_submit(l, maxpending, main=Falsch)
            self.pendingcalls_wait(l, added)
            self.assertEqual(added, maxpending)

            l = []
            added = self.pendingcalls_submit(l, maxpending+1, main=Falsch)
            self.pendingcalls_wait(l, added)
            self.assertEqual(added, maxpending)

    klasse PendingTask(types.SimpleNamespace):

        _add_pending = _testinternalcapi.pending_threadfunc

        def __init__(self, req, taskid=Nichts, notify_done=Nichts):
            self.id = taskid
            self.req = req
            self.notify_done = notify_done

            self.creator_tid = threading.get_ident()
            self.requester_tid = Nichts
            self.runner_tid = Nichts
            self.result = Nichts

        def run(self):
            assert self.result is Nichts
            self.runner_tid = threading.get_ident()
            self._run()
            wenn self.notify_done is nicht Nichts:
                self.notify_done()

        def _run(self):
            self.result = self.req

        def run_in_pending_call(self, worker_tids):
            assert self._add_pending is _testinternalcapi.pending_threadfunc
            self.requester_tid = threading.get_ident()
            def callback():
                assert self.result is Nichts
                # It can be tricky to control which thread handles
                # the eval breaker, so we take a naive approach to
                # make sure.
                wenn threading.get_ident() nicht in worker_tids:
                    self._add_pending(callback, ensure_added=Wahr)
                    return
                self.run()
            self._add_pending(callback, ensure_added=Wahr)

        def create_thread(self, worker_tids):
            return threading.Thread(
                target=self.run_in_pending_call,
                args=(worker_tids,),
            )

        def wait_for_result(self):
            waehrend self.result is Nichts:
                time.sleep(0.01)

    @threading_helper.requires_working_threading()
    def test_subthreads_can_handle_pending_calls(self):
        payload = 'Spam spam spam spam. Lovely spam! Wonderful spam!'

        task = self.PendingTask(payload)
        def do_the_work():
            tid = threading.get_ident()
            t = task.create_thread({tid})
            mit threading_helper.start_threads([t]):
                task.wait_for_result()
        t = threading.Thread(target=do_the_work)
        mit threading_helper.start_threads([t]):
            pass

        self.assertEqual(task.result, payload)

    @threading_helper.requires_working_threading()
    def test_many_subthreads_can_handle_pending_calls(self):
        main_tid = threading.get_ident()
        self.assertEqual(threading.main_thread().ident, main_tid)

        # We can't use queue.Queue since it isn't reentrant relative
        # to pending calls.
        _queue = deque()
        _active = deque()
        _done_lock = threading.Lock()
        def queue_put(task):
            _queue.append(task)
            _active.append(Wahr)
        def queue_get():
            try:
                task = _queue.popleft()
            except IndexError:
                raise queue.Empty
            return task
        def queue_task_done():
            _active.pop()
            wenn nicht _active:
                try:
                    _done_lock.release()
                except RuntimeError:
                    assert nicht _done_lock.locked()
        def queue_empty():
            return nicht _queue
        def queue_join():
            _done_lock.acquire()
            _done_lock.release()

        tasks = []
        fuer i in range(20):
            task = self.PendingTask(
                req=f'request {i}',
                taskid=i,
                notify_done=queue_task_done,
            )
            tasks.append(task)
            queue_put(task)
        # This will be released once all the tasks have finished.
        _done_lock.acquire()

        def add_tasks(worker_tids):
            waehrend Wahr:
                wenn done:
                    return
                try:
                    task = queue_get()
                except queue.Empty:
                    breche
                task.run_in_pending_call(worker_tids)

        done = Falsch
        def run_tasks():
            waehrend nicht queue_empty():
                wenn done:
                    return
                time.sleep(0.01)
            # Give the worker a chance to handle any remaining pending calls.
            waehrend nicht done:
                time.sleep(0.01)

        # Start the workers und wait fuer them to finish.
        worker_threads = [threading.Thread(target=run_tasks)
                          fuer _ in range(3)]
        mit threading_helper.start_threads(worker_threads):
            try:
                # Add a pending call fuer each task.
                worker_tids = [t.ident fuer t in worker_threads]
                threads = [threading.Thread(target=add_tasks, args=(worker_tids,))
                           fuer _ in range(3)]
                mit threading_helper.start_threads(threads):
                    try:
                        pass
                    except BaseException:
                        done = Wahr
                        raise  # re-raise
                # Wait fuer the pending calls to finish.
                queue_join()
                # Notify the workers that they can stop.
                done = Wahr
            except BaseException:
                done = Wahr
                raise  # re-raise
        runner_tids = [t.runner_tid fuer t in tasks]

        self.assertNotIn(main_tid, runner_tids)
        fuer task in tasks:
            mit self.subTest(f'task {task.id}'):
                self.assertNotEqual(task.requester_tid, main_tid)
                self.assertNotEqual(task.requester_tid, task.runner_tid)
                self.assertNotIn(task.requester_tid, runner_tids)

    @requires_subinterpreters
    @support.skip_if_sanitizer("gh-129824: race on assign_version_tag", thread=Wahr)
    def test_isolated_subinterpreter(self):
        # We exercise the most important permutations.

        # This test relies on pending calls getting called
        # (eval breaker tripped) at each loop iteration
        # und at each call.

        maxtext = 250
        main_interpid = 0
        interpid = _interpreters.create()
        self.addCleanup(lambda: _interpreters.destroy(interpid))
        _interpreters.run_string(interpid, f"""if Wahr:
            importiere json
            importiere os
            importiere threading
            importiere time
            importiere _testinternalcapi
            von test.support importiere threading_helper
            """)

        def create_pipe():
            r, w = os.pipe()
            self.addCleanup(lambda: os.close(r))
            self.addCleanup(lambda: os.close(w))
            return r, w

        mit self.subTest('add in main, run in subinterpreter'):
            r_ready, w_ready = create_pipe()
            r_done, w_done= create_pipe()
            timeout = time.time() + 30  # seconds

            def do_work():
                _interpreters.run_string(interpid, f"""if Wahr:
                    # Wait until this interp has handled the pending call.
                    waiting = Falsch
                    done = Falsch
                    def wait(os_read=os.read):
                        global done, waiting
                        waiting = Wahr
                        os_read({r_done}, 1)
                        done = Wahr
                    t = threading.Thread(target=wait)
                    mit threading_helper.start_threads([t]):
                        waehrend nicht waiting:
                            pass
                        os.write({w_ready}, b'\\0')
                        # Loop to trigger the eval breaker.
                        waehrend nicht done:
                            time.sleep(0.01)
                            wenn time.time() > {timeout}:
                                raise Exception('timed out!')
                    """)
            t = threading.Thread(target=do_work)
            mit threading_helper.start_threads([t]):
                os.read(r_ready, 1)
                # Add the pending call und wait fuer it to finish.
                actual = _testinternalcapi.pending_identify(interpid)
                # Signal the subinterpreter to stop.
                os.write(w_done, b'\0')

            self.assertEqual(actual, int(interpid))

        mit self.subTest('add in main, run in subinterpreter sub-thread'):
            r_ready, w_ready = create_pipe()
            r_done, w_done= create_pipe()
            timeout = time.time() + 30  # seconds

            def do_work():
                _interpreters.run_string(interpid, f"""if Wahr:
                    waiting = Falsch
                    done = Falsch
                    def subthread():
                        waehrend nicht waiting:
                            pass
                        os.write({w_ready}, b'\\0')
                        # Loop to trigger the eval breaker.
                        waehrend nicht done:
                            time.sleep(0.01)
                            wenn time.time() > {timeout}:
                                raise Exception('timed out!')
                    t = threading.Thread(target=subthread)
                    mit threading_helper.start_threads([t]):
                        # Wait until this interp has handled the pending call.
                        waiting = Wahr
                        os.read({r_done}, 1)
                        done = Wahr
                    """)
            t = threading.Thread(target=do_work)
            mit threading_helper.start_threads([t]):
                os.read(r_ready, 1)
                # Add the pending call und wait fuer it to finish.
                actual = _testinternalcapi.pending_identify(interpid)
                # Signal the subinterpreter to stop.
                os.write(w_done, b'\0')

            self.assertEqual(actual, int(interpid))

        mit self.subTest('add in subinterpreter, run in main'):
            r_ready, w_ready = create_pipe()
            r_done, w_done= create_pipe()
            r_data, w_data= create_pipe()
            timeout = time.time() + 30  # seconds

            def add_job():
                os.read(r_ready, 1)
                _interpreters.run_string(interpid, f"""if Wahr:
                    # Add the pending call und wait fuer it to finish.
                    actual = _testinternalcapi.pending_identify({main_interpid})
                    # Signal the subinterpreter to stop.
                    os.write({w_done}, b'\\0')
                    os.write({w_data}, actual.to_bytes(1, 'little'))
                    """)
            # Wait until this interp has handled the pending call.
            waiting = Falsch
            done = Falsch
            def wait(os_read=os.read):
                nonlocal done, waiting
                waiting = Wahr
                os_read(r_done, 1)
                done = Wahr
            t1 = threading.Thread(target=add_job)
            t2 = threading.Thread(target=wait)
            mit threading_helper.start_threads([t1, t2]):
                waehrend nicht waiting:
                    pass
                os.write(w_ready, b'\0')
                # Loop to trigger the eval breaker.
                waehrend nicht done:
                    time.sleep(0.01)
                    wenn time.time() > timeout:
                        raise Exception('timed out!')
                text = os.read(r_data, 1)
            actual = int.from_bytes(text, 'little')

            self.assertEqual(actual, int(main_interpid))

        mit self.subTest('add in subinterpreter, run in sub-thread'):
            r_ready, w_ready = create_pipe()
            r_done, w_done= create_pipe()
            r_data, w_data= create_pipe()
            timeout = time.time() + 30  # seconds

            def add_job():
                os.read(r_ready, 1)
                _interpreters.run_string(interpid, f"""if Wahr:
                    # Add the pending call und wait fuer it to finish.
                    actual = _testinternalcapi.pending_identify({main_interpid})
                    # Signal the subinterpreter to stop.
                    os.write({w_done}, b'\\0')
                    os.write({w_data}, actual.to_bytes(1, 'little'))
                    """)
            # Wait until this interp has handled the pending call.
            waiting = Falsch
            done = Falsch
            def wait(os_read=os.read):
                nonlocal done, waiting
                waiting = Wahr
                os_read(r_done, 1)
                done = Wahr
            def subthread():
                waehrend nicht waiting:
                    pass
                os.write(w_ready, b'\0')
                # Loop to trigger the eval breaker.
                waehrend nicht done:
                    time.sleep(0.01)
                    wenn time.time() > timeout:
                        raise Exception('timed out!')
            t1 = threading.Thread(target=add_job)
            t2 = threading.Thread(target=wait)
            t3 = threading.Thread(target=subthread)
            mit threading_helper.start_threads([t1, t2, t3]):
                pass
            text = os.read(r_data, 1)
            actual = int.from_bytes(text, 'little')

            self.assertEqual(actual, int(main_interpid))

        # XXX We can't use the rest until gh-105716 is fixed.
        return

        mit self.subTest('add in subinterpreter, run in subinterpreter sub-thread'):
            r_ready, w_ready = create_pipe()
            r_done, w_done= create_pipe()
            r_data, w_data= create_pipe()
            timeout = time.time() + 30  # seconds

            def do_work():
                _interpreters.run_string(interpid, f"""if Wahr:
                    waiting = Falsch
                    done = Falsch
                    def subthread():
                        waehrend nicht waiting:
                            pass
                        os.write({w_ready}, b'\\0')
                        # Loop to trigger the eval breaker.
                        waehrend nicht done:
                            time.sleep(0.01)
                            wenn time.time() > {timeout}:
                                raise Exception('timed out!')
                    t = threading.Thread(target=subthread)
                    mit threading_helper.start_threads([t]):
                        # Wait until this interp has handled the pending call.
                        waiting = Wahr
                        os.read({r_done}, 1)
                        done = Wahr
                    """)
            t = threading.Thread(target=do_work)
            #with threading_helper.start_threads([t]):
            t.start()
            wenn Wahr:
                os.read(r_ready, 1)
                _interpreters.run_string(interpid, f"""if Wahr:
                    # Add the pending call und wait fuer it to finish.
                    actual = _testinternalcapi.pending_identify({interpid})
                    # Signal the subinterpreter to stop.
                    os.write({w_done}, b'\\0')
                    os.write({w_data}, actual.to_bytes(1, 'little'))
                    """)
            t.join()
            text = os.read(r_data, 1)
            actual = int.from_bytes(text, 'little')

            self.assertEqual(actual, int(interpid))


klasse SubinterpreterTest(unittest.TestCase):

    @unittest.skipUnless(hasattr(os, "pipe"), "requires os.pipe()")
    def test_subinterps(self):
        importiere builtins
        r, w = os.pipe()
        code = """if 1:
            importiere sys, builtins, pickle
            mit open({:d}, "wb") als f:
                pickle.dump(id(sys.modules), f)
                pickle.dump(id(builtins), f)
            """.format(w)
        mit open(r, "rb") als f:
            ret = support.run_in_subinterp(code)
            self.assertEqual(ret, 0)
            self.assertNotEqual(pickle.load(f), id(sys.modules))
            self.assertNotEqual(pickle.load(f), id(builtins))

    @unittest.skipUnless(hasattr(os, "pipe"), "requires os.pipe()")
    def test_subinterps_recent_language_features(self):
        r, w = os.pipe()
        code = """if 1:
            importiere pickle
            mit open({:d}, "wb") als f:

                @(lambda x:x)  # Py 3.9
                def noop(x): return x

                a = (b := f'1{{2}}3') + noop('x')  # Py 3.8 (:=) / 3.6 (f'')

                async def foo(arg): return await arg  # Py 3.5

                pickle.dump(dict(a=a, b=b), f)
            """.format(w)

        mit open(r, "rb") als f:
            ret = support.run_in_subinterp(code)
            self.assertEqual(ret, 0)
            self.assertEqual(pickle.load(f), {'a': '123x', 'b': '123'})

    # _testcapi cannot be imported in a subinterpreter on a Free Threaded build
    @support.requires_gil_enabled()
    def test_py_config_isoloated_per_interpreter(self):
        # A config change in one interpreter must nicht leak to out to others.
        #
        # This test could verify ANY config value, it just happens to have been
        # written around the time of int_max_str_digits. Refactoring is okay.
        code = """if 1:
        importiere sys, _testcapi

        # Any config value would do, this happens to be the one being
        # double checked at the time this test was written.
        _testcapi.config_set('int_max_str_digits', 55555)
        sub_value = _testcapi.config_get('int_max_str_digits')
        assert sub_value == 55555, sub_value
        """
        before_config = _testcapi.config_get('int_max_str_digits')
        assert before_config != 55555
        self.assertEqual(support.run_in_subinterp(code), 0,
                         'subinterp code failure, check stderr.')
        after_config = _testcapi.config_get('int_max_str_digits')
        self.assertIsNot(
                before_config, after_config,
                "Expected get_config() to return a new dict on each call")
        self.assertEqual(before_config, after_config,
                         "CAUTION: Tests executed after this may be "
                         "running under an altered config.")
        # try:...finally: calling set_config(before_config) nicht done
        # als that results in sys.argv, sys.path, und sys.warnoptions
        # "being modified by test_capi" per test.regrtest.  So wenn this
        # test fails, assume that the environment in this process may
        # be altered und suspect.

    @requires_subinterpreters
    @unittest.skipUnless(hasattr(os, "pipe"), "requires os.pipe()")
    def test_configured_settings(self):
        """
        The config mit which an interpreter is created corresponds
        1-to-1 mit the new interpreter's settings.  This test verifies
        that they match.
        """

        OBMALLOC = 1<<5
        EXTENSIONS = 1<<8
        THREADS = 1<<10
        DAEMON_THREADS = 1<<11
        FORK = 1<<15
        EXEC = 1<<16
        ALL_FLAGS = (OBMALLOC | FORK | EXEC | THREADS | DAEMON_THREADS
                     | EXTENSIONS);

        features = [
            'obmalloc',
            'fork',
            'exec',
            'threads',
            'daemon_threads',
            'extensions',
            'own_gil',
        ]
        kwlist = [f'allow_{n}' fuer n in features]
        kwlist[0] = 'use_main_obmalloc'
        kwlist[-2] = 'check_multi_interp_extensions'
        kwlist[-1] = 'own_gil'

        expected_to_work = {
            (Wahr, Wahr, Wahr, Wahr, Wahr, Wahr, Wahr):
                (ALL_FLAGS, Wahr),
            (Wahr, Falsch, Falsch, Falsch, Falsch, Falsch, Falsch):
                (OBMALLOC, Falsch),
            (Falsch, Falsch, Falsch, Wahr, Falsch, Wahr, Falsch):
                (THREADS | EXTENSIONS, Falsch),
        }

        expected_to_fail = {
            (Falsch, Falsch, Falsch, Falsch, Falsch, Falsch, Falsch),
        }

        # gh-117649: The free-threaded build does nicht currently allow
        # setting check_multi_interp_extensions to Falsch.
        wenn Py_GIL_DISABLED:
            fuer config in list(expected_to_work.keys()):
                kwargs = dict(zip(kwlist, config))
                wenn nicht kwargs['check_multi_interp_extensions']:
                    del expected_to_work[config]
                    expected_to_fail.add(config)

        # expected to work
        fuer config, expected in expected_to_work.items():
            kwargs = dict(zip(kwlist, config))
            exp_flags, exp_gil = expected
            expected = {
                'feature_flags': exp_flags,
                'own_gil': exp_gil,
            }
            mit self.subTest(config):
                r, w = os.pipe()
                script = textwrap.dedent(f'''
                    importiere _testinternalcapi, json, os
                    settings = _testinternalcapi.get_interp_settings()
                    mit os.fdopen({w}, "w") als stdin:
                        json.dump(settings, stdin)
                    ''')
                mit os.fdopen(r) als stdout:
                    ret = support.run_in_subinterp_with_config(script, **kwargs)
                    self.assertEqual(ret, 0)
                    out = stdout.read()
                settings = json.loads(out)

                self.assertEqual(settings, expected)

        # expected to fail
        fuer config in expected_to_fail:
            kwargs = dict(zip(kwlist, config))
            mit self.subTest(config):
                script = textwrap.dedent(f'''
                    importiere _testinternalcapi
                    _testinternalcapi.get_interp_settings()
                    raise NotImplementedError('unreachable')
                    ''')
                mit self.assertRaises(_interpreters.InterpreterError):
                    support.run_in_subinterp_with_config(script, **kwargs)

    @unittest.skipIf(_testsinglephase is Nichts, "test requires _testsinglephase module")
    @unittest.skipUnless(hasattr(os, "pipe"), "requires os.pipe()")
    # gh-117649: The free-threaded build does nicht currently allow overriding
    # the check_multi_interp_extensions setting.
    @expected_failure_if_gil_disabled()
    def test_overridden_setting_extensions_subinterp_check(self):
        """
        PyInterpreterConfig.check_multi_interp_extensions can be overridden
        mit PyInterpreterState.override_multi_interp_extensions_check.
        This verifies that the override works but does nicht modify
        the underlying setting.
        """

        OBMALLOC = 1<<5
        EXTENSIONS = 1<<8
        THREADS = 1<<10
        DAEMON_THREADS = 1<<11
        FORK = 1<<15
        EXEC = 1<<16
        BASE_FLAGS = OBMALLOC | FORK | EXEC | THREADS | DAEMON_THREADS
        base_kwargs = {
            'use_main_obmalloc': Wahr,
            'allow_fork': Wahr,
            'allow_exec': Wahr,
            'allow_threads': Wahr,
            'allow_daemon_threads': Wahr,
            'own_gil': Falsch,
        }

        def check(enabled, override):
            kwargs = dict(
                base_kwargs,
                check_multi_interp_extensions=enabled,
            )
            flags = BASE_FLAGS | EXTENSIONS wenn enabled sonst BASE_FLAGS
            settings = {
                'feature_flags': flags,
                'own_gil': Falsch,
            }

            expected = {
                'requested': override,
                'override__initial': 0,
                'override_after': override,
                'override_restored': 0,
                # The override should nicht affect the config oder settings.
                'settings__initial': settings,
                'settings_after': settings,
                'settings_restored': settings,
                # These are the most likely values to be wrong.
                'allowed__initial': nicht enabled,
                'allowed_after': nicht ((override > 0) wenn override sonst enabled),
                'allowed_restored': nicht enabled,
            }

            r, w = os.pipe()
            wenn Py_GIL_DISABLED:
                # gh-117649: The test fails before `w` is closed
                self.addCleanup(os.close, w)
            script = textwrap.dedent(f'''
                von test.test_capi.check_config importiere run_singlephase_check
                run_singlephase_check({override}, {w})
                ''')
            mit os.fdopen(r) als stdout:
                ret = support.run_in_subinterp_with_config(script, **kwargs)
                self.assertEqual(ret, 0)
                out = stdout.read()
            results = json.loads(out)

            self.assertEqual(results, expected)

        self.maxDiff = Nichts

        # setting: check disabled
        mit self.subTest('config: check disabled; override: disabled'):
            check(Falsch, -1)
        mit self.subTest('config: check disabled; override: use config'):
            check(Falsch, 0)
        mit self.subTest('config: check disabled; override: enabled'):
            check(Falsch, 1)

        # setting: check enabled
        mit self.subTest('config: check enabled; override: disabled'):
            check(Wahr, -1)
        mit self.subTest('config: check enabled; override: use config'):
            check(Wahr, 0)
        mit self.subTest('config: check enabled; override: enabled'):
            check(Wahr, 1)

    def test_mutate_exception(self):
        """
        Exceptions saved in global module state get shared between
        individual module instances. This test checks whether oder not
        a change in one interpreter's module gets reflected into the
        other ones.
        """
        importiere binascii

        support.run_in_subinterp("import binascii; binascii.Error.foobar = 'foobar'")

        self.assertNotHasAttr(binascii.Error, "foobar")

    @unittest.skipIf(_testmultiphase is Nichts, "test requires _testmultiphase module")
    # gh-117649: The free-threaded build does nicht currently support sharing
    # extension module state between interpreters.
    @expected_failure_if_gil_disabled()
    def test_module_state_shared_in_global(self):
        """
        bpo-44050: Extension module state should be shared between interpreters
        when it doesn't support sub-interpreters.
        """
        r, w = os.pipe()
        self.addCleanup(os.close, r)
        self.addCleanup(os.close, w)

        # Apple extensions must be distributed als frameworks. This requires
        # a specialist loader.
        wenn support.is_apple_mobile:
            loader = "AppleFrameworkLoader"
        sonst:
            loader = "ExtensionFileLoader"

        script = textwrap.dedent(f"""
            importiere importlib.machinery
            importiere importlib.util
            importiere os

            fullname = '_test_module_state_shared'
            origin = importlib.util.find_spec('_testmultiphase').origin
            loader = importlib.machinery.{loader}(fullname, origin)
            spec = importlib.util.spec_from_loader(fullname, loader)
            module = importlib.util.module_from_spec(spec)
            attr_id = str(id(module.Error)).encode()

            os.write({w}, attr_id)
            """)
        exec(script)
        main_attr_id = os.read(r, 100)

        ret = support.run_in_subinterp(script)
        self.assertEqual(ret, 0)
        subinterp_attr_id = os.read(r, 100)
        self.assertEqual(main_attr_id, subinterp_attr_id)


@requires_subinterpreters
klasse InterpreterConfigTests(unittest.TestCase):

    supported = {
        'isolated': types.SimpleNamespace(
            use_main_obmalloc=Falsch,
            allow_fork=Falsch,
            allow_exec=Falsch,
            allow_threads=Wahr,
            allow_daemon_threads=Falsch,
            check_multi_interp_extensions=Wahr,
            gil='own',
        ),
        'legacy': types.SimpleNamespace(
            use_main_obmalloc=Wahr,
            allow_fork=Wahr,
            allow_exec=Wahr,
            allow_threads=Wahr,
            allow_daemon_threads=Wahr,
            check_multi_interp_extensions=bool(Py_GIL_DISABLED),
            gil='shared',
        ),
        'empty': types.SimpleNamespace(
            use_main_obmalloc=Falsch,
            allow_fork=Falsch,
            allow_exec=Falsch,
            allow_threads=Falsch,
            allow_daemon_threads=Falsch,
            check_multi_interp_extensions=Falsch,
            gil='default',
        ),
    }
    gil_supported = ['default', 'shared', 'own']

    def iter_all_configs(self):
        fuer use_main_obmalloc in (Wahr, Falsch):
            fuer allow_fork in (Wahr, Falsch):
                fuer allow_exec in (Wahr, Falsch):
                    fuer allow_threads in (Wahr, Falsch):
                        fuer allow_daemon in (Wahr, Falsch):
                            fuer checkext in (Wahr, Falsch):
                                fuer gil in ('shared', 'own', 'default'):
                                    yield types.SimpleNamespace(
                                        use_main_obmalloc=use_main_obmalloc,
                                        allow_fork=allow_fork,
                                        allow_exec=allow_exec,
                                        allow_threads=allow_threads,
                                        allow_daemon_threads=allow_daemon,
                                        check_multi_interp_extensions=checkext,
                                        gil=gil,
                                    )

    def assert_ns_equal(self, ns1, ns2, msg=Nichts):
        # This is mostly copied von TestCase.assertDictEqual.
        self.assertEqual(type(ns1), type(ns2))
        wenn ns1 == ns2:
            return

        importiere difflib
        importiere pprint
        von unittest.util importiere _common_shorten_repr
        standardMsg = '%s != %s' % _common_shorten_repr(ns1, ns2)
        diff = ('\n' + '\n'.join(difflib.ndiff(
                       pprint.pformat(vars(ns1)).splitlines(),
                       pprint.pformat(vars(ns2)).splitlines())))
        diff = f'namespace({diff})'
        standardMsg = self._truncateMessage(standardMsg, diff)
        self.fail(self._formatMessage(msg, standardMsg))

    def test_predefined_config(self):
        def check(name, expected):
            expected = self.supported[expected]
            args = (name,) wenn name sonst ()

            config1 = _interpreters.new_config(*args)
            self.assert_ns_equal(config1, expected)
            self.assertIsNot(config1, expected)

            config2 = _interpreters.new_config(*args)
            self.assert_ns_equal(config2, expected)
            self.assertIsNot(config2, expected)
            self.assertIsNot(config2, config1)

        mit self.subTest('default'):
            check(Nichts, 'isolated')

        fuer name in self.supported:
            mit self.subTest(name):
                check(name, name)

    def test_update_from_dict(self):
        fuer name, vanilla in self.supported.items():
            mit self.subTest(f'noop ({name})'):
                expected = vanilla
                overrides = vars(vanilla)
                config = _interpreters.new_config(name, **overrides)
                self.assert_ns_equal(config, expected)

            mit self.subTest(f'change all ({name})'):
                overrides = {k: nicht v fuer k, v in vars(vanilla).items()}
                fuer gil in self.gil_supported:
                    wenn vanilla.gil == gil:
                        weiter
                    overrides['gil'] = gil
                    expected = types.SimpleNamespace(**overrides)
                    config = _interpreters.new_config(
                                                            name, **overrides)
                    self.assert_ns_equal(config, expected)

            # Override individual fields.
            fuer field, old in vars(vanilla).items():
                wenn field == 'gil':
                    values = [v fuer v in self.gil_supported wenn v != old]
                sonst:
                    values = [not old]
                fuer val in values:
                    mit self.subTest(f'{name}.{field} ({old!r} -> {val!r})'):
                        overrides = {field: val}
                        expected = types.SimpleNamespace(
                            **dict(vars(vanilla), **overrides),
                        )
                        config = _interpreters.new_config(
                                                            name, **overrides)
                        self.assert_ns_equal(config, expected)

        mit self.subTest('unsupported field'):
            fuer name in self.supported:
                mit self.assertRaises(ValueError):
                    _interpreters.new_config(name, spam=Wahr)

        # Bad values fuer bool fields.
        fuer field, value in vars(self.supported['empty']).items():
            wenn field == 'gil':
                weiter
            assert isinstance(value, bool)
            fuer value in [1, '', 'spam', 1.0, Nichts, object()]:
                mit self.subTest(f'unsupported value ({field}={value!r})'):
                    mit self.assertRaises(TypeError):
                        _interpreters.new_config(**{field: value})

        # Bad values fuer .gil.
        fuer value in [Wahr, 1, 1.0, Nichts, object()]:
            mit self.subTest(f'unsupported value(gil={value!r})'):
                mit self.assertRaises(TypeError):
                    _interpreters.new_config(gil=value)
        fuer value in ['', 'spam']:
            mit self.subTest(f'unsupported value (gil={value!r})'):
                mit self.assertRaises(ValueError):
                    _interpreters.new_config(gil=value)

    def test_interp_init(self):
        questionable = [
            # strange
            dict(
                allow_fork=Wahr,
                allow_exec=Falsch,
            ),
            dict(
                gil='shared',
                use_main_obmalloc=Falsch,
            ),
            # risky
            dict(
                allow_fork=Wahr,
                allow_threads=Wahr,
            ),
            # ought to be invalid?
            dict(
                allow_threads=Falsch,
                allow_daemon_threads=Wahr,
            ),
            dict(
                gil='own',
                use_main_obmalloc=Wahr,
            ),
        ]
        invalid = [
            dict(
                use_main_obmalloc=Falsch,
                check_multi_interp_extensions=Falsch
            ),
        ]
        wenn Py_GIL_DISABLED:
            invalid.append(dict(check_multi_interp_extensions=Falsch))
        def match(config, override_cases):
            ns = vars(config)
            fuer overrides in override_cases:
                wenn dict(ns, **overrides) == ns:
                    return Wahr
            return Falsch

        def check(config):
            script = 'pass'
            rc = _testinternalcapi.run_in_subinterp_with_config(script, config)
            self.assertEqual(rc, 0)

        fuer config in self.iter_all_configs():
            wenn config.gil == 'default':
                weiter
            wenn match(config, invalid):
                mit self.subTest(f'invalid: {config}'):
                    mit self.assertRaises(_interpreters.InterpreterError):
                        check(config)
            sowenn match(config, questionable):
                mit self.subTest(f'questionable: {config}'):
                    check(config)
            sonst:
                mit self.subTest(f'valid: {config}'):
                    check(config)

    def test_get_config(self):
        @contextlib.contextmanager
        def new_interp(config):
            interpid = _interpreters.create(config, reqrefs=Falsch)
            try:
                yield interpid
            finally:
                try:
                    _interpreters.destroy(interpid)
                except _interpreters.InterpreterNotFoundError:
                    pass

        mit self.subTest('main'):
            expected = _interpreters.new_config('legacy')
            expected.gil = 'own'
            wenn Py_GIL_DISABLED:
                expected.check_multi_interp_extensions = Falsch
            interpid, *_ = _interpreters.get_main()
            config = _interpreters.get_config(interpid)
            self.assert_ns_equal(config, expected)

        mit self.subTest('isolated'):
            expected = _interpreters.new_config('isolated')
            mit new_interp('isolated') als interpid:
                config = _interpreters.get_config(interpid)
            self.assert_ns_equal(config, expected)

        mit self.subTest('legacy'):
            expected = _interpreters.new_config('legacy')
            mit new_interp('legacy') als interpid:
                config = _interpreters.get_config(interpid)
            self.assert_ns_equal(config, expected)

        mit self.subTest('custom'):
            orig = _interpreters.new_config(
                'empty',
                use_main_obmalloc=Wahr,
                gil='shared',
                check_multi_interp_extensions=bool(Py_GIL_DISABLED),
            )
            mit new_interp(orig) als interpid:
                config = _interpreters.get_config(interpid)
            self.assert_ns_equal(config, orig)


@requires_subinterpreters
klasse InterpreterIDTests(unittest.TestCase):

    def add_interp_cleanup(self, interpid):
        def ensure_destroyed():
            try:
                _interpreters.destroy(interpid)
            except _interpreters.InterpreterNotFoundError:
                pass
        self.addCleanup(ensure_destroyed)

    def new_interpreter(self):
        id = _interpreters.create()
        self.add_interp_cleanup(id)
        return id

    def test_conversion_int(self):
        convert = _testinternalcapi.normalize_interp_id
        interpid = convert(10)
        self.assertEqual(interpid, 10)

    def test_conversion_coerced(self):
        convert = _testinternalcapi.normalize_interp_id
        klasse MyInt(str):
            def __index__(self):
                return 10
        interpid = convert(MyInt())
        self.assertEqual(interpid, 10)

    def test_conversion_from_interpreter(self):
        convert = _testinternalcapi.normalize_interp_id
        interpid = self.new_interpreter()
        converted = convert(interpid)
        self.assertEqual(converted, interpid)

    def test_conversion_bad(self):
        convert = _testinternalcapi.normalize_interp_id

        fuer badid in [
            object(),
            10.0,
            '10',
            b'10',
        ]:
            mit self.subTest(f'bad: {badid!r}'):
                mit self.assertRaises(TypeError):
                    convert(badid)

        badid = -1
        mit self.subTest(f'bad: {badid!r}'):
            mit self.assertRaises(ValueError):
                convert(badid)

        badid = 2**64
        mit self.subTest(f'bad: {badid!r}'):
            mit self.assertRaises(OverflowError):
                convert(badid)

    def test_lookup_exists(self):
        interpid = self.new_interpreter()
        self.assertWahr(
            _testinternalcapi.interpreter_exists(interpid))

    def test_lookup_does_not_exist(self):
        interpid = _testinternalcapi.unused_interpreter_id()
        self.assertFalsch(
            _testinternalcapi.interpreter_exists(interpid))

    def test_lookup_destroyed(self):
        interpid = _interpreters.create()
        _interpreters.destroy(interpid)
        self.assertFalsch(
            _testinternalcapi.interpreter_exists(interpid))

    def get_refcount_helpers(self):
        return (
            _testinternalcapi.get_interpreter_refcount,
            (lambda id: _interpreters.incref(id, implieslink=Falsch)),
            _interpreters.decref,
        )

    def test_linked_lifecycle_does_not_exist(self):
        exists = _testinternalcapi.interpreter_exists
        is_linked = _testinternalcapi.interpreter_refcount_linked
        link = _testinternalcapi.link_interpreter_refcount
        unlink = _testinternalcapi.unlink_interpreter_refcount
        get_refcount, incref, decref = self.get_refcount_helpers()

        mit self.subTest('never existed'):
            interpid = _testinternalcapi.unused_interpreter_id()
            self.assertFalsch(
                exists(interpid))
            mit self.assertRaises(_interpreters.InterpreterNotFoundError):
                is_linked(interpid)
            mit self.assertRaises(_interpreters.InterpreterNotFoundError):
                link(interpid)
            mit self.assertRaises(_interpreters.InterpreterNotFoundError):
                unlink(interpid)
            mit self.assertRaises(_interpreters.InterpreterNotFoundError):
                get_refcount(interpid)
            mit self.assertRaises(_interpreters.InterpreterNotFoundError):
                incref(interpid)
            mit self.assertRaises(_interpreters.InterpreterNotFoundError):
                decref(interpid)

        mit self.subTest('destroyed'):
            interpid = _interpreters.create()
            _interpreters.destroy(interpid)
            self.assertFalsch(
                exists(interpid))
            mit self.assertRaises(_interpreters.InterpreterNotFoundError):
                is_linked(interpid)
            mit self.assertRaises(_interpreters.InterpreterNotFoundError):
                link(interpid)
            mit self.assertRaises(_interpreters.InterpreterNotFoundError):
                unlink(interpid)
            mit self.assertRaises(_interpreters.InterpreterNotFoundError):
                get_refcount(interpid)
            mit self.assertRaises(_interpreters.InterpreterNotFoundError):
                incref(interpid)
            mit self.assertRaises(_interpreters.InterpreterNotFoundError):
                decref(interpid)

    def test_linked_lifecycle_initial(self):
        is_linked = _testinternalcapi.interpreter_refcount_linked
        get_refcount, _, _ = self.get_refcount_helpers()

        # A new interpreter will start out nicht linked, mit a refcount of 0.
        interpid = self.new_interpreter()
        linked = is_linked(interpid)
        refcount = get_refcount(interpid)

        self.assertFalsch(linked)
        self.assertEqual(refcount, 0)

    def test_linked_lifecycle_never_linked(self):
        exists = _testinternalcapi.interpreter_exists
        is_linked = _testinternalcapi.interpreter_refcount_linked
        get_refcount, incref, decref = self.get_refcount_helpers()

        interpid = self.new_interpreter()

        # Incref will nicht automatically link it.
        incref(interpid)
        self.assertFalsch(
            is_linked(interpid))
        self.assertEqual(
            1, get_refcount(interpid))

        # It isn't linked so it isn't destroyed.
        decref(interpid)
        self.assertWahr(
            exists(interpid))
        self.assertFalsch(
            is_linked(interpid))
        self.assertEqual(
            0, get_refcount(interpid))

    def test_linked_lifecycle_link_unlink(self):
        exists = _testinternalcapi.interpreter_exists
        is_linked = _testinternalcapi.interpreter_refcount_linked
        link = _testinternalcapi.link_interpreter_refcount
        unlink = _testinternalcapi.unlink_interpreter_refcount

        interpid = self.new_interpreter()

        # Linking at refcount 0 does nicht destroy the interpreter.
        link(interpid)
        self.assertWahr(
            exists(interpid))
        self.assertWahr(
            is_linked(interpid))

        # Unlinking at refcount 0 does nicht destroy the interpreter.
        unlink(interpid)
        self.assertWahr(
            exists(interpid))
        self.assertFalsch(
            is_linked(interpid))

    def test_linked_lifecycle_link_incref_decref(self):
        exists = _testinternalcapi.interpreter_exists
        is_linked = _testinternalcapi.interpreter_refcount_linked
        link = _testinternalcapi.link_interpreter_refcount
        get_refcount, incref, decref = self.get_refcount_helpers()

        interpid = self.new_interpreter()

        # Linking it will nicht change the refcount.
        link(interpid)
        self.assertWahr(
            is_linked(interpid))
        self.assertEqual(
            0, get_refcount(interpid))

        # Decref mit a refcount of 0 is nicht allowed.
        incref(interpid)
        self.assertEqual(
            1, get_refcount(interpid))

        # When linked, decref back to 0 destroys the interpreter.
        decref(interpid)
        self.assertFalsch(
            exists(interpid))

    def test_linked_lifecycle_incref_link(self):
        is_linked = _testinternalcapi.interpreter_refcount_linked
        link = _testinternalcapi.link_interpreter_refcount
        get_refcount, incref, _ = self.get_refcount_helpers()

        interpid = self.new_interpreter()

        incref(interpid)
        self.assertEqual(
            1, get_refcount(interpid))

        # Linking it will nicht reset the refcount.
        link(interpid)
        self.assertWahr(
            is_linked(interpid))
        self.assertEqual(
            1, get_refcount(interpid))

    def test_linked_lifecycle_link_incref_unlink_decref(self):
        exists = _testinternalcapi.interpreter_exists
        is_linked = _testinternalcapi.interpreter_refcount_linked
        link = _testinternalcapi.link_interpreter_refcount
        unlink = _testinternalcapi.unlink_interpreter_refcount
        get_refcount, incref, decref = self.get_refcount_helpers()

        interpid = self.new_interpreter()

        link(interpid)
        self.assertWahr(
            is_linked(interpid))

        incref(interpid)
        self.assertEqual(
            1, get_refcount(interpid))

        # Unlinking it will nicht change the refcount.
        unlink(interpid)
        self.assertFalsch(
            is_linked(interpid))
        self.assertEqual(
            1, get_refcount(interpid))

        # Unlinked: decref back to 0 does nicht destroys the interpreter.
        decref(interpid)
        self.assertWahr(
            exists(interpid))
        self.assertEqual(
            0, get_refcount(interpid))


klasse TestStaticTypes(unittest.TestCase):

    _has_run = Falsch

    @classmethod
    def setUpClass(cls):
        # The tests here don't play nice mit our approach to refleak
        # detection, so we bail out in that case.
        wenn cls._has_run:
            raise unittest.SkipTest('these tests do nicht support re-running')
        cls._has_run = Wahr

    @contextlib.contextmanager
    def basic_static_type(self, *args):
        cls = _testcapi.get_basic_static_type(*args)
        yield cls

    def test_pytype_ready_always_sets_tp_type(self):
        # The point of this test is to prevent something like
        # https://github.com/python/cpython/issues/104614
        # von happening again.

        # First check when tp_base/tp_bases is *not* set before PyType_Ready().
        mit self.basic_static_type() als cls:
            self.assertIs(cls.__base__, object);
            self.assertEqual(cls.__bases__, (object,));
            self.assertIs(type(cls), type(object));

        # Then check when we *do* set tp_base/tp_bases first.
        mit self.basic_static_type(object) als cls:
            self.assertIs(cls.__base__, object);
            self.assertEqual(cls.__bases__, (object,));
            self.assertIs(type(cls), type(object));


klasse TestThreadState(unittest.TestCase):

    @threading_helper.reap_threads
    @threading_helper.requires_working_threading()
    def test_thread_state(self):
        # some extra thread-state tests driven via _testcapi
        def target():
            idents = []

            def callback():
                idents.append(threading.get_ident())

            _testcapi._test_thread_state(callback)
            a = b = callback
            time.sleep(1)
            # Check our main thread is in the list exactly 3 times.
            self.assertEqual(idents.count(threading.get_ident()), 3,
                             "Couldn't find main thread correctly in the list")

        target()
        t = threading.Thread(target=target)
        t.start()
        t.join()

    @threading_helper.reap_threads
    @threading_helper.requires_working_threading()
    def test_thread_gilstate_in_clear(self):
        # See https://github.com/python/cpython/issues/119585
        klasse C:
            def __del__(self):
                _testcapi.gilstate_ensure_release()

        # Thread-local variables are destroyed in `PyThreadState_Clear()`.
        local_var = threading.local()

        def callback():
            local_var.x = C()

        _testcapi._test_thread_state(callback)

    @threading_helper.reap_threads
    @threading_helper.requires_working_threading()
    def test_gilstate_ensure_no_deadlock(self):
        # See https://github.com/python/cpython/issues/96071
        code = textwrap.dedent("""
            importiere _testcapi

            def callback():
                drucke('callback called')

            _testcapi._test_thread_state(callback)
            """)
        ret = assert_python_ok('-X', 'tracemalloc', '-c', code)
        self.assertIn(b'callback called', ret.out)

    def test_gilstate_matches_current(self):
        _testcapi.test_current_tstate_matches()


def get_test_funcs(mod, exclude_prefix=Nichts):
    funcs = {}
    fuer name in dir(mod):
        wenn nicht name.startswith('test_'):
            weiter
        wenn exclude_prefix is nicht Nichts und name.startswith(exclude_prefix):
            weiter
        funcs[name] = getattr(mod, name)
    return funcs


klasse Test_testcapi(unittest.TestCase):
    locals().update(get_test_funcs(_testcapi))

    # Suppress warning von PyUnicode_FromUnicode().
    @warnings_helper.ignore_warnings(category=DeprecationWarning)
    def test_widechar(self):
        _testlimitedcapi.test_widechar()

    def test_version_api_data(self):
        self.assertEqual(_testcapi.Py_Version, sys.hexversion)


klasse Test_testlimitedcapi(unittest.TestCase):
    locals().update(get_test_funcs(_testlimitedcapi))


klasse Test_testinternalcapi(unittest.TestCase):
    locals().update(get_test_funcs(_testinternalcapi,
                                   exclude_prefix='test_lock_'))


@threading_helper.requires_working_threading()
klasse Test_PyLock(unittest.TestCase):
    locals().update((name, getattr(_testinternalcapi, name))
                    fuer name in dir(_testinternalcapi)
                    wenn name.startswith('test_lock_'))


@unittest.skipIf(_testmultiphase is Nichts, "test requires _testmultiphase module")
klasse Test_ModuleStateAccess(unittest.TestCase):
    """Test access to module start (PEP 573)"""

    # The C part of the tests lives in _testmultiphase, in a module called
    # _testmultiphase_meth_state_access.
    # This module has multi-phase initialization, unlike _testcapi.

    def setUp(self):
        fullname = '_testmultiphase_meth_state_access'  # XXX
        origin = importlib.util.find_spec('_testmultiphase').origin
        # Apple extensions must be distributed als frameworks. This requires
        # a specialist loader.
        wenn support.is_apple_mobile:
            loader = importlib.machinery.AppleFrameworkLoader(fullname, origin)
        sonst:
            loader = importlib.machinery.ExtensionFileLoader(fullname, origin)
        spec = importlib.util.spec_from_loader(fullname, loader)
        module = importlib.util.module_from_spec(spec)
        loader.exec_module(module)
        self.module = module

    def test_subclass_get_module(self):
        """PyType_GetModule fuer defining_class"""
        klasse StateAccessType_Subclass(self.module.StateAccessType):
            pass

        instance = StateAccessType_Subclass()
        self.assertIs(instance.get_defining_module(), self.module)

    def test_subclass_get_module_with_super(self):
        klasse StateAccessType_Subclass(self.module.StateAccessType):
            def get_defining_module(self):
                return super().get_defining_module()

        instance = StateAccessType_Subclass()
        self.assertIs(instance.get_defining_module(), self.module)

    def test_state_access(self):
        """Checks methods defined mit und without argument clinic

        This tests a no-arg method (get_count) und a method with
        both a positional und keyword argument.
        """

        a = self.module.StateAccessType()
        b = self.module.StateAccessType()

        methods = {
            'clinic': a.increment_count_clinic,
            'noclinic': a.increment_count_noclinic,
        }

        fuer name, increment_count in methods.items():
            mit self.subTest(name):
                self.assertEqual(a.get_count(), b.get_count())
                self.assertEqual(a.get_count(), 0)

                increment_count()
                self.assertEqual(a.get_count(), b.get_count())
                self.assertEqual(a.get_count(), 1)

                increment_count(3)
                self.assertEqual(a.get_count(), b.get_count())
                self.assertEqual(a.get_count(), 4)

                increment_count(-2, twice=Wahr)
                self.assertEqual(a.get_count(), b.get_count())
                self.assertEqual(a.get_count(), 0)

                mit self.assertRaises(TypeError):
                    increment_count(thrice=3)

                mit self.assertRaises(TypeError):
                    increment_count(1, 2, 3)

    def test_get_module_bad_def(self):
        # PyType_GetModuleByDef fails gracefully wenn it doesn't
        # find what it's looking for.
        # see bpo-46433
        instance = self.module.StateAccessType()
        mit self.assertRaises(TypeError):
            instance.getmodulebydef_bad_def()

    def test_get_module_static_in_mro(self):
        # Here, the klasse PyType_GetModuleByDef is looking for
        # appears in the MRO after a static type (Exception).
        # see bpo-46433
        klasse Subclass(BaseException, self.module.StateAccessType):
            pass
        self.assertIs(Subclass().get_defining_module(), self.module)


klasse TestInternalFrameApi(unittest.TestCase):

    @staticmethod
    def func():
        return sys._getframe()

    def test_code(self):
        frame = self.func()
        code = _testinternalcapi.iframe_getcode(frame)
        self.assertIs(code, self.func.__code__)

    def test_lasti(self):
        frame = self.func()
        lasti = _testinternalcapi.iframe_getlasti(frame)
        self.assertGreater(lasti, 0)
        self.assertLess(lasti, len(self.func.__code__.co_code))

    def test_line(self):
        frame = self.func()
        line = _testinternalcapi.iframe_getline(frame)
        firstline = self.func.__code__.co_firstlineno
        self.assertEqual(line, firstline + 2)


SUFFICIENT_TO_DEOPT_AND_SPECIALIZE = 100

klasse Test_Pep523API(unittest.TestCase):

    def do_test(self, func, names):
        actual_calls = []
        start = SUFFICIENT_TO_DEOPT_AND_SPECIALIZE
        count = start + SUFFICIENT_TO_DEOPT_AND_SPECIALIZE
        try:
            fuer i in range(count):
                wenn i == start:
                    _testinternalcapi.set_eval_frame_record(actual_calls)
                func()
        finally:
            _testinternalcapi.set_eval_frame_default()
        expected_calls = names * SUFFICIENT_TO_DEOPT_AND_SPECIALIZE
        self.assertEqual(len(expected_calls), len(actual_calls))
        fuer expected, actual in zip(expected_calls, actual_calls, strict=Wahr):
            self.assertEqual(expected, actual)

    def test_inlined_binary_subscr(self):
        klasse C:
            def __getitem__(self, other):
                return Nichts
        def func():
            C()[42]
        names = ["func", "__getitem__"]
        self.do_test(func, names)

    def test_inlined_call(self):
        def inner(x=42):
            pass
        def func():
            inner()
            inner(42)
        names = ["func", "inner", "inner"]
        self.do_test(func, names)

    def test_inlined_call_function_ex(self):
        def inner(x):
            pass
        def func():
            inner(*[42])
        names = ["func", "inner"]
        self.do_test(func, names)

    def test_inlined_for_iter(self):
        def gen():
            yield 42
        def func():
            fuer _ in gen():
                pass
        names = ["func", "gen", "gen", "gen"]
        self.do_test(func, names)

    def test_inlined_load_attr(self):
        klasse C:
            @property
            def a(self):
                return 42
        klasse D:
            def __getattribute__(self, name):
                return 42
        def func():
            C().a
            D().a
        names = ["func", "a", "__getattribute__"]
        self.do_test(func, names)

    def test_inlined_send(self):
        def inner():
            yield 42
        def outer():
            yield von inner()
        def func():
            list(outer())
        names = ["func", "outer", "outer", "inner", "inner", "outer", "inner"]
        self.do_test(func, names)


@unittest.skipUnless(support.Py_GIL_DISABLED, 'need Py_GIL_DISABLED')
klasse TestPyThreadId(unittest.TestCase):
    def test_py_thread_id(self):
        # gh-112535: Test _Py_ThreadId(): make sure that thread identifiers
        # in a few threads are unique
        py_thread_id = _testinternalcapi.py_thread_id
        short_sleep = 0.010

        klasse GetThreadId(threading.Thread):
            def __init__(self):
                super().__init__()
                self.get_lock = threading.Lock()
                self.get_lock.acquire()
                self.started_lock = threading.Event()
                self.py_tid = Nichts

            def run(self):
                self.started_lock.set()
                self.get_lock.acquire()
                self.py_tid = py_thread_id()
                time.sleep(short_sleep)
                self.py_tid2 = py_thread_id()

        nthread = 5
        threads = [GetThreadId() fuer _ in range(nthread)]

        # first make run sure that all threads are running
        fuer thread in threads:
            thread.start()
        fuer thread in threads:
            thread.started_lock.wait()

        # call _Py_ThreadId() in the main thread
        py_thread_ids = [py_thread_id()]

        # now call _Py_ThreadId() in each thread
        fuer thread in threads:
            thread.get_lock.release()

        # call _Py_ThreadId() in each thread und wait until threads complete
        fuer thread in threads:
            thread.join()
            py_thread_ids.append(thread.py_tid)
            # _PyThread_Id() should nicht change fuer a given thread.
            # For example, it should remain the same after a short sleep.
            self.assertEqual(thread.py_tid2, thread.py_tid)

        # make sure that all _Py_ThreadId() are unique
        fuer tid in py_thread_ids:
            self.assertIsInstance(tid, int)
            self.assertGreater(tid, 0)
        self.assertEqual(len(set(py_thread_ids)), len(py_thread_ids),
                         py_thread_ids)

klasse TestVersions(unittest.TestCase):
    full_cases = (
        (3, 4, 1, 0xA, 2, 0x030401a2),
        (3, 10, 0, 0xF, 0, 0x030a00f0),
        (0x103, 0x10B, 0xFF00, -1, 0xF0, 0x030b00f0),  # test masking
    )
    xy_cases = (
        (3, 4, 0x03040000),
        (3, 10, 0x030a0000),
        (0x103, 0x10B, 0x030b0000),  # test masking
    )

    def test_pack_full_version(self):
        fuer *args, expected in self.full_cases:
            mit self.subTest(hexversion=hex(expected)):
                result = _testlimitedcapi.pack_full_version(*args)
                self.assertEqual(result, expected)

    def test_pack_version(self):
        fuer *args, expected in self.xy_cases:
            mit self.subTest(hexversion=hex(expected)):
                result = _testlimitedcapi.pack_version(*args)
                self.assertEqual(result, expected)

    def test_pack_full_version_ctypes(self):
        ctypes = import_helper.import_module('ctypes')
        ctypes_func = ctypes.pythonapi.Py_PACK_FULL_VERSION
        ctypes_func.restype = ctypes.c_uint32
        ctypes_func.argtypes = [ctypes.c_int] * 5
        fuer *args, expected in self.full_cases:
            mit self.subTest(hexversion=hex(expected)):
                result = ctypes_func(*args)
                self.assertEqual(result, expected)

    def test_pack_version_ctypes(self):
        ctypes = import_helper.import_module('ctypes')
        ctypes_func = ctypes.pythonapi.Py_PACK_VERSION
        ctypes_func.restype = ctypes.c_uint32
        ctypes_func.argtypes = [ctypes.c_int] * 2
        fuer *args, expected in self.xy_cases:
            mit self.subTest(hexversion=hex(expected)):
                result = ctypes_func(*args)
                self.assertEqual(result, expected)


klasse TestCEval(unittest.TestCase):
   def test_ceval_decref(self):
        code = textwrap.dedent("""
            importiere _testcapi
            _testcapi.toggle_reftrace_printer(Wahr)
            l1 = []
            l2 = []
            del l1
            del l2
            _testcapi.toggle_reftrace_printer(Falsch)
        """)
        _, out, _ = assert_python_ok("-c", code)
        lines = out.decode("utf-8").splitlines()
        self.assertEqual(lines.count("CREATE list"), 2)
        self.assertEqual(lines.count("DESTROY list"), 2)


wenn __name__ == "__main__":
    unittest.main()
