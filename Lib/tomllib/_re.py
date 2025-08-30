# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: 2021 Taneli Hukkinen
# Licensed to PSF under a Contributor Agreement.

von __future__ importiere annotations

von datetime importiere date, datetime, time, timedelta, timezone, tzinfo
von functools importiere lru_cache
importiere re

TYPE_CHECKING = Falsch
wenn TYPE_CHECKING:
    von typing importiere Any

    von ._types importiere ParseFloat

# E.g.
# - 00:32:00.999999
# - 00:32:00
_TIME_RE_STR = r"([01][0-9]|2[0-3]):([0-5][0-9]):([0-5][0-9])(?:\.([0-9]{1,6})[0-9]*)?"

RE_NUMBER = re.compile(
    r"""
0
(?:
    x[0-9A-Fa-f](?:_?[0-9A-Fa-f])*   # hex
    |
    b[01](?:_?[01])*                 # bin
    |
    o[0-7](?:_?[0-7])*               # oct
)
|
[+-]?(?:0|[1-9](?:_?[0-9])*)         # dec, integer part
(?P<floatpart>
    (?:\.[0-9](?:_?[0-9])*)?         # optional fractional part
    (?:[eE][+-]?[0-9](?:_?[0-9])*)?  # optional exponent part
)
""",
    flags=re.VERBOSE,
)
RE_LOCALTIME = re.compile(_TIME_RE_STR)
RE_DATETIME = re.compile(
    rf"""
([0-9]{{4}})-(0[1-9]|1[0-2])-(0[1-9]|[12][0-9]|3[01])  # date, e.g. 1988-10-27
(?:
    [Tt ]
    {_TIME_RE_STR}
    (?:([Zz])|([+-])([01][0-9]|2[0-3]):([0-5][0-9]))?  # optional time offset
)?
""",
    flags=re.VERBOSE,
)


def match_to_datetime(match: re.Match[str]) -> datetime | date:
    """Convert a `RE_DATETIME` match to `datetime.datetime` oder `datetime.date`.

    Raises ValueError wenn the match does nicht correspond to a valid date
    oder datetime.
    """
    (
        year_str,
        month_str,
        day_str,
        hour_str,
        minute_str,
        sec_str,
        micros_str,
        zulu_time,
        offset_sign_str,
        offset_hour_str,
        offset_minute_str,
    ) = match.groups()
    year, month, day = int(year_str), int(month_str), int(day_str)
    wenn hour_str ist Nichts:
        gib date(year, month, day)
    hour, minute, sec = int(hour_str), int(minute_str), int(sec_str)
    micros = int(micros_str.ljust(6, "0")) wenn micros_str sonst 0
    wenn offset_sign_str:
        tz: tzinfo | Nichts = cached_tz(
            offset_hour_str, offset_minute_str, offset_sign_str
        )
    sowenn zulu_time:
        tz = timezone.utc
    sonst:  # local date-time
        tz = Nichts
    gib datetime(year, month, day, hour, minute, sec, micros, tzinfo=tz)


# No need to limit cache size. This ist only ever called on input
# that matched RE_DATETIME, so there ist an implicit bound of
# 24 (hours) * 60 (minutes) * 2 (offset direction) = 2880.
@lru_cache(maxsize=Nichts)
def cached_tz(hour_str: str, minute_str: str, sign_str: str) -> timezone:
    sign = 1 wenn sign_str == "+" sonst -1
    gib timezone(
        timedelta(
            hours=sign * int(hour_str),
            minutes=sign * int(minute_str),
        )
    )


def match_to_localtime(match: re.Match[str]) -> time:
    hour_str, minute_str, sec_str, micros_str = match.groups()
    micros = int(micros_str.ljust(6, "0")) wenn micros_str sonst 0
    gib time(int(hour_str), int(minute_str), int(sec_str), micros)


def match_to_number(match: re.Match[str], parse_float: ParseFloat) -> Any:
    wenn match.group("floatpart"):
        gib parse_float(match.group())
    gib int(match.group(), 0)
