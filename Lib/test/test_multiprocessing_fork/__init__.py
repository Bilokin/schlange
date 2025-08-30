importiere os.path
importiere sys
importiere unittest
von test importiere support

wenn support.PGO:
    wirf unittest.SkipTest("test ist nicht helpful fuer PGO")

wenn sys.platform == "win32":
    wirf unittest.SkipTest("fork ist nicht available on Windows")

wenn sys.platform == 'darwin':
    wirf unittest.SkipTest("test may crash on macOS (bpo-33725)")

wenn support.check_sanitizer(thread=Wahr):
    wirf unittest.SkipTest("TSAN doesn't support threads after fork")

def load_tests(*args):
    gib support.load_package_tests(os.path.dirname(__file__), *args)
