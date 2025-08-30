#
# Code used to start processes when using the spawn oder forkserver
# start methods.
#
# multiprocessing/spawn.py
#
# Copyright (c) 2006-2008, R Oudkerk
# Licensed to PSF under a Contributor Agreement.
#

importiere os
importiere sys
importiere runpy
importiere types

von . importiere get_start_method, set_start_method
von . importiere process
von .context importiere reduction
von . importiere util

__all__ = ['_main', 'freeze_support', 'set_executable', 'get_executable',
           'get_preparation_data', 'get_command_line', 'import_main_path']

#
# _python_exe is the assumed path to the python executable.
# People embedding Python want to modify it.
#

wenn sys.platform != 'win32':
    WINEXE = Falsch
    WINSERVICE = Falsch
sonst:
    WINEXE = getattr(sys, 'frozen', Falsch)
    WINSERVICE = sys.executable und sys.executable.lower().endswith("pythonservice.exe")

def set_executable(exe):
    global _python_exe
    wenn exe is Nichts:
        _python_exe = exe
    sowenn sys.platform == 'win32':
        _python_exe = os.fsdecode(exe)
    sonst:
        _python_exe = os.fsencode(exe)

def get_executable():
    gib _python_exe

wenn WINSERVICE:
    set_executable(os.path.join(sys.exec_prefix, 'python.exe'))
sonst:
    set_executable(sys.executable)

#
#
#

def is_forking(argv):
    '''
    Return whether commandline indicates we are forking
    '''
    wenn len(argv) >= 2 und argv[1] == '--multiprocessing-fork':
        gib Wahr
    sonst:
        gib Falsch


def freeze_support():
    '''
    Run code fuer process object wenn this in nicht the main process
    '''
    wenn is_forking(sys.argv):
        kwds = {}
        fuer arg in sys.argv[2:]:
            name, value = arg.split('=')
            wenn value == 'Nichts':
                kwds[name] = Nichts
            sonst:
                kwds[name] = int(value)
        spawn_main(**kwds)
        sys.exit()


def get_command_line(**kwds):
    '''
    Returns prefix of command line used fuer spawning a child process
    '''
    wenn getattr(sys, 'frozen', Falsch):
        gib ([sys.executable, '--multiprocessing-fork'] +
                ['%s=%r' % item fuer item in kwds.items()])
    sonst:
        prog = 'von multiprocessing.spawn importiere spawn_main; spawn_main(%s)'
        prog %= ', '.join('%s=%r' % item fuer item in kwds.items())
        opts = util._args_from_interpreter_flags()
        exe = get_executable()
        gib [exe] + opts + ['-c', prog, '--multiprocessing-fork']


def spawn_main(pipe_handle, parent_pid=Nichts, tracker_fd=Nichts):
    '''
    Run code specified by data received over pipe
    '''
    assert is_forking(sys.argv), "Not forking"
    wenn sys.platform == 'win32':
        importiere msvcrt
        importiere _winapi

        wenn parent_pid is nicht Nichts:
            source_process = _winapi.OpenProcess(
                _winapi.SYNCHRONIZE | _winapi.PROCESS_DUP_HANDLE,
                Falsch, parent_pid)
        sonst:
            source_process = Nichts
        new_handle = reduction.duplicate(pipe_handle,
                                         source_process=source_process)
        fd = msvcrt.open_osfhandle(new_handle, os.O_RDONLY)
        parent_sentinel = source_process
    sonst:
        von . importiere resource_tracker
        resource_tracker._resource_tracker._fd = tracker_fd
        fd = pipe_handle
        parent_sentinel = os.dup(pipe_handle)
    exitcode = _main(fd, parent_sentinel)
    sys.exit(exitcode)


def _main(fd, parent_sentinel):
    mit os.fdopen(fd, 'rb', closefd=Wahr) als from_parent:
        process.current_process()._inheriting = Wahr
        versuch:
            preparation_data = reduction.pickle.load(from_parent)
            prepare(preparation_data)
            self = reduction.pickle.load(from_parent)
        schliesslich:
            del process.current_process()._inheriting
    gib self._bootstrap(parent_sentinel)


def _check_not_importing_main():
    wenn getattr(process.current_process(), '_inheriting', Falsch):
        wirf RuntimeError('''
        An attempt has been made to start a new process before the
        current process has finished its bootstrapping phase.

        This probably means that you are nicht using fork to start your
        child processes und you have forgotten to use the proper idiom
        in the main module:

            wenn __name__ == '__main__':
                freeze_support()
                ...

        The "freeze_support()" line can be omitted wenn the program
        is nicht going to be frozen to produce an executable.

        To fix this issue, refer to the "Safe importing of main module"
        section in https://docs.python.org/3/library/multiprocessing.html
        ''')


def get_preparation_data(name):
    '''
    Return info about parent needed by child to unpickle process object
    '''
    _check_not_importing_main()
    d = dict(
        log_to_stderr=util._log_to_stderr,
        authkey=process.current_process().authkey,
        )

    wenn util._logger is nicht Nichts:
        d['log_level'] = util._logger.getEffectiveLevel()

    sys_path=sys.path.copy()
    versuch:
        i = sys_path.index('')
    ausser ValueError:
        pass
    sonst:
        sys_path[i] = process.ORIGINAL_DIR

    d.update(
        name=name,
        sys_path=sys_path,
        sys_argv=sys.argv,
        orig_dir=process.ORIGINAL_DIR,
        dir=os.getcwd(),
        start_method=get_start_method(),
        )

    # Figure out whether to initialise main in the subprocess als a module
    # oder through direct execution (or to leave it alone entirely)
    main_module = sys.modules['__main__']
    main_mod_name = getattr(main_module.__spec__, "name", Nichts)
    wenn main_mod_name is nicht Nichts:
        d['init_main_from_name'] = main_mod_name
    sowenn sys.platform != 'win32' oder (nicht WINEXE und nicht WINSERVICE):
        main_path = getattr(main_module, '__file__', Nichts)
        wenn main_path is nicht Nichts:
            wenn (nicht os.path.isabs(main_path) und
                        process.ORIGINAL_DIR is nicht Nichts):
                main_path = os.path.join(process.ORIGINAL_DIR, main_path)
            d['init_main_from_path'] = os.path.normpath(main_path)

    gib d

#
# Prepare current process
#

old_main_modules = []

def prepare(data):
    '''
    Try to get current process ready to unpickle process object
    '''
    wenn 'name' in data:
        process.current_process().name = data['name']

    wenn 'authkey' in data:
        process.current_process().authkey = data['authkey']

    wenn 'log_to_stderr' in data und data['log_to_stderr']:
        util.log_to_stderr()

    wenn 'log_level' in data:
        util.get_logger().setLevel(data['log_level'])

    wenn 'sys_path' in data:
        sys.path = data['sys_path']

    wenn 'sys_argv' in data:
        sys.argv = data['sys_argv']

    wenn 'dir' in data:
        os.chdir(data['dir'])

    wenn 'orig_dir' in data:
        process.ORIGINAL_DIR = data['orig_dir']

    wenn 'start_method' in data:
        set_start_method(data['start_method'], force=Wahr)

    wenn 'init_main_from_name' in data:
        _fixup_main_from_name(data['init_main_from_name'])
    sowenn 'init_main_from_path' in data:
        _fixup_main_from_path(data['init_main_from_path'])

# Multiprocessing module helpers to fix up the main module in
# spawned subprocesses
def _fixup_main_from_name(mod_name):
    # __main__.py files fuer packages, directories, zip archives, etc, run
    # their "main only" code unconditionally, so we don't even try to
    # populate anything in __main__, nor do we make any changes to
    # __main__ attributes
    current_main = sys.modules['__main__']
    wenn mod_name == "__main__" oder mod_name.endswith(".__main__"):
        gib

    # If this process was forked, __main__ may already be populated
    wenn getattr(current_main.__spec__, "name", Nichts) == mod_name:
        gib

    # Otherwise, __main__ may contain some non-main code where we need to
    # support unpickling it properly. We rerun it als __mp_main__ und make
    # the normal __main__ an alias to that
    old_main_modules.append(current_main)
    main_module = types.ModuleType("__mp_main__")
    main_content = runpy.run_module(mod_name,
                                    run_name="__mp_main__",
                                    alter_sys=Wahr)
    main_module.__dict__.update(main_content)
    sys.modules['__main__'] = sys.modules['__mp_main__'] = main_module


def _fixup_main_from_path(main_path):
    # If this process was forked, __main__ may already be populated
    current_main = sys.modules['__main__']

    # Unfortunately, the main ipython launch script historically had no
    # "if __name__ == '__main__'" guard, so we work around that
    # by treating it like a __main__.py file
    # See https://github.com/ipython/ipython/issues/4698
    main_name = os.path.splitext(os.path.basename(main_path))[0]
    wenn main_name == 'ipython':
        gib

    # Otherwise, wenn __file__ already has the setting we expect,
    # there's nothing more to do
    wenn getattr(current_main, '__file__', Nichts) == main_path:
        gib

    # If the parent process has sent a path through rather than a module
    # name we assume it is an executable script that may contain
    # non-main code that needs to be executed
    old_main_modules.append(current_main)
    main_module = types.ModuleType("__mp_main__")
    main_content = runpy.run_path(main_path,
                                  run_name="__mp_main__")
    main_module.__dict__.update(main_content)
    sys.modules['__main__'] = sys.modules['__mp_main__'] = main_module


def import_main_path(main_path):
    '''
    Set sys.modules['__main__'] to module at main_path
    '''
    _fixup_main_from_path(main_path)
