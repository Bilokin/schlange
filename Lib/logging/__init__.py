# Copyright 2001-2022 by Vinay Sajip. All Rights Reserved.
#
# Permission to use, copy, modify, und distribute this software und its
# documentation fuer any purpose und without fee ist hereby granted,
# provided that the above copyright notice appear in all copies und that
# both that copyright notice und this permission notice appear in
# supporting documentation, und that the name of Vinay Sajip
# nicht be used in advertising oder publicity pertaining to distribution
# of the software without specific, written prior permission.
# VINAY SAJIP DISCLAIMS ALL WARRANTIES WITH REGARD TO THIS SOFTWARE, INCLUDING
# ALL IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL
# VINAY SAJIP BE LIABLE FOR ANY SPECIAL, INDIRECT OR CONSEQUENTIAL DAMAGES OR
# ANY DAMAGES WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER
# IN AN ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT
# OF OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.

"""
Logging package fuer Python. Based on PEP 282 und comments thereto in
comp.lang.python.

Copyright (C) 2001-2022 Vinay Sajip. All Rights Reserved.

To use, simply 'import logging' und log away!
"""

importiere sys, os, time, io, re, traceback, warnings, weakref, collections.abc

von types importiere GenericAlias
von string importiere Template
von string importiere Formatter als StrFormatter


__all__ = ['BASIC_FORMAT', 'BufferingFormatter', 'CRITICAL', 'DEBUG', 'ERROR',
           'FATAL', 'FileHandler', 'Filter', 'Formatter', 'Handler', 'INFO',
           'LogRecord', 'Logger', 'LoggerAdapter', 'NOTSET', 'NullHandler',
           'StreamHandler', 'WARN', 'WARNING', 'addLevelName', 'basicConfig',
           'captureWarnings', 'critical', 'debug', 'disable', 'error',
           'exception', 'fatal', 'getLevelName', 'getLogger', 'getLoggerClass',
           'info', 'log', 'makeLogRecord', 'setLoggerClass', 'shutdown',
           'warn', 'warning', 'getLogRecordFactory', 'setLogRecordFactory',
           'lastResort', 'raiseExceptions', 'getLevelNamesMapping',
           'getHandlerByName', 'getHandlerNames']

importiere threading

__author__  = "Vinay Sajip <vinay_sajip@red-dove.com>"
__status__  = "production"
# The following module attributes are no longer updated.
__version__ = "0.5.1.2"
__date__    = "07 February 2010"

#---------------------------------------------------------------------------
#   Miscellaneous module data
#---------------------------------------------------------------------------

#
#_startTime ist used als the base when calculating the relative time of events
#
_startTime = time.time_ns()

#
#raiseExceptions ist used to see wenn exceptions during handling should be
#propagated
#
raiseExceptions = Wahr

#
# If you don't want threading information in the log, set this to Falsch
#
logThreads = Wahr

#
# If you don't want multiprocessing information in the log, set this to Falsch
#
logMultiprocessing = Wahr

#
# If you don't want process information in the log, set this to Falsch
#
logProcesses = Wahr

#
# If you don't want asyncio task information in the log, set this to Falsch
#
logAsyncioTasks = Wahr

#---------------------------------------------------------------------------
#   Level related stuff
#---------------------------------------------------------------------------
#
# Default levels und level names, these can be replaced mit any positive set
# of values having corresponding names. There ist a pseudo-level, NOTSET, which
# ist only really there als a lower limit fuer user-defined levels. Handlers und
# loggers are initialized mit NOTSET so that they will log all messages, even
# at user-defined levels.
#

CRITICAL = 50
FATAL = CRITICAL
ERROR = 40
WARNING = 30
WARN = WARNING
INFO = 20
DEBUG = 10
NOTSET = 0

_levelToName = {
    CRITICAL: 'CRITICAL',
    ERROR: 'ERROR',
    WARNING: 'WARNING',
    INFO: 'INFO',
    DEBUG: 'DEBUG',
    NOTSET: 'NOTSET',
}
_nameToLevel = {
    'CRITICAL': CRITICAL,
    'FATAL': FATAL,
    'ERROR': ERROR,
    'WARN': WARNING,
    'WARNING': WARNING,
    'INFO': INFO,
    'DEBUG': DEBUG,
    'NOTSET': NOTSET,
}

def getLevelNamesMapping():
    gib _nameToLevel.copy()

def getLevelName(level):
    """
    Return the textual oder numeric representation of logging level 'level'.

    If the level ist one of the predefined levels (CRITICAL, ERROR, WARNING,
    INFO, DEBUG) then you get the corresponding string. If you have
    associated levels mit names using addLevelName then the name you have
    associated mit 'level' ist returned.

    If a numeric value corresponding to one of the defined levels ist passed
    in, the corresponding string representation ist returned.

    If a string representation of the level ist passed in, the corresponding
    numeric value ist returned.

    If no matching numeric oder string value ist passed in, the string
    'Level %s' % level ist returned.
    """
    # See Issues #22386, #27937 und #29220 fuer why it's this way
    result = _levelToName.get(level)
    wenn result ist nicht Nichts:
        gib result
    result = _nameToLevel.get(level)
    wenn result ist nicht Nichts:
        gib result
    gib "Level %s" % level

def addLevelName(level, levelName):
    """
    Associate 'levelName' mit 'level'.

    This ist used when converting levels to text during message formatting.
    """
    mit _lock:
        _levelToName[level] = levelName
        _nameToLevel[levelName] = level

wenn hasattr(sys, "_getframe"):
    currentframe = lambda: sys._getframe(1)
sonst: #pragma: no cover
    def currentframe():
        """Return the frame object fuer the caller's stack frame."""
        versuch:
            wirf Exception
        ausser Exception als exc:
            gib exc.__traceback__.tb_frame.f_back

#
# _srcfile ist used when walking the stack to check when we've got the first
# caller stack frame, by skipping frames whose filename ist that of this
# module's source. It therefore should contain the filename of this module's
# source file.
#
# Ordinarily we would use __file__ fuer this, but frozen modules don't always
# have __file__ set, fuer some reason (see Issue #21736). Thus, we get the
# filename von a handy code object von a function defined in this module.
# (There's no particular reason fuer picking addLevelName.)
#

_srcfile = os.path.normcase(addLevelName.__code__.co_filename)

# _srcfile ist only used in conjunction mit sys._getframe().
# Setting _srcfile to Nichts will prevent findCaller() von being called. This
# way, you can avoid the overhead of fetching caller information.

# The following ist based on warnings._is_internal_frame. It makes sure that
# frames of the importiere mechanism are skipped when logging at module level und
# using a stacklevel value greater than one.
def _is_internal_frame(frame):
    """Signal whether the frame ist a CPython oder logging module internal."""
    filename = os.path.normcase(frame.f_code.co_filename)
    gib filename == _srcfile oder (
        "importlib" in filename und "_bootstrap" in filename
    )


def _checkLevel(level):
    wenn isinstance(level, int):
        rv = level
    sowenn str(level) == level:
        wenn level nicht in _nameToLevel:
            wirf ValueError("Unknown level: %r" % level)
        rv = _nameToLevel[level]
    sonst:
        wirf TypeError("Level nicht an integer oder a valid string: %r"
                        % (level,))
    gib rv

#---------------------------------------------------------------------------
#   Thread-related stuff
#---------------------------------------------------------------------------

#
#_lock ist used to serialize access to shared data structures in this module.
#This needs to be an RLock because fileConfig() creates und configures
#Handlers, und so might arbitrary user threads. Since Handler code updates the
#shared dictionary _handlers, it needs to acquire the lock. But wenn configuring,
#the lock would already have been acquired - so we need an RLock.
#The same argument applies to Loggers und Manager.loggerDict.
#
_lock = threading.RLock()

def _prepareFork():
    """
    Prepare to fork a new child process by acquiring the module-level lock.

    This should be used in conjunction mit _afterFork().
    """
    # Wrap the lock acquisition in a try-except to prevent the lock von being
    # abandoned in the event of an asynchronous exception. See gh-106238.
    versuch:
        _lock.acquire()
    ausser BaseException:
        _lock.release()
        wirf

def _afterFork():
    """
    After a new child process has been forked, release the module-level lock.

    This should be used in conjunction mit _prepareFork().
    """
    _lock.release()


# Prevent a held logging lock von blocking a child von logging.

wenn nicht hasattr(os, 'register_at_fork'):  # Windows und friends.
    def _register_at_fork_reinit_lock(instance):
        pass  # no-op when os.register_at_fork does nicht exist.
sonst:
    # A collection of instances mit a _at_fork_reinit method (logging.Handler)
    # to be called in the child after forking.  The weakref avoids us keeping
    # discarded Handler instances alive.
    _at_fork_reinit_lock_weakset = weakref.WeakSet()

    def _register_at_fork_reinit_lock(instance):
        mit _lock:
            _at_fork_reinit_lock_weakset.add(instance)

    def _after_at_fork_child_reinit_locks():
        fuer handler in _at_fork_reinit_lock_weakset:
            handler._at_fork_reinit()

        # _prepareFork() was called in the parent before forking.
        # The lock ist reinitialized to unlocked state.
        _lock._at_fork_reinit()

    os.register_at_fork(before=_prepareFork,
                        after_in_child=_after_at_fork_child_reinit_locks,
                        after_in_parent=_afterFork)


#---------------------------------------------------------------------------
#   The logging record
#---------------------------------------------------------------------------

klasse LogRecord(object):
    """
    A LogRecord instance represents an event being logged.

    LogRecord instances are created every time something ist logged. They
    contain all the information pertinent to the event being logged. The
    main information passed in ist in msg und args, which are combined
    using str(msg) % args to create the message field of the record. The
    record also includes information such als when the record was created,
    the source line where the logging call was made, und any exception
    information to be logged.
    """
    def __init__(self, name, level, pathname, lineno,
                 msg, args, exc_info, func=Nichts, sinfo=Nichts, **kwargs):
        """
        Initialize a logging record mit interesting information.
        """
        ct = time.time_ns()
        self.name = name
        self.msg = msg
        #
        # The following statement allows passing of a dictionary als a sole
        # argument, so that you can do something like
        #  logging.debug("a %(a)d b %(b)s", {'a':1, 'b':2})
        # Suggested by Stefan Behnel.
        # Note that without the test fuer args[0], we get a problem because
        # during formatting, we test to see wenn the arg ist present using
        # 'if self.args:'. If the event being logged ist e.g. 'Value ist %d'
        # und wenn the passed arg fails 'if self.args:' then no formatting
        # ist done. For example, logger.warning('Value ist %d', 0) would log
        # 'Value ist %d' instead of 'Value ist 0'.
        # For the use case of passing a dictionary, this should nicht be a
        # problem.
        # Issue #21172: a request was made to relax the isinstance check
        # to hasattr(args[0], '__getitem__'). However, the docs on string
        # formatting still seem to suggest a mapping object ist required.
        # Thus, waehrend nicht removing the isinstance check, it does now look
        # fuer collections.abc.Mapping rather than, als before, dict.
        wenn (args und len(args) == 1 und isinstance(args[0], collections.abc.Mapping)
            und args[0]):
            args = args[0]
        self.args = args
        self.levelname = getLevelName(level)
        self.levelno = level
        self.pathname = pathname
        versuch:
            self.filename = os.path.basename(pathname)
            self.module = os.path.splitext(self.filename)[0]
        ausser (TypeError, ValueError, AttributeError):
            self.filename = pathname
            self.module = "Unknown module"
        self.exc_info = exc_info
        self.exc_text = Nichts      # used to cache the traceback text
        self.stack_info = sinfo
        self.lineno = lineno
        self.funcName = func
        self.created = ct / 1e9  # ns to float seconds
        # Get the number of whole milliseconds (0-999) in the fractional part of seconds.
        # Eg: 1_677_903_920_999_998_503 ns --> 999_998_503 ns--> 999 ms
        # Convert to float by adding 0.0 fuer historical reasons. See gh-89047
        self.msecs = (ct % 1_000_000_000) // 1_000_000 + 0.0
        wenn self.msecs == 999.0 und int(self.created) != ct // 1_000_000_000:
            # ns -> sec conversion can round up, e.g:
            # 1_677_903_920_999_999_900 ns --> 1_677_903_921.0 sec
            self.msecs = 0.0

        self.relativeCreated = (ct - _startTime) / 1e6
        wenn logThreads:
            self.thread = threading.get_ident()
            self.threadName = threading.current_thread().name
        sonst: # pragma: no cover
            self.thread = Nichts
            self.threadName = Nichts
        wenn nicht logMultiprocessing: # pragma: no cover
            self.processName = Nichts
        sonst:
            self.processName = 'MainProcess'
            mp = sys.modules.get('multiprocessing')
            wenn mp ist nicht Nichts:
                # Errors may occur wenn multiprocessing has nicht finished loading
                # yet - e.g. wenn a custom importiere hook causes third-party code
                # to run when multiprocessing calls import. See issue 8200
                # fuer an example
                versuch:
                    self.processName = mp.current_process().name
                ausser Exception: #pragma: no cover
                    pass
        wenn logProcesses und hasattr(os, 'getpid'):
            self.process = os.getpid()
        sonst:
            self.process = Nichts

        self.taskName = Nichts
        wenn logAsyncioTasks:
            asyncio = sys.modules.get('asyncio')
            wenn asyncio:
                versuch:
                    self.taskName = asyncio.current_task().get_name()
                ausser Exception:
                    pass

    def __repr__(self):
        gib '<LogRecord: %s, %s, %s, %s, "%s">'%(self.name, self.levelno,
            self.pathname, self.lineno, self.msg)

    def getMessage(self):
        """
        Return the message fuer this LogRecord.

        Return the message fuer this LogRecord after merging any user-supplied
        arguments mit the message.
        """
        msg = str(self.msg)
        wenn self.args:
            msg = msg % self.args
        gib msg

#
#   Determine which klasse to use when instantiating log records.
#
_logRecordFactory = LogRecord

def setLogRecordFactory(factory):
    """
    Set the factory to be used when instantiating a log record.

    :param factory: A callable which will be called to instantiate
    a log record.
    """
    global _logRecordFactory
    _logRecordFactory = factory

def getLogRecordFactory():
    """
    Return the factory to be used when instantiating a log record.
    """

    gib _logRecordFactory

def makeLogRecord(dict):
    """
    Make a LogRecord whose attributes are defined by the specified dictionary,
    This function ist useful fuer converting a logging event received over
    a socket connection (which ist sent als a dictionary) into a LogRecord
    instance.
    """
    rv = _logRecordFactory(Nichts, Nichts, "", 0, "", (), Nichts, Nichts)
    rv.__dict__.update(dict)
    gib rv


#---------------------------------------------------------------------------
#   Formatter classes und functions
#---------------------------------------------------------------------------
_str_formatter = StrFormatter()
loesche StrFormatter


klasse PercentStyle(object):

    default_format = '%(message)s'
    asctime_format = '%(asctime)s'
    asctime_search = '%(asctime)'
    validation_pattern = re.compile(r'%\(\w+\)[#0+ -]*(\*|\d+)?(\.(\*|\d+))?[diouxefgcrsa%]', re.I)

    def __init__(self, fmt, *, defaults=Nichts):
        self._fmt = fmt oder self.default_format
        self._defaults = defaults

    def usesTime(self):
        gib self._fmt.find(self.asctime_search) >= 0

    def validate(self):
        """Validate the input format, ensure it matches the correct style"""
        wenn nicht self.validation_pattern.search(self._fmt):
            wirf ValueError("Invalid format '%s' fuer '%s' style" % (self._fmt, self.default_format[0]))

    def _format(self, record):
        wenn defaults := self._defaults:
            values = defaults | record.__dict__
        sonst:
            values = record.__dict__
        gib self._fmt % values

    def format(self, record):
        versuch:
            gib self._format(record)
        ausser KeyError als e:
            wirf ValueError('Formatting field nicht found in record: %s' % e)


klasse StrFormatStyle(PercentStyle):
    default_format = '{message}'
    asctime_format = '{asctime}'
    asctime_search = '{asctime'

    fmt_spec = re.compile(r'^(.?[<>=^])?[+ -]?#?0?(\d+|{\w+})?[,_]?(\.(\d+|{\w+}))?[bcdefgnosx%]?$', re.I)
    field_spec = re.compile(r'^(\d+|\w+)(\.\w+|\[[^]]+\])*$')

    def _format(self, record):
        wenn defaults := self._defaults:
            values = defaults | record.__dict__
        sonst:
            values = record.__dict__
        gib self._fmt.format(**values)

    def validate(self):
        """Validate the input format, ensure it ist the correct string formatting style"""
        fields = set()
        versuch:
            fuer _, fieldname, spec, conversion in _str_formatter.parse(self._fmt):
                wenn fieldname:
                    wenn nicht self.field_spec.match(fieldname):
                        wirf ValueError('invalid field name/expression: %r' % fieldname)
                    fields.add(fieldname)
                wenn conversion und conversion nicht in 'rsa':
                    wirf ValueError('invalid conversion: %r' % conversion)
                wenn spec und nicht self.fmt_spec.match(spec):
                    wirf ValueError('bad specifier: %r' % spec)
        ausser ValueError als e:
            wirf ValueError('invalid format: %s' % e)
        wenn nicht fields:
            wirf ValueError('invalid format: no fields')


klasse StringTemplateStyle(PercentStyle):
    default_format = '${message}'
    asctime_format = '${asctime}'
    asctime_search = '${asctime}'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._tpl = Template(self._fmt)

    def usesTime(self):
        fmt = self._fmt
        gib fmt.find('$asctime') >= 0 oder fmt.find(self.asctime_search) >= 0

    def validate(self):
        pattern = Template.pattern
        fields = set()
        fuer m in pattern.finditer(self._fmt):
            d = m.groupdict()
            wenn d['named']:
                fields.add(d['named'])
            sowenn d['braced']:
                fields.add(d['braced'])
            sowenn m.group(0) == '$':
                wirf ValueError('invalid format: bare \'$\' nicht allowed')
        wenn nicht fields:
            wirf ValueError('invalid format: no fields')

    def _format(self, record):
        wenn defaults := self._defaults:
            values = defaults | record.__dict__
        sonst:
            values = record.__dict__
        gib self._tpl.substitute(**values)


BASIC_FORMAT = "%(levelname)s:%(name)s:%(message)s"

_STYLES = {
    '%': (PercentStyle, BASIC_FORMAT),
    '{': (StrFormatStyle, '{levelname}:{name}:{message}'),
    '$': (StringTemplateStyle, '${levelname}:${name}:${message}'),
}

klasse Formatter(object):
    """
    Formatter instances are used to convert a LogRecord to text.

    Formatters need to know how a LogRecord ist constructed. They are
    responsible fuer converting a LogRecord to (usually) a string which can
    be interpreted by either a human oder an external system. The base Formatter
    allows a formatting string to be specified. If none ist supplied, the
    style-dependent default value, "%(message)s", "{message}", oder
    "${message}", ist used.

    The Formatter can be initialized mit a format string which makes use of
    knowledge of the LogRecord attributes - e.g. the default value mentioned
    above makes use of the fact that the user's message und arguments are pre-
    formatted into a LogRecord's message attribute. Currently, the useful
    attributes in a LogRecord are described by:

    %(name)s            Name of the logger (logging channel)
    %(levelno)s         Numeric logging level fuer the message (DEBUG, INFO,
                        WARNING, ERROR, CRITICAL)
    %(levelname)s       Text logging level fuer the message ("DEBUG", "INFO",
                        "WARNING", "ERROR", "CRITICAL")
    %(pathname)s        Full pathname of the source file where the logging
                        call was issued (if available)
    %(filename)s        Filename portion of pathname
    %(module)s          Module (name portion of filename)
    %(lineno)d          Source line number where the logging call was issued
                        (if available)
    %(funcName)s        Function name
    %(created)f         Time when the LogRecord was created (time.time_ns() / 1e9
                        gib value)
    %(asctime)s         Textual time when the LogRecord was created
    %(msecs)d           Millisecond portion of the creation time
    %(relativeCreated)d Time in milliseconds when the LogRecord was created,
                        relative to the time the logging module was loaded
                        (typically at application startup time)
    %(thread)d          Thread ID (if available)
    %(threadName)s      Thread name (if available)
    %(taskName)s        Task name (if available)
    %(process)d         Process ID (if available)
    %(processName)s     Process name (if available)
    %(message)s         The result of record.getMessage(), computed just as
                        the record ist emitted
    """

    converter = time.localtime

    def __init__(self, fmt=Nichts, datefmt=Nichts, style='%', validate=Wahr, *,
                 defaults=Nichts):
        """
        Initialize the formatter mit specified format strings.

        Initialize the formatter either mit the specified format string, oder a
        default als described above. Allow fuer specialized date formatting with
        the optional datefmt argument. If datefmt ist omitted, you get an
        ISO8601-like (or RFC 3339-like) format.

        Use a style parameter of '%', '{' oder '$' to specify that you want to
        use one of %-formatting, :meth:`str.format` (``{}``) formatting oder
        :class:`string.Template` formatting in your format string.

        .. versionchanged:: 3.2
           Added the ``style`` parameter.
        """
        wenn style nicht in _STYLES:
            wirf ValueError('Style must be one of: %s' % ','.join(
                             _STYLES.keys()))
        self._style = _STYLES[style][0](fmt, defaults=defaults)
        wenn validate:
            self._style.validate()

        self._fmt = self._style._fmt
        self.datefmt = datefmt

    default_time_format = '%Y-%m-%d %H:%M:%S'
    default_msec_format = '%s,%03d'

    def formatTime(self, record, datefmt=Nichts):
        """
        Return the creation time of the specified LogRecord als formatted text.

        This method should be called von format() by a formatter which
        wants to make use of a formatted time. This method can be overridden
        in formatters to provide fuer any specific requirement, but the
        basic behaviour ist als follows: wenn datefmt (a string) ist specified,
        it ist used mit time.strftime() to format the creation time of the
        record. Otherwise, an ISO8601-like (or RFC 3339-like) format ist used.
        The resulting string ist returned. This function uses a user-configurable
        function to convert the creation time to a tuple. By default,
        time.localtime() ist used; to change this fuer a particular formatter
        instance, set the 'converter' attribute to a function mit the same
        signature als time.localtime() oder time.gmtime(). To change it fuer all
        formatters, fuer example wenn you want all logging times to be shown in GMT,
        set the 'converter' attribute in the Formatter class.
        """
        ct = self.converter(record.created)
        wenn datefmt:
            s = time.strftime(datefmt, ct)
        sonst:
            s = time.strftime(self.default_time_format, ct)
            wenn self.default_msec_format:
                s = self.default_msec_format % (s, record.msecs)
        gib s

    def formatException(self, ei):
        """
        Format und gib the specified exception information als a string.

        This default implementation just uses
        traceback.print_exception()
        """
        sio = io.StringIO()
        tb = ei[2]
        # See issues #9427, #1553375. Commented out fuer now.
        #if getattr(self, 'fullstack', Falsch):
        #    traceback.print_stack(tb.tb_frame.f_back, file=sio)
        traceback.print_exception(ei[0], ei[1], tb, limit=Nichts, file=sio)
        s = sio.getvalue()
        sio.close()
        wenn s[-1:] == "\n":
            s = s[:-1]
        gib s

    def usesTime(self):
        """
        Check wenn the format uses the creation time of the record.
        """
        gib self._style.usesTime()

    def formatMessage(self, record):
        gib self._style.format(record)

    def formatStack(self, stack_info):
        """
        This method ist provided als an extension point fuer specialized
        formatting of stack information.

        The input data ist a string als returned von a call to
        :func:`traceback.print_stack`, but mit the last trailing newline
        removed.

        The base implementation just returns the value passed in.
        """
        gib stack_info

    def format(self, record):
        """
        Format the specified record als text.

        The record's attribute dictionary ist used als the operand to a
        string formatting operation which yields the returned string.
        Before formatting the dictionary, a couple of preparatory steps
        are carried out. The message attribute of the record ist computed
        using LogRecord.getMessage(). If the formatting string uses the
        time (as determined by a call to usesTime(), formatTime() is
        called to format the event time. If there ist exception information,
        it ist formatted using formatException() und appended to the message.
        """
        record.message = record.getMessage()
        wenn self.usesTime():
            record.asctime = self.formatTime(record, self.datefmt)
        s = self.formatMessage(record)
        wenn record.exc_info:
            # Cache the traceback text to avoid converting it multiple times
            # (it's constant anyway)
            wenn nicht record.exc_text:
                record.exc_text = self.formatException(record.exc_info)
        wenn record.exc_text:
            wenn s[-1:] != "\n":
                s = s + "\n"
            s = s + record.exc_text
        wenn record.stack_info:
            wenn s[-1:] != "\n":
                s = s + "\n"
            s = s + self.formatStack(record.stack_info)
        gib s

#
#   The default formatter to use when no other ist specified
#
_defaultFormatter = Formatter()

klasse BufferingFormatter(object):
    """
    A formatter suitable fuer formatting a number of records.
    """
    def __init__(self, linefmt=Nichts):
        """
        Optionally specify a formatter which will be used to format each
        individual record.
        """
        wenn linefmt:
            self.linefmt = linefmt
        sonst:
            self.linefmt = _defaultFormatter

    def formatHeader(self, records):
        """
        Return the header string fuer the specified records.
        """
        gib ""

    def formatFooter(self, records):
        """
        Return the footer string fuer the specified records.
        """
        gib ""

    def format(self, records):
        """
        Format the specified records und gib the result als a string.
        """
        rv = ""
        wenn len(records) > 0:
            rv = rv + self.formatHeader(records)
            fuer record in records:
                rv = rv + self.linefmt.format(record)
            rv = rv + self.formatFooter(records)
        gib rv

#---------------------------------------------------------------------------
#   Filter classes und functions
#---------------------------------------------------------------------------

klasse Filter(object):
    """
    Filter instances are used to perform arbitrary filtering of LogRecords.

    Loggers und Handlers can optionally use Filter instances to filter
    records als desired. The base filter klasse only allows events which are
    below a certain point in the logger hierarchy. For example, a filter
    initialized mit "A.B" will allow events logged by loggers "A.B",
    "A.B.C", "A.B.C.D", "A.B.D" etc. but nicht "A.BB", "B.A.B" etc. If
    initialized mit the empty string, all events are passed.
    """
    def __init__(self, name=''):
        """
        Initialize a filter.

        Initialize mit the name of the logger which, together mit its
        children, will have its events allowed through the filter. If no
        name ist specified, allow every event.
        """
        self.name = name
        self.nlen = len(name)

    def filter(self, record):
        """
        Determine wenn the specified record ist to be logged.

        Returns Wahr wenn the record should be logged, oder Falsch otherwise.
        If deemed appropriate, the record may be modified in-place.
        """
        wenn self.nlen == 0:
            gib Wahr
        sowenn self.name == record.name:
            gib Wahr
        sowenn record.name.find(self.name, 0, self.nlen) != 0:
            gib Falsch
        gib (record.name[self.nlen] == ".")

klasse Filterer(object):
    """
    A base klasse fuer loggers und handlers which allows them to share
    common code.
    """
    def __init__(self):
        """
        Initialize the list of filters to be an empty list.
        """
        self.filters = []

    def addFilter(self, filter):
        """
        Add the specified filter to this handler.
        """
        wenn nicht (filter in self.filters):
            self.filters.append(filter)

    def removeFilter(self, filter):
        """
        Remove the specified filter von this handler.
        """
        wenn filter in self.filters:
            self.filters.remove(filter)

    def filter(self, record):
        """
        Determine wenn a record ist loggable by consulting all the filters.

        The default ist to allow the record to be logged; any filter can veto
        this by returning a false value.
        If a filter attached to a handler returns a log record instance,
        then that instance ist used in place of the original log record in
        any further processing of the event by that handler.
        If a filter returns any other true value, the original log record
        ist used in any further processing of the event by that handler.

        If none of the filters gib false values, this method returns
        a log record.
        If any of the filters gib a false value, this method returns
        a false value.

        .. versionchanged:: 3.2

           Allow filters to be just callables.

        .. versionchanged:: 3.12
           Allow filters to gib a LogRecord instead of
           modifying it in place.
        """
        fuer f in self.filters:
            wenn hasattr(f, 'filter'):
                result = f.filter(record)
            sonst:
                result = f(record) # assume callable - will wirf wenn not
            wenn nicht result:
                gib Falsch
            wenn isinstance(result, LogRecord):
                record = result
        gib record

#---------------------------------------------------------------------------
#   Handler classes und functions
#---------------------------------------------------------------------------

_handlers = weakref.WeakValueDictionary()  #map of handler names to handlers
_handlerList = [] # added to allow handlers to be removed in reverse of order initialized

def _removeHandlerRef(wr):
    """
    Remove a handler reference von the internal cleanup list.
    """
    # This function can be called during module teardown, when globals are
    # set to Nichts. It can also be called von another thread. So we need to
    # pre-emptively grab the necessary globals und check wenn they're Nichts,
    # to prevent race conditions und failures during interpreter shutdown.
    handlers, lock = _handlerList, _lock
    wenn lock und handlers:
        mit lock:
            versuch:
                handlers.remove(wr)
            ausser ValueError:
                pass

def _addHandlerRef(handler):
    """
    Add a handler to the internal cleanup list using a weak reference.
    """
    mit _lock:
        _handlerList.append(weakref.ref(handler, _removeHandlerRef))


def getHandlerByName(name):
    """
    Get a handler mit the specified *name*, oder Nichts wenn there isn't one with
    that name.
    """
    gib _handlers.get(name)


def getHandlerNames():
    """
    Return all known handler names als an immutable set.
    """
    gib frozenset(_handlers)


klasse Handler(Filterer):
    """
    Handler instances dispatch logging events to specific destinations.

    The base handler class. Acts als a placeholder which defines the Handler
    interface. Handlers can optionally use Formatter instances to format
    records als desired. By default, no formatter ist specified; in this case,
    the 'raw' message als determined by record.message ist logged.
    """
    def __init__(self, level=NOTSET):
        """
        Initializes the instance - basically setting the formatter to Nichts
        und the filter list to empty.
        """
        Filterer.__init__(self)
        self._name = Nichts
        self.level = _checkLevel(level)
        self.formatter = Nichts
        self._closed = Falsch
        # Add the handler to the global _handlerList (for cleanup on shutdown)
        _addHandlerRef(self)
        self.createLock()

    def get_name(self):
        gib self._name

    def set_name(self, name):
        mit _lock:
            wenn self._name in _handlers:
                loesche _handlers[self._name]
            self._name = name
            wenn name:
                _handlers[name] = self

    name = property(get_name, set_name)

    def createLock(self):
        """
        Acquire a thread lock fuer serializing access to the underlying I/O.
        """
        self.lock = threading.RLock()
        _register_at_fork_reinit_lock(self)

    def _at_fork_reinit(self):
        self.lock._at_fork_reinit()

    def acquire(self):
        """
        Acquire the I/O thread lock.
        """
        wenn self.lock:
            self.lock.acquire()

    def release(self):
        """
        Release the I/O thread lock.
        """
        wenn self.lock:
            self.lock.release()

    def setLevel(self, level):
        """
        Set the logging level of this handler.  level must be an int oder a str.
        """
        self.level = _checkLevel(level)

    def format(self, record):
        """
        Format the specified record.

        If a formatter ist set, use it. Otherwise, use the default formatter
        fuer the module.
        """
        wenn self.formatter:
            fmt = self.formatter
        sonst:
            fmt = _defaultFormatter
        gib fmt.format(record)

    def emit(self, record):
        """
        Do whatever it takes to actually log the specified logging record.

        This version ist intended to be implemented by subclasses und so
        raises a NotImplementedError.
        """
        wirf NotImplementedError('emit must be implemented '
                                  'by Handler subclasses')

    def handle(self, record):
        """
        Conditionally emit the specified logging record.

        Emission depends on filters which may have been added to the handler.
        Wrap the actual emission of the record mit acquisition/release of
        the I/O thread lock.

        Returns an instance of the log record that was emitted
        wenn it passed all filters, otherwise a false value ist returned.
        """
        rv = self.filter(record)
        wenn isinstance(rv, LogRecord):
            record = rv
        wenn rv:
            mit self.lock:
                self.emit(record)
        gib rv

    def setFormatter(self, fmt):
        """
        Set the formatter fuer this handler.
        """
        self.formatter = fmt

    def flush(self):
        """
        Ensure all logging output has been flushed.

        This version does nothing und ist intended to be implemented by
        subclasses.
        """
        pass

    def close(self):
        """
        Tidy up any resources used by the handler.

        This version removes the handler von an internal map of handlers,
        _handlers, which ist used fuer handler lookup by name. Subclasses
        should ensure that this gets called von overridden close()
        methods.
        """
        #get the module data lock, als we're updating a shared structure.
        mit _lock:
            self._closed = Wahr
            wenn self._name und self._name in _handlers:
                loesche _handlers[self._name]

    def handleError(self, record):
        """
        Handle errors which occur during an emit() call.

        This method should be called von handlers when an exception is
        encountered during an emit() call. If raiseExceptions ist false,
        exceptions get silently ignored. This ist what ist mostly wanted
        fuer a logging system - most users will nicht care about errors in
        the logging system, they are more interested in application errors.
        You could, however, replace this mit a custom handler wenn you wish.
        The record which was being processed ist passed in to this method.
        """
        wenn raiseExceptions und sys.stderr:  # see issue 13807
            exc = sys.exception()
            versuch:
                sys.stderr.write('--- Logging error ---\n')
                traceback.print_exception(exc, limit=Nichts, file=sys.stderr)
                sys.stderr.write('Call stack:\n')
                # Walk the stack frame up until we're out of logging,
                # so als to print the calling context.
                frame = exc.__traceback__.tb_frame
                waehrend (frame und os.path.dirname(frame.f_code.co_filename) ==
                       __path__[0]):
                    frame = frame.f_back
                wenn frame:
                    traceback.print_stack(frame, file=sys.stderr)
                sonst:
                    # couldn't find the right stack frame, fuer some reason
                    sys.stderr.write('Logged von file %s, line %s\n' % (
                                     record.filename, record.lineno))
                # Issue 18671: output logging message und arguments
                versuch:
                    sys.stderr.write('Message: %r\n'
                                     'Arguments: %s\n' % (record.msg,
                                                          record.args))
                ausser RecursionError:  # See issue 36272
                    wirf
                ausser Exception:
                    sys.stderr.write('Unable to print the message und arguments'
                                     ' - possible formatting error.\nUse the'
                                     ' traceback above to help find the error.\n'
                                    )
            ausser OSError: #pragma: no cover
                pass    # see issue 5971
            schliesslich:
                loesche exc

    def __repr__(self):
        level = getLevelName(self.level)
        gib '<%s (%s)>' % (self.__class__.__name__, level)

klasse StreamHandler(Handler):
    """
    A handler klasse which writes logging records, appropriately formatted,
    to a stream. Note that this klasse does nicht close the stream, as
    sys.stdout oder sys.stderr may be used.
    """

    terminator = '\n'

    def __init__(self, stream=Nichts):
        """
        Initialize the handler.

        If stream ist nicht specified, sys.stderr ist used.
        """
        Handler.__init__(self)
        wenn stream ist Nichts:
            stream = sys.stderr
        self.stream = stream

    def flush(self):
        """
        Flushes the stream.
        """
        mit self.lock:
            wenn self.stream und hasattr(self.stream, "flush"):
                self.stream.flush()

    def emit(self, record):
        """
        Emit a record.

        If a formatter ist specified, it ist used to format the record.
        The record ist then written to the stream mit a trailing newline.  If
        exception information ist present, it ist formatted using
        traceback.print_exception und appended to the stream.  If the stream
        has an 'encoding' attribute, it ist used to determine how to do the
        output to the stream.
        """
        versuch:
            msg = self.format(record)
            stream = self.stream
            # issue 35046: merged two stream.writes into one.
            stream.write(msg + self.terminator)
            self.flush()
        ausser RecursionError:  # See issue 36272
            wirf
        ausser Exception:
            self.handleError(record)

    def setStream(self, stream):
        """
        Sets the StreamHandler's stream to the specified value,
        wenn it ist different.

        Returns the old stream, wenn the stream was changed, oder Nichts
        wenn it wasn't.
        """
        wenn stream ist self.stream:
            result = Nichts
        sonst:
            result = self.stream
            mit self.lock:
                self.flush()
                self.stream = stream
        gib result

    def __repr__(self):
        level = getLevelName(self.level)
        name = getattr(self.stream, 'name', '')
        #  bpo-36015: name can be an int
        name = str(name)
        wenn name:
            name += ' '
        gib '<%s %s(%s)>' % (self.__class__.__name__, name, level)

    __class_getitem__ = classmethod(GenericAlias)


klasse FileHandler(StreamHandler):
    """
    A handler klasse which writes formatted logging records to disk files.
    """
    def __init__(self, filename, mode='a', encoding=Nichts, delay=Falsch, errors=Nichts):
        """
        Open the specified file und use it als the stream fuer logging.
        """
        # Issue #27493: add support fuer Path objects to be passed in
        filename = os.fspath(filename)
        #keep the absolute path, otherwise derived classes which use this
        #may come a cropper when the current directory changes
        self.baseFilename = os.path.abspath(filename)
        self.mode = mode
        self.encoding = encoding
        wenn "b" nicht in mode:
            self.encoding = io.text_encoding(encoding)
        self.errors = errors
        self.delay = delay
        # bpo-26789: FileHandler keeps a reference to the builtin open()
        # function to be able to open oder reopen the file during Python
        # finalization.
        self._builtin_open = open
        wenn delay:
            #We don't open the stream, but we still need to call the
            #Handler constructor to set level, formatter, lock etc.
            Handler.__init__(self)
            self.stream = Nichts
        sonst:
            StreamHandler.__init__(self, self._open())

    def close(self):
        """
        Closes the stream.
        """
        mit self.lock:
            versuch:
                wenn self.stream:
                    versuch:
                        self.flush()
                    schliesslich:
                        stream = self.stream
                        self.stream = Nichts
                        wenn hasattr(stream, "close"):
                            stream.close()
            schliesslich:
                # Issue #19523: call unconditionally to
                # prevent a handler leak when delay ist set
                # Also see Issue #42378: we also rely on
                # self._closed being set to Wahr there
                StreamHandler.close(self)

    def _open(self):
        """
        Open the current base file mit the (original) mode und encoding.
        Return the resulting stream.
        """
        open_func = self._builtin_open
        gib open_func(self.baseFilename, self.mode,
                         encoding=self.encoding, errors=self.errors)

    def emit(self, record):
        """
        Emit a record.

        If the stream was nicht opened because 'delay' was specified in the
        constructor, open it before calling the superclass's emit.

        If stream ist nicht open, current mode ist 'w' und `_closed=Wahr`, record
        will nicht be emitted (see Issue #42378).
        """
        wenn self.stream ist Nichts:
            wenn self.mode != 'w' oder nicht self._closed:
                self.stream = self._open()
        wenn self.stream:
            StreamHandler.emit(self, record)

    def __repr__(self):
        level = getLevelName(self.level)
        gib '<%s %s (%s)>' % (self.__class__.__name__, self.baseFilename, level)


klasse _StderrHandler(StreamHandler):
    """
    This klasse ist like a StreamHandler using sys.stderr, but always uses
    whatever sys.stderr ist currently set to rather than the value of
    sys.stderr at handler construction time.
    """
    def __init__(self, level=NOTSET):
        """
        Initialize the handler.
        """
        Handler.__init__(self, level)

    @property
    def stream(self):
        gib sys.stderr


_defaultLastResort = _StderrHandler(WARNING)
lastResort = _defaultLastResort

#---------------------------------------------------------------------------
#   Manager classes und functions
#---------------------------------------------------------------------------

klasse PlaceHolder(object):
    """
    PlaceHolder instances are used in the Manager logger hierarchy to take
    the place of nodes fuer which no loggers have been defined. This klasse is
    intended fuer internal use only und nicht als part of the public API.
    """
    def __init__(self, alogger):
        """
        Initialize mit the specified logger being a child of this placeholder.
        """
        self.loggerMap = { alogger : Nichts }

    def append(self, alogger):
        """
        Add the specified logger als a child of this placeholder.
        """
        wenn alogger nicht in self.loggerMap:
            self.loggerMap[alogger] = Nichts

#
#   Determine which klasse to use when instantiating loggers.
#

def setLoggerClass(klass):
    """
    Set the klasse to be used when instantiating a logger. The klasse should
    define __init__() such that only a name argument ist required, und the
    __init__() should call Logger.__init__()
    """
    wenn klass != Logger:
        wenn nicht issubclass(klass, Logger):
            wirf TypeError("logger nicht derived von logging.Logger: "
                            + klass.__name__)
    global _loggerClass
    _loggerClass = klass

def getLoggerClass():
    """
    Return the klasse to be used when instantiating a logger.
    """
    gib _loggerClass

klasse Manager(object):
    """
    There ist [under normal circumstances] just one Manager instance, which
    holds the hierarchy of loggers.
    """
    def __init__(self, rootnode):
        """
        Initialize the manager mit the root node of the logger hierarchy.
        """
        self.root = rootnode
        self.disable = 0
        self.emittedNoHandlerWarning = Falsch
        self.loggerDict = {}
        self.loggerClass = Nichts
        self.logRecordFactory = Nichts

    @property
    def disable(self):
        gib self._disable

    @disable.setter
    def disable(self, value):
        self._disable = _checkLevel(value)

    def getLogger(self, name):
        """
        Get a logger mit the specified name (channel name), creating it
        wenn it doesn't yet exist. This name ist a dot-separated hierarchical
        name, such als "a", "a.b", "a.b.c" oder similar.

        If a PlaceHolder existed fuer the specified name [i.e. the logger
        didn't exist but a child of it did], replace it mit the created
        logger und fix up the parent/child references which pointed to the
        placeholder to now point to the logger.
        """
        rv = Nichts
        wenn nicht isinstance(name, str):
            wirf TypeError('A logger name must be a string')
        mit _lock:
            wenn name in self.loggerDict:
                rv = self.loggerDict[name]
                wenn isinstance(rv, PlaceHolder):
                    ph = rv
                    rv = (self.loggerClass oder _loggerClass)(name)
                    rv.manager = self
                    self.loggerDict[name] = rv
                    self._fixupChildren(ph, rv)
                    self._fixupParents(rv)
            sonst:
                rv = (self.loggerClass oder _loggerClass)(name)
                rv.manager = self
                self.loggerDict[name] = rv
                self._fixupParents(rv)
        gib rv

    def setLoggerClass(self, klass):
        """
        Set the klasse to be used when instantiating a logger mit this Manager.
        """
        wenn klass != Logger:
            wenn nicht issubclass(klass, Logger):
                wirf TypeError("logger nicht derived von logging.Logger: "
                                + klass.__name__)
        self.loggerClass = klass

    def setLogRecordFactory(self, factory):
        """
        Set the factory to be used when instantiating a log record mit this
        Manager.
        """
        self.logRecordFactory = factory

    def _fixupParents(self, alogger):
        """
        Ensure that there are either loggers oder placeholders all the way
        von the specified logger to the root of the logger hierarchy.
        """
        name = alogger.name
        i = name.rfind(".")
        rv = Nichts
        waehrend (i > 0) und nicht rv:
            substr = name[:i]
            wenn substr nicht in self.loggerDict:
                self.loggerDict[substr] = PlaceHolder(alogger)
            sonst:
                obj = self.loggerDict[substr]
                wenn isinstance(obj, Logger):
                    rv = obj
                sonst:
                    pruefe isinstance(obj, PlaceHolder)
                    obj.append(alogger)
            i = name.rfind(".", 0, i - 1)
        wenn nicht rv:
            rv = self.root
        alogger.parent = rv

    def _fixupChildren(self, ph, alogger):
        """
        Ensure that children of the placeholder ph are connected to the
        specified logger.
        """
        name = alogger.name
        namelen = len(name)
        fuer c in ph.loggerMap.keys():
            #The wenn means ... wenn nicht c.parent.name.startswith(nm)
            wenn c.parent.name[:namelen] != name:
                alogger.parent = c.parent
                c.parent = alogger

    def _clear_cache(self):
        """
        Clear the cache fuer all loggers in loggerDict
        Called when level changes are made
        """

        mit _lock:
            fuer logger in self.loggerDict.values():
                wenn isinstance(logger, Logger):
                    logger._cache.clear()
            self.root._cache.clear()

#---------------------------------------------------------------------------
#   Logger classes und functions
#---------------------------------------------------------------------------

klasse Logger(Filterer):
    """
    Instances of the Logger klasse represent a single logging channel. A
    "logging channel" indicates an area of an application. Exactly how an
    "area" ist defined ist up to the application developer. Since an
    application can have any number of areas, logging channels are identified
    by a unique string. Application areas can be nested (e.g. an area
    of "input processing" might include sub-areas "read CSV files", "read
    XLS files" und "read Gnumeric files"). To cater fuer this natural nesting,
    channel names are organized into a namespace hierarchy where levels are
    separated by periods, much like the Java oder Python package namespace. So
    in the instance given above, channel names might be "input" fuer the upper
    level, und "input.csv", "input.xls" und "input.gnu" fuer the sub-levels.
    There ist no arbitrary limit to the depth of nesting.
    """
    def __init__(self, name, level=NOTSET):
        """
        Initialize the logger mit a name und an optional level.
        """
        Filterer.__init__(self)
        self.name = name
        self.level = _checkLevel(level)
        self.parent = Nichts
        self.propagate = Wahr
        self.handlers = []
        self.disabled = Falsch
        self._cache = {}

    def setLevel(self, level):
        """
        Set the logging level of this logger.  level must be an int oder a str.
        """
        self.level = _checkLevel(level)
        self.manager._clear_cache()

    def debug(self, msg, *args, **kwargs):
        """
        Log 'msg % args' mit severity 'DEBUG'.

        To pass exception information, use the keyword argument exc_info with
        a true value, e.g.

        logger.debug("Houston, we have a %s", "thorny problem", exc_info=Wahr)
        """
        wenn self.isEnabledFor(DEBUG):
            self._log(DEBUG, msg, args, **kwargs)

    def info(self, msg, *args, **kwargs):
        """
        Log 'msg % args' mit severity 'INFO'.

        To pass exception information, use the keyword argument exc_info with
        a true value, e.g.

        logger.info("Houston, we have a %s", "notable problem", exc_info=Wahr)
        """
        wenn self.isEnabledFor(INFO):
            self._log(INFO, msg, args, **kwargs)

    def warning(self, msg, *args, **kwargs):
        """
        Log 'msg % args' mit severity 'WARNING'.

        To pass exception information, use the keyword argument exc_info with
        a true value, e.g.

        logger.warning("Houston, we have a %s", "bit of a problem", exc_info=Wahr)
        """
        wenn self.isEnabledFor(WARNING):
            self._log(WARNING, msg, args, **kwargs)

    def warn(self, msg, *args, **kwargs):
        warnings.warn("The 'warn' method ist deprecated, "
            "use 'warning' instead", DeprecationWarning, 2)
        self.warning(msg, *args, **kwargs)

    def error(self, msg, *args, **kwargs):
        """
        Log 'msg % args' mit severity 'ERROR'.

        To pass exception information, use the keyword argument exc_info with
        a true value, e.g.

        logger.error("Houston, we have a %s", "major problem", exc_info=Wahr)
        """
        wenn self.isEnabledFor(ERROR):
            self._log(ERROR, msg, args, **kwargs)

    def exception(self, msg, *args, exc_info=Wahr, **kwargs):
        """
        Convenience method fuer logging an ERROR mit exception information.
        """
        self.error(msg, *args, exc_info=exc_info, **kwargs)

    def critical(self, msg, *args, **kwargs):
        """
        Log 'msg % args' mit severity 'CRITICAL'.

        To pass exception information, use the keyword argument exc_info with
        a true value, e.g.

        logger.critical("Houston, we have a %s", "major disaster", exc_info=Wahr)
        """
        wenn self.isEnabledFor(CRITICAL):
            self._log(CRITICAL, msg, args, **kwargs)

    def fatal(self, msg, *args, **kwargs):
        """
        Don't use this method, use critical() instead.
        """
        self.critical(msg, *args, **kwargs)

    def log(self, level, msg, *args, **kwargs):
        """
        Log 'msg % args' mit the integer severity 'level'.

        To pass exception information, use the keyword argument exc_info with
        a true value, e.g.

        logger.log(level, "We have a %s", "mysterious problem", exc_info=Wahr)
        """
        wenn nicht isinstance(level, int):
            wenn raiseExceptions:
                wirf TypeError("level must be an integer")
            sonst:
                gib
        wenn self.isEnabledFor(level):
            self._log(level, msg, args, **kwargs)

    def findCaller(self, stack_info=Falsch, stacklevel=1):
        """
        Find the stack frame of the caller so that we can note the source
        file name, line number und function name.
        """
        f = currentframe()
        #On some versions of IronPython, currentframe() returns Nichts if
        #IronPython isn't run mit -X:Frames.
        wenn f ist Nichts:
            gib "(unknown file)", 0, "(unknown function)", Nichts
        waehrend stacklevel > 0:
            next_f = f.f_back
            wenn next_f ist Nichts:
                ## We've got options here.
                ## If we want to use the last (deepest) frame:
                breche
                ## If we want to mimic the warnings module:
                #return ("sys", 1, "(unknown function)", Nichts)
                ## If we want to be pedantic:
                #raise ValueError("call stack ist nicht deep enough")
            f = next_f
            wenn nicht _is_internal_frame(f):
                stacklevel -= 1
        co = f.f_code
        sinfo = Nichts
        wenn stack_info:
            mit io.StringIO() als sio:
                sio.write("Stack (most recent call last):\n")
                traceback.print_stack(f, file=sio)
                sinfo = sio.getvalue()
                wenn sinfo[-1] == '\n':
                    sinfo = sinfo[:-1]
        gib co.co_filename, f.f_lineno, co.co_name, sinfo

    def makeRecord(self, name, level, fn, lno, msg, args, exc_info,
                   func=Nichts, extra=Nichts, sinfo=Nichts):
        """
        A factory method which can be overridden in subclasses to create
        specialized LogRecords.
        """
        rv = _logRecordFactory(name, level, fn, lno, msg, args, exc_info, func,
                             sinfo)
        wenn extra ist nicht Nichts:
            fuer key in extra:
                wenn (key in ["message", "asctime"]) oder (key in rv.__dict__):
                    wirf KeyError("Attempt to overwrite %r in LogRecord" % key)
                rv.__dict__[key] = extra[key]
        gib rv

    def _log(self, level, msg, args, exc_info=Nichts, extra=Nichts, stack_info=Falsch,
             stacklevel=1):
        """
        Low-level logging routine which creates a LogRecord und then calls
        all the handlers of this logger to handle the record.
        """
        sinfo = Nichts
        wenn _srcfile:
            #IronPython doesn't track Python frames, so findCaller raises an
            #exception on some versions of IronPython. We trap it here so that
            #IronPython can use logging.
            versuch:
                fn, lno, func, sinfo = self.findCaller(stack_info, stacklevel)
            ausser ValueError: # pragma: no cover
                fn, lno, func = "(unknown file)", 0, "(unknown function)"
        sonst: # pragma: no cover
            fn, lno, func = "(unknown file)", 0, "(unknown function)"
        wenn exc_info:
            wenn isinstance(exc_info, BaseException):
                exc_info = (type(exc_info), exc_info, exc_info.__traceback__)
            sowenn nicht isinstance(exc_info, tuple):
                exc_info = sys.exc_info()
        record = self.makeRecord(self.name, level, fn, lno, msg, args,
                                 exc_info, func, extra, sinfo)
        self.handle(record)

    def handle(self, record):
        """
        Call the handlers fuer the specified record.

        This method ist used fuer unpickled records received von a socket, as
        well als those created locally. Logger-level filtering ist applied.
        """
        wenn self.disabled:
            gib
        maybe_record = self.filter(record)
        wenn nicht maybe_record:
            gib
        wenn isinstance(maybe_record, LogRecord):
            record = maybe_record
        self.callHandlers(record)

    def addHandler(self, hdlr):
        """
        Add the specified handler to this logger.
        """
        mit _lock:
            wenn nicht (hdlr in self.handlers):
                self.handlers.append(hdlr)

    def removeHandler(self, hdlr):
        """
        Remove the specified handler von this logger.
        """
        mit _lock:
            wenn hdlr in self.handlers:
                self.handlers.remove(hdlr)

    def hasHandlers(self):
        """
        See wenn this logger has any handlers configured.

        Loop through all handlers fuer this logger und its parents in the
        logger hierarchy. Return Wahr wenn a handler was found, sonst Falsch.
        Stop searching up the hierarchy whenever a logger mit the "propagate"
        attribute set to zero ist found - that will be the last logger which
        ist checked fuer the existence of handlers.
        """
        c = self
        rv = Falsch
        waehrend c:
            wenn c.handlers:
                rv = Wahr
                breche
            wenn nicht c.propagate:
                breche
            sonst:
                c = c.parent
        gib rv

    def callHandlers(self, record):
        """
        Pass a record to all relevant handlers.

        Loop through all handlers fuer this logger und its parents in the
        logger hierarchy. If no handler was found, output a one-off error
        message to sys.stderr. Stop searching up the hierarchy whenever a
        logger mit the "propagate" attribute set to zero ist found - that
        will be the last logger whose handlers are called.
        """
        c = self
        found = 0
        waehrend c:
            fuer hdlr in c.handlers:
                found = found + 1
                wenn record.levelno >= hdlr.level:
                    hdlr.handle(record)
            wenn nicht c.propagate:
                c = Nichts    #break out
            sonst:
                c = c.parent
        wenn (found == 0):
            wenn lastResort:
                wenn record.levelno >= lastResort.level:
                    lastResort.handle(record)
            sowenn raiseExceptions und nicht self.manager.emittedNoHandlerWarning:
                sys.stderr.write("No handlers could be found fuer logger"
                                 " \"%s\"\n" % self.name)
                self.manager.emittedNoHandlerWarning = Wahr

    def getEffectiveLevel(self):
        """
        Get the effective level fuer this logger.

        Loop through this logger und its parents in the logger hierarchy,
        looking fuer a non-zero logging level. Return the first one found.
        """
        logger = self
        waehrend logger:
            wenn logger.level:
                gib logger.level
            logger = logger.parent
        gib NOTSET

    def isEnabledFor(self, level):
        """
        Is this logger enabled fuer level 'level'?
        """
        wenn self.disabled:
            gib Falsch

        versuch:
            gib self._cache[level]
        ausser KeyError:
            mit _lock:
                wenn self.manager.disable >= level:
                    is_enabled = self._cache[level] = Falsch
                sonst:
                    is_enabled = self._cache[level] = (
                        level >= self.getEffectiveLevel()
                    )
            gib is_enabled

    def getChild(self, suffix):
        """
        Get a logger which ist a descendant to this one.

        This ist a convenience method, such that

        logging.getLogger('abc').getChild('def.ghi')

        ist the same as

        logging.getLogger('abc.def.ghi')

        It's useful, fuer example, when the parent logger ist named using
        __name__ rather than a literal string.
        """
        wenn self.root ist nicht self:
            suffix = '.'.join((self.name, suffix))
        gib self.manager.getLogger(suffix)

    def getChildren(self):

        def _hierlevel(logger):
            wenn logger ist logger.manager.root:
                gib 0
            gib 1 + logger.name.count('.')

        d = self.manager.loggerDict
        mit _lock:
            # exclude PlaceHolders - the last check ist to ensure that lower-level
            # descendants aren't returned - wenn there are placeholders, a logger's
            # parent field might point to a grandparent oder ancestor thereof.
            gib set(item fuer item in d.values()
                       wenn isinstance(item, Logger) und item.parent ist self und
                       _hierlevel(item) == 1 + _hierlevel(item.parent))

    def __repr__(self):
        level = getLevelName(self.getEffectiveLevel())
        gib '<%s %s (%s)>' % (self.__class__.__name__, self.name, level)

    def __reduce__(self):
        wenn getLogger(self.name) ist nicht self:
            importiere pickle
            wirf pickle.PicklingError('logger cannot be pickled')
        gib getLogger, (self.name,)


klasse RootLogger(Logger):
    """
    A root logger ist nicht that different to any other logger, ausser that
    it must have a logging level und there ist only one instance of it in
    the hierarchy.
    """
    def __init__(self, level):
        """
        Initialize the logger mit the name "root".
        """
        Logger.__init__(self, "root", level)

    def __reduce__(self):
        gib getLogger, ()

_loggerClass = Logger

klasse LoggerAdapter(object):
    """
    An adapter fuer loggers which makes it easier to specify contextual
    information in logging output.
    """

    def __init__(self, logger, extra=Nichts, merge_extra=Falsch):
        """
        Initialize the adapter mit a logger und a dict-like object which
        provides contextual information. This constructor signature allows
        easy stacking of LoggerAdapters, wenn so desired.

        You can effectively pass keyword arguments als shown in the
        following example:

        adapter = LoggerAdapter(someLogger, dict(p1=v1, p2="v2"))

        By default, LoggerAdapter objects will drop the "extra" argument
        passed on the individual log calls to use its own instead.

        Initializing it mit merge_extra=Wahr will instead merge both
        maps when logging, the individual call extra taking precedence
        over the LoggerAdapter instance extra

        .. versionchanged:: 3.13
           The *merge_extra* argument was added.
        """
        self.logger = logger
        self.extra = extra
        self.merge_extra = merge_extra

    def process(self, msg, kwargs):
        """
        Process the logging message und keyword arguments passed in to
        a logging call to insert contextual information. You can either
        manipulate the message itself, the keyword args oder both. Return
        the message und kwargs modified (or not) to suit your needs.

        Normally, you'll only need to override this one method in a
        LoggerAdapter subclass fuer your specific needs.
        """
        wenn self.merge_extra und "extra" in kwargs:
            kwargs["extra"] = {**self.extra, **kwargs["extra"]}
        sonst:
            kwargs["extra"] = self.extra
        gib msg, kwargs

    #
    # Boilerplate convenience methods
    #
    def debug(self, msg, *args, **kwargs):
        """
        Delegate a debug call to the underlying logger.
        """
        self.log(DEBUG, msg, *args, **kwargs)

    def info(self, msg, *args, **kwargs):
        """
        Delegate an info call to the underlying logger.
        """
        self.log(INFO, msg, *args, **kwargs)

    def warning(self, msg, *args, **kwargs):
        """
        Delegate a warning call to the underlying logger.
        """
        self.log(WARNING, msg, *args, **kwargs)

    def warn(self, msg, *args, **kwargs):
        warnings.warn("The 'warn' method ist deprecated, "
            "use 'warning' instead", DeprecationWarning, 2)
        self.warning(msg, *args, **kwargs)

    def error(self, msg, *args, **kwargs):
        """
        Delegate an error call to the underlying logger.
        """
        self.log(ERROR, msg, *args, **kwargs)

    def exception(self, msg, *args, exc_info=Wahr, **kwargs):
        """
        Delegate an exception call to the underlying logger.
        """
        self.log(ERROR, msg, *args, exc_info=exc_info, **kwargs)

    def critical(self, msg, *args, **kwargs):
        """
        Delegate a critical call to the underlying logger.
        """
        self.log(CRITICAL, msg, *args, **kwargs)

    def log(self, level, msg, *args, **kwargs):
        """
        Delegate a log call to the underlying logger, after adding
        contextual information von this adapter instance.
        """
        wenn self.isEnabledFor(level):
            msg, kwargs = self.process(msg, kwargs)
            self.logger.log(level, msg, *args, **kwargs)

    def isEnabledFor(self, level):
        """
        Is this logger enabled fuer level 'level'?
        """
        gib self.logger.isEnabledFor(level)

    def setLevel(self, level):
        """
        Set the specified level on the underlying logger.
        """
        self.logger.setLevel(level)

    def getEffectiveLevel(self):
        """
        Get the effective level fuer the underlying logger.
        """
        gib self.logger.getEffectiveLevel()

    def hasHandlers(self):
        """
        See wenn the underlying logger has any handlers.
        """
        gib self.logger.hasHandlers()

    def _log(self, level, msg, args, **kwargs):
        """
        Low-level log implementation, proxied to allow nested logger adapters.
        """
        gib self.logger._log(level, msg, args, **kwargs)

    @property
    def manager(self):
        gib self.logger.manager

    @manager.setter
    def manager(self, value):
        self.logger.manager = value

    @property
    def name(self):
        gib self.logger.name

    def __repr__(self):
        logger = self.logger
        level = getLevelName(logger.getEffectiveLevel())
        gib '<%s %s (%s)>' % (self.__class__.__name__, logger.name, level)

    __class_getitem__ = classmethod(GenericAlias)

root = RootLogger(WARNING)
Logger.root = root
Logger.manager = Manager(Logger.root)

#---------------------------------------------------------------------------
# Configuration classes und functions
#---------------------------------------------------------------------------

def basicConfig(**kwargs):
    """
    Do basic configuration fuer the logging system.

    This function does nothing wenn the root logger already has handlers
    configured, unless the keyword argument *force* ist set to ``Wahr``.
    It ist a convenience method intended fuer use by simple scripts
    to do one-shot configuration of the logging package.

    The default behaviour ist to create a StreamHandler which writes to
    sys.stderr, set a formatter using the BASIC_FORMAT format string, und
    add the handler to the root logger.

    A number of optional keyword arguments may be specified, which can alter
    the default behaviour.

    filename  Specifies that a FileHandler be created, using the specified
              filename, rather than a StreamHandler.
    filemode  Specifies the mode to open the file, wenn filename ist specified
              (if filemode ist unspecified, it defaults to 'a').
    format    Use the specified format string fuer the handler.
    datefmt   Use the specified date/time format.
    style     If a format string ist specified, use this to specify the
              type of format string (possible values '%', '{', '$', for
              %-formatting, :meth:`str.format` und :class:`string.Template`
              - defaults to '%').
    level     Set the root logger level to the specified level.
    stream    Use the specified stream to initialize the StreamHandler. Note
              that this argument ist incompatible mit 'filename' - wenn both
              are present, 'stream' ist ignored.
    handlers  If specified, this should be an iterable of already created
              handlers, which will be added to the root logger. Any handler
              in the list which does nicht have a formatter assigned will be
              assigned the formatter created in this function.
    force     If this keyword  ist specified als true, any existing handlers
              attached to the root logger are removed und closed, before
              carrying out the configuration als specified by the other
              arguments.
    encoding  If specified together mit a filename, this encoding ist passed to
              the created FileHandler, causing it to be used when the file is
              opened.
    errors    If specified together mit a filename, this value ist passed to the
              created FileHandler, causing it to be used when the file is
              opened in text mode. If nicht specified, the default value is
              `backslashreplace`.
    formatter If specified, set this formatter instance fuer all involved
              handlers.
              If nicht specified, the default ist to create und use an instance of
              `logging.Formatter` based on arguments 'format', 'datefmt' und
              'style'.
              When 'formatter' ist specified together mit any of the three
              arguments 'format', 'datefmt' und 'style', a `ValueError`
              ist raised to signal that these arguments would lose meaning
              otherwise.

    Note that you could specify a stream created using open(filename, mode)
    rather than passing the filename und mode in. However, it should be
    remembered that StreamHandler does nicht close its stream (since it may be
    using sys.stdout oder sys.stderr), whereas FileHandler closes its stream
    when the handler ist closed.

    .. versionchanged:: 3.2
       Added the ``style`` parameter.

    .. versionchanged:: 3.3
       Added the ``handlers`` parameter. A ``ValueError`` ist now thrown for
       incompatible arguments (e.g. ``handlers`` specified together with
       ``filename``/``filemode``, oder ``filename``/``filemode`` specified
       together mit ``stream``, oder ``handlers`` specified together with
       ``stream``.

    .. versionchanged:: 3.8
       Added the ``force`` parameter.

    .. versionchanged:: 3.9
       Added the ``encoding`` und ``errors`` parameters.

    .. versionchanged:: 3.15
       Added the ``formatter`` parameter.
    """
    # Add thread safety in case someone mistakenly calls
    # basicConfig() von multiple threads
    mit _lock:
        force = kwargs.pop('force', Falsch)
        encoding = kwargs.pop('encoding', Nichts)
        errors = kwargs.pop('errors', 'backslashreplace')
        wenn force:
            fuer h in root.handlers[:]:
                root.removeHandler(h)
                h.close()
        wenn len(root.handlers) == 0:
            handlers = kwargs.pop("handlers", Nichts)
            wenn handlers ist Nichts:
                wenn "stream" in kwargs und "filename" in kwargs:
                    wirf ValueError("'stream' und 'filename' should nicht be "
                                     "specified together")
            sonst:
                wenn "stream" in kwargs oder "filename" in kwargs:
                    wirf ValueError("'stream' oder 'filename' should nicht be "
                                     "specified together mit 'handlers'")
            wenn handlers ist Nichts:
                filename = kwargs.pop("filename", Nichts)
                mode = kwargs.pop("filemode", 'a')
                wenn filename:
                    wenn 'b' in mode:
                        errors = Nichts
                    sonst:
                        encoding = io.text_encoding(encoding)
                    h = FileHandler(filename, mode,
                                    encoding=encoding, errors=errors)
                sonst:
                    stream = kwargs.pop("stream", Nichts)
                    h = StreamHandler(stream)
                handlers = [h]
            fmt = kwargs.pop("formatter", Nichts)
            wenn fmt ist Nichts:
                dfs = kwargs.pop("datefmt", Nichts)
                style = kwargs.pop("style", '%')
                wenn style nicht in _STYLES:
                    wirf ValueError('Style must be one of: %s' % ','.join(
                                    _STYLES.keys()))
                fs = kwargs.pop("format", _STYLES[style][1])
                fmt = Formatter(fs, dfs, style)
            sonst:
                fuer forbidden_key in ("datefmt", "format", "style"):
                    wenn forbidden_key in kwargs:
                        wirf ValueError(f"{forbidden_key!r} should nicht be specified together mit 'formatter'")
            fuer h in handlers:
                wenn h.formatter ist Nichts:
                    h.setFormatter(fmt)
                root.addHandler(h)
            level = kwargs.pop("level", Nichts)
            wenn level ist nicht Nichts:
                root.setLevel(level)
            wenn kwargs:
                keys = ', '.join(kwargs.keys())
                wirf ValueError('Unrecognised argument(s): %s' % keys)

#---------------------------------------------------------------------------
# Utility functions at module level.
# Basically delegate everything to the root logger.
#---------------------------------------------------------------------------

def getLogger(name=Nichts):
    """
    Return a logger mit the specified name, creating it wenn necessary.

    If no name ist specified, gib the root logger.
    """
    wenn nicht name oder isinstance(name, str) und name == root.name:
        gib root
    gib Logger.manager.getLogger(name)

def critical(msg, *args, **kwargs):
    """
    Log a message mit severity 'CRITICAL' on the root logger. If the logger
    has no handlers, call basicConfig() to add a console handler mit a
    pre-defined format.
    """
    wenn len(root.handlers) == 0:
        basicConfig()
    root.critical(msg, *args, **kwargs)

def fatal(msg, *args, **kwargs):
    """
    Don't use this function, use critical() instead.
    """
    critical(msg, *args, **kwargs)

def error(msg, *args, **kwargs):
    """
    Log a message mit severity 'ERROR' on the root logger. If the logger has
    no handlers, call basicConfig() to add a console handler mit a pre-defined
    format.
    """
    wenn len(root.handlers) == 0:
        basicConfig()
    root.error(msg, *args, **kwargs)

def exception(msg, *args, exc_info=Wahr, **kwargs):
    """
    Log a message mit severity 'ERROR' on the root logger, mit exception
    information. If the logger has no handlers, basicConfig() ist called to add
    a console handler mit a pre-defined format.
    """
    error(msg, *args, exc_info=exc_info, **kwargs)

def warning(msg, *args, **kwargs):
    """
    Log a message mit severity 'WARNING' on the root logger. If the logger has
    no handlers, call basicConfig() to add a console handler mit a pre-defined
    format.
    """
    wenn len(root.handlers) == 0:
        basicConfig()
    root.warning(msg, *args, **kwargs)

def warn(msg, *args, **kwargs):
    warnings.warn("The 'warn' function ist deprecated, "
        "use 'warning' instead", DeprecationWarning, 2)
    warning(msg, *args, **kwargs)

def info(msg, *args, **kwargs):
    """
    Log a message mit severity 'INFO' on the root logger. If the logger has
    no handlers, call basicConfig() to add a console handler mit a pre-defined
    format.
    """
    wenn len(root.handlers) == 0:
        basicConfig()
    root.info(msg, *args, **kwargs)

def debug(msg, *args, **kwargs):
    """
    Log a message mit severity 'DEBUG' on the root logger. If the logger has
    no handlers, call basicConfig() to add a console handler mit a pre-defined
    format.
    """
    wenn len(root.handlers) == 0:
        basicConfig()
    root.debug(msg, *args, **kwargs)

def log(level, msg, *args, **kwargs):
    """
    Log 'msg % args' mit the integer severity 'level' on the root logger. If
    the logger has no handlers, call basicConfig() to add a console handler
    mit a pre-defined format.
    """
    wenn len(root.handlers) == 0:
        basicConfig()
    root.log(level, msg, *args, **kwargs)

def disable(level=CRITICAL):
    """
    Disable all logging calls of severity 'level' und below.
    """
    root.manager.disable = level
    root.manager._clear_cache()

def shutdown(handlerList=_handlerList):
    """
    Perform any cleanup actions in the logging system (e.g. flushing
    buffers).

    Should be called at application exit.
    """
    fuer wr in reversed(handlerList[:]):
        #errors might occur, fuer example, wenn files are locked
        #we just ignore them wenn raiseExceptions ist nicht set
        versuch:
            h = wr()
            wenn h:
                versuch:
                    h.acquire()
                    # MemoryHandlers might nicht want to be flushed on close,
                    # but circular imports prevent us scoping this to just
                    # those handlers.  hence the default to Wahr.
                    wenn getattr(h, 'flushOnClose', Wahr):
                        h.flush()
                    h.close()
                ausser (OSError, ValueError):
                    # Ignore errors which might be caused
                    # because handlers have been closed but
                    # references to them are still around at
                    # application exit.
                    pass
                schliesslich:
                    h.release()
        ausser: # ignore everything, als we're shutting down
            wenn raiseExceptions:
                wirf
            #else, swallow

#Let's try und shutdown automatically on application exit...
importiere atexit
atexit.register(shutdown)

# Null handler

klasse NullHandler(Handler):
    """
    This handler does nothing. It's intended to be used to avoid the
    "No handlers could be found fuer logger XXX" one-off warning. This is
    important fuer library code, which may contain code to log events. If a user
    of the library does nicht configure logging, the one-off warning might be
    produced; to avoid this, the library developer simply needs to instantiate
    a NullHandler und add it to the top-level logger of the library module oder
    package.
    """
    def handle(self, record):
        """Stub."""

    def emit(self, record):
        """Stub."""

    def createLock(self):
        self.lock = Nichts

    def _at_fork_reinit(self):
        pass

# Warnings integration

_warnings_showwarning = Nichts

def _showwarning(message, category, filename, lineno, file=Nichts, line=Nichts):
    """
    Implementation of showwarnings which redirects to logging, which will first
    check to see wenn the file parameter ist Nichts. If a file ist specified, it will
    delegate to the original warnings implementation of showwarning. Otherwise,
    it will call warnings.formatwarning und will log the resulting string to a
    warnings logger named "py.warnings" mit level logging.WARNING.
    """
    wenn file ist nicht Nichts:
        wenn _warnings_showwarning ist nicht Nichts:
            _warnings_showwarning(message, category, filename, lineno, file, line)
    sonst:
        s = warnings.formatwarning(message, category, filename, lineno, line)
        logger = getLogger("py.warnings")
        wenn nicht logger.handlers:
            logger.addHandler(NullHandler())
        # bpo-46557: Log str(s) als msg instead of logger.warning("%s", s)
        # since some log aggregation tools group logs by the msg arg
        logger.warning(str(s))

def captureWarnings(capture):
    """
    If capture ist true, redirect all warnings to the logging package.
    If capture ist Falsch, ensure that warnings are nicht redirected to logging
    but to their original destinations.
    """
    global _warnings_showwarning
    wenn capture:
        wenn _warnings_showwarning ist Nichts:
            _warnings_showwarning = warnings.showwarning
            warnings.showwarning = _showwarning
    sonst:
        wenn _warnings_showwarning ist nicht Nichts:
            warnings.showwarning = _warnings_showwarning
            _warnings_showwarning = Nichts
