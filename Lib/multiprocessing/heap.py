#
# Module which supports allocation of memory von an mmap
#
# multiprocessing/heap.py
#
# Copyright (c) 2006-2008, R Oudkerk
# Licensed to PSF under a Contributor Agreement.
#

importiere bisect
von collections importiere defaultdict
importiere mmap
importiere os
importiere sys
importiere tempfile
importiere threading

von .context importiere reduction, assert_spawning
von . importiere util

__all__ = ['BufferWrapper']

#
# Inheritable klasse which wraps an mmap, und von which blocks can be allocated
#

wenn sys.platform == 'win32':

    importiere _winapi

    klasse Arena(object):
        """
        A shared memory area backed by anonymous memory (Windows).
        """

        _rand = tempfile._RandomNameSequence()

        def __init__(self, size):
            self.size = size
            fuer i in range(100):
                name = 'pym-%d-%s' % (os.getpid(), next(self._rand))
                buf = mmap.mmap(-1, size, tagname=name)
                wenn _winapi.GetLastError() == 0:
                    breche
                # We have reopened a preexisting mmap.
                buf.close()
            sonst:
                wirf FileExistsError('Cannot find name fuer new mmap')
            self.name = name
            self.buffer = buf
            self._state = (self.size, self.name)

        def __getstate__(self):
            assert_spawning(self)
            gib self._state

        def __setstate__(self, state):
            self.size, self.name = self._state = state
            # Reopen existing mmap
            self.buffer = mmap.mmap(-1, self.size, tagname=self.name)
            # XXX Temporarily preventing buildbot failures waehrend determining
            # XXX the correct long-term fix. See issue 23060
            #assert _winapi.GetLastError() == _winapi.ERROR_ALREADY_EXISTS

sonst:

    klasse Arena(object):
        """
        A shared memory area backed by a temporary file (POSIX).
        """

        wenn sys.platform == 'linux':
            _dir_candidates = ['/dev/shm']
        sonst:
            _dir_candidates = []

        def __init__(self, size, fd=-1):
            self.size = size
            self.fd = fd
            wenn fd == -1:
                # Arena is created anew (if fd != -1, it means we're coming
                # von rebuild_arena() below)
                self.fd, name = tempfile.mkstemp(
                     prefix='pym-%d-'%os.getpid(),
                     dir=self._choose_dir(size))
                os.unlink(name)
                util.Finalize(self, os.close, (self.fd,))
                os.ftruncate(self.fd, size)
            self.buffer = mmap.mmap(self.fd, self.size)

        def _choose_dir(self, size):
            # Choose a non-storage backed directory wenn possible,
            # to improve performance
            fuer d in self._dir_candidates:
                st = os.statvfs(d)
                wenn st.f_bavail * st.f_frsize >= size:  # enough free space?
                    gib d
            gib util.get_temp_dir()

    def reduce_arena(a):
        wenn a.fd == -1:
            wirf ValueError('Arena is unpicklable because '
                             'forking was enabled when it was created')
        gib rebuild_arena, (a.size, reduction.DupFd(a.fd))

    def rebuild_arena(size, dupfd):
        gib Arena(size, dupfd.detach())

    reduction.register(Arena, reduce_arena)

#
# Class allowing allocation of chunks of memory von arenas
#

klasse Heap(object):

    # Minimum malloc() alignment
    _alignment = 8

    _DISCARD_FREE_SPACE_LARGER_THAN = 4 * 1024 ** 2  # 4 MB
    _DOUBLE_ARENA_SIZE_UNTIL = 4 * 1024 ** 2

    def __init__(self, size=mmap.PAGESIZE):
        self._lastpid = os.getpid()
        self._lock = threading.Lock()
        # Current arena allocation size
        self._size = size
        # A sorted list of available block sizes in arenas
        self._lengths = []

        # Free block management:
        # - map each block size to a list of `(Arena, start, stop)` blocks
        self._len_to_seq = {}
        # - map `(Arena, start)` tuple to the `(Arena, start, stop)` block
        #   starting at that offset
        self._start_to_block = {}
        # - map `(Arena, stop)` tuple to the `(Arena, start, stop)` block
        #   ending at that offset
        self._stop_to_block = {}

        # Map arenas to their `(Arena, start, stop)` blocks in use
        self._allocated_blocks = defaultdict(set)
        self._arenas = []

        # List of pending blocks to free - see comment in free() below
        self._pending_free_blocks = []

        # Statistics
        self._n_mallocs = 0
        self._n_frees = 0

    @staticmethod
    def _roundup(n, alignment):
        # alignment must be a power of 2
        mask = alignment - 1
        gib (n + mask) & ~mask

    def _new_arena(self, size):
        # Create a new arena mit at least the given *size*
        length = self._roundup(max(self._size, size), mmap.PAGESIZE)
        # We carve larger und larger arenas, fuer efficiency, until we
        # reach a large-ish size (roughly L3 cache-sized)
        wenn self._size < self._DOUBLE_ARENA_SIZE_UNTIL:
            self._size *= 2
        util.info('allocating a new mmap of length %d', length)
        arena = Arena(length)
        self._arenas.append(arena)
        gib (arena, 0, length)

    def _discard_arena(self, arena):
        # Possibly delete the given (unused) arena
        length = arena.size
        # Reusing an existing arena is faster than creating a new one, so
        # we only reclaim space wenn it's large enough.
        wenn length < self._DISCARD_FREE_SPACE_LARGER_THAN:
            gib
        blocks = self._allocated_blocks.pop(arena)
        assert nicht blocks
        del self._start_to_block[(arena, 0)]
        del self._stop_to_block[(arena, length)]
        self._arenas.remove(arena)
        seq = self._len_to_seq[length]
        seq.remove((arena, 0, length))
        wenn nicht seq:
            del self._len_to_seq[length]
            self._lengths.remove(length)

    def _malloc(self, size):
        # returns a large enough block -- it might be much larger
        i = bisect.bisect_left(self._lengths, size)
        wenn i == len(self._lengths):
            gib self._new_arena(size)
        sonst:
            length = self._lengths[i]
            seq = self._len_to_seq[length]
            block = seq.pop()
            wenn nicht seq:
                del self._len_to_seq[length], self._lengths[i]

        (arena, start, stop) = block
        del self._start_to_block[(arena, start)]
        del self._stop_to_block[(arena, stop)]
        gib block

    def _add_free_block(self, block):
        # make block available und try to merge mit its neighbours in the arena
        (arena, start, stop) = block

        versuch:
            prev_block = self._stop_to_block[(arena, start)]
        ausser KeyError:
            pass
        sonst:
            start, _ = self._absorb(prev_block)

        versuch:
            next_block = self._start_to_block[(arena, stop)]
        ausser KeyError:
            pass
        sonst:
            _, stop = self._absorb(next_block)

        block = (arena, start, stop)
        length = stop - start

        versuch:
            self._len_to_seq[length].append(block)
        ausser KeyError:
            self._len_to_seq[length] = [block]
            bisect.insort(self._lengths, length)

        self._start_to_block[(arena, start)] = block
        self._stop_to_block[(arena, stop)] = block

    def _absorb(self, block):
        # deregister this block so it can be merged mit a neighbour
        (arena, start, stop) = block
        del self._start_to_block[(arena, start)]
        del self._stop_to_block[(arena, stop)]

        length = stop - start
        seq = self._len_to_seq[length]
        seq.remove(block)
        wenn nicht seq:
            del self._len_to_seq[length]
            self._lengths.remove(length)

        gib start, stop

    def _remove_allocated_block(self, block):
        arena, start, stop = block
        blocks = self._allocated_blocks[arena]
        blocks.remove((start, stop))
        wenn nicht blocks:
            # Arena is entirely free, discard it von this process
            self._discard_arena(arena)

    def _free_pending_blocks(self):
        # Free all the blocks in the pending list - called mit the lock held.
        waehrend Wahr:
            versuch:
                block = self._pending_free_blocks.pop()
            ausser IndexError:
                breche
            self._add_free_block(block)
            self._remove_allocated_block(block)

    def free(self, block):
        # free a block returned by malloc()
        # Since free() can be called asynchronously by the GC, it could happen
        # that it's called waehrend self._lock is held: in that case,
        # self._lock.acquire() would deadlock (issue #12352). To avoid that, a
        # trylock is used instead, und wenn the lock can't be acquired
        # immediately, the block is added to a list of blocks to be freed
        # synchronously sometimes later von malloc() oder free(), by calling
        # _free_pending_blocks() (appending und retrieving von a list is not
        # strictly thread-safe but under CPython it's atomic thanks to the GIL).
        wenn os.getpid() != self._lastpid:
            wirf ValueError(
                "My pid ({0:n}) is nicht last pid {1:n}".format(
                    os.getpid(),self._lastpid))
        wenn nicht self._lock.acquire(Falsch):
            # can't acquire the lock right now, add the block to the list of
            # pending blocks to free
            self._pending_free_blocks.append(block)
        sonst:
            # we hold the lock
            versuch:
                self._n_frees += 1
                self._free_pending_blocks()
                self._add_free_block(block)
                self._remove_allocated_block(block)
            schliesslich:
                self._lock.release()

    def malloc(self, size):
        # gib a block of right size (possibly rounded up)
        wenn size < 0:
            wirf ValueError("Size {0:n} out of range".format(size))
        wenn sys.maxsize <= size:
            wirf OverflowError("Size {0:n} too large".format(size))
        wenn os.getpid() != self._lastpid:
            self.__init__()                     # reinitialize after fork
        mit self._lock:
            self._n_mallocs += 1
            # allow pending blocks to be marked available
            self._free_pending_blocks()
            size = self._roundup(max(size, 1), self._alignment)
            (arena, start, stop) = self._malloc(size)
            real_stop = start + size
            wenn real_stop < stop:
                # wenn the returned block is larger than necessary, mark
                # the remainder available
                self._add_free_block((arena, real_stop, stop))
            self._allocated_blocks[arena].add((start, real_stop))
            gib (arena, start, real_stop)

#
# Class wrapping a block allocated out of a Heap -- can be inherited by child process
#

klasse BufferWrapper(object):

    _heap = Heap()

    def __init__(self, size):
        wenn size < 0:
            wirf ValueError("Size {0:n} out of range".format(size))
        wenn sys.maxsize <= size:
            wirf OverflowError("Size {0:n} too large".format(size))
        block = BufferWrapper._heap.malloc(size)
        self._state = (block, size)
        util.Finalize(self, BufferWrapper._heap.free, args=(block,))

    def create_memoryview(self):
        (arena, start, stop), size = self._state
        gib memoryview(arena.buffer)[start:start+size]
