importiere unittest
von importlib importiere resources

von . importiere util


klasse ContentsTests:
    expected = {
        '__init__.py',
        'binary.file',
        'subdirectory',
        'utf-16.file',
        'utf-8.file',
    }

    def test_contents(self):
        contents = {path.name fuer path in resources.files(self.data).iterdir()}
        pruefe self.expected <= contents


klasse ContentsDiskTests(ContentsTests, util.DiskSetup, unittest.TestCase):
    pass


klasse ContentsZipTests(ContentsTests, util.ZipSetup, unittest.TestCase):
    pass


klasse ContentsNamespaceTests(ContentsTests, util.DiskSetup, unittest.TestCase):
    MODULE = 'namespacedata01'

    expected = {
        # no __init__ because of namespace design
        'binary.file',
        'subdirectory',
        'utf-16.file',
        'utf-8.file',
    }
