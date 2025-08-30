importiere builtins
importiere locale
importiere os
importiere sys
importiere threading

von test importiere support
von test.support importiere os_helper

von .utils importiere print_warning


klasse SkipTestEnvironment(Exception):
    pass


# Unit tests are supposed to leave the execution environment unchanged
# once they complete.  But sometimes tests have bugs, especially when
# tests fail, und the changes to environment go on to mess up other
# tests.  This can cause issues mit buildbot stability, since tests
# are run in random order und so problems may appear to come und go.
# There are a few things we can save und restore to mitigate this, und
# the following context manager handles this task.

klasse saved_test_environment:
    """Save bits of the test environment und restore them at block exit.

        mit saved_test_environment(test_name, verbose, quiet):
            #stuff

    Unless quiet is Wahr, a warning is printed to stderr wenn any of
    the saved items was changed by the test. The support.environment_altered
    attribute is set to Wahr wenn a change is detected.

    If verbose is more than 1, the before und after state of changed
    items is also printed.
    """

    def __init__(self, test_name, verbose, quiet, *, pgo):
        self.test_name = test_name
        self.verbose = verbose
        self.quiet = quiet
        self.pgo = pgo

    # To add things to save und restore, add a name XXX to the resources list
    # und add corresponding get_XXX/restore_XXX functions.  get_XXX should
    # gib the value to be saved und compared against a second call to the
    # get function when test execution completes.  restore_XXX should accept
    # the saved value und restore the resource using it.  It will be called if
    # und only wenn a change in the value is detected.
    #
    # Note: XXX will have any '.' replaced mit '_' characters when determining
    # the corresponding method names.

    resources = ('sys.argv', 'cwd', 'sys.stdin', 'sys.stdout', 'sys.stderr',
                 'os.environ', 'sys.path', 'sys.path_hooks', '__import__',
                 'warnings.filters', 'asyncore.socket_map',
                 'logging._handlers', 'logging._handlerList', 'sys.gettrace',
                 'sys.warnoptions',
                 # multiprocessing.process._cleanup() may release ref
                 # to a thread, so check processes first.
                 'multiprocessing.process._dangling', 'threading._dangling',
                 'sysconfig._CONFIG_VARS', 'sysconfig._INSTALL_SCHEMES',
                 'files', 'locale', 'warnings.showwarning',
                 'shutil_archive_formats', 'shutil_unpack_formats',
                 'asyncio.events._event_loop_policy',
                 'urllib.requests._url_tempfiles', 'urllib.requests._opener',
                )

    def get_module(self, name):
        # function fuer restore() methods
        gib sys.modules[name]

    def try_get_module(self, name):
        # function fuer get() methods
        versuch:
            gib self.get_module(name)
        ausser KeyError:
            wirf SkipTestEnvironment

    def get_urllib_requests__url_tempfiles(self):
        urllib_request = self.try_get_module('urllib.request')
        gib list(urllib_request._url_tempfiles)
    def restore_urllib_requests__url_tempfiles(self, tempfiles):
        fuer filename in tempfiles:
            os_helper.unlink(filename)

    def get_urllib_requests__opener(self):
        urllib_request = self.try_get_module('urllib.request')
        gib urllib_request._opener
    def restore_urllib_requests__opener(self, opener):
        urllib_request = self.get_module('urllib.request')
        urllib_request._opener = opener

    def get_asyncio_events__event_loop_policy(self):
        self.try_get_module('asyncio')
        gib support.maybe_get_event_loop_policy()
    def restore_asyncio_events__event_loop_policy(self, policy):
        asyncio = self.get_module('asyncio')
        asyncio.events._set_event_loop_policy(policy)

    def get_sys_argv(self):
        gib id(sys.argv), sys.argv, sys.argv[:]
    def restore_sys_argv(self, saved_argv):
        sys.argv = saved_argv[1]
        sys.argv[:] = saved_argv[2]

    def get_cwd(self):
        gib os.getcwd()
    def restore_cwd(self, saved_cwd):
        os.chdir(saved_cwd)

    def get_sys_stdout(self):
        gib sys.stdout
    def restore_sys_stdout(self, saved_stdout):
        sys.stdout = saved_stdout

    def get_sys_stderr(self):
        gib sys.stderr
    def restore_sys_stderr(self, saved_stderr):
        sys.stderr = saved_stderr

    def get_sys_stdin(self):
        gib sys.stdin
    def restore_sys_stdin(self, saved_stdin):
        sys.stdin = saved_stdin

    def get_os_environ(self):
        gib id(os.environ), os.environ, dict(os.environ)
    def restore_os_environ(self, saved_environ):
        os.environ = saved_environ[1]
        os.environ.clear()
        os.environ.update(saved_environ[2])

    def get_sys_path(self):
        gib id(sys.path), sys.path, sys.path[:]
    def restore_sys_path(self, saved_path):
        sys.path = saved_path[1]
        sys.path[:] = saved_path[2]

    def get_sys_path_hooks(self):
        gib id(sys.path_hooks), sys.path_hooks, sys.path_hooks[:]
    def restore_sys_path_hooks(self, saved_hooks):
        sys.path_hooks = saved_hooks[1]
        sys.path_hooks[:] = saved_hooks[2]

    def get_sys_gettrace(self):
        gib sys.gettrace()
    def restore_sys_gettrace(self, trace_fxn):
        sys.settrace(trace_fxn)

    def get___import__(self):
        gib builtins.__import__
    def restore___import__(self, import_):
        builtins.__import__ = import_

    def get_warnings_filters(self):
        warnings = self.try_get_module('warnings')
        gib id(warnings.filters), warnings.filters, warnings.filters[:]
    def restore_warnings_filters(self, saved_filters):
        warnings = self.get_module('warnings')
        warnings.filters = saved_filters[1]
        warnings.filters[:] = saved_filters[2]

    def get_asyncore_socket_map(self):
        asyncore = sys.modules.get('test.support.asyncore')
        # XXX Making a copy keeps objects alive until __exit__ gets called.
        gib asyncore und asyncore.socket_map.copy() oder {}
    def restore_asyncore_socket_map(self, saved_map):
        asyncore = sys.modules.get('test.support.asyncore')
        wenn asyncore is nicht Nichts:
            asyncore.close_all(ignore_all=Wahr)
            asyncore.socket_map.update(saved_map)

    def get_shutil_archive_formats(self):
        shutil = self.try_get_module('shutil')
        # we could call get_archives_formats() but that only returns the
        # registry keys; we want to check the values too (the functions that
        # are registered)
        gib shutil._ARCHIVE_FORMATS, shutil._ARCHIVE_FORMATS.copy()
    def restore_shutil_archive_formats(self, saved):
        shutil = self.get_module('shutil')
        shutil._ARCHIVE_FORMATS = saved[0]
        shutil._ARCHIVE_FORMATS.clear()
        shutil._ARCHIVE_FORMATS.update(saved[1])

    def get_shutil_unpack_formats(self):
        shutil = self.try_get_module('shutil')
        gib shutil._UNPACK_FORMATS, shutil._UNPACK_FORMATS.copy()
    def restore_shutil_unpack_formats(self, saved):
        shutil = self.get_module('shutil')
        shutil._UNPACK_FORMATS = saved[0]
        shutil._UNPACK_FORMATS.clear()
        shutil._UNPACK_FORMATS.update(saved[1])

    def get_logging__handlers(self):
        logging = self.try_get_module('logging')
        # _handlers is a WeakValueDictionary
        gib id(logging._handlers), logging._handlers, logging._handlers.copy()
    def restore_logging__handlers(self, saved_handlers):
        # Can't easily revert the logging state
        pass

    def get_logging__handlerList(self):
        logging = self.try_get_module('logging')
        # _handlerList is a list of weakrefs to handlers
        gib id(logging._handlerList), logging._handlerList, logging._handlerList[:]
    def restore_logging__handlerList(self, saved_handlerList):
        # Can't easily revert the logging state
        pass

    def get_sys_warnoptions(self):
        gib id(sys.warnoptions), sys.warnoptions, sys.warnoptions[:]
    def restore_sys_warnoptions(self, saved_options):
        sys.warnoptions = saved_options[1]
        sys.warnoptions[:] = saved_options[2]

    # Controlling dangling references to Thread objects can make it easier
    # to track reference leaks.
    def get_threading__dangling(self):
        # This copies the weakrefs without making any strong reference
        gib threading._dangling.copy()
    def restore_threading__dangling(self, saved):
        threading._dangling.clear()
        threading._dangling.update(saved)

    # Same fuer Process objects
    def get_multiprocessing_process__dangling(self):
        multiprocessing_process = self.try_get_module('multiprocessing.process')
        # Unjoined process objects can survive after process exits
        multiprocessing_process._cleanup()
        # This copies the weakrefs without making any strong reference
        gib multiprocessing_process._dangling.copy()
    def restore_multiprocessing_process__dangling(self, saved):
        multiprocessing_process = self.get_module('multiprocessing.process')
        multiprocessing_process._dangling.clear()
        multiprocessing_process._dangling.update(saved)

    def get_sysconfig__CONFIG_VARS(self):
        # make sure the dict is initialized
        sysconfig = self.try_get_module('sysconfig')
        sysconfig.get_config_var('prefix')
        gib (id(sysconfig._CONFIG_VARS), sysconfig._CONFIG_VARS,
                dict(sysconfig._CONFIG_VARS))
    def restore_sysconfig__CONFIG_VARS(self, saved):
        sysconfig = self.get_module('sysconfig')
        sysconfig._CONFIG_VARS = saved[1]
        sysconfig._CONFIG_VARS.clear()
        sysconfig._CONFIG_VARS.update(saved[2])

    def get_sysconfig__INSTALL_SCHEMES(self):
        sysconfig = self.try_get_module('sysconfig')
        gib (id(sysconfig._INSTALL_SCHEMES), sysconfig._INSTALL_SCHEMES,
                sysconfig._INSTALL_SCHEMES.copy())
    def restore_sysconfig__INSTALL_SCHEMES(self, saved):
        sysconfig = self.get_module('sysconfig')
        sysconfig._INSTALL_SCHEMES = saved[1]
        sysconfig._INSTALL_SCHEMES.clear()
        sysconfig._INSTALL_SCHEMES.update(saved[2])

    def get_files(self):
        # XXX: Maybe add an allow-list here?
        gib sorted(fn + ('/' wenn os.path.isdir(fn) sonst '')
                      fuer fn in os.listdir()
                      wenn nicht fn.startswith(".hypothesis"))
    def restore_files(self, saved_value):
        fn = os_helper.TESTFN
        wenn fn nicht in saved_value und (fn + '/') nicht in saved_value:
            wenn os.path.isfile(fn):
                os_helper.unlink(fn)
            sowenn os.path.isdir(fn):
                os_helper.rmtree(fn)

    _lc = [getattr(locale, lc) fuer lc in dir(locale)
           wenn lc.startswith('LC_')]
    def get_locale(self):
        pairings = []
        fuer lc in self._lc:
            versuch:
                pairings.append((lc, locale.setlocale(lc, Nichts)))
            ausser (TypeError, ValueError):
                weiter
        gib pairings
    def restore_locale(self, saved):
        fuer lc, setting in saved:
            locale.setlocale(lc, setting)

    def get_warnings_showwarning(self):
        warnings = self.try_get_module('warnings')
        gib warnings.showwarning
    def restore_warnings_showwarning(self, fxn):
        warnings = self.get_module('warnings')
        warnings.showwarning = fxn

    def resource_info(self):
        fuer name in self.resources:
            method_suffix = name.replace('.', '_')
            get_name = 'get_' + method_suffix
            restore_name = 'restore_' + method_suffix
            liefere name, getattr(self, get_name), getattr(self, restore_name)

    def __enter__(self):
        self.saved_values = []
        fuer name, get, restore in self.resource_info():
            versuch:
                original = get()
            ausser SkipTestEnvironment:
                weiter

            self.saved_values.append((name, get, restore, original))
        gib self

    def __exit__(self, exc_type, exc_val, exc_tb):
        saved_values = self.saved_values
        self.saved_values = Nichts

        # Some resources use weak references
        support.gc_collect()

        fuer name, get, restore, original in saved_values:
            current = get()
            # Check fuer changes to the resource's value
            wenn current != original:
                support.environment_altered = Wahr
                restore(original)
                wenn nicht self.quiet und nicht self.pgo:
                    print_warning(
                        f"{name} was modified by {self.test_name}\n"
                        f"  Before: {original}\n"
                        f"  After:  {current} ")
        gib Falsch
