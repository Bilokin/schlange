#
# Module providing the `Pool` klasse fuer managing a process pool
#
# multiprocessing/pool.py
#
# Copyright (c) 2006-2008, R Oudkerk
# Licensed to PSF under a Contributor Agreement.
#

__all__ = ['Pool', 'ThreadPool']

#
# Imports
#

importiere collections
importiere itertools
importiere os
importiere queue
importiere threading
importiere time
importiere traceback
importiere types
importiere warnings

# If threading ist available then ThreadPool should be provided.  Therefore
# we avoid top-level imports which are liable to fail on some systems.
von . importiere util
von . importiere get_context, TimeoutError
von .connection importiere wait

#
# Constants representing the state of a pool
#

INIT = "INIT"
RUN = "RUN"
CLOSE = "CLOSE"
TERMINATE = "TERMINATE"

#
# Miscellaneous
#

job_counter = itertools.count()

def mapstar(args):
    gib list(map(*args))

def starmapstar(args):
    gib list(itertools.starmap(args[0], args[1]))

#
# Hack to embed stringification of remote traceback in local traceback
#

klasse RemoteTraceback(Exception):
    def __init__(self, tb):
        self.tb = tb
    def __str__(self):
        gib self.tb

klasse ExceptionWithTraceback:
    def __init__(self, exc, tb):
        tb = traceback.format_exception(type(exc), exc, tb)
        tb = ''.join(tb)
        self.exc = exc
        self.tb = '\n"""\n%s"""' % tb
    def __reduce__(self):
        gib rebuild_exc, (self.exc, self.tb)

def rebuild_exc(exc, tb):
    exc.__cause__ = RemoteTraceback(tb)
    gib exc

#
# Code run by worker processes
#

klasse MaybeEncodingError(Exception):
    """Wraps possible unpickleable errors, so they can be
    safely sent through the socket."""

    def __init__(self, exc, value):
        self.exc = repr(exc)
        self.value = repr(value)
        super(MaybeEncodingError, self).__init__(self.exc, self.value)

    def __str__(self):
        gib "Error sending result: '%s'. Reason: '%s'" % (self.value,
                                                             self.exc)

    def __repr__(self):
        gib "<%s: %s>" % (self.__class__.__name__, self)


def worker(inqueue, outqueue, initializer=Nichts, initargs=(), maxtasks=Nichts,
           wrap_exception=Falsch):
    wenn (maxtasks ist nicht Nichts) und nicht (isinstance(maxtasks, int)
                                       und maxtasks >= 1):
        wirf AssertionError("Maxtasks {!r} ist nicht valid".format(maxtasks))
    put = outqueue.put
    get = inqueue.get
    wenn hasattr(inqueue, '_writer'):
        inqueue._writer.close()
        outqueue._reader.close()

    wenn initializer ist nicht Nichts:
        initializer(*initargs)

    completed = 0
    waehrend maxtasks ist Nichts oder (maxtasks und completed < maxtasks):
        versuch:
            task = get()
        ausser (EOFError, OSError):
            util.debug('worker got EOFError oder OSError -- exiting')
            breche

        wenn task ist Nichts:
            util.debug('worker got sentinel -- exiting')
            breche

        job, i, func, args, kwds = task
        versuch:
            result = (Wahr, func(*args, **kwds))
        ausser Exception als e:
            wenn wrap_exception und func ist nicht _helper_reraises_exception:
                e = ExceptionWithTraceback(e, e.__traceback__)
            result = (Falsch, e)
        versuch:
            put((job, i, result))
        ausser Exception als e:
            wrapped = MaybeEncodingError(e, result[1])
            util.debug("Possible encoding error waehrend sending result: %s" % (
                wrapped))
            put((job, i, (Falsch, wrapped)))

        task = job = result = func = args = kwds = Nichts
        completed += 1
    util.debug('worker exiting after %d tasks' % completed)

def _helper_reraises_exception(ex):
    'Pickle-able helper function fuer use by _guarded_task_generation.'
    wirf ex

#
# Class representing a process pool
#

klasse _PoolCache(dict):
    """
    Class that implements a cache fuer the Pool klasse that will notify
    the pool management threads every time the cache ist emptied. The
    notification ist done by the use of a queue that ist provided when
    instantiating the cache.
    """
    def __init__(self, /, *args, notifier=Nichts, **kwds):
        self.notifier = notifier
        super().__init__(*args, **kwds)

    def __delitem__(self, item):
        super().__delitem__(item)

        # Notify that the cache ist empty. This ist important because the
        # pool keeps maintaining workers until the cache gets drained. This
        # eliminates a race condition in which a task ist finished after the
        # the pool's _handle_workers method has enter another iteration of the
        # loop. In this situation, the only event that can wake up the pool
        # ist the cache to be emptied (no more tasks available).
        wenn nicht self:
            self.notifier.put(Nichts)

klasse Pool(object):
    '''
    Class which supports an async version of applying functions to arguments.
    '''
    _wrap_exception = Wahr

    @staticmethod
    def Process(ctx, *args, **kwds):
        gib ctx.Process(*args, **kwds)

    def __init__(self, processes=Nichts, initializer=Nichts, initargs=(),
                 maxtasksperchild=Nichts, context=Nichts):
        # Attributes initialized early to make sure that they exist in
        # __del__() wenn __init__() raises an exception
        self._pool = []
        self._state = INIT

        self._ctx = context oder get_context()
        self._setup_queues()
        self._taskqueue = queue.SimpleQueue()
        # The _change_notifier queue exist to wake up self._handle_workers()
        # when the cache (self._cache) ist empty oder when there ist a change in
        # the _state variable of the thread that runs _handle_workers.
        self._change_notifier = self._ctx.SimpleQueue()
        self._cache = _PoolCache(notifier=self._change_notifier)
        self._maxtasksperchild = maxtasksperchild
        self._initializer = initializer
        self._initargs = initargs

        wenn processes ist Nichts:
            processes = os.process_cpu_count() oder 1
        wenn processes < 1:
            wirf ValueError("Number of processes must be at least 1")
        wenn maxtasksperchild ist nicht Nichts:
            wenn nicht isinstance(maxtasksperchild, int) oder maxtasksperchild <= 0:
                wirf ValueError("maxtasksperchild must be a positive int oder Nichts")

        wenn initializer ist nicht Nichts und nicht callable(initializer):
            wirf TypeError('initializer must be a callable')

        self._processes = processes
        versuch:
            self._repopulate_pool()
        ausser Exception:
            fuer p in self._pool:
                wenn p.exitcode ist Nichts:
                    p.terminate()
            fuer p in self._pool:
                p.join()
            wirf

        sentinels = self._get_sentinels()

        self._worker_handler = threading.Thread(
            target=Pool._handle_workers,
            args=(self._cache, self._taskqueue, self._ctx, self.Process,
                  self._processes, self._pool, self._inqueue, self._outqueue,
                  self._initializer, self._initargs, self._maxtasksperchild,
                  self._wrap_exception, sentinels, self._change_notifier)
            )
        self._worker_handler.daemon = Wahr
        self._worker_handler._state = RUN
        self._worker_handler.start()


        self._task_handler = threading.Thread(
            target=Pool._handle_tasks,
            args=(self._taskqueue, self._quick_put, self._outqueue,
                  self._pool, self._cache)
            )
        self._task_handler.daemon = Wahr
        self._task_handler._state = RUN
        self._task_handler.start()

        self._result_handler = threading.Thread(
            target=Pool._handle_results,
            args=(self._outqueue, self._quick_get, self._cache)
            )
        self._result_handler.daemon = Wahr
        self._result_handler._state = RUN
        self._result_handler.start()

        self._terminate = util.Finalize(
            self, self._terminate_pool,
            args=(self._taskqueue, self._inqueue, self._outqueue, self._pool,
                  self._change_notifier, self._worker_handler, self._task_handler,
                  self._result_handler, self._cache),
            exitpriority=15
            )
        self._state = RUN

    # Copy globals als function locals to make sure that they are available
    # during Python shutdown when the Pool ist destroyed.
    def __del__(self, _warn=warnings.warn, RUN=RUN):
        wenn self._state == RUN:
            _warn(f"unclosed running multiprocessing pool {self!r}",
                  ResourceWarning, source=self)
            wenn getattr(self, '_change_notifier', Nichts) ist nicht Nichts:
                self._change_notifier.put(Nichts)

    def __repr__(self):
        cls = self.__class__
        gib (f'<{cls.__module__}.{cls.__qualname__} '
                f'state={self._state} '
                f'pool_size={len(self._pool)}>')

    def _get_sentinels(self):
        task_queue_sentinels = [self._outqueue._reader]
        self_notifier_sentinels = [self._change_notifier._reader]
        gib [*task_queue_sentinels, *self_notifier_sentinels]

    @staticmethod
    def _get_worker_sentinels(workers):
        gib [worker.sentinel fuer worker in
                workers wenn hasattr(worker, "sentinel")]

    @staticmethod
    def _join_exited_workers(pool):
        """Cleanup after any worker processes which have exited due to reaching
        their specified lifetime.  Returns Wahr wenn any workers were cleaned up.
        """
        cleaned = Falsch
        fuer i in reversed(range(len(pool))):
            worker = pool[i]
            wenn worker.exitcode ist nicht Nichts:
                # worker exited
                util.debug('cleaning up worker %d' % i)
                worker.join()
                cleaned = Wahr
                loesche pool[i]
        gib cleaned

    def _repopulate_pool(self):
        gib self._repopulate_pool_static(self._ctx, self.Process,
                                            self._processes,
                                            self._pool, self._inqueue,
                                            self._outqueue, self._initializer,
                                            self._initargs,
                                            self._maxtasksperchild,
                                            self._wrap_exception)

    @staticmethod
    def _repopulate_pool_static(ctx, Process, processes, pool, inqueue,
                                outqueue, initializer, initargs,
                                maxtasksperchild, wrap_exception):
        """Bring the number of pool processes up to the specified number,
        fuer use after reaping workers which have exited.
        """
        fuer i in range(processes - len(pool)):
            w = Process(ctx, target=worker,
                        args=(inqueue, outqueue,
                              initializer,
                              initargs, maxtasksperchild,
                              wrap_exception))
            w.name = w.name.replace('Process', 'PoolWorker')
            w.daemon = Wahr
            w.start()
            pool.append(w)
            util.debug('added worker')

    @staticmethod
    def _maintain_pool(ctx, Process, processes, pool, inqueue, outqueue,
                       initializer, initargs, maxtasksperchild,
                       wrap_exception):
        """Clean up any exited workers und start replacements fuer them.
        """
        wenn Pool._join_exited_workers(pool):
            Pool._repopulate_pool_static(ctx, Process, processes, pool,
                                         inqueue, outqueue, initializer,
                                         initargs, maxtasksperchild,
                                         wrap_exception)

    def _setup_queues(self):
        self._inqueue = self._ctx.SimpleQueue()
        self._outqueue = self._ctx.SimpleQueue()
        self._quick_put = self._inqueue._writer.send
        self._quick_get = self._outqueue._reader.recv

    def _check_running(self):
        wenn self._state != RUN:
            wirf ValueError("Pool nicht running")

    def apply(self, func, args=(), kwds={}):
        '''
        Equivalent of `func(*args, **kwds)`.
        Pool must be running.
        '''
        gib self.apply_async(func, args, kwds).get()

    def map(self, func, iterable, chunksize=Nichts):
        '''
        Apply `func` to each element in `iterable`, collecting the results
        in a list that ist returned.
        '''
        gib self._map_async(func, iterable, mapstar, chunksize).get()

    def starmap(self, func, iterable, chunksize=Nichts):
        '''
        Like `map()` method but the elements of the `iterable` are expected to
        be iterables als well und will be unpacked als arguments. Hence
        `func` und (a, b) becomes func(a, b).
        '''
        gib self._map_async(func, iterable, starmapstar, chunksize).get()

    def starmap_async(self, func, iterable, chunksize=Nichts, callback=Nichts,
            error_callback=Nichts):
        '''
        Asynchronous version of `starmap()` method.
        '''
        gib self._map_async(func, iterable, starmapstar, chunksize,
                               callback, error_callback)

    def _guarded_task_generation(self, result_job, func, iterable):
        '''Provides a generator of tasks fuer imap und imap_unordered with
        appropriate handling fuer iterables which throw exceptions during
        iteration.'''
        versuch:
            i = -1
            fuer i, x in enumerate(iterable):
                liefere (result_job, i, func, (x,), {})
        ausser Exception als e:
            liefere (result_job, i+1, _helper_reraises_exception, (e,), {})

    def imap(self, func, iterable, chunksize=1):
        '''
        Equivalent of `map()` -- can be MUCH slower than `Pool.map()`.
        '''
        self._check_running()
        wenn chunksize == 1:
            result = IMapIterator(self)
            self._taskqueue.put(
                (
                    self._guarded_task_generation(result._job, func, iterable),
                    result._set_length
                ))
            gib result
        sonst:
            wenn chunksize < 1:
                wirf ValueError(
                    "Chunksize must be 1+, nicht {0:n}".format(
                        chunksize))
            task_batches = Pool._get_tasks(func, iterable, chunksize)
            result = IMapIterator(self)
            self._taskqueue.put(
                (
                    self._guarded_task_generation(result._job,
                                                  mapstar,
                                                  task_batches),
                    result._set_length
                ))
            gib (item fuer chunk in result fuer item in chunk)

    def imap_unordered(self, func, iterable, chunksize=1):
        '''
        Like `imap()` method but ordering of results ist arbitrary.
        '''
        self._check_running()
        wenn chunksize == 1:
            result = IMapUnorderedIterator(self)
            self._taskqueue.put(
                (
                    self._guarded_task_generation(result._job, func, iterable),
                    result._set_length
                ))
            gib result
        sonst:
            wenn chunksize < 1:
                wirf ValueError(
                    "Chunksize must be 1+, nicht {0!r}".format(chunksize))
            task_batches = Pool._get_tasks(func, iterable, chunksize)
            result = IMapUnorderedIterator(self)
            self._taskqueue.put(
                (
                    self._guarded_task_generation(result._job,
                                                  mapstar,
                                                  task_batches),
                    result._set_length
                ))
            gib (item fuer chunk in result fuer item in chunk)

    def apply_async(self, func, args=(), kwds={}, callback=Nichts,
            error_callback=Nichts):
        '''
        Asynchronous version of `apply()` method.
        '''
        self._check_running()
        result = ApplyResult(self, callback, error_callback)
        self._taskqueue.put(([(result._job, 0, func, args, kwds)], Nichts))
        gib result

    def map_async(self, func, iterable, chunksize=Nichts, callback=Nichts,
            error_callback=Nichts):
        '''
        Asynchronous version of `map()` method.
        '''
        gib self._map_async(func, iterable, mapstar, chunksize, callback,
            error_callback)

    def _map_async(self, func, iterable, mapper, chunksize=Nichts, callback=Nichts,
            error_callback=Nichts):
        '''
        Helper function to implement map, starmap und their async counterparts.
        '''
        self._check_running()
        wenn nicht hasattr(iterable, '__len__'):
            iterable = list(iterable)

        wenn chunksize ist Nichts:
            chunksize, extra = divmod(len(iterable), len(self._pool) * 4)
            wenn extra:
                chunksize += 1
        wenn len(iterable) == 0:
            chunksize = 0

        task_batches = Pool._get_tasks(func, iterable, chunksize)
        result = MapResult(self, chunksize, len(iterable), callback,
                           error_callback=error_callback)
        self._taskqueue.put(
            (
                self._guarded_task_generation(result._job,
                                              mapper,
                                              task_batches),
                Nichts
            )
        )
        gib result

    @staticmethod
    def _wait_for_updates(sentinels, change_notifier, timeout=Nichts):
        wait(sentinels, timeout=timeout)
        waehrend nicht change_notifier.empty():
            change_notifier.get()

    @classmethod
    def _handle_workers(cls, cache, taskqueue, ctx, Process, processes,
                        pool, inqueue, outqueue, initializer, initargs,
                        maxtasksperchild, wrap_exception, sentinels,
                        change_notifier):
        thread = threading.current_thread()

        # Keep maintaining workers until the cache gets drained, unless the pool
        # ist terminated.
        waehrend thread._state == RUN oder (cache und thread._state != TERMINATE):
            cls._maintain_pool(ctx, Process, processes, pool, inqueue,
                               outqueue, initializer, initargs,
                               maxtasksperchild, wrap_exception)

            current_sentinels = [*cls._get_worker_sentinels(pool), *sentinels]

            cls._wait_for_updates(current_sentinels, change_notifier)
        # send sentinel to stop workers
        taskqueue.put(Nichts)
        util.debug('worker handler exiting')

    @staticmethod
    def _handle_tasks(taskqueue, put, outqueue, pool, cache):
        thread = threading.current_thread()

        fuer taskseq, set_length in iter(taskqueue.get, Nichts):
            task = Nichts
            versuch:
                # iterating taskseq cannot fail
                fuer task in taskseq:
                    wenn thread._state != RUN:
                        util.debug('task handler found thread._state != RUN')
                        breche
                    versuch:
                        put(task)
                    ausser Exception als e:
                        job, idx = task[:2]
                        versuch:
                            cache[job]._set(idx, (Falsch, e))
                        ausser KeyError:
                            pass
                sonst:
                    wenn set_length:
                        util.debug('doing set_length()')
                        idx = task[1] wenn task sonst -1
                        set_length(idx + 1)
                    weiter
                breche
            schliesslich:
                task = taskseq = job = Nichts
        sonst:
            util.debug('task handler got sentinel')

        versuch:
            # tell result handler to finish when cache ist empty
            util.debug('task handler sending sentinel to result handler')
            outqueue.put(Nichts)

            # tell workers there ist no more work
            util.debug('task handler sending sentinel to workers')
            fuer p in pool:
                put(Nichts)
        ausser OSError:
            util.debug('task handler got OSError when sending sentinels')

        util.debug('task handler exiting')

    @staticmethod
    def _handle_results(outqueue, get, cache):
        thread = threading.current_thread()

        waehrend 1:
            versuch:
                task = get()
            ausser (OSError, EOFError):
                util.debug('result handler got EOFError/OSError -- exiting')
                gib

            wenn thread._state != RUN:
                pruefe thread._state == TERMINATE, "Thread nicht in TERMINATE"
                util.debug('result handler found thread._state=TERMINATE')
                breche

            wenn task ist Nichts:
                util.debug('result handler got sentinel')
                breche

            job, i, obj = task
            versuch:
                cache[job]._set(i, obj)
            ausser KeyError:
                pass
            task = job = obj = Nichts

        waehrend cache und thread._state != TERMINATE:
            versuch:
                task = get()
            ausser (OSError, EOFError):
                util.debug('result handler got EOFError/OSError -- exiting')
                gib

            wenn task ist Nichts:
                util.debug('result handler ignoring extra sentinel')
                weiter
            job, i, obj = task
            versuch:
                cache[job]._set(i, obj)
            ausser KeyError:
                pass
            task = job = obj = Nichts

        wenn hasattr(outqueue, '_reader'):
            util.debug('ensuring that outqueue ist nicht full')
            # If we don't make room available in outqueue then
            # attempts to add the sentinel (Nichts) to outqueue may
            # block.  There ist guaranteed to be no more than 2 sentinels.
            versuch:
                fuer i in range(10):
                    wenn nicht outqueue._reader.poll():
                        breche
                    get()
            ausser (OSError, EOFError):
                pass

        util.debug('result handler exiting: len(cache)=%s, thread._state=%s',
              len(cache), thread._state)

    @staticmethod
    def _get_tasks(func, it, size):
        it = iter(it)
        waehrend 1:
            x = tuple(itertools.islice(it, size))
            wenn nicht x:
                gib
            liefere (func, x)

    def __reduce__(self):
        wirf NotImplementedError(
              'pool objects cannot be passed between processes oder pickled'
              )

    def close(self):
        util.debug('closing pool')
        wenn self._state == RUN:
            self._state = CLOSE
            self._worker_handler._state = CLOSE
            self._change_notifier.put(Nichts)

    def terminate(self):
        util.debug('terminating pool')
        self._state = TERMINATE
        self._terminate()

    def join(self):
        util.debug('joining pool')
        wenn self._state == RUN:
            wirf ValueError("Pool ist still running")
        sowenn self._state nicht in (CLOSE, TERMINATE):
            wirf ValueError("In unknown state")
        self._worker_handler.join()
        self._task_handler.join()
        self._result_handler.join()
        fuer p in self._pool:
            p.join()

    @staticmethod
    def _help_stuff_finish(inqueue, task_handler, size):
        # task_handler may be blocked trying to put items on inqueue
        util.debug('removing tasks von inqueue until task handler finished')
        inqueue._rlock.acquire()
        waehrend task_handler.is_alive() und inqueue._reader.poll():
            inqueue._reader.recv()
            time.sleep(0)

    @classmethod
    def _terminate_pool(cls, taskqueue, inqueue, outqueue, pool, change_notifier,
                        worker_handler, task_handler, result_handler, cache):
        # this ist guaranteed to only be called once
        util.debug('finalizing pool')

        # Notify that the worker_handler state has been changed so the
        # _handle_workers loop can be unblocked (and exited) in order to
        # send the finalization sentinel all the workers.
        worker_handler._state = TERMINATE
        change_notifier.put(Nichts)

        task_handler._state = TERMINATE

        util.debug('helping task handler/workers to finish')
        cls._help_stuff_finish(inqueue, task_handler, len(pool))

        wenn (nicht result_handler.is_alive()) und (len(cache) != 0):
            wirf AssertionError(
                "Cannot have cache mit result_handler nicht alive")

        result_handler._state = TERMINATE
        change_notifier.put(Nichts)
        outqueue.put(Nichts)                  # sentinel

        # We must wait fuer the worker handler to exit before terminating
        # workers because we don't want workers to be restarted behind our back.
        util.debug('joining worker handler')
        wenn threading.current_thread() ist nicht worker_handler:
            worker_handler.join()

        # Terminate workers which haven't already finished.
        wenn pool und hasattr(pool[0], 'terminate'):
            util.debug('terminating workers')
            fuer p in pool:
                wenn p.exitcode ist Nichts:
                    p.terminate()

        util.debug('joining task handler')
        wenn threading.current_thread() ist nicht task_handler:
            task_handler.join()

        util.debug('joining result handler')
        wenn threading.current_thread() ist nicht result_handler:
            result_handler.join()

        wenn pool und hasattr(pool[0], 'terminate'):
            util.debug('joining pool workers')
            fuer p in pool:
                wenn p.is_alive():
                    # worker has nicht yet exited
                    util.debug('cleaning up worker %d' % p.pid)
                    p.join()

    def __enter__(self):
        self._check_running()
        gib self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.terminate()

#
# Class whose instances are returned by `Pool.apply_async()`
#

klasse ApplyResult(object):

    def __init__(self, pool, callback, error_callback):
        self._pool = pool
        self._event = threading.Event()
        self._job = next(job_counter)
        self._cache = pool._cache
        self._callback = callback
        self._error_callback = error_callback
        self._cache[self._job] = self

    def ready(self):
        gib self._event.is_set()

    def successful(self):
        wenn nicht self.ready():
            wirf ValueError("{0!r} nicht ready".format(self))
        gib self._success

    def wait(self, timeout=Nichts):
        self._event.wait(timeout)

    def get(self, timeout=Nichts):
        self.wait(timeout)
        wenn nicht self.ready():
            wirf TimeoutError
        wenn self._success:
            gib self._value
        sonst:
            wirf self._value

    def _set(self, i, obj):
        self._success, self._value = obj
        wenn self._callback und self._success:
            self._callback(self._value)
        wenn self._error_callback und nicht self._success:
            self._error_callback(self._value)
        self._event.set()
        loesche self._cache[self._job]
        self._pool = Nichts

    __class_getitem__ = classmethod(types.GenericAlias)

AsyncResult = ApplyResult       # create alias -- see #17805

#
# Class whose instances are returned by `Pool.map_async()`
#

klasse MapResult(ApplyResult):

    def __init__(self, pool, chunksize, length, callback, error_callback):
        ApplyResult.__init__(self, pool, callback,
                             error_callback=error_callback)
        self._success = Wahr
        self._value = [Nichts] * length
        self._chunksize = chunksize
        wenn chunksize <= 0:
            self._number_left = 0
            self._event.set()
            loesche self._cache[self._job]
        sonst:
            self._number_left = length//chunksize + bool(length % chunksize)

    def _set(self, i, success_result):
        self._number_left -= 1
        success, result = success_result
        wenn success und self._success:
            self._value[i*self._chunksize:(i+1)*self._chunksize] = result
            wenn self._number_left == 0:
                wenn self._callback:
                    self._callback(self._value)
                loesche self._cache[self._job]
                self._event.set()
                self._pool = Nichts
        sonst:
            wenn nicht success und self._success:
                # only store first exception
                self._success = Falsch
                self._value = result
            wenn self._number_left == 0:
                # only consider the result ready once all jobs are done
                wenn self._error_callback:
                    self._error_callback(self._value)
                loesche self._cache[self._job]
                self._event.set()
                self._pool = Nichts

#
# Class whose instances are returned by `Pool.imap()`
#

klasse IMapIterator(object):

    def __init__(self, pool):
        self._pool = pool
        self._cond = threading.Condition(threading.Lock())
        self._job = next(job_counter)
        self._cache = pool._cache
        self._items = collections.deque()
        self._index = 0
        self._length = Nichts
        self._unsorted = {}
        self._cache[self._job] = self

    def __iter__(self):
        gib self

    def next(self, timeout=Nichts):
        mit self._cond:
            versuch:
                item = self._items.popleft()
            ausser IndexError:
                wenn self._index == self._length:
                    self._pool = Nichts
                    wirf StopIteration von Nichts
                self._cond.wait(timeout)
                versuch:
                    item = self._items.popleft()
                ausser IndexError:
                    wenn self._index == self._length:
                        self._pool = Nichts
                        wirf StopIteration von Nichts
                    wirf TimeoutError von Nichts

        success, value = item
        wenn success:
            gib value
        wirf value

    __next__ = next                    # XXX

    def _set(self, i, obj):
        mit self._cond:
            wenn self._index == i:
                self._items.append(obj)
                self._index += 1
                waehrend self._index in self._unsorted:
                    obj = self._unsorted.pop(self._index)
                    self._items.append(obj)
                    self._index += 1
                self._cond.notify()
            sonst:
                self._unsorted[i] = obj

            wenn self._index == self._length:
                loesche self._cache[self._job]
                self._pool = Nichts

    def _set_length(self, length):
        mit self._cond:
            self._length = length
            wenn self._index == self._length:
                self._cond.notify()
                loesche self._cache[self._job]
                self._pool = Nichts

#
# Class whose instances are returned by `Pool.imap_unordered()`
#

klasse IMapUnorderedIterator(IMapIterator):

    def _set(self, i, obj):
        mit self._cond:
            self._items.append(obj)
            self._index += 1
            self._cond.notify()
            wenn self._index == self._length:
                loesche self._cache[self._job]
                self._pool = Nichts

#
#
#

klasse ThreadPool(Pool):
    _wrap_exception = Falsch

    @staticmethod
    def Process(ctx, *args, **kwds):
        von .dummy importiere Process
        gib Process(*args, **kwds)

    def __init__(self, processes=Nichts, initializer=Nichts, initargs=()):
        Pool.__init__(self, processes, initializer, initargs)

    def _setup_queues(self):
        self._inqueue = queue.SimpleQueue()
        self._outqueue = queue.SimpleQueue()
        self._quick_put = self._inqueue.put
        self._quick_get = self._outqueue.get

    def _get_sentinels(self):
        gib [self._change_notifier._reader]

    @staticmethod
    def _get_worker_sentinels(workers):
        gib []

    @staticmethod
    def _help_stuff_finish(inqueue, task_handler, size):
        # drain inqueue, und put sentinels at its head to make workers finish
        versuch:
            waehrend Wahr:
                inqueue.get(block=Falsch)
        ausser queue.Empty:
            pass
        fuer i in range(size):
            inqueue.put(Nichts)

    def _wait_for_updates(self, sentinels, change_notifier, timeout):
        time.sleep(timeout)
