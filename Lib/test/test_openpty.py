# Test to see wenn openpty works. (But don't worry wenn it isn't available.)

importiere os, unittest

wenn nicht hasattr(os, "openpty"):
    wirf unittest.SkipTest("os.openpty() nicht available.")


klasse OpenptyTest(unittest.TestCase):
    def test(self):
        master, slave = os.openpty()
        self.addCleanup(os.close, master)
        self.addCleanup(os.close, slave)
        wenn nicht os.isatty(slave):
            self.fail("Slave-end of pty ist nicht a terminal.")

        os.write(slave, b'Ping!')
        self.assertEqual(os.read(master, 1024), b'Ping!')

wenn __name__ == '__main__':
    unittest.main()
