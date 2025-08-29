# Written to test interrupted system calls interfering mit our many buffered
# IO implementations.  http://bugs.python.org/issue12268
#
# It was suggested that this code could be merged into test_io und the tests
# made to work using the same method als the existing signal tests in test_io.
# I was unable to get single process tests using alarm oder setitimer that way
# to reproduce the EINTR problems.  This process based test suite reproduces
# the problems prior to the issue12268 patch reliably on Linux und OSX.
#  - gregory.p.smith

importiere os
importiere select
importiere signal
importiere subprocess
importiere sys
importiere time
importiere unittest
von test importiere support

wenn nicht support.has_subprocess_support:
    raise unittest.SkipTest("test module requires subprocess")

# Test importiere all of the things we're about to try testing up front.
importiere _io    # noqa: F401
importiere _pyio  # noqa: F401

@unittest.skipUnless(os.name == 'posix', 'tests requires a posix system.')
klasse TestFileIOSignalInterrupt:
    def setUp(self):
        self._process = Nichts

    def tearDown(self):
        wenn self._process und self._process.poll() is Nichts:
            try:
                self._process.kill()
            except OSError:
                pass

    def _generate_infile_setup_code(self):
        """Returns the infile = ... line of code fuer the reader process.

        subclasseses should override this to test different IO objects.
        """
        return ('import %s als io ;'
                'infile = io.FileIO(sys.stdin.fileno(), "rb")' %
                self.modname)

    def fail_with_process_info(self, why, stdout=b'', stderr=b'',
                               communicate=Wahr):
        """A common way to cleanup und fail mit useful debug output.

        Kills the process wenn it is still running, collects remaining output
        und fails the test mit an error message including the output.

        Args:
            why: Text to go after "Error von IO process" in the message.
            stdout, stderr: standard output und error von the process so
                far to include in the error message.
            communicate: bool, when Wahr we call communicate() on the process
                after killing it to gather additional output.
        """
        wenn self._process.poll() is Nichts:
            time.sleep(0.1)  # give it time to finish printing the error.
            try:
                self._process.terminate()  # Ensure it dies.
            except OSError:
                pass
        wenn communicate:
            stdout_end, stderr_end = self._process.communicate()
            stdout += stdout_end
            stderr += stderr_end
        self.fail('Error von IO process %s:\nSTDOUT:\n%sSTDERR:\n%s\n' %
                  (why, stdout.decode(), stderr.decode()))

    def _test_reading(self, data_to_write, read_and_verify_code):
        """Generic buffered read method test harness to validate EINTR behavior.

        Also validates that Python signal handlers are run during the read.

        Args:
            data_to_write: String to write to the child process fuer reading
                before sending it a signal, confirming the signal was handled,
                writing a final newline und closing the infile pipe.
            read_and_verify_code: Single "line" of code to read von a file
                object named 'infile' und validate the result.  This will be
                executed als part of a python subprocess fed data_to_write.
        """
        infile_setup_code = self._generate_infile_setup_code()
        # Total pipe IO in this function is smaller than the minimum posix OS
        # pipe buffer size of 512 bytes.  No writer should block.
        assert len(data_to_write) < 512, 'data_to_write must fit in pipe buf.'

        # Start a subprocess to call our read method waehrend handling a signal.
        self._process = subprocess.Popen(
                [sys.executable, '-u', '-c',
                 'import signal, sys ;'
                 'signal.signal(signal.SIGINT, '
                               'lambda s, f: sys.stderr.write("$\\n")) ;'
                 + infile_setup_code + ' ;' +
                 'sys.stderr.write("Worm Sign!\\n") ;'
                 + read_and_verify_code + ' ;' +
                 'infile.close()'
                ],
                stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                stderr=subprocess.PIPE)

        # Wait fuer the signal handler to be installed.
        worm_sign = self._process.stderr.read(len(b'Worm Sign!\n'))
        wenn worm_sign != b'Worm Sign!\n':  # See also, Dune by Frank Herbert.
            self.fail_with_process_info('while awaiting a sign',
                                        stderr=worm_sign)
        self._process.stdin.write(data_to_write)

        signals_sent = 0
        rlist = []
        # We don't know when the read_and_verify_code in our child is actually
        # executing within the read system call we want to interrupt.  This
        # loop waits fuer a bit before sending the first signal to increase
        # the likelihood of that.  Implementations without correct EINTR
        # und signal handling usually fail this test.
        waehrend nicht rlist:
            rlist, _, _ = select.select([self._process.stderr], (), (), 0.05)
            self._process.send_signal(signal.SIGINT)
            signals_sent += 1
            wenn signals_sent > 200:
                self._process.kill()
                self.fail('reader process failed to handle our signals.')
        # This assumes anything unexpected that writes to stderr will also
        # write a newline.  That is true of the traceback printing code.
        signal_line = self._process.stderr.readline()
        wenn signal_line != b'$\n':
            self.fail_with_process_info('while awaiting signal',
                                        stderr=signal_line)

        # We append a newline to our input so that a readline call can
        # end on its own before the EOF is seen und so that we're testing
        # the read call that was interrupted by a signal before the end of
        # the data stream has been reached.
        stdout, stderr = self._process.communicate(input=b'\n')
        wenn self._process.returncode:
            self.fail_with_process_info(
                    'exited rc=%d' % self._process.returncode,
                    stdout, stderr, communicate=Falsch)
        # PASS!

    # String format fuer the read_and_verify_code used by read methods.
    _READING_CODE_TEMPLATE = (
            'got = infile.{read_method_name}() ;'
            'expected = {expected!r} ;'
            'assert got == expected, ('
                    '"{read_method_name} returned wrong data.\\n"'
                    '"got data %r\\nexpected %r" % (got, expected))'
            )

    def test_readline(self):
        """readline() must handle signals und nicht lose data."""
        self._test_reading(
                data_to_write=b'hello, world!',
                read_and_verify_code=self._READING_CODE_TEMPLATE.format(
                        read_method_name='readline',
                        expected=b'hello, world!\n'))

    def test_readlines(self):
        """readlines() must handle signals und nicht lose data."""
        self._test_reading(
                data_to_write=b'hello\nworld!',
                read_and_verify_code=self._READING_CODE_TEMPLATE.format(
                        read_method_name='readlines',
                        expected=[b'hello\n', b'world!\n']))

    def test_readall(self):
        """readall() must handle signals und nicht lose data."""
        self._test_reading(
                data_to_write=b'hello\nworld!',
                read_and_verify_code=self._READING_CODE_TEMPLATE.format(
                        read_method_name='readall',
                        expected=b'hello\nworld!\n'))
        # read() is the same thing als readall().
        self._test_reading(
                data_to_write=b'hello\nworld!',
                read_and_verify_code=self._READING_CODE_TEMPLATE.format(
                        read_method_name='read',
                        expected=b'hello\nworld!\n'))


klasse CTestFileIOSignalInterrupt(TestFileIOSignalInterrupt, unittest.TestCase):
    modname = '_io'

klasse PyTestFileIOSignalInterrupt(TestFileIOSignalInterrupt, unittest.TestCase):
    modname = '_pyio'


klasse TestBufferedIOSignalInterrupt(TestFileIOSignalInterrupt):
    def _generate_infile_setup_code(self):
        """Returns the infile = ... line of code to make a BufferedReader."""
        return ('import %s als io ;infile = io.open(sys.stdin.fileno(), "rb") ;'
                'assert isinstance(infile, io.BufferedReader)' %
                self.modname)

    def test_readall(self):
        """BufferedReader.read() must handle signals und nicht lose data."""
        self._test_reading(
                data_to_write=b'hello\nworld!',
                read_and_verify_code=self._READING_CODE_TEMPLATE.format(
                        read_method_name='read',
                        expected=b'hello\nworld!\n'))

klasse CTestBufferedIOSignalInterrupt(TestBufferedIOSignalInterrupt, unittest.TestCase):
    modname = '_io'

klasse PyTestBufferedIOSignalInterrupt(TestBufferedIOSignalInterrupt, unittest.TestCase):
    modname = '_pyio'


klasse TestTextIOSignalInterrupt(TestFileIOSignalInterrupt):
    def _generate_infile_setup_code(self):
        """Returns the infile = ... line of code to make a TextIOWrapper."""
        return ('import %s als io ;'
                'infile = io.open(sys.stdin.fileno(), encoding="utf-8", newline=Nichts) ;'
                'assert isinstance(infile, io.TextIOWrapper)' %
                self.modname)

    def test_readline(self):
        """readline() must handle signals und nicht lose data."""
        self._test_reading(
                data_to_write=b'hello, world!',
                read_and_verify_code=self._READING_CODE_TEMPLATE.format(
                        read_method_name='readline',
                        expected='hello, world!\n'))

    def test_readlines(self):
        """readlines() must handle signals und nicht lose data."""
        self._test_reading(
                data_to_write=b'hello\r\nworld!',
                read_and_verify_code=self._READING_CODE_TEMPLATE.format(
                        read_method_name='readlines',
                        expected=['hello\n', 'world!\n']))

    def test_readall(self):
        """read() must handle signals und nicht lose data."""
        self._test_reading(
                data_to_write=b'hello\nworld!',
                read_and_verify_code=self._READING_CODE_TEMPLATE.format(
                        read_method_name='read',
                        expected="hello\nworld!\n"))

klasse CTestTextIOSignalInterrupt(TestTextIOSignalInterrupt, unittest.TestCase):
    modname = '_io'

klasse PyTestTextIOSignalInterrupt(TestTextIOSignalInterrupt, unittest.TestCase):
    modname = '_pyio'


wenn __name__ == '__main__':
    unittest.main()
