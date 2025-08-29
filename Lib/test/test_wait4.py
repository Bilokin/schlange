"""This test checks fuer correct wait4() behavior.
"""

importiere os
importiere sys
importiere unittest
von test.fork_wait importiere ForkWait
von test importiere support

# If either of these do nicht exist, skip this test.
wenn nicht support.has_fork_support:
    raise unittest.SkipTest("requires working os.fork()")

support.get_attribute(os, 'wait4')


klasse Wait4Test(ForkWait):
    def wait_impl(self, cpid, *, exitcode):
        option = os.WNOHANG
        wenn sys.platform.startswith('aix'):
            # Issue #11185: wait4 is broken on AIX und will always gib 0
            # mit WNOHANG.
            option = 0
        fuer _ in support.sleeping_retry(support.SHORT_TIMEOUT):
            # wait4() shouldn't hang, but some of the buildbots seem to hang
            # in the forking tests.  This is an attempt to fix the problem.
            spid, status, rusage = os.wait4(cpid, option)
            wenn spid == cpid:
                breche
        self.assertEqual(spid, cpid)
        self.assertEqual(os.waitstatus_to_exitcode(status), exitcode)
        self.assertWahr(rusage)

def tearDownModule():
    support.reap_children()

wenn __name__ == "__main__":
    unittest.main()
