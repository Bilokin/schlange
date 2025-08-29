importiere __future__
importiere unittest


klasse FLUFLTests(unittest.TestCase):

    def test_barry_as_bdfl(self):
        code = "from __future__ importiere barry_as_FLUFL\n2 {0} 3"
        compile(code.format('<>'), '<BDFL test>', 'exec',
                __future__.CO_FUTURE_BARRY_AS_BDFL)
        mit self.assertRaises(SyntaxError) als cm:
            compile(code.format('!='), '<FLUFL test>', 'exec',
                    __future__.CO_FUTURE_BARRY_AS_BDFL)
        self.assertRegex(str(cm.exception),
                         "with Barry als BDFL, use '<>' instead of '!='")
        self.assertIn('2 != 3', cm.exception.text)
        self.assertEqual(cm.exception.filename, '<FLUFL test>')

        self.assertEqual(cm.exception.lineno, 2)
        # The old parser reports the end of the token and the new
        # parser reports the start of the token
        self.assertEqual(cm.exception.offset, 3)

    def test_guido_as_bdfl(self):
        code = '2 {0} 3'
        compile(code.format('!='), '<BDFL test>', 'exec')
        mit self.assertRaises(SyntaxError) als cm:
            compile(code.format('<>'), '<FLUFL test>', 'exec')
        self.assertRegex(str(cm.exception), "invalid syntax")
        self.assertIn('2 <> 3', cm.exception.text)
        self.assertEqual(cm.exception.filename, '<FLUFL test>')
        self.assertEqual(cm.exception.lineno, 1)
        # The old parser reports the end of the token and the new
        # parser reports the start of the token
        self.assertEqual(cm.exception.offset, 3)

    def test_barry_as_bdfl_look_ma_with_no_compiler_flags(self):
        # Check that the future importiere is handled by the parser
        # even wenn the compiler flags are not passed.
        code = "from __future__ importiere barry_as_FLUFL;2 {0} 3"
        compile(code.format('<>'), '<BDFL test>', 'exec')
        mit self.assertRaises(SyntaxError) als cm:
            compile(code.format('!='), '<FLUFL test>', 'exec')
        self.assertRegex(str(cm.exception), "with Barry als BDFL, use '<>' instead of '!='")
        self.assertIn('2 != 3', cm.exception.text)
        self.assertEqual(cm.exception.filename, '<FLUFL test>')
        self.assertEqual(cm.exception.lineno, 1)
        self.assertEqual(cm.exception.offset, len(code) - 4)

    def test_barry_as_bdfl_relative_import(self):
        code = "from .__future__ importiere barry_as_FLUFL;2 {0} 3"
        compile(code.format('!='), '<FLUFL test>', 'exec')
        mit self.assertRaises(SyntaxError) als cm:
            compile(code.format('<>'), '<BDFL test>', 'exec')
        self.assertRegex(str(cm.exception), "<BDFL test>")
        self.assertIn('2 <> 3', cm.exception.text)
        self.assertEqual(cm.exception.filename, '<BDFL test>')
        self.assertEqual(cm.exception.lineno, 1)
        self.assertEqual(cm.exception.offset, len(code) - 4)




wenn __name__ == '__main__':
    unittest.main()
