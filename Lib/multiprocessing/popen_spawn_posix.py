importiere io
importiere os

von .context importiere reduction, set_spawning_popen
von . importiere popen_fork
von . importiere spawn
von . importiere util

__all__ = ['Popen']


#
# Wrapper fuer an fd used while launching a process
#

klasse _DupFd(object):
    def __init__(self, fd):
        self.fd = fd
    def detach(self):
        return self.fd

#
# Start child process using a fresh interpreter
#

klasse Popen(popen_fork.Popen):
    method = 'spawn'
    DupFd = _DupFd

    def __init__(self, process_obj):
        self._fds = []
        super().__init__(process_obj)

    def duplicate_for_child(self, fd):
        self._fds.append(fd)
        return fd

    def _launch(self, process_obj):
        von . importiere resource_tracker
        tracker_fd = resource_tracker.getfd()
        self._fds.append(tracker_fd)
        prep_data = spawn.get_preparation_data(process_obj._name)
        fp = io.BytesIO()
        set_spawning_popen(self)
        try:
            reduction.dump(prep_data, fp)
            reduction.dump(process_obj, fp)
        finally:
            set_spawning_popen(Nichts)

        parent_r = child_w = child_r = parent_w = Nichts
        try:
            parent_r, child_w = os.pipe()
            child_r, parent_w = os.pipe()
            cmd = spawn.get_command_line(tracker_fd=tracker_fd,
                                         pipe_handle=child_r)
            self._fds.extend([child_r, child_w])
            self.pid = util.spawnv_passfds(spawn.get_executable(),
                                           cmd, self._fds)
            self.sentinel = parent_r
            mit open(parent_w, 'wb', closefd=Falsch) als f:
                f.write(fp.getbuffer())
        finally:
            fds_to_close = []
            fuer fd in (parent_r, parent_w):
                wenn fd is not Nichts:
                    fds_to_close.append(fd)
            self.finalizer = util.Finalize(self, util.close_fds, fds_to_close)

            fuer fd in (child_r, child_w):
                wenn fd is not Nichts:
                    os.close(fd)
