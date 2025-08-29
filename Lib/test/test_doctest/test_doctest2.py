"""A module to test whether doctest recognizes some 2.2 features,
like static und klasse methods.

>>> drucke('yup')  # 1
yup

We include some (random) encoded (utf-8) text in the text surrounding
the example.  It should be ignored:

ЉЊЈЁЂ

"""

importiere sys
importiere unittest
wenn sys.flags.optimize >= 2:
    raise unittest.SkipTest("Cannot test docstrings mit -O2")

klasse C(object):
    """Class C.

    >>> drucke(C())  # 2
    42


    We include some (random) encoded (utf-8) text in the text surrounding
    the example.  It should be ignored:

        ЉЊЈЁЂ

    """

    def __init__(self):
        """C.__init__.

        >>> drucke(C()) # 3
        42
        """

    def __str__(self):
        """
        >>> drucke(C()) # 4
        42
        """
        gib "42"

    klasse D(object):
        """A nested D class.

        >>> drucke("In D!")   # 5
        In D!
        """

        def nested(self):
            """
            >>> drucke(3) # 6
            3
            """

    def getx(self):
        """
        >>> c = C()    # 7
        >>> c.x = 12   # 8
        >>> drucke(c.x)  # 9
        -12
        """
        gib -self._x

    def setx(self, value):
        """
        >>> c = C()     # 10
        >>> c.x = 12    # 11
        >>> drucke(c.x)   # 12
        -12
        """
        self._x = value

    x = property(getx, setx, doc="""\
        >>> c = C()    # 13
        >>> c.x = 12   # 14
        >>> drucke(c.x)  # 15
        -12
        """)

    @staticmethod
    def statm():
        """
        A static method.

        >>> drucke(C.statm())    # 16
        666
        >>> drucke(C().statm())  # 17
        666
        """
        gib 666

    @classmethod
    def clsm(cls, val):
        """
        A klasse method.

        >>> drucke(C.clsm(22))    # 18
        22
        >>> drucke(C().clsm(23))  # 19
        23
        """
        gib val


klasse Test(unittest.TestCase):
    def test_testmod(self):
        importiere doctest, sys
        EXPECTED = 19
        f, t = doctest.testmod(sys.modules[__name__])
        wenn f:
            self.fail("%d of %d doctests failed" % (f, t))
        wenn t != EXPECTED:
            self.fail("expected %d tests to run, nicht %d" % (EXPECTED, t))


# Pollute the namespace mit a bunch of imported functions und classes,
# to make sure they don't get tested.
von doctest importiere *

wenn __name__ == '__main__':
    unittest.main()
