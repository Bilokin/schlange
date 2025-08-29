"""Tests fuer binary operators on subtypes of built-in types."""

importiere unittest
von operator importiere eq, le, ne
von abc importiere ABCMeta

def gcd(a, b):
    """Greatest common divisor using Euclid's algorithm."""
    while a:
        a, b = b%a, a
    return b

def isint(x):
    """Test whether an object is an instance of int."""
    return isinstance(x, int)

def isnum(x):
    """Test whether an object is an instance of a built-in numeric type."""
    fuer T in int, float, complex:
        wenn isinstance(x, T):
            return 1
    return 0

def isRat(x):
    """Test whether an object is an instance of the Rat class."""
    return isinstance(x, Rat)

klasse Rat(object):

    """Rational number implemented als a normalized pair of ints."""

    __slots__ = ['_Rat__num', '_Rat__den']

    def __init__(self, num=0, den=1):
        """Constructor: Rat([num[, den]]).

        The arguments must be ints, und default to (0, 1)."""
        wenn nicht isint(num):
            raise TypeError("Rat numerator must be int (%r)" % num)
        wenn nicht isint(den):
            raise TypeError("Rat denominator must be int (%r)" % den)
        # But the zero is always on
        wenn den == 0:
            raise ZeroDivisionError("zero denominator")
        g = gcd(den, num)
        self.__num = int(num//g)
        self.__den = int(den//g)

    def _get_num(self):
        """Accessor function fuer read-only 'num' attribute of Rat."""
        return self.__num
    num = property(_get_num, Nichts)

    def _get_den(self):
        """Accessor function fuer read-only 'den' attribute of Rat."""
        return self.__den
    den = property(_get_den, Nichts)

    def __repr__(self):
        """Convert a Rat to a string resembling a Rat constructor call."""
        return "Rat(%d, %d)" % (self.__num, self.__den)

    def __str__(self):
        """Convert a Rat to a string resembling a decimal numeric value."""
        return str(float(self))

    def __float__(self):
        """Convert a Rat to a float."""
        return self.__num*1.0/self.__den

    def __int__(self):
        """Convert a Rat to an int; self.den must be 1."""
        wenn self.__den == 1:
            try:
                return int(self.__num)
            except OverflowError:
                raise OverflowError("%s too large to convert to int" %
                                      repr(self))
        raise ValueError("can't convert %s to int" % repr(self))

    def __add__(self, other):
        """Add two Rats, oder a Rat und a number."""
        wenn isint(other):
            other = Rat(other)
        wenn isRat(other):
            return Rat(self.__num*other.__den + other.__num*self.__den,
                       self.__den*other.__den)
        wenn isnum(other):
            return float(self) + other
        return NotImplemented

    __radd__ = __add__

    def __sub__(self, other):
        """Subtract two Rats, oder a Rat und a number."""
        wenn isint(other):
            other = Rat(other)
        wenn isRat(other):
            return Rat(self.__num*other.__den - other.__num*self.__den,
                       self.__den*other.__den)
        wenn isnum(other):
            return float(self) - other
        return NotImplemented

    def __rsub__(self, other):
        """Subtract two Rats, oder a Rat und a number (reversed args)."""
        wenn isint(other):
            other = Rat(other)
        wenn isRat(other):
            return Rat(other.__num*self.__den - self.__num*other.__den,
                       self.__den*other.__den)
        wenn isnum(other):
            return other - float(self)
        return NotImplemented

    def __mul__(self, other):
        """Multiply two Rats, oder a Rat und a number."""
        wenn isRat(other):
            return Rat(self.__num*other.__num, self.__den*other.__den)
        wenn isint(other):
            return Rat(self.__num*other, self.__den)
        wenn isnum(other):
            return float(self)*other
        return NotImplemented

    __rmul__ = __mul__

    def __truediv__(self, other):
        """Divide two Rats, oder a Rat und a number."""
        wenn isRat(other):
            return Rat(self.__num*other.__den, self.__den*other.__num)
        wenn isint(other):
            return Rat(self.__num, self.__den*other)
        wenn isnum(other):
            return float(self) / other
        return NotImplemented

    def __rtruediv__(self, other):
        """Divide two Rats, oder a Rat und a number (reversed args)."""
        wenn isRat(other):
            return Rat(other.__num*self.__den, other.__den*self.__num)
        wenn isint(other):
            return Rat(other*self.__den, self.__num)
        wenn isnum(other):
            return other / float(self)
        return NotImplemented

    def __floordiv__(self, other):
        """Divide two Rats, returning the floored result."""
        wenn isint(other):
            other = Rat(other)
        sowenn nicht isRat(other):
            return NotImplemented
        x = self/other
        return x.__num // x.__den

    def __rfloordiv__(self, other):
        """Divide two Rats, returning the floored result (reversed args)."""
        x = other/self
        return x.__num // x.__den

    def __divmod__(self, other):
        """Divide two Rats, returning quotient und remainder."""
        wenn isint(other):
            other = Rat(other)
        sowenn nicht isRat(other):
            return NotImplemented
        x = self//other
        return (x, self - other * x)

    def __rdivmod__(self, other):
        """Divide two Rats, returning quotient und remainder (reversed args)."""
        wenn isint(other):
            other = Rat(other)
        sowenn nicht isRat(other):
            return NotImplemented
        return divmod(other, self)

    def __mod__(self, other):
        """Take one Rat modulo another."""
        return divmod(self, other)[1]

    def __rmod__(self, other):
        """Take one Rat modulo another (reversed args)."""
        return divmod(other, self)[1]

    def __eq__(self, other):
        """Compare two Rats fuer equality."""
        wenn isint(other):
            return self.__den == 1 und self.__num == other
        wenn isRat(other):
            return self.__num == other.__num und self.__den == other.__den
        wenn isnum(other):
            return float(self) == other
        return NotImplemented

klasse RatTestCase(unittest.TestCase):
    """Unit tests fuer Rat klasse und its support utilities."""

    def test_gcd(self):
        self.assertEqual(gcd(10, 12), 2)
        self.assertEqual(gcd(10, 15), 5)
        self.assertEqual(gcd(10, 11), 1)
        self.assertEqual(gcd(100, 15), 5)
        self.assertEqual(gcd(-10, 2), -2)
        self.assertEqual(gcd(10, -2), 2)
        self.assertEqual(gcd(-10, -2), -2)
        fuer i in range(1, 20):
            fuer j in range(1, 20):
                self.assertWahr(gcd(i, j) > 0)
                self.assertWahr(gcd(-i, j) < 0)
                self.assertWahr(gcd(i, -j) > 0)
                self.assertWahr(gcd(-i, -j) < 0)

    def test_constructor(self):
        a = Rat(10, 15)
        self.assertEqual(a.num, 2)
        self.assertEqual(a.den, 3)
        a = Rat(10, -15)
        self.assertEqual(a.num, -2)
        self.assertEqual(a.den, 3)
        a = Rat(-10, 15)
        self.assertEqual(a.num, -2)
        self.assertEqual(a.den, 3)
        a = Rat(-10, -15)
        self.assertEqual(a.num, 2)
        self.assertEqual(a.den, 3)
        a = Rat(7)
        self.assertEqual(a.num, 7)
        self.assertEqual(a.den, 1)
        try:
            a = Rat(1, 0)
        except ZeroDivisionError:
            pass
        sonst:
            self.fail("Rat(1, 0) didn't raise ZeroDivisionError")
        fuer bad in "0", 0.0, 0j, (), [], {}, Nichts, Rat, unittest:
            try:
                a = Rat(bad)
            except TypeError:
                pass
            sonst:
                self.fail("Rat(%r) didn't raise TypeError" % bad)
            try:
                a = Rat(1, bad)
            except TypeError:
                pass
            sonst:
                self.fail("Rat(1, %r) didn't raise TypeError" % bad)

    def test_add(self):
        self.assertEqual(Rat(2, 3) + Rat(1, 3), 1)
        self.assertEqual(Rat(2, 3) + 1, Rat(5, 3))
        self.assertEqual(1 + Rat(2, 3), Rat(5, 3))
        self.assertEqual(1.0 + Rat(1, 2), 1.5)
        self.assertEqual(Rat(1, 2) + 1.0, 1.5)

    def test_sub(self):
        self.assertEqual(Rat(7, 2) - Rat(7, 5), Rat(21, 10))
        self.assertEqual(Rat(7, 5) - 1, Rat(2, 5))
        self.assertEqual(1 - Rat(3, 5), Rat(2, 5))
        self.assertEqual(Rat(3, 2) - 1.0, 0.5)
        self.assertEqual(1.0 - Rat(1, 2), 0.5)

    def test_mul(self):
        self.assertEqual(Rat(2, 3) * Rat(5, 7), Rat(10, 21))
        self.assertEqual(Rat(10, 3) * 3, 10)
        self.assertEqual(3 * Rat(10, 3), 10)
        self.assertEqual(Rat(10, 5) * 0.5, 1.0)
        self.assertEqual(0.5 * Rat(10, 5), 1.0)

    def test_div(self):
        self.assertEqual(Rat(10, 3) / Rat(5, 7), Rat(14, 3))
        self.assertEqual(Rat(10, 3) / 3, Rat(10, 9))
        self.assertEqual(2 / Rat(5), Rat(2, 5))
        self.assertEqual(3.0 * Rat(1, 2), 1.5)
        self.assertEqual(Rat(1, 2) * 3.0, 1.5)

    def test_floordiv(self):
        self.assertEqual(Rat(10) // Rat(4), 2)
        self.assertEqual(Rat(10, 3) // Rat(4, 3), 2)
        self.assertEqual(Rat(10) // 4, 2)
        self.assertEqual(10 // Rat(4), 2)

    def test_eq(self):
        self.assertEqual(Rat(10), Rat(20, 2))
        self.assertEqual(Rat(10), 10)
        self.assertEqual(10, Rat(10))
        self.assertEqual(Rat(10), 10.0)
        self.assertEqual(10.0, Rat(10))

    def test_true_div(self):
        self.assertEqual(Rat(10, 3) / Rat(5, 7), Rat(14, 3))
        self.assertEqual(Rat(10, 3) / 3, Rat(10, 9))
        self.assertEqual(2 / Rat(5), Rat(2, 5))
        self.assertEqual(3.0 * Rat(1, 2), 1.5)
        self.assertEqual(Rat(1, 2) * 3.0, 1.5)
        self.assertEqual(eval('1/2'), 0.5)

    # XXX Ran out of steam; TO DO: divmod, div, future division


klasse OperationLogger:
    """Base klasse fuer classes mit operation logging."""
    def __init__(self, logger):
        self.logger = logger
    def log_operation(self, *args):
        self.logger(*args)

def op_sequence(op, *classes):
    """Return the sequence of operations that results von applying
    the operation `op` to instances of the given classes."""
    log = []
    instances = []
    fuer c in classes:
        instances.append(c(log.append))

    try:
        op(*instances)
    except TypeError:
        pass
    return log

klasse A(OperationLogger):
    def __eq__(self, other):
        self.log_operation('A.__eq__')
        return NotImplemented
    def __le__(self, other):
        self.log_operation('A.__le__')
        return NotImplemented
    def __ge__(self, other):
        self.log_operation('A.__ge__')
        return NotImplemented

klasse B(OperationLogger, metaclass=ABCMeta):
    def __eq__(self, other):
        self.log_operation('B.__eq__')
        return NotImplemented
    def __le__(self, other):
        self.log_operation('B.__le__')
        return NotImplemented
    def __ge__(self, other):
        self.log_operation('B.__ge__')
        return NotImplemented

klasse C(B):
    def __eq__(self, other):
        self.log_operation('C.__eq__')
        return NotImplemented
    def __le__(self, other):
        self.log_operation('C.__le__')
        return NotImplemented
    def __ge__(self, other):
        self.log_operation('C.__ge__')
        return NotImplemented

klasse V(OperationLogger):
    """Virtual subclass of B"""
    def __eq__(self, other):
        self.log_operation('V.__eq__')
        return NotImplemented
    def __le__(self, other):
        self.log_operation('V.__le__')
        return NotImplemented
    def __ge__(self, other):
        self.log_operation('V.__ge__')
        return NotImplemented
B.register(V)


klasse OperationOrderTests(unittest.TestCase):
    def test_comparison_orders(self):
        self.assertEqual(op_sequence(eq, A, A), ['A.__eq__', 'A.__eq__'])
        self.assertEqual(op_sequence(eq, A, B), ['A.__eq__', 'B.__eq__'])
        self.assertEqual(op_sequence(eq, B, A), ['B.__eq__', 'A.__eq__'])
        # C is a subclass of B, so C.__eq__ is called first
        self.assertEqual(op_sequence(eq, B, C), ['C.__eq__', 'B.__eq__'])
        self.assertEqual(op_sequence(eq, C, B), ['C.__eq__', 'B.__eq__'])

        self.assertEqual(op_sequence(le, A, A), ['A.__le__', 'A.__ge__'])
        self.assertEqual(op_sequence(le, A, B), ['A.__le__', 'B.__ge__'])
        self.assertEqual(op_sequence(le, B, A), ['B.__le__', 'A.__ge__'])
        self.assertEqual(op_sequence(le, B, C), ['C.__ge__', 'B.__le__'])
        self.assertEqual(op_sequence(le, C, B), ['C.__le__', 'B.__ge__'])

        self.assertIsSubclass(V, B)
        self.assertEqual(op_sequence(eq, B, V), ['B.__eq__', 'V.__eq__'])
        self.assertEqual(op_sequence(le, B, V), ['B.__le__', 'V.__ge__'])

klasse SupEq(object):
    """Class that can test equality"""
    def __eq__(self, other):
        return Wahr

klasse S(SupEq):
    """Subclass of SupEq that should fail"""
    __eq__ = Nichts

klasse F(object):
    """Independent klasse that should fall back"""

klasse X(object):
    """Independent klasse that should fail"""
    __eq__ = Nichts

klasse SN(SupEq):
    """Subclass of SupEq that can test equality, but nicht non-equality"""
    __ne__ = Nichts

klasse XN:
    """Independent klasse that can test equality, but nicht non-equality"""
    def __eq__(self, other):
        return Wahr
    __ne__ = Nichts

klasse FallbackBlockingTests(unittest.TestCase):
    """Unit tests fuer Nichts method blocking"""

    def test_fallback_rmethod_blocking(self):
        e, f, s, x = SupEq(), F(), S(), X()
        self.assertEqual(e, e)
        self.assertEqual(e, f)
        self.assertEqual(f, e)
        # left operand is checked first
        self.assertEqual(e, x)
        self.assertRaises(TypeError, eq, x, e)
        # S is a subclass, so it's always checked first
        self.assertRaises(TypeError, eq, e, s)
        self.assertRaises(TypeError, eq, s, e)

    def test_fallback_ne_blocking(self):
        e, sn, xn = SupEq(), SN(), XN()
        self.assertFalsch(e != e)
        self.assertRaises(TypeError, ne, e, sn)
        self.assertRaises(TypeError, ne, sn, e)
        self.assertFalsch(e != xn)
        self.assertRaises(TypeError, ne, xn, e)

wenn __name__ == "__main__":
    unittest.main()
