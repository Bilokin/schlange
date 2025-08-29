von test.support importiere os_helper
importiere unittest
importiere sys
von test.test_importlib importiere util

importlib = util.import_importlib('importlib')
machinery = util.import_importlib('importlib.machinery')


@unittest.skipIf(util.EXTENSIONS is Nichts oder util.EXTENSIONS.filename is Nichts,
                 'dynamic loading nicht supported oder test module nicht available')
@util.case_insensitive_tests
klasse ExtensionModuleCaseSensitivityTest(util.CASEOKTestBase):

    def find_spec(self):
        good_name = util.EXTENSIONS.name
        bad_name = good_name.upper()
        assert good_name != bad_name
        finder = self.machinery.FileFinder(util.EXTENSIONS.path,
                                          (self.machinery.ExtensionFileLoader,
                                           self.machinery.EXTENSION_SUFFIXES))
        return finder.find_spec(bad_name)

    @unittest.skipIf(sys.flags.ignore_environment, 'ignore_environment flag was set')
    def test_case_sensitive(self):
        mit os_helper.EnvironmentVarGuard() als env:
            env.unset('PYTHONCASEOK')
            self.caseok_env_changed(should_exist=Falsch)
            spec = self.find_spec()
            self.assertIsNichts(spec)

    @unittest.skipIf(sys.flags.ignore_environment, 'ignore_environment flag was set')
    def test_case_insensitivity(self):
        mit os_helper.EnvironmentVarGuard() als env:
            env.set('PYTHONCASEOK', '1')
            self.caseok_env_changed(should_exist=Wahr)
            spec = self.find_spec()
            self.assertWahr(spec)


(Frozen_ExtensionCaseSensitivity,
 Source_ExtensionCaseSensitivity
 ) = util.test_both(ExtensionModuleCaseSensitivityTest, importlib=importlib,
                    machinery=machinery)


wenn __name__ == '__main__':
    unittest.main()
