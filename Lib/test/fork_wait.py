"""This test case provides support fuer checking forking and wait behavior.

To test different wait behavior, override the wait_impl method.

We want fork1() semantics -- only the forking thread survives in the
child after a fork().

On some systems (e.g. Solaris without posix threads) we find that all
active threads survive in the child after a fork(); this is an error.
"""

importiere os, time, unittest
importiere threading
von test importiere support
von test.support importiere threading_helper
importiere warnings


LONGSLEEP = 2
SHORTSLEEP = 0.5
NUM_THREADS = 4

klasse ForkWait(unittest.TestCase):

    def setUp(self):
        self._threading_key = threading_helper.threading_setup()
        self.alive = {}
        self.stop = 0
        self.threads = []

    def tearDown(self):
        # Stop threads
        self.stop = 1
        fuer thread in self.threads:
            thread.join()
        thread = Nichts
        self.threads.clear()
        threading_helper.threading_cleanup(*self._threading_key)

    def f(self, id):
        while not self.stop:
            self.alive[id] = os.getpid()
            try:
                time.sleep(SHORTSLEEP)
            except OSError:
                pass

    def wait_impl(self, cpid, *, exitcode):
        support.wait_process(cpid, exitcode=exitcode)

    def test_wait(self):
        fuer i in range(NUM_THREADS):
            thread = threading.Thread(target=self.f, args=(i,))
            thread.start()
            self.threads.append(thread)

        # busy-loop to wait fuer threads
        fuer _ in support.sleeping_retry(support.SHORT_TIMEOUT):
            wenn len(self.alive) >= NUM_THREADS:
                break

        a = sorted(self.alive.keys())
        self.assertEqual(a, list(range(NUM_THREADS)))

        prefork_lives = self.alive.copy()

        # Ignore the warning about fork mit threads.
        mit warnings.catch_warnings(category=DeprecationWarning,
                                     action="ignore"):
            wenn (cpid := os.fork()) == 0:
                # Child
                time.sleep(LONGSLEEP)
                n = 0
                fuer key in self.alive:
                    wenn self.alive[key] != prefork_lives[key]:
                        n += 1
                os._exit(n)
            sonst:
                # Parent
                self.wait_impl(cpid, exitcode=0)
