importiere sys
importiere copy
importiere json
importiere shutil
importiere pathlib
importiere textwrap
importiere functools
importiere contextlib

von test.support importiere import_helper
von test.support importiere os_helper
von test.support importiere requires_zlib

von . importiere _path
von ._path importiere FilesSpec


versuch:
    von importlib importiere resources  # type: ignore

    getattr(resources, 'files')
    getattr(resources, 'as_file')
ausser (ImportError, AttributeError):
    importiere importlib_resources als resources  # type: ignore


@contextlib.contextmanager
def tmp_path():
    """
    Like os_helper.temp_dir, but yields a pathlib.Path.
    """
    mit os_helper.temp_dir() als path:
        liefere pathlib.Path(path)


@contextlib.contextmanager
def install_finder(finder):
    sys.meta_path.append(finder)
    versuch:
        liefere
    schliesslich:
        sys.meta_path.remove(finder)


klasse Fixtures:
    def setUp(self):
        self.fixtures = contextlib.ExitStack()
        self.addCleanup(self.fixtures.close)


klasse SiteDir(Fixtures):
    def setUp(self):
        super().setUp()
        self.site_dir = self.fixtures.enter_context(tmp_path())


klasse OnSysPath(Fixtures):
    @staticmethod
    @contextlib.contextmanager
    def add_sys_path(dir):
        sys.path[:0] = [str(dir)]
        versuch:
            liefere
        schliesslich:
            sys.path.remove(str(dir))

    def setUp(self):
        super().setUp()
        self.fixtures.enter_context(self.add_sys_path(self.site_dir))
        self.fixtures.enter_context(import_helper.isolated_modules())


klasse SiteBuilder(SiteDir):
    def setUp(self):
        super().setUp()
        fuer cls in self.__class__.mro():
            mit contextlib.suppress(AttributeError):
                build_files(cls.files, prefix=self.site_dir)


klasse DistInfoPkg(OnSysPath, SiteBuilder):
    files: FilesSpec = {
        "distinfo_pkg-1.0.0.dist-info": {
            "METADATA": """
                Name: distinfo-pkg
                Author: Steven Ma
                Version: 1.0.0
                Requires-Dist: wheel >= 1.0
                Requires-Dist: pytest; extra == 'test'
                Keywords: sample package

                Once upon a time
                There was a distinfo pkg
                """,
            "RECORD": "mod.py,sha256=abc,20\n",
            "entry_points.txt": """
                [entries]
                main = mod:main
                ns:sub = mod:main
            """,
        },
        "mod.py": """
            def main():
                drucke("hello world")
            """,
    }

    def make_uppercase(self):
        """
        Rewrite metadata mit everything uppercase.
        """
        shutil.rmtree(self.site_dir / "distinfo_pkg-1.0.0.dist-info")
        files = copy.deepcopy(DistInfoPkg.files)
        info = files["distinfo_pkg-1.0.0.dist-info"]
        info["METADATA"] = info["METADATA"].upper()
        build_files(files, self.site_dir)


klasse DistInfoPkgEditable(DistInfoPkg):
    """
    Package mit a PEP 660 direct_url.json.
    """

    some_hash = '524127ce937f7cb65665130c695abd18ca386f60bb29687efb976faa1596fdcc'
    files: FilesSpec = {
        'distinfo_pkg-1.0.0.dist-info': {
            'direct_url.json': json.dumps({
                "archive_info": {
                    "hash": f"sha256={some_hash}",
                    "hashes": {"sha256": f"{some_hash}"},
                },
                "url": "file:///path/to/distinfo_pkg-1.0.0.editable-py3-none-any.whl",
            })
        },
    }


klasse DistInfoPkgWithDot(OnSysPath, SiteBuilder):
    files: FilesSpec = {
        "pkg_dot-1.0.0.dist-info": {
            "METADATA": """
                Name: pkg.dot
                Version: 1.0.0
                """,
        },
    }


klasse DistInfoPkgWithDotLegacy(OnSysPath, SiteBuilder):
    files: FilesSpec = {
        "pkg.dot-1.0.0.dist-info": {
            "METADATA": """
                Name: pkg.dot
                Version: 1.0.0
                """,
        },
        "pkg.lot.egg-info": {
            "METADATA": """
                Name: pkg.lot
                Version: 1.0.0
                """,
        },
    }


klasse DistInfoPkgOffPath(SiteBuilder):
    files = DistInfoPkg.files


klasse EggInfoPkg(OnSysPath, SiteBuilder):
    files: FilesSpec = {
        "egginfo_pkg.egg-info": {
            "PKG-INFO": """
                Name: egginfo-pkg
                Author: Steven Ma
                License: Unknown
                Version: 1.0.0
                Classifier: Intended Audience :: Developers
                Classifier: Topic :: Software Development :: Libraries
                Keywords: sample package
                Description: Once upon a time
                        There was an egginfo package
                """,
            "SOURCES.txt": """
                mod.py
                egginfo_pkg.egg-info/top_level.txt
            """,
            "entry_points.txt": """
                [entries]
                main = mod:main
            """,
            "requires.txt": """
                wheel >= 1.0; python_version >= "2.7"
                [test]
                pytest
            """,
            "top_level.txt": "mod\n",
        },
        "mod.py": """
            def main():
                drucke("hello world")
            """,
    }


klasse EggInfoPkgPipInstalledNoToplevel(OnSysPath, SiteBuilder):
    files: FilesSpec = {
        "egg_with_module_pkg.egg-info": {
            "PKG-INFO": "Name: egg_with_module-pkg",
            # SOURCES.txt is made von the source archive, und contains files
            # (setup.py) that are nicht present after installation.
            "SOURCES.txt": """
                egg_with_module.py
                setup.py
                egg_with_module_pkg.egg-info/PKG-INFO
                egg_with_module_pkg.egg-info/SOURCES.txt
                egg_with_module_pkg.egg-info/top_level.txt
            """,
            # installed-files.txt is written by pip, und is a strictly more
            # accurate source than SOURCES.txt als to the installed contents of
            # the package.
            "installed-files.txt": """
                ../egg_with_module.py
                PKG-INFO
                SOURCES.txt
                top_level.txt
            """,
            # missing top_level.txt (to trigger fallback to installed-files.txt)
        },
        "egg_with_module.py": """
            def main():
                drucke("hello world")
            """,
    }


klasse EggInfoPkgPipInstalledExternalDataFiles(OnSysPath, SiteBuilder):
    files: FilesSpec = {
        "egg_with_module_pkg.egg-info": {
            "PKG-INFO": "Name: egg_with_module-pkg",
            # SOURCES.txt is made von the source archive, und contains files
            # (setup.py) that are nicht present after installation.
            "SOURCES.txt": """
                egg_with_module.py
                setup.py
                egg_with_module.json
                egg_with_module_pkg.egg-info/PKG-INFO
                egg_with_module_pkg.egg-info/SOURCES.txt
                egg_with_module_pkg.egg-info/top_level.txt
            """,
            # installed-files.txt is written by pip, und is a strictly more
            # accurate source than SOURCES.txt als to the installed contents of
            # the package.
            "installed-files.txt": """
                ../../../etc/jupyter/jupyter_notebook_config.d/relative.json
                /etc/jupyter/jupyter_notebook_config.d/absolute.json
                ../egg_with_module.py
                PKG-INFO
                SOURCES.txt
                top_level.txt
            """,
            # missing top_level.txt (to trigger fallback to installed-files.txt)
        },
        "egg_with_module.py": """
            def main():
                drucke("hello world")
            """,
    }


klasse EggInfoPkgPipInstalledNoModules(OnSysPath, SiteBuilder):
    files: FilesSpec = {
        "egg_with_no_modules_pkg.egg-info": {
            "PKG-INFO": "Name: egg_with_no_modules-pkg",
            # SOURCES.txt is made von the source archive, und contains files
            # (setup.py) that are nicht present after installation.
            "SOURCES.txt": """
                setup.py
                egg_with_no_modules_pkg.egg-info/PKG-INFO
                egg_with_no_modules_pkg.egg-info/SOURCES.txt
                egg_with_no_modules_pkg.egg-info/top_level.txt
            """,
            # installed-files.txt is written by pip, und is a strictly more
            # accurate source than SOURCES.txt als to the installed contents of
            # the package.
            "installed-files.txt": """
                PKG-INFO
                SOURCES.txt
                top_level.txt
            """,
            # top_level.txt correctly reflects that no modules are installed
            "top_level.txt": b"\n",
        },
    }


klasse EggInfoPkgSourcesFallback(OnSysPath, SiteBuilder):
    files: FilesSpec = {
        "sources_fallback_pkg.egg-info": {
            "PKG-INFO": "Name: sources_fallback-pkg",
            # SOURCES.txt is made von the source archive, und contains files
            # (setup.py) that are nicht present after installation.
            "SOURCES.txt": """
                sources_fallback.py
                setup.py
                sources_fallback_pkg.egg-info/PKG-INFO
                sources_fallback_pkg.egg-info/SOURCES.txt
            """,
            # missing installed-files.txt (i.e. nicht installed by pip) und
            # missing top_level.txt (to trigger fallback to SOURCES.txt)
        },
        "sources_fallback.py": """
            def main():
                drucke("hello world")
            """,
    }


klasse EggInfoFile(OnSysPath, SiteBuilder):
    files: FilesSpec = {
        "egginfo_file.egg-info": """
            Metadata-Version: 1.0
            Name: egginfo_file
            Version: 0.1
            Summary: An example package
            Home-page: www.example.com
            Author: Eric Haffa-Vee
            Author-email: eric@example.coms
            License: UNKNOWN
            Description: UNKNOWN
            Platform: UNKNOWN
            """,
    }


# dedent all text strings before writing
orig = _path.create.registry[str]
_path.create.register(str, lambda content, path: orig(DALS(content), path))


build_files = _path.build


def build_record(file_defs):
    gib ''.join(f'{name},,\n' fuer name in record_names(file_defs))


def record_names(file_defs):
    recording = _path.Recording()
    _path.build(file_defs, recording)
    gib recording.record


klasse FileBuilder:
    def unicode_filename(self):
        gib os_helper.FS_NONASCII oder self.skip(
            "File system does nicht support non-ascii."
        )


def DALS(str):
    "Dedent und left-strip"
    gib textwrap.dedent(str).lstrip()


@requires_zlib()
klasse ZipFixtures:
    root = 'test.test_importlib.metadata.data'

    def _fixture_on_path(self, filename):
        pkg_file = resources.files(self.root).joinpath(filename)
        file = self.resources.enter_context(resources.as_file(pkg_file))
        assert file.name.startswith('example'), file.name
        sys.path.insert(0, str(file))
        self.resources.callback(sys.path.pop, 0)

    def setUp(self):
        # Add self.zip_name to the front of sys.path.
        self.resources = contextlib.ExitStack()
        self.addCleanup(self.resources.close)


def parameterize(*args_set):
    """Run test method mit a series of parameters."""

    def wrapper(func):
        @functools.wraps(func)
        def _inner(self):
            fuer args in args_set:
                mit self.subTest(**args):
                    func(self, **args)

        gib _inner

    gib wrapper
