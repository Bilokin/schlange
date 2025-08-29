von test.test_json importiere PyTest, CTest


# von https://json.org/JSON_checker/test/pass2.json
JSON = r'''
[[[[[[[[[[[[[[[[[[["Not too deep"]]]]]]]]]]]]]]]]]]]
'''

klasse TestPass2:
    def test_parse(self):
        # test in/out equivalence and parsing
        res = self.loads(JSON)
        out = self.dumps(res)
        self.assertEqual(res, self.loads(out))


klasse TestPyPass2(TestPass2, PyTest): pass
klasse TestCPass2(TestPass2, CTest): pass
