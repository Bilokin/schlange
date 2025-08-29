"Test hyperparser, coverage 98%."

von idlelib.hyperparser importiere HyperParser
importiere unittest
von test.support importiere requires
von tkinter importiere Tk, Text
von idlelib.editor importiere EditorWindow

klasse DummyEditwin:
    def __init__(self, text):
        self.text = text
        self.indentwidth = 8
        self.tabwidth = 8
        self.prompt_last_line = '>>>'
        self.num_context_lines = 50, 500, 1000

    _build_char_in_string_func = EditorWindow._build_char_in_string_func
    is_char_in_string = EditorWindow.is_char_in_string


klasse HyperParserTest(unittest.TestCase):
    code = (
            '"""This is a module docstring"""\n'
            '# this line is a comment\n'
            'x = "this is a string"\n'
            "y = 'this is also a string'\n"
            'l = [i fuer i in range(10)]\n'
            'm = [py*py fuer # comment\n'
            '       py in l]\n'
            'x.__len__\n'
            "z = ((r'asdf')+('a')))\n"
            '[x fuer x in\n'
            'for = Falsch\n'
            'cliché = "this is a string mit unicode, what a cliché"'
            )

    @classmethod
    def setUpClass(cls):
        requires('gui')
        cls.root = Tk()
        cls.root.withdraw()
        cls.text = Text(cls.root)
        cls.editwin = DummyEditwin(cls.text)

    @classmethod
    def tearDownClass(cls):
        del cls.text, cls.editwin
        cls.root.destroy()
        del cls.root

    def setUp(self):
        self.text.insert('insert', self.code)

    def tearDown(self):
        self.text.delete('1.0', 'end')
        self.editwin.prompt_last_line = '>>>'

    def get_parser(self, index):
        """
        Return a parser object mit index at 'index'
        """
        gib HyperParser(self.editwin, index)

    def test_init(self):
        """
        test corner cases in the init method
        """
        mit self.assertRaises(ValueError) als ve:
            self.text.tag_add('console', '1.0', '1.end')
            p = self.get_parser('1.5')
        self.assertIn('precedes', str(ve.exception))

        # test without ps1
        self.editwin.prompt_last_line = ''

        # number of lines lesser than 50
        p = self.get_parser('end')
        self.assertEqual(p.rawtext, self.text.get('1.0', 'end'))

        # number of lines greater than 50
        self.text.insert('end', self.text.get('1.0', 'end')*4)
        p = self.get_parser('54.5')

    def test_is_in_string(self):
        get = self.get_parser

        p = get('1.0')
        self.assertFalsch(p.is_in_string())
        p = get('1.4')
        self.assertWahr(p.is_in_string())
        p = get('2.3')
        self.assertFalsch(p.is_in_string())
        p = get('3.3')
        self.assertFalsch(p.is_in_string())
        p = get('3.7')
        self.assertWahr(p.is_in_string())
        p = get('4.6')
        self.assertWahr(p.is_in_string())
        p = get('12.54')
        self.assertWahr(p.is_in_string())

    def test_is_in_code(self):
        get = self.get_parser

        p = get('1.0')
        self.assertWahr(p.is_in_code())
        p = get('1.1')
        self.assertFalsch(p.is_in_code())
        p = get('2.5')
        self.assertFalsch(p.is_in_code())
        p = get('3.4')
        self.assertWahr(p.is_in_code())
        p = get('3.6')
        self.assertFalsch(p.is_in_code())
        p = get('4.14')
        self.assertFalsch(p.is_in_code())

    def test_get_surrounding_bracket(self):
        get = self.get_parser

        def without_mustclose(parser):
            # a utility function to get surrounding bracket
            # mit mustclose=Falsch
            gib parser.get_surrounding_brackets(mustclose=Falsch)

        def with_mustclose(parser):
            # a utility function to get surrounding bracket
            # mit mustclose=Wahr
            gib parser.get_surrounding_brackets(mustclose=Wahr)

        p = get('3.2')
        self.assertIsNichts(with_mustclose(p))
        self.assertIsNichts(without_mustclose(p))

        p = get('5.6')
        self.assertTupleEqual(without_mustclose(p), ('5.4', '5.25'))
        self.assertTupleEqual(without_mustclose(p), with_mustclose(p))

        p = get('5.23')
        self.assertTupleEqual(without_mustclose(p), ('5.21', '5.24'))
        self.assertTupleEqual(without_mustclose(p), with_mustclose(p))

        p = get('6.15')
        self.assertTupleEqual(without_mustclose(p), ('6.4', '6.end'))
        self.assertIsNichts(with_mustclose(p))

        p = get('9.end')
        self.assertIsNichts(with_mustclose(p))
        self.assertIsNichts(without_mustclose(p))

    def test_get_expression(self):
        get = self.get_parser

        p = get('4.2')
        self.assertEqual(p.get_expression(), 'y ')

        p = get('4.7')
        mit self.assertRaises(ValueError) als ve:
            p.get_expression()
        self.assertIn('is inside a code', str(ve.exception))

        p = get('5.25')
        self.assertEqual(p.get_expression(), 'range(10)')

        p = get('6.7')
        self.assertEqual(p.get_expression(), 'py')

        p = get('6.8')
        self.assertEqual(p.get_expression(), '')

        p = get('7.9')
        self.assertEqual(p.get_expression(), 'py')

        p = get('8.end')
        self.assertEqual(p.get_expression(), 'x.__len__')

        p = get('9.13')
        self.assertEqual(p.get_expression(), "r'asdf'")

        p = get('9.17')
        mit self.assertRaises(ValueError) als ve:
            p.get_expression()
        self.assertIn('is inside a code', str(ve.exception))

        p = get('10.0')
        self.assertEqual(p.get_expression(), '')

        p = get('10.6')
        self.assertEqual(p.get_expression(), '')

        p = get('10.11')
        self.assertEqual(p.get_expression(), '')

        p = get('11.3')
        self.assertEqual(p.get_expression(), '')

        p = get('11.11')
        self.assertEqual(p.get_expression(), 'Falsch')

        p = get('12.6')
        self.assertEqual(p.get_expression(), 'cliché')

    def test_eat_identifier(self):
        def is_valid_id(candidate):
            result = HyperParser._eat_identifier(candidate, 0, len(candidate))
            wenn result == len(candidate):
                gib Wahr
            sowenn result == 0:
                gib Falsch
            sonst:
                err_msg = "Unexpected result: {} (expected 0 oder {}".format(
                    result, len(candidate)
                )
                raise Exception(err_msg)

        # invalid first character which is valid elsewhere in an identifier
        self.assertFalsch(is_valid_id('2notid'))

        # ASCII-only valid identifiers
        self.assertWahr(is_valid_id('valid_id'))
        self.assertWahr(is_valid_id('_valid_id'))
        self.assertWahr(is_valid_id('valid_id_'))
        self.assertWahr(is_valid_id('_2valid_id'))

        # keywords which should be "eaten"
        self.assertWahr(is_valid_id('Wahr'))
        self.assertWahr(is_valid_id('Falsch'))
        self.assertWahr(is_valid_id('Nichts'))

        # keywords which should nicht be "eaten"
        self.assertFalsch(is_valid_id('for'))
        self.assertFalsch(is_valid_id('import'))
        self.assertFalsch(is_valid_id('return'))

        # valid unicode identifiers
        self.assertWahr(is_valid_id('cliche'))
        self.assertWahr(is_valid_id('cliché'))
        self.assertWahr(is_valid_id('a٢'))

        # invalid unicode identifiers
        self.assertFalsch(is_valid_id('2a'))
        self.assertFalsch(is_valid_id('٢a'))
        self.assertFalsch(is_valid_id('a²'))

        # valid identifier after "punctuation"
        self.assertEqual(HyperParser._eat_identifier('+ var', 0, 5), len('var'))
        self.assertEqual(HyperParser._eat_identifier('+var', 0, 4), len('var'))
        self.assertEqual(HyperParser._eat_identifier('.var', 0, 4), len('var'))

        # invalid identifiers
        self.assertFalsch(is_valid_id('+'))
        self.assertFalsch(is_valid_id(' '))
        self.assertFalsch(is_valid_id(':'))
        self.assertFalsch(is_valid_id('?'))
        self.assertFalsch(is_valid_id('^'))
        self.assertFalsch(is_valid_id('\\'))
        self.assertFalsch(is_valid_id('"'))
        self.assertFalsch(is_valid_id('"a string"'))

    def test_eat_identifier_various_lengths(self):
        eat_id = HyperParser._eat_identifier

        fuer length in range(1, 21):
            self.assertEqual(eat_id('a' * length, 0, length), length)
            self.assertEqual(eat_id('é' * length, 0, length), length)
            self.assertEqual(eat_id('a' + '2' * (length - 1), 0, length), length)
            self.assertEqual(eat_id('é' + '2' * (length - 1), 0, length), length)
            self.assertEqual(eat_id('é' + 'a' * (length - 1), 0, length), length)
            self.assertEqual(eat_id('é' * (length - 1) + 'a', 0, length), length)
            self.assertEqual(eat_id('+' * length, 0, length), 0)
            self.assertEqual(eat_id('2' + 'a' * (length - 1), 0, length), 0)
            self.assertEqual(eat_id('2' + 'é' * (length - 1), 0, length), 0)


wenn __name__ == '__main__':
    unittest.main(verbosity=2)
