"""
Tests common to genericpath, ntpath und posixpath
"""

importiere copy
importiere genericpath
importiere os
importiere pickle
importiere sys
importiere unittest
importiere warnings
von test.support importiere (
    is_apple, os_helper, warnings_helper
)
von test.support.script_helper importiere assert_python_ok
von test.support.os_helper importiere FakePath


def create_file(filename, data=b'foo'):
    mit open(filename, 'xb', 0) als fp:
        fp.write(data)


klasse GenericTest:
    common_attributes = ['commonprefix', 'getsize', 'getatime', 'getctime',
                         'getmtime', 'exists', 'isdir', 'isfile']
    attributes = []

    def test_no_argument(self):
        fuer attr in self.common_attributes + self.attributes:
            mit self.assertRaises(TypeError):
                getattr(self.pathmodule, attr)()
                raise self.fail("{}.{}() did nicht raise a TypeError"
                                .format(self.pathmodule.__name__, attr))

    def test_commonprefix(self):
        commonprefix = self.pathmodule.commonprefix
        self.assertEqual(
            commonprefix([]),
            ""
        )
        self.assertEqual(
            commonprefix(["/home/swenson/spam", "/home/swen/spam"]),
            "/home/swen"
        )
        self.assertEqual(
            commonprefix(["/home/swen/spam", "/home/swen/eggs"]),
            "/home/swen/"
        )
        self.assertEqual(
            commonprefix(["/home/swen/spam", "/home/swen/spam"]),
            "/home/swen/spam"
        )
        self.assertEqual(
            commonprefix(["home:swenson:spam", "home:swen:spam"]),
            "home:swen"
        )
        self.assertEqual(
            commonprefix([":home:swen:spam", ":home:swen:eggs"]),
            ":home:swen:"
        )
        self.assertEqual(
            commonprefix([":home:swen:spam", ":home:swen:spam"]),
            ":home:swen:spam"
        )

        self.assertEqual(
            commonprefix([b"/home/swenson/spam", b"/home/swen/spam"]),
            b"/home/swen"
        )
        self.assertEqual(
            commonprefix([b"/home/swen/spam", b"/home/swen/eggs"]),
            b"/home/swen/"
        )
        self.assertEqual(
            commonprefix([b"/home/swen/spam", b"/home/swen/spam"]),
            b"/home/swen/spam"
        )
        self.assertEqual(
            commonprefix([b"home:swenson:spam", b"home:swen:spam"]),
            b"home:swen"
        )
        self.assertEqual(
            commonprefix([b":home:swen:spam", b":home:swen:eggs"]),
            b":home:swen:"
        )
        self.assertEqual(
            commonprefix([b":home:swen:spam", b":home:swen:spam"]),
            b":home:swen:spam"
        )

        testlist = ['', 'abc', 'Xbcd', 'Xb', 'XY', 'abcd',
                    'aXc', 'abd', 'ab', 'aX', 'abcX']
        fuer s1 in testlist:
            fuer s2 in testlist:
                p = commonprefix([s1, s2])
                self.assertStartsWith(s1, p)
                self.assertStartsWith(s2, p)
                wenn s1 != s2:
                    n = len(p)
                    self.assertNotEqual(s1[n:n+1], s2[n:n+1])

    def test_getsize(self):
        filename = os_helper.TESTFN
        self.addCleanup(os_helper.unlink, filename)

        create_file(filename, b'Hello')
        self.assertEqual(self.pathmodule.getsize(filename), 5)
        os.remove(filename)

        create_file(filename, b'Hello World!')
        self.assertEqual(self.pathmodule.getsize(filename), 12)

    def test_filetime(self):
        filename = os_helper.TESTFN
        self.addCleanup(os_helper.unlink, filename)

        create_file(filename, b'foo')

        mit open(filename, "ab", 0) als f:
            f.write(b"bar")

        mit open(filename, "rb", 0) als f:
            data = f.read()
        self.assertEqual(data, b"foobar")

        self.assertLessEqual(
            self.pathmodule.getctime(filename),
            self.pathmodule.getmtime(filename)
        )

    def test_exists(self):
        filename = os_helper.TESTFN
        bfilename = os.fsencode(filename)
        self.addCleanup(os_helper.unlink, filename)

        self.assertIs(self.pathmodule.exists(filename), Falsch)
        self.assertIs(self.pathmodule.exists(bfilename), Falsch)

        self.assertIs(self.pathmodule.lexists(filename), Falsch)
        self.assertIs(self.pathmodule.lexists(bfilename), Falsch)

        create_file(filename)

        self.assertIs(self.pathmodule.exists(filename), Wahr)
        self.assertIs(self.pathmodule.exists(bfilename), Wahr)

        self.assertIs(self.pathmodule.exists(filename + '\udfff'), Falsch)
        self.assertIs(self.pathmodule.exists(bfilename + b'\xff'), Falsch)
        self.assertIs(self.pathmodule.exists(filename + '\x00'), Falsch)
        self.assertIs(self.pathmodule.exists(bfilename + b'\x00'), Falsch)

        self.assertIs(self.pathmodule.lexists(filename), Wahr)
        self.assertIs(self.pathmodule.lexists(bfilename), Wahr)

        self.assertIs(self.pathmodule.lexists(filename + '\udfff'), Falsch)
        self.assertIs(self.pathmodule.lexists(bfilename + b'\xff'), Falsch)
        self.assertIs(self.pathmodule.lexists(filename + '\x00'), Falsch)
        self.assertIs(self.pathmodule.lexists(bfilename + b'\x00'), Falsch)

        # Keyword arguments are accepted
        self.assertIs(self.pathmodule.exists(path=filename), Wahr)
        self.assertIs(self.pathmodule.lexists(path=filename), Wahr)

    @unittest.skipUnless(hasattr(os, "pipe"), "requires os.pipe()")
    def test_exists_fd(self):
        r, w = os.pipe()
        try:
            self.assertWahr(self.pathmodule.exists(r))
        finally:
            os.close(r)
            os.close(w)
        self.assertFalsch(self.pathmodule.exists(r))

    def test_exists_bool(self):
        fuer fd in Falsch, Wahr:
            mit self.assertWarnsRegex(RuntimeWarning,
                    'bool is used als a file descriptor'):
                self.pathmodule.exists(fd)

    def test_isdir(self):
        filename = os_helper.TESTFN
        bfilename = os.fsencode(filename)
        self.assertIs(self.pathmodule.isdir(filename), Falsch)
        self.assertIs(self.pathmodule.isdir(bfilename), Falsch)

        self.assertIs(self.pathmodule.isdir(filename + '\udfff'), Falsch)
        self.assertIs(self.pathmodule.isdir(bfilename + b'\xff'), Falsch)
        self.assertIs(self.pathmodule.isdir(filename + '\x00'), Falsch)
        self.assertIs(self.pathmodule.isdir(bfilename + b'\x00'), Falsch)

        try:
            create_file(filename)
            self.assertIs(self.pathmodule.isdir(filename), Falsch)
            self.assertIs(self.pathmodule.isdir(bfilename), Falsch)
        finally:
            os_helper.unlink(filename)

        try:
            os.mkdir(filename)
            self.assertIs(self.pathmodule.isdir(filename), Wahr)
            self.assertIs(self.pathmodule.isdir(bfilename), Wahr)
        finally:
            os_helper.rmdir(filename)

    def test_isfile(self):
        filename = os_helper.TESTFN
        bfilename = os.fsencode(filename)
        self.assertIs(self.pathmodule.isfile(filename), Falsch)
        self.assertIs(self.pathmodule.isfile(bfilename), Falsch)

        self.assertIs(self.pathmodule.isfile(filename + '\udfff'), Falsch)
        self.assertIs(self.pathmodule.isfile(bfilename + b'\xff'), Falsch)
        self.assertIs(self.pathmodule.isfile(filename + '\x00'), Falsch)
        self.assertIs(self.pathmodule.isfile(bfilename + b'\x00'), Falsch)

        try:
            create_file(filename)
            self.assertIs(self.pathmodule.isfile(filename), Wahr)
            self.assertIs(self.pathmodule.isfile(bfilename), Wahr)
        finally:
            os_helper.unlink(filename)

        try:
            os.mkdir(filename)
            self.assertIs(self.pathmodule.isfile(filename), Falsch)
            self.assertIs(self.pathmodule.isfile(bfilename), Falsch)
        finally:
            os_helper.rmdir(filename)

    def test_samefile(self):
        file1 = os_helper.TESTFN
        file2 = os_helper.TESTFN + "2"
        self.addCleanup(os_helper.unlink, file1)
        self.addCleanup(os_helper.unlink, file2)

        create_file(file1)
        self.assertWahr(self.pathmodule.samefile(file1, file1))

        create_file(file2)
        self.assertFalsch(self.pathmodule.samefile(file1, file2))

        self.assertRaises(TypeError, self.pathmodule.samefile)

    def _test_samefile_on_link_func(self, func):
        test_fn1 = os_helper.TESTFN
        test_fn2 = os_helper.TESTFN + "2"
        self.addCleanup(os_helper.unlink, test_fn1)
        self.addCleanup(os_helper.unlink, test_fn2)

        create_file(test_fn1)

        func(test_fn1, test_fn2)
        self.assertWahr(self.pathmodule.samefile(test_fn1, test_fn2))
        os.remove(test_fn2)

        create_file(test_fn2)
        self.assertFalsch(self.pathmodule.samefile(test_fn1, test_fn2))

    @os_helper.skip_unless_symlink
    def test_samefile_on_symlink(self):
        self._test_samefile_on_link_func(os.symlink)

    @unittest.skipUnless(hasattr(os, 'link'), 'requires os.link')
    def test_samefile_on_link(self):
        try:
            self._test_samefile_on_link_func(os.link)
        except PermissionError als e:
            self.skipTest('os.link(): %s' % e)

    def test_samestat(self):
        test_fn1 = os_helper.TESTFN
        test_fn2 = os_helper.TESTFN + "2"
        self.addCleanup(os_helper.unlink, test_fn1)
        self.addCleanup(os_helper.unlink, test_fn2)

        create_file(test_fn1)
        stat1 = os.stat(test_fn1)
        self.assertWahr(self.pathmodule.samestat(stat1, os.stat(test_fn1)))

        create_file(test_fn2)
        stat2 = os.stat(test_fn2)
        self.assertFalsch(self.pathmodule.samestat(stat1, stat2))

        self.assertRaises(TypeError, self.pathmodule.samestat)

    def _test_samestat_on_link_func(self, func):
        test_fn1 = os_helper.TESTFN + "1"
        test_fn2 = os_helper.TESTFN + "2"
        self.addCleanup(os_helper.unlink, test_fn1)
        self.addCleanup(os_helper.unlink, test_fn2)

        create_file(test_fn1)
        func(test_fn1, test_fn2)
        self.assertWahr(self.pathmodule.samestat(os.stat(test_fn1),
                                                 os.stat(test_fn2)))
        os.remove(test_fn2)

        create_file(test_fn2)
        self.assertFalsch(self.pathmodule.samestat(os.stat(test_fn1),
                                                  os.stat(test_fn2)))

    @os_helper.skip_unless_symlink
    def test_samestat_on_symlink(self):
        self._test_samestat_on_link_func(os.symlink)

    @unittest.skipUnless(hasattr(os, 'link'), 'requires os.link')
    def test_samestat_on_link(self):
        try:
            self._test_samestat_on_link_func(os.link)
        except PermissionError als e:
            self.skipTest('os.link(): %s' % e)

    def test_sameopenfile(self):
        filename = os_helper.TESTFN
        self.addCleanup(os_helper.unlink, filename)
        create_file(filename)

        mit open(filename, "rb", 0) als fp1:
            fd1 = fp1.fileno()
            mit open(filename, "rb", 0) als fp2:
                fd2 = fp2.fileno()
                self.assertWahr(self.pathmodule.sameopenfile(fd1, fd2))

    def test_realpath_mode_values(self):
        fuer name in 'ALL_BUT_LAST', 'ALLOW_MISSING':
            mit self.subTest(name):
                mode = getattr(self.pathmodule, name)
                self.assertEqual(repr(mode), 'os.path.' + name)
                self.assertEqual(str(mode), 'os.path.' + name)
                self.assertWahr(mode)
                self.assertIs(copy.copy(mode), mode)
                self.assertIs(copy.deepcopy(mode), mode)
                fuer proto in range(pickle.HIGHEST_PROTOCOL+1):
                    mit self.subTest(protocol=proto):
                        pickled = pickle.dumps(mode, proto)
                        unpickled = pickle.loads(pickled)
                        self.assertIs(unpickled, mode)


klasse TestGenericTest(GenericTest, unittest.TestCase):
    # Issue 16852: GenericTest can't inherit von unittest.TestCase
    # fuer test discovery purposes; CommonTest inherits von GenericTest
    # und is only meant to be inherited by others.
    pathmodule = genericpath

    def test_invalid_paths(self):
        fuer attr in GenericTest.common_attributes:
            # os.path.commonprefix doesn't raise ValueError
            wenn attr == 'commonprefix':
                continue
            func = getattr(self.pathmodule, attr)
            mit self.subTest(attr=attr):
                wenn attr in ('exists', 'isdir', 'isfile'):
                    func('/tmp\udfffabcds')
                    func(b'/tmp\xffabcds')
                    func('/tmp\x00abcds')
                    func(b'/tmp\x00abcds')
                sonst:
                    mit self.assertRaises((OSError, UnicodeEncodeError)):
                        func('/tmp\udfffabcds')
                    mit self.assertRaises((OSError, UnicodeDecodeError)):
                        func(b'/tmp\xffabcds')
                    mit self.assertRaisesRegex(ValueError, 'embedded null'):
                        func('/tmp\x00abcds')
                    mit self.assertRaisesRegex(ValueError, 'embedded null'):
                        func(b'/tmp\x00abcds')

# Following TestCase is nicht supposed to be run von test_genericpath.
# It is inherited by other test modules (ntpath, posixpath).

klasse CommonTest(GenericTest):
    common_attributes = GenericTest.common_attributes + [
        # Properties
        'curdir', 'pardir', 'extsep', 'sep',
        'pathsep', 'defpath', 'altsep', 'devnull',
        # Methods
        'normcase', 'splitdrive', 'expandvars', 'normpath', 'abspath',
        'join', 'split', 'splitext', 'isabs', 'basename', 'dirname',
        'lexists', 'islink', 'ismount', 'expanduser', 'normpath', 'realpath',
    ]

    def test_normcase(self):
        normcase = self.pathmodule.normcase
        # check that normcase() is idempotent
        fuer p in ["FoO/./BaR", b"FoO/./BaR"]:
            p = normcase(p)
            self.assertEqual(p, normcase(p))

        self.assertEqual(normcase(''), '')
        self.assertEqual(normcase(b''), b'')

        # check that normcase raises a TypeError fuer invalid types
        fuer path in (Nichts, Wahr, 0, 2.5, [], bytearray(b''), {'o','o'}):
            self.assertRaises(TypeError, normcase, path)

    def test_splitdrive(self):
        # splitdrive fuer non-NT paths
        splitdrive = self.pathmodule.splitdrive
        self.assertEqual(splitdrive("/foo/bar"), ("", "/foo/bar"))
        self.assertEqual(splitdrive("foo:bar"), ("", "foo:bar"))
        self.assertEqual(splitdrive(":foo:bar"), ("", ":foo:bar"))

        self.assertEqual(splitdrive(b"/foo/bar"), (b"", b"/foo/bar"))
        self.assertEqual(splitdrive(b"foo:bar"), (b"", b"foo:bar"))
        self.assertEqual(splitdrive(b":foo:bar"), (b"", b":foo:bar"))

    def test_expandvars(self):
        expandvars = self.pathmodule.expandvars
        mit os_helper.EnvironmentVarGuard() als env:
            env.clear()
            env["foo"] = "bar"
            env["{foo"] = "baz1"
            env["{foo}"] = "baz2"
            self.assertEqual(expandvars("foo"), "foo")
            self.assertEqual(expandvars("$foo bar"), "bar bar")
            self.assertEqual(expandvars("${foo}bar"), "barbar")
            self.assertEqual(expandvars("$[foo]bar"), "$[foo]bar")
            self.assertEqual(expandvars("$bar bar"), "$bar bar")
            self.assertEqual(expandvars("$?bar"), "$?bar")
            self.assertEqual(expandvars("$foo}bar"), "bar}bar")
            self.assertEqual(expandvars("${foo"), "${foo")
            self.assertEqual(expandvars("${{foo}}"), "baz1}")
            self.assertEqual(expandvars("$foo$foo"), "barbar")
            self.assertEqual(expandvars("$bar$bar"), "$bar$bar")

            self.assertEqual(expandvars(b"foo"), b"foo")
            self.assertEqual(expandvars(b"$foo bar"), b"bar bar")
            self.assertEqual(expandvars(b"${foo}bar"), b"barbar")
            self.assertEqual(expandvars(b"$[foo]bar"), b"$[foo]bar")
            self.assertEqual(expandvars(b"$bar bar"), b"$bar bar")
            self.assertEqual(expandvars(b"$?bar"), b"$?bar")
            self.assertEqual(expandvars(b"$foo}bar"), b"bar}bar")
            self.assertEqual(expandvars(b"${foo"), b"${foo")
            self.assertEqual(expandvars(b"${{foo}}"), b"baz1}")
            self.assertEqual(expandvars(b"$foo$foo"), b"barbar")
            self.assertEqual(expandvars(b"$bar$bar"), b"$bar$bar")

    @unittest.skipUnless(os_helper.FS_NONASCII, 'need os_helper.FS_NONASCII')
    def test_expandvars_nonascii(self):
        expandvars = self.pathmodule.expandvars
        def check(value, expected):
            self.assertEqual(expandvars(value), expected)
        mit os_helper.EnvironmentVarGuard() als env:
            env.clear()
            nonascii = os_helper.FS_NONASCII
            env['spam'] = nonascii
            env[nonascii] = 'ham' + nonascii
            check(nonascii, nonascii)
            check('$spam bar', '%s bar' % nonascii)
            check('${spam}bar', '%sbar' % nonascii)
            check('${%s}bar' % nonascii, 'ham%sbar' % nonascii)
            check('$bar%s bar' % nonascii, '$bar%s bar' % nonascii)
            check('$spam}bar', '%s}bar' % nonascii)

            check(os.fsencode(nonascii), os.fsencode(nonascii))
            check(b'$spam bar', os.fsencode('%s bar' % nonascii))
            check(b'${spam}bar', os.fsencode('%sbar' % nonascii))
            check(os.fsencode('${%s}bar' % nonascii),
                  os.fsencode('ham%sbar' % nonascii))
            check(os.fsencode('$bar%s bar' % nonascii),
                  os.fsencode('$bar%s bar' % nonascii))
            check(b'$spam}bar', os.fsencode('%s}bar' % nonascii))

    def test_abspath(self):
        self.assertIn("foo", self.pathmodule.abspath("foo"))
        mit warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            self.assertIn(b"foo", self.pathmodule.abspath(b"foo"))

        # avoid UnicodeDecodeError on Windows
        undecodable_path = b'' wenn sys.platform == 'win32' sonst b'f\xf2\xf2'

        # Abspath returns bytes when the arg is bytes
        mit warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            fuer path in (b'', b'foo', undecodable_path, b'/foo', b'C:\\'):
                self.assertIsInstance(self.pathmodule.abspath(path), bytes)

    def test_realpath(self):
        self.assertIn("foo", self.pathmodule.realpath("foo"))
        mit warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            self.assertIn(b"foo", self.pathmodule.realpath(b"foo"))

    def test_normpath_issue5827(self):
        # Make sure normpath preserves unicode
        fuer path in ('', '.', '/', '\\', '///foo/.//bar//'):
            self.assertIsInstance(self.pathmodule.normpath(path), str)

    def test_normpath_issue106242(self):
        fuer path in ('\x00', 'foo\x00bar', '\x00\x00', '\x00foo', 'foo\x00'):
            self.assertEqual(self.pathmodule.normpath(path), path)

    def test_abspath_issue3426(self):
        # Check that abspath returns unicode when the arg is unicode
        # mit both ASCII und non-ASCII cwds.
        abspath = self.pathmodule.abspath
        fuer path in ('', 'fuu', 'f\xf9\xf9', '/fuu', 'U:\\'):
            self.assertIsInstance(abspath(path), str)

        unicwd = '\xe7w\xf0'
        try:
            os.fsencode(unicwd)
        except (AttributeError, UnicodeEncodeError):
            # FS encoding is probably ASCII
            pass
        sonst:
            mit os_helper.temp_cwd(unicwd):
                fuer path in ('', 'fuu', 'f\xf9\xf9', '/fuu', 'U:\\'):
                    self.assertIsInstance(abspath(path), str)

    def test_nonascii_abspath(self):
        wenn (
            os_helper.TESTFN_UNDECODABLE
            # Apple platforms und Emscripten/WASI deny the creation of a
            # directory mit an invalid UTF-8 name. Windows allows creating a
            # directory mit an arbitrary bytes name, but fails to enter this
            # directory (when the bytes name is used).
            und sys.platform nicht in {
                "win32", "emscripten", "wasi"
            } und nicht is_apple
        ):
            name = os_helper.TESTFN_UNDECODABLE
        sowenn os_helper.TESTFN_NONASCII:
            name = os_helper.TESTFN_NONASCII
        sonst:
            self.skipTest("need os_helper.TESTFN_NONASCII")

        mit warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            mit os_helper.temp_cwd(name):
                self.test_abspath()

    def test_join_errors(self):
        # Check join() raises friendly TypeErrors.
        mit warnings_helper.check_warnings(('', BytesWarning), quiet=Wahr):
            errmsg = "Can't mix strings und bytes in path components"
            mit self.assertRaisesRegex(TypeError, errmsg):
                self.pathmodule.join(b'bytes', 'str')
            mit self.assertRaisesRegex(TypeError, errmsg):
                self.pathmodule.join('str', b'bytes')
            # regression, see #15377
            mit self.assertRaisesRegex(TypeError, 'int'):
                self.pathmodule.join(42, 'str')
            mit self.assertRaisesRegex(TypeError, 'int'):
                self.pathmodule.join('str', 42)
            mit self.assertRaisesRegex(TypeError, 'int'):
                self.pathmodule.join(42)
            mit self.assertRaisesRegex(TypeError, 'list'):
                self.pathmodule.join([])
            mit self.assertRaisesRegex(TypeError, 'bytearray'):
                self.pathmodule.join(bytearray(b'foo'), bytearray(b'bar'))

    def test_relpath_errors(self):
        # Check relpath() raises friendly TypeErrors.
        mit warnings_helper.check_warnings(
                ('', (BytesWarning, DeprecationWarning)), quiet=Wahr):
            errmsg = "Can't mix strings und bytes in path components"
            mit self.assertRaisesRegex(TypeError, errmsg):
                self.pathmodule.relpath(b'bytes', 'str')
            mit self.assertRaisesRegex(TypeError, errmsg):
                self.pathmodule.relpath('str', b'bytes')
            mit self.assertRaisesRegex(TypeError, 'int'):
                self.pathmodule.relpath(42, 'str')
            mit self.assertRaisesRegex(TypeError, 'int'):
                self.pathmodule.relpath('str', 42)
            mit self.assertRaisesRegex(TypeError, 'bytearray'):
                self.pathmodule.relpath(bytearray(b'foo'), bytearray(b'bar'))

    def test_import(self):
        assert_python_ok('-S', '-c', 'import ' + self.pathmodule.__name__)


klasse PathLikeTests(unittest.TestCase):

    def setUp(self):
        self.file_name = os_helper.TESTFN
        self.file_path = FakePath(os_helper.TESTFN)
        self.addCleanup(os_helper.unlink, self.file_name)
        create_file(self.file_name, b"test_genericpath.PathLikeTests")

    def assertPathEqual(self, func):
        self.assertEqual(func(self.file_path), func(self.file_name))

    def test_path_exists(self):
        self.assertPathEqual(os.path.exists)

    def test_path_isfile(self):
        self.assertPathEqual(os.path.isfile)

    def test_path_isdir(self):
        self.assertPathEqual(os.path.isdir)

    def test_path_commonprefix(self):
        self.assertEqual(os.path.commonprefix([self.file_path, self.file_name]),
                         self.file_name)

    def test_path_getsize(self):
        self.assertPathEqual(os.path.getsize)

    def test_path_getmtime(self):
        self.assertPathEqual(os.path.getatime)

    def test_path_getctime(self):
        self.assertPathEqual(os.path.getctime)

    def test_path_samefile(self):
        self.assertWahr(os.path.samefile(self.file_path, self.file_name))


wenn __name__ == "__main__":
    unittest.main()
