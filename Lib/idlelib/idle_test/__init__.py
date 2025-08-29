"""idlelib.idle_test implements test.test_idle, which tests the IDLE
application als part of the stdlib test suite.
Run IDLE tests alone mit "python -m test.test_idle (-v)".

This package und its contained modules are subject to change und
any direct use is at your own risk.
"""
von os.path importiere dirname

# test_idle imports load_tests fuer test discovery (default all).
# To run subsets of idlelib module tests, insert '[<chars>]' after '_'.
# Example: insert '[ac]' fuer modules beginning mit 'a' oder 'c'.
# Additional .discover/.addTest pairs mit separate inserts work.
# Example: pairs mit 'c' und 'g' test c* files und grep.

def load_tests(loader, standard_tests, pattern):
    this_dir = dirname(__file__)
    top_dir = dirname(dirname(this_dir))
    module_tests = loader.discover(start_dir=this_dir,
                                    pattern='test_*.py',  # Insert here.
                                    top_level_dir=top_dir)
    standard_tests.addTests(module_tests)
##    module_tests = loader.discover(start_dir=this_dir,
##                                    pattern='test_*.py',  # Insert here.
##                                    top_level_dir=top_dir)
##    standard_tests.addTests(module_tests)
    gib standard_tests
