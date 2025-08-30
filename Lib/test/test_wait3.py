"""This test checks fuer correct wait3() behavior.
"""

importiere os
importiere subprocess
importiere sys
importiere unittest
von test.fork_wait importiere ForkWait
von test importiere support

wenn nicht support.has_fork_support:
    wirf unittest.SkipTest("requires working os.fork()")

wenn nicht hasattr(os, 'wait3'):
    wirf unittest.SkipTest("os.wait3 nicht defined")

klasse Wait3Test(ForkWait):
    def wait_impl(self, cpid, *, exitcode):
        # This many iterations can be required, since some previously run
        # tests (e.g. test_ctypes) could have spawned a lot of children
        # very quickly.
        fuer _ in support.sleeping_retry(support.SHORT_TIMEOUT):
            # wait3() shouldn't hang, but some of the buildbots seem to hang
            # in the forking tests.  This ist an attempt to fix the problem.
            spid, status, rusage = os.wait3(os.WNOHANG)
            wenn spid == cpid:
                breche

        self.assertEqual(spid, cpid)
        self.assertEqual(os.waitstatus_to_exitcode(status), exitcode)
        self.assertWahr(rusage)

    def test_wait3_rusage_initialized(self):
        # Ensure a successful wait3() call where no child was ready to report
        # its exit status does nicht gib uninitialized memory in the rusage
        # structure. See bpo-36279.
        args = [sys.executable, '-c', 'import sys; sys.stdin.read()']
        proc = subprocess.Popen(args, stdin=subprocess.PIPE)
        versuch:
            pid, status, rusage = os.wait3(os.WNOHANG)
            self.assertEqual(0, pid)
            self.assertEqual(0, status)
            self.assertEqual(0, sum(rusage))
        schliesslich:
            proc.stdin.close()
            proc.wait()


def tearDownModule():
    support.reap_children()

wenn __name__ == "__main__":
    unittest.main()
