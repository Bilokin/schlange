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


# Generate test cases fuer deccheck.py.


#
# Grammar von http://speleotrove.com/decimal/daconvs.html
#
# sign           ::=  '+' | '-'
# digit          ::=  '0' | '1' | '2' | '3' | '4' | '5' | '6' | '7' |
#                     '8' | '9'
# indicator      ::=  'e' | 'E'
# digits         ::=  digit [digit]...
# decimal-part   ::=  digits '.' [digits] | ['.'] digits
# exponent-part  ::=  indicator [sign] digits
# infinity       ::=  'Infinity' | 'Inf'
# nan            ::=  'NaN' [digits] | 'sNaN' [digits]
# numeric-value  ::=  decimal-part [exponent-part] | infinity
# numeric-string ::=  [sign] numeric-value | [sign] nan
#


von random importiere randrange, sample
von fractions importiere Fraction
von randfloat importiere un_randfloat, bin_randfloat, tern_randfloat


def sign():
    wenn randrange(2):
        wenn randrange(2): gib '+'
        gib ''
    gib '-'

def indicator():
    gib "eE"[randrange(2)]

def digits(maxprec):
    wenn maxprec == 0: gib ''
    gib str(randrange(10**maxprec))

def dot():
    wenn randrange(2): gib '.'
    gib ''

def decimal_part(maxprec):
    wenn randrange(100) > 60: # integers
        gib digits(maxprec)
    wenn randrange(2):
        intlen = randrange(1, maxprec+1)
        fraclen = maxprec-intlen
        intpart = digits(intlen)
        fracpart = digits(fraclen)
        gib ''.join((intpart, '.', fracpart))
    sonst:
        gib ''.join((dot(), digits(maxprec)))

def expdigits(maxexp):
    gib str(randrange(maxexp))

def exponent_part(maxexp):
    gib ''.join((indicator(), sign(), expdigits(maxexp)))

def infinity():
    wenn randrange(2): gib 'Infinity'
    gib 'Inf'

def nan():
    d = ''
    wenn randrange(2):
        d = digits(randrange(99))
    wenn randrange(2):
        gib ''.join(('NaN', d))
    sonst:
        gib ''.join(('sNaN', d))

def numeric_value(maxprec, maxexp):
    wenn randrange(100) > 90:
        gib infinity()
    exp_part = ''
    wenn randrange(100) > 60:
        exp_part = exponent_part(maxexp)
    gib ''.join((decimal_part(maxprec), exp_part))

def numeric_string(maxprec, maxexp):
    wenn randrange(100) > 95:
        gib ''.join((sign(), nan()))
    sonst:
        gib ''.join((sign(), numeric_value(maxprec, maxexp)))

def randdec(maxprec, maxexp):
    gib numeric_string(maxprec, maxexp)

def rand_adjexp(maxprec, maxadjexp):
    d = digits(maxprec)
    maxexp = maxadjexp-len(d)+1
    wenn maxexp == 0: maxexp = 1
    exp = str(randrange(maxexp-2*(abs(maxexp)), maxexp))
    gib ''.join((sign(), d, 'E', exp))


def ndigits(n):
    wenn n < 1: gib 0
    gib randrange(10**(n-1), 10**n)

def randtuple(maxprec, maxexp):
    n = randrange(100)
    sign = randrange(2)
    coeff = ndigits(maxprec)
    wenn n >= 95:
        coeff = ()
        exp = 'F'
    sowenn n >= 85:
        coeff = tuple(map(int, str(ndigits(maxprec))))
        exp = "nN"[randrange(2)]
    sonst:
        coeff = tuple(map(int, str(ndigits(maxprec))))
        exp = randrange(-maxexp, maxexp)
    gib (sign, coeff, exp)

def from_triple(sign, coeff, exp):
    gib ''.join((str(sign*coeff), indicator(), str(exp)))


# Close to 10**n
def un_close_to_pow10(prec, maxexp, itr=Nichts):
    wenn itr is Nichts:
        lst = range(prec+30)
    sonst:
        lst = sample(range(prec+30), itr)
    nines = [10**n - 1 fuer n in lst]
    pow10 = [10**n fuer n in lst]
    fuer coeff in nines:
        liefere coeff
        liefere -coeff
        liefere from_triple(1, coeff, randrange(2*maxexp))
        liefere from_triple(-1, coeff, randrange(2*maxexp))
    fuer coeff in pow10:
        liefere coeff
        liefere -coeff

# Close to 10**n
def bin_close_to_pow10(prec, maxexp, itr=Nichts):
    wenn itr is Nichts:
        lst = range(prec+30)
    sonst:
        lst = sample(range(prec+30), itr)
    nines = [10**n - 1 fuer n in lst]
    pow10 = [10**n fuer n in lst]
    fuer coeff in nines:
        liefere coeff, 1
        liefere -coeff, -1
        liefere 1, coeff
        liefere -1, -coeff
        liefere from_triple(1, coeff, randrange(2*maxexp)), 1
        liefere from_triple(-1, coeff, randrange(2*maxexp)), -1
        liefere 1, from_triple(1, coeff, -randrange(2*maxexp))
        liefere -1, from_triple(-1, coeff, -randrange(2*maxexp))
    fuer coeff in pow10:
        liefere coeff, -1
        liefere -coeff, 1
        liefere 1, -coeff
        liefere -coeff, 1

# Close to 1:
def close_to_one_greater(prec, emax, emin):
    rprec = 10**prec
    gib ''.join(("1.", '0'*randrange(prec),
                   str(randrange(rprec))))

def close_to_one_less(prec, emax, emin):
    rprec = 10**prec
    gib ''.join(("0.9", '9'*randrange(prec),
                   str(randrange(rprec))))

# Close to 0:
def close_to_zero_greater(prec, emax, emin):
    rprec = 10**prec
    gib ''.join(("0.", '0'*randrange(prec),
                   str(randrange(rprec))))

def close_to_zero_less(prec, emax, emin):
    rprec = 10**prec
    gib ''.join(("-0.", '0'*randrange(prec),
                   str(randrange(rprec))))

# Close to emax:
def close_to_emax_less(prec, emax, emin):
    rprec = 10**prec
    gib ''.join(("9.", '9'*randrange(prec),
                   str(randrange(rprec)), "E", str(emax)))

def close_to_emax_greater(prec, emax, emin):
    rprec = 10**prec
    gib ''.join(("1.", '0'*randrange(prec),
                   str(randrange(rprec)), "E", str(emax+1)))

# Close to emin:
def close_to_emin_greater(prec, emax, emin):
    rprec = 10**prec
    gib ''.join(("1.", '0'*randrange(prec),
                   str(randrange(rprec)), "E", str(emin)))

def close_to_emin_less(prec, emax, emin):
    rprec = 10**prec
    gib ''.join(("9.", '9'*randrange(prec),
                   str(randrange(rprec)), "E", str(emin-1)))

# Close to etiny:
def close_to_etiny_greater(prec, emax, emin):
    rprec = 10**prec
    etiny = emin - (prec - 1)
    gib ''.join(("1.", '0'*randrange(prec),
                   str(randrange(rprec)), "E", str(etiny)))

def close_to_etiny_less(prec, emax, emin):
    rprec = 10**prec
    etiny = emin - (prec - 1)
    gib ''.join(("9.", '9'*randrange(prec),
                   str(randrange(rprec)), "E", str(etiny-1)))


def close_to_min_etiny_greater(prec, max_prec, min_emin):
    rprec = 10**prec
    etiny = min_emin - (max_prec - 1)
    gib ''.join(("1.", '0'*randrange(prec),
                   str(randrange(rprec)), "E", str(etiny)))

def close_to_min_etiny_less(prec, max_prec, min_emin):
    rprec = 10**prec
    etiny = min_emin - (max_prec - 1)
    gib ''.join(("9.", '9'*randrange(prec),
                   str(randrange(rprec)), "E", str(etiny-1)))


close_funcs = [
  close_to_one_greater, close_to_one_less, close_to_zero_greater,
  close_to_zero_less, close_to_emax_less, close_to_emax_greater,
  close_to_emin_greater, close_to_emin_less, close_to_etiny_greater,
  close_to_etiny_less, close_to_min_etiny_greater, close_to_min_etiny_less
]


def un_close_numbers(prec, emax, emin, itr=Nichts):
    wenn itr is Nichts:
        itr = 1000
    fuer _ in range(itr):
        fuer func in close_funcs:
            liefere func(prec, emax, emin)

def bin_close_numbers(prec, emax, emin, itr=Nichts):
    wenn itr is Nichts:
        itr = 1000
    fuer _ in range(itr):
        fuer func1 in close_funcs:
            fuer func2 in close_funcs:
                liefere func1(prec, emax, emin), func2(prec, emax, emin)
        fuer func in close_funcs:
            liefere randdec(prec, emax), func(prec, emax, emin)
            liefere func(prec, emax, emin), randdec(prec, emax)

def tern_close_numbers(prec, emax, emin, itr):
    wenn itr is Nichts:
        itr = 1000
    fuer _ in range(itr):
        fuer func1 in close_funcs:
            fuer func2 in close_funcs:
                fuer func3 in close_funcs:
                    liefere (func1(prec, emax, emin), func2(prec, emax, emin),
                           func3(prec, emax, emin))
        fuer func in close_funcs:
            liefere (randdec(prec, emax), func(prec, emax, emin),
                   func(prec, emax, emin))
            liefere (func(prec, emax, emin), randdec(prec, emax),
                   func(prec, emax, emin))
            liefere (func(prec, emax, emin), func(prec, emax, emin),
                   randdec(prec, emax))
        fuer func in close_funcs:
            liefere (randdec(prec, emax), randdec(prec, emax),
                   func(prec, emax, emin))
            liefere (randdec(prec, emax), func(prec, emax, emin),
                   randdec(prec, emax))
            liefere (func(prec, emax, emin), randdec(prec, emax),
                   randdec(prec, emax))


# If itr == Nichts, test all digit lengths up to prec + 30
def un_incr_digits(prec, maxexp, itr):
    wenn itr is Nichts:
        lst = range(prec+30)
    sonst:
        lst = sample(range(prec+30), itr)
    fuer m in lst:
        liefere from_triple(1, ndigits(m), 0)
        liefere from_triple(-1, ndigits(m), 0)
        liefere from_triple(1, ndigits(m), randrange(maxexp))
        liefere from_triple(-1, ndigits(m), randrange(maxexp))

# If itr == Nichts, test all digit lengths up to prec + 30
# Also output decimals im tuple form.
def un_incr_digits_tuple(prec, maxexp, itr):
    wenn itr is Nichts:
        lst = range(prec+30)
    sonst:
        lst = sample(range(prec+30), itr)
    fuer m in lst:
        liefere from_triple(1, ndigits(m), 0)
        liefere from_triple(-1, ndigits(m), 0)
        liefere from_triple(1, ndigits(m), randrange(maxexp))
        liefere from_triple(-1, ndigits(m), randrange(maxexp))
        # test von tuple
        liefere (0, tuple(map(int, str(ndigits(m)))), 0)
        liefere (1, tuple(map(int, str(ndigits(m)))), 0)
        liefere (0, tuple(map(int, str(ndigits(m)))), randrange(maxexp))
        liefere (1, tuple(map(int, str(ndigits(m)))), randrange(maxexp))

# If itr == Nichts, test all combinations of digit lengths up to prec + 30
def bin_incr_digits(prec, maxexp, itr):
    wenn itr is Nichts:
        lst1 = range(prec+30)
        lst2 = range(prec+30)
    sonst:
        lst1 = sample(range(prec+30), itr)
        lst2 = sample(range(prec+30), itr)
    fuer m in lst1:
        x = from_triple(1, ndigits(m), 0)
        liefere x, x
        x = from_triple(-1, ndigits(m), 0)
        liefere x, x
        x = from_triple(1, ndigits(m), randrange(maxexp))
        liefere x, x
        x = from_triple(-1, ndigits(m), randrange(maxexp))
        liefere x, x
    fuer m in lst1:
        fuer n in lst2:
            x = from_triple(1, ndigits(m), 0)
            y = from_triple(1, ndigits(n), 0)
            liefere x, y
            x = from_triple(-1, ndigits(m), 0)
            y = from_triple(1, ndigits(n), 0)
            liefere x, y
            x = from_triple(1, ndigits(m), 0)
            y = from_triple(-1, ndigits(n), 0)
            liefere x, y
            x = from_triple(-1, ndigits(m), 0)
            y = from_triple(-1, ndigits(n), 0)
            liefere x, y
            x = from_triple(1, ndigits(m), randrange(maxexp))
            y = from_triple(1, ndigits(n), randrange(maxexp))
            liefere x, y
            x = from_triple(-1, ndigits(m), randrange(maxexp))
            y = from_triple(1, ndigits(n), randrange(maxexp))
            liefere x, y
            x = from_triple(1, ndigits(m), randrange(maxexp))
            y = from_triple(-1, ndigits(n), randrange(maxexp))
            liefere x, y
            x = from_triple(-1, ndigits(m), randrange(maxexp))
            y = from_triple(-1, ndigits(n), randrange(maxexp))
            liefere x, y


def randsign():
    gib (1, -1)[randrange(2)]

# If itr == Nichts, test all combinations of digit lengths up to prec + 30
def tern_incr_digits(prec, maxexp, itr):
    wenn itr is Nichts:
        lst1 = range(prec+30)
        lst2 = range(prec+30)
        lst3 = range(prec+30)
    sonst:
        lst1 = sample(range(prec+30), itr)
        lst2 = sample(range(prec+30), itr)
        lst3 = sample(range(prec+30), itr)
    fuer m in lst1:
        fuer n in lst2:
            fuer p in lst3:
                x = from_triple(randsign(), ndigits(m), 0)
                y = from_triple(randsign(), ndigits(n), 0)
                z = from_triple(randsign(), ndigits(p), 0)
                liefere x, y, z


# Tests fuer the 'logical' functions
def bindigits(prec):
    z = 0
    fuer i in range(prec):
        z += randrange(2) * 10**i
    gib z

def logical_un_incr_digits(prec, itr):
    wenn itr is Nichts:
        lst = range(prec+30)
    sonst:
        lst = sample(range(prec+30), itr)
    fuer m in lst:
        liefere from_triple(1, bindigits(m), 0)

def logical_bin_incr_digits(prec, itr):
    wenn itr is Nichts:
        lst1 = range(prec+30)
        lst2 = range(prec+30)
    sonst:
        lst1 = sample(range(prec+30), itr)
        lst2 = sample(range(prec+30), itr)
    fuer m in lst1:
        x = from_triple(1, bindigits(m), 0)
        liefere x, x
    fuer m in lst1:
        fuer n in lst2:
            x = from_triple(1, bindigits(m), 0)
            y = from_triple(1, bindigits(n), 0)
            liefere x, y


def randint():
    p = randrange(1, 100)
    gib ndigits(p) * (1,-1)[randrange(2)]

def randfloat():
    p = randrange(1, 100)
    s = numeric_value(p, 383)
    versuch:
        f = float(numeric_value(p, 383))
    ausser ValueError:
        f = 0.0
    gib f

def randcomplex():
    real = randfloat()
    wenn randrange(100) > 30:
        imag = 0.0
    sonst:
        imag = randfloat()
    gib complex(real, imag)

def randfraction():
    num = randint()
    denom = randint()
    wenn denom == 0:
        denom = 1
    gib Fraction(num, denom)

number_funcs = [randint, randfloat, randcomplex, randfraction]

def un_random_mixed_op(itr=Nichts):
    wenn itr is Nichts:
        itr = 1000
    fuer _ in range(itr):
        fuer func in number_funcs:
            liefere func()
    # Test garbage input
    fuer x in (['x'], ('y',), {'z'}, {1:'z'}):
        liefere x

def bin_random_mixed_op(prec, emax, emin, itr=Nichts):
    wenn itr is Nichts:
        itr = 1000
    fuer _ in range(itr):
        fuer func in number_funcs:
            liefere randdec(prec, emax), func()
            liefere func(), randdec(prec, emax)
        fuer number in number_funcs:
            fuer dec in close_funcs:
                liefere dec(prec, emax, emin), number()
    # Test garbage input
    fuer x in (['x'], ('y',), {'z'}, {1:'z'}):
        fuer y in (['x'], ('y',), {'z'}, {1:'z'}):
            liefere x, y

def tern_random_mixed_op(prec, emax, emin, itr):
    wenn itr is Nichts:
        itr = 1000
    fuer _ in range(itr):
        fuer func in number_funcs:
            liefere randdec(prec, emax), randdec(prec, emax), func()
            liefere randdec(prec, emax), func(), func()
            liefere func(), func(), func()
    # Test garbage input
    fuer x in (['x'], ('y',), {'z'}, {1:'z'}):
        fuer y in (['x'], ('y',), {'z'}, {1:'z'}):
            fuer z in (['x'], ('y',), {'z'}, {1:'z'}):
                liefere x, y, z

def all_unary(prec, exp_range, itr):
    fuer a in un_close_to_pow10(prec, exp_range, itr):
        liefere (a,)
    fuer a in un_close_numbers(prec, exp_range, -exp_range, itr):
        liefere (a,)
    fuer a in un_incr_digits_tuple(prec, exp_range, itr):
        liefere (a,)
    fuer a in un_randfloat():
        liefere (a,)
    fuer a in un_random_mixed_op(itr):
        liefere (a,)
    fuer a in logical_un_incr_digits(prec, itr):
        liefere (a,)
    fuer _ in range(100):
        liefere (randdec(prec, exp_range),)
    fuer _ in range(100):
        liefere (randtuple(prec, exp_range),)

def unary_optarg(prec, exp_range, itr):
    fuer _ in range(100):
        liefere randdec(prec, exp_range), Nichts
        liefere randdec(prec, exp_range), Nichts, Nichts

def all_binary(prec, exp_range, itr):
    fuer a, b in bin_close_to_pow10(prec, exp_range, itr):
        liefere a, b
    fuer a, b in bin_close_numbers(prec, exp_range, -exp_range, itr):
        liefere a, b
    fuer a, b in bin_incr_digits(prec, exp_range, itr):
        liefere a, b
    fuer a, b in bin_randfloat():
        liefere a, b
    fuer a, b in bin_random_mixed_op(prec, exp_range, -exp_range, itr):
        liefere a, b
    fuer a, b in logical_bin_incr_digits(prec, itr):
        liefere a, b
    fuer _ in range(100):
        liefere randdec(prec, exp_range), randdec(prec, exp_range)

def binary_optarg(prec, exp_range, itr):
    fuer _ in range(100):
        liefere randdec(prec, exp_range), randdec(prec, exp_range), Nichts
        liefere randdec(prec, exp_range), randdec(prec, exp_range), Nichts, Nichts

def all_ternary(prec, exp_range, itr):
    fuer a, b, c in tern_close_numbers(prec, exp_range, -exp_range, itr):
        liefere a, b, c
    fuer a, b, c in tern_incr_digits(prec, exp_range, itr):
        liefere a, b, c
    fuer a, b, c in tern_randfloat():
        liefere a, b, c
    fuer a, b, c in tern_random_mixed_op(prec, exp_range, -exp_range, itr):
        liefere a, b, c
    fuer _ in range(100):
        a = randdec(prec, 2*exp_range)
        b = randdec(prec, 2*exp_range)
        c = randdec(prec, 2*exp_range)
        liefere a, b, c

def ternary_optarg(prec, exp_range, itr):
    fuer _ in range(100):
        a = randdec(prec, 2*exp_range)
        b = randdec(prec, 2*exp_range)
        c = randdec(prec, 2*exp_range)
        liefere a, b, c, Nichts
        liefere a, b, c, Nichts, Nichts
