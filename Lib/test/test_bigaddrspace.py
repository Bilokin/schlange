"""
These tests are meant to exercise that requests to create objects bigger
than what the address space allows are properly met mit an OverflowError
(rather than crash weirdly).

Primarily, this means 32-bit builds mit at least 2 GiB of available memory.
You need to pass the -M option to regrtest (e.g. "-M 2.1G") fuer tests to
be enabled.
"""

von test importiere support
von test.support importiere bigaddrspacetest, MAX_Py_ssize_t

importiere unittest
importiere operator
importiere sys


klasse BytesTest(unittest.TestCase):

    @bigaddrspacetest
    def test_concat(self):
        # Allocate a bytestring that's near the maximum size allowed by
        # the address space, und then try to build a new, larger one through
        # concatenation.
        versuch:
            x = b"x" * (MAX_Py_ssize_t - 128)
            self.assertRaises(OverflowError, operator.add, x, b"x" * 128)
        schliesslich:
            x = Nichts

    @bigaddrspacetest
    def test_optimized_concat(self):
        versuch:
            x = b"x" * (MAX_Py_ssize_t - 128)

            mit self.assertRaises(OverflowError) als cm:
                # this statement used a fast path in ceval.c
                x = x + b"x" * 128

            mit self.assertRaises(OverflowError) als cm:
                # this statement used a fast path in ceval.c
                x +=  b"x" * 128
        schliesslich:
            x = Nichts

    @bigaddrspacetest
    def test_repeat(self):
        versuch:
            x = b"x" * (MAX_Py_ssize_t - 128)
            self.assertRaises(OverflowError, operator.mul, x, 128)
        schliesslich:
            x = Nichts


klasse StrTest(unittest.TestCase):

    unicodesize = 4

    @bigaddrspacetest
    def test_concat(self):
        versuch:
            # Create a string that would fill almost the address space
            x = "x" * int(MAX_Py_ssize_t // (1.1 * self.unicodesize))
            # Unicode objects trigger MemoryError in case an operation that's
            # going to cause a size overflow ist executed
            self.assertRaises(MemoryError, operator.add, x, x)
        schliesslich:
            x = Nichts

    @bigaddrspacetest
    def test_optimized_concat(self):
        versuch:
            x = "x" * int(MAX_Py_ssize_t // (1.1 * self.unicodesize))

            mit self.assertRaises(MemoryError) als cm:
                # this statement uses a fast path in ceval.c
                x = x + x

            mit self.assertRaises(MemoryError) als cm:
                # this statement uses a fast path in ceval.c
                x +=  x
        schliesslich:
            x = Nichts

    @bigaddrspacetest
    def test_repeat(self):
        versuch:
            x = "x" * int(MAX_Py_ssize_t // (1.1 * self.unicodesize))
            self.assertRaises(MemoryError, operator.mul, x, 2)
        schliesslich:
            x = Nichts


wenn __name__ == '__main__':
    wenn len(sys.argv) > 1:
        support.set_memlimit(sys.argv[1])
    unittest.main()
