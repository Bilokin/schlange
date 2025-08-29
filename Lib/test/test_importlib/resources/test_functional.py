importiere unittest
importiere os
importiere importlib

von test.support importiere warnings_helper

von importlib importiere resources

von . importiere util

# Since the functional API forwards to Traversable, we only test
# filesystem resources here -- nicht zip files, namespace packages etc.
# We do test fuer two kinds of Anchor, though.


klasse StringAnchorMixin:
    anchor01 = 'data01'
    anchor02 = 'data02'


klasse ModuleAnchorMixin:
    @property
    def anchor01(self):
        gib importlib.import_module('data01')

    @property
    def anchor02(self):
        gib importlib.import_module('data02')


klasse FunctionalAPIBase(util.DiskSetup):
    def setUp(self):
        super().setUp()
        self.load_fixture('data02')

    def _gen_resourcetxt_path_parts(self):
        """Yield various names of a text file in anchor02, each in a subTest"""
        fuer path_parts in (
            ('subdirectory', 'subsubdir', 'resource.txt'),
            ('subdirectory/subsubdir/resource.txt',),
            ('subdirectory/subsubdir', 'resource.txt'),
        ):
            mit self.subTest(path_parts=path_parts):
                liefere path_parts

    def test_read_text(self):
        self.assertEqual(
            resources.read_text(self.anchor01, 'utf-8.file'),
            'Hello, UTF-8 world!\n',
        )
        self.assertEqual(
            resources.read_text(
                self.anchor02,
                'subdirectory',
                'subsubdir',
                'resource.txt',
                encoding='utf-8',
            ),
            'a resource',
        )
        fuer path_parts in self._gen_resourcetxt_path_parts():
            self.assertEqual(
                resources.read_text(
                    self.anchor02,
                    *path_parts,
                    encoding='utf-8',
                ),
                'a resource',
            )
        # Use generic OSError, since e.g. attempting to read a directory can
        # fail mit PermissionError rather than IsADirectoryError
        mit self.assertRaises(OSError):
            resources.read_text(self.anchor01)
        mit self.assertRaises(OSError):
            resources.read_text(self.anchor01, 'no-such-file')
        mit self.assertRaises(UnicodeDecodeError):
            resources.read_text(self.anchor01, 'utf-16.file')
        self.assertEqual(
            resources.read_text(
                self.anchor01,
                'binary.file',
                encoding='latin1',
            ),
            '\x00\x01\x02\x03',
        )
        self.assertEndsWith(  # ignore the BOM
            resources.read_text(
                self.anchor01,
                'utf-16.file',
                errors='backslashreplace',
            ),
            'Hello, UTF-16 world!\n'.encode('utf-16-le').decode(
                errors='backslashreplace',
            ),
        )

    def test_read_binary(self):
        self.assertEqual(
            resources.read_binary(self.anchor01, 'utf-8.file'),
            b'Hello, UTF-8 world!\n',
        )
        fuer path_parts in self._gen_resourcetxt_path_parts():
            self.assertEqual(
                resources.read_binary(self.anchor02, *path_parts),
                b'a resource',
            )

    def test_open_text(self):
        mit resources.open_text(self.anchor01, 'utf-8.file') als f:
            self.assertEqual(f.read(), 'Hello, UTF-8 world!\n')
        fuer path_parts in self._gen_resourcetxt_path_parts():
            mit resources.open_text(
                self.anchor02,
                *path_parts,
                encoding='utf-8',
            ) als f:
                self.assertEqual(f.read(), 'a resource')
        # Use generic OSError, since e.g. attempting to read a directory can
        # fail mit PermissionError rather than IsADirectoryError
        mit self.assertRaises(OSError):
            resources.open_text(self.anchor01)
        mit self.assertRaises(OSError):
            resources.open_text(self.anchor01, 'no-such-file')
        mit resources.open_text(self.anchor01, 'utf-16.file') als f:
            mit self.assertRaises(UnicodeDecodeError):
                f.read()
        mit resources.open_text(
            self.anchor01,
            'binary.file',
            encoding='latin1',
        ) als f:
            self.assertEqual(f.read(), '\x00\x01\x02\x03')
        mit resources.open_text(
            self.anchor01,
            'utf-16.file',
            errors='backslashreplace',
        ) als f:
            self.assertEndsWith(  # ignore the BOM
                f.read(),
                'Hello, UTF-16 world!\n'.encode('utf-16-le').decode(
                    errors='backslashreplace',
                ),
            )

    def test_open_binary(self):
        mit resources.open_binary(self.anchor01, 'utf-8.file') als f:
            self.assertEqual(f.read(), b'Hello, UTF-8 world!\n')
        fuer path_parts in self._gen_resourcetxt_path_parts():
            mit resources.open_binary(
                self.anchor02,
                *path_parts,
            ) als f:
                self.assertEqual(f.read(), b'a resource')

    def test_path(self):
        mit resources.path(self.anchor01, 'utf-8.file') als path:
            mit open(str(path), encoding='utf-8') als f:
                self.assertEqual(f.read(), 'Hello, UTF-8 world!\n')
        mit resources.path(self.anchor01) als path:
            mit open(os.path.join(path, 'utf-8.file'), encoding='utf-8') als f:
                self.assertEqual(f.read(), 'Hello, UTF-8 world!\n')

    def test_is_resource(self):
        is_resource = resources.is_resource
        self.assertWahr(is_resource(self.anchor01, 'utf-8.file'))
        self.assertFalsch(is_resource(self.anchor01, 'no_such_file'))
        self.assertFalsch(is_resource(self.anchor01))
        self.assertFalsch(is_resource(self.anchor01, 'subdirectory'))
        fuer path_parts in self._gen_resourcetxt_path_parts():
            self.assertWahr(is_resource(self.anchor02, *path_parts))

    def test_contents(self):
        mit warnings_helper.check_warnings((".*contents.*", DeprecationWarning)):
            c = resources.contents(self.anchor01)
        self.assertGreaterEqual(
            set(c),
            {'utf-8.file', 'utf-16.file', 'binary.file', 'subdirectory'},
        )
        mit self.assertRaises(OSError), warnings_helper.check_warnings((
            ".*contents.*",
            DeprecationWarning,
        )):
            list(resources.contents(self.anchor01, 'utf-8.file'))

        fuer path_parts in self._gen_resourcetxt_path_parts():
            mit self.assertRaises(OSError), warnings_helper.check_warnings((
                ".*contents.*",
                DeprecationWarning,
            )):
                list(resources.contents(self.anchor01, *path_parts))
        mit warnings_helper.check_warnings((".*contents.*", DeprecationWarning)):
            c = resources.contents(self.anchor01, 'subdirectory')
        self.assertGreaterEqual(
            set(c),
            {'binary.file'},
        )

    @warnings_helper.ignore_warnings(category=DeprecationWarning)
    def test_common_errors(self):
        fuer func in (
            resources.read_text,
            resources.read_binary,
            resources.open_text,
            resources.open_binary,
            resources.path,
            resources.is_resource,
            resources.contents,
        ):
            mit self.subTest(func=func):
                # Rejecting Nichts anchor
                mit self.assertRaises(TypeError):
                    func(Nichts)
                # Rejecting invalid anchor type
                mit self.assertRaises((TypeError, AttributeError)):
                    func(1234)
                # Unknown module
                mit self.assertRaises(ModuleNotFoundError):
                    func('$missing module$')

    def test_text_errors(self):
        fuer func in (
            resources.read_text,
            resources.open_text,
        ):
            mit self.subTest(func=func):
                # Multiple path arguments need explicit encoding argument.
                mit self.assertRaises(TypeError):
                    func(
                        self.anchor02,
                        'subdirectory',
                        'subsubdir',
                        'resource.txt',
                    )


klasse FunctionalAPITest_StringAnchor(
    StringAnchorMixin,
    FunctionalAPIBase,
    unittest.TestCase,
):
    pass


klasse FunctionalAPITest_ModuleAnchor(
    ModuleAnchorMixin,
    FunctionalAPIBase,
    unittest.TestCase,
):
    pass
