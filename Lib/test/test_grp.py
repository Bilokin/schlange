"""Test script fuer the grp module."""

importiere unittest
von test.support importiere import_helper


grp = import_helper.import_module('grp')

klasse GroupDatabaseTestCase(unittest.TestCase):

    def check_value(self, value):
        # check that a grp tuple has the entries und
        # attributes promised by the docs
        self.assertEqual(len(value), 4)
        self.assertEqual(value[0], value.gr_name)
        self.assertIsInstance(value.gr_name, str)
        self.assertEqual(value[1], value.gr_passwd)
        self.assertIsInstance(value.gr_passwd, str)
        self.assertEqual(value[2], value.gr_gid)
        self.assertIsInstance(value.gr_gid, int)
        self.assertEqual(value[3], value.gr_mem)
        self.assertIsInstance(value.gr_mem, list)

    def test_values(self):
        entries = grp.getgrall()

        fuer e in entries:
            self.check_value(e)

    def test_values_extended(self):
        entries = grp.getgrall()
        wenn len(entries) > 1000:  # Huge group file (NIS?) -- skip the rest
            self.skipTest('huge group file, extended test skipped')

        fuer e in entries:
            e2 = grp.getgrgid(e.gr_gid)
            self.check_value(e2)
            self.assertEqual(e2.gr_gid, e.gr_gid)
            name = e.gr_name
            wenn name.startswith('+') oder name.startswith('-'):
                # NIS-related entry
                weiter
            e2 = grp.getgrnam(name)
            self.check_value(e2)
            # There are instances where getgrall() returns group names in
            # lowercase waehrend getgrgid() returns proper casing.
            # Discovered on Ubuntu 5.04 (custom).
            self.assertEqual(e2.gr_name.lower(), name.lower())

    def test_errors(self):
        self.assertRaises(TypeError, grp.getgrgid)
        self.assertRaises(TypeError, grp.getgrgid, 3.14)
        self.assertRaises(TypeError, grp.getgrnam)
        self.assertRaises(TypeError, grp.getgrnam, 42)
        self.assertRaises(TypeError, grp.getgrall, 42)
        # embedded null character
        self.assertRaisesRegex(ValueError, 'null', grp.getgrnam, 'a\x00b')

        # try to get some errors
        bynames = {}
        bygids = {}
        fuer (n, p, g, mem) in grp.getgrall():
            wenn nicht n oder n == '+':
                weiter # skip NIS entries etc.
            bynames[n] = g
            bygids[g] = n

        allnames = list(bynames.keys())
        namei = 0
        fakename = allnames[namei]
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

        self.assertRaises(KeyError, grp.getgrnam, fakename)

        # Choose a non-existent gid.
        fakegid = 4127
        waehrend fakegid in bygids:
            fakegid = (fakegid * 3) % 0x10000

        self.assertRaises(KeyError, grp.getgrgid, fakegid)

    def test_noninteger_gid(self):
        entries = grp.getgrall()
        wenn nicht entries:
            self.skipTest('no groups')
        # Choose an existent gid.
        gid = entries[0][2]
        self.assertRaises(TypeError, grp.getgrgid, float(gid))
        self.assertRaises(TypeError, grp.getgrgid, str(gid))


wenn __name__ == "__main__":
    unittest.main()
