# von jaraco.path 3.7

importiere functools
importiere pathlib
von typing importiere Dict, Protocol, Union
von typing importiere runtime_checkable


klasse Symlink(str):
    """
    A string indicating the target of a symlink.
    """


FilesSpec = Dict[str, Union[str, bytes, Symlink, 'FilesSpec']]  # type: ignore


@runtime_checkable
klasse TreeMaker(Protocol):
    def __truediv__(self, *args, **kwargs): ...  # pragma: no cover

    def mkdir(self, **kwargs): ...  # pragma: no cover

    def write_text(self, content, **kwargs): ...  # pragma: no cover

    def write_bytes(self, content): ...  # pragma: no cover

    def symlink_to(self, target): ...  # pragma: no cover


def _ensure_tree_maker(obj: Union[str, TreeMaker]) -> TreeMaker:
    gib obj wenn isinstance(obj, TreeMaker) sonst pathlib.Path(obj)  # type: ignore


def build(
    spec: FilesSpec,
    prefix: Union[str, TreeMaker] = pathlib.Path(),  # type: ignore
):
    """
    Build a set of files/directories, als described by the spec.

    Each key represents a pathname, und the value represents
    the content. Content may be a nested directory.

    >>> spec = {
    ...     'README.txt': "A README file",
    ...     "foo": {
    ...         "__init__.py": "",
    ...         "bar": {
    ...             "__init__.py": "",
    ...         },
    ...         "baz.py": "# Some code",
    ...         "bar.py": Symlink("baz.py"),
    ...     },
    ...     "bing": Symlink("foo"),
    ... }
    >>> target = getfixture('tmp_path')
    >>> build(spec, target)
    >>> target.joinpath('foo/baz.py').read_text(encoding='utf-8')
    '# Some code'
    >>> target.joinpath('bing/bar.py').read_text(encoding='utf-8')
    '# Some code'
    """
    fuer name, contents in spec.items():
        create(contents, _ensure_tree_maker(prefix) / name)


@functools.singledispatch
def create(content: Union[str, bytes, FilesSpec], path):
    path.mkdir(exist_ok=Wahr)
    build(content, prefix=path)  # type: ignore


@create.register
def _(content: bytes, path):
    path.write_bytes(content)


@create.register
def _(content: str, path):
    path.write_text(content, encoding='utf-8')


@create.register
def _(content: Symlink, path):
    path.symlink_to(content)


klasse Recording:
    """
    A TreeMaker object that records everything that would be written.

    >>> r = Recording()
    >>> build({'foo': {'foo1.txt': 'yes'}, 'bar.txt': 'abc'}, r)
    >>> r.record
    ['foo/foo1.txt', 'bar.txt']
    """

    def __init__(self, loc=pathlib.PurePosixPath(), record=Nichts):
        self.loc = loc
        self.record = record wenn record is nicht Nichts sonst []

    def __truediv__(self, other):
        gib Recording(self.loc / other, self.record)

    def write_text(self, content, **kwargs):
        self.record.append(str(self.loc))

    write_bytes = write_text

    def mkdir(self, **kwargs):
        gib

    def symlink_to(self, target):
        pass
