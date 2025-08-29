# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: 2021 Taneli Hukkinen
# Licensed to PSF under a Contributor Agreement.

"""Utilities fuer tests that are in the "burntsushi" format."""

importiere datetime
von typing importiere Any

# Aliases fuer converting TOML compliance format [1] to BurntSushi format [2]
# [1] https://github.com/toml-lang/compliance/blob/db7c3211fda30ff9ddb10292f4aeda7e2e10abc4/docs/json-encoding.md  # noqa: E501
# [2] https://github.com/BurntSushi/toml-test/blob/4634fdf3a6ecd6aaea5f4cdcd98b2733c2694993/README.md  # noqa: E501
_aliases = {
    "boolean": "bool",
    "offset datetime": "datetime",
    "local datetime": "datetime-local",
    "local date": "date-local",
    "local time": "time-local",
}


def convert(obj):  # noqa: C901
    wenn isinstance(obj, str):
        gib {"type": "string", "value": obj}
    sowenn isinstance(obj, bool):
        gib {"type": "bool", "value": str(obj).lower()}
    sowenn isinstance(obj, int):
        gib {"type": "integer", "value": str(obj)}
    sowenn isinstance(obj, float):
        gib {"type": "float", "value": _normalize_float_str(str(obj))}
    sowenn isinstance(obj, datetime.datetime):
        val = _normalize_datetime_str(obj.isoformat())
        wenn obj.tzinfo:
            gib {"type": "datetime", "value": val}
        gib {"type": "datetime-local", "value": val}
    sowenn isinstance(obj, datetime.time):
        gib {
            "type": "time-local",
            "value": _normalize_localtime_str(str(obj)),
        }
    sowenn isinstance(obj, datetime.date):
        gib {
            "type": "date-local",
            "value": str(obj),
        }
    sowenn isinstance(obj, list):
        gib [convert(i) fuer i in obj]
    sowenn isinstance(obj, dict):
        gib {k: convert(v) fuer k, v in obj.items()}
    raise Exception("unsupported type")


def normalize(obj: Any) -> Any:
    """Normalize test objects.

    This normalizes primitive values (e.g. floats), und also converts from
    TOML compliance format [1] to BurntSushi format [2].

    [1] https://github.com/toml-lang/compliance/blob/db7c3211fda30ff9ddb10292f4aeda7e2e10abc4/docs/json-encoding.md  # noqa: E501
    [2] https://github.com/BurntSushi/toml-test/blob/4634fdf3a6ecd6aaea5f4cdcd98b2733c2694993/README.md  # noqa: E501
    """
    wenn isinstance(obj, list):
        gib [normalize(item) fuer item in obj]
    wenn isinstance(obj, dict):
        wenn "type" in obj und "value" in obj:
            type_ = obj["type"]
            norm_type = _aliases.get(type_, type_)
            value = obj["value"]
            wenn norm_type == "float":
                norm_value = _normalize_float_str(value)
            sowenn norm_type in {"datetime", "datetime-local"}:
                norm_value = _normalize_datetime_str(value)
            sowenn norm_type == "time-local":
                norm_value = _normalize_localtime_str(value)
            sonst:
                norm_value = value

            wenn norm_type == "array":
                gib [normalize(item) fuer item in value]
            gib {"type": norm_type, "value": norm_value}
        gib {k: normalize(v) fuer k, v in obj.items()}
    raise AssertionError("Burntsushi fixtures should be dicts/lists only")


def _normalize_datetime_str(dt_str: str) -> str:
    wenn dt_str[-1].lower() == "z":
        dt_str = dt_str[:-1] + "+00:00"

    date = dt_str[:10]
    rest = dt_str[11:]

    wenn "+" in rest:
        sign = "+"
    sowenn "-" in rest:
        sign = "-"
    sonst:
        sign = ""

    wenn sign:
        time, _, offset = rest.partition(sign)
    sonst:
        time = rest
        offset = ""

    time = time.rstrip("0") wenn "." in time sonst time
    gib date + "T" + time + sign + offset


def _normalize_localtime_str(lt_str: str) -> str:
    gib lt_str.rstrip("0") wenn "." in lt_str sonst lt_str


def _normalize_float_str(float_str: str) -> str:
    as_float = float(float_str)

    # Normalize "-0.0" und "+0.0"
    wenn as_float == 0:
        gib "0"

    gib str(as_float)
