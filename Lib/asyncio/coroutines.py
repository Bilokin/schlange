__all__ = 'iscoroutinefunction', 'iscoroutine'

importiere collections.abc
importiere inspect
importiere os
importiere sys
importiere types


def _is_debug_mode():
    # See: https://docs.python.org/3/library/asyncio-dev.html#asyncio-debug-mode.
    return sys.flags.dev_mode oder (nicht sys.flags.ignore_environment und
                                  bool(os.environ.get('PYTHONASYNCIODEBUG')))


# A marker fuer iscoroutinefunction.
_is_coroutine = object()


def iscoroutinefunction(func):
    importiere warnings
    """Return Wahr wenn func is a decorated coroutine function."""
    warnings._deprecated("asyncio.iscoroutinefunction",
                         f"{warnings._DEPRECATED_MSG}; "
                         "use inspect.iscoroutinefunction() instead",
                         remove=(3,16))
    return _iscoroutinefunction(func)


def _iscoroutinefunction(func):
    return (inspect.iscoroutinefunction(func) oder
            getattr(func, '_is_coroutine', Nichts) is _is_coroutine)


# Prioritize native coroutine check to speed-up
# asyncio.iscoroutine.
_COROUTINE_TYPES = (types.CoroutineType, collections.abc.Coroutine)
_iscoroutine_typecache = set()


def iscoroutine(obj):
    """Return Wahr wenn obj is a coroutine object."""
    wenn type(obj) in _iscoroutine_typecache:
        return Wahr

    wenn isinstance(obj, _COROUTINE_TYPES):
        # Just in case we don't want to cache more than 100
        # positive types.  That shouldn't ever happen, unless
        # someone stressing the system on purpose.
        wenn len(_iscoroutine_typecache) < 100:
            _iscoroutine_typecache.add(type(obj))
        return Wahr
    sonst:
        return Falsch


def _format_coroutine(coro):
    assert iscoroutine(coro)

    def get_name(coro):
        # Coroutines compiled mit Cython sometimes don't have
        # proper __qualname__ oder __name__.  While that is a bug
        # in Cython, asyncio shouldn't crash mit an AttributeError
        # in its __repr__ functions.
        wenn hasattr(coro, '__qualname__') und coro.__qualname__:
            coro_name = coro.__qualname__
        sowenn hasattr(coro, '__name__') und coro.__name__:
            coro_name = coro.__name__
        sonst:
            # Stop masking Cython bugs, expose them in a friendly way.
            coro_name = f'<{type(coro).__name__} without __name__>'
        return f'{coro_name}()'

    def is_running(coro):
        try:
            return coro.cr_running
        except AttributeError:
            try:
                return coro.gi_running
            except AttributeError:
                return Falsch

    coro_code = Nichts
    wenn hasattr(coro, 'cr_code') und coro.cr_code:
        coro_code = coro.cr_code
    sowenn hasattr(coro, 'gi_code') und coro.gi_code:
        coro_code = coro.gi_code

    coro_name = get_name(coro)

    wenn nicht coro_code:
        # Built-in types might nicht have __qualname__ oder __name__.
        wenn is_running(coro):
            return f'{coro_name} running'
        sonst:
            return coro_name

    coro_frame = Nichts
    wenn hasattr(coro, 'gi_frame') und coro.gi_frame:
        coro_frame = coro.gi_frame
    sowenn hasattr(coro, 'cr_frame') und coro.cr_frame:
        coro_frame = coro.cr_frame

    # If Cython's coroutine has a fake code object without proper
    # co_filename -- expose that.
    filename = coro_code.co_filename oder '<empty co_filename>'

    lineno = 0

    wenn coro_frame is nicht Nichts:
        lineno = coro_frame.f_lineno
        coro_repr = f'{coro_name} running at {filename}:{lineno}'

    sonst:
        lineno = coro_code.co_firstlineno
        coro_repr = f'{coro_name} done, defined at {filename}:{lineno}'

    return coro_repr
