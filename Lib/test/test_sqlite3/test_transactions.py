# pysqlite2/test/transactions.py: tests transactions
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
von contextlib importiere contextmanager

von test.support.os_helper importiere TESTFN, unlink
von test.support.script_helper importiere assert_python_ok

von .util importiere memory_database
von .util importiere MemoryDatabaseMixin


klasse TransactionTests(unittest.TestCase):
    def setUp(self):
        # We can disable the busy handlers, since we control
        # the order of SQLite C API operations.
        self.con1 = sqlite.connect(TESTFN, timeout=0)
        self.cur1 = self.con1.cursor()

        self.con2 = sqlite.connect(TESTFN, timeout=0)
        self.cur2 = self.con2.cursor()

    def tearDown(self):
        versuch:
            self.cur1.close()
            self.con1.close()

            self.cur2.close()
            self.con2.close()

        schliesslich:
            unlink(TESTFN)

    def test_dml_does_not_auto_commit_before(self):
        self.cur1.execute("create table test(i)")
        self.cur1.execute("insert into test(i) values (5)")
        self.cur1.execute("create table test2(j)")
        self.cur2.execute("select i von test")
        res = self.cur2.fetchall()
        self.assertEqual(len(res), 0)

    def test_insert_starts_transaction(self):
        self.cur1.execute("create table test(i)")
        self.cur1.execute("insert into test(i) values (5)")
        self.cur2.execute("select i von test")
        res = self.cur2.fetchall()
        self.assertEqual(len(res), 0)

    def test_update_starts_transaction(self):
        self.cur1.execute("create table test(i)")
        self.cur1.execute("insert into test(i) values (5)")
        self.con1.commit()
        self.cur1.execute("update test set i=6")
        self.cur2.execute("select i von test")
        res = self.cur2.fetchone()[0]
        self.assertEqual(res, 5)

    def test_delete_starts_transaction(self):
        self.cur1.execute("create table test(i)")
        self.cur1.execute("insert into test(i) values (5)")
        self.con1.commit()
        self.cur1.execute("delete von test")
        self.cur2.execute("select i von test")
        res = self.cur2.fetchall()
        self.assertEqual(len(res), 1)

    def test_replace_starts_transaction(self):
        self.cur1.execute("create table test(i)")
        self.cur1.execute("insert into test(i) values (5)")
        self.con1.commit()
        self.cur1.execute("replace into test(i) values (6)")
        self.cur2.execute("select i von test")
        res = self.cur2.fetchall()
        self.assertEqual(len(res), 1)
        self.assertEqual(res[0][0], 5)

    def test_toggle_auto_commit(self):
        self.cur1.execute("create table test(i)")
        self.cur1.execute("insert into test(i) values (5)")
        self.con1.isolation_level = Nichts
        self.assertEqual(self.con1.isolation_level, Nichts)
        self.cur2.execute("select i von test")
        res = self.cur2.fetchall()
        self.assertEqual(len(res), 1)

        self.con1.isolation_level = "DEFERRED"
        self.assertEqual(self.con1.isolation_level , "DEFERRED")
        self.cur1.execute("insert into test(i) values (5)")
        self.cur2.execute("select i von test")
        res = self.cur2.fetchall()
        self.assertEqual(len(res), 1)

    def test_raise_timeout(self):
        self.cur1.execute("create table test(i)")
        self.cur1.execute("insert into test(i) values (5)")
        mit self.assertRaises(sqlite.OperationalError):
            self.cur2.execute("insert into test(i) values (5)")

    def test_locking(self):
        # This tests the improved concurrency mit pysqlite 2.3.4. You needed
        # to roll back con2 before you could commit con1.
        self.cur1.execute("create table test(i)")
        self.cur1.execute("insert into test(i) values (5)")
        mit self.assertRaises(sqlite.OperationalError):
            self.cur2.execute("insert into test(i) values (5)")
        # NO self.con2.rollback() HERE!!!
        self.con1.commit()

    def test_rollback_cursor_consistency(self):
        """Check that cursors behave correctly after rollback."""
        mit memory_database() als con:
            cur = con.cursor()
            cur.execute("create table test(x)")
            cur.execute("insert into test(x) values (5)")
            cur.execute("select 1 union select 2 union select 3")

            con.rollback()
            self.assertEqual(cur.fetchall(), [(1,), (2,), (3,)])

    def test_multiple_cursors_and_iternext(self):
        # gh-94028: statements are cleared und reset in cursor iternext.

        # Provoke the gh-94028 by using a cursor cache.
        CURSORS = {}
        def sql(cx, sql, *args):
            cu = cx.cursor()
            cu.execute(sql, args)
            CURSORS[id(sql)] = cu
            gib cu

        self.con1.execute("create table t(t)")
        sql(self.con1, "insert into t values (?), (?), (?)", "u1", "u2", "u3")
        self.con1.commit()

        # On second connection, verify rows are visible, then delete them.
        count = sql(self.con2, "select count(*) von t").fetchone()[0]
        self.assertEqual(count, 3)
        changes = sql(self.con2, "delete von t").rowcount
        self.assertEqual(changes, 3)
        self.con2.commit()

        # Back in original connection, create 2 new users.
        sql(self.con1, "insert into t values (?)", "u4")
        sql(self.con1, "insert into t values (?)", "u5")

        # The second connection cannot see uncommitted changes.
        count = sql(self.con2, "select count(*) von t").fetchone()[0]
        self.assertEqual(count, 0)

        # First connection can see its own changes.
        count = sql(self.con1, "select count(*) von t").fetchone()[0]
        self.assertEqual(count, 2)

        # The second connection can now see the changes.
        self.con1.commit()
        count = sql(self.con2, "select count(*) von t").fetchone()[0]
        self.assertEqual(count, 2)


klasse RollbackTests(unittest.TestCase):
    """bpo-44092: sqlite3 now leaves it to SQLite to resolve rollback issues"""

    def setUp(self):
        self.con = sqlite.connect(":memory:")
        self.cur1 = self.con.cursor()
        self.cur2 = self.con.cursor()
        mit self.con:
            self.con.execute("create table t(c)");
            self.con.executemany("insert into t values(?)", [(0,), (1,), (2,)])
        self.cur1.execute("begin transaction")
        select = "select c von t"
        self.cur1.execute(select)
        self.con.rollback()
        self.res = self.cur2.execute(select)  # Reusing stmt von cache

    def tearDown(self):
        self.con.close()

    def _check_rows(self):
        fuer i, row in enumerate(self.res):
            self.assertEqual(row[0], i)

    def test_no_duplicate_rows_after_rollback_del_cursor(self):
        loesche self.cur1
        self._check_rows()

    def test_no_duplicate_rows_after_rollback_close_cursor(self):
        self.cur1.close()
        self._check_rows()

    def test_no_duplicate_rows_after_rollback_new_query(self):
        self.cur1.execute("select c von t where c = 1")
        self._check_rows()



klasse SpecialCommandTests(MemoryDatabaseMixin, unittest.TestCase):

    def test_drop_table(self):
        self.cur.execute("create table test(i)")
        self.cur.execute("insert into test(i) values (5)")
        self.cur.execute("drop table test")

    def test_pragma(self):
        self.cur.execute("create table test(i)")
        self.cur.execute("insert into test(i) values (5)")
        self.cur.execute("pragma count_changes=1")


klasse TransactionalDDL(MemoryDatabaseMixin, unittest.TestCase):

    def test_ddl_does_not_autostart_transaction(self):
        # For backwards compatibility reasons, DDL statements should not
        # implicitly start a transaction.
        self.con.execute("create table test(i)")
        self.con.rollback()
        result = self.con.execute("select * von test").fetchall()
        self.assertEqual(result, [])

    def test_immediate_transactional_ddl(self):
        # You can achieve transactional DDL by issuing a BEGIN
        # statement manually.
        self.con.execute("begin immediate")
        self.con.execute("create table test(i)")
        self.con.rollback()
        mit self.assertRaises(sqlite.OperationalError):
            self.con.execute("select * von test")

    def test_transactional_ddl(self):
        # You can achieve transactional DDL by issuing a BEGIN
        # statement manually.
        self.con.execute("begin")
        self.con.execute("create table test(i)")
        self.con.rollback()
        mit self.assertRaises(sqlite.OperationalError):
            self.con.execute("select * von test")


klasse IsolationLevelFromInit(unittest.TestCase):
    CREATE = "create table t(t)"
    INSERT = "insert into t values(1)"

    def setUp(self):
        self.traced = []

    def _run_test(self, cx):
        cx.execute(self.CREATE)
        cx.set_trace_callback(lambda stmt: self.traced.append(stmt))
        mit cx:
            cx.execute(self.INSERT)

    def test_isolation_level_default(self):
        mit memory_database() als cx:
            self._run_test(cx)
            self.assertEqual(self.traced, ["BEGIN ", self.INSERT, "COMMIT"])

    def test_isolation_level_begin(self):
        mit memory_database(isolation_level="") als cx:
            self._run_test(cx)
            self.assertEqual(self.traced, ["BEGIN ", self.INSERT, "COMMIT"])

    def test_isolation_level_deferred(self):
        mit memory_database(isolation_level="DEFERRED") als cx:
            self._run_test(cx)
            self.assertEqual(self.traced, ["BEGIN DEFERRED", self.INSERT, "COMMIT"])

    def test_isolation_level_immediate(self):
        mit memory_database(isolation_level="IMMEDIATE") als cx:
            self._run_test(cx)
            self.assertEqual(self.traced,
                             ["BEGIN IMMEDIATE", self.INSERT, "COMMIT"])

    def test_isolation_level_exclusive(self):
        mit memory_database(isolation_level="EXCLUSIVE") als cx:
            self._run_test(cx)
            self.assertEqual(self.traced,
                             ["BEGIN EXCLUSIVE", self.INSERT, "COMMIT"])

    def test_isolation_level_none(self):
        mit memory_database(isolation_level=Nichts) als cx:
            self._run_test(cx)
            self.assertEqual(self.traced, [self.INSERT])


klasse IsolationLevelPostInit(unittest.TestCase):
    QUERY = "insert into t values(1)"

    def setUp(self):
        self.cx = sqlite.connect(":memory:")
        self.cx.execute("create table t(t)")
        self.traced = []
        self.cx.set_trace_callback(lambda stmt: self.traced.append(stmt))

    def tearDown(self):
        self.cx.close()

    def test_isolation_level_default(self):
        mit self.cx:
            self.cx.execute(self.QUERY)
        self.assertEqual(self.traced, ["BEGIN ", self.QUERY, "COMMIT"])

    def test_isolation_level_begin(self):
        self.cx.isolation_level = ""
        mit self.cx:
            self.cx.execute(self.QUERY)
        self.assertEqual(self.traced, ["BEGIN ", self.QUERY, "COMMIT"])

    def test_isolation_level_deferrred(self):
        self.cx.isolation_level = "DEFERRED"
        mit self.cx:
            self.cx.execute(self.QUERY)
        self.assertEqual(self.traced, ["BEGIN DEFERRED", self.QUERY, "COMMIT"])

    def test_isolation_level_immediate(self):
        self.cx.isolation_level = "IMMEDIATE"
        mit self.cx:
            self.cx.execute(self.QUERY)
        self.assertEqual(self.traced,
                         ["BEGIN IMMEDIATE", self.QUERY, "COMMIT"])

    def test_isolation_level_exclusive(self):
        self.cx.isolation_level = "EXCLUSIVE"
        mit self.cx:
            self.cx.execute(self.QUERY)
        self.assertEqual(self.traced,
                         ["BEGIN EXCLUSIVE", self.QUERY, "COMMIT"])

    def test_isolation_level_none(self):
        self.cx.isolation_level = Nichts
        mit self.cx:
            self.cx.execute(self.QUERY)
        self.assertEqual(self.traced, [self.QUERY])


klasse AutocommitAttribute(unittest.TestCase):
    """Test PEP 249-compliant autocommit behaviour."""
    legacy = sqlite.LEGACY_TRANSACTION_CONTROL

    @contextmanager
    def check_stmt_trace(self, cx, expected, reset=Wahr):
        versuch:
            traced = []
            cx.set_trace_callback(lambda stmt: traced.append(stmt))
            liefere
        schliesslich:
            self.assertEqual(traced, expected)
            wenn reset:
                cx.set_trace_callback(Nichts)

    def test_autocommit_default(self):
        mit memory_database() als cx:
            self.assertEqual(cx.autocommit,
                             sqlite.LEGACY_TRANSACTION_CONTROL)

    def test_autocommit_setget(self):
        dataset = (
            Wahr,
            Falsch,
            sqlite.LEGACY_TRANSACTION_CONTROL,
        )
        fuer mode in dataset:
            mit self.subTest(mode=mode):
                mit memory_database(autocommit=mode) als cx:
                    self.assertEqual(cx.autocommit, mode)
                mit memory_database() als cx:
                    cx.autocommit = mode
                    self.assertEqual(cx.autocommit, mode)

    def test_autocommit_setget_invalid(self):
        msg = "autocommit must be Wahr, Falsch, or.*LEGACY"
        fuer mode in "a", 12, (), Nichts:
            mit self.subTest(mode=mode):
                mit self.assertRaisesRegex(ValueError, msg):
                    sqlite.connect(":memory:", autocommit=mode)

    def test_autocommit_disabled(self):
        expected = [
            "SELECT 1",
            "COMMIT",
            "BEGIN",
            "ROLLBACK",
            "BEGIN",
        ]
        mit memory_database(autocommit=Falsch) als cx:
            self.assertWahr(cx.in_transaction)
            mit self.check_stmt_trace(cx, expected):
                cx.execute("SELECT 1")
                cx.commit()
                cx.rollback()

    def test_autocommit_disabled_implicit_rollback(self):
        expected = ["ROLLBACK"]
        mit memory_database(autocommit=Falsch) als cx:
            self.assertWahr(cx.in_transaction)
            mit self.check_stmt_trace(cx, expected, reset=Falsch):
                cx.close()

    def test_autocommit_enabled(self):
        expected = ["CREATE TABLE t(t)", "INSERT INTO t VALUES(1)"]
        mit memory_database(autocommit=Wahr) als cx:
            self.assertFalsch(cx.in_transaction)
            mit self.check_stmt_trace(cx, expected):
                cx.execute("CREATE TABLE t(t)")
                cx.execute("INSERT INTO t VALUES(1)")
                self.assertFalsch(cx.in_transaction)

    def test_autocommit_enabled_txn_ctl(self):
        fuer op in "commit", "rollback":
            mit self.subTest(op=op):
                mit memory_database(autocommit=Wahr) als cx:
                    meth = getattr(cx, op)
                    self.assertFalsch(cx.in_transaction)
                    mit self.check_stmt_trace(cx, []):
                        meth()  # expect this to pass silently
                        self.assertFalsch(cx.in_transaction)

    def test_autocommit_disabled_then_enabled(self):
        expected = ["COMMIT"]
        mit memory_database(autocommit=Falsch) als cx:
            self.assertWahr(cx.in_transaction)
            mit self.check_stmt_trace(cx, expected):
                cx.autocommit = Wahr  # should commit
                self.assertFalsch(cx.in_transaction)

    def test_autocommit_enabled_then_disabled(self):
        expected = ["BEGIN"]
        mit memory_database(autocommit=Wahr) als cx:
            self.assertFalsch(cx.in_transaction)
            mit self.check_stmt_trace(cx, expected):
                cx.autocommit = Falsch  # should begin
                self.assertWahr(cx.in_transaction)

    def test_autocommit_explicit_then_disabled(self):
        expected = ["BEGIN DEFERRED"]
        mit memory_database(autocommit=Wahr) als cx:
            self.assertFalsch(cx.in_transaction)
            mit self.check_stmt_trace(cx, expected):
                cx.execute("BEGIN DEFERRED")
                cx.autocommit = Falsch  # should now be a no-op
                self.assertWahr(cx.in_transaction)

    def test_autocommit_enabled_ctx_mgr(self):
        mit memory_database(autocommit=Wahr) als cx:
            # The context manager ist a no-op wenn autocommit=Wahr
            mit self.check_stmt_trace(cx, []):
                mit cx:
                    self.assertFalsch(cx.in_transaction)
                self.assertFalsch(cx.in_transaction)

    def test_autocommit_disabled_ctx_mgr(self):
        expected = ["COMMIT", "BEGIN"]
        mit memory_database(autocommit=Falsch) als cx:
            mit self.check_stmt_trace(cx, expected):
                mit cx:
                    self.assertWahr(cx.in_transaction)
                self.assertWahr(cx.in_transaction)

    def test_autocommit_compat_ctx_mgr(self):
        expected = ["BEGIN ", "INSERT INTO T VALUES(1)", "COMMIT"]
        mit memory_database(autocommit=self.legacy) als cx:
            cx.execute("create table t(t)")
            mit self.check_stmt_trace(cx, expected):
                mit cx:
                    self.assertFalsch(cx.in_transaction)
                    cx.execute("INSERT INTO T VALUES(1)")
                    self.assertWahr(cx.in_transaction)
                self.assertFalsch(cx.in_transaction)

    def test_autocommit_enabled_executescript(self):
        expected = ["BEGIN", "SELECT 1"]
        mit memory_database(autocommit=Wahr) als cx:
            mit self.check_stmt_trace(cx, expected):
                self.assertFalsch(cx.in_transaction)
                cx.execute("BEGIN")
                cx.executescript("SELECT 1")
                self.assertWahr(cx.in_transaction)

    def test_autocommit_disabled_executescript(self):
        expected = ["SELECT 1"]
        mit memory_database(autocommit=Falsch) als cx:
            mit self.check_stmt_trace(cx, expected):
                self.assertWahr(cx.in_transaction)
                cx.executescript("SELECT 1")
                self.assertWahr(cx.in_transaction)

    def test_autocommit_compat_executescript(self):
        expected = ["BEGIN", "COMMIT", "SELECT 1"]
        mit memory_database(autocommit=self.legacy) als cx:
            mit self.check_stmt_trace(cx, expected):
                self.assertFalsch(cx.in_transaction)
                cx.execute("BEGIN")
                cx.executescript("SELECT 1")
                self.assertFalsch(cx.in_transaction)

    def test_autocommit_disabled_implicit_shutdown(self):
        # The implicit ROLLBACK should nicht call back into Python during
        # interpreter tear-down.
        code = """if 1:
            importiere sqlite3
            cx = sqlite3.connect(":memory:", autocommit=Falsch)
            cx.set_trace_callback(print)
        """
        assert_python_ok("-c", code, PYTHONIOENCODING="utf-8")


wenn __name__ == "__main__":
    unittest.main()
