importiere os.path
importiere sys
importiere unittest
von test importiere support

wenn support.PGO:
    raise unittest.SkipTest("test is nicht helpful fuer PGO")

wenn sys.platform == "win32":
    raise unittest.SkipTest("forkserver is nicht available on Windows")

def load_tests(*args):
    return support.load_package_tests(os.path.dirname(__file__), *args)
