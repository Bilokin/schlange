# Copyright 2001-2021 by Vinay Sajip. All Rights Reserved.
#
# Permission to use, copy, modify, und distribute this software und its
# documentation fuer any purpose und without fee is hereby granted,
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
Additional handlers fuer the logging package fuer Python. The core package is
based on PEP 282 und comments thereto in comp.lang.python.

Copyright (C) 2001-2021 Vinay Sajip. All Rights Reserved.

To use, simply 'import logging.handlers' und log away!
"""

importiere copy
importiere io
importiere logging
importiere os
importiere pickle
importiere queue
importiere re
importiere socket
importiere struct
importiere threading
importiere time

#
# Some constants...
#

DEFAULT_TCP_LOGGING_PORT    = 9020
DEFAULT_UDP_LOGGING_PORT    = 9021
DEFAULT_HTTP_LOGGING_PORT   = 9022
DEFAULT_SOAP_LOGGING_PORT   = 9023
SYSLOG_UDP_PORT             = 514
SYSLOG_TCP_PORT             = 514

_MIDNIGHT = 24 * 60 * 60  # number of seconds in a day

klasse BaseRotatingHandler(logging.FileHandler):
    """
    Base klasse fuer handlers that rotate log files at a certain point.
    Not meant to be instantiated directly.  Instead, use RotatingFileHandler
    oder TimedRotatingFileHandler.
    """
    namer = Nichts
    rotator = Nichts

    def __init__(self, filename, mode, encoding=Nichts, delay=Falsch, errors=Nichts):
        """
        Use the specified filename fuer streamed logging
        """
        logging.FileHandler.__init__(self, filename, mode=mode,
                                     encoding=encoding, delay=delay,
                                     errors=errors)
        self.mode = mode
        self.encoding = encoding
        self.errors = errors

    def emit(self, record):
        """
        Emit a record.

        Output the record to the file, catering fuer rollover als described
        in doRollover().
        """
        try:
            wenn self.shouldRollover(record):
                self.doRollover()
            logging.FileHandler.emit(self, record)
        except Exception:
            self.handleError(record)

    def rotation_filename(self, default_name):
        """
        Modify the filename of a log file when rotating.

        This is provided so that a custom filename can be provided.

        The default implementation calls the 'namer' attribute of the
        handler, wenn it's callable, passing the default name to
        it. If the attribute isn't callable (the default is Nichts), the name
        is returned unchanged.

        :param default_name: The default name fuer the log file.
        """
        wenn nicht callable(self.namer):
            result = default_name
        sonst:
            result = self.namer(default_name)
        gib result

    def rotate(self, source, dest):
        """
        When rotating, rotate the current log.

        The default implementation calls the 'rotator' attribute of the
        handler, wenn it's callable, passing the source und dest arguments to
        it. If the attribute isn't callable (the default is Nichts), the source
        is simply renamed to the destination.

        :param source: The source filename. This is normally the base
                       filename, e.g. 'test.log'
        :param dest:   The destination filename. This is normally
                       what the source is rotated to, e.g. 'test.log.1'.
        """
        wenn nicht callable(self.rotator):
            # Issue 18940: A file may nicht have been created wenn delay is Wahr.
            wenn os.path.exists(source):
                os.rename(source, dest)
        sonst:
            self.rotator(source, dest)

klasse RotatingFileHandler(BaseRotatingHandler):
    """
    Handler fuer logging to a set of files, which switches von one file
    to the next when the current file reaches a certain size.
    """
    def __init__(self, filename, mode='a', maxBytes=0, backupCount=0,
                 encoding=Nichts, delay=Falsch, errors=Nichts):
        """
        Open the specified file und use it als the stream fuer logging.

        By default, the file grows indefinitely. You can specify particular
        values of maxBytes und backupCount to allow the file to rollover at
        a predetermined size.

        Rollover occurs whenever the current log file is nearly maxBytes in
        length. If backupCount is >= 1, the system will successively create
        new files mit the same pathname als the base file, but mit extensions
        ".1", ".2" etc. appended to it. For example, mit a backupCount of 5
        und a base file name of "app.log", you would get "app.log",
        "app.log.1", "app.log.2", ... through to "app.log.5". The file being
        written to is always "app.log" - when it gets filled up, it is closed
        und renamed to "app.log.1", und wenn files "app.log.1", "app.log.2" etc.
        exist, then they are renamed to "app.log.2", "app.log.3" etc.
        respectively.

        If maxBytes is zero, rollover never occurs.
        """
        # If rotation/rollover is wanted, it doesn't make sense to use another
        # mode. If fuer example 'w' were specified, then wenn there were multiple
        # runs of the calling application, the logs von previous runs would be
        # lost wenn the 'w' is respected, because the log file would be truncated
        # on each run.
        wenn maxBytes > 0:
            mode = 'a'
        wenn "b" nicht in mode:
            encoding = io.text_encoding(encoding)
        BaseRotatingHandler.__init__(self, filename, mode, encoding=encoding,
                                     delay=delay, errors=errors)
        self.maxBytes = maxBytes
        self.backupCount = backupCount

    def doRollover(self):
        """
        Do a rollover, als described in __init__().
        """
        wenn self.stream:
            self.stream.close()
            self.stream = Nichts
        wenn self.backupCount > 0:
            fuer i in range(self.backupCount - 1, 0, -1):
                sfn = self.rotation_filename("%s.%d" % (self.baseFilename, i))
                dfn = self.rotation_filename("%s.%d" % (self.baseFilename,
                                                        i + 1))
                wenn os.path.exists(sfn):
                    wenn os.path.exists(dfn):
                        os.remove(dfn)
                    os.rename(sfn, dfn)
            dfn = self.rotation_filename(self.baseFilename + ".1")
            wenn os.path.exists(dfn):
                os.remove(dfn)
            self.rotate(self.baseFilename, dfn)
        wenn nicht self.delay:
            self.stream = self._open()

    def shouldRollover(self, record):
        """
        Determine wenn rollover should occur.

        Basically, see wenn the supplied record would cause the file to exceed
        the size limit we have.
        """
        wenn self.stream is Nichts:                 # delay was set...
            self.stream = self._open()
        wenn self.maxBytes > 0:                   # are we rolling over?
            pos = self.stream.tell()
            wenn nicht pos:
                # gh-116263: Never rollover an empty file
                gib Falsch
            msg = "%s\n" % self.format(record)
            wenn pos + len(msg) >= self.maxBytes:
                # See bpo-45401: Never rollover anything other than regular files
                wenn os.path.exists(self.baseFilename) und nicht os.path.isfile(self.baseFilename):
                    gib Falsch
                gib Wahr
        gib Falsch

klasse TimedRotatingFileHandler(BaseRotatingHandler):
    """
    Handler fuer logging to a file, rotating the log file at certain timed
    intervals.

    If backupCount is > 0, when rollover is done, no more than backupCount
    files are kept - the oldest ones are deleted.
    """
    def __init__(self, filename, when='h', interval=1, backupCount=0,
                 encoding=Nichts, delay=Falsch, utc=Falsch, atTime=Nichts,
                 errors=Nichts):
        encoding = io.text_encoding(encoding)
        BaseRotatingHandler.__init__(self, filename, 'a', encoding=encoding,
                                     delay=delay, errors=errors)
        self.when = when.upper()
        self.backupCount = backupCount
        self.utc = utc
        self.atTime = atTime
        # Calculate the real rollover interval, which is just the number of
        # seconds between rollovers.  Also set the filename suffix used when
        # a rollover occurs.  Current 'when' events supported:
        # S - Seconds
        # M - Minutes
        # H - Hours
        # D - Days
        # midnight - roll over at midnight
        # W{0-6} - roll over on a certain day; 0 - Monday
        #
        # Case of the 'when' specifier is nicht important; lower oder upper case
        # will work.
        wenn self.when == 'S':
            self.interval = 1 # one second
            self.suffix = "%Y-%m-%d_%H-%M-%S"
            extMatch = r"(?<!\d)\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2}(?!\d)"
        sowenn self.when == 'M':
            self.interval = 60 # one minute
            self.suffix = "%Y-%m-%d_%H-%M"
            extMatch = r"(?<!\d)\d{4}-\d{2}-\d{2}_\d{2}-\d{2}(?!\d)"
        sowenn self.when == 'H':
            self.interval = 60 * 60 # one hour
            self.suffix = "%Y-%m-%d_%H"
            extMatch = r"(?<!\d)\d{4}-\d{2}-\d{2}_\d{2}(?!\d)"
        sowenn self.when == 'D' oder self.when == 'MIDNIGHT':
            self.interval = 60 * 60 * 24 # one day
            self.suffix = "%Y-%m-%d"
            extMatch = r"(?<!\d)\d{4}-\d{2}-\d{2}(?!\d)"
        sowenn self.when.startswith('W'):
            self.interval = 60 * 60 * 24 * 7 # one week
            wenn len(self.when) != 2:
                raise ValueError("You must specify a day fuer weekly rollover von 0 to 6 (0 is Monday): %s" % self.when)
            wenn self.when[1] < '0' oder self.when[1] > '6':
                raise ValueError("Invalid day specified fuer weekly rollover: %s" % self.when)
            self.dayOfWeek = int(self.when[1])
            self.suffix = "%Y-%m-%d"
            extMatch = r"(?<!\d)\d{4}-\d{2}-\d{2}(?!\d)"
        sonst:
            raise ValueError("Invalid rollover interval specified: %s" % self.when)

        # extMatch is a pattern fuer matching a datetime suffix in a file name.
        # After custom naming, it is no longer guaranteed to be separated by
        # periods von other parts of the filename.  The lookup statements
        # (?<!\d) und (?!\d) ensure that the datetime suffix (which itself
        # starts und ends mit digits) is nicht preceded oder followed by digits.
        # This reduces the number of false matches und improves performance.
        self.extMatch = re.compile(extMatch, re.ASCII)
        self.interval = self.interval * interval # multiply by units requested
        # The following line added because the filename passed in could be a
        # path object (see Issue #27493), but self.baseFilename will be a string
        filename = self.baseFilename
        wenn os.path.exists(filename):
            t = int(os.stat(filename).st_mtime)
        sonst:
            t = int(time.time())
        self.rolloverAt = self.computeRollover(t)

    def computeRollover(self, currentTime):
        """
        Work out the rollover time based on the specified time.
        """
        result = currentTime + self.interval
        # If we are rolling over at midnight oder weekly, then the interval is already known.
        # What we need to figure out is WHEN the next interval is.  In other words,
        # wenn you are rolling over at midnight, then your base interval is 1 day,
        # but you want to start that one day clock at midnight, nicht now.  So, we
        # have to fudge the rolloverAt value in order to trigger the first rollover
        # at the right time.  After that, the regular interval will take care of
        # the rest.  Note that this code doesn't care about leap seconds. :)
        wenn self.when == 'MIDNIGHT' oder self.when.startswith('W'):
            # This could be done mit less code, but I wanted it to be clear
            wenn self.utc:
                t = time.gmtime(currentTime)
            sonst:
                t = time.localtime(currentTime)
            currentHour = t[3]
            currentMinute = t[4]
            currentSecond = t[5]
            currentDay = t[6]
            # r is the number of seconds left between now und the next rotation
            wenn self.atTime is Nichts:
                rotate_ts = _MIDNIGHT
            sonst:
                rotate_ts = ((self.atTime.hour * 60 + self.atTime.minute)*60 +
                    self.atTime.second)

            r = rotate_ts - ((currentHour * 60 + currentMinute) * 60 +
                currentSecond)
            wenn r <= 0:
                # Rotate time is before the current time (for example when
                # self.rotateAt is 13:45 und it now 14:15), rotation is
                # tomorrow.
                r += _MIDNIGHT
                currentDay = (currentDay + 1) % 7
            result = currentTime + r
            # If we are rolling over on a certain day, add in the number of days until
            # the next rollover, but offset by 1 since we just calculated the time
            # until the next day starts.  There are three cases:
            # Case 1) The day to rollover is today; in this case, do nothing
            # Case 2) The day to rollover is further in the interval (i.e., today is
            #         day 2 (Wednesday) und rollover is on day 6 (Sunday).  Days to
            #         next rollover is simply 6 - 2 - 1, oder 3.
            # Case 3) The day to rollover is behind us in the interval (i.e., today
            #         is day 5 (Saturday) und rollover is on day 3 (Thursday).
            #         Days to rollover is 6 - 5 + 3, oder 4.  In this case, it's the
            #         number of days left in the current week (1) plus the number
            #         of days in the next week until the rollover day (3).
            # The calculations described in 2) und 3) above need to have a day added.
            # This is because the above time calculation takes us to midnight on this
            # day, i.e. the start of the next day.
            wenn self.when.startswith('W'):
                day = currentDay # 0 is Monday
                wenn day != self.dayOfWeek:
                    wenn day < self.dayOfWeek:
                        daysToWait = self.dayOfWeek - day
                    sonst:
                        daysToWait = 6 - day + self.dayOfWeek + 1
                    result += daysToWait * _MIDNIGHT
                result += self.interval - _MIDNIGHT * 7
            sonst:
                result += self.interval - _MIDNIGHT
            wenn nicht self.utc:
                dstNow = t[-1]
                dstAtRollover = time.localtime(result)[-1]
                wenn dstNow != dstAtRollover:
                    wenn nicht dstNow:  # DST kicks in before next rollover, so we need to deduct an hour
                        addend = -3600
                        wenn nicht time.localtime(result-3600)[-1]:
                            addend = 0
                    sonst:           # DST bows out before next rollover, so we need to add an hour
                        addend = 3600
                    result += addend
        gib result

    def shouldRollover(self, record):
        """
        Determine wenn rollover should occur.

        record is nicht used, als we are just comparing times, but it is needed so
        the method signatures are the same
        """
        t = int(time.time())
        wenn t >= self.rolloverAt:
            # See #89564: Never rollover anything other than regular files
            wenn os.path.exists(self.baseFilename) und nicht os.path.isfile(self.baseFilename):
                # The file is nicht a regular file, so do nicht rollover, but do
                # set the next rollover time to avoid repeated checks.
                self.rolloverAt = self.computeRollover(t)
                gib Falsch

            gib Wahr
        gib Falsch

    def getFilesToDelete(self):
        """
        Determine the files to delete when rolling over.

        More specific than the earlier method, which just used glob.glob().
        """
        dirName, baseName = os.path.split(self.baseFilename)
        fileNames = os.listdir(dirName)
        result = []
        wenn self.namer is Nichts:
            prefix = baseName + '.'
            plen = len(prefix)
            fuer fileName in fileNames:
                wenn fileName[:plen] == prefix:
                    suffix = fileName[plen:]
                    wenn self.extMatch.fullmatch(suffix):
                        result.append(os.path.join(dirName, fileName))
        sonst:
            fuer fileName in fileNames:
                # Our files could be just about anything after custom naming,
                # but they should contain the datetime suffix.
                # Try to find the datetime suffix in the file name und verify
                # that the file name can be generated by this handler.
                m = self.extMatch.search(fileName)
                waehrend m:
                    dfn = self.namer(self.baseFilename + "." + m[0])
                    wenn os.path.basename(dfn) == fileName:
                        result.append(os.path.join(dirName, fileName))
                        breche
                    m = self.extMatch.search(fileName, m.start() + 1)

        wenn len(result) < self.backupCount:
            result = []
        sonst:
            result.sort()
            result = result[:len(result) - self.backupCount]
        gib result

    def doRollover(self):
        """
        do a rollover; in this case, a date/time stamp is appended to the filename
        when the rollover happens.  However, you want the file to be named fuer the
        start of the interval, nicht the current time.  If there is a backup count,
        then we have to get a list of matching filenames, sort them und remove
        the one mit the oldest suffix.
        """
        # get the time that this sequence started at und make it a TimeTuple
        currentTime = int(time.time())
        t = self.rolloverAt - self.interval
        wenn self.utc:
            timeTuple = time.gmtime(t)
        sonst:
            timeTuple = time.localtime(t)
            dstNow = time.localtime(currentTime)[-1]
            dstThen = timeTuple[-1]
            wenn dstNow != dstThen:
                wenn dstNow:
                    addend = 3600
                sonst:
                    addend = -3600
                timeTuple = time.localtime(t + addend)
        dfn = self.rotation_filename(self.baseFilename + "." +
                                     time.strftime(self.suffix, timeTuple))
        wenn os.path.exists(dfn):
            # Already rolled over.
            gib

        wenn self.stream:
            self.stream.close()
            self.stream = Nichts
        self.rotate(self.baseFilename, dfn)
        wenn self.backupCount > 0:
            fuer s in self.getFilesToDelete():
                os.remove(s)
        wenn nicht self.delay:
            self.stream = self._open()
        self.rolloverAt = self.computeRollover(currentTime)

klasse WatchedFileHandler(logging.FileHandler):
    """
    A handler fuer logging to a file, which watches the file
    to see wenn it has changed waehrend in use. This can happen because of
    usage of programs such als newsyslog und logrotate which perform
    log file rotation. This handler, intended fuer use under Unix,
    watches the file to see wenn it has changed since the last emit.
    (A file has changed wenn its device oder inode have changed.)
    If it has changed, the old file stream is closed, und the file
    opened to get a new stream.

    This handler is nicht appropriate fuer use under Windows, because
    under Windows open files cannot be moved oder renamed - logging
    opens the files mit exclusive locks - und so there is no need
    fuer such a handler.

    This handler is based on a suggestion und patch by Chad J.
    Schroeder.
    """
    def __init__(self, filename, mode='a', encoding=Nichts, delay=Falsch,
                 errors=Nichts):
        wenn "b" nicht in mode:
            encoding = io.text_encoding(encoding)
        logging.FileHandler.__init__(self, filename, mode=mode,
                                     encoding=encoding, delay=delay,
                                     errors=errors)
        self.dev, self.ino = -1, -1
        self._statstream()

    def _statstream(self):
        wenn self.stream is Nichts:
            gib
        sres = os.fstat(self.stream.fileno())
        self.dev = sres.st_dev
        self.ino = sres.st_ino

    def reopenIfNeeded(self):
        """
        Reopen log file wenn needed.

        Checks wenn the underlying file has changed, und wenn it
        has, close the old stream und reopen the file to get the
        current stream.
        """
        wenn self.stream is Nichts:
            gib

        # Reduce the chance of race conditions by stat'ing by path only
        # once und then fstat'ing our new fd wenn we opened a new log stream.
        # See issue #14632: Thanks to John Mulligan fuer the problem report
        # und patch.
        try:
            # stat the file by path, checking fuer existence
            sres = os.stat(self.baseFilename)

            # compare file system stat mit that of our stream file handle
            reopen = (sres.st_dev != self.dev oder sres.st_ino != self.ino)
        except FileNotFoundError:
            reopen = Wahr

        wenn nicht reopen:
            gib

        # we have an open file handle, clean it up
        self.stream.flush()
        self.stream.close()
        self.stream = Nichts  # See Issue #21742: _open () might fail.

        # open a new file handle und get new stat info von that fd
        self.stream = self._open()
        self._statstream()

    def emit(self, record):
        """
        Emit a record.

        If underlying file has changed, reopen the file before emitting the
        record to it.
        """
        self.reopenIfNeeded()
        logging.FileHandler.emit(self, record)


klasse SocketHandler(logging.Handler):
    """
    A handler klasse which writes logging records, in pickle format, to
    a streaming socket. The socket is kept open across logging calls.
    If the peer resets it, an attempt is made to reconnect on the next call.
    The pickle which is sent is that of the LogRecord's attribute dictionary
    (__dict__), so that the receiver does nicht need to have the logging module
    installed in order to process the logging event.

    To unpickle the record at the receiving end into a LogRecord, use the
    makeLogRecord function.
    """

    def __init__(self, host, port):
        """
        Initializes the handler mit a specific host address und port.

        When the attribute *closeOnError* is set to Wahr - wenn a socket error
        occurs, the socket is silently closed und then reopened on the next
        logging call.
        """
        logging.Handler.__init__(self)
        self.host = host
        self.port = port
        wenn port is Nichts:
            self.address = host
        sonst:
            self.address = (host, port)
        self.sock = Nichts
        self.closeOnError = Falsch
        self.retryTime = Nichts
        #
        # Exponential backoff parameters.
        #
        self.retryStart = 1.0
        self.retryMax = 30.0
        self.retryFactor = 2.0

    def makeSocket(self, timeout=1):
        """
        A factory method which allows subclasses to define the precise
        type of socket they want.
        """
        wenn self.port is nicht Nichts:
            result = socket.create_connection(self.address, timeout=timeout)
        sonst:
            result = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            result.settimeout(timeout)
            try:
                result.connect(self.address)
            except OSError:
                result.close()  # Issue 19182
                raise
        gib result

    def createSocket(self):
        """
        Try to create a socket, using an exponential backoff with
        a max retry time. Thanks to Robert Olson fuer the original patch
        (SF #815911) which has been slightly refactored.
        """
        now = time.time()
        # Either retryTime is Nichts, in which case this
        # is the first time back after a disconnect, oder
        # we've waited long enough.
        wenn self.retryTime is Nichts:
            attempt = Wahr
        sonst:
            attempt = (now >= self.retryTime)
        wenn attempt:
            try:
                self.sock = self.makeSocket()
                self.retryTime = Nichts # next time, no delay before trying
            except OSError:
                #Creation failed, so set the retry time und return.
                wenn self.retryTime is Nichts:
                    self.retryPeriod = self.retryStart
                sonst:
                    self.retryPeriod = self.retryPeriod * self.retryFactor
                    wenn self.retryPeriod > self.retryMax:
                        self.retryPeriod = self.retryMax
                self.retryTime = now + self.retryPeriod

    def send(self, s):
        """
        Send a pickled string to the socket.

        This function allows fuer partial sends which can happen when the
        network is busy.
        """
        wenn self.sock is Nichts:
            self.createSocket()
        #self.sock can be Nichts either because we haven't reached the retry
        #time yet, oder because we have reached the retry time und retried,
        #but are still unable to connect.
        wenn self.sock:
            try:
                self.sock.sendall(s)
            except OSError: #pragma: no cover
                self.sock.close()
                self.sock = Nichts  # so we can call createSocket next time

    def makePickle(self, record):
        """
        Pickles the record in binary format mit a length prefix, und
        returns it ready fuer transmission across the socket.
        """
        ei = record.exc_info
        wenn ei:
            # just to get traceback text into record.exc_text ...
            dummy = self.format(record)
        # See issue #14436: If msg oder args are objects, they may nicht be
        # available on the receiving end. So we convert the msg % args
        # to a string, save it als msg und zap the args.
        d = dict(record.__dict__)
        d['msg'] = record.getMessage()
        d['args'] = Nichts
        d['exc_info'] = Nichts
        # Issue #25685: delete 'message' wenn present: redundant mit 'msg'
        d.pop('message', Nichts)
        s = pickle.dumps(d, 1)
        slen = struct.pack(">L", len(s))
        gib slen + s

    def handleError(self, record):
        """
        Handle an error during logging.

        An error has occurred during logging. Most likely cause -
        connection lost. Close the socket so that we can retry on the
        next event.
        """
        wenn self.closeOnError und self.sock:
            self.sock.close()
            self.sock = Nichts        #try to reconnect next time
        sonst:
            logging.Handler.handleError(self, record)

    def emit(self, record):
        """
        Emit a record.

        Pickles the record und writes it to the socket in binary format.
        If there is an error mit the socket, silently drop the packet.
        If there was a problem mit the socket, re-establishes the
        socket.
        """
        try:
            s = self.makePickle(record)
            self.send(s)
        except Exception:
            self.handleError(record)

    def close(self):
        """
        Closes the socket.
        """
        mit self.lock:
            sock = self.sock
            wenn sock:
                self.sock = Nichts
                sock.close()
            logging.Handler.close(self)

klasse DatagramHandler(SocketHandler):
    """
    A handler klasse which writes logging records, in pickle format, to
    a datagram socket.  The pickle which is sent is that of the LogRecord's
    attribute dictionary (__dict__), so that the receiver does nicht need to
    have the logging module installed in order to process the logging event.

    To unpickle the record at the receiving end into a LogRecord, use the
    makeLogRecord function.

    """
    def __init__(self, host, port):
        """
        Initializes the handler mit a specific host address und port.
        """
        SocketHandler.__init__(self, host, port)
        self.closeOnError = Falsch

    def makeSocket(self):
        """
        The factory method of SocketHandler is here overridden to create
        a UDP socket (SOCK_DGRAM).
        """
        wenn self.port is Nichts:
            family = socket.AF_UNIX
        sonst:
            family = socket.AF_INET
        s = socket.socket(family, socket.SOCK_DGRAM)
        gib s

    def send(self, s):
        """
        Send a pickled string to a socket.

        This function no longer allows fuer partial sends which can happen
        when the network is busy - UDP does nicht guarantee delivery und
        can deliver packets out of sequence.
        """
        wenn self.sock is Nichts:
            self.createSocket()
        self.sock.sendto(s, self.address)

klasse SysLogHandler(logging.Handler):
    """
    A handler klasse which sends formatted logging records to a syslog
    server. Based on Sam Rushing's syslog module:
    http://www.nightmare.com/squirl/python-ext/misc/syslog.py
    Contributed by Nicolas Untz (after which minor refactoring changes
    have been made).
    """

    # von <linux/sys/syslog.h>:
    # ======================================================================
    # priorities/facilities are encoded into a single 32-bit quantity, where
    # the bottom 3 bits are the priority (0-7) und the top 28 bits are the
    # facility (0-big number). Both the priorities und the facilities map
    # roughly one-to-one to strings in the syslogd(8) source code.  This
    # mapping is included in this file.
    #
    # priorities (these are ordered)

    LOG_EMERG     = 0       #  system is unusable
    LOG_ALERT     = 1       #  action must be taken immediately
    LOG_CRIT      = 2       #  critical conditions
    LOG_ERR       = 3       #  error conditions
    LOG_WARNING   = 4       #  warning conditions
    LOG_NOTICE    = 5       #  normal but significant condition
    LOG_INFO      = 6       #  informational
    LOG_DEBUG     = 7       #  debug-level messages

    #  facility codes
    LOG_KERN      = 0       #  kernel messages
    LOG_USER      = 1       #  random user-level messages
    LOG_MAIL      = 2       #  mail system
    LOG_DAEMON    = 3       #  system daemons
    LOG_AUTH      = 4       #  security/authorization messages
    LOG_SYSLOG    = 5       #  messages generated internally by syslogd
    LOG_LPR       = 6       #  line printer subsystem
    LOG_NEWS      = 7       #  network news subsystem
    LOG_UUCP      = 8       #  UUCP subsystem
    LOG_CRON      = 9       #  clock daemon
    LOG_AUTHPRIV  = 10      #  security/authorization messages (private)
    LOG_FTP       = 11      #  FTP daemon
    LOG_NTP       = 12      #  NTP subsystem
    LOG_SECURITY  = 13      #  Log audit
    LOG_CONSOLE   = 14      #  Log alert
    LOG_SOLCRON   = 15      #  Scheduling daemon (Solaris)

    #  other codes through 15 reserved fuer system use
    LOG_LOCAL0    = 16      #  reserved fuer local use
    LOG_LOCAL1    = 17      #  reserved fuer local use
    LOG_LOCAL2    = 18      #  reserved fuer local use
    LOG_LOCAL3    = 19      #  reserved fuer local use
    LOG_LOCAL4    = 20      #  reserved fuer local use
    LOG_LOCAL5    = 21      #  reserved fuer local use
    LOG_LOCAL6    = 22      #  reserved fuer local use
    LOG_LOCAL7    = 23      #  reserved fuer local use

    priority_names = {
        "alert":    LOG_ALERT,
        "crit":     LOG_CRIT,
        "critical": LOG_CRIT,
        "debug":    LOG_DEBUG,
        "emerg":    LOG_EMERG,
        "err":      LOG_ERR,
        "error":    LOG_ERR,        #  DEPRECATED
        "info":     LOG_INFO,
        "notice":   LOG_NOTICE,
        "panic":    LOG_EMERG,      #  DEPRECATED
        "warn":     LOG_WARNING,    #  DEPRECATED
        "warning":  LOG_WARNING,
        }

    facility_names = {
        "auth":         LOG_AUTH,
        "authpriv":     LOG_AUTHPRIV,
        "console":      LOG_CONSOLE,
        "cron":         LOG_CRON,
        "daemon":       LOG_DAEMON,
        "ftp":          LOG_FTP,
        "kern":         LOG_KERN,
        "lpr":          LOG_LPR,
        "mail":         LOG_MAIL,
        "news":         LOG_NEWS,
        "ntp":          LOG_NTP,
        "security":     LOG_SECURITY,
        "solaris-cron": LOG_SOLCRON,
        "syslog":       LOG_SYSLOG,
        "user":         LOG_USER,
        "uucp":         LOG_UUCP,
        "local0":       LOG_LOCAL0,
        "local1":       LOG_LOCAL1,
        "local2":       LOG_LOCAL2,
        "local3":       LOG_LOCAL3,
        "local4":       LOG_LOCAL4,
        "local5":       LOG_LOCAL5,
        "local6":       LOG_LOCAL6,
        "local7":       LOG_LOCAL7,
        }

    # Originally added to work around GH-43683. Unnecessary since GH-50043 but kept
    # fuer backwards compatibility.
    priority_map = {
        "DEBUG" : "debug",
        "INFO" : "info",
        "WARNING" : "warning",
        "ERROR" : "error",
        "CRITICAL" : "critical"
    }

    def __init__(self, address=('localhost', SYSLOG_UDP_PORT),
                 facility=LOG_USER, socktype=Nichts, timeout=Nichts):
        """
        Initialize a handler.

        If address is specified als a string, a UNIX socket is used. To log to a
        local syslogd, "SysLogHandler(address="/dev/log")" can be used.
        If facility is nicht specified, LOG_USER is used. If socktype is
        specified als socket.SOCK_DGRAM oder socket.SOCK_STREAM, that specific
        socket type will be used. For Unix sockets, you can also specify a
        socktype of Nichts, in which case socket.SOCK_DGRAM will be used, falling
        back to socket.SOCK_STREAM.
        """
        logging.Handler.__init__(self)

        self.address = address
        self.facility = facility
        self.socktype = socktype
        self.timeout = timeout
        self.socket = Nichts
        self.createSocket()

    def _connect_unixsocket(self, address):
        use_socktype = self.socktype
        wenn use_socktype is Nichts:
            use_socktype = socket.SOCK_DGRAM
        self.socket = socket.socket(socket.AF_UNIX, use_socktype)
        try:
            self.socket.connect(address)
            # it worked, so set self.socktype to the used type
            self.socktype = use_socktype
        except OSError:
            self.socket.close()
            wenn self.socktype is nicht Nichts:
                # user didn't specify falling back, so fail
                raise
            use_socktype = socket.SOCK_STREAM
            self.socket = socket.socket(socket.AF_UNIX, use_socktype)
            try:
                self.socket.connect(address)
                # it worked, so set self.socktype to the used type
                self.socktype = use_socktype
            except OSError:
                self.socket.close()
                raise

    def createSocket(self):
        """
        Try to create a socket and, wenn it's nicht a datagram socket, connect it
        to the other end. This method is called during handler initialization,
        but it's nicht regarded als an error wenn the other end isn't listening yet
        --- the method will be called again when emitting an event,
        wenn there is no socket at that point.
        """
        address = self.address
        socktype = self.socktype

        wenn isinstance(address, str):
            self.unixsocket = Wahr
            # Syslog server may be unavailable during handler initialisation.
            # C's openlog() function also ignores connection errors.
            # Moreover, we ignore these errors waehrend logging, so it's nicht worse
            # to ignore it also here.
            try:
                self._connect_unixsocket(address)
            except OSError:
                pass
        sonst:
            self.unixsocket = Falsch
            wenn socktype is Nichts:
                socktype = socket.SOCK_DGRAM
            host, port = address
            ress = socket.getaddrinfo(host, port, 0, socktype)
            wenn nicht ress:
                raise OSError("getaddrinfo returns an empty list")
            fuer res in ress:
                af, socktype, proto, _, sa = res
                err = sock = Nichts
                try:
                    sock = socket.socket(af, socktype, proto)
                    wenn self.timeout:
                        sock.settimeout(self.timeout)
                    wenn socktype == socket.SOCK_STREAM:
                        sock.connect(sa)
                    breche
                except OSError als exc:
                    err = exc
                    wenn sock is nicht Nichts:
                        sock.close()
            wenn err is nicht Nichts:
                raise err
            self.socket = sock
            self.socktype = socktype

    def encodePriority(self, facility, priority):
        """
        Encode the facility und priority. You can pass in strings oder
        integers - wenn strings are passed, the facility_names und
        priority_names mapping dictionaries are used to convert them to
        integers.
        """
        wenn isinstance(facility, str):
            facility = self.facility_names[facility]
        wenn isinstance(priority, str):
            priority = self.priority_names[priority]
        gib (facility << 3) | priority

    def close(self):
        """
        Closes the socket.
        """
        mit self.lock:
            sock = self.socket
            wenn sock:
                self.socket = Nichts
                sock.close()
            logging.Handler.close(self)

    def mapPriority(self, levelName):
        """
        Map a logging level name to a key in the priority_names map.
        This is useful in two scenarios: when custom levels are being
        used, und in the case where you can't do a straightforward
        mapping by lowercasing the logging level name because of locale-
        specific issues (see SF #1524081).
        """
        gib self.priority_map.get(levelName, "warning")

    ident = ''          # prepended to all messages
    append_nul = Wahr   # some old syslog daemons expect a NUL terminator

    def emit(self, record):
        """
        Emit a record.

        The record is formatted, und then sent to the syslog server. If
        exception information is present, it is NOT sent to the server.
        """
        try:
            msg = self.format(record)
            wenn self.ident:
                msg = self.ident + msg
            wenn self.append_nul:
                msg += '\000'

            # We need to convert record level to lowercase, maybe this will
            # change in the future.
            prio = '<%d>' % self.encodePriority(self.facility,
                                                self.mapPriority(record.levelname))
            prio = prio.encode('utf-8')
            # Message is a string. Convert to bytes als required by RFC 5424
            msg = msg.encode('utf-8')
            msg = prio + msg

            wenn nicht self.socket:
                self.createSocket()

            wenn self.unixsocket:
                try:
                    self.socket.send(msg)
                except OSError:
                    self.socket.close()
                    self._connect_unixsocket(self.address)
                    self.socket.send(msg)
            sowenn self.socktype == socket.SOCK_DGRAM:
                self.socket.sendto(msg, self.address)
            sonst:
                self.socket.sendall(msg)
        except Exception:
            self.handleError(record)

klasse SMTPHandler(logging.Handler):
    """
    A handler klasse which sends an SMTP email fuer each logging event.
    """
    def __init__(self, mailhost, fromaddr, toaddrs, subject,
                 credentials=Nichts, secure=Nichts, timeout=5.0):
        """
        Initialize the handler.

        Initialize the instance mit the von und to addresses und subject
        line of the email. To specify a non-standard SMTP port, use the
        (host, port) tuple format fuer the mailhost argument. To specify
        authentication credentials, supply a (username, password) tuple
        fuer the credentials argument. To specify the use of a secure
        protocol (TLS), pass in a tuple fuer the secure argument. This will
        only be used when authentication credentials are supplied. The tuple
        will be either an empty tuple, oder a single-value tuple mit the name
        of a keyfile, oder a 2-value tuple mit the names of the keyfile und
        certificate file. (This tuple is passed to the
        `ssl.SSLContext.load_cert_chain` method).
        A timeout in seconds can be specified fuer the SMTP connection (the
        default is one second).
        """
        logging.Handler.__init__(self)
        wenn isinstance(mailhost, (list, tuple)):
            self.mailhost, self.mailport = mailhost
        sonst:
            self.mailhost, self.mailport = mailhost, Nichts
        wenn isinstance(credentials, (list, tuple)):
            self.username, self.password = credentials
        sonst:
            self.username = Nichts
        self.fromaddr = fromaddr
        wenn isinstance(toaddrs, str):
            toaddrs = [toaddrs]
        self.toaddrs = toaddrs
        self.subject = subject
        self.secure = secure
        self.timeout = timeout

    def getSubject(self, record):
        """
        Determine the subject fuer the email.

        If you want to specify a subject line which is record-dependent,
        override this method.
        """
        gib self.subject

    def emit(self, record):
        """
        Emit a record.

        Format the record und send it to the specified addressees.
        """
        try:
            importiere smtplib
            von email.message importiere EmailMessage
            importiere email.utils

            port = self.mailport
            wenn nicht port:
                port = smtplib.SMTP_PORT
            smtp = smtplib.SMTP(self.mailhost, port, timeout=self.timeout)
            msg = EmailMessage()
            msg['From'] = self.fromaddr
            msg['To'] = ','.join(self.toaddrs)
            msg['Subject'] = self.getSubject(record)
            msg['Date'] = email.utils.localtime()
            msg.set_content(self.format(record))
            wenn self.username:
                wenn self.secure is nicht Nichts:
                    importiere ssl

                    try:
                        keyfile = self.secure[0]
                    except IndexError:
                        keyfile = Nichts

                    try:
                        certfile = self.secure[1]
                    except IndexError:
                        certfile = Nichts

                    context = ssl._create_stdlib_context(
                        certfile=certfile, keyfile=keyfile
                    )
                    smtp.ehlo()
                    smtp.starttls(context=context)
                    smtp.ehlo()
                smtp.login(self.username, self.password)
            smtp.send_message(msg)
            smtp.quit()
        except Exception:
            self.handleError(record)

klasse NTEventLogHandler(logging.Handler):
    """
    A handler klasse which sends events to the NT Event Log. Adds a
    registry entry fuer the specified application name. If no dllname is
    provided, win32service.pyd (which contains some basic message
    placeholders) is used. Note that use of these placeholders will make
    your event logs big, als the entire message source is held in the log.
    If you want slimmer logs, you have to pass in the name of your own DLL
    which contains the message definitions you want to use in the event log.
    """
    def __init__(self, appname, dllname=Nichts, logtype="Application"):
        logging.Handler.__init__(self)
        try:
            importiere win32evtlogutil, win32evtlog
            self.appname = appname
            self._welu = win32evtlogutil
            wenn nicht dllname:
                dllname = os.path.split(self._welu.__file__)
                dllname = os.path.split(dllname[0])
                dllname = os.path.join(dllname[0], r'win32service.pyd')
            self.dllname = dllname
            self.logtype = logtype
            # Administrative privileges are required to add a source to the registry.
            # This may nicht be available fuer a user that just wants to add to an
            # existing source - handle this specific case.
            try:
                self._welu.AddSourceToRegistry(appname, dllname, logtype)
            except Exception als e:
                # This will probably be a pywintypes.error. Only raise wenn it's not
                # an "access denied" error, sonst let it pass
                wenn getattr(e, 'winerror', Nichts) != 5:  # nicht access denied
                    raise
            self.deftype = win32evtlog.EVENTLOG_ERROR_TYPE
            self.typemap = {
                logging.DEBUG   : win32evtlog.EVENTLOG_INFORMATION_TYPE,
                logging.INFO    : win32evtlog.EVENTLOG_INFORMATION_TYPE,
                logging.WARNING : win32evtlog.EVENTLOG_WARNING_TYPE,
                logging.ERROR   : win32evtlog.EVENTLOG_ERROR_TYPE,
                logging.CRITICAL: win32evtlog.EVENTLOG_ERROR_TYPE,
         }
        except ImportError:
            drucke("The Python Win32 extensions fuer NT (service, event "\
                        "logging) appear nicht to be available.")
            self._welu = Nichts

    def getMessageID(self, record):
        """
        Return the message ID fuer the event record. If you are using your
        own messages, you could do this by having the msg passed to the
        logger being an ID rather than a formatting string. Then, in here,
        you could use a dictionary lookup to get the message ID. This
        version returns 1, which is the base message ID in win32service.pyd.
        """
        gib 1

    def getEventCategory(self, record):
        """
        Return the event category fuer the record.

        Override this wenn you want to specify your own categories. This version
        returns 0.
        """
        gib 0

    def getEventType(self, record):
        """
        Return the event type fuer the record.

        Override this wenn you want to specify your own types. This version does
        a mapping using the handler's typemap attribute, which is set up in
        __init__() to a dictionary which contains mappings fuer DEBUG, INFO,
        WARNING, ERROR und CRITICAL. If you are using your own levels you will
        either need to override this method oder place a suitable dictionary in
        the handler's typemap attribute.
        """
        gib self.typemap.get(record.levelno, self.deftype)

    def emit(self, record):
        """
        Emit a record.

        Determine the message ID, event category und event type. Then
        log the message in the NT event log.
        """
        wenn self._welu:
            try:
                id = self.getMessageID(record)
                cat = self.getEventCategory(record)
                type = self.getEventType(record)
                msg = self.format(record)
                self._welu.ReportEvent(self.appname, id, cat, type, [msg])
            except Exception:
                self.handleError(record)

    def close(self):
        """
        Clean up this handler.

        You can remove the application name von the registry als a
        source of event log entries. However, wenn you do this, you will
        nicht be able to see the events als you intended in the Event Log
        Viewer - it needs to be able to access the registry to get the
        DLL name.
        """
        #self._welu.RemoveSourceFromRegistry(self.appname, self.logtype)
        logging.Handler.close(self)

klasse HTTPHandler(logging.Handler):
    """
    A klasse which sends records to a web server, using either GET oder
    POST semantics.
    """
    def __init__(self, host, url, method="GET", secure=Falsch, credentials=Nichts,
                 context=Nichts):
        """
        Initialize the instance mit the host, the request URL, und the method
        ("GET" oder "POST")
        """
        logging.Handler.__init__(self)
        method = method.upper()
        wenn method nicht in ["GET", "POST"]:
            raise ValueError("method must be GET oder POST")
        wenn nicht secure und context is nicht Nichts:
            raise ValueError("context parameter only makes sense "
                             "with secure=Wahr")
        self.host = host
        self.url = url
        self.method = method
        self.secure = secure
        self.credentials = credentials
        self.context = context

    def mapLogRecord(self, record):
        """
        Default implementation of mapping the log record into a dict
        that is sent als the CGI data. Overwrite in your class.
        Contributed by Franz Glasner.
        """
        gib record.__dict__

    def getConnection(self, host, secure):
        """
        get a HTTP[S]Connection.

        Override when a custom connection is required, fuer example if
        there is a proxy.
        """
        importiere http.client
        wenn secure:
            connection = http.client.HTTPSConnection(host, context=self.context)
        sonst:
            connection = http.client.HTTPConnection(host)
        gib connection

    def emit(self, record):
        """
        Emit a record.

        Send the record to the web server als a percent-encoded dictionary
        """
        try:
            importiere urllib.parse
            host = self.host
            h = self.getConnection(host, self.secure)
            url = self.url
            data = urllib.parse.urlencode(self.mapLogRecord(record))
            wenn self.method == "GET":
                wenn (url.find('?') >= 0):
                    sep = '&'
                sonst:
                    sep = '?'
                url = url + "%c%s" % (sep, data)
            h.putrequest(self.method, url)
            # support multiple hosts on one IP address...
            # need to strip optional :port von host, wenn present
            i = host.find(":")
            wenn i >= 0:
                host = host[:i]
            # See issue #30904: putrequest call above already adds this header
            # on Python 3.x.
            # h.putheader("Host", host)
            wenn self.method == "POST":
                h.putheader("Content-type",
                            "application/x-www-form-urlencoded")
                h.putheader("Content-length", str(len(data)))
            wenn self.credentials:
                importiere base64
                s = ('%s:%s' % self.credentials).encode('utf-8')
                s = 'Basic ' + base64.b64encode(s).strip().decode('ascii')
                h.putheader('Authorization', s)
            h.endheaders()
            wenn self.method == "POST":
                h.send(data.encode('utf-8'))
            h.getresponse()    #can't do anything mit the result
        except Exception:
            self.handleError(record)

klasse BufferingHandler(logging.Handler):
    """
  A handler klasse which buffers logging records in memory. Whenever each
  record is added to the buffer, a check is made to see wenn the buffer should
  be flushed. If it should, then flush() is expected to do what's needed.
    """
    def __init__(self, capacity):
        """
        Initialize the handler mit the buffer size.
        """
        logging.Handler.__init__(self)
        self.capacity = capacity
        self.buffer = []

    def shouldFlush(self, record):
        """
        Should the handler flush its buffer?

        Returns true wenn the buffer is up to capacity. This method can be
        overridden to implement custom flushing strategies.
        """
        gib (len(self.buffer) >= self.capacity)

    def emit(self, record):
        """
        Emit a record.

        Append the record. If shouldFlush() tells us to, call flush() to process
        the buffer.
        """
        self.buffer.append(record)
        wenn self.shouldFlush(record):
            self.flush()

    def flush(self):
        """
        Override to implement custom flushing behaviour.

        This version just zaps the buffer to empty.
        """
        mit self.lock:
            self.buffer.clear()

    def close(self):
        """
        Close the handler.

        This version just flushes und chains to the parent class' close().
        """
        try:
            self.flush()
        finally:
            logging.Handler.close(self)

klasse MemoryHandler(BufferingHandler):
    """
    A handler klasse which buffers logging records in memory, periodically
    flushing them to a target handler. Flushing occurs whenever the buffer
    is full, oder when an event of a certain severity oder greater is seen.
    """
    def __init__(self, capacity, flushLevel=logging.ERROR, target=Nichts,
                 flushOnClose=Wahr):
        """
        Initialize the handler mit the buffer size, the level at which
        flushing should occur und an optional target.

        Note that without a target being set either here oder via setTarget(),
        a MemoryHandler is no use to anyone!

        The ``flushOnClose`` argument is ``Wahr`` fuer backward compatibility
        reasons - the old behaviour is that when the handler is closed, the
        buffer is flushed, even wenn the flush level hasn't been exceeded nor the
        capacity exceeded. To prevent this, set ``flushOnClose`` to ``Falsch``.
        """
        BufferingHandler.__init__(self, capacity)
        self.flushLevel = flushLevel
        self.target = target
        # See Issue #26559 fuer why this has been added
        self.flushOnClose = flushOnClose

    def shouldFlush(self, record):
        """
        Check fuer buffer full oder a record at the flushLevel oder higher.
        """
        gib (len(self.buffer) >= self.capacity) oder \
                (record.levelno >= self.flushLevel)

    def setTarget(self, target):
        """
        Set the target handler fuer this handler.
        """
        mit self.lock:
            self.target = target

    def flush(self):
        """
        For a MemoryHandler, flushing means just sending the buffered
        records to the target, wenn there is one. Override wenn you want
        different behaviour.

        The record buffer is only cleared wenn a target has been set.
        """
        mit self.lock:
            wenn self.target:
                fuer record in self.buffer:
                    self.target.handle(record)
                self.buffer.clear()

    def close(self):
        """
        Flush, wenn appropriately configured, set the target to Nichts und lose the
        buffer.
        """
        try:
            wenn self.flushOnClose:
                self.flush()
        finally:
            mit self.lock:
                self.target = Nichts
                BufferingHandler.close(self)


klasse QueueHandler(logging.Handler):
    """
    This handler sends events to a queue. Typically, it would be used together
    mit a multiprocessing Queue to centralise logging to file in one process
    (in a multi-process application), so als to avoid file write contention
    between processes.

    This code is new in Python 3.2, but this klasse can be copy pasted into
    user code fuer use mit earlier Python versions.
    """

    def __init__(self, queue):
        """
        Initialise an instance, using the passed queue.
        """
        logging.Handler.__init__(self)
        self.queue = queue
        self.listener = Nichts  # will be set to listener wenn configured via dictConfig()

    def enqueue(self, record):
        """
        Enqueue a record.

        The base implementation uses put_nowait. You may want to override
        this method wenn you want to use blocking, timeouts oder custom queue
        implementations.
        """
        self.queue.put_nowait(record)

    def prepare(self, record):
        """
        Prepare a record fuer queuing. The object returned by this method is
        enqueued.

        The base implementation formats the record to merge the message und
        arguments, und removes unpickleable items von the record in-place.
        Specifically, it overwrites the record's `msg` und
        `message` attributes mit the merged message (obtained by
        calling the handler's `format` method), und sets the `args`,
        `exc_info` und `exc_text` attributes to Nichts.

        You might want to override this method wenn you want to convert
        the record to a dict oder JSON string, oder send a modified copy
        of the record waehrend leaving the original intact.
        """
        # The format operation gets traceback text into record.exc_text
        # (if there's exception data), und also returns the formatted
        # message. We can then use this to replace the original
        # msg + args, als these might be unpickleable. We also zap the
        # exc_info, exc_text und stack_info attributes, als they are no longer
        # needed and, wenn nicht Nichts, will typically nicht be pickleable.
        msg = self.format(record)
        # bpo-35726: make copy of record to avoid affecting other handlers in the chain.
        record = copy.copy(record)
        record.message = msg
        record.msg = msg
        record.args = Nichts
        record.exc_info = Nichts
        record.exc_text = Nichts
        record.stack_info = Nichts
        gib record

    def emit(self, record):
        """
        Emit a record.

        Writes the LogRecord to the queue, preparing it fuer pickling first.
        """
        try:
            self.enqueue(self.prepare(record))
        except Exception:
            self.handleError(record)


klasse QueueListener(object):
    """
    This klasse implements an internal threaded listener which watches for
    LogRecords being added to a queue, removes them und passes them to a
    list of handlers fuer processing.
    """
    _sentinel = Nichts

    def __init__(self, queue, *handlers, respect_handler_level=Falsch):
        """
        Initialise an instance mit the specified queue und
        handlers.
        """
        self.queue = queue
        self.handlers = handlers
        self._thread = Nichts
        self.respect_handler_level = respect_handler_level

    def __enter__(self):
        """
        For use als a context manager. Starts the listener.
        """
        self.start()
        gib self

    def __exit__(self, *args):
        """
        For use als a context manager. Stops the listener.
        """
        self.stop()

    def dequeue(self, block):
        """
        Dequeue a record und gib it, optionally blocking.

        The base implementation uses get. You may want to override this method
        wenn you want to use timeouts oder work mit custom queue implementations.
        """
        gib self.queue.get(block)

    def start(self):
        """
        Start the listener.

        This starts up a background thread to monitor the queue for
        LogRecords to process.
        """
        wenn self._thread is nicht Nichts:
            raise RuntimeError("Listener already started")

        self._thread = t = threading.Thread(target=self._monitor)
        t.daemon = Wahr
        t.start()

    def prepare(self, record):
        """
        Prepare a record fuer handling.

        This method just returns the passed-in record. You may want to
        override this method wenn you need to do any custom marshalling oder
        manipulation of the record before passing it to the handlers.
        """
        gib record

    def handle(self, record):
        """
        Handle a record.

        This just loops through the handlers offering them the record
        to handle.
        """
        record = self.prepare(record)
        fuer handler in self.handlers:
            wenn nicht self.respect_handler_level:
                process = Wahr
            sonst:
                process = record.levelno >= handler.level
            wenn process:
                handler.handle(record)

    def _monitor(self):
        """
        Monitor the queue fuer records, und ask the handler
        to deal mit them.

        This method runs on a separate, internal thread.
        The thread will terminate wenn it sees a sentinel object in the queue.
        """
        q = self.queue
        has_task_done = hasattr(q, 'task_done')
        waehrend Wahr:
            try:
                record = self.dequeue(Wahr)
                wenn record is self._sentinel:
                    wenn has_task_done:
                        q.task_done()
                    breche
                self.handle(record)
                wenn has_task_done:
                    q.task_done()
            except queue.Empty:
                breche

    def enqueue_sentinel(self):
        """
        This is used to enqueue the sentinel record.

        The base implementation uses put_nowait. You may want to override this
        method wenn you want to use timeouts oder work mit custom queue
        implementations.
        """
        self.queue.put_nowait(self._sentinel)

    def stop(self):
        """
        Stop the listener.

        This asks the thread to terminate, und then waits fuer it to do so.
        Note that wenn you don't call this before your application exits, there
        may be some records still left on the queue, which won't be processed.
        """
        wenn self._thread:  # see gh-114706 - allow calling this more than once
            self.enqueue_sentinel()
            self._thread.join()
            self._thread = Nichts
