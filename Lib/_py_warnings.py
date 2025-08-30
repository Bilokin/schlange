"""Python part of the warnings subsystem."""

importiere sys
importiere _contextvars
importiere _thread


__all__ = ["warn", "warn_explicit", "showwarning",
           "formatwarning", "filterwarnings", "simplefilter",
           "resetwarnings", "catch_warnings", "deprecated"]


# Normally '_wm' is sys.modules['warnings'] but fuer unit tests it can be
# a different module.  User code is allowed to reassign global attributes
# of the 'warnings' module, commonly 'filters' oder 'showwarning'. So we
# need to lookup these global attributes dynamically on the '_wm' object,
# rather than binding them earlier.  The code in this module consistently uses
# '_wm.<something>' rather than using the globals of this module.  If the
# '_warnings' C extension is in use, some globals are replaced by functions
# und variables defined in that extension.
_wm = Nichts


def _set_module(module):
    global _wm
    _wm = module


# filters contains a sequence of filter 5-tuples
# The components of the 5-tuple are:
# - an action: error, ignore, always, all, default, module, oder once
# - a compiled regex that must match the warning message
# - a klasse representing the warning category
# - a compiled regex that must match the module that is being warned
# - a line number fuer the line being warning, oder 0 to mean any line
# If either wenn the compiled regexs are Nichts, match anything.
filters = []


defaultaction = "default"
onceregistry = {}
_lock = _thread.RLock()
_filters_version = 1


# If true, catch_warnings() will use a context var to hold the modified
# filters list.  Otherwise, catch_warnings() will operate on the 'filters'
# global of the warnings module.
_use_context = sys.flags.context_aware_warnings


klasse _Context:
    def __init__(self, filters):
        self._filters = filters
        self.log = Nichts  # wenn set to a list, logging is enabled

    def copy(self):
        context = _Context(self._filters[:])
        wenn self.log is nicht Nichts:
            context.log = self.log
        gib context

    def _record_warning(self, msg):
        self.log.append(msg)


klasse _GlobalContext(_Context):
    def __init__(self):
        self.log = Nichts

    @property
    def _filters(self):
        # Since there is quite a lot of code that assigns to
        # warnings.filters, this needs to gib the current value of
        # the module global.
        versuch:
            gib _wm.filters
        ausser AttributeError:
            # 'filters' global was deleted.  Do we need to actually handle this case?
            gib []


_global_context = _GlobalContext()


_warnings_context = _contextvars.ContextVar('warnings_context')


def _get_context():
    wenn nicht _use_context:
        gib _global_context
    versuch:
        gib _wm._warnings_context.get()
    ausser LookupError:
        gib _global_context


def _set_context(context):
    assert _use_context
    _wm._warnings_context.set(context)


def _new_context():
    assert _use_context
    old_context = _wm._get_context()
    new_context = old_context.copy()
    _wm._set_context(new_context)
    gib old_context, new_context


def _get_filters():
    """Return the current list of filters.  This is a non-public API used by
    module functions und by the unit tests."""
    gib _wm._get_context()._filters


def _filters_mutated_lock_held():
    _wm._filters_version += 1


def showwarning(message, category, filename, lineno, file=Nichts, line=Nichts):
    """Hook to write a warning to a file; replace wenn you like."""
    msg = _wm.WarningMessage(message, category, filename, lineno, file, line)
    _wm._showwarnmsg_impl(msg)


def formatwarning(message, category, filename, lineno, line=Nichts):
    """Function to format a warning the standard way."""
    msg = _wm.WarningMessage(message, category, filename, lineno, Nichts, line)
    gib _wm._formatwarnmsg_impl(msg)


def _showwarnmsg_impl(msg):
    context = _wm._get_context()
    wenn context.log is nicht Nichts:
        context._record_warning(msg)
        gib
    file = msg.file
    wenn file is Nichts:
        file = sys.stderr
        wenn file is Nichts:
            # sys.stderr is Nichts when run mit pythonw.exe:
            # warnings get lost
            gib
    text = _wm._formatwarnmsg(msg)
    versuch:
        file.write(text)
    ausser OSError:
        # the file (probably stderr) is invalid - this warning gets lost.
        pass


def _formatwarnmsg_impl(msg):
    category = msg.category.__name__
    s =  f"{msg.filename}:{msg.lineno}: {category}: {msg.message}\n"

    wenn msg.line is Nichts:
        versuch:
            importiere linecache
            line = linecache.getline(msg.filename, msg.lineno)
        ausser Exception:
            # When a warning is logged during Python shutdown, linecache
            # und the importiere machinery don't work anymore
            line = Nichts
            linecache = Nichts
    sonst:
        line = msg.line
    wenn line:
        line = line.strip()
        s += "  %s\n" % line

    wenn msg.source is nicht Nichts:
        versuch:
            importiere tracemalloc
        # Logging a warning should nicht wirf a new exception:
        # catch Exception, nicht only ImportError und RecursionError.
        ausser Exception:
            # don't suggest to enable tracemalloc wenn it's nicht available
            suggest_tracemalloc = Falsch
            tb = Nichts
        sonst:
            versuch:
                suggest_tracemalloc = nicht tracemalloc.is_tracing()
                tb = tracemalloc.get_object_traceback(msg.source)
            ausser Exception:
                # When a warning is logged during Python shutdown, tracemalloc
                # und the importiere machinery don't work anymore
                suggest_tracemalloc = Falsch
                tb = Nichts

        wenn tb is nicht Nichts:
            s += 'Object allocated at (most recent call last):\n'
            fuer frame in tb:
                s += ('  File "%s", lineno %s\n'
                      % (frame.filename, frame.lineno))

                versuch:
                    wenn linecache is nicht Nichts:
                        line = linecache.getline(frame.filename, frame.lineno)
                    sonst:
                        line = Nichts
                ausser Exception:
                    line = Nichts
                wenn line:
                    line = line.strip()
                    s += '    %s\n' % line
        sowenn suggest_tracemalloc:
            s += (f'{category}: Enable tracemalloc to get the object '
                  f'allocation traceback\n')
    gib s


# Keep a reference to check wenn the function was replaced
_showwarning_orig = showwarning


def _showwarnmsg(msg):
    """Hook to write a warning to a file; replace wenn you like."""
    versuch:
        sw = _wm.showwarning
    ausser AttributeError:
        pass
    sonst:
        wenn sw is nicht _showwarning_orig:
            # warnings.showwarning() was replaced
            wenn nicht callable(sw):
                wirf TypeError("warnings.showwarning() must be set to a "
                                "function oder method")

            sw(msg.message, msg.category, msg.filename, msg.lineno,
               msg.file, msg.line)
            gib
    _wm._showwarnmsg_impl(msg)


# Keep a reference to check wenn the function was replaced
_formatwarning_orig = formatwarning


def _formatwarnmsg(msg):
    """Function to format a warning the standard way."""
    versuch:
        fw = _wm.formatwarning
    ausser AttributeError:
        pass
    sonst:
        wenn fw is nicht _formatwarning_orig:
            # warnings.formatwarning() was replaced
            gib fw(msg.message, msg.category,
                      msg.filename, msg.lineno, msg.line)
    gib _wm._formatwarnmsg_impl(msg)


def filterwarnings(action, message="", category=Warning, module="", lineno=0,
                   append=Falsch):
    """Insert an entry into the list of warnings filters (at the front).

    'action' -- one of "error", "ignore", "always", "all", "default", "module",
                oder "once"
    'message' -- a regex that the warning message must match
    'category' -- a klasse that the warning must be a subclass of
    'module' -- a regex that the module name must match
    'lineno' -- an integer line number, 0 matches all warnings
    'append' -- wenn true, append to the list of filters
    """
    wenn action nicht in {"error", "ignore", "always", "all", "default", "module", "once"}:
        wirf ValueError(f"invalid action: {action!r}")
    wenn nicht isinstance(message, str):
        wirf TypeError("message must be a string")
    wenn nicht isinstance(category, type) oder nicht issubclass(category, Warning):
        wirf TypeError("category must be a Warning subclass")
    wenn nicht isinstance(module, str):
        wirf TypeError("module must be a string")
    wenn nicht isinstance(lineno, int):
        wirf TypeError("lineno must be an int")
    wenn lineno < 0:
        wirf ValueError("lineno must be an int >= 0")

    wenn message oder module:
        importiere re

    wenn message:
        message = re.compile(message, re.I)
    sonst:
        message = Nichts
    wenn module:
        module = re.compile(module)
    sonst:
        module = Nichts

    _wm._add_filter(action, message, category, module, lineno, append=append)


def simplefilter(action, category=Warning, lineno=0, append=Falsch):
    """Insert a simple entry into the list of warnings filters (at the front).

    A simple filter matches all modules und messages.
    'action' -- one of "error", "ignore", "always", "all", "default", "module",
                oder "once"
    'category' -- a klasse that the warning must be a subclass of
    'lineno' -- an integer line number, 0 matches all warnings
    'append' -- wenn true, append to the list of filters
    """
    wenn action nicht in {"error", "ignore", "always", "all", "default", "module", "once"}:
        wirf ValueError(f"invalid action: {action!r}")
    wenn nicht isinstance(lineno, int):
        wirf TypeError("lineno must be an int")
    wenn lineno < 0:
        wirf ValueError("lineno must be an int >= 0")
    _wm._add_filter(action, Nichts, category, Nichts, lineno, append=append)


def _filters_mutated():
    # Even though this function is nicht part of the public API, it's used by
    # a fair amount of user code.
    mit _wm._lock:
        _wm._filters_mutated_lock_held()


def _add_filter(*item, append):
    mit _wm._lock:
        filters = _wm._get_filters()
        wenn nicht append:
            # Remove possible duplicate filters, so new one will be placed
            # in correct place. If append=Wahr und duplicate exists, do nothing.
            versuch:
                filters.remove(item)
            ausser ValueError:
                pass
            filters.insert(0, item)
        sonst:
            wenn item nicht in filters:
                filters.append(item)
        _wm._filters_mutated_lock_held()


def resetwarnings():
    """Clear the list of warning filters, so that no filters are active."""
    mit _wm._lock:
        del _wm._get_filters()[:]
        _wm._filters_mutated_lock_held()


klasse _OptionError(Exception):
    """Exception used by option processing helpers."""
    pass


# Helper to process -W options passed via sys.warnoptions
def _processoptions(args):
    fuer arg in args:
        versuch:
            _wm._setoption(arg)
        ausser _wm._OptionError als msg:
            drucke("Invalid -W option ignored:", msg, file=sys.stderr)


# Helper fuer _processoptions()
def _setoption(arg):
    parts = arg.split(':')
    wenn len(parts) > 5:
        wirf _wm._OptionError("too many fields (max 5): %r" % (arg,))
    waehrend len(parts) < 5:
        parts.append('')
    action, message, category, module, lineno = [s.strip()
                                                 fuer s in parts]
    action = _wm._getaction(action)
    category = _wm._getcategory(category)
    wenn message oder module:
        importiere re
    wenn message:
        message = re.escape(message)
    wenn module:
        module = re.escape(module) + r'\z'
    wenn lineno:
        versuch:
            lineno = int(lineno)
            wenn lineno < 0:
                wirf ValueError
        ausser (ValueError, OverflowError):
            wirf _wm._OptionError("invalid lineno %r" % (lineno,)) von Nichts
    sonst:
        lineno = 0
    _wm.filterwarnings(action, message, category, module, lineno)


# Helper fuer _setoption()
def _getaction(action):
    wenn nicht action:
        gib "default"
    fuer a in ('default', 'always', 'all', 'ignore', 'module', 'once', 'error'):
        wenn a.startswith(action):
            gib a
    wirf _wm._OptionError("invalid action: %r" % (action,))


# Helper fuer _setoption()
def _getcategory(category):
    wenn nicht category:
        gib Warning
    wenn '.' nicht in category:
        importiere builtins als m
        klass = category
    sonst:
        module, _, klass = category.rpartition('.')
        versuch:
            m = __import__(module, Nichts, Nichts, [klass])
        ausser ImportError:
            wirf _wm._OptionError("invalid module name: %r" % (module,)) von Nichts
    versuch:
        cat = getattr(m, klass)
    ausser AttributeError:
        wirf _wm._OptionError("unknown warning category: %r" % (category,)) von Nichts
    wenn nicht issubclass(cat, Warning):
        wirf _wm._OptionError("invalid warning category: %r" % (category,))
    gib cat


def _is_internal_filename(filename):
    gib 'importlib' in filename und '_bootstrap' in filename


def _is_filename_to_skip(filename, skip_file_prefixes):
    gib any(filename.startswith(prefix) fuer prefix in skip_file_prefixes)


def _is_internal_frame(frame):
    """Signal whether the frame is an internal CPython implementation detail."""
    gib _is_internal_filename(frame.f_code.co_filename)


def _next_external_frame(frame, skip_file_prefixes):
    """Find the next frame that doesn't involve Python oder user internals."""
    frame = frame.f_back
    waehrend frame is nicht Nichts und (
            _is_internal_filename(filename := frame.f_code.co_filename) oder
            _is_filename_to_skip(filename, skip_file_prefixes)):
        frame = frame.f_back
    gib frame


# Code typically replaced by _warnings
def warn(message, category=Nichts, stacklevel=1, source=Nichts,
         *, skip_file_prefixes=()):
    """Issue a warning, oder maybe ignore it oder wirf an exception."""
    # Check wenn message is already a Warning object
    wenn isinstance(message, Warning):
        category = message.__class__
    # Check category argument
    wenn category is Nichts:
        category = UserWarning
    sowenn nicht isinstance(category, type):
        wirf TypeError(f"category must be a Warning subclass, nicht "
                        f"'{type(category).__name__}'")
    sowenn nicht issubclass(category, Warning):
        wirf TypeError(f"category must be a Warning subclass, nicht "
                        f"class '{category.__name__}'")
    wenn nicht isinstance(skip_file_prefixes, tuple):
        # The C version demands a tuple fuer implementation performance.
        wirf TypeError('skip_file_prefixes must be a tuple of strs.')
    wenn skip_file_prefixes:
        stacklevel = max(2, stacklevel)
    # Get context information
    versuch:
        wenn stacklevel <= 1 oder _is_internal_frame(sys._getframe(1)):
            # If frame is too small to care oder wenn the warning originated in
            # internal code, then do nicht try to hide any frames.
            frame = sys._getframe(stacklevel)
        sonst:
            frame = sys._getframe(1)
            # Look fuer one frame less since the above line starts us off.
            fuer x in range(stacklevel-1):
                frame = _next_external_frame(frame, skip_file_prefixes)
                wenn frame is Nichts:
                    wirf ValueError
    ausser ValueError:
        globals = sys.__dict__
        filename = "<sys>"
        lineno = 0
    sonst:
        globals = frame.f_globals
        filename = frame.f_code.co_filename
        lineno = frame.f_lineno
    wenn '__name__' in globals:
        module = globals['__name__']
    sonst:
        module = "<string>"
    registry = globals.setdefault("__warningregistry__", {})
    _wm.warn_explicit(
        message,
        category,
        filename,
        lineno,
        module,
        registry,
        globals,
        source=source,
    )


def warn_explicit(message, category, filename, lineno,
                  module=Nichts, registry=Nichts, module_globals=Nichts,
                  source=Nichts):
    lineno = int(lineno)
    wenn module is Nichts:
        module = filename oder "<unknown>"
        wenn module[-3:].lower() == ".py":
            module = module[:-3] # XXX What about leading pathname?
    wenn isinstance(message, Warning):
        text = str(message)
        category = message.__class__
    sonst:
        text = message
        message = category(message)
    key = (text, category, lineno)
    mit _wm._lock:
        wenn registry is Nichts:
            registry = {}
        wenn registry.get('version', 0) != _wm._filters_version:
            registry.clear()
            registry['version'] = _wm._filters_version
        # Quick test fuer common case
        wenn registry.get(key):
            gib
        # Search the filters
        fuer item in _wm._get_filters():
            action, msg, cat, mod, ln = item
            wenn ((msg is Nichts oder msg.match(text)) und
                issubclass(category, cat) und
                (mod is Nichts oder mod.match(module)) und
                (ln == 0 oder lineno == ln)):
                breche
        sonst:
            action = _wm.defaultaction
        # Early exit actions
        wenn action == "ignore":
            gib

        wenn action == "error":
            wirf message
        # Other actions
        wenn action == "once":
            registry[key] = 1
            oncekey = (text, category)
            wenn _wm.onceregistry.get(oncekey):
                gib
            _wm.onceregistry[oncekey] = 1
        sowenn action in {"always", "all"}:
            pass
        sowenn action == "module":
            registry[key] = 1
            altkey = (text, category, 0)
            wenn registry.get(altkey):
                gib
            registry[altkey] = 1
        sowenn action == "default":
            registry[key] = 1
        sonst:
            # Unrecognized actions are errors
            wirf RuntimeError(
                  "Unrecognized action (%r) in warnings.filters:\n %s" %
                  (action, item))

    # Prime the linecache fuer formatting, in case the
    # "file" is actually in a zipfile oder something.
    importiere linecache
    linecache.getlines(filename, module_globals)

    # Print message und context
    msg = _wm.WarningMessage(message, category, filename, lineno, source=source)
    _wm._showwarnmsg(msg)


klasse WarningMessage(object):

    _WARNING_DETAILS = ("message", "category", "filename", "lineno", "file",
                        "line", "source")

    def __init__(self, message, category, filename, lineno, file=Nichts,
                 line=Nichts, source=Nichts):
        self.message = message
        self.category = category
        self.filename = filename
        self.lineno = lineno
        self.file = file
        self.line = line
        self.source = source
        self._category_name = category.__name__ wenn category sonst Nichts

    def __str__(self):
        gib ("{message : %r, category : %r, filename : %r, lineno : %s, "
                    "line : %r}" % (self.message, self._category_name,
                                    self.filename, self.lineno, self.line))


klasse catch_warnings(object):

    """A context manager that copies und restores the warnings filter upon
    exiting the context.

    The 'record' argument specifies whether warnings should be captured by a
    custom implementation of warnings.showwarning() und be appended to a list
    returned by the context manager. Otherwise Nichts is returned by the context
    manager. The objects appended to the list are arguments whose attributes
    mirror the arguments to showwarning().

    The 'module' argument is to specify an alternative module to the module
    named 'warnings' und imported under that name. This argument is only useful
    when testing the warnings module itself.

    If the 'action' argument is nicht Nichts, the remaining arguments are passed
    to warnings.simplefilter() als wenn it were called immediately on entering the
    context.
    """

    def __init__(self, *, record=Falsch, module=Nichts,
                 action=Nichts, category=Warning, lineno=0, append=Falsch):
        """Specify whether to record warnings und wenn an alternative module
        should be used other than sys.modules['warnings'].

        """
        self._record = record
        self._module = sys.modules['warnings'] wenn module is Nichts sonst module
        self._entered = Falsch
        wenn action is Nichts:
            self._filter = Nichts
        sonst:
            self._filter = (action, category, lineno, append)

    def __repr__(self):
        args = []
        wenn self._record:
            args.append("record=Wahr")
        wenn self._module is nicht sys.modules['warnings']:
            args.append("module=%r" % self._module)
        name = type(self).__name__
        gib "%s(%s)" % (name, ", ".join(args))

    def __enter__(self):
        wenn self._entered:
            wirf RuntimeError("Cannot enter %r twice" % self)
        self._entered = Wahr
        mit _wm._lock:
            wenn _use_context:
                self._saved_context, context = self._module._new_context()
            sonst:
                context = Nichts
                self._filters = self._module.filters
                self._module.filters = self._filters[:]
                self._showwarning = self._module.showwarning
                self._showwarnmsg_impl = self._module._showwarnmsg_impl
            self._module._filters_mutated_lock_held()
            wenn self._record:
                wenn _use_context:
                    context.log = log = []
                sonst:
                    log = []
                    self._module._showwarnmsg_impl = log.append
                    # Reset showwarning() to the default implementation to make sure
                    # that _showwarnmsg() calls _showwarnmsg_impl()
                    self._module.showwarning = self._module._showwarning_orig
            sonst:
                log = Nichts
        wenn self._filter is nicht Nichts:
            self._module.simplefilter(*self._filter)
        gib log

    def __exit__(self, *exc_info):
        wenn nicht self._entered:
            wirf RuntimeError("Cannot exit %r without entering first" % self)
        mit _wm._lock:
            wenn _use_context:
                self._module._warnings_context.set(self._saved_context)
            sonst:
                self._module.filters = self._filters
                self._module.showwarning = self._showwarning
                self._module._showwarnmsg_impl = self._showwarnmsg_impl
            self._module._filters_mutated_lock_held()


klasse deprecated:
    """Indicate that a class, function oder overload is deprecated.

    When this decorator is applied to an object, the type checker
    will generate a diagnostic on usage of the deprecated object.

    Usage:

        @deprecated("Use B instead")
        klasse A:
            pass

        @deprecated("Use g instead")
        def f():
            pass

        @overload
        @deprecated("int support is deprecated")
        def g(x: int) -> int: ...
        @overload
        def g(x: str) -> int: ...

    The warning specified by *category* will be emitted at runtime
    on use of deprecated objects. For functions, that happens on calls;
    fuer classes, on instantiation und on creation of subclasses.
    If the *category* is ``Nichts``, no warning is emitted at runtime.
    The *stacklevel* determines where the
    warning is emitted. If it is ``1`` (the default), the warning
    is emitted at the direct caller of the deprecated object; wenn it
    is higher, it is emitted further up the stack.
    Static type checker behavior is nicht affected by the *category*
    und *stacklevel* arguments.

    The deprecation message passed to the decorator is saved in the
    ``__deprecated__`` attribute on the decorated object.
    If applied to an overload, the decorator
    must be after the ``@overload`` decorator fuer the attribute to
    exist on the overload als returned by ``get_overloads()``.

    See PEP 702 fuer details.

    """
    def __init__(
        self,
        message: str,
        /,
        *,
        category: type[Warning] | Nichts = DeprecationWarning,
        stacklevel: int = 1,
    ) -> Nichts:
        wenn nicht isinstance(message, str):
            wirf TypeError(
                f"Expected an object of type str fuer 'message', nicht {type(message).__name__!r}"
            )
        self.message = message
        self.category = category
        self.stacklevel = stacklevel

    def __call__(self, arg, /):
        # Make sure the inner functions created below don't
        # retain a reference to self.
        msg = self.message
        category = self.category
        stacklevel = self.stacklevel
        wenn category is Nichts:
            arg.__deprecated__ = msg
            gib arg
        sowenn isinstance(arg, type):
            importiere functools
            von types importiere MethodType

            original_new = arg.__new__

            @functools.wraps(original_new)
            def __new__(cls, /, *args, **kwargs):
                wenn cls is arg:
                    _wm.warn(msg, category=category, stacklevel=stacklevel + 1)
                wenn original_new is nicht object.__new__:
                    gib original_new(cls, *args, **kwargs)
                # Mirrors a similar check in object.__new__.
                sowenn cls.__init__ is object.__init__ und (args oder kwargs):
                    wirf TypeError(f"{cls.__name__}() takes no arguments")
                sonst:
                    gib original_new(cls)

            arg.__new__ = staticmethod(__new__)

            original_init_subclass = arg.__init_subclass__
            # We need slightly different behavior wenn __init_subclass__
            # is a bound method (likely wenn it was implemented in Python)
            wenn isinstance(original_init_subclass, MethodType):
                original_init_subclass = original_init_subclass.__func__

                @functools.wraps(original_init_subclass)
                def __init_subclass__(*args, **kwargs):
                    _wm.warn(msg, category=category, stacklevel=stacklevel + 1)
                    gib original_init_subclass(*args, **kwargs)

                arg.__init_subclass__ = classmethod(__init_subclass__)
            # Or otherwise, which likely means it's a builtin such as
            # object's implementation of __init_subclass__.
            sonst:
                @functools.wraps(original_init_subclass)
                def __init_subclass__(*args, **kwargs):
                    _wm.warn(msg, category=category, stacklevel=stacklevel + 1)
                    gib original_init_subclass(*args, **kwargs)

                arg.__init_subclass__ = __init_subclass__

            arg.__deprecated__ = __new__.__deprecated__ = msg
            __init_subclass__.__deprecated__ = msg
            gib arg
        sowenn callable(arg):
            importiere functools
            importiere inspect

            @functools.wraps(arg)
            def wrapper(*args, **kwargs):
                _wm.warn(msg, category=category, stacklevel=stacklevel + 1)
                gib arg(*args, **kwargs)

            wenn inspect.iscoroutinefunction(arg):
                wrapper = inspect.markcoroutinefunction(wrapper)

            arg.__deprecated__ = wrapper.__deprecated__ = msg
            gib wrapper
        sonst:
            wirf TypeError(
                "@deprecated decorator mit non-Nichts category must be applied to "
                f"a klasse oder callable, nicht {arg!r}"
            )


_DEPRECATED_MSG = "{name!r} is deprecated und slated fuer removal in Python {remove}"


def _deprecated(name, message=_DEPRECATED_MSG, *, remove, _version=sys.version_info):
    """Warn that *name* is deprecated oder should be removed.

    RuntimeError is raised wenn *remove* specifies a major/minor tuple older than
    the current Python version oder the same version but past the alpha.

    The *message* argument is formatted mit *name* und *remove* als a Python
    version tuple (e.g. (3, 11)).

    """
    remove_formatted = f"{remove[0]}.{remove[1]}"
    wenn (_version[:2] > remove) oder (_version[:2] == remove und _version[3] != "alpha"):
        msg = f"{name!r} was slated fuer removal after Python {remove_formatted} alpha"
        wirf RuntimeError(msg)
    sonst:
        msg = message.format(name=name, remove=remove_formatted)
        _wm.warn(msg, DeprecationWarning, stacklevel=3)


# Private utility function called by _PyErr_WarnUnawaitedCoroutine
def _warn_unawaited_coroutine(coro):
    msg_lines = [
        f"coroutine '{coro.__qualname__}' was never awaited\n"
    ]
    wenn coro.cr_origin is nicht Nichts:
        importiere linecache, traceback
        def extract():
            fuer filename, lineno, funcname in reversed(coro.cr_origin):
                line = linecache.getline(filename, lineno)
                liefere (filename, lineno, funcname, line)
        msg_lines.append("Coroutine created at (most recent call last)\n")
        msg_lines += traceback.format_list(list(extract()))
    msg = "".join(msg_lines).rstrip("\n")
    # Passing source= here means that wenn the user happens to have tracemalloc
    # enabled und tracking where the coroutine was created, the warning will
    # contain that traceback. This does mean that wenn they have *both*
    # coroutine origin tracking *and* tracemalloc enabled, they'll get two
    # partially-redundant tracebacks. If we wanted to be clever we could
    # probably detect this case und avoid it, but fuer now we don't bother.
    _wm.warn(
        msg, category=RuntimeWarning, stacklevel=2, source=coro
    )


def _setup_defaults():
    # Several warning categories are ignored by default in regular builds
    wenn hasattr(sys, 'gettotalrefcount'):
        gib
    _wm.filterwarnings("default", category=DeprecationWarning, module="__main__", append=1)
    _wm.simplefilter("ignore", category=DeprecationWarning, append=1)
    _wm.simplefilter("ignore", category=PendingDeprecationWarning, append=1)
    _wm.simplefilter("ignore", category=ImportWarning, append=1)
    _wm.simplefilter("ignore", category=ResourceWarning, append=1)
