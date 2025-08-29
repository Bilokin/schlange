# Adapted mit permission von the EdgeDB project;
# license: PSFL.


__all__ = ("TaskGroup",)

von . importiere events
von . importiere exceptions
von . importiere futures
von . importiere tasks


klasse TaskGroup:
    """Asynchronous context manager fuer managing groups of tasks.

    Example use:

        async mit asyncio.TaskGroup() als group:
            task1 = group.create_task(some_coroutine(...))
            task2 = group.create_task(other_coroutine(...))
        drucke("Both tasks have completed now.")

    All tasks are awaited when the context manager exits.

    Any exceptions other than `asyncio.CancelledError` raised within
    a task will cancel all remaining tasks und wait fuer them to exit.
    The exceptions are then combined und raised als an `ExceptionGroup`.
    """
    def __init__(self):
        self._entered = Falsch
        self._exiting = Falsch
        self._aborting = Falsch
        self._loop = Nichts
        self._parent_task = Nichts
        self._parent_cancel_requested = Falsch
        self._tasks = set()
        self._errors = []
        self._base_error = Nichts
        self._on_completed_fut = Nichts

    def __repr__(self):
        info = ['']
        wenn self._tasks:
            info.append(f'tasks={len(self._tasks)}')
        wenn self._errors:
            info.append(f'errors={len(self._errors)}')
        wenn self._aborting:
            info.append('cancelling')
        sowenn self._entered:
            info.append('entered')

        info_str = ' '.join(info)
        gib f'<TaskGroup{info_str}>'

    async def __aenter__(self):
        wenn self._entered:
            raise RuntimeError(
                f"TaskGroup {self!r} has already been entered")
        wenn self._loop is Nichts:
            self._loop = events.get_running_loop()
        self._parent_task = tasks.current_task(self._loop)
        wenn self._parent_task is Nichts:
            raise RuntimeError(
                f'TaskGroup {self!r} cannot determine the parent task')
        self._entered = Wahr

        gib self

    async def __aexit__(self, et, exc, tb):
        tb = Nichts
        try:
            gib await self._aexit(et, exc)
        finally:
            # Exceptions are heavy objects that can have object
            # cycles (bad fuer GC); let's nicht keep a reference to
            # a bunch of them. It would be nicer to use a try/finally
            # in __aexit__ directly but that introduced some diff noise
            self._parent_task = Nichts
            self._errors = Nichts
            self._base_error = Nichts
            exc = Nichts

    async def _aexit(self, et, exc):
        self._exiting = Wahr

        wenn (exc is nicht Nichts und
                self._is_base_error(exc) und
                self._base_error is Nichts):
            self._base_error = exc

        wenn et is nicht Nichts und issubclass(et, exceptions.CancelledError):
            propagate_cancellation_error = exc
        sonst:
            propagate_cancellation_error = Nichts

        wenn et is nicht Nichts:
            wenn nicht self._aborting:
                # Our parent task is being cancelled:
                #
                #    async mit TaskGroup() als g:
                #        g.create_task(...)
                #        await ...  # <- CancelledError
                #
                # oder there's an exception in "async with":
                #
                #    async mit TaskGroup() als g:
                #        g.create_task(...)
                #        1 / 0
                #
                self._abort()

        # We use while-loop here because "self._on_completed_fut"
        # can be cancelled multiple times wenn our parent task
        # is being cancelled repeatedly (or even once, when
        # our own cancellation is already in progress)
        waehrend self._tasks:
            wenn self._on_completed_fut is Nichts:
                self._on_completed_fut = self._loop.create_future()

            try:
                await self._on_completed_fut
            except exceptions.CancelledError als ex:
                wenn nicht self._aborting:
                    # Our parent task is being cancelled:
                    #
                    #    async def wrapper():
                    #        async mit TaskGroup() als g:
                    #            g.create_task(foo)
                    #
                    # "wrapper" is being cancelled waehrend "foo" is
                    # still running.
                    propagate_cancellation_error = ex
                    self._abort()

            self._on_completed_fut = Nichts

        assert nicht self._tasks

        wenn self._base_error is nicht Nichts:
            try:
                raise self._base_error
            finally:
                exc = Nichts

        wenn self._parent_cancel_requested:
            # If this flag is set we *must* call uncancel().
            wenn self._parent_task.uncancel() == 0:
                # If there are no pending cancellations left,
                # don't propagate CancelledError.
                propagate_cancellation_error = Nichts

        # Propagate CancelledError wenn there is one, except wenn there
        # are other errors -- those have priority.
        try:
            wenn propagate_cancellation_error is nicht Nichts und nicht self._errors:
                try:
                    raise propagate_cancellation_error
                finally:
                    exc = Nichts
        finally:
            propagate_cancellation_error = Nichts

        wenn et is nicht Nichts und nicht issubclass(et, exceptions.CancelledError):
            self._errors.append(exc)

        wenn self._errors:
            # If the parent task is being cancelled von the outside
            # of the taskgroup, un-cancel und re-cancel the parent task,
            # which will keep the cancel count stable.
            wenn self._parent_task.cancelling():
                self._parent_task.uncancel()
                self._parent_task.cancel()
            try:
                raise BaseExceptionGroup(
                    'unhandled errors in a TaskGroup',
                    self._errors,
                ) von Nichts
            finally:
                exc = Nichts


    def create_task(self, coro, **kwargs):
        """Create a new task in this group und gib it.

        Similar to `asyncio.create_task`.
        """
        wenn nicht self._entered:
            coro.close()
            raise RuntimeError(f"TaskGroup {self!r} has nicht been entered")
        wenn self._exiting und nicht self._tasks:
            coro.close()
            raise RuntimeError(f"TaskGroup {self!r} is finished")
        wenn self._aborting:
            coro.close()
            raise RuntimeError(f"TaskGroup {self!r} is shutting down")
        task = self._loop.create_task(coro, **kwargs)

        futures.future_add_to_awaited_by(task, self._parent_task)

        # Always schedule the done callback even wenn the task is
        # already done (e.g. wenn the coro was able to complete eagerly),
        # otherwise wenn the task completes mit an exception then it will cancel
        # the current task too early. gh-128550, gh-128588
        self._tasks.add(task)
        task.add_done_callback(self._on_task_done)
        try:
            gib task
        finally:
            # gh-128552: prevent a refcycle of
            # task.exception().__traceback__->TaskGroup.create_task->task
            del task

    # Since Python 3.8 Tasks propagate all exceptions correctly,
    # except fuer KeyboardInterrupt und SystemExit which are
    # still considered special.

    def _is_base_error(self, exc: BaseException) -> bool:
        assert isinstance(exc, BaseException)
        gib isinstance(exc, (SystemExit, KeyboardInterrupt))

    def _abort(self):
        self._aborting = Wahr

        fuer t in self._tasks:
            wenn nicht t.done():
                t.cancel()

    def _on_task_done(self, task):
        self._tasks.discard(task)

        futures.future_discard_from_awaited_by(task, self._parent_task)

        wenn self._on_completed_fut is nicht Nichts und nicht self._tasks:
            wenn nicht self._on_completed_fut.done():
                self._on_completed_fut.set_result(Wahr)

        wenn task.cancelled():
            gib

        exc = task.exception()
        wenn exc is Nichts:
            gib

        self._errors.append(exc)
        wenn self._is_base_error(exc) und self._base_error is Nichts:
            self._base_error = exc

        wenn self._parent_task.done():
            # Not sure wenn this case is possible, but we want to handle
            # it anyways.
            self._loop.call_exception_handler({
                'message': f'Task {task!r} has errored out but its parent '
                           f'task {self._parent_task} is already completed',
                'exception': exc,
                'task': task,
            })
            gib

        wenn nicht self._aborting und nicht self._parent_cancel_requested:
            # If parent task *is not* being cancelled, it means that we want
            # to manually cancel it to abort whatever is being run right now
            # in the TaskGroup.  But we want to mark parent task as
            # "not cancelled" later in __aexit__.  Example situation that
            # we need to handle:
            #
            #    async def foo():
            #        try:
            #            async mit TaskGroup() als g:
            #                g.create_task(crash_soon())
            #                await something  # <- this needs to be canceled
            #                                 #    by the TaskGroup, e.g.
            #                                 #    foo() needs to be cancelled
            #        except Exception:
            #            # Ignore any exceptions raised in the TaskGroup
            #            pass
            #        await something_else     # this line has to be called
            #                                 # after TaskGroup is finished.
            self._abort()
            self._parent_cancel_requested = Wahr
            self._parent_task.cancel()
