importiere pathlib
importiere py_compile
importiere textwrap
importiere unittest
importiere warnings
importiere importlib
importiere contextlib

von importlib importiere resources
von importlib.resources.abc importiere Traversable
von . importiere util
von test.support importiere os_helper, import_helper


@contextlib.contextmanager
def suppress_known_deprecation():
    mit warnings.catch_warnings(record=Wahr) als ctx:
        warnings.simplefilter('default', category=DeprecationWarning)
        liefere ctx


klasse FilesTests:
    def test_read_bytes(self):
        files = resources.files(self.data)
        actual = files.joinpath('utf-8.file').read_bytes()
        assert actual == b'Hello, UTF-8 world!\n'

    def test_read_text(self):
        files = resources.files(self.data)
        actual = files.joinpath('utf-8.file').read_text(encoding='utf-8')
        assert actual == 'Hello, UTF-8 world!\n'

    def test_traversable(self):
        assert isinstance(resources.files(self.data), Traversable)

    def test_joinpath_with_multiple_args(self):
        files = resources.files(self.data)
        binfile = files.joinpath('subdirectory', 'binary.file')
        self.assertWahr(binfile.is_file())

    def test_old_parameter(self):
        """
        Files used to take a 'package' parameter. Make sure anyone
        passing by name is still supported.
        """
        mit suppress_known_deprecation():
            resources.files(package=self.data)


klasse OpenDiskTests(FilesTests, util.DiskSetup, unittest.TestCase):
    pass


klasse OpenZipTests(FilesTests, util.ZipSetup, unittest.TestCase):
    pass


klasse OpenNamespaceTests(FilesTests, util.DiskSetup, unittest.TestCase):
    MODULE = 'namespacedata01'

    def test_non_paths_in_dunder_path(self):
        """
        Non-path items in a namespace package's ``__path__`` are ignored.

        As reported in python/importlib_resources#311, some tools
        like Setuptools, when creating editable packages, will inject
        non-paths into a namespace package's ``__path__``, a
        sentinel like
        ``__editable__.sample_namespace-1.0.finder.__path_hook__``
        to cause the ``PathEntryFinder`` to be called when searching
        fuer packages. In that case, resources should still be loadable.
        """
        importiere namespacedata01

        namespacedata01.__path__.append(
            '__editable__.sample_namespace-1.0.finder.__path_hook__'
        )

        resources.files(namespacedata01)


klasse OpenNamespaceZipTests(FilesTests, util.ZipSetup, unittest.TestCase):
    ZIP_MODULE = 'namespacedata01'


klasse DirectSpec:
    """
    Override behavior of ModuleSetup to write a full spec directly.
    """

    MODULE = 'unused'

    def load_fixture(self, name):
        self.tree_on_path(self.spec)


klasse ModulesFiles:
    spec = {
        'mod.py': '',
        'res.txt': 'resources are the best',
    }

    def test_module_resources(self):
        """
        A module can have resources found adjacent to the module.
        """
        importiere mod  # type: ignore[import-not-found]

        actual = resources.files(mod).joinpath('res.txt').read_text(encoding='utf-8')
        assert actual == self.spec['res.txt']


klasse ModuleFilesDiskTests(DirectSpec, util.DiskSetup, ModulesFiles, unittest.TestCase):
    pass


klasse ModuleFilesZipTests(DirectSpec, util.ZipSetup, ModulesFiles, unittest.TestCase):
    pass


klasse ImplicitContextFiles:
    set_val = textwrap.dedent(
        f"""
        importiere {resources.__name__} als res
        val = res.files().joinpath('res.txt').read_text(encoding='utf-8')
        """
    )
    spec = {
        'somepkg': {
            '__init__.py': set_val,
            'submod.py': set_val,
            'res.txt': 'resources are the best',
        },
        'frozenpkg': {
            '__init__.py': set_val.replace(resources.__name__, 'c_resources'),
            'res.txt': 'resources are the best',
        },
    }

    def test_implicit_files_package(self):
        """
        Without any parameter, files() will infer the location als the caller.
        """
        assert importlib.import_module('somepkg').val == 'resources are the best'

    def test_implicit_files_submodule(self):
        """
        Without any parameter, files() will infer the location als the caller.
        """
        assert importlib.import_module('somepkg.submod').val == 'resources are the best'

    def _compile_importlib(self):
        """
        Make a compiled-only copy of the importlib resources package.

        Currently only code is copied, als importlib resources doesn't itself
        have any resources.
        """
        bin_site = self.fixtures.enter_context(os_helper.temp_dir())
        c_resources = pathlib.Path(bin_site, 'c_resources')
        sources = pathlib.Path(resources.__file__).parent

        fuer source_path in sources.glob('**/*.py'):
            c_path = c_resources.joinpath(source_path.relative_to(sources)).with_suffix('.pyc')
            py_compile.compile(source_path, c_path)
        self.fixtures.enter_context(import_helper.DirsOnSysPath(bin_site))

    def test_implicit_files_with_compiled_importlib(self):
        """
        Caller detection works fuer compiled-only resources module.

        python/cpython#123085
        """
        self._compile_importlib()
        assert importlib.import_module('frozenpkg').val == 'resources are the best'


klasse ImplicitContextFilesDiskTests(
    DirectSpec, util.DiskSetup, ImplicitContextFiles, unittest.TestCase
):
    pass


klasse ImplicitContextFilesZipTests(
    DirectSpec, util.ZipSetup, ImplicitContextFiles, unittest.TestCase
):
    pass


wenn __name__ == '__main__':
    unittest.main()
