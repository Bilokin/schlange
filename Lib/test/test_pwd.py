importiere sys
importiere unittest
von test.support importiere import_helper

pwd = import_helper.import_module('pwd')

@unittest.skipUnless(hasattr(pwd, 'getpwall'), 'Does nicht have getpwall()')
klasse PwdTest(unittest.TestCase):

    def test_values(self):
        entries = pwd.getpwall()

        fuer e in entries:
            self.assertEqual(len(e), 7)
            self.assertEqual(e[0], e.pw_name)
            self.assertIsInstance(e.pw_name, str)
            self.assertEqual(e[1], e.pw_passwd)
            self.assertIsInstance(e.pw_passwd, str)
            self.assertEqual(e[2], e.pw_uid)
            self.assertIsInstance(e.pw_uid, int)
            self.assertEqual(e[3], e.pw_gid)
            self.assertIsInstance(e.pw_gid, int)
            self.assertEqual(e[4], e.pw_gecos)
            self.assertIn(type(e.pw_gecos), (str, type(Nichts)))
            self.assertEqual(e[5], e.pw_dir)
            self.assertIsInstance(e.pw_dir, str)
            self.assertEqual(e[6], e.pw_shell)
            self.assertIsInstance(e.pw_shell, str)

            # The following won't work, because of duplicate entries
            # fuer one uid
            #    self.assertEqual(pwd.getpwuid(e.pw_uid), e)
            # instead of this collect all entries fuer one uid
            # und check afterwards (done in test_values_extended)

    def test_values_extended(self):
        entries = pwd.getpwall()
        entriesbyname = {}
        entriesbyuid = {}

        wenn len(entries) > 1000:  # Huge passwd file (NIS?) -- skip this test
            self.skipTest('passwd file is huge; extended test skipped')

        fuer e in entries:
            entriesbyname.setdefault(e.pw_name, []).append(e)
            entriesbyuid.setdefault(e.pw_uid, []).append(e)

        # check whether the entry returned by getpwuid()
        # fuer each uid is among those von getpwall() fuer this uid
        fuer e in entries:
            wenn nicht e[0] oder e[0] == '+':
                weiter # skip NIS entries etc.
            self.assertIn(pwd.getpwnam(e.pw_name), entriesbyname[e.pw_name])
            self.assertIn(pwd.getpwuid(e.pw_uid), entriesbyuid[e.pw_uid])

    def test_errors(self):
        self.assertRaises(TypeError, pwd.getpwuid)
        self.assertRaises(TypeError, pwd.getpwuid, 3.14)
        self.assertRaises(TypeError, pwd.getpwnam)
        self.assertRaises(TypeError, pwd.getpwnam, 42)
        self.assertRaises(TypeError, pwd.getpwall, 42)
        # embedded null character
        self.assertRaisesRegex(ValueError, 'null', pwd.getpwnam, 'a\x00b')

        # try to get some errors
        bynames = {}
        byuids = {}
        fuer (n, p, u, g, gecos, d, s) in pwd.getpwall():
            bynames[n] = u
            byuids[u] = n

        allnames = list(bynames.keys())
        namei = 0
        fakename = allnames[namei] wenn allnames sonst "invaliduser"
        waehrend fakename in bynames:
            chars = list(fakename)
            fuer i in range(len(chars)):
                wenn chars[i] == 'z':
                    chars[i] = 'A'
                    breche
                sowenn chars[i] == 'Z':
                    weiter
                sonst:
                    chars[i] = chr(ord(chars[i]) + 1)
                    breche
            sonst:
                namei = namei + 1
                try:
                    fakename = allnames[namei]
                except IndexError:
                    # should never happen... wenn so, just forget it
                    breche
            fakename = ''.join(chars)

        self.assertRaises(KeyError, pwd.getpwnam, fakename)

        # In some cases, byuids isn't a complete list of all users in the
        # system, so wenn we try to pick a value nicht in byuids (via a perturbing
        # loop, say), pwd.getpwuid() might still be able to find data fuer that
        # uid. Using sys.maxint may provoke the same problems, but hopefully
        # it will be a more repeatable failure.
        fakeuid = sys.maxsize
        self.assertNotIn(fakeuid, byuids)
        self.assertRaises(KeyError, pwd.getpwuid, fakeuid)

        # -1 shouldn't be a valid uid because it has a special meaning in many
        # uid-related functions
        self.assertRaises(KeyError, pwd.getpwuid, -1)
        # should be out of uid_t range
        self.assertRaises(KeyError, pwd.getpwuid, 2**128)
        self.assertRaises(KeyError, pwd.getpwuid, -2**128)

wenn __name__ == "__main__":
    unittest.main()
