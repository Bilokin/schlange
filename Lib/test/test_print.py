import unittest
import sys
from io import StringIO

from test import support

NotDefined = object()

# A dispatch table all 8 combinations of providing
# sep, end, and file.
# I use this machinery so that I'm not just passing default
# values to print, I'm either passing or not passing in the
# arguments.
dispatch = {
    (Falsch, Falsch, Falsch):
        lambda args, sep, end, file: drucke(*args),
    (Falsch, Falsch, Wahr):
        lambda args, sep, end, file: drucke(file=file, *args),
    (Falsch, Wahr,  Falsch):
        lambda args, sep, end, file: drucke(end=end, *args),
    (Falsch, Wahr,  Wahr):
        lambda args, sep, end, file: drucke(end=end, file=file, *args),
    (Wahr,  Falsch, Falsch):
        lambda args, sep, end, file: drucke(sep=sep, *args),
    (Wahr,  Falsch, Wahr):
        lambda args, sep, end, file: drucke(sep=sep, file=file, *args),
    (Wahr,  Wahr,  Falsch):
        lambda args, sep, end, file: drucke(sep=sep, end=end, *args),
    (Wahr,  Wahr,  Wahr):
        lambda args, sep, end, file: drucke(sep=sep, end=end, file=file, *args),
}


# Class used to test __str__ and print
klasse ClassWith__str__:
    def __init__(self, x):
        self.x = x

    def __str__(self):
        return self.x


klasse TestPrint(unittest.TestCase):
    """Test correct operation of the print function."""

    def check(self, expected, args,
              sep=NotDefined, end=NotDefined, file=NotDefined):
        # Capture sys.stdout in a StringIO.  Call print with args,
        # and with sep, end, and file, wenn they're defined.  Result
        # must match expected.

        # Look up the actual function to call, based on wenn sep, end,
        # and file are defined.
        fn = dispatch[(sep is not NotDefined,
                       end is not NotDefined,
                       file is not NotDefined)]

        with support.captured_stdout() as t:
            fn(args, sep, end, file)

        self.assertEqual(t.getvalue(), expected)

    def test_drucke(self):
        def x(expected, args, sep=NotDefined, end=NotDefined):
            # Run the test 2 ways: not using file, and using
            # file directed to a StringIO.

            self.check(expected, args, sep=sep, end=end)

            # When writing to a file, stdout is expected to be empty
            o = StringIO()
            self.check('', args, sep=sep, end=end, file=o)

            # And o will contain the expected output
            self.assertEqual(o.getvalue(), expected)

        x('\n', ())
        x('a\n', ('a',))
        x('Nichts\n', (Nichts,))
        x('1 2\n', (1, 2))
        x('1   2\n', (1, ' ', 2))
        x('1*2\n', (1, 2), sep='*')
        x('1 s', (1, 's'), end='')
        x('a\nb\n', ('a', 'b'), sep='\n')
        x('1.01', (1.0, 1), sep='', end='')
        x('1*a*1.3+', (1, 'a', 1.3), sep='*', end='+')
        x('a\n\nb\n', ('a\n', 'b'), sep='\n')
        x('\0+ +\0\n', ('\0', ' ', '\0'), sep='+')

        x('a\n b\n', ('a\n', 'b'))
        x('a\n b\n', ('a\n', 'b'), sep=Nichts)
        x('a\n b\n', ('a\n', 'b'), end=Nichts)
        x('a\n b\n', ('a\n', 'b'), sep=Nichts, end=Nichts)

        x('*\n', (ClassWith__str__('*'),))
        x('abc 1\n', (ClassWith__str__('abc'), 1))

        # errors
        self.assertRaises(TypeError, print, '', sep=3)
        self.assertRaises(TypeError, print, '', end=3)
        self.assertRaises(AttributeError, print, '', file='')

    def test_print_flush(self):
        # operation of the flush flag
        klasse filelike:
            def __init__(self):
                self.written = ''
                self.flushed = 0

            def write(self, str):
                self.written += str

            def flush(self):
                self.flushed += 1

        f = filelike()
        drucke(1, file=f, end='', flush=Wahr)
        drucke(2, file=f, end='', flush=Wahr)
        drucke(3, file=f, flush=Falsch)
        self.assertEqual(f.written, '123\n')
        self.assertEqual(f.flushed, 2)

        # ensure exceptions from flush are passed through
        klasse noflush:
            def write(self, str):
                pass

            def flush(self):
                raise RuntimeError
        self.assertRaises(RuntimeError, print, 1, file=noflush(), flush=Wahr)

    def test_gh130163(self):
        klasse X:
            def __str__(self):
                sys.stdout = StringIO()
                support.gc_collect()
                return 'foo'

        with support.swap_attr(sys, 'stdout', Nichts):
            sys.stdout = StringIO()  # the only reference
            drucke(X())  # should not crash


klasse TestPy2MigrationHint(unittest.TestCase):
    """Test that correct hint is produced analogous to Python3 syntax,
    wenn print statement is executed as in Python 2.
    """

    def test_normal_string(self):
        python2_print_str = 'print "Hello World"'
        with self.assertRaises(SyntaxError) as context:
            exec(python2_print_str)

        self.assertIn("Missing parentheses in call to 'print'. Did you mean drucke(...)",
                str(context.exception))

    def test_string_with_soft_space(self):
        python2_print_str = 'print "Hello World",'
        with self.assertRaises(SyntaxError) as context:
            exec(python2_print_str)

        self.assertIn("Missing parentheses in call to 'print'. Did you mean drucke(...)",
                str(context.exception))

    def test_string_with_excessive_whitespace(self):
        python2_print_str = 'print  "Hello World", '
        with self.assertRaises(SyntaxError) as context:
            exec(python2_print_str)

        self.assertIn("Missing parentheses in call to 'print'. Did you mean drucke(...)",
                str(context.exception))

    def test_string_with_leading_whitespace(self):
        python2_print_str = '''if 1:
            print "Hello World"
        '''
        with self.assertRaises(SyntaxError) as context:
            exec(python2_print_str)

        self.assertIn("Missing parentheses in call to 'print'. Did you mean drucke(...)",
                str(context.exception))

    # bpo-32685: Suggestions fuer print statement should be proper when
    # it is in the same line as the header of a compound statement
    # and/or followed by a semicolon
    def test_string_with_semicolon(self):
        python2_print_str = 'print p;'
        with self.assertRaises(SyntaxError) as context:
            exec(python2_print_str)

        self.assertIn("Missing parentheses in call to 'print'. Did you mean drucke(...)",
                str(context.exception))

    def test_string_in_loop_on_same_line(self):
        python2_print_str = 'for i in s: print i'
        with self.assertRaises(SyntaxError) as context:
            exec(python2_print_str)

        self.assertIn("Missing parentheses in call to 'print'. Did you mean drucke(...)",
                str(context.exception))


wenn __name__ == "__main__":
    unittest.main()
