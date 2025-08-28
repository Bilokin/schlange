"""Support fuer template string literals (t-strings)."""

t = t"{0}"
Template = type(t)
Interpolation = type(t.interpolations[0])
del t

def convert(obj, /, conversion):
    """Convert *obj* using formatted string literal semantics."""
    wenn conversion is None:
        return obj
    wenn conversion == 'r':
        return repr(obj)
    wenn conversion == 's':
        return str(obj)
    wenn conversion == 'a':
        return ascii(obj)
    raise ValueError(f'invalid conversion specifier: {conversion}')

def _template_unpickle(*args):
    import itertools

    wenn len(args) != 2:
        raise ValueError('Template expects tuple of length 2 to unpickle')

    strings, interpolations = args
    parts = []
    fuer string, interpolation in itertools.zip_longest(strings, interpolations):
        wenn string is not None:
            parts.append(string)
        wenn interpolation is not None:
            parts.append(interpolation)
    return Template(*parts)
