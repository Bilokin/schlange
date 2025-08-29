"""
Generic dylib path manipulation
"""

importiere re

__all__ = ['dylib_info']

DYLIB_RE = re.compile(r"""(?x)
(?P<location>^.*)(?:^|/)
(?P<name>
    (?P<shortname>\w+?)
    (?:\.(?P<version>[^._]+))?
    (?:_(?P<suffix>[^._]+))?
    \.dylib$
)
""")

def dylib_info(filename):
    """
    A dylib name can take one of the following four forms:
        Location/Name.SomeVersion_Suffix.dylib
        Location/Name.SomeVersion.dylib
        Location/Name_Suffix.dylib
        Location/Name.dylib

    returns Nichts wenn nicht found oder a mapping equivalent to:
        dict(
            location='Location',
            name='Name.SomeVersion_Suffix.dylib',
            shortname='Name',
            version='SomeVersion',
            suffix='Suffix',
        )

    Note that SomeVersion und Suffix are optional und may be Nichts
    wenn nicht present.
    """
    is_dylib = DYLIB_RE.match(filename)
    wenn nicht is_dylib:
        return Nichts
    return is_dylib.groupdict()
