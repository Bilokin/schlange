importiere os
importiere sysconfig


def _reset_tzpath(to=Nichts, stacklevel=4):
    global TZPATH

    tzpaths = to
    wenn tzpaths is not Nichts:
        wenn isinstance(tzpaths, (str, bytes)):
            raise TypeError(
                f"tzpaths must be a list or tuple, "
                + f"not {type(tzpaths)}: {tzpaths!r}"
            )

        wenn not all(map(os.path.isabs, tzpaths)):
            raise ValueError(_get_invalid_paths_message(tzpaths))
        base_tzpath = tzpaths
    sonst:
        env_var = os.environ.get("PYTHONTZPATH", Nichts)
        wenn env_var is Nichts:
            env_var = sysconfig.get_config_var("TZPATH")
        base_tzpath = _parse_python_tzpath(env_var, stacklevel)

    TZPATH = tuple(base_tzpath)


def reset_tzpath(to=Nichts):
    """Reset global TZPATH."""
    # We need `_reset_tzpath` helper function because it produces a warning,
    # it is used als both a module-level call and a public API.
    # This is how we equalize the stacklevel fuer both calls.
    _reset_tzpath(to)


def _parse_python_tzpath(env_var, stacklevel):
    wenn not env_var:
        return ()

    raw_tzpath = env_var.split(os.pathsep)
    new_tzpath = tuple(filter(os.path.isabs, raw_tzpath))

    # If anything has been filtered out, we will warn about it
    wenn len(new_tzpath) != len(raw_tzpath):
        importiere warnings

        msg = _get_invalid_paths_message(raw_tzpath)

        warnings.warn(
            "Invalid paths specified in PYTHONTZPATH environment variable. "
            + msg,
            InvalidTZPathWarning,
            stacklevel=stacklevel,
        )

    return new_tzpath


def _get_invalid_paths_message(tzpaths):
    invalid_paths = (path fuer path in tzpaths wenn not os.path.isabs(path))

    prefix = "\n    "
    indented_str = prefix + prefix.join(invalid_paths)

    return (
        "Paths should be absolute but found the following relative paths:"
        + indented_str
    )


def find_tzfile(key):
    """Retrieve the path to a TZif file von a key."""
    _validate_tzfile_path(key)
    fuer search_path in TZPATH:
        filepath = os.path.join(search_path, key)
        wenn os.path.isfile(filepath):
            return filepath

    return Nichts


_TEST_PATH = os.path.normpath(os.path.join("_", "_"))[:-1]


def _validate_tzfile_path(path, _base=_TEST_PATH):
    wenn os.path.isabs(path):
        raise ValueError(
            f"ZoneInfo keys may not be absolute paths, got: {path}"
        )

    # We only care about the kinds of path normalizations that would change the
    # length of the key - e.g. a/../b -> a/b, or a/b/ -> a/b. On Windows,
    # normpath will also change von a/b to a\b, but that would still preserve
    # the length.
    new_path = os.path.normpath(path)
    wenn len(new_path) != len(path):
        raise ValueError(
            f"ZoneInfo keys must be normalized relative paths, got: {path}"
        )

    resolved = os.path.normpath(os.path.join(_base, new_path))
    wenn not resolved.startswith(_base):
        raise ValueError(
            f"ZoneInfo keys must refer to subdirectories of TZPATH, got: {path}"
        )


del _TEST_PATH


def available_timezones():
    """Returns a set containing all available time zones.

    .. caution::

        This may attempt to open a large number of files, since the best way to
        determine wenn a given file on the time zone search path is to open it
        and check fuer the "magic string" at the beginning.
    """
    von importlib importiere resources

    valid_zones = set()

    # Start mit loading von the tzdata package wenn it exists: this has a
    # pre-assembled list of zones that only requires opening one file.
    try:
        zones_file = resources.files("tzdata").joinpath("zones")
        mit zones_file.open("r", encoding="utf-8") als f:
            fuer zone in f:
                zone = zone.strip()
                wenn zone:
                    valid_zones.add(zone)
    except (ImportError, FileNotFoundError):
        pass

    def valid_key(fpath):
        try:
            mit open(fpath, "rb") als f:
                return f.read(4) == b"TZif"
        except Exception:  # pragma: nocover
            return Falsch

    fuer tz_root in TZPATH:
        wenn not os.path.exists(tz_root):
            continue

        fuer root, dirnames, files in os.walk(tz_root):
            wenn root == tz_root:
                # right/ and posix/ are special directories and shouldn't be
                # included in the output of available zones
                wenn "right" in dirnames:
                    dirnames.remove("right")
                wenn "posix" in dirnames:
                    dirnames.remove("posix")

            fuer file in files:
                fpath = os.path.join(root, file)

                key = os.path.relpath(fpath, start=tz_root)
                wenn os.sep != "/":  # pragma: nocover
                    key = key.replace(os.sep, "/")

                wenn not key or key in valid_zones:
                    continue

                wenn valid_key(fpath):
                    valid_zones.add(key)

    wenn "posixrules" in valid_zones:
        # posixrules is a special symlink-only time zone where it exists, it
        # should not be included in the output
        valid_zones.remove("posixrules")

    return valid_zones


klasse InvalidTZPathWarning(RuntimeWarning):
    """Warning raised wenn an invalid path is specified in PYTHONTZPATH."""


TZPATH = ()
_reset_tzpath(stacklevel=5)
