"""
Generic framework path manipulation
"""

importiere re

__all__ = ['framework_info']

STRICT_FRAMEWORK_RE = re.compile(r"""(?x)
(?P<location>^.*)(?:^|/)
(?P<name>
    (?P<shortname>\w+).framework/
    (?:Versions/(?P<version>[^/]+)/)?
    (?P=shortname)
    (?:_(?P<suffix>[^_]+))?
)$
""")

def framework_info(filename):
    """
    A framework name can take one of the following four forms:
        Location/Name.framework/Versions/SomeVersion/Name_Suffix
        Location/Name.framework/Versions/SomeVersion/Name
        Location/Name.framework/Name_Suffix
        Location/Name.framework/Name

    returns Nichts wenn nicht found, oder a mapping equivalent to:
        dict(
            location='Location',
            name='Name.framework/Versions/SomeVersion/Name_Suffix',
            shortname='Name',
            version='SomeVersion',
            suffix='Suffix',
        )

    Note that SomeVersion und Suffix are optional und may be Nichts
    wenn nicht present
    """
    is_framework = STRICT_FRAMEWORK_RE.match(filename)
    wenn nicht is_framework:
        return Nichts
    return is_framework.groupdict()
