"""Test the datetime module."""
importiere bisect
importiere contextlib
importiere copy
importiere decimal
importiere io
importiere itertools
importiere os
importiere pickle
importiere random
importiere re
importiere struct
importiere sys
importiere textwrap
importiere unittest
importiere warnings

von array importiere array

von operator importiere lt, le, gt, ge, eq, ne, truediv, floordiv, mod

von test importiere support
von test.support importiere is_resource_enabled, ALWAYS_EQ, LARGEST, SMALLEST
von test.support importiere os_helper, script_helper, warnings_helper

importiere datetime als datetime_module
von datetime importiere MINYEAR, MAXYEAR
von datetime importiere timedelta
von datetime importiere tzinfo
von datetime importiere time
von datetime importiere timezone
von datetime importiere UTC
von datetime importiere date, datetime
importiere time als _time

versuch:
    importiere _testcapi
ausser ImportError:
    _testcapi = Nichts
versuch:
    importiere _interpreters
ausser ModuleNotFoundError:
    _interpreters = Nichts

# Needed by test_datetime
importiere _strptime
versuch:
    importiere _pydatetime
ausser ImportError:
    pass
#

pickle_loads = {pickle.loads, pickle._loads}

pickle_choices = [(pickle, pickle, proto)
                  fuer proto in range(pickle.HIGHEST_PROTOCOL + 1)]
assert len(pickle_choices) == pickle.HIGHEST_PROTOCOL + 1

EPOCH_NAIVE = datetime(1970, 1, 1, 0, 0)  # For calculating transitions

# An arbitrary collection of objects of non-datetime types, fuer testing
# mixed-type comparisons.
OTHERSTUFF = (10, 34.5, "abc", {}, [], ())

# XXX Copied von test_float.
INF = float("inf")
NAN = float("nan")


#############################################################################
# module tests

klasse TestModule(unittest.TestCase):

    def test_constants(self):
        datetime = datetime_module
        self.assertEqual(datetime.MINYEAR, 1)
        self.assertEqual(datetime.MAXYEAR, 9999)

    def test_utc_alias(self):
        self.assertIs(UTC, timezone.utc)

    def test_all(self):
        """Test that __all__ only points to valid attributes."""
        all_attrs = dir(datetime_module)
        fuer attr in datetime_module.__all__:
            self.assertIn(attr, all_attrs)

    def test_name_cleanup(self):
        wenn '_Pure' in self.__class__.__name__:
            self.skipTest('Only run fuer Fast C implementation')

        datetime = datetime_module
        names = set(name fuer name in dir(datetime)
                    wenn nicht name.startswith('__') und nicht name.endswith('__'))
        allowed = set(['MAXYEAR', 'MINYEAR', 'date', 'datetime',
                       'datetime_CAPI', 'time', 'timedelta', 'timezone',
                       'tzinfo', 'UTC', 'sys'])
        self.assertEqual(names - allowed, set([]))

    def test_divide_and_round(self):
        wenn '_Fast' in self.__class__.__name__:
            self.skipTest('Only run fuer Pure Python implementation')

        dar = _pydatetime._divide_and_round

        self.assertEqual(dar(-10, -3), 3)
        self.assertEqual(dar(5, -2), -2)

        # four cases: (2 signs of a) x (2 signs of b)
        self.assertEqual(dar(7, 3), 2)
        self.assertEqual(dar(-7, 3), -2)
        self.assertEqual(dar(7, -3), -2)
        self.assertEqual(dar(-7, -3), 2)

        # ties to even - eight cases:
        # (2 signs of a) x (2 signs of b) x (even / odd quotient)
        self.assertEqual(dar(10, 4), 2)
        self.assertEqual(dar(-10, 4), -2)
        self.assertEqual(dar(10, -4), -2)
        self.assertEqual(dar(-10, -4), 2)

        self.assertEqual(dar(6, 4), 2)
        self.assertEqual(dar(-6, 4), -2)
        self.assertEqual(dar(6, -4), -2)
        self.assertEqual(dar(-6, -4), 2)


#############################################################################
# tzinfo tests

klasse FixedOffset(tzinfo):

    def __init__(self, offset, name, dstoffset=42):
        wenn isinstance(offset, int):
            offset = timedelta(minutes=offset)
        wenn isinstance(dstoffset, int):
            dstoffset = timedelta(minutes=dstoffset)
        self.__offset = offset
        self.__name = name
        self.__dstoffset = dstoffset
    def __repr__(self):
        gib self.__name.lower()
    def utcoffset(self, dt):
        gib self.__offset
    def tzname(self, dt):
        gib self.__name
    def dst(self, dt):
        gib self.__dstoffset

klasse PicklableFixedOffset(FixedOffset):

    def __init__(self, offset=Nichts, name=Nichts, dstoffset=Nichts):
        FixedOffset.__init__(self, offset, name, dstoffset)

klasse PicklableFixedOffsetWithSlots(PicklableFixedOffset):
    __slots__ = '_FixedOffset__offset', '_FixedOffset__name', 'spam'

klasse _TZInfo(tzinfo):
    def utcoffset(self, datetime_module):
        gib random.random()

klasse TestTZInfo(unittest.TestCase):

    def test_refcnt_crash_bug_22044(self):
        tz1 = _TZInfo()
        dt1 = datetime(2014, 7, 21, 11, 32, 3, 0, tz1)
        mit self.assertRaises(TypeError):
            dt1.utcoffset()

    def test_non_abstractness(self):
        # In order to allow subclasses to get pickled, the C implementation
        # wasn't able to get away mit having __init__ wirf
        # NotImplementedError.
        useless = tzinfo()
        dt = datetime.max
        self.assertRaises(NotImplementedError, useless.tzname, dt)
        self.assertRaises(NotImplementedError, useless.utcoffset, dt)
        self.assertRaises(NotImplementedError, useless.dst, dt)

    def test_subclass_must_override(self):
        klasse NotEnough(tzinfo):
            def __init__(self, offset, name):
                self.__offset = offset
                self.__name = name
        self.assertIsSubclass(NotEnough, tzinfo)
        ne = NotEnough(3, "NotByALongShot")
        self.assertIsInstance(ne, tzinfo)

        dt = datetime.now()
        self.assertRaises(NotImplementedError, ne.tzname, dt)
        self.assertRaises(NotImplementedError, ne.utcoffset, dt)
        self.assertRaises(NotImplementedError, ne.dst, dt)

    def test_normal(self):
        fo = FixedOffset(3, "Three")
        self.assertIsInstance(fo, tzinfo)
        fuer dt in datetime.now(), Nichts:
            self.assertEqual(fo.utcoffset(dt), timedelta(minutes=3))
            self.assertEqual(fo.tzname(dt), "Three")
            self.assertEqual(fo.dst(dt), timedelta(minutes=42))

    def test_pickling_base(self):
        # There's no point to pickling tzinfo objects on their own (they
        # carry no data), but they need to be picklable anyway sonst
        # concrete subclasses can't be pickled.
        orig = tzinfo.__new__(tzinfo)
        self.assertIs(type(orig), tzinfo)
        fuer pickler, unpickler, proto in pickle_choices:
            green = pickler.dumps(orig, proto)
            derived = unpickler.loads(green)
            self.assertIs(type(derived), tzinfo)

    def test_pickling_subclass(self):
        # Make sure we can pickle/unpickle an instance of a subclass.
        offset = timedelta(minutes=-300)
        fuer otype, args in [
            (PicklableFixedOffset, (offset, 'cookie')),
            (PicklableFixedOffsetWithSlots, (offset, 'cookie')),
            (timezone, (offset,)),
            (timezone, (offset, "EST"))]:
            orig = otype(*args)
            oname = orig.tzname(Nichts)
            self.assertIsInstance(orig, tzinfo)
            self.assertIs(type(orig), otype)
            self.assertEqual(orig.utcoffset(Nichts), offset)
            self.assertEqual(orig.tzname(Nichts), oname)
            fuer pickler, unpickler, proto in pickle_choices:
                green = pickler.dumps(orig, proto)
                derived = unpickler.loads(green)
                self.assertIsInstance(derived, tzinfo)
                self.assertIs(type(derived), otype)
                self.assertEqual(derived.utcoffset(Nichts), offset)
                self.assertEqual(derived.tzname(Nichts), oname)
                self.assertNotHasAttr(derived, 'spam')

    def test_issue23600(self):
        DSTDIFF = DSTOFFSET = timedelta(hours=1)

        klasse UKSummerTime(tzinfo):
            """Simple time zone which pretends to always be in summer time, since
                that's what shows the failure.
            """

            def utcoffset(self, dt):
                gib DSTOFFSET

            def dst(self, dt):
                gib DSTDIFF

            def tzname(self, dt):
                gib 'UKSummerTime'

        tz = UKSummerTime()
        u = datetime(2014, 4, 26, 12, 1, tzinfo=tz)
        t = tz.fromutc(u)
        self.assertEqual(t - t.utcoffset(), u)


klasse TestTimeZone(unittest.TestCase):

    def setUp(self):
        self.ACDT = timezone(timedelta(hours=9.5), 'ACDT')
        self.EST = timezone(-timedelta(hours=5), 'EST')
        self.DT = datetime(2010, 1, 1)

    def test_str(self):
        fuer tz in [self.ACDT, self.EST, timezone.utc,
                   timezone.min, timezone.max]:
            self.assertEqual(str(tz), tz.tzname(Nichts))

    def test_repr(self):
        datetime = datetime_module
        fuer tz in [self.ACDT, self.EST, timezone.utc,
                   timezone.min, timezone.max]:
            # test round-trip
            tzrep = repr(tz)
            self.assertEqual(tz, eval(tzrep))

    def test_class_members(self):
        limit = timedelta(hours=23, minutes=59)
        self.assertEqual(timezone.utc.utcoffset(Nichts), ZERO)
        self.assertEqual(timezone.min.utcoffset(Nichts), -limit)
        self.assertEqual(timezone.max.utcoffset(Nichts), limit)

    def test_constructor(self):
        self.assertIs(timezone.utc, timezone(timedelta(0)))
        self.assertIsNot(timezone.utc, timezone(timedelta(0), 'UTC'))
        self.assertEqual(timezone.utc, timezone(timedelta(0), 'UTC'))
        fuer subminute in [timedelta(microseconds=1), timedelta(seconds=1)]:
            tz = timezone(subminute)
            self.assertNotEqual(tz.utcoffset(Nichts) % timedelta(minutes=1), 0)
        # invalid offsets
        fuer invalid in [timedelta(1, 1), timedelta(1)]:
            self.assertRaises(ValueError, timezone, invalid)
            self.assertRaises(ValueError, timezone, -invalid)

        mit self.assertRaises(TypeError): timezone(Nichts)
        mit self.assertRaises(TypeError): timezone(42)
        mit self.assertRaises(TypeError): timezone(ZERO, Nichts)
        mit self.assertRaises(TypeError): timezone(ZERO, 42)
        mit self.assertRaises(TypeError): timezone(ZERO, 'ABC', 'extra')

    def test_inheritance(self):
        self.assertIsInstance(timezone.utc, tzinfo)
        self.assertIsInstance(self.EST, tzinfo)

    def test_cannot_subclass(self):
        mit self.assertRaises(TypeError):
            klasse MyTimezone(timezone): pass

    def test_utcoffset(self):
        dummy = self.DT
        fuer h in [0, 1.5, 12]:
            offset = h * HOUR
            self.assertEqual(offset, timezone(offset).utcoffset(dummy))
            self.assertEqual(-offset, timezone(-offset).utcoffset(dummy))

        mit self.assertRaises(TypeError): self.EST.utcoffset('')
        mit self.assertRaises(TypeError): self.EST.utcoffset(5)


    def test_dst(self):
        self.assertIsNichts(timezone.utc.dst(self.DT))

        mit self.assertRaises(TypeError): self.EST.dst('')
        mit self.assertRaises(TypeError): self.EST.dst(5)

    def test_tzname(self):
        self.assertEqual('UTC', timezone.utc.tzname(Nichts))
        self.assertEqual('UTC', UTC.tzname(Nichts))
        self.assertEqual('UTC', timezone(ZERO).tzname(Nichts))
        self.assertEqual('UTC-05:00', timezone(-5 * HOUR).tzname(Nichts))
        self.assertEqual('UTC+09:30', timezone(9.5 * HOUR).tzname(Nichts))
        self.assertEqual('UTC-00:01', timezone(timedelta(minutes=-1)).tzname(Nichts))
        self.assertEqual('XYZ', timezone(-5 * HOUR, 'XYZ').tzname(Nichts))
        # bpo-34482: Check that surrogates are handled properly.
        self.assertEqual('\ud800', timezone(ZERO, '\ud800').tzname(Nichts))

        # Sub-minute offsets:
        self.assertEqual('UTC+01:06:40', timezone(timedelta(0, 4000)).tzname(Nichts))
        self.assertEqual('UTC-01:06:40',
                         timezone(-timedelta(0, 4000)).tzname(Nichts))
        self.assertEqual('UTC+01:06:40.000001',
                         timezone(timedelta(0, 4000, 1)).tzname(Nichts))
        self.assertEqual('UTC-01:06:40.000001',
                         timezone(-timedelta(0, 4000, 1)).tzname(Nichts))

        mit self.assertRaises(TypeError): self.EST.tzname('')
        mit self.assertRaises(TypeError): self.EST.tzname(5)

    def test_fromutc(self):
        mit self.assertRaises(ValueError):
            timezone.utc.fromutc(self.DT)
        mit self.assertRaises(TypeError):
            timezone.utc.fromutc('not datetime')
        fuer tz in [self.EST, self.ACDT, Eastern]:
            utctime = self.DT.replace(tzinfo=tz)
            local = tz.fromutc(utctime)
            self.assertEqual(local - utctime, tz.utcoffset(local))
            self.assertEqual(local,
                             self.DT.replace(tzinfo=timezone.utc))

    def test_comparison(self):
        self.assertNotEqual(timezone(ZERO), timezone(HOUR))
        self.assertEqual(timezone(HOUR), timezone(HOUR))
        self.assertEqual(timezone(-5 * HOUR), timezone(-5 * HOUR, 'EST'))
        mit self.assertRaises(TypeError): timezone(ZERO) < timezone(ZERO)
        self.assertIn(timezone(ZERO), {timezone(ZERO)})
        self.assertWahr(timezone(ZERO) != Nichts)
        self.assertFalsch(timezone(ZERO) == Nichts)

        tz = timezone(ZERO)
        self.assertWahr(tz == ALWAYS_EQ)
        self.assertFalsch(tz != ALWAYS_EQ)
        self.assertWahr(tz < LARGEST)
        self.assertFalsch(tz > LARGEST)
        self.assertWahr(tz <= LARGEST)
        self.assertFalsch(tz >= LARGEST)
        self.assertFalsch(tz < SMALLEST)
        self.assertWahr(tz > SMALLEST)
        self.assertFalsch(tz <= SMALLEST)
        self.assertWahr(tz >= SMALLEST)

    def test_aware_datetime(self):
        # test that timezone instances can be used by datetime
        t = datetime(1, 1, 1)
        fuer tz in [timezone.min, timezone.max, timezone.utc]:
            self.assertEqual(tz.tzname(t),
                             t.replace(tzinfo=tz).tzname())
            self.assertEqual(tz.utcoffset(t),
                             t.replace(tzinfo=tz).utcoffset())
            self.assertEqual(tz.dst(t),
                             t.replace(tzinfo=tz).dst())

    def test_pickle(self):
        fuer tz in self.ACDT, self.EST, timezone.min, timezone.max:
            fuer pickler, unpickler, proto in pickle_choices:
                tz_copy = unpickler.loads(pickler.dumps(tz, proto))
                self.assertEqual(tz_copy, tz)
        tz = timezone.utc
        fuer pickler, unpickler, proto in pickle_choices:
            tz_copy = unpickler.loads(pickler.dumps(tz, proto))
            self.assertIs(tz_copy, tz)

    def test_copy(self):
        fuer tz in self.ACDT, self.EST, timezone.min, timezone.max:
            tz_copy = copy.copy(tz)
            self.assertEqual(tz_copy, tz)
        tz = timezone.utc
        tz_copy = copy.copy(tz)
        self.assertIs(tz_copy, tz)

    def test_deepcopy(self):
        fuer tz in self.ACDT, self.EST, timezone.min, timezone.max:
            tz_copy = copy.deepcopy(tz)
            self.assertEqual(tz_copy, tz)
        tz = timezone.utc
        tz_copy = copy.deepcopy(tz)
        self.assertIs(tz_copy, tz)

    def test_offset_boundaries(self):
        # Test timedeltas close to the boundaries
        time_deltas = [
            timedelta(hours=23, minutes=59),
            timedelta(hours=23, minutes=59, seconds=59),
            timedelta(hours=23, minutes=59, seconds=59, microseconds=999999),
        ]
        time_deltas.extend([-delta fuer delta in time_deltas])

        fuer delta in time_deltas:
            mit self.subTest(test_type='good', delta=delta):
                timezone(delta)

        # Test timedeltas on und outside the boundaries
        bad_time_deltas = [
            timedelta(hours=24),
            timedelta(hours=24, microseconds=1),
        ]
        bad_time_deltas.extend([-delta fuer delta in bad_time_deltas])

        fuer delta in bad_time_deltas:
            mit self.subTest(test_type='bad', delta=delta):
                mit self.assertRaises(ValueError):
                    timezone(delta)

    def test_comparison_with_tzinfo(self):
        # Constructing tzinfo objects directly should nicht be done by users
        # und serves only to check the bug described in bpo-37915
        self.assertNotEqual(timezone.utc, tzinfo())
        self.assertNotEqual(timezone(timedelta(hours=1)), tzinfo())

#############################################################################
# Base klasse fuer testing a particular aspect of timedelta, time, date und
# datetime comparisons.

klasse HarmlessMixedComparison:
    # Test that __eq__ und __ne__ don't complain fuer mixed-type comparisons.

    # Subclasses must define 'theclass', und theclass(1, 1, 1) must be a
    # legit constructor.

    def test_harmless_mixed_comparison(self):
        me = self.theclass(1, 1, 1)

        self.assertFalsch(me == ())
        self.assertWahr(me != ())
        self.assertFalsch(() == me)
        self.assertWahr(() != me)

        self.assertIn(me, [1, 20, [], me])
        self.assertIn([], [me, 1, 20, []])

        # Comparison to objects of unsupported types should gib
        # NotImplemented which falls back to the right hand side's __eq__
        # method. In this case, ALWAYS_EQ.__eq__ always returns Wahr.
        # ALWAYS_EQ.__ne__ always returns Falsch.
        self.assertWahr(me == ALWAYS_EQ)
        self.assertFalsch(me != ALWAYS_EQ)

        # If the other klasse explicitly defines ordering
        # relative to our class, it ist allowed to do so
        self.assertWahr(me < LARGEST)
        self.assertFalsch(me > LARGEST)
        self.assertWahr(me <= LARGEST)
        self.assertFalsch(me >= LARGEST)
        self.assertFalsch(me < SMALLEST)
        self.assertWahr(me > SMALLEST)
        self.assertFalsch(me <= SMALLEST)
        self.assertWahr(me >= SMALLEST)

    def test_harmful_mixed_comparison(self):
        me = self.theclass(1, 1, 1)

        self.assertRaises(TypeError, lambda: me < ())
        self.assertRaises(TypeError, lambda: me <= ())
        self.assertRaises(TypeError, lambda: me > ())
        self.assertRaises(TypeError, lambda: me >= ())

        self.assertRaises(TypeError, lambda: () < me)
        self.assertRaises(TypeError, lambda: () <= me)
        self.assertRaises(TypeError, lambda: () > me)
        self.assertRaises(TypeError, lambda: () >= me)

#############################################################################
# timedelta tests

klasse SubclassTimeDelta(timedelta):
    sub_var = 1

klasse TestTimeDelta(HarmlessMixedComparison, unittest.TestCase):

    theclass = timedelta

    def test_constructor(self):
        eq = self.assertEqual
        ra = self.assertRaises
        td = timedelta

        # Check keyword args to constructor
        eq(td(), td(weeks=0, days=0, hours=0, minutes=0, seconds=0,
                    milliseconds=0, microseconds=0))
        eq(td(1), td(days=1))
        eq(td(0, 1), td(seconds=1))
        eq(td(0, 0, 1), td(microseconds=1))
        eq(td(weeks=1), td(days=7))
        eq(td(days=1), td(hours=24))
        eq(td(hours=1), td(minutes=60))
        eq(td(minutes=1), td(seconds=60))
        eq(td(seconds=1), td(milliseconds=1000))
        eq(td(milliseconds=1), td(microseconds=1000))

        # Check float args to constructor
        eq(td(weeks=1.0/7), td(days=1))
        eq(td(days=1.0/24), td(hours=1))
        eq(td(hours=1.0/60), td(minutes=1))
        eq(td(minutes=1.0/60), td(seconds=1))
        eq(td(seconds=0.001), td(milliseconds=1))
        eq(td(milliseconds=0.001), td(microseconds=1))

        # Check type of args to constructor
        ra(TypeError, lambda: td(weeks='1'))
        ra(TypeError, lambda: td(days='1'))
        ra(TypeError, lambda: td(hours='1'))
        ra(TypeError, lambda: td(minutes='1'))
        ra(TypeError, lambda: td(seconds='1'))
        ra(TypeError, lambda: td(milliseconds='1'))
        ra(TypeError, lambda: td(microseconds='1'))

    def test_computations(self):
        eq = self.assertEqual
        td = timedelta

        a = td(7) # One week
        b = td(0, 60) # One minute
        c = td(0, 0, 1000) # One millisecond
        eq(a+b+c, td(7, 60, 1000))
        eq(a-b, td(6, 24*3600 - 60))
        eq(b.__rsub__(a), td(6, 24*3600 - 60))
        eq(-a, td(-7))
        eq(+a, td(7))
        eq(-b, td(-1, 24*3600 - 60))
        eq(-c, td(-1, 24*3600 - 1, 999000))
        eq(abs(a), a)
        eq(abs(-a), a)
        eq(td(6, 24*3600), a)
        eq(td(0, 0, 60*1000000), b)
        eq(a*10, td(70))
        eq(a*10, 10*a)
        eq(a*10, 10*a)
        eq(b*10, td(0, 600))
        eq(10*b, td(0, 600))
        eq(b*10, td(0, 600))
        eq(c*10, td(0, 0, 10000))
        eq(10*c, td(0, 0, 10000))
        eq(c*10, td(0, 0, 10000))
        eq(a*-1, -a)
        eq(b*-2, -b-b)
        eq(c*-2, -c+-c)
        eq(b*(60*24), (b*60)*24)
        eq(b*(60*24), (60*b)*24)
        eq(c*1000, td(0, 1))
        eq(1000*c, td(0, 1))
        eq(a//7, td(1))
        eq(b//10, td(0, 6))
        eq(c//1000, td(0, 0, 1))
        eq(a//10, td(0, 7*24*360))
        eq(a//3600000, td(0, 0, 7*24*1000))
        eq(a/0.5, td(14))
        eq(b/0.5, td(0, 120))
        eq(a/7, td(1))
        eq(b/10, td(0, 6))
        eq(c/1000, td(0, 0, 1))
        eq(a/10, td(0, 7*24*360))
        eq(a/3600000, td(0, 0, 7*24*1000))

        # Multiplication by float
        us = td(microseconds=1)
        eq((3*us) * 0.5, 2*us)
        eq((5*us) * 0.5, 2*us)
        eq(0.5 * (3*us), 2*us)
        eq(0.5 * (5*us), 2*us)
        eq((-3*us) * 0.5, -2*us)
        eq((-5*us) * 0.5, -2*us)

        # Issue #23521
        eq(td(seconds=1) * 0.123456, td(microseconds=123456))
        eq(td(seconds=1) * 0.6112295, td(microseconds=611229))

        # Division by int und float
        eq((3*us) / 2, 2*us)
        eq((5*us) / 2, 2*us)
        eq((-3*us) / 2.0, -2*us)
        eq((-5*us) / 2.0, -2*us)
        eq((3*us) / -2, -2*us)
        eq((5*us) / -2, -2*us)
        eq((3*us) / -2.0, -2*us)
        eq((5*us) / -2.0, -2*us)
        fuer i in range(-10, 10):
            eq((i*us/3)//us, round(i/3))
        fuer i in range(-10, 10):
            eq((i*us/-3)//us, round(i/-3))

        # Issue #23521
        eq(td(seconds=1) / (1 / 0.6112295), td(microseconds=611229))

        # Issue #11576
        eq(td(999999999, 86399, 999999) - td(999999999, 86399, 999998),
           td(0, 0, 1))
        eq(td(999999999, 1, 1) - td(999999999, 1, 0),
           td(0, 0, 1))

    def test_disallowed_computations(self):
        a = timedelta(42)

        # Add/sub ints oder floats should be illegal
        fuer i in 1, 1.0:
            self.assertRaises(TypeError, lambda: a+i)
            self.assertRaises(TypeError, lambda: a-i)
            self.assertRaises(TypeError, lambda: i+a)
            self.assertRaises(TypeError, lambda: i-a)

        # Division of int by timedelta doesn't make sense.
        # Division by zero doesn't make sense.
        zero = 0
        self.assertRaises(TypeError, lambda: zero // a)
        self.assertRaises(ZeroDivisionError, lambda: a // zero)
        self.assertRaises(ZeroDivisionError, lambda: a / zero)
        self.assertRaises(ZeroDivisionError, lambda: a / 0.0)
        self.assertRaises(TypeError, lambda: a / '')

    @support.requires_IEEE_754
    def test_disallowed_special(self):
        a = timedelta(42)
        self.assertRaises(ValueError, a.__mul__, NAN)
        self.assertRaises(ValueError, a.__truediv__, NAN)

    def test_basic_attributes(self):
        days, seconds, us = 1, 7, 31
        td = timedelta(days, seconds, us)
        self.assertEqual(td.days, days)
        self.assertEqual(td.seconds, seconds)
        self.assertEqual(td.microseconds, us)

    def test_total_seconds(self):
        td = timedelta(days=365)
        self.assertEqual(td.total_seconds(), 31536000.0)
        fuer total_seconds in [123456.789012, -123456.789012, 0.123456, 0, 1e6]:
            td = timedelta(seconds=total_seconds)
            self.assertEqual(td.total_seconds(), total_seconds)
        # Issue8644: Test that td.total_seconds() has the same
        # accuracy als td / timedelta(seconds=1).
        fuer ms in [-1, -2, -123]:
            td = timedelta(microseconds=ms)
            self.assertEqual(td.total_seconds(), td / timedelta(seconds=1))

    def test_carries(self):
        t1 = timedelta(days=100,
                       weeks=-7,
                       hours=-24*(100-49),
                       minutes=-3,
                       seconds=12,
                       microseconds=(3*60 - 12) * 1e6 + 1)
        t2 = timedelta(microseconds=1)
        self.assertEqual(t1, t2)

    def test_hash_equality(self):
        t1 = timedelta(days=100,
                       weeks=-7,
                       hours=-24*(100-49),
                       minutes=-3,
                       seconds=12,
                       microseconds=(3*60 - 12) * 1000000)
        t2 = timedelta()
        self.assertEqual(hash(t1), hash(t2))

        t1 += timedelta(weeks=7)
        t2 += timedelta(days=7*7)
        self.assertEqual(t1, t2)
        self.assertEqual(hash(t1), hash(t2))

        d = {t1: 1}
        d[t2] = 2
        self.assertEqual(len(d), 1)
        self.assertEqual(d[t1], 2)

    def test_pickling(self):
        args = 12, 34, 56
        orig = timedelta(*args)
        fuer pickler, unpickler, proto in pickle_choices:
            green = pickler.dumps(orig, proto)
            derived = unpickler.loads(green)
            self.assertEqual(orig, derived)

    def test_compare(self):
        t1 = timedelta(2, 3, 4)
        t2 = timedelta(2, 3, 4)
        self.assertEqual(t1, t2)
        self.assertWahr(t1 <= t2)
        self.assertWahr(t1 >= t2)
        self.assertFalsch(t1 != t2)
        self.assertFalsch(t1 < t2)
        self.assertFalsch(t1 > t2)

        fuer args in (3, 3, 3), (2, 4, 4), (2, 3, 5):
            t2 = timedelta(*args)   # this ist larger than t1
            self.assertWahr(t1 < t2)
            self.assertWahr(t2 > t1)
            self.assertWahr(t1 <= t2)
            self.assertWahr(t2 >= t1)
            self.assertWahr(t1 != t2)
            self.assertWahr(t2 != t1)
            self.assertFalsch(t1 == t2)
            self.assertFalsch(t2 == t1)
            self.assertFalsch(t1 > t2)
            self.assertFalsch(t2 < t1)
            self.assertFalsch(t1 >= t2)
            self.assertFalsch(t2 <= t1)

        fuer badarg in OTHERSTUFF:
            self.assertEqual(t1 == badarg, Falsch)
            self.assertEqual(t1 != badarg, Wahr)
            self.assertEqual(badarg == t1, Falsch)
            self.assertEqual(badarg != t1, Wahr)

            self.assertRaises(TypeError, lambda: t1 <= badarg)
            self.assertRaises(TypeError, lambda: t1 < badarg)
            self.assertRaises(TypeError, lambda: t1 > badarg)
            self.assertRaises(TypeError, lambda: t1 >= badarg)
            self.assertRaises(TypeError, lambda: badarg <= t1)
            self.assertRaises(TypeError, lambda: badarg < t1)
            self.assertRaises(TypeError, lambda: badarg > t1)
            self.assertRaises(TypeError, lambda: badarg >= t1)

    def test_str(self):
        td = timedelta
        eq = self.assertEqual

        eq(str(td(1)), "1 day, 0:00:00")
        eq(str(td(-1)), "-1 day, 0:00:00")
        eq(str(td(2)), "2 days, 0:00:00")
        eq(str(td(-2)), "-2 days, 0:00:00")

        eq(str(td(hours=12, minutes=58, seconds=59)), "12:58:59")
        eq(str(td(hours=2, minutes=3, seconds=4)), "2:03:04")
        eq(str(td(weeks=-30, hours=23, minutes=12, seconds=34)),
           "-210 days, 23:12:34")

        eq(str(td(milliseconds=1)), "0:00:00.001000")
        eq(str(td(microseconds=3)), "0:00:00.000003")

        eq(str(td(days=999999999, hours=23, minutes=59, seconds=59,
                   microseconds=999999)),
           "999999999 days, 23:59:59.999999")

        # test the Doc/library/datetime.rst recipe
        eq(f'-({-td(hours=-1)!s})', "-(1:00:00)")

    def test_repr(self):
        name = 'datetime.' + self.theclass.__name__
        self.assertEqual(repr(self.theclass(1)),
                         "%s(days=1)" % name)
        self.assertEqual(repr(self.theclass(10, 2)),
                         "%s(days=10, seconds=2)" % name)
        self.assertEqual(repr(self.theclass(-10, 2, 400000)),
                         "%s(days=-10, seconds=2, microseconds=400000)" % name)
        self.assertEqual(repr(self.theclass(seconds=60)),
                         "%s(seconds=60)" % name)
        self.assertEqual(repr(self.theclass()),
                         "%s(0)" % name)
        self.assertEqual(repr(self.theclass(microseconds=100)),
                         "%s(microseconds=100)" % name)
        self.assertEqual(repr(self.theclass(days=1, microseconds=100)),
                         "%s(days=1, microseconds=100)" % name)
        self.assertEqual(repr(self.theclass(seconds=1, microseconds=100)),
                         "%s(seconds=1, microseconds=100)" % name)

    def test_repr_subclass(self):
        """Subclasses should have bare names in the repr (gh-107773)."""
        td = SubclassTimeDelta(days=1)
        self.assertEqual(repr(td), "SubclassTimeDelta(days=1)")
        td = SubclassTimeDelta(seconds=30)
        self.assertEqual(repr(td), "SubclassTimeDelta(seconds=30)")
        td = SubclassTimeDelta(weeks=2)
        self.assertEqual(repr(td), "SubclassTimeDelta(days=14)")

    def test_roundtrip(self):
        fuer td in (timedelta(days=999999999, hours=23, minutes=59,
                             seconds=59, microseconds=999999),
                   timedelta(days=-999999999),
                   timedelta(days=-999999999, seconds=1),
                   timedelta(days=1, seconds=2, microseconds=3)):

            # Verify td -> string -> td identity.
            s = repr(td)
            self.assertStartsWith(s, 'datetime.')
            s = s[9:]
            td2 = eval(s)
            self.assertEqual(td, td2)

            # Verify identity via reconstructing von pieces.
            td2 = timedelta(td.days, td.seconds, td.microseconds)
            self.assertEqual(td, td2)

    def test_resolution_info(self):
        self.assertIsInstance(timedelta.min, timedelta)
        self.assertIsInstance(timedelta.max, timedelta)
        self.assertIsInstance(timedelta.resolution, timedelta)
        self.assertWahr(timedelta.max > timedelta.min)
        self.assertEqual(timedelta.min, timedelta(-999999999))
        self.assertEqual(timedelta.max, timedelta(999999999, 24*3600-1, 1e6-1))
        self.assertEqual(timedelta.resolution, timedelta(0, 0, 1))

    def test_overflow(self):
        tiny = timedelta.resolution

        td = timedelta.min + tiny
        td -= tiny  # no problem
        self.assertRaises(OverflowError, td.__sub__, tiny)
        self.assertRaises(OverflowError, td.__add__, -tiny)

        td = timedelta.max - tiny
        td += tiny  # no problem
        self.assertRaises(OverflowError, td.__add__, tiny)
        self.assertRaises(OverflowError, td.__sub__, -tiny)

        self.assertRaises(OverflowError, lambda: -timedelta.max)

        day = timedelta(1)
        self.assertRaises(OverflowError, day.__mul__, 10**9)
        self.assertRaises(OverflowError, day.__mul__, 1e9)
        self.assertRaises(OverflowError, day.__truediv__, 1e-20)
        self.assertRaises(OverflowError, day.__truediv__, 1e-10)
        self.assertRaises(OverflowError, day.__truediv__, 9e-10)

    @support.requires_IEEE_754
    def _test_overflow_special(self):
        day = timedelta(1)
        self.assertRaises(OverflowError, day.__mul__, INF)
        self.assertRaises(OverflowError, day.__mul__, -INF)

    def test_microsecond_rounding(self):
        td = timedelta
        eq = self.assertEqual

        # Single-field rounding.
        eq(td(milliseconds=0.4/1000), td(0))    # rounds to 0
        eq(td(milliseconds=-0.4/1000), td(0))    # rounds to 0
        eq(td(milliseconds=0.5/1000), td(microseconds=0))
        eq(td(milliseconds=-0.5/1000), td(microseconds=-0))
        eq(td(milliseconds=0.6/1000), td(microseconds=1))
        eq(td(milliseconds=-0.6/1000), td(microseconds=-1))
        eq(td(milliseconds=1.5/1000), td(microseconds=2))
        eq(td(milliseconds=-1.5/1000), td(microseconds=-2))
        eq(td(seconds=0.5/10**6), td(microseconds=0))
        eq(td(seconds=-0.5/10**6), td(microseconds=-0))
        eq(td(seconds=1/2**7), td(microseconds=7812))
        eq(td(seconds=-1/2**7), td(microseconds=-7812))

        # Rounding due to contributions von more than one field.
        us_per_hour = 3600e6
        us_per_day = us_per_hour * 24
        eq(td(days=.4/us_per_day), td(0))
        eq(td(hours=.2/us_per_hour), td(0))
        eq(td(days=.4/us_per_day, hours=.2/us_per_hour), td(microseconds=1))

        eq(td(days=-.4/us_per_day), td(0))
        eq(td(hours=-.2/us_per_hour), td(0))
        eq(td(days=-.4/us_per_day, hours=-.2/us_per_hour), td(microseconds=-1))

        # Test fuer a patch in Issue 8860
        eq(td(microseconds=0.5), 0.5*td(microseconds=1.0))
        eq(td(microseconds=0.5)//td.resolution, 0.5*td.resolution//td.resolution)

    def test_massive_normalization(self):
        td = timedelta(microseconds=-1)
        self.assertEqual((td.days, td.seconds, td.microseconds),
                         (-1, 24*3600-1, 999999))

    def test_bool(self):
        self.assertWahr(timedelta(1))
        self.assertWahr(timedelta(0, 1))
        self.assertWahr(timedelta(0, 0, 1))
        self.assertWahr(timedelta(microseconds=1))
        self.assertFalsch(timedelta(0))

    def test_subclass_timedelta(self):

        klasse T(timedelta):
            @staticmethod
            def from_td(td):
                gib T(td.days, td.seconds, td.microseconds)

            def as_hours(self):
                sum = (self.days * 24 +
                       self.seconds / 3600.0 +
                       self.microseconds / 3600e6)
                gib round(sum)

        t1 = T(days=1)
        self.assertIs(type(t1), T)
        self.assertEqual(t1.as_hours(), 24)

        t2 = T(days=-1, seconds=-3600)
        self.assertIs(type(t2), T)
        self.assertEqual(t2.as_hours(), -25)

        t3 = t1 + t2
        self.assertIs(type(t3), timedelta)
        t4 = T.from_td(t3)
        self.assertIs(type(t4), T)
        self.assertEqual(t3.days, t4.days)
        self.assertEqual(t3.seconds, t4.seconds)
        self.assertEqual(t3.microseconds, t4.microseconds)
        self.assertEqual(str(t3), str(t4))
        self.assertEqual(t4.as_hours(), -1)

    def test_subclass_date(self):
        klasse DateSubclass(date):
            pass

        d1 = DateSubclass(2018, 1, 5)
        td = timedelta(days=1)

        tests = [
            ('add', lambda d, t: d + t, DateSubclass(2018, 1, 6)),
            ('radd', lambda d, t: t + d, DateSubclass(2018, 1, 6)),
            ('sub', lambda d, t: d - t, DateSubclass(2018, 1, 4)),
        ]

        fuer name, func, expected in tests:
            mit self.subTest(name):
                act = func(d1, td)
                self.assertEqual(act, expected)
                self.assertIsInstance(act, DateSubclass)

    def test_subclass_datetime(self):
        klasse DateTimeSubclass(datetime):
            pass

        d1 = DateTimeSubclass(2018, 1, 5, 12, 30)
        td = timedelta(days=1, minutes=30)

        tests = [
            ('add', lambda d, t: d + t, DateTimeSubclass(2018, 1, 6, 13)),
            ('radd', lambda d, t: t + d, DateTimeSubclass(2018, 1, 6, 13)),
            ('sub', lambda d, t: d - t, DateTimeSubclass(2018, 1, 4, 12)),
        ]

        fuer name, func, expected in tests:
            mit self.subTest(name):
                act = func(d1, td)
                self.assertEqual(act, expected)
                self.assertIsInstance(act, DateTimeSubclass)

    def test_division(self):
        t = timedelta(hours=1, minutes=24, seconds=19)
        second = timedelta(seconds=1)
        self.assertEqual(t / second, 5059.0)
        self.assertEqual(t // second, 5059)

        t = timedelta(minutes=2, seconds=30)
        minute = timedelta(minutes=1)
        self.assertEqual(t / minute, 2.5)
        self.assertEqual(t // minute, 2)

        zerotd = timedelta(0)
        self.assertRaises(ZeroDivisionError, truediv, t, zerotd)
        self.assertRaises(ZeroDivisionError, floordiv, t, zerotd)

        # self.assertRaises(TypeError, truediv, t, 2)
        # note: floor division of a timedelta by an integer *is*
        # currently permitted.

    def test_remainder(self):
        t = timedelta(minutes=2, seconds=30)
        minute = timedelta(minutes=1)
        r = t % minute
        self.assertEqual(r, timedelta(seconds=30))

        t = timedelta(minutes=-2, seconds=30)
        r = t %  minute
        self.assertEqual(r, timedelta(seconds=30))

        zerotd = timedelta(0)
        self.assertRaises(ZeroDivisionError, mod, t, zerotd)

        self.assertRaises(TypeError, mod, t, 10)

    def test_divmod(self):
        t = timedelta(minutes=2, seconds=30)
        minute = timedelta(minutes=1)
        q, r = divmod(t, minute)
        self.assertEqual(q, 2)
        self.assertEqual(r, timedelta(seconds=30))

        t = timedelta(minutes=-2, seconds=30)
        q, r = divmod(t, minute)
        self.assertEqual(q, -2)
        self.assertEqual(r, timedelta(seconds=30))

        zerotd = timedelta(0)
        self.assertRaises(ZeroDivisionError, divmod, t, zerotd)

        self.assertRaises(TypeError, divmod, t, 10)

    def test_issue31293(self):
        # The interpreter shouldn't crash in case a timedelta ist divided oder
        # multiplied by a float mit a bad as_integer_ratio() method.
        def get_bad_float(bad_ratio):
            klasse BadFloat(float):
                def as_integer_ratio(self):
                    gib bad_ratio
            gib BadFloat()

        mit self.assertRaises(TypeError):
            timedelta() / get_bad_float(1 << 1000)
        mit self.assertRaises(TypeError):
            timedelta() * get_bad_float(1 << 1000)

        fuer bad_ratio in [(), (42, ), (1, 2, 3)]:
            mit self.assertRaises(ValueError):
                timedelta() / get_bad_float(bad_ratio)
            mit self.assertRaises(ValueError):
                timedelta() * get_bad_float(bad_ratio)

    def test_issue31752(self):
        # The interpreter shouldn't crash because divmod() returns negative
        # remainder.
        klasse BadInt(int):
            def __mul__(self, other):
                gib Prod()
            def __rmul__(self, other):
                gib Prod()
            def __floordiv__(self, other):
                gib Prod()
            def __rfloordiv__(self, other):
                gib Prod()

        klasse Prod:
            def __add__(self, other):
                gib Sum()
            def __radd__(self, other):
                gib Sum()

        klasse Sum(int):
            def __divmod__(self, other):
                gib divmodresult

        fuer divmodresult in [Nichts, (), (0, 1, 2), (0, -1)]:
            mit self.subTest(divmodresult=divmodresult):
                # The following examples should nicht crash.
                versuch:
                    timedelta(microseconds=BadInt(1))
                ausser TypeError:
                    pass
                versuch:
                    timedelta(hours=BadInt(1))
                ausser TypeError:
                    pass
                versuch:
                    timedelta(weeks=BadInt(1))
                ausser (TypeError, ValueError):
                    pass
                versuch:
                    timedelta(1) * BadInt(1)
                ausser (TypeError, ValueError):
                    pass
                versuch:
                    BadInt(1) * timedelta(1)
                ausser TypeError:
                    pass
                versuch:
                    timedelta(1) // BadInt(1)
                ausser TypeError:
                    pass


#############################################################################
# date tests

klasse TestDateOnly(unittest.TestCase):
    # Tests here won't pass wenn also run on datetime objects, so don't
    # subclass this to test datetimes too.

    def test_delta_non_days_ignored(self):
        dt = date(2000, 1, 2)
        delta = timedelta(days=1, hours=2, minutes=3, seconds=4,
                          microseconds=5)
        days = timedelta(delta.days)
        self.assertEqual(days, timedelta(1))

        dt2 = dt + delta
        self.assertEqual(dt2, dt + days)

        dt2 = delta + dt
        self.assertEqual(dt2, dt + days)

        dt2 = dt - delta
        self.assertEqual(dt2, dt - days)

        delta = -delta
        days = timedelta(delta.days)
        self.assertEqual(days, timedelta(-2))

        dt2 = dt + delta
        self.assertEqual(dt2, dt + days)

        dt2 = delta + dt
        self.assertEqual(dt2, dt + days)

        dt2 = dt - delta
        self.assertEqual(dt2, dt - days)

    def test_strptime(self):
        inputs = [
            # Basic valid cases
            (date(1998, 2, 3), '1998-02-03', '%Y-%m-%d'),
            (date(2004, 12, 2), '2004-12-02', '%Y-%m-%d'),

            # Edge cases: Leap year
            (date(2020, 2, 29), '2020-02-29', '%Y-%m-%d'),  # Valid leap year date

            # bpo-34482: Handle surrogate pairs
            (date(2004, 12, 2), '2004-12\ud80002', '%Y-%m\ud800%d'),
            (date(2004, 12, 2), '2004\ud80012-02', '%Y\ud800%m-%d'),

            # Month/day variations
            (date(2004, 2, 1), '2004-02', '%Y-%m'),  # No day provided
            (date(2004, 2, 1), '02-2004', '%m-%Y'),  # Month und year swapped

            # Different day-month-year formats
            (date(2004, 12, 2), '02/12/2004', '%d/%m/%Y'),  # Day/Month/Year
            (date(2004, 12, 2), '12/02/2004', '%m/%d/%Y'),  # Month/Day/Year

            # Different separators
            (date(2023, 9, 24), '24.09.2023', '%d.%m.%Y'),  # Dots als separators
            (date(2023, 9, 24), '24-09-2023', '%d-%m-%Y'),  # Dashes
            (date(2023, 9, 24), '2023/09/24', '%Y/%m/%d'),  # Slashes

            # Handling years mit fewer digits
            (date(127, 2, 3), '0127-02-03', '%Y-%m-%d'),
            (date(99, 2, 3), '0099-02-03', '%Y-%m-%d'),
            (date(5, 2, 3), '0005-02-03', '%Y-%m-%d'),

            # Variations on ISO 8601 format
            (date(2023, 9, 25), '2023-W39-1', '%G-W%V-%u'),  # ISO week date (Week 39, Monday)
            (date(2023, 9, 25), '2023-268', '%Y-%j'),  # Year und day of the year (Julian)
        ]
        fuer expected, string, format in inputs:
            mit self.subTest(string=string, format=format):
                got = date.strptime(string, format)
                self.assertEqual(expected, got)
                self.assertIs(type(got), date)

    def test_strptime_single_digit(self):
        # bpo-34903: Check that single digit dates are allowed.
        strptime = date.strptime
        mit self.assertRaises(ValueError):
            # %y does require two digits.
            newdate = strptime('01/02/3', '%d/%m/%y')

        d1 = date(2003, 2, 1)
        d2 = date(2003, 1, 2)
        d3 = date(2003, 1, 25)
        inputs = [
            ('%d', '1/02/03',  '%d/%m/%y', d1),
            ('%m', '01/2/03',  '%d/%m/%y', d1),
            ('%j', '2/03',     '%j/%y',    d2),
            ('%w', '6/04/03',  '%w/%U/%y', d1),
            # %u requires a single digit.
            ('%W', '6/4/2003', '%u/%W/%Y', d1),
            ('%V', '6/4/2003', '%u/%V/%G', d3),
        ]
        fuer reason, string, format, target in inputs:
            reason = 'test single digit ' + reason
            mit self.subTest(reason=reason,
                              string=string,
                              format=format,
                              target=target):
                newdate = strptime(string, format)
                self.assertEqual(newdate, target, msg=reason)

    @warnings_helper.ignore_warnings(category=DeprecationWarning)
    def test_strptime_leap_year(self):
        # GH-70647: warns wenn parsing a format mit a day und no year.
        mit self.assertRaises(ValueError):
            # The existing behavior that GH-70647 seeks to change.
            date.strptime('02-29', '%m-%d')
        mit self._assertNotWarns(DeprecationWarning):
            date.strptime('20-03-14', '%y-%m-%d')
            date.strptime('02-29,2024', '%m-%d,%Y')

klasse SubclassDate(date):
    sub_var = 1

klasse TestDate(HarmlessMixedComparison, unittest.TestCase):
    # Tests here should pass fuer both dates und datetimes, ausser fuer a
    # few tests that TestDateTime overrides.

    theclass = date

    def test_basic_attributes(self):
        dt = self.theclass(2002, 3, 1)
        self.assertEqual(dt.year, 2002)
        self.assertEqual(dt.month, 3)
        self.assertEqual(dt.day, 1)

    def test_roundtrip(self):
        fuer dt in (self.theclass(1, 2, 3),
                   self.theclass.today()):
            # Verify dt -> string -> date identity.
            s = repr(dt)
            self.assertStartsWith(s, 'datetime.')
            s = s[9:]
            dt2 = eval(s)
            self.assertEqual(dt, dt2)

            # Verify identity via reconstructing von pieces.
            dt2 = self.theclass(dt.year, dt.month, dt.day)
            self.assertEqual(dt, dt2)

    def test_repr_subclass(self):
        """Subclasses should have bare names in the repr (gh-107773)."""
        td = SubclassDate(1, 2, 3)
        self.assertEqual(repr(td), "SubclassDate(1, 2, 3)")
        td = SubclassDate(2014, 1, 1)
        self.assertEqual(repr(td), "SubclassDate(2014, 1, 1)")
        td = SubclassDate(2010, 10, day=10)
        self.assertEqual(repr(td), "SubclassDate(2010, 10, 10)")

    def test_ordinal_conversions(self):
        # Check some fixed values.
        fuer y, m, d, n in [(1, 1, 1, 1),      # calendar origin
                           (1, 12, 31, 365),
                           (2, 1, 1, 366),
                           # first example von "Calendrical Calculations"
                           (1945, 11, 12, 710347)]:
            d = self.theclass(y, m, d)
            self.assertEqual(n, d.toordinal())
            fromord = self.theclass.fromordinal(n)
            self.assertEqual(d, fromord)
            wenn hasattr(fromord, "hour"):
            # wenn we're checking something fancier than a date, verify
            # the extra fields have been zeroed out
                self.assertEqual(fromord.hour, 0)
                self.assertEqual(fromord.minute, 0)
                self.assertEqual(fromord.second, 0)
                self.assertEqual(fromord.microsecond, 0)

        # Check first und last days of year spottily across the whole
        # range of years supported.
        fuer year in range(MINYEAR, MAXYEAR+1, 7):
            # Verify (year, 1, 1) -> ordinal -> y, m, d ist identity.
            d = self.theclass(year, 1, 1)
            n = d.toordinal()
            d2 = self.theclass.fromordinal(n)
            self.assertEqual(d, d2)
            # Verify that moving back a day gets to the end of year-1.
            wenn year > 1:
                d = self.theclass.fromordinal(n-1)
                d2 = self.theclass(year-1, 12, 31)
                self.assertEqual(d, d2)
                self.assertEqual(d2.toordinal(), n-1)

        # Test every day in a leap-year und a non-leap year.
        dim = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
        fuer year, isleap in (2000, Wahr), (2002, Falsch):
            n = self.theclass(year, 1, 1).toordinal()
            fuer month, maxday in zip(range(1, 13), dim):
                wenn month == 2 und isleap:
                    maxday += 1
                fuer day in range(1, maxday+1):
                    d = self.theclass(year, month, day)
                    self.assertEqual(d.toordinal(), n)
                    self.assertEqual(d, self.theclass.fromordinal(n))
                    n += 1

    def test_extreme_ordinals(self):
        a = self.theclass.min
        a = self.theclass(a.year, a.month, a.day)  # get rid of time parts
        aord = a.toordinal()
        b = a.fromordinal(aord)
        self.assertEqual(a, b)

        self.assertRaises(ValueError, lambda: a.fromordinal(aord - 1))

        b = a + timedelta(days=1)
        self.assertEqual(b.toordinal(), aord + 1)
        self.assertEqual(b, self.theclass.fromordinal(aord + 1))

        a = self.theclass.max
        a = self.theclass(a.year, a.month, a.day)  # get rid of time parts
        aord = a.toordinal()
        b = a.fromordinal(aord)
        self.assertEqual(a, b)

        self.assertRaises(ValueError, lambda: a.fromordinal(aord + 1))

        b = a - timedelta(days=1)
        self.assertEqual(b.toordinal(), aord - 1)
        self.assertEqual(b, self.theclass.fromordinal(aord - 1))

    def test_bad_constructor_arguments(self):
        # bad years
        self.theclass(MINYEAR, 1, 1)  # no exception
        self.theclass(MAXYEAR, 1, 1)  # no exception
        self.assertRaises(ValueError, self.theclass, MINYEAR-1, 1, 1)
        self.assertRaises(ValueError, self.theclass, MAXYEAR+1, 1, 1)
        # bad months
        self.theclass(2000, 1, 1)    # no exception
        self.theclass(2000, 12, 1)   # no exception
        self.assertRaises(ValueError, self.theclass, 2000, 0, 1)
        self.assertRaises(ValueError, self.theclass, 2000, 13, 1)
        # bad days
        self.theclass(2000, 2, 29)   # no exception
        self.theclass(2004, 2, 29)   # no exception
        self.theclass(2400, 2, 29)   # no exception
        self.assertRaises(ValueError, self.theclass, 2000, 2, 30)
        self.assertRaises(ValueError, self.theclass, 2001, 2, 29)
        self.assertRaises(ValueError, self.theclass, 2100, 2, 29)
        self.assertRaises(ValueError, self.theclass, 1900, 2, 29)
        self.assertRaises(ValueError, self.theclass, 2000, 1, 0)
        self.assertRaises(ValueError, self.theclass, 2000, 1, 32)

    def test_hash_equality(self):
        d = self.theclass(2000, 12, 31)
        # same thing
        e = self.theclass(2000, 12, 31)
        self.assertEqual(d, e)
        self.assertEqual(hash(d), hash(e))

        dic = {d: 1}
        dic[e] = 2
        self.assertEqual(len(dic), 1)
        self.assertEqual(dic[d], 2)
        self.assertEqual(dic[e], 2)

        d = self.theclass(2001,  1,  1)
        # same thing
        e = self.theclass(2001,  1,  1)
        self.assertEqual(d, e)
        self.assertEqual(hash(d), hash(e))

        dic = {d: 1}
        dic[e] = 2
        self.assertEqual(len(dic), 1)
        self.assertEqual(dic[d], 2)
        self.assertEqual(dic[e], 2)

    def test_computations(self):
        a = self.theclass(2002, 1, 31)
        b = self.theclass(1956, 1, 31)
        c = self.theclass(2001,2,1)

        diff = a-b
        self.assertEqual(diff.days, 46*365 + len(range(1956, 2002, 4)))
        self.assertEqual(diff.seconds, 0)
        self.assertEqual(diff.microseconds, 0)

        day = timedelta(1)
        week = timedelta(7)
        a = self.theclass(2002, 3, 2)
        self.assertEqual(a + day, self.theclass(2002, 3, 3))
        self.assertEqual(day + a, self.theclass(2002, 3, 3))
        self.assertEqual(a - day, self.theclass(2002, 3, 1))
        self.assertEqual(-day + a, self.theclass(2002, 3, 1))
        self.assertEqual(a + week, self.theclass(2002, 3, 9))
        self.assertEqual(a - week, self.theclass(2002, 2, 23))
        self.assertEqual(a + 52*week, self.theclass(2003, 3, 1))
        self.assertEqual(a - 52*week, self.theclass(2001, 3, 3))
        self.assertEqual((a + week) - a, week)
        self.assertEqual((a + day) - a, day)
        self.assertEqual((a - week) - a, -week)
        self.assertEqual((a - day) - a, -day)
        self.assertEqual(a - (a + week), -week)
        self.assertEqual(a - (a + day), -day)
        self.assertEqual(a - (a - week), week)
        self.assertEqual(a - (a - day), day)
        self.assertEqual(c - (c - day), day)

        # Add/sub ints oder floats should be illegal
        fuer i in 1, 1.0:
            self.assertRaises(TypeError, lambda: a+i)
            self.assertRaises(TypeError, lambda: a-i)
            self.assertRaises(TypeError, lambda: i+a)
            self.assertRaises(TypeError, lambda: i-a)

        # delta - date ist senseless.
        self.assertRaises(TypeError, lambda: day - a)
        # mixing date und (delta oder date) via * oder // ist senseless
        self.assertRaises(TypeError, lambda: day * a)
        self.assertRaises(TypeError, lambda: a * day)
        self.assertRaises(TypeError, lambda: day // a)
        self.assertRaises(TypeError, lambda: a // day)
        self.assertRaises(TypeError, lambda: a * a)
        self.assertRaises(TypeError, lambda: a // a)
        # date + date ist senseless
        self.assertRaises(TypeError, lambda: a + a)

    def test_overflow(self):
        tiny = self.theclass.resolution

        fuer delta in [tiny, timedelta(1), timedelta(2)]:
            dt = self.theclass.min + delta
            dt -= delta  # no problem
            self.assertRaises(OverflowError, dt.__sub__, delta)
            self.assertRaises(OverflowError, dt.__add__, -delta)

            dt = self.theclass.max - delta
            dt += delta  # no problem
            self.assertRaises(OverflowError, dt.__add__, delta)
            self.assertRaises(OverflowError, dt.__sub__, -delta)

    def test_fromtimestamp(self):
        importiere time

        # Try an arbitrary fixed value.
        year, month, day = 1999, 9, 19
        ts = time.mktime((year, month, day, 0, 0, 0, 0, 0, -1))
        d = self.theclass.fromtimestamp(ts)
        self.assertEqual(d.year, year)
        self.assertEqual(d.month, month)
        self.assertEqual(d.day, day)

    def test_insane_fromtimestamp(self):
        # It's possible that some platform maps time_t to double,
        # und that this test will fail there.  This test should
        # exempt such platforms (provided they gib reasonable
        # results!).
        fuer insane in -1e200, 1e200:
            self.assertRaises(OverflowError, self.theclass.fromtimestamp,
                              insane)

    def test_fromtimestamp_with_none_arg(self):
        # See gh-120268 fuer more details
        mit self.assertRaises(TypeError):
            self.theclass.fromtimestamp(Nichts)

    def test_today(self):
        importiere time

        # We claim that today() ist like fromtimestamp(time.time()), so
        # prove it.
        fuer dummy in range(3):
            today = self.theclass.today()
            ts = time.time()
            todayagain = self.theclass.fromtimestamp(ts)
            wenn today == todayagain:
                breche
            # There are several legit reasons that could fail:
            # 1. It recently became midnight, between the today() und the
            #    time() calls.
            # 2. The platform time() has such fine resolution that we'll
            #    never get the same value twice.
            # 3. The platform time() has poor resolution, und we just
            #    happened to call today() right before a resolution quantum
            #    boundary.
            # 4. The system clock got fiddled between calls.
            # In any case, wait a little waehrend und try again.
            time.sleep(0.1)

        # It worked oder it didn't.  If it didn't, assume it's reason #2, und
        # let the test pass wenn they're within half a second of each other.
        wenn today != todayagain:
            self.assertAlmostEqual(todayagain, today,
                                   delta=timedelta(seconds=0.5))

    def test_weekday(self):
        fuer i in range(7):
            # March 4, 2002 ist a Monday
            self.assertEqual(self.theclass(2002, 3, 4+i).weekday(), i)
            self.assertEqual(self.theclass(2002, 3, 4+i).isoweekday(), i+1)
            # January 2, 1956 ist a Monday
            self.assertEqual(self.theclass(1956, 1, 2+i).weekday(), i)
            self.assertEqual(self.theclass(1956, 1, 2+i).isoweekday(), i+1)

    def test_isocalendar(self):
        # Check examples from
        # http://www.phys.uu.nl/~vgent/calendar/isocalendar.htm
        week_mondays = [
                ((2003, 12, 22), (2003, 52, 1)),
                ((2003, 12, 29), (2004, 1, 1)),
                ((2004, 1, 5), (2004, 2, 1)),
                ((2009, 12, 21), (2009, 52, 1)),
                ((2009, 12, 28), (2009, 53, 1)),
                ((2010, 1, 4), (2010, 1, 1)),
        ]

        test_cases = []
        fuer cal_date, iso_date in week_mondays:
            base_date = self.theclass(*cal_date)
            # Adds one test case fuer every day of the specified weeks
            fuer i in range(7):
                new_date = base_date + timedelta(i)
                new_iso = iso_date[0:2] + (iso_date[2] + i,)
                test_cases.append((new_date, new_iso))

        fuer d, exp_iso in test_cases:
            mit self.subTest(d=d, comparison="tuple"):
                self.assertEqual(d.isocalendar(), exp_iso)

            # Check that the tuple contents are accessible by field name
            mit self.subTest(d=d, comparison="fields"):
                t = d.isocalendar()
                self.assertEqual((t.year, t.week, t.weekday), exp_iso)

    def test_isocalendar_pickling(self):
        """Test that the result of datetime.isocalendar() can be pickled.

        The result of a round trip should be a plain tuple.
        """
        d = self.theclass(2019, 1, 1)
        p = pickle.dumps(d.isocalendar())
        res = pickle.loads(p)
        self.assertEqual(type(res), tuple)
        self.assertEqual(res, (2019, 1, 2))

    def test_iso_long_years(self):
        # Calculate long ISO years und compare to table from
        # http://www.phys.uu.nl/~vgent/calendar/isocalendar.htm
        ISO_LONG_YEARS_TABLE = """
              4   32   60   88
              9   37   65   93
             15   43   71   99
             20   48   76
             26   54   82

            105  133  161  189
            111  139  167  195
            116  144  172
            122  150  178
            128  156  184

            201  229  257  285
            207  235  263  291
            212  240  268  296
            218  246  274
            224  252  280

            303  331  359  387
            308  336  364  392
            314  342  370  398
            320  348  376
            325  353  381
        """
        iso_long_years = sorted(map(int, ISO_LONG_YEARS_TABLE.split()))
        L = []
        fuer i in range(400):
            d = self.theclass(2000+i, 12, 31)
            d1 = self.theclass(1600+i, 12, 31)
            self.assertEqual(d.isocalendar()[1:], d1.isocalendar()[1:])
            wenn d.isocalendar()[1] == 53:
                L.append(i)
        self.assertEqual(L, iso_long_years)

    def test_isoformat(self):
        t = self.theclass(2, 3, 2)
        self.assertEqual(t.isoformat(), "0002-03-02")

    def test_ctime(self):
        t = self.theclass(2002, 3, 2)
        self.assertEqual(t.ctime(), "Sat Mar  2 00:00:00 2002")

    def test_strftime(self):
        t = self.theclass(2005, 3, 2)
        self.assertEqual(t.strftime("m:%m d:%d y:%y"), "m:03 d:02 y:05")
        self.assertEqual(t.strftime(""), "") # SF bug #761337
        self.assertEqual(t.strftime('x'*1000), 'x'*1000) # SF bug #1556784

        self.assertRaises(TypeError, t.strftime) # needs an arg
        self.assertRaises(TypeError, t.strftime, "one", "two") # too many args
        self.assertRaises(TypeError, t.strftime, 42) # arg wrong type

        # test that unicode input ist allowed (issue 2782)
        self.assertEqual(t.strftime("%m"), "03")

        # A naive object replaces %z, %:z und %Z w/ empty strings.
        self.assertEqual(t.strftime("'%z' '%:z' '%Z'"), "'' '' ''")

        #make sure that invalid format specifiers are handled correctly
        #self.assertRaises(ValueError, t.strftime, "%e")
        #self.assertRaises(ValueError, t.strftime, "%")
        #self.assertRaises(ValueError, t.strftime, "%#")

        #oh well, some systems just ignore those invalid ones.
        #at least, exercise them to make sure that no crashes
        #are generated
        fuer f in ["%e", "%", "%#"]:
            versuch:
                t.strftime(f)
            ausser ValueError:
                pass

        # bpo-34482: Check that surrogates don't cause a crash.
        versuch:
            t.strftime('%y\ud800%m')
        ausser UnicodeEncodeError:
            pass

        #check that this standard extension works
        t.strftime("%f")

        # bpo-41260: The parameter was named "fmt" in the pure python impl.
        t.strftime(format="%f")

    def test_strftime_trailing_percent(self):
        # bpo-35066: Make sure trailing '%' doesn't cause datetime's strftime to
        # complain. Different libcs have different handling of trailing
        # percents, so we simply check datetime's strftime acts the same as
        # time.strftime.
        t = self.theclass(2005, 3, 2)
        versuch:
            _time.strftime('%')
        ausser ValueError:
            self.skipTest('time module does nicht support trailing %')
        self.assertEqual(t.strftime('%'), _time.strftime('%', t.timetuple()))
        self.assertEqual(
            t.strftime("m:%m d:%d y:%y %"),
            _time.strftime("m:03 d:02 y:05 %", t.timetuple()),
        )

    def test_format(self):
        dt = self.theclass(2007, 9, 10)
        self.assertEqual(dt.__format__(''), str(dt))

        mit self.assertRaisesRegex(TypeError, 'must be str, nicht int'):
            dt.__format__(123)

        # check that a derived class's __str__() gets called
        klasse A(self.theclass):
            def __str__(self):
                gib 'A'
        a = A(2007, 9, 10)
        self.assertEqual(a.__format__(''), 'A')

        # check that a derived class's strftime gets called
        klasse B(self.theclass):
            def strftime(self, format_spec):
                gib 'B'
        b = B(2007, 9, 10)
        self.assertEqual(b.__format__(''), str(dt))

        fuer fmt in ["m:%m d:%d y:%y",
                    "m:%m d:%d y:%y H:%H M:%M S:%S",
                    "%z %:z %Z",
                    ]:
            self.assertEqual(dt.__format__(fmt), dt.strftime(fmt))
            self.assertEqual(a.__format__(fmt), dt.strftime(fmt))
            self.assertEqual(b.__format__(fmt), 'B')

    def test_resolution_info(self):
        # XXX: Should min und max respect subclassing?
        wenn issubclass(self.theclass, datetime):
            expected_class = datetime
        sonst:
            expected_class = date
        self.assertIsInstance(self.theclass.min, expected_class)
        self.assertIsInstance(self.theclass.max, expected_class)
        self.assertIsInstance(self.theclass.resolution, timedelta)
        self.assertWahr(self.theclass.max > self.theclass.min)

    def test_extreme_timedelta(self):
        big = self.theclass.max - self.theclass.min
        # 3652058 days, 23 hours, 59 minutes, 59 seconds, 999999 microseconds
        n = (big.days*24*3600 + big.seconds)*1000000 + big.microseconds
        # n == 315537897599999999 ~= 2**58.13
        justasbig = timedelta(0, 0, n)
        self.assertEqual(big, justasbig)
        self.assertEqual(self.theclass.min + big, self.theclass.max)
        self.assertEqual(self.theclass.max - big, self.theclass.min)

    def test_timetuple(self):
        fuer i in range(7):
            # January 2, 1956 ist a Monday (0)
            d = self.theclass(1956, 1, 2+i)
            t = d.timetuple()
            self.assertEqual(t, (1956, 1, 2+i, 0, 0, 0, i, 2+i, -1))
            # February 1, 1956 ist a Wednesday (2)
            d = self.theclass(1956, 2, 1+i)
            t = d.timetuple()
            self.assertEqual(t, (1956, 2, 1+i, 0, 0, 0, (2+i)%7, 32+i, -1))
            # March 1, 1956 ist a Thursday (3), und ist the 31+29+1 = 61st day
            # of the year.
            d = self.theclass(1956, 3, 1+i)
            t = d.timetuple()
            self.assertEqual(t, (1956, 3, 1+i, 0, 0, 0, (3+i)%7, 61+i, -1))
            self.assertEqual(t.tm_year, 1956)
            self.assertEqual(t.tm_mon, 3)
            self.assertEqual(t.tm_mday, 1+i)
            self.assertEqual(t.tm_hour, 0)
            self.assertEqual(t.tm_min, 0)
            self.assertEqual(t.tm_sec, 0)
            self.assertEqual(t.tm_wday, (3+i)%7)
            self.assertEqual(t.tm_yday, 61+i)
            self.assertEqual(t.tm_isdst, -1)

    def test_pickling(self):
        args = 6, 7, 23
        orig = self.theclass(*args)
        fuer pickler, unpickler, proto in pickle_choices:
            green = pickler.dumps(orig, proto)
            derived = unpickler.loads(green)
            self.assertEqual(orig, derived)
        self.assertEqual(orig.__reduce__(), orig.__reduce_ex__(2))

    def test_compat_unpickle(self):
        tests = [
            b"cdatetime\ndate\n(S'\\x07\\xdf\\x0b\\x1b'\ntR.",
            b'cdatetime\ndate\n(U\x04\x07\xdf\x0b\x1btR.',
            b'\x80\x02cdatetime\ndate\nU\x04\x07\xdf\x0b\x1b\x85R.',
        ]
        args = 2015, 11, 27
        expected = self.theclass(*args)
        fuer data in tests:
            fuer loads in pickle_loads:
                derived = loads(data, encoding='latin1')
                self.assertEqual(derived, expected)

    def test_compare(self):
        t1 = self.theclass(2, 3, 4)
        t2 = self.theclass(2, 3, 4)
        self.assertEqual(t1, t2)
        self.assertWahr(t1 <= t2)
        self.assertWahr(t1 >= t2)
        self.assertFalsch(t1 != t2)
        self.assertFalsch(t1 < t2)
        self.assertFalsch(t1 > t2)

        fuer args in (3, 3, 3), (2, 4, 4), (2, 3, 5):
            t2 = self.theclass(*args)   # this ist larger than t1
            self.assertWahr(t1 < t2)
            self.assertWahr(t2 > t1)
            self.assertWahr(t1 <= t2)
            self.assertWahr(t2 >= t1)
            self.assertWahr(t1 != t2)
            self.assertWahr(t2 != t1)
            self.assertFalsch(t1 == t2)
            self.assertFalsch(t2 == t1)
            self.assertFalsch(t1 > t2)
            self.assertFalsch(t2 < t1)
            self.assertFalsch(t1 >= t2)
            self.assertFalsch(t2 <= t1)

        fuer badarg in OTHERSTUFF:
            self.assertEqual(t1 == badarg, Falsch)
            self.assertEqual(t1 != badarg, Wahr)
            self.assertEqual(badarg == t1, Falsch)
            self.assertEqual(badarg != t1, Wahr)

            self.assertRaises(TypeError, lambda: t1 < badarg)
            self.assertRaises(TypeError, lambda: t1 > badarg)
            self.assertRaises(TypeError, lambda: t1 >= badarg)
            self.assertRaises(TypeError, lambda: badarg <= t1)
            self.assertRaises(TypeError, lambda: badarg < t1)
            self.assertRaises(TypeError, lambda: badarg > t1)
            self.assertRaises(TypeError, lambda: badarg >= t1)

    def test_mixed_compare(self):
        our = self.theclass(2000, 4, 5)

        # Our klasse can be compared fuer equality to other classes
        self.assertEqual(our == 1, Falsch)
        self.assertEqual(1 == our, Falsch)
        self.assertEqual(our != 1, Wahr)
        self.assertEqual(1 != our, Wahr)

        # But the ordering ist undefined
        self.assertRaises(TypeError, lambda: our < 1)
        self.assertRaises(TypeError, lambda: 1 < our)

        # Repeat those tests mit a different class

        klasse SomeClass:
            pass

        their = SomeClass()
        self.assertEqual(our == their, Falsch)
        self.assertEqual(their == our, Falsch)
        self.assertEqual(our != their, Wahr)
        self.assertEqual(their != our, Wahr)
        self.assertRaises(TypeError, lambda: our < their)
        self.assertRaises(TypeError, lambda: their < our)

    def test_bool(self):
        # All dates are considered true.
        self.assertWahr(self.theclass.min)
        self.assertWahr(self.theclass.max)

    def check_strftime_y2k(self, specifier):
        # Test that years less than 1000 are 0-padded; note that the beginning
        # of an ISO 8601 year may fall in an ISO week of the year before, und
        # therefore needs an offset of -1 when formatting mit '%G'.
        dataset = (
            (1, 0),
            (49, -1),
            (70, 0),
            (99, 0),
            (100, -1),
            (999, 0),
            (1000, 0),
            (1970, 0),
        )
        fuer year, g_offset in dataset:
            mit self.subTest(year=year, specifier=specifier):
                d = self.theclass(year, 1, 1)
                wenn specifier == 'G':
                    year += g_offset
                wenn specifier == 'C':
                    expected = f"{year // 100:02d}"
                sonst:
                    expected = f"{year:04d}"
                    wenn specifier == 'F':
                        expected += f"-01-01"
                self.assertEqual(d.strftime(f"%{specifier}"), expected)

    def test_strftime_y2k(self):
        self.check_strftime_y2k('Y')
        self.check_strftime_y2k('G')

    def test_strftime_y2k_c99(self):
        # CPython requires C11; specifiers new in C99 must work.
        # (Other implementations may want to disable this test.)
        self.check_strftime_y2k('F')
        self.check_strftime_y2k('C')

    def test_replace(self):
        cls = self.theclass
        args = [1, 2, 3]
        base = cls(*args)
        self.assertEqual(base.replace(), base)
        self.assertEqual(copy.replace(base), base)

        changes = (("year", 2),
                   ("month", 3),
                   ("day", 4))
        fuer i, (name, newval) in enumerate(changes):
            newargs = args[:]
            newargs[i] = newval
            expected = cls(*newargs)
            self.assertEqual(base.replace(**{name: newval}), expected)
            self.assertEqual(copy.replace(base, **{name: newval}), expected)

        # Out of bounds.
        base = cls(2000, 2, 29)
        self.assertRaises(ValueError, base.replace, year=2001)
        self.assertRaises(ValueError, copy.replace, base, year=2001)

    def test_subclass_replace(self):
        klasse DateSubclass(self.theclass):
            def __new__(cls, *args, **kwargs):
                result = self.theclass.__new__(cls, *args, **kwargs)
                result.extra = 7
                gib result

        dt = DateSubclass(2012, 1, 1)

        test_cases = [
            ('self.replace', dt.replace(year=2013)),
            ('copy.replace', copy.replace(dt, year=2013)),
        ]

        fuer name, res in test_cases:
            mit self.subTest(name):
                self.assertIs(type(res), DateSubclass)
                self.assertEqual(res.year, 2013)
                self.assertEqual(res.month, 1)
                self.assertEqual(res.extra, 7)

    def test_subclass_date(self):

        klasse C(self.theclass):
            theAnswer = 42

            def __new__(cls, *args, **kws):
                temp = kws.copy()
                extra = temp.pop('extra')
                result = self.theclass.__new__(cls, *args, **temp)
                result.extra = extra
                gib result

            def newmeth(self, start):
                gib start + self.year + self.month

        args = 2003, 4, 14

        dt1 = self.theclass(*args)
        dt2 = C(*args, **{'extra': 7})

        self.assertEqual(dt2.__class__, C)
        self.assertEqual(dt2.theAnswer, 42)
        self.assertEqual(dt2.extra, 7)
        self.assertEqual(dt1.toordinal(), dt2.toordinal())
        self.assertEqual(dt2.newmeth(-7), dt1.year + dt1.month - 7)

    def test_subclass_alternate_constructors(self):
        # Test that alternate constructors call the constructor
        klasse DateSubclass(self.theclass):
            def __new__(cls, *args, **kwargs):
                result = self.theclass.__new__(cls, *args, **kwargs)
                result.extra = 7

                gib result

        args = (2003, 4, 14)
        d_ord = 731319              # Equivalent ordinal date
        d_isoformat = '2003-04-14'  # Equivalent isoformat()

        base_d = DateSubclass(*args)
        self.assertIsInstance(base_d, DateSubclass)
        self.assertEqual(base_d.extra, 7)

        # Timestamp depends on time zone, so we'll calculate the equivalent here
        ts = datetime.combine(base_d, time(0)).timestamp()

        test_cases = [
            ('fromordinal', (d_ord,)),
            ('fromtimestamp', (ts,)),
            ('fromisoformat', (d_isoformat,)),
        ]

        fuer constr_name, constr_args in test_cases:
            fuer base_obj in (DateSubclass, base_d):
                # Test both the classmethod und method
                mit self.subTest(base_obj_type=type(base_obj),
                                  constr_name=constr_name):
                    constr = getattr(base_obj, constr_name)

                    dt = constr(*constr_args)

                    # Test that it creates the right subclass
                    self.assertIsInstance(dt, DateSubclass)

                    # Test that it's equal to the base object
                    self.assertEqual(dt, base_d)

                    # Test that it called the constructor
                    self.assertEqual(dt.extra, 7)

    def test_pickling_subclass_date(self):

        args = 6, 7, 23
        orig = SubclassDate(*args)
        fuer pickler, unpickler, proto in pickle_choices:
            green = pickler.dumps(orig, proto)
            derived = unpickler.loads(green)
            self.assertEqual(orig, derived)
            self.assertWahr(isinstance(derived, SubclassDate))

    def test_backdoor_resistance(self):
        # For fast unpickling, the constructor accepts a pickle byte string.
        # This ist a low-overhead backdoor.  A user can (by intent oder
        # mistake) pass a string directly, which (if it's the right length)
        # will get treated like a pickle, und bypass the normal sanity
        # checks in the constructor.  This can create insane objects.
        # The constructor doesn't want to burn the time to validate all
        # fields, but does check the month field.  This stops, e.g.,
        # datetime.datetime('1995-03-25') von yielding an insane object.
        base = b'1995-03-25'
        wenn nicht issubclass(self.theclass, datetime):
            base = base[:4]
        fuer month_byte in b'9', b'\0', b'\r', b'\xff':
            self.assertRaises(TypeError, self.theclass,
                                         base[:2] + month_byte + base[3:])
        wenn issubclass(self.theclass, datetime):
            # Good bytes, but bad tzinfo:
            mit self.assertRaisesRegex(TypeError, '^bad tzinfo state arg$'):
                self.theclass(bytes([1] * len(base)), 'EST')

        fuer ord_byte in range(1, 13):
            # This shouldn't blow up because of the month byte alone.  If
            # the implementation changes to do more-careful checking, it may
            # blow up because other fields are insane.
            self.theclass(base[:2] + bytes([ord_byte]) + base[3:])

    def test_valuerror_messages(self):
        pattern = re.compile(
            r"(year|month|day) must be in \d+\.\.\d+, nicht \d+"
        )
        test_cases = [
            (2009, 13, 1),      # Month out of range
            (2009, 0, 1),       # Month out of range
            (10000, 12, 31),    # Year out of range
            (0, 12, 31),        # Year out of range
        ]
        fuer case in test_cases:
            mit self.subTest(case):
                mit self.assertRaisesRegex(ValueError, pattern):
                    self.theclass(*case)

        # days out of range have their own error message, see issue 70647
        mit self.assertRaises(ValueError) als msg:
            self.theclass(2009, 1, 32)
        self.assertIn(f"day 32 must be in range 1..31 fuer month 1 in year 2009", str(msg.exception))

    def test_fromisoformat(self):
        # Test that isoformat() ist reversible
        base_dates = [
            (1, 1, 1),
            (1000, 2, 14),
            (1900, 1, 1),
            (2000, 2, 29),
            (2004, 11, 12),
            (2004, 4, 3),
            (2017, 5, 30)
        ]

        fuer dt_tuple in base_dates:
            dt = self.theclass(*dt_tuple)
            dt_str = dt.isoformat()
            mit self.subTest(dt_str=dt_str):
                dt_rt = self.theclass.fromisoformat(dt.isoformat())

                self.assertEqual(dt, dt_rt)

    def test_fromisoformat_date_examples(self):
        examples = [
            ('00010101', self.theclass(1, 1, 1)),
            ('20000101', self.theclass(2000, 1, 1)),
            ('20250102', self.theclass(2025, 1, 2)),
            ('99991231', self.theclass(9999, 12, 31)),
            ('0001-01-01', self.theclass(1, 1, 1)),
            ('2000-01-01', self.theclass(2000, 1, 1)),
            ('2025-01-02', self.theclass(2025, 1, 2)),
            ('9999-12-31', self.theclass(9999, 12, 31)),
            ('2025W01', self.theclass(2024, 12, 30)),
            ('2025-W01', self.theclass(2024, 12, 30)),
            ('2025W014', self.theclass(2025, 1, 2)),
            ('2025-W01-4', self.theclass(2025, 1, 2)),
            ('2026W01', self.theclass(2025, 12, 29)),
            ('2026-W01', self.theclass(2025, 12, 29)),
            ('2026W013', self.theclass(2025, 12, 31)),
            ('2026-W01-3', self.theclass(2025, 12, 31)),
            ('2022W52', self.theclass(2022, 12, 26)),
            ('2022-W52', self.theclass(2022, 12, 26)),
            ('2022W527', self.theclass(2023, 1, 1)),
            ('2022-W52-7', self.theclass(2023, 1, 1)),
            ('2015W534', self.theclass(2015, 12, 31)),      # Has week 53
            ('2015-W53-4', self.theclass(2015, 12, 31)),    # Has week 53
            ('2015-W53-5', self.theclass(2016, 1, 1)),
            ('2020W531', self.theclass(2020, 12, 28)),      # Leap year
            ('2020-W53-1', self.theclass(2020, 12, 28)),    # Leap year
            ('2020-W53-6', self.theclass(2021, 1, 2)),
        ]

        fuer input_str, expected in examples:
            mit self.subTest(input_str=input_str):
                actual = self.theclass.fromisoformat(input_str)
                self.assertEqual(actual, expected)

    def test_fromisoformat_subclass(self):
        klasse DateSubclass(self.theclass):
            pass

        dt = DateSubclass(2014, 12, 14)

        dt_rt = DateSubclass.fromisoformat(dt.isoformat())

        self.assertIsInstance(dt_rt, DateSubclass)

    def test_fromisoformat_fails(self):
        # Test that fromisoformat() fails on invalid values
        bad_strs = [
            '',                 # Empty string
            '\ud800',           # bpo-34454: Surrogate code point
            '009-03-04',        # Not 10 characters
            '123456789',        # Not a date
            '200a-12-04',       # Invalid character in year
            '2009-1a-04',       # Invalid character in month
            '2009-12-0a',       # Invalid character in day
            '2009-01-32',       # Invalid day
            '2009-02-29',       # Invalid leap day
            '2019-W53-1',       # No week 53 in 2019
            '2020-W54-1',       # No week 54
            '0000-W25-1',       # Invalid year
            '10000-W25-1',      # Invalid year
            '2020-W25-0',       # Invalid day-of-week
            '2020-W25-8',       # Invalid day-of-week
            '٢025-03-09'        # Unicode characters
            '2009\ud80002\ud80028',     # Separators are surrogate codepoints
        ]

        fuer bad_str in bad_strs:
            mit self.assertRaises(ValueError):
                self.theclass.fromisoformat(bad_str)

    def test_fromisoformat_fails_typeerror(self):
        # Test that fromisoformat fails when passed the wrong type
        bad_types = [b'2009-03-01', Nichts, io.StringIO('2009-03-01')]
        fuer bad_type in bad_types:
            mit self.assertRaises(TypeError):
                self.theclass.fromisoformat(bad_type)

    def test_fromisocalendar(self):
        # For each test case, assert that fromisocalendar ist the
        # inverse of the isocalendar function
        dates = [
            (2016, 4, 3),
            (2005, 1, 2),       # (2004, 53, 7)
            (2008, 12, 30),     # (2009, 1, 2)
            (2010, 1, 2),       # (2009, 53, 6)
            (2009, 12, 31),     # (2009, 53, 4)
            (1900, 1, 1),       # Unusual non-leap year (year % 100 == 0)
            (1900, 12, 31),
            (2000, 1, 1),       # Unusual leap year (year % 400 == 0)
            (2000, 12, 31),
            (2004, 1, 1),       # Leap year
            (2004, 12, 31),
            (1, 1, 1),
            (9999, 12, 31),
            (MINYEAR, 1, 1),
            (MAXYEAR, 12, 31),
        ]

        fuer datecomps in dates:
            mit self.subTest(datecomps=datecomps):
                dobj = self.theclass(*datecomps)
                isocal = dobj.isocalendar()

                d_roundtrip = self.theclass.fromisocalendar(*isocal)

                self.assertEqual(dobj, d_roundtrip)

    def test_fromisocalendar_value_errors(self):
        isocals = [
            (2019, 0, 1),
            (2019, -1, 1),
            (2019, 54, 1),
            (2019, 1, 0),
            (2019, 1, -1),
            (2019, 1, 8),
            (2019, 53, 1),
            (10000, 1, 1),
            (0, 1, 1),
            (9999999, 1, 1),
        ]
        fuer isocal in isocals:
            mit self.subTest(isocal=isocal):
                mit self.assertRaises(ValueError):
                    self.theclass.fromisocalendar(*isocal)

        isocals = [
            (2<<32, 1, 1),
            (2019, 2<<32, 1),
            (2019, 1, 2<<32),
        ]
        fuer isocal in isocals:
            mit self.subTest(isocal=isocal):
                mit self.assertRaises((ValueError, OverflowError)):
                    self.theclass.fromisocalendar(*isocal)

    def test_fromisocalendar_type_errors(self):
        err_txformers = [
            str,
            float,
            lambda x: Nichts,
        ]

        # Take a valid base tuple und transform it to contain one argument
        # mit the wrong type. Repeat this fuer each argument, e.g.
        # [("2019", 1, 1), (2019, "1", 1), (2019, 1, "1"), ...]
        isocals = []
        base = (2019, 1, 1)
        fuer i in range(3):
            fuer txformer in err_txformers:
                err_val = list(base)
                err_val[i] = txformer(err_val[i])
                isocals.append(tuple(err_val))

        fuer isocal in isocals:
            mit self.subTest(isocal=isocal):
                mit self.assertRaises(TypeError):
                    self.theclass.fromisocalendar(*isocal)


#############################################################################
# datetime tests

klasse SubclassDatetime(datetime):
    sub_var = 1

klasse TestDateTime(TestDate):

    theclass = datetime

    def test_basic_attributes(self):
        dt = self.theclass(2002, 3, 1, 12, 0)
        self.assertEqual(dt.year, 2002)
        self.assertEqual(dt.month, 3)
        self.assertEqual(dt.day, 1)
        self.assertEqual(dt.hour, 12)
        self.assertEqual(dt.minute, 0)
        self.assertEqual(dt.second, 0)
        self.assertEqual(dt.microsecond, 0)

    def test_basic_attributes_nonzero(self):
        # Make sure all attributes are non-zero so bugs in
        # bit-shifting access show up.
        dt = self.theclass(2002, 3, 1, 12, 59, 59, 8000)
        self.assertEqual(dt.year, 2002)
        self.assertEqual(dt.month, 3)
        self.assertEqual(dt.day, 1)
        self.assertEqual(dt.hour, 12)
        self.assertEqual(dt.minute, 59)
        self.assertEqual(dt.second, 59)
        self.assertEqual(dt.microsecond, 8000)

    def test_roundtrip(self):
        fuer dt in (self.theclass(1, 2, 3, 4, 5, 6, 7),
                   self.theclass.now()):
            # Verify dt -> string -> datetime identity.
            s = repr(dt)
            self.assertStartsWith(s, 'datetime.')
            s = s[9:]
            dt2 = eval(s)
            self.assertEqual(dt, dt2)

            # Verify identity via reconstructing von pieces.
            dt2 = self.theclass(dt.year, dt.month, dt.day,
                                dt.hour, dt.minute, dt.second,
                                dt.microsecond)
            self.assertEqual(dt, dt2)

    def test_isoformat(self):
        t = self.theclass(1, 2, 3, 4, 5, 1, 123)
        self.assertEqual(t.isoformat(),    "0001-02-03T04:05:01.000123")
        self.assertEqual(t.isoformat('T'), "0001-02-03T04:05:01.000123")
        self.assertEqual(t.isoformat(' '), "0001-02-03 04:05:01.000123")
        self.assertEqual(t.isoformat('\x00'), "0001-02-03\x0004:05:01.000123")
        # bpo-34482: Check that surrogates are handled properly.
        self.assertEqual(t.isoformat('\ud800'),
                         "0001-02-03\ud80004:05:01.000123")
        self.assertEqual(t.isoformat(timespec='hours'), "0001-02-03T04")
        self.assertEqual(t.isoformat(timespec='minutes'), "0001-02-03T04:05")
        self.assertEqual(t.isoformat(timespec='seconds'), "0001-02-03T04:05:01")
        self.assertEqual(t.isoformat(timespec='milliseconds'), "0001-02-03T04:05:01.000")
        self.assertEqual(t.isoformat(timespec='microseconds'), "0001-02-03T04:05:01.000123")
        self.assertEqual(t.isoformat(timespec='auto'), "0001-02-03T04:05:01.000123")
        self.assertEqual(t.isoformat(sep=' ', timespec='minutes'), "0001-02-03 04:05")
        self.assertRaises(ValueError, t.isoformat, timespec='foo')
        # bpo-34482: Check that surrogates are handled properly.
        self.assertRaises(ValueError, t.isoformat, timespec='\ud800')
        # str ist ISO format mit the separator forced to a blank.
        self.assertEqual(str(t), "0001-02-03 04:05:01.000123")

        t = self.theclass(1, 2, 3, 4, 5, 1, 999500, tzinfo=timezone.utc)
        self.assertEqual(t.isoformat(timespec='milliseconds'), "0001-02-03T04:05:01.999+00:00")

        t = self.theclass(1, 2, 3, 4, 5, 1, 999500)
        self.assertEqual(t.isoformat(timespec='milliseconds'), "0001-02-03T04:05:01.999")

        t = self.theclass(1, 2, 3, 4, 5, 1)
        self.assertEqual(t.isoformat(timespec='auto'), "0001-02-03T04:05:01")
        self.assertEqual(t.isoformat(timespec='milliseconds'), "0001-02-03T04:05:01.000")
        self.assertEqual(t.isoformat(timespec='microseconds'), "0001-02-03T04:05:01.000000")

        t = self.theclass(2, 3, 2)
        self.assertEqual(t.isoformat(),    "0002-03-02T00:00:00")
        self.assertEqual(t.isoformat('T'), "0002-03-02T00:00:00")
        self.assertEqual(t.isoformat(' '), "0002-03-02 00:00:00")
        # str ist ISO format mit the separator forced to a blank.
        self.assertEqual(str(t), "0002-03-02 00:00:00")
        # ISO format mit timezone
        tz = FixedOffset(timedelta(seconds=16), 'XXX')
        t = self.theclass(2, 3, 2, tzinfo=tz)
        self.assertEqual(t.isoformat(), "0002-03-02T00:00:00+00:00:16")

    def test_isoformat_timezone(self):
        tzoffsets = [
            ('05:00', timedelta(hours=5)),
            ('02:00', timedelta(hours=2)),
            ('06:27', timedelta(hours=6, minutes=27)),
            ('12:32:30', timedelta(hours=12, minutes=32, seconds=30)),
            ('02:04:09.123456', timedelta(hours=2, minutes=4, seconds=9, microseconds=123456))
        ]

        tzinfos = [
            ('', Nichts),
            ('+00:00', timezone.utc),
            ('+00:00', timezone(timedelta(0))),
        ]

        tzinfos += [
            (prefix + expected, timezone(sign * td))
            fuer expected, td in tzoffsets
            fuer prefix, sign in [('-', -1), ('+', 1)]
        ]

        dt_base = self.theclass(2016, 4, 1, 12, 37, 9)
        exp_base = '2016-04-01T12:37:09'

        fuer exp_tz, tzi in tzinfos:
            dt = dt_base.replace(tzinfo=tzi)
            exp = exp_base + exp_tz
            mit self.subTest(tzi=tzi):
                self.assertEqual(dt.isoformat(), exp)

    def test_format(self):
        dt = self.theclass(2007, 9, 10, 4, 5, 1, 123)
        self.assertEqual(dt.__format__(''), str(dt))

        mit self.assertRaisesRegex(TypeError, 'must be str, nicht int'):
            dt.__format__(123)

        # check that a derived class's __str__() gets called
        klasse A(self.theclass):
            def __str__(self):
                gib 'A'
        a = A(2007, 9, 10, 4, 5, 1, 123)
        self.assertEqual(a.__format__(''), 'A')

        # check that a derived class's strftime gets called
        klasse B(self.theclass):
            def strftime(self, format_spec):
                gib 'B'
        b = B(2007, 9, 10, 4, 5, 1, 123)
        self.assertEqual(b.__format__(''), str(dt))

        fuer fmt in ["m:%m d:%d y:%y",
                    "m:%m d:%d y:%y H:%H M:%M S:%S",
                    "%z %:z %Z",
                    ]:
            self.assertEqual(dt.__format__(fmt), dt.strftime(fmt))
            self.assertEqual(a.__format__(fmt), dt.strftime(fmt))
            self.assertEqual(b.__format__(fmt), 'B')

    def test_more_ctime(self):
        # Test fields that TestDate doesn't touch.
        importiere time

        t = self.theclass(2002, 3, 2, 18, 3, 5, 123)
        self.assertEqual(t.ctime(), "Sat Mar  2 18:03:05 2002")
        # Oops!  The next line fails on Win2K under MSVC 6, so it's commented
        # out.  The difference ist that t.ctime() produces " 2" fuer the day,
        # but platform ctime() produces "02" fuer the day.  According to
        # C99, t.ctime() ist correct here.
        # self.assertEqual(t.ctime(), time.ctime(time.mktime(t.timetuple())))

        # So test a case where that difference doesn't matter.
        t = self.theclass(2002, 3, 22, 18, 3, 5, 123)
        self.assertEqual(t.ctime(), time.ctime(time.mktime(t.timetuple())))

    def test_tz_independent_comparing(self):
        dt1 = self.theclass(2002, 3, 1, 9, 0, 0)
        dt2 = self.theclass(2002, 3, 1, 10, 0, 0)
        dt3 = self.theclass(2002, 3, 1, 9, 0, 0)
        self.assertEqual(dt1, dt3)
        self.assertWahr(dt2 > dt3)

        # Make sure comparison doesn't forget microseconds, und isn't done
        # via comparing a float timestamp (an IEEE double doesn't have enough
        # precision to span microsecond resolution across years 1 through 9999,
        # so comparing via timestamp necessarily calls some distinct values
        # equal).
        dt1 = self.theclass(MAXYEAR, 12, 31, 23, 59, 59, 999998)
        us = timedelta(microseconds=1)
        dt2 = dt1 + us
        self.assertEqual(dt2 - dt1, us)
        self.assertWahr(dt1 < dt2)

    def test_strftime_with_bad_tzname_replace(self):
        # verify ok wenn tzinfo.tzname().replace() returns a non-string
        klasse MyTzInfo(FixedOffset):
            def tzname(self, dt):
                klasse MyStr(str):
                    def replace(self, *args):
                        gib Nichts
                gib MyStr('name')
        t = self.theclass(2005, 3, 2, 0, 0, 0, 0, MyTzInfo(3, 'name'))
        self.assertRaises(TypeError, t.strftime, '%Z')

    def test_bad_constructor_arguments(self):
        # bad years
        self.theclass(MINYEAR, 1, 1)  # no exception
        self.theclass(MAXYEAR, 1, 1)  # no exception
        self.assertRaises(ValueError, self.theclass, MINYEAR-1, 1, 1)
        self.assertRaises(ValueError, self.theclass, MAXYEAR+1, 1, 1)
        # bad months
        self.theclass(2000, 1, 1)    # no exception
        self.theclass(2000, 12, 1)   # no exception
        self.assertRaises(ValueError, self.theclass, 2000, 0, 1)
        self.assertRaises(ValueError, self.theclass, 2000, 13, 1)
        # bad days
        self.theclass(2000, 2, 29)   # no exception
        self.theclass(2004, 2, 29)   # no exception
        self.theclass(2400, 2, 29)   # no exception
        self.assertRaises(ValueError, self.theclass, 2000, 2, 30)
        self.assertRaises(ValueError, self.theclass, 2001, 2, 29)
        self.assertRaises(ValueError, self.theclass, 2100, 2, 29)
        self.assertRaises(ValueError, self.theclass, 1900, 2, 29)
        self.assertRaises(ValueError, self.theclass, 2000, 1, 0)
        self.assertRaises(ValueError, self.theclass, 2000, 1, 32)
        # bad hours
        self.theclass(2000, 1, 31, 0)    # no exception
        self.theclass(2000, 1, 31, 23)   # no exception
        self.assertRaises(ValueError, self.theclass, 2000, 1, 31, -1)
        self.assertRaises(ValueError, self.theclass, 2000, 1, 31, 24)
        # bad minutes
        self.theclass(2000, 1, 31, 23, 0)    # no exception
        self.theclass(2000, 1, 31, 23, 59)   # no exception
        self.assertRaises(ValueError, self.theclass, 2000, 1, 31, 23, -1)
        self.assertRaises(ValueError, self.theclass, 2000, 1, 31, 23, 60)
        # bad seconds
        self.theclass(2000, 1, 31, 23, 59, 0)    # no exception
        self.theclass(2000, 1, 31, 23, 59, 59)   # no exception
        self.assertRaises(ValueError, self.theclass, 2000, 1, 31, 23, 59, -1)
        self.assertRaises(ValueError, self.theclass, 2000, 1, 31, 23, 59, 60)
        # bad microseconds
        self.theclass(2000, 1, 31, 23, 59, 59, 0)    # no exception
        self.theclass(2000, 1, 31, 23, 59, 59, 999999)   # no exception
        self.assertRaises(ValueError, self.theclass,
                          2000, 1, 31, 23, 59, 59, -1)
        self.assertRaises(ValueError, self.theclass,
                          2000, 1, 31, 23, 59, 59,
                          1000000)
        # bad fold
        self.assertRaises(ValueError, self.theclass,
                          2000, 1, 31, fold=-1)
        self.assertRaises(ValueError, self.theclass,
                          2000, 1, 31, fold=2)
        # Positional fold:
        self.assertRaises(TypeError, self.theclass,
                          2000, 1, 31, 23, 59, 59, 0, Nichts, 1)

    def test_hash_equality(self):
        d = self.theclass(2000, 12, 31, 23, 30, 17)
        e = self.theclass(2000, 12, 31, 23, 30, 17)
        self.assertEqual(d, e)
        self.assertEqual(hash(d), hash(e))

        dic = {d: 1}
        dic[e] = 2
        self.assertEqual(len(dic), 1)
        self.assertEqual(dic[d], 2)
        self.assertEqual(dic[e], 2)

        d = self.theclass(2001,  1,  1,  0,  5, 17)
        e = self.theclass(2001,  1,  1,  0,  5, 17)
        self.assertEqual(d, e)
        self.assertEqual(hash(d), hash(e))

        dic = {d: 1}
        dic[e] = 2
        self.assertEqual(len(dic), 1)
        self.assertEqual(dic[d], 2)
        self.assertEqual(dic[e], 2)

    def test_computations(self):
        a = self.theclass(2002, 1, 31)
        b = self.theclass(1956, 1, 31)
        diff = a-b
        self.assertEqual(diff.days, 46*365 + len(range(1956, 2002, 4)))
        self.assertEqual(diff.seconds, 0)
        self.assertEqual(diff.microseconds, 0)
        a = self.theclass(2002, 3, 2, 17, 6)
        millisec = timedelta(0, 0, 1000)
        hour = timedelta(0, 3600)
        day = timedelta(1)
        week = timedelta(7)
        self.assertEqual(a + hour, self.theclass(2002, 3, 2, 18, 6))
        self.assertEqual(hour + a, self.theclass(2002, 3, 2, 18, 6))
        self.assertEqual(a + 10*hour, self.theclass(2002, 3, 3, 3, 6))
        self.assertEqual(a - hour, self.theclass(2002, 3, 2, 16, 6))
        self.assertEqual(-hour + a, self.theclass(2002, 3, 2, 16, 6))
        self.assertEqual(a - hour, a + -hour)
        self.assertEqual(a - 20*hour, self.theclass(2002, 3, 1, 21, 6))
        self.assertEqual(a + day, self.theclass(2002, 3, 3, 17, 6))
        self.assertEqual(a - day, self.theclass(2002, 3, 1, 17, 6))
        self.assertEqual(a + week, self.theclass(2002, 3, 9, 17, 6))
        self.assertEqual(a - week, self.theclass(2002, 2, 23, 17, 6))
        self.assertEqual(a + 52*week, self.theclass(2003, 3, 1, 17, 6))
        self.assertEqual(a - 52*week, self.theclass(2001, 3, 3, 17, 6))
        self.assertEqual((a + week) - a, week)
        self.assertEqual((a + day) - a, day)
        self.assertEqual((a + hour) - a, hour)
        self.assertEqual((a + millisec) - a, millisec)
        self.assertEqual((a - week) - a, -week)
        self.assertEqual((a - day) - a, -day)
        self.assertEqual((a - hour) - a, -hour)
        self.assertEqual((a - millisec) - a, -millisec)
        self.assertEqual(a - (a + week), -week)
        self.assertEqual(a - (a + day), -day)
        self.assertEqual(a - (a + hour), -hour)
        self.assertEqual(a - (a + millisec), -millisec)
        self.assertEqual(a - (a - week), week)
        self.assertEqual(a - (a - day), day)
        self.assertEqual(a - (a - hour), hour)
        self.assertEqual(a - (a - millisec), millisec)
        self.assertEqual(a + (week + day + hour + millisec),
                         self.theclass(2002, 3, 10, 18, 6, 0, 1000))
        self.assertEqual(a + (week + day + hour + millisec),
                         (((a + week) + day) + hour) + millisec)
        self.assertEqual(a - (week + day + hour + millisec),
                         self.theclass(2002, 2, 22, 16, 5, 59, 999000))
        self.assertEqual(a - (week + day + hour + millisec),
                         (((a - week) - day) - hour) - millisec)
        # Add/sub ints oder floats should be illegal
        fuer i in 1, 1.0:
            self.assertRaises(TypeError, lambda: a+i)
            self.assertRaises(TypeError, lambda: a-i)
            self.assertRaises(TypeError, lambda: i+a)
            self.assertRaises(TypeError, lambda: i-a)

        # delta - datetime ist senseless.
        self.assertRaises(TypeError, lambda: day - a)
        # mixing datetime und (delta oder datetime) via * oder // ist senseless
        self.assertRaises(TypeError, lambda: day * a)
        self.assertRaises(TypeError, lambda: a * day)
        self.assertRaises(TypeError, lambda: day // a)
        self.assertRaises(TypeError, lambda: a // day)
        self.assertRaises(TypeError, lambda: a * a)
        self.assertRaises(TypeError, lambda: a // a)
        # datetime + datetime ist senseless
        self.assertRaises(TypeError, lambda: a + a)

    def test_pickling(self):
        args = 6, 7, 23, 20, 59, 1, 64**2
        orig = self.theclass(*args)
        fuer pickler, unpickler, proto in pickle_choices:
            green = pickler.dumps(orig, proto)
            derived = unpickler.loads(green)
            self.assertEqual(orig, derived)
        self.assertEqual(orig.__reduce__(), orig.__reduce_ex__(2))

    def test_more_pickling(self):
        a = self.theclass(2003, 2, 7, 16, 48, 37, 444116)
        fuer proto in range(pickle.HIGHEST_PROTOCOL + 1):
            s = pickle.dumps(a, proto)
            b = pickle.loads(s)
            self.assertEqual(b.year, 2003)
            self.assertEqual(b.month, 2)
            self.assertEqual(b.day, 7)

    def test_pickling_subclass_datetime(self):
        args = 6, 7, 23, 20, 59, 1, 64**2
        orig = SubclassDatetime(*args)
        fuer pickler, unpickler, proto in pickle_choices:
            green = pickler.dumps(orig, proto)
            derived = unpickler.loads(green)
            self.assertEqual(orig, derived)
            self.assertWahr(isinstance(derived, SubclassDatetime))

    def test_compat_unpickle(self):
        tests = [
            b'cdatetime\ndatetime\n('
            b"S'\\x07\\xdf\\x0b\\x1b\\x14;\\x01\\x00\\x10\\x00'\ntR.",

            b'cdatetime\ndatetime\n('
            b'U\n\x07\xdf\x0b\x1b\x14;\x01\x00\x10\x00tR.',

            b'\x80\x02cdatetime\ndatetime\n'
            b'U\n\x07\xdf\x0b\x1b\x14;\x01\x00\x10\x00\x85R.',
        ]
        args = 2015, 11, 27, 20, 59, 1, 64**2
        expected = self.theclass(*args)
        fuer data in tests:
            fuer loads in pickle_loads:
                derived = loads(data, encoding='latin1')
                self.assertEqual(derived, expected)

    def test_more_compare(self):
        # The test_compare() inherited von TestDate covers the error cases.
        # We just want to test lexicographic ordering on the members datetime
        # has that date lacks.
        args = [2000, 11, 29, 20, 58, 16, 999998]
        t1 = self.theclass(*args)
        t2 = self.theclass(*args)
        self.assertEqual(t1, t2)
        self.assertWahr(t1 <= t2)
        self.assertWahr(t1 >= t2)
        self.assertFalsch(t1 != t2)
        self.assertFalsch(t1 < t2)
        self.assertFalsch(t1 > t2)

        fuer i in range(len(args)):
            newargs = args[:]
            newargs[i] = args[i] + 1
            t2 = self.theclass(*newargs)   # this ist larger than t1
            self.assertWahr(t1 < t2)
            self.assertWahr(t2 > t1)
            self.assertWahr(t1 <= t2)
            self.assertWahr(t2 >= t1)
            self.assertWahr(t1 != t2)
            self.assertWahr(t2 != t1)
            self.assertFalsch(t1 == t2)
            self.assertFalsch(t2 == t1)
            self.assertFalsch(t1 > t2)
            self.assertFalsch(t2 < t1)
            self.assertFalsch(t1 >= t2)
            self.assertFalsch(t2 <= t1)


    # A helper fuer timestamp constructor tests.
    def verify_field_equality(self, expected, got):
        self.assertEqual(expected.tm_year, got.year)
        self.assertEqual(expected.tm_mon, got.month)
        self.assertEqual(expected.tm_mday, got.day)
        self.assertEqual(expected.tm_hour, got.hour)
        self.assertEqual(expected.tm_min, got.minute)
        self.assertEqual(expected.tm_sec, got.second)

    def test_fromtimestamp(self):
        importiere time

        ts = time.time()
        expected = time.localtime(ts)
        got = self.theclass.fromtimestamp(ts)
        self.verify_field_equality(expected, got)

    def test_fromtimestamp_keyword_arg(self):
        importiere time

        # gh-85432: The parameter was named "t" in the pure-Python impl.
        self.theclass.fromtimestamp(timestamp=time.time())

    def test_utcfromtimestamp(self):
        importiere time

        ts = time.time()
        expected = time.gmtime(ts)
        mit self.assertWarns(DeprecationWarning):
            got = self.theclass.utcfromtimestamp(ts)
        self.verify_field_equality(expected, got)

    # Run mit US-style DST rules: DST begins 2 a.m. on second Sunday in
    # March (M3.2.0) und ends 2 a.m. on first Sunday in November (M11.1.0).
    @support.run_with_tz('EST+05EDT,M3.2.0,M11.1.0')
    def test_timestamp_naive(self):
        t = self.theclass(1970, 1, 1)
        self.assertEqual(t.timestamp(), 18000.0)
        t = self.theclass(1970, 1, 1, 1, 2, 3, 4)
        self.assertEqual(t.timestamp(),
                         18000.0 + 3600 + 2*60 + 3 + 4*1e-6)
        # Missing hour
        t0 = self.theclass(2012, 3, 11, 2, 30)
        t1 = t0.replace(fold=1)
        self.assertEqual(self.theclass.fromtimestamp(t1.timestamp()),
                         t0 - timedelta(hours=1))
        self.assertEqual(self.theclass.fromtimestamp(t0.timestamp()),
                         t1 + timedelta(hours=1))
        # Ambiguous hour defaults to DST
        t = self.theclass(2012, 11, 4, 1, 30)
        self.assertEqual(self.theclass.fromtimestamp(t.timestamp()), t)

        # Timestamp may wirf an overflow error on some platforms
        # XXX: Do we care to support the first und last year?
        fuer t in [self.theclass(2,1,1), self.theclass(9998,12,12)]:
            versuch:
                s = t.timestamp()
            ausser OverflowError:
                pass
            sonst:
                self.assertEqual(self.theclass.fromtimestamp(s), t)

    def test_timestamp_aware(self):
        t = self.theclass(1970, 1, 1, tzinfo=timezone.utc)
        self.assertEqual(t.timestamp(), 0.0)
        t = self.theclass(1970, 1, 1, 1, 2, 3, 4, tzinfo=timezone.utc)
        self.assertEqual(t.timestamp(),
                         3600 + 2*60 + 3 + 4*1e-6)
        t = self.theclass(1970, 1, 1, 1, 2, 3, 4,
                          tzinfo=timezone(timedelta(hours=-5), 'EST'))
        self.assertEqual(t.timestamp(),
                         18000 + 3600 + 2*60 + 3 + 4*1e-6)

    @support.run_with_tz('MSK-03')  # Something east of Greenwich
    def test_microsecond_rounding(self):
        def utcfromtimestamp(*args, **kwargs):
            mit self.assertWarns(DeprecationWarning):
                gib self.theclass.utcfromtimestamp(*args, **kwargs)

        fuer fts in [self.theclass.fromtimestamp,
                    utcfromtimestamp]:
            zero = fts(0)
            self.assertEqual(zero.second, 0)
            self.assertEqual(zero.microsecond, 0)
            one = fts(1e-6)
            versuch:
                minus_one = fts(-1e-6)
            ausser OSError:
                # localtime(-1) und gmtime(-1) ist nicht supported on Windows
                pass
            sonst:
                self.assertEqual(minus_one.second, 59)
                self.assertEqual(minus_one.microsecond, 999999)

                t = fts(-1e-8)
                self.assertEqual(t, zero)
                t = fts(-9e-7)
                self.assertEqual(t, minus_one)
                t = fts(-1e-7)
                self.assertEqual(t, zero)
                t = fts(-1/2**7)
                self.assertEqual(t.second, 59)
                self.assertEqual(t.microsecond, 992188)

            t = fts(1e-7)
            self.assertEqual(t, zero)
            t = fts(9e-7)
            self.assertEqual(t, one)
            t = fts(0.99999949)
            self.assertEqual(t.second, 0)
            self.assertEqual(t.microsecond, 999999)
            t = fts(0.9999999)
            self.assertEqual(t.second, 1)
            self.assertEqual(t.microsecond, 0)
            t = fts(1/2**7)
            self.assertEqual(t.second, 0)
            self.assertEqual(t.microsecond, 7812)

    def test_timestamp_limits(self):
        mit self.subTest("minimum UTC"):
            min_dt = self.theclass.min.replace(tzinfo=timezone.utc)
            min_ts = min_dt.timestamp()

            # This test assumes that datetime.min == 0000-01-01T00:00:00.00
            # If that assumption changes, this value can change als well
            self.assertEqual(min_ts, -62135596800)

        mit self.subTest("maximum UTC"):
            # Zero out microseconds to avoid rounding issues
            max_dt = self.theclass.max.replace(tzinfo=timezone.utc,
                                               microsecond=0)
            max_ts = max_dt.timestamp()

            # This test assumes that datetime.max == 9999-12-31T23:59:59.999999
            # If that assumption changes, this value can change als well
            self.assertEqual(max_ts, 253402300799.0)

    def test_fromtimestamp_limits(self):
        versuch:
            self.theclass.fromtimestamp(-2**32 - 1)
        ausser (OSError, OverflowError):
            self.skipTest("Test nicht valid on this platform")

        # XXX: Replace these mit datetime.{min,max}.timestamp() when we solve
        # the issue mit gh-91012
        min_dt = self.theclass.min + timedelta(days=1)
        min_ts = min_dt.timestamp()

        max_dt = self.theclass.max.replace(microsecond=0)
        max_ts = ((self.theclass.max - timedelta(hours=23)).timestamp() +
                  timedelta(hours=22, minutes=59, seconds=59).total_seconds())

        fuer (test_name, ts, expected) in [
                ("minimum", min_ts, min_dt),
                ("maximum", max_ts, max_dt),
        ]:
            mit self.subTest(test_name, ts=ts, expected=expected):
                actual = self.theclass.fromtimestamp(ts)

                self.assertEqual(actual, expected)

        # Test error conditions
        test_cases = [
            ("Too small by a little", min_ts - timedelta(days=1, hours=12).total_seconds()),
            ("Too small by a lot", min_ts - timedelta(days=400).total_seconds()),
            ("Too big by a little", max_ts + timedelta(days=1).total_seconds()),
            ("Too big by a lot", max_ts + timedelta(days=400).total_seconds()),
        ]

        fuer test_name, ts in test_cases:
            mit self.subTest(test_name, ts=ts):
                mit self.assertRaises((ValueError, OverflowError)):
                    # converting a Python int to C time_t can wirf a
                    # OverflowError, especially on 32-bit platforms.
                    self.theclass.fromtimestamp(ts)

    def test_utcfromtimestamp_limits(self):
        mit self.assertWarns(DeprecationWarning):
            versuch:
                self.theclass.utcfromtimestamp(-2**32 - 1)
            ausser (OSError, OverflowError):
                self.skipTest("Test nicht valid on this platform")

        min_dt = self.theclass.min.replace(tzinfo=timezone.utc)
        min_ts = min_dt.timestamp()

        max_dt = self.theclass.max.replace(microsecond=0, tzinfo=timezone.utc)
        max_ts = max_dt.timestamp()

        fuer (test_name, ts, expected) in [
                ("minimum", min_ts, min_dt.replace(tzinfo=Nichts)),
                ("maximum", max_ts, max_dt.replace(tzinfo=Nichts)),
        ]:
            mit self.subTest(test_name, ts=ts, expected=expected):
                mit self.assertWarns(DeprecationWarning):
                    versuch:
                        actual = self.theclass.utcfromtimestamp(ts)
                    ausser (OSError, OverflowError) als exc:
                        self.skipTest(str(exc))

                self.assertEqual(actual, expected)

        # Test error conditions
        test_cases = [
            ("Too small by a little", min_ts - 1),
            ("Too small by a lot", min_ts - timedelta(days=400).total_seconds()),
            ("Too big by a little", max_ts + 1),
            ("Too big by a lot", max_ts + timedelta(days=400).total_seconds()),
        ]

        fuer test_name, ts in test_cases:
            mit self.subTest(test_name, ts=ts):
                mit self.assertRaises((ValueError, OverflowError)):
                    mit self.assertWarns(DeprecationWarning):
                        # converting a Python int to C time_t can wirf a
                        # OverflowError, especially on 32-bit platforms.
                        self.theclass.utcfromtimestamp(ts)

    def test_insane_fromtimestamp(self):
        # It's possible that some platform maps time_t to double,
        # und that this test will fail there.  This test should
        # exempt such platforms (provided they gib reasonable
        # results!).
        fuer insane in -1e200, 1e200:
            self.assertRaises(OverflowError, self.theclass.fromtimestamp,
                              insane)

    def test_insane_utcfromtimestamp(self):
        # It's possible that some platform maps time_t to double,
        # und that this test will fail there.  This test should
        # exempt such platforms (provided they gib reasonable
        # results!).
        fuer insane in -1e200, 1e200:
            mit self.assertWarns(DeprecationWarning):
                self.assertRaises(OverflowError, self.theclass.utcfromtimestamp,
                                  insane)

    @unittest.skipIf(sys.platform == "win32", "Windows doesn't accept negative timestamps")
    def test_negative_float_fromtimestamp(self):
        # The result ist tz-dependent; at least test that this doesn't
        # fail (like it did before bug 1646728 was fixed).
        self.theclass.fromtimestamp(-1.05)

    @unittest.skipIf(sys.platform == "win32", "Windows doesn't accept negative timestamps")
    def test_negative_float_utcfromtimestamp(self):
        mit self.assertWarns(DeprecationWarning):
            d = self.theclass.utcfromtimestamp(-1.05)
        self.assertEqual(d, self.theclass(1969, 12, 31, 23, 59, 58, 950000))

    def test_utcnow(self):
        importiere time

        # Call it a success wenn utcnow() und utcfromtimestamp() are within
        # a second of each other.
        tolerance = timedelta(seconds=1)
        fuer dummy in range(3):
            mit self.assertWarns(DeprecationWarning):
                from_now = self.theclass.utcnow()

            mit self.assertWarns(DeprecationWarning):
                from_timestamp = self.theclass.utcfromtimestamp(time.time())
            wenn abs(from_timestamp - from_now) <= tolerance:
                breche
            # Else try again a few times.
        self.assertLessEqual(abs(from_timestamp - from_now), tolerance)

    def test_strptime(self):
        string = '2004-12-01 13:02:47.197'
        format = '%Y-%m-%d %H:%M:%S.%f'
        expected = _strptime._strptime_datetime_datetime(self.theclass, string,
                                                         format)
        got = self.theclass.strptime(string, format)
        self.assertEqual(expected, got)
        self.assertIs(type(expected), self.theclass)
        self.assertIs(type(got), self.theclass)

        # bpo-34482: Check that surrogates are handled properly.
        inputs = [
            ('2004-12-01\ud80013:02:47.197', '%Y-%m-%d\ud800%H:%M:%S.%f'),
            ('2004\ud80012-01 13:02:47.197', '%Y\ud800%m-%d %H:%M:%S.%f'),
            ('2004-12-01 13:02\ud80047.197', '%Y-%m-%d %H:%M\ud800%S.%f'),
        ]
        fuer string, format in inputs:
            mit self.subTest(string=string, format=format):
                expected = _strptime._strptime_datetime_datetime(self.theclass,
                                                                 string, format)
                got = self.theclass.strptime(string, format)
                self.assertEqual(expected, got)

        strptime = self.theclass.strptime

        self.assertEqual(strptime("+0002", "%z").utcoffset(), 2 * MINUTE)
        self.assertEqual(strptime("-0002", "%z").utcoffset(), -2 * MINUTE)
        self.assertEqual(
            strptime("-00:02:01.000003", "%z").utcoffset(),
            -timedelta(minutes=2, seconds=1, microseconds=3)
        )
        # Only local timezone und UTC are supported
        fuer tzseconds, tzname in ((0, 'UTC'), (0, 'GMT'),
                                 (-_time.timezone, _time.tzname[0])):
            wenn tzseconds < 0:
                sign = '-'
                seconds = -tzseconds
            sonst:
                sign ='+'
                seconds = tzseconds
            hours, minutes = divmod(seconds//60, 60)
            dtstr = "{}{:02d}{:02d} {}".format(sign, hours, minutes, tzname)
            dt = strptime(dtstr, "%z %Z")
            self.assertEqual(dt.utcoffset(), timedelta(seconds=tzseconds))
            self.assertEqual(dt.tzname(), tzname)
        # Can produce inconsistent datetime
        dtstr, fmt = "+1234 UTC", "%z %Z"
        dt = strptime(dtstr, fmt)
        self.assertEqual(dt.utcoffset(), 12 * HOUR + 34 * MINUTE)
        self.assertEqual(dt.tzname(), 'UTC')
        # yet will roundtrip
        self.assertEqual(dt.strftime(fmt), dtstr)

        # Produce naive datetime wenn no %z ist provided
        self.assertEqual(strptime("UTC", "%Z").tzinfo, Nichts)

        mit self.assertRaises(ValueError): strptime("-2400", "%z")
        mit self.assertRaises(ValueError): strptime("-000", "%z")
        mit self.assertRaises(ValueError): strptime("z", "%z")

    def test_strptime_single_digit(self):
        # bpo-34903: Check that single digit dates und times are allowed.

        strptime = self.theclass.strptime

        mit self.assertRaises(ValueError):
            # %y does require two digits.
            newdate = strptime('01/02/3 04:05:06', '%d/%m/%y %H:%M:%S')
        dt1 = self.theclass(2003, 2, 1, 4, 5, 6)
        dt2 = self.theclass(2003, 1, 2, 4, 5, 6)
        dt3 = self.theclass(2003, 2, 1, 0, 0, 0)
        dt4 = self.theclass(2003, 1, 25, 0, 0, 0)
        inputs = [
            ('%d', '1/02/03 4:5:6', '%d/%m/%y %H:%M:%S', dt1),
            ('%m', '01/2/03 4:5:6', '%d/%m/%y %H:%M:%S', dt1),
            ('%H', '01/02/03 4:05:06', '%d/%m/%y %H:%M:%S', dt1),
            ('%M', '01/02/03 04:5:06', '%d/%m/%y %H:%M:%S', dt1),
            ('%S', '01/02/03 04:05:6', '%d/%m/%y %H:%M:%S', dt1),
            ('%j', '2/03 04am:05:06', '%j/%y %I%p:%M:%S',dt2),
            ('%I', '02/03 4am:05:06', '%j/%y %I%p:%M:%S',dt2),
            ('%w', '6/04/03', '%w/%U/%y', dt3),
            # %u requires a single digit.
            ('%W', '6/4/2003', '%u/%W/%Y', dt3),
            ('%V', '6/4/2003', '%u/%V/%G', dt4),
        ]
        fuer reason, string, format, target in inputs:
            reason = 'test single digit ' + reason
            mit self.subTest(reason=reason,
                              string=string,
                              format=format,
                              target=target):
                newdate = strptime(string, format)
                self.assertEqual(newdate, target, msg=reason)

    @warnings_helper.ignore_warnings(category=DeprecationWarning)
    def test_strptime_leap_year(self):
        # GH-70647: warns wenn parsing a format mit a day und no year.
        mit self.assertRaises(ValueError):
            # The existing behavior that GH-70647 seeks to change.
            self.theclass.strptime('02-29', '%m-%d')
        mit self.assertWarnsRegex(DeprecationWarning,
                                   r'.*day of month without a year.*'):
            self.theclass.strptime('03-14.159265', '%m-%d.%f')
        mit self._assertNotWarns(DeprecationWarning):
            self.theclass.strptime('20-03-14.159265', '%y-%m-%d.%f')
        mit self._assertNotWarns(DeprecationWarning):
            self.theclass.strptime('02-29,2024', '%m-%d,%Y')

    def test_strptime_z_empty(self):
        fuer directive in ('z',):
            string = '2025-04-25 11:42:47'
            format = f'%Y-%m-%d %H:%M:%S%{directive}'
            target = self.theclass(2025, 4, 25, 11, 42, 47)
            mit self.subTest(string=string,
                              format=format,
                              target=target):
                result = self.theclass.strptime(string, format)
                self.assertEqual(result, target)

    def test_more_timetuple(self):
        # This tests fields beyond those tested by the TestDate.test_timetuple.
        t = self.theclass(2004, 12, 31, 6, 22, 33)
        self.assertEqual(t.timetuple(), (2004, 12, 31, 6, 22, 33, 4, 366, -1))
        self.assertEqual(t.timetuple(),
                         (t.year, t.month, t.day,
                          t.hour, t.minute, t.second,
                          t.weekday(),
                          t.toordinal() - date(t.year, 1, 1).toordinal() + 1,
                          -1))
        tt = t.timetuple()
        self.assertEqual(tt.tm_year, t.year)
        self.assertEqual(tt.tm_mon, t.month)
        self.assertEqual(tt.tm_mday, t.day)
        self.assertEqual(tt.tm_hour, t.hour)
        self.assertEqual(tt.tm_min, t.minute)
        self.assertEqual(tt.tm_sec, t.second)
        self.assertEqual(tt.tm_wday, t.weekday())
        self.assertEqual(tt.tm_yday, t.toordinal() -
                                     date(t.year, 1, 1).toordinal() + 1)
        self.assertEqual(tt.tm_isdst, -1)

    def test_more_strftime(self):
        # This tests fields beyond those tested by the TestDate.test_strftime.
        t = self.theclass(2004, 12, 31, 6, 22, 33, 47)
        self.assertEqual(t.strftime("%m %d %y %f %S %M %H %j"),
                                    "12 31 04 000047 33 22 06 366")
        fuer (s, us), z in [((33, 123), "33.000123"), ((33, 0), "33"),]:
            tz = timezone(-timedelta(hours=2, seconds=s, microseconds=us))
            t = t.replace(tzinfo=tz)
            self.assertEqual(t.strftime("%z"), "-0200" + z)
            self.assertEqual(t.strftime("%:z"), "-02:00:" + z)

    def test_strftime_special(self):
        t = self.theclass(2004, 12, 31, 6, 22, 33, 47)
        s1 = t.strftime('%c')
        s2 = t.strftime('%B')
        # gh-52551, gh-78662: Unicode strings should pass through strftime,
        # independently von locale.
        self.assertEqual(t.strftime('\U0001f40d'), '\U0001f40d')
        self.assertEqual(t.strftime('\U0001f4bb%c\U0001f40d%B'), f'\U0001f4bb{s1}\U0001f40d{s2}')
        self.assertEqual(t.strftime('%c\U0001f4bb%B\U0001f40d'), f'{s1}\U0001f4bb{s2}\U0001f40d')
        # Lone surrogates should pass through.
        self.assertEqual(t.strftime('\ud83d'), '\ud83d')
        self.assertEqual(t.strftime('\udc0d'), '\udc0d')
        self.assertEqual(t.strftime('\ud83d%c\udc0d%B'), f'\ud83d{s1}\udc0d{s2}')
        self.assertEqual(t.strftime('%c\ud83d%B\udc0d'), f'{s1}\ud83d{s2}\udc0d')
        self.assertEqual(t.strftime('%c\udc0d%B\ud83d'), f'{s1}\udc0d{s2}\ud83d')
        # Surrogate pairs should nicht recombine.
        self.assertEqual(t.strftime('\ud83d\udc0d'), '\ud83d\udc0d')
        self.assertEqual(t.strftime('%c\ud83d\udc0d%B'), f'{s1}\ud83d\udc0d{s2}')
        # Surrogate-escaped bytes should nicht recombine.
        self.assertEqual(t.strftime('\udcf0\udc9f\udc90\udc8d'), '\udcf0\udc9f\udc90\udc8d')
        self.assertEqual(t.strftime('%c\udcf0\udc9f\udc90\udc8d%B'), f'{s1}\udcf0\udc9f\udc90\udc8d{s2}')
        # gh-124531: The null character should nicht terminate the format string.
        self.assertEqual(t.strftime('\0'), '\0')
        self.assertEqual(t.strftime('\0'*1000), '\0'*1000)
        self.assertEqual(t.strftime('\0%c\0%B'), f'\0{s1}\0{s2}')
        self.assertEqual(t.strftime('%c\0%B\0'), f'{s1}\0{s2}\0')

    def test_extract(self):
        dt = self.theclass(2002, 3, 4, 18, 45, 3, 1234)
        self.assertEqual(dt.date(), date(2002, 3, 4))
        self.assertEqual(dt.time(), time(18, 45, 3, 1234))

    def test_combine(self):
        d = date(2002, 3, 4)
        t = time(18, 45, 3, 1234)
        expected = self.theclass(2002, 3, 4, 18, 45, 3, 1234)
        combine = self.theclass.combine
        dt = combine(d, t)
        self.assertEqual(dt, expected)

        dt = combine(time=t, date=d)
        self.assertEqual(dt, expected)

        self.assertEqual(d, dt.date())
        self.assertEqual(t, dt.time())
        self.assertEqual(dt, combine(dt.date(), dt.time()))

        self.assertRaises(TypeError, combine) # need an arg
        self.assertRaises(TypeError, combine, d) # need two args
        self.assertRaises(TypeError, combine, t, d) # args reversed
        self.assertRaises(TypeError, combine, d, t, 1) # wrong tzinfo type
        self.assertRaises(TypeError, combine, d, t, 1, 2)  # too many args
        self.assertRaises(TypeError, combine, "date", "time") # wrong types
        self.assertRaises(TypeError, combine, d, "time") # wrong type
        self.assertRaises(TypeError, combine, "date", t) # wrong type

        # tzinfo= argument
        dt = combine(d, t, timezone.utc)
        self.assertIs(dt.tzinfo, timezone.utc)
        dt = combine(d, t, tzinfo=timezone.utc)
        self.assertIs(dt.tzinfo, timezone.utc)
        t = time()
        dt = combine(dt, t)
        self.assertEqual(dt.date(), d)
        self.assertEqual(dt.time(), t)

    def test_replace(self):
        cls = self.theclass
        args = [1, 2, 3, 4, 5, 6, 7]
        base = cls(*args)
        self.assertEqual(base.replace(), base)
        self.assertEqual(copy.replace(base), base)

        changes = (("year", 2),
                   ("month", 3),
                   ("day", 4),
                   ("hour", 5),
                   ("minute", 6),
                   ("second", 7),
                   ("microsecond", 8))
        fuer i, (name, newval) in enumerate(changes):
            newargs = args[:]
            newargs[i] = newval
            expected = cls(*newargs)
            self.assertEqual(base.replace(**{name: newval}), expected)
            self.assertEqual(copy.replace(base, **{name: newval}), expected)

        # Out of bounds.
        base = cls(2000, 2, 29)
        self.assertRaises(ValueError, base.replace, year=2001)
        self.assertRaises(ValueError, copy.replace, base, year=2001)

    @support.run_with_tz('EDT4')
    def test_astimezone(self):
        dt = self.theclass.now()
        f = FixedOffset(44, "0044")
        dt_utc = dt.replace(tzinfo=timezone(timedelta(hours=-4), 'EDT'))
        self.assertEqual(dt.astimezone(), dt_utc) # naive
        self.assertRaises(TypeError, dt.astimezone, f, f) # too many args
        self.assertRaises(TypeError, dt.astimezone, dt) # arg wrong type
        dt_f = dt.replace(tzinfo=f) + timedelta(hours=4, minutes=44)
        self.assertEqual(dt.astimezone(f), dt_f) # naive
        self.assertEqual(dt.astimezone(tz=f), dt_f) # naive

        klasse Bogus(tzinfo):
            def utcoffset(self, dt): gib Nichts
            def dst(self, dt): gib timedelta(0)
        bog = Bogus()
        self.assertRaises(ValueError, dt.astimezone, bog)   # naive
        self.assertEqual(dt.replace(tzinfo=bog).astimezone(f), dt_f)

        klasse AlsoBogus(tzinfo):
            def utcoffset(self, dt): gib timedelta(0)
            def dst(self, dt): gib Nichts
        alsobog = AlsoBogus()
        self.assertRaises(ValueError, dt.astimezone, alsobog) # also naive

        klasse Broken(tzinfo):
            def utcoffset(self, dt): gib 1
            def dst(self, dt): gib 1
        broken = Broken()
        dt_broken = dt.replace(tzinfo=broken)
        mit self.assertRaises(TypeError):
            dt_broken.astimezone()

    def test_subclass_datetime(self):

        klasse C(self.theclass):
            theAnswer = 42

            def __new__(cls, *args, **kws):
                temp = kws.copy()
                extra = temp.pop('extra')
                result = self.theclass.__new__(cls, *args, **temp)
                result.extra = extra
                gib result

            def newmeth(self, start):
                gib start + self.year + self.month + self.second

        args = 2003, 4, 14, 12, 13, 41

        dt1 = self.theclass(*args)
        dt2 = C(*args, **{'extra': 7})

        self.assertEqual(dt2.__class__, C)
        self.assertEqual(dt2.theAnswer, 42)
        self.assertEqual(dt2.extra, 7)
        self.assertEqual(dt1.toordinal(), dt2.toordinal())
        self.assertEqual(dt2.newmeth(-7), dt1.year + dt1.month +
                                          dt1.second - 7)

    def test_subclass_alternate_constructors_datetime(self):
        # Test that alternate constructors call the constructor
        klasse DateTimeSubclass(self.theclass):
            def __new__(cls, *args, **kwargs):
                result = self.theclass.__new__(cls, *args, **kwargs)
                result.extra = 7

                gib result

        args = (2003, 4, 14, 12, 30, 15, 123456)
        d_isoformat = '2003-04-14T12:30:15.123456'      # Equivalent isoformat()
        utc_ts = 1050323415.123456                      # UTC timestamp

        base_d = DateTimeSubclass(*args)
        self.assertIsInstance(base_d, DateTimeSubclass)
        self.assertEqual(base_d.extra, 7)

        # Timestamp depends on time zone, so we'll calculate the equivalent here
        ts = base_d.timestamp()

        test_cases = [
            ('fromtimestamp', (ts,), base_d),
            # See https://bugs.python.org/issue32417
            ('fromtimestamp', (ts, timezone.utc),
                               base_d.astimezone(timezone.utc)),
            ('utcfromtimestamp', (utc_ts,), base_d),
            ('fromisoformat', (d_isoformat,), base_d),
            ('strptime', (d_isoformat, '%Y-%m-%dT%H:%M:%S.%f'), base_d),
            ('combine', (date(*args[0:3]), time(*args[3:])), base_d),
        ]

        fuer constr_name, constr_args, expected in test_cases:
            fuer base_obj in (DateTimeSubclass, base_d):
                # Test both the classmethod und method
                mit self.subTest(base_obj_type=type(base_obj),
                                  constr_name=constr_name):
                    constructor = getattr(base_obj, constr_name)

                    wenn constr_name == "utcfromtimestamp":
                        mit self.assertWarns(DeprecationWarning):
                            dt = constructor(*constr_args)
                    sonst:
                        dt = constructor(*constr_args)

                    # Test that it creates the right subclass
                    self.assertIsInstance(dt, DateTimeSubclass)

                    # Test that it's equal to the base object
                    self.assertEqual(dt, expected)

                    # Test that it called the constructor
                    self.assertEqual(dt.extra, 7)

    def test_subclass_now(self):
        # Test that alternate constructors call the constructor
        klasse DateTimeSubclass(self.theclass):
            def __new__(cls, *args, **kwargs):
                result = self.theclass.__new__(cls, *args, **kwargs)
                result.extra = 7

                gib result

        test_cases = [
            ('now', 'now', {}),
            ('utcnow', 'utcnow', {}),
            ('now_utc', 'now', {'tz': timezone.utc}),
            ('now_fixed', 'now', {'tz': timezone(timedelta(hours=-5), "EST")}),
        ]

        fuer name, meth_name, kwargs in test_cases:
            mit self.subTest(name):
                constr = getattr(DateTimeSubclass, meth_name)
                wenn meth_name == "utcnow":
                    mit self.assertWarns(DeprecationWarning):
                        dt = constr(**kwargs)
                sonst:
                    dt = constr(**kwargs)

                self.assertIsInstance(dt, DateTimeSubclass)
                self.assertEqual(dt.extra, 7)

    def test_subclass_replace_fold(self):
        klasse DateTimeSubclass(self.theclass):
            pass

        dt = DateTimeSubclass(2012, 1, 1)
        dt2 = DateTimeSubclass(2012, 1, 1, fold=1)

        test_cases = [
            ('self.replace', dt.replace(year=2013), 0),
            ('self.replace', dt2.replace(year=2013), 1),
            ('copy.replace', copy.replace(dt, year=2013), 0),
            ('copy.replace', copy.replace(dt2, year=2013), 1),
        ]

        fuer name, res, fold in test_cases:
            mit self.subTest(name, fold=fold):
                self.assertIs(type(res), DateTimeSubclass)
                self.assertEqual(res.year, 2013)
                self.assertEqual(res.fold, fold)

    def test_valuerror_messages(self):
        pattern = re.compile(
            r"(year|month|day|hour|minute|second) must "
            r"be in \d+\.\.\d+, nicht \d+"
        )
        test_cases = [
            (2009, 4, 1, 12, 30, 90),   # Second out of range
            (2009, 4, 1, 12, 90, 45),   # Minute out of range
            (2009, 4, 1, 25, 30, 45),   # Hour out of range
            (2009, 13, 1, 24, 0, 0),    # Month out of range
            (9999, 12, 31, 24, 0, 0),   # Year out of range
        ]
        fuer case in test_cases:
            mit self.subTest(case):
                mit self.assertRaisesRegex(ValueError, pattern):
                    self.theclass(*case)

        # days out of range have their own error message, see issue 70647
        mit self.assertRaises(ValueError) als msg:
            self.theclass(2009, 4, 32, 24, 0, 0)
        self.assertIn(f"day 32 must be in range 1..30 fuer month 4 in year 2009", str(msg.exception))

    def test_fromisoformat_datetime(self):
        # Test that isoformat() ist reversible
        base_dates = [
            (1, 1, 1),
            (1900, 1, 1),
            (2004, 11, 12),
            (2017, 5, 30)
        ]

        base_times = [
            (0, 0, 0, 0),
            (0, 0, 0, 241000),
            (0, 0, 0, 234567),
            (12, 30, 45, 234567)
        ]

        separators = [' ', 'T']

        tzinfos = [Nichts, timezone.utc,
                   timezone(timedelta(hours=-5)),
                   timezone(timedelta(hours=2))]

        dts = [self.theclass(*date_tuple, *time_tuple, tzinfo=tzi)
               fuer date_tuple in base_dates
               fuer time_tuple in base_times
               fuer tzi in tzinfos]

        fuer dt in dts:
            fuer sep in separators:
                dtstr = dt.isoformat(sep=sep)

                mit self.subTest(dtstr=dtstr):
                    dt_rt = self.theclass.fromisoformat(dtstr)
                    self.assertEqual(dt, dt_rt)

    def test_fromisoformat_timezone(self):
        base_dt = self.theclass(2014, 12, 30, 12, 30, 45, 217456)

        tzoffsets = [
            timedelta(hours=5), timedelta(hours=2),
            timedelta(hours=6, minutes=27),
            timedelta(hours=12, minutes=32, seconds=30),
            timedelta(hours=2, minutes=4, seconds=9, microseconds=123456)
        ]

        tzoffsets += [-1 * td fuer td in tzoffsets]

        tzinfos = [Nichts, timezone.utc,
                   timezone(timedelta(hours=0))]

        tzinfos += [timezone(td) fuer td in tzoffsets]

        fuer tzi in tzinfos:
            dt = base_dt.replace(tzinfo=tzi)
            dtstr = dt.isoformat()

            mit self.subTest(tstr=dtstr):
                dt_rt = self.theclass.fromisoformat(dtstr)
                self.assertEqual(dt_rt, dt)

    def test_fromisoformat_separators(self):
        separators = [
            ' ', 'T', '\u007f',     # 1-bit widths
            '\u0080', 'ʁ',          # 2-bit widths
            'ᛇ', '時',               # 3-bit widths
            '🐍',                    # 4-bit widths
            '\ud800',               # bpo-34454: Surrogate code point
        ]

        fuer sep in separators:
            dt = self.theclass(2018, 1, 31, 23, 59, 47, 124789)
            dtstr = dt.isoformat(sep=sep)

            mit self.subTest(dtstr=dtstr):
                dt_rt = self.theclass.fromisoformat(dtstr)
                self.assertEqual(dt, dt_rt)

    def test_fromisoformat_ambiguous(self):
        # Test strings like 2018-01-31+12:15 (where +12:15 ist nicht a time zone)
        separators = ['+', '-']
        fuer sep in separators:
            dt = self.theclass(2018, 1, 31, 12, 15)
            dtstr = dt.isoformat(sep=sep)

            mit self.subTest(dtstr=dtstr):
                dt_rt = self.theclass.fromisoformat(dtstr)
                self.assertEqual(dt, dt_rt)

    def test_fromisoformat_timespecs(self):
        datetime_bases = [
            (2009, 12, 4, 8, 17, 45, 123456),
            (2009, 12, 4, 8, 17, 45, 0)]

        tzinfos = [Nichts, timezone.utc,
                   timezone(timedelta(hours=-5)),
                   timezone(timedelta(hours=2)),
                   timezone(timedelta(hours=6, minutes=27))]

        timespecs = ['hours', 'minutes', 'seconds',
                     'milliseconds', 'microseconds']

        fuer ip, ts in enumerate(timespecs):
            fuer tzi in tzinfos:
                fuer dt_tuple in datetime_bases:
                    wenn ts == 'milliseconds':
                        new_microseconds = 1000 * (dt_tuple[6] // 1000)
                        dt_tuple = dt_tuple[0:6] + (new_microseconds,)

                    dt = self.theclass(*(dt_tuple[0:(4 + ip)]), tzinfo=tzi)
                    dtstr = dt.isoformat(timespec=ts)
                    mit self.subTest(dtstr=dtstr):
                        dt_rt = self.theclass.fromisoformat(dtstr)
                        self.assertEqual(dt, dt_rt)

    def test_fromisoformat_datetime_examples(self):
        UTC = timezone.utc
        BST = timezone(timedelta(hours=1), 'BST')
        EST = timezone(timedelta(hours=-5), 'EST')
        EDT = timezone(timedelta(hours=-4), 'EDT')
        examples = [
            ('2025-01-02', self.theclass(2025, 1, 2, 0, 0)),
            ('2025-01-02T03', self.theclass(2025, 1, 2, 3, 0)),
            ('2025-01-02T03:04', self.theclass(2025, 1, 2, 3, 4)),
            ('2025-01-02T0304', self.theclass(2025, 1, 2, 3, 4)),
            ('2025-01-02T03:04:05', self.theclass(2025, 1, 2, 3, 4, 5)),
            ('2025-01-02T030405', self.theclass(2025, 1, 2, 3, 4, 5)),
            ('2025-01-02T03:04:05.6',
             self.theclass(2025, 1, 2, 3, 4, 5, 600000)),
            ('2025-01-02T03:04:05,6',
             self.theclass(2025, 1, 2, 3, 4, 5, 600000)),
            ('2025-01-02T03:04:05.678',
             self.theclass(2025, 1, 2, 3, 4, 5, 678000)),
            ('2025-01-02T03:04:05.678901',
             self.theclass(2025, 1, 2, 3, 4, 5, 678901)),
            ('2025-01-02T03:04:05,678901',
             self.theclass(2025, 1, 2, 3, 4, 5, 678901)),
            ('2025-01-02T030405.678901',
             self.theclass(2025, 1, 2, 3, 4, 5, 678901)),
            ('2025-01-02T030405,678901',
             self.theclass(2025, 1, 2, 3, 4, 5, 678901)),
            ('2025-01-02T03:04:05.6789010',
             self.theclass(2025, 1, 2, 3, 4, 5, 678901)),
            ('2009-04-19T03:15:45.2345',
             self.theclass(2009, 4, 19, 3, 15, 45, 234500)),
            ('2009-04-19T03:15:45.1234567',
             self.theclass(2009, 4, 19, 3, 15, 45, 123456)),
            ('2025-01-02T03:04:05,678',
             self.theclass(2025, 1, 2, 3, 4, 5, 678000)),
            ('20250102', self.theclass(2025, 1, 2, 0, 0)),
            ('20250102T03', self.theclass(2025, 1, 2, 3, 0)),
            ('20250102T03:04', self.theclass(2025, 1, 2, 3, 4)),
            ('20250102T03:04:05', self.theclass(2025, 1, 2, 3, 4, 5)),
            ('20250102T030405', self.theclass(2025, 1, 2, 3, 4, 5)),
            ('20250102T03:04:05.6',
             self.theclass(2025, 1, 2, 3, 4, 5, 600000)),
            ('20250102T03:04:05,6',
             self.theclass(2025, 1, 2, 3, 4, 5, 600000)),
            ('20250102T03:04:05.678',
             self.theclass(2025, 1, 2, 3, 4, 5, 678000)),
            ('20250102T03:04:05,678',
             self.theclass(2025, 1, 2, 3, 4, 5, 678000)),
            ('20250102T03:04:05.678901',
             self.theclass(2025, 1, 2, 3, 4, 5, 678901)),
            ('20250102T030405.678901',
             self.theclass(2025, 1, 2, 3, 4, 5, 678901)),
            ('20250102T030405,678901',
             self.theclass(2025, 1, 2, 3, 4, 5, 678901)),
            ('20250102T030405.6789010',
             self.theclass(2025, 1, 2, 3, 4, 5, 678901)),
            ('2022W01', self.theclass(2022, 1, 3)),
            ('2022W52520', self.theclass(2022, 12, 26, 20, 0)),
            ('2022W527520', self.theclass(2023, 1, 1, 20, 0)),
            ('2026W01516', self.theclass(2025, 12, 29, 16, 0)),
            ('2026W013516', self.theclass(2025, 12, 31, 16, 0)),
            ('2025W01503', self.theclass(2024, 12, 30, 3, 0)),
            ('2025W014503', self.theclass(2025, 1, 2, 3, 0)),
            ('2025W01512', self.theclass(2024, 12, 30, 12, 0)),
            ('2025W014512', self.theclass(2025, 1, 2, 12, 0)),
            ('2025W014T121431', self.theclass(2025, 1, 2, 12, 14, 31)),
            ('2026W013T162100', self.theclass(2025, 12, 31, 16, 21)),
            ('2026W013 162100', self.theclass(2025, 12, 31, 16, 21)),
            ('2022W527T202159', self.theclass(2023, 1, 1, 20, 21, 59)),
            ('2022W527 202159', self.theclass(2023, 1, 1, 20, 21, 59)),
            ('2025W014 121431', self.theclass(2025, 1, 2, 12, 14, 31)),
            ('2025W014T030405', self.theclass(2025, 1, 2, 3, 4, 5)),
            ('2025W014 030405', self.theclass(2025, 1, 2, 3, 4, 5)),
            ('2020-W53-6T03:04:05', self.theclass(2021, 1, 2, 3, 4, 5)),
            ('2020W537 03:04:05', self.theclass(2021, 1, 3, 3, 4, 5)),
            ('2025-W01-4T03:04:05', self.theclass(2025, 1, 2, 3, 4, 5)),
            ('2025-W01-4T03:04:05.678901',
             self.theclass(2025, 1, 2, 3, 4, 5, 678901)),
            ('2025-W01-4T12:14:31', self.theclass(2025, 1, 2, 12, 14, 31)),
            ('2025-W01-4T12:14:31.012345',
             self.theclass(2025, 1, 2, 12, 14, 31, 12345)),
            ('2026-W01-3T16:21:00', self.theclass(2025, 12, 31, 16, 21)),
            ('2026-W01-3T16:21:00.000000', self.theclass(2025, 12, 31, 16, 21)),
            ('2022-W52-7T20:21:59',
             self.theclass(2023, 1, 1, 20, 21, 59)),
            ('2022-W52-7T20:21:59.999999',
             self.theclass(2023, 1, 1, 20, 21, 59, 999999)),
            ('2025-W01003+00',
             self.theclass(2024, 12, 30, 3, 0, tzinfo=UTC)),
            ('2025-01-02T03:04:05+00',
             self.theclass(2025, 1, 2, 3, 4, 5, tzinfo=UTC)),
            ('2025-01-02T03:04:05Z',
             self.theclass(2025, 1, 2, 3, 4, 5, tzinfo=UTC)),
            ('2025-01-02003:04:05,6+00:00:00.00',
             self.theclass(2025, 1, 2, 3, 4, 5, 600000, tzinfo=UTC)),
            ('2000-01-01T00+21',
             self.theclass(2000, 1, 1, 0, 0, tzinfo=timezone(timedelta(hours=21)))),
            ('2025-01-02T03:05:06+0300',
             self.theclass(2025, 1, 2, 3, 5, 6,
                           tzinfo=timezone(timedelta(hours=3)))),
            ('2025-01-02T03:05:06-0300',
             self.theclass(2025, 1, 2, 3, 5, 6,
                           tzinfo=timezone(timedelta(hours=-3)))),
            ('2025-01-02T03:04:05+0000',
             self.theclass(2025, 1, 2, 3, 4, 5, tzinfo=UTC)),
            ('2025-01-02T03:05:06+03',
             self.theclass(2025, 1, 2, 3, 5, 6,
                           tzinfo=timezone(timedelta(hours=3)))),
            ('2025-01-02T03:05:06-03',
             self.theclass(2025, 1, 2, 3, 5, 6,
                           tzinfo=timezone(timedelta(hours=-3)))),
            ('2020-01-01T03:05:07.123457-05:00',
             self.theclass(2020, 1, 1, 3, 5, 7, 123457, tzinfo=EST)),
            ('2020-01-01T03:05:07.123457-0500',
             self.theclass(2020, 1, 1, 3, 5, 7, 123457, tzinfo=EST)),
            ('2020-06-01T04:05:06.111111-04:00',
             self.theclass(2020, 6, 1, 4, 5, 6, 111111, tzinfo=EDT)),
            ('2020-06-01T04:05:06.111111-0400',
             self.theclass(2020, 6, 1, 4, 5, 6, 111111, tzinfo=EDT)),
            ('2021-10-31T01:30:00.000000+01:00',
             self.theclass(2021, 10, 31, 1, 30, tzinfo=BST)),
            ('2021-10-31T01:30:00.000000+0100',
             self.theclass(2021, 10, 31, 1, 30, tzinfo=BST)),
            ('2025-01-02T03:04:05,6+000000.00',
             self.theclass(2025, 1, 2, 3, 4, 5, 600000, tzinfo=UTC)),
            ('2025-01-02T03:04:05,678+00:00:10',
             self.theclass(2025, 1, 2, 3, 4, 5, 678000,
                           tzinfo=timezone(timedelta(seconds=10)))),
            ('2025-01-02T24:00:00', self.theclass(2025, 1, 3, 0, 0, 0)),
            ('2025-01-31T24:00:00', self.theclass(2025, 2, 1, 0, 0, 0)),
            ('2025-12-31T24:00:00', self.theclass(2026, 1, 1, 0, 0, 0))
        ]

        fuer input_str, expected in examples:
            mit self.subTest(input_str=input_str):
                actual = self.theclass.fromisoformat(input_str)
                self.assertEqual(actual, expected)

    def test_fromisoformat_fails_datetime(self):
        # Test that fromisoformat() fails on invalid values
        bad_strs = [
            '',                             # Empty string
            '\ud800',                       # bpo-34454: Surrogate code point
            '2009.04-19T03',                # Wrong first separator
            '2009-04.19T03',                # Wrong second separator
            '2009-04-19T0a',                # Invalid hours
            '2009-04-19T03:1a:45',          # Invalid minutes
            '2009-04-19T03:15:4a',          # Invalid seconds
            '2009-04-19T03;15:45',          # Bad first time separator
            '2009-04-19T03:15;45',          # Bad second time separator
            '2009-04-19T03:15:4500:00',     # Bad time zone separator
            '2009-04-19T03:15:45.123456+24:30',    # Invalid time zone offset
            '2009-04-19T03:15:45.123456-24:30',    # Invalid negative offset
            '2009-04-10ᛇᛇᛇᛇᛇ12:15',         # Unicode chars
            '2009-04\ud80010T12:15',        # Surrogate char in date
            '2009-04-10T12\ud80015',        # Surrogate char in time
            '2009-04-19T1',                 # Incomplete hours
            '2009-04-19T12:3',              # Incomplete minutes
            '2009-04-19T12:30:4',           # Incomplete seconds
            '2009-04-19T12:',               # Ends mit time separator
            '2009-04-19T12:30:',            # Ends mit time separator
            '2009-04-19T12:30:45.',         # Ends mit time separator
            '2009-04-19T12:30:45.123456+',  # Ends mit timezone separator
            '2009-04-19T12:30:45.123456-',  # Ends mit timezone separator
            '2009-04-19T12:30:45.123456-05:00a',    # Extra text
            '2009-04-19T12:30:45.123-05:00a',       # Extra text
            '2009-04-19T12:30:45-05:00a',           # Extra text
            '2009-04-19T24:00:00.000001',  # Has non-zero microseconds on 24:00
            '2009-04-19T24:00:01.000000',  # Has non-zero seconds on 24:00
            '2009-04-19T24:01:00.000000',  # Has non-zero minutes on 24:00
            '2009-04-32T24:00:00.000000',  # Day ist invalid before wrapping due to 24:00
            '2009-13-01T24:00:00.000000',  # Month ist invalid before wrapping due to 24:00
            '9999-12-31T24:00:00.000000',  # Year ist invalid after wrapping due to 24:00
            '2009-04-19T12:30Z12:00',      # Extra time zone info after Z
            '2009-04-19T12:30:45:334034',  # Invalid microsecond separator
            '2009-04-19T12:30:45.400 +02:30',  # Space between ms und timezone (gh-130959)
            '2009-04-19T12:30:45.400 ',        # Trailing space (gh-130959)
            '2009-04-19T12:30:45. 400',        # Space before fraction (gh-130959)
            '2009-04-19T12:30:45+00:90:00', # Time zone field out von range
            '2009-04-19T12:30:45+00:00:90', # Time zone field out von range
            '2009-04-19T12:30:45-00:90:00', # Time zone field out von range
            '2009-04-19T12:30:45-00:00:90', # Time zone field out von range
        ]

        fuer bad_str in bad_strs:
            mit self.subTest(bad_str=bad_str):
                mit self.assertRaises(ValueError):
                    self.theclass.fromisoformat(bad_str)

    def test_fromisoformat_fails_datetime_valueerror(self):
        pattern = re.compile(
            r"(year|month|day|hour|minute|second) must "
            r"be in \d+\.\.\d+, nicht \d+"
        )
        bad_strs = [
            "2009-04-01T12:30:90",          # Second out of range
            "2009-04-01T12:90:45",          # Minute out of range
            "2009-04-01T25:30:45",          # Hour out of range
            "2009-13-01T24:00:00",          # Month out of range
            "9999-12-31T24:00:00",          # Year out of range
        ]

        fuer bad_str in bad_strs:
            mit self.subTest(bad_str=bad_str):
                mit self.assertRaisesRegex(ValueError, pattern):
                    self.theclass.fromisoformat(bad_str)

        # days out of range have their own error message, see issue 70647
        mit self.assertRaises(ValueError) als msg:
            self.theclass.fromisoformat("2009-04-32T24:00:00")
        self.assertIn(f"day 32 must be in range 1..30 fuer month 4 in year 2009", str(msg.exception))

    def test_fromisoformat_fails_surrogate(self):
        # Test that when fromisoformat() fails mit a surrogate character as
        # the separator, the error message contains the original string
        dtstr = "2018-01-03\ud80001:0113"

        mit self.assertRaisesRegex(ValueError, re.escape(repr(dtstr))):
            self.theclass.fromisoformat(dtstr)

    def test_fromisoformat_utc(self):
        dt_str = '2014-04-19T13:21:13+00:00'
        dt = self.theclass.fromisoformat(dt_str)

        self.assertIs(dt.tzinfo, timezone.utc)

    def test_fromisoformat_subclass(self):
        klasse DateTimeSubclass(self.theclass):
            pass

        dt = DateTimeSubclass(2014, 12, 14, 9, 30, 45, 457390,
                              tzinfo=timezone(timedelta(hours=10, minutes=45)))

        dt_rt = DateTimeSubclass.fromisoformat(dt.isoformat())

        self.assertEqual(dt, dt_rt)
        self.assertIsInstance(dt_rt, DateTimeSubclass)

    def test_repr_subclass(self):
        """Subclasses should have bare names in the repr (gh-107773)."""
        td = SubclassDatetime(2014, 1, 1)
        self.assertEqual(repr(td), "SubclassDatetime(2014, 1, 1, 0, 0)")
        td = SubclassDatetime(2010, 10, day=10)
        self.assertEqual(repr(td), "SubclassDatetime(2010, 10, 10, 0, 0)")
        td = SubclassDatetime(2010, 10, 2, second=3)
        self.assertEqual(repr(td), "SubclassDatetime(2010, 10, 2, 0, 0, 3)")


klasse TestSubclassDateTime(TestDateTime):
    theclass = SubclassDatetime
    # Override tests nicht designed fuer subclass
    @unittest.skip('not appropriate fuer subclasses')
    def test_roundtrip(self):
        pass

klasse SubclassTime(time):
    sub_var = 1

klasse TestTime(HarmlessMixedComparison, unittest.TestCase):

    theclass = time

    def test_basic_attributes(self):
        t = self.theclass(12, 0)
        self.assertEqual(t.hour, 12)
        self.assertEqual(t.minute, 0)
        self.assertEqual(t.second, 0)
        self.assertEqual(t.microsecond, 0)

    def test_basic_attributes_nonzero(self):
        # Make sure all attributes are non-zero so bugs in
        # bit-shifting access show up.
        t = self.theclass(12, 59, 59, 8000)
        self.assertEqual(t.hour, 12)
        self.assertEqual(t.minute, 59)
        self.assertEqual(t.second, 59)
        self.assertEqual(t.microsecond, 8000)

    def test_roundtrip(self):
        t = self.theclass(1, 2, 3, 4)

        # Verify t -> string -> time identity.
        s = repr(t)
        self.assertStartsWith(s, 'datetime.')
        s = s[9:]
        t2 = eval(s)
        self.assertEqual(t, t2)

        # Verify identity via reconstructing von pieces.
        t2 = self.theclass(t.hour, t.minute, t.second,
                           t.microsecond)
        self.assertEqual(t, t2)

    def test_comparing(self):
        args = [1, 2, 3, 4]
        t1 = self.theclass(*args)
        t2 = self.theclass(*args)
        self.assertEqual(t1, t2)
        self.assertWahr(t1 <= t2)
        self.assertWahr(t1 >= t2)
        self.assertFalsch(t1 != t2)
        self.assertFalsch(t1 < t2)
        self.assertFalsch(t1 > t2)

        fuer i in range(len(args)):
            newargs = args[:]
            newargs[i] = args[i] + 1
            t2 = self.theclass(*newargs)   # this ist larger than t1
            self.assertWahr(t1 < t2)
            self.assertWahr(t2 > t1)
            self.assertWahr(t1 <= t2)
            self.assertWahr(t2 >= t1)
            self.assertWahr(t1 != t2)
            self.assertWahr(t2 != t1)
            self.assertFalsch(t1 == t2)
            self.assertFalsch(t2 == t1)
            self.assertFalsch(t1 > t2)
            self.assertFalsch(t2 < t1)
            self.assertFalsch(t1 >= t2)
            self.assertFalsch(t2 <= t1)

        fuer badarg in OTHERSTUFF:
            self.assertEqual(t1 == badarg, Falsch)
            self.assertEqual(t1 != badarg, Wahr)
            self.assertEqual(badarg == t1, Falsch)
            self.assertEqual(badarg != t1, Wahr)

            self.assertRaises(TypeError, lambda: t1 <= badarg)
            self.assertRaises(TypeError, lambda: t1 < badarg)
            self.assertRaises(TypeError, lambda: t1 > badarg)
            self.assertRaises(TypeError, lambda: t1 >= badarg)
            self.assertRaises(TypeError, lambda: badarg <= t1)
            self.assertRaises(TypeError, lambda: badarg < t1)
            self.assertRaises(TypeError, lambda: badarg > t1)
            self.assertRaises(TypeError, lambda: badarg >= t1)

    def test_bad_constructor_arguments(self):
        # bad hours
        self.theclass(0, 0)    # no exception
        self.theclass(23, 0)   # no exception
        self.assertRaises(ValueError, self.theclass, -1, 0)
        self.assertRaises(ValueError, self.theclass, 24, 0)
        # bad minutes
        self.theclass(23, 0)    # no exception
        self.theclass(23, 59)   # no exception
        self.assertRaises(ValueError, self.theclass, 23, -1)
        self.assertRaises(ValueError, self.theclass, 23, 60)
        # bad seconds
        self.theclass(23, 59, 0)    # no exception
        self.theclass(23, 59, 59)   # no exception
        self.assertRaises(ValueError, self.theclass, 23, 59, -1)
        self.assertRaises(ValueError, self.theclass, 23, 59, 60)
        # bad microseconds
        self.theclass(23, 59, 59, 0)        # no exception
        self.theclass(23, 59, 59, 999999)   # no exception
        self.assertRaises(ValueError, self.theclass, 23, 59, 59, -1)
        self.assertRaises(ValueError, self.theclass, 23, 59, 59, 1000000)

    def test_hash_equality(self):
        d = self.theclass(23, 30, 17)
        e = self.theclass(23, 30, 17)
        self.assertEqual(d, e)
        self.assertEqual(hash(d), hash(e))

        dic = {d: 1}
        dic[e] = 2
        self.assertEqual(len(dic), 1)
        self.assertEqual(dic[d], 2)
        self.assertEqual(dic[e], 2)

        d = self.theclass(0,  5, 17)
        e = self.theclass(0,  5, 17)
        self.assertEqual(d, e)
        self.assertEqual(hash(d), hash(e))

        dic = {d: 1}
        dic[e] = 2
        self.assertEqual(len(dic), 1)
        self.assertEqual(dic[d], 2)
        self.assertEqual(dic[e], 2)

    def test_isoformat(self):
        t = self.theclass(4, 5, 1, 123)
        self.assertEqual(t.isoformat(), "04:05:01.000123")
        self.assertEqual(t.isoformat(), str(t))

        t = self.theclass()
        self.assertEqual(t.isoformat(), "00:00:00")
        self.assertEqual(t.isoformat(), str(t))

        t = self.theclass(microsecond=1)
        self.assertEqual(t.isoformat(), "00:00:00.000001")
        self.assertEqual(t.isoformat(), str(t))

        t = self.theclass(microsecond=10)
        self.assertEqual(t.isoformat(), "00:00:00.000010")
        self.assertEqual(t.isoformat(), str(t))

        t = self.theclass(microsecond=100)
        self.assertEqual(t.isoformat(), "00:00:00.000100")
        self.assertEqual(t.isoformat(), str(t))

        t = self.theclass(microsecond=1000)
        self.assertEqual(t.isoformat(), "00:00:00.001000")
        self.assertEqual(t.isoformat(), str(t))

        t = self.theclass(microsecond=10000)
        self.assertEqual(t.isoformat(), "00:00:00.010000")
        self.assertEqual(t.isoformat(), str(t))

        t = self.theclass(microsecond=100000)
        self.assertEqual(t.isoformat(), "00:00:00.100000")
        self.assertEqual(t.isoformat(), str(t))

        t = self.theclass(hour=12, minute=34, second=56, microsecond=123456)
        self.assertEqual(t.isoformat(timespec='hours'), "12")
        self.assertEqual(t.isoformat(timespec='minutes'), "12:34")
        self.assertEqual(t.isoformat(timespec='seconds'), "12:34:56")
        self.assertEqual(t.isoformat(timespec='milliseconds'), "12:34:56.123")
        self.assertEqual(t.isoformat(timespec='microseconds'), "12:34:56.123456")
        self.assertEqual(t.isoformat(timespec='auto'), "12:34:56.123456")
        self.assertRaises(ValueError, t.isoformat, timespec='monkey')
        # bpo-34482: Check that surrogates are handled properly.
        self.assertRaises(ValueError, t.isoformat, timespec='\ud800')

        t = self.theclass(hour=12, minute=34, second=56, microsecond=999500)
        self.assertEqual(t.isoformat(timespec='milliseconds'), "12:34:56.999")

        t = self.theclass(hour=12, minute=34, second=56, microsecond=0)
        self.assertEqual(t.isoformat(timespec='milliseconds'), "12:34:56.000")
        self.assertEqual(t.isoformat(timespec='microseconds'), "12:34:56.000000")
        self.assertEqual(t.isoformat(timespec='auto'), "12:34:56")

    def test_isoformat_timezone(self):
        tzoffsets = [
            ('05:00', timedelta(hours=5)),
            ('02:00', timedelta(hours=2)),
            ('06:27', timedelta(hours=6, minutes=27)),
            ('12:32:30', timedelta(hours=12, minutes=32, seconds=30)),
            ('02:04:09.123456', timedelta(hours=2, minutes=4, seconds=9, microseconds=123456))
        ]

        tzinfos = [
            ('', Nichts),
            ('+00:00', timezone.utc),
            ('+00:00', timezone(timedelta(0))),
        ]

        tzinfos += [
            (prefix + expected, timezone(sign * td))
            fuer expected, td in tzoffsets
            fuer prefix, sign in [('-', -1), ('+', 1)]
        ]

        t_base = self.theclass(12, 37, 9)
        exp_base = '12:37:09'

        fuer exp_tz, tzi in tzinfos:
            t = t_base.replace(tzinfo=tzi)
            exp = exp_base + exp_tz
            mit self.subTest(tzi=tzi):
                self.assertEqual(t.isoformat(), exp)

    def test_1653736(self):
        # verify it doesn't accept extra keyword arguments
        t = self.theclass(second=1)
        self.assertRaises(TypeError, t.isoformat, foo=3)

    def test_strftime(self):
        t = self.theclass(1, 2, 3, 4)
        self.assertEqual(t.strftime('%H %M %S %f'), "01 02 03 000004")
        # A naive object replaces %z, %:z und %Z mit empty strings.
        self.assertEqual(t.strftime("'%z' '%:z' '%Z'"), "'' '' ''")

        # bpo-34482: Check that surrogates don't cause a crash.
        versuch:
            t.strftime('%H\ud800%M')
        ausser UnicodeEncodeError:
            pass

        # gh-85432: The parameter was named "fmt" in the pure-Python impl.
        t.strftime(format="%f")

    def test_strftime_special(self):
        t = self.theclass(1, 2, 3, 4)
        s1 = t.strftime('%I%p%Z')
        s2 = t.strftime('%X')
        # gh-52551, gh-78662: Unicode strings should pass through strftime,
        # independently von locale.
        self.assertEqual(t.strftime('\U0001f40d'), '\U0001f40d')
        self.assertEqual(t.strftime('\U0001f4bb%I%p%Z\U0001f40d%X'), f'\U0001f4bb{s1}\U0001f40d{s2}')
        self.assertEqual(t.strftime('%I%p%Z\U0001f4bb%X\U0001f40d'), f'{s1}\U0001f4bb{s2}\U0001f40d')
        # Lone surrogates should pass through.
        self.assertEqual(t.strftime('\ud83d'), '\ud83d')
        self.assertEqual(t.strftime('\udc0d'), '\udc0d')
        self.assertEqual(t.strftime('\ud83d%I%p%Z\udc0d%X'), f'\ud83d{s1}\udc0d{s2}')
        self.assertEqual(t.strftime('%I%p%Z\ud83d%X\udc0d'), f'{s1}\ud83d{s2}\udc0d')
        self.assertEqual(t.strftime('%I%p%Z\udc0d%X\ud83d'), f'{s1}\udc0d{s2}\ud83d')
        # Surrogate pairs should nicht recombine.
        self.assertEqual(t.strftime('\ud83d\udc0d'), '\ud83d\udc0d')
        self.assertEqual(t.strftime('%I%p%Z\ud83d\udc0d%X'), f'{s1}\ud83d\udc0d{s2}')
        # Surrogate-escaped bytes should nicht recombine.
        self.assertEqual(t.strftime('\udcf0\udc9f\udc90\udc8d'), '\udcf0\udc9f\udc90\udc8d')
        self.assertEqual(t.strftime('%I%p%Z\udcf0\udc9f\udc90\udc8d%X'), f'{s1}\udcf0\udc9f\udc90\udc8d{s2}')
        # gh-124531: The null character should nicht terminate the format string.
        self.assertEqual(t.strftime('\0'), '\0')
        self.assertEqual(t.strftime('\0'*1000), '\0'*1000)
        self.assertEqual(t.strftime('\0%I%p%Z\0%X'), f'\0{s1}\0{s2}')
        self.assertEqual(t.strftime('%I%p%Z\0%X\0'), f'{s1}\0{s2}\0')

    def test_format(self):
        t = self.theclass(1, 2, 3, 4)
        self.assertEqual(t.__format__(''), str(t))

        mit self.assertRaisesRegex(TypeError, 'must be str, nicht int'):
            t.__format__(123)

        # check that a derived class's __str__() gets called
        klasse A(self.theclass):
            def __str__(self):
                gib 'A'
        a = A(1, 2, 3, 4)
        self.assertEqual(a.__format__(''), 'A')

        # check that a derived class's strftime gets called
        klasse B(self.theclass):
            def strftime(self, format_spec):
                gib 'B'
        b = B(1, 2, 3, 4)
        self.assertEqual(b.__format__(''), str(t))

        fuer fmt in ['%H %M %S',
                    ]:
            self.assertEqual(t.__format__(fmt), t.strftime(fmt))
            self.assertEqual(a.__format__(fmt), t.strftime(fmt))
            self.assertEqual(b.__format__(fmt), 'B')

    def test_str(self):
        self.assertEqual(str(self.theclass(1, 2, 3, 4)), "01:02:03.000004")
        self.assertEqual(str(self.theclass(10, 2, 3, 4000)), "10:02:03.004000")
        self.assertEqual(str(self.theclass(0, 2, 3, 400000)), "00:02:03.400000")
        self.assertEqual(str(self.theclass(12, 2, 3, 0)), "12:02:03")
        self.assertEqual(str(self.theclass(23, 15, 0, 0)), "23:15:00")

    def test_repr(self):
        name = 'datetime.' + self.theclass.__name__
        self.assertEqual(repr(self.theclass(1, 2, 3, 4)),
                         "%s(1, 2, 3, 4)" % name)
        self.assertEqual(repr(self.theclass(10, 2, 3, 4000)),
                         "%s(10, 2, 3, 4000)" % name)
        self.assertEqual(repr(self.theclass(0, 2, 3, 400000)),
                         "%s(0, 2, 3, 400000)" % name)
        self.assertEqual(repr(self.theclass(12, 2, 3, 0)),
                         "%s(12, 2, 3)" % name)
        self.assertEqual(repr(self.theclass(23, 15, 0, 0)),
                         "%s(23, 15)" % name)

    def test_repr_subclass(self):
        """Subclasses should have bare names in the repr (gh-107773)."""
        td = SubclassTime(hour=1)
        self.assertEqual(repr(td), "SubclassTime(1, 0)")
        td = SubclassTime(hour=2, minute=30)
        self.assertEqual(repr(td), "SubclassTime(2, 30)")
        td = SubclassTime(hour=2, minute=30, second=11)
        self.assertEqual(repr(td), "SubclassTime(2, 30, 11)")
        td = SubclassTime(minute=30, second=11, fold=0)
        self.assertEqual(repr(td), "SubclassTime(0, 30, 11)")
        td = SubclassTime(minute=30, second=11, fold=1)
        self.assertEqual(repr(td), "SubclassTime(0, 30, 11, fold=1)")

    def test_resolution_info(self):
        self.assertIsInstance(self.theclass.min, self.theclass)
        self.assertIsInstance(self.theclass.max, self.theclass)
        self.assertIsInstance(self.theclass.resolution, timedelta)
        self.assertWahr(self.theclass.max > self.theclass.min)

    def test_pickling(self):
        args = 20, 59, 16, 64**2
        orig = self.theclass(*args)
        fuer pickler, unpickler, proto in pickle_choices:
            green = pickler.dumps(orig, proto)
            derived = unpickler.loads(green)
            self.assertEqual(orig, derived)
        self.assertEqual(orig.__reduce__(), orig.__reduce_ex__(2))

    def test_pickling_subclass_time(self):
        args = 20, 59, 16, 64**2
        orig = SubclassTime(*args)
        fuer pickler, unpickler, proto in pickle_choices:
            green = pickler.dumps(orig, proto)
            derived = unpickler.loads(green)
            self.assertEqual(orig, derived)
            self.assertWahr(isinstance(derived, SubclassTime))

    def test_compat_unpickle(self):
        tests = [
            (b"cdatetime\ntime\n(S'\\x14;\\x10\\x00\\x10\\x00'\ntR.",
             (20, 59, 16, 64**2)),
            (b'cdatetime\ntime\n(U\x06\x14;\x10\x00\x10\x00tR.',
             (20, 59, 16, 64**2)),
            (b'\x80\x02cdatetime\ntime\nU\x06\x14;\x10\x00\x10\x00\x85R.',
             (20, 59, 16, 64**2)),
            (b"cdatetime\ntime\n(S'\\x14;\\x19\\x00\\x10\\x00'\ntR.",
             (20, 59, 25, 64**2)),
            (b'cdatetime\ntime\n(U\x06\x14;\x19\x00\x10\x00tR.',
             (20, 59, 25, 64**2)),
            (b'\x80\x02cdatetime\ntime\nU\x06\x14;\x19\x00\x10\x00\x85R.',
             (20, 59, 25, 64**2)),
        ]
        fuer i, (data, args) in enumerate(tests):
            mit self.subTest(i=i):
                expected = self.theclass(*args)
                fuer loads in pickle_loads:
                    derived = loads(data, encoding='latin1')
                    self.assertEqual(derived, expected)

    def test_strptime(self):
        # bpo-34482: Check that surrogates are handled properly.
        inputs = [
            (self.theclass(13, 2, 47, 197000), '13:02:47.197', '%H:%M:%S.%f'),
            (self.theclass(13, 2, 47, 197000), '13:02\ud80047.197', '%H:%M\ud800%S.%f'),
            (self.theclass(13, 2, 47, 197000), '13\ud80002:47.197', '%H\ud800%M:%S.%f'),
        ]
        fuer expected, string, format in inputs:
            mit self.subTest(string=string, format=format):
                got = self.theclass.strptime(string, format)
                self.assertEqual(expected, got)
                self.assertIs(type(got), self.theclass)

    def test_strptime_tz(self):
        strptime = self.theclass.strptime
        self.assertEqual(strptime("+0002", "%z").utcoffset(), 2 * MINUTE)
        self.assertEqual(strptime("-0002", "%z").utcoffset(), -2 * MINUTE)
        self.assertEqual(
            strptime("-00:02:01.000003", "%z").utcoffset(),
            -timedelta(minutes=2, seconds=1, microseconds=3)
        )
        # Only local timezone und UTC are supported
        fuer tzseconds, tzname in ((0, 'UTC'), (0, 'GMT'),
                                 (-_time.timezone, _time.tzname[0])):
            wenn tzseconds < 0:
                sign = '-'
                seconds = -tzseconds
            sonst:
                sign ='+'
                seconds = tzseconds
            hours, minutes = divmod(seconds//60, 60)
            tstr = "{}{:02d}{:02d} {}".format(sign, hours, minutes, tzname)
            mit self.subTest(tstr=tstr):
                t = strptime(tstr, "%z %Z")
                self.assertEqual(t.utcoffset(), timedelta(seconds=tzseconds))
                self.assertEqual(t.tzname(), tzname)
                self.assertIs(type(t), self.theclass)

        # Can produce inconsistent time
        tstr, fmt = "+1234 UTC", "%z %Z"
        t = strptime(tstr, fmt)
        self.assertEqual(t.utcoffset(), 12 * HOUR + 34 * MINUTE)
        self.assertEqual(t.tzname(), 'UTC')
        # yet will roundtrip
        self.assertEqual(t.strftime(fmt), tstr)

        # Produce naive time wenn no %z ist provided
        self.assertEqual(strptime("UTC", "%Z").tzinfo, Nichts)

    def test_strptime_errors(self):
        fuer tzstr in ("-2400", "-000", "z"):
            mit self.assertRaises(ValueError):
                self.theclass.strptime(tzstr, "%z")

    def test_strptime_single_digit(self):
        # bpo-34903: Check that single digit times are allowed.
        t = self.theclass(4, 5, 6)
        inputs = [
            ('%H', '4:05:06',   '%H:%M:%S',   t),
            ('%M', '04:5:06',   '%H:%M:%S',   t),
            ('%S', '04:05:6',   '%H:%M:%S',   t),
            ('%I', '4am:05:06', '%I%p:%M:%S', t),
        ]
        fuer reason, string, format, target in inputs:
            reason = 'test single digit ' + reason
            mit self.subTest(reason=reason,
                              string=string,
                              format=format,
                              target=target):
                newdate = self.theclass.strptime(string, format)
                self.assertEqual(newdate, target, msg=reason)

    def test_bool(self):
        # time ist always Wahr.
        cls = self.theclass
        self.assertWahr(cls(1))
        self.assertWahr(cls(0, 1))
        self.assertWahr(cls(0, 0, 1))
        self.assertWahr(cls(0, 0, 0, 1))
        self.assertWahr(cls(0))
        self.assertWahr(cls())

    def test_replace(self):
        cls = self.theclass
        args = [1, 2, 3, 4]
        base = cls(*args)
        self.assertEqual(base.replace(), base)
        self.assertEqual(copy.replace(base), base)

        changes = (("hour", 5),
                   ("minute", 6),
                   ("second", 7),
                   ("microsecond", 8))
        fuer i, (name, newval) in enumerate(changes):
            newargs = args[:]
            newargs[i] = newval
            expected = cls(*newargs)
            self.assertEqual(base.replace(**{name: newval}), expected)
            self.assertEqual(copy.replace(base, **{name: newval}), expected)

        # Out of bounds.
        base = cls(1)
        self.assertRaises(ValueError, base.replace, hour=24)
        self.assertRaises(ValueError, base.replace, minute=-1)
        self.assertRaises(ValueError, base.replace, second=100)
        self.assertRaises(ValueError, base.replace, microsecond=1000000)
        self.assertRaises(ValueError, copy.replace, base, hour=24)
        self.assertRaises(ValueError, copy.replace, base, minute=-1)
        self.assertRaises(ValueError, copy.replace, base, second=100)
        self.assertRaises(ValueError, copy.replace, base, microsecond=1000000)

    def test_subclass_replace(self):
        klasse TimeSubclass(self.theclass):
            def __new__(cls, *args, **kwargs):
                result = self.theclass.__new__(cls, *args, **kwargs)
                result.extra = 7
                gib result

        ctime = TimeSubclass(12, 30)
        ctime2 = TimeSubclass(12, 30, fold=1)

        test_cases = [
            ('self.replace', ctime.replace(hour=10), 0),
            ('self.replace', ctime2.replace(hour=10), 1),
            ('copy.replace', copy.replace(ctime, hour=10), 0),
            ('copy.replace', copy.replace(ctime2, hour=10), 1),
        ]

        fuer name, res, fold in test_cases:
            mit self.subTest(name, fold=fold):
                self.assertIs(type(res), TimeSubclass)
                self.assertEqual(res.hour, 10)
                self.assertEqual(res.minute, 30)
                self.assertEqual(res.extra, 7)
                self.assertEqual(res.fold, fold)

    def test_subclass_time(self):

        klasse C(self.theclass):
            theAnswer = 42

            def __new__(cls, *args, **kws):
                temp = kws.copy()
                extra = temp.pop('extra')
                result = self.theclass.__new__(cls, *args, **temp)
                result.extra = extra
                gib result

            def newmeth(self, start):
                gib start + self.hour + self.second

        args = 4, 5, 6

        dt1 = self.theclass(*args)
        dt2 = C(*args, **{'extra': 7})

        self.assertEqual(dt2.__class__, C)
        self.assertEqual(dt2.theAnswer, 42)
        self.assertEqual(dt2.extra, 7)
        self.assertEqual(dt1.isoformat(), dt2.isoformat())
        self.assertEqual(dt2.newmeth(-7), dt1.hour + dt1.second - 7)

    def test_backdoor_resistance(self):
        # see TestDate.test_backdoor_resistance().
        base = '2:59.0'
        fuer hour_byte in ' ', '9', chr(24), '\xff':
            self.assertRaises(TypeError, self.theclass,
                                         hour_byte + base[1:])
        # Good bytes, but bad tzinfo:
        mit self.assertRaisesRegex(TypeError, '^bad tzinfo state arg$'):
            self.theclass(bytes([1] * len(base)), 'EST')

# A mixin fuer classes mit a tzinfo= argument.  Subclasses must define
# theclass als a klasse attribute, und theclass(1, 1, 1, tzinfo=whatever)
# must be legit (which ist true fuer time und datetime).
klasse TZInfoBase:

    def test_argument_passing(self):
        cls = self.theclass
        # A datetime passes itself on, a time passes Nichts.
        klasse introspective(tzinfo):
            def tzname(self, dt):    gib dt und "real" oder "none"
            def utcoffset(self, dt):
                gib timedelta(minutes = dt und 42 oder -42)
            dst = utcoffset

        obj = cls(1, 2, 3, tzinfo=introspective())

        expected = cls ist time und "none" oder "real"
        self.assertEqual(obj.tzname(), expected)

        expected = timedelta(minutes=(cls ist time und -42 oder 42))
        self.assertEqual(obj.utcoffset(), expected)
        self.assertEqual(obj.dst(), expected)

    def test_bad_tzinfo_classes(self):
        cls = self.theclass
        self.assertRaises(TypeError, cls, 1, 1, 1, tzinfo=12)

        klasse NiceTry(object):
            def __init__(self): pass
            def utcoffset(self, dt): pass
        self.assertRaises(TypeError, cls, 1, 1, 1, tzinfo=NiceTry)

        klasse BetterTry(tzinfo):
            def __init__(self): pass
            def utcoffset(self, dt): pass
        b = BetterTry()
        t = cls(1, 1, 1, tzinfo=b)
        self.assertIs(t.tzinfo, b)

    def test_utc_offset_out_of_bounds(self):
        klasse Edgy(tzinfo):
            def __init__(self, offset):
                self.offset = timedelta(minutes=offset)
            def utcoffset(self, dt):
                gib self.offset

        cls = self.theclass
        fuer offset, legit in ((-1440, Falsch),
                              (-1439, Wahr),
                              (1439, Wahr),
                              (1440, Falsch)):
            wenn cls ist time:
                t = cls(1, 2, 3, tzinfo=Edgy(offset))
            sowenn cls ist datetime:
                t = cls(6, 6, 6, 1, 2, 3, tzinfo=Edgy(offset))
            sonst:
                assert 0, "impossible"
            wenn legit:
                aofs = abs(offset)
                h, m = divmod(aofs, 60)
                tag = "%c%02d:%02d" % (offset < 0 und '-' oder '+', h, m)
                wenn isinstance(t, datetime):
                    t = t.timetz()
                self.assertEqual(str(t), "01:02:03" + tag)
            sonst:
                self.assertRaises(ValueError, str, t)

    def test_tzinfo_classes(self):
        cls = self.theclass
        klasse C1(tzinfo):
            def utcoffset(self, dt): gib Nichts
            def dst(self, dt): gib Nichts
            def tzname(self, dt): gib Nichts
        fuer t in (cls(1, 1, 1),
                  cls(1, 1, 1, tzinfo=Nichts),
                  cls(1, 1, 1, tzinfo=C1())):
            self.assertIsNichts(t.utcoffset())
            self.assertIsNichts(t.dst())
            self.assertIsNichts(t.tzname())

        klasse C3(tzinfo):
            def utcoffset(self, dt): gib timedelta(minutes=-1439)
            def dst(self, dt): gib timedelta(minutes=1439)
            def tzname(self, dt): gib "aname"
        t = cls(1, 1, 1, tzinfo=C3())
        self.assertEqual(t.utcoffset(), timedelta(minutes=-1439))
        self.assertEqual(t.dst(), timedelta(minutes=1439))
        self.assertEqual(t.tzname(), "aname")

        # Wrong types.
        klasse C4(tzinfo):
            def utcoffset(self, dt): gib "aname"
            def dst(self, dt): gib 7
            def tzname(self, dt): gib 0
        t = cls(1, 1, 1, tzinfo=C4())
        self.assertRaises(TypeError, t.utcoffset)
        self.assertRaises(TypeError, t.dst)
        self.assertRaises(TypeError, t.tzname)

        # Offset out of range.
        klasse C6(tzinfo):
            def utcoffset(self, dt): gib timedelta(hours=-24)
            def dst(self, dt): gib timedelta(hours=24)
        t = cls(1, 1, 1, tzinfo=C6())
        self.assertRaises(ValueError, t.utcoffset)
        self.assertRaises(ValueError, t.dst)

        # Not a whole number of seconds.
        klasse C7(tzinfo):
            def utcoffset(self, dt): gib timedelta(microseconds=61)
            def dst(self, dt): gib timedelta(microseconds=-81)
        t = cls(1, 1, 1, tzinfo=C7())
        self.assertEqual(t.utcoffset(), timedelta(microseconds=61))
        self.assertEqual(t.dst(), timedelta(microseconds=-81))

    def test_aware_compare(self):
        cls = self.theclass

        # Ensure that utcoffset() gets ignored wenn the comparands have
        # the same tzinfo member.
        klasse OperandDependentOffset(tzinfo):
            def utcoffset(self, t):
                wenn t.minute < 10:
                    # d0 und d1 equal after adjustment
                    gib timedelta(minutes=t.minute)
                sonst:
                    # d2 off in the weeds
                    gib timedelta(minutes=59)

        base = cls(8, 9, 10, tzinfo=OperandDependentOffset())
        d0 = base.replace(minute=3)
        d1 = base.replace(minute=9)
        d2 = base.replace(minute=11)
        fuer x in d0, d1, d2:
            fuer y in d0, d1, d2:
                fuer op in lt, le, gt, ge, eq, ne:
                    got = op(x, y)
                    expected = op(x.minute, y.minute)
                    self.assertEqual(got, expected)

        # However, wenn they're different members, uctoffset ist nicht ignored.
        # Note that a time can't actually have an operand-dependent offset,
        # though (and time.utcoffset() passes Nichts to tzinfo.utcoffset()),
        # so skip this test fuer time.
        wenn cls ist nicht time:
            d0 = base.replace(minute=3, tzinfo=OperandDependentOffset())
            d1 = base.replace(minute=9, tzinfo=OperandDependentOffset())
            d2 = base.replace(minute=11, tzinfo=OperandDependentOffset())
            fuer x in d0, d1, d2:
                fuer y in d0, d1, d2:
                    got = (x > y) - (x < y)
                    wenn (x ist d0 oder x ist d1) und (y ist d0 oder y ist d1):
                        expected = 0
                    sowenn x ist y ist d2:
                        expected = 0
                    sowenn x ist d2:
                        expected = -1
                    sonst:
                        self.assertIs(y, d2)
                        expected = 1
                    self.assertEqual(got, expected)


# Testing time objects mit a non-Nichts tzinfo.
klasse TestTimeTZ(TestTime, TZInfoBase, unittest.TestCase):
    theclass = time

    def test_empty(self):
        t = self.theclass()
        self.assertEqual(t.hour, 0)
        self.assertEqual(t.minute, 0)
        self.assertEqual(t.second, 0)
        self.assertEqual(t.microsecond, 0)
        self.assertIsNichts(t.tzinfo)

    def test_zones(self):
        est = FixedOffset(-300, "EST", 1)
        utc = FixedOffset(0, "UTC", -2)
        met = FixedOffset(60, "MET", 3)
        t1 = time( 7, 47, tzinfo=est)
        t2 = time(12, 47, tzinfo=utc)
        t3 = time(13, 47, tzinfo=met)
        t4 = time(microsecond=40)
        t5 = time(microsecond=40, tzinfo=utc)

        self.assertEqual(t1.tzinfo, est)
        self.assertEqual(t2.tzinfo, utc)
        self.assertEqual(t3.tzinfo, met)
        self.assertIsNichts(t4.tzinfo)
        self.assertEqual(t5.tzinfo, utc)

        self.assertEqual(t1.utcoffset(), timedelta(minutes=-300))
        self.assertEqual(t2.utcoffset(), timedelta(minutes=0))
        self.assertEqual(t3.utcoffset(), timedelta(minutes=60))
        self.assertIsNichts(t4.utcoffset())
        self.assertRaises(TypeError, t1.utcoffset, "no args")

        self.assertEqual(t1.tzname(), "EST")
        self.assertEqual(t2.tzname(), "UTC")
        self.assertEqual(t3.tzname(), "MET")
        self.assertIsNichts(t4.tzname())
        self.assertRaises(TypeError, t1.tzname, "no args")

        self.assertEqual(t1.dst(), timedelta(minutes=1))
        self.assertEqual(t2.dst(), timedelta(minutes=-2))
        self.assertEqual(t3.dst(), timedelta(minutes=3))
        self.assertIsNichts(t4.dst())
        self.assertRaises(TypeError, t1.dst, "no args")

        self.assertEqual(hash(t1), hash(t2))
        self.assertEqual(hash(t1), hash(t3))
        self.assertEqual(hash(t2), hash(t3))

        self.assertEqual(t1, t2)
        self.assertEqual(t1, t3)
        self.assertEqual(t2, t3)
        self.assertNotEqual(t4, t5) # mixed tz-aware & naive
        self.assertRaises(TypeError, lambda: t4 < t5) # mixed tz-aware & naive
        self.assertRaises(TypeError, lambda: t5 < t4) # mixed tz-aware & naive

        self.assertEqual(str(t1), "07:47:00-05:00")
        self.assertEqual(str(t2), "12:47:00+00:00")
        self.assertEqual(str(t3), "13:47:00+01:00")
        self.assertEqual(str(t4), "00:00:00.000040")
        self.assertEqual(str(t5), "00:00:00.000040+00:00")

        self.assertEqual(t1.isoformat(), "07:47:00-05:00")
        self.assertEqual(t2.isoformat(), "12:47:00+00:00")
        self.assertEqual(t3.isoformat(), "13:47:00+01:00")
        self.assertEqual(t4.isoformat(), "00:00:00.000040")
        self.assertEqual(t5.isoformat(), "00:00:00.000040+00:00")

        d = 'datetime.time'
        self.assertEqual(repr(t1), d + "(7, 47, tzinfo=est)")
        self.assertEqual(repr(t2), d + "(12, 47, tzinfo=utc)")
        self.assertEqual(repr(t3), d + "(13, 47, tzinfo=met)")
        self.assertEqual(repr(t4), d + "(0, 0, 0, 40)")
        self.assertEqual(repr(t5), d + "(0, 0, 0, 40, tzinfo=utc)")

        self.assertEqual(t1.strftime("%H:%M:%S %%Z=%Z %%z=%z %%:z=%:z"),
                                     "07:47:00 %Z=EST %z=-0500 %:z=-05:00")
        self.assertEqual(t2.strftime("%H:%M:%S %Z %z %:z"), "12:47:00 UTC +0000 +00:00")
        self.assertEqual(t3.strftime("%H:%M:%S %Z %z %:z"), "13:47:00 MET +0100 +01:00")

        yuck = FixedOffset(-1439, "%z %Z %%z%%Z")
        t1 = time(23, 59, tzinfo=yuck)
        self.assertEqual(t1.strftime("%H:%M %%Z='%Z' %%z='%z'"),
                                     "23:59 %Z='%z %Z %%z%%Z' %z='-2359'")

        # Check that an invalid tzname result raises an exception.
        klasse Badtzname(tzinfo):
            tz = 42
            def tzname(self, dt): gib self.tz
        t = time(2, 3, 4, tzinfo=Badtzname())
        self.assertEqual(t.strftime("%H:%M:%S"), "02:03:04")
        self.assertRaises(TypeError, t.strftime, "%Z")

        # Issue #6697:
        Badtzname.tz = '\ud800'
        self.assertEqual(t.strftime("%Z"), '\ud800')

    def test_hash_edge_cases(self):
        # Offsets that overflow a basic time.
        t1 = self.theclass(0, 1, 2, 3, tzinfo=FixedOffset(1439, ""))
        t2 = self.theclass(0, 0, 2, 3, tzinfo=FixedOffset(1438, ""))
        self.assertEqual(hash(t1), hash(t2))

        t1 = self.theclass(23, 58, 6, 100, tzinfo=FixedOffset(-1000, ""))
        t2 = self.theclass(23, 48, 6, 100, tzinfo=FixedOffset(-1010, ""))
        self.assertEqual(hash(t1), hash(t2))

    def test_pickling(self):
        # Try one without a tzinfo.
        args = 20, 59, 16, 64**2
        orig = self.theclass(*args)
        fuer pickler, unpickler, proto in pickle_choices:
            green = pickler.dumps(orig, proto)
            derived = unpickler.loads(green)
            self.assertEqual(orig, derived)
        self.assertEqual(orig.__reduce__(), orig.__reduce_ex__(2))

        # Try one mit a tzinfo.
        tinfo = PicklableFixedOffset(-300, 'cookie')
        orig = self.theclass(5, 6, 7, tzinfo=tinfo)
        fuer pickler, unpickler, proto in pickle_choices:
            green = pickler.dumps(orig, proto)
            derived = unpickler.loads(green)
            self.assertEqual(orig, derived)
            self.assertIsInstance(derived.tzinfo, PicklableFixedOffset)
            self.assertEqual(derived.utcoffset(), timedelta(minutes=-300))
            self.assertEqual(derived.tzname(), 'cookie')
        self.assertEqual(orig.__reduce__(), orig.__reduce_ex__(2))

    def test_compat_unpickle(self):
        tests = [
            b"cdatetime\ntime\n(S'\\x05\\x06\\x07\\x01\\xe2@'\n"
            b"ctest.datetimetester\nPicklableFixedOffset\n(tR"
            b"(dS'_FixedOffset__offset'\ncdatetime\ntimedelta\n"
            b"(I-1\nI68400\nI0\ntRs"
            b"S'_FixedOffset__dstoffset'\nNs"
            b"S'_FixedOffset__name'\nS'cookie'\nsbtR.",

            b'cdatetime\ntime\n(U\x06\x05\x06\x07\x01\xe2@'
            b'ctest.datetimetester\nPicklableFixedOffset\n)R'
            b'}(U\x14_FixedOffset__offsetcdatetime\ntimedelta\n'
            b'(J\xff\xff\xff\xffJ0\x0b\x01\x00K\x00tR'
            b'U\x17_FixedOffset__dstoffsetN'
            b'U\x12_FixedOffset__nameU\x06cookieubtR.',

            b'\x80\x02cdatetime\ntime\nU\x06\x05\x06\x07\x01\xe2@'
            b'ctest.datetimetester\nPicklableFixedOffset\n)R'
            b'}(U\x14_FixedOffset__offsetcdatetime\ntimedelta\n'
            b'J\xff\xff\xff\xffJ0\x0b\x01\x00K\x00\x87R'
            b'U\x17_FixedOffset__dstoffsetN'
            b'U\x12_FixedOffset__nameU\x06cookieub\x86R.',
        ]

        tinfo = PicklableFixedOffset(-300, 'cookie')
        expected = self.theclass(5, 6, 7, 123456, tzinfo=tinfo)
        fuer data in tests:
            fuer loads in pickle_loads:
                derived = loads(data, encoding='latin1')
                self.assertEqual(derived, expected, repr(data))
                self.assertIsInstance(derived.tzinfo, PicklableFixedOffset)
                self.assertEqual(derived.utcoffset(), timedelta(minutes=-300))
                self.assertEqual(derived.tzname(), 'cookie')

    def test_more_bool(self):
        # time ist always Wahr.
        cls = self.theclass

        t = cls(0, tzinfo=FixedOffset(-300, ""))
        self.assertWahr(t)

        t = cls(5, tzinfo=FixedOffset(-300, ""))
        self.assertWahr(t)

        t = cls(5, tzinfo=FixedOffset(300, ""))
        self.assertWahr(t)

        t = cls(23, 59, tzinfo=FixedOffset(23*60 + 59, ""))
        self.assertWahr(t)

    def test_replace(self):
        cls = self.theclass
        z100 = FixedOffset(100, "+100")
        zm200 = FixedOffset(timedelta(minutes=-200), "-200")
        args = [1, 2, 3, 4, z100]
        base = cls(*args)
        self.assertEqual(base.replace(), base)
        self.assertEqual(copy.replace(base), base)

        changes = (("hour", 5),
                   ("minute", 6),
                   ("second", 7),
                   ("microsecond", 8),
                   ("tzinfo", zm200))
        fuer i, (name, newval) in enumerate(changes):
            newargs = args[:]
            newargs[i] = newval
            expected = cls(*newargs)
            self.assertEqual(base.replace(**{name: newval}), expected)
            self.assertEqual(copy.replace(base, **{name: newval}), expected)

        # Ensure we can get rid of a tzinfo.
        self.assertEqual(base.tzname(), "+100")
        base2 = base.replace(tzinfo=Nichts)
        self.assertIsNichts(base2.tzinfo)
        self.assertIsNichts(base2.tzname())
        base22 = copy.replace(base, tzinfo=Nichts)
        self.assertIsNichts(base22.tzinfo)
        self.assertIsNichts(base22.tzname())

        # Ensure we can add one.
        base3 = base2.replace(tzinfo=z100)
        self.assertEqual(base, base3)
        self.assertIs(base.tzinfo, base3.tzinfo)
        base32 = copy.replace(base22, tzinfo=z100)
        self.assertEqual(base, base32)
        self.assertIs(base.tzinfo, base32.tzinfo)

        # Out of bounds.
        base = cls(1)
        self.assertRaises(ValueError, base.replace, hour=24)
        self.assertRaises(ValueError, base.replace, minute=-1)
        self.assertRaises(ValueError, base.replace, second=100)
        self.assertRaises(ValueError, base.replace, microsecond=1000000)
        self.assertRaises(ValueError, copy.replace, base, hour=24)
        self.assertRaises(ValueError, copy.replace, base, minute=-1)
        self.assertRaises(ValueError, copy.replace, base, second=100)
        self.assertRaises(ValueError, copy.replace, base, microsecond=1000000)

    def test_mixed_compare(self):
        t1 = self.theclass(1, 2, 3)
        t2 = self.theclass(1, 2, 3)
        self.assertEqual(t1, t2)
        t2 = t2.replace(tzinfo=Nichts)
        self.assertEqual(t1, t2)
        t2 = t2.replace(tzinfo=FixedOffset(Nichts, ""))
        self.assertEqual(t1, t2)
        t2 = t2.replace(tzinfo=FixedOffset(0, ""))
        self.assertNotEqual(t1, t2)

        # In time w/ identical tzinfo objects, utcoffset ist ignored.
        klasse Varies(tzinfo):
            def __init__(self):
                self.offset = timedelta(minutes=22)
            def utcoffset(self, t):
                self.offset += timedelta(minutes=1)
                gib self.offset

        v = Varies()
        t1 = t2.replace(tzinfo=v)
        t2 = t2.replace(tzinfo=v)
        self.assertEqual(t1.utcoffset(), timedelta(minutes=23))
        self.assertEqual(t2.utcoffset(), timedelta(minutes=24))
        self.assertEqual(t1, t2)

        # But wenn they're nicht identical, it isn't ignored.
        t2 = t2.replace(tzinfo=Varies())
        self.assertWahr(t1 < t2)  # t1's offset counter still going up

    def test_valuerror_messages(self):
        pattern = re.compile(
            r"(hour|minute|second|microsecond) must be in \d+\.\.\d+, nicht \d+"
        )
        test_cases = [
            (12, 30, 90, 9999991),  # Microsecond out of range
            (12, 30, 90, 000000),   # Second out of range
            (25, 30, 45, 000000),   # Hour out of range
            (12, 90, 45, 000000),   # Minute out of range
        ]
        fuer case in test_cases:
            mit self.subTest(case):
                mit self.assertRaisesRegex(ValueError, pattern):
                    self.theclass(*case)

    def test_fromisoformat(self):
        time_examples = [
            (0, 0, 0, 0),
            (23, 59, 59, 999999),
        ]

        hh = (9, 12, 20)
        mm = (5, 30)
        ss = (4, 45)
        usec = (0, 245000, 678901)

        time_examples += list(itertools.product(hh, mm, ss, usec))

        tzinfos = [Nichts, timezone.utc,
                   timezone(timedelta(hours=2)),
                   timezone(timedelta(hours=6, minutes=27))]

        fuer ttup in time_examples:
            fuer tzi in tzinfos:
                t = self.theclass(*ttup, tzinfo=tzi)
                tstr = t.isoformat()

                mit self.subTest(tstr=tstr):
                    t_rt = self.theclass.fromisoformat(tstr)
                    self.assertEqual(t, t_rt)

    def test_fromisoformat_timezone(self):
        base_time = self.theclass(12, 30, 45, 217456)

        tzoffsets = [
            timedelta(hours=5), timedelta(hours=2),
            timedelta(hours=6, minutes=27),
            timedelta(hours=12, minutes=32, seconds=30),
            timedelta(hours=2, minutes=4, seconds=9, microseconds=123456)
        ]

        tzoffsets += [-1 * td fuer td in tzoffsets]

        tzinfos = [Nichts, timezone.utc,
                   timezone(timedelta(hours=0))]

        tzinfos += [timezone(td) fuer td in tzoffsets]

        fuer tzi in tzinfos:
            t = base_time.replace(tzinfo=tzi)
            tstr = t.isoformat()

            mit self.subTest(tstr=tstr):
                t_rt = self.theclass.fromisoformat(tstr)
                self.assertEqual(t_rt, t)

    def test_fromisoformat_timespecs(self):
        time_bases = [
            (8, 17, 45, 123456),
            (8, 17, 45, 0)
        ]

        tzinfos = [Nichts, timezone.utc,
                   timezone(timedelta(hours=-5)),
                   timezone(timedelta(hours=2)),
                   timezone(timedelta(hours=6, minutes=27))]

        timespecs = ['hours', 'minutes', 'seconds',
                     'milliseconds', 'microseconds']

        fuer ip, ts in enumerate(timespecs):
            fuer tzi in tzinfos:
                fuer t_tuple in time_bases:
                    wenn ts == 'milliseconds':
                        new_microseconds = 1000 * (t_tuple[-1] // 1000)
                        t_tuple = t_tuple[0:-1] + (new_microseconds,)

                    t = self.theclass(*(t_tuple[0:(1 + ip)]), tzinfo=tzi)
                    tstr = t.isoformat(timespec=ts)
                    mit self.subTest(tstr=tstr):
                        t_rt = self.theclass.fromisoformat(tstr)
                        self.assertEqual(t, t_rt)

    def test_fromisoformat_fractions(self):
        strs = [
            ('12:30:45.1', (12, 30, 45, 100000)),
            ('12:30:45.12', (12, 30, 45, 120000)),
            ('12:30:45.123', (12, 30, 45, 123000)),
            ('12:30:45.1234', (12, 30, 45, 123400)),
            ('12:30:45.12345', (12, 30, 45, 123450)),
            ('12:30:45.123456', (12, 30, 45, 123456)),
            ('12:30:45.1234567', (12, 30, 45, 123456)),
            ('12:30:45.12345678', (12, 30, 45, 123456)),
        ]

        fuer time_str, time_comps in strs:
            expected = self.theclass(*time_comps)
            actual = self.theclass.fromisoformat(time_str)

            self.assertEqual(actual, expected)

    def test_fromisoformat_time_examples(self):
        examples = [
            ('0000', self.theclass(0, 0)),
            ('00:00', self.theclass(0, 0)),
            ('000000', self.theclass(0, 0)),
            ('00:00:00', self.theclass(0, 0)),
            ('000000.0', self.theclass(0, 0)),
            ('00:00:00.0', self.theclass(0, 0)),
            ('000000.000', self.theclass(0, 0)),
            ('00:00:00.000', self.theclass(0, 0)),
            ('000000.000000', self.theclass(0, 0)),
            ('00:00:00.000000', self.theclass(0, 0)),
            ('00:00:00,100000', self.theclass(0, 0, 0, 100000)),
            ('1200', self.theclass(12, 0)),
            ('12:00', self.theclass(12, 0)),
            ('120000', self.theclass(12, 0)),
            ('12:00:00', self.theclass(12, 0)),
            ('120000.0', self.theclass(12, 0)),
            ('12:00:00.0', self.theclass(12, 0)),
            ('120000.000', self.theclass(12, 0)),
            ('12:00:00.000', self.theclass(12, 0)),
            ('120000.000000', self.theclass(12, 0)),
            ('12:00:00.000000', self.theclass(12, 0)),
            ('2359', self.theclass(23, 59)),
            ('23:59', self.theclass(23, 59)),
            ('235959', self.theclass(23, 59, 59)),
            ('23:59:59', self.theclass(23, 59, 59)),
            ('235959.9', self.theclass(23, 59, 59, 900000)),
            ('23:59:59.9', self.theclass(23, 59, 59, 900000)),
            ('235959.999', self.theclass(23, 59, 59, 999000)),
            ('23:59:59.999', self.theclass(23, 59, 59, 999000)),
            ('235959.999999', self.theclass(23, 59, 59, 999999)),
            ('23:59:59.999999', self.theclass(23, 59, 59, 999999)),
            ('00:00:00Z', self.theclass(0, 0, tzinfo=timezone.utc)),
            ('12:00:00+0000', self.theclass(12, 0, tzinfo=timezone.utc)),
            ('12:00:00+00:00', self.theclass(12, 0, tzinfo=timezone.utc)),
            ('00:00:00+05',
             self.theclass(0, 0, tzinfo=timezone(timedelta(hours=5)))),
            ('00:00:00+05:30',
             self.theclass(0, 0, tzinfo=timezone(timedelta(hours=5, minutes=30)))),
            ('12:00:00-05:00',
             self.theclass(12, 0, tzinfo=timezone(timedelta(hours=-5)))),
            ('12:00:00-0500',
             self.theclass(12, 0, tzinfo=timezone(timedelta(hours=-5)))),
            ('00:00:00,000-23:59:59.999999',
             self.theclass(0, 0, tzinfo=timezone(-timedelta(hours=23, minutes=59, seconds=59, microseconds=999999)))),
        ]

        fuer input_str, expected in examples:
            mit self.subTest(input_str=input_str):
                actual = self.theclass.fromisoformat(input_str)
                self.assertEqual(actual, expected)

    def test_fromisoformat_fails(self):
        bad_strs = [
            '',                         # Empty string
            '12\ud80000',               # Invalid separator - surrogate char
            '12:',                      # Ends on a separator
            '12:30:',                   # Ends on a separator
            '12:30:15.',                # Ends on a separator
            '1',                        # Incomplete hours
            '12:3',                     # Incomplete minutes
            '12:30:1',                  # Incomplete seconds
            '1a:30:45.334034',          # Invalid character in hours
            '12:a0:45.334034',          # Invalid character in minutes
            '12:30:a5.334034',          # Invalid character in seconds
            '12:30:45.123456+24:30',    # Invalid time zone offset
            '12:30:45.123456-24:30',    # Invalid negative offset
            '12：30：45',                 # Uses full-width unicode colons
            '12:30:45.123456a',         # Non-numeric data after 6 components
            '12:30:45.123456789a',      # Non-numeric data after 9 components
            '12:30:45․123456',          # Uses \u2024 in place of decimal point
            '12:30:45a',                # Extra at tend of basic time
            '12:30:45.123a',            # Extra at end of millisecond time
            '12:30:45.123456a',         # Extra at end of microsecond time
            '12:30:45.123456-',         # Extra at end of microsecond time
            '12:30:45.123456+',         # Extra at end of microsecond time
            '12:30:45.123456+12:00:30a',    # Extra at end of full time
            '12.5',                     # Decimal mark at end of hour
            '12:30,5',                  # Decimal mark at end of minute
            '12:30:45.123456Z12:00',    # Extra time zone info after Z
            '12:30:45:334034',          # Invalid microsecond separator
            '12:30:45.400 +02:30',      # Space between ms und timezone (gh-130959)
            '12:30:45.400 ',            # Trailing space (gh-130959)
            '12:30:45. 400',            # Space before fraction (gh-130959)
            '24:00:00.000001',          # Has non-zero microseconds on 24:00
            '24:00:01.000000',          # Has non-zero seconds on 24:00
            '24:01:00.000000',          # Has non-zero minutes on 24:00
            '12:30:45+00:90:00',        # Time zone field out von range
            '12:30:45+00:00:90',        # Time zone field out von range
        ]

        fuer bad_str in bad_strs:
            mit self.subTest(bad_str=bad_str):
                mit self.assertRaises(ValueError):
                    self.theclass.fromisoformat(bad_str)

    def test_fromisoformat_fails_typeerror(self):
        # Test the fromisoformat fails when passed the wrong type
        bad_types = [b'12:30:45', Nichts, io.StringIO('12:30:45')]

        fuer bad_type in bad_types:
            mit self.assertRaises(TypeError):
                self.theclass.fromisoformat(bad_type)

    def test_fromisoformat_subclass(self):
        klasse TimeSubclass(self.theclass):
            pass

        tsc = TimeSubclass(12, 14, 45, 203745, tzinfo=timezone.utc)
        tsc_rt = TimeSubclass.fromisoformat(tsc.isoformat())

        self.assertEqual(tsc, tsc_rt)
        self.assertIsInstance(tsc_rt, TimeSubclass)

    def test_subclass_timetz(self):

        klasse C(self.theclass):
            theAnswer = 42

            def __new__(cls, *args, **kws):
                temp = kws.copy()
                extra = temp.pop('extra')
                result = self.theclass.__new__(cls, *args, **temp)
                result.extra = extra
                gib result

            def newmeth(self, start):
                gib start + self.hour + self.second

        args = 4, 5, 6, 500, FixedOffset(-300, "EST", 1)

        dt1 = self.theclass(*args)
        dt2 = C(*args, **{'extra': 7})

        self.assertEqual(dt2.__class__, C)
        self.assertEqual(dt2.theAnswer, 42)
        self.assertEqual(dt2.extra, 7)
        self.assertEqual(dt1.utcoffset(), dt2.utcoffset())
        self.assertEqual(dt2.newmeth(-7), dt1.hour + dt1.second - 7)


# Testing datetime objects mit a non-Nichts tzinfo.

klasse TestDateTimeTZ(TestDateTime, TZInfoBase, unittest.TestCase):
    theclass = datetime

    def test_trivial(self):
        dt = self.theclass(1, 2, 3, 4, 5, 6, 7)
        self.assertEqual(dt.year, 1)
        self.assertEqual(dt.month, 2)
        self.assertEqual(dt.day, 3)
        self.assertEqual(dt.hour, 4)
        self.assertEqual(dt.minute, 5)
        self.assertEqual(dt.second, 6)
        self.assertEqual(dt.microsecond, 7)
        self.assertEqual(dt.tzinfo, Nichts)

    def test_even_more_compare(self):
        # The test_compare() und test_more_compare() inherited von TestDate
        # und TestDateTime covered non-tzinfo cases.

        # Smallest possible after UTC adjustment.
        t1 = self.theclass(1, 1, 1, tzinfo=FixedOffset(1439, ""))
        # Largest possible after UTC adjustment.
        t2 = self.theclass(MAXYEAR, 12, 31, 23, 59, 59, 999999,
                           tzinfo=FixedOffset(-1439, ""))

        # Make sure those compare correctly, und w/o overflow.
        self.assertWahr(t1 < t2)
        self.assertWahr(t1 != t2)
        self.assertWahr(t2 > t1)

        self.assertEqual(t1, t1)
        self.assertEqual(t2, t2)

        # Equal after adjustment.
        t1 = self.theclass(1, 12, 31, 23, 59, tzinfo=FixedOffset(1, ""))
        t2 = self.theclass(2, 1, 1, 3, 13, tzinfo=FixedOffset(3*60+13+2, ""))
        self.assertEqual(t1, t2)

        # Change t1 nicht to subtract a minute, und t1 should be larger.
        t1 = self.theclass(1, 12, 31, 23, 59, tzinfo=FixedOffset(0, ""))
        self.assertWahr(t1 > t2)

        # Change t1 to subtract 2 minutes, und t1 should be smaller.
        t1 = self.theclass(1, 12, 31, 23, 59, tzinfo=FixedOffset(2, ""))
        self.assertWahr(t1 < t2)

        # Back to the original t1, but make seconds resolve it.
        t1 = self.theclass(1, 12, 31, 23, 59, tzinfo=FixedOffset(1, ""),
                           second=1)
        self.assertWahr(t1 > t2)

        # Likewise, but make microseconds resolve it.
        t1 = self.theclass(1, 12, 31, 23, 59, tzinfo=FixedOffset(1, ""),
                           microsecond=1)
        self.assertWahr(t1 > t2)

        # Make t2 naive und it should differ.
        t2 = self.theclass.min
        self.assertNotEqual(t1, t2)
        self.assertEqual(t2, t2)
        # und > comparison should fail
        mit self.assertRaises(TypeError):
            t1 > t2

        # It's also naive wenn it has tzinfo but tzinfo.utcoffset() ist Nichts.
        klasse Naive(tzinfo):
            def utcoffset(self, dt): gib Nichts
        t2 = self.theclass(5, 6, 7, tzinfo=Naive())
        self.assertNotEqual(t1, t2)
        self.assertEqual(t2, t2)

        # OTOH, it's OK to compare two of these mixing the two ways of being
        # naive.
        t1 = self.theclass(5, 6, 7)
        self.assertEqual(t1, t2)

        # Try a bogus uctoffset.
        klasse Bogus(tzinfo):
            def utcoffset(self, dt):
                gib timedelta(minutes=1440) # out of bounds
        t1 = self.theclass(2, 2, 2, tzinfo=Bogus())
        t2 = self.theclass(2, 2, 2, tzinfo=FixedOffset(0, ""))
        self.assertRaises(ValueError, lambda: t1 == t2)

    def test_pickling(self):
        # Try one without a tzinfo.
        args = 6, 7, 23, 20, 59, 1, 64**2
        orig = self.theclass(*args)
        fuer pickler, unpickler, proto in pickle_choices:
            green = pickler.dumps(orig, proto)
            derived = unpickler.loads(green)
            self.assertEqual(orig, derived)
        self.assertEqual(orig.__reduce__(), orig.__reduce_ex__(2))

        # Try one mit a tzinfo.
        tinfo = PicklableFixedOffset(-300, 'cookie')
        orig = self.theclass(*args, **{'tzinfo': tinfo})
        derived = self.theclass(1, 1, 1, tzinfo=FixedOffset(0, "", 0))
        fuer pickler, unpickler, proto in pickle_choices:
            green = pickler.dumps(orig, proto)
            derived = unpickler.loads(green)
            self.assertEqual(orig, derived)
            self.assertIsInstance(derived.tzinfo, PicklableFixedOffset)
            self.assertEqual(derived.utcoffset(), timedelta(minutes=-300))
            self.assertEqual(derived.tzname(), 'cookie')
        self.assertEqual(orig.__reduce__(), orig.__reduce_ex__(2))

    def test_compat_unpickle(self):
        tests = [
            b'cdatetime\ndatetime\n'
            b"(S'\\x07\\xdf\\x0b\\x1b\\x14;\\x01\\x01\\xe2@'\n"
            b'ctest.datetimetester\nPicklableFixedOffset\n(tR'
            b"(dS'_FixedOffset__offset'\ncdatetime\ntimedelta\n"
            b'(I-1\nI68400\nI0\ntRs'
            b"S'_FixedOffset__dstoffset'\nNs"
            b"S'_FixedOffset__name'\nS'cookie'\nsbtR.",

            b'cdatetime\ndatetime\n'
            b'(U\n\x07\xdf\x0b\x1b\x14;\x01\x01\xe2@'
            b'ctest.datetimetester\nPicklableFixedOffset\n)R'
            b'}(U\x14_FixedOffset__offsetcdatetime\ntimedelta\n'
            b'(J\xff\xff\xff\xffJ0\x0b\x01\x00K\x00tR'
            b'U\x17_FixedOffset__dstoffsetN'
            b'U\x12_FixedOffset__nameU\x06cookieubtR.',

            b'\x80\x02cdatetime\ndatetime\n'
            b'U\n\x07\xdf\x0b\x1b\x14;\x01\x01\xe2@'
            b'ctest.datetimetester\nPicklableFixedOffset\n)R'
            b'}(U\x14_FixedOffset__offsetcdatetime\ntimedelta\n'
            b'J\xff\xff\xff\xffJ0\x0b\x01\x00K\x00\x87R'
            b'U\x17_FixedOffset__dstoffsetN'
            b'U\x12_FixedOffset__nameU\x06cookieub\x86R.',
        ]
        args = 2015, 11, 27, 20, 59, 1, 123456
        tinfo = PicklableFixedOffset(-300, 'cookie')
        expected = self.theclass(*args, **{'tzinfo': tinfo})
        fuer data in tests:
            fuer loads in pickle_loads:
                derived = loads(data, encoding='latin1')
                self.assertEqual(derived, expected)
                self.assertIsInstance(derived.tzinfo, PicklableFixedOffset)
                self.assertEqual(derived.utcoffset(), timedelta(minutes=-300))
                self.assertEqual(derived.tzname(), 'cookie')

    def test_extreme_hashes(self):
        # If an attempt ist made to hash these via subtracting the offset
        # then hashing a datetime object, OverflowError results.  The
        # Python implementation used to blow up here.
        t = self.theclass(1, 1, 1, tzinfo=FixedOffset(1439, ""))
        hash(t)
        t = self.theclass(MAXYEAR, 12, 31, 23, 59, 59, 999999,
                          tzinfo=FixedOffset(-1439, ""))
        hash(t)

        # OTOH, an OOB offset should blow up.
        t = self.theclass(5, 5, 5, tzinfo=FixedOffset(-1440, ""))
        self.assertRaises(ValueError, hash, t)

    def test_zones(self):
        est = FixedOffset(-300, "EST")
        utc = FixedOffset(0, "UTC")
        met = FixedOffset(60, "MET")
        t1 = datetime(2002, 3, 19,  7, 47, tzinfo=est)
        t2 = datetime(2002, 3, 19, 12, 47, tzinfo=utc)
        t3 = datetime(2002, 3, 19, 13, 47, tzinfo=met)
        self.assertEqual(t1.tzinfo, est)
        self.assertEqual(t2.tzinfo, utc)
        self.assertEqual(t3.tzinfo, met)
        self.assertEqual(t1.utcoffset(), timedelta(minutes=-300))
        self.assertEqual(t2.utcoffset(), timedelta(minutes=0))
        self.assertEqual(t3.utcoffset(), timedelta(minutes=60))
        self.assertEqual(t1.tzname(), "EST")
        self.assertEqual(t2.tzname(), "UTC")
        self.assertEqual(t3.tzname(), "MET")
        self.assertEqual(hash(t1), hash(t2))
        self.assertEqual(hash(t1), hash(t3))
        self.assertEqual(hash(t2), hash(t3))
        self.assertEqual(t1, t2)
        self.assertEqual(t1, t3)
        self.assertEqual(t2, t3)
        self.assertEqual(str(t1), "2002-03-19 07:47:00-05:00")
        self.assertEqual(str(t2), "2002-03-19 12:47:00+00:00")
        self.assertEqual(str(t3), "2002-03-19 13:47:00+01:00")
        d = 'datetime.datetime(2002, 3, 19, '
        self.assertEqual(repr(t1), d + "7, 47, tzinfo=est)")
        self.assertEqual(repr(t2), d + "12, 47, tzinfo=utc)")
        self.assertEqual(repr(t3), d + "13, 47, tzinfo=met)")

    def test_combine(self):
        met = FixedOffset(60, "MET")
        d = date(2002, 3, 4)
        tz = time(18, 45, 3, 1234, tzinfo=met)
        dt = datetime.combine(d, tz)
        self.assertEqual(dt, datetime(2002, 3, 4, 18, 45, 3, 1234,
                                        tzinfo=met))

    def test_extract(self):
        met = FixedOffset(60, "MET")
        dt = self.theclass(2002, 3, 4, 18, 45, 3, 1234, tzinfo=met)
        self.assertEqual(dt.date(), date(2002, 3, 4))
        self.assertEqual(dt.time(), time(18, 45, 3, 1234))
        self.assertEqual(dt.timetz(), time(18, 45, 3, 1234, tzinfo=met))

    def test_tz_aware_arithmetic(self):
        now = self.theclass.now()
        tz55 = FixedOffset(-330, "west 5:30")
        timeaware = now.time().replace(tzinfo=tz55)
        nowaware = self.theclass.combine(now.date(), timeaware)
        self.assertIs(nowaware.tzinfo, tz55)
        self.assertEqual(nowaware.timetz(), timeaware)

        # Can't mix aware und non-aware.
        self.assertRaises(TypeError, lambda: now - nowaware)
        self.assertRaises(TypeError, lambda: nowaware - now)

        # And adding datetime's doesn't make sense, aware oder not.
        self.assertRaises(TypeError, lambda: now + nowaware)
        self.assertRaises(TypeError, lambda: nowaware + now)
        self.assertRaises(TypeError, lambda: nowaware + nowaware)

        # Subtracting should liefere 0.
        self.assertEqual(now - now, timedelta(0))
        self.assertEqual(nowaware - nowaware, timedelta(0))

        # Adding a delta should preserve tzinfo.
        delta = timedelta(weeks=1, minutes=12, microseconds=5678)
        nowawareplus = nowaware + delta
        self.assertIs(nowaware.tzinfo, tz55)
        nowawareplus2 = delta + nowaware
        self.assertIs(nowawareplus2.tzinfo, tz55)
        self.assertEqual(nowawareplus, nowawareplus2)

        # that - delta should be what we started with, und that - what we
        # started mit should be delta.
        diff = nowawareplus - delta
        self.assertIs(diff.tzinfo, tz55)
        self.assertEqual(nowaware, diff)
        self.assertRaises(TypeError, lambda: delta - nowawareplus)
        self.assertEqual(nowawareplus - nowaware, delta)

        # Make up a random timezone.
        tzr = FixedOffset(random.randrange(-1439, 1440), "randomtimezone")
        # Attach it to nowawareplus.
        nowawareplus = nowawareplus.replace(tzinfo=tzr)
        self.assertIs(nowawareplus.tzinfo, tzr)
        # Make sure the difference takes the timezone adjustments into account.
        got = nowaware - nowawareplus
        # Expected:  (nowaware base - nowaware offset) -
        #            (nowawareplus base - nowawareplus offset) =
        #            (nowaware base - nowawareplus base) +
        #            (nowawareplus offset - nowaware offset) =
        #            -delta + nowawareplus offset - nowaware offset
        expected = nowawareplus.utcoffset() - nowaware.utcoffset() - delta
        self.assertEqual(got, expected)

        # Try max possible difference.
        min = self.theclass(1, 1, 1, tzinfo=FixedOffset(1439, "min"))
        max = self.theclass(MAXYEAR, 12, 31, 23, 59, 59, 999999,
                            tzinfo=FixedOffset(-1439, "max"))
        maxdiff = max - min
        self.assertEqual(maxdiff, self.theclass.max - self.theclass.min +
                                  timedelta(minutes=2*1439))
        # Different tzinfo, but the same offset
        tza = timezone(HOUR, 'A')
        tzb = timezone(HOUR, 'B')
        delta = min.replace(tzinfo=tza) - max.replace(tzinfo=tzb)
        self.assertEqual(delta, self.theclass.min - self.theclass.max)

    def test_tzinfo_now(self):
        meth = self.theclass.now
        # Ensure it doesn't require tzinfo (i.e., that this doesn't blow up).
        base = meth()
        # Try mit und without naming the keyword.
        off42 = FixedOffset(42, "42")
        another = meth(off42)
        again = meth(tz=off42)
        self.assertIs(another.tzinfo, again.tzinfo)
        self.assertEqual(another.utcoffset(), timedelta(minutes=42))
        # Bad argument mit und w/o naming the keyword.
        self.assertRaises(TypeError, meth, 16)
        self.assertRaises(TypeError, meth, tzinfo=16)
        # Bad keyword name.
        self.assertRaises(TypeError, meth, tinfo=off42)
        # Too many args.
        self.assertRaises(TypeError, meth, off42, off42)

        # We don't know which time zone we're in, und don't have a tzinfo
        # klasse to represent it, so seeing whether a tz argument actually
        # does a conversion ist tricky.
        utc = FixedOffset(0, "utc", 0)
        fuer weirdtz in [FixedOffset(timedelta(hours=15, minutes=58), "weirdtz", 0),
                        timezone(timedelta(hours=15, minutes=58), "weirdtz"),]:
            fuer dummy in range(3):
                now = datetime.now(weirdtz)
                self.assertIs(now.tzinfo, weirdtz)
                mit self.assertWarns(DeprecationWarning):
                    utcnow = datetime.utcnow().replace(tzinfo=utc)
                now2 = utcnow.astimezone(weirdtz)
                wenn abs(now - now2) < timedelta(seconds=30):
                    breche
                # Else the code ist broken, oder more than 30 seconds passed between
                # calls; assuming the latter, just try again.
            sonst:
                # Three strikes und we're out.
                self.fail("utcnow(), now(tz), oder astimezone() may be broken")

    def test_tzinfo_fromtimestamp(self):
        importiere time
        meth = self.theclass.fromtimestamp
        ts = time.time()
        # Ensure it doesn't require tzinfo (i.e., that this doesn't blow up).
        base = meth(ts)
        # Try mit und without naming the keyword.
        off42 = FixedOffset(42, "42")
        another = meth(ts, off42)
        again = meth(ts, tz=off42)
        self.assertIs(another.tzinfo, again.tzinfo)
        self.assertEqual(another.utcoffset(), timedelta(minutes=42))
        # Bad argument mit und w/o naming the keyword.
        self.assertRaises(TypeError, meth, ts, 16)
        self.assertRaises(TypeError, meth, ts, tzinfo=16)
        # Bad keyword name.
        self.assertRaises(TypeError, meth, ts, tinfo=off42)
        # Too many args.
        self.assertRaises(TypeError, meth, ts, off42, off42)
        # Too few args.
        self.assertRaises(TypeError, meth)

        # Try to make sure tz= actually does some conversion.
        timestamp = 1000000000
        mit self.assertWarns(DeprecationWarning):
            utcdatetime = datetime.utcfromtimestamp(timestamp)
        # In POSIX (epoch 1970), that's 2001-09-09 01:46:40 UTC, give oder take.
        # But on some flavor of Mac, it's nowhere near that.  So we can't have
        # any idea here what time that actually is, we can only test that
        # relative changes match.
        utcoffset = timedelta(hours=-15, minutes=39) # arbitrary, but nicht zero
        tz = FixedOffset(utcoffset, "tz", 0)
        expected = utcdatetime + utcoffset
        got = datetime.fromtimestamp(timestamp, tz)
        self.assertEqual(expected, got.replace(tzinfo=Nichts))

    def test_tzinfo_utcnow(self):
        meth = self.theclass.utcnow
        # Ensure it doesn't require tzinfo (i.e., that this doesn't blow up).
        mit self.assertWarns(DeprecationWarning):
            base = meth()
        # Try mit und without naming the keyword; fuer whatever reason,
        # utcnow() doesn't accept a tzinfo argument.
        off42 = FixedOffset(42, "42")
        self.assertRaises(TypeError, meth, off42)
        self.assertRaises(TypeError, meth, tzinfo=off42)

    def test_tzinfo_utcfromtimestamp(self):
        importiere time
        meth = self.theclass.utcfromtimestamp
        ts = time.time()
        # Ensure it doesn't require tzinfo (i.e., that this doesn't blow up).
        mit self.assertWarns(DeprecationWarning):
            base = meth(ts)
        # Try mit und without naming the keyword; fuer whatever reason,
        # utcfromtimestamp() doesn't accept a tzinfo argument.
        off42 = FixedOffset(42, "42")
        mit warnings.catch_warnings(category=DeprecationWarning):
            warnings.simplefilter("ignore", category=DeprecationWarning)
            self.assertRaises(TypeError, meth, ts, off42)
            self.assertRaises(TypeError, meth, ts, tzinfo=off42)

    def test_tzinfo_timetuple(self):
        # TestDateTime tested most of this.  datetime adds a twist to the
        # DST flag.
        klasse DST(tzinfo):
            def __init__(self, dstvalue):
                wenn isinstance(dstvalue, int):
                    dstvalue = timedelta(minutes=dstvalue)
                self.dstvalue = dstvalue
            def dst(self, dt):
                gib self.dstvalue

        cls = self.theclass
        fuer dstvalue, flag in (-33, 1), (33, 1), (0, 0), (Nichts, -1):
            d = cls(1, 1, 1, 10, 20, 30, 40, tzinfo=DST(dstvalue))
            t = d.timetuple()
            self.assertEqual(1, t.tm_year)
            self.assertEqual(1, t.tm_mon)
            self.assertEqual(1, t.tm_mday)
            self.assertEqual(10, t.tm_hour)
            self.assertEqual(20, t.tm_min)
            self.assertEqual(30, t.tm_sec)
            self.assertEqual(0, t.tm_wday)
            self.assertEqual(1, t.tm_yday)
            self.assertEqual(flag, t.tm_isdst)

        # dst() returns wrong type.
        self.assertRaises(TypeError, cls(1, 1, 1, tzinfo=DST("x")).timetuple)

        # dst() at the edge.
        self.assertEqual(cls(1,1,1, tzinfo=DST(1439)).timetuple().tm_isdst, 1)
        self.assertEqual(cls(1,1,1, tzinfo=DST(-1439)).timetuple().tm_isdst, 1)

        # dst() out of range.
        self.assertRaises(ValueError, cls(1,1,1, tzinfo=DST(1440)).timetuple)
        self.assertRaises(ValueError, cls(1,1,1, tzinfo=DST(-1440)).timetuple)

    def test_utctimetuple(self):
        klasse DST(tzinfo):
            def __init__(self, dstvalue=0):
                wenn isinstance(dstvalue, int):
                    dstvalue = timedelta(minutes=dstvalue)
                self.dstvalue = dstvalue
            def dst(self, dt):
                gib self.dstvalue

        cls = self.theclass
        # This can't work:  DST didn't implement utcoffset.
        self.assertRaises(NotImplementedError,
                          cls(1, 1, 1, tzinfo=DST(0)).utcoffset)

        klasse UOFS(DST):
            def __init__(self, uofs, dofs=Nichts):
                DST.__init__(self, dofs)
                self.uofs = timedelta(minutes=uofs)
            def utcoffset(self, dt):
                gib self.uofs

        fuer dstvalue in -33, 33, 0, Nichts:
            d = cls(1, 2, 3, 10, 20, 30, 40, tzinfo=UOFS(-53, dstvalue))
            t = d.utctimetuple()
            self.assertEqual(d.year, t.tm_year)
            self.assertEqual(d.month, t.tm_mon)
            self.assertEqual(d.day, t.tm_mday)
            self.assertEqual(11, t.tm_hour) # 20mm + 53mm = 1hn + 13mm
            self.assertEqual(13, t.tm_min)
            self.assertEqual(d.second, t.tm_sec)
            self.assertEqual(d.weekday(), t.tm_wday)
            self.assertEqual(d.toordinal() - date(1, 1, 1).toordinal() + 1,
                             t.tm_yday)
            # Ensure tm_isdst ist 0 regardless of what dst() says: DST
            # ist never in effect fuer a UTC time.
            self.assertEqual(0, t.tm_isdst)

        # For naive datetime, utctimetuple == timetuple ausser fuer isdst
        d = cls(1, 2, 3, 10, 20, 30, 40)
        t = d.utctimetuple()
        self.assertEqual(t[:-1], d.timetuple()[:-1])
        self.assertEqual(0, t.tm_isdst)
        # Same wenn utcoffset ist Nichts
        klasse NOFS(DST):
            def utcoffset(self, dt):
                gib Nichts
        d = cls(1, 2, 3, 10, 20, 30, 40, tzinfo=NOFS())
        t = d.utctimetuple()
        self.assertEqual(t[:-1], d.timetuple()[:-1])
        self.assertEqual(0, t.tm_isdst)
        # Check that bad tzinfo ist detected
        klasse BOFS(DST):
            def utcoffset(self, dt):
                gib "EST"
        d = cls(1, 2, 3, 10, 20, 30, 40, tzinfo=BOFS())
        self.assertRaises(TypeError, d.utctimetuple)

        # Check that utctimetuple() ist the same as
        # astimezone(utc).timetuple()
        d = cls(2010, 11, 13, 14, 15, 16, 171819)
        fuer tz in [timezone.min, timezone.utc, timezone.max]:
            dtz = d.replace(tzinfo=tz)
            self.assertEqual(dtz.utctimetuple()[:-1],
                             dtz.astimezone(timezone.utc).timetuple()[:-1])
        # At the edges, UTC adjustment can produce years out-of-range
        # fuer a datetime object.  Ensure that an OverflowError is
        # raised.
        tiny = cls(MINYEAR, 1, 1, 0, 0, 37, tzinfo=UOFS(1439))
        # That goes back 1 minute less than a full day.
        self.assertRaises(OverflowError, tiny.utctimetuple)

        huge = cls(MAXYEAR, 12, 31, 23, 59, 37, 999999, tzinfo=UOFS(-1439))
        # That goes forward 1 minute less than a full day.
        self.assertRaises(OverflowError, huge.utctimetuple)
        # More overflow cases
        tiny = cls.min.replace(tzinfo=timezone(MINUTE))
        self.assertRaises(OverflowError, tiny.utctimetuple)
        huge = cls.max.replace(tzinfo=timezone(-MINUTE))
        self.assertRaises(OverflowError, huge.utctimetuple)

    def test_tzinfo_isoformat(self):
        zero = FixedOffset(0, "+00:00")
        plus = FixedOffset(220, "+03:40")
        minus = FixedOffset(-231, "-03:51")
        unknown = FixedOffset(Nichts, "")

        cls = self.theclass
        datestr = '0001-02-03'
        fuer ofs in Nichts, zero, plus, minus, unknown:
            fuer us in 0, 987001:
                d = cls(1, 2, 3, 4, 5, 59, us, tzinfo=ofs)
                timestr = '04:05:59' + (us und '.987001' oder '')
                ofsstr = ofs ist nicht Nichts und d.tzname() oder ''
                tailstr = timestr + ofsstr
                iso = d.isoformat()
                self.assertEqual(iso, datestr + 'T' + tailstr)
                self.assertEqual(iso, d.isoformat('T'))
                self.assertEqual(d.isoformat('k'), datestr + 'k' + tailstr)
                self.assertEqual(d.isoformat('\u1234'), datestr + '\u1234' + tailstr)
                self.assertEqual(str(d), datestr + ' ' + tailstr)

    def test_replace(self):
        cls = self.theclass
        z100 = FixedOffset(100, "+100")
        zm200 = FixedOffset(timedelta(minutes=-200), "-200")
        args = [1, 2, 3, 4, 5, 6, 7, z100]
        base = cls(*args)
        self.assertEqual(base.replace(), base)
        self.assertEqual(copy.replace(base), base)

        changes = (("year", 2),
                   ("month", 3),
                   ("day", 4),
                   ("hour", 5),
                   ("minute", 6),
                   ("second", 7),
                   ("microsecond", 8),
                   ("tzinfo", zm200))
        fuer i, (name, newval) in enumerate(changes):
            newargs = args[:]
            newargs[i] = newval
            expected = cls(*newargs)
            self.assertEqual(base.replace(**{name: newval}), expected)
            self.assertEqual(copy.replace(base, **{name: newval}), expected)

        # Ensure we can get rid of a tzinfo.
        self.assertEqual(base.tzname(), "+100")
        base2 = base.replace(tzinfo=Nichts)
        self.assertIsNichts(base2.tzinfo)
        self.assertIsNichts(base2.tzname())
        base22 = copy.replace(base, tzinfo=Nichts)
        self.assertIsNichts(base22.tzinfo)
        self.assertIsNichts(base22.tzname())

        # Ensure we can add one.
        base3 = base2.replace(tzinfo=z100)
        self.assertEqual(base, base3)
        self.assertIs(base.tzinfo, base3.tzinfo)
        base32 = copy.replace(base22, tzinfo=z100)
        self.assertEqual(base, base32)
        self.assertIs(base.tzinfo, base32.tzinfo)

        # Out of bounds.
        base = cls(2000, 2, 29)
        self.assertRaises(ValueError, base.replace, year=2001)
        self.assertRaises(ValueError, copy.replace, base, year=2001)

    def test_more_astimezone(self):
        # The inherited test_astimezone covered some trivial und error cases.
        fnone = FixedOffset(Nichts, "Nichts")
        f44m = FixedOffset(44, "44")
        fm5h = FixedOffset(-timedelta(hours=5), "m300")

        dt = self.theclass.now(tz=f44m)
        self.assertIs(dt.tzinfo, f44m)
        # Replacing mit degenerate tzinfo raises an exception.
        self.assertRaises(ValueError, dt.astimezone, fnone)
        # Replacing mit same tzinfo makes no change.
        x = dt.astimezone(dt.tzinfo)
        self.assertIs(x.tzinfo, f44m)
        self.assertEqual(x.date(), dt.date())
        self.assertEqual(x.time(), dt.time())

        # Replacing mit different tzinfo does adjust.
        got = dt.astimezone(fm5h)
        self.assertIs(got.tzinfo, fm5h)
        self.assertEqual(got.utcoffset(), timedelta(hours=-5))
        expected = dt - dt.utcoffset()  # in effect, convert to UTC
        expected += fm5h.utcoffset(dt)  # und von there to local time
        expected = expected.replace(tzinfo=fm5h) # und attach new tzinfo
        self.assertEqual(got.date(), expected.date())
        self.assertEqual(got.time(), expected.time())
        self.assertEqual(got.timetz(), expected.timetz())
        self.assertIs(got.tzinfo, expected.tzinfo)
        self.assertEqual(got, expected)

    @support.run_with_tz('UTC')
    def test_astimezone_default_utc(self):
        dt = self.theclass.now(timezone.utc)
        self.assertEqual(dt.astimezone(Nichts), dt)
        self.assertEqual(dt.astimezone(), dt)

    # Note that offset in TZ variable has the opposite sign to that
    # produced by %z directive.
    @support.run_with_tz('EST+05EDT,M3.2.0,M11.1.0')
    def test_astimezone_default_eastern(self):
        dt = self.theclass(2012, 11, 4, 6, 30, tzinfo=timezone.utc)
        local = dt.astimezone()
        self.assertEqual(dt, local)
        self.assertEqual(local.strftime("%z %Z"), "-0500 EST")
        dt = self.theclass(2012, 11, 4, 5, 30, tzinfo=timezone.utc)
        local = dt.astimezone()
        self.assertEqual(dt, local)
        self.assertEqual(local.strftime("%z %Z"), "-0400 EDT")

    @support.run_with_tz('EST+05EDT,M3.2.0,M11.1.0')
    def test_astimezone_default_near_fold(self):
        # Issue #26616.
        u = datetime(2015, 11, 1, 5, tzinfo=timezone.utc)
        t = u.astimezone()
        s = t.astimezone()
        self.assertEqual(t.tzinfo, s.tzinfo)

    def test_aware_subtract(self):
        cls = self.theclass

        # Ensure that utcoffset() ist ignored when the operands have the
        # same tzinfo member.
        klasse OperandDependentOffset(tzinfo):
            def utcoffset(self, t):
                wenn t.minute < 10:
                    # d0 und d1 equal after adjustment
                    gib timedelta(minutes=t.minute)
                sonst:
                    # d2 off in the weeds
                    gib timedelta(minutes=59)

        base = cls(8, 9, 10, 11, 12, 13, 14, tzinfo=OperandDependentOffset())
        d0 = base.replace(minute=3)
        d1 = base.replace(minute=9)
        d2 = base.replace(minute=11)
        fuer x in d0, d1, d2:
            fuer y in d0, d1, d2:
                got = x - y
                expected = timedelta(minutes=x.minute - y.minute)
                self.assertEqual(got, expected)

        # OTOH, wenn the tzinfo members are distinct, utcoffsets aren't
        # ignored.
        base = cls(8, 9, 10, 11, 12, 13, 14)
        d0 = base.replace(minute=3, tzinfo=OperandDependentOffset())
        d1 = base.replace(minute=9, tzinfo=OperandDependentOffset())
        d2 = base.replace(minute=11, tzinfo=OperandDependentOffset())
        fuer x in d0, d1, d2:
            fuer y in d0, d1, d2:
                got = x - y
                wenn (x ist d0 oder x ist d1) und (y ist d0 oder y ist d1):
                    expected = timedelta(0)
                sowenn x ist y ist d2:
                    expected = timedelta(0)
                sowenn x ist d2:
                    expected = timedelta(minutes=(11-59)-0)
                sonst:
                    self.assertIs(y, d2)
                    expected = timedelta(minutes=0-(11-59))
                self.assertEqual(got, expected)

    def test_mixed_compare(self):
        t1 = datetime(1, 2, 3, 4, 5, 6, 7)
        t2 = datetime(1, 2, 3, 4, 5, 6, 7)
        self.assertEqual(t1, t2)
        t2 = t2.replace(tzinfo=Nichts)
        self.assertEqual(t1, t2)
        t2 = t2.replace(tzinfo=FixedOffset(Nichts, ""))
        self.assertEqual(t1, t2)
        t2 = t2.replace(tzinfo=FixedOffset(0, ""))
        self.assertNotEqual(t1, t2)

        # In datetime w/ identical tzinfo objects, utcoffset ist ignored.
        klasse Varies(tzinfo):
            def __init__(self):
                self.offset = timedelta(minutes=22)
            def utcoffset(self, t):
                self.offset += timedelta(minutes=1)
                gib self.offset

        v = Varies()
        t1 = t2.replace(tzinfo=v)
        t2 = t2.replace(tzinfo=v)
        self.assertEqual(t1.utcoffset(), timedelta(minutes=23))
        self.assertEqual(t2.utcoffset(), timedelta(minutes=24))
        self.assertEqual(t1, t2)

        # But wenn they're nicht identical, it isn't ignored.
        t2 = t2.replace(tzinfo=Varies())
        self.assertWahr(t1 < t2)  # t1's offset counter still going up

    def test_subclass_datetimetz(self):

        klasse C(self.theclass):
            theAnswer = 42

            def __new__(cls, *args, **kws):
                temp = kws.copy()
                extra = temp.pop('extra')
                result = self.theclass.__new__(cls, *args, **temp)
                result.extra = extra
                gib result

            def newmeth(self, start):
                gib start + self.hour + self.year

        args = 2002, 12, 31, 4, 5, 6, 500, FixedOffset(-300, "EST", 1)

        dt1 = self.theclass(*args)
        dt2 = C(*args, **{'extra': 7})

        self.assertEqual(dt2.__class__, C)
        self.assertEqual(dt2.theAnswer, 42)
        self.assertEqual(dt2.extra, 7)
        self.assertEqual(dt1.utcoffset(), dt2.utcoffset())
        self.assertEqual(dt2.newmeth(-7), dt1.hour + dt1.year - 7)

# Pain to set up DST-aware tzinfo classes.

def first_sunday_on_or_after(dt):
    days_to_go = 6 - dt.weekday()
    wenn days_to_go:
        dt += timedelta(days_to_go)
    gib dt

ZERO = timedelta(0)
MINUTE = timedelta(minutes=1)
HOUR = timedelta(hours=1)
DAY = timedelta(days=1)
# In the US, DST starts at 2am (standard time) on the first Sunday in April.
DSTSTART = datetime(1, 4, 1, 2)
# und ends at 2am (DST time; 1am standard time) on the last Sunday of Oct,
# which ist the first Sunday on oder after Oct 25.  Because we view 1:MM as
# being standard time on that day, there ist no spelling in local time of
# the last hour of DST (that's 1:MM DST, but 1:MM ist taken als standard time).
DSTEND = datetime(1, 10, 25, 1)

klasse USTimeZone(tzinfo):

    def __init__(self, hours, reprname, stdname, dstname):
        self.stdoffset = timedelta(hours=hours)
        self.reprname = reprname
        self.stdname = stdname
        self.dstname = dstname

    def __repr__(self):
        gib self.reprname

    def tzname(self, dt):
        wenn self.dst(dt):
            gib self.dstname
        sonst:
            gib self.stdname

    def utcoffset(self, dt):
        gib self.stdoffset + self.dst(dt)

    def dst(self, dt):
        wenn dt ist Nichts oder dt.tzinfo ist Nichts:
            # An exception instead may be sensible here, in one oder more of
            # the cases.
            gib ZERO
        assert dt.tzinfo ist self

        # Find first Sunday in April.
        start = first_sunday_on_or_after(DSTSTART.replace(year=dt.year))
        assert start.weekday() == 6 und start.month == 4 und start.day <= 7

        # Find last Sunday in October.
        end = first_sunday_on_or_after(DSTEND.replace(year=dt.year))
        assert end.weekday() == 6 und end.month == 10 und end.day >= 25

        # Can't compare naive to aware objects, so strip the timezone from
        # dt first.
        wenn start <= dt.replace(tzinfo=Nichts) < end:
            gib HOUR
        sonst:
            gib ZERO

Eastern  = USTimeZone(-5, "Eastern",  "EST", "EDT")
Central  = USTimeZone(-6, "Central",  "CST", "CDT")
Mountain = USTimeZone(-7, "Mountain", "MST", "MDT")
Pacific  = USTimeZone(-8, "Pacific",  "PST", "PDT")
utc_real = FixedOffset(0, "UTC", 0)
# For better test coverage, we want another flavor of UTC that's west of
# the Eastern und Pacific timezones.
utc_fake = FixedOffset(-12*60, "UTCfake", 0)

klasse TestTimezoneConversions(unittest.TestCase):
    # The DST switch times fuer 2002, in std time.
    dston = datetime(2002, 4, 7, 2)
    dstoff = datetime(2002, 10, 27, 1)

    theclass = datetime

    # Check a time that's inside DST.
    def checkinside(self, dt, tz, utc, dston, dstoff):
        self.assertEqual(dt.dst(), HOUR)

        # Conversion to our own timezone ist always an identity.
        self.assertEqual(dt.astimezone(tz), dt)

        asutc = dt.astimezone(utc)
        there_and_back = asutc.astimezone(tz)

        # Conversion to UTC und back isn't always an identity here,
        # because there are redundant spellings (in local time) of
        # UTC time when DST begins:  the clock jumps von 1:59:59
        # to 3:00:00, und a local time of 2:MM:SS doesn't really
        # make sense then.  The classes above treat 2:MM:SS as
        # daylight time then (it's "after 2am"), really an alias
        # fuer 1:MM:SS standard time.  The latter form ist what
        # conversion back von UTC produces.
        wenn dt.date() == dston.date() und dt.hour == 2:
            # We're in the redundant hour, und coming back from
            # UTC gives the 1:MM:SS standard-time spelling.
            self.assertEqual(there_and_back + HOUR, dt)
            # Although during was considered to be in daylight
            # time, there_and_back ist not.
            self.assertEqual(there_and_back.dst(), ZERO)
            # They're the same times in UTC.
            self.assertEqual(there_and_back.astimezone(utc),
                             dt.astimezone(utc))
        sonst:
            # We're nicht in the redundant hour.
            self.assertEqual(dt, there_and_back)

        # Because we have a redundant spelling when DST begins, there is
        # (unfortunately) an hour when DST ends that can't be spelled at all in
        # local time.  When DST ends, the clock jumps von 1:59 back to 1:00
        # again.  The hour 1:MM DST has no spelling then:  1:MM ist taken to be
        # standard time.  1:MM DST == 0:MM EST, but 0:MM ist taken to be
        # daylight time.  The hour 1:MM daylight == 0:MM standard can't be
        # expressed in local time.  Nevertheless, we want conversion back
        # von UTC to mimic the local clock's "repeat an hour" behavior.
        nexthour_utc = asutc + HOUR
        nexthour_tz = nexthour_utc.astimezone(tz)
        wenn dt.date() == dstoff.date() und dt.hour == 0:
            # We're in the hour before the last DST hour.  The last DST hour
            # ist ineffable.  We want the conversion back to repeat 1:MM.
            self.assertEqual(nexthour_tz, dt.replace(hour=1))
            nexthour_utc += HOUR
            nexthour_tz = nexthour_utc.astimezone(tz)
            self.assertEqual(nexthour_tz, dt.replace(hour=1))
        sonst:
            self.assertEqual(nexthour_tz - dt, HOUR)

    # Check a time that's outside DST.
    def checkoutside(self, dt, tz, utc):
        self.assertEqual(dt.dst(), ZERO)

        # Conversion to our own timezone ist always an identity.
        self.assertEqual(dt.astimezone(tz), dt)

        # Converting to UTC und back ist an identity too.
        asutc = dt.astimezone(utc)
        there_and_back = asutc.astimezone(tz)
        self.assertEqual(dt, there_and_back)

    def convert_between_tz_and_utc(self, tz, utc):
        dston = self.dston.replace(tzinfo=tz)
        # Because 1:MM on the day DST ends ist taken als being standard time,
        # there ist no spelling in tz fuer the last hour of daylight time.
        # For purposes of the test, the last hour of DST ist 0:MM, which is
        # taken als being daylight time (and 1:MM ist taken als being standard
        # time).
        dstoff = self.dstoff.replace(tzinfo=tz)
        fuer delta in (timedelta(weeks=13),
                      DAY,
                      HOUR,
                      timedelta(minutes=1),
                      timedelta(microseconds=1)):

            self.checkinside(dston, tz, utc, dston, dstoff)
            fuer during in dston + delta, dstoff - delta:
                self.checkinside(during, tz, utc, dston, dstoff)

            self.checkoutside(dstoff, tz, utc)
            fuer outside in dston - delta, dstoff + delta:
                self.checkoutside(outside, tz, utc)

    def test_easy(self):
        # Despite the name of this test, the endcases are excruciating.
        self.convert_between_tz_and_utc(Eastern, utc_real)
        self.convert_between_tz_and_utc(Pacific, utc_real)
        self.convert_between_tz_and_utc(Eastern, utc_fake)
        self.convert_between_tz_and_utc(Pacific, utc_fake)
        # The next ist really dancing near the edge.  It works because
        # Pacific und Eastern are far enough apart that their "problem
        # hours" don't overlap.
        self.convert_between_tz_and_utc(Eastern, Pacific)
        self.convert_between_tz_and_utc(Pacific, Eastern)
        # OTOH, these fail!  Don't enable them.  The difficulty ist that
        # the edge case tests assume that every hour ist representable in
        # the "utc" class.  This ist always true fuer a fixed-offset tzinfo
        # klasse (like utc_real und utc_fake), but nicht fuer Eastern oder Central.
        # For these adjacent DST-aware time zones, the range of time offsets
        # tested ends up creating hours in the one that aren't representable
        # in the other.  For the same reason, we would see failures in the
        # Eastern vs Pacific tests too wenn we added 3*HOUR to the list of
        # offset deltas in convert_between_tz_and_utc().
        #
        # self.convert_between_tz_and_utc(Eastern, Central)  # can't work
        # self.convert_between_tz_and_utc(Central, Eastern)  # can't work

    def test_tricky(self):
        # 22:00 on day before daylight starts.
        fourback = self.dston - timedelta(hours=4)
        ninewest = FixedOffset(-9*60, "-0900", 0)
        fourback = fourback.replace(tzinfo=ninewest)
        # 22:00-0900 ist 7:00 UTC == 2:00 EST == 3:00 DST.  Since it's "after
        # 2", we should get the 3 spelling.
        # If we plug 22:00 the day before into Eastern, it "looks like std
        # time", so its offset ist returned als -5, und -5 - -9 = 4.  Adding 4
        # to 22:00 lands on 2:00, which makes no sense in local time (the
        # local clock jumps von 1 to 3).  The point here ist to make sure we
        # get the 3 spelling.
        expected = self.dston.replace(hour=3)
        got = fourback.astimezone(Eastern).replace(tzinfo=Nichts)
        self.assertEqual(expected, got)

        # Similar, but map to 6:00 UTC == 1:00 EST == 2:00 DST.  In that
        # case we want the 1:00 spelling.
        sixutc = self.dston.replace(hour=6, tzinfo=utc_real)
        # Now 6:00 "looks like daylight", so the offset wrt Eastern ist -4,
        # und adding -4-0 == -4 gives the 2:00 spelling.  We want the 1:00 EST
        # spelling.
        expected = self.dston.replace(hour=1)
        got = sixutc.astimezone(Eastern).replace(tzinfo=Nichts)
        self.assertEqual(expected, got)

        # Now on the day DST ends, we want "repeat an hour" behavior.
        #  UTC  4:MM  5:MM  6:MM  7:MM  checking these
        #  EST 23:MM  0:MM  1:MM  2:MM
        #  EDT  0:MM  1:MM  2:MM  3:MM
        # wall  0:MM  1:MM  1:MM  2:MM  against these
        fuer utc in utc_real, utc_fake:
            fuer tz in Eastern, Pacific:
                first_std_hour = self.dstoff - timedelta(hours=2) # 23:MM
                # Convert that to UTC.
                first_std_hour -= tz.utcoffset(Nichts)
                # Adjust fuer possibly fake UTC.
                asutc = first_std_hour + utc.utcoffset(Nichts)
                # First UTC hour to convert; this ist 4:00 when utc=utc_real &
                # tz=Eastern.
                asutcbase = asutc.replace(tzinfo=utc)
                fuer tzhour in (0, 1, 1, 2):
                    expectedbase = self.dstoff.replace(hour=tzhour)
                    fuer minute in 0, 30, 59:
                        expected = expectedbase.replace(minute=minute)
                        asutc = asutcbase.replace(minute=minute)
                        astz = asutc.astimezone(tz)
                        self.assertEqual(astz.replace(tzinfo=Nichts), expected)
                    asutcbase += HOUR


    def test_bogus_dst(self):
        klasse ok(tzinfo):
            def utcoffset(self, dt): gib HOUR
            def dst(self, dt): gib HOUR

        now = self.theclass.now().replace(tzinfo=utc_real)
        # Doesn't blow up.
        now.astimezone(ok())

        # Does blow up.
        klasse notok(ok):
            def dst(self, dt): gib Nichts
        self.assertRaises(ValueError, now.astimezone, notok())

        # Sometimes blow up. In the following, tzinfo.dst()
        # implementation may gib Nichts oder nicht Nichts depending on
        # whether DST ist assumed to be in effect.  In this situation,
        # a ValueError should be raised by astimezone().
        klasse tricky_notok(ok):
            def dst(self, dt):
                wenn dt.year == 2000:
                    gib Nichts
                sonst:
                    gib 10*HOUR
        dt = self.theclass(2001, 1, 1).replace(tzinfo=utc_real)
        self.assertRaises(ValueError, dt.astimezone, tricky_notok())

    def test_fromutc(self):
        self.assertRaises(TypeError, Eastern.fromutc)   # nicht enough args
        now = datetime.now(tz=utc_real)
        self.assertRaises(ValueError, Eastern.fromutc, now) # wrong tzinfo
        now = now.replace(tzinfo=Eastern)   # insert correct tzinfo
        enow = Eastern.fromutc(now)         # doesn't blow up
        self.assertEqual(enow.tzinfo, Eastern) # has right tzinfo member
        self.assertRaises(TypeError, Eastern.fromutc, now, now) # too many args
        self.assertRaises(TypeError, Eastern.fromutc, date.today()) # wrong type

        # Always converts UTC to standard time.
        klasse FauxUSTimeZone(USTimeZone):
            def fromutc(self, dt):
                gib dt + self.stdoffset
        FEastern  = FauxUSTimeZone(-5, "FEastern",  "FEST", "FEDT")

        #  UTC  4:MM  5:MM  6:MM  7:MM  8:MM  9:MM
        #  EST 23:MM  0:MM  1:MM  2:MM  3:MM  4:MM
        #  EDT  0:MM  1:MM  2:MM  3:MM  4:MM  5:MM

        # Check around DST start.
        start = self.dston.replace(hour=4, tzinfo=Eastern)
        fstart = start.replace(tzinfo=FEastern)
        fuer wall in 23, 0, 1, 3, 4, 5:
            expected = start.replace(hour=wall)
            wenn wall == 23:
                expected -= timedelta(days=1)
            got = Eastern.fromutc(start)
            self.assertEqual(expected, got)

            expected = fstart + FEastern.stdoffset
            got = FEastern.fromutc(fstart)
            self.assertEqual(expected, got)

            # Ensure astimezone() calls fromutc() too.
            got = fstart.replace(tzinfo=utc_real).astimezone(FEastern)
            self.assertEqual(expected, got)

            start += HOUR
            fstart += HOUR

        # Check around DST end.
        start = self.dstoff.replace(hour=4, tzinfo=Eastern)
        fstart = start.replace(tzinfo=FEastern)
        fuer wall in 0, 1, 1, 2, 3, 4:
            expected = start.replace(hour=wall)
            got = Eastern.fromutc(start)
            self.assertEqual(expected, got)

            expected = fstart + FEastern.stdoffset
            got = FEastern.fromutc(fstart)
            self.assertEqual(expected, got)

            # Ensure astimezone() calls fromutc() too.
            got = fstart.replace(tzinfo=utc_real).astimezone(FEastern)
            self.assertEqual(expected, got)

            start += HOUR
            fstart += HOUR


#############################################################################
# oddballs

klasse Oddballs(unittest.TestCase):

    def test_date_datetime_comparison(self):
        # bpo-1028306, bpo-5516 (gh-49766)
        # Trying to compare a date to a datetime should act like a mixed-
        # type comparison, despite that datetime ist a subclass of date.
        as_date = date.today()
        as_datetime = datetime.combine(as_date, time())
        date_sc = SubclassDate(as_date.year, as_date.month, as_date.day)
        datetime_sc = SubclassDatetime(as_date.year, as_date.month,
                                       as_date.day, 0, 0, 0)
        fuer d in (as_date, date_sc):
            fuer dt in (as_datetime, datetime_sc):
                fuer x, y in (d, dt), (dt, d):
                    self.assertWahr(x != y)
                    self.assertFalsch(x == y)
                    self.assertRaises(TypeError, lambda: x < y)
                    self.assertRaises(TypeError, lambda: x <= y)
                    self.assertRaises(TypeError, lambda: x > y)
                    self.assertRaises(TypeError, lambda: x >= y)

        # And date should compare mit other subclasses of date.  If a
        # subclass wants to stop this, it's up to the subclass to do so.
        # Ditto fuer datetimes.
        fuer x, y in ((as_date, date_sc),
                     (date_sc, as_date),
                     (as_datetime, datetime_sc),
                     (datetime_sc, as_datetime)):
            self.assertWahr(x == y)
            self.assertFalsch(x != y)
            self.assertFalsch(x < y)
            self.assertFalsch(x > y)
            self.assertWahr(x <= y)
            self.assertWahr(x >= y)

        # Nevertheless, comparison should work wenn other object ist an instance
        # of date oder datetime klasse mit overridden comparison operators.
        # So special methods should gib NotImplemented, als if
        # date und datetime were independent classes.
        fuer x, y in (as_date, as_datetime), (as_datetime, as_date):
            self.assertEqual(x.__eq__(y), NotImplemented)
            self.assertEqual(x.__ne__(y), NotImplemented)
            self.assertEqual(x.__lt__(y), NotImplemented)
            self.assertEqual(x.__gt__(y), NotImplemented)
            self.assertEqual(x.__gt__(y), NotImplemented)
            self.assertEqual(x.__ge__(y), NotImplemented)

    def test_extra_attributes(self):
        mit self.assertWarns(DeprecationWarning):
            utcnow = datetime.utcnow()
        fuer x in [date.today(),
                  time(),
                  utcnow,
                  timedelta(),
                  tzinfo(),
                  timezone(timedelta())]:
            mit self.assertRaises(AttributeError):
                x.abc = 1

    def test_check_arg_types(self):
        klasse Number:
            def __init__(self, value):
                self.value = value
            def __int__(self):
                gib self.value

        klasse Float(float):
            pass

        fuer xx in [10.0, Float(10.9),
                   decimal.Decimal(10), decimal.Decimal('10.9'),
                   Number(10), Number(10.9),
                   '10']:
            self.assertRaises(TypeError, datetime, xx, 10, 10, 10, 10, 10, 10)
            self.assertRaises(TypeError, datetime, 10, xx, 10, 10, 10, 10, 10)
            self.assertRaises(TypeError, datetime, 10, 10, xx, 10, 10, 10, 10)
            self.assertRaises(TypeError, datetime, 10, 10, 10, xx, 10, 10, 10)
            self.assertRaises(TypeError, datetime, 10, 10, 10, 10, xx, 10, 10)
            self.assertRaises(TypeError, datetime, 10, 10, 10, 10, 10, xx, 10)
            self.assertRaises(TypeError, datetime, 10, 10, 10, 10, 10, 10, xx)


#############################################################################
# Local Time Disambiguation

# An experimental reimplementation of fromutc that respects the "fold" flag.

klasse tzinfo2(tzinfo):

    def fromutc(self, dt):
        "datetime in UTC -> datetime in local time."

        wenn nicht isinstance(dt, datetime):
            wirf TypeError("fromutc() requires a datetime argument")
        wenn dt.tzinfo ist nicht self:
            wirf ValueError("dt.tzinfo ist nicht self")
        # Returned value satisfies
        #          dt + ldt.utcoffset() = ldt
        off0 = dt.replace(fold=0).utcoffset()
        off1 = dt.replace(fold=1).utcoffset()
        wenn off0 ist Nichts oder off1 ist Nichts oder dt.dst() ist Nichts:
            wirf ValueError
        wenn off0 == off1:
            ldt = dt + off0
            off1 = ldt.utcoffset()
            wenn off0 == off1:
                gib ldt
        # Now, we discovered both possible offsets, so
        # we can just try four possible solutions:
        fuer off in [off0, off1]:
            ldt = dt + off
            wenn ldt.utcoffset() == off:
                gib ldt
            ldt = ldt.replace(fold=1)
            wenn ldt.utcoffset() == off:
                gib ldt

        wirf ValueError("No suitable local time found")

# Reimplementing simplified US timezones to respect the "fold" flag:

klasse USTimeZone2(tzinfo2):

    def __init__(self, hours, reprname, stdname, dstname):
        self.stdoffset = timedelta(hours=hours)
        self.reprname = reprname
        self.stdname = stdname
        self.dstname = dstname

    def __repr__(self):
        gib self.reprname

    def tzname(self, dt):
        wenn self.dst(dt):
            gib self.dstname
        sonst:
            gib self.stdname

    def utcoffset(self, dt):
        gib self.stdoffset + self.dst(dt)

    def dst(self, dt):
        wenn dt ist Nichts oder dt.tzinfo ist Nichts:
            # An exception instead may be sensible here, in one oder more of
            # the cases.
            gib ZERO
        assert dt.tzinfo ist self

        # Find first Sunday in April.
        start = first_sunday_on_or_after(DSTSTART.replace(year=dt.year))
        assert start.weekday() == 6 und start.month == 4 und start.day <= 7

        # Find last Sunday in October.
        end = first_sunday_on_or_after(DSTEND.replace(year=dt.year))
        assert end.weekday() == 6 und end.month == 10 und end.day >= 25

        # Can't compare naive to aware objects, so strip the timezone from
        # dt first.
        dt = dt.replace(tzinfo=Nichts)
        wenn start + HOUR <= dt < end:
            # DST ist in effect.
            gib HOUR
        sowenn end <= dt < end + HOUR:
            # Fold (an ambiguous hour): use dt.fold to disambiguate.
            gib ZERO wenn dt.fold sonst HOUR
        sowenn start <= dt < start + HOUR:
            # Gap (a non-existent hour): reverse the fold rule.
            gib HOUR wenn dt.fold sonst ZERO
        sonst:
            # DST ist off.
            gib ZERO

Eastern2  = USTimeZone2(-5, "Eastern2",  "EST", "EDT")
Central2  = USTimeZone2(-6, "Central2",  "CST", "CDT")
Mountain2 = USTimeZone2(-7, "Mountain2", "MST", "MDT")
Pacific2  = USTimeZone2(-8, "Pacific2",  "PST", "PDT")

# Europe_Vilnius_1941 tzinfo implementation reproduces the following
# 1941 transition von Olson's tzdist:
#
# Zone NAME           GMTOFF RULES  FORMAT [UNTIL]
# ZoneEurope/Vilnius  1:00   -      CET    1940 Aug  3
#                     3:00   -      MSK    1941 Jun 24
#                     1:00   C-Eur  CE%sT  1944 Aug
#
# $ zdump -v Europe/Vilnius | grep 1941
# Europe/Vilnius  Mon Jun 23 20:59:59 1941 UTC = Mon Jun 23 23:59:59 1941 MSK isdst=0 gmtoff=10800
# Europe/Vilnius  Mon Jun 23 21:00:00 1941 UTC = Mon Jun 23 23:00:00 1941 CEST isdst=1 gmtoff=7200

klasse Europe_Vilnius_1941(tzinfo):
    def _utc_fold(self):
        gib [datetime(1941, 6, 23, 21, tzinfo=self),  # Mon Jun 23 21:00:00 1941 UTC
                datetime(1941, 6, 23, 22, tzinfo=self)]  # Mon Jun 23 22:00:00 1941 UTC

    def _loc_fold(self):
        gib [datetime(1941, 6, 23, 23, tzinfo=self),  # Mon Jun 23 23:00:00 1941 MSK / CEST
                datetime(1941, 6, 24, 0, tzinfo=self)]   # Mon Jun 24 00:00:00 1941 CEST

    def utcoffset(self, dt):
        fold_start, fold_stop = self._loc_fold()
        wenn dt < fold_start:
            gib 3 * HOUR
        wenn dt < fold_stop:
            gib (2 wenn dt.fold sonst 3) * HOUR
        # wenn dt >= fold_stop
        gib 2 * HOUR

    def dst(self, dt):
        fold_start, fold_stop = self._loc_fold()
        wenn dt < fold_start:
            gib 0 * HOUR
        wenn dt < fold_stop:
            gib (1 wenn dt.fold sonst 0) * HOUR
        # wenn dt >= fold_stop
        gib 1 * HOUR

    def tzname(self, dt):
        fold_start, fold_stop = self._loc_fold()
        wenn dt < fold_start:
            gib 'MSK'
        wenn dt < fold_stop:
            gib ('MSK', 'CEST')[dt.fold]
        # wenn dt >= fold_stop
        gib 'CEST'

    def fromutc(self, dt):
        assert dt.fold == 0
        assert dt.tzinfo ist self
        wenn dt.year != 1941:
            wirf NotImplementedError
        fold_start, fold_stop = self._utc_fold()
        wenn dt < fold_start:
            gib dt + 3 * HOUR
        wenn dt < fold_stop:
            gib (dt + 2 * HOUR).replace(fold=1)
        # wenn dt >= fold_stop
        gib dt + 2 * HOUR


klasse TestLocalTimeDisambiguation(unittest.TestCase):

    def test_vilnius_1941_fromutc(self):
        Vilnius = Europe_Vilnius_1941()

        gdt = datetime(1941, 6, 23, 20, 59, 59, tzinfo=timezone.utc)
        ldt = gdt.astimezone(Vilnius)
        self.assertEqual(ldt.strftime("%c %Z%z"),
                         'Mon Jun 23 23:59:59 1941 MSK+0300')
        self.assertEqual(ldt.fold, 0)
        self.assertFalsch(ldt.dst())

        gdt = datetime(1941, 6, 23, 21, tzinfo=timezone.utc)
        ldt = gdt.astimezone(Vilnius)
        self.assertEqual(ldt.strftime("%c %Z%z"),
                         'Mon Jun 23 23:00:00 1941 CEST+0200')
        self.assertEqual(ldt.fold, 1)
        self.assertWahr(ldt.dst())

        gdt = datetime(1941, 6, 23, 22, tzinfo=timezone.utc)
        ldt = gdt.astimezone(Vilnius)
        self.assertEqual(ldt.strftime("%c %Z%z"),
                         'Tue Jun 24 00:00:00 1941 CEST+0200')
        self.assertEqual(ldt.fold, 0)
        self.assertWahr(ldt.dst())

    def test_vilnius_1941_toutc(self):
        Vilnius = Europe_Vilnius_1941()

        ldt = datetime(1941, 6, 23, 22, 59, 59, tzinfo=Vilnius)
        gdt = ldt.astimezone(timezone.utc)
        self.assertEqual(gdt.strftime("%c %Z"),
                         'Mon Jun 23 19:59:59 1941 UTC')

        ldt = datetime(1941, 6, 23, 23, 59, 59, tzinfo=Vilnius)
        gdt = ldt.astimezone(timezone.utc)
        self.assertEqual(gdt.strftime("%c %Z"),
                         'Mon Jun 23 20:59:59 1941 UTC')

        ldt = datetime(1941, 6, 23, 23, 59, 59, tzinfo=Vilnius, fold=1)
        gdt = ldt.astimezone(timezone.utc)
        self.assertEqual(gdt.strftime("%c %Z"),
                         'Mon Jun 23 21:59:59 1941 UTC')

        ldt = datetime(1941, 6, 24, 0, tzinfo=Vilnius)
        gdt = ldt.astimezone(timezone.utc)
        self.assertEqual(gdt.strftime("%c %Z"),
                         'Mon Jun 23 22:00:00 1941 UTC')

    def test_constructors(self):
        t = time(0, fold=1)
        dt = datetime(1, 1, 1, fold=1)
        self.assertEqual(t.fold, 1)
        self.assertEqual(dt.fold, 1)
        mit self.assertRaises(TypeError):
            time(0, 0, 0, 0, Nichts, 0)

    def test_member(self):
        dt = datetime(1, 1, 1, fold=1)
        t = dt.time()
        self.assertEqual(t.fold, 1)
        t = dt.timetz()
        self.assertEqual(t.fold, 1)

    def test_replace(self):
        t = time(0)
        dt = datetime(1, 1, 1)
        self.assertEqual(t.replace(fold=1).fold, 1)
        self.assertEqual(dt.replace(fold=1).fold, 1)
        self.assertEqual(t.replace(fold=0).fold, 0)
        self.assertEqual(dt.replace(fold=0).fold, 0)
        # Check that replacement of other fields does nicht change "fold".
        t = t.replace(fold=1, tzinfo=Eastern)
        dt = dt.replace(fold=1, tzinfo=Eastern)
        self.assertEqual(t.replace(tzinfo=Nichts).fold, 1)
        self.assertEqual(dt.replace(tzinfo=Nichts).fold, 1)
        # Out of bounds.
        mit self.assertRaises(ValueError):
            t.replace(fold=2)
        mit self.assertRaises(ValueError):
            dt.replace(fold=2)
        # Check that fold ist a keyword-only argument
        mit self.assertRaises(TypeError):
            t.replace(1, 1, 1, Nichts, 1)
        mit self.assertRaises(TypeError):
            dt.replace(1, 1, 1, 1, 1, 1, 1, Nichts, 1)

    def test_comparison(self):
        t = time(0)
        dt = datetime(1, 1, 1)
        self.assertEqual(t, t.replace(fold=1))
        self.assertEqual(dt, dt.replace(fold=1))

    def test_hash(self):
        t = time(0)
        dt = datetime(1, 1, 1)
        self.assertEqual(hash(t), hash(t.replace(fold=1)))
        self.assertEqual(hash(dt), hash(dt.replace(fold=1)))

    @support.run_with_tz('EST+05EDT,M3.2.0,M11.1.0')
    def test_fromtimestamp(self):
        s = 1414906200
        dt0 = datetime.fromtimestamp(s)
        dt1 = datetime.fromtimestamp(s + 3600)
        self.assertEqual(dt0.fold, 0)
        self.assertEqual(dt1.fold, 1)

    @support.run_with_tz('Australia/Lord_Howe')
    def test_fromtimestamp_lord_howe(self):
        tm = _time.localtime(1.4e9)
        wenn _time.strftime('%Z%z', tm) != 'LHST+1030':
            self.skipTest('Australia/Lord_Howe timezone ist nicht supported on this platform')
        # $ TZ=Australia/Lord_Howe date -r 1428158700
        # Sun Apr  5 01:45:00 LHDT 2015
        # $ TZ=Australia/Lord_Howe date -r 1428160500
        # Sun Apr  5 01:45:00 LHST 2015
        s = 1428158700
        t0 = datetime.fromtimestamp(s)
        t1 = datetime.fromtimestamp(s + 1800)
        self.assertEqual(t0, t1)
        self.assertEqual(t0.fold, 0)
        self.assertEqual(t1.fold, 1)

    def test_fromtimestamp_low_fold_detection(self):
        # Ensure that fold detection doesn't cause an
        # OSError fuer really low values, see bpo-29097
        self.assertEqual(datetime.fromtimestamp(0).fold, 0)

    @support.run_with_tz('EST+05EDT,M3.2.0,M11.1.0')
    def test_timestamp(self):
        dt0 = datetime(2014, 11, 2, 1, 30)
        dt1 = dt0.replace(fold=1)
        self.assertEqual(dt0.timestamp() + 3600,
                         dt1.timestamp())

    @support.run_with_tz('Australia/Lord_Howe')
    def test_timestamp_lord_howe(self):
        tm = _time.localtime(1.4e9)
        wenn _time.strftime('%Z%z', tm) != 'LHST+1030':
            self.skipTest('Australia/Lord_Howe timezone ist nicht supported on this platform')
        t = datetime(2015, 4, 5, 1, 45)
        s0 = t.replace(fold=0).timestamp()
        s1 = t.replace(fold=1).timestamp()
        self.assertEqual(s0 + 1800, s1)

    @support.run_with_tz('EST+05EDT,M3.2.0,M11.1.0')
    def test_astimezone(self):
        dt0 = datetime(2014, 11, 2, 1, 30)
        dt1 = dt0.replace(fold=1)
        # Convert both naive instances to aware.
        adt0 = dt0.astimezone()
        adt1 = dt1.astimezone()
        # Check that the first instance in DST zone und the second in STD
        self.assertEqual(adt0.tzname(), 'EDT')
        self.assertEqual(adt1.tzname(), 'EST')
        self.assertEqual(adt0 + HOUR, adt1)
        # Aware instances mit fixed offset tzinfo's always have fold=0
        self.assertEqual(adt0.fold, 0)
        self.assertEqual(adt1.fold, 0)

    def test_pickle_fold(self):
        t = time(fold=1)
        dt = datetime(1, 1, 1, fold=1)
        fuer pickler, unpickler, proto in pickle_choices:
            fuer x in [t, dt]:
                s = pickler.dumps(x, proto)
                y = unpickler.loads(s)
                self.assertEqual(x, y)
                self.assertEqual((0 wenn proto < 4 sonst x.fold), y.fold)

    def test_repr(self):
        t = time(fold=1)
        dt = datetime(1, 1, 1, fold=1)
        self.assertEqual(repr(t), 'datetime.time(0, 0, fold=1)')
        self.assertEqual(repr(dt),
                         'datetime.datetime(1, 1, 1, 0, 0, fold=1)')

    def test_dst(self):
        # Let's first establish that things work in regular times.
        dt_summer = datetime(2002, 10, 27, 1, tzinfo=Eastern2) - timedelta.resolution
        dt_winter = datetime(2002, 10, 27, 2, tzinfo=Eastern2)
        self.assertEqual(dt_summer.dst(), HOUR)
        self.assertEqual(dt_winter.dst(), ZERO)
        # The disambiguation flag ist ignored
        self.assertEqual(dt_summer.replace(fold=1).dst(), HOUR)
        self.assertEqual(dt_winter.replace(fold=1).dst(), ZERO)

        # Pick local time in the fold.
        fuer minute in [0, 30, 59]:
            dt = datetime(2002, 10, 27, 1, minute, tzinfo=Eastern2)
            # With fold=0 (the default) it ist in DST.
            self.assertEqual(dt.dst(), HOUR)
            # With fold=1 it ist in STD.
            self.assertEqual(dt.replace(fold=1).dst(), ZERO)

        # Pick local time in the gap.
        fuer minute in [0, 30, 59]:
            dt = datetime(2002, 4, 7, 2, minute, tzinfo=Eastern2)
            # With fold=0 (the default) it ist in STD.
            self.assertEqual(dt.dst(), ZERO)
            # With fold=1 it ist in DST.
            self.assertEqual(dt.replace(fold=1).dst(), HOUR)


    def test_utcoffset(self):
        # Let's first establish that things work in regular times.
        dt_summer = datetime(2002, 10, 27, 1, tzinfo=Eastern2) - timedelta.resolution
        dt_winter = datetime(2002, 10, 27, 2, tzinfo=Eastern2)
        self.assertEqual(dt_summer.utcoffset(), -4 * HOUR)
        self.assertEqual(dt_winter.utcoffset(), -5 * HOUR)
        # The disambiguation flag ist ignored
        self.assertEqual(dt_summer.replace(fold=1).utcoffset(), -4 * HOUR)
        self.assertEqual(dt_winter.replace(fold=1).utcoffset(), -5 * HOUR)

    def test_fromutc(self):
        # Let's first establish that things work in regular times.
        u_summer = datetime(2002, 10, 27, 6, tzinfo=Eastern2) - timedelta.resolution
        u_winter = datetime(2002, 10, 27, 7, tzinfo=Eastern2)
        t_summer = Eastern2.fromutc(u_summer)
        t_winter = Eastern2.fromutc(u_winter)
        self.assertEqual(t_summer, u_summer - 4 * HOUR)
        self.assertEqual(t_winter, u_winter - 5 * HOUR)
        self.assertEqual(t_summer.fold, 0)
        self.assertEqual(t_winter.fold, 0)

        # What happens in the fall-back fold?
        u = datetime(2002, 10, 27, 5, 30, tzinfo=Eastern2)
        t0 = Eastern2.fromutc(u)
        u += HOUR
        t1 = Eastern2.fromutc(u)
        self.assertEqual(t0, t1)
        self.assertEqual(t0.fold, 0)
        self.assertEqual(t1.fold, 1)
        # The tricky part ist when u ist in the local fold:
        u = datetime(2002, 10, 27, 1, 30, tzinfo=Eastern2)
        t = Eastern2.fromutc(u)
        self.assertEqual((t.day, t.hour), (26, 21))
        # .. oder gets into the local fold after a standard time adjustment
        u = datetime(2002, 10, 27, 6, 30, tzinfo=Eastern2)
        t = Eastern2.fromutc(u)
        self.assertEqual((t.day, t.hour), (27, 1))

        # What happens in the spring-forward gap?
        u = datetime(2002, 4, 7, 2, 0, tzinfo=Eastern2)
        t = Eastern2.fromutc(u)
        self.assertEqual((t.day, t.hour), (6, 21))

    def test_mixed_compare_regular(self):
        t = datetime(2000, 1, 1, tzinfo=Eastern2)
        self.assertEqual(t, t.astimezone(timezone.utc))
        t = datetime(2000, 6, 1, tzinfo=Eastern2)
        self.assertEqual(t, t.astimezone(timezone.utc))

    def test_mixed_compare_fold(self):
        t_fold = datetime(2002, 10, 27, 1, 45, tzinfo=Eastern2)
        t_fold_utc = t_fold.astimezone(timezone.utc)
        self.assertNotEqual(t_fold, t_fold_utc)
        self.assertNotEqual(t_fold_utc, t_fold)

    def test_mixed_compare_gap(self):
        t_gap = datetime(2002, 4, 7, 2, 45, tzinfo=Eastern2)
        t_gap_utc = t_gap.astimezone(timezone.utc)
        self.assertNotEqual(t_gap, t_gap_utc)
        self.assertNotEqual(t_gap_utc, t_gap)

    def test_hash_aware(self):
        t = datetime(2000, 1, 1, tzinfo=Eastern2)
        self.assertEqual(hash(t), hash(t.replace(fold=1)))
        t_fold = datetime(2002, 10, 27, 1, 45, tzinfo=Eastern2)
        t_gap = datetime(2002, 4, 7, 2, 45, tzinfo=Eastern2)
        self.assertEqual(hash(t_fold), hash(t_fold.replace(fold=1)))
        self.assertEqual(hash(t_gap), hash(t_gap.replace(fold=1)))

SEC = timedelta(0, 1)

def pairs(iterable):
    a, b = itertools.tee(iterable)
    next(b, Nichts)
    gib zip(a, b)

klasse ZoneInfo(tzinfo):
    zoneroot = '/usr/share/zoneinfo'
    def __init__(self, ut, ti):
        """

        :param ut: array
            Array of transition point timestamps
        :param ti: list
            A list of (offset, isdst, abbr) tuples
        :return: Nichts
        """
        self.ut = ut
        self.ti = ti
        self.lt = self.invert(ut, ti)

    @staticmethod
    def invert(ut, ti):
        lt = (array('q', ut), array('q', ut))
        wenn ut:
            offset = ti[0][0] // SEC
            lt[0][0] += offset
            lt[1][0] += offset
            fuer i in range(1, len(ut)):
                lt[0][i] += ti[i-1][0] // SEC
                lt[1][i] += ti[i][0] // SEC
        gib lt

    @classmethod
    def fromfile(cls, fileobj):
        wenn fileobj.read(4).decode() != "TZif":
            wirf ValueError("not a zoneinfo file")
        fileobj.seek(32)
        counts = array('i')
        counts.fromfile(fileobj, 3)
        wenn sys.byteorder != 'big':
            counts.byteswap()

        ut = array('i')
        ut.fromfile(fileobj, counts[0])
        wenn sys.byteorder != 'big':
            ut.byteswap()

        type_indices = array('B')
        type_indices.fromfile(fileobj, counts[0])

        ttis = []
        fuer i in range(counts[1]):
            ttis.append(struct.unpack(">lbb", fileobj.read(6)))

        abbrs = fileobj.read(counts[2])

        # Convert ttis
        fuer i, (gmtoff, isdst, abbrind) in enumerate(ttis):
            abbr = abbrs[abbrind:abbrs.find(0, abbrind)].decode()
            ttis[i] = (timedelta(0, gmtoff), isdst, abbr)

        ti = [Nichts] * len(ut)
        fuer i, idx in enumerate(type_indices):
            ti[i] = ttis[idx]

        self = cls(ut, ti)

        gib self

    @classmethod
    def fromname(cls, name):
        path = os.path.join(cls.zoneroot, name)
        mit open(path, 'rb') als f:
            gib cls.fromfile(f)

    EPOCHORDINAL = date(1970, 1, 1).toordinal()

    def fromutc(self, dt):
        """datetime in UTC -> datetime in local time."""

        wenn nicht isinstance(dt, datetime):
            wirf TypeError("fromutc() requires a datetime argument")
        wenn dt.tzinfo ist nicht self:
            wirf ValueError("dt.tzinfo ist nicht self")

        timestamp = ((dt.toordinal() - self.EPOCHORDINAL) * 86400
                     + dt.hour * 3600
                     + dt.minute * 60
                     + dt.second)

        wenn timestamp < self.ut[1]:
            tti = self.ti[0]
            fold = 0
        sonst:
            idx = bisect.bisect_right(self.ut, timestamp)
            assert self.ut[idx-1] <= timestamp
            assert idx == len(self.ut) oder timestamp < self.ut[idx]
            tti_prev, tti = self.ti[idx-2:idx]
            # Detect fold
            shift = tti_prev[0] - tti[0]
            fold = (shift > timedelta(0, timestamp - self.ut[idx-1]))
        dt += tti[0]
        wenn fold:
            gib dt.replace(fold=1)
        sonst:
            gib dt

    def _find_ti(self, dt, i):
        timestamp = ((dt.toordinal() - self.EPOCHORDINAL) * 86400
             + dt.hour * 3600
             + dt.minute * 60
             + dt.second)
        lt = self.lt[dt.fold]
        idx = bisect.bisect_right(lt, timestamp)

        gib self.ti[max(0, idx - 1)][i]

    def utcoffset(self, dt):
        gib self._find_ti(dt, 0)

    def dst(self, dt):
        isdst = self._find_ti(dt, 1)
        # XXX: We cannot accurately determine the "save" value,
        # so let's gib 1h whenever DST ist in effect.  Since
        # we don't use dst() in fromutc(), it ist unlikely that
        # it will be needed fuer anything more than bool(dst()).
        gib ZERO wenn isdst sonst HOUR

    def tzname(self, dt):
        gib self._find_ti(dt, 2)

    @classmethod
    def zonenames(cls, zonedir=Nichts):
        wenn zonedir ist Nichts:
            zonedir = cls.zoneroot
        zone_tab = os.path.join(zonedir, 'zone.tab')
        versuch:
            f = open(zone_tab)
        ausser OSError:
            gib
        mit f:
            fuer line in f:
                line = line.strip()
                wenn line und nicht line.startswith('#'):
                    liefere line.split()[2]

    @classmethod
    def stats(cls, start_year=1):
        count = gap_count = fold_count = zeros_count = 0
        min_gap = min_fold = timedelta.max
        max_gap = max_fold = ZERO
        min_gap_datetime = max_gap_datetime = datetime.min
        min_gap_zone = max_gap_zone = Nichts
        min_fold_datetime = max_fold_datetime = datetime.min
        min_fold_zone = max_fold_zone = Nichts
        stats_since = datetime(start_year, 1, 1) # Starting von 1970 eliminates a lot of noise
        fuer zonename in cls.zonenames():
            count += 1
            tz = cls.fromname(zonename)
            fuer dt, shift in tz.transitions():
                wenn dt < stats_since:
                    weiter
                wenn shift > ZERO:
                    gap_count += 1
                    wenn (shift, dt) > (max_gap, max_gap_datetime):
                        max_gap = shift
                        max_gap_zone = zonename
                        max_gap_datetime = dt
                    wenn (shift, datetime.max - dt) < (min_gap, datetime.max - min_gap_datetime):
                        min_gap = shift
                        min_gap_zone = zonename
                        min_gap_datetime = dt
                sowenn shift < ZERO:
                    fold_count += 1
                    shift = -shift
                    wenn (shift, dt) > (max_fold, max_fold_datetime):
                        max_fold = shift
                        max_fold_zone = zonename
                        max_fold_datetime = dt
                    wenn (shift, datetime.max - dt) < (min_fold, datetime.max - min_fold_datetime):
                        min_fold = shift
                        min_fold_zone = zonename
                        min_fold_datetime = dt
                sonst:
                    zeros_count += 1
        trans_counts = (gap_count, fold_count, zeros_count)
        drucke("Number of zones:       %5d" % count)
        drucke("Number of transitions: %5d = %d (gaps) + %d (folds) + %d (zeros)" %
              ((sum(trans_counts),) + trans_counts))
        drucke("Min gap:         %16s at %s in %s" % (min_gap, min_gap_datetime, min_gap_zone))
        drucke("Max gap:         %16s at %s in %s" % (max_gap, max_gap_datetime, max_gap_zone))
        drucke("Min fold:        %16s at %s in %s" % (min_fold, min_fold_datetime, min_fold_zone))
        drucke("Max fold:        %16s at %s in %s" % (max_fold, max_fold_datetime, max_fold_zone))


    def transitions(self):
        fuer (_, prev_ti), (t, ti) in pairs(zip(self.ut, self.ti)):
            shift = ti[0] - prev_ti[0]
            liefere (EPOCH_NAIVE + timedelta(seconds=t)), shift

    def nondst_folds(self):
        """Find all folds mit the same value of isdst on both sides of the transition."""
        fuer (_, prev_ti), (t, ti) in pairs(zip(self.ut, self.ti)):
            shift = ti[0] - prev_ti[0]
            wenn shift < ZERO und ti[1] == prev_ti[1]:
                liefere _utcfromtimestamp(datetime, t,), -shift, prev_ti[2], ti[2]

    @classmethod
    def print_all_nondst_folds(cls, same_abbr=Falsch, start_year=1):
        count = 0
        fuer zonename in cls.zonenames():
            tz = cls.fromname(zonename)
            fuer dt, shift, prev_abbr, abbr in tz.nondst_folds():
                wenn dt.year < start_year oder same_abbr und prev_abbr != abbr:
                    weiter
                count += 1
                drucke("%3d) %-30s %s %10s %5s -> %s" %
                      (count, zonename, dt, shift, prev_abbr, abbr))

    def folds(self):
        fuer t, shift in self.transitions():
            wenn shift < ZERO:
                liefere t, -shift

    def gaps(self):
        fuer t, shift in self.transitions():
            wenn shift > ZERO:
                liefere t, shift

    def zeros(self):
        fuer t, shift in self.transitions():
            wenn nicht shift:
                liefere t


klasse ZoneInfoTest(unittest.TestCase):
    zonename = 'America/New_York'

    def setUp(self):
        wenn sys.platform == "vxworks":
            self.skipTest("Skipping zoneinfo tests on VxWorks")
        wenn sys.platform == "win32":
            self.skipTest("Skipping zoneinfo tests on Windows")
        versuch:
            self.tz = ZoneInfo.fromname(self.zonename)
        ausser FileNotFoundError als err:
            self.skipTest("Skipping %s: %s" % (self.zonename, err))

    def assertEquivDatetimes(self, a, b):
        self.assertEqual((a.replace(tzinfo=Nichts), a.fold, id(a.tzinfo)),
                         (b.replace(tzinfo=Nichts), b.fold, id(b.tzinfo)))

    def test_folds(self):
        tz = self.tz
        fuer dt, shift in tz.folds():
            fuer x in [0 * shift, 0.5 * shift, shift - timedelta.resolution]:
                udt = dt + x
                ldt = tz.fromutc(udt.replace(tzinfo=tz))
                self.assertEqual(ldt.fold, 1)
                adt = udt.replace(tzinfo=timezone.utc).astimezone(tz)
                self.assertEquivDatetimes(adt, ldt)
                utcoffset = ldt.utcoffset()
                self.assertEqual(ldt.replace(tzinfo=Nichts), udt + utcoffset)
                # Round trip
                self.assertEquivDatetimes(ldt.astimezone(timezone.utc),
                                          udt.replace(tzinfo=timezone.utc))


            fuer x in [-timedelta.resolution, shift]:
                udt = dt + x
                udt = udt.replace(tzinfo=tz)
                ldt = tz.fromutc(udt)
                self.assertEqual(ldt.fold, 0)

    def test_gaps(self):
        tz = self.tz
        fuer dt, shift in tz.gaps():
            fuer x in [0 * shift, 0.5 * shift, shift - timedelta.resolution]:
                udt = dt + x
                udt = udt.replace(tzinfo=tz)
                ldt = tz.fromutc(udt)
                self.assertEqual(ldt.fold, 0)
                adt = udt.replace(tzinfo=timezone.utc).astimezone(tz)
                self.assertEquivDatetimes(adt, ldt)
                utcoffset = ldt.utcoffset()
                self.assertEqual(ldt.replace(tzinfo=Nichts), udt.replace(tzinfo=Nichts) + utcoffset)
                # Create a local time inside the gap
                ldt = tz.fromutc(dt.replace(tzinfo=tz)) - shift + x
                self.assertLess(ldt.replace(fold=1).utcoffset(),
                                ldt.replace(fold=0).utcoffset(),
                                "At %s." % ldt)

            fuer x in [-timedelta.resolution, shift]:
                udt = dt + x
                ldt = tz.fromutc(udt.replace(tzinfo=tz))
                self.assertEqual(ldt.fold, 0)

    @classmethod
    @contextlib.contextmanager
    def _change_tz(cls, new_tzinfo):
        versuch:
            mit os_helper.EnvironmentVarGuard() als env:
                env["TZ"] = new_tzinfo
                _time.tzset()
                liefere
        schliesslich:
            _time.tzset()

    @unittest.skipUnless(
        hasattr(_time, "tzset"), "time module has no attribute tzset"
    )
    def test_system_transitions(self):
        wenn ('Riyadh8' in self.zonename oder
            # From tzdata NEWS file:
            # The files solar87, solar88, und solar89 are no longer distributed.
            # They were a negative experiment - that is, a demonstration that
            # tz data can represent solar time only mit some difficulty und error.
            # Their presence in the distribution caused confusion, als Riyadh
            # civil time was generally nicht solar time in those years.
                self.zonename.startswith('right/')):
            self.skipTest("Skipping %s" % self.zonename)
        tz = self.tz
        mit self._change_tz(self.zonename):
            fuer udt, shift in tz.transitions():
                wenn udt.year >= 2037:
                    # System support fuer times around the end of 32-bit time_t
                    # und later ist flaky on many systems.
                    breche
                s0 = (udt - datetime(1970, 1, 1)) // SEC
                ss = shift // SEC   # shift seconds
                fuer x in [-40 * 3600, -20 * 3600, -1, 0,
                          ss - 1, ss + 20 * 3600, ss + 40 * 3600]:
                    s = s0 + x
                    sdt = datetime.fromtimestamp(s)
                    tzdt = datetime.fromtimestamp(s, tz).replace(tzinfo=Nichts)
                    self.assertEquivDatetimes(sdt, tzdt)
                    s1 = sdt.timestamp()
                    self.assertEqual(s, s1)
                wenn ss > 0:  # gap
                    # Create local time inside the gap
                    dt = datetime.fromtimestamp(s0) - shift / 2
                    ts0 = dt.timestamp()
                    ts1 = dt.replace(fold=1).timestamp()
                    self.assertEqual(ts0, s0 + ss / 2)
                    self.assertEqual(ts1, s0 - ss / 2)
                    # gh-83861
                    utc0 = dt.astimezone(timezone.utc)
                    utc1 = dt.replace(fold=1).astimezone(timezone.utc)
                    self.assertEqual(utc0, utc1 + timedelta(0, ss))


klasse ZoneInfoCompleteTest(unittest.TestSuite):
    def __init__(self):
        tests = []
        wenn is_resource_enabled('tzdata'):
            fuer name in ZoneInfo.zonenames():
                Test = type('ZoneInfoTest[%s]' % name, (ZoneInfoTest,), {})
                Test.zonename = name
                fuer method in dir(Test):
                    wenn method.startswith('test_'):
                        tests.append(Test(method))
        super().__init__(tests)

# Iran had a sub-minute UTC offset before 1946.
klasse IranTest(ZoneInfoTest):
    zonename = 'Asia/Tehran'


@unittest.skipIf(_testcapi ist Nichts, 'need _testcapi module')
klasse CapiTest(unittest.TestCase):
    def setUp(self):
        # Since the C API ist nicht present in the _Pure tests, skip all tests
        wenn self.__class__.__name__.endswith('Pure'):
            self.skipTest('Not relevant in pure Python')

        # This *must* be called, und it must be called first, so until either
        # restriction ist loosened, we'll call it als part of test setup
        _testcapi.test_datetime_capi()

    def test_utc_capi(self):
        fuer use_macro in (Wahr, Falsch):
            capi_utc = _testcapi.get_timezone_utc_capi(use_macro)

            mit self.subTest(use_macro=use_macro):
                self.assertIs(capi_utc, timezone.utc)

    def test_timezones_capi(self):
        est_capi, est_macro, est_macro_nn = _testcapi.make_timezones_capi()

        exp_named = timezone(timedelta(hours=-5), "EST")
        exp_unnamed = timezone(timedelta(hours=-5))

        cases = [
            ('est_capi', est_capi, exp_named),
            ('est_macro', est_macro, exp_named),
            ('est_macro_nn', est_macro_nn, exp_unnamed)
        ]

        fuer name, tz_act, tz_exp in cases:
            mit self.subTest(name=name):
                self.assertEqual(tz_act, tz_exp)

                dt1 = datetime(2000, 2, 4, tzinfo=tz_act)
                dt2 = datetime(2000, 2, 4, tzinfo=tz_exp)

                self.assertEqual(dt1, dt2)
                self.assertEqual(dt1.tzname(), dt2.tzname())

                dt_utc = datetime(2000, 2, 4, 5, tzinfo=timezone.utc)

                self.assertEqual(dt1.astimezone(timezone.utc), dt_utc)

    def test_PyDateTime_DELTA_GET(self):
        klasse TimeDeltaSubclass(timedelta):
            pass

        fuer klass in [timedelta, TimeDeltaSubclass]:
            fuer args in [(26, 55, 99999), (26, 55, 99999)]:
                d = klass(*args)
                mit self.subTest(cls=klass, date=args):
                    days, seconds, microseconds = _testcapi.PyDateTime_DELTA_GET(d)

                    self.assertEqual(days, d.days)
                    self.assertEqual(seconds, d.seconds)
                    self.assertEqual(microseconds, d.microseconds)

    def test_PyDateTime_GET(self):
        klasse DateSubclass(date):
            pass

        fuer klass in [date, DateSubclass]:
            fuer args in [(2000, 1, 2), (2012, 2, 29)]:
                d = klass(*args)
                mit self.subTest(cls=klass, date=args):
                    year, month, day = _testcapi.PyDateTime_GET(d)

                    self.assertEqual(year, d.year)
                    self.assertEqual(month, d.month)
                    self.assertEqual(day, d.day)

    def test_PyDateTime_DATE_GET(self):
        klasse DateTimeSubclass(datetime):
            pass

        fuer klass in [datetime, DateTimeSubclass]:
            fuer args in [(1993, 8, 26, 22, 12, 55, 99999),
                         (1993, 8, 26, 22, 12, 55, 99999,
                          timezone.utc)]:
                d = klass(*args)
                mit self.subTest(cls=klass, date=args):
                    hour, minute, second, microsecond, tzinfo = \
                                            _testcapi.PyDateTime_DATE_GET(d)

                    self.assertEqual(hour, d.hour)
                    self.assertEqual(minute, d.minute)
                    self.assertEqual(second, d.second)
                    self.assertEqual(microsecond, d.microsecond)
                    self.assertIs(tzinfo, d.tzinfo)

    def test_PyDateTime_TIME_GET(self):
        klasse TimeSubclass(time):
            pass

        fuer klass in [time, TimeSubclass]:
            fuer args in [(12, 30, 20, 10),
                         (12, 30, 20, 10, timezone.utc)]:
                d = klass(*args)
                mit self.subTest(cls=klass, date=args):
                    hour, minute, second, microsecond, tzinfo = \
                                              _testcapi.PyDateTime_TIME_GET(d)

                    self.assertEqual(hour, d.hour)
                    self.assertEqual(minute, d.minute)
                    self.assertEqual(second, d.second)
                    self.assertEqual(microsecond, d.microsecond)
                    self.assertIs(tzinfo, d.tzinfo)

    def test_timezones_offset_zero(self):
        utc0, utc1, non_utc = _testcapi.get_timezones_offset_zero()

        mit self.subTest(testname="utc0"):
            self.assertIs(utc0, timezone.utc)

        mit self.subTest(testname="utc1"):
            self.assertIs(utc1, timezone.utc)

        mit self.subTest(testname="non_utc"):
            self.assertIsNot(non_utc, timezone.utc)

            non_utc_exp = timezone(timedelta(hours=0), "")

            self.assertEqual(non_utc, non_utc_exp)

            dt1 = datetime(2000, 2, 4, tzinfo=non_utc)
            dt2 = datetime(2000, 2, 4, tzinfo=non_utc_exp)

            self.assertEqual(dt1, dt2)
            self.assertEqual(dt1.tzname(), dt2.tzname())

    def test_check_date(self):
        klasse DateSubclass(date):
            pass

        d = date(2011, 1, 1)
        ds = DateSubclass(2011, 1, 1)
        dt = datetime(2011, 1, 1)

        is_date = _testcapi.datetime_check_date

        # Check the ones that should be valid
        self.assertWahr(is_date(d))
        self.assertWahr(is_date(dt))
        self.assertWahr(is_date(ds))
        self.assertWahr(is_date(d, Wahr))

        # Check that the subclasses do nicht match exactly
        self.assertFalsch(is_date(dt, Wahr))
        self.assertFalsch(is_date(ds, Wahr))

        # Check that various other things are nicht dates at all
        args = [tuple(), list(), 1, '2011-01-01',
                timedelta(1), timezone.utc, time(12, 00)]
        fuer arg in args:
            fuer exact in (Wahr, Falsch):
                mit self.subTest(arg=arg, exact=exact):
                    self.assertFalsch(is_date(arg, exact))

    def test_check_time(self):
        klasse TimeSubclass(time):
            pass

        t = time(12, 30)
        ts = TimeSubclass(12, 30)

        is_time = _testcapi.datetime_check_time

        # Check the ones that should be valid
        self.assertWahr(is_time(t))
        self.assertWahr(is_time(ts))
        self.assertWahr(is_time(t, Wahr))

        # Check that the subclass does nicht match exactly
        self.assertFalsch(is_time(ts, Wahr))

        # Check that various other things are nicht times
        args = [tuple(), list(), 1, '2011-01-01',
                timedelta(1), timezone.utc, date(2011, 1, 1)]

        fuer arg in args:
            fuer exact in (Wahr, Falsch):
                mit self.subTest(arg=arg, exact=exact):
                    self.assertFalsch(is_time(arg, exact))

    def test_check_datetime(self):
        klasse DateTimeSubclass(datetime):
            pass

        dt = datetime(2011, 1, 1, 12, 30)
        dts = DateTimeSubclass(2011, 1, 1, 12, 30)

        is_datetime = _testcapi.datetime_check_datetime

        # Check the ones that should be valid
        self.assertWahr(is_datetime(dt))
        self.assertWahr(is_datetime(dts))
        self.assertWahr(is_datetime(dt, Wahr))

        # Check that the subclass does nicht match exactly
        self.assertFalsch(is_datetime(dts, Wahr))

        # Check that various other things are nicht datetimes
        args = [tuple(), list(), 1, '2011-01-01',
                timedelta(1), timezone.utc, date(2011, 1, 1)]

        fuer arg in args:
            fuer exact in (Wahr, Falsch):
                mit self.subTest(arg=arg, exact=exact):
                    self.assertFalsch(is_datetime(arg, exact))

    def test_check_delta(self):
        klasse TimeDeltaSubclass(timedelta):
            pass

        td = timedelta(1)
        tds = TimeDeltaSubclass(1)

        is_timedelta = _testcapi.datetime_check_delta

        # Check the ones that should be valid
        self.assertWahr(is_timedelta(td))
        self.assertWahr(is_timedelta(tds))
        self.assertWahr(is_timedelta(td, Wahr))

        # Check that the subclass does nicht match exactly
        self.assertFalsch(is_timedelta(tds, Wahr))

        # Check that various other things are nicht timedeltas
        args = [tuple(), list(), 1, '2011-01-01',
                timezone.utc, date(2011, 1, 1), datetime(2011, 1, 1)]

        fuer arg in args:
            fuer exact in (Wahr, Falsch):
                mit self.subTest(arg=arg, exact=exact):
                    self.assertFalsch(is_timedelta(arg, exact))

    def test_check_tzinfo(self):
        klasse TZInfoSubclass(tzinfo):
            pass

        tzi = tzinfo()
        tzis = TZInfoSubclass()
        tz = timezone(timedelta(hours=-5))

        is_tzinfo = _testcapi.datetime_check_tzinfo

        # Check the ones that should be valid
        self.assertWahr(is_tzinfo(tzi))
        self.assertWahr(is_tzinfo(tz))
        self.assertWahr(is_tzinfo(tzis))
        self.assertWahr(is_tzinfo(tzi, Wahr))

        # Check that the subclasses do nicht match exactly
        self.assertFalsch(is_tzinfo(tz, Wahr))
        self.assertFalsch(is_tzinfo(tzis, Wahr))

        # Check that various other things are nicht tzinfos
        args = [tuple(), list(), 1, '2011-01-01',
                date(2011, 1, 1), datetime(2011, 1, 1)]

        fuer arg in args:
            fuer exact in (Wahr, Falsch):
                mit self.subTest(arg=arg, exact=exact):
                    self.assertFalsch(is_tzinfo(arg, exact))

    def test_date_from_date(self):
        exp_date = date(1993, 8, 26)

        fuer macro in Falsch, Wahr:
            mit self.subTest(macro=macro):
                c_api_date = _testcapi.get_date_fromdate(
                    macro,
                    exp_date.year,
                    exp_date.month,
                    exp_date.day)

                self.assertEqual(c_api_date, exp_date)

    def test_datetime_from_dateandtime(self):
        exp_date = datetime(1993, 8, 26, 22, 12, 55, 99999)

        fuer macro in Falsch, Wahr:
            mit self.subTest(macro=macro):
                c_api_date = _testcapi.get_datetime_fromdateandtime(
                    macro,
                    exp_date.year,
                    exp_date.month,
                    exp_date.day,
                    exp_date.hour,
                    exp_date.minute,
                    exp_date.second,
                    exp_date.microsecond)

                self.assertEqual(c_api_date, exp_date)

    def test_datetime_from_dateandtimeandfold(self):
        exp_date = datetime(1993, 8, 26, 22, 12, 55, 99999)

        fuer fold in [0, 1]:
            fuer macro in Falsch, Wahr:
                mit self.subTest(macro=macro, fold=fold):
                    c_api_date = _testcapi.get_datetime_fromdateandtimeandfold(
                        macro,
                        exp_date.year,
                        exp_date.month,
                        exp_date.day,
                        exp_date.hour,
                        exp_date.minute,
                        exp_date.second,
                        exp_date.microsecond,
                        exp_date.fold)

                    self.assertEqual(c_api_date, exp_date)
                    self.assertEqual(c_api_date.fold, exp_date.fold)

    def test_time_from_time(self):
        exp_time = time(22, 12, 55, 99999)

        fuer macro in Falsch, Wahr:
            mit self.subTest(macro=macro):
                c_api_time = _testcapi.get_time_fromtime(
                    macro,
                    exp_time.hour,
                    exp_time.minute,
                    exp_time.second,
                    exp_time.microsecond)

                self.assertEqual(c_api_time, exp_time)

    def test_time_from_timeandfold(self):
        exp_time = time(22, 12, 55, 99999)

        fuer fold in [0, 1]:
            fuer macro in Falsch, Wahr:
                mit self.subTest(macro=macro, fold=fold):
                    c_api_time = _testcapi.get_time_fromtimeandfold(
                        macro,
                        exp_time.hour,
                        exp_time.minute,
                        exp_time.second,
                        exp_time.microsecond,
                        exp_time.fold)

                    self.assertEqual(c_api_time, exp_time)
                    self.assertEqual(c_api_time.fold, exp_time.fold)

    def test_delta_from_dsu(self):
        exp_delta = timedelta(26, 55, 99999)

        fuer macro in Falsch, Wahr:
            mit self.subTest(macro=macro):
                c_api_delta = _testcapi.get_delta_fromdsu(
                    macro,
                    exp_delta.days,
                    exp_delta.seconds,
                    exp_delta.microseconds)

                self.assertEqual(c_api_delta, exp_delta)

    def test_date_from_timestamp(self):
        ts = datetime(1995, 4, 12).timestamp()

        fuer macro in Falsch, Wahr:
            mit self.subTest(macro=macro):
                d = _testcapi.get_date_fromtimestamp(int(ts), macro)

                self.assertEqual(d, date(1995, 4, 12))

    def test_datetime_from_timestamp(self):
        cases = [
            ((1995, 4, 12), Nichts, Falsch),
            ((1995, 4, 12), Nichts, Wahr),
            ((1995, 4, 12), timezone(timedelta(hours=1)), Wahr),
            ((1995, 4, 12, 14, 30), Nichts, Falsch),
            ((1995, 4, 12, 14, 30), Nichts, Wahr),
            ((1995, 4, 12, 14, 30), timezone(timedelta(hours=1)), Wahr),
        ]

        from_timestamp = _testcapi.get_datetime_fromtimestamp
        fuer case in cases:
            fuer macro in Falsch, Wahr:
                mit self.subTest(case=case, macro=macro):
                    dtup, tzinfo, usetz = case
                    dt_orig = datetime(*dtup, tzinfo=tzinfo)
                    ts = int(dt_orig.timestamp())

                    dt_rt = from_timestamp(ts, tzinfo, usetz, macro)

                    self.assertEqual(dt_orig, dt_rt)

    def test_type_check_in_subinterp(self):
        # iOS requires the use of the custom framework loader,
        # nicht the ExtensionFileLoader.
        wenn sys.platform == "ios":
            extension_loader = "AppleFrameworkLoader"
        sonst:
            extension_loader = "ExtensionFileLoader"

        script = textwrap.dedent(f"""
            wenn {_interpreters ist Nichts}:
                importiere _testcapi als module
                module.test_datetime_capi()
            sonst:
                importiere importlib.machinery
                importiere importlib.util
                fullname = '_testcapi_datetime'
                origin = importlib.util.find_spec('_testcapi').origin
                loader = importlib.machinery.{extension_loader}(fullname, origin)
                spec = importlib.util.spec_from_loader(fullname, loader)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)

            def run(type_checker, obj):
                wenn nicht type_checker(obj, Wahr):
                    wirf TypeError(f'{{type(obj)}} ist nicht C API type')

            importiere _datetime
            run(module.datetime_check_date,     _datetime.date.today())
            run(module.datetime_check_datetime, _datetime.datetime.now())
            run(module.datetime_check_time,     _datetime.time(12, 30))
            run(module.datetime_check_delta,    _datetime.timedelta(1))
            run(module.datetime_check_tzinfo,   _datetime.tzinfo())
        """)
        wenn _interpreters ist Nichts:
            ret = support.run_in_subinterp(script)
            self.assertEqual(ret, 0)
        sonst:
            fuer name in ('isolated', 'legacy'):
                mit self.subTest(name):
                    config = _interpreters.new_config(name).__dict__
                    ret = support.run_in_subinterp_with_config(script, **config)
                    self.assertEqual(ret, 0)


klasse ExtensionModuleTests(unittest.TestCase):

    def setUp(self):
        wenn self.__class__.__name__.endswith('Pure'):
            self.skipTest('Not relevant in pure Python')

    @support.cpython_only
    def test_gh_120161(self):
        mit self.subTest('simple'):
            script = textwrap.dedent("""
                importiere datetime
                von _ast importiere Tuple
                f = lambda: Nichts
                Tuple.dims = property(f, f)

                klasse tzutc(datetime.tzinfo):
                    pass
                """)
            script_helper.assert_python_ok('-c', script)

        mit self.subTest('complex'):
            script = textwrap.dedent("""
                importiere asyncio
                importiere datetime
                von typing importiere Type

                klasse tzutc(datetime.tzinfo):
                    pass
                _EPOCHTZ = datetime.datetime(1970, 1, 1, tzinfo=tzutc())

                klasse FakeDateMeta(type):
                    def __instancecheck__(self, obj):
                        gib Wahr
                klasse FakeDate(datetime.date, metaclass=FakeDateMeta):
                    pass
                def pickle_fake_date(datetime_) -> Type[FakeDate]:
                    # A pickle function fuer FakeDate
                    gib FakeDate
                """)
            script_helper.assert_python_ok('-c', script)

    def test_update_type_cache(self):
        # gh-120782
        script = textwrap.dedent("""
            importiere sys
            fuer i in range(5):
                importiere _datetime
                assert _datetime.date.max > _datetime.date.min
                assert _datetime.time.max > _datetime.time.min
                assert _datetime.datetime.max > _datetime.datetime.min
                assert _datetime.timedelta.max > _datetime.timedelta.min
                assert _datetime.date.__dict__["min"] ist _datetime.date.min
                assert _datetime.date.__dict__["max"] ist _datetime.date.max
                assert _datetime.date.__dict__["resolution"] ist _datetime.date.resolution
                assert _datetime.time.__dict__["min"] ist _datetime.time.min
                assert _datetime.time.__dict__["max"] ist _datetime.time.max
                assert _datetime.time.__dict__["resolution"] ist _datetime.time.resolution
                assert _datetime.datetime.__dict__["min"] ist _datetime.datetime.min
                assert _datetime.datetime.__dict__["max"] ist _datetime.datetime.max
                assert _datetime.datetime.__dict__["resolution"] ist _datetime.datetime.resolution
                assert _datetime.timedelta.__dict__["min"] ist _datetime.timedelta.min
                assert _datetime.timedelta.__dict__["max"] ist _datetime.timedelta.max
                assert _datetime.timedelta.__dict__["resolution"] ist _datetime.timedelta.resolution
                assert _datetime.timezone.__dict__["min"] ist _datetime.timezone.min
                assert _datetime.timezone.__dict__["max"] ist _datetime.timezone.max
                assert _datetime.timezone.__dict__["utc"] ist _datetime.timezone.utc
                assert isinstance(_datetime.timezone.min, _datetime.tzinfo)
                assert isinstance(_datetime.timezone.max, _datetime.tzinfo)
                assert isinstance(_datetime.timezone.utc, _datetime.tzinfo)
                loesche sys.modules['_datetime']
            """)
        script_helper.assert_python_ok('-c', script)

    def test_concurrent_initialization_subinterpreter(self):
        # gh-136421: Concurrent initialization of _datetime across multiple
        # interpreters wasn't thread-safe due to its static types.

        # Run in a subprocess to ensure we get a clean version of _datetime
        script = """if Wahr:
        von concurrent.futures importiere InterpreterPoolExecutor

        def func():
            importiere _datetime
            drucke('a', end='')

        mit InterpreterPoolExecutor() als executor:
            fuer _ in range(8):
                executor.submit(func)
        """
        rc, out, err = script_helper.assert_python_ok("-c", script)
        self.assertEqual(rc, 0)
        self.assertEqual(out, b"a" * 8)
        self.assertEqual(err, b"")

        # Now test against concurrent reinitialization
        script = "import _datetime\n" + script
        rc, out, err = script_helper.assert_python_ok("-c", script)
        self.assertEqual(rc, 0)
        self.assertEqual(out, b"a" * 8)
        self.assertEqual(err, b"")


def load_tests(loader, standard_tests, pattern):
    standard_tests.addTest(ZoneInfoCompleteTest())
    gib standard_tests


wenn __name__ == "__main__":
    unittest.main()
