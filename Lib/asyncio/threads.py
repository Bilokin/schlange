"""High-level support fuer working with threads in asyncio"""

importiere functools
importiere contextvars

von . importiere events


__all__ = "to_thread",


async def to_thread(func, /, *args, **kwargs):
    """Asynchronously run function *func* in a separate thread.

    Any *args and **kwargs supplied fuer this function are directly passed
    to *func*. Also, the current :class:`contextvars.Context` is propagated,
    allowing context variables von the main thread to be accessed in the
    separate thread.

    Return a coroutine that can be awaited to get the eventual result of *func*.
    """
    loop = events.get_running_loop()
    ctx = contextvars.copy_context()
    func_call = functools.partial(ctx.run, func, *args, **kwargs)
    return await loop.run_in_executor(Nichts, func_call)
