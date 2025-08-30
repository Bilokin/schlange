"""Test suite fuer the sys.monitoring."""

importiere collections
importiere dis
importiere functools
importiere inspect
importiere math
importiere operator
importiere sys
importiere textwrap
importiere types
importiere unittest

importiere test.support
von test.support importiere requires_specialization_ft, script_helper

_testcapi = test.support.import_helper.import_module("_testcapi")
_testinternalcapi = test.support.import_helper.import_module("_testinternalcapi")

PAIR = (0,1)

def f1():
    pass

def f2():
    len([])
    sys.getsizeof(0)

def floop():
    fuer item in PAIR:
        pass

def gen():
    liefere
    liefere

def g1():
    fuer _ in gen():
        pass

TEST_TOOL = 2
TEST_TOOL2 = 3
TEST_TOOL3 = 4

def nth_line(func, offset):
    gib func.__code__.co_firstlineno + offset

klasse MonitoringBasicTest(unittest.TestCase):

    def tearDown(self):
        sys.monitoring.free_tool_id(TEST_TOOL)

    def test_has_objects(self):
        m = sys.monitoring
        m.events
        m.use_tool_id
        m.clear_tool_id
        m.free_tool_id
        m.get_tool
        m.get_events
        m.set_events
        m.get_local_events
        m.set_local_events
        m.register_callback
        m.restart_events
        m.DISABLE
        m.MISSING
        m.events.NO_EVENTS

    def test_tool(self):
        sys.monitoring.use_tool_id(TEST_TOOL, "MonitoringTest.Tool")
        self.assertEqual(sys.monitoring.get_tool(TEST_TOOL), "MonitoringTest.Tool")
        sys.monitoring.set_events(TEST_TOOL, 15)
        self.assertEqual(sys.monitoring.get_events(TEST_TOOL), 15)
        sys.monitoring.set_events(TEST_TOOL, 0)
        mit self.assertRaises(ValueError):
            sys.monitoring.set_events(TEST_TOOL, sys.monitoring.events.C_RETURN)
        mit self.assertRaises(ValueError):
            sys.monitoring.set_events(TEST_TOOL, sys.monitoring.events.C_RAISE)
        sys.monitoring.free_tool_id(TEST_TOOL)
        self.assertEqual(sys.monitoring.get_tool(TEST_TOOL), Nichts)
        mit self.assertRaises(ValueError):
            sys.monitoring.set_events(TEST_TOOL, sys.monitoring.events.CALL)

    def test_clear(self):
        events = []
        sys.monitoring.use_tool_id(TEST_TOOL, "MonitoringTest.Tool")
        sys.monitoring.register_callback(TEST_TOOL, E.PY_START, lambda *args: events.append(args))
        sys.monitoring.register_callback(TEST_TOOL, E.LINE, lambda *args: events.append(args))
        def f():
            a = 1
        sys.monitoring.set_local_events(TEST_TOOL, f.__code__, E.LINE)
        sys.monitoring.set_events(TEST_TOOL, E.PY_START)

        f()
        sys.monitoring.clear_tool_id(TEST_TOOL)
        f()

        # the first f() should trigger a PY_START und a LINE event
        # the second f() after clear_tool_id should nicht trigger any event
        # the callback function should be cleared als well
        self.assertEqual(len(events), 2)
        callback = sys.monitoring.register_callback(TEST_TOOL, E.LINE, Nichts)
        self.assertIs(callback, Nichts)

        sys.monitoring.free_tool_id(TEST_TOOL)

        events = []
        sys.monitoring.use_tool_id(TEST_TOOL, "MonitoringTest.Tool")
        sys.monitoring.register_callback(TEST_TOOL, E.LINE, lambda *args: events.append(args))
        sys.monitoring.set_local_events(TEST_TOOL, f.__code__, E.LINE)
        f()
        sys.monitoring.free_tool_id(TEST_TOOL)
        sys.monitoring.use_tool_id(TEST_TOOL, "MonitoringTest.Tool")
        f()
        # the first f() should trigger a LINE event, und even wenn we use the
        # tool id immediately after freeing it, the second f() should not
        # trigger any event
        self.assertEqual(len(events), 1)
        sys.monitoring.free_tool_id(TEST_TOOL)


klasse MonitoringTestBase:

    def setUp(self):
        # Check that a previous test hasn't left monitoring on.
        fuer tool in range(6):
            self.assertEqual(sys.monitoring.get_events(tool), 0)
        self.assertIs(sys.monitoring.get_tool(TEST_TOOL), Nichts)
        self.assertIs(sys.monitoring.get_tool(TEST_TOOL2), Nichts)
        self.assertIs(sys.monitoring.get_tool(TEST_TOOL3), Nichts)
        sys.monitoring.use_tool_id(TEST_TOOL, "test " + self.__class__.__name__)
        sys.monitoring.use_tool_id(TEST_TOOL2, "test2 " + self.__class__.__name__)
        sys.monitoring.use_tool_id(TEST_TOOL3, "test3 " + self.__class__.__name__)

    def tearDown(self):
        # Check that test hasn't left monitoring on.
        fuer tool in range(6):
            self.assertEqual(sys.monitoring.get_events(tool), 0)
        sys.monitoring.free_tool_id(TEST_TOOL)
        sys.monitoring.free_tool_id(TEST_TOOL2)
        sys.monitoring.free_tool_id(TEST_TOOL3)


klasse MonitoringCountTest(MonitoringTestBase, unittest.TestCase):

    def check_event_count(self, func, event, expected):

        klasse Counter:
            def __init__(self):
                self.count = 0
            def __call__(self, *args):
                self.count += 1

        counter = Counter()
        sys.monitoring.register_callback(TEST_TOOL, event, counter)
        wenn event == E.C_RETURN oder event == E.C_RAISE:
            sys.monitoring.set_events(TEST_TOOL, E.CALL)
        sonst:
            sys.monitoring.set_events(TEST_TOOL, event)
        self.assertEqual(counter.count, 0)
        counter.count = 0
        func()
        self.assertEqual(counter.count, expected)
        prev = sys.monitoring.register_callback(TEST_TOOL, event, Nichts)
        counter.count = 0
        func()
        self.assertEqual(counter.count, 0)
        self.assertEqual(prev, counter)
        sys.monitoring.set_events(TEST_TOOL, 0)

    def test_start_count(self):
        self.check_event_count(f1, E.PY_START, 1)

    def test_resume_count(self):
        self.check_event_count(g1, E.PY_RESUME, 2)

    def test_return_count(self):
        self.check_event_count(f1, E.PY_RETURN, 1)

    def test_call_count(self):
        self.check_event_count(f2, E.CALL, 3)

    def test_c_return_count(self):
        self.check_event_count(f2, E.C_RETURN, 2)


E = sys.monitoring.events

INSTRUMENTED_EVENTS = [
    (E.PY_START, "start"),
    (E.PY_RESUME, "resume"),
    (E.PY_RETURN, "return"),
    (E.PY_YIELD, "yield"),
    (E.JUMP, "jump"),
    (E.BRANCH, "branch"),
]

EXCEPT_EVENTS = [
    (E.RAISE, "raise"),
    (E.PY_UNWIND, "unwind"),
    (E.EXCEPTION_HANDLED, "exception_handled"),
]

SIMPLE_EVENTS = INSTRUMENTED_EVENTS + EXCEPT_EVENTS + [
    (E.C_RAISE, "c_raise"),
    (E.C_RETURN, "c_return"),
]


SIMPLE_EVENT_SET = functools.reduce(operator.or_, [ev fuer (ev, _) in SIMPLE_EVENTS], 0) | E.CALL


def just_pass():
    pass

just_pass.events = [
    "py_call",
    "start",
    "return",
]

def just_raise():
    wirf Exception

just_raise.events = [
    'py_call',
    "start",
    "raise",
    "unwind",
]

def just_call():
    len([])

just_call.events = [
    'py_call',
    "start",
    "c_call",
    "c_return",
    "return",
]

def caught():
    versuch:
        1/0
    ausser Exception:
        pass

caught.events = [
    'py_call',
    "start",
    "raise",
    "exception_handled",
    "branch",
    "return",
]

def nested_call():
    just_pass()

nested_call.events = [
    "py_call",
    "start",
    "py_call",
    "start",
    "return",
    "return",
]

PY_CALLABLES = (types.FunctionType, types.MethodType)

klasse MonitoringEventsBase(MonitoringTestBase):

    def gather_events(self, func):
        events = []
        fuer event, event_name in SIMPLE_EVENTS:
            def record(*args, event_name=event_name):
                events.append(event_name)
            sys.monitoring.register_callback(TEST_TOOL, event, record)
        def record_call(code, offset, obj, arg):
            wenn isinstance(obj, PY_CALLABLES):
                events.append("py_call")
            sonst:
                events.append("c_call")
        sys.monitoring.register_callback(TEST_TOOL, E.CALL, record_call)
        sys.monitoring.set_events(TEST_TOOL, SIMPLE_EVENT_SET)
        events = []
        versuch:
            func()
        ausser:
            pass
        sys.monitoring.set_events(TEST_TOOL, 0)
        #Remove the final event, the call to `sys.monitoring.set_events`
        events = events[:-1]
        gib events

    def check_events(self, func, expected=Nichts):
        events = self.gather_events(func)
        wenn expected is Nichts:
            expected = func.events
        self.assertEqual(events, expected)

klasse MonitoringEventsTest(MonitoringEventsBase, unittest.TestCase):

    def test_just_pass(self):
        self.check_events(just_pass)

    def test_just_raise(self):
        versuch:
            self.check_events(just_raise)
        ausser Exception:
            pass
        self.assertEqual(sys.monitoring.get_events(TEST_TOOL), 0)

    def test_just_call(self):
        self.check_events(just_call)

    def test_caught(self):
        self.check_events(caught)

    def test_nested_call(self):
        self.check_events(nested_call)

UP_EVENTS = (E.C_RETURN, E.C_RAISE, E.PY_RETURN, E.PY_UNWIND, E.PY_YIELD)
DOWN_EVENTS = (E.PY_START, E.PY_RESUME)

von test.profilee importiere testfunc

klasse SimulateProfileTest(MonitoringEventsBase, unittest.TestCase):

    def test_balanced(self):
        events = self.gather_events(testfunc)
        c = collections.Counter(events)
        self.assertEqual(c["c_call"], c["c_return"])
        self.assertEqual(c["start"], c["return"] + c["unwind"])
        self.assertEqual(c["raise"], c["exception_handled"] + c["unwind"])

    def test_frame_stack(self):
        self.maxDiff = Nichts
        stack = []
        errors = []
        seen = set()
        def up(*args):
            frame = sys._getframe(1)
            wenn nicht stack:
                errors.append("empty")
            sonst:
                expected = stack.pop()
                wenn frame != expected:
                    errors.append(f" Popping {frame} expected {expected}")
        def down(*args):
            frame = sys._getframe(1)
            stack.append(frame)
            seen.add(frame.f_code)
        def call(code, offset, callable, arg):
            wenn nicht isinstance(callable, PY_CALLABLES):
                stack.append(sys._getframe(1))
        fuer event in UP_EVENTS:
            sys.monitoring.register_callback(TEST_TOOL, event, up)
        fuer event in DOWN_EVENTS:
            sys.monitoring.register_callback(TEST_TOOL, event, down)
        sys.monitoring.register_callback(TEST_TOOL, E.CALL, call)
        sys.monitoring.set_events(TEST_TOOL, SIMPLE_EVENT_SET)
        testfunc()
        sys.monitoring.set_events(TEST_TOOL, 0)
        self.assertEqual(errors, [])
        self.assertEqual(stack, [sys._getframe()])
        self.assertEqual(len(seen), 9)


klasse CounterWithDisable:

    def __init__(self):
        self.disable = Falsch
        self.count = 0

    def __call__(self, *args):
        self.count += 1
        wenn self.disable:
            gib sys.monitoring.DISABLE


klasse RecorderWithDisable:

    def __init__(self, events):
        self.disable = Falsch
        self.events = events

    def __call__(self, code, event):
        self.events.append(event)
        wenn self.disable:
            gib sys.monitoring.DISABLE


klasse MontoringDisableAndRestartTest(MonitoringTestBase, unittest.TestCase):

    def test_disable(self):
        versuch:
            counter = CounterWithDisable()
            sys.monitoring.register_callback(TEST_TOOL, E.PY_START, counter)
            sys.monitoring.set_events(TEST_TOOL, E.PY_START)
            self.assertEqual(counter.count, 0)
            counter.count = 0
            f1()
            self.assertEqual(counter.count, 1)
            counter.disable = Wahr
            counter.count = 0
            f1()
            self.assertEqual(counter.count, 1)
            counter.count = 0
            f1()
            self.assertEqual(counter.count, 0)
            sys.monitoring.set_events(TEST_TOOL, 0)
        schliesslich:
            sys.monitoring.restart_events()

    def test_restart(self):
        versuch:
            counter = CounterWithDisable()
            sys.monitoring.register_callback(TEST_TOOL, E.PY_START, counter)
            sys.monitoring.set_events(TEST_TOOL, E.PY_START)
            counter.disable = Wahr
            f1()
            counter.count = 0
            f1()
            self.assertEqual(counter.count, 0)
            sys.monitoring.restart_events()
            counter.count = 0
            f1()
            self.assertEqual(counter.count, 1)
            sys.monitoring.set_events(TEST_TOOL, 0)
        schliesslich:
            sys.monitoring.restart_events()


klasse MultipleMonitorsTest(MonitoringTestBase, unittest.TestCase):

    def test_two_same(self):
        versuch:
            self.assertEqual(sys.monitoring._all_events(), {})
            counter1 = CounterWithDisable()
            counter2 = CounterWithDisable()
            sys.monitoring.register_callback(TEST_TOOL, E.PY_START, counter1)
            sys.monitoring.register_callback(TEST_TOOL2, E.PY_START, counter2)
            sys.monitoring.set_events(TEST_TOOL, E.PY_START)
            sys.monitoring.set_events(TEST_TOOL2, E.PY_START)
            self.assertEqual(sys.monitoring.get_events(TEST_TOOL), E.PY_START)
            self.assertEqual(sys.monitoring.get_events(TEST_TOOL2), E.PY_START)
            self.assertEqual(sys.monitoring._all_events(), {'PY_START': (1 << TEST_TOOL) | (1 << TEST_TOOL2)})
            counter1.count = 0
            counter2.count = 0
            f1()
            count1 = counter1.count
            count2 = counter2.count
            self.assertEqual((count1, count2), (1, 1))
        schliesslich:
            sys.monitoring.set_events(TEST_TOOL, 0)
            sys.monitoring.set_events(TEST_TOOL2, 0)
            sys.monitoring.register_callback(TEST_TOOL, E.PY_START, Nichts)
            sys.monitoring.register_callback(TEST_TOOL2, E.PY_START, Nichts)
            self.assertEqual(sys.monitoring._all_events(), {})

    def test_three_same(self):
        versuch:
            self.assertEqual(sys.monitoring._all_events(), {})
            counter1 = CounterWithDisable()
            counter2 = CounterWithDisable()
            counter3 = CounterWithDisable()
            sys.monitoring.register_callback(TEST_TOOL, E.PY_START, counter1)
            sys.monitoring.register_callback(TEST_TOOL2, E.PY_START, counter2)
            sys.monitoring.register_callback(TEST_TOOL3, E.PY_START, counter3)
            sys.monitoring.set_events(TEST_TOOL, E.PY_START)
            sys.monitoring.set_events(TEST_TOOL2, E.PY_START)
            sys.monitoring.set_events(TEST_TOOL3, E.PY_START)
            self.assertEqual(sys.monitoring.get_events(TEST_TOOL), E.PY_START)
            self.assertEqual(sys.monitoring.get_events(TEST_TOOL2), E.PY_START)
            self.assertEqual(sys.monitoring.get_events(TEST_TOOL3), E.PY_START)
            self.assertEqual(sys.monitoring._all_events(), {'PY_START': (1 << TEST_TOOL) | (1 << TEST_TOOL2) | (1 << TEST_TOOL3)})
            counter1.count = 0
            counter2.count = 0
            counter3.count = 0
            f1()
            count1 = counter1.count
            count2 = counter2.count
            count3 = counter3.count
            self.assertEqual((count1, count2, count3), (1, 1, 1))
        schliesslich:
            sys.monitoring.set_events(TEST_TOOL, 0)
            sys.monitoring.set_events(TEST_TOOL2, 0)
            sys.monitoring.set_events(TEST_TOOL3, 0)
            sys.monitoring.register_callback(TEST_TOOL, E.PY_START, Nichts)
            sys.monitoring.register_callback(TEST_TOOL2, E.PY_START, Nichts)
            sys.monitoring.register_callback(TEST_TOOL3, E.PY_START, Nichts)
            self.assertEqual(sys.monitoring._all_events(), {})

    def test_two_different(self):
        versuch:
            self.assertEqual(sys.monitoring._all_events(), {})
            counter1 = CounterWithDisable()
            counter2 = CounterWithDisable()
            sys.monitoring.register_callback(TEST_TOOL, E.PY_START, counter1)
            sys.monitoring.register_callback(TEST_TOOL2, E.PY_RETURN, counter2)
            sys.monitoring.set_events(TEST_TOOL, E.PY_START)
            sys.monitoring.set_events(TEST_TOOL2, E.PY_RETURN)
            self.assertEqual(sys.monitoring.get_events(TEST_TOOL), E.PY_START)
            self.assertEqual(sys.monitoring.get_events(TEST_TOOL2), E.PY_RETURN)
            self.assertEqual(sys.monitoring._all_events(), {'PY_START': 1 << TEST_TOOL, 'PY_RETURN': 1 << TEST_TOOL2})
            counter1.count = 0
            counter2.count = 0
            f1()
            count1 = counter1.count
            count2 = counter2.count
            self.assertEqual((count1, count2), (1, 1))
        schliesslich:
            sys.monitoring.set_events(TEST_TOOL, 0)
            sys.monitoring.set_events(TEST_TOOL2, 0)
            sys.monitoring.register_callback(TEST_TOOL, E.PY_START, Nichts)
            sys.monitoring.register_callback(TEST_TOOL2, E.PY_RETURN, Nichts)
            self.assertEqual(sys.monitoring._all_events(), {})

    def test_two_with_disable(self):
        versuch:
            self.assertEqual(sys.monitoring._all_events(), {})
            counter1 = CounterWithDisable()
            counter2 = CounterWithDisable()
            sys.monitoring.register_callback(TEST_TOOL, E.PY_START, counter1)
            sys.monitoring.register_callback(TEST_TOOL2, E.PY_START, counter2)
            sys.monitoring.set_events(TEST_TOOL, E.PY_START)
            sys.monitoring.set_events(TEST_TOOL2, E.PY_START)
            self.assertEqual(sys.monitoring.get_events(TEST_TOOL), E.PY_START)
            self.assertEqual(sys.monitoring.get_events(TEST_TOOL2), E.PY_START)
            self.assertEqual(sys.monitoring._all_events(), {'PY_START': (1 << TEST_TOOL) | (1 << TEST_TOOL2)})
            counter1.count = 0
            counter2.count = 0
            counter1.disable = Wahr
            f1()
            count1 = counter1.count
            count2 = counter2.count
            self.assertEqual((count1, count2), (1, 1))
            counter1.count = 0
            counter2.count = 0
            f1()
            count1 = counter1.count
            count2 = counter2.count
            self.assertEqual((count1, count2), (0, 1))
        schliesslich:
            sys.monitoring.set_events(TEST_TOOL, 0)
            sys.monitoring.set_events(TEST_TOOL2, 0)
            sys.monitoring.register_callback(TEST_TOOL, E.PY_START, Nichts)
            sys.monitoring.register_callback(TEST_TOOL2, E.PY_START, Nichts)
            self.assertEqual(sys.monitoring._all_events(), {})
            sys.monitoring.restart_events()

    def test_with_instruction_event(self):
        """Test that the second tool can set events mit instruction events set by the first tool."""
        def f():
            pass
        code = f.__code__

        versuch:
            self.assertEqual(sys.monitoring._all_events(), {})
            sys.monitoring.set_local_events(TEST_TOOL, code, E.INSTRUCTION | E.LINE)
            sys.monitoring.set_local_events(TEST_TOOL2, code, E.LINE)
        schliesslich:
            sys.monitoring.set_events(TEST_TOOL, 0)
            sys.monitoring.set_events(TEST_TOOL2, 0)
            self.assertEqual(sys.monitoring._all_events(), {})


klasse LineMonitoringTest(MonitoringTestBase, unittest.TestCase):

    def test_lines_single(self):
        versuch:
            self.assertEqual(sys.monitoring._all_events(), {})
            events = []
            recorder = RecorderWithDisable(events)
            sys.monitoring.register_callback(TEST_TOOL, E.LINE, recorder)
            sys.monitoring.set_events(TEST_TOOL, E.LINE)
            f1()
            sys.monitoring.set_events(TEST_TOOL, 0)
            sys.monitoring.register_callback(TEST_TOOL, E.LINE, Nichts)
            start = nth_line(LineMonitoringTest.test_lines_single, 0)
            self.assertEqual(events, [start+7, nth_line(f1, 1), start+8])
        schliesslich:
            sys.monitoring.set_events(TEST_TOOL, 0)
            sys.monitoring.register_callback(TEST_TOOL, E.LINE, Nichts)
            self.assertEqual(sys.monitoring._all_events(), {})
            sys.monitoring.restart_events()

    def test_lines_loop(self):
        versuch:
            self.assertEqual(sys.monitoring._all_events(), {})
            events = []
            recorder = RecorderWithDisable(events)
            sys.monitoring.register_callback(TEST_TOOL, E.LINE, recorder)
            sys.monitoring.set_events(TEST_TOOL, E.LINE)
            floop()
            sys.monitoring.set_events(TEST_TOOL, 0)
            sys.monitoring.register_callback(TEST_TOOL, E.LINE, Nichts)
            start = nth_line(LineMonitoringTest.test_lines_loop, 0)
            floop_1 = nth_line(floop, 1)
            floop_2 = nth_line(floop, 2)
            self.assertEqual(
                events,
                [start+7, floop_1, floop_2, floop_1, floop_2, floop_1, start+8]
            )
        schliesslich:
            sys.monitoring.set_events(TEST_TOOL, 0)
            sys.monitoring.register_callback(TEST_TOOL, E.LINE, Nichts)
            self.assertEqual(sys.monitoring._all_events(), {})
            sys.monitoring.restart_events()

    def test_lines_two(self):
        versuch:
            self.assertEqual(sys.monitoring._all_events(), {})
            events = []
            recorder = RecorderWithDisable(events)
            events2 = []
            recorder2 = RecorderWithDisable(events2)
            sys.monitoring.register_callback(TEST_TOOL, E.LINE, recorder)
            sys.monitoring.register_callback(TEST_TOOL2, E.LINE, recorder2)
            sys.monitoring.set_events(TEST_TOOL, E.LINE); sys.monitoring.set_events(TEST_TOOL2, E.LINE)
            f1()
            sys.monitoring.set_events(TEST_TOOL, 0); sys.monitoring.set_events(TEST_TOOL2, 0)
            sys.monitoring.register_callback(TEST_TOOL, E.LINE, Nichts)
            sys.monitoring.register_callback(TEST_TOOL2, E.LINE, Nichts)
            start = nth_line(LineMonitoringTest.test_lines_two, 0)
            expected = [start+10, nth_line(f1, 1), start+11]
            self.assertEqual(events, expected)
            self.assertEqual(events2, expected)
        schliesslich:
            sys.monitoring.set_events(TEST_TOOL, 0)
            sys.monitoring.set_events(TEST_TOOL2, 0)
            sys.monitoring.register_callback(TEST_TOOL, E.LINE, Nichts)
            sys.monitoring.register_callback(TEST_TOOL2, E.LINE, Nichts)
            self.assertEqual(sys.monitoring._all_events(), {})
            sys.monitoring.restart_events()

    def check_lines(self, func, expected, tool=TEST_TOOL):
        versuch:
            self.assertEqual(sys.monitoring._all_events(), {})
            events = []
            recorder = RecorderWithDisable(events)
            sys.monitoring.register_callback(tool, E.LINE, recorder)
            sys.monitoring.set_events(tool, E.LINE)
            func()
            sys.monitoring.set_events(tool, 0)
            sys.monitoring.register_callback(tool, E.LINE, Nichts)
            lines = [ line - func.__code__.co_firstlineno fuer line in events[1:-1] ]
            self.assertEqual(lines, expected)
        schliesslich:
            sys.monitoring.set_events(tool, 0)


    def test_linear(self):

        def func():
            line = 1
            line = 2
            line = 3
            line = 4
            line = 5

        self.check_lines(func, [1,2,3,4,5])

    def test_branch(self):
        def func():
            wenn "true".startswith("t"):
                line = 2
                line = 3
            sonst:
                line = 5
            line = 6

        self.check_lines(func, [1,2,3,6])

    def test_try_except(self):

        def func1():
            versuch:
                line = 2
                line = 3
            ausser:
                line = 5
            line = 6

        self.check_lines(func1, [1,2,3,6])

        def func2():
            versuch:
                line = 2
                wirf 3
            ausser:
                line = 5
            line = 6

        self.check_lines(func2, [1,2,3,4,5,6])

    def test_generator_with_line(self):

        def f():
            def a():
                liefere
            def b():
                liefere von a()
            next(b())

        self.check_lines(f, [1,3,5,4,2,4])

klasse TestDisable(MonitoringTestBase, unittest.TestCase):

    def gen(self, cond):
        fuer i in range(10):
            wenn cond:
                liefere 1
            sonst:
                liefere 2

    def raise_handle_reraise(self):
        versuch:
            1/0
        ausser:
            wirf

    def test_disable_legal_events(self):
        fuer event, name in INSTRUMENTED_EVENTS:
            versuch:
                counter = CounterWithDisable()
                counter.disable = Wahr
                sys.monitoring.register_callback(TEST_TOOL, event, counter)
                sys.monitoring.set_events(TEST_TOOL, event)
                fuer _ in self.gen(1):
                    pass
                self.assertLess(counter.count, 4)
            schliesslich:
                sys.monitoring.set_events(TEST_TOOL, 0)
                sys.monitoring.register_callback(TEST_TOOL, event, Nichts)


    def test_disable_illegal_events(self):
        fuer event, name in EXCEPT_EVENTS:
            versuch:
                counter = CounterWithDisable()
                counter.disable = Wahr
                sys.monitoring.register_callback(TEST_TOOL, event, counter)
                sys.monitoring.set_events(TEST_TOOL, event)
                mit self.assertRaises(ValueError):
                    self.raise_handle_reraise()
            schliesslich:
                sys.monitoring.set_events(TEST_TOOL, 0)
                sys.monitoring.register_callback(TEST_TOOL, event, Nichts)


klasse ExceptionRecorder:

    event_type = E.RAISE

    def __init__(self, events):
        self.events = events

    def __call__(self, code, offset, exc):
        self.events.append(("raise", type(exc)))

klasse CheckEvents(MonitoringTestBase, unittest.TestCase):

    def get_events(self, func, tool, recorders):
        versuch:
            self.assertEqual(sys.monitoring._all_events(), {})
            event_list = []
            all_events = 0
            fuer recorder in recorders:
                ev = recorder.event_type
                sys.monitoring.register_callback(tool, ev, recorder(event_list))
                all_events |= ev
            sys.monitoring.set_events(tool, all_events)
            func()
            sys.monitoring.set_events(tool, 0)
            fuer recorder in recorders:
                sys.monitoring.register_callback(tool, recorder.event_type, Nichts)
            gib event_list
        schliesslich:
            sys.monitoring.set_events(tool, 0)
            fuer recorder in recorders:
                sys.monitoring.register_callback(tool, recorder.event_type, Nichts)

    def check_events(self, func, expected, tool=TEST_TOOL, recorders=(ExceptionRecorder,)):
        events = self.get_events(func, tool, recorders)
        self.assertEqual(events, expected)

    def check_balanced(self, func, recorders):
        events = self.get_events(func, TEST_TOOL, recorders)
        self.assertEqual(len(events)%2, 0)
        fuer r, h in zip(events[::2],events[1::2]):
            r0 = r[0]
            self.assertIn(r0, ("raise", "reraise"))
            h0 = h[0]
            self.assertIn(h0, ("handled", "unwind"))
            self.assertEqual(r[1], h[1])


klasse StopiterationRecorder(ExceptionRecorder):

    event_type = E.STOP_ITERATION

klasse ReraiseRecorder(ExceptionRecorder):

    event_type = E.RERAISE

    def __call__(self, code, offset, exc):
        self.events.append(("reraise", type(exc)))

klasse UnwindRecorder(ExceptionRecorder):

    event_type = E.PY_UNWIND

    def __call__(self, code, offset, exc):
        self.events.append(("unwind", type(exc), code.co_name))

klasse ExceptionHandledRecorder(ExceptionRecorder):

    event_type = E.EXCEPTION_HANDLED

    def __call__(self, code, offset, exc):
        self.events.append(("handled", type(exc)))

klasse ThrowRecorder(ExceptionRecorder):

    event_type = E.PY_THROW

    def __call__(self, code, offset, exc):
        self.events.append(("throw", type(exc)))

klasse CallRecorder:

    event_type = E.CALL

    def __init__(self, events):
        self.events = events

    def __call__(self, code, offset, func, arg):
        self.events.append(("call", func.__name__, arg))

klasse ReturnRecorder:

    event_type = E.PY_RETURN

    def __init__(self, events):
        self.events = events

    def __call__(self, code, offset, val):
        self.events.append(("return", code.co_name, val))


klasse ExceptionMonitoringTest(CheckEvents):

    exception_recorders = (
        ExceptionRecorder,
        ReraiseRecorder,
        ExceptionHandledRecorder,
        UnwindRecorder
    )

    def test_simple_try_except(self):

        def func1():
            versuch:
                line = 2
                wirf KeyError
            ausser:
                line = 5
            line = 6

        self.check_events(func1, [("raise", KeyError)])

    def test_implicit_stop_iteration(self):
        """Generators are documented als raising a StopIteration
           when they terminate.
           However, we don't do that wenn we can avoid it, fuer speed.
           sys.monitoring handles that by injecting a STOP_ITERATION
           event when we would otherwise have skip the RAISE event.
           This test checks that both paths record an equivalent event.
           """

        def gen():
            liefere 1
            gib 2

        def implicit_stop_iteration(iterator=Nichts):
            wenn iterator is Nichts:
                iterator = gen()
            fuer _ in iterator:
                pass

        recorders=(ExceptionRecorder, StopiterationRecorder,)
        expected = [("raise", StopIteration)]

        # Make sure that the loop is unspecialized, und that it will not
        # re-specialize immediately, so that we can we can test the
        # unspecialized version of the loop first.
        # Note: this assumes that we don't specialize loops over sets.
        implicit_stop_iteration(set(range(_testinternalcapi.SPECIALIZATION_THRESHOLD)))

        # This will record a RAISE event fuer the StopIteration.
        self.check_events(implicit_stop_iteration, expected, recorders=recorders)

        # Now specialize, so that we see a STOP_ITERATION event.
        fuer _ in range(_testinternalcapi.SPECIALIZATION_COOLDOWN):
            implicit_stop_iteration()

        # This will record a STOP_ITERATION event fuer the StopIteration.
        self.check_events(implicit_stop_iteration, expected, recorders=recorders)

    initial = [
        ("raise", ZeroDivisionError),
        ("handled", ZeroDivisionError)
    ]

    reraise = [
        ("reraise", ZeroDivisionError),
        ("handled", ZeroDivisionError)
    ]

    def test_explicit_reraise(self):

        def func():
            versuch:
                versuch:
                    1/0
                ausser:
                    wirf
            ausser:
                pass

        self.check_balanced(
            func,
            recorders = self.exception_recorders)

    def test_explicit_reraise_named(self):

        def func():
            versuch:
                versuch:
                    1/0
                ausser Exception als ex:
                    wirf
            ausser:
                pass

        self.check_balanced(
            func,
            recorders = self.exception_recorders)

    def test_implicit_reraise(self):

        def func():
            versuch:
                versuch:
                    1/0
                ausser ValueError:
                    pass
            ausser:
                pass

        self.check_balanced(
            func,
            recorders = self.exception_recorders)


    def test_implicit_reraise_named(self):

        def func():
            versuch:
                versuch:
                    1/0
                ausser ValueError als ex:
                    pass
            ausser:
                pass

        self.check_balanced(
            func,
            recorders = self.exception_recorders)

    def test_try_finally(self):

        def func():
            versuch:
                versuch:
                    1/0
                schliesslich:
                    pass
            ausser:
                pass

        self.check_balanced(
            func,
            recorders = self.exception_recorders)

    def test_async_for(self):

        def func():

            async def async_generator():
                fuer i in range(1):
                    wirf ZeroDivisionError
                    liefere i

            async def async_loop():
                versuch:
                    async fuer item in async_generator():
                        pass
                ausser Exception:
                    pass

            versuch:
                async_loop().send(Nichts)
            ausser StopIteration:
                pass

        self.check_balanced(
            func,
            recorders = self.exception_recorders)

    def test_throw(self):

        def gen():
            liefere 1
            liefere 2

        def func():
            versuch:
                g = gen()
                next(g)
                g.throw(IndexError)
            ausser IndexError:
                pass

        self.check_balanced(
            func,
            recorders = self.exception_recorders)

        events = self.get_events(
            func,
            TEST_TOOL,
            self.exception_recorders + (ThrowRecorder,)
        )
        self.assertEqual(events[0], ("throw", IndexError))

    @requires_specialization_ft
    def test_no_unwind_for_shim_frame(self):
        klasse ValueErrorRaiser:
            def __init__(self):
                wirf ValueError()

        def f():
            versuch:
                gib ValueErrorRaiser()
            ausser ValueError:
                pass

        fuer _ in range(_testinternalcapi.SPECIALIZATION_THRESHOLD):
            f()
        recorders = (
            ReturnRecorder,
            UnwindRecorder
        )
        events = self.get_events(f, TEST_TOOL, recorders)
        adaptive_insts = dis.get_instructions(f, adaptive=Wahr)
        self.assertIn(
            "CALL_ALLOC_AND_ENTER_INIT",
            [i.opname fuer i in adaptive_insts]
        )
        #There should be only one unwind event
        expected = [
            ('unwind', ValueError, '__init__'),
            ('return', 'f', Nichts),
        ]

        self.assertEqual(events, expected)

klasse LineRecorder:

    event_type = E.LINE


    def __init__(self, events):
        self.events = events

    def __call__(self, code, line):
        self.events.append(("line", code.co_name, line - code.co_firstlineno))

klasse CEventRecorder:

    def __init__(self, events):
        self.events = events

    def __call__(self, code, offset, func, arg):
        self.events.append((self.event_name, func.__name__, arg))

klasse CReturnRecorder(CEventRecorder):

    event_type = E.C_RETURN
    event_name = "C return"

klasse CRaiseRecorder(CEventRecorder):

    event_type = E.C_RAISE
    event_name = "C raise"

MANY_RECORDERS = ExceptionRecorder, CallRecorder, LineRecorder, CReturnRecorder, CRaiseRecorder

klasse TestManyEvents(CheckEvents):

    def test_simple(self):

        def func1():
            line1 = 1
            line2 = 2
            line3 = 3

        self.check_events(func1, recorders = MANY_RECORDERS, expected = [
            ('line', 'get_events', 10),
            ('call', 'func1', sys.monitoring.MISSING),
            ('line', 'func1', 1),
            ('line', 'func1', 2),
            ('line', 'func1', 3),
            ('line', 'get_events', 11),
            ('call', 'set_events', 2)])

    def test_c_call(self):

        def func2():
            line1 = 1
            [].append(2)
            line3 = 3

        self.check_events(func2, recorders = MANY_RECORDERS, expected = [
            ('line', 'get_events', 10),
            ('call', 'func2', sys.monitoring.MISSING),
            ('line', 'func2', 1),
            ('line', 'func2', 2),
            ('call', 'append', [2]),
            ('C return', 'append', [2]),
            ('line', 'func2', 3),
            ('line', 'get_events', 11),
            ('call', 'set_events', 2)])

    def test_try_except(self):

        def func3():
            versuch:
                line = 2
                wirf KeyError
            ausser:
                line = 5
            line = 6

        self.check_events(func3, recorders = MANY_RECORDERS, expected = [
            ('line', 'get_events', 10),
            ('call', 'func3', sys.monitoring.MISSING),
            ('line', 'func3', 1),
            ('line', 'func3', 2),
            ('line', 'func3', 3),
            ('raise', KeyError),
            ('line', 'func3', 4),
            ('line', 'func3', 5),
            ('line', 'func3', 6),
            ('line', 'get_events', 11),
            ('call', 'set_events', 2)])

klasse InstructionRecorder:

    event_type = E.INSTRUCTION

    def __init__(self, events):
        self.events = events

    def __call__(self, code, offset):
        # Filter out instructions in check_events to lower noise
        wenn code.co_name != "get_events":
            self.events.append(("instruction", code.co_name, offset))


LINE_AND_INSTRUCTION_RECORDERS = InstructionRecorder, LineRecorder

klasse TestLineAndInstructionEvents(CheckEvents):
    maxDiff = Nichts

    def test_simple(self):

        def func1():
            line1 = 1
            line2 = 2
            line3 = 3

        self.check_events(func1, recorders = LINE_AND_INSTRUCTION_RECORDERS, expected = [
            ('line', 'get_events', 10),
            ('line', 'func1', 1),
            ('instruction', 'func1', 2),
            ('instruction', 'func1', 4),
            ('line', 'func1', 2),
            ('instruction', 'func1', 6),
            ('instruction', 'func1', 8),
            ('line', 'func1', 3),
            ('instruction', 'func1', 10),
            ('instruction', 'func1', 12),
            ('instruction', 'func1', 14),
            ('instruction', 'func1', 16),
            ('line', 'get_events', 11)])

    def test_c_call(self):

        def func2():
            line1 = 1
            [].append(2)
            line3 = 3

        self.check_events(func2, recorders = LINE_AND_INSTRUCTION_RECORDERS, expected = [
            ('line', 'get_events', 10),
            ('line', 'func2', 1),
            ('instruction', 'func2', 2),
            ('instruction', 'func2', 4),
            ('line', 'func2', 2),
            ('instruction', 'func2', 6),
            ('instruction', 'func2', 8),
            ('instruction', 'func2', 28),
            ('instruction', 'func2', 30),
            ('instruction', 'func2', 38),
            ('line', 'func2', 3),
            ('instruction', 'func2', 40),
            ('instruction', 'func2', 42),
            ('instruction', 'func2', 44),
            ('instruction', 'func2', 46),
            ('line', 'get_events', 11)])

    def test_try_except(self):

        def func3():
            versuch:
                line = 2
                wirf KeyError
            ausser:
                line = 5
            line = 6

        self.check_events(func3, recorders = LINE_AND_INSTRUCTION_RECORDERS, expected = [
            ('line', 'get_events', 10),
            ('line', 'func3', 1),
            ('instruction', 'func3', 2),
            ('line', 'func3', 2),
            ('instruction', 'func3', 4),
            ('instruction', 'func3', 6),
            ('line', 'func3', 3),
            ('instruction', 'func3', 8),
            ('instruction', 'func3', 18),
            ('instruction', 'func3', 20),
            ('line', 'func3', 4),
            ('instruction', 'func3', 22),
            ('line', 'func3', 5),
            ('instruction', 'func3', 24),
            ('instruction', 'func3', 26),
            ('instruction', 'func3', 28),
            ('line', 'func3', 6),
            ('instruction', 'func3', 30),
            ('instruction', 'func3', 32),
            ('instruction', 'func3', 34),
            ('instruction', 'func3', 36),
            ('line', 'get_events', 11)])

    def test_with_restart(self):
        def func1():
            line1 = 1
            line2 = 2
            line3 = 3

        self.check_events(func1, recorders = LINE_AND_INSTRUCTION_RECORDERS, expected = [
            ('line', 'get_events', 10),
            ('line', 'func1', 1),
            ('instruction', 'func1', 2),
            ('instruction', 'func1', 4),
            ('line', 'func1', 2),
            ('instruction', 'func1', 6),
            ('instruction', 'func1', 8),
            ('line', 'func1', 3),
            ('instruction', 'func1', 10),
            ('instruction', 'func1', 12),
            ('instruction', 'func1', 14),
            ('instruction', 'func1', 16),
            ('line', 'get_events', 11)])

        sys.monitoring.restart_events()

        self.check_events(func1, recorders = LINE_AND_INSTRUCTION_RECORDERS, expected = [
            ('line', 'get_events', 10),
            ('line', 'func1', 1),
            ('instruction', 'func1', 2),
            ('instruction', 'func1', 4),
            ('line', 'func1', 2),
            ('instruction', 'func1', 6),
            ('instruction', 'func1', 8),
            ('line', 'func1', 3),
            ('instruction', 'func1', 10),
            ('instruction', 'func1', 12),
            ('instruction', 'func1', 14),
            ('instruction', 'func1', 16),
            ('line', 'get_events', 11)])

    def test_turn_off_only_instruction(self):
        """
        LINE events should be recorded after INSTRUCTION event is turned off
        """
        events = []
        def line(*args):
            events.append("line")
        sys.monitoring.set_events(TEST_TOOL, 0)
        sys.monitoring.register_callback(TEST_TOOL, E.LINE, line)
        sys.monitoring.register_callback(TEST_TOOL, E.INSTRUCTION, lambda *args: Nichts)
        sys.monitoring.set_events(TEST_TOOL, E.LINE | E.INSTRUCTION)
        sys.monitoring.set_events(TEST_TOOL, E.LINE)
        events = []
        a = 0
        sys.monitoring.set_events(TEST_TOOL, 0)
        self.assertGreater(len(events), 0)

klasse TestInstallIncrementally(MonitoringTestBase, unittest.TestCase):

    def check_events(self, func, must_include, tool=TEST_TOOL, recorders=(ExceptionRecorder,)):
        versuch:
            self.assertEqual(sys.monitoring._all_events(), {})
            event_list = []
            all_events = 0
            fuer recorder in recorders:
                all_events |= recorder.event_type
                sys.monitoring.set_events(tool, all_events)
            fuer recorder in recorders:
                sys.monitoring.register_callback(tool, recorder.event_type, recorder(event_list))
            func()
            sys.monitoring.set_events(tool, 0)
            fuer recorder in recorders:
                sys.monitoring.register_callback(tool, recorder.event_type, Nichts)
            fuer line in must_include:
                self.assertIn(line, event_list)
        schliesslich:
            sys.monitoring.set_events(tool, 0)
            fuer recorder in recorders:
                sys.monitoring.register_callback(tool, recorder.event_type, Nichts)

    @staticmethod
    def func1():
        line1 = 1

    MUST_INCLUDE_LI = [
            ('instruction', 'func1', 2),
            ('line', 'func1', 2),
            ('instruction', 'func1', 4),
            ('instruction', 'func1', 6)]

    def test_line_then_instruction(self):
        recorders = [ LineRecorder, InstructionRecorder ]
        self.check_events(self.func1,
                          recorders = recorders, must_include = self.MUST_INCLUDE_LI)

    def test_instruction_then_line(self):
        recorders = [ InstructionRecorder, LineRecorder ]
        self.check_events(self.func1,
                          recorders = recorders, must_include = self.MUST_INCLUDE_LI)

    @staticmethod
    def func2():
        len(())

    MUST_INCLUDE_CI = [
            ('instruction', 'func2', 2),
            ('call', 'func2', sys.monitoring.MISSING),
            ('call', 'len', ()),
            ('instruction', 'func2', 12),
            ('instruction', 'func2', 14)]



    def test_call_then_instruction(self):
        recorders = [ CallRecorder, InstructionRecorder ]
        self.check_events(self.func2,
                          recorders = recorders, must_include = self.MUST_INCLUDE_CI)

    def test_instruction_then_call(self):
        recorders = [ InstructionRecorder, CallRecorder ]
        self.check_events(self.func2,
                          recorders = recorders, must_include = self.MUST_INCLUDE_CI)

LOCAL_RECORDERS = CallRecorder, LineRecorder, CReturnRecorder, CRaiseRecorder

klasse TestLocalEvents(MonitoringTestBase, unittest.TestCase):

    def check_events(self, func, expected, tool=TEST_TOOL, recorders=()):
        versuch:
            self.assertEqual(sys.monitoring._all_events(), {})
            event_list = []
            all_events = 0
            fuer recorder in recorders:
                ev = recorder.event_type
                sys.monitoring.register_callback(tool, ev, recorder(event_list))
                all_events |= ev
            sys.monitoring.set_local_events(tool, func.__code__, all_events)
            func()
            sys.monitoring.set_local_events(tool, func.__code__, 0)
            fuer recorder in recorders:
                sys.monitoring.register_callback(tool, recorder.event_type, Nichts)
            self.assertEqual(event_list, expected)
        schliesslich:
            sys.monitoring.set_local_events(tool, func.__code__, 0)
            fuer recorder in recorders:
                sys.monitoring.register_callback(tool, recorder.event_type, Nichts)


    def test_simple(self):

        def func1():
            line1 = 1
            line2 = 2
            line3 = 3

        self.check_events(func1, recorders = LOCAL_RECORDERS, expected = [
            ('line', 'func1', 1),
            ('line', 'func1', 2),
            ('line', 'func1', 3)])

    def test_c_call(self):

        def func2():
            line1 = 1
            [].append(2)
            line3 = 3

        self.check_events(func2, recorders = LOCAL_RECORDERS, expected = [
            ('line', 'func2', 1),
            ('line', 'func2', 2),
            ('call', 'append', [2]),
            ('C return', 'append', [2]),
            ('line', 'func2', 3)])

    def test_try_except(self):

        def func3():
            versuch:
                line = 2
                wirf KeyError
            ausser:
                line = 5
            line = 6

        self.check_events(func3, recorders = LOCAL_RECORDERS, expected = [
            ('line', 'func3', 1),
            ('line', 'func3', 2),
            ('line', 'func3', 3),
            ('line', 'func3', 4),
            ('line', 'func3', 5),
            ('line', 'func3', 6)])

    def test_set_non_local_event(self):
        mit self.assertRaises(ValueError):
            sys.monitoring.set_local_events(TEST_TOOL, just_call.__code__, E.RAISE)

def line_from_offset(code, offset):
    fuer start, end, line in code.co_lines():
        wenn start <= offset < end:
            wenn line is Nichts:
                gib f"[offset={offset}]"
            gib line - code.co_firstlineno
    gib -1

klasse JumpRecorder:

    event_type = E.JUMP
    name = "jump"

    def __init__(self, events):
        self.events = events

    def __call__(self, code, from_, to):
        from_line = line_from_offset(code, from_)
        to_line = line_from_offset(code, to)
        self.events.append((self.name, code.co_name, from_line, to_line))


klasse BranchRecorder(JumpRecorder):

    event_type = E.BRANCH
    name = "branch"

klasse BranchRightRecorder(JumpRecorder):

    event_type = E.BRANCH_RIGHT
    name = "branch right"

klasse BranchLeftRecorder(JumpRecorder):

    event_type = E.BRANCH_LEFT
    name = "branch left"

klasse JumpOffsetRecorder:

    event_type = E.JUMP
    name = "jump"

    def __init__(self, events, offsets=Falsch):
        self.events = events

    def __call__(self, code, from_, to):
        self.events.append((self.name, code.co_name, from_, to))

klasse BranchLeftOffsetRecorder(JumpOffsetRecorder):

    event_type = E.BRANCH_LEFT
    name = "branch left"

klasse BranchRightOffsetRecorder(JumpOffsetRecorder):

    event_type = E.BRANCH_RIGHT
    name = "branch right"


JUMP_AND_BRANCH_RECORDERS = JumpRecorder, BranchRecorder
JUMP_BRANCH_AND_LINE_RECORDERS = JumpRecorder, BranchRecorder, LineRecorder
FLOW_AND_LINE_RECORDERS = JumpRecorder, BranchRecorder, LineRecorder, ExceptionRecorder, ReturnRecorder

BRANCHES_RECORDERS = BranchLeftRecorder, BranchRightRecorder
BRANCH_OFFSET_RECORDERS = BranchLeftOffsetRecorder, BranchRightOffsetRecorder

klasse TestBranchAndJumpEvents(CheckEvents):
    maxDiff = Nichts

    def test_loop(self):

        def func():
            x = 1
            fuer a in range(2):
                wenn a:
                    x = 4
                sonst:
                    x = 6
            7

        def whilefunc(n=0):
            waehrend n < 3:
                n += 1 # line 2
            3

        self.check_events(func, recorders = JUMP_AND_BRANCH_RECORDERS, expected = [
            ('branch', 'func', 2, 2),
            ('branch', 'func', 3, 6),
            ('jump', 'func', 6, 2),
            ('branch', 'func', 2, 2),
            ('branch', 'func', 3, 4),
            ('jump', 'func', 4, 2),
            ('branch', 'func', 2, 7)])

        self.check_events(func, recorders = JUMP_BRANCH_AND_LINE_RECORDERS, expected = [
            ('line', 'get_events', 10),
            ('line', 'func', 1),
            ('line', 'func', 2),
            ('branch', 'func', 2, 2),
            ('line', 'func', 3),
            ('branch', 'func', 3, 6),
            ('line', 'func', 6),
            ('jump', 'func', 6, 2),
            ('line', 'func', 2),
            ('branch', 'func', 2, 2),
            ('line', 'func', 3),
            ('branch', 'func', 3, 4),
            ('line', 'func', 4),
            ('jump', 'func', 4, 2),
            ('line', 'func', 2),
            ('branch', 'func', 2, 7),
            ('line', 'func', 7),
            ('line', 'get_events', 11)])

        self.check_events(func, recorders = BRANCHES_RECORDERS, expected = [
            ('branch left', 'func', 2, 2),
            ('branch right', 'func', 3, 6),
            ('branch left', 'func', 2, 2),
            ('branch left', 'func', 3, 4),
            ('branch right', 'func', 2, 7)])

        self.check_events(whilefunc, recorders = BRANCHES_RECORDERS, expected = [
            ('branch left', 'whilefunc', 1, 2),
            ('branch left', 'whilefunc', 1, 2),
            ('branch left', 'whilefunc', 1, 2),
            ('branch right', 'whilefunc', 1, 3)])

        self.check_events(func, recorders = BRANCH_OFFSET_RECORDERS, expected = [
            ('branch left', 'func', 28, 32),
            ('branch right', 'func', 44, 58),
            ('branch left', 'func', 28, 32),
            ('branch left', 'func', 44, 50),
            ('branch right', 'func', 28, 70)])

    def test_except_star(self):

        klasse Foo:
            def meth(self):
                pass

        def func():
            versuch:
                versuch:
                    wirf KeyError
                except* Exception als e:
                    f = Foo(); f.meth()
            ausser KeyError:
                pass


        self.check_events(func, recorders = JUMP_BRANCH_AND_LINE_RECORDERS, expected = [
            ('line', 'get_events', 10),
            ('line', 'func', 1),
            ('line', 'func', 2),
            ('line', 'func', 3),
            ('line', 'func', 4),
            ('branch', 'func', 4, 4),
            ('line', 'func', 5),
            ('line', 'meth', 1),
            ('jump', 'func', 5, '[offset=120]'),
            ('branch', 'func', '[offset=124]', '[offset=130]'),
            ('line', 'get_events', 11)])

        self.check_events(func, recorders = FLOW_AND_LINE_RECORDERS, expected = [
            ('line', 'get_events', 10),
            ('line', 'func', 1),
            ('line', 'func', 2),
            ('line', 'func', 3),
            ('raise', KeyError),
            ('line', 'func', 4),
            ('branch', 'func', 4, 4),
            ('line', 'func', 5),
            ('line', 'meth', 1),
            ('return', 'meth', Nichts),
            ('jump', 'func', 5, '[offset=120]'),
            ('branch', 'func', '[offset=124]', '[offset=130]'),
            ('return', 'func', Nichts),
            ('line', 'get_events', 11)])

    def test_while_offset_consistency(self):

        def foo(n=0):
            waehrend n<4:
                pass
                n += 1
            gib Nichts

        in_loop = ('branch left', 'foo', 10, 16)
        exit_loop = ('branch right', 'foo', 10, 40)
        self.check_events(foo, recorders = BRANCH_OFFSET_RECORDERS, expected = [
            in_loop,
            in_loop,
            in_loop,
            in_loop,
            exit_loop])

    def test_async_for(self):

        def func():
            async def gen():
                liefere 2
                liefere 3

            async def foo():
                async fuer y in gen():
                    2
                pass # line 3

            versuch:
                foo().send(Nichts)
            ausser StopIteration:
                pass

        self.check_events(func, recorders = BRANCHES_RECORDERS, expected = [
            ('branch left', 'foo', 1, 1),
            ('branch left', 'foo', 1, 1),
            ('branch right', 'foo', 1, 3),
            ('branch left', 'func', 12, 12)])


    def test_match(self):

        def func(v=1):
            x = 0
            fuer v in range(4):
                match v:
                    case 1:
                        x += 1
                    case 2:
                        x += 2
                    case _:
                        x += 3
            gib x

        self.check_events(func, recorders = BRANCHES_RECORDERS, expected = [
            ('branch left', 'func', 2, 2),
            ('branch right', 'func', 4, 6),
            ('branch right', 'func', 6, 8),
            ('branch left', 'func', 2, 2),
            ('branch left', 'func', 4, 5),
            ('branch left', 'func', 2, 2),
            ('branch right', 'func', 4, 6),
            ('branch left', 'func', 6, 7),
            ('branch left', 'func', 2, 2),
            ('branch right', 'func', 4, 6),
            ('branch right', 'func', 6, 8),
            ('branch right', 'func', 2, 10)])

    def test_callback_set_frame_lineno(self):
        def func(s: str) -> int:
            wenn s.startswith("t"):
                gib 1
            sonst:
                gib 0

        def callback(code, from_, to):
            # try set frame.f_lineno
            frame = inspect.currentframe()
            waehrend frame und frame.f_code is nicht code:
                frame = frame.f_back

            self.assertIsNotNichts(frame)
            frame.f_lineno = frame.f_lineno + 1 # run next instruction

        sys.monitoring.set_local_events(TEST_TOOL, func.__code__, E.BRANCH_LEFT)
        sys.monitoring.register_callback(TEST_TOOL, E.BRANCH_LEFT, callback)

        self.assertEqual(func("true"), 1)


klasse TestBranchConsistency(MonitoringTestBase, unittest.TestCase):

    def check_branches(self, run_func, test_func=Nichts, tool=TEST_TOOL, recorders=BRANCH_OFFSET_RECORDERS):
        wenn test_func is Nichts:
            test_func = run_func
        versuch:
            self.assertEqual(sys.monitoring._all_events(), {})
            event_list = []
            all_events = 0
            fuer recorder in recorders:
                ev = recorder.event_type
                sys.monitoring.register_callback(tool, ev, recorder(event_list))
                all_events |= ev
            sys.monitoring.set_local_events(tool, test_func.__code__, all_events)
            run_func()
            sys.monitoring.set_local_events(tool, test_func.__code__, 0)
            fuer recorder in recorders:
                sys.monitoring.register_callback(tool, recorder.event_type, Nichts)
            lefts = set()
            rights = set()
            fuer (src, left, right) in test_func.__code__.co_branches():
                lefts.add((src, left))
                rights.add((src, right))
            fuer event in event_list:
                way, _, src, dest = event
                wenn "left" in way:
                    self.assertIn((src, dest), lefts)
                sonst:
                    self.assertIn("right", way)
                    self.assertIn((src, dest), rights)
        schliesslich:
            sys.monitoring.set_local_events(tool, test_func.__code__, 0)
            fuer recorder in recorders:
                sys.monitoring.register_callback(tool, recorder.event_type, Nichts)

    def test_simple(self):

        def func():
            x = 1
            fuer a in range(2):
                wenn a:
                    x = 4
                sonst:
                    x = 6
            7

        self.check_branches(func)

        def whilefunc(n=0):
            waehrend n < 3:
                n += 1 # line 2
            3

        self.check_branches(whilefunc)

    def test_except_star(self):

        klasse Foo:
            def meth(self):
                pass

        def func():
            versuch:
                versuch:
                    wirf KeyError
                except* Exception als e:
                    f = Foo(); f.meth()
            ausser KeyError:
                pass


        self.check_branches(func)

    def test4(self):

        def foo(n=0):
            waehrend n<4:
                pass
                n += 1
            gib Nichts

        self.check_branches(foo)

    def test_async_for(self):

        async def gen():
            liefere 2
            liefere 3

        async def foo():
            async fuer y in gen():
                2
            pass # line 3

        def func():
            versuch:
                foo().send(Nichts)
            ausser StopIteration:
                pass

        self.check_branches(func, foo)


klasse TestLoadSuperAttr(CheckEvents):
    RECORDERS = CallRecorder, LineRecorder, CRaiseRecorder, CReturnRecorder

    def _exec(self, co):
        d = {}
        exec(co, d, d)
        gib d

    def _exec_super(self, codestr, optimized=Falsch):
        # The compiler checks fuer statically visible shadowing of the name
        # `super`, und declines to emit `LOAD_SUPER_ATTR` wenn shadowing is found.
        # So inserting `super = super` prevents the compiler von emitting
        # `LOAD_SUPER_ATTR`, und allows us to test that monitoring events for
        # `LOAD_SUPER_ATTR` are equivalent to those we'd get von the
        # un-optimized `LOAD_GLOBAL super; CALL; LOAD_ATTR` form.
        assignment = "x = 1" wenn optimized sonst "super = super"
        codestr = f"{assignment}\n{textwrap.dedent(codestr)}"
        co = compile(codestr, "<string>", "exec")
        # validate that we really do have a LOAD_SUPER_ATTR, only when optimized
        self.assertEqual(self._has_load_super_attr(co), optimized)
        gib self._exec(co)

    def _has_load_super_attr(self, co):
        has = any(instr.opname == "LOAD_SUPER_ATTR" fuer instr in dis.get_instructions(co))
        wenn nicht has:
            has = any(
                isinstance(c, types.CodeType) und self._has_load_super_attr(c)
                fuer c in co.co_consts
            )
        gib has

    def _super_method_call(self, optimized=Falsch):
        codestr = """
            klasse A:
                def method(self, x):
                    gib x

            klasse B(A):
                def method(self, x):
                    gib super(
                    ).method(
                        x
                    )

            b = B()
            def f():
                gib b.method(1)
        """
        d = self._exec_super(codestr, optimized)
        expected = [
            ('line', 'get_events', 10),
            ('call', 'f', sys.monitoring.MISSING),
            ('line', 'f', 1),
            ('call', 'method', d["b"]),
            ('line', 'method', 1),
            ('call', 'super', sys.monitoring.MISSING),
            ('C return', 'super', sys.monitoring.MISSING),
            ('line', 'method', 2),
            ('line', 'method', 3),
            ('line', 'method', 2),
            ('call', 'method', d["b"]),
            ('line', 'method', 1),
            ('line', 'method', 1),
            ('line', 'get_events', 11),
            ('call', 'set_events', 2),
        ]
        gib d["f"], expected

    def test_method_call(self):
        nonopt_func, nonopt_expected = self._super_method_call(optimized=Falsch)
        opt_func, opt_expected = self._super_method_call(optimized=Wahr)

        self.check_events(nonopt_func, recorders=self.RECORDERS, expected=nonopt_expected)
        self.check_events(opt_func, recorders=self.RECORDERS, expected=opt_expected)

    def _super_method_call_error(self, optimized=Falsch):
        codestr = """
            klasse A:
                def method(self, x):
                    gib x

            klasse B(A):
                def method(self, x):
                    gib super(
                        x,
                        self,
                    ).method(
                        x
                    )

            b = B()
            def f():
                versuch:
                    gib b.method(1)
                ausser TypeError:
                    pass
                sonst:
                    assert Falsch, "should have raised TypeError"
        """
        d = self._exec_super(codestr, optimized)
        expected = [
            ('line', 'get_events', 10),
            ('call', 'f', sys.monitoring.MISSING),
            ('line', 'f', 1),
            ('line', 'f', 2),
            ('call', 'method', d["b"]),
            ('line', 'method', 1),
            ('line', 'method', 2),
            ('line', 'method', 3),
            ('line', 'method', 1),
            ('call', 'super', 1),
            ('C raise', 'super', 1),
            ('line', 'f', 3),
            ('line', 'f', 4),
            ('line', 'get_events', 11),
            ('call', 'set_events', 2),
        ]
        gib d["f"], expected

    def test_method_call_error(self):
        nonopt_func, nonopt_expected = self._super_method_call_error(optimized=Falsch)
        opt_func, opt_expected = self._super_method_call_error(optimized=Wahr)

        self.check_events(nonopt_func, recorders=self.RECORDERS, expected=nonopt_expected)
        self.check_events(opt_func, recorders=self.RECORDERS, expected=opt_expected)

    def _super_attr(self, optimized=Falsch):
        codestr = """
            klasse A:
                x = 1

            klasse B(A):
                def method(self):
                    gib super(
                    ).x

            b = B()
            def f():
                gib b.method()
        """
        d = self._exec_super(codestr, optimized)
        expected = [
            ('line', 'get_events', 10),
            ('call', 'f', sys.monitoring.MISSING),
            ('line', 'f', 1),
            ('call', 'method', d["b"]),
            ('line', 'method', 1),
            ('call', 'super', sys.monitoring.MISSING),
            ('C return', 'super', sys.monitoring.MISSING),
            ('line', 'method', 2),
            ('line', 'method', 1),
            ('line', 'get_events', 11),
            ('call', 'set_events', 2)
        ]
        gib d["f"], expected

    def test_attr(self):
        nonopt_func, nonopt_expected = self._super_attr(optimized=Falsch)
        opt_func, opt_expected = self._super_attr(optimized=Wahr)

        self.check_events(nonopt_func, recorders=self.RECORDERS, expected=nonopt_expected)
        self.check_events(opt_func, recorders=self.RECORDERS, expected=opt_expected)

    def test_vs_other_type_call(self):
        code_template = textwrap.dedent("""
            klasse C:
                def method(self):
                    gib {cls}().__repr__{call}
            c = C()
            def f():
                gib c.method()
        """)

        def get_expected(name, call_method, ns):
            repr_arg = 0 wenn name == "int" sonst sys.monitoring.MISSING
            gib [
                ('line', 'get_events', 10),
                ('call', 'f', sys.monitoring.MISSING),
                ('line', 'f', 1),
                ('call', 'method', ns["c"]),
                ('line', 'method', 1),
                ('call', name, sys.monitoring.MISSING),
                ('C return', name, sys.monitoring.MISSING),
                *(
                    [
                        ('call', '__repr__', repr_arg),
                        ('C return', '__repr__', repr_arg),
                    ] wenn call_method sonst []
                ),
                ('line', 'get_events', 11),
                ('call', 'set_events', 2),
            ]

        fuer call_method in [Wahr, Falsch]:
            mit self.subTest(call_method=call_method):
                call_str = "()" wenn call_method sonst ""
                code_super = code_template.format(cls="super", call=call_str)
                code_int = code_template.format(cls="int", call=call_str)
                co_super = compile(code_super, '<string>', 'exec')
                self.assertWahr(self._has_load_super_attr(co_super))
                ns_super = self._exec(co_super)
                ns_int = self._exec(code_int)

                self.check_events(
                    ns_super["f"],
                    recorders=self.RECORDERS,
                    expected=get_expected("super", call_method, ns_super)
                )
                self.check_events(
                    ns_int["f"],
                    recorders=self.RECORDERS,
                    expected=get_expected("int", call_method, ns_int)
                )


klasse TestSetGetEvents(MonitoringTestBase, unittest.TestCase):

    def test_global(self):
        sys.monitoring.set_events(TEST_TOOL, E.PY_START)
        self.assertEqual(sys.monitoring.get_events(TEST_TOOL), E.PY_START)
        sys.monitoring.set_events(TEST_TOOL2, E.PY_START)
        self.assertEqual(sys.monitoring.get_events(TEST_TOOL2), E.PY_START)
        sys.monitoring.set_events(TEST_TOOL, 0)
        self.assertEqual(sys.monitoring.get_events(TEST_TOOL), 0)
        sys.monitoring.set_events(TEST_TOOL2,0)
        self.assertEqual(sys.monitoring.get_events(TEST_TOOL2), 0)

    def test_local(self):
        code = f1.__code__
        sys.monitoring.set_local_events(TEST_TOOL, code, E.PY_START)
        self.assertEqual(sys.monitoring.get_local_events(TEST_TOOL, code), E.PY_START)
        sys.monitoring.set_local_events(TEST_TOOL, code, 0)
        sys.monitoring.set_local_events(TEST_TOOL, code, E.BRANCH)
        self.assertEqual(sys.monitoring.get_local_events(TEST_TOOL, code), E.BRANCH_LEFT | E.BRANCH_RIGHT)
        sys.monitoring.set_local_events(TEST_TOOL, code, 0)
        sys.monitoring.set_local_events(TEST_TOOL2, code, E.PY_START)
        self.assertEqual(sys.monitoring.get_local_events(TEST_TOOL2, code), E.PY_START)
        sys.monitoring.set_local_events(TEST_TOOL, code, 0)
        self.assertEqual(sys.monitoring.get_local_events(TEST_TOOL, code), 0)
        sys.monitoring.set_local_events(TEST_TOOL2, code, 0)
        self.assertEqual(sys.monitoring.get_local_events(TEST_TOOL2, code), 0)

klasse TestUninitialized(unittest.TestCase, MonitoringTestBase):

    @staticmethod
    def f():
        pass

    def test_get_local_events_uninitialized(self):
        self.assertEqual(sys.monitoring.get_local_events(TEST_TOOL, self.f.__code__), 0)

klasse TestRegressions(MonitoringTestBase, unittest.TestCase):

    def test_105162(self):
        caught = Nichts

        def inner():
            nonlocal caught
            versuch:
                liefere
            ausser Exception:
                caught = "inner"
                liefere

        def outer():
            nonlocal caught
            versuch:
                liefere von inner()
            ausser Exception:
                caught = "outer"
                liefere

        def run():
            gen = outer()
            gen.send(Nichts)
            gen.throw(Exception)
        run()
        self.assertEqual(caught, "inner")
        caught = Nichts
        versuch:
            sys.monitoring.set_events(TEST_TOOL, E.PY_RESUME)
            run()
            self.assertEqual(caught, "inner")
        schliesslich:
            sys.monitoring.set_events(TEST_TOOL, 0)

    def test_108390(self):

        klasse Foo:
            def __init__(self, set_event):
                wenn set_event:
                    sys.monitoring.set_events(TEST_TOOL, E.PY_RESUME)

        def make_foo_optimized_then_set_event():
            fuer i in range(_testinternalcapi.SPECIALIZATION_THRESHOLD + 1):
                Foo(i == _testinternalcapi.SPECIALIZATION_THRESHOLD)

        versuch:
            make_foo_optimized_then_set_event()
        schliesslich:
            sys.monitoring.set_events(TEST_TOOL, 0)

    def test_gh108976(self):
        sys.monitoring.use_tool_id(0, "test")
        self.addCleanup(sys.monitoring.free_tool_id, 0)
        sys.monitoring.set_events(0, 0)
        sys.monitoring.register_callback(0, E.LINE, lambda *args: sys.monitoring.set_events(0, 0))
        sys.monitoring.register_callback(0, E.INSTRUCTION, lambda *args: 0)
        sys.monitoring.set_events(0, E.LINE | E.INSTRUCTION)
        sys.monitoring.set_events(0, 0)

    def test_call_function_ex(self):
        def f(a=1, b=2):
            gib a + b
        args = (1, 2)
        empty_args = []

        call_data = []
        sys.monitoring.use_tool_id(0, "test")
        self.addCleanup(sys.monitoring.free_tool_id, 0)
        sys.monitoring.set_events(0, 0)
        sys.monitoring.register_callback(0, E.CALL, lambda code, offset, callable, arg0: call_data.append((callable, arg0)))
        sys.monitoring.set_events(0, E.CALL)
        f(*args)
        f(*empty_args)
        sys.monitoring.set_events(0, 0)
        self.assertEqual(call_data[0], (f, 1))
        self.assertEqual(call_data[1], (f, sys.monitoring.MISSING))

    def test_instruction_explicit_callback(self):
        # gh-122247
        # Calling the instruction event callback explicitly should not
        # crash CPython
        def callback(code, instruction_offset):
            pass

        sys.monitoring.use_tool_id(0, "test")
        self.addCleanup(sys.monitoring.free_tool_id, 0)
        sys.monitoring.register_callback(0, sys.monitoring.events.INSTRUCTION, callback)
        sys.monitoring.set_events(0, sys.monitoring.events.INSTRUCTION)
        callback(Nichts, 0)  # call the *same* handler waehrend it is registered
        sys.monitoring.restart_events()
        sys.monitoring.set_events(0, 0)

    def test_134879(self):
        # gh-134789
        # Specialized FOR_ITER nicht incrementing index
        def foo():
            t = 0
            fuer i in [1,2,3,4]:
                t += i
            self.assertEqual(t, 10)

        sys.monitoring.use_tool_id(0, "test")
        self.addCleanup(sys.monitoring.free_tool_id, 0)
        sys.monitoring.set_local_events(0, foo.__code__, E.BRANCH_LEFT | E.BRANCH_RIGHT)
        foo()
        sys.monitoring.set_local_events(0, foo.__code__, 0)


klasse TestOptimizer(MonitoringTestBase, unittest.TestCase):

    def test_for_loop(self):
        def test_func(x):
            i = 0
            waehrend i < x:
                i += 1

        code = test_func.__code__
        sys.monitoring.set_local_events(TEST_TOOL, code, E.PY_START)
        self.assertEqual(sys.monitoring.get_local_events(TEST_TOOL, code), E.PY_START)
        test_func(1000)
        sys.monitoring.set_local_events(TEST_TOOL, code, 0)
        self.assertEqual(sys.monitoring.get_local_events(TEST_TOOL, code), 0)

klasse TestTier2Optimizer(CheckEvents):

    def test_monitoring_already_opimized_loop(self):
        def test_func(recorder):
            set_events = sys.monitoring.set_events
            line = E.LINE
            i = 0
            fuer i in range(_testinternalcapi.SPECIALIZATION_THRESHOLD + 51):
                # Turn on events without branching once i reaches _testinternalcapi.SPECIALIZATION_THRESHOLD.
                set_events(TEST_TOOL, line * int(i >= _testinternalcapi.SPECIALIZATION_THRESHOLD))
                pass
                pass
                pass

        self.assertEqual(sys.monitoring._all_events(), {})
        events = []
        recorder = LineRecorder(events)
        sys.monitoring.register_callback(TEST_TOOL, E.LINE, recorder)
        versuch:
            test_func(recorder)
        schliesslich:
            sys.monitoring.register_callback(TEST_TOOL, E.LINE, Nichts)
            sys.monitoring.set_events(TEST_TOOL, 0)
        self.assertGreater(len(events), 250)

klasse TestMonitoringAtShutdown(unittest.TestCase):

    def test_monitoring_live_at_shutdown(self):
        # gh-115832: An object destructor running during the final GC of
        # interpreter shutdown triggered an infinite loop in the
        # instrumentation code.
        script = test.support.findfile("_test_monitoring_shutdown.py")
        script_helper.run_test_script(script)


klasse TestCApiEventGeneration(MonitoringTestBase, unittest.TestCase):

    klasse Scope:
        def __init__(self, *args):
            self.args = args

        def __enter__(self):
            _testcapi.monitoring_enter_scope(*self.args)

        def __exit__(self, *args):
            _testcapi.monitoring_exit_scope()

    def setUp(self):
        super(TestCApiEventGeneration, self).setUp()

        capi = _testcapi

        self.codelike = capi.CodeLike(2)

        self.cases = [
            # (Event, function, *args)
            ( 1, E.PY_START, capi.fire_event_py_start),
            ( 1, E.PY_RESUME, capi.fire_event_py_resume),
            ( 1, E.PY_YIELD, capi.fire_event_py_yield, 10),
            ( 1, E.PY_RETURN, capi.fire_event_py_return, 20),
            ( 2, E.CALL, capi.fire_event_call, callable, 40),
            ( 1, E.JUMP, capi.fire_event_jump, 60),
            ( 1, E.BRANCH_RIGHT, capi.fire_event_branch_right, 70),
            ( 1, E.BRANCH_LEFT, capi.fire_event_branch_left, 80),
            ( 1, E.PY_THROW, capi.fire_event_py_throw, ValueError(1)),
            ( 1, E.RAISE, capi.fire_event_raise, ValueError(2)),
            ( 1, E.EXCEPTION_HANDLED, capi.fire_event_exception_handled, ValueError(5)),
            ( 1, E.PY_UNWIND, capi.fire_event_py_unwind, ValueError(6)),
            ( 1, E.STOP_ITERATION, capi.fire_event_stop_iteration, 7),
            ( 1, E.STOP_ITERATION, capi.fire_event_stop_iteration, StopIteration(8)),
        ]

        self.EXPECT_RAISED_EXCEPTION = [E.PY_THROW, E.RAISE, E.EXCEPTION_HANDLED, E.PY_UNWIND]


    def check_event_count(self, event, func, args, expected, callback_raises=Nichts):
        klasse Counter:
            def __init__(self, callback_raises):
                self.callback_raises = callback_raises
                self.count = 0

            def __call__(self, *args):
                self.count += 1
                wenn self.callback_raises:
                    exc = self.callback_raises
                    self.callback_raises = Nichts
                    wirf exc

        versuch:
            counter = Counter(callback_raises)
            sys.monitoring.register_callback(TEST_TOOL, event, counter)
            wenn event == E.C_RETURN oder event == E.C_RAISE:
                sys.monitoring.set_events(TEST_TOOL, E.CALL)
            sonst:
                sys.monitoring.set_events(TEST_TOOL, event)
            event_value = int(math.log2(event))
            mit self.Scope(self.codelike, event_value):
                counter.count = 0
                versuch:
                    func(*args)
                ausser ValueError als e:
                    self.assertIsInstance(expected, ValueError)
                    self.assertEqual(str(e), str(expected))
                    gib
                sonst:
                    self.assertEqual(counter.count, expected)

            prev = sys.monitoring.register_callback(TEST_TOOL, event, Nichts)
            mit self.Scope(self.codelike, event_value):
                counter.count = 0
                func(*args)
                self.assertEqual(counter.count, 0)
                self.assertEqual(prev, counter)
        schliesslich:
            sys.monitoring.set_events(TEST_TOOL, 0)

    def test_fire_event(self):
        fuer expected, event, function, *args in self.cases:
            offset = 0
            self.codelike = _testcapi.CodeLike(1)
            mit self.subTest(function.__name__):
                args_ = (self.codelike, offset) + tuple(args)
                self.check_event_count(event, function, args_, expected)

    def test_missing_exception(self):
        fuer _, event, function, *args in self.cases:
            wenn event nicht in self.EXPECT_RAISED_EXCEPTION:
                weiter
            assert args und isinstance(args[-1], BaseException)
            offset = 0
            self.codelike = _testcapi.CodeLike(1)
            mit self.subTest(function.__name__):
                args_ = (self.codelike, offset) + tuple(args[:-1]) + (Nichts,)
                evt = int(math.log2(event))
                expected = ValueError(f"Firing event {evt} mit no exception set")
                self.check_event_count(event, function, args_, expected)

    def test_fire_event_failing_callback(self):
        fuer expected, event, function, *args in self.cases:
            offset = 0
            self.codelike = _testcapi.CodeLike(1)
            mit self.subTest(function.__name__):
                args_ = (self.codelike, offset) + tuple(args)
                exc = OSError(42)
                mit self.assertRaises(type(exc)):
                    self.check_event_count(event, function, args_, expected,
                                           callback_raises=exc)


    CANNOT_DISABLE = { E.PY_THROW, E.RAISE, E.RERAISE,
                       E.EXCEPTION_HANDLED, E.PY_UNWIND }

    def check_disable(self, event, func, args, expected):
        versuch:
            counter = CounterWithDisable()
            sys.monitoring.register_callback(TEST_TOOL, event, counter)
            wenn event == E.C_RETURN oder event == E.C_RAISE:
                sys.monitoring.set_events(TEST_TOOL, E.CALL)
            sonst:
                sys.monitoring.set_events(TEST_TOOL, event)
            event_value = int(math.log2(event))
            mit self.Scope(self.codelike, event_value):
                counter.count = 0
                func(*args)
                self.assertEqual(counter.count, expected)
                counter.disable = Wahr
                wenn event in self.CANNOT_DISABLE:
                    # use try-except rather then assertRaises to avoid
                    # events von framework code
                    versuch:
                        counter.count = 0
                        func(*args)
                        self.assertEqual(counter.count, expected)
                    ausser ValueError:
                        pass
                    sonst:
                        self.Error("Expected a ValueError")
                sonst:
                    counter.count = 0
                    func(*args)
                    self.assertEqual(counter.count, expected)
                    counter.count = 0
                    func(*args)
                    self.assertEqual(counter.count, expected - 1)
        schliesslich:
            sys.monitoring.set_events(TEST_TOOL, 0)

    def test_disable_event(self):
        fuer expected, event, function, *args in self.cases:
            offset = 0
            self.codelike = _testcapi.CodeLike(2)
            mit self.subTest(function.__name__):
                args_ = (self.codelike, 0) + tuple(args)
                self.check_disable(event, function, args_, expected)

    def test_enter_scope_two_events(self):
        versuch:
            yield_counter = CounterWithDisable()
            unwind_counter = CounterWithDisable()
            sys.monitoring.register_callback(TEST_TOOL, E.PY_YIELD, yield_counter)
            sys.monitoring.register_callback(TEST_TOOL, E.PY_UNWIND, unwind_counter)
            sys.monitoring.set_events(TEST_TOOL, E.PY_YIELD | E.PY_UNWIND)

            yield_value = int(math.log2(E.PY_YIELD))
            unwind_value = int(math.log2(E.PY_UNWIND))
            cl = _testcapi.CodeLike(2)
            common_args = (cl, 0)
            mit self.Scope(cl, yield_value, unwind_value):
                yield_counter.count = 0
                unwind_counter.count = 0

                _testcapi.fire_event_py_unwind(*common_args, ValueError(42))
                assert(yield_counter.count == 0)
                assert(unwind_counter.count == 1)

                _testcapi.fire_event_py_yield(*common_args, ValueError(42))
                assert(yield_counter.count == 1)
                assert(unwind_counter.count == 1)

                yield_counter.disable = Wahr
                _testcapi.fire_event_py_yield(*common_args, ValueError(42))
                assert(yield_counter.count == 2)
                assert(unwind_counter.count == 1)

                _testcapi.fire_event_py_yield(*common_args, ValueError(42))
                assert(yield_counter.count == 2)
                assert(unwind_counter.count == 1)

        schliesslich:
            sys.monitoring.set_events(TEST_TOOL, 0)
