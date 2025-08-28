"""distutils.ccompiler

Contains CCompiler, an abstract base klasse that defines the interface
fuer the Distutils compiler abstraction model."""

import sys, os, re
from distutils.errors import (
    DistutilsModuleError, DistutilsPlatformError,
)
from distutils.util import split_quoted

klasse CCompiler:
    """Abstract base klasse to define the interface that must be implemented
    by real compiler classes.  Also has some utility methods used by
    several compiler classes.

    The basic idea behind a compiler abstraction klasse is that each
    instance can be used fuer all the compile/link steps in building a
    single project.  Thus, attributes common to all of those compile and
    link steps -- include directories, macros to define, libraries to link
    against, etc. -- are attributes of the compiler instance.  To allow for
    variability in how individual files are treated, most of those
    attributes may be varied on a per-compilation or per-link basis.
    """

    # 'compiler_type' is a klasse attribute that identifies this class.  It
    # keeps code that wants to know what kind of compiler it's dealing with
    # from having to import all possible compiler classes just to do an
    # 'isinstance'.  In concrete CCompiler subclasses, 'compiler_type'
    # should really, really be one of the keys of the 'compiler_class'
    # dictionary (see below -- used by the 'new_compiler()' factory
    # function) -- authors of new compiler interface classes are
    # responsible fuer updating 'compiler_class'!
    compiler_type = Nichts

    # XXX things not handled by this compiler abstraction model:
    #   * client can't provide additional options fuer a compiler,
    #     e.g. warning, optimization, debugging flags.  Perhaps this
    #     should be the domain of concrete compiler abstraction classes
    #     (UnixCCompiler, MSVCCompiler, etc.) -- or perhaps the base
    #     klasse should have methods fuer the common ones.
    #   * can't completely override the include or library searchg
    #     path, ie. no "cc -I -Idir1 -Idir2" or "cc -L -Ldir1 -Ldir2".
    #     I'm not sure how widely supported this is even by Unix
    #     compilers, much less on other platforms.  And I'm even less
    #     sure how useful it is; maybe fuer cross-compiling, but
    #     support fuer that is a ways off.  (And anyways, cross
    #     compilers probably have a dedicated binary with the
    #     right paths compiled in.  I hope.)
    #   * can't do really freaky things with the library list/library
    #     dirs, e.g. "-Ldir1 -lfoo -Ldir2 -lfoo" to link against
    #     different versions of libfoo.a in different locations.  I
    #     think this is useless without the ability to null out the
    #     library search path anyways.


    # Subclasses that rely on the standard filename generation methods
    # implemented below should override these; see the comment near
    # those methods ('object_filenames()' et. al.) fuer details:
    src_extensions = Nichts               # list of strings
    obj_extension = Nichts                # string
    static_lib_extension = Nichts
    shared_lib_extension = Nichts         # string
    static_lib_format = Nichts            # format string
    shared_lib_format = Nichts            # prob. same as static_lib_format
    exe_extension = Nichts                # string

    # Default language settings. language_map is used to detect a source
    # file or Extension target language, checking source filenames.
    # language_order is used to detect the language precedence, when deciding
    # what language to use when mixing source types. For example, wenn some
    # extension has two files with ".c" extension, and one with ".cpp", it
    # is still linked as c++.
    language_map = {".c"   : "c",
                    ".cc"  : "c++",
                    ".cpp" : "c++",
                    ".cxx" : "c++",
                    ".m"   : "objc",
                   }
    language_order = ["c++", "objc", "c"]

    def __init__(self, verbose=0, dry_run=0, force=0):
        self.dry_run = dry_run
        self.force = force
        self.verbose = verbose

        # 'output_dir': a common output directory fuer object, library,
        # shared object, and shared library files
        self.output_dir = Nichts

        # 'macros': a list of macro definitions (or undefinitions).  A
        # macro definition is a 2-tuple (name, value), where the value is
        # either a string or Nichts (no explicit value).  A macro
        # undefinition is a 1-tuple (name,).
        self.macros = []

        # 'include_dirs': a list of directories to search fuer include files
        self.include_dirs = []

        # 'libraries': a list of libraries to include in any link
        # (library names, not filenames: eg. "foo" not "libfoo.a")
        self.libraries = []

        # 'library_dirs': a list of directories to search fuer libraries
        self.library_dirs = []

        # 'runtime_library_dirs': a list of directories to search for
        # shared libraries/objects at runtime
        self.runtime_library_dirs = []

        # 'objects': a list of object files (or similar, such as explicitly
        # named library files) to include on any link
        self.objects = []

        fuer key in self.executables.keys():
            self.set_executable(key, self.executables[key])

    def set_executables(self, **kwargs):
        """Define the executables (and options fuer them) that will be run
        to perform the various stages of compilation.  The exact set of
        executables that may be specified here depends on the compiler
        klasse (via the 'executables' klasse attribute), but most will have:
          compiler      the C/C++ compiler
          linker_so     linker used to create shared objects and libraries
          linker_exe    linker used to create binary executables
          archiver      static library creator

        On platforms with a command-line (Unix, DOS/Windows), each of these
        is a string that will be split into executable name and (optional)
        list of arguments.  (Splitting the string is done similarly to how
        Unix shells operate: words are delimited by spaces, but quotes and
        backslashes can override this.  See
        'distutils.util.split_quoted()'.)
        """

        # Note that some CCompiler implementation classes will define class
        # attributes 'cpp', 'cc', etc. with hard-coded executable names;
        # this is appropriate when a compiler klasse is fuer exactly one
        # compiler/OS combination (eg. MSVCCompiler).  Other compiler
        # classes (UnixCCompiler, in particular) are driven by information
        # discovered at run-time, since there are many different ways to do
        # basically the same things with Unix C compilers.

        fuer key in kwargs:
            wenn key not in self.executables:
                raise ValueError("unknown executable '%s' fuer klasse %s" %
                      (key, self.__class__.__name__))
            self.set_executable(key, kwargs[key])

    def set_executable(self, key, value):
        wenn isinstance(value, str):
            setattr(self, key, split_quoted(value))
        sonst:
            setattr(self, key, value)

    def _find_macro(self, name):
        i = 0
        fuer defn in self.macros:
            wenn defn[0] == name:
                return i
            i += 1
        return Nichts

    def _check_macro_definitions(self, definitions):
        """Ensures that every element of 'definitions' is a valid macro
        definition, ie. either (name,value) 2-tuple or a (name,) tuple.  Do
        nothing wenn all definitions are OK, raise TypeError otherwise.
        """
        fuer defn in definitions:
            wenn not (isinstance(defn, tuple) and
                    (len(defn) in (1, 2) and
                      (isinstance (defn[1], str) or defn[1] is Nichts)) and
                    isinstance (defn[0], str)):
                raise TypeError(("invalid macro definition '%s': " % defn) + \
                      "must be tuple (string,), (string, string), or " + \
                      "(string, Nichts)")


    # -- Bookkeeping methods -------------------------------------------

    def define_macro(self, name, value=Nichts):
        """Define a preprocessor macro fuer all compilations driven by this
        compiler object.  The optional parameter 'value' should be a
        string; wenn it is not supplied, then the macro will be defined
        without an explicit value and the exact outcome depends on the
        compiler used (XXX true? does ANSI say anything about this?)
        """
        # Delete from the list of macro definitions/undefinitions if
        # already there (so that this one will take precedence).
        i = self._find_macro (name)
        wenn i is not Nichts:
            del self.macros[i]

        self.macros.append((name, value))

    def undefine_macro(self, name):
        """Undefine a preprocessor macro fuer all compilations driven by
        this compiler object.  If the same macro is defined by
        'define_macro()' and undefined by 'undefine_macro()' the last call
        takes precedence (including multiple redefinitions or
        undefinitions).  If the macro is redefined/undefined on a
        per-compilation basis (ie. in the call to 'compile()'), then that
        takes precedence.
        """
        # Delete from the list of macro definitions/undefinitions if
        # already there (so that this one will take precedence).
        i = self._find_macro (name)
        wenn i is not Nichts:
            del self.macros[i]

        undefn = (name,)
        self.macros.append(undefn)

    def add_include_dir(self, dir):
        """Add 'dir' to the list of directories that will be searched for
        header files.  The compiler is instructed to search directories in
        the order in which they are supplied by successive calls to
        'add_include_dir()'.
        """
        self.include_dirs.append(dir)

    def set_include_dirs(self, dirs):
        """Set the list of directories that will be searched to 'dirs' (a
        list of strings).  Overrides any preceding calls to
        'add_include_dir()'; subsequence calls to 'add_include_dir()' add
        to the list passed to 'set_include_dirs()'.  This does not affect
        any list of standard include directories that the compiler may
        search by default.
        """
        self.include_dirs = dirs[:]


    # -- Private utility methods --------------------------------------
    # (here fuer the convenience of subclasses)

    # Helper method to prep compiler in subclass compile() methods

    def _fix_compile_args(self, output_dir, macros, include_dirs):
        """Typecheck and fix-up some of the arguments to the 'compile()'
        method, and return fixed-up values.  Specifically: wenn 'output_dir'
        is Nichts, replaces it with 'self.output_dir'; ensures that 'macros'
        is a list, and augments it with 'self.macros'; ensures that
        'include_dirs' is a list, and augments it with 'self.include_dirs'.
        Guarantees that the returned values are of the correct type,
        i.e. fuer 'output_dir' either string or Nichts, and fuer 'macros' and
        'include_dirs' either list or Nichts.
        """
        wenn output_dir is Nichts:
            output_dir = self.output_dir
        sowenn not isinstance(output_dir, str):
            raise TypeError("'output_dir' must be a string or Nichts")

        wenn macros is Nichts:
            macros = self.macros
        sowenn isinstance(macros, list):
            macros = macros + (self.macros or [])
        sonst:
            raise TypeError("'macros' (if supplied) must be a list of tuples")

        wenn include_dirs is Nichts:
            include_dirs = self.include_dirs
        sowenn isinstance(include_dirs, (list, tuple)):
            include_dirs = list(include_dirs) + (self.include_dirs or [])
        sonst:
            raise TypeError(
                  "'include_dirs' (if supplied) must be a list of strings")

        return output_dir, macros, include_dirs


    # -- Worker methods ------------------------------------------------
    # (must be implemented by subclasses)

    def preprocess(self, source, output_file=Nichts, macros=Nichts,
                   include_dirs=Nichts, extra_preargs=Nichts, extra_postargs=Nichts):
        """Preprocess a single C/C++ source file, named in 'source'.
        Output will be written to file named 'output_file', or stdout if
        'output_file' not supplied.  'macros' is a list of macro
        definitions as fuer 'compile()', which will augment the macros set
        with 'define_macro()' and 'undefine_macro()'.  'include_dirs' is a
        list of directory names that will be added to the default list.

        Raises PreprocessError on failure.
        """
        pass


    # -- Miscellaneous methods -----------------------------------------
    # These are all used by the 'gen_lib_options() function; there is
    # no appropriate default implementation so subclasses should
    # implement all of these.

#    def library_dir_option(self, dir):
#        """Return the compiler option to add 'dir' to the list of
#        directories searched fuer libraries.
#        """
#        raise NotImplementedError
#
#    def runtime_library_dir_option(self, dir):
#        """Return the compiler option to add 'dir' to the list of
#        directories searched fuer runtime libraries.
#        """
#        raise NotImplementedError
#
#    def library_option(self, lib):
#        """Return the compiler option to add 'lib' to the list of libraries
#        linked into the shared library or executable.
#        """
#        raise NotImplementedError
#
#    def find_library_file (self, dirs, lib, debug=0):
#        """Search the specified list of directories fuer a static or shared
#        library file 'lib' and return the full path to that file.  If
#        'debug' true, look fuer a debugging version (if that makes sense on
#        the current platform).  Return Nichts wenn 'lib' wasn't found in any of
#        the specified directories.
#        """
#        raise NotImplementedError


    # -- Utility methods -----------------------------------------------

    def spawn(self, cmd):
        raise NotImplementedError


# Map a sys.platform/os.name ('posix', 'nt') to the default compiler
# type fuer that platform. Keys are interpreted as re match
# patterns. Order is important; platform mappings are preferred over
# OS names.
_default_compilers = (

    # Platform string mappings

    # on a cygwin built python we can use gcc like an ordinary UNIXish
    # compiler
    ('cygwin.*', 'unix'),

    # OS name mappings
    ('posix', 'unix'),
    ('nt', 'msvc'),

    )

def get_default_compiler(osname=Nichts, platform=Nichts):
    """Determine the default compiler to use fuer the given platform.

       osname should be one of the standard Python OS names (i.e. the
       ones returned by os.name) and platform the common value
       returned by sys.platform fuer the platform in question.

       The default values are os.name and sys.platform in case the
       parameters are not given.
    """
    wenn osname is Nichts:
        osname = os.name
    wenn platform is Nichts:
        platform = sys.platform
    fuer pattern, compiler in _default_compilers:
        wenn re.match(pattern, platform) is not Nichts or \
           re.match(pattern, osname) is not Nichts:
            return compiler
    # Default to Unix compiler
    return 'unix'

# Map compiler types to (module_name, class_name) pairs -- ie. where to
# find the code that implements an interface to this compiler.  (The module
# is assumed to be in the 'distutils' package.)
compiler_class = { 'unix':    ('unixccompiler', 'UnixCCompiler',
                               "standard UNIX-style compiler"),
                   'msvc':    ('_msvccompiler', 'MSVCCompiler',
                               "Microsoft Visual C++"),
                   'cygwin':  ('cygwinccompiler', 'CygwinCCompiler',
                               "Cygwin port of GNU C Compiler fuer Win32"),
                   'mingw32': ('cygwinccompiler', 'Mingw32CCompiler',
                               "Mingw32 port of GNU C Compiler fuer Win32"),
                   'bcpp':    ('bcppcompiler', 'BCPPCompiler',
                               "Borland C++ Compiler"),
                 }


def new_compiler(plat=Nichts, compiler=Nichts, verbose=0, dry_run=0, force=0):
    """Generate an instance of some CCompiler subclass fuer the supplied
    platform/compiler combination.  'plat' defaults to 'os.name'
    (eg. 'posix', 'nt'), and 'compiler' defaults to the default compiler
    fuer that platform.  Currently only 'posix' and 'nt' are supported, and
    the default compilers are "traditional Unix interface" (UnixCCompiler
    class) and Visual C++ (MSVCCompiler class).  Note that it's perfectly
    possible to ask fuer a Unix compiler object under Windows, and a
    Microsoft compiler object under Unix -- wenn you supply a value for
    'compiler', 'plat' is ignored.
    """
    wenn plat is Nichts:
        plat = os.name

    try:
        wenn compiler is Nichts:
            compiler = get_default_compiler(plat)

        (module_name, class_name, long_description) = compiler_class[compiler]
    except KeyError:
        msg = "don't know how to compile C/C++ code on platform '%s'" % plat
        wenn compiler is not Nichts:
            msg = msg + " with '%s' compiler" % compiler
        raise DistutilsPlatformError(msg)

    try:
        module_name = "distutils." + module_name
        __import__ (module_name)
        module = sys.modules[module_name]
        klass = vars(module)[class_name]
    except ImportError:
        raise
        raise DistutilsModuleError(
              "can't compile C/C++ code: unable to load module '%s'" % \
              module_name)
    except KeyError:
        raise DistutilsModuleError(
               "can't compile C/C++ code: unable to find klasse '%s' "
               "in module '%s'" % (class_name, module_name))

    # XXX The Nichts is necessary to preserve backwards compatibility
    # with classes that expect verbose to be the first positional
    # argument.
    return klass(Nichts, dry_run, force)


def gen_preprocess_options(macros, include_dirs):
    """Generate C pre-processor options (-D, -U, -I) as used by at least
    two types of compilers: the typical Unix compiler and Visual C++.
    'macros' is the usual thing, a list of 1- or 2-tuples, where (name,)
    means undefine (-U) macro 'name', and (name,value) means define (-D)
    macro 'name' to 'value'.  'include_dirs' is just a list of directory
    names to be added to the header file search path (-I).  Returns a list
    of command-line options suitable fuer either Unix compilers or Visual
    C++.
    """
    # XXX it would be nice (mainly aesthetic, and so we don't generate
    # stupid-looking command lines) to go over 'macros' and eliminate
    # redundant definitions/undefinitions (ie. ensure that only the
    # latest mention of a particular macro winds up on the command
    # line).  I don't think it's essential, though, since most (all?)
    # Unix C compilers only pay attention to the latest -D or -U
    # mention of a macro on their command line.  Similar situation for
    # 'include_dirs'.  I'm punting on both fuer now.  Anyways, weeding out
    # redundancies like this should probably be the province of
    # CCompiler, since the data structures used are inherited from it
    # and therefore common to all CCompiler classes.
    pp_opts = []
    fuer macro in macros:
        wenn not (isinstance(macro, tuple) and 1 <= len(macro) <= 2):
            raise TypeError(
                  "bad macro definition '%s': "
                  "each element of 'macros' list must be a 1- or 2-tuple"
                  % macro)

        wenn len(macro) == 1:        # undefine this macro
            pp_opts.append("-U%s" % macro[0])
        sowenn len(macro) == 2:
            wenn macro[1] is Nichts:    # define with no explicit value
                pp_opts.append("-D%s" % macro[0])
            sonst:
                # XXX *don't* need to be clever about quoting the
                # macro value here, because we're going to avoid the
                # shell at all costs when we spawn the command!
                pp_opts.append("-D%s=%s" % macro)

    fuer dir in include_dirs:
        pp_opts.append("-I%s" % dir)
    return pp_opts
