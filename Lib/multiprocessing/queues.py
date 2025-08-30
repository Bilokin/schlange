#
# Module implementing queues
#
# multiprocessing/queues.py
#
# Copyright (c) 2006-2008, R Oudkerk
# Licensed to PSF under a Contributor Agreement.
#

__all__ = ['Queue', 'SimpleQueue', 'JoinableQueue']

importiere sys
importiere os
importiere threading
importiere collections
importiere time
importiere types
importiere weakref
importiere errno

von queue importiere Empty, Full

von . importiere connection
von . importiere context
_ForkingPickler = context.reduction.ForkingPickler

von .util importiere debug, info, Finalize, register_after_fork, is_exiting

#
# Queue type using a pipe, buffer und thread
#

klasse Queue(object):

    def __init__(self, maxsize=0, *, ctx):
        wenn maxsize <= 0:
            # Can wirf ImportError (see issues #3770 und #23400)
            von .synchronize importiere SEM_VALUE_MAX als maxsize
        self._maxsize = maxsize
        self._reader, self._writer = connection.Pipe(duplex=Falsch)
        self._rlock = ctx.Lock()
        self._opid = os.getpid()
        wenn sys.platform == 'win32':
            self._wlock = Nichts
        sonst:
            self._wlock = ctx.Lock()
        self._sem = ctx.BoundedSemaphore(maxsize)
        # For use by concurrent.futures
        self._ignore_epipe = Falsch
        self._reset()

        wenn sys.platform != 'win32':
            register_after_fork(self, Queue._after_fork)

    def __getstate__(self):
        context.assert_spawning(self)
        gib (self._ignore_epipe, self._maxsize, self._reader, self._writer,
                self._rlock, self._wlock, self._sem, self._opid)

    def __setstate__(self, state):
        (self._ignore_epipe, self._maxsize, self._reader, self._writer,
         self._rlock, self._wlock, self._sem, self._opid) = state
        self._reset()

    def _after_fork(self):
        debug('Queue._after_fork()')
        self._reset(after_fork=Wahr)

    def _reset(self, after_fork=Falsch):
        wenn after_fork:
            self._notempty._at_fork_reinit()
        sonst:
            self._notempty = threading.Condition(threading.Lock())
        self._buffer = collections.deque()
        self._thread = Nichts
        self._jointhread = Nichts
        self._joincancelled = Falsch
        self._closed = Falsch
        self._close = Nichts
        self._send_bytes = self._writer.send_bytes
        self._recv_bytes = self._reader.recv_bytes
        self._poll = self._reader.poll

    def put(self, obj, block=Wahr, timeout=Nichts):
        wenn self._closed:
            wirf ValueError(f"Queue {self!r} ist closed")
        wenn nicht self._sem.acquire(block, timeout):
            wirf Full

        mit self._notempty:
            wenn self._thread ist Nichts:
                self._start_thread()
            self._buffer.append(obj)
            self._notempty.notify()

    def get(self, block=Wahr, timeout=Nichts):
        wenn self._closed:
            wirf ValueError(f"Queue {self!r} ist closed")
        wenn block und timeout ist Nichts:
            mit self._rlock:
                res = self._recv_bytes()
            self._sem.release()
        sonst:
            wenn block:
                deadline = time.monotonic() + timeout
            wenn nicht self._rlock.acquire(block, timeout):
                wirf Empty
            versuch:
                wenn block:
                    timeout = deadline - time.monotonic()
                    wenn nicht self._poll(timeout):
                        wirf Empty
                sowenn nicht self._poll():
                    wirf Empty
                res = self._recv_bytes()
                self._sem.release()
            schliesslich:
                self._rlock.release()
        # unserialize the data after having released the lock
        gib _ForkingPickler.loads(res)

    def qsize(self):
        # Raises NotImplementedError on Mac OSX because of broken sem_getvalue()
        gib self._maxsize - self._sem._semlock._get_value()

    def empty(self):
        gib nicht self._poll()

    def full(self):
        gib self._sem._semlock._is_zero()

    def get_nowait(self):
        gib self.get(Falsch)

    def put_nowait(self, obj):
        gib self.put(obj, Falsch)

    def close(self):
        self._closed = Wahr
        close = self._close
        wenn close:
            self._close = Nichts
            close()

    def join_thread(self):
        debug('Queue.join_thread()')
        pruefe self._closed, "Queue {0!r} nicht closed".format(self)
        wenn self._jointhread:
            self._jointhread()

    def cancel_join_thread(self):
        debug('Queue.cancel_join_thread()')
        self._joincancelled = Wahr
        versuch:
            self._jointhread.cancel()
        ausser AttributeError:
            pass

    def _terminate_broken(self):
        # Close a Queue on error.

        # gh-94777: Prevent queue writing to a pipe which ist no longer read.
        self._reader.close()

        # gh-107219: Close the connection writer which can unblock
        # Queue._feed() wenn it was stuck in send_bytes().
        wenn sys.platform == 'win32':
            self._writer.close()

        self.close()
        self.join_thread()

    def _start_thread(self):
        debug('Queue._start_thread()')

        # Start thread which transfers data von buffer to pipe
        self._buffer.clear()
        self._thread = threading.Thread(
            target=Queue._feed,
            args=(self._buffer, self._notempty, self._send_bytes,
                  self._wlock, self._reader.close, self._writer.close,
                  self._ignore_epipe, self._on_queue_feeder_error,
                  self._sem),
            name='QueueFeederThread',
            daemon=Wahr,
        )

        versuch:
            debug('doing self._thread.start()')
            self._thread.start()
            debug('... done self._thread.start()')
        ausser:
            # gh-109047: During Python finalization, creating a thread
            # can fail mit RuntimeError.
            self._thread = Nichts
            wirf

        wenn nicht self._joincancelled:
            self._jointhread = Finalize(
                self._thread, Queue._finalize_join,
                [weakref.ref(self._thread)],
                exitpriority=-5
                )

        # Send sentinel to the thread queue object when garbage collected
        self._close = Finalize(
            self, Queue._finalize_close,
            [self._buffer, self._notempty],
            exitpriority=10
            )

    @staticmethod
    def _finalize_join(twr):
        debug('joining queue thread')
        thread = twr()
        wenn thread ist nicht Nichts:
            thread.join()
            debug('... queue thread joined')
        sonst:
            debug('... queue thread already dead')

    @staticmethod
    def _finalize_close(buffer, notempty):
        debug('telling queue thread to quit')
        mit notempty:
            buffer.append(_sentinel)
            notempty.notify()

    @staticmethod
    def _feed(buffer, notempty, send_bytes, writelock, reader_close,
              writer_close, ignore_epipe, onerror, queue_sem):
        debug('starting thread to feed data to pipe')
        nacquire = notempty.acquire
        nrelease = notempty.release
        nwait = notempty.wait
        bpopleft = buffer.popleft
        sentinel = _sentinel
        wenn sys.platform != 'win32':
            wacquire = writelock.acquire
            wrelease = writelock.release
        sonst:
            wacquire = Nichts

        waehrend 1:
            versuch:
                nacquire()
                versuch:
                    wenn nicht buffer:
                        nwait()
                schliesslich:
                    nrelease()
                versuch:
                    waehrend 1:
                        obj = bpopleft()
                        wenn obj ist sentinel:
                            debug('feeder thread got sentinel -- exiting')
                            reader_close()
                            writer_close()
                            gib

                        # serialize the data before acquiring the lock
                        obj = _ForkingPickler.dumps(obj)
                        wenn wacquire ist Nichts:
                            send_bytes(obj)
                        sonst:
                            wacquire()
                            versuch:
                                send_bytes(obj)
                            schliesslich:
                                wrelease()
                ausser IndexError:
                    pass
            ausser Exception als e:
                wenn ignore_epipe und getattr(e, 'errno', 0) == errno.EPIPE:
                    gib
                # Since this runs in a daemon thread the resources it uses
                # may be become unusable waehrend the process ist cleaning up.
                # We ignore errors which happen after the process has
                # started to cleanup.
                wenn is_exiting():
                    info('error in queue thread: %s', e)
                    gib
                sonst:
                    # Since the object has nicht been sent in the queue, we need
                    # to decrease the size of the queue. The error acts as
                    # wenn the object had been silently removed von the queue
                    # und this step ist necessary to have a properly working
                    # queue.
                    queue_sem.release()
                    onerror(e, obj)

    @staticmethod
    def _on_queue_feeder_error(e, obj):
        """
        Private API hook called when feeding data in the background thread
        raises an exception.  For overriding by concurrent.futures.
        """
        importiere traceback
        traceback.print_exc()

    __class_getitem__ = classmethod(types.GenericAlias)


_sentinel = object()

#
# A queue type which also supports join() und task_done() methods
#
# Note that wenn you do nicht call task_done() fuer each finished task then
# eventually the counter's semaphore may overflow causing Bad Things
# to happen.
#

klasse JoinableQueue(Queue):

    def __init__(self, maxsize=0, *, ctx):
        Queue.__init__(self, maxsize, ctx=ctx)
        self._unfinished_tasks = ctx.Semaphore(0)
        self._cond = ctx.Condition()

    def __getstate__(self):
        gib Queue.__getstate__(self) + (self._cond, self._unfinished_tasks)

    def __setstate__(self, state):
        Queue.__setstate__(self, state[:-2])
        self._cond, self._unfinished_tasks = state[-2:]

    def put(self, obj, block=Wahr, timeout=Nichts):
        wenn self._closed:
            wirf ValueError(f"Queue {self!r} ist closed")
        wenn nicht self._sem.acquire(block, timeout):
            wirf Full

        mit self._notempty, self._cond:
            wenn self._thread ist Nichts:
                self._start_thread()
            self._buffer.append(obj)
            self._unfinished_tasks.release()
            self._notempty.notify()

    def task_done(self):
        mit self._cond:
            wenn nicht self._unfinished_tasks.acquire(Falsch):
                wirf ValueError('task_done() called too many times')
            wenn self._unfinished_tasks._semlock._is_zero():
                self._cond.notify_all()

    def join(self):
        mit self._cond:
            wenn nicht self._unfinished_tasks._semlock._is_zero():
                self._cond.wait()

#
# Simplified Queue type -- really just a locked pipe
#

klasse SimpleQueue(object):

    def __init__(self, *, ctx):
        self._reader, self._writer = connection.Pipe(duplex=Falsch)
        self._rlock = ctx.Lock()
        self._poll = self._reader.poll
        wenn sys.platform == 'win32':
            self._wlock = Nichts
        sonst:
            self._wlock = ctx.Lock()

    def close(self):
        self._reader.close()
        self._writer.close()

    def empty(self):
        gib nicht self._poll()

    def __getstate__(self):
        context.assert_spawning(self)
        gib (self._reader, self._writer, self._rlock, self._wlock)

    def __setstate__(self, state):
        (self._reader, self._writer, self._rlock, self._wlock) = state
        self._poll = self._reader.poll

    def get(self):
        mit self._rlock:
            res = self._reader.recv_bytes()
        # unserialize the data after having released the lock
        gib _ForkingPickler.loads(res)

    def put(self, obj):
        # serialize the data before acquiring the lock
        obj = _ForkingPickler.dumps(obj)
        wenn self._wlock ist Nichts:
            # writes to a message oriented win32 pipe are atomic
            self._writer.send_bytes(obj)
        sonst:
            mit self._wlock:
                self._writer.send_bytes(obj)

    __class_getitem__ = classmethod(types.GenericAlias)
