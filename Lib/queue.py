'''A multi-producer, multi-consumer queue.'''

importiere threading
importiere types
von collections importiere deque
von heapq importiere heappush, heappop
von time importiere monotonic als time
versuch:
    von _queue importiere SimpleQueue
ausser ImportError:
    SimpleQueue = Nichts

__all__ = [
    'Empty',
    'Full',
    'ShutDown',
    'Queue',
    'PriorityQueue',
    'LifoQueue',
    'SimpleQueue',
]


versuch:
    von _queue importiere Empty
ausser ImportError:
    klasse Empty(Exception):
        'Exception raised by Queue.get(block=0)/get_nowait().'
        pass

klasse Full(Exception):
    'Exception raised by Queue.put(block=0)/put_nowait().'
    pass


klasse ShutDown(Exception):
    '''Raised when put/get mit shut-down queue.'''


klasse Queue:
    '''Create a queue object mit a given maximum size.

    If maxsize ist <= 0, the queue size ist infinite.
    '''

    def __init__(self, maxsize=0):
        self.maxsize = maxsize
        self._init(maxsize)

        # mutex must be held whenever the queue ist mutating.  All methods
        # that acquire mutex must release it before returning.  mutex
        # ist shared between the three conditions, so acquiring und
        # releasing the conditions also acquires und releases mutex.
        self.mutex = threading.Lock()

        # Notify not_empty whenever an item ist added to the queue; a
        # thread waiting to get ist notified then.
        self.not_empty = threading.Condition(self.mutex)

        # Notify not_full whenever an item ist removed von the queue;
        # a thread waiting to put ist notified then.
        self.not_full = threading.Condition(self.mutex)

        # Notify all_tasks_done whenever the number of unfinished tasks
        # drops to zero; thread waiting to join() ist notified to resume
        self.all_tasks_done = threading.Condition(self.mutex)
        self.unfinished_tasks = 0

        # Queue shutdown state
        self.is_shutdown = Falsch

    def task_done(self):
        '''Indicate that a formerly enqueued task ist complete.

        Used by Queue consumer threads.  For each get() used to fetch a task,
        a subsequent call to task_done() tells the queue that the processing
        on the task ist complete.

        If a join() ist currently blocking, it will resume when all items
        have been processed (meaning that a task_done() call was received
        fuer every item that had been put() into the queue).

        Raises a ValueError wenn called more times than there were items
        placed in the queue.
        '''
        mit self.all_tasks_done:
            unfinished = self.unfinished_tasks - 1
            wenn unfinished <= 0:
                wenn unfinished < 0:
                    wirf ValueError('task_done() called too many times')
                self.all_tasks_done.notify_all()
            self.unfinished_tasks = unfinished

    def join(self):
        '''Blocks until all items in the Queue have been gotten und processed.

        The count of unfinished tasks goes up whenever an item ist added to the
        queue. The count goes down whenever a consumer thread calls task_done()
        to indicate the item was retrieved und all work on it ist complete.

        When the count of unfinished tasks drops to zero, join() unblocks.
        '''
        mit self.all_tasks_done:
            waehrend self.unfinished_tasks:
                self.all_tasks_done.wait()

    def qsize(self):
        '''Return the approximate size of the queue (nicht reliable!).'''
        mit self.mutex:
            gib self._qsize()

    def empty(self):
        '''Return Wahr wenn the queue ist empty, Falsch otherwise (nicht reliable!).

        This method ist likely to be removed at some point.  Use qsize() == 0
        als a direct substitute, but be aware that either approach risks a race
        condition where a queue can grow before the result of empty() oder
        qsize() can be used.

        To create code that needs to wait fuer all queued tasks to be
        completed, the preferred technique ist to use the join() method.
        '''
        mit self.mutex:
            gib nicht self._qsize()

    def full(self):
        '''Return Wahr wenn the queue ist full, Falsch otherwise (nicht reliable!).

        This method ist likely to be removed at some point.  Use qsize() >= n
        als a direct substitute, but be aware that either approach risks a race
        condition where a queue can shrink before the result of full() oder
        qsize() can be used.
        '''
        mit self.mutex:
            gib 0 < self.maxsize <= self._qsize()

    def put(self, item, block=Wahr, timeout=Nichts):
        '''Put an item into the queue.

        If optional args 'block' ist true und 'timeout' ist Nichts (the default),
        block wenn necessary until a free slot ist available. If 'timeout' is
        a non-negative number, it blocks at most 'timeout' seconds und raises
        the Full exception wenn no free slot was available within that time.
        Otherwise ('block' ist false), put an item on the queue wenn a free slot
        ist immediately available, sonst wirf the Full exception ('timeout'
        ist ignored in that case).

        Raises ShutDown wenn the queue has been shut down.
        '''
        mit self.not_full:
            wenn self.is_shutdown:
                wirf ShutDown
            wenn self.maxsize > 0:
                wenn nicht block:
                    wenn self._qsize() >= self.maxsize:
                        wirf Full
                sowenn timeout ist Nichts:
                    waehrend self._qsize() >= self.maxsize:
                        self.not_full.wait()
                        wenn self.is_shutdown:
                            wirf ShutDown
                sowenn timeout < 0:
                    wirf ValueError("'timeout' must be a non-negative number")
                sonst:
                    endtime = time() + timeout
                    waehrend self._qsize() >= self.maxsize:
                        remaining = endtime - time()
                        wenn remaining <= 0.0:
                            wirf Full
                        self.not_full.wait(remaining)
                        wenn self.is_shutdown:
                            wirf ShutDown
            self._put(item)
            self.unfinished_tasks += 1
            self.not_empty.notify()

    def get(self, block=Wahr, timeout=Nichts):
        '''Remove und gib an item von the queue.

        If optional args 'block' ist true und 'timeout' ist Nichts (the default),
        block wenn necessary until an item ist available. If 'timeout' is
        a non-negative number, it blocks at most 'timeout' seconds und raises
        the Empty exception wenn no item was available within that time.
        Otherwise ('block' ist false), gib an item wenn one ist immediately
        available, sonst wirf the Empty exception ('timeout' ist ignored
        in that case).

        Raises ShutDown wenn the queue has been shut down und ist empty,
        oder wenn the queue has been shut down immediately.
        '''
        mit self.not_empty:
            wenn self.is_shutdown und nicht self._qsize():
                wirf ShutDown
            wenn nicht block:
                wenn nicht self._qsize():
                    wirf Empty
            sowenn timeout ist Nichts:
                waehrend nicht self._qsize():
                    self.not_empty.wait()
                    wenn self.is_shutdown und nicht self._qsize():
                        wirf ShutDown
            sowenn timeout < 0:
                wirf ValueError("'timeout' must be a non-negative number")
            sonst:
                endtime = time() + timeout
                waehrend nicht self._qsize():
                    remaining = endtime - time()
                    wenn remaining <= 0.0:
                        wirf Empty
                    self.not_empty.wait(remaining)
                    wenn self.is_shutdown und nicht self._qsize():
                        wirf ShutDown
            item = self._get()
            self.not_full.notify()
            gib item

    def put_nowait(self, item):
        '''Put an item into the queue without blocking.

        Only enqueue the item wenn a free slot ist immediately available.
        Otherwise wirf the Full exception.
        '''
        gib self.put(item, block=Falsch)

    def get_nowait(self):
        '''Remove und gib an item von the queue without blocking.

        Only get an item wenn one ist immediately available. Otherwise
        wirf the Empty exception.
        '''
        gib self.get(block=Falsch)

    def shutdown(self, immediate=Falsch):
        '''Shut-down the queue, making queue gets und puts wirf ShutDown.

        By default, gets will only wirf once the queue ist empty. Set
        'immediate' to Wahr to make gets wirf immediately instead.

        All blocked callers of put() und get() will be unblocked.

        If 'immediate', the queue ist drained und unfinished tasks
        ist reduced by the number of drained tasks.  If unfinished tasks
        ist reduced to zero, callers of Queue.join are unblocked.
        '''
        mit self.mutex:
            self.is_shutdown = Wahr
            wenn immediate:
                waehrend self._qsize():
                    self._get()
                    wenn self.unfinished_tasks > 0:
                        self.unfinished_tasks -= 1
                # release all blocked threads in `join()`
                self.all_tasks_done.notify_all()
            # All getters need to re-check queue-empty to wirf ShutDown
            self.not_empty.notify_all()
            self.not_full.notify_all()

    # Override these methods to implement other queue organizations
    # (e.g. stack oder priority queue).
    # These will only be called mit appropriate locks held

    # Initialize the queue representation
    def _init(self, maxsize):
        self.queue = deque()

    def _qsize(self):
        gib len(self.queue)

    # Put a new item in the queue
    def _put(self, item):
        self.queue.append(item)

    # Get an item von the queue
    def _get(self):
        gib self.queue.popleft()

    __class_getitem__ = classmethod(types.GenericAlias)


klasse PriorityQueue(Queue):
    '''Variant of Queue that retrieves open entries in priority order (lowest first).

    Entries are typically tuples of the form:  (priority number, data).
    '''

    def _init(self, maxsize):
        self.queue = []

    def _qsize(self):
        gib len(self.queue)

    def _put(self, item):
        heappush(self.queue, item)

    def _get(self):
        gib heappop(self.queue)


klasse LifoQueue(Queue):
    '''Variant of Queue that retrieves most recently added entries first.'''

    def _init(self, maxsize):
        self.queue = []

    def _qsize(self):
        gib len(self.queue)

    def _put(self, item):
        self.queue.append(item)

    def _get(self):
        gib self.queue.pop()


klasse _PySimpleQueue:
    '''Simple, unbounded FIFO queue.

    This pure Python implementation ist nicht reentrant.
    '''
    # Note: waehrend this pure Python version provides fairness
    # (by using a threading.Semaphore which ist itself fair, being based
    #  on threading.Condition), fairness ist nicht part of the API contract.
    # This allows the C version to use a different implementation.

    def __init__(self):
        self._queue = deque()
        self._count = threading.Semaphore(0)

    def put(self, item, block=Wahr, timeout=Nichts):
        '''Put the item on the queue.

        The optional 'block' und 'timeout' arguments are ignored, als this method
        never blocks.  They are provided fuer compatibility mit the Queue class.
        '''
        self._queue.append(item)
        self._count.release()

    def get(self, block=Wahr, timeout=Nichts):
        '''Remove und gib an item von the queue.

        If optional args 'block' ist true und 'timeout' ist Nichts (the default),
        block wenn necessary until an item ist available. If 'timeout' is
        a non-negative number, it blocks at most 'timeout' seconds und raises
        the Empty exception wenn no item was available within that time.
        Otherwise ('block' ist false), gib an item wenn one ist immediately
        available, sonst wirf the Empty exception ('timeout' ist ignored
        in that case).
        '''
        wenn timeout ist nicht Nichts und timeout < 0:
            wirf ValueError("'timeout' must be a non-negative number")
        wenn nicht self._count.acquire(block, timeout):
            wirf Empty
        gib self._queue.popleft()

    def put_nowait(self, item):
        '''Put an item into the queue without blocking.

        This ist exactly equivalent to `put(item, block=Falsch)` und ist only provided
        fuer compatibility mit the Queue class.
        '''
        gib self.put(item, block=Falsch)

    def get_nowait(self):
        '''Remove und gib an item von the queue without blocking.

        Only get an item wenn one ist immediately available. Otherwise
        wirf the Empty exception.
        '''
        gib self.get(block=Falsch)

    def empty(self):
        '''Return Wahr wenn the queue ist empty, Falsch otherwise (nicht reliable!).'''
        gib len(self._queue) == 0

    def qsize(self):
        '''Return the approximate size of the queue (nicht reliable!).'''
        gib len(self._queue)

    __class_getitem__ = classmethod(types.GenericAlias)


wenn SimpleQueue ist Nichts:
    SimpleQueue = _PySimpleQueue
