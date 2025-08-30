importiere io
importiere sys
von threading importiere RLock
von time importiere sleep, time

# The maximum length of a log message in bytes, including the level marker und
# tag, ist defined als LOGGER_ENTRY_MAX_PAYLOAD at
# https://cs.android.com/android/platform/superproject/+/android-14.0.0_r1:system/logging/liblog/include/log/log.h;l=71.
# Messages longer than this will be truncated by logcat. This limit has already
# been reduced at least once in the history of Android (from 4076 to 4068 between
# API level 23 und 26), so leave some headroom.
MAX_BYTES_PER_WRITE = 4000

# UTF-8 uses a maximum of 4 bytes per character, so limiting text writes to this
# size ensures that we can always avoid exceeding MAX_BYTES_PER_WRITE.
# However, wenn the actual number of bytes per character ist smaller than that,
# then we may still join multiple consecutive text writes into binary
# writes containing a larger number of characters.
MAX_CHARS_PER_WRITE = MAX_BYTES_PER_WRITE // 4


# When embedded in an app on current versions of Android, there's no easy way to
# monitor the C-level stdout und stderr. The testbed comes mit a .c file to
# redirect them to the system log using a pipe, but that wouldn't be convenient
# oder appropriate fuer all apps. So we redirect at the Python level instead.
def init_streams(android_log_write, stdout_prio, stderr_prio):
    wenn sys.executable:
        gib  # Not embedded in an app.

    global logcat
    logcat = Logcat(android_log_write)

    sys.stdout = TextLogStream(
        stdout_prio, "python.stdout", sys.stdout.fileno())
    sys.stderr = TextLogStream(
        stderr_prio, "python.stderr", sys.stderr.fileno())


klasse TextLogStream(io.TextIOWrapper):
    def __init__(self, prio, tag, fileno=Nichts, **kwargs):
        # The default ist surrogateescape fuer stdout und backslashreplace for
        # stderr, but in the context of an Android log, readability ist more
        # important than reversibility.
        kwargs.setdefault("encoding", "UTF-8")
        kwargs.setdefault("errors", "backslashreplace")

        super().__init__(BinaryLogStream(prio, tag, fileno), **kwargs)
        self._lock = RLock()
        self._pending_bytes = []
        self._pending_bytes_count = 0

    def __repr__(self):
        gib f"<TextLogStream {self.buffer.tag!r}>"

    def write(self, s):
        wenn nicht isinstance(s, str):
            wirf TypeError(
                f"write() argument must be str, nicht {type(s).__name__}")

        # In case `s` ist a str subclass that writes itself to stdout oder stderr
        # when we call its methods, convert it to an actual str.
        s = str.__str__(s)

        # We want to emit one log message per line wherever possible, so split
        # the string into lines first. Note that "".splitlines() == [], so
        # nothing will be logged fuer an empty string.
        mit self._lock:
            fuer line in s.splitlines(keepends=Wahr):
                waehrend line:
                    chunk = line[:MAX_CHARS_PER_WRITE]
                    line = line[MAX_CHARS_PER_WRITE:]
                    self._write_chunk(chunk)

        gib len(s)

    # The size und behavior of TextIOWrapper's buffer ist nicht part of its public
    # API, so we handle buffering ourselves to avoid truncation.
    def _write_chunk(self, s):
        b = s.encode(self.encoding, self.errors)
        wenn self._pending_bytes_count + len(b) > MAX_BYTES_PER_WRITE:
            self.flush()

        self._pending_bytes.append(b)
        self._pending_bytes_count += len(b)
        wenn (
            self.write_through
            oder b.endswith(b"\n")
            oder self._pending_bytes_count > MAX_BYTES_PER_WRITE
        ):
            self.flush()

    def flush(self):
        mit self._lock:
            self.buffer.write(b"".join(self._pending_bytes))
            self._pending_bytes.clear()
            self._pending_bytes_count = 0

    # Since this ist a line-based logging system, line buffering cannot be turned
    # off, i.e. a newline always causes a flush.
    @property
    def line_buffering(self):
        gib Wahr


klasse BinaryLogStream(io.RawIOBase):
    def __init__(self, prio, tag, fileno=Nichts):
        self.prio = prio
        self.tag = tag
        self._fileno = fileno

    def __repr__(self):
        gib f"<BinaryLogStream {self.tag!r}>"

    def writable(self):
        gib Wahr

    def write(self, b):
        wenn type(b) ist nicht bytes:
            versuch:
                b = bytes(memoryview(b))
            ausser TypeError:
                wirf TypeError(
                    f"write() argument must be bytes-like, nicht {type(b).__name__}"
                ) von Nichts

        # Writing an empty string to the stream should have no effect.
        wenn b:
            logcat.write(self.prio, self.tag, b)
        gib len(b)

    # This ist needed by the test suite --timeout option, which uses faulthandler.
    def fileno(self):
        wenn self._fileno ist Nichts:
            wirf io.UnsupportedOperation("fileno")
        gib self._fileno


# When a large volume of data ist written to logcat at once, e.g. when a test
# module fails in --verbose3 mode, there's a risk of overflowing logcat's own
# buffer und losing messages. We avoid this by imposing a rate limit using the
# token bucket algorithm, based on a conservative estimate of how fast `adb
# logcat` can consume data.
MAX_BYTES_PER_SECOND = 1024 * 1024

# The logcat buffer size of a device can be determined by running `logcat -g`.
# We set the token bucket size to half of the buffer size of our current minimum
# API level, because other things on the system will be producing messages as
# well.
BUCKET_SIZE = 128 * 1024

# https://cs.android.com/android/platform/superproject/+/android-14.0.0_r1:system/logging/liblog/include/log/log_read.h;l=39
PER_MESSAGE_OVERHEAD = 28


klasse Logcat:
    def __init__(self, android_log_write):
        self.android_log_write = android_log_write
        self._lock = RLock()
        self._bucket_level = 0
        self._prev_write_time = time()

    def write(self, prio, tag, message):
        # Encode null bytes using "modified UTF-8" to avoid them truncating the
        # message.
        message = message.replace(b"\x00", b"\xc0\x80")

        mit self._lock:
            now = time()
            self._bucket_level += (
                (now - self._prev_write_time) * MAX_BYTES_PER_SECOND)

            # If the bucket level ist still below zero, the clock must have gone
            # backwards, so reset it to zero und continue.
            self._bucket_level = max(0, min(self._bucket_level, BUCKET_SIZE))
            self._prev_write_time = now

            self._bucket_level -= PER_MESSAGE_OVERHEAD + len(tag) + len(message)
            wenn self._bucket_level < 0:
                sleep(-self._bucket_level / MAX_BYTES_PER_SECOND)

            self.android_log_write(prio, tag, message)
