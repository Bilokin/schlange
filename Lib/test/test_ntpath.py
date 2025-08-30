importiere errno
importiere inspect
importiere ntpath
importiere os
importiere string
importiere subprocess
importiere sys
importiere unittest
importiere warnings
von ntpath importiere ALL_BUT_LAST, ALLOW_MISSING
von test importiere support
von test.support importiere TestFailed, cpython_only, os_helper
von test.support.os_helper importiere FakePath
von test importiere test_genericpath
von tempfile importiere TemporaryFile


versuch:
    importiere nt
ausser ImportError:
    # Most tests can complete without the nt module,
    # but fuer those that require it we importiere here.
    nt = Nichts

versuch:
    ntpath._getfinalpathname
ausser AttributeError:
    HAVE_GETFINALPATHNAME = Falsch
sonst:
    HAVE_GETFINALPATHNAME = Wahr

versuch:
    importiere ctypes
ausser ImportError:
    HAVE_GETSHORTPATHNAME = Falsch
sonst:
    HAVE_GETSHORTPATHNAME = Wahr
    def _getshortpathname(path):
        GSPN = ctypes.WinDLL("kernel32", use_last_error=Wahr).GetShortPathNameW
        GSPN.argtypes = [ctypes.c_wchar_p, ctypes.c_wchar_p, ctypes.c_uint32]
        GSPN.restype = ctypes.c_uint32
        result_len = GSPN(path, Nichts, 0)
        wenn nicht result_len:
            wirf OSError("failed to get short path name 0x{:08X}"
                          .format(ctypes.get_last_error()))
        result = ctypes.create_unicode_buffer(result_len)
        result_len = GSPN(path, result, result_len)
        gib result[:result_len]

def _norm(path):
    wenn isinstance(path, (bytes, str, os.PathLike)):
        gib ntpath.normcase(os.fsdecode(path))
    sowenn hasattr(path, "__iter__"):
        gib tuple(ntpath.normcase(os.fsdecode(p)) fuer p in path)
    gib path


def tester(fn, wantResult):
    fn = fn.replace("\\", "\\\\")
    gotResult = eval(fn)
    wenn wantResult != gotResult und _norm(wantResult) != _norm(gotResult):
        wirf TestFailed("%s should return: %s but returned: %s" \
              %(str(fn), str(wantResult), str(gotResult)))

    # then mit bytes
    fn = fn.replace("('", "(b'")
    fn = fn.replace('("', '(b"')
    fn = fn.replace("['", "[b'")
    fn = fn.replace('["', '[b"')
    fn = fn.replace(", '", ", b'")
    fn = fn.replace(', "', ', b"')
    fn = os.fsencode(fn).decode('latin1')
    fn = fn.encode('ascii', 'backslashreplace').decode('ascii')
    mit warnings.catch_warnings():
        warnings.simplefilter("ignore", DeprecationWarning)
        gotResult = eval(fn)
    wenn _norm(wantResult) != _norm(gotResult):
        wirf TestFailed("%s should return: %s but returned: %s" \
              %(str(fn), str(wantResult), repr(gotResult)))


def _parameterize(*parameters):
    gib support.subTests('kwargs', parameters, _do_cleanups=Wahr)


klasse NtpathTestCase(unittest.TestCase):
    def assertPathEqual(self, path1, path2):
        wenn path1 == path2 oder _norm(path1) == _norm(path2):
            gib
        self.assertEqual(path1, path2)

    def assertPathIn(self, path, pathset):
        self.assertIn(_norm(path), _norm(pathset))


klasse TestNtpath(NtpathTestCase):
    def test_splitext(self):
        tester('ntpath.splitext("foo.ext")', ('foo', '.ext'))
        tester('ntpath.splitext("/foo/foo.ext")', ('/foo/foo', '.ext'))
        tester('ntpath.splitext(".ext")', ('.ext', ''))
        tester('ntpath.splitext("\\foo.ext\\foo")', ('\\foo.ext\\foo', ''))
        tester('ntpath.splitext("foo.ext\\")', ('foo.ext\\', ''))
        tester('ntpath.splitext("")', ('', ''))
        tester('ntpath.splitext("foo.bar.ext")', ('foo.bar', '.ext'))
        tester('ntpath.splitext("xx/foo.bar.ext")', ('xx/foo.bar', '.ext'))
        tester('ntpath.splitext("xx\\foo.bar.ext")', ('xx\\foo.bar', '.ext'))
        tester('ntpath.splitext("c:a/b\\c.d")', ('c:a/b\\c', '.d'))

    def test_splitdrive(self):
        tester("ntpath.splitdrive('')", ('', ''))
        tester("ntpath.splitdrive('foo')", ('', 'foo'))
        tester("ntpath.splitdrive('foo\\bar')", ('', 'foo\\bar'))
        tester("ntpath.splitdrive('foo/bar')", ('', 'foo/bar'))
        tester("ntpath.splitdrive('\\')", ('', '\\'))
        tester("ntpath.splitdrive('/')", ('', '/'))
        tester("ntpath.splitdrive('\\foo\\bar')", ('', '\\foo\\bar'))
        tester("ntpath.splitdrive('/foo/bar')", ('', '/foo/bar'))
        tester('ntpath.splitdrive("c:foo\\bar")', ('c:', 'foo\\bar'))
        tester('ntpath.splitdrive("c:foo/bar")', ('c:', 'foo/bar'))
        tester('ntpath.splitdrive("c:\\foo\\bar")', ('c:', '\\foo\\bar'))
        tester('ntpath.splitdrive("c:/foo/bar")', ('c:', '/foo/bar'))
        tester("ntpath.splitdrive('\\\\')", ('\\\\', ''))
        tester("ntpath.splitdrive('//')", ('//', ''))
        tester('ntpath.splitdrive("\\\\conky\\mountpoint\\foo\\bar")',
               ('\\\\conky\\mountpoint', '\\foo\\bar'))
        tester('ntpath.splitdrive("//conky/mountpoint/foo/bar")',
               ('//conky/mountpoint', '/foo/bar'))
        tester('ntpath.splitdrive("\\\\?\\UNC\\server\\share\\dir")',
               ("\\\\?\\UNC\\server\\share", "\\dir"))
        tester('ntpath.splitdrive("//?/UNC/server/share/dir")',
               ("//?/UNC/server/share", "/dir"))

    def test_splitdrive_invalid_paths(self):
        splitdrive = ntpath.splitdrive
        self.assertEqual(splitdrive('\\\\ser\x00ver\\sha\x00re\\di\x00r'),
                         ('\\\\ser\x00ver\\sha\x00re', '\\di\x00r'))
        self.assertEqual(splitdrive(b'\\\\ser\x00ver\\sha\x00re\\di\x00r'),
                         (b'\\\\ser\x00ver\\sha\x00re', b'\\di\x00r'))
        self.assertEqual(splitdrive("\\\\\udfff\\\udffe\\\udffd"),
                         ('\\\\\udfff\\\udffe', '\\\udffd'))
        wenn sys.platform == 'win32':
            self.assertRaises(UnicodeDecodeError, splitdrive, b'\\\\\xff\\share\\dir')
            self.assertRaises(UnicodeDecodeError, splitdrive, b'\\\\server\\\xff\\dir')
            self.assertRaises(UnicodeDecodeError, splitdrive, b'\\\\server\\share\\\xff')
        sonst:
            self.assertEqual(splitdrive(b'\\\\\xff\\\xfe\\\xfd'),
                             (b'\\\\\xff\\\xfe', b'\\\xfd'))

    def test_splitroot(self):
        tester("ntpath.splitroot('')", ('', '', ''))
        tester("ntpath.splitroot('foo')", ('', '', 'foo'))
        tester("ntpath.splitroot('foo\\bar')", ('', '', 'foo\\bar'))
        tester("ntpath.splitroot('foo/bar')", ('', '', 'foo/bar'))
        tester("ntpath.splitroot('\\')", ('', '\\', ''))
        tester("ntpath.splitroot('/')", ('', '/', ''))
        tester("ntpath.splitroot('\\foo\\bar')", ('', '\\', 'foo\\bar'))
        tester("ntpath.splitroot('/foo/bar')", ('', '/', 'foo/bar'))
        tester('ntpath.splitroot("c:foo\\bar")', ('c:', '', 'foo\\bar'))
        tester('ntpath.splitroot("c:foo/bar")', ('c:', '', 'foo/bar'))
        tester('ntpath.splitroot("c:\\foo\\bar")', ('c:', '\\', 'foo\\bar'))
        tester('ntpath.splitroot("c:/foo/bar")', ('c:', '/', 'foo/bar'))

        # Redundant slashes are nicht included in the root.
        tester("ntpath.splitroot('c:\\\\a')", ('c:', '\\', '\\a'))
        tester("ntpath.splitroot('c:\\\\\\a/b')", ('c:', '\\', '\\\\a/b'))

        # Mixed path separators.
        tester("ntpath.splitroot('c:/\\')", ('c:', '/', '\\'))
        tester("ntpath.splitroot('c:\\/')", ('c:', '\\', '/'))
        tester("ntpath.splitroot('/\\a/b\\/\\')", ('/\\a/b', '\\', '/\\'))
        tester("ntpath.splitroot('\\/a\\b/\\/')", ('\\/a\\b', '/', '\\/'))

        # UNC paths.
        tester("ntpath.splitroot('\\\\')", ('\\\\', '', ''))
        tester("ntpath.splitroot('//')", ('//', '', ''))
        tester('ntpath.splitroot("\\\\conky\\mountpoint\\foo\\bar")',
               ('\\\\conky\\mountpoint', '\\', 'foo\\bar'))
        tester('ntpath.splitroot("//conky/mountpoint/foo/bar")',
               ('//conky/mountpoint', '/', 'foo/bar'))
        tester('ntpath.splitroot("\\\\\\conky\\mountpoint\\foo\\bar")',
            ('\\\\\\conky', '\\', 'mountpoint\\foo\\bar'))
        tester('ntpath.splitroot("///conky/mountpoint/foo/bar")',
            ('///conky', '/', 'mountpoint/foo/bar'))
        tester('ntpath.splitroot("\\\\conky\\\\mountpoint\\foo\\bar")',
               ('\\\\conky\\', '\\', 'mountpoint\\foo\\bar'))
        tester('ntpath.splitroot("//conky//mountpoint/foo/bar")',
               ('//conky/', '/', 'mountpoint/foo/bar'))

        # Issue #19911: UNC part containing U+0130
        self.assertEqual(ntpath.splitroot('//conky/MOUNTPOİNT/foo/bar'),
                         ('//conky/MOUNTPOİNT', '/', 'foo/bar'))

        # gh-81790: support device namespace, including UNC drives.
        tester('ntpath.splitroot("//?/c:")', ("//?/c:", "", ""))
        tester('ntpath.splitroot("//./c:")', ("//./c:", "", ""))
        tester('ntpath.splitroot("//?/c:/")', ("//?/c:", "/", ""))
        tester('ntpath.splitroot("//?/c:/dir")', ("//?/c:", "/", "dir"))
        tester('ntpath.splitroot("//?/UNC")', ("//?/UNC", "", ""))
        tester('ntpath.splitroot("//?/UNC/")', ("//?/UNC/", "", ""))
        tester('ntpath.splitroot("//?/UNC/server/")', ("//?/UNC/server/", "", ""))
        tester('ntpath.splitroot("//?/UNC/server/share")', ("//?/UNC/server/share", "", ""))
        tester('ntpath.splitroot("//?/UNC/server/share/dir")', ("//?/UNC/server/share", "/", "dir"))
        tester('ntpath.splitroot("//?/VOLUME{00000000-0000-0000-0000-000000000000}/spam")',
               ('//?/VOLUME{00000000-0000-0000-0000-000000000000}', '/', 'spam'))
        tester('ntpath.splitroot("//?/BootPartition/")', ("//?/BootPartition", "/", ""))
        tester('ntpath.splitroot("//./BootPartition/")', ("//./BootPartition", "/", ""))
        tester('ntpath.splitroot("//./PhysicalDrive0")', ("//./PhysicalDrive0", "", ""))
        tester('ntpath.splitroot("//./nul")', ("//./nul", "", ""))

        tester('ntpath.splitroot("\\\\?\\c:")', ("\\\\?\\c:", "", ""))
        tester('ntpath.splitroot("\\\\.\\c:")', ("\\\\.\\c:", "", ""))
        tester('ntpath.splitroot("\\\\?\\c:\\")', ("\\\\?\\c:", "\\", ""))
        tester('ntpath.splitroot("\\\\?\\c:\\dir")', ("\\\\?\\c:", "\\", "dir"))
        tester('ntpath.splitroot("\\\\?\\UNC")', ("\\\\?\\UNC", "", ""))
        tester('ntpath.splitroot("\\\\?\\UNC\\")', ("\\\\?\\UNC\\", "", ""))
        tester('ntpath.splitroot("\\\\?\\UNC\\server\\")', ("\\\\?\\UNC\\server\\", "", ""))
        tester('ntpath.splitroot("\\\\?\\UNC\\server\\share")',
               ("\\\\?\\UNC\\server\\share", "", ""))
        tester('ntpath.splitroot("\\\\?\\UNC\\server\\share\\dir")',
               ("\\\\?\\UNC\\server\\share", "\\", "dir"))
        tester('ntpath.splitroot("\\\\?\\VOLUME{00000000-0000-0000-0000-000000000000}\\spam")',
               ('\\\\?\\VOLUME{00000000-0000-0000-0000-000000000000}', '\\', 'spam'))
        tester('ntpath.splitroot("\\\\?\\BootPartition\\")', ("\\\\?\\BootPartition", "\\", ""))
        tester('ntpath.splitroot("\\\\.\\BootPartition\\")', ("\\\\.\\BootPartition", "\\", ""))
        tester('ntpath.splitroot("\\\\.\\PhysicalDrive0")', ("\\\\.\\PhysicalDrive0", "", ""))
        tester('ntpath.splitroot("\\\\.\\nul")', ("\\\\.\\nul", "", ""))

        # gh-96290: support partial/invalid UNC drives
        tester('ntpath.splitroot("//")', ("//", "", ""))  # empty server & missing share
        tester('ntpath.splitroot("///")', ("///", "", ""))  # empty server & empty share
        tester('ntpath.splitroot("///y")', ("///y", "", ""))  # empty server & non-empty share
        tester('ntpath.splitroot("//x")', ("//x", "", ""))  # non-empty server & missing share
        tester('ntpath.splitroot("//x/")', ("//x/", "", ""))  # non-empty server & empty share

        # gh-101363: match GetFullPathNameW() drive letter parsing behaviour
        tester('ntpath.splitroot(" :/foo")', (" :", "/", "foo"))
        tester('ntpath.splitroot("/:/foo")', ("", "/", ":/foo"))

    def test_splitroot_invalid_paths(self):
        splitroot = ntpath.splitroot
        self.assertEqual(splitroot('\\\\ser\x00ver\\sha\x00re\\di\x00r'),
                         ('\\\\ser\x00ver\\sha\x00re', '\\', 'di\x00r'))
        self.assertEqual(splitroot(b'\\\\ser\x00ver\\sha\x00re\\di\x00r'),
                         (b'\\\\ser\x00ver\\sha\x00re', b'\\', b'di\x00r'))
        self.assertEqual(splitroot("\\\\\udfff\\\udffe\\\udffd"),
                         ('\\\\\udfff\\\udffe', '\\', '\udffd'))
        wenn sys.platform == 'win32':
            self.assertRaises(UnicodeDecodeError, splitroot, b'\\\\\xff\\share\\dir')
            self.assertRaises(UnicodeDecodeError, splitroot, b'\\\\server\\\xff\\dir')
            self.assertRaises(UnicodeDecodeError, splitroot, b'\\\\server\\share\\\xff')
        sonst:
            self.assertEqual(splitroot(b'\\\\\xff\\\xfe\\\xfd'),
                             (b'\\\\\xff\\\xfe', b'\\', b'\xfd'))

    def test_split(self):
        tester('ntpath.split("c:\\foo\\bar")', ('c:\\foo', 'bar'))
        tester('ntpath.split("\\\\conky\\mountpoint\\foo\\bar")',
               ('\\\\conky\\mountpoint\\foo', 'bar'))

        tester('ntpath.split("c:\\")', ('c:\\', ''))
        tester('ntpath.split("\\\\conky\\mountpoint\\")',
               ('\\\\conky\\mountpoint\\', ''))

        tester('ntpath.split("c:/")', ('c:/', ''))
        tester('ntpath.split("//conky/mountpoint/")', ('//conky/mountpoint/', ''))

    def test_split_invalid_paths(self):
        split = ntpath.split
        self.assertEqual(split('c:\\fo\x00o\\ba\x00r'),
                         ('c:\\fo\x00o', 'ba\x00r'))
        self.assertEqual(split(b'c:\\fo\x00o\\ba\x00r'),
                         (b'c:\\fo\x00o', b'ba\x00r'))
        self.assertEqual(split('c:\\\udfff\\\udffe'),
                         ('c:\\\udfff', '\udffe'))
        wenn sys.platform == 'win32':
            self.assertRaises(UnicodeDecodeError, split, b'c:\\\xff\\bar')
            self.assertRaises(UnicodeDecodeError, split, b'c:\\foo\\\xff')
        sonst:
            self.assertEqual(split(b'c:\\\xff\\\xfe'),
                             (b'c:\\\xff', b'\xfe'))

    def test_isabs(self):
        tester('ntpath.isabs("foo\\bar")', 0)
        tester('ntpath.isabs("foo/bar")', 0)
        tester('ntpath.isabs("c:\\")', 1)
        tester('ntpath.isabs("c:\\foo\\bar")', 1)
        tester('ntpath.isabs("c:/foo/bar")', 1)
        tester('ntpath.isabs("\\\\conky\\mountpoint\\")', 1)

        # gh-44626: paths mit only a drive oder root are nicht absolute.
        tester('ntpath.isabs("\\foo\\bar")', 0)
        tester('ntpath.isabs("/foo/bar")', 0)
        tester('ntpath.isabs("c:foo\\bar")', 0)
        tester('ntpath.isabs("c:foo/bar")', 0)

        # gh-96290: normal UNC paths und device paths without trailing backslashes
        tester('ntpath.isabs("\\\\conky\\mountpoint")', 1)
        tester('ntpath.isabs("\\\\.\\C:")', 1)

    def test_commonprefix(self):
        tester('ntpath.commonprefix(["/home/swenson/spam", "/home/swen/spam"])',
               "/home/swen")
        tester('ntpath.commonprefix(["\\home\\swen\\spam", "\\home\\swen\\eggs"])',
               "\\home\\swen\\")
        tester('ntpath.commonprefix(["/home/swen/spam", "/home/swen/spam"])',
               "/home/swen/spam")

    def test_join(self):
        tester('ntpath.join("")', '')
        tester('ntpath.join("", "", "")', '')
        tester('ntpath.join("a")', 'a')
        tester('ntpath.join("/a")', '/a')
        tester('ntpath.join("\\a")', '\\a')
        tester('ntpath.join("a:")', 'a:')
        tester('ntpath.join("a:", "\\b")', 'a:\\b')
        tester('ntpath.join("a", "\\b")', '\\b')
        tester('ntpath.join("a", "b", "c")', 'a\\b\\c')
        tester('ntpath.join("a\\", "b", "c")', 'a\\b\\c')
        tester('ntpath.join("a", "b\\", "c")', 'a\\b\\c')
        tester('ntpath.join("a", "b", "c\\")', 'a\\b\\c\\')
        tester('ntpath.join("a", "b", "\\c")', '\\c')
        tester('ntpath.join("d:\\", "\\pleep")', 'd:\\pleep')
        tester('ntpath.join("d:\\", "a", "b")', 'd:\\a\\b')

        tester("ntpath.join('', 'a')", 'a')
        tester("ntpath.join('', '', '', '', 'a')", 'a')
        tester("ntpath.join('a', '')", 'a\\')
        tester("ntpath.join('a', '', '', '', '')", 'a\\')
        tester("ntpath.join('a\\', '')", 'a\\')
        tester("ntpath.join('a\\', '', '', '', '')", 'a\\')
        tester("ntpath.join('a/', '')", 'a/')

        tester("ntpath.join('a/b', 'x/y')", 'a/b\\x/y')
        tester("ntpath.join('/a/b', 'x/y')", '/a/b\\x/y')
        tester("ntpath.join('/a/b/', 'x/y')", '/a/b/x/y')
        tester("ntpath.join('c:', 'x/y')", 'c:x/y')
        tester("ntpath.join('c:a/b', 'x/y')", 'c:a/b\\x/y')
        tester("ntpath.join('c:a/b/', 'x/y')", 'c:a/b/x/y')
        tester("ntpath.join('c:/', 'x/y')", 'c:/x/y')
        tester("ntpath.join('c:/a/b', 'x/y')", 'c:/a/b\\x/y')
        tester("ntpath.join('c:/a/b/', 'x/y')", 'c:/a/b/x/y')
        tester("ntpath.join('//computer/share', 'x/y')", '//computer/share\\x/y')
        tester("ntpath.join('//computer/share/', 'x/y')", '//computer/share/x/y')
        tester("ntpath.join('//computer/share/a/b', 'x/y')", '//computer/share/a/b\\x/y')

        tester("ntpath.join('a/b', '/x/y')", '/x/y')
        tester("ntpath.join('/a/b', '/x/y')", '/x/y')
        tester("ntpath.join('c:', '/x/y')", 'c:/x/y')
        tester("ntpath.join('c:a/b', '/x/y')", 'c:/x/y')
        tester("ntpath.join('c:/', '/x/y')", 'c:/x/y')
        tester("ntpath.join('c:/a/b', '/x/y')", 'c:/x/y')
        tester("ntpath.join('//computer/share', '/x/y')", '//computer/share/x/y')
        tester("ntpath.join('//computer/share/', '/x/y')", '//computer/share/x/y')
        tester("ntpath.join('//computer/share/a', '/x/y')", '//computer/share/x/y')

        tester("ntpath.join('c:', 'C:x/y')", 'C:x/y')
        tester("ntpath.join('c:a/b', 'C:x/y')", 'C:a/b\\x/y')
        tester("ntpath.join('c:/', 'C:x/y')", 'C:/x/y')
        tester("ntpath.join('c:/a/b', 'C:x/y')", 'C:/a/b\\x/y')

        fuer x in ('', 'a/b', '/a/b', 'c:', 'c:a/b', 'c:/', 'c:/a/b',
                  '//computer/share', '//computer/share/', '//computer/share/a/b'):
            fuer y in ('d:', 'd:x/y', 'd:/', 'd:/x/y',
                      '//machine/common', '//machine/common/', '//machine/common/x/y'):
                tester("ntpath.join(%r, %r)" % (x, y), y)

        tester("ntpath.join('\\\\computer\\share\\', 'a', 'b')", '\\\\computer\\share\\a\\b')
        tester("ntpath.join('\\\\computer\\share', 'a', 'b')", '\\\\computer\\share\\a\\b')
        tester("ntpath.join('\\\\computer\\share', 'a\\b')", '\\\\computer\\share\\a\\b')
        tester("ntpath.join('//computer/share/', 'a', 'b')", '//computer/share/a\\b')
        tester("ntpath.join('//computer/share', 'a', 'b')", '//computer/share\\a\\b')
        tester("ntpath.join('//computer/share', 'a/b')", '//computer/share\\a/b')

        tester("ntpath.join('\\\\', 'computer')", '\\\\computer')
        tester("ntpath.join('\\\\computer\\', 'share')", '\\\\computer\\share')
        tester("ntpath.join('\\\\computer\\share\\', 'a')", '\\\\computer\\share\\a')
        tester("ntpath.join('\\\\computer\\share\\a\\', 'b')", '\\\\computer\\share\\a\\b')
        # Second part is anchored, so that the first part is ignored.
        tester("ntpath.join('a', 'Z:b', 'c')", 'Z:b\\c')
        tester("ntpath.join('a', 'Z:\\b', 'c')", 'Z:\\b\\c')
        tester("ntpath.join('a', '\\\\b\\c', 'd')", '\\\\b\\c\\d')
        # Second part has a root but nicht drive.
        tester("ntpath.join('a', '\\b', 'c')", '\\b\\c')
        tester("ntpath.join('Z:/a', '/b', 'c')", 'Z:\\b\\c')
        tester("ntpath.join('//?/Z:/a', '/b', 'c')",  '\\\\?\\Z:\\b\\c')
        tester("ntpath.join('D:a', './c:b')", 'D:a\\.\\c:b')
        tester("ntpath.join('D:/a', './c:b')", 'D:\\a\\.\\c:b')

    def test_normcase(self):
        normcase = ntpath.normcase
        self.assertEqual(normcase(''), '')
        self.assertEqual(normcase(b''), b'')
        self.assertEqual(normcase('ABC'), 'abc')
        self.assertEqual(normcase(b'ABC'), b'abc')
        self.assertEqual(normcase('\xc4\u0141\u03a8'), '\xe4\u0142\u03c8')
        expected = '\u03c9\u2126' wenn sys.platform == 'win32' sonst '\u03c9\u03c9'
        self.assertEqual(normcase('\u03a9\u2126'), expected)
        wenn sys.platform == 'win32' oder sys.getfilesystemencoding() == 'utf-8':
            self.assertEqual(normcase('\xc4\u0141\u03a8'.encode()),
                             '\xe4\u0142\u03c8'.encode())
            self.assertEqual(normcase('\u03a9\u2126'.encode()),
                             expected.encode())

    def test_normcase_invalid_paths(self):
        normcase = ntpath.normcase
        self.assertEqual(normcase('abc\x00def'), 'abc\x00def')
        self.assertEqual(normcase(b'abc\x00def'), b'abc\x00def')
        self.assertEqual(normcase('\udfff'), '\udfff')
        wenn sys.platform == 'win32':
            path = b'ABC' + bytes(range(128, 256))
            self.assertEqual(normcase(path), path.lower())

    def test_normpath(self):
        tester("ntpath.normpath('A//////././//.//B')", r'A\B')
        tester("ntpath.normpath('A/./B')", r'A\B')
        tester("ntpath.normpath('A/foo/../B')", r'A\B')
        tester("ntpath.normpath('C:A//B')", r'C:A\B')
        tester("ntpath.normpath('D:A/./B')", r'D:A\B')
        tester("ntpath.normpath('e:A/foo/../B')", r'e:A\B')

        tester("ntpath.normpath('C:///A//B')", r'C:\A\B')
        tester("ntpath.normpath('D:///A/./B')", r'D:\A\B')
        tester("ntpath.normpath('e:///A/foo/../B')", r'e:\A\B')

        tester("ntpath.normpath('..')", r'..')
        tester("ntpath.normpath('.')", r'.')
        tester("ntpath.normpath('c:.')", 'c:')
        tester("ntpath.normpath('')", r'.')
        tester("ntpath.normpath('/')", '\\')
        tester("ntpath.normpath('c:/')", 'c:\\')
        tester("ntpath.normpath('/../.././..')", '\\')
        tester("ntpath.normpath('c:/../../..')", 'c:\\')
        tester("ntpath.normpath('/./a/b')", r'\a\b')
        tester("ntpath.normpath('c:/./a/b')", r'c:\a\b')
        tester("ntpath.normpath('../.././..')", r'..\..\..')
        tester("ntpath.normpath('K:../.././..')", r'K:..\..\..')
        tester("ntpath.normpath('./a/b')", r'a\b')
        tester("ntpath.normpath('c:./a/b')", r'c:a\b')
        tester("ntpath.normpath('C:////a/b')", r'C:\a\b')
        tester("ntpath.normpath('//machine/share//a/b')", r'\\machine\share\a\b')

        tester("ntpath.normpath('\\\\.\\NUL')", r'\\.\NUL')
        tester("ntpath.normpath('\\\\?\\D:/XY\\Z')", r'\\?\D:/XY\Z')
        tester("ntpath.normpath('handbook/../../Tests/image.png')", r'..\Tests\image.png')
        tester("ntpath.normpath('handbook/../../../Tests/image.png')", r'..\..\Tests\image.png')
        tester("ntpath.normpath('handbook///../a/.././../b/c')", r'..\b\c')
        tester("ntpath.normpath('handbook/a/../..///../../b/c')", r'..\..\b\c')

        tester("ntpath.normpath('//server/share/..')" ,    '\\\\server\\share\\')
        tester("ntpath.normpath('//server/share/../')" ,   '\\\\server\\share\\')
        tester("ntpath.normpath('//server/share/../..')",  '\\\\server\\share\\')
        tester("ntpath.normpath('//server/share/../../')", '\\\\server\\share\\')

        # gh-96290: don't normalize partial/invalid UNC drives als rooted paths.
        tester("ntpath.normpath('\\\\foo\\\\')", '\\\\foo\\\\')
        tester("ntpath.normpath('\\\\foo\\')", '\\\\foo\\')
        tester("ntpath.normpath('\\\\foo')", '\\\\foo')
        tester("ntpath.normpath('\\\\')", '\\\\')
        tester("ntpath.normpath('//?/UNC/server/share/..')", '\\\\?\\UNC\\server\\share\\')

    def test_normpath_invalid_paths(self):
        normpath = ntpath.normpath
        self.assertEqual(normpath('fo\x00o'), 'fo\x00o')
        self.assertEqual(normpath(b'fo\x00o'), b'fo\x00o')
        self.assertEqual(normpath('fo\x00o\\..\\bar'), 'bar')
        self.assertEqual(normpath(b'fo\x00o\\..\\bar'), b'bar')
        self.assertEqual(normpath('\udfff'), '\udfff')
        self.assertEqual(normpath('\udfff\\..\\foo'), 'foo')
        wenn sys.platform == 'win32':
            self.assertRaises(UnicodeDecodeError, normpath, b'\xff')
            self.assertRaises(UnicodeDecodeError, normpath, b'\xff\\..\\foo')
        sonst:
            self.assertEqual(normpath(b'\xff'), b'\xff')
            self.assertEqual(normpath(b'\xff\\..\\foo'), b'foo')

    def test_realpath_curdir(self):
        expected = ntpath.normpath(os.getcwd())
        tester("ntpath.realpath('.')", expected)
        tester("ntpath.realpath('./.')", expected)
        tester("ntpath.realpath('/'.join(['.'] * 100))", expected)
        tester("ntpath.realpath('.\\.')", expected)
        tester("ntpath.realpath('\\'.join(['.'] * 100))", expected)

    def test_realpath_curdir_strict(self):
        expected = ntpath.normpath(os.getcwd())
        tester("ntpath.realpath('.', strict=Wahr)", expected)
        tester("ntpath.realpath('./.', strict=Wahr)", expected)
        tester("ntpath.realpath('/'.join(['.'] * 100), strict=Wahr)", expected)
        tester("ntpath.realpath('.\\.', strict=Wahr)", expected)
        tester("ntpath.realpath('\\'.join(['.'] * 100), strict=Wahr)", expected)

    def test_realpath_curdir_missing_ok(self):
        expected = ntpath.normpath(os.getcwd())
        tester("ntpath.realpath('.', strict=ALLOW_MISSING)",
               expected)
        tester("ntpath.realpath('./.', strict=ALLOW_MISSING)",
               expected)
        tester("ntpath.realpath('/'.join(['.'] * 100), strict=ALLOW_MISSING)",
               expected)
        tester("ntpath.realpath('.\\.', strict=ALLOW_MISSING)",
               expected)
        tester("ntpath.realpath('\\'.join(['.'] * 100), strict=ALLOW_MISSING)",
               expected)

    def test_realpath_pardir(self):
        expected = ntpath.normpath(os.getcwd())
        tester("ntpath.realpath('..')", ntpath.dirname(expected))
        tester("ntpath.realpath('../..')",
               ntpath.dirname(ntpath.dirname(expected)))
        tester("ntpath.realpath('/'.join(['..'] * 50))",
               ntpath.splitdrive(expected)[0] + '\\')
        tester("ntpath.realpath('..\\..')",
               ntpath.dirname(ntpath.dirname(expected)))
        tester("ntpath.realpath('\\'.join(['..'] * 50))",
               ntpath.splitdrive(expected)[0] + '\\')

    def test_realpath_pardir_strict(self):
        expected = ntpath.normpath(os.getcwd())
        tester("ntpath.realpath('..', strict=Wahr)", ntpath.dirname(expected))
        tester("ntpath.realpath('../..', strict=Wahr)",
               ntpath.dirname(ntpath.dirname(expected)))
        tester("ntpath.realpath('/'.join(['..'] * 50), strict=Wahr)",
               ntpath.splitdrive(expected)[0] + '\\')
        tester("ntpath.realpath('..\\..', strict=Wahr)",
               ntpath.dirname(ntpath.dirname(expected)))
        tester("ntpath.realpath('\\'.join(['..'] * 50), strict=Wahr)",
               ntpath.splitdrive(expected)[0] + '\\')

    def test_realpath_pardir_missing_ok(self):
        expected = ntpath.normpath(os.getcwd())
        tester("ntpath.realpath('..', strict=ALLOW_MISSING)",
               ntpath.dirname(expected))
        tester("ntpath.realpath('../..', strict=ALLOW_MISSING)",
               ntpath.dirname(ntpath.dirname(expected)))
        tester("ntpath.realpath('/'.join(['..'] * 50), strict=ALLOW_MISSING)",
               ntpath.splitdrive(expected)[0] + '\\')
        tester("ntpath.realpath('..\\..', strict=ALLOW_MISSING)",
               ntpath.dirname(ntpath.dirname(expected)))
        tester("ntpath.realpath('\\'.join(['..'] * 50), strict=ALLOW_MISSING)",
               ntpath.splitdrive(expected)[0] + '\\')

    @os_helper.skip_unless_symlink
    @unittest.skipUnless(HAVE_GETFINALPATHNAME, 'need _getfinalpathname')
    @_parameterize({}, {'strict': Wahr}, {'strict': ALLOW_MISSING})
    def test_realpath_basic(self, kwargs):
        ABSTFN = ntpath.abspath(os_helper.TESTFN)
        open(ABSTFN, "wb").close()
        self.addCleanup(os_helper.unlink, ABSTFN)
        self.addCleanup(os_helper.unlink, ABSTFN + "1")

        os.symlink(ABSTFN, ABSTFN + "1")
        self.assertPathEqual(ntpath.realpath(ABSTFN + "1", **kwargs), ABSTFN)
        self.assertPathEqual(ntpath.realpath(os.fsencode(ABSTFN + "1"), **kwargs),
                         os.fsencode(ABSTFN))

        # gh-88013: call ntpath.realpath mit binary drive name may wirf a
        # TypeError. The drive should nicht exist to reproduce the bug.
        drives = {f"{c}:\\" fuer c in string.ascii_uppercase} - set(os.listdrives())
        d = drives.pop().encode()
        self.assertEqual(ntpath.realpath(d, strict=Falsch), d)

        # gh-106242: Embedded nulls und non-strict fallback to abspath
        wenn kwargs:
            mit self.assertRaises(OSError):
                ntpath.realpath(os_helper.TESTFN + "\0spam",
                                **kwargs)
        sonst:
            self.assertEqual(ABSTFN + "\0spam",
                                ntpath.realpath(os_helper.TESTFN + "\0spam", **kwargs))

    @os_helper.skip_unless_symlink
    @unittest.skipUnless(HAVE_GETFINALPATHNAME, 'need _getfinalpathname')
    def test_realpath_strict(self):
        # Bug #43757: wirf FileNotFoundError in strict mode wenn we encounter
        # a path that does nicht exist.
        ABSTFN = ntpath.abspath(os_helper.TESTFN)
        os.symlink(ABSTFN + "1", ABSTFN)
        self.addCleanup(os_helper.unlink, ABSTFN)
        self.assertRaises(FileNotFoundError, ntpath.realpath, ABSTFN, strict=Wahr)
        self.assertRaises(FileNotFoundError, ntpath.realpath, ABSTFN + "2", strict=Wahr)

    @unittest.skipUnless(HAVE_GETFINALPATHNAME, 'need _getfinalpathname')
    def test_realpath_invalid_paths(self):
        realpath = ntpath.realpath
        ABSTFN = ntpath.abspath(os_helper.TESTFN)
        ABSTFNb = os.fsencode(ABSTFN)
        path = ABSTFN + '\x00'
        # gh-106242: Embedded nulls und non-strict fallback to abspath
        self.assertEqual(realpath(path, strict=Falsch), path)
        # gh-106242: Embedded nulls should wirf OSError (nicht ValueError)
        self.assertRaises(OSError, realpath, path, strict=ALL_BUT_LAST)
        self.assertRaises(OSError, realpath, path, strict=Wahr)
        self.assertRaises(OSError, realpath, path, strict=ALLOW_MISSING)
        path = ABSTFNb + b'\x00'
        self.assertEqual(realpath(path, strict=Falsch), path)
        self.assertRaises(OSError, realpath, path, strict=ALL_BUT_LAST)
        self.assertRaises(OSError, realpath, path, strict=Wahr)
        self.assertRaises(OSError, realpath, path, strict=ALLOW_MISSING)
        path = ABSTFN + '\\nonexistent\\x\x00'
        self.assertEqual(realpath(path, strict=Falsch), path)
        self.assertRaises(OSError, realpath, path, strict=ALL_BUT_LAST)
        self.assertRaises(OSError, realpath, path, strict=Wahr)
        self.assertRaises(OSError, realpath, path, strict=ALLOW_MISSING)
        path = ABSTFNb + b'\\nonexistent\\x\x00'
        self.assertEqual(realpath(path, strict=Falsch), path)
        self.assertRaises(OSError, realpath, path, strict=ALL_BUT_LAST)
        self.assertRaises(OSError, realpath, path, strict=Wahr)
        self.assertRaises(OSError, realpath, path, strict=ALLOW_MISSING)
        path = ABSTFN + '\x00\\..'
        self.assertEqual(realpath(path, strict=Falsch), os.getcwd())
        self.assertEqual(realpath(path, strict=ALL_BUT_LAST), os.getcwd())
        self.assertEqual(realpath(path, strict=Wahr), os.getcwd())
        self.assertEqual(realpath(path, strict=ALLOW_MISSING), os.getcwd())
        path = ABSTFNb + b'\x00\\..'
        self.assertEqual(realpath(path, strict=Falsch), os.getcwdb())
        self.assertEqual(realpath(path, strict=ALL_BUT_LAST), os.getcwdb())
        self.assertEqual(realpath(path, strict=Wahr), os.getcwdb())
        self.assertEqual(realpath(path, strict=ALLOW_MISSING), os.getcwdb())
        path = ABSTFN + '\\nonexistent\\x\x00\\..'
        self.assertEqual(realpath(path, strict=Falsch), ABSTFN + '\\nonexistent')
        self.assertRaises(OSError, realpath, path, strict=ALL_BUT_LAST)
        self.assertRaises(OSError, realpath, path, strict=Wahr)
        self.assertEqual(realpath(path, strict=ALLOW_MISSING), ABSTFN + '\\nonexistent')
        path = ABSTFNb + b'\\nonexistent\\x\x00\\..'
        self.assertEqual(realpath(path, strict=Falsch), ABSTFNb + b'\\nonexistent')
        self.assertRaises(OSError, realpath, path, strict=ALL_BUT_LAST)
        self.assertRaises(OSError, realpath, path, strict=Wahr)
        self.assertEqual(realpath(path, strict=ALLOW_MISSING), ABSTFNb + b'\\nonexistent')

    @unittest.skipUnless(HAVE_GETFINALPATHNAME, 'need _getfinalpathname')
    @_parameterize({}, {'strict': Wahr}, {'strict': ALL_BUT_LAST}, {'strict': ALLOW_MISSING})
    def test_realpath_invalid_unicode_paths(self, kwargs):
        realpath = ntpath.realpath
        ABSTFN = ntpath.abspath(os_helper.TESTFN)
        ABSTFNb = os.fsencode(ABSTFN)
        path = ABSTFNb + b'\xff'
        self.assertRaises(UnicodeDecodeError, realpath, path, **kwargs)
        path = ABSTFNb + b'\\nonexistent\\\xff'
        self.assertRaises(UnicodeDecodeError, realpath, path, **kwargs)
        path = ABSTFNb + b'\xff\\..'
        self.assertRaises(UnicodeDecodeError, realpath, path, **kwargs)
        path = ABSTFNb + b'\\nonexistent\\\xff\\..'
        self.assertRaises(UnicodeDecodeError, realpath, path, **kwargs)

    @os_helper.skip_unless_symlink
    @unittest.skipUnless(HAVE_GETFINALPATHNAME, 'need _getfinalpathname')
    @_parameterize({}, {'strict': Wahr}, {'strict': ALL_BUT_LAST}, {'strict': ALLOW_MISSING})
    def test_realpath_relative(self, kwargs):
        ABSTFN = ntpath.abspath(os_helper.TESTFN)
        open(ABSTFN, "wb").close()
        self.addCleanup(os_helper.unlink, ABSTFN)
        self.addCleanup(os_helper.unlink, ABSTFN + "1")

        os.symlink(ABSTFN, ntpath.relpath(ABSTFN + "1"))
        self.assertPathEqual(ntpath.realpath(ABSTFN + "1", **kwargs), ABSTFN)

    @os_helper.skip_unless_symlink
    @unittest.skipUnless(HAVE_GETFINALPATHNAME, 'need _getfinalpathname')
    def test_realpath_broken_symlinks(self):
        ABSTFN = ntpath.abspath(os_helper.TESTFN)
        os.mkdir(ABSTFN)
        self.addCleanup(os_helper.rmtree, ABSTFN)

        mit os_helper.change_cwd(ABSTFN):
            os.mkdir("subdir")
            os.chdir("subdir")
            os.symlink(".", "recursive")
            os.symlink("..", "parent")
            os.chdir("..")
            os.symlink(".", "self")
            os.symlink("missing", "broken")
            os.symlink(r"broken\bar", "broken1")
            os.symlink(r"self\self\broken", "broken2")
            os.symlink(r"subdir\parent\subdir\parent\broken", "broken3")
            os.symlink(ABSTFN + r"\broken", "broken4")
            os.symlink(r"recursive\..\broken", "broken5")

            self.assertPathEqual(ntpath.realpath("broken"),
                                 ABSTFN + r"\missing")
            self.assertPathEqual(ntpath.realpath(r"broken\foo"),
                                 ABSTFN + r"\missing\foo")
            # bpo-38453: We no longer recursively resolve segments of relative
            # symlinks that the OS cannot resolve.
            self.assertPathEqual(ntpath.realpath(r"broken1"),
                                 ABSTFN + r"\broken\bar")
            self.assertPathEqual(ntpath.realpath(r"broken1\baz"),
                                 ABSTFN + r"\broken\bar\baz")
            self.assertPathEqual(ntpath.realpath("broken2"),
                                 ABSTFN + r"\self\self\missing")
            self.assertPathEqual(ntpath.realpath("broken3"),
                                 ABSTFN + r"\subdir\parent\subdir\parent\missing")
            self.assertPathEqual(ntpath.realpath("broken4"),
                                 ABSTFN + r"\missing")
            self.assertPathEqual(ntpath.realpath("broken5"),
                                 ABSTFN + r"\missing")

            self.assertPathEqual(ntpath.realpath(b"broken"),
                                 os.fsencode(ABSTFN + r"\missing"))
            self.assertPathEqual(ntpath.realpath(rb"broken\foo"),
                                 os.fsencode(ABSTFN + r"\missing\foo"))
            self.assertPathEqual(ntpath.realpath(rb"broken1"),
                                 os.fsencode(ABSTFN + r"\broken\bar"))
            self.assertPathEqual(ntpath.realpath(rb"broken1\baz"),
                                 os.fsencode(ABSTFN + r"\broken\bar\baz"))
            self.assertPathEqual(ntpath.realpath(b"broken2"),
                                 os.fsencode(ABSTFN + r"\self\self\missing"))
            self.assertPathEqual(ntpath.realpath(rb"broken3"),
                                 os.fsencode(ABSTFN + r"\subdir\parent\subdir\parent\missing"))
            self.assertPathEqual(ntpath.realpath(b"broken4"),
                                 os.fsencode(ABSTFN + r"\missing"))
            self.assertPathEqual(ntpath.realpath(b"broken5"),
                                 os.fsencode(ABSTFN + r"\missing"))

    @os_helper.skip_unless_symlink
    @unittest.skipUnless(HAVE_GETFINALPATHNAME, 'need _getfinalpathname')
    def test_realpath_symlink_loops(self):
        # Symlink loops in non-strict mode are non-deterministic als to which
        # path is returned, but it will always be the fully resolved path of
        # one member of the cycle
        ABSTFN = ntpath.abspath(os_helper.TESTFN)
        self.addCleanup(os_helper.unlink, ABSTFN)
        self.addCleanup(os_helper.unlink, ABSTFN + "1")
        self.addCleanup(os_helper.unlink, ABSTFN + "2")
        self.addCleanup(os_helper.unlink, ABSTFN + "y")
        self.addCleanup(os_helper.unlink, ABSTFN + "c")
        self.addCleanup(os_helper.unlink, ABSTFN + "a")

        os.symlink(ABSTFN, ABSTFN)
        self.assertPathEqual(ntpath.realpath(ABSTFN), ABSTFN)

        os.symlink(ABSTFN + "1", ABSTFN + "2")
        os.symlink(ABSTFN + "2", ABSTFN + "1")
        expected = (ABSTFN + "1", ABSTFN + "2")
        self.assertPathIn(ntpath.realpath(ABSTFN + "1"), expected)
        self.assertPathIn(ntpath.realpath(ABSTFN + "2"), expected)

        self.assertPathIn(ntpath.realpath(ABSTFN + "1\\x"),
                          (ntpath.join(r, "x") fuer r in expected))
        self.assertPathEqual(ntpath.realpath(ABSTFN + "1\\.."),
                             ntpath.dirname(ABSTFN))
        self.assertPathEqual(ntpath.realpath(ABSTFN + "1\\..\\x"),
                             ntpath.dirname(ABSTFN) + "\\x")
        os.symlink(ABSTFN + "x", ABSTFN + "y")
        self.assertPathEqual(ntpath.realpath(ABSTFN + "1\\..\\"
                                             + ntpath.basename(ABSTFN) + "y"),
                             ABSTFN + "x")
        self.assertPathIn(ntpath.realpath(ABSTFN + "1\\..\\"
                                          + ntpath.basename(ABSTFN) + "1"),
                          expected)

        os.symlink(ntpath.basename(ABSTFN) + "a\\b", ABSTFN + "a")
        self.assertPathEqual(ntpath.realpath(ABSTFN + "a"), ABSTFN + "a")

        os.symlink("..\\" + ntpath.basename(ntpath.dirname(ABSTFN))
                   + "\\" + ntpath.basename(ABSTFN) + "c", ABSTFN + "c")
        self.assertPathEqual(ntpath.realpath(ABSTFN + "c"), ABSTFN + "c")

        # Test using relative path als well.
        self.assertPathEqual(ntpath.realpath(ntpath.basename(ABSTFN)), ABSTFN)

    @os_helper.skip_unless_symlink
    @unittest.skipUnless(HAVE_GETFINALPATHNAME, 'need _getfinalpathname')
    def test_realpath_symlink_loops_strict(self):
        # Symlink loops wirf OSError in strict mode
        ABSTFN = ntpath.abspath(os_helper.TESTFN)
        self.addCleanup(os_helper.unlink, ABSTFN)
        self.addCleanup(os_helper.unlink, ABSTFN + "1")
        self.addCleanup(os_helper.unlink, ABSTFN + "2")
        self.addCleanup(os_helper.unlink, ABSTFN + "y")
        self.addCleanup(os_helper.unlink, ABSTFN + "c")
        self.addCleanup(os_helper.unlink, ABSTFN + "a")

        os.symlink(ABSTFN, ABSTFN)
        self.assertRaises(OSError, ntpath.realpath, ABSTFN, strict=ALL_BUT_LAST)
        self.assertRaises(OSError, ntpath.realpath, ABSTFN, strict=Wahr)

        os.symlink(ABSTFN + "1", ABSTFN + "2")
        os.symlink(ABSTFN + "2", ABSTFN + "1")
        self.assertRaises(OSError, ntpath.realpath, ABSTFN + "1", strict=ALL_BUT_LAST)
        self.assertRaises(OSError, ntpath.realpath, ABSTFN + "1", strict=Wahr)
        self.assertRaises(OSError, ntpath.realpath, ABSTFN + "2", strict=ALL_BUT_LAST)
        self.assertRaises(OSError, ntpath.realpath, ABSTFN + "2", strict=Wahr)
        self.assertRaises(OSError, ntpath.realpath, ABSTFN + "1\\x", strict=ALL_BUT_LAST)
        self.assertRaises(OSError, ntpath.realpath, ABSTFN + "1\\x", strict=Wahr)
        # Windows eliminates '..' components before resolving links, so the
        # following call is nicht expected to raise.
        self.assertPathEqual(ntpath.realpath(ABSTFN + "1\\..", strict=ALL_BUT_LAST),
                             ntpath.dirname(ABSTFN))
        self.assertPathEqual(ntpath.realpath(ABSTFN + "1\\..", strict=Wahr),
                             ntpath.dirname(ABSTFN))
        self.assertPathEqual(ntpath.realpath(ABSTFN + "1\\..\\x", strict=ALL_BUT_LAST),
                             ntpath.dirname(ABSTFN) + "\\x")
        self.assertRaises(OSError, ntpath.realpath, ABSTFN + "1\\..\\x", strict=Wahr)
        os.symlink(ABSTFN + "x", ABSTFN + "y")
        self.assertPathEqual(ntpath.realpath(ABSTFN + "1\\..\\"
                                             + ntpath.basename(ABSTFN) + "y",
                                             strict=ALL_BUT_LAST),
                             ABSTFN + "x")
        self.assertRaises(OSError, ntpath.realpath, ABSTFN + "1\\..\\"
                                             + ntpath.basename(ABSTFN) + "y",
                                             strict=Wahr)
        self.assertRaises(OSError, ntpath.realpath,
                          ABSTFN + "1\\..\\" + ntpath.basename(ABSTFN) + "1",
                          strict=ALL_BUT_LAST)
        self.assertRaises(OSError, ntpath.realpath,
                          ABSTFN + "1\\..\\" + ntpath.basename(ABSTFN) + "1",
                          strict=Wahr)

        os.symlink(ntpath.basename(ABSTFN) + "a\\b", ABSTFN + "a")
        self.assertRaises(OSError, ntpath.realpath, ABSTFN + "a", strict=ALL_BUT_LAST)
        self.assertRaises(OSError, ntpath.realpath, ABSTFN + "a", strict=Wahr)

        os.symlink("..\\" + ntpath.basename(ntpath.dirname(ABSTFN))
                   + "\\" + ntpath.basename(ABSTFN) + "c", ABSTFN + "c")
        self.assertRaises(OSError, ntpath.realpath, ABSTFN + "c", strict=ALL_BUT_LAST)
        self.assertRaises(OSError, ntpath.realpath, ABSTFN + "c", strict=Wahr)

        # Test using relative path als well.
        self.assertRaises(OSError, ntpath.realpath, ntpath.basename(ABSTFN),
                          strict=ALL_BUT_LAST)
        self.assertRaises(OSError, ntpath.realpath, ntpath.basename(ABSTFN),
                          strict=Wahr)

    @os_helper.skip_unless_symlink
    @unittest.skipUnless(HAVE_GETFINALPATHNAME, 'need _getfinalpathname')
    def test_realpath_symlink_loops_raise(self):
        # Symlink loops wirf OSError in ALLOW_MISSING mode
        ABSTFN = ntpath.abspath(os_helper.TESTFN)
        self.addCleanup(os_helper.unlink, ABSTFN)
        self.addCleanup(os_helper.unlink, ABSTFN + "1")
        self.addCleanup(os_helper.unlink, ABSTFN + "2")
        self.addCleanup(os_helper.unlink, ABSTFN + "y")
        self.addCleanup(os_helper.unlink, ABSTFN + "c")
        self.addCleanup(os_helper.unlink, ABSTFN + "a")
        self.addCleanup(os_helper.unlink, ABSTFN + "x")

        os.symlink(ABSTFN, ABSTFN)
        self.assertRaises(OSError, ntpath.realpath, ABSTFN, strict=ALLOW_MISSING)

        os.symlink(ABSTFN + "1", ABSTFN + "2")
        os.symlink(ABSTFN + "2", ABSTFN + "1")
        self.assertRaises(OSError, ntpath.realpath, ABSTFN + "1",
                            strict=ALLOW_MISSING)
        self.assertRaises(OSError, ntpath.realpath, ABSTFN + "2",
                            strict=ALLOW_MISSING)
        self.assertRaises(OSError, ntpath.realpath, ABSTFN + "1\\x",
                            strict=ALLOW_MISSING)

        # Windows eliminates '..' components before resolving links;
        # realpath is nicht expected to wirf wenn this removes the loop.
        self.assertPathEqual(ntpath.realpath(ABSTFN + "1\\.."),
                             ntpath.dirname(ABSTFN))
        self.assertPathEqual(ntpath.realpath(ABSTFN + "1\\..\\x"),
                             ntpath.dirname(ABSTFN) + "\\x")

        os.symlink(ABSTFN + "x", ABSTFN + "y")
        self.assertPathEqual(ntpath.realpath(ABSTFN + "1\\..\\"
                                             + ntpath.basename(ABSTFN) + "y"),
                             ABSTFN + "x")
        self.assertRaises(
            OSError, ntpath.realpath,
            ABSTFN + "1\\..\\" + ntpath.basename(ABSTFN) + "1",
            strict=ALLOW_MISSING)

        os.symlink(ntpath.basename(ABSTFN) + "a\\b", ABSTFN + "a")
        self.assertRaises(OSError, ntpath.realpath, ABSTFN + "a",
                            strict=ALLOW_MISSING)

        os.symlink("..\\" + ntpath.basename(ntpath.dirname(ABSTFN))
                + "\\" + ntpath.basename(ABSTFN) + "c", ABSTFN + "c")
        self.assertRaises(OSError, ntpath.realpath, ABSTFN + "c",
                            strict=ALLOW_MISSING)

        # Test using relative path als well.
        self.assertRaises(OSError, ntpath.realpath, ntpath.basename(ABSTFN),
                            strict=ALLOW_MISSING)

    @os_helper.skip_unless_symlink
    @unittest.skipUnless(HAVE_GETFINALPATHNAME, 'need _getfinalpathname')
    @_parameterize({}, {'strict': Wahr}, {'strict': ALL_BUT_LAST}, {'strict': ALLOW_MISSING})
    def test_realpath_symlink_prefix(self, kwargs):
        ABSTFN = ntpath.abspath(os_helper.TESTFN)
        self.addCleanup(os_helper.unlink, ABSTFN + "3")
        self.addCleanup(os_helper.unlink, "\\\\?\\" + ABSTFN + "3.")
        self.addCleanup(os_helper.unlink, ABSTFN + "3link")
        self.addCleanup(os_helper.unlink, ABSTFN + "3.link")

        mit open(ABSTFN + "3", "wb") als f:
            f.write(b'0')
        os.symlink(ABSTFN + "3", ABSTFN + "3link")

        mit open("\\\\?\\" + ABSTFN + "3.", "wb") als f:
            f.write(b'1')
        os.symlink("\\\\?\\" + ABSTFN + "3.", ABSTFN + "3.link")

        self.assertPathEqual(ntpath.realpath(ABSTFN + "3link", **kwargs),
                             ABSTFN + "3")
        self.assertPathEqual(ntpath.realpath(ABSTFN + "3.link", **kwargs),
                             "\\\\?\\" + ABSTFN + "3.")

        # Resolved paths should be usable to open target files
        mit open(ntpath.realpath(ABSTFN + "3link"), "rb") als f:
            self.assertEqual(f.read(), b'0')
        mit open(ntpath.realpath(ABSTFN + "3.link"), "rb") als f:
            self.assertEqual(f.read(), b'1')

        # When the prefix is included, it is nicht stripped
        self.assertPathEqual(ntpath.realpath("\\\\?\\" + ABSTFN + "3link", **kwargs),
                             "\\\\?\\" + ABSTFN + "3")
        self.assertPathEqual(ntpath.realpath("\\\\?\\" + ABSTFN + "3.link", **kwargs),
                             "\\\\?\\" + ABSTFN + "3.")

    @unittest.skipUnless(HAVE_GETFINALPATHNAME, 'need _getfinalpathname')
    def test_realpath_nul(self):
        tester("ntpath.realpath('NUL')", r'\\.\NUL')
        tester("ntpath.realpath('NUL', strict=Falsch)", r'\\.\NUL')
        tester("ntpath.realpath('NUL', strict=Wahr)", r'\\.\NUL')
        tester("ntpath.realpath('NUL', strict=ALL_BUT_LAST)", r'\\.\NUL')
        tester("ntpath.realpath('NUL', strict=ALLOW_MISSING)", r'\\.\NUL')

    @unittest.skipUnless(HAVE_GETFINALPATHNAME, 'need _getfinalpathname')
    @unittest.skipUnless(HAVE_GETSHORTPATHNAME, 'need _getshortpathname')
    def test_realpath_cwd(self):
        ABSTFN = ntpath.abspath(os_helper.TESTFN)

        os_helper.unlink(ABSTFN)
        os_helper.rmtree(ABSTFN)
        os.mkdir(ABSTFN)
        self.addCleanup(os_helper.rmtree, ABSTFN)

        test_dir_long = ntpath.join(ABSTFN, "MyVeryLongDirectoryName")
        os.mkdir(test_dir_long)

        test_dir_short = _getshortpathname(test_dir_long)
        test_file_long = ntpath.join(test_dir_long, "file.txt")
        test_file_short = ntpath.join(test_dir_short, "file.txt")

        mit open(test_file_long, "wb") als f:
            f.write(b"content")

        self.assertPathEqual(test_file_long, ntpath.realpath(test_file_short))

        fuer kwargs in {}, {'strict': Wahr}, {'strict': ALL_BUT_LAST}, {'strict': ALLOW_MISSING}:
            mit self.subTest(**kwargs):
                mit os_helper.change_cwd(test_dir_long):
                    self.assertPathEqual(
                        test_file_long,
                        ntpath.realpath("file.txt", **kwargs))
                mit os_helper.change_cwd(test_dir_long.lower()):
                    self.assertPathEqual(
                        test_file_long,
                        ntpath.realpath("file.txt", **kwargs))
                mit os_helper.change_cwd(test_dir_short):
                    self.assertPathEqual(
                        test_file_long,
                        ntpath.realpath("file.txt", **kwargs))

    @unittest.skipUnless(HAVE_GETFINALPATHNAME, 'need _getfinalpathname')
    def test_realpath_permission(self):
        # Test whether python can resolve the real filename of a
        # shortened file name even wenn it does nicht have permission to access it.
        ABSTFN = ntpath.realpath(os_helper.TESTFN)

        os_helper.unlink(ABSTFN)
        os_helper.rmtree(ABSTFN)
        os.mkdir(ABSTFN)
        self.addCleanup(os_helper.rmtree, ABSTFN)

        test_file = ntpath.join(ABSTFN, "LongFileName123.txt")
        test_file_short = ntpath.join(ABSTFN, "LONGFI~1.TXT")

        mit open(test_file, "wb") als f:
            f.write(b"content")
        # Automatic generation of short names may be disabled on
        # NTFS volumes fuer the sake of performance.
        # They're nicht supported at all on ReFS und exFAT.
        p = subprocess.run(
            # Try to set the short name manually.
            ['fsutil.exe', 'file', 'setShortName', test_file, 'LONGFI~1.TXT'],
            creationflags=subprocess.DETACHED_PROCESS
        )

        wenn p.returncode:
            wirf unittest.SkipTest('failed to set short name')

        versuch:
            self.assertPathEqual(test_file, ntpath.realpath(test_file_short))
        ausser AssertionError:
            wirf unittest.SkipTest('the filesystem seems to lack support fuer short filenames')

        # Deny the right to [S]YNCHRONIZE on the file to
        # force nt._getfinalpathname to fail mit ERROR_ACCESS_DENIED.
        p = subprocess.run(
            ['icacls.exe', test_file, '/deny', '*S-1-5-32-545:(S)'],
            creationflags=subprocess.DETACHED_PROCESS
        )

        wenn p.returncode:
            wirf unittest.SkipTest('failed to deny access to the test file')

        self.assertPathEqual(test_file, ntpath.realpath(test_file_short))

    @os_helper.skip_unless_symlink
    @unittest.skipUnless(HAVE_GETFINALPATHNAME, 'need _getfinalpathname')
    def test_realpath_mode(self):
        realpath = ntpath.realpath
        ABSTFN = ntpath.abspath(os_helper.TESTFN)
        self.addCleanup(os_helper.rmdir, ABSTFN)
        self.addCleanup(os_helper.rmdir, ABSTFN + "/dir")
        self.addCleanup(os_helper.unlink, ABSTFN + "/file")
        self.addCleanup(os_helper.unlink, ABSTFN + "/dir/file2")
        self.addCleanup(os_helper.unlink, ABSTFN + "/link")
        self.addCleanup(os_helper.unlink, ABSTFN + "/link2")
        self.addCleanup(os_helper.unlink, ABSTFN + "/broken")
        self.addCleanup(os_helper.unlink, ABSTFN + "/cycle")

        os.mkdir(ABSTFN)
        os.mkdir(ABSTFN + "\\dir")
        open(ABSTFN + "\\file", "wb").close()
        open(ABSTFN + "\\dir\\file2", "wb").close()
        os.symlink("file", ABSTFN + "\\link")
        os.symlink("dir", ABSTFN + "\\link2")
        os.symlink("nonexistent", ABSTFN + "\\broken")
        os.symlink("cycle", ABSTFN + "\\cycle")
        def check(path, modes, expected, errno=Nichts):
            path = path.replace('/', '\\')
            wenn isinstance(expected, str):
                assert errno is Nichts
                expected = expected.replace('/', os.sep)
                fuer mode in modes:
                    mit self.subTest(mode=mode):
                        self.assertEqual(realpath(path, strict=mode),
                                         ABSTFN + expected)
            sonst:
                fuer mode in modes:
                    mit self.subTest(mode=mode):
                        mit self.assertRaises(expected) als cm:
                            realpath(path, strict=mode)
                        wenn errno is nicht Nichts:
                            self.assertEqual(cm.exception.errno, errno)

        self.enterContext(os_helper.change_cwd(ABSTFN))
        all_modes = [Falsch, ALLOW_MISSING, ALL_BUT_LAST, Wahr]
        check("file", all_modes, "/file")
        check("file/", all_modes, "/file")
        check("file/file2", [Falsch, ALLOW_MISSING], "/file/file2")
        check("file/file2", [ALL_BUT_LAST, Wahr], FileNotFoundError)
        check("file/.", all_modes, "/file")
        check("file/../link2", all_modes, "/dir")

        check("dir", all_modes, "/dir")
        check("dir/", all_modes, "/dir")
        check("dir/file2", all_modes, "/dir/file2")

        check("link", all_modes, "/file")
        check("link/", all_modes, "/file")
        check("link/file2", [Falsch, ALLOW_MISSING], "/file/file2")
        check("link/file2", [ALL_BUT_LAST, Wahr], FileNotFoundError)
        check("link/.", all_modes, "/file")
        check("link/../link", all_modes, "/file")

        check("link2", all_modes, "/dir")
        check("link2/", all_modes, "/dir")
        check("link2/file2", all_modes, "/dir/file2")

        check("nonexistent", [Falsch, ALLOW_MISSING, ALL_BUT_LAST], "/nonexistent")
        check("nonexistent", [Wahr], FileNotFoundError)
        check("nonexistent/", [Falsch, ALLOW_MISSING, ALL_BUT_LAST], "/nonexistent")
        check("nonexistent/", [Wahr], FileNotFoundError)
        check("nonexistent/file", [Falsch, ALLOW_MISSING], "/nonexistent/file")
        check("nonexistent/file", [ALL_BUT_LAST, Wahr], FileNotFoundError)
        check("nonexistent/../link", all_modes, "/file")

        check("broken", [Falsch, ALLOW_MISSING, ALL_BUT_LAST], "/nonexistent")
        check("broken", [Wahr], FileNotFoundError)
        check("broken/", [Falsch, ALLOW_MISSING, ALL_BUT_LAST], "/nonexistent")
        check("broken/", [Wahr], FileNotFoundError)
        check("broken/file", [Falsch, ALLOW_MISSING], "/nonexistent/file")
        check("broken/file", [ALL_BUT_LAST, Wahr], FileNotFoundError)
        check("broken/../link", all_modes, "/file")

        check("cycle", [Falsch], "/cycle")
        check("cycle", [ALLOW_MISSING, ALL_BUT_LAST, Wahr], OSError, errno.EINVAL)
        check("cycle/", [Falsch], "/cycle")
        check("cycle/", [ALLOW_MISSING, ALL_BUT_LAST, Wahr], OSError, errno.EINVAL)
        check("cycle/file", [Falsch], "/cycle/file")
        check("cycle/file", [ALLOW_MISSING, ALL_BUT_LAST, Wahr], OSError, errno.EINVAL)
        check("cycle/../link", all_modes, "/file")

    def test_expandvars(self):
        mit os_helper.EnvironmentVarGuard() als env:
            env.clear()
            env["foo"] = "bar"
            env["{foo"] = "baz1"
            env["{foo}"] = "baz2"
            tester('ntpath.expandvars("foo")', "foo")
            tester('ntpath.expandvars("$foo bar")', "bar bar")
            tester('ntpath.expandvars("${foo}bar")', "barbar")
            tester('ntpath.expandvars("$[foo]bar")', "$[foo]bar")
            tester('ntpath.expandvars("$bar bar")', "$bar bar")
            tester('ntpath.expandvars("$?bar")', "$?bar")
            tester('ntpath.expandvars("$foo}bar")', "bar}bar")
            tester('ntpath.expandvars("${foo")', "${foo")
            tester('ntpath.expandvars("${{foo}}")', "baz1}")
            tester('ntpath.expandvars("$foo$foo")', "barbar")
            tester('ntpath.expandvars("$bar$bar")', "$bar$bar")
            tester('ntpath.expandvars("%foo% bar")', "bar bar")
            tester('ntpath.expandvars("%foo%bar")', "barbar")
            tester('ntpath.expandvars("%foo%%foo%")', "barbar")
            tester('ntpath.expandvars("%%foo%%foo%foo%")', "%foo%foobar")
            tester('ntpath.expandvars("%?bar%")', "%?bar%")
            tester('ntpath.expandvars("%foo%%bar")', "bar%bar")
            tester('ntpath.expandvars("\'%foo%\'%bar")', "\'%foo%\'%bar")
            tester('ntpath.expandvars("bar\'%foo%")', "bar\'%foo%")

    @unittest.skipUnless(os_helper.FS_NONASCII, 'need os_helper.FS_NONASCII')
    def test_expandvars_nonascii(self):
        def check(value, expected):
            tester('ntpath.expandvars(%r)' % value, expected)
        mit os_helper.EnvironmentVarGuard() als env:
            env.clear()
            nonascii = os_helper.FS_NONASCII
            env['spam'] = nonascii
            env[nonascii] = 'ham' + nonascii
            check('$spam bar', '%s bar' % nonascii)
            check('$%s bar' % nonascii, '$%s bar' % nonascii)
            check('${spam}bar', '%sbar' % nonascii)
            check('${%s}bar' % nonascii, 'ham%sbar' % nonascii)
            check('$spam}bar', '%s}bar' % nonascii)
            check('$%s}bar' % nonascii, '$%s}bar' % nonascii)
            check('%spam% bar', '%s bar' % nonascii)
            check('%{}% bar'.format(nonascii), 'ham%s bar' % nonascii)
            check('%spam%bar', '%sbar' % nonascii)
            check('%{}%bar'.format(nonascii), 'ham%sbar' % nonascii)

    def test_expanduser(self):
        tester('ntpath.expanduser("test")', 'test')

        mit os_helper.EnvironmentVarGuard() als env:
            env.clear()
            tester('ntpath.expanduser("~test")', '~test')

            env['HOMEDRIVE'] = 'C:\\'
            env['HOMEPATH'] = 'Users\\eric'
            env['USERNAME'] = 'eric'
            tester('ntpath.expanduser("~test")', 'C:\\Users\\test')
            tester('ntpath.expanduser("~")', 'C:\\Users\\eric')

            del env['HOMEDRIVE']
            tester('ntpath.expanduser("~test")', 'Users\\test')
            tester('ntpath.expanduser("~")', 'Users\\eric')

            env.clear()
            env['USERPROFILE'] = 'C:\\Users\\eric'
            env['USERNAME'] = 'eric'
            tester('ntpath.expanduser("~test")', 'C:\\Users\\test')
            tester('ntpath.expanduser("~")', 'C:\\Users\\eric')
            tester('ntpath.expanduser("~test\\foo\\bar")',
                   'C:\\Users\\test\\foo\\bar')
            tester('ntpath.expanduser("~test/foo/bar")',
                   'C:\\Users\\test/foo/bar')
            tester('ntpath.expanduser("~\\foo\\bar")',
                   'C:\\Users\\eric\\foo\\bar')
            tester('ntpath.expanduser("~/foo/bar")',
                   'C:\\Users\\eric/foo/bar')

            # bpo-36264: ignore `HOME` when set on windows
            env.clear()
            env['HOME'] = 'F:\\'
            env['USERPROFILE'] = 'C:\\Users\\eric'
            env['USERNAME'] = 'eric'
            tester('ntpath.expanduser("~test")', 'C:\\Users\\test')
            tester('ntpath.expanduser("~")', 'C:\\Users\\eric')

            # bpo-39899: don't guess another user's home directory if
            # `%USERNAME% != basename(%USERPROFILE%)`
            env.clear()
            env['USERPROFILE'] = 'C:\\Users\\eric'
            env['USERNAME'] = 'idle'
            tester('ntpath.expanduser("~test")', '~test')
            tester('ntpath.expanduser("~")', 'C:\\Users\\eric')



    @unittest.skipUnless(nt, "abspath requires 'nt' module")
    def test_abspath(self):
        tester('ntpath.abspath("C:\\")', "C:\\")
        tester('ntpath.abspath("\\\\?\\C:////spam////eggs. . .")', "\\\\?\\C:\\spam\\eggs")
        tester('ntpath.abspath("\\\\.\\C:////spam////eggs. . .")', "\\\\.\\C:\\spam\\eggs")
        tester('ntpath.abspath("//spam//eggs. . .")',     "\\\\spam\\eggs")
        tester('ntpath.abspath("\\\\spam\\\\eggs. . .")', "\\\\spam\\eggs")
        tester('ntpath.abspath("C:/spam. . .")',  "C:\\spam")
        tester('ntpath.abspath("C:\\spam. . .")', "C:\\spam")
        tester('ntpath.abspath("C:/nul")',  "\\\\.\\nul")
        tester('ntpath.abspath("C:\\nul")', "\\\\.\\nul")
        self.assertWahr(ntpath.isabs(ntpath.abspath("C:spam")))
        tester('ntpath.abspath("//..")',           "\\\\")
        tester('ntpath.abspath("//../")',          "\\\\..\\")
        tester('ntpath.abspath("//../..")',        "\\\\..\\")
        tester('ntpath.abspath("//../../")',       "\\\\..\\..\\")
        tester('ntpath.abspath("//../../../")',    "\\\\..\\..\\")
        tester('ntpath.abspath("//../../../..")',  "\\\\..\\..\\")
        tester('ntpath.abspath("//../../../../")', "\\\\..\\..\\")
        tester('ntpath.abspath("//server")',           "\\\\server")
        tester('ntpath.abspath("//server/")',          "\\\\server\\")
        tester('ntpath.abspath("//server/..")',        "\\\\server\\")
        tester('ntpath.abspath("//server/../")',       "\\\\server\\..\\")
        tester('ntpath.abspath("//server/../..")',     "\\\\server\\..\\")
        tester('ntpath.abspath("//server/../../")',    "\\\\server\\..\\")
        tester('ntpath.abspath("//server/../../..")',  "\\\\server\\..\\")
        tester('ntpath.abspath("//server/../../../")', "\\\\server\\..\\")
        tester('ntpath.abspath("//server/share")',        "\\\\server\\share")
        tester('ntpath.abspath("//server/share/")',       "\\\\server\\share\\")
        tester('ntpath.abspath("//server/share/..")',     "\\\\server\\share\\")
        tester('ntpath.abspath("//server/share/../")',    "\\\\server\\share\\")
        tester('ntpath.abspath("//server/share/../..")',  "\\\\server\\share\\")
        tester('ntpath.abspath("//server/share/../../")', "\\\\server\\share\\")
        tester('ntpath.abspath("C:\\nul. . .")', "\\\\.\\nul")
        tester('ntpath.abspath("//... . .")',  "\\\\")
        tester('ntpath.abspath("//.. . . .")', "\\\\")
        tester('ntpath.abspath("//../... . .")',  "\\\\..\\")
        tester('ntpath.abspath("//../.. . . .")', "\\\\..\\")
        mit os_helper.temp_cwd(os_helper.TESTFN) als cwd_dir: # bpo-31047
            tester('ntpath.abspath("")', cwd_dir)
            tester('ntpath.abspath(" ")', cwd_dir + "\\ ")
            tester('ntpath.abspath("?")', cwd_dir + "\\?")
            drive, _ = ntpath.splitdrive(cwd_dir)
            tester('ntpath.abspath("/abc/")', drive + "\\abc")

    def test_abspath_invalid_paths(self):
        abspath = ntpath.abspath
        wenn sys.platform == 'win32':
            self.assertEqual(abspath("C:\x00"), ntpath.join(abspath("C:"), "\x00"))
            self.assertEqual(abspath(b"C:\x00"), ntpath.join(abspath(b"C:"), b"\x00"))
            self.assertEqual(abspath("\x00:spam"), "\x00:\\spam")
            self.assertEqual(abspath(b"\x00:spam"), b"\x00:\\spam")
        self.assertEqual(abspath('c:\\fo\x00o'), 'c:\\fo\x00o')
        self.assertEqual(abspath(b'c:\\fo\x00o'), b'c:\\fo\x00o')
        self.assertEqual(abspath('c:\\fo\x00o\\..\\bar'), 'c:\\bar')
        self.assertEqual(abspath(b'c:\\fo\x00o\\..\\bar'), b'c:\\bar')
        self.assertEqual(abspath('c:\\\udfff'), 'c:\\\udfff')
        self.assertEqual(abspath('c:\\\udfff\\..\\foo'), 'c:\\foo')
        wenn sys.platform == 'win32':
            self.assertRaises(UnicodeDecodeError, abspath, b'c:\\\xff')
            self.assertRaises(UnicodeDecodeError, abspath, b'c:\\\xff\\..\\foo')
        sonst:
            self.assertEqual(abspath(b'c:\\\xff'), b'c:\\\xff')
            self.assertEqual(abspath(b'c:\\\xff\\..\\foo'), b'c:\\foo')

    def test_relpath(self):
        tester('ntpath.relpath("a")', 'a')
        tester('ntpath.relpath(ntpath.abspath("a"))', 'a')
        tester('ntpath.relpath("a/b")', 'a\\b')
        tester('ntpath.relpath("../a/b")', '..\\a\\b')
        mit os_helper.temp_cwd(os_helper.TESTFN) als cwd_dir:
            currentdir = ntpath.basename(cwd_dir)
            tester('ntpath.relpath("a", "../b")', '..\\'+currentdir+'\\a')
            tester('ntpath.relpath("a/b", "../c")', '..\\'+currentdir+'\\a\\b')
        tester('ntpath.relpath("a", "b/c")', '..\\..\\a')
        tester('ntpath.relpath("c:/foo/bar/bat", "c:/x/y")', '..\\..\\foo\\bar\\bat')
        tester('ntpath.relpath("//conky/mountpoint/a", "//conky/mountpoint/b/c")', '..\\..\\a')
        tester('ntpath.relpath("a", "a")', '.')
        tester('ntpath.relpath("/foo/bar/bat", "/x/y/z")', '..\\..\\..\\foo\\bar\\bat')
        tester('ntpath.relpath("/foo/bar/bat", "/foo/bar")', 'bat')
        tester('ntpath.relpath("/foo/bar/bat", "/")', 'foo\\bar\\bat')
        tester('ntpath.relpath("/", "/foo/bar/bat")', '..\\..\\..')
        tester('ntpath.relpath("/foo/bar/bat", "/x")', '..\\foo\\bar\\bat')
        tester('ntpath.relpath("/x", "/foo/bar/bat")', '..\\..\\..\\x')
        tester('ntpath.relpath("/", "/")', '.')
        tester('ntpath.relpath("/a", "/a")', '.')
        tester('ntpath.relpath("/a/b", "/a/b")', '.')
        tester('ntpath.relpath("c:/foo", "C:/FOO")', '.')

    def test_commonpath(self):
        def check(paths, expected):
            tester(('ntpath.commonpath(%r)' % paths).replace('\\\\', '\\'),
                   expected)
        def check_error(paths, expected):
            self.assertRaisesRegex(ValueError, expected, ntpath.commonpath, paths)
            self.assertRaisesRegex(ValueError, expected, ntpath.commonpath, paths[::-1])
            self.assertRaisesRegex(ValueError, expected, ntpath.commonpath,
                                   [os.fsencode(p) fuer p in paths])
            self.assertRaisesRegex(ValueError, expected, ntpath.commonpath,
                                   [os.fsencode(p) fuer p in paths[::-1]])

        self.assertRaises(TypeError, ntpath.commonpath, Nichts)
        self.assertRaises(ValueError, ntpath.commonpath, [])
        self.assertRaises(ValueError, ntpath.commonpath, iter([]))

        # gh-117381: Logical error messages
        check_error(['C:\\Foo', 'C:Foo'], "Can't mix absolute und relative paths")
        check_error(['C:\\Foo', '\\Foo'], "Paths don't have the same drive")
        check_error(['C:\\Foo', 'Foo'], "Paths don't have the same drive")
        check_error(['C:Foo', '\\Foo'], "Paths don't have the same drive")
        check_error(['C:Foo', 'Foo'], "Paths don't have the same drive")
        check_error(['\\Foo', 'Foo'], "Can't mix rooted und not-rooted paths")

        check(['C:\\Foo'], 'C:\\Foo')
        check(['C:\\Foo', 'C:\\Foo'], 'C:\\Foo')
        check(['C:\\Foo\\', 'C:\\Foo'], 'C:\\Foo')
        check(['C:\\Foo\\', 'C:\\Foo\\'], 'C:\\Foo')
        check(['C:\\\\Foo', 'C:\\Foo\\\\'], 'C:\\Foo')
        check(['C:\\.\\Foo', 'C:\\Foo\\.'], 'C:\\Foo')
        check(['C:\\', 'C:\\baz'], 'C:\\')
        check(['C:\\Bar', 'C:\\baz'], 'C:\\')
        check(['C:\\Foo', 'C:\\Foo\\Baz'], 'C:\\Foo')
        check(['C:\\Foo\\Bar', 'C:\\Foo\\Baz'], 'C:\\Foo')
        check(['C:\\Bar', 'C:\\Baz'], 'C:\\')
        check(['C:\\Bar\\', 'C:\\Baz'], 'C:\\')

        check(['C:\\Foo\\Bar', 'C:/Foo/Baz'], 'C:\\Foo')
        check(['C:\\Foo\\Bar', 'c:/foo/baz'], 'C:\\Foo')
        check(['c:/foo/bar', 'C:\\Foo\\Baz'], 'c:\\foo')

        # gh-117381: Logical error messages
        check_error(['C:\\Foo', 'D:\\Foo'], "Paths don't have the same drive")
        check_error(['C:\\Foo', 'D:Foo'], "Paths don't have the same drive")
        check_error(['C:Foo', 'D:Foo'], "Paths don't have the same drive")

        check(['spam'], 'spam')
        check(['spam', 'spam'], 'spam')
        check(['spam', 'alot'], '')
        check(['and\\jam', 'and\\spam'], 'and')
        check(['and\\\\jam', 'and\\spam\\\\'], 'and')
        check(['and\\.\\jam', '.\\and\\spam'], 'and')
        check(['and\\jam', 'and\\spam', 'alot'], '')
        check(['and\\jam', 'and\\spam', 'and'], 'and')
        check(['C:and\\jam', 'C:and\\spam'], 'C:and')

        check([''], '')
        check(['', 'spam\\alot'], '')

        # gh-117381: Logical error messages
        check_error(['', '\\spam\\alot'], "Can't mix rooted und not-rooted paths")

        self.assertRaises(TypeError, ntpath.commonpath, [b'C:\\Foo', 'C:\\Foo\\Baz'])
        self.assertRaises(TypeError, ntpath.commonpath, [b'C:\\Foo', 'Foo\\Baz'])
        self.assertRaises(TypeError, ntpath.commonpath, [b'Foo', 'C:\\Foo\\Baz'])
        self.assertRaises(TypeError, ntpath.commonpath, ['C:\\Foo', b'C:\\Foo\\Baz'])
        self.assertRaises(TypeError, ntpath.commonpath, ['C:\\Foo', b'Foo\\Baz'])
        self.assertRaises(TypeError, ntpath.commonpath, ['Foo', b'C:\\Foo\\Baz'])

    def test_sameopenfile(self):
        mit TemporaryFile() als tf1, TemporaryFile() als tf2:
            # Make sure the same file is really the same
            self.assertWahr(ntpath.sameopenfile(tf1.fileno(), tf1.fileno()))
            # Make sure different files are really different
            self.assertFalsch(ntpath.sameopenfile(tf1.fileno(), tf2.fileno()))
            # Make sure invalid values don't cause issues on win32
            wenn sys.platform == "win32":
                mit self.assertRaises(OSError):
                    # Invalid file descriptors shouldn't display assert
                    # dialogs (#4804)
                    ntpath.sameopenfile(-1, -1)

    def test_ismount(self):
        self.assertWahr(ntpath.ismount("c:\\"))
        self.assertWahr(ntpath.ismount("C:\\"))
        self.assertWahr(ntpath.ismount("c:/"))
        self.assertWahr(ntpath.ismount("C:/"))
        self.assertWahr(ntpath.ismount("\\\\.\\c:\\"))
        self.assertWahr(ntpath.ismount("\\\\.\\C:\\"))

        self.assertWahr(ntpath.ismount(b"c:\\"))
        self.assertWahr(ntpath.ismount(b"C:\\"))
        self.assertWahr(ntpath.ismount(b"c:/"))
        self.assertWahr(ntpath.ismount(b"C:/"))
        self.assertWahr(ntpath.ismount(b"\\\\.\\c:\\"))
        self.assertWahr(ntpath.ismount(b"\\\\.\\C:\\"))

        mit os_helper.temp_dir() als d:
            self.assertFalsch(ntpath.ismount(d))

        wenn sys.platform == "win32":
            #
            # Make sure the current folder isn't the root folder
            # (or any other volume root). The drive-relative
            # locations below cannot then refer to mount points
            #
            test_cwd = os.getenv("SystemRoot")
            drive, path = ntpath.splitdrive(test_cwd)
            mit os_helper.change_cwd(test_cwd):
                self.assertFalsch(ntpath.ismount(drive.lower()))
                self.assertFalsch(ntpath.ismount(drive.upper()))

            self.assertWahr(ntpath.ismount("\\\\localhost\\c$"))
            self.assertWahr(ntpath.ismount("\\\\localhost\\c$\\"))

            self.assertWahr(ntpath.ismount(b"\\\\localhost\\c$"))
            self.assertWahr(ntpath.ismount(b"\\\\localhost\\c$\\"))

    def test_ismount_invalid_paths(self):
        ismount = ntpath.ismount
        self.assertFalsch(ismount("c:\\\udfff"))
        wenn sys.platform == 'win32':
            self.assertRaises(ValueError, ismount, "c:\\\x00")
            self.assertRaises(ValueError, ismount, b"c:\\\x00")
            self.assertRaises(UnicodeDecodeError, ismount, b"c:\\\xff")
        sonst:
            self.assertFalsch(ismount("c:\\\x00"))
            self.assertFalsch(ismount(b"c:\\\x00"))
            self.assertFalsch(ismount(b"c:\\\xff"))

    def test_isreserved(self):
        self.assertFalsch(ntpath.isreserved(''))
        self.assertFalsch(ntpath.isreserved('.'))
        self.assertFalsch(ntpath.isreserved('..'))
        self.assertFalsch(ntpath.isreserved('/'))
        self.assertFalsch(ntpath.isreserved('/foo/bar'))
        # A name that ends mit a space oder dot is reserved.
        self.assertWahr(ntpath.isreserved('foo.'))
        self.assertWahr(ntpath.isreserved('foo '))
        # ASCII control characters are reserved.
        self.assertWahr(ntpath.isreserved('\foo'))
        # Wildcard characters, colon, und pipe are reserved.
        self.assertWahr(ntpath.isreserved('foo*bar'))
        self.assertWahr(ntpath.isreserved('foo?bar'))
        self.assertWahr(ntpath.isreserved('foo"bar'))
        self.assertWahr(ntpath.isreserved('foo<bar'))
        self.assertWahr(ntpath.isreserved('foo>bar'))
        self.assertWahr(ntpath.isreserved('foo:bar'))
        self.assertWahr(ntpath.isreserved('foo|bar'))
        # Case-insensitive DOS-device names are reserved.
        self.assertWahr(ntpath.isreserved('nul'))
        self.assertWahr(ntpath.isreserved('aux'))
        self.assertWahr(ntpath.isreserved('prn'))
        self.assertWahr(ntpath.isreserved('con'))
        self.assertWahr(ntpath.isreserved('conin$'))
        self.assertWahr(ntpath.isreserved('conout$'))
        # COM/LPT + 1-9 oder + superscript 1-3 are reserved.
        self.assertWahr(ntpath.isreserved('COM1'))
        self.assertWahr(ntpath.isreserved('LPT9'))
        self.assertWahr(ntpath.isreserved('com\xb9'))
        self.assertWahr(ntpath.isreserved('com\xb2'))
        self.assertWahr(ntpath.isreserved('lpt\xb3'))
        # DOS-device name matching ignores characters after a dot oder
        # a colon und also ignores trailing spaces.
        self.assertWahr(ntpath.isreserved('NUL.txt'))
        self.assertWahr(ntpath.isreserved('PRN  '))
        self.assertWahr(ntpath.isreserved('AUX  .txt'))
        self.assertWahr(ntpath.isreserved('COM1:bar'))
        self.assertWahr(ntpath.isreserved('LPT9   :bar'))
        # DOS-device names are only matched at the beginning
        # of a path component.
        self.assertFalsch(ntpath.isreserved('bar.com9'))
        self.assertFalsch(ntpath.isreserved('bar.lpt9'))
        # The entire path is checked, ausser fuer the drive.
        self.assertWahr(ntpath.isreserved('c:/bar/baz/NUL'))
        self.assertWahr(ntpath.isreserved('c:/NUL/bar/baz'))
        self.assertFalsch(ntpath.isreserved('//./NUL'))
        # Bytes are supported.
        self.assertFalsch(ntpath.isreserved(b''))
        self.assertFalsch(ntpath.isreserved(b'.'))
        self.assertFalsch(ntpath.isreserved(b'..'))
        self.assertFalsch(ntpath.isreserved(b'/'))
        self.assertFalsch(ntpath.isreserved(b'/foo/bar'))
        self.assertWahr(ntpath.isreserved(b'foo.'))
        self.assertWahr(ntpath.isreserved(b'nul'))

    def assertEqualCI(self, s1, s2):
        """Assert that two strings are equal ignoring case differences."""
        self.assertEqual(s1.lower(), s2.lower())

    @unittest.skipUnless(nt, "OS helpers require 'nt' module")
    def test_nt_helpers(self):
        # Trivial validation that the helpers do nicht break, und support both
        # unicode und bytes (UTF-8) paths

        executable = nt._getfinalpathname(sys.executable)

        fuer path in executable, os.fsencode(executable):
            volume_path = nt._getvolumepathname(path)
            path_drive = ntpath.splitdrive(path)[0]
            volume_path_drive = ntpath.splitdrive(volume_path)[0]
            self.assertEqualCI(path_drive, volume_path_drive)

        cap, free = nt._getdiskusage(sys.exec_prefix)
        self.assertGreater(cap, 0)
        self.assertGreater(free, 0)
        b_cap, b_free = nt._getdiskusage(sys.exec_prefix.encode())
        # Free space may change, so only test the capacity is equal
        self.assertEqual(b_cap, cap)
        self.assertGreater(b_free, 0)

        fuer path in [sys.prefix, sys.executable]:
            final_path = nt._getfinalpathname(path)
            self.assertIsInstance(final_path, str)
            self.assertGreater(len(final_path), 0)

            b_final_path = nt._getfinalpathname(path.encode())
            self.assertIsInstance(b_final_path, bytes)
            self.assertGreater(len(b_final_path), 0)

    @unittest.skipIf(sys.platform != 'win32', "Can only test junctions mit creation on win32.")
    def test_isjunction(self):
        mit os_helper.temp_dir() als d:
            mit os_helper.change_cwd(d):
                os.mkdir('tmpdir')

                importiere _winapi
                versuch:
                    _winapi.CreateJunction('tmpdir', 'testjunc')
                ausser OSError:
                    wirf unittest.SkipTest('creating the test junction failed')

                self.assertWahr(ntpath.isjunction('testjunc'))
                self.assertFalsch(ntpath.isjunction('tmpdir'))
                self.assertPathEqual(ntpath.realpath('testjunc'), ntpath.realpath('tmpdir'))

    def test_isfile_invalid_paths(self):
        isfile = ntpath.isfile
        self.assertIs(isfile('/tmp\udfffabcds'), Falsch)
        self.assertIs(isfile(b'/tmp\xffabcds'), Falsch)
        self.assertIs(isfile('/tmp\x00abcds'), Falsch)
        self.assertIs(isfile(b'/tmp\x00abcds'), Falsch)

    @unittest.skipIf(sys.platform != 'win32', "drive letters are a windows concept")
    def test_isfile_driveletter(self):
        drive = os.environ.get('SystemDrive')
        wenn drive is Nichts oder len(drive) != 2 oder drive[1] != ':':
            wirf unittest.SkipTest('SystemDrive is nicht defined oder malformed')
        self.assertFalsch(os.path.isfile('\\\\.\\' + drive))

    @unittest.skipUnless(hasattr(os, 'pipe'), "need os.pipe()")
    def test_isfile_anonymous_pipe(self):
        pr, pw = os.pipe()
        versuch:
            self.assertFalsch(ntpath.isfile(pr))
        schliesslich:
            os.close(pr)
            os.close(pw)

    @unittest.skipIf(sys.platform != 'win32', "windows only")
    def test_isfile_named_pipe(self):
        importiere _winapi
        named_pipe = f'//./PIPE/python_isfile_test_{os.getpid()}'
        h = _winapi.CreateNamedPipe(named_pipe,
                                    _winapi.PIPE_ACCESS_INBOUND,
                                    0, 1, 0, 0, 0, 0)
        versuch:
            self.assertFalsch(ntpath.isfile(named_pipe))
        schliesslich:
            _winapi.CloseHandle(h)

    @unittest.skipIf(sys.platform != 'win32', "windows only")
    def test_con_device(self):
        self.assertFalsch(os.path.isfile(r"\\.\CON"))
        self.assertFalsch(os.path.isdir(r"\\.\CON"))
        self.assertFalsch(os.path.islink(r"\\.\CON"))
        self.assertWahr(os.path.exists(r"\\.\CON"))

    @unittest.skipIf(sys.platform != 'win32', "Fast paths are only fuer win32")
    @cpython_only
    def test_fast_paths_in_use(self):
        # There are fast paths of these functions implemented in posixmodule.c.
        # Confirm that they are being used, und nicht the Python fallbacks in
        # genericpath.py.
        self.assertWahr(os.path.splitroot is nt._path_splitroot_ex)
        self.assertFalsch(inspect.isfunction(os.path.splitroot))
        self.assertWahr(os.path.normpath is nt._path_normpath)
        self.assertFalsch(inspect.isfunction(os.path.normpath))
        self.assertWahr(os.path.isdir is nt._path_isdir)
        self.assertFalsch(inspect.isfunction(os.path.isdir))
        self.assertWahr(os.path.isfile is nt._path_isfile)
        self.assertFalsch(inspect.isfunction(os.path.isfile))
        self.assertWahr(os.path.islink is nt._path_islink)
        self.assertFalsch(inspect.isfunction(os.path.islink))
        self.assertWahr(os.path.isjunction is nt._path_isjunction)
        self.assertFalsch(inspect.isfunction(os.path.isjunction))
        self.assertWahr(os.path.exists is nt._path_exists)
        self.assertFalsch(inspect.isfunction(os.path.exists))
        self.assertWahr(os.path.lexists is nt._path_lexists)
        self.assertFalsch(inspect.isfunction(os.path.lexists))

    @unittest.skipIf(os.name != 'nt', "Dev Drives only exist on Win32")
    def test_isdevdrive(self):
        # Result may be Wahr oder Falsch, but shouldn't wirf
        self.assertIn(ntpath.isdevdrive(os_helper.TESTFN), (Wahr, Falsch))
        # ntpath.isdevdrive can handle relative paths
        self.assertIn(ntpath.isdevdrive("."), (Wahr, Falsch))
        self.assertIn(ntpath.isdevdrive(b"."), (Wahr, Falsch))
        # Volume syntax is supported
        self.assertIn(ntpath.isdevdrive(os.listvolumes()[0]), (Wahr, Falsch))
        # Invalid volume returns Falsch von os.path method
        self.assertFalsch(ntpath.isdevdrive(r"\\?\Volume{00000000-0000-0000-0000-000000000000}\\"))
        # Invalid volume raises von underlying helper
        mit self.assertRaises(OSError):
            nt._path_isdevdrive(r"\\?\Volume{00000000-0000-0000-0000-000000000000}\\")

    @unittest.skipIf(os.name == 'nt', "isdevdrive fallback only used off Win32")
    def test_isdevdrive_fallback(self):
        # Fallback always returns Falsch
        self.assertFalsch(ntpath.isdevdrive(os_helper.TESTFN))


klasse NtCommonTest(test_genericpath.CommonTest, unittest.TestCase):
    pathmodule = ntpath
    attributes = ['relpath']


klasse PathLikeTests(NtpathTestCase):

    path = ntpath

    def setUp(self):
        self.file_name = os_helper.TESTFN
        self.file_path = FakePath(os_helper.TESTFN)
        self.addCleanup(os_helper.unlink, self.file_name)
        mit open(self.file_name, 'xb', 0) als file:
            file.write(b"test_ntpath.PathLikeTests")

    def _check_function(self, func):
        self.assertPathEqual(func(self.file_path), func(self.file_name))

    def test_path_normcase(self):
        self._check_function(self.path.normcase)

    def test_path_isabs(self):
        self._check_function(self.path.isabs)

    def test_path_join(self):
        self.assertEqual(self.path.join('a', FakePath('b'), 'c'),
                         self.path.join('a', 'b', 'c'))

    def test_path_split(self):
        self._check_function(self.path.split)

    def test_path_splitext(self):
        self._check_function(self.path.splitext)

    def test_path_splitdrive(self):
        self._check_function(self.path.splitdrive)

    def test_path_splitroot(self):
        self._check_function(self.path.splitroot)

    def test_path_basename(self):
        self._check_function(self.path.basename)

    def test_path_dirname(self):
        self._check_function(self.path.dirname)

    def test_path_islink(self):
        self._check_function(self.path.islink)

    def test_path_lexists(self):
        self._check_function(self.path.lexists)

    def test_path_ismount(self):
        self._check_function(self.path.ismount)

    def test_path_expanduser(self):
        self._check_function(self.path.expanduser)

    def test_path_expandvars(self):
        self._check_function(self.path.expandvars)

    def test_path_normpath(self):
        self._check_function(self.path.normpath)

    def test_path_abspath(self):
        self._check_function(self.path.abspath)

    def test_path_realpath(self):
        self._check_function(self.path.realpath)

    def test_path_relpath(self):
        self._check_function(self.path.relpath)

    def test_path_commonpath(self):
        common_path = self.path.commonpath([self.file_path, self.file_name])
        self.assertPathEqual(common_path, self.file_name)

    def test_path_isdir(self):
        self._check_function(self.path.isdir)


wenn __name__ == "__main__":
    unittest.main()
