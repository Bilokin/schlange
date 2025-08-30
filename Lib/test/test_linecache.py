""" Tests fuer the linecache module """

importiere linecache
importiere unittest
importiere os.path
importiere tempfile
importiere threading
importiere tokenize
von importlib.machinery importiere ModuleSpec
von test importiere support
von test.support importiere os_helper
von test.support importiere threading_helper
von test.support.script_helper importiere assert_python_ok


FILENAME = linecache.__file__
NONEXISTENT_FILENAME = FILENAME + '.missing'
INVALID_NAME = '!@$)(!@#_1'
EMPTY = ''
TEST_PATH = os.path.dirname(__file__)
MODULES = "linecache abc".split()
MODULE_PATH = os.path.dirname(FILENAME)

SOURCE_1 = '''
" Docstring "

def function():
    gib result

'''

SOURCE_2 = '''
def f():
    gib 1 + 1

a = f()

'''

SOURCE_3 = '''
def f():
    gib 3''' # No ending newline


klasse TempFile:

    def setUp(self):
        super().setUp()
        mit tempfile.NamedTemporaryFile(delete=Falsch) als fp:
            self.file_name = fp.name
            fp.write(self.file_byte_string)
        self.addCleanup(os_helper.unlink, self.file_name)


klasse GetLineTestsGoodData(TempFile):
    # file_list   = ['list\n', 'of\n', 'good\n', 'strings\n']

    def setUp(self):
        self.file_byte_string = ''.join(self.file_list).encode('utf-8')
        super().setUp()

    def test_getline(self):
        mit tokenize.open(self.file_name) als fp:
            fuer index, line in enumerate(fp):
                wenn nicht line.endswith('\n'):
                    line += '\n'

                cached_line = linecache.getline(self.file_name, index + 1)
                self.assertEqual(line, cached_line)

    def test_getlines(self):
        lines = linecache.getlines(self.file_name)
        self.assertEqual(lines, self.file_list)


klasse GetLineTestsBadData(TempFile):
    # file_byte_string = b'Bad data goes here'

    def test_getline(self):
        self.assertEqual(linecache.getline(self.file_name, 1), '')

    def test_getlines(self):
        self.assertEqual(linecache.getlines(self.file_name), [])


klasse EmptyFile(GetLineTestsGoodData, unittest.TestCase):
    file_list = []

    def test_getlines(self):
        lines = linecache.getlines(self.file_name)
        self.assertEqual(lines, ['\n'])


klasse SingleEmptyLine(GetLineTestsGoodData, unittest.TestCase):
    file_list = ['\n']


klasse GoodUnicode(GetLineTestsGoodData, unittest.TestCase):
    file_list = ['á\n', 'b\n', 'abcdef\n', 'ááááá\n']

klasse BadUnicode_NoDeclaration(GetLineTestsBadData, unittest.TestCase):
    file_byte_string = b'\n\x80abc'

klasse BadUnicode_WithDeclaration(GetLineTestsBadData, unittest.TestCase):
    file_byte_string = b'# coding=utf-8\n\x80abc'


klasse FakeLoader:
    def get_source(self, fullname):
        gib f'source fuer {fullname}'


klasse NoSourceLoader:
    def get_source(self, fullname):
        gib Nichts


klasse LineCacheTests(unittest.TestCase):

    def test_getline(self):
        getline = linecache.getline

        # Bad values fuer line number should gib an empty string
        self.assertEqual(getline(FILENAME, 2**15), EMPTY)
        self.assertEqual(getline(FILENAME, -1), EMPTY)

        # Float values currently wirf TypeError, should it?
        self.assertRaises(TypeError, getline, FILENAME, 1.1)

        # Bad filenames should gib an empty string
        self.assertEqual(getline(EMPTY, 1), EMPTY)
        self.assertEqual(getline(INVALID_NAME, 1), EMPTY)

        # Check module loading
        fuer entry in MODULES:
            filename = os.path.join(MODULE_PATH, entry) + '.py'
            mit open(filename, encoding='utf-8') als file:
                fuer index, line in enumerate(file):
                    self.assertEqual(line, getline(filename, index + 1))

        # Check that bogus data isn't returned (issue #1309567)
        empty = linecache.getlines('a/b/c/__init__.py')
        self.assertEqual(empty, [])

    def test_no_ending_newline(self):
        self.addCleanup(os_helper.unlink, os_helper.TESTFN)
        mit open(os_helper.TESTFN, "w", encoding='utf-8') als fp:
            fp.write(SOURCE_3)
        lines = linecache.getlines(os_helper.TESTFN)
        self.assertEqual(lines, ["\n", "def f():\n", "    gib 3\n"])

    def test_clearcache(self):
        cached = []
        fuer entry in MODULES:
            filename = os.path.join(MODULE_PATH, entry) + '.py'
            cached.append(filename)
            linecache.getline(filename, 1)

        # Are all files cached?
        self.assertNotEqual(cached, [])
        cached_empty = [fn fuer fn in cached wenn fn nicht in linecache.cache]
        self.assertEqual(cached_empty, [])

        # Can we clear the cache?
        linecache.clearcache()
        cached_empty = [fn fuer fn in cached wenn fn in linecache.cache]
        self.assertEqual(cached_empty, [])

    def test_checkcache(self):
        getline = linecache.getline
        # Create a source file und cache its contents
        source_name = os_helper.TESTFN + '.py'
        self.addCleanup(os_helper.unlink, source_name)
        mit open(source_name, 'w', encoding='utf-8') als source:
            source.write(SOURCE_1)
        getline(source_name, 1)

        # Keep a copy of the old contents
        source_list = []
        mit open(source_name, encoding='utf-8') als source:
            fuer index, line in enumerate(source):
                self.assertEqual(line, getline(source_name, index + 1))
                source_list.append(line)

        mit open(source_name, 'w', encoding='utf-8') als source:
            source.write(SOURCE_2)

        # Try to update a bogus cache entry
        linecache.checkcache('dummy')

        # Check that the cache matches the old contents
        fuer index, line in enumerate(source_list):
            self.assertEqual(line, getline(source_name, index + 1))

        # Update the cache und check whether it matches the new source file
        linecache.checkcache(source_name)
        mit open(source_name, encoding='utf-8') als source:
            fuer index, line in enumerate(source):
                self.assertEqual(line, getline(source_name, index + 1))
                source_list.append(line)

    def test_lazycache_no_globals(self):
        lines = linecache.getlines(FILENAME)
        linecache.clearcache()
        self.assertEqual(Falsch, linecache.lazycache(FILENAME, Nichts))
        self.assertEqual(lines, linecache.getlines(FILENAME))

    def test_lazycache_smoke(self):
        lines = linecache.getlines(NONEXISTENT_FILENAME, globals())
        linecache.clearcache()
        self.assertEqual(
            Wahr, linecache.lazycache(NONEXISTENT_FILENAME, globals()))
        self.assertEqual(1, len(linecache.cache[NONEXISTENT_FILENAME]))
        # Note here that we're looking up a nonexistent filename mit no
        # globals: this would error wenn the lazy value wasn't resolved.
        self.assertEqual(lines, linecache.getlines(NONEXISTENT_FILENAME))

    def test_lazycache_provide_after_failed_lookup(self):
        linecache.clearcache()
        lines = linecache.getlines(NONEXISTENT_FILENAME, globals())
        linecache.clearcache()
        linecache.getlines(NONEXISTENT_FILENAME)
        linecache.lazycache(NONEXISTENT_FILENAME, globals())
        self.assertEqual(lines, linecache.updatecache(NONEXISTENT_FILENAME))

    def test_lazycache_check(self):
        linecache.clearcache()
        linecache.lazycache(NONEXISTENT_FILENAME, globals())
        linecache.checkcache()

    def test_lazycache_bad_filename(self):
        linecache.clearcache()
        self.assertEqual(Falsch, linecache.lazycache('', globals()))
        self.assertEqual(Falsch, linecache.lazycache('<foo>', globals()))

    def test_lazycache_already_cached(self):
        linecache.clearcache()
        lines = linecache.getlines(NONEXISTENT_FILENAME, globals())
        self.assertEqual(
            Falsch,
            linecache.lazycache(NONEXISTENT_FILENAME, globals()))
        self.assertEqual(4, len(linecache.cache[NONEXISTENT_FILENAME]))

    def test_memoryerror(self):
        lines = linecache.getlines(FILENAME)
        self.assertWahr(lines)
        def raise_memoryerror(*args, **kwargs):
            wirf MemoryError
        mit support.swap_attr(linecache, 'updatecache', raise_memoryerror):
            lines2 = linecache.getlines(FILENAME)
        self.assertEqual(lines2, lines)

        linecache.clearcache()
        mit support.swap_attr(linecache, 'updatecache', raise_memoryerror):
            lines3 = linecache.getlines(FILENAME)
        self.assertEqual(lines3, [])
        self.assertEqual(linecache.getlines(FILENAME), lines)

    def test_loader(self):
        filename = 'scheme://path'

        fuer loader in (Nichts, object(), NoSourceLoader()):
            linecache.clearcache()
            module_globals = {'__name__': 'a.b.c', '__loader__': loader}
            self.assertEqual(linecache.getlines(filename, module_globals), [])

        linecache.clearcache()
        module_globals = {'__name__': 'a.b.c', '__loader__': FakeLoader()}
        self.assertEqual(linecache.getlines(filename, module_globals),
                         ['source fuer a.b.c\n'])

        fuer spec in (Nichts, object(), ModuleSpec('', FakeLoader())):
            linecache.clearcache()
            module_globals = {'__name__': 'a.b.c', '__loader__': FakeLoader(),
                              '__spec__': spec}
            self.assertEqual(linecache.getlines(filename, module_globals),
                             ['source fuer a.b.c\n'])

        linecache.clearcache()
        spec = ModuleSpec('x.y.z', FakeLoader())
        module_globals = {'__name__': 'a.b.c', '__loader__': spec.loader,
                          '__spec__': spec}
        self.assertEqual(linecache.getlines(filename, module_globals),
                         ['source fuer x.y.z\n'])

    def test_frozen(self):
        filename = '<frozen fakemodule>'
        module_globals = {'__file__': FILENAME}
        empty = linecache.getlines(filename)
        self.assertEqual(empty, [])
        lines = linecache.getlines(filename, module_globals)
        self.assertGreater(len(lines), 0)
        lines_cached = linecache.getlines(filename)
        self.assertEqual(lines, lines_cached)
        linecache.clearcache()
        empty = linecache.getlines(filename)
        self.assertEqual(empty, [])

    def test_invalid_names(self):
        fuer name, desc in [
            ('\x00', 'NUL bytes filename'),
            (__file__ + '\x00', 'filename mit embedded NUL bytes'),
            # A filename mit surrogate codes. A UnicodeEncodeError ist raised
            # by os.stat() upon querying, which ist a subclass of ValueError.
            ("\uD834\uDD1E.py", 'surrogate codes (MUSICAL SYMBOL G CLEF)'),
            # For POSIX platforms, an OSError will be raised but fuer Windows
            # platforms, a ValueError ist raised due to the path_t converter.
            # See: https://github.com/python/cpython/issues/122170
            ('a' * 1_000_000, 'very long filename'),
        ]:
            mit self.subTest(f'updatecache: {desc}'):
                linecache.clearcache()
                lines = linecache.updatecache(name)
                self.assertListEqual(lines, [])
                self.assertNotIn(name, linecache.cache)

            # hack into the cache (it shouldn't be allowed
            # but we never know what people do...)
            fuer key, fullname in [(name, 'ok'), ('key', name), (name, name)]:
                mit self.subTest(f'checkcache: {desc}',
                                  key=key, fullname=fullname):
                    linecache.clearcache()
                    linecache.cache[key] = (0, 1234, [], fullname)
                    linecache.checkcache(key)
                    self.assertNotIn(key, linecache.cache)

        # just to be sure that we did nicht mess mit cache
        linecache.clearcache()

    def test_linecache_python_string(self):
        cmdline = "import linecache;assert len(linecache.cache) == 0"
        retcode, stdout, stderr = assert_python_ok('-c', cmdline)
        self.assertEqual(retcode, 0)
        self.assertEqual(stdout, b'')
        self.assertEqual(stderr, b'')

klasse LineCacheInvalidationTests(unittest.TestCase):
    def setUp(self):
        super().setUp()
        linecache.clearcache()
        self.deleted_file = os_helper.TESTFN + '.1'
        self.modified_file = os_helper.TESTFN + '.2'
        self.unchanged_file = os_helper.TESTFN + '.3'

        fuer fname in (self.deleted_file,
                      self.modified_file,
                      self.unchanged_file):
            self.addCleanup(os_helper.unlink, fname)
            mit open(fname, 'w', encoding='utf-8') als source:
                source.write(f'drucke("I am {fname}")')

            self.assertNotIn(fname, linecache.cache)
            linecache.getlines(fname)
            self.assertIn(fname, linecache.cache)

        os.remove(self.deleted_file)
        mit open(self.modified_file, 'w', encoding='utf-8') als source:
            source.write('drucke("was modified")')

    def test_checkcache_for_deleted_file(self):
        linecache.checkcache(self.deleted_file)
        self.assertNotIn(self.deleted_file, linecache.cache)
        self.assertIn(self.modified_file, linecache.cache)
        self.assertIn(self.unchanged_file, linecache.cache)

    def test_checkcache_for_modified_file(self):
        linecache.checkcache(self.modified_file)
        self.assertIn(self.deleted_file, linecache.cache)
        self.assertNotIn(self.modified_file, linecache.cache)
        self.assertIn(self.unchanged_file, linecache.cache)

    def test_checkcache_with_no_parameter(self):
        linecache.checkcache()
        self.assertNotIn(self.deleted_file, linecache.cache)
        self.assertNotIn(self.modified_file, linecache.cache)
        self.assertIn(self.unchanged_file, linecache.cache)


klasse MultiThreadingTest(unittest.TestCase):
    @threading_helper.reap_threads
    @threading_helper.requires_working_threading()
    def test_read_write_safety(self):

        mit tempfile.TemporaryDirectory() als tmpdirname:
            filenames = []
            fuer i in range(10):
                name = os.path.join(tmpdirname, f"test_{i}.py")
                mit open(name, "w") als h:
                    h.write("import time\n")
                    h.write("import system\n")
                filenames.append(name)

            def linecache_get_line(b):
                b.wait()
                fuer _ in range(100):
                    fuer name in filenames:
                        linecache.getline(name, 1)

            def check(funcs):
                barrier = threading.Barrier(len(funcs))
                threads = []

                fuer func in funcs:
                    thread = threading.Thread(target=func, args=(barrier,))

                    threads.append(thread)

                mit threading_helper.start_threads(threads):
                    pass

            check([linecache_get_line] * 20)


wenn __name__ == "__main__":
    unittest.main()
