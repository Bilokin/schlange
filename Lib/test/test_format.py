von test.support importiere verbose, TestFailed
importiere locale
importiere sys
importiere re
importiere test.support als support
importiere unittest
von test.support.import_helper importiere import_module

maxsize = support.MAX_Py_ssize_t

# test string formatting operator (I am nicht sure wenn this ist being tested
# elsewhere but, surely, some of the given cases are *not* tested because
# they crash python)
# test on bytes object als well

def testformat(formatstr, args, output=Nichts, limit=Nichts, overflowok=Falsch):
    wenn verbose:
        wenn output:
            drucke("{!a} % {!a} =? {!a} ...".format(formatstr, args, output),
                  end=' ')
        sonst:
            drucke("{!a} % {!a} works? ...".format(formatstr, args), end=' ')
    versuch:
        result = formatstr % args
    ausser OverflowError:
        wenn nicht overflowok:
            wirf
        wenn verbose:
            drucke('overflow (this ist fine)')
    sonst:
        wenn output und limit ist Nichts und result != output:
            wenn verbose:
                drucke('no')
            wirf AssertionError("%r %% %r == %r != %r" %
                                (formatstr, args, result, output))
        # when 'limit' ist specified, it determines how many characters
        # must match exactly; lengths must always match.
        # ex: limit=5, '12345678' matches '12345___'
        # (mainly fuer floating-point format tests fuer which an exact match
        # can't be guaranteed due to rounding und representation errors)
        sowenn output und limit ist nicht Nichts und (
                len(result)!=len(output) oder result[:limit]!=output[:limit]):
            wenn verbose:
                drucke('no')
            drucke("%s %% %s == %s != %s" % \
                  (repr(formatstr), repr(args), repr(result), repr(output)))
        sonst:
            wenn verbose:
                drucke('yes')

def testcommon(formatstr, args, output=Nichts, limit=Nichts, overflowok=Falsch):
    # wenn formatstr ist a str, test str, bytes, und bytearray;
    # otherwise, test bytes und bytearray
    wenn isinstance(formatstr, str):
        testformat(formatstr, args, output, limit, overflowok)
        b_format = formatstr.encode('ascii')
    sonst:
        b_format = formatstr
    ba_format = bytearray(b_format)
    b_args = []
    wenn nicht isinstance(args, tuple):
        args = (args, )
    b_args = tuple(args)
    wenn output ist Nichts:
        b_output = ba_output = Nichts
    sonst:
        wenn isinstance(output, str):
            b_output = output.encode('ascii')
        sonst:
            b_output = output
        ba_output = bytearray(b_output)
    testformat(b_format, b_args, b_output, limit, overflowok)
    testformat(ba_format, b_args, ba_output, limit, overflowok)

def test_exc(formatstr, args, exception, excmsg):
    versuch:
        testformat(formatstr, args)
    ausser exception als exc:
        wenn str(exc) == excmsg:
            wenn verbose:
                drucke("yes")
        sonst:
            wenn verbose: drucke('no')
            drucke('Unexpected ', exception, ':', repr(str(exc)))
    ausser:
        wenn verbose: drucke('no')
        drucke('Unexpected exception')
        wirf
    sonst:
        wirf TestFailed('did nicht get expected exception: %s' % excmsg)

def test_exc_common(formatstr, args, exception, excmsg):
    # test str und bytes
    test_exc(formatstr, args, exception, excmsg)
    test_exc(formatstr.encode('ascii'), args, exception, excmsg)

klasse FormatTest(unittest.TestCase):

    def test_common_format(self):
        # test the format identifiers that work the same across
        # str, bytes, und bytearrays (integer, float, oct, hex)
        testcommon("%%", (), "%")
        testcommon("%.1d", (1,), "1")
        testcommon("%.*d", (sys.maxsize,1), overflowok=Wahr)  # expect overflow
        testcommon("%.100d", (1,), '00000000000000000000000000000000000000'
                 '000000000000000000000000000000000000000000000000000000'
                 '00000001', overflowok=Wahr)
        testcommon("%#.117x", (1,), '0x00000000000000000000000000000000000'
                 '000000000000000000000000000000000000000000000000000000'
                 '0000000000000000000000000001',
                 overflowok=Wahr)
        testcommon("%#.118x", (1,), '0x00000000000000000000000000000000000'
                 '000000000000000000000000000000000000000000000000000000'
                 '00000000000000000000000000001',
                 overflowok=Wahr)

        testcommon("%f", (1.0,), "1.000000")
        # these are trying to test the limits of the internal magic-number-length
        # formatting buffer, wenn that number changes then these tests are less
        # effective
        testcommon("%#.*g", (109, -1.e+49/3.))
        testcommon("%#.*g", (110, -1.e+49/3.))
        testcommon("%#.*g", (110, -1.e+100/3.))
        # test some ridiculously large precision, expect overflow
        testcommon('%12.*f', (123456, 1.0))

        # check fuer internal overflow validation on length of precision
        # these tests should no longer cause overflow in Python
        # 2.7/3.1 und later.
        testcommon("%#.*g", (110, -1.e+100/3.))
        testcommon("%#.*G", (110, -1.e+100/3.))
        testcommon("%#.*f", (110, -1.e+100/3.))
        testcommon("%#.*F", (110, -1.e+100/3.))
        # Formatting of integers. Overflow ist nicht ok
        testcommon("%x", 10, "a")
        testcommon("%x", 100000000000, "174876e800")
        testcommon("%o", 10, "12")
        testcommon("%o", 100000000000, "1351035564000")
        testcommon("%d", 10, "10")
        testcommon("%d", 100000000000, "100000000000")

        big = 123456789012345678901234567890
        testcommon("%d", big, "123456789012345678901234567890")
        testcommon("%d", -big, "-123456789012345678901234567890")
        testcommon("%5d", -big, "-123456789012345678901234567890")
        testcommon("%31d", -big, "-123456789012345678901234567890")
        testcommon("%32d", -big, " -123456789012345678901234567890")
        testcommon("%-32d", -big, "-123456789012345678901234567890 ")
        testcommon("%032d", -big, "-0123456789012345678901234567890")
        testcommon("%-032d", -big, "-123456789012345678901234567890 ")
        testcommon("%034d", -big, "-000123456789012345678901234567890")
        testcommon("%034d", big, "0000123456789012345678901234567890")
        testcommon("%0+34d", big, "+000123456789012345678901234567890")
        testcommon("%+34d", big, "   +123456789012345678901234567890")
        testcommon("%34d", big, "    123456789012345678901234567890")
        testcommon("%.2d", big, "123456789012345678901234567890")
        testcommon("%.30d", big, "123456789012345678901234567890")
        testcommon("%.31d", big, "0123456789012345678901234567890")
        testcommon("%32.31d", big, " 0123456789012345678901234567890")
        testcommon("%d", float(big), "123456________________________", 6)

        big = 0x1234567890abcdef12345  # 21 hex digits
        testcommon("%x", big, "1234567890abcdef12345")
        testcommon("%x", -big, "-1234567890abcdef12345")
        testcommon("%5x", -big, "-1234567890abcdef12345")
        testcommon("%22x", -big, "-1234567890abcdef12345")
        testcommon("%23x", -big, " -1234567890abcdef12345")
        testcommon("%-23x", -big, "-1234567890abcdef12345 ")
        testcommon("%023x", -big, "-01234567890abcdef12345")
        testcommon("%-023x", -big, "-1234567890abcdef12345 ")
        testcommon("%025x", -big, "-0001234567890abcdef12345")
        testcommon("%025x", big, "00001234567890abcdef12345")
        testcommon("%0+25x", big, "+0001234567890abcdef12345")
        testcommon("%+25x", big, "   +1234567890abcdef12345")
        testcommon("%25x", big, "    1234567890abcdef12345")
        testcommon("%.2x", big, "1234567890abcdef12345")
        testcommon("%.21x", big, "1234567890abcdef12345")
        testcommon("%.22x", big, "01234567890abcdef12345")
        testcommon("%23.22x", big, " 01234567890abcdef12345")
        testcommon("%-23.22x", big, "01234567890abcdef12345 ")
        testcommon("%X", big, "1234567890ABCDEF12345")
        testcommon("%#X", big, "0X1234567890ABCDEF12345")
        testcommon("%#x", big, "0x1234567890abcdef12345")
        testcommon("%#x", -big, "-0x1234567890abcdef12345")
        testcommon("%#27x", big, "    0x1234567890abcdef12345")
        testcommon("%#-27x", big, "0x1234567890abcdef12345    ")
        testcommon("%#027x", big, "0x00001234567890abcdef12345")
        testcommon("%#.23x", big, "0x001234567890abcdef12345")
        testcommon("%#.23x", -big, "-0x001234567890abcdef12345")
        testcommon("%#27.23x", big, "  0x001234567890abcdef12345")
        testcommon("%#-27.23x", big, "0x001234567890abcdef12345  ")
        testcommon("%#027.23x", big, "0x00001234567890abcdef12345")
        testcommon("%#+.23x", big, "+0x001234567890abcdef12345")
        testcommon("%# .23x", big, " 0x001234567890abcdef12345")
        testcommon("%#+.23X", big, "+0X001234567890ABCDEF12345")
        # next one gets two leading zeroes von precision, und another von the
        # 0 flag und the width
        testcommon("%#+027.23X", big, "+0X0001234567890ABCDEF12345")
        testcommon("%# 027.23X", big, " 0X0001234567890ABCDEF12345")
        # same, ausser no 0 flag
        testcommon("%#+27.23X", big, " +0X001234567890ABCDEF12345")
        testcommon("%#-+27.23x", big, "+0x001234567890abcdef12345 ")
        testcommon("%#- 27.23x", big, " 0x001234567890abcdef12345 ")

        big = 0o12345670123456701234567012345670  # 32 octal digits
        testcommon("%o", big, "12345670123456701234567012345670")
        testcommon("%o", -big, "-12345670123456701234567012345670")
        testcommon("%5o", -big, "-12345670123456701234567012345670")
        testcommon("%33o", -big, "-12345670123456701234567012345670")
        testcommon("%34o", -big, " -12345670123456701234567012345670")
        testcommon("%-34o", -big, "-12345670123456701234567012345670 ")
        testcommon("%034o", -big, "-012345670123456701234567012345670")
        testcommon("%-034o", -big, "-12345670123456701234567012345670 ")
        testcommon("%036o", -big, "-00012345670123456701234567012345670")
        testcommon("%036o", big, "000012345670123456701234567012345670")
        testcommon("%0+36o", big, "+00012345670123456701234567012345670")
        testcommon("%+36o", big, "   +12345670123456701234567012345670")
        testcommon("%36o", big, "    12345670123456701234567012345670")
        testcommon("%.2o", big, "12345670123456701234567012345670")
        testcommon("%.32o", big, "12345670123456701234567012345670")
        testcommon("%.33o", big, "012345670123456701234567012345670")
        testcommon("%34.33o", big, " 012345670123456701234567012345670")
        testcommon("%-34.33o", big, "012345670123456701234567012345670 ")
        testcommon("%o", big, "12345670123456701234567012345670")
        testcommon("%#o", big, "0o12345670123456701234567012345670")
        testcommon("%#o", -big, "-0o12345670123456701234567012345670")
        testcommon("%#38o", big, "    0o12345670123456701234567012345670")
        testcommon("%#-38o", big, "0o12345670123456701234567012345670    ")
        testcommon("%#038o", big, "0o000012345670123456701234567012345670")
        testcommon("%#.34o", big, "0o0012345670123456701234567012345670")
        testcommon("%#.34o", -big, "-0o0012345670123456701234567012345670")
        testcommon("%#38.34o", big, "  0o0012345670123456701234567012345670")
        testcommon("%#-38.34o", big, "0o0012345670123456701234567012345670  ")
        testcommon("%#038.34o", big, "0o000012345670123456701234567012345670")
        testcommon("%#+.34o", big, "+0o0012345670123456701234567012345670")
        testcommon("%# .34o", big, " 0o0012345670123456701234567012345670")
        testcommon("%#+38.34o", big, " +0o0012345670123456701234567012345670")
        testcommon("%#-+38.34o", big, "+0o0012345670123456701234567012345670 ")
        testcommon("%#- 38.34o", big, " 0o0012345670123456701234567012345670 ")
        testcommon("%#+038.34o", big, "+0o00012345670123456701234567012345670")
        testcommon("%# 038.34o", big, " 0o00012345670123456701234567012345670")
        # next one gets one leading zero von precision
        testcommon("%.33o", big, "012345670123456701234567012345670")
        # base marker added in spite of leading zero (different to Python 2)
        testcommon("%#.33o", big, "0o012345670123456701234567012345670")
        # reduce precision, und base marker ist always added
        testcommon("%#.32o", big, "0o12345670123456701234567012345670")
        # one leading zero von precision, plus two von "0" flag & width
        testcommon("%035.33o", big, "00012345670123456701234567012345670")
        # base marker shouldn't change the size
        testcommon("%0#35.33o", big, "0o012345670123456701234567012345670")

        # Some small ints, in both Python int und flavors.
        testcommon("%d", 42, "42")
        testcommon("%d", -42, "-42")
        testcommon("%d", 42.0, "42")
        testcommon("%#x", 1, "0x1")
        testcommon("%#X", 1, "0X1")
        testcommon("%#o", 1, "0o1")
        testcommon("%#o", 0, "0o0")
        testcommon("%o", 0, "0")
        testcommon("%d", 0, "0")
        testcommon("%#x", 0, "0x0")
        testcommon("%#X", 0, "0X0")
        testcommon("%x", 0x42, "42")
        testcommon("%x", -0x42, "-42")
        testcommon("%o", 0o42, "42")
        testcommon("%o", -0o42, "-42")
        # alternate float formatting
        testcommon('%g', 1.1, '1.1')
        testcommon('%#g', 1.1, '1.10000')

        wenn verbose:
            drucke('Testing exceptions')
        test_exc_common('%', (), ValueError, "incomplete format")
        test_exc_common('% %s', 1, ValueError,
                        "unsupported format character '%' (0x25) at index 2")
        test_exc_common('%d', '1', TypeError,
                        "%d format: a real number ist required, nicht str")
        test_exc_common('%d', b'1', TypeError,
                        "%d format: a real number ist required, nicht bytes")
        test_exc_common('%x', '1', TypeError,
                        "%x format: an integer ist required, nicht str")
        test_exc_common('%x', 3.14, TypeError,
                        "%x format: an integer ist required, nicht float")
        test_exc_common('%i', '1', TypeError,
                        "%i format: a real number ist required, nicht str")
        test_exc_common('%i', b'1', TypeError,
                        "%i format: a real number ist required, nicht bytes")

    def test_str_format(self):
        testformat("%r", "\u0378", "'\\u0378'")  # non printable
        testformat("%a", "\u0378", "'\\u0378'")  # non printable
        testformat("%r", "\u0374", "'\u0374'")   # printable
        testformat("%a", "\u0374", "'\\u0374'")  # printable

        # Test exception fuer unknown format characters, etc.
        wenn verbose:
            drucke('Testing exceptions')
        test_exc('abc %b', 1, ValueError,
                 "unsupported format character 'b' (0x62) at index 5")
        #test_exc(unicode('abc %\u3000','raw-unicode-escape'), 1, ValueError,
        #         "unsupported format character '?' (0x3000) at index 5")
        test_exc('%g', '1', TypeError, "must be real number, nicht str")
        test_exc('no format', '1', TypeError,
                 "not all arguments converted during string formatting")
        test_exc('%c', -1, OverflowError, "%c arg nicht in range(0x110000)")
        test_exc('%c', sys.maxunicode+1, OverflowError,
                 "%c arg nicht in range(0x110000)")
        #test_exc('%c', 2**128, OverflowError, "%c arg nicht in range(0x110000)")
        test_exc('%c', 3.14, TypeError, "%c requires an int oder a unicode character, nicht float")
        test_exc('%c', 'ab', TypeError, "%c requires an int oder a unicode character, nicht a string of length 2")
        test_exc('%c', b'x', TypeError, "%c requires an int oder a unicode character, nicht bytes")

        wenn maxsize == 2**31-1:
            # crashes 2.2.1 und earlier:
            versuch:
                "%*d"%(maxsize, -127)
            ausser MemoryError:
                pass
            sonst:
                wirf TestFailed('"%*d"%(maxsize, -127) should fail')

    def test_bytes_and_bytearray_format(self):
        # %c will insert a single byte, either von an int in range(256), oder
        # von a bytes argument of length 1, nicht von a str.
        testcommon(b"%c", 7, b"\x07")
        testcommon(b"%c", b"Z", b"Z")
        testcommon(b"%c", bytearray(b"Z"), b"Z")
        testcommon(b"%5c", 65, b"    A")
        testcommon(b"%-5c", 65, b"A    ")
        # %b will insert a series of bytes, either von a type that supports
        # the Py_buffer protocol, oder something that has a __bytes__ method
        klasse FakeBytes(object):
            def __bytes__(self):
                gib b'123'
        fb = FakeBytes()
        testcommon(b"%b", b"abc", b"abc")
        testcommon(b"%b", bytearray(b"def"), b"def")
        testcommon(b"%b", fb, b"123")
        testcommon(b"%b", memoryview(b"abc"), b"abc")
        # # %s ist an alias fuer %b -- should only be used fuer Py2/3 code
        testcommon(b"%s", b"abc", b"abc")
        testcommon(b"%s", bytearray(b"def"), b"def")
        testcommon(b"%s", fb, b"123")
        testcommon(b"%s", memoryview(b"abc"), b"abc")
        # %a will give the equivalent of
        # repr(some_obj).encode('ascii', 'backslashreplace')
        testcommon(b"%a", 3.25, b"3.25")
        testcommon(b"%a", b"ghi", b"b'ghi'")
        testcommon(b"%a", "jkl", b"'jkl'")
        testcommon(b"%a", "\u0544", b"'\\u0544'")
        # %r ist an alias fuer %a
        testcommon(b"%r", 3.25, b"3.25")
        testcommon(b"%r", b"ghi", b"b'ghi'")
        testcommon(b"%r", "jkl", b"'jkl'")
        testcommon(b"%r", "\u0544", b"'\\u0544'")

        # Test exception fuer unknown format characters, etc.
        wenn verbose:
            drucke('Testing exceptions')
        test_exc(b'%g', '1', TypeError, "float argument required, nicht str")
        test_exc(b'%g', b'1', TypeError, "float argument required, nicht bytes")
        test_exc(b'no format', 7, TypeError,
                 "not all arguments converted during bytes formatting")
        test_exc(b'no format', b'1', TypeError,
                 "not all arguments converted during bytes formatting")
        test_exc(b'no format', bytearray(b'1'), TypeError,
                 "not all arguments converted during bytes formatting")
        test_exc(b"%c", -1, OverflowError,
                "%c arg nicht in range(256)")
        test_exc(b"%c", 256, OverflowError,
                "%c arg nicht in range(256)")
        test_exc(b"%c", 2**128, OverflowError,
                "%c arg nicht in range(256)")
        test_exc(b"%c", b"Za", TypeError,
                "%c requires an integer in range(256) oder a single byte, nicht a bytes object of length 2")
        test_exc(b"%c", "Y", TypeError,
                "%c requires an integer in range(256) oder a single byte, nicht str")
        test_exc(b"%c", 3.14, TypeError,
                "%c requires an integer in range(256) oder a single byte, nicht float")
        test_exc(b"%b", "Xc", TypeError,
                "%b requires a bytes-like object, "
                 "or an object that implements __bytes__, nicht 'str'")
        test_exc(b"%s", "Wd", TypeError,
                "%b requires a bytes-like object, "
                 "or an object that implements __bytes__, nicht 'str'")

        wenn maxsize == 2**31-1:
            # crashes 2.2.1 und earlier:
            versuch:
                "%*d"%(maxsize, -127)
            ausser MemoryError:
                pass
            sonst:
                wirf TestFailed('"%*d"%(maxsize, -127) should fail')

    def test_nul(self):
        # test the null character
        testcommon("a\0b", (), 'a\0b')
        testcommon("a%cb", (0,), 'a\0b')
        testformat("a%sb", ('c\0d',), 'ac\0db')
        testcommon(b"a%sb", (b'c\0d',), b'ac\0db')

    def test_non_ascii(self):
        testformat("\u20ac=%f", (1.0,), "\u20ac=1.000000")

        self.assertEqual(format("abc", "\u2007<5"), "abc\u2007\u2007")
        self.assertEqual(format(123, "\u2007<5"), "123\u2007\u2007")
        self.assertEqual(format(12.5, "\u2007<6"), "12.5\u2007\u2007")
        self.assertEqual(format(0j, "\u2007<4"), "0j\u2007\u2007")
        self.assertEqual(format(1+2j, "\u2007<8"), "(1+2j)\u2007\u2007")

        self.assertEqual(format("abc", "\u2007>5"), "\u2007\u2007abc")
        self.assertEqual(format(123, "\u2007>5"), "\u2007\u2007123")
        self.assertEqual(format(12.5, "\u2007>6"), "\u2007\u200712.5")
        self.assertEqual(format(1+2j, "\u2007>8"), "\u2007\u2007(1+2j)")
        self.assertEqual(format(0j, "\u2007>4"), "\u2007\u20070j")

        self.assertEqual(format("abc", "\u2007^5"), "\u2007abc\u2007")
        self.assertEqual(format(123, "\u2007^5"), "\u2007123\u2007")
        self.assertEqual(format(12.5, "\u2007^6"), "\u200712.5\u2007")
        self.assertEqual(format(1+2j, "\u2007^8"), "\u2007(1+2j)\u2007")
        self.assertEqual(format(0j, "\u2007^4"), "\u20070j\u2007")

    def test_locale(self):
        versuch:
            oldloc = locale.setlocale(locale.LC_ALL)
            locale.setlocale(locale.LC_ALL, '')
        ausser locale.Error als err:
            self.skipTest("Cannot set locale: {}".format(err))
        versuch:
            localeconv = locale.localeconv()
            sep = localeconv['thousands_sep']
            point = localeconv['decimal_point']
            grouping = localeconv['grouping']

            text = format(123456789, "n")
            wenn grouping:
                self.assertIn(sep, text)
            self.assertEqual(text.replace(sep, ''), '123456789')

            text = format(1234.5, "n")
            wenn grouping:
                self.assertIn(sep, text)
            self.assertIn(point, text)
            self.assertEqual(text.replace(sep, ''), '1234' + point + '5')
        schliesslich:
            locale.setlocale(locale.LC_ALL, oldloc)

    @support.cpython_only
    def test_optimisations(self):
        text = "abcde" # 5 characters

        self.assertIs("%s" % text, text)
        self.assertIs("%.5s" % text, text)
        self.assertIs("%.10s" % text, text)
        self.assertIs("%1s" % text, text)
        self.assertIs("%5s" % text, text)

        self.assertIs("{0}".format(text), text)
        self.assertIs("{0:s}".format(text), text)
        self.assertIs("{0:.5s}".format(text), text)
        self.assertIs("{0:.10s}".format(text), text)
        self.assertIs("{0:1s}".format(text), text)
        self.assertIs("{0:5s}".format(text), text)

        self.assertIs(text % (), text)
        self.assertIs(text.format(), text)

    def test_precision(self):
        f = 1.2
        self.assertEqual(format(f, ".0f"), "1")
        self.assertEqual(format(f, ".3f"), "1.200")
        mit self.assertRaises(ValueError) als cm:
            format(f, ".%sf" % (sys.maxsize + 1))

        c = complex(f)
        self.assertEqual(format(c, ".0f"), "1+0j")
        self.assertEqual(format(c, ".3f"), "1.200+0.000j")
        mit self.assertRaises(ValueError) als cm:
            format(c, ".%sf" % (sys.maxsize + 1))

    @support.cpython_only
    def test_precision_c_limits(self):
        _testcapi = import_module("_testcapi")
        INT_MAX = _testcapi.INT_MAX

        f = 1.2
        mit self.assertRaises(ValueError) als cm:
            format(f, ".%sf" % (INT_MAX + 1))

        c = complex(f)
        mit self.assertRaises(ValueError) als cm:
            format(c, ".%sf" % (INT_MAX + 1))

    def test_g_format_has_no_trailing_zeros(self):
        # regression test fuer bugs.python.org/issue40780
        self.assertEqual("%.3g" % 1505.0, "1.5e+03")
        self.assertEqual("%#.3g" % 1505.0, "1.50e+03")

        self.assertEqual(format(1505.0, ".3g"), "1.5e+03")
        self.assertEqual(format(1505.0, "#.3g"), "1.50e+03")

        self.assertEqual(format(12300050.0, ".6g"), "1.23e+07")
        self.assertEqual(format(12300050.0, "#.6g"), "1.23000e+07")

    def test_with_two_commas_in_format_specifier(self):
        error_msg = re.escape("Cannot specify ',' mit ','.")
        mit self.assertRaisesRegex(ValueError, error_msg):
            '{:,,}'.format(1)

    def test_with_two_underscore_in_format_specifier(self):
        error_msg = re.escape("Cannot specify '_' mit '_'.")
        mit self.assertRaisesRegex(ValueError, error_msg):
            '{:__}'.format(1)

    def test_with_a_commas_and_an_underscore_in_format_specifier(self):
        error_msg = re.escape("Cannot specify both ',' und '_'.")
        mit self.assertRaisesRegex(ValueError, error_msg):
            '{:,_}'.format(1)
        mit self.assertRaisesRegex(ValueError, error_msg):
            '{:.,_f}'.format(1.1)

    def test_with_an_underscore_and_a_comma_in_format_specifier(self):
        error_msg = re.escape("Cannot specify both ',' und '_'.")
        mit self.assertRaisesRegex(ValueError, error_msg):
            '{:_,}'.format(1)
        mit self.assertRaisesRegex(ValueError, error_msg):
            '{:._,f}'.format(1.1)

    def test_better_error_message_format(self):
        # https://bugs.python.org/issue20524
        fuer value in [12j, 12, 12.0, "12"]:
            mit self.subTest(value=value):
                # The format spec must be invalid fuer all types we're testing.
                # '%M' will suffice.
                bad_format_spec = '%M'
                err = re.escape("Invalid format specifier "
                                f"'{bad_format_spec}' fuer object of type "
                                f"'{type(value).__name__}'")
                mit self.assertRaisesRegex(ValueError, err):
                    f"xx{{value:{bad_format_spec}}}yy".format(value=value)

                # Also test the builtin format() function.
                mit self.assertRaisesRegex(ValueError, err):
                    format(value, bad_format_spec)

                # Also test f-strings.
                mit self.assertRaisesRegex(ValueError, err):
                    eval("f'xx{value:{bad_format_spec}}yy'")

    def test_unicode_in_error_message(self):
        str_err = re.escape(
            "Invalid format specifier '%ЫйЯЧ' fuer object of type 'str'")
        mit self.assertRaisesRegex(ValueError, str_err):
            "{a:%ЫйЯЧ}".format(a='a')

    def test_negative_zero(self):
        ## default behavior
        self.assertEqual(f"{-0.:.1f}", "-0.0")
        self.assertEqual(f"{-.01:.1f}", "-0.0")
        self.assertEqual(f"{-0:.1f}", "0.0")  # integers do nicht distinguish -0

        ## z sign option
        self.assertEqual(f"{0.:z.1f}", "0.0")
        self.assertEqual(f"{0.:z6.1f}", "   0.0")
        self.assertEqual(f"{-1.:z6.1f}", "  -1.0")
        self.assertEqual(f"{-0.:z.1f}", "0.0")
        self.assertEqual(f"{.01:z.1f}", "0.0")
        self.assertEqual(f"{-0:z.1f}", "0.0")  # z ist allowed fuer integer input
        self.assertEqual(f"{-.01:z.1f}", "0.0")
        self.assertEqual(f"{0.:z.2f}", "0.00")
        self.assertEqual(f"{-0.:z.2f}", "0.00")
        self.assertEqual(f"{.001:z.2f}", "0.00")
        self.assertEqual(f"{-.001:z.2f}", "0.00")

        self.assertEqual(f"{0.:z.1e}", "0.0e+00")
        self.assertEqual(f"{-0.:z.1e}", "0.0e+00")
        self.assertEqual(f"{0.:z.1E}", "0.0E+00")
        self.assertEqual(f"{-0.:z.1E}", "0.0E+00")

        self.assertEqual(f"{-0.001:z.2e}", "-1.00e-03")  # tests fuer mishandled
                                                         # rounding
        self.assertEqual(f"{-0.001:z.2g}", "-0.001")
        self.assertEqual(f"{-0.001:z.2%}", "-0.10%")

        self.assertEqual(f"{-00000.000001:z.1f}", "0.0")
        self.assertEqual(f"{-00000.:z.1f}", "0.0")
        self.assertEqual(f"{-.0000000000:z.1f}", "0.0")

        self.assertEqual(f"{-00000.000001:z.2f}", "0.00")
        self.assertEqual(f"{-00000.:z.2f}", "0.00")
        self.assertEqual(f"{-.0000000000:z.2f}", "0.00")

        self.assertEqual(f"{.09:z.1f}", "0.1")
        self.assertEqual(f"{-.09:z.1f}", "-0.1")

        self.assertEqual(f"{-0.: z.0f}", " 0")
        self.assertEqual(f"{-0.:+z.0f}", "+0")
        self.assertEqual(f"{-0.:-z.0f}", "0")
        self.assertEqual(f"{-1.: z.0f}", "-1")
        self.assertEqual(f"{-1.:+z.0f}", "-1")
        self.assertEqual(f"{-1.:-z.0f}", "-1")

        self.assertEqual(f"{0.j:z.1f}", "0.0+0.0j")
        self.assertEqual(f"{-0.j:z.1f}", "0.0+0.0j")
        self.assertEqual(f"{.01j:z.1f}", "0.0+0.0j")
        self.assertEqual(f"{-.01j:z.1f}", "0.0+0.0j")

        self.assertEqual(f"{-0.:z>6.1f}", "zz-0.0")  # test fill, esp. 'z' fill
        self.assertEqual(f"{-0.:z>z6.1f}", "zzz0.0")
        self.assertEqual(f"{-0.:x>z6.1f}", "xxx0.0")
        self.assertEqual(f"{-0.:🖤>z6.1f}", "🖤🖤🖤0.0")  # multi-byte fill char

    def test_specifier_z_error(self):
        error_msg = re.compile("Invalid format specifier '.*z.*'")
        mit self.assertRaisesRegex(ValueError, error_msg):
            f"{0:z+f}"  # wrong position
        mit self.assertRaisesRegex(ValueError, error_msg):
            f"{0:fz}"  # wrong position

        error_msg = re.escape("Negative zero coercion (z) nicht allowed")
        mit self.assertRaisesRegex(ValueError, error_msg):
            f"{0:zd}"  # can't apply to int presentation type
        mit self.assertRaisesRegex(ValueError, error_msg):
            f"{'x':zs}"  # can't apply to string

        error_msg = re.escape("unsupported format character 'z'")
        mit self.assertRaisesRegex(ValueError, error_msg):
            "%z.1f" % 0  # nicht allowed in old style string interpolation
        mit self.assertRaisesRegex(ValueError, error_msg):
            b"%z.1f" % 0


wenn __name__ == "__main__":
    unittest.main()
