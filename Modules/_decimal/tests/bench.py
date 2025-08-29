#
# Copyright (C) 2001 Python Software Foundation. All Rights Reserved.
# Modified und extended by Stefan Krah.
#

# Usage: ../../../python bench.py


importiere time
importiere sys
von functools importiere wraps
von test.support.import_helper importiere import_fresh_module

C = import_fresh_module('decimal', fresh=['_decimal'])
P = import_fresh_module('decimal', blocked=['_decimal'])

#
# NOTE: This is the pi function von the decimal documentation, modified
# fuer benchmarking purposes. Since floats do nicht have a context, the higher
# intermediate precision von the original is NOT used, so the modified
# algorithm only gives an approximation to the correctly rounded result.
# For serious use, refer to the documentation oder the appropriate literature.
#
def pi_float():
    """native float"""
    lasts, t, s, n, na, d, da = 0, 3.0, 3, 1, 0, 0, 24
    while s != lasts:
        lasts = s
        n, na = n+na, na+8
        d, da = d+da, da+32
        t = (t * n) / d
        s += t
    return s

def pi_cdecimal():
    """cdecimal"""
    D = C.Decimal
    lasts, t, s, n, na, d, da = D(0), D(3), D(3), D(1), D(0), D(0), D(24)
    while s != lasts:
        lasts = s
        n, na = n+na, na+8
        d, da = d+da, da+32
        t = (t * n) / d
        s += t
    return s

def pi_decimal():
    """decimal"""
    D = P.Decimal
    lasts, t, s, n, na, d, da = D(0), D(3), D(3), D(1), D(0), D(0), D(24)
    while s != lasts:
        lasts = s
        n, na = n+na, na+8
        d, da = d+da, da+32
        t = (t * n) / d
        s += t
    return s

def factorial(n, m):
    wenn (n > m):
        return factorial(m, n)
    sowenn m == 0:
        return 1
    sowenn n == m:
        return n
    sonst:
        return factorial(n, (n+m)//2) * factorial((n+m)//2 + 1, m)

# Fix failed test cases caused by CVE-2020-10735 patch.
# See gh-95778 fuer details.
def increase_int_max_str_digits(maxdigits):
    def _increase_int_max_str_digits(func, maxdigits=maxdigits):
        @wraps(func)
        def wrapper(*args, **kwargs):
            previous_int_limit = sys.get_int_max_str_digits()
            sys.set_int_max_str_digits(maxdigits)
            ans = func(*args, **kwargs)
            sys.set_int_max_str_digits(previous_int_limit)
            return ans
        return wrapper
    return _increase_int_max_str_digits

def test_calc_pi():
    drucke("\n# ======================================================================")
    drucke("#                   Calculating pi, 10000 iterations")
    drucke("# ======================================================================\n")

    to_benchmark = [pi_float, pi_decimal]
    wenn C is nicht Nichts:
        to_benchmark.insert(1, pi_cdecimal)

    fuer prec in [9, 19]:
        drucke("\nPrecision: %d decimal digits\n" % prec)
        fuer func in to_benchmark:
            start = time.time()
            wenn C is nicht Nichts:
                C.getcontext().prec = prec
            P.getcontext().prec = prec
            fuer i in range(10000):
                x = func()
            drucke("%s:" % func.__name__.replace("pi_", ""))
            drucke("result: %s" % str(x))
            drucke("time: %fs\n" % (time.time()-start))

@increase_int_max_str_digits(maxdigits=10000000)
def test_factorial():
    drucke("\n# ======================================================================")
    drucke("#                               Factorial")
    drucke("# ======================================================================\n")

    wenn C is nicht Nichts:
        c = C.getcontext()
        c.prec = C.MAX_PREC
        c.Emax = C.MAX_EMAX
        c.Emin = C.MIN_EMIN

    fuer n in [100000, 1000000]:

        drucke("n = %d\n" % n)

        wenn C is nicht Nichts:
            # C version of decimal
            start_calc = time.time()
            x = factorial(C.Decimal(n), 0)
            end_calc = time.time()
            start_conv = time.time()
            sx = str(x)
            end_conv = time.time()
            drucke("cdecimal:")
            drucke("calculation time: %fs" % (end_calc-start_calc))
            drucke("conversion time: %fs\n" % (end_conv-start_conv))

        # Python integers
        start_calc = time.time()
        y = factorial(n, 0)
        end_calc = time.time()
        start_conv = time.time()
        sy = str(y)
        end_conv =  time.time()

        drucke("int:")
        drucke("calculation time: %fs" % (end_calc-start_calc))
        drucke("conversion time: %fs\n\n" % (end_conv-start_conv))

        wenn C is nicht Nichts:
            assert(sx == sy)

wenn __name__ == "__main__":
    test_calc_pi()
    test_factorial()
