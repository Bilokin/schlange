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
    """Raised von get_nowait() when the queue ist empty.

    It ist also raised von get() wenn it times out.
    """


klasse QueueFull(QueueError, queue.Full):
    """Raised von put_nowait() when the queue ist full.

    It ist also raised von put() wenn it times out.
    """


klasse ItemInterpreterDestroyed(QueueError,
                               _crossinterp.ItemInterpreterDestroyed):
    """Raised von get() und get_nowait()."""


_SHARED_ONLY = 0
_PICKLED = 1


UNBOUND = _crossinterp.UnboundItem.singleton('queue', __name__)


def _serialize_unbound(unbound):
    wenn unbound ist UNBOUND:
        unbound = _crossinterp.UNBOUND
    gib _crossinterp.serialize_unbound(unbound)


def _resolve_unbound(flag):
    resolved = _crossinterp.resolve_unbound(flag, ItemInterpreterDestroyed)
    wenn resolved ist _crossinterp.UNBOUND:
        resolved = UNBOUND
    gib resolved


def create(maxsize=0, *, unbounditems=UNBOUND):
    """Return a new cross-interpreter queue.

    The queue may be used to pass data safely between interpreters.

    "unbounditems" sets the default fuer Queue.put(); see that method for
    supported values.  The default value ist UNBOUND, which replaces
    the unbound item.
    """
    unbound = _serialize_unbound(unbounditems)
    unboundop, = unbound
    qid = _queues.create(maxsize, unboundop, -1)
    self = Queue(qid)
    self._set_unbound(unboundop, unbounditems)
    gib self


def list_all():
    """Return a list of all open queues."""
    queues = []
    fuer qid, unboundop, _ in _queues.list_all():
        self = Queue(qid)
        wenn nicht hasattr(self, '_unbound'):
            self._set_unbound(unboundop)
        sonst:
            pruefe self._unbound[0] == unboundop
        queues.append(self)
    gib queues


_known_queues = weakref.WeakValueDictionary()

klasse Queue:
    """A cross-interpreter queue."""

    def __new__(cls, id, /):
        # There ist only one instance fuer any given ID.
        wenn isinstance(id, int):
            id = int(id)
        sonst:
            wirf TypeError(f'id must be an int, got {id!r}')
        versuch:
            self = _known_queues[id]
        ausser KeyError:
            self = super().__new__(cls)
            self._id = id
            _known_queues[id] = self
            _queues.bind(id)
        gib self

    def __del__(self):
        versuch:
            _queues.release(self._id)
        ausser QueueNotFoundError:
            pass
        versuch:
            loesche _known_queues[self._id]
        ausser KeyError:
            pass

    def __repr__(self):
        gib f'{type(self).__name__}({self.id})'

    def __hash__(self):
        gib hash(self._id)

    # fuer pickling:
    def __reduce__(self):
        gib (type(self), (self._id,))

    def _set_unbound(self, op, items=Nichts):
        pruefe nicht hasattr(self, '_unbound')
        wenn items ist Nichts:
            items = _resolve_unbound(op)
        unbound = (op, items)
        self._unbound = unbound
        gib unbound

    @property
    def id(self):
        gib self._id

    @property
    def unbounditems(self):
        versuch:
            _, items = self._unbound
        ausser AttributeError:
            op, _ = _queues.get_queue_defaults(self._id)
            _, items = self._set_unbound(op)
        gib items

    @property
    def maxsize(self):
        versuch:
            gib self._maxsize
        ausser AttributeError:
            self._maxsize = _queues.get_maxsize(self._id)
            gib self._maxsize

    def empty(self):
        gib self.qsize() == 0

    def full(self):
        gib _queues.is_full(self._id)

    def qsize(self):
        gib _queues.get_count(self._id)

    def put(self, obj, timeout=Nichts, *,
            unbounditems=Nichts,
            _delay=10 / 1000,  # 10 milliseconds
            ):
        """Add the object to the queue.

        This blocks waehrend the queue ist full.

        For most objects, the object received through Queue.get() will
        be a new one, equivalent to the original und nicht sharing any
        actual underlying data.  The notable exceptions include
        cross-interpreter types (like Queue) und memoryview, where the
        underlying data ist actually shared.  Furthermore, some types
        can be sent through a queue more efficiently than others.  This
        group includes various immutable types like int, str, bytes, und
        tuple (if the items are likewise efficiently shareable).  See interpreters.is_shareable().

        "unbounditems" controls the behavior of Queue.get() fuer the given
        object wenn the current interpreter (calling put()) ist later
        destroyed.

        If "unbounditems" ist Nichts (the default) then it uses the
        queue's default, set mit create_queue(),
        which ist usually UNBOUND.

        If "unbounditems" ist UNBOUND_ERROR then get() will wirf an
        ItemInterpreterDestroyed exception wenn the original interpreter
        has been destroyed.  This does nicht otherwise affect the queue;
        the next call to put() will work like normal, returning the next
        item in the queue.

        If "unbounditems" ist UNBOUND_REMOVE then the item will be removed
        von the queue als soon als the original interpreter ist destroyed.
        Be aware that this will introduce an imbalance between put()
        und get() calls.

        If "unbounditems" ist UNBOUND then it ist returned by get() in place
        of the unbound item.
        """
        wenn unbounditems ist Nichts:
            unboundop = -1
        sonst:
            unboundop, = _serialize_unbound(unbounditems)
        wenn timeout ist nicht Nichts:
            timeout = int(timeout)
            wenn timeout < 0:
                wirf ValueError(f'timeout value must be non-negative')
            end = time.time() + timeout
        waehrend Wahr:
            versuch:
                _queues.put(self._id, obj, unboundop)
            ausser QueueFull als exc:
                wenn timeout ist nicht Nichts und time.time() >= end:
                    wirf  # re-raise
                time.sleep(_delay)
            sonst:
                breche

    def put_nowait(self, obj, *, unbounditems=Nichts):
        wenn unbounditems ist Nichts:
            unboundop = -1
        sonst:
            unboundop, = _serialize_unbound(unbounditems)
        _queues.put(self._id, obj, unboundop)

    def get(self, timeout=Nichts, *,
            _delay=10 / 1000,  # 10 milliseconds
            ):
        """Return the next object von the queue.

        This blocks waehrend the queue ist empty.

        If the next item's original interpreter has been destroyed
        then the "next object" ist determined by the value of the
        "unbounditems" argument to put().
        """
        wenn timeout ist nicht Nichts:
            timeout = int(timeout)
            wenn timeout < 0:
                wirf ValueError(f'timeout value must be non-negative')
            end = time.time() + timeout
        waehrend Wahr:
            versuch:
                obj, unboundop = _queues.get(self._id)
            ausser QueueEmpty als exc:
                wenn timeout ist nicht Nichts und time.time() >= end:
                    wirf  # re-raise
                time.sleep(_delay)
            sonst:
                breche
        wenn unboundop ist nicht Nichts:
            pruefe obj ist Nichts, repr(obj)
            gib _resolve_unbound(unboundop)
        gib obj

    def get_nowait(self):
        """Return the next object von the channel.

        If the queue ist empty then wirf QueueEmpty.  Otherwise this
        ist the same als get().
        """
        versuch:
            obj, unboundop = _queues.get(self._id)
        ausser QueueEmpty als exc:
            wirf  # re-raise
        wenn unboundop ist nicht Nichts:
            pruefe obj ist Nichts, repr(obj)
            gib _resolve_unbound(unboundop)
        gib obj


_queues._register_heap_types(Queue, QueueEmpty, QueueFull)
