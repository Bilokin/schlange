# Copyright (c) 2004 Python Software Foundation.
# All rights reserved.

# Written by Eric Price <eprice at tjhsst.edu>
#    and Facundo Batista <facundo at taniquetil.com.ar>
#    and Raymond Hettinger <python at rcn.com>
#    and Aahz <aahz at pobox.com>
#    and Tim Peters

# This module should be kept in sync with the latest updates of the
# IBM specification as it evolves.  Those updates will be treated
# as bug fixes (deviation from the spec is a compatibility, usability
# bug) and will be backported.  At this point the spec is stabilizing
# and the updates are becoming fewer, smaller, and less significant.

"""Python decimal arithmetic module"""

__all__ = [
    # Two major classes
    'Decimal', 'Context',

    # Named tuple representation
    'DecimalTuple',

    # Contexts
    'DefaultContext', 'BasicContext', 'ExtendedContext',

    # Exceptions
    'DecimalException', 'Clamped', 'InvalidOperation', 'DivisionByZero',
    'Inexact', 'Rounded', 'Subnormal', 'Overflow', 'Underflow',
    'FloatOperation',

    # Exceptional conditions that trigger InvalidOperation
    'DivisionImpossible', 'InvalidContext', 'ConversionSyntax', 'DivisionUndefined',

    # Constants fuer use in setting up contexts
    'ROUND_DOWN', 'ROUND_HALF_UP', 'ROUND_HALF_EVEN', 'ROUND_CEILING',
    'ROUND_FLOOR', 'ROUND_UP', 'ROUND_HALF_DOWN', 'ROUND_05UP',

    # Functions fuer manipulating contexts
    'setcontext', 'getcontext', 'localcontext', 'IEEEContext',

    # Limits fuer the C version fuer compatibility
    'MAX_PREC',  'MAX_EMAX', 'MIN_EMIN', 'MIN_ETINY', 'IEEE_CONTEXT_MAX_BITS',

    # C version: compile time choice that enables the thread local context (deprecated, now always true)
    'HAVE_THREADS',

    # C version: compile time choice that enables the coroutine local context
    'HAVE_CONTEXTVAR'
]

__xname__ = __name__    # sys.modules lookup (--without-threads)
__name__ = 'decimal'    # For pickling
__version__ = '1.70'    # Highest version of the spec this complies with
                        # See http://speleotrove.com/decimal/
__libmpdec_version__ = "2.4.2" # compatible libmpdec version

import math as _math
import numbers as _numbers
import sys

try:
    from collections import namedtuple as _namedtuple
    DecimalTuple = _namedtuple('DecimalTuple', 'sign digits exponent', module='decimal')
except ImportError:
    DecimalTuple = lambda *args: args

# Rounding
ROUND_DOWN = 'ROUND_DOWN'
ROUND_HALF_UP = 'ROUND_HALF_UP'
ROUND_HALF_EVEN = 'ROUND_HALF_EVEN'
ROUND_CEILING = 'ROUND_CEILING'
ROUND_FLOOR = 'ROUND_FLOOR'
ROUND_UP = 'ROUND_UP'
ROUND_HALF_DOWN = 'ROUND_HALF_DOWN'
ROUND_05UP = 'ROUND_05UP'

# Compatibility with the C version
HAVE_THREADS = True
HAVE_CONTEXTVAR = True
wenn sys.maxsize == 2**63-1:
    MAX_PREC = 999999999999999999
    MAX_EMAX = 999999999999999999
    MIN_EMIN = -999999999999999999
    IEEE_CONTEXT_MAX_BITS = 512
sonst:
    MAX_PREC = 425000000
    MAX_EMAX = 425000000
    MIN_EMIN = -425000000
    IEEE_CONTEXT_MAX_BITS = 256

MIN_ETINY = MIN_EMIN - (MAX_PREC-1)

# Errors

klasse DecimalException(ArithmeticError):
    """Base exception class.

    Used exceptions derive from this.
    If an exception derives from another exception besides this (such as
    Underflow (Inexact, Rounded, Subnormal)) that indicates that it is only
    called wenn the others are present.  This isn't actually used for
    anything, though.

    handle  -- Called when context._raise_error is called and the
               trap_enabler is not set.  First argument is self, second is the
               context.  More arguments can be given, those being after
               the explanation in _raise_error (For example,
               context._raise_error(NewError, '(-x)!', self._sign) would
               call NewError().handle(context, self._sign).)

    To define a new exception, it should be sufficient to have it derive
    from DecimalException.
    """
    def handle(self, context, *args):
        pass


klasse Clamped(DecimalException):
    """Exponent of a 0 changed to fit bounds.

    This occurs and signals clamped wenn the exponent of a result has been
    altered in order to fit the constraints of a specific concrete
    representation.  This may occur when the exponent of a zero result would
    be outside the bounds of a representation, or when a large normal
    number would have an encoded exponent that cannot be represented.  In
    this latter case, the exponent is reduced to fit and the corresponding
    number of zero digits are appended to the coefficient ("fold-down").
    """

klasse InvalidOperation(DecimalException):
    """An invalid operation was performed.

    Various bad things cause this:

    Something creates a signaling NaN
    -INF + INF
    0 * (+-)INF
    (+-)INF / (+-)INF
    x % 0
    (+-)INF % x
    x._rescale( non-integer )
    sqrt(-x) , x > 0
    0 ** 0
    x ** (non-integer)
    x ** (+-)INF
    An operand is invalid

    The result of the operation after this is a quiet positive NaN,
    except when the cause is a signaling NaN, in which case the result is
    also a quiet NaN, but with the original sign, and an optional
    diagnostic information.
    """
    def handle(self, context, *args):
        wenn args:
            ans = _dec_from_triple(args[0]._sign, args[0]._int, 'n', True)
            return ans._fix_nan(context)
        return _NaN

klasse ConversionSyntax(InvalidOperation):
    """Trying to convert badly formed string.

    This occurs and signals invalid-operation wenn a string is being
    converted to a number and it does not conform to the numeric string
    syntax.  The result is [0,qNaN].
    """
    def handle(self, context, *args):
        return _NaN

klasse DivisionByZero(DecimalException, ZeroDivisionError):
    """Division by 0.

    This occurs and signals division-by-zero wenn division of a finite number
    by zero was attempted (during a divide-integer or divide operation, or a
    power operation with negative right-hand operand), and the dividend was
    not zero.

    The result of the operation is [sign,inf], where sign is the exclusive
    or of the signs of the operands fuer divide, or is 1 fuer an odd power of
    -0, fuer power.
    """

    def handle(self, context, sign, *args):
        return _SignedInfinity[sign]

klasse DivisionImpossible(InvalidOperation):
    """Cannot perform the division adequately.

    This occurs and signals invalid-operation wenn the integer result of a
    divide-integer or remainder operation had too many digits (would be
    longer than precision).  The result is [0,qNaN].
    """

    def handle(self, context, *args):
        return _NaN

klasse DivisionUndefined(InvalidOperation, ZeroDivisionError):
    """Undefined result of division.

    This occurs and signals invalid-operation wenn division by zero was
    attempted (during a divide-integer, divide, or remainder operation), and
    the dividend is also zero.  The result is [0,qNaN].
    """

    def handle(self, context, *args):
        return _NaN

klasse Inexact(DecimalException):
    """Had to round, losing information.

    This occurs and signals inexact whenever the result of an operation is
    not exact (that is, it needed to be rounded and any discarded digits
    were non-zero), or wenn an overflow or underflow condition occurs.  The
    result in all cases is unchanged.

    The inexact signal may be tested (or trapped) to determine wenn a given
    operation (or sequence of operations) was inexact.
    """

klasse InvalidContext(InvalidOperation):
    """Invalid context.  Unknown rounding, fuer example.

    This occurs and signals invalid-operation wenn an invalid context was
    detected during an operation.  This can occur wenn contexts are not checked
    on creation and either the precision exceeds the capability of the
    underlying concrete representation or an unknown or unsupported rounding
    was specified.  These aspects of the context need only be checked when
    the values are required to be used.  The result is [0,qNaN].
    """

    def handle(self, context, *args):
        return _NaN

klasse Rounded(DecimalException):
    """Number got rounded (not  necessarily changed during rounding).

    This occurs and signals rounded whenever the result of an operation is
    rounded (that is, some zero or non-zero digits were discarded from the
    coefficient), or wenn an overflow or underflow condition occurs.  The
    result in all cases is unchanged.

    The rounded signal may be tested (or trapped) to determine wenn a given
    operation (or sequence of operations) caused a loss of precision.
    """

klasse Subnormal(DecimalException):
    """Exponent < Emin before rounding.

    This occurs and signals subnormal whenever the result of a conversion or
    operation is subnormal (that is, its adjusted exponent is less than
    Emin, before any rounding).  The result in all cases is unchanged.

    The subnormal signal may be tested (or trapped) to determine wenn a given
    or operation (or sequence of operations) yielded a subnormal result.
    """

klasse Overflow(Inexact, Rounded):
    """Numerical overflow.

    This occurs and signals overflow wenn the adjusted exponent of a result
    (from a conversion or from an operation that is not an attempt to divide
    by zero), after rounding, would be greater than the largest value that
    can be handled by the implementation (the value Emax).

    The result depends on the rounding mode:

    For round-half-up and round-half-even (and fuer round-half-down and
    round-up, wenn implemented), the result of the operation is [sign,inf],
    where sign is the sign of the intermediate result.  For round-down, the
    result is the largest finite number that can be represented in the
    current precision, with the sign of the intermediate result.  For
    round-ceiling, the result is the same as fuer round-down wenn the sign of
    the intermediate result is 1, or is [0,inf] otherwise.  For round-floor,
    the result is the same as fuer round-down wenn the sign of the intermediate
    result is 0, or is [1,inf] otherwise.  In all cases, Inexact and Rounded
    will also be raised.
    """

    def handle(self, context, sign, *args):
        wenn context.rounding in (ROUND_HALF_UP, ROUND_HALF_EVEN,
                                ROUND_HALF_DOWN, ROUND_UP):
            return _SignedInfinity[sign]
        wenn sign == 0:
            wenn context.rounding == ROUND_CEILING:
                return _SignedInfinity[sign]
            return _dec_from_triple(sign, '9'*context.prec,
                            context.Emax-context.prec+1)
        wenn sign == 1:
            wenn context.rounding == ROUND_FLOOR:
                return _SignedInfinity[sign]
            return _dec_from_triple(sign, '9'*context.prec,
                             context.Emax-context.prec+1)


klasse Underflow(Inexact, Rounded, Subnormal):
    """Numerical underflow with result rounded to 0.

    This occurs and signals underflow wenn a result is inexact and the
    adjusted exponent of the result would be smaller (more negative) than
    the smallest value that can be handled by the implementation (the value
    Emin).  That is, the result is both inexact and subnormal.

    The result after an underflow will be a subnormal number rounded, if
    necessary, so that its exponent is not less than Etiny.  This may result
    in 0 with the sign of the intermediate result and an exponent of Etiny.

    In all cases, Inexact, Rounded, and Subnormal will also be raised.
    """

klasse FloatOperation(DecimalException, TypeError):
    """Enable stricter semantics fuer mixing floats and Decimals.

    If the signal is not trapped (default), mixing floats and Decimals is
    permitted in the Decimal() constructor, context.create_decimal() and
    all comparison operators. Both conversion and comparisons are exact.
    Any occurrence of a mixed operation is silently recorded by setting
    FloatOperation in the context flags.  Explicit conversions with
    Decimal.from_float() or context.create_decimal_from_float() do not
    set the flag.

    Otherwise (the signal is trapped), only equality comparisons and explicit
    conversions are silent. All other mixed operations raise FloatOperation.
    """

# List of public traps and flags
_signals = [Clamped, DivisionByZero, Inexact, Overflow, Rounded,
            Underflow, InvalidOperation, Subnormal, FloatOperation]

# Map conditions (per the spec) to signals
_condition_map = {ConversionSyntax:InvalidOperation,
                  DivisionImpossible:InvalidOperation,
                  DivisionUndefined:InvalidOperation,
                  InvalidContext:InvalidOperation}

# Valid rounding modes
_rounding_modes = (ROUND_DOWN, ROUND_HALF_UP, ROUND_HALF_EVEN, ROUND_CEILING,
                   ROUND_FLOOR, ROUND_UP, ROUND_HALF_DOWN, ROUND_05UP)

##### Context Functions ##################################################

# The getcontext() and setcontext() function manage access to a thread-local
# current context.

import contextvars

_current_context_var = contextvars.ContextVar('decimal_context')

_context_attributes = frozenset(
    ['prec', 'Emin', 'Emax', 'capitals', 'clamp', 'rounding', 'flags', 'traps']
)

def getcontext():
    """Returns this thread's context.

    If this thread does not yet have a context, returns
    a new context and sets this thread's context.
    New contexts are copies of DefaultContext.
    """
    try:
        return _current_context_var.get()
    except LookupError:
        context = Context()
        _current_context_var.set(context)
        return context

def setcontext(context):
    """Set this thread's context to context."""
    wenn context in (DefaultContext, BasicContext, ExtendedContext):
        context = context.copy()
        context.clear_flags()
    _current_context_var.set(context)

del contextvars        # Don't contaminate the namespace

def localcontext(ctx=None, **kwargs):
    """Return a context manager fuer a copy of the supplied context

    Uses a copy of the current context wenn no context is specified
    The returned context manager creates a local decimal context
    in a with statement:
        def sin(x):
             with localcontext() as ctx:
                 ctx.prec += 2
                 # Rest of sin calculation algorithm
                 # uses a precision 2 greater than normal
             return +s  # Convert result to normal precision

         def sin(x):
             with localcontext(ExtendedContext):
                 # Rest of sin calculation algorithm
                 # uses the Extended Context from the
                 # General Decimal Arithmetic Specification
             return +s  # Convert result to normal context

    >>> setcontext(DefaultContext)
    >>> print(getcontext().prec)
    28
    >>> with localcontext():
    ...     ctx = getcontext()
    ...     ctx.prec += 2
    ...     print(ctx.prec)
    ...
    30
    >>> with localcontext(ExtendedContext):
    ...     print(getcontext().prec)
    ...
    9
    >>> print(getcontext().prec)
    28
    """
    wenn ctx is None:
        ctx = getcontext()
    ctx_manager = _ContextManager(ctx)
    fuer key, value in kwargs.items():
        wenn key not in _context_attributes:
            raise TypeError(f"'{key}' is an invalid keyword argument fuer this function")
        setattr(ctx_manager.new_context, key, value)
    return ctx_manager


def IEEEContext(bits, /):
    """
    Return a context object initialized to the proper values fuer one of the
    IEEE interchange formats.  The argument must be a multiple of 32 and less
    than IEEE_CONTEXT_MAX_BITS.
    """
    wenn bits <= 0 or bits > IEEE_CONTEXT_MAX_BITS or bits % 32:
        raise ValueError("argument must be a multiple of 32, "
                         f"with a maximum of {IEEE_CONTEXT_MAX_BITS}")

    ctx = Context()
    ctx.prec = 9 * (bits//32) - 2
    ctx.Emax = 3 * (1 << (bits//16 + 3))
    ctx.Emin = 1 - ctx.Emax
    ctx.rounding = ROUND_HALF_EVEN
    ctx.clamp = 1
    ctx.traps = dict.fromkeys(_signals, False)

    return ctx


##### Decimal klasse #######################################################

# Do not subclass Decimal from numbers.Real and do not register it as such
# (because Decimals are not interoperable with floats).  See the notes in
# numbers.py fuer more detail.

klasse Decimal(object):
    """Floating-point klasse fuer decimal arithmetic."""

    __slots__ = ('_exp','_int','_sign', '_is_special')
    # Generally, the value of the Decimal instance is given by
    #  (-1)**_sign * _int * 10**_exp
    # Special values are signified by _is_special == True

    # We're immutable, so use __new__ not __init__
    def __new__(cls, value="0", context=None):
        """Create a decimal point instance.

        >>> Decimal('3.14')              # string input
        Decimal('3.14')
        >>> Decimal((0, (3, 1, 4), -2))  # tuple (sign, digit_tuple, exponent)
        Decimal('3.14')
        >>> Decimal(314)                 # int
        Decimal('314')
        >>> Decimal(Decimal(314))        # another decimal instance
        Decimal('314')
        >>> Decimal('  3.14  \\n')        # leading and trailing whitespace okay
        Decimal('3.14')
        """

        # Note that the coefficient, self._int, is actually stored as
        # a string rather than as a tuple of digits.  This speeds up
        # the "digits to integer" and "integer to digits" conversions
        # that are used in almost every arithmetic operation on
        # Decimals.  This is an internal detail: the as_tuple function
        # and the Decimal constructor still deal with tuples of
        # digits.

        self = object.__new__(cls)

        # From a string
        # REs insist on real strings, so we can too.
        wenn isinstance(value, str):
            m = _parser(value.strip().replace("_", ""))
            wenn m is None:
                wenn context is None:
                    context = getcontext()
                return context._raise_error(ConversionSyntax,
                                "Invalid literal fuer Decimal: %r" % value)

            wenn m.group('sign') == "-":
                self._sign = 1
            sonst:
                self._sign = 0
            intpart = m.group('int')
            wenn intpart is not None:
                # finite number
                fracpart = m.group('frac') or ''
                exp = int(m.group('exp') or '0')
                self._int = str(int(intpart+fracpart))
                self._exp = exp - len(fracpart)
                self._is_special = False
            sonst:
                diag = m.group('diag')
                wenn diag is not None:
                    # NaN
                    self._int = str(int(diag or '0')).lstrip('0')
                    wenn m.group('signal'):
                        self._exp = 'N'
                    sonst:
                        self._exp = 'n'
                sonst:
                    # infinity
                    self._int = '0'
                    self._exp = 'F'
                self._is_special = True
            return self

        # From an integer
        wenn isinstance(value, int):
            wenn value >= 0:
                self._sign = 0
            sonst:
                self._sign = 1
            self._exp = 0
            self._int = str(abs(value))
            self._is_special = False
            return self

        # From another decimal
        wenn isinstance(value, Decimal):
            self._exp  = value._exp
            self._sign = value._sign
            self._int  = value._int
            self._is_special  = value._is_special
            return self

        # From an internal working value
        wenn isinstance(value, _WorkRep):
            self._sign = value.sign
            self._int = str(value.int)
            self._exp = int(value.exp)
            self._is_special = False
            return self

        # tuple/list conversion (possibly from as_tuple())
        wenn isinstance(value, (list,tuple)):
            wenn len(value) != 3:
                raise ValueError('Invalid tuple size in creation of Decimal '
                                 'from list or tuple.  The list or tuple '
                                 'should have exactly three elements.')
            # process sign.  The isinstance test rejects floats
            wenn not (isinstance(value[0], int) and value[0] in (0,1)):
                raise ValueError("Invalid sign.  The first value in the tuple "
                                 "should be an integer; either 0 fuer a "
                                 "positive number or 1 fuer a negative number.")
            self._sign = value[0]
            wenn value[2] == 'F':
                # infinity: value[1] is ignored
                self._int = '0'
                self._exp = value[2]
                self._is_special = True
            sonst:
                # process and validate the digits in value[1]
                digits = []
                fuer digit in value[1]:
                    wenn isinstance(digit, int) and 0 <= digit <= 9:
                        # skip leading zeros
                        wenn digits or digit != 0:
                            digits.append(digit)
                    sonst:
                        raise ValueError("The second value in the tuple must "
                                         "be composed of integers in the range "
                                         "0 through 9.")
                wenn value[2] in ('n', 'N'):
                    # NaN: digits form the diagnostic
                    self._int = ''.join(map(str, digits))
                    self._exp = value[2]
                    self._is_special = True
                sowenn isinstance(value[2], int):
                    # finite number: digits give the coefficient
                    self._int = ''.join(map(str, digits or [0]))
                    self._exp = value[2]
                    self._is_special = False
                sonst:
                    raise ValueError("The third value in the tuple must "
                                     "be an integer, or one of the "
                                     "strings 'F', 'n', 'N'.")
            return self

        wenn isinstance(value, float):
            wenn context is None:
                context = getcontext()
            context._raise_error(FloatOperation,
                "strict semantics fuer mixing floats and Decimals are "
                "enabled")
            value = Decimal.from_float(value)
            self._exp  = value._exp
            self._sign = value._sign
            self._int  = value._int
            self._is_special  = value._is_special
            return self

        raise TypeError("Cannot convert %r to Decimal" % value)

    @classmethod
    def from_number(cls, number):
        """Converts a real number to a decimal number, exactly.

        >>> Decimal.from_number(314)              # int
        Decimal('314')
        >>> Decimal.from_number(0.1)              # float
        Decimal('0.1000000000000000055511151231257827021181583404541015625')
        >>> Decimal.from_number(Decimal('3.14'))  # another decimal instance
        Decimal('3.14')
        """
        wenn isinstance(number, (int, Decimal, float)):
            return cls(number)
        raise TypeError("Cannot convert %r to Decimal" % number)

    @classmethod
    def from_float(cls, f):
        """Converts a float to a decimal number, exactly.

        Note that Decimal.from_float(0.1) is not the same as Decimal('0.1').
        Since 0.1 is not exactly representable in binary floating point, the
        value is stored as the nearest representable value which is
        0x1.999999999999ap-4.  The exact equivalent of the value in decimal
        is 0.1000000000000000055511151231257827021181583404541015625.

        >>> Decimal.from_float(0.1)
        Decimal('0.1000000000000000055511151231257827021181583404541015625')
        >>> Decimal.from_float(float('nan'))
        Decimal('NaN')
        >>> Decimal.from_float(float('inf'))
        Decimal('Infinity')
        >>> Decimal.from_float(-float('inf'))
        Decimal('-Infinity')
        >>> Decimal.from_float(-0.0)
        Decimal('-0')

        """
        wenn isinstance(f, int):                # handle integer inputs
            sign = 0 wenn f >= 0 sonst 1
            k = 0
            coeff = str(abs(f))
        sowenn isinstance(f, float):
            wenn _math.isinf(f) or _math.isnan(f):
                return cls(repr(f))
            wenn _math.copysign(1.0, f) == 1.0:
                sign = 0
            sonst:
                sign = 1
            n, d = abs(f).as_integer_ratio()
            k = d.bit_length() - 1
            coeff = str(n*5**k)
        sonst:
            raise TypeError("argument must be int or float.")

        result = _dec_from_triple(sign, coeff, -k)
        wenn cls is Decimal:
            return result
        sonst:
            return cls(result)

    def _isnan(self):
        """Returns whether the number is not actually one.

        0 wenn a number
        1 wenn NaN
        2 wenn sNaN
        """
        wenn self._is_special:
            exp = self._exp
            wenn exp == 'n':
                return 1
            sowenn exp == 'N':
                return 2
        return 0

    def _isinfinity(self):
        """Returns whether the number is infinite

        0 wenn finite or not a number
        1 wenn +INF
        -1 wenn -INF
        """
        wenn self._exp == 'F':
            wenn self._sign:
                return -1
            return 1
        return 0

    def _check_nans(self, other=None, context=None):
        """Returns whether the number is not actually one.

        wenn self, other are sNaN, signal
        wenn self, other are NaN return nan
        return 0

        Done before operations.
        """

        self_is_nan = self._isnan()
        wenn other is None:
            other_is_nan = False
        sonst:
            other_is_nan = other._isnan()

        wenn self_is_nan or other_is_nan:
            wenn context is None:
                context = getcontext()

            wenn self_is_nan == 2:
                return context._raise_error(InvalidOperation, 'sNaN',
                                        self)
            wenn other_is_nan == 2:
                return context._raise_error(InvalidOperation, 'sNaN',
                                        other)
            wenn self_is_nan:
                return self._fix_nan(context)

            return other._fix_nan(context)
        return 0

    def _compare_check_nans(self, other, context):
        """Version of _check_nans used fuer the signaling comparisons
        compare_signal, __le__, __lt__, __ge__, __gt__.

        Signal InvalidOperation wenn either self or other is a (quiet
        or signaling) NaN.  Signaling NaNs take precedence over quiet
        NaNs.

        Return 0 wenn neither operand is a NaN.

        """
        wenn context is None:
            context = getcontext()

        wenn self._is_special or other._is_special:
            wenn self.is_snan():
                return context._raise_error(InvalidOperation,
                                            'comparison involving sNaN',
                                            self)
            sowenn other.is_snan():
                return context._raise_error(InvalidOperation,
                                            'comparison involving sNaN',
                                            other)
            sowenn self.is_qnan():
                return context._raise_error(InvalidOperation,
                                            'comparison involving NaN',
                                            self)
            sowenn other.is_qnan():
                return context._raise_error(InvalidOperation,
                                            'comparison involving NaN',
                                            other)
        return 0

    def __bool__(self):
        """Return True wenn self is nonzero; otherwise return False.

        NaNs and infinities are considered nonzero.
        """
        return self._is_special or self._int != '0'

    def _cmp(self, other):
        """Compare the two non-NaN decimal instances self and other.

        Returns -1 wenn self < other, 0 wenn self == other and 1
        wenn self > other.  This routine is fuer internal use only."""

        wenn self._is_special or other._is_special:
            self_inf = self._isinfinity()
            other_inf = other._isinfinity()
            wenn self_inf == other_inf:
                return 0
            sowenn self_inf < other_inf:
                return -1
            sonst:
                return 1

        # check fuer zeros;  Decimal('0') == Decimal('-0')
        wenn not self:
            wenn not other:
                return 0
            sonst:
                return -((-1)**other._sign)
        wenn not other:
            return (-1)**self._sign

        # If different signs, neg one is less
        wenn other._sign < self._sign:
            return -1
        wenn self._sign < other._sign:
            return 1

        self_adjusted = self.adjusted()
        other_adjusted = other.adjusted()
        wenn self_adjusted == other_adjusted:
            self_padded = self._int + '0'*(self._exp - other._exp)
            other_padded = other._int + '0'*(other._exp - self._exp)
            wenn self_padded == other_padded:
                return 0
            sowenn self_padded < other_padded:
                return -(-1)**self._sign
            sonst:
                return (-1)**self._sign
        sowenn self_adjusted > other_adjusted:
            return (-1)**self._sign
        sonst: # self_adjusted < other_adjusted
            return -((-1)**self._sign)

    # Note: The Decimal standard doesn't cover rich comparisons for
    # Decimals.  In particular, the specification is silent on the
    # subject of what should happen fuer a comparison involving a NaN.
    # We take the following approach:
    #
    #   == comparisons involving a quiet NaN always return False
    #   != comparisons involving a quiet NaN always return True
    #   == or != comparisons involving a signaling NaN signal
    #      InvalidOperation, and return False or True as above wenn the
    #      InvalidOperation is not trapped.
    #   <, >, <= and >= comparisons involving a (quiet or signaling)
    #      NaN signal InvalidOperation, and return False wenn the
    #      InvalidOperation is not trapped.
    #
    # This behavior is designed to conform as closely as possible to
    # that specified by IEEE 754.

    def __eq__(self, other, context=None):
        self, other = _convert_for_comparison(self, other, equality_op=True)
        wenn other is NotImplemented:
            return other
        wenn self._check_nans(other, context):
            return False
        return self._cmp(other) == 0

    def __lt__(self, other, context=None):
        self, other = _convert_for_comparison(self, other)
        wenn other is NotImplemented:
            return other
        ans = self._compare_check_nans(other, context)
        wenn ans:
            return False
        return self._cmp(other) < 0

    def __le__(self, other, context=None):
        self, other = _convert_for_comparison(self, other)
        wenn other is NotImplemented:
            return other
        ans = self._compare_check_nans(other, context)
        wenn ans:
            return False
        return self._cmp(other) <= 0

    def __gt__(self, other, context=None):
        self, other = _convert_for_comparison(self, other)
        wenn other is NotImplemented:
            return other
        ans = self._compare_check_nans(other, context)
        wenn ans:
            return False
        return self._cmp(other) > 0

    def __ge__(self, other, context=None):
        self, other = _convert_for_comparison(self, other)
        wenn other is NotImplemented:
            return other
        ans = self._compare_check_nans(other, context)
        wenn ans:
            return False
        return self._cmp(other) >= 0

    def compare(self, other, context=None):
        """Compare self to other.  Return a decimal value:

        a or b is a NaN ==> Decimal('NaN')
        a < b           ==> Decimal('-1')
        a == b          ==> Decimal('0')
        a > b           ==> Decimal('1')
        """
        other = _convert_other(other, raiseit=True)

        # Compare(NaN, NaN) = NaN
        wenn (self._is_special or other and other._is_special):
            ans = self._check_nans(other, context)
            wenn ans:
                return ans

        return Decimal(self._cmp(other))

    def __hash__(self):
        """x.__hash__() <==> hash(x)"""

        # In order to make sure that the hash of a Decimal instance
        # agrees with the hash of a numerically equal integer, float
        # or Fraction, we follow the rules fuer numeric hashes outlined
        # in the documentation.  (See library docs, 'Built-in Types').
        wenn self._is_special:
            wenn self.is_snan():
                raise TypeError('Cannot hash a signaling NaN value.')
            sowenn self.is_nan():
                return object.__hash__(self)
            sonst:
                wenn self._sign:
                    return -_PyHASH_INF
                sonst:
                    return _PyHASH_INF

        wenn self._exp >= 0:
            exp_hash = pow(10, self._exp, _PyHASH_MODULUS)
        sonst:
            exp_hash = pow(_PyHASH_10INV, -self._exp, _PyHASH_MODULUS)
        hash_ = int(self._int) * exp_hash % _PyHASH_MODULUS
        ans = hash_ wenn self >= 0 sonst -hash_
        return -2 wenn ans == -1 sonst ans

    def as_tuple(self):
        """Represents the number as a triple tuple.

        To show the internals exactly as they are.
        """
        return DecimalTuple(self._sign, tuple(map(int, self._int)), self._exp)

    def as_integer_ratio(self):
        """Express a finite Decimal instance in the form n / d.

        Returns a pair (n, d) of integers.  When called on an infinity
        or NaN, raises OverflowError or ValueError respectively.

        >>> Decimal('3.14').as_integer_ratio()
        (157, 50)
        >>> Decimal('-123e5').as_integer_ratio()
        (-12300000, 1)
        >>> Decimal('0.00').as_integer_ratio()
        (0, 1)

        """
        wenn self._is_special:
            wenn self.is_nan():
                raise ValueError("cannot convert NaN to integer ratio")
            sonst:
                raise OverflowError("cannot convert Infinity to integer ratio")

        wenn not self:
            return 0, 1

        # Find n, d in lowest terms such that abs(self) == n / d;
        # we'll deal with the sign later.
        n = int(self._int)
        wenn self._exp >= 0:
            # self is an integer.
            n, d = n * 10**self._exp, 1
        sonst:
            # Find d2, d5 such that abs(self) = n / (2**d2 * 5**d5).
            d5 = -self._exp
            while d5 > 0 and n % 5 == 0:
                n //= 5
                d5 -= 1

            # (n & -n).bit_length() - 1 counts trailing zeros in binary
            # representation of n (provided n is nonzero).
            d2 = -self._exp
            shift2 = min((n & -n).bit_length() - 1, d2)
            wenn shift2:
                n >>= shift2
                d2 -= shift2

            d = 5**d5 << d2

        wenn self._sign:
            n = -n
        return n, d

    def __repr__(self):
        """Represents the number as an instance of Decimal."""
        # Invariant:  eval(repr(d)) == d
        return "Decimal('%s')" % str(self)

    def __str__(self, eng=False, context=None):
        """Return string representation of the number in scientific notation.

        Captures all of the information in the underlying representation.
        """

        sign = ['', '-'][self._sign]
        wenn self._is_special:
            wenn self._exp == 'F':
                return sign + 'Infinity'
            sowenn self._exp == 'n':
                return sign + 'NaN' + self._int
            sonst: # self._exp == 'N'
                return sign + 'sNaN' + self._int

        # number of digits of self._int to left of decimal point
        leftdigits = self._exp + len(self._int)

        # dotplace is number of digits of self._int to the left of the
        # decimal point in the mantissa of the output string (that is,
        # after adjusting the exponent)
        wenn self._exp <= 0 and leftdigits > -6:
            # no exponent required
            dotplace = leftdigits
        sowenn not eng:
            # usual scientific notation: 1 digit on left of the point
            dotplace = 1
        sowenn self._int == '0':
            # engineering notation, zero
            dotplace = (leftdigits + 1) % 3 - 1
        sonst:
            # engineering notation, nonzero
            dotplace = (leftdigits - 1) % 3 + 1

        wenn dotplace <= 0:
            intpart = '0'
            fracpart = '.' + '0'*(-dotplace) + self._int
        sowenn dotplace >= len(self._int):
            intpart = self._int+'0'*(dotplace-len(self._int))
            fracpart = ''
        sonst:
            intpart = self._int[:dotplace]
            fracpart = '.' + self._int[dotplace:]
        wenn leftdigits == dotplace:
            exp = ''
        sonst:
            wenn context is None:
                context = getcontext()
            exp = ['e', 'E'][context.capitals] + "%+d" % (leftdigits-dotplace)

        return sign + intpart + fracpart + exp

    def to_eng_string(self, context=None):
        """Convert to a string, using engineering notation wenn an exponent is needed.

        Engineering notation has an exponent which is a multiple of 3.  This
        can leave up to 3 digits to the left of the decimal place and may
        require the addition of either one or two trailing zeros.
        """
        return self.__str__(eng=True, context=context)

    def __neg__(self, context=None):
        """Returns a copy with the sign switched.

        Rounds, wenn it has reason.
        """
        wenn self._is_special:
            ans = self._check_nans(context=context)
            wenn ans:
                return ans

        wenn context is None:
            context = getcontext()

        wenn not self and context.rounding != ROUND_FLOOR:
            # -Decimal('0') is Decimal('0'), not Decimal('-0'), except
            # in ROUND_FLOOR rounding mode.
            ans = self.copy_abs()
        sonst:
            ans = self.copy_negate()

        return ans._fix(context)

    def __pos__(self, context=None):
        """Returns a copy, unless it is a sNaN.

        Rounds the number (if more than precision digits)
        """
        wenn self._is_special:
            ans = self._check_nans(context=context)
            wenn ans:
                return ans

        wenn context is None:
            context = getcontext()

        wenn not self and context.rounding != ROUND_FLOOR:
            # + (-0) = 0, except in ROUND_FLOOR rounding mode.
            ans = self.copy_abs()
        sonst:
            ans = Decimal(self)

        return ans._fix(context)

    def __abs__(self, round=True, context=None):
        """Returns the absolute value of self.

        If the keyword argument 'round' is false, do not round.  The
        expression self.__abs__(round=False) is equivalent to
        self.copy_abs().
        """
        wenn not round:
            return self.copy_abs()

        wenn self._is_special:
            ans = self._check_nans(context=context)
            wenn ans:
                return ans

        wenn self._sign:
            ans = self.__neg__(context=context)
        sonst:
            ans = self.__pos__(context=context)

        return ans

    def __add__(self, other, context=None):
        """Returns self + other.

        -INF + INF (or the reverse) cause InvalidOperation errors.
        """
        other = _convert_other(other)
        wenn other is NotImplemented:
            return other

        wenn context is None:
            context = getcontext()

        wenn self._is_special or other._is_special:
            ans = self._check_nans(other, context)
            wenn ans:
                return ans

            wenn self._isinfinity():
                # If both INF, same sign => same as both, opposite => error.
                wenn self._sign != other._sign and other._isinfinity():
                    return context._raise_error(InvalidOperation, '-INF + INF')
                return Decimal(self)
            wenn other._isinfinity():
                return Decimal(other)  # Can't both be infinity here

        exp = min(self._exp, other._exp)
        negativezero = 0
        wenn context.rounding == ROUND_FLOOR and self._sign != other._sign:
            # If the answer is 0, the sign should be negative, in this case.
            negativezero = 1

        wenn not self and not other:
            sign = min(self._sign, other._sign)
            wenn negativezero:
                sign = 1
            ans = _dec_from_triple(sign, '0', exp)
            ans = ans._fix(context)
            return ans
        wenn not self:
            exp = max(exp, other._exp - context.prec-1)
            ans = other._rescale(exp, context.rounding)
            ans = ans._fix(context)
            return ans
        wenn not other:
            exp = max(exp, self._exp - context.prec-1)
            ans = self._rescale(exp, context.rounding)
            ans = ans._fix(context)
            return ans

        op1 = _WorkRep(self)
        op2 = _WorkRep(other)
        op1, op2 = _normalize(op1, op2, context.prec)

        result = _WorkRep()
        wenn op1.sign != op2.sign:
            # Equal and opposite
            wenn op1.int == op2.int:
                ans = _dec_from_triple(negativezero, '0', exp)
                ans = ans._fix(context)
                return ans
            wenn op1.int < op2.int:
                op1, op2 = op2, op1
                # OK, now abs(op1) > abs(op2)
            wenn op1.sign == 1:
                result.sign = 1
                op1.sign, op2.sign = op2.sign, op1.sign
            sonst:
                result.sign = 0
                # So we know the sign, and op1 > 0.
        sowenn op1.sign == 1:
            result.sign = 1
            op1.sign, op2.sign = (0, 0)
        sonst:
            result.sign = 0
        # Now, op1 > abs(op2) > 0

        wenn op2.sign == 0:
            result.int = op1.int + op2.int
        sonst:
            result.int = op1.int - op2.int

        result.exp = op1.exp
        ans = Decimal(result)
        ans = ans._fix(context)
        return ans

    __radd__ = __add__

    def __sub__(self, other, context=None):
        """Return self - other"""
        other = _convert_other(other)
        wenn other is NotImplemented:
            return other

        wenn self._is_special or other._is_special:
            ans = self._check_nans(other, context=context)
            wenn ans:
                return ans

        # self - other is computed as self + other.copy_negate()
        return self.__add__(other.copy_negate(), context=context)

    def __rsub__(self, other, context=None):
        """Return other - self"""
        other = _convert_other(other)
        wenn other is NotImplemented:
            return other

        return other.__sub__(self, context=context)

    def __mul__(self, other, context=None):
        """Return self * other.

        (+-) INF * 0 (or its reverse) raise InvalidOperation.
        """
        other = _convert_other(other)
        wenn other is NotImplemented:
            return other

        wenn context is None:
            context = getcontext()

        resultsign = self._sign ^ other._sign

        wenn self._is_special or other._is_special:
            ans = self._check_nans(other, context)
            wenn ans:
                return ans

            wenn self._isinfinity():
                wenn not other:
                    return context._raise_error(InvalidOperation, '(+-)INF * 0')
                return _SignedInfinity[resultsign]

            wenn other._isinfinity():
                wenn not self:
                    return context._raise_error(InvalidOperation, '0 * (+-)INF')
                return _SignedInfinity[resultsign]

        resultexp = self._exp + other._exp

        # Special case fuer multiplying by zero
        wenn not self or not other:
            ans = _dec_from_triple(resultsign, '0', resultexp)
            # Fixing in case the exponent is out of bounds
            ans = ans._fix(context)
            return ans

        # Special case fuer multiplying by power of 10
        wenn self._int == '1':
            ans = _dec_from_triple(resultsign, other._int, resultexp)
            ans = ans._fix(context)
            return ans
        wenn other._int == '1':
            ans = _dec_from_triple(resultsign, self._int, resultexp)
            ans = ans._fix(context)
            return ans

        op1 = _WorkRep(self)
        op2 = _WorkRep(other)

        ans = _dec_from_triple(resultsign, str(op1.int * op2.int), resultexp)
        ans = ans._fix(context)

        return ans
    __rmul__ = __mul__

    def __truediv__(self, other, context=None):
        """Return self / other."""
        other = _convert_other(other)
        wenn other is NotImplemented:
            return NotImplemented

        wenn context is None:
            context = getcontext()

        sign = self._sign ^ other._sign

        wenn self._is_special or other._is_special:
            ans = self._check_nans(other, context)
            wenn ans:
                return ans

            wenn self._isinfinity() and other._isinfinity():
                return context._raise_error(InvalidOperation, '(+-)INF/(+-)INF')

            wenn self._isinfinity():
                return _SignedInfinity[sign]

            wenn other._isinfinity():
                context._raise_error(Clamped, 'Division by infinity')
                return _dec_from_triple(sign, '0', context.Etiny())

        # Special cases fuer zeroes
        wenn not other:
            wenn not self:
                return context._raise_error(DivisionUndefined, '0 / 0')
            return context._raise_error(DivisionByZero, 'x / 0', sign)

        wenn not self:
            exp = self._exp - other._exp
            coeff = 0
        sonst:
            # OK, so neither = 0, INF or NaN
            shift = len(other._int) - len(self._int) + context.prec + 1
            exp = self._exp - other._exp - shift
            op1 = _WorkRep(self)
            op2 = _WorkRep(other)
            wenn shift >= 0:
                coeff, remainder = divmod(op1.int * 10**shift, op2.int)
            sonst:
                coeff, remainder = divmod(op1.int, op2.int * 10**-shift)
            wenn remainder:
                # result is not exact; adjust to ensure correct rounding
                wenn coeff % 5 == 0:
                    coeff += 1
            sonst:
                # result is exact; get as close to ideal exponent as possible
                ideal_exp = self._exp - other._exp
                while exp < ideal_exp and coeff % 10 == 0:
                    coeff //= 10
                    exp += 1

        ans = _dec_from_triple(sign, str(coeff), exp)
        return ans._fix(context)

    def _divide(self, other, context):
        """Return (self // other, self % other), to context.prec precision.

        Assumes that neither self nor other is a NaN, that self is not
        infinite and that other is nonzero.
        """
        sign = self._sign ^ other._sign
        wenn other._isinfinity():
            ideal_exp = self._exp
        sonst:
            ideal_exp = min(self._exp, other._exp)

        expdiff = self.adjusted() - other.adjusted()
        wenn not self or other._isinfinity() or expdiff <= -2:
            return (_dec_from_triple(sign, '0', 0),
                    self._rescale(ideal_exp, context.rounding))
        wenn expdiff <= context.prec:
            op1 = _WorkRep(self)
            op2 = _WorkRep(other)
            wenn op1.exp >= op2.exp:
                op1.int *= 10**(op1.exp - op2.exp)
            sonst:
                op2.int *= 10**(op2.exp - op1.exp)
            q, r = divmod(op1.int, op2.int)
            wenn q < 10**context.prec:
                return (_dec_from_triple(sign, str(q), 0),
                        _dec_from_triple(self._sign, str(r), ideal_exp))

        # Here the quotient is too large to be representable
        ans = context._raise_error(DivisionImpossible,
                                   'quotient too large in //, % or divmod')
        return ans, ans

    def __rtruediv__(self, other, context=None):
        """Swaps self/other and returns __truediv__."""
        other = _convert_other(other)
        wenn other is NotImplemented:
            return other
        return other.__truediv__(self, context=context)

    def __divmod__(self, other, context=None):
        """
        Return (self // other, self % other)
        """
        other = _convert_other(other)
        wenn other is NotImplemented:
            return other

        wenn context is None:
            context = getcontext()

        ans = self._check_nans(other, context)
        wenn ans:
            return (ans, ans)

        sign = self._sign ^ other._sign
        wenn self._isinfinity():
            wenn other._isinfinity():
                ans = context._raise_error(InvalidOperation, 'divmod(INF, INF)')
                return ans, ans
            sonst:
                return (_SignedInfinity[sign],
                        context._raise_error(InvalidOperation, 'INF % x'))

        wenn not other:
            wenn not self:
                ans = context._raise_error(DivisionUndefined, 'divmod(0, 0)')
                return ans, ans
            sonst:
                return (context._raise_error(DivisionByZero, 'x // 0', sign),
                        context._raise_error(InvalidOperation, 'x % 0'))

        quotient, remainder = self._divide(other, context)
        remainder = remainder._fix(context)
        return quotient, remainder

    def __rdivmod__(self, other, context=None):
        """Swaps self/other and returns __divmod__."""
        other = _convert_other(other)
        wenn other is NotImplemented:
            return other
        return other.__divmod__(self, context=context)

    def __mod__(self, other, context=None):
        """
        self % other
        """
        other = _convert_other(other)
        wenn other is NotImplemented:
            return other

        wenn context is None:
            context = getcontext()

        ans = self._check_nans(other, context)
        wenn ans:
            return ans

        wenn self._isinfinity():
            return context._raise_error(InvalidOperation, 'INF % x')
        sowenn not other:
            wenn self:
                return context._raise_error(InvalidOperation, 'x % 0')
            sonst:
                return context._raise_error(DivisionUndefined, '0 % 0')

        remainder = self._divide(other, context)[1]
        remainder = remainder._fix(context)
        return remainder

    def __rmod__(self, other, context=None):
        """Swaps self/other and returns __mod__."""
        other = _convert_other(other)
        wenn other is NotImplemented:
            return other
        return other.__mod__(self, context=context)

    def remainder_near(self, other, context=None):
        """
        Remainder nearest to 0-  abs(remainder-near) <= other/2
        """
        wenn context is None:
            context = getcontext()

        other = _convert_other(other, raiseit=True)

        ans = self._check_nans(other, context)
        wenn ans:
            return ans

        # self == +/-infinity -> InvalidOperation
        wenn self._isinfinity():
            return context._raise_error(InvalidOperation,
                                        'remainder_near(infinity, x)')

        # other == 0 -> either InvalidOperation or DivisionUndefined
        wenn not other:
            wenn self:
                return context._raise_error(InvalidOperation,
                                            'remainder_near(x, 0)')
            sonst:
                return context._raise_error(DivisionUndefined,
                                            'remainder_near(0, 0)')

        # other = +/-infinity -> remainder = self
        wenn other._isinfinity():
            ans = Decimal(self)
            return ans._fix(context)

        # self = 0 -> remainder = self, with ideal exponent
        ideal_exponent = min(self._exp, other._exp)
        wenn not self:
            ans = _dec_from_triple(self._sign, '0', ideal_exponent)
            return ans._fix(context)

        # catch most cases of large or small quotient
        expdiff = self.adjusted() - other.adjusted()
        wenn expdiff >= context.prec + 1:
            # expdiff >= prec+1 => abs(self/other) > 10**prec
            return context._raise_error(DivisionImpossible)
        wenn expdiff <= -2:
            # expdiff <= -2 => abs(self/other) < 0.1
            ans = self._rescale(ideal_exponent, context.rounding)
            return ans._fix(context)

        # adjust both arguments to have the same exponent, then divide
        op1 = _WorkRep(self)
        op2 = _WorkRep(other)
        wenn op1.exp >= op2.exp:
            op1.int *= 10**(op1.exp - op2.exp)
        sonst:
            op2.int *= 10**(op2.exp - op1.exp)
        q, r = divmod(op1.int, op2.int)
        # remainder is r*10**ideal_exponent; other is +/-op2.int *
        # 10**ideal_exponent.   Apply correction to ensure that
        # abs(remainder) <= abs(other)/2
        wenn 2*r + (q&1) > op2.int:
            r -= op2.int
            q += 1

        wenn q >= 10**context.prec:
            return context._raise_error(DivisionImpossible)

        # result has same sign as self unless r is negative
        sign = self._sign
        wenn r < 0:
            sign = 1-sign
            r = -r

        ans = _dec_from_triple(sign, str(r), ideal_exponent)
        return ans._fix(context)

    def __floordiv__(self, other, context=None):
        """self // other"""
        other = _convert_other(other)
        wenn other is NotImplemented:
            return other

        wenn context is None:
            context = getcontext()

        ans = self._check_nans(other, context)
        wenn ans:
            return ans

        wenn self._isinfinity():
            wenn other._isinfinity():
                return context._raise_error(InvalidOperation, 'INF // INF')
            sonst:
                return _SignedInfinity[self._sign ^ other._sign]

        wenn not other:
            wenn self:
                return context._raise_error(DivisionByZero, 'x // 0',
                                            self._sign ^ other._sign)
            sonst:
                return context._raise_error(DivisionUndefined, '0 // 0')

        return self._divide(other, context)[0]

    def __rfloordiv__(self, other, context=None):
        """Swaps self/other and returns __floordiv__."""
        other = _convert_other(other)
        wenn other is NotImplemented:
            return other
        return other.__floordiv__(self, context=context)

    def __float__(self):
        """Float representation."""
        wenn self._isnan():
            wenn self.is_snan():
                raise ValueError("Cannot convert signaling NaN to float")
            s = "-nan" wenn self._sign sonst "nan"
        sonst:
            s = str(self)
        return float(s)

    def __int__(self):
        """Converts self to an int, truncating wenn necessary."""
        wenn self._is_special:
            wenn self._isnan():
                raise ValueError("Cannot convert NaN to integer")
            sowenn self._isinfinity():
                raise OverflowError("Cannot convert infinity to integer")
        s = (-1)**self._sign
        wenn self._exp >= 0:
            return s*int(self._int)*10**self._exp
        sonst:
            return s*int(self._int[:self._exp] or '0')

    __trunc__ = __int__

    @property
    def real(self):
        return self

    @property
    def imag(self):
        return Decimal(0)

    def conjugate(self):
        return self

    def __complex__(self):
        return complex(float(self))

    def _fix_nan(self, context):
        """Decapitate the payload of a NaN to fit the context"""
        payload = self._int

        # maximum length of payload is precision wenn clamp=0,
        # precision-1 wenn clamp=1.
        max_payload_len = context.prec - context.clamp
        wenn len(payload) > max_payload_len:
            payload = payload[len(payload)-max_payload_len:].lstrip('0')
            return _dec_from_triple(self._sign, payload, self._exp, True)
        return Decimal(self)

    def _fix(self, context):
        """Round wenn it is necessary to keep self within prec precision.

        Rounds and fixes the exponent.  Does not raise on a sNaN.

        Arguments:
        self - Decimal instance
        context - context used.
        """

        wenn self._is_special:
            wenn self._isnan():
                # decapitate payload wenn necessary
                return self._fix_nan(context)
            sonst:
                # self is +/-Infinity; return unaltered
                return Decimal(self)

        # wenn self is zero then exponent should be between Etiny and
        # Emax wenn clamp==0, and between Etiny and Etop wenn clamp==1.
        Etiny = context.Etiny()
        Etop = context.Etop()
        wenn not self:
            exp_max = [context.Emax, Etop][context.clamp]
            new_exp = min(max(self._exp, Etiny), exp_max)
            wenn new_exp != self._exp:
                context._raise_error(Clamped)
                return _dec_from_triple(self._sign, '0', new_exp)
            sonst:
                return Decimal(self)

        # exp_min is the smallest allowable exponent of the result,
        # equal to max(self.adjusted()-context.prec+1, Etiny)
        exp_min = len(self._int) + self._exp - context.prec
        wenn exp_min > Etop:
            # overflow: exp_min > Etop iff self.adjusted() > Emax
            ans = context._raise_error(Overflow, 'above Emax', self._sign)
            context._raise_error(Inexact)
            context._raise_error(Rounded)
            return ans

        self_is_subnormal = exp_min < Etiny
        wenn self_is_subnormal:
            exp_min = Etiny

        # round wenn self has too many digits
        wenn self._exp < exp_min:
            digits = len(self._int) + self._exp - exp_min
            wenn digits < 0:
                self = _dec_from_triple(self._sign, '1', exp_min-1)
                digits = 0
            rounding_method = self._pick_rounding_function[context.rounding]
            changed = rounding_method(self, digits)
            coeff = self._int[:digits] or '0'
            wenn changed > 0:
                coeff = str(int(coeff)+1)
                wenn len(coeff) > context.prec:
                    coeff = coeff[:-1]
                    exp_min += 1

            # check whether the rounding pushed the exponent out of range
            wenn exp_min > Etop:
                ans = context._raise_error(Overflow, 'above Emax', self._sign)
            sonst:
                ans = _dec_from_triple(self._sign, coeff, exp_min)

            # raise the appropriate signals, taking care to respect
            # the precedence described in the specification
            wenn changed and self_is_subnormal:
                context._raise_error(Underflow)
            wenn self_is_subnormal:
                context._raise_error(Subnormal)
            wenn changed:
                context._raise_error(Inexact)
            context._raise_error(Rounded)
            wenn not ans:
                # raise Clamped on underflow to 0
                context._raise_error(Clamped)
            return ans

        wenn self_is_subnormal:
            context._raise_error(Subnormal)

        # fold down wenn clamp == 1 and self has too few digits
        wenn context.clamp == 1 and self._exp > Etop:
            context._raise_error(Clamped)
            self_padded = self._int + '0'*(self._exp - Etop)
            return _dec_from_triple(self._sign, self_padded, Etop)

        # here self was representable to begin with; return unchanged
        return Decimal(self)

    # fuer each of the rounding functions below:
    #   self is a finite, nonzero Decimal
    #   prec is an integer satisfying 0 <= prec < len(self._int)
    #
    # each function returns either -1, 0, or 1, as follows:
    #   1 indicates that self should be rounded up (away from zero)
    #   0 indicates that self should be truncated, and that all the
    #     digits to be truncated are zeros (so the value is unchanged)
    #  -1 indicates that there are nonzero digits to be truncated

    def _round_down(self, prec):
        """Also known as round-towards-0, truncate."""
        wenn _all_zeros(self._int, prec):
            return 0
        sonst:
            return -1

    def _round_up(self, prec):
        """Rounds away from 0."""
        return -self._round_down(prec)

    def _round_half_up(self, prec):
        """Rounds 5 up (away from 0)"""
        wenn self._int[prec] in '56789':
            return 1
        sowenn _all_zeros(self._int, prec):
            return 0
        sonst:
            return -1

    def _round_half_down(self, prec):
        """Round 5 down"""
        wenn _exact_half(self._int, prec):
            return -1
        sonst:
            return self._round_half_up(prec)

    def _round_half_even(self, prec):
        """Round 5 to even, rest to nearest."""
        wenn _exact_half(self._int, prec) and \
                (prec == 0 or self._int[prec-1] in '02468'):
            return -1
        sonst:
            return self._round_half_up(prec)

    def _round_ceiling(self, prec):
        """Rounds up (not away from 0 wenn negative.)"""
        wenn self._sign:
            return self._round_down(prec)
        sonst:
            return -self._round_down(prec)

    def _round_floor(self, prec):
        """Rounds down (not towards 0 wenn negative)"""
        wenn not self._sign:
            return self._round_down(prec)
        sonst:
            return -self._round_down(prec)

    def _round_05up(self, prec):
        """Round down unless digit prec-1 is 0 or 5."""
        wenn prec and self._int[prec-1] not in '05':
            return self._round_down(prec)
        sonst:
            return -self._round_down(prec)

    _pick_rounding_function = dict(
        ROUND_DOWN = _round_down,
        ROUND_UP = _round_up,
        ROUND_HALF_UP = _round_half_up,
        ROUND_HALF_DOWN = _round_half_down,
        ROUND_HALF_EVEN = _round_half_even,
        ROUND_CEILING = _round_ceiling,
        ROUND_FLOOR = _round_floor,
        ROUND_05UP = _round_05up,
    )

    def __round__(self, n=None):
        """Round self to the nearest integer, or to a given precision.

        If only one argument is supplied, round a finite Decimal
        instance self to the nearest integer.  If self is infinite or
        a NaN then a Python exception is raised.  If self is finite
        and lies exactly halfway between two integers then it is
        rounded to the integer with even last digit.

        >>> round(Decimal('123.456'))
        123
        >>> round(Decimal('-456.789'))
        -457
        >>> round(Decimal('-3.0'))
        -3
        >>> round(Decimal('2.5'))
        2
        >>> round(Decimal('3.5'))
        4
        >>> round(Decimal('Inf'))
        Traceback (most recent call last):
          ...
        OverflowError: cannot round an infinity
        >>> round(Decimal('NaN'))
        Traceback (most recent call last):
          ...
        ValueError: cannot round a NaN

        If a second argument n is supplied, self is rounded to n
        decimal places using the rounding mode fuer the current
        context.

        For an integer n, round(self, -n) is exactly equivalent to
        self.quantize(Decimal('1En')).

        >>> round(Decimal('123.456'), 0)
        Decimal('123')
        >>> round(Decimal('123.456'), 2)
        Decimal('123.46')
        >>> round(Decimal('123.456'), -2)
        Decimal('1E+2')
        >>> round(Decimal('-Infinity'), 37)
        Decimal('NaN')
        >>> round(Decimal('sNaN123'), 0)
        Decimal('NaN123')

        """
        wenn n is not None:
            # two-argument form: use the equivalent quantize call
            wenn not isinstance(n, int):
                raise TypeError('Second argument to round should be integral')
            exp = _dec_from_triple(0, '1', -n)
            return self.quantize(exp)

        # one-argument form
        wenn self._is_special:
            wenn self.is_nan():
                raise ValueError("cannot round a NaN")
            sonst:
                raise OverflowError("cannot round an infinity")
        return int(self._rescale(0, ROUND_HALF_EVEN))

    def __floor__(self):
        """Return the floor of self, as an integer.

        For a finite Decimal instance self, return the greatest
        integer n such that n <= self.  If self is infinite or a NaN
        then a Python exception is raised.

        """
        wenn self._is_special:
            wenn self.is_nan():
                raise ValueError("cannot round a NaN")
            sonst:
                raise OverflowError("cannot round an infinity")
        return int(self._rescale(0, ROUND_FLOOR))

    def __ceil__(self):
        """Return the ceiling of self, as an integer.

        For a finite Decimal instance self, return the least integer n
        such that n >= self.  If self is infinite or a NaN then a
        Python exception is raised.

        """
        wenn self._is_special:
            wenn self.is_nan():
                raise ValueError("cannot round a NaN")
            sonst:
                raise OverflowError("cannot round an infinity")
        return int(self._rescale(0, ROUND_CEILING))

    def fma(self, other, third, context=None):
        """Fused multiply-add.

        Returns self*other+third with no rounding of the intermediate
        product self*other.

        self and other are multiplied together, with no rounding of
        the result.  The third operand is then added to the result,
        and a single final rounding is performed.
        """

        other = _convert_other(other, raiseit=True)
        third = _convert_other(third, raiseit=True)

        # compute product; raise InvalidOperation wenn either operand is
        # a signaling NaN or wenn the product is zero times infinity.
        wenn self._is_special or other._is_special:
            wenn context is None:
                context = getcontext()
            wenn self._exp == 'N':
                return context._raise_error(InvalidOperation, 'sNaN', self)
            wenn other._exp == 'N':
                return context._raise_error(InvalidOperation, 'sNaN', other)
            wenn self._exp == 'n':
                product = self
            sowenn other._exp == 'n':
                product = other
            sowenn self._exp == 'F':
                wenn not other:
                    return context._raise_error(InvalidOperation,
                                                'INF * 0 in fma')
                product = _SignedInfinity[self._sign ^ other._sign]
            sowenn other._exp == 'F':
                wenn not self:
                    return context._raise_error(InvalidOperation,
                                                '0 * INF in fma')
                product = _SignedInfinity[self._sign ^ other._sign]
        sonst:
            product = _dec_from_triple(self._sign ^ other._sign,
                                       str(int(self._int) * int(other._int)),
                                       self._exp + other._exp)

        return product.__add__(third, context)

    def _power_modulo(self, other, modulo, context=None):
        """Three argument version of __pow__"""

        other = _convert_other(other)
        wenn other is NotImplemented:
            return other
        modulo = _convert_other(modulo)
        wenn modulo is NotImplemented:
            return modulo

        wenn context is None:
            context = getcontext()

        # deal with NaNs: wenn there are any sNaNs then first one wins,
        # (i.e. behaviour fuer NaNs is identical to that of fma)
        self_is_nan = self._isnan()
        other_is_nan = other._isnan()
        modulo_is_nan = modulo._isnan()
        wenn self_is_nan or other_is_nan or modulo_is_nan:
            wenn self_is_nan == 2:
                return context._raise_error(InvalidOperation, 'sNaN',
                                        self)
            wenn other_is_nan == 2:
                return context._raise_error(InvalidOperation, 'sNaN',
                                        other)
            wenn modulo_is_nan == 2:
                return context._raise_error(InvalidOperation, 'sNaN',
                                        modulo)
            wenn self_is_nan:
                return self._fix_nan(context)
            wenn other_is_nan:
                return other._fix_nan(context)
            return modulo._fix_nan(context)

        # check inputs: we apply same restrictions as Python's pow()
        wenn not (self._isinteger() and
                other._isinteger() and
                modulo._isinteger()):
            return context._raise_error(InvalidOperation,
                                        'pow() 3rd argument not allowed '
                                        'unless all arguments are integers')
        wenn other < 0:
            return context._raise_error(InvalidOperation,
                                        'pow() 2nd argument cannot be '
                                        'negative when 3rd argument specified')
        wenn not modulo:
            return context._raise_error(InvalidOperation,
                                        'pow() 3rd argument cannot be 0')

        # additional restriction fuer decimal: the modulus must be less
        # than 10**prec in absolute value
        wenn modulo.adjusted() >= context.prec:
            return context._raise_error(InvalidOperation,
                                        'insufficient precision: pow() 3rd '
                                        'argument must not have more than '
                                        'precision digits')

        # define 0**0 == NaN, fuer consistency with two-argument pow
        # (even though it hurts!)
        wenn not other and not self:
            return context._raise_error(InvalidOperation,
                                        'at least one of pow() 1st argument '
                                        'and 2nd argument must be nonzero; '
                                        '0**0 is not defined')

        # compute sign of result
        wenn other._iseven():
            sign = 0
        sonst:
            sign = self._sign

        # convert modulo to a Python integer, and self and other to
        # Decimal integers (i.e. force their exponents to be >= 0)
        modulo = abs(int(modulo))
        base = _WorkRep(self.to_integral_value())
        exponent = _WorkRep(other.to_integral_value())

        # compute result using integer pow()
        base = (base.int % modulo * pow(10, base.exp, modulo)) % modulo
        fuer i in range(exponent.exp):
            base = pow(base, 10, modulo)
        base = pow(base, exponent.int, modulo)

        return _dec_from_triple(sign, str(base), 0)

    def _power_exact(self, other, p):
        """Attempt to compute self**other exactly.

        Given Decimals self and other and an integer p, attempt to
        compute an exact result fuer the power self**other, with p
        digits of precision.  Return None wenn self**other is not
        exactly representable in p digits.

        Assumes that elimination of special cases has already been
        performed: self and other must both be nonspecial; self must
        be positive and not numerically equal to 1; other must be
        nonzero.  For efficiency, other._exp should not be too large,
        so that 10**abs(other._exp) is a feasible calculation."""

        # In the comments below, we write x fuer the value of self and y fuer the
        # value of other.  Write x = xc*10**xe and abs(y) = yc*10**ye, with xc
        # and yc positive integers not divisible by 10.

        # The main purpose of this method is to identify the *failure*
        # of x**y to be exactly representable with as little effort as
        # possible.  So we look fuer cheap and easy tests that
        # eliminate the possibility of x**y being exact.  Only wenn all
        # these tests are passed do we go on to actually compute x**y.

        # Here's the main idea.  Express y as a rational number m/n, with m and
        # n relatively prime and n>0.  Then fuer x**y to be exactly
        # representable (at *any* precision), xc must be the nth power of a
        # positive integer and xe must be divisible by n.  If y is negative
        # then additionally xc must be a power of either 2 or 5, hence a power
        # of 2**n or 5**n.
        #
        # There's a limit to how small |y| can be: wenn y=m/n as above
        # then:
        #
        #  (1) wenn xc != 1 then fuer the result to be representable we
        #      need xc**(1/n) >= 2, and hence also xc**|y| >= 2.  So
        #      wenn |y| <= 1/nbits(xc) then xc < 2**nbits(xc) <=
        #      2**(1/|y|), hence xc**|y| < 2 and the result is not
        #      representable.
        #
        #  (2) wenn xe != 0, |xe|*(1/n) >= 1, so |xe|*|y| >= 1.  Hence if
        #      |y| < 1/|xe| then the result is not representable.
        #
        # Note that since x is not equal to 1, at least one of (1) and
        # (2) must apply.  Now |y| < 1/nbits(xc) iff |yc|*nbits(xc) <
        # 10**-ye iff len(str(|yc|*nbits(xc)) <= -ye.
        #
        # There's also a limit to how large y can be, at least wenn it's
        # positive: the normalized result will have coefficient xc**y,
        # so wenn it's representable then xc**y < 10**p, and y <
        # p/log10(xc).  Hence wenn y*log10(xc) >= p then the result is
        # not exactly representable.

        # wenn len(str(abs(yc*xe)) <= -ye then abs(yc*xe) < 10**-ye,
        # so |y| < 1/xe and the result is not representable.
        # Similarly, len(str(abs(yc)*xc_bits)) <= -ye implies |y|
        # < 1/nbits(xc).

        x = _WorkRep(self)
        xc, xe = x.int, x.exp
        while xc % 10 == 0:
            xc //= 10
            xe += 1

        y = _WorkRep(other)
        yc, ye = y.int, y.exp
        while yc % 10 == 0:
            yc //= 10
            ye += 1

        # case where xc == 1: result is 10**(xe*y), with xe*y
        # required to be an integer
        wenn xc == 1:
            xe *= yc
            # result is now 10**(xe * 10**ye);  xe * 10**ye must be integral
            while xe % 10 == 0:
                xe //= 10
                ye += 1
            wenn ye < 0:
                return None
            exponent = xe * 10**ye
            wenn y.sign == 1:
                exponent = -exponent
            # wenn other is a nonnegative integer, use ideal exponent
            wenn other._isinteger() and other._sign == 0:
                ideal_exponent = self._exp*int(other)
                zeros = min(exponent-ideal_exponent, p-1)
            sonst:
                zeros = 0
            return _dec_from_triple(0, '1' + '0'*zeros, exponent-zeros)

        # case where y is negative: xc must be either a power
        # of 2 or a power of 5.
        wenn y.sign == 1:
            last_digit = xc % 10
            wenn last_digit in (2,4,6,8):
                # quick test fuer power of 2
                wenn xc & -xc != xc:
                    return None
                # now xc is a power of 2; e is its exponent
                e = _nbits(xc)-1

                # We now have:
                #
                #   x = 2**e * 10**xe, e > 0, and y < 0.
                #
                # The exact result is:
                #
                #   x**y = 5**(-e*y) * 10**(e*y + xe*y)
                #
                # provided that both e*y and xe*y are integers.  Note that if
                # 5**(-e*y) >= 10**p, then the result can't be expressed
                # exactly with p digits of precision.
                #
                # Using the above, we can guard against large values of ye.
                # 93/65 is an upper bound fuer log(10)/log(5), so if
                #
                #   ye >= len(str(93*p//65))
                #
                # then
                #
                #   -e*y >= -y >= 10**ye > 93*p/65 > p*log(10)/log(5),
                #
                # so 5**(-e*y) >= 10**p, and the coefficient of the result
                # can't be expressed in p digits.

                # emax >= largest e such that 5**e < 10**p.
                emax = p*93//65
                wenn ye >= len(str(emax)):
                    return None

                # Find -e*y and -xe*y; both must be integers
                e = _decimal_lshift_exact(e * yc, ye)
                xe = _decimal_lshift_exact(xe * yc, ye)
                wenn e is None or xe is None:
                    return None

                wenn e > emax:
                    return None
                xc = 5**e

            sowenn last_digit == 5:
                # e >= log_5(xc) wenn xc is a power of 5; we have
                # equality all the way up to xc=5**2658
                e = _nbits(xc)*28//65
                xc, remainder = divmod(5**e, xc)
                wenn remainder:
                    return None
                while xc % 5 == 0:
                    xc //= 5
                    e -= 1

                # Guard against large values of ye, using the same logic as in
                # the 'xc is a power of 2' branch.  10/3 is an upper bound for
                # log(10)/log(2).
                emax = p*10//3
                wenn ye >= len(str(emax)):
                    return None

                e = _decimal_lshift_exact(e * yc, ye)
                xe = _decimal_lshift_exact(xe * yc, ye)
                wenn e is None or xe is None:
                    return None

                wenn e > emax:
                    return None
                xc = 2**e
            sonst:
                return None

            # An exact power of 10 is representable, but can convert to a
            # string of any length. But an exact power of 10 shouldn't be
            # possible at this point.
            assert xc > 1, self
            assert xc % 10 != 0, self
            strxc = str(xc)
            wenn len(strxc) > p:
                return None
            xe = -e-xe
            return _dec_from_triple(0, strxc, xe)

        # now y is positive; find m and n such that y = m/n
        wenn ye >= 0:
            m, n = yc*10**ye, 1
        sonst:
            wenn xe != 0 and len(str(abs(yc*xe))) <= -ye:
                return None
            xc_bits = _nbits(xc)
            wenn len(str(abs(yc)*xc_bits)) <= -ye:
                return None
            m, n = yc, 10**(-ye)
            while m % 2 == n % 2 == 0:
                m //= 2
                n //= 2
            while m % 5 == n % 5 == 0:
                m //= 5
                n //= 5

        # compute nth root of xc*10**xe
        wenn n > 1:
            # wenn 1 < xc < 2**n then xc isn't an nth power
            wenn xc_bits <= n:
                return None

            xe, rem = divmod(xe, n)
            wenn rem != 0:
                return None

            # compute nth root of xc using Newton's method
            a = 1 << -(-_nbits(xc)//n) # initial estimate
            while True:
                q, r = divmod(xc, a**(n-1))
                wenn a <= q:
                    break
                sonst:
                    a = (a*(n-1) + q)//n
            wenn not (a == q and r == 0):
                return None
            xc = a

        # now xc*10**xe is the nth root of the original xc*10**xe
        # compute mth power of xc*10**xe

        # wenn m > p*100//_log10_lb(xc) then m > p/log10(xc), hence xc**m >
        # 10**p and the result is not representable.
        wenn xc > 1 and m > p*100//_log10_lb(xc):
            return None
        xc = xc**m
        xe *= m
        # An exact power of 10 is representable, but can convert to a string
        # of any length. But an exact power of 10 shouldn't be possible at
        # this point.
        assert xc > 1, self
        assert xc % 10 != 0, self
        str_xc = str(xc)
        wenn len(str_xc) > p:
            return None

        # by this point the result *is* exactly representable
        # adjust the exponent to get as close as possible to the ideal
        # exponent, wenn necessary
        wenn other._isinteger() and other._sign == 0:
            ideal_exponent = self._exp*int(other)
            zeros = min(xe-ideal_exponent, p-len(str_xc))
        sonst:
            zeros = 0
        return _dec_from_triple(0, str_xc+'0'*zeros, xe-zeros)

    def __pow__(self, other, modulo=None, context=None):
        """Return self ** other [ % modulo].

        With two arguments, compute self**other.

        With three arguments, compute (self**other) % modulo.  For the
        three argument form, the following restrictions on the
        arguments hold:

         - all three arguments must be integral
         - other must be nonnegative
         - either self or other (or both) must be nonzero
         - modulo must be nonzero and must have at most p digits,
           where p is the context precision.

        If any of these restrictions is violated the InvalidOperation
        flag is raised.

        The result of pow(self, other, modulo) is identical to the
        result that would be obtained by computing (self**other) %
        modulo with unbounded precision, but is computed more
        efficiently.  It is always exact.
        """

        wenn modulo is not None:
            return self._power_modulo(other, modulo, context)

        other = _convert_other(other)
        wenn other is NotImplemented:
            return other

        wenn context is None:
            context = getcontext()

        # either argument is a NaN => result is NaN
        ans = self._check_nans(other, context)
        wenn ans:
            return ans

        # 0**0 = NaN (!), x**0 = 1 fuer nonzero x (including +/-Infinity)
        wenn not other:
            wenn not self:
                return context._raise_error(InvalidOperation, '0 ** 0')
            sonst:
                return _One

        # result has sign 1 iff self._sign is 1 and other is an odd integer
        result_sign = 0
        wenn self._sign == 1:
            wenn other._isinteger():
                wenn not other._iseven():
                    result_sign = 1
            sonst:
                # -ve**noninteger = NaN
                # (-0)**noninteger = 0**noninteger
                wenn self:
                    return context._raise_error(InvalidOperation,
                        'x ** y with x negative and y not an integer')
            # negate self, without doing any unwanted rounding
            self = self.copy_negate()

        # 0**(+ve or Inf)= 0; 0**(-ve or -Inf) = Infinity
        wenn not self:
            wenn other._sign == 0:
                return _dec_from_triple(result_sign, '0', 0)
            sonst:
                return _SignedInfinity[result_sign]

        # Inf**(+ve or Inf) = Inf; Inf**(-ve or -Inf) = 0
        wenn self._isinfinity():
            wenn other._sign == 0:
                return _SignedInfinity[result_sign]
            sonst:
                return _dec_from_triple(result_sign, '0', 0)

        # 1**other = 1, but the choice of exponent and the flags
        # depend on the exponent of self, and on whether other is a
        # positive integer, a negative integer, or neither
        wenn self == _One:
            wenn other._isinteger():
                # exp = max(self._exp*max(int(other), 0),
                # 1-context.prec) but evaluating int(other) directly
                # is dangerous until we know other is small (other
                # could be 1e999999999)
                wenn other._sign == 1:
                    multiplier = 0
                sowenn other > context.prec:
                    multiplier = context.prec
                sonst:
                    multiplier = int(other)

                exp = self._exp * multiplier
                wenn exp < 1-context.prec:
                    exp = 1-context.prec
                    context._raise_error(Rounded)
            sonst:
                context._raise_error(Inexact)
                context._raise_error(Rounded)
                exp = 1-context.prec

            return _dec_from_triple(result_sign, '1'+'0'*-exp, exp)

        # compute adjusted exponent of self
        self_adj = self.adjusted()

        # self ** infinity is infinity wenn self > 1, 0 wenn self < 1
        # self ** -infinity is infinity wenn self < 1, 0 wenn self > 1
        wenn other._isinfinity():
            wenn (other._sign == 0) == (self_adj < 0):
                return _dec_from_triple(result_sign, '0', 0)
            sonst:
                return _SignedInfinity[result_sign]

        # from here on, the result always goes through the call
        # to _fix at the end of this function.
        ans = None
        exact = False

        # crude test to catch cases of extreme overflow/underflow.  If
        # log10(self)*other >= 10**bound and bound >= len(str(Emax))
        # then 10**bound >= 10**len(str(Emax)) >= Emax+1 and hence
        # self**other >= 10**(Emax+1), so overflow occurs.  The test
        # fuer underflow is similar.
        bound = self._log10_exp_bound() + other.adjusted()
        wenn (self_adj >= 0) == (other._sign == 0):
            # self > 1 and other +ve, or self < 1 and other -ve
            # possibility of overflow
            wenn bound >= len(str(context.Emax)):
                ans = _dec_from_triple(result_sign, '1', context.Emax+1)
        sonst:
            # self > 1 and other -ve, or self < 1 and other +ve
            # possibility of underflow to 0
            Etiny = context.Etiny()
            wenn bound >= len(str(-Etiny)):
                ans = _dec_from_triple(result_sign, '1', Etiny-1)

        # try fuer an exact result with precision +1
        wenn ans is None:
            ans = self._power_exact(other, context.prec + 1)
            wenn ans is not None:
                wenn result_sign == 1:
                    ans = _dec_from_triple(1, ans._int, ans._exp)
                exact = True

        # usual case: inexact result, x**y computed directly as exp(y*log(x))
        wenn ans is None:
            p = context.prec
            x = _WorkRep(self)
            xc, xe = x.int, x.exp
            y = _WorkRep(other)
            yc, ye = y.int, y.exp
            wenn y.sign == 1:
                yc = -yc

            # compute correctly rounded result:  start with precision +3,
            # then increase precision until result is unambiguously roundable
            extra = 3
            while True:
                coeff, exp = _dpower(xc, xe, yc, ye, p+extra)
                wenn coeff % (5*10**(len(str(coeff))-p-1)):
                    break
                extra += 3

            ans = _dec_from_triple(result_sign, str(coeff), exp)

        # unlike exp, ln and log10, the power function respects the
        # rounding mode; no need to switch to ROUND_HALF_EVEN here

        # There's a difficulty here when 'other' is not an integer and
        # the result is exact.  In this case, the specification
        # requires that the Inexact flag be raised (in spite of
        # exactness), but since the result is exact _fix won't do this
        # fuer us.  (Correspondingly, the Underflow signal should also
        # be raised fuer subnormal results.)  We can't directly raise
        # these signals either before or after calling _fix, since
        # that would violate the precedence fuer signals.  So we wrap
        # the ._fix call in a temporary context, and reraise
        # afterwards.
        wenn exact and not other._isinteger():
            # pad with zeros up to length context.prec+1 wenn necessary; this
            # ensures that the Rounded signal will be raised.
            wenn len(ans._int) <= context.prec:
                expdiff = context.prec + 1 - len(ans._int)
                ans = _dec_from_triple(ans._sign, ans._int+'0'*expdiff,
                                       ans._exp-expdiff)

            # create a copy of the current context, with cleared flags/traps
            newcontext = context.copy()
            newcontext.clear_flags()
            fuer exception in _signals:
                newcontext.traps[exception] = 0

            # round in the new context
            ans = ans._fix(newcontext)

            # raise Inexact, and wenn necessary, Underflow
            newcontext._raise_error(Inexact)
            wenn newcontext.flags[Subnormal]:
                newcontext._raise_error(Underflow)

            # propagate signals to the original context; _fix could
            # have raised any of Overflow, Underflow, Subnormal,
            # Inexact, Rounded, Clamped.  Overflow needs the correct
            # arguments.  Note that the order of the exceptions is
            # important here.
            wenn newcontext.flags[Overflow]:
                context._raise_error(Overflow, 'above Emax', ans._sign)
            fuer exception in Underflow, Subnormal, Inexact, Rounded, Clamped:
                wenn newcontext.flags[exception]:
                    context._raise_error(exception)

        sonst:
            ans = ans._fix(context)

        return ans

    def __rpow__(self, other, modulo=None, context=None):
        """Swaps self/other and returns __pow__."""
        other = _convert_other(other)
        wenn other is NotImplemented:
            return other
        return other.__pow__(self, modulo, context=context)

    def normalize(self, context=None):
        """Normalize- strip trailing 0s, change anything equal to 0 to 0e0"""

        wenn context is None:
            context = getcontext()

        wenn self._is_special:
            ans = self._check_nans(context=context)
            wenn ans:
                return ans

        dup = self._fix(context)
        wenn dup._isinfinity():
            return dup

        wenn not dup:
            return _dec_from_triple(dup._sign, '0', 0)
        exp_max = [context.Emax, context.Etop()][context.clamp]
        end = len(dup._int)
        exp = dup._exp
        while dup._int[end-1] == '0' and exp < exp_max:
            exp += 1
            end -= 1
        return _dec_from_triple(dup._sign, dup._int[:end], exp)

    def quantize(self, exp, rounding=None, context=None):
        """Quantize self so its exponent is the same as that of exp.

        Similar to self._rescale(exp._exp) but with error checking.
        """
        exp = _convert_other(exp, raiseit=True)

        wenn context is None:
            context = getcontext()
        wenn rounding is None:
            rounding = context.rounding

        wenn self._is_special or exp._is_special:
            ans = self._check_nans(exp, context)
            wenn ans:
                return ans

            wenn exp._isinfinity() or self._isinfinity():
                wenn exp._isinfinity() and self._isinfinity():
                    return Decimal(self)  # wenn both are inf, it is OK
                return context._raise_error(InvalidOperation,
                                        'quantize with one INF')

        # exp._exp should be between Etiny and Emax
        wenn not (context.Etiny() <= exp._exp <= context.Emax):
            return context._raise_error(InvalidOperation,
                   'target exponent out of bounds in quantize')

        wenn not self:
            ans = _dec_from_triple(self._sign, '0', exp._exp)
            return ans._fix(context)

        self_adjusted = self.adjusted()
        wenn self_adjusted > context.Emax:
            return context._raise_error(InvalidOperation,
                                        'exponent of quantize result too large fuer current context')
        wenn self_adjusted - exp._exp + 1 > context.prec:
            return context._raise_error(InvalidOperation,
                                        'quantize result has too many digits fuer current context')

        ans = self._rescale(exp._exp, rounding)
        wenn ans.adjusted() > context.Emax:
            return context._raise_error(InvalidOperation,
                                        'exponent of quantize result too large fuer current context')
        wenn len(ans._int) > context.prec:
            return context._raise_error(InvalidOperation,
                                        'quantize result has too many digits fuer current context')

        # raise appropriate flags
        wenn ans and ans.adjusted() < context.Emin:
            context._raise_error(Subnormal)
        wenn ans._exp > self._exp:
            wenn ans != self:
                context._raise_error(Inexact)
            context._raise_error(Rounded)

        # call to fix takes care of any necessary folddown, and
        # signals Clamped wenn necessary
        ans = ans._fix(context)
        return ans

    def same_quantum(self, other, context=None):
        """Return True wenn self and other have the same exponent; otherwise
        return False.

        If either operand is a special value, the following rules are used:
           * return True wenn both operands are infinities
           * return True wenn both operands are NaNs
           * otherwise, return False.
        """
        other = _convert_other(other, raiseit=True)
        wenn self._is_special or other._is_special:
            return (self.is_nan() and other.is_nan() or
                    self.is_infinite() and other.is_infinite())
        return self._exp == other._exp

    def _rescale(self, exp, rounding):
        """Rescale self so that the exponent is exp, either by padding with zeros
        or by truncating digits, using the given rounding mode.

        Specials are returned without change.  This operation is
        quiet: it raises no flags, and uses no information from the
        context.

        exp = exp to scale to (an integer)
        rounding = rounding mode
        """
        wenn self._is_special:
            return Decimal(self)
        wenn not self:
            return _dec_from_triple(self._sign, '0', exp)

        wenn self._exp >= exp:
            # pad answer with zeros wenn necessary
            return _dec_from_triple(self._sign,
                                        self._int + '0'*(self._exp - exp), exp)

        # too many digits; round and lose data.  If self.adjusted() <
        # exp-1, replace self by 10**(exp-1) before rounding
        digits = len(self._int) + self._exp - exp
        wenn digits < 0:
            self = _dec_from_triple(self._sign, '1', exp-1)
            digits = 0
        this_function = self._pick_rounding_function[rounding]
        changed = this_function(self, digits)
        coeff = self._int[:digits] or '0'
        wenn changed == 1:
            coeff = str(int(coeff)+1)
        return _dec_from_triple(self._sign, coeff, exp)

    def _round(self, places, rounding):
        """Round a nonzero, nonspecial Decimal to a fixed number of
        significant figures, using the given rounding mode.

        Infinities, NaNs and zeros are returned unaltered.

        This operation is quiet: it raises no flags, and uses no
        information from the context.

        """
        wenn places <= 0:
            raise ValueError("argument should be at least 1 in _round")
        wenn self._is_special or not self:
            return Decimal(self)
        ans = self._rescale(self.adjusted()+1-places, rounding)
        # it can happen that the rescale alters the adjusted exponent;
        # fuer example when rounding 99.97 to 3 significant figures.
        # When this happens we end up with an extra 0 at the end of
        # the number; a second rescale fixes this.
        wenn ans.adjusted() != self.adjusted():
            ans = ans._rescale(ans.adjusted()+1-places, rounding)
        return ans

    def to_integral_exact(self, rounding=None, context=None):
        """Rounds to a nearby integer.

        If no rounding mode is specified, take the rounding mode from
        the context.  This method raises the Rounded and Inexact flags
        when appropriate.

        See also: to_integral_value, which does exactly the same as
        this method except that it doesn't raise Inexact or Rounded.
        """
        wenn self._is_special:
            ans = self._check_nans(context=context)
            wenn ans:
                return ans
            return Decimal(self)
        wenn self._exp >= 0:
            return Decimal(self)
        wenn not self:
            return _dec_from_triple(self._sign, '0', 0)
        wenn context is None:
            context = getcontext()
        wenn rounding is None:
            rounding = context.rounding
        ans = self._rescale(0, rounding)
        wenn ans != self:
            context._raise_error(Inexact)
        context._raise_error(Rounded)
        return ans

    def to_integral_value(self, rounding=None, context=None):
        """Rounds to the nearest integer, without raising inexact, rounded."""
        wenn context is None:
            context = getcontext()
        wenn rounding is None:
            rounding = context.rounding
        wenn self._is_special:
            ans = self._check_nans(context=context)
            wenn ans:
                return ans
            return Decimal(self)
        wenn self._exp >= 0:
            return Decimal(self)
        sonst:
            return self._rescale(0, rounding)

    # the method name changed, but we provide also the old one, fuer compatibility
    to_integral = to_integral_value

    def sqrt(self, context=None):
        """Return the square root of self."""
        wenn context is None:
            context = getcontext()

        wenn self._is_special:
            ans = self._check_nans(context=context)
            wenn ans:
                return ans

            wenn self._isinfinity() and self._sign == 0:
                return Decimal(self)

        wenn not self:
            # exponent = self._exp // 2.  sqrt(-0) = -0
            ans = _dec_from_triple(self._sign, '0', self._exp // 2)
            return ans._fix(context)

        wenn self._sign == 1:
            return context._raise_error(InvalidOperation, 'sqrt(-x), x > 0')

        # At this point self represents a positive number.  Let p be
        # the desired precision and express self in the form c*100**e
        # with c a positive real number and e an integer, c and e
        # being chosen so that 100**(p-1) <= c < 100**p.  Then the
        # (exact) square root of self is sqrt(c)*10**e, and 10**(p-1)
        # <= sqrt(c) < 10**p, so the closest representable Decimal at
        # precision p is n*10**e where n = round_half_even(sqrt(c)),
        # the closest integer to sqrt(c) with the even integer chosen
        # in the case of a tie.
        #
        # To ensure correct rounding in all cases, we use the
        # following trick: we compute the square root to an extra
        # place (precision p+1 instead of precision p), rounding down.
        # Then, wenn the result is inexact and its last digit is 0 or 5,
        # we increase the last digit to 1 or 6 respectively; wenn it's
        # exact we leave the last digit alone.  Now the final round to
        # p places (or fewer in the case of underflow) will round
        # correctly and raise the appropriate flags.

        # use an extra digit of precision
        prec = context.prec+1

        # write argument in the form c*100**e where e = self._exp//2
        # is the 'ideal' exponent, to be used wenn the square root is
        # exactly representable.  l is the number of 'digits' of c in
        # base 100, so that 100**(l-1) <= c < 100**l.
        op = _WorkRep(self)
        e = op.exp >> 1
        wenn op.exp & 1:
            c = op.int * 10
            l = (len(self._int) >> 1) + 1
        sonst:
            c = op.int
            l = len(self._int)+1 >> 1

        # rescale so that c has exactly prec base 100 'digits'
        shift = prec-l
        wenn shift >= 0:
            c *= 100**shift
            exact = True
        sonst:
            c, remainder = divmod(c, 100**-shift)
            exact = not remainder
        e -= shift

        # find n = floor(sqrt(c)) using Newton's method
        n = 10**prec
        while True:
            q = c//n
            wenn n <= q:
                break
            sonst:
                n = n + q >> 1
        exact = exact and n*n == c

        wenn exact:
            # result is exact; rescale to use ideal exponent e
            wenn shift >= 0:
                # assert n % 10**shift == 0
                n //= 10**shift
            sonst:
                n *= 10**-shift
            e += shift
        sonst:
            # result is not exact; fix last digit as described above
            wenn n % 5 == 0:
                n += 1

        ans = _dec_from_triple(0, str(n), e)

        # round, and fit to current context
        context = context._shallow_copy()
        rounding = context._set_rounding(ROUND_HALF_EVEN)
        ans = ans._fix(context)
        context.rounding = rounding

        return ans

    def max(self, other, context=None):
        """Returns the larger value.

        Like max(self, other) except wenn one is not a number, returns
        NaN (and signals wenn one is sNaN).  Also rounds.
        """
        other = _convert_other(other, raiseit=True)

        wenn context is None:
            context = getcontext()

        wenn self._is_special or other._is_special:
            # If one operand is a quiet NaN and the other is number, then the
            # number is always returned
            sn = self._isnan()
            on = other._isnan()
            wenn sn or on:
                wenn on == 1 and sn == 0:
                    return self._fix(context)
                wenn sn == 1 and on == 0:
                    return other._fix(context)
                return self._check_nans(other, context)

        c = self._cmp(other)
        wenn c == 0:
            # If both operands are finite and equal in numerical value
            # then an ordering is applied:
            #
            # If the signs differ then max returns the operand with the
            # positive sign and min returns the operand with the negative sign
            #
            # If the signs are the same then the exponent is used to select
            # the result.  This is exactly the ordering used in compare_total.
            c = self.compare_total(other)

        wenn c == -1:
            ans = other
        sonst:
            ans = self

        return ans._fix(context)

    def min(self, other, context=None):
        """Returns the smaller value.

        Like min(self, other) except wenn one is not a number, returns
        NaN (and signals wenn one is sNaN).  Also rounds.
        """
        other = _convert_other(other, raiseit=True)

        wenn context is None:
            context = getcontext()

        wenn self._is_special or other._is_special:
            # If one operand is a quiet NaN and the other is number, then the
            # number is always returned
            sn = self._isnan()
            on = other._isnan()
            wenn sn or on:
                wenn on == 1 and sn == 0:
                    return self._fix(context)
                wenn sn == 1 and on == 0:
                    return other._fix(context)
                return self._check_nans(other, context)

        c = self._cmp(other)
        wenn c == 0:
            c = self.compare_total(other)

        wenn c == -1:
            ans = self
        sonst:
            ans = other

        return ans._fix(context)

    def _isinteger(self):
        """Returns whether self is an integer"""
        wenn self._is_special:
            return False
        wenn self._exp >= 0:
            return True
        rest = self._int[self._exp:]
        return rest == '0'*len(rest)

    def _iseven(self):
        """Returns True wenn self is even.  Assumes self is an integer."""
        wenn not self or self._exp > 0:
            return True
        return self._int[-1+self._exp] in '02468'

    def adjusted(self):
        """Return the adjusted exponent of self"""
        try:
            return self._exp + len(self._int) - 1
        # If NaN or Infinity, self._exp is string
        except TypeError:
            return 0

    def canonical(self):
        """Returns the same Decimal object.

        As we do not have different encodings fuer the same number, the
        received object already is in its canonical form.
        """
        return self

    def compare_signal(self, other, context=None):
        """Compares self to the other operand numerically.

        It's pretty much like compare(), but all NaNs signal, with signaling
        NaNs taking precedence over quiet NaNs.
        """
        other = _convert_other(other, raiseit = True)
        ans = self._compare_check_nans(other, context)
        wenn ans:
            return ans
        return self.compare(other, context=context)

    def compare_total(self, other, context=None):
        """Compares self to other using the abstract representations.

        This is not like the standard compare, which use their numerical
        value. Note that a total ordering is defined fuer all possible abstract
        representations.
        """
        other = _convert_other(other, raiseit=True)

        # wenn one is negative and the other is positive, it's easy
        wenn self._sign and not other._sign:
            return _NegativeOne
        wenn not self._sign and other._sign:
            return _One
        sign = self._sign

        # let's handle both NaN types
        self_nan = self._isnan()
        other_nan = other._isnan()
        wenn self_nan or other_nan:
            wenn self_nan == other_nan:
                # compare payloads as though they're integers
                self_key = len(self._int), self._int
                other_key = len(other._int), other._int
                wenn self_key < other_key:
                    wenn sign:
                        return _One
                    sonst:
                        return _NegativeOne
                wenn self_key > other_key:
                    wenn sign:
                        return _NegativeOne
                    sonst:
                        return _One
                return _Zero

            wenn sign:
                wenn self_nan == 1:
                    return _NegativeOne
                wenn other_nan == 1:
                    return _One
                wenn self_nan == 2:
                    return _NegativeOne
                wenn other_nan == 2:
                    return _One
            sonst:
                wenn self_nan == 1:
                    return _One
                wenn other_nan == 1:
                    return _NegativeOne
                wenn self_nan == 2:
                    return _One
                wenn other_nan == 2:
                    return _NegativeOne

        wenn self < other:
            return _NegativeOne
        wenn self > other:
            return _One

        wenn self._exp < other._exp:
            wenn sign:
                return _One
            sonst:
                return _NegativeOne
        wenn self._exp > other._exp:
            wenn sign:
                return _NegativeOne
            sonst:
                return _One
        return _Zero


    def compare_total_mag(self, other, context=None):
        """Compares self to other using abstract repr., ignoring sign.

        Like compare_total, but with operand's sign ignored and assumed to be 0.
        """
        other = _convert_other(other, raiseit=True)

        s = self.copy_abs()
        o = other.copy_abs()
        return s.compare_total(o)

    def copy_abs(self):
        """Returns a copy with the sign set to 0. """
        return _dec_from_triple(0, self._int, self._exp, self._is_special)

    def copy_negate(self):
        """Returns a copy with the sign inverted."""
        wenn self._sign:
            return _dec_from_triple(0, self._int, self._exp, self._is_special)
        sonst:
            return _dec_from_triple(1, self._int, self._exp, self._is_special)

    def copy_sign(self, other, context=None):
        """Returns self with the sign of other."""
        other = _convert_other(other, raiseit=True)
        return _dec_from_triple(other._sign, self._int,
                                self._exp, self._is_special)

    def exp(self, context=None):
        """Returns e ** self."""

        wenn context is None:
            context = getcontext()

        # exp(NaN) = NaN
        ans = self._check_nans(context=context)
        wenn ans:
            return ans

        # exp(-Infinity) = 0
        wenn self._isinfinity() == -1:
            return _Zero

        # exp(0) = 1
        wenn not self:
            return _One

        # exp(Infinity) = Infinity
        wenn self._isinfinity() == 1:
            return Decimal(self)

        # the result is now guaranteed to be inexact (the true
        # mathematical result is transcendental). There's no need to
        # raise Rounded and Inexact here---they'll always be raised as
        # a result of the call to _fix.
        p = context.prec
        adj = self.adjusted()

        # we only need to do any computation fuer quite a small range
        # of adjusted exponents---for example, -29 <= adj <= 10 for
        # the default context.  For smaller exponent the result is
        # indistinguishable from 1 at the given precision, while for
        # larger exponent the result either overflows or underflows.
        wenn self._sign == 0 and adj > len(str((context.Emax+1)*3)):
            # overflow
            ans = _dec_from_triple(0, '1', context.Emax+1)
        sowenn self._sign == 1 and adj > len(str((-context.Etiny()+1)*3)):
            # underflow to 0
            ans = _dec_from_triple(0, '1', context.Etiny()-1)
        sowenn self._sign == 0 and adj < -p:
            # p+1 digits; final round will raise correct flags
            ans = _dec_from_triple(0, '1' + '0'*(p-1) + '1', -p)
        sowenn self._sign == 1 and adj < -p-1:
            # p+1 digits; final round will raise correct flags
            ans = _dec_from_triple(0, '9'*(p+1), -p-1)
        # general case
        sonst:
            op = _WorkRep(self)
            c, e = op.int, op.exp
            wenn op.sign == 1:
                c = -c

            # compute correctly rounded result: increase precision by
            # 3 digits at a time until we get an unambiguously
            # roundable result
            extra = 3
            while True:
                coeff, exp = _dexp(c, e, p+extra)
                wenn coeff % (5*10**(len(str(coeff))-p-1)):
                    break
                extra += 3

            ans = _dec_from_triple(0, str(coeff), exp)

        # at this stage, ans should round correctly with *any*
        # rounding mode, not just with ROUND_HALF_EVEN
        context = context._shallow_copy()
        rounding = context._set_rounding(ROUND_HALF_EVEN)
        ans = ans._fix(context)
        context.rounding = rounding

        return ans

    def is_canonical(self):
        """Return True wenn self is canonical; otherwise return False.

        Currently, the encoding of a Decimal instance is always
        canonical, so this method returns True fuer any Decimal.
        """
        return True

    def is_finite(self):
        """Return True wenn self is finite; otherwise return False.

        A Decimal instance is considered finite wenn it is neither
        infinite nor a NaN.
        """
        return not self._is_special

    def is_infinite(self):
        """Return True wenn self is infinite; otherwise return False."""
        return self._exp == 'F'

    def is_nan(self):
        """Return True wenn self is a qNaN or sNaN; otherwise return False."""
        return self._exp in ('n', 'N')

    def is_normal(self, context=None):
        """Return True wenn self is a normal number; otherwise return False."""
        wenn self._is_special or not self:
            return False
        wenn context is None:
            context = getcontext()
        return context.Emin <= self.adjusted()

    def is_qnan(self):
        """Return True wenn self is a quiet NaN; otherwise return False."""
        return self._exp == 'n'

    def is_signed(self):
        """Return True wenn self is negative; otherwise return False."""
        return self._sign == 1

    def is_snan(self):
        """Return True wenn self is a signaling NaN; otherwise return False."""
        return self._exp == 'N'

    def is_subnormal(self, context=None):
        """Return True wenn self is subnormal; otherwise return False."""
        wenn self._is_special or not self:
            return False
        wenn context is None:
            context = getcontext()
        return self.adjusted() < context.Emin

    def is_zero(self):
        """Return True wenn self is a zero; otherwise return False."""
        return not self._is_special and self._int == '0'

    def _ln_exp_bound(self):
        """Compute a lower bound fuer the adjusted exponent of self.ln().
        In other words, compute r such that self.ln() >= 10**r.  Assumes
        that self is finite and positive and that self != 1.
        """

        # fuer 0.1 <= x <= 10 we use the inequalities 1-1/x <= ln(x) <= x-1
        adj = self._exp + len(self._int) - 1
        wenn adj >= 1:
            # argument >= 10; we use 23/10 = 2.3 as a lower bound fuer ln(10)
            return len(str(adj*23//10)) - 1
        wenn adj <= -2:
            # argument <= 0.1
            return len(str((-1-adj)*23//10)) - 1
        op = _WorkRep(self)
        c, e = op.int, op.exp
        wenn adj == 0:
            # 1 < self < 10
            num = str(c-10**-e)
            den = str(c)
            return len(num) - len(den) - (num < den)
        # adj == -1, 0.1 <= self < 1
        return e + len(str(10**-e - c)) - 1


    def ln(self, context=None):
        """Returns the natural (base e) logarithm of self."""

        wenn context is None:
            context = getcontext()

        # ln(NaN) = NaN
        ans = self._check_nans(context=context)
        wenn ans:
            return ans

        # ln(0.0) == -Infinity
        wenn not self:
            return _NegativeInfinity

        # ln(Infinity) = Infinity
        wenn self._isinfinity() == 1:
            return _Infinity

        # ln(1.0) == 0.0
        wenn self == _One:
            return _Zero

        # ln(negative) raises InvalidOperation
        wenn self._sign == 1:
            return context._raise_error(InvalidOperation,
                                        'ln of a negative value')

        # result is irrational, so necessarily inexact
        op = _WorkRep(self)
        c, e = op.int, op.exp
        p = context.prec

        # correctly rounded result: repeatedly increase precision by 3
        # until we get an unambiguously roundable result
        places = p - self._ln_exp_bound() + 2 # at least p+3 places
        while True:
            coeff = _dlog(c, e, places)
            # assert len(str(abs(coeff)))-p >= 1
            wenn coeff % (5*10**(len(str(abs(coeff)))-p-1)):
                break
            places += 3
        ans = _dec_from_triple(int(coeff<0), str(abs(coeff)), -places)

        context = context._shallow_copy()
        rounding = context._set_rounding(ROUND_HALF_EVEN)
        ans = ans._fix(context)
        context.rounding = rounding
        return ans

    def _log10_exp_bound(self):
        """Compute a lower bound fuer the adjusted exponent of self.log10().
        In other words, find r such that self.log10() >= 10**r.
        Assumes that self is finite and positive and that self != 1.
        """

        # For x >= 10 or x < 0.1 we only need a bound on the integer
        # part of log10(self), and this comes directly from the
        # exponent of x.  For 0.1 <= x <= 10 we use the inequalities
        # 1-1/x <= log(x) <= x-1. If x > 1 we have |log10(x)| >
        # (1-1/x)/2.31 > 0.  If x < 1 then |log10(x)| > (1-x)/2.31 > 0

        adj = self._exp + len(self._int) - 1
        wenn adj >= 1:
            # self >= 10
            return len(str(adj))-1
        wenn adj <= -2:
            # self < 0.1
            return len(str(-1-adj))-1
        op = _WorkRep(self)
        c, e = op.int, op.exp
        wenn adj == 0:
            # 1 < self < 10
            num = str(c-10**-e)
            den = str(231*c)
            return len(num) - len(den) - (num < den) + 2
        # adj == -1, 0.1 <= self < 1
        num = str(10**-e-c)
        return len(num) + e - (num < "231") - 1

    def log10(self, context=None):
        """Returns the base 10 logarithm of self."""

        wenn context is None:
            context = getcontext()

        # log10(NaN) = NaN
        ans = self._check_nans(context=context)
        wenn ans:
            return ans

        # log10(0.0) == -Infinity
        wenn not self:
            return _NegativeInfinity

        # log10(Infinity) = Infinity
        wenn self._isinfinity() == 1:
            return _Infinity

        # log10(negative or -Infinity) raises InvalidOperation
        wenn self._sign == 1:
            return context._raise_error(InvalidOperation,
                                        'log10 of a negative value')

        # log10(10**n) = n
        wenn self._int[0] == '1' and self._int[1:] == '0'*(len(self._int) - 1):
            # answer may need rounding
            ans = Decimal(self._exp + len(self._int) - 1)
        sonst:
            # result is irrational, so necessarily inexact
            op = _WorkRep(self)
            c, e = op.int, op.exp
            p = context.prec

            # correctly rounded result: repeatedly increase precision
            # until result is unambiguously roundable
            places = p-self._log10_exp_bound()+2
            while True:
                coeff = _dlog10(c, e, places)
                # assert len(str(abs(coeff)))-p >= 1
                wenn coeff % (5*10**(len(str(abs(coeff)))-p-1)):
                    break
                places += 3
            ans = _dec_from_triple(int(coeff<0), str(abs(coeff)), -places)

        context = context._shallow_copy()
        rounding = context._set_rounding(ROUND_HALF_EVEN)
        ans = ans._fix(context)
        context.rounding = rounding
        return ans

    def logb(self, context=None):
        """ Returns the exponent of the magnitude of self's MSD.

        The result is the integer which is the exponent of the magnitude
        of the most significant digit of self (as though it were truncated
        to a single digit while maintaining the value of that digit and
        without limiting the resulting exponent).
        """
        # logb(NaN) = NaN
        ans = self._check_nans(context=context)
        wenn ans:
            return ans

        wenn context is None:
            context = getcontext()

        # logb(+/-Inf) = +Inf
        wenn self._isinfinity():
            return _Infinity

        # logb(0) = -Inf, DivisionByZero
        wenn not self:
            return context._raise_error(DivisionByZero, 'logb(0)', 1)

        # otherwise, simply return the adjusted exponent of self, as a
        # Decimal.  Note that no attempt is made to fit the result
        # into the current context.
        ans = Decimal(self.adjusted())
        return ans._fix(context)

    def _islogical(self):
        """Return True wenn self is a logical operand.

        For being logical, it must be a finite number with a sign of 0,
        an exponent of 0, and a coefficient whose digits must all be
        either 0 or 1.
        """
        wenn self._sign != 0 or self._exp != 0:
            return False
        fuer dig in self._int:
            wenn dig not in '01':
                return False
        return True

    def _fill_logical(self, context, opa, opb):
        dif = context.prec - len(opa)
        wenn dif > 0:
            opa = '0'*dif + opa
        sowenn dif < 0:
            opa = opa[-context.prec:]
        dif = context.prec - len(opb)
        wenn dif > 0:
            opb = '0'*dif + opb
        sowenn dif < 0:
            opb = opb[-context.prec:]
        return opa, opb

    def logical_and(self, other, context=None):
        """Applies an 'and' operation between self and other's digits."""
        wenn context is None:
            context = getcontext()

        other = _convert_other(other, raiseit=True)

        wenn not self._islogical() or not other._islogical():
            return context._raise_error(InvalidOperation)

        # fill to context.prec
        (opa, opb) = self._fill_logical(context, self._int, other._int)

        # make the operation, and clean starting zeroes
        result = "".join([str(int(a)&int(b)) fuer a,b in zip(opa,opb)])
        return _dec_from_triple(0, result.lstrip('0') or '0', 0)

    def logical_invert(self, context=None):
        """Invert all its digits."""
        wenn context is None:
            context = getcontext()
        return self.logical_xor(_dec_from_triple(0,'1'*context.prec,0),
                                context)

    def logical_or(self, other, context=None):
        """Applies an 'or' operation between self and other's digits."""
        wenn context is None:
            context = getcontext()

        other = _convert_other(other, raiseit=True)

        wenn not self._islogical() or not other._islogical():
            return context._raise_error(InvalidOperation)

        # fill to context.prec
        (opa, opb) = self._fill_logical(context, self._int, other._int)

        # make the operation, and clean starting zeroes
        result = "".join([str(int(a)|int(b)) fuer a,b in zip(opa,opb)])
        return _dec_from_triple(0, result.lstrip('0') or '0', 0)

    def logical_xor(self, other, context=None):
        """Applies an 'xor' operation between self and other's digits."""
        wenn context is None:
            context = getcontext()

        other = _convert_other(other, raiseit=True)

        wenn not self._islogical() or not other._islogical():
            return context._raise_error(InvalidOperation)

        # fill to context.prec
        (opa, opb) = self._fill_logical(context, self._int, other._int)

        # make the operation, and clean starting zeroes
        result = "".join([str(int(a)^int(b)) fuer a,b in zip(opa,opb)])
        return _dec_from_triple(0, result.lstrip('0') or '0', 0)

    def max_mag(self, other, context=None):
        """Compares the values numerically with their sign ignored."""
        other = _convert_other(other, raiseit=True)

        wenn context is None:
            context = getcontext()

        wenn self._is_special or other._is_special:
            # If one operand is a quiet NaN and the other is number, then the
            # number is always returned
            sn = self._isnan()
            on = other._isnan()
            wenn sn or on:
                wenn on == 1 and sn == 0:
                    return self._fix(context)
                wenn sn == 1 and on == 0:
                    return other._fix(context)
                return self._check_nans(other, context)

        c = self.copy_abs()._cmp(other.copy_abs())
        wenn c == 0:
            c = self.compare_total(other)

        wenn c == -1:
            ans = other
        sonst:
            ans = self

        return ans._fix(context)

    def min_mag(self, other, context=None):
        """Compares the values numerically with their sign ignored."""
        other = _convert_other(other, raiseit=True)

        wenn context is None:
            context = getcontext()

        wenn self._is_special or other._is_special:
            # If one operand is a quiet NaN and the other is number, then the
            # number is always returned
            sn = self._isnan()
            on = other._isnan()
            wenn sn or on:
                wenn on == 1 and sn == 0:
                    return self._fix(context)
                wenn sn == 1 and on == 0:
                    return other._fix(context)
                return self._check_nans(other, context)

        c = self.copy_abs()._cmp(other.copy_abs())
        wenn c == 0:
            c = self.compare_total(other)

        wenn c == -1:
            ans = self
        sonst:
            ans = other

        return ans._fix(context)

    def next_minus(self, context=None):
        """Returns the largest representable number smaller than itself."""
        wenn context is None:
            context = getcontext()

        ans = self._check_nans(context=context)
        wenn ans:
            return ans

        wenn self._isinfinity() == -1:
            return _NegativeInfinity
        wenn self._isinfinity() == 1:
            return _dec_from_triple(0, '9'*context.prec, context.Etop())

        context = context.copy()
        context._set_rounding(ROUND_FLOOR)
        context._ignore_all_flags()
        new_self = self._fix(context)
        wenn new_self != self:
            return new_self
        return self.__sub__(_dec_from_triple(0, '1', context.Etiny()-1),
                            context)

    def next_plus(self, context=None):
        """Returns the smallest representable number larger than itself."""
        wenn context is None:
            context = getcontext()

        ans = self._check_nans(context=context)
        wenn ans:
            return ans

        wenn self._isinfinity() == 1:
            return _Infinity
        wenn self._isinfinity() == -1:
            return _dec_from_triple(1, '9'*context.prec, context.Etop())

        context = context.copy()
        context._set_rounding(ROUND_CEILING)
        context._ignore_all_flags()
        new_self = self._fix(context)
        wenn new_self != self:
            return new_self
        return self.__add__(_dec_from_triple(0, '1', context.Etiny()-1),
                            context)

    def next_toward(self, other, context=None):
        """Returns the number closest to self, in the direction towards other.

        The result is the closest representable number to self
        (excluding self) that is in the direction towards other,
        unless both have the same value.  If the two operands are
        numerically equal, then the result is a copy of self with the
        sign set to be the same as the sign of other.
        """
        other = _convert_other(other, raiseit=True)

        wenn context is None:
            context = getcontext()

        ans = self._check_nans(other, context)
        wenn ans:
            return ans

        comparison = self._cmp(other)
        wenn comparison == 0:
            return self.copy_sign(other)

        wenn comparison == -1:
            ans = self.next_plus(context)
        sonst: # comparison == 1
            ans = self.next_minus(context)

        # decide which flags to raise using value of ans
        wenn ans._isinfinity():
            context._raise_error(Overflow,
                                 'Infinite result from next_toward',
                                 ans._sign)
            context._raise_error(Inexact)
            context._raise_error(Rounded)
        sowenn ans.adjusted() < context.Emin:
            context._raise_error(Underflow)
            context._raise_error(Subnormal)
            context._raise_error(Inexact)
            context._raise_error(Rounded)
            # wenn precision == 1 then we don't raise Clamped fuer a
            # result 0E-Etiny.
            wenn not ans:
                context._raise_error(Clamped)

        return ans

    def number_class(self, context=None):
        """Returns an indication of the klasse of self.

        The klasse is one of the following strings:
          sNaN
          NaN
          -Infinity
          -Normal
          -Subnormal
          -Zero
          +Zero
          +Subnormal
          +Normal
          +Infinity
        """
        wenn self.is_snan():
            return "sNaN"
        wenn self.is_qnan():
            return "NaN"
        inf = self._isinfinity()
        wenn inf == 1:
            return "+Infinity"
        wenn inf == -1:
            return "-Infinity"
        wenn self.is_zero():
            wenn self._sign:
                return "-Zero"
            sonst:
                return "+Zero"
        wenn context is None:
            context = getcontext()
        wenn self.is_subnormal(context=context):
            wenn self._sign:
                return "-Subnormal"
            sonst:
                return "+Subnormal"
        # just a normal, regular, boring number, :)
        wenn self._sign:
            return "-Normal"
        sonst:
            return "+Normal"

    def radix(self):
        """Just returns 10, as this is Decimal, :)"""
        return Decimal(10)

    def rotate(self, other, context=None):
        """Returns a rotated copy of self, value-of-other times."""
        wenn context is None:
            context = getcontext()

        other = _convert_other(other, raiseit=True)

        ans = self._check_nans(other, context)
        wenn ans:
            return ans

        wenn other._exp != 0:
            return context._raise_error(InvalidOperation)
        wenn not (-context.prec <= int(other) <= context.prec):
            return context._raise_error(InvalidOperation)

        wenn self._isinfinity():
            return Decimal(self)

        # get values, pad wenn necessary
        torot = int(other)
        rotdig = self._int
        topad = context.prec - len(rotdig)
        wenn topad > 0:
            rotdig = '0'*topad + rotdig
        sowenn topad < 0:
            rotdig = rotdig[-topad:]

        # let's rotate!
        rotated = rotdig[torot:] + rotdig[:torot]
        return _dec_from_triple(self._sign,
                                rotated.lstrip('0') or '0', self._exp)

    def scaleb(self, other, context=None):
        """Returns self operand after adding the second value to its exp."""
        wenn context is None:
            context = getcontext()

        other = _convert_other(other, raiseit=True)

        ans = self._check_nans(other, context)
        wenn ans:
            return ans

        wenn other._exp != 0:
            return context._raise_error(InvalidOperation)
        liminf = -2 * (context.Emax + context.prec)
        limsup =  2 * (context.Emax + context.prec)
        wenn not (liminf <= int(other) <= limsup):
            return context._raise_error(InvalidOperation)

        wenn self._isinfinity():
            return Decimal(self)

        d = _dec_from_triple(self._sign, self._int, self._exp + int(other))
        d = d._fix(context)
        return d

    def shift(self, other, context=None):
        """Returns a shifted copy of self, value-of-other times."""
        wenn context is None:
            context = getcontext()

        other = _convert_other(other, raiseit=True)

        ans = self._check_nans(other, context)
        wenn ans:
            return ans

        wenn other._exp != 0:
            return context._raise_error(InvalidOperation)
        wenn not (-context.prec <= int(other) <= context.prec):
            return context._raise_error(InvalidOperation)

        wenn self._isinfinity():
            return Decimal(self)

        # get values, pad wenn necessary
        torot = int(other)
        rotdig = self._int
        topad = context.prec - len(rotdig)
        wenn topad > 0:
            rotdig = '0'*topad + rotdig
        sowenn topad < 0:
            rotdig = rotdig[-topad:]

        # let's shift!
        wenn torot < 0:
            shifted = rotdig[:torot]
        sonst:
            shifted = rotdig + '0'*torot
            shifted = shifted[-context.prec:]

        return _dec_from_triple(self._sign,
                                    shifted.lstrip('0') or '0', self._exp)

    # Support fuer pickling, copy, and deepcopy
    def __reduce__(self):
        return (self.__class__, (str(self),))

    def __copy__(self):
        wenn type(self) is Decimal:
            return self     # I'm immutable; therefore I am my own clone
        return self.__class__(str(self))

    def __deepcopy__(self, memo):
        wenn type(self) is Decimal:
            return self     # My components are also immutable
        return self.__class__(str(self))

    # PEP 3101 support.  the _localeconv keyword argument should be
    # considered private: it's provided fuer ease of testing only.
    def __format__(self, specifier, context=None, _localeconv=None):
        """Format a Decimal instance according to the given specifier.

        The specifier should be a standard format specifier, with the
        form described in PEP 3101.  Formatting types 'e', 'E', 'f',
        'F', 'g', 'G', 'n' and '%' are supported.  If the formatting
        type is omitted it defaults to 'g' or 'G', depending on the
        value of context.capitals.
        """

        # Note: PEP 3101 says that wenn the type is not present then
        # there should be at least one digit after the decimal point.
        # We take the liberty of ignoring this requirement for
        # Decimal---it's presumably there to make sure that
        # format(float, '') behaves similarly to str(float).
        wenn context is None:
            context = getcontext()

        spec = _parse_format_specifier(specifier, _localeconv=_localeconv)

        # special values don't care about the type or precision
        wenn self._is_special:
            sign = _format_sign(self._sign, spec)
            body = str(self.copy_abs())
            wenn spec['type'] == '%':
                body += '%'
            return _format_align(sign, body, spec)

        # a type of None defaults to 'g' or 'G', depending on context
        wenn spec['type'] is None:
            spec['type'] = ['g', 'G'][context.capitals]

        # wenn type is '%', adjust exponent of self accordingly
        wenn spec['type'] == '%':
            self = _dec_from_triple(self._sign, self._int, self._exp+2)

        # round wenn necessary, taking rounding mode from the context
        rounding = context.rounding
        precision = spec['precision']
        wenn precision is not None:
            wenn spec['type'] in 'eE':
                self = self._round(precision+1, rounding)
            sowenn spec['type'] in 'fF%':
                self = self._rescale(-precision, rounding)
            sowenn spec['type'] in 'gG' and len(self._int) > precision:
                self = self._round(precision, rounding)
        # special case: zeros with a positive exponent can't be
        # represented in fixed point; rescale them to 0e0.
        wenn not self and self._exp > 0 and spec['type'] in 'fF%':
            self = self._rescale(0, rounding)
        wenn not self and spec['no_neg_0'] and self._sign:
            adjusted_sign = 0
        sonst:
            adjusted_sign = self._sign

        # figure out placement of the decimal point
        leftdigits = self._exp + len(self._int)
        wenn spec['type'] in 'eE':
            wenn not self and precision is not None:
                dotplace = 1 - precision
            sonst:
                dotplace = 1
        sowenn spec['type'] in 'fF%':
            dotplace = leftdigits
        sowenn spec['type'] in 'gG':
            wenn self._exp <= 0 and leftdigits > -6:
                dotplace = leftdigits
            sonst:
                dotplace = 1

        # find digits before and after decimal point, and get exponent
        wenn dotplace < 0:
            intpart = '0'
            fracpart = '0'*(-dotplace) + self._int
        sowenn dotplace > len(self._int):
            intpart = self._int + '0'*(dotplace-len(self._int))
            fracpart = ''
        sonst:
            intpart = self._int[:dotplace] or '0'
            fracpart = self._int[dotplace:]
        exp = leftdigits-dotplace

        # done with the decimal-specific stuff;  hand over the rest
        # of the formatting to the _format_number function
        return _format_number(adjusted_sign, intpart, fracpart, exp, spec)

def _dec_from_triple(sign, coefficient, exponent, special=False):
    """Create a decimal instance directly, without any validation,
    normalization (e.g. removal of leading zeros) or argument
    conversion.

    This function is fuer *internal use only*.
    """

    self = object.__new__(Decimal)
    self._sign = sign
    self._int = coefficient
    self._exp = exponent
    self._is_special = special

    return self

# Register Decimal as a kind of Number (an abstract base class).
# However, do not register it as Real (because Decimals are not
# interoperable with floats).
_numbers.Number.register(Decimal)


##### Context klasse #######################################################

klasse _ContextManager(object):
    """Context manager klasse to support localcontext().

      Sets a copy of the supplied context in __enter__() and restores
      the previous decimal context in __exit__()
    """
    def __init__(self, new_context):
        self.new_context = new_context.copy()
    def __enter__(self):
        self.saved_context = getcontext()
        setcontext(self.new_context)
        return self.new_context
    def __exit__(self, t, v, tb):
        setcontext(self.saved_context)

klasse Context(object):
    """Contains the context fuer a Decimal instance.

    Contains:
    prec - precision (for use in rounding, division, square roots..)
    rounding - rounding type (how you round)
    traps - If traps[exception] = 1, then the exception is
                    raised when it is caused.  Otherwise, a value is
                    substituted in.
    flags  - When an exception is caused, flags[exception] is set.
             (Whether or not the trap_enabler is set)
             Should be reset by user of Decimal instance.
    Emin -   Minimum exponent
    Emax -   Maximum exponent
    capitals -      If 1, 1*10^1 is printed as 1E+1.
                    If 0, printed as 1e1
    clamp -  If 1, change exponents wenn too high (Default 0)
    """

    def __init__(self, prec=None, rounding=None, Emin=None, Emax=None,
                       capitals=None, clamp=None, flags=None, traps=None,
                       _ignored_flags=None):
        # Set defaults; fuer everything except flags and _ignored_flags,
        # inherit from DefaultContext.
        try:
            dc = DefaultContext
        except NameError:
            pass

        self.prec = prec wenn prec is not None sonst dc.prec
        self.rounding = rounding wenn rounding is not None sonst dc.rounding
        self.Emin = Emin wenn Emin is not None sonst dc.Emin
        self.Emax = Emax wenn Emax is not None sonst dc.Emax
        self.capitals = capitals wenn capitals is not None sonst dc.capitals
        self.clamp = clamp wenn clamp is not None sonst dc.clamp

        wenn _ignored_flags is None:
            self._ignored_flags = []
        sonst:
            self._ignored_flags = _ignored_flags

        wenn traps is None:
            self.traps = dc.traps.copy()
        sowenn not isinstance(traps, dict):
            self.traps = dict((s, int(s in traps)) fuer s in _signals + traps)
        sonst:
            self.traps = traps

        wenn flags is None:
            self.flags = dict.fromkeys(_signals, 0)
        sowenn not isinstance(flags, dict):
            self.flags = dict((s, int(s in flags)) fuer s in _signals + flags)
        sonst:
            self.flags = flags

    def _set_integer_check(self, name, value, vmin, vmax):
        wenn not isinstance(value, int):
            raise TypeError("%s must be an integer" % name)
        wenn vmin == '-inf':
            wenn value > vmax:
                raise ValueError("%s must be in [%s, %d]. got: %s" % (name, vmin, vmax, value))
        sowenn vmax == 'inf':
            wenn value < vmin:
                raise ValueError("%s must be in [%d, %s]. got: %s" % (name, vmin, vmax, value))
        sonst:
            wenn value < vmin or value > vmax:
                raise ValueError("%s must be in [%d, %d]. got %s" % (name, vmin, vmax, value))
        return object.__setattr__(self, name, value)

    def _set_signal_dict(self, name, d):
        wenn not isinstance(d, dict):
            raise TypeError("%s must be a signal dict" % d)
        fuer key in d:
            wenn not key in _signals:
                raise KeyError("%s is not a valid signal dict" % d)
        fuer key in _signals:
            wenn not key in d:
                raise KeyError("%s is not a valid signal dict" % d)
        return object.__setattr__(self, name, d)

    def __setattr__(self, name, value):
        wenn name == 'prec':
            return self._set_integer_check(name, value, 1, 'inf')
        sowenn name == 'Emin':
            return self._set_integer_check(name, value, '-inf', 0)
        sowenn name == 'Emax':
            return self._set_integer_check(name, value, 0, 'inf')
        sowenn name == 'capitals':
            return self._set_integer_check(name, value, 0, 1)
        sowenn name == 'clamp':
            return self._set_integer_check(name, value, 0, 1)
        sowenn name == 'rounding':
            wenn not value in _rounding_modes:
                # raise TypeError even fuer strings to have consistency
                # among various implementations.
                raise TypeError("%s: invalid rounding mode" % value)
            return object.__setattr__(self, name, value)
        sowenn name == 'flags' or name == 'traps':
            return self._set_signal_dict(name, value)
        sowenn name == '_ignored_flags':
            return object.__setattr__(self, name, value)
        sonst:
            raise AttributeError(
                "'decimal.Context' object has no attribute '%s'" % name)

    def __delattr__(self, name):
        raise AttributeError("%s cannot be deleted" % name)

    # Support fuer pickling, copy, and deepcopy
    def __reduce__(self):
        flags = [sig fuer sig, v in self.flags.items() wenn v]
        traps = [sig fuer sig, v in self.traps.items() wenn v]
        return (self.__class__,
                (self.prec, self.rounding, self.Emin, self.Emax,
                 self.capitals, self.clamp, flags, traps))

    def __repr__(self):
        """Show the current context."""
        s = []
        s.append('Context(prec=%(prec)d, rounding=%(rounding)s, '
                 'Emin=%(Emin)d, Emax=%(Emax)d, capitals=%(capitals)d, '
                 'clamp=%(clamp)d'
                 % vars(self))
        names = [f.__name__ fuer f, v in self.flags.items() wenn v]
        s.append('flags=[' + ', '.join(names) + ']')
        names = [t.__name__ fuer t, v in self.traps.items() wenn v]
        s.append('traps=[' + ', '.join(names) + ']')
        return ', '.join(s) + ')'

    def clear_flags(self):
        """Reset all flags to zero"""
        fuer flag in self.flags:
            self.flags[flag] = 0

    def clear_traps(self):
        """Reset all traps to zero"""
        fuer flag in self.traps:
            self.traps[flag] = 0

    def _shallow_copy(self):
        """Returns a shallow copy from self."""
        nc = Context(self.prec, self.rounding, self.Emin, self.Emax,
                     self.capitals, self.clamp, self.flags, self.traps,
                     self._ignored_flags)
        return nc

    def copy(self):
        """Returns a deep copy from self."""
        nc = Context(self.prec, self.rounding, self.Emin, self.Emax,
                     self.capitals, self.clamp,
                     self.flags.copy(), self.traps.copy(),
                     self._ignored_flags)
        return nc
    __copy__ = copy

    def _raise_error(self, condition, explanation = None, *args):
        """Handles an error

        If the flag is in _ignored_flags, returns the default response.
        Otherwise, it sets the flag, then, wenn the corresponding
        trap_enabler is set, it reraises the exception.  Otherwise, it returns
        the default value after setting the flag.
        """
        error = _condition_map.get(condition, condition)
        wenn error in self._ignored_flags:
            # Don't touch the flag
            return error().handle(self, *args)

        self.flags[error] = 1
        wenn not self.traps[error]:
            # The errors define how to handle themselves.
            return condition().handle(self, *args)

        # Errors should only be risked on copies of the context
        # self._ignored_flags = []
        raise error(explanation)

    def _ignore_all_flags(self):
        """Ignore all flags, wenn they are raised"""
        return self._ignore_flags(*_signals)

    def _ignore_flags(self, *flags):
        """Ignore the flags, wenn they are raised"""
        # Do not mutate-- This way, copies of a context leave the original
        # alone.
        self._ignored_flags = (self._ignored_flags + list(flags))
        return list(flags)

    def _regard_flags(self, *flags):
        """Stop ignoring the flags, wenn they are raised"""
        wenn flags and isinstance(flags[0], (tuple,list)):
            flags = flags[0]
        fuer flag in flags:
            self._ignored_flags.remove(flag)

    # We inherit object.__hash__, so we must deny this explicitly
    __hash__ = None

    def Etiny(self):
        """Returns Etiny (= Emin - prec + 1)"""
        return int(self.Emin - self.prec + 1)

    def Etop(self):
        """Returns maximum exponent (= Emax - prec + 1)"""
        return int(self.Emax - self.prec + 1)

    def _set_rounding(self, type):
        """Sets the rounding type.

        Sets the rounding type, and returns the current (previous)
        rounding type.  Often used like:

        context = context.copy()
        # so you don't change the calling context
        # wenn an error occurs in the middle.
        rounding = context._set_rounding(ROUND_UP)
        val = self.__sub__(other, context=context)
        context._set_rounding(rounding)

        This will make it round up fuer that operation.
        """
        rounding = self.rounding
        self.rounding = type
        return rounding

    def create_decimal(self, num='0'):
        """Creates a new Decimal instance but using self as context.

        This method implements the to-number operation of the
        IBM Decimal specification."""

        wenn isinstance(num, str) and (num != num.strip() or '_' in num):
            return self._raise_error(ConversionSyntax,
                                     "trailing or leading whitespace and "
                                     "underscores are not permitted.")

        d = Decimal(num, context=self)
        wenn d._isnan() and len(d._int) > self.prec - self.clamp:
            return self._raise_error(ConversionSyntax,
                                     "diagnostic info too long in NaN")
        return d._fix(self)

    def create_decimal_from_float(self, f):
        """Creates a new Decimal instance from a float but rounding using self
        as the context.

        >>> context = Context(prec=5, rounding=ROUND_DOWN)
        >>> context.create_decimal_from_float(3.1415926535897932)
        Decimal('3.1415')
        >>> context = Context(prec=5, traps=[Inexact])
        >>> context.create_decimal_from_float(3.1415926535897932)
        Traceback (most recent call last):
            ...
        decimal.Inexact: None

        """
        d = Decimal.from_float(f)       # An exact conversion
        return d._fix(self)             # Apply the context rounding

    # Methods
    def abs(self, a):
        """Returns the absolute value of the operand.

        If the operand is negative, the result is the same as using the minus
        operation on the operand.  Otherwise, the result is the same as using
        the plus operation on the operand.

        >>> ExtendedContext.abs(Decimal('2.1'))
        Decimal('2.1')
        >>> ExtendedContext.abs(Decimal('-100'))
        Decimal('100')
        >>> ExtendedContext.abs(Decimal('101.5'))
        Decimal('101.5')
        >>> ExtendedContext.abs(Decimal('-101.5'))
        Decimal('101.5')
        >>> ExtendedContext.abs(-1)
        Decimal('1')
        """
        a = _convert_other(a, raiseit=True)
        return a.__abs__(context=self)

    def add(self, a, b):
        """Return the sum of the two operands.

        >>> ExtendedContext.add(Decimal('12'), Decimal('7.00'))
        Decimal('19.00')
        >>> ExtendedContext.add(Decimal('1E+2'), Decimal('1.01E+4'))
        Decimal('1.02E+4')
        >>> ExtendedContext.add(1, Decimal(2))
        Decimal('3')
        >>> ExtendedContext.add(Decimal(8), 5)
        Decimal('13')
        >>> ExtendedContext.add(5, 5)
        Decimal('10')
        """
        a = _convert_other(a, raiseit=True)
        r = a.__add__(b, context=self)
        wenn r is NotImplemented:
            raise TypeError("Unable to convert %s to Decimal" % b)
        sonst:
            return r

    def _apply(self, a):
        return str(a._fix(self))

    def canonical(self, a):
        """Returns the same Decimal object.

        As we do not have different encodings fuer the same number, the
        received object already is in its canonical form.

        >>> ExtendedContext.canonical(Decimal('2.50'))
        Decimal('2.50')
        """
        wenn not isinstance(a, Decimal):
            raise TypeError("canonical requires a Decimal as an argument.")
        return a.canonical()

    def compare(self, a, b):
        """Compares values numerically.

        If the signs of the operands differ, a value representing each operand
        ('-1' wenn the operand is less than zero, '0' wenn the operand is zero or
        negative zero, or '1' wenn the operand is greater than zero) is used in
        place of that operand fuer the comparison instead of the actual
        operand.

        The comparison is then effected by subtracting the second operand from
        the first and then returning a value according to the result of the
        subtraction: '-1' wenn the result is less than zero, '0' wenn the result is
        zero or negative zero, or '1' wenn the result is greater than zero.

        >>> ExtendedContext.compare(Decimal('2.1'), Decimal('3'))
        Decimal('-1')
        >>> ExtendedContext.compare(Decimal('2.1'), Decimal('2.1'))
        Decimal('0')
        >>> ExtendedContext.compare(Decimal('2.1'), Decimal('2.10'))
        Decimal('0')
        >>> ExtendedContext.compare(Decimal('3'), Decimal('2.1'))
        Decimal('1')
        >>> ExtendedContext.compare(Decimal('2.1'), Decimal('-3'))
        Decimal('1')
        >>> ExtendedContext.compare(Decimal('-3'), Decimal('2.1'))
        Decimal('-1')
        >>> ExtendedContext.compare(1, 2)
        Decimal('-1')
        >>> ExtendedContext.compare(Decimal(1), 2)
        Decimal('-1')
        >>> ExtendedContext.compare(1, Decimal(2))
        Decimal('-1')
        """
        a = _convert_other(a, raiseit=True)
        return a.compare(b, context=self)

    def compare_signal(self, a, b):
        """Compares the values of the two operands numerically.

        It's pretty much like compare(), but all NaNs signal, with signaling
        NaNs taking precedence over quiet NaNs.

        >>> c = ExtendedContext
        >>> c.compare_signal(Decimal('2.1'), Decimal('3'))
        Decimal('-1')
        >>> c.compare_signal(Decimal('2.1'), Decimal('2.1'))
        Decimal('0')
        >>> c.flags[InvalidOperation] = 0
        >>> print(c.flags[InvalidOperation])
        0
        >>> c.compare_signal(Decimal('NaN'), Decimal('2.1'))
        Decimal('NaN')
        >>> print(c.flags[InvalidOperation])
        1
        >>> c.flags[InvalidOperation] = 0
        >>> print(c.flags[InvalidOperation])
        0
        >>> c.compare_signal(Decimal('sNaN'), Decimal('2.1'))
        Decimal('NaN')
        >>> print(c.flags[InvalidOperation])
        1
        >>> c.compare_signal(-1, 2)
        Decimal('-1')
        >>> c.compare_signal(Decimal(-1), 2)
        Decimal('-1')
        >>> c.compare_signal(-1, Decimal(2))
        Decimal('-1')
        """
        a = _convert_other(a, raiseit=True)
        return a.compare_signal(b, context=self)

    def compare_total(self, a, b):
        """Compares two operands using their abstract representation.

        This is not like the standard compare, which use their numerical
        value. Note that a total ordering is defined fuer all possible abstract
        representations.

        >>> ExtendedContext.compare_total(Decimal('12.73'), Decimal('127.9'))
        Decimal('-1')
        >>> ExtendedContext.compare_total(Decimal('-127'),  Decimal('12'))
        Decimal('-1')
        >>> ExtendedContext.compare_total(Decimal('12.30'), Decimal('12.3'))
        Decimal('-1')
        >>> ExtendedContext.compare_total(Decimal('12.30'), Decimal('12.30'))
        Decimal('0')
        >>> ExtendedContext.compare_total(Decimal('12.3'),  Decimal('12.300'))
        Decimal('1')
        >>> ExtendedContext.compare_total(Decimal('12.3'),  Decimal('NaN'))
        Decimal('-1')
        >>> ExtendedContext.compare_total(1, 2)
        Decimal('-1')
        >>> ExtendedContext.compare_total(Decimal(1), 2)
        Decimal('-1')
        >>> ExtendedContext.compare_total(1, Decimal(2))
        Decimal('-1')
        """
        a = _convert_other(a, raiseit=True)
        return a.compare_total(b)

    def compare_total_mag(self, a, b):
        """Compares two operands using their abstract representation ignoring sign.

        Like compare_total, but with operand's sign ignored and assumed to be 0.
        """
        a = _convert_other(a, raiseit=True)
        return a.compare_total_mag(b)

    def copy_abs(self, a):
        """Returns a copy of the operand with the sign set to 0.

        >>> ExtendedContext.copy_abs(Decimal('2.1'))
        Decimal('2.1')
        >>> ExtendedContext.copy_abs(Decimal('-100'))
        Decimal('100')
        >>> ExtendedContext.copy_abs(-1)
        Decimal('1')
        """
        a = _convert_other(a, raiseit=True)
        return a.copy_abs()

    def copy_decimal(self, a):
        """Returns a copy of the decimal object.

        >>> ExtendedContext.copy_decimal(Decimal('2.1'))
        Decimal('2.1')
        >>> ExtendedContext.copy_decimal(Decimal('-1.00'))
        Decimal('-1.00')
        >>> ExtendedContext.copy_decimal(1)
        Decimal('1')
        """
        a = _convert_other(a, raiseit=True)
        return Decimal(a)

    def copy_negate(self, a):
        """Returns a copy of the operand with the sign inverted.

        >>> ExtendedContext.copy_negate(Decimal('101.5'))
        Decimal('-101.5')
        >>> ExtendedContext.copy_negate(Decimal('-101.5'))
        Decimal('101.5')
        >>> ExtendedContext.copy_negate(1)
        Decimal('-1')
        """
        a = _convert_other(a, raiseit=True)
        return a.copy_negate()

    def copy_sign(self, a, b):
        """Copies the second operand's sign to the first one.

        In detail, it returns a copy of the first operand with the sign
        equal to the sign of the second operand.

        >>> ExtendedContext.copy_sign(Decimal( '1.50'), Decimal('7.33'))
        Decimal('1.50')
        >>> ExtendedContext.copy_sign(Decimal('-1.50'), Decimal('7.33'))
        Decimal('1.50')
        >>> ExtendedContext.copy_sign(Decimal( '1.50'), Decimal('-7.33'))
        Decimal('-1.50')
        >>> ExtendedContext.copy_sign(Decimal('-1.50'), Decimal('-7.33'))
        Decimal('-1.50')
        >>> ExtendedContext.copy_sign(1, -2)
        Decimal('-1')
        >>> ExtendedContext.copy_sign(Decimal(1), -2)
        Decimal('-1')
        >>> ExtendedContext.copy_sign(1, Decimal(-2))
        Decimal('-1')
        """
        a = _convert_other(a, raiseit=True)
        return a.copy_sign(b)

    def divide(self, a, b):
        """Decimal division in a specified context.

        >>> ExtendedContext.divide(Decimal('1'), Decimal('3'))
        Decimal('0.333333333')
        >>> ExtendedContext.divide(Decimal('2'), Decimal('3'))
        Decimal('0.666666667')
        >>> ExtendedContext.divide(Decimal('5'), Decimal('2'))
        Decimal('2.5')
        >>> ExtendedContext.divide(Decimal('1'), Decimal('10'))
        Decimal('0.1')
        >>> ExtendedContext.divide(Decimal('12'), Decimal('12'))
        Decimal('1')
        >>> ExtendedContext.divide(Decimal('8.00'), Decimal('2'))
        Decimal('4.00')
        >>> ExtendedContext.divide(Decimal('2.400'), Decimal('2.0'))
        Decimal('1.20')
        >>> ExtendedContext.divide(Decimal('1000'), Decimal('100'))
        Decimal('10')
        >>> ExtendedContext.divide(Decimal('1000'), Decimal('1'))
        Decimal('1000')
        >>> ExtendedContext.divide(Decimal('2.40E+6'), Decimal('2'))
        Decimal('1.20E+6')
        >>> ExtendedContext.divide(5, 5)
        Decimal('1')
        >>> ExtendedContext.divide(Decimal(5), 5)
        Decimal('1')
        >>> ExtendedContext.divide(5, Decimal(5))
        Decimal('1')
        """
        a = _convert_other(a, raiseit=True)
        r = a.__truediv__(b, context=self)
        wenn r is NotImplemented:
            raise TypeError("Unable to convert %s to Decimal" % b)
        sonst:
            return r

    def divide_int(self, a, b):
        """Divides two numbers and returns the integer part of the result.

        >>> ExtendedContext.divide_int(Decimal('2'), Decimal('3'))
        Decimal('0')
        >>> ExtendedContext.divide_int(Decimal('10'), Decimal('3'))
        Decimal('3')
        >>> ExtendedContext.divide_int(Decimal('1'), Decimal('0.3'))
        Decimal('3')
        >>> ExtendedContext.divide_int(10, 3)
        Decimal('3')
        >>> ExtendedContext.divide_int(Decimal(10), 3)
        Decimal('3')
        >>> ExtendedContext.divide_int(10, Decimal(3))
        Decimal('3')
        """
        a = _convert_other(a, raiseit=True)
        r = a.__floordiv__(b, context=self)
        wenn r is NotImplemented:
            raise TypeError("Unable to convert %s to Decimal" % b)
        sonst:
            return r

    def divmod(self, a, b):
        """Return (a // b, a % b).

        >>> ExtendedContext.divmod(Decimal(8), Decimal(3))
        (Decimal('2'), Decimal('2'))
        >>> ExtendedContext.divmod(Decimal(8), Decimal(4))
        (Decimal('2'), Decimal('0'))
        >>> ExtendedContext.divmod(8, 4)
        (Decimal('2'), Decimal('0'))
        >>> ExtendedContext.divmod(Decimal(8), 4)
        (Decimal('2'), Decimal('0'))
        >>> ExtendedContext.divmod(8, Decimal(4))
        (Decimal('2'), Decimal('0'))
        """
        a = _convert_other(a, raiseit=True)
        r = a.__divmod__(b, context=self)
        wenn r is NotImplemented:
            raise TypeError("Unable to convert %s to Decimal" % b)
        sonst:
            return r

    def exp(self, a):
        """Returns e ** a.

        >>> c = ExtendedContext.copy()
        >>> c.Emin = -999
        >>> c.Emax = 999
        >>> c.exp(Decimal('-Infinity'))
        Decimal('0')
        >>> c.exp(Decimal('-1'))
        Decimal('0.367879441')
        >>> c.exp(Decimal('0'))
        Decimal('1')
        >>> c.exp(Decimal('1'))
        Decimal('2.71828183')
        >>> c.exp(Decimal('0.693147181'))
        Decimal('2.00000000')
        >>> c.exp(Decimal('+Infinity'))
        Decimal('Infinity')
        >>> c.exp(10)
        Decimal('22026.4658')
        """
        a =_convert_other(a, raiseit=True)
        return a.exp(context=self)

    def fma(self, a, b, c):
        """Returns a multiplied by b, plus c.

        The first two operands are multiplied together, using multiply,
        the third operand is then added to the result of that
        multiplication, using add, all with only one final rounding.

        >>> ExtendedContext.fma(Decimal('3'), Decimal('5'), Decimal('7'))
        Decimal('22')
        >>> ExtendedContext.fma(Decimal('3'), Decimal('-5'), Decimal('7'))
        Decimal('-8')
        >>> ExtendedContext.fma(Decimal('888565290'), Decimal('1557.96930'), Decimal('-86087.7578'))
        Decimal('1.38435736E+12')
        >>> ExtendedContext.fma(1, 3, 4)
        Decimal('7')
        >>> ExtendedContext.fma(1, Decimal(3), 4)
        Decimal('7')
        >>> ExtendedContext.fma(1, 3, Decimal(4))
        Decimal('7')
        """
        a = _convert_other(a, raiseit=True)
        return a.fma(b, c, context=self)

    def is_canonical(self, a):
        """Return True wenn the operand is canonical; otherwise return False.

        Currently, the encoding of a Decimal instance is always
        canonical, so this method returns True fuer any Decimal.

        >>> ExtendedContext.is_canonical(Decimal('2.50'))
        True
        """
        wenn not isinstance(a, Decimal):
            raise TypeError("is_canonical requires a Decimal as an argument.")
        return a.is_canonical()

    def is_finite(self, a):
        """Return True wenn the operand is finite; otherwise return False.

        A Decimal instance is considered finite wenn it is neither
        infinite nor a NaN.

        >>> ExtendedContext.is_finite(Decimal('2.50'))
        True
        >>> ExtendedContext.is_finite(Decimal('-0.3'))
        True
        >>> ExtendedContext.is_finite(Decimal('0'))
        True
        >>> ExtendedContext.is_finite(Decimal('Inf'))
        False
        >>> ExtendedContext.is_finite(Decimal('NaN'))
        False
        >>> ExtendedContext.is_finite(1)
        True
        """
        a = _convert_other(a, raiseit=True)
        return a.is_finite()

    def is_infinite(self, a):
        """Return True wenn the operand is infinite; otherwise return False.

        >>> ExtendedContext.is_infinite(Decimal('2.50'))
        False
        >>> ExtendedContext.is_infinite(Decimal('-Inf'))
        True
        >>> ExtendedContext.is_infinite(Decimal('NaN'))
        False
        >>> ExtendedContext.is_infinite(1)
        False
        """
        a = _convert_other(a, raiseit=True)
        return a.is_infinite()

    def is_nan(self, a):
        """Return True wenn the operand is a qNaN or sNaN;
        otherwise return False.

        >>> ExtendedContext.is_nan(Decimal('2.50'))
        False
        >>> ExtendedContext.is_nan(Decimal('NaN'))
        True
        >>> ExtendedContext.is_nan(Decimal('-sNaN'))
        True
        >>> ExtendedContext.is_nan(1)
        False
        """
        a = _convert_other(a, raiseit=True)
        return a.is_nan()

    def is_normal(self, a):
        """Return True wenn the operand is a normal number;
        otherwise return False.

        >>> c = ExtendedContext.copy()
        >>> c.Emin = -999
        >>> c.Emax = 999
        >>> c.is_normal(Decimal('2.50'))
        True
        >>> c.is_normal(Decimal('0.1E-999'))
        False
        >>> c.is_normal(Decimal('0.00'))
        False
        >>> c.is_normal(Decimal('-Inf'))
        False
        >>> c.is_normal(Decimal('NaN'))
        False
        >>> c.is_normal(1)
        True
        """
        a = _convert_other(a, raiseit=True)
        return a.is_normal(context=self)

    def is_qnan(self, a):
        """Return True wenn the operand is a quiet NaN; otherwise return False.

        >>> ExtendedContext.is_qnan(Decimal('2.50'))
        False
        >>> ExtendedContext.is_qnan(Decimal('NaN'))
        True
        >>> ExtendedContext.is_qnan(Decimal('sNaN'))
        False
        >>> ExtendedContext.is_qnan(1)
        False
        """
        a = _convert_other(a, raiseit=True)
        return a.is_qnan()

    def is_signed(self, a):
        """Return True wenn the operand is negative; otherwise return False.

        >>> ExtendedContext.is_signed(Decimal('2.50'))
        False
        >>> ExtendedContext.is_signed(Decimal('-12'))
        True
        >>> ExtendedContext.is_signed(Decimal('-0'))
        True
        >>> ExtendedContext.is_signed(8)
        False
        >>> ExtendedContext.is_signed(-8)
        True
        """
        a = _convert_other(a, raiseit=True)
        return a.is_signed()

    def is_snan(self, a):
        """Return True wenn the operand is a signaling NaN;
        otherwise return False.

        >>> ExtendedContext.is_snan(Decimal('2.50'))
        False
        >>> ExtendedContext.is_snan(Decimal('NaN'))
        False
        >>> ExtendedContext.is_snan(Decimal('sNaN'))
        True
        >>> ExtendedContext.is_snan(1)
        False
        """
        a = _convert_other(a, raiseit=True)
        return a.is_snan()

    def is_subnormal(self, a):
        """Return True wenn the operand is subnormal; otherwise return False.

        >>> c = ExtendedContext.copy()
        >>> c.Emin = -999
        >>> c.Emax = 999
        >>> c.is_subnormal(Decimal('2.50'))
        False
        >>> c.is_subnormal(Decimal('0.1E-999'))
        True
        >>> c.is_subnormal(Decimal('0.00'))
        False
        >>> c.is_subnormal(Decimal('-Inf'))
        False
        >>> c.is_subnormal(Decimal('NaN'))
        False
        >>> c.is_subnormal(1)
        False
        """
        a = _convert_other(a, raiseit=True)
        return a.is_subnormal(context=self)

    def is_zero(self, a):
        """Return True wenn the operand is a zero; otherwise return False.

        >>> ExtendedContext.is_zero(Decimal('0'))
        True
        >>> ExtendedContext.is_zero(Decimal('2.50'))
        False
        >>> ExtendedContext.is_zero(Decimal('-0E+2'))
        True
        >>> ExtendedContext.is_zero(1)
        False
        >>> ExtendedContext.is_zero(0)
        True
        """
        a = _convert_other(a, raiseit=True)
        return a.is_zero()

    def ln(self, a):
        """Returns the natural (base e) logarithm of the operand.

        >>> c = ExtendedContext.copy()
        >>> c.Emin = -999
        >>> c.Emax = 999
        >>> c.ln(Decimal('0'))
        Decimal('-Infinity')
        >>> c.ln(Decimal('1.000'))
        Decimal('0')
        >>> c.ln(Decimal('2.71828183'))
        Decimal('1.00000000')
        >>> c.ln(Decimal('10'))
        Decimal('2.30258509')
        >>> c.ln(Decimal('+Infinity'))
        Decimal('Infinity')
        >>> c.ln(1)
        Decimal('0')
        """
        a = _convert_other(a, raiseit=True)
        return a.ln(context=self)

    def log10(self, a):
        """Returns the base 10 logarithm of the operand.

        >>> c = ExtendedContext.copy()
        >>> c.Emin = -999
        >>> c.Emax = 999
        >>> c.log10(Decimal('0'))
        Decimal('-Infinity')
        >>> c.log10(Decimal('0.001'))
        Decimal('-3')
        >>> c.log10(Decimal('1.000'))
        Decimal('0')
        >>> c.log10(Decimal('2'))
        Decimal('0.301029996')
        >>> c.log10(Decimal('10'))
        Decimal('1')
        >>> c.log10(Decimal('70'))
        Decimal('1.84509804')
        >>> c.log10(Decimal('+Infinity'))
        Decimal('Infinity')
        >>> c.log10(0)
        Decimal('-Infinity')
        >>> c.log10(1)
        Decimal('0')
        """
        a = _convert_other(a, raiseit=True)
        return a.log10(context=self)

    def logb(self, a):
        """ Returns the exponent of the magnitude of the operand's MSD.

        The result is the integer which is the exponent of the magnitude
        of the most significant digit of the operand (as though the
        operand were truncated to a single digit while maintaining the
        value of that digit and without limiting the resulting exponent).

        >>> ExtendedContext.logb(Decimal('250'))
        Decimal('2')
        >>> ExtendedContext.logb(Decimal('2.50'))
        Decimal('0')
        >>> ExtendedContext.logb(Decimal('0.03'))
        Decimal('-2')
        >>> ExtendedContext.logb(Decimal('0'))
        Decimal('-Infinity')
        >>> ExtendedContext.logb(1)
        Decimal('0')
        >>> ExtendedContext.logb(10)
        Decimal('1')
        >>> ExtendedContext.logb(100)
        Decimal('2')
        """
        a = _convert_other(a, raiseit=True)
        return a.logb(context=self)

    def logical_and(self, a, b):
        """Applies the logical operation 'and' between each operand's digits.

        The operands must be both logical numbers.

        >>> ExtendedContext.logical_and(Decimal('0'), Decimal('0'))
        Decimal('0')
        >>> ExtendedContext.logical_and(Decimal('0'), Decimal('1'))
        Decimal('0')
        >>> ExtendedContext.logical_and(Decimal('1'), Decimal('0'))
        Decimal('0')
        >>> ExtendedContext.logical_and(Decimal('1'), Decimal('1'))
        Decimal('1')
        >>> ExtendedContext.logical_and(Decimal('1100'), Decimal('1010'))
        Decimal('1000')
        >>> ExtendedContext.logical_and(Decimal('1111'), Decimal('10'))
        Decimal('10')
        >>> ExtendedContext.logical_and(110, 1101)
        Decimal('100')
        >>> ExtendedContext.logical_and(Decimal(110), 1101)
        Decimal('100')
        >>> ExtendedContext.logical_and(110, Decimal(1101))
        Decimal('100')
        """
        a = _convert_other(a, raiseit=True)
        return a.logical_and(b, context=self)

    def logical_invert(self, a):
        """Invert all the digits in the operand.

        The operand must be a logical number.

        >>> ExtendedContext.logical_invert(Decimal('0'))
        Decimal('111111111')
        >>> ExtendedContext.logical_invert(Decimal('1'))
        Decimal('111111110')
        >>> ExtendedContext.logical_invert(Decimal('111111111'))
        Decimal('0')
        >>> ExtendedContext.logical_invert(Decimal('101010101'))
        Decimal('10101010')
        >>> ExtendedContext.logical_invert(1101)
        Decimal('111110010')
        """
        a = _convert_other(a, raiseit=True)
        return a.logical_invert(context=self)

    def logical_or(self, a, b):
        """Applies the logical operation 'or' between each operand's digits.

        The operands must be both logical numbers.

        >>> ExtendedContext.logical_or(Decimal('0'), Decimal('0'))
        Decimal('0')
        >>> ExtendedContext.logical_or(Decimal('0'), Decimal('1'))
        Decimal('1')
        >>> ExtendedContext.logical_or(Decimal('1'), Decimal('0'))
        Decimal('1')
        >>> ExtendedContext.logical_or(Decimal('1'), Decimal('1'))
        Decimal('1')
        >>> ExtendedContext.logical_or(Decimal('1100'), Decimal('1010'))
        Decimal('1110')
        >>> ExtendedContext.logical_or(Decimal('1110'), Decimal('10'))
        Decimal('1110')
        >>> ExtendedContext.logical_or(110, 1101)
        Decimal('1111')
        >>> ExtendedContext.logical_or(Decimal(110), 1101)
        Decimal('1111')
        >>> ExtendedContext.logical_or(110, Decimal(1101))
        Decimal('1111')
        """
        a = _convert_other(a, raiseit=True)
        return a.logical_or(b, context=self)

    def logical_xor(self, a, b):
        """Applies the logical operation 'xor' between each operand's digits.

        The operands must be both logical numbers.

        >>> ExtendedContext.logical_xor(Decimal('0'), Decimal('0'))
        Decimal('0')
        >>> ExtendedContext.logical_xor(Decimal('0'), Decimal('1'))
        Decimal('1')
        >>> ExtendedContext.logical_xor(Decimal('1'), Decimal('0'))
        Decimal('1')
        >>> ExtendedContext.logical_xor(Decimal('1'), Decimal('1'))
        Decimal('0')
        >>> ExtendedContext.logical_xor(Decimal('1100'), Decimal('1010'))
        Decimal('110')
        >>> ExtendedContext.logical_xor(Decimal('1111'), Decimal('10'))
        Decimal('1101')
        >>> ExtendedContext.logical_xor(110, 1101)
        Decimal('1011')
        >>> ExtendedContext.logical_xor(Decimal(110), 1101)
        Decimal('1011')
        >>> ExtendedContext.logical_xor(110, Decimal(1101))
        Decimal('1011')
        """
        a = _convert_other(a, raiseit=True)
        return a.logical_xor(b, context=self)

    def max(self, a, b):
        """max compares two values numerically and returns the maximum.

        If either operand is a NaN then the general rules apply.
        Otherwise, the operands are compared as though by the compare
        operation.  If they are numerically equal then the left-hand operand
        is chosen as the result.  Otherwise the maximum (closer to positive
        infinity) of the two operands is chosen as the result.

        >>> ExtendedContext.max(Decimal('3'), Decimal('2'))
        Decimal('3')
        >>> ExtendedContext.max(Decimal('-10'), Decimal('3'))
        Decimal('3')
        >>> ExtendedContext.max(Decimal('1.0'), Decimal('1'))
        Decimal('1')
        >>> ExtendedContext.max(Decimal('7'), Decimal('NaN'))
        Decimal('7')
        >>> ExtendedContext.max(1, 2)
        Decimal('2')
        >>> ExtendedContext.max(Decimal(1), 2)
        Decimal('2')
        >>> ExtendedContext.max(1, Decimal(2))
        Decimal('2')
        """
        a = _convert_other(a, raiseit=True)
        return a.max(b, context=self)

    def max_mag(self, a, b):
        """Compares the values numerically with their sign ignored.

        >>> ExtendedContext.max_mag(Decimal('7'), Decimal('NaN'))
        Decimal('7')
        >>> ExtendedContext.max_mag(Decimal('7'), Decimal('-10'))
        Decimal('-10')
        >>> ExtendedContext.max_mag(1, -2)
        Decimal('-2')
        >>> ExtendedContext.max_mag(Decimal(1), -2)
        Decimal('-2')
        >>> ExtendedContext.max_mag(1, Decimal(-2))
        Decimal('-2')
        """
        a = _convert_other(a, raiseit=True)
        return a.max_mag(b, context=self)

    def min(self, a, b):
        """min compares two values numerically and returns the minimum.

        If either operand is a NaN then the general rules apply.
        Otherwise, the operands are compared as though by the compare
        operation.  If they are numerically equal then the left-hand operand
        is chosen as the result.  Otherwise the minimum (closer to negative
        infinity) of the two operands is chosen as the result.

        >>> ExtendedContext.min(Decimal('3'), Decimal('2'))
        Decimal('2')
        >>> ExtendedContext.min(Decimal('-10'), Decimal('3'))
        Decimal('-10')
        >>> ExtendedContext.min(Decimal('1.0'), Decimal('1'))
        Decimal('1.0')
        >>> ExtendedContext.min(Decimal('7'), Decimal('NaN'))
        Decimal('7')
        >>> ExtendedContext.min(1, 2)
        Decimal('1')
        >>> ExtendedContext.min(Decimal(1), 2)
        Decimal('1')
        >>> ExtendedContext.min(1, Decimal(29))
        Decimal('1')
        """
        a = _convert_other(a, raiseit=True)
        return a.min(b, context=self)

    def min_mag(self, a, b):
        """Compares the values numerically with their sign ignored.

        >>> ExtendedContext.min_mag(Decimal('3'), Decimal('-2'))
        Decimal('-2')
        >>> ExtendedContext.min_mag(Decimal('-3'), Decimal('NaN'))
        Decimal('-3')
        >>> ExtendedContext.min_mag(1, -2)
        Decimal('1')
        >>> ExtendedContext.min_mag(Decimal(1), -2)
        Decimal('1')
        >>> ExtendedContext.min_mag(1, Decimal(-2))
        Decimal('1')
        """
        a = _convert_other(a, raiseit=True)
        return a.min_mag(b, context=self)

    def minus(self, a):
        """Minus corresponds to unary prefix minus in Python.

        The operation is evaluated using the same rules as subtract; the
        operation minus(a) is calculated as subtract('0', a) where the '0'
        has the same exponent as the operand.

        >>> ExtendedContext.minus(Decimal('1.3'))
        Decimal('-1.3')
        >>> ExtendedContext.minus(Decimal('-1.3'))
        Decimal('1.3')
        >>> ExtendedContext.minus(1)
        Decimal('-1')
        """
        a = _convert_other(a, raiseit=True)
        return a.__neg__(context=self)

    def multiply(self, a, b):
        """multiply multiplies two operands.

        If either operand is a special value then the general rules apply.
        Otherwise, the operands are multiplied together
        ('long multiplication'), resulting in a number which may be as long as
        the sum of the lengths of the two operands.

        >>> ExtendedContext.multiply(Decimal('1.20'), Decimal('3'))
        Decimal('3.60')
        >>> ExtendedContext.multiply(Decimal('7'), Decimal('3'))
        Decimal('21')
        >>> ExtendedContext.multiply(Decimal('0.9'), Decimal('0.8'))
        Decimal('0.72')
        >>> ExtendedContext.multiply(Decimal('0.9'), Decimal('-0'))
        Decimal('-0.0')
        >>> ExtendedContext.multiply(Decimal('654321'), Decimal('654321'))
        Decimal('4.28135971E+11')
        >>> ExtendedContext.multiply(7, 7)
        Decimal('49')
        >>> ExtendedContext.multiply(Decimal(7), 7)
        Decimal('49')
        >>> ExtendedContext.multiply(7, Decimal(7))
        Decimal('49')
        """
        a = _convert_other(a, raiseit=True)
        r = a.__mul__(b, context=self)
        wenn r is NotImplemented:
            raise TypeError("Unable to convert %s to Decimal" % b)
        sonst:
            return r

    def next_minus(self, a):
        """Returns the largest representable number smaller than a.

        >>> c = ExtendedContext.copy()
        >>> c.Emin = -999
        >>> c.Emax = 999
        >>> ExtendedContext.next_minus(Decimal('1'))
        Decimal('0.999999999')
        >>> c.next_minus(Decimal('1E-1007'))
        Decimal('0E-1007')
        >>> ExtendedContext.next_minus(Decimal('-1.00000003'))
        Decimal('-1.00000004')
        >>> c.next_minus(Decimal('Infinity'))
        Decimal('9.99999999E+999')
        >>> c.next_minus(1)
        Decimal('0.999999999')
        """
        a = _convert_other(a, raiseit=True)
        return a.next_minus(context=self)

    def next_plus(self, a):
        """Returns the smallest representable number larger than a.

        >>> c = ExtendedContext.copy()
        >>> c.Emin = -999
        >>> c.Emax = 999
        >>> ExtendedContext.next_plus(Decimal('1'))
        Decimal('1.00000001')
        >>> c.next_plus(Decimal('-1E-1007'))
        Decimal('-0E-1007')
        >>> ExtendedContext.next_plus(Decimal('-1.00000003'))
        Decimal('-1.00000002')
        >>> c.next_plus(Decimal('-Infinity'))
        Decimal('-9.99999999E+999')
        >>> c.next_plus(1)
        Decimal('1.00000001')
        """
        a = _convert_other(a, raiseit=True)
        return a.next_plus(context=self)

    def next_toward(self, a, b):
        """Returns the number closest to a, in direction towards b.

        The result is the closest representable number from the first
        operand (but not the first operand) that is in the direction
        towards the second operand, unless the operands have the same
        value.

        >>> c = ExtendedContext.copy()
        >>> c.Emin = -999
        >>> c.Emax = 999
        >>> c.next_toward(Decimal('1'), Decimal('2'))
        Decimal('1.00000001')
        >>> c.next_toward(Decimal('-1E-1007'), Decimal('1'))
        Decimal('-0E-1007')
        >>> c.next_toward(Decimal('-1.00000003'), Decimal('0'))
        Decimal('-1.00000002')
        >>> c.next_toward(Decimal('1'), Decimal('0'))
        Decimal('0.999999999')
        >>> c.next_toward(Decimal('1E-1007'), Decimal('-100'))
        Decimal('0E-1007')
        >>> c.next_toward(Decimal('-1.00000003'), Decimal('-10'))
        Decimal('-1.00000004')
        >>> c.next_toward(Decimal('0.00'), Decimal('-0.0000'))
        Decimal('-0.00')
        >>> c.next_toward(0, 1)
        Decimal('1E-1007')
        >>> c.next_toward(Decimal(0), 1)
        Decimal('1E-1007')
        >>> c.next_toward(0, Decimal(1))
        Decimal('1E-1007')
        """
        a = _convert_other(a, raiseit=True)
        return a.next_toward(b, context=self)

    def normalize(self, a):
        """normalize reduces an operand to its simplest form.

        Essentially a plus operation with all trailing zeros removed from the
        result.

        >>> ExtendedContext.normalize(Decimal('2.1'))
        Decimal('2.1')
        >>> ExtendedContext.normalize(Decimal('-2.0'))
        Decimal('-2')
        >>> ExtendedContext.normalize(Decimal('1.200'))
        Decimal('1.2')
        >>> ExtendedContext.normalize(Decimal('-120'))
        Decimal('-1.2E+2')
        >>> ExtendedContext.normalize(Decimal('120.00'))
        Decimal('1.2E+2')
        >>> ExtendedContext.normalize(Decimal('0.00'))
        Decimal('0')
        >>> ExtendedContext.normalize(6)
        Decimal('6')
        """
        a = _convert_other(a, raiseit=True)
        return a.normalize(context=self)

    def number_class(self, a):
        """Returns an indication of the klasse of the operand.

        The klasse is one of the following strings:
          -sNaN
          -NaN
          -Infinity
          -Normal
          -Subnormal
          -Zero
          +Zero
          +Subnormal
          +Normal
          +Infinity

        >>> c = ExtendedContext.copy()
        >>> c.Emin = -999
        >>> c.Emax = 999
        >>> c.number_class(Decimal('Infinity'))
        '+Infinity'
        >>> c.number_class(Decimal('1E-10'))
        '+Normal'
        >>> c.number_class(Decimal('2.50'))
        '+Normal'
        >>> c.number_class(Decimal('0.1E-999'))
        '+Subnormal'
        >>> c.number_class(Decimal('0'))
        '+Zero'
        >>> c.number_class(Decimal('-0'))
        '-Zero'
        >>> c.number_class(Decimal('-0.1E-999'))
        '-Subnormal'
        >>> c.number_class(Decimal('-1E-10'))
        '-Normal'
        >>> c.number_class(Decimal('-2.50'))
        '-Normal'
        >>> c.number_class(Decimal('-Infinity'))
        '-Infinity'
        >>> c.number_class(Decimal('NaN'))
        'NaN'
        >>> c.number_class(Decimal('-NaN'))
        'NaN'
        >>> c.number_class(Decimal('sNaN'))
        'sNaN'
        >>> c.number_class(123)
        '+Normal'
        """
        a = _convert_other(a, raiseit=True)
        return a.number_class(context=self)

    def plus(self, a):
        """Plus corresponds to unary prefix plus in Python.

        The operation is evaluated using the same rules as add; the
        operation plus(a) is calculated as add('0', a) where the '0'
        has the same exponent as the operand.

        >>> ExtendedContext.plus(Decimal('1.3'))
        Decimal('1.3')
        >>> ExtendedContext.plus(Decimal('-1.3'))
        Decimal('-1.3')
        >>> ExtendedContext.plus(-1)
        Decimal('-1')
        """
        a = _convert_other(a, raiseit=True)
        return a.__pos__(context=self)

    def power(self, a, b, modulo=None):
        """Raises a to the power of b, to modulo wenn given.

        With two arguments, compute a**b.  If a is negative then b
        must be integral.  The result will be inexact unless b is
        integral and the result is finite and can be expressed exactly
        in 'precision' digits.

        With three arguments, compute (a**b) % modulo.  For the
        three argument form, the following restrictions on the
        arguments hold:

         - all three arguments must be integral
         - b must be nonnegative
         - at least one of a or b must be nonzero
         - modulo must be nonzero and have at most 'precision' digits

        The result of pow(a, b, modulo) is identical to the result
        that would be obtained by computing (a**b) % modulo with
        unbounded precision, but is computed more efficiently.  It is
        always exact.

        >>> c = ExtendedContext.copy()
        >>> c.Emin = -999
        >>> c.Emax = 999
        >>> c.power(Decimal('2'), Decimal('3'))
        Decimal('8')
        >>> c.power(Decimal('-2'), Decimal('3'))
        Decimal('-8')
        >>> c.power(Decimal('2'), Decimal('-3'))
        Decimal('0.125')
        >>> c.power(Decimal('1.7'), Decimal('8'))
        Decimal('69.7575744')
        >>> c.power(Decimal('10'), Decimal('0.301029996'))
        Decimal('2.00000000')
        >>> c.power(Decimal('Infinity'), Decimal('-1'))
        Decimal('0')
        >>> c.power(Decimal('Infinity'), Decimal('0'))
        Decimal('1')
        >>> c.power(Decimal('Infinity'), Decimal('1'))
        Decimal('Infinity')
        >>> c.power(Decimal('-Infinity'), Decimal('-1'))
        Decimal('-0')
        >>> c.power(Decimal('-Infinity'), Decimal('0'))
        Decimal('1')
        >>> c.power(Decimal('-Infinity'), Decimal('1'))
        Decimal('-Infinity')
        >>> c.power(Decimal('-Infinity'), Decimal('2'))
        Decimal('Infinity')
        >>> c.power(Decimal('0'), Decimal('0'))
        Decimal('NaN')

        >>> c.power(Decimal('3'), Decimal('7'), Decimal('16'))
        Decimal('11')
        >>> c.power(Decimal('-3'), Decimal('7'), Decimal('16'))
        Decimal('-11')
        >>> c.power(Decimal('-3'), Decimal('8'), Decimal('16'))
        Decimal('1')
        >>> c.power(Decimal('3'), Decimal('7'), Decimal('-16'))
        Decimal('11')
        >>> c.power(Decimal('23E12345'), Decimal('67E189'), Decimal('123456789'))
        Decimal('11729830')
        >>> c.power(Decimal('-0'), Decimal('17'), Decimal('1729'))
        Decimal('-0')
        >>> c.power(Decimal('-23'), Decimal('0'), Decimal('65537'))
        Decimal('1')
        >>> ExtendedContext.power(7, 7)
        Decimal('823543')
        >>> ExtendedContext.power(Decimal(7), 7)
        Decimal('823543')
        >>> ExtendedContext.power(7, Decimal(7), 2)
        Decimal('1')
        """
        a = _convert_other(a, raiseit=True)
        r = a.__pow__(b, modulo, context=self)
        wenn r is NotImplemented:
            raise TypeError("Unable to convert %s to Decimal" % b)
        sonst:
            return r

    def quantize(self, a, b):
        """Returns a value equal to 'a' (rounded), having the exponent of 'b'.

        The coefficient of the result is derived from that of the left-hand
        operand.  It may be rounded using the current rounding setting (if the
        exponent is being increased), multiplied by a positive power of ten (if
        the exponent is being decreased), or is unchanged (if the exponent is
        already equal to that of the right-hand operand).

        Unlike other operations, wenn the length of the coefficient after the
        quantize operation would be greater than precision then an Invalid
        operation condition is raised.  This guarantees that, unless there is
        an error condition, the exponent of the result of a quantize is always
        equal to that of the right-hand operand.

        Also unlike other operations, quantize will never raise Underflow, even
        wenn the result is subnormal and inexact.

        >>> ExtendedContext.quantize(Decimal('2.17'), Decimal('0.001'))
        Decimal('2.170')
        >>> ExtendedContext.quantize(Decimal('2.17'), Decimal('0.01'))
        Decimal('2.17')
        >>> ExtendedContext.quantize(Decimal('2.17'), Decimal('0.1'))
        Decimal('2.2')
        >>> ExtendedContext.quantize(Decimal('2.17'), Decimal('1e+0'))
        Decimal('2')
        >>> ExtendedContext.quantize(Decimal('2.17'), Decimal('1e+1'))
        Decimal('0E+1')
        >>> ExtendedContext.quantize(Decimal('-Inf'), Decimal('Infinity'))
        Decimal('-Infinity')
        >>> ExtendedContext.quantize(Decimal('2'), Decimal('Infinity'))
        Decimal('NaN')
        >>> ExtendedContext.quantize(Decimal('-0.1'), Decimal('1'))
        Decimal('-0')
        >>> ExtendedContext.quantize(Decimal('-0'), Decimal('1e+5'))
        Decimal('-0E+5')
        >>> ExtendedContext.quantize(Decimal('+35236450.6'), Decimal('1e-2'))
        Decimal('NaN')
        >>> ExtendedContext.quantize(Decimal('-35236450.6'), Decimal('1e-2'))
        Decimal('NaN')
        >>> ExtendedContext.quantize(Decimal('217'), Decimal('1e-1'))
        Decimal('217.0')
        >>> ExtendedContext.quantize(Decimal('217'), Decimal('1e-0'))
        Decimal('217')
        >>> ExtendedContext.quantize(Decimal('217'), Decimal('1e+1'))
        Decimal('2.2E+2')
        >>> ExtendedContext.quantize(Decimal('217'), Decimal('1e+2'))
        Decimal('2E+2')
        >>> ExtendedContext.quantize(1, 2)
        Decimal('1')
        >>> ExtendedContext.quantize(Decimal(1), 2)
        Decimal('1')
        >>> ExtendedContext.quantize(1, Decimal(2))
        Decimal('1')
        """
        a = _convert_other(a, raiseit=True)
        return a.quantize(b, context=self)

    def radix(self):
        """Just returns 10, as this is Decimal, :)

        >>> ExtendedContext.radix()
        Decimal('10')
        """
        return Decimal(10)

    def remainder(self, a, b):
        """Returns the remainder from integer division.

        The result is the residue of the dividend after the operation of
        calculating integer division as described fuer divide-integer, rounded
        to precision digits wenn necessary.  The sign of the result, if
        non-zero, is the same as that of the original dividend.

        This operation will fail under the same conditions as integer division
        (that is, wenn integer division on the same two operands would fail, the
        remainder cannot be calculated).

        >>> ExtendedContext.remainder(Decimal('2.1'), Decimal('3'))
        Decimal('2.1')
        >>> ExtendedContext.remainder(Decimal('10'), Decimal('3'))
        Decimal('1')
        >>> ExtendedContext.remainder(Decimal('-10'), Decimal('3'))
        Decimal('-1')
        >>> ExtendedContext.remainder(Decimal('10.2'), Decimal('1'))
        Decimal('0.2')
        >>> ExtendedContext.remainder(Decimal('10'), Decimal('0.3'))
        Decimal('0.1')
        >>> ExtendedContext.remainder(Decimal('3.6'), Decimal('1.3'))
        Decimal('1.0')
        >>> ExtendedContext.remainder(22, 6)
        Decimal('4')
        >>> ExtendedContext.remainder(Decimal(22), 6)
        Decimal('4')
        >>> ExtendedContext.remainder(22, Decimal(6))
        Decimal('4')
        """
        a = _convert_other(a, raiseit=True)
        r = a.__mod__(b, context=self)
        wenn r is NotImplemented:
            raise TypeError("Unable to convert %s to Decimal" % b)
        sonst:
            return r

    def remainder_near(self, a, b):
        """Returns to be "a - b * n", where n is the integer nearest the exact
        value of "x / b" (if two integers are equally near then the even one
        is chosen).  If the result is equal to 0 then its sign will be the
        sign of a.

        This operation will fail under the same conditions as integer division
        (that is, wenn integer division on the same two operands would fail, the
        remainder cannot be calculated).

        >>> ExtendedContext.remainder_near(Decimal('2.1'), Decimal('3'))
        Decimal('-0.9')
        >>> ExtendedContext.remainder_near(Decimal('10'), Decimal('6'))
        Decimal('-2')
        >>> ExtendedContext.remainder_near(Decimal('10'), Decimal('3'))
        Decimal('1')
        >>> ExtendedContext.remainder_near(Decimal('-10'), Decimal('3'))
        Decimal('-1')
        >>> ExtendedContext.remainder_near(Decimal('10.2'), Decimal('1'))
        Decimal('0.2')
        >>> ExtendedContext.remainder_near(Decimal('10'), Decimal('0.3'))
        Decimal('0.1')
        >>> ExtendedContext.remainder_near(Decimal('3.6'), Decimal('1.3'))
        Decimal('-0.3')
        >>> ExtendedContext.remainder_near(3, 11)
        Decimal('3')
        >>> ExtendedContext.remainder_near(Decimal(3), 11)
        Decimal('3')
        >>> ExtendedContext.remainder_near(3, Decimal(11))
        Decimal('3')
        """
        a = _convert_other(a, raiseit=True)
        return a.remainder_near(b, context=self)

    def rotate(self, a, b):
        """Returns a rotated copy of a, b times.

        The coefficient of the result is a rotated copy of the digits in
        the coefficient of the first operand.  The number of places of
        rotation is taken from the absolute value of the second operand,
        with the rotation being to the left wenn the second operand is
        positive or to the right otherwise.

        >>> ExtendedContext.rotate(Decimal('34'), Decimal('8'))
        Decimal('400000003')
        >>> ExtendedContext.rotate(Decimal('12'), Decimal('9'))
        Decimal('12')
        >>> ExtendedContext.rotate(Decimal('123456789'), Decimal('-2'))
        Decimal('891234567')
        >>> ExtendedContext.rotate(Decimal('123456789'), Decimal('0'))
        Decimal('123456789')
        >>> ExtendedContext.rotate(Decimal('123456789'), Decimal('+2'))
        Decimal('345678912')
        >>> ExtendedContext.rotate(1333333, 1)
        Decimal('13333330')
        >>> ExtendedContext.rotate(Decimal(1333333), 1)
        Decimal('13333330')
        >>> ExtendedContext.rotate(1333333, Decimal(1))
        Decimal('13333330')
        """
        a = _convert_other(a, raiseit=True)
        return a.rotate(b, context=self)

    def same_quantum(self, a, b):
        """Returns True wenn the two operands have the same exponent.

        The result is never affected by either the sign or the coefficient of
        either operand.

        >>> ExtendedContext.same_quantum(Decimal('2.17'), Decimal('0.001'))
        False
        >>> ExtendedContext.same_quantum(Decimal('2.17'), Decimal('0.01'))
        True
        >>> ExtendedContext.same_quantum(Decimal('2.17'), Decimal('1'))
        False
        >>> ExtendedContext.same_quantum(Decimal('Inf'), Decimal('-Inf'))
        True
        >>> ExtendedContext.same_quantum(10000, -1)
        True
        >>> ExtendedContext.same_quantum(Decimal(10000), -1)
        True
        >>> ExtendedContext.same_quantum(10000, Decimal(-1))
        True
        """
        a = _convert_other(a, raiseit=True)
        return a.same_quantum(b)

    def scaleb (self, a, b):
        """Returns the first operand after adding the second value its exp.

        >>> ExtendedContext.scaleb(Decimal('7.50'), Decimal('-2'))
        Decimal('0.0750')
        >>> ExtendedContext.scaleb(Decimal('7.50'), Decimal('0'))
        Decimal('7.50')
        >>> ExtendedContext.scaleb(Decimal('7.50'), Decimal('3'))
        Decimal('7.50E+3')
        >>> ExtendedContext.scaleb(1, 4)
        Decimal('1E+4')
        >>> ExtendedContext.scaleb(Decimal(1), 4)
        Decimal('1E+4')
        >>> ExtendedContext.scaleb(1, Decimal(4))
        Decimal('1E+4')
        """
        a = _convert_other(a, raiseit=True)
        return a.scaleb(b, context=self)

    def shift(self, a, b):
        """Returns a shifted copy of a, b times.

        The coefficient of the result is a shifted copy of the digits
        in the coefficient of the first operand.  The number of places
        to shift is taken from the absolute value of the second operand,
        with the shift being to the left wenn the second operand is
        positive or to the right otherwise.  Digits shifted into the
        coefficient are zeros.

        >>> ExtendedContext.shift(Decimal('34'), Decimal('8'))
        Decimal('400000000')
        >>> ExtendedContext.shift(Decimal('12'), Decimal('9'))
        Decimal('0')
        >>> ExtendedContext.shift(Decimal('123456789'), Decimal('-2'))
        Decimal('1234567')
        >>> ExtendedContext.shift(Decimal('123456789'), Decimal('0'))
        Decimal('123456789')
        >>> ExtendedContext.shift(Decimal('123456789'), Decimal('+2'))
        Decimal('345678900')
        >>> ExtendedContext.shift(88888888, 2)
        Decimal('888888800')
        >>> ExtendedContext.shift(Decimal(88888888), 2)
        Decimal('888888800')
        >>> ExtendedContext.shift(88888888, Decimal(2))
        Decimal('888888800')
        """
        a = _convert_other(a, raiseit=True)
        return a.shift(b, context=self)

    def sqrt(self, a):
        """Square root of a non-negative number to context precision.

        If the result must be inexact, it is rounded using the round-half-even
        algorithm.

        >>> ExtendedContext.sqrt(Decimal('0'))
        Decimal('0')
        >>> ExtendedContext.sqrt(Decimal('-0'))
        Decimal('-0')
        >>> ExtendedContext.sqrt(Decimal('0.39'))
        Decimal('0.624499800')
        >>> ExtendedContext.sqrt(Decimal('100'))
        Decimal('10')
        >>> ExtendedContext.sqrt(Decimal('1'))
        Decimal('1')
        >>> ExtendedContext.sqrt(Decimal('1.0'))
        Decimal('1.0')
        >>> ExtendedContext.sqrt(Decimal('1.00'))
        Decimal('1.0')
        >>> ExtendedContext.sqrt(Decimal('7'))
        Decimal('2.64575131')
        >>> ExtendedContext.sqrt(Decimal('10'))
        Decimal('3.16227766')
        >>> ExtendedContext.sqrt(2)
        Decimal('1.41421356')
        >>> ExtendedContext.prec
        9
        """
        a = _convert_other(a, raiseit=True)
        return a.sqrt(context=self)

    def subtract(self, a, b):
        """Return the difference between the two operands.

        >>> ExtendedContext.subtract(Decimal('1.3'), Decimal('1.07'))
        Decimal('0.23')
        >>> ExtendedContext.subtract(Decimal('1.3'), Decimal('1.30'))
        Decimal('0.00')
        >>> ExtendedContext.subtract(Decimal('1.3'), Decimal('2.07'))
        Decimal('-0.77')
        >>> ExtendedContext.subtract(8, 5)
        Decimal('3')
        >>> ExtendedContext.subtract(Decimal(8), 5)
        Decimal('3')
        >>> ExtendedContext.subtract(8, Decimal(5))
        Decimal('3')
        """
        a = _convert_other(a, raiseit=True)
        r = a.__sub__(b, context=self)
        wenn r is NotImplemented:
            raise TypeError("Unable to convert %s to Decimal" % b)
        sonst:
            return r

    def to_eng_string(self, a):
        """Convert to a string, using engineering notation wenn an exponent is needed.

        Engineering notation has an exponent which is a multiple of 3.  This
        can leave up to 3 digits to the left of the decimal place and may
        require the addition of either one or two trailing zeros.

        The operation is not affected by the context.

        >>> ExtendedContext.to_eng_string(Decimal('123E+1'))
        '1.23E+3'
        >>> ExtendedContext.to_eng_string(Decimal('123E+3'))
        '123E+3'
        >>> ExtendedContext.to_eng_string(Decimal('123E-10'))
        '12.3E-9'
        >>> ExtendedContext.to_eng_string(Decimal('-123E-12'))
        '-123E-12'
        >>> ExtendedContext.to_eng_string(Decimal('7E-7'))
        '700E-9'
        >>> ExtendedContext.to_eng_string(Decimal('7E+1'))
        '70'
        >>> ExtendedContext.to_eng_string(Decimal('0E+1'))
        '0.00E+3'

        """
        a = _convert_other(a, raiseit=True)
        return a.to_eng_string(context=self)

    def to_sci_string(self, a):
        """Converts a number to a string, using scientific notation.

        The operation is not affected by the context.
        """
        a = _convert_other(a, raiseit=True)
        return a.__str__(context=self)

    def to_integral_exact(self, a):
        """Rounds to an integer.

        When the operand has a negative exponent, the result is the same
        as using the quantize() operation using the given operand as the
        left-hand-operand, 1E+0 as the right-hand-operand, and the precision
        of the operand as the precision setting; Inexact and Rounded flags
        are allowed in this operation.  The rounding mode is taken from the
        context.

        >>> ExtendedContext.to_integral_exact(Decimal('2.1'))
        Decimal('2')
        >>> ExtendedContext.to_integral_exact(Decimal('100'))
        Decimal('100')
        >>> ExtendedContext.to_integral_exact(Decimal('100.0'))
        Decimal('100')
        >>> ExtendedContext.to_integral_exact(Decimal('101.5'))
        Decimal('102')
        >>> ExtendedContext.to_integral_exact(Decimal('-101.5'))
        Decimal('-102')
        >>> ExtendedContext.to_integral_exact(Decimal('10E+5'))
        Decimal('1.0E+6')
        >>> ExtendedContext.to_integral_exact(Decimal('7.89E+77'))
        Decimal('7.89E+77')
        >>> ExtendedContext.to_integral_exact(Decimal('-Inf'))
        Decimal('-Infinity')
        """
        a = _convert_other(a, raiseit=True)
        return a.to_integral_exact(context=self)

    def to_integral_value(self, a):
        """Rounds to an integer.

        When the operand has a negative exponent, the result is the same
        as using the quantize() operation using the given operand as the
        left-hand-operand, 1E+0 as the right-hand-operand, and the precision
        of the operand as the precision setting, except that no flags will
        be set.  The rounding mode is taken from the context.

        >>> ExtendedContext.to_integral_value(Decimal('2.1'))
        Decimal('2')
        >>> ExtendedContext.to_integral_value(Decimal('100'))
        Decimal('100')
        >>> ExtendedContext.to_integral_value(Decimal('100.0'))
        Decimal('100')
        >>> ExtendedContext.to_integral_value(Decimal('101.5'))
        Decimal('102')
        >>> ExtendedContext.to_integral_value(Decimal('-101.5'))
        Decimal('-102')
        >>> ExtendedContext.to_integral_value(Decimal('10E+5'))
        Decimal('1.0E+6')
        >>> ExtendedContext.to_integral_value(Decimal('7.89E+77'))
        Decimal('7.89E+77')
        >>> ExtendedContext.to_integral_value(Decimal('-Inf'))
        Decimal('-Infinity')
        """
        a = _convert_other(a, raiseit=True)
        return a.to_integral_value(context=self)

    # the method name changed, but we provide also the old one, fuer compatibility
    to_integral = to_integral_value

klasse _WorkRep(object):
    __slots__ = ('sign','int','exp')
    # sign: 0 or 1
    # int:  int
    # exp:  None, int, or string

    def __init__(self, value=None):
        wenn value is None:
            self.sign = None
            self.int = 0
            self.exp = None
        sowenn isinstance(value, Decimal):
            self.sign = value._sign
            self.int = int(value._int)
            self.exp = value._exp
        sonst:
            # assert isinstance(value, tuple)
            self.sign = value[0]
            self.int = value[1]
            self.exp = value[2]

    def __repr__(self):
        return "(%r, %r, %r)" % (self.sign, self.int, self.exp)



def _normalize(op1, op2, prec = 0):
    """Normalizes op1, op2 to have the same exp and length of coefficient.

    Done during addition.
    """
    wenn op1.exp < op2.exp:
        tmp = op2
        other = op1
    sonst:
        tmp = op1
        other = op2

    # Let exp = min(tmp.exp - 1, tmp.adjusted() - precision - 1).
    # Then adding 10**exp to tmp has the same effect (after rounding)
    # as adding any positive quantity smaller than 10**exp; similarly
    # fuer subtraction.  So wenn other is smaller than 10**exp we replace
    # it with 10**exp.  This avoids tmp.exp - other.exp getting too large.
    tmp_len = len(str(tmp.int))
    other_len = len(str(other.int))
    exp = tmp.exp + min(-1, tmp_len - prec - 2)
    wenn other_len + other.exp - 1 < exp:
        other.int = 1
        other.exp = exp

    tmp.int *= 10 ** (tmp.exp - other.exp)
    tmp.exp = other.exp
    return op1, op2

##### Integer arithmetic functions used by ln, log10, exp and __pow__ #####

_nbits = int.bit_length

def _decimal_lshift_exact(n, e):
    """ Given integers n and e, return n * 10**e wenn it's an integer, sonst None.

    The computation is designed to avoid computing large powers of 10
    unnecessarily.

    >>> _decimal_lshift_exact(3, 4)
    30000
    >>> _decimal_lshift_exact(300, -999999999)  # returns None

    """
    wenn n == 0:
        return 0
    sowenn e >= 0:
        return n * 10**e
    sonst:
        # val_n = largest power of 10 dividing n.
        str_n = str(abs(n))
        val_n = len(str_n) - len(str_n.rstrip('0'))
        return None wenn val_n < -e sonst n // 10**-e

def _sqrt_nearest(n, a):
    """Closest integer to the square root of the positive integer n.  a is
    an initial approximation to the square root.  Any positive integer
    will do fuer a, but the closer a is to the square root of n the
    faster convergence will be.

    """
    wenn n <= 0 or a <= 0:
        raise ValueError("Both arguments to _sqrt_nearest should be positive.")

    b=0
    while a != b:
        b, a = a, a--n//a>>1
    return a

def _rshift_nearest(x, shift):
    """Given an integer x and a nonnegative integer shift, return closest
    integer to x / 2**shift; use round-to-even in case of a tie.

    """
    b, q = 1 << shift, x >> shift
    return q + (2*(x & (b-1)) + (q&1) > b)

def _div_nearest(a, b):
    """Closest integer to a/b, a and b positive integers; rounds to even
    in the case of a tie.

    """
    q, r = divmod(a, b)
    return q + (2*r + (q&1) > b)

def _ilog(x, M, L = 8):
    """Integer approximation to M*log(x/M), with absolute error boundable
    in terms only of x/M.

    Given positive integers x and M, return an integer approximation to
    M * log(x/M).  For L = 8 and 0.1 <= x/M <= 10 the difference
    between the approximation and the exact result is at most 22.  For
    L = 8 and 1.0 <= x/M <= 10.0 the difference is at most 15.  In
    both cases these are upper bounds on the error; it will usually be
    much smaller."""

    # The basic algorithm is the following: let log1p be the function
    # log1p(x) = log(1+x).  Then log(x/M) = log1p((x-M)/M).  We use
    # the reduction
    #
    #    log1p(y) = 2*log1p(y/(1+sqrt(1+y)))
    #
    # repeatedly until the argument to log1p is small (< 2**-L in
    # absolute value).  For small y we can use the Taylor series
    # expansion
    #
    #    log1p(y) ~ y - y**2/2 + y**3/3 - ... - (-y)**T/T
    #
    # truncating at T such that y**T is small enough.  The whole
    # computation is carried out in a form of fixed-point arithmetic,
    # with a real number z being represented by an integer
    # approximation to z*M.  To avoid loss of precision, the y below
    # is actually an integer approximation to 2**R*y*M, where R is the
    # number of reductions performed so far.

    y = x-M
    # argument reduction; R = number of reductions performed
    R = 0
    while (R <= L and abs(y) << L-R >= M or
           R > L and abs(y) >> R-L >= M):
        y = _div_nearest((M*y) << 1,
                         M + _sqrt_nearest(M*(M+_rshift_nearest(y, R)), M))
        R += 1

    # Taylor series with T terms
    T = -int(-10*len(str(M))//(3*L))
    yshift = _rshift_nearest(y, R)
    w = _div_nearest(M, T)
    fuer k in range(T-1, 0, -1):
        w = _div_nearest(M, k) - _div_nearest(yshift*w, M)

    return _div_nearest(w*y, M)

def _dlog10(c, e, p):
    """Given integers c, e and p with c > 0, p >= 0, compute an integer
    approximation to 10**p * log10(c*10**e), with an absolute error of
    at most 1.  Assumes that c*10**e is not exactly 1."""

    # increase precision by 2; compensate fuer this by dividing
    # final result by 100
    p += 2

    # write c*10**e as d*10**f with either:
    #   f >= 0 and 1 <= d <= 10, or
    #   f <= 0 and 0.1 <= d <= 1.
    # Thus fuer c*10**e close to 1, f = 0
    l = len(str(c))
    f = e+l - (e+l >= 1)

    wenn p > 0:
        M = 10**p
        k = e+p-f
        wenn k >= 0:
            c *= 10**k
        sonst:
            c = _div_nearest(c, 10**-k)

        log_d = _ilog(c, M) # error < 5 + 22 = 27
        log_10 = _log10_digits(p) # error < 1
        log_d = _div_nearest(log_d*M, log_10)
        log_tenpower = f*M # exact
    sonst:
        log_d = 0  # error < 2.31
        log_tenpower = _div_nearest(f, 10**-p) # error < 0.5

    return _div_nearest(log_tenpower+log_d, 100)

def _dlog(c, e, p):
    """Given integers c, e and p with c > 0, compute an integer
    approximation to 10**p * log(c*10**e), with an absolute error of
    at most 1.  Assumes that c*10**e is not exactly 1."""

    # Increase precision by 2. The precision increase is compensated
    # fuer at the end with a division by 100.
    p += 2

    # rewrite c*10**e as d*10**f with either f >= 0 and 1 <= d <= 10,
    # or f <= 0 and 0.1 <= d <= 1.  Then we can compute 10**p * log(c*10**e)
    # as 10**p * log(d) + 10**p*f * log(10).
    l = len(str(c))
    f = e+l - (e+l >= 1)

    # compute approximation to 10**p*log(d), with error < 27
    wenn p > 0:
        k = e+p-f
        wenn k >= 0:
            c *= 10**k
        sonst:
            c = _div_nearest(c, 10**-k)  # error of <= 0.5 in c

        # _ilog magnifies existing error in c by a factor of at most 10
        log_d = _ilog(c, 10**p) # error < 5 + 22 = 27
    sonst:
        # p <= 0: just approximate the whole thing by 0; error < 2.31
        log_d = 0

    # compute approximation to f*10**p*log(10), with error < 11.
    wenn f:
        extra = len(str(abs(f)))-1
        wenn p + extra >= 0:
            # error in f * _log10_digits(p+extra) < |f| * 1 = |f|
            # after division, error < |f|/10**extra + 0.5 < 10 + 0.5 < 11
            f_log_ten = _div_nearest(f*_log10_digits(p+extra), 10**extra)
        sonst:
            f_log_ten = 0
    sonst:
        f_log_ten = 0

    # error in sum < 11+27 = 38; error after division < 0.38 + 0.5 < 1
    return _div_nearest(f_log_ten + log_d, 100)

klasse _Log10Memoize(object):
    """Class to compute, store, and allow retrieval of, digits of the
    constant log(10) = 2.302585....  This constant is needed by
    Decimal.ln, Decimal.log10, Decimal.exp and Decimal.__pow__."""
    def __init__(self):
        self.digits = "23025850929940456840179914546843642076011014886"

    def getdigits(self, p):
        """Given an integer p >= 0, return floor(10**p)*log(10).

        For example, self.getdigits(3) returns 2302.
        """
        # digits are stored as a string, fuer quick conversion to
        # integer in the case that we've already computed enough
        # digits; the stored digits should always be correct
        # (truncated, not rounded to nearest).
        wenn p < 0:
            raise ValueError("p should be nonnegative")

        wenn p >= len(self.digits):
            # compute p+3, p+6, p+9, ... digits; continue until at
            # least one of the extra digits is nonzero
            extra = 3
            while True:
                # compute p+extra digits, correct to within 1ulp
                M = 10**(p+extra+2)
                digits = str(_div_nearest(_ilog(10*M, M), 100))
                wenn digits[-extra:] != '0'*extra:
                    break
                extra += 3
            # keep all reliable digits so far; remove trailing zeros
            # and next nonzero digit
            self.digits = digits.rstrip('0')[:-1]
        return int(self.digits[:p+1])

_log10_digits = _Log10Memoize().getdigits

def _iexp(x, M, L=8):
    """Given integers x and M, M > 0, such that x/M is small in absolute
    value, compute an integer approximation to M*exp(x/M).  For 0 <=
    x/M <= 2.4, the absolute error in the result is bounded by 60 (and
    is usually much smaller)."""

    # Algorithm: to compute exp(z) fuer a real number z, first divide z
    # by a suitable power R of 2 so that |z/2**R| < 2**-L.  Then
    # compute expm1(z/2**R) = exp(z/2**R) - 1 using the usual Taylor
    # series
    #
    #     expm1(x) = x + x**2/2! + x**3/3! + ...
    #
    # Now use the identity
    #
    #     expm1(2x) = expm1(x)*(expm1(x)+2)
    #
    # R times to compute the sequence expm1(z/2**R),
    # expm1(z/2**(R-1)), ... , exp(z/2), exp(z).

    # Find R such that x/2**R/M <= 2**-L
    R = _nbits((x<<L)//M)

    # Taylor series.  (2**L)**T > M
    T = -int(-10*len(str(M))//(3*L))
    y = _div_nearest(x, T)
    Mshift = M<<R
    fuer i in range(T-1, 0, -1):
        y = _div_nearest(x*(Mshift + y), Mshift * i)

    # Expansion
    fuer k in range(R-1, -1, -1):
        Mshift = M<<(k+2)
        y = _div_nearest(y*(y+Mshift), Mshift)

    return M+y

def _dexp(c, e, p):
    """Compute an approximation to exp(c*10**e), with p decimal places of
    precision.

    Returns integers d, f such that:

      10**(p-1) <= d <= 10**p, and
      (d-1)*10**f < exp(c*10**e) < (d+1)*10**f

    In other words, d*10**f is an approximation to exp(c*10**e) with p
    digits of precision, and with an error in d of at most 1.  This is
    almost, but not quite, the same as the error being < 1ulp: when d
    = 10**(p-1) the error could be up to 10 ulp."""

    # we'll call iexp with M = 10**(p+2), giving p+3 digits of precision
    p += 2

    # compute log(10) with extra precision = adjusted exponent of c*10**e
    extra = max(0, e + len(str(c)) - 1)
    q = p + extra

    # compute quotient c*10**e/(log(10)) = c*10**(e+q)/(log(10)*10**q),
    # rounding down
    shift = e+q
    wenn shift >= 0:
        cshift = c*10**shift
    sonst:
        cshift = c//10**-shift
    quot, rem = divmod(cshift, _log10_digits(q))

    # reduce remainder back to original precision
    rem = _div_nearest(rem, 10**extra)

    # error in result of _iexp < 120;  error after division < 0.62
    return _div_nearest(_iexp(rem, 10**p), 1000), quot - p + 3

def _dpower(xc, xe, yc, ye, p):
    """Given integers xc, xe, yc and ye representing Decimals x = xc*10**xe and
    y = yc*10**ye, compute x**y.  Returns a pair of integers (c, e) such that:

      10**(p-1) <= c <= 10**p, and
      (c-1)*10**e < x**y < (c+1)*10**e

    in other words, c*10**e is an approximation to x**y with p digits
    of precision, and with an error in c of at most 1.  (This is
    almost, but not quite, the same as the error being < 1ulp: when c
    == 10**(p-1) we can only guarantee error < 10ulp.)

    We assume that: x is positive and not equal to 1, and y is nonzero.
    """

    # Find b such that 10**(b-1) <= |y| <= 10**b
    b = len(str(abs(yc))) + ye

    # log(x) = lxc*10**(-p-b-1), to p+b+1 places after the decimal point
    lxc = _dlog(xc, xe, p+b+1)

    # compute product y*log(x) = yc*lxc*10**(-p-b-1+ye) = pc*10**(-p-1)
    shift = ye-b
    wenn shift >= 0:
        pc = lxc*yc*10**shift
    sonst:
        pc = _div_nearest(lxc*yc, 10**-shift)

    wenn pc == 0:
        # we prefer a result that isn't exactly 1; this makes it
        # easier to compute a correctly rounded result in __pow__
        wenn ((len(str(xc)) + xe >= 1) == (yc > 0)): # wenn x**y > 1:
            coeff, exp = 10**(p-1)+1, 1-p
        sonst:
            coeff, exp = 10**p-1, -p
    sonst:
        coeff, exp = _dexp(pc, -(p+1), p+1)
        coeff = _div_nearest(coeff, 10)
        exp += 1

    return coeff, exp

def _log10_lb(c, correction = {
        '1': 100, '2': 70, '3': 53, '4': 40, '5': 31,
        '6': 23, '7': 16, '8': 10, '9': 5}):
    """Compute a lower bound fuer 100*log10(c) fuer a positive integer c."""
    wenn c <= 0:
        raise ValueError("The argument to _log10_lb should be nonnegative.")
    str_c = str(c)
    return 100*len(str_c) - correction[str_c[0]]

##### Helper Functions ####################################################

def _convert_other(other, raiseit=False, allow_float=False):
    """Convert other to Decimal.

    Verifies that it's ok to use in an implicit construction.
    If allow_float is true, allow conversion from float;  this
    is used in the comparison methods (__eq__ and friends).

    """
    wenn isinstance(other, Decimal):
        return other
    wenn isinstance(other, int):
        return Decimal(other)
    wenn allow_float and isinstance(other, float):
        return Decimal.from_float(other)

    wenn raiseit:
        raise TypeError("Unable to convert %s to Decimal" % other)
    return NotImplemented

def _convert_for_comparison(self, other, equality_op=False):
    """Given a Decimal instance self and a Python object other, return
    a pair (s, o) of Decimal instances such that "s op o" is
    equivalent to "self op other" fuer any of the 6 comparison
    operators "op".

    """
    wenn isinstance(other, Decimal):
        return self, other

    # Comparison with a Rational instance (also includes integers):
    # self op n/d <=> self*d op n (for n and d integers, d positive).
    # A NaN or infinity can be left unchanged without affecting the
    # comparison result.
    wenn isinstance(other, _numbers.Rational):
        wenn not self._is_special:
            self = _dec_from_triple(self._sign,
                                    str(int(self._int) * other.denominator),
                                    self._exp)
        return self, Decimal(other.numerator)

    # Comparisons with float and complex types.  == and != comparisons
    # with complex numbers should succeed, returning either True or False
    # as appropriate.  Other comparisons return NotImplemented.
    wenn equality_op and isinstance(other, _numbers.Complex) and other.imag == 0:
        other = other.real
    wenn isinstance(other, float):
        context = getcontext()
        wenn equality_op:
            context.flags[FloatOperation] = 1
        sonst:
            context._raise_error(FloatOperation,
                "strict semantics fuer mixing floats and Decimals are enabled")
        return self, Decimal.from_float(other)
    return NotImplemented, NotImplemented


##### Setup Specific Contexts ############################################

# The default context prototype used by Context()
# Is mutable, so that new contexts can have different default values

DefaultContext = Context(
        prec=28, rounding=ROUND_HALF_EVEN,
        traps=[DivisionByZero, Overflow, InvalidOperation],
        flags=[],
        Emax=999999,
        Emin=-999999,
        capitals=1,
        clamp=0
)

# Pre-made alternate contexts offered by the specification
# Don't change these; the user should be able to select these
# contexts and be able to reproduce results from other implementations
# of the spec.

BasicContext = Context(
        prec=9, rounding=ROUND_HALF_UP,
        traps=[DivisionByZero, Overflow, InvalidOperation, Clamped, Underflow],
        flags=[],
)

ExtendedContext = Context(
        prec=9, rounding=ROUND_HALF_EVEN,
        traps=[],
        flags=[],
)


##### crud fuer parsing strings #############################################
#
# Regular expression used fuer parsing numeric strings.  Additional
# comments:
#
# 1. Uncomment the two '\s*' lines to allow leading and/or trailing
# whitespace.  But note that the specification disallows whitespace in
# a numeric string.
#
# 2. For finite numbers (not infinities and NaNs) the body of the
# number between the optional sign and the optional exponent must have
# at least one decimal digit, possibly after the decimal point.  The
# lookahead expression '(?=\d|\.\d)' checks this.

import re
_parser = re.compile(r"""        # A numeric string consists of:
#    \s*
    (?P<sign>[-+])?              # an optional sign, followed by either...
    (
        (?=\d|\.\d)              # ...a number (with at least one digit)
        (?P<int>\d*)             # having a (possibly empty) integer part
        (\.(?P<frac>\d*))?       # followed by an optional fractional part
        (E(?P<exp>[-+]?\d+))?    # followed by an optional exponent, or...
    |
        Inf(inity)?              # ...an infinity, or...
    |
        (?P<signal>s)?           # ...an (optionally signaling)
        NaN                      # NaN
        (?P<diag>\d*)            # with (possibly empty) diagnostic info.
    )
#    \s*
    \z
""", re.VERBOSE | re.IGNORECASE).match

_all_zeros = re.compile('0*$').match
_exact_half = re.compile('50*$').match

##### PEP3101 support functions ##############################################
# The functions in this section have little to do with the Decimal
# class, and could potentially be reused or adapted fuer other pure
# Python numeric classes that want to implement __format__
#
# A format specifier fuer Decimal looks like:
#
#   [[fill]align][sign][z][#][0][minimumwidth][,][.precision][type]

_parse_format_specifier_regex = re.compile(r"""\A
(?:
   (?P<fill>.)?
   (?P<align>[<>=^])
)?
(?P<sign>[-+ ])?
(?P<no_neg_0>z)?
(?P<alt>\#)?
(?P<zeropad>0)?
(?P<minimumwidth>\d+)?
(?P<thousands_sep>[,_])?
(?:\.
    (?=[\d,_])  # lookahead fuer digit or separator
    (?P<precision>\d+)?
    (?P<frac_separators>[,_])?
)?
(?P<type>[eEfFgGn%])?
\z
""", re.VERBOSE|re.DOTALL)

del re

# The locale module is only needed fuer the 'n' format specifier.  The
# rest of the PEP 3101 code functions quite happily without it, so we
# don't care too much wenn locale isn't present.
try:
    import locale as _locale
except ImportError:
    pass

def _parse_format_specifier(format_spec, _localeconv=None):
    """Parse and validate a format specifier.

    Turns a standard numeric format specifier into a dict, with the
    following entries:

      fill: fill character to pad field to minimum width
      align: alignment type, either '<', '>', '=' or '^'
      sign: either '+', '-' or ' '
      minimumwidth: nonnegative integer giving minimum width
      zeropad: boolean, indicating whether to pad with zeros
      thousands_sep: string to use as thousands separator, or ''
      grouping: grouping fuer thousands separators, in format
        used by localeconv
      decimal_point: string to use fuer decimal point
      precision: nonnegative integer giving precision, or None
      type: one of the characters 'eEfFgG%', or None

    """
    m = _parse_format_specifier_regex.match(format_spec)
    wenn m is None:
        raise ValueError("Invalid format specifier: " + format_spec)

    # get the dictionary
    format_dict = m.groupdict()

    # zeropad; defaults fuer fill and alignment.  If zero padding
    # is requested, the fill and align fields should be absent.
    fill = format_dict['fill']
    align = format_dict['align']
    format_dict['zeropad'] = (format_dict['zeropad'] is not None)
    wenn format_dict['zeropad']:
        wenn fill is not None:
            raise ValueError("Fill character conflicts with '0'"
                             " in format specifier: " + format_spec)
        wenn align is not None:
            raise ValueError("Alignment conflicts with '0' in "
                             "format specifier: " + format_spec)
    format_dict['fill'] = fill or ' '
    # PEP 3101 originally specified that the default alignment should
    # be left;  it was later agreed that right-aligned makes more sense
    # fuer numeric types.  See http://bugs.python.org/issue6857.
    format_dict['align'] = align or '>'

    # default sign handling: '-' fuer negative, '' fuer positive
    wenn format_dict['sign'] is None:
        format_dict['sign'] = '-'

    # minimumwidth defaults to 0; precision remains None wenn not given
    format_dict['minimumwidth'] = int(format_dict['minimumwidth'] or '0')
    wenn format_dict['precision'] is not None:
        format_dict['precision'] = int(format_dict['precision'])

    # wenn format type is 'g' or 'G' then a precision of 0 makes little
    # sense; convert it to 1.  Same wenn format type is unspecified.
    wenn format_dict['precision'] == 0:
        wenn format_dict['type'] is None or format_dict['type'] in 'gGn':
            format_dict['precision'] = 1

    # determine thousands separator, grouping, and decimal separator, and
    # add appropriate entries to format_dict
    wenn format_dict['type'] == 'n':
        # apart from separators, 'n' behaves just like 'g'
        format_dict['type'] = 'g'
        wenn _localeconv is None:
            _localeconv = _locale.localeconv()
        wenn format_dict['thousands_sep'] is not None:
            raise ValueError("Explicit thousands separator conflicts with "
                             "'n' type in format specifier: " + format_spec)
        format_dict['thousands_sep'] = _localeconv['thousands_sep']
        format_dict['grouping'] = _localeconv['grouping']
        format_dict['decimal_point'] = _localeconv['decimal_point']
    sonst:
        wenn format_dict['thousands_sep'] is None:
            format_dict['thousands_sep'] = ''
        format_dict['grouping'] = [3, 0]
        format_dict['decimal_point'] = '.'

    wenn format_dict['frac_separators'] is None:
        format_dict['frac_separators'] = ''

    return format_dict

def _format_align(sign, body, spec):
    """Given an unpadded, non-aligned numeric string 'body' and sign
    string 'sign', add padding and alignment conforming to the given
    format specifier dictionary 'spec' (as produced by
    parse_format_specifier).

    """
    # how much extra space do we have to play with?
    minimumwidth = spec['minimumwidth']
    fill = spec['fill']
    padding = fill*(minimumwidth - len(sign) - len(body))

    align = spec['align']
    wenn align == '<':
        result = sign + body + padding
    sowenn align == '>':
        result = padding + sign + body
    sowenn align == '=':
        result = sign + padding + body
    sowenn align == '^':
        half = len(padding)//2
        result = padding[:half] + sign + body + padding[half:]
    sonst:
        raise ValueError('Unrecognised alignment field')

    return result

def _group_lengths(grouping):
    """Convert a localeconv-style grouping into a (possibly infinite)
    iterable of integers representing group lengths.

    """
    # The result from localeconv()['grouping'], and the input to this
    # function, should be a list of integers in one of the
    # following three forms:
    #
    #   (1) an empty list, or
    #   (2) nonempty list of positive integers + [0]
    #   (3) list of positive integers + [locale.CHAR_MAX], or

    from itertools import chain, repeat
    wenn not grouping:
        return []
    sowenn grouping[-1] == 0 and len(grouping) >= 2:
        return chain(grouping[:-1], repeat(grouping[-2]))
    sowenn grouping[-1] == _locale.CHAR_MAX:
        return grouping[:-1]
    sonst:
        raise ValueError('unrecognised format fuer grouping')

def _insert_thousands_sep(digits, spec, min_width=1):
    """Insert thousands separators into a digit string.

    spec is a dictionary whose keys should include 'thousands_sep' and
    'grouping'; typically it's the result of parsing the format
    specifier using _parse_format_specifier.

    The min_width keyword argument gives the minimum length of the
    result, which will be padded on the left with zeros wenn necessary.

    If necessary, the zero padding adds an extra '0' on the left to
    avoid a leading thousands separator.  For example, inserting
    commas every three digits in '123456', with min_width=8, gives
    '0,123,456', even though that has length 9.

    """

    sep = spec['thousands_sep']
    grouping = spec['grouping']

    groups = []
    fuer l in _group_lengths(grouping):
        wenn l <= 0:
            raise ValueError("group length should be positive")
        # max(..., 1) forces at least 1 digit to the left of a separator
        l = min(max(len(digits), min_width, 1), l)
        groups.append('0'*(l - len(digits)) + digits[-l:])
        digits = digits[:-l]
        min_width -= l
        wenn not digits and min_width <= 0:
            break
        min_width -= len(sep)
    sonst:
        l = max(len(digits), min_width, 1)
        groups.append('0'*(l - len(digits)) + digits[-l:])
    return sep.join(reversed(groups))

def _format_sign(is_negative, spec):
    """Determine sign character."""

    wenn is_negative:
        return '-'
    sowenn spec['sign'] in ' +':
        return spec['sign']
    sonst:
        return ''

def _format_number(is_negative, intpart, fracpart, exp, spec):
    """Format a number, given the following data:

    is_negative: true wenn the number is negative, sonst false
    intpart: string of digits that must appear before the decimal point
    fracpart: string of digits that must come after the point
    exp: exponent, as an integer
    spec: dictionary resulting from parsing the format specifier

    This function uses the information in spec to:
      insert separators (decimal separator and thousands separators)
      format the sign
      format the exponent
      add trailing '%' fuer the '%' type
      zero-pad wenn necessary
      fill and align wenn necessary
    """

    sign = _format_sign(is_negative, spec)

    frac_sep = spec['frac_separators']
    wenn fracpart and frac_sep:
        fracpart = frac_sep.join(fracpart[pos:pos + 3]
                                 fuer pos in range(0, len(fracpart), 3))

    wenn fracpart or spec['alt']:
        fracpart = spec['decimal_point'] + fracpart

    wenn exp != 0 or spec['type'] in 'eE':
        echar = {'E': 'E', 'e': 'e', 'G': 'E', 'g': 'e'}[spec['type']]
        fracpart += "{0}{1:+}".format(echar, exp)
    wenn spec['type'] == '%':
        fracpart += '%'

    wenn spec['zeropad']:
        min_width = spec['minimumwidth'] - len(fracpart) - len(sign)
    sonst:
        min_width = 0
    intpart = _insert_thousands_sep(intpart, spec, min_width)

    return _format_align(sign, intpart+fracpart, spec)


##### Useful Constants (internal use only) ################################

# Reusable defaults
_Infinity = Decimal('Inf')
_NegativeInfinity = Decimal('-Inf')
_NaN = Decimal('NaN')
_Zero = Decimal(0)
_One = Decimal(1)
_NegativeOne = Decimal(-1)

# _SignedInfinity[sign] is infinity w/ that sign
_SignedInfinity = (_Infinity, _NegativeInfinity)

# Constants related to the hash implementation;  hash(x) is based
# on the reduction of x modulo _PyHASH_MODULUS
_PyHASH_MODULUS = sys.hash_info.modulus
# hash values to use fuer positive and negative infinities, and nans
_PyHASH_INF = sys.hash_info.inf
_PyHASH_NAN = sys.hash_info.nan

# _PyHASH_10INV is the inverse of 10 modulo the prime _PyHASH_MODULUS
_PyHASH_10INV = pow(10, _PyHASH_MODULUS - 2, _PyHASH_MODULUS)
del sys
