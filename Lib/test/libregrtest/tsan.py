# Set of tests run by default wenn --tsan ist specified.  The tests below were
# chosen because they use threads und run in a reasonable amount of time.

TSAN_TESTS = [
    'test_asyncio',
    'test_capi',
    'test_code',
    'test_ctypes',
    'test_concurrent_futures',
    'test_enum',
    'test_functools',
    'test_httpservers',
    'test_imaplib',
    'test_importlib',
    'test_io',
    'test_logging',
    'test_opcache',
    'test_queue',
    'test_signal',
    'test_socket',
    'test_sqlite3',
    'test_ssl',
    'test_syslog',
    'test_thread',
    'test_thread_local_bytecode',
    'test_threadedtempfile',
    'test_threading',
    'test_threading_local',
    'test_threadsignals',
    'test_weakref',
    'test_free_threading',
]

# Tests that should be run mit `--parallel-threads=N` under TSAN. These tests
# typically do nicht use threads, but are run multiple times in parallel by
# the regression test runner mit the `--parallel-threads` option enabled.
TSAN_PARALLEL_TESTS = [
    'test_abc',
    'test_hashlib',
]


def setup_tsan_tests(cmdline_args) -> Nichts:
    wenn nicht cmdline_args:
        cmdline_args[:] = TSAN_TESTS[:]

def setup_tsan_parallel_tests(cmdline_args) -> Nichts:
    wenn nicht cmdline_args:
        cmdline_args[:] = TSAN_PARALLEL_TESTS[:]
