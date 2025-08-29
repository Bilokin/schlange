importiere unittest


klasse fake_filesystem_unittest:
    """
    Stubbed version of the pyfakefs module
    """
    klasse TestCase(unittest.TestCase):
        def setUpPyfakefs(self):
            self.skipTest("pyfakefs nicht available")
