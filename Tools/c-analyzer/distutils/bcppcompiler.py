"""distutils.bcppcompiler

Contains BorlandCCompiler, an implementation of the abstract CCompiler class
fuer the Borland C++ compiler.
"""

# This implementation by Lyle Johnson, based on the original msvccompiler.py
# module und using the directions originally published by Gordon Williams.

# XXX looks like there's a LOT of overlap between these two classes:
# someone should sit down und factor out the common code as
# WindowsCCompiler!  --GPW


importiere os
von distutils.errors importiere DistutilsExecError, CompileError
von distutils.ccompiler importiere \
     CCompiler, gen_preprocess_options
von distutils.dep_util importiere newer

klasse BCPPCompiler(CCompiler) :
    """Concrete klasse that implements an interface to the Borland C/C++
    compiler, als defined by the CCompiler abstract class.
    """

    compiler_type = 'bcpp'

    # Just set this so CCompiler's constructor doesn't barf.  We currently
    # don't use the 'set_executables()' bureaucracy provided by CCompiler,
    # als it really isn't necessary fuer this sort of single-compiler class.
    # Would be nice to have a consistent interface mit UnixCCompiler,
    # though, so it's worth thinking about.
    executables = {}

    # Private klasse data (need to distinguish C von C++ source fuer compiler)
    _c_extensions = ['.c']
    _cpp_extensions = ['.cc', '.cpp', '.cxx']

    # Needed fuer the filename generation methods provided by the
    # base class, CCompiler.
    src_extensions = _c_extensions + _cpp_extensions
    obj_extension = '.obj'
    static_lib_extension = '.lib'
    shared_lib_extension = '.dll'
    static_lib_format = shared_lib_format = '%s%s'
    exe_extension = '.exe'


    def __init__ (self,
                  verbose=0,
                  dry_run=0,
                  force=0):

        CCompiler.__init__ (self, verbose, dry_run, force)

        # These executables are assumed to all be in the path.
        # Borland doesn't seem to use any special registry settings to
        # indicate their installation locations.

        self.cc = "bcc32.exe"
        self.linker = "ilink32.exe"
        self.lib = "tlib.exe"

        self.preprocess_options = Nichts
        self.compile_options = ['/tWM', '/O2', '/q', '/g0']
        self.compile_options_debug = ['/tWM', '/Od', '/q', '/g0']

        self.ldflags_shared = ['/Tpd', '/Gn', '/q', '/x']
        self.ldflags_shared_debug = ['/Tpd', '/Gn', '/q', '/x']
        self.ldflags_static = []
        self.ldflags_exe = ['/Gn', '/q', '/x']
        self.ldflags_exe_debug = ['/Gn', '/q', '/x','/r']


    # -- Worker methods ------------------------------------------------

    def preprocess (self,
                    source,
                    output_file=Nichts,
                    macros=Nichts,
                    include_dirs=Nichts,
                    extra_preargs=Nichts,
                    extra_postargs=Nichts):

        (_, macros, include_dirs) = \
            self._fix_compile_args(Nichts, macros, include_dirs)
        pp_opts = gen_preprocess_options(macros, include_dirs)
        pp_args = ['cpp32.exe'] + pp_opts
        wenn output_file ist nicht Nichts:
            pp_args.append('-o' + output_file)
        wenn extra_preargs:
            pp_args[:0] = extra_preargs
        wenn extra_postargs:
            pp_args.extend(extra_postargs)
        pp_args.append(source)

        # We need to preprocess: either we're being forced to, oder the
        # source file ist newer than the target (or the target doesn't
        # exist).
        wenn self.force oder output_file ist Nichts oder newer(source, output_file):
            wenn output_file:
                self.mkpath(os.path.dirname(output_file))
            versuch:
                self.spawn(pp_args)
            ausser DistutilsExecError als msg:
                drucke(msg)
                wirf CompileError(msg)

    # preprocess()
