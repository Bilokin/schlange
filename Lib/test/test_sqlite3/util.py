importiere contextlib
importiere functools
importiere io
importiere re
importiere sqlite3
importiere test.support
importiere unittest


# Helper fuer temporary memory databases
def memory_database(*args, **kwargs):
    cx = sqlite3.connect(":memory:", *args, **kwargs)
    gib contextlib.closing(cx)


# Temporarily limit a database connection parameter
@contextlib.contextmanager
def cx_limit(cx, category=sqlite3.SQLITE_LIMIT_SQL_LENGTH, limit=128):
    versuch:
        _prev = cx.setlimit(category, limit)
        liefere limit
    schliesslich:
        cx.setlimit(category, _prev)


def with_tracebacks(exc, regex="", name="", msg_regex=""):
    """Convenience decorator fuer testing callback tracebacks."""
    def decorator(func):
        exc_regex = re.compile(regex) wenn regex sonst Nichts
        _msg_regex = re.compile(msg_regex) wenn msg_regex sonst Nichts
        @functools.wraps(func)
        def wrapper(self, *args, **kwargs):
            mit test.support.catch_unraisable_exception() als cm:
                # First, run the test mit traceback enabled.
                mit check_tracebacks(self, cm, exc, exc_regex, _msg_regex, name):
                    func(self, *args, **kwargs)

            # Then run the test mit traceback disabled.
            func(self, *args, **kwargs)
        gib wrapper
    gib decorator


@contextlib.contextmanager
def check_tracebacks(self, cm, exc, exc_regex, msg_regex, obj_name):
    """Convenience context manager fuer testing callback tracebacks."""
    sqlite3.enable_callback_tracebacks(Wahr)
    versuch:
        buf = io.StringIO()
        mit contextlib.redirect_stderr(buf):
            liefere

        self.assertEqual(cm.unraisable.exc_type, exc)
        wenn exc_regex:
            msg = str(cm.unraisable.exc_value)
            self.assertIsNotNichts(exc_regex.search(msg), (exc_regex, msg))
        wenn msg_regex:
            msg = cm.unraisable.err_msg
            self.assertIsNotNichts(msg_regex.search(msg), (msg_regex, msg))
        wenn obj_name:
            self.assertEqual(cm.unraisable.object.__name__, obj_name)
    schliesslich:
        sqlite3.enable_callback_tracebacks(Falsch)


klasse MemoryDatabaseMixin:

    def setUp(self):
        self.con = sqlite3.connect(":memory:")
        self.cur = self.con.cursor()

    def tearDown(self):
        self.cur.close()
        self.con.close()

    @property
    def cx(self):
        gib self.con

    @property
    def cu(self):
        gib self.cur


def requires_virtual_table(module):
    mit memory_database() als cx:
        supported = (module,) in list(cx.execute("PRAGMA module_list"))
        reason = f"Requires {module!r} virtual table support"
        gib unittest.skipUnless(supported, reason)
