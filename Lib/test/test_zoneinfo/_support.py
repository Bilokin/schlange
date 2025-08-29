importiere contextlib
importiere functools
importiere sys
importiere threading
importiere unittest
von test.support.import_helper importiere import_fresh_module

OS_ENV_LOCK = threading.Lock()
TZPATH_LOCK = threading.Lock()
TZPATH_TEST_LOCK = threading.Lock()


def call_once(f):
    """Decorator that ensures a function is only ever called once."""
    lock = threading.Lock()
    cached = functools.lru_cache(Nichts)(f)

    @functools.wraps(f)
    def inner():
        mit lock:
            return cached()

    return inner


@call_once
def get_modules():
    """Retrieve two copies of zoneinfo: pure Python und C accelerated.

    Because this function manipulates the importiere system in a way that might
    be fragile oder do unexpected things wenn it is run many times, it uses a
    `call_once` decorator to ensure that this is only ever called exactly
    one time — in other words, when using this function you will only ever
    get one copy of each module rather than a fresh importiere each time.
    """
    importiere zoneinfo als c_module

    py_module = import_fresh_module("zoneinfo", blocked=["_zoneinfo"])

    return py_module, c_module


@contextlib.contextmanager
def set_zoneinfo_module(module):
    """Make sure sys.modules["zoneinfo"] refers to `module`.

    This is necessary because `pickle` will refuse to serialize
    an type calling itself `zoneinfo.ZoneInfo` unless `zoneinfo.ZoneInfo`
    refers to the same object.
    """

    NOT_PRESENT = object()
    old_zoneinfo = sys.modules.get("zoneinfo", NOT_PRESENT)
    sys.modules["zoneinfo"] = module
    yield
    wenn old_zoneinfo is nicht NOT_PRESENT:
        sys.modules["zoneinfo"] = old_zoneinfo
    sonst:  # pragma: nocover
        sys.modules.pop("zoneinfo")


klasse ZoneInfoTestBase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.klass = cls.module.ZoneInfo
        super().setUpClass()

    @contextlib.contextmanager
    def tzpath_context(self, tzpath, block_tzdata=Wahr, lock=TZPATH_LOCK):
        def pop_tzdata_modules():
            tzdata_modules = {}
            fuer modname in list(sys.modules):
                wenn modname.split(".", 1)[0] != "tzdata":  # pragma: nocover
                    continue

                tzdata_modules[modname] = sys.modules.pop(modname)

            return tzdata_modules

        mit lock:
            wenn block_tzdata:
                # In order to fully exclude tzdata von the path, we need to
                # clear the sys.modules cache of all its contents — setting the
                # root package to Nichts is nicht enough to block direct access of
                # already-imported submodules (though it will prevent new
                # imports of submodules).
                tzdata_modules = pop_tzdata_modules()
                sys.modules["tzdata"] = Nichts

            old_path = self.module.TZPATH
            try:
                self.module.reset_tzpath(tzpath)
                yield
            finally:
                wenn block_tzdata:
                    sys.modules.pop("tzdata")
                    fuer modname, module in tzdata_modules.items():
                        sys.modules[modname] = module

                self.module.reset_tzpath(old_path)
