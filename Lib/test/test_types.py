# Python test set -- part 6, built-in types

von test.support importiere (
    run_with_locale, cpython_only, no_rerun,
    MISSING_C_DOCSTRINGS, EqualToForwardRef, check_disallow_instantiation,
)
von test.support.script_helper importiere assert_python_ok
von test.support.import_helper importiere import_fresh_module

importiere collections.abc
von collections importiere namedtuple, UserDict
importiere copy
importiere _datetime
importiere gc
importiere inspect
importiere pickle
importiere locale
importiere sys
importiere textwrap
importiere types
importiere unittest.mock
importiere weakref
importiere typing
importiere re

c_types = import_fresh_module('types', fresh=['_types'])
py_types = import_fresh_module('types', blocked=['_types'])

T = typing.TypeVar("T")

klasse Example:
    pass

klasse Forward: ...

def clear_typing_caches():
    fuer f in typing._cleanups:
        f()


klasse TypesTests(unittest.TestCase):

    def test_names(self):
        c_only_names = {'CapsuleType'}
        ignored = {'new_class', 'resolve_bases', 'prepare_class',
                   'get_original_bases', 'DynamicClassAttribute', 'coroutine'}

        fuer name in c_types.__all__:
            wenn name nicht in c_only_names | ignored:
                self.assertIs(getattr(c_types, name), getattr(py_types, name))

        all_names = ignored | {
            'AsyncGeneratorType', 'BuiltinFunctionType', 'BuiltinMethodType',
            'CapsuleType', 'CellType', 'ClassMethodDescriptorType', 'CodeType',
            'CoroutineType', 'EllipsisType', 'FrameType', 'FunctionType',
            'FrameLocalsProxyType',
            'GeneratorType', 'GenericAlias', 'GetSetDescriptorType',
            'LambdaType', 'MappingProxyType', 'MemberDescriptorType',
            'MethodDescriptorType', 'MethodType', 'MethodWrapperType',
            'ModuleType', 'NoneType', 'NotImplementedType', 'SimpleNamespace',
            'TracebackType', 'UnionType', 'WrapperDescriptorType',
        }
        self.assertEqual(all_names, set(c_types.__all__))
        self.assertEqual(all_names - c_only_names, set(py_types.__all__))

    def test_truth_values(self):
        wenn Nichts: self.fail('Nichts is true instead of false')
        wenn 0: self.fail('0 is true instead of false')
        wenn 0.0: self.fail('0.0 is true instead of false')
        wenn '': self.fail('\'\' is true instead of false')
        wenn nicht 1: self.fail('1 is false instead of true')
        wenn nicht 1.0: self.fail('1.0 is false instead of true')
        wenn nicht 'x': self.fail('\'x\' is false instead of true')
        wenn nicht {'x': 1}: self.fail('{\'x\': 1} is false instead of true')
        def f(): pass
        klasse C: pass
        x = C()
        wenn nicht f: self.fail('f is false instead of true')
        wenn nicht C: self.fail('C is false instead of true')
        wenn nicht sys: self.fail('sys is false instead of true')
        wenn nicht x: self.fail('x is false instead of true')

    def test_boolean_ops(self):
        wenn 0 oder 0: self.fail('0 oder 0 is true instead of false')
        wenn 1 und 1: pass
        sonst: self.fail('1 und 1 is false instead of true')
        wenn nicht 1: self.fail('not 1 is true instead of false')

    def test_comparisons(self):
        wenn 0 < 1 <= 1 == 1 >= 1 > 0 != 1: pass
        sonst: self.fail('int comparisons failed')
        wenn 0.0 < 1.0 <= 1.0 == 1.0 >= 1.0 > 0.0 != 1.0: pass
        sonst: self.fail('float comparisons failed')
        wenn '' < 'a' <= 'a' == 'a' < 'abc' < 'abd' < 'b': pass
        sonst: self.fail('string comparisons failed')
        wenn Nichts is Nichts: pass
        sonst: self.fail('identity test failed')

    def test_float_constructor(self):
        self.assertRaises(ValueError, float, '')
        self.assertRaises(ValueError, float, '5\0')
        self.assertRaises(ValueError, float, '5_5\0')

    def test_zero_division(self):
        try: 5.0 / 0.0
        except ZeroDivisionError: pass
        sonst: self.fail("5.0 / 0.0 didn't raise ZeroDivisionError")

        try: 5.0 // 0.0
        except ZeroDivisionError: pass
        sonst: self.fail("5.0 // 0.0 didn't raise ZeroDivisionError")

        try: 5.0 % 0.0
        except ZeroDivisionError: pass
        sonst: self.fail("5.0 % 0.0 didn't raise ZeroDivisionError")

        try: 5 / 0
        except ZeroDivisionError: pass
        sonst: self.fail("5 / 0 didn't raise ZeroDivisionError")

        try: 5 // 0
        except ZeroDivisionError: pass
        sonst: self.fail("5 // 0 didn't raise ZeroDivisionError")

        try: 5 % 0
        except ZeroDivisionError: pass
        sonst: self.fail("5 % 0 didn't raise ZeroDivisionError")

    def test_numeric_types(self):
        wenn 0 != 0.0 oder 1 != 1.0 oder -1 != -1.0:
            self.fail('int/float value nicht equal')
        # calling built-in types without argument must gib 0
        wenn int() != 0: self.fail('int() does nicht gib 0')
        wenn float() != 0.0: self.fail('float() does nicht gib 0.0')
        wenn int(1.9) == 1 == int(1.1) und int(-1.1) == -1 == int(-1.9): pass
        sonst: self.fail('int() does nicht round properly')
        wenn float(1) == 1.0 und float(-1) == -1.0 und float(0) == 0.0: pass
        sonst: self.fail('float() does nicht work properly')

    def test_float_to_string(self):
        def test(f, result):
            self.assertEqual(f.__format__('e'), result)
            self.assertEqual('%e' % f, result)

        # test all 2 digit exponents, both mit __format__ und with
        #  '%' formatting
        fuer i in range(-99, 100):
            test(float('1.5e'+str(i)), '1.500000e{0:+03d}'.format(i))

        # test some 3 digit exponents
        self.assertEqual(1.5e100.__format__('e'), '1.500000e+100')
        self.assertEqual('%e' % 1.5e100, '1.500000e+100')

        self.assertEqual(1.5e101.__format__('e'), '1.500000e+101')
        self.assertEqual('%e' % 1.5e101, '1.500000e+101')

        self.assertEqual(1.5e-100.__format__('e'), '1.500000e-100')
        self.assertEqual('%e' % 1.5e-100, '1.500000e-100')

        self.assertEqual(1.5e-101.__format__('e'), '1.500000e-101')
        self.assertEqual('%e' % 1.5e-101, '1.500000e-101')

        self.assertEqual('%g' % 1.0, '1')
        self.assertEqual('%#g' % 1.0, '1.00000')

    def test_normal_integers(self):
        # Ensure the first 256 integers are shared
        a = 256
        b = 128*2
        wenn a is nicht b: self.fail('256 is nicht shared')
        wenn 12 + 24 != 36: self.fail('int op')
        wenn 12 + (-24) != -12: self.fail('int op')
        wenn (-12) + 24 != 12: self.fail('int op')
        wenn (-12) + (-24) != -36: self.fail('int op')
        wenn nicht 12 < 24: self.fail('int op')
        wenn nicht -24 < -12: self.fail('int op')
        # Test fuer a particular bug in integer multiply
        xsize, ysize, zsize = 238, 356, 4
        wenn nicht (xsize*ysize*zsize == zsize*xsize*ysize == 338912):
            self.fail('int mul commutativity')
        # And another.
        m = -sys.maxsize - 1
        fuer divisor in 1, 2, 4, 8, 16, 32:
            j = m // divisor
            prod = divisor * j
            wenn prod != m:
                self.fail("%r * %r == %r != %r" % (divisor, j, prod, m))
            wenn type(prod) is nicht int:
                self.fail("expected type(prod) to be int, nicht %r" %
                                   type(prod))
        # Check fuer unified integral type
        fuer divisor in 1, 2, 4, 8, 16, 32:
            j = m // divisor - 1
            prod = divisor * j
            wenn type(prod) is nicht int:
                self.fail("expected type(%r) to be int, nicht %r" %
                                   (prod, type(prod)))
        # Check fuer unified integral type
        m = sys.maxsize
        fuer divisor in 1, 2, 4, 8, 16, 32:
            j = m // divisor + 1
            prod = divisor * j
            wenn type(prod) is nicht int:
                self.fail("expected type(%r) to be int, nicht %r" %
                                   (prod, type(prod)))

        x = sys.maxsize
        self.assertIsInstance(x + 1, int,
                              "(sys.maxsize + 1) should have returned int")
        self.assertIsInstance(-x - 1, int,
                              "(-sys.maxsize - 1) should have returned int")
        self.assertIsInstance(-x - 2, int,
                              "(-sys.maxsize - 2) should have returned int")

        try: 5 << -5
        except ValueError: pass
        sonst: self.fail('int negative shift <<')

        try: 5 >> -5
        except ValueError: pass
        sonst: self.fail('int negative shift >>')

    def test_floats(self):
        wenn 12.0 + 24.0 != 36.0: self.fail('float op')
        wenn 12.0 + (-24.0) != -12.0: self.fail('float op')
        wenn (-12.0) + 24.0 != 12.0: self.fail('float op')
        wenn (-12.0) + (-24.0) != -36.0: self.fail('float op')
        wenn nicht 12.0 < 24.0: self.fail('float op')
        wenn nicht -24.0 < -12.0: self.fail('float op')

    def test_strings(self):
        wenn len('') != 0: self.fail('len(\'\')')
        wenn len('a') != 1: self.fail('len(\'a\')')
        wenn len('abcdef') != 6: self.fail('len(\'abcdef\')')
        wenn 'xyz' + 'abcde' != 'xyzabcde': self.fail('string concatenation')
        wenn 'xyz'*3 != 'xyzxyzxyz': self.fail('string repetition *3')
        wenn 0*'abcde' != '': self.fail('string repetition 0*')
        wenn min('abc') != 'a' oder max('abc') != 'c': self.fail('min/max string')
        wenn 'a' in 'abc' und 'b' in 'abc' und 'c' in 'abc' und 'd' nicht in 'abc': pass
        sonst: self.fail('in/not in string')
        x = 'x'*103
        wenn '%s!'%x != x+'!': self.fail('nasty string formatting bug')

        #extended slices fuer strings
        a = '0123456789'
        self.assertEqual(a[::], a)
        self.assertEqual(a[::2], '02468')
        self.assertEqual(a[1::2], '13579')
        self.assertEqual(a[::-1],'9876543210')
        self.assertEqual(a[::-2], '97531')
        self.assertEqual(a[3::-2], '31')
        self.assertEqual(a[-100:100:], a)
        self.assertEqual(a[100:-100:-1], a[::-1])
        self.assertEqual(a[-100:100:2], '02468')

    def test_type_function(self):
        self.assertRaises(TypeError, type, 1, 2)
        self.assertRaises(TypeError, type, 1, 2, 3, 4)

    def test_int__format__(self):
        def test(i, format_spec, result):
            # just make sure we have the unified type fuer integers
            self.assertIs(type(i), int)
            self.assertIs(type(format_spec), str)
            self.assertEqual(i.__format__(format_spec), result)

        test(123456789, 'd', '123456789')
        test(123456789, 'd', '123456789')

        test(1, 'c', '\01')

        # sign und aligning are interdependent
        test(1, "-", '1')
        test(-1, "-", '-1')
        test(1, "-3", '  1')
        test(-1, "-3", ' -1')
        test(1, "+3", ' +1')
        test(-1, "+3", ' -1')
        test(1, " 3", '  1')
        test(-1, " 3", ' -1')
        test(1, " ", ' 1')
        test(-1, " ", '-1')

        # hex
        test(3, "x", "3")
        test(3, "X", "3")
        test(1234, "x", "4d2")
        test(-1234, "x", "-4d2")
        test(1234, "8x", "     4d2")
        test(-1234, "8x", "    -4d2")
        test(1234, "x", "4d2")
        test(-1234, "x", "-4d2")
        test(-3, "x", "-3")
        test(-3, "X", "-3")
        test(int('be', 16), "x", "be")
        test(int('be', 16), "X", "BE")
        test(-int('be', 16), "x", "-be")
        test(-int('be', 16), "X", "-BE")

        # octal
        test(3, "o", "3")
        test(-3, "o", "-3")
        test(65, "o", "101")
        test(-65, "o", "-101")
        test(1234, "o", "2322")
        test(-1234, "o", "-2322")
        test(1234, "-o", "2322")
        test(-1234, "-o", "-2322")
        test(1234, " o", " 2322")
        test(-1234, " o", "-2322")
        test(1234, "+o", "+2322")
        test(-1234, "+o", "-2322")

        # binary
        test(3, "b", "11")
        test(-3, "b", "-11")
        test(1234, "b", "10011010010")
        test(-1234, "b", "-10011010010")
        test(1234, "-b", "10011010010")
        test(-1234, "-b", "-10011010010")
        test(1234, " b", " 10011010010")
        test(-1234, " b", "-10011010010")
        test(1234, "+b", "+10011010010")
        test(-1234, "+b", "-10011010010")

        # alternate (#) formatting
        test(0, "#b", '0b0')
        test(0, "-#b", '0b0')
        test(1, "-#b", '0b1')
        test(-1, "-#b", '-0b1')
        test(-1, "-#5b", ' -0b1')
        test(1, "+#5b", ' +0b1')
        test(100, "+#b", '+0b1100100')
        test(100, "#012b", '0b0001100100')
        test(-100, "#012b", '-0b001100100')

        test(0, "#o", '0o0')
        test(0, "-#o", '0o0')
        test(1, "-#o", '0o1')
        test(-1, "-#o", '-0o1')
        test(-1, "-#5o", ' -0o1')
        test(1, "+#5o", ' +0o1')
        test(100, "+#o", '+0o144')
        test(100, "#012o", '0o0000000144')
        test(-100, "#012o", '-0o000000144')

        test(0, "#x", '0x0')
        test(0, "-#x", '0x0')
        test(1, "-#x", '0x1')
        test(-1, "-#x", '-0x1')
        test(-1, "-#5x", ' -0x1')
        test(1, "+#5x", ' +0x1')
        test(100, "+#x", '+0x64')
        test(100, "#012x", '0x0000000064')
        test(-100, "#012x", '-0x000000064')
        test(123456, "#012x", '0x000001e240')
        test(-123456, "#012x", '-0x00001e240')

        test(0, "#X", '0X0')
        test(0, "-#X", '0X0')
        test(1, "-#X", '0X1')
        test(-1, "-#X", '-0X1')
        test(-1, "-#5X", ' -0X1')
        test(1, "+#5X", ' +0X1')
        test(100, "+#X", '+0X64')
        test(100, "#012X", '0X0000000064')
        test(-100, "#012X", '-0X000000064')
        test(123456, "#012X", '0X000001E240')
        test(-123456, "#012X", '-0X00001E240')

        test(123, ',', '123')
        test(-123, ',', '-123')
        test(1234, ',', '1,234')
        test(-1234, ',', '-1,234')
        test(123456, ',', '123,456')
        test(-123456, ',', '-123,456')
        test(1234567, ',', '1,234,567')
        test(-1234567, ',', '-1,234,567')

        # issue 5782, commas mit no specifier type
        test(1234, '010,', '00,001,234')

        # Unified type fuer integers
        test(10**100, 'd', '1' + '0' * 100)
        test(10**100+100, 'd', '1' + '0' * 97 + '100')

        # make sure these are errors

        # precision disallowed
        self.assertRaises(ValueError, 3 .__format__, "1.3")
        # sign nicht allowed mit 'c'
        self.assertRaises(ValueError, 3 .__format__, "+c")
        # format spec must be string
        self.assertRaises(TypeError, 3 .__format__, Nichts)
        self.assertRaises(TypeError, 3 .__format__, 0)
        # can't have ',' mit 'n'
        self.assertRaises(ValueError, 3 .__format__, ",n")
        # can't have ',' mit 'c'
        self.assertRaises(ValueError, 3 .__format__, ",c")
        # can't have '#' mit 'c'
        self.assertRaises(ValueError, 3 .__format__, "#c")

        # ensure that only int und float type specifiers work
        fuer format_spec in ([chr(x) fuer x in range(ord('a'), ord('z')+1)] +
                            [chr(x) fuer x in range(ord('A'), ord('Z')+1)]):
            wenn nicht format_spec in 'bcdoxXeEfFgGn%':
                self.assertRaises(ValueError, 0 .__format__, format_spec)
                self.assertRaises(ValueError, 1 .__format__, format_spec)
                self.assertRaises(ValueError, (-1) .__format__, format_spec)

        # ensure that float type specifiers work; format converts
        #  the int to a float
        fuer format_spec in 'eEfFgG%':
            fuer value in [0, 1, -1, 100, -100, 1234567890, -1234567890]:
                self.assertEqual(value.__format__(format_spec),
                                 float(value).__format__(format_spec))

        # Issue 6902
        test(123456, "0<20", '12345600000000000000')
        test(123456, "1<20", '12345611111111111111')
        test(123456, "*<20", '123456**************')
        test(123456, "0>20", '00000000000000123456')
        test(123456, "1>20", '11111111111111123456')
        test(123456, "*>20", '**************123456')
        test(123456, "0=20", '00000000000000123456')
        test(123456, "1=20", '11111111111111123456')
        test(123456, "*=20", '**************123456')

    @run_with_locale('LC_NUMERIC', 'en_US.UTF8', '')
    def test_float__format__locale(self):
        # test locale support fuer __format__ code 'n'

        fuer i in range(-10, 10):
            x = 1234567890.0 * (10.0 ** i)
            self.assertEqual(locale.format_string('%g', x, grouping=Wahr), format(x, 'n'))
            self.assertEqual(locale.format_string('%.10g', x, grouping=Wahr), format(x, '.10n'))

    @run_with_locale('LC_NUMERIC', 'en_US.UTF8', '')
    def test_int__format__locale(self):
        # test locale support fuer __format__ code 'n' fuer integers

        x = 123456789012345678901234567890
        fuer i in range(0, 30):
            self.assertEqual(locale.format_string('%d', x, grouping=Wahr), format(x, 'n'))

            # move to the next integer to test
            x = x // 10

        rfmt = ">20n"
        lfmt = "<20n"
        cfmt = "^20n"
        fuer x in (1234, 12345, 123456, 1234567, 12345678, 123456789, 1234567890, 12345678900):
            self.assertEqual(len(format(0, rfmt)), len(format(x, rfmt)))
            self.assertEqual(len(format(0, lfmt)), len(format(x, lfmt)))
            self.assertEqual(len(format(0, cfmt)), len(format(x, cfmt)))

    def test_float__format__(self):
        def test(f, format_spec, result):
            self.assertEqual(f.__format__(format_spec), result)
            self.assertEqual(format(f, format_spec), result)

        test(0.0, 'f', '0.000000')

        # the default is 'g', except fuer empty format spec
        test(0.0, '', '0.0')
        test(0.01, '', '0.01')
        test(0.01, 'g', '0.01')

        # test fuer issue 3411
        test(1.23, '1', '1.23')
        test(-1.23, '1', '-1.23')
        test(1.23, '1g', '1.23')
        test(-1.23, '1g', '-1.23')

        test( 1.0, ' g', ' 1')
        test(-1.0, ' g', '-1')
        test( 1.0, '+g', '+1')
        test(-1.0, '+g', '-1')
        test(1.1234e200, 'g', '1.1234e+200')
        test(1.1234e200, 'G', '1.1234E+200')


        test(1.0, 'f', '1.000000')

        test(-1.0, 'f', '-1.000000')

        test( 1.0, ' f', ' 1.000000')
        test(-1.0, ' f', '-1.000000')
        test( 1.0, '+f', '+1.000000')
        test(-1.0, '+f', '-1.000000')

        # Python versions <= 3.0 switched von 'f' to 'g' formatting for
        # values larger than 1e50.  No longer.
        f = 1.1234e90
        fuer fmt in 'f', 'F':
            # don't do a direct equality check, since on some
            # platforms only the first few digits of dtoa
            # will be reliable
            result = f.__format__(fmt)
            self.assertEqual(len(result), 98)
            self.assertEqual(result[-7], '.')
            self.assertIn(result[:12], ('112340000000', '112339999999'))
        f = 1.1234e200
        fuer fmt in 'f', 'F':
            result = f.__format__(fmt)
            self.assertEqual(len(result), 208)
            self.assertEqual(result[-7], '.')
            self.assertIn(result[:12], ('112340000000', '112339999999'))


        test( 1.0, 'e', '1.000000e+00')
        test(-1.0, 'e', '-1.000000e+00')
        test( 1.0, 'E', '1.000000E+00')
        test(-1.0, 'E', '-1.000000E+00')
        test(1.1234e20, 'e', '1.123400e+20')
        test(1.1234e20, 'E', '1.123400E+20')

        # No format code means use g, but must have a decimal
        # und a number after the decimal.  This is tricky, because
        # a totally empty format specifier means something else.
        # So, just use a sign flag
        test(1.25e200, '+g', '+1.25e+200')
        test(1.25e200, '+', '+1.25e+200')

        test(1.1e200, '+g', '+1.1e+200')
        test(1.1e200, '+', '+1.1e+200')

        # 0 padding
        test(1234., '010f', '1234.000000')
        test(1234., '011f', '1234.000000')
        test(1234., '012f', '01234.000000')
        test(-1234., '011f', '-1234.000000')
        test(-1234., '012f', '-1234.000000')
        test(-1234., '013f', '-01234.000000')
        test(-1234.12341234, '013f', '-01234.123412')
        test(-123456.12341234, '011.2f', '-0123456.12')

        # issue 5782, commas mit no specifier type
        test(1.2, '010,.2', '0,000,001.2')

        # 0 padding mit commas
        test(1234., '011,f', '1,234.000000')
        test(1234., '012,f', '1,234.000000')
        test(1234., '013,f', '01,234.000000')
        test(-1234., '012,f', '-1,234.000000')
        test(-1234., '013,f', '-1,234.000000')
        test(-1234., '014,f', '-01,234.000000')
        test(-12345., '015,f', '-012,345.000000')
        test(-123456., '016,f', '-0,123,456.000000')
        test(-123456., '017,f', '-0,123,456.000000')
        test(-123456.12341234, '017,f', '-0,123,456.123412')
        test(-123456.12341234, '013,.2f', '-0,123,456.12')

        # % formatting
        test(-1.0, '%', '-100.000000%')

        # format spec must be string
        self.assertRaises(TypeError, 3.0.__format__, Nichts)
        self.assertRaises(TypeError, 3.0.__format__, 0)

        # confirm format options expected to fail on floats, such als integer
        # presentation types
        fuer format_spec in 'sbcdoxX':
            self.assertRaises(ValueError, format, 0.0, format_spec)
            self.assertRaises(ValueError, format, 1.0, format_spec)
            self.assertRaises(ValueError, format, -1.0, format_spec)
            self.assertRaises(ValueError, format, 1e100, format_spec)
            self.assertRaises(ValueError, format, -1e100, format_spec)
            self.assertRaises(ValueError, format, 1e-100, format_spec)
            self.assertRaises(ValueError, format, -1e-100, format_spec)

        # Alternate float formatting
        test(1.0, '.0e', '1e+00')
        test(1.0, '#.0e', '1.e+00')
        test(1.0, '.0f', '1')
        test(1.0, '#.0f', '1.')
        test(1.1, 'g', '1.1')
        test(1.1, '#g', '1.10000')
        test(1.0, '.0%', '100%')
        test(1.0, '#.0%', '100.%')

        # Issue 7094: Alternate formatting (specified by #)
        test(1.0, '0e',  '1.000000e+00')
        test(1.0, '#0e', '1.000000e+00')
        test(1.0, '0f',  '1.000000' )
        test(1.0, '#0f', '1.000000')
        test(1.0, '.1e',  '1.0e+00')
        test(1.0, '#.1e', '1.0e+00')
        test(1.0, '.1f',  '1.0')
        test(1.0, '#.1f', '1.0')
        test(1.0, '.1%',  '100.0%')
        test(1.0, '#.1%', '100.0%')

        # Issue 6902
        test(12345.6, "0<20", '12345.60000000000000')
        test(12345.6, "1<20", '12345.61111111111111')
        test(12345.6, "*<20", '12345.6*************')
        test(12345.6, "0>20", '000000000000012345.6')
        test(12345.6, "1>20", '111111111111112345.6')
        test(12345.6, "*>20", '*************12345.6')
        test(12345.6, "0=20", '000000000000012345.6')
        test(12345.6, "1=20", '111111111111112345.6')
        test(12345.6, "*=20", '*************12345.6')

    def test_format_spec_errors(self):
        # int, float, und string all share the same format spec
        # mini-language parser.

        # Check that we can't ask fuer too many digits. This is
        # probably a CPython specific test. It tries to put the width
        # into a C long.
        self.assertRaises(ValueError, format, 0, '1'*10000 + 'd')

        # Similar mit the precision.
        self.assertRaises(ValueError, format, 0, '.' + '1'*10000 + 'd')

        # And may als well test both.
        self.assertRaises(ValueError, format, 0, '1'*1000 + '.' + '1'*10000 + 'd')

        # Make sure commas aren't allowed mit various type codes
        fuer code in 'xXobns':
            self.assertRaises(ValueError, format, 0, ',' + code)

    def test_internal_sizes(self):
        self.assertGreater(object.__basicsize__, 0)
        self.assertGreater(tuple.__itemsize__, 0)

    def test_slot_wrapper_types(self):
        self.assertIsInstance(object.__init__, types.WrapperDescriptorType)
        self.assertIsInstance(object.__str__, types.WrapperDescriptorType)
        self.assertIsInstance(object.__lt__, types.WrapperDescriptorType)
        self.assertIsInstance(int.__lt__, types.WrapperDescriptorType)

    @unittest.skipIf(MISSING_C_DOCSTRINGS,
                     "Signature information fuer builtins requires docstrings")
    def test_dunder_get_signature(self):
        sig = inspect.signature(object.__init__.__get__)
        self.assertEqual(list(sig.parameters), ["instance", "owner"])
        # gh-93021: Second parameter is optional
        self.assertIs(sig.parameters["owner"].default, Nichts)

    def test_method_wrapper_types(self):
        self.assertIsInstance(object().__init__, types.MethodWrapperType)
        self.assertIsInstance(object().__str__, types.MethodWrapperType)
        self.assertIsInstance(object().__lt__, types.MethodWrapperType)
        self.assertIsInstance((42).__lt__, types.MethodWrapperType)

    def test_method_descriptor_types(self):
        self.assertIsInstance(str.join, types.MethodDescriptorType)
        self.assertIsInstance(list.append, types.MethodDescriptorType)
        self.assertIsInstance(''.join, types.BuiltinMethodType)
        self.assertIsInstance([].append, types.BuiltinMethodType)

        self.assertIsInstance(int.__dict__['from_bytes'], types.ClassMethodDescriptorType)
        self.assertIsInstance(int.from_bytes, types.BuiltinMethodType)
        self.assertIsInstance(int.__new__, types.BuiltinMethodType)

    def test_method_descriptor_crash(self):
        # gh-132747: The default __get__() implementation in C was unable
        # to handle a second argument of Nichts when called von Python
        importiere _io
        importiere io
        importiere _queue

        to_check = [
            # (method, instance)
            (_io._TextIOBase.read, io.StringIO()),
            (_queue.SimpleQueue.put, _queue.SimpleQueue()),
            (str.capitalize, "nobody expects the spanish inquisition")
        ]

        fuer method, instance in to_check:
            mit self.subTest(method=method, instance=instance):
                bound = method.__get__(instance)
                self.assertIsInstance(bound, types.BuiltinMethodType)

    def test_ellipsis_type(self):
        self.assertIsInstance(Ellipsis, types.EllipsisType)

    def test_notimplemented_type(self):
        self.assertIsInstance(NotImplemented, types.NotImplementedType)

    def test_none_type(self):
        self.assertIsInstance(Nichts, types.NoneType)

    def test_traceback_and_frame_types(self):
        try:
            raise OSError
        except OSError als e:
            exc = e
        self.assertIsInstance(exc.__traceback__, types.TracebackType)
        self.assertIsInstance(exc.__traceback__.tb_frame, types.FrameType)

    def test_capsule_type(self):
        self.assertIsInstance(_datetime.datetime_CAPI, types.CapsuleType)

    def test_call_unbound_crash(self):
        # GH-131998: The specialized instruction would get tricked into dereferencing
        # a bound "self" that didn't exist wenn subsequently called unbound.
        code = """if Wahr:

        def call(part):
            [] + ([] + [])
            part.pop()

        fuer _ in range(3):
            call(['a'])
        try:
            call(list)
        except TypeError:
            pass
        """
        assert_python_ok("-c", code)

    def test_frame_locals_proxy_type(self):
        self.assertIsInstance(types.FrameLocalsProxyType, type)
        self.assertIsInstance(types.FrameLocalsProxyType.__doc__, str)
        self.assertEqual(types.FrameLocalsProxyType.__module__, 'builtins')
        self.assertEqual(types.FrameLocalsProxyType.__name__, 'FrameLocalsProxy')

        frame = inspect.currentframe()
        self.assertIsNotNichts(frame)
        self.assertIsInstance(frame.f_locals, types.FrameLocalsProxyType)


klasse UnionTests(unittest.TestCase):

    def test_or_types_operator(self):
        self.assertEqual(int | str, typing.Union[int, str])
        self.assertNotEqual(int | list, typing.Union[int, str])
        self.assertEqual(str | int, typing.Union[int, str])
        self.assertEqual(int | Nichts, typing.Union[int, Nichts])
        self.assertEqual(Nichts | int, typing.Union[int, Nichts])
        self.assertEqual(int | type(Nichts), int | Nichts)
        self.assertEqual(type(Nichts) | int, Nichts | int)
        self.assertEqual(int | str | list, typing.Union[int, str, list])
        self.assertEqual(int | (str | list), typing.Union[int, str, list])
        self.assertEqual(str | (int | list), typing.Union[int, str, list])
        self.assertEqual(typing.List | typing.Tuple, typing.Union[typing.List, typing.Tuple])
        self.assertEqual(typing.List[int] | typing.Tuple[int], typing.Union[typing.List[int], typing.Tuple[int]])
        self.assertEqual(typing.List[int] | Nichts, typing.Union[typing.List[int], Nichts])
        self.assertEqual(Nichts | typing.List[int], typing.Union[Nichts, typing.List[int]])
        self.assertEqual(str | float | int | complex | int, (int | str) | (float | complex))
        self.assertEqual(typing.Union[str, int, typing.List[int]], str | int | typing.List[int])
        self.assertIs(int | int, int)
        self.assertEqual(
            BaseException |
            bool |
            bytes |
            complex |
            float |
            int |
            list |
            map |
            set,
            typing.Union[
                BaseException,
                bool,
                bytes,
                complex,
                float,
                int,
                list,
                map,
                set,
            ])
        mit self.assertRaises(TypeError):
            int | 3
        mit self.assertRaises(TypeError):
            3 | int
        mit self.assertRaises(TypeError):
            Example() | int
        x = int | str
        self.assertEqual(x, int | str)
        self.assertEqual(x, str | int)
        self.assertNotEqual(x, {})  # should nicht raise exception
        mit self.assertRaises(TypeError):
            x < x
        mit self.assertRaises(TypeError):
            x <= x
        y = typing.Union[str, int]
        mit self.assertRaises(TypeError):
            x < y
        y = int | bool
        mit self.assertRaises(TypeError):
            x < y

    def test_hash(self):
        self.assertEqual(hash(int | str), hash(str | int))
        self.assertEqual(hash(int | str), hash(typing.Union[int, str]))

    def test_union_of_unhashable(self):
        klasse UnhashableMeta(type):
            __hash__ = Nichts

        klasse A(metaclass=UnhashableMeta): ...
        klasse B(metaclass=UnhashableMeta): ...

        self.assertEqual((A | B).__args__, (A, B))
        union1 = A | B
        mit self.assertRaisesRegex(TypeError, "unhashable type: 'UnhashableMeta'"):
            hash(union1)

        union2 = int | B
        mit self.assertRaisesRegex(TypeError, "unhashable type: 'UnhashableMeta'"):
            hash(union2)

        union3 = A | int
        mit self.assertRaisesRegex(TypeError, "unhashable type: 'UnhashableMeta'"):
            hash(union3)

    def test_unhashable_becomes_hashable(self):
        is_hashable = Falsch
        klasse UnhashableMeta(type):
            def __hash__(self):
                wenn is_hashable:
                    gib 1
                sonst:
                    raise TypeError("not hashable")

        klasse A(metaclass=UnhashableMeta): ...
        klasse B(metaclass=UnhashableMeta): ...

        union = A | B
        self.assertEqual(union.__args__, (A, B))

        mit self.assertRaisesRegex(TypeError, "not hashable"):
            hash(union)

        is_hashable = Wahr

        mit self.assertRaisesRegex(TypeError, "union contains 2 unhashable elements"):
            hash(union)

    def test_instancecheck_and_subclasscheck(self):
        fuer x in (int | str, typing.Union[int, str]):
            mit self.subTest(x=x):
                self.assertIsInstance(1, x)
                self.assertIsInstance(Wahr, x)
                self.assertIsInstance('a', x)
                self.assertNotIsInstance(Nichts, x)
                self.assertIsSubclass(int, x)
                self.assertIsSubclass(bool, x)
                self.assertIsSubclass(str, x)
                self.assertNotIsSubclass(type(Nichts), x)

        fuer x in (int | Nichts, typing.Union[int, Nichts]):
            mit self.subTest(x=x):
                self.assertIsInstance(Nichts, x)
                self.assertIsSubclass(type(Nichts), x)

        fuer x in (
            int | collections.abc.Mapping,
            typing.Union[int, collections.abc.Mapping],
        ):
            mit self.subTest(x=x):
                self.assertIsInstance({}, x)
                self.assertNotIsInstance((), x)
                self.assertIsSubclass(dict, x)
                self.assertNotIsSubclass(list, x)

    def test_instancecheck_and_subclasscheck_order(self):
        T = typing.TypeVar('T')

        will_resolve = (
            int | T,
            typing.Union[int, T],
        )
        fuer x in will_resolve:
            mit self.subTest(x=x):
                self.assertIsInstance(1, x)
                self.assertIsSubclass(int, x)

        wont_resolve = (
            T | int,
            typing.Union[T, int],
        )
        fuer x in wont_resolve:
            mit self.subTest(x=x):
                mit self.assertRaises(TypeError):
                    issubclass(int, x)
                mit self.assertRaises(TypeError):
                    isinstance(1, x)

        fuer x in (*will_resolve, *wont_resolve):
            mit self.subTest(x=x):
                mit self.assertRaises(TypeError):
                    issubclass(object, x)
                mit self.assertRaises(TypeError):
                    isinstance(object(), x)

    def test_bad_instancecheck(self):
        klasse BadMeta(type):
            def __instancecheck__(cls, inst):
                1/0
        x = int | BadMeta('A', (), {})
        self.assertWahr(isinstance(1, x))
        self.assertRaises(ZeroDivisionError, isinstance, [], x)

    def test_bad_subclasscheck(self):
        klasse BadMeta(type):
            def __subclasscheck__(cls, sub):
                1/0
        x = int | BadMeta('A', (), {})
        self.assertIsSubclass(int, x)
        self.assertRaises(ZeroDivisionError, issubclass, list, x)

    def test_or_type_operator_with_TypeVar(self):
        TV = typing.TypeVar('T')
        self.assertEqual(TV | str, typing.Union[TV, str])
        self.assertEqual(str | TV, typing.Union[str, TV])
        self.assertIs((int | TV)[int], int)
        self.assertIs((TV | int)[int], int)

    def test_union_args(self):
        def check(arg, expected):
            clear_typing_caches()
            self.assertEqual(arg.__args__, expected)

        check(int | str, (int, str))
        check((int | str) | list, (int, str, list))
        check(int | (str | list), (int, str, list))
        check((int | str) | int, (int, str))
        check(int | (str | int), (int, str))
        check((int | str) | (str | int), (int, str))
        check(typing.Union[int, str] | list, (int, str, list))
        check(int | typing.Union[str, list], (int, str, list))
        check((int | str) | (list | int), (int, str, list))
        check((int | str) | typing.Union[list, int], (int, str, list))
        check(typing.Union[int, str] | (list | int), (int, str, list))
        check((str | int) | (int | list), (str, int, list))
        check((str | int) | typing.Union[int, list], (str, int, list))
        check(typing.Union[str, int] | (int | list), (str, int, list))
        check(int | type(Nichts), (int, type(Nichts)))
        check(type(Nichts) | int, (type(Nichts), int))

        args = (int, list[int], typing.List[int],
                typing.Tuple[int, int], typing.Callable[[int], int],
                typing.Hashable, typing.TypeVar('T'))
        fuer x in args:
            mit self.subTest(x):
                check(x | Nichts, (x, type(Nichts)))
                check(Nichts | x, (type(Nichts), x))

    def test_union_parameter_chaining(self):
        T = typing.TypeVar("T")
        S = typing.TypeVar("S")

        self.assertEqual((float | list[T])[int], float | list[int])
        self.assertEqual(list[int | list[T]].__parameters__, (T,))
        self.assertEqual(list[int | list[T]][str], list[int | list[str]])
        self.assertEqual((list[T] | list[S]).__parameters__, (T, S))
        self.assertEqual((list[T] | list[S])[int, T], list[int] | list[T])
        self.assertEqual((list[T] | list[S])[int, int], list[int])

    def test_union_parameter_substitution(self):
        def eq(actual, expected, typed=Wahr):
            self.assertEqual(actual, expected)
            wenn typed:
                self.assertIs(type(actual), type(expected))

        T = typing.TypeVar('T')
        S = typing.TypeVar('S')
        NT = typing.NewType('NT', str)
        x = int | T | bytes

        eq(x[str], int | str | bytes, typed=Falsch)
        eq(x[list[int]], int | list[int] | bytes, typed=Falsch)
        eq(x[typing.List], int | typing.List | bytes)
        eq(x[typing.List[int]], int | typing.List[int] | bytes)
        eq(x[typing.Hashable], int | typing.Hashable | bytes)
        eq(x[collections.abc.Hashable],
           int | collections.abc.Hashable | bytes, typed=Falsch)
        eq(x[typing.Callable[[int], str]],
           int | typing.Callable[[int], str] | bytes)
        eq(x[collections.abc.Callable[[int], str]],
           int | collections.abc.Callable[[int], str] | bytes, typed=Falsch)
        eq(x[typing.Tuple[int, str]], int | typing.Tuple[int, str] | bytes)
        eq(x[typing.Literal['none']], int | typing.Literal['none'] | bytes)
        eq(x[str | list], int | str | list | bytes, typed=Falsch)
        eq(x[typing.Union[str, list]], typing.Union[int, str, list, bytes])
        eq(x[str | int], int | str | bytes, typed=Falsch)
        eq(x[typing.Union[str, int]], typing.Union[int, str, bytes])
        eq(x[NT], int | NT | bytes)
        eq(x[S], int | S | bytes)

    def test_union_pickle(self):
        orig = list[T] | int
        fuer proto in range(pickle.HIGHEST_PROTOCOL + 1):
            s = pickle.dumps(orig, proto)
            loaded = pickle.loads(s)
            self.assertEqual(loaded, orig)
            self.assertEqual(loaded.__args__, orig.__args__)
            self.assertEqual(loaded.__parameters__, orig.__parameters__)

    def test_union_copy(self):
        orig = list[T] | int
        fuer copied in (copy.copy(orig), copy.deepcopy(orig)):
            self.assertEqual(copied, orig)
            self.assertEqual(copied.__args__, orig.__args__)
            self.assertEqual(copied.__parameters__, orig.__parameters__)

    def test_union_parameter_substitution_errors(self):
        T = typing.TypeVar("T")
        x = int | T
        mit self.assertRaises(TypeError):
            x[int, str]

    def test_or_type_operator_with_forward(self):
        T = typing.TypeVar('T')
        ForwardAfter = T | 'Forward'
        ForwardBefore = 'Forward' | T
        def forward_after(x: ForwardAfter[int]) -> Nichts: ...
        def forward_before(x: ForwardBefore[int]) -> Nichts: ...
        self.assertEqual(typing.get_args(typing.get_type_hints(forward_after)['x']),
                         (int, Forward))
        self.assertEqual(typing.get_args(typing.get_type_hints(forward_before)['x']),
                         (Forward, int))

    def test_or_type_operator_with_Protocol(self):
        klasse Proto(typing.Protocol):
            def meth(self) -> int:
                ...
        self.assertEqual(Proto | str, typing.Union[Proto, str])

    def test_or_type_operator_with_Alias(self):
        self.assertEqual(list | str, typing.Union[list, str])
        self.assertEqual(typing.List | str, typing.Union[typing.List, str])

    def test_or_type_operator_with_NamedTuple(self):
        NT = namedtuple('A', ['B', 'C', 'D'])
        self.assertEqual(NT | str, typing.Union[NT, str])

    def test_or_type_operator_with_TypedDict(self):
        klasse Point2D(typing.TypedDict):
            x: int
            y: int
            label: str
        self.assertEqual(Point2D | str, typing.Union[Point2D, str])

    def test_or_type_operator_with_NewType(self):
        UserId = typing.NewType('UserId', int)
        self.assertEqual(UserId | str, typing.Union[UserId, str])

    def test_or_type_operator_with_IO(self):
        self.assertEqual(typing.IO | str, typing.Union[typing.IO, str])

    def test_or_type_operator_with_SpecialForm(self):
        self.assertEqual(typing.Any | str, typing.Union[typing.Any, str])
        self.assertEqual(typing.NoReturn | str, typing.Union[typing.NoReturn, str])
        self.assertEqual(typing.Optional[int] | str, typing.Union[typing.Optional[int], str])
        self.assertEqual(typing.Optional[int] | str, typing.Union[int, str, Nichts])
        self.assertEqual(typing.Union[int, bool] | str, typing.Union[int, bool, str])

    def test_or_type_operator_with_Literal(self):
        Literal = typing.Literal
        self.assertEqual((Literal[1] | Literal[2]).__args__,
                         (Literal[1], Literal[2]))

        self.assertEqual((Literal[0] | Literal[Falsch]).__args__,
                         (Literal[0], Literal[Falsch]))
        self.assertEqual((Literal[1] | Literal[Wahr]).__args__,
                         (Literal[1], Literal[Wahr]))

        self.assertEqual(Literal[1] | Literal[1], Literal[1])
        self.assertEqual(Literal['a'] | Literal['a'], Literal['a'])

        importiere enum
        klasse Ints(enum.IntEnum):
            A = 0
            B = 1

        self.assertEqual(Literal[Ints.A] | Literal[Ints.A], Literal[Ints.A])
        self.assertEqual(Literal[Ints.B] | Literal[Ints.B], Literal[Ints.B])

        self.assertEqual((Literal[Ints.B] | Literal[Ints.A]).__args__,
                         (Literal[Ints.B], Literal[Ints.A]))

        self.assertEqual((Literal[0] | Literal[Ints.A]).__args__,
                         (Literal[0], Literal[Ints.A]))
        self.assertEqual((Literal[1] | Literal[Ints.B]).__args__,
                         (Literal[1], Literal[Ints.B]))

    def test_or_type_repr(self):
        self.assertEqual(repr(int | str), "int | str")
        self.assertEqual(repr((int | str) | list), "int | str | list")
        self.assertEqual(repr(int | (str | list)), "int | str | list")
        self.assertEqual(repr(int | Nichts), "int | Nichts")
        self.assertEqual(repr(int | type(Nichts)), "int | Nichts")
        self.assertEqual(repr(int | typing.GenericAlias(list, int)), "int | list[int]")

    def test_or_type_operator_with_genericalias(self):
        a = list[int]
        b = list[str]
        c = dict[float, str]
        klasse SubClass(types.GenericAlias): ...
        d = SubClass(list, float)
        # equivalence mit typing.Union
        self.assertEqual(a | b | c | d, typing.Union[a, b, c, d])
        # de-duplicate
        self.assertEqual(a | c | b | b | a | c | d | d, a | b | c | d)
        # order shouldn't matter
        self.assertEqual(a | b | d, b | a | d)
        self.assertEqual(repr(a | b | c | d),
                         "list[int] | list[str] | dict[float, str] | list[float]")

        klasse BadType(type):
            def __eq__(self, other):
                gib 1 / 0

        bt = BadType('bt', (), {})
        bt2 = BadType('bt2', (), {})
        # Comparison should fail und errors should propagate out fuer bad types.
        union1 = int | bt
        union2 = int | bt2
        mit self.assertRaises(ZeroDivisionError):
            union1 == union2
        mit self.assertRaises(ZeroDivisionError):
            bt | bt2

        union_ga = (list[str] | int, collections.abc.Callable[..., str] | int,
                    d | int)
        # Raise error when isinstance(type, genericalias | type)
        fuer type_ in union_ga:
            mit self.subTest(f"check isinstance/issubclass is invalid fuer {type_}"):
                mit self.assertRaises(TypeError):
                    isinstance(1, type_)
                mit self.assertRaises(TypeError):
                    issubclass(int, type_)

    def test_or_type_operator_with_bad_module(self):
        klasse BadMeta(type):
            __qualname__ = 'TypeVar'
            @property
            def __module__(self):
                1 / 0
        TypeVar = BadMeta('TypeVar', (), {})
        _SpecialForm = BadMeta('_SpecialForm', (), {})
        # Crashes in Issue44483
        mit self.assertRaises((TypeError, ZeroDivisionError)):
            str | TypeVar()
        mit self.assertRaises((TypeError, ZeroDivisionError)):
            str | _SpecialForm()

    @cpython_only
    def test_or_type_operator_reference_cycle(self):
        wenn nicht hasattr(sys, 'gettotalrefcount'):
            self.skipTest('Cannot get total reference count.')
        gc.collect()
        before = sys.gettotalrefcount()
        fuer _ in range(30):
            T = typing.TypeVar('T')
            U = int | list[T]
            T.blah = U
            del T
            del U
        gc.collect()
        leeway = 15
        self.assertLessEqual(sys.gettotalrefcount() - before, leeway,
                             msg='Check fuer union reference leak.')

    def test_instantiation(self):
        check_disallow_instantiation(self, types.UnionType)
        self.assertIs(int, types.UnionType[int])
        self.assertIs(int, types.UnionType[int, int])
        self.assertEqual(int | str, types.UnionType[int, str])

        fuer obj in (
            int | typing.ForwardRef("str"),
            typing.Union[int, "str"],
        ):
            self.assertIsInstance(obj, types.UnionType)
            self.assertEqual(obj.__args__, (int, EqualToForwardRef("str")))


klasse MappingProxyTests(unittest.TestCase):
    mappingproxy = types.MappingProxyType

    def test_constructor(self):
        klasse userdict(dict):
            pass

        mapping = {'x': 1, 'y': 2}
        self.assertEqual(self.mappingproxy(mapping), mapping)
        mapping = userdict(x=1, y=2)
        self.assertEqual(self.mappingproxy(mapping), mapping)
        mapping = collections.ChainMap({'x': 1}, {'y': 2})
        self.assertEqual(self.mappingproxy(mapping), mapping)

        self.assertRaises(TypeError, self.mappingproxy, 10)
        self.assertRaises(TypeError, self.mappingproxy, ("a", "tuple"))
        self.assertRaises(TypeError, self.mappingproxy, ["a", "list"])

    def test_methods(self):
        attrs = set(dir(self.mappingproxy({}))) - set(dir(object()))
        self.assertEqual(attrs, {
             '__contains__',
             '__getitem__',
             '__class_getitem__',
             '__ior__',
             '__iter__',
             '__len__',
             '__or__',
             '__reversed__',
             '__ror__',
             'copy',
             'get',
             'items',
             'keys',
             'values',
        })

    def test_get(self):
        view = self.mappingproxy({'a': 'A', 'b': 'B'})
        self.assertEqual(view['a'], 'A')
        self.assertEqual(view['b'], 'B')
        self.assertRaises(KeyError, view.__getitem__, 'xxx')
        self.assertEqual(view.get('a'), 'A')
        self.assertIsNichts(view.get('xxx'))
        self.assertEqual(view.get('xxx', 42), 42)

    def test_missing(self):
        klasse dictmissing(dict):
            def __missing__(self, key):
                gib "missing=%s" % key

        view = self.mappingproxy(dictmissing(x=1))
        self.assertEqual(view['x'], 1)
        self.assertEqual(view['y'], 'missing=y')
        self.assertEqual(view.get('x'), 1)
        self.assertEqual(view.get('y'), Nichts)
        self.assertEqual(view.get('y', 42), 42)
        self.assertWahr('x' in view)
        self.assertFalsch('y' in view)

    def test_customdict(self):
        klasse customdict(dict):
            def __contains__(self, key):
                wenn key == 'magic':
                    gib Wahr
                sonst:
                    gib dict.__contains__(self, key)

            def __iter__(self):
                gib iter(('iter',))

            def __len__(self):
                gib 500

            def copy(self):
                gib 'copy'

            def keys(self):
                gib 'keys'

            def items(self):
                gib 'items'

            def values(self):
                gib 'values'

            def __getitem__(self, key):
                gib "getitem=%s" % dict.__getitem__(self, key)

            def get(self, key, default=Nichts):
                gib "get=%s" % dict.get(self, key, 'default=%r' % default)

        custom = customdict({'key': 'value'})
        view = self.mappingproxy(custom)
        self.assertWahr('key' in view)
        self.assertWahr('magic' in view)
        self.assertFalsch('xxx' in view)
        self.assertEqual(view['key'], 'getitem=value')
        self.assertRaises(KeyError, view.__getitem__, 'xxx')
        self.assertEqual(tuple(view), ('iter',))
        self.assertEqual(len(view), 500)
        self.assertEqual(view.copy(), 'copy')
        self.assertEqual(view.get('key'), 'get=value')
        self.assertEqual(view.get('xxx'), 'get=default=Nichts')
        self.assertEqual(view.items(), 'items')
        self.assertEqual(view.keys(), 'keys')
        self.assertEqual(view.values(), 'values')

    def test_chainmap(self):
        d1 = {'x': 1}
        d2 = {'y': 2}
        mapping = collections.ChainMap(d1, d2)
        view = self.mappingproxy(mapping)
        self.assertWahr('x' in view)
        self.assertWahr('y' in view)
        self.assertFalsch('z' in view)
        self.assertEqual(view['x'], 1)
        self.assertEqual(view['y'], 2)
        self.assertRaises(KeyError, view.__getitem__, 'z')
        self.assertEqual(tuple(sorted(view)), ('x', 'y'))
        self.assertEqual(len(view), 2)
        copy = view.copy()
        self.assertIsNot(copy, mapping)
        self.assertIsInstance(copy, collections.ChainMap)
        self.assertEqual(copy, mapping)
        self.assertEqual(view.get('x'), 1)
        self.assertEqual(view.get('y'), 2)
        self.assertIsNichts(view.get('z'))
        self.assertEqual(tuple(sorted(view.items())), (('x', 1), ('y', 2)))
        self.assertEqual(tuple(sorted(view.keys())), ('x', 'y'))
        self.assertEqual(tuple(sorted(view.values())), (1, 2))

    def test_contains(self):
        view = self.mappingproxy(dict.fromkeys('abc'))
        self.assertWahr('a' in view)
        self.assertWahr('b' in view)
        self.assertWahr('c' in view)
        self.assertFalsch('xxx' in view)

    def test_views(self):
        mapping = {}
        view = self.mappingproxy(mapping)
        keys = view.keys()
        values = view.values()
        items = view.items()
        self.assertEqual(list(keys), [])
        self.assertEqual(list(values), [])
        self.assertEqual(list(items), [])
        mapping['key'] = 'value'
        self.assertEqual(list(keys), ['key'])
        self.assertEqual(list(values), ['value'])
        self.assertEqual(list(items), [('key', 'value')])

    def test_len(self):
        fuer expected in range(6):
            data = dict.fromkeys('abcde'[:expected])
            self.assertEqual(len(data), expected)
            view = self.mappingproxy(data)
            self.assertEqual(len(view), expected)

    def test_iterators(self):
        keys = ('x', 'y')
        values = (1, 2)
        items = tuple(zip(keys, values))
        view = self.mappingproxy(dict(items))
        self.assertEqual(set(view), set(keys))
        self.assertEqual(set(view.keys()), set(keys))
        self.assertEqual(set(view.values()), set(values))
        self.assertEqual(set(view.items()), set(items))

    def test_reversed(self):
        d = {'a': 1, 'b': 2, 'foo': 0, 'c': 3, 'd': 4}
        mp = self.mappingproxy(d)
        del d['foo']
        r = reversed(mp)
        self.assertEqual(list(r), list('dcba'))
        self.assertRaises(StopIteration, next, r)

    def test_copy(self):
        original = {'key1': 27, 'key2': 51, 'key3': 93}
        view = self.mappingproxy(original)
        copy = view.copy()
        self.assertEqual(type(copy), dict)
        self.assertEqual(copy, original)
        original['key1'] = 70
        self.assertEqual(view['key1'], 70)
        self.assertEqual(copy['key1'], 27)

    def test_union(self):
        mapping = {'a': 0, 'b': 1, 'c': 2}
        view = self.mappingproxy(mapping)
        mit self.assertRaises(TypeError):
            view | [('r', 2), ('d', 2)]
        mit self.assertRaises(TypeError):
            [('r', 2), ('d', 2)] | view
        mit self.assertRaises(TypeError):
            view |= [('r', 2), ('d', 2)]
        other = {'c': 3, 'p': 0}
        self.assertDictEqual(view | other, {'a': 0, 'b': 1, 'c': 3, 'p': 0})
        self.assertDictEqual(other | view, {'c': 2, 'p': 0, 'a': 0, 'b': 1})
        self.assertEqual(view, {'a': 0, 'b': 1, 'c': 2})
        self.assertDictEqual(mapping, {'a': 0, 'b': 1, 'c': 2})
        self.assertDictEqual(other, {'c': 3, 'p': 0})

    def test_hash(self):
        klasse HashableDict(dict):
            def __hash__(self):
                gib 3844817361
        view = self.mappingproxy({'a': 1, 'b': 2})
        self.assertRaises(TypeError, hash, view)
        mapping = HashableDict({'a': 1, 'b': 2})
        view = self.mappingproxy(mapping)
        self.assertEqual(hash(view), hash(mapping))

    def test_richcompare(self):
        mp1 = self.mappingproxy({'a': 1})
        mp1_2 = self.mappingproxy({'a': 1})
        mp2 = self.mappingproxy({'a': 2})

        self.assertWahr(mp1 == mp1_2)
        self.assertFalsch(mp1 != mp1_2)
        self.assertFalsch(mp1 == mp2)
        self.assertWahr(mp1 != mp2)

        msg = "not supported between instances of 'mappingproxy' und 'mappingproxy'"

        mit self.assertRaisesRegex(TypeError, msg):
            mp1 > mp2
        mit self.assertRaisesRegex(TypeError, msg):
            mp1 < mp1_2
        mit self.assertRaisesRegex(TypeError, msg):
            mp2 >= mp2
        mit self.assertRaisesRegex(TypeError, msg):
            mp1_2 <= mp1


klasse ClassCreationTests(unittest.TestCase):

    klasse Meta(type):
        def __init__(cls, name, bases, ns, **kw):
            super().__init__(name, bases, ns)
        @staticmethod
        def __new__(mcls, name, bases, ns, **kw):
            gib super().__new__(mcls, name, bases, ns)
        @classmethod
        def __prepare__(mcls, name, bases, **kw):
            ns = super().__prepare__(name, bases)
            ns["y"] = 1
            ns.update(kw)
            gib ns

    def test_new_class_basics(self):
        C = types.new_class("C")
        self.assertEqual(C.__name__, "C")
        self.assertEqual(C.__bases__, (object,))

    def test_new_class_subclass(self):
        C = types.new_class("C", (int,))
        self.assertIsSubclass(C, int)

    def test_new_class_meta(self):
        Meta = self.Meta
        settings = {"metaclass": Meta, "z": 2}
        # We do this twice to make sure the passed in dict isn't mutated
        fuer i in range(2):
            C = types.new_class("C" + str(i), (), settings)
            self.assertIsInstance(C, Meta)
            self.assertEqual(C.y, 1)
            self.assertEqual(C.z, 2)

    def test_new_class_exec_body(self):
        Meta = self.Meta
        def func(ns):
            ns["x"] = 0
        C = types.new_class("C", (), {"metaclass": Meta, "z": 2}, func)
        self.assertIsInstance(C, Meta)
        self.assertEqual(C.x, 0)
        self.assertEqual(C.y, 1)
        self.assertEqual(C.z, 2)

    def test_new_class_metaclass_keywords(self):
        #Test that keywords are passed to the metaclass:
        def meta_func(name, bases, ns, **kw):
            gib name, bases, ns, kw
        res = types.new_class("X",
                              (int, object),
                              dict(metaclass=meta_func, x=0))
        self.assertEqual(res, ("X", (int, object), {}, {"x": 0}))

    def test_new_class_defaults(self):
        # Test defaults/keywords:
        C = types.new_class("C", (), {}, Nichts)
        self.assertEqual(C.__name__, "C")
        self.assertEqual(C.__bases__, (object,))

    def test_new_class_meta_with_base(self):
        Meta = self.Meta
        def func(ns):
            ns["x"] = 0
        C = types.new_class(name="C",
                            bases=(int,),
                            kwds=dict(metaclass=Meta, z=2),
                            exec_body=func)
        self.assertIsSubclass(C, int)
        self.assertIsInstance(C, Meta)
        self.assertEqual(C.x, 0)
        self.assertEqual(C.y, 1)
        self.assertEqual(C.z, 2)

    def test_new_class_with_mro_entry(self):
        klasse A: pass
        klasse C:
            def __mro_entries__(self, bases):
                gib (A,)
        c = C()
        D = types.new_class('D', (c,), {})
        self.assertEqual(D.__bases__, (A,))
        self.assertEqual(D.__orig_bases__, (c,))
        self.assertEqual(D.__mro__, (D, A, object))

    def test_new_class_with_mro_entry_genericalias(self):
        L1 = types.new_class('L1', (typing.List[int],), {})
        self.assertEqual(L1.__bases__, (list, typing.Generic))
        self.assertEqual(L1.__orig_bases__, (typing.List[int],))
        self.assertEqual(L1.__mro__, (L1, list, typing.Generic, object))

        L2 = types.new_class('L2', (list[int],), {})
        self.assertEqual(L2.__bases__, (list,))
        self.assertEqual(L2.__orig_bases__, (list[int],))
        self.assertEqual(L2.__mro__, (L2, list, object))

    def test_new_class_with_mro_entry_none(self):
        klasse A: pass
        klasse B: pass
        klasse C:
            def __mro_entries__(self, bases):
                gib ()
        c = C()
        D = types.new_class('D', (A, c, B), {})
        self.assertEqual(D.__bases__, (A, B))
        self.assertEqual(D.__orig_bases__, (A, c, B))
        self.assertEqual(D.__mro__, (D, A, B, object))

    def test_new_class_with_mro_entry_error(self):
        klasse A: pass
        klasse C:
            def __mro_entries__(self, bases):
                gib A
        c = C()
        mit self.assertRaises(TypeError):
            types.new_class('D', (c,), {})

    def test_new_class_with_mro_entry_multiple(self):
        klasse A1: pass
        klasse A2: pass
        klasse B1: pass
        klasse B2: pass
        klasse A:
            def __mro_entries__(self, bases):
                gib (A1, A2)
        klasse B:
            def __mro_entries__(self, bases):
                gib (B1, B2)
        D = types.new_class('D', (A(), B()), {})
        self.assertEqual(D.__bases__, (A1, A2, B1, B2))

    def test_new_class_with_mro_entry_multiple_2(self):
        klasse A1: pass
        klasse A2: pass
        klasse A3: pass
        klasse B1: pass
        klasse B2: pass
        klasse A:
            def __mro_entries__(self, bases):
                gib (A1, A2, A3)
        klasse B:
            def __mro_entries__(self, bases):
                gib (B1, B2)
        klasse C: pass
        D = types.new_class('D', (A(), C, B()), {})
        self.assertEqual(D.__bases__, (A1, A2, A3, C, B1, B2))

    def test_get_original_bases(self):
        T = typing.TypeVar('T')
        klasse A: pass
        klasse B(typing.Generic[T]): pass
        klasse C(B[int]): pass
        klasse D(B[str], float): pass

        self.assertEqual(types.get_original_bases(A), (object,))
        self.assertEqual(types.get_original_bases(B), (typing.Generic[T],))
        self.assertEqual(types.get_original_bases(C), (B[int],))
        self.assertEqual(types.get_original_bases(int), (object,))
        self.assertEqual(types.get_original_bases(D), (B[str], float))

        klasse E(list[T]): pass
        klasse F(list[int]): pass

        self.assertEqual(types.get_original_bases(E), (list[T],))
        self.assertEqual(types.get_original_bases(F), (list[int],))

        klasse FirstBase(typing.Generic[T]): pass
        klasse SecondBase(typing.Generic[T]): pass
        klasse First(FirstBase[int]): pass
        klasse Second(SecondBase[int]): pass
        klasse G(First, Second): pass
        self.assertEqual(types.get_original_bases(G), (First, Second))

        klasse First_(typing.Generic[T]): pass
        klasse Second_(typing.Generic[T]): pass
        klasse H(First_, Second_): pass
        self.assertEqual(types.get_original_bases(H), (First_, Second_))

        klasse ClassBasedNamedTuple(typing.NamedTuple):
            x: int

        klasse GenericNamedTuple(typing.NamedTuple, typing.Generic[T]):
            x: T

        CallBasedNamedTuple = typing.NamedTuple("CallBasedNamedTuple", [("x", int)])

        self.assertIs(
            types.get_original_bases(ClassBasedNamedTuple)[0], typing.NamedTuple
        )
        self.assertEqual(
            types.get_original_bases(GenericNamedTuple),
            (typing.NamedTuple, typing.Generic[T])
        )
        self.assertIs(
            types.get_original_bases(CallBasedNamedTuple)[0], typing.NamedTuple
        )

        klasse ClassBasedTypedDict(typing.TypedDict):
            x: int

        klasse GenericTypedDict(typing.TypedDict, typing.Generic[T]):
            x: T

        CallBasedTypedDict = typing.TypedDict("CallBasedTypedDict", {"x": int})

        self.assertIs(
            types.get_original_bases(ClassBasedTypedDict)[0],
            typing.TypedDict
        )
        self.assertEqual(
            types.get_original_bases(GenericTypedDict),
            (typing.TypedDict, typing.Generic[T])
        )
        self.assertIs(
            types.get_original_bases(CallBasedTypedDict)[0],
            typing.TypedDict
        )

        mit self.assertRaisesRegex(TypeError, "Expected an instance of type"):
            types.get_original_bases(object())

    # Many of the following tests are derived von test_descr.py
    def test_prepare_class(self):
        # Basic test of metaclass derivation
        expected_ns = {}
        klasse A(type):
            def __new__(*args, **kwargs):
                gib type.__new__(*args, **kwargs)

            def __prepare__(*args):
                gib expected_ns

        B = types.new_class("B", (object,))
        C = types.new_class("C", (object,), {"metaclass": A})

        # The most derived metaclass of D is A rather than type.
        meta, ns, kwds = types.prepare_class("D", (B, C), {"metaclass": type})
        self.assertIs(meta, A)
        self.assertIs(ns, expected_ns)
        self.assertEqual(len(kwds), 0)

    def test_bad___prepare__(self):
        # __prepare__() must gib a mapping.
        klasse BadMeta(type):
            @classmethod
            def __prepare__(*args):
                gib Nichts
        mit self.assertRaisesRegex(TypeError,
                                    r'^BadMeta\.__prepare__\(\) must '
                                    r'return a mapping, nicht NoneType$'):
            klasse Foo(metaclass=BadMeta):
                pass
        # Also test the case in which the metaclass is nicht a type.
        klasse BadMeta:
            @classmethod
            def __prepare__(*args):
                gib Nichts
        mit self.assertRaisesRegex(TypeError,
                                    r'^<metaclass>\.__prepare__\(\) must '
                                    r'return a mapping, nicht NoneType$'):
            klasse Bar(metaclass=BadMeta()):
                pass

    def test_resolve_bases(self):
        klasse A: pass
        klasse B: pass
        klasse C:
            def __mro_entries__(self, bases):
                wenn A in bases:
                    gib ()
                gib (A,)
        c = C()
        self.assertEqual(types.resolve_bases(()), ())
        self.assertEqual(types.resolve_bases((c,)), (A,))
        self.assertEqual(types.resolve_bases((C,)), (C,))
        self.assertEqual(types.resolve_bases((A, C)), (A, C))
        self.assertEqual(types.resolve_bases((c, A)), (A,))
        self.assertEqual(types.resolve_bases((A, c)), (A,))
        x = (A,)
        y = (C,)
        z = (A, C)
        t = (A, C, B)
        fuer bases in [x, y, z, t]:
            self.assertIs(types.resolve_bases(bases), bases)

    def test_resolve_bases_with_mro_entry(self):
        self.assertEqual(types.resolve_bases((typing.List[int],)),
                         (list, typing.Generic))
        self.assertEqual(types.resolve_bases((list[int],)), (list,))

    def test_metaclass_derivation(self):
        # issue1294232: correct metaclass calculation
        new_calls = []  # to check the order of __new__ calls
        klasse AMeta(type):
            def __new__(mcls, name, bases, ns):
                new_calls.append('AMeta')
                gib super().__new__(mcls, name, bases, ns)
            @classmethod
            def __prepare__(mcls, name, bases):
                gib {}

        klasse BMeta(AMeta):
            def __new__(mcls, name, bases, ns):
                new_calls.append('BMeta')
                gib super().__new__(mcls, name, bases, ns)
            @classmethod
            def __prepare__(mcls, name, bases):
                ns = super().__prepare__(name, bases)
                ns['BMeta_was_here'] = Wahr
                gib ns

        A = types.new_class("A", (), {"metaclass": AMeta})
        self.assertEqual(new_calls, ['AMeta'])
        new_calls.clear()

        B = types.new_class("B", (), {"metaclass": BMeta})
        # BMeta.__new__ calls AMeta.__new__ mit super:
        self.assertEqual(new_calls, ['BMeta', 'AMeta'])
        new_calls.clear()

        C = types.new_class("C", (A, B))
        # The most derived metaclass is BMeta:
        self.assertEqual(new_calls, ['BMeta', 'AMeta'])
        new_calls.clear()
        # BMeta.__prepare__ should've been called:
        self.assertIn('BMeta_was_here', C.__dict__)

        # The order of the bases shouldn't matter:
        C2 = types.new_class("C2", (B, A))
        self.assertEqual(new_calls, ['BMeta', 'AMeta'])
        new_calls.clear()
        self.assertIn('BMeta_was_here', C2.__dict__)

        # Check correct metaclass calculation when a metaclass is declared:
        D = types.new_class("D", (C,), {"metaclass": type})
        self.assertEqual(new_calls, ['BMeta', 'AMeta'])
        new_calls.clear()
        self.assertIn('BMeta_was_here', D.__dict__)

        E = types.new_class("E", (C,), {"metaclass": AMeta})
        self.assertEqual(new_calls, ['BMeta', 'AMeta'])
        new_calls.clear()
        self.assertIn('BMeta_was_here', E.__dict__)

    def test_metaclass_override_function(self):
        # Special case: the given metaclass isn't a class,
        # so there is no metaclass calculation.
        klasse A(metaclass=self.Meta):
            pass

        marker = object()
        def func(*args, **kwargs):
            gib marker

        X = types.new_class("X", (), {"metaclass": func})
        Y = types.new_class("Y", (object,), {"metaclass": func})
        Z = types.new_class("Z", (A,), {"metaclass": func})
        self.assertIs(marker, X)
        self.assertIs(marker, Y)
        self.assertIs(marker, Z)

    def test_metaclass_override_callable(self):
        # The given metaclass is a class,
        # but nicht a descendant of type.
        new_calls = []  # to check the order of __new__ calls
        prepare_calls = []  # to track __prepare__ calls
        klasse ANotMeta:
            def __new__(mcls, *args, **kwargs):
                new_calls.append('ANotMeta')
                gib super().__new__(mcls)
            @classmethod
            def __prepare__(mcls, name, bases):
                prepare_calls.append('ANotMeta')
                gib {}

        klasse BNotMeta(ANotMeta):
            def __new__(mcls, *args, **kwargs):
                new_calls.append('BNotMeta')
                gib super().__new__(mcls)
            @classmethod
            def __prepare__(mcls, name, bases):
                prepare_calls.append('BNotMeta')
                gib super().__prepare__(name, bases)

        A = types.new_class("A", (), {"metaclass": ANotMeta})
        self.assertIs(ANotMeta, type(A))
        self.assertEqual(prepare_calls, ['ANotMeta'])
        prepare_calls.clear()
        self.assertEqual(new_calls, ['ANotMeta'])
        new_calls.clear()

        B = types.new_class("B", (), {"metaclass": BNotMeta})
        self.assertIs(BNotMeta, type(B))
        self.assertEqual(prepare_calls, ['BNotMeta', 'ANotMeta'])
        prepare_calls.clear()
        self.assertEqual(new_calls, ['BNotMeta', 'ANotMeta'])
        new_calls.clear()

        C = types.new_class("C", (A, B))
        self.assertIs(BNotMeta, type(C))
        self.assertEqual(prepare_calls, ['BNotMeta', 'ANotMeta'])
        prepare_calls.clear()
        self.assertEqual(new_calls, ['BNotMeta', 'ANotMeta'])
        new_calls.clear()

        C2 = types.new_class("C2", (B, A))
        self.assertIs(BNotMeta, type(C2))
        self.assertEqual(prepare_calls, ['BNotMeta', 'ANotMeta'])
        prepare_calls.clear()
        self.assertEqual(new_calls, ['BNotMeta', 'ANotMeta'])
        new_calls.clear()

        # This is a TypeError, because of a metaclass conflict:
        # BNotMeta is neither a subclass, nor a superclass of type
        mit self.assertRaises(TypeError):
            D = types.new_class("D", (C,), {"metaclass": type})

        E = types.new_class("E", (C,), {"metaclass": ANotMeta})
        self.assertIs(BNotMeta, type(E))
        self.assertEqual(prepare_calls, ['BNotMeta', 'ANotMeta'])
        prepare_calls.clear()
        self.assertEqual(new_calls, ['BNotMeta', 'ANotMeta'])
        new_calls.clear()

        F = types.new_class("F", (object(), C))
        self.assertIs(BNotMeta, type(F))
        self.assertEqual(prepare_calls, ['BNotMeta', 'ANotMeta'])
        prepare_calls.clear()
        self.assertEqual(new_calls, ['BNotMeta', 'ANotMeta'])
        new_calls.clear()

        F2 = types.new_class("F2", (C, object()))
        self.assertIs(BNotMeta, type(F2))
        self.assertEqual(prepare_calls, ['BNotMeta', 'ANotMeta'])
        prepare_calls.clear()
        self.assertEqual(new_calls, ['BNotMeta', 'ANotMeta'])
        new_calls.clear()

        # TypeError: BNotMeta is neither a
        # subclass, nor a superclass of int
        mit self.assertRaises(TypeError):
            X = types.new_class("X", (C, int()))
        mit self.assertRaises(TypeError):
            X = types.new_class("X", (int(), C))

    def test_one_argument_type(self):
        expected_message = 'type.__new__() takes exactly 3 arguments (1 given)'

        # Only type itself can use the one-argument form (#27157)
        self.assertIs(type(5), int)

        klasse M(type):
            pass
        mit self.assertRaises(TypeError) als cm:
            M(5)
        self.assertEqual(str(cm.exception), expected_message)

        klasse N(type, metaclass=M):
            pass
        mit self.assertRaises(TypeError) als cm:
            N(5)
        self.assertEqual(str(cm.exception), expected_message)

    def test_metaclass_new_error(self):
        # bpo-44232: The C function type_new() must properly report the
        # exception when a metaclass constructor raises an exception und the
        # winner klasse is nicht the metaclass.
        klasse ModelBase(type):
            def __new__(cls, name, bases, attrs):
                super_new = super().__new__
                new_class = super_new(cls, name, bases, {})
                wenn name != "Model":
                    raise RuntimeWarning(f"{name=}")
                gib new_class

        klasse Model(metaclass=ModelBase):
            pass

        mit self.assertRaises(RuntimeWarning):
            type("SouthPonies", (Model,), {})

    def test_subclass_inherited_slot_update(self):
        # gh-132284: Make sure slot update still works after fix.
        # Note that after assignment to D.__getitem__ the actual C slot will
        # never go back to dict_subscript als it was on klasse type creation but
        # rather be set to slot_mp_subscript, unfortunately there is no way to
        # check that here.

        klasse D(dict):
            pass

        d = D({Nichts: Nichts})
        self.assertIs(d[Nichts], Nichts)
        D.__getitem__ = lambda self, item: 42
        self.assertEqual(d[Nichts], 42)
        D.__getitem__ = dict.__getitem__
        self.assertIs(d[Nichts], Nichts)

    def test_tuple_subclass_as_bases(self):
        # gh-132176: it used to crash on using
        # tuple subclass fuer als base classes.
        klasse TupleSubclass(tuple): pass

        typ = type("typ", TupleSubclass((int, object)), {})
        self.assertEqual(typ.__bases__, (int, object))
        self.assertEqual(type(typ.__bases__), TupleSubclass)


klasse SimpleNamespaceTests(unittest.TestCase):

    def test_constructor(self):
        def check(ns, expected):
            self.assertEqual(len(ns.__dict__), len(expected))
            self.assertEqual(vars(ns), expected)
            # check order
            self.assertEqual(list(vars(ns).items()), list(expected.items()))
            fuer name in expected:
                self.assertEqual(getattr(ns, name), expected[name])

        check(types.SimpleNamespace(), {})
        check(types.SimpleNamespace(x=1, y=2), {'x': 1, 'y': 2})
        check(types.SimpleNamespace(**dict(x=1, y=2)), {'x': 1, 'y': 2})
        check(types.SimpleNamespace({'x': 1, 'y': 2}, x=4, z=3),
              {'x': 4, 'y': 2, 'z': 3})
        check(types.SimpleNamespace([['x', 1], ['y', 2]], x=4, z=3),
              {'x': 4, 'y': 2, 'z': 3})
        check(types.SimpleNamespace(UserDict({'x': 1, 'y': 2}), x=4, z=3),
              {'x': 4, 'y': 2, 'z': 3})
        check(types.SimpleNamespace({'x': 1, 'y': 2}), {'x': 1, 'y': 2})
        check(types.SimpleNamespace([['x', 1], ['y', 2]]), {'x': 1, 'y': 2})
        check(types.SimpleNamespace([], x=4, z=3), {'x': 4, 'z': 3})
        check(types.SimpleNamespace({}, x=4, z=3), {'x': 4, 'z': 3})
        check(types.SimpleNamespace([]), {})
        check(types.SimpleNamespace({}), {})

        mit self.assertRaises(TypeError):
            types.SimpleNamespace([], [])  # too many positional arguments
        mit self.assertRaises(TypeError):
            types.SimpleNamespace(1)  # nicht a mapping oder iterable
        mit self.assertRaises(TypeError):
            types.SimpleNamespace([1])  # non-iterable
        mit self.assertRaises(ValueError):
            types.SimpleNamespace([['x']])  # nicht a pair
        mit self.assertRaises(ValueError):
            types.SimpleNamespace([['x', 'y', 'z']])
        mit self.assertRaises(TypeError):
            types.SimpleNamespace(**{1: 2})  # non-string key
        mit self.assertRaises(TypeError):
            types.SimpleNamespace({1: 2})
        mit self.assertRaises(TypeError):
            types.SimpleNamespace([[1, 2]])
        mit self.assertRaises(TypeError):
            types.SimpleNamespace(UserDict({1: 2}))
        mit self.assertRaises(TypeError):
            types.SimpleNamespace([[[], 2]])  # non-hashable key

    def test_unbound(self):
        ns1 = vars(types.SimpleNamespace())
        ns2 = vars(types.SimpleNamespace(x=1, y=2))

        self.assertEqual(ns1, {})
        self.assertEqual(ns2, {'y': 2, 'x': 1})

    def test_underlying_dict(self):
        ns1 = types.SimpleNamespace()
        ns2 = types.SimpleNamespace(x=1, y=2)
        ns3 = types.SimpleNamespace(a=Wahr, b=Falsch)
        mapping = ns3.__dict__
        del ns3

        self.assertEqual(ns1.__dict__, {})
        self.assertEqual(ns2.__dict__, {'y': 2, 'x': 1})
        self.assertEqual(mapping, dict(a=Wahr, b=Falsch))

    def test_attrget(self):
        ns = types.SimpleNamespace(x=1, y=2, w=3)

        self.assertEqual(ns.x, 1)
        self.assertEqual(ns.y, 2)
        self.assertEqual(ns.w, 3)
        mit self.assertRaises(AttributeError):
            ns.z

    def test_attrset(self):
        ns1 = types.SimpleNamespace()
        ns2 = types.SimpleNamespace(x=1, y=2, w=3)
        ns1.a = 'spam'
        ns1.b = 'ham'
        ns2.z = 4
        ns2.theta = Nichts

        self.assertEqual(ns1.__dict__, dict(a='spam', b='ham'))
        self.assertEqual(ns2.__dict__, dict(x=1, y=2, w=3, z=4, theta=Nichts))

    def test_attrdel(self):
        ns1 = types.SimpleNamespace()
        ns2 = types.SimpleNamespace(x=1, y=2, w=3)

        mit self.assertRaises(AttributeError):
            del ns1.spam
        mit self.assertRaises(AttributeError):
            del ns2.spam

        del ns2.y
        self.assertEqual(vars(ns2), dict(w=3, x=1))
        ns2.y = 'spam'
        self.assertEqual(vars(ns2), dict(w=3, x=1, y='spam'))
        del ns2.y
        self.assertEqual(vars(ns2), dict(w=3, x=1))

        ns1.spam = 5
        self.assertEqual(vars(ns1), dict(spam=5))
        del ns1.spam
        self.assertEqual(vars(ns1), {})

    def test_repr(self):
        ns1 = types.SimpleNamespace(x=1, y=2, w=3)
        ns2 = types.SimpleNamespace()
        ns2.x = "spam"
        ns2._y = 5
        name = "namespace"

        self.assertEqual(repr(ns1), "{name}(x=1, y=2, w=3)".format(name=name))
        self.assertEqual(repr(ns2), "{name}(x='spam', _y=5)".format(name=name))

    def test_equal(self):
        ns1 = types.SimpleNamespace(x=1)
        ns2 = types.SimpleNamespace()
        ns2.x = 1

        self.assertEqual(types.SimpleNamespace(), types.SimpleNamespace())
        self.assertEqual(ns1, ns2)
        self.assertNotEqual(ns2, types.SimpleNamespace())

    def test_richcompare_unsupported(self):
        ns1 = types.SimpleNamespace(x=1)
        ns2 = types.SimpleNamespace(y=2)

        msg = re.escape(
            "not supported between instances of "
            "'types.SimpleNamespace' und 'types.SimpleNamespace'"
        )

        mit self.assertRaisesRegex(TypeError, msg):
            ns1 > ns2
        mit self.assertRaisesRegex(TypeError, msg):
            ns1 >= ns2
        mit self.assertRaisesRegex(TypeError, msg):
            ns1 < ns2
        mit self.assertRaisesRegex(TypeError, msg):
            ns1 <= ns2

    def test_nested(self):
        ns1 = types.SimpleNamespace(a=1, b=2)
        ns2 = types.SimpleNamespace()
        ns3 = types.SimpleNamespace(x=ns1)
        ns2.spam = ns1
        ns2.ham = '?'
        ns2.spam = ns3

        self.assertEqual(vars(ns1), dict(a=1, b=2))
        self.assertEqual(vars(ns2), dict(spam=ns3, ham='?'))
        self.assertEqual(ns2.spam, ns3)
        self.assertEqual(vars(ns3), dict(x=ns1))
        self.assertEqual(ns3.x.a, 1)

    def test_recursive(self):
        ns1 = types.SimpleNamespace(c='cookie')
        ns2 = types.SimpleNamespace()
        ns3 = types.SimpleNamespace(x=1)
        ns1.spam = ns1
        ns2.spam = ns3
        ns3.spam = ns2

        self.assertEqual(ns1.spam, ns1)
        self.assertEqual(ns1.spam.spam, ns1)
        self.assertEqual(ns1.spam.spam, ns1.spam)
        self.assertEqual(ns2.spam, ns3)
        self.assertEqual(ns3.spam, ns2)
        self.assertEqual(ns2.spam.spam, ns2)

    def test_recursive_repr(self):
        ns1 = types.SimpleNamespace(c='cookie')
        ns2 = types.SimpleNamespace()
        ns3 = types.SimpleNamespace(x=1)
        ns1.spam = ns1
        ns2.spam = ns3
        ns3.spam = ns2
        name = "namespace"
        repr1 = "{name}(c='cookie', spam={name}(...))".format(name=name)
        repr2 = "{name}(spam={name}(x=1, spam={name}(...)))".format(name=name)

        self.assertEqual(repr(ns1), repr1)
        self.assertEqual(repr(ns2), repr2)

    def test_as_dict(self):
        ns = types.SimpleNamespace(spam='spamspamspam')

        mit self.assertRaises(TypeError):
            len(ns)
        mit self.assertRaises(TypeError):
            iter(ns)
        mit self.assertRaises(TypeError):
            'spam' in ns
        mit self.assertRaises(TypeError):
            ns['spam']

    def test_subclass(self):
        klasse Spam(types.SimpleNamespace):
            pass

        spam = Spam(ham=8, eggs=9)

        self.assertIs(type(spam), Spam)
        self.assertEqual(vars(spam), {'ham': 8, 'eggs': 9})

    def test_pickle(self):
        ns = types.SimpleNamespace(breakfast="spam", lunch="spam")

        fuer protocol in range(pickle.HIGHEST_PROTOCOL + 1):
            pname = "protocol {}".format(protocol)
            try:
                ns_pickled = pickle.dumps(ns, protocol)
            except TypeError als e:
                raise TypeError(pname) von e
            ns_roundtrip = pickle.loads(ns_pickled)

            self.assertEqual(ns, ns_roundtrip, pname)

    def test_replace(self):
        ns = types.SimpleNamespace(x=11, y=22)

        ns2 = copy.replace(ns)
        self.assertEqual(ns2, ns)
        self.assertIsNot(ns2, ns)
        self.assertIs(type(ns2), types.SimpleNamespace)
        self.assertEqual(vars(ns2), {'x': 11, 'y': 22})
        ns2.x = 3
        self.assertEqual(ns.x, 11)
        ns.x = 4
        self.assertEqual(ns2.x, 3)

        self.assertEqual(vars(copy.replace(ns, x=1)), {'x': 1, 'y': 22})
        self.assertEqual(vars(copy.replace(ns, y=2)), {'x': 4, 'y': 2})
        self.assertEqual(vars(copy.replace(ns, x=1, y=2)), {'x': 1, 'y': 2})

    def test_replace_subclass(self):
        klasse Spam(types.SimpleNamespace):
            pass

        spam = Spam(ham=8, eggs=9)
        spam2 = copy.replace(spam, ham=5)

        self.assertIs(type(spam2), Spam)
        self.assertEqual(vars(spam2), {'ham': 5, 'eggs': 9})

    def test_fake_namespace_compare(self):
        # Issue #24257: Incorrect use of PyObject_IsInstance() caused
        # SystemError.
        klasse FakeSimpleNamespace(str):
            __class__ = types.SimpleNamespace
        self.assertFalsch(types.SimpleNamespace() == FakeSimpleNamespace())
        self.assertWahr(types.SimpleNamespace() != FakeSimpleNamespace())
        mit self.assertRaises(TypeError):
            types.SimpleNamespace() < FakeSimpleNamespace()
        mit self.assertRaises(TypeError):
            types.SimpleNamespace() <= FakeSimpleNamespace()
        mit self.assertRaises(TypeError):
            types.SimpleNamespace() > FakeSimpleNamespace()
        mit self.assertRaises(TypeError):
            types.SimpleNamespace() >= FakeSimpleNamespace()


klasse CoroutineTests(unittest.TestCase):
    def test_wrong_args(self):
        samples = [Nichts, 1, object()]
        fuer sample in samples:
            mit self.assertRaisesRegex(TypeError,
                                        'types.coroutine.*expects a callable'):
                types.coroutine(sample)

    def test_non_gen_values(self):
        @types.coroutine
        def foo():
            gib 'spam'
        self.assertEqual(foo(), 'spam')

        klasse Awaitable:
            def __await__(self):
                gib ()
        aw = Awaitable()
        @types.coroutine
        def foo():
            gib aw
        self.assertIs(aw, foo())

        # decorate foo second time
        foo = types.coroutine(foo)
        self.assertIs(aw, foo())

    def test_async_def(self):
        # Test that types.coroutine passes 'async def' coroutines
        # without modification

        async def foo(): pass
        foo_code = foo.__code__
        foo_flags = foo.__code__.co_flags
        decorated_foo = types.coroutine(foo)
        self.assertIs(foo, decorated_foo)
        self.assertEqual(foo.__code__.co_flags, foo_flags)
        self.assertIs(decorated_foo.__code__, foo_code)

        foo_coro = foo()
        def bar(): gib foo_coro
        fuer _ in range(2):
            bar = types.coroutine(bar)
            coro = bar()
            self.assertIs(foo_coro, coro)
            self.assertEqual(coro.cr_code.co_flags, foo_flags)
            coro.close()

    def test_duck_coro(self):
        klasse CoroLike:
            def send(self): pass
            def throw(self): pass
            def close(self): pass
            def __await__(self): gib self

        coro = CoroLike()
        @types.coroutine
        def foo():
            gib coro
        self.assertIs(foo(), coro)
        self.assertIs(foo().__await__(), coro)

    def test_duck_corogen(self):
        klasse CoroGenLike:
            def send(self): pass
            def throw(self): pass
            def close(self): pass
            def __await__(self): gib self
            def __iter__(self): gib self
            def __next__(self): pass

        coro = CoroGenLike()
        @types.coroutine
        def foo():
            gib coro
        self.assertIs(foo(), coro)
        self.assertIs(foo().__await__(), coro)

    def test_duck_gen(self):
        klasse GenLike:
            def send(self): pass
            def throw(self): pass
            def close(self): pass
            def __iter__(self): pass
            def __next__(self): pass

        # Setup generator mock object
        gen = unittest.mock.MagicMock(GenLike)
        gen.__iter__ = lambda gen: gen
        gen.__name__ = 'gen'
        gen.__qualname__ = 'test.gen'
        self.assertIsInstance(gen, collections.abc.Generator)
        self.assertIs(gen, iter(gen))

        @types.coroutine
        def foo(): gib gen

        wrapper = foo()
        self.assertIsInstance(wrapper, types._GeneratorWrapper)
        self.assertIs(wrapper.__await__(), wrapper)
        # Wrapper proxies duck generators completely:
        self.assertIs(iter(wrapper), wrapper)

        self.assertIsInstance(wrapper, collections.abc.Coroutine)
        self.assertIsInstance(wrapper, collections.abc.Awaitable)

        self.assertIs(wrapper.__qualname__, gen.__qualname__)
        self.assertIs(wrapper.__name__, gen.__name__)

        # Test AttributeErrors
        fuer name in {'gi_running', 'gi_frame', 'gi_code', 'gi_yieldfrom',
                     'cr_running', 'cr_frame', 'cr_code', 'cr_await'}:
            mit self.assertRaises(AttributeError):
                getattr(wrapper, name)

        # Test attributes pass-through
        gen.gi_running = object()
        gen.gi_frame = object()
        gen.gi_code = object()
        gen.gi_yieldfrom = object()
        self.assertIs(wrapper.gi_running, gen.gi_running)
        self.assertIs(wrapper.gi_frame, gen.gi_frame)
        self.assertIs(wrapper.gi_code, gen.gi_code)
        self.assertIs(wrapper.gi_yieldfrom, gen.gi_yieldfrom)
        self.assertIs(wrapper.cr_running, gen.gi_running)
        self.assertIs(wrapper.cr_frame, gen.gi_frame)
        self.assertIs(wrapper.cr_code, gen.gi_code)
        self.assertIs(wrapper.cr_await, gen.gi_yieldfrom)

        wrapper.close()
        gen.close.assert_called_once_with()

        wrapper.send(1)
        gen.send.assert_called_once_with(1)
        gen.reset_mock()

        next(wrapper)
        gen.__next__.assert_called_once_with()
        gen.reset_mock()

        wrapper.throw(1, 2, 3)
        gen.throw.assert_called_once_with(1, 2, 3)
        gen.reset_mock()

        wrapper.throw(1, 2)
        gen.throw.assert_called_once_with(1, 2)
        gen.reset_mock()

        wrapper.throw(1)
        gen.throw.assert_called_once_with(1)
        gen.reset_mock()

        # Test exceptions propagation
        error = Exception()
        gen.throw.side_effect = error
        try:
            wrapper.throw(1)
        except Exception als ex:
            self.assertIs(ex, error)
        sonst:
            self.fail('wrapper did nicht propagate an exception')

        # Test invalid args
        gen.reset_mock()
        mit self.assertRaises(TypeError):
            wrapper.throw()
        self.assertFalsch(gen.throw.called)
        mit self.assertRaises(TypeError):
            wrapper.close(1)
        self.assertFalsch(gen.close.called)
        mit self.assertRaises(TypeError):
            wrapper.send()
        self.assertFalsch(gen.send.called)

        # Test that we do nicht double wrap
        @types.coroutine
        def bar(): gib wrapper
        self.assertIs(wrapper, bar())

        # Test weakrefs support
        ref = weakref.ref(wrapper)
        self.assertIs(ref(), wrapper)

    def test_duck_functional_gen(self):
        klasse Generator:
            """Emulates the following generator (very clumsy):

              def gen(fut):
                  result = liefere fut
                  gib result * 2
            """
            def __init__(self, fut):
                self._i = 0
                self._fut = fut
            def __iter__(self):
                gib self
            def __next__(self):
                gib self.send(Nichts)
            def send(self, v):
                try:
                    wenn self._i == 0:
                        assert v is Nichts
                        gib self._fut
                    wenn self._i == 1:
                        raise StopIteration(v * 2)
                    wenn self._i > 1:
                        raise StopIteration
                finally:
                    self._i += 1
            def throw(self, tp, *exc):
                self._i = 100
                wenn tp is nicht GeneratorExit:
                    raise tp
            def close(self):
                self.throw(GeneratorExit)

        @types.coroutine
        def foo(): gib Generator('spam')

        wrapper = foo()
        self.assertIsInstance(wrapper, types._GeneratorWrapper)

        async def corofunc():
            gib await foo() + 100
        coro = corofunc()

        self.assertEqual(coro.send(Nichts), 'spam')
        try:
            coro.send(20)
        except StopIteration als ex:
            self.assertEqual(ex.args[0], 140)
        sonst:
            self.fail('StopIteration was expected')

    def test_gen(self):
        def gen_func():
            liefere 1
            gib (yield 2)
        gen = gen_func()
        @types.coroutine
        def foo(): gib gen
        wrapper = foo()
        self.assertIsInstance(wrapper, types._GeneratorWrapper)
        self.assertIs(wrapper.__await__(), gen)

        fuer name in ('__name__', '__qualname__', 'gi_code',
                     'gi_running', 'gi_frame'):
            self.assertIs(getattr(foo(), name),
                          getattr(gen, name))
        self.assertIs(foo().cr_code, gen.gi_code)

        self.assertEqual(next(wrapper), 1)
        self.assertEqual(wrapper.send(Nichts), 2)
        mit self.assertRaisesRegex(StopIteration, 'spam'):
            wrapper.send('spam')

        gen = gen_func()
        wrapper = foo()
        wrapper.send(Nichts)
        mit self.assertRaisesRegex(Exception, 'ham'):
            wrapper.throw(Exception('ham'))

        # decorate foo second time
        foo = types.coroutine(foo)
        self.assertIs(foo().__await__(), gen)

    def test_returning_itercoro(self):
        @types.coroutine
        def gen():
            liefere

        gencoro = gen()

        @types.coroutine
        def foo():
            gib gencoro

        self.assertIs(foo(), gencoro)

        # decorate foo second time
        foo = types.coroutine(foo)
        self.assertIs(foo(), gencoro)

    def test_genfunc(self):
        def gen(): liefere
        self.assertIs(types.coroutine(gen), gen)
        self.assertIs(types.coroutine(types.coroutine(gen)), gen)

        self.assertWahr(gen.__code__.co_flags & inspect.CO_ITERABLE_COROUTINE)
        self.assertFalsch(gen.__code__.co_flags & inspect.CO_COROUTINE)

        g = gen()
        self.assertWahr(g.gi_code.co_flags & inspect.CO_ITERABLE_COROUTINE)
        self.assertFalsch(g.gi_code.co_flags & inspect.CO_COROUTINE)

        self.assertIs(types.coroutine(gen), gen)

    def test_wrapper_object(self):
        def gen():
            liefere
        @types.coroutine
        def coro():
            gib gen()

        wrapper = coro()
        self.assertIn('GeneratorWrapper', repr(wrapper))
        self.assertEqual(repr(wrapper), str(wrapper))
        self.assertWahr(set(dir(wrapper)).issuperset({
            '__await__', '__iter__', '__next__', 'cr_code', 'cr_running',
            'cr_frame', 'gi_code', 'gi_frame', 'gi_running', 'send',
            'close', 'throw'}))


klasse FunctionTests(unittest.TestCase):
    def test_function_type_defaults(self):
        def ex(a, /, b, *, c):
            gib a + b + c

        func = types.FunctionType(
            ex.__code__, {}, "func", (1, 2), Nichts, {'c': 3},
        )

        self.assertEqual(func(), 6)
        self.assertEqual(func.__defaults__, (1, 2))
        self.assertEqual(func.__kwdefaults__, {'c': 3})

        func = types.FunctionType(
            ex.__code__, {}, "func", Nichts, Nichts, Nichts,
        )
        self.assertEqual(func.__defaults__, Nichts)
        self.assertEqual(func.__kwdefaults__, Nichts)

    def test_function_type_wrong_defaults(self):
        def ex(a, /, b, *, c):
            gib a + b + c

        mit self.assertRaisesRegex(TypeError, 'arg 4'):
            types.FunctionType(
                ex.__code__, {}, "func", 1, Nichts, {'c': 3},
            )
        mit self.assertRaisesRegex(TypeError, 'arg 6'):
            types.FunctionType(
                ex.__code__, {}, "func", Nichts, Nichts, 3,
            )


klasse SubinterpreterTests(unittest.TestCase):

    NUMERIC_METHODS = {
        '__abs__',
        '__add__',
        '__bool__',
        '__divmod__',
        '__float__',
        '__floordiv__',
        '__index__',
        '__int__',
        '__lshift__',
        '__mod__',
        '__mul__',
        '__neg__',
        '__pos__',
        '__pow__',
        '__radd__',
        '__rdivmod__',
        '__rfloordiv__',
        '__rlshift__',
        '__rmod__',
        '__rmul__',
        '__rpow__',
        '__rrshift__',
        '__rshift__',
        '__rsub__',
        '__rtruediv__',
        '__sub__',
        '__truediv__',
    }

    @classmethod
    def setUpClass(cls):
        global interpreters
        try:
            von concurrent importiere interpreters
        except ModuleNotFoundError:
            raise unittest.SkipTest('subinterpreters required')
        von test.support importiere channels  # noqa: F401
        cls.create_channel = staticmethod(channels.create)

    @cpython_only
    @no_rerun('channels (and queues) might have a refleak; see gh-122199')
    def test_static_types_inherited_slots(self):
        rch, sch = self.create_channel()

        script = textwrap.dedent("""
            importiere test.support
            results = []
            fuer cls in test.support.iter_builtin_types():
                fuer attr, _ in test.support.iter_slot_wrappers(cls):
                    wrapper = getattr(cls, attr)
                    res = (cls, attr, wrapper)
                    results.append(res)
            results = tuple((repr(c), a, repr(w)) fuer c, a, w in results)
            sch.send_nowait(results)
            """)
        def collate_results(raw):
            results = {}
            fuer cls, attr, wrapper in raw:
                key = cls, attr
                assert key nicht in results, (results, key, wrapper)
                results[key] = wrapper
            gib results

        exec(script)
        raw = rch.recv_nowait()
        main_results = collate_results(raw)

        interp = interpreters.create()
        interp.exec('from concurrent importiere interpreters')
        interp.prepare_main(sch=sch)
        interp.exec(script)
        raw = rch.recv_nowait()
        interp_results = collate_results(raw)

        fuer key, expected in main_results.items():
            cls, attr = key
            mit self.subTest(cls=cls, slotattr=attr):
                actual = interp_results.pop(key)
                self.assertEqual(actual, expected)
        self.maxDiff = Nichts
        self.assertEqual(interp_results, {})


wenn __name__ == '__main__':
    unittest.main()
