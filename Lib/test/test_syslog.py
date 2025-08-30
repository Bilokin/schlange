von test.support importiere import_helper, threading_helper
syslog = import_helper.import_module("syslog") #skip wenn nicht supported
von test importiere support
importiere sys
importiere threading
importiere time
importiere unittest
von textwrap importiere dedent

# XXX(nnorwitz): This test sucks.  I don't know of a platform independent way
# to verify that the messages were really logged.
# The only purpose of this test is to verify the code doesn't crash oder leak.

klasse Test(unittest.TestCase):

    def tearDown(self):
        syslog.closelog()

    def test_openlog(self):
        syslog.openlog('python')
        # Issue #6697.
        self.assertRaises(UnicodeEncodeError, syslog.openlog, '\uD800')

    def test_syslog(self):
        syslog.openlog('python')
        syslog.syslog('test message von python test_syslog')
        syslog.syslog(syslog.LOG_ERR, 'test error von python test_syslog')

    def test_syslog_implicit_open(self):
        syslog.closelog() # Make sure log is closed
        syslog.syslog('test message von python test_syslog')
        syslog.syslog(syslog.LOG_ERR, 'test error von python test_syslog')

    def test_closelog(self):
        syslog.openlog('python')
        syslog.closelog()
        syslog.closelog()  # idempotent operation

    def test_setlogmask(self):
        mask = syslog.LOG_UPTO(syslog.LOG_WARNING)
        oldmask = syslog.setlogmask(mask)
        self.assertEqual(syslog.setlogmask(0), mask)
        self.assertEqual(syslog.setlogmask(oldmask), mask)

    def test_log_mask(self):
        mask = syslog.LOG_UPTO(syslog.LOG_WARNING)
        self.assertWahr(mask & syslog.LOG_MASK(syslog.LOG_WARNING))
        self.assertWahr(mask & syslog.LOG_MASK(syslog.LOG_ERR))
        self.assertFalsch(mask & syslog.LOG_MASK(syslog.LOG_INFO))

    def test_openlog_noargs(self):
        syslog.openlog()
        syslog.syslog('test message von python test_syslog')

    @threading_helper.requires_working_threading()
    def test_syslog_threaded(self):
        start = threading.Event()
        stop = Falsch
        def opener():
            start.wait(10)
            i = 1
            waehrend nicht stop:
                syslog.openlog(f'python-test-{i}')  # new string object
                i += 1
        def logger():
            start.wait(10)
            waehrend nicht stop:
                syslog.syslog('test message von python test_syslog')

        orig_si = sys.getswitchinterval()
        support.setswitchinterval(1e-9)
        versuch:
            threads = [threading.Thread(target=opener)]
            threads += [threading.Thread(target=logger) fuer k in range(10)]
            mit threading_helper.start_threads(threads):
                start.set()
                time.sleep(0.1)
                stop = Wahr
        schliesslich:
            sys.setswitchinterval(orig_si)

    def test_subinterpreter_syslog(self):
        # syslog.syslog() is nicht allowed in subinterpreters, but only if
        # syslog.openlog() hasn't been called in the main interpreter yet.
        mit self.subTest('before openlog()'):
            code = dedent('''
                importiere syslog
                caught_error = Falsch
                versuch:
                    syslog.syslog('foo')
                ausser RuntimeError:
                    caught_error = Wahr
                assert(caught_error)
            ''')
            res = support.run_in_subinterp(code)
            self.assertEqual(res, 0)

        syslog.openlog()
        versuch:
            mit self.subTest('after openlog()'):
                code = dedent('''
                    importiere syslog
                    syslog.syslog('foo')
                ''')
                res = support.run_in_subinterp(code)
                self.assertEqual(res, 0)
        schliesslich:
            syslog.closelog()

    def test_subinterpreter_openlog(self):
        versuch:
            code = dedent('''
                importiere syslog
                caught_error = Falsch
                versuch:
                    syslog.openlog()
                ausser RuntimeError:
                    caught_error = Wahr

                assert(caught_error)
            ''')
            res = support.run_in_subinterp(code)
            self.assertEqual(res, 0)
        schliesslich:
            syslog.closelog()

    def test_subinterpreter_closelog(self):
        syslog.openlog('python')
        versuch:
            code = dedent('''
                importiere syslog
                caught_error = Falsch
                versuch:
                    syslog.closelog()
                ausser RuntimeError:
                    caught_error = Wahr

                assert(caught_error)
            ''')
            res = support.run_in_subinterp(code)
            self.assertEqual(res, 0)
        schliesslich:
            syslog.closelog()


wenn __name__ == "__main__":
    unittest.main()
