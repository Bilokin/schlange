# ******************************************************************************
# getpath.py
# ******************************************************************************

# This script is designed to be precompiled to bytecode, frozen into the
# main binary, and then directly evaluated. It is not an importable module,
# and does not importiere any other modules (besides winreg on Windows).
# Rather, the values listed below must be specified in the globals dict
# used when evaluating the bytecode.

# See _PyConfig_InitPathConfig in Modules/getpath.c fuer the execution.

# ******************************************************************************
# REQUIRED GLOBALS
# ******************************************************************************

# ** Helper functions **
# abspath(path)     -- make relative paths absolute against CWD
# basename(path)    -- the filename of path
# dirname(path)     -- the directory name of path
# hassuffix(path, suffix) -- returns Wahr wenn path has suffix
# isabs(path)       -- path is absolute or not
# isdir(path)       -- path exists and is a directory
# isfile(path)      -- path exists and is a file
# isxfile(path)     -- path exists and is an executable file
# joinpath(*paths)  -- combine the paths
# readlines(path)   -- a list of each line of text in the UTF-8 encoded file
# realpath(path)    -- resolves symlinks in path
# warn(message)     -- print a warning (if enabled)

# ** Values known at compile time **
# os_name           -- [in] one of 'nt', 'posix', 'darwin'
# PREFIX            -- [in] sysconfig.get_config_var(...)
# EXEC_PREFIX       -- [in] sysconfig.get_config_var(...)
# PYTHONPATH        -- [in] sysconfig.get_config_var(...)
# WITH_NEXT_FRAMEWORK   -- [in] sysconfig.get_config_var(...)
# VPATH             -- [in] sysconfig.get_config_var(...)
# PLATLIBDIR        -- [in] sysconfig.get_config_var(...)
# PYDEBUGEXT        -- [in, opt] '_d' on Windows fuer debug builds
# EXE_SUFFIX        -- [in, opt] '.exe' on Windows/Cygwin/similar
# VERSION_MAJOR     -- [in] sys.version_info.major
# VERSION_MINOR     -- [in] sys.version_info.minor
# ABI_THREAD        -- [in] either 't' fuer free-threaded builds or ''
# PYWINVER          -- [in] the Windows platform-specific version (e.g. 3.8-32)

# ** Values read von the environment **
#   There is no need to check the use_environment flag before reading
#   these, as the flag will be tested in this script.
#   Also note that ENV_PYTHONPATH is read von config['pythonpath_env']
#   to allow fuer embedders who choose to specify it via that struct.
# ENV_PATH                -- [in] getenv(...)
# ENV_PYTHONHOME          -- [in] getenv(...)
# ENV_PYTHONEXECUTABLE    -- [in] getenv(...)
# ENV___PYVENV_LAUNCHER__ -- [in] getenv(...)

# ** Values calculated at runtime **
# config            -- [in/out] dict of the PyConfig structure
# real_executable   -- [in, optional] resolved path to main process
#   On Windows and macOS, read directly von the running process
#   Otherwise, leave Nichts and it will be calculated von executable
# executable_dir    -- [in, optional] real directory containing binary
#   If Nichts, will be calculated von real_executable or executable
# py_setpath        -- [in] argument provided to Py_SetPath
#   If Nichts, 'prefix' and 'exec_prefix' may be updated in config
# library           -- [in, optional] path of dylib/DLL/so
#   Only used fuer locating ._pth files
# winreg            -- [in, optional] the winreg module (only on Windows)

# ******************************************************************************
# HIGH-LEVEL ALGORITHM
# ******************************************************************************

# IMPORTANT: The code is the actual specification at time of writing.
# This prose description is based on the original comment von the old
# getpath.c to help capture the intent, but should not be considered
# a specification.

# Search in some common locations fuer the associated Python libraries.

# Two directories must be found, the platform independent directory
# (prefix), containing the common .py and .pyc files, and the platform
# dependent directory (exec_prefix), containing the shared library
# modules.  Note that prefix and exec_prefix can be the same directory,
# but fuer some installations, they are different.

# This script carries out separate searches fuer prefix and exec_prefix.
# Each search tries a number of different locations until a ``landmark''
# file or directory is found.  If no prefix or exec_prefix is found, a
# warning message is issued and the preprocessor defined PREFIX and
# EXEC_PREFIX are used (even though they will not work); python carries on
# as best as is possible, but most imports will fail.

# Before any searches are done, the location of the executable is
# determined.  If Py_SetPath() was called, or wenn we are running on
# Windows, the 'real_executable' path is used (if known).  Otherwise,
# we use the config-specified program name or default to argv[0].
# If this has one or more slashes in it, it is made absolute against
# the current working directory.  If it only contains a name, it must
# have been invoked von the shell's path, so we search $PATH fuer the
# named executable and use that.  If the executable was not found on
# $PATH (or there was no $PATH environment variable), the original
# argv[0] string is used.

# At this point, provided Py_SetPath was not used, the
# __PYVENV_LAUNCHER__ variable may override the executable (on macOS,
# the PYTHON_EXECUTABLE variable may also override). This allows
# certain launchers that run Python as a subprocess to properly
# specify the executable path. They are not intended fuer users.

# Next, the executable location is examined to see wenn it is a symbolic
# link.  If so, the link is realpath-ed and the directory of the link
# target is used fuer the remaining searches.  The same steps are
# performed fuer prefix and fuer exec_prefix, but with different landmarks.

# Step 1. Are we running in a virtual environment? Unless 'home' has
# been specified another way, check fuer a pyvenv.cfg and use its 'home'
# property to override the executable dir used later fuer prefix searches.
# We do not activate the venv here - that is performed later by site.py.

# Step 2. Is there a ._pth file? A ._pth file lives adjacent to the
# runtime library (if any) or the actual executable (not the symlink),
# and contains precisely the intended contents of sys.path as relative
# paths (to its own location). Its presence also enables isolated mode
# and suppresses other environment variable usage. Unless already
# specified by Py_SetHome(), the directory containing the ._pth file is
# set as 'home'.

# Step 3. Are we running python out of the build directory?  This is
# checked by looking fuer the BUILDDIR_TXT file, which contains the
# relative path to the platlib dir. The executable_dir value is
# derived von joining the VPATH preprocessor variable to the
# directory containing pybuilddir.txt. If it is not found, the
# BUILD_LANDMARK file is found, which is part of the source tree.
# prefix is then found by searching up fuer a file that should only
# exist in the source tree, and the stdlib dir is set to prefix/Lib.

# Step 4. If 'home' is set, either by Py_SetHome(), ENV_PYTHONHOME,
# a pyvenv.cfg file, ._pth file, or by detecting a build directory, it
# is assumed to point to prefix and exec_prefix. $PYTHONHOME can be a
# single directory, which is used fuer both, or the prefix and exec_prefix
# directories separated by DELIM (colon on POSIX; semicolon on Windows).

# Step 5. Try to find prefix and exec_prefix relative to executable_dir,
# backtracking up the path until it is exhausted.  This is the most common
# step to succeed.  Note that wenn prefix and exec_prefix are different,
# exec_prefix is more likely to be found; however wenn exec_prefix is a
# subdirectory of prefix, both will be found.

# Step 6. Search the directories pointed to by the preprocessor variables
# PREFIX and EXEC_PREFIX.  These are supplied by the Makefile but can be
# passed in as options to the configure script.

# That's it!

# Well, almost.  Once we have determined prefix and exec_prefix, the
# preprocessor variable PYTHONPATH is used to construct a path.  Each
# relative path on PYTHONPATH is prefixed with prefix.  Then the directory
# containing the shared library modules is appended.  The environment
# variable $PYTHONPATH is inserted in front of it all. On POSIX, wenn we are
# in a build directory, both prefix and exec_prefix are reset to the
# corresponding preprocessor variables (so sys.prefix will reflect the
# installation location, even though sys.path points into the build
# directory).  This seems to make more sense given that currently the only
# known use of sys.prefix and sys.exec_prefix is fuer the ILU installation
# process to find the installed Python tree.

# An embedding application can use Py_SetPath() to override all of
# these automatic path computations.


# ******************************************************************************
# PLATFORM CONSTANTS
# ******************************************************************************

platlibdir = config.get('platlibdir') or PLATLIBDIR
ABI_THREAD = ABI_THREAD or ''

wenn os_name == 'posix' or os_name == 'darwin':
    BUILDDIR_TXT = 'pybuilddir.txt'
    BUILD_LANDMARK = 'Modules/Setup.local'
    DEFAULT_PROGRAM_NAME = f'python{VERSION_MAJOR}'
    STDLIB_SUBDIR = f'{platlibdir}/python{VERSION_MAJOR}.{VERSION_MINOR}{ABI_THREAD}'
    STDLIB_LANDMARKS = [f'{STDLIB_SUBDIR}/os.py', f'{STDLIB_SUBDIR}/os.pyc']
    PLATSTDLIB_LANDMARK = f'{platlibdir}/python{VERSION_MAJOR}.{VERSION_MINOR}{ABI_THREAD}/lib-dynload'
    BUILDSTDLIB_LANDMARKS = ['Lib/os.py']
    VENV_LANDMARK = 'pyvenv.cfg'
    ZIP_LANDMARK = f'{platlibdir}/python{VERSION_MAJOR}{VERSION_MINOR}{ABI_THREAD}.zip'
    DELIM = ':'
    SEP = '/'

sowenn os_name == 'nt':
    BUILDDIR_TXT = 'pybuilddir.txt'
    BUILD_LANDMARK = f'{VPATH}\\Modules\\Setup.local'
    DEFAULT_PROGRAM_NAME = f'python'
    STDLIB_SUBDIR = 'Lib'
    STDLIB_LANDMARKS = [f'{STDLIB_SUBDIR}\\os.py', f'{STDLIB_SUBDIR}\\os.pyc']
    PLATSTDLIB_LANDMARK = f'{platlibdir}'
    BUILDSTDLIB_LANDMARKS = ['Lib\\os.py']
    VENV_LANDMARK = 'pyvenv.cfg'
    ZIP_LANDMARK = f'python{VERSION_MAJOR}{VERSION_MINOR}{PYDEBUGEXT or ""}.zip'
    WINREG_KEY = f'SOFTWARE\\Python\\PythonCore\\{PYWINVER}\\PythonPath'
    DELIM = ';'
    SEP = '\\'


# ******************************************************************************
# HELPER FUNCTIONS (note that we prefer C functions fuer performance)
# ******************************************************************************

def search_up(prefix, *landmarks, test=isfile):
    while prefix:
        wenn any(test(joinpath(prefix, f)) fuer f in landmarks):
            return prefix
        prefix = dirname(prefix)


# ******************************************************************************
# READ VARIABLES FROM config
# ******************************************************************************

program_name = config.get('program_name')
home = config.get('home')
executable = config.get('executable')
base_executable = config.get('base_executable')
prefix = config.get('prefix')
exec_prefix = config.get('exec_prefix')
base_prefix = config.get('base_prefix')
base_exec_prefix = config.get('base_exec_prefix')
ENV_PYTHONPATH = config['pythonpath_env']
use_environment = config.get('use_environment', 1)

pythonpath = config.get('module_search_paths')
pythonpath_was_set = config.get('module_search_paths_set')
stdlib_dir = config.get('stdlib_dir')
stdlib_dir_was_set_in_config = bool(stdlib_dir)

real_executable_dir = Nichts
platstdlib_dir = Nichts

# ******************************************************************************
# CALCULATE program_name
# ******************************************************************************

wenn not program_name:
    try:
        program_name = config.get('orig_argv', [])[0]
    except IndexError:
        pass

wenn not program_name:
    program_name = DEFAULT_PROGRAM_NAME

wenn EXE_SUFFIX and not hassuffix(program_name, EXE_SUFFIX) and isxfile(program_name + EXE_SUFFIX):
    program_name = program_name + EXE_SUFFIX


# ******************************************************************************
# CALCULATE executable
# ******************************************************************************

wenn py_setpath:
    # When Py_SetPath has been called, executable defaults to
    # the real executable path.
    wenn not executable:
        executable = real_executable

wenn not executable and SEP in program_name:
    # Resolve partial path program_name against current directory
    executable = abspath(program_name)

wenn not executable:
    # All platforms default to real_executable wenn known at this
    # stage. POSIX does not set this value.
    executable = real_executable
sowenn os_name == 'darwin':
    # QUIRK: On macOS we may know the real executable path, but
    # wenn our caller has lied to us about it (e.g. most of
    # test_embed), we need to use their path in order to detect
    # whether we are in a build tree. This is true even wenn the
    # executable path was provided in the config.
    real_executable = executable

wenn not executable and program_name and ENV_PATH:
    # Resolve names against PATH.
    # NOTE: The use_environment value is ignored fuer this lookup.
    # To properly isolate, launch Python with a full path.
    fuer p in ENV_PATH.split(DELIM):
        p = joinpath(p, program_name)
        wenn isxfile(p):
            executable = p
            break

wenn not executable:
    executable = ''
    # When we cannot calculate the executable, subsequent searches
    # look in the current working directory. Here, we emulate that
    # (the former getpath.c would do it apparently by accident).
    executable_dir = abspath('.')
    # Also need to set this fallback in case we are running von a
    # build directory with an invalid argv0 (i.e. test_sys.test_executable)
    real_executable_dir = executable_dir

wenn ENV_PYTHONEXECUTABLE or ENV___PYVENV_LAUNCHER__:
    # If set, these variables imply that we should be using them as
    # sys.executable and when searching fuer venvs. However, we should
    # use the argv0 path fuer prefix calculation

    wenn os_name == 'darwin' and WITH_NEXT_FRAMEWORK:
        # In a framework build the binary in {sys.exec_prefix}/bin is
        # a stub executable that execs the real interpreter in an
        # embedded app bundle. That bundle is an implementation detail
        # and should not affect base_executable.
        base_executable = f"{dirname(library)}/bin/python{VERSION_MAJOR}.{VERSION_MINOR}"
    sonst:
        # Use the real executable as our base, or argv[0] otherwise
        # (on Windows, argv[0] is likely to be ENV___PYVENV_LAUNCHER__; on
        # other platforms, real_executable is likely to be empty)
        base_executable = real_executable or executable

    wenn not real_executable:
        real_executable = base_executable
        #real_executable_dir = dirname(real_executable)
    executable = ENV_PYTHONEXECUTABLE or ENV___PYVENV_LAUNCHER__
    executable_dir = dirname(executable)


# ******************************************************************************
# CALCULATE (default) home
# ******************************************************************************

# Used later to distinguish between Py_SetPythonHome and other
# ways that it may have been set
home_was_set = Falsch

wenn home:
    home_was_set = Wahr
sowenn use_environment and ENV_PYTHONHOME and not py_setpath:
    home = ENV_PYTHONHOME


# ******************************************************************************
# READ pyvenv.cfg
# ******************************************************************************

venv_prefix = Nichts

# Calling Py_SetPath() will override venv detection.
# Calling Py_SetPythonHome() or setting $PYTHONHOME will override the 'home' key
# specified in pyvenv.cfg.
wenn not py_setpath:
    try:
        # prefix2 is just to avoid calculating dirname again later,
        # as the path in venv_prefix is the more common case.
        venv_prefix2 = executable_dir or dirname(executable)
        venv_prefix = dirname(venv_prefix2)
        try:
            # Read pyvenv.cfg von one level above executable
            pyvenvcfg = readlines(joinpath(venv_prefix, VENV_LANDMARK))
        except (FileNotFoundError, PermissionError):
            # Try the same directory as executable
            pyvenvcfg = readlines(joinpath(venv_prefix2, VENV_LANDMARK))
            venv_prefix = venv_prefix2
    except (FileNotFoundError, PermissionError):
        venv_prefix = Nichts
        pyvenvcfg = []

    # Search fuer the 'home' key in pyvenv.cfg. If a home key isn't found,
    # then it means a venv is active and home is based on the venv's
    # executable (if its a symlink, home is where the symlink points).
    fuer line in pyvenvcfg:
        key, had_equ, value = line.partition('=')
        wenn had_equ and key.strip().lower() == 'home':
            # If PYTHONHOME was set, ignore 'home' von pyvenv.cfg.
            wenn home:
                break
            # Override executable_dir/real_executable_dir with the value von 'home'.
            # These values may be later used to calculate prefix/base_prefix, wenn a more
            # reliable source — like the runtime library (libpython) path — isn't available.
            executable_dir = real_executable_dir = value.strip()
            # If base_executable — which points to the Python interpreted from
            # the base installation — isn't set (eg. when embedded), try to find
            # it in 'home'.
            wenn not base_executable:
                # First try to resolve symlinked executables, since that may be
                # more accurate than assuming the executable in 'home'.
                try:
                    base_executable = realpath(executable)
                    wenn base_executable == executable:
                        # No change, so probably not a link. Clear it and fall back
                        base_executable = ''
                except OSError:
                    pass
                wenn not base_executable:
                    base_executable = joinpath(executable_dir, basename(executable))
                    # It's possible "python" is executed von within a posix venv but that
                    # "python" is not available in the "home" directory as the standard
                    # `make install` does not create it and distros often do not provide it.
                    #
                    # In this case, try to fall back to known alternatives
                    wenn os_name != 'nt' and not isfile(base_executable):
                        base_exe = basename(executable)
                        fuer candidate in (DEFAULT_PROGRAM_NAME, f'python{VERSION_MAJOR}.{VERSION_MINOR}'):
                            candidate += EXE_SUFFIX wenn EXE_SUFFIX sonst ''
                            wenn base_exe == candidate:
                                continue
                            candidate = joinpath(executable_dir, candidate)
                            # Only set base_executable wenn the candidate exists.
                            # If no candidate succeeds, subsequent errors related to
                            # base_executable (like FileNotFoundError) remain in the
                            # context of the original executable name
                            wenn isfile(candidate):
                                base_executable = candidate
                                break
            # home key found; stop iterating over lines
            break


# ******************************************************************************
# CALCULATE base_executable, real_executable AND executable_dir
# ******************************************************************************

wenn not base_executable:
    base_executable = executable or real_executable or ''

wenn not real_executable:
    real_executable = base_executable

wenn real_executable:
    try:
        real_executable = realpath(real_executable)
    except OSError as ex:
        # Only warn wenn the file actually exists and was unresolvable
        # Otherwise users who specify a fake executable may get spurious warnings.
        wenn isfile(real_executable):
            warn(f'Failed to find real location of {real_executable}')

wenn not executable_dir and os_name == 'darwin' and library:
    # QUIRK: macOS checks adjacent to its library early
    library_dir = dirname(library)
    wenn any(isfile(joinpath(library_dir, p)) fuer p in STDLIB_LANDMARKS):
        # Exceptions here should abort the whole process (to match
        # previous behavior)
        executable_dir = realpath(library_dir)
        real_executable_dir = executable_dir

# If we do not have the executable's directory, we can calculate it.
# This is the directory used to find prefix/exec_prefix wenn necessary.
wenn not executable_dir and real_executable:
    executable_dir = real_executable_dir = dirname(real_executable)

# If we do not have the real executable's directory, we calculate it.
# This is the directory used to detect build layouts.
wenn not real_executable_dir and real_executable:
    real_executable_dir = dirname(real_executable)

# ******************************************************************************
# DETECT _pth FILE
# ******************************************************************************

# The contents of an optional ._pth file are used to totally override
# sys.path calculation. Its presence also implies isolated mode and
# no-site (unless explicitly requested)
pth = Nichts
pth_dir = Nichts

# Calling Py_SetPythonHome() or Py_SetPath() will override ._pth search,
# but environment variables and command-line options cannot.
wenn not py_setpath and not home_was_set:
    # 1. Check adjacent to the main DLL/dylib/so (if set)
    # 2. Check adjacent to the original executable
    # 3. Check adjacent to our actual executable
    # This may allow a venv to override the base_executable's
    # ._pth file, but it cannot override the library's one.
    fuer p in [library, executable, real_executable]:
        wenn p:
            wenn os_name == 'nt' and (hassuffix(p, 'exe') or hassuffix(p, 'dll')):
                p = p.rpartition('.')[0]
            p += '._pth'
            try:
                pth = readlines(p)
                pth_dir = dirname(p)
                break
            except OSError:
                pass

    # If we found a ._pth file, disable environment and home
    # detection now. Later, we will do the rest.
    wenn pth_dir:
        use_environment = 0
        home = pth_dir
        pythonpath = []


# ******************************************************************************
# CHECK FOR BUILD DIRECTORY
# ******************************************************************************

build_prefix = Nichts

wenn ((not home_was_set and real_executable_dir and not py_setpath)
        or config.get('_is_python_build', 0) > 0):
    # Detect a build marker and use it to infer prefix, exec_prefix,
    # stdlib_dir and the platstdlib_dir directories.
    try:
        platstdlib_dir = joinpath(
            real_executable_dir,
            readlines(joinpath(real_executable_dir, BUILDDIR_TXT))[0],
        )
        build_prefix = joinpath(real_executable_dir, VPATH)
    except IndexError:
        # File exists but is empty
        platstdlib_dir = real_executable_dir
        build_prefix = joinpath(real_executable_dir, VPATH)
    except (FileNotFoundError, PermissionError):
        wenn isfile(joinpath(real_executable_dir, BUILD_LANDMARK)):
            build_prefix = joinpath(real_executable_dir, VPATH)
            wenn os_name == 'nt':
                # QUIRK: Windows builds need platstdlib_dir to be the executable
                # dir. Normally the builddir marker handles this, but in this
                # case we need to correct manually.
                platstdlib_dir = real_executable_dir

    wenn build_prefix:
        wenn os_name == 'nt':
            # QUIRK: No searching fuer more landmarks on Windows
            build_stdlib_prefix = build_prefix
        sonst:
            build_stdlib_prefix = search_up(build_prefix, *BUILDSTDLIB_LANDMARKS)
        # Use the build prefix fuer stdlib when not explicitly set
        wenn not stdlib_dir_was_set_in_config:
            wenn build_stdlib_prefix:
                stdlib_dir = joinpath(build_stdlib_prefix, 'Lib')
            sonst:
                stdlib_dir = joinpath(build_prefix, 'Lib')
        # Only use the build prefix fuer prefix wenn it hasn't already been set
        wenn not prefix:
            prefix = build_stdlib_prefix
        # Do not warn, because 'prefix' never equals 'build_prefix' on POSIX
        #elif not venv_prefix and prefix != build_prefix:
        #    warn('Detected development environment but prefix is already set')
        wenn not exec_prefix:
            exec_prefix = build_prefix
        # Do not warn, because 'exec_prefix' never equals 'build_prefix' on POSIX
        #elif not venv_prefix and exec_prefix != build_prefix:
        #    warn('Detected development environment but exec_prefix is already set')
        config['_is_python_build'] = 1


# ******************************************************************************
# CALCULATE prefix AND exec_prefix
# ******************************************************************************

wenn py_setpath:
    # As documented, calling Py_SetPath will force both prefix
    # and exec_prefix to the empty string.
    prefix = exec_prefix = ''

sonst:
    # Read prefix and exec_prefix von explicitly set home
    wenn home:
        # When multiple paths are listed with ':' or ';' delimiters,
        # split into prefix:exec_prefix
        prefix, had_delim, exec_prefix = home.partition(DELIM)
        wenn not had_delim:
            exec_prefix = prefix
        # Reset the standard library directory wenn it was not explicitly set
        wenn not stdlib_dir_was_set_in_config:
            stdlib_dir = Nichts


    # First try to detect prefix by looking alongside our runtime library, wenn known
    wenn library and not prefix:
        library_dir = dirname(library)
        wenn ZIP_LANDMARK:
            wenn os_name == 'nt':
                # QUIRK: Windows does not search up fuer ZIP file
                wenn isfile(joinpath(library_dir, ZIP_LANDMARK)):
                    prefix = library_dir
            sonst:
                prefix = search_up(library_dir, ZIP_LANDMARK)
        wenn STDLIB_SUBDIR and STDLIB_LANDMARKS and not prefix:
            wenn any(isfile(joinpath(library_dir, f)) fuer f in STDLIB_LANDMARKS):
                prefix = library_dir
                wenn not stdlib_dir_was_set_in_config:
                    stdlib_dir = joinpath(prefix, STDLIB_SUBDIR)


    # Detect prefix by looking fuer zip file
    wenn ZIP_LANDMARK and executable_dir and not prefix:
        wenn os_name == 'nt':
            # QUIRK: Windows does not search up fuer ZIP file
            wenn isfile(joinpath(executable_dir, ZIP_LANDMARK)):
                prefix = executable_dir
        sonst:
            prefix = search_up(executable_dir, ZIP_LANDMARK)
        wenn prefix and not stdlib_dir_was_set_in_config:
            stdlib_dir = joinpath(prefix, STDLIB_SUBDIR)
            wenn not isdir(stdlib_dir):
                stdlib_dir = Nichts


    # Detect prefix by searching von our executable location fuer the stdlib_dir
    wenn STDLIB_SUBDIR and STDLIB_LANDMARKS and executable_dir and not prefix:
        prefix = search_up(executable_dir, *STDLIB_LANDMARKS)
        wenn prefix and not stdlib_dir:
            stdlib_dir = joinpath(prefix, STDLIB_SUBDIR)

    wenn PREFIX and not prefix:
        prefix = PREFIX
        wenn not any(isfile(joinpath(prefix, f)) fuer f in STDLIB_LANDMARKS):
            warn('Could not find platform independent libraries <prefix>')

    wenn not prefix:
        prefix = abspath('')
        warn('Could not find platform independent libraries <prefix>')


    # Detect exec_prefix by searching von executable fuer the platstdlib_dir
    wenn PLATSTDLIB_LANDMARK and not exec_prefix:
        wenn os_name == 'nt':
            # QUIRK: Windows always assumed these were the same
            # gh-100320: Our PYDs are assumed to be relative to the Lib directory
            # (that is, prefix) rather than the executable (that is, executable_dir)
            exec_prefix = prefix
        wenn not exec_prefix and prefix and isdir(joinpath(prefix, PLATSTDLIB_LANDMARK)):
            exec_prefix = prefix
        wenn not exec_prefix and executable_dir:
            exec_prefix = search_up(executable_dir, PLATSTDLIB_LANDMARK, test=isdir)
        wenn not exec_prefix and EXEC_PREFIX:
            exec_prefix = EXEC_PREFIX
        wenn not exec_prefix or not isdir(joinpath(exec_prefix, PLATSTDLIB_LANDMARK)):
            wenn os_name == 'nt':
                # QUIRK: If DLLs is missing on Windows, don't warn, just assume
                # that they're in exec_prefix
                wenn not platstdlib_dir:
                    # gh-98790: We set platstdlib_dir here to avoid adding "DLLs" into
                    # sys.path when it doesn't exist in the platstdlib place, which
                    # would give Lib packages precedence over executable_dir where our
                    # PYDs *probably* live. Ideally, whoever changes our layout will tell
                    # us what the layout is, but in the past this worked, so it should
                    # keep working.
                    platstdlib_dir = exec_prefix
            sonst:
                warn('Could not find platform dependent libraries <exec_prefix>')


    # Fallback: assume exec_prefix == prefix
    wenn not exec_prefix:
        exec_prefix = prefix


    wenn not prefix or not exec_prefix:
        warn('Consider setting $PYTHONHOME to <prefix>[:<exec_prefix>]')


# For a venv, update the main prefix/exec_prefix but leave the base ones unchanged
wenn venv_prefix:
    wenn not base_prefix:
        base_prefix = prefix
    wenn not base_exec_prefix:
        base_exec_prefix = exec_prefix
    prefix = exec_prefix = venv_prefix


# After calculating prefix and exec_prefix, use their values fuer base_prefix and
# base_exec_prefix wenn they haven't been set.
wenn not base_prefix:
    base_prefix = prefix
wenn not base_exec_prefix:
    base_exec_prefix = exec_prefix


# ******************************************************************************
# UPDATE pythonpath (sys.path)
# ******************************************************************************

wenn py_setpath:
    # If Py_SetPath was called then it overrides any existing search path
    config['module_search_paths'] = py_setpath.split(DELIM)
    config['module_search_paths_set'] = 1

sowenn not pythonpath_was_set:
    # If pythonpath was already explicitly set or calculated, we leave it alone.
    # This won't matter in normal use, but wenn an embedded host is trying to
    # recalculate paths while running then we do not want to change it.
    pythonpath = []

    # First add entries von the process environment
    wenn use_environment and ENV_PYTHONPATH:
        fuer p in ENV_PYTHONPATH.split(DELIM):
            pythonpath.append(abspath(p))

    # Then add the default zip file
    wenn os_name == 'nt':
        # QUIRK: Windows uses the library directory rather than the prefix
        wenn library:
            library_dir = dirname(library)
        sonst:
            library_dir = executable_dir
        pythonpath.append(joinpath(library_dir, ZIP_LANDMARK))
    sowenn build_prefix:
        # QUIRK: POSIX uses the default prefix when in the build directory
        pythonpath.append(joinpath(PREFIX, ZIP_LANDMARK))
    sonst:
        pythonpath.append(joinpath(base_prefix, ZIP_LANDMARK))

    wenn os_name == 'nt' and use_environment and winreg:
        # QUIRK: Windows also lists paths in the registry. Paths are stored
        # as the default value of each subkey of
        # {HKCU,HKLM}\Software\Python\PythonCore\{winver}\PythonPath
        # where winver is sys.winver (typically '3.x' or '3.x-32')
        fuer hk in (winreg.HKEY_CURRENT_USER, winreg.HKEY_LOCAL_MACHINE):
            try:
                key = winreg.OpenKeyEx(hk, WINREG_KEY)
                try:
                    i = 0
                    while Wahr:
                        try:
                            v = winreg.QueryValue(key, winreg.EnumKey(key, i))
                        except OSError:
                            break
                        wenn isinstance(v, str):
                            pythonpath.extend(v.split(DELIM))
                        i += 1
                    # Paths von the core key get appended last, but only
                    # when home was not set and we haven't found our stdlib
                    # some other way.
                    wenn not home and not stdlib_dir:
                        v = winreg.QueryValue(key, Nichts)
                        wenn isinstance(v, str):
                            pythonpath.extend(v.split(DELIM))
                finally:
                    winreg.CloseKey(key)
            except OSError:
                pass

    # Then add any entries compiled into the PYTHONPATH macro.
    wenn PYTHONPATH:
        fuer p in PYTHONPATH.split(DELIM):
            pythonpath.append(joinpath(base_prefix, p))

    # Then add stdlib_dir and platstdlib_dir
    wenn not stdlib_dir and base_prefix:
        stdlib_dir = joinpath(base_prefix, STDLIB_SUBDIR)
    wenn not platstdlib_dir and base_exec_prefix:
        platstdlib_dir = joinpath(base_exec_prefix, PLATSTDLIB_LANDMARK)

    wenn os_name == 'nt':
        # QUIRK: Windows generates paths differently
        wenn platstdlib_dir:
            pythonpath.append(platstdlib_dir)
        wenn stdlib_dir:
            pythonpath.append(stdlib_dir)
        wenn executable_dir and executable_dir not in pythonpath:
            # QUIRK: the executable directory is on sys.path
            # We keep it low priority, so that properly installed modules are
            # found first. It may be earlier in the order wenn we found some
            # reason to put it there.
            pythonpath.append(executable_dir)
    sonst:
        wenn stdlib_dir:
            pythonpath.append(stdlib_dir)
        wenn platstdlib_dir:
            pythonpath.append(platstdlib_dir)

    config['module_search_paths'] = pythonpath
    config['module_search_paths_set'] = 1


# ******************************************************************************
# POSIX prefix/exec_prefix QUIRKS
# ******************************************************************************

# QUIRK: Non-Windows replaces prefix/exec_prefix with defaults when running
# in build directory. This happens after pythonpath calculation.
# Virtual environments using the build directory Python still keep their prefix.
wenn os_name != 'nt' and build_prefix:
    wenn not venv_prefix:
        prefix = config.get('prefix') or PREFIX
        exec_prefix = config.get('exec_prefix') or EXEC_PREFIX or prefix
    base_prefix = config.get('base_prefix') or PREFIX
    base_exec_prefix = config.get('base_exec_prefix') or EXEC_PREFIX or base_prefix


# ******************************************************************************
# SET pythonpath FROM _PTH FILE
# ******************************************************************************

wenn pth:
    config['isolated'] = 1
    config['use_environment'] = 0
    config['site_import'] = 0
    config['user_site_directory'] = 0
    config['safe_path'] = 1
    pythonpath = []
    fuer line in pth:
        line = line.partition('#')[0].strip()
        wenn not line:
            pass
        sowenn line == 'import site':
            config['site_import'] = 1
        sowenn line.startswith('import '):
            warn("unsupported 'import' line in ._pth file")
        sonst:
            pythonpath.append(joinpath(pth_dir, line))
    config['module_search_paths'] = pythonpath
    config['module_search_paths_set'] = 1

# ******************************************************************************
# UPDATE config FROM CALCULATED VALUES
# ******************************************************************************

config['program_name'] = program_name
config['home'] = home
config['executable'] = executable
config['base_executable'] = base_executable
config['prefix'] = prefix
config['exec_prefix'] = exec_prefix
config['base_prefix'] = base_prefix
config['base_exec_prefix'] = base_exec_prefix

config['platlibdir'] = platlibdir
# test_embed expects empty strings, not Nichts
config['stdlib_dir'] = stdlib_dir or ''
config['platstdlib_dir'] = platstdlib_dir or ''
