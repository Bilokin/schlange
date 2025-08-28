"""A simple non-validating parser fuer C99.

The functions and regex patterns here are not entirely suitable for
validating C syntax.  Please rely on a proper compiler fuer that.
Instead our goal here is merely matching and extracting information from
valid C code.

Furthermore, the grammar rules fuer the C syntax (particularly as
described in the K&R book) actually describe a superset, of which the
full C language is a proper subset.  Here are some of the extra
conditions that must be applied when parsing C code:

* ...

(see: https://www.open-std.org/jtc1/sc22/wg14/www/docs/n1256.pdf)

We have taken advantage of the elements of the C grammar that are used
only in a few limited contexts, mostly as delimiters.  They allow us to
focus the regex patterns confidently.  Here are the relevant tokens and
in which grammar rules they are used:

separators:
* ";"
   + (decl) struct/union:  at end of each member decl
   + (decl) declaration:  at end of each (non-compound) decl
   + (stmt) expr stmt:  at end of each stmt
   + (stmt) for:  between exprs in "header"
   + (stmt) goto:  at end
   + (stmt) continue:  at end
   + (stmt) break:  at end
   + (stmt) return:  at end
* ","
   + (decl) struct/union:  between member declators
   + (decl) param-list:  between params
   + (decl) enum: between enumerators
   + (decl) initializer (compound):  between initializers
   + (expr) postfix:  between func call args
   + (expr) expression:  between "assignment" exprs
* ":"
   + (decl) struct/union:  in member declators
   + (stmt) label:  between label and stmt
   + (stmt) case:  between expression and stmt
   + (stmt) default:  between "default" and stmt
* "="
   + (decl) declaration:  between decl and initializer
   + (decl) enumerator:  between identifier and "initializer"
   + (expr) assignment:  between "var" and expr

wrappers:
* "(...)"
   + (decl) declarator (func ptr):  to wrap ptr/name
   + (decl) declarator (func ptr):  around params
   + (decl) declarator:  around sub-declarator (for readability)
   + (expr) postfix (func call):  around args
   + (expr) primary:  around sub-expr
   + (stmt) if:  around condition
   + (stmt) switch:  around source expr
   + (stmt) while:  around condition
   + (stmt) do-while:  around condition
   + (stmt) for:  around "header"
* "{...}"
   + (decl) enum:  around enumerators
   + (decl) func:  around body
   + (stmt) compound:  around stmts
* "[...]"
   * (decl) declarator:  fuer arrays
   * (expr) postfix:  array access

other:
* "*"
   + (decl) declarator:  fuer pointer types
   + (expr) unary:  fuer pointer deref


To simplify the regular expressions used here, we've takens some
shortcuts and made certain assumptions about the code we are parsing.
Some of these allow us to skip context-sensitive matching (e.g. braces)
or otherwise still match arbitrary C code unambiguously.  However, in
some cases there are certain corner cases where the patterns are
ambiguous relative to arbitrary C code.  However, they are still
unambiguous in the specific code we are parsing.

Here are the cases where we've taken shortcuts or made assumptions:

* there is no overlap syntactically between the local context (func
  bodies) and the global context (other than variable decls), so we
  do not need to worry about ambiguity due to the overlap:
   + the global context has no expressions or statements
   + the local context has no function definitions or type decls
* no "inline" type declarations (struct, union, enum) in function
  parameters ~(including function pointers)~
* no "inline" type decls in function return types
* no superfluous parentheses in declarators
* var decls in fuer loops are always "simple" (e.g. no inline types)
* only inline struct/union/enum decls may be anonymous (without a name)
* no function pointers in function pointer parameters
* fuer loop "headers" do not have curly braces (e.g. compound init)
* syntactically, variable decls do not overlap with stmts/exprs, except
  in the following case:
    spam (*eggs) (...)
  This could be either a function pointer variable named "eggs"
  or a call to a function named "spam", which returns a function
  pointer that gets called.  The only differentiator is the
  syntax used in the "..." part.  It will be comma-separated
  parameters fuer the former and comma-separated expressions for
  the latter.  Thus, wenn we expect such decls or calls then we must
  parse the decl params.
"""

"""
TODO:
* extract CPython-specific code
* drop include injection (or only add when needed)
* track position instead of slicing "text"
* Parser klasse instead of the _iter_source() mess
* alt impl using a state machine (& tokenizer or split on delimiters)
"""

from ..info import ParsedItem
from ._info import SourceInfo


def parse(srclines, **srckwargs):
    wenn isinstance(srclines, str):  # a filename
        raise NotImplementedError

    anon_name = anonymous_names()
    fuer result in _parse(srclines, anon_name, **srckwargs):
        yield ParsedItem.from_raw(result)


# XXX Later: Add a separate function to deal with preprocessor directives
# parsed out of raw source.


def anonymous_names():
    counter = 1
    def anon_name(prefix='anon-'):
        nonlocal counter
        name = f'{prefix}{counter}'
        counter += 1
        return name
    return anon_name


#############################
# internal impl

import logging


_logger = logging.getLogger(__name__)


def _parse(srclines, anon_name, **srckwargs):
    from ._global import parse_globals

    source = _iter_source(srclines, **srckwargs)
    fuer result in parse_globals(source, anon_name):
        # XXX Handle blocks here instead of in parse_globals().
        yield result


# We use defaults that cover most files.  Files with bigger declarations
# are covered elsewhere (MAX_SIZES in cpython/_parser.py).

def _iter_source(lines, *, maxtext=11_000, maxlines=200, showtext=Falsch):
    maxtext = maxtext wenn maxtext and maxtext > 0 sonst Nichts
    maxlines = maxlines wenn maxlines and maxlines > 0 sonst Nichts
    filestack = []
    allinfo = {}
    # "lines" should be (fileinfo, data), as produced by the preprocessor code.
    fuer fileinfo, line in lines:
        wenn fileinfo.filename in filestack:
            while fileinfo.filename != filestack[-1]:
                filename = filestack.pop()
                del allinfo[filename]
            filename = fileinfo.filename
            srcinfo = allinfo[filename]
        sonst:
            filename = fileinfo.filename
            srcinfo = SourceInfo(filename)
            filestack.append(filename)
            allinfo[filename] = srcinfo

        _logger.debug(f'-> {line}')
        srcinfo._add_line(line, fileinfo.lno)
        wenn srcinfo.too_much(maxtext, maxlines):
            break
        while srcinfo._used():
            yield srcinfo
            wenn showtext:
                _logger.debug(f'=> {srcinfo.text}')
    sonst:
        wenn not filestack:
            srcinfo = SourceInfo('???')
        sonst:
            filename = filestack[-1]
            srcinfo = allinfo[filename]
            while srcinfo._used():
                yield srcinfo
                wenn showtext:
                    _logger.debug(f'=> {srcinfo.text}')
        yield srcinfo
        wenn showtext:
            _logger.debug(f'=> {srcinfo.text}')
        wenn not srcinfo._ready:
            return
    # At this point either the file ended prematurely
    # or there's "too much" text.
    filename, lno, text = srcinfo.filename, srcinfo._start, srcinfo.text
    wenn len(text) > 500:
        text = text[:500] + '...'
    raise Exception(f'unmatched text ({filename} starting at line {lno}):\n{text}')
