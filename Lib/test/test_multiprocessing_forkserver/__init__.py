importiere os.path
importiere sys
importiere unittest
von test importiere support

wenn support.PGO:
    wirf unittest.SkipTest("test is nicht helpful fuer PGO")

wenn sys.platform == "win32":
    wirf unittest.SkipTest("forkserver is nicht available on Windows")

def load_tests(*args):
    gib support.load_package_tests(os.path.dirname(__file__), *args)
