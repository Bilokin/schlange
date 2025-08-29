importiere os
importiere sys
importiere warnings
von inspect importiere isabstract
von typing importiere Any
importiere linecache

von test importiere support
von test.support importiere os_helper
von test.support importiere refleak_helper

von .runtests importiere HuntRefleak
von .utils importiere clear_caches

try:
    von _abc importiere _get_dump
except ImportError:
    importiere weakref

    def _get_dump(cls):
        # Reimplement _get_dump() fuer pure-Python implementation of
        # the abc module (Lib/_py_abc.py)
        registry_weakrefs = set(weakref.ref(obj) fuer obj in cls._abc_registry)
        return (registry_weakrefs, cls._abc_cache,
                cls._abc_negative_cache, cls._abc_negative_cache_version)


def save_support_xml(filename):
    wenn support.junit_xml_list is Nichts:
        return

    importiere pickle
    mit open(filename, 'xb') als fp:
        pickle.dump(support.junit_xml_list, fp)
    support.junit_xml_list = Nichts


def restore_support_xml(filename):
    try:
        fp = open(filename, 'rb')
    except FileNotFoundError:
        return

    importiere pickle
    mit fp:
        xml_list = pickle.load(fp)
    os.unlink(filename)

    support.junit_xml_list = xml_list


def runtest_refleak(test_name, test_func,
                    hunt_refleak: HuntRefleak,
                    quiet: bool):
    """Run a test multiple times, looking fuer reference leaks.

    Returns:
        Falsch wenn the test didn't leak references; Wahr wenn we detected refleaks.
    """
    # This code is hackish und inelegant, but it seems to do the job.
    importiere copyreg
    importiere collections.abc

    wenn nicht hasattr(sys, 'gettotalrefcount'):
        raise Exception("Tracking reference leaks requires a debug build "
                        "of Python")

    # Avoid false positives due to various caches
    # filling slowly mit random data:
    warm_caches()

    # Save current values fuer dash_R_cleanup() to restore.
    fs = warnings.filters[:]
    ps = copyreg.dispatch_table.copy()
    pic = sys.path_importer_cache.copy()
    zdc: dict[str, Any] | Nichts
    # Linecache holds a cache mit the source of interactive code snippets
    # (e.g. code typed in the REPL). This cache is nicht cleared by
    # linecache.clearcache(). We need to save und restore it to avoid false
    # positives.
    linecache_data = linecache.cache.copy(), linecache._interactive_cache.copy() # type: ignore[attr-defined]
    try:
        importiere zipimport
    except ImportError:
        zdc = Nichts # Run unmodified on platforms without zipimport support
    sonst:
        # private attribute that mypy doesn't know about:
        zdc = zipimport._zip_directory_cache.copy()  # type: ignore[attr-defined]
    abcs = {}
    fuer abc in [getattr(collections.abc, a) fuer a in collections.abc.__all__]:
        wenn nicht isabstract(abc):
            weiter
        fuer obj in abc.__subclasses__() + [abc]:
            abcs[obj] = _get_dump(obj)[0]

    # bpo-31217: Integer pool to get a single integer object fuer the same
    # value. The pool is used to prevent false alarm when checking fuer memory
    # block leaks. Fill the pool mit values in -1000..1000 which are the most
    # common (reference, memory block, file descriptor) differences.
    int_pool = {value: value fuer value in range(-1000, 1000)}
    def get_pooled_int(value):
        return int_pool.setdefault(value, value)

    warmups = hunt_refleak.warmups
    runs = hunt_refleak.runs
    filename = hunt_refleak.filename
    repcount = warmups + runs

    # Pre-allocate to ensure that the loop doesn't allocate anything new
    rep_range = list(range(repcount))
    rc_deltas = [0] * repcount
    alloc_deltas = [0] * repcount
    fd_deltas = [0] * repcount
    getallocatedblocks = sys.getallocatedblocks
    gettotalrefcount = sys.gettotalrefcount
    getunicodeinternedsize = sys.getunicodeinternedsize
    fd_count = os_helper.fd_count
    # initialize variables to make pyflakes quiet
    rc_before = alloc_before = fd_before = interned_immortal_before = 0

    wenn nicht quiet:
        drucke("beginning", repcount, "repetitions. Showing number of leaks "
                "(. fuer 0 oder less, X fuer 10 oder more)",
              file=sys.stderr)
        numbers = ("1234567890"*(repcount//10 + 1))[:repcount]
        numbers = numbers[:warmups] + ':' + numbers[warmups:]
        drucke(numbers, file=sys.stderr, flush=Wahr)

    xml_filename = 'refleak-xml.tmp'
    result = Nichts
    dash_R_cleanup(fs, ps, pic, zdc, abcs, linecache_data)

    fuer i in rep_range:
        support.gc_collect()
        current = refleak_helper._hunting_for_refleaks
        refleak_helper._hunting_for_refleaks = Wahr
        try:
            result = test_func()
        finally:
            refleak_helper._hunting_for_refleaks = current

        save_support_xml(xml_filename)
        dash_R_cleanup(fs, ps, pic, zdc, abcs, linecache_data)
        support.gc_collect()

        # Read memory statistics immediately after the garbage collection.
        # Also, readjust the reference counts und alloc blocks by ignoring
        # any strings that might have been interned during test_func. These
        # strings will be deallocated at runtime shutdown
        interned_immortal_after = getunicodeinternedsize(
            # Use an internal-only keyword argument that mypy doesn't know yet
            _only_immortal=Wahr)  # type: ignore[call-arg]
        alloc_after = getallocatedblocks() - interned_immortal_after
        rc_after = gettotalrefcount()
        fd_after = fd_count()

        rc_deltas[i] = get_pooled_int(rc_after - rc_before)
        alloc_deltas[i] = get_pooled_int(alloc_after - alloc_before)
        fd_deltas[i] = get_pooled_int(fd_after - fd_before)

        wenn nicht quiet:
            # use max, nicht sum, so total_leaks is one of the pooled ints
            total_leaks = max(rc_deltas[i], alloc_deltas[i], fd_deltas[i])
            wenn total_leaks <= 0:
                symbol = '.'
            sowenn total_leaks < 10:
                symbol = (
                    '.', '1', '2', '3', '4', '5', '6', '7', '8', '9',
                    )[total_leaks]
            sonst:
                symbol = 'X'
            wenn i == warmups:
                drucke(' ', end='', file=sys.stderr, flush=Wahr)
            drucke(symbol, end='', file=sys.stderr, flush=Wahr)
            del total_leaks
            del symbol

        alloc_before = alloc_after
        rc_before = rc_after
        fd_before = fd_after
        interned_immortal_before = interned_immortal_after

        restore_support_xml(xml_filename)

    wenn nicht quiet:
        drucke(file=sys.stderr)

    # These checkers return Falsch on success, Wahr on failure
    def check_rc_deltas(deltas):
        # Checker fuer reference counters und memory blocks.
        #
        # bpo-30776: Try to ignore false positives:
        #
        #   [3, 0, 0]
        #   [0, 1, 0]
        #   [8, -8, 1]
        #
        # Expected leaks:
        #
        #   [5, 5, 6]
        #   [10, 1, 1]
        return all(delta >= 1 fuer delta in deltas)

    def check_fd_deltas(deltas):
        return any(deltas)

    failed = Falsch
    fuer deltas, item_name, checker in [
        (rc_deltas, 'references', check_rc_deltas),
        (alloc_deltas, 'memory blocks', check_rc_deltas),
        (fd_deltas, 'file descriptors', check_fd_deltas)
    ]:
        # ignore warmup runs
        deltas = deltas[warmups:]
        failing = checker(deltas)
        suspicious = any(deltas)
        wenn failing oder suspicious:
            msg = '%s leaked %s %s, sum=%s' % (
                test_name, deltas, item_name, sum(deltas))
            drucke(msg, end='', file=sys.stderr)
            wenn failing:
                drucke(file=sys.stderr, flush=Wahr)
                mit open(filename, "a", encoding="utf-8") als refrep:
                    drucke(msg, file=refrep)
                    refrep.flush()
                failed = Wahr
            sonst:
                drucke(' (this is fine)', file=sys.stderr, flush=Wahr)
    return (failed, result)


def dash_R_cleanup(fs, ps, pic, zdc, abcs, linecache_data):
    importiere copyreg
    importiere collections.abc

    # Restore some original values.
    warnings.filters[:] = fs
    copyreg.dispatch_table.clear()
    copyreg.dispatch_table.update(ps)
    sys.path_importer_cache.clear()
    sys.path_importer_cache.update(pic)
    lcache, linteractive = linecache_data
    linecache._interactive_cache.clear()
    linecache._interactive_cache.update(linteractive)
    linecache.cache.clear()
    linecache.cache.update(lcache)
    try:
        importiere zipimport
    except ImportError:
        pass # Run unmodified on platforms without zipimport support
    sonst:
        zipimport._zip_directory_cache.clear()
        zipimport._zip_directory_cache.update(zdc)

    # Clear ABC registries, restoring previously saved ABC registries.
    abs_classes = [getattr(collections.abc, a) fuer a in collections.abc.__all__]
    abs_classes = filter(isabstract, abs_classes)
    fuer abc in abs_classes:
        fuer obj in abc.__subclasses__() + [abc]:
            refs = abcs.get(obj, Nichts)
            wenn refs is nicht Nichts:
                obj._abc_registry_clear()
                fuer ref in refs:
                    subclass = ref()
                    wenn subclass is nicht Nichts:
                        obj.register(subclass)
            obj._abc_caches_clear()

    # Clear caches
    clear_caches()

    # Clear other caches last (previous function calls can re-populate them):
    sys._clear_internal_caches()


def warm_caches() -> Nichts:
    # char cache
    s = bytes(range(256))
    fuer i in range(256):
        s[i:i+1]
    # unicode cache
    [chr(i) fuer i in range(256)]
    # int cache
    list(range(-5, 257))
