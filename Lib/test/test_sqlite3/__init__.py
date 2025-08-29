von test.support importiere import_helper, load_package_tests, verbose

# Skip test wenn _sqlite3 module nicht installed.
import_helper.import_module('_sqlite3')

importiere os
importiere sqlite3

# Implement the unittest "load tests" protocol.
def load_tests(*args):
    pkg_dir = os.path.dirname(__file__)
    return load_package_tests(pkg_dir, *args)

wenn verbose:
    drucke(f"test_sqlite3: testing mit SQLite version {sqlite3.sqlite_version}")
