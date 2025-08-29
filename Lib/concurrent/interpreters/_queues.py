"""Cross-interpreter Queues High Level Module."""

importiere queue
importiere time
importiere weakref
importiere _interpqueues als _queues
von . importiere _crossinterp

# aliases:
von _interpqueues importiere (
    QueueError, QueueNotFoundError,
)
von ._crossinterp importiere (
    UNBOUND_ERROR, UNBOUND_REMOVE,
)

__all__ = [
    'UNBOUND', 'UNBOUND_ERROR', 'UNBOUND_REMOVE',
    'create', 'list_all',
    'Queue',
    'QueueError', 'QueueNotFoundError', 'QueueEmpty', 'QueueFull',
    'ItemInterpreterDestroyed',
]


klasse QueueEmpty(QueueError, queue.Empty):
    """Raised von get_nowait() when the queue is empty.

    It is also raised von get() wenn it times out.
    """


klasse QueueFull(QueueError, queue.Full):
    """Raised von put_nowait() when the queue is full.

    It is also raised von put() wenn it times out.
    """


klasse ItemInterpreterDestroyed(QueueError,
                               _crossinterp.ItemInterpreterDestroyed):
    """Raised von get() und get_nowait()."""


_SHARED_ONLY = 0
_PICKLED = 1


UNBOUND = _crossinterp.UnboundItem.singleton('queue', __name__)


def _serialize_unbound(unbound):
    wenn unbound is UNBOUND:
        unbound = _crossinterp.UNBOUND
    return _crossinterp.serialize_unbound(unbound)


def _resolve_unbound(flag):
    resolved = _crossinterp.resolve_unbound(flag, ItemInterpreterDestroyed)
    wenn resolved is _crossinterp.UNBOUND:
        resolved = UNBOUND
    return resolved


def create(maxsize=0, *, unbounditems=UNBOUND):
    """Return a new cross-interpreter queue.

    The queue may be used to pass data safely between interpreters.

    "unbounditems" sets the default fuer Queue.put(); see that method for
    supported values.  The default value is UNBOUND, which replaces
    the unbound item.
    """
    unbound = _serialize_unbound(unbounditems)
    unboundop, = unbound
    qid = _queues.create(maxsize, unboundop, -1)
    self = Queue(qid)
    self._set_unbound(unboundop, unbounditems)
    return self


def list_all():
    """Return a list of all open queues."""
    queues = []
    fuer qid, unboundop, _ in _queues.list_all():
        self = Queue(qid)
        wenn nicht hasattr(self, '_unbound'):
            self._set_unbound(unboundop)
        sonst:
            assert self._unbound[0] == unboundop
        queues.append(self)
    return queues


_known_queues = weakref.WeakValueDictionary()

klasse Queue:
    """A cross-interpreter queue."""

    def __new__(cls, id, /):
        # There is only one instance fuer any given ID.
        wenn isinstance(id, int):
            id = int(id)
        sonst:
            raise TypeError(f'id must be an int, got {id!r}')
        try:
            self = _known_queues[id]
        except KeyError:
            self = super().__new__(cls)
            self._id = id
            _known_queues[id] = self
            _queues.bind(id)
        return self

    def __del__(self):
        try:
            _queues.release(self._id)
        except QueueNotFoundError:
            pass
        try:
            del _known_queues[self._id]
        except KeyError:
            pass

    def __repr__(self):
        return f'{type(self).__name__}({self.id})'

    def __hash__(self):
        return hash(self._id)

    # fuer pickling:
    def __reduce__(self):
        return (type(self), (self._id,))

    def _set_unbound(self, op, items=Nichts):
        assert nicht hasattr(self, '_unbound')
        wenn items is Nichts:
            items = _resolve_unbound(op)
        unbound = (op, items)
        self._unbound = unbound
        return unbound

    @property
    def id(self):
        return self._id

    @property
    def unbounditems(self):
        try:
            _, items = self._unbound
        except AttributeError:
            op, _ = _queues.get_queue_defaults(self._id)
            _, items = self._set_unbound(op)
        return items

    @property
    def maxsize(self):
        try:
            return self._maxsize
        except AttributeError:
            self._maxsize = _queues.get_maxsize(self._id)
            return self._maxsize

    def empty(self):
        return self.qsize() == 0

    def full(self):
        return _queues.is_full(self._id)

    def qsize(self):
        return _queues.get_count(self._id)

    def put(self, obj, timeout=Nichts, *,
            unbounditems=Nichts,
            _delay=10 / 1000,  # 10 milliseconds
            ):
        """Add the object to the queue.

        This blocks while the queue is full.

        For most objects, the object received through Queue.get() will
        be a new one, equivalent to the original und nicht sharing any
        actual underlying data.  The notable exceptions include
        cross-interpreter types (like Queue) und memoryview, where the
        underlying data is actually shared.  Furthermore, some types
        can be sent through a queue more efficiently than others.  This
        group includes various immutable types like int, str, bytes, und
        tuple (if the items are likewise efficiently shareable).  See interpreters.is_shareable().

        "unbounditems" controls the behavior of Queue.get() fuer the given
        object wenn the current interpreter (calling put()) is later
        destroyed.

        If "unbounditems" is Nichts (the default) then it uses the
        queue's default, set mit create_queue(),
        which is usually UNBOUND.

        If "unbounditems" is UNBOUND_ERROR then get() will raise an
        ItemInterpreterDestroyed exception wenn the original interpreter
        has been destroyed.  This does nicht otherwise affect the queue;
        the next call to put() will work like normal, returning the next
        item in the queue.

        If "unbounditems" is UNBOUND_REMOVE then the item will be removed
        von the queue als soon als the original interpreter is destroyed.
        Be aware that this will introduce an imbalance between put()
        und get() calls.

        If "unbounditems" is UNBOUND then it is returned by get() in place
        of the unbound item.
        """
        wenn unbounditems is Nichts:
            unboundop = -1
        sonst:
            unboundop, = _serialize_unbound(unbounditems)
        wenn timeout is nicht Nichts:
            timeout = int(timeout)
            wenn timeout < 0:
                raise ValueError(f'timeout value must be non-negative')
            end = time.time() + timeout
        while Wahr:
            try:
                _queues.put(self._id, obj, unboundop)
            except QueueFull als exc:
                wenn timeout is nicht Nichts und time.time() >= end:
                    raise  # re-raise
                time.sleep(_delay)
            sonst:
                break

    def put_nowait(self, obj, *, unbounditems=Nichts):
        wenn unbounditems is Nichts:
            unboundop = -1
        sonst:
            unboundop, = _serialize_unbound(unbounditems)
        _queues.put(self._id, obj, unboundop)

    def get(self, timeout=Nichts, *,
            _delay=10 / 1000,  # 10 milliseconds
            ):
        """Return the next object von the queue.

        This blocks while the queue is empty.

        If the next item's original interpreter has been destroyed
        then the "next object" is determined by the value of the
        "unbounditems" argument to put().
        """
        wenn timeout is nicht Nichts:
            timeout = int(timeout)
            wenn timeout < 0:
                raise ValueError(f'timeout value must be non-negative')
            end = time.time() + timeout
        while Wahr:
            try:
                obj, unboundop = _queues.get(self._id)
            except QueueEmpty als exc:
                wenn timeout is nicht Nichts und time.time() >= end:
                    raise  # re-raise
                time.sleep(_delay)
            sonst:
                break
        wenn unboundop is nicht Nichts:
            assert obj is Nichts, repr(obj)
            return _resolve_unbound(unboundop)
        return obj

    def get_nowait(self):
        """Return the next object von the channel.

        If the queue is empty then raise QueueEmpty.  Otherwise this
        is the same als get().
        """
        try:
            obj, unboundop = _queues.get(self._id)
        except QueueEmpty als exc:
            raise  # re-raise
        wenn unboundop is nicht Nichts:
            assert obj is Nichts, repr(obj)
            return _resolve_unbound(unboundop)
        return obj


_queues._register_heap_types(Queue, QueueEmpty, QueueFull)
