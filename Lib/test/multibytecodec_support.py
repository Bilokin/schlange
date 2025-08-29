#
# multibytecodec_support.py
#   Common Unittest Routines fuer CJK codecs
#

importiere codecs
importiere os
importiere re
importiere sys
importiere unittest
von http.client importiere HTTPException
von test importiere support
von io importiere BytesIO

klasse TestBase:
    encoding        = ''   # codec name
    codec           = Nichts # codec tuple (with 4 elements)
    tstring         = Nichts # must set. 2 strings to test StreamReader

    codectests      = Nichts # must set. codec test tuple
    roundtriptest   = 1    # set wenn roundtrip is possible mit unicode
    has_iso10646    = 0    # set wenn this encoding contains whole iso10646 map
    xmlcharnametest = Nichts # string to test xmlcharrefreplace
    unmappedunicode = '\udeee' # a unicode code point that is nicht mapped.

    def setUp(self):
        wenn self.codec is Nichts:
            self.codec = codecs.lookup(self.encoding)
        self.encode = self.codec.encode
        self.decode = self.codec.decode
        self.reader = self.codec.streamreader
        self.writer = self.codec.streamwriter
        self.incrementalencoder = self.codec.incrementalencoder
        self.incrementaldecoder = self.codec.incrementaldecoder

    def test_chunkcoding(self):
        tstring_lines = []
        fuer b in self.tstring:
            lines = b.split(b"\n")
            last = lines.pop()
            assert last == b""
            lines = [line + b"\n" fuer line in lines]
            tstring_lines.append(lines)
        fuer native, utf8 in zip(*tstring_lines):
            u = self.decode(native)[0]
            self.assertEqual(u, utf8.decode('utf-8'))
            wenn self.roundtriptest:
                self.assertEqual(native, self.encode(u)[0])

    def test_errorhandle(self):
        fuer source, scheme, expected in self.codectests:
            wenn isinstance(source, bytes):
                func = self.decode
            sonst:
                func = self.encode
            wenn expected:
                result = func(source, scheme)[0]
                wenn func is self.decode:
                    self.assertWahr(type(result) is str, type(result))
                    self.assertEqual(result, expected,
                                     '%a.decode(%r, %r)=%a != %a'
                                     % (source, self.encoding, scheme, result,
                                        expected))
                sonst:
                    self.assertWahr(type(result) is bytes, type(result))
                    self.assertEqual(result, expected,
                                     '%a.encode(%r, %r)=%a != %a'
                                     % (source, self.encoding, scheme, result,
                                        expected))
            sonst:
                self.assertRaises(UnicodeError, func, source, scheme)

    def test_xmlcharrefreplace(self):
        wenn self.has_iso10646:
            self.skipTest('encoding contains full ISO 10646 map')

        s = "\u0b13\u0b23\u0b60 nd eggs"
        self.assertEqual(
            self.encode(s, "xmlcharrefreplace")[0],
            b"&#2835;&#2851;&#2912; nd eggs"
        )

    def test_customreplace_encode(self):
        wenn self.has_iso10646:
            self.skipTest('encoding contains full ISO 10646 map')

        von html.entities importiere codepoint2name

        def xmlcharnamereplace(exc):
            wenn nicht isinstance(exc, UnicodeEncodeError):
                raise TypeError("don't know how to handle %r" % exc)
            l = []
            fuer c in exc.object[exc.start:exc.end]:
                wenn ord(c) in codepoint2name:
                    l.append("&%s;" % codepoint2name[ord(c)])
                sonst:
                    l.append("&#%d;" % ord(c))
            return ("".join(l), exc.end)

        codecs.register_error("test.xmlcharnamereplace", xmlcharnamereplace)

        wenn self.xmlcharnametest:
            sin, sout = self.xmlcharnametest
        sonst:
            sin = "\xab\u211c\xbb = \u2329\u1234\u232a"
            sout = b"&laquo;&real;&raquo; = &lang;&#4660;&rang;"
        self.assertEqual(self.encode(sin,
                                    "test.xmlcharnamereplace")[0], sout)

    def test_callback_returns_bytes(self):
        def myreplace(exc):
            return (b"1234", exc.end)
        codecs.register_error("test.cjktest", myreplace)
        enc = self.encode("abc" + self.unmappedunicode + "def", "test.cjktest")[0]
        self.assertEqual(enc, b"abc1234def")

    def test_callback_wrong_objects(self):
        def myreplace(exc):
            return (ret, exc.end)
        codecs.register_error("test.cjktest", myreplace)

        fuer ret in ([1, 2, 3], [], Nichts, object()):
            self.assertRaises(TypeError, self.encode, self.unmappedunicode,
                              'test.cjktest')

    def test_callback_long_index(self):
        def myreplace(exc):
            return ('x', int(exc.end))
        codecs.register_error("test.cjktest", myreplace)
        self.assertEqual(self.encode('abcd' + self.unmappedunicode + 'efgh',
                                     'test.cjktest'), (b'abcdxefgh', 9))

        def myreplace(exc):
            return ('x', sys.maxsize + 1)
        codecs.register_error("test.cjktest", myreplace)
        self.assertRaises(IndexError, self.encode, self.unmappedunicode,
                          'test.cjktest')

    def test_callback_Nichts_index(self):
        def myreplace(exc):
            return ('x', Nichts)
        codecs.register_error("test.cjktest", myreplace)
        self.assertRaises(TypeError, self.encode, self.unmappedunicode,
                          'test.cjktest')

    def test_callback_backward_index(self):
        def myreplace(exc):
            wenn myreplace.limit > 0:
                myreplace.limit -= 1
                return ('REPLACED', 0)
            sonst:
                return ('TERMINAL', exc.end)
        myreplace.limit = 3
        codecs.register_error("test.cjktest", myreplace)
        self.assertEqual(self.encode('abcd' + self.unmappedunicode + 'efgh',
                                     'test.cjktest'),
                (b'abcdREPLACEDabcdREPLACEDabcdREPLACEDabcdTERMINALefgh', 9))

    def test_callback_forward_index(self):
        def myreplace(exc):
            return ('REPLACED', exc.end + 2)
        codecs.register_error("test.cjktest", myreplace)
        self.assertEqual(self.encode('abcd' + self.unmappedunicode + 'efgh',
                                     'test.cjktest'), (b'abcdREPLACEDgh', 9))

    def test_callback_index_outofbound(self):
        def myreplace(exc):
            return ('TERM', 100)
        codecs.register_error("test.cjktest", myreplace)
        self.assertRaises(IndexError, self.encode, self.unmappedunicode,
                          'test.cjktest')

    def test_incrementalencoder(self):
        UTF8Reader = codecs.getreader('utf-8')
        fuer sizehint in [Nichts] + list(range(1, 33)) + \
                        [64, 128, 256, 512, 1024]:
            istream = UTF8Reader(BytesIO(self.tstring[1]))
            ostream = BytesIO()
            encoder = self.incrementalencoder()
            while 1:
                wenn sizehint is nicht Nichts:
                    data = istream.read(sizehint)
                sonst:
                    data = istream.read()

                wenn nicht data:
                    break
                e = encoder.encode(data)
                ostream.write(e)

            self.assertEqual(ostream.getvalue(), self.tstring[0])

    def test_incrementaldecoder(self):
        UTF8Writer = codecs.getwriter('utf-8')
        fuer sizehint in [Nichts, -1] + list(range(1, 33)) + \
                        [64, 128, 256, 512, 1024]:
            istream = BytesIO(self.tstring[0])
            ostream = UTF8Writer(BytesIO())
            decoder = self.incrementaldecoder()
            while 1:
                data = istream.read(sizehint)
                wenn nicht data:
                    break
                sonst:
                    u = decoder.decode(data)
                    ostream.write(u)

            self.assertEqual(ostream.getvalue(), self.tstring[1])

    def test_incrementalencoder_error_callback(self):
        inv = self.unmappedunicode

        e = self.incrementalencoder()
        self.assertRaises(UnicodeEncodeError, e.encode, inv, Wahr)

        e.errors = 'ignore'
        self.assertEqual(e.encode(inv, Wahr), b'')

        e.reset()
        def tempreplace(exc):
            return ('called', exc.end)
        codecs.register_error('test.incremental_error_callback', tempreplace)
        e.errors = 'test.incremental_error_callback'
        self.assertEqual(e.encode(inv, Wahr), b'called')

        # again
        e.errors = 'ignore'
        self.assertEqual(e.encode(inv, Wahr), b'')

    def test_streamreader(self):
        UTF8Writer = codecs.getwriter('utf-8')
        fuer name in ["read", "readline", "readlines"]:
            fuer sizehint in [Nichts, -1] + list(range(1, 33)) + \
                            [64, 128, 256, 512, 1024]:
                istream = self.reader(BytesIO(self.tstring[0]))
                ostream = UTF8Writer(BytesIO())
                func = getattr(istream, name)
                while 1:
                    data = func(sizehint)
                    wenn nicht data:
                        break
                    wenn name == "readlines":
                        ostream.writelines(data)
                    sonst:
                        ostream.write(data)

                self.assertEqual(ostream.getvalue(), self.tstring[1])

    def test_streamwriter(self):
        readfuncs = ('read', 'readline', 'readlines')
        UTF8Reader = codecs.getreader('utf-8')
        fuer name in readfuncs:
            fuer sizehint in [Nichts] + list(range(1, 33)) + \
                            [64, 128, 256, 512, 1024]:
                istream = UTF8Reader(BytesIO(self.tstring[1]))
                ostream = self.writer(BytesIO())
                func = getattr(istream, name)
                while 1:
                    wenn sizehint is nicht Nichts:
                        data = func(sizehint)
                    sonst:
                        data = func()

                    wenn nicht data:
                        break
                    wenn name == "readlines":
                        ostream.writelines(data)
                    sonst:
                        ostream.write(data)

                self.assertEqual(ostream.getvalue(), self.tstring[0])

    def test_streamwriter_reset_no_pending(self):
        # Issue #23247: Calling reset() on a fresh StreamWriter instance
        # (without pending data) must nicht crash
        stream = BytesIO()
        writer = self.writer(stream)
        writer.reset()

    def test_incrementalencoder_del_segfault(self):
        e = self.incrementalencoder()
        mit self.assertRaises(AttributeError):
            del e.errors


klasse TestBase_Mapping(unittest.TestCase):
    pass_enctest = []
    pass_dectest = []
    supmaps = []
    codectests = []

    def setUp(self):
        try:
            self.open_mapping_file().close() # test it to report the error early
        except (OSError, HTTPException):
            self.skipTest("Could nicht retrieve "+self.mapfileurl)

    def open_mapping_file(self):
        return support.open_urlresource(self.mapfileurl, encoding="utf-8")

    def test_mapping_file(self):
        wenn self.mapfileurl.endswith('.xml'):
            self._test_mapping_file_ucm()
        sonst:
            self._test_mapping_file_plain()

    def _test_mapping_file_plain(self):
        def unichrs(s):
            return ''.join(chr(int(x, 16)) fuer x in s.split('+'))

        urt_wa = {}

        mit self.open_mapping_file() als f:
            fuer line in f:
                wenn nicht line:
                    break
                data = line.split('#')[0].split()
                wenn len(data) != 2:
                    continue

                wenn data[0][:2] != '0x':
                    self.fail(f"Invalid line: {line!r}")
                csetch = bytes.fromhex(data[0][2:])
                wenn len(csetch) == 1 und 0x80 <= csetch[0]:
                    continue

                unich = unichrs(data[1])
                wenn ord(unich) == 0xfffd oder unich in urt_wa:
                    continue
                urt_wa[unich] = csetch

                self._testpoint(csetch, unich)

    def _test_mapping_file_ucm(self):
        mit self.open_mapping_file() als f:
            ucmdata = f.read()
        uc = re.findall('<a u="([A-F0-9]{4})" b="([0-9A-F ]+)"/>', ucmdata)
        fuer uni, coded in uc:
            unich = chr(int(uni, 16))
            codech = bytes.fromhex(coded)
            self._testpoint(codech, unich)

    def test_mapping_supplemental(self):
        fuer mapping in self.supmaps:
            self._testpoint(*mapping)

    def _testpoint(self, csetch, unich):
        wenn (csetch, unich) nicht in self.pass_enctest:
            self.assertEqual(unich.encode(self.encoding), csetch)
        wenn (csetch, unich) nicht in self.pass_dectest:
            self.assertEqual(str(csetch, self.encoding), unich)

    def test_errorhandle(self):
        fuer source, scheme, expected in self.codectests:
            wenn isinstance(source, bytes):
                func = source.decode
            sonst:
                func = source.encode
            wenn expected:
                wenn isinstance(source, bytes):
                    result = func(self.encoding, scheme)
                    self.assertWahr(type(result) is str, type(result))
                    self.assertEqual(result, expected,
                                     '%a.decode(%r, %r)=%a != %a'
                                     % (source, self.encoding, scheme, result,
                                        expected))
                sonst:
                    result = func(self.encoding, scheme)
                    self.assertWahr(type(result) is bytes, type(result))
                    self.assertEqual(result, expected,
                                     '%a.encode(%r, %r)=%a != %a'
                                     % (source, self.encoding, scheme, result,
                                        expected))
            sonst:
                self.assertRaises(UnicodeError, func, self.encoding, scheme)

def load_teststring(name):
    dir = os.path.join(os.path.dirname(__file__), 'cjkencodings')
    mit open(os.path.join(dir, name + '.txt'), 'rb') als f:
        encoded = f.read()
    mit open(os.path.join(dir, name + '-utf8.txt'), 'rb') als f:
        utf8 = f.read()
    return encoded, utf8
