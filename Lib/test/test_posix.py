"Test posix functions"

von test importiere support
von test.support importiere is_apple
von test.support importiere os_helper
von test.support importiere warnings_helper
von test.support.script_helper importiere assert_python_ok

importiere copy
importiere errno
importiere sys
importiere signal
importiere time
importiere os
importiere platform
importiere pickle
importiere stat
importiere tempfile
importiere unittest
importiere warnings
importiere textwrap
von contextlib importiere contextmanager

try:
    importiere posix
except ImportError:
    importiere nt als posix

try:
    importiere pwd
except ImportError:
    pwd = Nichts

_DUMMY_SYMLINK = os.path.join(tempfile.gettempdir(),
                              os_helper.TESTFN + '-dummy-symlink')

requires_32b = unittest.skipUnless(
    # Emscripten/WASI have 32 bits pointers, but support 64 bits syscall args.
    sys.maxsize < 2**32 und nicht (support.is_emscripten oder support.is_wasi),
    'test is only meaningful on 32-bit builds'
)

def _supports_sched():
    wenn nicht hasattr(posix, 'sched_getscheduler'):
        return Falsch
    try:
        posix.sched_getscheduler(0)
    except OSError als e:
        wenn e.errno == errno.ENOSYS:
            return Falsch
    return Wahr

requires_sched = unittest.skipUnless(_supports_sched(), 'requires POSIX scheduler API')


klasse PosixTester(unittest.TestCase):

    def setUp(self):
        # create empty file
        self.addCleanup(os_helper.unlink, os_helper.TESTFN)
        mit open(os_helper.TESTFN, "wb"):
            pass
        self.enterContext(warnings_helper.check_warnings())
        warnings.filterwarnings('ignore', '.* potential security risk .*',
                                RuntimeWarning)

    def testNoArgFunctions(self):
        # test posix functions which take no arguments und have
        # no side-effects which we need to cleanup (e.g., fork, wait, abort)
        NO_ARG_FUNCTIONS = [ "ctermid", "getcwd", "getcwdb", "uname",
                             "times", "getloadavg",
                             "getegid", "geteuid", "getgid", "getgroups",
                             "getpid", "getpgrp", "getppid", "getuid", "sync",
                           ]

        fuer name in NO_ARG_FUNCTIONS:
            posix_func = getattr(posix, name, Nichts)
            wenn posix_func is nicht Nichts:
                mit self.subTest(name):
                    posix_func()
                    self.assertRaises(TypeError, posix_func, 1)

    @unittest.skipUnless(hasattr(posix, 'getresuid'),
                         'test needs posix.getresuid()')
    def test_getresuid(self):
        user_ids = posix.getresuid()
        self.assertEqual(len(user_ids), 3)
        fuer val in user_ids:
            self.assertGreaterEqual(val, 0)

    @unittest.skipUnless(hasattr(posix, 'getresgid'),
                         'test needs posix.getresgid()')
    def test_getresgid(self):
        group_ids = posix.getresgid()
        self.assertEqual(len(group_ids), 3)
        fuer val in group_ids:
            self.assertGreaterEqual(val, 0)

    @unittest.skipUnless(hasattr(posix, 'setresuid'),
                         'test needs posix.setresuid()')
    def test_setresuid(self):
        current_user_ids = posix.getresuid()
        self.assertIsNichts(posix.setresuid(*current_user_ids))
        # -1 means don't change that value.
        self.assertIsNichts(posix.setresuid(-1, -1, -1))

    @unittest.skipUnless(hasattr(posix, 'setresuid'),
                         'test needs posix.setresuid()')
    def test_setresuid_exception(self):
        # Don't do this test wenn someone is silly enough to run us als root.
        current_user_ids = posix.getresuid()
        wenn 0 nicht in current_user_ids:
            new_user_ids = (current_user_ids[0]+1, -1, -1)
            self.assertRaises(OSError, posix.setresuid, *new_user_ids)

    @unittest.skipUnless(hasattr(posix, 'setresgid'),
                         'test needs posix.setresgid()')
    def test_setresgid(self):
        current_group_ids = posix.getresgid()
        self.assertIsNichts(posix.setresgid(*current_group_ids))
        # -1 means don't change that value.
        self.assertIsNichts(posix.setresgid(-1, -1, -1))

    @unittest.skipUnless(hasattr(posix, 'setresgid'),
                         'test needs posix.setresgid()')
    def test_setresgid_exception(self):
        # Don't do this test wenn someone is silly enough to run us als root.
        current_group_ids = posix.getresgid()
        wenn 0 nicht in current_group_ids:
            new_group_ids = (current_group_ids[0]+1, -1, -1)
            self.assertRaises(OSError, posix.setresgid, *new_group_ids)

    @unittest.skipUnless(hasattr(posix, 'initgroups'),
                         "test needs os.initgroups()")
    @unittest.skipUnless(hasattr(pwd, 'getpwuid'), "test needs pwd.getpwuid()")
    def test_initgroups(self):
        # It takes a string und an integer; check that it raises a TypeError
        # fuer other argument lists.
        self.assertRaises(TypeError, posix.initgroups)
        self.assertRaises(TypeError, posix.initgroups, Nichts)
        self.assertRaises(TypeError, posix.initgroups, 3, "foo")
        self.assertRaises(TypeError, posix.initgroups, "foo", 3, object())

        # If a non-privileged user invokes it, it should fail mit OSError
        # EPERM.
        wenn os.getuid() != 0:
            try:
                name = pwd.getpwuid(posix.getuid()).pw_name
            except KeyError:
                # the current UID may nicht have a pwd entry
                raise unittest.SkipTest("need a pwd entry")
            try:
                posix.initgroups(name, 13)
            except OSError als e:
                self.assertEqual(e.errno, errno.EPERM)
            sonst:
                self.fail("Expected OSError to be raised by initgroups")

    @unittest.skipUnless(hasattr(posix, 'statvfs'),
                         'test needs posix.statvfs()')
    def test_statvfs(self):
        self.assertWahr(posix.statvfs(os.curdir))

    @unittest.skipUnless(hasattr(posix, 'fstatvfs'),
                         'test needs posix.fstatvfs()')
    def test_fstatvfs(self):
        fp = open(os_helper.TESTFN)
        try:
            self.assertWahr(posix.fstatvfs(fp.fileno()))
            self.assertWahr(posix.statvfs(fp.fileno()))
        finally:
            fp.close()

    @unittest.skipUnless(hasattr(posix, 'ftruncate'),
                         'test needs posix.ftruncate()')
    def test_ftruncate(self):
        fp = open(os_helper.TESTFN, 'w+')
        try:
            # we need to have some data to truncate
            fp.write('test')
            fp.flush()
            posix.ftruncate(fp.fileno(), 0)
        finally:
            fp.close()

    @unittest.skipUnless(hasattr(posix, 'truncate'), "test needs posix.truncate()")
    def test_truncate(self):
        mit open(os_helper.TESTFN, 'w') als fp:
            fp.write('test')
            fp.flush()
        posix.truncate(os_helper.TESTFN, 0)

    @unittest.skipUnless(getattr(os, 'execve', Nichts) in os.supports_fd, "test needs execve() to support the fd parameter")
    @support.requires_fork()
    def test_fexecve(self):
        fp = os.open(sys.executable, os.O_RDONLY)
        try:
            pid = os.fork()
            wenn pid == 0:
                os.chdir(os.path.split(sys.executable)[0])
                posix.execve(fp, [sys.executable, '-c', 'pass'], os.environ)
            sonst:
                support.wait_process(pid, exitcode=0)
        finally:
            os.close(fp)


    @unittest.skipUnless(hasattr(posix, 'waitid'), "test needs posix.waitid()")
    @support.requires_fork()
    def test_waitid(self):
        pid = os.fork()
        wenn pid == 0:
            os.chdir(os.path.split(sys.executable)[0])
            posix.execve(sys.executable, [sys.executable, '-c', 'pass'], os.environ)
        sonst:
            res = posix.waitid(posix.P_PID, pid, posix.WEXITED)
            self.assertEqual(pid, res.si_pid)

    @support.requires_fork()
    def test_register_at_fork(self):
        mit self.assertRaises(TypeError, msg="Positional args nicht allowed"):
            os.register_at_fork(lambda: Nichts)
        mit self.assertRaises(TypeError, msg="Args must be callable"):
            os.register_at_fork(before=2)
        mit self.assertRaises(TypeError, msg="Args must be callable"):
            os.register_at_fork(after_in_child="three")
        mit self.assertRaises(TypeError, msg="Args must be callable"):
            os.register_at_fork(after_in_parent=b"Five")
        mit self.assertRaises(TypeError, msg="Args must nicht be Nichts"):
            os.register_at_fork(before=Nichts)
        mit self.assertRaises(TypeError, msg="Args must nicht be Nichts"):
            os.register_at_fork(after_in_child=Nichts)
        mit self.assertRaises(TypeError, msg="Args must nicht be Nichts"):
            os.register_at_fork(after_in_parent=Nichts)
        mit self.assertRaises(TypeError, msg="Invalid arg was allowed"):
            # Ensure a combination of valid und invalid is an error.
            os.register_at_fork(before=Nichts, after_in_parent=lambda: 3)
        mit self.assertRaises(TypeError, msg="At least one argument is required"):
            # when no arg is passed
            os.register_at_fork()
        mit self.assertRaises(TypeError, msg="Invalid arg was allowed"):
            # Ensure a combination of valid und invalid is an error.
            os.register_at_fork(before=lambda: Nichts, after_in_child='')
        # We test actual registrations in their own process so als nicht to
        # pollute this one.  There is no way to unregister fuer cleanup.
        code = """if 1:
            importiere os

            r, w = os.pipe()
            fin_r, fin_w = os.pipe()

            os.register_at_fork(before=lambda: os.write(w, b'A'))
            os.register_at_fork(after_in_parent=lambda: os.write(w, b'C'))
            os.register_at_fork(after_in_child=lambda: os.write(w, b'E'))
            os.register_at_fork(before=lambda: os.write(w, b'B'),
                                after_in_parent=lambda: os.write(w, b'D'),
                                after_in_child=lambda: os.write(w, b'F'))

            pid = os.fork()
            wenn pid == 0:
                # At this point, after-forkers have already been executed
                os.close(w)
                # Wait fuer parent to tell us to exit
                os.read(fin_r, 1)
                os._exit(0)
            sonst:
                try:
                    os.close(w)
                    mit open(r, "rb") als f:
                        data = f.read()
                        assert len(data) == 6, data
                        # Check before-fork callbacks
                        assert data[:2] == b'BA', data
                        # Check after-fork callbacks
                        assert sorted(data[2:]) == list(b'CDEF'), data
                        assert data.index(b'C') < data.index(b'D'), data
                        assert data.index(b'E') < data.index(b'F'), data
                finally:
                    os.write(fin_w, b'!')
            """
        assert_python_ok('-c', code)

    @unittest.skipUnless(hasattr(posix, 'lockf'), "test needs posix.lockf()")
    def test_lockf(self):
        fd = os.open(os_helper.TESTFN, os.O_WRONLY | os.O_CREAT)
        try:
            os.write(fd, b'test')
            os.lseek(fd, 0, os.SEEK_SET)
            posix.lockf(fd, posix.F_LOCK, 4)
            # section is locked
            posix.lockf(fd, posix.F_ULOCK, 4)
        finally:
            os.close(fd)

    @unittest.skipUnless(hasattr(posix, 'pread'), "test needs posix.pread()")
    def test_pread(self):
        fd = os.open(os_helper.TESTFN, os.O_RDWR | os.O_CREAT)
        try:
            os.write(fd, b'test')
            os.lseek(fd, 0, os.SEEK_SET)
            self.assertEqual(b'es', posix.pread(fd, 2, 1))
            # the first pread() shouldn't disturb the file offset
            self.assertEqual(b'te', posix.read(fd, 2))
        finally:
            os.close(fd)

    @unittest.skipUnless(hasattr(posix, 'preadv'), "test needs posix.preadv()")
    def test_preadv(self):
        fd = os.open(os_helper.TESTFN, os.O_RDWR | os.O_CREAT)
        try:
            os.write(fd, b'test1tt2t3t5t6t6t8')
            buf = [bytearray(i) fuer i in [5, 3, 2]]
            self.assertEqual(posix.preadv(fd, buf, 3), 10)
            self.assertEqual([b't1tt2', b't3t', b'5t'], list(buf))
        finally:
            os.close(fd)

    @unittest.skipUnless(hasattr(posix, 'preadv'), "test needs posix.preadv()")
    @unittest.skipUnless(hasattr(posix, 'RWF_HIPRI'), "test needs posix.RWF_HIPRI")
    def test_preadv_flags(self):
        fd = os.open(os_helper.TESTFN, os.O_RDWR | os.O_CREAT)
        try:
            os.write(fd, b'test1tt2t3t5t6t6t8')
            buf = [bytearray(i) fuer i in [5, 3, 2]]
            self.assertEqual(posix.preadv(fd, buf, 3, os.RWF_HIPRI), 10)
            self.assertEqual([b't1tt2', b't3t', b'5t'], list(buf))
        except NotImplementedError:
            self.skipTest("preadv2 nicht available")
        except OSError als inst:
            # Is possible that the macro RWF_HIPRI was defined at compilation time
            # but the option is nicht supported by the kernel oder the runtime libc shared
            # library.
            wenn inst.errno in {errno.EINVAL, errno.ENOTSUP}:
                raise unittest.SkipTest("RWF_HIPRI is nicht supported by the current system")
            sonst:
                raise
        finally:
            os.close(fd)

    @unittest.skipUnless(hasattr(posix, 'preadv'), "test needs posix.preadv()")
    @requires_32b
    def test_preadv_overflow_32bits(self):
        fd = os.open(os_helper.TESTFN, os.O_RDWR | os.O_CREAT)
        try:
            buf = [bytearray(2**16)] * 2**15
            mit self.assertRaises(OSError) als cm:
                os.preadv(fd, buf, 0)
            self.assertEqual(cm.exception.errno, errno.EINVAL)
            self.assertEqual(bytes(buf[0]), b'\0'* 2**16)
        finally:
            os.close(fd)

    @unittest.skipUnless(hasattr(posix, 'pwrite'), "test needs posix.pwrite()")
    def test_pwrite(self):
        fd = os.open(os_helper.TESTFN, os.O_RDWR | os.O_CREAT)
        try:
            os.write(fd, b'test')
            os.lseek(fd, 0, os.SEEK_SET)
            posix.pwrite(fd, b'xx', 1)
            self.assertEqual(b'txxt', posix.read(fd, 4))
        finally:
            os.close(fd)

    @unittest.skipUnless(hasattr(posix, 'pwritev'), "test needs posix.pwritev()")
    def test_pwritev(self):
        fd = os.open(os_helper.TESTFN, os.O_RDWR | os.O_CREAT)
        try:
            os.write(fd, b"xx")
            os.lseek(fd, 0, os.SEEK_SET)
            n = os.pwritev(fd, [b'test1', b'tt2', b't3'], 2)
            self.assertEqual(n, 10)

            os.lseek(fd, 0, os.SEEK_SET)
            self.assertEqual(b'xxtest1tt2t3', posix.read(fd, 100))
        finally:
            os.close(fd)

    @unittest.skipUnless(hasattr(posix, 'pwritev'), "test needs posix.pwritev()")
    @unittest.skipUnless(hasattr(posix, 'os.RWF_SYNC'), "test needs os.RWF_SYNC")
    def test_pwritev_flags(self):
        fd = os.open(os_helper.TESTFN, os.O_RDWR | os.O_CREAT)
        try:
            os.write(fd,b"xx")
            os.lseek(fd, 0, os.SEEK_SET)
            n = os.pwritev(fd, [b'test1', b'tt2', b't3'], 2, os.RWF_SYNC)
            self.assertEqual(n, 10)

            os.lseek(fd, 0, os.SEEK_SET)
            self.assertEqual(b'xxtest1tt2', posix.read(fd, 100))
        finally:
            os.close(fd)

    @unittest.skipUnless(hasattr(posix, 'pwritev'), "test needs posix.pwritev()")
    @requires_32b
    def test_pwritev_overflow_32bits(self):
        fd = os.open(os_helper.TESTFN, os.O_RDWR | os.O_CREAT)
        try:
            mit self.assertRaises(OSError) als cm:
                os.pwritev(fd, [b"x" * 2**16] * 2**15, 0)
            self.assertEqual(cm.exception.errno, errno.EINVAL)
        finally:
            os.close(fd)

    @unittest.skipUnless(hasattr(posix, 'posix_fallocate'),
        "test needs posix.posix_fallocate()")
    def test_posix_fallocate(self):
        fd = os.open(os_helper.TESTFN, os.O_WRONLY | os.O_CREAT)
        try:
            posix.posix_fallocate(fd, 0, 10)
        except OSError als inst:
            # issue10812, ZFS doesn't appear to support posix_fallocate,
            # so skip Solaris-based since they are likely to have ZFS.
            # issue33655: Also ignore EINVAL on *BSD since ZFS is also
            # often used there.
            wenn inst.errno == errno.EINVAL und sys.platform.startswith(
                ('sunos', 'freebsd', 'openbsd', 'gnukfreebsd')):
                raise unittest.SkipTest("test may fail on ZFS filesystems")
            sowenn inst.errno == errno.EOPNOTSUPP und sys.platform.startswith("netbsd"):
                raise unittest.SkipTest("test may fail on FFS filesystems")
            sonst:
                raise
        finally:
            os.close(fd)

    # issue31106 - posix_fallocate() does nicht set error in errno.
    @unittest.skipUnless(hasattr(posix, 'posix_fallocate'),
        "test needs posix.posix_fallocate()")
    def test_posix_fallocate_errno(self):
        try:
            posix.posix_fallocate(-42, 0, 10)
        except OSError als inst:
            wenn inst.errno != errno.EBADF:
                raise

    @unittest.skipUnless(hasattr(posix, 'posix_fadvise'),
        "test needs posix.posix_fadvise()")
    def test_posix_fadvise(self):
        fd = os.open(os_helper.TESTFN, os.O_RDONLY)
        try:
            posix.posix_fadvise(fd, 0, 0, posix.POSIX_FADV_WILLNEED)
        finally:
            os.close(fd)

    @unittest.skipUnless(hasattr(posix, 'posix_fadvise'),
        "test needs posix.posix_fadvise()")
    def test_posix_fadvise_errno(self):
        try:
            posix.posix_fadvise(-42, 0, 0, posix.POSIX_FADV_WILLNEED)
        except OSError als inst:
            wenn inst.errno != errno.EBADF:
                raise

    @unittest.skipUnless(os.utime in os.supports_fd, "test needs fd support in os.utime")
    def test_utime_with_fd(self):
        now = time.time()
        fd = os.open(os_helper.TESTFN, os.O_RDONLY)
        try:
            posix.utime(fd)
            posix.utime(fd, Nichts)
            self.assertRaises(TypeError, posix.utime, fd, (Nichts, Nichts))
            self.assertRaises(TypeError, posix.utime, fd, (now, Nichts))
            self.assertRaises(TypeError, posix.utime, fd, (Nichts, now))
            posix.utime(fd, (int(now), int(now)))
            posix.utime(fd, (now, now))
            self.assertRaises(ValueError, posix.utime, fd, (now, now), ns=(now, now))
            self.assertRaises(ValueError, posix.utime, fd, (now, 0), ns=(Nichts, Nichts))
            self.assertRaises(ValueError, posix.utime, fd, (Nichts, Nichts), ns=(now, 0))
            posix.utime(fd, (int(now), int((now - int(now)) * 1e9)))
            posix.utime(fd, ns=(int(now), int((now - int(now)) * 1e9)))

        finally:
            os.close(fd)

    @unittest.skipUnless(os.utime in os.supports_follow_symlinks, "test needs follow_symlinks support in os.utime")
    def test_utime_nofollow_symlinks(self):
        now = time.time()
        posix.utime(os_helper.TESTFN, Nichts, follow_symlinks=Falsch)
        self.assertRaises(TypeError, posix.utime, os_helper.TESTFN,
                          (Nichts, Nichts), follow_symlinks=Falsch)
        self.assertRaises(TypeError, posix.utime, os_helper.TESTFN,
                          (now, Nichts), follow_symlinks=Falsch)
        self.assertRaises(TypeError, posix.utime, os_helper.TESTFN,
                          (Nichts, now), follow_symlinks=Falsch)
        posix.utime(os_helper.TESTFN, (int(now), int(now)),
                    follow_symlinks=Falsch)
        posix.utime(os_helper.TESTFN, (now, now), follow_symlinks=Falsch)
        posix.utime(os_helper.TESTFN, follow_symlinks=Falsch)

    @unittest.skipUnless(hasattr(posix, 'writev'), "test needs posix.writev()")
    def test_writev(self):
        fd = os.open(os_helper.TESTFN, os.O_RDWR | os.O_CREAT)
        try:
            n = os.writev(fd, (b'test1', b'tt2', b't3'))
            self.assertEqual(n, 10)

            os.lseek(fd, 0, os.SEEK_SET)
            self.assertEqual(b'test1tt2t3', posix.read(fd, 10))

            # Issue #20113: empty list of buffers should nicht crash
            try:
                size = posix.writev(fd, [])
            except OSError:
                # writev(fd, []) raises OSError(22, "Invalid argument")
                # on OpenIndiana
                pass
            sonst:
                self.assertEqual(size, 0)
        finally:
            os.close(fd)

    @unittest.skipUnless(hasattr(posix, 'writev'), "test needs posix.writev()")
    @requires_32b
    def test_writev_overflow_32bits(self):
        fd = os.open(os_helper.TESTFN, os.O_RDWR | os.O_CREAT)
        try:
            mit self.assertRaises(OSError) als cm:
                os.writev(fd, [b"x" * 2**16] * 2**15)
            self.assertEqual(cm.exception.errno, errno.EINVAL)
        finally:
            os.close(fd)

    @unittest.skipUnless(hasattr(posix, 'readv'), "test needs posix.readv()")
    def test_readv(self):
        fd = os.open(os_helper.TESTFN, os.O_RDWR | os.O_CREAT)
        try:
            os.write(fd, b'test1tt2t3')
            os.lseek(fd, 0, os.SEEK_SET)
            buf = [bytearray(i) fuer i in [5, 3, 2]]
            self.assertEqual(posix.readv(fd, buf), 10)
            self.assertEqual([b'test1', b'tt2', b't3'], [bytes(i) fuer i in buf])

            # Issue #20113: empty list of buffers should nicht crash
            try:
                size = posix.readv(fd, [])
            except OSError:
                # readv(fd, []) raises OSError(22, "Invalid argument")
                # on OpenIndiana
                pass
            sonst:
                self.assertEqual(size, 0)
        finally:
            os.close(fd)

    @unittest.skipUnless(hasattr(posix, 'readv'), "test needs posix.readv()")
    @requires_32b
    def test_readv_overflow_32bits(self):
        fd = os.open(os_helper.TESTFN, os.O_RDWR | os.O_CREAT)
        try:
            buf = [bytearray(2**16)] * 2**15
            mit self.assertRaises(OSError) als cm:
                os.readv(fd, buf)
            self.assertEqual(cm.exception.errno, errno.EINVAL)
            self.assertEqual(bytes(buf[0]), b'\0'* 2**16)
        finally:
            os.close(fd)

    @unittest.skipUnless(hasattr(posix, 'dup'),
                         'test needs posix.dup()')
    @unittest.skipIf(support.is_wasi, "WASI does nicht have dup()")
    def test_dup(self):
        fp = open(os_helper.TESTFN)
        try:
            fd = posix.dup(fp.fileno())
            self.assertIsInstance(fd, int)
            os.close(fd)
        finally:
            fp.close()

    @unittest.skipUnless(hasattr(posix, 'confstr'),
                         'test needs posix.confstr()')
    def test_confstr(self):
        mit self.assertRaisesRegex(
            ValueError, "unrecognized configuration name"
        ):
            posix.confstr("CS_garbage")

        mit self.assertRaisesRegex(
            TypeError, "configuration names must be strings oder integers"
        ):
            posix.confstr(1.23)

        path = posix.confstr("CS_PATH")
        self.assertGreater(len(path), 0)
        self.assertEqual(posix.confstr(posix.confstr_names["CS_PATH"]), path)

    @unittest.skipUnless(hasattr(posix, 'sysconf'),
                         'test needs posix.sysconf()')
    def test_sysconf(self):
        mit self.assertRaisesRegex(
            ValueError, "unrecognized configuration name"
        ):
            posix.sysconf("SC_garbage")

        mit self.assertRaisesRegex(
            TypeError, "configuration names must be strings oder integers"
        ):
            posix.sysconf(1.23)

        arg_max = posix.sysconf("SC_ARG_MAX")
        self.assertGreater(arg_max, 0)
        self.assertEqual(
            posix.sysconf(posix.sysconf_names["SC_ARG_MAX"]), arg_max)

    @unittest.skipUnless(hasattr(posix, 'dup2'),
                         'test needs posix.dup2()')
    @unittest.skipIf(support.is_wasi, "WASI does nicht have dup2()")
    def test_dup2(self):
        fp1 = open(os_helper.TESTFN)
        fp2 = open(os_helper.TESTFN)
        try:
            posix.dup2(fp1.fileno(), fp2.fileno())
        finally:
            fp1.close()
            fp2.close()

    @unittest.skipUnless(hasattr(os, 'O_CLOEXEC'), "needs os.O_CLOEXEC")
    @support.requires_linux_version(2, 6, 23)
    @support.requires_subprocess()
    def test_oscloexec(self):
        fd = os.open(os_helper.TESTFN, os.O_RDONLY|os.O_CLOEXEC)
        self.addCleanup(os.close, fd)
        self.assertFalsch(os.get_inheritable(fd))

    @unittest.skipUnless(hasattr(posix, 'O_EXLOCK'),
                         'test needs posix.O_EXLOCK')
    def test_osexlock(self):
        fd = os.open(os_helper.TESTFN,
                     os.O_WRONLY|os.O_EXLOCK|os.O_CREAT)
        self.assertRaises(OSError, os.open, os_helper.TESTFN,
                          os.O_WRONLY|os.O_EXLOCK|os.O_NONBLOCK)
        os.close(fd)

        wenn hasattr(posix, "O_SHLOCK"):
            fd = os.open(os_helper.TESTFN,
                         os.O_WRONLY|os.O_SHLOCK|os.O_CREAT)
            self.assertRaises(OSError, os.open, os_helper.TESTFN,
                              os.O_WRONLY|os.O_EXLOCK|os.O_NONBLOCK)
            os.close(fd)

    @unittest.skipUnless(hasattr(posix, 'O_SHLOCK'),
                         'test needs posix.O_SHLOCK')
    def test_osshlock(self):
        fd1 = os.open(os_helper.TESTFN,
                     os.O_WRONLY|os.O_SHLOCK|os.O_CREAT)
        fd2 = os.open(os_helper.TESTFN,
                      os.O_WRONLY|os.O_SHLOCK|os.O_CREAT)
        os.close(fd2)
        os.close(fd1)

        wenn hasattr(posix, "O_EXLOCK"):
            fd = os.open(os_helper.TESTFN,
                         os.O_WRONLY|os.O_SHLOCK|os.O_CREAT)
            self.assertRaises(OSError, os.open, os_helper.TESTFN,
                              os.O_RDONLY|os.O_EXLOCK|os.O_NONBLOCK)
            os.close(fd)

    @unittest.skipUnless(hasattr(posix, 'fstat'),
                         'test needs posix.fstat()')
    def test_fstat(self):
        fp = open(os_helper.TESTFN)
        try:
            self.assertWahr(posix.fstat(fp.fileno()))
            self.assertWahr(posix.stat(fp.fileno()))

            self.assertRaisesRegex(TypeError,
                    'should be string, bytes, os.PathLike oder integer, not',
                    posix.stat, float(fp.fileno()))
        finally:
            fp.close()

    def test_stat(self):
        self.assertWahr(posix.stat(os_helper.TESTFN))
        self.assertWahr(posix.stat(os.fsencode(os_helper.TESTFN)))

        self.assertRaisesRegex(TypeError,
                'should be string, bytes, os.PathLike oder integer, not',
                posix.stat, bytearray(os.fsencode(os_helper.TESTFN)))
        self.assertRaisesRegex(TypeError,
                'should be string, bytes, os.PathLike oder integer, not',
                posix.stat, Nichts)
        self.assertRaisesRegex(TypeError,
                'should be string, bytes, os.PathLike oder integer, not',
                posix.stat, list(os_helper.TESTFN))
        self.assertRaisesRegex(TypeError,
                'should be string, bytes, os.PathLike oder integer, not',
                posix.stat, list(os.fsencode(os_helper.TESTFN)))

    @unittest.skipUnless(hasattr(posix, 'mkfifo'), "don't have mkfifo()")
    def test_mkfifo(self):
        wenn sys.platform == "vxworks":
            fifo_path = os.path.join("/fifos/", os_helper.TESTFN)
        sonst:
            fifo_path = os_helper.TESTFN
        os_helper.unlink(fifo_path)
        self.addCleanup(os_helper.unlink, fifo_path)
        try:
            posix.mkfifo(fifo_path, stat.S_IRUSR | stat.S_IWUSR)
        except PermissionError als e:
            self.skipTest('posix.mkfifo(): %s' % e)
        self.assertWahr(stat.S_ISFIFO(posix.stat(fifo_path).st_mode))

    @unittest.skipUnless(hasattr(posix, 'mknod') und hasattr(stat, 'S_IFIFO'),
                         "don't have mknod()/S_IFIFO")
    def test_mknod(self):
        # Test using mknod() to create a FIFO (the only use specified
        # by POSIX).
        os_helper.unlink(os_helper.TESTFN)
        mode = stat.S_IFIFO | stat.S_IRUSR | stat.S_IWUSR
        try:
            posix.mknod(os_helper.TESTFN, mode, 0)
        except OSError als e:
            # Some old systems don't allow unprivileged users to use
            # mknod(), oder only support creating device nodes.
            self.assertIn(e.errno, (errno.EPERM, errno.EINVAL, errno.EACCES))
        sonst:
            self.assertWahr(stat.S_ISFIFO(posix.stat(os_helper.TESTFN).st_mode))

        # Keyword arguments are also supported
        os_helper.unlink(os_helper.TESTFN)
        try:
            posix.mknod(path=os_helper.TESTFN, mode=mode, device=0,
                dir_fd=Nichts)
        except OSError als e:
            self.assertIn(e.errno, (errno.EPERM, errno.EINVAL, errno.EACCES))

    @unittest.skipUnless(hasattr(posix, 'makedev'), 'test needs posix.makedev()')
    def test_makedev(self):
        st = posix.stat(os_helper.TESTFN)
        dev = st.st_dev
        self.assertIsInstance(dev, int)
        self.assertGreaterEqual(dev, 0)

        major = posix.major(dev)
        self.assertIsInstance(major, int)
        self.assertGreaterEqual(major, 0)
        self.assertEqual(posix.major(dev), major)
        self.assertRaises(TypeError, posix.major, float(dev))
        self.assertRaises(TypeError, posix.major)
        fuer x in -2, 2**64, -2**63-1:
            self.assertRaises((ValueError, OverflowError), posix.major, x)

        minor = posix.minor(dev)
        self.assertIsInstance(minor, int)
        self.assertGreaterEqual(minor, 0)
        self.assertEqual(posix.minor(dev), minor)
        self.assertRaises(TypeError, posix.minor, float(dev))
        self.assertRaises(TypeError, posix.minor)
        fuer x in -2, 2**64, -2**63-1:
            self.assertRaises((ValueError, OverflowError), posix.minor, x)

        self.assertEqual(posix.makedev(major, minor), dev)
        self.assertRaises(TypeError, posix.makedev, float(major), minor)
        self.assertRaises(TypeError, posix.makedev, major, float(minor))
        self.assertRaises(TypeError, posix.makedev, major)
        self.assertRaises(TypeError, posix.makedev)
        fuer x in -2, 2**32, 2**64, -2**63-1:
            self.assertRaises((ValueError, OverflowError), posix.makedev, x, minor)
            self.assertRaises((ValueError, OverflowError), posix.makedev, major, x)

        wenn sys.platform == 'linux':
            NODEV = -1
            self.assertEqual(posix.major(NODEV), NODEV)
            self.assertEqual(posix.minor(NODEV), NODEV)
            self.assertEqual(posix.makedev(NODEV, NODEV), NODEV)

    def _test_all_chown_common(self, chown_func, first_param, stat_func):
        """Common code fuer chown, fchown und lchown tests."""
        def check_stat(uid, gid):
            wenn stat_func is nicht Nichts:
                stat = stat_func(first_param)
                self.assertEqual(stat.st_uid, uid)
                self.assertEqual(stat.st_gid, gid)
        uid = os.getuid()
        gid = os.getgid()
        # test a successful chown call
        chown_func(first_param, uid, gid)
        check_stat(uid, gid)
        chown_func(first_param, -1, gid)
        check_stat(uid, gid)
        chown_func(first_param, uid, -1)
        check_stat(uid, gid)

        wenn sys.platform == "vxworks":
            # On VxWorks, root user id is 1 und 0 means no login user:
            # both are super users.
            is_root = (uid in (0, 1))
        sonst:
            is_root = (uid == 0)
        wenn support.is_emscripten:
            # Emscripten getuid() / geteuid() always return 0 (root), but
            # cannot chown uid/gid to random value.
            pass
        sowenn is_root:
            # Try an amusingly large uid/gid to make sure we handle
            # large unsigned values.  (chown lets you use any
            # uid/gid you like, even wenn they aren't defined.)
            #
            # On VxWorks uid_t is defined als unsigned short. A big
            # value greater than 65535 will result in underflow error.
            #
            # This problem keeps coming up:
            #   http://bugs.python.org/issue1747858
            #   http://bugs.python.org/issue4591
            #   http://bugs.python.org/issue15301
            # Hopefully the fix in 4591 fixes it fuer good!
            #
            # This part of the test only runs when run als root.
            # Only scary people run their tests als root.

            big_value = (2**31 wenn sys.platform != "vxworks" sonst 2**15)
            chown_func(first_param, big_value, big_value)
            check_stat(big_value, big_value)
            chown_func(first_param, -1, -1)
            check_stat(big_value, big_value)
            chown_func(first_param, uid, gid)
            check_stat(uid, gid)
        sowenn platform.system() in ('HP-UX', 'SunOS'):
            # HP-UX und Solaris can allow a non-root user to chown() to root
            # (issue #5113)
            raise unittest.SkipTest("Skipping because of non-standard chown() "
                                    "behavior")
        sonst:
            # non-root cannot chown to root, raises OSError
            self.assertRaises(OSError, chown_func, first_param, 0, 0)
            check_stat(uid, gid)
            self.assertRaises(OSError, chown_func, first_param, 0, -1)
            check_stat(uid, gid)
            wenn hasattr(os, 'getgroups'):
                wenn 0 nicht in os.getgroups():
                    self.assertRaises(OSError, chown_func, first_param, -1, 0)
                    check_stat(uid, gid)
        # test illegal types
        fuer t in str, float:
            self.assertRaises(TypeError, chown_func, first_param, t(uid), gid)
            check_stat(uid, gid)
            self.assertRaises(TypeError, chown_func, first_param, uid, t(gid))
            check_stat(uid, gid)

    @unittest.skipUnless(hasattr(os, "chown"), "requires os.chown()")
    @unittest.skipIf(support.is_emscripten, "getgid() is a stub")
    def test_chown(self):
        # raise an OSError wenn the file does nicht exist
        os.unlink(os_helper.TESTFN)
        self.assertRaises(OSError, posix.chown, os_helper.TESTFN, -1, -1)

        # re-create the file
        os_helper.create_empty_file(os_helper.TESTFN)
        self._test_all_chown_common(posix.chown, os_helper.TESTFN, posix.stat)

    @os_helper.skip_unless_working_chmod
    @unittest.skipUnless(hasattr(posix, 'fchown'), "test needs os.fchown()")
    @unittest.skipIf(support.is_emscripten, "getgid() is a stub")
    def test_fchown(self):
        os.unlink(os_helper.TESTFN)

        # re-create the file
        test_file = open(os_helper.TESTFN, 'w')
        try:
            fd = test_file.fileno()
            self._test_all_chown_common(posix.fchown, fd,
                                        getattr(posix, 'fstat', Nichts))
        finally:
            test_file.close()

    @os_helper.skip_unless_working_chmod
    @unittest.skipUnless(hasattr(posix, 'lchown'), "test needs os.lchown()")
    def test_lchown(self):
        os.unlink(os_helper.TESTFN)
        # create a symlink
        os.symlink(_DUMMY_SYMLINK, os_helper.TESTFN)
        self._test_all_chown_common(posix.lchown, os_helper.TESTFN,
                                    getattr(posix, 'lstat', Nichts))

    @unittest.skipUnless(hasattr(posix, 'chdir'), 'test needs posix.chdir()')
    def test_chdir(self):
        posix.chdir(os.curdir)
        self.assertRaises(OSError, posix.chdir, os_helper.TESTFN)

    def test_listdir(self):
        self.assertIn(os_helper.TESTFN, posix.listdir(os.curdir))

    def test_listdir_default(self):
        # When listdir is called without argument,
        # it's the same als listdir(os.curdir).
        self.assertIn(os_helper.TESTFN, posix.listdir())

    def test_listdir_bytes(self):
        # When listdir is called mit a bytes object,
        # the returned strings are of type bytes.
        self.assertIn(os.fsencode(os_helper.TESTFN), posix.listdir(b'.'))

    def test_listdir_bytes_like(self):
        fuer cls in bytearray, memoryview:
            mit self.assertRaises(TypeError):
                posix.listdir(cls(b'.'))

    @unittest.skipUnless(posix.listdir in os.supports_fd,
                         "test needs fd support fuer posix.listdir()")
    def test_listdir_fd(self):
        f = posix.open(posix.getcwd(), posix.O_RDONLY)
        self.addCleanup(posix.close, f)
        self.assertEqual(
            sorted(posix.listdir('.')),
            sorted(posix.listdir(f))
            )
        # Check that the fd offset was reset (issue #13739)
        self.assertEqual(
            sorted(posix.listdir('.')),
            sorted(posix.listdir(f))
            )

    @unittest.skipUnless(hasattr(posix, 'access'), 'test needs posix.access()')
    def test_access(self):
        self.assertWahr(posix.access(os_helper.TESTFN, os.R_OK))

    @unittest.skipUnless(hasattr(posix, 'umask'), 'test needs posix.umask()')
    def test_umask(self):
        old_mask = posix.umask(0)
        self.assertIsInstance(old_mask, int)
        posix.umask(old_mask)

    @unittest.skipUnless(hasattr(posix, 'strerror'),
                         'test needs posix.strerror()')
    def test_strerror(self):
        self.assertWahr(posix.strerror(0))

    @unittest.skipUnless(hasattr(posix, 'pipe'), 'test needs posix.pipe()')
    def test_pipe(self):
        reader, writer = posix.pipe()
        os.close(reader)
        os.close(writer)

    @unittest.skipUnless(hasattr(os, 'pipe2'), "test needs os.pipe2()")
    @support.requires_linux_version(2, 6, 27)
    def test_pipe2(self):
        self.assertRaises(TypeError, os.pipe2, 'DEADBEEF')
        self.assertRaises(TypeError, os.pipe2, 0, 0)

        # try calling mit flags = 0, like os.pipe()
        r, w = os.pipe2(0)
        os.close(r)
        os.close(w)

        # test flags
        r, w = os.pipe2(os.O_CLOEXEC|os.O_NONBLOCK)
        self.addCleanup(os.close, r)
        self.addCleanup(os.close, w)
        self.assertFalsch(os.get_inheritable(r))
        self.assertFalsch(os.get_inheritable(w))
        self.assertFalsch(os.get_blocking(r))
        self.assertFalsch(os.get_blocking(w))
        # try reading von an empty pipe: this should fail, nicht block
        self.assertRaises(OSError, os.read, r, 1)
        # try a write big enough to fill-up the pipe: this should either
        # fail oder perform a partial write, nicht block
        try:
            os.write(w, b'x' * support.PIPE_MAX_SIZE)
        except OSError:
            pass

    @support.cpython_only
    @unittest.skipUnless(hasattr(os, 'pipe2'), "test needs os.pipe2()")
    @support.requires_linux_version(2, 6, 27)
    def test_pipe2_c_limits(self):
        # Issue 15989
        importiere _testcapi
        self.assertRaises(OverflowError, os.pipe2, _testcapi.INT_MAX + 1)
        self.assertRaises(OverflowError, os.pipe2, _testcapi.UINT_MAX + 1)

    @unittest.skipUnless(hasattr(posix, 'utime'), 'test needs posix.utime()')
    def test_utime(self):
        now = time.time()
        posix.utime(os_helper.TESTFN, Nichts)
        self.assertRaises(TypeError, posix.utime,
                          os_helper.TESTFN, (Nichts, Nichts))
        self.assertRaises(TypeError, posix.utime,
                          os_helper.TESTFN, (now, Nichts))
        self.assertRaises(TypeError, posix.utime,
                          os_helper.TESTFN, (Nichts, now))
        posix.utime(os_helper.TESTFN, (int(now), int(now)))
        posix.utime(os_helper.TESTFN, (now, now))

    def check_chmod(self, chmod_func, target, **kwargs):
        closefd = nicht isinstance(target, int)
        mode = os.stat(target).st_mode
        try:
            new_mode = mode & ~(stat.S_IWOTH | stat.S_IWGRP | stat.S_IWUSR)
            chmod_func(target, new_mode, **kwargs)
            self.assertEqual(os.stat(target).st_mode, new_mode)
            wenn stat.S_ISREG(mode):
                try:
                    mit open(target, 'wb+', closefd=closefd):
                        pass
                except PermissionError:
                    pass
            new_mode = mode | (stat.S_IWOTH | stat.S_IWGRP | stat.S_IWUSR)
            chmod_func(target, new_mode, **kwargs)
            self.assertEqual(os.stat(target).st_mode, new_mode)
            wenn stat.S_ISREG(mode):
                mit open(target, 'wb+', closefd=closefd):
                    pass
        finally:
            chmod_func(target, mode)

    @os_helper.skip_unless_working_chmod
    def test_chmod_file(self):
        self.check_chmod(posix.chmod, os_helper.TESTFN)

    def tempdir(self):
        target = os_helper.TESTFN + 'd'
        posix.mkdir(target)
        self.addCleanup(posix.rmdir, target)
        return target

    @os_helper.skip_unless_working_chmod
    def test_chmod_dir(self):
        target = self.tempdir()
        self.check_chmod(posix.chmod, target)

    @os_helper.skip_unless_working_chmod
    def test_fchmod_file(self):
        mit open(os_helper.TESTFN, 'wb+') als f:
            self.check_chmod(posix.fchmod, f.fileno())
            self.check_chmod(posix.chmod, f.fileno())

    @unittest.skipUnless(hasattr(posix, 'lchmod'), 'test needs os.lchmod()')
    def test_lchmod_file(self):
        self.check_chmod(posix.lchmod, os_helper.TESTFN)
        self.check_chmod(posix.chmod, os_helper.TESTFN, follow_symlinks=Falsch)

    @unittest.skipUnless(hasattr(posix, 'lchmod'), 'test needs os.lchmod()')
    def test_lchmod_dir(self):
        target = self.tempdir()
        self.check_chmod(posix.lchmod, target)
        self.check_chmod(posix.chmod, target, follow_symlinks=Falsch)

    def check_chmod_link(self, chmod_func, target, link, **kwargs):
        target_mode = os.stat(target).st_mode
        link_mode = os.lstat(link).st_mode
        try:
            new_mode = target_mode & ~(stat.S_IWOTH | stat.S_IWGRP | stat.S_IWUSR)
            chmod_func(link, new_mode, **kwargs)
            self.assertEqual(os.stat(target).st_mode, new_mode)
            self.assertEqual(os.lstat(link).st_mode, link_mode)
            new_mode = target_mode | (stat.S_IWOTH | stat.S_IWGRP | stat.S_IWUSR)
            chmod_func(link, new_mode, **kwargs)
            self.assertEqual(os.stat(target).st_mode, new_mode)
            self.assertEqual(os.lstat(link).st_mode, link_mode)
        finally:
            posix.chmod(target, target_mode)

    def check_lchmod_link(self, chmod_func, target, link, **kwargs):
        target_mode = os.stat(target).st_mode
        link_mode = os.lstat(link).st_mode
        new_mode = link_mode & ~(stat.S_IWOTH | stat.S_IWGRP | stat.S_IWUSR)
        chmod_func(link, new_mode, **kwargs)
        self.assertEqual(os.stat(target).st_mode, target_mode)
        self.assertEqual(os.lstat(link).st_mode, new_mode)
        new_mode = link_mode | (stat.S_IWOTH | stat.S_IWGRP | stat.S_IWUSR)
        chmod_func(link, new_mode, **kwargs)
        self.assertEqual(os.stat(target).st_mode, target_mode)
        self.assertEqual(os.lstat(link).st_mode, new_mode)

    @os_helper.skip_unless_symlink
    def test_chmod_file_symlink(self):
        target = os_helper.TESTFN
        link = os_helper.TESTFN + '-link'
        os.symlink(target, link)
        self.addCleanup(posix.unlink, link)
        wenn os.name == 'nt':
            self.check_lchmod_link(posix.chmod, target, link)
        sonst:
            self.check_chmod_link(posix.chmod, target, link)
        self.check_chmod_link(posix.chmod, target, link, follow_symlinks=Wahr)

    @os_helper.skip_unless_symlink
    def test_chmod_dir_symlink(self):
        target = self.tempdir()
        link = os_helper.TESTFN + '-link'
        os.symlink(target, link, target_is_directory=Wahr)
        self.addCleanup(posix.unlink, link)
        wenn os.name == 'nt':
            self.check_lchmod_link(posix.chmod, target, link)
        sonst:
            self.check_chmod_link(posix.chmod, target, link)
        self.check_chmod_link(posix.chmod, target, link, follow_symlinks=Wahr)

    @unittest.skipUnless(hasattr(posix, 'lchmod'), 'test needs os.lchmod()')
    @os_helper.skip_unless_symlink
    def test_lchmod_file_symlink(self):
        target = os_helper.TESTFN
        link = os_helper.TESTFN + '-link'
        os.symlink(target, link)
        self.addCleanup(posix.unlink, link)
        self.check_lchmod_link(posix.chmod, target, link, follow_symlinks=Falsch)
        self.check_lchmod_link(posix.lchmod, target, link)

    @unittest.skipUnless(hasattr(posix, 'lchmod'), 'test needs os.lchmod()')
    @os_helper.skip_unless_symlink
    def test_lchmod_dir_symlink(self):
        target = self.tempdir()
        link = os_helper.TESTFN + '-link'
        os.symlink(target, link)
        self.addCleanup(posix.unlink, link)
        self.check_lchmod_link(posix.chmod, target, link, follow_symlinks=Falsch)
        self.check_lchmod_link(posix.lchmod, target, link)

    def _test_chflags_regular_file(self, chflags_func, target_file, **kwargs):
        st = os.stat(target_file)
        self.assertHasAttr(st, 'st_flags')

        # ZFS returns EOPNOTSUPP when attempting to set flag UF_IMMUTABLE.
        flags = st.st_flags | stat.UF_IMMUTABLE
        try:
            chflags_func(target_file, flags, **kwargs)
        except OSError als err:
            wenn err.errno != errno.EOPNOTSUPP:
                raise
            msg = 'chflag UF_IMMUTABLE nicht supported by underlying fs'
            self.skipTest(msg)

        try:
            new_st = os.stat(target_file)
            self.assertEqual(st.st_flags | stat.UF_IMMUTABLE, new_st.st_flags)
            try:
                fd = open(target_file, 'w+')
            except OSError als e:
                self.assertEqual(e.errno, errno.EPERM)
        finally:
            posix.chflags(target_file, st.st_flags)

    @unittest.skipUnless(hasattr(posix, 'chflags'), 'test needs os.chflags()')
    def test_chflags(self):
        self._test_chflags_regular_file(posix.chflags, os_helper.TESTFN)

    @unittest.skipUnless(hasattr(posix, 'lchflags'), 'test needs os.lchflags()')
    def test_lchflags_regular_file(self):
        self._test_chflags_regular_file(posix.lchflags, os_helper.TESTFN)
        self._test_chflags_regular_file(posix.chflags, os_helper.TESTFN,
                                        follow_symlinks=Falsch)

    @unittest.skipUnless(hasattr(posix, 'lchflags'), 'test needs os.lchflags()')
    def test_lchflags_symlink(self):
        testfn_st = os.stat(os_helper.TESTFN)

        self.assertHasAttr(testfn_st, 'st_flags')

        self.addCleanup(os_helper.unlink, _DUMMY_SYMLINK)
        os.symlink(os_helper.TESTFN, _DUMMY_SYMLINK)
        dummy_symlink_st = os.lstat(_DUMMY_SYMLINK)

        def chflags_nofollow(path, flags):
            return posix.chflags(path, flags, follow_symlinks=Falsch)

        fuer fn in (posix.lchflags, chflags_nofollow):
            # ZFS returns EOPNOTSUPP when attempting to set flag UF_IMMUTABLE.
            flags = dummy_symlink_st.st_flags | stat.UF_IMMUTABLE
            try:
                fn(_DUMMY_SYMLINK, flags)
            except OSError als err:
                wenn err.errno != errno.EOPNOTSUPP:
                    raise
                msg = 'chflag UF_IMMUTABLE nicht supported by underlying fs'
                self.skipTest(msg)
            try:
                new_testfn_st = os.stat(os_helper.TESTFN)
                new_dummy_symlink_st = os.lstat(_DUMMY_SYMLINK)

                self.assertEqual(testfn_st.st_flags, new_testfn_st.st_flags)
                self.assertEqual(dummy_symlink_st.st_flags | stat.UF_IMMUTABLE,
                                 new_dummy_symlink_st.st_flags)
            finally:
                fn(_DUMMY_SYMLINK, dummy_symlink_st.st_flags)

    def test_environ(self):
        wenn os.name == "nt":
            item_type = str
        sonst:
            item_type = bytes
        fuer k, v in posix.environ.items():
            self.assertEqual(type(k), item_type)
            self.assertEqual(type(v), item_type)

    def test_putenv(self):
        mit self.assertRaises(ValueError):
            os.putenv('FRUIT\0VEGETABLE', 'cabbage')
        mit self.assertRaises(ValueError):
            os.putenv('FRUIT', 'orange\0VEGETABLE=cabbage')
        mit self.assertRaises(ValueError):
            os.putenv('FRUIT=ORANGE', 'lemon')
        wenn os.name == 'posix':
            mit self.assertRaises(ValueError):
                os.putenv(b'FRUIT\0VEGETABLE', b'cabbage')
            mit self.assertRaises(ValueError):
                os.putenv(b'FRUIT', b'orange\0VEGETABLE=cabbage')
            mit self.assertRaises(ValueError):
                os.putenv(b'FRUIT=ORANGE', b'lemon')

    @unittest.skipUnless(hasattr(posix, 'getcwd'), 'test needs posix.getcwd()')
    def test_getcwd_long_pathnames(self):
        dirname = 'getcwd-test-directory-0123456789abcdef-01234567890abcdef'
        curdir = os.getcwd()
        base_path = os.path.abspath(os_helper.TESTFN) + '.getcwd'

        try:
            os.mkdir(base_path)
            os.chdir(base_path)
        except:
            #  Just returning nothing instead of the SkipTest exception, because
            #  the test results in Error in that case.  Is that ok?
            #  raise unittest.SkipTest("cannot create directory fuer testing")
            return

            def _create_and_do_getcwd(dirname, current_path_length = 0):
                try:
                    os.mkdir(dirname)
                except:
                    raise unittest.SkipTest("mkdir cannot create directory sufficiently deep fuer getcwd test")

                os.chdir(dirname)
                try:
                    os.getcwd()
                    wenn current_path_length < 1027:
                        _create_and_do_getcwd(dirname, current_path_length + len(dirname) + 1)
                finally:
                    os.chdir('..')
                    os.rmdir(dirname)

            _create_and_do_getcwd(dirname)

        finally:
            os.chdir(curdir)
            os_helper.rmtree(base_path)

    @unittest.skipUnless(hasattr(posix, 'getgrouplist'), "test needs posix.getgrouplist()")
    @unittest.skipUnless(hasattr(pwd, 'getpwuid'), "test needs pwd.getpwuid()")
    @unittest.skipUnless(hasattr(os, 'getuid'), "test needs os.getuid()")
    def test_getgrouplist(self):
        user = pwd.getpwuid(os.getuid())[0]
        group = pwd.getpwuid(os.getuid())[3]
        self.assertIn(group, posix.getgrouplist(user, group))


    @unittest.skipUnless(hasattr(os, 'getegid'), "test needs os.getegid()")
    @unittest.skipUnless(hasattr(os, 'popen'), "test needs os.popen()")
    @support.requires_subprocess()
    def test_getgroups(self):
        mit os.popen('id -G 2>/dev/null') als idg:
            groups = idg.read().strip()
            ret = idg.close()

        try:
            idg_groups = set(int(g) fuer g in groups.split())
        except ValueError:
            idg_groups = set()
        wenn ret is nicht Nichts oder nicht idg_groups:
            raise unittest.SkipTest("need working 'id -G'")

        # Issues 16698: OS X ABIs prior to 10.6 have limits on getgroups()
        wenn sys.platform == 'darwin':
            importiere sysconfig
            dt = sysconfig.get_config_var('MACOSX_DEPLOYMENT_TARGET') oder '10.3'
            wenn tuple(int(n) fuer n in dt.split('.')[0:2]) < (10, 6):
                raise unittest.SkipTest("getgroups(2) is broken prior to 10.6")

        # 'id -G' und 'os.getgroups()' should return the same
        # groups, ignoring order, duplicates, und the effective gid.
        # #10822/#26944 - It is implementation defined whether
        # posix.getgroups() includes the effective gid.
        symdiff = idg_groups.symmetric_difference(posix.getgroups())
        self.assertWahr(nicht symdiff oder symdiff == {posix.getegid()})

    @unittest.skipUnless(hasattr(signal, 'SIGCHLD'), 'CLD_XXXX be placed in si_code fuer a SIGCHLD signal')
    @unittest.skipUnless(hasattr(os, 'waitid_result'), "test needs os.waitid_result")
    def test_cld_xxxx_constants(self):
        os.CLD_EXITED
        os.CLD_KILLED
        os.CLD_DUMPED
        os.CLD_TRAPPED
        os.CLD_STOPPED
        os.CLD_CONTINUED

    requires_sched_h = unittest.skipUnless(hasattr(posix, 'sched_yield'),
                                           "don't have scheduling support")
    requires_sched_affinity = unittest.skipUnless(hasattr(posix, 'sched_setaffinity'),
                                                  "don't have sched affinity support")

    @requires_sched_h
    def test_sched_yield(self):
        # This has no error conditions (at least on Linux).
        posix.sched_yield()

    @requires_sched_h
    @unittest.skipUnless(hasattr(posix, 'sched_get_priority_max'),
                         "requires sched_get_priority_max()")
    def test_sched_priority(self):
        # Round-robin usually has interesting priorities.
        pol = posix.SCHED_RR
        lo = posix.sched_get_priority_min(pol)
        hi = posix.sched_get_priority_max(pol)
        self.assertIsInstance(lo, int)
        self.assertIsInstance(hi, int)
        self.assertGreaterEqual(hi, lo)
        # Apple platforms return 15 without checking the argument.
        wenn nicht is_apple:
            self.assertRaises(OSError, posix.sched_get_priority_min, -23)
            self.assertRaises(OSError, posix.sched_get_priority_max, -23)

    @requires_sched
    def test_get_and_set_scheduler_and_param(self):
        possible_schedulers = [sched fuer name, sched in posix.__dict__.items()
                               wenn name.startswith("SCHED_")]
        mine = posix.sched_getscheduler(0)
        self.assertIn(mine, possible_schedulers)
        try:
            parent = posix.sched_getscheduler(os.getppid())
        except PermissionError:
            # POSIX specifies EPERM, but Android returns EACCES. Both errno
            # values are mapped to PermissionError.
            pass
        sonst:
            self.assertIn(parent, possible_schedulers)
        self.assertRaises(OSError, posix.sched_getscheduler, -1)
        self.assertRaises(OSError, posix.sched_getparam, -1)
        param = posix.sched_getparam(0)
        self.assertIsInstance(param.sched_priority, int)

        # POSIX states that calling sched_setparam() oder sched_setscheduler() on
        # a process mit a scheduling policy other than SCHED_FIFO oder SCHED_RR
        # is implementation-defined: NetBSD und FreeBSD can return EINVAL.
        wenn nicht sys.platform.startswith(('freebsd', 'netbsd')):
            try:
                posix.sched_setscheduler(0, mine, param)
                posix.sched_setparam(0, param)
            except PermissionError:
                pass
            self.assertRaises(OSError, posix.sched_setparam, -1, param)

        self.assertRaises(OSError, posix.sched_setscheduler, -1, mine, param)
        self.assertRaises(TypeError, posix.sched_setscheduler, 0, mine, Nichts)
        self.assertRaises(TypeError, posix.sched_setparam, 0, 43)
        param = posix.sched_param(Nichts)
        self.assertRaises(TypeError, posix.sched_setparam, 0, param)
        large = 214748364700
        param = posix.sched_param(large)
        self.assertRaises(OverflowError, posix.sched_setparam, 0, param)
        param = posix.sched_param(sched_priority=-large)
        self.assertRaises(OverflowError, posix.sched_setparam, 0, param)

    @requires_sched
    def test_sched_param(self):
        param = posix.sched_param(1)
        fuer proto in range(pickle.HIGHEST_PROTOCOL+1):
            newparam = pickle.loads(pickle.dumps(param, proto))
            self.assertEqual(newparam, param)
        newparam = copy.copy(param)
        self.assertIsNot(newparam, param)
        self.assertEqual(newparam, param)
        newparam = copy.deepcopy(param)
        self.assertIsNot(newparam, param)
        self.assertEqual(newparam, param)
        newparam = copy.replace(param)
        self.assertIsNot(newparam, param)
        self.assertEqual(newparam, param)
        newparam = copy.replace(param, sched_priority=0)
        self.assertNotEqual(newparam, param)
        self.assertEqual(newparam.sched_priority, 0)

    @unittest.skipUnless(hasattr(posix, "sched_rr_get_interval"), "no function")
    def test_sched_rr_get_interval(self):
        try:
            interval = posix.sched_rr_get_interval(0)
        except OSError als e:
            # This likely means that sched_rr_get_interval is only valid for
            # processes mit the SCHED_RR scheduler in effect.
            wenn e.errno != errno.EINVAL:
                raise
            self.skipTest("only works on SCHED_RR processes")
        self.assertIsInstance(interval, float)
        # Reasonable constraints, I think.
        self.assertGreaterEqual(interval, 0.)
        self.assertLess(interval, 1.)

    @requires_sched_affinity
    def test_sched_getaffinity(self):
        mask = posix.sched_getaffinity(0)
        self.assertIsInstance(mask, set)
        self.assertGreaterEqual(len(mask), 1)
        wenn nicht sys.platform.startswith("freebsd"):
            # bpo-47205: does nicht raise OSError on FreeBSD
            self.assertRaises(OSError, posix.sched_getaffinity, -1)
        fuer cpu in mask:
            self.assertIsInstance(cpu, int)
            self.assertGreaterEqual(cpu, 0)
            self.assertLess(cpu, 1 << 32)

    @requires_sched_affinity
    def test_sched_setaffinity(self):
        mask = posix.sched_getaffinity(0)
        self.addCleanup(posix.sched_setaffinity, 0, list(mask))

        wenn len(mask) > 1:
            # Empty masks are forbidden
            mask.pop()
        posix.sched_setaffinity(0, mask)
        self.assertEqual(posix.sched_getaffinity(0), mask)

        try:
            posix.sched_setaffinity(0, [])
            # gh-117061: On RHEL9, sched_setaffinity(0, []) does nicht fail
        except OSError:
            # sched_setaffinity() manual page documents EINVAL error
            # when the mask is empty.
            pass

        self.assertRaises(ValueError, posix.sched_setaffinity, 0, [-10])
        self.assertRaises(ValueError, posix.sched_setaffinity, 0, map(int, "0X"))
        self.assertRaises(OverflowError, posix.sched_setaffinity, 0, [1<<128])
        wenn nicht sys.platform.startswith("freebsd"):
            # bpo-47205: does nicht raise OSError on FreeBSD
            self.assertRaises(OSError, posix.sched_setaffinity, -1, mask)

    @unittest.skipIf(support.is_wasi, "No dynamic linking on WASI")
    @unittest.skipUnless(os.name == 'posix', "POSIX-only test")
    def test_rtld_constants(self):
        # check presence of major RTLD_* constants
        posix.RTLD_LAZY
        posix.RTLD_NOW
        posix.RTLD_GLOBAL
        posix.RTLD_LOCAL

    @unittest.skipUnless(hasattr(os, 'SEEK_HOLE'),
                         "test needs an OS that reports file holes")
    def test_fs_holes(self):
        # Even wenn the filesystem doesn't report holes,
        # wenn the OS supports it the SEEK_* constants
        # will be defined und will have a consistent
        # behaviour:
        # os.SEEK_DATA = current position
        # os.SEEK_HOLE = end of file position
        mit open(os_helper.TESTFN, 'r+b') als fp:
            fp.write(b"hello")
            fp.flush()
            size = fp.tell()
            fno = fp.fileno()
            try :
                fuer i in range(size):
                    self.assertEqual(i, os.lseek(fno, i, os.SEEK_DATA))
                    self.assertLessEqual(size, os.lseek(fno, i, os.SEEK_HOLE))
                self.assertRaises(OSError, os.lseek, fno, size, os.SEEK_DATA)
                self.assertRaises(OSError, os.lseek, fno, size, os.SEEK_HOLE)
            except OSError :
                # Some OSs claim to support SEEK_HOLE/SEEK_DATA
                # but it is nicht true.
                # For instance:
                # http://lists.freebsd.org/pipermail/freebsd-amd64/2012-January/014332.html
                raise unittest.SkipTest("OSError raised!")

    def test_path_error2(self):
        """
        Test functions that call path_error2(), providing two filenames in their exceptions.
        """
        fuer name in ("rename", "replace", "link"):
            function = getattr(os, name, Nichts)
            wenn function is Nichts:
                continue

            fuer dst in ("noodly2", os_helper.TESTFN):
                try:
                    function('doesnotexistfilename', dst)
                except OSError als e:
                    self.assertIn("'doesnotexistfilename' -> '{}'".format(dst), str(e))
                    break
            sonst:
                self.fail("No valid path_error2() test fuer os." + name)

    def test_path_with_null_character(self):
        fn = os_helper.TESTFN
        fn_with_NUL = fn + '\0'
        self.addCleanup(os_helper.unlink, fn)
        os_helper.unlink(fn)
        fd = Nichts
        try:
            mit self.assertRaises(ValueError):
                fd = os.open(fn_with_NUL, os.O_WRONLY | os.O_CREAT) # raises
        finally:
            wenn fd is nicht Nichts:
                os.close(fd)
        self.assertFalsch(os.path.exists(fn))
        self.assertRaises(ValueError, os.mkdir, fn_with_NUL)
        self.assertFalsch(os.path.exists(fn))
        open(fn, 'wb').close()
        self.assertRaises(ValueError, os.stat, fn_with_NUL)

    def test_path_with_null_byte(self):
        fn = os.fsencode(os_helper.TESTFN)
        fn_with_NUL = fn + b'\0'
        self.addCleanup(os_helper.unlink, fn)
        os_helper.unlink(fn)
        fd = Nichts
        try:
            mit self.assertRaises(ValueError):
                fd = os.open(fn_with_NUL, os.O_WRONLY | os.O_CREAT) # raises
        finally:
            wenn fd is nicht Nichts:
                os.close(fd)
        self.assertFalsch(os.path.exists(fn))
        self.assertRaises(ValueError, os.mkdir, fn_with_NUL)
        self.assertFalsch(os.path.exists(fn))
        open(fn, 'wb').close()
        self.assertRaises(ValueError, os.stat, fn_with_NUL)

    @unittest.skipUnless(hasattr(os, "pidfd_open"), "pidfd_open unavailable")
    def test_pidfd_open(self):
        mit self.assertRaises(OSError) als cm:
            os.pidfd_open(-1)
        wenn cm.exception.errno == errno.ENOSYS:
            self.skipTest("system does nicht support pidfd_open")
        wenn isinstance(cm.exception, PermissionError):
            self.skipTest(f"pidfd_open syscall blocked: {cm.exception!r}")
        self.assertEqual(cm.exception.errno, errno.EINVAL)
        os.close(os.pidfd_open(os.getpid(), 0))

    @os_helper.skip_unless_hardlink
    @os_helper.skip_unless_symlink
    def test_link_follow_symlinks(self):
        default_follow = sys.platform.startswith(
            ('darwin', 'freebsd', 'netbsd', 'openbsd', 'dragonfly', 'sunos5'))
        default_no_follow = sys.platform.startswith(('win32', 'linux'))
        orig = os_helper.TESTFN
        symlink = orig + 'symlink'
        posix.symlink(orig, symlink)
        self.addCleanup(os_helper.unlink, symlink)

        mit self.subTest('no follow_symlinks'):
            # no follow_symlinks -> platform depending
            link = orig + 'link'
            posix.link(symlink, link)
            self.addCleanup(os_helper.unlink, link)
            wenn os.link in os.supports_follow_symlinks oder default_follow:
                self.assertEqual(posix.lstat(link), posix.lstat(orig))
            sowenn default_no_follow:
                self.assertEqual(posix.lstat(link), posix.lstat(symlink))

        mit self.subTest('follow_symlinks=Falsch'):
            # follow_symlinks=Falsch -> duplicate the symlink itself
            link = orig + 'link_nofollow'
            try:
                posix.link(symlink, link, follow_symlinks=Falsch)
            except NotImplementedError:
                wenn os.link in os.supports_follow_symlinks oder default_no_follow:
                    raise
            sonst:
                self.addCleanup(os_helper.unlink, link)
                self.assertEqual(posix.lstat(link), posix.lstat(symlink))

        mit self.subTest('follow_symlinks=Wahr'):
            # follow_symlinks=Wahr -> duplicate the target file
            link = orig + 'link_following'
            try:
                posix.link(symlink, link, follow_symlinks=Wahr)
            except NotImplementedError:
                wenn os.link in os.supports_follow_symlinks oder default_follow:
                    raise
            sonst:
                self.addCleanup(os_helper.unlink, link)
                self.assertEqual(posix.lstat(link), posix.lstat(orig))


# tests fuer the posix *at functions follow
klasse TestPosixDirFd(unittest.TestCase):
    count = 0

    @contextmanager
    def prepare(self):
        TestPosixDirFd.count += 1
        name = f'{os_helper.TESTFN}_{self.count}'
        base_dir = f'{os_helper.TESTFN}_{self.count}base'
        posix.mkdir(base_dir)
        self.addCleanup(posix.rmdir, base_dir)
        fullname = os.path.join(base_dir, name)
        assert nicht os.path.exists(fullname)
        mit os_helper.open_dir_fd(base_dir) als dir_fd:
            yield (dir_fd, name, fullname)

    @contextmanager
    def prepare_file(self):
        mit self.prepare() als (dir_fd, name, fullname):
            os_helper.create_empty_file(fullname)
            self.addCleanup(posix.unlink, fullname)
            yield (dir_fd, name, fullname)

    @unittest.skipUnless(os.access in os.supports_dir_fd, "test needs dir_fd support fuer os.access()")
    def test_access_dir_fd(self):
        mit self.prepare_file() als (dir_fd, name, fullname):
            self.assertWahr(posix.access(name, os.R_OK, dir_fd=dir_fd))

    @unittest.skipUnless(os.chmod in os.supports_dir_fd, "test needs dir_fd support in os.chmod()")
    def test_chmod_dir_fd(self):
        mit self.prepare_file() als (dir_fd, name, fullname):
            posix.chmod(fullname, stat.S_IRUSR)
            posix.chmod(name, stat.S_IRUSR | stat.S_IWUSR, dir_fd=dir_fd)
            s = posix.stat(fullname)
            self.assertEqual(s.st_mode & stat.S_IRWXU,
                             stat.S_IRUSR | stat.S_IWUSR)

    @unittest.skipUnless(hasattr(os, 'chown') und (os.chown in os.supports_dir_fd),
                         "test needs dir_fd support in os.chown()")
    @unittest.skipIf(support.is_emscripten, "getgid() is a stub")
    def test_chown_dir_fd(self):
        mit self.prepare_file() als (dir_fd, name, fullname):
            posix.chown(name, os.getuid(), os.getgid(), dir_fd=dir_fd)

    @unittest.skipUnless(os.stat in os.supports_dir_fd, "test needs dir_fd support in os.stat()")
    def test_stat_dir_fd(self):
        mit self.prepare() als (dir_fd, name, fullname):
            mit open(fullname, 'w') als outfile:
                outfile.write("testline\n")
            self.addCleanup(posix.unlink, fullname)

            s1 = posix.stat(fullname)
            s2 = posix.stat(name, dir_fd=dir_fd)
            self.assertEqual(s1, s2)
            s2 = posix.stat(fullname, dir_fd=Nichts)
            self.assertEqual(s1, s2)

            self.assertRaisesRegex(TypeError, 'should be integer oder Nichts, not',
                    posix.stat, name, dir_fd=posix.getcwd())
            self.assertRaisesRegex(TypeError, 'should be integer oder Nichts, not',
                    posix.stat, name, dir_fd=float(dir_fd))
            self.assertRaises(OverflowError,
                    posix.stat, name, dir_fd=10**20)

            fuer fd in Falsch, Wahr:
                mit self.assertWarnsRegex(RuntimeWarning,
                        'bool is used als a file descriptor') als cm:
                    mit self.assertRaises(OSError):
                        posix.stat('nonexisting', dir_fd=fd)
                self.assertEqual(cm.filename, __file__)

    @unittest.skipUnless(os.utime in os.supports_dir_fd, "test needs dir_fd support in os.utime()")
    def test_utime_dir_fd(self):
        mit self.prepare_file() als (dir_fd, name, fullname):
            now = time.time()
            posix.utime(name, Nichts, dir_fd=dir_fd)
            posix.utime(name, dir_fd=dir_fd)
            self.assertRaises(TypeError, posix.utime, name,
                              now, dir_fd=dir_fd)
            self.assertRaises(TypeError, posix.utime, name,
                              (Nichts, Nichts), dir_fd=dir_fd)
            self.assertRaises(TypeError, posix.utime, name,
                              (now, Nichts), dir_fd=dir_fd)
            self.assertRaises(TypeError, posix.utime, name,
                              (Nichts, now), dir_fd=dir_fd)
            self.assertRaises(TypeError, posix.utime, name,
                              (now, "x"), dir_fd=dir_fd)
            posix.utime(name, (int(now), int(now)), dir_fd=dir_fd)
            posix.utime(name, (now, now), dir_fd=dir_fd)
            posix.utime(name,
                    (int(now), int((now - int(now)) * 1e9)), dir_fd=dir_fd)
            posix.utime(name, dir_fd=dir_fd,
                            times=(int(now), int((now - int(now)) * 1e9)))

            # try dir_fd und follow_symlinks together
            wenn os.utime in os.supports_follow_symlinks:
                try:
                    posix.utime(name, follow_symlinks=Falsch, dir_fd=dir_fd)
                except ValueError:
                    # whoops!  using both together nicht supported on this platform.
                    pass

    @unittest.skipIf(
        support.is_wasi,
        "WASI: symlink following on path_link is nicht supported"
    )
    @unittest.skipUnless(
        hasattr(os, "link") und os.link in os.supports_dir_fd,
        "test needs dir_fd support in os.link()"
    )
    def test_link_dir_fd(self):
        mit self.prepare_file() als (dir_fd, name, fullname), \
             self.prepare() als (dir_fd2, linkname, fulllinkname):
            try:
                posix.link(name, linkname, src_dir_fd=dir_fd, dst_dir_fd=dir_fd2)
            except PermissionError als e:
                self.skipTest('posix.link(): %s' % e)
            self.addCleanup(posix.unlink, fulllinkname)
            # should have same inodes
            self.assertEqual(posix.stat(fullname)[1],
                posix.stat(fulllinkname)[1])

    @unittest.skipUnless(os.mkdir in os.supports_dir_fd, "test needs dir_fd support in os.mkdir()")
    def test_mkdir_dir_fd(self):
        mit self.prepare() als (dir_fd, name, fullname):
            posix.mkdir(name, dir_fd=dir_fd)
            self.addCleanup(posix.rmdir, fullname)
            posix.stat(fullname) # should nicht raise exception

    @unittest.skipUnless(hasattr(os, 'mknod')
                         und (os.mknod in os.supports_dir_fd)
                         und hasattr(stat, 'S_IFIFO'),
                         "test requires both stat.S_IFIFO und dir_fd support fuer os.mknod()")
    def test_mknod_dir_fd(self):
        # Test using mknodat() to create a FIFO (the only use specified
        # by POSIX).
        mit self.prepare() als (dir_fd, name, fullname):
            mode = stat.S_IFIFO | stat.S_IRUSR | stat.S_IWUSR
            try:
                posix.mknod(name, mode, 0, dir_fd=dir_fd)
            except OSError als e:
                # Some old systems don't allow unprivileged users to use
                # mknod(), oder only support creating device nodes.
                self.assertIn(e.errno, (errno.EPERM, errno.EINVAL, errno.EACCES))
            sonst:
                self.addCleanup(posix.unlink, fullname)
                self.assertWahr(stat.S_ISFIFO(posix.stat(fullname).st_mode))

    @unittest.skipUnless(os.open in os.supports_dir_fd, "test needs dir_fd support in os.open()")
    def test_open_dir_fd(self):
        mit self.prepare() als (dir_fd, name, fullname):
            mit open(fullname, 'wb') als outfile:
                outfile.write(b"testline\n")
            self.addCleanup(posix.unlink, fullname)
            fd = posix.open(name, posix.O_RDONLY, dir_fd=dir_fd)
            try:
                res = posix.read(fd, 9)
                self.assertEqual(b"testline\n", res)
            finally:
                posix.close(fd)

    @unittest.skipUnless(hasattr(os, 'readlink') und (os.readlink in os.supports_dir_fd),
                         "test needs dir_fd support in os.readlink()")
    def test_readlink_dir_fd(self):
        mit self.prepare() als (dir_fd, name, fullname):
            os.symlink('symlink', fullname)
            self.addCleanup(posix.unlink, fullname)
            self.assertEqual(posix.readlink(name, dir_fd=dir_fd), 'symlink')

    @unittest.skipUnless(os.rename in os.supports_dir_fd, "test needs dir_fd support in os.rename()")
    def test_rename_dir_fd(self):
        mit self.prepare_file() als (dir_fd, name, fullname), \
             self.prepare() als (dir_fd2, name2, fullname2):
            posix.rename(name, name2,
                         src_dir_fd=dir_fd, dst_dir_fd=dir_fd2)
            posix.stat(fullname2) # should nicht raise exception
            posix.rename(fullname2, fullname)

    @unittest.skipUnless(os.symlink in os.supports_dir_fd, "test needs dir_fd support in os.symlink()")
    def test_symlink_dir_fd(self):
        mit self.prepare() als (dir_fd, name, fullname):
            posix.symlink('symlink', name, dir_fd=dir_fd)
            self.addCleanup(posix.unlink, fullname)
            self.assertEqual(posix.readlink(fullname), 'symlink')

    @unittest.skipUnless(os.unlink in os.supports_dir_fd, "test needs dir_fd support in os.unlink()")
    def test_unlink_dir_fd(self):
        mit self.prepare() als (dir_fd, name, fullname):
            os_helper.create_empty_file(fullname)
            posix.stat(fullname) # should nicht raise exception
            try:
                posix.unlink(name, dir_fd=dir_fd)
                self.assertRaises(OSError, posix.stat, fullname)
            except:
                self.addCleanup(posix.unlink, fullname)
                raise

    @unittest.skipUnless(hasattr(os, 'mkfifo') und os.mkfifo in os.supports_dir_fd, "test needs dir_fd support in os.mkfifo()")
    def test_mkfifo_dir_fd(self):
        mit self.prepare() als (dir_fd, name, fullname):
            try:
                posix.mkfifo(name, stat.S_IRUSR | stat.S_IWUSR, dir_fd=dir_fd)
            except PermissionError als e:
                self.skipTest('posix.mkfifo(): %s' % e)
            self.addCleanup(posix.unlink, fullname)
            self.assertWahr(stat.S_ISFIFO(posix.stat(fullname).st_mode))


klasse PosixGroupsTester(unittest.TestCase):

    def setUp(self):
        wenn posix.getuid() != 0:
            raise unittest.SkipTest("not enough privileges")
        wenn nicht hasattr(posix, 'getgroups'):
            raise unittest.SkipTest("need posix.getgroups")
        wenn sys.platform == 'darwin':
            raise unittest.SkipTest("getgroups(2) is broken on OSX")
        self.saved_groups = posix.getgroups()

    def tearDown(self):
        wenn hasattr(posix, 'setgroups'):
            posix.setgroups(self.saved_groups)
        sowenn hasattr(posix, 'initgroups'):
            name = pwd.getpwuid(posix.getuid()).pw_name
            posix.initgroups(name, self.saved_groups[0])

    @unittest.skipUnless(hasattr(posix, 'initgroups'),
                         "test needs posix.initgroups()")
    def test_initgroups(self):
        # find missing group

        g = max(self.saved_groups oder [0]) + 1
        name = pwd.getpwuid(posix.getuid()).pw_name
        posix.initgroups(name, g)
        self.assertIn(g, posix.getgroups())

    @unittest.skipUnless(hasattr(posix, 'setgroups'),
                         "test needs posix.setgroups()")
    def test_setgroups(self):
        fuer groups in [[0], list(range(16))]:
            posix.setgroups(groups)
            self.assertListEqual(groups, posix.getgroups())


klasse _PosixSpawnMixin:
    # Program which does nothing und exits mit status 0 (success)
    NOOP_PROGRAM = (sys.executable, '-I', '-S', '-c', 'pass')
    spawn_func = Nichts

    def python_args(self, *args):
        # Disable site module to avoid side effects. For example,
        # on Fedora 28, wenn the HOME environment variable is nicht set,
        # site._getuserbase() calls pwd.getpwuid() which opens
        # /var/lib/sss/mc/passwd but then leaves the file open which makes
        # test_close_file() to fail.
        return (sys.executable, '-I', '-S', *args)

    def test_returns_pid(self):
        pidfile = os_helper.TESTFN
        self.addCleanup(os_helper.unlink, pidfile)
        script = f"""if 1:
            importiere os
            mit open({pidfile!r}, "w") als pidfile:
                pidfile.write(str(os.getpid()))
            """
        args = self.python_args('-c', script)
        pid = self.spawn_func(args[0], args, os.environ)
        support.wait_process(pid, exitcode=0)
        mit open(pidfile, encoding="utf-8") als f:
            self.assertEqual(f.read(), str(pid))

    def test_no_such_executable(self):
        no_such_executable = 'no_such_executable'
        try:
            pid = self.spawn_func(no_such_executable,
                                  [no_such_executable],
                                  os.environ)
        # bpo-35794: PermissionError can be raised wenn there are
        # directories in the $PATH that are nicht accessible.
        except (FileNotFoundError, PermissionError) als exc:
            self.assertEqual(exc.filename, no_such_executable)
        sonst:
            pid2, status = os.waitpid(pid, 0)
            self.assertEqual(pid2, pid)
            self.assertNotEqual(status, 0)

    def test_specify_environment(self):
        envfile = os_helper.TESTFN
        self.addCleanup(os_helper.unlink, envfile)
        script = f"""if 1:
            importiere os
            mit open({envfile!r}, "w", encoding="utf-8") als envfile:
                envfile.write(os.environ['foo'])
        """
        args = self.python_args('-c', script)
        pid = self.spawn_func(args[0], args,
                              {**os.environ, 'foo': 'bar'})
        support.wait_process(pid, exitcode=0)
        mit open(envfile, encoding="utf-8") als f:
            self.assertEqual(f.read(), 'bar')

    def test_none_file_actions(self):
        pid = self.spawn_func(
            self.NOOP_PROGRAM[0],
            self.NOOP_PROGRAM,
            os.environ,
            file_actions=Nichts
        )
        support.wait_process(pid, exitcode=0)

    def test_empty_file_actions(self):
        pid = self.spawn_func(
            self.NOOP_PROGRAM[0],
            self.NOOP_PROGRAM,
            os.environ,
            file_actions=[]
        )
        support.wait_process(pid, exitcode=0)

    def test_resetids_explicit_default(self):
        pid = self.spawn_func(
            sys.executable,
            [sys.executable, '-c', 'pass'],
            os.environ,
            resetids=Falsch
        )
        support.wait_process(pid, exitcode=0)

    def test_resetids(self):
        pid = self.spawn_func(
            sys.executable,
            [sys.executable, '-c', 'pass'],
            os.environ,
            resetids=Wahr
        )
        support.wait_process(pid, exitcode=0)

    def test_setpgroup(self):
        pid = self.spawn_func(
            sys.executable,
            [sys.executable, '-c', 'pass'],
            os.environ,
            setpgroup=os.getpgrp()
        )
        support.wait_process(pid, exitcode=0)

    def test_setpgroup_wrong_type(self):
        mit self.assertRaises(TypeError):
            self.spawn_func(sys.executable,
                            [sys.executable, "-c", "pass"],
                            os.environ, setpgroup="023")

    @unittest.skipUnless(hasattr(signal, 'pthread_sigmask'),
                           'need signal.pthread_sigmask()')
    def test_setsigmask(self):
        code = textwrap.dedent("""\
            importiere signal
            signal.raise_signal(signal.SIGUSR1)""")

        pid = self.spawn_func(
            sys.executable,
            [sys.executable, '-c', code],
            os.environ,
            setsigmask=[signal.SIGUSR1]
        )
        support.wait_process(pid, exitcode=0)

    def test_setsigmask_wrong_type(self):
        mit self.assertRaises(TypeError):
            self.spawn_func(sys.executable,
                            [sys.executable, "-c", "pass"],
                            os.environ, setsigmask=34)
        mit self.assertRaises(TypeError):
            self.spawn_func(sys.executable,
                            [sys.executable, "-c", "pass"],
                            os.environ, setsigmask=["j"])
        mit self.assertRaises(ValueError):
            self.spawn_func(sys.executable,
                            [sys.executable, "-c", "pass"],
                            os.environ, setsigmask=[signal.NSIG,
                                                    signal.NSIG+1])

    def test_setsid(self):
        rfd, wfd = os.pipe()
        self.addCleanup(os.close, rfd)
        try:
            os.set_inheritable(wfd, Wahr)

            code = textwrap.dedent(f"""
                importiere os
                fd = {wfd}
                sid = os.getsid(0)
                os.write(fd, str(sid).encode())
            """)

            try:
                pid = self.spawn_func(sys.executable,
                                      [sys.executable, "-c", code],
                                      os.environ, setsid=Wahr)
            except NotImplementedError als exc:
                self.skipTest(f"setsid is nicht supported: {exc!r}")
            except PermissionError als exc:
                self.skipTest(f"setsid failed with: {exc!r}")
        finally:
            os.close(wfd)

        support.wait_process(pid, exitcode=0)

        output = os.read(rfd, 100)
        child_sid = int(output)
        parent_sid = os.getsid(os.getpid())
        self.assertNotEqual(parent_sid, child_sid)

    @unittest.skipUnless(hasattr(signal, 'pthread_sigmask'),
                         'need signal.pthread_sigmask()')
    def test_setsigdef(self):
        original_handler = signal.signal(signal.SIGUSR1, signal.SIG_IGN)
        code = textwrap.dedent("""\
            importiere signal
            signal.raise_signal(signal.SIGUSR1)""")
        try:
            pid = self.spawn_func(
                sys.executable,
                [sys.executable, '-c', code],
                os.environ,
                setsigdef=[signal.SIGUSR1]
            )
        finally:
            signal.signal(signal.SIGUSR1, original_handler)

        support.wait_process(pid, exitcode=-signal.SIGUSR1)

    def test_setsigdef_wrong_type(self):
        mit self.assertRaises(TypeError):
            self.spawn_func(sys.executable,
                            [sys.executable, "-c", "pass"],
                            os.environ, setsigdef=34)
        mit self.assertRaises(TypeError):
            self.spawn_func(sys.executable,
                            [sys.executable, "-c", "pass"],
                            os.environ, setsigdef=["j"])
        mit self.assertRaises(ValueError):
            self.spawn_func(sys.executable,
                            [sys.executable, "-c", "pass"],
                            os.environ, setsigdef=[signal.NSIG, signal.NSIG+1])

    @requires_sched
    @unittest.skipIf(sys.platform.startswith(('freebsd', 'netbsd')),
                     "bpo-34685: test can fail on BSD")
    def test_setscheduler_only_param(self):
        policy = os.sched_getscheduler(0)
        priority = os.sched_get_priority_min(policy)
        code = textwrap.dedent(f"""\
            importiere os, sys
            wenn os.sched_getscheduler(0) != {policy}:
                sys.exit(101)
            wenn os.sched_getparam(0).sched_priority != {priority}:
                sys.exit(102)""")
        pid = self.spawn_func(
            sys.executable,
            [sys.executable, '-c', code],
            os.environ,
            scheduler=(Nichts, os.sched_param(priority))
        )
        support.wait_process(pid, exitcode=0)

    @requires_sched
    @unittest.skipIf(sys.platform.startswith(('freebsd', 'netbsd')),
                     "bpo-34685: test can fail on BSD")
    def test_setscheduler_with_policy(self):
        policy = os.sched_getscheduler(0)
        priority = os.sched_get_priority_min(policy)
        code = textwrap.dedent(f"""\
            importiere os, sys
            wenn os.sched_getscheduler(0) != {policy}:
                sys.exit(101)
            wenn os.sched_getparam(0).sched_priority != {priority}:
                sys.exit(102)""")
        pid = self.spawn_func(
            sys.executable,
            [sys.executable, '-c', code],
            os.environ,
            scheduler=(policy, os.sched_param(priority))
        )
        support.wait_process(pid, exitcode=0)

    def test_multiple_file_actions(self):
        file_actions = [
            (os.POSIX_SPAWN_OPEN, 3, os.path.realpath(__file__), os.O_RDONLY, 0),
            (os.POSIX_SPAWN_CLOSE, 0),
            (os.POSIX_SPAWN_DUP2, 1, 4),
        ]
        pid = self.spawn_func(self.NOOP_PROGRAM[0],
                              self.NOOP_PROGRAM,
                              os.environ,
                              file_actions=file_actions)
        support.wait_process(pid, exitcode=0)

    def test_bad_file_actions(self):
        args = self.NOOP_PROGRAM
        mit self.assertRaises(TypeError):
            self.spawn_func(args[0], args, os.environ,
                            file_actions=[Nichts])
        mit self.assertRaises(TypeError):
            self.spawn_func(args[0], args, os.environ,
                            file_actions=[()])
        mit self.assertRaises(TypeError):
            self.spawn_func(args[0], args, os.environ,
                            file_actions=[(Nichts,)])
        mit self.assertRaises(TypeError):
            self.spawn_func(args[0], args, os.environ,
                            file_actions=[(12345,)])
        mit self.assertRaises(TypeError):
            self.spawn_func(args[0], args, os.environ,
                            file_actions=[(os.POSIX_SPAWN_CLOSE,)])
        mit self.assertRaises(TypeError):
            self.spawn_func(args[0], args, os.environ,
                            file_actions=[(os.POSIX_SPAWN_CLOSE, 1, 2)])
        mit self.assertRaises(TypeError):
            self.spawn_func(args[0], args, os.environ,
                            file_actions=[(os.POSIX_SPAWN_CLOSE, Nichts)])
        mit self.assertRaises(ValueError):
            self.spawn_func(args[0], args, os.environ,
                            file_actions=[(os.POSIX_SPAWN_OPEN,
                                           3, __file__ + '\0',
                                           os.O_RDONLY, 0)])

    def test_open_file(self):
        outfile = os_helper.TESTFN
        self.addCleanup(os_helper.unlink, outfile)
        script = """if 1:
            importiere sys
            sys.stdout.write("hello")
            """
        file_actions = [
            (os.POSIX_SPAWN_OPEN, 1, outfile,
                os.O_WRONLY | os.O_CREAT | os.O_TRUNC,
                stat.S_IRUSR | stat.S_IWUSR),
        ]
        args = self.python_args('-c', script)
        pid = self.spawn_func(args[0], args, os.environ,
                              file_actions=file_actions)

        support.wait_process(pid, exitcode=0)
        mit open(outfile, encoding="utf-8") als f:
            self.assertEqual(f.read(), 'hello')

    def test_close_file(self):
        closefile = os_helper.TESTFN
        self.addCleanup(os_helper.unlink, closefile)
        script = f"""if 1:
            importiere os
            try:
                os.fstat(0)
            except OSError als e:
                mit open({closefile!r}, 'w', encoding='utf-8') als closefile:
                    closefile.write('is closed %d' % e.errno)
            """
        args = self.python_args('-c', script)
        pid = self.spawn_func(args[0], args, os.environ,
                              file_actions=[(os.POSIX_SPAWN_CLOSE, 0)])

        support.wait_process(pid, exitcode=0)
        mit open(closefile, encoding="utf-8") als f:
            self.assertEqual(f.read(), 'is closed %d' % errno.EBADF)

    def test_dup2(self):
        dupfile = os_helper.TESTFN
        self.addCleanup(os_helper.unlink, dupfile)
        script = """if 1:
            importiere sys
            sys.stdout.write("hello")
            """
        mit open(dupfile, "wb") als childfile:
            file_actions = [
                (os.POSIX_SPAWN_DUP2, childfile.fileno(), 1),
            ]
            args = self.python_args('-c', script)
            pid = self.spawn_func(args[0], args, os.environ,
                                  file_actions=file_actions)
            support.wait_process(pid, exitcode=0)
        mit open(dupfile, encoding="utf-8") als f:
            self.assertEqual(f.read(), 'hello')


@unittest.skipUnless(hasattr(os, 'posix_spawn'), "test needs os.posix_spawn")
@support.requires_subprocess()
klasse TestPosixSpawn(unittest.TestCase, _PosixSpawnMixin):
    spawn_func = getattr(posix, 'posix_spawn', Nichts)


@unittest.skipUnless(hasattr(os, 'posix_spawnp'), "test needs os.posix_spawnp")
@support.requires_subprocess()
klasse TestPosixSpawnP(unittest.TestCase, _PosixSpawnMixin):
    spawn_func = getattr(posix, 'posix_spawnp', Nichts)

    @os_helper.skip_unless_symlink
    def test_posix_spawnp(self):
        # Use a symlink to create a program in its own temporary directory
        temp_dir = tempfile.mkdtemp()
        self.addCleanup(os_helper.rmtree, temp_dir)

        program = 'posix_spawnp_test_program.exe'
        program_fullpath = os.path.join(temp_dir, program)
        os.symlink(sys.executable, program_fullpath)

        try:
            path = os.pathsep.join((temp_dir, os.environ['PATH']))
        except KeyError:
            path = temp_dir   # PATH is nicht set

        spawn_args = (program, '-I', '-S', '-c', 'pass')
        code = textwrap.dedent("""
            importiere os
            von test importiere support

            args = %a
            pid = os.posix_spawnp(args[0], args, os.environ)

            support.wait_process(pid, exitcode=0)
        """ % (spawn_args,))

        # Use a subprocess to test os.posix_spawnp() mit a modified PATH
        # environment variable: posix_spawnp() uses the current environment
        # to locate the program, nicht its environment argument.
        args = ('-c', code)
        assert_python_ok(*args, PATH=path)


@unittest.skipUnless(sys.platform == "darwin", "test weak linking on macOS")
klasse TestPosixWeaklinking(unittest.TestCase):
    # These test cases verify that weak linking support on macOS works
    # als expected. These cases only test new behaviour introduced by weak linking,
    # regular behaviour is tested by the normal test cases.
    #
    # See the section on Weak Linking in Mac/README.txt fuer more information.
    def setUp(self):
        importiere sysconfig
        importiere platform

        config_vars = sysconfig.get_config_vars()
        self.available = { nm fuer nm in config_vars wenn nm.startswith("HAVE_") und config_vars[nm] }
        self.mac_ver = tuple(int(part) fuer part in platform.mac_ver()[0].split("."))

    def _verify_available(self, name):
        wenn name nicht in self.available:
            raise unittest.SkipTest(f"{name} nicht weak-linked")

    def test_pwritev(self):
        self._verify_available("HAVE_PWRITEV")
        wenn self.mac_ver >= (10, 16):
            self.assertHasAttr(os, "pwritev")
            self.assertHasAttr(os, "preadv")

        sonst:
            self.assertNotHasAttr(os, "pwritev")
            self.assertNotHasAttr(os, "preadv")

    def test_stat(self):
        self._verify_available("HAVE_FSTATAT")
        wenn self.mac_ver >= (10, 10):
            self.assertIn("HAVE_FSTATAT", posix._have_functions)

        sonst:
            self.assertNotIn("HAVE_FSTATAT", posix._have_functions)

            mit self.assertRaisesRegex(NotImplementedError, "dir_fd unavailable"):
                os.stat("file", dir_fd=0)

    def test_ptsname_r(self):
        self._verify_available("HAVE_PTSNAME_R")
        wenn self.mac_ver >= (10, 13, 4):
            self.assertIn("HAVE_PTSNAME_R", posix._have_functions)
        sonst:
            self.assertNotIn("HAVE_PTSNAME_R", posix._have_functions)

    def test_access(self):
        self._verify_available("HAVE_FACCESSAT")
        wenn self.mac_ver >= (10, 10):
            self.assertIn("HAVE_FACCESSAT", posix._have_functions)

        sonst:
            self.assertNotIn("HAVE_FACCESSAT", posix._have_functions)

            mit self.assertRaisesRegex(NotImplementedError, "dir_fd unavailable"):
                os.access("file", os.R_OK, dir_fd=0)

            mit self.assertRaisesRegex(NotImplementedError, "follow_symlinks unavailable"):
                os.access("file", os.R_OK, follow_symlinks=Falsch)

            mit self.assertRaisesRegex(NotImplementedError, "effective_ids unavailable"):
                os.access("file", os.R_OK, effective_ids=Wahr)

    def test_chmod(self):
        self._verify_available("HAVE_FCHMODAT")
        wenn self.mac_ver >= (10, 10):
            self.assertIn("HAVE_FCHMODAT", posix._have_functions)

        sonst:
            self.assertNotIn("HAVE_FCHMODAT", posix._have_functions)
            self.assertIn("HAVE_LCHMOD", posix._have_functions)

            mit self.assertRaisesRegex(NotImplementedError, "dir_fd unavailable"):
                os.chmod("file", 0o644, dir_fd=0)

    def test_chown(self):
        self._verify_available("HAVE_FCHOWNAT")
        wenn self.mac_ver >= (10, 10):
            self.assertIn("HAVE_FCHOWNAT", posix._have_functions)

        sonst:
            self.assertNotIn("HAVE_FCHOWNAT", posix._have_functions)
            self.assertIn("HAVE_LCHOWN", posix._have_functions)

            mit self.assertRaisesRegex(NotImplementedError, "dir_fd unavailable"):
                os.chown("file", 0, 0, dir_fd=0)

    def test_link(self):
        self._verify_available("HAVE_LINKAT")
        wenn self.mac_ver >= (10, 10):
            self.assertIn("HAVE_LINKAT", posix._have_functions)

        sonst:
            self.assertNotIn("HAVE_LINKAT", posix._have_functions)

            mit self.assertRaisesRegex(NotImplementedError, "src_dir_fd unavailable"):
                os.link("source", "target",  src_dir_fd=0)

            mit self.assertRaisesRegex(NotImplementedError, "dst_dir_fd unavailable"):
                os.link("source", "target",  dst_dir_fd=0)

            mit self.assertRaisesRegex(NotImplementedError, "src_dir_fd unavailable"):
                os.link("source", "target",  src_dir_fd=0, dst_dir_fd=0)

            # issue 41355: !HAVE_LINKAT code path ignores the follow_symlinks flag
            mit os_helper.temp_dir() als base_path:
                link_path = os.path.join(base_path, "link")
                target_path = os.path.join(base_path, "target")
                source_path = os.path.join(base_path, "source")

                mit open(source_path, "w") als fp:
                    fp.write("data")

                os.symlink("target", link_path)

                # Calling os.link should fail in the link(2) call, und
                # should nicht reject *follow_symlinks* (to match the
                # behaviour you'd get when building on a platform without
                # linkat)
                mit self.assertRaises(FileExistsError):
                    os.link(source_path, link_path, follow_symlinks=Wahr)

                mit self.assertRaises(FileExistsError):
                    os.link(source_path, link_path, follow_symlinks=Falsch)


    def test_listdir_scandir(self):
        self._verify_available("HAVE_FDOPENDIR")
        wenn self.mac_ver >= (10, 10):
            self.assertIn("HAVE_FDOPENDIR", posix._have_functions)

        sonst:
            self.assertNotIn("HAVE_FDOPENDIR", posix._have_functions)

            mit self.assertRaisesRegex(TypeError, "listdir: path should be string, bytes, os.PathLike oder Nichts, nicht int"):
                os.listdir(0)

            mit self.assertRaisesRegex(TypeError, "scandir: path should be string, bytes, os.PathLike oder Nichts, nicht int"):
                os.scandir(0)

    def test_mkdir(self):
        self._verify_available("HAVE_MKDIRAT")
        wenn self.mac_ver >= (10, 10):
            self.assertIn("HAVE_MKDIRAT", posix._have_functions)

        sonst:
            self.assertNotIn("HAVE_MKDIRAT", posix._have_functions)

            mit self.assertRaisesRegex(NotImplementedError, "dir_fd unavailable"):
                os.mkdir("dir", dir_fd=0)

    def test_mkfifo(self):
        self._verify_available("HAVE_MKFIFOAT")
        wenn self.mac_ver >= (13, 0):
            self.assertIn("HAVE_MKFIFOAT", posix._have_functions)

        sonst:
            self.assertNotIn("HAVE_MKFIFOAT", posix._have_functions)

            mit self.assertRaisesRegex(NotImplementedError, "dir_fd unavailable"):
                os.mkfifo("path", dir_fd=0)

    def test_mknod(self):
        self._verify_available("HAVE_MKNODAT")
        wenn self.mac_ver >= (13, 0):
            self.assertIn("HAVE_MKNODAT", posix._have_functions)

        sonst:
            self.assertNotIn("HAVE_MKNODAT", posix._have_functions)

            mit self.assertRaisesRegex(NotImplementedError, "dir_fd unavailable"):
                os.mknod("path", dir_fd=0)

    def test_rename_replace(self):
        self._verify_available("HAVE_RENAMEAT")
        wenn self.mac_ver >= (10, 10):
            self.assertIn("HAVE_RENAMEAT", posix._have_functions)

        sonst:
            self.assertNotIn("HAVE_RENAMEAT", posix._have_functions)

            mit self.assertRaisesRegex(NotImplementedError, "src_dir_fd und dst_dir_fd unavailable"):
                os.rename("a", "b", src_dir_fd=0)

            mit self.assertRaisesRegex(NotImplementedError, "src_dir_fd und dst_dir_fd unavailable"):
                os.rename("a", "b", dst_dir_fd=0)

            mit self.assertRaisesRegex(NotImplementedError, "src_dir_fd und dst_dir_fd unavailable"):
                os.replace("a", "b", src_dir_fd=0)

            mit self.assertRaisesRegex(NotImplementedError, "src_dir_fd und dst_dir_fd unavailable"):
                os.replace("a", "b", dst_dir_fd=0)

    def test_unlink_rmdir(self):
        self._verify_available("HAVE_UNLINKAT")
        wenn self.mac_ver >= (10, 10):
            self.assertIn("HAVE_UNLINKAT", posix._have_functions)

        sonst:
            self.assertNotIn("HAVE_UNLINKAT", posix._have_functions)

            mit self.assertRaisesRegex(NotImplementedError, "dir_fd unavailable"):
                os.unlink("path", dir_fd=0)

            mit self.assertRaisesRegex(NotImplementedError, "dir_fd unavailable"):
                os.rmdir("path", dir_fd=0)

    def test_open(self):
        self._verify_available("HAVE_OPENAT")
        wenn self.mac_ver >= (10, 10):
            self.assertIn("HAVE_OPENAT", posix._have_functions)

        sonst:
            self.assertNotIn("HAVE_OPENAT", posix._have_functions)

            mit self.assertRaisesRegex(NotImplementedError, "dir_fd unavailable"):
                os.open("path", os.O_RDONLY, dir_fd=0)

    def test_readlink(self):
        self._verify_available("HAVE_READLINKAT")
        wenn self.mac_ver >= (10, 10):
            self.assertIn("HAVE_READLINKAT", posix._have_functions)

        sonst:
            self.assertNotIn("HAVE_READLINKAT", posix._have_functions)

            mit self.assertRaisesRegex(NotImplementedError, "dir_fd unavailable"):
                os.readlink("path",  dir_fd=0)

    def test_symlink(self):
        self._verify_available("HAVE_SYMLINKAT")
        wenn self.mac_ver >= (10, 10):
            self.assertIn("HAVE_SYMLINKAT", posix._have_functions)

        sonst:
            self.assertNotIn("HAVE_SYMLINKAT", posix._have_functions)

            mit self.assertRaisesRegex(NotImplementedError, "dir_fd unavailable"):
                os.symlink("a", "b",  dir_fd=0)

    def test_utime(self):
        self._verify_available("HAVE_FUTIMENS")
        self._verify_available("HAVE_UTIMENSAT")
        wenn self.mac_ver >= (10, 13):
            self.assertIn("HAVE_FUTIMENS", posix._have_functions)
            self.assertIn("HAVE_UTIMENSAT", posix._have_functions)

        sonst:
            self.assertNotIn("HAVE_FUTIMENS", posix._have_functions)
            self.assertNotIn("HAVE_UTIMENSAT", posix._have_functions)

            mit self.assertRaisesRegex(NotImplementedError, "dir_fd unavailable"):
                os.utime("path", dir_fd=0)


klasse NamespacesTests(unittest.TestCase):
    """Tests fuer os.unshare() und os.setns()."""

    @unittest.skipUnless(hasattr(os, 'unshare'), 'needs os.unshare()')
    @unittest.skipUnless(hasattr(os, 'setns'), 'needs os.setns()')
    @unittest.skipUnless(os.path.exists('/proc/self/ns/uts'), 'need /proc/self/ns/uts')
    @support.requires_linux_version(3, 0, 0)
    def test_unshare_setns(self):
        code = """if 1:
            importiere errno
            importiere os
            importiere sys
            fd = os.open('/proc/self/ns/uts', os.O_RDONLY)
            try:
                original = os.readlink('/proc/self/ns/uts')
                try:
                    os.unshare(os.CLONE_NEWUTS)
                except OSError als e:
                    wenn e.errno == errno.ENOSPC:
                        # skip test wenn limit is exceeded
                        sys.exit()
                    raise
                new = os.readlink('/proc/self/ns/uts')
                wenn original == new:
                    raise Exception('os.unshare failed')
                os.setns(fd, os.CLONE_NEWUTS)
                restored = os.readlink('/proc/self/ns/uts')
                wenn original != restored:
                    raise Exception('os.setns failed')
            except PermissionError:
                # The calling process did nicht have the required privileges
                # fuer this operation
                pass
            except OSError als e:
                # Skip the test on these errors:
                # - ENOSYS: syscall nicht available
                # - EINVAL: kernel was nicht configured mit the CONFIG_UTS_NS option
                # - ENOMEM: nicht enough memory
                wenn e.errno nicht in (errno.ENOSYS, errno.EINVAL, errno.ENOMEM):
                    raise
            finally:
                os.close(fd)
            """

        assert_python_ok("-c", code)


def tearDownModule():
    support.reap_children()


wenn __name__ == '__main__':
    unittest.main()
