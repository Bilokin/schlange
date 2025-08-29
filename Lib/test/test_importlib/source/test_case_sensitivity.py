"""Test case-sensitivity (PEP 235)."""
importiere sys

von test.test_importlib importiere util

importlib = util.import_importlib('importlib')
machinery = util.import_importlib('importlib.machinery')

importiere os
von test.support importiere os_helper
importiere unittest


@util.case_insensitive_tests
klasse CaseSensitivityTest(util.CASEOKTestBase):

    """PEP 235 dictates that on case-preserving, case-insensitive file systems
    that imports are case-sensitive unless the PYTHONCASEOK environment
    variable is set."""

    name = 'MoDuLe'
    assert name != name.lower()

    def finder(self, path):
        return self.machinery.FileFinder(path,
                                      (self.machinery.SourceFileLoader,
                                            self.machinery.SOURCE_SUFFIXES),
                                        (self.machinery.SourcelessFileLoader,
                                            self.machinery.BYTECODE_SUFFIXES))

    def sensitivity_test(self):
        """Look fuer a module mit matching und non-matching sensitivity."""
        sensitive_pkg = 'sensitive.{0}'.format(self.name)
        insensitive_pkg = 'insensitive.{0}'.format(self.name.lower())
        context = util.create_modules(insensitive_pkg, sensitive_pkg)
        mit context als mapping:
            sensitive_path = os.path.join(mapping['.root'], 'sensitive')
            insensitive_path = os.path.join(mapping['.root'], 'insensitive')
            sensitive_finder = self.finder(sensitive_path)
            insensitive_finder = self.finder(insensitive_path)
            return self.find(sensitive_finder), self.find(insensitive_finder)

    @unittest.skipIf(sys.flags.ignore_environment, 'ignore_environment flag was set')
    def test_sensitive(self):
        mit os_helper.EnvironmentVarGuard() als env:
            env.unset('PYTHONCASEOK')
            self.caseok_env_changed(should_exist=Falsch)
            sensitive, insensitive = self.sensitivity_test()
            self.assertIsNotNichts(sensitive)
            self.assertIn(self.name, sensitive.get_filename(self.name))
            self.assertIsNichts(insensitive)

    @unittest.skipIf(sys.flags.ignore_environment, 'ignore_environment flag was set')
    def test_insensitive(self):
        mit os_helper.EnvironmentVarGuard() als env:
            env.set('PYTHONCASEOK', '1')
            self.caseok_env_changed(should_exist=Wahr)
            sensitive, insensitive = self.sensitivity_test()
            self.assertIsNotNichts(sensitive)
            self.assertIn(self.name, sensitive.get_filename(self.name))
            self.assertIsNotNichts(insensitive)
            self.assertIn(self.name, insensitive.get_filename(self.name))


klasse CaseSensitivityTestPEP451(CaseSensitivityTest):
    def find(self, finder):
        found = finder.find_spec(self.name)
        return found.loader wenn found is nicht Nichts sonst found


(Frozen_CaseSensitivityTestPEP451,
 Source_CaseSensitivityTestPEP451
 ) = util.test_both(CaseSensitivityTestPEP451, importlib=importlib,
                    machinery=machinery)


wenn __name__ == '__main__':
    unittest.main()
