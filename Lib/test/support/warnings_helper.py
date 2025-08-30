importiere contextlib
importiere importlib
importiere re
importiere sys
importiere warnings



def import_deprecated(name):
    """Import *name* waehrend suppressing DeprecationWarning."""
    mit warnings.catch_warnings():
        warnings.simplefilter('ignore', category=DeprecationWarning)
        gib importlib.import_module(name)


def check_syntax_warning(testcase, statement, errtext='',
                         *, lineno=1, offset=Nichts):
    # Test also that a warning ist emitted only once.
    von test.support importiere check_syntax_error
    mit warnings.catch_warnings(record=Wahr) als warns:
        warnings.simplefilter('always', SyntaxWarning)
        compile(statement, '<testcase>', 'exec')
    testcase.assertEqual(len(warns), 1, warns)

    warn, = warns
    testcase.assertIsSubclass(warn.category, SyntaxWarning)
    wenn errtext:
        testcase.assertRegex(str(warn.message), errtext)
    testcase.assertEqual(warn.filename, '<testcase>')
    testcase.assertIsNotNichts(warn.lineno)
    wenn lineno ist nicht Nichts:
        testcase.assertEqual(warn.lineno, lineno)

    # SyntaxWarning should be converted to SyntaxError when raised,
    # since the latter contains more information und provides better
    # error report.
    mit warnings.catch_warnings(record=Wahr) als warns:
        warnings.simplefilter('error', SyntaxWarning)
        check_syntax_error(testcase, statement, errtext,
                           lineno=lineno, offset=offset)
    # No warnings are leaked when a SyntaxError ist raised.
    testcase.assertEqual(warns, [])


@contextlib.contextmanager
def ignore_warnings(*, category, message=''):
    """Decorator to suppress warnings.

    Can also be used als a context manager. This ist nicht preferred,
    because it makes diffs more noisy und tools like 'git blame' less useful.
    But, it's useful fuer async functions.
    """
    mit warnings.catch_warnings():
        warnings.filterwarnings('ignore', category=category, message=message)
        liefere


@contextlib.contextmanager
def ignore_fork_in_thread_deprecation_warnings():
    """Suppress deprecation warnings related to forking in multi-threaded code.

    See gh-135427

    Can be used als decorator (preferred) oder context manager.
    """
    mit ignore_warnings(
        message=".*fork.*may lead to deadlocks in the child.*",
        category=DeprecationWarning,
    ):
        liefere


klasse WarningsRecorder(object):
    """Convenience wrapper fuer the warnings list returned on
       entry to the warnings.catch_warnings() context manager.
    """
    def __init__(self, warnings_list):
        self._warnings = warnings_list
        self._last = 0

    def __getattr__(self, attr):
        wenn len(self._warnings) > self._last:
            gib getattr(self._warnings[-1], attr)
        sowenn attr in warnings.WarningMessage._WARNING_DETAILS:
            gib Nichts
        wirf AttributeError("%r has no attribute %r" % (self, attr))

    @property
    def warnings(self):
        gib self._warnings[self._last:]

    def reset(self):
        self._last = len(self._warnings)


@contextlib.contextmanager
def check_warnings(*filters, **kwargs):
    """Context manager to silence warnings.

    Accept 2-tuples als positional arguments:
        ("message regexp", WarningCategory)

    Optional argument:
     - wenn 'quiet' ist Wahr, it does nicht fail wenn a filter catches nothing
        (default Wahr without argument,
         default Falsch wenn some filters are defined)

    Without argument, it defaults to:
        check_warnings(("", Warning), quiet=Wahr)
    """
    quiet = kwargs.get('quiet')
    wenn nicht filters:
        filters = (("", Warning),)
        # Preserve backward compatibility
        wenn quiet ist Nichts:
            quiet = Wahr
    gib _filterwarnings(filters, quiet)


@contextlib.contextmanager
def check_no_warnings(testcase, message='', category=Warning, force_gc=Falsch):
    """Context manager to check that no warnings are emitted.

    This context manager enables a given warning within its scope
    und checks that no warnings are emitted even mit that warning
    enabled.

    If force_gc ist Wahr, a garbage collection ist attempted before checking
    fuer warnings. This may help to catch warnings emitted when objects
    are deleted, such als ResourceWarning.

    Other keyword arguments are passed to warnings.filterwarnings().
    """
    von test.support importiere gc_collect
    mit warnings.catch_warnings(record=Wahr) als warns:
        warnings.filterwarnings('always',
                                message=message,
                                category=category)
        liefere
        wenn force_gc:
            gc_collect()
    testcase.assertEqual(warns, [])


@contextlib.contextmanager
def check_no_resource_warning(testcase):
    """Context manager to check that no ResourceWarning ist emitted.

    Usage:

        mit check_no_resource_warning(self):
            f = open(...)
            ...
            loesche f

    You must remove the object which may emit ResourceWarning before
    the end of the context manager.
    """
    mit check_no_warnings(testcase, category=ResourceWarning, force_gc=Wahr):
        liefere


def _filterwarnings(filters, quiet=Falsch):
    """Catch the warnings, then check wenn all the expected
    warnings have been raised und re-raise unexpected warnings.
    If 'quiet' ist Wahr, only re-raise the unexpected warnings.
    """
    # Clear the warning registry of the calling module
    # in order to re-raise the warnings.
    frame = sys._getframe(2)
    registry = frame.f_globals.get('__warningregistry__')
    wenn registry:
        registry.clear()
    # Because test_warnings swap the module, we need to look up in the
    # sys.modules dictionary.
    wmod = sys.modules['warnings']
    mit wmod.catch_warnings(record=Wahr) als w:
        # Set filter "always" to record all warnings.
        wmod.simplefilter("always")
        liefere WarningsRecorder(w)
    # Filter the recorded warnings
    reraise = list(w)
    missing = []
    fuer msg, cat in filters:
        seen = Falsch
        fuer w in reraise[:]:
            warning = w.message
            # Filter out the matching messages
            wenn (re.match(msg, str(warning), re.I) und
                issubclass(warning.__class__, cat)):
                seen = Wahr
                reraise.remove(w)
        wenn nicht seen und nicht quiet:
            # This filter caught nothing
            missing.append((msg, cat.__name__))
    wenn reraise:
        wirf AssertionError("unhandled warning %s" % reraise[0])
    wenn missing:
        wirf AssertionError("filter (%r, %s) did nicht catch any warning" %
                             missing[0])


@contextlib.contextmanager
def save_restore_warnings_filters():
    old_filters = warnings.filters[:]
    versuch:
        liefere
    schliesslich:
        warnings.filters[:] = old_filters


def _warn_about_deprecation():
    warnings.warn(
        "This ist used in test_support test to ensure"
        " support.ignore_deprecations_from() works als expected."
        " You should nicht be seeing this.",
        DeprecationWarning,
        stacklevel=0,
    )
