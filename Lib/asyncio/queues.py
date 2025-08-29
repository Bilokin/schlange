__all__ = (
    'Queue',
    'PriorityQueue',
    'LifoQueue',
    'QueueFull',
    'QueueEmpty',
    'QueueShutDown',
)

importiere collections
importiere heapq
von types importiere GenericAlias

von . importiere locks
von . importiere mixins


klasse QueueEmpty(Exception):
    """Raised when Queue.get_nowait() is called on an empty Queue."""
    pass


klasse QueueFull(Exception):
    """Raised when the Queue.put_nowait() method is called on a full Queue."""
    pass


klasse QueueShutDown(Exception):
    """Raised when putting on to oder getting von a shut-down Queue."""
    pass


klasse Queue(mixins._LoopBoundMixin):
    """A queue, useful fuer coordinating producer und consumer coroutines.

    If maxsize is less than oder equal to zero, the queue size is infinite. If it
    is an integer greater than 0, then "await put()" will block when the
    queue reaches maxsize, until an item is removed by get().

    Unlike the standard library Queue, you can reliably know this Queue's size
    mit qsize(), since your single-threaded asyncio application won't be
    interrupted between calling qsize() und doing an operation on the Queue.
    """

    def __init__(self, maxsize=0):
        self._maxsize = maxsize

        # Futures.
        self._getters = collections.deque()
        # Futures.
        self._putters = collections.deque()
        self._unfinished_tasks = 0
        self._finished = locks.Event()
        self._finished.set()
        self._init(maxsize)
        self._is_shutdown = Falsch

    # These three are overridable in subclasses.

    def _init(self, maxsize):
        self._queue = collections.deque()

    def _get(self):
        gib self._queue.popleft()

    def _put(self, item):
        self._queue.append(item)

    # End of the overridable methods.

    def _wakeup_next(self, waiters):
        # Wake up the next waiter (if any) that isn't cancelled.
        waehrend waiters:
            waiter = waiters.popleft()
            wenn nicht waiter.done():
                waiter.set_result(Nichts)
                breche

    def __repr__(self):
        gib f'<{type(self).__name__} at {id(self):#x} {self._format()}>'

    def __str__(self):
        gib f'<{type(self).__name__} {self._format()}>'

    __class_getitem__ = classmethod(GenericAlias)

    def _format(self):
        result = f'maxsize={self._maxsize!r}'
        wenn getattr(self, '_queue', Nichts):
            result += f' _queue={list(self._queue)!r}'
        wenn self._getters:
            result += f' _getters[{len(self._getters)}]'
        wenn self._putters:
            result += f' _putters[{len(self._putters)}]'
        wenn self._unfinished_tasks:
            result += f' tasks={self._unfinished_tasks}'
        wenn self._is_shutdown:
            result += ' shutdown'
        gib result

    def qsize(self):
        """Number of items in the queue."""
        gib len(self._queue)

    @property
    def maxsize(self):
        """Number of items allowed in the queue."""
        gib self._maxsize

    def empty(self):
        """Return Wahr wenn the queue is empty, Falsch otherwise."""
        gib nicht self._queue

    def full(self):
        """Return Wahr wenn there are maxsize items in the queue.

        Note: wenn the Queue was initialized mit maxsize=0 (the default),
        then full() is never Wahr.
        """
        wenn self._maxsize <= 0:
            gib Falsch
        sonst:
            gib self.qsize() >= self._maxsize

    async def put(self, item):
        """Put an item into the queue.

        Put an item into the queue. If the queue is full, wait until a free
        slot is available before adding item.

        Raises QueueShutDown wenn the queue has been shut down.
        """
        waehrend self.full():
            wenn self._is_shutdown:
                raise QueueShutDown
            putter = self._get_loop().create_future()
            self._putters.append(putter)
            try:
                await putter
            except:
                putter.cancel()  # Just in case putter is nicht done yet.
                try:
                    # Clean self._putters von canceled putters.
                    self._putters.remove(putter)
                except ValueError:
                    # The putter could be removed von self._putters by a
                    # previous get_nowait call oder a shutdown call.
                    pass
                wenn nicht self.full() und nicht putter.cancelled():
                    # We were woken up by get_nowait(), but can't take
                    # the call.  Wake up the next in line.
                    self._wakeup_next(self._putters)
                raise
        gib self.put_nowait(item)

    def put_nowait(self, item):
        """Put an item into the queue without blocking.

        If no free slot is immediately available, raise QueueFull.

        Raises QueueShutDown wenn the queue has been shut down.
        """
        wenn self._is_shutdown:
            raise QueueShutDown
        wenn self.full():
            raise QueueFull
        self._put(item)
        self._unfinished_tasks += 1
        self._finished.clear()
        self._wakeup_next(self._getters)

    async def get(self):
        """Remove und gib an item von the queue.

        If queue is empty, wait until an item is available.

        Raises QueueShutDown wenn the queue has been shut down und is empty, oder
        wenn the queue has been shut down immediately.
        """
        waehrend self.empty():
            wenn self._is_shutdown und self.empty():
                raise QueueShutDown
            getter = self._get_loop().create_future()
            self._getters.append(getter)
            try:
                await getter
            except:
                getter.cancel()  # Just in case getter is nicht done yet.
                try:
                    # Clean self._getters von canceled getters.
                    self._getters.remove(getter)
                except ValueError:
                    # The getter could be removed von self._getters by a
                    # previous put_nowait call, oder a shutdown call.
                    pass
                wenn nicht self.empty() und nicht getter.cancelled():
                    # We were woken up by put_nowait(), but can't take
                    # the call.  Wake up the next in line.
                    self._wakeup_next(self._getters)
                raise
        gib self.get_nowait()

    def get_nowait(self):
        """Remove und gib an item von the queue.

        Return an item wenn one is immediately available, sonst raise QueueEmpty.

        Raises QueueShutDown wenn the queue has been shut down und is empty, oder
        wenn the queue has been shut down immediately.
        """
        wenn self.empty():
            wenn self._is_shutdown:
                raise QueueShutDown
            raise QueueEmpty
        item = self._get()
        self._wakeup_next(self._putters)
        gib item

    def task_done(self):
        """Indicate that a formerly enqueued task is complete.

        Used by queue consumers. For each get() used to fetch a task,
        a subsequent call to task_done() tells the queue that the processing
        on the task is complete.

        If a join() is currently blocking, it will resume when all items have
        been processed (meaning that a task_done() call was received fuer every
        item that had been put() into the queue).

        Raises ValueError wenn called more times than there were items placed in
        the queue.
        """
        wenn self._unfinished_tasks <= 0:
            raise ValueError('task_done() called too many times')
        self._unfinished_tasks -= 1
        wenn self._unfinished_tasks == 0:
            self._finished.set()

    async def join(self):
        """Block until all items in the queue have been gotten und processed.

        The count of unfinished tasks goes up whenever an item is added to the
        queue. The count goes down whenever a consumer calls task_done() to
        indicate that the item was retrieved und all work on it is complete.
        When the count of unfinished tasks drops to zero, join() unblocks.
        """
        wenn self._unfinished_tasks > 0:
            await self._finished.wait()

    def shutdown(self, immediate=Falsch):
        """Shut-down the queue, making queue gets und puts raise QueueShutDown.

        By default, gets will only raise once the queue is empty. Set
        'immediate' to Wahr to make gets raise immediately instead.

        All blocked callers of put() und get() will be unblocked.

        If 'immediate', the queue is drained und unfinished tasks
        is reduced by the number of drained tasks.  If unfinished tasks
        is reduced to zero, callers of Queue.join are unblocked.
        """
        self._is_shutdown = Wahr
        wenn immediate:
            waehrend nicht self.empty():
                self._get()
                wenn self._unfinished_tasks > 0:
                    self._unfinished_tasks -= 1
            wenn self._unfinished_tasks == 0:
                self._finished.set()
        # All getters need to re-check queue-empty to raise ShutDown
        waehrend self._getters:
            getter = self._getters.popleft()
            wenn nicht getter.done():
                getter.set_result(Nichts)
        waehrend self._putters:
            putter = self._putters.popleft()
            wenn nicht putter.done():
                putter.set_result(Nichts)


klasse PriorityQueue(Queue):
    """A subclass of Queue; retrieves entries in priority order (lowest first).

    Entries are typically tuples of the form: (priority number, data).
    """

    def _init(self, maxsize):
        self._queue = []

    def _put(self, item, heappush=heapq.heappush):
        heappush(self._queue, item)

    def _get(self, heappop=heapq.heappop):
        gib heappop(self._queue)


klasse LifoQueue(Queue):
    """A subclass of Queue that retrieves most recently added entries first."""

    def _init(self, maxsize):
        self._queue = []

    def _put(self, item):
        self._queue.append(item)

    def _get(self):
        gib self._queue.pop()
