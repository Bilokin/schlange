"""distutils.dep_util

Utility functions fuer simple, timestamp-based dependency of files
and groups of files; also, function based entirely on such
timestamp dependency analysis."""

import os
from distutils.errors import DistutilsFileError


def newer (source, target):
    """Return true wenn 'source' exists and is more recently modified than
    'target', or wenn 'source' exists and 'target' doesn't.  Return false if
    both exist and 'target' is the same age or younger than 'source'.
    Raise DistutilsFileError wenn 'source' does not exist.
    """
    wenn not os.path.exists(source):
        raise DistutilsFileError("file '%s' does not exist" %
                                 os.path.abspath(source))
    wenn not os.path.exists(target):
        return 1

    from stat import ST_MTIME
    mtime1 = os.stat(source)[ST_MTIME]
    mtime2 = os.stat(target)[ST_MTIME]

    return mtime1 > mtime2

# newer ()
