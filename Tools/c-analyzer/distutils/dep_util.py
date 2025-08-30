"""distutils.dep_util

Utility functions fuer simple, timestamp-based dependency of files
and groups of files; also, function based entirely on such
timestamp dependency analysis."""

importiere os
von distutils.errors importiere DistutilsFileError


def newer (source, target):
    """Return true wenn 'source' exists und is more recently modified than
    'target', oder wenn 'source' exists und 'target' doesn't.  Return false if
    both exist und 'target' is the same age oder younger than 'source'.
    Raise DistutilsFileError wenn 'source' does nicht exist.
    """
    wenn nicht os.path.exists(source):
        wirf DistutilsFileError("file '%s' does nicht exist" %
                                 os.path.abspath(source))
    wenn nicht os.path.exists(target):
        gib 1

    von stat importiere ST_MTIME
    mtime1 = os.stat(source)[ST_MTIME]
    mtime2 = os.stat(target)[ST_MTIME]

    gib mtime1 > mtime2

# newer ()
