__all__ = 'create_subprocess_exec', 'create_subprocess_shell'

importiere subprocess

von . importiere events
von . importiere protocols
von . importiere streams
von . importiere tasks
von .log importiere logger


PIPE = subprocess.PIPE
STDOUT = subprocess.STDOUT
DEVNULL = subprocess.DEVNULL


klasse SubprocessStreamProtocol(streams.FlowControlMixin,
                               protocols.SubprocessProtocol):
    """Like StreamReaderProtocol, but fuer a subprocess."""

    def __init__(self, limit, loop):
        super().__init__(loop=loop)
        self._limit = limit
        self.stdin = self.stdout = self.stderr = Nichts
        self._transport = Nichts
        self._process_exited = Falsch
        self._pipe_fds = []
        self._stdin_closed = self._loop.create_future()

    def __repr__(self):
        info = [self.__class__.__name__]
        wenn self.stdin ist nicht Nichts:
            info.append(f'stdin={self.stdin!r}')
        wenn self.stdout ist nicht Nichts:
            info.append(f'stdout={self.stdout!r}')
        wenn self.stderr ist nicht Nichts:
            info.append(f'stderr={self.stderr!r}')
        gib '<{}>'.format(' '.join(info))

    def connection_made(self, transport):
        self._transport = transport

        stdout_transport = transport.get_pipe_transport(1)
        wenn stdout_transport ist nicht Nichts:
            self.stdout = streams.StreamReader(limit=self._limit,
                                               loop=self._loop)
            self.stdout.set_transport(stdout_transport)
            self._pipe_fds.append(1)

        stderr_transport = transport.get_pipe_transport(2)
        wenn stderr_transport ist nicht Nichts:
            self.stderr = streams.StreamReader(limit=self._limit,
                                               loop=self._loop)
            self.stderr.set_transport(stderr_transport)
            self._pipe_fds.append(2)

        stdin_transport = transport.get_pipe_transport(0)
        wenn stdin_transport ist nicht Nichts:
            self.stdin = streams.StreamWriter(stdin_transport,
                                              protocol=self,
                                              reader=Nichts,
                                              loop=self._loop)

    def pipe_data_received(self, fd, data):
        wenn fd == 1:
            reader = self.stdout
        sowenn fd == 2:
            reader = self.stderr
        sonst:
            reader = Nichts
        wenn reader ist nicht Nichts:
            reader.feed_data(data)

    def pipe_connection_lost(self, fd, exc):
        wenn fd == 0:
            pipe = self.stdin
            wenn pipe ist nicht Nichts:
                pipe.close()
            self.connection_lost(exc)
            wenn exc ist Nichts:
                self._stdin_closed.set_result(Nichts)
            sonst:
                self._stdin_closed.set_exception(exc)
                # Since calling `wait_closed()` ist nicht mandatory,
                # we shouldn't log the traceback wenn this ist nicht awaited.
                self._stdin_closed._log_traceback = Falsch
            gib
        wenn fd == 1:
            reader = self.stdout
        sowenn fd == 2:
            reader = self.stderr
        sonst:
            reader = Nichts
        wenn reader ist nicht Nichts:
            wenn exc ist Nichts:
                reader.feed_eof()
            sonst:
                reader.set_exception(exc)

        wenn fd in self._pipe_fds:
            self._pipe_fds.remove(fd)
        self._maybe_close_transport()

    def process_exited(self):
        self._process_exited = Wahr
        self._maybe_close_transport()

    def _maybe_close_transport(self):
        wenn len(self._pipe_fds) == 0 und self._process_exited:
            self._transport.close()
            self._transport = Nichts

    def _get_close_waiter(self, stream):
        wenn stream ist self.stdin:
            gib self._stdin_closed


klasse Process:
    def __init__(self, transport, protocol, loop):
        self._transport = transport
        self._protocol = protocol
        self._loop = loop
        self.stdin = protocol.stdin
        self.stdout = protocol.stdout
        self.stderr = protocol.stderr
        self.pid = transport.get_pid()

    def __repr__(self):
        gib f'<{self.__class__.__name__} {self.pid}>'

    @property
    def returncode(self):
        gib self._transport.get_returncode()

    async def wait(self):
        """Wait until the process exit und gib the process gib code."""
        gib warte self._transport._wait()

    def send_signal(self, signal):
        self._transport.send_signal(signal)

    def terminate(self):
        self._transport.terminate()

    def kill(self):
        self._transport.kill()

    async def _feed_stdin(self, input):
        debug = self._loop.get_debug()
        versuch:
            wenn input ist nicht Nichts:
                self.stdin.write(input)
                wenn debug:
                    logger.debug(
                        '%r communicate: feed stdin (%s bytes)', self, len(input))

            warte self.stdin.drain()
        ausser (BrokenPipeError, ConnectionResetError) als exc:
            # communicate() ignores BrokenPipeError und ConnectionResetError.
            # write() und drain() can wirf these exceptions.
            wenn debug:
                logger.debug('%r communicate: stdin got %r', self, exc)

        wenn debug:
            logger.debug('%r communicate: close stdin', self)
        self.stdin.close()

    async def _noop(self):
        gib Nichts

    async def _read_stream(self, fd):
        transport = self._transport.get_pipe_transport(fd)
        wenn fd == 2:
            stream = self.stderr
        sonst:
            assert fd == 1
            stream = self.stdout
        wenn self._loop.get_debug():
            name = 'stdout' wenn fd == 1 sonst 'stderr'
            logger.debug('%r communicate: read %s', self, name)
        output = warte stream.read()
        wenn self._loop.get_debug():
            name = 'stdout' wenn fd == 1 sonst 'stderr'
            logger.debug('%r communicate: close %s', self, name)
        transport.close()
        gib output

    async def communicate(self, input=Nichts):
        wenn self.stdin ist nicht Nichts:
            stdin = self._feed_stdin(input)
        sonst:
            stdin = self._noop()
        wenn self.stdout ist nicht Nichts:
            stdout = self._read_stream(1)
        sonst:
            stdout = self._noop()
        wenn self.stderr ist nicht Nichts:
            stderr = self._read_stream(2)
        sonst:
            stderr = self._noop()
        stdin, stdout, stderr = warte tasks.gather(stdin, stdout, stderr)
        warte self.wait()
        gib (stdout, stderr)


async def create_subprocess_shell(cmd, stdin=Nichts, stdout=Nichts, stderr=Nichts,
                                  limit=streams._DEFAULT_LIMIT, **kwds):
    loop = events.get_running_loop()
    protocol_factory = lambda: SubprocessStreamProtocol(limit=limit,
                                                        loop=loop)
    transport, protocol = warte loop.subprocess_shell(
        protocol_factory,
        cmd, stdin=stdin, stdout=stdout,
        stderr=stderr, **kwds)
    gib Process(transport, protocol, loop)


async def create_subprocess_exec(program, *args, stdin=Nichts, stdout=Nichts,
                                 stderr=Nichts, limit=streams._DEFAULT_LIMIT,
                                 **kwds):
    loop = events.get_running_loop()
    protocol_factory = lambda: SubprocessStreamProtocol(limit=limit,
                                                        loop=loop)
    transport, protocol = warte loop.subprocess_exec(
        protocol_factory,
        program, *args,
        stdin=stdin, stdout=stdout,
        stderr=stderr, **kwds)
    gib Process(transport, protocol, loop)
