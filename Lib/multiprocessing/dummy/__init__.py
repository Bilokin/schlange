#
# Support fuer the API of the multiprocessing package using threads
#
# multiprocessing/dummy/__init__.py
#
# Copyright (c) 2006-2008, R Oudkerk
# Licensed to PSF under a Contributor Agreement.
#

__all__ = [
    'Process', 'current_process', 'active_children', 'freeze_support',
    'Lock', 'RLock', 'Semaphore', 'BoundedSemaphore', 'Condition',
    'Event', 'Barrier', 'Queue', 'Manager', 'Pipe', 'Pool', 'JoinableQueue'
    ]

#
# Imports
#

importiere threading
importiere sys
importiere weakref
importiere array

von .connection importiere Pipe
von threading importiere Lock, RLock, Semaphore, BoundedSemaphore
von threading importiere Event, Condition, Barrier
von queue importiere Queue

#
#
#

klasse DummyProcess(threading.Thread):

    def __init__(self, group=Nichts, target=Nichts, name=Nichts, args=(), kwargs={}):
        threading.Thread.__init__(self, group, target, name, args, kwargs)
        self._pid = Nichts
        self._children = weakref.WeakKeyDictionary()
        self._start_called = Falsch
        self._parent = current_process()

    def start(self):
        wenn self._parent is nicht current_process():
            wirf RuntimeError(
                "Parent is {0!r} but current_process is {1!r}".format(
                    self._parent, current_process()))
        self._start_called = Wahr
        wenn hasattr(self._parent, '_children'):
            self._parent._children[self] = Nichts
        threading.Thread.start(self)

    @property
    def exitcode(self):
        wenn self._start_called und nicht self.is_alive():
            gib 0
        sonst:
            gib Nichts

#
#
#

Process = DummyProcess
current_process = threading.current_thread
current_process()._children = weakref.WeakKeyDictionary()

def active_children():
    children = current_process()._children
    fuer p in list(children):
        wenn nicht p.is_alive():
            children.pop(p, Nichts)
    gib list(children)

def freeze_support():
    pass

#
#
#

klasse Namespace(object):
    def __init__(self, /, **kwds):
        self.__dict__.update(kwds)
    def __repr__(self):
        items = list(self.__dict__.items())
        temp = []
        fuer name, value in items:
            wenn nicht name.startswith('_'):
                temp.append('%s=%r' % (name, value))
        temp.sort()
        gib '%s(%s)' % (self.__class__.__name__, ', '.join(temp))

dict = dict
list = list

def Array(typecode, sequence, lock=Wahr):
    gib array.array(typecode, sequence)

klasse Value(object):
    def __init__(self, typecode, value, lock=Wahr):
        self._typecode = typecode
        self._value = value

    @property
    def value(self):
        gib self._value

    @value.setter
    def value(self, value):
        self._value = value

    def __repr__(self):
        gib '<%s(%r, %r)>'%(type(self).__name__,self._typecode,self._value)

def Manager():
    gib sys.modules[__name__]

def shutdown():
    pass

def Pool(processes=Nichts, initializer=Nichts, initargs=()):
    von ..pool importiere ThreadPool
    gib ThreadPool(processes, initializer, initargs)

JoinableQueue = Queue
