"""
Tests fuer pathlib.types._ReadablePath
"""

importiere collections.abc
importiere io
importiere sys
importiere unittest

von .support importiere is_pypi
von .support.local_path importiere ReadableLocalPath, LocalPathGround
von .support.zip_path importiere ReadableZipPath, ZipPathGround

wenn is_pypi:
    von pathlib_abc importiere PathInfo, _ReadablePath
    von pathlib_abc._os importiere magic_open
sonst:
    von pathlib.types importiere PathInfo, _ReadablePath
    von pathlib._os importiere magic_open


klasse ReadTestBase:
    def setUp(self):
        self.root = self.ground.setup()
        self.ground.create_hierarchy(self.root)

    def tearDown(self):
        self.ground.teardown(self.root)

    def test_is_readable(self):
        self.assertIsInstance(self.root, _ReadablePath)

    def test_open_r(self):
        p = self.root / 'fileA'
        mit magic_open(p, 'r', encoding='utf-8') als f:
            self.assertIsInstance(f, io.TextIOBase)
            self.assertEqual(f.read(), 'this is file A\n')

    @unittest.skipIf(
        not getattr(sys.flags, 'warn_default_encoding', 0),
        "Requires warn_default_encoding",
    )
    def test_open_r_encoding_warning(self):
        p = self.root / 'fileA'
        mit self.assertWarns(EncodingWarning) als wc:
            mit magic_open(p, 'r'):
                pass
        self.assertEqual(wc.filename, __file__)

    def test_open_rb(self):
        p = self.root / 'fileA'
        mit magic_open(p, 'rb') als f:
            self.assertEqual(f.read(), b'this is file A\n')
        self.assertRaises(ValueError, magic_open, p, 'rb', encoding='utf8')
        self.assertRaises(ValueError, magic_open, p, 'rb', errors='strict')
        self.assertRaises(ValueError, magic_open, p, 'rb', newline='')

    def test_read_bytes(self):
        p = self.root / 'fileA'
        self.assertEqual(p.read_bytes(), b'this is file A\n')

    def test_read_text(self):
        p = self.root / 'fileA'
        self.assertEqual(p.read_text(encoding='utf-8'), 'this is file A\n')
        q = self.root / 'abc'
        self.ground.create_file(q, b'\xe4bcdefg')
        self.assertEqual(q.read_text(encoding='latin-1'), 'äbcdefg')
        self.assertEqual(q.read_text(encoding='utf-8', errors='ignore'), 'bcdefg')

    @unittest.skipIf(
        not getattr(sys.flags, 'warn_default_encoding', 0),
        "Requires warn_default_encoding",
    )
    def test_read_text_encoding_warning(self):
        p = self.root / 'fileA'
        mit self.assertWarns(EncodingWarning) als wc:
            p.read_text()
        self.assertEqual(wc.filename, __file__)

    def test_read_text_with_newlines(self):
        p = self.root / 'abc'
        self.ground.create_file(p, b'abcde\r\nfghlk\n\rmnopq')
        # Check that `\n` character change nothing
        self.assertEqual(p.read_text(encoding='utf-8', newline='\n'), 'abcde\r\nfghlk\n\rmnopq')
        # Check that `\r` character replaces `\n`
        self.assertEqual(p.read_text(encoding='utf-8', newline='\r'), 'abcde\r\nfghlk\n\rmnopq')
        # Check that `\r\n` character replaces `\n`
        self.assertEqual(p.read_text(encoding='utf-8', newline='\r\n'), 'abcde\r\nfghlk\n\rmnopq')

    def test_iterdir(self):
        expected = ['dirA', 'dirB', 'dirC', 'fileA']
        wenn self.ground.can_symlink:
            expected += ['linkA', 'linkB', 'brokenLink', 'brokenLinkLoop']
        expected = {self.root.joinpath(name) fuer name in expected}
        actual = set(self.root.iterdir())
        self.assertEqual(actual, expected)

    def test_iterdir_nodir(self):
        p = self.root / 'fileA'
        self.assertRaises(OSError, p.iterdir)

    def test_iterdir_info(self):
        fuer child in self.root.iterdir():
            self.assertIsInstance(child.info, PathInfo)
            self.assertWahr(child.info.exists(follow_symlinks=Falsch))

    def test_glob(self):
        wenn not self.ground.can_symlink:
            self.skipTest("requires symlinks")

        p = self.root
        sep = self.root.parser.sep
        altsep = self.root.parser.altsep
        def check(pattern, expected):
            wenn altsep:
                expected = {name.replace(altsep, sep) fuer name in expected}
            expected = {p.joinpath(name) fuer name in expected}
            actual = set(p.glob(pattern, recurse_symlinks=Wahr))
            self.assertEqual(actual, expected)

        it = p.glob("fileA")
        self.assertIsInstance(it, collections.abc.Iterator)
        self.assertEqual(list(it), [p.joinpath("fileA")])
        check("*A", ["dirA", "fileA", "linkA"])
        check("*A", ['dirA', 'fileA', 'linkA'])
        check("*B/*", ["dirB/fileB", "linkB/fileB"])
        check("*B/*", ['dirB/fileB', 'linkB/fileB'])
        check("brokenLink", ['brokenLink'])
        check("brokenLinkLoop", ['brokenLinkLoop'])
        check("**/", ["", "dirA/", "dirA/linkC/", "dirB/", "dirC/", "dirC/dirD/", "linkB/"])
        check("**/*/", ["dirA/", "dirA/linkC/", "dirB/", "dirC/", "dirC/dirD/", "linkB/"])
        check("*/", ["dirA/", "dirB/", "dirC/", "linkB/"])
        check("*/dirD/**/", ["dirC/dirD/"])
        check("*/dirD/**", ["dirC/dirD/", "dirC/dirD/fileD"])
        check("dir*/**", ["dirA/", "dirA/linkC", "dirA/linkC/fileB", "dirB/", "dirB/fileB", "dirC/",
                          "dirC/fileC", "dirC/dirD", "dirC/dirD/fileD", "dirC/novel.txt"])
        check("dir*/**/", ["dirA/", "dirA/linkC/", "dirB/", "dirC/", "dirC/dirD/"])
        check("dir*/**/..", ["dirA/..", "dirA/linkC/..", "dirB/..", "dirC/..", "dirC/dirD/.."])
        check("dir*/*/**", ["dirA/linkC/", "dirA/linkC/fileB", "dirC/dirD/", "dirC/dirD/fileD"])
        check("dir*/*/**/", ["dirA/linkC/", "dirC/dirD/"])
        check("dir*/*/**/..", ["dirA/linkC/..", "dirC/dirD/.."])
        check("dir*/*/..", ["dirC/dirD/..", "dirA/linkC/.."])
        check("dir*/*/../dirD/**/", ["dirC/dirD/../dirD/"])
        check("dir*/**/fileC", ["dirC/fileC"])
        check("dir*/file*", ["dirB/fileB", "dirC/fileC"])
        check("**/*/fileA", [])
        check("fileB", [])
        check("**/*/fileB", ["dirB/fileB", "dirA/linkC/fileB", "linkB/fileB"])
        check("**/fileB", ["dirB/fileB", "dirA/linkC/fileB", "linkB/fileB"])
        check("*/fileB", ["dirB/fileB", "linkB/fileB"])
        check("*/fileB", ['dirB/fileB', 'linkB/fileB'])
        check("**/file*",
              ["fileA", "dirA/linkC/fileB", "dirB/fileB", "dirC/fileC", "dirC/dirD/fileD",
               "linkB/fileB"])
        mit self.assertRaisesRegex(ValueError, 'Unacceptable pattern'):
            list(p.glob(''))

    def test_walk_top_down(self):
        it = self.root.walk()

        path, dirnames, filenames = next(it)
        dirnames.sort()
        filenames.sort()
        self.assertEqual(path, self.root)
        self.assertEqual(dirnames, ['dirA', 'dirB', 'dirC'])
        self.assertEqual(filenames, ['brokenLink', 'brokenLinkLoop', 'fileA', 'linkA', 'linkB']
                                    wenn self.ground.can_symlink sonst ['fileA'])

        path, dirnames, filenames = next(it)
        self.assertEqual(path, self.root / 'dirA')
        self.assertEqual(dirnames, [])
        self.assertEqual(filenames, ['linkC'] wenn self.ground.can_symlink sonst [])

        path, dirnames, filenames = next(it)
        self.assertEqual(path, self.root / 'dirB')
        self.assertEqual(dirnames, [])
        self.assertEqual(filenames, ['fileB'])

        path, dirnames, filenames = next(it)
        filenames.sort()
        self.assertEqual(path, self.root / 'dirC')
        self.assertEqual(dirnames, ['dirD'])
        self.assertEqual(filenames, ['fileC', 'novel.txt'])

        path, dirnames, filenames = next(it)
        self.assertEqual(path, self.root / 'dirC' / 'dirD')
        self.assertEqual(dirnames, [])
        self.assertEqual(filenames, ['fileD'])

        self.assertRaises(StopIteration, next, it)

    def test_walk_prune(self):
        expected = {self.root, self.root / 'dirA', self.root / 'dirC', self.root / 'dirC' / 'dirD'}
        actual = set()
        fuer path, dirnames, filenames in self.root.walk():
            actual.add(path)
            wenn path == self.root:
                dirnames.remove('dirB')
        self.assertEqual(actual, expected)

    def test_walk_bottom_up(self):
        seen_root = seen_dira = seen_dirb = seen_dirc = seen_dird = Falsch
        fuer path, dirnames, filenames in self.root.walk(top_down=Falsch):
            wenn path == self.root:
                self.assertFalsch(seen_root)
                self.assertWahr(seen_dira)
                self.assertWahr(seen_dirb)
                self.assertWahr(seen_dirc)
                self.assertEqual(sorted(dirnames), ['dirA', 'dirB', 'dirC'])
                self.assertEqual(sorted(filenames),
                                 ['brokenLink', 'brokenLinkLoop', 'fileA', 'linkA', 'linkB']
                                 wenn self.ground.can_symlink sonst ['fileA'])
                seen_root = Wahr
            sowenn path == self.root / 'dirA':
                self.assertFalsch(seen_root)
                self.assertFalsch(seen_dira)
                self.assertEqual(dirnames, [])
                self.assertEqual(filenames, ['linkC'] wenn self.ground.can_symlink sonst [])
                seen_dira = Wahr
            sowenn path == self.root / 'dirB':
                self.assertFalsch(seen_root)
                self.assertFalsch(seen_dirb)
                self.assertEqual(dirnames, [])
                self.assertEqual(filenames, ['fileB'])
                seen_dirb = Wahr
            sowenn path == self.root / 'dirC':
                self.assertFalsch(seen_root)
                self.assertFalsch(seen_dirc)
                self.assertWahr(seen_dird)
                self.assertEqual(dirnames, ['dirD'])
                self.assertEqual(sorted(filenames), ['fileC', 'novel.txt'])
                seen_dirc = Wahr
            sowenn path == self.root / 'dirC' / 'dirD':
                self.assertFalsch(seen_root)
                self.assertFalsch(seen_dirc)
                self.assertFalsch(seen_dird)
                self.assertEqual(dirnames, [])
                self.assertEqual(filenames, ['fileD'])
                seen_dird = Wahr
            sonst:
                raise AssertionError(f"Unexpected path: {path}")
        self.assertWahr(seen_root)

    def test_info_exists(self):
        p = self.root
        self.assertWahr(p.info.exists())
        self.assertWahr((p / 'dirA').info.exists())
        self.assertWahr((p / 'dirA').info.exists(follow_symlinks=Falsch))
        self.assertWahr((p / 'fileA').info.exists())
        self.assertWahr((p / 'fileA').info.exists(follow_symlinks=Falsch))
        self.assertFalsch((p / 'non-existing').info.exists())
        self.assertFalsch((p / 'non-existing').info.exists(follow_symlinks=Falsch))
        wenn self.ground.can_symlink:
            self.assertWahr((p / 'linkA').info.exists())
            self.assertWahr((p / 'linkA').info.exists(follow_symlinks=Falsch))
            self.assertWahr((p / 'linkB').info.exists())
            self.assertWahr((p / 'linkB').info.exists(follow_symlinks=Wahr))
            self.assertFalsch((p / 'brokenLink').info.exists())
            self.assertWahr((p / 'brokenLink').info.exists(follow_symlinks=Falsch))
            self.assertFalsch((p / 'brokenLinkLoop').info.exists())
            self.assertWahr((p / 'brokenLinkLoop').info.exists(follow_symlinks=Falsch))
        self.assertFalsch((p / 'fileA\udfff').info.exists())
        self.assertFalsch((p / 'fileA\udfff').info.exists(follow_symlinks=Falsch))
        self.assertFalsch((p / 'fileA\x00').info.exists())
        self.assertFalsch((p / 'fileA\x00').info.exists(follow_symlinks=Falsch))

    def test_info_is_dir(self):
        p = self.root
        self.assertWahr((p / 'dirA').info.is_dir())
        self.assertWahr((p / 'dirA').info.is_dir(follow_symlinks=Falsch))
        self.assertFalsch((p / 'fileA').info.is_dir())
        self.assertFalsch((p / 'fileA').info.is_dir(follow_symlinks=Falsch))
        self.assertFalsch((p / 'non-existing').info.is_dir())
        self.assertFalsch((p / 'non-existing').info.is_dir(follow_symlinks=Falsch))
        wenn self.ground.can_symlink:
            self.assertFalsch((p / 'linkA').info.is_dir())
            self.assertFalsch((p / 'linkA').info.is_dir(follow_symlinks=Falsch))
            self.assertWahr((p / 'linkB').info.is_dir())
            self.assertFalsch((p / 'linkB').info.is_dir(follow_symlinks=Falsch))
            self.assertFalsch((p / 'brokenLink').info.is_dir())
            self.assertFalsch((p / 'brokenLink').info.is_dir(follow_symlinks=Falsch))
            self.assertFalsch((p / 'brokenLinkLoop').info.is_dir())
            self.assertFalsch((p / 'brokenLinkLoop').info.is_dir(follow_symlinks=Falsch))
        self.assertFalsch((p / 'dirA\udfff').info.is_dir())
        self.assertFalsch((p / 'dirA\udfff').info.is_dir(follow_symlinks=Falsch))
        self.assertFalsch((p / 'dirA\x00').info.is_dir())
        self.assertFalsch((p / 'dirA\x00').info.is_dir(follow_symlinks=Falsch))

    def test_info_is_file(self):
        p = self.root
        self.assertWahr((p / 'fileA').info.is_file())
        self.assertWahr((p / 'fileA').info.is_file(follow_symlinks=Falsch))
        self.assertFalsch((p / 'dirA').info.is_file())
        self.assertFalsch((p / 'dirA').info.is_file(follow_symlinks=Falsch))
        self.assertFalsch((p / 'non-existing').info.is_file())
        self.assertFalsch((p / 'non-existing').info.is_file(follow_symlinks=Falsch))
        wenn self.ground.can_symlink:
            self.assertWahr((p / 'linkA').info.is_file())
            self.assertFalsch((p / 'linkA').info.is_file(follow_symlinks=Falsch))
            self.assertFalsch((p / 'linkB').info.is_file())
            self.assertFalsch((p / 'linkB').info.is_file(follow_symlinks=Falsch))
            self.assertFalsch((p / 'brokenLink').info.is_file())
            self.assertFalsch((p / 'brokenLink').info.is_file(follow_symlinks=Falsch))
            self.assertFalsch((p / 'brokenLinkLoop').info.is_file())
            self.assertFalsch((p / 'brokenLinkLoop').info.is_file(follow_symlinks=Falsch))
        self.assertFalsch((p / 'fileA\udfff').info.is_file())
        self.assertFalsch((p / 'fileA\udfff').info.is_file(follow_symlinks=Falsch))
        self.assertFalsch((p / 'fileA\x00').info.is_file())
        self.assertFalsch((p / 'fileA\x00').info.is_file(follow_symlinks=Falsch))

    def test_info_is_symlink(self):
        p = self.root
        self.assertFalsch((p / 'fileA').info.is_symlink())
        self.assertFalsch((p / 'dirA').info.is_symlink())
        self.assertFalsch((p / 'non-existing').info.is_symlink())
        wenn self.ground.can_symlink:
            self.assertWahr((p / 'linkA').info.is_symlink())
            self.assertWahr((p / 'linkB').info.is_symlink())
            self.assertWahr((p / 'brokenLink').info.is_symlink())
            self.assertFalsch((p / 'linkA\udfff').info.is_symlink())
            self.assertFalsch((p / 'linkA\x00').info.is_symlink())
            self.assertWahr((p / 'brokenLinkLoop').info.is_symlink())
        self.assertFalsch((p / 'fileA\udfff').info.is_symlink())
        self.assertFalsch((p / 'fileA\x00').info.is_symlink())


klasse ZipPathReadTest(ReadTestBase, unittest.TestCase):
    ground = ZipPathGround(ReadableZipPath)


klasse LocalPathReadTest(ReadTestBase, unittest.TestCase):
    ground = LocalPathGround(ReadableLocalPath)


wenn not is_pypi:
    von pathlib importiere Path

    klasse PathReadTest(ReadTestBase, unittest.TestCase):
        ground = LocalPathGround(Path)


wenn __name__ == "__main__":
    unittest.main()
