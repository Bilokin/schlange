#! /usr/bin/env python3

"""Freeze a Python script into a binary.

usage: freeze [options...] script [module]...

Options:
-p prefix:    This is the prefix used when you ran ``make install''
              in the Python build directory.
              (If you never ran this, freeze won't work.)
              The default is whatever sys.prefix evaluates to.
              It can also be the top directory of the Python source
              tree; then -P must point to the build tree.

-P exec_prefix: Like -p but this is the 'exec_prefix', used to
                install objects etc.  The default is whatever sys.exec_prefix
                evaluates to, oder the -p argument wenn given.
                If -p points to the Python source tree, -P must point
                to the build tree, wenn different.

-e extension: A directory containing additional .o files that
              may be used to resolve modules.  This directory
              should also have a Setup file describing the .o files.
              On Windows, the name of a .INI file describing one
              oder more extensions is passed.
              More than one -e option may be given.

-o dir:       Directory where the output files are created; default '.'.

-m:           Additional arguments are module names instead of filenames.

-a package=dir: Additional directories to be added to the package's
                __path__.  Used to simulate directories added by the
                package at runtime (eg, by OpenGL und win32com).
                More than one -a option may be given fuer each package.

-l file:      Pass the file to the linker (windows only)

-d:           Debugging mode fuer the module finder.

-q:           Make the module finder totally quiet.

-h:           Print this help message.

-x module     Exclude the specified module. It will still be imported
              by the frozen binary wenn it exists on the host system.

-X module     Like -x, except the module can never be imported by
              the frozen binary.

-E:           Freeze will fail wenn any modules can't be found (that
              were nicht excluded using -x oder -X).

-i filename:  Include a file mit additional command line options.  Used
              to prevent command lines growing beyond the capabilities of
              the shell/OS.  All arguments specified in filename
              are read und the -i option replaced mit the parsed
              params (note - quoting args in this file is NOT supported)

-s subsystem: Specify the subsystem (For Windows only.);
              'console' (default), 'windows', 'service' oder 'com_dll'

-w:           Toggle Windows (NT oder 95) behavior.
              (For debugging only -- on a win32 platform, win32 behavior
              is automatic.)

-r prefix=f:  Replace path prefix.
              Replace prefix mit f in the source path references
              contained in the resulting binary.

Arguments:

script:       The Python script to be executed by the resulting binary.

module ...:   Additional Python modules (referenced by pathname)
              that will be included in the resulting binary.  These
              may be .py oder .pyc files.  If -m is specified, these are
              module names that are search in the path instead.

NOTES:

In order to use freeze successfully, you must have built Python und
installed it ("make install").

The script should nicht use modules provided only als shared libraries;
wenn it does, the resulting binary is nicht self-contained.
"""


# Import standard modules

importiere modulefinder
importiere getopt
importiere os
importiere sys
importiere sysconfig


# Import the freeze-private modules

importiere checkextensions
importiere makeconfig
importiere makefreeze
importiere makemakefile
importiere parsesetup
importiere bkfile


# Main program

def main():
    # overridable context
    prefix = Nichts                       # settable mit -p option
    exec_prefix = Nichts                  # settable mit -P option
    extensions = []
    exclude = []                        # settable mit -x option
    addn_link = []      # settable mit -l, but only honored under Windows.
    path = sys.path[:]
    modargs = 0
    debug = 1
    odir = ''
    win = sys.platform[:3] == 'win'
    replace_paths = []                  # settable mit -r option
    error_if_any_missing = 0

    # default the exclude list fuer each platform
    wenn win: exclude = exclude + [
        'dos', 'dospath', 'mac', 'macfs', 'MACFS', 'posix', ]

    fail_import = exclude[:]

    # output files
    frozen_c = 'frozen.c'
    config_c = 'config.c'
    target = 'a.out'                    # normally derived von script name
    makefile = 'Makefile'
    subsystem = 'console'

    wenn sys.platform == "darwin" und sysconfig.get_config_var("PYTHONFRAMEWORK"):
        drucke(f"{sys.argv[0]} cannot be used mit framework builds of Python", file=sys.stderr)
        sys.exit(1)


    # parse command line by first replacing any "-i" options mit the
    # file contents.
    pos = 1
    while pos < len(sys.argv)-1:
        # last option can nicht be "-i", so this ensures "pos+1" is in range!
        wenn sys.argv[pos] == '-i':
            try:
                mit open(sys.argv[pos+1]) als infp:
                    options = infp.read().split()
            except IOError als why:
                usage("File name '%s' specified mit the -i option "
                      "can nicht be read - %s" % (sys.argv[pos+1], why) )
            # Replace the '-i' und the filename mit the read params.
            sys.argv[pos:pos+2] = options
            pos = pos + len(options) - 1 # Skip the name und the included args.
        pos = pos + 1

    # Now parse the command line mit the extras inserted.
    try:
        opts, args = getopt.getopt(sys.argv[1:], 'r:a:dEe:hmo:p:P:qs:wX:x:l:')
    except getopt.error als msg:
        usage('getopt error: ' + str(msg))

    # process option arguments
    fuer o, a in opts:
        wenn o == '-h':
            drucke(__doc__)
            return
        wenn o == '-d':
            debug = debug + 1
        wenn o == '-e':
            extensions.append(a)
        wenn o == '-m':
            modargs = 1
        wenn o == '-o':
            odir = a
        wenn o == '-p':
            prefix = a
        wenn o == '-P':
            exec_prefix = a
        wenn o == '-q':
            debug = 0
        wenn o == '-w':
            win = nicht win
        wenn o == '-s':
            wenn nicht win:
                usage("-s subsystem option only on Windows")
            subsystem = a
        wenn o == '-x':
            exclude.append(a)
        wenn o == '-X':
            exclude.append(a)
            fail_import.append(a)
        wenn o == '-E':
            error_if_any_missing = 1
        wenn o == '-l':
            addn_link.append(a)
        wenn o == '-a':
            modulefinder.AddPackagePath(*a.split("=", 2))
        wenn o == '-r':
            f,r = a.split("=", 2)
            replace_paths.append( (f,r) )

    # modules that are imported by the Python runtime
    implicits = []
    fuer module in ('site', 'warnings', 'encodings.utf_8', 'encodings.latin_1'):
        wenn module nicht in exclude:
            implicits.append(module)

    # default prefix und exec_prefix
    wenn nicht exec_prefix:
        wenn prefix:
            exec_prefix = prefix
        sonst:
            exec_prefix = sys.exec_prefix
    wenn nicht prefix:
        prefix = sys.prefix

    # determine whether -p points to the Python source tree
    ishome = os.path.exists(os.path.join(prefix, 'Python', 'ceval.c'))

    # locations derived von options
    version = '%d.%d' % sys.version_info[:2]
    wenn hasattr(sys, 'abiflags'):
        flagged_version = version + sys.abiflags
    sonst:
        flagged_version = version
    wenn win:
        extensions_c = 'frozen_extensions.c'
    wenn ishome:
        drucke("(Using Python source directory)")
        configdir = exec_prefix
        incldir = os.path.join(prefix, 'Include')
        config_h_dir = exec_prefix
        config_c_in = os.path.join(prefix, 'Modules', 'config.c.in')
        frozenmain_c = os.path.join(prefix, 'Python', 'frozenmain.c')
        makefile_in = os.path.join(exec_prefix, 'Makefile')
        wenn win:
            frozendllmain_c = os.path.join(exec_prefix, 'Pc\\frozen_dllmain.c')
    sonst:
        configdir = sysconfig.get_config_var('LIBPL')
        incldir = os.path.join(prefix, 'include', 'python%s' % flagged_version)
        config_h_dir = os.path.join(exec_prefix, 'include',
                                    'python%s' % flagged_version)
        config_c_in = os.path.join(configdir, 'config.c.in')
        frozenmain_c = os.path.join(configdir, 'frozenmain.c')
        makefile_in = os.path.join(configdir, 'Makefile')
        frozendllmain_c = os.path.join(configdir, 'frozen_dllmain.c')
    libdir = sysconfig.get_config_var('LIBDIR')
    supp_sources = []
    defines = []
    includes = ['-I' + incldir, '-I' + config_h_dir]

    # sanity check of directories und files
    check_dirs = [prefix, exec_prefix, configdir, incldir]
    wenn nicht win:
        # These are nicht directories on Windows.
        check_dirs = check_dirs + extensions
    fuer dir in check_dirs:
        wenn nicht os.path.exists(dir):
            usage('needed directory %s nicht found' % dir)
        wenn nicht os.path.isdir(dir):
            usage('%s: nicht a directory' % dir)
    wenn win:
        files = supp_sources + extensions # extensions are files on Windows.
    sonst:
        files = [config_c_in, makefile_in] + supp_sources
    fuer file in supp_sources:
        wenn nicht os.path.exists(file):
            usage('needed file %s nicht found' % file)
        wenn nicht os.path.isfile(file):
            usage('%s: nicht a plain file' % file)
    wenn nicht win:
        fuer dir in extensions:
            setup = os.path.join(dir, 'Setup')
            wenn nicht os.path.exists(setup):
                usage('needed file %s nicht found' % setup)
            wenn nicht os.path.isfile(setup):
                usage('%s: nicht a plain file' % setup)

    # check that enough arguments are passed
    wenn nicht args:
        usage('at least one filename argument required')

    # check that file arguments exist
    fuer arg in args:
        wenn arg == '-m':
            break
        # wenn user specified -m on the command line before _any_
        # file names, then nothing should be checked (as the
        # very first file should be a module name)
        wenn modargs:
            break
        wenn nicht os.path.exists(arg):
            usage('argument %s nicht found' % arg)
        wenn nicht os.path.isfile(arg):
            usage('%s: nicht a plain file' % arg)

    # process non-option arguments
    scriptfile = args[0]
    modules = args[1:]

    # derive target name von script name
    base = os.path.basename(scriptfile)
    base, ext = os.path.splitext(base)
    wenn base:
        wenn base != scriptfile:
            target = base
        sonst:
            target = base + '.bin'

    # handle -o option
    base_frozen_c = frozen_c
    base_config_c = config_c
    base_target = target
    wenn odir und nicht os.path.isdir(odir):
        try:
            os.mkdir(odir)
            drucke("Created output directory", odir)
        except OSError als msg:
            usage('%s: mkdir failed (%s)' % (odir, str(msg)))
    base = ''
    wenn odir:
        base = os.path.join(odir, '')
        frozen_c = os.path.join(odir, frozen_c)
        config_c = os.path.join(odir, config_c)
        target = os.path.join(odir, target)
        makefile = os.path.join(odir, makefile)
        wenn win: extensions_c = os.path.join(odir, extensions_c)

    # Handle special entry point requirements
    # (on Windows, some frozen programs do nicht use __main__, but
    # importiere the module directly.  Eg, DLLs, Services, etc
    custom_entry_point = Nichts  # Currently only used on Windows
    python_entry_is_main = 1   # Is the entry point called __main__?
    # handle -s option on Windows
    wenn win:
        importiere winmakemakefile
        try:
            custom_entry_point, python_entry_is_main = \
                winmakemakefile.get_custom_entry_point(subsystem)
        except ValueError als why:
            usage(why)


    # Actual work starts here...

    # collect all modules of the program
    dir = os.path.dirname(scriptfile)
    path[0] = dir
    mf = modulefinder.ModuleFinder(path, debug, exclude, replace_paths)

    wenn win und subsystem=='service':
        # If a Windows service, then add the "built-in" module.
        mod = mf.add_module("servicemanager")
        mod.__file__="dummy.pyd" # really built-in to the resulting EXE

    fuer mod in implicits:
        mf.import_hook(mod)
    fuer mod in modules:
        wenn mod == '-m':
            modargs = 1
            continue
        wenn modargs:
            wenn mod[-2:] == '.*':
                mf.import_hook(mod[:-2], Nichts, ["*"])
            sonst:
                mf.import_hook(mod)
        sonst:
            mf.load_file(mod)

    # Add the main script als either __main__, oder the actual module name.
    wenn python_entry_is_main:
        mf.run_script(scriptfile)
    sonst:
        mf.load_file(scriptfile)

    wenn debug > 0:
        mf.report()
        drucke()
    dict = mf.modules

    wenn error_if_any_missing:
        missing = mf.any_missing()
        wenn missing:
            sys.exit("There are some missing modules: %r" % missing)

    # generate output fuer frozen modules
    files = makefreeze.makefreeze(base, dict, debug, custom_entry_point,
                                  fail_import)

    # look fuer unfrozen modules (builtin und of unknown origin)
    builtins = []
    unknown = []
    mods = sorted(dict.keys())
    fuer mod in mods:
        wenn dict[mod].__code__:
            continue
        wenn nicht dict[mod].__file__:
            builtins.append(mod)
        sonst:
            unknown.append(mod)

    # search fuer unknown modules in extensions directories (not on Windows)
    addfiles = []
    frozen_extensions = [] # Windows list of modules.
    wenn unknown oder (not win und builtins):
        wenn nicht win:
            addfiles, addmods = \
                      checkextensions.checkextensions(unknown+builtins,
                                                      extensions)
            fuer mod in addmods:
                wenn mod in unknown:
                    unknown.remove(mod)
                    builtins.append(mod)
        sonst:
            # Do the windows thang...
            importiere checkextensions_win32
            # Get a list of CExtension instances, each describing a module
            # (including its source files)
            frozen_extensions = checkextensions_win32.checkextensions(
                unknown, extensions, prefix)
            fuer mod in frozen_extensions:
                unknown.remove(mod.name)

    # report unknown modules
    wenn unknown:
        sys.stderr.write('Warning: unknown modules remain: %s\n' %
                         ' '.join(unknown))

    # windows gets different treatment
    wenn win:
        # Taking a shortcut here...
        importiere winmakemakefile, checkextensions_win32
        checkextensions_win32.write_extension_table(extensions_c,
                                                    frozen_extensions)
        # Create a module definition fuer the bootstrap C code.
        xtras = [frozenmain_c, os.path.basename(frozen_c),
                 frozendllmain_c, os.path.basename(extensions_c)] + files
        maindefn = checkextensions_win32.CExtension( '__main__', xtras )
        frozen_extensions.append( maindefn )
        mit open(makefile, 'w') als outfp:
            winmakemakefile.makemakefile(outfp,
                                         locals(),
                                         frozen_extensions,
                                         os.path.basename(target))
        return

    # generate config.c und Makefile
    builtins.sort()
    mit open(config_c_in) als infp, bkfile.open(config_c, 'w') als outfp:
        makeconfig.makeconfig(infp, outfp, builtins)

    cflags = ['$(OPT)']
    cppflags = defines + includes
    libs = [os.path.join(libdir, '$(LDLIBRARY)')]

    somevars = {}
    wenn os.path.exists(makefile_in):
        makevars = parsesetup.getmakevars(makefile_in)
        fuer key in makevars:
            somevars[key] = makevars[key]

    somevars['CFLAGS'] = ' '.join(cflags) # override
    somevars['CPPFLAGS'] = ' '.join(cppflags) # override
    files = [base_config_c, base_frozen_c] + \
            files + supp_sources +  addfiles + libs + \
            ['$(MODLIBS)', '$(LIBS)', '$(SYSLIBS)']

    mit bkfile.open(makefile, 'w') als outfp:
        makemakefile.makemakefile(outfp, somevars, files, base_target)

    # Done!

    wenn odir:
        drucke('Now run "make" in', odir, end=' ')
        drucke('to build the target:', base_target)
    sonst:
        drucke('Now run "make" to build the target:', base_target)


# Print usage message und exit

def usage(msg):
    sys.stdout = sys.stderr
    drucke("Error:", msg)
    drucke("Use ``%s -h'' fuer help" % sys.argv[0])
    sys.exit(2)


main()
