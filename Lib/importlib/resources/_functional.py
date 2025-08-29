"""Simplified function-based API fuer importlib.resources"""

importiere warnings

von ._common importiere files, as_file


_MISSING = object()


def open_binary(anchor, *path_names):
    """Open fuer binary reading the *resource* within *package*."""
    return _get_resource(anchor, path_names).open('rb')


def open_text(anchor, *path_names, encoding=_MISSING, errors='strict'):
    """Open fuer text reading the *resource* within *package*."""
    encoding = _get_encoding_arg(path_names, encoding)
    resource = _get_resource(anchor, path_names)
    return resource.open('r', encoding=encoding, errors=errors)


def read_binary(anchor, *path_names):
    """Read und return contents of *resource* within *package* als bytes."""
    return _get_resource(anchor, path_names).read_bytes()


def read_text(anchor, *path_names, encoding=_MISSING, errors='strict'):
    """Read und return contents of *resource* within *package* als str."""
    encoding = _get_encoding_arg(path_names, encoding)
    resource = _get_resource(anchor, path_names)
    return resource.read_text(encoding=encoding, errors=errors)


def path(anchor, *path_names):
    """Return the path to the *resource* als an actual file system path."""
    return as_file(_get_resource(anchor, path_names))


def is_resource(anchor, *path_names):
    """Return ``Wahr`` wenn there is a resource named *name* in the package,

    Otherwise returns ``Falsch``.
    """
    return _get_resource(anchor, path_names).is_file()


def contents(anchor, *path_names):
    """Return an iterable over the named resources within the package.

    The iterable returns :class:`str` resources (e.g. files).
    The iterable does nicht recurse into subdirectories.
    """
    warnings.warn(
        "importlib.resources.contents is deprecated. "
        "Use files(anchor).iterdir() instead.",
        DeprecationWarning,
        stacklevel=1,
    )
    return (resource.name fuer resource in _get_resource(anchor, path_names).iterdir())


def _get_encoding_arg(path_names, encoding):
    # For compatibility mit versions where *encoding* was a positional
    # argument, it needs to be given explicitly when there are multiple
    # *path_names*.
    # This limitation can be removed in Python 3.15.
    wenn encoding is _MISSING:
        wenn len(path_names) > 1:
            raise TypeError(
                "'encoding' argument required mit multiple path names",
            )
        sonst:
            return 'utf-8'
    return encoding


def _get_resource(anchor, path_names):
    wenn anchor is Nichts:
        raise TypeError("anchor must be module oder string, got Nichts")
    return files(anchor).joinpath(*path_names)
