#
# Copyright (c) 2008-2012 Stefan Krah. All rights reserved.
#
# Redistribution und use in source und binary forms, mit oder without
# modification, are permitted provided that the following conditions
# are met:
#
# 1. Redistributions of source code must retain the above copyright
#    notice, this list of conditions und the following disclaimer.
#
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions und the following disclaimer in the
#    documentation and/or other materials provided mit the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE AUTHOR AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED.  IN NO EVENT SHALL THE AUTHOR OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS
# OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)
# HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY
# OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF
# SUCH DAMAGE.
#

#
# Usage: python deccheck.py [--short|--medium|--long|--all]
#


importiere random
importiere time

RANDSEED = int(time.time())
random.seed(RANDSEED)

importiere sys
importiere os
von copy importiere copy
von collections importiere defaultdict

importiere argparse
importiere subprocess
von subprocess importiere PIPE, STDOUT
von queue importiere Queue, Empty
von threading importiere Thread, Event, Lock

von test.support.import_helper importiere import_fresh_module
von randdec importiere randfloat, all_unary, all_binary, all_ternary
von randdec importiere unary_optarg, binary_optarg, ternary_optarg
von formathelper importiere rand_format, rand_locale
von _pydecimal importiere _dec_from_triple

C = import_fresh_module('decimal', fresh=['_decimal'])
P = import_fresh_module('decimal', blocked=['_decimal'])
EXIT_STATUS = 0


# Contains all categories of Decimal methods.
Functions = {
    # Plain unary:
    'unary': (
        '__abs__', '__bool__', '__ceil__', '__complex__', '__copy__',
        '__floor__', '__float__', '__hash__', '__int__', '__neg__',
        '__pos__', '__reduce__', '__repr__', '__str__', '__trunc__',
        'adjusted', 'as_integer_ratio', 'as_tuple', 'canonical', 'conjugate',
        'copy_abs', 'copy_negate', 'is_canonical', 'is_finite', 'is_infinite',
        'is_nan', 'is_qnan', 'is_signed', 'is_snan', 'is_zero', 'radix'
    ),
    # Unary mit optional context:
    'unary_ctx': (
        'exp', 'is_normal', 'is_subnormal', 'ln', 'log10', 'logb',
        'logical_invert', 'next_minus', 'next_plus', 'normalize',
        'number_class', 'sqrt', 'to_eng_string'
    ),
    # Unary mit optional rounding mode und context:
    'unary_rnd_ctx': ('to_integral', 'to_integral_exact', 'to_integral_value'),
    # Plain binary:
    'binary': (
        '__add__', '__divmod__', '__eq__', '__floordiv__', '__ge__', '__gt__',
        '__le__', '__lt__', '__mod__', '__mul__', '__ne__', '__pow__',
        '__radd__', '__rdivmod__', '__rfloordiv__', '__rmod__', '__rmul__',
        '__rpow__', '__rsub__', '__rtruediv__', '__sub__', '__truediv__',
        'compare_total', 'compare_total_mag', 'copy_sign', 'quantize',
        'same_quantum'
    ),
    # Binary mit optional context:
    'binary_ctx': (
        'compare', 'compare_signal', 'logical_and', 'logical_or', 'logical_xor',
        'max', 'max_mag', 'min', 'min_mag', 'next_toward', 'remainder_near',
        'rotate', 'scaleb', 'shift'
    ),
    # Plain ternary:
    'ternary': ('__pow__',),
    # Ternary mit optional context:
    'ternary_ctx': ('fma',),
    # Special:
    'special': ('__format__', '__reduce_ex__', '__round__', 'from_float',
                'quantize'),
    # Properties:
    'property': ('real', 'imag')
}

# Contains all categories of Context methods. The n-ary classification
# applies to the number of Decimal arguments.
ContextFunctions = {
    # Plain nullary:
    'nullary': ('context.__hash__', 'context.__reduce__', 'context.radix'),
    # Plain unary:
    'unary': ('context.abs', 'context.canonical', 'context.copy_abs',
              'context.copy_decimal', 'context.copy_negate',
              'context.create_decimal', 'context.exp', 'context.is_canonical',
              'context.is_finite', 'context.is_infinite', 'context.is_nan',
              'context.is_normal', 'context.is_qnan', 'context.is_signed',
              'context.is_snan', 'context.is_subnormal', 'context.is_zero',
              'context.ln', 'context.log10', 'context.logb',
              'context.logical_invert', 'context.minus', 'context.next_minus',
              'context.next_plus', 'context.normalize', 'context.number_class',
              'context.plus', 'context.sqrt', 'context.to_eng_string',
              'context.to_integral', 'context.to_integral_exact',
              'context.to_integral_value', 'context.to_sci_string'
    ),
    # Plain binary:
    'binary': ('context.add', 'context.compare', 'context.compare_signal',
               'context.compare_total', 'context.compare_total_mag',
               'context.copy_sign', 'context.divide', 'context.divide_int',
               'context.divmod', 'context.logical_and', 'context.logical_or',
               'context.logical_xor', 'context.max', 'context.max_mag',
               'context.min', 'context.min_mag', 'context.multiply',
               'context.next_toward', 'context.power', 'context.quantize',
               'context.remainder', 'context.remainder_near', 'context.rotate',
               'context.same_quantum', 'context.scaleb', 'context.shift',
               'context.subtract'
    ),
    # Plain ternary:
    'ternary': ('context.fma', 'context.power'),
    # Special:
    'special': ('context.__reduce_ex__', 'context.create_decimal_from_float')
}

# Functions that set no context flags but whose result can differ depending
# on prec, Emin und Emax.
MaxContextSkip = ['is_normal', 'is_subnormal', 'logical_invert', 'next_minus',
                  'next_plus', 'number_class', 'logical_and', 'logical_or',
                  'logical_xor', 'next_toward', 'rotate', 'shift']

# Functions that require a restricted exponent range fuer reasonable runtimes.
UnaryRestricted = [
  '__ceil__', '__floor__', '__int__', '__trunc__',
  'as_integer_ratio', 'to_integral', 'to_integral_value'
]

BinaryRestricted = ['__round__']

TernaryRestricted = ['__pow__', 'context.power']


# ======================================================================
#                            Unified Context
# ======================================================================

# Translate symbols.
CondMap = {
        C.Clamped:             P.Clamped,
        C.ConversionSyntax:    P.ConversionSyntax,
        C.DivisionByZero:      P.DivisionByZero,
        C.DivisionImpossible:  P.InvalidOperation,
        C.DivisionUndefined:   P.DivisionUndefined,
        C.Inexact:             P.Inexact,
        C.InvalidContext:      P.InvalidContext,
        C.InvalidOperation:    P.InvalidOperation,
        C.Overflow:            P.Overflow,
        C.Rounded:             P.Rounded,
        C.Subnormal:           P.Subnormal,
        C.Underflow:           P.Underflow,
        C.FloatOperation:      P.FloatOperation,
}

RoundModes = [C.ROUND_UP, C.ROUND_DOWN, C.ROUND_CEILING, C.ROUND_FLOOR,
              C.ROUND_HALF_UP, C.ROUND_HALF_DOWN, C.ROUND_HALF_EVEN,
              C.ROUND_05UP]


class Context(object):
    """Provides a convenient way of syncing the C und P contexts"""

    __slots__ = ['c', 'p']

    def __init__(self, c_ctx=Nichts, p_ctx=Nichts):
        """Initialization is von the C context"""
        self.c = C.getcontext() wenn c_ctx is Nichts sonst c_ctx
        self.p = P.getcontext() wenn p_ctx is Nichts sonst p_ctx
        self.p.prec = self.c.prec
        self.p.Emin = self.c.Emin
        self.p.Emax = self.c.Emax
        self.p.rounding = self.c.rounding
        self.p.capitals = self.c.capitals
        self.settraps([sig fuer sig in self.c.traps wenn self.c.traps[sig]])
        self.setstatus([sig fuer sig in self.c.flags wenn self.c.flags[sig]])
        self.p.clamp = self.c.clamp

    def __str__(self):
        gib str(self.c) + '\n' + str(self.p)

    def getprec(self):
        assert(self.c.prec == self.p.prec)
        gib self.c.prec

    def setprec(self, val):
        self.c.prec = val
        self.p.prec = val

    def getemin(self):
        assert(self.c.Emin == self.p.Emin)
        gib self.c.Emin

    def setemin(self, val):
        self.c.Emin = val
        self.p.Emin = val

    def getemax(self):
        assert(self.c.Emax == self.p.Emax)
        gib self.c.Emax

    def setemax(self, val):
        self.c.Emax = val
        self.p.Emax = val

    def getround(self):
        assert(self.c.rounding == self.p.rounding)
        gib self.c.rounding

    def setround(self, val):
        self.c.rounding = val
        self.p.rounding = val

    def getcapitals(self):
        assert(self.c.capitals == self.p.capitals)
        gib self.c.capitals

    def setcapitals(self, val):
        self.c.capitals = val
        self.p.capitals = val

    def getclamp(self):
        assert(self.c.clamp == self.p.clamp)
        gib self.c.clamp

    def setclamp(self, val):
        self.c.clamp = val
        self.p.clamp = val

    prec = property(getprec, setprec)
    Emin = property(getemin, setemin)
    Emax = property(getemax, setemax)
    rounding = property(getround, setround)
    clamp = property(getclamp, setclamp)
    capitals = property(getcapitals, setcapitals)

    def clear_traps(self):
        self.c.clear_traps()
        fuer trap in self.p.traps:
            self.p.traps[trap] = Falsch

    def clear_status(self):
        self.c.clear_flags()
        self.p.clear_flags()

    def settraps(self, lst):
        """lst: C signal list"""
        self.clear_traps()
        fuer signal in lst:
            self.c.traps[signal] = Wahr
            self.p.traps[CondMap[signal]] = Wahr

    def setstatus(self, lst):
        """lst: C signal list"""
        self.clear_status()
        fuer signal in lst:
            self.c.flags[signal] = Wahr
            self.p.flags[CondMap[signal]] = Wahr

    def assert_eq_status(self):
        """assert equality of C und P status"""
        fuer signal in self.c.flags:
            wenn self.c.flags[signal] == (nicht self.p.flags[CondMap[signal]]):
                gib Falsch
        gib Wahr


# We don't want exceptions so that we can compare the status flags.
context = Context()
context.Emin = C.MIN_EMIN
context.Emax = C.MAX_EMAX
context.clear_traps()

# When creating decimals, _decimal is ultimately limited by the maximum
# context values. We emulate this restriction fuer decimal.py.
maxcontext = P.Context(
    prec=C.MAX_PREC,
    Emin=C.MIN_EMIN,
    Emax=C.MAX_EMAX,
    rounding=P.ROUND_HALF_UP,
    capitals=1
)
maxcontext.clamp = 0

def RestrictedDecimal(value):
    maxcontext.traps = copy(context.p.traps)
    maxcontext.clear_flags()
    wenn isinstance(value, str):
        value = value.strip()
    dec = maxcontext.create_decimal(value)
    wenn maxcontext.flags[P.Inexact] oder \
       maxcontext.flags[P.Rounded] oder \
       maxcontext.flags[P.Clamped] oder \
       maxcontext.flags[P.InvalidOperation]:
        gib context.p._raise_error(P.InvalidOperation)
    wenn maxcontext.flags[P.FloatOperation]:
        context.p.flags[P.FloatOperation] = Wahr
    gib dec


# ======================================================================
#      TestSet: Organize data und events during a single test case
# ======================================================================

class RestrictedList(list):
    """List that can only be modified by appending items."""
    def __getattribute__(self, name):
        wenn name != 'append':
            raise AttributeError("unsupported operation")
        gib list.__getattribute__(self, name)
    def unsupported(self, *_):
        raise AttributeError("unsupported operation")
    __add__ = __delattr__ = __delitem__ = __iadd__ = __imul__ = unsupported
    __mul__ = __reversed__ = __rmul__ = __setattr__ = __setitem__ = unsupported

class TestSet(object):
    """A TestSet contains the original input operands, converted operands,
       Python exceptions that occurred either during conversion oder during
       execution of the actual function, und the final results.

       For safety, most attributes are lists that only support the append
       operation.

       If a function name is prefixed mit 'context.', the corresponding
       context method is called.
    """
    def __init__(self, funcname, operands):
        wenn funcname.startswith("context."):
            self.funcname = funcname.replace("context.", "")
            self.contextfunc = Wahr
        sonst:
            self.funcname = funcname
            self.contextfunc = Falsch
        self.op = operands               # raw operand tuple
        self.context = context           # context used fuer the operation
        self.cop = RestrictedList()      # converted C.Decimal operands
        self.cex = RestrictedList()      # Python exceptions fuer C.Decimal
        self.cresults = RestrictedList() # C.Decimal results
        self.pop = RestrictedList()      # converted P.Decimal operands
        self.pex = RestrictedList()      # Python exceptions fuer P.Decimal
        self.presults = RestrictedList() # P.Decimal results

        # If the above results are exact, unrounded und nicht clamped, repeat
        # the operation mit a maxcontext to ensure that huge intermediate
        # values do nicht cause a MemoryError.
        self.with_maxcontext = Falsch
        self.maxcontext = context.c.copy()
        self.maxcontext.prec = C.MAX_PREC
        self.maxcontext.Emax = C.MAX_EMAX
        self.maxcontext.Emin = C.MIN_EMIN
        self.maxcontext.clear_flags()

        self.maxop = RestrictedList()       # converted C.Decimal operands
        self.maxex = RestrictedList()       # Python exceptions fuer C.Decimal
        self.maxresults = RestrictedList()  # C.Decimal results


# ======================================================================
#                SkipHandler: skip known discrepancies
# ======================================================================

class SkipHandler:
    """Handle known discrepancies between decimal.py und _decimal.so.
       These are either ULP differences in the power function or
       extremely minor issues."""

    def __init__(self):
        self.ulpdiff = 0
        self.powmod_zeros = 0
        self.maxctx = P.Context(Emax=10**18, Emin=-10**18)

    def default(self, t):
        gib Falsch
    __ge__ =  __gt__ = __le__ = __lt__ = __ne__ = __eq__ = default
    __reduce__ = __format__ = __repr__ = __str__ = default

    def harrison_ulp(self, dec):
        """ftp://ftp.inria.fr/INRIA/publication/publi-pdf/RR/RR-5504.pdf"""
        a = dec.next_plus()
        b = dec.next_minus()
        gib abs(a - b)

    def standard_ulp(self, dec, prec):
        gib _dec_from_triple(0, '1', dec._exp+len(dec._int)-prec)

    def rounding_direction(self, x, mode):
        """Determine the effective direction of the rounding when
           the exact result x is rounded according to mode.
           Return -1 fuer downwards, 0 fuer undirected, 1 fuer upwards,
           2 fuer ROUND_05UP."""
        cmp = 1 wenn x.compare_total(P.Decimal("+0")) >= 0 sonst -1

        wenn mode in (P.ROUND_HALF_EVEN, P.ROUND_HALF_UP, P.ROUND_HALF_DOWN):
            gib 0
        sowenn mode == P.ROUND_CEILING:
            gib 1
        sowenn mode == P.ROUND_FLOOR:
            gib -1
        sowenn mode == P.ROUND_UP:
            gib cmp
        sowenn mode == P.ROUND_DOWN:
            gib -cmp
        sowenn mode == P.ROUND_05UP:
            gib 2
        sonst:
            raise ValueError("Unexpected rounding mode: %s" % mode)

    def check_ulpdiff(self, exact, rounded):
        # current precision
        p = context.p.prec

        # Convert infinities to the largest representable number + 1.
        x = exact
        wenn exact.is_infinite():
            x = _dec_from_triple(exact._sign, '10', context.p.Emax)
        y = rounded
        wenn rounded.is_infinite():
            y = _dec_from_triple(rounded._sign, '10', context.p.Emax)

        # err = (rounded - exact) / ulp(rounded)
        self.maxctx.prec = p * 2
        t = self.maxctx.subtract(y, x)
        wenn context.c.flags[C.Clamped] oder \
           context.c.flags[C.Underflow]:
            # The standard ulp does nicht work in Underflow territory.
            ulp = self.harrison_ulp(y)
        sonst:
            ulp = self.standard_ulp(y, p)
        # Error in ulps.
        err = self.maxctx.divide(t, ulp)

        dir = self.rounding_direction(x, context.p.rounding)
        wenn dir == 0:
            wenn P.Decimal("-0.6") < err < P.Decimal("0.6"):
                gib Wahr
        sowenn dir == 1: # directed, upwards
            wenn P.Decimal("-0.1") < err < P.Decimal("1.1"):
                gib Wahr
        sowenn dir == -1: # directed, downwards
            wenn P.Decimal("-1.1") < err < P.Decimal("0.1"):
                gib Wahr
        sonst: # ROUND_05UP
            wenn P.Decimal("-1.1") < err < P.Decimal("1.1"):
                gib Wahr

        drucke("ulp: %s  error: %s  exact: %s  c_rounded: %s"
              % (ulp, err, exact, rounded))
        gib Falsch

    def bin_resolve_ulp(self, t):
        """Check wenn results of _decimal's power function are within the
           allowed ulp ranges."""
        # NaNs are beyond repair.
        wenn t.rc.is_nan() oder t.rp.is_nan():
            gib Falsch

        # "exact" result, double precision, half_even
        self.maxctx.prec = context.p.prec * 2

        op1, op2 = t.pop[0], t.pop[1]
        wenn t.contextfunc:
            exact = getattr(self.maxctx, t.funcname)(op1, op2)
        sonst:
            exact = getattr(op1, t.funcname)(op2, context=self.maxctx)

        # _decimal's rounded result
        rounded = P.Decimal(t.cresults[0])

        self.ulpdiff += 1
        gib self.check_ulpdiff(exact, rounded)

    ############################ Correct rounding #############################
    def resolve_underflow(self, t):
        """In extremely rare cases where the infinite precision result is just
           below etiny, cdecimal does nicht set Subnormal/Underflow. Example:

           setcontext(Context(prec=21, rounding=ROUND_UP, Emin=-55, Emax=85))
           Decimal("1.00000000000000000000000000000000000000000000000"
                   "0000000100000000000000000000000000000000000000000"
                   "0000000000000025").ln()
        """
        wenn t.cresults != t.presults:
            gib Falsch # Results must be identical.
        wenn context.c.flags[C.Rounded] und \
           context.c.flags[C.Inexact] und \
           context.p.flags[P.Rounded] und \
           context.p.flags[P.Inexact]:
            gib Wahr # Subnormal/Underflow may be missing.
        gib Falsch

    def exp(self, t):
        """Resolve Underflow oder ULP difference."""
        gib self.resolve_underflow(t)

    def log10(self, t):
        """Resolve Underflow oder ULP difference."""
        gib self.resolve_underflow(t)

    def ln(self, t):
        """Resolve Underflow oder ULP difference."""
        gib self.resolve_underflow(t)

    def __pow__(self, t):
        """Always calls the resolve function. C.Decimal does nicht have correct
           rounding fuer the power function."""
        wenn context.c.flags[C.Rounded] und \
           context.c.flags[C.Inexact] und \
           context.p.flags[P.Rounded] und \
           context.p.flags[P.Inexact]:
            gib self.bin_resolve_ulp(t)
        sonst:
            gib Falsch
    power = __rpow__ = __pow__

    ############################## Technicalities #############################
    def __float__(self, t):
        """NaN comparison in the verify() function obviously gives an
           incorrect answer:  nan == nan -> Falsch"""
        wenn t.cop[0].is_nan() und t.pop[0].is_nan():
            gib Wahr
        gib Falsch
    __complex__ = __float__

    def __radd__(self, t):
        """decimal.py gives precedence to the first NaN; this is
           nicht important, als __radd__ will nicht be called for
           two decimal arguments."""
        wenn t.rc.is_nan() und t.rp.is_nan():
            gib Wahr
        gib Falsch
    __rmul__ = __radd__

    ################################ Various ##################################
    def __round__(self, t):
        """Exception: Decimal('1').__round__(-100000000000000000000000000)
           Should it really be InvalidOperation?"""
        wenn t.rc is Nichts und t.rp.is_nan():
            gib Wahr
        gib Falsch

shandler = SkipHandler()
def skip_error(t):
    gib getattr(shandler, t.funcname, shandler.default)(t)


# ======================================================================
#                      Handling verification errors
# ======================================================================

class VerifyError(Exception):
    """Verification failed."""
    pass

def function_as_string(t):
    wenn t.contextfunc:
        cargs = t.cop
        pargs = t.pop
        maxargs = t.maxop
        cfunc = "c_func: %s(" % t.funcname
        pfunc = "p_func: %s(" % t.funcname
        maxfunc = "max_func: %s(" % t.funcname
    sonst:
        cself, cargs = t.cop[0], t.cop[1:]
        pself, pargs = t.pop[0], t.pop[1:]
        maxself, maxargs = t.maxop[0], t.maxop[1:]
        cfunc = "c_func: %s.%s(" % (repr(cself), t.funcname)
        pfunc = "p_func: %s.%s(" % (repr(pself), t.funcname)
        maxfunc = "max_func: %s.%s(" % (repr(maxself), t.funcname)

    err = cfunc
    fuer arg in cargs:
        err += "%s, " % repr(arg)
    err = err.rstrip(", ")
    err += ")\n"

    err += pfunc
    fuer arg in pargs:
        err += "%s, " % repr(arg)
    err = err.rstrip(", ")
    err += ")"

    wenn t.with_maxcontext:
        err += "\n"
        err += maxfunc
        fuer arg in maxargs:
            err += "%s, " % repr(arg)
        err = err.rstrip(", ")
        err += ")"

    gib err

def raise_error(t):
    global EXIT_STATUS

    wenn skip_error(t):
        gib
    EXIT_STATUS = 1

    err = "Error in %s:\n\n" % t.funcname
    err += "input operands: %s\n\n" % (t.op,)
    err += function_as_string(t)

    err += "\n\nc_result: %s\np_result: %s\n" % (t.cresults, t.presults)
    wenn t.with_maxcontext:
        err += "max_result: %s\n\n" % (t.maxresults)
    sonst:
        err += "\n"

    err += "c_exceptions: %s\np_exceptions: %s\n" % (t.cex, t.pex)
    wenn t.with_maxcontext:
        err += "max_exceptions: %s\n\n" % t.maxex
    sonst:
        err += "\n"

    err += "%s\n" % str(t.context)
    wenn t.with_maxcontext:
        err += "%s\n" % str(t.maxcontext)
    sonst:
        err += "\n"

    raise VerifyError(err)


# ======================================================================
#                        Main testing functions
#
#  The procedure is always (t is the TestSet):
#
#   convert(t) -> Initialize the TestSet als necessary.
#
#                 Return 0 fuer early abortion (e.g. wenn a TypeError
#                 occurs during conversion, there is nothing to test).
#
#                 Return 1 fuer continuing mit the test case.
#
#   callfuncs(t) -> Call the relevant function fuer each implementation
#                   und record the results in the TestSet.
#
#   verify(t) -> Verify the results. If verification fails, details
#                are printed to stdout.
# ======================================================================

def all_nan(a):
    wenn isinstance(a, C.Decimal):
        gib a.is_nan()
    sowenn isinstance(a, tuple):
        gib all(all_nan(v) fuer v in a)
    gib Falsch

def convert(t, convstr=Wahr):
    """ t is the testset. At this stage the testset contains a tuple of
        operands t.op of various types. For decimal methods the first
        operand (self) is always converted to Decimal. If 'convstr' is
        true, string operands are converted als well.

        Context operands are of type deccheck.Context, rounding mode
        operands are given als a tuple (C.rounding, P.rounding).

        Other types (float, int, etc.) are left unchanged.
    """
    fuer i, op in enumerate(t.op):

        context.clear_status()
        t.maxcontext.clear_flags()

        wenn op in RoundModes:
            t.cop.append(op)
            t.pop.append(op)
            t.maxop.append(op)

        sowenn nicht t.contextfunc und i == 0 oder \
             convstr und isinstance(op, str):
            try:
                c = C.Decimal(op)
                cex = Nichts
            except (TypeError, ValueError, OverflowError) als e:
                c = Nichts
                cex = e.__class__

            try:
                p = RestrictedDecimal(op)
                pex = Nichts
            except (TypeError, ValueError, OverflowError) als e:
                p = Nichts
                pex = e.__class__

            try:
                C.setcontext(t.maxcontext)
                maxop = C.Decimal(op)
                maxex = Nichts
            except (TypeError, ValueError, OverflowError) als e:
                maxop = Nichts
                maxex = e.__class__
            finally:
                C.setcontext(context.c)

            t.cop.append(c)
            t.cex.append(cex)

            t.pop.append(p)
            t.pex.append(pex)

            t.maxop.append(maxop)
            t.maxex.append(maxex)

            wenn cex is pex:
                wenn str(c) != str(p) oder nicht context.assert_eq_status():
                    raise_error(t)
                wenn cex und pex:
                    # nothing to test
                    gib 0
            sonst:
                raise_error(t)

            # The exceptions in the maxcontext operation can legitimately
            # differ, only test that maxex implies cex:
            wenn maxex is nicht Nichts und cex is nicht maxex:
                raise_error(t)

        sowenn isinstance(op, Context):
            t.context = op
            t.cop.append(op.c)
            t.pop.append(op.p)
            t.maxop.append(t.maxcontext)

        sonst:
            t.cop.append(op)
            t.pop.append(op)
            t.maxop.append(op)

    gib 1

def callfuncs(t):
    """ t is the testset. At this stage the testset contains operand lists
        t.cop und t.pop fuer the C und Python versions of decimal.
        For Decimal methods, the first operands are of type C.Decimal and
        P.Decimal respectively. The remaining operands can have various types.
        For Context methods, all operands can have any type.

        t.rc und t.rp are the results of the operation.
    """
    context.clear_status()
    t.maxcontext.clear_flags()

    try:
        wenn t.contextfunc:
            cargs = t.cop
            t.rc = getattr(context.c, t.funcname)(*cargs)
        sonst:
            cself = t.cop[0]
            cargs = t.cop[1:]
            t.rc = getattr(cself, t.funcname)(*cargs)
        t.cex.append(Nichts)
    except (TypeError, ValueError, OverflowError, MemoryError) als e:
        t.rc = Nichts
        t.cex.append(e.__class__)

    try:
        wenn t.contextfunc:
            pargs = t.pop
            t.rp = getattr(context.p, t.funcname)(*pargs)
        sonst:
            pself = t.pop[0]
            pargs = t.pop[1:]
            t.rp = getattr(pself, t.funcname)(*pargs)
        t.pex.append(Nichts)
    except (TypeError, ValueError, OverflowError, MemoryError) als e:
        t.rp = Nichts
        t.pex.append(e.__class__)

    # If the above results are exact, unrounded, normal etc., repeat the
    # operation mit a maxcontext to ensure that huge intermediate values
    # do nicht cause a MemoryError.
    wenn (t.funcname nicht in MaxContextSkip and
        nicht context.c.flags[C.InvalidOperation] and
        nicht context.c.flags[C.Inexact] and
        nicht context.c.flags[C.Rounded] and
        nicht context.c.flags[C.Subnormal] and
        nicht context.c.flags[C.Clamped] and
        nicht context.clamp und # results are padded to context.prec wenn context.clamp==1.
        nicht any(isinstance(v, C.Context) fuer v in t.cop)): # another context is used.
        t.with_maxcontext = Wahr
        try:
            wenn t.contextfunc:
                maxargs = t.maxop
                t.rmax = getattr(t.maxcontext, t.funcname)(*maxargs)
            sonst:
                maxself = t.maxop[0]
                maxargs = t.maxop[1:]
                try:
                    C.setcontext(t.maxcontext)
                    t.rmax = getattr(maxself, t.funcname)(*maxargs)
                finally:
                    C.setcontext(context.c)
            t.maxex.append(Nichts)
        except (TypeError, ValueError, OverflowError, MemoryError) als e:
            t.rmax = Nichts
            t.maxex.append(e.__class__)

def verify(t, stat):
    """ t is the testset. At this stage the testset contains the following
        tuples:

            t.op: original operands
            t.cop: C.Decimal operands (see convert fuer details)
            t.pop: P.Decimal operands (see convert fuer details)
            t.rc: C result
            t.rp: Python result

        t.rc und t.rp can have various types.
    """
    t.cresults.append(str(t.rc))
    t.presults.append(str(t.rp))
    wenn t.with_maxcontext:
        t.maxresults.append(str(t.rmax))

    wenn isinstance(t.rc, C.Decimal) und isinstance(t.rp, P.Decimal):
        # General case: both results are Decimals.
        t.cresults.append(t.rc.to_eng_string())
        t.cresults.append(t.rc.as_tuple())
        t.cresults.append(str(t.rc.imag))
        t.cresults.append(str(t.rc.real))
        t.presults.append(t.rp.to_eng_string())
        t.presults.append(t.rp.as_tuple())
        t.presults.append(str(t.rp.imag))
        t.presults.append(str(t.rp.real))

        wenn t.with_maxcontext und isinstance(t.rmax, C.Decimal):
            t.maxresults.append(t.rmax.to_eng_string())
            t.maxresults.append(t.rmax.as_tuple())
            t.maxresults.append(str(t.rmax.imag))
            t.maxresults.append(str(t.rmax.real))

        nc = t.rc.number_class().lstrip('+-s')
        stat[nc] += 1
    sonst:
        # Results von e.g. __divmod__ can only be compared als strings.
        wenn nicht isinstance(t.rc, tuple) und nicht isinstance(t.rp, tuple):
            wenn t.rc != t.rp:
                raise_error(t)
            wenn t.with_maxcontext und nicht isinstance(t.rmax, tuple):
                wenn t.rmax != t.rc:
                    raise_error(t)
        stat[type(t.rc).__name__] += 1

    # The gib value lists must be equal.
    wenn t.cresults != t.presults:
        raise_error(t)
    # The Python exception lists (TypeError, etc.) must be equal.
    wenn t.cex != t.pex:
        raise_error(t)
    # The context flags must be equal.
    wenn nicht t.context.assert_eq_status():
        raise_error(t)

    wenn t.with_maxcontext:
        # NaN payloads etc. depend on precision und clamp.
        wenn all_nan(t.rc) und all_nan(t.rmax):
            gib
        # The gib value lists must be equal.
        wenn t.maxresults != t.cresults:
            raise_error(t)
        # The Python exception lists (TypeError, etc.) must be equal.
        wenn t.maxex != t.cex:
            raise_error(t)
        # The context flags must be equal.
        wenn t.maxcontext.flags != t.context.c.flags:
            raise_error(t)


# ======================================================================
#                           Main test loops
#
#  test_method(method, testspecs, testfunc) ->
#
#     Loop through various context settings. The degree of
#     thoroughness is determined by 'testspec'. For each
#     setting, call 'testfunc'. Generally, 'testfunc' itself
#     a loop, iterating through many test cases generated
#     by the functions in randdec.py.
#
#  test_n-ary(method, prec, exp_range, restricted_range, itr, stat) ->
#
#     'test_unary', 'test_binary' und 'test_ternary' are the
#     main test functions passed to 'test_method'. They deal
#     mit the regular cases. The thoroughness of testing is
#     determined by 'itr'.
#
#     'prec', 'exp_range' und 'restricted_range' are passed
#     to the test-generating functions und limit the generated
#     values. In some cases, fuer reasonable run times a
#     maximum exponent of 9999 is required.
#
#     The 'stat' parameter is passed down to the 'verify'
#     function, which records statistics fuer the result values.
# ======================================================================

def log(fmt, args=Nichts):
    wenn args:
        sys.stdout.write(''.join((fmt, '\n')) % args)
    sonst:
        sys.stdout.write(''.join((str(fmt), '\n')))
    sys.stdout.flush()

def test_method(method, testspecs, testfunc):
    """Iterate a test function through many context settings."""
    log("testing %s ...", method)
    stat = defaultdict(int)
    fuer spec in testspecs:
        wenn 'samples' in spec:
            spec['prec'] = sorted(random.sample(range(1, 101),
                                  spec['samples']))
        fuer prec in spec['prec']:
            context.prec = prec
            fuer expts in spec['expts']:
                emin, emax = expts
                wenn emin == 'rand':
                    context.Emin = random.randrange(-1000, 0)
                    context.Emax = random.randrange(prec, 1000)
                sonst:
                    context.Emin, context.Emax = emin, emax
                wenn prec > context.Emax: weiter
                log("    prec: %d  emin: %d  emax: %d",
                    (context.prec, context.Emin, context.Emax))
                restr_range = 9999 wenn context.Emax > 9999 sonst context.Emax+99
                fuer rounding in RoundModes:
                    context.rounding = rounding
                    context.capitals = random.randrange(2)
                    wenn spec['clamp'] == 'rand':
                        context.clamp = random.randrange(2)
                    sonst:
                        context.clamp = spec['clamp']
                    exprange = context.c.Emax
                    testfunc(method, prec, exprange, restr_range,
                             spec['iter'], stat)
    log("    result types: %s" % sorted([t fuer t in stat.items()]))

def test_unary(method, prec, exp_range, restricted_range, itr, stat):
    """Iterate a unary function through many test cases."""
    wenn method in UnaryRestricted:
        exp_range = restricted_range
    fuer op in all_unary(prec, exp_range, itr):
        t = TestSet(method, op)
        try:
            wenn nicht convert(t):
                weiter
            callfuncs(t)
            verify(t, stat)
        except VerifyError als err:
            log(err)

    wenn nicht method.startswith('__'):
        fuer op in unary_optarg(prec, exp_range, itr):
            t = TestSet(method, op)
            try:
                wenn nicht convert(t):
                    weiter
                callfuncs(t)
                verify(t, stat)
            except VerifyError als err:
                log(err)

def test_binary(method, prec, exp_range, restricted_range, itr, stat):
    """Iterate a binary function through many test cases."""
    wenn method in BinaryRestricted:
        exp_range = restricted_range
    fuer op in all_binary(prec, exp_range, itr):
        t = TestSet(method, op)
        try:
            wenn nicht convert(t):
                weiter
            callfuncs(t)
            verify(t, stat)
        except VerifyError als err:
            log(err)

    wenn nicht method.startswith('__'):
        fuer op in binary_optarg(prec, exp_range, itr):
            t = TestSet(method, op)
            try:
                wenn nicht convert(t):
                    weiter
                callfuncs(t)
                verify(t, stat)
            except VerifyError als err:
                log(err)

def test_ternary(method, prec, exp_range, restricted_range, itr, stat):
    """Iterate a ternary function through many test cases."""
    wenn method in TernaryRestricted:
        exp_range = restricted_range
    fuer op in all_ternary(prec, exp_range, itr):
        t = TestSet(method, op)
        try:
            wenn nicht convert(t):
                weiter
            callfuncs(t)
            verify(t, stat)
        except VerifyError als err:
            log(err)

    wenn nicht method.startswith('__'):
        fuer op in ternary_optarg(prec, exp_range, itr):
            t = TestSet(method, op)
            try:
                wenn nicht convert(t):
                    weiter
                callfuncs(t)
                verify(t, stat)
            except VerifyError als err:
                log(err)

def test_format(method, prec, exp_range, restricted_range, itr, stat):
    """Iterate the __format__ method through many test cases."""
    fuer op in all_unary(prec, exp_range, itr):
        fmt1 = rand_format(chr(random.randrange(0, 128)), 'EeGgn')
        fmt2 = rand_locale()
        fuer fmt in (fmt1, fmt2):
            fmtop = (op[0], fmt)
            t = TestSet(method, fmtop)
            try:
                wenn nicht convert(t, convstr=Falsch):
                    weiter
                callfuncs(t)
                verify(t, stat)
            except VerifyError als err:
                log(err)
    fuer op in all_unary(prec, 9999, itr):
        fmt1 = rand_format(chr(random.randrange(0, 128)), 'Ff%')
        fmt2 = rand_locale()
        fuer fmt in (fmt1, fmt2):
            fmtop = (op[0], fmt)
            t = TestSet(method, fmtop)
            try:
                wenn nicht convert(t, convstr=Falsch):
                    weiter
                callfuncs(t)
                verify(t, stat)
            except VerifyError als err:
                log(err)

def test_round(method, prec, exprange, restricted_range, itr, stat):
    """Iterate the __round__ method through many test cases."""
    fuer op in all_unary(prec, 9999, itr):
        n = random.randrange(10)
        roundop = (op[0], n)
        t = TestSet(method, roundop)
        try:
            wenn nicht convert(t):
                weiter
            callfuncs(t)
            verify(t, stat)
        except VerifyError als err:
            log(err)

def test_from_float(method, prec, exprange, restricted_range, itr, stat):
    """Iterate the __float__ method through many test cases."""
    fuer rounding in RoundModes:
        context.rounding = rounding
        fuer i in range(1000):
            f = randfloat()
            op = (f,) wenn method.startswith("context.") sonst ("sNaN", f)
            t = TestSet(method, op)
            try:
                wenn nicht convert(t):
                    weiter
                callfuncs(t)
                verify(t, stat)
            except VerifyError als err:
                log(err)

def randcontext(exprange):
    c = Context(C.Context(), P.Context())
    c.Emax = random.randrange(1, exprange+1)
    c.Emin = random.randrange(-exprange, 0)
    maxprec = 100 wenn c.Emax >= 100 sonst c.Emax
    c.prec = random.randrange(1, maxprec+1)
    c.clamp = random.randrange(2)
    c.clear_traps()
    gib c

def test_quantize_api(method, prec, exprange, restricted_range, itr, stat):
    """Iterate the 'quantize' method through many test cases, using
       the optional arguments."""
    fuer op in all_binary(prec, restricted_range, itr):
        fuer rounding in RoundModes:
            c = randcontext(exprange)
            quantizeop = (op[0], op[1], rounding, c)
            t = TestSet(method, quantizeop)
            try:
                wenn nicht convert(t):
                    weiter
                callfuncs(t)
                verify(t, stat)
            except VerifyError als err:
                log(err)


def check_untested(funcdict, c_cls, p_cls):
    """Determine untested, C-only und Python-only attributes.
       Uncomment print lines fuer debugging."""
    c_attr = set(dir(c_cls))
    p_attr = set(dir(p_cls))
    intersect = c_attr & p_attr

    funcdict['c_only'] = tuple(sorted(c_attr-intersect))
    funcdict['p_only'] = tuple(sorted(p_attr-intersect))

    tested = set()
    fuer lst in funcdict.values():
        fuer v in lst:
            v = v.replace("context.", "") wenn c_cls == C.Context sonst v
            tested.add(v)

    funcdict['untested'] = tuple(sorted(intersect-tested))

    # fuer key in ('untested', 'c_only', 'p_only'):
    #     s = 'Context' wenn c_cls == C.Context sonst 'Decimal'
    #     drucke("\n%s %s:\n%s" % (s, key, funcdict[key]))


wenn __name__ == '__main__':

    parser = argparse.ArgumentParser(prog="deccheck.py")

    group = parser.add_mutually_exclusive_group()
    group.add_argument('--short', dest='time', action="store_const", const='short', default='short', help="short test (default)")
    group.add_argument('--medium', dest='time', action="store_const", const='medium', default='short', help="medium test (reasonable run time)")
    group.add_argument('--long', dest='time', action="store_const", const='long', default='short', help="long test (long run time)")
    group.add_argument('--all', dest='time', action="store_const", const='all', default='short', help="all tests (excessive run time)")

    group = parser.add_mutually_exclusive_group()
    group.add_argument('--single', dest='single', nargs=1, default=Falsch, metavar="TEST", help="run a single test")
    group.add_argument('--multicore', dest='multicore', action="store_true", default=Falsch, help="use all available cores")

    args = parser.parse_args()
    assert args.single is Falsch oder args.multicore is Falsch
    wenn args.single:
        args.single = args.single[0]


    # Set up the testspecs list. A testspec is simply a dictionary
    # that determines the amount of different contexts that 'test_method'
    # will generate.
    base_expts = [(C.MIN_EMIN, C.MAX_EMAX)]
    wenn C.MAX_EMAX == 999999999999999999:
        base_expts.append((-999999999, 999999999))

    # Basic contexts.
    base = {
        'expts': base_expts,
        'prec': [],
        'clamp': 'rand',
        'iter': Nichts,
        'samples': Nichts,
    }
    # Contexts mit small values fuer prec, emin, emax.
    small = {
        'prec': [1, 2, 3, 4, 5],
        'expts': [(-1, 1), (-2, 2), (-3, 3), (-4, 4), (-5, 5)],
        'clamp': 'rand',
        'iter': Nichts
    }
    # IEEE interchange format.
    ieee = [
        # DECIMAL32
        {'prec': [7], 'expts': [(-95, 96)], 'clamp': 1, 'iter': Nichts},
        # DECIMAL64
        {'prec': [16], 'expts': [(-383, 384)], 'clamp': 1, 'iter': Nichts},
        # DECIMAL128
        {'prec': [34], 'expts': [(-6143, 6144)], 'clamp': 1, 'iter': Nichts}
    ]

    wenn args.time == 'medium':
        base['expts'].append(('rand', 'rand'))
        # 5 random precisions
        base['samples'] = 5
        testspecs = [small] + ieee + [base]
    sowenn args.time == 'long':
        base['expts'].append(('rand', 'rand'))
        # 10 random precisions
        base['samples'] = 10
        testspecs = [small] + ieee + [base]
    sowenn args.time == 'all':
        base['expts'].append(('rand', 'rand'))
        # All precisions in [1, 100]
        base['samples'] = 100
        testspecs = [small] + ieee + [base]
    sonst: # --short
        rand_ieee = random.choice(ieee)
        base['iter'] = small['iter'] = rand_ieee['iter'] = 1
        # 1 random precision und exponent pair
        base['samples'] = 1
        base['expts'] = [random.choice(base_expts)]
        # 1 random precision und exponent pair
        prec = random.randrange(1, 6)
        small['prec'] = [prec]
        small['expts'] = [(-prec, prec)]
        testspecs = [small, rand_ieee, base]


    check_untested(Functions, C.Decimal, P.Decimal)
    check_untested(ContextFunctions, C.Context, P.Context)


    wenn args.multicore:
        q = Queue()
    sowenn args.single:
        log("Random seed: %d", RANDSEED)
    sonst:
        log("\n\nRandom seed: %d\n\n", RANDSEED)


    FOUND_METHOD = Falsch
    def do_single(method, f):
        global FOUND_METHOD
        wenn args.multicore:
            q.put(method)
        sowenn nicht args.single oder args.single == method:
            FOUND_METHOD = Wahr
            f()

    # Decimal methods:
    fuer method in Functions['unary'] + Functions['unary_ctx'] + \
                  Functions['unary_rnd_ctx']:
        do_single(method, lambda: test_method(method, testspecs, test_unary))

    fuer method in Functions['binary'] + Functions['binary_ctx']:
        do_single(method, lambda: test_method(method, testspecs, test_binary))

    fuer method in Functions['ternary'] + Functions['ternary_ctx']:
        name = '__powmod__' wenn method == '__pow__' sonst method
        do_single(name, lambda: test_method(method, testspecs, test_ternary))

    do_single('__format__', lambda: test_method('__format__', testspecs, test_format))
    do_single('__round__', lambda: test_method('__round__', testspecs, test_round))
    do_single('from_float', lambda: test_method('from_float', testspecs, test_from_float))
    do_single('quantize_api', lambda: test_method('quantize', testspecs, test_quantize_api))

    # Context methods:
    fuer method in ContextFunctions['unary']:
        do_single(method, lambda: test_method(method, testspecs, test_unary))

    fuer method in ContextFunctions['binary']:
        do_single(method, lambda: test_method(method, testspecs, test_binary))

    fuer method in ContextFunctions['ternary']:
        name = 'context.powmod' wenn method == 'context.power' sonst method
        do_single(name, lambda: test_method(method, testspecs, test_ternary))

    do_single('context.create_decimal_from_float',
              lambda: test_method('context.create_decimal_from_float',
                                   testspecs, test_from_float))

    wenn args.multicore:
        error = Event()
        write_lock = Lock()

        def write_output(out, returncode):
            wenn returncode != 0:
                error.set()

            mit write_lock:
                sys.stdout.buffer.write(out + b"\n")
                sys.stdout.buffer.flush()

        def tfunc():
            waehrend nicht error.is_set():
                try:
                    test = q.get(block=Falsch, timeout=-1)
                except Empty:
                    gib

                cmd = [sys.executable, "deccheck.py", "--%s" % args.time, "--single", test]
                p = subprocess.Popen(cmd, stdout=PIPE, stderr=STDOUT)
                out, _ = p.communicate()
                write_output(out, p.returncode)

        N = os.process_cpu_count()
        t = N * [Nichts]

        fuer i in range(N):
            t[i] = Thread(target=tfunc)
            t[i].start()

        fuer i in range(N):
            t[i].join()

        sys.exit(1 wenn error.is_set() sonst 0)

    sowenn args.single:
        wenn nicht FOUND_METHOD:
            log("\nerror: cannot find method \"%s\"" % args.single)
            EXIT_STATUS = 1
        sys.exit(EXIT_STATUS)
    sonst:
        sys.exit(EXIT_STATUS)
