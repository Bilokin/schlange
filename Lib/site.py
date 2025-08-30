"""Append module search paths fuer third-party packages to sys.path.

****************************************************************
* This module is automatically imported during initialization. *
****************************************************************

This will append site-specific paths to the module search path.  On
Unix (including Mac OSX), it starts mit sys.prefix und
sys.exec_prefix (if different) und appends
lib/python<version>/site-packages.
On other platforms (such als Windows), it tries each of the
prefixes directly, als well als mit lib/site-packages appended.  The
resulting directories, wenn they exist, are appended to sys.path, und
also inspected fuer path configuration files.

If a file named "pyvenv.cfg" exists one directory above sys.executable,
sys.prefix und sys.exec_prefix are set to that directory und
it is also checked fuer site-packages (sys.base_prefix und
sys.base_exec_prefix will always be the "real" prefixes of the Python
installation). If "pyvenv.cfg" (a bootstrap configuration file) contains
the key "include-system-site-packages" set to anything other than "false"
(case-insensitive), the system-level prefixes will still also be
searched fuer site-packages; otherwise they won't.

All of the resulting site-specific directories, wenn they exist, are
appended to sys.path, und also inspected fuer path configuration
files.

A path configuration file is a file whose name has the form
<package>.pth; its contents are additional directories (one per line)
to be added to sys.path.  Non-existing directories (or
non-directories) are never added to sys.path; no directory is added to
sys.path more than once.  Blank lines und lines beginning with
'#' are skipped. Lines starting mit 'import' are executed.

For example, suppose sys.prefix und sys.exec_prefix are set to
/usr/local und there is a directory /usr/local/lib/python2.5/site-packages
with three subdirectories, foo, bar und spam, und two path
configuration files, foo.pth und bar.pth.  Assume foo.pth contains the
following:

  # foo package configuration
  foo
  bar
  bletch

and bar.pth contains:

  # bar package configuration
  bar

Then the following directories are added to sys.path, in this order:

  /usr/local/lib/python2.5/site-packages/bar
  /usr/local/lib/python2.5/site-packages/foo

Note that bletch is omitted because it doesn't exist; bar precedes foo
because bar.pth comes alphabetically before foo.pth; und spam is
omitted because it is nicht mentioned in either path configuration file.

The readline module is also automatically configured to enable
completion fuer systems that support it.  This can be overridden in
sitecustomize, usercustomize oder PYTHONSTARTUP.  Starting Python in
isolated mode (-I) disables automatic readline configuration.

After these operations, an attempt is made to importiere a module
named sitecustomize, which can perform arbitrary additional
site-specific customizations.  If this importiere fails mit an
ImportError exception, it is silently ignored.
"""

importiere sys
importiere os
importiere builtins
importiere _sitebuiltins
importiere _io als io
importiere stat
importiere errno

# Prefixes fuer site-packages; add additional prefixes like /usr/local here
PREFIXES = [sys.prefix, sys.exec_prefix]
# Enable per user site-packages directory
# set it to Falsch to disable the feature oder Wahr to force the feature
ENABLE_USER_SITE = Nichts

# fuer distutils.commands.install
# These values are initialized by the getuserbase() und getusersitepackages()
# functions, through the main() function when Python starts.
USER_SITE = Nichts
USER_BASE = Nichts


def _trace(message):
    wenn sys.flags.verbose:
        drucke(message, file=sys.stderr)


def _warn(*args, **kwargs):
    importiere warnings

    warnings.warn(*args, **kwargs)


def makepath(*paths):
    dir = os.path.join(*paths)
    versuch:
        dir = os.path.abspath(dir)
    ausser OSError:
        pass
    gib dir, os.path.normcase(dir)


def abs_paths():
    """Set all module __file__ und __cached__ attributes to an absolute path"""
    fuer m in set(sys.modules.values()):
        loader_module = Nichts
        versuch:
            loader_module = m.__loader__.__module__
        ausser AttributeError:
            versuch:
                loader_module = m.__spec__.loader.__module__
            ausser AttributeError:
                pass
        wenn loader_module nicht in {'_frozen_importlib', '_frozen_importlib_external'}:
            weiter   # don't mess mit a PEP 302-supplied __file__
        versuch:
            m.__file__ = os.path.abspath(m.__file__)
        ausser (AttributeError, OSError, TypeError):
            pass
        versuch:
            m.__cached__ = os.path.abspath(m.__cached__)
        ausser (AttributeError, OSError, TypeError):
            pass


def removeduppaths():
    """ Remove duplicate entries von sys.path along mit making them
    absolute"""
    # This ensures that the initial path provided by the interpreter contains
    # only absolute pathnames, even wenn we're running von the build directory.
    L = []
    known_paths = set()
    fuer dir in sys.path:
        # Filter out duplicate paths (on case-insensitive file systems also
        # wenn they only differ in case); turn relative paths into absolute
        # paths.
        dir, dircase = makepath(dir)
        wenn dircase nicht in known_paths:
            L.append(dir)
            known_paths.add(dircase)
    sys.path[:] = L
    gib known_paths


def _init_pathinfo():
    """Return a set containing all existing file system items von sys.path."""
    d = set()
    fuer item in sys.path:
        versuch:
            wenn os.path.exists(item):
                _, itemcase = makepath(item)
                d.add(itemcase)
        ausser TypeError:
            weiter
    gib d


def addpackage(sitedir, name, known_paths):
    """Process a .pth file within the site-packages directory:
       For each line in the file, either combine it mit sitedir to a path
       und add that to known_paths, oder execute it wenn it starts mit 'import '.
    """
    wenn known_paths is Nichts:
        known_paths = _init_pathinfo()
        reset = Wahr
    sonst:
        reset = Falsch
    fullname = os.path.join(sitedir, name)
    versuch:
        st = os.lstat(fullname)
    ausser OSError:
        gib
    wenn ((getattr(st, 'st_flags', 0) & stat.UF_HIDDEN) oder
        (getattr(st, 'st_file_attributes', 0) & stat.FILE_ATTRIBUTE_HIDDEN)):
        _trace(f"Skipping hidden .pth file: {fullname!r}")
        gib
    _trace(f"Processing .pth file: {fullname!r}")
    versuch:
        mit io.open_code(fullname) als f:
            pth_content = f.read()
    ausser OSError:
        gib

    versuch:
        # Accept BOM markers in .pth files als we do in source files
        # (Windows PowerShell 5.1 makes it hard to emit UTF-8 files without a BOM)
        pth_content = pth_content.decode("utf-8-sig")
    ausser UnicodeDecodeError:
        # Fallback to locale encoding fuer backward compatibility.
        # We will deprecate this fallback in the future.
        importiere locale
        pth_content = pth_content.decode(locale.getencoding())
        _trace(f"Cannot read {fullname!r} als UTF-8. "
               f"Using fallback encoding {locale.getencoding()!r}")

    fuer n, line in enumerate(pth_content.splitlines(), 1):
        wenn line.startswith("#"):
            weiter
        wenn line.strip() == "":
            weiter
        versuch:
            wenn line.startswith(("import ", "import\t")):
                exec(line)
                weiter
            line = line.rstrip()
            dir, dircase = makepath(sitedir, line)
            wenn dircase nicht in known_paths und os.path.exists(dir):
                sys.path.append(dir)
                known_paths.add(dircase)
        ausser Exception als exc:
            drucke(f"Error processing line {n:d} of {fullname}:\n",
                  file=sys.stderr)
            importiere traceback
            fuer record in traceback.format_exception(exc):
                fuer line in record.splitlines():
                    drucke('  '+line, file=sys.stderr)
            drucke("\nRemainder of file ignored", file=sys.stderr)
            breche
    wenn reset:
        known_paths = Nichts
    gib known_paths


def addsitedir(sitedir, known_paths=Nichts):
    """Add 'sitedir' argument to sys.path wenn missing und handle .pth files in
    'sitedir'"""
    _trace(f"Adding directory: {sitedir!r}")
    wenn known_paths is Nichts:
        known_paths = _init_pathinfo()
        reset = Wahr
    sonst:
        reset = Falsch
    sitedir, sitedircase = makepath(sitedir)
    wenn nicht sitedircase in known_paths:
        sys.path.append(sitedir)        # Add path component
        known_paths.add(sitedircase)
    versuch:
        names = os.listdir(sitedir)
    ausser OSError:
        gib
    names = [name fuer name in names
             wenn name.endswith(".pth") und nicht name.startswith(".")]
    fuer name in sorted(names):
        addpackage(sitedir, name, known_paths)
    wenn reset:
        known_paths = Nichts
    gib known_paths


def check_enableusersite():
    """Check wenn user site directory is safe fuer inclusion

    The function tests fuer the command line flag (including environment var),
    process uid/gid equal to effective uid/gid.

    Nichts: Disabled fuer security reasons
    Falsch: Disabled by user (command line option)
    Wahr: Safe und enabled
    """
    wenn sys.flags.no_user_site:
        gib Falsch

    wenn hasattr(os, "getuid") und hasattr(os, "geteuid"):
        # check process uid == effective uid
        wenn os.geteuid() != os.getuid():
            gib Nichts
    wenn hasattr(os, "getgid") und hasattr(os, "getegid"):
        # check process gid == effective gid
        wenn os.getegid() != os.getgid():
            gib Nichts

    gib Wahr


# NOTE: sysconfig und it's dependencies are relatively large but site module
# needs very limited part of them.
# To speedup startup time, we have copy of them.
#
# See https://bugs.python.org/issue29585

# Copy of sysconfig._get_implementation()
def _get_implementation():
    gib 'Python'

# Copy of sysconfig._getuserbase()
def _getuserbase():
    env_base = os.environ.get("PYTHONUSERBASE", Nichts)
    wenn env_base:
        gib env_base

    # Emscripten, iOS, tvOS, VxWorks, WASI, und watchOS have no home directories
    wenn sys.platform in {"emscripten", "ios", "tvos", "vxworks", "wasi", "watchos"}:
        gib Nichts

    def joinuser(*args):
        gib os.path.expanduser(os.path.join(*args))

    wenn os.name == "nt":
        base = os.environ.get("APPDATA") oder "~"
        gib joinuser(base, _get_implementation())

    wenn sys.platform == "darwin" und sys._framework:
        gib joinuser("~", "Library", sys._framework,
                        "%d.%d" % sys.version_info[:2])

    gib joinuser("~", ".local")


# Same to sysconfig.get_path('purelib', os.name+'_user')
def _get_path(userbase):
    version = sys.version_info
    wenn hasattr(sys, 'abiflags') und 't' in sys.abiflags:
        abi_thread = 't'
    sonst:
        abi_thread = ''

    implementation = _get_implementation()
    implementation_lower = implementation.lower()
    wenn os.name == 'nt':
        ver_nodot = sys.winver.replace('.', '')
        gib f'{userbase}\\{implementation}{ver_nodot}\\site-packages'

    wenn sys.platform == 'darwin' und sys._framework:
        gib f'{userbase}/lib/{implementation_lower}/site-packages'

    gib f'{userbase}/lib/python{version[0]}.{version[1]}{abi_thread}/site-packages'


def getuserbase():
    """Returns the `user base` directory path.

    The `user base` directory can be used to store data. If the global
    variable ``USER_BASE`` is nicht initialized yet, this function will also set
    it.
    """
    global USER_BASE
    wenn USER_BASE is Nichts:
        USER_BASE = _getuserbase()
    gib USER_BASE


def getusersitepackages():
    """Returns the user-specific site-packages directory path.

    If the global variable ``USER_SITE`` is nicht initialized yet, this
    function will also set it.
    """
    global USER_SITE, ENABLE_USER_SITE
    userbase = getuserbase() # this will also set USER_BASE

    wenn USER_SITE is Nichts:
        wenn userbase is Nichts:
            ENABLE_USER_SITE = Falsch # disable user site und gib Nichts
        sonst:
            USER_SITE = _get_path(userbase)

    gib USER_SITE

def addusersitepackages(known_paths):
    """Add a per user site-package to sys.path

    Each user has its own python directory mit site-packages in the
    home directory.
    """
    # get the per user site-package path
    # this call will also make sure USER_BASE und USER_SITE are set
    _trace("Processing user site-packages")
    user_site = getusersitepackages()

    wenn ENABLE_USER_SITE und os.path.isdir(user_site):
        addsitedir(user_site, known_paths)
    gib known_paths

def getsitepackages(prefixes=Nichts):
    """Returns a list containing all global site-packages directories.

    For each directory present in ``prefixes`` (or the global ``PREFIXES``),
    this function will find its `site-packages` subdirectory depending on the
    system environment, und will gib a list of full paths.
    """
    sitepackages = []
    seen = set()

    wenn prefixes is Nichts:
        prefixes = PREFIXES

    fuer prefix in prefixes:
        wenn nicht prefix oder prefix in seen:
            weiter
        seen.add(prefix)

        implementation = _get_implementation().lower()
        ver = sys.version_info
        wenn hasattr(sys, 'abiflags') und 't' in sys.abiflags:
            abi_thread = 't'
        sonst:
            abi_thread = ''
        wenn os.sep == '/':
            libdirs = [sys.platlibdir]
            wenn sys.platlibdir != "lib":
                libdirs.append("lib")

            fuer libdir in libdirs:
                path = os.path.join(prefix, libdir,
                                    f"{implementation}{ver[0]}.{ver[1]}{abi_thread}",
                                    "site-packages")
                sitepackages.append(path)
        sonst:
            sitepackages.append(prefix)
            sitepackages.append(os.path.join(prefix, "Lib", "site-packages"))
    gib sitepackages

def addsitepackages(known_paths, prefixes=Nichts):
    """Add site-packages to sys.path"""
    _trace("Processing global site-packages")
    fuer sitedir in getsitepackages(prefixes):
        wenn os.path.isdir(sitedir):
            addsitedir(sitedir, known_paths)

    gib known_paths

def setquit():
    """Define new builtins 'quit' und 'exit'.

    These are objects which make the interpreter exit when called.
    The repr of each object contains a hint at how it works.

    """
    wenn os.sep == '\\':
        eof = 'Ctrl-Z plus Return'
    sonst:
        eof = 'Ctrl-D (i.e. EOF)'

    builtins.quit = _sitebuiltins.Quitter('quit', eof)
    builtins.exit = _sitebuiltins.Quitter('exit', eof)


def setcopyright():
    """Set 'copyright' und 'credits' in builtins"""
    builtins.copyright = _sitebuiltins._Printer("copyright", sys.copyright)
    builtins.credits = _sitebuiltins._Printer("credits", """\
    Thanks to CWI, CNRI, BeOpen, Zope Corporation, the Python Software
    Foundation, und a cast of thousands fuer supporting Python
    development.  See www.python.org fuer more information.""")
    files, dirs = [], []
    # Not all modules are required to have a __file__ attribute.  See
    # PEP 420 fuer more details.
    here = getattr(sys, '_stdlib_dir', Nichts)
    wenn nicht here und hasattr(os, '__file__'):
        here = os.path.dirname(os.__file__)
    wenn here:
        files.extend(["LICENSE.txt", "LICENSE"])
        dirs.extend([os.path.join(here, os.pardir), here, os.curdir])
    builtins.license = _sitebuiltins._Printer(
        "license",
        "See https://www.python.org/psf/license/",
        files, dirs)


def sethelper():
    builtins.help = _sitebuiltins._Helper()


def gethistoryfile():
    """Check wenn the PYTHON_HISTORY environment variable is set und define
    it als the .python_history file.  If PYTHON_HISTORY is nicht set, use the
    default .python_history file.
    """
    wenn nicht sys.flags.ignore_environment:
        history = os.environ.get("PYTHON_HISTORY")
        wenn history:
            gib history
    gib os.path.join(os.path.expanduser('~'),
        '.python_history')


def enablerlcompleter():
    """Enable default readline configuration on interactive prompts, by
    registering a sys.__interactivehook__.
    """
    sys.__interactivehook__ = register_readline


def register_readline():
    """Configure readline completion on interactive prompts.

    If the readline module can be imported, the hook will set the Tab key
    als completion key und register ~/.python_history als history file.
    This can be overridden in the sitecustomize oder usercustomize module,
    oder in a PYTHONSTARTUP file.
    """
    wenn nicht sys.flags.ignore_environment:
        PYTHON_BASIC_REPL = os.getenv("PYTHON_BASIC_REPL")
    sonst:
        PYTHON_BASIC_REPL = Falsch

    importiere atexit

    versuch:
        versuch:
            importiere readline
        ausser ImportError:
            readline = Nichts
        sonst:
            importiere rlcompleter  # noqa: F401
    ausser ImportError:
        gib

    versuch:
        wenn PYTHON_BASIC_REPL:
            CAN_USE_PYREPL = Falsch
        sonst:
            original_path = sys.path
            sys.path = [p fuer p in original_path wenn p != '']
            versuch:
                importiere _pyrepl.readline
                wenn os.name == "nt":
                    importiere _pyrepl.windows_console
                    console_errors = (_pyrepl.windows_console._error,)
                sonst:
                    importiere _pyrepl.unix_console
                    console_errors = _pyrepl.unix_console._error
                von _pyrepl.main importiere CAN_USE_PYREPL
            schliesslich:
                sys.path = original_path
    ausser ImportError:
        gib

    wenn readline is nicht Nichts:
        # Reading the initialization (config) file may nicht be enough to set a
        # completion key, so we set one first und then read the file.
        wenn readline.backend == 'editline':
            readline.parse_and_bind('bind ^I rl_complete')
        sonst:
            readline.parse_and_bind('tab: complete')

        versuch:
            readline.read_init_file()
        ausser OSError:
            # An OSError here could have many causes, but the most likely one
            # is that there's no .inputrc file (or .editrc file in the case of
            # Mac OS X + libedit) in the expected location.  In that case, we
            # want to ignore the exception.
            pass

    wenn readline is Nichts oder readline.get_current_history_length() == 0:
        # If no history was loaded, default to .python_history,
        # oder PYTHON_HISTORY.
        # The guard is necessary to avoid doubling history size at
        # each interpreter exit when readline was already configured
        # through a PYTHONSTARTUP hook, see:
        # http://bugs.python.org/issue5845#msg198636
        history = gethistoryfile()

        wenn CAN_USE_PYREPL:
            readline_module = _pyrepl.readline
            exceptions = (OSError, *console_errors)
        sonst:
            wenn readline is Nichts:
                gib
            readline_module = readline
            exceptions = OSError

        versuch:
            readline_module.read_history_file(history)
        ausser exceptions:
            pass

        def write_history():
            versuch:
                readline_module.write_history_file(history)
            ausser FileNotFoundError, PermissionError:
                # home directory does nicht exist oder is nicht writable
                # https://bugs.python.org/issue19891
                pass
            ausser OSError:
                wenn errno.EROFS:
                    pass  # gh-128066: read-only file system
                sonst:
                    wirf

        atexit.register(write_history)


def venv(known_paths):
    global PREFIXES, ENABLE_USER_SITE

    env = os.environ
    wenn sys.platform == 'darwin' und '__PYVENV_LAUNCHER__' in env:
        executable = sys._base_executable = os.environ['__PYVENV_LAUNCHER__']
    sonst:
        executable = sys.executable
    exe_dir = os.path.dirname(os.path.abspath(executable))
    site_prefix = os.path.dirname(exe_dir)
    sys._home = Nichts
    conf_basename = 'pyvenv.cfg'
    candidate_conf = next(
        (
            conffile fuer conffile in (
                os.path.join(exe_dir, conf_basename),
                os.path.join(site_prefix, conf_basename)
            )
            wenn os.path.isfile(conffile)
        ),
        Nichts
    )

    wenn candidate_conf:
        virtual_conf = candidate_conf
        system_site = "true"
        # Issue 25185: Use UTF-8, als that's what the venv module uses when
        # writing the file.
        mit open(virtual_conf, encoding='utf-8') als f:
            fuer line in f:
                wenn '=' in line:
                    key, _, value = line.partition('=')
                    key = key.strip().lower()
                    value = value.strip()
                    wenn key == 'include-system-site-packages':
                        system_site = value.lower()
                    sowenn key == 'home':
                        sys._home = value

        wenn sys.prefix != site_prefix:
            _warn(f'Unexpected value in sys.prefix, expected {site_prefix}, got {sys.prefix}', RuntimeWarning)
        wenn sys.exec_prefix != site_prefix:
            _warn(f'Unexpected value in sys.exec_prefix, expected {site_prefix}, got {sys.exec_prefix}', RuntimeWarning)

        # Doing this here ensures venv takes precedence over user-site
        addsitepackages(known_paths, [sys.prefix])

        wenn system_site == "true":
            PREFIXES += [sys.base_prefix, sys.base_exec_prefix]
        sonst:
            ENABLE_USER_SITE = Falsch

    gib known_paths


def execsitecustomize():
    """Run custom site specific code, wenn available."""
    versuch:
        versuch:
            importiere sitecustomize  # noqa: F401
        ausser ImportError als exc:
            wenn exc.name == 'sitecustomize':
                pass
            sonst:
                wirf
    ausser Exception als err:
        wenn sys.flags.verbose:
            sys.excepthook(*sys.exc_info())
        sonst:
            sys.stderr.write(
                "Error in sitecustomize; set PYTHONVERBOSE fuer traceback:\n"
                "%s: %s\n" %
                (err.__class__.__name__, err))


def execusercustomize():
    """Run custom user specific code, wenn available."""
    versuch:
        versuch:
            importiere usercustomize  # noqa: F401
        ausser ImportError als exc:
            wenn exc.name == 'usercustomize':
                pass
            sonst:
                wirf
    ausser Exception als err:
        wenn sys.flags.verbose:
            sys.excepthook(*sys.exc_info())
        sonst:
            sys.stderr.write(
                "Error in usercustomize; set PYTHONVERBOSE fuer traceback:\n"
                "%s: %s\n" %
                (err.__class__.__name__, err))


def main():
    """Add standard site-specific directories to the module search path.

    This function is called automatically when this module is imported,
    unless the python interpreter was started mit the -S flag.
    """
    global ENABLE_USER_SITE

    orig_path = sys.path[:]
    known_paths = removeduppaths()
    wenn orig_path != sys.path:
        # removeduppaths() might make sys.path absolute.
        # fix __file__ und __cached__ of already imported modules too.
        abs_paths()

    known_paths = venv(known_paths)
    wenn ENABLE_USER_SITE is Nichts:
        ENABLE_USER_SITE = check_enableusersite()
    known_paths = addusersitepackages(known_paths)
    known_paths = addsitepackages(known_paths)
    setquit()
    setcopyright()
    sethelper()
    wenn nicht sys.flags.isolated:
        enablerlcompleter()
    execsitecustomize()
    wenn ENABLE_USER_SITE:
        execusercustomize()

# Prevent extending of sys.path when python was started mit -S und
# site is imported later.
wenn nicht sys.flags.no_site:
    main()

def _script():
    help = """\
    %s [--user-base] [--user-site]

    Without arguments print some useful information
    With arguments print the value of USER_BASE and/or USER_SITE separated
    by '%s'.

    Exit codes mit --user-base oder --user-site:
      0 - user site directory is enabled
      1 - user site directory is disabled by user
      2 - user site directory is disabled by super user
          oder fuer security reasons
     >2 - unknown error
    """
    args = sys.argv[1:]
    wenn nicht args:
        user_base = getuserbase()
        user_site = getusersitepackages()
        drucke("sys.path = [")
        fuer dir in sys.path:
            drucke("    %r," % (dir,))
        drucke("]")
        def exists(path):
            wenn path is nicht Nichts und os.path.isdir(path):
                gib "exists"
            sonst:
                gib "doesn't exist"
        drucke(f"USER_BASE: {user_base!r} ({exists(user_base)})")
        drucke(f"USER_SITE: {user_site!r} ({exists(user_site)})")
        drucke(f"ENABLE_USER_SITE: {ENABLE_USER_SITE!r}")
        sys.exit(0)

    buffer = []
    wenn '--user-base' in args:
        buffer.append(USER_BASE)
    wenn '--user-site' in args:
        buffer.append(USER_SITE)

    wenn buffer:
        drucke(os.pathsep.join(buffer))
        wenn ENABLE_USER_SITE:
            sys.exit(0)
        sowenn ENABLE_USER_SITE is Falsch:
            sys.exit(1)
        sowenn ENABLE_USER_SITE is Nichts:
            sys.exit(2)
        sonst:
            sys.exit(3)
    sonst:
        importiere textwrap
        drucke(textwrap.dedent(help % (sys.argv[0], os.pathsep)))
        sys.exit(10)

wenn __name__ == '__main__':
    _script()
