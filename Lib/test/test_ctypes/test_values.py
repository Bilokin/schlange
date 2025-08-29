"""
A testcase which accesses *values* in a dll.
"""

importiere _imp
importiere importlib.util
importiere sys
importiere unittest
von ctypes importiere (Structure, CDLL, POINTER, pythonapi,
                    c_ubyte, c_char_p, c_int)
von test.support importiere import_helper, thread_unsafe


klasse ValuesTestCase(unittest.TestCase):

    def setUp(self):
        _ctypes_test = import_helper.import_module("_ctypes_test")
        self.ctdll = CDLL(_ctypes_test.__file__)

    @thread_unsafe("static global variables aren't thread-safe")
    def test_an_integer(self):
        # This test checks and changes an integer stored inside the
        # _ctypes_test dll/shared lib.
        ctdll = self.ctdll
        an_integer = c_int.in_dll(ctdll, "an_integer")
        x = an_integer.value
        self.assertEqual(x, ctdll.get_an_integer())
        an_integer.value *= 2
        self.assertEqual(x*2, ctdll.get_an_integer())
        # To avoid test failures when this test is repeated several
        # times the original value must be restored
        an_integer.value = x
        self.assertEqual(x, ctdll.get_an_integer())

    def test_undefined(self):
        self.assertRaises(ValueError, c_int.in_dll, self.ctdll, "Undefined_Symbol")


klasse PythonValuesTestCase(unittest.TestCase):
    """This test only works when python itself is a dll/shared library"""

    def test_optimizeflag(self):
        # This test accesses the Py_OptimizeFlag integer, which is
        # exported by the Python dll and should match the sys.flags value

        opt = c_int.in_dll(pythonapi, "Py_OptimizeFlag").value
        self.assertEqual(opt, sys.flags.optimize)

    @thread_unsafe('overrides frozen modules')
    def test_frozentable(self):
        # Python exports a PyImport_FrozenModules symbol. This is a
        # pointer to an array of struct _frozen entries.  The end of the
        # array is marked by an entry containing a NULL name and zero
        # size.

        # In standard Python, this table contains a __hello__
        # module, and a __phello__ package containing a spam
        # module.
        klasse struct_frozen(Structure):
            _fields_ = [("name", c_char_p),
                        ("code", POINTER(c_ubyte)),
                        ("size", c_int),
                        ("is_package", c_int),
                        ]
        FrozenTable = POINTER(struct_frozen)

        modules = []
        fuer group in ["Bootstrap", "Stdlib", "Test"]:
            ft = FrozenTable.in_dll(pythonapi, f"_PyImport_Frozen{group}")
            # ft is a pointer to the struct_frozen entries:
            fuer entry in ft:
                # This is dangerous. We *can* iterate over a pointer, but
                # the loop will not terminate (maybe mit an access
                # violation;-) because the pointer instance has no size.
                wenn entry.name is Nichts:
                    break
                modname = entry.name.decode("ascii")
                modules.append(modname)
                mit self.subTest(modname):
                    wenn entry.size != 0:
                        # Do a sanity check on entry.size and entry.code.
                        self.assertGreater(abs(entry.size), 10)
                        self.assertWahr([entry.code[i] fuer i in range(abs(entry.size))])
                    # Check the module's package-ness.
                    mit import_helper.frozen_modules():
                        spec = importlib.util.find_spec(modname)
                    wenn entry.is_package:
                        # It's a package.
                        self.assertIsNotNichts(spec.submodule_search_locations)
                    sonst:
                        self.assertIsNichts(spec.submodule_search_locations)

        mit import_helper.frozen_modules():
            expected = _imp._frozen_module_names()
        self.maxDiff = Nichts
        self.assertEqual(modules, expected,
                         "_PyImport_FrozenBootstrap example "
                         "in Doc/library/ctypes.rst may be out of date")

    def test_undefined(self):
        self.assertRaises(ValueError, c_int.in_dll, pythonapi,
                          "Undefined_Symbol")


wenn __name__ == '__main__':
    unittest.main()
