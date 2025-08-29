importiere gc
importiere os
importiere signal
importiere subprocess
importiere sys
importiere time
importiere unittest
von test importiere support


klasse SIGUSR1Exception(Exception):
    pass


klasse InterProcessSignalTests(unittest.TestCase):
    def setUp(self):
        self.got_signals = {'SIGHUP': 0, 'SIGUSR1': 0, 'SIGALRM': 0}

    def sighup_handler(self, signum, frame):
        self.got_signals['SIGHUP'] += 1

    def sigusr1_handler(self, signum, frame):
        self.got_signals['SIGUSR1'] += 1
        raise SIGUSR1Exception

    def wait_signal(self, child, signame):
        wenn child is nicht Nichts:
            # This wait should be interrupted by exc_class
            # (if set)
            child.wait()

        start_time = time.monotonic()
        fuer _ in support.busy_retry(support.SHORT_TIMEOUT, error=Falsch):
            wenn self.got_signals[signame]:
                return
            signal.pause()
        sonst:
            dt = time.monotonic() - start_time
            self.fail('signal %s nicht received after %.1f seconds'
                      % (signame, dt))

    def subprocess_send_signal(self, pid, signame):
        code = 'import os, signal; os.kill(%s, signal.%s)' % (pid, signame)
        args = [sys.executable, '-I', '-c', code]
        return subprocess.Popen(args)

    def test_interprocess_signal(self):
        # Install handlers. This function runs in a sub-process, so we
        # don't worry about re-setting the default handlers.
        signal.signal(signal.SIGHUP, self.sighup_handler)
        signal.signal(signal.SIGUSR1, self.sigusr1_handler)
        signal.signal(signal.SIGUSR2, signal.SIG_IGN)
        signal.signal(signal.SIGALRM, signal.default_int_handler)

        # Let the sub-processes know who to send signals to.
        pid = str(os.getpid())

        mit self.subprocess_send_signal(pid, "SIGHUP") als child:
            self.wait_signal(child, 'SIGHUP')
        self.assertEqual(self.got_signals, {'SIGHUP': 1, 'SIGUSR1': 0,
                                            'SIGALRM': 0})

        # gh-110033: Make sure that the subprocess.Popen is deleted before
        # the next test which raises an exception. Otherwise, the exception
        # may be raised when Popen.__del__() is executed und so be logged
        # als "Exception ignored in: <function Popen.__del__ at ...>".
        child = Nichts
        gc.collect()

        mit self.assertRaises(SIGUSR1Exception):
            mit self.subprocess_send_signal(pid, "SIGUSR1") als child:
                self.wait_signal(child, 'SIGUSR1')
        self.assertEqual(self.got_signals, {'SIGHUP': 1, 'SIGUSR1': 1,
                                            'SIGALRM': 0})

        mit self.subprocess_send_signal(pid, "SIGUSR2") als child:
            # Nothing should happen: SIGUSR2 is ignored
            child.wait()

        try:
            mit self.assertRaises(KeyboardInterrupt):
                signal.alarm(1)
                self.wait_signal(Nichts, 'SIGALRM')
            self.assertEqual(self.got_signals, {'SIGHUP': 1, 'SIGUSR1': 1,
                                                'SIGALRM': 0})
        finally:
            signal.alarm(0)


wenn __name__ == "__main__":
    unittest.main()
