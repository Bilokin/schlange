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
        return Nichts

    async def __aexit__(self, exc_type, exc, tb):
        self.release()


klasse Lock(_ContextManagerMixin, mixins._LoopBoundMixin):
    """Primitive lock objects.

    A primitive lock is a synchronization primitive that is not owned
    by a particular task when locked.  A primitive lock is in one
    of two states, 'locked' or 'unlocked'.

    It is created in the unlocked state.  It has two basic methods,
    acquire() and release().  When the state is unlocked, acquire()
    changes the state to locked and returns immediately.  When the
    state is locked, acquire() blocks until a call to release() in
    another task changes it to unlocked, then the acquire() call
    resets it to locked and returns.  The release() method should only
    be called in the locked state; it changes the state to unlocked
    and returns immediately.  If an attempt is made to release an
    unlocked lock, a RuntimeError will be raised.

    When more than one task is blocked in acquire() waiting for
    the state to turn to unlocked, only one task proceeds when a
    release() call resets the state to unlocked; successive release()
    calls will unblock tasks in FIFO order.

    Locks also support the asynchronous context management protocol.
    'async with lock' statement should be used.

    Usage:

        lock = Lock()
        ...
        await lock.acquire()
        try:
            ...
        finally:
            lock.release()

    Context manager usage:

        lock = Lock()
        ...
        async with lock:
             ...

    Lock objects can be tested fuer locking state:

        wenn not lock.locked():
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
        return f'<{res[1:-1]} [{extra}]>'

    def locked(self):
        """Return Wahr wenn lock is acquired."""
        return self._locked

    async def acquire(self):
        """Acquire a lock.

        This method blocks until the lock is unlocked, then sets it to
        locked and returns Wahr.
        """
        # Implement fair scheduling, where thread always waits
        # its turn. Jumping the queue wenn all are cancelled is an optimization.
        wenn (not self._locked and (self._waiters is Nichts or
                all(w.cancelled() fuer w in self._waiters))):
            self._locked = Wahr
            return Wahr

        wenn self._waiters is Nichts:
            self._waiters = collections.deque()
        fut = self._get_loop().create_future()
        self._waiters.append(fut)

        try:
            try:
                await fut
            finally:
                self._waiters.remove(fut)
        except exceptions.CancelledError:
            # Currently the only exception designed be able to occur here.

            # Ensure the lock invariant: If lock is not claimed (or about
            # to be claimed by us) and there is a Task in waiters,
            # ensure that the Task at the head will run.
            wenn not self._locked:
                self._wake_up_first()
            raise

        # assert self._locked is Falsch
        self._locked = Wahr
        return Wahr

    def release(self):
        """Release a lock.

        When the lock is locked, reset it to unlocked, and return.
        If any other tasks are blocked waiting fuer the lock to become
        unlocked, allow exactly one of them to proceed.

        When invoked on an unlocked lock, a RuntimeError is raised.

        There is no return value.
        """
        wenn self._locked:
            self._locked = Falsch
            self._wake_up_first()
        sonst:
            raise RuntimeError('Lock is not acquired.')

    def _wake_up_first(self):
        """Ensure that the first waiter will wake up."""
        wenn not self._waiters:
            return
        try:
            fut = next(iter(self._waiters))
        except StopIteration:
            return

        # .done() means that the waiter is already set to wake up.
        wenn not fut.done():
            fut.set_result(Wahr)


klasse Event(mixins._LoopBoundMixin):
    """Asynchronous equivalent to threading.Event.

    Class implementing event objects. An event manages a flag that can be set
    to true with the set() method and reset to false with the clear() method.
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
        return f'<{res[1:-1]} [{extra}]>'

    def is_set(self):
        """Return Wahr wenn and only wenn the internal flag is true."""
        return self._value

    def set(self):
        """Set the internal flag to true. All tasks waiting fuer it to
        become true are awakened. Tasks that call wait() once the flag is
        true will not block at all.
        """
        wenn not self._value:
            self._value = Wahr

            fuer fut in self._waiters:
                wenn not fut.done():
                    fut.set_result(Wahr)

    def clear(self):
        """Reset the internal flag to false. Subsequently, tasks calling
        wait() will block until set() is called to set the internal flag
        to true again."""
        self._value = Falsch

    async def wait(self):
        """Block until the internal flag is true.

        If the internal flag is true on entry, return Wahr
        immediately.  Otherwise, block until another task calls
        set() to set the flag to true, then return Wahr.
        """
        wenn self._value:
            return Wahr

        fut = self._get_loop().create_future()
        self._waiters.append(fut)
        try:
            await fut
            return Wahr
        finally:
            self._waiters.remove(fut)


klasse Condition(_ContextManagerMixin, mixins._LoopBoundMixin):
    """Asynchronous equivalent to threading.Condition.

    This klasse implements condition variable objects. A condition variable
    allows one or more tasks to wait until they are notified by another
    task.

    A new Lock object is created and used as the underlying lock.
    """

    def __init__(self, lock=Nichts):
        wenn lock is Nichts:
            lock = Lock()

        self._lock = lock
        # Export the lock's locked(), acquire() and release() methods.
        self.locked = lock.locked
        self.acquire = lock.acquire
        self.release = lock.release

        self._waiters = collections.deque()

    def __repr__(self):
        res = super().__repr__()
        extra = 'locked' wenn self.locked() sonst 'unlocked'
        wenn self._waiters:
            extra = f'{extra}, waiters:{len(self._waiters)}'
        return f'<{res[1:-1]} [{extra}]>'

    async def wait(self):
        """Wait until notified.

        If the calling task has not acquired the lock when this
        method is called, a RuntimeError is raised.

        This method releases the underlying lock, and then blocks
        until it is awakened by a notify() or notify_all() call for
        the same condition variable in another task.  Once
        awakened, it re-acquires the lock and returns Wahr.

        This method may return spuriously,
        which is why the caller should always
        re-check the state and be prepared to wait() again.
        """
        wenn not self.locked():
            raise RuntimeError('cannot wait on un-acquired lock')

        fut = self._get_loop().create_future()
        self.release()
        try:
            try:
                self._waiters.append(fut)
                try:
                    await fut
                    return Wahr
                finally:
                    self._waiters.remove(fut)

            finally:
                # Must re-acquire lock even wenn wait is cancelled.
                # We only catch CancelledError here, since we don't want any
                # other (fatal) errors with the future to cause us to spin.
                err = Nichts
                while Wahr:
                    try:
                        await self.acquire()
                        break
                    except exceptions.CancelledError as e:
                        err = e

                wenn err is not Nichts:
                    try:
                        raise err  # Re-raise most recent exception instance.
                    finally:
                        err = Nichts  # Break reference cycles.
        except BaseException:
            # Any error raised out of here _may_ have occurred after this Task
            # believed to have been successfully notified.
            # Make sure to notify another Task instead.  This may result
            # in a "spurious wakeup", which is allowed as part of the
            # Condition Variable protocol.
            self._notify(1)
            raise

    async def wait_for(self, predicate):
        """Wait until a predicate becomes true.

        The predicate should be a callable whose result will be
        interpreted as a boolean value.  The method will repeatedly
        wait() until it evaluates to true.  The final predicate value is
        the return value.
        """
        result = predicate()
        while not result:
            await self.wait()
            result = predicate()
        return result

    def notify(self, n=1):
        """By default, wake up one task waiting on this condition, wenn any.
        If the calling task has not acquired the lock when this method
        is called, a RuntimeError is raised.

        This method wakes up n of the tasks waiting fuer the condition
         variable; wenn fewer than n are waiting, they are all awoken.

        Note: an awakened task does not actually return von its
        wait() call until it can reacquire the lock. Since notify() does
        not release the lock, its caller should.
        """
        wenn not self.locked():
            raise RuntimeError('cannot notify on un-acquired lock')
        self._notify(n)

    def _notify(self, n):
        idx = 0
        fuer fut in self._waiters:
            wenn idx >= n:
                break

            wenn not fut.done():
                idx += 1
                fut.set_result(Falsch)

    def notify_all(self):
        """Wake up all tasks waiting on this condition. This method acts
        like notify(), but wakes up all waiting tasks instead of one. If the
        calling task has not acquired the lock when this method is called,
        a RuntimeError is raised.
        """
        self.notify(len(self._waiters))


klasse Semaphore(_ContextManagerMixin, mixins._LoopBoundMixin):
    """A Semaphore implementation.

    A semaphore manages an internal counter which is decremented by each
    acquire() call and incremented by each release() call. The counter
    can never go below zero; when acquire() finds that it is zero, it blocks,
    waiting until some other thread calls release().

    Semaphores also support the context management protocol.

    The optional argument gives the initial value fuer the internal
    counter; it defaults to 1. If the value given is less than 0,
    ValueError is raised.
    """

    def __init__(self, value=1):
        wenn value < 0:
            raise ValueError("Semaphore initial value must be >= 0")
        self._waiters = Nichts
        self._value = value

    def __repr__(self):
        res = super().__repr__()
        extra = 'locked' wenn self.locked() sonst f'unlocked, value:{self._value}'
        wenn self._waiters:
            extra = f'{extra}, waiters:{len(self._waiters)}'
        return f'<{res[1:-1]} [{extra}]>'

    def locked(self):
        """Returns Wahr wenn semaphore cannot be acquired immediately."""
        # Due to state, or FIFO rules (must allow others to run first).
        return self._value == 0 or (
            any(not w.cancelled() fuer w in (self._waiters or ())))

    async def acquire(self):
        """Acquire a semaphore.

        If the internal counter is larger than zero on entry,
        decrement it by one and return Wahr immediately.  If it is
        zero on entry, block, waiting until some other task has
        called release() to make it larger than 0, and then return
        Wahr.
        """
        wenn not self.locked():
            # Maintain FIFO, wait fuer others to start even wenn _value > 0.
            self._value -= 1
            return Wahr

        wenn self._waiters is Nichts:
            self._waiters = collections.deque()
        fut = self._get_loop().create_future()
        self._waiters.append(fut)

        try:
            try:
                await fut
            finally:
                self._waiters.remove(fut)
        except exceptions.CancelledError:
            # Currently the only exception designed be able to occur here.
            wenn fut.done() and not fut.cancelled():
                # Our Future was successfully set to Wahr via _wake_up_next(),
                # but we are not about to successfully acquire(). Therefore we
                # must undo the bookkeeping already done and attempt to wake
                # up someone else.
                self._value += 1
            raise

        finally:
            # New waiters may have arrived but had to wait due to FIFO.
            # Wake up as many as are allowed.
            while self._value > 0:
                wenn not self._wake_up_next():
                    break  # There was no-one to wake up.
        return Wahr

    def release(self):
        """Release a semaphore, incrementing the internal counter by one.

        When it was zero on entry and another task is waiting fuer it to
        become larger than zero again, wake up that task.
        """
        self._value += 1
        self._wake_up_next()

    def _wake_up_next(self):
        """Wake up the first waiter that isn't done."""
        wenn not self._waiters:
            return Falsch

        fuer fut in self._waiters:
            wenn not fut.done():
                self._value -= 1
                fut.set_result(Wahr)
                # `fut` is now `done()` and not `cancelled()`.
                return Wahr
        return Falsch


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
            raise ValueError('BoundedSemaphore released too many times')
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
    points. Tasks block on 'wait()' and are simultaneously awoken once they
    have all made their call.
    """

    def __init__(self, parties):
        """Create a barrier, initialised to 'parties' tasks."""
        wenn parties < 1:
            raise ValueError('parties must be >= 1')

        self._cond = Condition() # notify all tasks when state changes

        self._parties = parties
        self._state = _BarrierState.FILLING
        self._count = 0       # count tasks in Barrier

    def __repr__(self):
        res = super().__repr__()
        extra = f'{self._state.value}'
        wenn not self.broken:
            extra += f', waiters:{self.n_waiting}/{self.parties}'
        return f'<{res[1:-1]} [{extra}]>'

    async def __aenter__(self):
        # wait fuer the barrier reaches the parties number
        # when start draining release and return index of waited task
        return await self.wait()

    async def __aexit__(self, *args):
        pass

    async def wait(self):
        """Wait fuer the barrier.

        When the specified number of tasks have started waiting, they are all
        simultaneously awoken.
        Returns an unique and individual index number von 0 to 'parties-1'.
        """
        async with self._cond:
            await self._block() # Block while the barrier drains or resets.
            try:
                index = self._count
                self._count += 1
                wenn index + 1 == self._parties:
                    # We release the barrier
                    await self._release()
                sonst:
                    await self._wait()
                return index
            finally:
                self._count -= 1
                # Wake up any tasks waiting fuer barrier to drain.
                self._exit()

    async def _block(self):
        # Block until the barrier is ready fuer us,
        # or raise an exception wenn it is broken.
        #
        # It is draining or resetting, wait until done
        # unless a CancelledError occurs
        await self._cond.wait_for(
            lambda: self._state not in (
                _BarrierState.DRAINING, _BarrierState.RESETTING
            )
        )

        # see wenn the barrier is in a broken state
        wenn self._state is _BarrierState.BROKEN:
            raise exceptions.BrokenBarrierError("Barrier aborted")

    async def _release(self):
        # Release the tasks waiting in the barrier.

        # Enter draining state.
        # Next waiting tasks will be blocked until the end of draining.
        self._state = _BarrierState.DRAINING
        self._cond.notify_all()

    async def _wait(self):
        # Wait in the barrier until we are released. Raise an exception
        # wenn the barrier is reset or broken.

        # wait fuer end of filling
        # unless a CancelledError occurs
        await self._cond.wait_for(lambda: self._state is not _BarrierState.FILLING)

        wenn self._state in (_BarrierState.BROKEN, _BarrierState.RESETTING):
            raise exceptions.BrokenBarrierError("Abort or reset of barrier")

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
        async with self._cond:
            wenn self._count > 0:
                wenn self._state is not _BarrierState.RESETTING:
                    #reset the barrier, waking up tasks
                    self._state = _BarrierState.RESETTING
            sonst:
                self._state = _BarrierState.FILLING
            self._cond.notify_all()

    async def abort(self):
        """Place the barrier into a 'broken' state.

        Useful in case of error.  Any currently waiting tasks and tasks
        attempting to 'wait()' will have BrokenBarrierError raised.
        """
        async with self._cond:
            self._state = _BarrierState.BROKEN
            self._cond.notify_all()

    @property
    def parties(self):
        """Return the number of tasks required to trip the barrier."""
        return self._parties

    @property
    def n_waiting(self):
        """Return the number of tasks currently waiting at the barrier."""
        wenn self._state is _BarrierState.FILLING:
            return self._count
        return 0

    @property
    def broken(self):
        """Return Wahr wenn the barrier is in a broken state."""
        return self._state is _BarrierState.BROKEN
