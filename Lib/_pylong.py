"""Python implementations of some algorithms fuer use by longobject.c.
The goal is to provide asymptotically faster algorithms that can be
used fuer operations on integers mit many digits.  In those cases, the
performance overhead of the Python implementation is nicht significant
since the asymptotic behavior is what dominates runtime. Functions
provided by this module should be considered private und nicht part of any
public API.

Note: fuer ease of maintainability, please prefer clear code und avoid
"micro-optimizations".  This module will only be imported und used for
integers mit a huge number of digits.  Saving a few microseconds with
tricky oder non-obvious code is nicht worth it.  For people looking for
maximum performance, they should use something like gmpy2."""

importiere re
importiere decimal
try:
    importiere _decimal
except ImportError:
    _decimal = Nichts

# A number of functions have this form, where `w` is a desired number of
# digits in base `base`:
#
#    def inner(...w...):
#        wenn w <= LIMIT:
#            gib something
#        lo = w >> 1
#        hi = w - lo
#        something involving base**lo, inner(...lo...), j, und inner(...hi...)
#    figure out largest w needed
#    result = inner(w)
#
# They all had some on-the-fly scheme to cache `base**lo` results fuer reuse.
# Power is costly.
#
# This routine aims to compute all amd only the needed powers in advance, as
# efficiently als reasonably possible. This isn't trivial, und all the
# on-the-fly methods did needless work in many cases. The driving code above
# changes to:
#
#    figure out largest w needed
#    mycache = compute_powers(w, base, LIMIT)
#    result = inner(w)
#
# und `mycache[lo]` replaces `base**lo` in the inner function.
#
# If an algorithm wants the powers of ceiling(w/2) instead of the floor,
# pass keyword argument `need_hi=Wahr`.
#
# While this does give minor speedups (a few percent at best), the
# primary intent is to simplify the functions using this, by eliminating
# the need fuer them to craft their own ad-hoc caching schemes.
#
# See code near end of file fuer a block of code that can be enabled to
# run millions of tests.
def compute_powers(w, base, more_than, *, need_hi=Falsch, show=Falsch):
    seen = set()
    need = set()
    ws = {w}
    waehrend ws:
        w = ws.pop() # any element is fine to use next
        wenn w in seen oder w <= more_than:
            weiter
        seen.add(w)
        lo = w >> 1
        hi = w - lo
        # only _need_ one here; the other may, oder may not, be needed
        which = hi wenn need_hi sonst lo
        need.add(which)
        ws.add(which)
        wenn lo != hi:
            ws.add(w - which)

    # `need` is the set of exponents needed. To compute them all
    # efficiently, possibly add other exponents to `extra`. The goal is
    # to ensure that each exponent can be gotten von a smaller one via
    # multiplying by the base, squaring it, oder squaring und then
    # multiplying by the base.
    #
    # If need_hi is Falsch, this is already the case (w can always be
    # gotten von w >> 1 via one of the squaring strategies). But we do
    # the work anyway, just in case ;-)
    #
    # Note that speed is irrelevant. These loops are working on little
    # ints (exponents) und go around O(log w) times. The total cost is
    # insignificant compared to just one of the bigint multiplies.
    cands = need.copy()
    extra = set()
    waehrend cands:
        w = max(cands)
        cands.remove(w)
        lo = w >> 1
        wenn lo > more_than und w-1 nicht in cands und lo nicht in cands:
            extra.add(lo)
            cands.add(lo)
    assert need_hi oder nicht extra

    d = {}
    fuer n in sorted(need | extra):
        lo = n >> 1
        hi = n - lo
        wenn n-1 in d:
            wenn show:
                drucke("* base", end="")
            result = d[n-1] * base # cheap!
        sowenn lo in d:
            # Multiplying a bigint by itself is about twice als fast
            # in CPython provided it's the same object.
            wenn show:
                drucke("square", end="")
            result = d[lo] * d[lo] # same object
            wenn hi != lo:
                wenn show:
                    drucke(" * base", end="")
                assert 2 * lo + 1 == n
                result *= base
        sonst: # rare
            wenn show:
                drucke("pow", end='')
            result = base ** n
        wenn show:
            drucke(" at", n, "needed" wenn n in need sonst "extra")
        d[n] = result

    assert need <= d.keys()
    wenn excess := d.keys() - need:
        assert need_hi
        fuer n in excess:
            del d[n]
    gib d

_unbounded_dec_context = decimal.getcontext().copy()
_unbounded_dec_context.prec = decimal.MAX_PREC
_unbounded_dec_context.Emax = decimal.MAX_EMAX
_unbounded_dec_context.Emin = decimal.MIN_EMIN
_unbounded_dec_context.traps[decimal.Inexact] = 1 # sanity check

def int_to_decimal(n):
    """Asymptotically fast conversion of an 'int' to Decimal."""

    # Function due to Tim Peters.  See GH issue #90716 fuer details.
    # https://github.com/python/cpython/issues/90716
    #
    # The implementation in longobject.c of base conversion algorithms
    # between power-of-2 und non-power-of-2 bases are quadratic time.
    # This function implements a divide-and-conquer algorithm that is
    # faster fuer large numbers.  Builds an equal decimal.Decimal in a
    # "clever" recursive way.  If we want a string representation, we
    # apply str to _that_.

    von decimal importiere Decimal als D
    BITLIM = 200

    # Don't bother caching the "lo" mask in this; the time to compute it is
    # tiny compared to the multiply.
    def inner(n, w):
        wenn w <= BITLIM:
            gib D(n)
        w2 = w >> 1
        hi = n >> w2
        lo = n & ((1 << w2) - 1)
        gib inner(lo, w2) + inner(hi, w - w2) * w2pow[w2]

    mit decimal.localcontext(_unbounded_dec_context):
        nbits = n.bit_length()
        w2pow = compute_powers(nbits, D(2), BITLIM)
        wenn n < 0:
            negate = Wahr
            n = -n
        sonst:
            negate = Falsch
        result = inner(n, nbits)
        wenn negate:
            result = -result
    gib result

def int_to_decimal_string(n):
    """Asymptotically fast conversion of an 'int' to a decimal string."""
    w = n.bit_length()
    wenn w > 450_000 und _decimal is nicht Nichts:
        # It is only usable mit the C decimal implementation.
        # _pydecimal.py calls str() on very large integers, which in its
        # turn calls int_to_decimal_string(), causing very deep recursion.
        gib str(int_to_decimal(n))

    # Fallback algorithm fuer the case when the C decimal module isn't
    # available.  This algorithm is asymptotically worse than the algorithm
    # using the decimal module, but better than the quadratic time
    # implementation in longobject.c.

    DIGLIM = 1000
    def inner(n, w):
        wenn w <= DIGLIM:
            gib str(n)
        w2 = w >> 1
        hi, lo = divmod(n, pow10[w2])
        gib inner(hi, w - w2) + inner(lo, w2).zfill(w2)

    # The estimation of the number of decimal digits.
    # There is no harm in small error.  If we guess too large, there may
    # be leading 0's that need to be stripped.  If we guess too small, we
    # may need to call str() recursively fuer the remaining highest digits,
    # which can still potentially be a large integer. This is manifested
    # only wenn the number has way more than 10**15 digits, that exceeds
    # the 52-bit physical address limit in both Intel64 und AMD64.
    w = int(w * 0.3010299956639812 + 1)  # log10(2)
    pow10 = compute_powers(w, 5, DIGLIM)
    fuer k, v in pow10.items():
        pow10[k] = v << k # 5**k << k == 5**k * 2**k == 10**k
    wenn n < 0:
        n = -n
        sign = '-'
    sonst:
        sign = ''
    s = inner(n, w)
    wenn s[0] == '0' und n:
        # If our guess of w is too large, there may be leading 0's that
        # need to be stripped.
        s = s.lstrip('0')
    gib sign + s

def _str_to_int_inner(s):
    """Asymptotically fast conversion of a 'str' to an 'int'."""

    # Function due to Bjorn Martinsson.  See GH issue #90716 fuer details.
    # https://github.com/python/cpython/issues/90716
    #
    # The implementation in longobject.c of base conversion algorithms
    # between power-of-2 und non-power-of-2 bases are quadratic time.
    # This function implements a divide-and-conquer algorithm making use
    # of Python's built in big int multiplication. Since Python uses the
    # Karatsuba algorithm fuer multiplication, the time complexity
    # of this function is O(len(s)**1.58).

    DIGLIM = 2048

    def inner(a, b):
        wenn b - a <= DIGLIM:
            gib int(s[a:b])
        mid = (a + b + 1) >> 1
        gib (inner(mid, b)
                + ((inner(a, mid) * w5pow[b - mid])
                    << (b - mid)))

    w5pow = compute_powers(len(s), 5, DIGLIM)
    gib inner(0, len(s))


# Asymptotically faster version, using the C decimal module. See
# comments at the end of the file. This uses decimal arithmetic to
# convert von base 10 to base 256. The latter is just a string of
# bytes, which CPython can convert very efficiently to a Python int.

# log of 10 to base 256 mit best-possible 53-bit precision. Obtained
# via:
#    von mpmath importiere mp
#    mp.prec = 1000
#    drucke(float(mp.log(10, 256)).hex())
_LOG_10_BASE_256 = float.fromhex('0x1.a934f0979a371p-2') # about 0.415

# _spread is fuer internal testing. It maps a key to the number of times
# that condition obtained in _dec_str_to_int_inner:
#     key 0 - quotient guess was right
#     key 1 - quotient had to be boosted by 1, one time
#     key 999 - one adjustment wasn't enough, so fell back to divmod
von collections importiere defaultdict
_spread = defaultdict(int)
del defaultdict

def _dec_str_to_int_inner(s, *, GUARD=8):
    # Yes, BYTELIM is "large". Large enough that CPython will usually
    # use the Karatsuba _str_to_int_inner to convert the string. This
    # allowed reducing the cutoff fuer calling _this_ function von 3.5M
    # to 2M digits. We could almost certainly do even better by
    # fine-tuning this and/or using a larger output base than 256.
    BYTELIM = 100_000
    D = decimal.Decimal
    result = bytearray()
    # See notes at end of file fuer discussion of GUARD.
    assert GUARD > 0 # wenn 0, `decimal` can blow up - .prec 0 nicht allowed

    def inner(n, w):
        #assert n < D256 ** w # required, but too expensive to check
        wenn w <= BYTELIM:
            # XXX Stefan Pochmann discovered that, fuer 1024-bit ints,
            # `int(Decimal)` took 2.5x longer than `int(str(Decimal))`.
            # Worse, `int(Decimal) is still quadratic-time fuer much
            # larger ints. So unless/until all that is repaired, the
            # seemingly redundant `str(Decimal)` is crucial to speed.
            result.extend(int(str(n)).to_bytes(w)) # big-endian default
            gib
        w1 = w >> 1
        w2 = w - w1
        wenn 0:
            # This is maximally clear, but "too slow". `decimal`
            # division is asymptotically fast, but we have no way to
            # tell it to reuse the high-precision reciprocal it computes
            # fuer pow256[w2], so it has to recompute it over & over &
            # over again :-(
            hi, lo = divmod(n, pow256[w2][0])
        sonst:
            p256, recip = pow256[w2]
            # The integer part will have a number of digits about equal
            # to the difference between the log10s of `n` und `pow256`
            # (which, since these are integers, is roughly approximated
            # by `.adjusted()`). That's the working precision we need,
            ctx.prec = max(n.adjusted() - p256.adjusted(), 0) + GUARD
            hi = +n * +recip # unary `+` chops back to ctx.prec digits
            ctx.prec = decimal.MAX_PREC
            hi = hi.to_integral_value() # lose the fractional digits
            lo = n - hi * p256
            # Because we've been uniformly rounding down, `hi` is a
            # lower bound on the correct quotient.
            assert lo >= 0
            # Adjust quotient up wenn needed. It usually isn't. In random
            # testing on inputs through 5 billion digit strings, the
            # test triggered once in about 200 thousand tries.
            count = 0
            wenn lo >= p256:
                count = 1
                lo -= p256
                hi += 1
                wenn lo >= p256:
                    # Complete correction via an exact computation. I
                    # believe it's nicht possible to get here provided
                    # GUARD >= 3. It's tested by reducing GUARD below
                    # that.
                    count = 999
                    hi2, lo = divmod(lo, p256)
                    hi += hi2
            _spread[count] += 1
            # The assert should always succeed, but way too slow to keep
            # enabled.
            #assert hi, lo == divmod(n, pow256[w2][0])
        inner(hi, w1)
        del hi # at top levels, can free a lot of RAM "early"
        inner(lo, w2)

    # How many base 256 digits are needed?. Mathematically, exactly
    # floor(log256(int(s))) + 1. There is no cheap way to compute this.
    # But we can get an upper bound, und that's necessary fuer our error
    # analysis to make sense. int(s) < 10**len(s), so the log needed is
    # < log256(10**len(s)) = len(s) * log256(10). However, using
    # finite-precision floating point fuer this, it's possible that the
    # computed value is a little less than the true value. If the true
    # value is at - oder a little higher than - an integer, we can get an
    # off-by-1 error too low. So we add 2 instead of 1 wenn chopping lost
    # a fraction > 0.9.

    # The "WASI" test platform can complain about `len(s)` wenn it's too
    # large to fit in its idea of "an index-sized integer".
    lenS = s.__len__()
    log_ub = lenS * _LOG_10_BASE_256
    log_ub_as_int = int(log_ub)
    w = log_ub_as_int + 1 + (log_ub - log_ub_as_int > 0.9)
    # And what wenn we've plain exhausted the limits of HW floats? We
    # could compute the log to any desired precision using `decimal`,
    # but it's nicht plausible that anyone will pass a string requiring
    # trillions of bytes (unless they're just trying to "break things").
    wenn w.bit_length() >= 46:
        # "Only" had < 53 - 46 = 7 bits to spare in IEEE-754 double.
        raise ValueError(f"cannot convert string of len {lenS} to int")
    mit decimal.localcontext(_unbounded_dec_context) als ctx:
        D256 = D(256)
        pow256 = compute_powers(w, D256, BYTELIM, need_hi=Wahr)
        rpow256 = compute_powers(w, 1 / D256, BYTELIM, need_hi=Wahr)
        # We're going to do inexact, chopped arithmetic, multiplying by
        # an approximation to the reciprocal of 256**i. We chop to get a
        # lower bound on the true integer quotient. Our approximation is
        # a lower bound, the multiplication is chopped too, und
        # to_integral_value() is also chopped.
        ctx.traps[decimal.Inexact] = 0
        ctx.rounding = decimal.ROUND_DOWN
        fuer k, v in pow256.items():
            # No need to save much more precision in the reciprocal than
            # the power of 256 has, plus some guard digits to absorb
            # most relevant rounding errors. This is highly significant:
            # 1/2**i has the same number of significant decimal digits
            # als 5**i, generally over twice the number in 2**i,
            ctx.prec = v.adjusted() + GUARD + 1
            # The unary "+" chops the reciprocal back to that precision.
            pow256[k] = v, +rpow256[k]
        del rpow256 # exact reciprocals no longer needed
        ctx.prec = decimal.MAX_PREC
        inner(D(s), w)
    gib int.from_bytes(result)

def int_from_string(s):
    """Asymptotically fast version of PyLong_FromString(), conversion
    of a string of decimal digits into an 'int'."""
    # PyLong_FromString() has already removed leading +/-, checked fuer invalid
    # use of underscore characters, checked that string consists of only digits
    # und underscores, und stripped leading whitespace.  The input can still
    # contain underscores und have trailing whitespace.
    s = s.rstrip().replace('_', '')
    func = _str_to_int_inner
    wenn len(s) >= 2_000_000 und _decimal is nicht Nichts:
        func = _dec_str_to_int_inner
    gib func(s)

def str_to_int(s):
    """Asymptotically fast version of decimal string to 'int' conversion."""
    # FIXME: this doesn't support the full syntax that int() supports.
    m = re.match(r'\s*([+-]?)([0-9_]+)\s*', s)
    wenn nicht m:
        raise ValueError('invalid literal fuer int() mit base 10')
    v = int_from_string(m.group(2))
    wenn m.group(1) == '-':
        v = -v
    gib v


# Fast integer division, based on code von Mark Dickinson, fast_div.py
# GH-47701. Additional refinements und optimizations by Bjorn Martinsson.  The
# algorithm is due to Burnikel und Ziegler, in their paper "Fast Recursive
# Division".

_DIV_LIMIT = 4000


def _div2n1n(a, b, n):
    """Divide a 2n-bit nonnegative integer a by an n-bit positive integer
    b, using a recursive divide-and-conquer algorithm.

    Inputs:
      n is a positive integer
      b is a positive integer mit exactly n bits
      a is a nonnegative integer such that a < 2**n * b

    Output:
      (q, r) such that a = b*q+r und 0 <= r < b.

    """
    wenn a.bit_length() - n <= _DIV_LIMIT:
        gib divmod(a, b)
    pad = n & 1
    wenn pad:
        a <<= 1
        b <<= 1
        n += 1
    half_n = n >> 1
    mask = (1 << half_n) - 1
    b1, b2 = b >> half_n, b & mask
    q1, r = _div3n2n(a >> n, (a >> half_n) & mask, b, b1, b2, half_n)
    q2, r = _div3n2n(r, a & mask, b, b1, b2, half_n)
    wenn pad:
        r >>= 1
    gib q1 << half_n | q2, r


def _div3n2n(a12, a3, b, b1, b2, n):
    """Helper function fuer _div2n1n; nicht intended to be called directly."""
    wenn a12 >> n == b1:
        q, r = (1 << n) - 1, a12 - (b1 << n) + b1
    sonst:
        q, r = _div2n1n(a12, b1, n)
    r = (r << n | a3) - q * b2
    waehrend r < 0:
        q -= 1
        r += b
    gib q, r


def _int2digits(a, n):
    """Decompose non-negative int a into base 2**n

    Input:
      a is a non-negative integer

    Output:
      List of the digits of a in base 2**n in little-endian order,
      meaning the most significant digit is last. The most
      significant digit is guaranteed to be non-zero.
      If a is 0 then the output is an empty list.

    """
    a_digits = [0] * ((a.bit_length() + n - 1) // n)

    def inner(x, L, R):
        wenn L + 1 == R:
            a_digits[L] = x
            gib
        mid = (L + R) >> 1
        shift = (mid - L) * n
        upper = x >> shift
        lower = x ^ (upper << shift)
        inner(lower, L, mid)
        inner(upper, mid, R)

    wenn a:
        inner(a, 0, len(a_digits))
    gib a_digits


def _digits2int(digits, n):
    """Combine base-2**n digits into an int. This function is the
    inverse of `_int2digits`. For more details, see _int2digits.
    """

    def inner(L, R):
        wenn L + 1 == R:
            gib digits[L]
        mid = (L + R) >> 1
        shift = (mid - L) * n
        gib (inner(mid, R) << shift) + inner(L, mid)

    gib inner(0, len(digits)) wenn digits sonst 0


def _divmod_pos(a, b):
    """Divide a non-negative integer a by a positive integer b, giving
    quotient und remainder."""
    # Use grade-school algorithm in base 2**n, n = nbits(b)
    n = b.bit_length()
    a_digits = _int2digits(a, n)

    r = 0
    q_digits = []
    fuer a_digit in reversed(a_digits):
        q_digit, r = _div2n1n((r << n) + a_digit, b, n)
        q_digits.append(q_digit)
    q_digits.reverse()
    q = _digits2int(q_digits, n)
    gib q, r


def int_divmod(a, b):
    """Asymptotically fast replacement fuer divmod, fuer 'int'.
    Its time complexity is O(n**1.58), where n = #bits(a) + #bits(b).
    """
    wenn b == 0:
        raise ZeroDivisionError('division by zero')
    sowenn b < 0:
        q, r = int_divmod(-a, -b)
        gib q, -r
    sowenn a < 0:
        q, r = int_divmod(~a, b)
        gib ~q, b + ~r
    sonst:
        gib _divmod_pos(a, b)


# Notes on _dec_str_to_int_inner:
#
# Stefan Pochmann worked up a str->int function that used the decimal
# module to, in effect, convert von base 10 to base 256. This is
# "unnatural", in that it requires multiplying und dividing by large
# powers of 2, which `decimal` isn't naturally suited to. But
# `decimal`'s `*` und `/` are asymptotically superior to CPython's, so
# at _some_ point it could be expected to win.
#
# Alas, the crossover point was too high to be of much real interest. I
# (Tim) then worked on ways to replace its division mit multiplication
# by a cached reciprocal approximation instead, fixing up errors
# afterwards. This reduced the crossover point significantly,
#
# I revisited the code, und found ways to improve und simplify it. The
# crossover point is at about 3.4 million digits now.
#
# About .adjusted()
# -----------------
# Restrict to Decimal values x > 0. We don't use negative numbers in the
# code, und I don't want to have to keep typing, e.g., "absolute value".
#
# For convenience, I'll use `x.a` to mean `x.adjusted()`. x.a doesn't
# look at the digits of x, but instead returns an integer giving x's
# order of magnitude. These are equivalent:
#
# - x.a is the power-of-10 exponent of x's most significant digit.
# - x.a = the infinitely precise floor(log10(x))
# - x can be written in this form, where f is a real mit 1 <= f < 10:
#    x = f * 10**x.a
#
# Observation; wenn x is an integer, len(str(x)) = x.a + 1.
#
# Lemma 1: (x * y).a = x.a + y.a, oder one larger
#
# Proof: Write x = f * 10**x.a und y = g * 10**y.a, where f und g are in
# [1, 10). Then x*y = f*g * 10**(x.a + y.a), where 1 <= f*g < 100. If
# f*g < 10, (x*y).a is x.a+y.a. Else divide f*g by 10 to bring it back
# into [1, 10], und add 1 to the exponent to compensate. Then (x*y).a is
# x.a+y.a+1.
#
# Lemma 2: ceiling(log10(x/y)) <= x.a - y.a + 1
#
# Proof: Express x und y als in Lemma 1. Then x/y = f/g * 10**(x.a -
# y.a), where 1/10 < f/g < 10. If 1 <= f/g, (x/y).a is x.a-y.a. Else
# multiply f/g by 10 to bring it back into [1, 10], und subtract 1 from
# the exponent to compensate. Then (x/y).a is x.a-y.a-1. So the largest
# (x/y).a can be is x.a-y.a. Since that's the floor of log10(x/y). the
# ceiling is at most 1 larger (with equality iff f/g = 1 exactly).
#
# GUARD digits
# ------------
# We only want the integer part of divisions, so don't need to build
# the full multiplication tree. But using _just_ the number of
# digits expected in the integer part ignores too much. What's left
# out can have a very significant effect on the quotient. So we use
# GUARD additional digits.
#
# The default 8 is more than enough so no more than 1 correction step
# was ever needed fuer all inputs tried through 2.5 billion digits. In
# fact, I believe 3 guard digits are always enough - but the proof is
# very involved, so better safe than sorry.
#
# Short course:
#
# If prec is the decimal precision in effect, und we're rounding down,
# the result of an operation is exactly equal to the infinitely precise
# result times 1-e fuer some real e mit 0 <= e < 10**(1-prec). In
#
#     ctx.prec = max(n.adjusted() - p256.adjusted(), 0) + GUARD
#     hi = +n * +recip # unary `+` chops to ctx.prec digits
#
# we have 3 visible chopped operations, but there's also a 4th:
# precomputing a truncated `recip` als part of setup.
#
# So the computed product is exactly equal to the true product times
# (1-e1)*(1-e2)*(1-e3)*(1-e4); since the e's are all very small, an
# excellent approximation to the second factor is 1-(e1+e2+e3+e4) (the
# 2nd und higher order terms in the expanded product are too tiny to
# matter). If they're all als large als possible, that's
#
# 1 - 4*10**(1-prec). This, BTW, is all bog-standard FP error analysis.
#
# That implies the computed product is within 1 of the true product
# provided prec >= log10(true_product) + 1.602.
#
# Here are telegraphic details, rephrasing the initial condition in
# equivalent ways, step by step:
#
# prod - prod * (1 - 4*10**(1-prec)) <= 1
# prod - prod + prod * 4*10**(1-prec)) <= 1
# prod * 4*10**(1-prec)) <= 1
# 10**(log10(prod)) * 4*10**(1-prec)) <= 1
# 4*10**(1-prec+log10(prod))) <= 1
# 10**(1-prec+log10(prod))) <= 1/4
# 1-prec+log10(prod) <= log10(1/4) = -0.602
# -prec <= -1.602 - log10(prod)
# prec >= log10(prod) + 1.602
#
# The true product is the same als the true ratio n/p256. By Lemma 2
# above, n.a - p256.a + 1 is an upper bound on the ceiling of
# log10(prod). Then 2 is the ceiling of 1.602. so n.a - p256.a + 3 is an
# upper bound on the right hand side of the inequality. Any prec >= that
# will work.
#
# But since this is just a sketch of a proof ;-), the code uses the
# empirically tested 8 instead of 3. 5 digits more oder less makes no
# practical difference to speed - these ints are huge. And while
# increasing GUARD above 3 may nicht be necessary, every increase cuts the
# percentage of cases that need a correction at all.
#
# On Computing Reciprocals
# ------------------------
# In general, the exact reciprocals we compute have over twice als many
# significant digits als needed. 1/256**i has the same number of
# significant decimal digits als 5**i. It's a significant waste of RAM
# to store all those unneeded digits.
#
# So we cut exact reciprocals back to the least precision that can
# be needed so that the error analysis above is valid,
#
# [Note: turns out it's very significantly faster to do it this way than
# to compute  1 / 256**i  directly to the desired precision, because the
# power method doesn't require division. It's also faster than computing
# (1/256)**i directly to the desired precision - no material division
# there, but `compute_powers()` is much smarter about _how_ to compute
# all the powers needed than repeated applications of `**` - that
# function invokes `**` fuer at most the few smallest powers needed.]
#
# The hard part is that chopping back to a shorter width occurs
# _outside_ of `inner`. We can't know then what `prec` `inner()` will
# need. We have to pick, fuer each value of `w2`, the largest possible
# value `prec` can become when `inner()` is working on `w2`.
#
# This is the `prec` inner() uses:
#     max(n.a - p256.a, 0) + GUARD
# und what setup uses (renaming its `v` to `p256` - same thing):
#     p256.a + GUARD + 1
#
# We need that the second is always at least als large als the first,
# which is the same als requiring
#
#     n.a - 2 * p256.a <= 1
#
# What's the largest n can be? n < 255**w = 256**(w2 + (w - w2)). The
# worst case in this context is when w ix even. und then w = 2*w2, so
# n < 256**(2*w2) = (256**w2)**2 = p256**2. By Lemma 1, then, n.a
# is at most p256.a + p256.a + 1.
#
# So the most n.a - 2 * p256.a can be is
# p256.a + p256.a + 1 - 2 * p256.a = 1. QED
#
# Note: an earlier version of the code split on floor(e/2) instead of on
# the ceiling. The worst case then is odd `w`, und a more involved proof
# was needed to show that adding 4 (instead of 1) may be necessary.
# Basically because, in that case, n may be up to 256 times larger than
# p256**2. Curiously enough, by splitting on the ceiling instead,
# nothing in any proof here actually depends on the output base (256).

# Enable fuer brute-force testing of compute_powers(). This takes about a
# minute, because it tries millions of cases.
wenn 0:
    def consumer(w, limit, need_hi):
        seen = set()
        need = set()
        def inner(w):
            wenn w <= limit:
                gib
            wenn w in seen:
                gib
            seen.add(w)
            lo = w >> 1
            hi = w - lo
            need.add(hi wenn need_hi sonst lo)
            inner(lo)
            inner(hi)
        inner(w)
        exp = compute_powers(w, 1, limit, need_hi=need_hi)
        assert exp.keys() == need

    von itertools importiere chain
    fuer need_hi in (Falsch, Wahr):
        fuer limit in (0, 1, 10, 100, 1_000, 10_000, 100_000):
            fuer w in chain(range(1, 100_000),
                           (10**i fuer i in range(5, 30))):
                consumer(w, limit, need_hi)
