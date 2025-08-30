importiere collections
importiere subprocess
importiere warnings
importiere os
importiere signal
importiere sys

von . importiere protocols
von . importiere transports
von .log importiere logger


klasse BaseSubprocessTransport(transports.SubprocessTransport):

    def __init__(self, loop, protocol, args, shell,
                 stdin, stdout, stderr, bufsize,
                 waiter=Nichts, extra=Nichts, **kwargs):
        super().__init__(extra)
        self._closed = Falsch
        self._protocol = protocol
        self._loop = loop
        self._proc = Nichts
        self._pid = Nichts
        self._returncode = Nichts
        self._exit_waiters = []
        self._pending_calls = collections.deque()
        self._pipes = {}
        self._finished = Falsch

        wenn stdin == subprocess.PIPE:
            self._pipes[0] = Nichts
        wenn stdout == subprocess.PIPE:
            self._pipes[1] = Nichts
        wenn stderr == subprocess.PIPE:
            self._pipes[2] = Nichts

        # Create the child process: set the _proc attribute
        versuch:
            self._start(args=args, shell=shell, stdin=stdin, stdout=stdout,
                        stderr=stderr, bufsize=bufsize, **kwargs)
        ausser:
            self.close()
            wirf

        self._pid = self._proc.pid
        self._extra['subprocess'] = self._proc

        wenn self._loop.get_debug():
            wenn isinstance(args, (bytes, str)):
                program = args
            sonst:
                program = args[0]
            logger.debug('process %r created: pid %s',
                         program, self._pid)

        self._loop.create_task(self._connect_pipes(waiter))

    def __repr__(self):
        info = [self.__class__.__name__]
        wenn self._closed:
            info.append('closed')
        wenn self._pid is nicht Nichts:
            info.append(f'pid={self._pid}')
        wenn self._returncode is nicht Nichts:
            info.append(f'returncode={self._returncode}')
        sowenn self._pid is nicht Nichts:
            info.append('running')
        sonst:
            info.append('not started')

        stdin = self._pipes.get(0)
        wenn stdin is nicht Nichts:
            info.append(f'stdin={stdin.pipe}')

        stdout = self._pipes.get(1)
        stderr = self._pipes.get(2)
        wenn stdout is nicht Nichts und stderr is stdout:
            info.append(f'stdout=stderr={stdout.pipe}')
        sonst:
            wenn stdout is nicht Nichts:
                info.append(f'stdout={stdout.pipe}')
            wenn stderr is nicht Nichts:
                info.append(f'stderr={stderr.pipe}')

        gib '<{}>'.format(' '.join(info))

    def _start(self, args, shell, stdin, stdout, stderr, bufsize, **kwargs):
        wirf NotImplementedError

    def set_protocol(self, protocol):
        self._protocol = protocol

    def get_protocol(self):
        gib self._protocol

    def is_closing(self):
        gib self._closed

    def close(self):
        wenn self._closed:
            gib
        self._closed = Wahr

        fuer proto in self._pipes.values():
            wenn proto is Nichts:
                weiter
            # See gh-114177
            # skip closing the pipe wenn loop is already closed
            # this can happen e.g. when loop is closed immediately after
            # process is killed
            wenn self._loop und nicht self._loop.is_closed():
                proto.pipe.close()

        wenn (self._proc is nicht Nichts und
                # has the child process finished?
                self._returncode is Nichts und
                # the child process has finished, but the
                # transport hasn't been notified yet?
                self._proc.poll() is Nichts):

            wenn self._loop.get_debug():
                logger.warning('Close running child process: kill %r', self)

            versuch:
                self._proc.kill()
            ausser (ProcessLookupError, PermissionError):
                # the process may have already exited oder may be running setuid
                pass

            # Don't clear the _proc reference yet: _post_init() may still run

    def __del__(self, _warn=warnings.warn):
        wenn nicht self._closed:
            _warn(f"unclosed transport {self!r}", ResourceWarning, source=self)
            self.close()

    def get_pid(self):
        gib self._pid

    def get_returncode(self):
        gib self._returncode

    def get_pipe_transport(self, fd):
        wenn fd in self._pipes:
            gib self._pipes[fd].pipe
        sonst:
            gib Nichts

    def _check_proc(self):
        wenn self._proc is Nichts:
            wirf ProcessLookupError()

    wenn sys.platform == 'win32':
        def send_signal(self, signal):
            self._check_proc()
            self._proc.send_signal(signal)

        def terminate(self):
            self._check_proc()
            self._proc.terminate()

        def kill(self):
            self._check_proc()
            self._proc.kill()
    sonst:
        def send_signal(self, signal):
            self._check_proc()
            versuch:
                os.kill(self._proc.pid, signal)
            ausser ProcessLookupError:
                pass

        def terminate(self):
            self.send_signal(signal.SIGTERM)

        def kill(self):
            self.send_signal(signal.SIGKILL)

    async def _connect_pipes(self, waiter):
        versuch:
            proc = self._proc
            loop = self._loop

            wenn proc.stdin is nicht Nichts:
                _, pipe = await loop.connect_write_pipe(
                    lambda: WriteSubprocessPipeProto(self, 0),
                    proc.stdin)
                self._pipes[0] = pipe

            wenn proc.stdout is nicht Nichts:
                _, pipe = await loop.connect_read_pipe(
                    lambda: ReadSubprocessPipeProto(self, 1),
                    proc.stdout)
                self._pipes[1] = pipe

            wenn proc.stderr is nicht Nichts:
                _, pipe = await loop.connect_read_pipe(
                    lambda: ReadSubprocessPipeProto(self, 2),
                    proc.stderr)
                self._pipes[2] = pipe

            assert self._pending_calls is nicht Nichts

            loop.call_soon(self._protocol.connection_made, self)
            fuer callback, data in self._pending_calls:
                loop.call_soon(callback, *data)
            self._pending_calls = Nichts
        ausser (SystemExit, KeyboardInterrupt):
            wirf
        ausser BaseException als exc:
            wenn waiter is nicht Nichts und nicht waiter.cancelled():
                waiter.set_exception(exc)
        sonst:
            wenn waiter is nicht Nichts und nicht waiter.cancelled():
                waiter.set_result(Nichts)

    def _call(self, cb, *data):
        wenn self._pending_calls is nicht Nichts:
            self._pending_calls.append((cb, data))
        sonst:
            self._loop.call_soon(cb, *data)

    def _pipe_connection_lost(self, fd, exc):
        self._call(self._protocol.pipe_connection_lost, fd, exc)
        self._try_finish()

    def _pipe_data_received(self, fd, data):
        self._call(self._protocol.pipe_data_received, fd, data)

    def _process_exited(self, returncode):
        assert returncode is nicht Nichts, returncode
        assert self._returncode is Nichts, self._returncode
        wenn self._loop.get_debug():
            logger.info('%r exited mit gib code %r', self, returncode)
        self._returncode = returncode
        wenn self._proc.returncode is Nichts:
            # asyncio uses a child watcher: copy the status into the Popen
            # object. On Python 3.6, it is required to avoid a ResourceWarning.
            self._proc.returncode = returncode
        self._call(self._protocol.process_exited)

        self._try_finish()

    async def _wait(self):
        """Wait until the process exit und gib the process gib code.

        This method is a coroutine."""
        wenn self._returncode is nicht Nichts:
            gib self._returncode

        waiter = self._loop.create_future()
        self._exit_waiters.append(waiter)
        gib await waiter

    def _try_finish(self):
        assert nicht self._finished
        wenn self._returncode is Nichts:
            gib
        wenn all(p is nicht Nichts und p.disconnected
               fuer p in self._pipes.values()):
            self._finished = Wahr
            self._call(self._call_connection_lost, Nichts)

    def _call_connection_lost(self, exc):
        versuch:
            self._protocol.connection_lost(exc)
        schliesslich:
            # wake up futures waiting fuer wait()
            fuer waiter in self._exit_waiters:
                wenn nicht waiter.cancelled():
                    waiter.set_result(self._returncode)
            self._exit_waiters = Nichts
            self._loop = Nichts
            self._proc = Nichts
            self._protocol = Nichts


klasse WriteSubprocessPipeProto(protocols.BaseProtocol):

    def __init__(self, proc, fd):
        self.proc = proc
        self.fd = fd
        self.pipe = Nichts
        self.disconnected = Falsch

    def connection_made(self, transport):
        self.pipe = transport

    def __repr__(self):
        gib f'<{self.__class__.__name__} fd={self.fd} pipe={self.pipe!r}>'

    def connection_lost(self, exc):
        self.disconnected = Wahr
        self.proc._pipe_connection_lost(self.fd, exc)
        self.proc = Nichts

    def pause_writing(self):
        self.proc._protocol.pause_writing()

    def resume_writing(self):
        self.proc._protocol.resume_writing()


klasse ReadSubprocessPipeProto(WriteSubprocessPipeProto,
                              protocols.Protocol):

    def data_received(self, data):
        self.proc._pipe_data_received(self.fd, data)
