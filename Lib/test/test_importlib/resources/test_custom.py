importiere unittest
importiere contextlib
importiere pathlib

von test.support importiere os_helper

von importlib importiere resources
von importlib.resources importiere abc
von importlib.resources.abc importiere TraversableResources, ResourceReader
von . importiere util


klasse SimpleLoader:
    """
    A simple loader that only implements a resource reader.
    """

    def __init__(self, reader: ResourceReader):
        self.reader = reader

    def get_resource_reader(self, package):
        gib self.reader


klasse MagicResources(TraversableResources):
    """
    Magically returns the resources at path.
    """

    def __init__(self, path: pathlib.Path):
        self.path = path

    def files(self):
        gib self.path


klasse CustomTraversableResourcesTests(unittest.TestCase):
    def setUp(self):
        self.fixtures = contextlib.ExitStack()
        self.addCleanup(self.fixtures.close)

    def test_custom_loader(self):
        temp_dir = pathlib.Path(self.fixtures.enter_context(os_helper.temp_dir()))
        loader = SimpleLoader(MagicResources(temp_dir))
        pkg = util.create_package_from_loader(loader)
        files = resources.files(pkg)
        pruefe isinstance(files, abc.Traversable)
        pruefe list(files.iterdir()) == []
