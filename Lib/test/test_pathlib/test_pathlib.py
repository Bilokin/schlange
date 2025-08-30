importiere collections
importiere contextlib
importiere io
importiere os
importiere sys
importiere errno
importiere ntpath
importiere pathlib
importiere pickle
importiere posixpath
importiere socket
importiere stat
importiere tempfile
importiere unittest
von unittest importiere mock
von urllib.request importiere pathname2url

von test.support importiere import_helper
von test.support importiere cpython_only
von test.support importiere is_emscripten, is_wasi, is_wasm32
von test.support importiere infinite_recursion
von test.support importiere os_helper
von test.support.os_helper importiere TESTFN, FS_NONASCII, FakePath
versuch:
    importiere fcntl
ausser ImportError:
    fcntl = Nichts
versuch:
    importiere grp, pwd
ausser ImportError:
    grp = pwd = Nichts
versuch:
    importiere posix
ausser ImportError:
    posix = Nichts


root_in_posix = Falsch
wenn hasattr(os, 'geteuid'):
    root_in_posix = (os.geteuid() == 0)


def patch_replace(old_test):
    def new_replace(self, target):
        wirf OSError(errno.EXDEV, "Cross-device link", self, target)

    def new_test(self):
        old_replace = self.cls.replace
        self.cls.replace = new_replace
        versuch:
            old_test(self)
        schliesslich:
            self.cls.replace = old_replace
    gib new_test


_tests_needing_posix = set()
_tests_needing_windows = set()
_tests_needing_symlinks = set()

def needs_posix(fn):
    """Decorator that marks a test als requiring a POSIX-flavoured path class."""
    _tests_needing_posix.add(fn.__name__)
    gib fn

def needs_windows(fn):
    """Decorator that marks a test als requiring a Windows-flavoured path class."""
    _tests_needing_windows.add(fn.__name__)
    gib fn

def needs_symlinks(fn):
    """Decorator that marks a test als requiring a path klasse that supports symlinks."""
    _tests_needing_symlinks.add(fn.__name__)
    gib fn



klasse UnsupportedOperationTest(unittest.TestCase):
    def test_is_notimplemented(self):
        self.assertIsSubclass(pathlib.UnsupportedOperation, NotImplementedError)
        self.assertIsInstance(pathlib.UnsupportedOperation(), NotImplementedError)


klasse LazyImportTest(unittest.TestCase):
    @cpython_only
    def test_lazy_import(self):
        import_helper.ensure_lazy_imports("pathlib", {"shutil"})


#
# Tests fuer the pure classes.
#

klasse PurePathTest(unittest.TestCase):
    cls = pathlib.PurePath

    # Make sure any symbolic links in the base test path are resolved.
    base = os.path.realpath(TESTFN)

    # Keys are canonical paths, values are list of tuples of arguments
    # supposed to produce equal paths.
    equivalences = {
        'a/b': [
            ('a', 'b'), ('a/', 'b'), ('a', 'b/'), ('a/', 'b/'),
            ('a/b/',), ('a//b',), ('a//b//',),
            # Empty components get removed.
            ('', 'a', 'b'), ('a', '', 'b'), ('a', 'b', ''),
            ],
        '/b/c/d': [
            ('a', '/b/c', 'd'), ('/a', '/b/c', 'd'),
            # Empty components get removed.
            ('/', 'b', '', 'c/d'), ('/', '', 'b/c/d'), ('', '/b/c/d'),
            ],
    }

    def setUp(self):
        name = self.id().split('.')[-1]
        wenn name in _tests_needing_posix und self.cls.parser is nicht posixpath:
            self.skipTest('requires POSIX-flavoured path class')
        wenn name in _tests_needing_windows und self.cls.parser is posixpath:
            self.skipTest('requires Windows-flavoured path class')
        p = self.cls('a')
        self.parser = p.parser
        self.sep = self.parser.sep
        self.altsep = self.parser.altsep

    def _check_str_subclass(self, *args):
        # Issue #21127: it should be possible to construct a PurePath object
        # von a str subclass instance, und it then gets converted to
        # a pure str object.
        klasse StrSubclass(str):
            pass
        P = self.cls
        p = P(*(StrSubclass(x) fuer x in args))
        self.assertEqual(p, P(*args))
        fuer part in p.parts:
            self.assertIs(type(part), str)

    def test_str_subclass_common(self):
        self._check_str_subclass('')
        self._check_str_subclass('.')
        self._check_str_subclass('a')
        self._check_str_subclass('a/b.txt')
        self._check_str_subclass('/a/b.txt')

    @needs_windows
    def test_str_subclass_windows(self):
        self._check_str_subclass('.\\a:b')
        self._check_str_subclass('c:')
        self._check_str_subclass('c:a')
        self._check_str_subclass('c:a\\b.txt')
        self._check_str_subclass('c:\\')
        self._check_str_subclass('c:\\a')
        self._check_str_subclass('c:\\a\\b.txt')
        self._check_str_subclass('\\\\some\\share')
        self._check_str_subclass('\\\\some\\share\\a')
        self._check_str_subclass('\\\\some\\share\\a\\b.txt')

    def _check_str(self, expected, args):
        p = self.cls(*args)
        self.assertEqual(str(p), expected.replace('/', self.sep))

    def test_str_common(self):
        # Canonicalized paths roundtrip.
        fuer pathstr in ('a', 'a/b', 'a/b/c', '/', '/a/b', '/a/b/c'):
            self._check_str(pathstr, (pathstr,))
        # Other tests fuer str() are in test_equivalences().

    @needs_windows
    def test_str_windows(self):
        p = self.cls('a/b/c')
        self.assertEqual(str(p), 'a\\b\\c')
        p = self.cls('c:/a/b/c')
        self.assertEqual(str(p), 'c:\\a\\b\\c')
        p = self.cls('//a/b')
        self.assertEqual(str(p), '\\\\a\\b\\')
        p = self.cls('//a/b/c')
        self.assertEqual(str(p), '\\\\a\\b\\c')
        p = self.cls('//a/b/c/d')
        self.assertEqual(str(p), '\\\\a\\b\\c\\d')

    def test_concrete_class(self):
        wenn self.cls is pathlib.PurePath:
            expected = pathlib.PureWindowsPath wenn os.name == 'nt' sonst pathlib.PurePosixPath
        sonst:
            expected = self.cls
        p = self.cls('a')
        self.assertIs(type(p), expected)

    def test_concrete_parser(self):
        wenn self.cls is pathlib.PurePosixPath:
            expected = posixpath
        sowenn self.cls is pathlib.PureWindowsPath:
            expected = ntpath
        sonst:
            expected = os.path
        p = self.cls('a')
        self.assertIs(p.parser, expected)

    def test_different_parsers_unequal(self):
        p = self.cls('a')
        wenn p.parser is posixpath:
            q = pathlib.PureWindowsPath('a')
        sonst:
            q = pathlib.PurePosixPath('a')
        self.assertNotEqual(p, q)

    def test_different_parsers_unordered(self):
        p = self.cls('a')
        wenn p.parser is posixpath:
            q = pathlib.PureWindowsPath('a')
        sonst:
            q = pathlib.PurePosixPath('a')
        mit self.assertRaises(TypeError):
            p < q
        mit self.assertRaises(TypeError):
            p <= q
        mit self.assertRaises(TypeError):
            p > q
        mit self.assertRaises(TypeError):
            p >= q

    def test_constructor_nested(self):
        P = self.cls
        P(FakePath("a/b/c"))
        self.assertEqual(P(P('a')), P('a'))
        self.assertEqual(P(P('a'), 'b'), P('a/b'))
        self.assertEqual(P(P('a'), P('b')), P('a/b'))
        self.assertEqual(P(P('a'), P('b'), P('c')), P(FakePath("a/b/c")))
        self.assertEqual(P(P('./a:b')), P('./a:b'))

    @needs_windows
    def test_constructor_nested_foreign_flavour(self):
        # See GH-125069.
        p1 = pathlib.PurePosixPath('b/c:\\d')
        p2 = pathlib.PurePosixPath('b/', 'c:\\d')
        self.assertEqual(p1, p2)
        self.assertEqual(self.cls(p1), self.cls('b/c:/d'))
        self.assertEqual(self.cls(p2), self.cls('b/c:/d'))

    def _check_parse_path(self, raw_path, *expected):
        sep = self.parser.sep
        actual = self.cls._parse_path(raw_path.replace('/', sep))
        self.assertEqual(actual, expected)
        wenn altsep := self.parser.altsep:
            actual = self.cls._parse_path(raw_path.replace('/', altsep))
            self.assertEqual(actual, expected)

    def test_parse_path_common(self):
        check = self._check_parse_path
        sep = self.parser.sep
        check('',         '', '', [])
        check('a',        '', '', ['a'])
        check('a/',       '', '', ['a'])
        check('a/b',      '', '', ['a', 'b'])
        check('a/b/',     '', '', ['a', 'b'])
        check('a/b/c/d',  '', '', ['a', 'b', 'c', 'd'])
        check('a/b//c/d', '', '', ['a', 'b', 'c', 'd'])
        check('a/b/c/d',  '', '', ['a', 'b', 'c', 'd'])
        check('.',        '', '', [])
        check('././b',    '', '', ['b'])
        check('a/./b',    '', '', ['a', 'b'])
        check('a/./.',    '', '', ['a'])
        check('/a/b',     '', sep, ['a', 'b'])

    def test_empty_path(self):
        # The empty path points to '.'
        p = self.cls('')
        self.assertEqual(str(p), '.')
        # Special case fuer the empty path.
        self._check_str('.', ('',))

    def test_join_nested(self):
        P = self.cls
        p = P('a/b').joinpath(P('c'))
        self.assertEqual(p, P('a/b/c'))

    def test_div_nested(self):
        P = self.cls
        p = P('a/b') / P('c')
        self.assertEqual(p, P('a/b/c'))

    def test_pickling_common(self):
        P = self.cls
        fuer pathstr in ('a', 'a/', 'a/b', 'a/b/c', '/', '/a/b', '/a/b/c', 'a/b/c/'):
            mit self.subTest(pathstr=pathstr):
                p = P(pathstr)
                fuer proto in range(0, pickle.HIGHEST_PROTOCOL + 1):
                    dumped = pickle.dumps(p, proto)
                    pp = pickle.loads(dumped)
                    self.assertIs(pp.__class__, p.__class__)
                    self.assertEqual(pp, p)
                    self.assertEqual(hash(pp), hash(p))
                    self.assertEqual(str(pp), str(p))

    def test_repr_common(self):
        fuer pathstr in ('a', 'a/b', 'a/b/c', '/', '/a/b', '/a/b/c'):
            mit self.subTest(pathstr=pathstr):
                p = self.cls(pathstr)
                clsname = p.__class__.__name__
                r = repr(p)
                # The repr() is in the form ClassName("forward-slashes path").
                self.assertStartsWith(r, clsname + '(')
                self.assertEndsWith(r, ')')
                inner = r[len(clsname) + 1 : -1]
                self.assertEqual(eval(inner), p.as_posix())

    def test_fspath_common(self):
        P = self.cls
        p = P('a/b')
        self._check_str(p.__fspath__(), ('a/b',))
        self._check_str(os.fspath(p), ('a/b',))

    def test_bytes(self):
        P = self.cls
        mit self.assertRaises(TypeError):
            P(b'a')
        mit self.assertRaises(TypeError):
            P(b'a', 'b')
        mit self.assertRaises(TypeError):
            P('a', b'b')
        mit self.assertRaises(TypeError):
            P('a').joinpath(b'b')
        mit self.assertRaises(TypeError):
            P('a') / b'b'
        mit self.assertRaises(TypeError):
            b'a' / P('b')
        mit self.assertRaises(TypeError):
            P('a').match(b'b')
        mit self.assertRaises(TypeError):
            P('a').relative_to(b'b')
        mit self.assertRaises(TypeError):
            P('a').with_name(b'b')
        mit self.assertRaises(TypeError):
            P('a').with_stem(b'b')
        mit self.assertRaises(TypeError):
            P('a').with_suffix(b'b')

    def test_bytes_exc_message(self):
        P = self.cls
        message = (r"argument should be a str oder an os\.PathLike object "
                   r"where __fspath__ returns a str, nicht 'bytes'")
        mit self.assertRaisesRegex(TypeError, message):
            P(b'a')
        mit self.assertRaisesRegex(TypeError, message):
            P(b'a', 'b')
        mit self.assertRaisesRegex(TypeError, message):
            P('a', b'b')

    def test_as_bytes_common(self):
        sep = os.fsencode(self.sep)
        P = self.cls
        self.assertEqual(bytes(P('a/b')), b'a' + sep + b'b')

    def test_as_posix_common(self):
        P = self.cls
        fuer pathstr in ('a', 'a/b', 'a/b/c', '/', '/a/b', '/a/b/c'):
            self.assertEqual(P(pathstr).as_posix(), pathstr)
        # Other tests fuer as_posix() are in test_equivalences().

    def test_eq_common(self):
        P = self.cls
        self.assertEqual(P('a/b'), P('a/b'))
        self.assertEqual(P('a/b'), P('a', 'b'))
        self.assertNotEqual(P('a/b'), P('a'))
        self.assertNotEqual(P('a/b'), P('/a/b'))
        self.assertNotEqual(P('a/b'), P())
        self.assertNotEqual(P('/a/b'), P('/'))
        self.assertNotEqual(P(), P('/'))
        self.assertNotEqual(P(), "")
        self.assertNotEqual(P(), {})
        self.assertNotEqual(P(), int)

    def test_equivalences(self, equivalences=Nichts):
        wenn equivalences is Nichts:
            equivalences = self.equivalences
        fuer k, tuples in equivalences.items():
            canon = k.replace('/', self.sep)
            posix = k.replace(self.sep, '/')
            wenn canon != posix:
                tuples = tuples + [
                    tuple(part.replace('/', self.sep) fuer part in t)
                    fuer t in tuples
                    ]
                tuples.append((posix, ))
            pcanon = self.cls(canon)
            fuer t in tuples:
                p = self.cls(*t)
                self.assertEqual(p, pcanon, "failed mit args {}".format(t))
                self.assertEqual(hash(p), hash(pcanon))
                self.assertEqual(str(p), canon)
                self.assertEqual(p.as_posix(), posix)

    def test_ordering_common(self):
        # Ordering is tuple-alike.
        def assertLess(a, b):
            self.assertLess(a, b)
            self.assertGreater(b, a)
        P = self.cls
        a = P('a')
        b = P('a/b')
        c = P('abc')
        d = P('b')
        assertLess(a, b)
        assertLess(a, c)
        assertLess(a, d)
        assertLess(b, c)
        assertLess(c, d)
        P = self.cls
        a = P('/a')
        b = P('/a/b')
        c = P('/abc')
        d = P('/b')
        assertLess(a, b)
        assertLess(a, c)
        assertLess(a, d)
        assertLess(b, c)
        assertLess(c, d)
        mit self.assertRaises(TypeError):
            P() < {}

    def make_uri(self, path):
        wenn isinstance(path, pathlib.Path):
            gib path.as_uri()
        mit self.assertWarns(DeprecationWarning):
            gib path.as_uri()

    def test_as_uri_common(self):
        P = self.cls
        mit self.assertRaises(ValueError):
            self.make_uri(P('a'))
        mit self.assertRaises(ValueError):
            self.make_uri(P())

    def test_repr_roundtrips(self):
        fuer pathstr in ('a', 'a/b', 'a/b/c', '/', '/a/b', '/a/b/c'):
            mit self.subTest(pathstr=pathstr):
                p = self.cls(pathstr)
                r = repr(p)
                # The repr() roundtrips.
                q = eval(r, pathlib.__dict__)
                self.assertIs(q.__class__, p.__class__)
                self.assertEqual(q, p)
                self.assertEqual(repr(q), r)

    def test_drive_common(self):
        P = self.cls
        self.assertEqual(P('a/b').drive, '')
        self.assertEqual(P('/a/b').drive, '')
        self.assertEqual(P('').drive, '')

    @needs_windows
    def test_drive_windows(self):
        P = self.cls
        self.assertEqual(P('c:').drive, 'c:')
        self.assertEqual(P('c:a/b').drive, 'c:')
        self.assertEqual(P('c:/').drive, 'c:')
        self.assertEqual(P('c:/a/b/').drive, 'c:')
        self.assertEqual(P('//a/b').drive, '\\\\a\\b')
        self.assertEqual(P('//a/b/').drive, '\\\\a\\b')
        self.assertEqual(P('//a/b/c/d').drive, '\\\\a\\b')
        self.assertEqual(P('./c:a').drive, '')


    def test_root_common(self):
        P = self.cls
        sep = self.sep
        self.assertEqual(P('').root, '')
        self.assertEqual(P('a/b').root, '')
        self.assertEqual(P('/').root, sep)
        self.assertEqual(P('/a/b').root, sep)

    @needs_posix
    def test_root_posix(self):
        P = self.cls
        self.assertEqual(P('/a/b').root, '/')
        # POSIX special case fuer two leading slashes.
        self.assertEqual(P('//a/b').root, '//')

    @needs_windows
    def test_root_windows(self):
        P = self.cls
        self.assertEqual(P('c:').root, '')
        self.assertEqual(P('c:a/b').root, '')
        self.assertEqual(P('c:/').root, '\\')
        self.assertEqual(P('c:/a/b/').root, '\\')
        self.assertEqual(P('//a/b').root, '\\')
        self.assertEqual(P('//a/b/').root, '\\')
        self.assertEqual(P('//a/b/c/d').root, '\\')

    def test_name_empty(self):
        P = self.cls
        self.assertEqual(P('').name, '')
        self.assertEqual(P('.').name, '')
        self.assertEqual(P('/a/b/.').name, 'b')

    def test_stem_empty(self):
        P = self.cls
        self.assertEqual(P('').stem, '')
        self.assertEqual(P('.').stem, '')

    @needs_windows
    def test_with_name_windows(self):
        P = self.cls
        self.assertRaises(ValueError, P(r'c:').with_name, 'd.xml')
        self.assertRaises(ValueError, P(r'c:\\').with_name, 'd.xml')
        self.assertRaises(ValueError, P(r'\\My\Share').with_name, 'd.xml')
        # NTFS alternate data streams
        self.assertEqual(str(P('a').with_name('d:')), '.\\d:')
        self.assertEqual(str(P('a').with_name('d:e')), '.\\d:e')
        self.assertEqual(P(r'c:a\b').with_name('d:'), P(r'c:a\d:'))
        self.assertEqual(P(r'c:a\b').with_name('d:e'), P(r'c:a\d:e'))

    def test_with_name_empty(self):
        P = self.cls
        self.assertRaises(ValueError, P('').with_name, 'd.xml')
        self.assertRaises(ValueError, P('.').with_name, 'd.xml')
        self.assertRaises(ValueError, P('/').with_name, 'd.xml')
        self.assertRaises(ValueError, P('a/b').with_name, '')
        self.assertRaises(ValueError, P('a/b').with_name, '.')

    @needs_windows
    def test_with_stem_windows(self):
        P = self.cls
        self.assertRaises(ValueError, P('c:').with_stem, 'd')
        self.assertRaises(ValueError, P('c:/').with_stem, 'd')
        self.assertRaises(ValueError, P('//My/Share').with_stem, 'd')
        # NTFS alternate data streams
        self.assertEqual(str(P('a').with_stem('d:')), '.\\d:')
        self.assertEqual(str(P('a').with_stem('d:e')), '.\\d:e')
        self.assertEqual(P('c:a/b').with_stem('d:'), P('c:a/d:'))
        self.assertEqual(P('c:a/b').with_stem('d:e'), P('c:a/d:e'))

    def test_with_stem_empty(self):
        P = self.cls
        self.assertRaises(ValueError, P('').with_stem, 'd')
        self.assertRaises(ValueError, P('.').with_stem, 'd')
        self.assertRaises(ValueError, P('/').with_stem, 'd')
        self.assertRaises(ValueError, P('a/b').with_stem, '')
        self.assertRaises(ValueError, P('a/b').with_stem, '.')

    def test_full_match_case_sensitive(self):
        P = self.cls
        self.assertFalsch(P('A.py').full_match('a.PY', case_sensitive=Wahr))
        self.assertWahr(P('A.py').full_match('a.PY', case_sensitive=Falsch))
        self.assertFalsch(P('c:/a/B.Py').full_match('C:/A/*.pY', case_sensitive=Wahr))
        self.assertWahr(P('/a/b/c.py').full_match('/A/*/*.Py', case_sensitive=Falsch))

    def test_match_empty(self):
        P = self.cls
        self.assertRaises(ValueError, P('a').match, '')
        self.assertRaises(ValueError, P('a').match, '.')

    def test_match_common(self):
        P = self.cls
        # Simple relative pattern.
        self.assertWahr(P('b.py').match('b.py'))
        self.assertWahr(P('a/b.py').match('b.py'))
        self.assertWahr(P('/a/b.py').match('b.py'))
        self.assertFalsch(P('a.py').match('b.py'))
        self.assertFalsch(P('b/py').match('b.py'))
        self.assertFalsch(P('/a.py').match('b.py'))
        self.assertFalsch(P('b.py/c').match('b.py'))
        # Wildcard relative pattern.
        self.assertWahr(P('b.py').match('*.py'))
        self.assertWahr(P('a/b.py').match('*.py'))
        self.assertWahr(P('/a/b.py').match('*.py'))
        self.assertFalsch(P('b.pyc').match('*.py'))
        self.assertFalsch(P('b./py').match('*.py'))
        self.assertFalsch(P('b.py/c').match('*.py'))
        # Multi-part relative pattern.
        self.assertWahr(P('ab/c.py').match('a*/*.py'))
        self.assertWahr(P('/d/ab/c.py').match('a*/*.py'))
        self.assertFalsch(P('a.py').match('a*/*.py'))
        self.assertFalsch(P('/dab/c.py').match('a*/*.py'))
        self.assertFalsch(P('ab/c.py/d').match('a*/*.py'))
        # Absolute pattern.
        self.assertWahr(P('/b.py').match('/*.py'))
        self.assertFalsch(P('b.py').match('/*.py'))
        self.assertFalsch(P('a/b.py').match('/*.py'))
        self.assertFalsch(P('/a/b.py').match('/*.py'))
        # Multi-part absolute pattern.
        self.assertWahr(P('/a/b.py').match('/a/*.py'))
        self.assertFalsch(P('/ab.py').match('/a/*.py'))
        self.assertFalsch(P('/a/b/c.py').match('/a/*.py'))
        # Multi-part glob-style pattern.
        self.assertFalsch(P('/a/b/c.py').match('/**/*.py'))
        self.assertWahr(P('/a/b/c.py').match('/a/**/*.py'))
        # Case-sensitive flag
        self.assertFalsch(P('A.py').match('a.PY', case_sensitive=Wahr))
        self.assertWahr(P('A.py').match('a.PY', case_sensitive=Falsch))
        self.assertFalsch(P('c:/a/B.Py').match('C:/A/*.pY', case_sensitive=Wahr))
        self.assertWahr(P('/a/b/c.py').match('/A/*/*.Py', case_sensitive=Falsch))
        # Matching against empty path
        self.assertFalsch(P('').match('*'))
        self.assertFalsch(P('').match('**'))
        self.assertFalsch(P('').match('**/*'))

    @needs_posix
    def test_match_posix(self):
        P = self.cls
        self.assertFalsch(P('A.py').match('a.PY'))

    @needs_windows
    def test_match_windows(self):
        P = self.cls
        # Absolute patterns.
        self.assertWahr(P('c:/b.py').match('*:/*.py'))
        self.assertWahr(P('c:/b.py').match('c:/*.py'))
        self.assertFalsch(P('d:/b.py').match('c:/*.py'))  # wrong drive
        self.assertFalsch(P('b.py').match('/*.py'))
        self.assertFalsch(P('b.py').match('c:*.py'))
        self.assertFalsch(P('b.py').match('c:/*.py'))
        self.assertFalsch(P('c:b.py').match('/*.py'))
        self.assertFalsch(P('c:b.py').match('c:/*.py'))
        self.assertFalsch(P('/b.py').match('c:*.py'))
        self.assertFalsch(P('/b.py').match('c:/*.py'))
        # UNC patterns.
        self.assertWahr(P('//some/share/a.py').match('//*/*/*.py'))
        self.assertWahr(P('//some/share/a.py').match('//some/share/*.py'))
        self.assertFalsch(P('//other/share/a.py').match('//some/share/*.py'))
        self.assertFalsch(P('//some/share/a/b.py').match('//some/share/*.py'))
        # Case-insensitivity.
        self.assertWahr(P('B.py').match('b.PY'))
        self.assertWahr(P('c:/a/B.Py').match('C:/A/*.pY'))
        self.assertWahr(P('//Some/Share/B.Py').match('//somE/sharE/*.pY'))
        # Path anchor doesn't match pattern anchor
        self.assertFalsch(P('c:/b.py').match('/*.py'))  # 'c:/' vs '/'
        self.assertFalsch(P('c:/b.py').match('c:*.py'))  # 'c:/' vs 'c:'
        self.assertFalsch(P('//some/share/a.py').match('/*.py'))  # '//some/share/' vs '/'

    @needs_posix
    def test_parse_path_posix(self):
        check = self._check_parse_path
        # Collapsing of excess leading slashes, ausser fuer the double-slash
        # special case.
        check('//a/b',   '', '//', ['a', 'b'])
        check('///a/b',  '', '/', ['a', 'b'])
        check('////a/b', '', '/', ['a', 'b'])
        # Paths which look like NT paths aren't treated specially.
        check('c:a',     '', '', ['c:a',])
        check('c:\\a',   '', '', ['c:\\a',])
        check('\\a',     '', '', ['\\a',])

    @needs_posix
    def test_eq_posix(self):
        P = self.cls
        self.assertNotEqual(P('a/b'), P('A/b'))
        self.assertEqual(P('/a'), P('///a'))
        self.assertNotEqual(P('/a'), P('//a'))

    @needs_posix
    def test_as_uri_posix(self):
        P = self.cls
        self.assertEqual(self.make_uri(P('/')), 'file:///')
        self.assertEqual(self.make_uri(P('/a/b.c')), 'file:///a/b.c')
        self.assertEqual(self.make_uri(P('/a/b%#c')), 'file:///a/b%25%23c')

    @needs_posix
    def test_as_uri_non_ascii(self):
        von urllib.parse importiere quote_from_bytes
        P = self.cls
        versuch:
            os.fsencode('\xe9')
        ausser UnicodeEncodeError:
            self.skipTest("\\xe9 cannot be encoded to the filesystem encoding")
        self.assertEqual(self.make_uri(P('/a/b\xe9')),
                         'file:///a/b' + quote_from_bytes(os.fsencode('\xe9')))

    @needs_posix
    def test_parse_windows_path(self):
        P = self.cls
        p = P('c:', 'a', 'b')
        pp = P(pathlib.PureWindowsPath('c:\\a\\b'))
        self.assertEqual(p, pp)

    windows_equivalences = {
        './a:b': [ ('./a:b',) ],
        'c:a': [ ('c:', 'a'), ('c:', 'a/'), ('.', 'c:', 'a') ],
        'c:/a': [
            ('c:/', 'a'), ('c:', '/', 'a'), ('c:', '/a'),
            ('/z', 'c:/', 'a'), ('//x/y', 'c:/', 'a'),
            ],
        '//a/b/': [ ('//a/b',) ],
        '//a/b/c': [
            ('//a/b', 'c'), ('//a/b/', 'c'),
            ],
    }

    @needs_windows
    def test_equivalences_windows(self):
        self.test_equivalences(self.windows_equivalences)

    @needs_windows
    def test_parse_path_windows(self):
        check = self._check_parse_path
        # First part is anchored.
        check('c:',                  'c:', '', [])
        check('c:/',                 'c:', '\\', [])
        check('/',                   '', '\\', [])
        check('c:a',                 'c:', '', ['a'])
        check('c:/a',                'c:', '\\', ['a'])
        check('/a',                  '', '\\', ['a'])
        # UNC paths.
        check('//',                  '\\\\', '', [])
        check('//a',                 '\\\\a', '', [])
        check('//a/',                '\\\\a\\', '', [])
        check('//a/b',               '\\\\a\\b', '\\', [])
        check('//a/b/',              '\\\\a\\b', '\\', [])
        check('//a/b/c',             '\\\\a\\b', '\\', ['c'])
        # Collapsing und stripping excess slashes.
        check('Z://b//c/d/',         'Z:', '\\', ['b', 'c', 'd'])
        # UNC paths.
        check('//b/c//d',            '\\\\b\\c', '\\', ['d'])
        # Extended paths.
        check('//./c:',              '\\\\.\\c:', '', [])
        check('//?/c:/',             '\\\\?\\c:', '\\', [])
        check('//?/c:/a',            '\\\\?\\c:', '\\', ['a'])
        # Extended UNC paths (format is "\\?\UNC\server\share").
        check('//?',                 '\\\\?', '', [])
        check('//?/',                '\\\\?\\', '', [])
        check('//?/UNC',             '\\\\?\\UNC', '', [])
        check('//?/UNC/',            '\\\\?\\UNC\\', '', [])
        check('//?/UNC/b',           '\\\\?\\UNC\\b', '', [])
        check('//?/UNC/b/',          '\\\\?\\UNC\\b\\', '', [])
        check('//?/UNC/b/c',         '\\\\?\\UNC\\b\\c', '\\', [])
        check('//?/UNC/b/c/',        '\\\\?\\UNC\\b\\c', '\\', [])
        check('//?/UNC/b/c/d',       '\\\\?\\UNC\\b\\c', '\\', ['d'])
        # UNC device paths
        check('//./BootPartition/',  '\\\\.\\BootPartition', '\\', [])
        check('//?/BootPartition/',  '\\\\?\\BootPartition', '\\', [])
        check('//./PhysicalDrive0',  '\\\\.\\PhysicalDrive0', '', [])
        check('//?/Volume{}/',       '\\\\?\\Volume{}', '\\', [])
        check('//./nul',             '\\\\.\\nul', '', [])
        # Paths to files mit NTFS alternate data streams
        check('./c:s',               '', '', ['c:s'])
        check('cc:s',                '', '', ['cc:s'])
        check('C:c:s',               'C:', '', ['c:s'])
        check('C:/c:s',              'C:', '\\', ['c:s'])
        check('D:a/c:b',             'D:', '', ['a', 'c:b'])
        check('D:/a/c:b',            'D:', '\\', ['a', 'c:b'])

    @needs_windows
    def test_eq_windows(self):
        P = self.cls
        self.assertEqual(P('c:a/b'), P('c:a/b'))
        self.assertEqual(P('c:a/b'), P('c:', 'a', 'b'))
        self.assertNotEqual(P('c:a/b'), P('d:a/b'))
        self.assertNotEqual(P('c:a/b'), P('c:/a/b'))
        self.assertNotEqual(P('/a/b'), P('c:/a/b'))
        # Case-insensitivity.
        self.assertEqual(P('a/B'), P('A/b'))
        self.assertEqual(P('C:a/B'), P('c:A/b'))
        self.assertEqual(P('//Some/SHARE/a/B'), P('//somE/share/A/b'))
        self.assertEqual(P('\u0130'), P('i\u0307'))

    @needs_windows
    def test_as_uri_windows(self):
        P = self.cls
        mit self.assertRaises(ValueError):
            self.make_uri(P('/a/b'))
        mit self.assertRaises(ValueError):
            self.make_uri(P('c:a/b'))
        self.assertEqual(self.make_uri(P('c:/')), 'file:///c:/')
        self.assertEqual(self.make_uri(P('c:/a/b.c')), 'file:///c:/a/b.c')
        self.assertEqual(self.make_uri(P('c:/a/b%#c')), 'file:///c:/a/b%25%23c')
        self.assertEqual(self.make_uri(P('//some/share/')), 'file://some/share/')
        self.assertEqual(self.make_uri(P('//some/share/a/b.c')),
                         'file://some/share/a/b.c')

        von urllib.parse importiere quote_from_bytes
        QUOTED_FS_NONASCII = quote_from_bytes(os.fsencode(FS_NONASCII))
        self.assertEqual(self.make_uri(P('c:/a/b' + FS_NONASCII)),
                         'file:///c:/a/b' + QUOTED_FS_NONASCII)
        self.assertEqual(self.make_uri(P('//some/share/a/b%#c' + FS_NONASCII)),
                         'file://some/share/a/b%25%23c' + QUOTED_FS_NONASCII)

    @needs_windows
    def test_ordering_windows(self):
        # Case-insensitivity.
        def assertOrderedEqual(a, b):
            self.assertLessEqual(a, b)
            self.assertGreaterEqual(b, a)
        P = self.cls
        p = P('c:A/b')
        q = P('C:a/B')
        assertOrderedEqual(p, q)
        self.assertFalsch(p < q)
        self.assertFalsch(p > q)
        p = P('//some/Share/A/b')
        q = P('//Some/SHARE/a/B')
        assertOrderedEqual(p, q)
        self.assertFalsch(p < q)
        self.assertFalsch(p > q)

    @needs_posix
    def test_is_absolute_posix(self):
        P = self.cls
        self.assertFalsch(P('').is_absolute())
        self.assertFalsch(P('a').is_absolute())
        self.assertFalsch(P('a/b/').is_absolute())
        self.assertWahr(P('/').is_absolute())
        self.assertWahr(P('/a').is_absolute())
        self.assertWahr(P('/a/b/').is_absolute())
        self.assertWahr(P('//a').is_absolute())
        self.assertWahr(P('//a/b').is_absolute())

    @needs_windows
    def test_is_absolute_windows(self):
        P = self.cls
        # Under NT, only paths mit both a drive und a root are absolute.
        self.assertFalsch(P().is_absolute())
        self.assertFalsch(P('a').is_absolute())
        self.assertFalsch(P('a/b/').is_absolute())
        self.assertFalsch(P('/').is_absolute())
        self.assertFalsch(P('/a').is_absolute())
        self.assertFalsch(P('/a/b/').is_absolute())
        self.assertFalsch(P('c:').is_absolute())
        self.assertFalsch(P('c:a').is_absolute())
        self.assertFalsch(P('c:a/b/').is_absolute())
        self.assertWahr(P('c:/').is_absolute())
        self.assertWahr(P('c:/a').is_absolute())
        self.assertWahr(P('c:/a/b/').is_absolute())
        # UNC paths are absolute by definition.
        self.assertWahr(P('//').is_absolute())
        self.assertWahr(P('//a').is_absolute())
        self.assertWahr(P('//a/b').is_absolute())
        self.assertWahr(P('//a/b/').is_absolute())
        self.assertWahr(P('//a/b/c').is_absolute())
        self.assertWahr(P('//a/b/c/d').is_absolute())
        self.assertWahr(P('//?/UNC/').is_absolute())
        self.assertWahr(P('//?/UNC/spam').is_absolute())

    def test_relative_to_common(self):
        P = self.cls
        p = P('a/b')
        self.assertRaises(TypeError, p.relative_to)
        self.assertRaises(TypeError, p.relative_to, b'a')
        self.assertEqual(p.relative_to(P('')), P('a/b'))
        self.assertEqual(p.relative_to(''), P('a/b'))
        self.assertEqual(p.relative_to(P('a')), P('b'))
        self.assertEqual(p.relative_to('a'), P('b'))
        self.assertEqual(p.relative_to('a/'), P('b'))
        self.assertEqual(p.relative_to(P('a/b')), P(''))
        self.assertEqual(p.relative_to('a/b'), P(''))
        self.assertEqual(p.relative_to(P(''), walk_up=Wahr), P('a/b'))
        self.assertEqual(p.relative_to('', walk_up=Wahr), P('a/b'))
        self.assertEqual(p.relative_to(P('a'), walk_up=Wahr), P('b'))
        self.assertEqual(p.relative_to('a', walk_up=Wahr), P('b'))
        self.assertEqual(p.relative_to('a/', walk_up=Wahr), P('b'))
        self.assertEqual(p.relative_to(P('a/b'), walk_up=Wahr), P(''))
        self.assertEqual(p.relative_to('a/b', walk_up=Wahr), P(''))
        self.assertEqual(p.relative_to(P('a/c'), walk_up=Wahr), P('../b'))
        self.assertEqual(p.relative_to('a/c', walk_up=Wahr), P('../b'))
        self.assertEqual(p.relative_to(P('a/b/c'), walk_up=Wahr), P('..'))
        self.assertEqual(p.relative_to('a/b/c', walk_up=Wahr), P('..'))
        self.assertEqual(p.relative_to(P('c'), walk_up=Wahr), P('../a/b'))
        self.assertEqual(p.relative_to('c', walk_up=Wahr), P('../a/b'))
        # Unrelated paths.
        self.assertRaises(ValueError, p.relative_to, P('c'))
        self.assertRaises(ValueError, p.relative_to, P('a/b/c'))
        self.assertRaises(ValueError, p.relative_to, P('a/c'))
        self.assertRaises(ValueError, p.relative_to, P('/a'))
        self.assertRaises(ValueError, p.relative_to, P("../a"))
        self.assertRaises(ValueError, p.relative_to, P("a/.."))
        self.assertRaises(ValueError, p.relative_to, P("/a/.."))
        self.assertRaises(ValueError, p.relative_to, P('/'), walk_up=Wahr)
        self.assertRaises(ValueError, p.relative_to, P('/a'), walk_up=Wahr)
        self.assertRaises(ValueError, p.relative_to, P("../a"), walk_up=Wahr)
        self.assertRaises(ValueError, p.relative_to, P("a/.."), walk_up=Wahr)
        self.assertRaises(ValueError, p.relative_to, P("/a/.."), walk_up=Wahr)
        p = P('/a/b')
        self.assertEqual(p.relative_to(P('/')), P('a/b'))
        self.assertEqual(p.relative_to('/'), P('a/b'))
        self.assertEqual(p.relative_to(P('/a')), P('b'))
        self.assertEqual(p.relative_to('/a'), P('b'))
        self.assertEqual(p.relative_to('/a/'), P('b'))
        self.assertEqual(p.relative_to(P('/a/b')), P(''))
        self.assertEqual(p.relative_to('/a/b'), P(''))
        self.assertEqual(p.relative_to(P('/'), walk_up=Wahr), P('a/b'))
        self.assertEqual(p.relative_to('/', walk_up=Wahr), P('a/b'))
        self.assertEqual(p.relative_to(P('/a'), walk_up=Wahr), P('b'))
        self.assertEqual(p.relative_to('/a', walk_up=Wahr), P('b'))
        self.assertEqual(p.relative_to('/a/', walk_up=Wahr), P('b'))
        self.assertEqual(p.relative_to(P('/a/b'), walk_up=Wahr), P(''))
        self.assertEqual(p.relative_to('/a/b', walk_up=Wahr), P(''))
        self.assertEqual(p.relative_to(P('/a/c'), walk_up=Wahr), P('../b'))
        self.assertEqual(p.relative_to('/a/c', walk_up=Wahr), P('../b'))
        self.assertEqual(p.relative_to(P('/a/b/c'), walk_up=Wahr), P('..'))
        self.assertEqual(p.relative_to('/a/b/c', walk_up=Wahr), P('..'))
        self.assertEqual(p.relative_to(P('/c'), walk_up=Wahr), P('../a/b'))
        self.assertEqual(p.relative_to('/c', walk_up=Wahr), P('../a/b'))
        # Unrelated paths.
        self.assertRaises(ValueError, p.relative_to, P('/c'))
        self.assertRaises(ValueError, p.relative_to, P('/a/b/c'))
        self.assertRaises(ValueError, p.relative_to, P('/a/c'))
        self.assertRaises(ValueError, p.relative_to, P(''))
        self.assertRaises(ValueError, p.relative_to, '')
        self.assertRaises(ValueError, p.relative_to, P('a'))
        self.assertRaises(ValueError, p.relative_to, P("../a"))
        self.assertRaises(ValueError, p.relative_to, P("a/.."))
        self.assertRaises(ValueError, p.relative_to, P("/a/.."))
        self.assertRaises(ValueError, p.relative_to, P(''), walk_up=Wahr)
        self.assertRaises(ValueError, p.relative_to, P('a'), walk_up=Wahr)
        self.assertRaises(ValueError, p.relative_to, P("../a"), walk_up=Wahr)
        self.assertRaises(ValueError, p.relative_to, P("a/.."), walk_up=Wahr)
        self.assertRaises(ValueError, p.relative_to, P("/a/.."), walk_up=Wahr)

    @needs_windows
    def test_relative_to_windows(self):
        P = self.cls
        p = P('C:Foo/Bar')
        self.assertEqual(p.relative_to(P('c:')), P('Foo/Bar'))
        self.assertEqual(p.relative_to('c:'), P('Foo/Bar'))
        self.assertEqual(p.relative_to(P('c:foO')), P('Bar'))
        self.assertEqual(p.relative_to('c:foO'), P('Bar'))
        self.assertEqual(p.relative_to('c:foO/'), P('Bar'))
        self.assertEqual(p.relative_to(P('c:foO/baR')), P())
        self.assertEqual(p.relative_to('c:foO/baR'), P())
        self.assertEqual(p.relative_to(P('c:'), walk_up=Wahr), P('Foo/Bar'))
        self.assertEqual(p.relative_to('c:', walk_up=Wahr), P('Foo/Bar'))
        self.assertEqual(p.relative_to(P('c:foO'), walk_up=Wahr), P('Bar'))
        self.assertEqual(p.relative_to('c:foO', walk_up=Wahr), P('Bar'))
        self.assertEqual(p.relative_to('c:foO/', walk_up=Wahr), P('Bar'))
        self.assertEqual(p.relative_to(P('c:foO/baR'), walk_up=Wahr), P())
        self.assertEqual(p.relative_to('c:foO/baR', walk_up=Wahr), P())
        self.assertEqual(p.relative_to(P('C:Foo/Bar/Baz'), walk_up=Wahr), P('..'))
        self.assertEqual(p.relative_to(P('C:Foo/Baz'), walk_up=Wahr), P('../Bar'))
        self.assertEqual(p.relative_to(P('C:Baz/Bar'), walk_up=Wahr), P('../../Foo/Bar'))
        # Unrelated paths.
        self.assertRaises(ValueError, p.relative_to, P())
        self.assertRaises(ValueError, p.relative_to, '')
        self.assertRaises(ValueError, p.relative_to, P('d:'))
        self.assertRaises(ValueError, p.relative_to, P('/'))
        self.assertRaises(ValueError, p.relative_to, P('Foo'))
        self.assertRaises(ValueError, p.relative_to, P('/Foo'))
        self.assertRaises(ValueError, p.relative_to, P('C:/Foo'))
        self.assertRaises(ValueError, p.relative_to, P('C:Foo/Bar/Baz'))
        self.assertRaises(ValueError, p.relative_to, P('C:Foo/Baz'))
        self.assertRaises(ValueError, p.relative_to, P(), walk_up=Wahr)
        self.assertRaises(ValueError, p.relative_to, '', walk_up=Wahr)
        self.assertRaises(ValueError, p.relative_to, P('d:'), walk_up=Wahr)
        self.assertRaises(ValueError, p.relative_to, P('/'), walk_up=Wahr)
        self.assertRaises(ValueError, p.relative_to, P('Foo'), walk_up=Wahr)
        self.assertRaises(ValueError, p.relative_to, P('/Foo'), walk_up=Wahr)
        self.assertRaises(ValueError, p.relative_to, P('C:/Foo'), walk_up=Wahr)
        p = P('C:/Foo/Bar')
        self.assertEqual(p.relative_to(P('c:/')), P('Foo/Bar'))
        self.assertEqual(p.relative_to('c:/'), P('Foo/Bar'))
        self.assertEqual(p.relative_to(P('c:/foO')), P('Bar'))
        self.assertEqual(p.relative_to('c:/foO'), P('Bar'))
        self.assertEqual(p.relative_to('c:/foO/'), P('Bar'))
        self.assertEqual(p.relative_to(P('c:/foO/baR')), P())
        self.assertEqual(p.relative_to('c:/foO/baR'), P())
        self.assertEqual(p.relative_to(P('c:/'), walk_up=Wahr), P('Foo/Bar'))
        self.assertEqual(p.relative_to('c:/', walk_up=Wahr), P('Foo/Bar'))
        self.assertEqual(p.relative_to(P('c:/foO'), walk_up=Wahr), P('Bar'))
        self.assertEqual(p.relative_to('c:/foO', walk_up=Wahr), P('Bar'))
        self.assertEqual(p.relative_to('c:/foO/', walk_up=Wahr), P('Bar'))
        self.assertEqual(p.relative_to(P('c:/foO/baR'), walk_up=Wahr), P())
        self.assertEqual(p.relative_to('c:/foO/baR', walk_up=Wahr), P())
        self.assertEqual(p.relative_to('C:/Baz', walk_up=Wahr), P('../Foo/Bar'))
        self.assertEqual(p.relative_to('C:/Foo/Bar/Baz', walk_up=Wahr), P('..'))
        self.assertEqual(p.relative_to('C:/Foo/Baz', walk_up=Wahr), P('../Bar'))
        # Unrelated paths.
        self.assertRaises(ValueError, p.relative_to, 'c:')
        self.assertRaises(ValueError, p.relative_to, P('c:'))
        self.assertRaises(ValueError, p.relative_to, P('C:/Baz'))
        self.assertRaises(ValueError, p.relative_to, P('C:/Foo/Bar/Baz'))
        self.assertRaises(ValueError, p.relative_to, P('C:/Foo/Baz'))
        self.assertRaises(ValueError, p.relative_to, P('C:Foo'))
        self.assertRaises(ValueError, p.relative_to, P('d:'))
        self.assertRaises(ValueError, p.relative_to, P('d:/'))
        self.assertRaises(ValueError, p.relative_to, P('/'))
        self.assertRaises(ValueError, p.relative_to, P('/Foo'))
        self.assertRaises(ValueError, p.relative_to, P('//C/Foo'))
        self.assertRaises(ValueError, p.relative_to, 'c:', walk_up=Wahr)
        self.assertRaises(ValueError, p.relative_to, P('c:'), walk_up=Wahr)
        self.assertRaises(ValueError, p.relative_to, P('C:Foo'), walk_up=Wahr)
        self.assertRaises(ValueError, p.relative_to, P('d:'), walk_up=Wahr)
        self.assertRaises(ValueError, p.relative_to, P('d:/'), walk_up=Wahr)
        self.assertRaises(ValueError, p.relative_to, P('/'), walk_up=Wahr)
        self.assertRaises(ValueError, p.relative_to, P('/Foo'), walk_up=Wahr)
        self.assertRaises(ValueError, p.relative_to, P('//C/Foo'), walk_up=Wahr)
        # UNC paths.
        p = P('//Server/Share/Foo/Bar')
        self.assertEqual(p.relative_to(P('//sErver/sHare')), P('Foo/Bar'))
        self.assertEqual(p.relative_to('//sErver/sHare'), P('Foo/Bar'))
        self.assertEqual(p.relative_to('//sErver/sHare/'), P('Foo/Bar'))
        self.assertEqual(p.relative_to(P('//sErver/sHare/Foo')), P('Bar'))
        self.assertEqual(p.relative_to('//sErver/sHare/Foo'), P('Bar'))
        self.assertEqual(p.relative_to('//sErver/sHare/Foo/'), P('Bar'))
        self.assertEqual(p.relative_to(P('//sErver/sHare/Foo/Bar')), P())
        self.assertEqual(p.relative_to('//sErver/sHare/Foo/Bar'), P())
        self.assertEqual(p.relative_to(P('//sErver/sHare'), walk_up=Wahr), P('Foo/Bar'))
        self.assertEqual(p.relative_to('//sErver/sHare', walk_up=Wahr), P('Foo/Bar'))
        self.assertEqual(p.relative_to('//sErver/sHare/', walk_up=Wahr), P('Foo/Bar'))
        self.assertEqual(p.relative_to(P('//sErver/sHare/Foo'), walk_up=Wahr), P('Bar'))
        self.assertEqual(p.relative_to('//sErver/sHare/Foo', walk_up=Wahr), P('Bar'))
        self.assertEqual(p.relative_to('//sErver/sHare/Foo/', walk_up=Wahr), P('Bar'))
        self.assertEqual(p.relative_to(P('//sErver/sHare/Foo/Bar'), walk_up=Wahr), P())
        self.assertEqual(p.relative_to('//sErver/sHare/Foo/Bar', walk_up=Wahr), P())
        self.assertEqual(p.relative_to(P('//sErver/sHare/bar'), walk_up=Wahr), P('../Foo/Bar'))
        self.assertEqual(p.relative_to('//sErver/sHare/bar', walk_up=Wahr), P('../Foo/Bar'))
        # Unrelated paths.
        self.assertRaises(ValueError, p.relative_to, P('/Server/Share/Foo'))
        self.assertRaises(ValueError, p.relative_to, P('c:/Server/Share/Foo'))
        self.assertRaises(ValueError, p.relative_to, P('//z/Share/Foo'))
        self.assertRaises(ValueError, p.relative_to, P('//Server/z/Foo'))
        self.assertRaises(ValueError, p.relative_to, P('/Server/Share/Foo'), walk_up=Wahr)
        self.assertRaises(ValueError, p.relative_to, P('c:/Server/Share/Foo'), walk_up=Wahr)
        self.assertRaises(ValueError, p.relative_to, P('//z/Share/Foo'), walk_up=Wahr)
        self.assertRaises(ValueError, p.relative_to, P('//Server/z/Foo'), walk_up=Wahr)

    def test_is_relative_to_common(self):
        P = self.cls
        p = P('a/b')
        self.assertRaises(TypeError, p.is_relative_to)
        self.assertRaises(TypeError, p.is_relative_to, b'a')
        self.assertWahr(p.is_relative_to(P('')))
        self.assertWahr(p.is_relative_to(''))
        self.assertWahr(p.is_relative_to(P('a')))
        self.assertWahr(p.is_relative_to('a/'))
        self.assertWahr(p.is_relative_to(P('a/b')))
        self.assertWahr(p.is_relative_to('a/b'))
        # Unrelated paths.
        self.assertFalsch(p.is_relative_to(P('c')))
        self.assertFalsch(p.is_relative_to(P('a/b/c')))
        self.assertFalsch(p.is_relative_to(P('a/c')))
        self.assertFalsch(p.is_relative_to(P('/a')))
        p = P('/a/b')
        self.assertWahr(p.is_relative_to(P('/')))
        self.assertWahr(p.is_relative_to('/'))
        self.assertWahr(p.is_relative_to(P('/a')))
        self.assertWahr(p.is_relative_to('/a'))
        self.assertWahr(p.is_relative_to('/a/'))
        self.assertWahr(p.is_relative_to(P('/a/b')))
        self.assertWahr(p.is_relative_to('/a/b'))
        # Unrelated paths.
        self.assertFalsch(p.is_relative_to(P('/c')))
        self.assertFalsch(p.is_relative_to(P('/a/b/c')))
        self.assertFalsch(p.is_relative_to(P('/a/c')))
        self.assertFalsch(p.is_relative_to(P('')))
        self.assertFalsch(p.is_relative_to(''))
        self.assertFalsch(p.is_relative_to(P('a')))

    @needs_windows
    def test_is_relative_to_windows(self):
        P = self.cls
        p = P('C:Foo/Bar')
        self.assertWahr(p.is_relative_to(P('c:')))
        self.assertWahr(p.is_relative_to('c:'))
        self.assertWahr(p.is_relative_to(P('c:foO')))
        self.assertWahr(p.is_relative_to('c:foO'))
        self.assertWahr(p.is_relative_to('c:foO/'))
        self.assertWahr(p.is_relative_to(P('c:foO/baR')))
        self.assertWahr(p.is_relative_to('c:foO/baR'))
        # Unrelated paths.
        self.assertFalsch(p.is_relative_to(P()))
        self.assertFalsch(p.is_relative_to(''))
        self.assertFalsch(p.is_relative_to(P('d:')))
        self.assertFalsch(p.is_relative_to(P('/')))
        self.assertFalsch(p.is_relative_to(P('Foo')))
        self.assertFalsch(p.is_relative_to(P('/Foo')))
        self.assertFalsch(p.is_relative_to(P('C:/Foo')))
        self.assertFalsch(p.is_relative_to(P('C:Foo/Bar/Baz')))
        self.assertFalsch(p.is_relative_to(P('C:Foo/Baz')))
        p = P('C:/Foo/Bar')
        self.assertWahr(p.is_relative_to(P('c:/')))
        self.assertWahr(p.is_relative_to(P('c:/foO')))
        self.assertWahr(p.is_relative_to('c:/foO/'))
        self.assertWahr(p.is_relative_to(P('c:/foO/baR')))
        self.assertWahr(p.is_relative_to('c:/foO/baR'))
        # Unrelated paths.
        self.assertFalsch(p.is_relative_to('c:'))
        self.assertFalsch(p.is_relative_to(P('C:/Baz')))
        self.assertFalsch(p.is_relative_to(P('C:/Foo/Bar/Baz')))
        self.assertFalsch(p.is_relative_to(P('C:/Foo/Baz')))
        self.assertFalsch(p.is_relative_to(P('C:Foo')))
        self.assertFalsch(p.is_relative_to(P('d:')))
        self.assertFalsch(p.is_relative_to(P('d:/')))
        self.assertFalsch(p.is_relative_to(P('/')))
        self.assertFalsch(p.is_relative_to(P('/Foo')))
        self.assertFalsch(p.is_relative_to(P('//C/Foo')))
        # UNC paths.
        p = P('//Server/Share/Foo/Bar')
        self.assertWahr(p.is_relative_to(P('//sErver/sHare')))
        self.assertWahr(p.is_relative_to('//sErver/sHare'))
        self.assertWahr(p.is_relative_to('//sErver/sHare/'))
        self.assertWahr(p.is_relative_to(P('//sErver/sHare/Foo')))
        self.assertWahr(p.is_relative_to('//sErver/sHare/Foo'))
        self.assertWahr(p.is_relative_to('//sErver/sHare/Foo/'))
        self.assertWahr(p.is_relative_to(P('//sErver/sHare/Foo/Bar')))
        self.assertWahr(p.is_relative_to('//sErver/sHare/Foo/Bar'))
        # Unrelated paths.
        self.assertFalsch(p.is_relative_to(P('/Server/Share/Foo')))
        self.assertFalsch(p.is_relative_to(P('c:/Server/Share/Foo')))
        self.assertFalsch(p.is_relative_to(P('//z/Share/Foo')))
        self.assertFalsch(p.is_relative_to(P('//Server/z/Foo')))


klasse PurePosixPathTest(PurePathTest):
    cls = pathlib.PurePosixPath


klasse PureWindowsPathTest(PurePathTest):
    cls = pathlib.PureWindowsPath


klasse PurePathSubclassTest(PurePathTest):
    klasse cls(pathlib.PurePath):
        pass

    # repr() roundtripping is nicht supported in custom subclass.
    test_repr_roundtrips = Nichts


#
# Tests fuer the concrete classes.
#

klasse PathTest(PurePathTest):
    """Tests fuer the FS-accessing functionalities of the Path classes."""
    cls = pathlib.Path
    can_symlink = os_helper.can_symlink()

    def setUp(self):
        name = self.id().split('.')[-1]
        wenn name in _tests_needing_symlinks und nicht self.can_symlink:
            self.skipTest('requires symlinks')
        super().setUp()
        os.mkdir(self.base)
        os.mkdir(os.path.join(self.base, 'dirA'))
        os.mkdir(os.path.join(self.base, 'dirB'))
        os.mkdir(os.path.join(self.base, 'dirC'))
        os.mkdir(os.path.join(self.base, 'dirC', 'dirD'))
        os.mkdir(os.path.join(self.base, 'dirE'))
        mit open(os.path.join(self.base, 'fileA'), 'wb') als f:
            f.write(b"this is file A\n")
        mit open(os.path.join(self.base, 'dirB', 'fileB'), 'wb') als f:
            f.write(b"this is file B\n")
        mit open(os.path.join(self.base, 'dirC', 'fileC'), 'wb') als f:
            f.write(b"this is file C\n")
        mit open(os.path.join(self.base, 'dirC', 'novel.txt'), 'wb') als f:
            f.write(b"this is a novel\n")
        mit open(os.path.join(self.base, 'dirC', 'dirD', 'fileD'), 'wb') als f:
            f.write(b"this is file D\n")
        os.chmod(os.path.join(self.base, 'dirE'), 0)
        wenn self.can_symlink:
            # Relative symlinks.
            os.symlink('fileA', os.path.join(self.base, 'linkA'))
            os.symlink('non-existing', os.path.join(self.base, 'brokenLink'))
            os.symlink('dirB',
                       os.path.join(self.base, 'linkB'),
                       target_is_directory=Wahr)
            os.symlink(os.path.join('..', 'dirB'),
                       os.path.join(self.base, 'dirA', 'linkC'),
                       target_is_directory=Wahr)
            # This one goes upwards, creating a loop.
            os.symlink(os.path.join('..', 'dirB'),
                       os.path.join(self.base, 'dirB', 'linkD'),
                       target_is_directory=Wahr)
            # Broken symlink (pointing to itself).
            os.symlink('brokenLinkLoop', os.path.join(self.base, 'brokenLinkLoop'))

    def tearDown(self):
        os.chmod(os.path.join(self.base, 'dirE'), 0o777)
        os_helper.rmtree(self.base)

    def assertFileNotFound(self, func, *args, **kwargs):
        mit self.assertRaises(FileNotFoundError) als cm:
            func(*args, **kwargs)
        self.assertEqual(cm.exception.errno, errno.ENOENT)

    def assertEqualNormCase(self, path_a, path_b):
        normcase = self.parser.normcase
        self.assertEqual(normcase(path_a), normcase(path_b))

    def tempdir(self):
        d = os_helper._longpath(tempfile.mkdtemp(suffix='-dirD',
                                                 dir=os.getcwd()))
        self.addCleanup(os_helper.rmtree, d)
        gib d

    def test_matches_writablepath_docstrings(self):
        path_names = {name fuer name in dir(pathlib.types._WritablePath) wenn name[0] != '_'}
        fuer attr_name in path_names:
            wenn attr_name == 'parser':
                # On Windows, Path.parser is ntpath, but WritablePath.parser is
                # posixpath, und so their docstrings differ.
                weiter
            our_attr = getattr(self.cls, attr_name)
            path_attr = getattr(pathlib.types._WritablePath, attr_name)
            self.assertEqual(our_attr.__doc__, path_attr.__doc__)

    def test_concrete_class(self):
        wenn self.cls is pathlib.Path:
            expected = pathlib.WindowsPath wenn os.name == 'nt' sonst pathlib.PosixPath
        sonst:
            expected = self.cls
        p = self.cls('a')
        self.assertIs(type(p), expected)

    def test_unsupported_parser(self):
        wenn self.cls.parser is os.path:
            self.skipTest("path parser is supported")
        sonst:
            self.assertRaises(pathlib.UnsupportedOperation, self.cls)

    def _test_cwd(self, p):
        q = self.cls(os.getcwd())
        self.assertEqual(p, q)
        self.assertEqualNormCase(str(p), str(q))
        self.assertIs(type(p), type(q))
        self.assertWahr(p.is_absolute())

    def test_cwd(self):
        p = self.cls.cwd()
        self._test_cwd(p)

    def test_absolute_common(self):
        P = self.cls

        mit mock.patch("os.getcwd") als getcwd:
            getcwd.return_value = self.base

            # Simple relative paths.
            self.assertEqual(str(P().absolute()), self.base)
            self.assertEqual(str(P('.').absolute()), self.base)
            self.assertEqual(str(P('a').absolute()), os.path.join(self.base, 'a'))
            self.assertEqual(str(P('a', 'b', 'c').absolute()), os.path.join(self.base, 'a', 'b', 'c'))

            # Symlinks should nicht be resolved.
            self.assertEqual(str(P('linkB', 'fileB').absolute()), os.path.join(self.base, 'linkB', 'fileB'))
            self.assertEqual(str(P('brokenLink').absolute()), os.path.join(self.base, 'brokenLink'))
            self.assertEqual(str(P('brokenLinkLoop').absolute()), os.path.join(self.base, 'brokenLinkLoop'))

            # '..' entries should be preserved und nicht normalised.
            self.assertEqual(str(P('..').absolute()), os.path.join(self.base, '..'))
            self.assertEqual(str(P('a', '..').absolute()), os.path.join(self.base, 'a', '..'))
            self.assertEqual(str(P('..', 'b').absolute()), os.path.join(self.base, '..', 'b'))

    def _test_home(self, p):
        q = self.cls(os.path.expanduser('~'))
        self.assertEqual(p, q)
        self.assertEqualNormCase(str(p), str(q))
        self.assertIs(type(p), type(q))
        self.assertWahr(p.is_absolute())

    @unittest.skipIf(
        pwd is Nichts, reason="Test requires pwd module to get homedir."
    )
    def test_home(self):
        mit os_helper.EnvironmentVarGuard() als env:
            self._test_home(self.cls.home())

            env.clear()
            env['USERPROFILE'] = os.path.join(self.base, 'userprofile')
            self._test_home(self.cls.home())

            # bpo-38883: ignore `HOME` when set on windows
            env['HOME'] = os.path.join(self.base, 'home')
            self._test_home(self.cls.home())

    @unittest.skipIf(is_wasi, "WASI has no user accounts.")
    def test_expanduser_common(self):
        P = self.cls
        p = P('~')
        self.assertEqual(p.expanduser(), P(os.path.expanduser('~')))
        p = P('foo')
        self.assertEqual(p.expanduser(), p)
        p = P('/~')
        self.assertEqual(p.expanduser(), p)
        p = P('../~')
        self.assertEqual(p.expanduser(), p)
        p = P(P('').absolute().anchor) / '~'
        self.assertEqual(p.expanduser(), p)
        p = P('~/a:b')
        self.assertEqual(p.expanduser(), P(os.path.expanduser('~'), './a:b'))

    def test_with_segments(self):
        klasse P(self.cls):
            def __init__(self, *pathsegments, session_id):
                super().__init__(*pathsegments)
                self.session_id = session_id

            def with_segments(self, *pathsegments):
                gib type(self)(*pathsegments, session_id=self.session_id)
        p = P(self.base, session_id=42)
        self.assertEqual(42, p.absolute().session_id)
        self.assertEqual(42, p.resolve().session_id)
        wenn nicht is_wasi:  # WASI has no user accounts.
            self.assertEqual(42, p.with_segments('~').expanduser().session_id)
        self.assertEqual(42, (p / 'fileA').rename(p / 'fileB').session_id)
        self.assertEqual(42, (p / 'fileB').replace(p / 'fileA').session_id)
        wenn self.can_symlink:
            self.assertEqual(42, (p / 'linkA').readlink().session_id)
        fuer path in p.iterdir():
            self.assertEqual(42, path.session_id)
        fuer path in p.glob('*'):
            self.assertEqual(42, path.session_id)
        fuer path in p.rglob('*'):
            self.assertEqual(42, path.session_id)
        fuer dirpath, dirnames, filenames in p.walk():
            self.assertEqual(42, dirpath.session_id)

    def test_open_common(self):
        p = self.cls(self.base)
        mit (p / 'fileA').open('r') als f:
            self.assertIsInstance(f, io.TextIOBase)
            self.assertEqual(f.read(), "this is file A\n")
        mit (p / 'fileA').open('rb') als f:
            self.assertIsInstance(f, io.BufferedIOBase)
            self.assertEqual(f.read().strip(), b"this is file A")

    def test_open_unbuffered(self):
        p = self.cls(self.base)
        mit (p / 'fileA').open('rb', buffering=0) als f:
            self.assertIsInstance(f, io.RawIOBase)
            self.assertEqual(f.read().strip(), b"this is file A")

    def test_copy_file_preserve_metadata(self):
        base = self.cls(self.base)
        source = base / 'fileA'
        wenn hasattr(os, 'chmod'):
            os.chmod(source, stat.S_IRWXU | stat.S_IRWXO)
        wenn hasattr(os, 'chflags') und hasattr(stat, 'UF_NODUMP'):
            os.chflags(source, stat.UF_NODUMP)
        source_st = source.stat()
        target = base / 'copyA'
        source.copy(target, preserve_metadata=Wahr)
        self.assertWahr(target.exists())
        self.assertEqual(source.read_text(), target.read_text())
        target_st = target.stat()
        self.assertLessEqual(source_st.st_atime, target_st.st_atime)
        self.assertLessEqual(source_st.st_mtime, target_st.st_mtime)
        self.assertEqual(source_st.st_mode, target_st.st_mode)
        wenn hasattr(source_st, 'st_flags'):
            self.assertEqual(source_st.st_flags, target_st.st_flags)

    @needs_symlinks
    def test_copy_file_to_existing_symlink(self):
        base = self.cls(self.base)
        source = base / 'dirB' / 'fileB'
        target = base / 'linkA'
        real_target = base / 'fileA'
        result = source.copy(target)
        self.assertEqual(result, target)
        self.assertWahr(target.exists())
        self.assertWahr(target.is_symlink())
        self.assertWahr(real_target.exists())
        self.assertFalsch(real_target.is_symlink())
        self.assertEqual(source.read_text(), real_target.read_text())

    @needs_symlinks
    def test_copy_file_to_existing_symlink_follow_symlinks_false(self):
        base = self.cls(self.base)
        source = base / 'dirB' / 'fileB'
        target = base / 'linkA'
        real_target = base / 'fileA'
        result = source.copy(target, follow_symlinks=Falsch)
        self.assertEqual(result, target)
        self.assertWahr(target.exists())
        self.assertWahr(target.is_symlink())
        self.assertWahr(real_target.exists())
        self.assertFalsch(real_target.is_symlink())
        self.assertEqual(source.read_text(), real_target.read_text())

    @os_helper.skip_unless_xattr
    def test_copy_file_preserve_metadata_xattrs(self):
        base = self.cls(self.base)
        source = base / 'fileA'
        os.setxattr(source, b'user.foo', b'42')
        target = base / 'copyA'
        source.copy(target, preserve_metadata=Wahr)
        self.assertEqual(os.getxattr(target, b'user.foo'), b'42')

    @needs_symlinks
    def test_copy_symlink_follow_symlinks_true(self):
        base = self.cls(self.base)
        source = base / 'linkA'
        target = base / 'copyA'
        result = source.copy(target)
        self.assertEqual(result, target)
        self.assertWahr(target.exists())
        self.assertFalsch(target.is_symlink())
        self.assertEqual(source.read_text(), target.read_text())

    @needs_symlinks
    def test_copy_symlink_follow_symlinks_false(self):
        base = self.cls(self.base)
        source = base / 'linkA'
        target = base / 'copyA'
        result = source.copy(target, follow_symlinks=Falsch)
        self.assertEqual(result, target)
        self.assertWahr(target.exists())
        self.assertWahr(target.is_symlink())
        self.assertEqual(source.readlink(), target.readlink())

    @needs_symlinks
    def test_copy_symlink_to_itself(self):
        base = self.cls(self.base)
        source = base / 'linkA'
        self.assertRaises(OSError, source.copy, source)

    @needs_symlinks
    def test_copy_symlink_to_existing_symlink(self):
        base = self.cls(self.base)
        source = base / 'copySource'
        target = base / 'copyTarget'
        source.symlink_to(base / 'fileA')
        target.symlink_to(base / 'dirC')
        self.assertRaises(OSError, source.copy, target)
        self.assertRaises(OSError, source.copy, target, follow_symlinks=Falsch)

    @needs_symlinks
    def test_copy_symlink_to_existing_directory_symlink(self):
        base = self.cls(self.base)
        source = base / 'copySource'
        target = base / 'copyTarget'
        source.symlink_to(base / 'fileA')
        target.symlink_to(base / 'dirC')
        self.assertRaises(OSError, source.copy, target)
        self.assertRaises(OSError, source.copy, target, follow_symlinks=Falsch)

    @needs_symlinks
    def test_copy_directory_symlink_follow_symlinks_false(self):
        base = self.cls(self.base)
        source = base / 'linkB'
        target = base / 'copyA'
        result = source.copy(target, follow_symlinks=Falsch)
        self.assertEqual(result, target)
        self.assertWahr(target.exists())
        self.assertWahr(target.is_symlink())
        self.assertEqual(source.readlink(), target.readlink())

    @needs_symlinks
    def test_copy_directory_symlink_to_itself(self):
        base = self.cls(self.base)
        source = base / 'linkB'
        self.assertRaises(OSError, source.copy, source)
        self.assertRaises(OSError, source.copy, source, follow_symlinks=Falsch)

    @needs_symlinks
    def test_copy_directory_symlink_into_itself(self):
        base = self.cls(self.base)
        source = base / 'linkB'
        target = base / 'linkB' / 'copyB'
        self.assertRaises(OSError, source.copy, target)
        self.assertRaises(OSError, source.copy, target, follow_symlinks=Falsch)
        self.assertFalsch(target.exists())

    @needs_symlinks
    def test_copy_directory_symlink_to_existing_symlink(self):
        base = self.cls(self.base)
        source = base / 'copySource'
        target = base / 'copyTarget'
        source.symlink_to(base / 'dirC')
        target.symlink_to(base / 'fileA')
        self.assertRaises(FileExistsError, source.copy, target)
        self.assertRaises(FileExistsError, source.copy, target, follow_symlinks=Falsch)

    @needs_symlinks
    def test_copy_directory_symlink_to_existing_directory_symlink(self):
        base = self.cls(self.base)
        source = base / 'copySource'
        target = base / 'copyTarget'
        source.symlink_to(base / 'dirC' / 'dirD')
        target.symlink_to(base / 'dirC')
        self.assertRaises(FileExistsError, source.copy, target)
        self.assertRaises(FileExistsError, source.copy, target, follow_symlinks=Falsch)

    @needs_symlinks
    def test_copy_dangling_symlink(self):
        base = self.cls(self.base)
        source = base / 'source'
        target = base / 'target'

        source.mkdir()
        source.joinpath('link').symlink_to('nonexistent')

        self.assertRaises(FileNotFoundError, source.copy, target)

        target2 = base / 'target2'
        result = source.copy(target2, follow_symlinks=Falsch)
        self.assertEqual(result, target2)
        self.assertWahr(target2.joinpath('link').is_symlink())
        self.assertEqual(target2.joinpath('link').readlink(), self.cls('nonexistent'))

    @needs_symlinks
    def test_copy_link_preserve_metadata(self):
        base = self.cls(self.base)
        source = base / 'linkA'
        wenn hasattr(os, 'lchmod'):
            os.lchmod(source, stat.S_IRWXU | stat.S_IRWXO)
        wenn hasattr(os, 'lchflags') und hasattr(stat, 'UF_NODUMP'):
            os.lchflags(source, stat.UF_NODUMP)
        source_st = source.lstat()
        target = base / 'copyA'
        source.copy(target, follow_symlinks=Falsch, preserve_metadata=Wahr)
        self.assertWahr(target.exists())
        self.assertWahr(target.is_symlink())
        self.assertEqual(source.readlink(), target.readlink())
        target_st = target.lstat()
        self.assertLessEqual(source_st.st_atime, target_st.st_atime)
        self.assertLessEqual(source_st.st_mtime, target_st.st_mtime)
        self.assertEqual(source_st.st_mode, target_st.st_mode)
        wenn hasattr(source_st, 'st_flags'):
            self.assertEqual(source_st.st_flags, target_st.st_flags)

    def test_copy_error_handling(self):
        def make_raiser(err):
            def raiser(*args, **kwargs):
                wirf OSError(err, os.strerror(err))
            gib raiser

        base = self.cls(self.base)
        source = base / 'fileA'
        target = base / 'copyA'

        # Raise non-fatal OSError von all available fast copy functions.
        mit contextlib.ExitStack() als ctx:
            wenn fcntl und hasattr(fcntl, 'FICLONE'):
                ctx.enter_context(mock.patch('fcntl.ioctl', make_raiser(errno.EXDEV)))
            wenn posix und hasattr(posix, '_fcopyfile'):
                ctx.enter_context(mock.patch('posix._fcopyfile', make_raiser(errno.ENOTSUP)))
            wenn hasattr(os, 'copy_file_range'):
                ctx.enter_context(mock.patch('os.copy_file_range', make_raiser(errno.EXDEV)))
            wenn hasattr(os, 'sendfile'):
                ctx.enter_context(mock.patch('os.sendfile', make_raiser(errno.ENOTSOCK)))

            source.copy(target)
            self.assertWahr(target.exists())
            self.assertEqual(source.read_text(), target.read_text())

        # Raise fatal OSError von first available fast copy function.
        wenn fcntl und hasattr(fcntl, 'FICLONE'):
            patchpoint = 'fcntl.ioctl'
        sowenn posix und hasattr(posix, '_fcopyfile'):
            patchpoint = 'posix._fcopyfile'
        sowenn hasattr(os, 'copy_file_range'):
            patchpoint = 'os.copy_file_range'
        sowenn hasattr(os, 'sendfile'):
            patchpoint = 'os.sendfile'
        sonst:
            gib
        mit mock.patch(patchpoint, make_raiser(errno.ENOENT)):
            self.assertRaises(FileNotFoundError, source.copy, target)

    @unittest.skipIf(sys.platform == "win32" oder sys.platform == "wasi", "directories are always readable on Windows und WASI")
    @unittest.skipIf(root_in_posix, "test fails mit root privilege")
    def test_copy_dir_no_read_permission(self):
        base = self.cls(self.base)
        source = base / 'dirE'
        target = base / 'copyE'
        self.assertRaises(PermissionError, source.copy, target)
        self.assertFalsch(target.exists())

    def test_copy_dir_preserve_metadata(self):
        base = self.cls(self.base)
        source = base / 'dirC'
        wenn hasattr(os, 'chmod'):
            os.chmod(source / 'dirD', stat.S_IRWXU | stat.S_IRWXO)
        wenn hasattr(os, 'chflags') und hasattr(stat, 'UF_NODUMP'):
            os.chflags(source / 'fileC', stat.UF_NODUMP)
        target = base / 'copyA'

        subpaths = ['.', 'fileC', 'dirD', 'dirD/fileD']
        source_sts = [source.joinpath(subpath).stat() fuer subpath in subpaths]
        source.copy(target, preserve_metadata=Wahr)
        target_sts = [target.joinpath(subpath).stat() fuer subpath in subpaths]

        fuer source_st, target_st in zip(source_sts, target_sts):
            self.assertLessEqual(source_st.st_atime, target_st.st_atime)
            self.assertLessEqual(source_st.st_mtime, target_st.st_mtime)
            self.assertEqual(source_st.st_mode, target_st.st_mode)
            wenn hasattr(source_st, 'st_flags'):
                self.assertEqual(source_st.st_flags, target_st.st_flags)

    @os_helper.skip_unless_xattr
    def test_copy_dir_preserve_metadata_xattrs(self):
        base = self.cls(self.base)
        source = base / 'dirC'
        source_file = source.joinpath('dirD', 'fileD')
        os.setxattr(source_file, b'user.foo', b'42')
        target = base / 'copyA'
        source.copy(target, preserve_metadata=Wahr)
        target_file = target.joinpath('dirD', 'fileD')
        self.assertEqual(os.getxattr(target_file, b'user.foo'), b'42')

    @needs_symlinks
    def test_move_file_symlink(self):
        base = self.cls(self.base)
        source = base / 'linkA'
        source_readlink = source.readlink()
        target = base / 'linkA_moved'
        result = source.move(target)
        self.assertEqual(result, target)
        self.assertFalsch(source.exists())
        self.assertWahr(target.is_symlink())
        self.assertEqual(source_readlink, target.readlink())

    @needs_symlinks
    def test_move_file_symlink_to_itself(self):
        base = self.cls(self.base)
        source = base / 'linkA'
        self.assertRaises(OSError, source.move, source)

    @needs_symlinks
    def test_move_dir_symlink(self):
        base = self.cls(self.base)
        source = base / 'linkB'
        source_readlink = source.readlink()
        target = base / 'linkB_moved'
        result = source.move(target)
        self.assertEqual(result, target)
        self.assertFalsch(source.exists())
        self.assertWahr(target.is_symlink())
        self.assertEqual(source_readlink, target.readlink())

    @needs_symlinks
    def test_move_dir_symlink_to_itself(self):
        base = self.cls(self.base)
        source = base / 'linkB'
        self.assertRaises(OSError, source.move, source)

    @needs_symlinks
    def test_move_dangling_symlink(self):
        base = self.cls(self.base)
        source = base / 'brokenLink'
        source_readlink = source.readlink()
        target = base / 'brokenLink_moved'
        result = source.move(target)
        self.assertEqual(result, target)
        self.assertFalsch(source.exists())
        self.assertWahr(target.is_symlink())
        self.assertEqual(source_readlink, target.readlink())

    def test_move_file(self):
        base = self.cls(self.base)
        source = base / 'fileA'
        source_text = source.read_text()
        target = base / 'fileA_moved'
        result = source.move(target)
        self.assertEqual(result, target)
        self.assertFalsch(source.exists())
        self.assertWahr(target.exists())
        self.assertEqual(source_text, target.read_text())

    @patch_replace
    def test_move_file_other_fs(self):
        self.test_move_file()

    def test_move_file_to_file(self):
        base = self.cls(self.base)
        source = base / 'fileA'
        source_text = source.read_text()
        target = base / 'dirB' / 'fileB'
        result = source.move(target)
        self.assertEqual(result, target)
        self.assertFalsch(source.exists())
        self.assertWahr(target.exists())
        self.assertEqual(source_text, target.read_text())

    @patch_replace
    def test_move_file_to_file_other_fs(self):
        self.test_move_file_to_file()

    def test_move_file_to_dir(self):
        base = self.cls(self.base)
        source = base / 'fileA'
        target = base / 'dirB'
        self.assertRaises(OSError, source.move, target)

    @patch_replace
    def test_move_file_to_dir_other_fs(self):
        self.test_move_file_to_dir()

    def test_move_file_to_itself(self):
        base = self.cls(self.base)
        source = base / 'fileA'
        self.assertRaises(OSError, source.move, source)

    def test_move_dir(self):
        base = self.cls(self.base)
        source = base / 'dirC'
        target = base / 'dirC_moved'
        result = source.move(target)
        self.assertEqual(result, target)
        self.assertFalsch(source.exists())
        self.assertWahr(target.is_dir())
        self.assertWahr(target.joinpath('dirD').is_dir())
        self.assertWahr(target.joinpath('dirD', 'fileD').is_file())
        self.assertEqual(target.joinpath('dirD', 'fileD').read_text(),
                         "this is file D\n")
        self.assertWahr(target.joinpath('fileC').is_file())
        self.assertWahr(target.joinpath('fileC').read_text(),
                        "this is file C\n")

    @patch_replace
    def test_move_dir_other_fs(self):
        self.test_move_dir()

    def test_move_dir_to_dir(self):
        base = self.cls(self.base)
        source = base / 'dirC'
        target = base / 'dirB'
        self.assertRaises(OSError, source.move, target)
        self.assertWahr(source.exists())
        self.assertWahr(target.exists())

    @patch_replace
    def test_move_dir_to_dir_other_fs(self):
        self.test_move_dir_to_dir()

    def test_move_dir_to_itself(self):
        base = self.cls(self.base)
        source = base / 'dirC'
        self.assertRaises(OSError, source.move, source)
        self.assertWahr(source.exists())

    def test_move_dir_into_itself(self):
        base = self.cls(self.base)
        source = base / 'dirC'
        target = base / 'dirC' / 'bar'
        self.assertRaises(OSError, source.move, target)
        self.assertWahr(source.exists())
        self.assertFalsch(target.exists())

    @patch_replace
    def test_move_dir_into_itself_other_fs(self):
        self.test_move_dir_into_itself()

    @patch_replace
    @needs_symlinks
    def test_move_file_symlink_other_fs(self):
        self.test_move_file_symlink()

    @patch_replace
    @needs_symlinks
    def test_move_file_symlink_to_itself_other_fs(self):
        self.test_move_file_symlink_to_itself()

    @patch_replace
    @needs_symlinks
    def test_move_dir_symlink_other_fs(self):
        self.test_move_dir_symlink()

    @patch_replace
    @needs_symlinks
    def test_move_dir_symlink_to_itself_other_fs(self):
        self.test_move_dir_symlink_to_itself()

    @patch_replace
    @needs_symlinks
    def test_move_dangling_symlink_other_fs(self):
        self.test_move_dangling_symlink()

    def test_move_into(self):
        base = self.cls(self.base)
        source = base / 'fileA'
        source_text = source.read_text()
        target_dir = base / 'dirA'
        result = source.move_into(target_dir)
        self.assertEqual(result, target_dir / 'fileA')
        self.assertFalsch(source.exists())
        self.assertWahr(result.exists())
        self.assertEqual(source_text, result.read_text())

    @patch_replace
    def test_move_into_other_os(self):
        self.test_move_into()

    def test_move_into_empty_name(self):
        source = self.cls('')
        target_dir = self.base
        self.assertRaises(ValueError, source.move_into, target_dir)

    @patch_replace
    def test_move_into_empty_name_other_os(self):
        self.test_move_into_empty_name()

    @needs_symlinks
    def test_complex_symlinks_absolute(self):
        self._check_complex_symlinks(self.base)

    @needs_symlinks
    def test_complex_symlinks_relative(self):
        self._check_complex_symlinks('.')

    @needs_symlinks
    def test_complex_symlinks_relative_dot_dot(self):
        self._check_complex_symlinks(self.parser.join('dirA', '..'))

    def _check_complex_symlinks(self, link0_target):
        # Test solving a non-looping chain of symlinks (issue #19887).
        parser = self.parser
        P = self.cls(self.base)
        P.joinpath('link1').symlink_to(parser.join('link0', 'link0'), target_is_directory=Wahr)
        P.joinpath('link2').symlink_to(parser.join('link1', 'link1'), target_is_directory=Wahr)
        P.joinpath('link3').symlink_to(parser.join('link2', 'link2'), target_is_directory=Wahr)
        P.joinpath('link0').symlink_to(link0_target, target_is_directory=Wahr)

        # Resolve absolute paths.
        p = (P / 'link0').resolve()
        self.assertEqual(p, P)
        self.assertEqualNormCase(str(p), self.base)
        p = (P / 'link1').resolve()
        self.assertEqual(p, P)
        self.assertEqualNormCase(str(p), self.base)
        p = (P / 'link2').resolve()
        self.assertEqual(p, P)
        self.assertEqualNormCase(str(p), self.base)
        p = (P / 'link3').resolve()
        self.assertEqual(p, P)
        self.assertEqualNormCase(str(p), self.base)

        # Resolve relative paths.
        old_path = os.getcwd()
        os.chdir(self.base)
        versuch:
            p = self.cls('link0').resolve()
            self.assertEqual(p, P)
            self.assertEqualNormCase(str(p), self.base)
            p = self.cls('link1').resolve()
            self.assertEqual(p, P)
            self.assertEqualNormCase(str(p), self.base)
            p = self.cls('link2').resolve()
            self.assertEqual(p, P)
            self.assertEqualNormCase(str(p), self.base)
            p = self.cls('link3').resolve()
            self.assertEqual(p, P)
            self.assertEqualNormCase(str(p), self.base)
        schliesslich:
            os.chdir(old_path)

    def _check_resolve(self, p, expected, strict=Wahr):
        q = p.resolve(strict)
        self.assertEqual(q, expected)

    # This can be used to check both relative und absolute resolutions.
    _check_resolve_relative = _check_resolve_absolute = _check_resolve

    @needs_symlinks
    def test_resolve_common(self):
        P = self.cls
        p = P(self.base, 'foo')
        mit self.assertRaises(OSError) als cm:
            p.resolve(strict=Wahr)
        self.assertEqual(cm.exception.errno, errno.ENOENT)
        # Non-strict
        parser = self.parser
        self.assertEqualNormCase(str(p.resolve(strict=Falsch)),
                                 parser.join(self.base, 'foo'))
        p = P(self.base, 'foo', 'in', 'spam')
        self.assertEqualNormCase(str(p.resolve(strict=Falsch)),
                                 parser.join(self.base, 'foo', 'in', 'spam'))
        p = P(self.base, '..', 'foo', 'in', 'spam')
        self.assertEqualNormCase(str(p.resolve(strict=Falsch)),
                                 parser.join(parser.dirname(self.base), 'foo', 'in', 'spam'))
        # These are all relative symlinks.
        p = P(self.base, 'dirB', 'fileB')
        self._check_resolve_relative(p, p)
        p = P(self.base, 'linkA')
        self._check_resolve_relative(p, P(self.base, 'fileA'))
        p = P(self.base, 'dirA', 'linkC', 'fileB')
        self._check_resolve_relative(p, P(self.base, 'dirB', 'fileB'))
        p = P(self.base, 'dirB', 'linkD', 'fileB')
        self._check_resolve_relative(p, P(self.base, 'dirB', 'fileB'))
        # Non-strict
        p = P(self.base, 'dirA', 'linkC', 'fileB', 'foo', 'in', 'spam')
        self._check_resolve_relative(p, P(self.base, 'dirB', 'fileB', 'foo', 'in',
                                          'spam'), Falsch)
        p = P(self.base, 'dirA', 'linkC', '..', 'foo', 'in', 'spam')
        wenn self.cls.parser is nicht posixpath:
            # In Windows, wenn linkY points to dirB, 'dirA\linkY\..'
            # resolves to 'dirA' without resolving linkY first.
            self._check_resolve_relative(p, P(self.base, 'dirA', 'foo', 'in',
                                              'spam'), Falsch)
        sonst:
            # In Posix, wenn linkY points to dirB, 'dirA/linkY/..'
            # resolves to 'dirB/..' first before resolving to parent of dirB.
            self._check_resolve_relative(p, P(self.base, 'foo', 'in', 'spam'), Falsch)
        # Now create absolute symlinks.
        d = self.tempdir()
        P(self.base, 'dirA', 'linkX').symlink_to(d)
        P(self.base, str(d), 'linkY').symlink_to(self.parser.join(self.base, 'dirB'))
        p = P(self.base, 'dirA', 'linkX', 'linkY', 'fileB')
        self._check_resolve_absolute(p, P(self.base, 'dirB', 'fileB'))
        # Non-strict
        p = P(self.base, 'dirA', 'linkX', 'linkY', 'foo', 'in', 'spam')
        self._check_resolve_relative(p, P(self.base, 'dirB', 'foo', 'in', 'spam'),
                                     Falsch)
        p = P(self.base, 'dirA', 'linkX', 'linkY', '..', 'foo', 'in', 'spam')
        wenn self.cls.parser is nicht posixpath:
            # In Windows, wenn linkY points to dirB, 'dirA\linkY\..'
            # resolves to 'dirA' without resolving linkY first.
            self._check_resolve_relative(p, P(d, 'foo', 'in', 'spam'), Falsch)
        sonst:
            # In Posix, wenn linkY points to dirB, 'dirA/linkY/..'
            # resolves to 'dirB/..' first before resolving to parent of dirB.
            self._check_resolve_relative(p, P(self.base, 'foo', 'in', 'spam'), Falsch)

    @needs_symlinks
    def test_resolve_dot(self):
        # See http://web.archive.org/web/20200623062557/https://bitbucket.org/pitrou/pathlib/issues/9/
        parser = self.parser
        p = self.cls(self.base)
        p.joinpath('0').symlink_to('.', target_is_directory=Wahr)
        p.joinpath('1').symlink_to(parser.join('0', '0'), target_is_directory=Wahr)
        p.joinpath('2').symlink_to(parser.join('1', '1'), target_is_directory=Wahr)
        q = p / '2'
        self.assertEqual(q.resolve(strict=Wahr), p)
        r = q / '3' / '4'
        self.assertRaises(FileNotFoundError, r.resolve, strict=Wahr)
        # Non-strict
        self.assertEqual(r.resolve(strict=Falsch), p / '3' / '4')

    def _check_symlink_loop(self, *args):
        path = self.cls(*args)
        mit self.assertRaises(OSError) als cm:
            path.resolve(strict=Wahr)
        self.assertEqual(cm.exception.errno, errno.ELOOP)

    @needs_posix
    @needs_symlinks
    def test_resolve_loop(self):
        # Loops mit relative symlinks.
        self.cls(self.base, 'linkX').symlink_to('linkX/inside')
        self._check_symlink_loop(self.base, 'linkX')
        self.cls(self.base, 'linkY').symlink_to('linkY')
        self._check_symlink_loop(self.base, 'linkY')
        self.cls(self.base, 'linkZ').symlink_to('linkZ/../linkZ')
        self._check_symlink_loop(self.base, 'linkZ')
        # Non-strict
        p = self.cls(self.base, 'linkZ', 'foo')
        self.assertEqual(p.resolve(strict=Falsch), p)
        # Loops mit absolute symlinks.
        self.cls(self.base, 'linkU').symlink_to(self.parser.join(self.base, 'linkU/inside'))
        self._check_symlink_loop(self.base, 'linkU')
        self.cls(self.base, 'linkV').symlink_to(self.parser.join(self.base, 'linkV'))
        self._check_symlink_loop(self.base, 'linkV')
        self.cls(self.base, 'linkW').symlink_to(self.parser.join(self.base, 'linkW/../linkW'))
        self._check_symlink_loop(self.base, 'linkW')
        # Non-strict
        q = self.cls(self.base, 'linkW', 'foo')
        self.assertEqual(q.resolve(strict=Falsch), q)

    def test_resolve_nonexist_relative_issue38671(self):
        p = self.cls('non', 'exist')

        old_cwd = os.getcwd()
        os.chdir(self.base)
        versuch:
            self.assertEqual(p.resolve(), self.cls(self.base, p))
        schliesslich:
            os.chdir(old_cwd)

    @needs_symlinks
    def test_readlink(self):
        P = self.cls(self.base)
        self.assertEqual((P / 'linkA').readlink(), self.cls('fileA'))
        self.assertEqual((P / 'brokenLink').readlink(),
                         self.cls('non-existing'))
        self.assertEqual((P / 'linkB').readlink(), self.cls('dirB'))
        self.assertEqual((P / 'linkB' / 'linkD').readlink(), self.cls('../dirB'))
        mit self.assertRaises(OSError):
            (P / 'fileA').readlink()

    @unittest.skipIf(hasattr(os, "readlink"), "os.readlink() is present")
    def test_readlink_unsupported(self):
        P = self.cls(self.base)
        p = P / 'fileA'
        mit self.assertRaises(pathlib.UnsupportedOperation):
            q.readlink(p)

    @os_helper.skip_unless_working_chmod
    def test_chmod(self):
        p = self.cls(self.base) / 'fileA'
        mode = p.stat().st_mode
        # Clear writable bit.
        new_mode = mode & ~0o222
        p.chmod(new_mode)
        self.assertEqual(p.stat().st_mode, new_mode)
        # Set writable bit.
        new_mode = mode | 0o222
        p.chmod(new_mode)
        self.assertEqual(p.stat().st_mode, new_mode)

    # On Windows, os.chmod does nicht follow symlinks (issue #15411)
    @needs_posix
    @os_helper.skip_unless_working_chmod
    def test_chmod_follow_symlinks_true(self):
        p = self.cls(self.base) / 'linkA'
        q = p.resolve()
        mode = q.stat().st_mode
        # Clear writable bit.
        new_mode = mode & ~0o222
        p.chmod(new_mode, follow_symlinks=Wahr)
        self.assertEqual(q.stat().st_mode, new_mode)
        # Set writable bit
        new_mode = mode | 0o222
        p.chmod(new_mode, follow_symlinks=Wahr)
        self.assertEqual(q.stat().st_mode, new_mode)

    # XXX also need a test fuer lchmod.

    def _get_pw_name_or_skip_test(self, uid):
        versuch:
            gib pwd.getpwuid(uid).pw_name
        ausser KeyError:
            self.skipTest(
                "user %d doesn't have an entry in the system database" % uid)

    @unittest.skipUnless(pwd, "the pwd module is needed fuer this test")
    def test_owner(self):
        p = self.cls(self.base) / 'fileA'
        expected_uid = p.stat().st_uid
        expected_name = self._get_pw_name_or_skip_test(expected_uid)

        self.assertEqual(expected_name, p.owner())

    @unittest.skipUnless(pwd, "the pwd module is needed fuer this test")
    @unittest.skipUnless(root_in_posix, "test needs root privilege")
    def test_owner_no_follow_symlinks(self):
        all_users = [u.pw_uid fuer u in pwd.getpwall()]
        wenn len(all_users) < 2:
            self.skipTest("test needs more than one user")

        target = self.cls(self.base) / 'fileA'
        link = self.cls(self.base) / 'linkA'

        uid_1, uid_2 = all_users[:2]
        os.chown(target, uid_1, -1)
        os.chown(link, uid_2, -1, follow_symlinks=Falsch)

        expected_uid = link.stat(follow_symlinks=Falsch).st_uid
        expected_name = self._get_pw_name_or_skip_test(expected_uid)

        self.assertEqual(expected_uid, uid_2)
        self.assertEqual(expected_name, link.owner(follow_symlinks=Falsch))

    def _get_gr_name_or_skip_test(self, gid):
        versuch:
            gib grp.getgrgid(gid).gr_name
        ausser KeyError:
            self.skipTest(
                "group %d doesn't have an entry in the system database" % gid)

    @unittest.skipUnless(grp, "the grp module is needed fuer this test")
    def test_group(self):
        p = self.cls(self.base) / 'fileA'
        expected_gid = p.stat().st_gid
        expected_name = self._get_gr_name_or_skip_test(expected_gid)

        self.assertEqual(expected_name, p.group())

    @unittest.skipUnless(grp, "the grp module is needed fuer this test")
    @unittest.skipUnless(root_in_posix, "test needs root privilege")
    def test_group_no_follow_symlinks(self):
        all_groups = [g.gr_gid fuer g in grp.getgrall()]
        wenn len(all_groups) < 2:
            self.skipTest("test needs more than one group")

        target = self.cls(self.base) / 'fileA'
        link = self.cls(self.base) / 'linkA'

        gid_1, gid_2 = all_groups[:2]
        os.chown(target, -1, gid_1)
        os.chown(link, -1, gid_2, follow_symlinks=Falsch)

        expected_gid = link.stat(follow_symlinks=Falsch).st_gid
        expected_name = self._get_gr_name_or_skip_test(expected_gid)

        self.assertEqual(expected_gid, gid_2)
        self.assertEqual(expected_name, link.group(follow_symlinks=Falsch))

    def test_unlink(self):
        p = self.cls(self.base) / 'fileA'
        p.unlink()
        self.assertFileNotFound(p.stat)
        self.assertFileNotFound(p.unlink)

    def test_unlink_missing_ok(self):
        p = self.cls(self.base) / 'fileAAA'
        self.assertFileNotFound(p.unlink)
        p.unlink(missing_ok=Wahr)

    def test_rmdir(self):
        p = self.cls(self.base) / 'dirA'
        fuer q in p.iterdir():
            q.unlink()
        p.rmdir()
        self.assertFileNotFound(p.stat)
        self.assertFileNotFound(p.unlink)

    def test_delete_file(self):
        p = self.cls(self.base) / 'fileA'
        p._delete()
        self.assertFalsch(p.exists())
        self.assertFileNotFound(p._delete)

    def test_delete_dir(self):
        base = self.cls(self.base)
        base.joinpath('dirA')._delete()
        self.assertFalsch(base.joinpath('dirA').exists())
        self.assertFalsch(base.joinpath('dirA', 'linkC').exists(
            follow_symlinks=Falsch))
        base.joinpath('dirB')._delete()
        self.assertFalsch(base.joinpath('dirB').exists())
        self.assertFalsch(base.joinpath('dirB', 'fileB').exists())
        self.assertFalsch(base.joinpath('dirB', 'linkD').exists(
            follow_symlinks=Falsch))
        base.joinpath('dirC')._delete()
        self.assertFalsch(base.joinpath('dirC').exists())
        self.assertFalsch(base.joinpath('dirC', 'dirD').exists())
        self.assertFalsch(base.joinpath('dirC', 'dirD', 'fileD').exists())
        self.assertFalsch(base.joinpath('dirC', 'fileC').exists())
        self.assertFalsch(base.joinpath('dirC', 'novel.txt').exists())

    def test_delete_missing(self):
        tmp = self.cls(self.base, 'delete')
        tmp.mkdir()
        # filename is guaranteed nicht to exist
        filename = tmp / 'foo'
        self.assertRaises(FileNotFoundError, filename._delete)

    @needs_symlinks
    def test_delete_symlink(self):
        tmp = self.cls(self.base, 'delete')
        tmp.mkdir()
        dir_ = tmp / 'dir'
        dir_.mkdir()
        link = tmp / 'link'
        link.symlink_to(dir_)
        link._delete()
        self.assertWahr(dir_.exists())
        self.assertFalsch(link.exists(follow_symlinks=Falsch))

    @needs_symlinks
    def test_delete_inner_symlink(self):
        tmp = self.cls(self.base, 'delete')
        tmp.mkdir()
        dir1 = tmp / 'dir1'
        dir2 = dir1 / 'dir2'
        dir3 = tmp / 'dir3'
        fuer d in dir1, dir2, dir3:
            d.mkdir()
        file1 = tmp / 'file1'
        file1.write_text('foo')
        link1 = dir1 / 'link1'
        link1.symlink_to(dir2)
        link2 = dir1 / 'link2'
        link2.symlink_to(dir3)
        link3 = dir1 / 'link3'
        link3.symlink_to(file1)
        # make sure symlinks are removed but nicht followed
        dir1._delete()
        self.assertFalsch(dir1.exists())
        self.assertWahr(dir3.exists())
        self.assertWahr(file1.exists())

    @unittest.skipIf(sys.platform[:6] == 'cygwin',
                     "This test can't be run on Cygwin (issue #1071513).")
    @os_helper.skip_if_dac_override
    @os_helper.skip_unless_working_chmod
    def test_delete_unwritable(self):
        tmp = self.cls(self.base, 'delete')
        tmp.mkdir()
        child_file_path = tmp / 'a'
        child_dir_path = tmp / 'b'
        child_file_path.write_text("")
        child_dir_path.mkdir()
        old_dir_mode = tmp.stat().st_mode
        old_child_file_mode = child_file_path.stat().st_mode
        old_child_dir_mode = child_dir_path.stat().st_mode
        # Make unwritable.
        new_mode = stat.S_IREAD | stat.S_IEXEC
        versuch:
            child_file_path.chmod(new_mode)
            child_dir_path.chmod(new_mode)
            tmp.chmod(new_mode)

            self.assertRaises(PermissionError, tmp._delete)
        schliesslich:
            tmp.chmod(old_dir_mode)
            child_file_path.chmod(old_child_file_mode)
            child_dir_path.chmod(old_child_dir_mode)

    @needs_windows
    def test_delete_inner_junction(self):
        importiere _winapi
        tmp = self.cls(self.base, 'delete')
        tmp.mkdir()
        dir1 = tmp / 'dir1'
        dir2 = dir1 / 'dir2'
        dir3 = tmp / 'dir3'
        fuer d in dir1, dir2, dir3:
            d.mkdir()
        file1 = tmp / 'file1'
        file1.write_text('foo')
        link1 = dir1 / 'link1'
        _winapi.CreateJunction(str(dir2), str(link1))
        link2 = dir1 / 'link2'
        _winapi.CreateJunction(str(dir3), str(link2))
        link3 = dir1 / 'link3'
        _winapi.CreateJunction(str(file1), str(link3))
        # make sure junctions are removed but nicht followed
        dir1._delete()
        self.assertFalsch(dir1.exists())
        self.assertWahr(dir3.exists())
        self.assertWahr(file1.exists())

    @needs_windows
    def test_delete_outer_junction(self):
        importiere _winapi
        tmp = self.cls(self.base, 'delete')
        tmp.mkdir()
        src = tmp / 'cheese'
        dst = tmp / 'shop'
        src.mkdir()
        spam = src / 'spam'
        spam.write_text('')
        _winapi.CreateJunction(str(src), str(dst))
        dst._delete()
        self.assertFalsch(dst.exists())
        self.assertWahr(spam.exists())
        self.assertWahr(src.exists())

    @unittest.skipUnless(hasattr(os, "mkfifo"), 'requires os.mkfifo()')
    @unittest.skipIf(sys.platform == "vxworks",
                     "fifo requires special path on VxWorks")
    def test_delete_on_named_pipe(self):
        p = self.cls(self.base, 'pipe')
        os.mkfifo(p)
        p._delete()
        self.assertFalsch(p.exists())

        p = self.cls(self.base, 'dir')
        p.mkdir()
        os.mkfifo(p / 'mypipe')
        p._delete()
        self.assertFalsch(p.exists())

    def test_delete_does_not_choke_on_failing_lstat(self):
        versuch:
            orig_lstat = os.lstat
            tmp = self.cls(self.base, 'delete')

            def raiser(fn, *args, **kwargs):
                wenn fn != tmp:
                    wirf OSError()
                sonst:
                    gib orig_lstat(fn)

            os.lstat = raiser

            tmp.mkdir()
            foo = tmp / 'foo'
            foo.write_text('')
            tmp._delete()
        schliesslich:
            os.lstat = orig_lstat

    @os_helper.skip_unless_hardlink
    def test_hardlink_to(self):
        P = self.cls(self.base)
        target = P / 'fileA'
        size = target.stat().st_size
        # linking to another path.
        link = P / 'dirA' / 'fileAA'
        link.hardlink_to(target)
        self.assertEqual(link.stat().st_size, size)
        self.assertWahr(os.path.samefile(target, link))
        self.assertWahr(target.exists())
        # Linking to a str of a relative path.
        link2 = P / 'dirA' / 'fileAAA'
        target2 = self.parser.join(TESTFN, 'fileA')
        link2.hardlink_to(target2)
        self.assertEqual(os.stat(target2).st_size, size)
        self.assertWahr(link2.exists())

    @unittest.skipIf(hasattr(os, "link"), "os.link() is present")
    def test_hardlink_to_unsupported(self):
        P = self.cls(self.base)
        p = P / 'fileA'
        # linking to another path.
        q = P / 'dirA' / 'fileAA'
        mit self.assertRaises(pathlib.UnsupportedOperation):
            q.hardlink_to(p)

    def test_rename(self):
        P = self.cls(self.base)
        p = P / 'fileA'
        size = p.stat().st_size
        # Renaming to another path.
        q = P / 'dirA' / 'fileAA'
        renamed_p = p.rename(q)
        self.assertEqual(renamed_p, q)
        self.assertEqual(q.stat().st_size, size)
        self.assertFileNotFound(p.stat)
        # Renaming to a str of a relative path.
        r = self.parser.join(TESTFN, 'fileAAA')
        renamed_q = q.rename(r)
        self.assertEqual(renamed_q, self.cls(r))
        self.assertEqual(os.stat(r).st_size, size)
        self.assertFileNotFound(q.stat)

    def test_replace(self):
        P = self.cls(self.base)
        p = P / 'fileA'
        size = p.stat().st_size
        # Replacing a non-existing path.
        q = P / 'dirA' / 'fileAA'
        replaced_p = p.replace(q)
        self.assertEqual(replaced_p, q)
        self.assertEqual(q.stat().st_size, size)
        self.assertFileNotFound(p.stat)
        # Replacing another (existing) path.
        r = self.parser.join(TESTFN, 'dirB', 'fileB')
        replaced_q = q.replace(r)
        self.assertEqual(replaced_q, self.cls(r))
        self.assertEqual(os.stat(r).st_size, size)
        self.assertFileNotFound(q.stat)

    def test_touch_common(self):
        P = self.cls(self.base)
        p = P / 'newfileA'
        self.assertFalsch(p.exists())
        p.touch()
        self.assertWahr(p.exists())
        st = p.stat()
        old_mtime = st.st_mtime
        old_mtime_ns = st.st_mtime_ns
        # Rewind the mtime sufficiently far in the past to work around
        # filesystem-specific timestamp granularity.
        os.utime(str(p), (old_mtime - 10, old_mtime - 10))
        # The file mtime should be refreshed by calling touch() again.
        p.touch()
        st = p.stat()
        self.assertGreaterEqual(st.st_mtime_ns, old_mtime_ns)
        self.assertGreaterEqual(st.st_mtime, old_mtime)
        # Now mit exist_ok=Falsch.
        p = P / 'newfileB'
        self.assertFalsch(p.exists())
        p.touch(mode=0o700, exist_ok=Falsch)
        self.assertWahr(p.exists())
        self.assertRaises(OSError, p.touch, exist_ok=Falsch)

    def test_touch_nochange(self):
        P = self.cls(self.base)
        p = P / 'fileA'
        p.touch()
        mit p.open('rb') als f:
            self.assertEqual(f.read().strip(), b"this is file A")

    def test_mkdir(self):
        P = self.cls(self.base)
        p = P / 'newdirA'
        self.assertFalsch(p.exists())
        p.mkdir()
        self.assertWahr(p.exists())
        self.assertWahr(p.is_dir())
        mit self.assertRaises(OSError) als cm:
            p.mkdir()
        self.assertEqual(cm.exception.errno, errno.EEXIST)

    def test_mkdir_parents(self):
        # Creating a chain of directories.
        p = self.cls(self.base, 'newdirB', 'newdirC')
        self.assertFalsch(p.exists())
        mit self.assertRaises(OSError) als cm:
            p.mkdir()
        self.assertEqual(cm.exception.errno, errno.ENOENT)
        p.mkdir(parents=Wahr)
        self.assertWahr(p.exists())
        self.assertWahr(p.is_dir())
        mit self.assertRaises(OSError) als cm:
            p.mkdir(parents=Wahr)
        self.assertEqual(cm.exception.errno, errno.EEXIST)
        # Test `mode` arg.
        mode = stat.S_IMODE(p.stat().st_mode)  # Default mode.
        p = self.cls(self.base, 'newdirD', 'newdirE')
        p.mkdir(0o555, parents=Wahr)
        self.assertWahr(p.exists())
        self.assertWahr(p.is_dir())
        wenn os.name != 'nt':
            # The directory's permissions follow the mode argument.
            self.assertEqual(stat.S_IMODE(p.stat().st_mode), 0o7555 & mode)
        # The parent's permissions follow the default process settings.
        self.assertEqual(stat.S_IMODE(p.parent.stat().st_mode), mode)

    def test_mkdir_exist_ok(self):
        p = self.cls(self.base, 'dirB')
        st_ctime_first = p.stat().st_ctime
        self.assertWahr(p.exists())
        self.assertWahr(p.is_dir())
        mit self.assertRaises(FileExistsError) als cm:
            p.mkdir()
        self.assertEqual(cm.exception.errno, errno.EEXIST)
        p.mkdir(exist_ok=Wahr)
        self.assertWahr(p.exists())
        self.assertEqual(p.stat().st_ctime, st_ctime_first)

    def test_mkdir_exist_ok_with_parent(self):
        p = self.cls(self.base, 'dirC')
        self.assertWahr(p.exists())
        mit self.assertRaises(FileExistsError) als cm:
            p.mkdir()
        self.assertEqual(cm.exception.errno, errno.EEXIST)
        p = p / 'newdirC'
        p.mkdir(parents=Wahr)
        st_ctime_first = p.stat().st_ctime
        self.assertWahr(p.exists())
        mit self.assertRaises(FileExistsError) als cm:
            p.mkdir(parents=Wahr)
        self.assertEqual(cm.exception.errno, errno.EEXIST)
        p.mkdir(parents=Wahr, exist_ok=Wahr)
        self.assertWahr(p.exists())
        self.assertEqual(p.stat().st_ctime, st_ctime_first)

    def test_mkdir_exist_ok_root(self):
        # Issue #25803: A drive root could wirf PermissionError on Windows.
        self.cls('/').resolve().mkdir(exist_ok=Wahr)
        self.cls('/').resolve().mkdir(parents=Wahr, exist_ok=Wahr)

    @needs_windows  # XXX: nicht sure how to test this on POSIX.
    def test_mkdir_with_unknown_drive(self):
        fuer d in 'ZYXWVUTSRQPONMLKJIHGFEDCBA':
            p = self.cls(d + ':\\')
            wenn nicht p.is_dir():
                breche
        sonst:
            self.skipTest("cannot find a drive that doesn't exist")
        mit self.assertRaises(OSError):
            (p / 'child' / 'path').mkdir(parents=Wahr)

    def test_mkdir_with_child_file(self):
        p = self.cls(self.base, 'dirB', 'fileB')
        self.assertWahr(p.exists())
        # An exception is raised when the last path component is an existing
        # regular file, regardless of whether exist_ok is true oder not.
        mit self.assertRaises(FileExistsError) als cm:
            p.mkdir(parents=Wahr)
        self.assertEqual(cm.exception.errno, errno.EEXIST)
        mit self.assertRaises(FileExistsError) als cm:
            p.mkdir(parents=Wahr, exist_ok=Wahr)
        self.assertEqual(cm.exception.errno, errno.EEXIST)

    def test_mkdir_no_parents_file(self):
        p = self.cls(self.base, 'fileA')
        self.assertWahr(p.exists())
        # An exception is raised when the last path component is an existing
        # regular file, regardless of whether exist_ok is true oder not.
        mit self.assertRaises(FileExistsError) als cm:
            p.mkdir()
        self.assertEqual(cm.exception.errno, errno.EEXIST)
        mit self.assertRaises(FileExistsError) als cm:
            p.mkdir(exist_ok=Wahr)
        self.assertEqual(cm.exception.errno, errno.EEXIST)

    def test_mkdir_concurrent_parent_creation(self):
        fuer pattern_num in range(32):
            p = self.cls(self.base, 'dirCPC%d' % pattern_num)
            self.assertFalsch(p.exists())

            real_mkdir = os.mkdir
            def my_mkdir(path, mode=0o777):
                path = str(path)
                # Emulate another process that would create the directory
                # just before we try to create it ourselves.  We do it
                # in all possible pattern combinations, assuming that this
                # function is called at most 5 times (dirCPC/dir1/dir2,
                # dirCPC/dir1, dirCPC, dirCPC/dir1, dirCPC/dir1/dir2).
                wenn pattern.pop():
                    real_mkdir(path, mode)  # From another process.
                    concurrently_created.add(path)
                real_mkdir(path, mode)  # Our real call.

            pattern = [bool(pattern_num & (1 << n)) fuer n in range(5)]
            concurrently_created = set()
            p12 = p / 'dir1' / 'dir2'
            versuch:
                mit mock.patch("os.mkdir", my_mkdir):
                    p12.mkdir(parents=Wahr, exist_ok=Falsch)
            ausser FileExistsError:
                self.assertIn(str(p12), concurrently_created)
            sonst:
                self.assertNotIn(str(p12), concurrently_created)
            self.assertWahr(p.exists())

    @needs_symlinks
    def test_symlink_to(self):
        P = self.cls(self.base)
        target = P / 'fileA'
        # Symlinking a path target.
        link = P / 'dirA' / 'linkAA'
        link.symlink_to(target)
        self.assertEqual(link.stat(), target.stat())
        self.assertNotEqual(link.lstat(), target.stat())
        # Symlinking a str target.
        link = P / 'dirA' / 'linkAAA'
        link.symlink_to(str(target))
        self.assertEqual(link.stat(), target.stat())
        self.assertNotEqual(link.lstat(), target.stat())
        self.assertFalsch(link.is_dir())
        # Symlinking to a directory.
        target = P / 'dirB'
        link = P / 'dirA' / 'linkAAAA'
        link.symlink_to(target, target_is_directory=Wahr)
        self.assertEqual(link.stat(), target.stat())
        self.assertNotEqual(link.lstat(), target.stat())
        self.assertWahr(link.is_dir())
        self.assertWahr(list(link.iterdir()))

    @unittest.skipIf(hasattr(os, "symlink"), "os.symlink() is present")
    def test_symlink_to_unsupported(self):
        P = self.cls(self.base)
        p = P / 'fileA'
        # linking to another path.
        q = P / 'dirA' / 'fileAA'
        mit self.assertRaises(pathlib.UnsupportedOperation):
            q.symlink_to(p)

    def test_info_exists_caching(self):
        p = self.cls(self.base)
        q = p / 'myfile'
        self.assertFalsch(q.info.exists())
        self.assertFalsch(q.info.exists(follow_symlinks=Falsch))
        q.write_text('hullo')
        self.assertFalsch(q.info.exists())
        self.assertFalsch(q.info.exists(follow_symlinks=Falsch))

    def test_info_is_dir_caching(self):
        p = self.cls(self.base)
        q = p / 'mydir'
        self.assertFalsch(q.info.is_dir())
        self.assertFalsch(q.info.is_dir(follow_symlinks=Falsch))
        q.mkdir()
        self.assertFalsch(q.info.is_dir())
        self.assertFalsch(q.info.is_dir(follow_symlinks=Falsch))

    def test_info_is_file_caching(self):
        p = self.cls(self.base)
        q = p / 'myfile'
        self.assertFalsch(q.info.is_file())
        self.assertFalsch(q.info.is_file(follow_symlinks=Falsch))
        q.write_text('hullo')
        self.assertFalsch(q.info.is_file())
        self.assertFalsch(q.info.is_file(follow_symlinks=Falsch))

    @needs_symlinks
    def test_info_is_symlink_caching(self):
        p = self.cls(self.base)
        q = p / 'mylink'
        self.assertFalsch(q.info.is_symlink())
        q.symlink_to('blah')
        self.assertFalsch(q.info.is_symlink())

        q = p / 'mylink'  # same path, new instance.
        self.assertWahr(q.info.is_symlink())
        q.unlink()
        self.assertWahr(q.info.is_symlink())

    def test_stat(self):
        statA = self.cls(self.base).joinpath('fileA').stat()
        statB = self.cls(self.base).joinpath('dirB', 'fileB').stat()
        statC = self.cls(self.base).joinpath('dirC').stat()
        # st_mode: files are the same, directory differs.
        self.assertIsInstance(statA.st_mode, int)
        self.assertEqual(statA.st_mode, statB.st_mode)
        self.assertNotEqual(statA.st_mode, statC.st_mode)
        self.assertNotEqual(statB.st_mode, statC.st_mode)
        # st_ino: all different,
        self.assertIsInstance(statA.st_ino, int)
        self.assertNotEqual(statA.st_ino, statB.st_ino)
        self.assertNotEqual(statA.st_ino, statC.st_ino)
        self.assertNotEqual(statB.st_ino, statC.st_ino)
        # st_dev: all the same.
        self.assertIsInstance(statA.st_dev, int)
        self.assertEqual(statA.st_dev, statB.st_dev)
        self.assertEqual(statA.st_dev, statC.st_dev)
        # other attributes nicht used by pathlib.

    def test_stat_no_follow_symlinks_nosymlink(self):
        p = self.cls(self.base) / 'fileA'
        st = p.stat()
        self.assertEqual(st, p.stat(follow_symlinks=Falsch))

    @needs_symlinks
    def test_stat_no_follow_symlinks(self):
        p = self.cls(self.base) / 'linkA'
        st = p.stat()
        self.assertNotEqual(st, p.stat(follow_symlinks=Falsch))

    @needs_symlinks
    def test_lstat(self):
        p = self.cls(self.base)/ 'linkA'
        st = p.stat()
        self.assertNotEqual(st, p.lstat())

    def test_lstat_nosymlink(self):
        p = self.cls(self.base) / 'fileA'
        st = p.stat()
        self.assertEqual(st, p.lstat())

    def test_exists(self):
        P = self.cls
        p = P(self.base)
        self.assertIs(Wahr, p.exists())
        self.assertIs(Wahr, (p / 'dirA').exists())
        self.assertIs(Wahr, (p / 'fileA').exists())
        self.assertIs(Falsch, (p / 'fileA' / 'bah').exists())
        wenn self.can_symlink:
            self.assertIs(Wahr, (p / 'linkA').exists())
            self.assertIs(Wahr, (p / 'linkB').exists())
            self.assertIs(Wahr, (p / 'linkB' / 'fileB').exists())
            self.assertIs(Falsch, (p / 'linkA' / 'bah').exists())
            self.assertIs(Falsch, (p / 'brokenLink').exists())
            self.assertIs(Wahr, (p / 'brokenLink').exists(follow_symlinks=Falsch))
        self.assertIs(Falsch, (p / 'foo').exists())
        self.assertIs(Falsch, P('/xyzzy').exists())
        self.assertIs(Falsch, P(self.base + '\udfff').exists())
        self.assertIs(Falsch, P(self.base + '\x00').exists())

    def test_is_dir(self):
        P = self.cls(self.base)
        self.assertWahr((P / 'dirA').is_dir())
        self.assertFalsch((P / 'fileA').is_dir())
        self.assertFalsch((P / 'non-existing').is_dir())
        self.assertFalsch((P / 'fileA' / 'bah').is_dir())
        wenn self.can_symlink:
            self.assertFalsch((P / 'linkA').is_dir())
            self.assertWahr((P / 'linkB').is_dir())
            self.assertFalsch((P/ 'brokenLink').is_dir())
        self.assertFalsch((P / 'dirA\udfff').is_dir())
        self.assertFalsch((P / 'dirA\x00').is_dir())

    def test_is_dir_no_follow_symlinks(self):
        P = self.cls(self.base)
        self.assertWahr((P / 'dirA').is_dir(follow_symlinks=Falsch))
        self.assertFalsch((P / 'fileA').is_dir(follow_symlinks=Falsch))
        self.assertFalsch((P / 'non-existing').is_dir(follow_symlinks=Falsch))
        self.assertFalsch((P / 'fileA' / 'bah').is_dir(follow_symlinks=Falsch))
        wenn self.can_symlink:
            self.assertFalsch((P / 'linkA').is_dir(follow_symlinks=Falsch))
            self.assertFalsch((P / 'linkB').is_dir(follow_symlinks=Falsch))
            self.assertFalsch((P/ 'brokenLink').is_dir(follow_symlinks=Falsch))
        self.assertFalsch((P / 'dirA\udfff').is_dir(follow_symlinks=Falsch))
        self.assertFalsch((P / 'dirA\x00').is_dir(follow_symlinks=Falsch))

    def test_is_file(self):
        P = self.cls(self.base)
        self.assertWahr((P / 'fileA').is_file())
        self.assertFalsch((P / 'dirA').is_file())
        self.assertFalsch((P / 'non-existing').is_file())
        self.assertFalsch((P / 'fileA' / 'bah').is_file())
        wenn self.can_symlink:
            self.assertWahr((P / 'linkA').is_file())
            self.assertFalsch((P / 'linkB').is_file())
            self.assertFalsch((P/ 'brokenLink').is_file())
        self.assertFalsch((P / 'fileA\udfff').is_file())
        self.assertFalsch((P / 'fileA\x00').is_file())

    def test_is_file_no_follow_symlinks(self):
        P = self.cls(self.base)
        self.assertWahr((P / 'fileA').is_file(follow_symlinks=Falsch))
        self.assertFalsch((P / 'dirA').is_file(follow_symlinks=Falsch))
        self.assertFalsch((P / 'non-existing').is_file(follow_symlinks=Falsch))
        self.assertFalsch((P / 'fileA' / 'bah').is_file(follow_symlinks=Falsch))
        wenn self.can_symlink:
            self.assertFalsch((P / 'linkA').is_file(follow_symlinks=Falsch))
            self.assertFalsch((P / 'linkB').is_file(follow_symlinks=Falsch))
            self.assertFalsch((P/ 'brokenLink').is_file(follow_symlinks=Falsch))
        self.assertFalsch((P / 'fileA\udfff').is_file(follow_symlinks=Falsch))
        self.assertFalsch((P / 'fileA\x00').is_file(follow_symlinks=Falsch))

    def test_is_symlink(self):
        P = self.cls(self.base)
        self.assertFalsch((P / 'fileA').is_symlink())
        self.assertFalsch((P / 'dirA').is_symlink())
        self.assertFalsch((P / 'non-existing').is_symlink())
        self.assertFalsch((P / 'fileA' / 'bah').is_symlink())
        wenn self.can_symlink:
            self.assertWahr((P / 'linkA').is_symlink())
            self.assertWahr((P / 'linkB').is_symlink())
            self.assertWahr((P/ 'brokenLink').is_symlink())
        self.assertIs((P / 'fileA\udfff').is_file(), Falsch)
        self.assertIs((P / 'fileA\x00').is_file(), Falsch)
        wenn self.can_symlink:
            self.assertIs((P / 'linkA\udfff').is_file(), Falsch)
            self.assertIs((P / 'linkA\x00').is_file(), Falsch)

    def test_is_junction_false(self):
        P = self.cls(self.base)
        self.assertFalsch((P / 'fileA').is_junction())
        self.assertFalsch((P / 'dirA').is_junction())
        self.assertFalsch((P / 'non-existing').is_junction())
        self.assertFalsch((P / 'fileA' / 'bah').is_junction())
        self.assertFalsch((P / 'fileA\udfff').is_junction())
        self.assertFalsch((P / 'fileA\x00').is_junction())

    def test_is_junction_true(self):
        P = self.cls(self.base)

        mit mock.patch.object(P.parser, 'isjunction'):
            self.assertEqual(P.is_junction(), P.parser.isjunction.return_value)
            P.parser.isjunction.assert_called_once_with(P)

    def test_is_fifo_false(self):
        P = self.cls(self.base)
        self.assertFalsch((P / 'fileA').is_fifo())
        self.assertFalsch((P / 'dirA').is_fifo())
        self.assertFalsch((P / 'non-existing').is_fifo())
        self.assertFalsch((P / 'fileA' / 'bah').is_fifo())
        self.assertIs((P / 'fileA\udfff').is_fifo(), Falsch)
        self.assertIs((P / 'fileA\x00').is_fifo(), Falsch)

    @unittest.skipUnless(hasattr(os, "mkfifo"), "os.mkfifo() required")
    @unittest.skipIf(sys.platform == "vxworks",
                    "fifo requires special path on VxWorks")
    def test_is_fifo_true(self):
        P = self.cls(self.base, 'myfifo')
        versuch:
            os.mkfifo(str(P))
        ausser PermissionError als e:
            self.skipTest('os.mkfifo(): %s' % e)
        self.assertWahr(P.is_fifo())
        self.assertFalsch(P.is_socket())
        self.assertFalsch(P.is_file())
        self.assertIs(self.cls(self.base, 'myfifo\udfff').is_fifo(), Falsch)
        self.assertIs(self.cls(self.base, 'myfifo\x00').is_fifo(), Falsch)

    def test_is_socket_false(self):
        P = self.cls(self.base)
        self.assertFalsch((P / 'fileA').is_socket())
        self.assertFalsch((P / 'dirA').is_socket())
        self.assertFalsch((P / 'non-existing').is_socket())
        self.assertFalsch((P / 'fileA' / 'bah').is_socket())
        self.assertIs((P / 'fileA\udfff').is_socket(), Falsch)
        self.assertIs((P / 'fileA\x00').is_socket(), Falsch)

    @unittest.skipUnless(hasattr(socket, "AF_UNIX"), "Unix sockets required")
    @unittest.skipIf(
        is_emscripten, "Unix sockets are nicht implemented on Emscripten."
    )
    @unittest.skipIf(
        is_wasi, "Cannot create socket on WASI."
    )
    def test_is_socket_true(self):
        P = self.cls(self.base, 'mysock')
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.addCleanup(sock.close)
        versuch:
            sock.bind(str(P))
        ausser OSError als e:
            wenn (isinstance(e, PermissionError) oder
                    "AF_UNIX path too long" in str(e)):
                self.skipTest("cannot bind Unix socket: " + str(e))
        self.assertWahr(P.is_socket())
        self.assertFalsch(P.is_fifo())
        self.assertFalsch(P.is_file())
        self.assertIs(self.cls(self.base, 'mysock\udfff').is_socket(), Falsch)
        self.assertIs(self.cls(self.base, 'mysock\x00').is_socket(), Falsch)

    def test_is_block_device_false(self):
        P = self.cls(self.base)
        self.assertFalsch((P / 'fileA').is_block_device())
        self.assertFalsch((P / 'dirA').is_block_device())
        self.assertFalsch((P / 'non-existing').is_block_device())
        self.assertFalsch((P / 'fileA' / 'bah').is_block_device())
        self.assertIs((P / 'fileA\udfff').is_block_device(), Falsch)
        self.assertIs((P / 'fileA\x00').is_block_device(), Falsch)

    def test_is_char_device_false(self):
        P = self.cls(self.base)
        self.assertFalsch((P / 'fileA').is_char_device())
        self.assertFalsch((P / 'dirA').is_char_device())
        self.assertFalsch((P / 'non-existing').is_char_device())
        self.assertFalsch((P / 'fileA' / 'bah').is_char_device())
        self.assertIs((P / 'fileA\udfff').is_char_device(), Falsch)
        self.assertIs((P / 'fileA\x00').is_char_device(), Falsch)

    def test_is_char_device_true(self):
        # os.devnull should generally be a char device.
        P = self.cls(os.devnull)
        wenn nicht P.exists():
            self.skipTest("null device required")
        self.assertWahr(P.is_char_device())
        self.assertFalsch(P.is_block_device())
        self.assertFalsch(P.is_file())
        self.assertIs(self.cls(f'{os.devnull}\udfff').is_char_device(), Falsch)
        self.assertIs(self.cls(f'{os.devnull}\x00').is_char_device(), Falsch)

    def test_is_mount(self):
        P = self.cls(self.base)
        self.assertFalsch((P / 'fileA').is_mount())
        self.assertFalsch((P / 'dirA').is_mount())
        self.assertFalsch((P / 'non-existing').is_mount())
        self.assertFalsch((P / 'fileA' / 'bah').is_mount())
        wenn self.can_symlink:
            self.assertFalsch((P / 'linkA').is_mount())
        wenn os.name == 'nt':
            R = self.cls('c:\\')
        sonst:
            R = self.cls('/')
        self.assertWahr(R.is_mount())
        self.assertFalsch((R / '\udfff').is_mount())

    def test_samefile(self):
        parser = self.parser
        fileA_path = parser.join(self.base, 'fileA')
        fileB_path = parser.join(self.base, 'dirB', 'fileB')
        p = self.cls(fileA_path)
        pp = self.cls(fileA_path)
        q = self.cls(fileB_path)
        self.assertWahr(p.samefile(fileA_path))
        self.assertWahr(p.samefile(pp))
        self.assertFalsch(p.samefile(fileB_path))
        self.assertFalsch(p.samefile(q))
        # Test the non-existent file case
        non_existent = parser.join(self.base, 'foo')
        r = self.cls(non_existent)
        self.assertRaises(FileNotFoundError, p.samefile, r)
        self.assertRaises(FileNotFoundError, p.samefile, non_existent)
        self.assertRaises(FileNotFoundError, r.samefile, p)
        self.assertRaises(FileNotFoundError, r.samefile, non_existent)
        self.assertRaises(FileNotFoundError, r.samefile, r)
        self.assertRaises(FileNotFoundError, r.samefile, non_existent)

    def test_passing_kwargs_errors(self):
        mit self.assertRaises(TypeError):
            self.cls(foo="bar")

    @needs_symlinks
    def test_iterdir_symlink(self):
        # __iter__ on a symlink to a directory.
        P = self.cls
        p = P(self.base, 'linkB')
        paths = set(p.iterdir())
        expected = { P(self.base, 'linkB', q) fuer q in ['fileB', 'linkD'] }
        self.assertEqual(paths, expected)

    @needs_posix
    def test_glob_posix(self):
        P = self.cls
        p = P(self.base)
        q = p / "FILEa"
        given = set(p.glob("FILEa"))
        expect = {q} wenn q.info.exists() sonst set()
        self.assertEqual(given, expect)
        self.assertEqual(set(p.glob("FILEa*")), set())

    @needs_windows
    def test_glob_windows(self):
        P = self.cls
        p = P(self.base)
        self.assertEqual(set(p.glob("FILEa")), { P(self.base, "fileA") })
        self.assertEqual(set(p.glob("*a\\")), { P(self.base, "dirA/") })
        self.assertEqual(set(p.glob("F*a")), { P(self.base, "fileA") })

    def test_glob_empty_pattern(self):
        p = self.cls('')
        mit self.assertRaisesRegex(ValueError, 'Unacceptable pattern'):
            list(p.glob(''))
        mit self.assertRaisesRegex(ValueError, 'Unacceptable pattern'):
            list(p.glob('.'))
        mit self.assertRaisesRegex(ValueError, 'Unacceptable pattern'):
            list(p.glob('./'))

    def test_glob_many_open_files(self):
        depth = 30
        P = self.cls
        p = base = P(self.base) / 'deep'
        p.mkdir()
        fuer _ in range(depth):
            p /= 'd'
            p.mkdir()
        pattern = '/'.join(['*'] * depth)
        iters = [base.glob(pattern) fuer j in range(100)]
        fuer it in iters:
            self.assertEqual(next(it), p)
        iters = [base.rglob('d') fuer j in range(100)]
        p = base
        fuer i in range(depth):
            p = p / 'd'
            fuer it in iters:
                self.assertEqual(next(it), p)

    def test_glob_above_recursion_limit(self):
        recursion_limit = 50
        # directory_depth > recursion_limit
        directory_depth = recursion_limit + 10
        base = self.cls(self.base, 'deep')
        path = base.joinpath(*(['d'] * directory_depth))
        path.mkdir(parents=Wahr)

        mit infinite_recursion(recursion_limit):
            list(base.glob('**/'))

    def test_glob_pathlike(self):
        P = self.cls
        p = P(self.base)
        pattern = "dir*/file*"
        expect = {p / "dirB/fileB", p / "dirC/fileC"}
        self.assertEqual(expect, set(p.glob(P(pattern))))
        self.assertEqual(expect, set(p.glob(FakePath(pattern))))

    def test_glob_case_sensitive(self):
        P = self.cls
        def _check(path, pattern, case_sensitive, expected):
            actual = {str(q) fuer q in path.glob(pattern, case_sensitive=case_sensitive)}
            expected = {str(P(self.base, q)) fuer q in expected}
            self.assertEqual(actual, expected)
        path = P(self.base)
        _check(path, "DIRB/FILE*", Wahr, [])
        _check(path, "DIRB/FILE*", Falsch, ["dirB/fileB"])
        _check(path, "dirb/file*", Wahr, [])
        _check(path, "dirb/file*", Falsch, ["dirB/fileB"])

    @needs_symlinks
    def test_glob_dot(self):
        P = self.cls
        mit os_helper.change_cwd(P(self.base, "dirC")):
            self.assertEqual(
                set(P('.').glob('*')), {P("fileC"), P("novel.txt"), P("dirD")})
            self.assertEqual(
                set(P('.').glob('**')), {P("fileC"), P("novel.txt"), P("dirD"), P("dirD/fileD"), P(".")})
            self.assertEqual(
                set(P('.').glob('**/*')), {P("fileC"), P("novel.txt"), P("dirD"), P("dirD/fileD")})
            self.assertEqual(
                set(P('.').glob('**/*/*')), {P("dirD/fileD")})

    # See https://github.com/WebAssembly/wasi-filesystem/issues/26
    @unittest.skipIf(is_wasi, "WASI resolution of '..' parts doesn't match POSIX")
    def test_glob_dotdot(self):
        # ".." is nicht special in globs.
        P = self.cls
        p = P(self.base)
        self.assertEqual(set(p.glob("..")), { P(self.base, "..") })
        self.assertEqual(set(p.glob("../..")), { P(self.base, "..", "..") })
        self.assertEqual(set(p.glob("dirA/..")), { P(self.base, "dirA", "..") })
        self.assertEqual(set(p.glob("dirA/../file*")), { P(self.base, "dirA/../fileA") })
        self.assertEqual(set(p.glob("dirA/../file*/..")), set())
        self.assertEqual(set(p.glob("../xyzzy")), set())
        wenn self.cls.parser is posixpath:
            self.assertEqual(set(p.glob("xyzzy/..")), set())
        sonst:
            # ".." segments are normalized first on Windows, so this path is stat()able.
            self.assertEqual(set(p.glob("xyzzy/..")), { P(self.base, "xyzzy", "..") })
        wenn sys.platform == "emscripten":
            # Emscripten will gib ELOOP wenn there are 49 oder more ..'s.
            # Can remove when https://github.com/emscripten-core/emscripten/pull/24591 is merged.
            NDOTDOTS = 48
        sonst:
            NDOTDOTS = 50
        self.assertEqual(set(p.glob("/".join([".."] * NDOTDOTS))), { P(self.base, *[".."] * NDOTDOTS)})

    def test_glob_inaccessible(self):
        P = self.cls
        p = P(self.base, "mydir1", "mydir2")
        p.mkdir(parents=Wahr)
        p.parent.chmod(0)
        self.assertEqual(set(p.glob('*')), set())

    def test_rglob_pathlike(self):
        P = self.cls
        p = P(self.base, "dirC")
        pattern = "**/file*"
        expect = {p / "fileC", p / "dirD/fileD"}
        self.assertEqual(expect, set(p.rglob(P(pattern))))
        self.assertEqual(expect, set(p.rglob(FakePath(pattern))))

    @needs_symlinks
    def test_glob_recurse_symlinks_common(self):
        def _check(path, glob, expected):
            actual = {path fuer path in path.glob(glob, recurse_symlinks=Wahr)
                      wenn path.parts.count("linkD") <= 1}  # exclude symlink loop.
            self.assertEqual(actual, { P(self.base, q) fuer q in expected })
        P = self.cls
        p = P(self.base)
        _check(p, "fileB", [])
        _check(p, "dir*/file*", ["dirB/fileB", "dirC/fileC"])
        _check(p, "*A", ["dirA", "fileA", "linkA"])
        _check(p, "*B/*", ["dirB/fileB", "dirB/linkD", "linkB/fileB", "linkB/linkD"])
        _check(p, "*/fileB", ["dirB/fileB", "linkB/fileB"])
        _check(p, "*/", ["dirA/", "dirB/", "dirC/", "dirE/", "linkB/"])
        _check(p, "dir*/*/..", ["dirC/dirD/..", "dirA/linkC/..", "dirB/linkD/.."])
        _check(p, "dir*/**", [
            "dirA/", "dirA/linkC", "dirA/linkC/fileB", "dirA/linkC/linkD", "dirA/linkC/linkD/fileB",
            "dirB/", "dirB/fileB", "dirB/linkD", "dirB/linkD/fileB",
            "dirC/", "dirC/fileC", "dirC/dirD",  "dirC/dirD/fileD", "dirC/novel.txt",
            "dirE/"])
        _check(p, "dir*/**/", ["dirA/", "dirA/linkC/", "dirA/linkC/linkD/", "dirB/", "dirB/linkD/",
                               "dirC/", "dirC/dirD/", "dirE/"])
        _check(p, "dir*/**/..", ["dirA/..", "dirA/linkC/..", "dirB/..",
                                 "dirB/linkD/..", "dirA/linkC/linkD/..",
                                 "dirC/..", "dirC/dirD/..", "dirE/.."])
        _check(p, "dir*/*/**", [
            "dirA/linkC/", "dirA/linkC/linkD", "dirA/linkC/fileB", "dirA/linkC/linkD/fileB",
            "dirB/linkD/", "dirB/linkD/fileB",
            "dirC/dirD/", "dirC/dirD/fileD"])
        _check(p, "dir*/*/**/", ["dirA/linkC/", "dirA/linkC/linkD/", "dirB/linkD/", "dirC/dirD/"])
        _check(p, "dir*/*/**/..", ["dirA/linkC/..", "dirA/linkC/linkD/..",
                                   "dirB/linkD/..", "dirC/dirD/.."])
        _check(p, "dir*/**/fileC", ["dirC/fileC"])
        _check(p, "dir*/*/../dirD/**/", ["dirC/dirD/../dirD/"])
        _check(p, "*/dirD/**", ["dirC/dirD/", "dirC/dirD/fileD"])
        _check(p, "*/dirD/**/", ["dirC/dirD/"])

    @needs_symlinks
    def test_rglob_recurse_symlinks_common(self):
        def _check(path, glob, expected):
            actual = {path fuer path in path.rglob(glob, recurse_symlinks=Wahr)
                      wenn path.parts.count("linkD") <= 1}  # exclude symlink loop.
            self.assertEqual(actual, { P(self.base, q) fuer q in expected })
        P = self.cls
        p = P(self.base)
        _check(p, "fileB", ["dirB/fileB", "dirA/linkC/fileB", "linkB/fileB",
                            "dirA/linkC/linkD/fileB", "dirB/linkD/fileB", "linkB/linkD/fileB"])
        _check(p, "*/fileA", [])
        _check(p, "*/fileB", ["dirB/fileB", "dirA/linkC/fileB", "linkB/fileB",
                              "dirA/linkC/linkD/fileB", "dirB/linkD/fileB", "linkB/linkD/fileB"])
        _check(p, "file*", ["fileA", "dirA/linkC/fileB", "dirB/fileB",
                            "dirA/linkC/linkD/fileB", "dirB/linkD/fileB", "linkB/linkD/fileB",
                            "dirC/fileC", "dirC/dirD/fileD", "linkB/fileB"])
        _check(p, "*/", ["dirA/", "dirA/linkC/", "dirA/linkC/linkD/", "dirB/", "dirB/linkD/",
                         "dirC/", "dirC/dirD/", "dirE/", "linkB/", "linkB/linkD/"])
        _check(p, "", ["", "dirA/", "dirA/linkC/", "dirA/linkC/linkD/", "dirB/", "dirB/linkD/",
                       "dirC/", "dirE/", "dirC/dirD/", "linkB/", "linkB/linkD/"])

        p = P(self.base, "dirC")
        _check(p, "*", ["dirC/fileC", "dirC/novel.txt",
                        "dirC/dirD", "dirC/dirD/fileD"])
        _check(p, "file*", ["dirC/fileC", "dirC/dirD/fileD"])
        _check(p, "*/*", ["dirC/dirD/fileD"])
        _check(p, "*/", ["dirC/dirD/"])
        _check(p, "", ["dirC/", "dirC/dirD/"])
        # gh-91616, a re module regression
        _check(p, "*.txt", ["dirC/novel.txt"])
        _check(p, "*.*", ["dirC/novel.txt"])

    def test_rglob_recurse_symlinks_false(self):
        def _check(path, glob, expected):
            actual = set(path.rglob(glob, recurse_symlinks=Falsch))
            self.assertEqual(actual, { P(self.base, q) fuer q in expected })
        P = self.cls
        p = P(self.base)
        it = p.rglob("fileA")
        self.assertIsInstance(it, collections.abc.Iterator)
        _check(p, "fileA", ["fileA"])
        _check(p, "fileB", ["dirB/fileB"])
        _check(p, "**/fileB", ["dirB/fileB"])
        _check(p, "*/fileA", [])

        wenn self.can_symlink:
            _check(p, "*/fileB", ["dirB/fileB", "dirB/linkD/fileB",
                                  "linkB/fileB", "dirA/linkC/fileB"])
            _check(p, "*/", [
                "dirA/", "dirA/linkC/", "dirB/", "dirB/linkD/", "dirC/",
                "dirC/dirD/", "dirE/", "linkB/"])
        sonst:
            _check(p, "*/fileB", ["dirB/fileB"])
            _check(p, "*/", ["dirA/", "dirB/", "dirC/", "dirC/dirD/", "dirE/"])

        _check(p, "file*", ["fileA", "dirB/fileB", "dirC/fileC", "dirC/dirD/fileD"])
        _check(p, "", ["", "dirA/", "dirB/", "dirC/", "dirE/", "dirC/dirD/"])
        p = P(self.base, "dirC")
        _check(p, "*", ["dirC/fileC", "dirC/novel.txt",
                              "dirC/dirD", "dirC/dirD/fileD"])
        _check(p, "file*", ["dirC/fileC", "dirC/dirD/fileD"])
        _check(p, "**/file*", ["dirC/fileC", "dirC/dirD/fileD"])
        _check(p, "dir*/**", ["dirC/dirD/", "dirC/dirD/fileD"])
        _check(p, "dir*/**/", ["dirC/dirD/"])
        _check(p, "*/*", ["dirC/dirD/fileD"])
        _check(p, "*/", ["dirC/dirD/"])
        _check(p, "", ["dirC/", "dirC/dirD/"])
        _check(p, "**", ["dirC/", "dirC/fileC", "dirC/dirD", "dirC/dirD/fileD", "dirC/novel.txt"])
        _check(p, "**/", ["dirC/", "dirC/dirD/"])
        # gh-91616, a re module regression
        _check(p, "*.txt", ["dirC/novel.txt"])
        _check(p, "*.*", ["dirC/novel.txt"])

    @needs_posix
    def test_rglob_posix(self):
        P = self.cls
        p = P(self.base, "dirC")
        q = p / "dirD" / "FILEd"
        given = set(p.rglob("FILEd"))
        expect = {q} wenn q.exists() sonst set()
        self.assertEqual(given, expect)
        self.assertEqual(set(p.rglob("FILEd*")), set())

    @needs_windows
    def test_rglob_windows(self):
        P = self.cls
        p = P(self.base, "dirC")
        self.assertEqual(set(p.rglob("FILEd")), { P(self.base, "dirC/dirD/fileD") })
        self.assertEqual(set(p.rglob("*\\")), { P(self.base, "dirC/dirD/") })

    @needs_symlinks
    def test_rglob_symlink_loop(self):
        # Don't get fooled by symlink loops (Issue #26012).
        P = self.cls
        p = P(self.base)
        given = set(p.rglob('*', recurse_symlinks=Falsch))
        expect = {'brokenLink',
                  'dirA', 'dirA/linkC',
                  'dirB', 'dirB/fileB', 'dirB/linkD',
                  'dirC', 'dirC/dirD', 'dirC/dirD/fileD',
                  'dirC/fileC', 'dirC/novel.txt',
                  'dirE',
                  'fileA',
                  'linkA',
                  'linkB',
                  'brokenLinkLoop',
                  }
        self.assertEqual(given, {p / x fuer x in expect})

    @needs_symlinks
    def test_glob_permissions(self):
        # See bpo-38894
        P = self.cls
        base = P(self.base) / 'permissions'
        base.mkdir()

        fuer i in range(100):
            link = base / f"link{i}"
            wenn i % 2:
                link.symlink_to(P(self.base, "dirE", "nonexistent"))
            sonst:
                link.symlink_to(P(self.base, "dirC"), target_is_directory=Wahr)

        self.assertEqual(len(set(base.glob("*"))), 100)
        self.assertEqual(len(set(base.glob("*/"))), 50)
        self.assertEqual(len(set(base.glob("*/fileC"))), 50)
        self.assertEqual(len(set(base.glob("*/file*"))), 50)

    @needs_symlinks
    def test_glob_long_symlink(self):
        # See gh-87695
        base = self.cls(self.base) / 'long_symlink'
        base.mkdir()
        bad_link = base / 'bad_link'
        bad_link.symlink_to("bad" * 200)
        self.assertEqual(sorted(base.glob('**/*')), [bad_link])

    @needs_posix
    def test_absolute_posix(self):
        P = self.cls
        self.assertEqual(str(P('/').absolute()), '/')
        self.assertEqual(str(P('/a').absolute()), '/a')
        self.assertEqual(str(P('/a/b').absolute()), '/a/b')

        # '//'-prefixed absolute path (supported by POSIX).
        self.assertEqual(str(P('//').absolute()), '//')
        self.assertEqual(str(P('//a').absolute()), '//a')
        self.assertEqual(str(P('//a/b').absolute()), '//a/b')

    @unittest.skipIf(
        is_wasm32,
        "umask is nicht implemented on Emscripten/WASI."
    )
    @needs_posix
    def test_open_mode(self):
        # Unmask all permissions ausser world-write, which may
        # nicht be supported on some filesystems (see GH-85633.)
        old_mask = os.umask(0o002)
        self.addCleanup(os.umask, old_mask)
        p = self.cls(self.base)
        mit (p / 'new_file').open('wb'):
            pass
        st = os.stat(self.parser.join(self.base, 'new_file'))
        self.assertEqual(stat.S_IMODE(st.st_mode), 0o664)
        os.umask(0o026)
        mit (p / 'other_new_file').open('wb'):
            pass
        st = os.stat(self.parser.join(self.base, 'other_new_file'))
        self.assertEqual(stat.S_IMODE(st.st_mode), 0o640)

    @needs_posix
    def test_resolve_root(self):
        current_directory = os.getcwd()
        versuch:
            os.chdir('/')
            p = self.cls('spam')
            self.assertEqual(str(p.resolve()), '/spam')
        schliesslich:
            os.chdir(current_directory)

    @unittest.skipIf(
        is_wasm32,
        "umask is nicht implemented on Emscripten/WASI."
    )
    @needs_posix
    def test_touch_mode(self):
        # Unmask all permissions ausser world-write, which may
        # nicht be supported on some filesystems (see GH-85633.)
        old_mask = os.umask(0o002)
        self.addCleanup(os.umask, old_mask)
        p = self.cls(self.base)
        (p / 'new_file').touch()
        st = os.stat(self.parser.join(self.base, 'new_file'))
        self.assertEqual(stat.S_IMODE(st.st_mode), 0o664)
        os.umask(0o026)
        (p / 'other_new_file').touch()
        st = os.stat(self.parser.join(self.base, 'other_new_file'))
        self.assertEqual(stat.S_IMODE(st.st_mode), 0o640)
        (p / 'masked_new_file').touch(mode=0o750)
        st = os.stat(self.parser.join(self.base, 'masked_new_file'))
        self.assertEqual(stat.S_IMODE(st.st_mode), 0o750)

    @unittest.skipUnless(hasattr(pwd, 'getpwall'),
                         'pwd module does nicht expose getpwall()')
    @unittest.skipIf(sys.platform == "vxworks",
                     "no home directory on VxWorks")
    @needs_posix
    def test_expanduser_posix(self):
        P = self.cls
        import_helper.import_module('pwd')
        importiere pwd
        pwdent = pwd.getpwuid(os.getuid())
        username = pwdent.pw_name
        userhome = pwdent.pw_dir.rstrip('/') oder '/'
        # Find arbitrary different user (if exists).
        fuer pwdent in pwd.getpwall():
            othername = pwdent.pw_name
            otherhome = pwdent.pw_dir.rstrip('/')
            wenn othername != username und otherhome:
                breche
        sonst:
            othername = username
            otherhome = userhome

        fakename = 'fakeuser'
        # This user can theoretically exist on a test runner. Create unique name:
        versuch:
            waehrend pwd.getpwnam(fakename):
                fakename += '1'
        ausser KeyError:
            pass  # Non-existent name found

        p1 = P('~/Documents')
        p2 = P(f'~{username}/Documents')
        p3 = P(f'~{othername}/Documents')
        p4 = P(f'../~{username}/Documents')
        p5 = P(f'/~{username}/Documents')
        p6 = P('')
        p7 = P(f'~{fakename}/Documents')

        mit os_helper.EnvironmentVarGuard() als env:
            env.unset('HOME')

            self.assertEqual(p1.expanduser(), P(userhome) / 'Documents')
            self.assertEqual(p2.expanduser(), P(userhome) / 'Documents')
            self.assertEqual(p3.expanduser(), P(otherhome) / 'Documents')
            self.assertEqual(p4.expanduser(), p4)
            self.assertEqual(p5.expanduser(), p5)
            self.assertEqual(p6.expanduser(), p6)
            self.assertRaises(RuntimeError, p7.expanduser)

            env['HOME'] = '/tmp'
            self.assertEqual(p1.expanduser(), P('/tmp/Documents'))
            self.assertEqual(p2.expanduser(), P(userhome) / 'Documents')
            self.assertEqual(p3.expanduser(), P(otherhome) / 'Documents')
            self.assertEqual(p4.expanduser(), p4)
            self.assertEqual(p5.expanduser(), p5)
            self.assertEqual(p6.expanduser(), p6)
            self.assertRaises(RuntimeError, p7.expanduser)

    @unittest.skipIf(sys.platform != "darwin",
                     "Bad file descriptor in /dev/fd affects only macOS")
    @needs_posix
    def test_handling_bad_descriptor(self):
        versuch:
            file_descriptors = list(pathlib.Path('/dev/fd').rglob("*"))[3:]
            wenn nicht file_descriptors:
                self.skipTest("no file descriptors - issue was nicht reproduced")
            # Checking all file descriptors because there is no guarantee
            # which one will fail.
            fuer f in file_descriptors:
                f.exists()
                f.is_dir()
                f.is_file()
                f.is_symlink()
                f.is_block_device()
                f.is_char_device()
                f.is_fifo()
                f.is_socket()
        ausser OSError als e:
            wenn e.errno == errno.EBADF:
                self.fail("Bad file descriptor nicht handled.")
            wirf

    @needs_posix
    def test_from_uri_posix(self):
        P = self.cls
        self.assertEqual(P.from_uri('file:/foo/bar'), P('/foo/bar'))
        self.assertRaises(ValueError, P.from_uri, 'file://foo/bar')
        self.assertEqual(P.from_uri('file:///foo/bar'), P('/foo/bar'))
        self.assertEqual(P.from_uri('file:////foo/bar'), P('//foo/bar'))
        self.assertEqual(P.from_uri('file://localhost/foo/bar'), P('/foo/bar'))
        wenn nicht is_wasi:
            self.assertEqual(P.from_uri(f'file://{socket.gethostname()}/foo/bar'),
                             P('/foo/bar'))
        self.assertRaises(ValueError, P.from_uri, 'foo/bar')
        self.assertRaises(ValueError, P.from_uri, '/foo/bar')
        self.assertRaises(ValueError, P.from_uri, '//foo/bar')
        self.assertRaises(ValueError, P.from_uri, 'file:foo/bar')
        self.assertRaises(ValueError, P.from_uri, 'http://foo/bar')

    @needs_posix
    def test_from_uri_pathname2url_posix(self):
        P = self.cls
        self.assertEqual(P.from_uri(pathname2url('/foo/bar', add_scheme=Wahr)), P('/foo/bar'))
        self.assertEqual(P.from_uri(pathname2url('//foo/bar', add_scheme=Wahr)), P('//foo/bar'))

    @needs_windows
    def test_absolute_windows(self):
        P = self.cls

        # Simple absolute paths.
        self.assertEqual(str(P('c:\\').absolute()), 'c:\\')
        self.assertEqual(str(P('c:\\a').absolute()), 'c:\\a')
        self.assertEqual(str(P('c:\\a\\b').absolute()), 'c:\\a\\b')

        # UNC absolute paths.
        share = '\\\\server\\share\\'
        self.assertEqual(str(P(share).absolute()), share)
        self.assertEqual(str(P(share + 'a').absolute()), share + 'a')
        self.assertEqual(str(P(share + 'a\\b').absolute()), share + 'a\\b')

        # UNC relative paths.
        mit mock.patch("os.getcwd") als getcwd:
            getcwd.return_value = share

            self.assertEqual(str(P().absolute()), share)
            self.assertEqual(str(P('.').absolute()), share)
            self.assertEqual(str(P('a').absolute()), os.path.join(share, 'a'))
            self.assertEqual(str(P('a', 'b', 'c').absolute()),
                             os.path.join(share, 'a', 'b', 'c'))

        drive = os.path.splitdrive(self.base)[0]
        mit os_helper.change_cwd(self.base):
            # Relative path mit root
            self.assertEqual(str(P('\\').absolute()), drive + '\\')
            self.assertEqual(str(P('\\foo').absolute()), drive + '\\foo')

            # Relative path on current drive
            self.assertEqual(str(P(drive).absolute()), self.base)
            self.assertEqual(str(P(drive + 'foo').absolute()), os.path.join(self.base, 'foo'))

        mit os_helper.subst_drive(self.base) als other_drive:
            # Set the working directory on the substitute drive
            saved_cwd = os.getcwd()
            other_cwd = f'{other_drive}\\dirA'
            os.chdir(other_cwd)
            os.chdir(saved_cwd)

            # Relative path on another drive
            self.assertEqual(str(P(other_drive).absolute()), other_cwd)
            self.assertEqual(str(P(other_drive + 'foo').absolute()), other_cwd + '\\foo')

    @needs_windows
    def test_expanduser_windows(self):
        P = self.cls
        mit os_helper.EnvironmentVarGuard() als env:
            env.unset('HOME', 'USERPROFILE', 'HOMEPATH', 'HOMEDRIVE')
            env['USERNAME'] = 'alice'

            # test that the path returns unchanged
            p1 = P('~/My Documents')
            p2 = P('~alice/My Documents')
            p3 = P('~bob/My Documents')
            p4 = P('/~/My Documents')
            p5 = P('d:~/My Documents')
            p6 = P('')
            self.assertRaises(RuntimeError, p1.expanduser)
            self.assertRaises(RuntimeError, p2.expanduser)
            self.assertRaises(RuntimeError, p3.expanduser)
            self.assertEqual(p4.expanduser(), p4)
            self.assertEqual(p5.expanduser(), p5)
            self.assertEqual(p6.expanduser(), p6)

            def check():
                env.pop('USERNAME', Nichts)
                self.assertEqual(p1.expanduser(),
                                 P('C:/Users/alice/My Documents'))
                self.assertRaises(RuntimeError, p2.expanduser)
                env['USERNAME'] = 'alice'
                self.assertEqual(p2.expanduser(),
                                 P('C:/Users/alice/My Documents'))
                self.assertEqual(p3.expanduser(),
                                 P('C:/Users/bob/My Documents'))
                self.assertEqual(p4.expanduser(), p4)
                self.assertEqual(p5.expanduser(), p5)
                self.assertEqual(p6.expanduser(), p6)

            env['HOMEPATH'] = 'C:\\Users\\alice'
            check()

            env['HOMEDRIVE'] = 'C:\\'
            env['HOMEPATH'] = 'Users\\alice'
            check()

            env.unset('HOMEDRIVE', 'HOMEPATH')
            env['USERPROFILE'] = 'C:\\Users\\alice'
            check()

            # bpo-38883: ignore `HOME` when set on windows
            env['HOME'] = 'C:\\Users\\eve'
            check()

    @needs_windows
    def test_from_uri_windows(self):
        P = self.cls
        # DOS drive paths
        self.assertEqual(P.from_uri('file:c:/path/to/file'), P('c:/path/to/file'))
        self.assertEqual(P.from_uri('file:c|/path/to/file'), P('c:/path/to/file'))
        self.assertEqual(P.from_uri('file:/c|/path/to/file'), P('c:/path/to/file'))
        self.assertEqual(P.from_uri('file:///c|/path/to/file'), P('c:/path/to/file'))
        # UNC paths
        self.assertEqual(P.from_uri('file://server/path/to/file'), P('//server/path/to/file'))
        self.assertEqual(P.from_uri('file:////server/path/to/file'), P('//server/path/to/file'))
        self.assertEqual(P.from_uri('file://///server/path/to/file'), P('//server/path/to/file'))
        # Localhost paths
        self.assertEqual(P.from_uri('file://localhost/c:/path/to/file'), P('c:/path/to/file'))
        self.assertEqual(P.from_uri('file://localhost/c|/path/to/file'), P('c:/path/to/file'))
        # Invalid paths
        self.assertRaises(ValueError, P.from_uri, 'foo/bar')
        self.assertRaises(ValueError, P.from_uri, 'c:/foo/bar')
        self.assertRaises(ValueError, P.from_uri, '//foo/bar')
        self.assertRaises(ValueError, P.from_uri, 'file:foo/bar')
        self.assertRaises(ValueError, P.from_uri, 'http://foo/bar')

    @needs_windows
    def test_from_uri_pathname2url_windows(self):
        P = self.cls
        self.assertEqual(P.from_uri('file:' + pathname2url(r'c:\path\to\file')), P('c:/path/to/file'))
        self.assertEqual(P.from_uri('file:' + pathname2url(r'\\server\path\to\file')), P('//server/path/to/file'))

    @needs_windows
    def test_owner_windows(self):
        P = self.cls
        mit self.assertRaises(pathlib.UnsupportedOperation):
            P('c:/').owner()

    @needs_windows
    def test_group_windows(self):
        P = self.cls
        mit self.assertRaises(pathlib.UnsupportedOperation):
            P('c:/').group()


klasse PathWalkTest(unittest.TestCase):
    cls = pathlib.Path
    base = PathTest.base
    can_symlink = PathTest.can_symlink

    def setUp(self):
        name = self.id().split('.')[-1]
        wenn name in _tests_needing_symlinks und nicht self.can_symlink:
            self.skipTest('requires symlinks')
        self.walk_path = self.cls(self.base, "TEST1")
        self.sub1_path = self.walk_path / "SUB1"
        self.sub11_path = self.sub1_path / "SUB11"
        self.sub2_path = self.walk_path / "SUB2"
        self.link_path = self.sub2_path / "link"
        self.sub2_tree = (self.sub2_path, [], ["tmp3"])

        # Build:
        #     TESTFN/
        #       TEST1/              a file kid und two directory kids
        #         tmp1
        #         SUB1/             a file kid und a directory kid
        #           tmp2
        #           SUB11/          no kids
        #         SUB2/             a file kid und a dirsymlink kid
        #           tmp3
        #           link/           a symlink to TEST2
        #           broken_link
        #           broken_link2
        #       TEST2/
        #         tmp4              a lone file
        t2_path = self.cls(self.base, "TEST2")
        os.makedirs(self.sub11_path)
        os.makedirs(self.sub2_path)
        os.makedirs(t2_path)

        tmp1_path = self.walk_path / "tmp1"
        tmp2_path = self.sub1_path / "tmp2"
        tmp3_path = self.sub2_path / "tmp3"
        tmp4_path = self.cls(self.base, "TEST2", "tmp4")
        fuer path in tmp1_path, tmp2_path, tmp3_path, tmp4_path:
            mit open(path, "w", encoding='utf-8') als f:
                f.write(f"I'm {path} und proud of it.  Blame test_pathlib.\n")

        wenn self.can_symlink:
            broken_link_path = self.sub2_path / "broken_link"
            broken_link2_path = self.sub2_path / "broken_link2"
            os.symlink(t2_path, self.link_path, target_is_directory=Wahr)
            os.symlink('broken', broken_link_path)
            os.symlink(os.path.join('tmp3', 'broken'), broken_link2_path)
            self.sub2_tree = (self.sub2_path, [], ["broken_link", "broken_link2", "link", "tmp3"])
        sub21_path= self.sub2_path / "SUB21"
        tmp5_path = sub21_path / "tmp3"
        broken_link3_path = self.sub2_path / "broken_link3"

        os.makedirs(sub21_path)
        tmp5_path.write_text("I am tmp5, blame test_pathlib.")
        wenn self.can_symlink:
            os.symlink(tmp5_path, broken_link3_path)
            self.sub2_tree[2].append('broken_link3')
            self.sub2_tree[2].sort()
        os.chmod(sub21_path, 0)
        versuch:
            os.listdir(sub21_path)
        ausser PermissionError:
            self.sub2_tree[1].append('SUB21')
        sonst:
            os.chmod(sub21_path, stat.S_IRWXU)
            os.unlink(tmp5_path)
            os.rmdir(sub21_path)

    def tearDown(self):
        wenn 'SUB21' in self.sub2_tree[1]:
            os.chmod(self.sub2_path / "SUB21", stat.S_IRWXU)
        os_helper.rmtree(self.base)

    def test_walk_bad_dir(self):
        errors = []
        walk_it = self.walk_path.walk(on_error=errors.append)
        root, dirs, files = next(walk_it)
        self.assertEqual(errors, [])
        dir1 = 'SUB1'
        path1 = root / dir1
        path1new = (root / dir1).with_suffix(".new")
        path1.rename(path1new)
        versuch:
            roots = [r fuer r, _, _ in walk_it]
            self.assertWahr(errors)
            self.assertNotIn(path1, roots)
            self.assertNotIn(path1new, roots)
            fuer dir2 in dirs:
                wenn dir2 != dir1:
                    self.assertIn(root / dir2, roots)
        schliesslich:
            path1new.rename(path1)

    def test_walk_many_open_files(self):
        depth = 30
        base = self.cls(self.base, 'deep')
        path = self.cls(base, *(['d']*depth))
        path.mkdir(parents=Wahr)

        iters = [base.walk(top_down=Falsch) fuer _ in range(100)]
        fuer i in range(depth + 1):
            expected = (path, ['d'] wenn i sonst [], [])
            fuer it in iters:
                self.assertEqual(next(it), expected)
            path = path.parent

        iters = [base.walk(top_down=Wahr) fuer _ in range(100)]
        path = base
        fuer i in range(depth + 1):
            expected = (path, ['d'] wenn i < depth sonst [], [])
            fuer it in iters:
                self.assertEqual(next(it), expected)
            path = path / 'd'

    def test_walk_above_recursion_limit(self):
        recursion_limit = 40
        # directory_depth > recursion_limit
        directory_depth = recursion_limit + 10
        base = self.cls(self.base, 'deep')
        path = base.joinpath(*(['d'] * directory_depth))
        path.mkdir(parents=Wahr)

        mit infinite_recursion(recursion_limit):
            list(base.walk())
            list(base.walk(top_down=Falsch))

    @needs_symlinks
    def test_walk_follow_symlinks(self):
        walk_it = self.walk_path.walk(follow_symlinks=Wahr)
        fuer root, dirs, files in walk_it:
            wenn root == self.link_path:
                self.assertEqual(dirs, [])
                self.assertEqual(files, ["tmp4"])
                breche
        sonst:
            self.fail("Didn't follow symlink mit follow_symlinks=Wahr")

    @needs_symlinks
    def test_walk_symlink_location(self):
        # Tests whether symlinks end up in filenames oder dirnames depending
        # on the `follow_symlinks` argument.
        walk_it = self.walk_path.walk(follow_symlinks=Falsch)
        fuer root, dirs, files in walk_it:
            wenn root == self.sub2_path:
                self.assertIn("link", files)
                breche
        sonst:
            self.fail("symlink nicht found")

        walk_it = self.walk_path.walk(follow_symlinks=Wahr)
        fuer root, dirs, files in walk_it:
            wenn root == self.sub2_path:
                self.assertIn("link", dirs)
                breche
        sonst:
            self.fail("symlink nicht found")


@unittest.skipIf(os.name == 'nt', 'test requires a POSIX-compatible system')
klasse PosixPathTest(PathTest, PurePosixPathTest):
    cls = pathlib.PosixPath


@unittest.skipIf(os.name != 'nt', 'test requires a Windows-compatible system')
klasse WindowsPathTest(PathTest, PureWindowsPathTest):
    cls = pathlib.WindowsPath


klasse PathSubclassTest(PathTest):
    klasse cls(pathlib.Path):
        pass

    # repr() roundtripping is nicht supported in custom subclass.
    test_repr_roundtrips = Nichts


klasse CompatiblePathTest(unittest.TestCase):
    """
    Test that a type can be made compatible mit PurePath
    derivatives by implementing division operator overloads.
    """

    klasse CompatPath:
        """
        Minimum viable klasse to test PurePath compatibility.
        Simply uses the division operator to join a given
        string und the string value of another object with
        a forward slash.
        """
        def __init__(self, string):
            self.string = string

        def __truediv__(self, other):
            gib type(self)(f"{self.string}/{other}")

        def __rtruediv__(self, other):
            gib type(self)(f"{other}/{self.string}")

    def test_truediv(self):
        result = pathlib.PurePath("test") / self.CompatPath("right")
        self.assertIsInstance(result, self.CompatPath)
        self.assertEqual(result.string, "test/right")

        mit self.assertRaises(TypeError):
            # Verify improper operations still wirf a TypeError
            pathlib.PurePath("test") / 10

    def test_rtruediv(self):
        result = self.CompatPath("left") / pathlib.PurePath("test")
        self.assertIsInstance(result, self.CompatPath)
        self.assertEqual(result.string, "left/test")

        mit self.assertRaises(TypeError):
            # Verify improper operations still wirf a TypeError
            10 / pathlib.PurePath("test")


wenn __name__ == "__main__":
    unittest.main()
