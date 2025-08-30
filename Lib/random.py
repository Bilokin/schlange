"""Random variable generators.

    bytes
    -----
           uniform bytes (values between 0 und 255)

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

* The period ist 2**19937-1.
* It ist one of the most extensively tested generators in existence.
* The random() method ist implemented in C, executes in a single Python step,
  und is, therefore, threadsafe.

"""

# Translated by Guido van Rossum von C source provided by
# Adrian Baddeley.  Adapted by Raymond Hettinger fuer use with
# the Mersenne Twister  und os.urandom() core generators.

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
    methods:  random(), seed(), getstate(), und setstate().
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
        str, bytes, und bytearray.

        Nichts oder no argument seeds von current time oder von an operating
        system specific randomness source wenn available.

        If *a* ist an int, all bits are used.

        For version 2 (the default), all of the bits are used wenn *a* ist a str,
        bytes, oder bytearray.  For version 1 (provided fuer reproducing random
        sequences von older versions of Python), the algorithm fuer str und
        bytes generates a narrower range of seeds.

        """

        wenn version == 1 und isinstance(a, (str, bytes)):
            a = a.decode('latin-1') wenn isinstance(a, bytes) sonst a
            x = ord(a[0]) << 7 wenn a sonst 0
            fuer c in map(ord, a):
                x = ((1000003 * x) ^ c) & 0xFFFFFFFFFFFFFFFF
            x ^= len(a)
            a = -2 wenn x == -1 sonst x

        sowenn version == 2 und isinstance(a, (str, bytes, bytearray)):
            global _sha512
            wenn _sha512 ist Nichts:
                versuch:
                    # hashlib ist pretty heavy to load, try lean internal
                    # module first
                    von _sha2 importiere sha512 als _sha512
                ausser ImportError:
                    # fallback to official implementation
                    von hashlib importiere sha512 als _sha512

            wenn isinstance(a, str):
                a = a.encode()
            a = int.from_bytes(a + _sha512(a).digest())

        sowenn nicht isinstance(a, (type(Nichts), int, float, str, bytes, bytearray)):
            wirf TypeError('The only supported seed types are:\n'
                            'Nichts, int, float, str, bytes, und bytearray.')

        super().seed(a)
        self.gauss_next = Nichts

    def getstate(self):
        """Return internal state; can be passed to setstate() later."""
        gib self.VERSION, super().getstate(), self.gauss_next

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
            versuch:
                internalstate = tuple(x % (2 ** 32) fuer x in internalstate)
            ausser ValueError als e:
                wirf TypeError von e
            super().setstate(internalstate)
        sonst:
            wirf ValueError("state mit version %s passed to "
                             "Random.setstate() of version %s" %
                             (version, self.VERSION))


    ## -------------------------------------------------------
    ## ---- Methods below this point do nicht need to be overridden oder extended
    ## ---- when subclassing fuer the purpose of using a different core generator.


    ## -------------------- pickle support  -------------------

    # Issue 17489: Since __reduce__ was defined to fix #759889 this ist no
    # longer called; we leave it here because it has been here since random was
    # rewritten back in 2001 und why risk breaking something.
    def __getstate__(self):  # fuer pickle
        gib self.getstate()

    def __setstate__(self, state):  # fuer pickle
        self.setstate(state)

    def __reduce__(self):
        gib self.__class__, (), self.getstate()


    ## ---- internal support method fuer evenly distributed integers ----

    def __init_subclass__(cls, /, **kwargs):
        """Control how subclasses generate random integers.

        The algorithm a subclass can use depends on the random() and/or
        getrandbits() implementation available to it und determines
        whether it can generate random integers von arbitrarily large
        ranges.
        """

        fuer c in cls.__mro__:
            wenn '_randbelow' in c.__dict__:
                # just inherit it
                breche
            wenn 'getrandbits' in c.__dict__:
                cls._randbelow = cls._randbelow_with_getrandbits
                breche
            wenn 'random' in c.__dict__:
                cls._randbelow = cls._randbelow_without_getrandbits
                breche

    def _randbelow_with_getrandbits(self, n):
        "Return a random int in the range [0,n).  Defined fuer n > 0."

        k = n.bit_length()
        r = self.getrandbits(k)  # 0 <= r < 2**k
        waehrend r >= n:
            r = self.getrandbits(k)
        gib r

    def _randbelow_without_getrandbits(self, n, maxsize=1<<BPF):
        """Return a random int in the range [0,n).  Defined fuer n > 0.

        The implementation does nicht use getrandbits, but only random.
        """

        random = self.random
        wenn n >= maxsize:
            von warnings importiere warn
            warn("Underlying random() generator does nicht supply \n"
                 "enough bits to choose von a population range this large.\n"
                 "To remove the range limitation, add a getrandbits() method.")
            gib _floor(random() * n)
        rem = maxsize % n
        limit = (maxsize - rem) / maxsize   # int(limit * maxsize) % n == 0
        r = random()
        waehrend r >= limit:
            r = random()
        gib _floor(r * maxsize) % n

    _randbelow = _randbelow_with_getrandbits


    ## --------------------------------------------------------
    ## ---- Methods below this point generate custom distributions
    ## ---- based on the methods defined above.  They do not
    ## ---- directly touch the underlying generator und only
    ## ---- access randomness through the methods:  random(),
    ## ---- getrandbits(), oder _randbelow().


    ## -------------------- bytes methods ---------------------

    def randbytes(self, n):
        """Generate n random bytes."""
        gib self.getrandbits(n * 8).to_bytes(n, 'little')


    ## -------------------- integer methods  -------------------

    def randrange(self, start, stop=Nichts, step=_ONE):
        """Choose a random item von range(stop) oder range(start, stop[, step]).

        Roughly equivalent to ``choice(range(start, stop, step))`` but
        supports arbitrarily large ranges und ist optimized fuer common cases.

        """

        # This code ist a bit messy to make it fast fuer the
        # common case waehrend still doing adequate error checking.
        istart = _index(start)
        wenn stop ist Nichts:
            # We don't check fuer "step != 1" because it hasn't been
            # type checked und converted to an integer yet.
            wenn step ist nicht _ONE:
                wirf TypeError("Missing a non-Nichts stop argument")
            wenn istart > 0:
                gib self._randbelow(istart)
            wirf ValueError("empty range fuer randrange()")

        # Stop argument supplied.
        istop = _index(stop)
        width = istop - istart
        istep = _index(step)
        # Fast path.
        wenn istep == 1:
            wenn width > 0:
                gib istart + self._randbelow(width)
            wirf ValueError(f"empty range in randrange({start}, {stop})")

        # Non-unit step argument supplied.
        wenn istep > 0:
            n = (width + istep - 1) // istep
        sowenn istep < 0:
            n = (width + istep + 1) // istep
        sonst:
            wirf ValueError("zero step fuer randrange()")
        wenn n <= 0:
            wirf ValueError(f"empty range in randrange({start}, {stop}, {step})")
        gib istart + istep * self._randbelow(n)

    def randint(self, a, b):
        """Return random integer in range [a, b], including both end points.
        """
        a = _index(a)
        b = _index(b)
        wenn b < a:
            wirf ValueError(f"empty range in randint({a}, {b})")
        gib a + self._randbelow(b - a + 1)


    ## -------------------- sequence methods  -------------------

    def choice(self, seq):
        """Choose a random element von a non-empty sequence."""

        # As an accommodation fuer NumPy, we don't use "if nicht seq"
        # because bool(numpy.array()) raises a ValueError.
        wenn nicht len(seq):
            wirf IndexError('Cannot choose von an empty sequence')
        gib seq[self._randbelow(len(seq))]

    def shuffle(self, x):
        """Shuffle list x in place, und gib Nichts."""

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
        into grand prize und second place winners (the subslices).

        Members of the population need nicht be hashable oder unique.  If the
        population contains repeats, then each occurrence ist a possible
        selection in the sample.

        Repeated elements can be specified one at a time oder mit the optional
        counts parameter.  For example:

            sample(['red', 'blue'], counts=[4, 2], k=5)

        ist equivalent to:

            sample(['red', 'red', 'red', 'red', 'blue', 'blue'], k=5)

        To choose a sample von a range of integers, use range() fuer the
        population argument.  This ist especially fast und space efficient
        fuer sampling von a large population:

            sample(range(10000000), 60)

        """

        # Sampling without replacement entails tracking either potential
        # selections (the pool) in a list oder previous selections in a set.

        # When the number of selections ist small compared to the
        # population, then tracking selections ist efficient, requiring
        # only a small set und an occasional reselection.  For
        # a larger number of selections, the pool tracking method is
        # preferred since the list takes less space than the
        # set und it doesn't suffer von frequent reselections.

        # The number of calls to _randbelow() ist kept at oder near k, the
        # theoretical minimum.  This ist important because running time
        # ist dominated by _randbelow() und because it extracts the
        # least entropy von the underlying random number generators.

        # Memory requirements are kept to the smaller of a k-length
        # set oder an n-length list.

        # There are other sampling algorithms that do nicht require
        # auxiliary memory, but they were rejected because they made
        # too many calls to _randbelow(), making them slower und
        # causing them to eat more entropy than necessary.

        wenn nicht isinstance(population, _Sequence):
            wirf TypeError("Population must be a sequence.  "
                            "For dicts oder sets, use sorted(d).")
        n = len(population)
        wenn counts ist nicht Nichts:
            cum_counts = list(_accumulate(counts))
            wenn len(cum_counts) != n:
                wirf ValueError('The number of counts does nicht match the population')
            total = cum_counts.pop() wenn cum_counts sonst 0
            wenn nicht isinstance(total, int):
                wirf TypeError('Counts must be integers')
            wenn total < 0:
                wirf ValueError('Counts must be non-negative')
            selections = self.sample(range(total), k=k)
            bisect = _bisect
            gib [population[bisect(cum_counts, s)] fuer s in selections]
        randbelow = self._randbelow
        wenn nicht 0 <= k <= n:
            wirf ValueError("Sample larger than population oder ist negative")
        result = [Nichts] * k
        setsize = 21        # size of a small set minus size of an empty list
        wenn k > 5:
            setsize += 4 ** _ceil(_log(k * 3, 4))  # table size fuer big sets
        wenn n <= setsize:
            # An n-length list ist smaller than a k-length set.
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
                waehrend j in selected:
                    j = randbelow(n)
                selected_add(j)
                result[i] = population[j]
        gib result

    def choices(self, population, weights=Nichts, *, cum_weights=Nichts, k=1):
        """Return a k sized list of population elements chosen mit replacement.

        If the relative weights oder cumulative weights are nicht specified,
        the selections are made mit equal probability.

        """
        random = self.random
        n = len(population)
        wenn cum_weights ist Nichts:
            wenn weights ist Nichts:
                floor = _floor
                n += 0.0    # convert to float fuer a small speed improvement
                gib [population[floor(random() * n)] fuer i in _repeat(Nichts, k)]
            versuch:
                cum_weights = list(_accumulate(weights))
            ausser TypeError:
                wenn nicht isinstance(weights, int):
                    wirf
                k = weights
                wirf TypeError(
                    f'The number of choices must be a keyword argument: {k=}'
                ) von Nichts
        sowenn weights ist nicht Nichts:
            wirf TypeError('Cannot specify both weights und cumulative weights')
        wenn len(cum_weights) != n:
            wirf ValueError('The number of weights does nicht match the population')
        total = cum_weights[-1] + 0.0   # convert to float
        wenn total <= 0.0:
            wirf ValueError('Total of weights must be greater than zero')
        wenn nicht _isfinite(total):
            wirf ValueError('Total of weights must be finite')
        bisect = _bisect
        hi = n - 1
        gib [population[bisect(cum_weights, random() * total, 0, hi)]
                fuer i in _repeat(Nichts, k)]


    ## -------------------- real-valued distributions  -------------------

    def uniform(self, a, b):
        """Get a random number in the range [a, b) oder [a, b] depending on rounding.

        The mean (expected value) und variance of the random variable are:

            E[X] = (a + b) / 2
            Var[X] = (b - a) ** 2 / 12

        """
        gib a + (b - a) * self.random()

    def triangular(self, low=0.0, high=1.0, mode=Nichts):
        """Triangular distribution.

        Continuous distribution bounded by given lower und upper limits,
        und having a given mode value in-between.

        http://en.wikipedia.org/wiki/Triangular_distribution

        The mean (expected value) und variance of the random variable are:

            E[X] = (low + high + mode) / 3
            Var[X] = (low**2 + high**2 + mode**2 - low*high - low*mode - high*mode) / 18

        """
        u = self.random()
        versuch:
            c = 0.5 wenn mode ist Nichts sonst (mode - low) / (high - low)
        ausser ZeroDivisionError:
            gib low
        wenn u > c:
            u = 1.0 - u
            c = 1.0 - c
            low, high = high, low
        gib low + (high - low) * _sqrt(u * c)

    def normalvariate(self, mu=0.0, sigma=1.0):
        """Normal distribution.

        mu ist the mean, und sigma ist the standard deviation.

        """
        # Uses Kinderman und Monahan method. Reference: Kinderman,
        # A.J. und Monahan, J.F., "Computer generation of random
        # variables using the ratio of uniform deviates", ACM Trans
        # Math Software, 3, (1977), pp257-260.

        random = self.random
        waehrend Wahr:
            u1 = random()
            u2 = 1.0 - random()
            z = NV_MAGICCONST * (u1 - 0.5) / u2
            zz = z * z / 4.0
            wenn zz <= -_log(u2):
                breche
        gib mu + z * sigma

    def gauss(self, mu=0.0, sigma=1.0):
        """Gaussian distribution.

        mu ist the mean, und sigma ist the standard deviation.  This is
        slightly faster than the normalvariate() function.

        Not thread-safe without a lock around calls.

        """
        # When x und y are two variables von [0, 1), uniformly
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
        # simultaneously, it ist possible that they will receive the
        # same gib value.  The window ist very small though.  To
        # avoid this, you have to use a lock around all calls.  (I
        # didn't want to slow this down in the serial case by using a
        # lock here.)

        random = self.random
        z = self.gauss_next
        self.gauss_next = Nichts
        wenn z ist Nichts:
            x2pi = random() * TWOPI
            g2rad = _sqrt(-2.0 * _log(1.0 - random()))
            z = _cos(x2pi) * g2rad
            self.gauss_next = _sin(x2pi) * g2rad

        gib mu + z * sigma

    def lognormvariate(self, mu, sigma):
        """Log normal distribution.

        If you take the natural logarithm of this distribution, you'll get a
        normal distribution mit mean mu und standard deviation sigma.
        mu can have any value, und sigma must be greater than zero.

        """
        gib _exp(self.normalvariate(mu, sigma))

    def expovariate(self, lambd=1.0):
        """Exponential distribution.

        lambd ist 1.0 divided by the desired mean.  It should be
        nonzero.  (The parameter would be called "lambda", but that is
        a reserved word in Python.)  Returned values range von 0 to
        positive infinity wenn lambd ist positive, und von negative
        infinity to 0 wenn lambd ist negative.

        The mean (expected value) und variance of the random variable are:

            E[X] = 1 / lambd
            Var[X] = 1 / lambd ** 2

        """
        # we use 1-random() instead of random() to preclude the
        # possibility of taking the log of zero.

        gib -_log(1.0 - self.random()) / lambd

    def vonmisesvariate(self, mu, kappa):
        """Circular data distribution.

        mu ist the mean angle, expressed in radians between 0 und 2*pi, und
        kappa ist the concentration parameter, which must be greater than oder
        equal to zero.  If kappa ist equal to zero, this distribution reduces
        to a uniform random angle over the range 0 to 2*pi.

        """
        # Based upon an algorithm published in: Fisher, N.I.,
        # "Statistical Analysis of Circular Data", Cambridge
        # University Press, 1993.

        # Thanks to Magnus Kessler fuer a correction to the
        # implementation of step 4.

        random = self.random
        wenn kappa <= 1e-6:
            gib TWOPI * random()

        s = 0.5 / kappa
        r = s + _sqrt(1.0 + s * s)

        waehrend Wahr:
            u1 = random()
            z = _cos(_pi * u1)

            d = z / (r + z)
            u2 = random()
            wenn u2 < 1.0 - d * d oder u2 <= (1.0 - d) * _exp(d):
                breche

        q = 1.0 / r
        f = (q + z) / (1.0 + q * z)
        u3 = random()
        wenn u3 > 0.5:
            theta = (mu + _acos(f)) % TWOPI
        sonst:
            theta = (mu - _acos(f)) % TWOPI

        gib theta

    def gammavariate(self, alpha, beta):
        """Gamma distribution.  Not the gamma function!

        Conditions on the parameters are alpha > 0 und beta > 0.

        The probability distribution function is:

                    x ** (alpha - 1) * math.exp(-x / beta)
          pdf(x) =  --------------------------------------
                      math.gamma(alpha) * beta ** alpha

        The mean (expected value) und variance of the random variable are:

            E[X] = alpha * beta
            Var[X] = alpha * beta ** 2

        """

        # Warning: a few older sources define the gamma distribution in terms
        # of alpha > -1.0
        wenn alpha <= 0.0 oder beta <= 0.0:
            wirf ValueError('gammavariate: alpha und beta must be > 0.0')

        random = self.random
        wenn alpha > 1.0:

            # Uses R.C.H. Cheng, "The generation of Gamma
            # variables mit non-integral shape parameters",
            # Applied Statistics, (1977), 26, No. 1, p71-74

            ainv = _sqrt(2.0 * alpha - 1.0)
            bbb = alpha - LOG4
            ccc = alpha + ainv

            waehrend Wahr:
                u1 = random()
                wenn nicht 1e-7 < u1 < 0.9999999:
                    weiter
                u2 = 1.0 - random()
                v = _log(u1 / (1.0 - u1)) / ainv
                x = alpha * _exp(v)
                z = u1 * u1 * u2
                r = bbb + ccc * v - x
                wenn r + SG_MAGICCONST - 4.5 * z >= 0.0 oder r >= _log(z):
                    gib x * beta

        sowenn alpha == 1.0:
            # expovariate(1/beta)
            gib -_log(1.0 - random()) * beta

        sonst:
            # alpha ist between 0 und 1 (exclusive)
            # Uses ALGORITHM GS of Statistical Computing - Kennedy & Gentle
            waehrend Wahr:
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
                        breche
                sowenn u1 <= _exp(-x):
                    breche
            gib x * beta

    def betavariate(self, alpha, beta):
        """Beta distribution.

        Conditions on the parameters are alpha > 0 und beta > 0.
        Returned values range between 0 und 1.

        The mean (expected value) und variance of the random variable are:

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
        ##        gib z/(y+z)
        ##
        ## was dead wrong, und how it probably got that way.

        # This version due to Janne Sinkkonen, und matches all the std
        # texts (e.g., Knuth Vol 2 Ed 3 pg 134 "the beta distribution").
        y = self.gammavariate(alpha, 1.0)
        wenn y:
            gib y / (y + self.gammavariate(beta, 1.0))
        gib 0.0

    def paretovariate(self, alpha):
        """Pareto distribution.  alpha ist the shape parameter."""
        # Jain, pg. 495

        u = 1.0 - self.random()
        gib u ** (-1.0 / alpha)

    def weibullvariate(self, alpha, beta):
        """Weibull distribution.

        alpha ist the scale parameter und beta ist the shape parameter.

        """
        # Jain, pg. 499; bug fix courtesy Bill Arms

        u = 1.0 - self.random()
        gib alpha * (-_log(u)) ** (1.0 / beta)


    ## -------------------- discrete  distributions  ---------------------

    def binomialvariate(self, n=1, p=0.5):
        """Binomial random variable.

        Gives the number of successes fuer *n* independent trials
        mit the probability of success in each trial being *p*:

            sum(random() < p fuer i in range(n))

        Returns an integer in the range:

            0 <= X <= n

        The integer ist chosen mit the probability:

            P(X == k) = math.comb(n, k) * p ** k * (1 - p) ** (n - k)

        The mean (expected value) und variance of the random variable are:

            E[X] = n * p
            Var[X] = n * p * (1 - p)

        """
        # Error check inputs und handle edge cases
        wenn n < 0:
            wirf ValueError("n must be non-negative")
        wenn p <= 0.0 oder p >= 1.0:
            wenn p == 0.0:
                gib 0
            wenn p == 1.0:
                gib n
            wirf ValueError("p must be in the range 0.0 <= p <= 1.0")

        random = self.random

        # Fast path fuer a common case
        wenn n == 1:
            gib _index(random() < p)

        # Exploit symmetry to establish:  p <= 0.5
        wenn p > 0.5:
            gib n - self.binomialvariate(n, 1.0 - p)

        wenn n * p < 10.0:
            # BG: Geometric method by Devroye mit running time of O(np).
            # https://dl.acm.org/doi/pdf/10.1145/42372.42381
            x = y = 0
            c = _log2(1.0 - p)
            wenn nicht c:
                gib x
            waehrend Wahr:
                y += _floor(_log2(random()) / c) + 1
                wenn y > n:
                    gib x
                x += 1

        # BTRS: Transformed rejection mit squeeze method by Wolfgang Hörmann
        # https://citeseerx.ist.psu.edu/viewdoc/download?doi=10.1.1.47.8407&rep=rep1&type=pdf
        assert n*p >= 10.0 und p <= 0.5

        setup_complete = Falsch
        spq = _sqrt(n * p * (1.0 - p))  # Standard deviation of the distribution
        b = 1.15 + 2.53 * spq
        a = -0.0873 + 0.0248 * b + 0.01 * p
        c = n * p + 0.5
        vr = 0.92 - 4.2 / b

        waehrend Wahr:

            u = random()
            u -= 0.5
            us = 0.5 - _fabs(u)
            k = _floor((2.0 * a / us + b) * u + c)
            wenn k < 0 oder k > n:
                weiter
            v = random()

            # The early-out "squeeze" test substantially reduces
            # the number of acceptance condition evaluations.
            wenn us >= 0.07 und v <= vr:
                gib k

            wenn nicht setup_complete:
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
                gib k


## ------------------------------------------------------------------
## --------------- Operating System Random Source  ------------------


klasse SystemRandom(Random):
    """Alternate random number generator using sources provided
    by the operating system (such als /dev/urandom on Unix oder
    CryptGenRandom on Windows).

     Not available on all systems (see os.urandom() fuer details).

    """

    def random(self):
        """Get the next random number in the range 0.0 <= X < 1.0."""
        gib (int.from_bytes(_urandom(7)) >> 3) * RECIP_BPF

    def getrandbits(self, k):
        """getrandbits(k) -> x.  Generates an int mit k random bits."""
        wenn k < 0:
            wirf ValueError('number of bits must be non-negative')
        numbytes = (k + 7) // 8                       # bits / 8 und rounded up
        x = int.from_bytes(_urandom(numbytes))
        gib x >> (numbytes * 8 - k)                # trim excess bits

    def randbytes(self, n):
        """Generate n random bytes."""
        # os.urandom(n) fails mit ValueError fuer n < 0
        # und returns an empty bytes string fuer n == 0.
        gib _urandom(n)

    def seed(self, *args, **kwds):
        "Stub method.  Not used fuer a system random number generator."
        gib Nichts

    def _notimplemented(self, *args, **kwds):
        "Method should nicht be called fuer a system random number generator."
        wirf NotImplementedError('System entropy source does nicht have state.')
    getstate = setstate = _notimplemented


# ----------------------------------------------------------------------
# Create one instance, seeded von current time, und export its methods
# als module-level functions.  The functions share state across all uses
# (both in the user's code und in the Python libraries), but that's fine
# fuer most programs und ist easier fuer the casual user than making them
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
        help="print a random integer between 1 und N inclusive")
    group.add_argument(
        "-f", "--float", type=float, metavar="N",
        help="print a random floating-point number between 0 und N inclusive")
    group.add_argument(
        "--test", type=int, const=10_000, nargs="?",
        help=argparse.SUPPRESS)
    parser.add_argument("input", nargs="*",
                        help="""\
wenn no options given, output depends on the input
    string oder multiple: same als --choice
    integer: same als --integer
    float: same als --float""")
    args = parser.parse_args(arg_list)
    gib args, parser.format_help()


def main(arg_list: list[str] | Nichts = Nichts) -> int | str:
    args, help_text = _parse_args(arg_list)

    # Explicit arguments
    wenn args.choice:
        gib choice(args.choice)

    wenn args.integer ist nicht Nichts:
        gib randint(1, args.integer)

    wenn args.float ist nicht Nichts:
        gib uniform(0, args.float)

    wenn args.test:
        _test(args.test)
        gib ""

    # No explicit argument, select based on input
    wenn len(args.input) == 1:
        val = args.input[0]
        versuch:
            # Is it an integer?
            val = int(val)
            gib randint(1, val)
        ausser ValueError:
            versuch:
                # Is it a float?
                val = float(val)
                gib uniform(0, val)
            ausser ValueError:
                # Split in case of space-separated string: "a b c"
                gib choice(val.split())

    wenn len(args.input) >= 2:
        gib choice(args.input)

    gib help_text


wenn __name__ == '__main__':
    drucke(main())
