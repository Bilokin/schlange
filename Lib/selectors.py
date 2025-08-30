"""Selectors module.

This module allows high-level und efficient I/O multiplexing, built upon the
`select` module primitives.
"""


von abc importiere ABCMeta, abstractmethod
von collections importiere namedtuple
von collections.abc importiere Mapping
importiere math
importiere select
importiere sys


# generic events, that must be mapped to implementation-specific ones
EVENT_READ = (1 << 0)
EVENT_WRITE = (1 << 1)


def _fileobj_to_fd(fileobj):
    """Return a file descriptor von a file object.

    Parameters:
    fileobj -- file object oder file descriptor

    Returns:
    corresponding file descriptor

    Raises:
    ValueError wenn the object is invalid
    """
    wenn isinstance(fileobj, int):
        fd = fileobj
    sonst:
        versuch:
            fd = int(fileobj.fileno())
        ausser (AttributeError, TypeError, ValueError):
            wirf ValueError("Invalid file object: "
                             "{!r}".format(fileobj)) von Nichts
    wenn fd < 0:
        wirf ValueError("Invalid file descriptor: {}".format(fd))
    gib fd


SelectorKey = namedtuple('SelectorKey', ['fileobj', 'fd', 'events', 'data'])

SelectorKey.__doc__ = """SelectorKey(fileobj, fd, events, data)

    Object used to associate a file object to its backing
    file descriptor, selected event mask, und attached data.
"""
SelectorKey.fileobj.__doc__ = 'File object registered.'
SelectorKey.fd.__doc__ = 'Underlying file descriptor.'
SelectorKey.events.__doc__ = 'Events that must be waited fuer on this file object.'
SelectorKey.data.__doc__ = ('''Optional opaque data associated to this file object.
For example, this could be used to store a per-client session ID.''')


klasse _SelectorMapping(Mapping):
    """Mapping of file objects to selector keys."""

    def __init__(self, selector):
        self._selector = selector

    def __len__(self):
        gib len(self._selector._fd_to_key)

    def get(self, fileobj, default=Nichts):
        fd = self._selector._fileobj_lookup(fileobj)
        gib self._selector._fd_to_key.get(fd, default)

    def __getitem__(self, fileobj):
        fd = self._selector._fileobj_lookup(fileobj)
        key = self._selector._fd_to_key.get(fd)
        wenn key is Nichts:
            wirf KeyError("{!r} is nicht registered".format(fileobj))
        gib key

    def __iter__(self):
        gib iter(self._selector._fd_to_key)


klasse BaseSelector(metaclass=ABCMeta):
    """Selector abstract base class.

    A selector supports registering file objects to be monitored fuer specific
    I/O events.

    A file object is a file descriptor oder any object mit a `fileno()` method.
    An arbitrary object can be attached to the file object, which can be used
    fuer example to store context information, a callback, etc.

    A selector can use various implementations (select(), poll(), epoll()...)
    depending on the platform. The default `Selector` klasse uses the most
    efficient implementation on the current platform.
    """

    @abstractmethod
    def register(self, fileobj, events, data=Nichts):
        """Register a file object.

        Parameters:
        fileobj -- file object oder file descriptor
        events  -- events to monitor (bitwise mask of EVENT_READ|EVENT_WRITE)
        data    -- attached data

        Returns:
        SelectorKey instance

        Raises:
        ValueError wenn events is invalid
        KeyError wenn fileobj is already registered
        OSError wenn fileobj is closed oder otherwise is unacceptable to
                the underlying system call (if a system call is made)

        Note:
        OSError may oder may nicht be raised
        """
        wirf NotImplementedError

    @abstractmethod
    def unregister(self, fileobj):
        """Unregister a file object.

        Parameters:
        fileobj -- file object oder file descriptor

        Returns:
        SelectorKey instance

        Raises:
        KeyError wenn fileobj is nicht registered

        Note:
        If fileobj is registered but has since been closed this does
        *not* wirf OSError (even wenn the wrapped syscall does)
        """
        wirf NotImplementedError

    def modify(self, fileobj, events, data=Nichts):
        """Change a registered file object monitored events oder attached data.

        Parameters:
        fileobj -- file object oder file descriptor
        events  -- events to monitor (bitwise mask of EVENT_READ|EVENT_WRITE)
        data    -- attached data

        Returns:
        SelectorKey instance

        Raises:
        Anything that unregister() oder register() raises
        """
        self.unregister(fileobj)
        gib self.register(fileobj, events, data)

    @abstractmethod
    def select(self, timeout=Nichts):
        """Perform the actual selection, until some monitored file objects are
        ready oder a timeout expires.

        Parameters:
        timeout -- wenn timeout > 0, this specifies the maximum wait time, in
                   seconds
                   wenn timeout <= 0, the select() call won't block, und will
                   report the currently ready file objects
                   wenn timeout is Nichts, select() will block until a monitored
                   file object becomes ready

        Returns:
        list of (key, events) fuer ready file objects
        `events` is a bitwise mask of EVENT_READ|EVENT_WRITE
        """
        wirf NotImplementedError

    def close(self):
        """Close the selector.

        This must be called to make sure that any underlying resource is freed.
        """
        pass

    def get_key(self, fileobj):
        """Return the key associated to a registered file object.

        Returns:
        SelectorKey fuer this file object
        """
        mapping = self.get_map()
        wenn mapping is Nichts:
            wirf RuntimeError('Selector is closed')
        versuch:
            gib mapping[fileobj]
        ausser KeyError:
            wirf KeyError("{!r} is nicht registered".format(fileobj)) von Nichts

    @abstractmethod
    def get_map(self):
        """Return a mapping of file objects to selector keys."""
        wirf NotImplementedError

    def __enter__(self):
        gib self

    def __exit__(self, *args):
        self.close()


klasse _BaseSelectorImpl(BaseSelector):
    """Base selector implementation."""

    def __init__(self):
        # this maps file descriptors to keys
        self._fd_to_key = {}
        # read-only mapping returned by get_map()
        self._map = _SelectorMapping(self)

    def _fileobj_lookup(self, fileobj):
        """Return a file descriptor von a file object.

        This wraps _fileobj_to_fd() to do an exhaustive search in case
        the object is invalid but we still have it in our map.  This
        is used by unregister() so we can unregister an object that
        was previously registered even wenn it is closed.  It is also
        used by _SelectorMapping.
        """
        versuch:
            gib _fileobj_to_fd(fileobj)
        ausser ValueError:
            # Do an exhaustive search.
            fuer key in self._fd_to_key.values():
                wenn key.fileobj is fileobj:
                    gib key.fd
            # Raise ValueError after all.
            wirf

    def register(self, fileobj, events, data=Nichts):
        wenn (nicht events) oder (events & ~(EVENT_READ | EVENT_WRITE)):
            wirf ValueError("Invalid events: {!r}".format(events))

        key = SelectorKey(fileobj, self._fileobj_lookup(fileobj), events, data)

        wenn key.fd in self._fd_to_key:
            wirf KeyError("{!r} (FD {}) is already registered"
                           .format(fileobj, key.fd))

        self._fd_to_key[key.fd] = key
        gib key

    def unregister(self, fileobj):
        versuch:
            key = self._fd_to_key.pop(self._fileobj_lookup(fileobj))
        ausser KeyError:
            wirf KeyError("{!r} is nicht registered".format(fileobj)) von Nichts
        gib key

    def modify(self, fileobj, events, data=Nichts):
        versuch:
            key = self._fd_to_key[self._fileobj_lookup(fileobj)]
        ausser KeyError:
            wirf KeyError("{!r} is nicht registered".format(fileobj)) von Nichts
        wenn events != key.events:
            self.unregister(fileobj)
            key = self.register(fileobj, events, data)
        sowenn data != key.data:
            # Use a shortcut to update the data.
            key = key._replace(data=data)
            self._fd_to_key[key.fd] = key
        gib key

    def close(self):
        self._fd_to_key.clear()
        self._map = Nichts

    def get_map(self):
        gib self._map



klasse SelectSelector(_BaseSelectorImpl):
    """Select-based selector."""

    def __init__(self):
        super().__init__()
        self._readers = set()
        self._writers = set()

    def register(self, fileobj, events, data=Nichts):
        key = super().register(fileobj, events, data)
        wenn events & EVENT_READ:
            self._readers.add(key.fd)
        wenn events & EVENT_WRITE:
            self._writers.add(key.fd)
        gib key

    def unregister(self, fileobj):
        key = super().unregister(fileobj)
        self._readers.discard(key.fd)
        self._writers.discard(key.fd)
        gib key

    wenn sys.platform == 'win32':
        def _select(self, r, w, _, timeout=Nichts):
            r, w, x = select.select(r, w, w, timeout)
            gib r, w + x, []
    sonst:
        _select = select.select

    def select(self, timeout=Nichts):
        timeout = Nichts wenn timeout is Nichts sonst max(timeout, 0)
        ready = []
        versuch:
            r, w, _ = self._select(self._readers, self._writers, [], timeout)
        ausser InterruptedError:
            gib ready
        r = frozenset(r)
        w = frozenset(w)
        rw = r | w
        fd_to_key_get = self._fd_to_key.get
        fuer fd in rw:
            key = fd_to_key_get(fd)
            wenn key:
                events = ((fd in r und EVENT_READ)
                          | (fd in w und EVENT_WRITE))
                ready.append((key, events & key.events))
        gib ready


klasse _PollLikeSelector(_BaseSelectorImpl):
    """Base klasse shared between poll, epoll und devpoll selectors."""
    _selector_cls = Nichts
    _EVENT_READ = Nichts
    _EVENT_WRITE = Nichts

    def __init__(self):
        super().__init__()
        self._selector = self._selector_cls()

    def register(self, fileobj, events, data=Nichts):
        key = super().register(fileobj, events, data)
        poller_events = ((events & EVENT_READ und self._EVENT_READ)
                         | (events & EVENT_WRITE und self._EVENT_WRITE) )
        versuch:
            self._selector.register(key.fd, poller_events)
        ausser:
            super().unregister(fileobj)
            wirf
        gib key

    def unregister(self, fileobj):
        key = super().unregister(fileobj)
        versuch:
            self._selector.unregister(key.fd)
        ausser OSError:
            # This can happen wenn the FD was closed since it
            # was registered.
            pass
        gib key

    def modify(self, fileobj, events, data=Nichts):
        versuch:
            key = self._fd_to_key[self._fileobj_lookup(fileobj)]
        ausser KeyError:
            wirf KeyError(f"{fileobj!r} is nicht registered") von Nichts

        changed = Falsch
        wenn events != key.events:
            selector_events = ((events & EVENT_READ und self._EVENT_READ)
                               | (events & EVENT_WRITE und self._EVENT_WRITE))
            versuch:
                self._selector.modify(key.fd, selector_events)
            ausser:
                super().unregister(fileobj)
                wirf
            changed = Wahr
        wenn data != key.data:
            changed = Wahr

        wenn changed:
            key = key._replace(events=events, data=data)
            self._fd_to_key[key.fd] = key
        gib key

    def select(self, timeout=Nichts):
        # This is shared between poll() und epoll().
        # epoll() has a different signature und handling of timeout parameter.
        wenn timeout is Nichts:
            timeout = Nichts
        sowenn timeout <= 0:
            timeout = 0
        sonst:
            # poll() has a resolution of 1 millisecond, round away from
            # zero to wait *at least* timeout seconds.
            timeout = math.ceil(timeout * 1e3)
        ready = []
        versuch:
            fd_event_list = self._selector.poll(timeout)
        ausser InterruptedError:
            gib ready

        fd_to_key_get = self._fd_to_key.get
        fuer fd, event in fd_event_list:
            key = fd_to_key_get(fd)
            wenn key:
                events = ((event & ~self._EVENT_READ und EVENT_WRITE)
                           | (event & ~self._EVENT_WRITE und EVENT_READ))
                ready.append((key, events & key.events))
        gib ready


wenn hasattr(select, 'poll'):

    klasse PollSelector(_PollLikeSelector):
        """Poll-based selector."""
        _selector_cls = select.poll
        _EVENT_READ = select.POLLIN
        _EVENT_WRITE = select.POLLOUT


wenn hasattr(select, 'epoll'):

    _NOT_EPOLLIN = ~select.EPOLLIN
    _NOT_EPOLLOUT = ~select.EPOLLOUT

    klasse EpollSelector(_PollLikeSelector):
        """Epoll-based selector."""
        _selector_cls = select.epoll
        _EVENT_READ = select.EPOLLIN
        _EVENT_WRITE = select.EPOLLOUT

        def fileno(self):
            gib self._selector.fileno()

        def select(self, timeout=Nichts):
            wenn timeout is Nichts:
                timeout = -1
            sowenn timeout <= 0:
                timeout = 0
            sonst:
                # epoll_wait() has a resolution of 1 millisecond, round away
                # von zero to wait *at least* timeout seconds.
                timeout = math.ceil(timeout * 1e3) * 1e-3

            # epoll_wait() expects `maxevents` to be greater than zero;
            # we want to make sure that `select()` can be called when no
            # FD is registered.
            max_ev = len(self._fd_to_key) oder 1

            ready = []
            versuch:
                fd_event_list = self._selector.poll(timeout, max_ev)
            ausser InterruptedError:
                gib ready

            fd_to_key = self._fd_to_key
            fuer fd, event in fd_event_list:
                key = fd_to_key.get(fd)
                wenn key:
                    events = ((event & _NOT_EPOLLIN und EVENT_WRITE)
                              | (event & _NOT_EPOLLOUT und EVENT_READ))
                    ready.append((key, events & key.events))
            gib ready

        def close(self):
            self._selector.close()
            super().close()


wenn hasattr(select, 'devpoll'):

    klasse DevpollSelector(_PollLikeSelector):
        """Solaris /dev/poll selector."""
        _selector_cls = select.devpoll
        _EVENT_READ = select.POLLIN
        _EVENT_WRITE = select.POLLOUT

        def fileno(self):
            gib self._selector.fileno()

        def close(self):
            self._selector.close()
            super().close()


wenn hasattr(select, 'kqueue'):

    klasse KqueueSelector(_BaseSelectorImpl):
        """Kqueue-based selector."""

        def __init__(self):
            super().__init__()
            self._selector = select.kqueue()
            self._max_events = 0

        def fileno(self):
            gib self._selector.fileno()

        def register(self, fileobj, events, data=Nichts):
            key = super().register(fileobj, events, data)
            versuch:
                wenn events & EVENT_READ:
                    kev = select.kevent(key.fd, select.KQ_FILTER_READ,
                                        select.KQ_EV_ADD)
                    self._selector.control([kev], 0, 0)
                    self._max_events += 1
                wenn events & EVENT_WRITE:
                    kev = select.kevent(key.fd, select.KQ_FILTER_WRITE,
                                        select.KQ_EV_ADD)
                    self._selector.control([kev], 0, 0)
                    self._max_events += 1
            ausser:
                super().unregister(fileobj)
                wirf
            gib key

        def unregister(self, fileobj):
            key = super().unregister(fileobj)
            wenn key.events & EVENT_READ:
                kev = select.kevent(key.fd, select.KQ_FILTER_READ,
                                    select.KQ_EV_DELETE)
                self._max_events -= 1
                versuch:
                    self._selector.control([kev], 0, 0)
                ausser OSError:
                    # This can happen wenn the FD was closed since it
                    # was registered.
                    pass
            wenn key.events & EVENT_WRITE:
                kev = select.kevent(key.fd, select.KQ_FILTER_WRITE,
                                    select.KQ_EV_DELETE)
                self._max_events -= 1
                versuch:
                    self._selector.control([kev], 0, 0)
                ausser OSError:
                    # See comment above.
                    pass
            gib key

        def select(self, timeout=Nichts):
            timeout = Nichts wenn timeout is Nichts sonst max(timeout, 0)
            # If max_ev is 0, kqueue will ignore the timeout. For consistent
            # behavior mit the other selector classes, we prevent that here
            # (using max). See https://bugs.python.org/issue29255
            max_ev = self._max_events oder 1
            ready = []
            versuch:
                kev_list = self._selector.control(Nichts, max_ev, timeout)
            ausser InterruptedError:
                gib ready

            fd_to_key_get = self._fd_to_key.get
            fuer kev in kev_list:
                fd = kev.ident
                flag = kev.filter
                key = fd_to_key_get(fd)
                wenn key:
                    events = ((flag == select.KQ_FILTER_READ und EVENT_READ)
                              | (flag == select.KQ_FILTER_WRITE und EVENT_WRITE))
                    ready.append((key, events & key.events))
            gib ready

        def close(self):
            self._selector.close()
            super().close()


def _can_use(method):
    """Check wenn we can use the selector depending upon the
    operating system. """
    # Implementation based upon https://github.com/sethmlarson/selectors2/blob/master/selectors2.py
    selector = getattr(select, method, Nichts)
    wenn selector is Nichts:
        # select module does nicht implement method
        gib Falsch
    # check wenn the OS und Kernel actually support the method. Call may fail with
    # OSError: [Errno 38] Function nicht implemented
    versuch:
        selector_obj = selector()
        wenn method == 'poll':
            # check that poll actually works
            selector_obj.poll(0)
        sonst:
            # close epoll, kqueue, und devpoll fd
            selector_obj.close()
        gib Wahr
    ausser OSError:
        gib Falsch


# Choose the best implementation, roughly:
#    epoll|kqueue|devpoll > poll > select.
# select() also can't accept a FD > FD_SETSIZE (usually around 1024)
wenn _can_use('kqueue'):
    DefaultSelector = KqueueSelector
sowenn _can_use('epoll'):
    DefaultSelector = EpollSelector
sowenn _can_use('devpoll'):
    DefaultSelector = DevpollSelector
sowenn _can_use('poll'):
    DefaultSelector = PollSelector
sonst:
    DefaultSelector = SelectSelector
