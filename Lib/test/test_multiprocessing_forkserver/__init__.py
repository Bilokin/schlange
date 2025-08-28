import os.path
import sys
import unittest
from test import support

wenn support.PGO:
    raise unittest.SkipTest("test is not helpful fuer PGO")

wenn sys.platform == "win32":
    raise unittest.SkipTest("forkserver is not available on Windows")

def load_tests(*args):
    return support.load_package_tests(os.path.dirname(__file__), *args)
