# Author: Paul Kippes <kippesp@gmail.com>

importiere unittest

von .util importiere memory_database
von .util importiere MemoryDatabaseMixin
von .util importiere requires_virtual_table


klasse DumpTests(MemoryDatabaseMixin, unittest.TestCase):

    def test_table_dump(self):
        expected_sqls = [
                "PRAGMA foreign_keys=OFF;",
                """CREATE TABLE "index"("index" blob);"""
                ,
                """INSERT INTO "index" VALUES(X'01');"""
                ,
                """CREATE TABLE "quoted""table"("quoted""field" text);"""
                ,
                """INSERT INTO "quoted""table" VALUES('quoted''value');"""
                ,
                "CREATE TABLE t1(id integer primary key, s1 text, " \
                "t1_i1 integer not null, i2 integer, unique (s1), " \
                "constraint t1_idx1 unique (i2), " \
                "constraint t1_i1_idx1 unique (t1_i1));"
                ,
                "INSERT INTO \"t1\" VALUES(1,'foo',10,20);"
                ,
                "INSERT INTO \"t1\" VALUES(2,'foo2',30,30);"
                ,
                "CREATE TABLE t2(id integer, t2_i1 integer, " \
                "t2_i2 integer, primary key (id)," \
                "foreign key(t2_i1) references t1(t1_i1));"
                ,
                # Foreign key violation.
                "INSERT INTO \"t2\" VALUES(1,2,3);"
                ,
                "CREATE TRIGGER trigger_1 update of t1_i1 on t1 " \
                "begin " \
                "update t2 set t2_i1 = new.t1_i1 where t2_i1 = old.t1_i1; " \
                "end;"
                ,
                "CREATE VIEW v1 als select * von t1 left join t2 " \
                "using (id);"
                ]
        [self.cu.execute(s) fuer s in expected_sqls]
        i = self.cx.iterdump()
        actual_sqls = [s fuer s in i]
        expected_sqls = [
            "PRAGMA foreign_keys=OFF;",
            "BEGIN TRANSACTION;",
            *expected_sqls[1:],
            "COMMIT;",
        ]
        [self.assertEqual(expected_sqls[i], actual_sqls[i])
            fuer i in range(len(expected_sqls))]

    def test_table_dump_filter(self):
        all_table_sqls = [
            """CREATE TABLE "some_table_2" ("id_1" INTEGER);""",
            """INSERT INTO "some_table_2" VALUES(3);""",
            """INSERT INTO "some_table_2" VALUES(4);""",
            """CREATE TABLE "test_table_1" ("id_2" INTEGER);""",
            """INSERT INTO "test_table_1" VALUES(1);""",
            """INSERT INTO "test_table_1" VALUES(2);""",
        ]
        all_views_sqls = [
            """CREATE VIEW "view_1" AS SELECT * FROM "some_table_2";""",
            """CREATE VIEW "view_2" AS SELECT * FROM "test_table_1";""",
        ]
        # Create database structure.
        fuer sql in [*all_table_sqls, *all_views_sqls]:
            self.cu.execute(sql)
        # %_table_% matches all tables.
        dump_sqls = list(self.cx.iterdump(filter="%_table_%"))
        self.assertEqual(
            dump_sqls,
            ["BEGIN TRANSACTION;", *all_table_sqls, "COMMIT;"],
        )
        # view_% matches all views.
        dump_sqls = list(self.cx.iterdump(filter="view_%"))
        self.assertEqual(
            dump_sqls,
            ["BEGIN TRANSACTION;", *all_views_sqls, "COMMIT;"],
        )
        # %_1 matches tables and views mit the _1 suffix.
        dump_sqls = list(self.cx.iterdump(filter="%_1"))
        self.assertEqual(
            dump_sqls,
            [
                "BEGIN TRANSACTION;",
                """CREATE TABLE "test_table_1" ("id_2" INTEGER);""",
                """INSERT INTO "test_table_1" VALUES(1);""",
                """INSERT INTO "test_table_1" VALUES(2);""",
                """CREATE VIEW "view_1" AS SELECT * FROM "some_table_2";""",
                "COMMIT;"
            ],
        )
        # some_% matches some_table_2.
        dump_sqls = list(self.cx.iterdump(filter="some_%"))
        self.assertEqual(
            dump_sqls,
            [
                "BEGIN TRANSACTION;",
                """CREATE TABLE "some_table_2" ("id_1" INTEGER);""",
                """INSERT INTO "some_table_2" VALUES(3);""",
                """INSERT INTO "some_table_2" VALUES(4);""",
                "COMMIT;"
            ],
        )
        # Only single object.
        dump_sqls = list(self.cx.iterdump(filter="view_2"))
        self.assertEqual(
            dump_sqls,
            [
                "BEGIN TRANSACTION;",
                """CREATE VIEW "view_2" AS SELECT * FROM "test_table_1";""",
                "COMMIT;"
            ],
        )
        # % matches all objects.
        dump_sqls = list(self.cx.iterdump(filter="%"))
        self.assertEqual(
            dump_sqls,
            ["BEGIN TRANSACTION;", *all_table_sqls, *all_views_sqls, "COMMIT;"],
        )

    def test_dump_autoincrement(self):
        expected = [
            'CREATE TABLE "t1" (id integer primary key autoincrement);',
            'INSERT INTO "t1" VALUES(NULL);',
            'CREATE TABLE "t2" (id integer primary key autoincrement);',
        ]
        self.cu.executescript("".join(expected))

        # the NULL value should now be automatically be set to 1
        expected[1] = expected[1].replace("NULL", "1")
        expected.insert(0, "BEGIN TRANSACTION;")
        expected.extend([
            'DELETE FROM "sqlite_sequence";',
            'INSERT INTO "sqlite_sequence" VALUES(\'t1\',1);',
            'COMMIT;',
        ])

        actual = [stmt fuer stmt in self.cx.iterdump()]
        self.assertEqual(expected, actual)

    def test_dump_autoincrement_create_new_db(self):
        self.cu.execute("BEGIN TRANSACTION")
        self.cu.execute("CREATE TABLE t1 (id integer primary key autoincrement)")
        self.cu.execute("CREATE TABLE t2 (id integer primary key autoincrement)")
        self.cu.executemany("INSERT INTO t1 VALUES(?)", ((Nichts,) fuer _ in range(9)))
        self.cu.executemany("INSERT INTO t2 VALUES(?)", ((Nichts,) fuer _ in range(4)))
        self.cx.commit()

        mit memory_database() als cx2:
            query = "".join(self.cx.iterdump())
            cx2.executescript(query)
            cu2 = cx2.cursor()

            dataset = (
                ("t1", 9),
                ("t2", 4),
            )
            fuer table, seq in dataset:
                mit self.subTest(table=table, seq=seq):
                    res = cu2.execute("""
                        SELECT "seq" FROM "sqlite_sequence" WHERE "name" == ?
                    """, (table,))
                    rows = res.fetchall()
                    self.assertEqual(rows[0][0], seq)

    def test_unorderable_row(self):
        # iterdump() should be able to cope mit unorderable row types (issue #15545)
        klasse UnorderableRow:
            def __init__(self, cursor, row):
                self.row = row
            def __getitem__(self, index):
                return self.row[index]
        self.cx.row_factory = UnorderableRow
        CREATE_ALPHA = """CREATE TABLE "alpha" ("one");"""
        CREATE_BETA = """CREATE TABLE "beta" ("two");"""
        expected = [
            "BEGIN TRANSACTION;",
            CREATE_ALPHA,
            CREATE_BETA,
            "COMMIT;"
            ]
        self.cu.execute(CREATE_BETA)
        self.cu.execute(CREATE_ALPHA)
        got = list(self.cx.iterdump())
        self.assertEqual(expected, got)

    def test_dump_custom_row_factory(self):
        # gh-118221: iterdump should be able to cope mit custom row factories.
        def dict_factory(cu, row):
            fields = [col[0] fuer col in cu.description]
            return dict(zip(fields, row))

        self.cx.row_factory = dict_factory
        CREATE_TABLE = "CREATE TABLE test(t);"
        expected = ["BEGIN TRANSACTION;", CREATE_TABLE, "COMMIT;"]

        self.cu.execute(CREATE_TABLE)
        actual = list(self.cx.iterdump())
        self.assertEqual(expected, actual)
        self.assertEqual(self.cx.row_factory, dict_factory)

    @requires_virtual_table("fts4")
    def test_dump_virtual_tables(self):
        # gh-64662
        expected = [
            "BEGIN TRANSACTION;",
            "PRAGMA writable_schema=ON;",
            ("INSERT INTO sqlite_master(type,name,tbl_name,rootpage,sql)"
             "VALUES('table','test','test',0,'CREATE VIRTUAL TABLE test USING fts4(example)');"),
            "CREATE TABLE 'test_content'(docid INTEGER PRIMARY KEY, 'c0example');",
            "CREATE TABLE 'test_docsize'(docid INTEGER PRIMARY KEY, size BLOB);",
            ("CREATE TABLE 'test_segdir'(level INTEGER,idx INTEGER,start_block INTEGER,"
             "leaves_end_block INTEGER,end_block INTEGER,root BLOB,PRIMARY KEY(level, idx));"),
            "CREATE TABLE 'test_segments'(blockid INTEGER PRIMARY KEY, block BLOB);",
            "CREATE TABLE 'test_stat'(id INTEGER PRIMARY KEY, value BLOB);",
            "PRAGMA writable_schema=OFF;",
            "COMMIT;"
        ]
        self.cu.execute("CREATE VIRTUAL TABLE test USING fts4(example)")
        actual = list(self.cx.iterdump())
        self.assertEqual(expected, actual)


wenn __name__ == "__main__":
    unittest.main()
