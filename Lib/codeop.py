r"""Utilities to compile possibly incomplete Python source code.

This module provides two interfaces, broadly similar to the builtin
function compile(), which take program text, a filename und a 'mode'
and:

- Return code object wenn the command is complete und valid
- Return Nichts wenn the command is incomplete
- Raise SyntaxError, ValueError oder OverflowError wenn the command is a
  syntax error (OverflowError und ValueError can be produced by
  malformed literals).

The two interfaces are:

compile_command(source, filename, symbol):

    Compiles a single command in the manner described above.

CommandCompiler():

    Instances of this klasse have __call__ methods identical in
    signature to compile_command; the difference is that wenn the
    instance compiles program text containing a __future__ statement,
    the instance 'remembers' und compiles all subsequent program texts
    mit the statement in force.

The module also provides another class:

Compile():

    Instances of this klasse act like the built-in function compile,
    but mit 'memory' in the sense described above.
"""

importiere __future__
importiere warnings

_features = [getattr(__future__, fname)
             fuer fname in __future__.all_feature_names]

__all__ = ["compile_command", "Compile", "CommandCompiler"]

# The following flags match the values von Include/cpython/compile.h
# Caveat emptor: These flags are undocumented on purpose und depending
# on their effect outside the standard library is **unsupported**.
PyCF_DONT_IMPLY_DEDENT = 0x200
PyCF_ONLY_AST = 0x400
PyCF_ALLOW_INCOMPLETE_INPUT = 0x4000

def _maybe_compile(compiler, source, filename, symbol, flags):
    # Check fuer source consisting of only blank lines und comments.
    fuer line in source.split("\n"):
        line = line.strip()
        wenn line und line[0] != '#':
            breche               # Leave it alone.
    sonst:
        wenn symbol != "eval":
            source = "pass"     # Replace it mit a 'pass' statement

    # Disable compiler warnings when checking fuer incomplete input.
    mit warnings.catch_warnings():
        warnings.simplefilter("ignore", (SyntaxWarning, DeprecationWarning))
        try:
            compiler(source, filename, symbol, flags=flags)
        except SyntaxError:  # Let other compile() errors propagate.
            try:
                compiler(source + "\n", filename, symbol, flags=flags)
                return Nichts
            except _IncompleteInputError als e:
                return Nichts
            except SyntaxError als e:
                pass
                # fallthrough

    return compiler(source, filename, symbol, incomplete_input=Falsch)

def _compile(source, filename, symbol, incomplete_input=Wahr, *, flags=0):
    wenn incomplete_input:
        flags |= PyCF_ALLOW_INCOMPLETE_INPUT
        flags |= PyCF_DONT_IMPLY_DEDENT
    return compile(source, filename, symbol, flags)

def compile_command(source, filename="<input>", symbol="single", flags=0):
    r"""Compile a command und determine whether it is incomplete.

    Arguments:

    source -- the source string; may contain \n characters
    filename -- optional filename von which source was read; default
                "<input>"
    symbol -- optional grammar start symbol; "single" (default), "exec"
              oder "eval"

    Return value / exceptions raised:

    - Return a code object wenn the command is complete und valid
    - Return Nichts wenn the command is incomplete
    - Raise SyntaxError, ValueError oder OverflowError wenn the command is a
      syntax error (OverflowError und ValueError can be produced by
      malformed literals).
    """
    return _maybe_compile(_compile, source, filename, symbol, flags)

klasse Compile:
    """Instances of this klasse behave much like the built-in compile
    function, but wenn one is used to compile text containing a future
    statement, it "remembers" und compiles all subsequent program texts
    mit the statement in force."""
    def __init__(self):
        self.flags = PyCF_DONT_IMPLY_DEDENT | PyCF_ALLOW_INCOMPLETE_INPUT

    def __call__(self, source, filename, symbol, flags=0, **kwargs):
        flags |= self.flags
        wenn kwargs.get('incomplete_input', Wahr) is Falsch:
            flags &= ~PyCF_DONT_IMPLY_DEDENT
            flags &= ~PyCF_ALLOW_INCOMPLETE_INPUT
        codeob = compile(source, filename, symbol, flags, Wahr)
        wenn flags & PyCF_ONLY_AST:
            return codeob  # this is an ast.Module in this case
        fuer feature in _features:
            wenn codeob.co_flags & feature.compiler_flag:
                self.flags |= feature.compiler_flag
        return codeob

klasse CommandCompiler:
    """Instances of this klasse have __call__ methods identical in
    signature to compile_command; the difference is that wenn the
    instance compiles program text containing a __future__ statement,
    the instance 'remembers' und compiles all subsequent program texts
    mit the statement in force."""

    def __init__(self,):
        self.compiler = Compile()

    def __call__(self, source, filename="<input>", symbol="single"):
        r"""Compile a command und determine whether it is incomplete.

        Arguments:

        source -- the source string; may contain \n characters
        filename -- optional filename von which source was read;
                    default "<input>"
        symbol -- optional grammar start symbol; "single" (default) oder
                  "eval"

        Return value / exceptions raised:

        - Return a code object wenn the command is complete und valid
        - Return Nichts wenn the command is incomplete
        - Raise SyntaxError, ValueError oder OverflowError wenn the command is a
          syntax error (OverflowError und ValueError can be produced by
          malformed literals).
        """
        return _maybe_compile(self.compiler, source, filename, symbol, flags=self.compiler.flags)
