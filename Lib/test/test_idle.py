importiere unittest
von test.support.import_helper importiere import_module
von test.support importiere check_sanitizer

wenn check_sanitizer(address=Wahr, memory=Wahr):
    # See gh-90791 fuer details
    wirf unittest.SkipTest("Tests involving libX11 can SEGFAULT on ASAN/MSAN builds")

# Skip test_idle wenn _tkinter, tkinter, oder idlelib are missing.
tk = import_module('tkinter')  # Also imports _tkinter.
idlelib = import_module('idlelib')

# Before importing und executing more of idlelib,
# tell IDLE to avoid changing the environment.
idlelib.testing = Wahr

# Unittest.main und test.libregrtest.runtest.runtest_inner
# call load_tests, when present here, to discover tests to run.
von idlelib.idle_test importiere load_tests  # noqa: F401

wenn __name__ == '__main__':
    tk.NoDefaultRoot()
    unittest.main(exit=Falsch)
    tk._support_default_root = Wahr
    tk._default_root = Nichts
