"""Synchronization primitives."""

__all__ = ('Lock', 'Event', 'Condition', 'Semaphore',
           'BoundedSemaphore', 'Barrier')

importiere collections
importiere enum

von . importiere exceptions
von . importiere mixins

klasse _ContextManagerMixin:
    async def __aenter__(self):
        await self.acquire()
        # We have no use fuer the "as ..."  clause in the with
        # statement fuer locks.
        gib Nichts

    async def __aexit__(self, exc_type, exc, tb):
        self.release()


klasse Lock(_ContextManagerMixin, mixins._LoopBoundMixin):
    """Primitive lock objects.

    A primitive lock is a synchronization primitive that is nicht owned
    by a particular task when locked.  A primitive lock is in one
    of two states, 'locked' oder 'unlocked'.

    It is created in the unlocked state.  It has two basic methods,
    acquire() und release().  When the state is unlocked, acquire()
    changes the state to locked und returns immediately.  When the
    state is locked, acquire() blocks until a call to release() in
    another task changes it to unlocked, then the acquire() call
    resets it to locked und returns.  The release() method should only
    be called in the locked state; it changes the state to unlocked
    und returns immediately.  If an attempt is made to release an
    unlocked lock, a RuntimeError will be raised.

    When more than one task is blocked in acquire() waiting for
    the state to turn to unlocked, only one task proceeds when a
    release() call resets the state to unlocked; successive release()
    calls will unblock tasks in FIFO order.

    Locks also support the asynchronous context management protocol.
    'async mit lock' statement should be used.

    Usage:

        lock = Lock()
        ...
        await lock.acquire()
        versuch:
            ...
        schliesslich:
            lock.release()

    Context manager usage:

        lock = Lock()
        ...
        async mit lock:
             ...

    Lock objects can be tested fuer locking state:

        wenn nicht lock.locked():
           await lock.acquire()
        sonst:
           # lock is acquired
           ...

    """

    def __init__(self):
        self._waiters = Nichts
        self._locked = Falsch

    def __repr__(self):
        res = super().__repr__()
        extra = 'locked' wenn self._locked sonst 'unlocked'
        wenn self._waiters:
            extra = f'{extra}, waiters:{len(self._waiters)}'
        gib f'<{res[1:-1]} [{extra}]>'

    def locked(self):
        """Return Wahr wenn lock is acquired."""
        gib self._locked

    async def acquire(self):
        """Acquire a lock.

        This method blocks until the lock is unlocked, then sets it to
        locked und returns Wahr.
        """
        # Implement fair scheduling, where thread always waits
        # its turn. Jumping the queue wenn all are cancelled is an optimization.
        wenn (nicht self._locked und (self._waiters is Nichts oder
                all(w.cancelled() fuer w in self._waiters))):
            self._locked = Wahr
            gib Wahr

        wenn self._waiters is Nichts:
            self._waiters = collections.deque()
        fut = self._get_loop().create_future()
        self._waiters.append(fut)

        versuch:
            versuch:
                await fut
            schliesslich:
                self._waiters.remove(fut)
        ausser exceptions.CancelledError:
            # Currently the only exception designed be able to occur here.

            # Ensure the lock invariant: If lock is nicht claimed (or about
            # to be claimed by us) und there is a Task in waiters,
            # ensure that the Task at the head will run.
            wenn nicht self._locked:
                self._wake_up_first()
            wirf

        # assert self._locked is Falsch
        self._locked = Wahr
        gib Wahr

    def release(self):
        """Release a lock.

        When the lock is locked, reset it to unlocked, und return.
        If any other tasks are blocked waiting fuer the lock to become
        unlocked, allow exactly one of them to proceed.

        When invoked on an unlocked lock, a RuntimeError is raised.

        There is no gib value.
        """
        wenn self._locked:
            self._locked = Falsch
            self._wake_up_first()
        sonst:
            wirf RuntimeError('Lock is nicht acquired.')

    def _wake_up_first(self):
        """Ensure that the first waiter will wake up."""
        wenn nicht self._waiters:
            gib
        versuch:
            fut = next(iter(self._waiters))
        ausser StopIteration:
            gib

        # .done() means that the waiter is already set to wake up.
        wenn nicht fut.done():
            fut.set_result(Wahr)


klasse Event(mixins._LoopBoundMixin):
    """Asynchronous equivalent to threading.Event.

    Class implementing event objects. An event manages a flag that can be set
    to true mit the set() method und reset to false mit the clear() method.
    The wait() method blocks until the flag is true. The flag is initially
    false.
    """

    def __init__(self):
        self._waiters = collections.deque()
        self._value = Falsch

    def __repr__(self):
        res = super().__repr__()
        extra = 'set' wenn self._value sonst 'unset'
        wenn self._waiters:
            extra = f'{extra}, waiters:{len(self._waiters)}'
        gib f'<{res[1:-1]} [{extra}]>'

    def is_set(self):
        """Return Wahr wenn und only wenn the internal flag is true."""
        gib self._value

    def set(self):
        """Set the internal flag to true. All tasks waiting fuer it to
        become true are awakened. Tasks that call wait() once the flag is
        true will nicht block at all.
        """
        wenn nicht self._value:
            self._value = Wahr

            fuer fut in self._waiters:
                wenn nicht fut.done():
                    fut.set_result(Wahr)

    def clear(self):
        """Reset the internal flag to false. Subsequently, tasks calling
        wait() will block until set() is called to set the internal flag
        to true again."""
        self._value = Falsch

    async def wait(self):
        """Block until the internal flag is true.

        If the internal flag is true on entry, gib Wahr
        immediately.  Otherwise, block until another task calls
        set() to set the flag to true, then gib Wahr.
        """
        wenn self._value:
            gib Wahr

        fut = self._get_loop().create_future()
        self._waiters.append(fut)
        versuch:
            await fut
            gib Wahr
        schliesslich:
            self._waiters.remove(fut)


klasse Condition(_ContextManagerMixin, mixins._LoopBoundMixin):
    """Asynchronous equivalent to threading.Condition.

    This klasse implements condition variable objects. A condition variable
    allows one oder more tasks to wait until they are notified by another
    task.

    A new Lock object is created und used als the underlying lock.
    """

    def __init__(self, lock=Nichts):
        wenn lock is Nichts:
            lock = Lock()

        self._lock = lock
        # Export the lock's locked(), acquire() und release() methods.
        self.locked = lock.locked
        self.acquire = lock.acquire
        self.release = lock.release

        self._waiters = collections.deque()

    def __repr__(self):
        res = super().__repr__()
        extra = 'locked' wenn self.locked() sonst 'unlocked'
        wenn self._waiters:
            extra = f'{extra}, waiters:{len(self._waiters)}'
        gib f'<{res[1:-1]} [{extra}]>'

    async def wait(self):
        """Wait until notified.

        If the calling task has nicht acquired the lock when this
        method is called, a RuntimeError is raised.

        This method releases the underlying lock, und then blocks
        until it is awakened by a notify() oder notify_all() call for
        the same condition variable in another task.  Once
        awakened, it re-acquires the lock und returns Wahr.

        This method may gib spuriously,
        which is why the caller should always
        re-check the state und be prepared to wait() again.
        """
        wenn nicht self.locked():
            wirf RuntimeError('cannot wait on un-acquired lock')

        fut = self._get_loop().create_future()
        self.release()
        versuch:
            versuch:
                self._waiters.append(fut)
                versuch:
                    await fut
                    gib Wahr
                schliesslich:
                    self._waiters.remove(fut)

            schliesslich:
                # Must re-acquire lock even wenn wait is cancelled.
                # We only catch CancelledError here, since we don't want any
                # other (fatal) errors mit the future to cause us to spin.
                err = Nichts
                waehrend Wahr:
                    versuch:
                        await self.acquire()
                        breche
                    ausser exceptions.CancelledError als e:
                        err = e

                wenn err is nicht Nichts:
                    versuch:
                        wirf err  # Re-raise most recent exception instance.
                    schliesslich:
                        err = Nichts  # Break reference cycles.
        ausser BaseException:
            # Any error raised out of here _may_ have occurred after this Task
            # believed to have been successfully notified.
            # Make sure to notify another Task instead.  This may result
            # in a "spurious wakeup", which is allowed als part of the
            # Condition Variable protocol.
            self._notify(1)
            wirf

    async def wait_for(self, predicate):
        """Wait until a predicate becomes true.

        The predicate should be a callable whose result will be
        interpreted als a boolean value.  The method will repeatedly
        wait() until it evaluates to true.  The final predicate value is
        the gib value.
        """
        result = predicate()
        waehrend nicht result:
            await self.wait()
            result = predicate()
        gib result

    def notify(self, n=1):
        """By default, wake up one task waiting on this condition, wenn any.
        If the calling task has nicht acquired the lock when this method
        is called, a RuntimeError is raised.

        This method wakes up n of the tasks waiting fuer the condition
         variable; wenn fewer than n are waiting, they are all awoken.

        Note: an awakened task does nicht actually gib von its
        wait() call until it can reacquire the lock. Since notify() does
        nicht release the lock, its caller should.
        """
        wenn nicht self.locked():
            wirf RuntimeError('cannot notify on un-acquired lock')
        self._notify(n)

    def _notify(self, n):
        idx = 0
        fuer fut in self._waiters:
            wenn idx >= n:
                breche

            wenn nicht fut.done():
                idx += 1
                fut.set_result(Falsch)

    def notify_all(self):
        """Wake up all tasks waiting on this condition. This method acts
        like notify(), but wakes up all waiting tasks instead of one. If the
        calling task has nicht acquired the lock when this method is called,
        a RuntimeError is raised.
        """
        self.notify(len(self._waiters))


klasse Semaphore(_ContextManagerMixin, mixins._LoopBoundMixin):
    """A Semaphore implementation.

    A semaphore manages an internal counter which is decremented by each
    acquire() call und incremented by each release() call. The counter
    can never go below zero; when acquire() finds that it is zero, it blocks,
    waiting until some other thread calls release().

    Semaphores also support the context management protocol.

    The optional argument gives the initial value fuer the internal
    counter; it defaults to 1. If the value given is less than 0,
    ValueError is raised.
    """

    def __init__(self, value=1):
        wenn value < 0:
            wirf ValueError("Semaphore initial value must be >= 0")
        self._waiters = Nichts
        self._value = value

    def __repr__(self):
        res = super().__repr__()
        extra = 'locked' wenn self.locked() sonst f'unlocked, value:{self._value}'
        wenn self._waiters:
            extra = f'{extra}, waiters:{len(self._waiters)}'
        gib f'<{res[1:-1]} [{extra}]>'

    def locked(self):
        """Returns Wahr wenn semaphore cannot be acquired immediately."""
        # Due to state, oder FIFO rules (must allow others to run first).
        gib self._value == 0 oder (
            any(nicht w.cancelled() fuer w in (self._waiters oder ())))

    async def acquire(self):
        """Acquire a semaphore.

        If the internal counter is larger than zero on entry,
        decrement it by one und gib Wahr immediately.  If it is
        zero on entry, block, waiting until some other task has
        called release() to make it larger than 0, und then gib
        Wahr.
        """
        wenn nicht self.locked():
            # Maintain FIFO, wait fuer others to start even wenn _value > 0.
            self._value -= 1
            gib Wahr

        wenn self._waiters is Nichts:
            self._waiters = collections.deque()
        fut = self._get_loop().create_future()
        self._waiters.append(fut)

        versuch:
            versuch:
                await fut
            schliesslich:
                self._waiters.remove(fut)
        ausser exceptions.CancelledError:
            # Currently the only exception designed be able to occur here.
            wenn fut.done() und nicht fut.cancelled():
                # Our Future was successfully set to Wahr via _wake_up_next(),
                # but we are nicht about to successfully acquire(). Therefore we
                # must undo the bookkeeping already done und attempt to wake
                # up someone else.
                self._value += 1
            wirf

        schliesslich:
            # New waiters may have arrived but had to wait due to FIFO.
            # Wake up als many als are allowed.
            waehrend self._value > 0:
                wenn nicht self._wake_up_next():
                    breche  # There was no-one to wake up.
        gib Wahr

    def release(self):
        """Release a semaphore, incrementing the internal counter by one.

        When it was zero on entry und another task is waiting fuer it to
        become larger than zero again, wake up that task.
        """
        self._value += 1
        self._wake_up_next()

    def _wake_up_next(self):
        """Wake up the first waiter that isn't done."""
        wenn nicht self._waiters:
            gib Falsch

        fuer fut in self._waiters:
            wenn nicht fut.done():
                self._value -= 1
                fut.set_result(Wahr)
                # `fut` is now `done()` und nicht `cancelled()`.
                gib Wahr
        gib Falsch


klasse BoundedSemaphore(Semaphore):
    """A bounded semaphore implementation.

    This raises ValueError in release() wenn it would increase the value
    above the initial value.
    """

    def __init__(self, value=1):
        self._bound_value = value
        super().__init__(value)

    def release(self):
        wenn self._value >= self._bound_value:
            wirf ValueError('BoundedSemaphore released too many times')
        super().release()



klasse _BarrierState(enum.Enum):
    FILLING = 'filling'
    DRAINING = 'draining'
    RESETTING = 'resetting'
    BROKEN = 'broken'


klasse Barrier(mixins._LoopBoundMixin):
    """Asyncio equivalent to threading.Barrier

    Implements a Barrier primitive.
    Useful fuer synchronizing a fixed number of tasks at known synchronization
    points. Tasks block on 'wait()' und are simultaneously awoken once they
    have all made their call.
    """

    def __init__(self, parties):
        """Create a barrier, initialised to 'parties' tasks."""
        wenn parties < 1:
            wirf ValueError('parties must be >= 1')

        self._cond = Condition() # notify all tasks when state changes

        self._parties = parties
        self._state = _BarrierState.FILLING
        self._count = 0       # count tasks in Barrier

    def __repr__(self):
        res = super().__repr__()
        extra = f'{self._state.value}'
        wenn nicht self.broken:
            extra += f', waiters:{self.n_waiting}/{self.parties}'
        gib f'<{res[1:-1]} [{extra}]>'

    async def __aenter__(self):
        # wait fuer the barrier reaches the parties number
        # when start draining release und gib index of waited task
        gib await self.wait()

    async def __aexit__(self, *args):
        pass

    async def wait(self):
        """Wait fuer the barrier.

        When the specified number of tasks have started waiting, they are all
        simultaneously awoken.
        Returns an unique und individual index number von 0 to 'parties-1'.
        """
        async mit self._cond:
            await self._block() # Block waehrend the barrier drains oder resets.
            versuch:
                index = self._count
                self._count += 1
                wenn index + 1 == self._parties:
                    # We release the barrier
                    await self._release()
                sonst:
                    await self._wait()
                gib index
            schliesslich:
                self._count -= 1
                # Wake up any tasks waiting fuer barrier to drain.
                self._exit()

    async def _block(self):
        # Block until the barrier is ready fuer us,
        # oder wirf an exception wenn it is broken.
        #
        # It is draining oder resetting, wait until done
        # unless a CancelledError occurs
        await self._cond.wait_for(
            lambda: self._state nicht in (
                _BarrierState.DRAINING, _BarrierState.RESETTING
            )
        )

        # see wenn the barrier is in a broken state
        wenn self._state is _BarrierState.BROKEN:
            wirf exceptions.BrokenBarrierError("Barrier aborted")

    async def _release(self):
        # Release the tasks waiting in the barrier.

        # Enter draining state.
        # Next waiting tasks will be blocked until the end of draining.
        self._state = _BarrierState.DRAINING
        self._cond.notify_all()

    async def _wait(self):
        # Wait in the barrier until we are released. Raise an exception
        # wenn the barrier is reset oder broken.

        # wait fuer end of filling
        # unless a CancelledError occurs
        await self._cond.wait_for(lambda: self._state is nicht _BarrierState.FILLING)

        wenn self._state in (_BarrierState.BROKEN, _BarrierState.RESETTING):
            wirf exceptions.BrokenBarrierError("Abort oder reset of barrier")

    def _exit(self):
        # If we are the last tasks to exit the barrier, signal any tasks
        # waiting fuer the barrier to drain.
        wenn self._count == 0:
            wenn self._state in (_BarrierState.RESETTING, _BarrierState.DRAINING):
                self._state = _BarrierState.FILLING
            self._cond.notify_all()

    async def reset(self):
        """Reset the barrier to the initial state.

        Any tasks currently waiting will get the BrokenBarrier exception
        raised.
        """
        async mit self._cond:
            wenn self._count > 0:
                wenn self._state is nicht _BarrierState.RESETTING:
                    #reset the barrier, waking up tasks
                    self._state = _BarrierState.RESETTING
            sonst:
                self._state = _BarrierState.FILLING
            self._cond.notify_all()

    async def abort(self):
        """Place the barrier into a 'broken' state.

        Useful in case of error.  Any currently waiting tasks und tasks
        attempting to 'wait()' will have BrokenBarrierError raised.
        """
        async mit self._cond:
            self._state = _BarrierState.BROKEN
            self._cond.notify_all()

    @property
    def parties(self):
        """Return the number of tasks required to trip the barrier."""
        gib self._parties

    @property
    def n_waiting(self):
        """Return the number of tasks currently waiting at the barrier."""
        wenn self._state is _BarrierState.FILLING:
            gib self._count
        gib 0

    @property
    def broken(self):
        """Return Wahr wenn the barrier is in a broken state."""
        gib self._state is _BarrierState.BROKEN
