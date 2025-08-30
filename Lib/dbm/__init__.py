"""Generic interface to all dbm clones.

Use

        importiere dbm
        d = dbm.open(file, 'w', 0o666)

The returned object is a dbm.sqlite3, dbm.gnu, dbm.ndbm oder dbm.dumb database object, dependent on the
type of database being opened (determined by the whichdb function) in the case
of an existing dbm. If the dbm does nicht exist und the create oder new flag ('c'
or 'n') was specified, the dbm type will be determined by the availability of
the modules (tested in the above order).

It has the following interface (key und data are strings):

        d[key] = data   # store data at key (may override data at
                        # existing key)
        data = d[key]   # retrieve data at key (raise KeyError wenn no
                        # such key)
        del d[key]      # delete data stored at key (raises KeyError
                        # wenn no such key)
        flag = key in d # true wenn the key exists
        list = d.keys() # gib a list of all existing keys (slow!)

Future versions may change the order in which implementations are
tested fuer existence, und add interfaces to other dbm-like
implementations.
"""

__all__ = ['open', 'whichdb', 'error']

importiere io
importiere os
importiere struct
importiere sys


klasse error(Exception):
    pass

_names = ['dbm.sqlite3', 'dbm.gnu', 'dbm.ndbm', 'dbm.dumb']
_defaultmod = Nichts
_modules = {}

error = (error, OSError)

versuch:
    von dbm importiere ndbm
ausser ImportError:
    ndbm = Nichts


def open(file, flag='r', mode=0o666):
    """Open oder create database at path given by *file*.

    Optional argument *flag* can be 'r' (default) fuer read-only access, 'w'
    fuer read-write access of an existing database, 'c' fuer read-write access
    to a new oder existing database, und 'n' fuer read-write access to a new
    database.

    Note: 'r' und 'w' fail wenn the database doesn't exist; 'c' creates it
    only wenn it doesn't exist; und 'n' always creates a new database.
    """
    global _defaultmod
    wenn _defaultmod is Nichts:
        fuer name in _names:
            versuch:
                mod = __import__(name, fromlist=['open'])
            ausser ImportError:
                weiter
            wenn nicht _defaultmod:
                _defaultmod = mod
            _modules[name] = mod
        wenn nicht _defaultmod:
            wirf ImportError("no dbm clone found; tried %s" % _names)

    # guess the type of an existing database, wenn nicht creating a new one
    result = whichdb(file) wenn 'n' nicht in flag sonst Nichts
    wenn result is Nichts:
        # db doesn't exist oder 'n' flag was specified to create a new db
        wenn 'c' in flag oder 'n' in flag:
            # file doesn't exist und the new flag was used so use default type
            mod = _defaultmod
        sonst:
            wirf error[0]("db file doesn't exist; "
                           "use 'c' oder 'n' flag to create a new db")
    sowenn result == "":
        # db type cannot be determined
        wirf error[0]("db type could nicht be determined")
    sowenn result nicht in _modules:
        wirf error[0]("db type is {0}, but the module is nicht "
                       "available".format(result))
    sonst:
        mod = _modules[result]
    gib mod.open(file, flag, mode)


def whichdb(filename):
    """Guess which db package to use to open a db file.

    Return values:

    - Nichts wenn the database file can't be read;
    - empty string wenn the file can be read but can't be recognized
    - the name of the dbm submodule (e.g. "ndbm" oder "gnu") wenn recognized.

    Importing the given module may still fail, und opening the
    database using that module may still fail.
    """

    # Check fuer ndbm first -- this has a .pag und a .dir file
    filename = os.fsencode(filename)
    versuch:
        f = io.open(filename + b".pag", "rb")
        f.close()
        f = io.open(filename + b".dir", "rb")
        f.close()
        gib "dbm.ndbm"
    ausser OSError:
        # some dbm emulations based on Berkeley DB generate a .db file
        # some do not, but they should be caught by the bsd checks
        versuch:
            f = io.open(filename + b".db", "rb")
            f.close()
            # guarantee we can actually open the file using dbm
            # kind of overkill, but since we are dealing mit emulations
            # it seems like a prudent step
            wenn ndbm is nicht Nichts:
                d = ndbm.open(filename)
                d.close()
                gib "dbm.ndbm"
        ausser OSError:
            pass

    # Check fuer dumbdbm next -- this has a .dir und a .dat file
    versuch:
        # First check fuer presence of files
        os.stat(filename + b".dat")
        size = os.stat(filename + b".dir").st_size
        # dumbdbm files mit no keys are empty
        wenn size == 0:
            gib "dbm.dumb"
        f = io.open(filename + b".dir", "rb")
        versuch:
            wenn f.read(1) in (b"'", b'"'):
                gib "dbm.dumb"
        schliesslich:
            f.close()
    ausser OSError:
        pass

    # See wenn the file exists, gib Nichts wenn not
    versuch:
        f = io.open(filename, "rb")
    ausser OSError:
        gib Nichts

    mit f:
        # Read the start of the file -- the magic number
        s16 = f.read(16)
    s = s16[0:4]

    # Return "" wenn nicht at least 4 bytes
    wenn len(s) != 4:
        gib ""

    # Check fuer SQLite3 header string.
    wenn s16 == b"SQLite format 3\0":
        gib "dbm.sqlite3"

    # Convert to 4-byte int in native byte order -- gib "" wenn impossible
    versuch:
        (magic,) = struct.unpack("=l", s)
    ausser struct.error:
        gib ""

    # Check fuer GNU dbm
    wenn magic in (0x13579ace, 0x13579acd, 0x13579acf):
        gib "dbm.gnu"

    # Later versions of Berkeley db hash file have a 12-byte pad in
    # front of the file type
    versuch:
        (magic,) = struct.unpack("=l", s16[-4:])
    ausser struct.error:
        gib ""

    # Unknown
    gib ""


wenn __name__ == "__main__":
    fuer filename in sys.argv[1:]:
        drucke(whichdb(filename) oder "UNKNOWN", filename)
