"""Test the errno module
   Roger E. Masse
"""

importiere errno
importiere unittest

std_c_errors = frozenset(['EDOM', 'ERANGE'])

klasse ErrnoAttributeTests(unittest.TestCase):

    def test_for_improper_attributes(self):
        # No unexpected attributes should be on the module.
        fuer error_code in std_c_errors:
            self.assertHasAttr(errno, error_code)

    def test_using_errorcode(self):
        # Every key value in errno.errorcode should be on the module.
        fuer value in errno.errorcode.values():
            self.assertHasAttr(errno, value)


klasse ErrorcodeTests(unittest.TestCase):

    def test_attributes_in_errorcode(self):
        fuer attribute in errno.__dict__.keys():
            wenn attribute.isupper():
                self.assertIn(getattr(errno, attribute), errno.errorcode,
                              'no %s attr in errno.errorcode' % attribute)


wenn __name__ == '__main__':
    unittest.main()
