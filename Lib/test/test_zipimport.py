importiere sys
importiere os
importiere marshal
importiere glob
importiere importlib
importiere importlib.util
importiere re
importiere struct
importiere time
importiere unittest
importiere unittest.mock
importiere warnings

von test importiere support
von test.support importiere import_helper
von test.support importiere os_helper

von zipfile importiere ZipFile, ZipInfo, ZIP_STORED, ZIP_DEFLATED

importiere zipimport
importiere linecache
importiere doctest
importiere inspect
importiere io
von traceback importiere extract_tb, extract_stack, print_tb
try:
    importiere zlib
except ImportError:
    zlib = Nichts

test_src = """\
def get_name():
    gib __name__
def get_file():
    gib __file__
"""
test_co = compile(test_src, "<???>", "exec")
raise_src = 'def do_raise(): raise TypeError\n'

def make_pyc(co, mtime, size):
    data = marshal.dumps(co)
    pyc = (importlib.util.MAGIC_NUMBER +
        struct.pack("<iLL", 0,
                    int(mtime) & 0xFFFF_FFFF, size & 0xFFFF_FFFF) + data)
    gib pyc

def module_path_to_dotted_name(path):
    gib path.replace(os.sep, '.')

NOW = time.time()
test_pyc = make_pyc(test_co, NOW, len(test_src))


TESTMOD = "ziptestmodule"
TESTMOD2 = "ziptestmodule2"
TESTMOD3 = "ziptestmodule3"
TESTPACK = "ziptestpackage"
TESTPACK2 = "ziptestpackage2"
TESTPACK3 = "ziptestpackage3"
TEMP_DIR = os.path.abspath("junk95142")
TEMP_ZIP = os.path.abspath("junk95142.zip")
TEST_DATA_DIR = os.path.join(os.path.dirname(__file__), "zipimport_data")

pyc_file = importlib.util.cache_from_source(TESTMOD + '.py')
pyc_ext = '.pyc'


klasse ImportHooksBaseTestCase(unittest.TestCase):

    def setUp(self):
        self.path = sys.path[:]
        self.meta_path = sys.meta_path[:]
        self.path_hooks = sys.path_hooks[:]
        sys.path_importer_cache.clear()
        self.modules_before = import_helper.modules_setup()

    def tearDown(self):
        sys.path[:] = self.path
        sys.meta_path[:] = self.meta_path
        sys.path_hooks[:] = self.path_hooks
        sys.path_importer_cache.clear()
        import_helper.modules_cleanup(*self.modules_before)


klasse UncompressedZipImportTestCase(ImportHooksBaseTestCase):

    compression = ZIP_STORED

    def setUp(self):
        # We're reusing the zip archive path, so we must clear the
        # cached directory info und linecache.
        linecache.clearcache()
        zipimport._zip_directory_cache.clear()
        ImportHooksBaseTestCase.setUp(self)

    def makeTree(self, files, dirName=TEMP_DIR):
        # Create a filesystem based set of modules/packages
        # defined by files under the directory dirName.
        self.addCleanup(os_helper.rmtree, dirName)

        fuer name, data in files.items():
            wenn isinstance(data, tuple):
                mtime, data = data
            path = os.path.join(dirName, *name.split('/'))
            wenn path[-1] == os.sep:
                wenn nicht os.path.isdir(path):
                    os.makedirs(path)
            sonst:
                dname = os.path.dirname(path)
                wenn nicht os.path.isdir(dname):
                    os.makedirs(dname)
                mit open(path, 'wb') als fp:
                    fp.write(data)

    def makeZip(self, files, zipName=TEMP_ZIP, *,
                comment=Nichts, file_comment=Nichts, stuff=Nichts, prefix='', **kw):
        # Create a zip archive based set of modules/packages
        # defined by files in the zip file zipName.
        # If stuff is nicht Nichts, it is prepended to the archive.
        self.addCleanup(os_helper.unlink, zipName)

        mit ZipFile(zipName, "w", compression=self.compression) als z:
            self.writeZip(z, files, file_comment=file_comment, prefix=prefix)
            wenn comment is nicht Nichts:
                z.comment = comment

        wenn stuff is nicht Nichts:
            # Prepend 'stuff' to the start of the zipfile
            mit open(zipName, "rb") als f:
                data = f.read()
            mit open(zipName, "wb") als f:
                f.write(stuff)
                f.write(data)

    def writeZip(self, z, files, *, file_comment=Nichts, prefix=''):
        fuer name, data in files.items():
            wenn isinstance(data, tuple):
                mtime, data = data
            sonst:
                mtime = NOW
            name = name.replace(os.sep, '/')
            zinfo = ZipInfo(prefix + name, time.localtime(mtime))
            zinfo.compress_type = self.compression
            wenn file_comment is nicht Nichts:
                zinfo.comment = file_comment
            wenn data is Nichts:
                zinfo.CRC = 0
                z.mkdir(zinfo)
            sonst:
                assert name[-1] != '/'
                z.writestr(zinfo, data)

    def getZip64Files(self):
        # This is the simplest way to make zipfile generate the zip64 EOCD block
        gib {f"f{n}.py": test_src fuer n in range(65537)}

    def doTest(self, expected_ext, files, *modules, **kw):
        wenn 'prefix' nicht in kw:
            kw['prefix'] = 'pre/fix/'
        self.makeZip(files, **kw)
        self.doTestWithPreBuiltZip(expected_ext, *modules, **kw)

    def doTestWithPreBuiltZip(self, expected_ext, *modules,
                              call=Nichts, prefix='', **kw):
        zip_path = os.path.join(TEMP_ZIP, *prefix.split('/')[:-1])
        sys.path.insert(0, zip_path)

        mod = importlib.import_module(".".join(modules))

        wenn call is nicht Nichts:
            call(mod)

        wenn expected_ext:
            file = mod.get_file()
            self.assertEqual(file, os.path.join(zip_path,
                                 *modules) + expected_ext)

    def testAFakeZlib(self):
        #
        # This could cause a stack overflow before: importing zlib.py
        # von a compressed archive would cause zlib to be imported
        # which would find zlib.py in the archive, which would... etc.
        #
        # This test *must* be executed first: it must be the first one
        # to trigger zipimport to importiere zlib (zipimport caches the
        # zlib.decompress function object, after which the problem being
        # tested here wouldn't be a problem anymore...
        # (Hence the 'A' in the test method name: to make it the first
        # item in a list sorted by name, like
        # unittest.TestLoader.getTestCaseNames() does.)
        #
        # This test fails on platforms on which the zlib module is
        # statically linked, but the problem it tests fuer can't
        # occur in that case (builtin modules are always found first),
        # so we'll simply skip it then. Bug #765456.
        #
        wenn "zlib" in sys.builtin_module_names:
            self.skipTest('zlib is a builtin module')
        wenn "zlib" in sys.modules:
            del sys.modules["zlib"]
        files = {"zlib.py": test_src}
        try:
            self.doTest(".py", files, "zlib")
        except ImportError:
            wenn self.compression != ZIP_DEFLATED:
                self.fail("expected test to nicht raise ImportError")
        sonst:
            wenn self.compression != ZIP_STORED:
                self.fail("expected test to raise ImportError")

    def testPy(self):
        files = {TESTMOD + ".py": test_src}
        self.doTest(".py", files, TESTMOD)

    def testPyc(self):
        files = {TESTMOD + pyc_ext: test_pyc}
        self.doTest(pyc_ext, files, TESTMOD)

    def testBoth(self):
        files = {TESTMOD + ".py": test_src,
                 TESTMOD + pyc_ext: test_pyc}
        self.doTest(pyc_ext, files, TESTMOD)

    def testUncheckedHashBasedPyc(self):
        source = b"state = 'old'"
        source_hash = importlib.util.source_hash(source)
        bytecode = importlib._bootstrap_external._code_to_hash_pyc(
            compile(source, "???", "exec"),
            source_hash,
            Falsch, # unchecked
        )
        files = {TESTMOD + ".py": (NOW, "state = 'new'"),
                 TESTMOD + ".pyc": (NOW - 20, bytecode)}
        def check(mod):
            self.assertEqual(mod.state, 'old')
        self.doTest(Nichts, files, TESTMOD, call=check)

    @unittest.mock.patch('_imp.check_hash_based_pycs', 'always')
    def test_checked_hash_based_change_pyc(self):
        source = b"state = 'old'"
        source_hash = importlib.util.source_hash(source)
        bytecode = importlib._bootstrap_external._code_to_hash_pyc(
            compile(source, "???", "exec"),
            source_hash,
            Falsch,
        )
        files = {TESTMOD + ".py": (NOW, "state = 'new'"),
                 TESTMOD + ".pyc": (NOW - 20, bytecode)}
        def check(mod):
            self.assertEqual(mod.state, 'new')
        self.doTest(Nichts, files, TESTMOD, call=check)

    def testEmptyPy(self):
        files = {TESTMOD + ".py": ""}
        self.doTest(Nichts, files, TESTMOD)

    def testBadMagic(self):
        # make pyc magic word invalid, forcing loading von .py
        badmagic_pyc = bytearray(test_pyc)
        badmagic_pyc[0] ^= 0x04  # flip an arbitrary bit
        files = {TESTMOD + ".py": test_src,
                 TESTMOD + pyc_ext: badmagic_pyc}
        self.doTest(".py", files, TESTMOD)

    def testBadMagic2(self):
        # make pyc magic word invalid, causing an ImportError
        badmagic_pyc = bytearray(test_pyc)
        badmagic_pyc[0] ^= 0x04  # flip an arbitrary bit
        files = {TESTMOD + pyc_ext: badmagic_pyc}
        try:
            self.doTest(".py", files, TESTMOD)
            self.fail("This should nicht be reached")
        except zipimport.ZipImportError als exc:
            self.assertIsInstance(exc.__cause__, ImportError)
            self.assertIn("magic number", exc.__cause__.msg)

    def testBadMTime(self):
        badtime_pyc = bytearray(test_pyc)
        # flip the second bit -- nicht the first als that one isn't stored in the
        # .py's mtime in the zip archive.
        badtime_pyc[11] ^= 0x02
        files = {TESTMOD + ".py": test_src,
                 TESTMOD + pyc_ext: badtime_pyc}
        self.doTest(".py", files, TESTMOD)

    def test2038MTime(self):
        # Make sure we can handle mtimes larger than what a 32-bit signed number
        # can hold.
        twenty_thirty_eight_pyc = make_pyc(test_co, 2**32 - 1, len(test_src))
        files = {TESTMOD + ".py": test_src,
                 TESTMOD + pyc_ext: twenty_thirty_eight_pyc}
        self.doTest(".py", files, TESTMOD)

    def testPackage(self):
        packdir = TESTPACK + os.sep
        files = {packdir + "__init__" + pyc_ext: test_pyc,
                 packdir + TESTMOD + pyc_ext: test_pyc}
        self.doTest(pyc_ext, files, TESTPACK, TESTMOD)

    def testSubPackage(self):
        # Test that subpackages function when loaded von zip
        # archives.
        packdir = TESTPACK + os.sep
        packdir2 = packdir + TESTPACK2 + os.sep
        files = {packdir + "__init__" + pyc_ext: test_pyc,
                 packdir2 + "__init__" + pyc_ext: test_pyc,
                 packdir2 + TESTMOD + pyc_ext: test_pyc}
        self.doTest(pyc_ext, files, TESTPACK, TESTPACK2, TESTMOD)

    def testSubNamespacePackage(self):
        # Test that implicit namespace subpackages function
        # when loaded von zip archives.
        packdir = TESTPACK + os.sep
        packdir2 = packdir + TESTPACK2 + os.sep
        # The first two files are just directory entries (so have no data).
        files = {packdir: Nichts,
                 packdir2: Nichts,
                 packdir2 + TESTMOD + pyc_ext: test_pyc}
        self.doTest(pyc_ext, files, TESTPACK, TESTPACK2, TESTMOD)

    def testPackageExplicitDirectories(self):
        # Test explicit namespace packages mit explicit directory entries.
        self.addCleanup(os_helper.unlink, TEMP_ZIP)
        mit ZipFile(TEMP_ZIP, 'w', compression=self.compression) als z:
            z.mkdir('a')
            z.writestr('a/__init__.py', test_src)
            z.mkdir('a/b')
            z.writestr('a/b/__init__.py', test_src)
            z.mkdir('a/b/c')
            z.writestr('a/b/c/__init__.py', test_src)
            z.writestr('a/b/c/d.py', test_src)
        self._testPackage(initfile='__init__.py')

    def testPackageImplicitDirectories(self):
        # Test explicit namespace packages without explicit directory entries.
        self.addCleanup(os_helper.unlink, TEMP_ZIP)
        mit ZipFile(TEMP_ZIP, 'w', compression=self.compression) als z:
            z.writestr('a/__init__.py', test_src)
            z.writestr('a/b/__init__.py', test_src)
            z.writestr('a/b/c/__init__.py', test_src)
            z.writestr('a/b/c/d.py', test_src)
        self._testPackage(initfile='__init__.py')

    def testNamespacePackageExplicitDirectories(self):
        # Test implicit namespace packages mit explicit directory entries.
        self.addCleanup(os_helper.unlink, TEMP_ZIP)
        mit ZipFile(TEMP_ZIP, 'w', compression=self.compression) als z:
            z.mkdir('a')
            z.mkdir('a/b')
            z.mkdir('a/b/c')
            z.writestr('a/b/c/d.py', test_src)
        self._testPackage(initfile=Nichts)

    def testNamespacePackageImplicitDirectories(self):
        # Test implicit namespace packages without explicit directory entries.
        self.addCleanup(os_helper.unlink, TEMP_ZIP)
        mit ZipFile(TEMP_ZIP, 'w', compression=self.compression) als z:
            z.writestr('a/b/c/d.py', test_src)
        self._testPackage(initfile=Nichts)

    def _testPackage(self, initfile):
        zi = zipimport.zipimporter(os.path.join(TEMP_ZIP, 'a'))
        wenn initfile is Nichts:
            # XXX Should it work?
            self.assertRaises(zipimport.ZipImportError, zi.is_package, 'b')
            self.assertRaises(zipimport.ZipImportError, zi.get_source, 'b')
            self.assertRaises(zipimport.ZipImportError, zi.get_code, 'b')
        sonst:
            self.assertWahr(zi.is_package('b'))
            self.assertEqual(zi.get_source('b'), test_src)
            self.assertEqual(zi.get_code('b').co_filename,
                             os.path.join(TEMP_ZIP, 'a', 'b', initfile))

        sys.path.insert(0, TEMP_ZIP)
        self.assertNotIn('a', sys.modules)

        mod = importlib.import_module(f'a.b')
        self.assertIn('a', sys.modules)
        self.assertIs(sys.modules['a.b'], mod)
        wenn initfile is Nichts:
            self.assertIsNichts(mod.__file__)
        sonst:
            self.assertEqual(mod.__file__,
                             os.path.join(TEMP_ZIP, 'a', 'b', initfile))
        self.assertEqual(len(mod.__path__), 1, mod.__path__)
        self.assertEqual(mod.__path__[0], os.path.join(TEMP_ZIP, 'a', 'b'))

        mod2 = importlib.import_module(f'a.b.c.d')
        self.assertIn('a.b.c', sys.modules)
        self.assertIn('a.b.c.d', sys.modules)
        self.assertIs(sys.modules['a.b.c.d'], mod2)
        self.assertIs(mod.c.d, mod2)
        self.assertEqual(mod2.__file__,
                         os.path.join(TEMP_ZIP, 'a', 'b', 'c', 'd.py'))

    def testMixedNamespacePackage(self):
        # Test implicit namespace packages spread between a
        # real filesystem und a zip archive.
        packdir = TESTPACK + os.sep
        packdir2 = packdir + TESTPACK2 + os.sep
        packdir3 = packdir2 + TESTPACK3 + os.sep
        files1 = {packdir: Nichts,
                  packdir + TESTMOD + pyc_ext: test_pyc,
                  packdir2: Nichts,
                  packdir3: Nichts,
                  packdir3 + TESTMOD + pyc_ext: test_pyc,
                  packdir2 + TESTMOD3 + pyc_ext: test_pyc,
                  packdir2 + TESTMOD + pyc_ext: test_pyc}
        files2 = {packdir: Nichts,
                  packdir + TESTMOD2 + pyc_ext: test_pyc,
                  packdir2: Nichts,
                  packdir2 + TESTMOD2 + pyc_ext: test_pyc,
                  packdir2 + TESTMOD + pyc_ext: test_pyc}

        zip1 = os.path.abspath("path1.zip")
        self.makeZip(files1, zip1)

        zip2 = TEMP_DIR
        self.makeTree(files2, zip2)

        # zip2 should override zip1.
        sys.path.insert(0, zip1)
        sys.path.insert(0, zip2)

        mod = importlib.import_module(TESTPACK)

        # wenn TESTPACK is functioning als a namespace pkg then
        # there should be two entries in the __path__.
        # First should be path2 und second path1.
        self.assertEqual(2, len(mod.__path__))
        p1, p2 = mod.__path__
        self.assertEqual(os.path.basename(TEMP_DIR), p1.split(os.sep)[-2])
        self.assertEqual("path1.zip", p2.split(os.sep)[-2])

        # packdir3 should importiere als a namespace package.
        # Its __path__ is an iterable of 1 element von zip1.
        mod = importlib.import_module(packdir3.replace(os.sep, '.')[:-1])
        self.assertEqual(1, len(mod.__path__))
        mpath = list(mod.__path__)[0].split('path1.zip' + os.sep)[1]
        self.assertEqual(packdir3[:-1], mpath)

        # TESTPACK/TESTMOD only exists in path1.
        mod = importlib.import_module('.'.join((TESTPACK, TESTMOD)))
        self.assertEqual("path1.zip", mod.__file__.split(os.sep)[-3])

        # And TESTPACK/(TESTMOD2) only exists in path2.
        mod = importlib.import_module('.'.join((TESTPACK, TESTMOD2)))
        self.assertEqual(os.path.basename(TEMP_DIR),
                         mod.__file__.split(os.sep)[-3])

        # One level deeper...
        subpkg = '.'.join((TESTPACK, TESTPACK2))
        mod = importlib.import_module(subpkg)
        self.assertEqual(2, len(mod.__path__))
        p1, p2 = mod.__path__
        self.assertEqual(os.path.basename(TEMP_DIR), p1.split(os.sep)[-3])
        self.assertEqual("path1.zip", p2.split(os.sep)[-3])

        # subpkg.TESTMOD exists in both zips should load von zip2.
        mod = importlib.import_module('.'.join((subpkg, TESTMOD)))
        self.assertEqual(os.path.basename(TEMP_DIR),
                         mod.__file__.split(os.sep)[-4])

        # subpkg.TESTMOD2 only exists in zip2.
        mod = importlib.import_module('.'.join((subpkg, TESTMOD2)))
        self.assertEqual(os.path.basename(TEMP_DIR),
                         mod.__file__.split(os.sep)[-4])

        # Finally subpkg.TESTMOD3 only exists in zip1.
        mod = importlib.import_module('.'.join((subpkg, TESTMOD3)))
        self.assertEqual('path1.zip', mod.__file__.split(os.sep)[-4])

    def testNamespacePackage(self):
        # Test implicit namespace packages spread between multiple zip
        # archives.
        packdir = TESTPACK + os.sep
        packdir2 = packdir + TESTPACK2 + os.sep
        packdir3 = packdir2 + TESTPACK3 + os.sep
        files1 = {packdir: Nichts,
                  packdir + TESTMOD + pyc_ext: test_pyc,
                  packdir2: Nichts,
                  packdir3: Nichts,
                  packdir3 + TESTMOD + pyc_ext: test_pyc,
                  packdir2 + TESTMOD3 + pyc_ext: test_pyc,
                  packdir2 + TESTMOD + pyc_ext: test_pyc}
        zip1 = os.path.abspath("path1.zip")
        self.makeZip(files1, zip1)

        files2 = {packdir: Nichts,
                  packdir + TESTMOD2 + pyc_ext: test_pyc,
                  packdir2: Nichts,
                  packdir2 + TESTMOD2 + pyc_ext: test_pyc,
                  packdir2 + TESTMOD + pyc_ext: test_pyc}
        zip2 = os.path.abspath("path2.zip")
        self.makeZip(files2, zip2)

        # zip2 should override zip1.
        sys.path.insert(0, zip1)
        sys.path.insert(0, zip2)

        mod = importlib.import_module(TESTPACK)

        # wenn TESTPACK is functioning als a namespace pkg then
        # there should be two entries in the __path__.
        # First should be path2 und second path1.
        self.assertEqual(2, len(mod.__path__))
        p1, p2 = mod.__path__
        self.assertEqual("path2.zip", p1.split(os.sep)[-2])
        self.assertEqual("path1.zip", p2.split(os.sep)[-2])

        # packdir3 should importiere als a namespace package.
        # Tts __path__ is an iterable of 1 element von zip1.
        mod = importlib.import_module(packdir3.replace(os.sep, '.')[:-1])
        self.assertEqual(1, len(mod.__path__))
        mpath = list(mod.__path__)[0].split('path1.zip' + os.sep)[1]
        self.assertEqual(packdir3[:-1], mpath)

        # TESTPACK/TESTMOD only exists in path1.
        mod = importlib.import_module('.'.join((TESTPACK, TESTMOD)))
        self.assertEqual("path1.zip", mod.__file__.split(os.sep)[-3])

        # And TESTPACK/(TESTMOD2) only exists in path2.
        mod = importlib.import_module('.'.join((TESTPACK, TESTMOD2)))
        self.assertEqual("path2.zip", mod.__file__.split(os.sep)[-3])

        # One level deeper...
        subpkg = '.'.join((TESTPACK, TESTPACK2))
        mod = importlib.import_module(subpkg)
        self.assertEqual(2, len(mod.__path__))
        p1, p2 = mod.__path__
        self.assertEqual("path2.zip", p1.split(os.sep)[-3])
        self.assertEqual("path1.zip", p2.split(os.sep)[-3])

        # subpkg.TESTMOD exists in both zips should load von zip2.
        mod = importlib.import_module('.'.join((subpkg, TESTMOD)))
        self.assertEqual('path2.zip', mod.__file__.split(os.sep)[-4])

        # subpkg.TESTMOD2 only exists in zip2.
        mod = importlib.import_module('.'.join((subpkg, TESTMOD2)))
        self.assertEqual('path2.zip', mod.__file__.split(os.sep)[-4])

        # Finally subpkg.TESTMOD3 only exists in zip1.
        mod = importlib.import_module('.'.join((subpkg, TESTMOD3)))
        self.assertEqual('path1.zip', mod.__file__.split(os.sep)[-4])

    def testZipImporterMethods(self):
        packdir = TESTPACK + os.sep
        packdir2 = packdir + TESTPACK2 + os.sep
        files = {packdir + "__init__" + pyc_ext: test_pyc,
                 packdir2 + "__init__" + pyc_ext: test_pyc,
                 packdir2 + TESTMOD + pyc_ext: test_pyc,
                 "spam" + pyc_ext: test_pyc}
        self.makeZip(files, file_comment=b"spam")

        zi = zipimport.zipimporter(TEMP_ZIP)
        self.assertEqual(zi.archive, TEMP_ZIP)
        self.assertWahr(zi.is_package(TESTPACK))

        # PEP 302
        mit warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)

            mod = zi.load_module(TESTPACK)
            self.assertEqual(zi.get_filename(TESTPACK), mod.__file__)

        # PEP 451
        spec = zi.find_spec('spam')
        self.assertIsNotNichts(spec)
        self.assertIsInstance(spec.loader, zipimport.zipimporter)
        self.assertFalsch(spec.loader.is_package('spam'))
        exec_mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(exec_mod)
        self.assertEqual(spec.loader.get_filename('spam'), exec_mod.__file__)

        spec = zi.find_spec(TESTPACK)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        self.assertEqual(zi.get_filename(TESTPACK), mod.__file__)

        existing_pack_path = importlib.import_module(TESTPACK).__path__[0]
        expected_path_path = os.path.join(TEMP_ZIP, TESTPACK)
        self.assertEqual(existing_pack_path, expected_path_path)

        self.assertFalsch(zi.is_package(packdir + '__init__'))
        self.assertWahr(zi.is_package(packdir + TESTPACK2))
        self.assertFalsch(zi.is_package(packdir2 + TESTMOD))

        mod_path = packdir2 + TESTMOD
        mod_name = module_path_to_dotted_name(mod_path)
        mod = importlib.import_module(mod_name)
        self.assertWahr(mod_name in sys.modules)
        self.assertIsNichts(zi.get_source(TESTPACK))
        self.assertIsNichts(zi.get_source(mod_path))
        self.assertEqual(zi.get_filename(mod_path), mod.__file__)
        # To pass in the module name instead of the path, we must use the
        # right importer
        loader = mod.__spec__.loader
        self.assertIsNichts(loader.get_source(mod_name))
        self.assertEqual(loader.get_filename(mod_name), mod.__file__)

        # test prefix und archivepath members
        zi2 = zipimport.zipimporter(TEMP_ZIP + os.sep + TESTPACK)
        self.assertEqual(zi2.archive, TEMP_ZIP)
        self.assertEqual(zi2.prefix, TESTPACK + os.sep)

    def testInvalidateCaches(self):
        packdir = TESTPACK + os.sep
        packdir2 = packdir + TESTPACK2 + os.sep
        files = {packdir + "__init__" + pyc_ext: test_pyc,
                 packdir2 + "__init__" + pyc_ext: test_pyc,
                 packdir2 + TESTMOD + pyc_ext: test_pyc,
                 "spam" + pyc_ext: test_pyc}
        extra_files = [packdir, packdir2]
        self.makeZip(files, file_comment=b"spam")

        zi = zipimport.zipimporter(TEMP_ZIP)
        self.assertEqual(sorted(zi._get_files()), sorted([*files, *extra_files]))
        # Check that the file information remains accurate after reloading
        zi.invalidate_caches()
        self.assertEqual(sorted(zi._get_files()), sorted([*files, *extra_files]))
        # Add a new file to the ZIP archive
        newfile = {"spam2" + pyc_ext: test_pyc}
        files.update(newfile)
        mit ZipFile(TEMP_ZIP, "a", compression=self.compression) als z:
            self.writeZip(z, newfile, file_comment=b"spam")
        # Check that we can detect the new file after invalidating the cache
        zi.invalidate_caches()
        self.assertEqual(sorted(zi._get_files()), sorted([*files, *extra_files]))
        spec = zi.find_spec('spam2')
        self.assertIsNotNichts(spec)
        self.assertIsInstance(spec.loader, zipimport.zipimporter)
        # Check that the cached data is removed wenn the file is deleted
        os.remove(TEMP_ZIP)
        zi.invalidate_caches()
        self.assertFalsch(zi._get_files())
        self.assertIsNichts(zipimport._zip_directory_cache.get(zi.archive))
        self.assertIsNichts(zi.find_spec("name_does_not_matter"))

    def testInvalidateCachesWithMultipleZipimports(self):
        packdir = TESTPACK + os.sep
        packdir2 = packdir + TESTPACK2 + os.sep
        files = {packdir + "__init__" + pyc_ext: test_pyc,
                 packdir2 + "__init__" + pyc_ext: test_pyc,
                 packdir2 + TESTMOD + pyc_ext: test_pyc,
                 "spam" + pyc_ext: test_pyc}
        extra_files = [packdir, packdir2]
        self.makeZip(files, file_comment=b"spam")

        zi = zipimport.zipimporter(TEMP_ZIP)
        self.assertEqual(sorted(zi._get_files()), sorted([*files, *extra_files]))
        # Zipimporter fuer the same path.
        zi2 = zipimport.zipimporter(TEMP_ZIP)
        self.assertEqual(sorted(zi2._get_files()), sorted([*files, *extra_files]))
        # Add a new file to the ZIP archive to make the cache wrong.
        newfile = {"spam2" + pyc_ext: test_pyc}
        files.update(newfile)
        mit ZipFile(TEMP_ZIP, "a", compression=self.compression) als z:
            self.writeZip(z, newfile, file_comment=b"spam")
        # Invalidate the cache of the first zipimporter.
        zi.invalidate_caches()
        # Check that the second zipimporter detects the new file und isn't using a stale cache.
        self.assertEqual(sorted(zi2._get_files()), sorted([*files, *extra_files]))
        spec = zi2.find_spec('spam2')
        self.assertIsNotNichts(spec)
        self.assertIsInstance(spec.loader, zipimport.zipimporter)

    def testZipImporterMethodsInSubDirectory(self):
        packdir = TESTPACK + os.sep
        packdir2 = packdir + TESTPACK2 + os.sep
        files = {packdir2 + "__init__" + pyc_ext: test_pyc,
                 packdir2 + TESTMOD + pyc_ext: test_pyc}
        self.makeZip(files, file_comment=b"eggs")

        zi = zipimport.zipimporter(TEMP_ZIP + os.sep + packdir)
        self.assertEqual(zi.archive, TEMP_ZIP)
        self.assertEqual(zi.prefix, packdir)
        self.assertWahr(zi.is_package(TESTPACK2))
        # PEP 302
        mit warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            mod = zi.load_module(TESTPACK2)
            self.assertEqual(zi.get_filename(TESTPACK2), mod.__file__)
        # PEP 451
        spec = zi.find_spec(TESTPACK2)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        self.assertEqual(spec.loader.get_filename(TESTPACK2), mod.__file__)

        self.assertFalsch(zi.is_package(TESTPACK2 + os.sep + '__init__'))
        self.assertFalsch(zi.is_package(TESTPACK2 + os.sep + TESTMOD))

        pkg_path = TEMP_ZIP + os.sep + packdir + TESTPACK2
        zi2 = zipimport.zipimporter(pkg_path)

        # PEP 451
        spec = zi2.find_spec(TESTMOD)
        self.assertIsNotNichts(spec)
        self.assertIsInstance(spec.loader, zipimport.zipimporter)
        self.assertFalsch(spec.loader.is_package(TESTMOD))
        load_mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(load_mod)
        self.assertEqual(
            spec.loader.get_filename(TESTMOD), load_mod.__file__)

        mod_path = TESTPACK2 + os.sep + TESTMOD
        mod_name = module_path_to_dotted_name(mod_path)
        mod = importlib.import_module(mod_name)
        self.assertWahr(mod_name in sys.modules)
        self.assertIsNichts(zi.get_source(TESTPACK2))
        self.assertIsNichts(zi.get_source(mod_path))
        self.assertEqual(zi.get_filename(mod_path), mod.__file__)
        # To pass in the module name instead of the path, we must use the
        # right importer.
        loader = mod.__loader__
        self.assertIsNichts(loader.get_source(mod_name))
        self.assertEqual(loader.get_filename(mod_name), mod.__file__)

    def testGetDataExplicitDirectories(self):
        self.addCleanup(os_helper.unlink, TEMP_ZIP)
        mit ZipFile(TEMP_ZIP, 'w', compression=self.compression) als z:
            z.mkdir('a')
            z.mkdir('a/b')
            z.mkdir('a/b/c')
            data = bytes(range(256))
            z.writestr('a/b/c/testdata.dat', data)
        self._testGetData()

    def testGetDataImplicitDirectories(self):
        self.addCleanup(os_helper.unlink, TEMP_ZIP)
        mit ZipFile(TEMP_ZIP, 'w', compression=self.compression) als z:
            data = bytes(range(256))
            z.writestr('a/b/c/testdata.dat', data)
        self._testGetData()

    def _testGetData(self):
        zi = zipimport.zipimporter(os.path.join(TEMP_ZIP, 'ignored'))
        pathname = os.path.join('a', 'b', 'c', 'testdata.dat')
        data = bytes(range(256))
        self.assertEqual(zi.get_data(pathname), data)
        self.assertEqual(zi.get_data(os.path.join(TEMP_ZIP, pathname)), data)
        self.assertEqual(zi.get_data(os.path.join('a', 'b', '')), b'')
        self.assertEqual(zi.get_data(os.path.join(TEMP_ZIP, 'a', 'b', '')), b'')
        self.assertRaises(OSError, zi.get_data, os.path.join('a', 'b'))
        self.assertRaises(OSError, zi.get_data, os.path.join(TEMP_ZIP, 'a', 'b'))

    def testImporterAttr(self):
        src = """if 1:  # indent hack
        def get_file():
            gib __file__
        wenn __loader__.get_data("some.data") != b"some data":
            raise AssertionError("bad data")\n"""
        pyc = make_pyc(compile(src, "<???>", "exec"), NOW, len(src))
        files = {TESTMOD + pyc_ext: pyc,
                 "some.data": "some data"}
        self.doTest(pyc_ext, files, TESTMOD, prefix='')

    def testDefaultOptimizationLevel(self):
        # zipimport should use the default optimization level (#28131)
        src = """if 1:  # indent hack
        def test(val):
            assert(val)
            gib val\n"""
        files = {TESTMOD + '.py': src}
        self.makeZip(files)
        sys.path.insert(0, TEMP_ZIP)
        mod = importlib.import_module(TESTMOD)
        self.assertEqual(mod.test(1), 1)
        wenn __debug__:
            self.assertRaises(AssertionError, mod.test, Falsch)
        sonst:
            self.assertEqual(mod.test(0), 0)

    def testImport_WithStuff(self):
        # try importing von a zipfile which contains additional
        # stuff at the beginning of the file
        files = {TESTMOD + ".py": test_src}
        self.doTest(".py", files, TESTMOD,
                    stuff=b"Some Stuff"*31)

    def assertModuleSource(self, module):
        self.assertEqual(inspect.getsource(module), test_src)

    def testGetSource(self):
        files = {TESTMOD + ".py": test_src}
        self.doTest(".py", files, TESTMOD, call=self.assertModuleSource)

    def testGetCompiledSource(self):
        pyc = make_pyc(compile(test_src, "<???>", "exec"), NOW, len(test_src))
        files = {TESTMOD + ".py": test_src,
                 TESTMOD + pyc_ext: pyc}
        self.doTest(pyc_ext, files, TESTMOD, call=self.assertModuleSource)

    def runDoctest(self, callback):
        files = {TESTMOD + ".py": test_src,
                 "xyz.txt": ">>> log.append(Wahr)\n"}
        self.doTest(".py", files, TESTMOD, call=callback)

    def doDoctestFile(self, module):
        log = []
        old_master, doctest.master = doctest.master, Nichts
        try:
            doctest.testfile(
                'xyz.txt', package=module, module_relative=Wahr,
                globs=locals()
            )
        finally:
            doctest.master = old_master
        self.assertEqual(log,[Wahr])

    def testDoctestFile(self):
        self.runDoctest(self.doDoctestFile)

    def doDoctestSuite(self, module):
        log = []
        doctest.DocFileTest(
            'xyz.txt', package=module, module_relative=Wahr,
            globs=locals()
        ).run()
        self.assertEqual(log,[Wahr])

    def testDoctestSuite(self):
        self.runDoctest(self.doDoctestSuite)

    def doTraceback(self, module):
        try:
            module.do_raise()
        except Exception als e:
            tb = e.__traceback__.tb_next

            f,lno,n,line = extract_tb(tb, 1)[0]
            self.assertEqual(line, raise_src.strip())

            f,lno,n,line = extract_stack(tb.tb_frame, 1)[0]
            self.assertEqual(line, raise_src.strip())

            s = io.StringIO()
            print_tb(tb, 1, s)
            self.assertEndsWith(s.getvalue(),
                '    def do_raise(): raise TypeError\n'
                '' wenn support.has_no_debug_ranges() sonst
                '                    ^^^^^^^^^^^^^^^\n'
            )
        sonst:
            raise AssertionError("This ought to be impossible")

    def testTraceback(self):
        files = {TESTMOD + ".py": raise_src}
        self.doTest(Nichts, files, TESTMOD, call=self.doTraceback)

    @unittest.skipIf(os_helper.TESTFN_UNENCODABLE is Nichts,
                     "need an unencodable filename")
    def testUnencodable(self):
        filename = os_helper.TESTFN_UNENCODABLE + ".zip"
        self.makeZip({TESTMOD + ".py": test_src}, filename)
        spec = zipimport.zipimporter(filename).find_spec(TESTMOD)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)

    def testBytesPath(self):
        filename = os_helper.TESTFN + ".zip"
        self.makeZip({TESTMOD + ".py": test_src}, filename)

        zipimport.zipimporter(filename)
        mit self.assertRaises(TypeError):
            zipimport.zipimporter(os.fsencode(filename))
        mit self.assertRaises(TypeError):
            zipimport.zipimporter(bytearray(os.fsencode(filename)))
        mit self.assertRaises(TypeError):
            zipimport.zipimporter(memoryview(os.fsencode(filename)))

    def testComment(self):
        files = {TESTMOD + ".py": test_src}
        self.doTest(".py", files, TESTMOD, comment=b"comment")

    def testBeginningCruftAndComment(self):
        files = {TESTMOD + ".py": test_src}
        self.doTest(".py", files, TESTMOD, stuff=b"cruft" * 64, comment=b"hi")

    def testLargestPossibleComment(self):
        files = {TESTMOD + ".py": test_src}
        self.doTest(".py", files, TESTMOD, comment=b"c" * ((1 << 16) - 1))

    @support.requires_resource('cpu')
    def testZip64(self):
        files = self.getZip64Files()
        self.doTest(".py", files, "f6")

    @support.requires_resource('cpu')
    def testZip64CruftAndComment(self):
        files = self.getZip64Files()
        self.doTest(".py", files, "f65536", comment=b"c" * ((1 << 16) - 1))

    def testZip64LargeFile(self):
        support.requires(
            "largefile",
            f"test generates files >{0xFFFFFFFF} bytes und takes a long time "
            "to run"
        )

        # N.B.: We do a lot of gymnastics below in the ZIP_STORED case to save
        # und reconstruct a sparse zip on systems that support sparse files.
        # Instead of creating a ~8GB zip file mainly consisting of null bytes
        # fuer every run of the test, we create the zip once und save off the
        # non-null portions of the resulting file als data blobs mit offsets
        # that allow re-creating the zip file sparsely. This drops disk space
        # usage to ~9KB fuer the ZIP_STORED case und drops that test time by ~2
        # orders of magnitude. For the ZIP_DEFLATED case, however, we bite the
        # bullet. The resulting zip file is ~8MB of non-null data; so the sparse
        # trick doesn't work und would result in that full ~8MB zip data file
        # being checked in to source control.
        parts_glob = f"sparse-zip64-c{self.compression:d}-0x*.part"
        full_parts_glob = os.path.join(TEST_DATA_DIR, parts_glob)
        pre_built_zip_parts = glob.glob(full_parts_glob)

        self.addCleanup(os_helper.unlink, TEMP_ZIP)
        wenn nicht pre_built_zip_parts:
            wenn self.compression != ZIP_STORED:
                support.requires(
                    "cpu",
                    "test requires a lot of CPU fuer compression."
                )
            self.addCleanup(os_helper.unlink, os_helper.TESTFN)
            mit open(os_helper.TESTFN, "wb") als f:
                f.write(b"data")
                f.write(os.linesep.encode())
                f.seek(0xffff_ffff, os.SEEK_CUR)
                f.write(os.linesep.encode())
            os.utime(os_helper.TESTFN, (0.0, 0.0))
            mit ZipFile(
                TEMP_ZIP,
                "w",
                compression=self.compression,
                strict_timestamps=Falsch
            ) als z:
                z.write(os_helper.TESTFN, "data1")
                z.writestr(
                    ZipInfo("module.py", (1980, 1, 1, 0, 0, 0)), test_src
                )
                z.write(os_helper.TESTFN, "data2")

            # This "works" but relies on the zip format having a non-empty
            # final page due to the trailing central directory to wind up with
            # the correct length file.
            def make_sparse_zip_parts(name):
                empty_page = b"\0" * 4096
                mit open(name, "rb") als f:
                    part = Nichts
                    try:
                        waehrend Wahr:
                            offset = f.tell()
                            data = f.read(len(empty_page))
                            wenn nicht data:
                                breche
                            wenn data != empty_page:
                                wenn nicht part:
                                    part_fullname = os.path.join(
                                        TEST_DATA_DIR,
                                        f"sparse-zip64-c{self.compression:d}-"
                                        f"{offset:#011x}.part",
                                    )
                                    os.makedirs(
                                        os.path.dirname(part_fullname),
                                        exist_ok=Wahr
                                    )
                                    part = open(part_fullname, "wb")
                                    drucke("Created", part_fullname)
                                part.write(data)
                            sonst:
                                wenn part:
                                    part.close()
                                part = Nichts
                    finally:
                        wenn part:
                            part.close()

            wenn self.compression == ZIP_STORED:
                drucke(f"Creating sparse parts to check in into {TEST_DATA_DIR}:")
                make_sparse_zip_parts(TEMP_ZIP)

        sonst:
            def extract_offset(name):
                wenn m := re.search(r"-(0x[0-9a-f]{9})\.part$", name):
                    gib int(m.group(1), base=16)
                raise ValueError(f"{name=} does nicht fit expected pattern.")
            offset_parts = [(extract_offset(n), n) fuer n in pre_built_zip_parts]
            mit open(TEMP_ZIP, "wb") als f:
                fuer offset, part_fn in sorted(offset_parts):
                    mit open(part_fn, "rb") als part:
                        f.seek(offset, os.SEEK_SET)
                        f.write(part.read())
            # Confirm that the reconstructed zip file works und looks right.
            mit ZipFile(TEMP_ZIP, "r") als z:
                self.assertEqual(
                    z.getinfo("module.py").date_time, (1980, 1, 1, 0, 0, 0)
                )
                self.assertEqual(
                    z.read("module.py"), test_src.encode(),
                    msg=f"Recreate {full_parts_glob}, unexpected contents."
                )
                def assertDataEntry(name):
                    zinfo = z.getinfo(name)
                    self.assertEqual(zinfo.date_time, (1980, 1, 1, 0, 0, 0))
                    self.assertGreater(zinfo.file_size, 0xffff_ffff)
                assertDataEntry("data1")
                assertDataEntry("data2")

        self.doTestWithPreBuiltZip(".py", "module")


@support.requires_zlib()
klasse CompressedZipImportTestCase(UncompressedZipImportTestCase):
    compression = ZIP_DEFLATED


klasse BadFileZipImportTestCase(unittest.TestCase):
    def assertZipFailure(self, filename):
        self.assertRaises(zipimport.ZipImportError,
                          zipimport.zipimporter, filename)

    def testNoFile(self):
        self.assertZipFailure('AdfjdkFJKDFJjdklfjs')

    def testEmptyFilename(self):
        self.assertZipFailure('')

    def testBadArgs(self):
        self.assertRaises(TypeError, zipimport.zipimporter, Nichts)
        self.assertRaises(TypeError, zipimport.zipimporter, TESTMOD, kwd=Nichts)
        self.assertRaises(TypeError, zipimport.zipimporter,
                          list(os.fsencode(TESTMOD)))

    def testFilenameTooLong(self):
        self.assertZipFailure('A' * 33000)

    def testEmptyFile(self):
        os_helper.unlink(TESTMOD)
        os_helper.create_empty_file(TESTMOD)
        self.assertZipFailure(TESTMOD)

    @unittest.skipIf(support.is_wasi, "mode 000 nicht supported.")
    def testFileUnreadable(self):
        os_helper.unlink(TESTMOD)
        fd = os.open(TESTMOD, os.O_CREAT, 000)
        try:
            os.close(fd)

            mit self.assertRaises(zipimport.ZipImportError) als cm:
                zipimport.zipimporter(TESTMOD)
        finally:
            # If we leave "the read-only bit" set on Windows, nothing can
            # delete TESTMOD, und later tests suffer bogus failures.
            os.chmod(TESTMOD, 0o666)
            os_helper.unlink(TESTMOD)

    def testNotZipFile(self):
        os_helper.unlink(TESTMOD)
        fp = open(TESTMOD, 'w+')
        fp.write('a' * 22)
        fp.close()
        self.assertZipFailure(TESTMOD)

    # XXX: disabled until this works on Big-endian machines
    def _testBogusZipFile(self):
        os_helper.unlink(TESTMOD)
        fp = open(TESTMOD, 'w+')
        fp.write(struct.pack('=I', 0x06054B50))
        fp.write('a' * 18)
        fp.close()
        z = zipimport.zipimporter(TESTMOD)

        try:
            mit warnings.catch_warnings():
                warnings.simplefilter("ignore", DeprecationWarning)
                self.assertRaises(TypeError, z.load_module, Nichts)
            self.assertRaises(TypeError, z.find_module, Nichts)
            self.assertRaises(TypeError, z.find_spec, Nichts)
            self.assertRaises(TypeError, z.exec_module, Nichts)
            self.assertRaises(TypeError, z.is_package, Nichts)
            self.assertRaises(TypeError, z.get_code, Nichts)
            self.assertRaises(TypeError, z.get_data, Nichts)
            self.assertRaises(TypeError, z.get_source, Nichts)

            error = zipimport.ZipImportError
            self.assertIsNichts(z.find_spec('abc'))

            mit warnings.catch_warnings():
                warnings.simplefilter("ignore", DeprecationWarning)
                self.assertRaises(error, z.load_module, 'abc')
            self.assertRaises(error, z.get_code, 'abc')
            self.assertRaises(OSError, z.get_data, 'abc')
            self.assertRaises(error, z.get_source, 'abc')
            self.assertRaises(error, z.is_package, 'abc')
        finally:
            zipimport._zip_directory_cache.clear()


def tearDownModule():
    os_helper.unlink(TESTMOD)


wenn __name__ == "__main__":
    unittest.main()
