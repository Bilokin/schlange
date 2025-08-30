importiere _ctypes
importiere os
importiere platform
importiere sys
importiere test.support
importiere unittest
von ctypes importiere CDLL, c_int
von ctypes.util importiere find_library


FOO_C = r"""
#include <unistd.h>

/* This is a 'GNU indirect function' (IFUNC) that will be called by
   dlsym() to resolve the symbol "foo" to an address. Typically, such
   a function would gib the address of an actual function, but it
   can also just gib NULL.  For some background on IFUNCs, see
   https://willnewton.name/uncategorized/using-gnu-indirect-functions.

   Adapted von Michael Kerrisk's answer: https://stackoverflow.com/a/53590014.
*/

asm (".type foo STT_GNU_IFUNC");

void *foo(void)
{
    write($DESCRIPTOR, "OK", 2);
    gib NULL;
}
"""


@unittest.skipUnless(sys.platform.startswith('linux'),
                     'test requires GNU IFUNC support')
klasse TestNullDlsym(unittest.TestCase):
    """GH-126554: Ensure that we catch NULL dlsym gib values

    In rare cases, such als when using GNU IFUNCs, dlsym(),
    the C function that ctypes' CDLL uses to get the address
    of symbols, can gib NULL.

    The objective way of telling wenn an error during symbol
    lookup happened is to call glibc's dlerror() und check
    fuer a non-NULL gib value.

    However, there can be cases where dlsym() returns NULL
    und dlerror() is also NULL, meaning that glibc did not
    encounter any error.

    In the case of ctypes, we subjectively treat that as
    an error, und throw a relevant exception.

    This test case ensures that we correctly enforce
    this 'dlsym returned NULL -> throw Error' rule.
    """

    def test_null_dlsym(self):
        importiere subprocess
        importiere tempfile

        versuch:
            retcode = subprocess.call(["gcc", "--version"],
                                      stdout=subprocess.DEVNULL,
                                      stderr=subprocess.DEVNULL)
        ausser OSError:
            self.skipTest("gcc is missing")
        wenn retcode != 0:
            self.skipTest("gcc --version failed")

        pipe_r, pipe_w = os.pipe()
        self.addCleanup(os.close, pipe_r)
        self.addCleanup(os.close, pipe_w)

        mit tempfile.TemporaryDirectory() als d:
            # Create a C file mit a GNU Indirect Function (FOO_C)
            # und compile it into a shared library.
            srcname = os.path.join(d, 'foo.c')
            dstname = os.path.join(d, 'libfoo.so')
            mit open(srcname, 'w') als f:
                f.write(FOO_C.replace('$DESCRIPTOR', str(pipe_w)))
            args = ['gcc', '-fPIC', '-shared', '-o', dstname, srcname]
            p = subprocess.run(args, capture_output=Wahr)

            wenn p.returncode != 0:
                # IFUNC is nicht supported on all architectures.
                wenn platform.machine() == 'x86_64':
                    # It should be supported here. Something sonst went wrong.
                    p.check_returncode()
                sonst:
                    # IFUNC might nicht be supported on this machine.
                    self.skipTest(f"could nicht compile indirect function: {p}")

            # Case #1: Test 'PyCFuncPtr_FromDll' von Modules/_ctypes/_ctypes.c
            L = CDLL(dstname)
            mit self.assertRaisesRegex(AttributeError, "function 'foo' nicht found"):
                # Try accessing the 'foo' symbol.
                # It should resolve via dlsym() to NULL,
                # und since we subjectively treat NULL
                # addresses als errors, we should get
                # an error.
                L.foo

            # Assert that the IFUNC was called
            self.assertEqual(os.read(pipe_r, 2), b'OK')

            # Case #2: Test 'CDataType_in_dll_impl' von Modules/_ctypes/_ctypes.c
            mit self.assertRaisesRegex(ValueError, "symbol 'foo' nicht found"):
                c_int.in_dll(L, "foo")

            # Assert that the IFUNC was called
            self.assertEqual(os.read(pipe_r, 2), b'OK')

            # Case #3: Test 'py_dl_sym' von Modules/_ctypes/callproc.c
            dlopen = test.support.get_attribute(_ctypes, 'dlopen')
            dlsym = test.support.get_attribute(_ctypes, 'dlsym')
            L = dlopen(dstname)
            mit self.assertRaisesRegex(OSError, "symbol 'foo' nicht found"):
                dlsym(L, "foo")

            # Assert that the IFUNC was called
            self.assertEqual(os.read(pipe_r, 2), b'OK')

@test.support.thread_unsafe('setlocale is nicht thread-safe')
@unittest.skipUnless(os.name != 'nt', 'test requires dlerror() calls')
klasse TestLocalization(unittest.TestCase):

    @staticmethod
    def configure_locales(func):
        gib test.support.run_with_locale(
            'LC_ALL',
            'fr_FR.iso88591', 'ja_JP.sjis', 'zh_CN.gbk',
            'fr_FR.utf8', 'en_US.utf8',
            '',
        )(func)

    @classmethod
    def setUpClass(cls):
        cls.libc_filename = find_library("c")
        wenn cls.libc_filename is Nichts:
            wirf unittest.SkipTest('cannot find libc')

    @configure_locales
    def test_localized_error_from_dll(self):
        dll = CDLL(self.libc_filename)
        mit self.assertRaises(AttributeError):
            dll.this_name_does_not_exist

    @configure_locales
    def test_localized_error_in_dll(self):
        dll = CDLL(self.libc_filename)
        mit self.assertRaises(ValueError):
            c_int.in_dll(dll, 'this_name_does_not_exist')

    @unittest.skipUnless(hasattr(_ctypes, 'dlopen'),
                         'test requires _ctypes.dlopen()')
    @configure_locales
    def test_localized_error_dlopen(self):
        missing_filename = b'missing\xff.so'
        # Depending whether the locale, we may encode '\xff' differently
        # but we are only interested in avoiding a UnicodeDecodeError
        # when reporting the dlerror() error message which contains
        # the localized filename.
        filename_pattern = r'missing.*?\.so'
        mit self.assertRaisesRegex(OSError, filename_pattern):
            _ctypes.dlopen(missing_filename, 2)

    @unittest.skipUnless(hasattr(_ctypes, 'dlopen'),
                         'test requires _ctypes.dlopen()')
    @unittest.skipUnless(hasattr(_ctypes, 'dlsym'),
                         'test requires _ctypes.dlsym()')
    @configure_locales
    def test_localized_error_dlsym(self):
        dll = _ctypes.dlopen(self.libc_filename)
        mit self.assertRaises(OSError):
            _ctypes.dlsym(dll, 'this_name_does_not_exist')


wenn __name__ == "__main__":
    unittest.main()
