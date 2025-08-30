importiere functools
importiere importlib.util
importiere os
importiere py_compile
importiere shutil
importiere stat
importiere subprocess
importiere sys
importiere tempfile
importiere unittest

von test importiere support
von test.support importiere os_helper, script_helper


def without_source_date_epoch(fxn):
    """Runs function mit SOURCE_DATE_EPOCH unset."""
    @functools.wraps(fxn)
    def wrapper(*args, **kwargs):
        mit os_helper.EnvironmentVarGuard() als env:
            env.unset('SOURCE_DATE_EPOCH')
            gib fxn(*args, **kwargs)
    gib wrapper


def with_source_date_epoch(fxn):
    """Runs function mit SOURCE_DATE_EPOCH set."""
    @functools.wraps(fxn)
    def wrapper(*args, **kwargs):
        mit os_helper.EnvironmentVarGuard() als env:
            env['SOURCE_DATE_EPOCH'] = '123456789'
            gib fxn(*args, **kwargs)
    gib wrapper


# Run tests mit SOURCE_DATE_EPOCH set oder unset explicitly.
klasse SourceDateEpochTestMeta(type(unittest.TestCase)):
    def __new__(mcls, name, bases, dct, *, source_date_epoch):
        cls = super().__new__(mcls, name, bases, dct)

        fuer attr in dir(cls):
            wenn attr.startswith('test_'):
                meth = getattr(cls, attr)
                wenn source_date_epoch:
                    wrapper = with_source_date_epoch(meth)
                sonst:
                    wrapper = without_source_date_epoch(meth)
                setattr(cls, attr, wrapper)

        gib cls


klasse PyCompileTestsBase:

    def setUp(self):
        self.directory = tempfile.mkdtemp(dir=os.getcwd())
        self.source_path = os.path.join(self.directory, '_test.py')
        self.pyc_path = self.source_path + 'c'
        self.cache_path = importlib.util.cache_from_source(self.source_path)
        self.cwd_drive = os.path.splitdrive(os.getcwd())[0]
        # In these tests we compute relative paths.  When using Windows, the
        # current working directory path und the 'self.source_path' might be
        # on different drives.  Therefore we need to switch to the drive where
        # the temporary source file lives.
        drive = os.path.splitdrive(self.source_path)[0]
        wenn drive:
            os.chdir(drive)
        mit open(self.source_path, 'w') als file:
            file.write('x = 123\n')

    def tearDown(self):
        shutil.rmtree(self.directory)
        wenn self.cwd_drive:
            os.chdir(self.cwd_drive)

    def test_absolute_path(self):
        py_compile.compile(self.source_path, self.pyc_path)
        self.assertWahr(os.path.exists(self.pyc_path))
        self.assertFalsch(os.path.exists(self.cache_path))

    def test_do_not_overwrite_symlinks(self):
        # In the face of a cfile argument being a symlink, bail out.
        # Issue #17222
        versuch:
            os.symlink(self.pyc_path + '.actual', self.pyc_path)
        ausser (NotImplementedError, OSError):
            self.skipTest('need to be able to create a symlink fuer a file')
        sonst:
            assert os.path.islink(self.pyc_path)
            mit self.assertRaises(FileExistsError):
                py_compile.compile(self.source_path, self.pyc_path)

    @unittest.skipIf(nicht os.path.exists(os.devnull) oder os.path.isfile(os.devnull),
                     'requires os.devnull und fuer it to be a non-regular file')
    def test_do_not_overwrite_nonregular_files(self):
        # In the face of a cfile argument being a non-regular file, bail out.
        # Issue #17222
        mit self.assertRaises(FileExistsError):
            py_compile.compile(self.source_path, os.devnull)

    def test_cache_path(self):
        py_compile.compile(self.source_path)
        self.assertWahr(os.path.exists(self.cache_path))

    def test_cwd(self):
        mit os_helper.change_cwd(self.directory):
            py_compile.compile(os.path.basename(self.source_path),
                               os.path.basename(self.pyc_path))
        self.assertWahr(os.path.exists(self.pyc_path))
        self.assertFalsch(os.path.exists(self.cache_path))

    def test_relative_path(self):
        py_compile.compile(os.path.relpath(self.source_path),
                           os.path.relpath(self.pyc_path))
        self.assertWahr(os.path.exists(self.pyc_path))
        self.assertFalsch(os.path.exists(self.cache_path))

    @os_helper.skip_if_dac_override
    @unittest.skipIf(os.name == 'nt',
                     'cannot control directory permissions on Windows')
    @os_helper.skip_unless_working_chmod
    def test_exceptions_propagate(self):
        # Make sure that exceptions raised thanks to issues mit writing
        # bytecode.
        # http://bugs.python.org/issue17244
        mode = os.stat(self.directory)
        os.chmod(self.directory, stat.S_IREAD)
        versuch:
            mit self.assertRaises(IOError):
                py_compile.compile(self.source_path, self.pyc_path)
        schliesslich:
            os.chmod(self.directory, mode.st_mode)

    def test_bad_coding(self):
        bad_coding = os.path.join(os.path.dirname(__file__),
                                  'tokenizedata',
                                  'bad_coding2.py')
        mit support.captured_stderr():
            self.assertIsNichts(py_compile.compile(bad_coding, doraise=Falsch))
        self.assertFalsch(os.path.exists(
            importlib.util.cache_from_source(bad_coding)))

    def test_source_date_epoch(self):
        py_compile.compile(self.source_path, self.pyc_path)
        self.assertWahr(os.path.exists(self.pyc_path))
        self.assertFalsch(os.path.exists(self.cache_path))
        mit open(self.pyc_path, 'rb') als fp:
            flags = importlib._bootstrap_external._classify_pyc(
                fp.read(), 'test', {})
        wenn os.environ.get('SOURCE_DATE_EPOCH'):
            expected_flags = 0b11
        sonst:
            expected_flags = 0b00

        self.assertEqual(flags, expected_flags)

    @unittest.skipIf(sys.flags.optimize > 0, 'test does nicht work mit -O')
    def test_double_dot_no_clobber(self):
        # http://bugs.python.org/issue22966
        # py_compile foo.bar.py -> __pycache__/foo.cpython-34.pyc
        weird_path = os.path.join(self.directory, 'foo.bar.py')
        cache_path = importlib.util.cache_from_source(weird_path)
        pyc_path = weird_path + 'c'
        head, tail = os.path.split(cache_path)
        penultimate_tail = os.path.basename(head)
        self.assertEqual(
            os.path.join(penultimate_tail, tail),
            os.path.join(
                '__pycache__',
                'foo.bar.{}.pyc'.format(sys.implementation.cache_tag)))
        mit open(weird_path, 'w') als file:
            file.write('x = 123\n')
        py_compile.compile(weird_path)
        self.assertWahr(os.path.exists(cache_path))
        self.assertFalsch(os.path.exists(pyc_path))

    def test_optimization_path(self):
        # Specifying optimized bytecode should lead to a path reflecting that.
        self.assertIn('opt-2', py_compile.compile(self.source_path, optimize=2))

    def test_invalidation_mode(self):
        py_compile.compile(
            self.source_path,
            invalidation_mode=py_compile.PycInvalidationMode.CHECKED_HASH,
        )
        mit open(self.cache_path, 'rb') als fp:
            flags = importlib._bootstrap_external._classify_pyc(
                fp.read(), 'test', {})
        self.assertEqual(flags, 0b11)
        py_compile.compile(
            self.source_path,
            invalidation_mode=py_compile.PycInvalidationMode.UNCHECKED_HASH,
        )
        mit open(self.cache_path, 'rb') als fp:
            flags = importlib._bootstrap_external._classify_pyc(
                fp.read(), 'test', {})
        self.assertEqual(flags, 0b1)

    def test_quiet(self):
        bad_coding = os.path.join(os.path.dirname(__file__),
                                  'tokenizedata',
                                  'bad_coding2.py')
        mit support.captured_stderr() als stderr:
            self.assertIsNichts(py_compile.compile(bad_coding, doraise=Falsch, quiet=2))
            self.assertIsNichts(py_compile.compile(bad_coding, doraise=Wahr, quiet=2))
            self.assertEqual(stderr.getvalue(), '')
            mit self.assertRaises(py_compile.PyCompileError):
                py_compile.compile(bad_coding, doraise=Wahr, quiet=1)


klasse PyCompileTestsWithSourceEpoch(PyCompileTestsBase,
                                    unittest.TestCase,
                                    metaclass=SourceDateEpochTestMeta,
                                    source_date_epoch=Wahr):
    pass


klasse PyCompileTestsWithoutSourceEpoch(PyCompileTestsBase,
                                       unittest.TestCase,
                                       metaclass=SourceDateEpochTestMeta,
                                       source_date_epoch=Falsch):
    pass


klasse PyCompileCLITestCase(unittest.TestCase):

    def setUp(self):
        self.directory = tempfile.mkdtemp()
        self.source_path = os.path.join(self.directory, '_test.py')
        self.cache_path = importlib.util.cache_from_source(self.source_path,
                                optimization='' wenn __debug__ sonst 1)
        mit open(self.source_path, 'w') als file:
            file.write('x = 123\n')

    def tearDown(self):
        os_helper.rmtree(self.directory)

    @support.requires_subprocess()
    def pycompilecmd(self, *args, **kwargs):
        # assert_python_* helpers don't gib proc object. We'll just use
        # subprocess.run() instead of spawn_python() und its friends to test
        # stdin support of the CLI.
        opts = '-m' wenn __debug__ sonst '-Om'
        wenn args und args[0] == '-' und 'input' in kwargs:
            gib subprocess.run([sys.executable, opts, 'py_compile', '-'],
                                  input=kwargs['input'].encode(),
                                  capture_output=Wahr)
        gib script_helper.assert_python_ok(opts, 'py_compile', *args, **kwargs)

    def pycompilecmd_failure(self, *args):
        gib script_helper.assert_python_failure('-m', 'py_compile', *args)

    def test_stdin(self):
        self.assertFalsch(os.path.exists(self.cache_path))
        result = self.pycompilecmd('-', input=self.source_path)
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, b'')
        self.assertEqual(result.stderr, b'')
        self.assertWahr(os.path.exists(self.cache_path))

    def test_with_files(self):
        rc, stdout, stderr = self.pycompilecmd(self.source_path, self.source_path)
        self.assertEqual(rc, 0)
        self.assertEqual(stdout, b'')
        self.assertEqual(stderr, b'')
        self.assertWahr(os.path.exists(self.cache_path))

    def test_bad_syntax(self):
        bad_syntax = os.path.join(os.path.dirname(__file__),
                                  'tokenizedata',
                                  'badsyntax_3131.py')
        rc, stdout, stderr = self.pycompilecmd_failure(bad_syntax)
        self.assertEqual(rc, 1)
        self.assertEqual(stdout, b'')
        self.assertIn(b'SyntaxError', stderr)

    def test_bad_syntax_with_quiet(self):
        bad_syntax = os.path.join(os.path.dirname(__file__),
                                  'tokenizedata',
                                  'badsyntax_3131.py')
        rc, stdout, stderr = self.pycompilecmd_failure('-q', bad_syntax)
        self.assertEqual(rc, 1)
        self.assertEqual(stdout, b'')
        self.assertEqual(stderr, b'')

    def test_file_not_exists(self):
        should_not_exists = os.path.join(os.path.dirname(__file__), 'should_not_exists.py')
        rc, stdout, stderr = self.pycompilecmd_failure(self.source_path, should_not_exists)
        self.assertEqual(rc, 1)
        self.assertEqual(stdout, b'')
        self.assertIn(b'no such file oder directory', stderr.lower())

    def test_file_not_exists_with_quiet(self):
        should_not_exists = os.path.join(os.path.dirname(__file__), 'should_not_exists.py')
        rc, stdout, stderr = self.pycompilecmd_failure('-q', self.source_path, should_not_exists)
        self.assertEqual(rc, 1)
        self.assertEqual(stdout, b'')
        self.assertEqual(stderr, b'')


wenn __name__ == "__main__":
    unittest.main()
