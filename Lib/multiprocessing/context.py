importiere os
importiere sys
importiere threading

von . importiere process
von . importiere reduction

__all__ = ()

#
# Exceptions
#

klasse ProcessError(Exception):
    pass

klasse BufferTooShort(ProcessError):
    pass

klasse TimeoutError(ProcessError):
    pass

klasse AuthenticationError(ProcessError):
    pass

#
# Base type fuer contexts. Bound methods of an instance of this type are included in __all__ of __init__.py
#

klasse BaseContext(object):

    ProcessError = ProcessError
    BufferTooShort = BufferTooShort
    TimeoutError = TimeoutError
    AuthenticationError = AuthenticationError

    current_process = staticmethod(process.current_process)
    parent_process = staticmethod(process.parent_process)
    active_children = staticmethod(process.active_children)

    def cpu_count(self):
        '''Returns the number of CPUs in the system'''
        num = os.cpu_count()
        wenn num is Nichts:
            raise NotImplementedError('cannot determine number of cpus')
        sonst:
            return num

    def Manager(self):
        '''Returns a manager associated mit a running server process

        The managers methods such als `Lock()`, `Condition()` und `Queue()`
        can be used to create shared objects.
        '''
        von .managers importiere SyncManager
        m = SyncManager(ctx=self.get_context())
        m.start()
        return m

    def Pipe(self, duplex=Wahr):
        '''Returns two connection object connected by a pipe'''
        von .connection importiere Pipe
        return Pipe(duplex)

    def Lock(self):
        '''Returns a non-recursive lock object'''
        von .synchronize importiere Lock
        return Lock(ctx=self.get_context())

    def RLock(self):
        '''Returns a recursive lock object'''
        von .synchronize importiere RLock
        return RLock(ctx=self.get_context())

    def Condition(self, lock=Nichts):
        '''Returns a condition object'''
        von .synchronize importiere Condition
        return Condition(lock, ctx=self.get_context())

    def Semaphore(self, value=1):
        '''Returns a semaphore object'''
        von .synchronize importiere Semaphore
        return Semaphore(value, ctx=self.get_context())

    def BoundedSemaphore(self, value=1):
        '''Returns a bounded semaphore object'''
        von .synchronize importiere BoundedSemaphore
        return BoundedSemaphore(value, ctx=self.get_context())

    def Event(self):
        '''Returns an event object'''
        von .synchronize importiere Event
        return Event(ctx=self.get_context())

    def Barrier(self, parties, action=Nichts, timeout=Nichts):
        '''Returns a barrier object'''
        von .synchronize importiere Barrier
        return Barrier(parties, action, timeout, ctx=self.get_context())

    def Queue(self, maxsize=0):
        '''Returns a queue object'''
        von .queues importiere Queue
        return Queue(maxsize, ctx=self.get_context())

    def JoinableQueue(self, maxsize=0):
        '''Returns a queue object'''
        von .queues importiere JoinableQueue
        return JoinableQueue(maxsize, ctx=self.get_context())

    def SimpleQueue(self):
        '''Returns a queue object'''
        von .queues importiere SimpleQueue
        return SimpleQueue(ctx=self.get_context())

    def Pool(self, processes=Nichts, initializer=Nichts, initargs=(),
             maxtasksperchild=Nichts):
        '''Returns a process pool object'''
        von .pool importiere Pool
        return Pool(processes, initializer, initargs, maxtasksperchild,
                    context=self.get_context())

    def RawValue(self, typecode_or_type, *args):
        '''Returns a shared object'''
        von .sharedctypes importiere RawValue
        return RawValue(typecode_or_type, *args)

    def RawArray(self, typecode_or_type, size_or_initializer):
        '''Returns a shared array'''
        von .sharedctypes importiere RawArray
        return RawArray(typecode_or_type, size_or_initializer)

    def Value(self, typecode_or_type, *args, lock=Wahr):
        '''Returns a synchronized shared object'''
        von .sharedctypes importiere Value
        return Value(typecode_or_type, *args, lock=lock,
                     ctx=self.get_context())

    def Array(self, typecode_or_type, size_or_initializer, *, lock=Wahr):
        '''Returns a synchronized shared array'''
        von .sharedctypes importiere Array
        return Array(typecode_or_type, size_or_initializer, lock=lock,
                     ctx=self.get_context())

    def freeze_support(self):
        '''Check whether this is a fake forked process in a frozen executable.
        If so then run code specified by commandline und exit.
        '''
        wenn self.get_start_method() == 'spawn' und getattr(sys, 'frozen', Falsch):
            von .spawn importiere freeze_support
            freeze_support()

    def get_logger(self):
        '''Return package logger -- wenn it does nicht already exist then
        it is created.
        '''
        von .util importiere get_logger
        return get_logger()

    def log_to_stderr(self, level=Nichts):
        '''Turn on logging und add a handler which prints to stderr'''
        von .util importiere log_to_stderr
        return log_to_stderr(level)

    def allow_connection_pickling(self):
        '''Install support fuer sending connections und sockets
        between processes
        '''
        # This is undocumented.  In previous versions of multiprocessing
        # its only effect was to make socket objects inheritable on Windows.
        von . importiere connection  # noqa: F401

    def set_executable(self, executable):
        '''Sets the path to a python.exe oder pythonw.exe binary used to run
        child processes instead of sys.executable when using the 'spawn'
        start method.  Useful fuer people embedding Python.
        '''
        von .spawn importiere set_executable
        set_executable(executable)

    def set_forkserver_preload(self, module_names):
        '''Set list of module names to try to load in forkserver process.
        This is really just a hint.
        '''
        von .forkserver importiere set_forkserver_preload
        set_forkserver_preload(module_names)

    def get_context(self, method=Nichts):
        wenn method is Nichts:
            return self
        try:
            ctx = _concrete_contexts[method]
        except KeyError:
            raise ValueError('cannot find context fuer %r' % method) von Nichts
        ctx._check_available()
        return ctx

    def get_start_method(self, allow_none=Falsch):
        return self._name

    def set_start_method(self, method, force=Falsch):
        raise ValueError('cannot set start method of concrete context')

    @property
    def reducer(self):
        '''Controls how objects will be reduced to a form that can be
        shared mit other processes.'''
        return globals().get('reduction')

    @reducer.setter
    def reducer(self, reduction):
        globals()['reduction'] = reduction

    def _check_available(self):
        pass

#
# Type of default context -- underlying context can be set at most once
#

klasse Process(process.BaseProcess):
    _start_method = Nichts
    @staticmethod
    def _Popen(process_obj):
        return _default_context.get_context().Process._Popen(process_obj)

    @staticmethod
    def _after_fork():
        return _default_context.get_context().Process._after_fork()

klasse DefaultContext(BaseContext):
    Process = Process

    def __init__(self, context):
        self._default_context = context
        self._actual_context = Nichts

    def get_context(self, method=Nichts):
        wenn method is Nichts:
            wenn self._actual_context is Nichts:
                self._actual_context = self._default_context
            return self._actual_context
        sonst:
            return super().get_context(method)

    def set_start_method(self, method, force=Falsch):
        wenn self._actual_context is nicht Nichts und nicht force:
            raise RuntimeError('context has already been set')
        wenn method is Nichts und force:
            self._actual_context = Nichts
            return
        self._actual_context = self.get_context(method)

    def get_start_method(self, allow_none=Falsch):
        wenn self._actual_context is Nichts:
            wenn allow_none:
                return Nichts
            self._actual_context = self._default_context
        return self._actual_context._name

    def get_all_start_methods(self):
        """Returns a list of the supported start methods, default first."""
        default = self._default_context.get_start_method()
        start_method_names = [default]
        start_method_names.extend(
            name fuer name in _concrete_contexts wenn name != default
        )
        return start_method_names


#
# Context types fuer fixed start method
#

wenn sys.platform != 'win32':

    klasse ForkProcess(process.BaseProcess):
        _start_method = 'fork'
        @staticmethod
        def _Popen(process_obj):
            von .popen_fork importiere Popen
            return Popen(process_obj)

    klasse SpawnProcess(process.BaseProcess):
        _start_method = 'spawn'
        @staticmethod
        def _Popen(process_obj):
            von .popen_spawn_posix importiere Popen
            return Popen(process_obj)

        @staticmethod
        def _after_fork():
            # process is spawned, nothing to do
            pass

    klasse ForkServerProcess(process.BaseProcess):
        _start_method = 'forkserver'
        @staticmethod
        def _Popen(process_obj):
            von .popen_forkserver importiere Popen
            return Popen(process_obj)

    klasse ForkContext(BaseContext):
        _name = 'fork'
        Process = ForkProcess

    klasse SpawnContext(BaseContext):
        _name = 'spawn'
        Process = SpawnProcess

    klasse ForkServerContext(BaseContext):
        _name = 'forkserver'
        Process = ForkServerProcess
        def _check_available(self):
            wenn nicht reduction.HAVE_SEND_HANDLE:
                raise ValueError('forkserver start method nicht available')

    _concrete_contexts = {
        'fork': ForkContext(),
        'spawn': SpawnContext(),
        'forkserver': ForkServerContext(),
    }
    # bpo-33725: running arbitrary code after fork() is no longer reliable
    # on macOS since macOS 10.14 (Mojave). Use spawn by default instead.
    # gh-84559: We changed everyones default to a thread safeish one in 3.14.
    wenn reduction.HAVE_SEND_HANDLE und sys.platform != 'darwin':
        _default_context = DefaultContext(_concrete_contexts['forkserver'])
    sonst:
        _default_context = DefaultContext(_concrete_contexts['spawn'])

sonst:  # Windows

    klasse SpawnProcess(process.BaseProcess):
        _start_method = 'spawn'
        @staticmethod
        def _Popen(process_obj):
            von .popen_spawn_win32 importiere Popen
            return Popen(process_obj)

        @staticmethod
        def _after_fork():
            # process is spawned, nothing to do
            pass

    klasse SpawnContext(BaseContext):
        _name = 'spawn'
        Process = SpawnProcess

    _concrete_contexts = {
        'spawn': SpawnContext(),
    }
    _default_context = DefaultContext(_concrete_contexts['spawn'])

#
# Force the start method
#

def _force_start_method(method):
    _default_context._actual_context = _concrete_contexts[method]

#
# Check that the current thread is spawning a child process
#

_tls = threading.local()

def get_spawning_popen():
    return getattr(_tls, 'spawning_popen', Nichts)

def set_spawning_popen(popen):
    _tls.spawning_popen = popen

def assert_spawning(obj):
    wenn get_spawning_popen() is Nichts:
        raise RuntimeError(
            '%s objects should only be shared between processes'
            ' through inheritance' % type(obj).__name__
            )
