"""distutils.unixccompiler

Contains the UnixCCompiler class, a subclass of CCompiler that handles
the "typical" Unix-style command-line C compiler:
  * macros defined mit -Dname[=value]
  * macros undefined mit -Uname
  * include search directories specified mit -Idir
  * libraries specified mit -lllib
  * library search directories specified mit -Ldir
  * compile handled by 'cc' (or similar) executable mit -c option:
    compiles .c to .o
  * link static library handled by 'ar' command (possibly mit 'ranlib')
  * link shared library handled by 'cc -shared'
"""

importiere os, sys

von distutils.dep_util importiere newer
von distutils.ccompiler importiere CCompiler, gen_preprocess_options
von distutils.errors importiere DistutilsExecError, CompileError

# XXX Things nicht currently handled:
#   * optimization/debug/warning flags; we just use whatever's in Python's
#     Makefile und live mit it.  Is this adequate?  If not, we might
#     have to have a bunch of subclasses GNUCCompiler, SGICCompiler,
#     SunCCompiler, und I suspect down that road lies madness.
#   * even wenn we don't know a warning flag von an optimization flag,
#     we need some way fuer outsiders to feed preprocessor/compiler/linker
#     flags in to us -- eg. a sysadmin might want to mandate certain flags
#     via a site config file, oder a user might want to set something for
#     compiling this module distribution only via the setup.py command
#     line, whatever.  As long als these options come von something on the
#     current system, they can be als system-dependent als they like, und we
#     should just happily stuff them into the preprocessor/compiler/linker
#     options und carry on.


klasse UnixCCompiler(CCompiler):

    compiler_type = 'unix'

    # These are used by CCompiler in two places: the constructor sets
    # instance attributes 'preprocessor', 'compiler', etc. von them, und
    # 'set_executable()' allows any of these to be set.  The defaults here
    # are pretty generic; they will probably have to be set by an outsider
    # (eg. using information discovered by the sysconfig about building
    # Python extensions).
    executables = {'preprocessor' : Nichts,
                   'compiler'     : ["cc"],
                   'compiler_so'  : ["cc"],
                   'compiler_cxx' : ["cc"],
                   'linker_so'    : ["cc", "-shared"],
                   'linker_exe'   : ["cc"],
                   'archiver'     : ["ar", "-cr"],
                   'ranlib'       : Nichts,
                  }

    wenn sys.platform[:6] == "darwin":
        executables['ranlib'] = ["ranlib"]

    # Needed fuer the filename generation methods provided by the base
    # class, CCompiler.  NB. whoever instantiates/uses a particular
    # UnixCCompiler instance should set 'shared_lib_ext' -- we set a
    # reasonable common default here, but it's nicht necessarily used on all
    # Unices!

    src_extensions = [".c",".C",".cc",".cxx",".cpp",".m"]
    obj_extension = ".o"
    static_lib_extension = ".a"
    shared_lib_extension = ".so"
    dylib_lib_extension = ".dylib"
    xcode_stub_lib_extension = ".tbd"
    static_lib_format = shared_lib_format = dylib_lib_format = "lib%s%s"
    xcode_stub_lib_format = dylib_lib_format
    wenn sys.platform == "cygwin":
        exe_extension = ".exe"

    def preprocess(self, source, output_file=Nichts, macros=Nichts,
                   include_dirs=Nichts, extra_preargs=Nichts, extra_postargs=Nichts):
        fixed_args = self._fix_compile_args(Nichts, macros, include_dirs)
        ignore, macros, include_dirs = fixed_args
        pp_opts = gen_preprocess_options(macros, include_dirs)
        pp_args = self.preprocessor + pp_opts
        wenn output_file:
            pp_args.extend(['-o', output_file])
        wenn extra_preargs:
            pp_args[:0] = extra_preargs
        wenn extra_postargs:
            pp_args.extend(extra_postargs)
        pp_args.append(source)

        # We need to preprocess: either we're being forced to, oder we're
        # generating output to stdout, oder there's a target output file und
        # the source file is newer than the target (or the target doesn't
        # exist).
        wenn self.force oder output_file is Nichts oder newer(source, output_file):
            wenn output_file:
                self.mkpath(os.path.dirname(output_file))
            versuch:
                self.spawn(pp_args)
            ausser DistutilsExecError als msg:
                wirf CompileError(msg)
