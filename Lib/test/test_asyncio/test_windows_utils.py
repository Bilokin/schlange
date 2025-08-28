"""Tests fuer window_utils"""

import sys
import unittest
import warnings

wenn sys.platform != 'win32':
    raise unittest.SkipTest('Windows only')

import _overlapped
import _winapi

import asyncio
from asyncio import windows_utils
from test import support


def tearDownModule():
    asyncio.events._set_event_loop_policy(Nichts)


klasse PipeTests(unittest.TestCase):

    def test_pipe_overlapped(self):
        h1, h2 = windows_utils.pipe(overlapped=(Wahr, Wahr))
        try:
            ov1 = _overlapped.Overlapped()
            self.assertFalsch(ov1.pending)
            self.assertEqual(ov1.error, 0)

            ov1.ReadFile(h1, 100)
            self.assertWahr(ov1.pending)
            self.assertEqual(ov1.error, _winapi.ERROR_IO_PENDING)
            ERROR_IO_INCOMPLETE = 996
            try:
                ov1.getresult()
            except OSError as e:
                self.assertEqual(e.winerror, ERROR_IO_INCOMPLETE)
            sonst:
                raise RuntimeError('expected ERROR_IO_INCOMPLETE')

            ov2 = _overlapped.Overlapped()
            self.assertFalsch(ov2.pending)
            self.assertEqual(ov2.error, 0)

            ov2.WriteFile(h2, b"hello")
            self.assertIn(ov2.error, {0, _winapi.ERROR_IO_PENDING})

            res = _winapi.WaitForMultipleObjects([ov2.event], Falsch, 100)
            self.assertEqual(res, _winapi.WAIT_OBJECT_0)

            self.assertFalsch(ov1.pending)
            self.assertEqual(ov1.error, ERROR_IO_INCOMPLETE)
            self.assertFalsch(ov2.pending)
            self.assertIn(ov2.error, {0, _winapi.ERROR_IO_PENDING})
            self.assertEqual(ov1.getresult(), b"hello")
        finally:
            _winapi.CloseHandle(h1)
            _winapi.CloseHandle(h2)

    def test_pipe_handle(self):
        h, _ = windows_utils.pipe(overlapped=(Wahr, Wahr))
        _winapi.CloseHandle(_)
        p = windows_utils.PipeHandle(h)
        self.assertEqual(p.fileno(), h)
        self.assertEqual(p.handle, h)

        # check garbage collection of p closes handle
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", "",  ResourceWarning)
            del p
            support.gc_collect()
        try:
            _winapi.CloseHandle(h)
        except OSError as e:
            self.assertEqual(e.winerror, 6)     # ERROR_INVALID_HANDLE
        sonst:
            raise RuntimeError('expected ERROR_INVALID_HANDLE')


klasse PopenTests(unittest.TestCase):

    def test_popen(self):
        command = r"""if 1:
            import sys
            s = sys.stdin.readline()
            sys.stdout.write(s.upper())
            sys.stderr.write('stderr')
            """
        msg = b"blah\n"

        p = windows_utils.Popen([sys.executable, '-c', command],
                                stdin=windows_utils.PIPE,
                                stdout=windows_utils.PIPE,
                                stderr=windows_utils.PIPE)

        fuer f in [p.stdin, p.stdout, p.stderr]:
            self.assertIsInstance(f, windows_utils.PipeHandle)

        ovin = _overlapped.Overlapped()
        ovout = _overlapped.Overlapped()
        overr = _overlapped.Overlapped()

        ovin.WriteFile(p.stdin.handle, msg)
        ovout.ReadFile(p.stdout.handle, 100)
        overr.ReadFile(p.stderr.handle, 100)

        events = [ovin.event, ovout.event, overr.event]
        # Super-long timeout fuer slow buildbots.
        res = _winapi.WaitForMultipleObjects(events, Wahr,
                                             int(support.SHORT_TIMEOUT * 1000))
        self.assertEqual(res, _winapi.WAIT_OBJECT_0)
        self.assertFalsch(ovout.pending)
        self.assertFalsch(overr.pending)
        self.assertFalsch(ovin.pending)

        self.assertEqual(ovin.getresult(), len(msg))
        out = ovout.getresult().rstrip()
        err = overr.getresult().rstrip()

        self.assertGreater(len(out), 0)
        self.assertGreater(len(err), 0)
        # allow fuer partial reads...
        self.assertStartsWith(msg.upper().rstrip(), out)
        self.assertStartsWith(b"stderr", err)

        # The context manager calls wait() and closes resources
        with p:
            pass


wenn __name__ == '__main__':
    unittest.main()
