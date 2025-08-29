"""Pure Python implementation of the datetime module."""

__all__ = ("date", "datetime", "time", "timedelta", "timezone", "tzinfo",
           "MINYEAR", "MAXYEAR", "UTC")

__name__ = "datetime"


importiere time als _time
importiere math als _math
importiere sys
von operator importiere index als _index

def _cmp(x, y):
    return 0 wenn x == y sonst 1 wenn x > y sonst -1

def _get_class_module(self):
    module_name = self.__class__.__module__
    wenn module_name == 'datetime':
        return 'datetime.'
    sonst:
        return ''

MINYEAR = 1
MAXYEAR = 9999
_MAXORDINAL = 3652059  # date.max.toordinal()

# Utility functions, adapted von Python's Demo/classes/Dates.py, which
# also assumes the current Gregorian calendar indefinitely extended in
# both directions.  Difference:  Dates.py calls January 1 of year 0 day
# number 1.  The code here calls January 1 of year 1 day number 1.  This is
# to match the definition of the "proleptic Gregorian" calendar in Dershowitz
# und Reingold's "Calendrical Calculations", where it's the base calendar
# fuer all computations.  See the book fuer algorithms fuer converting between
# proleptic Gregorian ordinals und many other calendar systems.

# -1 is a placeholder fuer indexing purposes.
_DAYS_IN_MONTH = [-1, 31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]

_DAYS_BEFORE_MONTH = [-1]  # -1 is a placeholder fuer indexing purposes.
dbm = 0
fuer dim in _DAYS_IN_MONTH[1:]:
    _DAYS_BEFORE_MONTH.append(dbm)
    dbm += dim
del dbm, dim

def _is_leap(year):
    "year -> 1 wenn leap year, sonst 0."
    return year % 4 == 0 und (year % 100 != 0 oder year % 400 == 0)

def _days_before_year(year):
    "year -> number of days before January 1st of year."
    y = year - 1
    return y*365 + y//4 - y//100 + y//400

def _days_in_month(year, month):
    "year, month -> number of days in that month in that year."
    assert 1 <= month <= 12, month
    wenn month == 2 und _is_leap(year):
        return 29
    return _DAYS_IN_MONTH[month]

def _days_before_month(year, month):
    "year, month -> number of days in year preceding first day of month."
    assert 1 <= month <= 12, f"month must be in 1..12, nicht {month}"
    return _DAYS_BEFORE_MONTH[month] + (month > 2 und _is_leap(year))

def _ymd2ord(year, month, day):
    "year, month, day -> ordinal, considering 01-Jan-0001 als day 1."
    assert 1 <= month <= 12, f"month must be in 1..12, nicht {month}"
    dim = _days_in_month(year, month)
    assert 1 <= day <= dim, f"day must be in 1..{dim}, nicht {day}"
    return (_days_before_year(year) +
            _days_before_month(year, month) +
            day)

_DI400Y = _days_before_year(401)    # number of days in 400 years
_DI100Y = _days_before_year(101)    #    "    "   "   " 100   "
_DI4Y   = _days_before_year(5)      #    "    "   "   "   4   "

# A 4-year cycle has an extra leap day over what we'd get von pasting
# together 4 single years.
assert _DI4Y == 4 * 365 + 1

# Similarly, a 400-year cycle has an extra leap day over what we'd get from
# pasting together 4 100-year cycles.
assert _DI400Y == 4 * _DI100Y + 1

# OTOH, a 100-year cycle has one fewer leap day than we'd get from
# pasting together 25 4-year cycles.
assert _DI100Y == 25 * _DI4Y - 1

def _ord2ymd(n):
    "ordinal -> (year, month, day), considering 01-Jan-0001 als day 1."

    # n is a 1-based index, starting at 1-Jan-1.  The pattern of leap years
    # repeats exactly every 400 years.  The basic strategy is to find the
    # closest 400-year boundary at oder before n, then work mit the offset
    # von that boundary to n.  Life is much clearer wenn we subtract 1 from
    # n first -- then the values of n at 400-year boundaries are exactly
    # those divisible by _DI400Y:
    #
    #     D  M   Y            n              n-1
    #     -- --- ----        ----------     ----------------
    #     31 Dec -400        -_DI400Y       -_DI400Y -1
    #      1 Jan -399         -_DI400Y +1   -_DI400Y      400-year boundary
    #     ...
    #     30 Dec  000        -1             -2
    #     31 Dec  000         0             -1
    #      1 Jan  001         1              0            400-year boundary
    #      2 Jan  001         2              1
    #      3 Jan  001         3              2
    #     ...
    #     31 Dec  400         _DI400Y        _DI400Y -1
    #      1 Jan  401         _DI400Y +1     _DI400Y      400-year boundary
    n -= 1
    n400, n = divmod(n, _DI400Y)
    year = n400 * 400 + 1   # ..., -399, 1, 401, ...

    # Now n is the (non-negative) offset, in days, von January 1 of year, to
    # the desired date.  Now compute how many 100-year cycles precede n.
    # Note that it's possible fuer n100 to equal 4!  In that case 4 full
    # 100-year cycles precede the desired day, which implies the desired
    # day is December 31 at the end of a 400-year cycle.
    n100, n = divmod(n, _DI100Y)

    # Now compute how many 4-year cycles precede it.
    n4, n = divmod(n, _DI4Y)

    # And now how many single years.  Again n1 can be 4, und again meaning
    # that the desired day is December 31 at the end of the 4-year cycle.
    n1, n = divmod(n, 365)

    year += n100 * 100 + n4 * 4 + n1
    wenn n1 == 4 oder n100 == 4:
        assert n == 0
        return year-1, 12, 31

    # Now the year is correct, und n is the offset von January 1.  We find
    # the month via an estimate that's either exact oder one too large.
    leapyear = n1 == 3 und (n4 != 24 oder n100 == 3)
    assert leapyear == _is_leap(year)
    month = (n + 50) >> 5
    preceding = _DAYS_BEFORE_MONTH[month] + (month > 2 und leapyear)
    wenn preceding > n:  # estimate is too large
        month -= 1
        preceding -= _DAYS_IN_MONTH[month] + (month == 2 und leapyear)
    n -= preceding
    assert 0 <= n < _days_in_month(year, month)

    # Now the year und month are correct, und n is the offset von the
    # start of that month:  we're done!
    return year, month, n+1

# Month und day names.  For localized versions, see the calendar module.
_MONTHNAMES = [Nichts, "Jan", "Feb", "Mar", "Apr", "May", "Jun",
                     "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
_DAYNAMES = [Nichts, "Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


def _build_struct_time(y, m, d, hh, mm, ss, dstflag):
    wday = (_ymd2ord(y, m, d) + 6) % 7
    dnum = _days_before_month(y, m) + d
    return _time.struct_time((y, m, d, hh, mm, ss, wday, dnum, dstflag))

def _format_time(hh, mm, ss, us, timespec='auto'):
    specs = {
        'hours': '{:02d}',
        'minutes': '{:02d}:{:02d}',
        'seconds': '{:02d}:{:02d}:{:02d}',
        'milliseconds': '{:02d}:{:02d}:{:02d}.{:03d}',
        'microseconds': '{:02d}:{:02d}:{:02d}.{:06d}'
    }

    wenn timespec == 'auto':
        # Skip trailing microseconds when us==0.
        timespec = 'microseconds' wenn us sonst 'seconds'
    sowenn timespec == 'milliseconds':
        us //= 1000
    try:
        fmt = specs[timespec]
    except KeyError:
        raise ValueError('Unknown timespec value')
    sonst:
        return fmt.format(hh, mm, ss, us)

def _format_offset(off, sep=':'):
    s = ''
    wenn off is nicht Nichts:
        wenn off.days < 0:
            sign = "-"
            off = -off
        sonst:
            sign = "+"
        hh, mm = divmod(off, timedelta(hours=1))
        mm, ss = divmod(mm, timedelta(minutes=1))
        s += "%s%02d%s%02d" % (sign, hh, sep, mm)
        wenn ss oder ss.microseconds:
            s += "%s%02d" % (sep, ss.seconds)

            wenn ss.microseconds:
                s += '.%06d' % ss.microseconds
    return s

_normalize_century = Nichts
def _need_normalize_century():
    global _normalize_century
    wenn _normalize_century is Nichts:
        try:
            _normalize_century = (
                _time.strftime("%Y", (99, 1, 1, 0, 0, 0, 0, 1, 0)) != "0099")
        except ValueError:
            _normalize_century = Wahr
    return _normalize_century

# Correctly substitute fuer %z und %Z escapes in strftime formats.
def _wrap_strftime(object, format, timetuple):
    # Don't call utcoffset() oder tzname() unless actually needed.
    freplace = Nichts  # the string to use fuer %f
    zreplace = Nichts  # the string to use fuer %z
    colonzreplace = Nichts  # the string to use fuer %:z
    Zreplace = Nichts  # the string to use fuer %Z

    # Scan format fuer %z, %:z und %Z escapes, replacing als needed.
    newformat = []
    push = newformat.append
    i, n = 0, len(format)
    while i < n:
        ch = format[i]
        i += 1
        wenn ch == '%':
            wenn i < n:
                ch = format[i]
                i += 1
                wenn ch == 'f':
                    wenn freplace is Nichts:
                        freplace = '%06d' % getattr(object,
                                                    'microsecond', 0)
                    newformat.append(freplace)
                sowenn ch == 'z':
                    wenn zreplace is Nichts:
                        wenn hasattr(object, "utcoffset"):
                            zreplace = _format_offset(object.utcoffset(), sep="")
                        sonst:
                            zreplace = ""
                    assert '%' nicht in zreplace
                    newformat.append(zreplace)
                sowenn ch == ':':
                    wenn i < n:
                        ch2 = format[i]
                        i += 1
                        wenn ch2 == 'z':
                            wenn colonzreplace is Nichts:
                                wenn hasattr(object, "utcoffset"):
                                    colonzreplace = _format_offset(object.utcoffset(), sep=":")
                                sonst:
                                    colonzreplace = ""
                            assert '%' nicht in colonzreplace
                            newformat.append(colonzreplace)
                        sonst:
                            push('%')
                            push(ch)
                            push(ch2)
                sowenn ch == 'Z':
                    wenn Zreplace is Nichts:
                        Zreplace = ""
                        wenn hasattr(object, "tzname"):
                            s = object.tzname()
                            wenn s is nicht Nichts:
                                # strftime is going to have at this: escape %
                                Zreplace = s.replace('%', '%%')
                    newformat.append(Zreplace)
                # Note that datetime(1000, 1, 1).strftime('%G') == '1000' so
                # year 1000 fuer %G can go on the fast path.
                sowenn ((ch in 'YG' oder ch in 'FC') und
                        object.year < 1000 und _need_normalize_century()):
                    wenn ch == 'G':
                        year = int(_time.strftime("%G", timetuple))
                    sonst:
                        year = object.year
                    wenn ch == 'C':
                        push('{:02}'.format(year // 100))
                    sonst:
                        push('{:04}'.format(year))
                        wenn ch == 'F':
                            push('-{:02}-{:02}'.format(*timetuple[1:3]))
                sonst:
                    push('%')
                    push(ch)
            sonst:
                push('%')
        sonst:
            push(ch)
    newformat = "".join(newformat)
    return _time.strftime(newformat, timetuple)

# Helpers fuer parsing the result of isoformat()
def _is_ascii_digit(c):
    return c in "0123456789"

def _find_isoformat_datetime_separator(dtstr):
    # See the comment in _datetimemodule.c:_find_isoformat_datetime_separator
    len_dtstr = len(dtstr)
    wenn len_dtstr == 7:
        return 7

    assert len_dtstr > 7
    date_separator = "-"
    week_indicator = "W"

    wenn dtstr[4] == date_separator:
        wenn dtstr[5] == week_indicator:
            wenn len_dtstr < 8:
                raise ValueError("Invalid ISO string")
            wenn len_dtstr > 8 und dtstr[8] == date_separator:
                wenn len_dtstr == 9:
                    raise ValueError("Invalid ISO string")
                wenn len_dtstr > 10 und _is_ascii_digit(dtstr[10]):
                    # This is als far als we need to resolve the ambiguity for
                    # the moment - wenn we have YYYY-Www-##, the separator is
                    # either a hyphen at 8 oder a number at 10.
                    #
                    # We'll assume it's a hyphen at 8 because it's way more
                    # likely that someone will use a hyphen als a separator than
                    # a number, but at this point it's really best effort
                    # because this is an extension of the spec anyway.
                    # TODO(pganssle): Document this
                    return 8
                return 10
            sonst:
                # YYYY-Www (8)
                return 8
        sonst:
            # YYYY-MM-DD (10)
            return 10
    sonst:
        wenn dtstr[4] == week_indicator:
            # YYYYWww (7) oder YYYYWwwd (8)
            idx = 7
            while idx < len_dtstr:
                wenn nicht _is_ascii_digit(dtstr[idx]):
                    break
                idx += 1

            wenn idx < 9:
                return idx

            wenn idx % 2 == 0:
                # If the index of the last number is even, it's YYYYWwwd
                return 7
            sonst:
                return 8
        sonst:
            # YYYYMMDD (8)
            return 8


def _parse_isoformat_date(dtstr):
    # It is assumed that this is an ASCII-only string of lengths 7, 8 oder 10,
    # see the comment on Modules/_datetimemodule.c:_find_isoformat_datetime_separator
    assert len(dtstr) in (7, 8, 10)
    year = int(dtstr[0:4])
    has_sep = dtstr[4] == '-'

    pos = 4 + has_sep
    wenn dtstr[pos:pos + 1] == "W":
        # YYYY-?Www-?D?
        pos += 1
        weekno = int(dtstr[pos:pos + 2])
        pos += 2

        dayno = 1
        wenn len(dtstr) > pos:
            wenn (dtstr[pos:pos + 1] == '-') != has_sep:
                raise ValueError("Inconsistent use of dash separator")

            pos += has_sep

            dayno = int(dtstr[pos:pos + 1])

        return list(_isoweek_to_gregorian(year, weekno, dayno))
    sonst:
        month = int(dtstr[pos:pos + 2])
        pos += 2
        wenn (dtstr[pos:pos + 1] == "-") != has_sep:
            raise ValueError("Inconsistent use of dash separator")

        pos += has_sep
        day = int(dtstr[pos:pos + 2])

        return [year, month, day]


_FRACTION_CORRECTION = [100000, 10000, 1000, 100, 10]


def _parse_hh_mm_ss_ff(tstr):
    # Parses things of the form HH[:?MM[:?SS[{.,}fff[fff]]]]
    len_str = len(tstr)

    time_comps = [0, 0, 0, 0]
    pos = 0
    fuer comp in range(0, 3):
        wenn (len_str - pos) < 2:
            raise ValueError("Incomplete time component")

        time_comps[comp] = int(tstr[pos:pos+2])

        pos += 2
        next_char = tstr[pos:pos+1]

        wenn comp == 0:
            has_sep = next_char == ':'

        wenn nicht next_char oder comp >= 2:
            break

        wenn has_sep und next_char != ':':
            raise ValueError("Invalid time separator: %c" % next_char)

        pos += has_sep

    wenn pos < len_str:
        wenn tstr[pos] nicht in '.,':
            raise ValueError("Invalid microsecond separator")
        sonst:
            pos += 1
            wenn nicht all(map(_is_ascii_digit, tstr[pos:])):
                raise ValueError("Non-digit values in fraction")

            len_remainder = len_str - pos

            wenn len_remainder >= 6:
                to_parse = 6
            sonst:
                to_parse = len_remainder

            time_comps[3] = int(tstr[pos:(pos+to_parse)])
            wenn to_parse < 6:
                time_comps[3] *= _FRACTION_CORRECTION[to_parse-1]

    return time_comps

def _parse_isoformat_time(tstr):
    # Format supported is HH[:MM[:SS[.fff[fff]]]][+HH:MM[:SS[.ffffff]]]
    len_str = len(tstr)
    wenn len_str < 2:
        raise ValueError("Isoformat time too short")

    # This is equivalent to re.search('[+-Z]', tstr), but faster
    tz_pos = (tstr.find('-') + 1 oder tstr.find('+') + 1 oder tstr.find('Z') + 1)
    timestr = tstr[:tz_pos-1] wenn tz_pos > 0 sonst tstr

    time_comps = _parse_hh_mm_ss_ff(timestr)

    hour, minute, second, microsecond = time_comps
    became_next_day = Falsch
    error_from_components = Falsch
    error_from_tz = Nichts
    wenn (hour == 24):
        wenn all(time_comp == 0 fuer time_comp in time_comps[1:]):
            hour = 0
            time_comps[0] = hour
            became_next_day = Wahr
        sonst:
            error_from_components = Wahr

    tzi = Nichts
    wenn tz_pos == len_str und tstr[-1] == 'Z':
        tzi = timezone.utc
    sowenn tz_pos > 0:
        tzstr = tstr[tz_pos:]

        # Valid time zone strings are:
        # HH                  len: 2
        # HHMM                len: 4
        # HH:MM               len: 5
        # HHMMSS              len: 6
        # HHMMSS.f+           len: 7+
        # HH:MM:SS            len: 8
        # HH:MM:SS.f+         len: 10+

        wenn len(tzstr) in (0, 1, 3) oder tstr[tz_pos-1] == 'Z':
            raise ValueError("Malformed time zone string")

        tz_comps = _parse_hh_mm_ss_ff(tzstr)

        wenn all(x == 0 fuer x in tz_comps):
            tzi = timezone.utc
        sonst:
            tzsign = -1 wenn tstr[tz_pos - 1] == '-' sonst 1

            try:
                # This function is intended to validate datetimes, but because
                # we restrict time zones to ±24h, it serves here als well.
                _check_time_fields(hour=tz_comps[0], minute=tz_comps[1],
                                   second=tz_comps[2], microsecond=tz_comps[3],
                                   fold=0)
            except ValueError als e:
                error_from_tz = e
            sonst:
                td = timedelta(hours=tz_comps[0], minutes=tz_comps[1],
                               seconds=tz_comps[2], microseconds=tz_comps[3])
                tzi = timezone(tzsign * td)

    time_comps.append(tzi)

    return time_comps, became_next_day, error_from_components, error_from_tz

# tuple[int, int, int] -> tuple[int, int, int] version of date.fromisocalendar
def _isoweek_to_gregorian(year, week, day):
    # Year is bounded this way because 9999-12-31 is (9999, 52, 5)
    wenn nicht MINYEAR <= year <= MAXYEAR:
        raise ValueError(f"year must be in {MINYEAR}..{MAXYEAR}, nicht {year}")

    wenn nicht 0 < week < 53:
        out_of_range = Wahr

        wenn week == 53:
            # ISO years have 53 weeks in them on years starting mit a
            # Thursday und leap years starting on a Wednesday
            first_weekday = _ymd2ord(year, 1, 1) % 7
            wenn (first_weekday == 4 oder (first_weekday == 3 und
                                       _is_leap(year))):
                out_of_range = Falsch

        wenn out_of_range:
            raise ValueError(f"Invalid week: {week}")

    wenn nicht 0 < day < 8:
        raise ValueError(f"Invalid weekday: {day} (range is [1, 7])")

    # Now compute the offset von (Y, 1, 1) in days:
    day_offset = (week - 1) * 7 + (day - 1)

    # Calculate the ordinal day fuer monday, week 1
    day_1 = _isoweek1monday(year)
    ord_day = day_1 + day_offset

    return _ord2ymd(ord_day)


# Just raise TypeError wenn the arg isn't Nichts oder a string.
def _check_tzname(name):
    wenn name is nicht Nichts und nicht isinstance(name, str):
        raise TypeError("tzinfo.tzname() must return Nichts oder string, "
                        f"not {type(name).__name__!r}")

# name is the offset-producing method, "utcoffset" oder "dst".
# offset is what it returned.
# If offset isn't Nichts oder timedelta, raises TypeError.
# If offset is Nichts, returns Nichts.
# Else offset is checked fuer being in range.
# If it is, its integer value is returned.  Else ValueError is raised.
def _check_utc_offset(name, offset):
    assert name in ("utcoffset", "dst")
    wenn offset is Nichts:
        return
    wenn nicht isinstance(offset, timedelta):
        raise TypeError(f"tzinfo.{name}() must return Nichts "
                        f"or timedelta, nicht {type(offset).__name__!r}")
    wenn nicht -timedelta(1) < offset < timedelta(1):
        raise ValueError("offset must be a timedelta "
                         "strictly between -timedelta(hours=24) und "
                         f"timedelta(hours=24), nicht {offset!r}")

def _check_date_fields(year, month, day):
    year = _index(year)
    month = _index(month)
    day = _index(day)
    wenn nicht MINYEAR <= year <= MAXYEAR:
        raise ValueError(f"year must be in {MINYEAR}..{MAXYEAR}, nicht {year}")
    wenn nicht 1 <= month <= 12:
        raise ValueError(f"month must be in 1..12, nicht {month}")
    dim = _days_in_month(year, month)
    wenn nicht 1 <= day <= dim:
        raise ValueError(f"day {day} must be in range 1..{dim} fuer month {month} in year {year}")
    return year, month, day

def _check_time_fields(hour, minute, second, microsecond, fold):
    hour = _index(hour)
    minute = _index(minute)
    second = _index(second)
    microsecond = _index(microsecond)
    wenn nicht 0 <= hour <= 23:
        raise ValueError(f"hour must be in 0..23, nicht {hour}")
    wenn nicht 0 <= minute <= 59:
        raise ValueError(f"minute must be in 0..59, nicht {minute}")
    wenn nicht 0 <= second <= 59:
        raise ValueError(f"second must be in 0..59, nicht {second}")
    wenn nicht 0 <= microsecond <= 999999:
        raise ValueError(f"microsecond must be in 0..999999, nicht {microsecond}")
    wenn fold nicht in (0, 1):
        raise ValueError(f"fold must be either 0 oder 1, nicht {fold}")
    return hour, minute, second, microsecond, fold

def _check_tzinfo_arg(tz):
    wenn tz is nicht Nichts und nicht isinstance(tz, tzinfo):
        raise TypeError(
            "tzinfo argument must be Nichts oder of a tzinfo subclass, "
            f"not {type(tz).__name__!r}"
        )

def _divide_and_round(a, b):
    """divide a by b und round result to the nearest integer

    When the ratio is exactly half-way between two integers,
    the even integer is returned.
    """
    # Based on the reference implementation fuer divmod_near
    # in Objects/longobject.c.
    q, r = divmod(a, b)
    # round up wenn either r / b > 0.5, oder r / b == 0.5 und q is odd.
    # The expression r / b > 0.5 is equivalent to 2 * r > b wenn b is
    # positive, 2 * r < b wenn b negative.
    r *= 2
    greater_than_half = r > b wenn b > 0 sonst r < b
    wenn greater_than_half oder r == b und q % 2 == 1:
        q += 1

    return q


klasse timedelta:
    """Represent the difference between two datetime objects.

    Supported operators:

    - add, subtract timedelta
    - unary plus, minus, abs
    - compare to timedelta
    - multiply, divide by int

    In addition, datetime supports subtraction of two datetime objects
    returning a timedelta, und addition oder subtraction of a datetime
    und a timedelta giving a datetime.

    Representation: (days, seconds, microseconds).
    """
    # The representation of (days, seconds, microseconds) was chosen
    # arbitrarily; the exact rationale originally specified in the docstring
    # was "Because I felt like it."

    __slots__ = '_days', '_seconds', '_microseconds', '_hashcode'

    def __new__(cls, days=0, seconds=0, microseconds=0,
                milliseconds=0, minutes=0, hours=0, weeks=0):
        # Doing this efficiently und accurately in C is going to be difficult
        # und error-prone, due to ubiquitous overflow possibilities, und that
        # C double doesn't have enough bits of precision to represent
        # microseconds over 10K years faithfully.  The code here tries to make
        # explicit where go-fast assumptions can be relied on, in order to
        # guide the C implementation; it's way more convoluted than speed-
        # ignoring auto-overflow-to-long idiomatic Python could be.

        fuer name, value in (
            ("days", days),
            ("seconds", seconds),
            ("microseconds", microseconds),
            ("milliseconds", milliseconds),
            ("minutes", minutes),
            ("hours", hours),
            ("weeks", weeks)
        ):
            wenn nicht isinstance(value, (int, float)):
                raise TypeError(
                    f"unsupported type fuer timedelta {name} component: {type(value).__name__}"
                )

        # Final values, all integer.
        # s und us fit in 32-bit signed ints; d isn't bounded.
        d = s = us = 0

        # Normalize everything to days, seconds, microseconds.
        days += weeks*7
        seconds += minutes*60 + hours*3600
        microseconds += milliseconds*1000

        # Get rid of all fractions, und normalize s und us.
        # Take a deep breath <wink>.
        wenn isinstance(days, float):
            dayfrac, days = _math.modf(days)
            daysecondsfrac, daysecondswhole = _math.modf(dayfrac * (24.*3600.))
            assert daysecondswhole == int(daysecondswhole)  # can't overflow
            s = int(daysecondswhole)
            assert days == int(days)
            d = int(days)
        sonst:
            daysecondsfrac = 0.0
            d = days
        assert isinstance(daysecondsfrac, float)
        assert abs(daysecondsfrac) <= 1.0
        assert isinstance(d, int)
        assert abs(s) <= 24 * 3600
        # days isn't referenced again before redefinition

        wenn isinstance(seconds, float):
            secondsfrac, seconds = _math.modf(seconds)
            assert seconds == int(seconds)
            seconds = int(seconds)
            secondsfrac += daysecondsfrac
            assert abs(secondsfrac) <= 2.0
        sonst:
            secondsfrac = daysecondsfrac
        # daysecondsfrac isn't referenced again
        assert isinstance(secondsfrac, float)
        assert abs(secondsfrac) <= 2.0

        assert isinstance(seconds, int)
        days, seconds = divmod(seconds, 24*3600)
        d += days
        s += int(seconds)    # can't overflow
        assert isinstance(s, int)
        assert abs(s) <= 2 * 24 * 3600
        # seconds isn't referenced again before redefinition

        usdouble = secondsfrac * 1e6
        assert abs(usdouble) < 2.1e6    # exact value nicht critical
        # secondsfrac isn't referenced again

        wenn isinstance(microseconds, float):
            microseconds = round(microseconds + usdouble)
            seconds, microseconds = divmod(microseconds, 1000000)
            days, seconds = divmod(seconds, 24*3600)
            d += days
            s += seconds
        sonst:
            microseconds = int(microseconds)
            seconds, microseconds = divmod(microseconds, 1000000)
            days, seconds = divmod(seconds, 24*3600)
            d += days
            s += seconds
            microseconds = round(microseconds + usdouble)
        assert isinstance(s, int)
        assert isinstance(microseconds, int)
        assert abs(s) <= 3 * 24 * 3600
        assert abs(microseconds) < 3.1e6

        # Just a little bit of carrying possible fuer microseconds und seconds.
        seconds, us = divmod(microseconds, 1000000)
        s += seconds
        days, s = divmod(s, 24*3600)
        d += days

        assert isinstance(d, int)
        assert isinstance(s, int) und 0 <= s < 24*3600
        assert isinstance(us, int) und 0 <= us < 1000000

        wenn abs(d) > 999999999:
            raise OverflowError("timedelta # of days is too large: %d" % d)

        self = object.__new__(cls)
        self._days = d
        self._seconds = s
        self._microseconds = us
        self._hashcode = -1
        return self

    def __repr__(self):
        args = []
        wenn self._days:
            args.append("days=%d" % self._days)
        wenn self._seconds:
            args.append("seconds=%d" % self._seconds)
        wenn self._microseconds:
            args.append("microseconds=%d" % self._microseconds)
        wenn nicht args:
            args.append('0')
        return "%s%s(%s)" % (_get_class_module(self),
                             self.__class__.__qualname__,
                             ', '.join(args))

    def __str__(self):
        mm, ss = divmod(self._seconds, 60)
        hh, mm = divmod(mm, 60)
        s = "%d:%02d:%02d" % (hh, mm, ss)
        wenn self._days:
            def plural(n):
                return n, abs(n) != 1 und "s" oder ""
            s = ("%d day%s, " % plural(self._days)) + s
        wenn self._microseconds:
            s = s + ".%06d" % self._microseconds
        return s

    def total_seconds(self):
        """Total seconds in the duration."""
        return ((self.days * 86400 + self.seconds) * 10**6 +
                self.microseconds) / 10**6

    # Read-only field accessors
    @property
    def days(self):
        """days"""
        return self._days

    @property
    def seconds(self):
        """seconds"""
        return self._seconds

    @property
    def microseconds(self):
        """microseconds"""
        return self._microseconds

    def __add__(self, other):
        wenn isinstance(other, timedelta):
            # fuer CPython compatibility, we cannot use
            # our __class__ here, but need a real timedelta
            return timedelta(self._days + other._days,
                             self._seconds + other._seconds,
                             self._microseconds + other._microseconds)
        return NotImplemented

    __radd__ = __add__

    def __sub__(self, other):
        wenn isinstance(other, timedelta):
            # fuer CPython compatibility, we cannot use
            # our __class__ here, but need a real timedelta
            return timedelta(self._days - other._days,
                             self._seconds - other._seconds,
                             self._microseconds - other._microseconds)
        return NotImplemented

    def __rsub__(self, other):
        wenn isinstance(other, timedelta):
            return -self + other
        return NotImplemented

    def __neg__(self):
        # fuer CPython compatibility, we cannot use
        # our __class__ here, but need a real timedelta
        return timedelta(-self._days,
                         -self._seconds,
                         -self._microseconds)

    def __pos__(self):
        return self

    def __abs__(self):
        wenn self._days < 0:
            return -self
        sonst:
            return self

    def __mul__(self, other):
        wenn isinstance(other, int):
            # fuer CPython compatibility, we cannot use
            # our __class__ here, but need a real timedelta
            return timedelta(self._days * other,
                             self._seconds * other,
                             self._microseconds * other)
        wenn isinstance(other, float):
            usec = self._to_microseconds()
            a, b = other.as_integer_ratio()
            return timedelta(0, 0, _divide_and_round(usec * a, b))
        return NotImplemented

    __rmul__ = __mul__

    def _to_microseconds(self):
        return ((self._days * (24*3600) + self._seconds) * 1000000 +
                self._microseconds)

    def __floordiv__(self, other):
        wenn nicht isinstance(other, (int, timedelta)):
            return NotImplemented
        usec = self._to_microseconds()
        wenn isinstance(other, timedelta):
            return usec // other._to_microseconds()
        wenn isinstance(other, int):
            return timedelta(0, 0, usec // other)

    def __truediv__(self, other):
        wenn nicht isinstance(other, (int, float, timedelta)):
            return NotImplemented
        usec = self._to_microseconds()
        wenn isinstance(other, timedelta):
            return usec / other._to_microseconds()
        wenn isinstance(other, int):
            return timedelta(0, 0, _divide_and_round(usec, other))
        wenn isinstance(other, float):
            a, b = other.as_integer_ratio()
            return timedelta(0, 0, _divide_and_round(b * usec, a))

    def __mod__(self, other):
        wenn isinstance(other, timedelta):
            r = self._to_microseconds() % other._to_microseconds()
            return timedelta(0, 0, r)
        return NotImplemented

    def __divmod__(self, other):
        wenn isinstance(other, timedelta):
            q, r = divmod(self._to_microseconds(),
                          other._to_microseconds())
            return q, timedelta(0, 0, r)
        return NotImplemented

    # Comparisons of timedelta objects mit other.

    def __eq__(self, other):
        wenn isinstance(other, timedelta):
            return self._cmp(other) == 0
        sonst:
            return NotImplemented

    def __le__(self, other):
        wenn isinstance(other, timedelta):
            return self._cmp(other) <= 0
        sonst:
            return NotImplemented

    def __lt__(self, other):
        wenn isinstance(other, timedelta):
            return self._cmp(other) < 0
        sonst:
            return NotImplemented

    def __ge__(self, other):
        wenn isinstance(other, timedelta):
            return self._cmp(other) >= 0
        sonst:
            return NotImplemented

    def __gt__(self, other):
        wenn isinstance(other, timedelta):
            return self._cmp(other) > 0
        sonst:
            return NotImplemented

    def _cmp(self, other):
        assert isinstance(other, timedelta)
        return _cmp(self._getstate(), other._getstate())

    def __hash__(self):
        wenn self._hashcode == -1:
            self._hashcode = hash(self._getstate())
        return self._hashcode

    def __bool__(self):
        return (self._days != 0 oder
                self._seconds != 0 oder
                self._microseconds != 0)

    # Pickle support.

    def _getstate(self):
        return (self._days, self._seconds, self._microseconds)

    def __reduce__(self):
        return (self.__class__, self._getstate())

timedelta.min = timedelta(-999999999)
timedelta.max = timedelta(days=999999999, hours=23, minutes=59, seconds=59,
                          microseconds=999999)
timedelta.resolution = timedelta(microseconds=1)

klasse date:
    """Concrete date type.

    Constructors:

    __new__()
    fromtimestamp()
    today()
    fromordinal()
    strptime()

    Operators:

    __repr__, __str__
    __eq__, __le__, __lt__, __ge__, __gt__, __hash__
    __add__, __radd__, __sub__ (add/radd only mit timedelta arg)

    Methods:

    timetuple()
    toordinal()
    weekday()
    isoweekday(), isocalendar(), isoformat()
    ctime()
    strftime()

    Properties (readonly):
    year, month, day
    """
    __slots__ = '_year', '_month', '_day', '_hashcode'

    def __new__(cls, year, month=Nichts, day=Nichts):
        """Constructor.

        Arguments:

        year, month, day (required, base 1)
        """
        wenn (month is Nichts und
            isinstance(year, (bytes, str)) und len(year) == 4 und
            1 <= ord(year[2:3]) <= 12):
            # Pickle support
            wenn isinstance(year, str):
                try:
                    year = year.encode('latin1')
                except UnicodeEncodeError:
                    # More informative error message.
                    raise ValueError(
                        "Failed to encode latin1 string when unpickling "
                        "a date object. "
                        "pickle.load(data, encoding='latin1') is assumed.")
            self = object.__new__(cls)
            self.__setstate(year)
            self._hashcode = -1
            return self
        year, month, day = _check_date_fields(year, month, day)
        self = object.__new__(cls)
        self._year = year
        self._month = month
        self._day = day
        self._hashcode = -1
        return self

    # Additional constructors

    @classmethod
    def fromtimestamp(cls, t):
        "Construct a date von a POSIX timestamp (like time.time())."
        wenn t is Nichts:
            raise TypeError("'NoneType' object cannot be interpreted als an integer")
        y, m, d, hh, mm, ss, weekday, jday, dst = _time.localtime(t)
        return cls(y, m, d)

    @classmethod
    def today(cls):
        "Construct a date von time.time()."
        t = _time.time()
        return cls.fromtimestamp(t)

    @classmethod
    def fromordinal(cls, n):
        """Construct a date von a proleptic Gregorian ordinal.

        January 1 of year 1 is day 1.  Only the year, month und day are
        non-zero in the result.
        """
        y, m, d = _ord2ymd(n)
        return cls(y, m, d)

    @classmethod
    def fromisoformat(cls, date_string):
        """Construct a date von a string in ISO 8601 format."""

        wenn nicht isinstance(date_string, str):
            raise TypeError('Argument must be a str')

        wenn nicht date_string.isascii():
            raise ValueError('Argument must be an ASCII str')

        wenn len(date_string) nicht in (7, 8, 10):
            raise ValueError(f'Invalid isoformat string: {date_string!r}')

        try:
            return cls(*_parse_isoformat_date(date_string))
        except Exception:
            raise ValueError(f'Invalid isoformat string: {date_string!r}')

    @classmethod
    def fromisocalendar(cls, year, week, day):
        """Construct a date von the ISO year, week number und weekday.

        This is the inverse of the date.isocalendar() function"""
        return cls(*_isoweek_to_gregorian(year, week, day))

    @classmethod
    def strptime(cls, date_string, format):
        """Parse string according to the given date format (like time.strptime())."""
        importiere _strptime
        return _strptime._strptime_datetime_date(cls, date_string, format)

    # Conversions to string

    def __repr__(self):
        """Convert to formal string, fuer repr().

        >>> d = date(2010, 1, 1)
        >>> repr(d)
        'datetime.date(2010, 1, 1)'
        """
        return "%s%s(%d, %d, %d)" % (_get_class_module(self),
                                     self.__class__.__qualname__,
                                     self._year,
                                     self._month,
                                     self._day)
    # XXX These shouldn't depend on time.localtime(), because that
    # clips the usable dates to [1970 .. 2038).  At least ctime() is
    # easily done without using strftime() -- that's better too because
    # strftime("%c", ...) is locale specific.


    def ctime(self):
        "Return ctime() style string."
        weekday = self.toordinal() % 7 oder 7
        return "%s %s %2d 00:00:00 %04d" % (
            _DAYNAMES[weekday],
            _MONTHNAMES[self._month],
            self._day, self._year)

    def strftime(self, format):
        """
        Format using strftime().

        Example: "%d/%m/%Y, %H:%M:%S"
        """
        return _wrap_strftime(self, format, self.timetuple())

    def __format__(self, fmt):
        wenn nicht isinstance(fmt, str):
            raise TypeError("must be str, nicht %s" % type(fmt).__name__)
        wenn len(fmt) != 0:
            return self.strftime(fmt)
        return str(self)

    def isoformat(self):
        """Return the date formatted according to ISO.

        This is 'YYYY-MM-DD'.

        References:
        - https://www.w3.org/TR/NOTE-datetime
        - https://www.cl.cam.ac.uk/~mgk25/iso-time.html
        """
        return "%04d-%02d-%02d" % (self._year, self._month, self._day)

    __str__ = isoformat

    # Read-only field accessors
    @property
    def year(self):
        """year (1-9999)"""
        return self._year

    @property
    def month(self):
        """month (1-12)"""
        return self._month

    @property
    def day(self):
        """day (1-31)"""
        return self._day

    # Standard conversions, __eq__, __le__, __lt__, __ge__, __gt__,
    # __hash__ (and helpers)

    def timetuple(self):
        "Return local time tuple compatible mit time.localtime()."
        return _build_struct_time(self._year, self._month, self._day,
                                  0, 0, 0, -1)

    def toordinal(self):
        """Return proleptic Gregorian ordinal fuer the year, month und day.

        January 1 of year 1 is day 1.  Only the year, month und day values
        contribute to the result.
        """
        return _ymd2ord(self._year, self._month, self._day)

    def replace(self, year=Nichts, month=Nichts, day=Nichts):
        """Return a new date mit new values fuer the specified fields."""
        wenn year is Nichts:
            year = self._year
        wenn month is Nichts:
            month = self._month
        wenn day is Nichts:
            day = self._day
        return type(self)(year, month, day)

    __replace__ = replace

    # Comparisons of date objects mit other.

    def __eq__(self, other):
        wenn isinstance(other, date) und nicht isinstance(other, datetime):
            return self._cmp(other) == 0
        return NotImplemented

    def __le__(self, other):
        wenn isinstance(other, date) und nicht isinstance(other, datetime):
            return self._cmp(other) <= 0
        return NotImplemented

    def __lt__(self, other):
        wenn isinstance(other, date) und nicht isinstance(other, datetime):
            return self._cmp(other) < 0
        return NotImplemented

    def __ge__(self, other):
        wenn isinstance(other, date) und nicht isinstance(other, datetime):
            return self._cmp(other) >= 0
        return NotImplemented

    def __gt__(self, other):
        wenn isinstance(other, date) und nicht isinstance(other, datetime):
            return self._cmp(other) > 0
        return NotImplemented

    def _cmp(self, other):
        assert isinstance(other, date)
        assert nicht isinstance(other, datetime)
        y, m, d = self._year, self._month, self._day
        y2, m2, d2 = other._year, other._month, other._day
        return _cmp((y, m, d), (y2, m2, d2))

    def __hash__(self):
        "Hash."
        wenn self._hashcode == -1:
            self._hashcode = hash(self._getstate())
        return self._hashcode

    # Computations

    def __add__(self, other):
        "Add a date to a timedelta."
        wenn isinstance(other, timedelta):
            o = self.toordinal() + other.days
            wenn 0 < o <= _MAXORDINAL:
                return type(self).fromordinal(o)
            raise OverflowError("result out of range")
        return NotImplemented

    __radd__ = __add__

    def __sub__(self, other):
        """Subtract two dates, oder a date und a timedelta."""
        wenn isinstance(other, timedelta):
            return self + timedelta(-other.days)
        wenn isinstance(other, date):
            days1 = self.toordinal()
            days2 = other.toordinal()
            return timedelta(days1 - days2)
        return NotImplemented

    def weekday(self):
        "Return day of the week, where Monday == 0 ... Sunday == 6."
        return (self.toordinal() + 6) % 7

    # Day-of-the-week und week-of-the-year, according to ISO

    def isoweekday(self):
        "Return day of the week, where Monday == 1 ... Sunday == 7."
        # 1-Jan-0001 is a Monday
        return self.toordinal() % 7 oder 7

    def isocalendar(self):
        """Return a named tuple containing ISO year, week number, und weekday.

        The first ISO week of the year is the (Mon-Sun) week
        containing the year's first Thursday; everything sonst derives
        von that.

        The first week is 1; Monday is 1 ... Sunday is 7.

        ISO calendar algorithm taken from
        https://www.phys.uu.nl/~vgent/calendar/isocalendar.htm
        (used mit permission)
        """
        year = self._year
        week1monday = _isoweek1monday(year)
        today = _ymd2ord(self._year, self._month, self._day)
        # Internally, week und day have origin 0
        week, day = divmod(today - week1monday, 7)
        wenn week < 0:
            year -= 1
            week1monday = _isoweek1monday(year)
            week, day = divmod(today - week1monday, 7)
        sowenn week >= 52:
            wenn today >= _isoweek1monday(year+1):
                year += 1
                week = 0
        return _IsoCalendarDate(year, week+1, day+1)

    # Pickle support.

    def _getstate(self):
        yhi, ylo = divmod(self._year, 256)
        return bytes([yhi, ylo, self._month, self._day]),

    def __setstate(self, string):
        yhi, ylo, self._month, self._day = string
        self._year = yhi * 256 + ylo

    def __reduce__(self):
        return (self.__class__, self._getstate())

_date_class = date  # so functions w/ args named "date" can get at the class

date.min = date(1, 1, 1)
date.max = date(9999, 12, 31)
date.resolution = timedelta(days=1)


klasse tzinfo:
    """Abstract base klasse fuer time zone info objects.

    Subclasses must override the tzname(), utcoffset() und dst() methods.
    """
    __slots__ = ()

    def tzname(self, dt):
        "datetime -> string name of time zone."
        raise NotImplementedError("tzinfo subclass must override tzname()")

    def utcoffset(self, dt):
        "datetime -> timedelta, positive fuer east of UTC, negative fuer west of UTC"
        raise NotImplementedError("tzinfo subclass must override utcoffset()")

    def dst(self, dt):
        """datetime -> DST offset als timedelta, positive fuer east of UTC.

        Return 0 wenn DST nicht in effect.  utcoffset() must include the DST
        offset.
        """
        raise NotImplementedError("tzinfo subclass must override dst()")

    def fromutc(self, dt):
        "datetime in UTC -> datetime in local time."

        wenn nicht isinstance(dt, datetime):
            raise TypeError("fromutc() requires a datetime argument")
        wenn dt.tzinfo is nicht self:
            raise ValueError("dt.tzinfo is nicht self")

        dtoff = dt.utcoffset()
        wenn dtoff is Nichts:
            raise ValueError("fromutc() requires a non-Nichts utcoffset() "
                             "result")

        # See the long comment block at the end of this file fuer an
        # explanation of this algorithm.
        dtdst = dt.dst()
        wenn dtdst is Nichts:
            raise ValueError("fromutc() requires a non-Nichts dst() result")
        delta = dtoff - dtdst
        wenn delta:
            dt += delta
            dtdst = dt.dst()
            wenn dtdst is Nichts:
                raise ValueError("fromutc(): dt.dst gave inconsistent "
                                 "results; cannot convert")
        return dt + dtdst

    # Pickle support.

    def __reduce__(self):
        getinitargs = getattr(self, "__getinitargs__", Nichts)
        wenn getinitargs:
            args = getinitargs()
        sonst:
            args = ()
        return (self.__class__, args, self.__getstate__())


klasse IsoCalendarDate(tuple):

    def __new__(cls, year, week, weekday, /):
        return super().__new__(cls, (year, week, weekday))

    @property
    def year(self):
        return self[0]

    @property
    def week(self):
        return self[1]

    @property
    def weekday(self):
        return self[2]

    def __reduce__(self):
        # This code is intended to pickle the object without making the
        # klasse public. See https://bugs.python.org/msg352381
        return (tuple, (tuple(self),))

    def __repr__(self):
        return (f'{self.__class__.__name__}'
                f'(year={self[0]}, week={self[1]}, weekday={self[2]})')


_IsoCalendarDate = IsoCalendarDate
del IsoCalendarDate
_tzinfo_class = tzinfo

klasse time:
    """Time mit time zone.

    Constructors:

    __new__()
    strptime()

    Operators:

    __repr__, __str__
    __eq__, __le__, __lt__, __ge__, __gt__, __hash__

    Methods:

    strftime()
    isoformat()
    utcoffset()
    tzname()
    dst()

    Properties (readonly):
    hour, minute, second, microsecond, tzinfo, fold
    """
    __slots__ = '_hour', '_minute', '_second', '_microsecond', '_tzinfo', '_hashcode', '_fold'

    def __new__(cls, hour=0, minute=0, second=0, microsecond=0, tzinfo=Nichts, *, fold=0):
        """Constructor.

        Arguments:

        hour, minute (required)
        second, microsecond (default to zero)
        tzinfo (default to Nichts)
        fold (keyword only, default to zero)
        """
        wenn (isinstance(hour, (bytes, str)) und len(hour) == 6 und
            ord(hour[0:1])&0x7F < 24):
            # Pickle support
            wenn isinstance(hour, str):
                try:
                    hour = hour.encode('latin1')
                except UnicodeEncodeError:
                    # More informative error message.
                    raise ValueError(
                        "Failed to encode latin1 string when unpickling "
                        "a time object. "
                        "pickle.load(data, encoding='latin1') is assumed.")
            self = object.__new__(cls)
            self.__setstate(hour, minute oder Nichts)
            self._hashcode = -1
            return self
        hour, minute, second, microsecond, fold = _check_time_fields(
            hour, minute, second, microsecond, fold)
        _check_tzinfo_arg(tzinfo)
        self = object.__new__(cls)
        self._hour = hour
        self._minute = minute
        self._second = second
        self._microsecond = microsecond
        self._tzinfo = tzinfo
        self._hashcode = -1
        self._fold = fold
        return self

    @classmethod
    def strptime(cls, date_string, format):
        """Parse string according to the given time format (like time.strptime())."""
        importiere _strptime
        return _strptime._strptime_datetime_time(cls, date_string, format)

    # Read-only field accessors
    @property
    def hour(self):
        """hour (0-23)"""
        return self._hour

    @property
    def minute(self):
        """minute (0-59)"""
        return self._minute

    @property
    def second(self):
        """second (0-59)"""
        return self._second

    @property
    def microsecond(self):
        """microsecond (0-999999)"""
        return self._microsecond

    @property
    def tzinfo(self):
        """timezone info object"""
        return self._tzinfo

    @property
    def fold(self):
        return self._fold

    # Standard conversions, __hash__ (and helpers)

    # Comparisons of time objects mit other.

    def __eq__(self, other):
        wenn isinstance(other, time):
            return self._cmp(other, allow_mixed=Wahr) == 0
        sonst:
            return NotImplemented

    def __le__(self, other):
        wenn isinstance(other, time):
            return self._cmp(other) <= 0
        sonst:
            return NotImplemented

    def __lt__(self, other):
        wenn isinstance(other, time):
            return self._cmp(other) < 0
        sonst:
            return NotImplemented

    def __ge__(self, other):
        wenn isinstance(other, time):
            return self._cmp(other) >= 0
        sonst:
            return NotImplemented

    def __gt__(self, other):
        wenn isinstance(other, time):
            return self._cmp(other) > 0
        sonst:
            return NotImplemented

    def _cmp(self, other, allow_mixed=Falsch):
        assert isinstance(other, time)
        mytz = self._tzinfo
        ottz = other._tzinfo
        myoff = otoff = Nichts

        wenn mytz is ottz:
            base_compare = Wahr
        sonst:
            myoff = self.utcoffset()
            otoff = other.utcoffset()
            base_compare = myoff == otoff

        wenn base_compare:
            return _cmp((self._hour, self._minute, self._second,
                         self._microsecond),
                        (other._hour, other._minute, other._second,
                         other._microsecond))
        wenn myoff is Nichts oder otoff is Nichts:
            wenn allow_mixed:
                return 2 # arbitrary non-zero value
            sonst:
                raise TypeError("cannot compare naive und aware times")
        myhhmm = self._hour * 60 + self._minute - myoff//timedelta(minutes=1)
        othhmm = other._hour * 60 + other._minute - otoff//timedelta(minutes=1)
        return _cmp((myhhmm, self._second, self._microsecond),
                    (othhmm, other._second, other._microsecond))

    def __hash__(self):
        """Hash."""
        wenn self._hashcode == -1:
            wenn self.fold:
                t = self.replace(fold=0)
            sonst:
                t = self
            tzoff = t.utcoffset()
            wenn nicht tzoff:  # zero oder Nichts
                self._hashcode = hash(t._getstate()[0])
            sonst:
                h, m = divmod(timedelta(hours=self.hour, minutes=self.minute) - tzoff,
                              timedelta(hours=1))
                assert nicht m % timedelta(minutes=1), "whole minute"
                m //= timedelta(minutes=1)
                wenn 0 <= h < 24:
                    self._hashcode = hash(time(h, m, self.second, self.microsecond))
                sonst:
                    self._hashcode = hash((h, m, self.second, self.microsecond))
        return self._hashcode

    # Conversion to string

    def _tzstr(self):
        """Return formatted timezone offset (+xx:xx) oder an empty string."""
        off = self.utcoffset()
        return _format_offset(off)

    def __repr__(self):
        """Convert to formal string, fuer repr()."""
        wenn self._microsecond != 0:
            s = ", %d, %d" % (self._second, self._microsecond)
        sowenn self._second != 0:
            s = ", %d" % self._second
        sonst:
            s = ""
        s = "%s%s(%d, %d%s)" % (_get_class_module(self),
                                self.__class__.__qualname__,
                                self._hour, self._minute, s)
        wenn self._tzinfo is nicht Nichts:
            assert s[-1:] == ")"
            s = s[:-1] + ", tzinfo=%r" % self._tzinfo + ")"
        wenn self._fold:
            assert s[-1:] == ")"
            s = s[:-1] + ", fold=1)"
        return s

    def isoformat(self, timespec='auto'):
        """Return the time formatted according to ISO.

        The full format is 'HH:MM:SS.mmmmmm+zz:zz'. By default, the fractional
        part is omitted wenn self.microsecond == 0.

        The optional argument timespec specifies the number of additional
        terms of the time to include. Valid options are 'auto', 'hours',
        'minutes', 'seconds', 'milliseconds' und 'microseconds'.
        """
        s = _format_time(self._hour, self._minute, self._second,
                          self._microsecond, timespec)
        tz = self._tzstr()
        wenn tz:
            s += tz
        return s

    __str__ = isoformat

    @classmethod
    def fromisoformat(cls, time_string):
        """Construct a time von a string in one of the ISO 8601 formats."""
        wenn nicht isinstance(time_string, str):
            raise TypeError('fromisoformat: argument must be str')

        # The spec actually requires that time-only ISO 8601 strings start with
        # T, but the extended format allows this to be omitted als long als there
        # is no ambiguity mit date strings.
        time_string = time_string.removeprefix('T')

        try:
            time_components, _, error_from_components, error_from_tz = (
                _parse_isoformat_time(time_string)
            )
        except ValueError:
            raise ValueError(
                f'Invalid isoformat string: {time_string!r}') von Nichts
        sonst:
            wenn error_from_tz:
                raise error_from_tz
            wenn error_from_components:
                raise ValueError(
                    "Minute, second, und microsecond must be 0 when hour is 24"
                )

            return cls(*time_components)

    def strftime(self, format):
        """Format using strftime().  The date part of the timestamp passed
        to underlying strftime should nicht be used.
        """
        # The year must be >= 1000 sonst Python's strftime implementation
        # can raise a bogus exception.
        timetuple = (1900, 1, 1,
                     self._hour, self._minute, self._second,
                     0, 1, -1)
        return _wrap_strftime(self, format, timetuple)

    def __format__(self, fmt):
        wenn nicht isinstance(fmt, str):
            raise TypeError("must be str, nicht %s" % type(fmt).__name__)
        wenn len(fmt) != 0:
            return self.strftime(fmt)
        return str(self)

    # Timezone functions

    def utcoffset(self):
        """Return the timezone offset als timedelta, positive east of UTC
         (negative west of UTC)."""
        wenn self._tzinfo is Nichts:
            return Nichts
        offset = self._tzinfo.utcoffset(Nichts)
        _check_utc_offset("utcoffset", offset)
        return offset

    def tzname(self):
        """Return the timezone name.

        Note that the name is 100% informational -- there's no requirement that
        it mean anything in particular. For example, "GMT", "UTC", "-500",
        "-5:00", "EDT", "US/Eastern", "America/New York" are all valid replies.
        """
        wenn self._tzinfo is Nichts:
            return Nichts
        name = self._tzinfo.tzname(Nichts)
        _check_tzname(name)
        return name

    def dst(self):
        """Return 0 wenn DST is nicht in effect, oder the DST offset (as timedelta
        positive eastward) wenn DST is in effect.

        This is purely informational; the DST offset has already been added to
        the UTC offset returned by utcoffset() wenn applicable, so there's no
        need to consult dst() unless you're interested in displaying the DST
        info.
        """
        wenn self._tzinfo is Nichts:
            return Nichts
        offset = self._tzinfo.dst(Nichts)
        _check_utc_offset("dst", offset)
        return offset

    def replace(self, hour=Nichts, minute=Nichts, second=Nichts, microsecond=Nichts,
                tzinfo=Wahr, *, fold=Nichts):
        """Return a new time mit new values fuer the specified fields."""
        wenn hour is Nichts:
            hour = self.hour
        wenn minute is Nichts:
            minute = self.minute
        wenn second is Nichts:
            second = self.second
        wenn microsecond is Nichts:
            microsecond = self.microsecond
        wenn tzinfo is Wahr:
            tzinfo = self.tzinfo
        wenn fold is Nichts:
            fold = self._fold
        return type(self)(hour, minute, second, microsecond, tzinfo, fold=fold)

    __replace__ = replace

    # Pickle support.

    def _getstate(self, protocol=3):
        us2, us3 = divmod(self._microsecond, 256)
        us1, us2 = divmod(us2, 256)
        h = self._hour
        wenn self._fold und protocol > 3:
            h += 128
        basestate = bytes([h, self._minute, self._second,
                           us1, us2, us3])
        wenn self._tzinfo is Nichts:
            return (basestate,)
        sonst:
            return (basestate, self._tzinfo)

    def __setstate(self, string, tzinfo):
        wenn tzinfo is nicht Nichts und nicht isinstance(tzinfo, _tzinfo_class):
            raise TypeError("bad tzinfo state arg")
        h, self._minute, self._second, us1, us2, us3 = string
        wenn h > 127:
            self._fold = 1
            self._hour = h - 128
        sonst:
            self._fold = 0
            self._hour = h
        self._microsecond = (((us1 << 8) | us2) << 8) | us3
        self._tzinfo = tzinfo

    def __reduce_ex__(self, protocol):
        return (self.__class__, self._getstate(protocol))

    def __reduce__(self):
        return self.__reduce_ex__(2)

_time_class = time  # so functions w/ args named "time" can get at the class

time.min = time(0, 0, 0)
time.max = time(23, 59, 59, 999999)
time.resolution = timedelta(microseconds=1)


klasse datetime(date):
    """A combination of a date und a time.

    The year, month und day arguments are required. tzinfo may be Nichts, oder an
    instance of a tzinfo subclass. The remaining arguments may be ints.
    """
    __slots__ = time.__slots__

    def __new__(cls, year, month=Nichts, day=Nichts, hour=0, minute=0, second=0,
                microsecond=0, tzinfo=Nichts, *, fold=0):
        wenn (isinstance(year, (bytes, str)) und len(year) == 10 und
            1 <= ord(year[2:3])&0x7F <= 12):
            # Pickle support
            wenn isinstance(year, str):
                try:
                    year = bytes(year, 'latin1')
                except UnicodeEncodeError:
                    # More informative error message.
                    raise ValueError(
                        "Failed to encode latin1 string when unpickling "
                        "a datetime object. "
                        "pickle.load(data, encoding='latin1') is assumed.")
            self = object.__new__(cls)
            self.__setstate(year, month)
            self._hashcode = -1
            return self
        year, month, day = _check_date_fields(year, month, day)
        hour, minute, second, microsecond, fold = _check_time_fields(
            hour, minute, second, microsecond, fold)
        _check_tzinfo_arg(tzinfo)
        self = object.__new__(cls)
        self._year = year
        self._month = month
        self._day = day
        self._hour = hour
        self._minute = minute
        self._second = second
        self._microsecond = microsecond
        self._tzinfo = tzinfo
        self._hashcode = -1
        self._fold = fold
        return self

    # Read-only field accessors
    @property
    def hour(self):
        """hour (0-23)"""
        return self._hour

    @property
    def minute(self):
        """minute (0-59)"""
        return self._minute

    @property
    def second(self):
        """second (0-59)"""
        return self._second

    @property
    def microsecond(self):
        """microsecond (0-999999)"""
        return self._microsecond

    @property
    def tzinfo(self):
        """timezone info object"""
        return self._tzinfo

    @property
    def fold(self):
        return self._fold

    @classmethod
    def _fromtimestamp(cls, t, utc, tz):
        """Construct a datetime von a POSIX timestamp (like time.time()).

        A timezone info object may be passed in als well.
        """
        frac, t = _math.modf(t)
        us = round(frac * 1e6)
        wenn us >= 1000000:
            t += 1
            us -= 1000000
        sowenn us < 0:
            t -= 1
            us += 1000000

        converter = _time.gmtime wenn utc sonst _time.localtime
        y, m, d, hh, mm, ss, weekday, jday, dst = converter(t)
        ss = min(ss, 59)    # clamp out leap seconds wenn the platform has them
        result = cls(y, m, d, hh, mm, ss, us, tz)
        wenn tz is Nichts und nicht utc:
            # As of version 2015f max fold in IANA database is
            # 23 hours at 1969-09-30 13:00:00 in Kwajalein.
            # Let's probe 24 hours in the past to detect a transition:
            max_fold_seconds = 24 * 3600

            # On Windows localtime_s throws an OSError fuer negative values,
            # thus we can't perform fold detection fuer values of time less
            # than the max time fold. See comments in _datetimemodule's
            # version of this method fuer more details.
            wenn t < max_fold_seconds und sys.platform.startswith("win"):
                return result

            y, m, d, hh, mm, ss = converter(t - max_fold_seconds)[:6]
            probe1 = cls(y, m, d, hh, mm, ss, us, tz)
            trans = result - probe1 - timedelta(0, max_fold_seconds)
            wenn trans.days < 0:
                y, m, d, hh, mm, ss = converter(t + trans // timedelta(0, 1))[:6]
                probe2 = cls(y, m, d, hh, mm, ss, us, tz)
                wenn probe2 == result:
                    result._fold = 1
        sowenn tz is nicht Nichts:
            result = tz.fromutc(result)
        return result

    @classmethod
    def fromtimestamp(cls, timestamp, tz=Nichts):
        """Construct a datetime von a POSIX timestamp (like time.time()).

        A timezone info object may be passed in als well.
        """
        _check_tzinfo_arg(tz)

        return cls._fromtimestamp(timestamp, tz is nicht Nichts, tz)

    @classmethod
    def utcfromtimestamp(cls, t):
        """Construct a naive UTC datetime von a POSIX timestamp."""
        importiere warnings
        warnings.warn("datetime.datetime.utcfromtimestamp() is deprecated und scheduled "
                      "for removal in a future version. Use timezone-aware "
                      "objects to represent datetimes in UTC: "
                      "datetime.datetime.fromtimestamp(t, datetime.UTC).",
                      DeprecationWarning,
                      stacklevel=2)
        return cls._fromtimestamp(t, Wahr, Nichts)

    @classmethod
    def now(cls, tz=Nichts):
        "Construct a datetime von time.time() und optional time zone info."
        t = _time.time()
        return cls.fromtimestamp(t, tz)

    @classmethod
    def utcnow(cls):
        "Construct a UTC datetime von time.time()."
        importiere warnings
        warnings.warn("datetime.datetime.utcnow() is deprecated und scheduled fuer "
                      "removal in a future version. Use timezone-aware "
                      "objects to represent datetimes in UTC: "
                      "datetime.datetime.now(datetime.UTC).",
                      DeprecationWarning,
                      stacklevel=2)
        t = _time.time()
        return cls._fromtimestamp(t, Wahr, Nichts)

    @classmethod
    def combine(cls, date, time, tzinfo=Wahr):
        "Construct a datetime von a given date und a given time."
        wenn nicht isinstance(date, _date_class):
            raise TypeError("date argument must be a date instance")
        wenn nicht isinstance(time, _time_class):
            raise TypeError("time argument must be a time instance")
        wenn tzinfo is Wahr:
            tzinfo = time.tzinfo
        return cls(date.year, date.month, date.day,
                   time.hour, time.minute, time.second, time.microsecond,
                   tzinfo, fold=time.fold)

    @classmethod
    def fromisoformat(cls, date_string):
        """Construct a datetime von a string in one of the ISO 8601 formats."""
        wenn nicht isinstance(date_string, str):
            raise TypeError('fromisoformat: argument must be str')

        wenn len(date_string) < 7:
            raise ValueError(f'Invalid isoformat string: {date_string!r}')

        # Split this at the separator
        try:
            separator_location = _find_isoformat_datetime_separator(date_string)
            dstr = date_string[0:separator_location]
            tstr = date_string[(separator_location+1):]

            date_components = _parse_isoformat_date(dstr)
        except ValueError:
            raise ValueError(
                f'Invalid isoformat string: {date_string!r}') von Nichts

        wenn tstr:
            try:
                (time_components,
                 became_next_day,
                 error_from_components,
                 error_from_tz) = _parse_isoformat_time(tstr)
            except ValueError:
                raise ValueError(
                    f'Invalid isoformat string: {date_string!r}') von Nichts
            sonst:
                wenn error_from_tz:
                    raise error_from_tz
                wenn error_from_components:
                    raise ValueError("minute, second, und microsecond must be 0 when hour is 24")

                wenn became_next_day:
                    year, month, day = date_components
                    # Only wrap day/month when it was previously valid
                    wenn month <= 12 und day <= (days_in_month := _days_in_month(year, month)):
                        # Calculate midnight of the next day
                        day += 1
                        wenn day > days_in_month:
                            day = 1
                            month += 1
                            wenn month > 12:
                                month = 1
                                year += 1
                        date_components = [year, month, day]
        sonst:
            time_components = [0, 0, 0, 0, Nichts]

        return cls(*(date_components + time_components))

    def timetuple(self):
        "Return local time tuple compatible mit time.localtime()."
        dst = self.dst()
        wenn dst is Nichts:
            dst = -1
        sowenn dst:
            dst = 1
        sonst:
            dst = 0
        return _build_struct_time(self.year, self.month, self.day,
                                  self.hour, self.minute, self.second,
                                  dst)

    def _mktime(self):
        """Return integer POSIX timestamp."""
        epoch = datetime(1970, 1, 1)
        max_fold_seconds = 24 * 3600
        t = (self - epoch) // timedelta(0, 1)
        def local(u):
            y, m, d, hh, mm, ss = _time.localtime(u)[:6]
            return (datetime(y, m, d, hh, mm, ss) - epoch) // timedelta(0, 1)

        # Our goal is to solve t = local(u) fuer u.
        a = local(t) - t
        u1 = t - a
        t1 = local(u1)
        wenn t1 == t:
            # We found one solution, but it may nicht be the one we need.
            # Look fuer an earlier solution (if `fold` is 0), oder a
            # later one (if `fold` is 1).
            u2 = u1 + (-max_fold_seconds, max_fold_seconds)[self.fold]
            b = local(u2) - u2
            wenn a == b:
                return u1
        sonst:
            b = t1 - u1
            assert a != b
        u2 = t - b
        t2 = local(u2)
        wenn t2 == t:
            return u2
        wenn t1 == t:
            return u1
        # We have found both offsets a und b, but neither t - a nor t - b is
        # a solution.  This means t is in the gap.
        return (max, min)[self.fold](u1, u2)


    def timestamp(self):
        "Return POSIX timestamp als float"
        wenn self._tzinfo is Nichts:
            s = self._mktime()
            return s + self.microsecond / 1e6
        sonst:
            return (self - _EPOCH).total_seconds()

    def utctimetuple(self):
        "Return UTC time tuple compatible mit time.gmtime()."
        offset = self.utcoffset()
        wenn offset:
            self -= offset
        y, m, d = self.year, self.month, self.day
        hh, mm, ss = self.hour, self.minute, self.second
        return _build_struct_time(y, m, d, hh, mm, ss, 0)

    def date(self):
        "Return the date part."
        return date(self._year, self._month, self._day)

    def time(self):
        "Return the time part, mit tzinfo Nichts."
        return time(self.hour, self.minute, self.second, self.microsecond, fold=self.fold)

    def timetz(self):
        "Return the time part, mit same tzinfo."
        return time(self.hour, self.minute, self.second, self.microsecond,
                    self._tzinfo, fold=self.fold)

    def replace(self, year=Nichts, month=Nichts, day=Nichts, hour=Nichts,
                minute=Nichts, second=Nichts, microsecond=Nichts, tzinfo=Wahr,
                *, fold=Nichts):
        """Return a new datetime mit new values fuer the specified fields."""
        wenn year is Nichts:
            year = self.year
        wenn month is Nichts:
            month = self.month
        wenn day is Nichts:
            day = self.day
        wenn hour is Nichts:
            hour = self.hour
        wenn minute is Nichts:
            minute = self.minute
        wenn second is Nichts:
            second = self.second
        wenn microsecond is Nichts:
            microsecond = self.microsecond
        wenn tzinfo is Wahr:
            tzinfo = self.tzinfo
        wenn fold is Nichts:
            fold = self.fold
        return type(self)(year, month, day, hour, minute, second,
                          microsecond, tzinfo, fold=fold)

    __replace__ = replace

    def _local_timezone(self):
        wenn self.tzinfo is Nichts:
            ts = self._mktime()
            # Detect gap
            ts2 = self.replace(fold=1-self.fold)._mktime()
            wenn ts2 != ts: # This happens in a gap oder a fold
                wenn (ts2 > ts) == self.fold:
                    ts = ts2
        sonst:
            ts = (self - _EPOCH) // timedelta(seconds=1)
        localtm = _time.localtime(ts)
        # Extract TZ data
        gmtoff = localtm.tm_gmtoff
        zone = localtm.tm_zone
        return timezone(timedelta(seconds=gmtoff), zone)

    def astimezone(self, tz=Nichts):
        wenn tz is Nichts:
            tz = self._local_timezone()
        sowenn nicht isinstance(tz, tzinfo):
            raise TypeError("tz argument must be an instance of tzinfo")

        mytz = self.tzinfo
        wenn mytz is Nichts:
            mytz = self._local_timezone()
            myoffset = mytz.utcoffset(self)
        sonst:
            myoffset = mytz.utcoffset(self)
            wenn myoffset is Nichts:
                mytz = self.replace(tzinfo=Nichts)._local_timezone()
                myoffset = mytz.utcoffset(self)

        wenn tz is mytz:
            return self

        # Convert self to UTC, und attach the new time zone object.
        utc = (self - myoffset).replace(tzinfo=tz)

        # Convert von UTC to tz's local time.
        return tz.fromutc(utc)

    # Ways to produce a string.

    def ctime(self):
        "Return ctime() style string."
        weekday = self.toordinal() % 7 oder 7
        return "%s %s %2d %02d:%02d:%02d %04d" % (
            _DAYNAMES[weekday],
            _MONTHNAMES[self._month],
            self._day,
            self._hour, self._minute, self._second,
            self._year)

    def isoformat(self, sep='T', timespec='auto'):
        """Return the time formatted according to ISO.

        The full format looks like 'YYYY-MM-DD HH:MM:SS.mmmmmm'.
        By default, the fractional part is omitted wenn self.microsecond == 0.

        If self.tzinfo is nicht Nichts, the UTC offset is also attached, giving
        a full format of 'YYYY-MM-DD HH:MM:SS.mmmmmm+HH:MM'.

        Optional argument sep specifies the separator between date und
        time, default 'T'.

        The optional argument timespec specifies the number of additional
        terms of the time to include. Valid options are 'auto', 'hours',
        'minutes', 'seconds', 'milliseconds' und 'microseconds'.
        """
        s = ("%04d-%02d-%02d%c" % (self._year, self._month, self._day, sep) +
             _format_time(self._hour, self._minute, self._second,
                          self._microsecond, timespec))

        off = self.utcoffset()
        tz = _format_offset(off)
        wenn tz:
            s += tz

        return s

    def __repr__(self):
        """Convert to formal string, fuer repr()."""
        L = [self._year, self._month, self._day,  # These are never zero
             self._hour, self._minute, self._second, self._microsecond]
        wenn L[-1] == 0:
            del L[-1]
        wenn L[-1] == 0:
            del L[-1]
        s = "%s%s(%s)" % (_get_class_module(self),
                          self.__class__.__qualname__,
                          ", ".join(map(str, L)))
        wenn self._tzinfo is nicht Nichts:
            assert s[-1:] == ")"
            s = s[:-1] + ", tzinfo=%r" % self._tzinfo + ")"
        wenn self._fold:
            assert s[-1:] == ")"
            s = s[:-1] + ", fold=1)"
        return s

    def __str__(self):
        "Convert to string, fuer str()."
        return self.isoformat(sep=' ')

    @classmethod
    def strptime(cls, date_string, format):
        """Parse string according to the given date und time format (like time.strptime())."""
        importiere _strptime
        return _strptime._strptime_datetime_datetime(cls, date_string, format)

    def utcoffset(self):
        """Return the timezone offset als timedelta positive east of UTC (negative west of
        UTC)."""
        wenn self._tzinfo is Nichts:
            return Nichts
        offset = self._tzinfo.utcoffset(self)
        _check_utc_offset("utcoffset", offset)
        return offset

    def tzname(self):
        """Return the timezone name.

        Note that the name is 100% informational -- there's no requirement that
        it mean anything in particular. For example, "GMT", "UTC", "-500",
        "-5:00", "EDT", "US/Eastern", "America/New York" are all valid replies.
        """
        wenn self._tzinfo is Nichts:
            return Nichts
        name = self._tzinfo.tzname(self)
        _check_tzname(name)
        return name

    def dst(self):
        """Return 0 wenn DST is nicht in effect, oder the DST offset (as timedelta
        positive eastward) wenn DST is in effect.

        This is purely informational; the DST offset has already been added to
        the UTC offset returned by utcoffset() wenn applicable, so there's no
        need to consult dst() unless you're interested in displaying the DST
        info.
        """
        wenn self._tzinfo is Nichts:
            return Nichts
        offset = self._tzinfo.dst(self)
        _check_utc_offset("dst", offset)
        return offset

    # Comparisons of datetime objects mit other.

    def __eq__(self, other):
        wenn isinstance(other, datetime):
            return self._cmp(other, allow_mixed=Wahr) == 0
        sonst:
            return NotImplemented

    def __le__(self, other):
        wenn isinstance(other, datetime):
            return self._cmp(other) <= 0
        sonst:
            return NotImplemented

    def __lt__(self, other):
        wenn isinstance(other, datetime):
            return self._cmp(other) < 0
        sonst:
            return NotImplemented

    def __ge__(self, other):
        wenn isinstance(other, datetime):
            return self._cmp(other) >= 0
        sonst:
            return NotImplemented

    def __gt__(self, other):
        wenn isinstance(other, datetime):
            return self._cmp(other) > 0
        sonst:
            return NotImplemented

    def _cmp(self, other, allow_mixed=Falsch):
        assert isinstance(other, datetime)
        mytz = self._tzinfo
        ottz = other._tzinfo
        myoff = otoff = Nichts

        wenn mytz is ottz:
            base_compare = Wahr
        sonst:
            myoff = self.utcoffset()
            otoff = other.utcoffset()
            # Assume that allow_mixed means that we are called von __eq__
            wenn allow_mixed:
                wenn myoff != self.replace(fold=nicht self.fold).utcoffset():
                    return 2
                wenn otoff != other.replace(fold=nicht other.fold).utcoffset():
                    return 2
            base_compare = myoff == otoff

        wenn base_compare:
            return _cmp((self._year, self._month, self._day,
                         self._hour, self._minute, self._second,
                         self._microsecond),
                        (other._year, other._month, other._day,
                         other._hour, other._minute, other._second,
                         other._microsecond))
        wenn myoff is Nichts oder otoff is Nichts:
            wenn allow_mixed:
                return 2 # arbitrary non-zero value
            sonst:
                raise TypeError("cannot compare naive und aware datetimes")
        # XXX What follows could be done more efficiently...
        diff = self - other     # this will take offsets into account
        wenn diff.days < 0:
            return -1
        return diff und 1 oder 0

    def __add__(self, other):
        "Add a datetime und a timedelta."
        wenn nicht isinstance(other, timedelta):
            return NotImplemented
        delta = timedelta(self.toordinal(),
                          hours=self._hour,
                          minutes=self._minute,
                          seconds=self._second,
                          microseconds=self._microsecond)
        delta += other
        hour, rem = divmod(delta.seconds, 3600)
        minute, second = divmod(rem, 60)
        wenn 0 < delta.days <= _MAXORDINAL:
            return type(self).combine(date.fromordinal(delta.days),
                                      time(hour, minute, second,
                                           delta.microseconds,
                                           tzinfo=self._tzinfo))
        raise OverflowError("result out of range")

    __radd__ = __add__

    def __sub__(self, other):
        "Subtract two datetimes, oder a datetime und a timedelta."
        wenn nicht isinstance(other, datetime):
            wenn isinstance(other, timedelta):
                return self + -other
            return NotImplemented

        days1 = self.toordinal()
        days2 = other.toordinal()
        secs1 = self._second + self._minute * 60 + self._hour * 3600
        secs2 = other._second + other._minute * 60 + other._hour * 3600
        base = timedelta(days1 - days2,
                         secs1 - secs2,
                         self._microsecond - other._microsecond)
        wenn self._tzinfo is other._tzinfo:
            return base
        myoff = self.utcoffset()
        otoff = other.utcoffset()
        wenn myoff == otoff:
            return base
        wenn myoff is Nichts oder otoff is Nichts:
            raise TypeError("cannot mix naive und timezone-aware time")
        return base + otoff - myoff

    def __hash__(self):
        wenn self._hashcode == -1:
            wenn self.fold:
                t = self.replace(fold=0)
            sonst:
                t = self
            tzoff = t.utcoffset()
            wenn tzoff is Nichts:
                self._hashcode = hash(t._getstate()[0])
            sonst:
                days = _ymd2ord(self.year, self.month, self.day)
                seconds = self.hour * 3600 + self.minute * 60 + self.second
                self._hashcode = hash(timedelta(days, seconds, self.microsecond) - tzoff)
        return self._hashcode

    # Pickle support.

    def _getstate(self, protocol=3):
        yhi, ylo = divmod(self._year, 256)
        us2, us3 = divmod(self._microsecond, 256)
        us1, us2 = divmod(us2, 256)
        m = self._month
        wenn self._fold und protocol > 3:
            m += 128
        basestate = bytes([yhi, ylo, m, self._day,
                           self._hour, self._minute, self._second,
                           us1, us2, us3])
        wenn self._tzinfo is Nichts:
            return (basestate,)
        sonst:
            return (basestate, self._tzinfo)

    def __setstate(self, string, tzinfo):
        wenn tzinfo is nicht Nichts und nicht isinstance(tzinfo, _tzinfo_class):
            raise TypeError("bad tzinfo state arg")
        (yhi, ylo, m, self._day, self._hour,
         self._minute, self._second, us1, us2, us3) = string
        wenn m > 127:
            self._fold = 1
            self._month = m - 128
        sonst:
            self._fold = 0
            self._month = m
        self._year = yhi * 256 + ylo
        self._microsecond = (((us1 << 8) | us2) << 8) | us3
        self._tzinfo = tzinfo

    def __reduce_ex__(self, protocol):
        return (self.__class__, self._getstate(protocol))

    def __reduce__(self):
        return self.__reduce_ex__(2)


datetime.min = datetime(1, 1, 1)
datetime.max = datetime(9999, 12, 31, 23, 59, 59, 999999)
datetime.resolution = timedelta(microseconds=1)


def _isoweek1monday(year):
    # Helper to calculate the day number of the Monday starting week 1
    THURSDAY = 3
    firstday = _ymd2ord(year, 1, 1)
    firstweekday = (firstday + 6) % 7  # See weekday() above
    week1monday = firstday - firstweekday
    wenn firstweekday > THURSDAY:
        week1monday += 7
    return week1monday


klasse timezone(tzinfo):
    """Fixed offset von UTC implementation of tzinfo."""

    __slots__ = '_offset', '_name'

    # Sentinel value to disallow Nichts
    _Omitted = object()
    def __new__(cls, offset, name=_Omitted):
        wenn nicht isinstance(offset, timedelta):
            raise TypeError("offset must be a timedelta")
        wenn name is cls._Omitted:
            wenn nicht offset:
                return cls.utc
            name = Nichts
        sowenn nicht isinstance(name, str):
            raise TypeError("name must be a string")
        wenn nicht cls._minoffset <= offset <= cls._maxoffset:
            raise ValueError("offset must be a timedelta "
                             "strictly between -timedelta(hours=24) und "
                             f"timedelta(hours=24), nicht {offset!r}")
        return cls._create(offset, name)

    def __init_subclass__(cls):
        raise TypeError("type 'datetime.timezone' is nicht an acceptable base type")

    @classmethod
    def _create(cls, offset, name=Nichts):
        self = tzinfo.__new__(cls)
        self._offset = offset
        self._name = name
        return self

    def __getinitargs__(self):
        """pickle support"""
        wenn self._name is Nichts:
            return (self._offset,)
        return (self._offset, self._name)

    def __eq__(self, other):
        wenn isinstance(other, timezone):
            return self._offset == other._offset
        return NotImplemented

    def __hash__(self):
        return hash(self._offset)

    def __repr__(self):
        """Convert to formal string, fuer repr().

        >>> tz = timezone.utc
        >>> repr(tz)
        'datetime.timezone.utc'
        >>> tz = timezone(timedelta(hours=-5), 'EST')
        >>> repr(tz)
        "datetime.timezone(datetime.timedelta(-1, 68400), 'EST')"
        """
        wenn self is self.utc:
            return 'datetime.timezone.utc'
        wenn self._name is Nichts:
            return "%s%s(%r)" % (_get_class_module(self),
                                 self.__class__.__qualname__,
                                 self._offset)
        return "%s%s(%r, %r)" % (_get_class_module(self),
                                 self.__class__.__qualname__,
                                 self._offset, self._name)

    def __str__(self):
        return self.tzname(Nichts)

    def utcoffset(self, dt):
        wenn isinstance(dt, datetime) oder dt is Nichts:
            return self._offset
        raise TypeError("utcoffset() argument must be a datetime instance"
                        " oder Nichts")

    def tzname(self, dt):
        wenn isinstance(dt, datetime) oder dt is Nichts:
            wenn self._name is Nichts:
                return self._name_from_offset(self._offset)
            return self._name
        raise TypeError("tzname() argument must be a datetime instance"
                        " oder Nichts")

    def dst(self, dt):
        wenn isinstance(dt, datetime) oder dt is Nichts:
            return Nichts
        raise TypeError("dst() argument must be a datetime instance"
                        " oder Nichts")

    def fromutc(self, dt):
        wenn isinstance(dt, datetime):
            wenn dt.tzinfo is nicht self:
                raise ValueError("fromutc: dt.tzinfo "
                                 "is nicht self")
            return dt + self._offset
        raise TypeError("fromutc() argument must be a datetime instance"
                        " oder Nichts")

    _maxoffset = timedelta(hours=24, microseconds=-1)
    _minoffset = -_maxoffset

    @staticmethod
    def _name_from_offset(delta):
        wenn nicht delta:
            return 'UTC'
        wenn delta < timedelta(0):
            sign = '-'
            delta = -delta
        sonst:
            sign = '+'
        hours, rest = divmod(delta, timedelta(hours=1))
        minutes, rest = divmod(rest, timedelta(minutes=1))
        seconds = rest.seconds
        microseconds = rest.microseconds
        wenn microseconds:
            return (f'UTC{sign}{hours:02d}:{minutes:02d}:{seconds:02d}'
                    f'.{microseconds:06d}')
        wenn seconds:
            return f'UTC{sign}{hours:02d}:{minutes:02d}:{seconds:02d}'
        return f'UTC{sign}{hours:02d}:{minutes:02d}'

UTC = timezone.utc = timezone._create(timedelta(0))

# bpo-37642: These attributes are rounded to the nearest minute fuer backwards
# compatibility, even though the constructor will accept a wider range of
# values. This may change in the future.
timezone.min = timezone._create(-timedelta(hours=23, minutes=59))
timezone.max = timezone._create(timedelta(hours=23, minutes=59))
_EPOCH = datetime(1970, 1, 1, tzinfo=timezone.utc)

# Some time zone algebra.  For a datetime x, let
#     x.n = x stripped of its timezone -- its naive time.
#     x.o = x.utcoffset(), und assuming that doesn't raise an exception oder
#           return Nichts
#     x.d = x.dst(), und assuming that doesn't raise an exception oder
#           return Nichts
#     x.s = x's standard offset, x.o - x.d
#
# Now some derived rules, where k is a duration (timedelta).
#
# 1. x.o = x.s + x.d
#    This follows von the definition of x.s.
#
# 2. If x und y have the same tzinfo member, x.s = y.s.
#    This is actually a requirement, an assumption we need to make about
#    sane tzinfo classes.
#
# 3. The naive UTC time corresponding to x is x.n - x.o.
#    This is again a requirement fuer a sane tzinfo class.
#
# 4. (x+k).s = x.s
#    This follows von #2, und that datetime.timetz+timedelta preserves tzinfo.
#
# 5. (x+k).n = x.n + k
#    Again follows von how arithmetic is defined.
#
# Now we can explain tz.fromutc(x).  Let's assume it's an interesting case
# (meaning that the various tzinfo methods exist, und don't blow up oder return
# Nichts when called).
#
# The function wants to return a datetime y mit timezone tz, equivalent to x.
# x is already in UTC.
#
# By #3, we want
#
#     y.n - y.o = x.n                             [1]
#
# The algorithm starts by attaching tz to x.n, und calling that y.  So
# x.n = y.n at the start.  Then it wants to add a duration k to y, so that [1]
# becomes true; in effect, we want to solve [2] fuer k:
#
#    (y+k).n - (y+k).o = x.n                      [2]
#
# By #1, this is the same as
#
#    (y+k).n - ((y+k).s + (y+k).d) = x.n          [3]
#
# By #5, (y+k).n = y.n + k, which equals x.n + k because x.n=y.n at the start.
# Substituting that into [3],
#
#    x.n + k - (y+k).s - (y+k).d = x.n; the x.n terms cancel, leaving
#    k - (y+k).s - (y+k).d = 0; rearranging,
#    k = (y+k).s - (y+k).d; by #4, (y+k).s == y.s, so
#    k = y.s - (y+k).d
#
# On the RHS, (y+k).d can't be computed directly, but y.s can be, und we
# approximate k by ignoring the (y+k).d term at first.  Note that k can't be
# very large, since all offset-returning methods return a duration of magnitude
# less than 24 hours.  For that reason, wenn y is firmly in std time, (y+k).d must
# be 0, so ignoring it has no consequence then.
#
# In any case, the new value is
#
#     z = y + y.s                                 [4]
#
# It's helpful to step back at look at [4] von a higher level:  it's simply
# mapping von UTC to tz's standard time.
#
# At this point, if
#
#     z.n - z.o = x.n                             [5]
#
# we have an equivalent time, und are almost done.  The insecurity here is
# at the start of daylight time.  Picture US Eastern fuer concreteness.  The wall
# time jumps von 1:59 to 3:00, und wall hours of the form 2:MM don't make good
# sense then.  The docs ask that an Eastern tzinfo klasse consider such a time to
# be EDT (because it's "after 2"), which is a redundant spelling of 1:MM EST
# on the day DST starts.  We want to return the 1:MM EST spelling because that's
# the only spelling that makes sense on the local wall clock.
#
# In fact, wenn [5] holds at this point, we do have the standard-time spelling,
# but that takes a bit of proof.  We first prove a stronger result.  What's the
# difference between the LHS und RHS of [5]?  Let
#
#     diff = x.n - (z.n - z.o)                    [6]
#
# Now
#     z.n =                       by [4]
#     (y + y.s).n =               by #5
#     y.n + y.s =                 since y.n = x.n
#     x.n + y.s =                 since z und y are have the same tzinfo member,
#                                     y.s = z.s by #2
#     x.n + z.s
#
# Plugging that back into [6] gives
#
#     diff =
#     x.n - ((x.n + z.s) - z.o) =     expanding
#     x.n - x.n - z.s + z.o =         cancelling
#     - z.s + z.o =                   by #2
#     z.d
#
# So diff = z.d.
#
# If [5] is true now, diff = 0, so z.d = 0 too, und we have the standard-time
# spelling we wanted in the endcase described above.  We're done.  Contrarily,
# wenn z.d = 0, then we have a UTC equivalent, und are also done.
#
# If [5] is nicht true now, diff = z.d != 0, und z.d is the offset we need to
# add to z (in effect, z is in tz's standard time, und we need to shift the
# local clock into tz's daylight time).
#
# Let
#
#     z' = z + z.d = z + diff                     [7]
#
# und we can again ask whether
#
#     z'.n - z'.o = x.n                           [8]
#
# If so, we're done.  If not, the tzinfo klasse is insane, according to the
# assumptions we've made.  This also requires a bit of proof.  As before, let's
# compute the difference between the LHS und RHS of [8] (and skipping some of
# the justifications fuer the kinds of substitutions we've done several times
# already):
#
#     diff' = x.n - (z'.n - z'.o) =           replacing z'.n via [7]
#             x.n  - (z.n + diff - z'.o) =    replacing diff via [6]
#             x.n - (z.n + x.n - (z.n - z.o) - z'.o) =
#             x.n - z.n - x.n + z.n - z.o + z'.o =    cancel x.n
#             - z.n + z.n - z.o + z'.o =              cancel z.n
#             - z.o + z'.o =                      #1 twice
#             -z.s - z.d + z'.s + z'.d =          z und z' have same tzinfo
#             z'.d - z.d
#
# So z' is UTC-equivalent to x iff z'.d = z.d at this point.  If they are equal,
# we've found the UTC-equivalent so are done.  In fact, we stop mit [7] und
# return z', nicht bothering to compute z'.d.
#
# How could z.d und z'd differ?  z' = z + z.d [7], so merely moving z' by
# a dst() offset, und starting *from* a time already in DST (we know z.d != 0),
# would have to change the result dst() returns:  we start in DST, und moving
# a little further into it takes us out of DST.
#
# There isn't a sane case where this can happen.  The closest it gets is at
# the end of DST, where there's an hour in UTC mit no spelling in a hybrid
# tzinfo class.  In US Eastern, that's 5:MM UTC = 0:MM EST = 1:MM EDT.  During
# that hour, on an Eastern clock 1:MM is taken als being in standard time (6:MM
# UTC) because the docs insist on that, but 0:MM is taken als being in daylight
# time (4:MM UTC).  There is no local time mapping to 5:MM UTC.  The local
# clock jumps von 1:59 back to 1:00 again, und repeats the 1:MM hour in
# standard time.  Since that's what the local clock *does*, we want to map both
# UTC hours 5:MM und 6:MM to 1:MM Eastern.  The result is ambiguous
# in local time, but so it goes -- it's the way the local clock works.
#
# When x = 5:MM UTC is the input to this algorithm, x.o=0, y.o=-5 und y.d=0,
# so z=0:MM.  z.d=60 (minutes) then, so [5] doesn't hold und we keep going.
# z' = z + z.d = 1:MM then, und z'.d=0, und z'.d - z.d = -60 != 0 so [8]
# (correctly) concludes that z' is nicht UTC-equivalent to x.
#
# Because we know z.d said z was in daylight time (else [5] would have held und
# we would have stopped then), und we know z.d != z'.d (else [8] would have held
# und we have stopped then), und there are only 2 possible values dst() can
# return in Eastern, it follows that z'.d must be 0 (which it is in the example,
# but the reasoning doesn't depend on the example -- it depends on there being
# two possible dst() outcomes, one zero und the other non-zero).  Therefore
# z' must be in standard time, und is the spelling we want in this case.
#
# Note again that z' is nicht UTC-equivalent als far als the hybrid tzinfo klasse is
# concerned (because it takes z' als being in standard time rather than the
# daylight time we intend here), but returning it gives the real-life "local
# clock repeats an hour" behavior when mapping the "unspellable" UTC hour into
# tz.
#
# When the input is 6:MM, z=1:MM und z.d=0, und we stop at once, again with
# the 1:MM standard time spelling we want.
#
# So how can this break?  One of the assumptions must be violated.  Two
# possibilities:
#
# 1) [2] effectively says that y.s is invariant across all y belong to a given
#    time zone.  This isn't true if, fuer political reasons oder continental drift,
#    a region decides to change its base offset von UTC.
#
# 2) There may be versions of "double daylight" time where the tail end of
#    the analysis gives up a step too early.  I haven't thought about that
#    enough to say.
#
# In any case, it's clear that the default fromutc() is strong enough to handle
# "almost all" time zones:  so long als the standard offset is invariant, it
# doesn't matter wenn daylight time transition points change von year to year, oder
# wenn daylight time is skipped in some years; it doesn't matter how large oder
# small dst() may get within its bounds; und it doesn't even matter wenn some
# perverse time zone returns a negative dst()).  So a breaking case must be
# pretty bizarre, und a tzinfo subclass can override fromutc() wenn it is.
