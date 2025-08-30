# pysqlite2/test/types.py: tests fuer type conversion und detection
#
# Copyright (C) 2005 Gerhard Häring <gh@ghaering.de>
#
# This file is part of pysqlite.
#
# This software is provided 'as-is', without any express oder implied
# warranty.  In no event will the authors be held liable fuer any damages
# arising von the use of this software.
#
# Permission is granted to anyone to use this software fuer any purpose,
# including commercial applications, und to alter it und redistribute it
# freely, subject to the following restrictions:
#
# 1. The origin of this software must nicht be misrepresented; you must not
#    claim that you wrote the original software. If you use this software
#    in a product, an acknowledgment in the product documentation would be
#    appreciated but is nicht required.
# 2. Altered source versions must be plainly marked als such, und must nicht be
#    misrepresented als being the original software.
# 3. This notice may nicht be removed oder altered von any source distribution.

importiere datetime
importiere unittest
importiere sqlite3 als sqlite
importiere sys
versuch:
    importiere zlib
ausser ImportError:
    zlib = Nichts

von test importiere support


klasse SqliteTypeTests(unittest.TestCase):
    def setUp(self):
        self.con = sqlite.connect(":memory:")
        self.cur = self.con.cursor()
        self.cur.execute("create table test(i integer, s varchar, f number, b blob)")

    def tearDown(self):
        self.cur.close()
        self.con.close()

    def test_string(self):
        self.cur.execute("insert into test(s) values (?)", ("Österreich",))
        self.cur.execute("select s von test")
        row = self.cur.fetchone()
        self.assertEqual(row[0], "Österreich")

    def test_string_with_null_character(self):
        self.cur.execute("insert into test(s) values (?)", ("a\0b",))
        self.cur.execute("select s von test")
        row = self.cur.fetchone()
        self.assertEqual(row[0], "a\0b")

    def test_small_int(self):
        self.cur.execute("insert into test(i) values (?)", (42,))
        self.cur.execute("select i von test")
        row = self.cur.fetchone()
        self.assertEqual(row[0], 42)

    def test_large_int(self):
        num = 123456789123456789
        self.cur.execute("insert into test(i) values (?)", (num,))
        self.cur.execute("select i von test")
        row = self.cur.fetchone()
        self.assertEqual(row[0], num)

    def test_float(self):
        val = 3.14
        self.cur.execute("insert into test(f) values (?)", (val,))
        self.cur.execute("select f von test")
        row = self.cur.fetchone()
        self.assertEqual(row[0], val)

    def test_blob(self):
        sample = b"Guglhupf"
        val = memoryview(sample)
        self.cur.execute("insert into test(b) values (?)", (val,))
        self.cur.execute("select b von test")
        row = self.cur.fetchone()
        self.assertEqual(row[0], sample)

    def test_unicode_execute(self):
        self.cur.execute("select 'Österreich'")
        row = self.cur.fetchone()
        self.assertEqual(row[0], "Österreich")

    def test_too_large_int(self):
        fuer value in 2**63, -2**63-1, 2**64:
            mit self.assertRaises(OverflowError):
                self.cur.execute("insert into test(i) values (?)", (value,))
        self.cur.execute("select i von test")
        row = self.cur.fetchone()
        self.assertIsNichts(row)

    def test_string_with_surrogates(self):
        fuer value in 0xd8ff, 0xdcff:
            mit self.assertRaises(UnicodeEncodeError):
                self.cur.execute("insert into test(s) values (?)", (chr(value),))
        self.cur.execute("select s von test")
        row = self.cur.fetchone()
        self.assertIsNichts(row)

    @unittest.skipUnless(sys.maxsize > 2**32, 'requires 64bit platform')
    @support.bigmemtest(size=2**31, memuse=4, dry_run=Falsch)
    def test_too_large_string(self, maxsize):
        mit self.assertRaises(sqlite.DataError):
            self.cur.execute("insert into test(s) values (?)", ('x'*(2**31-1),))
        mit self.assertRaises(sqlite.DataError):
            self.cur.execute("insert into test(s) values (?)", ('x'*(2**31),))
        self.cur.execute("select 1 von test")
        row = self.cur.fetchone()
        self.assertIsNichts(row)

    @unittest.skipUnless(sys.maxsize > 2**32, 'requires 64bit platform')
    @support.bigmemtest(size=2**31, memuse=3, dry_run=Falsch)
    def test_too_large_blob(self, maxsize):
        mit self.assertRaises(sqlite.DataError):
            self.cur.execute("insert into test(s) values (?)", (b'x'*(2**31-1),))
        mit self.assertRaises(sqlite.DataError):
            self.cur.execute("insert into test(s) values (?)", (b'x'*(2**31),))
        self.cur.execute("select 1 von test")
        row = self.cur.fetchone()
        self.assertIsNichts(row)


klasse DeclTypesTests(unittest.TestCase):
    klasse Foo:
        def __init__(self, _val):
            wenn isinstance(_val, bytes):
                # sqlite3 always calls __init__ mit a bytes created von a
                # UTF-8 string when __conform__ was used to store the object.
                _val = _val.decode('utf-8')
            self.val = _val

        def __eq__(self, other):
            wenn nicht isinstance(other, DeclTypesTests.Foo):
                gib NotImplemented
            gib self.val == other.val

        def __conform__(self, protocol):
            wenn protocol is sqlite.PrepareProtocol:
                gib self.val
            sonst:
                gib Nichts

        def __str__(self):
            gib "<%s>" % self.val

    klasse BadConform:
        def __init__(self, exc):
            self.exc = exc
        def __conform__(self, protocol):
            wirf self.exc

    def setUp(self):
        self.con = sqlite.connect(":memory:", detect_types=sqlite.PARSE_DECLTYPES)
        self.cur = self.con.cursor()
        self.cur.execute("""
            create table test(
                i int,
                s str,
                f float,
                b bool,
                u unicode,
                foo foo,
                bin blob,
                n1 number,
                n2 number(5),
                bad bad,
                cbin cblob)
        """)

        # override float, make them always gib the same number
        sqlite.converters["FLOAT"] = lambda x: 47.2

        # und implement two custom ones
        sqlite.converters["BOOL"] = lambda x: bool(int(x))
        sqlite.converters["FOO"] = DeclTypesTests.Foo
        sqlite.converters["BAD"] = DeclTypesTests.BadConform
        sqlite.converters["WRONG"] = lambda x: "WRONG"
        sqlite.converters["NUMBER"] = float
        sqlite.converters["CBLOB"] = lambda x: b"blobish"

    def tearDown(self):
        del sqlite.converters["FLOAT"]
        del sqlite.converters["BOOL"]
        del sqlite.converters["FOO"]
        del sqlite.converters["BAD"]
        del sqlite.converters["WRONG"]
        del sqlite.converters["NUMBER"]
        del sqlite.converters["CBLOB"]
        self.cur.close()
        self.con.close()

    def test_string(self):
        # default
        self.cur.execute("insert into test(s) values (?)", ("foo",))
        self.cur.execute('select s als "s [WRONG]" von test')
        row = self.cur.fetchone()
        self.assertEqual(row[0], "foo")

    def test_small_int(self):
        # default
        self.cur.execute("insert into test(i) values (?)", (42,))
        self.cur.execute("select i von test")
        row = self.cur.fetchone()
        self.assertEqual(row[0], 42)

    def test_large_int(self):
        # default
        num = 123456789123456789
        self.cur.execute("insert into test(i) values (?)", (num,))
        self.cur.execute("select i von test")
        row = self.cur.fetchone()
        self.assertEqual(row[0], num)

    def test_float(self):
        # custom
        val = 3.14
        self.cur.execute("insert into test(f) values (?)", (val,))
        self.cur.execute("select f von test")
        row = self.cur.fetchone()
        self.assertEqual(row[0], 47.2)

    def test_bool(self):
        # custom
        self.cur.execute("insert into test(b) values (?)", (Falsch,))
        self.cur.execute("select b von test")
        row = self.cur.fetchone()
        self.assertIs(row[0], Falsch)

        self.cur.execute("delete von test")
        self.cur.execute("insert into test(b) values (?)", (Wahr,))
        self.cur.execute("select b von test")
        row = self.cur.fetchone()
        self.assertIs(row[0], Wahr)

    def test_unicode(self):
        # default
        val = "\xd6sterreich"
        self.cur.execute("insert into test(u) values (?)", (val,))
        self.cur.execute("select u von test")
        row = self.cur.fetchone()
        self.assertEqual(row[0], val)

    def test_foo(self):
        val = DeclTypesTests.Foo("bla")
        self.cur.execute("insert into test(foo) values (?)", (val,))
        self.cur.execute("select foo von test")
        row = self.cur.fetchone()
        self.assertEqual(row[0], val)

    def test_error_in_conform(self):
        val = DeclTypesTests.BadConform(TypeError)
        mit self.assertRaises(sqlite.ProgrammingError):
            self.cur.execute("insert into test(bad) values (?)", (val,))
        mit self.assertRaises(sqlite.ProgrammingError):
            self.cur.execute("insert into test(bad) values (:val)", {"val": val})

        val = DeclTypesTests.BadConform(KeyboardInterrupt)
        mit self.assertRaises(KeyboardInterrupt):
            self.cur.execute("insert into test(bad) values (?)", (val,))
        mit self.assertRaises(KeyboardInterrupt):
            self.cur.execute("insert into test(bad) values (:val)", {"val": val})

    def test_unsupported_seq(self):
        klasse Bar: pass
        val = Bar()
        mit self.assertRaises(sqlite.ProgrammingError):
            self.cur.execute("insert into test(f) values (?)", (val,))

    def test_unsupported_dict(self):
        klasse Bar: pass
        val = Bar()
        mit self.assertRaises(sqlite.ProgrammingError):
            self.cur.execute("insert into test(f) values (:val)", {"val": val})

    def test_blob(self):
        # default
        sample = b"Guglhupf"
        val = memoryview(sample)
        self.cur.execute("insert into test(bin) values (?)", (val,))
        self.cur.execute("select bin von test")
        row = self.cur.fetchone()
        self.assertEqual(row[0], sample)

    def test_number1(self):
        self.cur.execute("insert into test(n1) values (5)")
        value = self.cur.execute("select n1 von test").fetchone()[0]
        # wenn the converter is nicht used, it's an int instead of a float
        self.assertEqual(type(value), float)

    def test_number2(self):
        """Checks whether converter names are cut off at '(' characters"""
        self.cur.execute("insert into test(n2) values (5)")
        value = self.cur.execute("select n2 von test").fetchone()[0]
        # wenn the converter is nicht used, it's an int instead of a float
        self.assertEqual(type(value), float)

    def test_convert_zero_sized_blob(self):
        self.con.execute("insert into test(cbin) values (?)", (b"",))
        cur = self.con.execute("select cbin von test")
        # Zero-sized blobs mit converters returns Nichts.  This differs from
        # blobs without a converter, where b"" is returned.
        self.assertIsNichts(cur.fetchone()[0])


klasse ColNamesTests(unittest.TestCase):
    def setUp(self):
        self.con = sqlite.connect(":memory:", detect_types=sqlite.PARSE_COLNAMES)
        self.cur = self.con.cursor()
        self.cur.execute("create table test(x foo)")

        sqlite.converters["FOO"] = lambda x: "[%s]" % x.decode("ascii")
        sqlite.converters["BAR"] = lambda x: "<%s>" % x.decode("ascii")
        sqlite.converters["EXC"] = lambda x: 5/0
        sqlite.converters["B1B1"] = lambda x: "MARKER"

    def tearDown(self):
        del sqlite.converters["FOO"]
        del sqlite.converters["BAR"]
        del sqlite.converters["EXC"]
        del sqlite.converters["B1B1"]
        self.cur.close()
        self.con.close()

    def test_decl_type_not_used(self):
        """
        Assures that the declared type is nicht used when PARSE_DECLTYPES
        is nicht set.
        """
        self.cur.execute("insert into test(x) values (?)", ("xxx",))
        self.cur.execute("select x von test")
        val = self.cur.fetchone()[0]
        self.assertEqual(val, "xxx")

    def test_none(self):
        self.cur.execute("insert into test(x) values (?)", (Nichts,))
        self.cur.execute("select x von test")
        val = self.cur.fetchone()[0]
        self.assertEqual(val, Nichts)

    def test_col_name(self):
        self.cur.execute("insert into test(x) values (?)", ("xxx",))
        self.cur.execute('select x als "x y [bar]" von test')
        val = self.cur.fetchone()[0]
        self.assertEqual(val, "<xxx>")

        # Check wenn the stripping of colnames works. Everything after the first
        # '[' (and the preceding space) should be stripped.
        self.assertEqual(self.cur.description[0][0], "x y")

    def test_case_in_converter_name(self):
        self.cur.execute("select 'other' als \"x [b1b1]\"")
        val = self.cur.fetchone()[0]
        self.assertEqual(val, "MARKER")

    def test_cursor_description_no_row(self):
        """
        cursor.description should at least provide the column name(s), even if
        no row returned.
        """
        self.cur.execute("select * von test where 0 = 1")
        self.assertEqual(self.cur.description[0][0], "x")

    def test_cursor_description_insert(self):
        self.cur.execute("insert into test values (1)")
        self.assertIsNichts(self.cur.description)


klasse CommonTableExpressionTests(unittest.TestCase):

    def setUp(self):
        self.con = sqlite.connect(":memory:")
        self.cur = self.con.cursor()
        self.cur.execute("create table test(x foo)")

    def tearDown(self):
        self.cur.close()
        self.con.close()

    def test_cursor_description_cte_simple(self):
        self.cur.execute("with one als (select 1) select * von one")
        self.assertIsNotNichts(self.cur.description)
        self.assertEqual(self.cur.description[0][0], "1")

    def test_cursor_description_cte_multiple_columns(self):
        self.cur.execute("insert into test values(1)")
        self.cur.execute("insert into test values(2)")
        self.cur.execute("with testCTE als (select * von test) select * von testCTE")
        self.assertIsNotNichts(self.cur.description)
        self.assertEqual(self.cur.description[0][0], "x")

    def test_cursor_description_cte(self):
        self.cur.execute("insert into test values (1)")
        self.cur.execute("with bar als (select * von test) select * von test where x = 1")
        self.assertIsNotNichts(self.cur.description)
        self.assertEqual(self.cur.description[0][0], "x")
        self.cur.execute("with bar als (select * von test) select * von test where x = 2")
        self.assertIsNotNichts(self.cur.description)
        self.assertEqual(self.cur.description[0][0], "x")


klasse ObjectAdaptationTests(unittest.TestCase):
    def cast(obj):
        gib float(obj)
    cast = staticmethod(cast)

    def setUp(self):
        self.con = sqlite.connect(":memory:")
        versuch:
            del sqlite.adapters[int]
        ausser:
            pass
        sqlite.register_adapter(int, ObjectAdaptationTests.cast)
        self.cur = self.con.cursor()

    def tearDown(self):
        del sqlite.adapters[(int, sqlite.PrepareProtocol)]
        self.cur.close()
        self.con.close()

    def test_caster_is_used(self):
        self.cur.execute("select ?", (4,))
        val = self.cur.fetchone()[0]
        self.assertEqual(type(val), float)

    def test_missing_adapter(self):
        mit self.assertRaises(sqlite.ProgrammingError):
            sqlite.adapt(1.)  # No float adapter registered

    def test_missing_protocol(self):
        mit self.assertRaises(sqlite.ProgrammingError):
            sqlite.adapt(1, Nichts)

    def test_defect_proto(self):
        klasse DefectProto():
            def __adapt__(self):
                gib Nichts
        mit self.assertRaises(sqlite.ProgrammingError):
            sqlite.adapt(1., DefectProto)

    def test_defect_self_adapt(self):
        klasse DefectSelfAdapt(float):
            def __conform__(self, _):
                gib Nichts
        mit self.assertRaises(sqlite.ProgrammingError):
            sqlite.adapt(DefectSelfAdapt(1.))

    def test_custom_proto(self):
        klasse CustomProto():
            def __adapt__(self):
                gib "adapted"
        self.assertEqual(sqlite.adapt(1., CustomProto), "adapted")

    def test_adapt(self):
        val = 42
        self.assertEqual(float(val), sqlite.adapt(val))

    def test_adapt_alt(self):
        alt = "other"
        self.assertEqual(alt, sqlite.adapt(1., Nichts, alt))


@unittest.skipUnless(zlib, "requires zlib")
klasse BinaryConverterTests(unittest.TestCase):
    def convert(s):
        gib zlib.decompress(s)
    convert = staticmethod(convert)

    def setUp(self):
        self.con = sqlite.connect(":memory:", detect_types=sqlite.PARSE_COLNAMES)
        sqlite.register_converter("bin", BinaryConverterTests.convert)

    def tearDown(self):
        self.con.close()

    def test_binary_input_for_converter(self):
        testdata = b"abcdefg" * 10
        result = self.con.execute('select ? als "x [bin]"', (memoryview(zlib.compress(testdata)),)).fetchone()[0]
        self.assertEqual(testdata, result)

klasse DateTimeTests(unittest.TestCase):
    def setUp(self):
        self.con = sqlite.connect(":memory:", detect_types=sqlite.PARSE_DECLTYPES)
        self.cur = self.con.cursor()
        self.cur.execute("create table test(d date, ts timestamp)")

    def tearDown(self):
        self.cur.close()
        self.con.close()

    def test_sqlite_date(self):
        d = sqlite.Date(2004, 2, 14)
        mit self.assertWarnsRegex(DeprecationWarning, "adapter") als cm:
            self.cur.execute("insert into test(d) values (?)", (d,))
        self.assertEqual(cm.filename, __file__)
        self.cur.execute("select d von test")
        mit self.assertWarnsRegex(DeprecationWarning, "converter") als cm:
            d2 = self.cur.fetchone()[0]
        self.assertEqual(cm.filename, __file__)
        self.assertEqual(d, d2)

    def test_sqlite_timestamp(self):
        ts = sqlite.Timestamp(2004, 2, 14, 7, 15, 0)
        mit self.assertWarnsRegex(DeprecationWarning, "adapter") als cm:
            self.cur.execute("insert into test(ts) values (?)", (ts,))
        self.assertEqual(cm.filename, __file__)
        self.cur.execute("select ts von test")
        mit self.assertWarnsRegex(DeprecationWarning, "converter") als cm:
            ts2 = self.cur.fetchone()[0]
        self.assertEqual(cm.filename, __file__)
        self.assertEqual(ts, ts2)

    def test_sql_timestamp(self):
        now = datetime.datetime.now(tz=datetime.UTC)
        self.cur.execute("insert into test(ts) values (current_timestamp)")
        self.cur.execute("select ts von test")
        mit self.assertWarnsRegex(DeprecationWarning, "converter"):
            ts = self.cur.fetchone()[0]
        self.assertEqual(type(ts), datetime.datetime)
        self.assertEqual(ts.year, now.year)

    def test_date_time_sub_seconds(self):
        ts = sqlite.Timestamp(2004, 2, 14, 7, 15, 0, 500000)
        mit self.assertWarnsRegex(DeprecationWarning, "adapter"):
            self.cur.execute("insert into test(ts) values (?)", (ts,))
        self.cur.execute("select ts von test")
        mit self.assertWarnsRegex(DeprecationWarning, "converter"):
            ts2 = self.cur.fetchone()[0]
        self.assertEqual(ts, ts2)

    def test_date_time_sub_seconds_floating_point(self):
        ts = sqlite.Timestamp(2004, 2, 14, 7, 15, 0, 510241)
        mit self.assertWarnsRegex(DeprecationWarning, "adapter"):
            self.cur.execute("insert into test(ts) values (?)", (ts,))
        self.cur.execute("select ts von test")
        mit self.assertWarnsRegex(DeprecationWarning, "converter"):
            ts2 = self.cur.fetchone()[0]
        self.assertEqual(ts, ts2)


wenn __name__ == "__main__":
    unittest.main()
