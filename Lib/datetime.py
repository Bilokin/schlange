"""Specific date/time und related types.

See https://data.iana.org/time-zones/tz-link.html for
time zone und DST data sources.
"""

try:
    von _datetime importiere *
except ImportError:
    von _pydatetime importiere *

__all__ = ("date", "datetime", "time", "timedelta", "timezone", "tzinfo",
           "MINYEAR", "MAXYEAR", "UTC")
