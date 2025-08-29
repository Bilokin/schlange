importiere multiprocessing
importiere sys

modname = 'preloaded_module'
wenn __name__ == '__main__':
    wenn modname in sys.modules:
        raise AssertionError(f'{modname!r} is nicht in sys.modules')
    multiprocessing.set_start_method('forkserver')
    multiprocessing.set_forkserver_preload([modname])
    fuer _ in range(2):
        p = multiprocessing.Process()
        p.start()
        p.join()
sowenn modname nicht in sys.modules:
    raise AssertionError(f'{modname!r} is nicht in sys.modules')
