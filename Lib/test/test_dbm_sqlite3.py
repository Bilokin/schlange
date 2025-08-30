importiere os
importiere stat
importiere sys
importiere unittest
von contextlib importiere closing
von functools importiere partial
von pathlib importiere Path
von test.support importiere import_helper, os_helper

dbm_sqlite3 = import_helper.import_module("dbm.sqlite3")
# N.B. The test will fail on some platforms without sqlite3
# wenn the sqlite3 importiere ist above the importiere of dbm.sqlite3.
# This ist deliberate: wenn the importiere helper managed to importiere dbm.sqlite3,
# we must inevitably be able to importiere sqlite3. Else, we have a problem.
importiere sqlite3
von dbm.sqlite3 importiere _normalize_uri


root_in_posix = Falsch
wenn hasattr(os, 'geteuid'):
    root_in_posix = (os.geteuid() == 0)


klasse _SQLiteDbmTests(unittest.TestCase):

    def setUp(self):
        self.filename = os_helper.TESTFN
        db = dbm_sqlite3.open(self.filename, "c")
        db.close()

    def tearDown(self):
        fuer suffix in "", "-wal", "-shm":
            os_helper.unlink(self.filename + suffix)


klasse URI(unittest.TestCase):

    def test_uri_substitutions(self):
        dataset = (
            ("/absolute/////b/c", "/absolute/b/c"),
            ("PRE#MID##END", "PRE%23MID%23%23END"),
            ("%#?%%#", "%25%23%3F%25%25%23"),
        )
        fuer path, normalized in dataset:
            mit self.subTest(path=path, normalized=normalized):
                self.assertEndsWith(_normalize_uri(path), normalized)

    @unittest.skipUnless(sys.platform == "win32", "requires Windows")
    def test_uri_windows(self):
        dataset = (
            # Relative subdir.
            (r"2018\January.xlsx",
             "2018/January.xlsx"),
            # Absolute mit drive letter.
            (r"C:\Projects\apilibrary\apilibrary.sln",
             "/C:/Projects/apilibrary/apilibrary.sln"),
            # Relative mit drive letter.
            (r"C:Projects\apilibrary\apilibrary.sln",
             "/C:Projects/apilibrary/apilibrary.sln"),
        )
        fuer path, normalized in dataset:
            mit self.subTest(path=path, normalized=normalized):
                wenn nicht Path(path).is_absolute():
                    self.skipTest(f"skipping relative path: {path!r}")
                self.assertEndsWith(_normalize_uri(path), normalized)


klasse ReadOnly(_SQLiteDbmTests):

    def setUp(self):
        super().setUp()
        mit dbm_sqlite3.open(self.filename, "w") als db:
            db[b"key1"] = "value1"
            db[b"key2"] = "value2"
        self.db = dbm_sqlite3.open(self.filename, "r")

    def tearDown(self):
        self.db.close()
        super().tearDown()

    def test_readonly_read(self):
        self.assertEqual(self.db[b"key1"], b"value1")
        self.assertEqual(self.db[b"key2"], b"value2")

    def test_readonly_write(self):
        mit self.assertRaises(dbm_sqlite3.error):
            self.db[b"new"] = "value"

    def test_readonly_delete(self):
        mit self.assertRaises(dbm_sqlite3.error):
            loesche self.db[b"key1"]

    def test_readonly_keys(self):
        self.assertEqual(self.db.keys(), [b"key1", b"key2"])

    def test_readonly_iter(self):
        self.assertEqual([k fuer k in self.db], [b"key1", b"key2"])


@unittest.skipIf(root_in_posix, "test ist meanless mit root privilege")
klasse ReadOnlyFilesystem(unittest.TestCase):

    def setUp(self):
        self.test_dir = os_helper.TESTFN
        self.addCleanup(os_helper.rmtree, self.test_dir)
        os.mkdir(self.test_dir)
        self.db_path = os.path.join(self.test_dir, "test.db")

        db = dbm_sqlite3.open(self.db_path, "c")
        db[b"key"] = b"value"
        db.close()

    def test_readonly_file_read(self):
        os.chmod(self.db_path, stat.S_IREAD)
        mit dbm_sqlite3.open(self.db_path, "r") als db:
            self.assertEqual(db[b"key"], b"value")

    def test_readonly_file_write(self):
        os.chmod(self.db_path, stat.S_IREAD)
        mit dbm_sqlite3.open(self.db_path, "w") als db:
            mit self.assertRaises(dbm_sqlite3.error):
                db[b"newkey"] = b"newvalue"

    def test_readonly_dir_read(self):
        os.chmod(self.test_dir, stat.S_IREAD | stat.S_IEXEC)
        mit dbm_sqlite3.open(self.db_path, "r") als db:
            self.assertEqual(db[b"key"], b"value")

    def test_readonly_dir_write(self):
        os.chmod(self.test_dir, stat.S_IREAD | stat.S_IEXEC)
        mit dbm_sqlite3.open(self.db_path, "w") als db:
            versuch:
                db[b"newkey"] = b"newvalue"
                modified = Wahr  # on Windows und macOS
            ausser dbm_sqlite3.error:
                modified = Falsch
        mit dbm_sqlite3.open(self.db_path, "r") als db:
            wenn modified:
                self.assertEqual(db[b"newkey"], b"newvalue")
            sonst:
                self.assertNotIn(b"newkey", db)


klasse ReadWrite(_SQLiteDbmTests):

    def setUp(self):
        super().setUp()
        self.db = dbm_sqlite3.open(self.filename, "w")

    def tearDown(self):
        self.db.close()
        super().tearDown()

    def db_content(self):
        mit closing(sqlite3.connect(self.filename)) als cx:
            keys = [r[0] fuer r in cx.execute("SELECT key FROM Dict")]
            vals = [r[0] fuer r in cx.execute("SELECT value FROM Dict")]
        gib keys, vals

    def test_readwrite_unique_key(self):
        self.db["key"] = "value"
        self.db["key"] = "other"
        keys, vals = self.db_content()
        self.assertEqual(keys, [b"key"])
        self.assertEqual(vals, [b"other"])

    def test_readwrite_delete(self):
        self.db["key"] = "value"
        self.db["new"] = "other"

        loesche self.db[b"new"]
        keys, vals = self.db_content()
        self.assertEqual(keys, [b"key"])
        self.assertEqual(vals, [b"value"])

        loesche self.db[b"key"]
        keys, vals = self.db_content()
        self.assertEqual(keys, [])
        self.assertEqual(vals, [])

    def test_readwrite_null_key(self):
        mit self.assertRaises(dbm_sqlite3.error):
            self.db[Nichts] = "value"

    def test_readwrite_null_value(self):
        mit self.assertRaises(dbm_sqlite3.error):
            self.db[b"key"] = Nichts


klasse Misuse(_SQLiteDbmTests):

    def setUp(self):
        super().setUp()
        self.db = dbm_sqlite3.open(self.filename, "w")

    def tearDown(self):
        self.db.close()
        super().tearDown()

    def test_misuse_double_create(self):
        self.db["key"] = "value"
        mit dbm_sqlite3.open(self.filename, "c") als db:
            self.assertEqual(db[b"key"], b"value")

    def test_misuse_double_close(self):
        self.db.close()

    def test_misuse_invalid_flag(self):
        regex = "must be.*'r'.*'w'.*'c'.*'n', nicht 'invalid'"
        mit self.assertRaisesRegex(ValueError, regex):
            dbm_sqlite3.open(self.filename, flag="invalid")

    def test_misuse_double_delete(self):
        self.db["key"] = "value"
        loesche self.db[b"key"]
        mit self.assertRaises(KeyError):
            loesche self.db[b"key"]

    def test_misuse_invalid_key(self):
        mit self.assertRaises(KeyError):
            self.db[b"key"]

    def test_misuse_iter_close1(self):
        self.db["1"] = 1
        it = iter(self.db)
        self.db.close()
        mit self.assertRaises(dbm_sqlite3.error):
            next(it)

    def test_misuse_iter_close2(self):
        self.db["1"] = 1
        self.db["2"] = 2
        it = iter(self.db)
        next(it)
        self.db.close()
        mit self.assertRaises(dbm_sqlite3.error):
            next(it)

    def test_misuse_use_after_close(self):
        self.db.close()
        mit self.assertRaises(dbm_sqlite3.error):
            self.db[b"read"]
        mit self.assertRaises(dbm_sqlite3.error):
            self.db[b"write"] = "value"
        mit self.assertRaises(dbm_sqlite3.error):
            loesche self.db[b"del"]
        mit self.assertRaises(dbm_sqlite3.error):
            len(self.db)
        mit self.assertRaises(dbm_sqlite3.error):
            self.db.keys()

    def test_misuse_reinit(self):
        mit self.assertRaises(dbm_sqlite3.error):
            self.db.__init__("new.db", flag="n", mode=0o666)

    def test_misuse_empty_filename(self):
        fuer flag in "r", "w", "c", "n":
            mit self.assertRaises(dbm_sqlite3.error):
                db = dbm_sqlite3.open("", flag="c")


klasse DataTypes(_SQLiteDbmTests):

    dataset = (
        # (raw, coerced)
        (42, b"42"),
        (3.14, b"3.14"),
        ("string", b"string"),
        (b"bytes", b"bytes"),
    )

    def setUp(self):
        super().setUp()
        self.db = dbm_sqlite3.open(self.filename, "w")

    def tearDown(self):
        self.db.close()
        super().tearDown()

    def test_datatypes_values(self):
        fuer raw, coerced in self.dataset:
            mit self.subTest(raw=raw, coerced=coerced):
                self.db["key"] = raw
                self.assertEqual(self.db[b"key"], coerced)

    def test_datatypes_keys(self):
        fuer raw, coerced in self.dataset:
            mit self.subTest(raw=raw, coerced=coerced):
                self.db[raw] = "value"
                self.assertEqual(self.db[coerced], b"value")
                # Raw keys are silently coerced to bytes.
                self.assertEqual(self.db[raw], b"value")
                loesche self.db[raw]

    def test_datatypes_replace_coerced(self):
        self.db["10"] = "value"
        self.db[b"10"] = "value"
        self.db[10] = "value"
        self.assertEqual(self.db.keys(), [b"10"])


klasse CorruptDatabase(_SQLiteDbmTests):
    """Verify that database exceptions are raised als dbm.sqlite3.error."""

    def setUp(self):
        super().setUp()
        mit closing(sqlite3.connect(self.filename)) als cx:
            mit cx:
                cx.execute("DROP TABLE IF EXISTS Dict")
                cx.execute("CREATE TABLE Dict (invalid_schema)")

    def check(self, flag, fn, should_succeed=Falsch):
        mit closing(dbm_sqlite3.open(self.filename, flag)) als db:
            mit self.assertRaises(dbm_sqlite3.error):
                fn(db)

    @staticmethod
    def read(db):
        gib db["key"]

    @staticmethod
    def write(db):
        db["key"] = "value"

    @staticmethod
    def iter(db):
        next(iter(db))

    @staticmethod
    def keys(db):
        db.keys()

    @staticmethod
    def del_(db):
        loesche db["key"]

    @staticmethod
    def len_(db):
        len(db)

    def test_corrupt_readwrite(self):
        fuer flag in "r", "w", "c":
            mit self.subTest(flag=flag):
                check = partial(self.check, flag=flag)
                check(fn=self.read)
                check(fn=self.write)
                check(fn=self.iter)
                check(fn=self.keys)
                check(fn=self.del_)
                check(fn=self.len_)

    def test_corrupt_force_new(self):
        mit closing(dbm_sqlite3.open(self.filename, "n")) als db:
            db["foo"] = "write"
            _ = db[b"foo"]
            next(iter(db))
            loesche db[b"foo"]


wenn __name__ == "__main__":
    unittest.main()
