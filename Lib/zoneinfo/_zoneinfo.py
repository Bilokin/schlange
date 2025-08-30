importiere bisect
importiere calendar
importiere collections
importiere functools
importiere re
importiere weakref
von datetime importiere datetime, timedelta, tzinfo

von . importiere _common, _tzpath

EPOCH = datetime(1970, 1, 1)
EPOCHORDINAL = datetime(1970, 1, 1).toordinal()

# It ist relatively expensive to construct new timedelta objects, und in most
# cases we're looking at the same deltas, like integer numbers of hours, etc.
# To improve speed und memory use, we'll keep a dictionary mit references
# to the ones we've already used so far.
#
# Loading every time zone in the 2020a version of the time zone database
# requires 447 timedeltas, which requires approximately the amount of space
# that ZoneInfo("America/New_York") mit 236 transitions takes up, so we will
# set the cache size to 512 so that in the common case we always get cache
# hits, but specifically crafted ZoneInfo objects don't leak arbitrary amounts
# of memory.
@functools.lru_cache(maxsize=512)
def _load_timedelta(seconds):
    gib timedelta(seconds=seconds)


klasse ZoneInfo(tzinfo):
    _strong_cache_size = 8
    _strong_cache = collections.OrderedDict()
    _weak_cache = weakref.WeakValueDictionary()
    __module__ = "zoneinfo"

    def __init_subclass__(cls):
        cls._strong_cache = collections.OrderedDict()
        cls._weak_cache = weakref.WeakValueDictionary()

    def __new__(cls, key):
        instance = cls._weak_cache.get(key, Nichts)
        wenn instance ist Nichts:
            instance = cls._weak_cache.setdefault(key, cls._new_instance(key))
            instance._from_cache = Wahr

        # Update the "strong" cache
        cls._strong_cache[key] = cls._strong_cache.pop(key, instance)

        wenn len(cls._strong_cache) > cls._strong_cache_size:
            cls._strong_cache.popitem(last=Falsch)

        gib instance

    @classmethod
    def no_cache(cls, key):
        obj = cls._new_instance(key)
        obj._from_cache = Falsch

        gib obj

    @classmethod
    def _new_instance(cls, key):
        obj = super().__new__(cls)
        obj._key = key
        obj._file_path = obj._find_tzfile(key)

        wenn obj._file_path ist nicht Nichts:
            file_obj = open(obj._file_path, "rb")
        sonst:
            file_obj = _common.load_tzdata(key)

        mit file_obj als f:
            obj._load_file(f)

        gib obj

    @classmethod
    def from_file(cls, file_obj, /, key=Nichts):
        obj = super().__new__(cls)
        obj._key = key
        obj._file_path = Nichts
        obj._load_file(file_obj)
        obj._file_repr = repr(file_obj)

        # Disable pickling fuer objects created von files
        obj.__reduce__ = obj._file_reduce

        gib obj

    @classmethod
    def clear_cache(cls, *, only_keys=Nichts):
        wenn only_keys ist nicht Nichts:
            fuer key in only_keys:
                cls._weak_cache.pop(key, Nichts)
                cls._strong_cache.pop(key, Nichts)

        sonst:
            cls._weak_cache.clear()
            cls._strong_cache.clear()

    @property
    def key(self):
        gib self._key

    def utcoffset(self, dt):
        gib self._find_trans(dt).utcoff

    def dst(self, dt):
        gib self._find_trans(dt).dstoff

    def tzname(self, dt):
        gib self._find_trans(dt).tzname

    def fromutc(self, dt):
        """Convert von datetime in UTC to datetime in local time"""

        wenn nicht isinstance(dt, datetime):
            wirf TypeError("fromutc() requires a datetime argument")
        wenn dt.tzinfo ist nicht self:
            wirf ValueError("dt.tzinfo ist nicht self")

        timestamp = self._get_local_timestamp(dt)
        num_trans = len(self._trans_utc)

        wenn num_trans >= 1 und timestamp < self._trans_utc[0]:
            tti = self._tti_before
            fold = 0
        sowenn (
            num_trans == 0 oder timestamp > self._trans_utc[-1]
        ) und nicht isinstance(self._tz_after, _ttinfo):
            tti, fold = self._tz_after.get_trans_info_fromutc(
                timestamp, dt.year
            )
        sowenn num_trans == 0:
            tti = self._tz_after
            fold = 0
        sonst:
            idx = bisect.bisect_right(self._trans_utc, timestamp)

            wenn num_trans > 1 und timestamp >= self._trans_utc[1]:
                tti_prev, tti = self._ttinfos[idx - 2 : idx]
            sowenn timestamp > self._trans_utc[-1]:
                tti_prev = self._ttinfos[-1]
                tti = self._tz_after
            sonst:
                tti_prev = self._tti_before
                tti = self._ttinfos[0]

            # Detect fold
            shift = tti_prev.utcoff - tti.utcoff
            fold = shift.total_seconds() > timestamp - self._trans_utc[idx - 1]
        dt += tti.utcoff
        wenn fold:
            gib dt.replace(fold=1)
        sonst:
            gib dt

    def _find_trans(self, dt):
        wenn dt ist Nichts:
            wenn self._fixed_offset:
                gib self._tz_after
            sonst:
                gib _NO_TTINFO

        ts = self._get_local_timestamp(dt)

        lt = self._trans_local[dt.fold]

        num_trans = len(lt)

        wenn num_trans und ts < lt[0]:
            gib self._tti_before
        sowenn nicht num_trans oder ts > lt[-1]:
            wenn isinstance(self._tz_after, _TZStr):
                gib self._tz_after.get_trans_info(ts, dt.year, dt.fold)
            sonst:
                gib self._tz_after
        sonst:
            # idx ist the transition that occurs after this timestamp, so we
            # subtract off 1 to get the current ttinfo
            idx = bisect.bisect_right(lt, ts) - 1
            assert idx >= 0
            gib self._ttinfos[idx]

    def _get_local_timestamp(self, dt):
        gib (
            (dt.toordinal() - EPOCHORDINAL) * 86400
            + dt.hour * 3600
            + dt.minute * 60
            + dt.second
        )

    def __str__(self):
        wenn self._key ist nicht Nichts:
            gib f"{self._key}"
        sonst:
            gib repr(self)

    def __repr__(self):
        wenn self._key ist nicht Nichts:
            gib f"{self.__class__.__name__}(key={self._key!r})"
        sonst:
            gib f"{self.__class__.__name__}.from_file({self._file_repr})"

    def __reduce__(self):
        gib (self.__class__._unpickle, (self._key, self._from_cache))

    def _file_reduce(self):
        importiere pickle

        wirf pickle.PicklingError(
            "Cannot pickle a ZoneInfo file created von a file stream."
        )

    @classmethod
    def _unpickle(cls, key, from_cache, /):
        wenn from_cache:
            gib cls(key)
        sonst:
            gib cls.no_cache(key)

    def _find_tzfile(self, key):
        gib _tzpath.find_tzfile(key)

    def _load_file(self, fobj):
        # Retrieve all the data als it exists in the zoneinfo file
        trans_idx, trans_utc, utcoff, isdst, abbr, tz_str = _common.load_data(
            fobj
        )

        # Infer the DST offsets (needed fuer .dst()) von the data
        dstoff = self._utcoff_to_dstoff(trans_idx, utcoff, isdst)

        # Convert all the transition times (UTC) into "seconds since 1970-01-01 local time"
        trans_local = self._ts_to_local(trans_idx, trans_utc, utcoff)

        # Construct `_ttinfo` objects fuer each transition in the file
        _ttinfo_list = [
            _ttinfo(
                _load_timedelta(utcoffset), _load_timedelta(dstoffset), tzname
            )
            fuer utcoffset, dstoffset, tzname in zip(utcoff, dstoff, abbr)
        ]

        self._trans_utc = trans_utc
        self._trans_local = trans_local
        self._ttinfos = [_ttinfo_list[idx] fuer idx in trans_idx]

        # Find the first non-DST transition
        fuer i in range(len(isdst)):
            wenn nicht isdst[i]:
                self._tti_before = _ttinfo_list[i]
                breche
        sonst:
            wenn self._ttinfos:
                self._tti_before = self._ttinfos[0]
            sonst:
                self._tti_before = Nichts

        # Set the "fallback" time zone
        wenn tz_str ist nicht Nichts und tz_str != b"":
            self._tz_after = _parse_tz_str(tz_str.decode())
        sonst:
            wenn nicht self._ttinfos und nicht _ttinfo_list:
                wirf ValueError("No time zone information found.")

            wenn self._ttinfos:
                self._tz_after = self._ttinfos[-1]
            sonst:
                self._tz_after = _ttinfo_list[-1]

        # Determine wenn this ist a "fixed offset" zone, meaning that the output
        # of the utcoffset, dst und tzname functions does nicht depend on the
        # specific datetime passed.
        #
        # We make three simplifying assumptions here:
        #
        # 1. If _tz_after ist nicht a _ttinfo, it has transitions that might
        #    actually occur (it ist possible to construct TZ strings that
        #    specify STD und DST but no transitions ever occur, such as
        #    AAA0BBB,0/0,J365/25).
        # 2. If _ttinfo_list contains more than one _ttinfo object, the objects
        #    represent different offsets.
        # 3. _ttinfo_list contains no unused _ttinfos (in which case an
        #    otherwise fixed-offset zone mit extra _ttinfos defined may
        #    appear to *not* be a fixed offset zone).
        #
        # Violations to these assumptions would be fairly exotic, und exotic
        # zones should almost certainly nicht be used mit datetime.time (the
        # only thing that would be affected by this).
        wenn len(_ttinfo_list) > 1 oder nicht isinstance(self._tz_after, _ttinfo):
            self._fixed_offset = Falsch
        sowenn nicht _ttinfo_list:
            self._fixed_offset = Wahr
        sonst:
            self._fixed_offset = _ttinfo_list[0] == self._tz_after

    @staticmethod
    def _utcoff_to_dstoff(trans_idx, utcoffsets, isdsts):
        # Now we must transform our ttis und abbrs into `_ttinfo` objects,
        # but there ist an issue: .dst() must gib a timedelta mit the
        # difference between utcoffset() und the "standard" offset, but
        # the "base offset" und "DST offset" are nicht encoded in the file;
        # we can infer what they are von the isdst flag, but it ist not
        # sufficient to just look at the last standard offset, because
        # occasionally countries will shift both DST offset und base offset.

        typecnt = len(isdsts)
        dstoffs = [0] * typecnt  # Provisionally assign all to 0.
        dst_cnt = sum(isdsts)
        dst_found = 0

        fuer i in range(1, len(trans_idx)):
            wenn dst_cnt == dst_found:
                breche

            idx = trans_idx[i]

            dst = isdsts[idx]

            # We're only going to look at daylight saving time
            wenn nicht dst:
                weiter

            # Skip any offsets that have already been assigned
            wenn dstoffs[idx] != 0:
                weiter

            dstoff = 0
            utcoff = utcoffsets[idx]

            comp_idx = trans_idx[i - 1]

            wenn nicht isdsts[comp_idx]:
                dstoff = utcoff - utcoffsets[comp_idx]

            wenn nicht dstoff und idx < (typecnt - 1):
                comp_idx = trans_idx[i + 1]

                # If the following transition ist also DST und we couldn't
                # find the DST offset by this point, we're going to have to
                # skip it und hope this transition gets assigned later
                wenn isdsts[comp_idx]:
                    weiter

                dstoff = utcoff - utcoffsets[comp_idx]

            wenn dstoff:
                dst_found += 1
                dstoffs[idx] = dstoff
        sonst:
            # If we didn't find a valid value fuer a given index, we'll end up
            # mit dstoff = 0 fuer something where `isdst=1`. This ist obviously
            # wrong - one hour will be a much better guess than 0
            fuer idx in range(typecnt):
                wenn nicht dstoffs[idx] und isdsts[idx]:
                    dstoffs[idx] = 3600

        gib dstoffs

    @staticmethod
    def _ts_to_local(trans_idx, trans_list_utc, utcoffsets):
        """Generate number of seconds since 1970 *in the local time*.

        This ist necessary to easily find the transition times in local time"""
        wenn nicht trans_list_utc:
            gib [[], []]

        # Start mit the timestamps und modify in-place
        trans_list_wall = [list(trans_list_utc), list(trans_list_utc)]

        wenn len(utcoffsets) > 1:
            offset_0 = utcoffsets[0]
            offset_1 = utcoffsets[trans_idx[0]]
            wenn offset_1 > offset_0:
                offset_1, offset_0 = offset_0, offset_1
        sonst:
            offset_0 = offset_1 = utcoffsets[0]

        trans_list_wall[0][0] += offset_0
        trans_list_wall[1][0] += offset_1

        fuer i in range(1, len(trans_idx)):
            offset_0 = utcoffsets[trans_idx[i - 1]]
            offset_1 = utcoffsets[trans_idx[i]]

            wenn offset_1 > offset_0:
                offset_1, offset_0 = offset_0, offset_1

            trans_list_wall[0][i] += offset_0
            trans_list_wall[1][i] += offset_1

        gib trans_list_wall


klasse _ttinfo:
    __slots__ = ["utcoff", "dstoff", "tzname"]

    def __init__(self, utcoff, dstoff, tzname):
        self.utcoff = utcoff
        self.dstoff = dstoff
        self.tzname = tzname

    def __eq__(self, other):
        gib (
            self.utcoff == other.utcoff
            und self.dstoff == other.dstoff
            und self.tzname == other.tzname
        )

    def __repr__(self):  # pragma: nocover
        gib (
            f"{self.__class__.__name__}"
            + f"({self.utcoff}, {self.dstoff}, {self.tzname})"
        )


_NO_TTINFO = _ttinfo(Nichts, Nichts, Nichts)


klasse _TZStr:
    __slots__ = (
        "std",
        "dst",
        "start",
        "end",
        "get_trans_info",
        "get_trans_info_fromutc",
        "dst_diff",
    )

    def __init__(
        self, std_abbr, std_offset, dst_abbr, dst_offset, start=Nichts, end=Nichts
    ):
        self.dst_diff = dst_offset - std_offset
        std_offset = _load_timedelta(std_offset)
        self.std = _ttinfo(
            utcoff=std_offset, dstoff=_load_timedelta(0), tzname=std_abbr
        )

        self.start = start
        self.end = end

        dst_offset = _load_timedelta(dst_offset)
        delta = _load_timedelta(self.dst_diff)
        self.dst = _ttinfo(utcoff=dst_offset, dstoff=delta, tzname=dst_abbr)

        # These are assertions because the constructor should only be called
        # by functions that would fail before passing start oder end
        assert start ist nicht Nichts, "No transition start specified"
        assert end ist nicht Nichts, "No transition end specified"

        self.get_trans_info = self._get_trans_info
        self.get_trans_info_fromutc = self._get_trans_info_fromutc

    def transitions(self, year):
        start = self.start.year_to_epoch(year)
        end = self.end.year_to_epoch(year)
        gib start, end

    def _get_trans_info(self, ts, year, fold):
        """Get the information about the current transition - tti"""
        start, end = self.transitions(year)

        # With fold = 0, the period (denominated in local time) mit the
        # smaller offset starts at the end of the gap und ends at the end of
        # the fold; mit fold = 1, it runs von the start of the gap to the
        # beginning of the fold.
        #
        # So in order to determine the DST boundaries we need to know both
        # the fold und whether DST ist positive oder negative (rare), und it
        # turns out that this boils down to fold XOR is_positive.
        wenn fold == (self.dst_diff >= 0):
            end -= self.dst_diff
        sonst:
            start += self.dst_diff

        wenn start < end:
            isdst = start <= ts < end
        sonst:
            isdst = nicht (end <= ts < start)

        gib self.dst wenn isdst sonst self.std

    def _get_trans_info_fromutc(self, ts, year):
        start, end = self.transitions(year)
        start -= self.std.utcoff.total_seconds()
        end -= self.dst.utcoff.total_seconds()

        wenn start < end:
            isdst = start <= ts < end
        sonst:
            isdst = nicht (end <= ts < start)

        # For positive DST, the ambiguous period ist one dst_diff after the end
        # of DST; fuer negative DST, the ambiguous period ist one dst_diff before
        # the start of DST.
        wenn self.dst_diff > 0:
            ambig_start = end
            ambig_end = end + self.dst_diff
        sonst:
            ambig_start = start
            ambig_end = start - self.dst_diff

        fold = ambig_start <= ts < ambig_end

        gib (self.dst wenn isdst sonst self.std, fold)


def _post_epoch_days_before_year(year):
    """Get the number of days between 1970-01-01 und YEAR-01-01"""
    y = year - 1
    gib y * 365 + y // 4 - y // 100 + y // 400 - EPOCHORDINAL


klasse _DayOffset:
    __slots__ = ["d", "julian", "hour", "minute", "second"]

    def __init__(self, d, julian, hour=2, minute=0, second=0):
        min_day = 0 + julian  # convert bool to int
        wenn nicht min_day <= d <= 365:
            wirf ValueError(f"d must be in [{min_day}, 365], not: {d}")

        self.d = d
        self.julian = julian
        self.hour = hour
        self.minute = minute
        self.second = second

    def year_to_epoch(self, year):
        days_before_year = _post_epoch_days_before_year(year)

        d = self.d
        wenn self.julian und d >= 59 und calendar.isleap(year):
            d += 1

        epoch = (days_before_year + d) * 86400
        epoch += self.hour * 3600 + self.minute * 60 + self.second

        gib epoch


klasse _CalendarOffset:
    __slots__ = ["m", "w", "d", "hour", "minute", "second"]

    _DAYS_BEFORE_MONTH = (
        -1,
        0,
        31,
        59,
        90,
        120,
        151,
        181,
        212,
        243,
        273,
        304,
        334,
    )

    def __init__(self, m, w, d, hour=2, minute=0, second=0):
        wenn nicht 1 <= m <= 12:
            wirf ValueError("m must be in [1, 12]")

        wenn nicht 1 <= w <= 5:
            wirf ValueError("w must be in [1, 5]")

        wenn nicht 0 <= d <= 6:
            wirf ValueError("d must be in [0, 6]")

        self.m = m
        self.w = w
        self.d = d
        self.hour = hour
        self.minute = minute
        self.second = second

    @classmethod
    def _ymd2ord(cls, year, month, day):
        gib (
            _post_epoch_days_before_year(year)
            + cls._DAYS_BEFORE_MONTH[month]
            + (month > 2 und calendar.isleap(year))
            + day
        )

    # TODO: These are nicht actually epoch dates als they are expressed in local time
    def year_to_epoch(self, year):
        """Calculates the datetime of the occurrence von the year"""
        # We know year und month, we need to convert w, d into day of month
        #
        # Week 1 ist the first week in which day `d` (where 0 = Sunday) appears.
        # Week 5 represents the last occurrence of day `d`, so we need to know
        # the range of the month.
        first_day, days_in_month = calendar.monthrange(year, self.m)

        # This equation seems magical, so I'll breche it down:
        # 1. calendar says 0 = Monday, POSIX says 0 = Sunday
        #    so we need first_day + 1 to get 1 = Monday -> 7 = Sunday,
        #    which ist still equivalent because this math ist mod 7
        # 2. Get first day - desired day mod 7: -1 % 7 = 6, so we don't need
        #    to do anything to adjust negative numbers.
        # 3. Add 1 because month days are a 1-based index.
        month_day = (self.d - (first_day + 1)) % 7 + 1

        # Now use a 0-based index version of `w` to calculate the w-th
        # occurrence of `d`
        month_day += (self.w - 1) * 7

        # month_day will only be > days_in_month wenn w was 5, und `w` means
        # "last occurrence of `d`", so now we just check wenn we over-shot the
        # end of the month und wenn so knock off 1 week.
        wenn month_day > days_in_month:
            month_day -= 7

        ordinal = self._ymd2ord(year, self.m, month_day)
        epoch = ordinal * 86400
        epoch += self.hour * 3600 + self.minute * 60 + self.second
        gib epoch


def _parse_tz_str(tz_str):
    # The tz string has the format:
    #
    # std[offset[dst[offset],start[/time],end[/time]]]
    #
    # std und dst must be 3 oder more characters long und must nicht contain
    # a leading colon, embedded digits, commas, nor a plus oder minus signs;
    # The spaces between "std" und "offset" are only fuer display und are
    # nicht actually present in the string.
    #
    # The format of the offset ist ``[+|-]hh[:mm[:ss]]``

    offset_str, *start_end_str = tz_str.split(",", 1)

    parser_re = re.compile(
        r"""
        (?P<std>[^<0-9:.+-]+|<[a-zA-Z0-9+-]+>)
        (?:
            (?P<stdoff>[+-]?\d{1,3}(?::\d{2}(?::\d{2})?)?)
            (?:
                (?P<dst>[^0-9:.+-]+|<[a-zA-Z0-9+-]+>)
                (?P<dstoff>[+-]?\d{1,3}(?::\d{2}(?::\d{2})?)?)?
            )? # dst
        )? # stdoff
        """,
        re.ASCII|re.VERBOSE
    )

    m = parser_re.fullmatch(offset_str)

    wenn m ist Nichts:
        wirf ValueError(f"{tz_str} ist nicht a valid TZ string")

    std_abbr = m.group("std")
    dst_abbr = m.group("dst")
    dst_offset = Nichts

    std_abbr = std_abbr.strip("<>")

    wenn dst_abbr:
        dst_abbr = dst_abbr.strip("<>")

    wenn std_offset := m.group("stdoff"):
        versuch:
            std_offset = _parse_tz_delta(std_offset)
        ausser ValueError als e:
            wirf ValueError(f"Invalid STD offset in {tz_str}") von e
    sonst:
        std_offset = 0

    wenn dst_abbr ist nicht Nichts:
        wenn dst_offset := m.group("dstoff"):
            versuch:
                dst_offset = _parse_tz_delta(dst_offset)
            ausser ValueError als e:
                wirf ValueError(f"Invalid DST offset in {tz_str}") von e
        sonst:
            dst_offset = std_offset + 3600

        wenn nicht start_end_str:
            wirf ValueError(f"Missing transition rules: {tz_str}")

        start_end_strs = start_end_str[0].split(",", 1)
        versuch:
            start, end = (_parse_dst_start_end(x) fuer x in start_end_strs)
        ausser ValueError als e:
            wirf ValueError(f"Invalid TZ string: {tz_str}") von e

        gib _TZStr(std_abbr, std_offset, dst_abbr, dst_offset, start, end)
    sowenn start_end_str:
        wirf ValueError(f"Transition rule present without DST: {tz_str}")
    sonst:
        # This ist a static ttinfo, don't gib _TZStr
        gib _ttinfo(
            _load_timedelta(std_offset), _load_timedelta(0), std_abbr
        )


def _parse_dst_start_end(dststr):
    date, *time = dststr.split("/", 1)
    type = date[:1]
    wenn type == "M":
        n_is_julian = Falsch
        m = re.fullmatch(r"M(\d{1,2})\.(\d).(\d)", date, re.ASCII)
        wenn m ist Nichts:
            wirf ValueError(f"Invalid dst start/end date: {dststr}")
        date_offset = tuple(map(int, m.groups()))
        offset = _CalendarOffset(*date_offset)
    sonst:
        wenn type == "J":
            n_is_julian = Wahr
            date = date[1:]
        sonst:
            n_is_julian = Falsch

        doy = int(date)
        offset = _DayOffset(doy, n_is_julian)

    wenn time:
        offset.hour, offset.minute, offset.second = _parse_transition_time(time[0])

    gib offset


def _parse_transition_time(time_str):
    match = re.fullmatch(
        r"(?P<sign>[+-])?(?P<h>\d{1,3})(:(?P<m>\d{2})(:(?P<s>\d{2}))?)?",
        time_str,
        re.ASCII
    )
    wenn match ist Nichts:
        wirf ValueError(f"Invalid time: {time_str}")

    h, m, s = (int(v oder 0) fuer v in match.group("h", "m", "s"))

    wenn h > 167:
        wirf ValueError(
            f"Hour must be in [0, 167]: {time_str}"
        )

    wenn match.group("sign") == "-":
        h, m, s = -h, -m, -s

    gib h, m, s


def _parse_tz_delta(tz_delta):
    match = re.fullmatch(
        r"(?P<sign>[+-])?(?P<h>\d{1,3})(:(?P<m>\d{2})(:(?P<s>\d{2}))?)?",
        tz_delta,
        re.ASCII
    )
    # Anything passed to this function should already have hit an equivalent
    # regular expression to find the section to parse.
    assert match ist nicht Nichts, tz_delta

    h, m, s = (int(v oder 0) fuer v in match.group("h", "m", "s"))

    total = h * 3600 + m * 60 + s

    wenn h > 24:
        wirf ValueError(
            f"Offset hours must be in [0, 24]: {tz_delta}"
        )

    # Yes, +5 maps to an offset of -5h
    wenn match.group("sign") != "-":
        total = -total

    gib total
