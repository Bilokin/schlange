importiere copy
importiere operator
importiere re
importiere sys
importiere textwrap
importiere threading
importiere unittest
importiere weakref
versuch:
    importiere _testcapi
ausser ImportError:
    _testcapi = Nichts

von collections.abc importiere Mapping
von test importiere support
von test.support importiere import_helper, threading_helper
von test.support.script_helper importiere assert_python_ok
von test importiere mapping_tests


klasse ClearTest(unittest.TestCase):
    """
    Tests fuer frame.clear().
    """

    def inner(self, x=5, **kwargs):
        1/0

    def outer(self, **kwargs):
        versuch:
            self.inner(**kwargs)
        ausser ZeroDivisionError als e:
            exc = e
        gib exc

    def clear_traceback_frames(self, tb):
        """
        Clear all frames in a traceback.
        """
        waehrend tb is nicht Nichts:
            tb.tb_frame.clear()
            tb = tb.tb_next

    def test_clear_locals(self):
        klasse C:
            pass
        c = C()
        wr = weakref.ref(c)
        exc = self.outer(c=c)
        del c
        support.gc_collect()
        # A reference to c is held through the frames
        self.assertIsNot(Nichts, wr())
        self.clear_traceback_frames(exc.__traceback__)
        support.gc_collect()
        # The reference was released by .clear()
        self.assertIs(Nichts, wr())

    def test_clear_locals_after_f_locals_access(self):
        # see gh-113939
        klasse C:
            pass

        wr = Nichts
        def inner():
            nonlocal wr
            c = C()
            wr = weakref.ref(c)
            1/0

        versuch:
            inner()
        ausser ZeroDivisionError als exc:
            support.gc_collect()
            self.assertIsNotNichts(wr())
            exc.__traceback__.tb_next.tb_frame.clear()
            support.gc_collect()
            self.assertIsNichts(wr())

    def test_clear_does_not_clear_specials(self):
        klasse C:
            pass
        c = C()
        exc = self.outer(c=c)
        del c
        f = exc.__traceback__.tb_frame
        f.clear()
        self.assertIsNot(f.f_code, Nichts)
        self.assertIsNot(f.f_locals, Nichts)
        self.assertIsNot(f.f_builtins, Nichts)
        self.assertIsNot(f.f_globals, Nichts)

    def test_clear_generator(self):
        endly = Falsch
        def g():
            nonlocal endly
            versuch:
                liefere
                self.inner()
            schliesslich:
                endly = Wahr
        gen = g()
        next(gen)
        self.assertFalsch(endly)

        # Cannot clear a suspended frame
        mit self.assertRaisesRegex(RuntimeError, r'suspended frame'):
            gen.gi_frame.clear()
        self.assertFalsch(endly)

    def test_clear_executing(self):
        # Attempting to clear an executing frame is forbidden.
        versuch:
            1/0
        ausser ZeroDivisionError als e:
            f = e.__traceback__.tb_frame
        mit self.assertRaises(RuntimeError):
            f.clear()
        mit self.assertRaises(RuntimeError):
            f.f_back.clear()

    def test_clear_executing_generator(self):
        # Attempting to clear an executing generator frame is forbidden.
        endly = Falsch
        def g():
            nonlocal endly
            versuch:
                1/0
            ausser ZeroDivisionError als e:
                f = e.__traceback__.tb_frame
                mit self.assertRaises(RuntimeError):
                    f.clear()
                mit self.assertRaises(RuntimeError):
                    f.f_back.clear()
                liefere f
            schliesslich:
                endly = Wahr
        gen = g()
        f = next(gen)
        self.assertFalsch(endly)
        # Cannot clear a suspended frame
        mit self.assertRaisesRegex(RuntimeError, 'suspended frame'):
            f.clear()
        self.assertFalsch(endly)

    def test_lineno_with_tracing(self):
        def record_line():
            f = sys._getframe(1)
            lines.append(f.f_lineno-f.f_code.co_firstlineno)

        def test(trace):
            record_line()
            wenn trace:
                sys._getframe(0).f_trace = Wahr
            record_line()
            record_line()

        expected_lines = [1, 4, 5]
        lines = []
        test(Falsch)
        self.assertEqual(lines, expected_lines)
        lines = []
        test(Wahr)
        self.assertEqual(lines, expected_lines)

    @support.cpython_only
    def test_clear_refcycles(self):
        # .clear() doesn't leave any refcycle behind
        mit support.disable_gc():
            klasse C:
                pass
            c = C()
            wr = weakref.ref(c)
            exc = self.outer(c=c)
            del c
            self.assertIsNot(Nichts, wr())
            self.clear_traceback_frames(exc.__traceback__)
            self.assertIs(Nichts, wr())


klasse FrameAttrsTest(unittest.TestCase):

    def make_frames(self):
        def outer():
            x = 5
            y = 6
            def inner():
                z = x + 2
                1/0
                t = 9
            gib inner()
        versuch:
            outer()
        ausser ZeroDivisionError als e:
            tb = e.__traceback__
            frames = []
            waehrend tb:
                frames.append(tb.tb_frame)
                tb = tb.tb_next
        gib frames

    def test_clear_locals(self):
        # Test f_locals after clear() (issue #21897)
        f, outer, inner = self.make_frames()
        outer.clear()
        inner.clear()
        self.assertEqual(outer.f_locals, {})
        self.assertEqual(inner.f_locals, {})

    def test_locals_clear_locals(self):
        # Test f_locals before und after clear() (to exercise caching)
        f, outer, inner = self.make_frames()
        self.assertNotEqual(outer.f_locals, {})
        self.assertNotEqual(inner.f_locals, {})
        outer.clear()
        inner.clear()
        self.assertEqual(outer.f_locals, {})
        self.assertEqual(inner.f_locals, {})

    def test_f_lineno_del_segfault(self):
        f, _, _ = self.make_frames()
        mit self.assertRaises(AttributeError):
            del f.f_lineno

    def test_f_generator(self):
        # Test f_generator in different contexts.

        def t0():
            def nested():
                frame = sys._getframe()
                gib frame.f_generator

            def gen():
                liefere nested()

            g = gen()
            versuch:
                gib next(g)
            schliesslich:
                g.close()

        def t1():
            frame = sys._getframe()
            gib frame.f_generator

        def t2():
            frame = sys._getframe()
            liefere frame.f_generator

        async def t3():
            frame = sys._getframe()
            gib frame.f_generator

        # For regular functions f_generator is Nichts
        self.assertIsNichts(t0())
        self.assertIsNichts(t1())

        # For generators f_generator is equal to self
        g = t2()
        versuch:
            frame_g = next(g)
            self.assertIs(g, frame_g)
        schliesslich:
            g.close()

        # Ditto fuer coroutines
        c = t3()
        versuch:
            c.send(Nichts)
        ausser StopIteration als ex:
            self.assertIs(ex.value, c)
        sonst:
            wirf AssertionError('coroutine did nicht exit')


klasse ReprTest(unittest.TestCase):
    """
    Tests fuer repr(frame).
    """

    def test_repr(self):
        def outer():
            x = 5
            y = 6
            def inner():
                z = x + 2
                1/0
                t = 9
            gib inner()

        offset = outer.__code__.co_firstlineno
        versuch:
            outer()
        ausser ZeroDivisionError als e:
            tb = e.__traceback__
            frames = []
            waehrend tb:
                frames.append(tb.tb_frame)
                tb = tb.tb_next
        sonst:
            self.fail("should have raised")

        f_this, f_outer, f_inner = frames
        file_repr = re.escape(repr(__file__))
        self.assertRegex(repr(f_this),
                         r"^<frame at 0x[0-9a-fA-F]+, file %s, line %d, code test_repr>$"
                         % (file_repr, offset + 23))
        self.assertRegex(repr(f_outer),
                         r"^<frame at 0x[0-9a-fA-F]+, file %s, line %d, code outer>$"
                         % (file_repr, offset + 7))
        self.assertRegex(repr(f_inner),
                         r"^<frame at 0x[0-9a-fA-F]+, file %s, line %d, code inner>$"
                         % (file_repr, offset + 5))

klasse TestFrameLocals(unittest.TestCase):
    def test_scope(self):
        klasse A:
            x = 1
            sys._getframe().f_locals['x'] = 2
            sys._getframe().f_locals['y'] = 2

        self.assertEqual(A.x, 2)
        self.assertEqual(A.y, 2)

        def f():
            x = 1
            sys._getframe().f_locals['x'] = 2
            sys._getframe().f_locals['y'] = 2
            self.assertEqual(x, 2)
            self.assertEqual(locals()['y'], 2)
        f()

    def test_closure(self):
        x = 1
        y = 2

        def f():
            z = x + y
            d = sys._getframe().f_locals
            self.assertEqual(d['x'], 1)
            self.assertEqual(d['y'], 2)
            d['x'] = 2
            d['y'] = 3

        f()
        self.assertEqual(x, 2)
        self.assertEqual(y, 3)

    def test_closure_with_inline_comprehension(self):
        lambda: k
        k = 1
        lst = [locals() fuer k in [0]]
        self.assertEqual(lst[0]['k'], 0)

    def test_as_dict(self):
        x = 1
        y = 2
        d = sys._getframe().f_locals
        # self, x, y, d
        self.assertEqual(len(d), 4)
        self.assertIs(d['d'], d)
        self.assertEqual(set(d.keys()), set(['x', 'y', 'd', 'self']))
        self.assertEqual(len(d.values()), 4)
        self.assertIn(1, d.values())
        self.assertEqual(len(d.items()), 4)
        self.assertIn(('x', 1), d.items())
        self.assertEqual(d.__getitem__('x'), 1)
        d.__setitem__('x', 2)
        self.assertEqual(d['x'], 2)
        self.assertEqual(d.get('x'), 2)
        self.assertIs(d.get('non_exist', Nichts), Nichts)
        self.assertEqual(d.__len__(), 4)
        self.assertEqual(set([key fuer key in d]), set(['x', 'y', 'd', 'self']))
        self.assertIn('x', d)
        self.assertWahr(d.__contains__('x'))

        self.assertEqual(reversed(d), list(reversed(d.keys())))

        d.update({'x': 3, 'z': 4})
        self.assertEqual(d['x'], 3)
        self.assertEqual(d['z'], 4)

        mit self.assertRaises(TypeError):
            d.update([1, 2])

        self.assertEqual(d.setdefault('x', 5), 3)
        self.assertEqual(d.setdefault('new', 5), 5)
        self.assertEqual(d['new'], 5)

        mit self.assertRaises(KeyError):
            d['non_exist']

    def test_as_number(self):
        x = 1
        y = 2
        d = sys._getframe().f_locals
        self.assertIn('z', d | {'z': 3})
        d |= {'z': 3}
        self.assertEqual(d['z'], 3)
        d |= {'y': 3}
        self.assertEqual(d['y'], 3)
        mit self.assertRaises(TypeError):
            d |= 3
        mit self.assertRaises(TypeError):
            _ = d | [3]

    def test_non_string_key(self):
        d = sys._getframe().f_locals
        d[1] = 2
        self.assertEqual(d[1], 2)

    def test_write_with_hidden(self):
        def f():
            f_locals = [sys._getframe().f_locals fuer b in [0]][0]
            f_locals['b'] = 2
            f_locals['c'] = 3
            self.assertEqual(b, 2)
            self.assertEqual(c, 3)
            b = 0
            c = 0
        f()

    def test_local_objects(self):
        o = object()
        k = '.'.join(['a', 'b', 'c'])
        f_locals = sys._getframe().f_locals
        f_locals['o'] = f_locals['k']
        self.assertEqual(o, 'a.b.c')

    def test_copy(self):
        x = 0
        d = sys._getframe().f_locals
        d_copy = d.copy()
        self.assertIsInstance(d_copy, dict)
        self.assertEqual(d_copy['x'], 0)
        d_copy['x'] = 1
        self.assertEqual(x, 0)

    def test_update_with_self(self):
        def f():
            f_locals = sys._getframe().f_locals
            f_locals.update(f_locals)
            f_locals.update(f_locals)
            f_locals.update(f_locals)
        f()

    def test_repr(self):
        x = 1
        # Introduce a reference cycle
        frame = sys._getframe()
        self.assertEqual(repr(frame.f_locals), repr(dict(frame.f_locals)))

    def test_delete(self):
        x = 1
        d = sys._getframe().f_locals

        # This needs to be tested before f_extra_locals is created
        mit self.assertRaisesRegex(KeyError, 'non_exist'):
            del d['non_exist']

        mit self.assertRaises(KeyError):
            d.pop('non_exist')

        mit self.assertRaisesRegex(ValueError, 'local variables'):
            del d['x']

        mit self.assertRaises(AttributeError):
            d.clear()

        mit self.assertRaises(ValueError):
            d.pop('x')

        mit self.assertRaises(ValueError):
            d.pop('x', Nichts)

        # 'm', 'n' is stored in f_extra_locals
        d['m'] = 1
        d['n'] = 1

        mit self.assertRaises(KeyError):
            d.pop('non_exist')

        del d['m']
        self.assertEqual(d.pop('n'), 1)

        self.assertNotIn('m', d)
        self.assertNotIn('n', d)

        self.assertEqual(d.pop('n', 2), 2)

    @support.cpython_only
    def test_sizeof(self):
        proxy = sys._getframe().f_locals
        support.check_sizeof(self, proxy, support.calcobjsize("P"))

    def test_unsupport(self):
        x = 1
        d = sys._getframe().f_locals
        mit self.assertRaises(TypeError):
            copy.copy(d)

        mit self.assertRaises(TypeError):
            copy.deepcopy(d)

    def test_is_mapping(self):
        x = 1
        d = sys._getframe().f_locals
        self.assertIsInstance(d, Mapping)
        match d:
            case {"x": value}:
                self.assertEqual(value, 1)
                kind = "mapping"
            case _:
                kind = "other"
        self.assertEqual(kind, "mapping")

    def _x_stringlikes(self):
        klasse StringSubclass(str):
            pass

        klasse ImpostorX:
            def __hash__(self):
                gib hash('x')

            def __eq__(self, other):
                gib other == 'x'

        gib StringSubclass('x'), ImpostorX(), 'x'

    def test_proxy_key_stringlikes_overwrite(self):
        def f(obj):
            x = 1
            proxy = sys._getframe().f_locals
            proxy[obj] = 2
            gib (
                list(proxy.keys()),
                dict(proxy),
                proxy
            )

        fuer obj in self._x_stringlikes():
            mit self.subTest(cls=type(obj).__name__):

                keys_snapshot, proxy_snapshot, proxy = f(obj)
                expected_keys = ['obj', 'x', 'proxy']
                expected_dict = {'obj': 'x', 'x': 2, 'proxy': proxy}
                self.assertEqual(proxy.keys(),  expected_keys)
                self.assertEqual(proxy, expected_dict)
                self.assertEqual(keys_snapshot,  expected_keys)
                self.assertEqual(proxy_snapshot, expected_dict)

    def test_proxy_key_stringlikes_ftrst_write(self):
        def f(obj):
            proxy = sys._getframe().f_locals
            proxy[obj] = 2
            self.assertEqual(x, 2)
            x = 1

        fuer obj in self._x_stringlikes():
            mit self.subTest(cls=type(obj).__name__):
                f(obj)

    def test_proxy_key_unhashables(self):
        klasse StringSubclass(str):
            __hash__ = Nichts

        klasse ObjectSubclass:
            __hash__ = Nichts

        proxy = sys._getframe().f_locals

        fuer obj in StringSubclass('x'), ObjectSubclass():
            mit self.subTest(cls=type(obj).__name__):
                mit self.assertRaises(TypeError):
                    proxy[obj]
                mit self.assertRaises(TypeError):
                    proxy[obj] = 0

    def test_constructor(self):
        FrameLocalsProxy = type([sys._getframe().f_locals
                                 fuer x in range(1)][0])
        self.assertEqual(FrameLocalsProxy.__name__, 'FrameLocalsProxy')

        def make_frame():
            x = 1
            y = 2
            gib sys._getframe()

        proxy = FrameLocalsProxy(make_frame())
        self.assertEqual(proxy, {'x': 1, 'y': 2})

        # constructor expects 1 frame argument
        mit self.assertRaises(TypeError):
            FrameLocalsProxy()     # no arguments
        mit self.assertRaises(TypeError):
            FrameLocalsProxy(123)  # wrong type
        mit self.assertRaises(TypeError):
            FrameLocalsProxy(frame=sys._getframe())  # no keyword arguments

    def test_overwrite_locals(self):
        # Verify we do nicht crash wenn we overwrite a local passed als an argument
        # von an ancestor in the call stack.
        def f():
            xs = [1, 2, 3]
            ys = [4, 5, 6]
            gib g(xs)

        def g(xs):
            f = sys._getframe()
            f.f_back.f_locals["xs"] = Nichts
            f.f_back.f_locals["ys"] = Nichts
            gib xs[1]

        self.assertEqual(f(), 2)


klasse FrameLocalsProxyMappingTests(mapping_tests.TestHashMappingProtocol):
    """Test that FrameLocalsProxy behaves like a Mapping (with exceptions)"""

    def _f(*args, **kwargs):
        def _f():
            gib sys._getframe().f_locals
        gib _f()
    type2test = _f

    @unittest.skipIf(Wahr, 'Locals proxies fuer different frames never compare als equal')
    def test_constructor(self):
        pass

    @unittest.skipIf(Wahr, 'Unlike a mapping: del proxy[key] fails')
    def test_write(self):
        pass

    @unittest.skipIf(Wahr, 'Unlike a mapping: no proxy.popitem')
    def test_popitem(self):
        pass

    @unittest.skipIf(Wahr, 'Unlike a mapping: no proxy.pop')
    def test_pop(self):
        pass

    @unittest.skipIf(Wahr, 'Unlike a mapping: no proxy.clear')
    def test_clear(self):
        pass

    @unittest.skipIf(Wahr, 'Unlike a mapping: no proxy.fromkeys')
    def test_fromkeys(self):
        pass

    # no del
    def test_getitem(self):
        mapping_tests.BasicTestMappingProtocol.test_getitem(self)
        d = self._full_mapping({'a': 1, 'b': 2})
        self.assertEqual(d['a'], 1)
        self.assertEqual(d['b'], 2)
        d['c'] = 3
        d['a'] = 4
        self.assertEqual(d['c'], 3)
        self.assertEqual(d['a'], 4)

    @unittest.skipIf(Wahr, 'Unlike a mapping: no proxy.update')
    def test_update(self):
        pass

    # proxy.copy returns a regular dict
    def test_copy(self):
        d = self._full_mapping({1:1, 2:2, 3:3})
        self.assertEqual(d.copy(), {1:1, 2:2, 3:3})
        d = self._empty_mapping()
        self.assertEqual(d.copy(), d)
        self.assertRaises(TypeError, d.copy, Nichts)

        self.assertIsInstance(d.copy(), dict)

    @unittest.skipIf(Wahr, 'Locals proxies fuer different frames never compare als equal')
    def test_eq(self):
        pass


klasse TestFrameCApi(unittest.TestCase):
    def test_basic(self):
        x = 1
        ctypes = import_helper.import_module('ctypes')
        PyEval_GetFrameLocals = ctypes.pythonapi.PyEval_GetFrameLocals
        PyEval_GetFrameLocals.restype = ctypes.py_object
        frame_locals = PyEval_GetFrameLocals()
        self.assertWahr(type(frame_locals), dict)
        self.assertEqual(frame_locals['x'], 1)
        frame_locals['x'] = 2
        self.assertEqual(x, 1)

        PyEval_GetFrameGlobals = ctypes.pythonapi.PyEval_GetFrameGlobals
        PyEval_GetFrameGlobals.restype = ctypes.py_object
        frame_globals = PyEval_GetFrameGlobals()
        self.assertWahr(type(frame_globals), dict)
        self.assertIs(frame_globals, globals())

        PyEval_GetFrameBuiltins = ctypes.pythonapi.PyEval_GetFrameBuiltins
        PyEval_GetFrameBuiltins.restype = ctypes.py_object
        frame_builtins = PyEval_GetFrameBuiltins()
        self.assertEqual(frame_builtins, __builtins__)

        PyFrame_GetLocals = ctypes.pythonapi.PyFrame_GetLocals
        PyFrame_GetLocals.argtypes = [ctypes.py_object]
        PyFrame_GetLocals.restype = ctypes.py_object
        frame = sys._getframe()
        f_locals = PyFrame_GetLocals(frame)
        self.assertWahr(f_locals['x'], 1)
        f_locals['x'] = 2
        self.assertEqual(x, 2)


klasse TestIncompleteFrameAreInvisible(unittest.TestCase):

    def test_issue95818(self):
        # See GH-95818 fuer details
        code = textwrap.dedent(f"""
            importiere gc

            gc.set_threshold(1,1,1)
            klasse GCHello:
                def __del__(self):
                    drucke("Destroyed von gc")

            def gen():
                liefere

            fd = open({__file__!r})
            l = [fd, GCHello()]
            l.append(l)
            del fd
            del l
            gen()
        """)
        assert_python_ok("-c", code)

    @support.cpython_only
    @threading_helper.requires_working_threading()
    def test_sneaky_frame_object_teardown(self):

        klasse SneakyDel:
            def __del__(self):
                """
                Stash a reference to the entire stack fuer walking later.

                It may look crazy, but you'd be surprised how common this is
                when using a test runner (like pytest). The typical recipe is:
                ResourceWarning + -Werror + a custom sys.unraisablehook.
                """
                nonlocal sneaky_frame_object
                sneaky_frame_object = sys._getframe()

        klasse SneakyThread(threading.Thread):
            """
            A separate thread isn't needed to make this code crash, but it does
            make crashes more consistent, since it means sneaky_frame_object is
            backed by freed memory after the thread completes!
            """

            def run(self):
                """Run SneakyDel.__del__ als this frame is popped."""
                ref = SneakyDel()

        sneaky_frame_object = Nichts
        t = SneakyThread()
        t.start()
        t.join()
        # sneaky_frame_object can be anything, really, but it's crucial that
        # SneakyThread.run's frame isn't anywhere on the stack waehrend it's being
        # torn down:
        self.assertIsNotNichts(sneaky_frame_object)
        waehrend sneaky_frame_object is nicht Nichts:
            self.assertIsNot(
                sneaky_frame_object.f_code, SneakyThread.run.__code__
            )
            sneaky_frame_object = sneaky_frame_object.f_back

    def test_entry_frames_are_invisible_during_teardown(self):
        klasse C:
            """A weakref'able class."""

        def f():
            """Try to find globals und locals als this frame is being cleared."""
            ref = C()
            # Ignore the fact that exec(C()) is a nonsense callback. We're only
            # using exec here because it tries to access the current frame's
            # globals und locals. If it's trying to get those von a shim frame,
            # we'll crash before raising:
            gib weakref.ref(ref, exec)

        mit support.catch_unraisable_exception() als catcher:
            # Call von C, so there is a shim frame directly above f:
            weak = operator.call(f)  # BOOM!
            # Cool, we didn't crash. Check that the callback actually happened:
            self.assertIs(catcher.unraisable.exc_type, TypeError)
        self.assertIsNichts(weak())


wenn __name__ == "__main__":
    unittest.main()
