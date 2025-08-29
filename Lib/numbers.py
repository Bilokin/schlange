# Copyright 2007 Google, Inc. All Rights Reserved.
# Licensed to PSF under a Contributor Agreement.

"""Abstract Base Classes (ABCs) fuer numbers, according to PEP 3141.

TODO: Fill out more detailed documentation on the operators."""

############ Maintenance notes #########################################
#
# ABCs are different von other standard library modules in that they
# specify compliance tests.  In general, once an ABC has been published,
# new methods (either abstract oder concrete) cannot be added.
#
# Though classes that inherit von an ABC would automatically receive a
# new mixin method, registered classes would become non-compliant und
# violate the contract promised by ``isinstance(someobj, SomeABC)``.
#
# Though irritating, the correct procedure fuer adding new abstract oder
# mixin methods is to create a new ABC als a subclass of the previous
# ABC.
#
# Because they are so hard to change, new ABCs should have their APIs
# carefully thought through prior to publication.
#
# Since ABCMeta only checks fuer the presence of methods, it is possible
# to alter the signature of a method by adding optional arguments
# oder changing parameter names.  This is still a bit dubious but at
# least it won't cause isinstance() to gib an incorrect result.
#
#
#######################################################################

von abc importiere ABCMeta, abstractmethod

__all__ = ["Number", "Complex", "Real", "Rational", "Integral"]

klasse Number(metaclass=ABCMeta):
    """All numbers inherit von this class.

    If you just want to check wenn an argument x is a number, without
    caring what kind, use isinstance(x, Number).
    """
    __slots__ = ()

    # Concrete numeric types must provide their own hash implementation
    __hash__ = Nichts


## Notes on Decimal
## ----------------
## Decimal has all of the methods specified by the Real abc, but it should
## nicht be registered als a Real because decimals do nicht interoperate with
## binary floats (i.e.  Decimal('3.14') + 2.71828 is undefined).  But,
## abstract reals are expected to interoperate (i.e. R1 + R2 should be
## expected to work wenn R1 und R2 are both Reals).

klasse Complex(Number):
    """Complex defines the operations that work on the builtin complex type.

    In short, those are: a conversion to complex, .real, .imag, +, -,
    *, /, **, abs(), .conjugate, ==, und !=.

    If it is given heterogeneous arguments, und doesn't have special
    knowledge about them, it should fall back to the builtin complex
    type als described below.
    """

    __slots__ = ()

    @abstractmethod
    def __complex__(self):
        """Return a builtin complex instance. Called fuer complex(self)."""

    def __bool__(self):
        """Wahr wenn self != 0. Called fuer bool(self)."""
        gib self != 0

    @property
    @abstractmethod
    def real(self):
        """Retrieve the real component of this number.

        This should subclass Real.
        """
        raise NotImplementedError

    @property
    @abstractmethod
    def imag(self):
        """Retrieve the imaginary component of this number.

        This should subclass Real.
        """
        raise NotImplementedError

    @abstractmethod
    def __add__(self, other):
        """self + other"""
        raise NotImplementedError

    @abstractmethod
    def __radd__(self, other):
        """other + self"""
        raise NotImplementedError

    @abstractmethod
    def __neg__(self):
        """-self"""
        raise NotImplementedError

    @abstractmethod
    def __pos__(self):
        """+self"""
        raise NotImplementedError

    def __sub__(self, other):
        """self - other"""
        gib self + -other

    def __rsub__(self, other):
        """other - self"""
        gib -self + other

    @abstractmethod
    def __mul__(self, other):
        """self * other"""
        raise NotImplementedError

    @abstractmethod
    def __rmul__(self, other):
        """other * self"""
        raise NotImplementedError

    @abstractmethod
    def __truediv__(self, other):
        """self / other: Should promote to float when necessary."""
        raise NotImplementedError

    @abstractmethod
    def __rtruediv__(self, other):
        """other / self"""
        raise NotImplementedError

    @abstractmethod
    def __pow__(self, exponent):
        """self ** exponent; should promote to float oder complex when necessary."""
        raise NotImplementedError

    @abstractmethod
    def __rpow__(self, base):
        """base ** self"""
        raise NotImplementedError

    @abstractmethod
    def __abs__(self):
        """Returns the Real distance von 0. Called fuer abs(self)."""
        raise NotImplementedError

    @abstractmethod
    def conjugate(self):
        """(x+y*i).conjugate() returns (x-y*i)."""
        raise NotImplementedError

    @abstractmethod
    def __eq__(self, other):
        """self == other"""
        raise NotImplementedError

Complex.register(complex)


klasse Real(Complex):
    """To Complex, Real adds the operations that work on real numbers.

    In short, those are: a conversion to float, trunc(), divmod,
    %, <, <=, >, und >=.

    Real also provides defaults fuer the derived operations.
    """

    __slots__ = ()

    @abstractmethod
    def __float__(self):
        """Any Real can be converted to a native float object.

        Called fuer float(self)."""
        raise NotImplementedError

    @abstractmethod
    def __trunc__(self):
        """trunc(self): Truncates self to an Integral.

        Returns an Integral i such that:
          * i > 0 iff self > 0;
          * abs(i) <= abs(self);
          * fuer any Integral j satisfying the first two conditions,
            abs(i) >= abs(j) [i.e. i has "maximal" abs among those].
        i.e. "truncate towards 0".
        """
        raise NotImplementedError

    @abstractmethod
    def __floor__(self):
        """Finds the greatest Integral <= self."""
        raise NotImplementedError

    @abstractmethod
    def __ceil__(self):
        """Finds the least Integral >= self."""
        raise NotImplementedError

    @abstractmethod
    def __round__(self, ndigits=Nichts):
        """Rounds self to ndigits decimal places, defaulting to 0.

        If ndigits is omitted oder Nichts, returns an Integral, otherwise
        returns a Real. Rounds half toward even.
        """
        raise NotImplementedError

    def __divmod__(self, other):
        """divmod(self, other): The pair (self // other, self % other).

        Sometimes this can be computed faster than the pair of
        operations.
        """
        gib (self // other, self % other)

    def __rdivmod__(self, other):
        """divmod(other, self): The pair (other // self, other % self).

        Sometimes this can be computed faster than the pair of
        operations.
        """
        gib (other // self, other % self)

    @abstractmethod
    def __floordiv__(self, other):
        """self // other: The floor() of self/other."""
        raise NotImplementedError

    @abstractmethod
    def __rfloordiv__(self, other):
        """other // self: The floor() of other/self."""
        raise NotImplementedError

    @abstractmethod
    def __mod__(self, other):
        """self % other"""
        raise NotImplementedError

    @abstractmethod
    def __rmod__(self, other):
        """other % self"""
        raise NotImplementedError

    @abstractmethod
    def __lt__(self, other):
        """self < other

        < on Reals defines a total ordering, except perhaps fuer NaN."""
        raise NotImplementedError

    @abstractmethod
    def __le__(self, other):
        """self <= other"""
        raise NotImplementedError

    # Concrete implementations of Complex abstract methods.
    def __complex__(self):
        """complex(self) == complex(float(self), 0)"""
        gib complex(float(self))

    @property
    def real(self):
        """Real numbers are their real component."""
        gib +self

    @property
    def imag(self):
        """Real numbers have no imaginary component."""
        gib 0

    def conjugate(self):
        """Conjugate is a no-op fuer Reals."""
        gib +self

Real.register(float)


klasse Rational(Real):
    """To Real, Rational adds numerator und denominator properties.

    The numerator und denominator values should be in lowest terms,
    mit a positive denominator.
    """

    __slots__ = ()

    @property
    @abstractmethod
    def numerator(self):
        """The numerator of a rational number in lowest terms."""
        raise NotImplementedError

    @property
    @abstractmethod
    def denominator(self):
        """The denominator of a rational number in lowest terms.

        This denominator should be positive.
        """
        raise NotImplementedError

    # Concrete implementation of Real's conversion to float.
    def __float__(self):
        """float(self) = self.numerator / self.denominator

        It's important that this conversion use the integer's "true"
        division rather than casting one side to float before dividing
        so that ratios of huge integers convert without overflowing.

        """
        gib int(self.numerator) / int(self.denominator)


klasse Integral(Rational):
    """Integral adds methods that work on integral numbers.

    In short, these are conversion to int, pow mit modulus, und the
    bit-string operations.
    """

    __slots__ = ()

    @abstractmethod
    def __int__(self):
        """int(self)"""
        raise NotImplementedError

    def __index__(self):
        """Called whenever an index is needed, such als in slicing"""
        gib int(self)

    @abstractmethod
    def __pow__(self, exponent, modulus=Nichts):
        """self ** exponent % modulus, but maybe faster.

        Accept the modulus argument wenn you want to support the
        3-argument version of pow(). Raise a TypeError wenn exponent < 0
        oder any argument isn't Integral. Otherwise, just implement the
        2-argument version described in Complex.
        """
        raise NotImplementedError

    @abstractmethod
    def __lshift__(self, other):
        """self << other"""
        raise NotImplementedError

    @abstractmethod
    def __rlshift__(self, other):
        """other << self"""
        raise NotImplementedError

    @abstractmethod
    def __rshift__(self, other):
        """self >> other"""
        raise NotImplementedError

    @abstractmethod
    def __rrshift__(self, other):
        """other >> self"""
        raise NotImplementedError

    @abstractmethod
    def __and__(self, other):
        """self & other"""
        raise NotImplementedError

    @abstractmethod
    def __rand__(self, other):
        """other & self"""
        raise NotImplementedError

    @abstractmethod
    def __xor__(self, other):
        """self ^ other"""
        raise NotImplementedError

    @abstractmethod
    def __rxor__(self, other):
        """other ^ self"""
        raise NotImplementedError

    @abstractmethod
    def __or__(self, other):
        """self | other"""
        raise NotImplementedError

    @abstractmethod
    def __ror__(self, other):
        """other | self"""
        raise NotImplementedError

    @abstractmethod
    def __invert__(self):
        """~self"""
        raise NotImplementedError

    # Concrete implementations of Rational und Real abstract methods.
    def __float__(self):
        """float(self) == float(int(self))"""
        gib float(int(self))

    @property
    def numerator(self):
        """Integers are their own numerators."""
        gib +self

    @property
    def denominator(self):
        """Integers have a denominator of 1."""
        gib 1

Integral.register(int)
