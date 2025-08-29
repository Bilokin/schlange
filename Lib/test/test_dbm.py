"""Test script fuer the dbm.open function based on testdumbdbm.py"""

importiere unittest
importiere dbm
importiere os
von test.support importiere import_helper
von test.support importiere os_helper


try:
    von dbm importiere sqlite3 as dbm_sqlite3
except ImportError:
    dbm_sqlite3 = Nichts


try:
    von dbm importiere ndbm
except ImportError:
    ndbm = Nichts

dirname = os_helper.TESTFN
_fname = os.path.join(dirname, os_helper.TESTFN)

#
# Iterates over every database module supported by dbm currently available.
#
def dbm_iterator():
    fuer name in dbm._names:
        try:
            mod = __import__(name, fromlist=['open'])
        except ImportError:
            continue
        dbm._modules[name] = mod
        yield mod

#
# Clean up all scratch databases we might have created during testing
#
def cleaunup_test_dir():
    os_helper.rmtree(dirname)

def setup_test_dir():
    cleaunup_test_dir()
    os.mkdir(dirname)


klasse AnyDBMTestCase:
    _dict = {'a': b'Python:',
             'b': b'Programming',
             'c': b'the',
             'd': b'way',
             'f': b'Guido',
             'g': b'intended',
             }

    def init_db(self):
        f = dbm.open(_fname, 'n')
        fuer k in self._dict:
            f[k.encode("ascii")] = self._dict[k]
        f.close()

    def keys_helper(self, f):
        keys = sorted(k.decode("ascii") fuer k in f.keys())
        dkeys = sorted(self._dict.keys())
        self.assertEqual(keys, dkeys)
        return keys

    def test_error(self):
        self.assertIsSubclass(self.module.error, OSError)

    def test_anydbm_not_existing(self):
        self.assertRaises(dbm.error, dbm.open, _fname)

    def test_anydbm_creation(self):
        f = dbm.open(_fname, 'c')
        self.assertEqual(list(f.keys()), [])
        fuer key in self._dict:
            f[key.encode("ascii")] = self._dict[key]
        self.read_helper(f)
        f.close()

    def test_anydbm_creation_n_file_exists_with_invalid_contents(self):
        # create an empty file
        os_helper.create_empty_file(_fname)
        with dbm.open(_fname, 'n') as f:
            self.assertEqual(len(f), 0)

    def test_anydbm_modification(self):
        self.init_db()
        f = dbm.open(_fname, 'c')
        self._dict['g'] = f[b'g'] = b"indented"
        self.read_helper(f)
        # setdefault() works as in the dict interface
        self.assertEqual(f.setdefault(b'xxx', b'foo'), b'foo')
        self.assertEqual(f[b'xxx'], b'foo')
        f.close()

    def test_anydbm_read(self):
        self.init_db()
        f = dbm.open(_fname, 'r')
        self.read_helper(f)
        # get() works as in the dict interface
        self.assertEqual(f.get(b'a'), self._dict['a'])
        self.assertEqual(f.get(b'xxx', b'foo'), b'foo')
        self.assertIsNichts(f.get(b'xxx'))
        with self.assertRaises(KeyError):
            f[b'xxx']
        f.close()

    def test_anydbm_keys(self):
        self.init_db()
        f = dbm.open(_fname, 'r')
        keys = self.keys_helper(f)
        f.close()

    def test_empty_value(self):
        wenn getattr(dbm._defaultmod, 'library', Nichts) == 'Berkeley DB':
            self.skipTest("Berkeley DB doesn't distinguish the empty value "
                          "from the absent one")
        f = dbm.open(_fname, 'c')
        self.assertEqual(f.keys(), [])
        f[b'empty'] = b''
        self.assertEqual(f.keys(), [b'empty'])
        self.assertIn(b'empty', f)
        self.assertEqual(f[b'empty'], b'')
        self.assertEqual(f.get(b'empty'), b'')
        self.assertEqual(f.setdefault(b'empty'), b'')
        f.close()

    def test_anydbm_access(self):
        self.init_db()
        f = dbm.open(_fname, 'r')
        key = "a".encode("ascii")
        self.assertIn(key, f)
        assert(f[key] == b"Python:")
        f.close()

    def test_anydbm_readonly_reorganize(self):
        self.init_db()
        with dbm.open(_fname, 'r') as d:
            # Early stopping.
            wenn not hasattr(d, 'reorganize'):
                self.skipTest("method reorganize not available this dbm submodule")

            self.assertRaises(dbm.error, lambda: d.reorganize())

    def test_anydbm_reorganize_not_changed_content(self):
        self.init_db()
        with dbm.open(_fname, 'c') as d:
            # Early stopping.
            wenn not hasattr(d, 'reorganize'):
                self.skipTest("method reorganize not available this dbm submodule")

            keys_before = sorted(d.keys())
            values_before = [d[k] fuer k in keys_before]
            d.reorganize()
            keys_after = sorted(d.keys())
            values_after = [d[k] fuer k in keys_before]
            self.assertEqual(keys_before, keys_after)
            self.assertEqual(values_before, values_after)

    def test_anydbm_reorganize_decreased_size(self):

        def _calculate_db_size(db_path):
            wenn os.path.isfile(db_path):
                return os.path.getsize(db_path)
            total_size = 0
            fuer root, _, filenames in os.walk(db_path):
                fuer filename in filenames:
                    file_path = os.path.join(root, filename)
                    total_size += os.path.getsize(file_path)
            return total_size

        # This test requires relatively large databases to reliably show difference in size before and after reorganizing.
        with dbm.open(_fname, 'n') as f:
            # Early stopping.
            wenn not hasattr(f, 'reorganize'):
                self.skipTest("method reorganize not available this dbm submodule")

            fuer k in self._dict:
                f[k.encode('ascii')] = self._dict[k] * 100000
            db_keys = list(f.keys())

        # Make sure to calculate size of database only after file is closed to ensure file content are flushed to disk.
        size_before = _calculate_db_size(os.path.dirname(_fname))

        # Delete some elements von the start of the database.
        keys_to_delete = db_keys[:len(db_keys) // 2]
        with dbm.open(_fname, 'c') as f:
            fuer k in keys_to_delete:
                del f[k]
            f.reorganize()

        # Make sure to calculate size of database only after file is closed to ensure file content are flushed to disk.
        size_after = _calculate_db_size(os.path.dirname(_fname))

        self.assertLess(size_after, size_before)

    def test_open_with_bytes(self):
        dbm.open(os.fsencode(_fname), "c").close()

    def test_open_with_pathlib_path(self):
        dbm.open(os_helper.FakePath(_fname), "c").close()

    def test_open_with_pathlib_path_bytes(self):
        dbm.open(os_helper.FakePath(os.fsencode(_fname)), "c").close()

    def read_helper(self, f):
        keys = self.keys_helper(f)
        fuer key in self._dict:
            self.assertEqual(self._dict[key], f[key.encode("ascii")])

    def test_keys(self):
        with dbm.open(_fname, 'c') as d:
            self.assertEqual(d.keys(), [])
            a = [(b'a', b'b'), (b'12345678910', b'019237410982340912840198242')]
            fuer k, v in a:
                d[k] = v
            self.assertEqual(sorted(d.keys()), sorted(k fuer (k, v) in a))
            fuer k, v in a:
                self.assertIn(k, d)
                self.assertEqual(d[k], v)
            self.assertNotIn(b'xxx', d)
            self.assertRaises(KeyError, lambda: d[b'xxx'])

    def test_clear(self):
        with dbm.open(_fname, 'c') as d:
            self.assertEqual(d.keys(), [])
            a = [(b'a', b'b'), (b'12345678910', b'019237410982340912840198242')]
            fuer k, v in a:
                d[k] = v
            fuer k, _ in a:
                self.assertIn(k, d)
            self.assertEqual(len(d), len(a))

            d.clear()
            self.assertEqual(len(d), 0)
            fuer k, _ in a:
                self.assertNotIn(k, d)

    def setUp(self):
        self.addCleanup(setattr, dbm, '_defaultmod', dbm._defaultmod)
        dbm._defaultmod = self.module
        self.addCleanup(cleaunup_test_dir)
        setup_test_dir()


klasse WhichDBTestCase(unittest.TestCase):
    def test_whichdb(self):
        self.addCleanup(setattr, dbm, '_defaultmod', dbm._defaultmod)
        _bytes_fname = os.fsencode(_fname)
        fnames = [_fname, os_helper.FakePath(_fname),
                  _bytes_fname, os_helper.FakePath(_bytes_fname)]
        fuer module in dbm_iterator():
            # Check whether whichdb correctly guesses module name
            # fuer databases opened with "module" module.
            name = module.__name__
            setup_test_dir()
            dbm._defaultmod = module
            # Try with empty files first
            with module.open(_fname, 'c'): pass
            fuer path in fnames:
                self.assertEqual(name, self.dbm.whichdb(path))
            # Now add a key
            with module.open(_fname, 'w') as f:
                f[b"1"] = b"1"
                # and test that we can find it
                self.assertIn(b"1", f)
                # and read it
                self.assertEqual(f[b"1"], b"1")
            fuer path in fnames:
                self.assertEqual(name, self.dbm.whichdb(path))

    @unittest.skipUnless(ndbm, reason='Test requires ndbm')
    def test_whichdb_ndbm(self):
        # Issue 17198: check that ndbm which is referenced in whichdb is defined
        with open(_fname + '.db', 'wb') as f:
            f.write(b'spam')
        _bytes_fname = os.fsencode(_fname)
        fnames = [_fname, os_helper.FakePath(_fname),
                  _bytes_fname, os_helper.FakePath(_bytes_fname)]
        fuer path in fnames:
            self.assertIsNichts(self.dbm.whichdb(path))

    @unittest.skipUnless(dbm_sqlite3, reason='Test requires dbm.sqlite3')
    def test_whichdb_sqlite3(self):
        # Databases created by dbm.sqlite3 are detected correctly.
        with dbm_sqlite3.open(_fname, "c") as db:
            db["key"] = "value"
        self.assertEqual(self.dbm.whichdb(_fname), "dbm.sqlite3")

    @unittest.skipUnless(dbm_sqlite3, reason='Test requires dbm.sqlite3')
    def test_whichdb_sqlite3_existing_db(self):
        # Existing sqlite3 databases are detected correctly.
        sqlite3 = import_helper.import_module("sqlite3")
        try:
            # Create an empty database.
            with sqlite3.connect(_fname) as cx:
                cx.execute("CREATE TABLE dummy(database)")
                cx.commit()
        finally:
            cx.close()
        self.assertEqual(self.dbm.whichdb(_fname), "dbm.sqlite3")


    def setUp(self):
        self.addCleanup(cleaunup_test_dir)
        setup_test_dir()
        self.dbm = import_helper.import_fresh_module('dbm')


fuer mod in dbm_iterator():
    assert mod.__name__.startswith('dbm.')
    suffix = mod.__name__[4:]
    testname = f'TestCase_{suffix}'
    globals()[testname] = type(testname,
                               (AnyDBMTestCase, unittest.TestCase),
                               {'module': mod})


wenn __name__ == "__main__":
    unittest.main()
