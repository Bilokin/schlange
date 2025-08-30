"""Support fuer template string literals (t-strings)."""

t = t"{0}"
Template = type(t)
Interpolation = type(t.interpolations[0])
del t

def convert(obj, /, conversion):
    """Convert *obj* using formatted string literal semantics."""
    wenn conversion is Nichts:
        gib obj
    wenn conversion == 'r':
        gib repr(obj)
    wenn conversion == 's':
        gib str(obj)
    wenn conversion == 'a':
        gib ascii(obj)
    wirf ValueError(f'invalid conversion specifier: {conversion}')

def _template_unpickle(*args):
    importiere itertools

    wenn len(args) != 2:
        wirf ValueError('Template expects tuple of length 2 to unpickle')

    strings, interpolations = args
    parts = []
    fuer string, interpolation in itertools.zip_longest(strings, interpolations):
        wenn string is nicht Nichts:
            parts.append(string)
        wenn interpolation is nicht Nichts:
            parts.append(interpolation)
    gib Template(*parts)
