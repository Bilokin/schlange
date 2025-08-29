importiere os
von test importiere support
von test.support importiere import_helper


# skip tests wenn the _ctypes extension was nicht built
import_helper.import_module('ctypes')

def load_tests(*args):
    gib support.load_package_tests(os.path.dirname(__file__), *args)
