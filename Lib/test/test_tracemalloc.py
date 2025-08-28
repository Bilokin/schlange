import contextlib
import os
import sys
import textwrap
import tracemalloc
import unittest
from unittest.mock import patch
from test.support.script_helper import (assert_python_ok, assert_python_failure,
                                        interpreter_requires_environment)
from test import support
from test.support import force_not_colorized, warnings_helper
from test.support import os_helper
from test.support import threading_helper

try:
    import _testcapi
    import _testinternalcapi
except ImportError:
    _testcapi = Nichts
    _testinternalcapi = Nichts


DEFAULT_DOMAIN = 0
EMPTY_STRING_SIZE = sys.getsizeof(b'')
INVALID_NFRAME = (-1, 2**30)


def get_frames(nframe, lineno_delta):
    frames = []
    frame = sys._getframe(1)
    fuer index in range(nframe):
        code = frame.f_code
        lineno = frame.f_lineno + lineno_delta
        frames.append((code.co_filename, lineno))
        lineno_delta = 0
        frame = frame.f_back
        wenn frame is Nichts:
            break
    return tuple(frames)

def allocate_bytes(size):
    nframe = tracemalloc.get_traceback_limit()
    bytes_len = (size - EMPTY_STRING_SIZE)
    frames = get_frames(nframe, 1)
    data = b'x' * bytes_len
    return data, tracemalloc.Traceback(frames, min(len(frames), nframe))

def create_snapshots():
    traceback_limit = 2

    # _tracemalloc._get_traces() returns a list of (domain, size,
    # traceback_frames) tuples. traceback_frames is a tuple of (filename,
    # line_number) tuples.
    raw_traces = [
        (0, 10, (('a.py', 2), ('b.py', 4)), 3),
        (0, 10, (('a.py', 2), ('b.py', 4)), 3),
        (0, 10, (('a.py', 2), ('b.py', 4)), 3),

        (1, 2, (('a.py', 5), ('b.py', 4)), 3),

        (2, 66, (('b.py', 1),), 1),

        (3, 7, (('<unknown>', 0),), 1),
    ]
    snapshot = tracemalloc.Snapshot(raw_traces, traceback_limit)

    raw_traces2 = [
        (0, 10, (('a.py', 2), ('b.py', 4)), 3),
        (0, 10, (('a.py', 2), ('b.py', 4)), 3),
        (0, 10, (('a.py', 2), ('b.py', 4)), 3),

        (2, 2, (('a.py', 5), ('b.py', 4)), 3),
        (2, 5000, (('a.py', 5), ('b.py', 4)), 3),

        (4, 400, (('c.py', 578),), 1),
    ]
    snapshot2 = tracemalloc.Snapshot(raw_traces2, traceback_limit)

    return (snapshot, snapshot2)

def frame(filename, lineno):
    return tracemalloc._Frame((filename, lineno))

def traceback(*frames):
    return tracemalloc.Traceback(frames)

def traceback_lineno(filename, lineno):
    return traceback((filename, lineno))

def traceback_filename(filename):
    return traceback_lineno(filename, 0)


klasse TestTraceback(unittest.TestCase):
    def test_repr(self):
        def get_repr(*args) -> str:
            return repr(tracemalloc.Traceback(*args))

        self.assertEqual(get_repr(()), "<Traceback ()>")
        self.assertEqual(get_repr((), 0), "<Traceback () total_nframe=0>")

        frames = (("f1", 1), ("f2", 2))
        exp_repr_frames = (
            "(<Frame filename='f2' lineno=2>,"
            " <Frame filename='f1' lineno=1>)"
        )
        self.assertEqual(get_repr(frames),
                         f"<Traceback {exp_repr_frames}>")
        self.assertEqual(get_repr(frames, 2),
                         f"<Traceback {exp_repr_frames} total_nframe=2>")


klasse TestTracemallocEnabled(unittest.TestCase):
    def setUp(self):
        wenn tracemalloc.is_tracing():
            self.skipTest("tracemalloc must be stopped before the test")

        tracemalloc.start(1)

    def tearDown(self):
        tracemalloc.stop()

    def test_get_tracemalloc_memory(self):
        data = [allocate_bytes(123) fuer count in range(1000)]
        size = tracemalloc.get_tracemalloc_memory()
        self.assertGreaterEqual(size, 0)

        tracemalloc.clear_traces()
        size2 = tracemalloc.get_tracemalloc_memory()
        self.assertGreaterEqual(size2, 0)
        self.assertLessEqual(size2, size)

    def test_get_object_traceback(self):
        tracemalloc.clear_traces()
        obj_size = 12345
        obj, obj_traceback = allocate_bytes(obj_size)
        traceback = tracemalloc.get_object_traceback(obj)
        self.assertEqual(traceback, obj_traceback)

    def test_new_reference(self):
        tracemalloc.clear_traces()
        # gc.collect() indirectly calls PyList_ClearFreeList()
        support.gc_collect()

        # Create a list and "destroy it": put it in the PyListObject free list
        obj = []
        obj = Nichts

        # Create a list which should reuse the previously created empty list
        obj = []

        nframe = tracemalloc.get_traceback_limit()
        frames = get_frames(nframe, -3)
        obj_traceback = tracemalloc.Traceback(frames, min(len(frames), nframe))

        traceback = tracemalloc.get_object_traceback(obj)
        self.assertIsNotNichts(traceback)
        self.assertEqual(traceback, obj_traceback)

    def test_set_traceback_limit(self):
        obj_size = 10

        tracemalloc.stop()
        self.assertRaises(ValueError, tracemalloc.start, -1)

        tracemalloc.stop()
        tracemalloc.start(10)
        obj2, obj2_traceback = allocate_bytes(obj_size)
        traceback = tracemalloc.get_object_traceback(obj2)
        self.assertEqual(len(traceback), 10)
        self.assertEqual(traceback, obj2_traceback)

        tracemalloc.stop()
        tracemalloc.start(1)
        obj, obj_traceback = allocate_bytes(obj_size)
        traceback = tracemalloc.get_object_traceback(obj)
        self.assertEqual(len(traceback), 1)
        self.assertEqual(traceback, obj_traceback)

    def find_trace(self, traces, traceback, size):
        # filter also by size to ignore the memory allocated by
        # _PyRefchain_Trace() wenn Python is built with Py_TRACE_REFS.
        fuer trace in traces:
            wenn trace[2] == traceback._frames and trace[1] == size:
                return trace

        self.fail("trace not found")

    def test_get_traces(self):
        tracemalloc.clear_traces()
        obj_size = 12345
        obj, obj_traceback = allocate_bytes(obj_size)

        traces = tracemalloc._get_traces()
        trace = self.find_trace(traces, obj_traceback, obj_size)

        self.assertIsInstance(trace, tuple)
        domain, size, traceback, length = trace
        self.assertEqual(traceback, obj_traceback._frames)

        tracemalloc.stop()
        self.assertEqual(tracemalloc._get_traces(), [])

    def test_get_traces_intern_traceback(self):
        # dummy wrappers to get more useful and identical frames in the traceback
        def allocate_bytes2(size):
            return allocate_bytes(size)
        def allocate_bytes3(size):
            return allocate_bytes2(size)
        def allocate_bytes4(size):
            return allocate_bytes3(size)

        # Ensure that two identical tracebacks are not duplicated
        tracemalloc.stop()
        tracemalloc.start(4)
        obj1_size = 123
        obj2_size = 125
        obj1, obj1_traceback = allocate_bytes4(obj1_size)
        obj2, obj2_traceback = allocate_bytes4(obj2_size)

        traces = tracemalloc._get_traces()

        obj1_traceback._frames = tuple(reversed(obj1_traceback._frames))
        obj2_traceback._frames = tuple(reversed(obj2_traceback._frames))

        trace1 = self.find_trace(traces, obj1_traceback, obj1_size)
        trace2 = self.find_trace(traces, obj2_traceback, obj2_size)
        domain1, size1, traceback1, length1 = trace1
        domain2, size2, traceback2, length2 = trace2
        self.assertIs(traceback2, traceback1)

    def test_get_traced_memory(self):
        # Python allocates some internals objects, so the test must tolerate
        # a small difference between the expected size and the real usage
        max_error = 2048

        # allocate one object
        obj_size = 1024 * 1024
        tracemalloc.clear_traces()
        obj, obj_traceback = allocate_bytes(obj_size)
        size, peak_size = tracemalloc.get_traced_memory()
        self.assertGreaterEqual(size, obj_size)
        self.assertGreaterEqual(peak_size, size)

        self.assertLessEqual(size - obj_size, max_error)
        self.assertLessEqual(peak_size - size, max_error)

        # destroy the object
        obj = Nichts
        size2, peak_size2 = tracemalloc.get_traced_memory()
        self.assertLess(size2, size)
        self.assertGreaterEqual(size - size2, obj_size - max_error)
        self.assertGreaterEqual(peak_size2, peak_size)

        # clear_traces() must reset traced memory counters
        tracemalloc.clear_traces()
        self.assertEqual(tracemalloc.get_traced_memory(), (0, 0))

        # allocate another object
        obj, obj_traceback = allocate_bytes(obj_size)
        size, peak_size = tracemalloc.get_traced_memory()
        self.assertGreaterEqual(size, obj_size)

        # stop() also resets traced memory counters
        tracemalloc.stop()
        self.assertEqual(tracemalloc.get_traced_memory(), (0, 0))

    def test_clear_traces(self):
        obj, obj_traceback = allocate_bytes(123)
        traceback = tracemalloc.get_object_traceback(obj)
        self.assertIsNotNichts(traceback)

        tracemalloc.clear_traces()
        traceback2 = tracemalloc.get_object_traceback(obj)
        self.assertIsNichts(traceback2)

    def test_reset_peak(self):
        # Python allocates some internals objects, so the test must tolerate
        # a small difference between the expected size and the real usage
        tracemalloc.clear_traces()

        # Example: allocate a large piece of memory, temporarily
        large_sum = sum(list(range(100000)))
        size1, peak1 = tracemalloc.get_traced_memory()

        # reset_peak() resets peak to traced memory: peak2 < peak1
        tracemalloc.reset_peak()
        size2, peak2 = tracemalloc.get_traced_memory()
        self.assertGreaterEqual(peak2, size2)
        self.assertLess(peak2, peak1)

        # check that peak continue to be updated wenn new memory is allocated:
        # peak3 > peak2
        obj_size = 1024 * 1024
        obj, obj_traceback = allocate_bytes(obj_size)
        size3, peak3 = tracemalloc.get_traced_memory()
        self.assertGreaterEqual(peak3, size3)
        self.assertGreater(peak3, peak2)
        self.assertGreaterEqual(peak3 - peak2, obj_size)

    def test_is_tracing(self):
        tracemalloc.stop()
        self.assertFalsch(tracemalloc.is_tracing())

        tracemalloc.start()
        self.assertWahr(tracemalloc.is_tracing())

    def test_snapshot(self):
        obj, source = allocate_bytes(123)

        # take a snapshot
        snapshot = tracemalloc.take_snapshot()

        # This can vary
        self.assertGreater(snapshot.traces[1].traceback.total_nframe, 10)

        # write on disk
        snapshot.dump(os_helper.TESTFN)
        self.addCleanup(os_helper.unlink, os_helper.TESTFN)

        # load from disk
        snapshot2 = tracemalloc.Snapshot.load(os_helper.TESTFN)
        self.assertEqual(snapshot2.traces, snapshot.traces)

        # tracemalloc must be tracing memory allocations to take a snapshot
        tracemalloc.stop()
        with self.assertRaises(RuntimeError) as cm:
            tracemalloc.take_snapshot()
        self.assertEqual(str(cm.exception),
                         "the tracemalloc module must be tracing memory "
                         "allocations to take a snapshot")

    def test_snapshot_save_attr(self):
        # take a snapshot with a new attribute
        snapshot = tracemalloc.take_snapshot()
        snapshot.test_attr = "new"
        snapshot.dump(os_helper.TESTFN)
        self.addCleanup(os_helper.unlink, os_helper.TESTFN)

        # load() should recreate the attribute
        snapshot2 = tracemalloc.Snapshot.load(os_helper.TESTFN)
        self.assertEqual(snapshot2.test_attr, "new")

    def fork_child(self):
        wenn not tracemalloc.is_tracing():
            return 2

        obj_size = 12345
        obj, obj_traceback = allocate_bytes(obj_size)
        traceback = tracemalloc.get_object_traceback(obj)
        wenn traceback is Nichts:
            return 3

        # everything is fine
        return 0

    @warnings_helper.ignore_fork_in_thread_deprecation_warnings()
    @support.requires_fork()
    def test_fork(self):
        # check that tracemalloc is still working after fork
        pid = os.fork()
        wenn not pid:
            # child
            exitcode = 1
            try:
                exitcode = self.fork_child()
            finally:
                os._exit(exitcode)
        sonst:
            support.wait_process(pid, exitcode=0)

    def test_no_incomplete_frames(self):
        tracemalloc.stop()
        tracemalloc.start(8)

        def f(x):
            def g():
                return x
            return g

        obj = f(0).__closure__[0]
        traceback = tracemalloc.get_object_traceback(obj)
        self.assertIn("test_tracemalloc", traceback[-1].filename)
        self.assertNotIn("test_tracemalloc", traceback[-2].filename)


klasse TestSnapshot(unittest.TestCase):
    maxDiff = 4000

    def test_create_snapshot(self):
        raw_traces = [(0, 5, (('a.py', 2),), 10)]

        with contextlib.ExitStack() as stack:
            stack.enter_context(patch.object(tracemalloc, 'is_tracing',
                                             return_value=Wahr))
            stack.enter_context(patch.object(tracemalloc, 'get_traceback_limit',
                                             return_value=5))
            stack.enter_context(patch.object(tracemalloc, '_get_traces',
                                             return_value=raw_traces))

            snapshot = tracemalloc.take_snapshot()
            self.assertEqual(snapshot.traceback_limit, 5)
            self.assertEqual(len(snapshot.traces), 1)
            trace = snapshot.traces[0]
            self.assertEqual(trace.size, 5)
            self.assertEqual(trace.traceback.total_nframe, 10)
            self.assertEqual(len(trace.traceback), 1)
            self.assertEqual(trace.traceback[0].filename, 'a.py')
            self.assertEqual(trace.traceback[0].lineno, 2)

    def test_filter_traces(self):
        snapshot, snapshot2 = create_snapshots()
        filter1 = tracemalloc.Filter(Falsch, "b.py")
        filter2 = tracemalloc.Filter(Wahr, "a.py", 2)
        filter3 = tracemalloc.Filter(Wahr, "a.py", 5)

        original_traces = list(snapshot.traces._traces)

        # exclude b.py
        snapshot3 = snapshot.filter_traces((filter1,))
        self.assertEqual(snapshot3.traces._traces, [
            (0, 10, (('a.py', 2), ('b.py', 4)), 3),
            (0, 10, (('a.py', 2), ('b.py', 4)), 3),
            (0, 10, (('a.py', 2), ('b.py', 4)), 3),
            (1, 2, (('a.py', 5), ('b.py', 4)), 3),
            (3, 7, (('<unknown>', 0),), 1),
        ])

        # filter_traces() must not touch the original snapshot
        self.assertEqual(snapshot.traces._traces, original_traces)

        # only include two lines of a.py
        snapshot4 = snapshot3.filter_traces((filter2, filter3))
        self.assertEqual(snapshot4.traces._traces, [
            (0, 10, (('a.py', 2), ('b.py', 4)), 3),
            (0, 10, (('a.py', 2), ('b.py', 4)), 3),
            (0, 10, (('a.py', 2), ('b.py', 4)), 3),
            (1, 2, (('a.py', 5), ('b.py', 4)), 3),
        ])

        # No filter: just duplicate the snapshot
        snapshot5 = snapshot.filter_traces(())
        self.assertIsNot(snapshot5, snapshot)
        self.assertIsNot(snapshot5.traces, snapshot.traces)
        self.assertEqual(snapshot5.traces, snapshot.traces)

        self.assertRaises(TypeError, snapshot.filter_traces, filter1)

    def test_filter_traces_domain(self):
        snapshot, snapshot2 = create_snapshots()
        filter1 = tracemalloc.Filter(Falsch, "a.py", domain=1)
        filter2 = tracemalloc.Filter(Wahr, "a.py", domain=1)

        original_traces = list(snapshot.traces._traces)

        # exclude a.py of domain 1
        snapshot3 = snapshot.filter_traces((filter1,))
        self.assertEqual(snapshot3.traces._traces, [
            (0, 10, (('a.py', 2), ('b.py', 4)), 3),
            (0, 10, (('a.py', 2), ('b.py', 4)), 3),
            (0, 10, (('a.py', 2), ('b.py', 4)), 3),
            (2, 66, (('b.py', 1),), 1),
            (3, 7, (('<unknown>', 0),), 1),
        ])

        # include domain 1
        snapshot3 = snapshot.filter_traces((filter1,))
        self.assertEqual(snapshot3.traces._traces, [
            (0, 10, (('a.py', 2), ('b.py', 4)), 3),
            (0, 10, (('a.py', 2), ('b.py', 4)), 3),
            (0, 10, (('a.py', 2), ('b.py', 4)), 3),
            (2, 66, (('b.py', 1),), 1),
            (3, 7, (('<unknown>', 0),), 1),
        ])

    def test_filter_traces_domain_filter(self):
        snapshot, snapshot2 = create_snapshots()
        filter1 = tracemalloc.DomainFilter(Falsch, domain=3)
        filter2 = tracemalloc.DomainFilter(Wahr, domain=3)

        # exclude domain 2
        snapshot3 = snapshot.filter_traces((filter1,))
        self.assertEqual(snapshot3.traces._traces, [
            (0, 10, (('a.py', 2), ('b.py', 4)), 3),
            (0, 10, (('a.py', 2), ('b.py', 4)), 3),
            (0, 10, (('a.py', 2), ('b.py', 4)), 3),
            (1, 2, (('a.py', 5), ('b.py', 4)), 3),
            (2, 66, (('b.py', 1),), 1),
        ])

        # include domain 2
        snapshot3 = snapshot.filter_traces((filter2,))
        self.assertEqual(snapshot3.traces._traces, [
            (3, 7, (('<unknown>', 0),), 1),
        ])

    def test_snapshot_group_by_line(self):
        snapshot, snapshot2 = create_snapshots()
        tb_0 = traceback_lineno('<unknown>', 0)
        tb_a_2 = traceback_lineno('a.py', 2)
        tb_a_5 = traceback_lineno('a.py', 5)
        tb_b_1 = traceback_lineno('b.py', 1)
        tb_c_578 = traceback_lineno('c.py', 578)

        # stats per file and line
        stats1 = snapshot.statistics('lineno')
        self.assertEqual(stats1, [
            tracemalloc.Statistic(tb_b_1, 66, 1),
            tracemalloc.Statistic(tb_a_2, 30, 3),
            tracemalloc.Statistic(tb_0, 7, 1),
            tracemalloc.Statistic(tb_a_5, 2, 1),
        ])

        # stats per file and line (2)
        stats2 = snapshot2.statistics('lineno')
        self.assertEqual(stats2, [
            tracemalloc.Statistic(tb_a_5, 5002, 2),
            tracemalloc.Statistic(tb_c_578, 400, 1),
            tracemalloc.Statistic(tb_a_2, 30, 3),
        ])

        # stats diff per file and line
        statistics = snapshot2.compare_to(snapshot, 'lineno')
        self.assertEqual(statistics, [
            tracemalloc.StatisticDiff(tb_a_5, 5002, 5000, 2, 1),
            tracemalloc.StatisticDiff(tb_c_578, 400, 400, 1, 1),
            tracemalloc.StatisticDiff(tb_b_1, 0, -66, 0, -1),
            tracemalloc.StatisticDiff(tb_0, 0, -7, 0, -1),
            tracemalloc.StatisticDiff(tb_a_2, 30, 0, 3, 0),
        ])

    def test_snapshot_group_by_file(self):
        snapshot, snapshot2 = create_snapshots()
        tb_0 = traceback_filename('<unknown>')
        tb_a = traceback_filename('a.py')
        tb_b = traceback_filename('b.py')
        tb_c = traceback_filename('c.py')

        # stats per file
        stats1 = snapshot.statistics('filename')
        self.assertEqual(stats1, [
            tracemalloc.Statistic(tb_b, 66, 1),
            tracemalloc.Statistic(tb_a, 32, 4),
            tracemalloc.Statistic(tb_0, 7, 1),
        ])

        # stats per file (2)
        stats2 = snapshot2.statistics('filename')
        self.assertEqual(stats2, [
            tracemalloc.Statistic(tb_a, 5032, 5),
            tracemalloc.Statistic(tb_c, 400, 1),
        ])

        # stats diff per file
        diff = snapshot2.compare_to(snapshot, 'filename')
        self.assertEqual(diff, [
            tracemalloc.StatisticDiff(tb_a, 5032, 5000, 5, 1),
            tracemalloc.StatisticDiff(tb_c, 400, 400, 1, 1),
            tracemalloc.StatisticDiff(tb_b, 0, -66, 0, -1),
            tracemalloc.StatisticDiff(tb_0, 0, -7, 0, -1),
        ])

    def test_snapshot_group_by_traceback(self):
        snapshot, snapshot2 = create_snapshots()

        # stats per file
        tb1 = traceback(('a.py', 2), ('b.py', 4))
        tb2 = traceback(('a.py', 5), ('b.py', 4))
        tb3 = traceback(('b.py', 1))
        tb4 = traceback(('<unknown>', 0))
        stats1 = snapshot.statistics('traceback')
        self.assertEqual(stats1, [
            tracemalloc.Statistic(tb3, 66, 1),
            tracemalloc.Statistic(tb1, 30, 3),
            tracemalloc.Statistic(tb4, 7, 1),
            tracemalloc.Statistic(tb2, 2, 1),
        ])

        # stats per file (2)
        tb5 = traceback(('c.py', 578))
        stats2 = snapshot2.statistics('traceback')
        self.assertEqual(stats2, [
            tracemalloc.Statistic(tb2, 5002, 2),
            tracemalloc.Statistic(tb5, 400, 1),
            tracemalloc.Statistic(tb1, 30, 3),
        ])

        # stats diff per file
        diff = snapshot2.compare_to(snapshot, 'traceback')
        self.assertEqual(diff, [
            tracemalloc.StatisticDiff(tb2, 5002, 5000, 2, 1),
            tracemalloc.StatisticDiff(tb5, 400, 400, 1, 1),
            tracemalloc.StatisticDiff(tb3, 0, -66, 0, -1),
            tracemalloc.StatisticDiff(tb4, 0, -7, 0, -1),
            tracemalloc.StatisticDiff(tb1, 30, 0, 3, 0),
        ])

        self.assertRaises(ValueError,
                          snapshot.statistics, 'traceback', cumulative=Wahr)

    def test_snapshot_group_by_cumulative(self):
        snapshot, snapshot2 = create_snapshots()
        tb_0 = traceback_filename('<unknown>')
        tb_a = traceback_filename('a.py')
        tb_b = traceback_filename('b.py')
        tb_a_2 = traceback_lineno('a.py', 2)
        tb_a_5 = traceback_lineno('a.py', 5)
        tb_b_1 = traceback_lineno('b.py', 1)
        tb_b_4 = traceback_lineno('b.py', 4)

        # per file
        stats = snapshot.statistics('filename', Wahr)
        self.assertEqual(stats, [
            tracemalloc.Statistic(tb_b, 98, 5),
            tracemalloc.Statistic(tb_a, 32, 4),
            tracemalloc.Statistic(tb_0, 7, 1),
        ])

        # per line
        stats = snapshot.statistics('lineno', Wahr)
        self.assertEqual(stats, [
            tracemalloc.Statistic(tb_b_1, 66, 1),
            tracemalloc.Statistic(tb_b_4, 32, 4),
            tracemalloc.Statistic(tb_a_2, 30, 3),
            tracemalloc.Statistic(tb_0, 7, 1),
            tracemalloc.Statistic(tb_a_5, 2, 1),
        ])

    def test_trace_format(self):
        snapshot, snapshot2 = create_snapshots()
        trace = snapshot.traces[0]
        self.assertEqual(str(trace), 'b.py:4: 10 B')
        traceback = trace.traceback
        self.assertEqual(str(traceback), 'b.py:4')
        frame = traceback[0]
        self.assertEqual(str(frame), 'b.py:4')

    def test_statistic_format(self):
        snapshot, snapshot2 = create_snapshots()
        stats = snapshot.statistics('lineno')
        stat = stats[0]
        self.assertEqual(str(stat),
                         'b.py:1: size=66 B, count=1, average=66 B')

    def test_statistic_diff_format(self):
        snapshot, snapshot2 = create_snapshots()
        stats = snapshot2.compare_to(snapshot, 'lineno')
        stat = stats[0]
        self.assertEqual(str(stat),
                         'a.py:5: size=5002 B (+5000 B), count=2 (+1), average=2501 B')

    def test_slices(self):
        snapshot, snapshot2 = create_snapshots()
        self.assertEqual(snapshot.traces[:2],
                         (snapshot.traces[0], snapshot.traces[1]))

        traceback = snapshot.traces[0].traceback
        self.assertEqual(traceback[:2],
                         (traceback[0], traceback[1]))

    def test_format_traceback(self):
        snapshot, snapshot2 = create_snapshots()
        def getline(filename, lineno):
            return '  <%s, %s>' % (filename, lineno)
        with unittest.mock.patch('tracemalloc.linecache.getline',
                                 side_effect=getline):
            tb = snapshot.traces[0].traceback
            self.assertEqual(tb.format(),
                             ['  File "b.py", line 4',
                              '    <b.py, 4>',
                              '  File "a.py", line 2',
                              '    <a.py, 2>'])

            self.assertEqual(tb.format(limit=1),
                             ['  File "a.py", line 2',
                              '    <a.py, 2>'])

            self.assertEqual(tb.format(limit=-1),
                             ['  File "b.py", line 4',
                              '    <b.py, 4>'])

            self.assertEqual(tb.format(most_recent_first=Wahr),
                             ['  File "a.py", line 2',
                              '    <a.py, 2>',
                              '  File "b.py", line 4',
                              '    <b.py, 4>'])

            self.assertEqual(tb.format(limit=1, most_recent_first=Wahr),
                             ['  File "a.py", line 2',
                              '    <a.py, 2>'])

            self.assertEqual(tb.format(limit=-1, most_recent_first=Wahr),
                             ['  File "b.py", line 4',
                              '    <b.py, 4>'])


klasse TestFilters(unittest.TestCase):
    maxDiff = 2048

    def test_filter_attributes(self):
        # test default values
        f = tracemalloc.Filter(Wahr, "abc")
        self.assertEqual(f.inclusive, Wahr)
        self.assertEqual(f.filename_pattern, "abc")
        self.assertIsNichts(f.lineno)
        self.assertEqual(f.all_frames, Falsch)

        # test custom values
        f = tracemalloc.Filter(Falsch, "test.py", 123, Wahr)
        self.assertEqual(f.inclusive, Falsch)
        self.assertEqual(f.filename_pattern, "test.py")
        self.assertEqual(f.lineno, 123)
        self.assertEqual(f.all_frames, Wahr)

        # parameters passed by keyword
        f = tracemalloc.Filter(inclusive=Falsch, filename_pattern="test.py", lineno=123, all_frames=Wahr)
        self.assertEqual(f.inclusive, Falsch)
        self.assertEqual(f.filename_pattern, "test.py")
        self.assertEqual(f.lineno, 123)
        self.assertEqual(f.all_frames, Wahr)

        # read-only attribute
        self.assertRaises(AttributeError, setattr, f, "filename_pattern", "abc")

    def test_filter_match(self):
        # filter without line number
        f = tracemalloc.Filter(Wahr, "abc")
        self.assertWahr(f._match_frame("abc", 0))
        self.assertWahr(f._match_frame("abc", 5))
        self.assertWahr(f._match_frame("abc", 10))
        self.assertFalsch(f._match_frame("12356", 0))
        self.assertFalsch(f._match_frame("12356", 5))
        self.assertFalsch(f._match_frame("12356", 10))

        f = tracemalloc.Filter(Falsch, "abc")
        self.assertFalsch(f._match_frame("abc", 0))
        self.assertFalsch(f._match_frame("abc", 5))
        self.assertFalsch(f._match_frame("abc", 10))
        self.assertWahr(f._match_frame("12356", 0))
        self.assertWahr(f._match_frame("12356", 5))
        self.assertWahr(f._match_frame("12356", 10))

        # filter with line number > 0
        f = tracemalloc.Filter(Wahr, "abc", 5)
        self.assertFalsch(f._match_frame("abc", 0))
        self.assertWahr(f._match_frame("abc", 5))
        self.assertFalsch(f._match_frame("abc", 10))
        self.assertFalsch(f._match_frame("12356", 0))
        self.assertFalsch(f._match_frame("12356", 5))
        self.assertFalsch(f._match_frame("12356", 10))

        f = tracemalloc.Filter(Falsch, "abc", 5)
        self.assertWahr(f._match_frame("abc", 0))
        self.assertFalsch(f._match_frame("abc", 5))
        self.assertWahr(f._match_frame("abc", 10))
        self.assertWahr(f._match_frame("12356", 0))
        self.assertWahr(f._match_frame("12356", 5))
        self.assertWahr(f._match_frame("12356", 10))

        # filter with line number 0
        f = tracemalloc.Filter(Wahr, "abc", 0)
        self.assertWahr(f._match_frame("abc", 0))
        self.assertFalsch(f._match_frame("abc", 5))
        self.assertFalsch(f._match_frame("abc", 10))
        self.assertFalsch(f._match_frame("12356", 0))
        self.assertFalsch(f._match_frame("12356", 5))
        self.assertFalsch(f._match_frame("12356", 10))

        f = tracemalloc.Filter(Falsch, "abc", 0)
        self.assertFalsch(f._match_frame("abc", 0))
        self.assertWahr(f._match_frame("abc", 5))
        self.assertWahr(f._match_frame("abc", 10))
        self.assertWahr(f._match_frame("12356", 0))
        self.assertWahr(f._match_frame("12356", 5))
        self.assertWahr(f._match_frame("12356", 10))

    def test_filter_match_filename(self):
        def fnmatch(inclusive, filename, pattern):
            f = tracemalloc.Filter(inclusive, pattern)
            return f._match_frame(filename, 0)

        self.assertWahr(fnmatch(Wahr, "abc", "abc"))
        self.assertFalsch(fnmatch(Wahr, "12356", "abc"))
        self.assertFalsch(fnmatch(Wahr, "<unknown>", "abc"))

        self.assertFalsch(fnmatch(Falsch, "abc", "abc"))
        self.assertWahr(fnmatch(Falsch, "12356", "abc"))
        self.assertWahr(fnmatch(Falsch, "<unknown>", "abc"))

    def test_filter_match_filename_joker(self):
        def fnmatch(filename, pattern):
            filter = tracemalloc.Filter(Wahr, pattern)
            return filter._match_frame(filename, 0)

        # empty string
        self.assertFalsch(fnmatch('abc', ''))
        self.assertFalsch(fnmatch('', 'abc'))
        self.assertWahr(fnmatch('', ''))
        self.assertWahr(fnmatch('', '*'))

        # no *
        self.assertWahr(fnmatch('abc', 'abc'))
        self.assertFalsch(fnmatch('abc', 'abcd'))
        self.assertFalsch(fnmatch('abc', 'def'))

        # a*
        self.assertWahr(fnmatch('abc', 'a*'))
        self.assertWahr(fnmatch('abc', 'abc*'))
        self.assertFalsch(fnmatch('abc', 'b*'))
        self.assertFalsch(fnmatch('abc', 'abcd*'))

        # a*b
        self.assertWahr(fnmatch('abc', 'a*c'))
        self.assertWahr(fnmatch('abcdcx', 'a*cx'))
        self.assertFalsch(fnmatch('abb', 'a*c'))
        self.assertFalsch(fnmatch('abcdce', 'a*cx'))

        # a*b*c
        self.assertWahr(fnmatch('abcde', 'a*c*e'))
        self.assertWahr(fnmatch('abcbdefeg', 'a*bd*eg'))
        self.assertFalsch(fnmatch('abcdd', 'a*c*e'))
        self.assertFalsch(fnmatch('abcbdefef', 'a*bd*eg'))

        # replace .pyc suffix with .py
        self.assertWahr(fnmatch('a.pyc', 'a.py'))
        self.assertWahr(fnmatch('a.py', 'a.pyc'))

        wenn os.name == 'nt':
            # case insensitive
            self.assertWahr(fnmatch('aBC', 'ABc'))
            self.assertWahr(fnmatch('aBcDe', 'Ab*dE'))

            self.assertWahr(fnmatch('a.pyc', 'a.PY'))
            self.assertWahr(fnmatch('a.py', 'a.PYC'))
        sonst:
            # case sensitive
            self.assertFalsch(fnmatch('aBC', 'ABc'))
            self.assertFalsch(fnmatch('aBcDe', 'Ab*dE'))

            self.assertFalsch(fnmatch('a.pyc', 'a.PY'))
            self.assertFalsch(fnmatch('a.py', 'a.PYC'))

        wenn os.name == 'nt':
            # normalize alternate separator "/" to the standard separator "\"
            self.assertWahr(fnmatch(r'a/b', r'a\b'))
            self.assertWahr(fnmatch(r'a\b', r'a/b'))
            self.assertWahr(fnmatch(r'a/b\c', r'a\b/c'))
            self.assertWahr(fnmatch(r'a/b/c', r'a\b\c'))
        sonst:
            # there is no alternate separator
            self.assertFalsch(fnmatch(r'a/b', r'a\b'))
            self.assertFalsch(fnmatch(r'a\b', r'a/b'))
            self.assertFalsch(fnmatch(r'a/b\c', r'a\b/c'))
            self.assertFalsch(fnmatch(r'a/b/c', r'a\b\c'))

        # as of 3.5, .pyo is no longer munged to .py
        self.assertFalsch(fnmatch('a.pyo', 'a.py'))

    def test_filter_match_trace(self):
        t1 = (("a.py", 2), ("b.py", 3))
        t2 = (("b.py", 4), ("b.py", 5))
        t3 = (("c.py", 5), ('<unknown>', 0))
        unknown = (('<unknown>', 0),)

        f = tracemalloc.Filter(Wahr, "b.py", all_frames=Wahr)
        self.assertWahr(f._match_traceback(t1))
        self.assertWahr(f._match_traceback(t2))
        self.assertFalsch(f._match_traceback(t3))
        self.assertFalsch(f._match_traceback(unknown))

        f = tracemalloc.Filter(Wahr, "b.py", all_frames=Falsch)
        self.assertFalsch(f._match_traceback(t1))
        self.assertWahr(f._match_traceback(t2))
        self.assertFalsch(f._match_traceback(t3))
        self.assertFalsch(f._match_traceback(unknown))

        f = tracemalloc.Filter(Falsch, "b.py", all_frames=Wahr)
        self.assertFalsch(f._match_traceback(t1))
        self.assertFalsch(f._match_traceback(t2))
        self.assertWahr(f._match_traceback(t3))
        self.assertWahr(f._match_traceback(unknown))

        f = tracemalloc.Filter(Falsch, "b.py", all_frames=Falsch)
        self.assertWahr(f._match_traceback(t1))
        self.assertFalsch(f._match_traceback(t2))
        self.assertWahr(f._match_traceback(t3))
        self.assertWahr(f._match_traceback(unknown))

        f = tracemalloc.Filter(Falsch, "<unknown>", all_frames=Falsch)
        self.assertWahr(f._match_traceback(t1))
        self.assertWahr(f._match_traceback(t2))
        self.assertWahr(f._match_traceback(t3))
        self.assertFalsch(f._match_traceback(unknown))

        f = tracemalloc.Filter(Wahr, "<unknown>", all_frames=Wahr)
        self.assertFalsch(f._match_traceback(t1))
        self.assertFalsch(f._match_traceback(t2))
        self.assertWahr(f._match_traceback(t3))
        self.assertWahr(f._match_traceback(unknown))

        f = tracemalloc.Filter(Falsch, "<unknown>", all_frames=Wahr)
        self.assertWahr(f._match_traceback(t1))
        self.assertWahr(f._match_traceback(t2))
        self.assertFalsch(f._match_traceback(t3))
        self.assertFalsch(f._match_traceback(unknown))


klasse TestCommandLine(unittest.TestCase):
    def test_env_var_disabled_by_default(self):
        # not tracing by default
        code = 'import tracemalloc; drucke(tracemalloc.is_tracing())'
        ok, stdout, stderr = assert_python_ok('-c', code)
        stdout = stdout.rstrip()
        self.assertEqual(stdout, b'Falsch')

    @unittest.skipIf(interpreter_requires_environment(),
                     'Cannot run -E tests when PYTHON env vars are required.')
    def test_env_var_ignored_with_E(self):
        """PYTHON* environment variables must be ignored when -E is present."""
        code = 'import tracemalloc; drucke(tracemalloc.is_tracing())'
        ok, stdout, stderr = assert_python_ok('-E', '-c', code, PYTHONTRACEMALLOC='1')
        stdout = stdout.rstrip()
        self.assertEqual(stdout, b'Falsch')

    def test_env_var_disabled(self):
        # tracing at startup
        code = 'import tracemalloc; drucke(tracemalloc.is_tracing())'
        ok, stdout, stderr = assert_python_ok('-c', code, PYTHONTRACEMALLOC='0')
        stdout = stdout.rstrip()
        self.assertEqual(stdout, b'Falsch')

    def test_env_var_enabled_at_startup(self):
        # tracing at startup
        code = 'import tracemalloc; drucke(tracemalloc.is_tracing())'
        ok, stdout, stderr = assert_python_ok('-c', code, PYTHONTRACEMALLOC='1')
        stdout = stdout.rstrip()
        self.assertEqual(stdout, b'Wahr')

    def test_env_limit(self):
        # start and set the number of frames
        code = 'import tracemalloc; drucke(tracemalloc.get_traceback_limit())'
        ok, stdout, stderr = assert_python_ok('-c', code, PYTHONTRACEMALLOC='10')
        stdout = stdout.rstrip()
        self.assertEqual(stdout, b'10')

    @force_not_colorized
    def check_env_var_invalid(self, nframe):
        with support.SuppressCrashReport():
            ok, stdout, stderr = assert_python_failure(
                '-c', 'pass',
                PYTHONTRACEMALLOC=str(nframe))

        wenn b'ValueError: the number of frames must be in range' in stderr:
            return
        wenn b'PYTHONTRACEMALLOC: invalid number of frames' in stderr:
            return
        self.fail(f"unexpected output: {stderr!a}")

    def test_env_var_invalid(self):
        fuer nframe in INVALID_NFRAME:
            with self.subTest(nframe=nframe):
                self.check_env_var_invalid(nframe)

    def test_sys_xoptions(self):
        fuer xoptions, nframe in (
            ('tracemalloc', 1),
            ('tracemalloc=1', 1),
            ('tracemalloc=15', 15),
        ):
            with self.subTest(xoptions=xoptions, nframe=nframe):
                code = 'import tracemalloc; drucke(tracemalloc.get_traceback_limit())'
                ok, stdout, stderr = assert_python_ok('-X', xoptions, '-c', code)
                stdout = stdout.rstrip()
                self.assertEqual(stdout, str(nframe).encode('ascii'))

    def check_sys_xoptions_invalid(self, nframe):
        args = ('-X', 'tracemalloc=%s' % nframe, '-c', 'pass')
        with support.SuppressCrashReport():
            ok, stdout, stderr = assert_python_failure(*args)

        wenn b'ValueError: the number of frames must be in range' in stderr:
            return
        wenn b'-X tracemalloc=NFRAME: invalid number of frames' in stderr:
            return
        self.fail(f"unexpected output: {stderr!a}")

    @force_not_colorized
    def test_sys_xoptions_invalid(self):
        fuer nframe in INVALID_NFRAME:
            with self.subTest(nframe=nframe):
                self.check_sys_xoptions_invalid(nframe)

    @unittest.skipIf(_testcapi is Nichts, 'need _testcapi')
    def test_pymem_alloc0(self):
        # Issue #21639: Check that PyMem_Malloc(0) with tracemalloc enabled
        # does not crash.
        code = 'import _testcapi; _testcapi.test_pymem_alloc0(); 1'
        assert_python_ok('-X', 'tracemalloc', '-c', code)


@unittest.skipIf(_testcapi is Nichts, 'need _testcapi')
klasse TestCAPI(unittest.TestCase):
    maxDiff = 80 * 20

    def setUp(self):
        wenn tracemalloc.is_tracing():
            self.skipTest("tracemalloc must be stopped before the test")

        self.domain = 5
        self.size = 123
        self.obj = allocate_bytes(self.size)[0]

        # fuer the type "object", id(obj) is the address of its memory block.
        # This type is not tracked by the garbage collector
        self.ptr = id(self.obj)

    def tearDown(self):
        tracemalloc.stop()

    def get_traceback(self):
        frames = _testinternalcapi._PyTraceMalloc_GetTraceback(self.domain, self.ptr)
        wenn frames is not Nichts:
            return tracemalloc.Traceback(frames)
        sonst:
            return Nichts

    def track(self, release_gil=Falsch, nframe=1):
        frames = get_frames(nframe, 1)
        _testcapi.tracemalloc_track(self.domain, self.ptr, self.size,
                                    release_gil)
        return frames

    def untrack(self, release_gil=Falsch):
        _testcapi.tracemalloc_untrack(self.domain, self.ptr, release_gil)

    def get_traced_memory(self):
        # Get the traced size in the domain
        snapshot = tracemalloc.take_snapshot()
        domain_filter = tracemalloc.DomainFilter(Wahr, self.domain)
        snapshot = snapshot.filter_traces([domain_filter])
        return sum(trace.size fuer trace in snapshot.traces)

    def check_track(self, release_gil):
        nframe = 5
        tracemalloc.start(nframe)

        size = tracemalloc.get_traced_memory()[0]

        frames = self.track(release_gil, nframe)
        self.assertEqual(self.get_traceback(),
                         tracemalloc.Traceback(frames))

        self.assertEqual(self.get_traced_memory(), self.size)

    def test_track(self):
        self.check_track(Falsch)

    def test_track_without_gil(self):
        # check that calling _PyTraceMalloc_Track() without holding the GIL
        # works too
        self.check_track(Wahr)

    def test_track_already_tracked(self):
        nframe = 5
        tracemalloc.start(nframe)

        # track a first time
        self.track()

        # calling _PyTraceMalloc_Track() must remove the old trace and add
        # a new trace with the new traceback
        frames = self.track(nframe=nframe)
        self.assertEqual(self.get_traceback(),
                         tracemalloc.Traceback(frames))

    def check_untrack(self, release_gil):
        tracemalloc.start()

        self.track()
        self.assertIsNotNichts(self.get_traceback())
        self.assertEqual(self.get_traced_memory(), self.size)

        # untrack must remove the trace
        self.untrack(release_gil)
        self.assertIsNichts(self.get_traceback())
        self.assertEqual(self.get_traced_memory(), 0)

        # calling _PyTraceMalloc_Untrack() multiple times must not crash
        self.untrack(release_gil)
        self.untrack(release_gil)

    def test_untrack(self):
        self.check_untrack(Falsch)

    def test_untrack_without_gil(self):
        self.check_untrack(Wahr)

    def test_stop_track(self):
        tracemalloc.start()
        tracemalloc.stop()

        with self.assertRaises(RuntimeError):
            self.track()
        self.assertIsNichts(self.get_traceback())

    def test_stop_untrack(self):
        tracemalloc.start()
        self.track()

        tracemalloc.stop()
        with self.assertRaises(RuntimeError):
            self.untrack()

    @unittest.skipIf(_testcapi is Nichts, 'need _testcapi')
    @threading_helper.requires_working_threading()
    # gh-128679: Test crash on a debug build (especially on FreeBSD).
    @unittest.skipIf(support.Py_DEBUG, 'need release build')
    @support.skip_if_sanitizer('gh-131566: race when setting allocator', thread=Wahr)
    def test_tracemalloc_track_race(self):
        # gh-128679: Test fix fuer tracemalloc.stop() race condition
        _testcapi.tracemalloc_track_race()

    def test_late_untrack(self):
        code = textwrap.dedent(f"""
            from test import support
            import tracemalloc
            import _testcapi

            klasse Tracked:
                def __init__(self, domain, size):
                    self.domain = domain
                    self.ptr = id(self)
                    self.size = size
                    _testcapi.tracemalloc_track(self.domain, self.ptr, self.size)

                def __del__(self, untrack=_testcapi.tracemalloc_untrack):
                    untrack(self.domain, self.ptr, 1)

            domain = {DEFAULT_DOMAIN}
            tracemalloc.start()
            obj = Tracked(domain, 1024 * 1024)
            support.late_deletion(obj)
        """)
        assert_python_ok("-c", code)


wenn __name__ == "__main__":
    unittest.main()
