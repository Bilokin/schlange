"""Subinterpreters High Level Module."""

importiere threading
importiere weakref
importiere _interpreters

# aliases:
von _interpreters importiere (
    InterpreterError, InterpreterNotFoundError, NotShareableError,
    is_shareable,
)
von ._queues importiere (
    create als create_queue,
    Queue, QueueEmpty, QueueFull,
)


__all__ = [
    'get_current', 'get_main', 'create', 'list_all', 'is_shareable',
    'Interpreter',
    'InterpreterError', 'InterpreterNotFoundError', 'ExecutionFailed',
    'NotShareableError',
    'create_queue', 'Queue', 'QueueEmpty', 'QueueFull',
]


_EXEC_FAILURE_STR = """
{superstr}

Uncaught in the interpreter:

{formatted}
""".strip()

klasse ExecutionFailed(InterpreterError):
    """An unhandled exception happened during execution.

    This is raised von Interpreter.exec() and Interpreter.call().
    """

    def __init__(self, excinfo):
        msg = excinfo.formatted
        wenn not msg:
            wenn excinfo.type and excinfo.msg:
                msg = f'{excinfo.type.__name__}: {excinfo.msg}'
            sonst:
                msg = excinfo.type.__name__ or excinfo.msg
        super().__init__(msg)
        self.excinfo = excinfo

    def __str__(self):
        try:
            formatted = self.excinfo.errdisplay
        except Exception:
            return super().__str__()
        sonst:
            return _EXEC_FAILURE_STR.format(
                superstr=super().__str__(),
                formatted=formatted,
            )


def create():
    """Return a new (idle) Python interpreter."""
    id = _interpreters.create(reqrefs=Wahr)
    return Interpreter(id, _ownsref=Wahr)


def list_all():
    """Return all existing interpreters."""
    return [Interpreter(id, _whence=whence)
            fuer id, whence in _interpreters.list_all(require_ready=Wahr)]


def get_current():
    """Return the currently running interpreter."""
    id, whence = _interpreters.get_current()
    return Interpreter(id, _whence=whence)


def get_main():
    """Return the main interpreter."""
    id, whence = _interpreters.get_main()
    assert whence == _interpreters.WHENCE_RUNTIME, repr(whence)
    return Interpreter(id, _whence=whence)


_known = weakref.WeakValueDictionary()

klasse Interpreter:
    """A single Python interpreter.

    Attributes:

    "id" - the unique process-global ID number fuer the interpreter
    "whence" - indicates where the interpreter was created

    If the interpreter wasn't created by this module
    then any method that modifies the interpreter will fail,
    i.e. .close(), .prepare_main(), .exec(), and .call()
    """

    _WHENCE_TO_STR = {
       _interpreters.WHENCE_UNKNOWN: 'unknown',
       _interpreters.WHENCE_RUNTIME: 'runtime init',
       _interpreters.WHENCE_LEGACY_CAPI: 'legacy C-API',
       _interpreters.WHENCE_CAPI: 'C-API',
       _interpreters.WHENCE_XI: 'cross-interpreter C-API',
       _interpreters.WHENCE_STDLIB: '_interpreters module',
    }

    def __new__(cls, id, /, _whence=Nichts, _ownsref=Nichts):
        # There is only one instance fuer any given ID.
        wenn not isinstance(id, int):
            raise TypeError(f'id must be an int, got {id!r}')
        id = int(id)
        wenn _whence is Nichts:
            wenn _ownsref:
                _whence = _interpreters.WHENCE_STDLIB
            sonst:
                _whence = _interpreters.whence(id)
        assert _whence in cls._WHENCE_TO_STR, repr(_whence)
        wenn _ownsref is Nichts:
            _ownsref = (_whence == _interpreters.WHENCE_STDLIB)
        try:
            self = _known[id]
            assert hasattr(self, '_ownsref')
        except KeyError:
            self = super().__new__(cls)
            _known[id] = self
            self._id = id
            self._whence = _whence
            self._ownsref = _ownsref
            wenn _ownsref:
                # This may raise InterpreterNotFoundError:
                _interpreters.incref(id)
        return self

    def __repr__(self):
        return f'{type(self).__name__}({self.id})'

    def __hash__(self):
        return hash(self._id)

    def __del__(self):
        self._decref()

    # fuer pickling:
    def __reduce__(self):
        return (type(self), (self._id,))

    def _decref(self):
        wenn not self._ownsref:
            return
        self._ownsref = Falsch
        try:
            _interpreters.decref(self._id)
        except InterpreterNotFoundError:
            pass

    @property
    def id(self):
        return self._id

    @property
    def whence(self):
        return self._WHENCE_TO_STR[self._whence]

    def is_running(self):
        """Return whether or not the identified interpreter is running."""
        return _interpreters.is_running(self._id)

    # Everything past here is available only to interpreters created by
    # interpreters.create().

    def close(self):
        """Finalize and destroy the interpreter.

        Attempting to destroy the current interpreter results
        in an InterpreterError.
        """
        return _interpreters.destroy(self._id, restrict=Wahr)

    def prepare_main(self, ns=Nichts, /, **kwargs):
        """Bind the given values into the interpreter's __main__.

        The values must be shareable.
        """
        ns = dict(ns, **kwargs) wenn ns is not Nichts sonst kwargs
        _interpreters.set___main___attrs(self._id, ns, restrict=Wahr)

    def exec(self, code, /):
        """Run the given source code in the interpreter.

        This is essentially the same als calling the builtin "exec"
        mit this interpreter, using the __dict__ of its __main__
        module als both globals and locals.

        There is no return value.

        If the code raises an unhandled exception then an ExecutionFailed
        exception is raised, which summarizes the unhandled exception.
        The actual exception is discarded because objects cannot be
        shared between interpreters.

        This blocks the current Python thread until done.  During
        that time, the previous interpreter is allowed to run
        in other threads.
        """
        excinfo = _interpreters.exec(self._id, code, restrict=Wahr)
        wenn excinfo is not Nichts:
            raise ExecutionFailed(excinfo)

    def _call(self, callable, args, kwargs):
        res, excinfo = _interpreters.call(self._id, callable, args, kwargs, restrict=Wahr)
        wenn excinfo is not Nichts:
            raise ExecutionFailed(excinfo)
        return res

    def call(self, callable, /, *args, **kwargs):
        """Call the object in the interpreter mit given args/kwargs.

        Nearly all callables, args, kwargs, and return values are
        supported.  All "shareable" objects are supported, als are
        "stateless" functions (meaning non-closures that do not use
        any globals).  This method will fall back to pickle.

        If the callable raises an exception then the error display
        (including full traceback) is sent back between the interpreters
        and an ExecutionFailed exception is raised, much like what
        happens mit Interpreter.exec().
        """
        return self._call(callable, args, kwargs)

    def call_in_thread(self, callable, /, *args, **kwargs):
        """Return a new thread that calls the object in the interpreter.

        The return value and any raised exception are discarded.
        """
        t = threading.Thread(target=self._call, args=(callable, args, kwargs))
        t.start()
        return t
