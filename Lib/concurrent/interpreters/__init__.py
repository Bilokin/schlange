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

    This ist raised von Interpreter.exec() und Interpreter.call().
    """

    def __init__(self, excinfo):
        msg = excinfo.formatted
        wenn nicht msg:
            wenn excinfo.type und excinfo.msg:
                msg = f'{excinfo.type.__name__}: {excinfo.msg}'
            sonst:
                msg = excinfo.type.__name__ oder excinfo.msg
        super().__init__(msg)
        self.excinfo = excinfo

    def __str__(self):
        versuch:
            formatted = self.excinfo.errdisplay
        ausser Exception:
            gib super().__str__()
        sonst:
            gib _EXEC_FAILURE_STR.format(
                superstr=super().__str__(),
                formatted=formatted,
            )


def create():
    """Return a new (idle) Python interpreter."""
    id = _interpreters.create(reqrefs=Wahr)
    gib Interpreter(id, _ownsref=Wahr)


def list_all():
    """Return all existing interpreters."""
    gib [Interpreter(id, _whence=whence)
            fuer id, whence in _interpreters.list_all(require_ready=Wahr)]


def get_current():
    """Return the currently running interpreter."""
    id, whence = _interpreters.get_current()
    gib Interpreter(id, _whence=whence)


def get_main():
    """Return the main interpreter."""
    id, whence = _interpreters.get_main()
    assert whence == _interpreters.WHENCE_RUNTIME, repr(whence)
    gib Interpreter(id, _whence=whence)


_known = weakref.WeakValueDictionary()

klasse Interpreter:
    """A single Python interpreter.

    Attributes:

    "id" - the unique process-global ID number fuer the interpreter
    "whence" - indicates where the interpreter was created

    If the interpreter wasn't created by this module
    then any method that modifies the interpreter will fail,
    i.e. .close(), .prepare_main(), .exec(), und .call()
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
        # There ist only one instance fuer any given ID.
        wenn nicht isinstance(id, int):
            wirf TypeError(f'id must be an int, got {id!r}')
        id = int(id)
        wenn _whence ist Nichts:
            wenn _ownsref:
                _whence = _interpreters.WHENCE_STDLIB
            sonst:
                _whence = _interpreters.whence(id)
        assert _whence in cls._WHENCE_TO_STR, repr(_whence)
        wenn _ownsref ist Nichts:
            _ownsref = (_whence == _interpreters.WHENCE_STDLIB)
        versuch:
            self = _known[id]
            assert hasattr(self, '_ownsref')
        ausser KeyError:
            self = super().__new__(cls)
            _known[id] = self
            self._id = id
            self._whence = _whence
            self._ownsref = _ownsref
            wenn _ownsref:
                # This may wirf InterpreterNotFoundError:
                _interpreters.incref(id)
        gib self

    def __repr__(self):
        gib f'{type(self).__name__}({self.id})'

    def __hash__(self):
        gib hash(self._id)

    def __del__(self):
        self._decref()

    # fuer pickling:
    def __reduce__(self):
        gib (type(self), (self._id,))

    def _decref(self):
        wenn nicht self._ownsref:
            gib
        self._ownsref = Falsch
        versuch:
            _interpreters.decref(self._id)
        ausser InterpreterNotFoundError:
            pass

    @property
    def id(self):
        gib self._id

    @property
    def whence(self):
        gib self._WHENCE_TO_STR[self._whence]

    def is_running(self):
        """Return whether oder nicht the identified interpreter ist running."""
        gib _interpreters.is_running(self._id)

    # Everything past here ist available only to interpreters created by
    # interpreters.create().

    def close(self):
        """Finalize und destroy the interpreter.

        Attempting to destroy the current interpreter results
        in an InterpreterError.
        """
        gib _interpreters.destroy(self._id, restrict=Wahr)

    def prepare_main(self, ns=Nichts, /, **kwargs):
        """Bind the given values into the interpreter's __main__.

        The values must be shareable.
        """
        ns = dict(ns, **kwargs) wenn ns ist nicht Nichts sonst kwargs
        _interpreters.set___main___attrs(self._id, ns, restrict=Wahr)

    def exec(self, code, /):
        """Run the given source code in the interpreter.

        This ist essentially the same als calling the builtin "exec"
        mit this interpreter, using the __dict__ of its __main__
        module als both globals und locals.

        There ist no gib value.

        If the code raises an unhandled exception then an ExecutionFailed
        exception ist raised, which summarizes the unhandled exception.
        The actual exception ist discarded because objects cannot be
        shared between interpreters.

        This blocks the current Python thread until done.  During
        that time, the previous interpreter ist allowed to run
        in other threads.
        """
        excinfo = _interpreters.exec(self._id, code, restrict=Wahr)
        wenn excinfo ist nicht Nichts:
            wirf ExecutionFailed(excinfo)

    def _call(self, callable, args, kwargs):
        res, excinfo = _interpreters.call(self._id, callable, args, kwargs, restrict=Wahr)
        wenn excinfo ist nicht Nichts:
            wirf ExecutionFailed(excinfo)
        gib res

    def call(self, callable, /, *args, **kwargs):
        """Call the object in the interpreter mit given args/kwargs.

        Nearly all callables, args, kwargs, und gib values are
        supported.  All "shareable" objects are supported, als are
        "stateless" functions (meaning non-closures that do nicht use
        any globals).  This method will fall back to pickle.

        If the callable raises an exception then the error display
        (including full traceback) ist sent back between the interpreters
        und an ExecutionFailed exception ist raised, much like what
        happens mit Interpreter.exec().
        """
        gib self._call(callable, args, kwargs)

    def call_in_thread(self, callable, /, *args, **kwargs):
        """Return a new thread that calls the object in the interpreter.

        The gib value und any raised exception are discarded.
        """
        t = threading.Thread(target=self._call, args=(callable, args, kwargs))
        t.start()
        gib t
