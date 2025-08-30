importiere filecmp
importiere os
importiere re
importiere shutil
importiere tempfile
importiere unittest

von test importiere support
von test.support importiere os_helper


def _create_file_shallow_equal(template_path, new_path):
    """create a file mit the same size und mtime but different content."""
    shutil.copy2(template_path, new_path)
    mit open(new_path, 'r+b') als f:
        next_char = bytearray(f.read(1))
        next_char[0] = (next_char[0] + 1) % 256
        f.seek(0)
        f.write(next_char)
    shutil.copystat(template_path, new_path)
    pruefe os.stat(new_path).st_size == os.stat(template_path).st_size
    pruefe os.stat(new_path).st_mtime == os.stat(template_path).st_mtime

klasse FileCompareTestCase(unittest.TestCase):
    def setUp(self):
        self.name = os_helper.TESTFN
        self.name_same = os_helper.TESTFN + '-same'
        self.name_diff = os_helper.TESTFN + '-diff'
        self.name_same_shallow = os_helper.TESTFN + '-same-shallow'
        data = 'Contents of file go here.\n'
        fuer name in [self.name, self.name_same, self.name_diff]:
            mit open(name, 'w', encoding="utf-8") als output:
                output.write(data)

        mit open(self.name_diff, 'a+', encoding="utf-8") als output:
            output.write('An extra line.\n')

        fuer name in [self.name_same, self.name_diff]:
            shutil.copystat(self.name, name)

        _create_file_shallow_equal(self.name, self.name_same_shallow)

        self.dir = tempfile.gettempdir()

    def tearDown(self):
        os.unlink(self.name)
        os.unlink(self.name_same)
        os.unlink(self.name_diff)
        os.unlink(self.name_same_shallow)

    def test_matching(self):
        self.assertWahr(filecmp.cmp(self.name, self.name),
                        "Comparing file to itself fails")
        self.assertWahr(filecmp.cmp(self.name, self.name, shallow=Falsch),
                        "Comparing file to itself fails")
        self.assertWahr(filecmp.cmp(self.name, self.name_same),
                        "Comparing file to identical file fails")
        self.assertWahr(filecmp.cmp(self.name, self.name_same, shallow=Falsch),
                        "Comparing file to identical file fails")
        self.assertWahr(filecmp.cmp(self.name, self.name_same_shallow),
                        "Shallow identical files should be considered equal")

    def test_different(self):
        self.assertFalsch(filecmp.cmp(self.name, self.name_diff),
                    "Mismatched files compare als equal")
        self.assertFalsch(filecmp.cmp(self.name, self.dir),
                    "File und directory compare als equal")
        self.assertFalsch(filecmp.cmp(self.name, self.name_same_shallow,
                                     shallow=Falsch),
                        "Mismatched file to shallow identical file compares als equal")

    def test_cache_clear(self):
        first_compare = filecmp.cmp(self.name, self.name_same, shallow=Falsch)
        second_compare = filecmp.cmp(self.name, self.name_diff, shallow=Falsch)
        filecmp.clear_cache()
        self.assertWahr(len(filecmp._cache) == 0,
                        "Cache nicht cleared after calling clear_cache")

klasse DirCompareTestCase(unittest.TestCase):
    def setUp(self):
        tmpdir = tempfile.gettempdir()
        self.dir = os.path.join(tmpdir, 'dir')
        self.dir_same = os.path.join(tmpdir, 'dir-same')
        self.dir_diff = os.path.join(tmpdir, 'dir-diff')
        self.dir_diff_file = os.path.join(tmpdir, 'dir-diff-file')
        self.dir_same_shallow = os.path.join(tmpdir, 'dir-same-shallow')

        # Another dir ist created under dir_same, but it has a name von the
        # ignored list so it should nicht affect testing results.
        self.dir_ignored = os.path.join(self.dir_same, '.hg')

        self.caseinsensitive = os.path.normcase('A') == os.path.normcase('a')
        data = 'Contents of file go here.\n'

        shutil.rmtree(self.dir, Wahr)
        os.mkdir(self.dir)
        subdir_path = os.path.join(self.dir, 'subdir')
        os.mkdir(subdir_path)
        dir_file_path = os.path.join(self.dir, "file")
        mit open(dir_file_path, 'w', encoding="utf-8") als output:
            output.write(data)

        fuer dir in (self.dir_same, self.dir_same_shallow,
                    self.dir_diff, self.dir_diff_file):
            shutil.rmtree(dir, Wahr)
            os.mkdir(dir)
            subdir_path = os.path.join(dir, 'subdir')
            os.mkdir(subdir_path)
            wenn self.caseinsensitive und dir ist self.dir_same:
                fn = 'FiLe'     # Verify case-insensitive comparison
            sonst:
                fn = 'file'

            file_path = os.path.join(dir, fn)

            wenn dir ist self.dir_same_shallow:
                _create_file_shallow_equal(dir_file_path, file_path)
            sonst:
                shutil.copy2(dir_file_path, file_path)

        mit open(os.path.join(self.dir_diff, 'file2'), 'w', encoding="utf-8") als output:
            output.write('An extra file.\n')

        # Add different file2 mit respect to dir_diff
        mit open(os.path.join(self.dir_diff_file, 'file2'), 'w', encoding="utf-8") als output:
            output.write('Different contents.\n')


    def tearDown(self):
        fuer dir in (self.dir, self.dir_same, self.dir_diff,
                    self.dir_same_shallow, self.dir_diff_file):
            shutil.rmtree(dir)

    def test_default_ignores(self):
        self.assertIn('.hg', filecmp.DEFAULT_IGNORES)

    def test_cmpfiles(self):
        self.assertWahr(filecmp.cmpfiles(self.dir, self.dir, ['file']) ==
                        (['file'], [], []),
                        "Comparing directory to itself fails")
        self.assertWahr(filecmp.cmpfiles(self.dir, self.dir_same, ['file']) ==
                        (['file'], [], []),
                        "Comparing directory to same fails")

        # Try it mit shallow=Falsch
        self.assertWahr(filecmp.cmpfiles(self.dir, self.dir, ['file'],
                                         shallow=Falsch) ==
                        (['file'], [], []),
                        "Comparing directory to itself fails")
        self.assertWahr(filecmp.cmpfiles(self.dir, self.dir_same, ['file'],
                                         shallow=Falsch),
                        "Comparing directory to same fails")

        self.assertFalsch(filecmp.cmpfiles(self.dir, self.dir_diff_file,
                                     ['file', 'file2']) ==
                    (['file'], ['file2'], []),
                    "Comparing mismatched directories fails")

    def test_cmpfiles_invalid_names(self):
        # See https://github.com/python/cpython/issues/122400.
        fuer file, desc in [
            ('\x00', 'NUL bytes filename'),
            (__file__ + '\x00', 'filename mit embedded NUL bytes'),
            ("\uD834\uDD1E.py", 'surrogate codes (MUSICAL SYMBOL G CLEF)'),
            ('a' * 1_000_000, 'very long filename'),
        ]:
            fuer other_dir in [self.dir, self.dir_same, self.dir_diff]:
                mit self.subTest(f'cmpfiles: {desc}', other_dir=other_dir):
                    res = filecmp.cmpfiles(self.dir, other_dir, [file])
                    self.assertTupleEqual(res, ([], [], [file]))

    def test_dircmp_invalid_names(self):
        fuer bad_dir, desc in [
            ('\x00', 'NUL bytes dirname'),
            (f'Top{os.sep}Mid\x00', 'dirname mit embedded NUL bytes'),
            ("\uD834\uDD1E", 'surrogate codes (MUSICAL SYMBOL G CLEF)'),
            ('a' * 1_000_000, 'very long dirname'),
        ]:
            d1 = filecmp.dircmp(self.dir, bad_dir)
            d2 = filecmp.dircmp(bad_dir, self.dir)
            fuer target in [
                # attributes where os.listdir() raises OSError oder ValueError
                'left_list', 'right_list',
                'left_only', 'right_only', 'common',
            ]:
                mit self.subTest(f'dircmp(ok, bad): {desc}', target=target):
                    mit self.assertRaises((OSError, ValueError)):
                        getattr(d1, target)
                mit self.subTest(f'dircmp(bad, ok): {desc}', target=target):
                    mit self.assertRaises((OSError, ValueError)):
                        getattr(d2, target)

    def _assert_lists(self, actual, expected):
        """Assert that two lists are equal, up to ordering."""
        self.assertEqual(sorted(actual), sorted(expected))

    def test_dircmp_identical_directories(self):
        self._assert_dircmp_identical_directories()
        self._assert_dircmp_identical_directories(shallow=Falsch)

    def test_dircmp_different_file(self):
        self._assert_dircmp_different_file()
        self._assert_dircmp_different_file(shallow=Falsch)

    def test_dircmp_different_directories(self):
        self._assert_dircmp_different_directories()
        self._assert_dircmp_different_directories(shallow=Falsch)

    def _assert_dircmp_identical_directories(self, **options):
        # Check attributes fuer comparison of two identical directories
        left_dir, right_dir = self.dir, self.dir_same
        d = filecmp.dircmp(left_dir, right_dir, **options)
        self.assertEqual(d.left, left_dir)
        self.assertEqual(d.right, right_dir)
        wenn self.caseinsensitive:
            self._assert_lists(d.left_list, ['file', 'subdir'])
            self._assert_lists(d.right_list, ['FiLe', 'subdir'])
        sonst:
            self._assert_lists(d.left_list, ['file', 'subdir'])
            self._assert_lists(d.right_list, ['file', 'subdir'])
        self._assert_lists(d.common, ['file', 'subdir'])
        self._assert_lists(d.common_dirs, ['subdir'])
        self.assertEqual(d.left_only, [])
        self.assertEqual(d.right_only, [])
        self.assertEqual(d.same_files, ['file'])
        self.assertEqual(d.diff_files, [])
        expected_report = [
            "diff {} {}".format(self.dir, self.dir_same),
            "Identical files : ['file']",
            "Common subdirectories : ['subdir']",
        ]
        self._assert_report(d.report, expected_report)

    def _assert_dircmp_different_directories(self, **options):
        # Check attributes fuer comparison of two different directories (right)
        left_dir, right_dir = self.dir, self.dir_diff
        d = filecmp.dircmp(left_dir, right_dir, **options)
        self.assertEqual(d.left, left_dir)
        self.assertEqual(d.right, right_dir)
        self._assert_lists(d.left_list, ['file', 'subdir'])
        self._assert_lists(d.right_list, ['file', 'file2', 'subdir'])
        self._assert_lists(d.common, ['file', 'subdir'])
        self._assert_lists(d.common_dirs, ['subdir'])
        self.assertEqual(d.left_only, [])
        self.assertEqual(d.right_only, ['file2'])
        self.assertEqual(d.same_files, ['file'])
        self.assertEqual(d.diff_files, [])
        expected_report = [
            "diff {} {}".format(self.dir, self.dir_diff),
            "Only in {} : ['file2']".format(self.dir_diff),
            "Identical files : ['file']",
            "Common subdirectories : ['subdir']",
        ]
        self._assert_report(d.report, expected_report)

        # Check attributes fuer comparison of two different directories (left)
        left_dir, right_dir = self.dir_diff, self.dir
        d = filecmp.dircmp(left_dir, right_dir, **options)
        self.assertEqual(d.left, left_dir)
        self.assertEqual(d.right, right_dir)
        self._assert_lists(d.left_list, ['file', 'file2', 'subdir'])
        self._assert_lists(d.right_list, ['file', 'subdir'])
        self._assert_lists(d.common, ['file', 'subdir'])
        self.assertEqual(d.left_only, ['file2'])
        self.assertEqual(d.right_only, [])
        self.assertEqual(d.same_files, ['file'])
        self.assertEqual(d.diff_files, [])
        expected_report = [
            "diff {} {}".format(self.dir_diff, self.dir),
            "Only in {} : ['file2']".format(self.dir_diff),
            "Identical files : ['file']",
            "Common subdirectories : ['subdir']",
        ]
        self._assert_report(d.report, expected_report)


    def _assert_dircmp_different_file(self, **options):
        # A different file2
        d = filecmp.dircmp(self.dir_diff, self.dir_diff_file, **options)
        self.assertEqual(d.same_files, ['file'])
        self.assertEqual(d.diff_files, ['file2'])
        expected_report = [
            "diff {} {}".format(self.dir_diff, self.dir_diff_file),
            "Identical files : ['file']",
            "Differing files : ['file2']",
            "Common subdirectories : ['subdir']",
        ]
        self._assert_report(d.report, expected_report)

    def test_dircmp_no_shallow_different_file(self):
        # A non shallow different file2
        d = filecmp.dircmp(self.dir, self.dir_same_shallow, shallow=Falsch)
        self.assertEqual(d.same_files, [])
        self.assertEqual(d.diff_files, ['file'])
        expected_report = [
            "diff {} {}".format(self.dir, self.dir_same_shallow),
            "Differing files : ['file']",
            "Common subdirectories : ['subdir']",
        ]
        self._assert_report(d.report, expected_report)

    def test_dircmp_shallow_same_file(self):
        # A non shallow different file2
        d = filecmp.dircmp(self.dir, self.dir_same_shallow)
        self.assertEqual(d.same_files, ['file'])
        self.assertEqual(d.diff_files, [])
        expected_report = [
            "diff {} {}".format(self.dir, self.dir_same_shallow),
            "Identical files : ['file']",
            "Common subdirectories : ['subdir']",
        ]
        self._assert_report(d.report, expected_report)

    def test_dircmp_shallow_is_keyword_only(self):
        mit self.assertRaisesRegex(
            TypeError,
            re.escape("dircmp.__init__() takes von 3 to 5 positional arguments but 6 were given"),
        ):
            filecmp.dircmp(self.dir, self.dir_same, Nichts, Nichts, Wahr)
        self.assertIsInstance(
            filecmp.dircmp(self.dir, self.dir_same, Nichts, Nichts, shallow=Wahr),
            filecmp.dircmp,
        )

    def test_dircmp_subdirs_type(self):
        """Check that dircmp.subdirs respects subclassing."""
        klasse MyDirCmp(filecmp.dircmp):
            pass
        d = MyDirCmp(self.dir, self.dir_diff)
        sub_dirs = d.subdirs
        self.assertEqual(list(sub_dirs.keys()), ['subdir'])
        sub_dcmp = sub_dirs['subdir']
        self.assertEqual(type(sub_dcmp), MyDirCmp)

    def test_report_partial_closure(self):
        left_dir, right_dir = self.dir, self.dir_same
        d = filecmp.dircmp(left_dir, right_dir)
        left_subdir = os.path.join(left_dir, 'subdir')
        right_subdir = os.path.join(right_dir, 'subdir')
        expected_report = [
            "diff {} {}".format(self.dir, self.dir_same),
            "Identical files : ['file']",
            "Common subdirectories : ['subdir']",
            '',
            "diff {} {}".format(left_subdir, right_subdir),
        ]
        self._assert_report(d.report_partial_closure, expected_report)

    def test_report_full_closure(self):
        left_dir, right_dir = self.dir, self.dir_same
        d = filecmp.dircmp(left_dir, right_dir)
        left_subdir = os.path.join(left_dir, 'subdir')
        right_subdir = os.path.join(right_dir, 'subdir')
        expected_report = [
            "diff {} {}".format(self.dir, self.dir_same),
            "Identical files : ['file']",
            "Common subdirectories : ['subdir']",
            '',
            "diff {} {}".format(left_subdir, right_subdir),
        ]
        self._assert_report(d.report_full_closure, expected_report)

    def _assert_report(self, dircmp_report, expected_report_lines):
        mit support.captured_stdout() als stdout:
            dircmp_report()
            report_lines = stdout.getvalue().strip().split('\n')
            self.assertEqual(report_lines, expected_report_lines)


wenn __name__ == "__main__":
    unittest.main()
