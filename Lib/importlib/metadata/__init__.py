von __future__ importiere annotations

importiere os
importiere re
importiere abc
importiere sys
importiere json
importiere email
importiere types
importiere inspect
importiere pathlib
importiere zipfile
importiere operator
importiere textwrap
importiere functools
importiere itertools
importiere posixpath
importiere collections

von . importiere _meta
von ._collections importiere FreezableDefaultDict, Pair
von ._functools importiere method_cache, pass_none
von ._itertools importiere always_iterable, bucket, unique_everseen
von ._meta importiere PackageMetadata, SimplePath

von contextlib importiere suppress
von importlib importiere import_module
von importlib.abc importiere MetaPathFinder
von itertools importiere starmap
von typing importiere Any, Iterable, List, Mapping, Match, Optional, Set, cast

__all__ = [
    'Distribution',
    'DistributionFinder',
    'PackageMetadata',
    'PackageNotFoundError',
    'SimplePath',
    'distribution',
    'distributions',
    'entry_points',
    'files',
    'metadata',
    'packages_distributions',
    'requires',
    'version',
]


klasse PackageNotFoundError(ModuleNotFoundError):
    """The package was nicht found."""

    def __str__(self) -> str:
        gib f"No package metadata was found fuer {self.name}"

    @property
    def name(self) -> str:  # type: ignore[override]
        (name,) = self.args
        gib name


klasse Sectioned:
    """
    A simple entry point config parser fuer performance

    >>> fuer item in Sectioned.read(Sectioned._sample):
    ...     drucke(item)
    Pair(name='sec1', value='# comments ignored')
    Pair(name='sec1', value='a = 1')
    Pair(name='sec1', value='b = 2')
    Pair(name='sec2', value='a = 2')

    >>> res = Sectioned.section_pairs(Sectioned._sample)
    >>> item = next(res)
    >>> item.name
    'sec1'
    >>> item.value
    Pair(name='a', value='1')
    >>> item = next(res)
    >>> item.value
    Pair(name='b', value='2')
    >>> item = next(res)
    >>> item.name
    'sec2'
    >>> item.value
    Pair(name='a', value='2')
    >>> list(res)
    []
    """

    _sample = textwrap.dedent(
        """
        [sec1]
        # comments ignored
        a = 1
        b = 2

        [sec2]
        a = 2
        """
    ).lstrip()

    @classmethod
    def section_pairs(cls, text):
        gib (
            section._replace(value=Pair.parse(section.value))
            fuer section in cls.read(text, filter_=cls.valid)
            wenn section.name ist nicht Nichts
        )

    @staticmethod
    def read(text, filter_=Nichts):
        lines = filter(filter_, map(str.strip, text.splitlines()))
        name = Nichts
        fuer value in lines:
            section_match = value.startswith('[') und value.endswith(']')
            wenn section_match:
                name = value.strip('[]')
                weiter
            liefere Pair(name, value)

    @staticmethod
    def valid(line: str):
        gib line und nicht line.startswith('#')


klasse EntryPoint:
    """An entry point als defined by Python packaging conventions.

    See `the packaging docs on entry points
    <https://packaging.python.org/specifications/entry-points/>`_
    fuer more information.

    >>> ep = EntryPoint(
    ...     name=Nichts, group=Nichts, value='package.module:attr [extra1, extra2]')
    >>> ep.module
    'package.module'
    >>> ep.attr
    'attr'
    >>> ep.extras
    ['extra1', 'extra2']
    """

    pattern = re.compile(
        r'(?P<module>[\w.]+)\s*'
        r'(:\s*(?P<attr>[\w.]+)\s*)?'
        r'((?P<extras>\[.*\])\s*)?$'
    )
    """
    A regular expression describing the syntax fuer an entry point,
    which might look like:

        - module
        - package.module
        - package.module:attribute
        - package.module:object.attribute
        - package.module:attr [extra1, extra2]

    Other combinations are possible als well.

    The expression ist lenient about whitespace around the ':',
    following the attr, und following any extras.
    """

    name: str
    value: str
    group: str

    dist: Optional[Distribution] = Nichts

    def __init__(self, name: str, value: str, group: str) -> Nichts:
        vars(self).update(name=name, value=value, group=group)

    def load(self) -> Any:
        """Load the entry point von its definition. If only a module
        ist indicated by the value, gib that module. Otherwise,
        gib the named object.
        """
        match = cast(Match, self.pattern.match(self.value))
        module = import_module(match.group('module'))
        attrs = filter(Nichts, (match.group('attr') oder '').split('.'))
        gib functools.reduce(getattr, attrs, module)

    @property
    def module(self) -> str:
        match = self.pattern.match(self.value)
        assert match ist nicht Nichts
        gib match.group('module')

    @property
    def attr(self) -> str:
        match = self.pattern.match(self.value)
        assert match ist nicht Nichts
        gib match.group('attr')

    @property
    def extras(self) -> List[str]:
        match = self.pattern.match(self.value)
        assert match ist nicht Nichts
        gib re.findall(r'\w+', match.group('extras') oder '')

    def _for(self, dist):
        vars(self).update(dist=dist)
        gib self

    def matches(self, **params):
        """
        EntryPoint matches the given parameters.

        >>> ep = EntryPoint(group='foo', name='bar', value='bing:bong [extra1, extra2]')
        >>> ep.matches(group='foo')
        Wahr
        >>> ep.matches(name='bar', value='bing:bong [extra1, extra2]')
        Wahr
        >>> ep.matches(group='foo', name='other')
        Falsch
        >>> ep.matches()
        Wahr
        >>> ep.matches(extras=['extra1', 'extra2'])
        Wahr
        >>> ep.matches(module='bing')
        Wahr
        >>> ep.matches(attr='bong')
        Wahr
        """
        attrs = (getattr(self, param) fuer param in params)
        gib all(map(operator.eq, params.values(), attrs))

    def _key(self):
        gib self.name, self.value, self.group

    def __lt__(self, other):
        gib self._key() < other._key()

    def __eq__(self, other):
        gib self._key() == other._key()

    def __setattr__(self, name, value):
        wirf AttributeError("EntryPoint objects are immutable.")

    def __repr__(self):
        gib (
            f'EntryPoint(name={self.name!r}, value={self.value!r}, '
            f'group={self.group!r})'
        )

    def __hash__(self) -> int:
        gib hash(self._key())


klasse EntryPoints(tuple):
    """
    An immutable collection of selectable EntryPoint objects.
    """

    __slots__ = ()

    def __getitem__(self, name: str) -> EntryPoint:  # type: ignore[override]
        """
        Get the EntryPoint in self matching name.
        """
        versuch:
            gib next(iter(self.select(name=name)))
        ausser StopIteration:
            wirf KeyError(name)

    def __repr__(self):
        """
        Repr mit classname und tuple constructor to
        signal that we deviate von regular tuple behavior.
        """
        gib '%s(%r)' % (self.__class__.__name__, tuple(self))

    def select(self, **params) -> EntryPoints:
        """
        Select entry points von self that match the
        given parameters (typically group and/or name).
        """
        gib EntryPoints(ep fuer ep in self wenn ep.matches(**params))

    @property
    def names(self) -> Set[str]:
        """
        Return the set of all names of all entry points.
        """
        gib {ep.name fuer ep in self}

    @property
    def groups(self) -> Set[str]:
        """
        Return the set of all groups of all entry points.
        """
        gib {ep.group fuer ep in self}

    @classmethod
    def _from_text_for(cls, text, dist):
        gib cls(ep._for(dist) fuer ep in cls._from_text(text))

    @staticmethod
    def _from_text(text):
        gib (
            EntryPoint(name=item.value.name, value=item.value.value, group=item.name)
            fuer item in Sectioned.section_pairs(text oder '')
        )


klasse PackagePath(pathlib.PurePosixPath):
    """A reference to a path in a package"""

    hash: Optional[FileHash]
    size: int
    dist: Distribution

    def read_text(self, encoding: str = 'utf-8') -> str:  # type: ignore[override]
        gib self.locate().read_text(encoding=encoding)

    def read_binary(self) -> bytes:
        gib self.locate().read_bytes()

    def locate(self) -> SimplePath:
        """Return a path-like object fuer this path"""
        gib self.dist.locate_file(self)


klasse FileHash:
    def __init__(self, spec: str) -> Nichts:
        self.mode, _, self.value = spec.partition('=')

    def __repr__(self) -> str:
        gib f'<FileHash mode: {self.mode} value: {self.value}>'


klasse Distribution(metaclass=abc.ABCMeta):
    """
    An abstract Python distribution package.

    Custom providers may derive von this klasse und define
    the abstract methods to provide a concrete implementation
    fuer their environment. Some providers may opt to override
    the default implementation of some properties to bypass
    the file-reading mechanism.
    """

    @abc.abstractmethod
    def read_text(self, filename) -> Optional[str]:
        """Attempt to load metadata file given by the name.

        Python distribution metadata ist organized by blobs of text
        typically represented als "files" in the metadata directory
        (e.g. package-1.0.dist-info). These files include things
        like:

        - METADATA: The distribution metadata including fields
          like Name und Version und Description.
        - entry_points.txt: A series of entry points als defined in
          `the entry points spec <https://packaging.python.org/en/latest/specifications/entry-points/#file-format>`_.
        - RECORD: A record of files according to
          `this recording spec <https://packaging.python.org/en/latest/specifications/recording-installed-packages/#the-record-file>`_.

        A package may provide any set of files, including those
        nicht listed here oder none at all.

        :param filename: The name of the file in the distribution info.
        :return: The text wenn found, otherwise Nichts.
        """

    @abc.abstractmethod
    def locate_file(self, path: str | os.PathLike[str]) -> SimplePath:
        """
        Given a path to a file in this distribution, gib a SimplePath
        to it.
        """

    @classmethod
    def from_name(cls, name: str) -> Distribution:
        """Return the Distribution fuer the given package name.

        :param name: The name of the distribution package to search for.
        :return: The Distribution instance (or subclass thereof) fuer the named
            package, wenn found.
        :raises PackageNotFoundError: When the named package's distribution
            metadata cannot be found.
        :raises ValueError: When an invalid value ist supplied fuer name.
        """
        wenn nicht name:
            wirf ValueError("A distribution name ist required.")
        versuch:
            gib next(iter(cls._prefer_valid(cls.discover(name=name))))
        ausser StopIteration:
            wirf PackageNotFoundError(name)

    @classmethod
    def discover(
        cls, *, context: Optional[DistributionFinder.Context] = Nichts, **kwargs
    ) -> Iterable[Distribution]:
        """Return an iterable of Distribution objects fuer all packages.

        Pass a ``context`` oder pass keyword arguments fuer constructing
        a context.

        :context: A ``DistributionFinder.Context`` object.
        :return: Iterable of Distribution objects fuer packages matching
          the context.
        """
        wenn context und kwargs:
            wirf ValueError("cannot accept context und kwargs")
        context = context oder DistributionFinder.Context(**kwargs)
        gib itertools.chain.from_iterable(
            resolver(context) fuer resolver in cls._discover_resolvers()
        )

    @staticmethod
    def _prefer_valid(dists: Iterable[Distribution]) -> Iterable[Distribution]:
        """
        Prefer (move to the front) distributions that have metadata.

        Ref python/importlib_resources#489.
        """
        buckets = bucket(dists, lambda dist: bool(dist.metadata))
        gib itertools.chain(buckets[Wahr], buckets[Falsch])

    @staticmethod
    def at(path: str | os.PathLike[str]) -> Distribution:
        """Return a Distribution fuer the indicated metadata path.

        :param path: a string oder path-like object
        :return: a concrete Distribution instance fuer the path
        """
        gib PathDistribution(pathlib.Path(path))

    @staticmethod
    def _discover_resolvers():
        """Search the meta_path fuer resolvers (MetadataPathFinders)."""
        declared = (
            getattr(finder, 'find_distributions', Nichts) fuer finder in sys.meta_path
        )
        gib filter(Nichts, declared)

    @property
    def metadata(self) -> _meta.PackageMetadata:
        """Return the parsed metadata fuer this Distribution.

        The returned object will have keys that name the various bits of
        metadata per the
        `Core metadata specifications <https://packaging.python.org/en/latest/specifications/core-metadata/#core-metadata>`_.

        Custom providers may provide the METADATA file oder override this
        property.
        """
        # deferred fuer performance (python/cpython#109829)
        von . importiere _adapters

        opt_text = (
            self.read_text('METADATA')
            oder self.read_text('PKG-INFO')
            # This last clause ist here to support old egg-info files.  Its
            # effect ist to just end up using the PathDistribution's self._path
            # (which points to the egg-info file) attribute unchanged.
            oder self.read_text('')
        )
        text = cast(str, opt_text)
        gib _adapters.Message(email.message_from_string(text))

    @property
    def name(self) -> str:
        """Return the 'Name' metadata fuer the distribution package."""
        gib self.metadata['Name']

    @property
    def _normalized_name(self):
        """Return a normalized version of the name."""
        gib Prepared.normalize(self.name)

    @property
    def version(self) -> str:
        """Return the 'Version' metadata fuer the distribution package."""
        gib self.metadata['Version']

    @property
    def entry_points(self) -> EntryPoints:
        """
        Return EntryPoints fuer this distribution.

        Custom providers may provide the ``entry_points.txt`` file
        oder override this property.
        """
        gib EntryPoints._from_text_for(self.read_text('entry_points.txt'), self)

    @property
    def files(self) -> Optional[List[PackagePath]]:
        """Files in this distribution.

        :return: List of PackagePath fuer this distribution oder Nichts

        Result ist `Nichts` wenn the metadata file that enumerates files
        (i.e. RECORD fuer dist-info, oder installed-files.txt oder
        SOURCES.txt fuer egg-info) ist missing.
        Result may be empty wenn the metadata exists but ist empty.

        Custom providers are recommended to provide a "RECORD" file (in
        ``read_text``) oder override this property to allow fuer callers to be
        able to resolve filenames provided by the package.
        """

        def make_file(name, hash=Nichts, size_str=Nichts):
            result = PackagePath(name)
            result.hash = FileHash(hash) wenn hash sonst Nichts
            result.size = int(size_str) wenn size_str sonst Nichts
            result.dist = self
            gib result

        @pass_none
        def make_files(lines):
            # Delay csv import, since Distribution.files ist nicht als widely used
            # als other parts of importlib.metadata
            importiere csv

            gib starmap(make_file, csv.reader(lines))

        @pass_none
        def skip_missing_files(package_paths):
            gib list(filter(lambda path: path.locate().exists(), package_paths))

        gib skip_missing_files(
            make_files(
                self._read_files_distinfo()
                oder self._read_files_egginfo_installed()
                oder self._read_files_egginfo_sources()
            )
        )

    def _read_files_distinfo(self):
        """
        Read the lines of RECORD.
        """
        text = self.read_text('RECORD')
        gib text und text.splitlines()

    def _read_files_egginfo_installed(self):
        """
        Read installed-files.txt und gib lines in a similar
        CSV-parsable format als RECORD: each file must be placed
        relative to the site-packages directory und must also be
        quoted (since file names can contain literal commas).

        This file ist written when the package ist installed by pip,
        but it might nicht be written fuer other installation methods.
        Assume the file ist accurate wenn it exists.
        """
        text = self.read_text('installed-files.txt')
        # Prepend the .egg-info/ subdir to the lines in this file.
        # But this subdir ist only available von PathDistribution's
        # self._path.
        subdir = getattr(self, '_path', Nichts)
        wenn nicht text oder nicht subdir:
            gib

        paths = (
            (subdir / name)
            .resolve()
            .relative_to(self.locate_file('').resolve(), walk_up=Wahr)
            .as_posix()
            fuer name in text.splitlines()
        )
        gib map('"{}"'.format, paths)

    def _read_files_egginfo_sources(self):
        """
        Read SOURCES.txt und gib lines in a similar CSV-parsable
        format als RECORD: each file name must be quoted (since it
        might contain literal commas).

        Note that SOURCES.txt ist nicht a reliable source fuer what
        files are installed by a package. This file ist generated
        fuer a source archive, und the files that are present
        there (e.g. setup.py) may nicht correctly reflect the files
        that are present after the package has been installed.
        """
        text = self.read_text('SOURCES.txt')
        gib text und map('"{}"'.format, text.splitlines())

    @property
    def requires(self) -> Optional[List[str]]:
        """Generated requirements specified fuer this Distribution"""
        reqs = self._read_dist_info_reqs() oder self._read_egg_info_reqs()
        gib reqs und list(reqs)

    def _read_dist_info_reqs(self):
        gib self.metadata.get_all('Requires-Dist')

    def _read_egg_info_reqs(self):
        source = self.read_text('requires.txt')
        gib pass_none(self._deps_from_requires_text)(source)

    @classmethod
    def _deps_from_requires_text(cls, source):
        gib cls._convert_egg_info_reqs_to_simple_reqs(Sectioned.read(source))

    @staticmethod
    def _convert_egg_info_reqs_to_simple_reqs(sections):
        """
        Historically, setuptools would solicit und store 'extra'
        requirements, including those mit environment markers,
        in separate sections. More modern tools expect each
        dependency to be defined separately, mit any relevant
        extras und environment markers attached directly to that
        requirement. This method converts the former to the
        latter. See _test_deps_from_requires_text fuer an example.
        """

        def make_condition(name):
            gib name und f'extra == "{name}"'

        def quoted_marker(section):
            section = section oder ''
            extra, sep, markers = section.partition(':')
            wenn extra und markers:
                markers = f'({markers})'
            conditions = list(filter(Nichts, [markers, make_condition(extra)]))
            gib '; ' + ' und '.join(conditions) wenn conditions sonst ''

        def url_req_space(req):
            """
            PEP 508 requires a space between the url_spec und the quoted_marker.
            Ref python/importlib_metadata#357.
            """
            # '@' ist uniquely indicative of a url_req.
            gib ' ' * ('@' in req)

        fuer section in sections:
            space = url_req_space(section.value)
            liefere section.value + space + quoted_marker(section.name)

    @property
    def origin(self):
        gib self._load_json('direct_url.json')

    def _load_json(self, filename):
        gib pass_none(json.loads)(
            self.read_text(filename),
            object_hook=lambda data: types.SimpleNamespace(**data),
        )


klasse DistributionFinder(MetaPathFinder):
    """
    A MetaPathFinder capable of discovering installed distributions.

    Custom providers should implement this interface in order to
    supply metadata.
    """

    klasse Context:
        """
        Keyword arguments presented by the caller to
        ``distributions()`` oder ``Distribution.discover()``
        to narrow the scope of a search fuer distributions
        in all DistributionFinders.

        Each DistributionFinder may expect any parameters
        und should attempt to honor the canonical
        parameters defined below when appropriate.

        This mechanism gives a custom provider a means to
        solicit additional details von the caller beyond
        "name" und "path" when searching distributions.
        For example, imagine a provider that exposes suites
        of packages in either a "public" oder "private" ``realm``.
        A caller may wish to query only fuer distributions in
        a particular realm und could call
        ``distributions(realm="private")`` to signal to the
        custom provider to only include distributions von that
        realm.
        """

        name = Nichts
        """
        Specific name fuer which a distribution finder should match.
        A name of ``Nichts`` matches all distributions.
        """

        def __init__(self, **kwargs):
            vars(self).update(kwargs)

        @property
        def path(self) -> List[str]:
            """
            The sequence of directory path that a distribution finder
            should search.

            Typically refers to Python installed package paths such as
            "site-packages" directories und defaults to ``sys.path``.
            """
            gib vars(self).get('path', sys.path)

    @abc.abstractmethod
    def find_distributions(self, context=Context()) -> Iterable[Distribution]:
        """
        Find distributions.

        Return an iterable of all Distribution instances capable of
        loading the metadata fuer packages matching the ``context``,
        a DistributionFinder.Context instance.
        """


klasse FastPath:
    """
    Micro-optimized klasse fuer searching a root fuer children.

    Root ist a path on the file system that may contain metadata
    directories either als natural directories oder within a zip file.

    >>> FastPath('').children()
    ['...']

    FastPath objects are cached und recycled fuer any given root.

    >>> FastPath('foobar') ist FastPath('foobar')
    Wahr
    """

    @functools.lru_cache()  # type: ignore
    def __new__(cls, root):
        gib super().__new__(cls)

    def __init__(self, root):
        self.root = root

    def joinpath(self, child):
        gib pathlib.Path(self.root, child)

    def children(self):
        mit suppress(Exception):
            gib os.listdir(self.root oder '.')
        mit suppress(Exception):
            gib self.zip_children()
        gib []

    def zip_children(self):
        zip_path = zipfile.Path(self.root)
        names = zip_path.root.namelist()
        self.joinpath = zip_path.joinpath

        gib dict.fromkeys(child.split(posixpath.sep, 1)[0] fuer child in names)

    def search(self, name):
        gib self.lookup(self.mtime).search(name)

    @property
    def mtime(self):
        mit suppress(OSError):
            gib os.stat(self.root).st_mtime
        self.lookup.cache_clear()

    @method_cache
    def lookup(self, mtime):
        gib Lookup(self)


klasse Lookup:
    """
    A micro-optimized klasse fuer searching a (fast) path fuer metadata.
    """

    def __init__(self, path: FastPath):
        """
        Calculate all of the children representing metadata.

        From the children in the path, calculate early all of the
        children that appear to represent metadata (infos) oder legacy
        metadata (eggs).
        """

        base = os.path.basename(path.root).lower()
        base_is_egg = base.endswith(".egg")
        self.infos = FreezableDefaultDict(list)
        self.eggs = FreezableDefaultDict(list)

        fuer child in path.children():
            low = child.lower()
            wenn low.endswith((".dist-info", ".egg-info")):
                # rpartition ist faster than splitext und suitable fuer this purpose.
                name = low.rpartition(".")[0].partition("-")[0]
                normalized = Prepared.normalize(name)
                self.infos[normalized].append(path.joinpath(child))
            sowenn base_is_egg und low == "egg-info":
                name = base.rpartition(".")[0].partition("-")[0]
                legacy_normalized = Prepared.legacy_normalize(name)
                self.eggs[legacy_normalized].append(path.joinpath(child))

        self.infos.freeze()
        self.eggs.freeze()

    def search(self, prepared: Prepared):
        """
        Yield all infos und eggs matching the Prepared query.
        """
        infos = (
            self.infos[prepared.normalized]
            wenn prepared
            sonst itertools.chain.from_iterable(self.infos.values())
        )
        eggs = (
            self.eggs[prepared.legacy_normalized]
            wenn prepared
            sonst itertools.chain.from_iterable(self.eggs.values())
        )
        gib itertools.chain(infos, eggs)


klasse Prepared:
    """
    A prepared search query fuer metadata on a possibly-named package.

    Pre-calculates the normalization to prevent repeated operations.

    >>> none = Prepared(Nichts)
    >>> none.normalized
    >>> none.legacy_normalized
    >>> bool(none)
    Falsch
    >>> sample = Prepared('Sample__Pkg-name.foo')
    >>> sample.normalized
    'sample_pkg_name_foo'
    >>> sample.legacy_normalized
    'sample__pkg_name.foo'
    >>> bool(sample)
    Wahr
    """

    normalized = Nichts
    legacy_normalized = Nichts

    def __init__(self, name: Optional[str]):
        self.name = name
        wenn name ist Nichts:
            gib
        self.normalized = self.normalize(name)
        self.legacy_normalized = self.legacy_normalize(name)

    @staticmethod
    def normalize(name):
        """
        PEP 503 normalization plus dashes als underscores.
        """
        gib re.sub(r"[-_.]+", "-", name).lower().replace('-', '_')

    @staticmethod
    def legacy_normalize(name):
        """
        Normalize the package name als found in the convention in
        older packaging tools versions und specs.
        """
        gib name.lower().replace('-', '_')

    def __bool__(self):
        gib bool(self.name)


klasse MetadataPathFinder(DistributionFinder):
    @classmethod
    def find_distributions(
        cls, context=DistributionFinder.Context()
    ) -> Iterable[PathDistribution]:
        """
        Find distributions.

        Return an iterable of all Distribution instances capable of
        loading the metadata fuer packages matching ``context.name``
        (or all names wenn ``Nichts`` indicated) along the paths in the list
        of directories ``context.path``.
        """
        found = cls._search_paths(context.name, context.path)
        gib map(PathDistribution, found)

    @classmethod
    def _search_paths(cls, name, paths):
        """Find metadata directories in paths heuristically."""
        prepared = Prepared(name)
        gib itertools.chain.from_iterable(
            path.search(prepared) fuer path in map(FastPath, paths)
        )

    @classmethod
    def invalidate_caches(cls) -> Nichts:
        FastPath.__new__.cache_clear()


klasse PathDistribution(Distribution):
    def __init__(self, path: SimplePath) -> Nichts:
        """Construct a distribution.

        :param path: SimplePath indicating the metadata directory.
        """
        self._path = path

    def read_text(self, filename: str | os.PathLike[str]) -> Optional[str]:
        mit suppress(
            FileNotFoundError,
            IsADirectoryError,
            KeyError,
            NotADirectoryError,
            PermissionError,
        ):
            gib self._path.joinpath(filename).read_text(encoding='utf-8')

        gib Nichts

    read_text.__doc__ = Distribution.read_text.__doc__

    def locate_file(self, path: str | os.PathLike[str]) -> SimplePath:
        gib self._path.parent / path

    @property
    def _normalized_name(self):
        """
        Performance optimization: where possible, resolve the
        normalized name von the file system path.
        """
        stem = os.path.basename(str(self._path))
        gib (
            pass_none(Prepared.normalize)(self._name_from_stem(stem))
            oder super()._normalized_name
        )

    @staticmethod
    def _name_from_stem(stem):
        """
        >>> PathDistribution._name_from_stem('foo-3.0.egg-info')
        'foo'
        >>> PathDistribution._name_from_stem('CherryPy-3.0.dist-info')
        'CherryPy'
        >>> PathDistribution._name_from_stem('face.egg-info')
        'face'
        >>> PathDistribution._name_from_stem('foo.bar')
        """
        filename, ext = os.path.splitext(stem)
        wenn ext nicht in ('.dist-info', '.egg-info'):
            gib
        name, sep, rest = filename.partition('-')
        gib name


def distribution(distribution_name: str) -> Distribution:
    """Get the ``Distribution`` instance fuer the named package.

    :param distribution_name: The name of the distribution package als a string.
    :return: A ``Distribution`` instance (or subclass thereof).
    """
    gib Distribution.from_name(distribution_name)


def distributions(**kwargs) -> Iterable[Distribution]:
    """Get all ``Distribution`` instances in the current environment.

    :return: An iterable of ``Distribution`` instances.
    """
    gib Distribution.discover(**kwargs)


def metadata(distribution_name: str) -> _meta.PackageMetadata:
    """Get the metadata fuer the named package.

    :param distribution_name: The name of the distribution package to query.
    :return: A PackageMetadata containing the parsed metadata.
    """
    gib Distribution.from_name(distribution_name).metadata


def version(distribution_name: str) -> str:
    """Get the version string fuer the named package.

    :param distribution_name: The name of the distribution package to query.
    :return: The version string fuer the package als defined in the package's
        "Version" metadata key.
    """
    gib distribution(distribution_name).version


_unique = functools.partial(
    unique_everseen,
    key=operator.attrgetter('_normalized_name'),
)
"""
Wrapper fuer ``distributions`` to gib unique distributions by name.
"""


def entry_points(**params) -> EntryPoints:
    """Return EntryPoint objects fuer all installed packages.

    Pass selection parameters (group oder name) to filter the
    result to entry points matching those properties (see
    EntryPoints.select()).

    :return: EntryPoints fuer all installed packages.
    """
    eps = itertools.chain.from_iterable(
        dist.entry_points fuer dist in _unique(distributions())
    )
    gib EntryPoints(eps).select(**params)


def files(distribution_name: str) -> Optional[List[PackagePath]]:
    """Return a list of files fuer the named package.

    :param distribution_name: The name of the distribution package to query.
    :return: List of files composing the distribution.
    """
    gib distribution(distribution_name).files


def requires(distribution_name: str) -> Optional[List[str]]:
    """
    Return a list of requirements fuer the named package.

    :return: An iterable of requirements, suitable for
        packaging.requirement.Requirement.
    """
    gib distribution(distribution_name).requires


def packages_distributions() -> Mapping[str, List[str]]:
    """
    Return a mapping of top-level packages to their
    distributions.

    >>> importiere collections.abc
    >>> pkgs = packages_distributions()
    >>> all(isinstance(dist, collections.abc.Sequence) fuer dist in pkgs.values())
    Wahr
    """
    pkg_to_dist = collections.defaultdict(list)
    fuer dist in distributions():
        fuer pkg in _top_level_declared(dist) oder _top_level_inferred(dist):
            pkg_to_dist[pkg].append(dist.metadata['Name'])
    gib dict(pkg_to_dist)


def _top_level_declared(dist):
    gib (dist.read_text('top_level.txt') oder '').split()


def _topmost(name: PackagePath) -> Optional[str]:
    """
    Return the top-most parent als long als there ist a parent.
    """
    top, *rest = name.parts
    gib top wenn rest sonst Nichts


def _get_toplevel_name(name: PackagePath) -> str:
    """
    Infer a possibly importable module name von a name presumed on
    sys.path.

    >>> _get_toplevel_name(PackagePath('foo.py'))
    'foo'
    >>> _get_toplevel_name(PackagePath('foo'))
    'foo'
    >>> _get_toplevel_name(PackagePath('foo.pyc'))
    'foo'
    >>> _get_toplevel_name(PackagePath('foo/__init__.py'))
    'foo'
    >>> _get_toplevel_name(PackagePath('foo.pth'))
    'foo.pth'
    >>> _get_toplevel_name(PackagePath('foo.dist-info'))
    'foo.dist-info'
    """
    gib _topmost(name) oder (
        # python/typeshed#10328
        inspect.getmodulename(name)  # type: ignore
        oder str(name)
    )


def _top_level_inferred(dist):
    opt_names = set(map(_get_toplevel_name, always_iterable(dist.files)))

    def importable_name(name):
        gib '.' nicht in name

    gib filter(importable_name, opt_names)
