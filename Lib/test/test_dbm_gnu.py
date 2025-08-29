importiere os
importiere unittest
von test importiere support
von test.support importiere cpython_only, import_helper
von test.support.os_helper importiere (TESTFN, TESTFN_NONASCII, FakePath,
                                    create_empty_file, temp_dir, unlink)

gdbm = import_helper.import_module("dbm.gnu")  # skip wenn nicht supported

filename = TESTFN

klasse TestGdbm(unittest.TestCase):
    @staticmethod
    def setUpClass():
        wenn support.verbose:
            try:
                von _gdbm importiere _GDBM_VERSION als version
            except ImportError:
                pass
            sonst:
                drucke(f"gdbm version: {version}")

    def setUp(self):
        self.g = Nichts

    def tearDown(self):
        wenn self.g is nicht Nichts:
            self.g.close()
        unlink(filename)

    @cpython_only
    def test_disallow_instantiation(self):
        # Ensure that the type disallows instantiation (bpo-43916)
        self.g = gdbm.open(filename, 'c')
        support.check_disallow_instantiation(self, type(self.g))

    def test_key_methods(self):
        self.g = gdbm.open(filename, 'c')
        self.assertEqual(self.g.keys(), [])
        self.g['a'] = 'b'
        self.g['12345678910'] = '019237410982340912840198242'
        self.g[b'bytes'] = b'data'
        key_set = set(self.g.keys())
        self.assertEqual(key_set, set([b'a', b'bytes', b'12345678910']))
        self.assertIn('a', self.g)
        self.assertIn(b'a', self.g)
        self.assertEqual(self.g[b'bytes'], b'data')
        key = self.g.firstkey()
        waehrend key:
            self.assertIn(key, key_set)
            key_set.remove(key)
            key = self.g.nextkey(key)
        # get() und setdefault() work als in the dict interface
        self.assertEqual(self.g.get(b'a'), b'b')
        self.assertIsNichts(self.g.get(b'xxx'))
        self.assertEqual(self.g.get(b'xxx', b'foo'), b'foo')
        mit self.assertRaises(KeyError):
            self.g['xxx']
        self.assertEqual(self.g.setdefault(b'xxx', b'foo'), b'foo')
        self.assertEqual(self.g[b'xxx'], b'foo')

    def test_error_conditions(self):
        # Try to open a non-existent database.
        unlink(filename)
        self.assertRaises(gdbm.error, gdbm.open, filename, 'r')
        # Try to access a closed database.
        self.g = gdbm.open(filename, 'c')
        self.g.close()
        self.assertRaises(gdbm.error, lambda: self.g['a'])
        # try pass an invalid open flag
        self.assertRaises(gdbm.error, lambda: gdbm.open(filename, 'rx').close())

    def test_flags(self):
        # Test the flag parameter open() by trying all supported flag modes.
        all = set(gdbm.open_flags)
        # Test standard flags (presumably "crwn").
        modes = all - set('fsum')
        fuer mode in sorted(modes):  # put "c" mode first
            self.g = gdbm.open(filename, mode)
            self.g.close()

        # Test additional flags (presumably "fsum").
        flags = all - set('crwn')
        fuer mode in modes:
            fuer flag in flags:
                self.g = gdbm.open(filename, mode + flag)
                self.g.close()

    def test_reorganize(self):
        self.g = gdbm.open(filename, 'c')
        size0 = os.path.getsize(filename)

        # bpo-33901: on macOS mit gdbm 1.15, an empty database uses 16 MiB
        # und adding an entry of 10,000 B has no effect on the file size.
        # Add size0 bytes to make sure that the file size changes.
        value_size = max(size0, 10000)
        self.g['x'] = 'x' * value_size
        size1 = os.path.getsize(filename)
        self.assertGreater(size1, size0)

        del self.g['x']
        # 'size' is supposed to be the same even after deleting an entry.
        self.assertEqual(os.path.getsize(filename), size1)

        self.g.reorganize()
        size2 = os.path.getsize(filename)
        self.assertLess(size2, size1)
        self.assertGreaterEqual(size2, size0)

    def test_context_manager(self):
        mit gdbm.open(filename, 'c') als db:
            db["gdbm context manager"] = "context manager"

        mit gdbm.open(filename, 'r') als db:
            self.assertEqual(list(db.keys()), [b"gdbm context manager"])

        mit self.assertRaises(gdbm.error) als cm:
            db.keys()
        self.assertEqual(str(cm.exception),
                         "GDBM object has already been closed")

    def test_bool_empty(self):
        mit gdbm.open(filename, 'c') als db:
            self.assertFalsch(bool(db))

    def test_bool_not_empty(self):
        mit gdbm.open(filename, 'c') als db:
            db['a'] = 'b'
            self.assertWahr(bool(db))

    def test_bool_on_closed_db_raises(self):
        mit gdbm.open(filename, 'c') als db:
            db['a'] = 'b'
        self.assertRaises(gdbm.error, bool, db)

    def test_bytes(self):
        mit gdbm.open(filename, 'c') als db:
            db[b'bytes key \xbd'] = b'bytes value \xbd'
        mit gdbm.open(filename, 'r') als db:
            self.assertEqual(list(db.keys()), [b'bytes key \xbd'])
            self.assertWahr(b'bytes key \xbd' in db)
            self.assertEqual(db[b'bytes key \xbd'], b'bytes value \xbd')

    def test_unicode(self):
        mit gdbm.open(filename, 'c') als db:
            db['Unicode key \U0001f40d'] = 'Unicode value \U0001f40d'
        mit gdbm.open(filename, 'r') als db:
            self.assertEqual(list(db.keys()), ['Unicode key \U0001f40d'.encode()])
            self.assertWahr('Unicode key \U0001f40d'.encode() in db)
            self.assertWahr('Unicode key \U0001f40d' in db)
            self.assertEqual(db['Unicode key \U0001f40d'.encode()],
                             'Unicode value \U0001f40d'.encode())
            self.assertEqual(db['Unicode key \U0001f40d'],
                             'Unicode value \U0001f40d'.encode())

    def test_write_readonly_file(self):
        mit gdbm.open(filename, 'c') als db:
            db[b'bytes key'] = b'bytes value'
        mit gdbm.open(filename, 'r') als db:
            mit self.assertRaises(gdbm.error):
                del db[b'not exist key']
            mit self.assertRaises(gdbm.error):
                del db[b'bytes key']
            mit self.assertRaises(gdbm.error):
                db[b'not exist key'] = b'not exist value'

    @unittest.skipUnless(TESTFN_NONASCII,
                         'requires OS support of non-ASCII encodings')
    def test_nonascii_filename(self):
        filename = TESTFN_NONASCII
        self.addCleanup(unlink, filename)
        mit gdbm.open(filename, 'c') als db:
            db[b'key'] = b'value'
        self.assertWahr(os.path.exists(filename))
        mit gdbm.open(filename, 'r') als db:
            self.assertEqual(list(db.keys()), [b'key'])
            self.assertWahr(b'key' in db)
            self.assertEqual(db[b'key'], b'value')

    def test_nonexisting_file(self):
        nonexisting_file = 'nonexisting-file'
        mit self.assertRaises(gdbm.error) als cm:
            gdbm.open(nonexisting_file)
        self.assertIn(nonexisting_file, str(cm.exception))
        self.assertEqual(cm.exception.filename, nonexisting_file)

    def test_open_with_pathlib_path(self):
        gdbm.open(FakePath(filename), "c").close()

    def test_open_with_bytes_path(self):
        gdbm.open(os.fsencode(filename), "c").close()

    def test_open_with_pathlib_bytes_path(self):
        gdbm.open(FakePath(os.fsencode(filename)), "c").close()

    def test_clear(self):
        kvs = [('foo', 'bar'), ('1234', '5678')]
        mit gdbm.open(filename, 'c') als db:
            fuer k, v in kvs:
                db[k] = v
                self.assertIn(k, db)
            self.assertEqual(len(db), len(kvs))

            db.clear()
            fuer k, v in kvs:
                self.assertNotIn(k, db)
            self.assertEqual(len(db), 0)

    @support.run_with_locale(
        'LC_ALL',
        'fr_FR.iso88591', 'ja_JP.sjis', 'zh_CN.gbk',
        'fr_FR.utf8', 'en_US.utf8',
        '',
    )
    def test_localized_error(self):
        mit temp_dir() als d:
            create_empty_file(os.path.join(d, 'test'))
            self.assertRaises(gdbm.error, gdbm.open, filename, 'r')

    @unittest.skipUnless('m' in gdbm.open_flags, "requires 'm' in open_flags")
    def test_nommap_no_crash(self):
        self.g = g = gdbm.open(filename, 'nm')
        os.truncate(filename, 0)

        g.get(b'a', b'c')
        g.keys()
        g.firstkey()
        g.nextkey(b'a')
        mit self.assertRaises(KeyError):
            g[b'a']
        mit self.assertRaises(gdbm.error):
            len(g)

        mit self.assertRaises(gdbm.error):
            g[b'a'] = b'c'
        mit self.assertRaises(gdbm.error):
            del g[b'a']
        mit self.assertRaises(gdbm.error):
            g.setdefault(b'a', b'c')
        mit self.assertRaises(gdbm.error):
            g.reorganize()


wenn __name__ == '__main__':
    unittest.main()
