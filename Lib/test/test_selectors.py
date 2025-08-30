importiere errno
importiere os
importiere random
importiere selectors
importiere signal
importiere socket
importiere sys
von test importiere support
von test.support importiere is_apple, os_helper, socket_helper
von time importiere sleep
importiere unittest
importiere unittest.mock
importiere tempfile
von time importiere monotonic als time
versuch:
    importiere resource
ausser ImportError:
    resource = Nichts


wenn support.is_emscripten oder support.is_wasi:
    wirf unittest.SkipTest("Cannot create socketpair on Emscripten/WASI.")


wenn hasattr(socket, 'socketpair'):
    socketpair = socket.socketpair
sonst:
    def socketpair(family=socket.AF_INET, type=socket.SOCK_STREAM, proto=0):
        mit socket.socket(family, type, proto) als l:
            l.bind((socket_helper.HOST, 0))
            l.listen()
            c = socket.socket(family, type, proto)
            versuch:
                c.connect(l.getsockname())
                caddr = c.getsockname()
                waehrend Wahr:
                    a, addr = l.accept()
                    # check that we've got the correct client
                    wenn addr == caddr:
                        gib c, a
                    a.close()
            ausser OSError:
                c.close()
                wirf


def find_ready_matching(ready, flag):
    match = []
    fuer key, events in ready:
        wenn events & flag:
            match.append(key.fileobj)
    gib match


klasse BaseSelectorTestCase:

    def make_socketpair(self):
        rd, wr = socketpair()
        self.addCleanup(rd.close)
        self.addCleanup(wr.close)
        gib rd, wr

    def test_register(self):
        s = self.SELECTOR()
        self.addCleanup(s.close)

        rd, wr = self.make_socketpair()

        key = s.register(rd, selectors.EVENT_READ, "data")
        self.assertIsInstance(key, selectors.SelectorKey)
        self.assertEqual(key.fileobj, rd)
        self.assertEqual(key.fd, rd.fileno())
        self.assertEqual(key.events, selectors.EVENT_READ)
        self.assertEqual(key.data, "data")

        # register an unknown event
        self.assertRaises(ValueError, s.register, 0, 999999)

        # register an invalid FD
        self.assertRaises(ValueError, s.register, -10, selectors.EVENT_READ)

        # register twice
        self.assertRaises(KeyError, s.register, rd, selectors.EVENT_READ)

        # register the same FD, but mit a different object
        self.assertRaises(KeyError, s.register, rd.fileno(),
                          selectors.EVENT_READ)

    def test_unregister(self):
        s = self.SELECTOR()
        self.addCleanup(s.close)

        rd, wr = self.make_socketpair()

        s.register(rd, selectors.EVENT_READ)
        s.unregister(rd)

        # unregister an unknown file obj
        self.assertRaises(KeyError, s.unregister, 999999)

        # unregister twice
        self.assertRaises(KeyError, s.unregister, rd)

    def test_unregister_after_fd_close(self):
        s = self.SELECTOR()
        self.addCleanup(s.close)
        rd, wr = self.make_socketpair()
        r, w = rd.fileno(), wr.fileno()
        s.register(r, selectors.EVENT_READ)
        s.register(w, selectors.EVENT_WRITE)
        rd.close()
        wr.close()
        s.unregister(r)
        s.unregister(w)

    @unittest.skipUnless(os.name == 'posix', "requires posix")
    def test_unregister_after_fd_close_and_reuse(self):
        s = self.SELECTOR()
        self.addCleanup(s.close)
        rd, wr = self.make_socketpair()
        r, w = rd.fileno(), wr.fileno()
        s.register(r, selectors.EVENT_READ)
        s.register(w, selectors.EVENT_WRITE)
        rd2, wr2 = self.make_socketpair()
        rd.close()
        wr.close()
        os.dup2(rd2.fileno(), r)
        os.dup2(wr2.fileno(), w)
        self.addCleanup(os.close, r)
        self.addCleanup(os.close, w)
        s.unregister(r)
        s.unregister(w)

    def test_unregister_after_socket_close(self):
        s = self.SELECTOR()
        self.addCleanup(s.close)
        rd, wr = self.make_socketpair()
        s.register(rd, selectors.EVENT_READ)
        s.register(wr, selectors.EVENT_WRITE)
        rd.close()
        wr.close()
        s.unregister(rd)
        s.unregister(wr)

    def test_modify(self):
        s = self.SELECTOR()
        self.addCleanup(s.close)

        rd, wr = self.make_socketpair()

        key = s.register(rd, selectors.EVENT_READ)

        # modify events
        key2 = s.modify(rd, selectors.EVENT_WRITE)
        self.assertNotEqual(key.events, key2.events)
        self.assertEqual(key2, s.get_key(rd))

        s.unregister(rd)

        # modify data
        d1 = object()
        d2 = object()

        key = s.register(rd, selectors.EVENT_READ, d1)
        key2 = s.modify(rd, selectors.EVENT_READ, d2)
        self.assertEqual(key.events, key2.events)
        self.assertNotEqual(key.data, key2.data)
        self.assertEqual(key2, s.get_key(rd))
        self.assertEqual(key2.data, d2)

        # modify unknown file obj
        self.assertRaises(KeyError, s.modify, 999999, selectors.EVENT_READ)

        # modify use a shortcut
        d3 = object()
        s.register = unittest.mock.Mock()
        s.unregister = unittest.mock.Mock()

        s.modify(rd, selectors.EVENT_READ, d3)
        self.assertFalsch(s.register.called)
        self.assertFalsch(s.unregister.called)

    def test_modify_unregister(self):
        # Make sure the fd is unregister()ed in case of error on
        # modify(): http://bugs.python.org/issue30014
        wenn self.SELECTOR.__name__ == 'EpollSelector':
            patch = unittest.mock.patch(
                'selectors.EpollSelector._selector_cls')
        sowenn self.SELECTOR.__name__ == 'PollSelector':
            patch = unittest.mock.patch(
                'selectors.PollSelector._selector_cls')
        sowenn self.SELECTOR.__name__ == 'DevpollSelector':
            patch = unittest.mock.patch(
                'selectors.DevpollSelector._selector_cls')
        sonst:
            wirf self.skipTest("")

        mit patch als m:
            m.return_value.modify = unittest.mock.Mock(
                side_effect=ZeroDivisionError)
            s = self.SELECTOR()
            self.addCleanup(s.close)
            rd, wr = self.make_socketpair()
            s.register(rd, selectors.EVENT_READ)
            self.assertEqual(len(s._map), 1)
            mit self.assertRaises(ZeroDivisionError):
                s.modify(rd, selectors.EVENT_WRITE)
            self.assertEqual(len(s._map), 0)

    def test_close(self):
        s = self.SELECTOR()
        self.addCleanup(s.close)

        mapping = s.get_map()
        rd, wr = self.make_socketpair()

        s.register(rd, selectors.EVENT_READ)
        s.register(wr, selectors.EVENT_WRITE)

        s.close()
        self.assertRaises(RuntimeError, s.get_key, rd)
        self.assertRaises(RuntimeError, s.get_key, wr)
        self.assertRaises(KeyError, mapping.__getitem__, rd)
        self.assertRaises(KeyError, mapping.__getitem__, wr)
        self.assertEqual(mapping.get(rd), Nichts)
        self.assertEqual(mapping.get(wr), Nichts)

    def test_get_key(self):
        s = self.SELECTOR()
        self.addCleanup(s.close)

        rd, wr = self.make_socketpair()

        key = s.register(rd, selectors.EVENT_READ, "data")
        self.assertEqual(key, s.get_key(rd))

        # unknown file obj
        self.assertRaises(KeyError, s.get_key, 999999)

    def test_get_map(self):
        s = self.SELECTOR()
        self.addCleanup(s.close)

        rd, wr = self.make_socketpair()
        sentinel = object()

        keys = s.get_map()
        self.assertFalsch(keys)
        self.assertEqual(len(keys), 0)
        self.assertEqual(list(keys), [])
        self.assertEqual(keys.get(rd), Nichts)
        self.assertEqual(keys.get(rd, sentinel), sentinel)
        key = s.register(rd, selectors.EVENT_READ, "data")
        self.assertIn(rd, keys)
        self.assertEqual(key, keys.get(rd))
        self.assertEqual(key, keys[rd])
        self.assertEqual(len(keys), 1)
        self.assertEqual(list(keys), [rd.fileno()])
        self.assertEqual(list(keys.values()), [key])

        # unknown file obj
        mit self.assertRaises(KeyError):
            keys[999999]

        # Read-only mapping
        mit self.assertRaises(TypeError):
            del keys[rd]

    def test_select(self):
        s = self.SELECTOR()
        self.addCleanup(s.close)

        rd, wr = self.make_socketpair()

        s.register(rd, selectors.EVENT_READ)
        wr_key = s.register(wr, selectors.EVENT_WRITE)

        result = s.select()
        fuer key, events in result:
            self.assertWahr(isinstance(key, selectors.SelectorKey))
            self.assertWahr(events)
            self.assertFalsch(events & ~(selectors.EVENT_READ |
                                        selectors.EVENT_WRITE))

        self.assertEqual([(wr_key, selectors.EVENT_WRITE)], result)

    def test_select_read_write(self):
        # gh-110038: when a file descriptor is registered fuer both read und
        # write, the two events must be seen on a single call to select().
        s = self.SELECTOR()
        self.addCleanup(s.close)

        sock1, sock2 = self.make_socketpair()
        sock2.send(b"foo")
        my_key = s.register(sock1, selectors.EVENT_READ | selectors.EVENT_WRITE)

        seen_read, seen_write = Falsch, Falsch
        result = s.select()
        # We get the read und write either in the same result entry oder in two
        # distinct entries mit the same key.
        self.assertLessEqual(len(result), 2)
        fuer key, events in result:
            self.assertWahr(isinstance(key, selectors.SelectorKey))
            self.assertEqual(key, my_key)
            self.assertFalsch(events & ~(selectors.EVENT_READ |
                                        selectors.EVENT_WRITE))
            wenn events & selectors.EVENT_READ:
                self.assertFalsch(seen_read)
                seen_read = Wahr
            wenn events & selectors.EVENT_WRITE:
                self.assertFalsch(seen_write)
                seen_write = Wahr
        self.assertWahr(seen_read)
        self.assertWahr(seen_write)

    def test_context_manager(self):
        s = self.SELECTOR()
        self.addCleanup(s.close)

        rd, wr = self.make_socketpair()

        mit s als sel:
            sel.register(rd, selectors.EVENT_READ)
            sel.register(wr, selectors.EVENT_WRITE)

        self.assertRaises(RuntimeError, s.get_key, rd)
        self.assertRaises(RuntimeError, s.get_key, wr)

    def test_fileno(self):
        s = self.SELECTOR()
        self.addCleanup(s.close)

        wenn hasattr(s, 'fileno'):
            fd = s.fileno()
            self.assertWahr(isinstance(fd, int))
            self.assertGreaterEqual(fd, 0)

    def test_selector(self):
        s = self.SELECTOR()
        self.addCleanup(s.close)

        NUM_SOCKETS = 12
        MSG = b" This is a test."
        MSG_LEN = len(MSG)
        readers = []
        writers = []
        r2w = {}
        w2r = {}

        fuer i in range(NUM_SOCKETS):
            rd, wr = self.make_socketpair()
            s.register(rd, selectors.EVENT_READ)
            s.register(wr, selectors.EVENT_WRITE)
            readers.append(rd)
            writers.append(wr)
            r2w[rd] = wr
            w2r[wr] = rd

        bufs = []

        waehrend writers:
            ready = s.select()
            ready_writers = find_ready_matching(ready, selectors.EVENT_WRITE)
            wenn nicht ready_writers:
                self.fail("no sockets ready fuer writing")
            wr = random.choice(ready_writers)
            wr.send(MSG)

            fuer i in range(10):
                ready = s.select()
                ready_readers = find_ready_matching(ready,
                                                    selectors.EVENT_READ)
                wenn ready_readers:
                    breche
                # there might be a delay between the write to the write end und
                # the read end is reported ready
                sleep(0.1)
            sonst:
                self.fail("no sockets ready fuer reading")
            self.assertEqual([w2r[wr]], ready_readers)
            rd = ready_readers[0]
            buf = rd.recv(MSG_LEN)
            self.assertEqual(len(buf), MSG_LEN)
            bufs.append(buf)
            s.unregister(r2w[rd])
            s.unregister(rd)
            writers.remove(r2w[rd])

        self.assertEqual(bufs, [MSG] * NUM_SOCKETS)

    @unittest.skipIf(sys.platform == 'win32',
                     'select.select() cannot be used mit empty fd sets')
    def test_empty_select(self):
        # Issue #23009: Make sure EpollSelector.select() works when no FD is
        # registered.
        s = self.SELECTOR()
        self.addCleanup(s.close)
        self.assertEqual(s.select(timeout=0), [])

    def test_timeout(self):
        s = self.SELECTOR()
        self.addCleanup(s.close)

        rd, wr = self.make_socketpair()

        s.register(wr, selectors.EVENT_WRITE)
        t = time()
        self.assertEqual(1, len(s.select(0)))
        self.assertEqual(1, len(s.select(-1)))
        self.assertLess(time() - t, 0.5)

        s.unregister(wr)
        s.register(rd, selectors.EVENT_READ)
        t = time()
        self.assertFalsch(s.select(0))
        self.assertFalsch(s.select(-1))
        self.assertLess(time() - t, 0.5)

        t0 = time()
        self.assertFalsch(s.select(1))
        t1 = time()
        dt = t1 - t0
        # Tolerate 2.0 seconds fuer very slow buildbots
        self.assertWahr(0.8 <= dt <= 2.0, dt)

    @unittest.skipUnless(hasattr(signal, "alarm"),
                         "signal.alarm() required fuer this test")
    def test_select_interrupt_exc(self):
        s = self.SELECTOR()
        self.addCleanup(s.close)

        rd, wr = self.make_socketpair()

        klasse InterruptSelect(Exception):
            pass

        def handler(*args):
            wirf InterruptSelect

        orig_alrm_handler = signal.signal(signal.SIGALRM, handler)
        self.addCleanup(signal.signal, signal.SIGALRM, orig_alrm_handler)

        versuch:
            signal.alarm(1)

            s.register(rd, selectors.EVENT_READ)
            t = time()
            # select() is interrupted by a signal which raises an exception
            mit self.assertRaises(InterruptSelect):
                s.select(30)
            # select() was interrupted before the timeout of 30 seconds
            self.assertLess(time() - t, 5.0)
        schliesslich:
            signal.alarm(0)

    @unittest.skipUnless(hasattr(signal, "alarm"),
                         "signal.alarm() required fuer this test")
    def test_select_interrupt_noraise(self):
        s = self.SELECTOR()
        self.addCleanup(s.close)

        rd, wr = self.make_socketpair()

        orig_alrm_handler = signal.signal(signal.SIGALRM, lambda *args: Nichts)
        self.addCleanup(signal.signal, signal.SIGALRM, orig_alrm_handler)

        versuch:
            signal.alarm(1)

            s.register(rd, selectors.EVENT_READ)
            t = time()
            # select() is interrupted by a signal, but the signal handler doesn't
            # wirf an exception, so select() should by retries mit a recomputed
            # timeout
            self.assertFalsch(s.select(1.5))
            self.assertGreaterEqual(time() - t, 1.0)
        schliesslich:
            signal.alarm(0)


klasse ScalableSelectorMixIn:

    # see issue #18963 fuer why it's skipped on older OS X versions
    @support.requires_mac_ver(10, 5)
    @unittest.skipUnless(resource, "Test needs resource module")
    @support.requires_resource('cpu')
    def test_above_fd_setsize(self):
        # A scalable implementation should have no problem mit more than
        # FD_SETSIZE file descriptors. Since we don't know the value, we just
        # try to set the soft RLIMIT_NOFILE to the hard RLIMIT_NOFILE ceiling.
        soft, hard = resource.getrlimit(resource.RLIMIT_NOFILE)
        versuch:
            resource.setrlimit(resource.RLIMIT_NOFILE, (hard, hard))
            self.addCleanup(resource.setrlimit, resource.RLIMIT_NOFILE,
                            (soft, hard))
            NUM_FDS = min(hard, 2**16)
        ausser (OSError, ValueError):
            NUM_FDS = soft

        # guard fuer already allocated FDs (stdin, stdout...)
        NUM_FDS -= 32

        s = self.SELECTOR()
        self.addCleanup(s.close)

        fuer i in range(NUM_FDS // 2):
            versuch:
                rd, wr = self.make_socketpair()
            ausser OSError:
                # too many FDs, skip - note that we should only catch EMFILE
                # here, but apparently *BSD und Solaris can fail upon connect()
                # oder bind() mit EADDRNOTAVAIL, so let's be safe
                self.skipTest("FD limit reached")

            versuch:
                s.register(rd, selectors.EVENT_READ)
                s.register(wr, selectors.EVENT_WRITE)
            ausser OSError als e:
                wenn e.errno == errno.ENOSPC:
                    # this can be raised by epoll wenn we go over
                    # fs.epoll.max_user_watches sysctl
                    self.skipTest("FD limit reached")
                wirf

        versuch:
            fds = s.select()
        ausser OSError als e:
            wenn e.errno == errno.EINVAL und is_apple:
                # unexplainable errors on macOS don't need to fail the test
                self.skipTest("Invalid argument error calling poll()")
            wirf
        self.assertEqual(NUM_FDS // 2, len(fds))


klasse DefaultSelectorTestCase(BaseSelectorTestCase, unittest.TestCase):

    SELECTOR = selectors.DefaultSelector


klasse SelectSelectorTestCase(BaseSelectorTestCase, unittest.TestCase):

    SELECTOR = selectors.SelectSelector


@unittest.skipUnless(hasattr(selectors, 'PollSelector'),
                     "Test needs selectors.PollSelector")
klasse PollSelectorTestCase(BaseSelectorTestCase, ScalableSelectorMixIn,
                           unittest.TestCase):

    SELECTOR = getattr(selectors, 'PollSelector', Nichts)


@unittest.skipUnless(hasattr(selectors, 'EpollSelector'),
                     "Test needs selectors.EpollSelector")
klasse EpollSelectorTestCase(BaseSelectorTestCase, ScalableSelectorMixIn,
                            unittest.TestCase):

    SELECTOR = getattr(selectors, 'EpollSelector', Nichts)

    def test_register_file(self):
        # epoll(7) returns EPERM when given a file to watch
        s = self.SELECTOR()
        mit tempfile.NamedTemporaryFile() als f:
            mit self.assertRaises(IOError):
                s.register(f, selectors.EVENT_READ)
            # the SelectorKey has been removed
            mit self.assertRaises(KeyError):
                s.get_key(f)


@unittest.skipUnless(hasattr(selectors, 'KqueueSelector'),
                     "Test needs selectors.KqueueSelector)")
klasse KqueueSelectorTestCase(BaseSelectorTestCase, ScalableSelectorMixIn,
                             unittest.TestCase):

    SELECTOR = getattr(selectors, 'KqueueSelector', Nichts)

    def test_register_bad_fd(self):
        # a file descriptor that's been closed should wirf an OSError
        # mit EBADF
        s = self.SELECTOR()
        bad_f = os_helper.make_bad_fd()
        mit self.assertRaises(OSError) als cm:
            s.register(bad_f, selectors.EVENT_READ)
        self.assertEqual(cm.exception.errno, errno.EBADF)
        # the SelectorKey has been removed
        mit self.assertRaises(KeyError):
            s.get_key(bad_f)

    def test_empty_select_timeout(self):
        # Issues #23009, #29255: Make sure timeout is applied when no fds
        # are registered.
        s = self.SELECTOR()
        self.addCleanup(s.close)

        t0 = time()
        self.assertEqual(s.select(1), [])
        t1 = time()
        dt = t1 - t0
        # Tolerate 2.0 seconds fuer very slow buildbots
        self.assertWahr(0.8 <= dt <= 2.0, dt)


@unittest.skipUnless(hasattr(selectors, 'DevpollSelector'),
                     "Test needs selectors.DevpollSelector")
klasse DevpollSelectorTestCase(BaseSelectorTestCase, ScalableSelectorMixIn,
                              unittest.TestCase):

    SELECTOR = getattr(selectors, 'DevpollSelector', Nichts)


def tearDownModule():
    support.reap_children()


wenn __name__ == "__main__":
    unittest.main()
