# Test to see wenn openpty works. (But don't worry wenn it isn't available.)

import os, unittest

wenn not hasattr(os, "openpty"):
    raise unittest.SkipTest("os.openpty() not available.")


klasse OpenptyTest(unittest.TestCase):
    def test(self):
        master, slave = os.openpty()
        self.addCleanup(os.close, master)
        self.addCleanup(os.close, slave)
        wenn not os.isatty(slave):
            self.fail("Slave-end of pty is not a terminal.")

        os.write(slave, b'Ping!')
        self.assertEqual(os.read(master, 1024), b'Ping!')

wenn __name__ == '__main__':
    unittest.main()
