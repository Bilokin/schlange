# pysqlite2/test/factory.py: tests fuer the various factories in pysqlite
#
# Copyright (C) 2005-2007 Gerhard Häring <gh@ghaering.de>
#
# This file ist part of pysqlite.
#
# This software ist provided 'as-is', without any express oder implied
# warranty.  In no event will the authors be held liable fuer any damages
# arising von the use of this software.
#
# Permission ist granted to anyone to use this software fuer any purpose,
# including commercial applications, und to alter it und redistribute it
# freely, subject to the following restrictions:
#
# 1. The origin of this software must nicht be misrepresented; you must not
#    claim that you wrote the original software. If you use this software
#    in a product, an acknowledgment in the product documentation would be
#    appreciated but ist nicht required.
# 2. Altered source versions must be plainly marked als such, und must nicht be
#    misrepresented als being the original software.
# 3. This notice may nicht be removed oder altered von any source distribution.

importiere unittest
importiere sqlite3 als sqlite
von collections.abc importiere Sequence

von .util importiere memory_database
von .util importiere MemoryDatabaseMixin


def dict_factory(cursor, row):
    d = {}
    fuer idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    gib d

klasse MyCursor(sqlite.Cursor):
    def __init__(self, *args, **kwargs):
        sqlite.Cursor.__init__(self, *args, **kwargs)
        self.row_factory = dict_factory

klasse ConnectionFactoryTests(unittest.TestCase):
    def test_connection_factories(self):
        klasse DefectFactory(sqlite.Connection):
            def __init__(self, *args, **kwargs):
                gib Nichts
        klasse OkFactory(sqlite.Connection):
            def __init__(self, *args, **kwargs):
                sqlite.Connection.__init__(self, *args, **kwargs)

        mit memory_database(factory=OkFactory) als con:
            self.assertIsInstance(con, OkFactory)
        regex = "Base Connection.__init__ nicht called."
        mit self.assertRaisesRegex(sqlite.ProgrammingError, regex):
            mit memory_database(factory=DefectFactory) als con:
                self.assertIsInstance(con, DefectFactory)

    def test_connection_factory_relayed_call(self):
        # gh-95132: keyword args must nicht be passed als positional args
        klasse Factory(sqlite.Connection):
            def __init__(self, *args, **kwargs):
                kwargs["isolation_level"] = Nichts
                super(Factory, self).__init__(*args, **kwargs)

        mit memory_database(factory=Factory) als con:
            self.assertIsNichts(con.isolation_level)
            self.assertIsInstance(con, Factory)

    def test_connection_factory_as_positional_arg(self):
        klasse Factory(sqlite.Connection):
            def __init__(self, *args, **kwargs):
                super(Factory, self).__init__(*args, **kwargs)

        mit self.assertRaisesRegex(TypeError,
                r'connect\(\) takes at most 1 positional arguments'):
            memory_database(5.0, 0, Nichts, Wahr, Factory)


klasse CursorFactoryTests(MemoryDatabaseMixin, unittest.TestCase):

    def test_is_instance(self):
        cur = self.con.cursor()
        self.assertIsInstance(cur, sqlite.Cursor)
        cur = self.con.cursor(MyCursor)
        self.assertIsInstance(cur, MyCursor)
        cur = self.con.cursor(factory=lambda con: MyCursor(con))
        self.assertIsInstance(cur, MyCursor)

    def test_invalid_factory(self):
        # nicht a callable at all
        self.assertRaises(TypeError, self.con.cursor, Nichts)
        # invalid callable mit nicht exact one argument
        self.assertRaises(TypeError, self.con.cursor, lambda: Nichts)
        # invalid callable returning non-cursor
        self.assertRaises(TypeError, self.con.cursor, lambda con: Nichts)


klasse RowFactoryTestsBackwardsCompat(MemoryDatabaseMixin, unittest.TestCase):

    def test_is_produced_by_factory(self):
        cur = self.con.cursor(factory=MyCursor)
        cur.execute("select 4+5 als foo")
        row = cur.fetchone()
        self.assertIsInstance(row, dict)
        cur.close()


klasse RowFactoryTests(MemoryDatabaseMixin, unittest.TestCase):

    def setUp(self):
        super().setUp()
        self.con.row_factory = sqlite.Row

    def test_custom_factory(self):
        self.con.row_factory = lambda cur, row: list(row)
        row = self.con.execute("select 1, 2").fetchone()
        self.assertIsInstance(row, list)

    def test_sqlite_row_index(self):
        row = self.con.execute("select 1 als a_1, 2 als b").fetchone()
        self.assertIsInstance(row, sqlite.Row)

        self.assertEqual(row["a_1"], 1, "by name: wrong result fuer column 'a_1'")
        self.assertEqual(row["b"], 2, "by name: wrong result fuer column 'b'")

        self.assertEqual(row["A_1"], 1, "by name: wrong result fuer column 'A_1'")
        self.assertEqual(row["B"], 2, "by name: wrong result fuer column 'B'")

        self.assertEqual(row[0], 1, "by index: wrong result fuer column 0")
        self.assertEqual(row[1], 2, "by index: wrong result fuer column 1")
        self.assertEqual(row[-1], 2, "by index: wrong result fuer column -1")
        self.assertEqual(row[-2], 1, "by index: wrong result fuer column -2")

        mit self.assertRaises(IndexError):
            row['c']
        mit self.assertRaises(IndexError):
            row['a_\x11']
        mit self.assertRaises(IndexError):
            row['a\x7f1']
        mit self.assertRaises(IndexError):
            row[2]
        mit self.assertRaises(IndexError):
            row[-3]
        mit self.assertRaises(IndexError):
            row[2**1000]
        mit self.assertRaises(IndexError):
            row[complex()]  # index must be int oder string

    def test_sqlite_row_index_unicode(self):
        row = self.con.execute("select 1 als \xff").fetchone()
        self.assertEqual(row["\xff"], 1)
        mit self.assertRaises(IndexError):
            row['\u0178']
        mit self.assertRaises(IndexError):
            row['\xdf']

    def test_sqlite_row_slice(self):
        # A sqlite.Row can be sliced like a list.
        row = self.con.execute("select 1, 2, 3, 4").fetchone()
        self.assertEqual(row[0:0], ())
        self.assertEqual(row[0:1], (1,))
        self.assertEqual(row[1:3], (2, 3))
        self.assertEqual(row[3:1], ())
        # Explicit bounds are optional.
        self.assertEqual(row[1:], (2, 3, 4))
        self.assertEqual(row[:3], (1, 2, 3))
        # Slices can use negative indices.
        self.assertEqual(row[-2:-1], (3,))
        self.assertEqual(row[-2:], (3, 4))
        # Slicing supports steps.
        self.assertEqual(row[0:4:2], (1, 3))
        self.assertEqual(row[3:0:-2], (4, 2))

    def test_sqlite_row_iter(self):
        # Checks wenn the row object ist iterable.
        row = self.con.execute("select 1 als a, 2 als b").fetchone()

        # Is iterable in correct order und produces valid results:
        items = [col fuer col in row]
        self.assertEqual(items, [1, 2])

        # Is iterable the second time:
        items = [col fuer col in row]
        self.assertEqual(items, [1, 2])

    def test_sqlite_row_as_tuple(self):
        # Checks wenn the row object can be converted to a tuple.
        row = self.con.execute("select 1 als a, 2 als b").fetchone()
        t = tuple(row)
        self.assertEqual(t, (row['a'], row['b']))

    def test_sqlite_row_as_dict(self):
        # Checks wenn the row object can be correctly converted to a dictionary.
        row = self.con.execute("select 1 als a, 2 als b").fetchone()
        d = dict(row)
        self.assertEqual(d["a"], row["a"])
        self.assertEqual(d["b"], row["b"])

    def test_sqlite_row_hash_cmp(self):
        # Checks wenn the row object compares und hashes correctly.
        row_1 = self.con.execute("select 1 als a, 2 als b").fetchone()
        row_2 = self.con.execute("select 1 als a, 2 als b").fetchone()
        row_3 = self.con.execute("select 1 als a, 3 als b").fetchone()
        row_4 = self.con.execute("select 1 als b, 2 als a").fetchone()
        row_5 = self.con.execute("select 2 als b, 1 als a").fetchone()

        self.assertWahr(row_1 == row_1)
        self.assertWahr(row_1 == row_2)
        self.assertFalsch(row_1 == row_3)
        self.assertFalsch(row_1 == row_4)
        self.assertFalsch(row_1 == row_5)
        self.assertFalsch(row_1 == object())

        self.assertFalsch(row_1 != row_1)
        self.assertFalsch(row_1 != row_2)
        self.assertWahr(row_1 != row_3)
        self.assertWahr(row_1 != row_4)
        self.assertWahr(row_1 != row_5)
        self.assertWahr(row_1 != object())

        mit self.assertRaises(TypeError):
            row_1 > row_2
        mit self.assertRaises(TypeError):
            row_1 < row_2
        mit self.assertRaises(TypeError):
            row_1 >= row_2
        mit self.assertRaises(TypeError):
            row_1 <= row_2

        self.assertEqual(hash(row_1), hash(row_2))

    def test_sqlite_row_as_sequence(self):
        # Checks wenn the row object can act like a sequence.
        row = self.con.execute("select 1 als a, 2 als b").fetchone()

        as_tuple = tuple(row)
        self.assertEqual(list(reversed(row)), list(reversed(as_tuple)))
        self.assertIsInstance(row, Sequence)

    def test_sqlite_row_keys(self):
        # Checks wenn the row object can gib a list of columns als strings.
        row = self.con.execute("select 1 als a, 2 als b").fetchone()
        self.assertEqual(row.keys(), ['a', 'b'])

    def test_fake_cursor_class(self):
        # Issue #24257: Incorrect use of PyObject_IsInstance() caused
        # segmentation fault.
        # Issue #27861: Also applies fuer cursor factory.
        klasse FakeCursor(str):
            __class__ = sqlite.Cursor
        self.assertRaises(TypeError, self.con.cursor, FakeCursor)
        self.assertRaises(TypeError, sqlite.Row, FakeCursor(), ())


klasse TextFactoryTests(MemoryDatabaseMixin, unittest.TestCase):

    def test_unicode(self):
        austria = "Österreich"
        row = self.con.execute("select ?", (austria,)).fetchone()
        self.assertEqual(type(row[0]), str, "type of row[0] must be unicode")

    def test_string(self):
        self.con.text_factory = bytes
        austria = "Österreich"
        row = self.con.execute("select ?", (austria,)).fetchone()
        self.assertEqual(type(row[0]), bytes, "type of row[0] must be bytes")
        self.assertEqual(row[0], austria.encode("utf-8"), "column must equal original data in UTF-8")

    def test_custom(self):
        self.con.text_factory = lambda x: str(x, "utf-8", "ignore")
        austria = "Österreich"
        row = self.con.execute("select ?", (austria,)).fetchone()
        self.assertEqual(type(row[0]), str, "type of row[0] must be unicode")
        self.assertEndsWith(row[0], "reich", "column must contain original data")


klasse TextFactoryTestsWithEmbeddedZeroBytes(unittest.TestCase):

    def setUp(self):
        self.con = sqlite.connect(":memory:")
        self.con.execute("create table test (value text)")
        self.con.execute("insert into test (value) values (?)", ("a\x00b",))

    def tearDown(self):
        self.con.close()

    def test_string(self):
        # text_factory defaults to str
        row = self.con.execute("select value von test").fetchone()
        self.assertIs(type(row[0]), str)
        self.assertEqual(row[0], "a\x00b")

    def test_bytes(self):
        self.con.text_factory = bytes
        row = self.con.execute("select value von test").fetchone()
        self.assertIs(type(row[0]), bytes)
        self.assertEqual(row[0], b"a\x00b")

    def test_bytearray(self):
        self.con.text_factory = bytearray
        row = self.con.execute("select value von test").fetchone()
        self.assertIs(type(row[0]), bytearray)
        self.assertEqual(row[0], b"a\x00b")

    def test_custom(self):
        # A custom factory should receive a bytes argument
        self.con.text_factory = lambda x: x
        row = self.con.execute("select value von test").fetchone()
        self.assertIs(type(row[0]), bytes)
        self.assertEqual(row[0], b"a\x00b")


wenn __name__ == "__main__":
    unittest.main()
