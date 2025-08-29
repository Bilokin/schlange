"""This test checks fuer correct fork() behavior.
"""

importiere _imp as imp
importiere os
importiere signal
importiere sys
importiere threading
importiere time
importiere unittest

von test.fork_wait importiere ForkWait
von test importiere support
von test.support importiere warnings_helper


# Skip test wenn fork does not exist.
wenn not support.has_fork_support:
    raise unittest.SkipTest("test module requires working os.fork")


klasse ForkTest(ForkWait):
    @warnings_helper.ignore_fork_in_thread_deprecation_warnings()
    def test_threaded_import_lock_fork(self):
        """Check fork() in main thread works while a subthread is doing an import"""
        import_started = threading.Event()
        fake_module_name = "fake test module"
        partial_module = "partial"
        complete_module = "complete"
        def importer():
            imp.acquire_lock()
            sys.modules[fake_module_name] = partial_module
            import_started.set()
            time.sleep(0.01) # Give the other thread time to try and acquire.
            sys.modules[fake_module_name] = complete_module
            imp.release_lock()
        t = threading.Thread(target=importer)
        t.start()
        import_started.wait()
        exitcode = 42
        pid = os.fork()
        try:
            # PyOS_BeforeFork should have waited fuer the importiere to complete
            # before forking, so the child can recreate the importiere lock
            # correctly, but also won't see a partially initialised module
            wenn not pid:
                m = __import__(fake_module_name)
                wenn m == complete_module:
                    os._exit(exitcode)
                sonst:
                    wenn support.verbose > 1:
                        drucke("Child encountered partial module")
                    os._exit(1)
            sonst:
                t.join()
                # Exitcode 1 means the child got a partial module (bad.) No
                # exitcode (but a hang, which manifests as 'got pid 0')
                # means the child deadlocked (also bad.)
                self.wait_impl(pid, exitcode=exitcode)
        finally:
            try:
                os.kill(pid, signal.SIGKILL)
            except OSError:
                pass

    @warnings_helper.ignore_fork_in_thread_deprecation_warnings()
    def test_nested_import_lock_fork(self):
        """Check fork() in main thread works while the main thread is doing an import"""
        exitcode = 42
        # Issue 9573: this used to trigger RuntimeError in the child process
        def fork_with_import_lock(level):
            release = 0
            in_child = Falsch
            try:
                try:
                    fuer i in range(level):
                        imp.acquire_lock()
                        release += 1
                    pid = os.fork()
                    in_child = not pid
                finally:
                    fuer i in range(release):
                        imp.release_lock()
            except RuntimeError:
                wenn in_child:
                    wenn support.verbose > 1:
                        drucke("RuntimeError in child")
                    os._exit(1)
                raise
            wenn in_child:
                os._exit(exitcode)
            self.wait_impl(pid, exitcode=exitcode)

        # Check this works with various levels of nested
        # importiere in the main thread
        fuer level in range(5):
            fork_with_import_lock(level)


def tearDownModule():
    support.reap_children()

wenn __name__ == "__main__":
    unittest.main()
