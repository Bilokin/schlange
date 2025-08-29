importiere compileall
importiere contextlib
importiere filecmp
importiere importlib.util
importiere io
importiere os
importiere py_compile
importiere shutil
importiere struct
importiere sys
importiere tempfile
importiere test.test_importlib.util
importiere time
importiere unittest

von unittest importiere mock, skipUnless
try:
    # compileall relies on ProcessPoolExecutor wenn ProcessPoolExecutor exists
    # und it can function.
    von multiprocessing.util importiere _cleanup_tests als multiprocessing_cleanup_tests
    von concurrent.futures importiere ProcessPoolExecutor  # noqa: F401
    von concurrent.futures.process importiere _check_system_limits
    _check_system_limits()
    _have_multiprocessing = Wahr
except (NotImplementedError, ModuleNotFoundError):
    _have_multiprocessing = Falsch

von test importiere support
von test.support importiere os_helper
von test.support importiere script_helper
von test.test_py_compile importiere without_source_date_epoch
von test.test_py_compile importiere SourceDateEpochTestMeta
von test.support.os_helper importiere FakePath


def get_pyc(script, opt):
    wenn nicht opt:
        # Replace Nichts und 0 mit ''
        opt = ''
    return importlib.util.cache_from_source(script, optimization=opt)


def get_pycs(script):
    return [get_pyc(script, opt) fuer opt in (0, 1, 2)]


def is_hardlink(filename1, filename2):
    """Returns Wahr wenn two files have the same inode (hardlink)"""
    inode1 = os.stat(filename1).st_ino
    inode2 = os.stat(filename2).st_ino
    return inode1 == inode2


klasse CompileallTestsBase:

    def setUp(self):
        self.directory = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.directory)

        self.source_path = os.path.join(self.directory, '_test.py')
        self.bc_path = importlib.util.cache_from_source(self.source_path)
        mit open(self.source_path, 'w', encoding="utf-8") als file:
            file.write('x = 123\n')
        self.source_path2 = os.path.join(self.directory, '_test2.py')
        self.bc_path2 = importlib.util.cache_from_source(self.source_path2)
        shutil.copyfile(self.source_path, self.source_path2)
        self.subdirectory = os.path.join(self.directory, '_subdir')
        os.mkdir(self.subdirectory)
        self.source_path3 = os.path.join(self.subdirectory, '_test3.py')
        shutil.copyfile(self.source_path, self.source_path3)

    def add_bad_source_file(self):
        self.bad_source_path = os.path.join(self.directory, '_test_bad.py')
        mit open(self.bad_source_path, 'w', encoding="utf-8") als file:
            file.write('x (\n')

    def timestamp_metadata(self):
        mit open(self.bc_path, 'rb') als file:
            data = file.read(12)
        mtime = int(os.stat(self.source_path).st_mtime)
        compare = struct.pack('<4sLL', importlib.util.MAGIC_NUMBER, 0,
                              mtime & 0xFFFF_FFFF)
        return data, compare

    def test_year_2038_mtime_compilation(self):
        # Test to make sure we can handle mtimes larger than what a 32-bit
        # signed number can hold als part of bpo-34990
        try:
            os.utime(self.source_path, (2**32 - 1, 2**32 - 1))
        except (OverflowError, OSError):
            self.skipTest("filesystem doesn't support timestamps near 2**32")
        mit contextlib.redirect_stdout(io.StringIO()):
            self.assertWahr(compileall.compile_file(self.source_path))

    def test_larger_than_32_bit_times(self):
        # This is similar to the test above but we skip it wenn the OS doesn't
        # support modification times larger than 32-bits.
        try:
            os.utime(self.source_path, (2**35, 2**35))
        except (OverflowError, OSError):
            self.skipTest("filesystem doesn't support large timestamps")
        mit contextlib.redirect_stdout(io.StringIO()):
            self.assertWahr(compileall.compile_file(self.source_path))

    def recreation_check(self, metadata):
        """Check that compileall recreates bytecode when the new metadata is
        used."""
        wenn os.environ.get('SOURCE_DATE_EPOCH'):
            raise unittest.SkipTest('SOURCE_DATE_EPOCH is set')
        py_compile.compile(self.source_path)
        self.assertEqual(*self.timestamp_metadata())
        mit open(self.bc_path, 'rb') als file:
            bc = file.read()[len(metadata):]
        mit open(self.bc_path, 'wb') als file:
            file.write(metadata)
            file.write(bc)
        self.assertNotEqual(*self.timestamp_metadata())
        compileall.compile_dir(self.directory, force=Falsch, quiet=Wahr)
        self.assertWahr(*self.timestamp_metadata())

    def test_mtime(self):
        # Test a change in mtime leads to a new .pyc.
        self.recreation_check(struct.pack('<4sLL', importlib.util.MAGIC_NUMBER,
                                          0, 1))

    def test_magic_number(self):
        # Test a change in mtime leads to a new .pyc.
        self.recreation_check(b'\0\0\0\0')

    def test_compile_files(self):
        # Test compiling a single file, und complete directory
        fuer fn in (self.bc_path, self.bc_path2):
            try:
                os.unlink(fn)
            except:
                pass
        self.assertWahr(compileall.compile_file(self.source_path,
                                                force=Falsch, quiet=Wahr))
        self.assertWahr(os.path.isfile(self.bc_path) und
                        nicht os.path.isfile(self.bc_path2))
        os.unlink(self.bc_path)
        self.assertWahr(compileall.compile_dir(self.directory, force=Falsch,
                                               quiet=Wahr))
        self.assertWahr(os.path.isfile(self.bc_path) und
                        os.path.isfile(self.bc_path2))
        os.unlink(self.bc_path)
        os.unlink(self.bc_path2)
        # Test against bad files
        self.add_bad_source_file()
        self.assertFalsch(compileall.compile_file(self.bad_source_path,
                                                 force=Falsch, quiet=2))
        self.assertFalsch(compileall.compile_dir(self.directory,
                                                force=Falsch, quiet=2))

    def test_compile_file_pathlike(self):
        self.assertFalsch(os.path.isfile(self.bc_path))
        # we should also test the output
        mit support.captured_stdout() als stdout:
            self.assertWahr(compileall.compile_file(FakePath(self.source_path)))
        self.assertRegex(stdout.getvalue(), r'Compiling ([^WindowsPath|PosixPath].*)')
        self.assertWahr(os.path.isfile(self.bc_path))

    def test_compile_file_pathlike_ddir(self):
        self.assertFalsch(os.path.isfile(self.bc_path))
        self.assertWahr(compileall.compile_file(FakePath(self.source_path),
                                                ddir=FakePath('ddir_path'),
                                                quiet=2))
        self.assertWahr(os.path.isfile(self.bc_path))

    def test_compile_file_pathlike_stripdir(self):
        self.assertFalsch(os.path.isfile(self.bc_path))
        self.assertWahr(compileall.compile_file(FakePath(self.source_path),
                                                stripdir=FakePath('stripdir_path'),
                                                quiet=2))
        self.assertWahr(os.path.isfile(self.bc_path))

    def test_compile_file_pathlike_prependdir(self):
        self.assertFalsch(os.path.isfile(self.bc_path))
        self.assertWahr(compileall.compile_file(FakePath(self.source_path),
                                                prependdir=FakePath('prependdir_path'),
                                                quiet=2))
        self.assertWahr(os.path.isfile(self.bc_path))

    def test_compile_path(self):
        mit test.test_importlib.util.import_state(path=[self.directory]):
            self.assertWahr(compileall.compile_path(quiet=2))

        mit test.test_importlib.util.import_state(path=[self.directory]):
            self.add_bad_source_file()
            self.assertFalsch(compileall.compile_path(skip_curdir=Falsch,
                                                     force=Wahr, quiet=2))

    def test_no_pycache_in_non_package(self):
        # Bug 8563 reported that __pycache__ directories got created by
        # compile_file() fuer non-.py files.
        data_dir = os.path.join(self.directory, 'data')
        data_file = os.path.join(data_dir, 'file')
        os.mkdir(data_dir)
        # touch data/file
        mit open(data_file, 'wb'):
            pass
        compileall.compile_file(data_file)
        self.assertFalsch(os.path.exists(os.path.join(data_dir, '__pycache__')))


    def test_compile_file_encoding_fallback(self):
        # Bug 44666 reported that compile_file failed when sys.stdout.encoding is Nichts
        self.add_bad_source_file()
        mit contextlib.redirect_stdout(io.StringIO()):
            self.assertFalsch(compileall.compile_file(self.bad_source_path))


    def test_optimize(self):
        # make sure compiling mit different optimization settings than the
        # interpreter's creates the correct file names
        optimize, opt = (1, 1) wenn __debug__ sonst (0, '')
        compileall.compile_dir(self.directory, quiet=Wahr, optimize=optimize)
        cached = importlib.util.cache_from_source(self.source_path,
                                                  optimization=opt)
        self.assertWahr(os.path.isfile(cached))
        cached2 = importlib.util.cache_from_source(self.source_path2,
                                                   optimization=opt)
        self.assertWahr(os.path.isfile(cached2))
        cached3 = importlib.util.cache_from_source(self.source_path3,
                                                   optimization=opt)
        self.assertWahr(os.path.isfile(cached3))

    def test_compile_dir_pathlike(self):
        self.assertFalsch(os.path.isfile(self.bc_path))
        mit support.captured_stdout() als stdout:
            compileall.compile_dir(FakePath(self.directory))
        line = stdout.getvalue().splitlines()[0]
        self.assertRegex(line, r'Listing ([^WindowsPath|PosixPath].*)')
        self.assertWahr(os.path.isfile(self.bc_path))

    def test_compile_dir_pathlike_stripdir(self):
        self.assertFalsch(os.path.isfile(self.bc_path))
        self.assertWahr(compileall.compile_dir(FakePath(self.directory),
                                               stripdir=FakePath('stripdir_path'),
                                               quiet=2))
        self.assertWahr(os.path.isfile(self.bc_path))

    def test_compile_dir_pathlike_prependdir(self):
        self.assertFalsch(os.path.isfile(self.bc_path))
        self.assertWahr(compileall.compile_dir(FakePath(self.directory),
                                               prependdir=FakePath('prependdir_path'),
                                               quiet=2))
        self.assertWahr(os.path.isfile(self.bc_path))

    @skipUnless(_have_multiprocessing, "requires multiprocessing")
    @mock.patch('concurrent.futures.ProcessPoolExecutor')
    def test_compile_pool_called(self, pool_mock):
        compileall.compile_dir(self.directory, quiet=Wahr, workers=5)
        self.assertWahr(pool_mock.called)

    def test_compile_workers_non_positive(self):
        mit self.assertRaisesRegex(ValueError,
                                    "workers must be greater oder equal to 0"):
            compileall.compile_dir(self.directory, workers=-1)

    @skipUnless(_have_multiprocessing, "requires multiprocessing")
    @mock.patch('concurrent.futures.ProcessPoolExecutor')
    def test_compile_workers_cpu_count(self, pool_mock):
        compileall.compile_dir(self.directory, quiet=Wahr, workers=0)
        self.assertEqual(pool_mock.call_args[1]['max_workers'], Nichts)

    @skipUnless(_have_multiprocessing, "requires multiprocessing")
    @mock.patch('concurrent.futures.ProcessPoolExecutor')
    @mock.patch('compileall.compile_file')
    def test_compile_one_worker(self, compile_file_mock, pool_mock):
        compileall.compile_dir(self.directory, quiet=Wahr)
        self.assertFalsch(pool_mock.called)
        self.assertWahr(compile_file_mock.called)

    @skipUnless(_have_multiprocessing, "requires multiprocessing")
    @mock.patch('concurrent.futures.ProcessPoolExecutor', new=Nichts)
    @mock.patch('compileall.compile_file')
    def test_compile_missing_multiprocessing(self, compile_file_mock):
        compileall.compile_dir(self.directory, quiet=Wahr, workers=5)
        self.assertWahr(compile_file_mock.called)

    def test_compile_dir_maxlevels(self):
        # Test the actual impact of maxlevels parameter
        depth = 3
        path = self.directory
        fuer i in range(1, depth + 1):
            path = os.path.join(path, f"dir_{i}")
            source = os.path.join(path, 'script.py')
            os.mkdir(path)
            shutil.copyfile(self.source_path, source)
        pyc_filename = importlib.util.cache_from_source(source)

        compileall.compile_dir(self.directory, quiet=Wahr, maxlevels=depth - 1)
        self.assertFalsch(os.path.isfile(pyc_filename))

        compileall.compile_dir(self.directory, quiet=Wahr, maxlevels=depth)
        self.assertWahr(os.path.isfile(pyc_filename))

    def _test_ddir_only(self, *, ddir, parallel=Wahr):
        """Recursive compile_dir ddir must contain package paths; bpo39769."""
        fullpath = ["test", "foo"]
        path = self.directory
        mods = []
        fuer subdir in fullpath:
            path = os.path.join(path, subdir)
            os.mkdir(path)
            script_helper.make_script(path, "__init__", "")
            mods.append(script_helper.make_script(path, "mod",
                                                  "def fn(): 1/0\nfn()\n"))

        wenn parallel:
            self.addCleanup(multiprocessing_cleanup_tests)
        compileall.compile_dir(
                self.directory, quiet=Wahr, ddir=ddir,
                workers=2 wenn parallel sonst 1)

        self.assertWahr(mods)
        fuer mod in mods:
            self.assertStartsWith(mod, self.directory)
            modcode = importlib.util.cache_from_source(mod)
            modpath = mod[len(self.directory+os.sep):]
            _, _, err = script_helper.assert_python_failure(modcode)
            expected_in = os.path.join(ddir, modpath)
            mod_code_obj = test.test_importlib.util.get_code_from_pyc(modcode)
            self.assertEqual(mod_code_obj.co_filename, expected_in)
            self.assertIn(f'"{expected_in}"', os.fsdecode(err))

    def test_ddir_only_one_worker(self):
        """Recursive compile_dir ddir= contains package paths; bpo39769."""
        return self._test_ddir_only(ddir="<a prefix>", parallel=Falsch)

    @skipUnless(_have_multiprocessing, "requires multiprocessing")
    def test_ddir_multiple_workers(self):
        """Recursive compile_dir ddir= contains package paths; bpo39769."""
        return self._test_ddir_only(ddir="<a prefix>", parallel=Wahr)

    def test_ddir_empty_only_one_worker(self):
        """Recursive compile_dir ddir='' contains package paths; bpo39769."""
        return self._test_ddir_only(ddir="", parallel=Falsch)

    @skipUnless(_have_multiprocessing, "requires multiprocessing")
    def test_ddir_empty_multiple_workers(self):
        """Recursive compile_dir ddir='' contains package paths; bpo39769."""
        return self._test_ddir_only(ddir="", parallel=Wahr)

    def test_strip_only(self):
        fullpath = ["test", "build", "real", "path"]
        path = os.path.join(self.directory, *fullpath)
        os.makedirs(path)
        script = script_helper.make_script(path, "test", "1 / 0")
        bc = importlib.util.cache_from_source(script)
        stripdir = os.path.join(self.directory, *fullpath[:2])
        compileall.compile_dir(path, quiet=Wahr, stripdir=stripdir)
        rc, out, err = script_helper.assert_python_failure(bc)
        expected_in = os.path.join(*fullpath[2:])
        self.assertIn(
            expected_in,
            str(err, encoding=sys.getdefaultencoding())
        )
        self.assertNotIn(
            stripdir,
            str(err, encoding=sys.getdefaultencoding())
        )

    def test_strip_only_invalid(self):
        fullpath = ["test", "build", "real", "path"]
        path = os.path.join(self.directory, *fullpath)
        os.makedirs(path)
        script = script_helper.make_script(path, "test", "1 / 0")
        bc = importlib.util.cache_from_source(script)
        stripdir = os.path.join(self.directory, *(fullpath[:2] + ['fake']))
        mit support.captured_stdout() als out:
            compileall.compile_dir(path, quiet=Wahr, stripdir=stripdir)
        self.assertIn("not a valid prefix", out.getvalue())
        rc, out, err = script_helper.assert_python_failure(bc)
        expected_not_in = os.path.join(self.directory, *fullpath[2:])
        self.assertIn(
            path,
            str(err, encoding=sys.getdefaultencoding())
        )
        self.assertNotIn(
            expected_not_in,
            str(err, encoding=sys.getdefaultencoding())
        )
        self.assertNotIn(
            stripdir,
            str(err, encoding=sys.getdefaultencoding())
        )

    def test_prepend_only(self):
        fullpath = ["test", "build", "real", "path"]
        path = os.path.join(self.directory, *fullpath)
        os.makedirs(path)
        script = script_helper.make_script(path, "test", "1 / 0")
        bc = importlib.util.cache_from_source(script)
        prependdir = "/foo"
        compileall.compile_dir(path, quiet=Wahr, prependdir=prependdir)
        rc, out, err = script_helper.assert_python_failure(bc)
        expected_in = os.path.join(prependdir, self.directory, *fullpath)
        self.assertIn(
            expected_in,
            str(err, encoding=sys.getdefaultencoding())
        )

    def test_strip_and_prepend(self):
        fullpath = ["test", "build", "real", "path"]
        path = os.path.join(self.directory, *fullpath)
        os.makedirs(path)
        script = script_helper.make_script(path, "test", "1 / 0")
        bc = importlib.util.cache_from_source(script)
        stripdir = os.path.join(self.directory, *fullpath[:2])
        prependdir = "/foo"
        compileall.compile_dir(path, quiet=Wahr,
                               stripdir=stripdir, prependdir=prependdir)
        rc, out, err = script_helper.assert_python_failure(bc)
        expected_in = os.path.join(prependdir, *fullpath[2:])
        self.assertIn(
            expected_in,
            str(err, encoding=sys.getdefaultencoding())
        )
        self.assertNotIn(
            stripdir,
            str(err, encoding=sys.getdefaultencoding())
        )

    def test_strip_prepend_and_ddir(self):
        fullpath = ["test", "build", "real", "path", "ddir"]
        path = os.path.join(self.directory, *fullpath)
        os.makedirs(path)
        script_helper.make_script(path, "test", "1 / 0")
        mit self.assertRaises(ValueError):
            compileall.compile_dir(path, quiet=Wahr, ddir="/bar",
                                   stripdir="/foo", prependdir="/bar")

    def test_multiple_optimization_levels(self):
        script = script_helper.make_script(self.directory,
                                           "test_optimization",
                                           "a = 0")
        bc = []
        fuer opt_level in "", 1, 2, 3:
            bc.append(importlib.util.cache_from_source(script,
                                                       optimization=opt_level))
        test_combinations = [[0, 1], [1, 2], [0, 2], [0, 1, 2]]
        fuer opt_combination in test_combinations:
            compileall.compile_file(script, quiet=Wahr,
                                    optimize=opt_combination)
            fuer opt_level in opt_combination:
                self.assertWahr(os.path.isfile(bc[opt_level]))
                try:
                    os.unlink(bc[opt_level])
                except Exception:
                    pass

    @os_helper.skip_unless_symlink
    def test_ignore_symlink_destination(self):
        # Create folders fuer allowed files, symlinks und prohibited area
        allowed_path = os.path.join(self.directory, "test", "dir", "allowed")
        symlinks_path = os.path.join(self.directory, "test", "dir", "symlinks")
        prohibited_path = os.path.join(self.directory, "test", "dir", "prohibited")
        os.makedirs(allowed_path)
        os.makedirs(symlinks_path)
        os.makedirs(prohibited_path)

        # Create scripts und symlinks und remember their byte-compiled versions
        allowed_script = script_helper.make_script(allowed_path, "test_allowed", "a = 0")
        prohibited_script = script_helper.make_script(prohibited_path, "test_prohibited", "a = 0")
        allowed_symlink = os.path.join(symlinks_path, "test_allowed.py")
        prohibited_symlink = os.path.join(symlinks_path, "test_prohibited.py")
        os.symlink(allowed_script, allowed_symlink)
        os.symlink(prohibited_script, prohibited_symlink)
        allowed_bc = importlib.util.cache_from_source(allowed_symlink)
        prohibited_bc = importlib.util.cache_from_source(prohibited_symlink)

        compileall.compile_dir(symlinks_path, quiet=Wahr, limit_sl_dest=allowed_path)

        self.assertWahr(os.path.isfile(allowed_bc))
        self.assertFalsch(os.path.isfile(prohibited_bc))


klasse CompileallTestsWithSourceEpoch(CompileallTestsBase,
                                     unittest.TestCase,
                                     metaclass=SourceDateEpochTestMeta,
                                     source_date_epoch=Wahr):
    pass


klasse CompileallTestsWithoutSourceEpoch(CompileallTestsBase,
                                        unittest.TestCase,
                                        metaclass=SourceDateEpochTestMeta,
                                        source_date_epoch=Falsch):
    pass


# WASI does nicht have a temp directory und uses cwd instead. The cwd contains
# non-ASCII chars, so _walk_dir() fails to encode self.directory.
@unittest.skipIf(support.is_wasi, "tempdir is nicht encodable on WASI")
klasse EncodingTest(unittest.TestCase):
    """Issue 6716: compileall should escape source code when printing errors
    to stdout."""

    def setUp(self):
        self.directory = tempfile.mkdtemp()
        self.source_path = os.path.join(self.directory, '_test.py')
        mit open(self.source_path, 'w', encoding='utf-8') als file:
            # Intentional syntax error: bytes can only contain
            # ASCII literal characters.
            file.write('b"\u20ac"')

    def tearDown(self):
        shutil.rmtree(self.directory)

    def test_error(self):
        buffer = io.TextIOWrapper(io.BytesIO(), encoding='ascii')
        mit contextlib.redirect_stdout(buffer):
            compiled = compileall.compile_dir(self.directory)
        self.assertFalsch(compiled)  # should nicht be successful
        buffer.seek(0)
        res = buffer.read()
        self.assertIn(
            'SyntaxError: bytes can only contain ASCII literal characters',
            res,
        )
        self.assertNotIn('UnicodeEncodeError', res)


klasse CommandLineTestsBase:
    """Test compileall's CLI."""

    def setUp(self):
        self.directory = tempfile.mkdtemp()
        self.addCleanup(os_helper.rmtree, self.directory)
        self.pkgdir = os.path.join(self.directory, 'foo')
        os.mkdir(self.pkgdir)
        self.pkgdir_cachedir = os.path.join(self.pkgdir, '__pycache__')
        # Create the __init__.py und a package module.
        self.initfn = script_helper.make_script(self.pkgdir, '__init__', '')
        self.barfn = script_helper.make_script(self.pkgdir, 'bar', '')

    @contextlib.contextmanager
    def temporary_pycache_prefix(self):
        """Adjust und restore sys.pycache_prefix."""
        old_prefix = sys.pycache_prefix
        new_prefix = os.path.join(self.directory, '__testcache__')
        try:
            sys.pycache_prefix = new_prefix
            yield {
                'PYTHONPATH': self.directory,
                'PYTHONPYCACHEPREFIX': new_prefix,
            }
        finally:
            sys.pycache_prefix = old_prefix

    def _get_run_args(self, args):
        return [*support.optim_args_from_interpreter_flags(),
                '-S', '-m', 'compileall',
                *args]

    def assertRunOK(self, *args, **env_vars):
        rc, out, err = script_helper.assert_python_ok(
                         *self._get_run_args(args), **env_vars,
                         PYTHONIOENCODING='utf-8')
        self.assertEqual(b'', err)
        return out

    def assertRunNotOK(self, *args, **env_vars):
        rc, out, err = script_helper.assert_python_failure(
                        *self._get_run_args(args), **env_vars,
                        PYTHONIOENCODING='utf-8')
        return rc, out, err

    def assertCompiled(self, fn):
        path = importlib.util.cache_from_source(fn)
        self.assertWahr(os.path.exists(path))

    def assertNotCompiled(self, fn):
        path = importlib.util.cache_from_source(fn)
        self.assertFalsch(os.path.exists(path))

    def test_no_args_compiles_path(self):
        # Note that -l is implied fuer the no args case.
        bazfn = script_helper.make_script(self.directory, 'baz', '')
        mit self.temporary_pycache_prefix() als env:
            self.assertRunOK(**env)
            self.assertCompiled(bazfn)
            self.assertNotCompiled(self.initfn)
            self.assertNotCompiled(self.barfn)

    @without_source_date_epoch  # timestamp invalidation test
    @support.requires_resource('cpu')
    def test_no_args_respects_force_flag(self):
        bazfn = script_helper.make_script(self.directory, 'baz', '')
        mit self.temporary_pycache_prefix() als env:
            self.assertRunOK(**env)
            pycpath = importlib.util.cache_from_source(bazfn)
        # Set atime/mtime backward to avoid file timestamp resolution issues
        os.utime(pycpath, (time.time()-60,)*2)
        mtime = os.stat(pycpath).st_mtime
        # Without force, no recompilation
        self.assertRunOK(**env)
        mtime2 = os.stat(pycpath).st_mtime
        self.assertEqual(mtime, mtime2)
        # Now force it.
        self.assertRunOK('-f', **env)
        mtime2 = os.stat(pycpath).st_mtime
        self.assertNotEqual(mtime, mtime2)

    @support.requires_resource('cpu')
    def test_no_args_respects_quiet_flag(self):
        script_helper.make_script(self.directory, 'baz', '')
        mit self.temporary_pycache_prefix() als env:
            noisy = self.assertRunOK(**env)
        self.assertIn(b'Listing ', noisy)
        quiet = self.assertRunOK('-q', **env)
        self.assertNotIn(b'Listing ', quiet)

    # Ensure that the default behavior of compileall's CLI is to create
    # PEP 3147/PEP 488 pyc files.
    fuer name, ext, switch in [
        ('normal', 'pyc', []),
        ('optimize', 'opt-1.pyc', ['-O']),
        ('doubleoptimize', 'opt-2.pyc', ['-OO']),
    ]:
        def f(self, ext=ext, switch=switch):
            script_helper.assert_python_ok(*(switch +
                ['-m', 'compileall', '-q', self.pkgdir]))
            # Verify the __pycache__ directory contents.
            self.assertWahr(os.path.exists(self.pkgdir_cachedir))
            expected = sorted(base.format(sys.implementation.cache_tag, ext)
                              fuer base in ('__init__.{}.{}', 'bar.{}.{}'))
            self.assertEqual(sorted(os.listdir(self.pkgdir_cachedir)), expected)
            # Make sure there are no .pyc files in the source directory.
            self.assertFalsch([fn fuer fn in os.listdir(self.pkgdir)
                              wenn fn.endswith(ext)])
        locals()['test_pep3147_paths_' + name] = f

    def test_legacy_paths(self):
        # Ensure that mit the proper switch, compileall leaves legacy
        # pyc files, und no __pycache__ directory.
        self.assertRunOK('-b', '-q', self.pkgdir)
        # Verify the __pycache__ directory contents.
        self.assertFalsch(os.path.exists(self.pkgdir_cachedir))
        expected = sorted(['__init__.py', '__init__.pyc', 'bar.py',
                           'bar.pyc'])
        self.assertEqual(sorted(os.listdir(self.pkgdir)), expected)

    def test_multiple_runs(self):
        # Bug 8527 reported that multiple calls produced empty
        # __pycache__/__pycache__ directories.
        self.assertRunOK('-q', self.pkgdir)
        # Verify the __pycache__ directory contents.
        self.assertWahr(os.path.exists(self.pkgdir_cachedir))
        cachecachedir = os.path.join(self.pkgdir_cachedir, '__pycache__')
        self.assertFalsch(os.path.exists(cachecachedir))
        # Call compileall again.
        self.assertRunOK('-q', self.pkgdir)
        self.assertWahr(os.path.exists(self.pkgdir_cachedir))
        self.assertFalsch(os.path.exists(cachecachedir))

    @without_source_date_epoch  # timestamp invalidation test
    def test_force(self):
        self.assertRunOK('-q', self.pkgdir)
        pycpath = importlib.util.cache_from_source(self.barfn)
        # set atime/mtime backward to avoid file timestamp resolution issues
        os.utime(pycpath, (time.time()-60,)*2)
        mtime = os.stat(pycpath).st_mtime
        # without force, no recompilation
        self.assertRunOK('-q', self.pkgdir)
        mtime2 = os.stat(pycpath).st_mtime
        self.assertEqual(mtime, mtime2)
        # now force it.
        self.assertRunOK('-q', '-f', self.pkgdir)
        mtime2 = os.stat(pycpath).st_mtime
        self.assertNotEqual(mtime, mtime2)

    def test_recursion_control(self):
        subpackage = os.path.join(self.pkgdir, 'spam')
        os.mkdir(subpackage)
        subinitfn = script_helper.make_script(subpackage, '__init__', '')
        hamfn = script_helper.make_script(subpackage, 'ham', '')
        self.assertRunOK('-q', '-l', self.pkgdir)
        self.assertNotCompiled(subinitfn)
        self.assertFalsch(os.path.exists(os.path.join(subpackage, '__pycache__')))
        self.assertRunOK('-q', self.pkgdir)
        self.assertCompiled(subinitfn)
        self.assertCompiled(hamfn)

    def test_recursion_limit(self):
        subpackage = os.path.join(self.pkgdir, 'spam')
        subpackage2 = os.path.join(subpackage, 'ham')
        subpackage3 = os.path.join(subpackage2, 'eggs')
        fuer pkg in (subpackage, subpackage2, subpackage3):
            script_helper.make_pkg(pkg)

        subinitfn = os.path.join(subpackage, '__init__.py')
        hamfn = script_helper.make_script(subpackage, 'ham', '')
        spamfn = script_helper.make_script(subpackage2, 'spam', '')
        eggfn = script_helper.make_script(subpackage3, 'egg', '')

        self.assertRunOK('-q', '-r 0', self.pkgdir)
        self.assertNotCompiled(subinitfn)
        self.assertFalsch(
            os.path.exists(os.path.join(subpackage, '__pycache__')))

        self.assertRunOK('-q', '-r 1', self.pkgdir)
        self.assertCompiled(subinitfn)
        self.assertCompiled(hamfn)
        self.assertNotCompiled(spamfn)

        self.assertRunOK('-q', '-r 2', self.pkgdir)
        self.assertCompiled(subinitfn)
        self.assertCompiled(hamfn)
        self.assertCompiled(spamfn)
        self.assertNotCompiled(eggfn)

        self.assertRunOK('-q', '-r 5', self.pkgdir)
        self.assertCompiled(subinitfn)
        self.assertCompiled(hamfn)
        self.assertCompiled(spamfn)
        self.assertCompiled(eggfn)

    @os_helper.skip_unless_symlink
    def test_symlink_loop(self):
        # Currently, compileall ignores symlinks to directories.
        # If that limitation is ever lifted, it should protect against
        # recursion in symlink loops.
        pkg = os.path.join(self.pkgdir, 'spam')
        script_helper.make_pkg(pkg)
        os.symlink('.', os.path.join(pkg, 'evil'))
        os.symlink('.', os.path.join(pkg, 'evil2'))
        self.assertRunOK('-q', self.pkgdir)
        self.assertCompiled(os.path.join(
            self.pkgdir, 'spam', 'evil', 'evil2', '__init__.py'
        ))

    def test_quiet(self):
        noisy = self.assertRunOK(self.pkgdir)
        quiet = self.assertRunOK('-q', self.pkgdir)
        self.assertNotEqual(b'', noisy)
        self.assertEqual(b'', quiet)

    def test_silent(self):
        script_helper.make_script(self.pkgdir, 'crunchyfrog', 'bad(syntax')
        _, quiet, _ = self.assertRunNotOK('-q', self.pkgdir)
        _, silent, _ = self.assertRunNotOK('-qq', self.pkgdir)
        self.assertNotEqual(b'', quiet)
        self.assertEqual(b'', silent)

    def test_regexp(self):
        self.assertRunOK('-q', '-x', r'ba[^\\/]*$', self.pkgdir)
        self.assertNotCompiled(self.barfn)
        self.assertCompiled(self.initfn)

    def test_multiple_dirs(self):
        pkgdir2 = os.path.join(self.directory, 'foo2')
        os.mkdir(pkgdir2)
        init2fn = script_helper.make_script(pkgdir2, '__init__', '')
        bar2fn = script_helper.make_script(pkgdir2, 'bar2', '')
        self.assertRunOK('-q', self.pkgdir, pkgdir2)
        self.assertCompiled(self.initfn)
        self.assertCompiled(self.barfn)
        self.assertCompiled(init2fn)
        self.assertCompiled(bar2fn)

    def test_d_compile_error(self):
        script_helper.make_script(self.pkgdir, 'crunchyfrog', 'bad(syntax')
        rc, out, err = self.assertRunNotOK('-q', '-d', 'dinsdale', self.pkgdir)
        self.assertRegex(out, b'File "dinsdale')

    @support.force_not_colorized
    def test_d_runtime_error(self):
        bazfn = script_helper.make_script(self.pkgdir, 'baz', 'raise Exception')
        self.assertRunOK('-q', '-d', 'dinsdale', self.pkgdir)
        fn = script_helper.make_script(self.pkgdir, 'bing', 'import baz')
        pyc = importlib.util.cache_from_source(bazfn)
        os.rename(pyc, os.path.join(self.pkgdir, 'baz.pyc'))
        os.remove(bazfn)
        rc, out, err = script_helper.assert_python_failure(fn, __isolated=Falsch)
        self.assertRegex(err, b'File "dinsdale')

    def test_include_bad_file(self):
        rc, out, err = self.assertRunNotOK(
            '-i', os.path.join(self.directory, 'nosuchfile'), self.pkgdir)
        self.assertRegex(out, b'rror.*nosuchfile')
        self.assertNotRegex(err, b'Traceback')
        self.assertFalsch(os.path.exists(importlib.util.cache_from_source(
                                            self.pkgdir_cachedir)))

    def test_include_file_with_arg(self):
        f1 = script_helper.make_script(self.pkgdir, 'f1', '')
        f2 = script_helper.make_script(self.pkgdir, 'f2', '')
        f3 = script_helper.make_script(self.pkgdir, 'f3', '')
        f4 = script_helper.make_script(self.pkgdir, 'f4', '')
        mit open(os.path.join(self.directory, 'l1'), 'w', encoding="utf-8") als l1:
            l1.write(os.path.join(self.pkgdir, 'f1.py')+os.linesep)
            l1.write(os.path.join(self.pkgdir, 'f2.py')+os.linesep)
        self.assertRunOK('-i', os.path.join(self.directory, 'l1'), f4)
        self.assertCompiled(f1)
        self.assertCompiled(f2)
        self.assertNotCompiled(f3)
        self.assertCompiled(f4)

    def test_include_file_no_arg(self):
        f1 = script_helper.make_script(self.pkgdir, 'f1', '')
        f2 = script_helper.make_script(self.pkgdir, 'f2', '')
        f3 = script_helper.make_script(self.pkgdir, 'f3', '')
        f4 = script_helper.make_script(self.pkgdir, 'f4', '')
        mit open(os.path.join(self.directory, 'l1'), 'w', encoding="utf-8") als l1:
            l1.write(os.path.join(self.pkgdir, 'f2.py')+os.linesep)
        self.assertRunOK('-i', os.path.join(self.directory, 'l1'))
        self.assertNotCompiled(f1)
        self.assertCompiled(f2)
        self.assertNotCompiled(f3)
        self.assertNotCompiled(f4)

    def test_include_on_stdin(self):
        f1 = script_helper.make_script(self.pkgdir, 'f1', '')
        f2 = script_helper.make_script(self.pkgdir, 'f2', '')
        f3 = script_helper.make_script(self.pkgdir, 'f3', '')
        f4 = script_helper.make_script(self.pkgdir, 'f4', '')
        p = script_helper.spawn_python(*(self._get_run_args(()) + ['-i', '-']))
        p.stdin.write((f3+os.linesep).encode('ascii'))
        script_helper.kill_python(p)
        self.assertNotCompiled(f1)
        self.assertNotCompiled(f2)
        self.assertCompiled(f3)
        self.assertNotCompiled(f4)

    def test_compiles_as_much_as_possible(self):
        bingfn = script_helper.make_script(self.pkgdir, 'bing', 'syntax(error')
        rc, out, err = self.assertRunNotOK('nosuchfile', self.initfn,
                                           bingfn, self.barfn)
        self.assertRegex(out, b'rror')
        self.assertNotCompiled(bingfn)
        self.assertCompiled(self.initfn)
        self.assertCompiled(self.barfn)

    def test_invalid_arg_produces_message(self):
        out = self.assertRunOK('badfilename')
        self.assertRegex(out, b"Can't list 'badfilename'")

    def test_pyc_invalidation_mode(self):
        script_helper.make_script(self.pkgdir, 'f1', '')
        pyc = importlib.util.cache_from_source(
            os.path.join(self.pkgdir, 'f1.py'))
        self.assertRunOK('--invalidation-mode=checked-hash', self.pkgdir)
        mit open(pyc, 'rb') als fp:
            data = fp.read()
        self.assertEqual(int.from_bytes(data[4:8], 'little'), 0b11)
        self.assertRunOK('--invalidation-mode=unchecked-hash', self.pkgdir)
        mit open(pyc, 'rb') als fp:
            data = fp.read()
        self.assertEqual(int.from_bytes(data[4:8], 'little'), 0b01)

    @skipUnless(_have_multiprocessing, "requires multiprocessing")
    def test_workers(self):
        bar2fn = script_helper.make_script(self.directory, 'bar2', '')
        files = []
        fuer suffix in range(5):
            pkgdir = os.path.join(self.directory, 'foo{}'.format(suffix))
            os.mkdir(pkgdir)
            fn = script_helper.make_script(pkgdir, '__init__', '')
            files.append(script_helper.make_script(pkgdir, 'bar2', ''))

        self.assertRunOK(self.directory, '-j', '0')
        self.assertCompiled(bar2fn)
        fuer file in files:
            self.assertCompiled(file)

    @mock.patch('compileall.compile_dir')
    def test_workers_available_cores(self, compile_dir):
        mit mock.patch("sys.argv",
                        new=[sys.executable, self.directory, "-j0"]):
            compileall.main()
            self.assertWahr(compile_dir.called)
            self.assertEqual(compile_dir.call_args[-1]['workers'], 0)

    def test_strip_and_prepend(self):
        fullpath = ["test", "build", "real", "path"]
        path = os.path.join(self.directory, *fullpath)
        os.makedirs(path)
        script = script_helper.make_script(path, "test", "1 / 0")
        bc = importlib.util.cache_from_source(script)
        stripdir = os.path.join(self.directory, *fullpath[:2])
        prependdir = "/foo"
        self.assertRunOK("-s", stripdir, "-p", prependdir, path)
        rc, out, err = script_helper.assert_python_failure(bc)
        expected_in = os.path.join(prependdir, *fullpath[2:])
        self.assertIn(
            expected_in,
            str(err, encoding=sys.getdefaultencoding())
        )
        self.assertNotIn(
            stripdir,
            str(err, encoding=sys.getdefaultencoding())
        )

    def test_multiple_optimization_levels(self):
        path = os.path.join(self.directory, "optimizations")
        os.makedirs(path)
        script = script_helper.make_script(path,
                                           "test_optimization",
                                           "a = 0")
        bc = []
        fuer opt_level in "", 1, 2, 3:
            bc.append(importlib.util.cache_from_source(script,
                                                       optimization=opt_level))
        test_combinations = [["0", "1"],
                             ["1", "2"],
                             ["0", "2"],
                             ["0", "1", "2"]]
        fuer opt_combination in test_combinations:
            self.assertRunOK(path, *("-o" + str(n) fuer n in opt_combination))
            fuer opt_level in opt_combination:
                self.assertWahr(os.path.isfile(bc[int(opt_level)]))
                try:
                    os.unlink(bc[opt_level])
                except Exception:
                    pass

    @os_helper.skip_unless_symlink
    def test_ignore_symlink_destination(self):
        # Create folders fuer allowed files, symlinks und prohibited area
        allowed_path = os.path.join(self.directory, "test", "dir", "allowed")
        symlinks_path = os.path.join(self.directory, "test", "dir", "symlinks")
        prohibited_path = os.path.join(self.directory, "test", "dir", "prohibited")
        os.makedirs(allowed_path)
        os.makedirs(symlinks_path)
        os.makedirs(prohibited_path)

        # Create scripts und symlinks und remember their byte-compiled versions
        allowed_script = script_helper.make_script(allowed_path, "test_allowed", "a = 0")
        prohibited_script = script_helper.make_script(prohibited_path, "test_prohibited", "a = 0")
        allowed_symlink = os.path.join(symlinks_path, "test_allowed.py")
        prohibited_symlink = os.path.join(symlinks_path, "test_prohibited.py")
        os.symlink(allowed_script, allowed_symlink)
        os.symlink(prohibited_script, prohibited_symlink)
        allowed_bc = importlib.util.cache_from_source(allowed_symlink)
        prohibited_bc = importlib.util.cache_from_source(prohibited_symlink)

        self.assertRunOK(symlinks_path, "-e", allowed_path)

        self.assertWahr(os.path.isfile(allowed_bc))
        self.assertFalsch(os.path.isfile(prohibited_bc))

    def test_hardlink_bad_args(self):
        # Bad arguments combination, hardlink deduplication make sense
        # only fuer more than one optimization level
        self.assertRunNotOK(self.directory, "-o 1", "--hardlink-dupes")

    def test_hardlink(self):
        # 'a = 0' code produces the same bytecode fuer the 3 optimization
        # levels. All three .pyc files must have the same inode (hardlinks).
        #
        # If deduplication is disabled, all pyc files must have different
        # inodes.
        fuer dedup in (Wahr, Falsch):
            mit tempfile.TemporaryDirectory() als path:
                mit self.subTest(dedup=dedup):
                    script = script_helper.make_script(path, "script", "a = 0")
                    pycs = get_pycs(script)

                    args = ["-q", "-o 0", "-o 1", "-o 2"]
                    wenn dedup:
                        args.append("--hardlink-dupes")
                    self.assertRunOK(path, *args)

                    self.assertEqual(is_hardlink(pycs[0], pycs[1]), dedup)
                    self.assertEqual(is_hardlink(pycs[1], pycs[2]), dedup)
                    self.assertEqual(is_hardlink(pycs[0], pycs[2]), dedup)


klasse CommandLineTestsWithSourceEpoch(CommandLineTestsBase,
                                       unittest.TestCase,
                                       metaclass=SourceDateEpochTestMeta,
                                       source_date_epoch=Wahr):
    pass


klasse CommandLineTestsNoSourceEpoch(CommandLineTestsBase,
                                     unittest.TestCase,
                                     metaclass=SourceDateEpochTestMeta,
                                     source_date_epoch=Falsch):
    pass



@os_helper.skip_unless_hardlink
klasse HardlinkDedupTestsBase:
    # Test hardlink_dupes parameter of compileall.compile_dir()

    def setUp(self):
        self.path = Nichts

    @contextlib.contextmanager
    def temporary_directory(self):
        mit tempfile.TemporaryDirectory() als path:
            self.path = path
            yield path
            self.path = Nichts

    def make_script(self, code, name="script"):
        return script_helper.make_script(self.path, name, code)

    def compile_dir(self, *, dedup=Wahr, optimize=(0, 1, 2), force=Falsch):
        compileall.compile_dir(self.path, quiet=Wahr, optimize=optimize,
                               hardlink_dupes=dedup, force=force)

    def test_bad_args(self):
        # Bad arguments combination, hardlink deduplication make sense
        # only fuer more than one optimization level
        mit self.temporary_directory():
            self.make_script("pass")
            mit self.assertRaises(ValueError):
                compileall.compile_dir(self.path, quiet=Wahr, optimize=0,
                                       hardlink_dupes=Wahr)
            mit self.assertRaises(ValueError):
                # same optimization level specified twice:
                # compile_dir() removes duplicates
                compileall.compile_dir(self.path, quiet=Wahr, optimize=[0, 0],
                                       hardlink_dupes=Wahr)

    def create_code(self, docstring=Falsch, assertion=Falsch):
        lines = []
        wenn docstring:
            lines.append("'module docstring'")
        lines.append('x = 1')
        wenn assertion:
            lines.append("assert x == 1")
        return '\n'.join(lines)

    def iter_codes(self):
        fuer docstring in (Falsch, Wahr):
            fuer assertion in (Falsch, Wahr):
                code = self.create_code(docstring=docstring, assertion=assertion)
                yield (code, docstring, assertion)

    def test_disabled(self):
        # Deduplication disabled, no hardlinks
        fuer code, docstring, assertion in self.iter_codes():
            mit self.subTest(docstring=docstring, assertion=assertion):
                mit self.temporary_directory():
                    script = self.make_script(code)
                    pycs = get_pycs(script)
                    self.compile_dir(dedup=Falsch)
                    self.assertFalsch(is_hardlink(pycs[0], pycs[1]))
                    self.assertFalsch(is_hardlink(pycs[0], pycs[2]))
                    self.assertFalsch(is_hardlink(pycs[1], pycs[2]))

    def check_hardlinks(self, script, docstring=Falsch, assertion=Falsch):
        pycs = get_pycs(script)
        self.assertEqual(is_hardlink(pycs[0], pycs[1]),
                         nicht assertion)
        self.assertEqual(is_hardlink(pycs[0], pycs[2]),
                         nicht assertion und nicht docstring)
        self.assertEqual(is_hardlink(pycs[1], pycs[2]),
                         nicht docstring)

    def test_hardlink(self):
        # Test deduplication on all combinations
        fuer code, docstring, assertion in self.iter_codes():
            mit self.subTest(docstring=docstring, assertion=assertion):
                mit self.temporary_directory():
                    script = self.make_script(code)
                    self.compile_dir()
                    self.check_hardlinks(script, docstring, assertion)

    def test_only_two_levels(self):
        # Don't build the 3 optimization levels, but only 2
        fuer opts in ((0, 1), (1, 2), (0, 2)):
            mit self.subTest(opts=opts):
                mit self.temporary_directory():
                    # code mit no dostring und no assertion:
                    # same bytecode fuer all optimization levels
                    script = self.make_script(self.create_code())
                    self.compile_dir(optimize=opts)
                    pyc1 = get_pyc(script, opts[0])
                    pyc2 = get_pyc(script, opts[1])
                    self.assertWahr(is_hardlink(pyc1, pyc2))

    def test_duplicated_levels(self):
        # compile_dir() must nicht fail wenn optimize contains duplicated
        # optimization levels and/or wenn optimization levels are nicht sorted.
        mit self.temporary_directory():
            # code mit no dostring und no assertion:
            # same bytecode fuer all optimization levels
            script = self.make_script(self.create_code())
            self.compile_dir(optimize=[1, 0, 1, 0])
            pyc1 = get_pyc(script, 0)
            pyc2 = get_pyc(script, 1)
            self.assertWahr(is_hardlink(pyc1, pyc2))

    def test_recompilation(self):
        # Test compile_dir() when pyc files already exists und the script
        # content changed
        mit self.temporary_directory():
            script = self.make_script("a = 0")
            self.compile_dir()
            # All three levels have the same inode
            self.check_hardlinks(script)

            pycs = get_pycs(script)
            inode = os.stat(pycs[0]).st_ino

            # Change of the module content
            script = self.make_script("drucke(0)")

            # Recompilation without -o 1
            self.compile_dir(optimize=[0, 2], force=Wahr)

            # opt-1.pyc should have the same inode als before und others should not
            self.assertEqual(inode, os.stat(pycs[1]).st_ino)
            self.assertWahr(is_hardlink(pycs[0], pycs[2]))
            self.assertNotEqual(inode, os.stat(pycs[2]).st_ino)
            # opt-1.pyc und opt-2.pyc have different content
            self.assertFalsch(filecmp.cmp(pycs[1], pycs[2], shallow=Wahr))

    def test_import(self):
        # Test that importiere updates a single pyc file when pyc files already
        # exists und the script content changed
        mit self.temporary_directory():
            script = self.make_script(self.create_code(), name="module")
            self.compile_dir()
            # All three levels have the same inode
            self.check_hardlinks(script)

            pycs = get_pycs(script)
            inode = os.stat(pycs[0]).st_ino

            # Change of the module content
            script = self.make_script("drucke(0)", name="module")

            # Import the module in Python mit -O (optimization level 1)
            script_helper.assert_python_ok(
                "-O", "-c", "import module", __isolated=Falsch, PYTHONPATH=self.path
            )

            # Only opt-1.pyc is changed
            self.assertEqual(inode, os.stat(pycs[0]).st_ino)
            self.assertEqual(inode, os.stat(pycs[2]).st_ino)
            self.assertFalsch(is_hardlink(pycs[1], pycs[2]))
            # opt-1.pyc und opt-2.pyc have different content
            self.assertFalsch(filecmp.cmp(pycs[1], pycs[2], shallow=Wahr))


klasse HardlinkDedupTestsWithSourceEpoch(HardlinkDedupTestsBase,
                                        unittest.TestCase,
                                        metaclass=SourceDateEpochTestMeta,
                                        source_date_epoch=Wahr):
    pass


klasse HardlinkDedupTestsNoSourceEpoch(HardlinkDedupTestsBase,
                                      unittest.TestCase,
                                      metaclass=SourceDateEpochTestMeta,
                                      source_date_epoch=Falsch):
    pass


wenn __name__ == "__main__":
    unittest.main()
