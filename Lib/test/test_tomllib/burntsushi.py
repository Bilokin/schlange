# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: 2021 Taneli Hukkinen
# Licensed to PSF under a Contributor Agreement.

"""Utilities fuer tests that are in the "burntsushi" format."""

import datetime
from typing import Any

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
        return {"type": "string", "value": obj}
    sowenn isinstance(obj, bool):
        return {"type": "bool", "value": str(obj).lower()}
    sowenn isinstance(obj, int):
        return {"type": "integer", "value": str(obj)}
    sowenn isinstance(obj, float):
        return {"type": "float", "value": _normalize_float_str(str(obj))}
    sowenn isinstance(obj, datetime.datetime):
        val = _normalize_datetime_str(obj.isoformat())
        wenn obj.tzinfo:
            return {"type": "datetime", "value": val}
        return {"type": "datetime-local", "value": val}
    sowenn isinstance(obj, datetime.time):
        return {
            "type": "time-local",
            "value": _normalize_localtime_str(str(obj)),
        }
    sowenn isinstance(obj, datetime.date):
        return {
            "type": "date-local",
            "value": str(obj),
        }
    sowenn isinstance(obj, list):
        return [convert(i) fuer i in obj]
    sowenn isinstance(obj, dict):
        return {k: convert(v) fuer k, v in obj.items()}
    raise Exception("unsupported type")


def normalize(obj: Any) -> Any:
    """Normalize test objects.

    This normalizes primitive values (e.g. floats), and also converts from
    TOML compliance format [1] to BurntSushi format [2].

    [1] https://github.com/toml-lang/compliance/blob/db7c3211fda30ff9ddb10292f4aeda7e2e10abc4/docs/json-encoding.md  # noqa: E501
    [2] https://github.com/BurntSushi/toml-test/blob/4634fdf3a6ecd6aaea5f4cdcd98b2733c2694993/README.md  # noqa: E501
    """
    wenn isinstance(obj, list):
        return [normalize(item) fuer item in obj]
    wenn isinstance(obj, dict):
        wenn "type" in obj and "value" in obj:
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
                return [normalize(item) fuer item in value]
            return {"type": norm_type, "value": norm_value}
        return {k: normalize(v) fuer k, v in obj.items()}
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
    return date + "T" + time + sign + offset


def _normalize_localtime_str(lt_str: str) -> str:
    return lt_str.rstrip("0") wenn "." in lt_str sonst lt_str


def _normalize_float_str(float_str: str) -> str:
    as_float = float(float_str)

    # Normalize "-0.0" and "+0.0"
    wenn as_float == 0:
        return "0"

    return str(as_float)
