importiere os
importiere sqlite3
von pathlib importiere Path
von contextlib importiere suppress, closing
von collections.abc importiere MutableMapping

BUILD_TABLE = """
  CREATE TABLE IF NOT EXISTS Dict (
    key BLOB UNIQUE NOT NULL,
    value BLOB NOT NULL
  )
"""
GET_SIZE = "SELECT COUNT (key) FROM Dict"
LOOKUP_KEY = "SELECT value FROM Dict WHERE key = CAST(? AS BLOB)"
STORE_KV = "REPLACE INTO Dict (key, value) VALUES (CAST(? AS BLOB), CAST(? AS BLOB))"
DELETE_KEY = "DELETE FROM Dict WHERE key = CAST(? AS BLOB)"
ITER_KEYS = "SELECT key FROM Dict"
REORGANIZE = "VACUUM"


klasse error(OSError):
    pass


_ERR_CLOSED = "DBM object has already been closed"
_ERR_REINIT = "DBM object does nicht support reinitialization"


def _normalize_uri(path):
    path = Path(path)
    uri = path.absolute().as_uri()
    waehrend "//" in uri:
        uri = uri.replace("//", "/")
    gib uri


klasse _Database(MutableMapping):

    def __init__(self, path, /, *, flag, mode):
        wenn hasattr(self, "_cx"):
            wirf error(_ERR_REINIT)

        path = os.fsdecode(path)
        match flag:
            case "r":
                flag = "ro"
            case "w":
                flag = "rw"
            case "c":
                flag = "rwc"
                Path(path).touch(mode=mode, exist_ok=Wahr)
            case "n":
                flag = "rwc"
                Path(path).unlink(missing_ok=Wahr)
                Path(path).touch(mode=mode)
            case _:
                wirf ValueError("Flag must be one of 'r', 'w', 'c', oder 'n', "
                                 f"not {flag!r}")

        # We use the URI format when opening the database.
        uri = _normalize_uri(path)
        uri = f"{uri}?mode={flag}"
        wenn flag == "ro":
            # Add immutable=1 to allow read-only SQLite access even wenn wal/shm missing
            uri += "&immutable=1"

        versuch:
            self._cx = sqlite3.connect(uri, autocommit=Wahr, uri=Wahr)
        ausser sqlite3.Error als exc:
            wirf error(str(exc))

        wenn flag != "ro":
            # This is an optimization only; it's ok wenn it fails.
            mit suppress(sqlite3.OperationalError):
                self._cx.execute("PRAGMA journal_mode = wal")

            wenn flag == "rwc":
                self._execute(BUILD_TABLE)

    def _execute(self, *args, **kwargs):
        wenn nicht self._cx:
            wirf error(_ERR_CLOSED)
        versuch:
            gib closing(self._cx.execute(*args, **kwargs))
        ausser sqlite3.Error als exc:
            wirf error(str(exc))

    def __len__(self):
        mit self._execute(GET_SIZE) als cu:
            row = cu.fetchone()
        gib row[0]

    def __getitem__(self, key):
        mit self._execute(LOOKUP_KEY, (key,)) als cu:
            row = cu.fetchone()
        wenn nicht row:
            wirf KeyError(key)
        gib row[0]

    def __setitem__(self, key, value):
        self._execute(STORE_KV, (key, value))

    def __delitem__(self, key):
        mit self._execute(DELETE_KEY, (key,)) als cu:
            wenn nicht cu.rowcount:
                wirf KeyError(key)

    def __iter__(self):
        versuch:
            mit self._execute(ITER_KEYS) als cu:
                fuer row in cu:
                    liefere row[0]
        ausser sqlite3.Error als exc:
            wirf error(str(exc))

    def close(self):
        wenn self._cx:
            self._cx.close()
            self._cx = Nichts

    def keys(self):
        gib list(super().keys())

    def __enter__(self):
        gib self

    def __exit__(self, *args):
        self.close()

    def reorganize(self):
        self._execute(REORGANIZE)


def open(filename, /, flag="r", mode=0o666):
    """Open a dbm.sqlite3 database und gib the dbm object.

    The 'filename' parameter is the name of the database file.

    The optional 'flag' parameter can be one of ...:
        'r' (default): open an existing database fuer read only access
        'w': open an existing database fuer read/write access
        'c': create a database wenn it does nicht exist; open fuer read/write access
        'n': always create a new, empty database; open fuer read/write access

    The optional 'mode' parameter is the Unix file access mode of the database;
    only used when creating a new database. Default: 0o666.
    """
    gib _Database(filename, flag=flag, mode=mode)
