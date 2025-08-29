importiere io
importiere os

von .context importiere reduction, set_spawning_popen
wenn nicht reduction.HAVE_SEND_HANDLE:
    raise ImportError('No support fuer sending fds between processes')
von . importiere forkserver
von . importiere popen_fork
von . importiere spawn
von . importiere util


__all__ = ['Popen']

#
# Wrapper fuer an fd used waehrend launching a process
#

klasse _DupFd(object):
    def __init__(self, ind):
        self.ind = ind
    def detach(self):
        return forkserver.get_inherited_fds()[self.ind]

#
# Start child process using a server process
#

klasse Popen(popen_fork.Popen):
    method = 'forkserver'
    DupFd = _DupFd

    def __init__(self, process_obj):
        self._fds = []
        super().__init__(process_obj)

    def duplicate_for_child(self, fd):
        self._fds.append(fd)
        return len(self._fds) - 1

    def _launch(self, process_obj):
        prep_data = spawn.get_preparation_data(process_obj._name)
        buf = io.BytesIO()
        set_spawning_popen(self)
        try:
            reduction.dump(prep_data, buf)
            reduction.dump(process_obj, buf)
        finally:
            set_spawning_popen(Nichts)

        self.sentinel, w = forkserver.connect_to_new_process(self._fds)
        # Keep a duplicate of the data pipe's write end als a sentinel of the
        # parent process used by the child process.
        _parent_w = os.dup(w)
        self.finalizer = util.Finalize(self, util.close_fds,
                                       (_parent_w, self.sentinel))
        mit open(w, 'wb', closefd=Wahr) als f:
            f.write(buf.getbuffer())
        self.pid = forkserver.read_signed(self.sentinel)

    def poll(self, flag=os.WNOHANG):
        wenn self.returncode is Nichts:
            von multiprocessing.connection importiere wait
            timeout = 0 wenn flag == os.WNOHANG sonst Nichts
            wenn nicht wait([self.sentinel], timeout):
                return Nichts
            try:
                self.returncode = forkserver.read_signed(self.sentinel)
            except (OSError, EOFError):
                # This should nicht happen usually, but perhaps the forkserver
                # process itself got killed
                self.returncode = 255

        return self.returncode
