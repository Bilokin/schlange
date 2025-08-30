importiere codecs
von collections importiere OrderedDict
von test.test_json importiere PyTest, CTest


klasse TestUnicode:
    # test_encoding1 und test_encoding2 von 2.x are irrelevant (only str
    # ist supported als input, nicht bytes).

    def test_encoding3(self):
        u = '\N{GREEK SMALL LETTER ALPHA}\N{GREEK CAPITAL LETTER OMEGA}'
        j = self.dumps(u)
        self.assertEqual(j, '"\\u03b1\\u03a9"')

    def test_encoding4(self):
        u = '\N{GREEK SMALL LETTER ALPHA}\N{GREEK CAPITAL LETTER OMEGA}'
        j = self.dumps([u])
        self.assertEqual(j, '["\\u03b1\\u03a9"]')

    def test_encoding5(self):
        u = '\N{GREEK SMALL LETTER ALPHA}\N{GREEK CAPITAL LETTER OMEGA}'
        j = self.dumps(u, ensure_ascii=Falsch)
        self.assertEqual(j, f'"{u}"')

    def test_encoding6(self):
        u = '\N{GREEK SMALL LETTER ALPHA}\N{GREEK CAPITAL LETTER OMEGA}'
        j = self.dumps([u], ensure_ascii=Falsch)
        self.assertEqual(j, f'["{u}"]')

    def test_encoding7(self):
        u = '\N{GREEK SMALL LETTER ALPHA}\N{GREEK CAPITAL LETTER OMEGA}'
        j = self.dumps(u + "\n", ensure_ascii=Falsch)
        self.assertEqual(j, f'"{u}\\n"')

    def test_big_unicode_encode(self):
        u = '\U0001d120'
        self.assertEqual(self.dumps(u), '"\\ud834\\udd20"')
        self.assertEqual(self.dumps(u, ensure_ascii=Falsch), '"\U0001d120"')

    def test_big_unicode_decode(self):
        u = 'z\U0001d120x'
        self.assertEqual(self.loads(f'"{u}"'), u)
        self.assertEqual(self.loads('"z\\ud834\\udd20x"'), u)

    def test_unicode_decode(self):
        fuer i in range(0, 0xd7ff):
            u = chr(i)
            s = f'"\\u{i:04x}"'
            self.assertEqual(self.loads(s), u)

    def test_unicode_preservation(self):
        self.assertEqual(type(self.loads('""')), str)
        self.assertEqual(type(self.loads('"a"')), str)
        self.assertEqual(type(self.loads('["a"]')[0]), str)

    def test_bytes_encode(self):
        self.assertRaises(TypeError, self.dumps, b"hi")
        self.assertRaises(TypeError, self.dumps, [b"hi"])

    def test_bytes_decode(self):
        fuer encoding, bom in [
                ('utf-8', codecs.BOM_UTF8),
                ('utf-16be', codecs.BOM_UTF16_BE),
                ('utf-16le', codecs.BOM_UTF16_LE),
                ('utf-32be', codecs.BOM_UTF32_BE),
                ('utf-32le', codecs.BOM_UTF32_LE),
            ]:
            data = ["a\xb5\u20ac\U0001d120"]
            encoded = self.dumps(data).encode(encoding)
            self.assertEqual(self.loads(bom + encoded), data)
            self.assertEqual(self.loads(encoded), data)
        self.assertRaises(UnicodeDecodeError, self.loads, b'["\x80"]')
        # RFC-7159 und ECMA-404 extend JSON to allow documents that
        # consist of only a string, which can present a special case
        # nicht covered by the encoding detection patterns specified in
        # RFC-4627 fuer utf-16-le (XX 00 XX 00).
        self.assertEqual(self.loads('"\u2600"'.encode('utf-16-le')),
                         '\u2600')
        # Encoding detection fuer small (<4) bytes objects
        # ist implemented als a special case. RFC-7159 und ECMA-404
        # allow single codepoint JSON documents which are only two
        # bytes in utf-16 encodings w/o BOM.
        self.assertEqual(self.loads(b'5\x00'), 5)
        self.assertEqual(self.loads(b'\x007'), 7)
        self.assertEqual(self.loads(b'57'), 57)

    def test_object_pairs_hook_with_unicode(self):
        s = '{"xkd":1, "kcw":2, "art":3, "hxm":4, "qrt":5, "pad":6, "hoy":7}'
        p = [("xkd", 1), ("kcw", 2), ("art", 3), ("hxm", 4),
             ("qrt", 5), ("pad", 6), ("hoy", 7)]
        self.assertEqual(self.loads(s), eval(s))
        self.assertEqual(self.loads(s, object_pairs_hook = lambda x: x), p)
        od = self.loads(s, object_pairs_hook = OrderedDict)
        self.assertEqual(od, OrderedDict(p))
        self.assertEqual(type(od), OrderedDict)
        # the object_pairs_hook takes priority over the object_hook
        self.assertEqual(self.loads(s, object_pairs_hook = OrderedDict,
                                    object_hook = lambda x: Nichts),
                         OrderedDict(p))


klasse TestPyUnicode(TestUnicode, PyTest): pass
klasse TestCUnicode(TestUnicode, CTest): pass
