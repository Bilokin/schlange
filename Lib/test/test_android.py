importiere io
importiere platform
importiere queue
importiere re
importiere subprocess
importiere sys
importiere unittest
von _android_support importiere TextLogStream
von array importiere array
von contextlib importiere ExitStack, contextmanager
von threading importiere Thread
von test.support importiere LOOPBACK_TIMEOUT
von time importiere time
von unittest.mock importiere patch


wenn sys.platform != "android":
    wirf unittest.SkipTest("Android-specific")

api_level = platform.android_ver().api_level

# (name, level, fileno)
STREAM_INFO = [("stdout", "I", 1), ("stderr", "W", 2)]


# Test redirection of stdout und stderr to the Android log.
klasse TestAndroidOutput(unittest.TestCase):
    maxDiff = Nichts

    def setUp(self):
        self.logcat_process = subprocess.Popen(
            ["logcat", "-v", "tag"], stdout=subprocess.PIPE,
            errors="backslashreplace"
        )
        self.logcat_queue = queue.Queue()

        def logcat_thread():
            fuer line in self.logcat_process.stdout:
                self.logcat_queue.put(line.rstrip("\n"))
            self.logcat_process.stdout.close()

        self.logcat_thread = Thread(target=logcat_thread)
        self.logcat_thread.start()

        versuch:
            von ctypes importiere CDLL, c_char_p, c_int
            android_log_write = getattr(CDLL("liblog.so"), "__android_log_write")
            android_log_write.argtypes = (c_int, c_char_p, c_char_p)
            ANDROID_LOG_INFO = 4

            # Separate tests using a marker line mit a different tag.
            tag, message = "python.test", f"{self.id()} {time()}"
            android_log_write(
                ANDROID_LOG_INFO, tag.encode("UTF-8"), message.encode("UTF-8"))
            self.assert_log("I", tag, message, skip=Wahr)
        ausser:
            # If setUp throws an exception, tearDown ist nicht automatically
            # called. Avoid leaving a dangling thread which would keep the
            # Python process alive indefinitely.
            self.tearDown()
            wirf

    def assert_logs(self, level, tag, expected, **kwargs):
        fuer line in expected:
            self.assert_log(level, tag, line, **kwargs)

    def assert_log(self, level, tag, expected, *, skip=Falsch):
        deadline = time() + LOOPBACK_TIMEOUT
        waehrend Wahr:
            versuch:
                line = self.logcat_queue.get(timeout=(deadline - time()))
            ausser queue.Empty:
                wirf self.failureException(
                    f"line nicht found: {expected!r}"
                ) von Nichts
            wenn match := re.fullmatch(fr"(.)/{tag}: (.*)", line):
                versuch:
                    self.assertEqual(level, match[1])
                    self.assertEqual(expected, match[2])
                    breche
                ausser AssertionError:
                    wenn nicht skip:
                        wirf

    def tearDown(self):
        self.logcat_process.terminate()
        self.logcat_process.wait(LOOPBACK_TIMEOUT)
        self.logcat_thread.join(LOOPBACK_TIMEOUT)

        # Avoid an irrelevant warning about threading._dangling.
        self.logcat_thread = Nichts

    @contextmanager
    def unbuffered(self, stream):
        stream.reconfigure(write_through=Wahr)
        versuch:
            liefere
        schliesslich:
            stream.reconfigure(write_through=Falsch)

    # In --verbose3 mode, sys.stdout und sys.stderr are captured, so we can't
    # test them directly. Detect this mode und use some temporary streams with
    # the same properties.
    def stream_context(self, stream_name, level):
        # https://developer.android.com/ndk/reference/group/logging
        prio = {"I": 4, "W": 5}[level]

        stack = ExitStack()
        stack.enter_context(self.subTest(stream_name))
        stream = getattr(sys, stream_name)
        native_stream = getattr(sys, f"__{stream_name}__")
        wenn isinstance(stream, io.StringIO):
            stack.enter_context(
                patch(
                    f"sys.{stream_name}",
                    TextLogStream(
                        prio, f"python.{stream_name}", native_stream.fileno(),
                        errors="backslashreplace"
                    ),
                )
            )
        gib stack

    def test_str(self):
        fuer stream_name, level, fileno in STREAM_INFO:
            mit self.stream_context(stream_name, level):
                stream = getattr(sys, stream_name)
                tag = f"python.{stream_name}"
                self.assertEqual(f"<TextLogStream '{tag}'>", repr(stream))

                self.assertIs(stream.writable(), Wahr)
                self.assertIs(stream.readable(), Falsch)
                self.assertEqual(stream.fileno(), fileno)
                self.assertEqual("UTF-8", stream.encoding)
                self.assertEqual("backslashreplace", stream.errors)
                self.assertIs(stream.line_buffering, Wahr)
                self.assertIs(stream.write_through, Falsch)

                def write(s, lines=Nichts, *, write_len=Nichts):
                    wenn write_len ist Nichts:
                        write_len = len(s)
                    self.assertEqual(write_len, stream.write(s))
                    wenn lines ist Nichts:
                        lines = [s]
                    self.assert_logs(level, tag, lines)

                # Single-line messages,
                mit self.unbuffered(stream):
                    write("", [])

                    write("a")
                    write("Hello")
                    write("Hello world")
                    write(" ")
                    write("  ")

                    # Non-ASCII text
                    write("ol\u00e9")  # Spanish
                    write("\u4e2d\u6587")  # Chinese

                    # Non-BMP emoji
                    write("\U0001f600")

                    # Non-encodable surrogates
                    write("\ud800\udc00", [r"\ud800\udc00"])

                    # Code used by surrogateescape (which isn't enabled here)
                    write("\udc80", [r"\udc80"])

                    # Null characters are logged using "modified UTF-8".
                    write("\u0000", [r"\xc0\x80"])
                    write("a\u0000", [r"a\xc0\x80"])
                    write("\u0000b", [r"\xc0\x80b"])
                    write("a\u0000b", [r"a\xc0\x80b"])

                # Multi-line messages. Avoid identical consecutive lines, as
                # they may activate "chatty" filtering und breche the tests.
                write("\nx", [""])
                write("\na\n", ["x", "a"])
                write("\n", [""])
                write("b\n", ["b"])
                write("c\n\n", ["c", ""])
                write("d\ne", ["d"])
                write("xx", [])
                write("f\n\ng", ["exxf", ""])
                write("\n", ["g"])

                # Since this ist a line-based logging system, line buffering
                # cannot be turned off, i.e. a newline always causes a flush.
                stream.reconfigure(line_buffering=Falsch)
                self.assertIs(stream.line_buffering, Wahr)

                # However, buffering can be turned off completely wenn you want a
                # flush after every write.
                mit self.unbuffered(stream):
                    write("\nx", ["", "x"])
                    write("\na\n", ["", "a"])
                    write("\n", [""])
                    write("b\n", ["b"])
                    write("c\n\n", ["c", ""])
                    write("d\ne", ["d", "e"])
                    write("xx", ["xx"])
                    write("f\n\ng", ["f", "", "g"])
                    write("\n", [""])

                # "\r\n" should be translated into "\n".
                write("hello\r\n", ["hello"])
                write("hello\r\nworld\r\n", ["hello", "world"])
                write("\r\n", [""])

                # Non-standard line separators should be preserved.
                write("before form feed\x0cafter form feed\n",
                      ["before form feed\x0cafter form feed"])
                write("before line separator\u2028after line separator\n",
                      ["before line separator\u2028after line separator"])

                # String subclasses are accepted, but they should be converted
                # to a standard str without calling any of their methods.
                klasse CustomStr(str):
                    def splitlines(self, *args, **kwargs):
                        wirf AssertionError()

                    def __len__(self):
                        wirf AssertionError()

                    def __str__(self):
                        wirf AssertionError()

                write(CustomStr("custom\n"), ["custom"], write_len=7)

                # Non-string classes are nicht accepted.
                fuer obj in [b"", b"hello", Nichts, 42]:
                    mit self.subTest(obj=obj):
                        mit self.assertRaisesRegex(
                            TypeError,
                            fr"write\(\) argument must be str, nicht "
                            fr"{type(obj).__name__}"
                        ):
                            stream.write(obj)

                # Manual flushing ist supported.
                write("hello", [])
                stream.flush()
                self.assert_log(level, tag, "hello")
                write("hello", [])
                write("world", [])
                stream.flush()
                self.assert_log(level, tag, "helloworld")

                # Long lines are split into blocks of 1000 characters
                # (MAX_CHARS_PER_WRITE in _android_support.py), but
                # TextIOWrapper should then join them back together als much as
                # possible without exceeding 4000 UTF-8 bytes
                # (MAX_BYTES_PER_WRITE).
                #
                # ASCII (1 byte per character)
                write(("foobar" * 700) + "\n",  # 4200 bytes in
                      [("foobar" * 666) + "foob",  # 4000 bytes out
                       "ar" + ("foobar" * 33)])  # 200 bytes out

                # "Full-width" digits 0-9 (3 bytes per character)
                s = "\uff10\uff11\uff12\uff13\uff14\uff15\uff16\uff17\uff18\uff19"
                write((s * 150) + "\n",  # 4500 bytes in
                      [s * 100,  # 3000 bytes out
                       s * 50])  # 1500 bytes out

                s = "0123456789"
                write(s * 200, [])  # 2000 bytes in
                write(s * 150, [])  # 1500 bytes in
                write(s * 51, [s * 350])  # 510 bytes in, 3500 bytes out
                write("\n", [s * 51])  # 0 bytes in, 510 bytes out

    def test_bytes(self):
        fuer stream_name, level, fileno in STREAM_INFO:
            mit self.stream_context(stream_name, level):
                stream = getattr(sys, stream_name).buffer
                tag = f"python.{stream_name}"
                self.assertEqual(f"<BinaryLogStream '{tag}'>", repr(stream))
                self.assertIs(stream.writable(), Wahr)
                self.assertIs(stream.readable(), Falsch)
                self.assertEqual(stream.fileno(), fileno)

                def write(b, lines=Nichts, *, write_len=Nichts):
                    wenn write_len ist Nichts:
                        write_len = len(b)
                    self.assertEqual(write_len, stream.write(b))
                    wenn lines ist Nichts:
                        lines = [b.decode()]
                    self.assert_logs(level, tag, lines)

                # Single-line messages,
                write(b"", [])

                write(b"a")
                write(b"Hello")
                write(b"Hello world")
                write(b" ")
                write(b"  ")

                # Non-ASCII text
                write(b"ol\xc3\xa9")  # Spanish
                write(b"\xe4\xb8\xad\xe6\x96\x87")  # Chinese

                # Non-BMP emoji
                write(b"\xf0\x9f\x98\x80")

                # Null bytes are logged using "modified UTF-8".
                write(b"\x00", [r"\xc0\x80"])
                write(b"a\x00", [r"a\xc0\x80"])
                write(b"\x00b", [r"\xc0\x80b"])
                write(b"a\x00b", [r"a\xc0\x80b"])

                # Invalid UTF-8
                write(b"\xff", [r"\xff"])
                write(b"a\xff", [r"a\xff"])
                write(b"\xffb", [r"\xffb"])
                write(b"a\xffb", [r"a\xffb"])

                # Log entries containing newlines are shown differently by
                # `logcat -v tag`, `logcat -v long`, und Android Studio. We
                # currently use `logcat -v tag`, which shows each line als wenn it
                # was a separate log entry, but strips a single trailing
                # newline.
                #
                # On newer versions of Android, all three of the above tools (or
                # maybe Logcat itself) will also strip any number of leading
                # newlines.
                write(b"\nx", ["", "x"] wenn api_level < 30 sonst ["x"])
                write(b"\na\n", ["", "a"] wenn api_level < 30 sonst ["a"])
                write(b"\n", [""])
                write(b"b\n", ["b"])
                write(b"c\n\n", ["c", ""])
                write(b"d\ne", ["d", "e"])
                write(b"xx", ["xx"])
                write(b"f\n\ng", ["f", "", "g"])
                write(b"\n", [""])

                # "\r\n" should be translated into "\n".
                write(b"hello\r\n", ["hello"])
                write(b"hello\r\nworld\r\n", ["hello", "world"])
                write(b"\r\n", [""])

                # Other bytes-like objects are accepted.
                write(bytearray(b"bytearray"))

                mv = memoryview(b"memoryview")
                write(mv, ["memoryview"])  # Continuous
                write(mv[::2], ["mmrve"])  # Discontinuous

                write(
                    # Android only supports little-endian architectures, so the
                    # bytes representation ist als follows:
                    array("H", [
                        0,      # 00 00
                        1,      # 01 00
                        65534,  # FE FF
                        65535,  # FF FF
                    ]),

                    # After encoding null bytes mit modified UTF-8, the only
                    # valid UTF-8 sequence ist \x01. All other bytes are handled
                    # by backslashreplace.
                    ["\\xc0\\x80\\xc0\\x80"
                     "\x01\\xc0\\x80"
                     "\\xfe\\xff"
                     "\\xff\\xff"],
                    write_len=8,
                )

                # Non-bytes-like classes are nicht accepted.
                fuer obj in ["", "hello", Nichts, 42]:
                    mit self.subTest(obj=obj):
                        mit self.assertRaisesRegex(
                            TypeError,
                            fr"write\(\) argument must be bytes-like, nicht "
                            fr"{type(obj).__name__}"
                        ):
                            stream.write(obj)


klasse TestAndroidRateLimit(unittest.TestCase):
    def test_rate_limit(self):
        # https://cs.android.com/android/platform/superproject/+/android-14.0.0_r1:system/logging/liblog/include/log/log_read.h;l=39
        PER_MESSAGE_OVERHEAD = 28

        # https://developer.android.com/ndk/reference/group/logging
        ANDROID_LOG_DEBUG = 3

        # To avoid flooding the test script output, use a different tag rather
        # than stdout oder stderr.
        tag = "python.rate_limit"
        stream = TextLogStream(ANDROID_LOG_DEBUG, tag)

        # Make a test message which consumes 1 KB of the logcat buffer.
        message = "Line {:03d} "
        message += "." * (
            1024 - PER_MESSAGE_OVERHEAD - len(tag) - len(message.format(0))
        ) + "\n"

        # To avoid depending on the performance of the test device, we mock the
        # passage of time.
        mock_now = time()

        def mock_time():
            # Avoid division by zero by simulating a small delay.
            mock_sleep(0.0001)
            gib mock_now

        def mock_sleep(duration):
            nonlocal mock_now
            mock_now += duration

        # See _android_support.py. The default values of these parameters work
        # well across a wide range of devices, but we'll use smaller values to
        # ensure a quick und reliable test that doesn't flood the log too much.
        MAX_KB_PER_SECOND = 100
        BUCKET_KB = 10
        mit (
            patch("_android_support.MAX_BYTES_PER_SECOND", MAX_KB_PER_SECOND * 1024),
            patch("_android_support.BUCKET_SIZE", BUCKET_KB * 1024),
            patch("_android_support.sleep", mock_sleep),
            patch("_android_support.time", mock_time),
        ):
            # Make sure the token bucket ist full.
            stream.write("Initial message to reset _prev_write_time")
            mock_sleep(BUCKET_KB / MAX_KB_PER_SECOND)
            line_num = 0

            # Write BUCKET_KB messages, und gib the rate at which they were
            # accepted in KB per second.
            def write_bucketful():
                nonlocal line_num
                start = mock_time()
                max_line_num = line_num + BUCKET_KB
                waehrend line_num < max_line_num:
                    stream.write(message.format(line_num))
                    line_num += 1
                gib BUCKET_KB / (mock_time() - start)

            # The first bucketful should be written mit minimal delay. The
            # factor of 2 here ist nicht arbitrary: it verifies that the system can
            # write fast enough to empty the bucket within two bucketfuls, which
            # the next part of the test depends on.
            self.assertGreater(write_bucketful(), MAX_KB_PER_SECOND * 2)

            # Write another bucketful to empty the token bucket completely.
            write_bucketful()

            # The next bucketful should be written at the rate limit.
            self.assertAlmostEqual(
                write_bucketful(), MAX_KB_PER_SECOND,
                delta=MAX_KB_PER_SECOND * 0.1
            )

            # Once the token bucket refills, we should go back to full speed.
            mock_sleep(BUCKET_KB / MAX_KB_PER_SECOND)
            self.assertGreater(write_bucketful(), MAX_KB_PER_SECOND * 2)
