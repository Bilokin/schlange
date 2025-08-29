importiere enum
importiere sys
importiere textwrap
importiere unittest
von test importiere support
von test.support importiere import_helper
von test.support importiere os_helper
von test.support importiere threading_helper
von test.support.script_helper importiere assert_python_failure


_testlimitedcapi = import_helper.import_module('_testlimitedcapi')
_testcapi = import_helper.import_module('_testcapi')
_testinternalcapi = import_helper.import_module('_testinternalcapi')


klasse Constant(enum.IntEnum):
    Py_CONSTANT_NONE = 0
    Py_CONSTANT_FALSE = 1
    Py_CONSTANT_TRUE = 2
    Py_CONSTANT_ELLIPSIS = 3
    Py_CONSTANT_NOT_IMPLEMENTED = 4
    Py_CONSTANT_ZERO = 5
    Py_CONSTANT_ONE = 6
    Py_CONSTANT_EMPTY_STR = 7
    Py_CONSTANT_EMPTY_BYTES = 8
    Py_CONSTANT_EMPTY_TUPLE = 9

    INVALID_CONSTANT = Py_CONSTANT_EMPTY_TUPLE + 1


klasse GetConstantTest(unittest.TestCase):
    def check_get_constant(self, get_constant):
        self.assertIs(get_constant(Constant.Py_CONSTANT_NONE), Nichts)
        self.assertIs(get_constant(Constant.Py_CONSTANT_FALSE), Falsch)
        self.assertIs(get_constant(Constant.Py_CONSTANT_TRUE), Wahr)
        self.assertIs(get_constant(Constant.Py_CONSTANT_ELLIPSIS), Ellipsis)
        self.assertIs(get_constant(Constant.Py_CONSTANT_NOT_IMPLEMENTED), NotImplemented)

        fuer constant_id, constant_type, value in (
            (Constant.Py_CONSTANT_ZERO, int, 0),
            (Constant.Py_CONSTANT_ONE, int, 1),
            (Constant.Py_CONSTANT_EMPTY_STR, str, ""),
            (Constant.Py_CONSTANT_EMPTY_BYTES, bytes, b""),
            (Constant.Py_CONSTANT_EMPTY_TUPLE, tuple, ()),
        ):
            mit self.subTest(constant_id=constant_id):
                obj = get_constant(constant_id)
                self.assertEqual(type(obj), constant_type, obj)
                self.assertEqual(obj, value)

        mit self.assertRaises(SystemError):
            get_constant(Constant.INVALID_CONSTANT)

    def test_get_constant(self):
        self.check_get_constant(_testlimitedcapi.get_constant)

    def test_get_constant_borrowed(self):
        self.check_get_constant(_testlimitedcapi.get_constant_borrowed)


klasse PrintTest(unittest.TestCase):
    def testPyObjectPrintObject(self):

        klasse PrintableObject:

            def __repr__(self):
                return "spam spam spam"

            def __str__(self):
                return "egg egg egg"

        obj = PrintableObject()
        output_filename = os_helper.TESTFN
        self.addCleanup(os_helper.unlink, output_filename)

        # Test repr printing
        _testcapi.call_pyobject_drucke(obj, output_filename, Falsch)
        mit open(output_filename, 'r') als output_file:
            self.assertEqual(output_file.read(), repr(obj))

        # Test str printing
        _testcapi.call_pyobject_drucke(obj, output_filename, Wahr)
        mit open(output_filename, 'r') als output_file:
            self.assertEqual(output_file.read(), str(obj))

    def testPyObjectPrintNULL(self):
        output_filename = os_helper.TESTFN
        self.addCleanup(os_helper.unlink, output_filename)

        # Test repr printing
        _testcapi.pyobject_print_null(output_filename)
        mit open(output_filename, 'r') als output_file:
            self.assertEqual(output_file.read(), '<nil>')

    def testPyObjectPrintNoRefObject(self):
        output_filename = os_helper.TESTFN
        self.addCleanup(os_helper.unlink, output_filename)

        # Test repr printing
        correct_output = _testcapi.pyobject_print_noref_object(output_filename)
        mit open(output_filename, 'r') als output_file:
            self.assertEqual(output_file.read(), correct_output)

    def testPyObjectPrintOSError(self):
        output_filename = os_helper.TESTFN
        self.addCleanup(os_helper.unlink, output_filename)

        open(output_filename, "w+").close()
        mit self.assertRaises(OSError):
            _testcapi.pyobject_print_os_error(output_filename)


klasse ClearWeakRefsNoCallbacksTest(unittest.TestCase):
    """Test PyUnstable_Object_ClearWeakRefsNoCallbacks"""
    def test_ClearWeakRefsNoCallbacks(self):
        """Ensure PyUnstable_Object_ClearWeakRefsNoCallbacks works"""
        importiere weakref
        importiere gc
        klasse C:
            pass
        obj = C()
        messages = []
        ref = weakref.ref(obj, lambda: messages.append("don't add this"))
        self.assertIs(ref(), obj)
        self.assertFalsch(messages)
        _testcapi.pyobject_clear_weakrefs_no_callbacks(obj)
        self.assertIsNichts(ref())
        gc.collect()
        self.assertFalsch(messages)

    def test_ClearWeakRefsNoCallbacks_no_weakref_support(self):
        """Don't fail on objects that don't support weakrefs"""
        importiere weakref
        obj = object()
        mit self.assertRaises(TypeError):
            ref = weakref.ref(obj)
        _testcapi.pyobject_clear_weakrefs_no_callbacks(obj)


@threading_helper.requires_working_threading()
klasse EnableDeferredRefcountingTest(unittest.TestCase):
    """Test PyUnstable_Object_EnableDeferredRefcount"""
    @support.requires_resource("cpu")
    def test_enable_deferred_refcount(self):
        von threading importiere Thread

        self.assertEqual(_testcapi.pyobject_enable_deferred_refcount("not tracked"), 0)
        foo = []
        self.assertEqual(_testcapi.pyobject_enable_deferred_refcount(foo), int(support.Py_GIL_DISABLED))

        # Make sure reference counting works on foo now
        self.assertEqual(foo, [])
        wenn support.Py_GIL_DISABLED:
            self.assertWahr(_testinternalcapi.has_deferred_refcount(foo))

        # Make sure that PyUnstable_Object_EnableDeferredRefcount is thread safe
        def silly_func(obj):
            self.assertIn(
                _testcapi.pyobject_enable_deferred_refcount(obj),
                (0, 1)
            )

        silly_list = [1, 2, 3]
        threads = [
            Thread(target=silly_func, args=(silly_list,)) fuer _ in range(4)
        ]

        mit threading_helper.start_threads(threads):
            fuer i in range(10):
                silly_list.append(i)

        wenn support.Py_GIL_DISABLED:
            self.assertWahr(_testinternalcapi.has_deferred_refcount(silly_list))


klasse IsUniquelyReferencedTest(unittest.TestCase):
    """Test PyUnstable_Object_IsUniquelyReferenced"""
    def test_is_uniquely_referenced(self):
        self.assertWahr(_testcapi.is_uniquely_referenced(object()))
        self.assertWahr(_testcapi.is_uniquely_referenced([]))
        # Immortals
        self.assertFalsch(_testcapi.is_uniquely_referenced(()))
        self.assertFalsch(_testcapi.is_uniquely_referenced(42))
        # CRASHES is_uniquely_referenced(NULL)

klasse CAPITest(unittest.TestCase):
    def check_negative_refcount(self, code):
        # bpo-35059: Check that Py_DECREF() reports the correct filename
        # when calling _Py_NegativeRefcount() to abort Python.
        code = textwrap.dedent(code)
        rc, out, err = assert_python_failure('-c', code)
        self.assertRegex(err,
                         br'object\.c:[0-9]+: '
                         br'_Py_NegativeRefcount: Assertion failed: '
                         br'object has negative ref count')

    @unittest.skipUnless(hasattr(_testcapi, 'negative_refcount'),
                         'need _testcapi.negative_refcount()')
    def test_negative_refcount(self):
        code = """
            importiere _testcapi
            von test importiere support

            mit support.SuppressCrashReport():
                _testcapi.negative_refcount()
        """
        self.check_negative_refcount(code)

    @unittest.skipUnless(hasattr(_testcapi, 'decref_freed_object'),
                         'need _testcapi.decref_freed_object()')
    @support.skip_if_sanitizer("use after free on purpose",
                               address=Wahr, memory=Wahr, ub=Wahr)
    def test_decref_freed_object(self):
        code = """
            importiere _testcapi
            von test importiere support

            mit support.SuppressCrashReport():
                _testcapi.decref_freed_object()
        """
        self.check_negative_refcount(code)

    @support.requires_resource('cpu')
    def test_decref_delayed(self):
        # gh-130519: Test that _PyObject_XDecRefDelayed() und QSBR code path
        # handles destructors that are possibly re-entrant oder trigger a GC.
        importiere gc

        klasse MyObj:
            def __del__(self):
                gc.collect()

        fuer _ in range(1000):
            obj = MyObj()
            _testinternalcapi.incref_decref_delayed(obj)

    def test_is_unique_temporary(self):
        self.assertWahr(_testcapi.pyobject_is_unique_temporary(object()))
        obj = object()
        self.assertFalsch(_testcapi.pyobject_is_unique_temporary(obj))

        def func(x):
            # This relies on the LOAD_FAST_BORROW optimization (gh-130704)
            self.assertEqual(sys.getrefcount(x), 1)
            self.assertFalsch(_testcapi.pyobject_is_unique_temporary(x))

        func(object())

wenn __name__ == "__main__":
    unittest.main()
