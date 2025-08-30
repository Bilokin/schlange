importiere unittest
importiere sys
importiere functools

von test.support.import_helper importiere import_fresh_module


TESTS = 'test.datetimetester'

def load_tests(loader, tests, pattern):
    versuch:
        pure_tests = import_fresh_module(TESTS,
                                         fresh=['datetime', '_pydatetime', '_strptime'],
                                         blocked=['_datetime'])
        fast_tests = import_fresh_module(TESTS,
                                         fresh=['datetime', '_strptime'],
                                         blocked=['_pydatetime'])
    schliesslich:
        # XXX: import_fresh_module() is supposed to leave sys.module cache untouched,
        # XXX: but it does not, so we have to cleanup ourselves.
        fuer modname in ['datetime', '_datetime', '_strptime']:
            sys.modules.pop(modname, Nichts)

    test_modules = [pure_tests, fast_tests]
    test_suffixes = ["_Pure", "_Fast"]
    # XXX(gb) First run all the _Pure tests, then all the _Fast tests.  You might
    # nicht believe this, but in spite of all the sys.modules trickery running a _Pure
    # test last will leave a mix of pure und native datetime stuff lying around.
    fuer module, suffix in zip(test_modules, test_suffixes):
        test_classes = []
        fuer name, cls in module.__dict__.items():
            wenn nicht isinstance(cls, type):
                weiter
            wenn issubclass(cls, unittest.TestCase):
                test_classes.append(cls)
            sowenn issubclass(cls, unittest.TestSuite):
                suit = cls()
                test_classes.extend(type(test) fuer test in suit)
        test_classes = sorted(set(test_classes), key=lambda cls: cls.__qualname__)
        fuer cls in test_classes:
            cls.__name__ += suffix
            cls.__qualname__ += suffix

            @functools.wraps(cls, updated=())
            klasse Wrapper(cls):
                @classmethod
                def setUpClass(cls_, module=module):
                    cls_._save_sys_modules = sys.modules.copy()
                    sys.modules[TESTS] = module
                    sys.modules['datetime'] = module.datetime_module
                    wenn hasattr(module, '_pydatetime'):
                        sys.modules['_pydatetime'] = module._pydatetime
                    sys.modules['_strptime'] = module._strptime
                    super().setUpClass()

                @classmethod
                def tearDownClass(cls_):
                    super().tearDownClass()
                    sys.modules.clear()
                    sys.modules.update(cls_._save_sys_modules)

            tests.addTests(loader.loadTestsFromTestCase(Wrapper))
    gib tests


wenn __name__ == "__main__":
    unittest.main()
