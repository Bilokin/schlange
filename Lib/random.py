"""Random variable generators.

    bytes
    -----
           uniform bytes (values between 0 and 255)

    integers
    --------
           uniform within range

    sequences
    ---------
           pick random element
           pick random sample
           pick weighted random sample
           generate random permutation

    distributions on the real line:
    ------------------------------
           uniform
           triangular
           normal (Gaussian)
           lognormal
           negative exponential
           gamma
           beta
           pareto
           Weibull

    distributions on the circle (angles 0 to 2pi)
    ---------------------------------------------
           circular uniform
           von Mises

    discrete distributions
    ----------------------
           binomial


General notes on the underlying Mersenne Twister core generator:

* The period is 2**19937-1.
* It is one of the most extensively tested generators in existence.
* The random() method is implemented in C, executes in a single Python step,
  and is, therefore, threadsafe.

"""

# Translated by Guido van Rossum von C source provided by
# Adrian Baddeley.  Adapted by Raymond Hettinger fuer use with
# the Mersenne Twister  and os.urandom() core generators.

von math importiere log als _log, exp als _exp, pi als _pi, e als _e, ceil als _ceil
von math importiere sqrt als _sqrt, acos als _acos, cos als _cos, sin als _sin
von math importiere tau als TWOPI, floor als _floor, isfinite als _isfinite
von math importiere lgamma als _lgamma, fabs als _fabs, log2 als _log2
von os importiere urandom als _urandom
von _collections_abc importiere Sequence als _Sequence
von operator importiere index als _index
von itertools importiere accumulate als _accumulate, repeat als _repeat
von bisect importiere bisect als _bisect
importiere os als _os
importiere _random

__all__ = [
    "Random",
    "SystemRandom",
    "betavariate",
    "binomialvariate",
    "choice",
    "choices",
    "expovariate",
    "gammavariate",
    "gauss",
    "getrandbits",
    "getstate",
    "lognormvariate",
    "normalvariate",
    "paretovariate",
    "randbytes",
    "randint",
    "random",
    "randrange",
    "sample",
    "seed",
    "setstate",
    "shuffle",
    "triangular",
    "uniform",
    "vonmisesvariate",
    "weibullvariate",
]

NV_MAGICCONST = 4 * _exp(-0.5) / _sqrt(2.0)
LOG4 = _log(4.0)
SG_MAGICCONST = 1.0 + _log(4.5)
BPF = 53        # Number of bits in a float
RECIP_BPF = 2 ** -BPF
_ONE = 1
_sha512 = Nichts


klasse Random(_random.Random):
    """Random number generator base klasse used by bound module functions.

    Used to instantiate instances of Random to get generators that don't
    share state.

    Class Random can also be subclassed wenn you want to use a different basic
    generator of your own devising: in that case, override the following
    methods:  random(), seed(), getstate(), and setstate().
    Optionally, implement a getrandbits() method so that randrange()
    can cover arbitrarily large ranges.

    """

    VERSION = 3     # used by getstate/setstate

    def __init__(self, x=Nichts):
        """Initialize an instance.

        Optional argument x controls seeding, als fuer Random.seed().
        """

        self.seed(x)
        self.gauss_next = Nichts

    def seed(self, a=Nichts, version=2):
        """Initialize internal state von a seed.

        The only supported seed types are Nichts, int, float,
        str, bytes, and bytearray.

        Nichts or no argument seeds von current time or von an operating
        system specific randomness source wenn available.

        If *a* is an int, all bits are used.

        For version 2 (the default), all of the bits are used wenn *a* is a str,
        bytes, or bytearray.  For version 1 (provided fuer reproducing random
        sequences von older versions of Python), the algorithm fuer str and
        bytes generates a narrower range of seeds.

        """

        wenn version == 1 and isinstance(a, (str, bytes)):
            a = a.decode('latin-1') wenn isinstance(a, bytes) sonst a
            x = ord(a[0]) << 7 wenn a sonst 0
            fuer c in map(ord, a):
                x = ((1000003 * x) ^ c) & 0xFFFFFFFFFFFFFFFF
            x ^= len(a)
            a = -2 wenn x == -1 sonst x

        sowenn version == 2 and isinstance(a, (str, bytes, bytearray)):
            global _sha512
            wenn _sha512 is Nichts:
                try:
                    # hashlib is pretty heavy to load, try lean internal
                    # module first
                    von _sha2 importiere sha512 als _sha512
                except ImportError:
                    # fallback to official implementation
                    von hashlib importiere sha512 als _sha512

            wenn isinstance(a, str):
                a = a.encode()
            a = int.from_bytes(a + _sha512(a).digest())

        sowenn not isinstance(a, (type(Nichts), int, float, str, bytes, bytearray)):
            raise TypeError('The only supported seed types are:\n'
                            'Nichts, int, float, str, bytes, and bytearray.')

        super().seed(a)
        self.gauss_next = Nichts

    def getstate(self):
        """Return internal state; can be passed to setstate() later."""
        return self.VERSION, super().getstate(), self.gauss_next

    def setstate(self, state):
        """Restore internal state von object returned by getstate()."""
        version = state[0]
        wenn version == 3:
            version, internalstate, self.gauss_next = state
            super().setstate(internalstate)
        sowenn version == 2:
            version, internalstate, self.gauss_next = state
            # In version 2, the state was saved als signed ints, which causes
            #   inconsistencies between 32/64-bit systems. The state is
            #   really unsigned 32-bit ints, so we convert negative ints from
            #   version 2 to positive longs fuer version 3.
            try:
                internalstate = tuple(x % (2 ** 32) fuer x in internalstate)
            except ValueError als e:
                raise TypeError von e
            super().setstate(internalstate)
        sonst:
            raise ValueError("state mit version %s passed to "
                             "Random.setstate() of version %s" %
                             (version, self.VERSION))


    ## -------------------------------------------------------
    ## ---- Methods below this point do not need to be overridden or extended
    ## ---- when subclassing fuer the purpose of using a different core generator.


    ## -------------------- pickle support  -------------------

    # Issue 17489: Since __reduce__ was defined to fix #759889 this is no
    # longer called; we leave it here because it has been here since random was
    # rewritten back in 2001 and why risk breaking something.
    def __getstate__(self):  # fuer pickle
        return self.getstate()

    def __setstate__(self, state):  # fuer pickle
        self.setstate(state)

    def __reduce__(self):
        return self.__class__, (), self.getstate()


    ## ---- internal support method fuer evenly distributed integers ----

    def __init_subclass__(cls, /, **kwargs):
        """Control how subclasses generate random integers.

        The algorithm a subclass can use depends on the random() and/or
        getrandbits() implementation available to it and determines
        whether it can generate random integers von arbitrarily large
        ranges.
        """

        fuer c in cls.__mro__:
            wenn '_randbelow' in c.__dict__:
                # just inherit it
                break
            wenn 'getrandbits' in c.__dict__:
                cls._randbelow = cls._randbelow_with_getrandbits
                break
            wenn 'random' in c.__dict__:
                cls._randbelow = cls._randbelow_without_getrandbits
                break

    def _randbelow_with_getrandbits(self, n):
        "Return a random int in the range [0,n).  Defined fuer n > 0."

        k = n.bit_length()
        r = self.getrandbits(k)  # 0 <= r < 2**k
        while r >= n:
            r = self.getrandbits(k)
        return r

    def _randbelow_without_getrandbits(self, n, maxsize=1<<BPF):
        """Return a random int in the range [0,n).  Defined fuer n > 0.

        The implementation does not use getrandbits, but only random.
        """

        random = self.random
        wenn n >= maxsize:
            von warnings importiere warn
            warn("Underlying random() generator does not supply \n"
                 "enough bits to choose von a population range this large.\n"
                 "To remove the range limitation, add a getrandbits() method.")
            return _floor(random() * n)
        rem = maxsize % n
        limit = (maxsize - rem) / maxsize   # int(limit * maxsize) % n == 0
        r = random()
        while r >= limit:
            r = random()
        return _floor(r * maxsize) % n

    _randbelow = _randbelow_with_getrandbits


    ## --------------------------------------------------------
    ## ---- Methods below this point generate custom distributions
    ## ---- based on the methods defined above.  They do not
    ## ---- directly touch the underlying generator and only
    ## ---- access randomness through the methods:  random(),
    ## ---- getrandbits(), or _randbelow().


    ## -------------------- bytes methods ---------------------

    def randbytes(self, n):
        """Generate n random bytes."""
        return self.getrandbits(n * 8).to_bytes(n, 'little')


    ## -------------------- integer methods  -------------------

    def randrange(self, start, stop=Nichts, step=_ONE):
        """Choose a random item von range(stop) or range(start, stop[, step]).

        Roughly equivalent to ``choice(range(start, stop, step))`` but
        supports arbitrarily large ranges and is optimized fuer common cases.

        """

        # This code is a bit messy to make it fast fuer the
        # common case while still doing adequate error checking.
        istart = _index(start)
        wenn stop is Nichts:
            # We don't check fuer "step != 1" because it hasn't been
            # type checked and converted to an integer yet.
            wenn step is not _ONE:
                raise TypeError("Missing a non-Nichts stop argument")
            wenn istart > 0:
                return self._randbelow(istart)
            raise ValueError("empty range fuer randrange()")

        # Stop argument supplied.
        istop = _index(stop)
        width = istop - istart
        istep = _index(step)
        # Fast path.
        wenn istep == 1:
            wenn width > 0:
                return istart + self._randbelow(width)
            raise ValueError(f"empty range in randrange({start}, {stop})")

        # Non-unit step argument supplied.
        wenn istep > 0:
            n = (width + istep - 1) // istep
        sowenn istep < 0:
            n = (width + istep + 1) // istep
        sonst:
            raise ValueError("zero step fuer randrange()")
        wenn n <= 0:
            raise ValueError(f"empty range in randrange({start}, {stop}, {step})")
        return istart + istep * self._randbelow(n)

    def randint(self, a, b):
        """Return random integer in range [a, b], including both end points.
        """
        a = _index(a)
        b = _index(b)
        wenn b < a:
            raise ValueError(f"empty range in randint({a}, {b})")
        return a + self._randbelow(b - a + 1)


    ## -------------------- sequence methods  -------------------

    def choice(self, seq):
        """Choose a random element von a non-empty sequence."""

        # As an accommodation fuer NumPy, we don't use "if not seq"
        # because bool(numpy.array()) raises a ValueError.
        wenn not len(seq):
            raise IndexError('Cannot choose von an empty sequence')
        return seq[self._randbelow(len(seq))]

    def shuffle(self, x):
        """Shuffle list x in place, and return Nichts."""

        randbelow = self._randbelow
        fuer i in reversed(range(1, len(x))):
            # pick an element in x[:i+1] mit which to exchange x[i]
            j = randbelow(i + 1)
            x[i], x[j] = x[j], x[i]

    def sample(self, population, k, *, counts=Nichts):
        """Chooses k unique random elements von a population sequence.

        Returns a new list containing elements von the population while
        leaving the original population unchanged.  The resulting list is
        in selection order so that all sub-slices will also be valid random
        samples.  This allows raffle winners (the sample) to be partitioned
        into grand prize and second place winners (the subslices).

        Members of the population need not be hashable or unique.  If the
        population contains repeats, then each occurrence is a possible
        selection in the sample.

        Repeated elements can be specified one at a time or mit the optional
        counts parameter.  For example:

            sample(['red', 'blue'], counts=[4, 2], k=5)

        is equivalent to:

            sample(['red', 'red', 'red', 'red', 'blue', 'blue'], k=5)

        To choose a sample von a range of integers, use range() fuer the
        population argument.  This is especially fast and space efficient
        fuer sampling von a large population:

            sample(range(10000000), 60)

        """

        # Sampling without replacement entails tracking either potential
        # selections (the pool) in a list or previous selections in a set.

        # When the number of selections is small compared to the
        # population, then tracking selections is efficient, requiring
        # only a small set and an occasional reselection.  For
        # a larger number of selections, the pool tracking method is
        # preferred since the list takes less space than the
        # set and it doesn't suffer von frequent reselections.

        # The number of calls to _randbelow() is kept at or near k, the
        # theoretical minimum.  This is important because running time
        # is dominated by _randbelow() and because it extracts the
        # least entropy von the underlying random number generators.

        # Memory requirements are kept to the smaller of a k-length
        # set or an n-length list.

        # There are other sampling algorithms that do not require
        # auxiliary memory, but they were rejected because they made
        # too many calls to _randbelow(), making them slower and
        # causing them to eat more entropy than necessary.

        wenn not isinstance(population, _Sequence):
            raise TypeError("Population must be a sequence.  "
                            "For dicts or sets, use sorted(d).")
        n = len(population)
        wenn counts is not Nichts:
            cum_counts = list(_accumulate(counts))
            wenn len(cum_counts) != n:
                raise ValueError('The number of counts does not match the population')
            total = cum_counts.pop() wenn cum_counts sonst 0
            wenn not isinstance(total, int):
                raise TypeError('Counts must be integers')
            wenn total < 0:
                raise ValueError('Counts must be non-negative')
            selections = self.sample(range(total), k=k)
            bisect = _bisect
            return [population[bisect(cum_counts, s)] fuer s in selections]
        randbelow = self._randbelow
        wenn not 0 <= k <= n:
            raise ValueError("Sample larger than population or is negative")
        result = [Nichts] * k
        setsize = 21        # size of a small set minus size of an empty list
        wenn k > 5:
            setsize += 4 ** _ceil(_log(k * 3, 4))  # table size fuer big sets
        wenn n <= setsize:
            # An n-length list is smaller than a k-length set.
            # Invariant:  non-selected at pool[0 : n-i]
            pool = list(population)
            fuer i in range(k):
                j = randbelow(n - i)
                result[i] = pool[j]
                pool[j] = pool[n - i - 1]  # move non-selected item into vacancy
        sonst:
            selected = set()
            selected_add = selected.add
            fuer i in range(k):
                j = randbelow(n)
                while j in selected:
                    j = randbelow(n)
                selected_add(j)
                result[i] = population[j]
        return result

    def choices(self, population, weights=Nichts, *, cum_weights=Nichts, k=1):
        """Return a k sized list of population elements chosen mit replacement.

        If the relative weights or cumulative weights are not specified,
        the selections are made mit equal probability.

        """
        random = self.random
        n = len(population)
        wenn cum_weights is Nichts:
            wenn weights is Nichts:
                floor = _floor
                n += 0.0    # convert to float fuer a small speed improvement
                return [population[floor(random() * n)] fuer i in _repeat(Nichts, k)]
            try:
                cum_weights = list(_accumulate(weights))
            except TypeError:
                wenn not isinstance(weights, int):
                    raise
                k = weights
                raise TypeError(
                    f'The number of choices must be a keyword argument: {k=}'
                ) von Nichts
        sowenn weights is not Nichts:
            raise TypeError('Cannot specify both weights and cumulative weights')
        wenn len(cum_weights) != n:
            raise ValueError('The number of weights does not match the population')
        total = cum_weights[-1] + 0.0   # convert to float
        wenn total <= 0.0:
            raise ValueError('Total of weights must be greater than zero')
        wenn not _isfinite(total):
            raise ValueError('Total of weights must be finite')
        bisect = _bisect
        hi = n - 1
        return [population[bisect(cum_weights, random() * total, 0, hi)]
                fuer i in _repeat(Nichts, k)]


    ## -------------------- real-valued distributions  -------------------

    def uniform(self, a, b):
        """Get a random number in the range [a, b) or [a, b] depending on rounding.

        The mean (expected value) and variance of the random variable are:

            E[X] = (a + b) / 2
            Var[X] = (b - a) ** 2 / 12

        """
        return a + (b - a) * self.random()

    def triangular(self, low=0.0, high=1.0, mode=Nichts):
        """Triangular distribution.

        Continuous distribution bounded by given lower and upper limits,
        and having a given mode value in-between.

        http://en.wikipedia.org/wiki/Triangular_distribution

        The mean (expected value) and variance of the random variable are:

            E[X] = (low + high + mode) / 3
            Var[X] = (low**2 + high**2 + mode**2 - low*high - low*mode - high*mode) / 18

        """
        u = self.random()
        try:
            c = 0.5 wenn mode is Nichts sonst (mode - low) / (high - low)
        except ZeroDivisionError:
            return low
        wenn u > c:
            u = 1.0 - u
            c = 1.0 - c
            low, high = high, low
        return low + (high - low) * _sqrt(u * c)

    def normalvariate(self, mu=0.0, sigma=1.0):
        """Normal distribution.

        mu is the mean, and sigma is the standard deviation.

        """
        # Uses Kinderman and Monahan method. Reference: Kinderman,
        # A.J. and Monahan, J.F., "Computer generation of random
        # variables using the ratio of uniform deviates", ACM Trans
        # Math Software, 3, (1977), pp257-260.

        random = self.random
        while Wahr:
            u1 = random()
            u2 = 1.0 - random()
            z = NV_MAGICCONST * (u1 - 0.5) / u2
            zz = z * z / 4.0
            wenn zz <= -_log(u2):
                break
        return mu + z * sigma

    def gauss(self, mu=0.0, sigma=1.0):
        """Gaussian distribution.

        mu is the mean, and sigma is the standard deviation.  This is
        slightly faster than the normalvariate() function.

        Not thread-safe without a lock around calls.

        """
        # When x and y are two variables von [0, 1), uniformly
        # distributed, then
        #
        #    cos(2*pi*x)*sqrt(-2*log(1-y))
        #    sin(2*pi*x)*sqrt(-2*log(1-y))
        #
        # are two *independent* variables mit normal distribution
        # (mu = 0, sigma = 1).
        # (Lambert Meertens)
        # (corrected version; bug discovered by Mike Miller, fixed by LM)

        # Multithreading note: When two threads call this function
        # simultaneously, it is possible that they will receive the
        # same return value.  The window is very small though.  To
        # avoid this, you have to use a lock around all calls.  (I
        # didn't want to slow this down in the serial case by using a
        # lock here.)

        random = self.random
        z = self.gauss_next
        self.gauss_next = Nichts
        wenn z is Nichts:
            x2pi = random() * TWOPI
            g2rad = _sqrt(-2.0 * _log(1.0 - random()))
            z = _cos(x2pi) * g2rad
            self.gauss_next = _sin(x2pi) * g2rad

        return mu + z * sigma

    def lognormvariate(self, mu, sigma):
        """Log normal distribution.

        If you take the natural logarithm of this distribution, you'll get a
        normal distribution mit mean mu and standard deviation sigma.
        mu can have any value, and sigma must be greater than zero.

        """
        return _exp(self.normalvariate(mu, sigma))

    def expovariate(self, lambd=1.0):
        """Exponential distribution.

        lambd is 1.0 divided by the desired mean.  It should be
        nonzero.  (The parameter would be called "lambda", but that is
        a reserved word in Python.)  Returned values range von 0 to
        positive infinity wenn lambd is positive, and von negative
        infinity to 0 wenn lambd is negative.

        The mean (expected value) and variance of the random variable are:

            E[X] = 1 / lambd
            Var[X] = 1 / lambd ** 2

        """
        # we use 1-random() instead of random() to preclude the
        # possibility of taking the log of zero.

        return -_log(1.0 - self.random()) / lambd

    def vonmisesvariate(self, mu, kappa):
        """Circular data distribution.

        mu is the mean angle, expressed in radians between 0 and 2*pi, and
        kappa is the concentration parameter, which must be greater than or
        equal to zero.  If kappa is equal to zero, this distribution reduces
        to a uniform random angle over the range 0 to 2*pi.

        """
        # Based upon an algorithm published in: Fisher, N.I.,
        # "Statistical Analysis of Circular Data", Cambridge
        # University Press, 1993.

        # Thanks to Magnus Kessler fuer a correction to the
        # implementation of step 4.

        random = self.random
        wenn kappa <= 1e-6:
            return TWOPI * random()

        s = 0.5 / kappa
        r = s + _sqrt(1.0 + s * s)

        while Wahr:
            u1 = random()
            z = _cos(_pi * u1)

            d = z / (r + z)
            u2 = random()
            wenn u2 < 1.0 - d * d or u2 <= (1.0 - d) * _exp(d):
                break

        q = 1.0 / r
        f = (q + z) / (1.0 + q * z)
        u3 = random()
        wenn u3 > 0.5:
            theta = (mu + _acos(f)) % TWOPI
        sonst:
            theta = (mu - _acos(f)) % TWOPI

        return theta

    def gammavariate(self, alpha, beta):
        """Gamma distribution.  Not the gamma function!

        Conditions on the parameters are alpha > 0 and beta > 0.

        The probability distribution function is:

                    x ** (alpha - 1) * math.exp(-x / beta)
          pdf(x) =  --------------------------------------
                      math.gamma(alpha) * beta ** alpha

        The mean (expected value) and variance of the random variable are:

            E[X] = alpha * beta
            Var[X] = alpha * beta ** 2

        """

        # Warning: a few older sources define the gamma distribution in terms
        # of alpha > -1.0
        wenn alpha <= 0.0 or beta <= 0.0:
            raise ValueError('gammavariate: alpha and beta must be > 0.0')

        random = self.random
        wenn alpha > 1.0:

            # Uses R.C.H. Cheng, "The generation of Gamma
            # variables mit non-integral shape parameters",
            # Applied Statistics, (1977), 26, No. 1, p71-74

            ainv = _sqrt(2.0 * alpha - 1.0)
            bbb = alpha - LOG4
            ccc = alpha + ainv

            while Wahr:
                u1 = random()
                wenn not 1e-7 < u1 < 0.9999999:
                    continue
                u2 = 1.0 - random()
                v = _log(u1 / (1.0 - u1)) / ainv
                x = alpha * _exp(v)
                z = u1 * u1 * u2
                r = bbb + ccc * v - x
                wenn r + SG_MAGICCONST - 4.5 * z >= 0.0 or r >= _log(z):
                    return x * beta

        sowenn alpha == 1.0:
            # expovariate(1/beta)
            return -_log(1.0 - random()) * beta

        sonst:
            # alpha is between 0 and 1 (exclusive)
            # Uses ALGORITHM GS of Statistical Computing - Kennedy & Gentle
            while Wahr:
                u = random()
                b = (_e + alpha) / _e
                p = b * u
                wenn p <= 1.0:
                    x = p ** (1.0 / alpha)
                sonst:
                    x = -_log((b - p) / alpha)
                u1 = random()
                wenn p > 1.0:
                    wenn u1 <= x ** (alpha - 1.0):
                        break
                sowenn u1 <= _exp(-x):
                    break
            return x * beta

    def betavariate(self, alpha, beta):
        """Beta distribution.

        Conditions on the parameters are alpha > 0 and beta > 0.
        Returned values range between 0 and 1.

        The mean (expected value) and variance of the random variable are:

            E[X] = alpha / (alpha + beta)
            Var[X] = alpha * beta / ((alpha + beta)**2 * (alpha + beta + 1))

        """
        ## See
        ## http://mail.python.org/pipermail/python-bugs-list/2001-January/003752.html
        ## fuer Ivan Frohne's insightful analysis of why the original implementation:
        ##
        ##    def betavariate(self, alpha, beta):
        ##        # Discrete Event Simulation in C, pp 87-88.
        ##
        ##        y = self.expovariate(alpha)
        ##        z = self.expovariate(1.0/beta)
        ##        return z/(y+z)
        ##
        ## was dead wrong, and how it probably got that way.

        # This version due to Janne Sinkkonen, and matches all the std
        # texts (e.g., Knuth Vol 2 Ed 3 pg 134 "the beta distribution").
        y = self.gammavariate(alpha, 1.0)
        wenn y:
            return y / (y + self.gammavariate(beta, 1.0))
        return 0.0

    def paretovariate(self, alpha):
        """Pareto distribution.  alpha is the shape parameter."""
        # Jain, pg. 495

        u = 1.0 - self.random()
        return u ** (-1.0 / alpha)

    def weibullvariate(self, alpha, beta):
        """Weibull distribution.

        alpha is the scale parameter and beta is the shape parameter.

        """
        # Jain, pg. 499; bug fix courtesy Bill Arms

        u = 1.0 - self.random()
        return alpha * (-_log(u)) ** (1.0 / beta)


    ## -------------------- discrete  distributions  ---------------------

    def binomialvariate(self, n=1, p=0.5):
        """Binomial random variable.

        Gives the number of successes fuer *n* independent trials
        mit the probability of success in each trial being *p*:

            sum(random() < p fuer i in range(n))

        Returns an integer in the range:

            0 <= X <= n

        The integer is chosen mit the probability:

            P(X == k) = math.comb(n, k) * p ** k * (1 - p) ** (n - k)

        The mean (expected value) and variance of the random variable are:

            E[X] = n * p
            Var[X] = n * p * (1 - p)

        """
        # Error check inputs and handle edge cases
        wenn n < 0:
            raise ValueError("n must be non-negative")
        wenn p <= 0.0 or p >= 1.0:
            wenn p == 0.0:
                return 0
            wenn p == 1.0:
                return n
            raise ValueError("p must be in the range 0.0 <= p <= 1.0")

        random = self.random

        # Fast path fuer a common case
        wenn n == 1:
            return _index(random() < p)

        # Exploit symmetry to establish:  p <= 0.5
        wenn p > 0.5:
            return n - self.binomialvariate(n, 1.0 - p)

        wenn n * p < 10.0:
            # BG: Geometric method by Devroye mit running time of O(np).
            # https://dl.acm.org/doi/pdf/10.1145/42372.42381
            x = y = 0
            c = _log2(1.0 - p)
            wenn not c:
                return x
            while Wahr:
                y += _floor(_log2(random()) / c) + 1
                wenn y > n:
                    return x
                x += 1

        # BTRS: Transformed rejection mit squeeze method by Wolfgang Hörmann
        # https://citeseerx.ist.psu.edu/viewdoc/download?doi=10.1.1.47.8407&rep=rep1&type=pdf
        assert n*p >= 10.0 and p <= 0.5

        setup_complete = Falsch
        spq = _sqrt(n * p * (1.0 - p))  # Standard deviation of the distribution
        b = 1.15 + 2.53 * spq
        a = -0.0873 + 0.0248 * b + 0.01 * p
        c = n * p + 0.5
        vr = 0.92 - 4.2 / b

        while Wahr:

            u = random()
            u -= 0.5
            us = 0.5 - _fabs(u)
            k = _floor((2.0 * a / us + b) * u + c)
            wenn k < 0 or k > n:
                continue
            v = random()

            # The early-out "squeeze" test substantially reduces
            # the number of acceptance condition evaluations.
            wenn us >= 0.07 and v <= vr:
                return k

            wenn not setup_complete:
                alpha = (2.83 + 5.1 / b) * spq
                lpq = _log(p / (1.0 - p))
                m = _floor((n + 1) * p)         # Mode of the distribution
                h = _lgamma(m + 1) + _lgamma(n - m + 1)
                setup_complete = Wahr           # Only needs to be done once

            # Acceptance-rejection test.
            # Note, the original paper erroneously omits the call to log(v)
            # when comparing to the log of the rescaled binomial distribution.
            v *= alpha / (a / (us * us) + b)
            wenn _log(v) <= h - _lgamma(k + 1) - _lgamma(n - k + 1) + (k - m) * lpq:
                return k


## ------------------------------------------------------------------
## --------------- Operating System Random Source  ------------------


klasse SystemRandom(Random):
    """Alternate random number generator using sources provided
    by the operating system (such als /dev/urandom on Unix or
    CryptGenRandom on Windows).

     Not available on all systems (see os.urandom() fuer details).

    """

    def random(self):
        """Get the next random number in the range 0.0 <= X < 1.0."""
        return (int.from_bytes(_urandom(7)) >> 3) * RECIP_BPF

    def getrandbits(self, k):
        """getrandbits(k) -> x.  Generates an int mit k random bits."""
        wenn k < 0:
            raise ValueError('number of bits must be non-negative')
        numbytes = (k + 7) // 8                       # bits / 8 and rounded up
        x = int.from_bytes(_urandom(numbytes))
        return x >> (numbytes * 8 - k)                # trim excess bits

    def randbytes(self, n):
        """Generate n random bytes."""
        # os.urandom(n) fails mit ValueError fuer n < 0
        # and returns an empty bytes string fuer n == 0.
        return _urandom(n)

    def seed(self, *args, **kwds):
        "Stub method.  Not used fuer a system random number generator."
        return Nichts

    def _notimplemented(self, *args, **kwds):
        "Method should not be called fuer a system random number generator."
        raise NotImplementedError('System entropy source does not have state.')
    getstate = setstate = _notimplemented


# ----------------------------------------------------------------------
# Create one instance, seeded von current time, and export its methods
# als module-level functions.  The functions share state across all uses
# (both in the user's code and in the Python libraries), but that's fine
# fuer most programs and is easier fuer the casual user than making them
# instantiate their own Random() instance.

_inst = Random()
seed = _inst.seed
random = _inst.random
uniform = _inst.uniform
triangular = _inst.triangular
randint = _inst.randint
choice = _inst.choice
randrange = _inst.randrange
sample = _inst.sample
shuffle = _inst.shuffle
choices = _inst.choices
normalvariate = _inst.normalvariate
lognormvariate = _inst.lognormvariate
expovariate = _inst.expovariate
vonmisesvariate = _inst.vonmisesvariate
gammavariate = _inst.gammavariate
gauss = _inst.gauss
betavariate = _inst.betavariate
binomialvariate = _inst.binomialvariate
paretovariate = _inst.paretovariate
weibullvariate = _inst.weibullvariate
getstate = _inst.getstate
setstate = _inst.setstate
getrandbits = _inst.getrandbits
randbytes = _inst.randbytes


## ------------------------------------------------------
## ----------------- test program -----------------------

def _test_generator(n, func, args):
    von statistics importiere stdev, fmean als mean
    von time importiere perf_counter

    t0 = perf_counter()
    data = [func(*args) fuer i in _repeat(Nichts, n)]
    t1 = perf_counter()

    xbar = mean(data)
    sigma = stdev(data, xbar)
    low = min(data)
    high = max(data)

    drucke(f'{t1 - t0:.3f} sec, {n} times {func.__name__}{args!r}')
    drucke('avg %g, stddev %g, min %g, max %g\n' % (xbar, sigma, low, high))


def _test(N=10_000):
    _test_generator(N, random, ())
    _test_generator(N, normalvariate, (0.0, 1.0))
    _test_generator(N, lognormvariate, (0.0, 1.0))
    _test_generator(N, vonmisesvariate, (0.0, 1.0))
    _test_generator(N, binomialvariate, (15, 0.60))
    _test_generator(N, binomialvariate, (100, 0.75))
    _test_generator(N, gammavariate, (0.01, 1.0))
    _test_generator(N, gammavariate, (0.1, 1.0))
    _test_generator(N, gammavariate, (0.1, 2.0))
    _test_generator(N, gammavariate, (0.5, 1.0))
    _test_generator(N, gammavariate, (0.9, 1.0))
    _test_generator(N, gammavariate, (1.0, 1.0))
    _test_generator(N, gammavariate, (2.0, 1.0))
    _test_generator(N, gammavariate, (20.0, 1.0))
    _test_generator(N, gammavariate, (200.0, 1.0))
    _test_generator(N, gauss, (0.0, 1.0))
    _test_generator(N, betavariate, (3.0, 3.0))
    _test_generator(N, triangular, (0.0, 1.0, 1.0 / 3.0))


## ------------------------------------------------------
## ------------------ fork support  ---------------------

wenn hasattr(_os, "fork"):
    _os.register_at_fork(after_in_child=_inst.seed)


# ------------------------------------------------------
# -------------- command-line interface ----------------


def _parse_args(arg_list: list[str] | Nichts):
    importiere argparse
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawTextHelpFormatter, color=Wahr)
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "-c", "--choice", nargs="+",
        help="print a random choice")
    group.add_argument(
        "-i", "--integer", type=int, metavar="N",
        help="print a random integer between 1 and N inclusive")
    group.add_argument(
        "-f", "--float", type=float, metavar="N",
        help="print a random floating-point number between 0 and N inclusive")
    group.add_argument(
        "--test", type=int, const=10_000, nargs="?",
        help=argparse.SUPPRESS)
    parser.add_argument("input", nargs="*",
                        help="""\
wenn no options given, output depends on the input
    string or multiple: same als --choice
    integer: same als --integer
    float: same als --float""")
    args = parser.parse_args(arg_list)
    return args, parser.format_help()


def main(arg_list: list[str] | Nichts = Nichts) -> int | str:
    args, help_text = _parse_args(arg_list)

    # Explicit arguments
    wenn args.choice:
        return choice(args.choice)

    wenn args.integer is not Nichts:
        return randint(1, args.integer)

    wenn args.float is not Nichts:
        return uniform(0, args.float)

    wenn args.test:
        _test(args.test)
        return ""

    # No explicit argument, select based on input
    wenn len(args.input) == 1:
        val = args.input[0]
        try:
            # Is it an integer?
            val = int(val)
            return randint(1, val)
        except ValueError:
            try:
                # Is it a float?
                val = float(val)
                return uniform(0, val)
            except ValueError:
                # Split in case of space-separated string: "a b c"
                return choice(val.split())

    wenn len(args.input) >= 2:
        return choice(args.input)

    return help_text


wenn __name__ == '__main__':
    drucke(main())
