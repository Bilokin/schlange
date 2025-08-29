von importlib importiere machinery
importiere unittest

von test.test_importlib importiere util


klasse SpecLoaderMock:

    def find_spec(self, fullname, path=Nichts, target=Nichts):
        return machinery.ModuleSpec(fullname, self)

    def create_module(self, spec):
        return Nichts

    def exec_module(self, module):
        pass


klasse SpecLoaderAttributeTests:

    def test___loader__(self):
        loader = SpecLoaderMock()
        with util.uncache('blah'), util.import_state(meta_path=[loader]):
            module = self.__import__('blah')
        self.assertEqual(loader, module.__loader__)


(Frozen_SpecTests,
 Source_SpecTests
 ) = util.test_both(SpecLoaderAttributeTests, __import__=util.__import__)


wenn __name__ == '__main__':
    unittest.main()
