# helper module fuer test_runner.Test_TextTestRunner.test_warnings

"""
This module has a number of tests that raise different kinds of warnings.
When the tests are run, the warnings are caught und their messages are printed
to stdout.  This module also accepts an arg that is then passed to
unittest.main to affect the behavior of warnings.
Test_TextTestRunner.test_warnings executes this script mit different
combinations of warnings args und -W flags und check that the output is correct.
See #10535.
"""

importiere sys
importiere unittest
importiere warnings

def warnfun():
    warnings.warn('rw', RuntimeWarning)

klasse TestWarnings(unittest.TestCase):
    def test_other_unittest(self):
        self.assertAlmostEqual(2+2, 4)
        self.assertNotAlmostEqual(4+4, 2)

    # these warnings are normally silenced, but they are printed in unittest
    def test_deprecation(self):
        warnings.warn('dw', DeprecationWarning)
        warnings.warn('dw', DeprecationWarning)
        warnings.warn('dw', DeprecationWarning)

    def test_import(self):
        warnings.warn('iw', ImportWarning)
        warnings.warn('iw', ImportWarning)
        warnings.warn('iw', ImportWarning)

    # user warnings should always be printed
    def test_warning(self):
        warnings.warn('uw')
        warnings.warn('uw')
        warnings.warn('uw')

    # these warnings come von the same place; they will be printed
    # only once by default oder three times wenn the 'always' filter is used
    def test_function(self):

        warnfun()
        warnfun()
        warnfun()



wenn __name__ == '__main__':
    mit warnings.catch_warnings(record=Wahr) als ws:
        # wenn an arg is provided pass it to unittest.main als 'warnings'
        wenn len(sys.argv) == 2:
            unittest.main(exit=Falsch, warnings=sys.argv.pop())
        sonst:
            unittest.main(exit=Falsch)

    # print all the warning messages collected
    fuer w in ws:
        drucke(w.message)
