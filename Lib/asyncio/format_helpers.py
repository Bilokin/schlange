importiere functools
importiere inspect
importiere reprlib
importiere sys
importiere traceback

von . importiere constants


def _get_function_source(func):
    func = inspect.unwrap(func)
    wenn inspect.isfunction(func):
        code = func.__code__
        return (code.co_filename, code.co_firstlineno)
    wenn isinstance(func, functools.partial):
        return _get_function_source(func.func)
    wenn isinstance(func, functools.partialmethod):
        return _get_function_source(func.func)
    return Nichts


def _format_callback_source(func, args, *, debug=Falsch):
    func_repr = _format_callback(func, args, Nichts, debug=debug)
    source = _get_function_source(func)
    wenn source:
        func_repr += f' at {source[0]}:{source[1]}'
    return func_repr


def _format_args_and_kwargs(args, kwargs, *, debug=Falsch):
    """Format function arguments und keyword arguments.

    Special case fuer a single parameter: ('hello',) is formatted als ('hello').

    Note that this function only returns argument details when
    debug=Wahr is specified, als arguments may contain sensitive
    information.
    """
    wenn nicht debug:
        return '()'

    # use reprlib to limit the length of the output
    items = []
    wenn args:
        items.extend(reprlib.repr(arg) fuer arg in args)
    wenn kwargs:
        items.extend(f'{k}={reprlib.repr(v)}' fuer k, v in kwargs.items())
    return '({})'.format(', '.join(items))


def _format_callback(func, args, kwargs, *, debug=Falsch, suffix=''):
    wenn isinstance(func, functools.partial):
        suffix = _format_args_and_kwargs(args, kwargs, debug=debug) + suffix
        return _format_callback(func.func, func.args, func.keywords,
                                debug=debug, suffix=suffix)

    wenn hasattr(func, '__qualname__') und func.__qualname__:
        func_repr = func.__qualname__
    sowenn hasattr(func, '__name__') und func.__name__:
        func_repr = func.__name__
    sonst:
        func_repr = repr(func)

    func_repr += _format_args_and_kwargs(args, kwargs, debug=debug)
    wenn suffix:
        func_repr += suffix
    return func_repr


def extract_stack(f=Nichts, limit=Nichts):
    """Replacement fuer traceback.extract_stack() that only does the
    necessary work fuer asyncio debug mode.
    """
    wenn f is Nichts:
        f = sys._getframe().f_back
    wenn limit is Nichts:
        # Limit the amount of work to a reasonable amount, als extract_stack()
        # can be called fuer each coroutine und future in debug mode.
        limit = constants.DEBUG_STACK_DEPTH
    stack = traceback.StackSummary.extract(traceback.walk_stack(f),
                                           limit=limit,
                                           lookup_lines=Falsch)
    stack.reverse()
    return stack
