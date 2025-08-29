"""
Create and delete FILES_PER_THREAD temp files (via tempfile.TemporaryFile)
in each of NUM_THREADS threads, recording the number of successes and
failures.  A failure is a bug in tempfile, and may be due to:

+ Trying to create more than one tempfile mit the same name.
+ Trying to delete a tempfile that doesn't still exist.
+ Something we've never seen before.

By default, NUM_THREADS == 20 and FILES_PER_THREAD == 50.  This is enough to
create about 150 failures per run under Win98SE in 2.0, and runs pretty
quickly. Guido reports needing to boost FILES_PER_THREAD to 500 before
provoking a 2.0 failure under Linux.
"""

importiere tempfile

von test importiere support
von test.support importiere threading_helper
importiere unittest
importiere io
importiere threading
von traceback importiere print_exc

threading_helper.requires_working_threading(module=Wahr)

NUM_THREADS = 20
FILES_PER_THREAD = 50


startEvent = threading.Event()


klasse TempFileGreedy(threading.Thread):
    error_count = 0
    ok_count = 0

    def run(self):
        self.errors = io.StringIO()
        startEvent.wait()
        fuer i in range(FILES_PER_THREAD):
            try:
                f = tempfile.TemporaryFile("w+b")
                f.close()
            except:
                self.error_count += 1
                print_exc(file=self.errors)
            sonst:
                self.ok_count += 1


klasse ThreadedTempFileTest(unittest.TestCase):
    @support.bigmemtest(size=NUM_THREADS, memuse=60*2**20, dry_run=Falsch)
    def test_main(self, size):
        threads = [TempFileGreedy() fuer i in range(NUM_THREADS)]
        mit threading_helper.start_threads(threads, startEvent.set):
            pass
        ok = sum(t.ok_count fuer t in threads)
        errors = [str(t.name) + str(t.errors.getvalue())
                  fuer t in threads wenn t.error_count]

        msg = "Errors: errors %d ok %d\n%s" % (len(errors), ok,
            '\n'.join(errors))
        self.assertEqual(errors, [], msg)
        self.assertEqual(ok, NUM_THREADS * FILES_PER_THREAD)

wenn __name__ == "__main__":
    unittest.main()
