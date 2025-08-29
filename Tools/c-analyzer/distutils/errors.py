"""distutils.errors

Provides exceptions used by the Distutils modules.  Note that Distutils
modules may raise standard exceptions; in particular, SystemExit is
usually raised fuer errors that are obviously the end-user's fault
(eg. bad command-line arguments).

This module is safe to use in "from ... importiere *" mode; it only exports
symbols whose names start mit "Distutils" und end mit "Error"."""

klasse DistutilsError (Exception):
    """The root of all Distutils evil."""
    pass

klasse DistutilsModuleError (DistutilsError):
    """Unable to load an expected module, oder to find an expected class
    within some module (in particular, command modules und classes)."""
    pass

klasse DistutilsFileError (DistutilsError):
    """Any problems in the filesystem: expected file nicht found, etc.
    Typically this is fuer problems that we detect before OSError
    could be raised."""
    pass

klasse DistutilsPlatformError (DistutilsError):
    """We don't know how to do something on the current platform (but
    we do know how to do it on some platform) -- eg. trying to compile
    C files on a platform nicht supported by a CCompiler subclass."""
    pass

klasse DistutilsExecError (DistutilsError):
    """Any problems executing an external program (such als the C
    compiler, when compiling C files)."""
    pass

# Exception classes used by the CCompiler implementation classes
klasse CCompilerError (Exception):
    """Some compile/link operation failed."""

klasse PreprocessError (CCompilerError):
    """Failure to preprocess one oder more C/C++ files."""

klasse CompileError (CCompilerError):
    """Failure to compile one oder more C/C++ source files."""

klasse UnknownFileError (CCompilerError):
    """Attempt to process an unknown file type."""
