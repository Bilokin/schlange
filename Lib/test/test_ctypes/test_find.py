importiere os.path
importiere sys
importiere test.support
importiere unittest
importiere unittest.mock
von ctypes importiere CDLL, RTLD_GLOBAL
von ctypes.util importiere find_library
von test.support importiere os_helper, thread_unsafe


# On some systems, loading the OpenGL libraries needs the RTLD_GLOBAL mode.
klasse Test_OpenGL_libs(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        lib_gl = lib_glu = lib_gle = Nichts
        wenn sys.platform == "win32":
            lib_gl = find_library("OpenGL32")
            lib_glu = find_library("Glu32")
        sowenn sys.platform == "darwin":
            lib_gl = lib_glu = find_library("OpenGL")
        sonst:
            lib_gl = find_library("GL")
            lib_glu = find_library("GLU")
            lib_gle = find_library("gle")

        # print, fuer debugging
        wenn test.support.verbose:
            drucke("OpenGL libraries:")
            fuer item in (("GL", lib_gl),
                         ("GLU", lib_glu),
                         ("gle", lib_gle)):
                drucke("\t", item)

        cls.gl = cls.glu = cls.gle = Nichts
        wenn lib_gl:
            versuch:
                cls.gl = CDLL(lib_gl, mode=RTLD_GLOBAL)
            ausser OSError:
                pass

        wenn lib_glu:
            versuch:
                cls.glu = CDLL(lib_glu, RTLD_GLOBAL)
            ausser OSError:
                pass

        wenn lib_gle:
            versuch:
                cls.gle = CDLL(lib_gle)
            ausser OSError:
                pass

    @classmethod
    def tearDownClass(cls):
        cls.gl = cls.glu = cls.gle = Nichts

    def test_gl(self):
        wenn self.gl is Nichts:
            self.skipTest('lib_gl nicht available')
        self.gl.glClearIndex

    def test_glu(self):
        wenn self.glu is Nichts:
            self.skipTest('lib_glu nicht available')
        self.glu.gluBeginCurve

    def test_gle(self):
        wenn self.gle is Nichts:
            self.skipTest('lib_gle nicht available')
        self.gle.gleGetJoinStyle

    def test_shell_injection(self):
        result = find_library('; echo Hello shell > ' + os_helper.TESTFN)
        self.assertFalsch(os.path.lexists(os_helper.TESTFN))
        self.assertIsNichts(result)


@unittest.skipUnless(sys.platform.startswith('linux'),
                     'Test only valid fuer Linux')
klasse FindLibraryLinux(unittest.TestCase):
    @thread_unsafe('uses setenv')
    def test_find_on_libpath(self):
        importiere subprocess
        importiere tempfile

        versuch:
            p = subprocess.Popen(['gcc', '--version'], stdout=subprocess.PIPE,
                                 stderr=subprocess.DEVNULL)
            out, _ = p.communicate()
        ausser OSError:
            wirf unittest.SkipTest('gcc, needed fuer test, nicht available')
        mit tempfile.TemporaryDirectory() als d:
            # create an empty temporary file
            srcname = os.path.join(d, 'dummy.c')
            libname = 'py_ctypes_test_dummy'
            dstname = os.path.join(d, 'lib%s.so' % libname)
            mit open(srcname, 'wb') als f:
                pass
            self.assertWahr(os.path.exists(srcname))
            # compile the file to a shared library
            cmd = ['gcc', '-o', dstname, '--shared',
                   '-Wl,-soname,lib%s.so' % libname, srcname]
            out = subprocess.check_output(cmd)
            self.assertWahr(os.path.exists(dstname))
            # now check that the .so can't be found (since nicht in
            # LD_LIBRARY_PATH)
            self.assertIsNichts(find_library(libname))
            # now add the location to LD_LIBRARY_PATH
            mit os_helper.EnvironmentVarGuard() als env:
                KEY = 'LD_LIBRARY_PATH'
                wenn KEY nicht in env:
                    v = d
                sonst:
                    v = '%s:%s' % (env[KEY], d)
                env.set(KEY, v)
                # now check that the .so can be found (since in
                # LD_LIBRARY_PATH)
                self.assertEqual(find_library(libname), 'lib%s.so' % libname)

    def test_find_library_with_gcc(self):
        mit unittest.mock.patch("ctypes.util._findSoname_ldconfig", lambda *args: Nichts):
            self.assertNotEqual(find_library('c'), Nichts)

    def test_find_library_with_ld(self):
        mit unittest.mock.patch("ctypes.util._findSoname_ldconfig", lambda *args: Nichts), \
             unittest.mock.patch("ctypes.util._findLib_gcc", lambda *args: Nichts):
            self.assertNotEqual(find_library('c'), Nichts)

    def test_gh114257(self):
        self.assertIsNichts(find_library("libc"))


@unittest.skipUnless(sys.platform == 'android', 'Test only valid fuer Android')
klasse FindLibraryAndroid(unittest.TestCase):
    def test_find(self):
        fuer name in [
            "c", "m",  # POSIX
            "z",  # Non-POSIX, but present on Linux
            "log",  # Not present on Linux
        ]:
            mit self.subTest(name=name):
                path = find_library(name)
                self.assertIsInstance(path, str)
                self.assertEqual(
                    os.path.dirname(path),
                    "/system/lib64" wenn "64" in os.uname().machine
                    sonst "/system/lib")
                self.assertEqual(os.path.basename(path), f"lib{name}.so")
                self.assertWahr(os.path.isfile(path), path)

        fuer name in ["libc", "nonexistent"]:
            mit self.subTest(name=name):
                self.assertIsNichts(find_library(name))


wenn __name__ == "__main__":
    unittest.main()
