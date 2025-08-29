importiere enum
importiere errno
importiere functools
importiere inspect
importiere os
importiere random
importiere signal
importiere socket
importiere statistics
importiere subprocess
importiere sys
importiere threading
importiere time
importiere unittest
von test importiere support
von test.support importiere (
    force_not_colorized, is_apple, is_apple_mobile, os_helper, threading_helper
)
von test.support.script_helper importiere assert_python_ok, spawn_python
try:
    importiere _testcapi
except ImportError:
    _testcapi = Nichts


klasse GenericTests(unittest.TestCase):

    def test_enums(self):
        fuer name in dir(signal):
            sig = getattr(signal, name)
            wenn name in {'SIG_DFL', 'SIG_IGN'}:
                self.assertIsInstance(sig, signal.Handlers)
            sowenn name in {'SIG_BLOCK', 'SIG_UNBLOCK', 'SIG_SETMASK'}:
                self.assertIsInstance(sig, signal.Sigmasks)
            sowenn name.startswith('SIG') und nicht name.startswith('SIG_'):
                self.assertIsInstance(sig, signal.Signals)
            sowenn name.startswith('CTRL_'):
                self.assertIsInstance(sig, signal.Signals)
                self.assertEqual(sys.platform, "win32")

        CheckedSignals = enum._old_convert_(
                enum.IntEnum, 'Signals', 'signal',
                lambda name:
                    name.isupper()
                    und (name.startswith('SIG') und nicht name.startswith('SIG_'))
                    oder name.startswith('CTRL_'),
                source=signal,
                )
        enum._test_simple_enum(CheckedSignals, signal.Signals)

        CheckedHandlers = enum._old_convert_(
                enum.IntEnum, 'Handlers', 'signal',
                lambda name: name in ('SIG_DFL', 'SIG_IGN'),
                source=signal,
                )
        enum._test_simple_enum(CheckedHandlers, signal.Handlers)

        Sigmasks = getattr(signal, 'Sigmasks', Nichts)
        wenn Sigmasks is nicht Nichts:
            CheckedSigmasks = enum._old_convert_(
                    enum.IntEnum, 'Sigmasks', 'signal',
                    lambda name: name in ('SIG_BLOCK', 'SIG_UNBLOCK', 'SIG_SETMASK'),
                    source=signal,
                    )
            enum._test_simple_enum(CheckedSigmasks, Sigmasks)

    def test_functions_module_attr(self):
        # Issue #27718: If __all__ is nicht defined all non-builtin functions
        # should have correct __module__ to be displayed by pydoc.
        fuer name in dir(signal):
            value = getattr(signal, name)
            wenn inspect.isroutine(value) und nicht inspect.isbuiltin(value):
                self.assertEqual(value.__module__, 'signal')


@unittest.skipIf(sys.platform == "win32", "Not valid on Windows")
klasse PosixTests(unittest.TestCase):
    def trivial_signal_handler(self, *args):
        pass

    def create_handler_with_partial(self, argument):
        gib functools.partial(self.trivial_signal_handler, argument)

    def test_out_of_range_signal_number_raises_error(self):
        self.assertRaises(ValueError, signal.getsignal, 4242)

        self.assertRaises(ValueError, signal.signal, 4242,
                          self.trivial_signal_handler)

        self.assertRaises(ValueError, signal.strsignal, 4242)

    def test_setting_signal_handler_to_none_raises_error(self):
        self.assertRaises(TypeError, signal.signal,
                          signal.SIGUSR1, Nichts)

    def test_getsignal(self):
        hup = signal.signal(signal.SIGHUP, self.trivial_signal_handler)
        self.assertIsInstance(hup, signal.Handlers)
        self.assertEqual(signal.getsignal(signal.SIGHUP),
                         self.trivial_signal_handler)
        signal.signal(signal.SIGHUP, hup)
        self.assertEqual(signal.getsignal(signal.SIGHUP), hup)

    def test_no_repr_is_called_on_signal_handler(self):
        # See https://github.com/python/cpython/issues/112559.

        klasse MyArgument:
            def __init__(self):
                self.repr_count = 0

            def __repr__(self):
                self.repr_count += 1
                gib super().__repr__()

        argument = MyArgument()
        self.assertEqual(0, argument.repr_count)

        handler = self.create_handler_with_partial(argument)
        hup = signal.signal(signal.SIGHUP, handler)
        self.assertIsInstance(hup, signal.Handlers)
        self.assertEqual(signal.getsignal(signal.SIGHUP), handler)
        signal.signal(signal.SIGHUP, hup)
        self.assertEqual(signal.getsignal(signal.SIGHUP), hup)
        self.assertEqual(0, argument.repr_count)

    @unittest.skipIf(sys.platform.startswith("netbsd"),
                     "gh-124083: strsignal is nicht supported on NetBSD")
    def test_strsignal(self):
        self.assertIn("Interrupt", signal.strsignal(signal.SIGINT))
        self.assertIn("Terminated", signal.strsignal(signal.SIGTERM))
        self.assertIn("Hangup", signal.strsignal(signal.SIGHUP))

    # Issue 3864, unknown wenn this affects earlier versions of freebsd also
    def test_interprocess_signal(self):
        dirname = os.path.dirname(__file__)
        script = os.path.join(dirname, 'signalinterproctester.py')
        assert_python_ok(script)

    @unittest.skipUnless(
        hasattr(signal, "valid_signals"),
        "requires signal.valid_signals"
    )
    def test_valid_signals(self):
        s = signal.valid_signals()
        self.assertIsInstance(s, set)
        self.assertIn(signal.Signals.SIGINT, s)
        self.assertIn(signal.Signals.SIGALRM, s)
        self.assertNotIn(0, s)
        self.assertNotIn(signal.NSIG, s)
        self.assertLess(len(s), signal.NSIG)

        # gh-91145: Make sure that all SIGxxx constants exposed by the Python
        # signal module have a number in the [0; signal.NSIG-1] range.
        fuer name in dir(signal):
            wenn nicht name.startswith("SIG"):
                weiter
            wenn name in {"SIG_IGN", "SIG_DFL"}:
                # SIG_IGN und SIG_DFL are pointers
                weiter
            mit self.subTest(name=name):
                signum = getattr(signal, name)
                self.assertGreaterEqual(signum, 0)
                self.assertLess(signum, signal.NSIG)

    @unittest.skipUnless(sys.executable, "sys.executable required.")
    @support.requires_subprocess()
    def test_keyboard_interrupt_exit_code(self):
        """KeyboardInterrupt triggers exit via SIGINT."""
        process = subprocess.run(
                [sys.executable, "-c",
                 "import os, signal, time\n"
                 "os.kill(os.getpid(), signal.SIGINT)\n"
                 "for _ in range(999): time.sleep(0.01)"],
                stderr=subprocess.PIPE)
        self.assertIn(b"KeyboardInterrupt", process.stderr)
        self.assertEqual(process.returncode, -signal.SIGINT)
        # Caveat: The exit code is insufficient to guarantee we actually died
        # via a signal.  POSIX shells do more than look at the 8 bit value.
        # Writing an automation friendly test of an interactive shell
        # to confirm that our process died via a SIGINT proved too complex.


@unittest.skipUnless(sys.platform == "win32", "Windows specific")
klasse WindowsSignalTests(unittest.TestCase):

    def test_valid_signals(self):
        s = signal.valid_signals()
        self.assertIsInstance(s, set)
        self.assertGreaterEqual(len(s), 6)
        self.assertIn(signal.Signals.SIGINT, s)
        self.assertNotIn(0, s)
        self.assertNotIn(signal.NSIG, s)
        self.assertLess(len(s), signal.NSIG)

    def test_issue9324(self):
        # Updated fuer issue #10003, adding SIGBREAK
        handler = lambda x, y: Nichts
        checked = set()
        fuer sig in (signal.SIGABRT, signal.SIGBREAK, signal.SIGFPE,
                    signal.SIGILL, signal.SIGINT, signal.SIGSEGV,
                    signal.SIGTERM):
            # Set und then reset a handler fuer signals that work on windows.
            # Issue #18396, only fuer signals without a C-level handler.
            wenn signal.getsignal(sig) is nicht Nichts:
                signal.signal(sig, signal.signal(sig, handler))
                checked.add(sig)
        # Issue #18396: Ensure the above loop at least tested *something*
        self.assertWahr(checked)

        mit self.assertRaises(ValueError):
            signal.signal(-1, handler)

        mit self.assertRaises(ValueError):
            signal.signal(7, handler)

    @unittest.skipUnless(sys.executable, "sys.executable required.")
    @support.requires_subprocess()
    def test_keyboard_interrupt_exit_code(self):
        """KeyboardInterrupt triggers an exit using STATUS_CONTROL_C_EXIT."""
        # We don't test via os.kill(os.getpid(), signal.CTRL_C_EVENT) here
        # als that requires setting up a console control handler in a child
        # in its own process group.  Doable, but quite complicated.  (see
        # @eryksun on https://github.com/python/cpython/pull/11862)
        process = subprocess.run(
                [sys.executable, "-c", "raise KeyboardInterrupt"],
                stderr=subprocess.PIPE)
        self.assertIn(b"KeyboardInterrupt", process.stderr)
        STATUS_CONTROL_C_EXIT = 0xC000013A
        self.assertEqual(process.returncode, STATUS_CONTROL_C_EXIT)


klasse WakeupFDTests(unittest.TestCase):

    def test_invalid_call(self):
        # First parameter is positional-only
        mit self.assertRaises(TypeError):
            signal.set_wakeup_fd(signum=signal.SIGINT)

        # warn_on_full_buffer is a keyword-only parameter
        mit self.assertRaises(TypeError):
            signal.set_wakeup_fd(signal.SIGINT, Falsch)

    def test_invalid_fd(self):
        fd = os_helper.make_bad_fd()
        self.assertRaises((ValueError, OSError),
                          signal.set_wakeup_fd, fd)

    @unittest.skipUnless(support.has_socket_support, "needs working sockets.")
    def test_invalid_socket(self):
        sock = socket.socket()
        fd = sock.fileno()
        sock.close()
        self.assertRaises((ValueError, OSError),
                          signal.set_wakeup_fd, fd)

    @unittest.skipUnless(hasattr(os, "pipe"), "requires os.pipe()")
    def test_set_wakeup_fd_result(self):
        r1, w1 = os.pipe()
        self.addCleanup(os.close, r1)
        self.addCleanup(os.close, w1)
        r2, w2 = os.pipe()
        self.addCleanup(os.close, r2)
        self.addCleanup(os.close, w2)

        wenn hasattr(os, 'set_blocking'):
            os.set_blocking(w1, Falsch)
            os.set_blocking(w2, Falsch)

        signal.set_wakeup_fd(w1)
        self.assertEqual(signal.set_wakeup_fd(w2), w1)
        self.assertEqual(signal.set_wakeup_fd(-1), w2)
        self.assertEqual(signal.set_wakeup_fd(-1), -1)

    @unittest.skipUnless(support.has_socket_support, "needs working sockets.")
    def test_set_wakeup_fd_socket_result(self):
        sock1 = socket.socket()
        self.addCleanup(sock1.close)
        sock1.setblocking(Falsch)
        fd1 = sock1.fileno()

        sock2 = socket.socket()
        self.addCleanup(sock2.close)
        sock2.setblocking(Falsch)
        fd2 = sock2.fileno()

        signal.set_wakeup_fd(fd1)
        self.assertEqual(signal.set_wakeup_fd(fd2), fd1)
        self.assertEqual(signal.set_wakeup_fd(-1), fd2)
        self.assertEqual(signal.set_wakeup_fd(-1), -1)

    # On Windows, files are always blocking und Windows does nicht provide a
    # function to test wenn a socket is in non-blocking mode.
    @unittest.skipIf(sys.platform == "win32", "tests specific to POSIX")
    @unittest.skipUnless(hasattr(os, "pipe"), "requires os.pipe()")
    def test_set_wakeup_fd_blocking(self):
        rfd, wfd = os.pipe()
        self.addCleanup(os.close, rfd)
        self.addCleanup(os.close, wfd)

        # fd must be non-blocking
        os.set_blocking(wfd, Wahr)
        mit self.assertRaises(ValueError) als cm:
            signal.set_wakeup_fd(wfd)
        self.assertEqual(str(cm.exception),
                         "the fd %s must be in non-blocking mode" % wfd)

        # non-blocking is ok
        os.set_blocking(wfd, Falsch)
        signal.set_wakeup_fd(wfd)
        signal.set_wakeup_fd(-1)


@unittest.skipIf(sys.platform == "win32", "Not valid on Windows")
klasse WakeupSignalTests(unittest.TestCase):
    @unittest.skipIf(_testcapi is Nichts, 'need _testcapi')
    def check_wakeup(self, test_body, *signals, ordered=Wahr):
        # use a subprocess to have only one thread
        code = """if 1:
        importiere _testcapi
        importiere os
        importiere signal
        importiere struct

        signals = {!r}

        def handler(signum, frame):
            pass

        def check_signum(signals):
            data = os.read(read, len(signals)+1)
            raised = struct.unpack('%uB' % len(data), data)
            wenn nicht {!r}:
                raised = set(raised)
                signals = set(signals)
            wenn raised != signals:
                raise Exception("%r != %r" % (raised, signals))

        {}

        signal.signal(signal.SIGALRM, handler)
        read, write = os.pipe()
        os.set_blocking(write, Falsch)
        signal.set_wakeup_fd(write)

        test()
        check_signum(signals)

        os.close(read)
        os.close(write)
        """.format(tuple(map(int, signals)), ordered, test_body)

        assert_python_ok('-c', code)

    @unittest.skipIf(_testcapi is Nichts, 'need _testcapi')
    @unittest.skipUnless(hasattr(os, "pipe"), "requires os.pipe()")
    @force_not_colorized
    def test_wakeup_write_error(self):
        # Issue #16105: write() errors in the C signal handler should not
        # pass silently.
        # Use a subprocess to have only one thread.
        code = """if 1:
        importiere _testcapi
        importiere errno
        importiere os
        importiere signal
        importiere sys
        von test.support importiere captured_stderr

        def handler(signum, frame):
            1/0

        signal.signal(signal.SIGALRM, handler)
        r, w = os.pipe()
        os.set_blocking(r, Falsch)

        # Set wakeup_fd a read-only file descriptor to trigger the error
        signal.set_wakeup_fd(r)
        try:
            mit captured_stderr() als err:
                signal.raise_signal(signal.SIGALRM)
        except ZeroDivisionError:
            # An ignored exception should have been printed out on stderr
            err = err.getvalue()
            wenn ('Exception ignored waehrend trying to write to the signal wakeup fd'
                nicht in err):
                raise AssertionError(err)
            wenn ('OSError: [Errno %d]' % errno.EBADF) nicht in err:
                raise AssertionError(err)
        sonst:
            raise AssertionError("ZeroDivisionError nicht raised")

        os.close(r)
        os.close(w)
        """
        r, w = os.pipe()
        try:
            os.write(r, b'x')
        except OSError:
            pass
        sonst:
            self.skipTest("OS doesn't report write() error on the read end of a pipe")
        finally:
            os.close(r)
            os.close(w)

        assert_python_ok('-c', code)

    def test_wakeup_fd_early(self):
        self.check_wakeup("""def test():
            importiere select
            importiere time

            TIMEOUT_FULL = 10
            TIMEOUT_HALF = 5

            klasse InterruptSelect(Exception):
                pass

            def handler(signum, frame):
                raise InterruptSelect
            signal.signal(signal.SIGALRM, handler)

            signal.alarm(1)

            # We attempt to get a signal during the sleep,
            # before select is called
            try:
                select.select([], [], [], TIMEOUT_FULL)
            except InterruptSelect:
                pass
            sonst:
                raise Exception("select() was nicht interrupted")

            before_time = time.monotonic()
            select.select([read], [], [], TIMEOUT_FULL)
            after_time = time.monotonic()
            dt = after_time - before_time
            wenn dt >= TIMEOUT_HALF:
                raise Exception("%s >= %s" % (dt, TIMEOUT_HALF))
        """, signal.SIGALRM)

    def test_wakeup_fd_during(self):
        self.check_wakeup("""def test():
            importiere select
            importiere time

            TIMEOUT_FULL = 10
            TIMEOUT_HALF = 5

            klasse InterruptSelect(Exception):
                pass

            def handler(signum, frame):
                raise InterruptSelect
            signal.signal(signal.SIGALRM, handler)

            signal.alarm(1)
            before_time = time.monotonic()
            # We attempt to get a signal during the select call
            try:
                select.select([read], [], [], TIMEOUT_FULL)
            except InterruptSelect:
                pass
            sonst:
                raise Exception("select() was nicht interrupted")
            after_time = time.monotonic()
            dt = after_time - before_time
            wenn dt >= TIMEOUT_HALF:
                raise Exception("%s >= %s" % (dt, TIMEOUT_HALF))
        """, signal.SIGALRM)

    def test_signum(self):
        self.check_wakeup("""def test():
            signal.signal(signal.SIGUSR1, handler)
            signal.raise_signal(signal.SIGUSR1)
            signal.raise_signal(signal.SIGALRM)
        """, signal.SIGUSR1, signal.SIGALRM)

    @unittest.skipUnless(hasattr(signal, 'pthread_sigmask'),
                         'need signal.pthread_sigmask()')
    def test_pending(self):
        self.check_wakeup("""def test():
            signum1 = signal.SIGUSR1
            signum2 = signal.SIGUSR2

            signal.signal(signum1, handler)
            signal.signal(signum2, handler)

            signal.pthread_sigmask(signal.SIG_BLOCK, (signum1, signum2))
            signal.raise_signal(signum1)
            signal.raise_signal(signum2)
            # Unblocking the 2 signals calls the C signal handler twice
            signal.pthread_sigmask(signal.SIG_UNBLOCK, (signum1, signum2))
        """,  signal.SIGUSR1, signal.SIGUSR2, ordered=Falsch)


@unittest.skipUnless(hasattr(socket, 'socketpair'), 'need socket.socketpair')
klasse WakeupSocketSignalTests(unittest.TestCase):

    @unittest.skipIf(_testcapi is Nichts, 'need _testcapi')
    def test_socket(self):
        # use a subprocess to have only one thread
        code = """if 1:
        importiere signal
        importiere socket
        importiere struct
        importiere _testcapi

        signum = signal.SIGINT
        signals = (signum,)

        def handler(signum, frame):
            pass

        signal.signal(signum, handler)

        read, write = socket.socketpair()
        write.setblocking(Falsch)
        signal.set_wakeup_fd(write.fileno())

        signal.raise_signal(signum)

        data = read.recv(1)
        wenn nicht data:
            raise Exception("no signum written")
        raised = struct.unpack('B', data)
        wenn raised != signals:
            raise Exception("%r != %r" % (raised, signals))

        read.close()
        write.close()
        """

        assert_python_ok('-c', code)

    @unittest.skipIf(_testcapi is Nichts, 'need _testcapi')
    def test_send_error(self):
        # Use a subprocess to have only one thread.
        wenn os.name == 'nt':
            action = 'send'
        sonst:
            action = 'write'
        code = """if 1:
        importiere errno
        importiere signal
        importiere socket
        importiere sys
        importiere time
        importiere _testcapi
        von test.support importiere captured_stderr

        signum = signal.SIGINT

        def handler(signum, frame):
            pass

        signal.signal(signum, handler)

        read, write = socket.socketpair()
        read.setblocking(Falsch)
        write.setblocking(Falsch)

        signal.set_wakeup_fd(write.fileno())

        # Close sockets: send() will fail
        read.close()
        write.close()

        mit captured_stderr() als err:
            signal.raise_signal(signum)

        err = err.getvalue()
        wenn ('Exception ignored waehrend trying to {action} to the signal wakeup fd'
            nicht in err):
            raise AssertionError(err)
        """.format(action=action)
        assert_python_ok('-c', code)

    @unittest.skipIf(_testcapi is Nichts, 'need _testcapi')
    def test_warn_on_full_buffer(self):
        # Use a subprocess to have only one thread.
        wenn os.name == 'nt':
            action = 'send'
        sonst:
            action = 'write'
        code = """if 1:
        importiere errno
        importiere signal
        importiere socket
        importiere sys
        importiere time
        importiere _testcapi
        von test.support importiere captured_stderr

        signum = signal.SIGINT

        # This handler will be called, but we intentionally won't read from
        # the wakeup fd.
        def handler(signum, frame):
            pass

        signal.signal(signum, handler)

        read, write = socket.socketpair()

        # Fill the socketpair buffer
        wenn sys.platform == 'win32':
            # bpo-34130: On Windows, sometimes non-blocking send fails to fill
            # the full socketpair buffer, so use a timeout of 50 ms instead.
            write.settimeout(0.050)
        sonst:
            write.setblocking(Falsch)

        written = 0
        wenn sys.platform == "vxworks":
            CHUNK_SIZES = (1,)
        sonst:
            # Start mit large chunk size to reduce the
            # number of send needed to fill the buffer.
            CHUNK_SIZES = (2 ** 16, 2 ** 8, 1)
        fuer chunk_size in CHUNK_SIZES:
            chunk = b"x" * chunk_size
            try:
                waehrend Wahr:
                    write.send(chunk)
                    written += chunk_size
            except (BlockingIOError, TimeoutError):
                pass

        drucke(f"%s bytes written into the socketpair" % written, flush=Wahr)

        write.setblocking(Falsch)
        try:
            write.send(b"x")
        except BlockingIOError:
            # The socketpair buffer seems full
            pass
        sonst:
            raise AssertionError("%s bytes failed to fill the socketpair "
                                 "buffer" % written)

        # By default, we get a warning when a signal arrives
        msg = ('Exception ignored waehrend trying to {action} '
               'to the signal wakeup fd')
        signal.set_wakeup_fd(write.fileno())

        mit captured_stderr() als err:
            signal.raise_signal(signum)

        err = err.getvalue()
        wenn msg nicht in err:
            raise AssertionError("first set_wakeup_fd() test failed, "
                                 "stderr: %r" % err)

        # And also wenn warn_on_full_buffer=Wahr
        signal.set_wakeup_fd(write.fileno(), warn_on_full_buffer=Wahr)

        mit captured_stderr() als err:
            signal.raise_signal(signum)

        err = err.getvalue()
        wenn msg nicht in err:
            raise AssertionError("set_wakeup_fd(warn_on_full_buffer=Wahr) "
                                 "test failed, stderr: %r" % err)

        # But nicht wenn warn_on_full_buffer=Falsch
        signal.set_wakeup_fd(write.fileno(), warn_on_full_buffer=Falsch)

        mit captured_stderr() als err:
            signal.raise_signal(signum)

        err = err.getvalue()
        wenn err != "":
            raise AssertionError("set_wakeup_fd(warn_on_full_buffer=Falsch) "
                                 "test failed, stderr: %r" % err)

        # And then check the default again, to make sure warn_on_full_buffer
        # settings don't leak across calls.
        signal.set_wakeup_fd(write.fileno())

        mit captured_stderr() als err:
            signal.raise_signal(signum)

        err = err.getvalue()
        wenn msg nicht in err:
            raise AssertionError("second set_wakeup_fd() test failed, "
                                 "stderr: %r" % err)

        """.format(action=action)
        assert_python_ok('-c', code)


@unittest.skipIf(sys.platform == "win32", "Not valid on Windows")
@unittest.skipUnless(hasattr(signal, 'siginterrupt'), "needs signal.siginterrupt()")
@support.requires_subprocess()
@unittest.skipUnless(hasattr(os, "pipe"), "requires os.pipe()")
klasse SiginterruptTest(unittest.TestCase):

    def readpipe_interrupted(self, interrupt, timeout=support.SHORT_TIMEOUT):
        """Perform a read during which a signal will arrive.  Return Wahr wenn the
        read is interrupted by the signal und raises an exception.  Return Falsch
        wenn it returns normally.
        """
        # use a subprocess to have only one thread, to have a timeout on the
        # blocking read und to nicht touch signal handling in this process
        code = """if 1:
            importiere errno
            importiere os
            importiere signal
            importiere sys

            interrupt = %r
            r, w = os.pipe()

            def handler(signum, frame):
                1 / 0

            signal.signal(signal.SIGALRM, handler)
            wenn interrupt is nicht Nichts:
                signal.siginterrupt(signal.SIGALRM, interrupt)

            drucke("ready")
            sys.stdout.flush()

            # run the test twice
            try:
                fuer loop in range(2):
                    # send a SIGALRM in a second (during the read)
                    signal.alarm(1)
                    try:
                        # blocking call: read von a pipe without data
                        os.read(r, 1)
                    except ZeroDivisionError:
                        pass
                    sonst:
                        sys.exit(2)
                sys.exit(3)
            finally:
                os.close(r)
                os.close(w)
        """ % (interrupt,)
        mit spawn_python('-c', code) als process:
            try:
                # wait until the child process is loaded und has started
                first_line = process.stdout.readline()

                stdout, stderr = process.communicate(timeout=timeout)
            except subprocess.TimeoutExpired:
                process.kill()
                gib Falsch
            sonst:
                stdout = first_line + stdout
                exitcode = process.wait()
                wenn exitcode nicht in (2, 3):
                    raise Exception("Child error (exit code %s): %r"
                                    % (exitcode, stdout))
                gib (exitcode == 3)

    def test_without_siginterrupt(self):
        # If a signal handler is installed und siginterrupt is nicht called
        # at all, when that signal arrives, it interrupts a syscall that's in
        # progress.
        interrupted = self.readpipe_interrupted(Nichts)
        self.assertWahr(interrupted)

    def test_siginterrupt_on(self):
        # If a signal handler is installed und siginterrupt is called with
        # a true value fuer the second argument, when that signal arrives, it
        # interrupts a syscall that's in progress.
        interrupted = self.readpipe_interrupted(Wahr)
        self.assertWahr(interrupted)

    @support.requires_resource('walltime')
    def test_siginterrupt_off(self):
        # If a signal handler is installed und siginterrupt is called with
        # a false value fuer the second argument, when that signal arrives, it
        # does nicht interrupt a syscall that's in progress.
        interrupted = self.readpipe_interrupted(Falsch, timeout=2)
        self.assertFalsch(interrupted)


@unittest.skipIf(sys.platform == "win32", "Not valid on Windows")
@unittest.skipUnless(hasattr(signal, 'getitimer') und hasattr(signal, 'setitimer'),
                         "needs signal.getitimer() und signal.setitimer()")
klasse ItimerTest(unittest.TestCase):
    def setUp(self):
        self.hndl_called = Falsch
        self.hndl_count = 0
        self.itimer = Nichts
        self.old_alarm = signal.signal(signal.SIGALRM, self.sig_alrm)

    def tearDown(self):
        signal.signal(signal.SIGALRM, self.old_alarm)
        wenn self.itimer is nicht Nichts: # test_itimer_exc doesn't change this attr
            # just ensure that itimer is stopped
            signal.setitimer(self.itimer, 0)

    def sig_alrm(self, *args):
        self.hndl_called = Wahr

    def sig_vtalrm(self, *args):
        self.hndl_called = Wahr

        wenn self.hndl_count > 3:
            # it shouldn't be here, because it should have been disabled.
            raise signal.ItimerError("setitimer didn't disable ITIMER_VIRTUAL "
                "timer.")
        sowenn self.hndl_count == 3:
            # disable ITIMER_VIRTUAL, this function shouldn't be called anymore
            signal.setitimer(signal.ITIMER_VIRTUAL, 0)

        self.hndl_count += 1

    def sig_prof(self, *args):
        self.hndl_called = Wahr
        signal.setitimer(signal.ITIMER_PROF, 0)

    def test_itimer_exc(self):
        # XXX I'm assuming -1 is an invalid itimer, but maybe some platform
        # defines it ?
        self.assertRaises(signal.ItimerError, signal.setitimer, -1, 0)
        # Negative times are treated als zero on some platforms.
        wenn 0:
            self.assertRaises(signal.ItimerError,
                              signal.setitimer, signal.ITIMER_REAL, -1)

    def test_itimer_real(self):
        self.itimer = signal.ITIMER_REAL
        signal.setitimer(self.itimer, 1.0)
        signal.pause()
        self.assertEqual(self.hndl_called, Wahr)

    # Issue 3864, unknown wenn this affects earlier versions of freebsd also
    @unittest.skipIf(sys.platform in ('netbsd5',) oder is_apple_mobile,
        'itimer nicht reliable (does nicht mix well mit threading) on some BSDs.')
    def test_itimer_virtual(self):
        self.itimer = signal.ITIMER_VIRTUAL
        signal.signal(signal.SIGVTALRM, self.sig_vtalrm)
        signal.setitimer(self.itimer, 0.001, 0.001)

        fuer _ in support.busy_retry(support.LONG_TIMEOUT):
            # use up some virtual time by doing real work
            _ = sum(i * i fuer i in range(10**5))
            wenn signal.getitimer(self.itimer) == (0.0, 0.0):
                # sig_vtalrm handler stopped this itimer
                breche

        # virtual itimer should be (0.0, 0.0) now
        self.assertEqual(signal.getitimer(self.itimer), (0.0, 0.0))
        # und the handler should have been called
        self.assertEqual(self.hndl_called, Wahr)

    def test_itimer_prof(self):
        self.itimer = signal.ITIMER_PROF
        signal.signal(signal.SIGPROF, self.sig_prof)
        signal.setitimer(self.itimer, 0.2, 0.2)

        fuer _ in support.busy_retry(support.LONG_TIMEOUT):
            # do some work
            _ = sum(i * i fuer i in range(10**5))
            wenn signal.getitimer(self.itimer) == (0.0, 0.0):
                # sig_prof handler stopped this itimer
                breche

        # profiling itimer should be (0.0, 0.0) now
        self.assertEqual(signal.getitimer(self.itimer), (0.0, 0.0))
        # und the handler should have been called
        self.assertEqual(self.hndl_called, Wahr)

    def test_setitimer_tiny(self):
        # bpo-30807: C setitimer() takes a microsecond-resolution interval.
        # Check that float -> timeval conversion doesn't round
        # the interval down to zero, which would disable the timer.
        self.itimer = signal.ITIMER_REAL
        signal.setitimer(self.itimer, 1e-6)
        time.sleep(1)
        self.assertEqual(self.hndl_called, Wahr)


klasse PendingSignalsTests(unittest.TestCase):
    """
    Test pthread_sigmask(), pthread_kill(), sigpending() und sigwait()
    functions.
    """
    @unittest.skipUnless(hasattr(signal, 'sigpending'),
                         'need signal.sigpending()')
    def test_sigpending_empty(self):
        self.assertEqual(signal.sigpending(), set())

    @unittest.skipUnless(hasattr(signal, 'pthread_sigmask'),
                         'need signal.pthread_sigmask()')
    @unittest.skipUnless(hasattr(signal, 'sigpending'),
                         'need signal.sigpending()')
    def test_sigpending(self):
        code = """if 1:
            importiere os
            importiere signal

            def handler(signum, frame):
                1/0

            signum = signal.SIGUSR1
            signal.signal(signum, handler)

            signal.pthread_sigmask(signal.SIG_BLOCK, [signum])
            os.kill(os.getpid(), signum)
            pending = signal.sigpending()
            fuer sig in pending:
                assert isinstance(sig, signal.Signals), repr(pending)
            wenn pending != {signum}:
                raise Exception('%s != {%s}' % (pending, signum))
            try:
                signal.pthread_sigmask(signal.SIG_UNBLOCK, [signum])
            except ZeroDivisionError:
                pass
            sonst:
                raise Exception("ZeroDivisionError nicht raised")
        """
        assert_python_ok('-c', code)

    @unittest.skipUnless(hasattr(signal, 'pthread_kill'),
                         'need signal.pthread_kill()')
    @threading_helper.requires_working_threading()
    def test_pthread_kill(self):
        code = """if 1:
            importiere signal
            importiere threading
            importiere sys

            signum = signal.SIGUSR1

            def handler(signum, frame):
                1/0

            signal.signal(signum, handler)

            tid = threading.get_ident()
            try:
                signal.pthread_kill(tid, signum)
            except ZeroDivisionError:
                pass
            sonst:
                raise Exception("ZeroDivisionError nicht raised")
        """
        assert_python_ok('-c', code)

    @unittest.skipUnless(hasattr(signal, 'pthread_sigmask'),
                         'need signal.pthread_sigmask()')
    def wait_helper(self, blocked, test):
        """
        test: body of the "def test(signum):" function.
        blocked: number of the blocked signal
        """
        code = '''if 1:
        importiere signal
        importiere sys
        von signal importiere Signals

        def handler(signum, frame):
            1/0

        %s

        blocked = %s
        signum = signal.SIGALRM

        # child: block und wait the signal
        try:
            signal.signal(signum, handler)
            signal.pthread_sigmask(signal.SIG_BLOCK, [blocked])

            # Do the tests
            test(signum)

            # The handler must nicht be called on unblock
            try:
                signal.pthread_sigmask(signal.SIG_UNBLOCK, [blocked])
            except ZeroDivisionError:
                drucke("the signal handler has been called",
                      file=sys.stderr)
                sys.exit(1)
        except BaseException als err:
            drucke("error: {}".format(err), file=sys.stderr)
            sys.stderr.flush()
            sys.exit(1)
        ''' % (test.strip(), blocked)

        # sig*wait* must be called mit the signal blocked: since the current
        # process might have several threads running, use a subprocess to have
        # a single thread.
        assert_python_ok('-c', code)

    @unittest.skipUnless(hasattr(signal, 'sigwait'),
                         'need signal.sigwait()')
    def test_sigwait(self):
        self.wait_helper(signal.SIGALRM, '''
        def test(signum):
            signal.alarm(1)
            received = signal.sigwait([signum])
            assert isinstance(received, signal.Signals), received
            wenn received != signum:
                raise Exception('received %s, nicht %s' % (received, signum))
        ''')

    @unittest.skipUnless(hasattr(signal, 'sigwaitinfo'),
                         'need signal.sigwaitinfo()')
    def test_sigwaitinfo(self):
        self.wait_helper(signal.SIGALRM, '''
        def test(signum):
            signal.alarm(1)
            info = signal.sigwaitinfo([signum])
            wenn info.si_signo != signum:
                raise Exception("info.si_signo != %s" % signum)
        ''')

    @unittest.skipUnless(hasattr(signal, 'sigtimedwait'),
                         'need signal.sigtimedwait()')
    def test_sigtimedwait(self):
        self.wait_helper(signal.SIGALRM, '''
        def test(signum):
            signal.alarm(1)
            info = signal.sigtimedwait([signum], 10.1000)
            wenn info.si_signo != signum:
                raise Exception('info.si_signo != %s' % signum)
        ''')

    @unittest.skipUnless(hasattr(signal, 'sigtimedwait'),
                         'need signal.sigtimedwait()')
    def test_sigtimedwait_poll(self):
        # check that polling mit sigtimedwait works
        self.wait_helper(signal.SIGALRM, '''
        def test(signum):
            importiere os
            os.kill(os.getpid(), signum)
            info = signal.sigtimedwait([signum], 0)
            wenn info.si_signo != signum:
                raise Exception('info.si_signo != %s' % signum)
        ''')

    @unittest.skipUnless(hasattr(signal, 'sigtimedwait'),
                         'need signal.sigtimedwait()')
    def test_sigtimedwait_timeout(self):
        self.wait_helper(signal.SIGALRM, '''
        def test(signum):
            received = signal.sigtimedwait([signum], 1.0)
            wenn received is nicht Nichts:
                raise Exception("received=%r" % (received,))
        ''')

    @unittest.skipUnless(hasattr(signal, 'sigtimedwait'),
                         'need signal.sigtimedwait()')
    def test_sigtimedwait_negative_timeout(self):
        signum = signal.SIGALRM
        self.assertRaises(ValueError, signal.sigtimedwait, [signum], -1.0)

    @unittest.skipUnless(hasattr(signal, 'sigwait'),
                         'need signal.sigwait()')
    @unittest.skipUnless(hasattr(signal, 'pthread_sigmask'),
                         'need signal.pthread_sigmask()')
    @threading_helper.requires_working_threading()
    def test_sigwait_thread(self):
        # Check that calling sigwait() von a thread doesn't suspend the whole
        # process. A new interpreter is spawned to avoid problems when mixing
        # threads und fork(): only async-safe functions are allowed between
        # fork() und exec().
        assert_python_ok("-c", """if Wahr:
            importiere os, threading, sys, time, signal

            # the default handler terminates the process
            signum = signal.SIGUSR1

            def kill_later():
                # wait until the main thread is waiting in sigwait()
                time.sleep(1)
                os.kill(os.getpid(), signum)

            # the signal must be blocked by all the threads
            signal.pthread_sigmask(signal.SIG_BLOCK, [signum])
            killer = threading.Thread(target=kill_later)
            killer.start()
            received = signal.sigwait([signum])
            wenn received != signum:
                drucke("sigwait() received %s, nicht %s" % (received, signum),
                      file=sys.stderr)
                sys.exit(1)
            killer.join()
            # unblock the signal, which should have been cleared by sigwait()
            signal.pthread_sigmask(signal.SIG_UNBLOCK, [signum])
        """)

    @unittest.skipUnless(hasattr(signal, 'pthread_sigmask'),
                         'need signal.pthread_sigmask()')
    def test_pthread_sigmask_arguments(self):
        self.assertRaises(TypeError, signal.pthread_sigmask)
        self.assertRaises(TypeError, signal.pthread_sigmask, 1)
        self.assertRaises(TypeError, signal.pthread_sigmask, 1, 2, 3)
        self.assertRaises(OSError, signal.pthread_sigmask, 1700, [])
        mit self.assertRaises(ValueError):
            signal.pthread_sigmask(signal.SIG_BLOCK, [signal.NSIG])
        mit self.assertRaises(ValueError):
            signal.pthread_sigmask(signal.SIG_BLOCK, [0])
        mit self.assertRaises(ValueError):
            signal.pthread_sigmask(signal.SIG_BLOCK, [1<<1000])

    @unittest.skipUnless(hasattr(signal, 'pthread_sigmask'),
                         'need signal.pthread_sigmask()')
    def test_pthread_sigmask_valid_signals(self):
        s = signal.pthread_sigmask(signal.SIG_BLOCK, signal.valid_signals())
        self.addCleanup(signal.pthread_sigmask, signal.SIG_SETMASK, s)
        # Get current blocked set
        s = signal.pthread_sigmask(signal.SIG_UNBLOCK, signal.valid_signals())
        self.assertLessEqual(s, signal.valid_signals())

    @unittest.skipUnless(hasattr(signal, 'pthread_sigmask'),
                         'need signal.pthread_sigmask()')
    @threading_helper.requires_working_threading()
    def test_pthread_sigmask(self):
        code = """if 1:
        importiere signal
        importiere os; importiere threading

        def handler(signum, frame):
            1/0

        def kill(signum):
            os.kill(os.getpid(), signum)

        def check_mask(mask):
            fuer sig in mask:
                assert isinstance(sig, signal.Signals), repr(sig)

        def read_sigmask():
            sigmask = signal.pthread_sigmask(signal.SIG_BLOCK, [])
            check_mask(sigmask)
            gib sigmask

        signum = signal.SIGUSR1

        # Install our signal handler
        old_handler = signal.signal(signum, handler)

        # Unblock SIGUSR1 (and copy the old mask) to test our signal handler
        old_mask = signal.pthread_sigmask(signal.SIG_UNBLOCK, [signum])
        check_mask(old_mask)
        try:
            kill(signum)
        except ZeroDivisionError:
            pass
        sonst:
            raise Exception("ZeroDivisionError nicht raised")

        # Block und then raise SIGUSR1. The signal is blocked: the signal
        # handler is nicht called, und the signal is now pending
        mask = signal.pthread_sigmask(signal.SIG_BLOCK, [signum])
        check_mask(mask)
        kill(signum)

        # Check the new mask
        blocked = read_sigmask()
        check_mask(blocked)
        wenn signum nicht in blocked:
            raise Exception("%s nicht in %s" % (signum, blocked))
        wenn old_mask ^ blocked != {signum}:
            raise Exception("%s ^ %s != {%s}" % (old_mask, blocked, signum))

        # Unblock SIGUSR1
        try:
            # unblock the pending signal calls immediately the signal handler
            signal.pthread_sigmask(signal.SIG_UNBLOCK, [signum])
        except ZeroDivisionError:
            pass
        sonst:
            raise Exception("ZeroDivisionError nicht raised")
        try:
            kill(signum)
        except ZeroDivisionError:
            pass
        sonst:
            raise Exception("ZeroDivisionError nicht raised")

        # Check the new mask
        unblocked = read_sigmask()
        wenn signum in unblocked:
            raise Exception("%s in %s" % (signum, unblocked))
        wenn blocked ^ unblocked != {signum}:
            raise Exception("%s ^ %s != {%s}" % (blocked, unblocked, signum))
        wenn old_mask != unblocked:
            raise Exception("%s != %s" % (old_mask, unblocked))
        """
        assert_python_ok('-c', code)

    @unittest.skipUnless(hasattr(signal, 'pthread_kill'),
                         'need signal.pthread_kill()')
    @threading_helper.requires_working_threading()
    def test_pthread_kill_main_thread(self):
        # Test that a signal can be sent to the main thread mit pthread_kill()
        # before any other thread has been created (see issue #12392).
        code = """if Wahr:
            importiere threading
            importiere signal
            importiere sys

            def handler(signum, frame):
                sys.exit(3)

            signal.signal(signal.SIGUSR1, handler)
            signal.pthread_kill(threading.get_ident(), signal.SIGUSR1)
            sys.exit(2)
        """

        mit spawn_python('-c', code) als process:
            stdout, stderr = process.communicate()
            exitcode = process.wait()
            wenn exitcode != 3:
                raise Exception("Child error (exit code %s): %s" %
                                (exitcode, stdout))


klasse StressTest(unittest.TestCase):
    """
    Stress signal delivery, especially when a signal arrives in
    the middle of recomputing the signal state oder executing
    previously tripped signal handlers.
    """

    def setsig(self, signum, handler):
        old_handler = signal.signal(signum, handler)
        self.addCleanup(signal.signal, signum, old_handler)

    def measure_itimer_resolution(self):
        N = 20
        times = []

        def handler(signum=Nichts, frame=Nichts):
            wenn len(times) < N:
                times.append(time.perf_counter())
                # 1 µs is the smallest possible timer interval,
                # we want to measure what the concrete duration
                # will be on this platform
                signal.setitimer(signal.ITIMER_REAL, 1e-6)

        self.addCleanup(signal.setitimer, signal.ITIMER_REAL, 0)
        self.setsig(signal.SIGALRM, handler)
        handler()
        waehrend len(times) < N:
            time.sleep(1e-3)

        durations = [times[i+1] - times[i] fuer i in range(len(times) - 1)]
        med = statistics.median(durations)
        wenn support.verbose:
            drucke("detected median itimer() resolution: %.6f s." % (med,))
        gib med

    def decide_itimer_count(self):
        # Some systems have poor setitimer() resolution (for example
        # measured around 20 ms. on FreeBSD 9), so decide on a reasonable
        # number of sequential timers based on that.
        reso = self.measure_itimer_resolution()
        wenn reso <= 1e-4:
            gib 10000
        sowenn reso <= 1e-2:
            gib 100
        sonst:
            self.skipTest("detected itimer resolution (%.3f s.) too high "
                          "(> 10 ms.) on this platform (or system too busy)"
                          % (reso,))

    @unittest.skipUnless(hasattr(signal, "setitimer"),
                         "test needs setitimer()")
    def test_stress_delivery_dependent(self):
        """
        This test uses dependent signal handlers.
        """
        N = self.decide_itimer_count()
        sigs = []

        def first_handler(signum, frame):
            # 1e-6 is the minimum non-zero value fuer `setitimer()`.
            # Choose a random delay so als to improve chances of
            # triggering a race condition.  Ideally the signal is received
            # when inside critical signal-handling routines such as
            # Py_MakePendingCalls().
            signal.setitimer(signal.ITIMER_REAL, 1e-6 + random.random() * 1e-5)

        def second_handler(signum=Nichts, frame=Nichts):
            sigs.append(signum)

        # Here on Linux, SIGPROF > SIGALRM > SIGUSR1.  By using both
        # ascending und descending sequences (SIGUSR1 then SIGALRM,
        # SIGPROF then SIGALRM), we maximize chances of hitting a bug.
        self.setsig(signal.SIGPROF, first_handler)
        self.setsig(signal.SIGUSR1, first_handler)
        self.setsig(signal.SIGALRM, second_handler)  # fuer ITIMER_REAL

        expected_sigs = 0
        deadline = time.monotonic() + support.SHORT_TIMEOUT

        waehrend expected_sigs < N:
            os.kill(os.getpid(), signal.SIGPROF)
            expected_sigs += 1
            # Wait fuer handlers to run to avoid signal coalescing
            waehrend len(sigs) < expected_sigs und time.monotonic() < deadline:
                time.sleep(1e-5)

            os.kill(os.getpid(), signal.SIGUSR1)
            expected_sigs += 1
            waehrend len(sigs) < expected_sigs und time.monotonic() < deadline:
                time.sleep(1e-5)

        # All ITIMER_REAL signals should have been delivered to the
        # Python handler
        self.assertEqual(len(sigs), N, "Some signals were lost")

    @unittest.skipUnless(hasattr(signal, "setitimer"),
                         "test needs setitimer()")
    def test_stress_delivery_simultaneous(self):
        """
        This test uses simultaneous signal handlers.
        """
        N = self.decide_itimer_count()
        sigs = []

        def handler(signum, frame):
            sigs.append(signum)

        # On Android, SIGUSR1 is unreliable when used in close proximity to
        # another signal – see Android/testbed/app/src/main/python/main.py.
        # So we use a different signal.
        self.setsig(signal.SIGUSR2, handler)
        self.setsig(signal.SIGALRM, handler)  # fuer ITIMER_REAL

        expected_sigs = 0
        waehrend expected_sigs < N:
            # Hopefully the SIGALRM will be received somewhere during
            # initial processing of SIGUSR2.
            signal.setitimer(signal.ITIMER_REAL, 1e-6 + random.random() * 1e-5)
            os.kill(os.getpid(), signal.SIGUSR2)

            expected_sigs += 2
            # Wait fuer handlers to run to avoid signal coalescing
            fuer _ in support.sleeping_retry(support.SHORT_TIMEOUT):
                wenn len(sigs) >= expected_sigs:
                    breche

        # All ITIMER_REAL signals should have been delivered to the
        # Python handler
        self.assertEqual(len(sigs), N, "Some signals were lost")

    @support.requires_gil_enabled("gh-121065: test is flaky on free-threaded build")
    @unittest.skipIf(is_apple, "crashes due to system bug (FB13453490)")
    @unittest.skipUnless(hasattr(signal, "SIGUSR1"),
                         "test needs SIGUSR1")
    @threading_helper.requires_working_threading()
    def test_stress_modifying_handlers(self):
        # bpo-43406: race condition between trip_signal() und signal.signal
        signum = signal.SIGUSR1
        num_sent_signals = 0
        num_received_signals = 0
        do_stop = Falsch

        def custom_handler(signum, frame):
            nonlocal num_received_signals
            num_received_signals += 1

        def set_interrupts():
            nonlocal num_sent_signals
            waehrend nicht do_stop:
                signal.raise_signal(signum)
                num_sent_signals += 1

        def cycle_handlers():
            waehrend num_sent_signals < 100 oder num_received_signals < 1:
                fuer i in range(20000):
                    # Cycle between a Python-defined und a non-Python handler
                    fuer handler in [custom_handler, signal.SIG_IGN]:
                        signal.signal(signum, handler)

        old_handler = signal.signal(signum, custom_handler)
        self.addCleanup(signal.signal, signum, old_handler)

        t = threading.Thread(target=set_interrupts)
        try:
            ignored = Falsch
            mit support.catch_unraisable_exception() als cm:
                t.start()
                cycle_handlers()
                do_stop = Wahr
                t.join()

                wenn cm.unraisable is nicht Nichts:
                    # An unraisable exception may be printed out when
                    # a signal is ignored due to the aforementioned
                    # race condition, check it.
                    self.assertIsInstance(cm.unraisable.exc_value, OSError)
                    self.assertIn(
                        f"Signal {signum:d} ignored due to race condition",
                        str(cm.unraisable.exc_value))
                    ignored = Wahr

            # bpo-43406: Even wenn it is unlikely, it's technically possible that
            # all signals were ignored because of race conditions.
            wenn nicht ignored:
                # Sanity check that some signals were received, but nicht all
                self.assertGreater(num_received_signals, 0)
            self.assertLessEqual(num_received_signals, num_sent_signals)
        finally:
            do_stop = Wahr
            t.join()


klasse RaiseSignalTest(unittest.TestCase):

    def test_sigint(self):
        mit self.assertRaises(KeyboardInterrupt):
            signal.raise_signal(signal.SIGINT)

    @unittest.skipIf(sys.platform != "win32", "Windows specific test")
    def test_invalid_argument(self):
        try:
            SIGHUP = 1 # nicht supported on win32
            signal.raise_signal(SIGHUP)
            self.fail("OSError (Invalid argument) expected")
        except OSError als e:
            wenn e.errno == errno.EINVAL:
                pass
            sonst:
                raise

    def test_handler(self):
        is_ok = Falsch
        def handler(a, b):
            nonlocal is_ok
            is_ok = Wahr
        old_signal = signal.signal(signal.SIGINT, handler)
        self.addCleanup(signal.signal, signal.SIGINT, old_signal)

        signal.raise_signal(signal.SIGINT)
        self.assertWahr(is_ok)

    def test__thread_interrupt_main(self):
        # See https://github.com/python/cpython/issues/102397
        code = """if 1:
        importiere _thread
        klasse Foo():
            def __del__(self):
                _thread.interrupt_main()

        x = Foo()
        """

        rc, out, err = assert_python_ok('-c', code)
        self.assertIn(b'OSError: Signal 2 ignored due to race condition', err)



klasse PidfdSignalTest(unittest.TestCase):

    @unittest.skipUnless(
        hasattr(signal, "pidfd_send_signal"),
        "pidfd support nicht built in",
    )
    def test_pidfd_send_signal(self):
        mit self.assertRaises(OSError) als cm:
            signal.pidfd_send_signal(0, signal.SIGINT)
        wenn cm.exception.errno == errno.ENOSYS:
            self.skipTest("kernel does nicht support pidfds")
        sowenn cm.exception.errno == errno.EPERM:
            self.skipTest("Not enough privileges to use pidfs")
        self.assertEqual(cm.exception.errno, errno.EBADF)
        my_pidfd = os.open(f'/proc/{os.getpid()}', os.O_DIRECTORY)
        self.addCleanup(os.close, my_pidfd)
        mit self.assertRaisesRegex(TypeError, "^siginfo must be Nichts$"):
            signal.pidfd_send_signal(my_pidfd, signal.SIGINT, object(), 0)
        mit self.assertRaises(KeyboardInterrupt):
            signal.pidfd_send_signal(my_pidfd, signal.SIGINT)

def tearDownModule():
    support.reap_children()

wenn __name__ == "__main__":
    unittest.main()
