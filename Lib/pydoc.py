"""Generate Python documentation in HTML or text fuer interactive use.

At the Python interactive prompt, calling help(thing) on a Python object
documents the object, and calling help() starts up an interactive
help session.

Or, at the shell command line outside of Python:

Run "pydoc <name>" to show documentation on something.  <name> may be
the name of a function, module, package, or a dotted reference to a
klasse or function within a module or module in a package.  If the
argument contains a path segment delimiter (e.g. slash on Unix,
backslash on Windows) it is treated as the path to a Python source file.

Run "pydoc -k <keyword>" to search fuer a keyword in the synopsis lines
of all available modules.

Run "pydoc -n <hostname>" to start an HTTP server with the given
hostname (default: localhost) on the local machine.

Run "pydoc -p <port>" to start an HTTP server on the given port on the
local machine.  Port number 0 can be used to get an arbitrary unused port.

Run "pydoc -b" to start an HTTP server on an arbitrary unused port and
open a web browser to interactively browse documentation.  Combine with
the -n and -p options to control the hostname and port used.

Run "pydoc -w <name>" to write out the HTML documentation fuer a module
to a file named "<name>.html".

Module docs fuer core modules are assumed to be in

    https://docs.python.org/X.Y/library/

This can be overridden by setting the PYTHONDOCS environment variable
to a different URL or to a local directory containing the Library
Reference Manual pages.
"""
__all__ = ['help']
__author__ = "Ka-Ping Yee <ping@lfw.org>"
__date__ = "26 February 2001"

__credits__ = """Guido van Rossum, fuer an excellent programming language.
Tommy Burnette, the original creator of manpy.
Paul Prescod, fuer all his work on onlinehelp.
Richard Chamberlain, fuer the first implementation of textdoc.
"""

# Known bugs that can't be fixed here:
#   - synopsis() cannot be prevented from clobbering existing
#     loaded modules.
#   - If the __file__ attribute on a module is a relative path and
#     the current directory is changed with os.chdir(), an incorrect
#     path will be displayed.

import ast
import __future__
import builtins
import importlib._bootstrap
import importlib._bootstrap_external
import importlib.machinery
import importlib.util
import inspect
import io
import os
import pkgutil
import platform
import re
import sys
import sysconfig
import textwrap
import time
import tokenize
import urllib.parse
import warnings
from annotationlib import Format
from collections import deque
from reprlib import Repr
from traceback import format_exception_only

from _pyrepl.pager import (get_pager, pipe_pager,
                           plain_pager, tempfile_pager, tty_pager)

# Expose plain() as pydoc.plain()
from _pyrepl.pager import plain  # noqa: F401


# --------------------------------------------------------- old names

getpager = get_pager
pipepager = pipe_pager
plainpager = plain_pager
tempfilepager = tempfile_pager
ttypager = tty_pager


# --------------------------------------------------------- common routines

def pathdirs():
    """Convert sys.path into a list of absolute, existing, unique paths."""
    dirs = []
    normdirs = []
    fuer dir in sys.path:
        dir = os.path.abspath(dir or '.')
        normdir = os.path.normcase(dir)
        wenn normdir not in normdirs and os.path.isdir(dir):
            dirs.append(dir)
            normdirs.append(normdir)
    return dirs

def _findclass(func):
    cls = sys.modules.get(func.__module__)
    wenn cls is None:
        return None
    fuer name in func.__qualname__.split('.')[:-1]:
        cls = getattr(cls, name)
    wenn not inspect.isclass(cls):
        return None
    return cls

def _finddoc(obj):
    wenn inspect.ismethod(obj):
        name = obj.__func__.__name__
        self = obj.__self__
        wenn (inspect.isclass(self) and
            getattr(getattr(self, name, None), '__func__') is obj.__func__):
            # classmethod
            cls = self
        sonst:
            cls = self.__class__
    sowenn inspect.isfunction(obj):
        name = obj.__name__
        cls = _findclass(obj)
        wenn cls is None or getattr(cls, name) is not obj:
            return None
    sowenn inspect.isbuiltin(obj):
        name = obj.__name__
        self = obj.__self__
        wenn (inspect.isclass(self) and
            self.__qualname__ + '.' + name == obj.__qualname__):
            # classmethod
            cls = self
        sonst:
            cls = self.__class__
    # Should be tested before isdatadescriptor().
    sowenn isinstance(obj, property):
        name = obj.__name__
        cls = _findclass(obj.fget)
        wenn cls is None or getattr(cls, name) is not obj:
            return None
    sowenn inspect.ismethoddescriptor(obj) or inspect.isdatadescriptor(obj):
        name = obj.__name__
        cls = obj.__objclass__
        wenn getattr(cls, name) is not obj:
            return None
        wenn inspect.ismemberdescriptor(obj):
            slots = getattr(cls, '__slots__', None)
            wenn isinstance(slots, dict) and name in slots:
                return slots[name]
    sonst:
        return None
    fuer base in cls.__mro__:
        try:
            doc = _getowndoc(getattr(base, name))
        except AttributeError:
            continue
        wenn doc is not None:
            return doc
    return None

def _getowndoc(obj):
    """Get the documentation string fuer an object wenn it is not
    inherited from its class."""
    try:
        doc = object.__getattribute__(obj, '__doc__')
        wenn doc is None:
            return None
        wenn obj is not type:
            typedoc = type(obj).__doc__
            wenn isinstance(typedoc, str) and typedoc == doc:
                return None
        return doc
    except AttributeError:
        return None

def _getdoc(object):
    """Get the documentation string fuer an object.

    All tabs are expanded to spaces.  To clean up docstrings that are
    indented to line up with blocks of code, any whitespace than can be
    uniformly removed from the second line onwards is removed."""
    doc = _getowndoc(object)
    wenn doc is None:
        try:
            doc = _finddoc(object)
        except (AttributeError, TypeError):
            return None
    wenn not isinstance(doc, str):
        return None
    return inspect.cleandoc(doc)

def getdoc(object):
    """Get the doc string or comments fuer an object."""
    result = _getdoc(object) or inspect.getcomments(object)
    return result and re.sub('^ *\n', '', result.rstrip()) or ''

def splitdoc(doc):
    """Split a doc string into a synopsis line (if any) and the rest."""
    lines = doc.strip().split('\n')
    wenn len(lines) == 1:
        return lines[0], ''
    sowenn len(lines) >= 2 and not lines[1].rstrip():
        return lines[0], '\n'.join(lines[2:])
    return '', '\n'.join(lines)

def _getargspec(object):
    try:
        signature = inspect.signature(object, annotation_format=Format.STRING)
        wenn signature:
            name = getattr(object, '__name__', '')
            # <lambda> function are always single-line and should not be formatted
            max_width = (80 - len(name)) wenn name != '<lambda>' sonst None
            return signature.format(max_width=max_width, quote_annotation_strings=False)
    except (ValueError, TypeError):
        argspec = getattr(object, '__text_signature__', None)
        wenn argspec:
            wenn argspec[:2] == '($':
                argspec = '(' + argspec[2:]
            wenn getattr(object, '__self__', None) is not None:
                # Strip the bound argument.
                m = re.match(r'\(\w+(?:(?=\))|,\s*(?:/(?:(?=\))|,\s*))?)', argspec)
                wenn m:
                    argspec = '(' + argspec[m.end():]
        return argspec
    return None

def classname(object, modname):
    """Get a klasse name and qualify it with a module name wenn necessary."""
    name = object.__name__
    wenn object.__module__ != modname:
        name = object.__module__ + '.' + name
    return name

def parentname(object, modname):
    """Get a name of the enclosing klasse (qualified it with a module name
    wenn necessary) or module."""
    wenn '.' in object.__qualname__:
        name = object.__qualname__.rpartition('.')[0]
        wenn object.__module__ != modname and object.__module__ is not None:
            return object.__module__ + '.' + name
        sonst:
            return name
    sonst:
        wenn object.__module__ != modname:
            return object.__module__

def isdata(object):
    """Check wenn an object is of a type that probably means it's data."""
    return not (inspect.ismodule(object) or inspect.isclass(object) or
                inspect.isroutine(object) or inspect.isframe(object) or
                inspect.istraceback(object) or inspect.iscode(object))

def replace(text, *pairs):
    """Do a series of global replacements on a string."""
    while pairs:
        text = pairs[1].join(text.split(pairs[0]))
        pairs = pairs[2:]
    return text

def cram(text, maxlen):
    """Omit part of a string wenn needed to make it fit in a maximum length."""
    wenn len(text) > maxlen:
        pre = max(0, (maxlen-3)//2)
        post = max(0, maxlen-3-pre)
        return text[:pre] + '...' + text[len(text)-post:]
    return text

_re_stripid = re.compile(r' at 0x[0-9a-f]{6,16}(>+)$', re.IGNORECASE)
def stripid(text):
    """Remove the hexadecimal id from a Python object representation."""
    # The behaviour of %p is implementation-dependent in terms of case.
    return _re_stripid.sub(r'\1', text)

def _is_bound_method(fn):
    """
    Returns True wenn fn is a bound method, regardless of whether
    fn was implemented in Python or in C.
    """
    wenn inspect.ismethod(fn):
        return True
    wenn inspect.isbuiltin(fn):
        self = getattr(fn, '__self__', None)
        return not (inspect.ismodule(self) or (self is None))
    return False


def allmethods(cl):
    methods = {}
    fuer key, value in inspect.getmembers(cl, inspect.isroutine):
        methods[key] = 1
    fuer base in cl.__bases__:
        methods.update(allmethods(base)) # all your base are belong to us
    fuer key in methods.keys():
        methods[key] = getattr(cl, key)
    return methods

def _split_list(s, predicate):
    """Split sequence s via predicate, and return pair ([true], [false]).

    The return value is a 2-tuple of lists,
        ([x fuer x in s wenn predicate(x)],
         [x fuer x in s wenn not predicate(x)])
    """

    yes = []
    no = []
    fuer x in s:
        wenn predicate(x):
            yes.append(x)
        sonst:
            no.append(x)
    return yes, no

_future_feature_names = set(__future__.all_feature_names)

def visiblename(name, all=None, obj=None):
    """Decide whether to show documentation on a variable."""
    # Certain special names are redundant or internal.
    # XXX Remove __initializing__?
    wenn name in {'__author__', '__builtins__', '__cached__', '__credits__',
                '__date__', '__doc__', '__file__', '__spec__',
                '__loader__', '__module__', '__name__', '__package__',
                '__path__', '__qualname__', '__slots__', '__version__',
                '__static_attributes__', '__firstlineno__',
                '__annotate_func__', '__annotations_cache__'}:
        return 0
    # Private names are hidden, but special names are displayed.
    wenn name.startswith('__') and name.endswith('__'): return 1
    # Namedtuples have public fields and methods with a single leading underscore
    wenn name.startswith('_') and hasattr(obj, '_fields'):
        return True
    # Ignore __future__ imports.
    wenn obj is not __future__ and name in _future_feature_names:
        wenn isinstance(getattr(obj, name, None), __future__._Feature):
            return False
    wenn all is not None:
        # only document that which the programmer exported in __all__
        return name in all
    sonst:
        return not name.startswith('_')

def classify_class_attrs(object):
    """Wrap inspect.classify_class_attrs, with fixup fuer data descriptors and bound methods."""
    results = []
    fuer (name, kind, cls, value) in inspect.classify_class_attrs(object):
        wenn inspect.isdatadescriptor(value):
            kind = 'data descriptor'
            wenn isinstance(value, property) and value.fset is None:
                kind = 'readonly property'
        sowenn kind == 'method' and _is_bound_method(value):
            kind = 'static method'
        results.append((name, kind, cls, value))
    return results

def sort_attributes(attrs, object):
    'Sort the attrs list in-place by _fields and then alphabetically by name'
    # This allows data descriptors to be ordered according
    # to a _fields attribute wenn present.
    fields = getattr(object, '_fields', [])
    try:
        field_order = {name : i-len(fields) fuer (i, name) in enumerate(fields)}
    except TypeError:
        field_order = {}
    keyfunc = lambda attr: (field_order.get(attr[0], 0), attr[0])
    attrs.sort(key=keyfunc)

# ----------------------------------------------------- module manipulation

def ispackage(path):
    """Guess whether a path refers to a package directory."""
    warnings.warn('The pydoc.ispackage() function is deprecated',
                  DeprecationWarning, stacklevel=2)
    wenn os.path.isdir(path):
        fuer ext in ('.py', '.pyc'):
            wenn os.path.isfile(os.path.join(path, '__init__' + ext)):
                return True
    return False

def source_synopsis(file):
    """Return the one-line summary of a file object, wenn present"""

    string = ''
    try:
        tokens = tokenize.generate_tokens(file.readline)
        fuer tok_type, tok_string, _, _, _ in tokens:
            wenn tok_type == tokenize.STRING:
                string += tok_string
            sowenn tok_type == tokenize.NEWLINE:
                with warnings.catch_warnings():
                    # Ignore the "invalid escape sequence" warning.
                    warnings.simplefilter("ignore", SyntaxWarning)
                    docstring = ast.literal_eval(string)
                wenn not isinstance(docstring, str):
                    return None
                return docstring.strip().split('\n')[0].strip()
            sowenn tok_type == tokenize.OP and tok_string in ('(', ')'):
                string += tok_string
            sowenn tok_type not in (tokenize.COMMENT, tokenize.NL, tokenize.ENCODING):
                return None
    except (tokenize.TokenError, UnicodeDecodeError, SyntaxError):
        return None
    return None

def synopsis(filename, cache={}):
    """Get the one-line summary out of a module file."""
    mtime = os.stat(filename).st_mtime
    lastupdate, result = cache.get(filename, (None, None))
    wenn lastupdate is None or lastupdate < mtime:
        # Look fuer binary suffixes first, falling back to source.
        wenn filename.endswith(tuple(importlib.machinery.BYTECODE_SUFFIXES)):
            loader_cls = importlib.machinery.SourcelessFileLoader
        sowenn filename.endswith(tuple(importlib.machinery.EXTENSION_SUFFIXES)):
            loader_cls = importlib.machinery.ExtensionFileLoader
        sonst:
            loader_cls = None
        # Now handle the choice.
        wenn loader_cls is None:
            # Must be a source file.
            try:
                file = tokenize.open(filename)
            except OSError:
                # module can't be opened, so skip it
                return None
            # text modules can be directly examined
            with file:
                result = source_synopsis(file)
        sonst:
            # Must be a binary module, which has to be imported.
            loader = loader_cls('__temp__', filename)
            # XXX We probably don't need to pass in the loader here.
            spec = importlib.util.spec_from_file_location('__temp__', filename,
                                                          loader=loader)
            try:
                module = importlib._bootstrap._load(spec)
            except:
                return None
            del sys.modules['__temp__']
            result = module.__doc__.splitlines()[0] wenn module.__doc__ sonst None
        # Cache the result.
        cache[filename] = (mtime, result)
    return result

klasse ErrorDuringImport(Exception):
    """Errors that occurred while trying to import something to document it."""
    def __init__(self, filename, exc_info):
        wenn not isinstance(exc_info, tuple):
            assert isinstance(exc_info, BaseException)
            self.exc = type(exc_info)
            self.value = exc_info
            self.tb = exc_info.__traceback__
        sonst:
            warnings.warn("A tuple value fuer exc_info is deprecated, use an exception instance",
                          DeprecationWarning)

            self.exc, self.value, self.tb = exc_info
        self.filename = filename

    def __str__(self):
        exc = self.exc.__name__
        return 'problem in %s - %s: %s' % (self.filename, exc, self.value)

def importfile(path):
    """Import a Python source file or compiled file given its path."""
    magic = importlib.util.MAGIC_NUMBER
    with open(path, 'rb') as file:
        is_bytecode = magic == file.read(len(magic))
    filename = os.path.basename(path)
    name, ext = os.path.splitext(filename)
    wenn is_bytecode:
        loader = importlib._bootstrap_external.SourcelessFileLoader(name, path)
    sonst:
        loader = importlib._bootstrap_external.SourceFileLoader(name, path)
    # XXX We probably don't need to pass in the loader here.
    spec = importlib.util.spec_from_file_location(name, path, loader=loader)
    try:
        return importlib._bootstrap._load(spec)
    except BaseException as err:
        raise ErrorDuringImport(path, err)

def safeimport(path, forceload=0, cache={}):
    """Import a module; handle errors; return None wenn the module isn't found.

    If the module *is* found but an exception occurs, it's wrapped in an
    ErrorDuringImport exception and reraised.  Unlike __import__, wenn a
    package path is specified, the module at the end of the path is returned,
    not the package at the beginning.  If the optional 'forceload' argument
    is 1, we reload the module from disk (unless it's a dynamic extension)."""
    try:
        # If forceload is 1 and the module has been previously loaded from
        # disk, we always have to reload the module.  Checking the file's
        # mtime isn't good enough (e.g. the module could contain a class
        # that inherits from another module that has changed).
        wenn forceload and path in sys.modules:
            wenn path not in sys.builtin_module_names:
                # Remove the module from sys.modules and re-import to try
                # and avoid problems with partially loaded modules.
                # Also remove any submodules because they won't appear
                # in the newly loaded module's namespace wenn they're already
                # in sys.modules.
                subs = [m fuer m in sys.modules wenn m.startswith(path + '.')]
                fuer key in [path] + subs:
                    # Prevent garbage collection.
                    cache[key] = sys.modules[key]
                    del sys.modules[key]
        module = importlib.import_module(path)
    except BaseException as err:
        # Did the error occur before or after the module was found?
        wenn path in sys.modules:
            # An error occurred while executing the imported module.
            raise ErrorDuringImport(sys.modules[path].__file__, err)
        sowenn type(err) is SyntaxError:
            # A SyntaxError occurred before we could execute the module.
            raise ErrorDuringImport(err.filename, err)
        sowenn isinstance(err, ImportError) and err.name == path:
            # No such module in the path.
            return None
        sonst:
            # Some other error occurred during the importing process.
            raise ErrorDuringImport(path, err)
    return module

# ---------------------------------------------------- formatter base class

klasse Doc:

    PYTHONDOCS = os.environ.get("PYTHONDOCS",
                                "https://docs.python.org/%d.%d/library"
                                % sys.version_info[:2])

    def document(self, object, name=None, *args):
        """Generate documentation fuer an object."""
        args = (object, name) + args
        # 'try' clause is to attempt to handle the possibility that inspect
        # identifies something in a way that pydoc itself has issues handling;
        # think 'super' and how it is a descriptor (which raises the exception
        # by lacking a __name__ attribute) and an instance.
        try:
            wenn inspect.ismodule(object): return self.docmodule(*args)
            wenn inspect.isclass(object): return self.docclass(*args)
            wenn inspect.isroutine(object): return self.docroutine(*args)
        except AttributeError:
            pass
        wenn inspect.isdatadescriptor(object): return self.docdata(*args)
        return self.docother(*args)

    def fail(self, object, name=None, *args):
        """Raise an exception fuer unimplemented types."""
        message = "don't know how to document object%s of type %s" % (
            name and ' ' + repr(name), type(object).__name__)
        raise TypeError(message)

    docmodule = docclass = docroutine = docother = docproperty = docdata = fail

    def getdocloc(self, object, basedir=sysconfig.get_path('stdlib')):
        """Return the location of module docs or None"""

        try:
            file = inspect.getabsfile(object)
        except TypeError:
            file = '(built-in)'

        docloc = os.environ.get("PYTHONDOCS", self.PYTHONDOCS)

        basedir = os.path.normcase(basedir)
        wenn (isinstance(object, type(os)) and
            (object.__name__ in ('errno', 'exceptions', 'gc',
                                 'marshal', 'posix', 'signal', 'sys',
                                 '_thread', 'zipimport') or
             (file.startswith(basedir) and
              not file.startswith(os.path.join(basedir, 'site-packages')))) and
            object.__name__ not in ('xml.etree', 'test.test_pydoc.pydoc_mod')):
            wenn docloc.startswith(("http://", "https://")):
                docloc = "{}/{}.html".format(docloc.rstrip("/"), object.__name__.lower())
            sonst:
                docloc = os.path.join(docloc, object.__name__.lower() + ".html")
        sonst:
            docloc = None
        return docloc

# -------------------------------------------- HTML documentation generator

klasse HTMLRepr(Repr):
    """Class fuer safely making an HTML representation of a Python object."""
    def __init__(self):
        Repr.__init__(self)
        self.maxlist = self.maxtuple = 20
        self.maxdict = 10
        self.maxstring = self.maxother = 100

    def escape(self, text):
        return replace(text, '&', '&amp;', '<', '&lt;', '>', '&gt;')

    def repr(self, object):
        return Repr.repr(self, object)

    def repr1(self, x, level):
        wenn hasattr(type(x), '__name__'):
            methodname = 'repr_' + '_'.join(type(x).__name__.split())
            wenn hasattr(self, methodname):
                return getattr(self, methodname)(x, level)
        return self.escape(cram(stripid(repr(x)), self.maxother))

    def repr_string(self, x, level):
        test = cram(x, self.maxstring)
        testrepr = repr(test)
        wenn '\\' in test and '\\' not in replace(testrepr, r'\\', ''):
            # Backslashes are only literal in the string and are never
            # needed to make any special characters, so show a raw string.
            return 'r' + testrepr[0] + self.escape(test) + testrepr[0]
        return re.sub(r'((\\[\\abfnrtv\'"]|\\[0-9]..|\\x..|\\u....)+)',
                      r'<span class="repr">\1</span>',
                      self.escape(testrepr))

    repr_str = repr_string

    def repr_instance(self, x, level):
        try:
            return self.escape(cram(stripid(repr(x)), self.maxstring))
        except:
            return self.escape('<%s instance>' % x.__class__.__name__)

    repr_unicode = repr_string

klasse HTMLDoc(Doc):
    """Formatter klasse fuer HTML documentation."""

    # ------------------------------------------- HTML formatting utilities

    _repr_instance = HTMLRepr()
    repr = _repr_instance.repr
    escape = _repr_instance.escape

    def page(self, title, contents):
        """Format an HTML page."""
        return '''\
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Python: %s</title>
</head><body>
%s
</body></html>''' % (title, contents)

    def heading(self, title, extras=''):
        """Format a page heading."""
        return '''
<table class="heading">
<tr class="heading-text decor">
<td class="title">&nbsp;<br>%s</td>
<td class="extra">%s</td></tr></table>
    ''' % (title, extras or '&nbsp;')

    def section(self, title, cls, contents, width=6,
                prelude='', marginalia=None, gap='&nbsp;'):
        """Format a section with a heading."""
        wenn marginalia is None:
            marginalia = '<span class="code">' + '&nbsp;' * width + '</span>'
        result = '''<p>
<table class="section">
<tr class="decor %s-decor heading-text">
<td class="section-title" colspan=3>&nbsp;<br>%s</td></tr>
    ''' % (cls, title)
        wenn prelude:
            result = result + '''
<tr><td class="decor %s-decor" rowspan=2>%s</td>
<td class="decor %s-decor" colspan=2>%s</td></tr>
<tr><td>%s</td>''' % (cls, marginalia, cls, prelude, gap)
        sonst:
            result = result + '''
<tr><td class="decor %s-decor">%s</td><td>%s</td>''' % (cls, marginalia, gap)

        return result + '\n<td class="singlecolumn">%s</td></tr></table>' % contents

    def bigsection(self, title, *args):
        """Format a section with a big heading."""
        title = '<strong class="bigsection">%s</strong>' % title
        return self.section(title, *args)

    def preformat(self, text):
        """Format literal preformatted text."""
        text = self.escape(text.expandtabs())
        return replace(text, '\n\n', '\n \n', '\n\n', '\n \n',
                             ' ', '&nbsp;', '\n', '<br>\n')

    def multicolumn(self, list, format):
        """Format a list of items into a multi-column list."""
        result = ''
        rows = (len(list) + 3) // 4
        fuer col in range(4):
            result = result + '<td class="multicolumn">'
            fuer i in range(rows*col, rows*col+rows):
                wenn i < len(list):
                    result = result + format(list[i]) + '<br>\n'
            result = result + '</td>'
        return '<table><tr>%s</tr></table>' % result

    def grey(self, text): return '<span class="grey">%s</span>' % text

    def namelink(self, name, *dicts):
        """Make a link fuer an identifier, given name-to-URL mappings."""
        fuer dict in dicts:
            wenn name in dict:
                return '<a href="%s">%s</a>' % (dict[name], name)
        return name

    def classlink(self, object, modname):
        """Make a link fuer a class."""
        name, module = object.__name__, sys.modules.get(object.__module__)
        wenn hasattr(module, name) and getattr(module, name) is object:
            return '<a href="%s.html#%s">%s</a>' % (
                module.__name__, name, classname(object, modname))
        return classname(object, modname)

    def parentlink(self, object, modname):
        """Make a link fuer the enclosing klasse or module."""
        link = None
        name, module = object.__name__, sys.modules.get(object.__module__)
        wenn hasattr(module, name) and getattr(module, name) is object:
            wenn '.' in object.__qualname__:
                name = object.__qualname__.rpartition('.')[0]
                wenn object.__module__ != modname:
                    link = '%s.html#%s' % (module.__name__, name)
                sonst:
                    link = '#%s' % name
            sonst:
                wenn object.__module__ != modname:
                    link = '%s.html' % module.__name__
        wenn link:
            return '<a href="%s">%s</a>' % (link, parentname(object, modname))
        sonst:
            return parentname(object, modname)

    def modulelink(self, object):
        """Make a link fuer a module."""
        return '<a href="%s.html">%s</a>' % (object.__name__, object.__name__)

    def modpkglink(self, modpkginfo):
        """Make a link fuer a module or package to display in an index."""
        name, path, ispackage, shadowed = modpkginfo
        wenn shadowed:
            return self.grey(name)
        wenn path:
            url = '%s.%s.html' % (path, name)
        sonst:
            url = '%s.html' % name
        wenn ispackage:
            text = '<strong>%s</strong>&nbsp;(package)' % name
        sonst:
            text = name
        return '<a href="%s">%s</a>' % (url, text)

    def filelink(self, url, path):
        """Make a link to source file."""
        return '<a href="file:%s">%s</a>' % (url, path)

    def markup(self, text, escape=None, funcs={}, classes={}, methods={}):
        """Mark up some plain text, given a context of symbols to look for.
        Each context dictionary maps object names to anchor names."""
        escape = escape or self.escape
        results = []
        here = 0
        pattern = re.compile(r'\b((http|https|ftp)://\S+[\w/]|'
                                r'RFC[- ]?(\d+)|'
                                r'PEP[- ]?(\d+)|'
                                r'(self\.)?(\w+))')
        while match := pattern.search(text, here):
            start, end = match.span()
            results.append(escape(text[here:start]))

            all, scheme, rfc, pep, selfdot, name = match.groups()
            wenn scheme:
                url = escape(all).replace('"', '&quot;')
                results.append('<a href="%s">%s</a>' % (url, url))
            sowenn rfc:
                url = 'https://www.rfc-editor.org/rfc/rfc%d.txt' % int(rfc)
                results.append('<a href="%s">%s</a>' % (url, escape(all)))
            sowenn pep:
                url = 'https://peps.python.org/pep-%04d/' % int(pep)
                results.append('<a href="%s">%s</a>' % (url, escape(all)))
            sowenn selfdot:
                # Create a link fuer methods like 'self.method(...)'
                # and use <strong> fuer attributes like 'self.attr'
                wenn text[end:end+1] == '(':
                    results.append('self.' + self.namelink(name, methods))
                sonst:
                    results.append('self.<strong>%s</strong>' % name)
            sowenn text[end:end+1] == '(':
                results.append(self.namelink(name, methods, funcs, classes))
            sonst:
                results.append(self.namelink(name, classes))
            here = end
        results.append(escape(text[here:]))
        return ''.join(results)

    # ---------------------------------------------- type-specific routines

    def formattree(self, tree, modname, parent=None):
        """Produce HTML fuer a klasse tree as given by inspect.getclasstree()."""
        result = ''
        fuer entry in tree:
            wenn isinstance(entry, tuple):
                c, bases = entry
                result = result + '<dt class="heading-text">'
                result = result + self.classlink(c, modname)
                wenn bases and bases != (parent,):
                    parents = []
                    fuer base in bases:
                        parents.append(self.classlink(base, modname))
                    result = result + '(' + ', '.join(parents) + ')'
                result = result + '\n</dt>'
            sowenn isinstance(entry, list):
                result = result + '<dd>\n%s</dd>\n' % self.formattree(
                    entry, modname, c)
        return '<dl>\n%s</dl>\n' % result

    def docmodule(self, object, name=None, mod=None, *ignored):
        """Produce HTML documentation fuer a module object."""
        name = object.__name__ # ignore the passed-in name
        try:
            all = object.__all__
        except AttributeError:
            all = None
        parts = name.split('.')
        links = []
        fuer i in range(len(parts)-1):
            links.append(
                '<a href="%s.html" class="white">%s</a>' %
                ('.'.join(parts[:i+1]), parts[i]))
        linkedname = '.'.join(links + parts[-1:])
        head = '<strong class="title">%s</strong>' % linkedname
        try:
            path = inspect.getabsfile(object)
            url = urllib.parse.quote(path)
            filelink = self.filelink(url, path)
        except TypeError:
            filelink = '(built-in)'
        info = []
        wenn hasattr(object, '__version__'):
            version = str(object.__version__)
            wenn version[:11] == '$' + 'Revision: ' and version[-1:] == '$':
                version = version[11:-1].strip()
            info.append('version %s' % self.escape(version))
        wenn hasattr(object, '__date__'):
            info.append(self.escape(str(object.__date__)))
        wenn info:
            head = head + ' (%s)' % ', '.join(info)
        docloc = self.getdocloc(object)
        wenn docloc is not None:
            docloc = '<br><a href="%(docloc)s">Module Reference</a>' % locals()
        sonst:
            docloc = ''
        result = self.heading(head, '<a href=".">index</a><br>' + filelink + docloc)

        modules = inspect.getmembers(object, inspect.ismodule)

        classes, cdict = [], {}
        fuer key, value in inspect.getmembers(object, inspect.isclass):
            # wenn __all__ exists, believe it.  Otherwise use old heuristic.
            wenn (all is not None or
                (inspect.getmodule(value) or object) is object):
                wenn visiblename(key, all, object):
                    classes.append((key, value))
                    cdict[key] = cdict[value] = '#' + key
        fuer key, value in classes:
            fuer base in value.__bases__:
                key, modname = base.__name__, base.__module__
                module = sys.modules.get(modname)
                wenn modname != name and module and hasattr(module, key):
                    wenn getattr(module, key) is base:
                        wenn not key in cdict:
                            cdict[key] = cdict[base] = modname + '.html#' + key
        funcs, fdict = [], {}
        fuer key, value in inspect.getmembers(object, inspect.isroutine):
            # wenn __all__ exists, believe it.  Otherwise use a heuristic.
            wenn (all is not None
                or (inspect.getmodule(value) or object) is object):
                wenn visiblename(key, all, object):
                    funcs.append((key, value))
                    fdict[key] = '#-' + key
                    wenn inspect.isfunction(value): fdict[value] = fdict[key]
        data = []
        fuer key, value in inspect.getmembers(object, isdata):
            wenn visiblename(key, all, object):
                data.append((key, value))

        doc = self.markup(getdoc(object), self.preformat, fdict, cdict)
        doc = doc and '<span class="code">%s</span>' % doc
        result = result + '<p>%s</p>\n' % doc

        wenn hasattr(object, '__path__'):
            modpkgs = []
            fuer importer, modname, ispkg in pkgutil.iter_modules(object.__path__):
                modpkgs.append((modname, name, ispkg, 0))
            modpkgs.sort()
            contents = self.multicolumn(modpkgs, self.modpkglink)
            result = result + self.bigsection(
                'Package Contents', 'pkg-content', contents)
        sowenn modules:
            contents = self.multicolumn(
                modules, lambda t: self.modulelink(t[1]))
            result = result + self.bigsection(
                'Modules', 'pkg-content', contents)

        wenn classes:
            classlist = [value fuer (key, value) in classes]
            contents = [
                self.formattree(inspect.getclasstree(classlist, 1), name)]
            fuer key, value in classes:
                contents.append(self.document(value, key, name, fdict, cdict))
            result = result + self.bigsection(
                'Classes', 'index', ' '.join(contents))
        wenn funcs:
            contents = []
            fuer key, value in funcs:
                contents.append(self.document(value, key, name, fdict, cdict))
            result = result + self.bigsection(
                'Functions', 'functions', ' '.join(contents))
        wenn data:
            contents = []
            fuer key, value in data:
                contents.append(self.document(value, key))
            result = result + self.bigsection(
                'Data', 'data', '<br>\n'.join(contents))
        wenn hasattr(object, '__author__'):
            contents = self.markup(str(object.__author__), self.preformat)
            result = result + self.bigsection('Author', 'author', contents)
        wenn hasattr(object, '__credits__'):
            contents = self.markup(str(object.__credits__), self.preformat)
            result = result + self.bigsection('Credits', 'credits', contents)

        return result

    def docclass(self, object, name=None, mod=None, funcs={}, classes={},
                 *ignored):
        """Produce HTML documentation fuer a klasse object."""
        realname = object.__name__
        name = name or realname
        bases = object.__bases__

        contents = []
        push = contents.append

        # Cute little klasse to pump out a horizontal rule between sections.
        klasse HorizontalRule:
            def __init__(self):
                self.needone = 0
            def maybe(self):
                wenn self.needone:
                    push('<hr>\n')
                self.needone = 1
        hr = HorizontalRule()

        # List the mro, wenn non-trivial.
        mro = deque(inspect.getmro(object))
        wenn len(mro) > 2:
            hr.maybe()
            push('<dl><dt>Method resolution order:</dt>\n')
            fuer base in mro:
                push('<dd>%s</dd>\n' % self.classlink(base,
                                                      object.__module__))
            push('</dl>\n')

        def spill(msg, attrs, predicate):
            ok, attrs = _split_list(attrs, predicate)
            wenn ok:
                hr.maybe()
                push(msg)
                fuer name, kind, homecls, value in ok:
                    try:
                        value = getattr(object, name)
                    except Exception:
                        # Some descriptors may meet a failure in their __get__.
                        # (bug #1785)
                        push(self.docdata(value, name, mod))
                    sonst:
                        push(self.document(value, name, mod,
                                        funcs, classes, mdict, object, homecls))
                    push('\n')
            return attrs

        def spilldescriptors(msg, attrs, predicate):
            ok, attrs = _split_list(attrs, predicate)
            wenn ok:
                hr.maybe()
                push(msg)
                fuer name, kind, homecls, value in ok:
                    push(self.docdata(value, name, mod))
            return attrs

        def spilldata(msg, attrs, predicate):
            ok, attrs = _split_list(attrs, predicate)
            wenn ok:
                hr.maybe()
                push(msg)
                fuer name, kind, homecls, value in ok:
                    base = self.docother(getattr(object, name), name, mod)
                    doc = getdoc(value)
                    wenn not doc:
                        push('<dl><dt>%s</dl>\n' % base)
                    sonst:
                        doc = self.markup(getdoc(value), self.preformat,
                                          funcs, classes, mdict)
                        doc = '<dd><span class="code">%s</span>' % doc
                        push('<dl><dt>%s%s</dl>\n' % (base, doc))
                    push('\n')
            return attrs

        attrs = [(name, kind, cls, value)
                 fuer name, kind, cls, value in classify_class_attrs(object)
                 wenn visiblename(name, obj=object)]

        mdict = {}
        fuer key, kind, homecls, value in attrs:
            mdict[key] = anchor = '#' + name + '-' + key
            try:
                value = getattr(object, name)
            except Exception:
                # Some descriptors may meet a failure in their __get__.
                # (bug #1785)
                pass
            try:
                # The value may not be hashable (e.g., a data attr with
                # a dict or list value).
                mdict[value] = anchor
            except TypeError:
                pass

        while attrs:
            wenn mro:
                thisclass = mro.popleft()
            sonst:
                thisclass = attrs[0][2]
            attrs, inherited = _split_list(attrs, lambda t: t[2] is thisclass)

            wenn object is not builtins.object and thisclass is builtins.object:
                attrs = inherited
                continue
            sowenn thisclass is object:
                tag = 'defined here'
            sonst:
                tag = 'inherited from %s' % self.classlink(thisclass,
                                                           object.__module__)
            tag += ':<br>\n'

            sort_attributes(attrs, object)

            # Pump out the attrs, segregated by kind.
            attrs = spill('Methods %s' % tag, attrs,
                          lambda t: t[1] == 'method')
            attrs = spill('Class methods %s' % tag, attrs,
                          lambda t: t[1] == 'class method')
            attrs = spill('Static methods %s' % tag, attrs,
                          lambda t: t[1] == 'static method')
            attrs = spilldescriptors("Readonly properties %s" % tag, attrs,
                                     lambda t: t[1] == 'readonly property')
            attrs = spilldescriptors('Data descriptors %s' % tag, attrs,
                                     lambda t: t[1] == 'data descriptor')
            attrs = spilldata('Data and other attributes %s' % tag, attrs,
                              lambda t: t[1] == 'data')
            assert attrs == []
            attrs = inherited

        contents = ''.join(contents)

        wenn name == realname:
            title = '<a name="%s">class <strong>%s</strong></a>' % (
                name, realname)
        sonst:
            title = '<strong>%s</strong> = <a name="%s">class %s</a>' % (
                name, name, realname)
        wenn bases:
            parents = []
            fuer base in bases:
                parents.append(self.classlink(base, object.__module__))
            title = title + '(%s)' % ', '.join(parents)

        decl = ''
        argspec = _getargspec(object)
        wenn argspec and argspec != '()':
            decl = name + self.escape(argspec) + '\n\n'

        doc = getdoc(object)
        wenn decl:
            doc = decl + (doc or '')
        doc = self.markup(doc, self.preformat, funcs, classes, mdict)
        doc = doc and '<span class="code">%s<br>&nbsp;</span>' % doc

        return self.section(title, 'title', contents, 3, doc)

    def formatvalue(self, object):
        """Format an argument default value as text."""
        return self.grey('=' + self.repr(object))

    def docroutine(self, object, name=None, mod=None,
                   funcs={}, classes={}, methods={}, cl=None, homecls=None):
        """Produce HTML documentation fuer a function or method object."""
        realname = object.__name__
        name = name or realname
        wenn homecls is None:
            homecls = cl
        anchor = ('' wenn cl is None sonst cl.__name__) + '-' + name
        note = ''
        skipdocs = False
        imfunc = None
        wenn _is_bound_method(object):
            imself = object.__self__
            wenn imself is cl:
                imfunc = getattr(object, '__func__', None)
            sowenn inspect.isclass(imself):
                note = ' klasse method of %s' % self.classlink(imself, mod)
            sonst:
                note = ' method of %s instance' % self.classlink(
                    imself.__class__, mod)
        sowenn (inspect.ismethoddescriptor(object) or
              inspect.ismethodwrapper(object)):
            try:
                objclass = object.__objclass__
            except AttributeError:
                pass
            sonst:
                wenn cl is None:
                    note = ' unbound %s method' % self.classlink(objclass, mod)
                sowenn objclass is not homecls:
                    note = ' from ' + self.classlink(objclass, mod)
        sonst:
            imfunc = object
        wenn inspect.isfunction(imfunc) and homecls is not None and (
            imfunc.__module__ != homecls.__module__ or
            imfunc.__qualname__ != homecls.__qualname__ + '.' + realname):
            pname = self.parentlink(imfunc, mod)
            wenn pname:
                note = ' from %s' % pname

        wenn (inspect.iscoroutinefunction(object) or
                inspect.isasyncgenfunction(object)):
            asyncqualifier = 'async '
        sonst:
            asyncqualifier = ''

        wenn name == realname:
            title = '<a name="%s"><strong>%s</strong></a>' % (anchor, realname)
        sonst:
            wenn (cl is not None and
                inspect.getattr_static(cl, realname, []) is object):
                reallink = '<a href="#%s">%s</a>' % (
                    cl.__name__ + '-' + realname, realname)
                skipdocs = True
                wenn note.startswith(' from '):
                    note = ''
            sonst:
                reallink = realname
            title = '<a name="%s"><strong>%s</strong></a> = %s' % (
                anchor, name, reallink)
        argspec = None
        wenn inspect.isroutine(object):
            argspec = _getargspec(object)
            wenn argspec and realname == '<lambda>':
                title = '<strong>%s</strong> <em>lambda</em> ' % name
                # XXX lambda's won't usually have func_annotations['return']
                # since the syntax doesn't support but it is possible.
                # So removing parentheses isn't truly safe.
                wenn not object.__annotations__:
                    argspec = argspec[1:-1] # remove parentheses
        wenn not argspec:
            argspec = '(...)'

        decl = asyncqualifier + title + self.escape(argspec) + (note and
               self.grey('<span class="heading-text">%s</span>' % note))

        wenn skipdocs:
            return '<dl><dt>%s</dt></dl>\n' % decl
        sonst:
            doc = self.markup(
                getdoc(object), self.preformat, funcs, classes, methods)
            doc = doc and '<dd><span class="code">%s</span></dd>' % doc
            return '<dl><dt>%s</dt>%s</dl>\n' % (decl, doc)

    def docdata(self, object, name=None, mod=None, cl=None, *ignored):
        """Produce html documentation fuer a data descriptor."""
        results = []
        push = results.append

        wenn name:
            push('<dl><dt><strong>%s</strong></dt>\n' % name)
        doc = self.markup(getdoc(object), self.preformat)
        wenn doc:
            push('<dd><span class="code">%s</span></dd>\n' % doc)
        push('</dl>\n')

        return ''.join(results)

    docproperty = docdata

    def docother(self, object, name=None, mod=None, *ignored):
        """Produce HTML documentation fuer a data object."""
        lhs = name and '<strong>%s</strong> = ' % name or ''
        return lhs + self.repr(object)

    def index(self, dir, shadowed=None):
        """Generate an HTML index fuer a directory of modules."""
        modpkgs = []
        wenn shadowed is None: shadowed = {}
        fuer importer, name, ispkg in pkgutil.iter_modules([dir]):
            wenn any((0xD800 <= ord(ch) <= 0xDFFF) fuer ch in name):
                # ignore a module wenn its name contains a surrogate character
                continue
            modpkgs.append((name, '', ispkg, name in shadowed))
            shadowed[name] = 1

        modpkgs.sort()
        contents = self.multicolumn(modpkgs, self.modpkglink)
        return self.bigsection(dir, 'index', contents)

# -------------------------------------------- text documentation generator

klasse TextRepr(Repr):
    """Class fuer safely making a text representation of a Python object."""
    def __init__(self):
        Repr.__init__(self)
        self.maxlist = self.maxtuple = 20
        self.maxdict = 10
        self.maxstring = self.maxother = 100

    def repr1(self, x, level):
        wenn hasattr(type(x), '__name__'):
            methodname = 'repr_' + '_'.join(type(x).__name__.split())
            wenn hasattr(self, methodname):
                return getattr(self, methodname)(x, level)
        return cram(stripid(repr(x)), self.maxother)

    def repr_string(self, x, level):
        test = cram(x, self.maxstring)
        testrepr = repr(test)
        wenn '\\' in test and '\\' not in replace(testrepr, r'\\', ''):
            # Backslashes are only literal in the string and are never
            # needed to make any special characters, so show a raw string.
            return 'r' + testrepr[0] + test + testrepr[0]
        return testrepr

    repr_str = repr_string

    def repr_instance(self, x, level):
        try:
            return cram(stripid(repr(x)), self.maxstring)
        except:
            return '<%s instance>' % x.__class__.__name__

klasse TextDoc(Doc):
    """Formatter klasse fuer text documentation."""

    # ------------------------------------------- text formatting utilities

    _repr_instance = TextRepr()
    repr = _repr_instance.repr

    def bold(self, text):
        """Format a string in bold by overstriking."""
        return ''.join(ch + '\b' + ch fuer ch in text)

    def indent(self, text, prefix='    '):
        """Indent text by prepending a given prefix to each line."""
        wenn not text: return ''
        lines = [(prefix + line).rstrip() fuer line in text.split('\n')]
        return '\n'.join(lines)

    def section(self, title, contents):
        """Format a section with a given heading."""
        clean_contents = self.indent(contents).rstrip()
        return self.bold(title) + '\n' + clean_contents + '\n\n'

    # ---------------------------------------------- type-specific routines

    def formattree(self, tree, modname, parent=None, prefix=''):
        """Render in text a klasse tree as returned by inspect.getclasstree()."""
        result = ''
        fuer entry in tree:
            wenn isinstance(entry, tuple):
                c, bases = entry
                result = result + prefix + classname(c, modname)
                wenn bases and bases != (parent,):
                    parents = (classname(c, modname) fuer c in bases)
                    result = result + '(%s)' % ', '.join(parents)
                result = result + '\n'
            sowenn isinstance(entry, list):
                result = result + self.formattree(
                    entry, modname, c, prefix + '    ')
        return result

    def docmodule(self, object, name=None, mod=None, *ignored):
        """Produce text documentation fuer a given module object."""
        name = object.__name__ # ignore the passed-in name
        synop, desc = splitdoc(getdoc(object))
        result = self.section('NAME', name + (synop and ' - ' + synop))
        all = getattr(object, '__all__', None)
        docloc = self.getdocloc(object)
        wenn docloc is not None:
            result = result + self.section('MODULE REFERENCE', docloc + """

The following documentation is automatically generated from the Python
source files.  It may be incomplete, incorrect or include features that
are considered implementation detail and may vary between Python
implementations.  When in doubt, consult the module reference at the
location listed above.
""")

        wenn desc:
            result = result + self.section('DESCRIPTION', desc)

        classes = []
        fuer key, value in inspect.getmembers(object, inspect.isclass):
            # wenn __all__ exists, believe it.  Otherwise use old heuristic.
            wenn (all is not None
                or (inspect.getmodule(value) or object) is object):
                wenn visiblename(key, all, object):
                    classes.append((key, value))
        funcs = []
        fuer key, value in inspect.getmembers(object, inspect.isroutine):
            # wenn __all__ exists, believe it.  Otherwise use a heuristic.
            wenn (all is not None
                or (inspect.getmodule(value) or object) is object):
                wenn visiblename(key, all, object):
                    funcs.append((key, value))
        data = []
        fuer key, value in inspect.getmembers(object, isdata):
            wenn visiblename(key, all, object):
                data.append((key, value))

        modpkgs = []
        modpkgs_names = set()
        wenn hasattr(object, '__path__'):
            fuer importer, modname, ispkg in pkgutil.iter_modules(object.__path__):
                modpkgs_names.add(modname)
                wenn ispkg:
                    modpkgs.append(modname + ' (package)')
                sonst:
                    modpkgs.append(modname)

            modpkgs.sort()
            result = result + self.section(
                'PACKAGE CONTENTS', '\n'.join(modpkgs))

        # Detect submodules as sometimes created by C extensions
        submodules = []
        fuer key, value in inspect.getmembers(object, inspect.ismodule):
            wenn value.__name__.startswith(name + '.') and key not in modpkgs_names:
                submodules.append(key)
        wenn submodules:
            submodules.sort()
            result = result + self.section(
                'SUBMODULES', '\n'.join(submodules))

        wenn classes:
            classlist = [value fuer key, value in classes]
            contents = [self.formattree(
                inspect.getclasstree(classlist, 1), name)]
            fuer key, value in classes:
                contents.append(self.document(value, key, name))
            result = result + self.section('CLASSES', '\n'.join(contents))

        wenn funcs:
            contents = []
            fuer key, value in funcs:
                contents.append(self.document(value, key, name))
            result = result + self.section('FUNCTIONS', '\n'.join(contents))

        wenn data:
            contents = []
            fuer key, value in data:
                contents.append(self.docother(value, key, name, maxlen=70))
            result = result + self.section('DATA', '\n'.join(contents))

        wenn hasattr(object, '__version__'):
            version = str(object.__version__)
            wenn version[:11] == '$' + 'Revision: ' and version[-1:] == '$':
                version = version[11:-1].strip()
            result = result + self.section('VERSION', version)
        wenn hasattr(object, '__date__'):
            result = result + self.section('DATE', str(object.__date__))
        wenn hasattr(object, '__author__'):
            result = result + self.section('AUTHOR', str(object.__author__))
        wenn hasattr(object, '__credits__'):
            result = result + self.section('CREDITS', str(object.__credits__))
        try:
            file = inspect.getabsfile(object)
        except TypeError:
            file = '(built-in)'
        result = result + self.section('FILE', file)
        return result

    def docclass(self, object, name=None, mod=None, *ignored):
        """Produce text documentation fuer a given klasse object."""
        realname = object.__name__
        name = name or realname
        bases = object.__bases__

        def makename(c, m=object.__module__):
            return classname(c, m)

        wenn name == realname:
            title = 'class ' + self.bold(realname)
        sonst:
            title = self.bold(name) + ' = klasse ' + realname
        wenn bases:
            parents = map(makename, bases)
            title = title + '(%s)' % ', '.join(parents)

        contents = []
        push = contents.append

        argspec = _getargspec(object)
        wenn argspec and argspec != '()':
            push(name + argspec + '\n')

        doc = getdoc(object)
        wenn doc:
            push(doc + '\n')

        # List the mro, wenn non-trivial.
        mro = deque(inspect.getmro(object))
        wenn len(mro) > 2:
            push("Method resolution order:")
            fuer base in mro:
                push('    ' + makename(base))
            push('')

        # List the built-in subclasses, wenn any:
        subclasses = sorted(
            (str(cls.__name__) fuer cls in type.__subclasses__(object)
             wenn (not cls.__name__.startswith("_") and
                 getattr(cls, '__module__', '') == "builtins")),
            key=str.lower
        )
        no_of_subclasses = len(subclasses)
        MAX_SUBCLASSES_TO_DISPLAY = 4
        wenn subclasses:
            push("Built-in subclasses:")
            fuer subclassname in subclasses[:MAX_SUBCLASSES_TO_DISPLAY]:
                push('    ' + subclassname)
            wenn no_of_subclasses > MAX_SUBCLASSES_TO_DISPLAY:
                push('    ... and ' +
                     str(no_of_subclasses - MAX_SUBCLASSES_TO_DISPLAY) +
                     ' other subclasses')
            push('')

        # Cute little klasse to pump out a horizontal rule between sections.
        klasse HorizontalRule:
            def __init__(self):
                self.needone = 0
            def maybe(self):
                wenn self.needone:
                    push('-' * 70)
                self.needone = 1
        hr = HorizontalRule()

        def spill(msg, attrs, predicate):
            ok, attrs = _split_list(attrs, predicate)
            wenn ok:
                hr.maybe()
                push(msg)
                fuer name, kind, homecls, value in ok:
                    try:
                        value = getattr(object, name)
                    except Exception:
                        # Some descriptors may meet a failure in their __get__.
                        # (bug #1785)
                        push(self.docdata(value, name, mod))
                    sonst:
                        push(self.document(value,
                                        name, mod, object, homecls))
            return attrs

        def spilldescriptors(msg, attrs, predicate):
            ok, attrs = _split_list(attrs, predicate)
            wenn ok:
                hr.maybe()
                push(msg)
                fuer name, kind, homecls, value in ok:
                    push(self.docdata(value, name, mod))
            return attrs

        def spilldata(msg, attrs, predicate):
            ok, attrs = _split_list(attrs, predicate)
            wenn ok:
                hr.maybe()
                push(msg)
                fuer name, kind, homecls, value in ok:
                    doc = getdoc(value)
                    try:
                        obj = getattr(object, name)
                    except AttributeError:
                        obj = homecls.__dict__[name]
                    push(self.docother(obj, name, mod, maxlen=70, doc=doc) +
                         '\n')
            return attrs

        attrs = [(name, kind, cls, value)
                 fuer name, kind, cls, value in classify_class_attrs(object)
                 wenn visiblename(name, obj=object)]

        while attrs:
            wenn mro:
                thisclass = mro.popleft()
            sonst:
                thisclass = attrs[0][2]
            attrs, inherited = _split_list(attrs, lambda t: t[2] is thisclass)

            wenn object is not builtins.object and thisclass is builtins.object:
                attrs = inherited
                continue
            sowenn thisclass is object:
                tag = "defined here"
            sonst:
                tag = "inherited from %s" % classname(thisclass,
                                                      object.__module__)

            sort_attributes(attrs, object)

            # Pump out the attrs, segregated by kind.
            attrs = spill("Methods %s:\n" % tag, attrs,
                          lambda t: t[1] == 'method')
            attrs = spill("Class methods %s:\n" % tag, attrs,
                          lambda t: t[1] == 'class method')
            attrs = spill("Static methods %s:\n" % tag, attrs,
                          lambda t: t[1] == 'static method')
            attrs = spilldescriptors("Readonly properties %s:\n" % tag, attrs,
                                     lambda t: t[1] == 'readonly property')
            attrs = spilldescriptors("Data descriptors %s:\n" % tag, attrs,
                                     lambda t: t[1] == 'data descriptor')
            attrs = spilldata("Data and other attributes %s:\n" % tag, attrs,
                              lambda t: t[1] == 'data')

            assert attrs == []
            attrs = inherited

        contents = '\n'.join(contents)
        wenn not contents:
            return title + '\n'
        return title + '\n' + self.indent(contents.rstrip(), ' |  ') + '\n'

    def formatvalue(self, object):
        """Format an argument default value as text."""
        return '=' + self.repr(object)

    def docroutine(self, object, name=None, mod=None, cl=None, homecls=None):
        """Produce text documentation fuer a function or method object."""
        realname = object.__name__
        name = name or realname
        wenn homecls is None:
            homecls = cl
        note = ''
        skipdocs = False
        imfunc = None
        wenn _is_bound_method(object):
            imself = object.__self__
            wenn imself is cl:
                imfunc = getattr(object, '__func__', None)
            sowenn inspect.isclass(imself):
                note = ' klasse method of %s' % classname(imself, mod)
            sonst:
                note = ' method of %s instance' % classname(
                    imself.__class__, mod)
        sowenn (inspect.ismethoddescriptor(object) or
              inspect.ismethodwrapper(object)):
            try:
                objclass = object.__objclass__
            except AttributeError:
                pass
            sonst:
                wenn cl is None:
                    note = ' unbound %s method' % classname(objclass, mod)
                sowenn objclass is not homecls:
                    note = ' from ' + classname(objclass, mod)
        sonst:
            imfunc = object
        wenn inspect.isfunction(imfunc) and homecls is not None and (
            imfunc.__module__ != homecls.__module__ or
            imfunc.__qualname__ != homecls.__qualname__ + '.' + realname):
            pname = parentname(imfunc, mod)
            wenn pname:
                note = ' from %s' % pname

        wenn (inspect.iscoroutinefunction(object) or
                inspect.isasyncgenfunction(object)):
            asyncqualifier = 'async '
        sonst:
            asyncqualifier = ''

        wenn name == realname:
            title = self.bold(realname)
        sonst:
            wenn (cl is not None and
                inspect.getattr_static(cl, realname, []) is object):
                skipdocs = True
                wenn note.startswith(' from '):
                    note = ''
            title = self.bold(name) + ' = ' + realname
        argspec = None

        wenn inspect.isroutine(object):
            argspec = _getargspec(object)
            wenn argspec and realname == '<lambda>':
                title = self.bold(name) + ' lambda '
                # XXX lambda's won't usually have func_annotations['return']
                # since the syntax doesn't support but it is possible.
                # So removing parentheses isn't truly safe.
                wenn not object.__annotations__:
                    argspec = argspec[1:-1]
        wenn not argspec:
            argspec = '(...)'
        decl = asyncqualifier + title + argspec + note

        wenn skipdocs:
            return decl + '\n'
        sonst:
            doc = getdoc(object) or ''
            return decl + '\n' + (doc and self.indent(doc).rstrip() + '\n')

    def docdata(self, object, name=None, mod=None, cl=None, *ignored):
        """Produce text documentation fuer a data descriptor."""
        results = []
        push = results.append

        wenn name:
            push(self.bold(name))
            push('\n')
        doc = getdoc(object) or ''
        wenn doc:
            push(self.indent(doc))
            push('\n')
        return ''.join(results)

    docproperty = docdata

    def docother(self, object, name=None, mod=None, parent=None, *ignored,
                 maxlen=None, doc=None):
        """Produce text documentation fuer a data object."""
        repr = self.repr(object)
        wenn maxlen:
            line = (name and name + ' = ' or '') + repr
            chop = maxlen - len(line)
            wenn chop < 0: repr = repr[:chop] + '...'
        line = (name and self.bold(name) + ' = ' or '') + repr
        wenn not doc:
            doc = getdoc(object)
        wenn doc:
            line += '\n' + self.indent(str(doc)) + '\n'
        return line

klasse _PlainTextDoc(TextDoc):
    """Subclass of TextDoc which overrides string styling"""
    def bold(self, text):
        return text

# --------------------------------------------------------- user interfaces

def pager(text, title=''):
    """The first time this is called, determine what kind of pager to use."""
    global pager
    pager = get_pager()
    pager(text, title)

def describe(thing):
    """Produce a short description of the given thing."""
    wenn inspect.ismodule(thing):
        wenn thing.__name__ in sys.builtin_module_names:
            return 'built-in module ' + thing.__name__
        wenn hasattr(thing, '__path__'):
            return 'package ' + thing.__name__
        sonst:
            return 'module ' + thing.__name__
    wenn inspect.isbuiltin(thing):
        return 'built-in function ' + thing.__name__
    wenn inspect.isgetsetdescriptor(thing):
        return 'getset descriptor %s.%s.%s' % (
            thing.__objclass__.__module__, thing.__objclass__.__name__,
            thing.__name__)
    wenn inspect.ismemberdescriptor(thing):
        return 'member descriptor %s.%s.%s' % (
            thing.__objclass__.__module__, thing.__objclass__.__name__,
            thing.__name__)
    wenn inspect.isclass(thing):
        return 'class ' + thing.__name__
    wenn inspect.isfunction(thing):
        return 'function ' + thing.__name__
    wenn inspect.ismethod(thing):
        return 'method ' + thing.__name__
    wenn inspect.ismethodwrapper(thing):
        return 'method wrapper ' + thing.__name__
    wenn inspect.ismethoddescriptor(thing):
        try:
            return 'method descriptor ' + thing.__name__
        except AttributeError:
            pass
    return type(thing).__name__

def locate(path, forceload=0):
    """Locate an object by name or dotted path, importing as necessary."""
    parts = [part fuer part in path.split('.') wenn part]
    module, n = None, 0
    while n < len(parts):
        nextmodule = safeimport('.'.join(parts[:n+1]), forceload)
        wenn nextmodule: module, n = nextmodule, n + 1
        sonst: break
    wenn module:
        object = module
    sonst:
        object = builtins
    fuer part in parts[n:]:
        try:
            object = getattr(object, part)
        except AttributeError:
            return None
    return object

# --------------------------------------- interactive interpreter interface

text = TextDoc()
plaintext = _PlainTextDoc()
html = HTMLDoc()

def resolve(thing, forceload=0):
    """Given an object or a path to an object, get the object and its name."""
    wenn isinstance(thing, str):
        object = locate(thing, forceload)
        wenn object is None:
            raise ImportError('''\
No Python documentation found fuer %r.
Use help() to get the interactive help utility.
Use help(str) fuer help on the str class.''' % thing)
        return object, thing
    sonst:
        name = getattr(thing, '__name__', None)
        return thing, name wenn isinstance(name, str) sonst None

def render_doc(thing, title='Python Library Documentation: %s', forceload=0,
        renderer=None):
    """Render text documentation, given an object or a path to an object."""
    wenn renderer is None:
        renderer = text
    object, name = resolve(thing, forceload)
    desc = describe(object)
    module = inspect.getmodule(object)
    wenn name and '.' in name:
        desc += ' in ' + name[:name.rfind('.')]
    sowenn module and module is not object:
        desc += ' in module ' + module.__name__

    wenn not (inspect.ismodule(object) or
              inspect.isclass(object) or
              inspect.isroutine(object) or
              inspect.isdatadescriptor(object) or
              _getdoc(object)):
        # If the passed object is a piece of data or an instance,
        # document its available methods instead of its value.
        wenn hasattr(object, '__origin__'):
            object = object.__origin__
        sonst:
            object = type(object)
            desc += ' object'
    return title % desc + '\n\n' + renderer.document(object, name)

def doc(thing, title='Python Library Documentation: %s', forceload=0,
        output=None, is_cli=False):
    """Display text documentation, given an object or a path to an object."""
    wenn output is None:
        try:
            wenn isinstance(thing, str):
                what = thing
            sonst:
                what = getattr(thing, '__qualname__', None)
                wenn not isinstance(what, str):
                    what = getattr(thing, '__name__', None)
                    wenn not isinstance(what, str):
                        what = type(thing).__name__ + ' object'
            pager(render_doc(thing, title, forceload), f'Help on {what!s}')
        except ImportError as exc:
            wenn is_cli:
                raise
            print(exc)
    sonst:
        try:
            s = render_doc(thing, title, forceload, plaintext)
        except ImportError as exc:
            s = str(exc)
        output.write(s)

def writedoc(thing, forceload=0):
    """Write HTML documentation to a file in the current directory."""
    object, name = resolve(thing, forceload)
    page = html.page(describe(object), html.document(object, name))
    with open(name + '.html', 'w', encoding='utf-8') as file:
        file.write(page)
    print('wrote', name + '.html')

def writedocs(dir, pkgpath='', done=None):
    """Write out HTML documentation fuer all modules in a directory tree."""
    wenn done is None: done = {}
    fuer importer, modname, ispkg in pkgutil.walk_packages([dir], pkgpath):
        writedoc(modname)
    return


def _introdoc():
    ver = '%d.%d' % sys.version_info[:2]
    wenn os.environ.get('PYTHON_BASIC_REPL'):
        pyrepl_keys = ''
    sonst:
        # Additional help fuer keyboard shortcuts wenn enhanced REPL is used.
        pyrepl_keys = '''
        You can use the following keyboard shortcuts at the main interpreter prompt.
        F1: enter interactive help, F2: enter history browsing mode, F3: enter paste
        mode (press again to exit).
        '''
    return textwrap.dedent(f'''\
        Welcome to Python {ver}'s help utility! If this is your first time using
        Python, you should definitely check out the tutorial at
        https://docs.python.org/{ver}/tutorial/.

        Enter the name of any module, keyword, or topic to get help on writing
        Python programs and using Python modules.  To get a list of available
        modules, keywords, symbols, or topics, enter "modules", "keywords",
        "symbols", or "topics".
        {pyrepl_keys}
        Each module also comes with a one-line summary of what it does; to list
        the modules whose name or summary contain a given string such as "spam",
        enter "modules spam".

        To quit this help utility and return to the interpreter,
        enter "q", "quit" or "exit".
    ''')

klasse Helper:

    # These dictionaries map a topic name to either an alias, or a tuple
    # (label, seealso-items).  The "label" is the label of the corresponding
    # section in the .rst file under Doc/ and an index into the dictionary
    # in pydoc_data/topics.py.
    #
    # CAUTION: wenn you change one of these dictionaries, be sure to adapt the
    #          list of needed labels in Doc/tools/extensions/pyspecific.py and
    #          regenerate the pydoc_data/topics.py file by running
    #              make pydoc-topics
    #          in Doc/ and copying the output file into the Lib/ directory.

    keywords = {
        'False': '',
        'None': '',
        'True': '',
        'and': 'BOOLEAN',
        'as': 'with',
        'assert': ('assert', ''),
        'async': ('async', ''),
        'await': ('await', ''),
        'break': ('break', 'while for'),
        'class': ('class', 'CLASSES SPECIALMETHODS'),
        'continue': ('continue', 'while for'),
        'def': ('function', ''),
        'del': ('del', 'BASICMETHODS'),
        'elif': 'if',
        'else': ('else', 'while for'),
        'except': 'try',
        'finally': 'try',
        'for': ('for', 'break continue while'),
        'from': 'import',
        'global': ('global', 'nonlocal NAMESPACES'),
        'if': ('if', 'TRUTHVALUE'),
        'import': ('import', 'MODULES'),
        'in': ('in', 'SEQUENCEMETHODS'),
        'is': 'COMPARISON',
        'lambda': ('lambda', 'FUNCTIONS'),
        'nonlocal': ('nonlocal', 'global NAMESPACES'),
        'not': 'BOOLEAN',
        'or': 'BOOLEAN',
        'pass': ('pass', ''),
        'raise': ('raise', 'EXCEPTIONS'),
        'return': ('return', 'FUNCTIONS'),
        'try': ('try', 'EXCEPTIONS'),
        'while': ('while', 'break continue wenn TRUTHVALUE'),
        'with': ('with', 'CONTEXTMANAGERS EXCEPTIONS yield'),
        'yield': ('yield', ''),
    }
    # Either add symbols to this dictionary or to the symbols dictionary
    # directly: Whichever is easier. They are merged later.
    _strprefixes = [p + q fuer p in ('b', 'f', 'r', 'u') fuer q in ("'", '"')]
    _symbols_inverse = {
        'STRINGS' : ("'", "'''", '"', '"""', *_strprefixes),
        'OPERATORS' : ('+', '-', '*', '**', '/', '//', '%', '<<', '>>', '&',
                       '|', '^', '~', '<', '>', '<=', '>=', '==', '!=', '<>'),
        'COMPARISON' : ('<', '>', '<=', '>=', '==', '!=', '<>'),
        'UNARY' : ('-', '~'),
        'AUGMENTEDASSIGNMENT' : ('+=', '-=', '*=', '/=', '%=', '&=', '|=',
                                '^=', '<<=', '>>=', '**=', '//='),
        'BITWISE' : ('<<', '>>', '&', '|', '^', '~'),
        'COMPLEX' : ('j', 'J')
    }
    symbols = {
        '%': 'OPERATORS FORMATTING',
        '**': 'POWER',
        ',': 'TUPLES LISTS FUNCTIONS',
        '.': 'ATTRIBUTES FLOAT MODULES OBJECTS',
        '...': 'ELLIPSIS',
        ':': 'SLICINGS DICTIONARYLITERALS',
        '@': 'def class',
        '\\': 'STRINGS',
        ':=': 'ASSIGNMENTEXPRESSIONS',
        '_': 'PRIVATENAMES',
        '__': 'PRIVATENAMES SPECIALMETHODS',
        '`': 'BACKQUOTES',
        '(': 'TUPLES FUNCTIONS CALLS',
        ')': 'TUPLES FUNCTIONS CALLS',
        '[': 'LISTS SUBSCRIPTS SLICINGS',
        ']': 'LISTS SUBSCRIPTS SLICINGS'
    }
    fuer topic, symbols_ in _symbols_inverse.items():
        fuer symbol in symbols_:
            topics = symbols.get(symbol, topic)
            wenn topic not in topics:
                topics = topics + ' ' + topic
            symbols[symbol] = topics
    del topic, symbols_, symbol, topics

    topics = {
        'TYPES': ('types', 'STRINGS UNICODE NUMBERS SEQUENCES MAPPINGS '
                  'FUNCTIONS CLASSES MODULES FILES inspect'),
        'STRINGS': ('strings', 'str UNICODE SEQUENCES STRINGMETHODS '
                    'FORMATTING TYPES'),
        'STRINGMETHODS': ('string-methods', 'STRINGS FORMATTING'),
        'FORMATTING': ('formatstrings', 'OPERATORS'),
        'UNICODE': ('strings', 'encodings unicode SEQUENCES STRINGMETHODS '
                    'FORMATTING TYPES'),
        'NUMBERS': ('numbers', 'INTEGER FLOAT COMPLEX TYPES'),
        'INTEGER': ('integers', 'int range'),
        'FLOAT': ('floating', 'float math'),
        'COMPLEX': ('imaginary', 'complex cmath'),
        'SEQUENCES': ('typesseq', 'STRINGMETHODS FORMATTING range LISTS'),
        'MAPPINGS': 'DICTIONARIES',
        'FUNCTIONS': ('typesfunctions', 'def TYPES'),
        'METHODS': ('typesmethods', 'class def CLASSES TYPES'),
        'CODEOBJECTS': ('bltin-code-objects', 'compile FUNCTIONS TYPES'),
        'TYPEOBJECTS': ('bltin-type-objects', 'types TYPES'),
        'FRAMEOBJECTS': 'TYPES',
        'TRACEBACKS': 'TYPES',
        'NONE': ('bltin-null-object', ''),
        'ELLIPSIS': ('bltin-ellipsis-object', 'SLICINGS'),
        'SPECIALATTRIBUTES': ('specialattrs', ''),
        'CLASSES': ('types', 'class SPECIALMETHODS PRIVATENAMES'),
        'MODULES': ('typesmodules', 'import'),
        'PACKAGES': 'import',
        'EXPRESSIONS': ('operator-summary', 'lambda or and not in is BOOLEAN '
                        'COMPARISON BITWISE SHIFTING BINARY FORMATTING POWER '
                        'UNARY ATTRIBUTES SUBSCRIPTS SLICINGS CALLS TUPLES '
                        'LISTS DICTIONARIES'),
        'OPERATORS': 'EXPRESSIONS',
        'PRECEDENCE': 'EXPRESSIONS',
        'OBJECTS': ('objects', 'TYPES'),
        'SPECIALMETHODS': ('specialnames', 'BASICMETHODS ATTRIBUTEMETHODS '
                           'CALLABLEMETHODS SEQUENCEMETHODS MAPPINGMETHODS '
                           'NUMBERMETHODS CLASSES'),
        'BASICMETHODS': ('customization', 'hash repr str SPECIALMETHODS'),
        'ATTRIBUTEMETHODS': ('attribute-access', 'ATTRIBUTES SPECIALMETHODS'),
        'CALLABLEMETHODS': ('callable-types', 'CALLS SPECIALMETHODS'),
        'SEQUENCEMETHODS': ('sequence-types', 'SEQUENCES SEQUENCEMETHODS '
                             'SPECIALMETHODS'),
        'MAPPINGMETHODS': ('sequence-types', 'MAPPINGS SPECIALMETHODS'),
        'NUMBERMETHODS': ('numeric-types', 'NUMBERS AUGMENTEDASSIGNMENT '
                          'SPECIALMETHODS'),
        'EXECUTION': ('execmodel', 'NAMESPACES DYNAMICFEATURES EXCEPTIONS'),
        'NAMESPACES': ('naming', 'global nonlocal ASSIGNMENT DELETION DYNAMICFEATURES'),
        'DYNAMICFEATURES': ('dynamic-features', ''),
        'SCOPING': 'NAMESPACES',
        'FRAMES': 'NAMESPACES',
        'EXCEPTIONS': ('exceptions', 'try except finally raise'),
        'CONVERSIONS': ('conversions', ''),
        'IDENTIFIERS': ('identifiers', 'keywords SPECIALIDENTIFIERS'),
        'SPECIALIDENTIFIERS': ('id-classes', ''),
        'PRIVATENAMES': ('atom-identifiers', ''),
        'LITERALS': ('atom-literals', 'STRINGS NUMBERS TUPLELITERALS '
                     'LISTLITERALS DICTIONARYLITERALS'),
        'TUPLES': 'SEQUENCES',
        'TUPLELITERALS': ('exprlists', 'TUPLES LITERALS'),
        'LISTS': ('typesseq-mutable', 'LISTLITERALS'),
        'LISTLITERALS': ('lists', 'LISTS LITERALS'),
        'DICTIONARIES': ('typesmapping', 'DICTIONARYLITERALS'),
        'DICTIONARYLITERALS': ('dict', 'DICTIONARIES LITERALS'),
        'ATTRIBUTES': ('attribute-references', 'getattr hasattr setattr ATTRIBUTEMETHODS'),
        'SUBSCRIPTS': ('subscriptions', 'SEQUENCEMETHODS'),
        'SLICINGS': ('slicings', 'SEQUENCEMETHODS'),
        'CALLS': ('calls', 'EXPRESSIONS'),
        'POWER': ('power', 'EXPRESSIONS'),
        'UNARY': ('unary', 'EXPRESSIONS'),
        'BINARY': ('binary', 'EXPRESSIONS'),
        'SHIFTING': ('shifting', 'EXPRESSIONS'),
        'BITWISE': ('bitwise', 'EXPRESSIONS'),
        'COMPARISON': ('comparisons', 'EXPRESSIONS BASICMETHODS'),
        'BOOLEAN': ('booleans', 'EXPRESSIONS TRUTHVALUE'),
        'ASSERTION': 'assert',
        'ASSIGNMENT': ('assignment', 'AUGMENTEDASSIGNMENT'),
        'AUGMENTEDASSIGNMENT': ('augassign', 'NUMBERMETHODS'),
        'ASSIGNMENTEXPRESSIONS': ('assignment-expressions', ''),
        'DELETION': 'del',
        'RETURNING': 'return',
        'IMPORTING': 'import',
        'CONDITIONAL': 'if',
        'LOOPING': ('compound', 'for while break continue'),
        'TRUTHVALUE': ('truth', 'if while and or not BASICMETHODS'),
        'DEBUGGING': ('debugger', 'pdb'),
        'CONTEXTMANAGERS': ('context-managers', 'with'),
    }

    def __init__(self, input=None, output=None):
        self._input = input
        self._output = output

    @property
    def input(self):
        return self._input or sys.stdin

    @property
    def output(self):
        return self._output or sys.stdout

    def __repr__(self):
        wenn inspect.stack()[1][3] == '?':
            self()
            return ''
        return '<%s.%s instance>' % (self.__class__.__module__,
                                     self.__class__.__qualname__)

    _GoInteractive = object()
    def __call__(self, request=_GoInteractive):
        wenn request is not self._GoInteractive:
            try:
                self.help(request)
            except ImportError as err:
                self.output.write(f'{err}\n')
        sonst:
            self.intro()
            self.interact()
            self.output.write('''
You are now leaving help and returning to the Python interpreter.
If you want to ask fuer help on a particular object directly from the
interpreter, you can type "help(object)".  Executing "help('string')"
has the same effect as typing a particular string at the help> prompt.
''')

    def interact(self):
        self.output.write('\n')
        while True:
            try:
                request = self.getline('help> ')
                wenn not request: break
            except (KeyboardInterrupt, EOFError):
                break
            request = request.strip()

            # Make sure significant trailing quoting marks of literals don't
            # get deleted while cleaning input
            wenn (len(request) > 2 and request[0] == request[-1] in ("'", '"')
                    and request[0] not in request[1:-1]):
                request = request[1:-1]
            wenn request.lower() in ('q', 'quit', 'exit'): break
            wenn request == 'help':
                self.intro()
            sonst:
                self.help(request)

    def getline(self, prompt):
        """Read one line, using input() when appropriate."""
        wenn self.input is sys.stdin:
            return input(prompt)
        sonst:
            self.output.write(prompt)
            self.output.flush()
            return self.input.readline()

    def help(self, request, is_cli=False):
        wenn isinstance(request, str):
            request = request.strip()
            wenn request == 'keywords': self.listkeywords()
            sowenn request == 'symbols': self.listsymbols()
            sowenn request == 'topics': self.listtopics()
            sowenn request == 'modules': self.listmodules()
            sowenn request[:8] == 'modules ':
                self.listmodules(request.split()[1])
            sowenn request in self.symbols: self.showsymbol(request)
            sowenn request in ['True', 'False', 'None']:
                # special case these keywords since they are objects too
                doc(eval(request), 'Help on %s:', output=self._output, is_cli=is_cli)
            sowenn request in self.keywords: self.showtopic(request)
            sowenn request in self.topics: self.showtopic(request)
            sowenn request: doc(request, 'Help on %s:', output=self._output, is_cli=is_cli)
            sonst: doc(str, 'Help on %s:', output=self._output, is_cli=is_cli)
        sowenn isinstance(request, Helper): self()
        sonst: doc(request, 'Help on %s:', output=self._output, is_cli=is_cli)
        self.output.write('\n')

    def intro(self):
        self.output.write(_introdoc())

    def list(self, items, columns=4, width=80):
        items = sorted(items)
        colw = width // columns
        rows = (len(items) + columns - 1) // columns
        fuer row in range(rows):
            fuer col in range(columns):
                i = col * rows + row
                wenn i < len(items):
                    self.output.write(items[i])
                    wenn col < columns - 1:
                        self.output.write(' ' + ' ' * (colw - 1 - len(items[i])))
            self.output.write('\n')

    def listkeywords(self):
        self.output.write('''
Here is a list of the Python keywords.  Enter any keyword to get more help.

''')
        self.list(self.keywords.keys())

    def listsymbols(self):
        self.output.write('''
Here is a list of the punctuation symbols which Python assigns special meaning
to. Enter any symbol to get more help.

''')
        self.list(self.symbols.keys())

    def listtopics(self):
        self.output.write('''
Here is a list of available topics.  Enter any topic name to get more help.

''')
        self.list(self.topics.keys(), columns=3)

    def showtopic(self, topic, more_xrefs=''):
        try:
            import pydoc_data.topics
        except ImportError:
            self.output.write('''
Sorry, topic and keyword documentation is not available because the
module "pydoc_data.topics" could not be found.
''')
            return
        target = self.topics.get(topic, self.keywords.get(topic))
        wenn not target:
            self.output.write('no documentation found fuer %s\n' % repr(topic))
            return
        wenn isinstance(target, str):
            return self.showtopic(target, more_xrefs)

        label, xrefs = target
        try:
            doc = pydoc_data.topics.topics[label]
        except KeyError:
            self.output.write('no documentation found fuer %s\n' % repr(topic))
            return
        doc = doc.strip() + '\n'
        wenn more_xrefs:
            xrefs = (xrefs or '') + ' ' + more_xrefs
        wenn xrefs:
            text = 'Related help topics: ' + ', '.join(xrefs.split()) + '\n'
            wrapped_text = textwrap.wrap(text, 72)
            doc += '\n%s\n' % '\n'.join(wrapped_text)

        wenn self._output is None:
            pager(doc, f'Help on {topic!s}')
        sonst:
            self.output.write(doc)

    def _gettopic(self, topic, more_xrefs=''):
        """Return unbuffered tuple of (topic, xrefs).

        If an error occurs here, the exception is caught and displayed by
        the url handler.

        This function duplicates the showtopic method but returns its
        result directly so it can be formatted fuer display in an html page.
        """
        try:
            import pydoc_data.topics
        except ImportError:
            return('''
Sorry, topic and keyword documentation is not available because the
module "pydoc_data.topics" could not be found.
''' , '')
        target = self.topics.get(topic, self.keywords.get(topic))
        wenn not target:
            raise ValueError('could not find topic')
        wenn isinstance(target, str):
            return self._gettopic(target, more_xrefs)
        label, xrefs = target
        doc = pydoc_data.topics.topics[label]
        wenn more_xrefs:
            xrefs = (xrefs or '') + ' ' + more_xrefs
        return doc, xrefs

    def showsymbol(self, symbol):
        target = self.symbols[symbol]
        topic, _, xrefs = target.partition(' ')
        self.showtopic(topic, xrefs)

    def listmodules(self, key=''):
        wenn key:
            self.output.write('''
Here is a list of modules whose name or summary contains '{}'.
If there are any, enter a module name to get more help.

'''.format(key))
            apropos(key)
        sonst:
            self.output.write('''
Please wait a moment while I gather a list of all available modules...

''')
            modules = {}
            def callback(path, modname, desc, modules=modules):
                wenn modname and modname[-9:] == '.__init__':
                    modname = modname[:-9] + ' (package)'
                wenn modname.find('.') < 0:
                    modules[modname] = 1
            def onerror(modname):
                callback(None, modname, None)
            ModuleScanner().run(callback, onerror=onerror)
            self.list(modules.keys())
            self.output.write('''
Enter any module name to get more help.  Or, type "modules spam" to search
fuer modules whose name or summary contain the string "spam".
''')

help = Helper()

klasse ModuleScanner:
    """An interruptible scanner that searches module synopses."""

    def run(self, callback, key=None, completer=None, onerror=None):
        wenn key: key = key.lower()
        self.quit = False
        seen = {}

        fuer modname in sys.builtin_module_names:
            wenn modname != '__main__':
                seen[modname] = 1
                wenn key is None:
                    callback(None, modname, '')
                sonst:
                    name = __import__(modname).__doc__ or ''
                    desc = name.split('\n')[0]
                    name = modname + ' - ' + desc
                    wenn name.lower().find(key) >= 0:
                        callback(None, modname, desc)

        fuer importer, modname, ispkg in pkgutil.walk_packages(onerror=onerror):
            wenn self.quit:
                break

            wenn key is None:
                callback(None, modname, '')
            sonst:
                try:
                    spec = importer.find_spec(modname)
                except SyntaxError:
                    # raised by tests fuer bad coding cookies or BOM
                    continue
                loader = spec.loader
                wenn hasattr(loader, 'get_source'):
                    try:
                        source = loader.get_source(modname)
                    except Exception:
                        wenn onerror:
                            onerror(modname)
                        continue
                    desc = source_synopsis(io.StringIO(source)) or ''
                    wenn hasattr(loader, 'get_filename'):
                        path = loader.get_filename(modname)
                    sonst:
                        path = None
                sonst:
                    try:
                        module = importlib._bootstrap._load(spec)
                    except ImportError:
                        wenn onerror:
                            onerror(modname)
                        continue
                    desc = module.__doc__.splitlines()[0] wenn module.__doc__ sonst ''
                    path = getattr(module,'__file__',None)
                name = modname + ' - ' + desc
                wenn name.lower().find(key) >= 0:
                    callback(path, modname, desc)

        wenn completer:
            completer()

def apropos(key):
    """Print all the one-line module summaries that contain a substring."""
    def callback(path, modname, desc):
        wenn modname[-9:] == '.__init__':
            modname = modname[:-9] + ' (package)'
        print(modname, desc and '- ' + desc)
    def onerror(modname):
        pass
    with warnings.catch_warnings():
        warnings.filterwarnings('ignore') # ignore problems during import
        ModuleScanner().run(callback, key, onerror=onerror)

# --------------------------------------- enhanced web browser interface

def _start_server(urlhandler, hostname, port):
    """Start an HTTP server thread on a specific port.

    Start an HTML/text server thread, so HTML or text documents can be
    browsed dynamically and interactively with a web browser.  Example use:

        >>> import time
        >>> import pydoc

        Define a URL handler.  To determine what the client is asking
        for, check the URL and content_type.

        Then get or generate some text or HTML code and return it.

        >>> def my_url_handler(url, content_type):
        ...     text = 'the URL sent was: (%s, %s)' % (url, content_type)
        ...     return text

        Start server thread on port 0.
        If you use port 0, the server will pick a random port number.
        You can then use serverthread.port to get the port number.

        >>> port = 0
        >>> serverthread = pydoc._start_server(my_url_handler, port)

        Check that the server is really started.  If it is, open browser
        and get first page.  Use serverthread.url as the starting page.

        >>> wenn serverthread.serving:
        ...    import webbrowser

        The next two lines are commented out so a browser doesn't open if
        doctest is run on this module.

        #...    webbrowser.open(serverthread.url)
        #True

        Let the server do its thing. We just need to monitor its status.
        Use time.sleep so the loop doesn't hog the CPU.

        >>> starttime = time.monotonic()
        >>> timeout = 1                    #seconds

        This is a short timeout fuer testing purposes.

        >>> while serverthread.serving:
        ...     time.sleep(.01)
        ...     wenn serverthread.serving and time.monotonic() - starttime > timeout:
        ...          serverthread.stop()
        ...          break

        Print any errors that may have occurred.

        >>> print(serverthread.error)
        None
   """
    import http.server
    import email.message
    import select
    import threading

    klasse DocHandler(http.server.BaseHTTPRequestHandler):

        def do_GET(self):
            """Process a request from an HTML browser.

            The URL received is in self.path.
            Get an HTML page from self.urlhandler and send it.
            """
            wenn self.path.endswith('.css'):
                content_type = 'text/css'
            sonst:
                content_type = 'text/html'
            self.send_response(200)
            self.send_header('Content-Type', '%s; charset=UTF-8' % content_type)
            self.end_headers()
            self.wfile.write(self.urlhandler(
                self.path, content_type).encode('utf-8'))

        def log_message(self, *args):
            # Don't log messages.
            pass

    klasse DocServer(http.server.HTTPServer):

        def __init__(self, host, port, callback):
            self.host = host
            self.address = (self.host, port)
            self.callback = callback
            self.base.__init__(self, self.address, self.handler)
            self.quit = False

        def serve_until_quit(self):
            while not self.quit:
                rd, wr, ex = select.select([self.socket.fileno()], [], [], 1)
                wenn rd:
                    self.handle_request()
            self.server_close()

        def server_activate(self):
            self.base.server_activate(self)
            wenn self.callback:
                self.callback(self)

    klasse ServerThread(threading.Thread):

        def __init__(self, urlhandler, host, port):
            self.urlhandler = urlhandler
            self.host = host
            self.port = int(port)
            threading.Thread.__init__(self)
            self.serving = False
            self.error = None
            self.docserver = None

        def run(self):
            """Start the server."""
            try:
                DocServer.base = http.server.HTTPServer
                DocServer.handler = DocHandler
                DocHandler.MessageClass = email.message.Message
                DocHandler.urlhandler = staticmethod(self.urlhandler)
                docsvr = DocServer(self.host, self.port, self.ready)
                self.docserver = docsvr
                docsvr.serve_until_quit()
            except Exception as err:
                self.error = err

        def ready(self, server):
            self.serving = True
            self.host = server.host
            self.port = server.server_port
            self.url = 'http://%s:%d/' % (self.host, self.port)

        def stop(self):
            """Stop the server and this thread nicely"""
            self.docserver.quit = True
            self.join()
            # explicitly break a reference cycle: DocServer.callback
            # has indirectly a reference to ServerThread.
            self.docserver = None
            self.serving = False
            self.url = None

    thread = ServerThread(urlhandler, hostname, port)
    thread.start()
    # Wait until thread.serving is True and thread.docserver is set
    # to make sure we are really up before returning.
    while not thread.error and not (thread.serving and thread.docserver):
        time.sleep(.01)
    return thread


def _url_handler(url, content_type="text/html"):
    """The pydoc url handler fuer use with the pydoc server.

    If the content_type is 'text/css', the _pydoc.css style
    sheet is read and returned wenn it exits.

    If the content_type is 'text/html', then the result of
    get_html_page(url) is returned.
    """
    klasse _HTMLDoc(HTMLDoc):

        def page(self, title, contents):
            """Format an HTML page."""
            css_path = "pydoc_data/_pydoc.css"
            css_link = (
                '<link rel="stylesheet" type="text/css" href="%s">' %
                css_path)
            return '''\
<!DOCTYPE>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Pydoc: %s</title>
%s</head><body>%s<div style="clear:both;padding-top:.5em;">%s</div>
</body></html>''' % (title, css_link, html_navbar(), contents)


    html = _HTMLDoc()

    def html_navbar():
        version = html.escape("%s [%s, %s]" % (platform.python_version(),
                                               platform.python_build()[0],
                                               platform.python_compiler()))
        return """
            <div style='float:left'>
                Python %s<br>%s
            </div>
            <div style='float:right'>
                <div style='text-align:center'>
                  <a href="index.html">Module Index</a>
                  : <a href="topics.html">Topics</a>
                  : <a href="keywords.html">Keywords</a>
                </div>
                <div>
                    <form action="get" style='display:inline;'>
                      <input type=text name=key size=15>
                      <input type=submit value="Get">
                    </form>&nbsp;
                    <form action="search" style='display:inline;'>
                      <input type=text name=key size=15>
                      <input type=submit value="Search">
                    </form>
                </div>
            </div>
            """ % (version, html.escape(platform.platform(terse=True)))

    def html_index():
        """Module Index page."""

        def bltinlink(name):
            return '<a href="%s.html">%s</a>' % (name, name)

        heading = html.heading(
            '<strong class="title">Index of Modules</strong>'
        )
        names = [name fuer name in sys.builtin_module_names
                 wenn name != '__main__']
        contents = html.multicolumn(names, bltinlink)
        contents = [heading, '<p>' + html.bigsection(
            'Built-in Modules', 'index', contents)]

        seen = {}
        fuer dir in sys.path:
            contents.append(html.index(dir, seen))

        contents.append(
            '<p align=right class="heading-text grey"><strong>pydoc</strong> by Ka-Ping Yee'
            '&lt;ping@lfw.org&gt;</p>')
        return 'Index of Modules', ''.join(contents)

    def html_search(key):
        """Search results page."""
        # scan fuer modules
        search_result = []

        def callback(path, modname, desc):
            wenn modname[-9:] == '.__init__':
                modname = modname[:-9] + ' (package)'
            search_result.append((modname, desc and '- ' + desc))

        with warnings.catch_warnings():
            warnings.filterwarnings('ignore') # ignore problems during import
            def onerror(modname):
                pass
            ModuleScanner().run(callback, key, onerror=onerror)

        # format page
        def bltinlink(name):
            return '<a href="%s.html">%s</a>' % (name, name)

        results = []
        heading = html.heading(
            '<strong class="title">Search Results</strong>',
        )
        fuer name, desc in search_result:
            results.append(bltinlink(name) + desc)
        contents = heading + html.bigsection(
            'key = %s' % key, 'index', '<br>'.join(results))
        return 'Search Results', contents

    def html_topics():
        """Index of topic texts available."""

        def bltinlink(name):
            return '<a href="topic?key=%s">%s</a>' % (name, name)

        heading = html.heading(
            '<strong class="title">INDEX</strong>',
        )
        names = sorted(Helper.topics.keys())

        contents = html.multicolumn(names, bltinlink)
        contents = heading + html.bigsection(
            'Topics', 'index', contents)
        return 'Topics', contents

    def html_keywords():
        """Index of keywords."""
        heading = html.heading(
            '<strong class="title">INDEX</strong>',
        )
        names = sorted(Helper.keywords.keys())

        def bltinlink(name):
            return '<a href="topic?key=%s">%s</a>' % (name, name)

        contents = html.multicolumn(names, bltinlink)
        contents = heading + html.bigsection(
            'Keywords', 'index', contents)
        return 'Keywords', contents

    def html_topicpage(topic):
        """Topic or keyword help page."""
        buf = io.StringIO()
        htmlhelp = Helper(buf, buf)
        contents, xrefs = htmlhelp._gettopic(topic)
        wenn topic in htmlhelp.keywords:
            title = 'KEYWORD'
        sonst:
            title = 'TOPIC'
        heading = html.heading(
            '<strong class="title">%s</strong>' % title,
        )
        contents = '<pre>%s</pre>' % html.markup(contents)
        contents = html.bigsection(topic , 'index', contents)
        wenn xrefs:
            xrefs = sorted(xrefs.split())

            def bltinlink(name):
                return '<a href="topic?key=%s">%s</a>' % (name, name)

            xrefs = html.multicolumn(xrefs, bltinlink)
            xrefs = html.section('Related help topics: ', 'index', xrefs)
        return ('%s %s' % (title, topic),
                ''.join((heading, contents, xrefs)))

    def html_getobj(url):
        obj = locate(url, forceload=1)
        wenn obj is None and url != 'None':
            raise ValueError('could not find object')
        title = describe(obj)
        content = html.document(obj, url)
        return title, content

    def html_error(url, exc):
        heading = html.heading(
            '<strong class="title">Error</strong>',
        )
        contents = '<br>'.join(html.escape(line) fuer line in
                               format_exception_only(type(exc), exc))
        contents = heading + html.bigsection(url, 'error', contents)
        return "Error - %s" % url, contents

    def get_html_page(url):
        """Generate an HTML page fuer url."""
        complete_url = url
        wenn url.endswith('.html'):
            url = url[:-5]
        try:
            wenn url in ("", "index"):
                title, content = html_index()
            sowenn url == "topics":
                title, content = html_topics()
            sowenn url == "keywords":
                title, content = html_keywords()
            sowenn '=' in url:
                op, _, url = url.partition('=')
                wenn op == "search?key":
                    title, content = html_search(url)
                sowenn op == "topic?key":
                    # try topics first, then objects.
                    try:
                        title, content = html_topicpage(url)
                    except ValueError:
                        title, content = html_getobj(url)
                sowenn op == "get?key":
                    # try objects first, then topics.
                    wenn url in ("", "index"):
                        title, content = html_index()
                    sonst:
                        try:
                            title, content = html_getobj(url)
                        except ValueError:
                            title, content = html_topicpage(url)
                sonst:
                    raise ValueError('bad pydoc url')
            sonst:
                title, content = html_getobj(url)
        except Exception as exc:
            # Catch any errors and display them in an error page.
            title, content = html_error(complete_url, exc)
        return html.page(title, content)

    wenn url.startswith('/'):
        url = url[1:]
    wenn content_type == 'text/css':
        path_here = os.path.dirname(os.path.realpath(__file__))
        css_path = os.path.join(path_here, url)
        with open(css_path) as fp:
            return ''.join(fp.readlines())
    sowenn content_type == 'text/html':
        return get_html_page(url)
    # Errors outside the url handler are caught by the server.
    raise TypeError('unknown content type %r fuer url %s' % (content_type, url))


def browse(port=0, *, open_browser=True, hostname='localhost'):
    """Start the enhanced pydoc web server and open a web browser.

    Use port '0' to start the server on an arbitrary port.
    Set open_browser to False to suppress opening a browser.
    """
    import webbrowser
    serverthread = _start_server(_url_handler, hostname, port)
    wenn serverthread.error:
        print(serverthread.error)
        return
    wenn serverthread.serving:
        server_help_msg = 'Server commands: [b]rowser, [q]uit'
        wenn open_browser:
            webbrowser.open(serverthread.url)
        try:
            print('Server ready at', serverthread.url)
            print(server_help_msg)
            while serverthread.serving:
                cmd = input('server> ')
                cmd = cmd.lower()
                wenn cmd == 'q':
                    break
                sowenn cmd == 'b':
                    webbrowser.open(serverthread.url)
                sonst:
                    print(server_help_msg)
        except (KeyboardInterrupt, EOFError):
            print()
        finally:
            wenn serverthread.serving:
                serverthread.stop()
                print('Server stopped')


# -------------------------------------------------- command-line interface

def ispath(x):
    return isinstance(x, str) and x.find(os.sep) >= 0

def _get_revised_path(given_path, argv0):
    """Ensures current directory is on returned path, and argv0 directory is not

    Exception: argv0 dir is left alone wenn it's also pydoc's directory.

    Returns a new path entry list, or None wenn no adjustment is needed.
    """
    # Scripts may get the current directory in their path by default wenn they're
    # run with the -m switch, or directly from the current directory.
    # The interactive prompt also allows imports from the current directory.

    # Accordingly, wenn the current directory is already present, don't make
    # any changes to the given_path
    wenn '' in given_path or os.curdir in given_path or os.getcwd() in given_path:
        return None

    # Otherwise, add the current directory to the given path, and remove the
    # script directory (as long as the latter isn't also pydoc's directory.
    stdlib_dir = os.path.dirname(__file__)
    script_dir = os.path.dirname(argv0)
    revised_path = given_path.copy()
    wenn script_dir in given_path and not os.path.samefile(script_dir, stdlib_dir):
        revised_path.remove(script_dir)
    revised_path.insert(0, os.getcwd())
    return revised_path


# Note: the tests only cover _get_revised_path, not _adjust_cli_path itself
def _adjust_cli_sys_path():
    """Ensures current directory is on sys.path, and __main__ directory is not.

    Exception: __main__ dir is left alone wenn it's also pydoc's directory.
    """
    revised_path = _get_revised_path(sys.path, sys.argv[0])
    wenn revised_path is not None:
        sys.path[:] = revised_path


def cli():
    """Command-line interface (looks at sys.argv to decide what to do)."""
    import getopt
    klasse BadUsage(Exception): pass

    _adjust_cli_sys_path()

    try:
        opts, args = getopt.getopt(sys.argv[1:], 'bk:n:p:w')
        writing = False
        start_server = False
        open_browser = False
        port = 0
        hostname = 'localhost'
        fuer opt, val in opts:
            wenn opt == '-b':
                start_server = True
                open_browser = True
            wenn opt == '-k':
                apropos(val)
                return
            wenn opt == '-p':
                start_server = True
                port = val
            wenn opt == '-w':
                writing = True
            wenn opt == '-n':
                start_server = True
                hostname = val

        wenn start_server:
            browse(port, hostname=hostname, open_browser=open_browser)
            return

        wenn not args: raise BadUsage
        fuer arg in args:
            wenn ispath(arg) and not os.path.exists(arg):
                print('file %r does not exist' % arg)
                sys.exit(1)
            try:
                wenn ispath(arg) and os.path.isfile(arg):
                    arg = importfile(arg)
                wenn writing:
                    wenn ispath(arg) and os.path.isdir(arg):
                        writedocs(arg)
                    sonst:
                        writedoc(arg)
                sonst:
                    help.help(arg, is_cli=True)
            except (ImportError, ErrorDuringImport) as value:
                print(value)
                sys.exit(1)

    except (getopt.error, BadUsage):
        cmd = os.path.splitext(os.path.basename(sys.argv[0]))[0]
        print("""pydoc - the Python documentation tool

{cmd} <name> ...
    Show text documentation on something.  <name> may be the name of a
    Python keyword, topic, function, module, or package, or a dotted
    reference to a klasse or function within a module or module in a
    package.  If <name> contains a '{sep}', it is used as the path to a
    Python source file to document. If name is 'keywords', 'topics',
    or 'modules', a listing of these things is displayed.

{cmd} -k <keyword>
    Search fuer a keyword in the synopsis lines of all available modules.

{cmd} -n <hostname>
    Start an HTTP server with the given hostname (default: localhost).

{cmd} -p <port>
    Start an HTTP server on the given port on the local machine.  Port
    number 0 can be used to get an arbitrary unused port.

{cmd} -b
    Start an HTTP server on an arbitrary unused port and open a web browser
    to interactively browse documentation.  This option can be used in
    combination with -n and/or -p.

{cmd} -w <name> ...
    Write out the HTML documentation fuer a module to a file in the current
    directory.  If <name> contains a '{sep}', it is treated as a filename; if
    it names a directory, documentation is written fuer all the contents.
""".format(cmd=cmd, sep=os.sep))

wenn __name__ == '__main__':
    cli()
