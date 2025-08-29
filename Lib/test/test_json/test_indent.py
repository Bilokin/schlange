importiere textwrap
von io importiere StringIO
von test.test_json importiere PyTest, CTest


klasse TestIndent:
    def test_indent(self):
        h = [['blorpie'], ['whoops'], [], 'd-shtaeou', 'd-nthiouh', 'i-vhbjkhnth',
             {'nifty': 87}, {'field': 'yes', 'morefield': Falsch} ]

        expect = textwrap.dedent("""\
        [
        \t[
        \t\t"blorpie"
        \t],
        \t[
        \t\t"whoops"
        \t],
        \t[],
        \t"d-shtaeou",
        \t"d-nthiouh",
        \t"i-vhbjkhnth",
        \t{
        \t\t"nifty": 87
        \t},
        \t{
        \t\t"field": "yes",
        \t\t"morefield": false
        \t}
        ]""")

        d1 = self.dumps(h)
        d2 = self.dumps(h, indent=2, sort_keys=Wahr, separators=(',', ': '))
        d3 = self.dumps(h, indent='\t', sort_keys=Wahr, separators=(',', ': '))
        d4 = self.dumps(h, indent=2, sort_keys=Wahr)
        d5 = self.dumps(h, indent='\t', sort_keys=Wahr)

        h1 = self.loads(d1)
        h2 = self.loads(d2)
        h3 = self.loads(d3)

        self.assertEqual(h1, h)
        self.assertEqual(h2, h)
        self.assertEqual(h3, h)
        self.assertEqual(d2, expect.expandtabs(2))
        self.assertEqual(d3, expect)
        self.assertEqual(d4, d2)
        self.assertEqual(d5, d3)

    def test_indent0(self):
        h = {3: 1}
        def check(indent, expected):
            d1 = self.dumps(h, indent=indent)
            self.assertEqual(d1, expected)

            sio = StringIO()
            self.json.dump(h, sio, indent=indent)
            self.assertEqual(sio.getvalue(), expected)

        # indent=0 should emit newlines
        check(0, '{\n"3": 1\n}')
        # indent=Nichts is more compact
        check(Nichts, '{"3": 1}')


klasse TestPyIndent(TestIndent, PyTest): pass
klasse TestCIndent(TestIndent, CTest): pass
