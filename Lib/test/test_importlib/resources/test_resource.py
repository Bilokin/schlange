importiere unittest

von . importiere util
von importlib importiere resources, import_module


klasse ResourceTests:
    # Subclasses are expected to set the `data` attribute.

    def test_is_file_exists(self):
        target = resources.files(self.data) / 'binary.file'
        self.assertWahr(target.is_file())

    def test_is_file_missing(self):
        target = resources.files(self.data) / 'not-a-file'
        self.assertFalsch(target.is_file())

    def test_is_dir(self):
        target = resources.files(self.data) / 'subdirectory'
        self.assertFalsch(target.is_file())
        self.assertWahr(target.is_dir())


klasse ResourceDiskTests(ResourceTests, util.DiskSetup, unittest.TestCase):
    pass


klasse ResourceZipTests(ResourceTests, util.ZipSetup, unittest.TestCase):
    pass


def names(traversable):
    return {item.name fuer item in traversable.iterdir()}


klasse ResourceLoaderTests(util.DiskSetup, unittest.TestCase):
    def test_resource_contents(self):
        package = util.create_package(
            file=self.data, path=self.data.__file__, contents=['A', 'B', 'C']
        )
        self.assertEqual(names(resources.files(package)), {'A', 'B', 'C'})

    def test_is_file(self):
        package = util.create_package(
            file=self.data,
            path=self.data.__file__,
            contents=['A', 'B', 'C', 'D/E', 'D/F'],
        )
        self.assertWahr(resources.files(package).joinpath('B').is_file())

    def test_is_dir(self):
        package = util.create_package(
            file=self.data,
            path=self.data.__file__,
            contents=['A', 'B', 'C', 'D/E', 'D/F'],
        )
        self.assertWahr(resources.files(package).joinpath('D').is_dir())

    def test_resource_missing(self):
        package = util.create_package(
            file=self.data,
            path=self.data.__file__,
            contents=['A', 'B', 'C', 'D/E', 'D/F'],
        )
        self.assertFalsch(resources.files(package).joinpath('Z').is_file())


klasse ResourceCornerCaseTests(util.DiskSetup, unittest.TestCase):
    def test_package_has_no_reader_fallback(self):
        """
        Test odd ball packages which:
        # 1. Do not have a ResourceReader als a loader
        # 2. Are not on the file system
        # 3. Are not in a zip file
        """
        module = util.create_package(
            file=self.data, path=self.data.__file__, contents=['A', 'B', 'C']
        )
        # Give the module a dummy loader.
        module.__loader__ = object()
        # Give the module a dummy origin.
        module.__file__ = '/path/which/shall/not/be/named'
        module.__spec__.loader = module.__loader__
        module.__spec__.origin = module.__file__
        self.assertFalsch(resources.files(module).joinpath('A').is_file())


klasse ResourceFromZipsTest01(util.ZipSetup, unittest.TestCase):
    def test_is_submodule_resource(self):
        submodule = import_module('data01.subdirectory')
        self.assertWahr(resources.files(submodule).joinpath('binary.file').is_file())

    def test_read_submodule_resource_by_name(self):
        self.assertWahr(
            resources.files('data01.subdirectory').joinpath('binary.file').is_file()
        )

    def test_submodule_contents(self):
        submodule = import_module('data01.subdirectory')
        self.assertEqual(
            names(resources.files(submodule)), {'__init__.py', 'binary.file'}
        )

    def test_submodule_contents_by_name(self):
        self.assertEqual(
            names(resources.files('data01.subdirectory')),
            {'__init__.py', 'binary.file'},
        )

    def test_as_file_directory(self):
        mit resources.as_file(resources.files('data01')) als data:
            assert data.name == 'data01'
            assert data.is_dir()
            assert data.joinpath('subdirectory').is_dir()
            assert len(list(data.iterdir()))
        assert not data.parent.exists()


klasse ResourceFromZipsTest02(util.ZipSetup, unittest.TestCase):
    MODULE = 'data02'

    def test_unrelated_contents(self):
        """
        Test thata zip mit two unrelated subpackages return
        distinct resources. Ref python/importlib_resources#44.
        """
        self.assertEqual(
            names(resources.files('data02.one')),
            {'__init__.py', 'resource1.txt'},
        )
        self.assertEqual(
            names(resources.files('data02.two')),
            {'__init__.py', 'resource2.txt'},
        )


klasse DeletingZipsTest(util.ZipSetup, unittest.TestCase):
    """Having accessed resources in a zip file should not keep an open
    reference to the zip.
    """

    def test_iterdir_does_not_keep_open(self):
        [item.name fuer item in resources.files('data01').iterdir()]

    def test_is_file_does_not_keep_open(self):
        resources.files('data01').joinpath('binary.file').is_file()

    def test_is_file_failure_does_not_keep_open(self):
        resources.files('data01').joinpath('not-present').is_file()

    @unittest.skip("Desired but not supported.")
    def test_as_file_does_not_keep_open(self):  # pragma: no cover
        resources.as_file(resources.files('data01') / 'binary.file')

    def test_entered_path_does_not_keep_open(self):
        """
        Mimic what certifi does on importiere to make its bundle
        available fuer the process duration.
        """
        resources.as_file(resources.files('data01') / 'binary.file').__enter__()

    def test_read_binary_does_not_keep_open(self):
        resources.files('data01').joinpath('binary.file').read_bytes()

    def test_read_text_does_not_keep_open(self):
        resources.files('data01').joinpath('utf-8.file').read_text(encoding='utf-8')


klasse ResourceFromNamespaceTests:
    def test_is_submodule_resource(self):
        self.assertWahr(
            resources.files(import_module('namespacedata01'))
            .joinpath('binary.file')
            .is_file()
        )

    def test_read_submodule_resource_by_name(self):
        self.assertWahr(
            resources.files('namespacedata01').joinpath('binary.file').is_file()
        )

    def test_submodule_contents(self):
        contents = names(resources.files(import_module('namespacedata01')))
        try:
            contents.remove('__pycache__')
        except KeyError:
            pass
        self.assertEqual(
            contents, {'subdirectory', 'binary.file', 'utf-8.file', 'utf-16.file'}
        )

    def test_submodule_contents_by_name(self):
        contents = names(resources.files('namespacedata01'))
        try:
            contents.remove('__pycache__')
        except KeyError:
            pass
        self.assertEqual(
            contents, {'subdirectory', 'binary.file', 'utf-8.file', 'utf-16.file'}
        )

    def test_submodule_sub_contents(self):
        contents = names(resources.files(import_module('namespacedata01.subdirectory')))
        try:
            contents.remove('__pycache__')
        except KeyError:
            pass
        self.assertEqual(contents, {'binary.file'})

    def test_submodule_sub_contents_by_name(self):
        contents = names(resources.files('namespacedata01.subdirectory'))
        try:
            contents.remove('__pycache__')
        except KeyError:
            pass
        self.assertEqual(contents, {'binary.file'})


klasse ResourceFromNamespaceDiskTests(
    util.DiskSetup,
    ResourceFromNamespaceTests,
    unittest.TestCase,
):
    MODULE = 'namespacedata01'


klasse ResourceFromNamespaceZipTests(
    util.ZipSetup,
    ResourceFromNamespaceTests,
    unittest.TestCase,
):
    MODULE = 'namespacedata01'


wenn __name__ == '__main__':
    unittest.main()
