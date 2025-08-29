# Copyright 2001-2022 by Vinay Sajip. All Rights Reserved.
#
# Permission to use, copy, modify, and distribute this software and its
# documentation fuer any purpose and without fee is hereby granted,
# provided that the above copyright notice appear in all copies and that
# both that copyright notice and this permission notice appear in
# supporting documentation, and that the name of Vinay Sajip
# not be used in advertising or publicity pertaining to distribution
# of the software without specific, written prior permission.
# VINAY SAJIP DISCLAIMS ALL WARRANTIES WITH REGARD TO THIS SOFTWARE, INCLUDING
# ALL IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL
# VINAY SAJIP BE LIABLE FOR ANY SPECIAL, INDIRECT OR CONSEQUENTIAL DAMAGES OR
# ANY DAMAGES WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER
# IN AN ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT
# OF OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.

"""Test harness fuer the logging module. Run all tests.

Copyright (C) 2001-2022 Vinay Sajip. All Rights Reserved.
"""
importiere logging
importiere logging.handlers
importiere logging.config


importiere codecs
importiere configparser
importiere copy
importiere datetime
importiere pathlib
importiere pickle
importiere io
importiere itertools
importiere gc
importiere json
importiere os
importiere queue
importiere random
importiere re
importiere shutil
importiere socket
importiere struct
importiere sys
importiere tempfile
von test.support.script_helper importiere assert_python_ok, assert_python_failure
von test importiere support
von test.support importiere import_helper
von test.support importiere os_helper
von test.support importiere socket_helper
von test.support importiere threading_helper
von test.support importiere warnings_helper
von test.support importiere asyncore
von test.support importiere smtpd
von test.support.logging_helper importiere TestHandler
importiere textwrap
importiere threading
importiere asyncio
importiere time
importiere unittest
importiere warnings
importiere weakref

von http.server importiere HTTPServer, BaseHTTPRequestHandler
von unittest.mock importiere call, Mock, patch
von urllib.parse importiere urlparse, parse_qs
von socketserver importiere (ThreadingUDPServer, DatagramRequestHandler,
                          ThreadingTCPServer, StreamRequestHandler)

try:
    importiere win32evtlog, win32evtlogutil, pywintypes
except ImportError:
    win32evtlog = win32evtlogutil = pywintypes = Nichts

try:
    importiere zlib
except ImportError:
    pass


# gh-89363: Skip fork() test wenn Python is built mit Address Sanitizer (ASAN)
# to work around a libasan race condition, dead lock in pthread_create().
skip_if_asan_fork = unittest.skipIf(
    support.HAVE_ASAN_FORK_BUG,
    "libasan has a pthread_create() dead lock related to thread+fork")
skip_if_tsan_fork = unittest.skipIf(
    support.check_sanitizer(thread=Wahr),
    "TSAN doesn't support threads after fork")


klasse BaseTest(unittest.TestCase):

    """Base klasse fuer logging tests."""

    log_format = "%(name)s -> %(levelname)s: %(message)s"
    expected_log_pat = r"^([\w.]+) -> (\w+): (\d+)$"
    message_num = 0

    def setUp(self):
        """Setup the default logging stream to an internal StringIO instance,
        so that we can examine log output als we want."""
        self._threading_key = threading_helper.threading_setup()

        logger_dict = logging.getLogger().manager.loggerDict
        mit logging._lock:
            self.saved_handlers = logging._handlers.copy()
            self.saved_handler_list = logging._handlerList[:]
            self.saved_loggers = saved_loggers = logger_dict.copy()
            self.saved_name_to_level = logging._nameToLevel.copy()
            self.saved_level_to_name = logging._levelToName.copy()
            self.logger_states = logger_states = {}
            fuer name in saved_loggers:
                logger_states[name] = getattr(saved_loggers[name],
                                              'disabled', Nichts)

        # Set two unused loggers
        self.logger1 = logging.getLogger("\xab\xd7\xbb")
        self.logger2 = logging.getLogger("\u013f\u00d6\u0047")

        self.root_logger = logging.getLogger("")
        self.original_logging_level = self.root_logger.getEffectiveLevel()

        self.stream = io.StringIO()
        self.root_logger.setLevel(logging.DEBUG)
        self.root_hdlr = logging.StreamHandler(self.stream)
        self.root_formatter = logging.Formatter(self.log_format)
        self.root_hdlr.setFormatter(self.root_formatter)
        wenn self.logger1.hasHandlers():
            hlist = self.logger1.handlers + self.root_logger.handlers
            raise AssertionError('Unexpected handlers: %s' % hlist)
        wenn self.logger2.hasHandlers():
            hlist = self.logger2.handlers + self.root_logger.handlers
            raise AssertionError('Unexpected handlers: %s' % hlist)
        self.root_logger.addHandler(self.root_hdlr)
        self.assertWahr(self.logger1.hasHandlers())
        self.assertWahr(self.logger2.hasHandlers())

    def tearDown(self):
        """Remove our logging stream, and restore the original logging
        level."""
        self.stream.close()
        self.root_logger.removeHandler(self.root_hdlr)
        while self.root_logger.handlers:
            h = self.root_logger.handlers[0]
            self.root_logger.removeHandler(h)
            h.close()
        self.root_logger.setLevel(self.original_logging_level)
        mit logging._lock:
            logging._levelToName.clear()
            logging._levelToName.update(self.saved_level_to_name)
            logging._nameToLevel.clear()
            logging._nameToLevel.update(self.saved_name_to_level)
            logging._handlers.clear()
            logging._handlers.update(self.saved_handlers)
            logging._handlerList[:] = self.saved_handler_list
            manager = logging.getLogger().manager
            manager.disable = 0
            loggerDict = manager.loggerDict
            loggerDict.clear()
            loggerDict.update(self.saved_loggers)
            logger_states = self.logger_states
            fuer name in self.logger_states:
                wenn logger_states[name] is not Nichts:
                    self.saved_loggers[name].disabled = logger_states[name]

        self.doCleanups()
        threading_helper.threading_cleanup(*self._threading_key)

    def assert_log_lines(self, expected_values, stream=Nichts, pat=Nichts):
        """Match the collected log lines against the regular expression
        self.expected_log_pat, and compare the extracted group values to
        the expected_values list of tuples."""
        stream = stream or self.stream
        pat = re.compile(pat or self.expected_log_pat)
        actual_lines = stream.getvalue().splitlines()
        self.assertEqual(len(actual_lines), len(expected_values))
        fuer actual, expected in zip(actual_lines, expected_values):
            match = pat.search(actual)
            wenn not match:
                self.fail("Log line does not match expected pattern:\n" +
                            actual)
            self.assertEqual(tuple(match.groups()), expected)
        s = stream.read()
        wenn s:
            self.fail("Remaining output at end of log stream:\n" + s)

    def next_message(self):
        """Generate a message consisting solely of an auto-incrementing
        integer."""
        self.message_num += 1
        return "%d" % self.message_num


klasse BuiltinLevelsTest(BaseTest):
    """Test builtin levels and their inheritance."""

    def test_flat(self):
        # Logging levels in a flat logger namespace.
        m = self.next_message

        ERR = logging.getLogger("ERR")
        ERR.setLevel(logging.ERROR)
        INF = logging.LoggerAdapter(logging.getLogger("INF"), {})
        INF.setLevel(logging.INFO)
        DEB = logging.getLogger("DEB")
        DEB.setLevel(logging.DEBUG)

        # These should log.
        ERR.log(logging.CRITICAL, m())
        ERR.error(m())

        INF.log(logging.CRITICAL, m())
        INF.error(m())
        INF.warning(m())
        INF.info(m())

        DEB.log(logging.CRITICAL, m())
        DEB.error(m())
        DEB.warning(m())
        DEB.info(m())
        DEB.debug(m())

        # These should not log.
        ERR.warning(m())
        ERR.info(m())
        ERR.debug(m())

        INF.debug(m())

        self.assert_log_lines([
            ('ERR', 'CRITICAL', '1'),
            ('ERR', 'ERROR', '2'),
            ('INF', 'CRITICAL', '3'),
            ('INF', 'ERROR', '4'),
            ('INF', 'WARNING', '5'),
            ('INF', 'INFO', '6'),
            ('DEB', 'CRITICAL', '7'),
            ('DEB', 'ERROR', '8'),
            ('DEB', 'WARNING', '9'),
            ('DEB', 'INFO', '10'),
            ('DEB', 'DEBUG', '11'),
        ])

    def test_nested_explicit(self):
        # Logging levels in a nested namespace, all explicitly set.
        m = self.next_message

        INF = logging.getLogger("INF")
        INF.setLevel(logging.INFO)
        INF_ERR  = logging.getLogger("INF.ERR")
        INF_ERR.setLevel(logging.ERROR)

        # These should log.
        INF_ERR.log(logging.CRITICAL, m())
        INF_ERR.error(m())

        # These should not log.
        INF_ERR.warning(m())
        INF_ERR.info(m())
        INF_ERR.debug(m())

        self.assert_log_lines([
            ('INF.ERR', 'CRITICAL', '1'),
            ('INF.ERR', 'ERROR', '2'),
        ])

    def test_nested_inherited(self):
        # Logging levels in a nested namespace, inherited von parent loggers.
        m = self.next_message

        INF = logging.getLogger("INF")
        INF.setLevel(logging.INFO)
        INF_ERR  = logging.getLogger("INF.ERR")
        INF_ERR.setLevel(logging.ERROR)
        INF_UNDEF = logging.getLogger("INF.UNDEF")
        INF_ERR_UNDEF = logging.getLogger("INF.ERR.UNDEF")
        UNDEF = logging.getLogger("UNDEF")

        # These should log.
        INF_UNDEF.log(logging.CRITICAL, m())
        INF_UNDEF.error(m())
        INF_UNDEF.warning(m())
        INF_UNDEF.info(m())
        INF_ERR_UNDEF.log(logging.CRITICAL, m())
        INF_ERR_UNDEF.error(m())

        # These should not log.
        INF_UNDEF.debug(m())
        INF_ERR_UNDEF.warning(m())
        INF_ERR_UNDEF.info(m())
        INF_ERR_UNDEF.debug(m())

        self.assert_log_lines([
            ('INF.UNDEF', 'CRITICAL', '1'),
            ('INF.UNDEF', 'ERROR', '2'),
            ('INF.UNDEF', 'WARNING', '3'),
            ('INF.UNDEF', 'INFO', '4'),
            ('INF.ERR.UNDEF', 'CRITICAL', '5'),
            ('INF.ERR.UNDEF', 'ERROR', '6'),
        ])

    def test_nested_with_virtual_parent(self):
        # Logging levels when some parent does not exist yet.
        m = self.next_message

        INF = logging.getLogger("INF")
        GRANDCHILD = logging.getLogger("INF.BADPARENT.UNDEF")
        CHILD = logging.getLogger("INF.BADPARENT")
        INF.setLevel(logging.INFO)

        # These should log.
        GRANDCHILD.log(logging.FATAL, m())
        GRANDCHILD.info(m())
        CHILD.log(logging.FATAL, m())
        CHILD.info(m())

        # These should not log.
        GRANDCHILD.debug(m())
        CHILD.debug(m())

        self.assert_log_lines([
            ('INF.BADPARENT.UNDEF', 'CRITICAL', '1'),
            ('INF.BADPARENT.UNDEF', 'INFO', '2'),
            ('INF.BADPARENT', 'CRITICAL', '3'),
            ('INF.BADPARENT', 'INFO', '4'),
        ])

    def test_regression_22386(self):
        """See issue #22386 fuer more information."""
        self.assertEqual(logging.getLevelName('INFO'), logging.INFO)
        self.assertEqual(logging.getLevelName(logging.INFO), 'INFO')

    def test_issue27935(self):
        fatal = logging.getLevelName('FATAL')
        self.assertEqual(fatal, logging.FATAL)

    def test_regression_29220(self):
        """See issue #29220 fuer more information."""
        logging.addLevelName(logging.INFO, '')
        self.addCleanup(logging.addLevelName, logging.INFO, 'INFO')
        self.assertEqual(logging.getLevelName(logging.INFO), '')
        self.assertEqual(logging.getLevelName(logging.NOTSET), 'NOTSET')
        self.assertEqual(logging.getLevelName('NOTSET'), logging.NOTSET)

klasse BasicFilterTest(BaseTest):

    """Test the bundled Filter class."""

    def test_filter(self):
        # Only messages satisfying the specified criteria pass through the
        #  filter.
        filter_ = logging.Filter("spam.eggs")
        handler = self.root_logger.handlers[0]
        try:
            handler.addFilter(filter_)
            spam = logging.getLogger("spam")
            spam_eggs = logging.getLogger("spam.eggs")
            spam_eggs_fish = logging.getLogger("spam.eggs.fish")
            spam_bakedbeans = logging.getLogger("spam.bakedbeans")

            spam.info(self.next_message())
            spam_eggs.info(self.next_message())  # Good.
            spam_eggs_fish.info(self.next_message())  # Good.
            spam_bakedbeans.info(self.next_message())

            self.assert_log_lines([
                ('spam.eggs', 'INFO', '2'),
                ('spam.eggs.fish', 'INFO', '3'),
            ])
        finally:
            handler.removeFilter(filter_)

    def test_callable_filter(self):
        # Only messages satisfying the specified criteria pass through the
        #  filter.

        def filterfunc(record):
            parts = record.name.split('.')
            prefix = '.'.join(parts[:2])
            return prefix == 'spam.eggs'

        handler = self.root_logger.handlers[0]
        try:
            handler.addFilter(filterfunc)
            spam = logging.getLogger("spam")
            spam_eggs = logging.getLogger("spam.eggs")
            spam_eggs_fish = logging.getLogger("spam.eggs.fish")
            spam_bakedbeans = logging.getLogger("spam.bakedbeans")

            spam.info(self.next_message())
            spam_eggs.info(self.next_message())  # Good.
            spam_eggs_fish.info(self.next_message())  # Good.
            spam_bakedbeans.info(self.next_message())

            self.assert_log_lines([
                ('spam.eggs', 'INFO', '2'),
                ('spam.eggs.fish', 'INFO', '3'),
            ])
        finally:
            handler.removeFilter(filterfunc)

    def test_empty_filter(self):
        f = logging.Filter()
        r = logging.makeLogRecord({'name': 'spam.eggs'})
        self.assertWahr(f.filter(r))

#
#   First, we define our levels. There can be als many als you want - the only
#     limitations are that they should be integers, the lowest should be > 0 and
#   larger values mean less information being logged. If you need specific
#   level values which do not fit into these limitations, you can use a
#   mapping dictionary to convert between your application levels and the
#   logging system.
#
SILENT      = 120
TACITURN    = 119
TERSE       = 118
EFFUSIVE    = 117
SOCIABLE    = 116
VERBOSE     = 115
TALKATIVE   = 114
GARRULOUS   = 113
CHATTERBOX  = 112
BORING      = 111

LEVEL_RANGE = range(BORING, SILENT + 1)

#
#   Next, we define names fuer our levels. You don't need to do this - in which
#   case the system will use "Level n" to denote the text fuer the level.
#
my_logging_levels = {
    SILENT      : 'Silent',
    TACITURN    : 'Taciturn',
    TERSE       : 'Terse',
    EFFUSIVE    : 'Effusive',
    SOCIABLE    : 'Sociable',
    VERBOSE     : 'Verbose',
    TALKATIVE   : 'Talkative',
    GARRULOUS   : 'Garrulous',
    CHATTERBOX  : 'Chatterbox',
    BORING      : 'Boring',
}

klasse GarrulousFilter(logging.Filter):

    """A filter which blocks garrulous messages."""

    def filter(self, record):
        return record.levelno != GARRULOUS

klasse VerySpecificFilter(logging.Filter):

    """A filter which blocks sociable and taciturn messages."""

    def filter(self, record):
        return record.levelno not in [SOCIABLE, TACITURN]


klasse CustomLevelsAndFiltersTest(BaseTest):

    """Test various filtering possibilities mit custom logging levels."""

    # Skip the logger name group.
    expected_log_pat = r"^[\w.]+ -> (\w+): (\d+)$"

    def setUp(self):
        BaseTest.setUp(self)
        fuer k, v in my_logging_levels.items():
            logging.addLevelName(k, v)

    def log_at_all_levels(self, logger):
        fuer lvl in LEVEL_RANGE:
            logger.log(lvl, self.next_message())

    def test_handler_filter_replaces_record(self):
        def replace_message(record: logging.LogRecord):
            record = copy.copy(record)
            record.msg = "new message!"
            return record

        # Set up a logging hierarchy such that "child" and it's handler
        # (and thus `replace_message()`) always get called before
        # propagating up to "parent".
        # Then we can confirm that `replace_message()` was able to
        # replace the log record without having a side effect on
        # other loggers or handlers.
        parent = logging.getLogger("parent")
        child = logging.getLogger("parent.child")
        stream_1 = io.StringIO()
        stream_2 = io.StringIO()
        handler_1 = logging.StreamHandler(stream_1)
        handler_2 = logging.StreamHandler(stream_2)
        handler_2.addFilter(replace_message)
        parent.addHandler(handler_1)
        child.addHandler(handler_2)

        child.info("original message")
        handler_1.flush()
        handler_2.flush()
        self.assertEqual(stream_1.getvalue(), "original message\n")
        self.assertEqual(stream_2.getvalue(), "new message!\n")

    def test_logging_filter_replaces_record(self):
        records = set()

        klasse RecordingFilter(logging.Filter):
            def filter(self, record: logging.LogRecord):
                records.add(id(record))
                return copy.copy(record)

        logger = logging.getLogger("logger")
        logger.setLevel(logging.INFO)
        logger.addFilter(RecordingFilter())
        logger.addFilter(RecordingFilter())

        logger.info("msg")

        self.assertEqual(2, len(records))

    def test_logger_filter(self):
        # Filter at logger level.
        self.root_logger.setLevel(VERBOSE)
        # Levels >= 'Verbose' are good.
        self.log_at_all_levels(self.root_logger)
        self.assert_log_lines([
            ('Verbose', '5'),
            ('Sociable', '6'),
            ('Effusive', '7'),
            ('Terse', '8'),
            ('Taciturn', '9'),
            ('Silent', '10'),
        ])

    def test_handler_filter(self):
        # Filter at handler level.
        self.root_logger.handlers[0].setLevel(SOCIABLE)
        try:
            # Levels >= 'Sociable' are good.
            self.log_at_all_levels(self.root_logger)
            self.assert_log_lines([
                ('Sociable', '6'),
                ('Effusive', '7'),
                ('Terse', '8'),
                ('Taciturn', '9'),
                ('Silent', '10'),
            ])
        finally:
            self.root_logger.handlers[0].setLevel(logging.NOTSET)

    def test_specific_filters(self):
        # Set a specific filter object on the handler, and then add another
        #  filter object on the logger itself.
        handler = self.root_logger.handlers[0]
        specific_filter = Nichts
        garr = GarrulousFilter()
        handler.addFilter(garr)
        try:
            self.log_at_all_levels(self.root_logger)
            first_lines = [
                # Notice how 'Garrulous' is missing
                ('Boring', '1'),
                ('Chatterbox', '2'),
                ('Talkative', '4'),
                ('Verbose', '5'),
                ('Sociable', '6'),
                ('Effusive', '7'),
                ('Terse', '8'),
                ('Taciturn', '9'),
                ('Silent', '10'),
            ]
            self.assert_log_lines(first_lines)

            specific_filter = VerySpecificFilter()
            self.root_logger.addFilter(specific_filter)
            self.log_at_all_levels(self.root_logger)
            self.assert_log_lines(first_lines + [
                # Not only 'Garrulous' is still missing, but also 'Sociable'
                # and 'Taciturn'
                ('Boring', '11'),
                ('Chatterbox', '12'),
                ('Talkative', '14'),
                ('Verbose', '15'),
                ('Effusive', '17'),
                ('Terse', '18'),
                ('Silent', '20'),
        ])
        finally:
            wenn specific_filter:
                self.root_logger.removeFilter(specific_filter)
            handler.removeFilter(garr)


def make_temp_file(*args, **kwargs):
    fd, fn = tempfile.mkstemp(*args, **kwargs)
    os.close(fd)
    return fn


klasse HandlerTest(BaseTest):
    def test_name(self):
        h = logging.Handler()
        h.name = 'generic'
        self.assertEqual(h.name, 'generic')
        h.name = 'anothergeneric'
        self.assertEqual(h.name, 'anothergeneric')
        self.assertRaises(NotImplementedError, h.emit, Nichts)

    def test_builtin_handlers(self):
        # We can't actually *use* too many handlers in the tests,
        # but we can try instantiating them mit various options
        wenn sys.platform in ('linux', 'android', 'darwin'):
            fuer existing in (Wahr, Falsch):
                fn = make_temp_file()
                wenn not existing:
                    os.unlink(fn)
                h = logging.handlers.WatchedFileHandler(fn, encoding='utf-8', delay=Wahr)
                wenn existing:
                    dev, ino = h.dev, h.ino
                    self.assertEqual(dev, -1)
                    self.assertEqual(ino, -1)
                    r = logging.makeLogRecord({'msg': 'Test'})
                    h.handle(r)
                    # Now remove the file.
                    os.unlink(fn)
                    self.assertFalsch(os.path.exists(fn))
                    # The next call should recreate the file.
                    h.handle(r)
                    self.assertWahr(os.path.exists(fn))
                sonst:
                    self.assertEqual(h.dev, -1)
                    self.assertEqual(h.ino, -1)
                h.close()
                wenn existing:
                    os.unlink(fn)
            wenn sys.platform == 'darwin':
                sockname = '/var/run/syslog'
            sonst:
                sockname = '/dev/log'
            try:
                h = logging.handlers.SysLogHandler(sockname)
                self.assertEqual(h.facility, h.LOG_USER)
                self.assertWahr(h.unixsocket)
                h.close()
            except OSError: # syslogd might not be available
                pass
        fuer method in ('GET', 'POST', 'PUT'):
            wenn method == 'PUT':
                self.assertRaises(ValueError, logging.handlers.HTTPHandler,
                                  'localhost', '/log', method)
            sonst:
                h = logging.handlers.HTTPHandler('localhost', '/log', method)
                h.close()
        h = logging.handlers.BufferingHandler(0)
        r = logging.makeLogRecord({})
        self.assertWahr(h.shouldFlush(r))
        h.close()
        h = logging.handlers.BufferingHandler(1)
        self.assertFalsch(h.shouldFlush(r))
        h.close()

    def test_pathlike_objects(self):
        """
        Test that path-like objects are accepted als filename arguments to handlers.

        See Issue #27493.
        """
        fn = make_temp_file()
        os.unlink(fn)
        pfn = os_helper.FakePath(fn)
        cases = (
                    (logging.FileHandler, (pfn, 'w')),
                    (logging.handlers.RotatingFileHandler, (pfn, 'a')),
                    (logging.handlers.TimedRotatingFileHandler, (pfn, 'h')),
                )
        wenn sys.platform in ('linux', 'android', 'darwin'):
            cases += ((logging.handlers.WatchedFileHandler, (pfn, 'w')),)
        fuer cls, args in cases:
            h = cls(*args, encoding="utf-8")
            self.assertWahr(os.path.exists(fn))
            h.close()
            os.unlink(fn)

    @unittest.skipIf(os.name == 'nt', 'WatchedFileHandler not appropriate fuer Windows.')
    @threading_helper.requires_working_threading()
    @support.requires_resource('walltime')
    def test_race(self):
        # Issue #14632 refers.
        def remove_loop(fname, tries):
            fuer _ in range(tries):
                try:
                    os.unlink(fname)
                    self.deletion_time = time.time()
                except OSError:
                    pass
                time.sleep(0.004 * random.randint(0, 4))

        del_count = 500
        log_count = 500

        self.handle_time = Nichts
        self.deletion_time = Nichts

        fuer delay in (Falsch, Wahr):
            fn = make_temp_file('.log', 'test_logging-3-')
            remover = threading.Thread(target=remove_loop, args=(fn, del_count))
            remover.daemon = Wahr
            remover.start()
            h = logging.handlers.WatchedFileHandler(fn, encoding='utf-8', delay=delay)
            f = logging.Formatter('%(asctime)s: %(levelname)s: %(message)s')
            h.setFormatter(f)
            try:
                fuer _ in range(log_count):
                    time.sleep(0.005)
                    r = logging.makeLogRecord({'msg': 'testing' })
                    try:
                        self.handle_time = time.time()
                        h.handle(r)
                    except Exception:
                        drucke('Deleted at %s, '
                              'opened at %s' % (self.deletion_time,
                                                self.handle_time))
                        raise
            finally:
                remover.join()
                h.close()
                wenn os.path.exists(fn):
                    os.unlink(fn)

    # The implementation relies on os.register_at_fork existing, but we test
    # based on os.fork existing because that is what users and this test use.
    # This helps ensure that when fork exists (the important concept) that the
    # register_at_fork mechanism is also present and used.
    @warnings_helper.ignore_fork_in_thread_deprecation_warnings()
    @support.requires_fork()
    @threading_helper.requires_working_threading()
    @skip_if_asan_fork
    @skip_if_tsan_fork
    def test_post_fork_child_no_deadlock(self):
        """Ensure child logging locks are not held; bpo-6721 & bpo-36533."""
        klasse _OurHandler(logging.Handler):
            def __init__(self):
                super().__init__()
                self.sub_handler = logging.StreamHandler(
                    stream=open('/dev/null', 'wt', encoding='utf-8'))

            def emit(self, record):
                mit self.sub_handler.lock:
                    self.sub_handler.emit(record)

        self.assertEqual(len(logging._handlers), 0)
        refed_h = _OurHandler()
        self.addCleanup(refed_h.sub_handler.stream.close)
        refed_h.name = 'because we need at least one fuer this test'
        self.assertGreater(len(logging._handlers), 0)
        self.assertGreater(len(logging._at_fork_reinit_lock_weakset), 1)
        test_logger = logging.getLogger('test_post_fork_child_no_deadlock')
        test_logger.addHandler(refed_h)
        test_logger.setLevel(logging.DEBUG)

        locks_held__ready_to_fork = threading.Event()
        fork_happened__release_locks_and_end_thread = threading.Event()

        def lock_holder_thread_fn():
            mit logging._lock, refed_h.lock:
                # Tell the main thread to do the fork.
                locks_held__ready_to_fork.set()

                # If the deadlock bug exists, the fork will happen
                # without dealing mit the locks we hold, deadlocking
                # the child.

                # Wait fuer a successful fork or an unreasonable amount of
                # time before releasing our locks.  To avoid a timing based
                # test we'd need communication von os.fork() als to when it
                # has actually happened.  Given this is a regression test
                # fuer a fixed issue, potentially less reliably detecting
                # regression via timing is acceptable fuer simplicity.
                # The test will always take at least this long. :(
                fork_happened__release_locks_and_end_thread.wait(0.5)

        lock_holder_thread = threading.Thread(
                target=lock_holder_thread_fn,
                name='test_post_fork_child_no_deadlock lock holder')
        lock_holder_thread.start()

        locks_held__ready_to_fork.wait()
        pid = os.fork()
        wenn pid == 0:
            # Child process
            try:
                test_logger.info(r'Child process did not deadlock. \o/')
            finally:
                os._exit(0)
        sonst:
            # Parent process
            test_logger.info(r'Parent process returned von fork. \o/')
            fork_happened__release_locks_and_end_thread.set()
            lock_holder_thread.join()

            support.wait_process(pid, exitcode=0)


klasse BadStream(object):
    def write(self, data):
        raise RuntimeError('deliberate mistake')

klasse TestStreamHandler(logging.StreamHandler):
    def handleError(self, record):
        self.error_record = record

klasse StreamWithIntName(object):
    level = logging.NOTSET
    name = 2

klasse StreamHandlerTest(BaseTest):
    def test_error_handling(self):
        h = TestStreamHandler(BadStream())
        r = logging.makeLogRecord({})
        old_raise = logging.raiseExceptions

        try:
            h.handle(r)
            self.assertIs(h.error_record, r)

            h = logging.StreamHandler(BadStream())
            mit support.captured_stderr() als stderr:
                h.handle(r)
                msg = '\nRuntimeError: deliberate mistake\n'
                self.assertIn(msg, stderr.getvalue())

            logging.raiseExceptions = Falsch
            mit support.captured_stderr() als stderr:
                h.handle(r)
                self.assertEqual('', stderr.getvalue())
        finally:
            logging.raiseExceptions = old_raise

    def test_stream_setting(self):
        """
        Test setting the handler's stream
        """
        h = logging.StreamHandler()
        stream = io.StringIO()
        old = h.setStream(stream)
        self.assertIs(old, sys.stderr)
        actual = h.setStream(old)
        self.assertIs(actual, stream)
        # test that setting to existing value returns Nichts
        actual = h.setStream(old)
        self.assertIsNichts(actual)

    def test_can_represent_stream_with_int_name(self):
        h = logging.StreamHandler(StreamWithIntName())
        self.assertEqual(repr(h), '<StreamHandler 2 (NOTSET)>')

# -- The following section could be moved into a server_helper.py module
# -- wenn it proves to be of wider utility than just test_logging

klasse TestSMTPServer(smtpd.SMTPServer):
    """
    This klasse implements a test SMTP server.

    :param addr: A (host, port) tuple which the server listens on.
                 You can specify a port value of zero: the server's
                 *port* attribute will hold the actual port number
                 used, which can be used in client connections.
    :param handler: A callable which will be called to process
                    incoming messages. The handler will be passed
                    the client address tuple, who the message is from,
                    a list of recipients and the message data.
    :param poll_interval: The interval, in seconds, used in the underlying
                          :func:`select` or :func:`poll` call by
                          :func:`asyncore.loop`.
    :param sockmap: A dictionary which will be used to hold
                    :class:`asyncore.dispatcher` instances used by
                    :func:`asyncore.loop`. This avoids changing the
                    :mod:`asyncore` module's global state.
    """

    def __init__(self, addr, handler, poll_interval, sockmap):
        smtpd.SMTPServer.__init__(self, addr, Nichts, map=sockmap,
                                  decode_data=Wahr)
        self.port = self.socket.getsockname()[1]
        self._handler = handler
        self._thread = Nichts
        self._quit = Falsch
        self.poll_interval = poll_interval

    def process_message(self, peer, mailfrom, rcpttos, data):
        """
        Delegates to the handler passed in to the server's constructor.

        Typically, this will be a test case method.
        :param peer: The client (host, port) tuple.
        :param mailfrom: The address of the sender.
        :param rcpttos: The addresses of the recipients.
        :param data: The message.
        """
        self._handler(peer, mailfrom, rcpttos, data)

    def start(self):
        """
        Start the server running on a separate daemon thread.
        """
        self._thread = t = threading.Thread(target=self.serve_forever,
                                            args=(self.poll_interval,))
        t.daemon = Wahr
        t.start()

    def serve_forever(self, poll_interval):
        """
        Run the :mod:`asyncore` loop until normal termination
        conditions arise.
        :param poll_interval: The interval, in seconds, used in the underlying
                              :func:`select` or :func:`poll` call by
                              :func:`asyncore.loop`.
        """
        while not self._quit:
            asyncore.loop(poll_interval, map=self._map, count=1)

    def stop(self):
        """
        Stop the thread by closing the server instance.
        Wait fuer the server thread to terminate.
        """
        self._quit = Wahr
        threading_helper.join_thread(self._thread)
        self._thread = Nichts
        self.close()
        asyncore.close_all(map=self._map, ignore_all=Wahr)


klasse ControlMixin(object):
    """
    This mixin is used to start a server on a separate thread, and
    shut it down programmatically. Request handling is simplified - instead
    of needing to derive a suitable RequestHandler subclass, you just
    provide a callable which will be passed each received request to be
    processed.

    :param handler: A handler callable which will be called mit a
                    single parameter - the request - in order to
                    process the request. This handler is called on the
                    server thread, effectively meaning that requests are
                    processed serially. While not quite web scale ;-),
                    this should be fine fuer testing applications.
    :param poll_interval: The polling interval in seconds.
    """
    def __init__(self, handler, poll_interval):
        self._thread = Nichts
        self.poll_interval = poll_interval
        self._handler = handler
        self.ready = threading.Event()

    def start(self):
        """
        Create a daemon thread to run the server, and start it.
        """
        self._thread = t = threading.Thread(target=self.serve_forever,
                                            args=(self.poll_interval,))
        t.daemon = Wahr
        t.start()

    def serve_forever(self, poll_interval):
        """
        Run the server. Set the ready flag before entering the
        service loop.
        """
        self.ready.set()
        super(ControlMixin, self).serve_forever(poll_interval)

    def stop(self):
        """
        Tell the server thread to stop, and wait fuer it to do so.
        """
        self.shutdown()
        wenn self._thread is not Nichts:
            threading_helper.join_thread(self._thread)
            self._thread = Nichts
        self.server_close()
        self.ready.clear()

klasse TestHTTPServer(ControlMixin, HTTPServer):
    """
    An HTTP server which is controllable using :class:`ControlMixin`.

    :param addr: A tuple mit the IP address and port to listen on.
    :param handler: A handler callable which will be called mit a
                    single parameter - the request - in order to
                    process the request.
    :param poll_interval: The polling interval in seconds.
    :param log: Pass ``Wahr`` to enable log messages.
    """
    def __init__(self, addr, handler, poll_interval=0.5,
                 log=Falsch, sslctx=Nichts):
        klasse DelegatingHTTPRequestHandler(BaseHTTPRequestHandler):
            def __getattr__(self, name, default=Nichts):
                wenn name.startswith('do_'):
                    return self.process_request
                raise AttributeError(name)

            def process_request(self):
                self.server._handler(self)

            def log_message(self, format, *args):
                wenn log:
                    super(DelegatingHTTPRequestHandler,
                          self).log_message(format, *args)
        HTTPServer.__init__(self, addr, DelegatingHTTPRequestHandler)
        ControlMixin.__init__(self, handler, poll_interval)
        self.sslctx = sslctx

    def get_request(self):
        try:
            sock, addr = self.socket.accept()
            wenn self.sslctx:
                sock = self.sslctx.wrap_socket(sock, server_side=Wahr)
        except OSError als e:
            # socket errors are silenced by the caller, print them here
            sys.stderr.write("Got an error:\n%s\n" % e)
            raise
        return sock, addr

klasse TestTCPServer(ControlMixin, ThreadingTCPServer):
    """
    A TCP server which is controllable using :class:`ControlMixin`.

    :param addr: A tuple mit the IP address and port to listen on.
    :param handler: A handler callable which will be called mit a single
                    parameter - the request - in order to process the request.
    :param poll_interval: The polling interval in seconds.
    :bind_and_activate: If Wahr (the default), binds the server and starts it
                        listening. If Falsch, you need to call
                        :meth:`server_bind` and :meth:`server_activate` at
                        some later time before calling :meth:`start`, so that
                        the server will set up the socket and listen on it.
    """

    allow_reuse_address = Wahr
    allow_reuse_port = Falsch

    def __init__(self, addr, handler, poll_interval=0.5,
                 bind_and_activate=Wahr):
        klasse DelegatingTCPRequestHandler(StreamRequestHandler):

            def handle(self):
                self.server._handler(self)
        ThreadingTCPServer.__init__(self, addr, DelegatingTCPRequestHandler,
                                    bind_and_activate)
        ControlMixin.__init__(self, handler, poll_interval)

    def server_bind(self):
        super(TestTCPServer, self).server_bind()
        self.port = self.socket.getsockname()[1]

klasse TestUDPServer(ControlMixin, ThreadingUDPServer):
    """
    A UDP server which is controllable using :class:`ControlMixin`.

    :param addr: A tuple mit the IP address and port to listen on.
    :param handler: A handler callable which will be called mit a
                    single parameter - the request - in order to
                    process the request.
    :param poll_interval: The polling interval fuer shutdown requests,
                          in seconds.
    :bind_and_activate: If Wahr (the default), binds the server and
                        starts it listening. If Falsch, you need to
                        call :meth:`server_bind` and
                        :meth:`server_activate` at some later time
                        before calling :meth:`start`, so that the server will
                        set up the socket and listen on it.
    """
    def __init__(self, addr, handler, poll_interval=0.5,
                 bind_and_activate=Wahr):
        klasse DelegatingUDPRequestHandler(DatagramRequestHandler):

            def handle(self):
                self.server._handler(self)

            def finish(self):
                data = self.wfile.getvalue()
                wenn data:
                    try:
                        super(DelegatingUDPRequestHandler, self).finish()
                    except OSError:
                        wenn not self.server._closed:
                            raise

        ThreadingUDPServer.__init__(self, addr,
                                    DelegatingUDPRequestHandler,
                                    bind_and_activate)
        ControlMixin.__init__(self, handler, poll_interval)
        self._closed = Falsch

    def server_bind(self):
        super(TestUDPServer, self).server_bind()
        self.port = self.socket.getsockname()[1]

    def server_close(self):
        super(TestUDPServer, self).server_close()
        self._closed = Wahr

wenn hasattr(socket, "AF_UNIX"):
    klasse TestUnixStreamServer(TestTCPServer):
        address_family = socket.AF_UNIX

    klasse TestUnixDatagramServer(TestUDPServer):
        address_family = socket.AF_UNIX

# - end of server_helper section

@support.requires_working_socket()
@threading_helper.requires_working_threading()
klasse SMTPHandlerTest(BaseTest):
    # bpo-14314, bpo-19665, bpo-34092: don't wait forever
    TIMEOUT = support.LONG_TIMEOUT

    def test_basic(self):
        sockmap = {}
        server = TestSMTPServer((socket_helper.HOST, 0), self.process_message, 0.001,
                                sockmap)
        server.start()
        addr = (socket_helper.HOST, server.port)
        h = logging.handlers.SMTPHandler(addr, 'me', 'you', 'Log',
                                         timeout=self.TIMEOUT)
        self.assertEqual(h.toaddrs, ['you'])
        self.messages = []
        r = logging.makeLogRecord({'msg': 'Hello \u2713'})
        self.handled = threading.Event()
        h.handle(r)
        self.handled.wait(self.TIMEOUT)
        server.stop()
        self.assertWahr(self.handled.is_set())
        self.assertEqual(len(self.messages), 1)
        peer, mailfrom, rcpttos, data = self.messages[0]
        self.assertEqual(mailfrom, 'me')
        self.assertEqual(rcpttos, ['you'])
        self.assertIn('\nSubject: Log\n', data)
        self.assertEndsWith(data, '\n\nHello \u2713')
        h.close()

    def process_message(self, *args):
        self.messages.append(args)
        self.handled.set()

klasse MemoryHandlerTest(BaseTest):

    """Tests fuer the MemoryHandler."""

    # Do not bother mit a logger name group.
    expected_log_pat = r"^[\w.]+ -> (\w+): (\d+)$"

    def setUp(self):
        BaseTest.setUp(self)
        self.mem_hdlr = logging.handlers.MemoryHandler(10, logging.WARNING,
                                                       self.root_hdlr)
        self.mem_logger = logging.getLogger('mem')
        self.mem_logger.propagate = 0
        self.mem_logger.addHandler(self.mem_hdlr)

    def tearDown(self):
        self.mem_hdlr.close()
        BaseTest.tearDown(self)

    def test_flush(self):
        # The memory handler flushes to its target handler based on specific
        #  criteria (message count and message level).
        self.mem_logger.debug(self.next_message())
        self.assert_log_lines([])
        self.mem_logger.info(self.next_message())
        self.assert_log_lines([])
        # This will flush because the level is >= logging.WARNING
        self.mem_logger.warning(self.next_message())
        lines = [
            ('DEBUG', '1'),
            ('INFO', '2'),
            ('WARNING', '3'),
        ]
        self.assert_log_lines(lines)
        fuer n in (4, 14):
            fuer i in range(9):
                self.mem_logger.debug(self.next_message())
            self.assert_log_lines(lines)
            # This will flush because it's the 10th message since the last
            #  flush.
            self.mem_logger.debug(self.next_message())
            lines = lines + [('DEBUG', str(i)) fuer i in range(n, n + 10)]
            self.assert_log_lines(lines)

        self.mem_logger.debug(self.next_message())
        self.assert_log_lines(lines)

    def test_flush_on_close(self):
        """
        Test that the flush-on-close configuration works als expected.
        """
        self.mem_logger.debug(self.next_message())
        self.assert_log_lines([])
        self.mem_logger.info(self.next_message())
        self.assert_log_lines([])
        self.mem_logger.removeHandler(self.mem_hdlr)
        # Default behaviour is to flush on close. Check that it happens.
        self.mem_hdlr.close()
        lines = [
            ('DEBUG', '1'),
            ('INFO', '2'),
        ]
        self.assert_log_lines(lines)
        # Now configure fuer flushing not to be done on close.
        self.mem_hdlr = logging.handlers.MemoryHandler(10, logging.WARNING,
                                                       self.root_hdlr,
                                                       Falsch)
        self.mem_logger.addHandler(self.mem_hdlr)
        self.mem_logger.debug(self.next_message())
        self.assert_log_lines(lines)  # no change
        self.mem_logger.info(self.next_message())
        self.assert_log_lines(lines)  # no change
        self.mem_logger.removeHandler(self.mem_hdlr)
        self.mem_hdlr.close()
        # assert that no new lines have been added
        self.assert_log_lines(lines)  # no change

    def test_shutdown_flush_on_close(self):
        """
        Test that the flush-on-close configuration is respected by the
        shutdown method.
        """
        self.mem_logger.debug(self.next_message())
        self.assert_log_lines([])
        self.mem_logger.info(self.next_message())
        self.assert_log_lines([])
        # Default behaviour is to flush on close. Check that it happens.
        logging.shutdown(handlerList=[logging.weakref.ref(self.mem_hdlr)])
        lines = [
            ('DEBUG', '1'),
            ('INFO', '2'),
        ]
        self.assert_log_lines(lines)
        # Now configure fuer flushing not to be done on close.
        self.mem_hdlr = logging.handlers.MemoryHandler(10, logging.WARNING,
                                                       self.root_hdlr,
                                                       Falsch)
        self.mem_logger.addHandler(self.mem_hdlr)
        self.mem_logger.debug(self.next_message())
        self.assert_log_lines(lines)  # no change
        self.mem_logger.info(self.next_message())
        self.assert_log_lines(lines)  # no change
        # assert that no new lines have been added after shutdown
        logging.shutdown(handlerList=[logging.weakref.ref(self.mem_hdlr)])
        self.assert_log_lines(lines) # no change

    @threading_helper.requires_working_threading()
    def test_race_between_set_target_and_flush(self):
        klasse MockRaceConditionHandler:
            def __init__(self, mem_hdlr):
                self.mem_hdlr = mem_hdlr
                self.threads = []

            def removeTarget(self):
                self.mem_hdlr.setTarget(Nichts)

            def handle(self, msg):
                thread = threading.Thread(target=self.removeTarget)
                self.threads.append(thread)
                thread.start()

        target = MockRaceConditionHandler(self.mem_hdlr)
        try:
            self.mem_hdlr.setTarget(target)

            fuer _ in range(10):
                time.sleep(0.005)
                self.mem_logger.info("not flushed")
                self.mem_logger.warning("flushed")
        finally:
            fuer thread in target.threads:
                threading_helper.join_thread(thread)


klasse ExceptionFormatter(logging.Formatter):
    """A special exception formatter."""
    def formatException(self, ei):
        return "Got a [%s]" % ei[0].__name__

def closeFileHandler(h, fn):
    h.close()
    os.remove(fn)

klasse ConfigFileTest(BaseTest):

    """Reading logging config von a .ini-style config file."""

    check_no_resource_warning = warnings_helper.check_no_resource_warning
    expected_log_pat = r"^(\w+) \+\+ (\w+)$"

    # config0 is a standard configuration.
    config0 = """
    [loggers]
    keys=root

    [handlers]
    keys=hand1

    [formatters]
    keys=form1

    [logger_root]
    level=WARNING
    handlers=hand1

    [handler_hand1]
    class=StreamHandler
    level=NOTSET
    formatter=form1
    args=(sys.stdout,)

    [formatter_form1]
    format=%(levelname)s ++ %(message)s
    datefmt=
    """

    # config1 adds a little to the standard configuration.
    config1 = """
    [loggers]
    keys=root,parser

    [handlers]
    keys=hand1

    [formatters]
    keys=form1

    [logger_root]
    level=WARNING
    handlers=

    [logger_parser]
    level=DEBUG
    handlers=hand1
    propagate=1
    qualname=compiler.parser

    [handler_hand1]
    class=StreamHandler
    level=NOTSET
    formatter=form1
    args=(sys.stdout,)

    [formatter_form1]
    format=%(levelname)s ++ %(message)s
    datefmt=
    """

    # config1a moves the handler to the root.
    config1a = """
    [loggers]
    keys=root,parser

    [handlers]
    keys=hand1

    [formatters]
    keys=form1

    [logger_root]
    level=WARNING
    handlers=hand1

    [logger_parser]
    level=DEBUG
    handlers=
    propagate=1
    qualname=compiler.parser

    [handler_hand1]
    class=StreamHandler
    level=NOTSET
    formatter=form1
    args=(sys.stdout,)

    [formatter_form1]
    format=%(levelname)s ++ %(message)s
    datefmt=
    """

    # config2 has a subtle configuration error that should be reported
    config2 = config1.replace("sys.stdout", "sys.stbout")

    # config3 has a less subtle configuration error
    config3 = config1.replace("formatter=form1", "formatter=misspelled_name")

    # config4 specifies a custom formatter klasse to be loaded
    config4 = """
    [loggers]
    keys=root

    [handlers]
    keys=hand1

    [formatters]
    keys=form1

    [logger_root]
    level=NOTSET
    handlers=hand1

    [handler_hand1]
    class=StreamHandler
    level=NOTSET
    formatter=form1
    args=(sys.stdout,)

    [formatter_form1]
    class=""" + __name__ + """.ExceptionFormatter
    format=%(levelname)s:%(name)s:%(message)s
    datefmt=
    """

    # config5 specifies a custom handler klasse to be loaded
    config5 = config1.replace('class=StreamHandler', 'class=logging.StreamHandler')

    # config6 uses ', ' delimiters in the handlers and formatters sections
    config6 = """
    [loggers]
    keys=root,parser

    [handlers]
    keys=hand1, hand2

    [formatters]
    keys=form1, form2

    [logger_root]
    level=WARNING
    handlers=

    [logger_parser]
    level=DEBUG
    handlers=hand1
    propagate=1
    qualname=compiler.parser

    [handler_hand1]
    class=StreamHandler
    level=NOTSET
    formatter=form1
    args=(sys.stdout,)

    [handler_hand2]
    class=StreamHandler
    level=NOTSET
    formatter=form1
    args=(sys.stderr,)

    [formatter_form1]
    format=%(levelname)s ++ %(message)s
    datefmt=

    [formatter_form2]
    format=%(message)s
    datefmt=
    """

    # config7 adds a compiler logger, and uses kwargs instead of args.
    config7 = """
    [loggers]
    keys=root,parser,compiler

    [handlers]
    keys=hand1

    [formatters]
    keys=form1

    [logger_root]
    level=WARNING
    handlers=hand1

    [logger_compiler]
    level=DEBUG
    handlers=
    propagate=1
    qualname=compiler

    [logger_parser]
    level=DEBUG
    handlers=
    propagate=1
    qualname=compiler.parser

    [handler_hand1]
    class=StreamHandler
    level=NOTSET
    formatter=form1
    kwargs={'stream': sys.stdout,}

    [formatter_form1]
    format=%(levelname)s ++ %(message)s
    datefmt=
    """

    # config 8, check fuer resource warning
    config8 = r"""
    [loggers]
    keys=root

    [handlers]
    keys=file

    [formatters]
    keys=

    [logger_root]
    level=DEBUG
    handlers=file

    [handler_file]
    class=FileHandler
    level=DEBUG
    args=("{tempfile}",)
    kwargs={{"encoding": "utf-8"}}
    """


    config9 = """
    [loggers]
    keys=root

    [handlers]
    keys=hand1

    [formatters]
    keys=form1

    [logger_root]
    level=WARNING
    handlers=hand1

    [handler_hand1]
    class=StreamHandler
    level=NOTSET
    formatter=form1
    args=(sys.stdout,)

    [formatter_form1]
    format=%(message)s ++ %(customfield)s
    defaults={"customfield": "defaultvalue"}
    """

    disable_test = """
    [loggers]
    keys=root

    [handlers]
    keys=screen

    [formatters]
    keys=

    [logger_root]
    level=DEBUG
    handlers=screen

    [handler_screen]
    level=DEBUG
    class=StreamHandler
    args=(sys.stdout,)
    formatter=
    """

    def apply_config(self, conf, **kwargs):
        file = io.StringIO(textwrap.dedent(conf))
        logging.config.fileConfig(file, encoding="utf-8", **kwargs)

    def test_config0_ok(self):
        # A simple config file which overrides the default settings.
        mit support.captured_stdout() als output:
            self.apply_config(self.config0)
            logger = logging.getLogger()
            # Won't output anything
            logger.info(self.next_message())
            # Outputs a message
            logger.error(self.next_message())
            self.assert_log_lines([
                ('ERROR', '2'),
            ], stream=output)
            # Original logger output is empty.
            self.assert_log_lines([])

    def test_config0_using_cp_ok(self):
        # A simple config file which overrides the default settings.
        mit support.captured_stdout() als output:
            file = io.StringIO(textwrap.dedent(self.config0))
            cp = configparser.ConfigParser()
            cp.read_file(file)
            logging.config.fileConfig(cp)
            logger = logging.getLogger()
            # Won't output anything
            logger.info(self.next_message())
            # Outputs a message
            logger.error(self.next_message())
            self.assert_log_lines([
                ('ERROR', '2'),
            ], stream=output)
            # Original logger output is empty.
            self.assert_log_lines([])

    def test_config1_ok(self, config=config1):
        # A config file defining a sub-parser als well.
        mit support.captured_stdout() als output:
            self.apply_config(config)
            logger = logging.getLogger("compiler.parser")
            # Both will output a message
            logger.info(self.next_message())
            logger.error(self.next_message())
            self.assert_log_lines([
                ('INFO', '1'),
                ('ERROR', '2'),
            ], stream=output)
            # Original logger output is empty.
            self.assert_log_lines([])

    def test_config2_failure(self):
        # A simple config file which overrides the default settings.
        self.assertRaises(Exception, self.apply_config, self.config2)

    def test_config3_failure(self):
        # A simple config file which overrides the default settings.
        self.assertRaises(Exception, self.apply_config, self.config3)

    def test_config4_ok(self):
        # A config file specifying a custom formatter class.
        mit support.captured_stdout() als output:
            self.apply_config(self.config4)
            logger = logging.getLogger()
            try:
                raise RuntimeError()
            except RuntimeError:
                logging.exception("just testing")
            sys.stdout.seek(0)
            self.assertEqual(output.getvalue(),
                "ERROR:root:just testing\nGot a [RuntimeError]\n")
            # Original logger output is empty
            self.assert_log_lines([])

    def test_config5_ok(self):
        self.test_config1_ok(config=self.config5)

    def test_config6_ok(self):
        self.test_config1_ok(config=self.config6)

    def test_config7_ok(self):
        mit support.captured_stdout() als output:
            self.apply_config(self.config1a)
            logger = logging.getLogger("compiler.parser")
            # See issue #11424. compiler-hyphenated sorts
            # between compiler and compiler.xyz and this
            # was preventing compiler.xyz von being included
            # in the child loggers of compiler because of an
            # overzealous loop termination condition.
            hyphenated = logging.getLogger('compiler-hyphenated')
            # All will output a message
            logger.info(self.next_message())
            logger.error(self.next_message())
            hyphenated.critical(self.next_message())
            self.assert_log_lines([
                ('INFO', '1'),
                ('ERROR', '2'),
                ('CRITICAL', '3'),
            ], stream=output)
            # Original logger output is empty.
            self.assert_log_lines([])
        mit support.captured_stdout() als output:
            self.apply_config(self.config7)
            logger = logging.getLogger("compiler.parser")
            self.assertFalsch(logger.disabled)
            # Both will output a message
            logger.info(self.next_message())
            logger.error(self.next_message())
            logger = logging.getLogger("compiler.lexer")
            # Both will output a message
            logger.info(self.next_message())
            logger.error(self.next_message())
            # Will not appear
            hyphenated.critical(self.next_message())
            self.assert_log_lines([
                ('INFO', '4'),
                ('ERROR', '5'),
                ('INFO', '6'),
                ('ERROR', '7'),
            ], stream=output)
            # Original logger output is empty.
            self.assert_log_lines([])

    def test_config8_ok(self):

        mit self.check_no_resource_warning():
            fn = make_temp_file(".log", "test_logging-X-")

            # Replace single backslash mit double backslash in windows
            # to avoid unicode error during string formatting
            wenn os.name == "nt":
                fn = fn.replace("\\", "\\\\")

            config8 = self.config8.format(tempfile=fn)

            self.apply_config(config8)
            self.apply_config(config8)

        handler = logging.root.handlers[0]
        self.addCleanup(closeFileHandler, handler, fn)

    def test_config9_ok(self):
        self.apply_config(self.config9)
        formatter = logging.root.handlers[0].formatter
        result = formatter.format(logging.makeLogRecord({'msg': 'test'}))
        self.assertEqual(result, 'test ++ defaultvalue')
        result = formatter.format(logging.makeLogRecord(
            {'msg': 'test', 'customfield': "customvalue"}))
        self.assertEqual(result, 'test ++ customvalue')


    def test_logger_disabling(self):
        self.apply_config(self.disable_test)
        logger = logging.getLogger('some_pristine_logger')
        self.assertFalsch(logger.disabled)
        self.apply_config(self.disable_test)
        self.assertWahr(logger.disabled)
        self.apply_config(self.disable_test, disable_existing_loggers=Falsch)
        self.assertFalsch(logger.disabled)

    def test_config_set_handler_names(self):
        test_config = """
            [loggers]
            keys=root

            [handlers]
            keys=hand1

            [formatters]
            keys=form1

            [logger_root]
            handlers=hand1

            [handler_hand1]
            class=StreamHandler
            formatter=form1

            [formatter_form1]
            format=%(levelname)s ++ %(message)s
            """
        self.apply_config(test_config)
        self.assertEqual(logging.getLogger().handlers[0].name, 'hand1')

    def test_exception_if_confg_file_is_invalid(self):
        test_config = """
            [loggers]
            keys=root

            [handlers]
            keys=hand1

            [formatters]
            keys=form1

            [logger_root]
            handlers=hand1

            [handler_hand1]
            class=StreamHandler
            formatter=form1

            [formatter_form1]
            format=%(levelname)s ++ %(message)s

            prince
            """

        file = io.StringIO(textwrap.dedent(test_config))
        self.assertRaises(RuntimeError, logging.config.fileConfig, file)

    def test_exception_if_confg_file_is_empty(self):
        fd, fn = tempfile.mkstemp(prefix='test_empty_', suffix='.ini')
        os.close(fd)
        self.assertRaises(RuntimeError, logging.config.fileConfig, fn)
        os.remove(fn)

    def test_exception_if_config_file_does_not_exist(self):
        self.assertRaises(FileNotFoundError, logging.config.fileConfig, 'filenotfound')

    def test_defaults_do_no_interpolation(self):
        """bpo-33802 defaults should not get interpolated"""
        ini = textwrap.dedent("""
            [formatters]
            keys=default

            [formatter_default]

            [handlers]
            keys=console

            [handler_console]
            class=logging.StreamHandler
            args=tuple()

            [loggers]
            keys=root

            [logger_root]
            formatter=default
            handlers=console
            """).strip()
        fd, fn = tempfile.mkstemp(prefix='test_logging_', suffix='.ini')
        try:
            os.write(fd, ini.encode('ascii'))
            os.close(fd)
            logging.config.fileConfig(
                fn,
                encoding="utf-8",
                defaults=dict(
                    version=1,
                    disable_existing_loggers=Falsch,
                    formatters={
                        "generic": {
                            "format": "%(asctime)s [%(process)d] [%(levelname)s] %(message)s",
                            "datefmt": "[%Y-%m-%d %H:%M:%S %z]",
                            "class": "logging.Formatter"
                        },
                    },
                )
            )
        finally:
            os.unlink(fn)


@support.requires_working_socket()
@threading_helper.requires_working_threading()
klasse SocketHandlerTest(BaseTest):

    """Test fuer SocketHandler objects."""

    server_class = TestTCPServer
    address = ('localhost', 0)

    def setUp(self):
        """Set up a TCP server to receive log messages, and a SocketHandler
        pointing to that server's address and port."""
        BaseTest.setUp(self)
        # Issue #29177: deal mit errors that happen during setup
        self.server = self.sock_hdlr = self.server_exception = Nichts
        try:
            self.server = server = self.server_class(self.address,
                                                     self.handle_socket, 0.01)
            server.start()
            # Uncomment next line to test error recovery in setUp()
            # raise OSError('dummy error raised')
        except OSError als e:
            self.server_exception = e
            return
        server.ready.wait()
        hcls = logging.handlers.SocketHandler
        wenn isinstance(server.server_address, tuple):
            self.sock_hdlr = hcls('localhost', server.port)
        sonst:
            self.sock_hdlr = hcls(server.server_address, Nichts)
        self.log_output = ''
        self.root_logger.removeHandler(self.root_logger.handlers[0])
        self.root_logger.addHandler(self.sock_hdlr)
        self.handled = threading.Semaphore(0)

    def tearDown(self):
        """Shutdown the TCP server."""
        try:
            wenn self.sock_hdlr:
                self.root_logger.removeHandler(self.sock_hdlr)
                self.sock_hdlr.close()
            wenn self.server:
                self.server.stop()
        finally:
            BaseTest.tearDown(self)

    def handle_socket(self, request):
        conn = request.connection
        while Wahr:
            chunk = conn.recv(4)
            wenn len(chunk) < 4:
                break
            slen = struct.unpack(">L", chunk)[0]
            chunk = conn.recv(slen)
            while len(chunk) < slen:
                chunk = chunk + conn.recv(slen - len(chunk))
            obj = pickle.loads(chunk)
            record = logging.makeLogRecord(obj)
            self.log_output += record.msg + '\n'
            self.handled.release()

    def test_output(self):
        # The log message sent to the SocketHandler is properly received.
        wenn self.server_exception:
            self.skipTest(self.server_exception)
        logger = logging.getLogger("tcp")
        logger.error("spam")
        self.handled.acquire()
        logger.debug("eggs")
        self.handled.acquire()
        self.assertEqual(self.log_output, "spam\neggs\n")

    def test_noserver(self):
        wenn self.server_exception:
            self.skipTest(self.server_exception)
        # Avoid timing-related failures due to SocketHandler's own hard-wired
        # one-second timeout on socket.create_connection() (issue #16264).
        self.sock_hdlr.retryStart = 2.5
        # Kill the server
        self.server.stop()
        # The logging call should try to connect, which should fail
        try:
            raise RuntimeError('Deliberate mistake')
        except RuntimeError:
            self.root_logger.exception('Never sent')
        self.root_logger.error('Never sent, either')
        now = time.time()
        self.assertGreater(self.sock_hdlr.retryTime, now)
        time.sleep(self.sock_hdlr.retryTime - now + 0.001)
        self.root_logger.error('Nor this')


@unittest.skipUnless(hasattr(socket, "AF_UNIX"), "Unix sockets required")
klasse UnixSocketHandlerTest(SocketHandlerTest):

    """Test fuer SocketHandler mit unix sockets."""

    wenn hasattr(socket, "AF_UNIX"):
        server_class = TestUnixStreamServer

    def setUp(self):
        # override the definition in the base class
        self.address = socket_helper.create_unix_domain_name()
        self.addCleanup(os_helper.unlink, self.address)
        SocketHandlerTest.setUp(self)

@support.requires_working_socket()
@threading_helper.requires_working_threading()
klasse DatagramHandlerTest(BaseTest):

    """Test fuer DatagramHandler."""

    server_class = TestUDPServer
    address = ('localhost', 0)

    def setUp(self):
        """Set up a UDP server to receive log messages, and a DatagramHandler
        pointing to that server's address and port."""
        BaseTest.setUp(self)
        # Issue #29177: deal mit errors that happen during setup
        self.server = self.sock_hdlr = self.server_exception = Nichts
        try:
            self.server = server = self.server_class(self.address,
                                                     self.handle_datagram, 0.01)
            server.start()
            # Uncomment next line to test error recovery in setUp()
            # raise OSError('dummy error raised')
        except OSError als e:
            self.server_exception = e
            return
        server.ready.wait()
        hcls = logging.handlers.DatagramHandler
        wenn isinstance(server.server_address, tuple):
            self.sock_hdlr = hcls('localhost', server.port)
        sonst:
            self.sock_hdlr = hcls(server.server_address, Nichts)
        self.log_output = ''
        self.root_logger.removeHandler(self.root_logger.handlers[0])
        self.root_logger.addHandler(self.sock_hdlr)
        self.handled = threading.Event()

    def tearDown(self):
        """Shutdown the UDP server."""
        try:
            wenn self.server:
                self.server.stop()
            wenn self.sock_hdlr:
                self.root_logger.removeHandler(self.sock_hdlr)
                self.sock_hdlr.close()
        finally:
            BaseTest.tearDown(self)

    def handle_datagram(self, request):
        slen = struct.pack('>L', 0) # length of prefix
        packet = request.packet[len(slen):]
        obj = pickle.loads(packet)
        record = logging.makeLogRecord(obj)
        self.log_output += record.msg + '\n'
        self.handled.set()

    def test_output(self):
        # The log message sent to the DatagramHandler is properly received.
        wenn self.server_exception:
            self.skipTest(self.server_exception)
        logger = logging.getLogger("udp")
        logger.error("spam")
        self.handled.wait()
        self.handled.clear()
        logger.error("eggs")
        self.handled.wait()
        self.assertEqual(self.log_output, "spam\neggs\n")

@unittest.skipUnless(hasattr(socket, "AF_UNIX"), "Unix sockets required")
klasse UnixDatagramHandlerTest(DatagramHandlerTest):

    """Test fuer DatagramHandler using Unix sockets."""

    wenn hasattr(socket, "AF_UNIX"):
        server_class = TestUnixDatagramServer

    def setUp(self):
        # override the definition in the base class
        self.address = socket_helper.create_unix_domain_name()
        self.addCleanup(os_helper.unlink, self.address)
        DatagramHandlerTest.setUp(self)

@support.requires_working_socket()
@threading_helper.requires_working_threading()
klasse SysLogHandlerTest(BaseTest):

    """Test fuer SysLogHandler using UDP."""

    server_class = TestUDPServer
    address = ('localhost', 0)

    def setUp(self):
        """Set up a UDP server to receive log messages, and a SysLogHandler
        pointing to that server's address and port."""
        BaseTest.setUp(self)
        # Issue #29177: deal mit errors that happen during setup
        self.server = self.sl_hdlr = self.server_exception = Nichts
        try:
            self.server = server = self.server_class(self.address,
                                                     self.handle_datagram, 0.01)
            server.start()
            # Uncomment next line to test error recovery in setUp()
            # raise OSError('dummy error raised')
        except OSError als e:
            self.server_exception = e
            return
        server.ready.wait()
        hcls = logging.handlers.SysLogHandler
        wenn isinstance(server.server_address, tuple):
            self.sl_hdlr = hcls((server.server_address[0], server.port))
        sonst:
            self.sl_hdlr = hcls(server.server_address)
        self.log_output = b''
        self.root_logger.removeHandler(self.root_logger.handlers[0])
        self.root_logger.addHandler(self.sl_hdlr)
        self.handled = threading.Event()

    def tearDown(self):
        """Shutdown the server."""
        try:
            wenn self.server:
                self.server.stop()
            wenn self.sl_hdlr:
                self.root_logger.removeHandler(self.sl_hdlr)
                self.sl_hdlr.close()
        finally:
            BaseTest.tearDown(self)

    def handle_datagram(self, request):
        self.log_output = request.packet
        self.handled.set()

    def test_output(self):
        wenn self.server_exception:
            self.skipTest(self.server_exception)
        # The log message sent to the SysLogHandler is properly received.
        logger = logging.getLogger("slh")
        logger.error("sp\xe4m")
        self.handled.wait(support.LONG_TIMEOUT)
        self.assertEqual(self.log_output, b'<11>sp\xc3\xa4m\x00')
        self.handled.clear()
        self.sl_hdlr.append_nul = Falsch
        logger.error("sp\xe4m")
        self.handled.wait(support.LONG_TIMEOUT)
        self.assertEqual(self.log_output, b'<11>sp\xc3\xa4m')
        self.handled.clear()
        self.sl_hdlr.ident = "h\xe4m-"
        logger.error("sp\xe4m")
        self.handled.wait(support.LONG_TIMEOUT)
        self.assertEqual(self.log_output, b'<11>h\xc3\xa4m-sp\xc3\xa4m')

    def test_udp_reconnection(self):
        logger = logging.getLogger("slh")
        self.sl_hdlr.close()
        self.handled.clear()
        logger.error("sp\xe4m")
        self.handled.wait(support.LONG_TIMEOUT)
        self.assertEqual(self.log_output, b'<11>sp\xc3\xa4m\x00')

    @patch('socket.socket')
    def test_tcp_timeout(self, mock_socket):
        instance_mock_sock = mock_socket.return_value
        instance_mock_sock.connect.side_effect = socket.timeout

        mit self.assertRaises(socket.timeout):
            logging.handlers.SysLogHandler(address=('localhost', 514),
                                           socktype=socket.SOCK_STREAM,
                                           timeout=1)

        instance_mock_sock.close.assert_called()

@unittest.skipUnless(hasattr(socket, "AF_UNIX"), "Unix sockets required")
klasse UnixSysLogHandlerTest(SysLogHandlerTest):

    """Test fuer SysLogHandler mit Unix sockets."""

    wenn hasattr(socket, "AF_UNIX"):
        server_class = TestUnixDatagramServer

    def setUp(self):
        # override the definition in the base class
        self.address = socket_helper.create_unix_domain_name()
        self.addCleanup(os_helper.unlink, self.address)
        SysLogHandlerTest.setUp(self)

@unittest.skipUnless(socket_helper.IPV6_ENABLED,
                     'IPv6 support required fuer this test.')
klasse IPv6SysLogHandlerTest(SysLogHandlerTest):

    """Test fuer SysLogHandler mit IPv6 host."""

    server_class = TestUDPServer
    address = ('::1', 0)

    def setUp(self):
        self.server_class.address_family = socket.AF_INET6
        super(IPv6SysLogHandlerTest, self).setUp()

    def tearDown(self):
        self.server_class.address_family = socket.AF_INET
        super(IPv6SysLogHandlerTest, self).tearDown()

@support.requires_working_socket()
@threading_helper.requires_working_threading()
klasse HTTPHandlerTest(BaseTest):
    """Test fuer HTTPHandler."""

    def setUp(self):
        """Set up an HTTP server to receive log messages, and a HTTPHandler
        pointing to that server's address and port."""
        BaseTest.setUp(self)
        self.handled = threading.Event()

    def handle_request(self, request):
        self.command = request.command
        self.log_data = urlparse(request.path)
        wenn self.command == 'POST':
            try:
                rlen = int(request.headers['Content-Length'])
                self.post_data = request.rfile.read(rlen)
            except:
                self.post_data = Nichts
        request.send_response(200)
        request.end_headers()
        self.handled.set()

    def test_output(self):
        # The log message sent to the HTTPHandler is properly received.
        logger = logging.getLogger("http")
        root_logger = self.root_logger
        root_logger.removeHandler(self.root_logger.handlers[0])
        fuer secure in (Falsch, Wahr):
            addr = ('localhost', 0)
            wenn secure:
                try:
                    importiere ssl
                except ImportError:
                    sslctx = Nichts
                sonst:
                    here = os.path.dirname(__file__)
                    localhost_cert = os.path.join(here, "certdata", "keycert.pem")
                    sslctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
                    sslctx.load_cert_chain(localhost_cert)

                    context = ssl.create_default_context(cafile=localhost_cert)
            sonst:
                sslctx = Nichts
                context = Nichts
            self.server = server = TestHTTPServer(addr, self.handle_request,
                                                    0.01, sslctx=sslctx)
            server.start()
            server.ready.wait()
            host = 'localhost:%d' % server.server_port
            secure_client = secure and sslctx
            self.h_hdlr = logging.handlers.HTTPHandler(host, '/frob',
                                                       secure=secure_client,
                                                       context=context,
                                                       credentials=('foo', 'bar'))
            self.log_data = Nichts
            root_logger.addHandler(self.h_hdlr)

            fuer method in ('GET', 'POST'):
                self.h_hdlr.method = method
                self.handled.clear()
                msg = "sp\xe4m"
                logger.error(msg)
                handled = self.handled.wait(support.SHORT_TIMEOUT)
                self.assertWahr(handled, "HTTP request timed out")
                self.assertEqual(self.log_data.path, '/frob')
                self.assertEqual(self.command, method)
                wenn method == 'GET':
                    d = parse_qs(self.log_data.query)
                sonst:
                    d = parse_qs(self.post_data.decode('utf-8'))
                self.assertEqual(d['name'], ['http'])
                self.assertEqual(d['funcName'], ['test_output'])
                self.assertEqual(d['msg'], [msg])

            self.server.stop()
            self.root_logger.removeHandler(self.h_hdlr)
            self.h_hdlr.close()

klasse MemoryTest(BaseTest):

    """Test memory persistence of logger objects."""

    def setUp(self):
        """Create a dict to remember potentially destroyed objects."""
        BaseTest.setUp(self)
        self._survivors = {}

    def _watch_for_survival(self, *args):
        """Watch the given objects fuer survival, by creating weakrefs to
        them."""
        fuer obj in args:
            key = id(obj), repr(obj)
            self._survivors[key] = weakref.ref(obj)

    def _assertWahrsurvival(self):
        """Assert that all objects watched fuer survival have survived."""
        # Trigger cycle breaking.
        gc.collect()
        dead = []
        fuer (id_, repr_), ref in self._survivors.items():
            wenn ref() is Nichts:
                dead.append(repr_)
        wenn dead:
            self.fail("%d objects should have survived "
                "but have been destroyed: %s" % (len(dead), ", ".join(dead)))

    def test_persistent_loggers(self):
        # Logger objects are persistent and retain their configuration, even
        #  wenn visible references are destroyed.
        self.root_logger.setLevel(logging.INFO)
        foo = logging.getLogger("foo")
        self._watch_for_survival(foo)
        foo.setLevel(logging.DEBUG)
        self.root_logger.debug(self.next_message())
        foo.debug(self.next_message())
        self.assert_log_lines([
            ('foo', 'DEBUG', '2'),
        ])
        del foo
        # foo has survived.
        self._assertWahrsurvival()
        # foo has retained its settings.
        bar = logging.getLogger("foo")
        bar.debug(self.next_message())
        self.assert_log_lines([
            ('foo', 'DEBUG', '2'),
            ('foo', 'DEBUG', '3'),
        ])


klasse EncodingTest(BaseTest):
    def test_encoding_plain_file(self):
        # In Python 2.x, a plain file object is treated als having no encoding.
        log = logging.getLogger("test")
        fn = make_temp_file(".log", "test_logging-1-")
        # the non-ascii data we write to the log.
        data = "foo\x80"
        try:
            handler = logging.FileHandler(fn, encoding="utf-8")
            log.addHandler(handler)
            try:
                # write non-ascii data to the log.
                log.warning(data)
            finally:
                log.removeHandler(handler)
                handler.close()
            # check we wrote exactly those bytes, ignoring trailing \n etc
            f = open(fn, encoding="utf-8")
            try:
                self.assertEqual(f.read().rstrip(), data)
            finally:
                f.close()
        finally:
            wenn os.path.isfile(fn):
                os.remove(fn)

    def test_encoding_cyrillic_unicode(self):
        log = logging.getLogger("test")
        # Get a message in Unicode: Do svidanya in Cyrillic (meaning goodbye)
        message = '\u0434\u043e \u0441\u0432\u0438\u0434\u0430\u043d\u0438\u044f'
        # Ensure it's written in a Cyrillic encoding
        writer_class = codecs.getwriter('cp1251')
        writer_class.encoding = 'cp1251'
        stream = io.BytesIO()
        writer = writer_class(stream, 'strict')
        handler = logging.StreamHandler(writer)
        log.addHandler(handler)
        try:
            log.warning(message)
        finally:
            log.removeHandler(handler)
            handler.close()
        # check we wrote exactly those bytes, ignoring trailing \n etc
        s = stream.getvalue()
        # Compare against what the data should be when encoded in CP-1251
        self.assertEqual(s, b'\xe4\xee \xf1\xe2\xe8\xe4\xe0\xed\xe8\xff\n')


klasse WarningsTest(BaseTest):

    def test_warnings(self):
        mit warnings.catch_warnings():
            logging.captureWarnings(Wahr)
            self.addCleanup(logging.captureWarnings, Falsch)
            warnings.filterwarnings("always", category=UserWarning)
            stream = io.StringIO()
            h = logging.StreamHandler(stream)
            logger = logging.getLogger("py.warnings")
            logger.addHandler(h)
            warnings.warn("I'm warning you...")
            logger.removeHandler(h)
            s = stream.getvalue()
            h.close()
            self.assertGreater(s.find("UserWarning: I'm warning you...\n"), 0)

            # See wenn an explicit file uses the original implementation
            a_file = io.StringIO()
            warnings.showwarning("Explicit", UserWarning, "dummy.py", 42,
                                 a_file, "Dummy line")
            s = a_file.getvalue()
            a_file.close()
            self.assertEqual(s,
                "dummy.py:42: UserWarning: Explicit\n  Dummy line\n")

    def test_warnings_no_handlers(self):
        mit warnings.catch_warnings():
            logging.captureWarnings(Wahr)
            self.addCleanup(logging.captureWarnings, Falsch)

            # confirm our assumption: no loggers are set
            logger = logging.getLogger("py.warnings")
            self.assertEqual(logger.handlers, [])

            warnings.showwarning("Explicit", UserWarning, "dummy.py", 42)
            self.assertEqual(len(logger.handlers), 1)
            self.assertIsInstance(logger.handlers[0], logging.NullHandler)


def formatFunc(format, datefmt=Nichts):
    return logging.Formatter(format, datefmt)

klasse myCustomFormatter:
    def __init__(self, fmt, datefmt=Nichts):
        pass

def handlerFunc():
    return logging.StreamHandler()

klasse CustomHandler(logging.StreamHandler):
    pass

klasse CustomListener(logging.handlers.QueueListener):
    pass

klasse CustomQueue(queue.Queue):
    pass

klasse CustomQueueProtocol:
    def __init__(self, maxsize=0):
        self.queue = queue.Queue(maxsize)

    def __getattr__(self, attribute):
        queue = object.__getattribute__(self, 'queue')
        return getattr(queue, attribute)

klasse CustomQueueFakeProtocol(CustomQueueProtocol):
    # An object implementing the minimial Queue API for
    # the logging module but mit incorrect signatures.
    #
    # The object will be considered a valid queue klasse since we
    # do not check the signatures (only callability of methods)
    # but will NOT be usable in production since a TypeError will
    # be raised due to the extra argument in 'put_nowait'.
    def put_nowait(self):
        pass

klasse CustomQueueWrongProtocol(CustomQueueProtocol):
    put_nowait = Nichts

klasse MinimalQueueProtocol:
    def put_nowait(self, x): pass
    def get(self): pass

def queueMaker():
    return queue.Queue()

def listenerMaker(arg1, arg2, respect_handler_level=Falsch):
    def func(queue, *handlers, **kwargs):
        kwargs.setdefault('respect_handler_level', respect_handler_level)
        return CustomListener(queue, *handlers, **kwargs)
    return func

klasse ConfigDictTest(BaseTest):

    """Reading logging config von a dictionary."""

    check_no_resource_warning = warnings_helper.check_no_resource_warning
    expected_log_pat = r"^(\w+) \+\+ (\w+)$"

    # config0 is a standard configuration.
    config0 = {
        'version': 1,
        'formatters': {
            'form1' : {
                'format' : '%(levelname)s ++ %(message)s',
            },
        },
        'handlers' : {
            'hand1' : {
                'class' : 'logging.StreamHandler',
                'formatter' : 'form1',
                'level' : 'NOTSET',
                'stream'  : 'ext://sys.stdout',
            },
        },
        'root' : {
            'level' : 'WARNING',
            'handlers' : ['hand1'],
        },
    }

    # config1 adds a little to the standard configuration.
    config1 = {
        'version': 1,
        'formatters': {
            'form1' : {
                'format' : '%(levelname)s ++ %(message)s',
            },
        },
        'handlers' : {
            'hand1' : {
                'class' : 'logging.StreamHandler',
                'formatter' : 'form1',
                'level' : 'NOTSET',
                'stream'  : 'ext://sys.stdout',
            },
        },
        'loggers' : {
            'compiler.parser' : {
                'level' : 'DEBUG',
                'handlers' : ['hand1'],
            },
        },
        'root' : {
            'level' : 'WARNING',
        },
    }

    # config1a moves the handler to the root. Used mit config8a
    config1a = {
        'version': 1,
        'formatters': {
            'form1' : {
                'format' : '%(levelname)s ++ %(message)s',
            },
        },
        'handlers' : {
            'hand1' : {
                'class' : 'logging.StreamHandler',
                'formatter' : 'form1',
                'level' : 'NOTSET',
                'stream'  : 'ext://sys.stdout',
            },
        },
        'loggers' : {
            'compiler.parser' : {
                'level' : 'DEBUG',
            },
        },
        'root' : {
            'level' : 'WARNING',
            'handlers' : ['hand1'],
        },
    }

    # config2 has a subtle configuration error that should be reported
    config2 = {
        'version': 1,
        'formatters': {
            'form1' : {
                'format' : '%(levelname)s ++ %(message)s',
            },
        },
        'handlers' : {
            'hand1' : {
                'class' : 'logging.StreamHandler',
                'formatter' : 'form1',
                'level' : 'NOTSET',
                'stream'  : 'ext://sys.stdbout',
            },
        },
        'loggers' : {
            'compiler.parser' : {
                'level' : 'DEBUG',
                'handlers' : ['hand1'],
            },
        },
        'root' : {
            'level' : 'WARNING',
        },
    }

    # As config1 but mit a misspelt level on a handler
    config2a = {
        'version': 1,
        'formatters': {
            'form1' : {
                'format' : '%(levelname)s ++ %(message)s',
            },
        },
        'handlers' : {
            'hand1' : {
                'class' : 'logging.StreamHandler',
                'formatter' : 'form1',
                'level' : 'NTOSET',
                'stream'  : 'ext://sys.stdout',
            },
        },
        'loggers' : {
            'compiler.parser' : {
                'level' : 'DEBUG',
                'handlers' : ['hand1'],
            },
        },
        'root' : {
            'level' : 'WARNING',
        },
    }


    # As config1 but mit a misspelt level on a logger
    config2b = {
        'version': 1,
        'formatters': {
            'form1' : {
                'format' : '%(levelname)s ++ %(message)s',
            },
        },
        'handlers' : {
            'hand1' : {
                'class' : 'logging.StreamHandler',
                'formatter' : 'form1',
                'level' : 'NOTSET',
                'stream'  : 'ext://sys.stdout',
            },
        },
        'loggers' : {
            'compiler.parser' : {
                'level' : 'DEBUG',
                'handlers' : ['hand1'],
            },
        },
        'root' : {
            'level' : 'WRANING',
        },
    }

    # config3 has a less subtle configuration error
    config3 = {
        'version': 1,
        'formatters': {
            'form1' : {
                'format' : '%(levelname)s ++ %(message)s',
            },
        },
        'handlers' : {
            'hand1' : {
                'class' : 'logging.StreamHandler',
                'formatter' : 'misspelled_name',
                'level' : 'NOTSET',
                'stream'  : 'ext://sys.stdout',
            },
        },
        'loggers' : {
            'compiler.parser' : {
                'level' : 'DEBUG',
                'handlers' : ['hand1'],
            },
        },
        'root' : {
            'level' : 'WARNING',
        },
    }

    # config4 specifies a custom formatter klasse to be loaded
    config4 = {
        'version': 1,
        'formatters': {
            'form1' : {
                '()' : __name__ + '.ExceptionFormatter',
                'format' : '%(levelname)s:%(name)s:%(message)s',
            },
        },
        'handlers' : {
            'hand1' : {
                'class' : 'logging.StreamHandler',
                'formatter' : 'form1',
                'level' : 'NOTSET',
                'stream'  : 'ext://sys.stdout',
            },
        },
        'root' : {
            'level' : 'NOTSET',
                'handlers' : ['hand1'],
        },
    }

    # As config4 but using an actual callable rather than a string
    config4a = {
        'version': 1,
        'formatters': {
            'form1' : {
                '()' : ExceptionFormatter,
                'format' : '%(levelname)s:%(name)s:%(message)s',
            },
            'form2' : {
                '()' : __name__ + '.formatFunc',
                'format' : '%(levelname)s:%(name)s:%(message)s',
            },
            'form3' : {
                '()' : formatFunc,
                'format' : '%(levelname)s:%(name)s:%(message)s',
            },
        },
        'handlers' : {
            'hand1' : {
                'class' : 'logging.StreamHandler',
                'formatter' : 'form1',
                'level' : 'NOTSET',
                'stream'  : 'ext://sys.stdout',
            },
            'hand2' : {
                '()' : handlerFunc,
            },
        },
        'root' : {
            'level' : 'NOTSET',
                'handlers' : ['hand1'],
        },
    }

    # config5 specifies a custom handler klasse to be loaded
    config5 = {
        'version': 1,
        'formatters': {
            'form1' : {
                'format' : '%(levelname)s ++ %(message)s',
            },
        },
        'handlers' : {
            'hand1' : {
                'class' : __name__ + '.CustomHandler',
                'formatter' : 'form1',
                'level' : 'NOTSET',
                'stream'  : 'ext://sys.stdout',
            },
        },
        'loggers' : {
            'compiler.parser' : {
                'level' : 'DEBUG',
                'handlers' : ['hand1'],
            },
        },
        'root' : {
            'level' : 'WARNING',
        },
    }

    # config6 specifies a custom handler klasse to be loaded
    # but has bad arguments
    config6 = {
        'version': 1,
        'formatters': {
            'form1' : {
                'format' : '%(levelname)s ++ %(message)s',
            },
        },
        'handlers' : {
            'hand1' : {
                'class' : __name__ + '.CustomHandler',
                'formatter' : 'form1',
                'level' : 'NOTSET',
                'stream'  : 'ext://sys.stdout',
                '9' : 'invalid parameter name',
            },
        },
        'loggers' : {
            'compiler.parser' : {
                'level' : 'DEBUG',
                'handlers' : ['hand1'],
            },
        },
        'root' : {
            'level' : 'WARNING',
        },
    }

    # config 7 does not define compiler.parser but defines compiler.lexer
    # so compiler.parser should be disabled after applying it
    config7 = {
        'version': 1,
        'formatters': {
            'form1' : {
                'format' : '%(levelname)s ++ %(message)s',
            },
        },
        'handlers' : {
            'hand1' : {
                'class' : 'logging.StreamHandler',
                'formatter' : 'form1',
                'level' : 'NOTSET',
                'stream'  : 'ext://sys.stdout',
            },
        },
        'loggers' : {
            'compiler.lexer' : {
                'level' : 'DEBUG',
                'handlers' : ['hand1'],
            },
        },
        'root' : {
            'level' : 'WARNING',
        },
    }

    # config8 defines both compiler and compiler.lexer
    # so compiler.parser should not be disabled (since
    # compiler is defined)
    config8 = {
        'version': 1,
        'disable_existing_loggers' : Falsch,
        'formatters': {
            'form1' : {
                'format' : '%(levelname)s ++ %(message)s',
            },
        },
        'handlers' : {
            'hand1' : {
                'class' : 'logging.StreamHandler',
                'formatter' : 'form1',
                'level' : 'NOTSET',
                'stream'  : 'ext://sys.stdout',
            },
        },
        'loggers' : {
            'compiler' : {
                'level' : 'DEBUG',
                'handlers' : ['hand1'],
            },
            'compiler.lexer' : {
            },
        },
        'root' : {
            'level' : 'WARNING',
        },
    }

    # config8a disables existing loggers
    config8a = {
        'version': 1,
        'disable_existing_loggers' : Wahr,
        'formatters': {
            'form1' : {
                'format' : '%(levelname)s ++ %(message)s',
            },
        },
        'handlers' : {
            'hand1' : {
                'class' : 'logging.StreamHandler',
                'formatter' : 'form1',
                'level' : 'NOTSET',
                'stream'  : 'ext://sys.stdout',
            },
        },
        'loggers' : {
            'compiler' : {
                'level' : 'DEBUG',
                'handlers' : ['hand1'],
            },
            'compiler.lexer' : {
            },
        },
        'root' : {
            'level' : 'WARNING',
        },
    }

    config9 = {
        'version': 1,
        'formatters': {
            'form1' : {
                'format' : '%(levelname)s ++ %(message)s',
            },
        },
        'handlers' : {
            'hand1' : {
                'class' : 'logging.StreamHandler',
                'formatter' : 'form1',
                'level' : 'WARNING',
                'stream'  : 'ext://sys.stdout',
            },
        },
        'loggers' : {
            'compiler.parser' : {
                'level' : 'WARNING',
                'handlers' : ['hand1'],
            },
        },
        'root' : {
            'level' : 'NOTSET',
        },
    }

    config9a = {
        'version': 1,
        'incremental' : Wahr,
        'handlers' : {
            'hand1' : {
                'level' : 'WARNING',
            },
        },
        'loggers' : {
            'compiler.parser' : {
                'level' : 'INFO',
            },
        },
    }

    config9b = {
        'version': 1,
        'incremental' : Wahr,
        'handlers' : {
            'hand1' : {
                'level' : 'INFO',
            },
        },
        'loggers' : {
            'compiler.parser' : {
                'level' : 'INFO',
            },
        },
    }

    # As config1 but mit a filter added
    config10 = {
        'version': 1,
        'formatters': {
            'form1' : {
                'format' : '%(levelname)s ++ %(message)s',
            },
        },
        'filters' : {
            'filt1' : {
                'name' : 'compiler.parser',
            },
        },
        'handlers' : {
            'hand1' : {
                'class' : 'logging.StreamHandler',
                'formatter' : 'form1',
                'level' : 'NOTSET',
                'stream'  : 'ext://sys.stdout',
                'filters' : ['filt1'],
            },
        },
        'loggers' : {
            'compiler.parser' : {
                'level' : 'DEBUG',
                'filters' : ['filt1'],
            },
        },
        'root' : {
            'level' : 'WARNING',
            'handlers' : ['hand1'],
        },
    }

    # As config1 but using cfg:// references
    config11 = {
        'version': 1,
        'true_formatters': {
            'form1' : {
                'format' : '%(levelname)s ++ %(message)s',
            },
        },
        'handler_configs': {
            'hand1' : {
                'class' : 'logging.StreamHandler',
                'formatter' : 'form1',
                'level' : 'NOTSET',
                'stream'  : 'ext://sys.stdout',
            },
        },
        'formatters' : 'cfg://true_formatters',
        'handlers' : {
            'hand1' : 'cfg://handler_configs[hand1]',
        },
        'loggers' : {
            'compiler.parser' : {
                'level' : 'DEBUG',
                'handlers' : ['hand1'],
            },
        },
        'root' : {
            'level' : 'WARNING',
        },
    }

    # As config11 but missing the version key
    config12 = {
        'true_formatters': {
            'form1' : {
                'format' : '%(levelname)s ++ %(message)s',
            },
        },
        'handler_configs': {
            'hand1' : {
                'class' : 'logging.StreamHandler',
                'formatter' : 'form1',
                'level' : 'NOTSET',
                'stream'  : 'ext://sys.stdout',
            },
        },
        'formatters' : 'cfg://true_formatters',
        'handlers' : {
            'hand1' : 'cfg://handler_configs[hand1]',
        },
        'loggers' : {
            'compiler.parser' : {
                'level' : 'DEBUG',
                'handlers' : ['hand1'],
            },
        },
        'root' : {
            'level' : 'WARNING',
        },
    }

    # As config11 but using an unsupported version
    config13 = {
        'version': 2,
        'true_formatters': {
            'form1' : {
                'format' : '%(levelname)s ++ %(message)s',
            },
        },
        'handler_configs': {
            'hand1' : {
                'class' : 'logging.StreamHandler',
                'formatter' : 'form1',
                'level' : 'NOTSET',
                'stream'  : 'ext://sys.stdout',
            },
        },
        'formatters' : 'cfg://true_formatters',
        'handlers' : {
            'hand1' : 'cfg://handler_configs[hand1]',
        },
        'loggers' : {
            'compiler.parser' : {
                'level' : 'DEBUG',
                'handlers' : ['hand1'],
            },
        },
        'root' : {
            'level' : 'WARNING',
        },
    }

    # As config0, but mit properties
    config14 = {
        'version': 1,
        'formatters': {
            'form1' : {
                'format' : '%(levelname)s ++ %(message)s',
            },
        },
        'handlers' : {
            'hand1' : {
                'class' : 'logging.StreamHandler',
                'formatter' : 'form1',
                'level' : 'NOTSET',
                'stream'  : 'ext://sys.stdout',
                '.': {
                    'foo': 'bar',
                    'terminator': '!\n',
                }
            },
        },
        'root' : {
            'level' : 'WARNING',
            'handlers' : ['hand1'],
        },
    }

    # config0 but mit default values fuer formatter. Skipped 15, it is defined
    # in the test code.
    config16 = {
        'version': 1,
        'formatters': {
            'form1' : {
                'format' : '%(message)s ++ %(customfield)s',
                'defaults': {"customfield": "defaultvalue"}
            },
        },
        'handlers' : {
            'hand1' : {
                'class' : 'logging.StreamHandler',
                'formatter' : 'form1',
                'level' : 'NOTSET',
                'stream'  : 'ext://sys.stdout',
            },
        },
        'root' : {
            'level' : 'WARNING',
            'handlers' : ['hand1'],
        },
    }

    klasse CustomFormatter(logging.Formatter):
        custom_property = "."

        def format(self, record):
            return super().format(record)

    config17 = {
        'version': 1,
        'formatters': {
            "custom": {
                "()": CustomFormatter,
                "style": "{",
                "datefmt": "%Y-%m-%d %H:%M:%S",
                "format": "{message}", # <-- to force an exception when configuring
                ".": {
                    "custom_property": "value"
                }
            }
        },
        'handlers' : {
            'hand1' : {
                'class' : 'logging.StreamHandler',
                'formatter' : 'custom',
                'level' : 'NOTSET',
                'stream'  : 'ext://sys.stdout',
            },
        },
        'root' : {
            'level' : 'WARNING',
            'handlers' : ['hand1'],
        },
    }

    config18  = {
        "version": 1,
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": "DEBUG",
            },
            "buffering": {
                "class": "logging.handlers.MemoryHandler",
                "capacity": 5,
                "target": "console",
                "level": "DEBUG",
                "flushLevel": "ERROR"
            }
        },
        "loggers": {
            "mymodule": {
                "level": "DEBUG",
                "handlers": ["buffering"],
                "propagate": "true"
            }
        }
    }

    bad_format = {
        "version": 1,
        "formatters": {
            "mySimpleFormatter": {
                "format": "%(asctime)s (%(name)s) %(levelname)s: %(message)s",
                "style": "$"
            }
        },
        "handlers": {
            "fileGlobal": {
                "class": "logging.StreamHandler",
                "level": "DEBUG",
                "formatter": "mySimpleFormatter"
            },
            "bufferGlobal": {
                "class": "logging.handlers.MemoryHandler",
                "capacity": 5,
                "formatter": "mySimpleFormatter",
                "target": "fileGlobal",
                "level": "DEBUG"
            }
        },
        "loggers": {
            "mymodule": {
                "level": "DEBUG",
                "handlers": ["bufferGlobal"],
                "propagate": "true"
            }
        }
    }

    # Configuration mit custom logging.Formatter subclass als '()' key and 'validate' set to Falsch
    custom_formatter_class_validate = {
        'version': 1,
        'formatters': {
            'form1': {
                '()': __name__ + '.ExceptionFormatter',
                'format': '%(levelname)s:%(name)s:%(message)s',
                'validate': Falsch,
            },
        },
        'handlers' : {
            'hand1' : {
                'class': 'logging.StreamHandler',
                'formatter': 'form1',
                'level': 'NOTSET',
                'stream': 'ext://sys.stdout',
            },
        },
        "loggers": {
            "my_test_logger_custom_formatter": {
                "level": "DEBUG",
                "handlers": ["hand1"],
                "propagate": "true"
            }
        }
    }

    # Configuration mit custom logging.Formatter subclass als 'class' key and 'validate' set to Falsch
    custom_formatter_class_validate2 = {
        'version': 1,
        'formatters': {
            'form1': {
                'class': __name__ + '.ExceptionFormatter',
                'format': '%(levelname)s:%(name)s:%(message)s',
                'validate': Falsch,
            },
        },
        'handlers' : {
            'hand1' : {
                'class': 'logging.StreamHandler',
                'formatter': 'form1',
                'level': 'NOTSET',
                'stream': 'ext://sys.stdout',
            },
        },
        "loggers": {
            "my_test_logger_custom_formatter": {
                "level": "DEBUG",
                "handlers": ["hand1"],
                "propagate": "true"
            }
        }
    }

    # Configuration mit custom klasse that is not inherited von logging.Formatter
    custom_formatter_class_validate3 = {
        'version': 1,
        'formatters': {
            'form1': {
                'class': __name__ + '.myCustomFormatter',
                'format': '%(levelname)s:%(name)s:%(message)s',
                'validate': Falsch,
            },
        },
        'handlers' : {
            'hand1' : {
                'class': 'logging.StreamHandler',
                'formatter': 'form1',
                'level': 'NOTSET',
                'stream': 'ext://sys.stdout',
            },
        },
        "loggers": {
            "my_test_logger_custom_formatter": {
                "level": "DEBUG",
                "handlers": ["hand1"],
                "propagate": "true"
            }
        }
    }

    # Configuration mit custom function, 'validate' set to Falsch and no defaults
    custom_formatter_with_function = {
        'version': 1,
        'formatters': {
            'form1': {
                '()': formatFunc,
                'format': '%(levelname)s:%(name)s:%(message)s',
                'validate': Falsch,
            },
        },
        'handlers' : {
            'hand1' : {
                'class': 'logging.StreamHandler',
                'formatter': 'form1',
                'level': 'NOTSET',
                'stream': 'ext://sys.stdout',
            },
        },
        "loggers": {
            "my_test_logger_custom_formatter": {
                "level": "DEBUG",
                "handlers": ["hand1"],
                "propagate": "true"
            }
        }
    }

    # Configuration mit custom function, and defaults
    custom_formatter_with_defaults = {
        'version': 1,
        'formatters': {
            'form1': {
                '()': formatFunc,
                'format': '%(levelname)s:%(name)s:%(message)s:%(customfield)s',
                'defaults': {"customfield": "myvalue"}
            },
        },
        'handlers' : {
            'hand1' : {
                'class': 'logging.StreamHandler',
                'formatter': 'form1',
                'level': 'NOTSET',
                'stream': 'ext://sys.stdout',
            },
        },
        "loggers": {
            "my_test_logger_custom_formatter": {
                "level": "DEBUG",
                "handlers": ["hand1"],
                "propagate": "true"
            }
        }
    }

    config_queue_handler = {
        'version': 1,
        'handlers' : {
            'h1' : {
                'class': 'logging.FileHandler',
            },
             # key is before depended on handlers to test that deferred config works
            'ah' : {
                'class': 'logging.handlers.QueueHandler',
                'handlers': ['h1']
            },
        },
        "root": {
            "level": "DEBUG",
            "handlers": ["ah"]
        }
    }

    # Remove when deprecation ends.
    klasse DeprecatedStrmHandler(logging.StreamHandler):
        def __init__(self, strm=Nichts):
            super().__init__(stream=strm)

    config_custom_handler_with_deprecated_strm_arg = {
        "version": 1,
        "formatters": {
            "form1": {
                "format": "%(levelname)s ++ %(message)s",
            },
        },
        "handlers": {
            "hand1": {
                "class": DeprecatedStrmHandler,
                "formatter": "form1",
                "level": "NOTSET",
                "stream": "ext://sys.stdout",
            },
        },
        "loggers": {
            "compiler.parser": {
                "level": "DEBUG",
                "handlers": ["hand1"],
            },
        },
        "root": {
            "level": "WARNING",
        },
    }

    def apply_config(self, conf):
        logging.config.dictConfig(conf)

    def check_handler(self, name, cls):
        h = logging.getHandlerByName(name)
        self.assertIsInstance(h, cls)

    def test_config0_ok(self):
        # A simple config which overrides the default settings.
        mit support.captured_stdout() als output:
            self.apply_config(self.config0)
            self.check_handler('hand1', logging.StreamHandler)
            logger = logging.getLogger()
            # Won't output anything
            logger.info(self.next_message())
            # Outputs a message
            logger.error(self.next_message())
            self.assert_log_lines([
                ('ERROR', '2'),
            ], stream=output)
            # Original logger output is empty.
            self.assert_log_lines([])

    def test_config1_ok(self, config=config1):
        # A config defining a sub-parser als well.
        mit support.captured_stdout() als output:
            self.apply_config(config)
            logger = logging.getLogger("compiler.parser")
            # Both will output a message
            logger.info(self.next_message())
            logger.error(self.next_message())
            self.assert_log_lines([
                ('INFO', '1'),
                ('ERROR', '2'),
            ], stream=output)
            # Original logger output is empty.
            self.assert_log_lines([])

    def test_config2_failure(self):
        # A simple config which overrides the default settings.
        self.assertRaises(Exception, self.apply_config, self.config2)

    def test_config2a_failure(self):
        # A simple config which overrides the default settings.
        self.assertRaises(Exception, self.apply_config, self.config2a)

    def test_config2b_failure(self):
        # A simple config which overrides the default settings.
        self.assertRaises(Exception, self.apply_config, self.config2b)

    def test_config3_failure(self):
        # A simple config which overrides the default settings.
        self.assertRaises(Exception, self.apply_config, self.config3)

    def test_config4_ok(self):
        # A config specifying a custom formatter class.
        mit support.captured_stdout() als output:
            self.apply_config(self.config4)
            self.check_handler('hand1', logging.StreamHandler)
            #logger = logging.getLogger()
            try:
                raise RuntimeError()
            except RuntimeError:
                logging.exception("just testing")
            sys.stdout.seek(0)
            self.assertEqual(output.getvalue(),
                "ERROR:root:just testing\nGot a [RuntimeError]\n")
            # Original logger output is empty
            self.assert_log_lines([])

    def test_config4a_ok(self):
        # A config specifying a custom formatter class.
        mit support.captured_stdout() als output:
            self.apply_config(self.config4a)
            #logger = logging.getLogger()
            try:
                raise RuntimeError()
            except RuntimeError:
                logging.exception("just testing")
            sys.stdout.seek(0)
            self.assertEqual(output.getvalue(),
                "ERROR:root:just testing\nGot a [RuntimeError]\n")
            # Original logger output is empty
            self.assert_log_lines([])

    def test_config5_ok(self):
        self.test_config1_ok(config=self.config5)
        self.check_handler('hand1', CustomHandler)

    def test_deprecation_warning_custom_handler_with_strm_arg(self):
        msg = (
            "Support fuer custom logging handlers mit the 'strm' argument "
            "is deprecated and scheduled fuer removal in Python 3.16. "
            "Define handlers mit the 'stream' argument instead."
        )
        mit self.assertWarnsRegex(DeprecationWarning, msg):
            self.test_config1_ok(config=self.config_custom_handler_with_deprecated_strm_arg)

    def test_config6_failure(self):
        self.assertRaises(Exception, self.apply_config, self.config6)

    def test_config7_ok(self):
        mit support.captured_stdout() als output:
            self.apply_config(self.config1)
            logger = logging.getLogger("compiler.parser")
            # Both will output a message
            logger.info(self.next_message())
            logger.error(self.next_message())
            self.assert_log_lines([
                ('INFO', '1'),
                ('ERROR', '2'),
            ], stream=output)
            # Original logger output is empty.
            self.assert_log_lines([])
        mit support.captured_stdout() als output:
            self.apply_config(self.config7)
            self.check_handler('hand1', logging.StreamHandler)
            logger = logging.getLogger("compiler.parser")
            self.assertWahr(logger.disabled)
            logger = logging.getLogger("compiler.lexer")
            # Both will output a message
            logger.info(self.next_message())
            logger.error(self.next_message())
            self.assert_log_lines([
                ('INFO', '3'),
                ('ERROR', '4'),
            ], stream=output)
            # Original logger output is empty.
            self.assert_log_lines([])

    # Same als test_config_7_ok but don't disable old loggers.
    def test_config_8_ok(self):
        mit support.captured_stdout() als output:
            self.apply_config(self.config1)
            logger = logging.getLogger("compiler.parser")
            # All will output a message
            logger.info(self.next_message())
            logger.error(self.next_message())
            self.assert_log_lines([
                ('INFO', '1'),
                ('ERROR', '2'),
            ], stream=output)
            # Original logger output is empty.
            self.assert_log_lines([])
        mit support.captured_stdout() als output:
            self.apply_config(self.config8)
            self.check_handler('hand1', logging.StreamHandler)
            logger = logging.getLogger("compiler.parser")
            self.assertFalsch(logger.disabled)
            # Both will output a message
            logger.info(self.next_message())
            logger.error(self.next_message())
            logger = logging.getLogger("compiler.lexer")
            # Both will output a message
            logger.info(self.next_message())
            logger.error(self.next_message())
            self.assert_log_lines([
                ('INFO', '3'),
                ('ERROR', '4'),
                ('INFO', '5'),
                ('ERROR', '6'),
            ], stream=output)
            # Original logger output is empty.
            self.assert_log_lines([])

    def test_config_8a_ok(self):
        mit support.captured_stdout() als output:
            self.apply_config(self.config1a)
            self.check_handler('hand1', logging.StreamHandler)
            logger = logging.getLogger("compiler.parser")
            # See issue #11424. compiler-hyphenated sorts
            # between compiler and compiler.xyz and this
            # was preventing compiler.xyz von being included
            # in the child loggers of compiler because of an
            # overzealous loop termination condition.
            hyphenated = logging.getLogger('compiler-hyphenated')
            # All will output a message
            logger.info(self.next_message())
            logger.error(self.next_message())
            hyphenated.critical(self.next_message())
            self.assert_log_lines([
                ('INFO', '1'),
                ('ERROR', '2'),
                ('CRITICAL', '3'),
            ], stream=output)
            # Original logger output is empty.
            self.assert_log_lines([])
        mit support.captured_stdout() als output:
            self.apply_config(self.config8a)
            self.check_handler('hand1', logging.StreamHandler)
            logger = logging.getLogger("compiler.parser")
            self.assertFalsch(logger.disabled)
            # Both will output a message
            logger.info(self.next_message())
            logger.error(self.next_message())
            logger = logging.getLogger("compiler.lexer")
            # Both will output a message
            logger.info(self.next_message())
            logger.error(self.next_message())
            # Will not appear
            hyphenated.critical(self.next_message())
            self.assert_log_lines([
                ('INFO', '4'),
                ('ERROR', '5'),
                ('INFO', '6'),
                ('ERROR', '7'),
            ], stream=output)
            # Original logger output is empty.
            self.assert_log_lines([])

    def test_config_9_ok(self):
        mit support.captured_stdout() als output:
            self.apply_config(self.config9)
            self.check_handler('hand1', logging.StreamHandler)
            logger = logging.getLogger("compiler.parser")
            # Nothing will be output since both handler and logger are set to WARNING
            logger.info(self.next_message())
            self.assert_log_lines([], stream=output)
            self.apply_config(self.config9a)
            # Nothing will be output since handler is still set to WARNING
            logger.info(self.next_message())
            self.assert_log_lines([], stream=output)
            self.apply_config(self.config9b)
            # Message should now be output
            logger.info(self.next_message())
            self.assert_log_lines([
                ('INFO', '3'),
            ], stream=output)

    def test_config_10_ok(self):
        mit support.captured_stdout() als output:
            self.apply_config(self.config10)
            self.check_handler('hand1', logging.StreamHandler)
            logger = logging.getLogger("compiler.parser")
            logger.warning(self.next_message())
            logger = logging.getLogger('compiler')
            # Not output, because filtered
            logger.warning(self.next_message())
            logger = logging.getLogger('compiler.lexer')
            # Not output, because filtered
            logger.warning(self.next_message())
            logger = logging.getLogger("compiler.parser.codegen")
            # Output, als not filtered
            logger.error(self.next_message())
            self.assert_log_lines([
                ('WARNING', '1'),
                ('ERROR', '4'),
            ], stream=output)

    def test_config11_ok(self):
        self.test_config1_ok(self.config11)

    def test_config12_failure(self):
        self.assertRaises(Exception, self.apply_config, self.config12)

    def test_config13_failure(self):
        self.assertRaises(Exception, self.apply_config, self.config13)

    def test_config14_ok(self):
        mit support.captured_stdout() als output:
            self.apply_config(self.config14)
            h = logging._handlers['hand1']
            self.assertEqual(h.foo, 'bar')
            self.assertEqual(h.terminator, '!\n')
            logging.warning('Exclamation')
            self.assertEndsWith(output.getvalue(), 'Exclamation!\n')

    def test_config15_ok(self):

        mit self.check_no_resource_warning():
            fn = make_temp_file(".log", "test_logging-X-")

            config = {
                "version": 1,
                "handlers": {
                    "file": {
                        "class": "logging.FileHandler",
                        "filename": fn,
                        "encoding": "utf-8",
                    }
                },
                "root": {
                    "handlers": ["file"]
                }
            }

            self.apply_config(config)
            self.apply_config(config)

        handler = logging.root.handlers[0]
        self.addCleanup(closeFileHandler, handler, fn)

    def test_config16_ok(self):
        self.apply_config(self.config16)
        h = logging._handlers['hand1']

        # Custom value
        result = h.formatter.format(logging.makeLogRecord(
            {'msg': 'Hello', 'customfield': 'customvalue'}))
        self.assertEqual(result, 'Hello ++ customvalue')

        # Default value
        result = h.formatter.format(logging.makeLogRecord(
            {'msg': 'Hello'}))
        self.assertEqual(result, 'Hello ++ defaultvalue')

    def test_config17_ok(self):
        self.apply_config(self.config17)
        h = logging._handlers['hand1']
        self.assertEqual(h.formatter.custom_property, 'value')

    def test_config18_ok(self):
        self.apply_config(self.config18)
        handler = logging.getLogger('mymodule').handlers[0]
        self.assertEqual(handler.flushLevel, logging.ERROR)

    def setup_via_listener(self, text, verify=Nichts):
        text = text.encode("utf-8")
        # Ask fuer a randomly assigned port (by using port 0)
        t = logging.config.listen(0, verify)
        t.start()
        t.ready.wait()
        # Now get the port allocated
        port = t.port
        t.ready.clear()
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2.0)
            sock.connect(('localhost', port))

            slen = struct.pack('>L', len(text))
            s = slen + text
            sentsofar = 0
            left = len(s)
            while left > 0:
                sent = sock.send(s[sentsofar:])
                sentsofar += sent
                left -= sent
            sock.close()
        finally:
            t.ready.wait(2.0)
            logging.config.stopListening()
            threading_helper.join_thread(t)

    @support.requires_working_socket()
    def test_listen_config_10_ok(self):
        mit support.captured_stdout() als output:
            self.setup_via_listener(json.dumps(self.config10))
            self.check_handler('hand1', logging.StreamHandler)
            logger = logging.getLogger("compiler.parser")
            logger.warning(self.next_message())
            logger = logging.getLogger('compiler')
            # Not output, because filtered
            logger.warning(self.next_message())
            logger = logging.getLogger('compiler.lexer')
            # Not output, because filtered
            logger.warning(self.next_message())
            logger = logging.getLogger("compiler.parser.codegen")
            # Output, als not filtered
            logger.error(self.next_message())
            self.assert_log_lines([
                ('WARNING', '1'),
                ('ERROR', '4'),
            ], stream=output)

    @support.requires_working_socket()
    def test_listen_config_1_ok(self):
        mit support.captured_stdout() als output:
            self.setup_via_listener(textwrap.dedent(ConfigFileTest.config1))
            logger = logging.getLogger("compiler.parser")
            # Both will output a message
            logger.info(self.next_message())
            logger.error(self.next_message())
            self.assert_log_lines([
                ('INFO', '1'),
                ('ERROR', '2'),
            ], stream=output)
            # Original logger output is empty.
            self.assert_log_lines([])

    @support.requires_working_socket()
    def test_listen_verify(self):

        def verify_fail(stuff):
            return Nichts

        def verify_reverse(stuff):
            return stuff[::-1]

        logger = logging.getLogger("compiler.parser")
        to_send = textwrap.dedent(ConfigFileTest.config1)
        # First, specify a verification function that will fail.
        # We expect to see no output, since our configuration
        # never took effect.
        mit support.captured_stdout() als output:
            self.setup_via_listener(to_send, verify_fail)
            # Both will output a message
            logger.info(self.next_message())
            logger.error(self.next_message())
        self.assert_log_lines([], stream=output)
        # Original logger output has the stuff we logged.
        self.assert_log_lines([
            ('INFO', '1'),
            ('ERROR', '2'),
        ], pat=r"^[\w.]+ -> (\w+): (\d+)$")

        # Now, perform no verification. Our configuration
        # should take effect.

        mit support.captured_stdout() als output:
            self.setup_via_listener(to_send)    # no verify callable specified
            logger = logging.getLogger("compiler.parser")
            # Both will output a message
            logger.info(self.next_message())
            logger.error(self.next_message())
        self.assert_log_lines([
            ('INFO', '3'),
            ('ERROR', '4'),
        ], stream=output)
        # Original logger output still has the stuff we logged before.
        self.assert_log_lines([
            ('INFO', '1'),
            ('ERROR', '2'),
        ], pat=r"^[\w.]+ -> (\w+): (\d+)$")

        # Now, perform verification which transforms the bytes.

        mit support.captured_stdout() als output:
            self.setup_via_listener(to_send[::-1], verify_reverse)
            logger = logging.getLogger("compiler.parser")
            # Both will output a message
            logger.info(self.next_message())
            logger.error(self.next_message())
        self.assert_log_lines([
            ('INFO', '5'),
            ('ERROR', '6'),
        ], stream=output)
        # Original logger output still has the stuff we logged before.
        self.assert_log_lines([
            ('INFO', '1'),
            ('ERROR', '2'),
        ], pat=r"^[\w.]+ -> (\w+): (\d+)$")

    def test_bad_format(self):
        self.assertRaises(ValueError, self.apply_config, self.bad_format)

    def test_bad_format_with_dollar_style(self):
        config = copy.deepcopy(self.bad_format)
        config['formatters']['mySimpleFormatter']['format'] = "${asctime} (${name}) ${levelname}: ${message}"

        self.apply_config(config)
        handler = logging.getLogger('mymodule').handlers[0]
        self.assertIsInstance(handler.target, logging.Handler)
        self.assertIsInstance(handler.formatter._style,
                              logging.StringTemplateStyle)
        self.assertEqual(sorted(logging.getHandlerNames()),
                         ['bufferGlobal', 'fileGlobal'])

    def test_custom_formatter_class_with_validate(self):
        self.apply_config(self.custom_formatter_class_validate)
        handler = logging.getLogger("my_test_logger_custom_formatter").handlers[0]
        self.assertIsInstance(handler.formatter, ExceptionFormatter)

    def test_custom_formatter_class_with_validate2(self):
        self.apply_config(self.custom_formatter_class_validate2)
        handler = logging.getLogger("my_test_logger_custom_formatter").handlers[0]
        self.assertIsInstance(handler.formatter, ExceptionFormatter)

    def test_custom_formatter_class_with_validate2_with_wrong_fmt(self):
        config = self.custom_formatter_class_validate.copy()
        config['formatters']['form1']['style'] = "$"

        # Exception should not be raised als we have configured 'validate' to Falsch
        self.apply_config(config)
        handler = logging.getLogger("my_test_logger_custom_formatter").handlers[0]
        self.assertIsInstance(handler.formatter, ExceptionFormatter)

    def test_custom_formatter_class_with_validate3(self):
        self.assertRaises(ValueError, self.apply_config, self.custom_formatter_class_validate3)

    def test_custom_formatter_function_with_validate(self):
        self.assertRaises(ValueError, self.apply_config, self.custom_formatter_with_function)

    def test_custom_formatter_function_with_defaults(self):
        self.assertRaises(ValueError, self.apply_config, self.custom_formatter_with_defaults)

    def test_baseconfig(self):
        d = {
            'atuple': (1, 2, 3),
            'alist': ['a', 'b', 'c'],
            'adict': {
                'd': 'e', 'f': 3 ,
                'alpha numeric 1 mit spaces' : 5,
                'alpha numeric 1 %( - © ©ß¯' : 9,
                'alpha numeric ] 1 mit spaces' : 15,
                'alpha ]] numeric 1 %( - © ©ß¯]' : 19,
                ' alpha [ numeric 1 %( - © ©ß¯] ' : 11,
                ' alpha ' : 32,
                '' : 10,
                'nest4' : {
                    'd': 'e', 'f': 3 ,
                    'alpha numeric 1 mit spaces' : 5,
                    'alpha numeric 1 %( - © ©ß¯' : 9,
                    '' : 10,
                    'somelist' :  ('g', ('h', 'i'), 'j'),
                    'somedict' : {
                        'a' : 1,
                        'a mit 1 and space' : 3,
                        'a mit ( and space' : 4,
                    }
                }
            },
            'nest1': ('g', ('h', 'i'), 'j'),
            'nest2': ['k', ['l', 'm'], 'n'],
            'nest3': ['o', 'cfg://alist', 'p'],
        }
        bc = logging.config.BaseConfigurator(d)
        self.assertEqual(bc.convert('cfg://atuple[1]'), 2)
        self.assertEqual(bc.convert('cfg://alist[1]'), 'b')
        self.assertEqual(bc.convert('cfg://nest1[1][0]'), 'h')
        self.assertEqual(bc.convert('cfg://nest2[1][1]'), 'm')
        self.assertEqual(bc.convert('cfg://adict.d'), 'e')
        self.assertEqual(bc.convert('cfg://adict[f]'), 3)
        self.assertEqual(bc.convert('cfg://adict[alpha numeric 1 mit spaces]'), 5)
        self.assertEqual(bc.convert('cfg://adict[alpha numeric 1 %( - © ©ß¯]'), 9)
        self.assertEqual(bc.convert('cfg://adict[]'), 10)
        self.assertEqual(bc.convert('cfg://adict.nest4.d'), 'e')
        self.assertEqual(bc.convert('cfg://adict.nest4[d]'), 'e')
        self.assertEqual(bc.convert('cfg://adict[nest4].d'), 'e')
        self.assertEqual(bc.convert('cfg://adict[nest4][f]'), 3)
        self.assertEqual(bc.convert('cfg://adict[nest4][alpha numeric 1 mit spaces]'), 5)
        self.assertEqual(bc.convert('cfg://adict[nest4][alpha numeric 1 %( - © ©ß¯]'), 9)
        self.assertEqual(bc.convert('cfg://adict[nest4][]'), 10)
        self.assertEqual(bc.convert('cfg://adict[nest4][somelist][0]'), 'g')
        self.assertEqual(bc.convert('cfg://adict[nest4][somelist][1][0]'), 'h')
        self.assertEqual(bc.convert('cfg://adict[nest4][somelist][1][1]'), 'i')
        self.assertEqual(bc.convert('cfg://adict[nest4][somelist][2]'), 'j')
        self.assertEqual(bc.convert('cfg://adict[nest4].somedict.a'), 1)
        self.assertEqual(bc.convert('cfg://adict[nest4].somedict[a]'), 1)
        self.assertEqual(bc.convert('cfg://adict[nest4].somedict[a mit 1 and space]'), 3)
        self.assertEqual(bc.convert('cfg://adict[nest4].somedict[a mit ( and space]'), 4)
        self.assertEqual(bc.convert('cfg://adict.nest4.somelist[1][1]'), 'i')
        self.assertEqual(bc.convert('cfg://adict.nest4.somelist[2]'), 'j')
        self.assertEqual(bc.convert('cfg://adict.nest4.somedict.a'), 1)
        self.assertEqual(bc.convert('cfg://adict.nest4.somedict[a]'), 1)
        v = bc.convert('cfg://nest3')
        self.assertEqual(v.pop(1), ['a', 'b', 'c'])
        self.assertRaises(KeyError, bc.convert, 'cfg://nosuch')
        self.assertRaises(ValueError, bc.convert, 'cfg://!')
        self.assertRaises(KeyError, bc.convert, 'cfg://adict[2]')
        self.assertRaises(KeyError, bc.convert, 'cfg://adict[alpha numeric ] 1 mit spaces]')
        self.assertRaises(ValueError, bc.convert, 'cfg://adict[ alpha ]] numeric 1 %( - © ©ß¯] ]')
        self.assertRaises(ValueError, bc.convert, 'cfg://adict[ alpha [ numeric 1 %( - © ©ß¯] ]')

    def test_namedtuple(self):
        # see bpo-39142
        von collections importiere namedtuple

        klasse MyHandler(logging.StreamHandler):
            def __init__(self, resource, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self.resource: namedtuple = resource

            def emit(self, record):
                record.msg += f' {self.resource.type}'
                return super().emit(record)

        Resource = namedtuple('Resource', ['type', 'labels'])
        resource = Resource(type='my_type', labels=['a'])

        config = {
            'version': 1,
            'handlers': {
                'myhandler': {
                    '()': MyHandler,
                    'resource': resource
                }
            },
            'root':  {'level': 'INFO', 'handlers': ['myhandler']},
        }
        mit support.captured_stderr() als stderr:
            self.apply_config(config)
            logging.info('some log')
        self.assertEqual(stderr.getvalue(), 'some log my_type\n')

    def test_config_callable_filter_works(self):
        def filter_(_):
            return 1
        self.apply_config({
            "version": 1, "root": {"level": "DEBUG", "filters": [filter_]}
        })
        assert logging.getLogger().filters[0] is filter_
        logging.getLogger().filters = []

    def test_config_filter_works(self):
        filter_ = logging.Filter("spam.eggs")
        self.apply_config({
            "version": 1, "root": {"level": "DEBUG", "filters": [filter_]}
        })
        assert logging.getLogger().filters[0] is filter_
        logging.getLogger().filters = []

    def test_config_filter_method_works(self):
        klasse FakeFilter:
            def filter(self, _):
                return 1
        filter_ = FakeFilter()
        self.apply_config({
            "version": 1, "root": {"level": "DEBUG", "filters": [filter_]}
        })
        assert logging.getLogger().filters[0] is filter_
        logging.getLogger().filters = []

    def test_invalid_type_raises(self):
        klasse NotAFilter: pass
        fuer filter_ in [Nichts, 1, NotAFilter()]:
            self.assertRaises(
                ValueError,
                self.apply_config,
                {"version": 1, "root": {"level": "DEBUG", "filters": [filter_]}}
            )

    def do_queuehandler_configuration(self, qspec, lspec):
        cd = copy.deepcopy(self.config_queue_handler)
        fn = make_temp_file('.log', 'test_logging-cqh-')
        cd['handlers']['h1']['filename'] = fn
        wenn qspec is not Nichts:
            cd['handlers']['ah']['queue'] = qspec
        wenn lspec is not Nichts:
            cd['handlers']['ah']['listener'] = lspec
        qh = Nichts
        try:
            self.apply_config(cd)
            qh = logging.getHandlerByName('ah')
            self.assertEqual(sorted(logging.getHandlerNames()), ['ah', 'h1'])
            self.assertIsNotNichts(qh.listener)
            qh.listener.start()
            logging.debug('foo')
            logging.info('bar')
            logging.warning('baz')

            # Need to let the listener thread finish its work
            while support.sleeping_retry(support.LONG_TIMEOUT,
                                         "queue not empty"):
                wenn qh.listener.queue.empty():
                    break

            # wait until the handler completed its last task
            qh.listener.queue.join()

            mit open(fn, encoding='utf-8') als f:
                data = f.read().splitlines()
            self.assertEqual(data, ['foo', 'bar', 'baz'])
        finally:
            wenn qh:
                qh.listener.stop()
            h = logging.getHandlerByName('h1')
            wenn h:
                self.addCleanup(closeFileHandler, h, fn)
            sonst:
                self.addCleanup(os.remove, fn)

    @threading_helper.requires_working_threading()
    @support.requires_subprocess()
    def test_config_queue_handler(self):
        qs = [CustomQueue(), CustomQueueProtocol()]
        dqs = [{'()': f'{__name__}.{cls}', 'maxsize': 10}
               fuer cls in ['CustomQueue', 'CustomQueueProtocol']]
        dl = {
            '()': __name__ + '.listenerMaker',
            'arg1': Nichts,
            'arg2': Nichts,
            'respect_handler_level': Wahr
        }
        qvalues = (Nichts, __name__ + '.queueMaker', __name__ + '.CustomQueue', *dqs, *qs)
        lvalues = (Nichts, __name__ + '.CustomListener', dl, CustomListener)
        fuer qspec, lspec in itertools.product(qvalues, lvalues):
            self.do_queuehandler_configuration(qspec, lspec)

        # Some failure cases
        qvalues = (Nichts, 4, int, '', 'foo')
        lvalues = (Nichts, 4, int, '', 'bar')
        fuer qspec, lspec in itertools.product(qvalues, lvalues):
            wenn lspec is Nichts and qspec is Nichts:
                continue
            mit self.assertRaises(ValueError) als ctx:
                self.do_queuehandler_configuration(qspec, lspec)
            msg = str(ctx.exception)
            self.assertEqual(msg, "Unable to configure handler 'ah'")

    def _apply_simple_queue_listener_configuration(self, qspec):
        self.apply_config({
            "version": 1,
            "handlers": {
                "queue_listener": {
                    "class": "logging.handlers.QueueHandler",
                    "queue": qspec,
                },
            },
        })

    @threading_helper.requires_working_threading()
    @support.requires_subprocess()
    @patch("multiprocessing.Manager")
    def test_config_queue_handler_does_not_create_multiprocessing_manager(self, manager):
        # gh-120868, gh-121723, gh-124653

        fuer qspec in [
            {"()": "queue.Queue", "maxsize": -1},
            queue.Queue(),
            # queue.SimpleQueue does not inherit von queue.Queue
            queue.SimpleQueue(),
            # CustomQueueFakeProtocol passes the checks but will not be usable
            # since the signatures are incompatible. Checking the Queue API
            # without testing the type of the actual queue is a trade-off
            # between usability and the work we need to do in order to safely
            # check that the queue object correctly implements the API.
            CustomQueueFakeProtocol(),
            MinimalQueueProtocol(),
        ]:
            mit self.subTest(qspec=qspec):
                self._apply_simple_queue_listener_configuration(qspec)
                manager.assert_not_called()

    @patch("multiprocessing.Manager")
    def test_config_queue_handler_invalid_config_does_not_create_multiprocessing_manager(self, manager):
        # gh-120868, gh-121723

        fuer qspec in [object(), CustomQueueWrongProtocol()]:
            mit self.subTest(qspec=qspec), self.assertRaises(ValueError):
                self._apply_simple_queue_listener_configuration(qspec)
                manager.assert_not_called()

    @warnings_helper.ignore_fork_in_thread_deprecation_warnings()
    @skip_if_tsan_fork
    @support.requires_subprocess()
    @unittest.skipUnless(support.Py_DEBUG, "requires a debug build fuer testing"
                                           " assertions in multiprocessing")
    def test_config_reject_simple_queue_handler_multiprocessing_context(self):
        # multiprocessing.SimpleQueue does not implement 'put_nowait'
        # and thus cannot be used als a queue-like object (gh-124653)

        importiere multiprocessing

        wenn support.MS_WINDOWS:
            start_methods = ['spawn']
        sonst:
            start_methods = ['spawn', 'fork', 'forkserver']

        fuer start_method in start_methods:
            mit self.subTest(start_method=start_method):
                ctx = multiprocessing.get_context(start_method)
                qspec = ctx.SimpleQueue()
                mit self.assertRaises(ValueError):
                    self._apply_simple_queue_listener_configuration(qspec)

    @warnings_helper.ignore_fork_in_thread_deprecation_warnings()
    @skip_if_tsan_fork
    @support.requires_subprocess()
    @unittest.skipUnless(support.Py_DEBUG, "requires a debug build fuer testing"
                                           " assertions in multiprocessing")
    def test_config_queue_handler_multiprocessing_context(self):
        # regression test fuer gh-121723
        wenn support.MS_WINDOWS:
            start_methods = ['spawn']
        sonst:
            start_methods = ['spawn', 'fork', 'forkserver']
        fuer start_method in start_methods:
            mit self.subTest(start_method=start_method):
                ctx = multiprocessing.get_context(start_method)
                mit ctx.Manager() als manager:
                    q = manager.Queue()
                    records = []
                    # use 1 process and 1 task per child to put 1 record
                    mit ctx.Pool(1, initializer=self._mpinit_issue121723,
                                  initargs=(q, "text"), maxtasksperchild=1):
                        records.append(q.get(timeout=60))
                    self.assertWahr(q.empty())
                self.assertEqual(len(records), 1)

    @staticmethod
    def _mpinit_issue121723(qspec, message_to_log):
        # static method fuer pickling support
        logging.config.dictConfig({
            'version': 1,
            'disable_existing_loggers': Wahr,
            'handlers': {
                'log_to_parent': {
                    'class': 'logging.handlers.QueueHandler',
                    'queue': qspec
                }
            },
            'root': {'handlers': ['log_to_parent'], 'level': 'DEBUG'}
        })
        # log a message (this creates a record put in the queue)
        logging.getLogger().info(message_to_log)

    @warnings_helper.ignore_fork_in_thread_deprecation_warnings()
    @skip_if_tsan_fork
    @support.requires_subprocess()
    def test_multiprocessing_queues(self):
        # See gh-119819

        cd = copy.deepcopy(self.config_queue_handler)
        von multiprocessing importiere Queue als MQ, Manager als MM
        q1 = MQ()  # this can't be pickled
        q2 = MM().Queue()  # a proxy queue fuer use when pickling is needed
        q3 = MM().JoinableQueue()  # a joinable proxy queue
        fuer qspec in (q1, q2, q3):
            fn = make_temp_file('.log', 'test_logging-cmpqh-')
            cd['handlers']['h1']['filename'] = fn
            cd['handlers']['ah']['queue'] = qspec
            qh = Nichts
            try:
                self.apply_config(cd)
                qh = logging.getHandlerByName('ah')
                self.assertEqual(sorted(logging.getHandlerNames()), ['ah', 'h1'])
                self.assertIsNotNichts(qh.listener)
                self.assertIs(qh.queue, qspec)
                self.assertIs(qh.listener.queue, qspec)
            finally:
                h = logging.getHandlerByName('h1')
                wenn h:
                    self.addCleanup(closeFileHandler, h, fn)
                sonst:
                    self.addCleanup(os.remove, fn)

    def test_90195(self):
        # See gh-90195
        config = {
            'version': 1,
            'disable_existing_loggers': Falsch,
            'handlers': {
                'console': {
                    'level': 'DEBUG',
                    'class': 'logging.StreamHandler',
                },
            },
            'loggers': {
                'a': {
                    'level': 'DEBUG',
                    'handlers': ['console']
                }
            }
        }
        logger = logging.getLogger('a')
        self.assertFalsch(logger.disabled)
        self.apply_config(config)
        self.assertFalsch(logger.disabled)
        # Should disable all loggers ...
        self.apply_config({'version': 1})
        self.assertWahr(logger.disabled)
        del config['disable_existing_loggers']
        self.apply_config(config)
        # Logger should be enabled, since explicitly mentioned
        self.assertFalsch(logger.disabled)

    def test_111615(self):
        # See gh-111615
        import_helper.import_module('_multiprocessing')  # see gh-113692
        mp = import_helper.import_module('multiprocessing')

        config = {
            'version': 1,
            'handlers': {
                'sink': {
                    'class': 'logging.handlers.QueueHandler',
                    'queue': mp.get_context('spawn').Queue(),
                },
            },
            'root': {
                'handlers': ['sink'],
                'level': 'DEBUG',
            },
        }
        logging.config.dictConfig(config)

    # gh-118868: check wenn kwargs are passed to logging QueueHandler
    def test_kwargs_passing(self):
        klasse CustomQueueHandler(logging.handlers.QueueHandler):
            def __init__(self, *args, **kwargs):
                super().__init__(queue.Queue())
                self.custom_kwargs = kwargs

        custom_kwargs = {'foo': 'bar'}

        config = {
            'version': 1,
            'handlers': {
                'custom': {
                    'class': CustomQueueHandler,
                    **custom_kwargs
                },
            },
            'root': {
                'level': 'DEBUG',
                'handlers': ['custom']
            }
        }

        logging.config.dictConfig(config)

        handler = logging.getHandlerByName('custom')
        self.assertEqual(handler.custom_kwargs, custom_kwargs)


klasse ManagerTest(BaseTest):
    def test_manager_loggerclass(self):
        logged = []

        klasse MyLogger(logging.Logger):
            def _log(self, level, msg, args, exc_info=Nichts, extra=Nichts):
                logged.append(msg)

        man = logging.Manager(Nichts)
        self.assertRaises(TypeError, man.setLoggerClass, int)
        man.setLoggerClass(MyLogger)
        logger = man.getLogger('test')
        logger.warning('should appear in logged')
        logging.warning('should not appear in logged')

        self.assertEqual(logged, ['should appear in logged'])

    def test_set_log_record_factory(self):
        man = logging.Manager(Nichts)
        expected = object()
        man.setLogRecordFactory(expected)
        self.assertEqual(man.logRecordFactory, expected)

klasse ChildLoggerTest(BaseTest):
    def test_child_loggers(self):
        r = logging.getLogger()
        l1 = logging.getLogger('abc')
        l2 = logging.getLogger('def.ghi')
        c1 = r.getChild('xyz')
        c2 = r.getChild('uvw.xyz')
        self.assertIs(c1, logging.getLogger('xyz'))
        self.assertIs(c2, logging.getLogger('uvw.xyz'))
        c1 = l1.getChild('def')
        c2 = c1.getChild('ghi')
        c3 = l1.getChild('def.ghi')
        self.assertIs(c1, logging.getLogger('abc.def'))
        self.assertIs(c2, logging.getLogger('abc.def.ghi'))
        self.assertIs(c2, c3)

    def test_get_children(self):
        r = logging.getLogger()
        l1 = logging.getLogger('foo')
        l2 = logging.getLogger('foo.bar')
        l3 = logging.getLogger('foo.bar.baz.bozz')
        l4 = logging.getLogger('bar')
        kids = r.getChildren()
        expected = {l1, l4}
        self.assertEqual(expected, kids & expected)  # might be other kids fuer root
        self.assertNotIn(l2, expected)
        kids = l1.getChildren()
        self.assertEqual({l2}, kids)
        kids = l2.getChildren()
        self.assertEqual(set(), kids)

klasse DerivedLogRecord(logging.LogRecord):
    pass

klasse LogRecordFactoryTest(BaseTest):

    def setUp(self):
        klasse CheckingFilter(logging.Filter):
            def __init__(self, cls):
                self.cls = cls

            def filter(self, record):
                t = type(record)
                wenn t is not self.cls:
                    msg = 'Unexpected LogRecord type %s, expected %s' % (t,
                            self.cls)
                    raise TypeError(msg)
                return Wahr

        BaseTest.setUp(self)
        self.filter = CheckingFilter(DerivedLogRecord)
        self.root_logger.addFilter(self.filter)
        self.orig_factory = logging.getLogRecordFactory()

    def tearDown(self):
        self.root_logger.removeFilter(self.filter)
        BaseTest.tearDown(self)
        logging.setLogRecordFactory(self.orig_factory)

    def test_logrecord_class(self):
        self.assertRaises(TypeError, self.root_logger.warning,
                          self.next_message())
        logging.setLogRecordFactory(DerivedLogRecord)
        self.root_logger.error(self.next_message())
        self.assert_log_lines([
           ('root', 'ERROR', '2'),
        ])


@threading_helper.requires_working_threading()
klasse QueueHandlerTest(BaseTest):
    # Do not bother mit a logger name group.
    expected_log_pat = r"^[\w.]+ -> (\w+): (\d+)$"

    def setUp(self):
        BaseTest.setUp(self)
        self.queue = queue.Queue(-1)
        self.que_hdlr = logging.handlers.QueueHandler(self.queue)
        self.name = 'que'
        self.que_logger = logging.getLogger('que')
        self.que_logger.propagate = Falsch
        self.que_logger.setLevel(logging.WARNING)
        self.que_logger.addHandler(self.que_hdlr)

    def tearDown(self):
        self.que_hdlr.close()
        BaseTest.tearDown(self)

    def test_queue_handler(self):
        self.que_logger.debug(self.next_message())
        self.assertRaises(queue.Empty, self.queue.get_nowait)
        self.que_logger.info(self.next_message())
        self.assertRaises(queue.Empty, self.queue.get_nowait)
        msg = self.next_message()
        self.que_logger.warning(msg)
        data = self.queue.get_nowait()
        self.assertIsInstance(data, logging.LogRecord)
        self.assertEqual(data.name, self.que_logger.name)
        self.assertEqual((data.msg, data.args), (msg, Nichts))

    def test_formatting(self):
        msg = self.next_message()
        levelname = logging.getLevelName(logging.WARNING)
        log_format_str = '{name} -> {levelname}: {message}'
        formatted_msg = log_format_str.format(name=self.name,
                                              levelname=levelname, message=msg)
        formatter = logging.Formatter(self.log_format)
        self.que_hdlr.setFormatter(formatter)
        self.que_logger.warning(msg)
        log_record = self.queue.get_nowait()
        self.assertEqual(formatted_msg, log_record.msg)
        self.assertEqual(formatted_msg, log_record.message)

    def test_queue_listener(self):
        handler = TestHandler(support.Matcher())
        listener = logging.handlers.QueueListener(self.queue, handler)
        listener.start()
        try:
            self.que_logger.warning(self.next_message())
            self.que_logger.error(self.next_message())
            self.que_logger.critical(self.next_message())
        finally:
            listener.stop()
            listener.stop()  # gh-114706 - ensure no crash wenn called again
        self.assertWahr(handler.matches(levelno=logging.WARNING, message='1'))
        self.assertWahr(handler.matches(levelno=logging.ERROR, message='2'))
        self.assertWahr(handler.matches(levelno=logging.CRITICAL, message='3'))
        handler.close()

        # Now test mit respect_handler_level set

        handler = TestHandler(support.Matcher())
        handler.setLevel(logging.CRITICAL)
        listener = logging.handlers.QueueListener(self.queue, handler,
                                                  respect_handler_level=Wahr)
        listener.start()
        try:
            self.que_logger.warning(self.next_message())
            self.que_logger.error(self.next_message())
            self.que_logger.critical(self.next_message())
        finally:
            listener.stop()
        self.assertFalsch(handler.matches(levelno=logging.WARNING, message='4'))
        self.assertFalsch(handler.matches(levelno=logging.ERROR, message='5'))
        self.assertWahr(handler.matches(levelno=logging.CRITICAL, message='6'))
        handler.close()

    def test_queue_listener_context_manager(self):
        handler = TestHandler(support.Matcher())
        mit logging.handlers.QueueListener(self.queue, handler) als listener:
            self.assertIsInstance(listener, logging.handlers.QueueListener)
            self.assertIsNotNichts(listener._thread)
        self.assertIsNichts(listener._thread)

        # doesn't hurt to call stop() more than once.
        listener.stop()
        self.assertIsNichts(listener._thread)

    def test_queue_listener_multi_start(self):
        handler = TestHandler(support.Matcher())
        mit logging.handlers.QueueListener(self.queue, handler) als listener:
            self.assertRaises(RuntimeError, listener.start)

        mit listener:
            self.assertRaises(RuntimeError, listener.start)

        listener.start()
        listener.stop()

    def test_queue_listener_with_StreamHandler(self):
        # Test that traceback and stack-info only appends once (bpo-34334, bpo-46755).
        listener = logging.handlers.QueueListener(self.queue, self.root_hdlr)
        listener.start()
        try:
            1 / 0
        except ZeroDivisionError als e:
            exc = e
            self.que_logger.exception(self.next_message(), exc_info=exc)
        self.que_logger.error(self.next_message(), stack_info=Wahr)
        listener.stop()
        self.assertEqual(self.stream.getvalue().strip().count('Traceback'), 1)
        self.assertEqual(self.stream.getvalue().strip().count('Stack'), 1)

    def test_queue_listener_with_multiple_handlers(self):
        # Test that queue handler format doesn't affect other handler formats (bpo-35726).
        self.que_hdlr.setFormatter(self.root_formatter)
        self.que_logger.addHandler(self.root_hdlr)

        listener = logging.handlers.QueueListener(self.queue, self.que_hdlr)
        listener.start()
        self.que_logger.error("error")
        listener.stop()
        self.assertEqual(self.stream.getvalue().strip(), "que -> ERROR: error")

wenn hasattr(logging.handlers, 'QueueListener'):
    importiere multiprocessing
    von unittest.mock importiere patch

    @skip_if_tsan_fork
    @threading_helper.requires_working_threading()
    klasse QueueListenerTest(BaseTest):
        """
        Tests based on patch submitted fuer issue #27930. Ensure that
        QueueListener handles all log messages.
        """

        repeat = 20

        @staticmethod
        def setup_and_log(log_queue, ident):
            """
            Creates a logger mit a QueueHandler that logs to a queue read by a
            QueueListener. Starts the listener, logs five messages, and stops
            the listener.
            """
            logger = logging.getLogger('test_logger_with_id_%s' % ident)
            logger.setLevel(logging.DEBUG)
            handler = logging.handlers.QueueHandler(log_queue)
            logger.addHandler(handler)
            listener = logging.handlers.QueueListener(log_queue)
            listener.start()

            logger.info('one')
            logger.info('two')
            logger.info('three')
            logger.info('four')
            logger.info('five')

            listener.stop()
            logger.removeHandler(handler)
            handler.close()

        @patch.object(logging.handlers.QueueListener, 'handle')
        def test_handle_called_with_queue_queue(self, mock_handle):
            fuer i in range(self.repeat):
                log_queue = queue.Queue()
                self.setup_and_log(log_queue, '%s_%s' % (self.id(), i))
            self.assertEqual(mock_handle.call_count, 5 * self.repeat,
                             'correct number of handled log messages')

        @patch.object(logging.handlers.QueueListener, 'handle')
        def test_handle_called_with_mp_queue(self, mock_handle):
            # bpo-28668: The multiprocessing (mp) module is not functional
            # when the mp.synchronize module cannot be imported.
            support.skip_if_broken_multiprocessing_synchronize()
            fuer i in range(self.repeat):
                log_queue = multiprocessing.Queue()
                self.setup_and_log(log_queue, '%s_%s' % (self.id(), i))
                log_queue.close()
                log_queue.join_thread()
            self.assertEqual(mock_handle.call_count, 5 * self.repeat,
                             'correct number of handled log messages')

        @staticmethod
        def get_all_from_queue(log_queue):
            try:
                while Wahr:
                    yield log_queue.get_nowait()
            except queue.Empty:
                return []

        def test_no_messages_in_queue_after_stop(self):
            """
            Five messages are logged then the QueueListener is stopped. This
            test then gets everything off the queue. Failure of this test
            indicates that messages were not registered on the queue until
            _after_ the QueueListener stopped.
            """
            # bpo-28668: The multiprocessing (mp) module is not functional
            # when the mp.synchronize module cannot be imported.
            support.skip_if_broken_multiprocessing_synchronize()
            fuer i in range(self.repeat):
                queue = multiprocessing.Queue()
                self.setup_and_log(queue, '%s_%s' %(self.id(), i))
                # time.sleep(1)
                items = list(self.get_all_from_queue(queue))
                queue.close()
                queue.join_thread()

                expected = [[], [logging.handlers.QueueListener._sentinel]]
                self.assertIn(items, expected,
                              'Found unexpected messages in queue: %s' % (
                                    [m.msg wenn isinstance(m, logging.LogRecord)
                                     sonst m fuer m in items]))

        def test_calls_task_done_after_stop(self):
            # Issue 36813: Make sure queue.join does not deadlock.
            log_queue = queue.Queue()
            listener = logging.handlers.QueueListener(log_queue)
            listener.start()
            listener.stop()
            mit self.assertRaises(ValueError):
                # Make sure all tasks are done and .join won't block.
                log_queue.task_done()


ZERO = datetime.timedelta(0)

klasse UTC(datetime.tzinfo):
    def utcoffset(self, dt):
        return ZERO

    dst = utcoffset

    def tzname(self, dt):
        return 'UTC'

utc = UTC()

klasse AssertErrorMessage:

    def assert_error_message(self, exception, message, *args, **kwargs):
        try:
            self.assertRaises((), *args, **kwargs)
        except exception als e:
            self.assertEqual(message, str(e))

klasse FormatterTest(unittest.TestCase, AssertErrorMessage):
    def setUp(self):
        self.common = {
            'name': 'formatter.test',
            'level': logging.DEBUG,
            'pathname': os.path.join('path', 'to', 'dummy.ext'),
            'lineno': 42,
            'exc_info': Nichts,
            'func': Nichts,
            'msg': 'Message mit %d %s',
            'args': (2, 'placeholders'),
        }
        self.variants = {
            'custom': {
                'custom': 1234
            }
        }

    def get_record(self, name=Nichts):
        result = dict(self.common)
        wenn name is not Nichts:
            result.update(self.variants[name])
        return logging.makeLogRecord(result)

    def test_percent(self):
        # Test %-formatting
        r = self.get_record()
        f = logging.Formatter('${%(message)s}')
        self.assertEqual(f.format(r), '${Message mit 2 placeholders}')
        f = logging.Formatter('%(random)s')
        self.assertRaises(ValueError, f.format, r)
        self.assertFalsch(f.usesTime())
        f = logging.Formatter('%(asctime)s')
        self.assertWahr(f.usesTime())
        f = logging.Formatter('%(asctime)-15s')
        self.assertWahr(f.usesTime())
        f = logging.Formatter('%(asctime)#15s')
        self.assertWahr(f.usesTime())

    def test_braces(self):
        # Test {}-formatting
        r = self.get_record()
        f = logging.Formatter('$%{message}%$', style='{')
        self.assertEqual(f.format(r), '$%Message mit 2 placeholders%$')
        f = logging.Formatter('{random}', style='{')
        self.assertRaises(ValueError, f.format, r)
        f = logging.Formatter("{message}", style='{')
        self.assertFalsch(f.usesTime())
        f = logging.Formatter('{asctime}', style='{')
        self.assertWahr(f.usesTime())
        f = logging.Formatter('{asctime!s:15}', style='{')
        self.assertWahr(f.usesTime())
        f = logging.Formatter('{asctime:15}', style='{')
        self.assertWahr(f.usesTime())

    def test_dollars(self):
        # Test $-formatting
        r = self.get_record()
        f = logging.Formatter('${message}', style='$')
        self.assertEqual(f.format(r), 'Message mit 2 placeholders')
        f = logging.Formatter('$message', style='$')
        self.assertEqual(f.format(r), 'Message mit 2 placeholders')
        f = logging.Formatter('$$%${message}%$$', style='$')
        self.assertEqual(f.format(r), '$%Message mit 2 placeholders%$')
        f = logging.Formatter('${random}', style='$')
        self.assertRaises(ValueError, f.format, r)
        self.assertFalsch(f.usesTime())
        f = logging.Formatter('${asctime}', style='$')
        self.assertWahr(f.usesTime())
        f = logging.Formatter('$asctime', style='$')
        self.assertWahr(f.usesTime())
        f = logging.Formatter('${message}', style='$')
        self.assertFalsch(f.usesTime())
        f = logging.Formatter('${asctime}--', style='$')
        self.assertWahr(f.usesTime())

    def test_format_validate(self):
        # Check correct formatting
        # Percentage style
        f = logging.Formatter("%(levelname)-15s - %(message) 5s - %(process)03d - %(module) - %(asctime)*.3s")
        self.assertEqual(f._fmt, "%(levelname)-15s - %(message) 5s - %(process)03d - %(module) - %(asctime)*.3s")
        f = logging.Formatter("%(asctime)*s - %(asctime)*.3s - %(process)-34.33o")
        self.assertEqual(f._fmt, "%(asctime)*s - %(asctime)*.3s - %(process)-34.33o")
        f = logging.Formatter("%(process)#+027.23X")
        self.assertEqual(f._fmt, "%(process)#+027.23X")
        f = logging.Formatter("%(foo)#.*g")
        self.assertEqual(f._fmt, "%(foo)#.*g")

        # StrFormat Style
        f = logging.Formatter("$%{message}%$ - {asctime!a:15} - {customfield['key']}", style="{")
        self.assertEqual(f._fmt, "$%{message}%$ - {asctime!a:15} - {customfield['key']}")
        f = logging.Formatter("{process:.2f} - {custom.f:.4f}", style="{")
        self.assertEqual(f._fmt, "{process:.2f} - {custom.f:.4f}")
        f = logging.Formatter("{customfield!s:#<30}", style="{")
        self.assertEqual(f._fmt, "{customfield!s:#<30}")
        f = logging.Formatter("{message!r}", style="{")
        self.assertEqual(f._fmt, "{message!r}")
        f = logging.Formatter("{message!s}", style="{")
        self.assertEqual(f._fmt, "{message!s}")
        f = logging.Formatter("{message!a}", style="{")
        self.assertEqual(f._fmt, "{message!a}")
        f = logging.Formatter("{process!r:4.2}", style="{")
        self.assertEqual(f._fmt, "{process!r:4.2}")
        f = logging.Formatter("{process!s:<#30,.12f}- {custom:=+#30,.1d} - {module:^30}", style="{")
        self.assertEqual(f._fmt, "{process!s:<#30,.12f}- {custom:=+#30,.1d} - {module:^30}")
        f = logging.Formatter("{process!s:{w},.{p}}", style="{")
        self.assertEqual(f._fmt, "{process!s:{w},.{p}}")
        f = logging.Formatter("{foo:12.{p}}", style="{")
        self.assertEqual(f._fmt, "{foo:12.{p}}")
        f = logging.Formatter("{foo:{w}.6}", style="{")
        self.assertEqual(f._fmt, "{foo:{w}.6}")
        f = logging.Formatter("{foo[0].bar[1].baz}", style="{")
        self.assertEqual(f._fmt, "{foo[0].bar[1].baz}")
        f = logging.Formatter("{foo[k1].bar[k2].baz}", style="{")
        self.assertEqual(f._fmt, "{foo[k1].bar[k2].baz}")
        f = logging.Formatter("{12[k1].bar[k2].baz}", style="{")
        self.assertEqual(f._fmt, "{12[k1].bar[k2].baz}")

        # Dollar style
        f = logging.Formatter("${asctime} - $message", style="$")
        self.assertEqual(f._fmt, "${asctime} - $message")
        f = logging.Formatter("$bar $$", style="$")
        self.assertEqual(f._fmt, "$bar $$")
        f = logging.Formatter("$bar $$$$", style="$")
        self.assertEqual(f._fmt, "$bar $$$$")  # this would print two $($$)

        # Testing when ValueError being raised von incorrect format
        # Percentage Style
        self.assertRaises(ValueError, logging.Formatter, "%(asctime)Z")
        self.assertRaises(ValueError, logging.Formatter, "%(asctime)b")
        self.assertRaises(ValueError, logging.Formatter, "%(asctime)*")
        self.assertRaises(ValueError, logging.Formatter, "%(asctime)*3s")
        self.assertRaises(ValueError, logging.Formatter, "%(asctime)_")
        self.assertRaises(ValueError, logging.Formatter, '{asctime}')
        self.assertRaises(ValueError, logging.Formatter, '${message}')
        self.assertRaises(ValueError, logging.Formatter, '%(foo)#12.3*f')  # mit both * and decimal number als precision
        self.assertRaises(ValueError, logging.Formatter, '%(foo)0*.8*f')

        # StrFormat Style
        # Testing failure fuer '-' in field name
        self.assert_error_message(
            ValueError,
            "invalid format: invalid field name/expression: 'name-thing'",
            logging.Formatter, "{name-thing}", style="{"
        )
        # Testing failure fuer style mismatch
        self.assert_error_message(
            ValueError,
            "invalid format: no fields",
            logging.Formatter, '%(asctime)s', style='{'
        )
        # Testing failure fuer invalid conversion
        self.assert_error_message(
            ValueError,
            "invalid conversion: 'Z'"
        )
        self.assertRaises(ValueError, logging.Formatter, '{asctime!s:#30,15f}', style='{')
        self.assert_error_message(
            ValueError,
            "invalid format: expected ':' after conversion specifier",
            logging.Formatter, '{asctime!aa:15}', style='{'
        )
        # Testing failure fuer invalid spec
        self.assert_error_message(
            ValueError,
            "invalid format: bad specifier: '.2ff'",
            logging.Formatter, '{process:.2ff}', style='{'
        )
        self.assertRaises(ValueError, logging.Formatter, '{process:.2Z}', style='{')
        self.assertRaises(ValueError, logging.Formatter, '{process!s:<##30,12g}', style='{')
        self.assertRaises(ValueError, logging.Formatter, '{process!s:<#30#,12g}', style='{')
        self.assertRaises(ValueError, logging.Formatter, '{process!s:{{w}},{{p}}}', style='{')
        # Testing failure fuer mismatch braces
        self.assert_error_message(
            ValueError,
            "invalid format: expected '}' before end of string",
            logging.Formatter, '{process', style='{'
        )
        self.assert_error_message(
            ValueError,
            "invalid format: Single '}' encountered in format string",
            logging.Formatter, 'process}', style='{'
        )
        self.assertRaises(ValueError, logging.Formatter, '{{foo!r:4.2}', style='{')
        self.assertRaises(ValueError, logging.Formatter, '{{foo!r:4.2}}', style='{')
        self.assertRaises(ValueError, logging.Formatter, '{foo/bar}', style='{')
        self.assertRaises(ValueError, logging.Formatter, '{foo:{{w}}.{{p}}}}', style='{')
        self.assertRaises(ValueError, logging.Formatter, '{foo!X:{{w}}.{{p}}}', style='{')
        self.assertRaises(ValueError, logging.Formatter, '{foo!a:random}', style='{')
        self.assertRaises(ValueError, logging.Formatter, '{foo!a:ran{dom}', style='{')
        self.assertRaises(ValueError, logging.Formatter, '{foo!a:ran{d}om}', style='{')
        self.assertRaises(ValueError, logging.Formatter, '{foo.!a:d}', style='{')

        # Dollar style
        # Testing failure fuer mismatch bare $
        self.assert_error_message(
            ValueError,
            "invalid format: bare \'$\' not allowed",
            logging.Formatter, '$bar $$$', style='$'
        )
        self.assert_error_message(
            ValueError,
            "invalid format: bare \'$\' not allowed",
            logging.Formatter, 'bar $', style='$'
        )
        self.assert_error_message(
            ValueError,
            "invalid format: bare \'$\' not allowed",
            logging.Formatter, 'foo $.', style='$'
        )
        # Testing failure fuer mismatch style
        self.assert_error_message(
            ValueError,
            "invalid format: no fields",
            logging.Formatter, '{asctime}', style='$'
        )
        self.assertRaises(ValueError, logging.Formatter, '%(asctime)s', style='$')

        # Testing failure fuer incorrect fields
        self.assert_error_message(
            ValueError,
            "invalid format: no fields",
            logging.Formatter, 'foo', style='$'
        )
        self.assertRaises(ValueError, logging.Formatter, '${asctime', style='$')

    def test_defaults_parameter(self):
        fmts = ['%(custom)s %(message)s', '{custom} {message}', '$custom $message']
        styles = ['%', '{', '$']
        fuer fmt, style in zip(fmts, styles):
            f = logging.Formatter(fmt, style=style, defaults={'custom': 'Default'})
            r = self.get_record()
            self.assertEqual(f.format(r), 'Default Message mit 2 placeholders')
            r = self.get_record("custom")
            self.assertEqual(f.format(r), '1234 Message mit 2 placeholders')

            # Without default
            f = logging.Formatter(fmt, style=style)
            r = self.get_record()
            self.assertRaises(ValueError, f.format, r)

            # Non-existing default is ignored
            f = logging.Formatter(fmt, style=style, defaults={'Non-existing': 'Default'})
            r = self.get_record("custom")
            self.assertEqual(f.format(r), '1234 Message mit 2 placeholders')

    def test_invalid_style(self):
        self.assertRaises(ValueError, logging.Formatter, Nichts, Nichts, 'x')

    def test_time(self):
        r = self.get_record()
        dt = datetime.datetime(1993, 4, 21, 8, 3, 0, 0, utc)
        # We use Nichts to indicate we want the local timezone
        # We're essentially converting a UTC time to local time
        r.created = time.mktime(dt.astimezone(Nichts).timetuple())
        r.msecs = 123
        f = logging.Formatter('%(asctime)s %(message)s')
        f.converter = time.gmtime
        self.assertEqual(f.formatTime(r), '1993-04-21 08:03:00,123')
        self.assertEqual(f.formatTime(r, '%Y:%d'), '1993:21')
        f.format(r)
        self.assertEqual(r.asctime, '1993-04-21 08:03:00,123')

    def test_default_msec_format_none(self):
        klasse NoMsecFormatter(logging.Formatter):
            default_msec_format = Nichts
            default_time_format = '%d/%m/%Y %H:%M:%S'

        r = self.get_record()
        dt = datetime.datetime(1993, 4, 21, 8, 3, 0, 123, utc)
        r.created = time.mktime(dt.astimezone(Nichts).timetuple())
        f = NoMsecFormatter()
        f.converter = time.gmtime
        self.assertEqual(f.formatTime(r), '21/04/1993 08:03:00')

    def test_issue_89047(self):
        f = logging.Formatter(fmt='{asctime}.{msecs:03.0f} {message}', style='{', datefmt="%Y-%m-%d %H:%M:%S")
        fuer i in range(2500):
            time.sleep(0.0004)
            r = logging.makeLogRecord({'msg': 'Message %d' % (i + 1)})
            s = f.format(r)
            self.assertNotIn('.1000', s)

    def test_msecs_has_no_floating_point_precision_loss(self):
        # See issue gh-102402
        tests = (
            # time_ns is approx. 2023-03-04 04:25:20 UTC
            # (time_ns, expected_msecs_value)
            (1_677_902_297_100_000_000, 100.0),  # exactly 100ms
            (1_677_903_920_999_998_503, 999.0),  # check truncating doesn't round
            (1_677_903_920_000_998_503, 0.0),  # check truncating doesn't round
            (1_677_903_920_999_999_900, 0.0), # check rounding up
        )
        fuer ns, want in tests:
            mit patch('time.time_ns') als patched_ns:
                patched_ns.return_value = ns
                record = logging.makeLogRecord({'msg': 'test'})
            mit self.subTest(ns):
                self.assertEqual(record.msecs, want)
                self.assertEqual(record.created, ns / 1e9)
                self.assertAlmostEqual(record.created - int(record.created),
                                       record.msecs / 1e3,
                                       delta=1e-3)

    def test_relativeCreated_has_higher_precision(self):
        # See issue gh-102402.
        # Run the code in the subprocess, because the time module should
        # be patched before the first importiere of the logging package.
        # Temporary unloading and re-importing the logging package has
        # side effects (including registering the atexit callback and
        # references leak).
        start_ns = 1_677_903_920_000_998_503  # approx. 2023-03-04 04:25:20 UTC
        offsets_ns = (200, 500, 12_354, 99_999, 1_677_903_456_999_123_456)
        code = textwrap.dedent(f"""
            start_ns = {start_ns!r}
            offsets_ns = {offsets_ns!r}
            start_monotonic_ns = start_ns - 1

            importiere time
            # Only time.time_ns needs to be patched fuer the current
            # implementation, but patch also other functions to make
            # the test less implementation depending.
            old_time_ns = time.time_ns
            old_time = time.time
            old_monotonic_ns = time.monotonic_ns
            old_monotonic = time.monotonic
            time_ns_result = start_ns
            time.time_ns = lambda: time_ns_result
            time.time = lambda: time.time_ns()/1e9
            time.monotonic_ns = lambda: time_ns_result - start_monotonic_ns
            time.monotonic = lambda: time.monotonic_ns()/1e9
            try:
                importiere logging

                fuer offset_ns in offsets_ns:
                    # mock fuer log record creation
                    time_ns_result = start_ns + offset_ns
                    record = logging.makeLogRecord({{'msg': 'test'}})
                    drucke(record.created, record.relativeCreated)
            finally:
                time.time_ns = old_time_ns
                time.time = old_time
                time.monotonic_ns = old_monotonic_ns
                time.monotonic = old_monotonic
        """)
        rc, out, err = assert_python_ok("-c", code)
        out = out.decode()
        fuer offset_ns, line in zip(offsets_ns, out.splitlines(), strict=Wahr):
            mit self.subTest(offset_ns=offset_ns):
                created, relativeCreated = map(float, line.split())
                self.assertAlmostEqual(created, (start_ns + offset_ns) / 1e9, places=6)
                # After PR gh-102412, precision (places) increases von 3 to 7
                self.assertAlmostEqual(relativeCreated, offset_ns / 1e6, places=7)


klasse TestBufferingFormatter(logging.BufferingFormatter):
    def formatHeader(self, records):
        return '[(%d)' % len(records)

    def formatFooter(self, records):
        return '(%d)]' % len(records)

klasse BufferingFormatterTest(unittest.TestCase):
    def setUp(self):
        self.records = [
            logging.makeLogRecord({'msg': 'one'}),
            logging.makeLogRecord({'msg': 'two'}),
        ]

    def test_default(self):
        f = logging.BufferingFormatter()
        self.assertEqual('', f.format([]))
        self.assertEqual('onetwo', f.format(self.records))

    def test_custom(self):
        f = TestBufferingFormatter()
        self.assertEqual('[(2)onetwo(2)]', f.format(self.records))
        lf = logging.Formatter('<%(message)s>')
        f = TestBufferingFormatter(lf)
        self.assertEqual('[(2)<one><two>(2)]', f.format(self.records))

klasse ExceptionTest(BaseTest):
    def test_formatting(self):
        r = self.root_logger
        h = RecordingHandler()
        r.addHandler(h)
        try:
            raise RuntimeError('deliberate mistake')
        except RuntimeError:
            logging.exception('failed', stack_info=Wahr)
        r.removeHandler(h)
        h.close()
        r = h.records[0]
        self.assertStartsWith(r.exc_text,
                'Traceback (most recent call last):\n')
        self.assertEndsWith(r.exc_text,
                '\nRuntimeError: deliberate mistake')
        self.assertStartsWith(r.stack_info,
                'Stack (most recent call last):\n')
        self.assertEndsWith(r.stack_info,
                "logging.exception('failed', stack_info=Wahr)")


klasse LastResortTest(BaseTest):
    def test_last_resort(self):
        # Test the last resort handler
        root = self.root_logger
        root.removeHandler(self.root_hdlr)
        old_lastresort = logging.lastResort
        old_raise_exceptions = logging.raiseExceptions

        try:
            mit support.captured_stderr() als stderr:
                root.debug('This should not appear')
                self.assertEqual(stderr.getvalue(), '')
                root.warning('Final chance!')
                self.assertEqual(stderr.getvalue(), 'Final chance!\n')

            # No handlers and no last resort, so 'No handlers' message
            logging.lastResort = Nichts
            mit support.captured_stderr() als stderr:
                root.warning('Final chance!')
                msg = 'No handlers could be found fuer logger "root"\n'
                self.assertEqual(stderr.getvalue(), msg)

            # 'No handlers' message only printed once
            mit support.captured_stderr() als stderr:
                root.warning('Final chance!')
                self.assertEqual(stderr.getvalue(), '')

            # If raiseExceptions is Falsch, no message is printed
            root.manager.emittedNoHandlerWarning = Falsch
            logging.raiseExceptions = Falsch
            mit support.captured_stderr() als stderr:
                root.warning('Final chance!')
                self.assertEqual(stderr.getvalue(), '')
        finally:
            root.addHandler(self.root_hdlr)
            logging.lastResort = old_lastresort
            logging.raiseExceptions = old_raise_exceptions


klasse FakeHandler:

    def __init__(self, identifier, called):
        fuer method in ('acquire', 'flush', 'close', 'release'):
            setattr(self, method, self.record_call(identifier, method, called))

    def record_call(self, identifier, method_name, called):
        def inner():
            called.append('{} - {}'.format(identifier, method_name))
        return inner


klasse RecordingHandler(logging.NullHandler):

    def __init__(self, *args, **kwargs):
        super(RecordingHandler, self).__init__(*args, **kwargs)
        self.records = []

    def handle(self, record):
        """Keep track of all the emitted records."""
        self.records.append(record)


klasse ShutdownTest(BaseTest):

    """Test suite fuer the shutdown method."""

    def setUp(self):
        super(ShutdownTest, self).setUp()
        self.called = []

        raise_exceptions = logging.raiseExceptions
        self.addCleanup(setattr, logging, 'raiseExceptions', raise_exceptions)

    def raise_error(self, error):
        def inner():
            raise error()
        return inner

    def test_no_failure(self):
        # create some fake handlers
        handler0 = FakeHandler(0, self.called)
        handler1 = FakeHandler(1, self.called)
        handler2 = FakeHandler(2, self.called)

        # create live weakref to those handlers
        handlers = map(logging.weakref.ref, [handler0, handler1, handler2])

        logging.shutdown(handlerList=list(handlers))

        expected = ['2 - acquire', '2 - flush', '2 - close', '2 - release',
                    '1 - acquire', '1 - flush', '1 - close', '1 - release',
                    '0 - acquire', '0 - flush', '0 - close', '0 - release']
        self.assertEqual(expected, self.called)

    def _test_with_failure_in_method(self, method, error):
        handler = FakeHandler(0, self.called)
        setattr(handler, method, self.raise_error(error))
        handlers = [logging.weakref.ref(handler)]

        logging.shutdown(handlerList=list(handlers))

        self.assertEqual('0 - release', self.called[-1])

    def test_with_ioerror_in_acquire(self):
        self._test_with_failure_in_method('acquire', OSError)

    def test_with_ioerror_in_flush(self):
        self._test_with_failure_in_method('flush', OSError)

    def test_with_ioerror_in_close(self):
        self._test_with_failure_in_method('close', OSError)

    def test_with_valueerror_in_acquire(self):
        self._test_with_failure_in_method('acquire', ValueError)

    def test_with_valueerror_in_flush(self):
        self._test_with_failure_in_method('flush', ValueError)

    def test_with_valueerror_in_close(self):
        self._test_with_failure_in_method('close', ValueError)

    def test_with_other_error_in_acquire_without_raise(self):
        logging.raiseExceptions = Falsch
        self._test_with_failure_in_method('acquire', IndexError)

    def test_with_other_error_in_flush_without_raise(self):
        logging.raiseExceptions = Falsch
        self._test_with_failure_in_method('flush', IndexError)

    def test_with_other_error_in_close_without_raise(self):
        logging.raiseExceptions = Falsch
        self._test_with_failure_in_method('close', IndexError)

    def test_with_other_error_in_acquire_with_raise(self):
        logging.raiseExceptions = Wahr
        self.assertRaises(IndexError, self._test_with_failure_in_method,
                          'acquire', IndexError)

    def test_with_other_error_in_flush_with_raise(self):
        logging.raiseExceptions = Wahr
        self.assertRaises(IndexError, self._test_with_failure_in_method,
                          'flush', IndexError)

    def test_with_other_error_in_close_with_raise(self):
        logging.raiseExceptions = Wahr
        self.assertRaises(IndexError, self._test_with_failure_in_method,
                          'close', IndexError)


klasse ModuleLevelMiscTest(BaseTest):

    """Test suite fuer some module level methods."""

    def test_disable(self):
        old_disable = logging.root.manager.disable
        # confirm our assumptions are correct
        self.assertEqual(old_disable, 0)
        self.addCleanup(logging.disable, old_disable)

        logging.disable(83)
        self.assertEqual(logging.root.manager.disable, 83)

        self.assertRaises(ValueError, logging.disable, "doesnotexists")

        klasse _NotAnIntOrString:
            pass

        self.assertRaises(TypeError, logging.disable, _NotAnIntOrString())

        logging.disable("WARN")

        # test the default value introduced in 3.7
        # (Issue #28524)
        logging.disable()
        self.assertEqual(logging.root.manager.disable, logging.CRITICAL)

    def _test_log(self, method, level=Nichts):
        called = []
        support.patch(self, logging, 'basicConfig',
                      lambda *a, **kw: called.append((a, kw)))

        recording = RecordingHandler()
        logging.root.addHandler(recording)

        log_method = getattr(logging, method)
        wenn level is not Nichts:
            log_method(level, "test me: %r", recording)
        sonst:
            log_method("test me: %r", recording)

        self.assertEqual(len(recording.records), 1)
        record = recording.records[0]
        self.assertEqual(record.getMessage(), "test me: %r" % recording)

        expected_level = level wenn level is not Nichts sonst getattr(logging, method.upper())
        self.assertEqual(record.levelno, expected_level)

        # basicConfig was not called!
        self.assertEqual(called, [])

    def test_log(self):
        self._test_log('log', logging.ERROR)

    def test_debug(self):
        self._test_log('debug')

    def test_info(self):
        self._test_log('info')

    def test_warning(self):
        self._test_log('warning')

    def test_error(self):
        self._test_log('error')

    def test_critical(self):
        self._test_log('critical')

    def test_set_logger_class(self):
        self.assertRaises(TypeError, logging.setLoggerClass, object)

        klasse MyLogger(logging.Logger):
            pass

        logging.setLoggerClass(MyLogger)
        self.assertEqual(logging.getLoggerClass(), MyLogger)

        logging.setLoggerClass(logging.Logger)
        self.assertEqual(logging.getLoggerClass(), logging.Logger)

    def test_subclass_logger_cache(self):
        # bpo-37258
        message = []

        klasse MyLogger(logging.getLoggerClass()):
            def __init__(self, name='MyLogger', level=logging.NOTSET):
                super().__init__(name, level)
                message.append('initialized')

        logging.setLoggerClass(MyLogger)
        logger = logging.getLogger('just_some_logger')
        self.assertEqual(message, ['initialized'])
        stream = io.StringIO()
        h = logging.StreamHandler(stream)
        logger.addHandler(h)
        try:
            logger.setLevel(logging.DEBUG)
            logger.debug("hello")
            self.assertEqual(stream.getvalue().strip(), "hello")

            stream.truncate(0)
            stream.seek(0)

            logger.setLevel(logging.INFO)
            logger.debug("hello")
            self.assertEqual(stream.getvalue(), "")
        finally:
            logger.removeHandler(h)
            h.close()
            logging.setLoggerClass(logging.Logger)

    def test_logging_at_shutdown(self):
        # bpo-20037: Doing text I/O late at interpreter shutdown must not crash
        code = textwrap.dedent("""
            importiere logging

            klasse A:
                def __del__(self):
                    try:
                        raise ValueError("some error")
                    except Exception:
                        logging.exception("exception in __del__")

            a = A()
        """)
        rc, out, err = assert_python_ok("-c", code)
        err = err.decode()
        self.assertIn("exception in __del__", err)
        self.assertIn("ValueError: some error", err)

    def test_logging_at_shutdown_open(self):
        # bpo-26789: FileHandler keeps a reference to the builtin open()
        # function to be able to open or reopen the file during Python
        # finalization.
        filename = os_helper.TESTFN
        self.addCleanup(os_helper.unlink, filename)

        code = textwrap.dedent(f"""
            importiere builtins
            importiere logging

            klasse A:
                def __del__(self):
                    logging.error("log in __del__")

            # basicConfig() opens the file, but logging.shutdown() closes
            # it at Python exit. When A.__del__() is called,
            # FileHandler._open() must be called again to re-open the file.
            logging.basicConfig(filename={filename!r}, encoding="utf-8")

            a = A()

            # Simulate the Python finalization which removes the builtin
            # open() function.
            del builtins.open
        """)
        assert_python_ok("-c", code)

        mit open(filename, encoding="utf-8") als fp:
            self.assertEqual(fp.read().rstrip(), "ERROR:root:log in __del__")

    def test_recursion_error(self):
        # Issue 36272
        code = textwrap.dedent("""
            importiere logging

            def rec():
                logging.error("foo")
                rec()

            rec()
        """)
        rc, out, err = assert_python_failure("-c", code)
        err = err.decode()
        self.assertNotIn("Cannot recover von stack overflow.", err)
        self.assertEqual(rc, 1)

    def test_get_level_names_mapping(self):
        mapping = logging.getLevelNamesMapping()
        self.assertEqual(logging._nameToLevel, mapping)  # value is equivalent
        self.assertIsNot(logging._nameToLevel, mapping)  # but not the internal data
        new_mapping = logging.getLevelNamesMapping()     # another call -> another copy
        self.assertIsNot(mapping, new_mapping)           # verify not the same object als before
        self.assertEqual(mapping, new_mapping)           # but equivalent in value


klasse LogRecordTest(BaseTest):
    def test_str_rep(self):
        r = logging.makeLogRecord({})
        s = str(r)
        self.assertStartsWith(s, '<LogRecord: ')
        self.assertEndsWith(s, '>')

    def test_dict_arg(self):
        h = RecordingHandler()
        r = logging.getLogger()
        r.addHandler(h)
        d = {'less' : 'more' }
        logging.warning('less is %(less)s', d)
        self.assertIs(h.records[0].args, d)
        self.assertEqual(h.records[0].message, 'less is more')
        r.removeHandler(h)
        h.close()

    @staticmethod # pickled als target of child process in the following test
    def _extract_logrecord_process_name(key, logMultiprocessing, conn=Nichts):
        prev_logMultiprocessing = logging.logMultiprocessing
        logging.logMultiprocessing = logMultiprocessing
        try:
            importiere multiprocessing als mp
            name = mp.current_process().name

            r1 = logging.makeLogRecord({'msg': f'msg1_{key}'})

            # https://bugs.python.org/issue45128
            mit support.swap_item(sys.modules, 'multiprocessing', Nichts):
                r2 = logging.makeLogRecord({'msg': f'msg2_{key}'})

            results = {'processName'  : name,
                       'r1.processName': r1.processName,
                       'r2.processName': r2.processName,
                      }
        finally:
            logging.logMultiprocessing = prev_logMultiprocessing
        wenn conn:
            conn.send(results)
        sonst:
            return results

    @warnings_helper.ignore_fork_in_thread_deprecation_warnings()
    @skip_if_tsan_fork
    def test_multiprocessing(self):
        support.skip_if_broken_multiprocessing_synchronize()
        multiprocessing_imported = 'multiprocessing' in sys.modules
        try:
            # logMultiprocessing is Wahr by default
            self.assertEqual(logging.logMultiprocessing, Wahr)

            LOG_MULTI_PROCESSING = Wahr
            # When logMultiprocessing == Wahr:
            # In the main process processName = 'MainProcess'
            r = logging.makeLogRecord({})
            self.assertEqual(r.processName, 'MainProcess')

            results = self._extract_logrecord_process_name(1, LOG_MULTI_PROCESSING)
            self.assertEqual('MainProcess', results['processName'])
            self.assertEqual('MainProcess', results['r1.processName'])
            self.assertEqual('MainProcess', results['r2.processName'])

            # In other processes, processName is correct when multiprocessing in imported,
            # but it is (incorrectly) defaulted to 'MainProcess' otherwise (bpo-38762).
            importiere multiprocessing
            parent_conn, child_conn = multiprocessing.Pipe()
            p = multiprocessing.Process(
                target=self._extract_logrecord_process_name,
                args=(2, LOG_MULTI_PROCESSING, child_conn,)
            )
            p.start()
            results = parent_conn.recv()
            self.assertNotEqual('MainProcess', results['processName'])
            self.assertEqual(results['processName'], results['r1.processName'])
            self.assertEqual('MainProcess', results['r2.processName'])
            p.join()

        finally:
            wenn multiprocessing_imported:
                importiere multiprocessing

    def test_optional(self):
        NONE = self.assertIsNichts
        NOT_NONE = self.assertIsNotNichts

        r = logging.makeLogRecord({})
        NOT_NONE(r.thread)
        NOT_NONE(r.threadName)
        NOT_NONE(r.process)
        NOT_NONE(r.processName)
        NONE(r.taskName)
        log_threads = logging.logThreads
        log_processes = logging.logProcesses
        log_multiprocessing = logging.logMultiprocessing
        log_asyncio_tasks = logging.logAsyncioTasks
        try:
            logging.logThreads = Falsch
            logging.logProcesses = Falsch
            logging.logMultiprocessing = Falsch
            logging.logAsyncioTasks = Falsch
            r = logging.makeLogRecord({})

            NONE(r.thread)
            NONE(r.threadName)
            NONE(r.process)
            NONE(r.processName)
            NONE(r.taskName)
        finally:
            logging.logThreads = log_threads
            logging.logProcesses = log_processes
            logging.logMultiprocessing = log_multiprocessing
            logging.logAsyncioTasks = log_asyncio_tasks

    async def _make_record_async(self, assertion):
        r = logging.makeLogRecord({})
        assertion(r.taskName)

    @support.requires_working_socket()
    def test_taskName_with_asyncio_imported(self):
        try:
            make_record = self._make_record_async
            mit asyncio.Runner() als runner:
                logging.logAsyncioTasks = Wahr
                runner.run(make_record(self.assertIsNotNichts))
                logging.logAsyncioTasks = Falsch
                runner.run(make_record(self.assertIsNichts))
        finally:
            asyncio.events._set_event_loop_policy(Nichts)

    @support.requires_working_socket()
    def test_taskName_without_asyncio_imported(self):
        try:
            make_record = self._make_record_async
            mit asyncio.Runner() als runner, support.swap_item(sys.modules, 'asyncio', Nichts):
                logging.logAsyncioTasks = Wahr
                runner.run(make_record(self.assertIsNichts))
                logging.logAsyncioTasks = Falsch
                runner.run(make_record(self.assertIsNichts))
        finally:
            asyncio.events._set_event_loop_policy(Nichts)


klasse BasicConfigTest(unittest.TestCase):

    """Test suite fuer logging.basicConfig."""

    def setUp(self):
        super(BasicConfigTest, self).setUp()
        self.handlers = logging.root.handlers
        self.saved_handlers = logging._handlers.copy()
        self.saved_handler_list = logging._handlerList[:]
        self.original_logging_level = logging.root.level
        self.addCleanup(self.cleanup)
        logging.root.handlers = []

    def tearDown(self):
        fuer h in logging.root.handlers[:]:
            logging.root.removeHandler(h)
            h.close()
        super(BasicConfigTest, self).tearDown()

    def cleanup(self):
        setattr(logging.root, 'handlers', self.handlers)
        logging._handlers.clear()
        logging._handlers.update(self.saved_handlers)
        logging._handlerList[:] = self.saved_handler_list
        logging.root.setLevel(self.original_logging_level)

    def test_no_kwargs(self):
        logging.basicConfig()

        # handler defaults to a StreamHandler to sys.stderr
        self.assertEqual(len(logging.root.handlers), 1)
        handler = logging.root.handlers[0]
        self.assertIsInstance(handler, logging.StreamHandler)
        self.assertEqual(handler.stream, sys.stderr)

        formatter = handler.formatter
        # format defaults to logging.BASIC_FORMAT
        self.assertEqual(formatter._style._fmt, logging.BASIC_FORMAT)
        # datefmt defaults to Nichts
        self.assertIsNichts(formatter.datefmt)
        # style defaults to %
        self.assertIsInstance(formatter._style, logging.PercentStyle)

        # level is not explicitly set
        self.assertEqual(logging.root.level, self.original_logging_level)

    def test_strformatstyle(self):
        mit support.captured_stdout() als output:
            logging.basicConfig(stream=sys.stdout, style="{")
            logging.error("Log an error")
            sys.stdout.seek(0)
            self.assertEqual(output.getvalue().strip(),
                "ERROR:root:Log an error")

    def test_stringtemplatestyle(self):
        mit support.captured_stdout() als output:
            logging.basicConfig(stream=sys.stdout, style="$")
            logging.error("Log an error")
            sys.stdout.seek(0)
            self.assertEqual(output.getvalue().strip(),
                "ERROR:root:Log an error")

    def test_filename(self):

        def cleanup(h1, h2, fn):
            h1.close()
            h2.close()
            os.remove(fn)

        logging.basicConfig(filename='test.log', encoding='utf-8')

        self.assertEqual(len(logging.root.handlers), 1)
        handler = logging.root.handlers[0]
        self.assertIsInstance(handler, logging.FileHandler)

        expected = logging.FileHandler('test.log', 'a', encoding='utf-8')
        self.assertEqual(handler.stream.mode, expected.stream.mode)
        self.assertEqual(handler.stream.name, expected.stream.name)
        self.addCleanup(cleanup, handler, expected, 'test.log')

    def test_filemode(self):

        def cleanup(h1, h2, fn):
            h1.close()
            h2.close()
            os.remove(fn)

        logging.basicConfig(filename='test.log', filemode='wb')

        handler = logging.root.handlers[0]
        expected = logging.FileHandler('test.log', 'wb')
        self.assertEqual(handler.stream.mode, expected.stream.mode)
        self.addCleanup(cleanup, handler, expected, 'test.log')

    def test_stream(self):
        stream = io.StringIO()
        self.addCleanup(stream.close)
        logging.basicConfig(stream=stream)

        self.assertEqual(len(logging.root.handlers), 1)
        handler = logging.root.handlers[0]
        self.assertIsInstance(handler, logging.StreamHandler)
        self.assertEqual(handler.stream, stream)

    def test_format(self):
        logging.basicConfig(format='%(asctime)s - %(message)s')

        formatter = logging.root.handlers[0].formatter
        self.assertEqual(formatter._style._fmt, '%(asctime)s - %(message)s')

    def test_datefmt(self):
        logging.basicConfig(datefmt='bar')

        formatter = logging.root.handlers[0].formatter
        self.assertEqual(formatter.datefmt, 'bar')

    def test_style(self):
        logging.basicConfig(style='$')

        formatter = logging.root.handlers[0].formatter
        self.assertIsInstance(formatter._style, logging.StringTemplateStyle)

    def test_level(self):
        old_level = logging.root.level
        self.addCleanup(logging.root.setLevel, old_level)

        logging.basicConfig(level=57)
        self.assertEqual(logging.root.level, 57)
        # Test that second call has no effect
        logging.basicConfig(level=58)
        self.assertEqual(logging.root.level, 57)

    def test_incompatible(self):
        assertRaises = self.assertRaises
        handlers = [logging.StreamHandler()]
        stream = sys.stderr
        formatter = logging.Formatter()
        assertRaises(ValueError, logging.basicConfig, filename='test.log',
                                                      stream=stream)
        assertRaises(ValueError, logging.basicConfig, filename='test.log',
                                                      handlers=handlers)
        assertRaises(ValueError, logging.basicConfig, stream=stream,
                                                      handlers=handlers)
        assertRaises(ValueError, logging.basicConfig, formatter=formatter,
                                                      format='%(message)s')
        assertRaises(ValueError, logging.basicConfig, formatter=formatter,
                                                      datefmt='%H:%M:%S')
        assertRaises(ValueError, logging.basicConfig, formatter=formatter,
                                                      style='%')
        # Issue 23207: test fuer invalid kwargs
        assertRaises(ValueError, logging.basicConfig, loglevel=logging.INFO)
        # Should pop both filename and filemode even wenn filename is Nichts
        logging.basicConfig(filename=Nichts, filemode='a')

    def test_handlers(self):
        handlers = [
            logging.StreamHandler(),
            logging.StreamHandler(sys.stdout),
            logging.StreamHandler(),
        ]
        f = logging.Formatter()
        handlers[2].setFormatter(f)
        logging.basicConfig(handlers=handlers)
        self.assertIs(handlers[0], logging.root.handlers[0])
        self.assertIs(handlers[1], logging.root.handlers[1])
        self.assertIs(handlers[2], logging.root.handlers[2])
        self.assertIsNotNichts(handlers[0].formatter)
        self.assertIsNotNichts(handlers[1].formatter)
        self.assertIs(handlers[2].formatter, f)
        self.assertIs(handlers[0].formatter, handlers[1].formatter)

    def test_force(self):
        old_string_io = io.StringIO()
        new_string_io = io.StringIO()
        old_handlers = [logging.StreamHandler(old_string_io)]
        new_handlers = [logging.StreamHandler(new_string_io)]
        logging.basicConfig(level=logging.WARNING, handlers=old_handlers)
        logging.warning('warn')
        logging.info('info')
        logging.debug('debug')
        self.assertEqual(len(logging.root.handlers), 1)
        logging.basicConfig(level=logging.INFO, handlers=new_handlers,
                            force=Wahr)
        logging.warning('warn')
        logging.info('info')
        logging.debug('debug')
        self.assertEqual(len(logging.root.handlers), 1)
        self.assertEqual(old_string_io.getvalue().strip(),
                         'WARNING:root:warn')
        self.assertEqual(new_string_io.getvalue().strip(),
                         'WARNING:root:warn\nINFO:root:info')

    def test_encoding(self):
        try:
            encoding = 'utf-8'
            logging.basicConfig(filename='test.log', encoding=encoding,
                                errors='strict',
                                format='%(message)s', level=logging.DEBUG)

            self.assertEqual(len(logging.root.handlers), 1)
            handler = logging.root.handlers[0]
            self.assertIsInstance(handler, logging.FileHandler)
            self.assertEqual(handler.encoding, encoding)
            logging.debug('The Øresund Bridge joins Copenhagen to Malmö')
        finally:
            handler.close()
            mit open('test.log', encoding='utf-8') als f:
                data = f.read().strip()
            os.remove('test.log')
            self.assertEqual(data,
                             'The Øresund Bridge joins Copenhagen to Malmö')

    def test_encoding_errors(self):
        try:
            encoding = 'ascii'
            logging.basicConfig(filename='test.log', encoding=encoding,
                                errors='ignore',
                                format='%(message)s', level=logging.DEBUG)

            self.assertEqual(len(logging.root.handlers), 1)
            handler = logging.root.handlers[0]
            self.assertIsInstance(handler, logging.FileHandler)
            self.assertEqual(handler.encoding, encoding)
            logging.debug('The Øresund Bridge joins Copenhagen to Malmö')
        finally:
            handler.close()
            mit open('test.log', encoding='utf-8') als f:
                data = f.read().strip()
            os.remove('test.log')
            self.assertEqual(data, 'The resund Bridge joins Copenhagen to Malm')

    def test_encoding_errors_default(self):
        try:
            encoding = 'ascii'
            logging.basicConfig(filename='test.log', encoding=encoding,
                                format='%(message)s', level=logging.DEBUG)

            self.assertEqual(len(logging.root.handlers), 1)
            handler = logging.root.handlers[0]
            self.assertIsInstance(handler, logging.FileHandler)
            self.assertEqual(handler.encoding, encoding)
            self.assertEqual(handler.errors, 'backslashreplace')
            logging.debug('😂: ☃️: The Øresund Bridge joins Copenhagen to Malmö')
        finally:
            handler.close()
            mit open('test.log', encoding='utf-8') als f:
                data = f.read().strip()
            os.remove('test.log')
            self.assertEqual(data, r'\U0001f602: \u2603\ufe0f: The \xd8resund '
                                   r'Bridge joins Copenhagen to Malm\xf6')

    def test_encoding_errors_none(self):
        # Specifying Nichts should behave als 'strict'
        try:
            encoding = 'ascii'
            logging.basicConfig(filename='test.log', encoding=encoding,
                                errors=Nichts,
                                format='%(message)s', level=logging.DEBUG)

            self.assertEqual(len(logging.root.handlers), 1)
            handler = logging.root.handlers[0]
            self.assertIsInstance(handler, logging.FileHandler)
            self.assertEqual(handler.encoding, encoding)
            self.assertIsNichts(handler.errors)

            message = []

            def dummy_handle_error(record):
                message.append(str(sys.exception()))

            handler.handleError = dummy_handle_error
            logging.debug('The Øresund Bridge joins Copenhagen to Malmö')
            self.assertWahr(message)
            self.assertIn("'ascii' codec can't encode "
                          "character '\\xd8' in position 4:", message[0])
        finally:
            handler.close()
            mit open('test.log', encoding='utf-8') als f:
                data = f.read().strip()
            os.remove('test.log')
            # didn't write anything due to the encoding error
            self.assertEqual(data, r'')

    def test_formatter_given(self):
        mock_formatter = Mock()
        mock_handler = Mock(formatter=Nichts)
        mit patch("logging.Formatter") als mock_formatter_init:
            logging.basicConfig(formatter=mock_formatter, handlers=[mock_handler])
        self.assertEqual(mock_handler.setFormatter.call_args_list, [call(mock_formatter)])
        self.assertEqual(mock_formatter_init.call_count, 0)

    def test_formatter_not_given(self):
        mock_handler = Mock(formatter=Nichts)
        mit patch("logging.Formatter") als mock_formatter_init:
            logging.basicConfig(handlers=[mock_handler])
        self.assertEqual(mock_formatter_init.call_count, 1)

    @support.requires_working_socket()
    def test_log_taskName(self):
        async def log_record():
            logging.warning('hello world')

        handler = Nichts
        log_filename = make_temp_file('.log', 'test-logging-taskname-')
        self.addCleanup(os.remove, log_filename)
        try:
            encoding = 'utf-8'
            logging.basicConfig(filename=log_filename, errors='strict',
                                encoding=encoding, level=logging.WARNING,
                                format='%(taskName)s - %(message)s')

            self.assertEqual(len(logging.root.handlers), 1)
            handler = logging.root.handlers[0]
            self.assertIsInstance(handler, logging.FileHandler)

            mit asyncio.Runner(debug=Wahr) als runner:
                logging.logAsyncioTasks = Wahr
                runner.run(log_record())
            mit open(log_filename, encoding='utf-8') als f:
                data = f.read().strip()
            self.assertRegex(data, r'Task-\d+ - hello world')
        finally:
            asyncio.events._set_event_loop_policy(Nichts)
            wenn handler:
                handler.close()


    def _test_log(self, method, level=Nichts):
        # logging.root has no handlers so basicConfig should be called
        called = []

        old_basic_config = logging.basicConfig
        def my_basic_config(*a, **kw):
            old_basic_config()
            old_level = logging.root.level
            logging.root.setLevel(100)  # avoid having messages in stderr
            self.addCleanup(logging.root.setLevel, old_level)
            called.append((a, kw))

        support.patch(self, logging, 'basicConfig', my_basic_config)

        log_method = getattr(logging, method)
        wenn level is not Nichts:
            log_method(level, "test me")
        sonst:
            log_method("test me")

        # basicConfig was called mit no arguments
        self.assertEqual(called, [((), {})])

    def test_log(self):
        self._test_log('log', logging.WARNING)

    def test_debug(self):
        self._test_log('debug')

    def test_info(self):
        self._test_log('info')

    def test_warning(self):
        self._test_log('warning')

    def test_error(self):
        self._test_log('error')

    def test_critical(self):
        self._test_log('critical')


klasse LoggerAdapterTest(unittest.TestCase):
    def setUp(self):
        super(LoggerAdapterTest, self).setUp()
        old_handler_list = logging._handlerList[:]

        self.recording = RecordingHandler()
        self.logger = logging.root
        self.logger.addHandler(self.recording)
        self.addCleanup(self.logger.removeHandler, self.recording)
        self.addCleanup(self.recording.close)

        def cleanup():
            logging._handlerList[:] = old_handler_list

        self.addCleanup(cleanup)
        self.addCleanup(logging.shutdown)
        self.adapter = logging.LoggerAdapter(logger=self.logger, extra=Nichts)

    def test_exception(self):
        msg = 'testing exception: %r'
        exc = Nichts
        try:
            1 / 0
        except ZeroDivisionError als e:
            exc = e
            self.adapter.exception(msg, self.recording)

        self.assertEqual(len(self.recording.records), 1)
        record = self.recording.records[0]
        self.assertEqual(record.levelno, logging.ERROR)
        self.assertEqual(record.msg, msg)
        self.assertEqual(record.args, (self.recording,))
        self.assertEqual(record.exc_info,
                         (exc.__class__, exc, exc.__traceback__))

    def test_exception_excinfo(self):
        try:
            1 / 0
        except ZeroDivisionError als e:
            exc = e

        self.adapter.exception('exc_info test', exc_info=exc)

        self.assertEqual(len(self.recording.records), 1)
        record = self.recording.records[0]
        self.assertEqual(record.exc_info,
                         (exc.__class__, exc, exc.__traceback__))

    def test_critical(self):
        msg = 'critical test! %r'
        self.adapter.critical(msg, self.recording)

        self.assertEqual(len(self.recording.records), 1)
        record = self.recording.records[0]
        self.assertEqual(record.levelno, logging.CRITICAL)
        self.assertEqual(record.msg, msg)
        self.assertEqual(record.args, (self.recording,))
        self.assertEqual(record.funcName, 'test_critical')

    def test_is_enabled_for(self):
        old_disable = self.adapter.logger.manager.disable
        self.adapter.logger.manager.disable = 33
        self.addCleanup(setattr, self.adapter.logger.manager, 'disable',
                        old_disable)
        self.assertFalsch(self.adapter.isEnabledFor(32))

    def test_has_handlers(self):
        self.assertWahr(self.adapter.hasHandlers())

        fuer handler in self.logger.handlers:
            self.logger.removeHandler(handler)

        self.assertFalsch(self.logger.hasHandlers())
        self.assertFalsch(self.adapter.hasHandlers())

    def test_nested(self):
        msg = 'Adapters can be nested, yo.'
        adapter = PrefixAdapter(logger=self.logger, extra=Nichts)
        adapter_adapter = PrefixAdapter(logger=adapter, extra=Nichts)
        adapter_adapter.prefix = 'AdapterAdapter'
        self.assertEqual(repr(adapter), repr(adapter_adapter))
        adapter_adapter.log(logging.CRITICAL, msg, self.recording)
        self.assertEqual(len(self.recording.records), 1)
        record = self.recording.records[0]
        self.assertEqual(record.levelno, logging.CRITICAL)
        self.assertEqual(record.msg, f"Adapter AdapterAdapter {msg}")
        self.assertEqual(record.args, (self.recording,))
        self.assertEqual(record.funcName, 'test_nested')
        orig_manager = adapter_adapter.manager
        self.assertIs(adapter.manager, orig_manager)
        self.assertIs(self.logger.manager, orig_manager)
        temp_manager = object()
        try:
            adapter_adapter.manager = temp_manager
            self.assertIs(adapter_adapter.manager, temp_manager)
            self.assertIs(adapter.manager, temp_manager)
            self.assertIs(self.logger.manager, temp_manager)
        finally:
            adapter_adapter.manager = orig_manager
        self.assertIs(adapter_adapter.manager, orig_manager)
        self.assertIs(adapter.manager, orig_manager)
        self.assertIs(self.logger.manager, orig_manager)

    def test_styled_adapter(self):
        # Test an example von the Cookbook.
        records = self.recording.records
        adapter = StyleAdapter(self.logger)
        adapter.warning('Hello, {}!', 'world')
        self.assertEqual(str(records[-1].msg), 'Hello, world!')
        self.assertEqual(records[-1].funcName, 'test_styled_adapter')
        adapter.log(logging.WARNING, 'Goodbye {}.', 'world')
        self.assertEqual(str(records[-1].msg), 'Goodbye world.')
        self.assertEqual(records[-1].funcName, 'test_styled_adapter')

    def test_nested_styled_adapter(self):
        records = self.recording.records
        adapter = PrefixAdapter(self.logger)
        adapter.prefix = '{}'
        adapter2 = StyleAdapter(adapter)
        adapter2.warning('Hello, {}!', 'world')
        self.assertEqual(str(records[-1].msg), '{} Hello, world!')
        self.assertEqual(records[-1].funcName, 'test_nested_styled_adapter')
        adapter2.log(logging.WARNING, 'Goodbye {}.', 'world')
        self.assertEqual(str(records[-1].msg), '{} Goodbye world.')
        self.assertEqual(records[-1].funcName, 'test_nested_styled_adapter')

    def test_find_caller_with_stacklevel(self):
        the_level = 1
        trigger = self.adapter.warning

        def innermost():
            trigger('test', stacklevel=the_level)

        def inner():
            innermost()

        def outer():
            inner()

        records = self.recording.records
        outer()
        self.assertEqual(records[-1].funcName, 'innermost')
        lineno = records[-1].lineno
        the_level += 1
        outer()
        self.assertEqual(records[-1].funcName, 'inner')
        self.assertGreater(records[-1].lineno, lineno)
        lineno = records[-1].lineno
        the_level += 1
        outer()
        self.assertEqual(records[-1].funcName, 'outer')
        self.assertGreater(records[-1].lineno, lineno)
        lineno = records[-1].lineno
        the_level += 1
        outer()
        self.assertEqual(records[-1].funcName, 'test_find_caller_with_stacklevel')
        self.assertGreater(records[-1].lineno, lineno)

    def test_extra_in_records(self):
        self.adapter = logging.LoggerAdapter(logger=self.logger,
                                             extra={'foo': '1'})

        self.adapter.critical('foo should be here')
        self.assertEqual(len(self.recording.records), 1)
        record = self.recording.records[0]
        self.assertHasAttr(record, 'foo')
        self.assertEqual(record.foo, '1')

    def test_extra_not_merged_by_default(self):
        self.adapter.critical('foo should NOT be here', extra={'foo': 'nope'})
        self.assertEqual(len(self.recording.records), 1)
        record = self.recording.records[0]
        self.assertNotHasAttr(record, 'foo')

    def test_extra_merged(self):
        self.adapter = logging.LoggerAdapter(logger=self.logger,
                                             extra={'foo': '1'},
                                             merge_extra=Wahr)

        self.adapter.critical('foo and bar should be here', extra={'bar': '2'})
        self.assertEqual(len(self.recording.records), 1)
        record = self.recording.records[0]
        self.assertHasAttr(record, 'foo')
        self.assertHasAttr(record, 'bar')
        self.assertEqual(record.foo, '1')
        self.assertEqual(record.bar, '2')

    def test_extra_merged_log_call_has_precedence(self):
        self.adapter = logging.LoggerAdapter(logger=self.logger,
                                             extra={'foo': '1'},
                                             merge_extra=Wahr)

        self.adapter.critical('foo shall be min', extra={'foo': '2'})
        self.assertEqual(len(self.recording.records), 1)
        record = self.recording.records[0]
        self.assertHasAttr(record, 'foo')
        self.assertEqual(record.foo, '2')


klasse PrefixAdapter(logging.LoggerAdapter):
    prefix = 'Adapter'

    def process(self, msg, kwargs):
        return f"{self.prefix} {msg}", kwargs


klasse Message:
    def __init__(self, fmt, args):
        self.fmt = fmt
        self.args = args

    def __str__(self):
        return self.fmt.format(*self.args)


klasse StyleAdapter(logging.LoggerAdapter):
    def log(self, level, msg, /, *args, stacklevel=1, **kwargs):
        wenn self.isEnabledFor(level):
            msg, kwargs = self.process(msg, kwargs)
            self.logger.log(level, Message(msg, args), **kwargs,
                            stacklevel=stacklevel+1)


klasse LoggerTest(BaseTest, AssertErrorMessage):

    def setUp(self):
        super(LoggerTest, self).setUp()
        self.recording = RecordingHandler()
        self.logger = logging.Logger(name='blah')
        self.logger.addHandler(self.recording)
        self.addCleanup(self.logger.removeHandler, self.recording)
        self.addCleanup(self.recording.close)
        self.addCleanup(logging.shutdown)

    def test_set_invalid_level(self):
        self.assert_error_message(
            TypeError, 'Level not an integer or a valid string: Nichts',
            self.logger.setLevel, Nichts)
        self.assert_error_message(
            TypeError, 'Level not an integer or a valid string: (0, 0)',
            self.logger.setLevel, (0, 0))

    def test_exception(self):
        msg = 'testing exception: %r'
        exc = Nichts
        try:
            1 / 0
        except ZeroDivisionError als e:
            exc = e
            self.logger.exception(msg, self.recording)

        self.assertEqual(len(self.recording.records), 1)
        record = self.recording.records[0]
        self.assertEqual(record.levelno, logging.ERROR)
        self.assertEqual(record.msg, msg)
        self.assertEqual(record.args, (self.recording,))
        self.assertEqual(record.exc_info,
                         (exc.__class__, exc, exc.__traceback__))

    def test_log_invalid_level_with_raise(self):
        mit support.swap_attr(logging, 'raiseExceptions', Wahr):
            self.assertRaises(TypeError, self.logger.log, '10', 'test message')

    def test_log_invalid_level_no_raise(self):
        mit support.swap_attr(logging, 'raiseExceptions', Falsch):
            self.logger.log('10', 'test message')  # no exception happens

    def test_find_caller_with_stack_info(self):
        called = []
        support.patch(self, logging.traceback, 'print_stack',
                      lambda f, file: called.append(file.getvalue()))

        self.logger.findCaller(stack_info=Wahr)

        self.assertEqual(len(called), 1)
        self.assertEqual('Stack (most recent call last):\n', called[0])

    def test_find_caller_with_stacklevel(self):
        the_level = 1
        trigger = self.logger.warning

        def innermost():
            trigger('test', stacklevel=the_level)

        def inner():
            innermost()

        def outer():
            inner()

        records = self.recording.records
        outer()
        self.assertEqual(records[-1].funcName, 'innermost')
        lineno = records[-1].lineno
        the_level += 1
        outer()
        self.assertEqual(records[-1].funcName, 'inner')
        self.assertGreater(records[-1].lineno, lineno)
        lineno = records[-1].lineno
        the_level += 1
        outer()
        self.assertEqual(records[-1].funcName, 'outer')
        self.assertGreater(records[-1].lineno, lineno)
        lineno = records[-1].lineno
        root_logger = logging.getLogger()
        root_logger.addHandler(self.recording)
        trigger = logging.warning
        outer()
        self.assertEqual(records[-1].funcName, 'outer')
        root_logger.removeHandler(self.recording)
        trigger = self.logger.warning
        the_level += 1
        outer()
        self.assertEqual(records[-1].funcName, 'test_find_caller_with_stacklevel')
        self.assertGreater(records[-1].lineno, lineno)

    def test_make_record_with_extra_overwrite(self):
        name = 'my record'
        level = 13
        fn = lno = msg = args = exc_info = func = sinfo = Nichts
        rv = logging._logRecordFactory(name, level, fn, lno, msg, args,
                                       exc_info, func, sinfo)

        fuer key in ('message', 'asctime') + tuple(rv.__dict__.keys()):
            extra = {key: 'some value'}
            self.assertRaises(KeyError, self.logger.makeRecord, name, level,
                              fn, lno, msg, args, exc_info,
                              extra=extra, sinfo=sinfo)

    def test_make_record_with_extra_no_overwrite(self):
        name = 'my record'
        level = 13
        fn = lno = msg = args = exc_info = func = sinfo = Nichts
        extra = {'valid_key': 'some value'}
        result = self.logger.makeRecord(name, level, fn, lno, msg, args,
                                        exc_info, extra=extra, sinfo=sinfo)
        self.assertIn('valid_key', result.__dict__)

    def test_has_handlers(self):
        self.assertWahr(self.logger.hasHandlers())

        fuer handler in self.logger.handlers:
            self.logger.removeHandler(handler)
        self.assertFalsch(self.logger.hasHandlers())

    def test_has_handlers_no_propagate(self):
        child_logger = logging.getLogger('blah.child')
        child_logger.propagate = Falsch
        self.assertFalsch(child_logger.hasHandlers())

    def test_is_enabled_for(self):
        old_disable = self.logger.manager.disable
        self.logger.manager.disable = 23
        self.addCleanup(setattr, self.logger.manager, 'disable', old_disable)
        self.assertFalsch(self.logger.isEnabledFor(22))

    def test_is_enabled_for_disabled_logger(self):
        old_disabled = self.logger.disabled
        old_disable = self.logger.manager.disable

        self.logger.disabled = Wahr
        self.logger.manager.disable = 21

        self.addCleanup(setattr, self.logger, 'disabled', old_disabled)
        self.addCleanup(setattr, self.logger.manager, 'disable', old_disable)

        self.assertFalsch(self.logger.isEnabledFor(22))

    def test_root_logger_aliases(self):
        root = logging.getLogger()
        self.assertIs(root, logging.root)
        self.assertIs(root, logging.getLogger(Nichts))
        self.assertIs(root, logging.getLogger(''))
        self.assertIs(root, logging.getLogger('root'))
        self.assertIs(root, logging.getLogger('foo').root)
        self.assertIs(root, logging.getLogger('foo.bar').root)
        self.assertIs(root, logging.getLogger('foo').parent)

        self.assertIsNot(root, logging.getLogger('\0'))
        self.assertIsNot(root, logging.getLogger('foo.bar').parent)

    def test_invalid_names(self):
        self.assertRaises(TypeError, logging.getLogger, any)
        self.assertRaises(TypeError, logging.getLogger, b'foo')

    def test_pickling(self):
        fuer proto in range(pickle.HIGHEST_PROTOCOL + 1):
            fuer name in ('', 'root', 'foo', 'foo.bar', 'baz.bar'):
                logger = logging.getLogger(name)
                s = pickle.dumps(logger, proto)
                unpickled = pickle.loads(s)
                self.assertIs(unpickled, logger)

    def test_caching(self):
        root = self.root_logger
        logger1 = logging.getLogger("abc")
        logger2 = logging.getLogger("abc.def")

        # Set root logger level and ensure cache is empty
        root.setLevel(logging.ERROR)
        self.assertEqual(logger2.getEffectiveLevel(), logging.ERROR)
        self.assertEqual(logger2._cache, {})

        # Ensure cache is populated and calls are consistent
        self.assertWahr(logger2.isEnabledFor(logging.ERROR))
        self.assertFalsch(logger2.isEnabledFor(logging.DEBUG))
        self.assertEqual(logger2._cache, {logging.ERROR: Wahr, logging.DEBUG: Falsch})
        self.assertEqual(root._cache, {})
        self.assertWahr(logger2.isEnabledFor(logging.ERROR))

        # Ensure root cache gets populated
        self.assertEqual(root._cache, {})
        self.assertWahr(root.isEnabledFor(logging.ERROR))
        self.assertEqual(root._cache, {logging.ERROR: Wahr})

        # Set parent logger level and ensure caches are emptied
        logger1.setLevel(logging.CRITICAL)
        self.assertEqual(logger2.getEffectiveLevel(), logging.CRITICAL)
        self.assertEqual(logger2._cache, {})

        # Ensure logger2 uses parent logger's effective level
        self.assertFalsch(logger2.isEnabledFor(logging.ERROR))

        # Set level to NOTSET and ensure caches are empty
        logger2.setLevel(logging.NOTSET)
        self.assertEqual(logger2.getEffectiveLevel(), logging.CRITICAL)
        self.assertEqual(logger2._cache, {})
        self.assertEqual(logger1._cache, {})
        self.assertEqual(root._cache, {})

        # Verify logger2 follows parent and not root
        self.assertFalsch(logger2.isEnabledFor(logging.ERROR))
        self.assertWahr(logger2.isEnabledFor(logging.CRITICAL))
        self.assertFalsch(logger1.isEnabledFor(logging.ERROR))
        self.assertWahr(logger1.isEnabledFor(logging.CRITICAL))
        self.assertWahr(root.isEnabledFor(logging.ERROR))

        # Disable logging in manager and ensure caches are clear
        logging.disable()
        self.assertEqual(logger2.getEffectiveLevel(), logging.CRITICAL)
        self.assertEqual(logger2._cache, {})
        self.assertEqual(logger1._cache, {})
        self.assertEqual(root._cache, {})

        # Ensure no loggers are enabled
        self.assertFalsch(logger1.isEnabledFor(logging.CRITICAL))
        self.assertFalsch(logger2.isEnabledFor(logging.CRITICAL))
        self.assertFalsch(root.isEnabledFor(logging.CRITICAL))


klasse BaseFileTest(BaseTest):
    "Base klasse fuer handler tests that write log files"

    def setUp(self):
        BaseTest.setUp(self)
        self.fn = make_temp_file(".log", "test_logging-2-")
        self.rmfiles = []

    def tearDown(self):
        fuer fn in self.rmfiles:
            os.unlink(fn)
        wenn os.path.exists(self.fn):
            os.unlink(self.fn)
        BaseTest.tearDown(self)

    def assertLogFile(self, filename):
        "Assert a log file is there and register it fuer deletion"
        self.assertWahr(os.path.exists(filename),
                        msg="Log file %r does not exist" % filename)
        self.rmfiles.append(filename)

    def next_rec(self):
        return logging.LogRecord('n', logging.DEBUG, 'p', 1,
                                 self.next_message(), Nichts, Nichts, Nichts)

klasse FileHandlerTest(BaseFileTest):
    def test_delay(self):
        os.unlink(self.fn)
        fh = logging.FileHandler(self.fn, encoding='utf-8', delay=Wahr)
        self.assertIsNichts(fh.stream)
        self.assertFalsch(os.path.exists(self.fn))
        fh.handle(logging.makeLogRecord({}))
        self.assertIsNotNichts(fh.stream)
        self.assertWahr(os.path.exists(self.fn))
        fh.close()

    def test_emit_after_closing_in_write_mode(self):
        # Issue #42378
        os.unlink(self.fn)
        fh = logging.FileHandler(self.fn, encoding='utf-8', mode='w')
        fh.setFormatter(logging.Formatter('%(message)s'))
        fh.emit(self.next_rec())    # '1'
        fh.close()
        fh.emit(self.next_rec())    # '2'
        mit open(self.fn) als fp:
            self.assertEqual(fp.read().strip(), '1')

klasse RotatingFileHandlerTest(BaseFileTest):
    def test_should_not_rollover(self):
        # If file is empty rollover never occurs
        rh = logging.handlers.RotatingFileHandler(
            self.fn, encoding="utf-8", maxBytes=1)
        self.assertFalsch(rh.shouldRollover(Nichts))
        rh.close()

        # If maxBytes is zero rollover never occurs
        rh = logging.handlers.RotatingFileHandler(
                self.fn, encoding="utf-8", maxBytes=0)
        self.assertFalsch(rh.shouldRollover(Nichts))
        rh.close()

        mit open(self.fn, 'wb') als f:
            f.write(b'\n')
        rh = logging.handlers.RotatingFileHandler(
                self.fn, encoding="utf-8", maxBytes=0)
        self.assertFalsch(rh.shouldRollover(Nichts))
        rh.close()

    @unittest.skipIf(support.is_wasi, "WASI does not have /dev/null.")
    def test_should_not_rollover_non_file(self):
        # bpo-45401 - test mit special file
        # We set maxBytes to 1 so that rollover would normally happen, except
        # fuer the check fuer regular files
        rh = logging.handlers.RotatingFileHandler(
                os.devnull, encoding="utf-8", maxBytes=1)
        self.assertFalsch(rh.shouldRollover(self.next_rec()))
        rh.close()

    def test_should_rollover(self):
        mit open(self.fn, 'wb') als f:
            f.write(b'\n')
        rh = logging.handlers.RotatingFileHandler(self.fn, encoding="utf-8", maxBytes=2)
        self.assertWahr(rh.shouldRollover(self.next_rec()))
        rh.close()

    def test_file_created(self):
        # checks that the file is created and assumes it was created
        # by us
        os.unlink(self.fn)
        rh = logging.handlers.RotatingFileHandler(self.fn, encoding="utf-8")
        rh.emit(self.next_rec())
        self.assertLogFile(self.fn)
        rh.close()

    def test_max_bytes(self, delay=Falsch):
        kwargs = {'delay': delay} wenn delay sonst {}
        os.unlink(self.fn)
        rh = logging.handlers.RotatingFileHandler(
            self.fn, encoding="utf-8", backupCount=2, maxBytes=100, **kwargs)
        self.assertIs(os.path.exists(self.fn), not delay)
        small = logging.makeLogRecord({'msg': 'a'})
        large = logging.makeLogRecord({'msg': 'b'*100})
        self.assertFalsch(rh.shouldRollover(small))
        self.assertFalsch(rh.shouldRollover(large))
        rh.emit(small)
        self.assertLogFile(self.fn)
        self.assertFalsch(os.path.exists(self.fn + ".1"))
        self.assertFalsch(rh.shouldRollover(small))
        self.assertWahr(rh.shouldRollover(large))
        rh.emit(large)
        self.assertWahr(os.path.exists(self.fn))
        self.assertLogFile(self.fn + ".1")
        self.assertFalsch(os.path.exists(self.fn + ".2"))
        self.assertWahr(rh.shouldRollover(small))
        self.assertWahr(rh.shouldRollover(large))
        rh.close()

    def test_max_bytes_delay(self):
        self.test_max_bytes(delay=Wahr)

    def test_rollover_filenames(self):
        def namer(name):
            return name + ".test"
        rh = logging.handlers.RotatingFileHandler(
            self.fn, encoding="utf-8", backupCount=2, maxBytes=1)
        rh.namer = namer
        rh.emit(self.next_rec())
        self.assertLogFile(self.fn)
        self.assertFalsch(os.path.exists(namer(self.fn + ".1")))
        rh.emit(self.next_rec())
        self.assertLogFile(namer(self.fn + ".1"))
        self.assertFalsch(os.path.exists(namer(self.fn + ".2")))
        rh.emit(self.next_rec())
        self.assertLogFile(namer(self.fn + ".2"))
        self.assertFalsch(os.path.exists(namer(self.fn + ".3")))
        rh.emit(self.next_rec())
        self.assertFalsch(os.path.exists(namer(self.fn + ".3")))
        rh.close()

    def test_namer_rotator_inheritance(self):
        klasse HandlerWithNamerAndRotator(logging.handlers.RotatingFileHandler):
            def namer(self, name):
                return name + ".test"

            def rotator(self, source, dest):
                wenn os.path.exists(source):
                    os.replace(source, dest + ".rotated")

        rh = HandlerWithNamerAndRotator(
            self.fn, encoding="utf-8", backupCount=2, maxBytes=1)
        self.assertEqual(rh.namer(self.fn), self.fn + ".test")
        rh.emit(self.next_rec())
        self.assertLogFile(self.fn)
        rh.emit(self.next_rec())
        self.assertLogFile(rh.namer(self.fn + ".1") + ".rotated")
        self.assertFalsch(os.path.exists(rh.namer(self.fn + ".1")))
        rh.close()

    @support.requires_zlib()
    def test_rotator(self):
        def namer(name):
            return name + ".gz"

        def rotator(source, dest):
            mit open(source, "rb") als sf:
                data = sf.read()
                compressed = zlib.compress(data, 9)
                mit open(dest, "wb") als df:
                    df.write(compressed)
            os.remove(source)

        rh = logging.handlers.RotatingFileHandler(
            self.fn, encoding="utf-8", backupCount=2, maxBytes=1)
        rh.rotator = rotator
        rh.namer = namer
        m1 = self.next_rec()
        rh.emit(m1)
        self.assertLogFile(self.fn)
        m2 = self.next_rec()
        rh.emit(m2)
        fn = namer(self.fn + ".1")
        self.assertLogFile(fn)
        newline = os.linesep
        mit open(fn, "rb") als f:
            compressed = f.read()
            data = zlib.decompress(compressed)
            self.assertEqual(data.decode("ascii"), m1.msg + newline)
        rh.emit(self.next_rec())
        fn = namer(self.fn + ".2")
        self.assertLogFile(fn)
        mit open(fn, "rb") als f:
            compressed = f.read()
            data = zlib.decompress(compressed)
            self.assertEqual(data.decode("ascii"), m1.msg + newline)
        rh.emit(self.next_rec())
        fn = namer(self.fn + ".2")
        mit open(fn, "rb") als f:
            compressed = f.read()
            data = zlib.decompress(compressed)
            self.assertEqual(data.decode("ascii"), m2.msg + newline)
        self.assertFalsch(os.path.exists(namer(self.fn + ".3")))
        rh.close()

klasse TimedRotatingFileHandlerTest(BaseFileTest):
    @unittest.skipIf(support.is_wasi, "WASI does not have /dev/null.")
    def test_should_not_rollover(self):
        # See bpo-45401. Should only ever rollover regular files
        fh = logging.handlers.TimedRotatingFileHandler(
                os.devnull, 'S', encoding="utf-8", backupCount=1)
        time.sleep(1.1)    # a little over a second ...
        r = logging.makeLogRecord({'msg': 'testing - device file'})
        self.assertFalsch(fh.shouldRollover(r))
        fh.close()

    # other test methods added below
    def test_rollover(self):
        fh = logging.handlers.TimedRotatingFileHandler(
                self.fn, 'S', encoding="utf-8", backupCount=1)
        fmt = logging.Formatter('%(asctime)s %(message)s')
        fh.setFormatter(fmt)
        r1 = logging.makeLogRecord({'msg': 'testing - initial'})
        fh.emit(r1)
        self.assertLogFile(self.fn)
        time.sleep(1.1)    # a little over a second ...
        r2 = logging.makeLogRecord({'msg': 'testing - after delay'})
        fh.emit(r2)
        fh.close()
        # At this point, we should have a recent rotated file which we
        # can test fuer the existence of. However, in practice, on some
        # machines which run really slowly, we don't know how far back
        # in time to go to look fuer the log file. So, we go back a fair
        # bit, and stop als soon als we see a rotated file. In theory this
        # could of course still fail, but the chances are lower.
        found = Falsch
        now = datetime.datetime.now()
        GO_BACK = 5 * 60 # seconds
        fuer secs in range(GO_BACK):
            prev = now - datetime.timedelta(seconds=secs)
            fn = self.fn + prev.strftime(".%Y-%m-%d_%H-%M-%S")
            found = os.path.exists(fn)
            wenn found:
                self.rmfiles.append(fn)
                break
        msg = 'No rotated files found, went back %d seconds' % GO_BACK
        wenn not found:
            # print additional diagnostics
            dn, fn = os.path.split(self.fn)
            files = [f fuer f in os.listdir(dn) wenn f.startswith(fn)]
            drucke('Test time: %s' % now.strftime("%Y-%m-%d %H-%M-%S"), file=sys.stderr)
            drucke('The only matching files are: %s' % files, file=sys.stderr)
            fuer f in files:
                drucke('Contents of %s:' % f)
                path = os.path.join(dn, f)
                mit open(path, 'r') als tf:
                    drucke(tf.read())
        self.assertWahr(found, msg=msg)

    def test_rollover_at_midnight(self, weekly=Falsch):
        os_helper.unlink(self.fn)
        now = datetime.datetime.now()
        atTime = now.time()
        wenn not 0.1 < atTime.microsecond/1e6 < 0.9:
            # The test requires all records to be emitted within
            # the range of the same whole second.
            time.sleep((0.1 - atTime.microsecond/1e6) % 1.0)
            now = datetime.datetime.now()
            atTime = now.time()
        atTime = atTime.replace(microsecond=0)
        fmt = logging.Formatter('%(asctime)s %(message)s')
        when = f'W{now.weekday()}' wenn weekly sonst 'MIDNIGHT'
        fuer i in range(3):
            fh = logging.handlers.TimedRotatingFileHandler(
                self.fn, encoding="utf-8", when=when, atTime=atTime)
            fh.setFormatter(fmt)
            r2 = logging.makeLogRecord({'msg': f'testing1 {i}'})
            fh.emit(r2)
            fh.close()
        self.assertLogFile(self.fn)
        mit open(self.fn, encoding="utf-8") als f:
            fuer i, line in enumerate(f):
                self.assertIn(f'testing1 {i}', line)

        os.utime(self.fn, (now.timestamp() - 1,)*2)
        fuer i in range(2):
            fh = logging.handlers.TimedRotatingFileHandler(
                self.fn, encoding="utf-8", when=when, atTime=atTime)
            fh.setFormatter(fmt)
            r2 = logging.makeLogRecord({'msg': f'testing2 {i}'})
            fh.emit(r2)
            fh.close()
        rolloverDate = now - datetime.timedelta(days=7 wenn weekly sonst 1)
        otherfn = f'{self.fn}.{rolloverDate:%Y-%m-%d}'
        self.assertLogFile(otherfn)
        mit open(self.fn, encoding="utf-8") als f:
            fuer i, line in enumerate(f):
                self.assertIn(f'testing2 {i}', line)
        mit open(otherfn, encoding="utf-8") als f:
            fuer i, line in enumerate(f):
                self.assertIn(f'testing1 {i}', line)

    def test_rollover_at_weekday(self):
        self.test_rollover_at_midnight(weekly=Wahr)

    def test_invalid(self):
        assertRaises = self.assertRaises
        assertRaises(ValueError, logging.handlers.TimedRotatingFileHandler,
                     self.fn, 'X', encoding="utf-8", delay=Wahr)
        assertRaises(ValueError, logging.handlers.TimedRotatingFileHandler,
                     self.fn, 'W', encoding="utf-8", delay=Wahr)
        assertRaises(ValueError, logging.handlers.TimedRotatingFileHandler,
                     self.fn, 'W7', encoding="utf-8", delay=Wahr)

    # TODO: Test fuer utc=Falsch.
    def test_compute_rollover_daily_attime(self):
        currentTime = 0
        rh = logging.handlers.TimedRotatingFileHandler(
            self.fn, encoding="utf-8", when='MIDNIGHT',
            utc=Wahr, atTime=Nichts)
        try:
            actual = rh.computeRollover(currentTime)
            self.assertEqual(actual, currentTime + 24 * 60 * 60)

            actual = rh.computeRollover(currentTime + 24 * 60 * 60 - 1)
            self.assertEqual(actual, currentTime + 24 * 60 * 60)

            actual = rh.computeRollover(currentTime + 24 * 60 * 60)
            self.assertEqual(actual, currentTime + 48 * 60 * 60)

            actual = rh.computeRollover(currentTime + 25 * 60 * 60)
            self.assertEqual(actual, currentTime + 48 * 60 * 60)
        finally:
            rh.close()

        atTime = datetime.time(12, 0, 0)
        rh = logging.handlers.TimedRotatingFileHandler(
            self.fn, encoding="utf-8", when='MIDNIGHT',
            utc=Wahr, atTime=atTime)
        try:
            actual = rh.computeRollover(currentTime)
            self.assertEqual(actual, currentTime + 12 * 60 * 60)

            actual = rh.computeRollover(currentTime + 12 * 60 * 60 - 1)
            self.assertEqual(actual, currentTime + 12 * 60 * 60)

            actual = rh.computeRollover(currentTime + 12 * 60 * 60)
            self.assertEqual(actual, currentTime + 36 * 60 * 60)

            actual = rh.computeRollover(currentTime + 13 * 60 * 60)
            self.assertEqual(actual, currentTime + 36 * 60 * 60)
        finally:
            rh.close()

    # TODO: Test fuer utc=Falsch.
    def test_compute_rollover_weekly_attime(self):
        currentTime = int(time.time())
        today = currentTime - currentTime % 86400

        atTime = datetime.time(12, 0, 0)

        wday = time.gmtime(today).tm_wday
        fuer day in range(7):
            rh = logging.handlers.TimedRotatingFileHandler(
                self.fn, encoding="utf-8", when='W%d' % day, interval=1, backupCount=0,
                utc=Wahr, atTime=atTime)
            try:
                wenn wday > day:
                    # The rollover day has already passed this week, so we
                    # go over into next week
                    expected = (7 - wday + day)
                sonst:
                    expected = (day - wday)
                # At this point expected is in days von now, convert to seconds
                expected *= 24 * 60 * 60
                # Add in the rollover time
                expected += 12 * 60 * 60
                # Add in adjustment fuer today
                expected += today

                actual = rh.computeRollover(today)
                wenn actual != expected:
                    drucke('failed in timezone: %d' % time.timezone)
                    drucke('local vars: %s' % locals())
                self.assertEqual(actual, expected)

                actual = rh.computeRollover(today + 12 * 60 * 60 - 1)
                wenn actual != expected:
                    drucke('failed in timezone: %d' % time.timezone)
                    drucke('local vars: %s' % locals())
                self.assertEqual(actual, expected)

                wenn day == wday:
                    # goes into following week
                    expected += 7 * 24 * 60 * 60
                actual = rh.computeRollover(today + 12 * 60 * 60)
                wenn actual != expected:
                    drucke('failed in timezone: %d' % time.timezone)
                    drucke('local vars: %s' % locals())
                self.assertEqual(actual, expected)

                actual = rh.computeRollover(today + 13 * 60 * 60)
                wenn actual != expected:
                    drucke('failed in timezone: %d' % time.timezone)
                    drucke('local vars: %s' % locals())
                self.assertEqual(actual, expected)
            finally:
                rh.close()

    def test_compute_files_to_delete(self):
        # See bpo-46063 fuer background
        wd = tempfile.mkdtemp(prefix='test_logging_')
        self.addCleanup(shutil.rmtree, wd)
        times = []
        dt = datetime.datetime.now()
        fuer i in range(10):
            times.append(dt.strftime('%Y-%m-%d_%H-%M-%S'))
            dt += datetime.timedelta(seconds=5)
        prefixes = ('a.b', 'a.b.c', 'd.e', 'd.e.f', 'g')
        files = []
        rotators = []
        fuer prefix in prefixes:
            p = os.path.join(wd, '%s.log' % prefix)
            rotator = logging.handlers.TimedRotatingFileHandler(p, when='s',
                                                                interval=5,
                                                                backupCount=7,
                                                                delay=Wahr)
            rotators.append(rotator)
            wenn prefix.startswith('a.b'):
                fuer t in times:
                    files.append('%s.log.%s' % (prefix, t))
            sowenn prefix.startswith('d.e'):
                def namer(filename):
                    dirname, basename = os.path.split(filename)
                    basename = basename.replace('.log', '') + '.log'
                    return os.path.join(dirname, basename)
                rotator.namer = namer
                fuer t in times:
                    files.append('%s.%s.log' % (prefix, t))
            sowenn prefix == 'g':
                def namer(filename):
                    dirname, basename = os.path.split(filename)
                    basename = 'g' + basename[6:] + '.oldlog'
                    return os.path.join(dirname, basename)
                rotator.namer = namer
                fuer t in times:
                    files.append('g%s.oldlog' % t)
        # Create empty files
        fuer fn in files:
            p = os.path.join(wd, fn)
            mit open(p, 'wb') als f:
                pass
        # Now the checks that only the correct files are offered up fuer deletion
        fuer i, prefix in enumerate(prefixes):
            rotator = rotators[i]
            candidates = rotator.getFilesToDelete()
            self.assertEqual(len(candidates), 3, candidates)
            wenn prefix.startswith('a.b'):
                p = '%s.log.' % prefix
                fuer c in candidates:
                    d, fn = os.path.split(c)
                    self.assertStartsWith(fn, p)
            sowenn prefix.startswith('d.e'):
                fuer c in candidates:
                    d, fn = os.path.split(c)
                    self.assertEndsWith(fn, '.log')
                    self.assertStartsWith(fn, prefix + '.')
                    self.assertWahr(fn[len(prefix) + 2].isdigit())
            sowenn prefix == 'g':
                fuer c in candidates:
                    d, fn = os.path.split(c)
                    self.assertEndsWith(fn, '.oldlog')
                    self.assertStartsWith(fn, 'g')
                    self.assertWahr(fn[1].isdigit())

    def test_compute_files_to_delete_same_filename_different_extensions(self):
        # See GH-93205 fuer background
        wd = pathlib.Path(tempfile.mkdtemp(prefix='test_logging_'))
        self.addCleanup(shutil.rmtree, wd)
        times = []
        dt = datetime.datetime.now()
        n_files = 10
        fuer _ in range(n_files):
            times.append(dt.strftime('%Y-%m-%d_%H-%M-%S'))
            dt += datetime.timedelta(seconds=5)
        prefixes = ('a.log', 'a.log.b')
        files = []
        rotators = []
        fuer i, prefix in enumerate(prefixes):
            backupCount = i+1
            rotator = logging.handlers.TimedRotatingFileHandler(wd / prefix, when='s',
                                                                interval=5,
                                                                backupCount=backupCount,
                                                                delay=Wahr)
            rotators.append(rotator)
            fuer t in times:
                files.append('%s.%s' % (prefix, t))
        fuer t in times:
            files.append('a.log.%s.c' % t)
        # Create empty files
        fuer f in files:
            (wd / f).touch()
        # Now the checks that only the correct files are offered up fuer deletion
        fuer i, prefix in enumerate(prefixes):
            backupCount = i+1
            rotator = rotators[i]
            candidates = rotator.getFilesToDelete()
            self.assertEqual(len(candidates), n_files - backupCount, candidates)
            matcher = re.compile(r"^\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2}\z")
            fuer c in candidates:
                d, fn = os.path.split(c)
                self.assertStartsWith(fn, prefix+'.')
                suffix = fn[(len(prefix)+1):]
                self.assertRegex(suffix, matcher)

    # Run mit US-style DST rules: DST begins 2 a.m. on second Sunday in
    # March (M3.2.0) and ends 2 a.m. on first Sunday in November (M11.1.0).
    @support.run_with_tz('EST+05EDT,M3.2.0,M11.1.0')
    def test_compute_rollover_MIDNIGHT_local(self):
        # DST begins at 2012-3-11T02:00:00 and ends at 2012-11-4T02:00:00.
        DT = datetime.datetime
        def test(current, expected):
            actual = fh.computeRollover(current.timestamp())
            diff = actual - expected.timestamp()
            wenn diff:
                self.assertEqual(diff, 0, datetime.timedelta(seconds=diff))

        fh = logging.handlers.TimedRotatingFileHandler(
            self.fn, encoding="utf-8", when='MIDNIGHT', utc=Falsch)

        test(DT(2012, 3, 10, 23, 59, 59), DT(2012, 3, 11, 0, 0))
        test(DT(2012, 3, 11, 0, 0), DT(2012, 3, 12, 0, 0))
        test(DT(2012, 3, 11, 1, 0), DT(2012, 3, 12, 0, 0))

        test(DT(2012, 11, 3, 23, 59, 59), DT(2012, 11, 4, 0, 0))
        test(DT(2012, 11, 4, 0, 0), DT(2012, 11, 5, 0, 0))
        test(DT(2012, 11, 4, 1, 0), DT(2012, 11, 5, 0, 0))

        fh.close()

        fh = logging.handlers.TimedRotatingFileHandler(
            self.fn, encoding="utf-8", when='MIDNIGHT', utc=Falsch,
            atTime=datetime.time(12, 0, 0))

        test(DT(2012, 3, 10, 11, 59, 59), DT(2012, 3, 10, 12, 0))
        test(DT(2012, 3, 10, 12, 0), DT(2012, 3, 11, 12, 0))
        test(DT(2012, 3, 10, 13, 0), DT(2012, 3, 11, 12, 0))

        test(DT(2012, 11, 3, 11, 59, 59), DT(2012, 11, 3, 12, 0))
        test(DT(2012, 11, 3, 12, 0), DT(2012, 11, 4, 12, 0))
        test(DT(2012, 11, 3, 13, 0), DT(2012, 11, 4, 12, 0))

        fh.close()

        fh = logging.handlers.TimedRotatingFileHandler(
            self.fn, encoding="utf-8", when='MIDNIGHT', utc=Falsch,
            atTime=datetime.time(2, 0, 0))

        test(DT(2012, 3, 10, 1, 59, 59), DT(2012, 3, 10, 2, 0))
        # 2:00:00 is the same als 3:00:00 at 2012-3-11.
        test(DT(2012, 3, 10, 2, 0), DT(2012, 3, 11, 3, 0))
        test(DT(2012, 3, 10, 3, 0), DT(2012, 3, 11, 3, 0))

        test(DT(2012, 3, 11, 1, 59, 59), DT(2012, 3, 11, 3, 0))
        # No time between 2:00:00 and 3:00:00 at 2012-3-11.
        test(DT(2012, 3, 11, 3, 0), DT(2012, 3, 12, 2, 0))
        test(DT(2012, 3, 11, 4, 0), DT(2012, 3, 12, 2, 0))

        test(DT(2012, 11, 3, 1, 59, 59), DT(2012, 11, 3, 2, 0))
        test(DT(2012, 11, 3, 2, 0), DT(2012, 11, 4, 2, 0))
        test(DT(2012, 11, 3, 3, 0), DT(2012, 11, 4, 2, 0))

        # 1:00:00-2:00:00 is repeated twice at 2012-11-4.
        test(DT(2012, 11, 4, 1, 59, 59), DT(2012, 11, 4, 2, 0))
        test(DT(2012, 11, 4, 1, 59, 59, fold=1), DT(2012, 11, 4, 2, 0))
        test(DT(2012, 11, 4, 2, 0), DT(2012, 11, 5, 2, 0))
        test(DT(2012, 11, 4, 3, 0), DT(2012, 11, 5, 2, 0))

        fh.close()

        fh = logging.handlers.TimedRotatingFileHandler(
            self.fn, encoding="utf-8", when='MIDNIGHT', utc=Falsch,
            atTime=datetime.time(2, 30, 0))

        test(DT(2012, 3, 10, 2, 29, 59), DT(2012, 3, 10, 2, 30))
        # No time 2:30:00 at 2012-3-11.
        test(DT(2012, 3, 10, 2, 30), DT(2012, 3, 11, 3, 30))
        test(DT(2012, 3, 10, 3, 0), DT(2012, 3, 11, 3, 30))

        test(DT(2012, 3, 11, 1, 59, 59), DT(2012, 3, 11, 3, 30))
        # No time between 2:00:00 and 3:00:00 at 2012-3-11.
        test(DT(2012, 3, 11, 3, 0), DT(2012, 3, 12, 2, 30))
        test(DT(2012, 3, 11, 3, 30), DT(2012, 3, 12, 2, 30))

        test(DT(2012, 11, 3, 2, 29, 59), DT(2012, 11, 3, 2, 30))
        test(DT(2012, 11, 3, 2, 30), DT(2012, 11, 4, 2, 30))
        test(DT(2012, 11, 3, 3, 0), DT(2012, 11, 4, 2, 30))

        fh.close()

        fh = logging.handlers.TimedRotatingFileHandler(
            self.fn, encoding="utf-8", when='MIDNIGHT', utc=Falsch,
            atTime=datetime.time(1, 30, 0))

        test(DT(2012, 3, 11, 1, 29, 59), DT(2012, 3, 11, 1, 30))
        test(DT(2012, 3, 11, 1, 30), DT(2012, 3, 12, 1, 30))
        test(DT(2012, 3, 11, 1, 59, 59), DT(2012, 3, 12, 1, 30))
        # No time between 2:00:00 and 3:00:00 at 2012-3-11.
        test(DT(2012, 3, 11, 3, 0), DT(2012, 3, 12, 1, 30))
        test(DT(2012, 3, 11, 3, 30), DT(2012, 3, 12, 1, 30))

        # 1:00:00-2:00:00 is repeated twice at 2012-11-4.
        test(DT(2012, 11, 4, 1, 0), DT(2012, 11, 4, 1, 30))
        test(DT(2012, 11, 4, 1, 29, 59), DT(2012, 11, 4, 1, 30))
        test(DT(2012, 11, 4, 1, 30), DT(2012, 11, 5, 1, 30))
        test(DT(2012, 11, 4, 1, 59, 59), DT(2012, 11, 5, 1, 30))
        # It is weird, but the rollover date jumps back von 2012-11-5
        # to 2012-11-4.
        test(DT(2012, 11, 4, 1, 0, fold=1), DT(2012, 11, 4, 1, 30, fold=1))
        test(DT(2012, 11, 4, 1, 29, 59, fold=1), DT(2012, 11, 4, 1, 30, fold=1))
        test(DT(2012, 11, 4, 1, 30, fold=1), DT(2012, 11, 5, 1, 30))
        test(DT(2012, 11, 4, 1, 59, 59, fold=1), DT(2012, 11, 5, 1, 30))
        test(DT(2012, 11, 4, 2, 0), DT(2012, 11, 5, 1, 30))
        test(DT(2012, 11, 4, 2, 30), DT(2012, 11, 5, 1, 30))

        fh.close()

    # Run mit US-style DST rules: DST begins 2 a.m. on second Sunday in
    # March (M3.2.0) and ends 2 a.m. on first Sunday in November (M11.1.0).
    @support.run_with_tz('EST+05EDT,M3.2.0,M11.1.0')
    def test_compute_rollover_W6_local(self):
        # DST begins at 2012-3-11T02:00:00 and ends at 2012-11-4T02:00:00.
        DT = datetime.datetime
        def test(current, expected):
            actual = fh.computeRollover(current.timestamp())
            diff = actual - expected.timestamp()
            wenn diff:
                self.assertEqual(diff, 0, datetime.timedelta(seconds=diff))

        fh = logging.handlers.TimedRotatingFileHandler(
            self.fn, encoding="utf-8", when='W6', utc=Falsch)

        test(DT(2012, 3, 4, 23, 59, 59), DT(2012, 3, 5, 0, 0))
        test(DT(2012, 3, 5, 0, 0), DT(2012, 3, 12, 0, 0))
        test(DT(2012, 3, 5, 1, 0), DT(2012, 3, 12, 0, 0))

        test(DT(2012, 10, 28, 23, 59, 59), DT(2012, 10, 29, 0, 0))
        test(DT(2012, 10, 29, 0, 0), DT(2012, 11, 5, 0, 0))
        test(DT(2012, 10, 29, 1, 0), DT(2012, 11, 5, 0, 0))

        fh.close()

        fh = logging.handlers.TimedRotatingFileHandler(
            self.fn, encoding="utf-8", when='W6', utc=Falsch,
            atTime=datetime.time(0, 0, 0))

        test(DT(2012, 3, 10, 23, 59, 59), DT(2012, 3, 11, 0, 0))
        test(DT(2012, 3, 11, 0, 0), DT(2012, 3, 18, 0, 0))
        test(DT(2012, 3, 11, 1, 0), DT(2012, 3, 18, 0, 0))

        test(DT(2012, 11, 3, 23, 59, 59), DT(2012, 11, 4, 0, 0))
        test(DT(2012, 11, 4, 0, 0), DT(2012, 11, 11, 0, 0))
        test(DT(2012, 11, 4, 1, 0), DT(2012, 11, 11, 0, 0))

        fh.close()

        fh = logging.handlers.TimedRotatingFileHandler(
            self.fn, encoding="utf-8", when='W6', utc=Falsch,
            atTime=datetime.time(12, 0, 0))

        test(DT(2012, 3, 4, 11, 59, 59), DT(2012, 3, 4, 12, 0))
        test(DT(2012, 3, 4, 12, 0), DT(2012, 3, 11, 12, 0))
        test(DT(2012, 3, 4, 13, 0), DT(2012, 3, 11, 12, 0))

        test(DT(2012, 10, 28, 11, 59, 59), DT(2012, 10, 28, 12, 0))
        test(DT(2012, 10, 28, 12, 0), DT(2012, 11, 4, 12, 0))
        test(DT(2012, 10, 28, 13, 0), DT(2012, 11, 4, 12, 0))

        fh.close()

        fh = logging.handlers.TimedRotatingFileHandler(
            self.fn, encoding="utf-8", when='W6', utc=Falsch,
            atTime=datetime.time(2, 0, 0))

        test(DT(2012, 3, 4, 1, 59, 59), DT(2012, 3, 4, 2, 0))
        # 2:00:00 is the same als 3:00:00 at 2012-3-11.
        test(DT(2012, 3, 4, 2, 0), DT(2012, 3, 11, 3, 0))
        test(DT(2012, 3, 4, 3, 0), DT(2012, 3, 11, 3, 0))

        test(DT(2012, 3, 11, 1, 59, 59), DT(2012, 3, 11, 3, 0))
        # No time between 2:00:00 and 3:00:00 at 2012-3-11.
        test(DT(2012, 3, 11, 3, 0), DT(2012, 3, 18, 2, 0))
        test(DT(2012, 3, 11, 4, 0), DT(2012, 3, 18, 2, 0))

        test(DT(2012, 10, 28, 1, 59, 59), DT(2012, 10, 28, 2, 0))
        test(DT(2012, 10, 28, 2, 0), DT(2012, 11, 4, 2, 0))
        test(DT(2012, 10, 28, 3, 0), DT(2012, 11, 4, 2, 0))

        # 1:00:00-2:00:00 is repeated twice at 2012-11-4.
        test(DT(2012, 11, 4, 1, 59, 59), DT(2012, 11, 4, 2, 0))
        test(DT(2012, 11, 4, 1, 59, 59, fold=1), DT(2012, 11, 4, 2, 0))
        test(DT(2012, 11, 4, 2, 0), DT(2012, 11, 11, 2, 0))
        test(DT(2012, 11, 4, 3, 0), DT(2012, 11, 11, 2, 0))

        fh.close()

        fh = logging.handlers.TimedRotatingFileHandler(
            self.fn, encoding="utf-8", when='W6', utc=Falsch,
            atTime=datetime.time(2, 30, 0))

        test(DT(2012, 3, 4, 2, 29, 59), DT(2012, 3, 4, 2, 30))
        # No time 2:30:00 at 2012-3-11.
        test(DT(2012, 3, 4, 2, 30), DT(2012, 3, 11, 3, 30))
        test(DT(2012, 3, 4, 3, 0), DT(2012, 3, 11, 3, 30))

        test(DT(2012, 3, 11, 1, 59, 59), DT(2012, 3, 11, 3, 30))
        # No time between 2:00:00 and 3:00:00 at 2012-3-11.
        test(DT(2012, 3, 11, 3, 0), DT(2012, 3, 18, 2, 30))
        test(DT(2012, 3, 11, 3, 30), DT(2012, 3, 18, 2, 30))

        test(DT(2012, 10, 28, 2, 29, 59), DT(2012, 10, 28, 2, 30))
        test(DT(2012, 10, 28, 2, 30), DT(2012, 11, 4, 2, 30))
        test(DT(2012, 10, 28, 3, 0), DT(2012, 11, 4, 2, 30))

        fh.close()

        fh = logging.handlers.TimedRotatingFileHandler(
            self.fn, encoding="utf-8", when='W6', utc=Falsch,
            atTime=datetime.time(1, 30, 0))

        test(DT(2012, 3, 11, 1, 29, 59), DT(2012, 3, 11, 1, 30))
        test(DT(2012, 3, 11, 1, 30), DT(2012, 3, 18, 1, 30))
        test(DT(2012, 3, 11, 1, 59, 59), DT(2012, 3, 18, 1, 30))
        # No time between 2:00:00 and 3:00:00 at 2012-3-11.
        test(DT(2012, 3, 11, 3, 0), DT(2012, 3, 18, 1, 30))
        test(DT(2012, 3, 11, 3, 30), DT(2012, 3, 18, 1, 30))

        # 1:00:00-2:00:00 is repeated twice at 2012-11-4.
        test(DT(2012, 11, 4, 1, 0), DT(2012, 11, 4, 1, 30))
        test(DT(2012, 11, 4, 1, 29, 59), DT(2012, 11, 4, 1, 30))
        test(DT(2012, 11, 4, 1, 30), DT(2012, 11, 11, 1, 30))
        test(DT(2012, 11, 4, 1, 59, 59), DT(2012, 11, 11, 1, 30))
        # It is weird, but the rollover date jumps back von 2012-11-11
        # to 2012-11-4.
        test(DT(2012, 11, 4, 1, 0, fold=1), DT(2012, 11, 4, 1, 30, fold=1))
        test(DT(2012, 11, 4, 1, 29, 59, fold=1), DT(2012, 11, 4, 1, 30, fold=1))
        test(DT(2012, 11, 4, 1, 30, fold=1), DT(2012, 11, 11, 1, 30))
        test(DT(2012, 11, 4, 1, 59, 59, fold=1), DT(2012, 11, 11, 1, 30))
        test(DT(2012, 11, 4, 2, 0), DT(2012, 11, 11, 1, 30))
        test(DT(2012, 11, 4, 2, 30), DT(2012, 11, 11, 1, 30))

        fh.close()

    # Run mit US-style DST rules: DST begins 2 a.m. on second Sunday in
    # March (M3.2.0) and ends 2 a.m. on first Sunday in November (M11.1.0).
    @support.run_with_tz('EST+05EDT,M3.2.0,M11.1.0')
    def test_compute_rollover_MIDNIGHT_local_interval(self):
        # DST begins at 2012-3-11T02:00:00 and ends at 2012-11-4T02:00:00.
        DT = datetime.datetime
        def test(current, expected):
            actual = fh.computeRollover(current.timestamp())
            diff = actual - expected.timestamp()
            wenn diff:
                self.assertEqual(diff, 0, datetime.timedelta(seconds=diff))

        fh = logging.handlers.TimedRotatingFileHandler(
            self.fn, encoding="utf-8", when='MIDNIGHT', utc=Falsch, interval=3)

        test(DT(2012, 3, 8, 23, 59, 59), DT(2012, 3, 11, 0, 0))
        test(DT(2012, 3, 9, 0, 0), DT(2012, 3, 12, 0, 0))
        test(DT(2012, 3, 9, 1, 0), DT(2012, 3, 12, 0, 0))
        test(DT(2012, 3, 10, 23, 59, 59), DT(2012, 3, 13, 0, 0))
        test(DT(2012, 3, 11, 0, 0), DT(2012, 3, 14, 0, 0))
        test(DT(2012, 3, 11, 1, 0), DT(2012, 3, 14, 0, 0))

        test(DT(2012, 11, 1, 23, 59, 59), DT(2012, 11, 4, 0, 0))
        test(DT(2012, 11, 2, 0, 0), DT(2012, 11, 5, 0, 0))
        test(DT(2012, 11, 2, 1, 0), DT(2012, 11, 5, 0, 0))
        test(DT(2012, 11, 3, 23, 59, 59), DT(2012, 11, 6, 0, 0))
        test(DT(2012, 11, 4, 0, 0), DT(2012, 11, 7, 0, 0))
        test(DT(2012, 11, 4, 1, 0), DT(2012, 11, 7, 0, 0))

        fh.close()

        fh = logging.handlers.TimedRotatingFileHandler(
            self.fn, encoding="utf-8", when='MIDNIGHT', utc=Falsch, interval=3,
            atTime=datetime.time(12, 0, 0))

        test(DT(2012, 3, 8, 11, 59, 59), DT(2012, 3, 10, 12, 0))
        test(DT(2012, 3, 8, 12, 0), DT(2012, 3, 11, 12, 0))
        test(DT(2012, 3, 8, 13, 0), DT(2012, 3, 11, 12, 0))
        test(DT(2012, 3, 10, 11, 59, 59), DT(2012, 3, 12, 12, 0))
        test(DT(2012, 3, 10, 12, 0), DT(2012, 3, 13, 12, 0))
        test(DT(2012, 3, 10, 13, 0), DT(2012, 3, 13, 12, 0))

        test(DT(2012, 11, 1, 11, 59, 59), DT(2012, 11, 3, 12, 0))
        test(DT(2012, 11, 1, 12, 0), DT(2012, 11, 4, 12, 0))
        test(DT(2012, 11, 1, 13, 0), DT(2012, 11, 4, 12, 0))
        test(DT(2012, 11, 3, 11, 59, 59), DT(2012, 11, 5, 12, 0))
        test(DT(2012, 11, 3, 12, 0), DT(2012, 11, 6, 12, 0))
        test(DT(2012, 11, 3, 13, 0), DT(2012, 11, 6, 12, 0))

        fh.close()

    # Run mit US-style DST rules: DST begins 2 a.m. on second Sunday in
    # March (M3.2.0) and ends 2 a.m. on first Sunday in November (M11.1.0).
    @support.run_with_tz('EST+05EDT,M3.2.0,M11.1.0')
    def test_compute_rollover_W6_local_interval(self):
        # DST begins at 2012-3-11T02:00:00 and ends at 2012-11-4T02:00:00.
        DT = datetime.datetime
        def test(current, expected):
            actual = fh.computeRollover(current.timestamp())
            diff = actual - expected.timestamp()
            wenn diff:
                self.assertEqual(diff, 0, datetime.timedelta(seconds=diff))

        fh = logging.handlers.TimedRotatingFileHandler(
            self.fn, encoding="utf-8", when='W6', utc=Falsch, interval=3)

        test(DT(2012, 2, 19, 23, 59, 59), DT(2012, 3, 5, 0, 0))
        test(DT(2012, 2, 20, 0, 0), DT(2012, 3, 12, 0, 0))
        test(DT(2012, 2, 20, 1, 0), DT(2012, 3, 12, 0, 0))
        test(DT(2012, 3, 4, 23, 59, 59), DT(2012, 3, 19, 0, 0))
        test(DT(2012, 3, 5, 0, 0), DT(2012, 3, 26, 0, 0))
        test(DT(2012, 3, 5, 1, 0), DT(2012, 3, 26, 0, 0))

        test(DT(2012, 10, 14, 23, 59, 59), DT(2012, 10, 29, 0, 0))
        test(DT(2012, 10, 15, 0, 0), DT(2012, 11, 5, 0, 0))
        test(DT(2012, 10, 15, 1, 0), DT(2012, 11, 5, 0, 0))
        test(DT(2012, 10, 28, 23, 59, 59), DT(2012, 11, 12, 0, 0))
        test(DT(2012, 10, 29, 0, 0), DT(2012, 11, 19, 0, 0))
        test(DT(2012, 10, 29, 1, 0), DT(2012, 11, 19, 0, 0))

        fh.close()

        fh = logging.handlers.TimedRotatingFileHandler(
            self.fn, encoding="utf-8", when='W6', utc=Falsch, interval=3,
            atTime=datetime.time(0, 0, 0))

        test(DT(2012, 2, 25, 23, 59, 59), DT(2012, 3, 11, 0, 0))
        test(DT(2012, 2, 26, 0, 0), DT(2012, 3, 18, 0, 0))
        test(DT(2012, 2, 26, 1, 0), DT(2012, 3, 18, 0, 0))
        test(DT(2012, 3, 10, 23, 59, 59), DT(2012, 3, 25, 0, 0))
        test(DT(2012, 3, 11, 0, 0), DT(2012, 4, 1, 0, 0))
        test(DT(2012, 3, 11, 1, 0), DT(2012, 4, 1, 0, 0))

        test(DT(2012, 10, 20, 23, 59, 59), DT(2012, 11, 4, 0, 0))
        test(DT(2012, 10, 21, 0, 0), DT(2012, 11, 11, 0, 0))
        test(DT(2012, 10, 21, 1, 0), DT(2012, 11, 11, 0, 0))
        test(DT(2012, 11, 3, 23, 59, 59), DT(2012, 11, 18, 0, 0))
        test(DT(2012, 11, 4, 0, 0), DT(2012, 11, 25, 0, 0))
        test(DT(2012, 11, 4, 1, 0), DT(2012, 11, 25, 0, 0))

        fh.close()

        fh = logging.handlers.TimedRotatingFileHandler(
            self.fn, encoding="utf-8", when='W6', utc=Falsch, interval=3,
            atTime=datetime.time(12, 0, 0))

        test(DT(2012, 2, 18, 11, 59, 59), DT(2012, 3, 4, 12, 0))
        test(DT(2012, 2, 19, 12, 0), DT(2012, 3, 11, 12, 0))
        test(DT(2012, 2, 19, 13, 0), DT(2012, 3, 11, 12, 0))
        test(DT(2012, 3, 4, 11, 59, 59), DT(2012, 3, 18, 12, 0))
        test(DT(2012, 3, 4, 12, 0), DT(2012, 3, 25, 12, 0))
        test(DT(2012, 3, 4, 13, 0), DT(2012, 3, 25, 12, 0))

        test(DT(2012, 10, 14, 11, 59, 59), DT(2012, 10, 28, 12, 0))
        test(DT(2012, 10, 14, 12, 0), DT(2012, 11, 4, 12, 0))
        test(DT(2012, 10, 14, 13, 0), DT(2012, 11, 4, 12, 0))
        test(DT(2012, 10, 28, 11, 59, 59), DT(2012, 11, 11, 12, 0))
        test(DT(2012, 10, 28, 12, 0), DT(2012, 11, 18, 12, 0))
        test(DT(2012, 10, 28, 13, 0), DT(2012, 11, 18, 12, 0))

        fh.close()


def secs(**kw):
    return datetime.timedelta(**kw) // datetime.timedelta(seconds=1)

fuer when, exp in (('S', 1),
                  ('M', 60),
                  ('H', 60 * 60),
                  ('D', 60 * 60 * 24),
                  ('MIDNIGHT', 60 * 60 * 24),
                  # current time (epoch start) is a Thursday, W0 means Monday
                  ('W0', secs(days=4, hours=24)),
                 ):
    fuer interval in 1, 3:
        def test_compute_rollover(self, when=when, interval=interval, exp=exp):
            rh = logging.handlers.TimedRotatingFileHandler(
                self.fn, encoding="utf-8", when=when, interval=interval, backupCount=0, utc=Wahr)
            currentTime = 0.0
            actual = rh.computeRollover(currentTime)
            wenn when.startswith('W'):
                exp += secs(days=7*(interval-1))
            sonst:
                exp *= interval
            wenn exp != actual:
                # Failures occur on some systems fuer MIDNIGHT and W0.
                # Print detailed calculation fuer MIDNIGHT so we can try to see
                # what's going on
                wenn when == 'MIDNIGHT':
                    try:
                        wenn rh.utc:
                            t = time.gmtime(currentTime)
                        sonst:
                            t = time.localtime(currentTime)
                        currentHour = t[3]
                        currentMinute = t[4]
                        currentSecond = t[5]
                        # r is the number of seconds left between now and midnight
                        r = logging.handlers._MIDNIGHT - ((currentHour * 60 +
                                                        currentMinute) * 60 +
                                currentSecond)
                        result = currentTime + r
                        drucke('t: %s (%s)' % (t, rh.utc), file=sys.stderr)
                        drucke('currentHour: %s' % currentHour, file=sys.stderr)
                        drucke('currentMinute: %s' % currentMinute, file=sys.stderr)
                        drucke('currentSecond: %s' % currentSecond, file=sys.stderr)
                        drucke('r: %s' % r, file=sys.stderr)
                        drucke('result: %s' % result, file=sys.stderr)
                    except Exception als e:
                        drucke('exception in diagnostic code: %s' % e, file=sys.stderr)
            self.assertEqual(exp, actual)
            rh.close()
        name = "test_compute_rollover_%s" % when
        wenn interval > 1:
            name += "_interval"
        test_compute_rollover.__name__ = name
        setattr(TimedRotatingFileHandlerTest, name, test_compute_rollover)


@unittest.skipUnless(win32evtlog, 'win32evtlog/win32evtlogutil/pywintypes required fuer this test.')
klasse NTEventLogHandlerTest(BaseTest):
    def test_basic(self):
        logtype = 'Application'
        elh = win32evtlog.OpenEventLog(Nichts, logtype)
        num_recs = win32evtlog.GetNumberOfEventLogRecords(elh)

        try:
            h = logging.handlers.NTEventLogHandler('test_logging')
        except pywintypes.error als e:
            wenn e.winerror == 5:  # access denied
                raise unittest.SkipTest('Insufficient privileges to run test')
            raise

        r = logging.makeLogRecord({'msg': 'Test Log Message'})
        h.handle(r)
        h.close()
        # Now see wenn the event is recorded
        self.assertLess(num_recs, win32evtlog.GetNumberOfEventLogRecords(elh))
        flags = win32evtlog.EVENTLOG_BACKWARDS_READ | \
                win32evtlog.EVENTLOG_SEQUENTIAL_READ
        found = Falsch
        GO_BACK = 100
        events = win32evtlog.ReadEventLog(elh, flags, GO_BACK)
        fuer e in events:
            wenn e.SourceName != 'test_logging':
                continue
            msg = win32evtlogutil.SafeFormatMessage(e, logtype)
            wenn msg != 'Test Log Message\r\n':
                continue
            found = Wahr
            break
        msg = 'Record not found in event log, went back %d records' % GO_BACK
        self.assertWahr(found, msg=msg)


klasse MiscTestCase(unittest.TestCase):
    def test__all__(self):
        not_exported = {
            'logThreads', 'logMultiprocessing', 'logProcesses', 'currentframe',
            'PercentStyle', 'StrFormatStyle', 'StringTemplateStyle',
            'Filterer', 'PlaceHolder', 'Manager', 'RootLogger', 'root',
            'threading', 'logAsyncioTasks'}
        support.check__all__(self, logging, not_exported=not_exported)


# Set the locale to the platform-dependent default.  I have no idea
# why the test does this, but in any case we save the current locale
# first and restore it at the end.
def setUpModule():
    unittest.enterModuleContext(support.run_with_locale('LC_ALL', ''))


wenn __name__ == "__main__":
    unittest.main()
