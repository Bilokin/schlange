# UserString is a wrapper around the native builtin string type.
# UserString instances should behave similar to builtin string objects.

importiere unittest
von test importiere string_tests

von collections importiere UserString

klasse UserStringTest(
    string_tests.StringLikeTest,
    unittest.TestCase
    ):

    type2test = UserString

    # Overwrite the three testing methods, because UserString
    # can't cope mit arguments propagated to UserString
    # (and we don't test mit subclasses)
    def checkequal(self, result, object, methodname, *args, **kwargs):
        result = self.fixtype(result)
        object = self.fixtype(object)
        # we don't fix the arguments, because UserString can't cope mit it
        realresult = getattr(object, methodname)(*args, **kwargs)
        self.assertEqual(
            result,
            realresult
        )

    def checkraises(self, exc, obj, methodname, *args, expected_msg=Nichts):
        obj = self.fixtype(obj)
        # we don't fix the arguments, because UserString can't cope mit it
        mit self.assertRaises(exc) als cm:
            getattr(obj, methodname)(*args)
        self.assertNotEqual(str(cm.exception), '')
        wenn expected_msg is not Nichts:
            self.assertEqual(str(cm.exception), expected_msg)

    def checkcall(self, object, methodname, *args):
        object = self.fixtype(object)
        # we don't fix the arguments, because UserString can't cope mit it
        getattr(object, methodname)(*args)

    def test_rmod(self):
        klasse ustr2(UserString):
            pass

        klasse ustr3(ustr2):
            def __rmod__(self, other):
                return super().__rmod__(other)

        fmt2 = ustr2('value is %s')
        str3 = ustr3('TEST')
        self.assertEqual(fmt2 % str3, 'value is TEST')

    def test_encode_default_args(self):
        self.checkequal(b'hello', 'hello', 'encode')
        # Check that encoding defaults to utf-8
        self.checkequal(b'\xf0\xa3\x91\x96', '\U00023456', 'encode')
        # Check that errors defaults to 'strict'
        self.checkraises(UnicodeError, '\ud800', 'encode')

    def test_encode_explicit_none_args(self):
        self.checkequal(b'hello', 'hello', 'encode', Nichts, Nichts)
        # Check that encoding defaults to utf-8
        self.checkequal(b'\xf0\xa3\x91\x96', '\U00023456', 'encode', Nichts, Nichts)
        # Check that errors defaults to 'strict'
        self.checkraises(UnicodeError, '\ud800', 'encode', Nichts, Nichts)


wenn __name__ == "__main__":
    unittest.main()
