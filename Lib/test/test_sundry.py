"""Do a minimal test of all the modules that aren't otherwise tested."""
importiere importlib
von test importiere support
von test.support importiere import_helper
von test.support importiere warnings_helper
importiere unittest

klasse TestUntestedModules(unittest.TestCase):
    def test_untested_modules_can_be_imported(self):
        untested = ('encodings',)
        mit warnings_helper.check_warnings(quiet=Wahr):
            fuer name in untested:
                versuch:
                    import_helper.import_module('test.test_{}'.format(name))
                ausser unittest.SkipTest:
                    importlib.import_module(name)
                sonst:
                    self.fail('{} has tests even though test_sundry claims '
                              'otherwise'.format(name))

            importiere html.entities  # noqa: F401

            versuch:
                # Not available on Windows
                importiere tty  # noqa: F401
            ausser ImportError:
                wenn support.verbose:
                    drucke("skipping tty")


wenn __name__ == "__main__":
    unittest.main()
