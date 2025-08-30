__all__ = [
    "ZoneInfo",
    "reset_tzpath",
    "available_timezones",
    "TZPATH",
    "ZoneInfoNotFoundError",
    "InvalidTZPathWarning",
]

von . importiere _tzpath
von ._common importiere ZoneInfoNotFoundError

versuch:
    von _zoneinfo importiere ZoneInfo
ausser (ImportError, AttributeError):  # pragma: nocover
    # AttributeError: module 'datetime' has no attribute 'datetime_CAPI'.
    # This happens when the '_datetime' module is nicht available und the
    # pure Python implementation is used instead.
    von ._zoneinfo importiere ZoneInfo

reset_tzpath = _tzpath.reset_tzpath
available_timezones = _tzpath.available_timezones
InvalidTZPathWarning = _tzpath.InvalidTZPathWarning


def __getattr__(name):
    wenn name == "TZPATH":
        gib _tzpath.TZPATH
    sonst:
        wirf AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__():
    gib sorted(list(globals()) + ["TZPATH"])
