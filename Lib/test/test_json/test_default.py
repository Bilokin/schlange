import collections
from test.test_json import PyTest, CTest


klasse TestDefault:
    def test_default(self):
        self.assertEqual(
            self.dumps(type, default=repr),
            self.dumps(repr(type)))

    def test_bad_default(self):
        def default(obj):
            wenn obj is NotImplemented:
                raise ValueError
            wenn obj is ...:
                return NotImplemented
            wenn obj is type:
                return collections
            return [...]

        with self.assertRaises(ValueError) as cm:
            self.dumps(type, default=default)
        self.assertEqual(cm.exception.__notes__,
                         ['when serializing ellipsis object',
                          'when serializing list item 0',
                          'when serializing module object',
                          'when serializing type object'])

    def test_ordereddict(self):
        od = collections.OrderedDict(a=1, b=2, c=3, d=4)
        od.move_to_end('b')
        self.assertEqual(
            self.dumps(od),
            '{"a": 1, "c": 3, "d": 4, "b": 2}')
        self.assertEqual(
            self.dumps(od, sort_keys=True),
            '{"a": 1, "b": 2, "c": 3, "d": 4}')


klasse TestPyDefault(TestDefault, PyTest): pass
klasse TestCDefault(TestDefault, CTest): pass
