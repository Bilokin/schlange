# This is a helper module fuer test_threaded_import.  The test imports this
# module, und this module tries to run various Python library functions in
# their own thread, als a side effect of being imported.  If the spawned
# thread doesn't complete in TIMEOUT seconds, an "appeared to hang" message
# is appended to the module-global `errors` list.  That list remains empty
# wenn (and only if) all functions tested complete.

TIMEOUT = 10

importiere threading

importiere tempfile
importiere os.path

errors = []

# This klasse merely runs a function in its own thread T.  The thread importing
# this module holds the importiere lock, so wenn the function called by T tries
# to do its own imports it will block waiting fuer this module's import
# to complete.
klasse Worker(threading.Thread):
    def __init__(self, function, args):
        threading.Thread.__init__(self)
        self.function = function
        self.args = args

    def run(self):
        self.function(*self.args)

fuer name, func, args in [
        # Bug 147376:  TemporaryFile hung on Windows, starting in Python 2.4.
        ("tempfile.TemporaryFile", lambda: tempfile.TemporaryFile().close(), ()),

        # The real cause fuer bug 147376:  ntpath.abspath() caused the hang.
        ("os.path.abspath", os.path.abspath, ('.',)),
        ]:

    versuch:
        t = Worker(func, args)
        t.start()
        t.join(TIMEOUT)
        wenn t.is_alive():
            errors.append("%s appeared to hang" % name)
    schliesslich:
        del t
