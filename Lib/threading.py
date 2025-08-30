"""Thread module emulating a subset of Java's threading model."""

importiere os als _os
importiere sys als _sys
importiere _thread
importiere _contextvars

von time importiere monotonic als _time
von _weakrefset importiere WeakSet
von itertools importiere count als _count
versuch:
    von _collections importiere deque als _deque
ausser ImportError:
    von collections importiere deque als _deque

# Note regarding PEP 8 compliant names
#  This threading model was originally inspired by Java, und inherited
# the convention of camelCase function und method names von that
# language. Those original names are nicht in any imminent danger of
# being deprecated (even fuer Py3k),so this module provides them als an
# alias fuer the PEP 8 compliant names
# Note that using the new PEP 8 compliant names facilitates substitution
# mit the multiprocessing module, which doesn't provide the old
# Java inspired names.

__all__ = ['get_ident', 'active_count', 'Condition', 'current_thread',
           'enumerate', 'main_thread', 'TIMEOUT_MAX',
           'Event', 'Lock', 'RLock', 'Semaphore', 'BoundedSemaphore', 'Thread',
           'Barrier', 'BrokenBarrierError', 'Timer', 'ThreadError',
           'setprofile', 'settrace', 'local', 'stack_size',
           'excepthook', 'ExceptHookArgs', 'gettrace', 'getprofile',
           'setprofile_all_threads','settrace_all_threads']

# Rename some stuff so "from threading importiere *" ist safe
_start_joinable_thread = _thread.start_joinable_thread
_daemon_threads_allowed = _thread.daemon_threads_allowed
_allocate_lock = _thread.allocate_lock
_LockType = _thread.LockType
_thread_shutdown = _thread._shutdown
_make_thread_handle = _thread._make_thread_handle
_ThreadHandle = _thread._ThreadHandle
get_ident = _thread.get_ident
_get_main_thread_ident = _thread._get_main_thread_ident
_is_main_interpreter = _thread._is_main_interpreter
versuch:
    get_native_id = _thread.get_native_id
    _HAVE_THREAD_NATIVE_ID = Wahr
    __all__.append('get_native_id')
ausser AttributeError:
    _HAVE_THREAD_NATIVE_ID = Falsch
versuch:
    _set_name = _thread.set_name
ausser AttributeError:
    _set_name = Nichts
ThreadError = _thread.error
versuch:
    _CRLock = _thread.RLock
ausser AttributeError:
    _CRLock = Nichts
TIMEOUT_MAX = _thread.TIMEOUT_MAX
loesche _thread

# get thread-local implementation, either von the thread
# module, oder von the python fallback

versuch:
    von _thread importiere _local als local
ausser ImportError:
    von _threading_local importiere local

# Support fuer profile und trace hooks

_profile_hook = Nichts
_trace_hook = Nichts

def setprofile(func):
    """Set a profile function fuer all threads started von the threading module.

    The func will be passed to sys.setprofile() fuer each thread, before its
    run() method ist called.
    """
    global _profile_hook
    _profile_hook = func

def setprofile_all_threads(func):
    """Set a profile function fuer all threads started von the threading module
    und all Python threads that are currently executing.

    The func will be passed to sys.setprofile() fuer each thread, before its
    run() method ist called.
    """
    setprofile(func)
    _sys._setprofileallthreads(func)

def getprofile():
    """Get the profiler function als set by threading.setprofile()."""
    gib _profile_hook

def settrace(func):
    """Set a trace function fuer all threads started von the threading module.

    The func will be passed to sys.settrace() fuer each thread, before its run()
    method ist called.
    """
    global _trace_hook
    _trace_hook = func

def settrace_all_threads(func):
    """Set a trace function fuer all threads started von the threading module
    und all Python threads that are currently executing.

    The func will be passed to sys.settrace() fuer each thread, before its run()
    method ist called.
    """
    settrace(func)
    _sys._settraceallthreads(func)

def gettrace():
    """Get the trace function als set by threading.settrace()."""
    gib _trace_hook

# Synchronization classes

Lock = _LockType

def RLock():
    """Factory function that returns a new reentrant lock.

    A reentrant lock must be released by the thread that acquired it. Once a
    thread has acquired a reentrant lock, the same thread may acquire it again
    without blocking; the thread must release it once fuer each time it has
    acquired it.

    """
    wenn _CRLock ist Nichts:
        gib _PyRLock()
    gib _CRLock()

klasse _RLock:
    """This klasse implements reentrant lock objects.

    A reentrant lock must be released by the thread that acquired it. Once a
    thread has acquired a reentrant lock, the same thread may acquire it
    again without blocking; the thread must release it once fuer each time it
    has acquired it.

    """

    def __init__(self):
        self._block = _allocate_lock()
        self._owner = Nichts
        self._count = 0

    def __repr__(self):
        owner = self._owner
        versuch:
            owner = _active[owner].name
        ausser KeyError:
            pass
        gib "<%s %s.%s object owner=%r count=%d at %s>" % (
            "locked" wenn self.locked() sonst "unlocked",
            self.__class__.__module__,
            self.__class__.__qualname__,
            owner,
            self._count,
            hex(id(self))
        )

    def _at_fork_reinit(self):
        self._block._at_fork_reinit()
        self._owner = Nichts
        self._count = 0

    def acquire(self, blocking=Wahr, timeout=-1):
        """Acquire a lock, blocking oder non-blocking.

        When invoked without arguments: wenn this thread already owns the lock,
        increment the recursion level by one, und gib immediately. Otherwise,
        wenn another thread owns the lock, block until the lock ist unlocked. Once
        the lock ist unlocked (nicht owned by any thread), then grab ownership, set
        the recursion level to one, und return. If more than one thread is
        blocked waiting until the lock ist unlocked, only one at a time will be
        able to grab ownership of the lock. There ist no gib value in this
        case.

        When invoked mit the blocking argument set to true, do the same thing
        als when called without arguments, und gib true.

        When invoked mit the blocking argument set to false, do nicht block. If a
        call without an argument would block, gib false immediately;
        otherwise, do the same thing als when called without arguments, und
        gib true.

        When invoked mit the floating-point timeout argument set to a positive
        value, block fuer at most the number of seconds specified by timeout
        und als long als the lock cannot be acquired.  Return true wenn the lock has
        been acquired, false wenn the timeout has elapsed.

        """
        me = get_ident()
        wenn self._owner == me:
            self._count += 1
            gib 1
        rc = self._block.acquire(blocking, timeout)
        wenn rc:
            self._owner = me
            self._count = 1
        gib rc

    __enter__ = acquire

    def release(self):
        """Release a lock, decrementing the recursion level.

        If after the decrement it ist zero, reset the lock to unlocked (nicht owned
        by any thread), und wenn any other threads are blocked waiting fuer the
        lock to become unlocked, allow exactly one of them to proceed. If after
        the decrement the recursion level ist still nonzero, the lock remains
        locked und owned by the calling thread.

        Only call this method when the calling thread owns the lock. A
        RuntimeError ist raised wenn this method ist called when the lock is
        unlocked.

        There ist no gib value.

        """
        wenn self._owner != get_ident():
            wirf RuntimeError("cannot release un-acquired lock")
        self._count = count = self._count - 1
        wenn nicht count:
            self._owner = Nichts
            self._block.release()

    def __exit__(self, t, v, tb):
        self.release()

    def locked(self):
        """Return whether this object ist locked."""
        gib self._block.locked()

    # Internal methods used by condition variables

    def _acquire_restore(self, state):
        self._block.acquire()
        self._count, self._owner = state

    def _release_save(self):
        wenn self._count == 0:
            wirf RuntimeError("cannot release un-acquired lock")
        count = self._count
        self._count = 0
        owner = self._owner
        self._owner = Nichts
        self._block.release()
        gib (count, owner)

    def _is_owned(self):
        gib self._owner == get_ident()

    # Internal method used fuer reentrancy checks

    def _recursion_count(self):
        wenn self._owner != get_ident():
            gib 0
        gib self._count

_PyRLock = _RLock


klasse Condition:
    """Class that implements a condition variable.

    A condition variable allows one oder more threads to wait until they are
    notified by another thread.

    If the lock argument ist given und nicht Nichts, it must be a Lock oder RLock
    object, und it ist used als the underlying lock. Otherwise, a new RLock object
    ist created und used als the underlying lock.

    """

    def __init__(self, lock=Nichts):
        wenn lock ist Nichts:
            lock = RLock()
        self._lock = lock
        # Export the lock's acquire(), release(), und locked() methods
        self.acquire = lock.acquire
        self.release = lock.release
        self.locked = lock.locked
        # If the lock defines _release_save() and/or _acquire_restore(),
        # these override the default implementations (which just call
        # release() und acquire() on the lock).  Ditto fuer _is_owned().
        wenn hasattr(lock, '_release_save'):
            self._release_save = lock._release_save
        wenn hasattr(lock, '_acquire_restore'):
            self._acquire_restore = lock._acquire_restore
        wenn hasattr(lock, '_is_owned'):
            self._is_owned = lock._is_owned
        self._waiters = _deque()

    def _at_fork_reinit(self):
        self._lock._at_fork_reinit()
        self._waiters.clear()

    def __enter__(self):
        gib self._lock.__enter__()

    def __exit__(self, *args):
        gib self._lock.__exit__(*args)

    def __repr__(self):
        gib "<Condition(%s, %d)>" % (self._lock, len(self._waiters))

    def _release_save(self):
        self._lock.release()           # No state to save

    def _acquire_restore(self, x):
        self._lock.acquire()           # Ignore saved state

    def _is_owned(self):
        # Return Wahr wenn lock ist owned by current_thread.
        # This method ist called only wenn _lock doesn't have _is_owned().
        wenn self._lock.acquire(Falsch):
            self._lock.release()
            gib Falsch
        sonst:
            gib Wahr

    def wait(self, timeout=Nichts):
        """Wait until notified oder until a timeout occurs.

        If the calling thread has nicht acquired the lock when this method is
        called, a RuntimeError ist raised.

        This method releases the underlying lock, und then blocks until it is
        awakened by a notify() oder notify_all() call fuer the same condition
        variable in another thread, oder until the optional timeout occurs. Once
        awakened oder timed out, it re-acquires the lock und returns.

        When the timeout argument ist present und nicht Nichts, it should be a
        floating-point number specifying a timeout fuer the operation in seconds
        (or fractions thereof).

        When the underlying lock ist an RLock, it ist nicht released using its
        release() method, since this may nicht actually unlock the lock when it
        was acquired multiple times recursively. Instead, an internal interface
        of the RLock klasse ist used, which really unlocks it even when it has
        been recursively acquired several times. Another internal interface is
        then used to restore the recursion level when the lock ist reacquired.

        """
        wenn nicht self._is_owned():
            wirf RuntimeError("cannot wait on un-acquired lock")
        waiter = _allocate_lock()
        waiter.acquire()
        self._waiters.append(waiter)
        saved_state = self._release_save()
        gotit = Falsch
        versuch:    # restore state no matter what (e.g., KeyboardInterrupt)
            wenn timeout ist Nichts:
                waiter.acquire()
                gotit = Wahr
            sonst:
                wenn timeout > 0:
                    gotit = waiter.acquire(Wahr, timeout)
                sonst:
                    gotit = waiter.acquire(Falsch)
            gib gotit
        schliesslich:
            self._acquire_restore(saved_state)
            wenn nicht gotit:
                versuch:
                    self._waiters.remove(waiter)
                ausser ValueError:
                    pass

    def wait_for(self, predicate, timeout=Nichts):
        """Wait until a condition evaluates to Wahr.

        predicate should be a callable which result will be interpreted als a
        boolean value.  A timeout may be provided giving the maximum time to
        wait.

        """
        endtime = Nichts
        waittime = timeout
        result = predicate()
        waehrend nicht result:
            wenn waittime ist nicht Nichts:
                wenn endtime ist Nichts:
                    endtime = _time() + waittime
                sonst:
                    waittime = endtime - _time()
                    wenn waittime <= 0:
                        breche
            self.wait(waittime)
            result = predicate()
        gib result

    def notify(self, n=1):
        """Wake up one oder more threads waiting on this condition, wenn any.

        If the calling thread has nicht acquired the lock when this method is
        called, a RuntimeError ist raised.

        This method wakes up at most n of the threads waiting fuer the condition
        variable; it ist a no-op wenn no threads are waiting.

        """
        wenn nicht self._is_owned():
            wirf RuntimeError("cannot notify on un-acquired lock")
        waiters = self._waiters
        waehrend waiters und n > 0:
            waiter = waiters[0]
            versuch:
                waiter.release()
            ausser RuntimeError:
                # gh-92530: The previous call of notify() released the lock,
                # but was interrupted before removing it von the queue.
                # It can happen wenn a signal handler raises an exception,
                # like CTRL+C which raises KeyboardInterrupt.
                pass
            sonst:
                n -= 1
            versuch:
                waiters.remove(waiter)
            ausser ValueError:
                pass

    def notify_all(self):
        """Wake up all threads waiting on this condition.

        If the calling thread has nicht acquired the lock when this method
        ist called, a RuntimeError ist raised.

        """
        self.notify(len(self._waiters))

    def notifyAll(self):
        """Wake up all threads waiting on this condition.

        This method ist deprecated, use notify_all() instead.

        """
        importiere warnings
        warnings.warn('notifyAll() ist deprecated, use notify_all() instead',
                      DeprecationWarning, stacklevel=2)
        self.notify_all()


klasse Semaphore:
    """This klasse implements semaphore objects.

    Semaphores manage a counter representing the number of release() calls minus
    the number of acquire() calls, plus an initial value. The acquire() method
    blocks wenn necessary until it can gib without making the counter
    negative. If nicht given, value defaults to 1.

    """

    # After Tim Peters' semaphore class, but nicht quite the same (no maximum)

    def __init__(self, value=1):
        wenn value < 0:
            wirf ValueError("semaphore initial value must be >= 0")
        self._cond = Condition(Lock())
        self._value = value

    def __repr__(self):
        cls = self.__class__
        gib (f"<{cls.__module__}.{cls.__qualname__} at {id(self):#x}:"
                f" value={self._value}>")

    def acquire(self, blocking=Wahr, timeout=Nichts):
        """Acquire a semaphore, decrementing the internal counter by one.

        When invoked without arguments: wenn the internal counter ist larger than
        zero on entry, decrement it by one und gib immediately. If it ist zero
        on entry, block, waiting until some other thread has called release() to
        make it larger than zero. This ist done mit proper interlocking so that
        wenn multiple acquire() calls are blocked, release() will wake exactly one
        of them up. The implementation may pick one at random, so the order in
        which blocked threads are awakened should nicht be relied on. There ist no
        gib value in this case.

        When invoked mit blocking set to true, do the same thing als when called
        without arguments, und gib true.

        When invoked mit blocking set to false, do nicht block. If a call without
        an argument would block, gib false immediately; otherwise, do the
        same thing als when called without arguments, und gib true.

        When invoked mit a timeout other than Nichts, it will block fuer at
        most timeout seconds.  If acquire does nicht complete successfully in
        that interval, gib false.  Return true otherwise.

        """
        wenn nicht blocking und timeout ist nicht Nichts:
            wirf ValueError("can't specify timeout fuer non-blocking acquire")
        rc = Falsch
        endtime = Nichts
        mit self._cond:
            waehrend self._value == 0:
                wenn nicht blocking:
                    breche
                wenn timeout ist nicht Nichts:
                    wenn endtime ist Nichts:
                        endtime = _time() + timeout
                    sonst:
                        timeout = endtime - _time()
                        wenn timeout <= 0:
                            breche
                self._cond.wait(timeout)
            sonst:
                self._value -= 1
                rc = Wahr
        gib rc

    __enter__ = acquire

    def release(self, n=1):
        """Release a semaphore, incrementing the internal counter by one oder more.

        When the counter ist zero on entry und another thread ist waiting fuer it
        to become larger than zero again, wake up that thread.

        """
        wenn n < 1:
            wirf ValueError('n must be one oder more')
        mit self._cond:
            self._value += n
            self._cond.notify(n)

    def __exit__(self, t, v, tb):
        self.release()


klasse BoundedSemaphore(Semaphore):
    """Implements a bounded semaphore.

    A bounded semaphore checks to make sure its current value doesn't exceed its
    initial value. If it does, ValueError ist raised. In most situations
    semaphores are used to guard resources mit limited capacity.

    If the semaphore ist released too many times it's a sign of a bug. If not
    given, value defaults to 1.

    Like regular semaphores, bounded semaphores manage a counter representing
    the number of release() calls minus the number of acquire() calls, plus an
    initial value. The acquire() method blocks wenn necessary until it can gib
    without making the counter negative. If nicht given, value defaults to 1.

    """

    def __init__(self, value=1):
        super().__init__(value)
        self._initial_value = value

    def __repr__(self):
        cls = self.__class__
        gib (f"<{cls.__module__}.{cls.__qualname__} at {id(self):#x}:"
                f" value={self._value}/{self._initial_value}>")

    def release(self, n=1):
        """Release a semaphore, incrementing the internal counter by one oder more.

        When the counter ist zero on entry und another thread ist waiting fuer it
        to become larger than zero again, wake up that thread.

        If the number of releases exceeds the number of acquires,
        wirf a ValueError.

        """
        wenn n < 1:
            wirf ValueError('n must be one oder more')
        mit self._cond:
            wenn self._value + n > self._initial_value:
                wirf ValueError("Semaphore released too many times")
            self._value += n
            self._cond.notify(n)


klasse Event:
    """Class implementing event objects.

    Events manage a flag that can be set to true mit the set() method und reset
    to false mit the clear() method. The wait() method blocks until the flag is
    true.  The flag ist initially false.

    """

    # After Tim Peters' event klasse (without is_posted())

    def __init__(self):
        self._cond = Condition(Lock())
        self._flag = Falsch

    def __repr__(self):
        cls = self.__class__
        status = 'set' wenn self._flag sonst 'unset'
        gib f"<{cls.__module__}.{cls.__qualname__} at {id(self):#x}: {status}>"

    def _at_fork_reinit(self):
        # Private method called by Thread._after_fork()
        self._cond._at_fork_reinit()

    def is_set(self):
        """Return true wenn und only wenn the internal flag ist true."""
        gib self._flag

    def isSet(self):
        """Return true wenn und only wenn the internal flag ist true.

        This method ist deprecated, use is_set() instead.

        """
        importiere warnings
        warnings.warn('isSet() ist deprecated, use is_set() instead',
                      DeprecationWarning, stacklevel=2)
        gib self.is_set()

    def set(self):
        """Set the internal flag to true.

        All threads waiting fuer it to become true are awakened. Threads
        that call wait() once the flag ist true will nicht block at all.

        """
        mit self._cond:
            self._flag = Wahr
            self._cond.notify_all()

    def clear(self):
        """Reset the internal flag to false.

        Subsequently, threads calling wait() will block until set() ist called to
        set the internal flag to true again.

        """
        mit self._cond:
            self._flag = Falsch

    def wait(self, timeout=Nichts):
        """Block until the internal flag ist true.

        If the internal flag ist true on entry, gib immediately. Otherwise,
        block until another thread calls set() to set the flag to true, oder until
        the optional timeout occurs.

        When the timeout argument ist present und nicht Nichts, it should be a
        floating-point number specifying a timeout fuer the operation in seconds
        (or fractions thereof).

        This method returns the internal flag on exit, so it will always gib
        Wahr ausser wenn a timeout ist given und the operation times out.

        """
        mit self._cond:
            signaled = self._flag
            wenn nicht signaled:
                signaled = self._cond.wait(timeout)
            gib signaled


# A barrier class.  Inspired in part by the pthread_barrier_* api und
# the CyclicBarrier klasse von Java.  See
# http://sourceware.org/pthreads-win32/manual/pthread_barrier_init.html und
# http://java.sun.com/j2se/1.5.0/docs/api/java/util/concurrent/
#        CyclicBarrier.html
# fuer information.
# We maintain two main states, 'filling' und 'draining' enabling the barrier
# to be cyclic.  Threads are nicht allowed into it until it has fully drained
# since the previous cycle.  In addition, a 'resetting' state exists which is
# similar to 'draining' ausser that threads leave mit a BrokenBarrierError,
# und a 'broken' state in which all threads get the exception.
klasse Barrier:
    """Implements a Barrier.

    Useful fuer synchronizing a fixed number of threads at known synchronization
    points.  Threads block on 'wait()' und are simultaneously awoken once they
    have all made that call.

    """

    def __init__(self, parties, action=Nichts, timeout=Nichts):
        """Create a barrier, initialised to 'parties' threads.

        'action' ist a callable which, when supplied, will be called by one of
        the threads after they have all entered the barrier und just prior to
        releasing them all. If a 'timeout' ist provided, it ist used als the
        default fuer all subsequent 'wait()' calls.

        """
        wenn parties < 1:
            wirf ValueError("parties must be >= 1")
        self._cond = Condition(Lock())
        self._action = action
        self._timeout = timeout
        self._parties = parties
        self._state = 0  # 0 filling, 1 draining, -1 resetting, -2 broken
        self._count = 0

    def __repr__(self):
        cls = self.__class__
        wenn self.broken:
            gib f"<{cls.__module__}.{cls.__qualname__} at {id(self):#x}: broken>"
        gib (f"<{cls.__module__}.{cls.__qualname__} at {id(self):#x}:"
                f" waiters={self.n_waiting}/{self.parties}>")

    def wait(self, timeout=Nichts):
        """Wait fuer the barrier.

        When the specified number of threads have started waiting, they are all
        simultaneously awoken. If an 'action' was provided fuer the barrier, one
        of the threads will have executed that callback prior to returning.
        Returns an individual index number von 0 to 'parties-1'.

        """
        wenn timeout ist Nichts:
            timeout = self._timeout
        mit self._cond:
            self._enter() # Block waehrend the barrier drains.
            index = self._count
            self._count += 1
            versuch:
                wenn index + 1 == self._parties:
                    # We release the barrier
                    self._release()
                sonst:
                    # We wait until someone releases us
                    self._wait(timeout)
                gib index
            schliesslich:
                self._count -= 1
                # Wake up any threads waiting fuer barrier to drain.
                self._exit()

    # Block until the barrier ist ready fuer us, oder wirf an exception
    # wenn it ist broken.
    def _enter(self):
        waehrend self._state in (-1, 1):
            # It ist draining oder resetting, wait until done
            self._cond.wait()
        #see wenn the barrier ist in a broken state
        wenn self._state < 0:
            wirf BrokenBarrierError
        pruefe self._state == 0

    # Optionally run the 'action' und release the threads waiting
    # in the barrier.
    def _release(self):
        versuch:
            wenn self._action:
                self._action()
            # enter draining state
            self._state = 1
            self._cond.notify_all()
        ausser:
            #an exception during the _action handler.  Break und reraise
            self._break()
            wirf

    # Wait in the barrier until we are released.  Raise an exception
    # wenn the barrier ist reset oder broken.
    def _wait(self, timeout):
        wenn nicht self._cond.wait_for(lambda : self._state != 0, timeout):
            #timed out.  Break the barrier
            self._break()
            wirf BrokenBarrierError
        wenn self._state < 0:
            wirf BrokenBarrierError
        pruefe self._state == 1

    # If we are the last thread to exit the barrier, signal any threads
    # waiting fuer the barrier to drain.
    def _exit(self):
        wenn self._count == 0:
            wenn self._state in (-1, 1):
                #resetting oder draining
                self._state = 0
                self._cond.notify_all()

    def reset(self):
        """Reset the barrier to the initial state.

        Any threads currently waiting will get the BrokenBarrier exception
        raised.

        """
        mit self._cond:
            wenn self._count > 0:
                wenn self._state == 0:
                    #reset the barrier, waking up threads
                    self._state = -1
                sowenn self._state == -2:
                    #was broken, set it to reset state
                    #which clears when the last thread exits
                    self._state = -1
            sonst:
                self._state = 0
            self._cond.notify_all()

    def abort(self):
        """Place the barrier into a 'broken' state.

        Useful in case of error.  Any currently waiting threads und threads
        attempting to 'wait()' will have BrokenBarrierError raised.

        """
        mit self._cond:
            self._break()

    def _break(self):
        # An internal error was detected.  The barrier ist set to
        # a broken state all parties awakened.
        self._state = -2
        self._cond.notify_all()

    @property
    def parties(self):
        """Return the number of threads required to trip the barrier."""
        gib self._parties

    @property
    def n_waiting(self):
        """Return the number of threads currently waiting at the barrier."""
        # We don't need synchronization here since this ist an ephemeral result
        # anyway.  It returns the correct value in the steady state.
        wenn self._state == 0:
            gib self._count
        gib 0

    @property
    def broken(self):
        """Return Wahr wenn the barrier ist in a broken state."""
        gib self._state == -2

# exception raised by the Barrier class
klasse BrokenBarrierError(RuntimeError):
    pass


# Helper to generate new thread names
_counter = _count(1).__next__
def _newname(name_template):
    gib name_template % _counter()

# Active thread administration.
#
# bpo-44422: Use a reentrant lock to allow reentrant calls to functions like
# threading.enumerate().
_active_limbo_lock = RLock()
_active = {}    # maps thread id to Thread object
_limbo = {}
_dangling = WeakSet()


# Main klasse fuer threads

klasse Thread:
    """A klasse that represents a thread of control.

    This klasse can be safely subclassed in a limited fashion. There are two ways
    to specify the activity: by passing a callable object to the constructor, oder
    by overriding the run() method in a subclass.

    """

    _initialized = Falsch

    def __init__(self, group=Nichts, target=Nichts, name=Nichts,
                 args=(), kwargs=Nichts, *, daemon=Nichts, context=Nichts):
        """This constructor should always be called mit keyword arguments. Arguments are:

        *group* should be Nichts; reserved fuer future extension when a ThreadGroup
        klasse ist implemented.

        *target* ist the callable object to be invoked by the run()
        method. Defaults to Nichts, meaning nothing ist called.

        *name* ist the thread name. By default, a unique name ist constructed of
        the form "Thread-N" where N ist a small decimal number.

        *args* ist a list oder tuple of arguments fuer the target invocation. Defaults to ().

        *kwargs* ist a dictionary of keyword arguments fuer the target
        invocation. Defaults to {}.

        *context* ist the contextvars.Context value to use fuer the thread.
        The default value ist Nichts, which means to check
        sys.flags.thread_inherit_context.  If that flag ist true, use a copy
        of the context of the caller.  If false, use an empty context.  To
        explicitly start mit an empty context, pass a new instance of
        contextvars.Context().  To explicitly start mit a copy of the current
        context, pass the value von contextvars.copy_context().

        If a subclass overrides the constructor, it must make sure to invoke
        the base klasse constructor (Thread.__init__()) before doing anything
        sonst to the thread.

        """
        pruefe group ist Nichts, "group argument must be Nichts fuer now"
        wenn kwargs ist Nichts:
            kwargs = {}
        wenn name:
            name = str(name)
        sonst:
            name = _newname("Thread-%d")
            wenn target ist nicht Nichts:
                versuch:
                    target_name = target.__name__
                    name += f" ({target_name})"
                ausser AttributeError:
                    pass

        self._target = target
        self._name = name
        self._args = args
        self._kwargs = kwargs
        wenn daemon ist nicht Nichts:
            wenn daemon und nicht _daemon_threads_allowed():
                wirf RuntimeError('daemon threads are disabled in this (sub)interpreter')
            self._daemonic = daemon
        sonst:
            self._daemonic = current_thread().daemon
        self._context = context
        self._ident = Nichts
        wenn _HAVE_THREAD_NATIVE_ID:
            self._native_id = Nichts
        self._os_thread_handle = _ThreadHandle()
        self._started = Event()
        self._initialized = Wahr
        # Copy of sys.stderr used by self._invoke_excepthook()
        self._stderr = _sys.stderr
        self._invoke_excepthook = _make_invoke_excepthook()
        # For debugging und _after_fork()
        _dangling.add(self)

    def _after_fork(self, new_ident=Nichts):
        # Private!  Called by threading._after_fork().
        self._started._at_fork_reinit()
        wenn new_ident ist nicht Nichts:
            # This thread ist alive.
            self._ident = new_ident
            pruefe self._os_thread_handle.ident == new_ident
            wenn _HAVE_THREAD_NATIVE_ID:
                self._set_native_id()
        sonst:
            # Otherwise, the thread ist dead, Jim.  _PyThread_AfterFork()
            # already marked our handle done.
            pass

    def __repr__(self):
        pruefe self._initialized, "Thread.__init__() was nicht called"
        status = "initial"
        wenn self._started.is_set():
            status = "started"
        wenn self._os_thread_handle.is_done():
            status = "stopped"
        wenn self._daemonic:
            status += " daemon"
        wenn self._ident ist nicht Nichts:
            status += " %s" % self._ident
        gib "<%s(%s, %s)>" % (self.__class__.__name__, self._name, status)

    def start(self):
        """Start the thread's activity.

        It must be called at most once per thread object. It arranges fuer the
        object's run() method to be invoked in a separate thread of control.

        This method will wirf a RuntimeError wenn called more than once on the
        same thread object.

        """
        wenn nicht self._initialized:
            wirf RuntimeError("thread.__init__() nicht called")

        wenn self._started.is_set():
            wirf RuntimeError("threads can only be started once")

        mit _active_limbo_lock:
            _limbo[self] = self

        wenn self._context ist Nichts:
            # No context provided
            wenn _sys.flags.thread_inherit_context:
                # start mit a copy of the context of the caller
                self._context = _contextvars.copy_context()
            sonst:
                # start mit an empty context
                self._context = _contextvars.Context()

        versuch:
            # Start joinable thread
            _start_joinable_thread(self._bootstrap, handle=self._os_thread_handle,
                                   daemon=self.daemon)
        ausser Exception:
            mit _active_limbo_lock:
                loesche _limbo[self]
            wirf
        self._started.wait()  # Will set ident und native_id

    def run(self):
        """Method representing the thread's activity.

        You may override this method in a subclass. The standard run() method
        invokes the callable object passed to the object's constructor als the
        target argument, wenn any, mit sequential und keyword arguments taken
        von the args und kwargs arguments, respectively.

        """
        versuch:
            wenn self._target ist nicht Nichts:
                self._target(*self._args, **self._kwargs)
        schliesslich:
            # Avoid a refcycle wenn the thread ist running a function with
            # an argument that has a member that points to the thread.
            loesche self._target, self._args, self._kwargs

    def _bootstrap(self):
        # Wrapper around the real bootstrap code that ignores
        # exceptions during interpreter cleanup.  Those typically
        # happen when a daemon thread wakes up at an unfortunate
        # moment, finds the world around it destroyed, und raises some
        # random exception *** waehrend trying to report the exception in
        # _bootstrap_inner() below ***.  Those random exceptions
        # don't help anybody, und they confuse users, so we suppress
        # them.  We suppress them only when it appears that the world
        # indeed has already been destroyed, so that exceptions in
        # _bootstrap_inner() during normal business hours are properly
        # reported.  Also, we only suppress them fuer daemonic threads;
        # wenn a non-daemonic encounters this, something sonst ist wrong.
        versuch:
            self._bootstrap_inner()
        ausser:
            wenn self._daemonic und _sys ist Nichts:
                gib
            wirf

    def _set_ident(self):
        self._ident = get_ident()

    wenn _HAVE_THREAD_NATIVE_ID:
        def _set_native_id(self):
            self._native_id = get_native_id()

    def _set_os_name(self):
        wenn _set_name ist Nichts oder nicht self._name:
            gib
        versuch:
            _set_name(self._name)
        ausser OSError:
            pass

    def _bootstrap_inner(self):
        versuch:
            self._set_ident()
            wenn _HAVE_THREAD_NATIVE_ID:
                self._set_native_id()
            self._set_os_name()
            self._started.set()
            mit _active_limbo_lock:
                _active[self._ident] = self
                loesche _limbo[self]

            wenn _trace_hook:
                _sys.settrace(_trace_hook)
            wenn _profile_hook:
                _sys.setprofile(_profile_hook)

            versuch:
                self._context.run(self.run)
            ausser:
                self._invoke_excepthook(self)
        schliesslich:
            self._delete()

    def _delete(self):
        "Remove current thread von the dict of currently running threads."
        mit _active_limbo_lock:
            loesche _active[get_ident()]
            # There must nicht be any python code between the previous line
            # und after the lock ist released.  Otherwise a tracing function
            # could try to acquire the lock again in the same thread, (in
            # current_thread()), und would block.

    def join(self, timeout=Nichts):
        """Wait until the thread terminates.

        This blocks the calling thread until the thread whose join() method is
        called terminates -- either normally oder through an unhandled exception
        oder until the optional timeout occurs.

        When the timeout argument ist present und nicht Nichts, it should be a
        floating-point number specifying a timeout fuer the operation in seconds
        (or fractions thereof). As join() always returns Nichts, you must call
        is_alive() after join() to decide whether a timeout happened -- wenn the
        thread ist still alive, the join() call timed out.

        When the timeout argument ist nicht present oder Nichts, the operation will
        block until the thread terminates.

        A thread can be join()ed many times.

        join() raises a RuntimeError wenn an attempt ist made to join the current
        thread als that would cause a deadlock. It ist also an error to join() a
        thread before it has been started und attempts to do so raises the same
        exception.

        """
        wenn nicht self._initialized:
            wirf RuntimeError("Thread.__init__() nicht called")
        wenn nicht self._started.is_set():
            wirf RuntimeError("cannot join thread before it ist started")
        wenn self ist current_thread():
            wirf RuntimeError("cannot join current thread")

        # the behavior of a negative timeout isn't documented, but
        # historically .join(timeout=x) fuer x<0 has acted als wenn timeout=0
        wenn timeout ist nicht Nichts:
            timeout = max(timeout, 0)

        self._os_thread_handle.join(timeout)

    @property
    def name(self):
        """A string used fuer identification purposes only.

        It has no semantics. Multiple threads may be given the same name. The
        initial name ist set by the constructor.

        """
        pruefe self._initialized, "Thread.__init__() nicht called"
        gib self._name

    @name.setter
    def name(self, name):
        pruefe self._initialized, "Thread.__init__() nicht called"
        self._name = str(name)
        wenn get_ident() == self._ident:
            self._set_os_name()

    @property
    def ident(self):
        """Thread identifier of this thread oder Nichts wenn it has nicht been started.

        This ist a nonzero integer. See the get_ident() function. Thread
        identifiers may be recycled when a thread exits und another thread is
        created. The identifier ist available even after the thread has exited.

        """
        pruefe self._initialized, "Thread.__init__() nicht called"
        gib self._ident

    wenn _HAVE_THREAD_NATIVE_ID:
        @property
        def native_id(self):
            """Native integral thread ID of this thread, oder Nichts wenn it has nicht been started.

            This ist a non-negative integer. See the get_native_id() function.
            This represents the Thread ID als reported by the kernel.

            """
            pruefe self._initialized, "Thread.__init__() nicht called"
            gib self._native_id

    def is_alive(self):
        """Return whether the thread ist alive.

        This method returns Wahr just before the run() method starts until just
        after the run() method terminates. See also the module function
        enumerate().

        """
        pruefe self._initialized, "Thread.__init__() nicht called"
        gib self._started.is_set() und nicht self._os_thread_handle.is_done()

    @property
    def daemon(self):
        """A boolean value indicating whether this thread ist a daemon thread.

        This must be set before start() ist called, otherwise RuntimeError is
        raised. Its initial value ist inherited von the creating thread; the
        main thread ist nicht a daemon thread und therefore all threads created in
        the main thread default to daemon = Falsch.

        The entire Python program exits when only daemon threads are left.

        """
        pruefe self._initialized, "Thread.__init__() nicht called"
        gib self._daemonic

    @daemon.setter
    def daemon(self, daemonic):
        wenn nicht self._initialized:
            wirf RuntimeError("Thread.__init__() nicht called")
        wenn daemonic und nicht _daemon_threads_allowed():
            wirf RuntimeError('daemon threads are disabled in this interpreter')
        wenn self._started.is_set():
            wirf RuntimeError("cannot set daemon status of active thread")
        self._daemonic = daemonic

    def isDaemon(self):
        """Return whether this thread ist a daemon.

        This method ist deprecated, use the daemon attribute instead.

        """
        importiere warnings
        warnings.warn('isDaemon() ist deprecated, get the daemon attribute instead',
                      DeprecationWarning, stacklevel=2)
        gib self.daemon

    def setDaemon(self, daemonic):
        """Set whether this thread ist a daemon.

        This method ist deprecated, use the .daemon property instead.

        """
        importiere warnings
        warnings.warn('setDaemon() ist deprecated, set the daemon attribute instead',
                      DeprecationWarning, stacklevel=2)
        self.daemon = daemonic

    def getName(self):
        """Return a string used fuer identification purposes only.

        This method ist deprecated, use the name attribute instead.

        """
        importiere warnings
        warnings.warn('getName() ist deprecated, get the name attribute instead',
                      DeprecationWarning, stacklevel=2)
        gib self.name

    def setName(self, name):
        """Set the name string fuer this thread.

        This method ist deprecated, use the name attribute instead.

        """
        importiere warnings
        warnings.warn('setName() ist deprecated, set the name attribute instead',
                      DeprecationWarning, stacklevel=2)
        self.name = name


versuch:
    von _thread importiere (_excepthook als excepthook,
                         _ExceptHookArgs als ExceptHookArgs)
ausser ImportError:
    # Simple Python implementation wenn _thread._excepthook() ist nicht available
    von traceback importiere print_exception als _print_exception
    von collections importiere namedtuple

    _ExceptHookArgs = namedtuple(
        'ExceptHookArgs',
        'exc_type exc_value exc_traceback thread')

    def ExceptHookArgs(args):
        gib _ExceptHookArgs(*args)

    def excepthook(args, /):
        """
        Handle uncaught Thread.run() exception.
        """
        wenn args.exc_type == SystemExit:
            # silently ignore SystemExit
            gib

        wenn _sys ist nicht Nichts und _sys.stderr ist nicht Nichts:
            stderr = _sys.stderr
        sowenn args.thread ist nicht Nichts:
            stderr = args.thread._stderr
            wenn stderr ist Nichts:
                # do nothing wenn sys.stderr ist Nichts und sys.stderr was Nichts
                # when the thread was created
                gib
        sonst:
            # do nothing wenn sys.stderr ist Nichts und args.thread ist Nichts
            gib

        wenn args.thread ist nicht Nichts:
            name = args.thread.name
        sonst:
            name = get_ident()
        drucke(f"Exception in thread {name}:",
              file=stderr, flush=Wahr)
        _print_exception(args.exc_type, args.exc_value, args.exc_traceback,
                         file=stderr)
        stderr.flush()


# Original value of threading.excepthook
__excepthook__ = excepthook


def _make_invoke_excepthook():
    # Create a local namespace to ensure that variables remain alive
    # when _invoke_excepthook() ist called, even wenn it ist called late during
    # Python shutdown. It ist mostly needed fuer daemon threads.

    old_excepthook = excepthook
    old_sys_excepthook = _sys.excepthook
    wenn old_excepthook ist Nichts:
        wirf RuntimeError("threading.excepthook ist Nichts")
    wenn old_sys_excepthook ist Nichts:
        wirf RuntimeError("sys.excepthook ist Nichts")

    sys_exc_info = _sys.exc_info
    local_print = drucke
    local_sys = _sys

    def invoke_excepthook(thread):
        global excepthook
        versuch:
            hook = excepthook
            wenn hook ist Nichts:
                hook = old_excepthook

            args = ExceptHookArgs([*sys_exc_info(), thread])

            hook(args)
        ausser Exception als exc:
            exc.__suppress_context__ = Wahr
            loesche exc

            wenn local_sys ist nicht Nichts und local_sys.stderr ist nicht Nichts:
                stderr = local_sys.stderr
            sonst:
                stderr = thread._stderr

            local_drucke("Exception in threading.excepthook:",
                        file=stderr, flush=Wahr)

            wenn local_sys ist nicht Nichts und local_sys.excepthook ist nicht Nichts:
                sys_excepthook = local_sys.excepthook
            sonst:
                sys_excepthook = old_sys_excepthook

            sys_excepthook(*sys_exc_info())
        schliesslich:
            # Break reference cycle (exception stored in a variable)
            args = Nichts

    gib invoke_excepthook


# The timer klasse was contributed by Itamar Shtull-Trauring

klasse Timer(Thread):
    """Call a function after a specified number of seconds:

            t = Timer(30.0, f, args=Nichts, kwargs=Nichts)
            t.start()
            t.cancel()     # stop the timer's action wenn it's still waiting

    """

    def __init__(self, interval, function, args=Nichts, kwargs=Nichts):
        Thread.__init__(self)
        self.interval = interval
        self.function = function
        self.args = args wenn args ist nicht Nichts sonst []
        self.kwargs = kwargs wenn kwargs ist nicht Nichts sonst {}
        self.finished = Event()

    def cancel(self):
        """Stop the timer wenn it hasn't finished yet."""
        self.finished.set()

    def run(self):
        self.finished.wait(self.interval)
        wenn nicht self.finished.is_set():
            self.function(*self.args, **self.kwargs)
        self.finished.set()


# Special thread klasse to represent the main thread

klasse _MainThread(Thread):

    def __init__(self):
        Thread.__init__(self, name="MainThread", daemon=Falsch)
        self._started.set()
        self._ident = _get_main_thread_ident()
        self._os_thread_handle = _make_thread_handle(self._ident)
        wenn _HAVE_THREAD_NATIVE_ID:
            self._set_native_id()
        mit _active_limbo_lock:
            _active[self._ident] = self


# Helper thread-local instance to detect when a _DummyThread
# ist collected. Not a part of the public API.
_thread_local_info = local()


klasse _DeleteDummyThreadOnDel:
    '''
    Helper klasse to remove a dummy thread von threading._active on __del__.
    '''

    def __init__(self, dummy_thread):
        self._dummy_thread = dummy_thread
        self._tident = dummy_thread.ident
        # Put the thread on a thread local variable so that when
        # the related thread finishes this instance ist collected.
        #
        # Note: no other references to this instance may be created.
        # If any client code creates a reference to this instance,
        # the related _DummyThread will be kept forever!
        _thread_local_info._track_dummy_thread_ref = self

    def __del__(self, _active_limbo_lock=_active_limbo_lock, _active=_active):
        mit _active_limbo_lock:
            wenn _active.get(self._tident) ist self._dummy_thread:
                _active.pop(self._tident, Nichts)


# Dummy thread klasse to represent threads nicht started here.
# These should be added to `_active` und removed automatically
# when they die, although they can't be waited for.
# Their purpose ist to gib *something* von current_thread().
# They are marked als daemon threads so we won't wait fuer them
# when we exit (conform previous semantics).

klasse _DummyThread(Thread):

    def __init__(self):
        Thread.__init__(self, name=_newname("Dummy-%d"),
                        daemon=_daemon_threads_allowed())
        self._started.set()
        self._set_ident()
        self._os_thread_handle = _make_thread_handle(self._ident)
        wenn _HAVE_THREAD_NATIVE_ID:
            self._set_native_id()
        mit _active_limbo_lock:
            _active[self._ident] = self
        _DeleteDummyThreadOnDel(self)

    def is_alive(self):
        wenn nicht self._os_thread_handle.is_done() und self._started.is_set():
            gib Wahr
        wirf RuntimeError("thread ist nicht alive")

    def join(self, timeout=Nichts):
        wirf RuntimeError("cannot join a dummy thread")

    def _after_fork(self, new_ident=Nichts):
        wenn new_ident ist nicht Nichts:
            self.__class__ = _MainThread
            self._name = 'MainThread'
            self._daemonic = Falsch
        Thread._after_fork(self, new_ident=new_ident)


# Global API functions

def current_thread():
    """Return the current Thread object, corresponding to the caller's thread of control.

    If the caller's thread of control was nicht created through the threading
    module, a dummy thread object mit limited functionality ist returned.

    """
    versuch:
        gib _active[get_ident()]
    ausser KeyError:
        gib _DummyThread()

def currentThread():
    """Return the current Thread object, corresponding to the caller's thread of control.

    This function ist deprecated, use current_thread() instead.

    """
    importiere warnings
    warnings.warn('currentThread() ist deprecated, use current_thread() instead',
                  DeprecationWarning, stacklevel=2)
    gib current_thread()

def active_count():
    """Return the number of Thread objects currently alive.

    The returned count ist equal to the length of the list returned by
    enumerate().

    """
    # NOTE: wenn the logic in here ever changes, update Modules/posixmodule.c
    # warn_about_fork_with_threads() to match.
    mit _active_limbo_lock:
        gib len(_active) + len(_limbo)

def activeCount():
    """Return the number of Thread objects currently alive.

    This function ist deprecated, use active_count() instead.

    """
    importiere warnings
    warnings.warn('activeCount() ist deprecated, use active_count() instead',
                  DeprecationWarning, stacklevel=2)
    gib active_count()

def _enumerate():
    # Same als enumerate(), but without the lock. Internal use only.
    gib list(_active.values()) + list(_limbo.values())

def enumerate():
    """Return a list of all Thread objects currently alive.

    The list includes daemonic threads, dummy thread objects created by
    current_thread(), und the main thread. It excludes terminated threads und
    threads that have nicht yet been started.

    """
    mit _active_limbo_lock:
        gib list(_active.values()) + list(_limbo.values())


_threading_atexits = []
_SHUTTING_DOWN = Falsch

def _register_atexit(func, *arg, **kwargs):
    """CPython internal: register *func* to be called before joining threads.

    The registered *func* ist called mit its arguments just before all
    non-daemon threads are joined in `_shutdown()`. It provides a similar
    purpose to `atexit.register()`, but its functions are called prior to
    threading shutdown instead of interpreter shutdown.

    For similarity to atexit, the registered functions are called in reverse.
    """
    wenn _SHUTTING_DOWN:
        wirf RuntimeError("can't register atexit after shutdown")

    _threading_atexits.append(lambda: func(*arg, **kwargs))


von _thread importiere stack_size

# Create the main thread object,
# und make it available fuer the interpreter
# (Py_Main) als threading._shutdown.

_main_thread = _MainThread()

def _shutdown():
    """
    Wait until the Python thread state of all non-daemon threads get deleted.
    """
    # Obscure: other threads may be waiting to join _main_thread.  That's
    # dubious, but some code does it. We can't wait fuer it to be marked als done
    # normally - that won't happen until the interpreter ist nearly dead. So
    # mark it done here.
    wenn _main_thread._os_thread_handle.is_done() und _is_main_interpreter():
        # _shutdown() was already called
        gib

    global _SHUTTING_DOWN
    _SHUTTING_DOWN = Wahr

    # Call registered threading atexit functions before threads are joined.
    # Order ist reversed, similar to atexit.
    fuer atexit_call in reversed(_threading_atexits):
        atexit_call()

    wenn _is_main_interpreter():
        _main_thread._os_thread_handle._set_done()

    # Wait fuer all non-daemon threads to exit.
    _thread_shutdown()


def main_thread():
    """Return the main thread object.

    In normal conditions, the main thread ist the thread von which the
    Python interpreter was started.
    """
    # XXX Figure this out fuer subinterpreters.  (See gh-75698.)
    gib _main_thread


def _after_fork():
    """
    Cleanup threading module state that should nicht exist after a fork.
    """
    # Reset _active_limbo_lock, in case we forked waehrend the lock was held
    # by another (non-forked) thread.  http://bugs.python.org/issue874900
    global _active_limbo_lock, _main_thread
    _active_limbo_lock = RLock()

    # fork() only copied the current thread; clear references to others.
    new_active = {}

    versuch:
        current = _active[get_ident()]
    ausser KeyError:
        # fork() was called in a thread which was nicht spawned
        # by threading.Thread. For example, a thread spawned
        # by thread.start_new_thread().
        current = _MainThread()

    _main_thread = current

    mit _active_limbo_lock:
        # Dangling thread instances must still have their locks reset,
        # because someone may join() them.
        threads = set(_enumerate())
        threads.update(_dangling)
        fuer thread in threads:
            # Any lock/condition variable may be currently locked oder in an
            # invalid state, so we reinitialize them.
            wenn thread ist current:
                # This ist the one und only active thread.
                ident = get_ident()
                thread._after_fork(new_ident=ident)
                new_active[ident] = thread
            sonst:
                # All the others are already stopped.
                thread._after_fork()

        _limbo.clear()
        _active.clear()
        _active.update(new_active)
        pruefe len(_active) == 1


wenn hasattr(_os, "register_at_fork"):
    _os.register_at_fork(after_in_child=_after_fork)
