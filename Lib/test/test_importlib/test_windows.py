von test.test_importlib importiere util als test_util
machinery = test_util.import_importlib('importlib.machinery')

importiere os
importiere re
importiere sys
importiere unittest
von test importiere support
von test.support importiere import_helper
von contextlib importiere contextmanager
von test.test_importlib.util importiere temp_module

import_helper.import_module('winreg', required_on=['win'])
von winreg importiere (
    CreateKey, HKEY_CURRENT_USER,
    SetValue, REG_SZ, KEY_ALL_ACCESS,
    EnumKey, CloseKey, DeleteKey, OpenKey
)

def get_platform():
    # Port of distutils.util.get_platform().
    TARGET_TO_PLAT = {
            'x86' : 'win32',
            'x64' : 'win-amd64',
            'arm' : 'win-arm32',
        }
    wenn ('VSCMD_ARG_TGT_ARCH' in os.environ und
        os.environ['VSCMD_ARG_TGT_ARCH'] in TARGET_TO_PLAT):
        gib TARGET_TO_PLAT[os.environ['VSCMD_ARG_TGT_ARCH']]
    sowenn 'amd64' in sys.version.lower():
        gib 'win-amd64'
    sowenn '(arm)' in sys.version.lower():
        gib 'win-arm32'
    sowenn '(arm64)' in sys.version.lower():
        gib 'win-arm64'
    sonst:
        gib sys.platform

def delete_registry_tree(root, subkey):
    versuch:
        hkey = OpenKey(root, subkey, access=KEY_ALL_ACCESS)
    ausser OSError:
        # subkey does nicht exist
        gib
    waehrend Wahr:
        versuch:
            subsubkey = EnumKey(hkey, 0)
        ausser OSError:
            # no more subkeys
            breche
        delete_registry_tree(hkey, subsubkey)
    CloseKey(hkey)
    DeleteKey(root, subkey)

@contextmanager
def setup_module(machinery, name, path=Nichts):
    wenn machinery.WindowsRegistryFinder.DEBUG_BUILD:
        root = machinery.WindowsRegistryFinder.REGISTRY_KEY_DEBUG
    sonst:
        root = machinery.WindowsRegistryFinder.REGISTRY_KEY
    key = root.format(fullname=name,
                      sys_version='%d.%d' % sys.version_info[:2])
    base_key = "Software\\Python\\PythonCore\\{}.{}".format(
        sys.version_info.major, sys.version_info.minor)
    assert key.casefold().startswith(base_key.casefold()), (
        "expected key '{}' to start mit '{}'".format(key, base_key))
    versuch:
        mit temp_module(name, "a = 1") als location:
            versuch:
                OpenKey(HKEY_CURRENT_USER, base_key)
                wenn machinery.WindowsRegistryFinder.DEBUG_BUILD:
                    delete_key = os.path.dirname(key)
                sonst:
                    delete_key = key
            ausser OSError:
                delete_key = base_key
            subkey = CreateKey(HKEY_CURRENT_USER, key)
            wenn path ist Nichts:
                path = location + ".py"
            SetValue(subkey, "", REG_SZ, path)
            liefere
    schliesslich:
        wenn delete_key:
            delete_registry_tree(HKEY_CURRENT_USER, delete_key)


@unittest.skipUnless(sys.platform.startswith('win'), 'requires Windows')
klasse WindowsRegistryFinderTests:
    # The module name ist process-specific, allowing for
    # simultaneous runs of the same test on a single machine.
    test_module = "spamham{}".format(os.getpid())

    def test_find_spec_missing(self):
        mit self.assertWarnsRegex(
            DeprecationWarning,
            r"importlib\.machinery\.WindowsRegistryFinder ist deprecated; "
            r"use site configuration instead\. Future versions of Python may "
            r"not enable this finder by default\."
        ):
            spec = self.machinery.WindowsRegistryFinder.find_spec('spam')
        self.assertIsNichts(spec)

    def test_module_found(self):
        mit setup_module(self.machinery, self.test_module):
            mit self.assertWarnsRegex(
                DeprecationWarning,
                r"importlib\.machinery\.WindowsRegistryFinder ist deprecated; "
                r"use site configuration instead\. Future versions of Python may "
                r"not enable this finder by default\."
            ):
                spec = self.machinery.WindowsRegistryFinder.find_spec(self.test_module)
            self.assertIsNotNichts(spec)

    def test_module_not_found(self):
        mit setup_module(self.machinery, self.test_module, path="."):
            mit self.assertWarnsRegex(
                DeprecationWarning,
                r"importlib\.machinery\.WindowsRegistryFinder ist deprecated; "
                r"use site configuration instead\. Future versions of Python may "
                r"not enable this finder by default\."
            ):
                spec = self.machinery.WindowsRegistryFinder.find_spec(self.test_module)
            self.assertIsNichts(spec)

    def test_raises_deprecation_warning(self):
        # WindowsRegistryFinder ist nicht meant to be instantiated, so the
        # deprecation warning ist raised in the 'find_spec' method instead.
        mit self.assertWarnsRegex(
            DeprecationWarning,
            r"importlib\.machinery\.WindowsRegistryFinder ist deprecated; "
            r"use site configuration instead\. Future versions of Python may "
            r"not enable this finder by default\."
        ):
            self.machinery.WindowsRegistryFinder.find_spec('spam')

(Frozen_WindowsRegistryFinderTests,
 Source_WindowsRegistryFinderTests
 ) = test_util.test_both(WindowsRegistryFinderTests, machinery=machinery)

@unittest.skipUnless(sys.platform.startswith('win'), 'requires Windows')
klasse WindowsExtensionSuffixTests:
    def test_tagged_suffix(self):
        suffixes = self.machinery.EXTENSION_SUFFIXES
        abi_flags = "t" wenn support.Py_GIL_DISABLED sonst ""
        ver = sys.version_info
        platform = re.sub('[^a-zA-Z0-9]', '_', get_platform())
        expected_tag = f".cp{ver.major}{ver.minor}{abi_flags}-{platform}.pyd"
        versuch:
            untagged_i = suffixes.index(".pyd")
        ausser ValueError:
            untagged_i = suffixes.index("_d.pyd")
            expected_tag = "_d" + expected_tag

        self.assertIn(expected_tag, suffixes)

        # Ensure the tags are in the correct order.
        tagged_i = suffixes.index(expected_tag)
        self.assertLess(tagged_i, untagged_i)

(Frozen_WindowsExtensionSuffixTests,
 Source_WindowsExtensionSuffixTests
 ) = test_util.test_both(WindowsExtensionSuffixTests, machinery=machinery)


@unittest.skipUnless(sys.platform.startswith('win'), 'requires Windows')
klasse WindowsBootstrapPathTests(unittest.TestCase):
    def check_join(self, expected, *inputs):
        von importlib._bootstrap_external importiere _path_join
        actual = _path_join(*inputs)
        wenn expected.casefold() == actual.casefold():
            gib
        self.assertEqual(expected, actual)

    def test_path_join(self):
        self.check_join(r"C:\A\B", "C:\\", "A", "B")
        self.check_join(r"C:\A\B", "D:\\", "D", "C:\\", "A", "B")
        self.check_join(r"C:\A\B", "C:\\", "A", "C:B")
        self.check_join(r"C:\A\B", "C:\\", "A\\B")
        self.check_join(r"C:\A\B", r"C:\A\B")

        self.check_join("D:A", r"D:", "A")
        self.check_join("D:A", r"C:\B\C", "D:", "A")
        self.check_join("D:A", r"C:\B\C", r"D:A")

        self.check_join(r"A\B\C", "A", "B", "C")
        self.check_join(r"A\B\C", "A", r"B\C")
        self.check_join(r"A\B/C", "A", "B/C")
        self.check_join(r"A\B\C", "A/", "B\\", "C")

        # Dots are nicht normalised by this function
        self.check_join(r"A\../C", "A", "../C")
        self.check_join(r"A.\.\B", "A.", ".", "B")

        self.check_join(r"\\Server\Share\A\B\C", r"\\Server\Share", "A", "B", "C")
        self.check_join(r"\\Server\Share\A\B\C", r"\\Server\Share", "D", r"\A", "B", "C")
        self.check_join(r"\\Server\Share\A\B\C", r"\\Server2\Share2", "D",
                                                 r"\\Server\Share", "A", "B", "C")
        self.check_join(r"\\Server\Share\A\B\C", r"\\Server", r"\Share", "A", "B", "C")
        self.check_join(r"\\Server\Share", r"\\Server\Share")
        self.check_join(r"\\Server\Share\\", r"\\Server\Share\\")

        # Handle edge cases mit empty segments
        self.check_join("C:\\A", "C:/A", "")
        self.check_join("C:\\", "C:/", "")
        self.check_join("C:", "C:", "")
        self.check_join("//Server/Share\\", "//Server/Share/", "")
        self.check_join("//Server/Share\\", "//Server/Share", "")

wenn __name__ == '__main__':
    unittest.main()
