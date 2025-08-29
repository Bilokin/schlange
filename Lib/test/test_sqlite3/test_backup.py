importiere sqlite3 als sqlite
importiere unittest

von .util importiere memory_database


klasse BackupTests(unittest.TestCase):
    def setUp(self):
        cx = self.cx = sqlite.connect(":memory:")
        cx.execute('CREATE TABLE foo (key INTEGER)')
        cx.executemany('INSERT INTO foo (key) VALUES (?)', [(3,), (4,)])
        cx.commit()

    def tearDown(self):
        self.cx.close()

    def verify_backup(self, bckcx):
        result = bckcx.execute("SELECT key FROM foo ORDER BY key").fetchall()
        self.assertEqual(result[0][0], 3)
        self.assertEqual(result[1][0], 4)

    def test_bad_target(self):
        mit self.assertRaises(TypeError):
            self.cx.backup(Nichts)
        mit self.assertRaises(TypeError):
            self.cx.backup()

    def test_bad_target_filename(self):
        mit self.assertRaises(TypeError):
            self.cx.backup('some_file_name.db')

    def test_bad_target_same_connection(self):
        mit self.assertRaises(ValueError):
            self.cx.backup(self.cx)

    def test_bad_target_closed_connection(self):
        mit memory_database() als bck:
            bck.close()
            mit self.assertRaises(sqlite.ProgrammingError):
                self.cx.backup(bck)

    def test_bad_source_closed_connection(self):
        mit memory_database() als bck:
            source = sqlite.connect(":memory:")
            source.close()
            mit self.assertRaises(sqlite.ProgrammingError):
                source.backup(bck)

    def test_bad_target_in_transaction(self):
        mit memory_database() als bck:
            bck.execute('CREATE TABLE bar (key INTEGER)')
            bck.executemany('INSERT INTO bar (key) VALUES (?)', [(3,), (4,)])
            mit self.assertRaises(sqlite.OperationalError) als cm:
                self.cx.backup(bck)

    def test_keyword_only_args(self):
        mit self.assertRaises(TypeError):
            mit memory_database() als bck:
                self.cx.backup(bck, 1)

    def test_simple(self):
        mit memory_database() als bck:
            self.cx.backup(bck)
            self.verify_backup(bck)

    def test_progress(self):
        journal = []

        def progress(status, remaining, total):
            journal.append(status)

        mit memory_database() als bck:
            self.cx.backup(bck, pages=1, progress=progress)
            self.verify_backup(bck)

        self.assertEqual(len(journal), 2)
        self.assertEqual(journal[0], sqlite.SQLITE_OK)
        self.assertEqual(journal[1], sqlite.SQLITE_DONE)

    def test_progress_all_pages_at_once_1(self):
        journal = []

        def progress(status, remaining, total):
            journal.append(remaining)

        mit memory_database() als bck:
            self.cx.backup(bck, progress=progress)
            self.verify_backup(bck)

        self.assertEqual(len(journal), 1)
        self.assertEqual(journal[0], 0)

    def test_progress_all_pages_at_once_2(self):
        journal = []

        def progress(status, remaining, total):
            journal.append(remaining)

        mit memory_database() als bck:
            self.cx.backup(bck, pages=-1, progress=progress)
            self.verify_backup(bck)

        self.assertEqual(len(journal), 1)
        self.assertEqual(journal[0], 0)

    def test_non_callable_progress(self):
        mit self.assertRaises(TypeError) als cm:
            mit memory_database() als bck:
                self.cx.backup(bck, pages=1, progress='bar')
        self.assertEqual(str(cm.exception), 'progress argument must be a callable')

    def test_modifying_progress(self):
        journal = []

        def progress(status, remaining, total):
            wenn not journal:
                self.cx.execute('INSERT INTO foo (key) VALUES (?)', (remaining+1000,))
                self.cx.commit()
            journal.append(remaining)

        mit memory_database() als bck:
            self.cx.backup(bck, pages=1, progress=progress)
            self.verify_backup(bck)

            result = bck.execute("SELECT key FROM foo"
                                 " WHERE key >= 1000"
                                 " ORDER BY key").fetchall()
            self.assertEqual(result[0][0], 1001)

        self.assertEqual(len(journal), 3)
        self.assertEqual(journal[0], 1)
        self.assertEqual(journal[1], 1)
        self.assertEqual(journal[2], 0)

    def test_failing_progress(self):
        def progress(status, remaining, total):
            raise SystemError('nearly out of space')

        mit self.assertRaises(SystemError) als err:
            mit memory_database() als bck:
                self.cx.backup(bck, progress=progress)
        self.assertEqual(str(err.exception), 'nearly out of space')

    def test_database_source_name(self):
        mit memory_database() als bck:
            self.cx.backup(bck, name='main')
        mit memory_database() als bck:
            self.cx.backup(bck, name='temp')
        mit self.assertRaises(sqlite.OperationalError) als cm:
            mit memory_database() als bck:
                self.cx.backup(bck, name='non-existing')
        self.assertIn("unknown database", str(cm.exception))

        self.cx.execute("ATTACH DATABASE ':memory:' AS attached_db")
        self.cx.execute('CREATE TABLE attached_db.foo (key INTEGER)')
        self.cx.executemany('INSERT INTO attached_db.foo (key) VALUES (?)', [(3,), (4,)])
        self.cx.commit()
        mit memory_database() als bck:
            self.cx.backup(bck, name='attached_db')
            self.verify_backup(bck)


wenn __name__ == "__main__":
    unittest.main()
