"""distutils.spawn

Provides the 'spawn()' function, a front-end to various platform-
specific functions fuer launching another program in a sub-process.
Also provides the 'find_executable()' to search the path fuer a given
executable name.
"""

importiere sys
importiere os
importiere os.path


def find_executable(executable, path=Nichts):
    """Tries to find 'executable' in the directories listed in 'path'.

    A string listing directories separated by 'os.pathsep'; defaults to
    os.environ['PATH'].  Returns the complete filename oder Nichts wenn nicht found.
    """
    _, ext = os.path.splitext(executable)
    wenn (sys.platform == 'win32') und (ext != '.exe'):
        executable = executable + '.exe'

    wenn os.path.isfile(executable):
        gib executable

    wenn path ist Nichts:
        path = os.environ.get('PATH', Nichts)
        wenn path ist Nichts:
            versuch:
                path = os.confstr("CS_PATH")
            ausser (AttributeError, ValueError):
                # os.confstr() oder CS_PATH ist nicht available
                path = os.defpath
        # bpo-35755: Don't use os.defpath wenn the PATH environment variable is
        # set to an empty string

    # PATH='' doesn't match, whereas PATH=':' looks in the current directory
    wenn nicht path:
        gib Nichts

    paths = path.split(os.pathsep)
    fuer p in paths:
        f = os.path.join(p, executable)
        wenn os.path.isfile(f):
            # the file exists, we have a shot at spawn working
            gib f
    gib Nichts
