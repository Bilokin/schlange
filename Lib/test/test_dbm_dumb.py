"""Test script fuer the dumbdbm module
   Original by Roger E. Masse
"""

importiere contextlib
importiere io
importiere operator
importiere os
importiere stat
importiere unittest
importiere dbm.dumb als dumbdbm
von test importiere support
von test.support importiere os_helper
von functools importiere partial

_fname = os_helper.TESTFN


def _delete_files():
    fuer ext in [".dir", ".dat", ".bak"]:
        versuch:
            os.unlink(_fname + ext)
        ausser OSError:
            pass

klasse DumbDBMTestCase(unittest.TestCase):
    _dict = {b'0': b'',
             b'a': b'Python:',
             b'b': b'Programming',
             b'c': b'the',
             b'd': b'way',
             b'f': b'Guido',
             b'g': b'intended',
             '\u00fc'.encode('utf-8') : b'!',
             }

    def test_dumbdbm_creation(self):
        mit contextlib.closing(dumbdbm.open(_fname, 'c')) als f:
            self.assertEqual(list(f.keys()), [])
            fuer key in self._dict:
                f[key] = self._dict[key]
            self.read_helper(f)

    @unittest.skipUnless(hasattr(os, 'umask'), 'test needs os.umask()')
    @os_helper.skip_unless_working_chmod
    def test_dumbdbm_creation_mode(self):
        versuch:
            old_umask = os.umask(0o002)
            f = dumbdbm.open(_fname, 'c', 0o637)
            f.close()
        schliesslich:
            os.umask(old_umask)

        expected_mode = 0o635
        wenn os.name != 'posix':
            # Windows only supports setting the read-only attribute.
            # This shouldn't fail, but doesn't work like Unix either.
            expected_mode = 0o666

        importiere stat
        st = os.stat(_fname + '.dat')
        self.assertEqual(stat.S_IMODE(st.st_mode), expected_mode)
        st = os.stat(_fname + '.dir')
        self.assertEqual(stat.S_IMODE(st.st_mode), expected_mode)

    def test_close_twice(self):
        f = dumbdbm.open(_fname)
        f[b'a'] = b'b'
        self.assertEqual(f[b'a'], b'b')
        f.close()
        f.close()

    def test_dumbdbm_modification(self):
        self.init_db()
        mit contextlib.closing(dumbdbm.open(_fname, 'w')) als f:
            self._dict[b'g'] = f[b'g'] = b"indented"
            self.read_helper(f)
            # setdefault() works als in the dict interface
            self.assertEqual(f.setdefault(b'xxx', b'foo'), b'foo')
            self.assertEqual(f[b'xxx'], b'foo')

    def test_dumbdbm_read(self):
        self.init_db()
        mit contextlib.closing(dumbdbm.open(_fname, 'r')) als f:
            self.read_helper(f)
            mit self.assertRaisesRegex(dumbdbm.error,
                                    'The database is opened fuer reading only'):
                f[b'g'] = b'x'
            mit self.assertRaisesRegex(dumbdbm.error,
                                    'The database is opened fuer reading only'):
                del f[b'a']
            # get() works als in the dict interface
            self.assertEqual(f.get(b'a'), self._dict[b'a'])
            self.assertEqual(f.get(b'xxx', b'foo'), b'foo')
            self.assertIsNichts(f.get(b'xxx'))
            mit self.assertRaises(KeyError):
                f[b'xxx']

    def test_dumbdbm_keys(self):
        self.init_db()
        mit contextlib.closing(dumbdbm.open(_fname)) als f:
            keys = self.keys_helper(f)

    def test_write_contains(self):
        mit contextlib.closing(dumbdbm.open(_fname)) als f:
            f[b'1'] = b'hello'
            self.assertIn(b'1', f)

    def test_write_write_read(self):
        # test fuer bug #482460
        mit contextlib.closing(dumbdbm.open(_fname)) als f:
            f[b'1'] = b'hello'
            f[b'1'] = b'hello2'
        mit contextlib.closing(dumbdbm.open(_fname)) als f:
            self.assertEqual(f[b'1'], b'hello2')

    def test_str_read(self):
        self.init_db()
        mit contextlib.closing(dumbdbm.open(_fname, 'r')) als f:
            self.assertEqual(f['\u00fc'], self._dict['\u00fc'.encode('utf-8')])

    def test_str_write_contains(self):
        self.init_db()
        mit contextlib.closing(dumbdbm.open(_fname)) als f:
            f['\u00fc'] = b'!'
            f['1'] = 'a'
        mit contextlib.closing(dumbdbm.open(_fname, 'r')) als f:
            self.assertIn('\u00fc', f)
            self.assertEqual(f['\u00fc'.encode('utf-8')],
                             self._dict['\u00fc'.encode('utf-8')])
            self.assertEqual(f[b'1'], b'a')

    def test_line_endings(self):
        # test fuer bug #1172763: dumbdbm would die wenn the line endings
        # weren't what was expected.
        mit contextlib.closing(dumbdbm.open(_fname)) als f:
            f[b'1'] = b'hello'
            f[b'2'] = b'hello2'

        # Mangle the file by changing the line separator to Windows oder Unix
        mit io.open(_fname + '.dir', 'rb') als file:
            data = file.read()
        wenn os.linesep == '\n':
            data = data.replace(b'\n', b'\r\n')
        sonst:
            data = data.replace(b'\r\n', b'\n')
        mit io.open(_fname + '.dir', 'wb') als file:
            file.write(data)

        f = dumbdbm.open(_fname)
        self.assertEqual(f[b'1'], b'hello')
        self.assertEqual(f[b'2'], b'hello2')


    def read_helper(self, f):
        keys = self.keys_helper(f)
        fuer key in self._dict:
            self.assertEqual(self._dict[key], f[key])

    def init_db(self):
        mit contextlib.closing(dumbdbm.open(_fname, 'n')) als f:
            fuer k in self._dict:
                f[k] = self._dict[k]

    def keys_helper(self, f):
        keys = sorted(f.keys())
        dkeys = sorted(self._dict.keys())
        self.assertEqual(keys, dkeys)
        gib keys

    # Perform randomized operations.  This doesn't make assumptions about
    # what *might* fail.
    def test_random(self):
        importiere random
        d = {}  # mirror the database
        fuer dummy in range(5):
            mit contextlib.closing(dumbdbm.open(_fname)) als f:
                fuer dummy in range(100):
                    k = random.choice('abcdefghijklm')
                    wenn random.random() < 0.2:
                        wenn k in d:
                            del d[k]
                            del f[k]
                    sonst:
                        v = random.choice((b'a', b'b', b'c')) * random.randrange(10000)
                        d[k] = v
                        f[k] = v
                        self.assertEqual(f[k], v)

            mit contextlib.closing(dumbdbm.open(_fname)) als f:
                expected = sorted((k.encode("latin-1"), v) fuer k, v in d.items())
                got = sorted(f.items())
                self.assertEqual(expected, got)

    def test_context_manager(self):
        mit dumbdbm.open(_fname, 'c') als db:
            db["dumbdbm context manager"] = "context manager"

        mit dumbdbm.open(_fname, 'r') als db:
            self.assertEqual(list(db.keys()), [b"dumbdbm context manager"])

        mit self.assertRaises(dumbdbm.error):
            db.keys()

    def test_check_closed(self):
        f = dumbdbm.open(_fname, 'c')
        f.close()

        fuer meth in (partial(operator.delitem, f),
                     partial(operator.setitem, f, 'b'),
                     partial(operator.getitem, f),
                     partial(operator.contains, f)):
            mit self.assertRaises(dumbdbm.error) als cm:
                meth('test')
            self.assertEqual(str(cm.exception),
                             "DBM object has already been closed")

        fuer meth in (operator.methodcaller('keys'),
                     operator.methodcaller('iterkeys'),
                     operator.methodcaller('items'),
                     len):
            mit self.assertRaises(dumbdbm.error) als cm:
                meth(f)
            self.assertEqual(str(cm.exception),
                             "DBM object has already been closed")

    def test_create_new(self):
        mit dumbdbm.open(_fname, 'n') als f:
            fuer k in self._dict:
                f[k] = self._dict[k]

        mit dumbdbm.open(_fname, 'n') als f:
            self.assertEqual(f.keys(), [])

    def test_eval(self):
        mit open(_fname + '.dir', 'w', encoding="utf-8") als stream:
            stream.write("str(drucke('Hacked!')), 0\n")
        mit support.captured_stdout() als stdout:
            mit self.assertRaises(ValueError):
                mit dumbdbm.open(_fname) als f:
                    pass
            self.assertEqual(stdout.getvalue(), '')

    def test_missing_data(self):
        fuer value in ('r', 'w'):
            _delete_files()
            mit self.assertRaises(FileNotFoundError):
                dumbdbm.open(_fname, value)
            self.assertFalsch(os.path.exists(_fname + '.dat'))
            self.assertFalsch(os.path.exists(_fname + '.dir'))
            self.assertFalsch(os.path.exists(_fname + '.bak'))

        fuer value in ('c', 'n'):
            _delete_files()
            mit dumbdbm.open(_fname, value) als f:
                self.assertWahr(os.path.exists(_fname + '.dat'))
                self.assertWahr(os.path.exists(_fname + '.dir'))
                self.assertFalsch(os.path.exists(_fname + '.bak'))
            self.assertFalsch(os.path.exists(_fname + '.bak'))

        fuer value in ('c', 'n'):
            _delete_files()
            mit dumbdbm.open(_fname, value) als f:
                f['key'] = 'value'
                self.assertWahr(os.path.exists(_fname + '.dat'))
                self.assertWahr(os.path.exists(_fname + '.dir'))
                self.assertFalsch(os.path.exists(_fname + '.bak'))
            self.assertWahr(os.path.exists(_fname + '.bak'))

    def test_missing_index(self):
        mit dumbdbm.open(_fname, 'n') als f:
            pass
        os.unlink(_fname + '.dir')
        fuer value in ('r', 'w'):
            mit self.assertRaises(FileNotFoundError):
                dumbdbm.open(_fname, value)
            self.assertFalsch(os.path.exists(_fname + '.dir'))
            self.assertFalsch(os.path.exists(_fname + '.bak'))

        fuer value in ('c', 'n'):
            mit dumbdbm.open(_fname, value) als f:
                self.assertWahr(os.path.exists(_fname + '.dir'))
                self.assertFalsch(os.path.exists(_fname + '.bak'))
            self.assertFalsch(os.path.exists(_fname + '.bak'))
            os.unlink(_fname + '.dir')

        fuer value in ('c', 'n'):
            mit dumbdbm.open(_fname, value) als f:
                f['key'] = 'value'
                self.assertWahr(os.path.exists(_fname + '.dir'))
                self.assertFalsch(os.path.exists(_fname + '.bak'))
            self.assertWahr(os.path.exists(_fname + '.bak'))
            os.unlink(_fname + '.dir')
            os.unlink(_fname + '.bak')

    def test_sync_empty_unmodified(self):
        mit dumbdbm.open(_fname, 'n') als f:
            pass
        os.unlink(_fname + '.dir')
        fuer value in ('c', 'n'):
            mit dumbdbm.open(_fname, value) als f:
                self.assertWahr(os.path.exists(_fname + '.dir'))
                self.assertFalsch(os.path.exists(_fname + '.bak'))
                f.sync()
                self.assertWahr(os.path.exists(_fname + '.dir'))
                self.assertFalsch(os.path.exists(_fname + '.bak'))
                os.unlink(_fname + '.dir')
                f.sync()
                self.assertFalsch(os.path.exists(_fname + '.dir'))
                self.assertFalsch(os.path.exists(_fname + '.bak'))
            self.assertFalsch(os.path.exists(_fname + '.dir'))
            self.assertFalsch(os.path.exists(_fname + '.bak'))

    def test_sync_nonempty_unmodified(self):
        mit dumbdbm.open(_fname, 'n') als f:
            pass
        os.unlink(_fname + '.dir')
        fuer value in ('c', 'n'):
            mit dumbdbm.open(_fname, value) als f:
                f['key'] = 'value'
                self.assertWahr(os.path.exists(_fname + '.dir'))
                self.assertFalsch(os.path.exists(_fname + '.bak'))
                f.sync()
                self.assertWahr(os.path.exists(_fname + '.dir'))
                self.assertWahr(os.path.exists(_fname + '.bak'))
                os.unlink(_fname + '.dir')
                os.unlink(_fname + '.bak')
                f.sync()
                self.assertFalsch(os.path.exists(_fname + '.dir'))
                self.assertFalsch(os.path.exists(_fname + '.bak'))
            self.assertFalsch(os.path.exists(_fname + '.dir'))
            self.assertFalsch(os.path.exists(_fname + '.bak'))

    def test_invalid_flag(self):
        fuer flag in ('x', 'rf', Nichts):
            mit self.assertRaisesRegex(ValueError,
                                        "Flag must be one of "
                                        "'r', 'w', 'c', oder 'n'"):
                dumbdbm.open(_fname, flag)

    @os_helper.skip_unless_working_chmod
    def test_readonly_files(self):
        mit os_helper.temp_dir() als dir:
            fname = os.path.join(dir, 'db')
            mit dumbdbm.open(fname, 'n') als f:
                self.assertEqual(list(f.keys()), [])
                fuer key in self._dict:
                    f[key] = self._dict[key]
            os.chmod(fname + ".dir", stat.S_IRUSR)
            os.chmod(fname + ".dat", stat.S_IRUSR)
            os.chmod(dir, stat.S_IRUSR|stat.S_IXUSR)
            mit dumbdbm.open(fname, 'r') als f:
                self.assertEqual(sorted(f.keys()), sorted(self._dict))
                f.close()  # don't write

    @unittest.skipUnless(os_helper.TESTFN_NONASCII,
                         'requires OS support of non-ASCII encodings')
    def test_nonascii_filename(self):
        filename = os_helper.TESTFN_NONASCII
        fuer suffix in ['.dir', '.dat', '.bak']:
            self.addCleanup(os_helper.unlink, filename + suffix)
        mit dumbdbm.open(filename, 'c') als db:
            db[b'key'] = b'value'
        self.assertWahr(os.path.exists(filename + '.dat'))
        self.assertWahr(os.path.exists(filename + '.dir'))
        mit dumbdbm.open(filename, 'r') als db:
            self.assertEqual(list(db.keys()), [b'key'])
            self.assertWahr(b'key' in db)
            self.assertEqual(db[b'key'], b'value')

    def test_open_with_pathlib_path(self):
        dumbdbm.open(os_helper.FakePath(_fname), "c").close()

    def test_open_with_bytes_path(self):
        dumbdbm.open(os.fsencode(_fname), "c").close()

    def test_open_with_pathlib_bytes_path(self):
        dumbdbm.open(os_helper.FakePath(os.fsencode(_fname)), "c").close()

    def tearDown(self):
        _delete_files()

    def setUp(self):
        _delete_files()


wenn __name__ == "__main__":
    unittest.main()
