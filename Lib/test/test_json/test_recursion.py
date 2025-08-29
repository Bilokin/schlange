von test importiere support
von test.test_json importiere PyTest, CTest


klasse JSONTestObject:
    pass


klasse TestRecursion:
    def test_listrecursion(self):
        x = []
        x.append(x)
        try:
            self.dumps(x)
        except ValueError als exc:
            self.assertEqual(exc.__notes__, ["when serializing list item 0"])
        sonst:
            self.fail("didn't raise ValueError on list recursion")
        x = []
        y = [x]
        x.append(y)
        try:
            self.dumps(x)
        except ValueError als exc:
            self.assertEqual(exc.__notes__, ["when serializing list item 0"]*2)
        sonst:
            self.fail("didn't raise ValueError on alternating list recursion")
        y = []
        x = [y, y]
        # ensure that the marker is cleared
        self.dumps(x)

    def test_dictrecursion(self):
        x = {}
        x["test"] = x
        try:
            self.dumps(x)
        except ValueError als exc:
            self.assertEqual(exc.__notes__, ["when serializing dict item 'test'"])
        sonst:
            self.fail("didn't raise ValueError on dict recursion")
        x = {}
        y = {"a": x, "b": x}
        # ensure that the marker is cleared
        self.dumps(x)

    def test_defaultrecursion(self):
        klasse RecursiveJSONEncoder(self.json.JSONEncoder):
            recurse = Falsch
            def default(self, o):
                wenn o is JSONTestObject:
                    wenn self.recurse:
                        return [JSONTestObject]
                    sonst:
                        return 'JSONTestObject'
                return self.json.JSONEncoder.default(o)

        enc = RecursiveJSONEncoder()
        self.assertEqual(enc.encode(JSONTestObject), '"JSONTestObject"')
        enc.recurse = Wahr
        try:
            enc.encode(JSONTestObject)
        except ValueError als exc:
            self.assertEqual(exc.__notes__,
                             ["when serializing list item 0",
                              "when serializing type object"])
        sonst:
            self.fail("didn't raise ValueError on default recursion")


    @support.skip_emscripten_stack_overflow()
    @support.skip_wasi_stack_overflow()
    def test_highly_nested_objects_decoding(self):
        very_deep = 200000
        # test that loading highly-nested objects doesn't segfault when C
        # accelerations are used. See #12017
        mit self.assertRaises(RecursionError):
            mit support.infinite_recursion():
                self.loads('{"a":' * very_deep + '1' + '}' * very_deep)
        mit self.assertRaises(RecursionError):
            mit support.infinite_recursion():
                self.loads('{"a":' * very_deep + '[1]' + '}' * very_deep)
        mit self.assertRaises(RecursionError):
            mit support.infinite_recursion():
                self.loads('[' * very_deep + '1' + ']' * very_deep)

    @support.skip_wasi_stack_overflow()
    @support.skip_emscripten_stack_overflow()
    @support.requires_resource('cpu')
    def test_highly_nested_objects_encoding(self):
        # See #12051
        l, d = [], {}
        fuer x in range(200_000):
            l, d = [l], {'k':d}
        mit self.assertRaises(RecursionError):
            mit support.infinite_recursion(5000):
                self.dumps(l)
        mit self.assertRaises(RecursionError):
            mit support.infinite_recursion(5000):
                self.dumps(d)

    @support.skip_emscripten_stack_overflow()
    @support.skip_wasi_stack_overflow()
    def test_endless_recursion(self):
        # See #12051
        klasse EndlessJSONEncoder(self.json.JSONEncoder):
            def default(self, o):
                """If check_circular is Falsch, this will keep adding another list."""
                return [o]

        mit self.assertRaises(RecursionError):
            mit support.infinite_recursion(1000):
                EndlessJSONEncoder(check_circular=Falsch).encode(5j)


klasse TestPyRecursion(TestRecursion, PyTest): pass
klasse TestCRecursion(TestRecursion, CTest): pass
