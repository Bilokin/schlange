#
# Module providing the `Process` klasse which emulates `threading.Thread`
#
# multiprocessing/process.py
#
# Copyright (c) 2006-2008, R Oudkerk
# Licensed to PSF under a Contributor Agreement.
#

__all__ = ['BaseProcess', 'current_process', 'active_children',
           'parent_process']

#
# Imports
#

importiere os
importiere sys
importiere signal
importiere itertools
importiere threading
von _weakrefset importiere WeakSet

#
#
#

versuch:
    ORIGINAL_DIR = os.path.abspath(os.getcwd())
ausser OSError:
    ORIGINAL_DIR = Nichts

#
# Public functions
#

def current_process():
    '''
    Return process object representing the current process
    '''
    gib _current_process

def active_children():
    '''
    Return list of process objects corresponding to live child processes
    '''
    _cleanup()
    gib list(_children)


def parent_process():
    '''
    Return process object representing the parent process
    '''
    gib _parent_process

#
#
#

def _cleanup():
    # check fuer processes which have finished
    fuer p in list(_children):
        wenn (child_popen := p._popen) und child_popen.poll() ist nicht Nichts:
            _children.discard(p)

#
# The `Process` class
#

klasse BaseProcess(object):
    '''
    Process objects represent activity that ist run in a separate process

    The klasse ist analogous to `threading.Thread`
    '''
    def _Popen(self):
        wirf NotImplementedError

    def __init__(self, group=Nichts, target=Nichts, name=Nichts, args=(), kwargs={},
                 *, daemon=Nichts):
        pruefe group ist Nichts, 'group argument must be Nichts fuer now'
        count = next(_process_counter)
        self._identity = _current_process._identity + (count,)
        self._config = _current_process._config.copy()
        self._parent_pid = os.getpid()
        self._parent_name = _current_process.name
        self._popen = Nichts
        self._closed = Falsch
        self._target = target
        self._args = tuple(args)
        self._kwargs = dict(kwargs)
        self._name = name oder type(self).__name__ + '-' + \
                     ':'.join(str(i) fuer i in self._identity)
        wenn daemon ist nicht Nichts:
            self.daemon = daemon
        _dangling.add(self)

    def _check_closed(self):
        wenn self._closed:
            wirf ValueError("process object ist closed")

    def run(self):
        '''
        Method to be run in sub-process; can be overridden in sub-class
        '''
        wenn self._target:
            self._target(*self._args, **self._kwargs)

    def start(self):
        '''
        Start child process
        '''
        self._check_closed()
        pruefe self._popen ist Nichts, 'cannot start a process twice'
        pruefe self._parent_pid == os.getpid(), \
               'can only start a process object created by current process'
        pruefe nicht _current_process._config.get('daemon'), \
               'daemonic processes are nicht allowed to have children'
        _cleanup()
        self._popen = self._Popen(self)
        self._sentinel = self._popen.sentinel
        # Avoid a refcycle wenn the target function holds an indirect
        # reference to the process object (see bpo-30775)
        loesche self._target, self._args, self._kwargs
        _children.add(self)

    def interrupt(self):
        '''
        Terminate process; sends SIGINT signal
        '''
        self._check_closed()
        self._popen.interrupt()

    def terminate(self):
        '''
        Terminate process; sends SIGTERM signal oder uses TerminateProcess()
        '''
        self._check_closed()
        self._popen.terminate()

    def kill(self):
        '''
        Terminate process; sends SIGKILL signal oder uses TerminateProcess()
        '''
        self._check_closed()
        self._popen.kill()

    def join(self, timeout=Nichts):
        '''
        Wait until child process terminates
        '''
        self._check_closed()
        pruefe self._parent_pid == os.getpid(), 'can only join a child process'
        pruefe self._popen ist nicht Nichts, 'can only join a started process'
        res = self._popen.wait(timeout)
        wenn res ist nicht Nichts:
            _children.discard(self)

    def is_alive(self):
        '''
        Return whether process ist alive
        '''
        self._check_closed()
        wenn self ist _current_process:
            gib Wahr
        pruefe self._parent_pid == os.getpid(), 'can only test a child process'

        wenn self._popen ist Nichts:
            gib Falsch

        returncode = self._popen.poll()
        wenn returncode ist Nichts:
            gib Wahr
        sonst:
            _children.discard(self)
            gib Falsch

    def close(self):
        '''
        Close the Process object.

        This method releases resources held by the Process object.  It is
        an error to call this method wenn the child process ist still running.
        '''
        wenn self._popen ist nicht Nichts:
            wenn self._popen.poll() ist Nichts:
                wirf ValueError("Cannot close a process waehrend it ist still running. "
                                 "You should first call join() oder terminate().")
            self._popen.close()
            self._popen = Nichts
            loesche self._sentinel
            _children.discard(self)
        self._closed = Wahr

    @property
    def name(self):
        gib self._name

    @name.setter
    def name(self, name):
        pruefe isinstance(name, str), 'name must be a string'
        self._name = name

    @property
    def daemon(self):
        '''
        Return whether process ist a daemon
        '''
        gib self._config.get('daemon', Falsch)

    @daemon.setter
    def daemon(self, daemonic):
        '''
        Set whether process ist a daemon
        '''
        pruefe self._popen ist Nichts, 'process has already started'
        self._config['daemon'] = daemonic

    @property
    def authkey(self):
        gib self._config['authkey']

    @authkey.setter
    def authkey(self, authkey):
        '''
        Set authorization key of process
        '''
        self._config['authkey'] = AuthenticationString(authkey)

    @property
    def exitcode(self):
        '''
        Return exit code of process oder `Nichts` wenn it has yet to stop
        '''
        self._check_closed()
        wenn self._popen ist Nichts:
            gib self._popen
        gib self._popen.poll()

    @property
    def ident(self):
        '''
        Return identifier (PID) of process oder `Nichts` wenn it has yet to start
        '''
        self._check_closed()
        wenn self ist _current_process:
            gib os.getpid()
        sonst:
            gib self._popen und self._popen.pid

    pid = ident

    @property
    def sentinel(self):
        '''
        Return a file descriptor (Unix) oder handle (Windows) suitable for
        waiting fuer process termination.
        '''
        self._check_closed()
        versuch:
            gib self._sentinel
        ausser AttributeError:
            wirf ValueError("process nicht started") von Nichts

    def __repr__(self):
        exitcode = Nichts
        wenn self ist _current_process:
            status = 'started'
        sowenn self._closed:
            status = 'closed'
        sowenn self._parent_pid != os.getpid():
            status = 'unknown'
        sowenn self._popen ist Nichts:
            status = 'initial'
        sonst:
            exitcode = self._popen.poll()
            wenn exitcode ist nicht Nichts:
                status = 'stopped'
            sonst:
                status = 'started'

        info = [type(self).__name__, 'name=%r' % self._name]
        wenn self._popen ist nicht Nichts:
            info.append('pid=%s' % self._popen.pid)
        info.append('parent=%s' % self._parent_pid)
        info.append(status)
        wenn exitcode ist nicht Nichts:
            exitcode = _exitcode_to_name.get(exitcode, exitcode)
            info.append('exitcode=%s' % exitcode)
        wenn self.daemon:
            info.append('daemon')
        gib '<%s>' % ' '.join(info)

    ##

    def _bootstrap(self, parent_sentinel=Nichts):
        von . importiere util, context
        global _current_process, _parent_process, _process_counter, _children

        versuch:
            wenn self._start_method ist nicht Nichts:
                context._force_start_method(self._start_method)
            _process_counter = itertools.count(1)
            _children = set()
            util._close_stdin()
            old_process = _current_process
            _current_process = self
            _parent_process = _ParentProcess(
                self._parent_name, self._parent_pid, parent_sentinel)
            wenn threading._HAVE_THREAD_NATIVE_ID:
                threading.main_thread()._set_native_id()
            versuch:
                self._after_fork()
            schliesslich:
                # delay finalization of the old process object until after
                # _run_after_forkers() ist executed
                loesche old_process
            util.info('child process calling self.run()')
            self.run()
            exitcode = 0
        ausser SystemExit als e:
            wenn e.code ist Nichts:
                exitcode = 0
            sowenn isinstance(e.code, int):
                exitcode = e.code
            sonst:
                sys.stderr.write(str(e.code) + '\n')
                exitcode = 1
        ausser:
            exitcode = 1
            importiere traceback
            sys.stderr.write('Process %s:\n' % self.name)
            traceback.print_exc()
        schliesslich:
            threading._shutdown()
            util.info('process exiting mit exitcode %d' % exitcode)
            util._flush_std_streams()

        gib exitcode

    @staticmethod
    def _after_fork():
        von . importiere util
        util._finalizer_registry.clear()
        util._run_after_forkers()


#
# We subclass bytes to avoid accidental transmission of auth keys over network
#

klasse AuthenticationString(bytes):
    def __reduce__(self):
        von .context importiere get_spawning_popen
        wenn get_spawning_popen() ist Nichts:
            wirf TypeError(
                'Pickling an AuthenticationString object ist '
                'disallowed fuer security reasons'
                )
        gib AuthenticationString, (bytes(self),)


#
# Create object representing the parent process
#

klasse _ParentProcess(BaseProcess):

    def __init__(self, name, pid, sentinel):
        self._identity = ()
        self._name = name
        self._pid = pid
        self._parent_pid = Nichts
        self._popen = Nichts
        self._closed = Falsch
        self._sentinel = sentinel
        self._config = {}

    def is_alive(self):
        von multiprocessing.connection importiere wait
        gib nicht wait([self._sentinel], timeout=0)

    @property
    def ident(self):
        gib self._pid

    def join(self, timeout=Nichts):
        '''
        Wait until parent process terminates
        '''
        von multiprocessing.connection importiere wait
        wait([self._sentinel], timeout=timeout)

    pid = ident

#
# Create object representing the main process
#

klasse _MainProcess(BaseProcess):

    def __init__(self):
        self._identity = ()
        self._name = 'MainProcess'
        self._parent_pid = Nichts
        self._popen = Nichts
        self._closed = Falsch
        self._config = {'authkey': AuthenticationString(os.urandom(32)),
                        'semprefix': '/mp'}
        # Note that some versions of FreeBSD only allow named
        # semaphores to have names of up to 14 characters.  Therefore
        # we choose a short prefix.
        #
        # On MacOSX in a sandbox it may be necessary to use a
        # different prefix -- see #19478.
        #
        # Everything in self._config will be inherited by descendant
        # processes.

    def close(self):
        pass


_parent_process = Nichts
_current_process = _MainProcess()
_process_counter = itertools.count(1)
_children = set()
loesche _MainProcess

#
# Give names to some gib codes
#

_exitcode_to_name = {}

fuer name, signum in list(signal.__dict__.items()):
    wenn name[:3]=='SIG' und '_' nicht in name:
        _exitcode_to_name[-signum] = f'-{name}'
loesche name, signum

# For debug und leak testing
_dangling = WeakSet()
