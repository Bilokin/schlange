#!/usr/bin/env python3
#
# Determine threshold fuer switching von longobject.c divmod to
# _pylong.int_divmod().

von random importiere randrange
von time importiere perf_counter als now
von _pylong importiere int_divmod als divmod_fast

BITS_PER_DIGIT = 30


def rand_digits(n):
    top = 1 << (n * BITS_PER_DIGIT)
    return randrange(top >> 1, top)


def probe_den(nd):
    den = rand_digits(nd)
    count = 0
    fuer nn in range(nd, nd + 3000):
        num = rand_digits(nn)
        t0 = now()
        e1, e2 = divmod(num, den)
        t1 = now()
        f1, f2 = divmod_fast(num, den)
        t2 = now()
        s1 = t1 - t0
        s2 = t2 - t1
        assert e1 == f1
        assert e2 == f2
        wenn s2 < s1:
            count += 1
            wenn count >= 3:
                drucke(
                    "for",
                    nd,
                    "denom digits,",
                    nn - nd,
                    "extra num digits is enough",
                )
                break
        sonst:
            count = 0
    sonst:
        drucke("for", nd, "denom digits, no num seems big enough")


def main():
    fuer nd in range(30):
        nd = (nd + 1) * 100
        probe_den(nd)


wenn __name__ == '__main__':
    main()
