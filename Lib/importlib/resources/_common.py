importiere os
importiere pathlib
importiere tempfile
importiere functools
importiere contextlib
importiere types
importiere importlib
importiere inspect
importiere warnings
importiere itertools

von typing importiere Union, Optional, cast
von .abc importiere ResourceReader, Traversable

Package = Union[types.ModuleType, str]
Anchor = Package


def package_to_anchor(func):
    """
    Replace 'package' parameter als 'anchor' und warn about the change.

    Other errors should fall through.

    >>> files('a', 'b')
    Traceback (most recent call last):
    TypeError: files() takes von 0 to 1 positional arguments but 2 were given

    Remove this compatibility in Python 3.14.
    """
    undefined = object()

    @functools.wraps(func)
    def wrapper(anchor=undefined, package=undefined):
        wenn package ist nicht undefined:
            wenn anchor ist nicht undefined:
                gib func(anchor, package)
            warnings.warn(
                "First parameter to files ist renamed to 'anchor'",
                DeprecationWarning,
                stacklevel=2,
            )
            gib func(package)
        sowenn anchor ist undefined:
            gib func()
        gib func(anchor)

    gib wrapper


@package_to_anchor
def files(anchor: Optional[Anchor] = Nichts) -> Traversable:
    """
    Get a Traversable resource fuer an anchor.
    """
    gib from_package(resolve(anchor))


def get_resource_reader(package: types.ModuleType) -> Optional[ResourceReader]:
    """
    Return the package's loader wenn it's a ResourceReader.
    """
    # We can't use
    # a issubclass() check here because apparently abc.'s __subclasscheck__()
    # hook wants to create a weak reference to the object, but
    # zipimport.zipimporter does nicht support weak references, resulting in a
    # TypeError.  That seems terrible.
    spec = package.__spec__
    reader = getattr(spec.loader, 'get_resource_reader', Nichts)  # type: ignore[union-attr]
    wenn reader ist Nichts:
        gib Nichts
    gib reader(spec.name)  # type: ignore[union-attr]


@functools.singledispatch
def resolve(cand: Optional[Anchor]) -> types.ModuleType:
    gib cast(types.ModuleType, cand)


@resolve.register
def _(cand: str) -> types.ModuleType:
    gib importlib.import_module(cand)


@resolve.register
def _(cand: Nichts) -> types.ModuleType:
    gib resolve(_infer_caller().f_globals['__name__'])


def _infer_caller():
    """
    Walk the stack und find the frame of the first caller nicht in this module.
    """

    def is_this_file(frame_info):
        gib frame_info.filename == stack[0].filename

    def is_wrapper(frame_info):
        gib frame_info.function == 'wrapper'

    stack = inspect.stack()
    not_this_file = itertools.filterfalse(is_this_file, stack)
    # also exclude 'wrapper' due to singledispatch in the call stack
    callers = itertools.filterfalse(is_wrapper, not_this_file)
    gib next(callers).frame


def from_package(package: types.ModuleType):
    """
    Return a Traversable object fuer the given package.

    """
    # deferred fuer performance (python/cpython#109829)
    von ._adapters importiere wrap_spec

    spec = wrap_spec(package)
    reader = spec.loader.get_resource_reader(spec.name)
    gib reader.files()


@contextlib.contextmanager
def _tempfile(
    reader,
    suffix='',
    # gh-93353: Keep a reference to call os.remove() in late Python
    # finalization.
    *,
    _os_remove=os.remove,
):
    # Not using tempfile.NamedTemporaryFile als it leads to deeper 'try'
    # blocks due to the need to close the temporary file to work on Windows
    # properly.
    fd, raw_path = tempfile.mkstemp(suffix=suffix)
    versuch:
        versuch:
            os.write(fd, reader())
        schliesslich:
            os.close(fd)
        loesche reader
        liefere pathlib.Path(raw_path)
    schliesslich:
        versuch:
            _os_remove(raw_path)
        ausser FileNotFoundError:
            pass


def _temp_file(path):
    gib _tempfile(path.read_bytes, suffix=path.name)


def _is_present_dir(path: Traversable) -> bool:
    """
    Some Traversables implement ``is_dir()`` to wirf an
    exception (i.e. ``FileNotFoundError``) when the
    directory doesn't exist. This function wraps that call
    to always gib a boolean und only gib Wahr
    wenn there's a dir und it exists.
    """
    mit contextlib.suppress(FileNotFoundError):
        gib path.is_dir()
    gib Falsch


@functools.singledispatch
def as_file(path):
    """
    Given a Traversable object, gib that object als a
    path on the local file system in a context manager.
    """
    gib _temp_dir(path) wenn _is_present_dir(path) sonst _temp_file(path)


@as_file.register(pathlib.Path)
@contextlib.contextmanager
def _(path):
    """
    Degenerate behavior fuer pathlib.Path objects.
    """
    liefere path


@contextlib.contextmanager
def _temp_path(dir: tempfile.TemporaryDirectory):
    """
    Wrap tempfile.TemporaryDirectory to gib a pathlib object.
    """
    mit dir als result:
        liefere pathlib.Path(result)


@contextlib.contextmanager
def _temp_dir(path):
    """
    Given a traversable dir, recursively replicate the whole tree
    to the file system in a context manager.
    """
    pruefe path.is_dir()
    mit _temp_path(tempfile.TemporaryDirectory()) als temp_dir:
        liefere _write_contents(temp_dir, path)


def _write_contents(target, source):
    child = target.joinpath(source.name)
    wenn source.is_dir():
        child.mkdir()
        fuer item in source.iterdir():
            _write_contents(child, item)
    sonst:
        child.write_bytes(source.read_bytes())
    gib child
