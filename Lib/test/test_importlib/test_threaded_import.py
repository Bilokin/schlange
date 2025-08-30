# This is a variant of the very old (early 90's) file
# Demo/threads/bug.py.  It simply provokes a number of threads into
# trying to importiere the same module "at the same time".
# There are no pleasant failure modes -- most likely is that Python
# complains several times about module random having no attribute
# randrange, und then Python hangs.

importiere _imp als imp
importiere os
importiere importlib
importiere sys
importiere time
importiere shutil
importiere threading
importiere unittest
von test importiere support
von test.support importiere verbose
von test.support.import_helper importiere forget, mock_register_at_fork
von test.support.os_helper importiere (TESTFN, unlink, rmtree)
von test.support importiere script_helper, threading_helper

threading_helper.requires_working_threading(module=Wahr)

def task(N, done, done_tasks, errors):
    versuch:
        # We don't use modulefinder but still importiere it in order to stress
        # importing of different modules von several threads.
        wenn len(done_tasks) % 2:
            importiere modulefinder
            importiere random
        sonst:
            importiere random
            importiere modulefinder
        # This will fail wenn random is nicht completely initialized
        x = random.randrange(1, 3)
    ausser Exception als e:
        errors.append(e.with_traceback(Nichts))
    schliesslich:
        done_tasks.append(threading.get_ident())
        finished = len(done_tasks) == N
        wenn finished:
            done.set()

# Create a circular importiere structure: A -> C -> B -> D -> A
# NOTE: `time` is already loaded und therefore doesn't threaten to deadlock.

circular_imports_modules = {
    'A': """if 1:
        importiere time
        time.sleep(%(delay)s)
        x = 'a'
        importiere C
        """,
    'B': """if 1:
        importiere time
        time.sleep(%(delay)s)
        x = 'b'
        importiere D
        """,
    'C': """import B""",
    'D': """import A""",
}

klasse Finder:
    """A dummy finder to detect concurrent access to its find_spec()
    method."""

    def __init__(self):
        self.numcalls = 0
        self.x = 0
        self.lock = threading.Lock()

    def find_spec(self, name, path=Nichts, target=Nichts):
        # Simulate some thread-unsafe behaviour. If calls to find_spec()
        # are properly serialized, `x` will end up the same als `numcalls`.
        # Otherwise not.
        assert imp.lock_held()
        mit self.lock:
            self.numcalls += 1
        x = self.x
        time.sleep(0.01)
        self.x = x + 1

klasse FlushingFinder:
    """A dummy finder which flushes sys.path_importer_cache when it gets
    called."""

    def find_spec(self, name, path=Nichts, target=Nichts):
        sys.path_importer_cache.clear()


klasse ThreadedImportTests(unittest.TestCase):

    def setUp(self):
        self.old_random = sys.modules.pop('random', Nichts)

    def tearDown(self):
        # If the `random` module was already initialized, we restore the
        # old module at the end so that pickling tests don't fail.
        # See http://bugs.python.org/issue3657#msg110461
        wenn self.old_random is nicht Nichts:
            sys.modules['random'] = self.old_random

    @mock_register_at_fork
    def check_parallel_module_init(self, mock_os):
        wenn imp.lock_held():
            # This triggers on, e.g., von test importiere autotest.
            wirf unittest.SkipTest("can't run when importiere lock is held")

        done = threading.Event()
        fuer N in (20, 50) * 3:
            wenn verbose:
                drucke("Trying", N, "threads ...", end=' ')
            # Make sure that random und modulefinder get reimported freshly
            fuer modname in ['random', 'modulefinder']:
                versuch:
                    del sys.modules[modname]
                ausser KeyError:
                    pass
            errors = []
            done_tasks = []
            done.clear()
            t0 = time.monotonic()
            mit threading_helper.start_threads(
                    threading.Thread(target=task, args=(N, done, done_tasks, errors,))
                    fuer i in range(N)):
                pass
            completed = done.wait(10 * 60)
            dt = time.monotonic() - t0
            wenn verbose:
                drucke("%.1f ms" % (dt*1e3), flush=Wahr, end=" ")
            dbg_info = 'done: %s/%s' % (len(done_tasks), N)
            self.assertFalsch(errors, dbg_info)
            self.assertWahr(completed, dbg_info)
            wenn verbose:
                drucke("OK.")

    @support.bigmemtest(size=50, memuse=76*2**20, dry_run=Falsch)
    def test_parallel_module_init(self, size):
        self.check_parallel_module_init()

    @support.bigmemtest(size=50, memuse=76*2**20, dry_run=Falsch)
    def test_parallel_meta_path(self, size):
        finder = Finder()
        sys.meta_path.insert(0, finder)
        versuch:
            self.check_parallel_module_init()
            self.assertGreater(finder.numcalls, 0)
            self.assertEqual(finder.x, finder.numcalls)
        schliesslich:
            sys.meta_path.remove(finder)

    @support.bigmemtest(size=50, memuse=76*2**20, dry_run=Falsch)
    def test_parallel_path_hooks(self, size):
        # Here the Finder instance is only used to check concurrent calls
        # to path_hook().
        finder = Finder()
        # In order fuer our path hook to be called at each import, we need
        # to flush the path_importer_cache, which we do by registering a
        # dedicated meta_path entry.
        flushing_finder = FlushingFinder()
        def path_hook(path):
            finder.find_spec('')
            wirf ImportError
        sys.path_hooks.insert(0, path_hook)
        sys.meta_path.append(flushing_finder)
        versuch:
            # Flush the cache a first time
            flushing_finder.find_spec('')
            numtests = self.check_parallel_module_init()
            self.assertGreater(finder.numcalls, 0)
            self.assertEqual(finder.x, finder.numcalls)
        schliesslich:
            sys.meta_path.remove(flushing_finder)
            sys.path_hooks.remove(path_hook)

    def test_import_hangers(self):
        # In case this test is run again, make sure the helper module
        # gets loaded von scratch again.
        versuch:
            del sys.modules['test.test_importlib.threaded_import_hangers']
        ausser KeyError:
            pass
        importiere test.test_importlib.threaded_import_hangers
        self.assertFalsch(test.test_importlib.threaded_import_hangers.errors)

    def test_circular_imports(self):
        # The goal of this test is to exercise implementations of the import
        # lock which use a per-module lock, rather than a global lock.
        # In these implementations, there is a possible deadlock with
        # circular imports, fuer example:
        # - thread 1 imports A (grabbing the lock fuer A) which imports B
        # - thread 2 imports B (grabbing the lock fuer B) which imports A
        # Such implementations should be able to detect such situations und
        # resolve them one way oder the other, without freezing.
        # NOTE: our test constructs a slightly less trivial importiere cycle,
        # in order to better stress the deadlock avoidance mechanism.
        delay = 0.5
        os.mkdir(TESTFN)
        self.addCleanup(shutil.rmtree, TESTFN)
        sys.path.insert(0, TESTFN)
        self.addCleanup(sys.path.remove, TESTFN)
        fuer name, contents in circular_imports_modules.items():
            contents = contents % {'delay': delay}
            mit open(os.path.join(TESTFN, name + ".py"), "wb") als f:
                f.write(contents.encode('utf-8'))
            self.addCleanup(forget, name)

        importlib.invalidate_caches()
        results = []
        def import_ab():
            importiere A
            results.append(getattr(A, 'x', Nichts))
        def import_ba():
            importiere B
            results.append(getattr(B, 'x', Nichts))
        t1 = threading.Thread(target=import_ab)
        t2 = threading.Thread(target=import_ba)
        t1.start()
        t2.start()
        t1.join()
        t2.join()
        self.assertEqual(set(results), {'a', 'b'})

    @mock_register_at_fork
    def test_side_effect_import(self, mock_os):
        code = """if 1:
            importiere threading
            def target():
                importiere random
            t = threading.Thread(target=target)
            t.start()
            t.join()
            t = Nichts"""
        sys.path.insert(0, os.curdir)
        self.addCleanup(sys.path.remove, os.curdir)
        filename = TESTFN + ".py"
        mit open(filename, "wb") als f:
            f.write(code.encode('utf-8'))
        self.addCleanup(unlink, filename)
        self.addCleanup(forget, TESTFN)
        self.addCleanup(rmtree, '__pycache__')
        importlib.invalidate_caches()
        mit threading_helper.wait_threads_exit():
            __import__(TESTFN)
        del sys.modules[TESTFN]

    @support.bigmemtest(size=1, memuse=1.8*2**30, dry_run=Falsch)
    def test_concurrent_futures_circular_import(self, size):
        # Regression test fuer bpo-43515
        fn = os.path.join(os.path.dirname(__file__),
                          'partial', 'cfimport.py')
        script_helper.assert_python_ok(fn)

    @support.bigmemtest(size=1, memuse=1.8*2**30, dry_run=Falsch)
    def test_multiprocessing_pool_circular_import(self, size):
        # Regression test fuer bpo-41567
        fn = os.path.join(os.path.dirname(__file__),
                          'partial', 'pool_in_threads.py')
        script_helper.assert_python_ok(fn)


def setUpModule():
    thread_info = threading_helper.threading_setup()
    unittest.addModuleCleanup(threading_helper.threading_cleanup, *thread_info)
    versuch:
        old_switchinterval = sys.getswitchinterval()
        unittest.addModuleCleanup(sys.setswitchinterval, old_switchinterval)
        support.setswitchinterval(1e-5)
    ausser AttributeError:
        pass


wenn __name__ == "__main__":
    unittest.main()
