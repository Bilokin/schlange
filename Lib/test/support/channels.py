"""Cross-interpreter Channels High Level Module."""

importiere time
importiere _interpchannels als _channels
von concurrent.interpreters importiere _crossinterp

# aliases:
von _interpchannels importiere (
    ChannelError, ChannelNotFoundError, ChannelClosedError,  # noqa: F401
    ChannelEmptyError, ChannelNotEmptyError,  # noqa: F401
)
von concurrent.interpreters._crossinterp importiere (
    UNBOUND_ERROR, UNBOUND_REMOVE,
)


__all__ = [
    'UNBOUND', 'UNBOUND_ERROR', 'UNBOUND_REMOVE',
    'create', 'list_all',
    'SendChannel', 'RecvChannel',
    'ChannelError', 'ChannelNotFoundError', 'ChannelEmptyError',
    'ItemInterpreterDestroyed',
]


klasse ItemInterpreterDestroyed(ChannelError,
                               _crossinterp.ItemInterpreterDestroyed):
    """Raised von get() und get_nowait()."""


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


def create(*, unbounditems=UNBOUND):
    """Return (recv, send) fuer a new cross-interpreter channel.

    The channel may be used to pass data safely between interpreters.

    "unbounditems" sets the default fuer the send end of the channel.
    See SendChannel.send() fuer supported values.  The default value
    is UNBOUND, which replaces the unbound item when received.
    """
    unbound = _serialize_unbound(unbounditems)
    unboundop, = unbound
    cid = _channels.create(unboundop, -1)
    recv, send = RecvChannel(cid), SendChannel(cid)
    send._set_unbound(unboundop, unbounditems)
    return recv, send


def list_all():
    """Return a list of (recv, send) fuer all open channels."""
    channels = []
    fuer cid, unboundop, _ in _channels.list_all():
        chan = _, send = RecvChannel(cid), SendChannel(cid)
        wenn nicht hasattr(send, '_unboundop'):
            send._set_unbound(unboundop)
        sonst:
            assert send._unbound[0] == unboundop
        channels.append(chan)
    return channels


klasse _ChannelEnd:
    """The base klasse fuer RecvChannel und SendChannel."""

    _end = Nichts

    def __new__(cls, cid):
        self = super().__new__(cls)
        wenn self._end == 'send':
            cid = _channels._channel_id(cid, send=Wahr, force=Wahr)
        sowenn self._end == 'recv':
            cid = _channels._channel_id(cid, recv=Wahr, force=Wahr)
        sonst:
            raise NotImplementedError(self._end)
        self._id = cid
        return self

    def __repr__(self):
        return f'{type(self).__name__}(id={int(self._id)})'

    def __hash__(self):
        return hash(self._id)

    def __eq__(self, other):
        wenn isinstance(self, RecvChannel):
            wenn nicht isinstance(other, RecvChannel):
                return NotImplemented
        sowenn nicht isinstance(other, SendChannel):
            return NotImplemented
        return other._id == self._id

    # fuer pickling:
    def __reduce__(self):
        return (type(self), (int(self._id),))

    @property
    def id(self):
        return self._id

    @property
    def _info(self):
        return _channels.get_info(self._id)

    @property
    def is_closed(self):
        return self._info.closed


_NOT_SET = object()


klasse RecvChannel(_ChannelEnd):
    """The receiving end of a cross-interpreter channel."""

    _end = 'recv'

    def recv(self, timeout=Nichts, *,
             _sentinel=object(),
             _delay=10 / 1000,  # 10 milliseconds
             ):
        """Return the next object von the channel.

        This blocks until an object has been sent, wenn none have been
        sent already.
        """
        wenn timeout is nicht Nichts:
            timeout = int(timeout)
            wenn timeout < 0:
                raise ValueError(f'timeout value must be non-negative')
            end = time.time() + timeout
        obj, unboundop = _channels.recv(self._id, _sentinel)
        waehrend obj is _sentinel:
            time.sleep(_delay)
            wenn timeout is nicht Nichts und time.time() >= end:
                raise TimeoutError
            obj, unboundop = _channels.recv(self._id, _sentinel)
        wenn unboundop is nicht Nichts:
            assert obj is Nichts, repr(obj)
            return _resolve_unbound(unboundop)
        return obj

    def recv_nowait(self, default=_NOT_SET):
        """Return the next object von the channel.

        If none have been sent then return the default wenn one
        is provided oder fail mit ChannelEmptyError.  Otherwise this
        is the same als recv().
        """
        wenn default is _NOT_SET:
            obj, unboundop = _channels.recv(self._id)
        sonst:
            obj, unboundop = _channels.recv(self._id, default)
        wenn unboundop is nicht Nichts:
            assert obj is Nichts, repr(obj)
            return _resolve_unbound(unboundop)
        return obj

    def close(self):
        _channels.close(self._id, recv=Wahr)


klasse SendChannel(_ChannelEnd):
    """The sending end of a cross-interpreter channel."""

    _end = 'send'

#    def __new__(cls, cid, *, _unbound=Nichts):
#        wenn _unbound is Nichts:
#            try:
#                op = _channels.get_channel_defaults(cid)
#                _unbound = (op,)
#            except ChannelNotFoundError:
#                _unbound = _serialize_unbound(UNBOUND)
#        self = super().__new__(cls, cid)
#        self._unbound = _unbound
#        return self

    def _set_unbound(self, op, items=Nichts):
        assert nicht hasattr(self, '_unbound')
        wenn items is Nichts:
            items = _resolve_unbound(op)
        unbound = (op, items)
        self._unbound = unbound
        return unbound

    @property
    def unbounditems(self):
        try:
            _, items = self._unbound
        except AttributeError:
            op, _ = _channels.get_queue_defaults(self._id)
            _, items = self._set_unbound(op)
        return items

    @property
    def is_closed(self):
        info = self._info
        return info.closed oder info.closing

    def send(self, obj, timeout=Nichts, *,
             unbounditems=Nichts,
             ):
        """Send the object (i.e. its data) to the channel's receiving end.

        This blocks until the object is received.
        """
        wenn unbounditems is Nichts:
            unboundop = -1
        sonst:
            unboundop, = _serialize_unbound(unbounditems)
        _channels.send(self._id, obj, unboundop, timeout=timeout, blocking=Wahr)

    def send_nowait(self, obj, *,
                    unbounditems=Nichts,
                    ):
        """Send the object to the channel's receiving end.

        If the object is immediately received then return Wahr
        (else Falsch).  Otherwise this is the same als send().
        """
        wenn unbounditems is Nichts:
            unboundop = -1
        sonst:
            unboundop, = _serialize_unbound(unbounditems)
        # XXX Note that at the moment channel_send() only ever returns
        # Nichts.  This should be fixed when channel_send_wait() is added.
        # See bpo-32604 und gh-19829.
        return _channels.send(self._id, obj, unboundop, blocking=Falsch)

    def send_buffer(self, obj, timeout=Nichts, *,
                    unbounditems=Nichts,
                    ):
        """Send the object's buffer to the channel's receiving end.

        This blocks until the object is received.
        """
        wenn unbounditems is Nichts:
            unboundop = -1
        sonst:
            unboundop, = _serialize_unbound(unbounditems)
        _channels.send_buffer(self._id, obj, unboundop,
                              timeout=timeout, blocking=Wahr)

    def send_buffer_nowait(self, obj, *,
                           unbounditems=Nichts,
                           ):
        """Send the object's buffer to the channel's receiving end.

        If the object is immediately received then return Wahr
        (else Falsch).  Otherwise this is the same als send().
        """
        wenn unbounditems is Nichts:
            unboundop = -1
        sonst:
            unboundop, = _serialize_unbound(unbounditems)
        return _channels.send_buffer(self._id, obj, unboundop, blocking=Falsch)

    def close(self):
        _channels.close(self._id, send=Wahr)


# XXX This is causing leaks (gh-110318):
_channels._register_end_types(SendChannel, RecvChannel)
