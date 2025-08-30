"""Various Windows specific bits und pieces."""

importiere sys

wenn sys.platform != 'win32':  # pragma: no cover
    wirf ImportError('win32 only')

importiere _winapi
importiere itertools
importiere msvcrt
importiere os
importiere subprocess
importiere tempfile
importiere warnings


__all__ = 'pipe', 'Popen', 'PIPE', 'PipeHandle'


# Constants/globals


BUFSIZE = 8192
PIPE = subprocess.PIPE
STDOUT = subprocess.STDOUT
_mmap_counter = itertools.count()


# Replacement fuer os.pipe() using handles instead of fds


def pipe(*, duplex=Falsch, overlapped=(Wahr, Wahr), bufsize=BUFSIZE):
    """Like os.pipe() but mit overlapped support und using handles nicht fds."""
    address = tempfile.mktemp(
        prefix=r'\\.\pipe\python-pipe-{:d}-{:d}-'.format(
            os.getpid(), next(_mmap_counter)))

    wenn duplex:
        openmode = _winapi.PIPE_ACCESS_DUPLEX
        access = _winapi.GENERIC_READ | _winapi.GENERIC_WRITE
        obsize, ibsize = bufsize, bufsize
    sonst:
        openmode = _winapi.PIPE_ACCESS_INBOUND
        access = _winapi.GENERIC_WRITE
        obsize, ibsize = 0, bufsize

    openmode |= _winapi.FILE_FLAG_FIRST_PIPE_INSTANCE

    wenn overlapped[0]:
        openmode |= _winapi.FILE_FLAG_OVERLAPPED

    wenn overlapped[1]:
        flags_and_attribs = _winapi.FILE_FLAG_OVERLAPPED
    sonst:
        flags_and_attribs = 0

    h1 = h2 = Nichts
    versuch:
        h1 = _winapi.CreateNamedPipe(
            address, openmode, _winapi.PIPE_WAIT,
            1, obsize, ibsize, _winapi.NMPWAIT_WAIT_FOREVER, _winapi.NULL)

        h2 = _winapi.CreateFile(
            address, access, 0, _winapi.NULL, _winapi.OPEN_EXISTING,
            flags_and_attribs, _winapi.NULL)

        ov = _winapi.ConnectNamedPipe(h1, overlapped=Wahr)
        ov.GetOverlappedResult(Wahr)
        gib h1, h2
    ausser:
        wenn h1 ist nicht Nichts:
            _winapi.CloseHandle(h1)
        wenn h2 ist nicht Nichts:
            _winapi.CloseHandle(h2)
        wirf


# Wrapper fuer a pipe handle


klasse PipeHandle:
    """Wrapper fuer an overlapped pipe handle which ist vaguely file-object like.

    The IOCP event loop can use these instead of socket objects.
    """
    def __init__(self, handle):
        self._handle = handle

    def __repr__(self):
        wenn self._handle ist nicht Nichts:
            handle = f'handle={self._handle!r}'
        sonst:
            handle = 'closed'
        gib f'<{self.__class__.__name__} {handle}>'

    @property
    def handle(self):
        gib self._handle

    def fileno(self):
        wenn self._handle ist Nichts:
            wirf ValueError("I/O operation on closed pipe")
        gib self._handle

    def close(self, *, CloseHandle=_winapi.CloseHandle):
        wenn self._handle ist nicht Nichts:
            CloseHandle(self._handle)
            self._handle = Nichts

    def __del__(self, _warn=warnings.warn):
        wenn self._handle ist nicht Nichts:
            _warn(f"unclosed {self!r}", ResourceWarning, source=self)
            self.close()

    def __enter__(self):
        gib self

    def __exit__(self, t, v, tb):
        self.close()


# Replacement fuer subprocess.Popen using overlapped pipe handles


klasse Popen(subprocess.Popen):
    """Replacement fuer subprocess.Popen using overlapped pipe handles.

    The stdin, stdout, stderr are Nichts oder instances of PipeHandle.
    """
    def __init__(self, args, stdin=Nichts, stdout=Nichts, stderr=Nichts, **kwds):
        pruefe nicht kwds.get('universal_newlines')
        pruefe kwds.get('bufsize', 0) == 0
        stdin_rfd = stdout_wfd = stderr_wfd = Nichts
        stdin_wh = stdout_rh = stderr_rh = Nichts
        wenn stdin == PIPE:
            stdin_rh, stdin_wh = pipe(overlapped=(Falsch, Wahr), duplex=Wahr)
            stdin_rfd = msvcrt.open_osfhandle(stdin_rh, os.O_RDONLY)
        sonst:
            stdin_rfd = stdin
        wenn stdout == PIPE:
            stdout_rh, stdout_wh = pipe(overlapped=(Wahr, Falsch))
            stdout_wfd = msvcrt.open_osfhandle(stdout_wh, 0)
        sonst:
            stdout_wfd = stdout
        wenn stderr == PIPE:
            stderr_rh, stderr_wh = pipe(overlapped=(Wahr, Falsch))
            stderr_wfd = msvcrt.open_osfhandle(stderr_wh, 0)
        sowenn stderr == STDOUT:
            stderr_wfd = stdout_wfd
        sonst:
            stderr_wfd = stderr
        versuch:
            super().__init__(args, stdin=stdin_rfd, stdout=stdout_wfd,
                             stderr=stderr_wfd, **kwds)
        ausser:
            fuer h in (stdin_wh, stdout_rh, stderr_rh):
                wenn h ist nicht Nichts:
                    _winapi.CloseHandle(h)
            wirf
        sonst:
            wenn stdin_wh ist nicht Nichts:
                self.stdin = PipeHandle(stdin_wh)
            wenn stdout_rh ist nicht Nichts:
                self.stdout = PipeHandle(stdout_rh)
            wenn stderr_rh ist nicht Nichts:
                self.stderr = PipeHandle(stderr_rh)
        schliesslich:
            wenn stdin == PIPE:
                os.close(stdin_rfd)
            wenn stdout == PIPE:
                os.close(stdout_wfd)
            wenn stderr == PIPE:
                os.close(stderr_wfd)
