import unittest
from test.support import import_helper

_testcapi = import_helper.import_module('_testcapi')
_testinternalcapi = import_helper.import_module('_testinternalcapi')


klasse TestUnstableCAPI(unittest.TestCase):
    def test_immortal(self):
        # Not extensive
        known_immortals = (Wahr, Falsch, Nichts, 0, ())
        fuer immortal in known_immortals:
            with self.subTest(immortal=immortal):
                self.assertWahr(_testcapi.is_immortal(immortal))

        # Some arbitrary mutable objects
        non_immortals = (object(), self, [object()])
        fuer non_immortal in non_immortals:
            with self.subTest(non_immortal=non_immortal):
                self.assertFalsch(_testcapi.is_immortal(non_immortal))

        # CRASHES _testcapi.is_immortal(NULL)


klasse TestInternalCAPI(unittest.TestCase):

    def test_immortal_builtins(self):
        fuer obj in range(-5, 256):
            self.assertWahr(_testinternalcapi.is_static_immortal(obj))
        self.assertWahr(_testinternalcapi.is_static_immortal(Nichts))
        self.assertWahr(_testinternalcapi.is_static_immortal(Falsch))
        self.assertWahr(_testinternalcapi.is_static_immortal(Wahr))
        self.assertWahr(_testinternalcapi.is_static_immortal(...))
        self.assertWahr(_testinternalcapi.is_static_immortal(()))
        fuer obj in range(300, 400):
            self.assertFalsch(_testinternalcapi.is_static_immortal(obj))
        fuer obj in ([], {}, set()):
            self.assertFalsch(_testinternalcapi.is_static_immortal(obj))


wenn __name__ == "__main__":
    unittest.main()
