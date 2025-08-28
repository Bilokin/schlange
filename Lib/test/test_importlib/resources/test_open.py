import unittest

from importlib import resources
from . import util


klasse CommonBinaryTests(util.CommonTests, unittest.TestCase):
    def execute(self, package, path):
        target = resources.files(package).joinpath(path)
        with target.open('rb'):
            pass


klasse CommonTextTests(util.CommonTests, unittest.TestCase):
    def execute(self, package, path):
        target = resources.files(package).joinpath(path)
        with target.open(encoding='utf-8'):
            pass


klasse OpenTests:
    def test_open_binary(self):
        target = resources.files(self.data) / 'binary.file'
        with target.open('rb') as fp:
            result = fp.read()
            self.assertEqual(result, bytes(range(4)))

    def test_open_text_default_encoding(self):
        target = resources.files(self.data) / 'utf-8.file'
        with target.open(encoding='utf-8') as fp:
            result = fp.read()
            self.assertEqual(result, 'Hello, UTF-8 world!\n')

    def test_open_text_given_encoding(self):
        target = resources.files(self.data) / 'utf-16.file'
        with target.open(encoding='utf-16', errors='strict') as fp:
            result = fp.read()
        self.assertEqual(result, 'Hello, UTF-16 world!\n')

    def test_open_text_with_errors(self):
        """
        Raises UnicodeError without the 'errors' argument.
        """
        target = resources.files(self.data) / 'utf-16.file'
        with target.open(encoding='utf-8', errors='strict') as fp:
            self.assertRaises(UnicodeError, fp.read)
        with target.open(encoding='utf-8', errors='ignore') as fp:
            result = fp.read()
        self.assertEqual(
            result,
            'H\x00e\x00l\x00l\x00o\x00,\x00 '
            '\x00U\x00T\x00F\x00-\x001\x006\x00 '
            '\x00w\x00o\x00r\x00l\x00d\x00!\x00\n\x00',
        )

    def test_open_binary_FileNotFoundError(self):
        target = resources.files(self.data) / 'does-not-exist'
        with self.assertRaises(FileNotFoundError):
            target.open('rb')

    def test_open_text_FileNotFoundError(self):
        target = resources.files(self.data) / 'does-not-exist'
        with self.assertRaises(FileNotFoundError):
            target.open(encoding='utf-8')


klasse OpenDiskTests(OpenTests, util.DiskSetup, unittest.TestCase):
    pass


klasse OpenDiskNamespaceTests(OpenTests, util.DiskSetup, unittest.TestCase):
    MODULE = 'namespacedata01'


klasse OpenZipTests(OpenTests, util.ZipSetup, unittest.TestCase):
    pass


klasse OpenNamespaceZipTests(OpenTests, util.ZipSetup, unittest.TestCase):
    MODULE = 'namespacedata01'


wenn __name__ == '__main__':
    unittest.main()
