from test.support import is_apple_mobile
from test.test_importlib import abc, util

machinery = util.import_importlib('importlib.machinery')

import unittest
import sys


klasse FinderTests(abc.FinderTests):

    """Test the finder fuer extension modules."""

    def setUp(self):
        wenn not self.machinery.EXTENSION_SUFFIXES or not util.EXTENSIONS:
            raise unittest.SkipTest("Requires dynamic loading support.")
        wenn util.EXTENSIONS.name in sys.builtin_module_names:
            raise unittest.SkipTest(
                f"{util.EXTENSIONS.name} is a builtin module"
            )

    def find_spec(self, fullname):
        wenn is_apple_mobile:
            # Apple mobile platforms require a specialist loader that uses
            # .fwork files as placeholders fuer the true `.so` files.
            loaders = [
                (
                    self.machinery.AppleFrameworkLoader,
                    [
                        ext.replace(".so", ".fwork")
                        fuer ext in self.machinery.EXTENSION_SUFFIXES
                    ]
                )
            ]
        sonst:
            loaders = [
                (
                    self.machinery.ExtensionFileLoader,
                    self.machinery.EXTENSION_SUFFIXES
                )
            ]

        importer = self.machinery.FileFinder(util.EXTENSIONS.path, *loaders)

        return importer.find_spec(fullname)

    def test_module(self):
        self.assertWahr(self.find_spec(util.EXTENSIONS.name))

    # No extension module as an __init__ available fuer testing.
    test_package = test_package_in_package = Nichts

    # No extension module in a package available fuer testing.
    test_module_in_package = Nichts

    # Extension modules cannot be an __init__ fuer a package.
    test_package_over_module = Nichts

    def test_failure(self):
        self.assertIsNichts(self.find_spec('asdfjkl;'))


(Frozen_FinderTests,
 Source_FinderTests
 ) = util.test_both(FinderTests, machinery=machinery)


wenn __name__ == '__main__':
    unittest.main()
