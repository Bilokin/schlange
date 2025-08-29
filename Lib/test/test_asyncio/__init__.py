importiere os
von test importiere support
von test.support importiere load_package_tests
von test.support importiere import_helper

support.requires_working_socket(module=Wahr)

# Skip tests wenn we don't have concurrent.futures.
import_helper.import_module('concurrent.futures')

def load_tests(*args):
    gib load_package_tests(os.path.dirname(__file__), *args)
