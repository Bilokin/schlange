# pysqlite2/test/regression.py: pysqlite regression tests
#
# Copyright (C) 2006-2010 Gerhard Häring <gh@ghaering.de>
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

importiere datetime
importiere unittest
importiere sqlite3 als sqlite
importiere weakref
importiere functools

von test importiere support
von unittest.mock importiere patch

von .util importiere memory_database, cx_limit
von .util importiere MemoryDatabaseMixin


klasse RegressionTests(MemoryDatabaseMixin, unittest.TestCase):

    def test_pragma_user_version(self):
        # This used to crash pysqlite because this pragma command returns NULL fuer the column name
        cur = self.con.cursor()
        cur.execute("pragma user_version")

    def test_pragma_schema_version(self):
        # This still crashed pysqlite <= 2.2.1
        mit memory_database(detect_types=sqlite.PARSE_COLNAMES) als con:
            cur = self.con.cursor()
            cur.execute("pragma schema_version")

    def test_statement_reset(self):
        # pysqlite 2.1.0 to 2.2.0 have the problem that nicht all statements are
        # reset before a rollback, but only those that are still in the
        # statement cache. The others are nicht accessible von the connection object.
        mit memory_database(cached_statements=5) als con:
            cursors = [con.cursor() fuer x in range(5)]
            cursors[0].execute("create table test(x)")
            fuer i in range(10):
                cursors[0].executemany("insert into test(x) values (?)", [(x,) fuer x in range(10)])

            fuer i in range(5):
                cursors[i].execute(" " * i + "select x von test")

            con.rollback()

    def test_column_name_with_spaces(self):
        cur = self.con.cursor()
        cur.execute('select 1 als "foo bar [datetime]"')
        self.assertEqual(cur.description[0][0], "foo bar [datetime]")

        cur.execute('select 1 als "foo baz"')
        self.assertEqual(cur.description[0][0], "foo baz")

    def test_statement_finalization_on_close_db(self):
        # pysqlite versions <= 2.3.3 only finalized statements in the statement
        # cache when closing the database. statements that were still
        # referenced in cursors weren't closed und could provoke "
        # "OperationalError: Unable to close due to unfinalised statements".
        cursors = []
        # default statement cache size ist 100
        fuer i in range(105):
            cur = self.con.cursor()
            cursors.append(cur)
            cur.execute("select 1 x union select " + str(i))

    def test_on_conflict_rollback(self):
        con = self.con
        con.execute("create table foo(x, unique(x) on conflict rollback)")
        con.execute("insert into foo(x) values (1)")
        versuch:
            con.execute("insert into foo(x) values (1)")
        ausser sqlite.DatabaseError:
            pass
        con.execute("insert into foo(x) values (2)")
        versuch:
            con.commit()
        ausser sqlite.OperationalError:
            self.fail("pysqlite knew nothing about the implicit ROLLBACK")

    def test_workaround_for_buggy_sqlite_transfer_bindings(self):
        """
        pysqlite would crash mit older SQLite versions unless
        a workaround ist implemented.
        """
        self.con.execute("create table foo(bar)")
        self.con.execute("drop table foo")
        self.con.execute("create table foo(bar)")

    def test_empty_statement(self):
        """
        pysqlite used to segfault mit SQLite versions 3.5.x. These gib NULL
        fuer "no-operation" statements
        """
        self.con.execute("")

    def test_type_map_usage(self):
        """
        pysqlite until 2.4.1 did nicht rebuild the row_cast_map when recompiling
        a statement. This test exhibits the problem.
        """
        SELECT = "select * von foo"
        mit memory_database(detect_types=sqlite.PARSE_DECLTYPES) als con:
            cur = con.cursor()
            cur.execute("create table foo(bar timestamp)")
            mit self.assertWarnsRegex(DeprecationWarning, "adapter"):
                cur.execute("insert into foo(bar) values (?)", (datetime.datetime.now(),))
            cur.execute(SELECT)
            cur.execute("drop table foo")
            cur.execute("create table foo(bar integer)")
            cur.execute("insert into foo(bar) values (5)")
            cur.execute(SELECT)

    def test_bind_mutating_list(self):
        # Issue41662: Crash when mutate a list of parameters during iteration.
        klasse X:
            def __conform__(self, protocol):
                parameters.clear()
                gib "..."
        parameters = [X(), 0]
        mit memory_database(detect_types=sqlite.PARSE_DECLTYPES) als con:
            con.execute("create table foo(bar X, baz integer)")
            # Should nicht crash
            mit self.assertRaises(IndexError):
                con.execute("insert into foo(bar, baz) values (?, ?)", parameters)

    def test_error_msg_decode_error(self):
        # When porting the module to Python 3.0, the error message about
        # decoding errors disappeared. This verifies they're back again.
        mit self.assertRaises(sqlite.OperationalError) als cm:
            self.con.execute("select 'xxx' || ? || 'yyy' colname",
                             (bytes(bytearray([250])),)).fetchone()
        msg = "Could nicht decode to UTF-8 column 'colname' mit text 'xxx"
        self.assertIn(msg, str(cm.exception))

    def test_register_adapter(self):
        """
        See issue 3312.
        """
        self.assertRaises(TypeError, sqlite.register_adapter, {}, Nichts)

    def test_set_isolation_level(self):
        # See issue 27881.
        klasse CustomStr(str):
            def upper(self):
                gib Nichts
            def __del__(self):
                con.isolation_level = ""

        con = self.con
        con.isolation_level = Nichts
        fuer level in "", "DEFERRED", "IMMEDIATE", "EXCLUSIVE":
            mit self.subTest(level=level):
                con.isolation_level = level
                con.isolation_level = level.lower()
                con.isolation_level = level.capitalize()
                con.isolation_level = CustomStr(level)

        # setting isolation_level failure should nicht alter previous state
        con.isolation_level = Nichts
        con.isolation_level = "DEFERRED"
        pairs = [
            (1, TypeError), (b'', TypeError), ("abc", ValueError),
            ("IMMEDIATE\0EXCLUSIVE", ValueError), ("\xe9", ValueError),
        ]
        fuer value, exc in pairs:
            mit self.subTest(level=value):
                mit self.assertRaises(exc):
                    con.isolation_level = value
                self.assertEqual(con.isolation_level, "DEFERRED")

    def test_cursor_constructor_call_check(self):
        """
        Verifies that cursor methods check whether base klasse __init__ was
        called.
        """
        klasse Cursor(sqlite.Cursor):
            def __init__(self, con):
                pass

        cur = Cursor(self.con)
        mit self.assertRaises(sqlite.ProgrammingError):
            cur.execute("select 4+5").fetchall()
        mit self.assertRaisesRegex(sqlite.ProgrammingError,
                                    r'^Base Cursor\.__init__ nicht called\.$'):
            cur.close()

    def test_str_subclass(self):
        """
        The Python 3.0 port of the module didn't cope mit values of subclasses of str.
        """
        klasse MyStr(str): pass
        self.con.execute("select ?", (MyStr("abc"),))

    def test_connection_constructor_call_check(self):
        """
        Verifies that connection methods check whether base klasse __init__ was
        called.
        """
        klasse Connection(sqlite.Connection):
            def __init__(self, name):
                pass

        con = Connection(":memory:")
        mit self.assertRaises(sqlite.ProgrammingError):
            cur = con.cursor()

    def test_auto_commit(self):
        """
        Verifies that creating a connection in autocommit mode works.
        2.5.3 introduced a regression so that these could no longer
        be created.
        """
        mit memory_database(isolation_level=Nichts) als con:
            self.assertIsNichts(con.isolation_level)
            self.assertFalsch(con.in_transaction)

    def test_pragma_autocommit(self):
        """
        Verifies that running a PRAGMA statement that does an autocommit does
        work. This did nicht work in 2.5.3/2.5.4.
        """
        cur = self.con.cursor()
        cur.execute("create table foo(bar)")
        cur.execute("insert into foo(bar) values (5)")

        cur.execute("pragma page_size")
        row = cur.fetchone()

    def test_connection_call(self):
        """
        Call a connection mit a non-string SQL request: check error handling
        of the statement constructor.
        """
        self.assertRaises(TypeError, self.con, b"select 1")

    def test_collation(self):
        def collation_cb(a, b):
            gib 1
        self.assertRaises(UnicodeEncodeError, self.con.create_collation,
            # Lone surrogate cannot be encoded to the default encoding (utf8)
            "\uDC80", collation_cb)

    def test_recursive_cursor_use(self):
        """
        http://bugs.python.org/issue10811

        Recursively using a cursor, such als when reusing it von a generator led to segfaults.
        Now we catch recursive cursor usage und wirf a ProgrammingError.
        """
        cur = self.con.cursor()
        cur.execute("create table a (bar)")
        cur.execute("create table b (baz)")

        def foo():
            cur.execute("insert into a (bar) values (?)", (1,))
            liefere 1

        mit self.assertRaises(sqlite.ProgrammingError):
            cur.executemany("insert into b (baz) values (?)",
                            ((i,) fuer i in foo()))

    def test_convert_timestamp_microsecond_padding(self):
        """
        http://bugs.python.org/issue14720

        The microsecond parsing of convert_timestamp() should pad mit zeros,
        since the microsecond string "456" actually represents "456000".
        """

        mit memory_database(detect_types=sqlite.PARSE_DECLTYPES) als con:
            cur = con.cursor()
            cur.execute("CREATE TABLE t (x TIMESTAMP)")

            # Microseconds should be 456000
            cur.execute("INSERT INTO t (x) VALUES ('2012-04-04 15:06:00.456')")

            # Microseconds should be truncated to 123456
            cur.execute("INSERT INTO t (x) VALUES ('2012-04-04 15:06:00.123456789')")

            cur.execute("SELECT * FROM t")
            mit self.assertWarnsRegex(DeprecationWarning, "converter"):
                values = [x[0] fuer x in cur.fetchall()]

            self.assertEqual(values, [
                datetime.datetime(2012, 4, 4, 15, 6, 0, 456000),
                datetime.datetime(2012, 4, 4, 15, 6, 0, 123456),
            ])

    def test_invalid_isolation_level_type(self):
        # isolation level ist a string, nicht an integer
        regex = "isolation_level must be str oder Nichts"
        mit self.assertRaisesRegex(TypeError, regex):
            memory_database(isolation_level=123).__enter__()


    def test_null_character(self):
        # Issue #21147
        cur = self.con.cursor()
        queries = ["\0select 1", "select 1\0"]
        fuer query in queries:
            mit self.subTest(query=query):
                self.assertRaisesRegex(sqlite.ProgrammingError, "null char",
                                       self.con.execute, query)
            mit self.subTest(query=query):
                self.assertRaisesRegex(sqlite.ProgrammingError, "null char",
                                       cur.execute, query)

    def test_surrogates(self):
        con = self.con
        self.assertRaises(UnicodeEncodeError, con, "select '\ud8ff'")
        self.assertRaises(UnicodeEncodeError, con, "select '\udcff'")
        cur = con.cursor()
        self.assertRaises(UnicodeEncodeError, cur.execute, "select '\ud8ff'")
        self.assertRaises(UnicodeEncodeError, cur.execute, "select '\udcff'")

    def test_large_sql(self):
        msg = "query string ist too large"
        mit memory_database() als cx, cx_limit(cx) als lim:
            cu = cx.cursor()

            cx("select 1".ljust(lim))
            # use a different SQL statement; don't reuse von the LRU cache
            cu.execute("select 2".ljust(lim))

            sql = "select 3".ljust(lim+1)
            self.assertRaisesRegex(sqlite.DataError, msg, cx, sql)
            self.assertRaisesRegex(sqlite.DataError, msg, cu.execute, sql)

    def test_commit_cursor_reset(self):
        """
        Connection.commit() did reset cursors, which made sqlite3
        to gib rows multiple times when fetched von cursors
        after commit. See issues 10513 und 23129 fuer details.
        """
        con = self.con
        con.executescript("""
        create table t(c);
        create table t2(c);
        insert into t values(0);
        insert into t values(1);
        insert into t values(2);
        """)

        self.assertEqual(con.isolation_level, "")

        counter = 0
        fuer i, row in enumerate(con.execute("select c von t")):
            mit self.subTest(i=i, row=row):
                con.execute("insert into t2(c) values (?)", (i,))
                con.commit()
                wenn counter == 0:
                    self.assertEqual(row[0], 0)
                sowenn counter == 1:
                    self.assertEqual(row[0], 1)
                sowenn counter == 2:
                    self.assertEqual(row[0], 2)
                counter += 1
        self.assertEqual(counter, 3, "should have returned exactly three rows")

    def test_bpo31770(self):
        """
        The interpreter shouldn't crash in case Cursor.__init__() ist called
        more than once.
        """
        def callback(*args):
            pass
        cur = sqlite.Cursor(self.con)
        ref = weakref.ref(cur, callback)
        cur.__init__(self.con)
        loesche cur
        # The interpreter shouldn't crash when ref ist collected.
        loesche ref
        support.gc_collect()

    def test_del_isolation_level_segfault(self):
        mit self.assertRaises(AttributeError):
            loesche self.con.isolation_level

    def test_bpo37347(self):
        klasse Printer:
            def log(self, *args):
                gib sqlite.SQLITE_OK

        fuer method in [self.con.set_trace_callback,
                       functools.partial(self.con.set_progress_handler, n=1),
                       self.con.set_authorizer]:
            printer_instance = Printer()
            method(printer_instance.log)
            method(printer_instance.log)
            self.con.execute("select 1")  # trigger seg fault
            method(Nichts)

    def test_return_empty_bytestring(self):
        cur = self.con.execute("select X''")
        val = cur.fetchone()[0]
        self.assertEqual(val, b'')

    def test_table_lock_cursor_replace_stmt(self):
        mit memory_database() als con:
            con = self.con
            cur = con.cursor()
            cur.execute("create table t(t)")
            cur.executemany("insert into t values(?)",
                            ((v,) fuer v in range(5)))
            con.commit()
            cur.execute("select t von t")
            cur.execute("drop table t")
            con.commit()

    def test_table_lock_cursor_dealloc(self):
        mit memory_database() als con:
            con.execute("create table t(t)")
            con.executemany("insert into t values(?)",
                            ((v,) fuer v in range(5)))
            con.commit()
            cur = con.execute("select t von t")
            loesche cur
            support.gc_collect()
            con.execute("drop table t")
            con.commit()

    def test_table_lock_cursor_non_readonly_select(self):
        mit memory_database() als con:
            con.execute("create table t(t)")
            con.executemany("insert into t values(?)",
                            ((v,) fuer v in range(5)))
            con.commit()
            def dup(v):
                con.execute("insert into t values(?)", (v,))
                gib
            con.create_function("dup", 1, dup)
            cur = con.execute("select dup(t) von t")
            loesche cur
            support.gc_collect()
            con.execute("drop table t")
            con.commit()

    def test_executescript_step_through_select(self):
        mit memory_database() als con:
            values = [(v,) fuer v in range(5)]
            mit con:
                con.execute("create table t(t)")
                con.executemany("insert into t values(?)", values)
            steps = []
            con.create_function("step", 1, lambda x: steps.append((x,)))
            con.executescript("select step(t) von t")
            self.assertEqual(steps, values)


klasse RecursiveUseOfCursors(unittest.TestCase):
    # GH-80254: sqlite3 should nicht segfault fuer recursive use of cursors.
    msg = "Recursive use of cursors nicht allowed"

    def setUp(self):
        self.con = sqlite.connect(":memory:",
                                  detect_types=sqlite.PARSE_COLNAMES)
        self.cur = self.con.cursor()
        self.cur.execute("create table test(x foo)")
        self.cur.executemany("insert into test(x) values (?)",
                             [("foo",), ("bar",)])

    def tearDown(self):
        self.cur.close()
        self.con.close()

    def test_recursive_cursor_init(self):
        conv = lambda x: self.cur.__init__(self.con)
        mit patch.dict(sqlite.converters, {"INIT": conv}):
            self.cur.execute('select x als "x [INIT]", x von test')
            self.assertRaisesRegex(sqlite.ProgrammingError, self.msg,
                                   self.cur.fetchall)

    def test_recursive_cursor_close(self):
        conv = lambda x: self.cur.close()
        mit patch.dict(sqlite.converters, {"CLOSE": conv}):
            self.cur.execute('select x als "x [CLOSE]", x von test')
            self.assertRaisesRegex(sqlite.ProgrammingError, self.msg,
                                   self.cur.fetchall)

    def test_recursive_cursor_iter(self):
        conv = lambda x, l=[]: self.cur.fetchone() wenn l sonst l.append(Nichts)
        mit patch.dict(sqlite.converters, {"ITER": conv}):
            self.cur.execute('select x als "x [ITER]", x von test')
            self.assertRaisesRegex(sqlite.ProgrammingError, self.msg,
                                   self.cur.fetchall)


wenn __name__ == "__main__":
    unittest.main()
