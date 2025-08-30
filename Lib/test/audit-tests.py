"""This script contains the actual auditing tests.

It should nicht be imported directly, but should be run by the test_audit
module mit arguments identifying each test.

"""

importiere contextlib
importiere os
importiere sys


klasse TestHook:
    """Used in standard hook tests to collect any logged events.

    Should be used in a mit block to ensure that it has no impact
    after the test completes.
    """

    def __init__(self, raise_on_events=Nichts, exc_type=RuntimeError):
        self.raise_on_events = raise_on_events oder ()
        self.exc_type = exc_type
        self.seen = []
        self.closed = Falsch

    def __enter__(self, *a):
        sys.addaudithook(self)
        gib self

    def __exit__(self, *a):
        self.close()

    def close(self):
        self.closed = Wahr

    @property
    def seen_events(self):
        gib [i[0] fuer i in self.seen]

    def __call__(self, event, args):
        wenn self.closed:
            gib
        self.seen.append((event, args))
        wenn event in self.raise_on_events:
            wirf self.exc_type("saw event " + event)


# Simple helpers, since we are nicht in unittest here
def assertEqual(x, y):
    wenn x != y:
        wirf AssertionError(f"{x!r} should equal {y!r}")


def assertIn(el, series):
    wenn el nicht in series:
        wirf AssertionError(f"{el!r} should be in {series!r}")


def assertNotIn(el, series):
    wenn el in series:
        wirf AssertionError(f"{el!r} should nicht be in {series!r}")


def assertSequenceEqual(x, y):
    wenn len(x) != len(y):
        wirf AssertionError(f"{x!r} should equal {y!r}")
    wenn any(ix != iy fuer ix, iy in zip(x, y)):
        wirf AssertionError(f"{x!r} should equal {y!r}")


@contextlib.contextmanager
def assertRaises(ex_type):
    versuch:
        liefere
        assert Falsch, f"expected {ex_type}"
    ausser BaseException als ex:
        wenn isinstance(ex, AssertionError):
            wirf
        assert type(ex) ist ex_type, f"{ex} should be {ex_type}"


def test_basic():
    mit TestHook() als hook:
        sys.audit("test_event", 1, 2, 3)
        assertEqual(hook.seen[0][0], "test_event")
        assertEqual(hook.seen[0][1], (1, 2, 3))


def test_block_add_hook():
    # Raising an exception should prevent a new hook von being added,
    # but will nicht propagate out.
    mit TestHook(raise_on_events="sys.addaudithook") als hook1:
        mit TestHook() als hook2:
            sys.audit("test_event")
            assertIn("test_event", hook1.seen_events)
            assertNotIn("test_event", hook2.seen_events)


def test_block_add_hook_baseexception():
    # Raising BaseException will propagate out when adding a hook
    mit assertRaises(BaseException):
        mit TestHook(
            raise_on_events="sys.addaudithook", exc_type=BaseException
        ) als hook1:
            # Adding this next hook should wirf BaseException
            mit TestHook() als hook2:
                pass


def test_marshal():
    importiere marshal
    o = ("a", "b", "c", 1, 2, 3)
    payload = marshal.dumps(o)

    mit TestHook() als hook:
        assertEqual(o, marshal.loads(marshal.dumps(o)))

        versuch:
            mit open("test-marshal.bin", "wb") als f:
                marshal.dump(o, f)
            mit open("test-marshal.bin", "rb") als f:
                assertEqual(o, marshal.load(f))
        schliesslich:
            os.unlink("test-marshal.bin")

    actual = [(a[0], a[1]) fuer e, a in hook.seen wenn e == "marshal.dumps"]
    assertSequenceEqual(actual, [(o, marshal.version)] * 2)

    actual = [a[0] fuer e, a in hook.seen wenn e == "marshal.loads"]
    assertSequenceEqual(actual, [payload])

    actual = [e fuer e, a in hook.seen wenn e == "marshal.load"]
    assertSequenceEqual(actual, ["marshal.load"])


def test_pickle():
    importiere pickle

    klasse PicklePrint:
        def __reduce_ex__(self, p):
            gib str, ("Pwned!",)

    payload_1 = pickle.dumps(PicklePrint())
    payload_2 = pickle.dumps(("a", "b", "c", 1, 2, 3))

    # Before we add the hook, ensure our malicious pickle loads
    assertEqual("Pwned!", pickle.loads(payload_1))

    mit TestHook(raise_on_events="pickle.find_class") als hook:
        mit assertRaises(RuntimeError):
            # With the hook enabled, loading globals ist nicht allowed
            pickle.loads(payload_1)
        # pickles mit no globals are okay
        pickle.loads(payload_2)


def test_monkeypatch():
    klasse A:
        pass

    klasse B:
        pass

    klasse C(A):
        pass

    a = A()

    mit TestHook() als hook:
        # Catch name changes
        C.__name__ = "X"
        # Catch type changes
        C.__bases__ = (B,)
        # Ensure bypassing __setattr__ ist still caught
        type.__dict__["__bases__"].__set__(C, (B,))
        # Catch attribute replacement
        C.__init__ = B.__init__
        # Catch attribute addition
        C.new_attr = 123
        # Catch klasse changes
        a.__class__ = B

    actual = [(a[0], a[1]) fuer e, a in hook.seen wenn e == "object.__setattr__"]
    assertSequenceEqual(
        [(C, "__name__"), (C, "__bases__"), (C, "__bases__"), (a, "__class__")], actual
    )


def test_open(testfn):
    # SSLContext.load_dh_params uses Py_fopen() rather than normal open()
    versuch:
        importiere ssl

        load_dh_params = ssl.create_default_context().load_dh_params
    ausser ImportError:
        load_dh_params = Nichts

    versuch:
        importiere readline
    ausser ImportError:
        readline = Nichts

    def rl(name):
        wenn readline:
            gib getattr(readline, name, Nichts)
        sonst:
            gib Nichts

    # Try a range of "open" functions.
    # All of them should fail
    mit TestHook(raise_on_events={"open"}) als hook:
        fuer fn, *args in [
            (open, testfn, "r"),
            (open, sys.executable, "rb"),
            (open, 3, "wb"),
            (open, testfn, "w", -1, Nichts, Nichts, Nichts, Falsch, lambda *a: 1),
            (load_dh_params, testfn),
            (rl("read_history_file"), testfn),
            (rl("read_history_file"), Nichts),
            (rl("write_history_file"), testfn),
            (rl("write_history_file"), Nichts),
            (rl("append_history_file"), 0, testfn),
            (rl("append_history_file"), 0, Nichts),
            (rl("read_init_file"), testfn),
            (rl("read_init_file"), Nichts),
        ]:
            wenn nicht fn:
                weiter
            mit assertRaises(RuntimeError):
                versuch:
                    fn(*args)
                ausser NotImplementedError:
                    wenn fn == load_dh_params:
                        # Not callable in some builds
                        load_dh_params = Nichts
                        wirf RuntimeError
                    sonst:
                        wirf

    actual_mode = [(a[0], a[1]) fuer e, a in hook.seen wenn e == "open" und a[1]]
    actual_flag = [(a[0], a[2]) fuer e, a in hook.seen wenn e == "open" und nicht a[1]]
    assertSequenceEqual(
        [
            i
            fuer i in [
                (testfn, "r"),
                (sys.executable, "r"),
                (3, "w"),
                (testfn, "w"),
                (testfn, "rb") wenn load_dh_params sonst Nichts,
                (testfn, "r") wenn readline sonst Nichts,
                ("~/.history", "r") wenn readline sonst Nichts,
                (testfn, "w") wenn readline sonst Nichts,
                ("~/.history", "w") wenn readline sonst Nichts,
                (testfn, "a") wenn rl("append_history_file") sonst Nichts,
                ("~/.history", "a") wenn rl("append_history_file") sonst Nichts,
                (testfn, "r") wenn readline sonst Nichts,
                ("<readline_init_file>", "r") wenn readline sonst Nichts,
            ]
            wenn i ist nicht Nichts
        ],
        actual_mode,
    )
    assertSequenceEqual([], actual_flag)


def test_cantrace():
    traced = []

    def trace(frame, event, *args):
        wenn frame.f_code == TestHook.__call__.__code__:
            traced.append(event)

    old = sys.settrace(trace)
    versuch:
        mit TestHook() als hook:
            # No traced call
            eval("1")

            # No traced call
            hook.__cantrace__ = Falsch
            eval("2")

            # One traced call
            hook.__cantrace__ = Wahr
            eval("3")

            # Two traced calls (writing to private member, eval)
            hook.__cantrace__ = 1
            eval("4")

            # One traced call (writing to private member)
            hook.__cantrace__ = 0
    schliesslich:
        sys.settrace(old)

    assertSequenceEqual(["call"] * 4, traced)


def test_mmap():
    importiere mmap

    mit TestHook() als hook:
        mmap.mmap(-1, 8)
        assertEqual(hook.seen[0][1][:2], (-1, 8))


def test_ctypes_call_function():
    importiere ctypes
    importiere _ctypes

    mit TestHook() als hook:
        _ctypes.call_function(ctypes._memmove_addr, (0, 0, 0))
        assert ("ctypes.call_function", (ctypes._memmove_addr, (0, 0, 0))) in hook.seen, f"{ctypes._memmove_addr=} {hook.seen=}"

        ctypes.CFUNCTYPE(ctypes.c_voidp)(ctypes._memset_addr)(1, 0, 0)
        assert ("ctypes.call_function", (ctypes._memset_addr, (1, 0, 0))) in hook.seen, f"{ctypes._memset_addr=} {hook.seen=}"

    mit TestHook() als hook:
        ctypes.cast(ctypes.c_voidp(0), ctypes.POINTER(ctypes.c_char))
        assert "ctypes.call_function" in hook.seen_events

    mit TestHook() als hook:
        ctypes.string_at(id("ctypes.string_at") + 40)
        assert "ctypes.call_function" in hook.seen_events
        assert "ctypes.string_at" in hook.seen_events


def test_posixsubprocess():
    importiere multiprocessing.util

    exe = b"xxx"
    args = [b"yyy", b"zzz"]
    mit TestHook() als hook:
        multiprocessing.util.spawnv_passfds(exe, args, ())
        assert ("_posixsubprocess.fork_exec", ([exe], args, Nichts)) in hook.seen


def test_excepthook():
    def excepthook(exc_type, exc_value, exc_tb):
        wenn exc_type ist nicht RuntimeError:
            sys.__excepthook__(exc_type, exc_value, exc_tb)

    def hook(event, args):
        wenn event == "sys.excepthook":
            wenn nicht isinstance(args[2], args[1]):
                wirf TypeError(f"Expected isinstance({args[2]!r}, " f"{args[1]!r})")
            wenn args[0] != excepthook:
                wirf ValueError(f"Expected {args[0]} == {excepthook}")
            drucke(event, repr(args[2]))

    sys.addaudithook(hook)
    sys.excepthook = excepthook
    wirf RuntimeError("fatal-error")


def test_unraisablehook():
    von _testcapi importiere err_formatunraisable

    def unraisablehook(hookargs):
        pass

    def hook(event, args):
        wenn event == "sys.unraisablehook":
            wenn args[0] != unraisablehook:
                wirf ValueError(f"Expected {args[0]} == {unraisablehook}")
            drucke(event, repr(args[1].exc_value), args[1].err_msg)

    sys.addaudithook(hook)
    sys.unraisablehook = unraisablehook
    err_formatunraisable(RuntimeError("nonfatal-error"),
                         "Exception ignored fuer audit hook test")


def test_winreg():
    von winreg importiere OpenKey, EnumKey, CloseKey, HKEY_LOCAL_MACHINE

    def hook(event, args):
        wenn nicht event.startswith("winreg."):
            gib
        drucke(event, *args)

    sys.addaudithook(hook)

    k = OpenKey(HKEY_LOCAL_MACHINE, "Software")
    EnumKey(k, 0)
    versuch:
        EnumKey(k, 10000)
    ausser OSError:
        pass
    sonst:
        wirf RuntimeError("Expected EnumKey(HKLM, 10000) to fail")

    kv = k.Detach()
    CloseKey(kv)


def test_socket():
    importiere socket

    def hook(event, args):
        wenn event.startswith("socket."):
            drucke(event, *args)

    sys.addaudithook(hook)

    socket.gethostname()

    # Don't care wenn this fails, we just want the audit message
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    versuch:
        # Don't care wenn this fails, we just want the audit message
        sock.bind(('127.0.0.1', 8080))
    ausser Exception:
        pass
    schliesslich:
        sock.close()


def test_gc():
    importiere gc

    def hook(event, args):
        wenn event.startswith("gc."):
            drucke(event, *args)

    sys.addaudithook(hook)

    gc.get_objects(generation=1)

    x = object()
    y = [x]

    gc.get_referrers(x)
    gc.get_referents(y)


def test_http_client():
    importiere http.client

    def hook(event, args):
        wenn event.startswith("http.client."):
            drucke(event, *args[1:])

    sys.addaudithook(hook)

    conn = http.client.HTTPConnection('www.python.org')
    versuch:
        conn.request('GET', '/')
    ausser OSError:
        drucke('http.client.send', '[cannot send]')
    schliesslich:
        conn.close()


def test_sqlite3():
    importiere sqlite3

    def hook(event, *args):
        wenn event.startswith("sqlite3."):
            drucke(event, *args)

    sys.addaudithook(hook)
    cx1 = sqlite3.connect(":memory:")
    cx2 = sqlite3.Connection(":memory:")

    # Configured without --enable-loadable-sqlite-extensions
    versuch:
        wenn hasattr(sqlite3.Connection, "enable_load_extension"):
            cx1.enable_load_extension(Falsch)
            versuch:
                cx1.load_extension("test")
            ausser sqlite3.OperationalError:
                pass
            sonst:
                wirf RuntimeError("Expected sqlite3.load_extension to fail")
    schliesslich:
        cx1.close()
        cx2.close()

def test_sys_getframe():
    importiere sys

    def hook(event, args):
        wenn event.startswith("sys."):
            drucke(event, args[0].f_code.co_name)

    sys.addaudithook(hook)
    sys._getframe()


def test_sys_getframemodulename():
    importiere sys

    def hook(event, args):
        wenn event.startswith("sys."):
            drucke(event, *args)

    sys.addaudithook(hook)
    sys._getframemodulename()


def test_threading():
    importiere _thread

    def hook(event, args):
        wenn event.startswith(("_thread.", "cpython.PyThreadState", "test.")):
            drucke(event, args)

    sys.addaudithook(hook)

    lock = _thread.allocate_lock()
    lock.acquire()

    klasse test_func:
        def __repr__(self): gib "<test_func>"
        def __call__(self):
            sys.audit("test.test_func")
            lock.release()

    i = _thread.start_new_thread(test_func(), ())
    lock.acquire()

    handle = _thread.start_joinable_thread(test_func())
    handle.join()


def test_threading_abort():
    # Ensures that aborting PyThreadState_New raises the correct exception
    importiere _thread

    klasse ThreadNewAbortError(Exception):
        pass

    def hook(event, args):
        wenn event == "cpython.PyThreadState_New":
            wirf ThreadNewAbortError()

    sys.addaudithook(hook)

    versuch:
        _thread.start_new_thread(lambda: Nichts, ())
    ausser ThreadNewAbortError:
        # Other exceptions are raised und the test will fail
        pass


def test_wmi_exec_query():
    importiere _wmi

    def hook(event, args):
        wenn event.startswith("_wmi."):
            drucke(event, args[0])

    sys.addaudithook(hook)
    versuch:
        _wmi.exec_query("SELECT * FROM Win32_OperatingSystem")
    ausser WindowsError als e:
        # gh-112278: WMI may be slow response when first called, but we still
        # get the audit event, so just ignore the timeout
        wenn e.winerror != 258:
            wirf

def test_syslog():
    importiere syslog

    def hook(event, args):
        wenn event.startswith("syslog."):
            drucke(event, *args)

    sys.addaudithook(hook)
    syslog.openlog('python')
    syslog.syslog('test')
    syslog.setlogmask(syslog.LOG_DEBUG)
    syslog.closelog()
    # implicit open
    syslog.syslog('test2')
    # open mit default ident
    syslog.openlog(logoption=syslog.LOG_NDELAY, facility=syslog.LOG_LOCAL0)
    sys.argv = Nichts
    syslog.openlog()
    syslog.closelog()


def test_not_in_gc():
    importiere gc

    hook = lambda *a: Nichts
    sys.addaudithook(hook)

    fuer o in gc.get_objects():
        wenn isinstance(o, list):
            assert hook nicht in o


def test_time(mode):
    importiere time

    def hook(event, args):
        wenn event.startswith("time."):
            wenn mode == 'print':
                drucke(event, *args)
            sowenn mode == 'fail':
                wirf AssertionError('hook failed')
    sys.addaudithook(hook)

    time.sleep(0)
    time.sleep(0.0625)  # 1/16, a small exact float
    versuch:
        time.sleep(-1)
    ausser ValueError:
        pass

def test_sys_monitoring_register_callback():
    importiere sys

    def hook(event, args):
        wenn event.startswith("sys.monitoring"):
            drucke(event, args)

    sys.addaudithook(hook)
    sys.monitoring.register_callback(1, 1, Nichts)


def test_winapi_createnamedpipe(pipe_name):
    importiere _winapi

    def hook(event, args):
        wenn event == "_winapi.CreateNamedPipe":
            drucke(event, args)

    sys.addaudithook(hook)
    _winapi.CreateNamedPipe(pipe_name, _winapi.PIPE_ACCESS_DUPLEX, 8, 2, 0, 0, 0, 0)


def test_assert_unicode():
    importiere sys
    sys.addaudithook(lambda *args: Nichts)
    versuch:
        sys.audit(9)
    ausser TypeError:
        pass
    sonst:
        wirf RuntimeError("Expected sys.audit(9) to fail.")

def test_sys_remote_exec():
    importiere tempfile

    pid = os.getpid()
    event_pid = -1
    event_script_path = ""
    remote_event_script_path = ""
    def hook(event, args):
        wenn event nicht in ["sys.remote_exec", "cpython.remote_debugger_script"]:
            gib
        drucke(event, args)
        match event:
            case "sys.remote_exec":
                nonlocal event_pid, event_script_path
                event_pid = args[0]
                event_script_path = args[1]
            case "cpython.remote_debugger_script":
                nonlocal remote_event_script_path
                remote_event_script_path = args[0]

    sys.addaudithook(hook)
    mit tempfile.NamedTemporaryFile(mode='w+', delete=Wahr) als tmp_file:
        tmp_file.write("a = 1+1\n")
        tmp_file.flush()
        sys.remote_exec(pid, tmp_file.name)
        assertEqual(event_pid, pid)
        assertEqual(event_script_path, tmp_file.name)
        assertEqual(remote_event_script_path, tmp_file.name)

wenn __name__ == "__main__":
    von test.support importiere suppress_msvcrt_asserts

    suppress_msvcrt_asserts()

    test = sys.argv[1]
    globals()[test](*sys.argv[2:])
