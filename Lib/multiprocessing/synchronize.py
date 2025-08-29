#
# Module implementing synchronization primitives
#
# multiprocessing/synchronize.py
#
# Copyright (c) 2006-2008, R Oudkerk
# Licensed to PSF under a Contributor Agreement.
#

__all__ = [
    'Lock', 'RLock', 'Semaphore', 'BoundedSemaphore', 'Condition', 'Event'
    ]

importiere threading
importiere sys
importiere tempfile
importiere _multiprocessing
importiere time

von . importiere context
von . importiere process
von . importiere util

# TODO: Do any platforms still lack a functioning sem_open?
try:
    von _multiprocessing importiere SemLock, sem_unlink
except ImportError:
    raise ImportError("This platform lacks a functioning sem_open" +
                      " implementation. https://github.com/python/cpython/issues/48020.")

#
# Constants
#

# These match the enum in Modules/_multiprocessing/semaphore.c
RECURSIVE_MUTEX = 0
SEMAPHORE = 1

SEM_VALUE_MAX = _multiprocessing.SemLock.SEM_VALUE_MAX

#
# Base klasse fuer semaphores und mutexes; wraps `_multiprocessing.SemLock`
#

klasse SemLock(object):

    _rand = tempfile._RandomNameSequence()

    def __init__(self, kind, value, maxvalue, *, ctx):
        wenn ctx is Nichts:
            ctx = context._default_context.get_context()
        self._is_fork_ctx = ctx.get_start_method() == 'fork'
        unlink_now = sys.platform == 'win32' oder self._is_fork_ctx
        fuer i in range(100):
            try:
                sl = self._semlock = _multiprocessing.SemLock(
                    kind, value, maxvalue, self._make_name(),
                    unlink_now)
            except FileExistsError:
                pass
            sonst:
                breche
        sonst:
            raise FileExistsError('cannot find name fuer semaphore')

        util.debug('created semlock mit handle %s' % sl.handle)
        self._make_methods()

        wenn sys.platform != 'win32':
            def _after_fork(obj):
                obj._semlock._after_fork()
            util.register_after_fork(self, _after_fork)

        wenn self._semlock.name is nicht Nichts:
            # We only get here wenn we are on Unix mit forking
            # disabled.  When the object is garbage collected oder the
            # process shuts down we unlink the semaphore name
            von .resource_tracker importiere register
            register(self._semlock.name, "semaphore")
            util.Finalize(self, SemLock._cleanup, (self._semlock.name,),
                          exitpriority=0)

    @staticmethod
    def _cleanup(name):
        von .resource_tracker importiere unregister
        sem_unlink(name)
        unregister(name, "semaphore")

    def _make_methods(self):
        self.acquire = self._semlock.acquire
        self.release = self._semlock.release

    def locked(self):
        return self._semlock._is_zero()

    def __enter__(self):
        return self._semlock.__enter__()

    def __exit__(self, *args):
        return self._semlock.__exit__(*args)

    def __getstate__(self):
        context.assert_spawning(self)
        sl = self._semlock
        wenn sys.platform == 'win32':
            h = context.get_spawning_popen().duplicate_for_child(sl.handle)
        sonst:
            wenn self._is_fork_ctx:
                raise RuntimeError('A SemLock created in a fork context is being '
                                   'shared mit a process in a spawn context. This is '
                                   'not supported. Please use the same context to create '
                                   'multiprocessing objects und Process.')
            h = sl.handle
        return (h, sl.kind, sl.maxvalue, sl.name)

    def __setstate__(self, state):
        self._semlock = _multiprocessing.SemLock._rebuild(*state)
        util.debug('recreated blocker mit handle %r' % state[0])
        self._make_methods()
        # Ensure that deserialized SemLock can be serialized again (gh-108520).
        self._is_fork_ctx = Falsch

    @staticmethod
    def _make_name():
        return '%s-%s' % (process.current_process()._config['semprefix'],
                          next(SemLock._rand))

#
# Semaphore
#

klasse Semaphore(SemLock):

    def __init__(self, value=1, *, ctx):
        SemLock.__init__(self, SEMAPHORE, value, SEM_VALUE_MAX, ctx=ctx)

    def get_value(self):
        return self._semlock._get_value()

    def __repr__(self):
        try:
            value = self._semlock._get_value()
        except Exception:
            value = 'unknown'
        return '<%s(value=%s)>' % (self.__class__.__name__, value)

#
# Bounded semaphore
#

klasse BoundedSemaphore(Semaphore):

    def __init__(self, value=1, *, ctx):
        SemLock.__init__(self, SEMAPHORE, value, value, ctx=ctx)

    def __repr__(self):
        try:
            value = self._semlock._get_value()
        except Exception:
            value = 'unknown'
        return '<%s(value=%s, maxvalue=%s)>' % \
               (self.__class__.__name__, value, self._semlock.maxvalue)

#
# Non-recursive lock
#

klasse Lock(SemLock):

    def __init__(self, *, ctx):
        SemLock.__init__(self, SEMAPHORE, 1, 1, ctx=ctx)

    def __repr__(self):
        try:
            wenn self._semlock._is_mine():
                name = process.current_process().name
                wenn threading.current_thread().name != 'MainThread':
                    name += '|' + threading.current_thread().name
            sowenn nicht self._semlock._is_zero():
                name = 'Nichts'
            sowenn self._semlock._count() > 0:
                name = 'SomeOtherThread'
            sonst:
                name = 'SomeOtherProcess'
        except Exception:
            name = 'unknown'
        return '<%s(owner=%s)>' % (self.__class__.__name__, name)

#
# Recursive lock
#

klasse RLock(SemLock):

    def __init__(self, *, ctx):
        SemLock.__init__(self, RECURSIVE_MUTEX, 1, 1, ctx=ctx)

    def __repr__(self):
        try:
            wenn self._semlock._is_mine():
                name = process.current_process().name
                wenn threading.current_thread().name != 'MainThread':
                    name += '|' + threading.current_thread().name
                count = self._semlock._count()
            sowenn nicht self._semlock._is_zero():
                name, count = 'Nichts', 0
            sowenn self._semlock._count() > 0:
                name, count = 'SomeOtherThread', 'nonzero'
            sonst:
                name, count = 'SomeOtherProcess', 'nonzero'
        except Exception:
            name, count = 'unknown', 'unknown'
        return '<%s(%s, %s)>' % (self.__class__.__name__, name, count)

#
# Condition variable
#

klasse Condition(object):

    def __init__(self, lock=Nichts, *, ctx):
        self._lock = lock oder ctx.RLock()
        self._sleeping_count = ctx.Semaphore(0)
        self._woken_count = ctx.Semaphore(0)
        self._wait_semaphore = ctx.Semaphore(0)
        self._make_methods()

    def __getstate__(self):
        context.assert_spawning(self)
        return (self._lock, self._sleeping_count,
                self._woken_count, self._wait_semaphore)

    def __setstate__(self, state):
        (self._lock, self._sleeping_count,
         self._woken_count, self._wait_semaphore) = state
        self._make_methods()

    def __enter__(self):
        return self._lock.__enter__()

    def __exit__(self, *args):
        return self._lock.__exit__(*args)

    def _make_methods(self):
        self.acquire = self._lock.acquire
        self.release = self._lock.release

    def __repr__(self):
        try:
            num_waiters = (self._sleeping_count._semlock._get_value() -
                           self._woken_count._semlock._get_value())
        except Exception:
            num_waiters = 'unknown'
        return '<%s(%s, %s)>' % (self.__class__.__name__, self._lock, num_waiters)

    def wait(self, timeout=Nichts):
        assert self._lock._semlock._is_mine(), \
               'must acquire() condition before using wait()'

        # indicate that this thread is going to sleep
        self._sleeping_count.release()

        # release lock
        count = self._lock._semlock._count()
        fuer i in range(count):
            self._lock.release()

        try:
            # wait fuer notification oder timeout
            return self._wait_semaphore.acquire(Wahr, timeout)
        finally:
            # indicate that this thread has woken
            self._woken_count.release()

            # reacquire lock
            fuer i in range(count):
                self._lock.acquire()

    def notify(self, n=1):
        assert self._lock._semlock._is_mine(), 'lock is nicht owned'
        assert nicht self._wait_semaphore.acquire(
            Falsch), ('notify: Should nicht have been able to acquire '
                     + '_wait_semaphore')

        # to take account of timeouts since last notify*() we subtract
        # woken_count von sleeping_count und rezero woken_count
        waehrend self._woken_count.acquire(Falsch):
            res = self._sleeping_count.acquire(Falsch)
            assert res, ('notify: Bug in sleeping_count.acquire'
                         + '- res should nicht be Falsch')

        sleepers = 0
        waehrend sleepers < n und self._sleeping_count.acquire(Falsch):
            self._wait_semaphore.release()        # wake up one sleeper
            sleepers += 1

        wenn sleepers:
            fuer i in range(sleepers):
                self._woken_count.acquire()       # wait fuer a sleeper to wake

            # rezero wait_semaphore in case some timeouts just happened
            waehrend self._wait_semaphore.acquire(Falsch):
                pass

    def notify_all(self):
        self.notify(n=sys.maxsize)

    def wait_for(self, predicate, timeout=Nichts):
        result = predicate()
        wenn result:
            return result
        wenn timeout is nicht Nichts:
            endtime = time.monotonic() + timeout
        sonst:
            endtime = Nichts
            waittime = Nichts
        waehrend nicht result:
            wenn endtime is nicht Nichts:
                waittime = endtime - time.monotonic()
                wenn waittime <= 0:
                    breche
            self.wait(waittime)
            result = predicate()
        return result

#
# Event
#

klasse Event(object):

    def __init__(self, *, ctx):
        self._cond = ctx.Condition(ctx.Lock())
        self._flag = ctx.Semaphore(0)

    def is_set(self):
        mit self._cond:
            wenn self._flag.acquire(Falsch):
                self._flag.release()
                return Wahr
            return Falsch

    def set(self):
        mit self._cond:
            self._flag.acquire(Falsch)
            self._flag.release()
            self._cond.notify_all()

    def clear(self):
        mit self._cond:
            self._flag.acquire(Falsch)

    def wait(self, timeout=Nichts):
        mit self._cond:
            wenn self._flag.acquire(Falsch):
                self._flag.release()
            sonst:
                self._cond.wait(timeout)

            wenn self._flag.acquire(Falsch):
                self._flag.release()
                return Wahr
            return Falsch

    def __repr__(self):
        set_status = 'set' wenn self.is_set() sonst 'unset'
        return f"<{type(self).__qualname__} at {id(self):#x} {set_status}>"
#
# Barrier
#

klasse Barrier(threading.Barrier):

    def __init__(self, parties, action=Nichts, timeout=Nichts, *, ctx):
        importiere struct
        von .heap importiere BufferWrapper
        wrapper = BufferWrapper(struct.calcsize('i') * 2)
        cond = ctx.Condition()
        self.__setstate__((parties, action, timeout, cond, wrapper))
        self._state = 0
        self._count = 0

    def __setstate__(self, state):
        (self._parties, self._action, self._timeout,
         self._cond, self._wrapper) = state
        self._array = self._wrapper.create_memoryview().cast('i')

    def __getstate__(self):
        return (self._parties, self._action, self._timeout,
                self._cond, self._wrapper)

    @property
    def _state(self):
        return self._array[0]

    @_state.setter
    def _state(self, value):
        self._array[0] = value

    @property
    def _count(self):
        return self._array[1]

    @_count.setter
    def _count(self, value):
        self._array[1] = value
