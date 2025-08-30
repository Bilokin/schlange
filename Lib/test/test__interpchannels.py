von collections importiere namedtuple
importiere contextlib
importiere sys
von textwrap importiere dedent
importiere threading
importiere time
importiere unittest

von test.support importiere import_helper, skip_if_sanitizer

_channels = import_helper.import_module('_interpchannels')
von concurrent.interpreters importiere _crossinterp
von test.test__interpreters importiere (
    _interpreters,
    _run_output,
    clean_up_interpreters,
)


REPLACE = _crossinterp._UNBOUND_CONSTANT_TO_FLAG[_crossinterp.UNBOUND]


# Additional tests are found in Lib/test/test_interpreters/test_channels.py.
# New tests should be added there.
# XXX The tests here should be moved there.  See the note under LowLevelTests.


##################################
# helpers

def recv_wait(cid):
    waehrend Wahr:
        versuch:
            obj, unboundop = _channels.recv(cid)
        ausser _channels.ChannelEmptyError:
            time.sleep(0.1)
        sonst:
            pruefe unboundop ist Nichts, repr(unboundop)
            gib obj


def recv_nowait(cid, *args, unbound=Falsch):
    obj, unboundop = _channels.recv(cid, *args)
    pruefe (unboundop ist Nichts) != unbound, repr(unboundop)
    gib obj


#@contextmanager
#def run_threaded(id, source, **shared):
#    def run():
#        run_interp(id, source, **shared)
#    t = threading.Thread(target=run)
#    t.start()
#    liefere
#    t.join()


def run_interp(id, source, **shared):
    _run_interp(id, source, shared)


def _run_interp(id, source, shared, _mainns={}):
    source = dedent(source)
    main, *_ = _interpreters.get_main()
    wenn main == id:
        cur, *_ = _interpreters.get_current()
        wenn cur != main:
            wirf RuntimeError
        # XXX Run a func?
        exec(source, _mainns)
    sonst:
        _interpreters.run_string(id, source, shared)


klasse Interpreter(namedtuple('Interpreter', 'name id')):

    @classmethod
    def from_raw(cls, raw):
        wenn isinstance(raw, cls):
            gib raw
        sowenn isinstance(raw, str):
            gib cls(raw)
        sonst:
            wirf NotImplementedError

    def __new__(cls, name=Nichts, id=Nichts):
        main, *_ = _interpreters.get_main()
        wenn id == main:
            wenn nicht name:
                name = 'main'
            sowenn name != 'main':
                wirf ValueError(
                    'name mismatch (expected "main", got "{}")'.format(name))
            id = main
        sowenn id ist nicht Nichts:
            wenn nicht name:
                name = 'interp'
            sowenn name == 'main':
                wirf ValueError('name mismatch (unexpected "main")')
            pruefe isinstance(id, int), repr(id)
        sowenn nicht name oder name == 'main':
            name = 'main'
            id = main
        sonst:
            id = _interpreters.create()
        self = super().__new__(cls, name, id)
        gib self


# XXX expect_channel_closed() ist unnecessary once we improve exc propagation.

@contextlib.contextmanager
def expect_channel_closed():
    versuch:
        liefere
    ausser _channels.ChannelClosedError:
        pass
    sonst:
        pruefe Falsch, 'channel nicht closed'


klasse ChannelAction(namedtuple('ChannelAction', 'action end interp')):

    def __new__(cls, action, end=Nichts, interp=Nichts):
        wenn nicht end:
            end = 'both'
        wenn nicht interp:
            interp = 'main'
        self = super().__new__(cls, action, end, interp)
        gib self

    def __init__(self, *args, **kwargs):
        wenn self.action == 'use':
            wenn self.end nicht in ('same', 'opposite', 'send', 'recv'):
                wirf ValueError(self.end)
        sowenn self.action in ('close', 'force-close'):
            wenn self.end nicht in ('both', 'same', 'opposite', 'send', 'recv'):
                wirf ValueError(self.end)
        sonst:
            wirf ValueError(self.action)
        wenn self.interp nicht in ('main', 'same', 'other', 'extra'):
            wirf ValueError(self.interp)

    def resolve_end(self, end):
        wenn self.end == 'same':
            gib end
        sowenn self.end == 'opposite':
            gib 'recv' wenn end == 'send' sonst 'send'
        sonst:
            gib self.end

    def resolve_interp(self, interp, other, extra):
        wenn self.interp == 'same':
            gib interp
        sowenn self.interp == 'other':
            wenn other ist Nichts:
                wirf RuntimeError
            gib other
        sowenn self.interp == 'extra':
            wenn extra ist Nichts:
                wirf RuntimeError
            gib extra
        sowenn self.interp == 'main':
            wenn interp.name == 'main':
                gib interp
            sowenn other und other.name == 'main':
                gib other
            sonst:
                wirf RuntimeError
        # Per __init__(), there aren't any others.


klasse ChannelState(namedtuple('ChannelState', 'pending closed')):

    def __new__(cls, pending=0, *, closed=Falsch):
        self = super().__new__(cls, pending, closed)
        gib self

    def incr(self):
        gib type(self)(self.pending + 1, closed=self.closed)

    def decr(self):
        gib type(self)(self.pending - 1, closed=self.closed)

    def close(self, *, force=Wahr):
        wenn self.closed:
            wenn nicht force oder self.pending == 0:
                gib self
        gib type(self)(0 wenn force sonst self.pending, closed=Wahr)


def run_action(cid, action, end, state, *, hideclosed=Wahr):
    wenn state.closed:
        wenn action == 'use' und end == 'recv' und state.pending:
            expectfail = Falsch
        sonst:
            expectfail = Wahr
    sonst:
        expectfail = Falsch

    versuch:
        result = _run_action(cid, action, end, state)
    ausser _channels.ChannelClosedError:
        wenn nicht hideclosed und nicht expectfail:
            wirf
        result = state.close()
    sonst:
        wenn expectfail:
            wirf ...  # XXX
    gib result


def _run_action(cid, action, end, state):
    wenn action == 'use':
        wenn end == 'send':
            _channels.send(cid, b'spam', blocking=Falsch)
            gib state.incr()
        sowenn end == 'recv':
            wenn nicht state.pending:
                versuch:
                    _channels.recv(cid)
                ausser _channels.ChannelEmptyError:
                    gib state
                sonst:
                    wirf Exception('expected ChannelEmptyError')
            sonst:
                recv_nowait(cid)
                gib state.decr()
        sonst:
            wirf ValueError(end)
    sowenn action == 'close':
        kwargs = {}
        wenn end in ('recv', 'send'):
            kwargs[end] = Wahr
        _channels.close(cid, **kwargs)
        gib state.close()
    sowenn action == 'force-close':
        kwargs = {
            'force': Wahr,
            }
        wenn end in ('recv', 'send'):
            kwargs[end] = Wahr
        _channels.close(cid, **kwargs)
        gib state.close(force=Wahr)
    sonst:
        wirf ValueError(action)


def clean_up_channels():
    fuer cid, _, _ in _channels.list_all():
        versuch:
            _channels.destroy(cid)
        ausser _channels.ChannelNotFoundError:
            pass  # already destroyed


klasse TestBase(unittest.TestCase):

    def tearDown(self):
        clean_up_channels()
        clean_up_interpreters()


##################################
# channel tests

klasse ChannelIDTests(TestBase):

    def test_default_kwargs(self):
        cid = _channels._channel_id(10, force=Wahr)

        self.assertEqual(int(cid), 10)
        self.assertEqual(cid.end, 'both')

    def test_with_kwargs(self):
        cid = _channels._channel_id(10, send=Wahr, force=Wahr)
        self.assertEqual(cid.end, 'send')

        cid = _channels._channel_id(10, send=Wahr, recv=Falsch, force=Wahr)
        self.assertEqual(cid.end, 'send')

        cid = _channels._channel_id(10, recv=Wahr, force=Wahr)
        self.assertEqual(cid.end, 'recv')

        cid = _channels._channel_id(10, recv=Wahr, send=Falsch, force=Wahr)
        self.assertEqual(cid.end, 'recv')

        cid = _channels._channel_id(10, send=Wahr, recv=Wahr, force=Wahr)
        self.assertEqual(cid.end, 'both')

    def test_coerce_id(self):
        klasse Int(str):
            def __index__(self):
                gib 10

        cid = _channels._channel_id(Int(), force=Wahr)
        self.assertEqual(int(cid), 10)

    def test_bad_id(self):
        self.assertRaises(TypeError, _channels._channel_id, object())
        self.assertRaises(TypeError, _channels._channel_id, 10.0)
        self.assertRaises(TypeError, _channels._channel_id, '10')
        self.assertRaises(TypeError, _channels._channel_id, b'10')
        self.assertRaises(ValueError, _channels._channel_id, -1)
        self.assertRaises(OverflowError, _channels._channel_id, 2**64)

    def test_bad_kwargs(self):
        mit self.assertRaises(ValueError):
            _channels._channel_id(10, send=Falsch, recv=Falsch)

    def test_does_not_exist(self):
        cid = _channels.create(REPLACE)
        mit self.assertRaises(_channels.ChannelNotFoundError):
            _channels._channel_id(int(cid) + 1)  # unforced

    def test_str(self):
        cid = _channels._channel_id(10, force=Wahr)
        self.assertEqual(str(cid), '10')

    def test_repr(self):
        cid = _channels._channel_id(10, force=Wahr)
        self.assertEqual(repr(cid), 'ChannelID(10)')

        cid = _channels._channel_id(10, send=Wahr, force=Wahr)
        self.assertEqual(repr(cid), 'ChannelID(10, send=Wahr)')

        cid = _channels._channel_id(10, recv=Wahr, force=Wahr)
        self.assertEqual(repr(cid), 'ChannelID(10, recv=Wahr)')

        cid = _channels._channel_id(10, send=Wahr, recv=Wahr, force=Wahr)
        self.assertEqual(repr(cid), 'ChannelID(10)')

    def test_equality(self):
        cid1 = _channels.create(REPLACE)
        cid2 = _channels._channel_id(int(cid1))
        cid3 = _channels.create(REPLACE)

        self.assertWahr(cid1 == cid1)
        self.assertWahr(cid1 == cid2)
        self.assertWahr(cid1 == int(cid1))
        self.assertWahr(int(cid1) == cid1)
        self.assertWahr(cid1 == float(int(cid1)))
        self.assertWahr(float(int(cid1)) == cid1)
        self.assertFalsch(cid1 == float(int(cid1)) + 0.1)
        self.assertFalsch(cid1 == str(int(cid1)))
        self.assertFalsch(cid1 == 2**1000)
        self.assertFalsch(cid1 == float('inf'))
        self.assertFalsch(cid1 == 'spam')
        self.assertFalsch(cid1 == cid3)

        self.assertFalsch(cid1 != cid1)
        self.assertFalsch(cid1 != cid2)
        self.assertWahr(cid1 != cid3)

    def test_shareable(self):
        chan = _channels.create(REPLACE)

        obj = _channels.create(REPLACE)
        _channels.send(chan, obj, blocking=Falsch)
        got = recv_nowait(chan)

        self.assertEqual(got, obj)
        self.assertIs(type(got), type(obj))
        # XXX Check the following in the channel tests?
        #self.assertIsNot(got, obj)


@skip_if_sanitizer('gh-129824: race on _waiting_release', thread=Wahr)
klasse ChannelTests(TestBase):

    def test_create_cid(self):
        cid = _channels.create(REPLACE)
        self.assertIsInstance(cid, _channels.ChannelID)

    def test_sequential_ids(self):
        before = [cid fuer cid, _, _ in _channels.list_all()]
        id1 = _channels.create(REPLACE)
        id2 = _channels.create(REPLACE)
        id3 = _channels.create(REPLACE)
        after = [cid fuer cid, _, _ in _channels.list_all()]

        self.assertEqual(id2, int(id1) + 1)
        self.assertEqual(id3, int(id2) + 1)
        self.assertEqual(set(after) - set(before), {id1, id2, id3})

    def test_ids_global(self):
        id1 = _interpreters.create()
        out = _run_output(id1, dedent("""
            importiere _interpchannels als _channels
            cid = _channels.create(3)
            drucke(cid)
            """))
        cid1 = int(out.strip())

        id2 = _interpreters.create()
        out = _run_output(id2, dedent("""
            importiere _interpchannels als _channels
            cid = _channels.create(3)
            drucke(cid)
            """))
        cid2 = int(out.strip())

        self.assertEqual(cid2, int(cid1) + 1)

    def test_channel_list_interpreters_none(self):
        """Test listing interpreters fuer a channel mit no associations."""
        # Test fuer channel mit no associated _interpreters.
        cid = _channels.create(REPLACE)
        send_interps = _channels.list_interpreters(cid, send=Wahr)
        recv_interps = _channels.list_interpreters(cid, send=Falsch)
        self.assertEqual(send_interps, [])
        self.assertEqual(recv_interps, [])

    def test_channel_list_interpreters_basic(self):
        """Test basic listing channel _interpreters."""
        interp0, *_ = _interpreters.get_main()
        cid = _channels.create(REPLACE)
        _channels.send(cid, "send", blocking=Falsch)
        # Test fuer a channel that has one end associated to an interpreter.
        send_interps = _channels.list_interpreters(cid, send=Wahr)
        recv_interps = _channels.list_interpreters(cid, send=Falsch)
        self.assertEqual(send_interps, [interp0])
        self.assertEqual(recv_interps, [])

        interp1 = _interpreters.create()
        _run_output(interp1, dedent(f"""
            importiere _interpchannels als _channels
            _channels.recv({cid})
            """))
        # Test fuer channel that has both ends associated to an interpreter.
        send_interps = _channels.list_interpreters(cid, send=Wahr)
        recv_interps = _channels.list_interpreters(cid, send=Falsch)
        self.assertEqual(send_interps, [interp0])
        self.assertEqual(recv_interps, [interp1])

    def test_channel_list_interpreters_multiple(self):
        """Test listing interpreters fuer a channel mit many associations."""
        interp0, *_ = _interpreters.get_main()
        interp1 = _interpreters.create()
        interp2 = _interpreters.create()
        interp3 = _interpreters.create()
        cid = _channels.create(REPLACE)

        _channels.send(cid, "send", blocking=Falsch)
        _run_output(interp1, dedent(f"""
            importiere _interpchannels als _channels
            _channels.send({cid}, "send", blocking=Falsch)
            """))
        _run_output(interp2, dedent(f"""
            importiere _interpchannels als _channels
            _channels.recv({cid})
            """))
        _run_output(interp3, dedent(f"""
            importiere _interpchannels als _channels
            _channels.recv({cid})
            """))
        send_interps = _channels.list_interpreters(cid, send=Wahr)
        recv_interps = _channels.list_interpreters(cid, send=Falsch)
        self.assertEqual(set(send_interps), {interp0, interp1})
        self.assertEqual(set(recv_interps), {interp2, interp3})

    def test_channel_list_interpreters_destroyed(self):
        """Test listing channel interpreters mit a destroyed interpreter."""
        interp0, *_ = _interpreters.get_main()
        interp1 = _interpreters.create()
        cid = _channels.create(REPLACE)
        _channels.send(cid, "send", blocking=Falsch)
        _run_output(interp1, dedent(f"""
            importiere _interpchannels als _channels
            _channels.recv({cid})
            """))
        # Should be one interpreter associated mit each end.
        send_interps = _channels.list_interpreters(cid, send=Wahr)
        recv_interps = _channels.list_interpreters(cid, send=Falsch)
        self.assertEqual(send_interps, [interp0])
        self.assertEqual(recv_interps, [interp1])

        _interpreters.destroy(interp1)
        # Destroyed interpreter should nicht be listed.
        send_interps = _channels.list_interpreters(cid, send=Wahr)
        recv_interps = _channels.list_interpreters(cid, send=Falsch)
        self.assertEqual(send_interps, [interp0])
        self.assertEqual(recv_interps, [])

    def test_channel_list_interpreters_released(self):
        """Test listing channel interpreters mit a released channel."""
        # Set up one channel mit main interpreter on the send end und two
        # subinterpreters on the receive end.
        interp0, *_ = _interpreters.get_main()
        interp1 = _interpreters.create()
        interp2 = _interpreters.create()
        cid = _channels.create(REPLACE)
        _channels.send(cid, "data", blocking=Falsch)
        _run_output(interp1, dedent(f"""
            importiere _interpchannels als _channels
            _channels.recv({cid})
            """))
        _channels.send(cid, "data", blocking=Falsch)
        _run_output(interp2, dedent(f"""
            importiere _interpchannels als _channels
            _channels.recv({cid})
            """))
        # Check the setup.
        send_interps = _channels.list_interpreters(cid, send=Wahr)
        recv_interps = _channels.list_interpreters(cid, send=Falsch)
        self.assertEqual(len(send_interps), 1)
        self.assertEqual(len(recv_interps), 2)

        # Release the main interpreter von the send end.
        _channels.release(cid, send=Wahr)
        # Send end should have no associated _interpreters.
        send_interps = _channels.list_interpreters(cid, send=Wahr)
        recv_interps = _channels.list_interpreters(cid, send=Falsch)
        self.assertEqual(len(send_interps), 0)
        self.assertEqual(len(recv_interps), 2)

        # Release one of the subinterpreters von the receive end.
        _run_output(interp2, dedent(f"""
            importiere _interpchannels als _channels
            _channels.release({cid})
            """))
        # Receive end should have the released interpreter removed.
        send_interps = _channels.list_interpreters(cid, send=Wahr)
        recv_interps = _channels.list_interpreters(cid, send=Falsch)
        self.assertEqual(len(send_interps), 0)
        self.assertEqual(recv_interps, [interp1])

    def test_channel_list_interpreters_closed(self):
        """Test listing channel interpreters mit a closed channel."""
        interp0, *_ = _interpreters.get_main()
        interp1 = _interpreters.create()
        cid = _channels.create(REPLACE)
        # Put something in the channel so that it's nicht empty.
        _channels.send(cid, "send", blocking=Falsch)

        # Check initial state.
        send_interps = _channels.list_interpreters(cid, send=Wahr)
        recv_interps = _channels.list_interpreters(cid, send=Falsch)
        self.assertEqual(len(send_interps), 1)
        self.assertEqual(len(recv_interps), 0)

        # Force close the channel.
        _channels.close(cid, force=Wahr)
        # Both ends should wirf an error.
        mit self.assertRaises(_channels.ChannelClosedError):
            _channels.list_interpreters(cid, send=Wahr)
        mit self.assertRaises(_channels.ChannelClosedError):
            _channels.list_interpreters(cid, send=Falsch)

    def test_channel_list_interpreters_closed_send_end(self):
        """Test listing channel interpreters mit a channel's send end closed."""
        interp0, *_ = _interpreters.get_main()
        interp1 = _interpreters.create()
        cid = _channels.create(REPLACE)
        # Put something in the channel so that it's nicht empty.
        _channels.send(cid, "send", blocking=Falsch)

        # Check initial state.
        send_interps = _channels.list_interpreters(cid, send=Wahr)
        recv_interps = _channels.list_interpreters(cid, send=Falsch)
        self.assertEqual(len(send_interps), 1)
        self.assertEqual(len(recv_interps), 0)

        # Close the send end of the channel.
        _channels.close(cid, send=Wahr)
        # Send end should wirf an error.
        mit self.assertRaises(_channels.ChannelClosedError):
            _channels.list_interpreters(cid, send=Wahr)
        # Receive end should nicht be closed (since channel ist nicht empty).
        recv_interps = _channels.list_interpreters(cid, send=Falsch)
        self.assertEqual(len(recv_interps), 0)

        # Close the receive end of the channel von a subinterpreter.
        _run_output(interp1, dedent(f"""
            importiere _interpchannels als _channels
            _channels.close({cid}, force=Wahr)
            """))
        gib
        # Both ends should wirf an error.
        mit self.assertRaises(_channels.ChannelClosedError):
            _channels.list_interpreters(cid, send=Wahr)
        mit self.assertRaises(_channels.ChannelClosedError):
            _channels.list_interpreters(cid, send=Falsch)

    def test_allowed_types(self):
        cid = _channels.create(REPLACE)
        objects = [
            Nichts,
            'spam',
            b'spam',
            42,
        ]
        fuer obj in objects:
            mit self.subTest(obj):
                _channels.send(cid, obj, blocking=Falsch)
                got = recv_nowait(cid)

                self.assertEqual(got, obj)
                self.assertIs(type(got), type(obj))
                # XXX Check the following?
                #self.assertIsNot(got, obj)
                # XXX What about between interpreters?

    def test_run_string_arg_unresolved(self):
        cid = _channels.create(REPLACE)
        interp = _interpreters.create()

        _interpreters.set___main___attrs(interp, dict(cid=cid.send))
        out = _run_output(interp, dedent("""
            importiere _interpchannels als _channels
            drucke(cid.end)
            _channels.send(cid, b'spam', blocking=Falsch)
            """))
        obj = recv_nowait(cid)

        self.assertEqual(obj, b'spam')
        self.assertEqual(out.strip(), 'send')

    # XXX For now there ist no high-level channel into which the
    # sent channel ID can be converted...
    # Note: this test caused crashes on some buildbots (bpo-33615).
    @unittest.skip('disabled until high-level channels exist')
    def test_run_string_arg_resolved(self):
        cid = _channels.create(REPLACE)
        cid = _channels._channel_id(cid, _resolve=Wahr)
        interp = _interpreters.create()

        out = _run_output(interp, dedent("""
            importiere _interpchannels als _channels
            drucke(chan.id.end)
            _channels.send(chan.id, b'spam', blocking=Falsch)
            """),
            dict(chan=cid.send))
        obj = recv_nowait(cid)

        self.assertEqual(obj, b'spam')
        self.assertEqual(out.strip(), 'send')

    #-------------------
    # send/recv

    def test_send_recv_main(self):
        cid = _channels.create(REPLACE)
        orig = b'spam'
        _channels.send(cid, orig, blocking=Falsch)
        obj = recv_nowait(cid)

        self.assertEqual(obj, orig)
        self.assertIsNot(obj, orig)

    def test_send_recv_same_interpreter(self):
        id1 = _interpreters.create()
        out = _run_output(id1, dedent("""
            importiere _interpchannels als _channels
            cid = _channels.create(REPLACE)
            orig = b'spam'
            _channels.send(cid, orig, blocking=Falsch)
            obj, _ = _channels.recv(cid)
            pruefe obj ist nicht orig
            pruefe obj == orig
            """))

    def test_send_recv_different_interpreters(self):
        cid = _channels.create(REPLACE)
        id1 = _interpreters.create()
        out = _run_output(id1, dedent(f"""
            importiere _interpchannels als _channels
            _channels.send({cid}, b'spam', blocking=Falsch)
            """))
        obj = recv_nowait(cid)

        self.assertEqual(obj, b'spam')

    def test_send_recv_different_threads(self):
        cid = _channels.create(REPLACE)

        def f():
            obj = recv_wait(cid)
            _channels.send(cid, obj)
        t = threading.Thread(target=f)
        t.start()

        _channels.send(cid, b'spam')
        obj = recv_wait(cid)
        t.join()

        self.assertEqual(obj, b'spam')

    def test_send_recv_different_interpreters_and_threads(self):
        cid = _channels.create(REPLACE)
        id1 = _interpreters.create()
        out = Nichts

        def f():
            nichtlokal out
            out = _run_output(id1, dedent(f"""
                importiere time
                importiere _interpchannels als _channels
                waehrend Wahr:
                    versuch:
                        obj, _ = _channels.recv({cid})
                        breche
                    ausser _channels.ChannelEmptyError:
                        time.sleep(0.1)
                assert(obj == b'spam')
                _channels.send({cid}, b'eggs')
                """))
        t = threading.Thread(target=f)
        t.start()

        _channels.send(cid, b'spam')
        obj = recv_wait(cid)
        t.join()

        self.assertEqual(obj, b'eggs')

    def test_send_not_found(self):
        mit self.assertRaises(_channels.ChannelNotFoundError):
            _channels.send(10, b'spam')

    def test_recv_not_found(self):
        mit self.assertRaises(_channels.ChannelNotFoundError):
            _channels.recv(10)

    def test_recv_empty(self):
        cid = _channels.create(REPLACE)
        mit self.assertRaises(_channels.ChannelEmptyError):
            _channels.recv(cid)

    def test_recv_default(self):
        default = object()
        cid = _channels.create(REPLACE)
        obj1 = recv_nowait(cid, default)
        _channels.send(cid, Nichts, blocking=Falsch)
        _channels.send(cid, 1, blocking=Falsch)
        _channels.send(cid, b'spam', blocking=Falsch)
        _channels.send(cid, b'eggs', blocking=Falsch)
        obj2 = recv_nowait(cid, default)
        obj3 = recv_nowait(cid, default)
        obj4 = recv_nowait(cid)
        obj5 = recv_nowait(cid, default)
        obj6 = recv_nowait(cid, default)

        self.assertIs(obj1, default)
        self.assertIs(obj2, Nichts)
        self.assertEqual(obj3, 1)
        self.assertEqual(obj4, b'spam')
        self.assertEqual(obj5, b'eggs')
        self.assertIs(obj6, default)

    def test_recv_sending_interp_destroyed(self):
        mit self.subTest('closed'):
            cid1 = _channels.create(REPLACE)
            interp = _interpreters.create()
            _interpreters.run_string(interp, dedent(f"""
                importiere _interpchannels als _channels
                _channels.send({cid1}, b'spam', blocking=Falsch)
                """))
            _interpreters.destroy(interp)

            mit self.assertRaisesRegex(RuntimeError,
                                        f'channel {cid1} ist closed'):
                _channels.recv(cid1)
            loesche cid1
        mit self.subTest('still open'):
            cid2 = _channels.create(REPLACE)
            interp = _interpreters.create()
            _interpreters.run_string(interp, dedent(f"""
                importiere _interpchannels als _channels
                _channels.send({cid2}, b'spam', blocking=Falsch)
                """))
            _channels.send(cid2, b'eggs', blocking=Falsch)
            _interpreters.destroy(interp)

            recv_nowait(cid2, unbound=Wahr)
            recv_nowait(cid2, unbound=Falsch)
            mit self.assertRaisesRegex(RuntimeError,
                                        f'channel {cid2} ist empty'):
                _channels.recv(cid2)
            loesche cid2

    #-------------------
    # send_buffer

    def test_send_buffer(self):
        buf = bytearray(b'spamspamspam')
        cid = _channels.create(REPLACE)
        _channels.send_buffer(cid, buf, blocking=Falsch)
        obj = recv_nowait(cid)

        self.assertIsNot(obj, buf)
        self.assertIsInstance(obj, memoryview)
        self.assertEqual(obj, buf)

        buf[4:8] = b'eggs'
        self.assertEqual(obj, buf)
        obj[4:8] = b'ham.'
        self.assertEqual(obj, buf)

    #-------------------
    # send mit waiting

    def build_send_waiter(self, obj, *, buffer=Falsch):
        # We want a long enough sleep that send() actually has to wait.

        wenn buffer:
            send = _channels.send_buffer
        sonst:
            send = _channels.send

        cid = _channels.create(REPLACE)
        versuch:
            started = time.monotonic()
            send(cid, obj, blocking=Falsch)
            stopped = time.monotonic()
            recv_nowait(cid)
        schliesslich:
            _channels.destroy(cid)
        delay = stopped - started  # seconds
        delay *= 3

        def wait():
            time.sleep(delay)
        gib wait

    def test_send_blocking_waiting(self):
        received = Nichts
        obj = b'spam'
        wait = self.build_send_waiter(obj)
        cid = _channels.create(REPLACE)
        def f():
            nichtlokal received
            wait()
            received = recv_wait(cid)
        t = threading.Thread(target=f)
        t.start()
        _channels.send(cid, obj, blocking=Wahr)
        t.join()

        self.assertEqual(received, obj)

    def test_send_buffer_blocking_waiting(self):
        received = Nichts
        obj = bytearray(b'spam')
        wait = self.build_send_waiter(obj, buffer=Wahr)
        cid = _channels.create(REPLACE)
        def f():
            nichtlokal received
            wait()
            received = recv_wait(cid)
        t = threading.Thread(target=f)
        t.start()
        _channels.send_buffer(cid, obj, blocking=Wahr)
        t.join()

        self.assertEqual(received, obj)

    def test_send_blocking_no_wait(self):
        received = Nichts
        obj = b'spam'
        cid = _channels.create(REPLACE)
        def f():
            nichtlokal received
            received = recv_wait(cid)
        t = threading.Thread(target=f)
        t.start()
        _channels.send(cid, obj, blocking=Wahr)
        t.join()

        self.assertEqual(received, obj)

    def test_send_buffer_blocking_no_wait(self):
        received = Nichts
        obj = bytearray(b'spam')
        cid = _channels.create(REPLACE)
        def f():
            nichtlokal received
            received = recv_wait(cid)
        t = threading.Thread(target=f)
        t.start()
        _channels.send_buffer(cid, obj, blocking=Wahr)
        t.join()

        self.assertEqual(received, obj)

    def test_send_timeout(self):
        obj = b'spam'

        mit self.subTest('non-blocking mit timeout'):
            cid = _channels.create(REPLACE)
            mit self.assertRaises(ValueError):
                _channels.send(cid, obj, blocking=Falsch, timeout=0.1)

        mit self.subTest('timeout hit'):
            cid = _channels.create(REPLACE)
            mit self.assertRaises(TimeoutError):
                _channels.send(cid, obj, blocking=Wahr, timeout=0.1)
            mit self.assertRaises(_channels.ChannelEmptyError):
                received = recv_nowait(cid)
                drucke(repr(received))

        mit self.subTest('timeout nicht hit'):
            cid = _channels.create(REPLACE)
            def f():
                recv_wait(cid)
            t = threading.Thread(target=f)
            t.start()
            _channels.send(cid, obj, blocking=Wahr, timeout=10)
            t.join()

    def test_send_buffer_timeout(self):
        versuch:
            self._has_run_once_timeout
        ausser AttributeError:
            # At the moment, this test leaks a few references.
            # It looks like the leak originates mit the addition
            # of _channels.send_buffer() (gh-110246), whereas the
            # tests were added afterward.  We want this test even
            # wenn the refleak isn't fixed yet, so we skip here.
            wirf unittest.SkipTest('temporarily skipped due to refleaks')
        sonst:
            self._has_run_once_timeout = Wahr

        obj = bytearray(b'spam')

        mit self.subTest('non-blocking mit timeout'):
            cid = _channels.create(REPLACE)
            mit self.assertRaises(ValueError):
                _channels.send_buffer(cid, obj, blocking=Falsch, timeout=0.1)

        mit self.subTest('timeout hit'):
            cid = _channels.create(REPLACE)
            mit self.assertRaises(TimeoutError):
                _channels.send_buffer(cid, obj, blocking=Wahr, timeout=0.1)
            mit self.assertRaises(_channels.ChannelEmptyError):
                received = recv_nowait(cid)
                drucke(repr(received))

        mit self.subTest('timeout nicht hit'):
            cid = _channels.create(REPLACE)
            def f():
                recv_wait(cid)
            t = threading.Thread(target=f)
            t.start()
            _channels.send_buffer(cid, obj, blocking=Wahr, timeout=10)
            t.join()

    def test_send_closed_while_waiting(self):
        obj = b'spam'
        wait = self.build_send_waiter(obj)

        mit self.subTest('without timeout'):
            cid = _channels.create(REPLACE)
            def f():
                wait()
                _channels.close(cid, force=Wahr)
            t = threading.Thread(target=f)
            t.start()
            mit self.assertRaises(_channels.ChannelClosedError):
                _channels.send(cid, obj, blocking=Wahr)
            t.join()

        mit self.subTest('with timeout'):
            cid = _channels.create(REPLACE)
            def f():
                wait()
                _channels.close(cid, force=Wahr)
            t = threading.Thread(target=f)
            t.start()
            mit self.assertRaises(_channels.ChannelClosedError):
                _channels.send(cid, obj, blocking=Wahr, timeout=30)
            t.join()

    def test_send_buffer_closed_while_waiting(self):
        versuch:
            self._has_run_once_closed
        ausser AttributeError:
            # At the moment, this test leaks a few references.
            # It looks like the leak originates mit the addition
            # of _channels.send_buffer() (gh-110246), whereas the
            # tests were added afterward.  We want this test even
            # wenn the refleak isn't fixed yet, so we skip here.
            wirf unittest.SkipTest('temporarily skipped due to refleaks')
        sonst:
            self._has_run_once_closed = Wahr

        obj = bytearray(b'spam')
        wait = self.build_send_waiter(obj, buffer=Wahr)

        mit self.subTest('without timeout'):
            cid = _channels.create(REPLACE)
            def f():
                wait()
                _channels.close(cid, force=Wahr)
            t = threading.Thread(target=f)
            t.start()
            mit self.assertRaises(_channels.ChannelClosedError):
                _channels.send_buffer(cid, obj, blocking=Wahr)
            t.join()

        mit self.subTest('with timeout'):
            cid = _channels.create(REPLACE)
            def f():
                wait()
                _channels.close(cid, force=Wahr)
            t = threading.Thread(target=f)
            t.start()
            mit self.assertRaises(_channels.ChannelClosedError):
                _channels.send_buffer(cid, obj, blocking=Wahr, timeout=30)
            t.join()

    #-------------------
    # close

    def test_close_single_user(self):
        cid = _channels.create(REPLACE)
        _channels.send(cid, b'spam', blocking=Falsch)
        recv_nowait(cid)
        _channels.close(cid)

        mit self.assertRaises(_channels.ChannelClosedError):
            _channels.send(cid, b'eggs')
        mit self.assertRaises(_channels.ChannelClosedError):
            _channels.recv(cid)

    def test_close_multiple_users(self):
        cid = _channels.create(REPLACE)
        id1 = _interpreters.create()
        id2 = _interpreters.create()
        _interpreters.run_string(id1, dedent(f"""
            importiere _interpchannels als _channels
            _channels.send({cid}, b'spam', blocking=Falsch)
            """))
        _interpreters.run_string(id2, dedent(f"""
            importiere _interpchannels als _channels
            _channels.recv({cid})
            """))
        _channels.close(cid)

        excsnap = _interpreters.run_string(id1, dedent(f"""
                _channels.send({cid}, b'spam')
                """))
        self.assertEqual(excsnap.type.__name__, 'ChannelClosedError')

        excsnap = _interpreters.run_string(id2, dedent(f"""
                _channels.send({cid}, b'spam')
                """))
        self.assertEqual(excsnap.type.__name__, 'ChannelClosedError')

    def test_close_multiple_times(self):
        cid = _channels.create(REPLACE)
        _channels.send(cid, b'spam', blocking=Falsch)
        recv_nowait(cid)
        _channels.close(cid)

        mit self.assertRaises(_channels.ChannelClosedError):
            _channels.close(cid)

    def test_close_empty(self):
        tests = [
            (Falsch, Falsch),
            (Wahr, Falsch),
            (Falsch, Wahr),
            (Wahr, Wahr),
            ]
        fuer send, recv in tests:
            mit self.subTest((send, recv)):
                cid = _channels.create(REPLACE)
                _channels.send(cid, b'spam', blocking=Falsch)
                recv_nowait(cid)
                _channels.close(cid, send=send, recv=recv)

                mit self.assertRaises(_channels.ChannelClosedError):
                    _channels.send(cid, b'eggs')
                mit self.assertRaises(_channels.ChannelClosedError):
                    _channels.recv(cid)

    def test_close_defaults_with_unused_items(self):
        cid = _channels.create(REPLACE)
        _channels.send(cid, b'spam', blocking=Falsch)
        _channels.send(cid, b'ham', blocking=Falsch)

        mit self.assertRaises(_channels.ChannelNotEmptyError):
            _channels.close(cid)
        recv_nowait(cid)
        _channels.send(cid, b'eggs', blocking=Falsch)

    def test_close_recv_with_unused_items_unforced(self):
        cid = _channels.create(REPLACE)
        _channels.send(cid, b'spam', blocking=Falsch)
        _channels.send(cid, b'ham', blocking=Falsch)

        mit self.assertRaises(_channels.ChannelNotEmptyError):
            _channels.close(cid, recv=Wahr)
        recv_nowait(cid)
        _channels.send(cid, b'eggs', blocking=Falsch)
        recv_nowait(cid)
        recv_nowait(cid)
        _channels.close(cid, recv=Wahr)

    def test_close_send_with_unused_items_unforced(self):
        cid = _channels.create(REPLACE)
        _channels.send(cid, b'spam', blocking=Falsch)
        _channels.send(cid, b'ham', blocking=Falsch)
        _channels.close(cid, send=Wahr)

        mit self.assertRaises(_channels.ChannelClosedError):
            _channels.send(cid, b'eggs')
        recv_nowait(cid)
        recv_nowait(cid)
        mit self.assertRaises(_channels.ChannelClosedError):
            _channels.recv(cid)

    def test_close_both_with_unused_items_unforced(self):
        cid = _channels.create(REPLACE)
        _channels.send(cid, b'spam', blocking=Falsch)
        _channels.send(cid, b'ham', blocking=Falsch)

        mit self.assertRaises(_channels.ChannelNotEmptyError):
            _channels.close(cid, recv=Wahr, send=Wahr)
        recv_nowait(cid)
        _channels.send(cid, b'eggs', blocking=Falsch)
        recv_nowait(cid)
        recv_nowait(cid)
        _channels.close(cid, recv=Wahr)

    def test_close_recv_with_unused_items_forced(self):
        cid = _channels.create(REPLACE)
        _channels.send(cid, b'spam', blocking=Falsch)
        _channels.send(cid, b'ham', blocking=Falsch)
        _channels.close(cid, recv=Wahr, force=Wahr)

        mit self.assertRaises(_channels.ChannelClosedError):
            _channels.send(cid, b'eggs')
        mit self.assertRaises(_channels.ChannelClosedError):
            _channels.recv(cid)

    def test_close_send_with_unused_items_forced(self):
        cid = _channels.create(REPLACE)
        _channels.send(cid, b'spam', blocking=Falsch)
        _channels.send(cid, b'ham', blocking=Falsch)
        _channels.close(cid, send=Wahr, force=Wahr)

        mit self.assertRaises(_channels.ChannelClosedError):
            _channels.send(cid, b'eggs')
        mit self.assertRaises(_channels.ChannelClosedError):
            _channels.recv(cid)

    def test_close_both_with_unused_items_forced(self):
        cid = _channels.create(REPLACE)
        _channels.send(cid, b'spam', blocking=Falsch)
        _channels.send(cid, b'ham', blocking=Falsch)
        _channels.close(cid, send=Wahr, recv=Wahr, force=Wahr)

        mit self.assertRaises(_channels.ChannelClosedError):
            _channels.send(cid, b'eggs')
        mit self.assertRaises(_channels.ChannelClosedError):
            _channels.recv(cid)

    def test_close_never_used(self):
        cid = _channels.create(REPLACE)
        _channels.close(cid)

        mit self.assertRaises(_channels.ChannelClosedError):
            _channels.send(cid, b'spam')
        mit self.assertRaises(_channels.ChannelClosedError):
            _channels.recv(cid)

    def test_close_by_unassociated_interp(self):
        cid = _channels.create(REPLACE)
        _channels.send(cid, b'spam', blocking=Falsch)
        interp = _interpreters.create()
        _interpreters.run_string(interp, dedent(f"""
            importiere _interpchannels als _channels
            _channels.close({cid}, force=Wahr)
            """))
        mit self.assertRaises(_channels.ChannelClosedError):
            _channels.recv(cid)
        mit self.assertRaises(_channels.ChannelClosedError):
            _channels.close(cid)

    def test_close_used_multiple_times_by_single_user(self):
        cid = _channels.create(REPLACE)
        _channels.send(cid, b'spam', blocking=Falsch)
        _channels.send(cid, b'spam', blocking=Falsch)
        _channels.send(cid, b'spam', blocking=Falsch)
        recv_nowait(cid)
        _channels.close(cid, force=Wahr)

        mit self.assertRaises(_channels.ChannelClosedError):
            _channels.send(cid, b'eggs')
        mit self.assertRaises(_channels.ChannelClosedError):
            _channels.recv(cid)

    def test_channel_list_interpreters_invalid_channel(self):
        cid = _channels.create(REPLACE)
        # Test fuer invalid channel ID.
        mit self.assertRaises(_channels.ChannelNotFoundError):
            _channels.list_interpreters(1000, send=Wahr)

        _channels.close(cid)
        # Test fuer a channel that has been closed.
        mit self.assertRaises(_channels.ChannelClosedError):
            _channels.list_interpreters(cid, send=Wahr)

    def test_channel_list_interpreters_invalid_args(self):
        # Tests fuer invalid arguments passed to the API.
        cid = _channels.create(REPLACE)
        mit self.assertRaises(TypeError):
            _channels.list_interpreters(cid)


klasse ChannelReleaseTests(TestBase):

    # XXX Add more test coverage a la the tests fuer close().

    """
    - main / interp / other
    - run in: current thread / new thread / other thread / different threads
    - end / opposite
    - force / no force
    - used / nicht used  (associated / nicht associated)
    - empty / emptied / never emptied / partly emptied
    - closed / nicht closed
    - released / nicht released
    - creator (interp) / other
    - associated interpreter nicht running
    - associated interpreter destroyed
    """

    """
    use
    pre-release
    release
    after
    check
    """

    """
    release in:         main, interp1
    creator:            same, other (incl. interp2)

    use:                Nichts,send,recv,send/recv in Nichts,same,other(incl. interp2),same+other(incl. interp2),all
    pre-release:        Nichts,send,recv,both in Nichts,same,other(incl. interp2),same+other(incl. interp2),all
    pre-release forced: Nichts,send,recv,both in Nichts,same,other(incl. interp2),same+other(incl. interp2),all

    release:            same
    release forced:     same

    use after:          Nichts,send,recv,send/recv in Nichts,same,other(incl. interp2),same+other(incl. interp2),all
    release after:      Nichts,send,recv,send/recv in Nichts,same,other(incl. interp2),same+other(incl. interp2),all
    check released:     send/recv fuer same/other(incl. interp2)
    check closed:       send/recv fuer same/other(incl. interp2)
    """

    def test_single_user(self):
        cid = _channels.create(REPLACE)
        _channels.send(cid, b'spam', blocking=Falsch)
        recv_nowait(cid)
        _channels.release(cid, send=Wahr, recv=Wahr)

        mit self.assertRaises(_channels.ChannelClosedError):
            _channels.send(cid, b'eggs')
        mit self.assertRaises(_channels.ChannelClosedError):
            _channels.recv(cid)

    def test_multiple_users(self):
        cid = _channels.create(REPLACE)
        id1 = _interpreters.create()
        id2 = _interpreters.create()
        _interpreters.run_string(id1, dedent(f"""
            importiere _interpchannels als _channels
            _channels.send({cid}, b'spam', blocking=Falsch)
            """))
        out = _run_output(id2, dedent(f"""
            importiere _interpchannels als _channels
            obj, _ = _channels.recv({cid})
            _channels.release({cid})
            drucke(repr(obj))
            """))
        _interpreters.run_string(id1, dedent(f"""
            _channels.release({cid})
            """))

        self.assertEqual(out.strip(), "b'spam'")

    def test_no_kwargs(self):
        cid = _channels.create(REPLACE)
        _channels.send(cid, b'spam', blocking=Falsch)
        recv_nowait(cid)
        _channels.release(cid)

        mit self.assertRaises(_channels.ChannelClosedError):
            _channels.send(cid, b'eggs')
        mit self.assertRaises(_channels.ChannelClosedError):
            _channels.recv(cid)

    def test_multiple_times(self):
        cid = _channels.create(REPLACE)
        _channels.send(cid, b'spam', blocking=Falsch)
        recv_nowait(cid)
        _channels.release(cid, send=Wahr, recv=Wahr)

        mit self.assertRaises(_channels.ChannelClosedError):
            _channels.release(cid, send=Wahr, recv=Wahr)

    def test_with_unused_items(self):
        cid = _channels.create(REPLACE)
        _channels.send(cid, b'spam', blocking=Falsch)
        _channels.send(cid, b'ham', blocking=Falsch)
        _channels.release(cid, send=Wahr, recv=Wahr)

        mit self.assertRaises(_channels.ChannelClosedError):
            _channels.recv(cid)

    def test_never_used(self):
        cid = _channels.create(REPLACE)
        _channels.release(cid)

        mit self.assertRaises(_channels.ChannelClosedError):
            _channels.send(cid, b'spam')
        mit self.assertRaises(_channels.ChannelClosedError):
            _channels.recv(cid)

    def test_by_unassociated_interp(self):
        cid = _channels.create(REPLACE)
        _channels.send(cid, b'spam', blocking=Falsch)
        interp = _interpreters.create()
        _interpreters.run_string(interp, dedent(f"""
            importiere _interpchannels als _channels
            _channels.release({cid})
            """))
        obj = recv_nowait(cid)
        _channels.release(cid)

        mit self.assertRaises(_channels.ChannelClosedError):
            _channels.send(cid, b'eggs')
        self.assertEqual(obj, b'spam')

    def test_close_if_unassociated(self):
        # XXX Something's nicht right mit this test...
        cid = _channels.create(REPLACE)
        interp = _interpreters.create()
        _interpreters.run_string(interp, dedent(f"""
            importiere _interpchannels als _channels
            obj = _channels.send({cid}, b'spam', blocking=Falsch)
            _channels.release({cid})
            """))

        mit self.assertRaises(_channels.ChannelClosedError):
            _channels.recv(cid)

    def test_partially(self):
        # XXX Is partial close too weird/confusing?
        cid = _channels.create(REPLACE)
        _channels.send(cid, Nichts, blocking=Falsch)
        recv_nowait(cid)
        _channels.send(cid, b'spam', blocking=Falsch)
        _channels.release(cid, send=Wahr)
        obj = recv_nowait(cid)

        self.assertEqual(obj, b'spam')

    def test_used_multiple_times_by_single_user(self):
        cid = _channels.create(REPLACE)
        _channels.send(cid, b'spam', blocking=Falsch)
        _channels.send(cid, b'spam', blocking=Falsch)
        _channels.send(cid, b'spam', blocking=Falsch)
        recv_nowait(cid)
        _channels.release(cid, send=Wahr, recv=Wahr)

        mit self.assertRaises(_channels.ChannelClosedError):
            _channels.send(cid, b'eggs')
        mit self.assertRaises(_channels.ChannelClosedError):
            _channels.recv(cid)


klasse ChannelCloseFixture(namedtuple('ChannelCloseFixture',
                                     'end interp other extra creator')):

    # Set this to Wahr to avoid creating interpreters, e.g. when
    # scanning through test permutations without running them.
    QUICK = Falsch

    def __new__(cls, end, interp, other, extra, creator):
        pruefe end in ('send', 'recv')
        wenn cls.QUICK:
            known = {}
        sonst:
            interp = Interpreter.from_raw(interp)
            other = Interpreter.from_raw(other)
            extra = Interpreter.from_raw(extra)
            known = {
                interp.name: interp,
                other.name: other,
                extra.name: extra,
                }
        wenn nicht creator:
            creator = 'same'
        self = super().__new__(cls, end, interp, other, extra, creator)
        self._prepped = set()
        self._state = ChannelState()
        self._known = known
        gib self

    @property
    def state(self):
        gib self._state

    @property
    def cid(self):
        versuch:
            gib self._cid
        ausser AttributeError:
            creator = self._get_interpreter(self.creator)
            self._cid = self._new_channel(creator)
            gib self._cid

    def get_interpreter(self, interp):
        interp = self._get_interpreter(interp)
        self._prep_interpreter(interp)
        gib interp

    def expect_closed_error(self, end=Nichts):
        wenn end ist Nichts:
            end = self.end
        wenn end == 'recv' und self.state.closed == 'send':
            gib Falsch
        gib bool(self.state.closed)

    def prep_interpreter(self, interp):
        self._prep_interpreter(interp)

    def record_action(self, action, result):
        self._state = result

    def clean_up(self):
        clean_up_interpreters()
        clean_up_channels()

    # internal methods

    def _new_channel(self, creator):
        wenn creator.name == 'main':
            gib _channels.create(REPLACE)
        sonst:
            ch = _channels.create(REPLACE)
            run_interp(creator.id, f"""
                importiere _interpreters
                cid = _xxsubchannels.create()
                # We purposefully send back an int to avoid tying the
                # channel to the other interpreter.
                _xxsubchannels.send({ch}, int(cid), blocking=Falsch)
                loesche _interpreters
                """)
            self._cid = recv_nowait(ch)
        gib self._cid

    def _get_interpreter(self, interp):
        wenn interp in ('same', 'interp'):
            gib self.interp
        sowenn interp == 'other':
            gib self.other
        sowenn interp == 'extra':
            gib self.extra
        sonst:
            name = interp
            versuch:
                interp = self._known[name]
            ausser KeyError:
                interp = self._known[name] = Interpreter(name)
            gib interp

    def _prep_interpreter(self, interp):
        wenn interp.id in self._prepped:
            gib
        self._prepped.add(interp.id)
        wenn interp.name == 'main':
            gib
        run_interp(interp.id, f"""
            importiere _interpchannels als channels
            importiere test.test__interpchannels als helpers
            ChannelState = helpers.ChannelState
            versuch:
                cid
            ausser NameError:
                cid = _channels._channel_id({self.cid})
            """)


@unittest.skip('these tests take several hours to run')
klasse ExhaustiveChannelTests(TestBase):

    """
    - main / interp / other
    - run in: current thread / new thread / other thread / different threads
    - end / opposite
    - force / no force
    - used / nicht used  (associated / nicht associated)
    - empty / emptied / never emptied / partly emptied
    - closed / nicht closed
    - released / nicht released
    - creator (interp) / other
    - associated interpreter nicht running
    - associated interpreter destroyed

    - close after unbound
    """

    """
    use
    pre-close
    close
    after
    check
    """

    """
    close in:         main, interp1
    creator:          same, other, extra

    use:              Nichts,send,recv,send/recv in Nichts,same,other,same+other,all
    pre-close:        Nichts,send,recv in Nichts,same,other,same+other,all
    pre-close forced: Nichts,send,recv in Nichts,same,other,same+other,all

    close:            same
    close forced:     same

    use after:        Nichts,send,recv,send/recv in Nichts,same,other,extra,same+other,all
    close after:      Nichts,send,recv,send/recv in Nichts,same,other,extra,same+other,all
    check closed:     send/recv fuer same/other(incl. interp2)
    """

    def iter_action_sets(self):
        # - used / nicht used  (associated / nicht associated)
        # - empty / emptied / never emptied / partly emptied
        # - closed / nicht closed
        # - released / nicht released

        # never used
        liefere []

        # only pre-closed (and possible used after)
        fuer closeactions in self._iter_close_action_sets('same', 'other'):
            liefere closeactions
            fuer postactions in self._iter_post_close_action_sets():
                liefere closeactions + postactions
        fuer closeactions in self._iter_close_action_sets('other', 'extra'):
            liefere closeactions
            fuer postactions in self._iter_post_close_action_sets():
                liefere closeactions + postactions

        # used
        fuer useactions in self._iter_use_action_sets('same', 'other'):
            liefere useactions
            fuer closeactions in self._iter_close_action_sets('same', 'other'):
                actions = useactions + closeactions
                liefere actions
                fuer postactions in self._iter_post_close_action_sets():
                    liefere actions + postactions
            fuer closeactions in self._iter_close_action_sets('other', 'extra'):
                actions = useactions + closeactions
                liefere actions
                fuer postactions in self._iter_post_close_action_sets():
                    liefere actions + postactions
        fuer useactions in self._iter_use_action_sets('other', 'extra'):
            liefere useactions
            fuer closeactions in self._iter_close_action_sets('same', 'other'):
                actions = useactions + closeactions
                liefere actions
                fuer postactions in self._iter_post_close_action_sets():
                    liefere actions + postactions
            fuer closeactions in self._iter_close_action_sets('other', 'extra'):
                actions = useactions + closeactions
                liefere actions
                fuer postactions in self._iter_post_close_action_sets():
                    liefere actions + postactions

    def _iter_use_action_sets(self, interp1, interp2):
        interps = (interp1, interp2)

        # only recv end used
        liefere [
            ChannelAction('use', 'recv', interp1),
            ]
        liefere [
            ChannelAction('use', 'recv', interp2),
            ]
        liefere [
            ChannelAction('use', 'recv', interp1),
            ChannelAction('use', 'recv', interp2),
            ]

        # never emptied
        liefere [
            ChannelAction('use', 'send', interp1),
            ]
        liefere [
            ChannelAction('use', 'send', interp2),
            ]
        liefere [
            ChannelAction('use', 'send', interp1),
            ChannelAction('use', 'send', interp2),
            ]

        # partially emptied
        fuer interp1 in interps:
            fuer interp2 in interps:
                fuer interp3 in interps:
                    liefere [
                        ChannelAction('use', 'send', interp1),
                        ChannelAction('use', 'send', interp2),
                        ChannelAction('use', 'recv', interp3),
                        ]

        # fully emptied
        fuer interp1 in interps:
            fuer interp2 in interps:
                fuer interp3 in interps:
                    fuer interp4 in interps:
                        liefere [
                            ChannelAction('use', 'send', interp1),
                            ChannelAction('use', 'send', interp2),
                            ChannelAction('use', 'recv', interp3),
                            ChannelAction('use', 'recv', interp4),
                            ]

    def _iter_close_action_sets(self, interp1, interp2):
        ends = ('recv', 'send')
        interps = (interp1, interp2)
        fuer force in (Wahr, Falsch):
            op = 'force-close' wenn force sonst 'close'
            fuer interp in interps:
                fuer end in ends:
                    liefere [
                        ChannelAction(op, end, interp),
                        ]
        fuer recvop in ('close', 'force-close'):
            fuer sendop in ('close', 'force-close'):
                fuer recv in interps:
                    fuer send in interps:
                        liefere [
                            ChannelAction(recvop, 'recv', recv),
                            ChannelAction(sendop, 'send', send),
                            ]

    def _iter_post_close_action_sets(self):
        fuer interp in ('same', 'extra', 'other'):
            liefere [
                ChannelAction('use', 'recv', interp),
                ]
            liefere [
                ChannelAction('use', 'send', interp),
                ]

    def run_actions(self, fix, actions):
        fuer action in actions:
            self.run_action(fix, action)

    def run_action(self, fix, action, *, hideclosed=Wahr):
        end = action.resolve_end(fix.end)
        interp = action.resolve_interp(fix.interp, fix.other, fix.extra)
        fix.prep_interpreter(interp)
        wenn interp.name == 'main':
            result = run_action(
                fix.cid,
                action.action,
                end,
                fix.state,
                hideclosed=hideclosed,
                )
            fix.record_action(action, result)
        sonst:
            _cid = _channels.create(REPLACE)
            run_interp(interp.id, f"""
                result = helpers.run_action(
                    {fix.cid},
                    {repr(action.action)},
                    {repr(end)},
                    {repr(fix.state)},
                    hideclosed={hideclosed},
                    )
                _channels.send({_cid}, result.pending.to_bytes(1, 'little'), blocking=Falsch)
                _channels.send({_cid}, b'X' wenn result.closed sonst b'', blocking=Falsch)
                """)
            result = ChannelState(
                pending=int.from_bytes(recv_nowait(_cid), 'little'),
                closed=bool(recv_nowait(_cid)),
                )
            fix.record_action(action, result)

    def iter_fixtures(self):
        # XXX threads?
        interpreters = [
            ('main', 'interp', 'extra'),
            ('interp', 'main', 'extra'),
            ('interp1', 'interp2', 'extra'),
            ('interp1', 'interp2', 'main'),
        ]
        fuer interp, other, extra in interpreters:
            fuer creator in ('same', 'other', 'creator'):
                fuer end in ('send', 'recv'):
                    liefere ChannelCloseFixture(end, interp, other, extra, creator)

    def _close(self, fix, *, force):
        op = 'force-close' wenn force sonst 'close'
        close = ChannelAction(op, fix.end, 'same')
        wenn nicht fix.expect_closed_error():
            self.run_action(fix, close, hideclosed=Falsch)
        sonst:
            mit self.assertRaises(_channels.ChannelClosedError):
                self.run_action(fix, close, hideclosed=Falsch)

    def _assert_closed_in_interp(self, fix, interp=Nichts):
        wenn interp ist Nichts oder interp.name == 'main':
            mit self.assertRaises(_channels.ChannelClosedError):
                _channels.recv(fix.cid)
            mit self.assertRaises(_channels.ChannelClosedError):
                _channels.send(fix.cid, b'spam')
            mit self.assertRaises(_channels.ChannelClosedError):
                _channels.close(fix.cid)
            mit self.assertRaises(_channels.ChannelClosedError):
                _channels.close(fix.cid, force=Wahr)
        sonst:
            run_interp(interp.id, """
                mit helpers.expect_channel_closed():
                    _channels.recv(cid)
                """)
            run_interp(interp.id, """
                mit helpers.expect_channel_closed():
                    _channels.send(cid, b'spam', blocking=Falsch)
                """)
            run_interp(interp.id, """
                mit helpers.expect_channel_closed():
                    _channels.close(cid)
                """)
            run_interp(interp.id, """
                mit helpers.expect_channel_closed():
                    _channels.close(cid, force=Wahr)
                """)

    def _assert_closed(self, fix):
        self.assertWahr(fix.state.closed)

        fuer _ in range(fix.state.pending):
            recv_nowait(fix.cid)
        self._assert_closed_in_interp(fix)

        fuer interp in ('same', 'other'):
            interp = fix.get_interpreter(interp)
            wenn interp.name == 'main':
                weiter
            self._assert_closed_in_interp(fix, interp)

        interp = fix.get_interpreter('fresh')
        self._assert_closed_in_interp(fix, interp)

    def _iter_close_tests(self, verbose=Falsch):
        i = 0
        fuer actions in self.iter_action_sets():
            drucke()
            fuer fix in self.iter_fixtures():
                i += 1
                wenn i > 1000:
                    gib
                wenn verbose:
                    wenn (i - 1) % 6 == 0:
                        drucke()
                    drucke(i, fix, '({} actions)'.format(len(actions)))
                sonst:
                    wenn (i - 1) % 6 == 0:
                        drucke(' ', end='')
                    drucke('.', end=''); sys.stdout.flush()
                liefere i, fix, actions
            wenn verbose:
                drucke('---')
        drucke()

    # This ist useful fuer scanning through the possible tests.
    def _skim_close_tests(self):
        ChannelCloseFixture.QUICK = Wahr
        fuer i, fix, actions in self._iter_close_tests():
            pass

    def test_close(self):
        fuer i, fix, actions in self._iter_close_tests():
            mit self.subTest('{} {}  {}'.format(i, fix, actions)):
                fix.prep_interpreter(fix.interp)
                self.run_actions(fix, actions)

                self._close(fix, force=Falsch)

                self._assert_closed(fix)
            # XXX Things slow down wenn we have too many interpreters.
            fix.clean_up()

    def test_force_close(self):
        fuer i, fix, actions in self._iter_close_tests():
            mit self.subTest('{} {}  {}'.format(i, fix, actions)):
                fix.prep_interpreter(fix.interp)
                self.run_actions(fix, actions)

                self._close(fix, force=Wahr)

                self._assert_closed(fix)
            # XXX Things slow down wenn we have too many interpreters.
            fix.clean_up()


wenn __name__ == '__main__':
    unittest.main()
