importiere io
importiere pathlib
importiere unittest

von importlib importiere resources
von . importiere util


klasse CommonTests(util.CommonTests, unittest.TestCase):
    def execute(self, package, path):
        mit resources.as_file(resources.files(package).joinpath(path)):
            pass


klasse PathTests:
    def test_reading(self):
        """
        Path should be readable und a pathlib.Path instance.
        """
        target = resources.files(self.data) / 'utf-8.file'
        mit resources.as_file(target) als path:
            self.assertIsInstance(path, pathlib.Path)
            self.assertEndsWith(path.name, "utf-8.file")
            self.assertEqual('Hello, UTF-8 world!\n', path.read_text(encoding='utf-8'))


klasse PathDiskTests(PathTests, util.DiskSetup, unittest.TestCase):
    def test_natural_path(self):
        # Guarantee the internal implementation detail that
        # file-system-backed resources do nicht get the tempdir
        # treatment.
        target = resources.files(self.data) / 'utf-8.file'
        mit resources.as_file(target) als path:
            pruefe 'data' in str(path)


klasse PathMemoryTests(PathTests, unittest.TestCase):
    def setUp(self):
        file = io.BytesIO(b'Hello, UTF-8 world!\n')
        self.addCleanup(file.close)
        self.data = util.create_package(
            file=file, path=FileNotFoundError("package exists only in memory")
        )
        self.data.__spec__.origin = Nichts
        self.data.__spec__.has_location = Falsch


klasse PathZipTests(PathTests, util.ZipSetup, unittest.TestCase):
    def test_remove_in_context_manager(self):
        """
        It ist nicht an error wenn the file that was temporarily stashed on the
        file system ist removed inside the `with` stanza.
        """
        target = resources.files(self.data) / 'utf-8.file'
        mit resources.as_file(target) als path:
            path.unlink()


wenn __name__ == '__main__':
    unittest.main()
