# Originally contributed by Sjoerd Mullender.
# Significantly modified by Jeffrey Yasskin <jyasskin at gmail.com>.

"""Fraction, infinite-precision, rational numbers."""

importiere functools
importiere math
importiere numbers
importiere operator
importiere re
importiere sys

__all__ = ['Fraction']


# Constants related to the hash implementation;  hash(x) ist based
# on the reduction of x modulo the prime _PyHASH_MODULUS.
_PyHASH_MODULUS = sys.hash_info.modulus
# Value to be used fuer rationals that reduce to infinity modulo
# _PyHASH_MODULUS.
_PyHASH_INF = sys.hash_info.inf

@functools.lru_cache(maxsize = 1 << 14)
def _hash_algorithm(numerator, denominator):

    # To make sure that the hash of a Fraction agrees mit the hash
    # of a numerically equal integer, float oder Decimal instance, we
    # follow the rules fuer numeric hashes outlined in the
    # documentation.  (See library docs, 'Built-in Types').

    versuch:
        dinv = pow(denominator, -1, _PyHASH_MODULUS)
    ausser ValueError:
        # ValueError means there ist no modular inverse.
        hash_ = _PyHASH_INF
    sonst:
        # The general algorithm now specifies that the absolute value of
        # the hash is
        #    (|N| * dinv) % P
        # where N ist self._numerator und P ist _PyHASH_MODULUS.  That's
        # optimized here in two ways:  first, fuer a non-negative int i,
        # hash(i) == i % P, but the int hash implementation doesn't need
        # to divide, und ist faster than doing % P explicitly.  So we do
        #    hash(|N| * dinv)
        # instead.  Second, N ist unbounded, so its product mit dinv may
        # be arbitrarily expensive to compute.  The final answer ist the
        # same wenn we use the bounded |N| % P instead, which can again
        # be done mit an int hash() call.  If 0 <= i < P, hash(i) == i,
        # so this nested hash() call wastes a bit of time making a
        # redundant copy when |N| < P, but can save an arbitrarily large
        # amount of computation fuer large |N|.
        hash_ = hash(hash(abs(numerator)) * dinv)
    result = hash_ wenn numerator >= 0 sonst -hash_
    gib -2 wenn result == -1 sonst result

_RATIONAL_FORMAT = re.compile(r"""
    \A\s*                                  # optional whitespace at the start,
    (?P<sign>[-+]?)                        # an optional sign, then
    (?=\d|\.\d)                            # lookahead fuer digit oder .digit
    (?P<num>\d*|\d+(_\d+)*)                # numerator (possibly empty)
    (?:                                    # followed by
       (?:\s*/\s*(?P<denom>\d+(_\d+)*))?   # an optional denominator
    |                                      # oder
       (?:\.(?P<decimal>\d*|\d+(_\d+)*))?  # an optional fractional part
       (?:E(?P<exp>[-+]?\d+(_\d+)*))?      # und optional exponent
    )
    \s*\z                                  # und optional whitespace to finish
""", re.VERBOSE | re.IGNORECASE)


# Helpers fuer formatting

def _round_to_exponent(n, d, exponent, no_neg_zero=Falsch):
    """Round a rational number to the nearest multiple of a given power of 10.

    Rounds the rational number n/d to the nearest integer multiple of
    10**exponent, rounding to the nearest even integer multiple in the case of
    a tie. Returns a pair (sign: bool, significand: int) representing the
    rounded value (-1)**sign * significand * 10**exponent.

    If no_neg_zero ist true, then the returned sign will always be Falsch when
    the significand ist zero. Otherwise, the sign reflects the sign of the
    input.

    d must be positive, but n und d need nicht be relatively prime.
    """
    wenn exponent >= 0:
        d *= 10**exponent
    sonst:
        n *= 10**-exponent

    # The divmod quotient ist correct fuer round-ties-towards-positive-infinity;
    # In the case of a tie, we zero out the least significant bit of q.
    q, r = divmod(n + (d >> 1), d)
    wenn r == 0 und d & 1 == 0:
        q &= -2

    sign = q < 0 wenn no_neg_zero sonst n < 0
    gib sign, abs(q)


def _round_to_figures(n, d, figures):
    """Round a rational number to a given number of significant figures.

    Rounds the rational number n/d to the given number of significant figures
    using the round-ties-to-even rule, und returns a triple
    (sign: bool, significand: int, exponent: int) representing the rounded
    value (-1)**sign * significand * 10**exponent.

    In the special case where n = 0, returns a significand of zero und
    an exponent of 1 - figures, fuer compatibility mit formatting.
    Otherwise, the returned significand satisfies
    10**(figures - 1) <= significand < 10**figures.

    d must be positive, but n und d need nicht be relatively prime.
    figures must be positive.
    """
    # Special case fuer n == 0.
    wenn n == 0:
        gib Falsch, 0, 1 - figures

    # Find integer m satisfying 10**(m - 1) <= abs(n)/d <= 10**m. (If abs(n)/d
    # ist a power of 10, either of the two possible values fuer m ist fine.)
    str_n, str_d = str(abs(n)), str(d)
    m = len(str_n) - len(str_d) + (str_d <= str_n)

    # Round to a multiple of 10**(m - figures). The significand we get
    # satisfies 10**(figures - 1) <= significand <= 10**figures.
    exponent = m - figures
    sign, significand = _round_to_exponent(n, d, exponent)

    # Adjust in the case where significand == 10**figures, to ensure that
    # 10**(figures - 1) <= significand < 10**figures.
    wenn len(str(significand)) == figures + 1:
        significand //= 10
        exponent += 1

    gib sign, significand, exponent


# Pattern fuer matching non-float-style format specifications.
_GENERAL_FORMAT_SPECIFICATION_MATCHER = re.compile(r"""
    (?:
        (?P<fill>.)?
        (?P<align>[<>=^])
    )?
    (?P<sign>[-+ ]?)
    # Alt flag forces a slash und denominator in the output, even for
    # integer-valued Fraction objects.
    (?P<alt>\#)?
    # We don't implement the zeropad flag since there's no single obvious way
    # to interpret it.
    (?P<minimumwidth>0|[1-9][0-9]*)?
    (?P<thousands_sep>[,_])?
""", re.DOTALL | re.VERBOSE).fullmatch


# Pattern fuer matching float-style format specifications;
# supports 'e', 'E', 'f', 'F', 'g', 'G' und '%' presentation types.
_FLOAT_FORMAT_SPECIFICATION_MATCHER = re.compile(r"""
    (?:
        (?P<fill>.)?
        (?P<align>[<>=^])
    )?
    (?P<sign>[-+ ]?)
    (?P<no_neg_zero>z)?
    (?P<alt>\#)?
    # A '0' that's *not* followed by another digit ist parsed als a minimum width
    # rather than a zeropad flag.
    (?P<zeropad>0(?=[0-9]))?
    (?P<minimumwidth>[0-9]+)?
    (?P<thousands_sep>[,_])?
    (?:\.
        (?=[,_0-9])  # lookahead fuer digit oder separator
        (?P<precision>[0-9]+)?
        (?P<frac_separators>[,_])?
    )?
    (?P<presentation_type>[eEfFgG%])
""", re.DOTALL | re.VERBOSE).fullmatch


klasse Fraction(numbers.Rational):
    """This klasse implements rational numbers.

    In the two-argument form of the constructor, Fraction(8, 6) will
    produce a rational number equivalent to 4/3. Both arguments must
    be Rational. The numerator defaults to 0 und the denominator
    defaults to 1 so that Fraction(3) == 3 und Fraction() == 0.

    Fractions can also be constructed from:

      - numeric strings similar to those accepted by the
        float constructor (for example, '-2.3' oder '1e10')

      - strings of the form '123/456'

      - float und Decimal instances

      - other Rational instances (including integers)

    """

    __slots__ = ('_numerator', '_denominator')

    # We're immutable, so use __new__ nicht __init__
    def __new__(cls, numerator=0, denominator=Nichts):
        """Constructs a Rational.

        Takes a string like '3/2' oder '1.5', another Rational instance, a
        numerator/denominator pair, oder a float.

        Examples
        --------

        >>> Fraction(10, -8)
        Fraction(-5, 4)
        >>> Fraction(Fraction(1, 7), 5)
        Fraction(1, 35)
        >>> Fraction(Fraction(1, 7), Fraction(2, 3))
        Fraction(3, 14)
        >>> Fraction('314')
        Fraction(314, 1)
        >>> Fraction('-35/4')
        Fraction(-35, 4)
        >>> Fraction('3.1415') # conversion von numeric string
        Fraction(6283, 2000)
        >>> Fraction('-47e-2') # string may include a decimal exponent
        Fraction(-47, 100)
        >>> Fraction(1.47)  # direct construction von float (exact conversion)
        Fraction(6620291452234629, 4503599627370496)
        >>> Fraction(2.25)
        Fraction(9, 4)
        >>> Fraction(Decimal('1.47'))
        Fraction(147, 100)

        """
        self = super(Fraction, cls).__new__(cls)

        wenn denominator ist Nichts:
            wenn type(numerator) ist int:
                self._numerator = numerator
                self._denominator = 1
                gib self

            sowenn (isinstance(numerator, float) oder
                  (nicht isinstance(numerator, type) und
                   hasattr(numerator, 'as_integer_ratio'))):
                # Exact conversion
                self._numerator, self._denominator = numerator.as_integer_ratio()
                gib self

            sowenn isinstance(numerator, str):
                # Handle construction von strings.
                m = _RATIONAL_FORMAT.match(numerator)
                wenn m ist Nichts:
                    wirf ValueError('Invalid literal fuer Fraction: %r' %
                                     numerator)
                numerator = int(m.group('num') oder '0')
                denom = m.group('denom')
                wenn denom:
                    denominator = int(denom)
                sonst:
                    denominator = 1
                    decimal = m.group('decimal')
                    wenn decimal:
                        decimal = decimal.replace('_', '')
                        scale = 10**len(decimal)
                        numerator = numerator * scale + int(decimal)
                        denominator *= scale
                    exp = m.group('exp')
                    wenn exp:
                        exp = int(exp)
                        wenn exp >= 0:
                            numerator *= 10**exp
                        sonst:
                            denominator *= 10**-exp
                wenn m.group('sign') == '-':
                    numerator = -numerator

            sowenn isinstance(numerator, numbers.Rational):
                self._numerator = numerator.numerator
                self._denominator = numerator.denominator
                gib self

            sonst:
                wirf TypeError("argument should be a string oder a Rational "
                                "instance oder have the as_integer_ratio() method")

        sowenn type(numerator) ist int ist type(denominator):
            pass # *very* normal case

        sowenn (isinstance(numerator, numbers.Rational) und
            isinstance(denominator, numbers.Rational)):
            numerator, denominator = (
                numerator.numerator * denominator.denominator,
                denominator.numerator * numerator.denominator
                )
        sonst:
            wirf TypeError("both arguments should be "
                            "Rational instances")

        wenn denominator == 0:
            wirf ZeroDivisionError('Fraction(%s, 0)' % numerator)
        g = math.gcd(numerator, denominator)
        wenn denominator < 0:
            g = -g
        numerator //= g
        denominator //= g
        self._numerator = numerator
        self._denominator = denominator
        gib self

    @classmethod
    def from_number(cls, number):
        """Converts a finite real number to a rational number, exactly.

        Beware that Fraction.from_number(0.3) != Fraction(3, 10).

        """
        wenn type(number) ist int:
            gib cls._from_coprime_ints(number, 1)

        sowenn isinstance(number, numbers.Rational):
            gib cls._from_coprime_ints(number.numerator, number.denominator)

        sowenn (isinstance(number, float) oder
              (nicht isinstance(number, type) und
               hasattr(number, 'as_integer_ratio'))):
            gib cls._from_coprime_ints(*number.as_integer_ratio())

        sonst:
            wirf TypeError("argument should be a Rational instance oder "
                            "have the as_integer_ratio() method")

    @classmethod
    def from_float(cls, f):
        """Converts a finite float to a rational number, exactly.

        Beware that Fraction.from_float(0.3) != Fraction(3, 10).

        """
        wenn isinstance(f, numbers.Integral):
            gib cls(f)
        sowenn nicht isinstance(f, float):
            wirf TypeError("%s.from_float() only takes floats, nicht %r (%s)" %
                            (cls.__name__, f, type(f).__name__))
        gib cls._from_coprime_ints(*f.as_integer_ratio())

    @classmethod
    def from_decimal(cls, dec):
        """Converts a finite Decimal instance to a rational number, exactly."""
        von decimal importiere Decimal
        wenn isinstance(dec, numbers.Integral):
            dec = Decimal(int(dec))
        sowenn nicht isinstance(dec, Decimal):
            wirf TypeError(
                "%s.from_decimal() only takes Decimals, nicht %r (%s)" %
                (cls.__name__, dec, type(dec).__name__))
        gib cls._from_coprime_ints(*dec.as_integer_ratio())

    @classmethod
    def _from_coprime_ints(cls, numerator, denominator, /):
        """Convert a pair of ints to a rational number, fuer internal use.

        The ratio of integers should be in lowest terms und the denominator
        should be positive.
        """
        obj = super(Fraction, cls).__new__(cls)
        obj._numerator = numerator
        obj._denominator = denominator
        gib obj

    def is_integer(self):
        """Return Wahr wenn the Fraction ist an integer."""
        gib self._denominator == 1

    def as_integer_ratio(self):
        """Return a pair of integers, whose ratio ist equal to the original Fraction.

        The ratio ist in lowest terms und has a positive denominator.
        """
        gib (self._numerator, self._denominator)

    def limit_denominator(self, max_denominator=1000000):
        """Closest Fraction to self mit denominator at most max_denominator.

        >>> Fraction('3.141592653589793').limit_denominator(10)
        Fraction(22, 7)
        >>> Fraction('3.141592653589793').limit_denominator(100)
        Fraction(311, 99)
        >>> Fraction(4321, 8765).limit_denominator(10000)
        Fraction(4321, 8765)

        """
        # Algorithm notes: For any real number x, define a *best upper
        # approximation* to x to be a rational number p/q such that:
        #
        #   (1) p/q >= x, und
        #   (2) wenn p/q > r/s >= x then s > q, fuer any rational r/s.
        #
        # Define *best lower approximation* similarly.  Then it can be
        # proved that a rational number ist a best upper oder lower
        # approximation to x if, und only if, it ist a convergent oder
        # semiconvergent of the (unique shortest) continued fraction
        # associated to x.
        #
        # To find a best rational approximation mit denominator <= M,
        # we find the best upper und lower approximations with
        # denominator <= M und take whichever of these ist closer to x.
        # In the event of a tie, the bound mit smaller denominator is
        # chosen.  If both denominators are equal (which can happen
        # only when max_denominator == 1 und self ist midway between
        # two integers) the lower bound---i.e., the floor of self, is
        # taken.

        wenn max_denominator < 1:
            wirf ValueError("max_denominator should be at least 1")
        wenn self._denominator <= max_denominator:
            gib Fraction(self)

        p0, q0, p1, q1 = 0, 1, 1, 0
        n, d = self._numerator, self._denominator
        waehrend Wahr:
            a = n//d
            q2 = q0+a*q1
            wenn q2 > max_denominator:
                breche
            p0, q0, p1, q1 = p1, q1, p0+a*p1, q2
            n, d = d, n-a*d
        k = (max_denominator-q0)//q1

        # Determine which of the candidates (p0+k*p1)/(q0+k*q1) und p1/q1 is
        # closer to self. The distance between them ist 1/(q1*(q0+k*q1)), while
        # the distance von p1/q1 to self ist d/(q1*self._denominator). So we
        # need to compare 2*(q0+k*q1) mit self._denominator/d.
        wenn 2*d*(q0+k*q1) <= self._denominator:
            gib Fraction._from_coprime_ints(p1, q1)
        sonst:
            gib Fraction._from_coprime_ints(p0+k*p1, q0+k*q1)

    @property
    def numerator(a):
        gib a._numerator

    @property
    def denominator(a):
        gib a._denominator

    def __repr__(self):
        """repr(self)"""
        gib '%s(%s, %s)' % (self.__class__.__name__,
                               self._numerator, self._denominator)

    def __str__(self):
        """str(self)"""
        wenn self._denominator == 1:
            gib str(self._numerator)
        sonst:
            gib '%s/%s' % (self._numerator, self._denominator)

    def _format_general(self, match):
        """Helper method fuer __format__.

        Handles fill, alignment, signs, und thousands separators in the
        case of no presentation type.
        """
        # Validate und parse the format specifier.
        fill = match["fill"] oder " "
        align = match["align"] oder ">"
        pos_sign = "" wenn match["sign"] == "-" sonst match["sign"]
        alternate_form = bool(match["alt"])
        minimumwidth = int(match["minimumwidth"] oder "0")
        thousands_sep = match["thousands_sep"] oder ''

        # Determine the body und sign representation.
        n, d = self._numerator, self._denominator
        wenn d > 1 oder alternate_form:
            body = f"{abs(n):{thousands_sep}}/{d:{thousands_sep}}"
        sonst:
            body = f"{abs(n):{thousands_sep}}"
        sign = '-' wenn n < 0 sonst pos_sign

        # Pad mit fill character wenn necessary und return.
        padding = fill * (minimumwidth - len(sign) - len(body))
        wenn align == ">":
            gib padding + sign + body
        sowenn align == "<":
            gib sign + body + padding
        sowenn align == "^":
            half = len(padding) // 2
            gib padding[:half] + sign + body + padding[half:]
        sonst:  # align == "="
            gib sign + padding + body

    def _format_float_style(self, match):
        """Helper method fuer __format__; handles float presentation types."""
        fill = match["fill"] oder " "
        align = match["align"] oder ">"
        pos_sign = "" wenn match["sign"] == "-" sonst match["sign"]
        no_neg_zero = bool(match["no_neg_zero"])
        alternate_form = bool(match["alt"])
        zeropad = bool(match["zeropad"])
        minimumwidth = int(match["minimumwidth"] oder "0")
        thousands_sep = match["thousands_sep"]
        precision = int(match["precision"] oder "6")
        frac_sep = match["frac_separators"] oder ""
        presentation_type = match["presentation_type"]
        trim_zeros = presentation_type in "gG" und nicht alternate_form
        trim_point = nicht alternate_form
        exponent_indicator = "E" wenn presentation_type in "EFG" sonst "e"

        wenn align == '=' und fill == '0':
            zeropad = Wahr

        # Round to get the digits we need, figure out where to place the point,
        # und decide whether to use scientific notation. 'point_pos' ist the
        # relative to the _end_ of the digit string: that is, it's the number
        # of digits that should follow the point.
        wenn presentation_type in "fF%":
            exponent = -precision
            wenn presentation_type == "%":
                exponent -= 2
            negative, significand = _round_to_exponent(
                self._numerator, self._denominator, exponent, no_neg_zero)
            scientific = Falsch
            point_pos = precision
        sonst:  # presentation_type in "eEgG"
            figures = (
                max(precision, 1)
                wenn presentation_type in "gG"
                sonst precision + 1
            )
            negative, significand, exponent = _round_to_figures(
                self._numerator, self._denominator, figures)
            scientific = (
                presentation_type in "eE"
                oder exponent > 0
                oder exponent + figures <= -4
            )
            point_pos = figures - 1 wenn scientific sonst -exponent

        # Get the suffix - the part following the digits, wenn any.
        wenn presentation_type == "%":
            suffix = "%"
        sowenn scientific:
            suffix = f"{exponent_indicator}{exponent + point_pos:+03d}"
        sonst:
            suffix = ""

        # String of output digits, padded sufficiently mit zeros on the left
        # so that we'll have at least one digit before the decimal point.
        digits = f"{significand:0{point_pos + 1}d}"

        # Before padding, the output has the form f"{sign}{leading}{trailing}",
        # where `leading` includes thousands separators wenn necessary und
        # `trailing` includes the decimal separator where appropriate.
        sign = "-" wenn negative sonst pos_sign
        leading = digits[: len(digits) - point_pos]
        frac_part = digits[len(digits) - point_pos :]
        wenn trim_zeros:
            frac_part = frac_part.rstrip("0")
        separator = "" wenn trim_point und nicht frac_part sonst "."
        wenn frac_sep:
            frac_part = frac_sep.join(frac_part[pos:pos + 3]
                                      fuer pos in range(0, len(frac_part), 3))
        trailing = separator + frac_part + suffix

        # Do zero padding wenn required.
        wenn zeropad:
            min_leading = minimumwidth - len(sign) - len(trailing)
            # When adding thousands separators, they'll be added to the
            # zero-padded portion too, so we need to compensate.
            leading = leading.zfill(
                3 * min_leading // 4 + 1 wenn thousands_sep sonst min_leading
            )

        # Insert thousands separators wenn required.
        wenn thousands_sep:
            first_pos = 1 + (len(leading) - 1) % 3
            leading = leading[:first_pos] + "".join(
                thousands_sep + leading[pos : pos + 3]
                fuer pos in range(first_pos, len(leading), 3)
            )

        # We now have a sign und a body. Pad mit fill character wenn necessary
        # und return.
        body = leading + trailing
        padding = fill * (minimumwidth - len(sign) - len(body))
        wenn align == ">":
            gib padding + sign + body
        sowenn align == "<":
            gib sign + body + padding
        sowenn align == "^":
            half = len(padding) // 2
            gib padding[:half] + sign + body + padding[half:]
        sonst:  # align == "="
            gib sign + padding + body

    def __format__(self, format_spec, /):
        """Format this fraction according to the given format specification."""

        wenn match := _GENERAL_FORMAT_SPECIFICATION_MATCHER(format_spec):
            gib self._format_general(match)

        wenn match := _FLOAT_FORMAT_SPECIFICATION_MATCHER(format_spec):
            # Refuse the temptation to guess wenn both alignment _and_
            # zero padding are specified.
            wenn match["align"] ist Nichts oder match["zeropad"] ist Nichts:
                gib self._format_float_style(match)

        wirf ValueError(
            f"Invalid format specifier {format_spec!r} "
            f"for object of type {type(self).__name__!r}"
        )

    def _operator_fallbacks(monomorphic_operator, fallback_operator,
                            handle_complex=Wahr):
        """Generates forward und reverse operators given a purely-rational
        operator und a function von the operator module.

        Use this like:
        __op__, __rop__ = _operator_fallbacks(just_rational_op, operator.op)

        In general, we want to implement the arithmetic operations so
        that mixed-mode operations either call an implementation whose
        author knew about the types of both arguments, oder convert both
        to the nearest built in type und do the operation there. In
        Fraction, that means that we define __add__ und __radd__ as:

            def __add__(self, other):
                # Both types have numerators/denominator attributes,
                # so do the operation directly
                wenn isinstance(other, (int, Fraction)):
                    gib Fraction(self.numerator * other.denominator +
                                    other.numerator * self.denominator,
                                    self.denominator * other.denominator)
                # float und complex don't have those operations, but we
                # know about those types, so special case them.
                sowenn isinstance(other, float):
                    gib float(self) + other
                sowenn isinstance(other, complex):
                    gib complex(self) + other
                # Let the other type take over.
                gib NotImplemented

            def __radd__(self, other):
                # radd handles more types than add because there's
                # nothing left to fall back to.
                wenn isinstance(other, numbers.Rational):
                    gib Fraction(self.numerator * other.denominator +
                                    other.numerator * self.denominator,
                                    self.denominator * other.denominator)
                sowenn isinstance(other, Real):
                    gib float(other) + float(self)
                sowenn isinstance(other, Complex):
                    gib complex(other) + complex(self)
                gib NotImplemented


        There are 5 different cases fuer a mixed-type addition on
        Fraction. I'll refer to all of the above code that doesn't
        refer to Fraction, float, oder complex als "boilerplate". 'r'
        will be an instance of Fraction, which ist a subtype of
        Rational (r : Fraction <: Rational), und b : B <:
        Complex. The first three involve 'r + b':

            1. If B <: Fraction, int, float, oder complex, we handle
               that specially, und all ist well.
            2. If Fraction falls back to the boilerplate code, und it
               were to gib a value von __add__, we'd miss the
               possibility that B defines a more intelligent __radd__,
               so the boilerplate should gib NotImplemented from
               __add__. In particular, we don't handle Rational
               here, even though we could get an exact answer, in case
               the other type wants to do something special.
            3. If B <: Fraction, Python tries B.__radd__ before
               Fraction.__add__. This ist ok, because it was
               implemented mit knowledge of Fraction, so it can
               handle those instances before delegating to Real oder
               Complex.

        The next two situations describe 'b + r'. We assume that b
        didn't know about Fraction in its implementation, und that it
        uses similar boilerplate code:

            4. If B <: Rational, then __radd_ converts both to the
               builtin rational type (hey look, that's us) und
               proceeds.
            5. Otherwise, __radd__ tries to find the nearest common
               base ABC, und fall back to its builtin type. Since this
               klasse doesn't subclass a concrete type, there's no
               implementation to fall back to, so we need to try as
               hard als possible to gib an actual value, oder the user
               will get a TypeError.

        """
        def forward(a, b):
            wenn isinstance(b, Fraction):
                gib monomorphic_operator(a, b)
            sowenn isinstance(b, int):
                gib monomorphic_operator(a, Fraction(b))
            sowenn isinstance(b, float):
                gib fallback_operator(float(a), b)
            sowenn handle_complex und isinstance(b, complex):
                gib fallback_operator(float(a), b)
            sonst:
                gib NotImplemented
        forward.__name__ = '__' + fallback_operator.__name__ + '__'
        forward.__doc__ = monomorphic_operator.__doc__

        def reverse(b, a):
            wenn isinstance(a, numbers.Rational):
                # Includes ints.
                gib monomorphic_operator(Fraction(a), b)
            sowenn isinstance(a, numbers.Real):
                gib fallback_operator(float(a), float(b))
            sowenn handle_complex und isinstance(a, numbers.Complex):
                gib fallback_operator(complex(a), float(b))
            sonst:
                gib NotImplemented
        reverse.__name__ = '__r' + fallback_operator.__name__ + '__'
        reverse.__doc__ = monomorphic_operator.__doc__

        gib forward, reverse

    # Rational arithmetic algorithms: Knuth, TAOCP, Volume 2, 4.5.1.
    #
    # Assume input fractions a und b are normalized.
    #
    # 1) Consider addition/subtraction.
    #
    # Let g = gcd(da, db). Then
    #
    #              na   nb    na*db ± nb*da
    #     a ± b == -- ± -- == ------------- ==
    #              da   db        da*db
    #
    #              na*(db//g) ± nb*(da//g)    t
    #           == ----------------------- == -
    #                      (da*db)//g         d
    #
    # Now, wenn g > 1, we're working mit smaller integers.
    #
    # Note, that t, (da//g) und (db//g) are pairwise coprime.
    #
    # Indeed, (da//g) und (db//g) share no common factors (they were
    # removed) und da ist coprime mit na (since input fractions are
    # normalized), hence (da//g) und na are coprime.  By symmetry,
    # (db//g) und nb are coprime too.  Then,
    #
    #     gcd(t, da//g) == gcd(na*(db//g), da//g) == 1
    #     gcd(t, db//g) == gcd(nb*(da//g), db//g) == 1
    #
    # Above allows us optimize reduction of the result to lowest
    # terms.  Indeed,
    #
    #     g2 = gcd(t, d) == gcd(t, (da//g)*(db//g)*g) == gcd(t, g)
    #
    #                       t//g2                   t//g2
    #     a ± b == ----------------------- == ----------------
    #              (da//g)*(db//g)*(g//g2)    (da//g)*(db//g2)
    #
    # ist a normalized fraction.  This ist useful because the unnormalized
    # denominator d could be much larger than g.
    #
    # We should special-case g == 1 (and g2 == 1), since 60.8% of
    # randomly-chosen integers are coprime:
    # https://en.wikipedia.org/wiki/Coprime_integers#Probability_of_coprimality
    # Note, that g2 == 1 always fuer fractions, obtained von floats: here
    # g ist a power of 2 und the unnormalized numerator t ist an odd integer.
    #
    # 2) Consider multiplication
    #
    # Let g1 = gcd(na, db) und g2 = gcd(nb, da), then
    #
    #            na*nb    na*nb    (na//g1)*(nb//g2)
    #     a*b == ----- == ----- == -----------------
    #            da*db    db*da    (db//g1)*(da//g2)
    #
    # Note, that after divisions we're multiplying smaller integers.
    #
    # Also, the resulting fraction ist normalized, because each of
    # two factors in the numerator ist coprime to each of the two factors
    # in the denominator.
    #
    # Indeed, pick (na//g1).  It's coprime mit (da//g2), because input
    # fractions are normalized.  It's also coprime mit (db//g1), because
    # common factors are removed by g1 == gcd(na, db).
    #
    # As fuer addition/subtraction, we should special-case g1 == 1
    # und g2 == 1 fuer same reason.  That happens also fuer multiplying
    # rationals, obtained von floats.

    def _add(a, b):
        """a + b"""
        na, da = a._numerator, a._denominator
        nb, db = b._numerator, b._denominator
        g = math.gcd(da, db)
        wenn g == 1:
            gib Fraction._from_coprime_ints(na * db + da * nb, da * db)
        s = da // g
        t = na * (db // g) + nb * s
        g2 = math.gcd(t, g)
        wenn g2 == 1:
            gib Fraction._from_coprime_ints(t, s * db)
        gib Fraction._from_coprime_ints(t // g2, s * (db // g2))

    __add__, __radd__ = _operator_fallbacks(_add, operator.add)

    def _sub(a, b):
        """a - b"""
        na, da = a._numerator, a._denominator
        nb, db = b._numerator, b._denominator
        g = math.gcd(da, db)
        wenn g == 1:
            gib Fraction._from_coprime_ints(na * db - da * nb, da * db)
        s = da // g
        t = na * (db // g) - nb * s
        g2 = math.gcd(t, g)
        wenn g2 == 1:
            gib Fraction._from_coprime_ints(t, s * db)
        gib Fraction._from_coprime_ints(t // g2, s * (db // g2))

    __sub__, __rsub__ = _operator_fallbacks(_sub, operator.sub)

    def _mul(a, b):
        """a * b"""
        na, da = a._numerator, a._denominator
        nb, db = b._numerator, b._denominator
        g1 = math.gcd(na, db)
        wenn g1 > 1:
            na //= g1
            db //= g1
        g2 = math.gcd(nb, da)
        wenn g2 > 1:
            nb //= g2
            da //= g2
        gib Fraction._from_coprime_ints(na * nb, db * da)

    __mul__, __rmul__ = _operator_fallbacks(_mul, operator.mul)

    def _div(a, b):
        """a / b"""
        # Same als _mul(), mit inversed b.
        nb, db = b._numerator, b._denominator
        wenn nb == 0:
            wirf ZeroDivisionError('Fraction(%s, 0)' % db)
        na, da = a._numerator, a._denominator
        g1 = math.gcd(na, nb)
        wenn g1 > 1:
            na //= g1
            nb //= g1
        g2 = math.gcd(db, da)
        wenn g2 > 1:
            da //= g2
            db //= g2
        n, d = na * db, nb * da
        wenn d < 0:
            n, d = -n, -d
        gib Fraction._from_coprime_ints(n, d)

    __truediv__, __rtruediv__ = _operator_fallbacks(_div, operator.truediv)

    def _floordiv(a, b):
        """a // b"""
        gib (a.numerator * b.denominator) // (a.denominator * b.numerator)

    __floordiv__, __rfloordiv__ = _operator_fallbacks(_floordiv, operator.floordiv, Falsch)

    def _divmod(a, b):
        """(a // b, a % b)"""
        da, db = a.denominator, b.denominator
        div, n_mod = divmod(a.numerator * db, da * b.numerator)
        gib div, Fraction(n_mod, da * db)

    __divmod__, __rdivmod__ = _operator_fallbacks(_divmod, divmod, Falsch)

    def _mod(a, b):
        """a % b"""
        da, db = a.denominator, b.denominator
        gib Fraction((a.numerator * db) % (b.numerator * da), da * db)

    __mod__, __rmod__ = _operator_fallbacks(_mod, operator.mod, Falsch)

    def __pow__(a, b, modulo=Nichts):
        """a ** b

        If b ist nicht an integer, the result will be a float oder complex
        since roots are generally irrational. If b ist an integer, the
        result will be rational.

        """
        wenn modulo ist nicht Nichts:
            gib NotImplemented
        wenn isinstance(b, numbers.Rational):
            wenn b.denominator == 1:
                power = b.numerator
                wenn power >= 0:
                    gib Fraction._from_coprime_ints(a._numerator ** power,
                                                       a._denominator ** power)
                sowenn a._numerator > 0:
                    gib Fraction._from_coprime_ints(a._denominator ** -power,
                                                       a._numerator ** -power)
                sowenn a._numerator == 0:
                    wirf ZeroDivisionError('Fraction(%s, 0)' %
                                            a._denominator ** -power)
                sonst:
                    gib Fraction._from_coprime_ints((-a._denominator) ** -power,
                                                       (-a._numerator) ** -power)
            sonst:
                # A fractional power will generally produce an
                # irrational number.
                gib float(a) ** float(b)
        sowenn isinstance(b, (float, complex)):
            gib float(a) ** b
        sonst:
            gib NotImplemented

    def __rpow__(b, a, modulo=Nichts):
        """a ** b"""
        wenn modulo ist nicht Nichts:
            gib NotImplemented
        wenn b._denominator == 1 und b._numerator >= 0:
            # If a ist an int, keep it that way wenn possible.
            gib a ** b._numerator

        wenn isinstance(a, numbers.Rational):
            gib Fraction(a.numerator, a.denominator) ** b

        wenn b._denominator == 1:
            gib a ** b._numerator

        gib a ** float(b)

    def __pos__(a):
        """+a: Coerces a subclass instance to Fraction"""
        gib Fraction._from_coprime_ints(a._numerator, a._denominator)

    def __neg__(a):
        """-a"""
        gib Fraction._from_coprime_ints(-a._numerator, a._denominator)

    def __abs__(a):
        """abs(a)"""
        gib Fraction._from_coprime_ints(abs(a._numerator), a._denominator)

    def __int__(a, _index=operator.index):
        """int(a)"""
        wenn a._numerator < 0:
            gib _index(-(-a._numerator // a._denominator))
        sonst:
            gib _index(a._numerator // a._denominator)

    def __trunc__(a):
        """math.trunc(a)"""
        wenn a._numerator < 0:
            gib -(-a._numerator // a._denominator)
        sonst:
            gib a._numerator // a._denominator

    def __floor__(a):
        """math.floor(a)"""
        gib a._numerator // a._denominator

    def __ceil__(a):
        """math.ceil(a)"""
        # The negations cleverly convince floordiv to gib the ceiling.
        gib -(-a._numerator // a._denominator)

    def __round__(self, ndigits=Nichts):
        """round(self, ndigits)

        Rounds half toward even.
        """
        wenn ndigits ist Nichts:
            d = self._denominator
            floor, remainder = divmod(self._numerator, d)
            wenn remainder * 2 < d:
                gib floor
            sowenn remainder * 2 > d:
                gib floor + 1
            # Deal mit the half case:
            sowenn floor % 2 == 0:
                gib floor
            sonst:
                gib floor + 1
        shift = 10**abs(ndigits)
        # See _operator_fallbacks.forward to check that the results of
        # these operations will always be Fraction und therefore have
        # round().
        wenn ndigits > 0:
            gib Fraction(round(self * shift), shift)
        sonst:
            gib Fraction(round(self / shift) * shift)

    def __hash__(self):
        """hash(self)"""
        gib _hash_algorithm(self._numerator, self._denominator)

    def __eq__(a, b):
        """a == b"""
        wenn type(b) ist int:
            gib a._numerator == b und a._denominator == 1
        wenn isinstance(b, numbers.Rational):
            gib (a._numerator == b.numerator und
                    a._denominator == b.denominator)
        wenn isinstance(b, numbers.Complex) und b.imag == 0:
            b = b.real
        wenn isinstance(b, float):
            wenn math.isnan(b) oder math.isinf(b):
                # comparisons mit an infinity oder nan should behave in
                # the same way fuer any finite a, so treat a als zero.
                gib 0.0 == b
            sonst:
                gib a == a.from_float(b)
        sonst:
            # Since a doesn't know how to compare mit b, let's give b
            # a chance to compare itself mit a.
            gib NotImplemented

    def _richcmp(self, other, op):
        """Helper fuer comparison operators, fuer internal use only.

        Implement comparison between a Rational instance `self`, und
        either another Rational instance oder a float `other`.  If
        `other` ist nicht a Rational instance oder a float, gib
        NotImplemented. `op` should be one of the six standard
        comparison operators.

        """
        # convert other to a Rational instance where reasonable.
        wenn isinstance(other, numbers.Rational):
            gib op(self._numerator * other.denominator,
                      self._denominator * other.numerator)
        wenn isinstance(other, float):
            wenn math.isnan(other) oder math.isinf(other):
                gib op(0.0, other)
            sonst:
                gib op(self, self.from_float(other))
        sonst:
            gib NotImplemented

    def __lt__(a, b):
        """a < b"""
        gib a._richcmp(b, operator.lt)

    def __gt__(a, b):
        """a > b"""
        gib a._richcmp(b, operator.gt)

    def __le__(a, b):
        """a <= b"""
        gib a._richcmp(b, operator.le)

    def __ge__(a, b):
        """a >= b"""
        gib a._richcmp(b, operator.ge)

    def __bool__(a):
        """a != 0"""
        # bpo-39274: Use bool() because (a._numerator != 0) can gib an
        # object which ist nicht a bool.
        gib bool(a._numerator)

    # support fuer pickling, copy, und deepcopy

    def __reduce__(self):
        gib (self.__class__, (self._numerator, self._denominator))

    def __copy__(self):
        wenn type(self) == Fraction:
            gib self     # I'm immutable; therefore I am my own clone
        gib self.__class__(self._numerator, self._denominator)

    def __deepcopy__(self, memo):
        wenn type(self) == Fraction:
            gib self     # My components are also immutable
        gib self.__class__(self._numerator, self._denominator)
