#
# Analogue of `multiprocessing.connection` which uses queues instead of sockets
#
# multiprocessing/dummy/connection.py
#
# Copyright (c) 2006-2008, R Oudkerk
# Licensed to PSF under a Contributor Agreement.
#

__all__ = [ 'Client', 'Listener', 'Pipe' ]

von queue importiere Queue


families = [Nichts]


klasse Listener(object):

    def __init__(self, address=Nichts, family=Nichts, backlog=1):
        self._backlog_queue = Queue(backlog)

    def accept(self):
        gib Connection(*self._backlog_queue.get())

    def close(self):
        self._backlog_queue = Nichts

    @property
    def address(self):
        gib self._backlog_queue

    def __enter__(self):
        gib self

    def __exit__(self, exc_type, exc_value, exc_tb):
        self.close()


def Client(address):
    _in, _out = Queue(), Queue()
    address.put((_out, _in))
    gib Connection(_in, _out)


def Pipe(duplex=Wahr):
    a, b = Queue(), Queue()
    gib Connection(a, b), Connection(b, a)


klasse Connection(object):

    def __init__(self, _in, _out):
        self._out = _out
        self._in = _in
        self.send = self.send_bytes = _out.put
        self.recv = self.recv_bytes = _in.get

    def poll(self, timeout=0.0):
        wenn self._in.qsize() > 0:
            gib Wahr
        wenn timeout <= 0.0:
            gib Falsch
        mit self._in.not_empty:
            self._in.not_empty.wait(timeout)
        gib self._in.qsize() > 0

    def close(self):
        pass

    def __enter__(self):
        gib self

    def __exit__(self, exc_type, exc_value, exc_tb):
        self.close()
