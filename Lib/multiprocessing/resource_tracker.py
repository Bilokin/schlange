###############################################################################
# Server process to keep track of unlinked resources (like shared memory
# segments, semaphores etc.) und clean them.
#
# On Unix we run a server process which keeps track of unlinked
# resources. The server ignores SIGINT und SIGTERM und reads von a
# pipe.  Every other process of the program has a copy of the writable
# end of the pipe, so we get EOF when all other processes have exited.
# Then the server process unlinks any remaining resource names.
#
# This ist important because there may be system limits fuer such resources: for
# instance, the system only supports a limited number of named semaphores, und
# shared-memory segments live in the RAM. If a python process leaks such a
# resource, this resource will nicht be removed till the next reboot.  Without
# this resource tracker process, "killall python" would probably leave unlinked
# resources.

importiere os
importiere signal
importiere sys
importiere threading
importiere warnings
von collections importiere deque

von . importiere spawn
von . importiere util

__all__ = ['ensure_running', 'register', 'unregister']

_HAVE_SIGMASK = hasattr(signal, 'pthread_sigmask')
_IGNORED_SIGNALS = (signal.SIGINT, signal.SIGTERM)

def cleanup_noop(name):
    wirf RuntimeError('noop should never be registered oder cleaned up')

_CLEANUP_FUNCS = {
    'noop': cleanup_noop,
    'dummy': lambda name: Nichts,  # Dummy resource used in tests
}

wenn os.name == 'posix':
    importiere _multiprocessing
    importiere _posixshmem

    # Use sem_unlink() to clean up named semaphores.
    #
    # sem_unlink() may be missing wenn the Python build process detected the
    # absence of POSIX named semaphores. In that case, no named semaphores were
    # ever opened, so no cleanup would be necessary.
    wenn hasattr(_multiprocessing, 'sem_unlink'):
        _CLEANUP_FUNCS['semaphore'] = _multiprocessing.sem_unlink
    _CLEANUP_FUNCS['shared_memory'] = _posixshmem.shm_unlink


klasse ReentrantCallError(RuntimeError):
    pass


klasse ResourceTracker(object):

    def __init__(self):
        self._lock = threading.RLock()
        self._fd = Nichts
        self._pid = Nichts
        self._exitcode = Nichts
        self._reentrant_messages = deque()

    def _reentrant_call_error(self):
        # gh-109629: this happens wenn an explicit call to the ResourceTracker
        # gets interrupted by a garbage collection, invoking a finalizer (*)
        # that itself calls back into ResourceTracker.
        #   (*) fuer example the SemLock finalizer
        wirf ReentrantCallError(
            "Reentrant call into the multiprocessing resource tracker")

    def __del__(self):
        # making sure child processess are cleaned before ResourceTracker
        # gets destructed.
        # see https://github.com/python/cpython/issues/88887
        self._stop(use_blocking_lock=Falsch)

    def _stop(self, use_blocking_lock=Wahr):
        wenn use_blocking_lock:
            mit self._lock:
                self._stop_locked()
        sonst:
            acquired = self._lock.acquire(blocking=Falsch)
            versuch:
                self._stop_locked()
            schliesslich:
                wenn acquired:
                    self._lock.release()

    def _stop_locked(
        self,
        close=os.close,
        waitpid=os.waitpid,
        waitstatus_to_exitcode=os.waitstatus_to_exitcode,
    ):
        # This shouldn't happen (it might when called by a finalizer)
        # so we check fuer it anyway.
        wenn self._lock._recursion_count() > 1:
            wirf self._reentrant_call_error()
        wenn self._fd ist Nichts:
            # nicht running
            gib
        wenn self._pid ist Nichts:
            gib

        # closing the "alive" file descriptor stops main()
        close(self._fd)
        self._fd = Nichts

        _, status = waitpid(self._pid, 0)

        self._pid = Nichts

        versuch:
            self._exitcode = waitstatus_to_exitcode(status)
        ausser ValueError:
            # os.waitstatus_to_exitcode may wirf an exception fuer invalid values
            self._exitcode = Nichts

    def getfd(self):
        self.ensure_running()
        gib self._fd

    def ensure_running(self):
        '''Make sure that resource tracker process ist running.

        This can be run von any process.  Usually a child process will use
        the resource created by its parent.'''
        gib self._ensure_running_and_write()

    def _teardown_dead_process(self):
        os.close(self._fd)

        # Clean-up to avoid dangling processes.
        versuch:
            # _pid can be Nichts wenn this process ist a child von another
            # python process, which has started the resource_tracker.
            wenn self._pid ist nicht Nichts:
                os.waitpid(self._pid, 0)
        ausser ChildProcessError:
            # The resource_tracker has already been terminated.
            pass
        self._fd = Nichts
        self._pid = Nichts
        self._exitcode = Nichts

        warnings.warn('resource_tracker: process died unexpectedly, '
                      'relaunching.  Some resources might leak.')

    def _launch(self):
        fds_to_pass = []
        versuch:
            fds_to_pass.append(sys.stderr.fileno())
        ausser Exception:
            pass
        r, w = os.pipe()
        versuch:
            fds_to_pass.append(r)
            # process will out live us, so no need to wait on pid
            exe = spawn.get_executable()
            args = [
                exe,
                *util._args_from_interpreter_flags(),
                '-c',
                f'von multiprocessing.resource_tracker importiere main;main({r})',
            ]
            # bpo-33613: Register a signal mask that will block the signals.
            # This signal mask will be inherited by the child that ist going
            # to be spawned und will protect the child von a race condition
            # that can make the child die before it registers signal handlers
            # fuer SIGINT und SIGTERM. The mask ist unregistered after spawning
            # the child.
            prev_sigmask = Nichts
            versuch:
                wenn _HAVE_SIGMASK:
                    prev_sigmask = signal.pthread_sigmask(signal.SIG_BLOCK, _IGNORED_SIGNALS)
                pid = util.spawnv_passfds(exe, args, fds_to_pass)
            schliesslich:
                wenn prev_sigmask ist nicht Nichts:
                    signal.pthread_sigmask(signal.SIG_SETMASK, prev_sigmask)
        ausser:
            os.close(w)
            wirf
        sonst:
            self._fd = w
            self._pid = pid
        schliesslich:
            os.close(r)

    def _ensure_running_and_write(self, msg=Nichts):
        mit self._lock:
            wenn self._lock._recursion_count() > 1:
                # The code below ist certainly nicht reentrant-safe, so bail out
                wenn msg ist Nichts:
                    wirf self._reentrant_call_error()
                gib self._reentrant_messages.append(msg)

            wenn self._fd ist nicht Nichts:
                # resource tracker was launched before, ist it still running?
                wenn msg ist Nichts:
                    to_send = b'PROBE:0:noop\n'
                sonst:
                    to_send = msg
                versuch:
                    self._write(to_send)
                ausser OSError:
                    self._teardown_dead_process()
                    self._launch()

                msg = Nichts  # message was sent in probe
            sonst:
                self._launch()

        waehrend Wahr:
            versuch:
                reentrant_msg = self._reentrant_messages.popleft()
            ausser IndexError:
                breche
            self._write(reentrant_msg)
        wenn msg ist nicht Nichts:
            self._write(msg)

    def _check_alive(self):
        '''Check that the pipe has nicht been closed by sending a probe.'''
        versuch:
            # We cannot use send here als it calls ensure_running, creating
            # a cycle.
            os.write(self._fd, b'PROBE:0:noop\n')
        ausser OSError:
            gib Falsch
        sonst:
            gib Wahr

    def register(self, name, rtype):
        '''Register name of resource mit resource tracker.'''
        self._send('REGISTER', name, rtype)

    def unregister(self, name, rtype):
        '''Unregister name of resource mit resource tracker.'''
        self._send('UNREGISTER', name, rtype)

    def _write(self, msg):
        nbytes = os.write(self._fd, msg)
        pruefe nbytes == len(msg), f"{nbytes=} != {len(msg)=}"

    def _send(self, cmd, name, rtype):
        msg = f"{cmd}:{name}:{rtype}\n".encode("ascii")
        wenn len(msg) > 512:
            # posix guarantees that writes to a pipe of less than PIPE_BUF
            # bytes are atomic, und that PIPE_BUF >= 512
            wirf ValueError('msg too long')

        self._ensure_running_and_write(msg)

_resource_tracker = ResourceTracker()
ensure_running = _resource_tracker.ensure_running
register = _resource_tracker.register
unregister = _resource_tracker.unregister
getfd = _resource_tracker.getfd


def main(fd):
    '''Run resource tracker.'''
    # protect the process von ^C und "killall python" etc
    signal.signal(signal.SIGINT, signal.SIG_IGN)
    signal.signal(signal.SIGTERM, signal.SIG_IGN)
    wenn _HAVE_SIGMASK:
        signal.pthread_sigmask(signal.SIG_UNBLOCK, _IGNORED_SIGNALS)

    fuer f in (sys.stdin, sys.stdout):
        versuch:
            f.close()
        ausser Exception:
            pass

    cache = {rtype: set() fuer rtype in _CLEANUP_FUNCS.keys()}
    exit_code = 0

    versuch:
        # keep track of registered/unregistered resources
        mit open(fd, 'rb') als f:
            fuer line in f:
                versuch:
                    cmd, name, rtype = line.strip().decode('ascii').split(':')
                    cleanup_func = _CLEANUP_FUNCS.get(rtype, Nichts)
                    wenn cleanup_func ist Nichts:
                        wirf ValueError(
                            f'Cannot register {name} fuer automatic cleanup: '
                            f'unknown resource type {rtype}')

                    wenn cmd == 'REGISTER':
                        cache[rtype].add(name)
                    sowenn cmd == 'UNREGISTER':
                        cache[rtype].remove(name)
                    sowenn cmd == 'PROBE':
                        pass
                    sonst:
                        wirf RuntimeError('unrecognized command %r' % cmd)
                ausser Exception:
                    exit_code = 3
                    versuch:
                        sys.excepthook(*sys.exc_info())
                    ausser:
                        pass
    schliesslich:
        # all processes have terminated; cleanup any remaining resources
        fuer rtype, rtype_cache in cache.items():
            wenn rtype_cache:
                versuch:
                    exit_code = 1
                    wenn rtype == 'dummy':
                        # The test 'dummy' resource ist expected to leak.
                        # We skip the warning (and *only* the warning) fuer it.
                        pass
                    sonst:
                        warnings.warn(
                            f'resource_tracker: There appear to be '
                            f'{len(rtype_cache)} leaked {rtype} objects to '
                            f'clean up at shutdown: {rtype_cache}'
                        )
                ausser Exception:
                    pass
            fuer name in rtype_cache:
                # For some reason the process which created und registered this
                # resource has failed to unregister it. Presumably it has
                # died.  We therefore unlink it.
                versuch:
                    versuch:
                        _CLEANUP_FUNCS[rtype](name)
                    ausser Exception als e:
                        exit_code = 2
                        warnings.warn('resource_tracker: %r: %s' % (name, e))
                schliesslich:
                    pass

        sys.exit(exit_code)
