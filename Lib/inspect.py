"""Get useful information from live Python objects.

This module encapsulates the interface provided by the internal special
attributes (co_*, im_*, tb_*, etc.) in a friendlier fashion.
It also provides some help fuer examining source code and klasse layout.

Here are some of the useful functions provided by this module:

    ismodule(), isclass(), ismethod(), ispackage(), isfunction(),
        isgeneratorfunction(), isgenerator(), istraceback(), isframe(),
        iscode(), isbuiltin(), isroutine() - check object types
    getmembers() - get members of an object that satisfy a given condition

    getfile(), getsourcefile(), getsource() - find an object's source code
    getdoc(), getcomments() - get documentation on an object
    getmodule() - determine the module that an object came from
    getclasstree() - arrange classes so as to represent their hierarchy

    getargvalues(), getcallargs() - get info about function arguments
    getfullargspec() - same, with support fuer Python 3 features
    formatargvalues() - format an argument spec
    getouterframes(), getinnerframes() - get info about frames
    currentframe() - get the current stack frame
    stack(), trace() - get info about frames on the stack or in a traceback

    signature() - get a Signature object fuer the callable
"""

# This module is in the public domain.  No warranties.

__author__ = ('Ka-Ping Yee <ping@lfw.org>',
              'Yury Selivanov <yselivanov@sprymix.com>')

__all__ = [
    "AGEN_CLOSED",
    "AGEN_CREATED",
    "AGEN_RUNNING",
    "AGEN_SUSPENDED",
    "ArgInfo",
    "Arguments",
    "Attribute",
    "BlockFinder",
    "BoundArguments",
    "BufferFlags",
    "CORO_CLOSED",
    "CORO_CREATED",
    "CORO_RUNNING",
    "CORO_SUSPENDED",
    "CO_ASYNC_GENERATOR",
    "CO_COROUTINE",
    "CO_GENERATOR",
    "CO_ITERABLE_COROUTINE",
    "CO_NESTED",
    "CO_NEWLOCALS",
    "CO_NOFREE",
    "CO_OPTIMIZED",
    "CO_VARARGS",
    "CO_VARKEYWORDS",
    "CO_HAS_DOCSTRING",
    "CO_METHOD",
    "ClassFoundException",
    "ClosureVars",
    "EndOfBlock",
    "FrameInfo",
    "FullArgSpec",
    "GEN_CLOSED",
    "GEN_CREATED",
    "GEN_RUNNING",
    "GEN_SUSPENDED",
    "Parameter",
    "Signature",
    "TPFLAGS_IS_ABSTRACT",
    "Traceback",
    "classify_class_attrs",
    "cleandoc",
    "currentframe",
    "findsource",
    "formatannotation",
    "formatannotationrelativeto",
    "formatargvalues",
    "get_annotations",
    "getabsfile",
    "getargs",
    "getargvalues",
    "getasyncgenlocals",
    "getasyncgenstate",
    "getattr_static",
    "getblock",
    "getcallargs",
    "getclasstree",
    "getclosurevars",
    "getcomments",
    "getcoroutinelocals",
    "getcoroutinestate",
    "getdoc",
    "getfile",
    "getframeinfo",
    "getfullargspec",
    "getgeneratorlocals",
    "getgeneratorstate",
    "getinnerframes",
    "getlineno",
    "getmembers",
    "getmembers_static",
    "getmodule",
    "getmodulename",
    "getmro",
    "getouterframes",
    "getsource",
    "getsourcefile",
    "getsourcelines",
    "indentsize",
    "isabstract",
    "isasyncgen",
    "isasyncgenfunction",
    "isawaitable",
    "isbuiltin",
    "isclass",
    "iscode",
    "iscoroutine",
    "iscoroutinefunction",
    "isdatadescriptor",
    "isframe",
    "isfunction",
    "isgenerator",
    "isgeneratorfunction",
    "isgetsetdescriptor",
    "ismemberdescriptor",
    "ismethod",
    "ismethoddescriptor",
    "ismethodwrapper",
    "ismodule",
    "ispackage",
    "isroutine",
    "istraceback",
    "markcoroutinefunction",
    "signature",
    "stack",
    "trace",
    "unwrap",
    "walktree",
]


import abc
from annotationlib import Format, ForwardRef
from annotationlib import get_annotations  # re-exported
import ast
import dis
import collections.abc
import enum
import importlib.machinery
import itertools
import linecache
import os
import re
import sys
import tokenize
import token
import types
import functools
import builtins
from keyword import iskeyword
from operator import attrgetter
from collections import namedtuple, OrderedDict
from weakref import ref as make_weakref

# Create constants fuer the compiler flags in Include/code.h
# We try to get them from dis to avoid duplication
mod_dict = globals()
fuer k, v in dis.COMPILER_FLAG_NAMES.items():
    mod_dict["CO_" + v] = k
del k, v, mod_dict

# See Include/object.h
TPFLAGS_IS_ABSTRACT = 1 << 20


# ----------------------------------------------------------- type-checking
def ismodule(object):
    """Return true wenn the object is a module."""
    return isinstance(object, types.ModuleType)

def isclass(object):
    """Return true wenn the object is a class."""
    return isinstance(object, type)

def ismethod(object):
    """Return true wenn the object is an instance method."""
    return isinstance(object, types.MethodType)

def ispackage(object):
    """Return true wenn the object is a package."""
    return ismodule(object) and hasattr(object, "__path__")

def ismethoddescriptor(object):
    """Return true wenn the object is a method descriptor.

    But not wenn ismethod() or isclass() or isfunction() are true.

    This is new in Python 2.2, and, fuer example, is true of int.__add__.
    An object passing this test has a __get__ attribute, but not a
    __set__ attribute or a __delete__ attribute. Beyond that, the set
    of attributes varies; __name__ is usually sensible, and __doc__
    often is.

    Methods implemented via descriptors that also pass one of the other
    tests return false from the ismethoddescriptor() test, simply because
    the other tests promise more -- you can, e.g., count on having the
    __func__ attribute (etc) when an object passes ismethod()."""
    wenn isclass(object) or ismethod(object) or isfunction(object):
        # mutual exclusion
        return Falsch
    tp = type(object)
    return (hasattr(tp, "__get__")
            and not hasattr(tp, "__set__")
            and not hasattr(tp, "__delete__"))

def isdatadescriptor(object):
    """Return true wenn the object is a data descriptor.

    Data descriptors have a __set__ or a __delete__ attribute.  Examples are
    properties (defined in Python) and getsets and members (defined in C).
    Typically, data descriptors will also have __name__ and __doc__ attributes
    (properties, getsets, and members have both of these attributes), but this
    is not guaranteed."""
    wenn isclass(object) or ismethod(object) or isfunction(object):
        # mutual exclusion
        return Falsch
    tp = type(object)
    return hasattr(tp, "__set__") or hasattr(tp, "__delete__")

wenn hasattr(types, 'MemberDescriptorType'):
    # CPython and equivalent
    def ismemberdescriptor(object):
        """Return true wenn the object is a member descriptor.

        Member descriptors are specialized descriptors defined in extension
        modules."""
        return isinstance(object, types.MemberDescriptorType)
sonst:
    # Other implementations
    def ismemberdescriptor(object):
        """Return true wenn the object is a member descriptor.

        Member descriptors are specialized descriptors defined in extension
        modules."""
        return Falsch

wenn hasattr(types, 'GetSetDescriptorType'):
    # CPython and equivalent
    def isgetsetdescriptor(object):
        """Return true wenn the object is a getset descriptor.

        getset descriptors are specialized descriptors defined in extension
        modules."""
        return isinstance(object, types.GetSetDescriptorType)
sonst:
    # Other implementations
    def isgetsetdescriptor(object):
        """Return true wenn the object is a getset descriptor.

        getset descriptors are specialized descriptors defined in extension
        modules."""
        return Falsch

def isfunction(object):
    """Return true wenn the object is a user-defined function.

    Function objects provide these attributes:
        __doc__         documentation string
        __name__        name with which this function was defined
        __qualname__    qualified name of this function
        __module__      name of the module the function was defined in or Nichts
        __code__        code object containing compiled function bytecode
        __defaults__    tuple of any default values fuer arguments
        __globals__     global namespace in which this function was defined
        __annotations__ dict of parameter annotations
        __kwdefaults__  dict of keyword only parameters with defaults
        __dict__        namespace which is supporting arbitrary function attributes
        __closure__     a tuple of cells or Nichts
        __type_params__ tuple of type parameters"""
    return isinstance(object, types.FunctionType)

def _has_code_flag(f, flag):
    """Return true wenn ``f`` is a function (or a method or functools.partial
    wrapper wrapping a function or a functools.partialmethod wrapping a
    function) whose code object has the given ``flag``
    set in its flags."""
    f = functools._unwrap_partialmethod(f)
    while ismethod(f):
        f = f.__func__
    f = functools._unwrap_partial(f)
    wenn not (isfunction(f) or _signature_is_functionlike(f)):
        return Falsch
    return bool(f.__code__.co_flags & flag)

def isgeneratorfunction(obj):
    """Return true wenn the object is a user-defined generator function.

    Generator function objects provide the same attributes as functions.
    See help(isfunction) fuer a list of attributes."""
    return _has_code_flag(obj, CO_GENERATOR)

# A marker fuer markcoroutinefunction and iscoroutinefunction.
_is_coroutine_mark = object()

def _has_coroutine_mark(f):
    while ismethod(f):
        f = f.__func__
    f = functools._unwrap_partial(f)
    return getattr(f, "_is_coroutine_marker", Nichts) is _is_coroutine_mark

def markcoroutinefunction(func):
    """
    Decorator to ensure callable is recognised as a coroutine function.
    """
    wenn hasattr(func, '__func__'):
        func = func.__func__
    func._is_coroutine_marker = _is_coroutine_mark
    return func

def iscoroutinefunction(obj):
    """Return true wenn the object is a coroutine function.

    Coroutine functions are normally defined with "async def" syntax, but may
    be marked via markcoroutinefunction.
    """
    return _has_code_flag(obj, CO_COROUTINE) or _has_coroutine_mark(obj)

def isasyncgenfunction(obj):
    """Return true wenn the object is an asynchronous generator function.

    Asynchronous generator functions are defined with "async def"
    syntax and have "yield" expressions in their body.
    """
    return _has_code_flag(obj, CO_ASYNC_GENERATOR)

def isasyncgen(object):
    """Return true wenn the object is an asynchronous generator."""
    return isinstance(object, types.AsyncGeneratorType)

def isgenerator(object):
    """Return true wenn the object is a generator.

    Generator objects provide these attributes:
        gi_code         code object
        gi_frame        frame object or possibly Nichts once the generator has
                        been exhausted
        gi_running      set to 1 when generator is executing, 0 otherwise
        gi_yieldfrom    object being iterated by yield from or Nichts

        __iter__()      defined to support iteration over container
        close()         raises a new GeneratorExit exception inside the
                        generator to terminate the iteration
        send()          resumes the generator and "sends" a value that becomes
                        the result of the current yield-expression
        throw()         used to raise an exception inside the generator"""
    return isinstance(object, types.GeneratorType)

def iscoroutine(object):
    """Return true wenn the object is a coroutine."""
    return isinstance(object, types.CoroutineType)

def isawaitable(object):
    """Return true wenn object can be passed to an ``await`` expression."""
    return (isinstance(object, types.CoroutineType) or
            isinstance(object, types.GeneratorType) and
                bool(object.gi_code.co_flags & CO_ITERABLE_COROUTINE) or
            isinstance(object, collections.abc.Awaitable))

def istraceback(object):
    """Return true wenn the object is a traceback.

    Traceback objects provide these attributes:
        tb_frame        frame object at this level
        tb_lasti        index of last attempted instruction in bytecode
        tb_lineno       current line number in Python source code
        tb_next         next inner traceback object (called by this level)"""
    return isinstance(object, types.TracebackType)

def isframe(object):
    """Return true wenn the object is a frame object.

    Frame objects provide these attributes:
        f_back          next outer frame object (this frame's caller)
        f_builtins      built-in namespace seen by this frame
        f_code          code object being executed in this frame
        f_globals       global namespace seen by this frame
        f_lasti         index of last attempted instruction in bytecode
        f_lineno        current line number in Python source code
        f_locals        local namespace seen by this frame
        f_trace         tracing function fuer this frame, or Nichts
        f_trace_lines   is a tracing event triggered fuer each source line?
        f_trace_opcodes are per-opcode events being requested?

        clear()          used to clear all references to local variables"""
    return isinstance(object, types.FrameType)

def iscode(object):
    """Return true wenn the object is a code object.

    Code objects provide these attributes:
        co_argcount         number of arguments (not including *, ** args
                            or keyword only arguments)
        co_code             string of raw compiled bytecode
        co_cellvars         tuple of names of cell variables
        co_consts           tuple of constants used in the bytecode
        co_filename         name of file in which this code object was created
        co_firstlineno      number of first line in Python source code
        co_flags            bitmap: 1=optimized | 2=newlocals | 4=*arg | 8=**arg
                            | 16=nested | 32=generator | 64=nofree | 128=coroutine
                            | 256=iterable_coroutine | 512=async_generator
                            | 0x4000000=has_docstring
        co_freevars         tuple of names of free variables
        co_posonlyargcount  number of positional only arguments
        co_kwonlyargcount   number of keyword only arguments (not including ** arg)
        co_lnotab           encoded mapping of line numbers to bytecode indices
        co_name             name with which this code object was defined
        co_names            tuple of names other than arguments and function locals
        co_nlocals          number of local variables
        co_stacksize        virtual machine stack space required
        co_varnames         tuple of names of arguments and local variables
        co_qualname         fully qualified function name

        co_lines()          returns an iterator that yields successive bytecode ranges
        co_positions()      returns an iterator of source code positions fuer each bytecode instruction
        replace()           returns a copy of the code object with a new values"""
    return isinstance(object, types.CodeType)

def isbuiltin(object):
    """Return true wenn the object is a built-in function or method.

    Built-in functions and methods provide these attributes:
        __doc__         documentation string
        __name__        original name of this function or method
        __self__        instance to which a method is bound, or Nichts"""
    return isinstance(object, types.BuiltinFunctionType)

def ismethodwrapper(object):
    """Return true wenn the object is a method wrapper."""
    return isinstance(object, types.MethodWrapperType)

def isroutine(object):
    """Return true wenn the object is any kind of function or method."""
    return (isbuiltin(object)
            or isfunction(object)
            or ismethod(object)
            or ismethoddescriptor(object)
            or ismethodwrapper(object)
            or isinstance(object, functools._singledispatchmethod_get))

def isabstract(object):
    """Return true wenn the object is an abstract base klasse (ABC)."""
    wenn not isinstance(object, type):
        return Falsch
    wenn object.__flags__ & TPFLAGS_IS_ABSTRACT:
        return Wahr
    wenn not issubclass(type(object), abc.ABCMeta):
        return Falsch
    wenn hasattr(object, '__abstractmethods__'):
        # It looks like ABCMeta.__new__ has finished running;
        # TPFLAGS_IS_ABSTRACT should have been accurate.
        return Falsch
    # It looks like ABCMeta.__new__ has not finished running yet; we're
    # probably in __init_subclass__. We'll look fuer abstractmethods manually.
    fuer name, value in object.__dict__.items():
        wenn getattr(value, "__isabstractmethod__", Falsch):
            return Wahr
    fuer base in object.__bases__:
        fuer name in getattr(base, "__abstractmethods__", ()):
            value = getattr(object, name, Nichts)
            wenn getattr(value, "__isabstractmethod__", Falsch):
                return Wahr
    return Falsch

def _getmembers(object, predicate, getter):
    results = []
    processed = set()
    names = dir(object)
    wenn isclass(object):
        mro = getmro(object)
        # add any DynamicClassAttributes to the list of names wenn object is a class;
        # this may result in duplicate entries if, fuer example, a virtual
        # attribute with the same name as a DynamicClassAttribute exists
        try:
            fuer base in object.__bases__:
                fuer k, v in base.__dict__.items():
                    wenn isinstance(v, types.DynamicClassAttribute):
                        names.append(k)
        except AttributeError:
            pass
    sonst:
        mro = ()
    fuer key in names:
        # First try to get the value via getattr.  Some descriptors don't
        # like calling their __get__ (see bug #1785), so fall back to
        # looking in the __dict__.
        try:
            value = getter(object, key)
            # handle the duplicate key
            wenn key in processed:
                raise AttributeError
        except AttributeError:
            fuer base in mro:
                wenn key in base.__dict__:
                    value = base.__dict__[key]
                    break
            sonst:
                # could be a (currently) missing slot member, or a buggy
                # __dir__; discard and move on
                continue
        wenn not predicate or predicate(value):
            results.append((key, value))
        processed.add(key)
    results.sort(key=lambda pair: pair[0])
    return results

def getmembers(object, predicate=Nichts):
    """Return all members of an object as (name, value) pairs sorted by name.
    Optionally, only return members that satisfy a given predicate."""
    return _getmembers(object, predicate, getattr)

def getmembers_static(object, predicate=Nichts):
    """Return all members of an object as (name, value) pairs sorted by name
    without triggering dynamic lookup via the descriptor protocol,
    __getattr__ or __getattribute__. Optionally, only return members that
    satisfy a given predicate.

    Note: this function may not be able to retrieve all members
       that getmembers can fetch (like dynamically created attributes)
       and may find members that getmembers can't (like descriptors
       that raise AttributeError). It can also return descriptor objects
       instead of instance members in some cases.
    """
    return _getmembers(object, predicate, getattr_static)

Attribute = namedtuple('Attribute', 'name kind defining_class object')

def classify_class_attrs(cls):
    """Return list of attribute-descriptor tuples.

    For each name in dir(cls), the return list contains a 4-tuple
    with these elements:

        0. The name (a string).

        1. The kind of attribute this is, one of these strings:
               'class method'    created via classmethod()
               'static method'   created via staticmethod()
               'property'        created via property()
               'method'          any other flavor of method or descriptor
               'data'            not a method

        2. The klasse which defined this attribute (a class).

        3. The object as obtained by calling getattr; wenn this fails, or wenn the
           resulting object does not live anywhere in the class' mro (including
           metaclasses) then the object is looked up in the defining class's
           dict (found by walking the mro).

    If one of the items in dir(cls) is stored in the metaclass it will now
    be discovered and not have Nichts be listed as the klasse in which it was
    defined.  Any items whose home klasse cannot be discovered are skipped.
    """

    mro = getmro(cls)
    metamro = getmro(type(cls)) # fuer attributes stored in the metaclass
    metamro = tuple(cls fuer cls in metamro wenn cls not in (type, object))
    class_bases = (cls,) + mro
    all_bases = class_bases + metamro
    names = dir(cls)
    # :dd any DynamicClassAttributes to the list of names;
    # this may result in duplicate entries if, fuer example, a virtual
    # attribute with the same name as a DynamicClassAttribute exists.
    fuer base in mro:
        fuer k, v in base.__dict__.items():
            wenn isinstance(v, types.DynamicClassAttribute) and v.fget is not Nichts:
                names.append(k)
    result = []
    processed = set()

    fuer name in names:
        # Get the object associated with the name, and where it was defined.
        # Normal objects will be looked up with both getattr and directly in
        # its class' dict (in case getattr fails [bug #1785], and also to look
        # fuer a docstring).
        # For DynamicClassAttributes on the second pass we only look in the
        # class's dict.
        #
        # Getting an obj from the __dict__ sometimes reveals more than
        # using getattr.  Static and klasse methods are dramatic examples.
        homecls = Nichts
        get_obj = Nichts
        dict_obj = Nichts
        wenn name not in processed:
            try:
                wenn name == '__dict__':
                    raise Exception("__dict__ is special, don't want the proxy")
                get_obj = getattr(cls, name)
            except Exception:
                pass
            sonst:
                homecls = getattr(get_obj, "__objclass__", homecls)
                wenn homecls not in class_bases:
                    # wenn the resulting object does not live somewhere in the
                    # mro, drop it and search the mro manually
                    homecls = Nichts
                    last_cls = Nichts
                    # first look in the classes
                    fuer srch_cls in class_bases:
                        srch_obj = getattr(srch_cls, name, Nichts)
                        wenn srch_obj is get_obj:
                            last_cls = srch_cls
                    # then check the metaclasses
                    fuer srch_cls in metamro:
                        try:
                            srch_obj = srch_cls.__getattr__(cls, name)
                        except AttributeError:
                            continue
                        wenn srch_obj is get_obj:
                            last_cls = srch_cls
                    wenn last_cls is not Nichts:
                        homecls = last_cls
        fuer base in all_bases:
            wenn name in base.__dict__:
                dict_obj = base.__dict__[name]
                wenn homecls not in metamro:
                    homecls = base
                break
        wenn homecls is Nichts:
            # unable to locate the attribute anywhere, most likely due to
            # buggy custom __dir__; discard and move on
            continue
        obj = get_obj wenn get_obj is not Nichts sonst dict_obj
        # Classify the object or its descriptor.
        wenn isinstance(dict_obj, (staticmethod, types.BuiltinMethodType)):
            kind = "static method"
            obj = dict_obj
        sowenn isinstance(dict_obj, (classmethod, types.ClassMethodDescriptorType)):
            kind = "class method"
            obj = dict_obj
        sowenn isinstance(dict_obj, property):
            kind = "property"
            obj = dict_obj
        sowenn isroutine(obj):
            kind = "method"
        sonst:
            kind = "data"
        result.append(Attribute(name, kind, homecls, obj))
        processed.add(name)
    return result

# ----------------------------------------------------------- klasse helpers

def getmro(cls):
    "Return tuple of base classes (including cls) in method resolution order."
    return cls.__mro__

# -------------------------------------------------------- function helpers

def unwrap(func, *, stop=Nichts):
    """Get the object wrapped by *func*.

   Follows the chain of :attr:`__wrapped__` attributes returning the last
   object in the chain.

   *stop* is an optional callback accepting an object in the wrapper chain
   as its sole argument that allows the unwrapping to be terminated early if
   the callback returns a true value. If the callback never returns a true
   value, the last object in the chain is returned as usual. For example,
   :func:`signature` uses this to stop unwrapping wenn any object in the
   chain has a ``__signature__`` attribute defined.

   :exc:`ValueError` is raised wenn a cycle is encountered.

    """
    f = func  # remember the original func fuer error reporting
    # Memoise by id to tolerate non-hashable objects, but store objects to
    # ensure they aren't destroyed, which would allow their IDs to be reused.
    memo = {id(f): f}
    recursion_limit = sys.getrecursionlimit()
    while not isinstance(func, type) and hasattr(func, '__wrapped__'):
        wenn stop is not Nichts and stop(func):
            break
        func = func.__wrapped__
        id_func = id(func)
        wenn (id_func in memo) or (len(memo) >= recursion_limit):
            raise ValueError('wrapper loop when unwrapping {!r}'.format(f))
        memo[id_func] = func
    return func

# -------------------------------------------------- source code extraction
def indentsize(line):
    """Return the indent size, in spaces, at the start of a line of text."""
    expline = line.expandtabs()
    return len(expline) - len(expline.lstrip())

def _findclass(func):
    cls = sys.modules.get(func.__module__)
    wenn cls is Nichts:
        return Nichts
    fuer name in func.__qualname__.split('.')[:-1]:
        cls = getattr(cls, name)
    wenn not isclass(cls):
        return Nichts
    return cls

def _finddoc(obj):
    wenn isclass(obj):
        fuer base in obj.__mro__:
            wenn base is not object:
                try:
                    doc = base.__doc__
                except AttributeError:
                    continue
                wenn doc is not Nichts:
                    return doc
        return Nichts

    wenn ismethod(obj):
        name = obj.__func__.__name__
        self = obj.__self__
        wenn (isclass(self) and
            getattr(getattr(self, name, Nichts), '__func__') is obj.__func__):
            # classmethod
            cls = self
        sonst:
            cls = self.__class__
    sowenn isfunction(obj):
        name = obj.__name__
        cls = _findclass(obj)
        wenn cls is Nichts or getattr(cls, name) is not obj:
            return Nichts
    sowenn isbuiltin(obj):
        name = obj.__name__
        self = obj.__self__
        wenn (isclass(self) and
            self.__qualname__ + '.' + name == obj.__qualname__):
            # classmethod
            cls = self
        sonst:
            cls = self.__class__
    # Should be tested before isdatadescriptor().
    sowenn isinstance(obj, property):
        name = obj.__name__
        cls = _findclass(obj.fget)
        wenn cls is Nichts or getattr(cls, name) is not obj:
            return Nichts
    sowenn ismethoddescriptor(obj) or isdatadescriptor(obj):
        name = obj.__name__
        cls = obj.__objclass__
        wenn getattr(cls, name) is not obj:
            return Nichts
        wenn ismemberdescriptor(obj):
            slots = getattr(cls, '__slots__', Nichts)
            wenn isinstance(slots, dict) and name in slots:
                return slots[name]
    sonst:
        return Nichts
    fuer base in cls.__mro__:
        try:
            doc = getattr(base, name).__doc__
        except AttributeError:
            continue
        wenn doc is not Nichts:
            return doc
    return Nichts

def getdoc(object):
    """Get the documentation string fuer an object.

    All tabs are expanded to spaces.  To clean up docstrings that are
    indented to line up with blocks of code, any whitespace than can be
    uniformly removed from the second line onwards is removed."""
    try:
        doc = object.__doc__
    except AttributeError:
        return Nichts
    wenn doc is Nichts:
        try:
            doc = _finddoc(object)
        except (AttributeError, TypeError):
            return Nichts
    wenn not isinstance(doc, str):
        return Nichts
    return cleandoc(doc)

def cleandoc(doc):
    """Clean up indentation from docstrings.

    Any whitespace that can be uniformly removed from the second line
    onwards is removed."""
    lines = doc.expandtabs().split('\n')

    # Find minimum indentation of any non-blank lines after first line.
    margin = sys.maxsize
    fuer line in lines[1:]:
        content = len(line.lstrip(' '))
        wenn content:
            indent = len(line) - content
            margin = min(margin, indent)
    # Remove indentation.
    wenn lines:
        lines[0] = lines[0].lstrip(' ')
    wenn margin < sys.maxsize:
        fuer i in range(1, len(lines)):
            lines[i] = lines[i][margin:]
    # Remove any trailing or leading blank lines.
    while lines and not lines[-1]:
        lines.pop()
    while lines and not lines[0]:
        lines.pop(0)
    return '\n'.join(lines)


def getfile(object):
    """Work out which source or compiled file an object was defined in."""
    wenn ismodule(object):
        wenn getattr(object, '__file__', Nichts):
            return object.__file__
        raise TypeError('{!r} is a built-in module'.format(object))
    wenn isclass(object):
        wenn hasattr(object, '__module__'):
            module = sys.modules.get(object.__module__)
            wenn getattr(module, '__file__', Nichts):
                return module.__file__
            wenn object.__module__ == '__main__':
                raise OSError('source code not available')
        raise TypeError('{!r} is a built-in class'.format(object))
    wenn ismethod(object):
        object = object.__func__
    wenn isfunction(object):
        object = object.__code__
    wenn istraceback(object):
        object = object.tb_frame
    wenn isframe(object):
        object = object.f_code
    wenn iscode(object):
        return object.co_filename
    raise TypeError('module, class, method, function, traceback, frame, or '
                    'code object was expected, got {}'.format(
                    type(object).__name__))

def getmodulename(path):
    """Return the module name fuer a given file, or Nichts."""
    fname = os.path.basename(path)
    # Check fuer paths that look like an actual module file
    suffixes = [(-len(suffix), suffix)
                    fuer suffix in importlib.machinery.all_suffixes()]
    suffixes.sort() # try longest suffixes first, in case they overlap
    fuer neglen, suffix in suffixes:
        wenn fname.endswith(suffix):
            return fname[:neglen]
    return Nichts

def getsourcefile(object):
    """Return the filename that can be used to locate an object's source.
    Return Nichts wenn no way can be identified to get the source.
    """
    filename = getfile(object)
    all_bytecode_suffixes = importlib.machinery.BYTECODE_SUFFIXES[:]
    wenn any(filename.endswith(s) fuer s in all_bytecode_suffixes):
        filename = (os.path.splitext(filename)[0] +
                    importlib.machinery.SOURCE_SUFFIXES[0])
    sowenn any(filename.endswith(s) fuer s in
                 importlib.machinery.EXTENSION_SUFFIXES):
        return Nichts
    sowenn filename.endswith(".fwork"):
        # Apple mobile framework markers are another type of non-source file
        return Nichts

    # return a filename found in the linecache even wenn it doesn't exist on disk
    wenn filename in linecache.cache:
        return filename
    wenn os.path.exists(filename):
        return filename
    # only return a non-existent filename wenn the module has a PEP 302 loader
    module = getmodule(object, filename)
    wenn getattr(module, '__loader__', Nichts) is not Nichts:
        return filename
    sowenn getattr(getattr(module, "__spec__", Nichts), "loader", Nichts) is not Nichts:
        return filename

def getabsfile(object, _filename=Nichts):
    """Return an absolute path to the source or compiled file fuer an object.

    The idea is fuer each object to have a unique origin, so this routine
    normalizes the result as much as possible."""
    wenn _filename is Nichts:
        _filename = getsourcefile(object) or getfile(object)
    return os.path.normcase(os.path.abspath(_filename))

modulesbyfile = {}
_filesbymodname = {}

def getmodule(object, _filename=Nichts):
    """Return the module an object was defined in, or Nichts wenn not found."""
    wenn ismodule(object):
        return object
    wenn hasattr(object, '__module__'):
        return sys.modules.get(object.__module__)

    # Try the filename to modulename cache
    wenn _filename is not Nichts and _filename in modulesbyfile:
        return sys.modules.get(modulesbyfile[_filename])
    # Try the cache again with the absolute file name
    try:
        file = getabsfile(object, _filename)
    except (TypeError, FileNotFoundError):
        return Nichts
    wenn file in modulesbyfile:
        return sys.modules.get(modulesbyfile[file])
    # Update the filename to module name cache and check yet again
    # Copy sys.modules in order to cope with changes while iterating
    fuer modname, module in sys.modules.copy().items():
        wenn ismodule(module) and hasattr(module, '__file__'):
            f = module.__file__
            wenn f == _filesbymodname.get(modname, Nichts):
                # Have already mapped this module, so skip it
                continue
            _filesbymodname[modname] = f
            f = getabsfile(module)
            # Always map to the name the module knows itself by
            modulesbyfile[f] = modulesbyfile[
                os.path.realpath(f)] = module.__name__
    wenn file in modulesbyfile:
        return sys.modules.get(modulesbyfile[file])
    # Check the main module
    main = sys.modules['__main__']
    wenn not hasattr(object, '__name__'):
        return Nichts
    wenn hasattr(main, object.__name__):
        mainobject = getattr(main, object.__name__)
        wenn mainobject is object:
            return main
    # Check builtins
    builtin = sys.modules['builtins']
    wenn hasattr(builtin, object.__name__):
        builtinobject = getattr(builtin, object.__name__)
        wenn builtinobject is object:
            return builtin


klasse ClassFoundException(Exception):
    pass


def findsource(object):
    """Return the entire source file and starting line number fuer an object.

    The argument may be a module, class, method, function, traceback, frame,
    or code object.  The source code is returned as a list of all the lines
    in the file and the line number indexes a line in that list.  An OSError
    is raised wenn the source code cannot be retrieved."""

    file = getsourcefile(object)
    wenn file:
        # Invalidate cache wenn needed.
        linecache.checkcache(file)
    sonst:
        file = getfile(object)
        # Allow filenames in form of "<something>" to pass through.
        # `doctest` monkeypatches `linecache` module to enable
        # inspection, so let `linecache.getlines` to be called.
        wenn (not (file.startswith('<') and file.endswith('>'))) or file.endswith('.fwork'):
            raise OSError('source code not available')

    module = getmodule(object, file)
    wenn module:
        lines = linecache.getlines(file, module.__dict__)
        wenn not lines and file.startswith('<') and hasattr(object, "__code__"):
            lines = linecache._getlines_from_code(object.__code__)
    sonst:
        lines = linecache.getlines(file)
    wenn not lines:
        raise OSError('could not get source code')

    wenn ismodule(object):
        return lines, 0

    wenn isclass(object):
        try:
            lnum = vars(object)['__firstlineno__'] - 1
        except (TypeError, KeyError):
            raise OSError('source code not available')
        wenn lnum >= len(lines):
            raise OSError('lineno is out of bounds')
        return lines, lnum

    wenn ismethod(object):
        object = object.__func__
    wenn isfunction(object):
        object = object.__code__
    wenn istraceback(object):
        object = object.tb_frame
    wenn isframe(object):
        object = object.f_code
    wenn iscode(object):
        wenn not hasattr(object, 'co_firstlineno'):
            raise OSError('could not find function definition')
        lnum = object.co_firstlineno - 1
        wenn lnum >= len(lines):
            raise OSError('lineno is out of bounds')
        return lines, lnum
    raise OSError('could not find code object')

def getcomments(object):
    """Get lines of comments immediately preceding an object's source code.

    Returns Nichts when source can't be found.
    """
    try:
        lines, lnum = findsource(object)
    except (OSError, TypeError):
        return Nichts

    wenn ismodule(object):
        # Look fuer a comment block at the top of the file.
        start = 0
        wenn lines and lines[0][:2] == '#!': start = 1
        while start < len(lines) and lines[start].strip() in ('', '#'):
            start = start + 1
        wenn start < len(lines) and lines[start][:1] == '#':
            comments = []
            end = start
            while end < len(lines) and lines[end][:1] == '#':
                comments.append(lines[end].expandtabs())
                end = end + 1
            return ''.join(comments)

    # Look fuer a preceding block of comments at the same indentation.
    sowenn lnum > 0:
        indent = indentsize(lines[lnum])
        end = lnum - 1
        wenn end >= 0 and lines[end].lstrip()[:1] == '#' and \
            indentsize(lines[end]) == indent:
            comments = [lines[end].expandtabs().lstrip()]
            wenn end > 0:
                end = end - 1
                comment = lines[end].expandtabs().lstrip()
                while comment[:1] == '#' and indentsize(lines[end]) == indent:
                    comments[:0] = [comment]
                    end = end - 1
                    wenn end < 0: break
                    comment = lines[end].expandtabs().lstrip()
            while comments and comments[0].strip() == '#':
                comments[:1] = []
            while comments and comments[-1].strip() == '#':
                comments[-1:] = []
            return ''.join(comments)

klasse EndOfBlock(Exception): pass

klasse BlockFinder:
    """Provide a tokeneater() method to detect the end of a code block."""
    def __init__(self):
        self.indent = 0
        self.singleline = Falsch
        self.started = Falsch
        self.passline = Falsch
        self.indecorator = Falsch
        self.last = 1
        self.body_col0 = Nichts

    def tokeneater(self, type, token, srowcol, erowcol, line):
        wenn not self.started and not self.indecorator:
            wenn type == tokenize.INDENT or token == "async":
                pass
            # skip any decorators
            sowenn token == "@":
                self.indecorator = Wahr
            sonst:
                # For "def" and "class" scan to the end of the block.
                # For "lambda" and generator expression scan to
                # the end of the logical line.
                self.singleline = token not in ("def", "class")
                self.started = Wahr
            self.passline = Wahr    # skip to the end of the line
        sowenn type == tokenize.NEWLINE:
            self.passline = Falsch   # stop skipping when a NEWLINE is seen
            self.last = srowcol[0]
            wenn self.singleline:
                raise EndOfBlock
            # hitting a NEWLINE when in a decorator without args
            # ends the decorator
            wenn self.indecorator:
                self.indecorator = Falsch
        sowenn self.passline:
            pass
        sowenn type == tokenize.INDENT:
            wenn self.body_col0 is Nichts and self.started:
                self.body_col0 = erowcol[1]
            self.indent = self.indent + 1
            self.passline = Wahr
        sowenn type == tokenize.DEDENT:
            self.indent = self.indent - 1
            # the end of matching indent/dedent pairs end a block
            # (note that this only works fuer "def"/"class" blocks,
            #  not e.g. fuer "if: sonst:" or "try: finally:" blocks)
            wenn self.indent <= 0:
                raise EndOfBlock
        sowenn type == tokenize.COMMENT:
            wenn self.body_col0 is not Nichts and srowcol[1] >= self.body_col0:
                # Include comments wenn indented at least as much as the block
                self.last = srowcol[0]
        sowenn self.indent == 0 and type not in (tokenize.COMMENT, tokenize.NL):
            # any other token on the same indentation level end the previous
            # block as well, except the pseudo-tokens COMMENT and NL.
            raise EndOfBlock

def getblock(lines):
    """Extract the block of code at the top of the given list of lines."""
    blockfinder = BlockFinder()
    try:
        tokens = tokenize.generate_tokens(iter(lines).__next__)
        fuer _token in tokens:
            blockfinder.tokeneater(*_token)
    except (EndOfBlock, IndentationError):
        pass
    except SyntaxError as e:
        wenn "unmatched" not in e.msg:
            raise e from Nichts
        _, *_token_info = _token
        try:
            blockfinder.tokeneater(tokenize.NEWLINE, *_token_info)
        except (EndOfBlock, IndentationError):
            pass
    return lines[:blockfinder.last]

def getsourcelines(object):
    """Return a list of source lines and starting line number fuer an object.

    The argument may be a module, class, method, function, traceback, frame,
    or code object.  The source code is returned as a list of the lines
    corresponding to the object and the line number indicates where in the
    original source file the first line of code was found.  An OSError is
    raised wenn the source code cannot be retrieved."""
    object = unwrap(object)
    lines, lnum = findsource(object)

    wenn istraceback(object):
        object = object.tb_frame

    # fuer module or frame that corresponds to module, return all source lines
    wenn (ismodule(object) or
        (isframe(object) and object.f_code.co_name == "<module>")):
        return lines, 0
    sonst:
        return getblock(lines[lnum:]), lnum + 1

def getsource(object):
    """Return the text of the source code fuer an object.

    The argument may be a module, class, method, function, traceback, frame,
    or code object.  The source code is returned as a single string.  An
    OSError is raised wenn the source code cannot be retrieved."""
    lines, lnum = getsourcelines(object)
    return ''.join(lines)

# --------------------------------------------------- klasse tree extraction
def walktree(classes, children, parent):
    """Recursive helper function fuer getclasstree()."""
    results = []
    classes.sort(key=attrgetter('__module__', '__name__'))
    fuer c in classes:
        results.append((c, c.__bases__))
        wenn c in children:
            results.append(walktree(children[c], children, c))
    return results

def getclasstree(classes, unique=Falsch):
    """Arrange the given list of classes into a hierarchy of nested lists.

    Where a nested list appears, it contains classes derived from the class
    whose entry immediately precedes the list.  Each entry is a 2-tuple
    containing a klasse and a tuple of its base classes.  If the 'unique'
    argument is true, exactly one entry appears in the returned structure
    fuer each klasse in the given list.  Otherwise, classes using multiple
    inheritance and their descendants will appear multiple times."""
    children = {}
    roots = []
    fuer c in classes:
        wenn c.__bases__:
            fuer parent in c.__bases__:
                wenn parent not in children:
                    children[parent] = []
                wenn c not in children[parent]:
                    children[parent].append(c)
                wenn unique and parent in classes: break
        sowenn c not in roots:
            roots.append(c)
    fuer parent in children:
        wenn parent not in classes:
            roots.append(parent)
    return walktree(roots, children, Nichts)

# ------------------------------------------------ argument list extraction
Arguments = namedtuple('Arguments', 'args, varargs, varkw')

def getargs(co):
    """Get information about the arguments accepted by a code object.

    Three things are returned: (args, varargs, varkw), where
    'args' is the list of argument names. Keyword-only arguments are
    appended. 'varargs' and 'varkw' are the names of the * and **
    arguments or Nichts."""
    wenn not iscode(co):
        raise TypeError('{!r} is not a code object'.format(co))

    names = co.co_varnames
    nargs = co.co_argcount
    nkwargs = co.co_kwonlyargcount
    args = list(names[:nargs])
    kwonlyargs = list(names[nargs:nargs+nkwargs])

    nargs += nkwargs
    varargs = Nichts
    wenn co.co_flags & CO_VARARGS:
        varargs = co.co_varnames[nargs]
        nargs = nargs + 1
    varkw = Nichts
    wenn co.co_flags & CO_VARKEYWORDS:
        varkw = co.co_varnames[nargs]
    return Arguments(args + kwonlyargs, varargs, varkw)


FullArgSpec = namedtuple('FullArgSpec',
    'args, varargs, varkw, defaults, kwonlyargs, kwonlydefaults, annotations')

def getfullargspec(func):
    """Get the names and default values of a callable object's parameters.

    A tuple of seven things is returned:
    (args, varargs, varkw, defaults, kwonlyargs, kwonlydefaults, annotations).
    'args' is a list of the parameter names.
    'varargs' and 'varkw' are the names of the * and ** parameters or Nichts.
    'defaults' is an n-tuple of the default values of the last n parameters.
    'kwonlyargs' is a list of keyword-only parameter names.
    'kwonlydefaults' is a dictionary mapping names from kwonlyargs to defaults.
    'annotations' is a dictionary mapping parameter names to annotations.

    Notable differences from inspect.signature():
      - the "self" parameter is always reported, even fuer bound methods
      - wrapper chains defined by __wrapped__ *not* unwrapped automatically
    """
    try:
        # Re: `skip_bound_arg=Falsch`
        #
        # There is a notable difference in behaviour between getfullargspec
        # and Signature: the former always returns 'self' parameter fuer bound
        # methods, whereas the Signature always shows the actual calling
        # signature of the passed object.
        #
        # To simulate this behaviour, we "unbind" bound methods, to trick
        # inspect.signature to always return their first parameter ("self",
        # usually)

        # Re: `follow_wrapper_chains=Falsch`
        #
        # getfullargspec() historically ignored __wrapped__ attributes,
        # so we ensure that remains the case in 3.3+

        sig = _signature_from_callable(func,
                                       follow_wrapper_chains=Falsch,
                                       skip_bound_arg=Falsch,
                                       sigcls=Signature,
                                       eval_str=Falsch)
    except Exception as ex:
        # Most of the times 'signature' will raise ValueError.
        # But, it can also raise AttributeError, and, maybe something
        # else. So to be fully backwards compatible, we catch all
        # possible exceptions here, and reraise a TypeError.
        raise TypeError('unsupported callable') from ex

    args = []
    varargs = Nichts
    varkw = Nichts
    posonlyargs = []
    kwonlyargs = []
    annotations = {}
    defaults = ()
    kwdefaults = {}

    wenn sig.return_annotation is not sig.empty:
        annotations['return'] = sig.return_annotation

    fuer param in sig.parameters.values():
        kind = param.kind
        name = param.name

        wenn kind is _POSITIONAL_ONLY:
            posonlyargs.append(name)
            wenn param.default is not param.empty:
                defaults += (param.default,)
        sowenn kind is _POSITIONAL_OR_KEYWORD:
            args.append(name)
            wenn param.default is not param.empty:
                defaults += (param.default,)
        sowenn kind is _VAR_POSITIONAL:
            varargs = name
        sowenn kind is _KEYWORD_ONLY:
            kwonlyargs.append(name)
            wenn param.default is not param.empty:
                kwdefaults[name] = param.default
        sowenn kind is _VAR_KEYWORD:
            varkw = name

        wenn param.annotation is not param.empty:
            annotations[name] = param.annotation

    wenn not kwdefaults:
        # compatibility with 'func.__kwdefaults__'
        kwdefaults = Nichts

    wenn not defaults:
        # compatibility with 'func.__defaults__'
        defaults = Nichts

    return FullArgSpec(posonlyargs + args, varargs, varkw, defaults,
                       kwonlyargs, kwdefaults, annotations)


ArgInfo = namedtuple('ArgInfo', 'args varargs keywords locals')

def getargvalues(frame):
    """Get information about arguments passed into a particular frame.

    A tuple of four things is returned: (args, varargs, varkw, locals).
    'args' is a list of the argument names.
    'varargs' and 'varkw' are the names of the * and ** arguments or Nichts.
    'locals' is the locals dictionary of the given frame."""
    args, varargs, varkw = getargs(frame.f_code)
    return ArgInfo(args, varargs, varkw, frame.f_locals)

def formatannotation(annotation, base_module=Nichts, *, quote_annotation_strings=Wahr):
    wenn not quote_annotation_strings and isinstance(annotation, str):
        return annotation
    wenn getattr(annotation, '__module__', Nichts) == 'typing':
        def repl(match):
            text = match.group()
            return text.removeprefix('typing.')
        return re.sub(r'[\w\.]+', repl, repr(annotation))
    wenn isinstance(annotation, types.GenericAlias):
        return str(annotation)
    wenn isinstance(annotation, type):
        wenn annotation.__module__ in ('builtins', base_module):
            return annotation.__qualname__
        return annotation.__module__+'.'+annotation.__qualname__
    wenn isinstance(annotation, ForwardRef):
        return annotation.__forward_arg__
    return repr(annotation)

def formatannotationrelativeto(object):
    module = getattr(object, '__module__', Nichts)
    def _formatannotation(annotation):
        return formatannotation(annotation, module)
    return _formatannotation


def formatargvalues(args, varargs, varkw, locals,
                    formatarg=str,
                    formatvarargs=lambda name: '*' + name,
                    formatvarkw=lambda name: '**' + name,
                    formatvalue=lambda value: '=' + repr(value)):
    """Format an argument spec from the 4 values returned by getargvalues.

    The first four arguments are (args, varargs, varkw, locals).  The
    next four arguments are the corresponding optional formatting functions
    that are called to turn names and values into strings.  The ninth
    argument is an optional function to format the sequence of arguments."""
    def convert(name, locals=locals,
                formatarg=formatarg, formatvalue=formatvalue):
        return formatarg(name) + formatvalue(locals[name])
    specs = []
    fuer i in range(len(args)):
        specs.append(convert(args[i]))
    wenn varargs:
        specs.append(formatvarargs(varargs) + formatvalue(locals[varargs]))
    wenn varkw:
        specs.append(formatvarkw(varkw) + formatvalue(locals[varkw]))
    return '(' + ', '.join(specs) + ')'

def _missing_arguments(f_name, argnames, pos, values):
    names = [repr(name) fuer name in argnames wenn name not in values]
    missing = len(names)
    wenn missing == 1:
        s = names[0]
    sowenn missing == 2:
        s = "{} and {}".format(*names)
    sonst:
        tail = ", {} and {}".format(*names[-2:])
        del names[-2:]
        s = ", ".join(names) + tail
    raise TypeError("%s() missing %i required %s argument%s: %s" %
                    (f_name, missing,
                      "positional" wenn pos sonst "keyword-only",
                      "" wenn missing == 1 sonst "s", s))

def _too_many(f_name, args, kwonly, varargs, defcount, given, values):
    atleast = len(args) - defcount
    kwonly_given = len([arg fuer arg in kwonly wenn arg in values])
    wenn varargs:
        plural = atleast != 1
        sig = "at least %d" % (atleast,)
    sowenn defcount:
        plural = Wahr
        sig = "from %d to %d" % (atleast, len(args))
    sonst:
        plural = len(args) != 1
        sig = str(len(args))
    kwonly_sig = ""
    wenn kwonly_given:
        msg = " positional argument%s (and %d keyword-only argument%s)"
        kwonly_sig = (msg % ("s" wenn given != 1 sonst "", kwonly_given,
                             "s" wenn kwonly_given != 1 sonst ""))
    raise TypeError("%s() takes %s positional argument%s but %d%s %s given" %
            (f_name, sig, "s" wenn plural sonst "", given, kwonly_sig,
             "was" wenn given == 1 and not kwonly_given sonst "were"))

def getcallargs(func, /, *positional, **named):
    """Get the mapping of arguments to values.

    A dict is returned, with keys the function argument names (including the
    names of the * and ** arguments, wenn any), and values the respective bound
    values from 'positional' and 'named'."""
    spec = getfullargspec(func)
    args, varargs, varkw, defaults, kwonlyargs, kwonlydefaults, ann = spec
    f_name = func.__name__
    arg2value = {}


    wenn ismethod(func) and func.__self__ is not Nichts:
        # implicit 'self' (or 'cls' fuer classmethods) argument
        positional = (func.__self__,) + positional
    num_pos = len(positional)
    num_args = len(args)
    num_defaults = len(defaults) wenn defaults sonst 0

    n = min(num_pos, num_args)
    fuer i in range(n):
        arg2value[args[i]] = positional[i]
    wenn varargs:
        arg2value[varargs] = tuple(positional[n:])
    possible_kwargs = set(args + kwonlyargs)
    wenn varkw:
        arg2value[varkw] = {}
    fuer kw, value in named.items():
        wenn kw not in possible_kwargs:
            wenn not varkw:
                raise TypeError("%s() got an unexpected keyword argument %r" %
                                (f_name, kw))
            arg2value[varkw][kw] = value
            continue
        wenn kw in arg2value:
            raise TypeError("%s() got multiple values fuer argument %r" %
                            (f_name, kw))
        arg2value[kw] = value
    wenn num_pos > num_args and not varargs:
        _too_many(f_name, args, kwonlyargs, varargs, num_defaults,
                   num_pos, arg2value)
    wenn num_pos < num_args:
        req = args[:num_args - num_defaults]
        fuer arg in req:
            wenn arg not in arg2value:
                _missing_arguments(f_name, req, Wahr, arg2value)
        fuer i, arg in enumerate(args[num_args - num_defaults:]):
            wenn arg not in arg2value:
                arg2value[arg] = defaults[i]
    missing = 0
    fuer kwarg in kwonlyargs:
        wenn kwarg not in arg2value:
            wenn kwonlydefaults and kwarg in kwonlydefaults:
                arg2value[kwarg] = kwonlydefaults[kwarg]
            sonst:
                missing += 1
    wenn missing:
        _missing_arguments(f_name, kwonlyargs, Falsch, arg2value)
    return arg2value

ClosureVars = namedtuple('ClosureVars', 'nonlocals globals builtins unbound')

def getclosurevars(func):
    """
    Get the mapping of free variables to their current values.

    Returns a named tuple of dicts mapping the current nonlocal, global
    and builtin references as seen by the body of the function. A final
    set of unbound names that could not be resolved is also provided.
    """

    wenn ismethod(func):
        func = func.__func__

    wenn not isfunction(func):
        raise TypeError("{!r} is not a Python function".format(func))

    code = func.__code__
    # Nonlocal references are named in co_freevars and resolved
    # by looking them up in __closure__ by positional index
    wenn func.__closure__ is Nichts:
        nonlocal_vars = {}
    sonst:
        nonlocal_vars = {
            var : cell.cell_contents
            fuer var, cell in zip(code.co_freevars, func.__closure__)
       }

    # Global and builtin references are named in co_names and resolved
    # by looking them up in __globals__ or __builtins__
    global_ns = func.__globals__
    builtin_ns = global_ns.get("__builtins__", builtins.__dict__)
    wenn ismodule(builtin_ns):
        builtin_ns = builtin_ns.__dict__
    global_vars = {}
    builtin_vars = {}
    unbound_names = set()
    global_names = set()
    fuer instruction in dis.get_instructions(code):
        opname = instruction.opname
        name = instruction.argval
        wenn opname == "LOAD_ATTR":
            unbound_names.add(name)
        sowenn opname == "LOAD_GLOBAL":
            global_names.add(name)
    fuer name in global_names:
        try:
            global_vars[name] = global_ns[name]
        except KeyError:
            try:
                builtin_vars[name] = builtin_ns[name]
            except KeyError:
                unbound_names.add(name)

    return ClosureVars(nonlocal_vars, global_vars,
                       builtin_vars, unbound_names)

# -------------------------------------------------- stack frame extraction

_Traceback = namedtuple('_Traceback', 'filename lineno function code_context index')

klasse Traceback(_Traceback):
    def __new__(cls, filename, lineno, function, code_context, index, *, positions=Nichts):
        instance = super().__new__(cls, filename, lineno, function, code_context, index)
        instance.positions = positions
        return instance

    def __repr__(self):
        return ('Traceback(filename={!r}, lineno={!r}, function={!r}, '
               'code_context={!r}, index={!r}, positions={!r})'.format(
                self.filename, self.lineno, self.function, self.code_context,
                self.index, self.positions))

def _get_code_position_from_tb(tb):
    code, instruction_index = tb.tb_frame.f_code, tb.tb_lasti
    return _get_code_position(code, instruction_index)

def _get_code_position(code, instruction_index):
    wenn instruction_index < 0:
        return (Nichts, Nichts, Nichts, Nichts)
    positions_gen = code.co_positions()
    # The nth entry in code.co_positions() corresponds to instruction (2*n)th since Python 3.10+
    return next(itertools.islice(positions_gen, instruction_index // 2, Nichts))

def getframeinfo(frame, context=1):
    """Get information about a frame or traceback object.

    A tuple of five things is returned: the filename, the line number of
    the current line, the function name, a list of lines of context from
    the source code, and the index of the current line within that list.
    The optional second argument specifies the number of lines of context
    to return, which are centered around the current line."""
    wenn istraceback(frame):
        positions = _get_code_position_from_tb(frame)
        lineno = frame.tb_lineno
        frame = frame.tb_frame
    sonst:
        lineno = frame.f_lineno
        positions = _get_code_position(frame.f_code, frame.f_lasti)

    wenn positions[0] is Nichts:
        frame, *positions = (frame, lineno, *positions[1:])
    sonst:
        frame, *positions = (frame, *positions)

    lineno = positions[0]

    wenn not isframe(frame):
        raise TypeError('{!r} is not a frame or traceback object'.format(frame))

    filename = getsourcefile(frame) or getfile(frame)
    wenn context > 0:
        start = lineno - 1 - context//2
        try:
            lines, lnum = findsource(frame)
        except OSError:
            lines = index = Nichts
        sonst:
            start = max(0, min(start, len(lines) - context))
            lines = lines[start:start+context]
            index = lineno - 1 - start
    sonst:
        lines = index = Nichts

    return Traceback(filename, lineno, frame.f_code.co_name, lines,
                     index, positions=dis.Positions(*positions))

def getlineno(frame):
    """Get the line number from a frame object, allowing fuer optimization."""
    # FrameType.f_lineno is now a descriptor that grovels co_lnotab
    return frame.f_lineno

_FrameInfo = namedtuple('_FrameInfo', ('frame',) + Traceback._fields)
klasse FrameInfo(_FrameInfo):
    def __new__(cls, frame, filename, lineno, function, code_context, index, *, positions=Nichts):
        instance = super().__new__(cls, frame, filename, lineno, function, code_context, index)
        instance.positions = positions
        return instance

    def __repr__(self):
        return ('FrameInfo(frame={!r}, filename={!r}, lineno={!r}, function={!r}, '
               'code_context={!r}, index={!r}, positions={!r})'.format(
                self.frame, self.filename, self.lineno, self.function,
                self.code_context, self.index, self.positions))

def getouterframes(frame, context=1):
    """Get a list of records fuer a frame and all higher (calling) frames.

    Each record contains a frame object, filename, line number, function
    name, a list of lines of context, and index within the context."""
    framelist = []
    while frame:
        traceback_info = getframeinfo(frame, context)
        frameinfo = (frame,) + traceback_info
        framelist.append(FrameInfo(*frameinfo, positions=traceback_info.positions))
        frame = frame.f_back
    return framelist

def getinnerframes(tb, context=1):
    """Get a list of records fuer a traceback's frame and all lower frames.

    Each record contains a frame object, filename, line number, function
    name, a list of lines of context, and index within the context."""
    framelist = []
    while tb:
        traceback_info = getframeinfo(tb, context)
        frameinfo = (tb.tb_frame,) + traceback_info
        framelist.append(FrameInfo(*frameinfo, positions=traceback_info.positions))
        tb = tb.tb_next
    return framelist

def currentframe():
    """Return the frame of the caller or Nichts wenn this is not possible."""
    return sys._getframe(1) wenn hasattr(sys, "_getframe") sonst Nichts

def stack(context=1):
    """Return a list of records fuer the stack above the caller's frame."""
    return getouterframes(sys._getframe(1), context)

def trace(context=1):
    """Return a list of records fuer the stack below the current exception."""
    exc = sys.exception()
    tb = Nichts wenn exc is Nichts sonst exc.__traceback__
    return getinnerframes(tb, context)


# ------------------------------------------------ static version of getattr

_sentinel = object()
_static_getmro = type.__dict__['__mro__'].__get__
_get_dunder_dict_of_class = type.__dict__["__dict__"].__get__


def _check_instance(obj, attr):
    instance_dict = {}
    try:
        instance_dict = object.__getattribute__(obj, "__dict__")
    except AttributeError:
        pass
    return dict.get(instance_dict, attr, _sentinel)


def _check_class(klass, attr):
    fuer entry in _static_getmro(klass):
        wenn _shadowed_dict(type(entry)) is _sentinel and attr in entry.__dict__:
            return entry.__dict__[attr]
    return _sentinel


@functools.lru_cache()
def _shadowed_dict_from_weakref_mro_tuple(*weakref_mro):
    fuer weakref_entry in weakref_mro:
        # Normally we'd have to check whether the result of weakref_entry()
        # is Nichts here, in case the object the weakref is pointing to has died.
        # In this specific case, however, we know that the only caller of this
        # function is `_shadowed_dict()`, and that therefore this weakref is
        # guaranteed to point to an object that is still alive.
        entry = weakref_entry()
        dunder_dict = _get_dunder_dict_of_class(entry)
        wenn '__dict__' in dunder_dict:
            class_dict = dunder_dict['__dict__']
            wenn not (type(class_dict) is types.GetSetDescriptorType and
                    class_dict.__name__ == "__dict__" and
                    (class_dict.__objclass__ is object or
                     class_dict.__objclass__ is entry)):
                return class_dict
    return _sentinel


def _shadowed_dict(klass):
    # gh-118013: the inner function here is decorated with lru_cache for
    # performance reasons, *but* make sure not to pass strong references
    # to the items in the mro. Doing so can lead to unexpected memory
    # consumption in cases where classes are dynamically created and
    # destroyed, and the dynamically created classes happen to be the only
    # objects that hold strong references to other objects that take up a
    # significant amount of memory.
    return _shadowed_dict_from_weakref_mro_tuple(
        *[make_weakref(entry) fuer entry in _static_getmro(klass)]
    )


def getattr_static(obj, attr, default=_sentinel):
    """Retrieve attributes without triggering dynamic lookup via the
       descriptor protocol,  __getattr__ or __getattribute__.

       Note: this function may not be able to retrieve all attributes
       that getattr can fetch (like dynamically created attributes)
       and may find attributes that getattr can't (like descriptors
       that raise AttributeError). It can also return descriptor objects
       instead of instance members in some cases. See the
       documentation fuer details.
    """
    instance_result = _sentinel

    objtype = type(obj)
    wenn type not in _static_getmro(objtype):
        klass = objtype
        dict_attr = _shadowed_dict(klass)
        wenn (dict_attr is _sentinel or
            type(dict_attr) is types.MemberDescriptorType):
            instance_result = _check_instance(obj, attr)
    sonst:
        klass = obj

    klass_result = _check_class(klass, attr)

    wenn instance_result is not _sentinel and klass_result is not _sentinel:
        wenn _check_class(type(klass_result), "__get__") is not _sentinel and (
            _check_class(type(klass_result), "__set__") is not _sentinel
            or _check_class(type(klass_result), "__delete__") is not _sentinel
        ):
            return klass_result

    wenn instance_result is not _sentinel:
        return instance_result
    wenn klass_result is not _sentinel:
        return klass_result

    wenn obj is klass:
        # fuer types we check the metaclass too
        fuer entry in _static_getmro(type(klass)):
            wenn (
                _shadowed_dict(type(entry)) is _sentinel
                and attr in entry.__dict__
            ):
                return entry.__dict__[attr]
    wenn default is not _sentinel:
        return default
    raise AttributeError(attr)


# ------------------------------------------------ generator introspection

GEN_CREATED = 'GEN_CREATED'
GEN_RUNNING = 'GEN_RUNNING'
GEN_SUSPENDED = 'GEN_SUSPENDED'
GEN_CLOSED = 'GEN_CLOSED'

def getgeneratorstate(generator):
    """Get current state of a generator-iterator.

    Possible states are:
      GEN_CREATED: Waiting to start execution.
      GEN_RUNNING: Currently being executed by the interpreter.
      GEN_SUSPENDED: Currently suspended at a yield expression.
      GEN_CLOSED: Execution has completed.
    """
    wenn generator.gi_running:
        return GEN_RUNNING
    wenn generator.gi_suspended:
        return GEN_SUSPENDED
    wenn generator.gi_frame is Nichts:
        return GEN_CLOSED
    return GEN_CREATED


def getgeneratorlocals(generator):
    """
    Get the mapping of generator local variables to their current values.

    A dict is returned, with the keys the local variable names and values the
    bound values."""

    wenn not isgenerator(generator):
        raise TypeError("{!r} is not a Python generator".format(generator))

    frame = getattr(generator, "gi_frame", Nichts)
    wenn frame is not Nichts:
        return generator.gi_frame.f_locals
    sonst:
        return {}


# ------------------------------------------------ coroutine introspection

CORO_CREATED = 'CORO_CREATED'
CORO_RUNNING = 'CORO_RUNNING'
CORO_SUSPENDED = 'CORO_SUSPENDED'
CORO_CLOSED = 'CORO_CLOSED'

def getcoroutinestate(coroutine):
    """Get current state of a coroutine object.

    Possible states are:
      CORO_CREATED: Waiting to start execution.
      CORO_RUNNING: Currently being executed by the interpreter.
      CORO_SUSPENDED: Currently suspended at an await expression.
      CORO_CLOSED: Execution has completed.
    """
    wenn coroutine.cr_running:
        return CORO_RUNNING
    wenn coroutine.cr_suspended:
        return CORO_SUSPENDED
    wenn coroutine.cr_frame is Nichts:
        return CORO_CLOSED
    return CORO_CREATED


def getcoroutinelocals(coroutine):
    """
    Get the mapping of coroutine local variables to their current values.

    A dict is returned, with the keys the local variable names and values the
    bound values."""
    frame = getattr(coroutine, "cr_frame", Nichts)
    wenn frame is not Nichts:
        return frame.f_locals
    sonst:
        return {}


# ----------------------------------- asynchronous generator introspection

AGEN_CREATED = 'AGEN_CREATED'
AGEN_RUNNING = 'AGEN_RUNNING'
AGEN_SUSPENDED = 'AGEN_SUSPENDED'
AGEN_CLOSED = 'AGEN_CLOSED'


def getasyncgenstate(agen):
    """Get current state of an asynchronous generator object.

    Possible states are:
      AGEN_CREATED: Waiting to start execution.
      AGEN_RUNNING: Currently being executed by the interpreter.
      AGEN_SUSPENDED: Currently suspended at a yield expression.
      AGEN_CLOSED: Execution has completed.
    """
    wenn agen.ag_running:
        return AGEN_RUNNING
    wenn agen.ag_suspended:
        return AGEN_SUSPENDED
    wenn agen.ag_frame is Nichts:
        return AGEN_CLOSED
    return AGEN_CREATED


def getasyncgenlocals(agen):
    """
    Get the mapping of asynchronous generator local variables to their current
    values.

    A dict is returned, with the keys the local variable names and values the
    bound values."""

    wenn not isasyncgen(agen):
        raise TypeError(f"{agen!r} is not a Python async generator")

    frame = getattr(agen, "ag_frame", Nichts)
    wenn frame is not Nichts:
        return agen.ag_frame.f_locals
    sonst:
        return {}


###############################################################################
### Function Signature Object (PEP 362)
###############################################################################


_NonUserDefinedCallables = (types.WrapperDescriptorType,
                            types.MethodWrapperType,
                            types.ClassMethodDescriptorType,
                            types.BuiltinFunctionType)


def _signature_get_user_defined_method(cls, method_name, *, follow_wrapper_chains=Wahr):
    """Private helper. Checks wenn ``cls`` has an attribute
    named ``method_name`` and returns it only wenn it is a
    pure python function.
    """
    wenn method_name == '__new__':
        meth = getattr(cls, method_name, Nichts)
    sonst:
        meth = getattr_static(cls, method_name, Nichts)
    wenn meth is Nichts:
        return Nichts

    wenn follow_wrapper_chains:
        meth = unwrap(meth, stop=(lambda m: hasattr(m, "__signature__")
                                  or _signature_is_builtin(m)))
    wenn isinstance(meth, _NonUserDefinedCallables):
        # Once '__signature__' will be added to 'C'-level
        # callables, this check won't be necessary
        return Nichts
    wenn method_name != '__new__':
        meth = _descriptor_get(meth, cls)
        wenn follow_wrapper_chains:
            meth = unwrap(meth, stop=lambda m: hasattr(m, "__signature__"))
    return meth


def _signature_get_partial(wrapped_sig, partial, extra_args=()):
    """Private helper to calculate how 'wrapped_sig' signature will
    look like after applying a 'functools.partial' object (or alike)
    on it.
    """

    old_params = wrapped_sig.parameters
    new_params = OrderedDict(old_params.items())

    partial_args = partial.args or ()
    partial_keywords = partial.keywords or {}

    wenn extra_args:
        partial_args = extra_args + partial_args

    try:
        ba = wrapped_sig.bind_partial(*partial_args, **partial_keywords)
    except TypeError as ex:
        msg = 'partial object {!r} has incorrect arguments'.format(partial)
        raise ValueError(msg) from ex


    transform_to_kwonly = Falsch
    fuer param_name, param in old_params.items():
        try:
            arg_value = ba.arguments[param_name]
        except KeyError:
            pass
        sonst:
            wenn param.kind is _POSITIONAL_ONLY:
                # If positional-only parameter is bound by partial,
                # it effectively disappears from the signature
                # However, wenn it is a Placeholder it is not removed
                # And also looses default value
                wenn arg_value is functools.Placeholder:
                    new_params[param_name] = param.replace(default=_empty)
                sonst:
                    new_params.pop(param_name)
                continue

            wenn param.kind is _POSITIONAL_OR_KEYWORD:
                wenn param_name in partial_keywords:
                    # This means that this parameter, and all parameters
                    # after it should be keyword-only (and var-positional
                    # should be removed). Here's why. Consider the following
                    # function:
                    #     foo(a, b, *args, c):
                    #         pass
                    #
                    # "partial(foo, a='spam')" will have the following
                    # signature: "(*, a='spam', b, c)". Because attempting
                    # to call that partial with "(10, 20)" arguments will
                    # raise a TypeError, saying that "a" argument received
                    # multiple values.
                    transform_to_kwonly = Wahr
                    # Set the new default value
                    new_params[param_name] = param.replace(default=arg_value)
                sonst:
                    # was passed as a positional argument
                    # Do not pop wenn it is a Placeholder
                    #   also change kind to positional only
                    #   and remove default
                    wenn arg_value is functools.Placeholder:
                        new_param = param.replace(
                            kind=_POSITIONAL_ONLY,
                            default=_empty
                        )
                        new_params[param_name] = new_param
                    sonst:
                        new_params.pop(param_name)
                    continue

            wenn param.kind is _KEYWORD_ONLY:
                # Set the new default value
                new_params[param_name] = param.replace(default=arg_value)

        wenn transform_to_kwonly:
            assert param.kind is not _POSITIONAL_ONLY

            wenn param.kind is _POSITIONAL_OR_KEYWORD:
                new_param = new_params[param_name].replace(kind=_KEYWORD_ONLY)
                new_params[param_name] = new_param
                new_params.move_to_end(param_name)
            sowenn param.kind in (_KEYWORD_ONLY, _VAR_KEYWORD):
                new_params.move_to_end(param_name)
            sowenn param.kind is _VAR_POSITIONAL:
                new_params.pop(param.name)

    return wrapped_sig.replace(parameters=new_params.values())


def _signature_bound_method(sig):
    """Private helper to transform signatures fuer unbound
    functions to bound methods.
    """

    params = tuple(sig.parameters.values())

    wenn not params or params[0].kind in (_VAR_KEYWORD, _KEYWORD_ONLY):
        raise ValueError('invalid method signature')

    kind = params[0].kind
    wenn kind in (_POSITIONAL_OR_KEYWORD, _POSITIONAL_ONLY):
        # Drop first parameter:
        # '(p1, p2[, ...])' -> '(p2[, ...])'
        params = params[1:]
    sonst:
        wenn kind is not _VAR_POSITIONAL:
            # Unless we add a new parameter type we never
            # get here
            raise ValueError('invalid argument type')
        # It's a var-positional parameter.
        # Do nothing. '(*args[, ...])' -> '(*args[, ...])'

    return sig.replace(parameters=params)


def _signature_is_builtin(obj):
    """Private helper to test wenn `obj` is a callable that might
    support Argument Clinic's __text_signature__ protocol.
    """
    return (isbuiltin(obj) or
            ismethoddescriptor(obj) or
            isinstance(obj, _NonUserDefinedCallables) or
            # Can't test 'isinstance(type)' here, as it would
            # also be Wahr fuer regular python classes.
            # Can't use the `in` operator here, as it would
            # invoke the custom __eq__ method.
            obj is type or obj is object)


def _signature_is_functionlike(obj):
    """Private helper to test wenn `obj` is a duck type of FunctionType.
    A good example of such objects are functions compiled with
    Cython, which have all attributes that a pure Python function
    would have, but have their code statically compiled.
    """

    wenn not callable(obj) or isclass(obj):
        # All function-like objects are obviously callables,
        # and not classes.
        return Falsch

    name = getattr(obj, '__name__', Nichts)
    code = getattr(obj, '__code__', Nichts)
    defaults = getattr(obj, '__defaults__', _void) # Important to use _void ...
    kwdefaults = getattr(obj, '__kwdefaults__', _void) # ... and not Nichts here

    return (isinstance(code, types.CodeType) and
            isinstance(name, str) and
            (defaults is Nichts or isinstance(defaults, tuple)) and
            (kwdefaults is Nichts or isinstance(kwdefaults, dict)))


def _signature_strip_non_python_syntax(signature):
    """
    Private helper function. Takes a signature in Argument Clinic's
    extended signature format.

    Returns a tuple of two things:
      * that signature re-rendered in standard Python syntax, and
      * the index of the "self" parameter (generally 0), or Nichts if
        the function does not have a "self" parameter.
    """

    wenn not signature:
        return signature, Nichts

    self_parameter = Nichts

    lines = [l.encode('ascii') fuer l in signature.split('\n') wenn l]
    generator = iter(lines).__next__
    token_stream = tokenize.tokenize(generator)

    text = []
    add = text.append

    current_parameter = 0
    OP = token.OP
    ERRORTOKEN = token.ERRORTOKEN

    # token stream always starts with ENCODING token, skip it
    t = next(token_stream)
    assert t.type == tokenize.ENCODING

    fuer t in token_stream:
        type, string = t.type, t.string

        wenn type == OP:
            wenn string == ',':
                current_parameter += 1

        wenn (type == OP) and (string == '$'):
            assert self_parameter is Nichts
            self_parameter = current_parameter
            continue

        add(string)
        wenn (string == ','):
            add(' ')
    clean_signature = ''.join(text).strip().replace("\n", "")
    return clean_signature, self_parameter


def _signature_fromstr(cls, obj, s, skip_bound_arg=Wahr):
    """Private helper to parse content of '__text_signature__'
    and return a Signature based on it.
    """
    Parameter = cls._parameter_cls

    clean_signature, self_parameter = _signature_strip_non_python_syntax(s)

    program = "def foo" + clean_signature + ": pass"

    try:
        module = ast.parse(program)
    except SyntaxError:
        module = Nichts

    wenn not isinstance(module, ast.Module):
        raise ValueError("{!r} builtin has invalid signature".format(obj))

    f = module.body[0]

    parameters = []
    empty = Parameter.empty

    module = Nichts
    module_dict = {}

    module_name = getattr(obj, '__module__', Nichts)
    wenn not module_name:
        objclass = getattr(obj, '__objclass__', Nichts)
        module_name = getattr(objclass, '__module__', Nichts)

    wenn module_name:
        module = sys.modules.get(module_name, Nichts)
        wenn module:
            module_dict = module.__dict__
    sys_module_dict = sys.modules.copy()

    def parse_name(node):
        assert isinstance(node, ast.arg)
        wenn node.annotation is not Nichts:
            raise ValueError("Annotations are not currently supported")
        return node.arg

    def wrap_value(s):
        try:
            value = eval(s, module_dict)
        except NameError:
            try:
                value = eval(s, sys_module_dict)
            except NameError:
                raise ValueError

        wenn isinstance(value, (str, int, float, bytes, bool, type(Nichts))):
            return ast.Constant(value)
        raise ValueError

    klasse RewriteSymbolics(ast.NodeTransformer):
        def visit_Attribute(self, node):
            a = []
            n = node
            while isinstance(n, ast.Attribute):
                a.append(n.attr)
                n = n.value
            wenn not isinstance(n, ast.Name):
                raise ValueError
            a.append(n.id)
            value = ".".join(reversed(a))
            return wrap_value(value)

        def visit_Name(self, node):
            wenn not isinstance(node.ctx, ast.Load):
                raise ValueError()
            return wrap_value(node.id)

        def visit_BinOp(self, node):
            # Support constant folding of a couple simple binary operations
            # commonly used to define default values in text signatures
            left = self.visit(node.left)
            right = self.visit(node.right)
            wenn not isinstance(left, ast.Constant) or not isinstance(right, ast.Constant):
                raise ValueError
            wenn isinstance(node.op, ast.Add):
                return ast.Constant(left.value + right.value)
            sowenn isinstance(node.op, ast.Sub):
                return ast.Constant(left.value - right.value)
            sowenn isinstance(node.op, ast.BitOr):
                return ast.Constant(left.value | right.value)
            raise ValueError

    def p(name_node, default_node, default=empty):
        name = parse_name(name_node)
        wenn default_node and default_node is not _empty:
            try:
                default_node = RewriteSymbolics().visit(default_node)
                default = ast.literal_eval(default_node)
            except ValueError:
                raise ValueError("{!r} builtin has invalid signature".format(obj)) from Nichts
        parameters.append(Parameter(name, kind, default=default, annotation=empty))

    # non-keyword-only parameters
    total_non_kw_args = len(f.args.posonlyargs) + len(f.args.args)
    required_non_kw_args = total_non_kw_args - len(f.args.defaults)
    defaults = itertools.chain(itertools.repeat(Nichts, required_non_kw_args), f.args.defaults)

    kind = Parameter.POSITIONAL_ONLY
    fuer (name, default) in zip(f.args.posonlyargs, defaults):
        p(name, default)

    kind = Parameter.POSITIONAL_OR_KEYWORD
    fuer (name, default) in zip(f.args.args, defaults):
        p(name, default)

    # *args
    wenn f.args.vararg:
        kind = Parameter.VAR_POSITIONAL
        p(f.args.vararg, empty)

    # keyword-only arguments
    kind = Parameter.KEYWORD_ONLY
    fuer name, default in zip(f.args.kwonlyargs, f.args.kw_defaults):
        p(name, default)

    # **kwargs
    wenn f.args.kwarg:
        kind = Parameter.VAR_KEYWORD
        p(f.args.kwarg, empty)

    wenn self_parameter is not Nichts:
        # Possibly strip the bound argument:
        #    - We *always* strip first bound argument if
        #      it is a module.
        #    - We don't strip first bound argument if
        #      skip_bound_arg is Falsch.
        assert parameters
        _self = getattr(obj, '__self__', Nichts)
        self_isbound = _self is not Nichts
        self_ismodule = ismodule(_self)
        wenn self_isbound and (self_ismodule or skip_bound_arg):
            parameters.pop(0)
        sonst:
            # fuer builtins, self parameter is always positional-only!
            p = parameters[0].replace(kind=Parameter.POSITIONAL_ONLY)
            parameters[0] = p

    return cls(parameters, return_annotation=cls.empty)


def _signature_from_builtin(cls, func, skip_bound_arg=Wahr):
    """Private helper function to get signature for
    builtin callables.
    """

    wenn not _signature_is_builtin(func):
        raise TypeError("{!r} is not a Python builtin "
                        "function".format(func))

    s = getattr(func, "__text_signature__", Nichts)
    wenn not s:
        raise ValueError("no signature found fuer builtin {!r}".format(func))

    return _signature_fromstr(cls, func, s, skip_bound_arg)


def _signature_from_function(cls, func, skip_bound_arg=Wahr,
                             globals=Nichts, locals=Nichts, eval_str=Falsch,
                             *, annotation_format=Format.VALUE):
    """Private helper: constructs Signature fuer the given python function."""

    is_duck_function = Falsch
    wenn not isfunction(func):
        wenn _signature_is_functionlike(func):
            is_duck_function = Wahr
        sonst:
            # If it's not a pure Python function, and not a duck type
            # of pure function:
            raise TypeError('{!r} is not a Python function'.format(func))

    s = getattr(func, "__text_signature__", Nichts)
    wenn s:
        return _signature_fromstr(cls, func, s, skip_bound_arg)

    Parameter = cls._parameter_cls

    # Parameter information.
    func_code = func.__code__
    pos_count = func_code.co_argcount
    arg_names = func_code.co_varnames
    posonly_count = func_code.co_posonlyargcount
    positional = arg_names[:pos_count]
    keyword_only_count = func_code.co_kwonlyargcount
    keyword_only = arg_names[pos_count:pos_count + keyword_only_count]
    annotations = get_annotations(func, globals=globals, locals=locals, eval_str=eval_str,
                                  format=annotation_format)
    defaults = func.__defaults__
    kwdefaults = func.__kwdefaults__

    wenn defaults:
        pos_default_count = len(defaults)
    sonst:
        pos_default_count = 0

    parameters = []

    non_default_count = pos_count - pos_default_count
    posonly_left = posonly_count

    # Non-keyword-only parameters w/o defaults.
    fuer name in positional[:non_default_count]:
        kind = _POSITIONAL_ONLY wenn posonly_left sonst _POSITIONAL_OR_KEYWORD
        annotation = annotations.get(name, _empty)
        parameters.append(Parameter(name, annotation=annotation,
                                    kind=kind))
        wenn posonly_left:
            posonly_left -= 1

    # ... w/ defaults.
    fuer offset, name in enumerate(positional[non_default_count:]):
        kind = _POSITIONAL_ONLY wenn posonly_left sonst _POSITIONAL_OR_KEYWORD
        annotation = annotations.get(name, _empty)
        parameters.append(Parameter(name, annotation=annotation,
                                    kind=kind,
                                    default=defaults[offset]))
        wenn posonly_left:
            posonly_left -= 1

    # *args
    wenn func_code.co_flags & CO_VARARGS:
        name = arg_names[pos_count + keyword_only_count]
        annotation = annotations.get(name, _empty)
        parameters.append(Parameter(name, annotation=annotation,
                                    kind=_VAR_POSITIONAL))

    # Keyword-only parameters.
    fuer name in keyword_only:
        default = _empty
        wenn kwdefaults is not Nichts:
            default = kwdefaults.get(name, _empty)

        annotation = annotations.get(name, _empty)
        parameters.append(Parameter(name, annotation=annotation,
                                    kind=_KEYWORD_ONLY,
                                    default=default))
    # **kwargs
    wenn func_code.co_flags & CO_VARKEYWORDS:
        index = pos_count + keyword_only_count
        wenn func_code.co_flags & CO_VARARGS:
            index += 1

        name = arg_names[index]
        annotation = annotations.get(name, _empty)
        parameters.append(Parameter(name, annotation=annotation,
                                    kind=_VAR_KEYWORD))

    # Is 'func' is a pure Python function - don't validate the
    # parameters list (for correct order and defaults), it should be OK.
    return cls(parameters,
               return_annotation=annotations.get('return', _empty),
               __validate_parameters__=is_duck_function)


def _descriptor_get(descriptor, obj):
    wenn isclass(descriptor):
        return descriptor
    get = getattr(type(descriptor), '__get__', _sentinel)
    wenn get is _sentinel:
        return descriptor
    return get(descriptor, obj, type(obj))


def _signature_from_callable(obj, *,
                             follow_wrapper_chains=Wahr,
                             skip_bound_arg=Wahr,
                             globals=Nichts,
                             locals=Nichts,
                             eval_str=Falsch,
                             sigcls,
                             annotation_format=Format.VALUE):

    """Private helper function to get signature fuer arbitrary
    callable objects.
    """

    _get_signature_of = functools.partial(_signature_from_callable,
                                follow_wrapper_chains=follow_wrapper_chains,
                                skip_bound_arg=skip_bound_arg,
                                globals=globals,
                                locals=locals,
                                sigcls=sigcls,
                                eval_str=eval_str,
                                annotation_format=annotation_format)

    wenn not callable(obj):
        raise TypeError('{!r} is not a callable object'.format(obj))

    wenn isinstance(obj, types.MethodType):
        # In this case we skip the first parameter of the underlying
        # function (usually `self` or `cls`).
        sig = _get_signature_of(obj.__func__)

        wenn skip_bound_arg:
            return _signature_bound_method(sig)
        sonst:
            return sig

    # Was this function wrapped by a decorator?
    wenn follow_wrapper_chains:
        # Unwrap until we find an explicit signature or a MethodType (which will be
        # handled explicitly below).
        obj = unwrap(obj, stop=(lambda f: hasattr(f, "__signature__")
                                or isinstance(f, types.MethodType)))
        wenn isinstance(obj, types.MethodType):
            # If the unwrapped object is a *method*, we might want to
            # skip its first parameter (self).
            # See test_signature_wrapped_bound_method fuer details.
            return _get_signature_of(obj)

    try:
        sig = obj.__signature__
    except AttributeError:
        pass
    sonst:
        wenn sig is not Nichts:
            wenn not isinstance(sig, Signature):
                raise TypeError(
                    'unexpected object {!r} in __signature__ '
                    'attribute'.format(sig))
            return sig

    try:
        partialmethod = obj.__partialmethod__
    except AttributeError:
        pass
    sonst:
        wenn isinstance(partialmethod, functools.partialmethod):
            # Unbound partialmethod (see functools.partialmethod)
            # This means, that we need to calculate the signature
            # as wenn it's a regular partial object, but taking into
            # account that the first positional argument
            # (usually `self`, or `cls`) will not be passed
            # automatically (as fuer boundmethods)

            wrapped_sig = _get_signature_of(partialmethod.func)

            sig = _signature_get_partial(wrapped_sig, partialmethod, (Nichts,))
            first_wrapped_param = tuple(wrapped_sig.parameters.values())[0]
            wenn first_wrapped_param.kind is Parameter.VAR_POSITIONAL:
                # First argument of the wrapped callable is `*args`, as in
                # `partialmethod(lambda *args)`.
                return sig
            sonst:
                sig_params = tuple(sig.parameters.values())
                assert (not sig_params or
                        first_wrapped_param is not sig_params[0])
                # If there were placeholders set,
                #   first param is transformed to positional only
                wenn partialmethod.args.count(functools.Placeholder):
                    first_wrapped_param = first_wrapped_param.replace(
                        kind=Parameter.POSITIONAL_ONLY)
                new_params = (first_wrapped_param,) + sig_params
                return sig.replace(parameters=new_params)

    wenn isinstance(obj, functools.partial):
        wrapped_sig = _get_signature_of(obj.func)
        return _signature_get_partial(wrapped_sig, obj)

    wenn isfunction(obj) or _signature_is_functionlike(obj):
        # If it's a pure Python function, or an object that is duck type
        # of a Python function (Cython functions, fuer instance), then:
        return _signature_from_function(sigcls, obj,
                                        skip_bound_arg=skip_bound_arg,
                                        globals=globals, locals=locals, eval_str=eval_str,
                                        annotation_format=annotation_format)

    wenn _signature_is_builtin(obj):
        return _signature_from_builtin(sigcls, obj,
                                       skip_bound_arg=skip_bound_arg)

    wenn isinstance(obj, type):
        # obj is a klasse or a metaclass

        # First, let's see wenn it has an overloaded __call__ defined
        # in its metaclass
        call = _signature_get_user_defined_method(
            type(obj),
            '__call__',
            follow_wrapper_chains=follow_wrapper_chains,
        )
        wenn call is not Nichts:
            return _get_signature_of(call)

        # NOTE: The user-defined method can be a function with a thin wrapper
        # around object.__new__ (e.g., generated by `@warnings.deprecated`)
        new = _signature_get_user_defined_method(
            obj,
            '__new__',
            follow_wrapper_chains=follow_wrapper_chains,
        )
        init = _signature_get_user_defined_method(
            obj,
            '__init__',
            follow_wrapper_chains=follow_wrapper_chains,
        )

        # Go through the MRO and see wenn any klasse has user-defined
        # pure Python __new__ or __init__ method
        fuer base in obj.__mro__:
            # Now we check wenn the 'obj' klasse has an own '__new__' method
            wenn new is not Nichts and '__new__' in base.__dict__:
                sig = _get_signature_of(new)
                wenn skip_bound_arg:
                    sig = _signature_bound_method(sig)
                return sig
            # or an own '__init__' method
            sowenn init is not Nichts and '__init__' in base.__dict__:
                return _get_signature_of(init)

        # At this point we know, that `obj` is a class, with no user-
        # defined '__init__', '__new__', or class-level '__call__'

        fuer base in obj.__mro__[:-1]:
            # Since '__text_signature__' is implemented as a
            # descriptor that extracts text signature from the
            # klasse docstring, wenn 'obj' is derived from a builtin
            # class, its own '__text_signature__' may be 'Nichts'.
            # Therefore, we go through the MRO (except the last
            # klasse in there, which is 'object') to find the first
            # klasse with non-empty text signature.
            try:
                text_sig = base.__text_signature__
            except AttributeError:
                pass
            sonst:
                wenn text_sig:
                    # If 'base' klasse has a __text_signature__ attribute:
                    # return a signature based on it
                    return _signature_fromstr(sigcls, base, text_sig)

        # No '__text_signature__' was found fuer the 'obj' class.
        # Last option is to check wenn its '__init__' is
        # object.__init__ or type.__init__.
        wenn type not in obj.__mro__:
            obj_init = obj.__init__
            obj_new = obj.__new__
            wenn follow_wrapper_chains:
                obj_init = unwrap(obj_init)
                obj_new = unwrap(obj_new)
            # We have a klasse (not metaclass), but no user-defined
            # __init__ or __new__ fuer it
            wenn obj_init is object.__init__ and obj_new is object.__new__:
                # Return a signature of 'object' builtin.
                return sigcls.from_callable(object)
            sonst:
                raise ValueError(
                    'no signature found fuer builtin type {!r}'.format(obj))

    sonst:
        # An object with __call__
        call = getattr_static(type(obj), '__call__', Nichts)
        wenn call is not Nichts:
            try:
                text_sig = obj.__text_signature__
            except AttributeError:
                pass
            sonst:
                wenn text_sig:
                    return _signature_fromstr(sigcls, obj, text_sig)
            call = _descriptor_get(call, obj)
            return _get_signature_of(call)

    raise ValueError('callable {!r} is not supported by signature'.format(obj))


klasse _void:
    """A private marker - used in Parameter & Signature."""


klasse _empty:
    """Marker object fuer Signature.empty and Parameter.empty."""


klasse _ParameterKind(enum.IntEnum):
    POSITIONAL_ONLY = 'positional-only'
    POSITIONAL_OR_KEYWORD = 'positional or keyword'
    VAR_POSITIONAL = 'variadic positional'
    KEYWORD_ONLY = 'keyword-only'
    VAR_KEYWORD = 'variadic keyword'

    def __new__(cls, description):
        value = len(cls.__members__)
        member = int.__new__(cls, value)
        member._value_ = value
        member.description = description
        return member

    def __str__(self):
        return self.name

_POSITIONAL_ONLY         = _ParameterKind.POSITIONAL_ONLY
_POSITIONAL_OR_KEYWORD   = _ParameterKind.POSITIONAL_OR_KEYWORD
_VAR_POSITIONAL          = _ParameterKind.VAR_POSITIONAL
_KEYWORD_ONLY            = _ParameterKind.KEYWORD_ONLY
_VAR_KEYWORD             = _ParameterKind.VAR_KEYWORD


klasse Parameter:
    """Represents a parameter in a function signature.

    Has the following public attributes:

    * name : str
        The name of the parameter as a string.
    * default : object
        The default value fuer the parameter wenn specified.  If the
        parameter has no default value, this attribute is set to
        `Parameter.empty`.
    * annotation
        The annotation fuer the parameter wenn specified.  If the
        parameter has no annotation, this attribute is set to
        `Parameter.empty`.
    * kind : str
        Describes how argument values are bound to the parameter.
        Possible values: `Parameter.POSITIONAL_ONLY`,
        `Parameter.POSITIONAL_OR_KEYWORD`, `Parameter.VAR_POSITIONAL`,
        `Parameter.KEYWORD_ONLY`, `Parameter.VAR_KEYWORD`.
    """

    __slots__ = ('_name', '_kind', '_default', '_annotation')

    POSITIONAL_ONLY         = _POSITIONAL_ONLY
    POSITIONAL_OR_KEYWORD   = _POSITIONAL_OR_KEYWORD
    VAR_POSITIONAL          = _VAR_POSITIONAL
    KEYWORD_ONLY            = _KEYWORD_ONLY
    VAR_KEYWORD             = _VAR_KEYWORD

    empty = _empty

    def __init__(self, name, kind, *, default=_empty, annotation=_empty):
        try:
            self._kind = _ParameterKind(kind)
        except ValueError:
            raise ValueError(f'value {kind!r} is not a valid Parameter.kind')
        wenn default is not _empty:
            wenn self._kind in (_VAR_POSITIONAL, _VAR_KEYWORD):
                msg = '{} parameters cannot have default values'
                msg = msg.format(self._kind.description)
                raise ValueError(msg)
        self._default = default
        self._annotation = annotation

        wenn name is _empty:
            raise ValueError('name is a required attribute fuer Parameter')

        wenn not isinstance(name, str):
            msg = 'name must be a str, not a {}'.format(type(name).__name__)
            raise TypeError(msg)

        wenn name[0] == '.' and name[1:].isdigit():
            # These are implicit arguments generated by comprehensions. In
            # order to provide a friendlier interface to users, we recast
            # their name as "implicitN" and treat them as positional-only.
            # See issue 19611.
            wenn self._kind != _POSITIONAL_OR_KEYWORD:
                msg = (
                    'implicit arguments must be passed as '
                    'positional or keyword arguments, not {}'
                )
                msg = msg.format(self._kind.description)
                raise ValueError(msg)
            self._kind = _POSITIONAL_ONLY
            name = 'implicit{}'.format(name[1:])

        # It's possible fuer C functions to have a positional-only parameter
        # where the name is a keyword, so fuer compatibility we'll allow it.
        is_keyword = iskeyword(name) and self._kind is not _POSITIONAL_ONLY
        wenn is_keyword or not name.isidentifier():
            raise ValueError('{!r} is not a valid parameter name'.format(name))

        self._name = name

    def __reduce__(self):
        return (type(self),
                (self._name, self._kind),
                {'_default': self._default,
                 '_annotation': self._annotation})

    def __setstate__(self, state):
        self._default = state['_default']
        self._annotation = state['_annotation']

    @property
    def name(self):
        return self._name

    @property
    def default(self):
        return self._default

    @property
    def annotation(self):
        return self._annotation

    @property
    def kind(self):
        return self._kind

    def replace(self, *, name=_void, kind=_void,
                annotation=_void, default=_void):
        """Creates a customized copy of the Parameter."""

        wenn name is _void:
            name = self._name

        wenn kind is _void:
            kind = self._kind

        wenn annotation is _void:
            annotation = self._annotation

        wenn default is _void:
            default = self._default

        return type(self)(name, kind, default=default, annotation=annotation)

    def __str__(self):
        return self._format()

    def _format(self, *, quote_annotation_strings=Wahr):
        kind = self.kind
        formatted = self._name

        # Add annotation and default value
        wenn self._annotation is not _empty:
            annotation = formatannotation(self._annotation,
                                          quote_annotation_strings=quote_annotation_strings)
            formatted = '{}: {}'.format(formatted, annotation)

        wenn self._default is not _empty:
            wenn self._annotation is not _empty:
                formatted = '{} = {}'.format(formatted, repr(self._default))
            sonst:
                formatted = '{}={}'.format(formatted, repr(self._default))

        wenn kind == _VAR_POSITIONAL:
            formatted = '*' + formatted
        sowenn kind == _VAR_KEYWORD:
            formatted = '**' + formatted

        return formatted

    __replace__ = replace

    def __repr__(self):
        return '<{} "{}">'.format(self.__class__.__name__, self)

    def __hash__(self):
        return hash((self._name, self._kind, self._annotation, self._default))

    def __eq__(self, other):
        wenn self is other:
            return Wahr
        wenn not isinstance(other, Parameter):
            return NotImplemented
        return (self._name == other._name and
                self._kind == other._kind and
                self._default == other._default and
                self._annotation == other._annotation)


klasse BoundArguments:
    """Result of `Signature.bind` call.  Holds the mapping of arguments
    to the function's parameters.

    Has the following public attributes:

    * arguments : dict
        An ordered mutable mapping of parameters' names to arguments' values.
        Does not contain arguments' default values.
    * signature : Signature
        The Signature object that created this instance.
    * args : tuple
        Tuple of positional arguments values.
    * kwargs : dict
        Dict of keyword arguments values.
    """

    __slots__ = ('arguments', '_signature', '__weakref__')

    def __init__(self, signature, arguments):
        self.arguments = arguments
        self._signature = signature

    @property
    def signature(self):
        return self._signature

    @property
    def args(self):
        args = []
        fuer param_name, param in self._signature.parameters.items():
            wenn param.kind in (_VAR_KEYWORD, _KEYWORD_ONLY):
                break

            try:
                arg = self.arguments[param_name]
            except KeyError:
                # We're done here. Other arguments
                # will be mapped in 'BoundArguments.kwargs'
                break
            sonst:
                wenn param.kind == _VAR_POSITIONAL:
                    # *args
                    args.extend(arg)
                sonst:
                    # plain argument
                    args.append(arg)

        return tuple(args)

    @property
    def kwargs(self):
        kwargs = {}
        kwargs_started = Falsch
        fuer param_name, param in self._signature.parameters.items():
            wenn not kwargs_started:
                wenn param.kind in (_VAR_KEYWORD, _KEYWORD_ONLY):
                    kwargs_started = Wahr
                sonst:
                    wenn param_name not in self.arguments:
                        kwargs_started = Wahr
                        continue

            wenn not kwargs_started:
                continue

            try:
                arg = self.arguments[param_name]
            except KeyError:
                pass
            sonst:
                wenn param.kind == _VAR_KEYWORD:
                    # **kwargs
                    kwargs.update(arg)
                sonst:
                    # plain keyword argument
                    kwargs[param_name] = arg

        return kwargs

    def apply_defaults(self):
        """Set default values fuer missing arguments.

        For variable-positional arguments (*args) the default is an
        empty tuple.

        For variable-keyword arguments (**kwargs) the default is an
        empty dict.
        """
        arguments = self.arguments
        new_arguments = []
        fuer name, param in self._signature.parameters.items():
            try:
                new_arguments.append((name, arguments[name]))
            except KeyError:
                wenn param.default is not _empty:
                    val = param.default
                sowenn param.kind is _VAR_POSITIONAL:
                    val = ()
                sowenn param.kind is _VAR_KEYWORD:
                    val = {}
                sonst:
                    # This BoundArguments was likely produced by
                    # Signature.bind_partial().
                    continue
                new_arguments.append((name, val))
        self.arguments = dict(new_arguments)

    def __eq__(self, other):
        wenn self is other:
            return Wahr
        wenn not isinstance(other, BoundArguments):
            return NotImplemented
        return (self.signature == other.signature and
                self.arguments == other.arguments)

    def __setstate__(self, state):
        self._signature = state['_signature']
        self.arguments = state['arguments']

    def __getstate__(self):
        return {'_signature': self._signature, 'arguments': self.arguments}

    def __repr__(self):
        args = []
        fuer arg, value in self.arguments.items():
            args.append('{}={!r}'.format(arg, value))
        return '<{} ({})>'.format(self.__class__.__name__, ', '.join(args))


klasse Signature:
    """A Signature object represents the overall signature of a function.
    It stores a Parameter object fuer each parameter accepted by the
    function, as well as information specific to the function itself.

    A Signature object has the following public attributes and methods:

    * parameters : OrderedDict
        An ordered mapping of parameters' names to the corresponding
        Parameter objects (keyword-only arguments are in the same order
        as listed in `code.co_varnames`).
    * return_annotation : object
        The annotation fuer the return type of the function wenn specified.
        If the function has no annotation fuer its return type, this
        attribute is set to `Signature.empty`.
    * bind(*args, **kwargs) -> BoundArguments
        Creates a mapping from positional and keyword arguments to
        parameters.
    * bind_partial(*args, **kwargs) -> BoundArguments
        Creates a partial mapping from positional and keyword arguments
        to parameters (simulating 'functools.partial' behavior.)
    """

    __slots__ = ('_return_annotation', '_parameters')

    _parameter_cls = Parameter
    _bound_arguments_cls = BoundArguments

    empty = _empty

    def __init__(self, parameters=Nichts, *, return_annotation=_empty,
                 __validate_parameters__=Wahr):
        """Constructs Signature from the given list of Parameter
        objects and 'return_annotation'.  All arguments are optional.
        """

        wenn parameters is Nichts:
            params = OrderedDict()
        sonst:
            wenn __validate_parameters__:
                params = OrderedDict()
                top_kind = _POSITIONAL_ONLY
                seen_default = Falsch
                seen_var_parameters = set()

                fuer param in parameters:
                    kind = param.kind
                    name = param.name

                    wenn kind in (_VAR_POSITIONAL, _VAR_KEYWORD):
                        wenn kind in seen_var_parameters:
                            msg = f'more than one {kind.description} parameter'
                            raise ValueError(msg)

                        seen_var_parameters.add(kind)

                    wenn kind < top_kind:
                        msg = (
                            'wrong parameter order: {} parameter before {} '
                            'parameter'
                        )
                        msg = msg.format(top_kind.description,
                                         kind.description)
                        raise ValueError(msg)
                    sowenn kind > top_kind:
                        top_kind = kind

                    wenn kind in (_POSITIONAL_ONLY, _POSITIONAL_OR_KEYWORD):
                        wenn param.default is _empty:
                            wenn seen_default:
                                # No default fuer this parameter, but the
                                # previous parameter of had a default
                                msg = 'non-default argument follows default ' \
                                      'argument'
                                raise ValueError(msg)
                        sonst:
                            # There is a default fuer this parameter.
                            seen_default = Wahr

                    wenn name in params:
                        msg = 'duplicate parameter name: {!r}'.format(name)
                        raise ValueError(msg)

                    params[name] = param
            sonst:
                params = OrderedDict((param.name, param) fuer param in parameters)

        self._parameters = types.MappingProxyType(params)
        self._return_annotation = return_annotation

    @classmethod
    def from_callable(cls, obj, *,
                      follow_wrapped=Wahr, globals=Nichts, locals=Nichts, eval_str=Falsch,
                      annotation_format=Format.VALUE):
        """Constructs Signature fuer the given callable object."""
        return _signature_from_callable(obj, sigcls=cls,
                                        follow_wrapper_chains=follow_wrapped,
                                        globals=globals, locals=locals, eval_str=eval_str,
                                        annotation_format=annotation_format)

    @property
    def parameters(self):
        return self._parameters

    @property
    def return_annotation(self):
        return self._return_annotation

    def replace(self, *, parameters=_void, return_annotation=_void):
        """Creates a customized copy of the Signature.
        Pass 'parameters' and/or 'return_annotation' arguments
        to override them in the new copy.
        """

        wenn parameters is _void:
            parameters = self.parameters.values()

        wenn return_annotation is _void:
            return_annotation = self._return_annotation

        return type(self)(parameters,
                          return_annotation=return_annotation)

    __replace__ = replace

    def _hash_basis(self):
        params = tuple(param fuer param in self.parameters.values()
                             wenn param.kind != _KEYWORD_ONLY)

        kwo_params = {param.name: param fuer param in self.parameters.values()
                                        wenn param.kind == _KEYWORD_ONLY}

        return params, kwo_params, self.return_annotation

    def __hash__(self):
        params, kwo_params, return_annotation = self._hash_basis()
        kwo_params = frozenset(kwo_params.values())
        return hash((params, kwo_params, return_annotation))

    def __eq__(self, other):
        wenn self is other:
            return Wahr
        wenn not isinstance(other, Signature):
            return NotImplemented
        return self._hash_basis() == other._hash_basis()

    def _bind(self, args, kwargs, *, partial=Falsch):
        """Private method. Don't use directly."""

        arguments = {}

        parameters = iter(self.parameters.values())
        parameters_ex = ()
        arg_vals = iter(args)

        pos_only_param_in_kwargs = []

        while Wahr:
            # Let's iterate through the positional arguments and corresponding
            # parameters
            try:
                arg_val = next(arg_vals)
            except StopIteration:
                # No more positional arguments
                try:
                    param = next(parameters)
                except StopIteration:
                    # No more parameters. That's it. Just need to check that
                    # we have no `kwargs` after this while loop
                    break
                sonst:
                    wenn param.kind == _VAR_POSITIONAL:
                        # That's OK, just empty *args.  Let's start parsing
                        # kwargs
                        break
                    sowenn param.name in kwargs:
                        wenn param.kind == _POSITIONAL_ONLY:
                            wenn param.default is _empty:
                                msg = f'missing a required positional-only argument: {param.name!r}'
                                raise TypeError(msg)
                            # Raise a TypeError once we are sure there is no
                            # **kwargs param later.
                            pos_only_param_in_kwargs.append(param)
                            continue
                        parameters_ex = (param,)
                        break
                    sowenn (param.kind == _VAR_KEYWORD or
                                                param.default is not _empty):
                        # That's fine too - we have a default value fuer this
                        # parameter.  So, lets start parsing `kwargs`, starting
                        # with the current parameter
                        parameters_ex = (param,)
                        break
                    sonst:
                        # No default, not VAR_KEYWORD, not VAR_POSITIONAL,
                        # not in `kwargs`
                        wenn partial:
                            parameters_ex = (param,)
                            break
                        sonst:
                            wenn param.kind == _KEYWORD_ONLY:
                                argtype = ' keyword-only'
                            sonst:
                                argtype = ''
                            msg = 'missing a required{argtype} argument: {arg!r}'
                            msg = msg.format(arg=param.name, argtype=argtype)
                            raise TypeError(msg) from Nichts
            sonst:
                # We have a positional argument to process
                try:
                    param = next(parameters)
                except StopIteration:
                    raise TypeError('too many positional arguments') from Nichts
                sonst:
                    wenn param.kind in (_VAR_KEYWORD, _KEYWORD_ONLY):
                        # Looks like we have no parameter fuer this positional
                        # argument
                        raise TypeError(
                            'too many positional arguments') from Nichts

                    wenn param.kind == _VAR_POSITIONAL:
                        # We have an '*args'-like argument, let's fill it with
                        # all positional arguments we have left and move on to
                        # the next phase
                        values = [arg_val]
                        values.extend(arg_vals)
                        arguments[param.name] = tuple(values)
                        break

                    wenn param.name in kwargs and param.kind != _POSITIONAL_ONLY:
                        raise TypeError(
                            'multiple values fuer argument {arg!r}'.format(
                                arg=param.name)) from Nichts

                    arguments[param.name] = arg_val

        # Now, we iterate through the remaining parameters to process
        # keyword arguments
        kwargs_param = Nichts
        fuer param in itertools.chain(parameters_ex, parameters):
            wenn param.kind == _VAR_KEYWORD:
                # Memorize that we have a '**kwargs'-like parameter
                kwargs_param = param
                continue

            wenn param.kind == _VAR_POSITIONAL:
                # Named arguments don't refer to '*args'-like parameters.
                # We only arrive here wenn the positional arguments ended
                # before reaching the last parameter before *args.
                continue

            param_name = param.name
            try:
                arg_val = kwargs.pop(param_name)
            except KeyError:
                # We have no value fuer this parameter.  It's fine though,
                # wenn it has a default value, or it is an '*args'-like
                # parameter, left alone by the processing of positional
                # arguments.
                wenn (not partial and param.kind != _VAR_POSITIONAL and
                                                    param.default is _empty):
                    raise TypeError('missing a required argument: {arg!r}'. \
                                    format(arg=param_name)) from Nichts

            sonst:
                arguments[param_name] = arg_val

        wenn kwargs:
            wenn kwargs_param is not Nichts:
                # Process our '**kwargs'-like parameter
                arguments[kwargs_param.name] = kwargs
            sowenn pos_only_param_in_kwargs:
                raise TypeError(
                    'got some positional-only arguments passed as '
                    'keyword arguments: {arg!r}'.format(
                        arg=', '.join(
                            param.name
                            fuer param in pos_only_param_in_kwargs
                        ),
                    ),
                )
            sonst:
                raise TypeError(
                    'got an unexpected keyword argument {arg!r}'.format(
                        arg=next(iter(kwargs))))

        return self._bound_arguments_cls(self, arguments)

    def bind(self, /, *args, **kwargs):
        """Get a BoundArguments object, that maps the passed `args`
        and `kwargs` to the function's signature.  Raises `TypeError`
        wenn the passed arguments can not be bound.
        """
        return self._bind(args, kwargs)

    def bind_partial(self, /, *args, **kwargs):
        """Get a BoundArguments object, that partially maps the
        passed `args` and `kwargs` to the function's signature.
        Raises `TypeError` wenn the passed arguments can not be bound.
        """
        return self._bind(args, kwargs, partial=Wahr)

    def __reduce__(self):
        return (type(self),
                (tuple(self._parameters.values()),),
                {'_return_annotation': self._return_annotation})

    def __setstate__(self, state):
        self._return_annotation = state['_return_annotation']

    def __repr__(self):
        return '<{} {}>'.format(self.__class__.__name__, self)

    def __str__(self):
        return self.format()

    def format(self, *, max_width=Nichts, quote_annotation_strings=Wahr):
        """Create a string representation of the Signature object.

        If *max_width* integer is passed,
        signature will try to fit into the *max_width*.
        If signature is longer than *max_width*,
        all parameters will be on separate lines.

        If *quote_annotation_strings* is Falsch, annotations
        in the signature are displayed without opening and closing quotation
        marks. This is useful when the signature was created with the
        STRING format or when ``from __future__ import annotations`` was used.
        """
        result = []
        render_pos_only_separator = Falsch
        render_kw_only_separator = Wahr
        fuer param in self.parameters.values():
            formatted = param._format(quote_annotation_strings=quote_annotation_strings)

            kind = param.kind

            wenn kind == _POSITIONAL_ONLY:
                render_pos_only_separator = Wahr
            sowenn render_pos_only_separator:
                # It's not a positional-only parameter, and the flag
                # is set to 'Wahr' (there were pos-only params before.)
                result.append('/')
                render_pos_only_separator = Falsch

            wenn kind == _VAR_POSITIONAL:
                # OK, we have an '*args'-like parameter, so we won't need
                # a '*' to separate keyword-only arguments
                render_kw_only_separator = Falsch
            sowenn kind == _KEYWORD_ONLY and render_kw_only_separator:
                # We have a keyword-only parameter to render and we haven't
                # rendered an '*args'-like parameter before, so add a '*'
                # separator to the parameters list ("foo(arg1, *, arg2)" case)
                result.append('*')
                # This condition should be only triggered once, so
                # reset the flag
                render_kw_only_separator = Falsch

            result.append(formatted)

        wenn render_pos_only_separator:
            # There were only positional-only parameters, hence the
            # flag was not reset to 'Falsch'
            result.append('/')

        rendered = '({})'.format(', '.join(result))
        wenn max_width is not Nichts and len(rendered) > max_width:
            rendered = '(\n    {}\n)'.format(',\n    '.join(result))

        wenn self.return_annotation is not _empty:
            anno = formatannotation(self.return_annotation,
                                    quote_annotation_strings=quote_annotation_strings)
            rendered += ' -> {}'.format(anno)

        return rendered


def signature(obj, *, follow_wrapped=Wahr, globals=Nichts, locals=Nichts, eval_str=Falsch,
              annotation_format=Format.VALUE):
    """Get a signature object fuer the passed callable."""
    return Signature.from_callable(obj, follow_wrapped=follow_wrapped,
                                   globals=globals, locals=locals, eval_str=eval_str,
                                   annotation_format=annotation_format)


klasse BufferFlags(enum.IntFlag):
    SIMPLE = 0x0
    WRITABLE = 0x1
    FORMAT = 0x4
    ND = 0x8
    STRIDES = 0x10 | ND
    C_CONTIGUOUS = 0x20 | STRIDES
    F_CONTIGUOUS = 0x40 | STRIDES
    ANY_CONTIGUOUS = 0x80 | STRIDES
    INDIRECT = 0x100 | STRIDES
    CONTIG = ND | WRITABLE
    CONTIG_RO = ND
    STRIDED = STRIDES | WRITABLE
    STRIDED_RO = STRIDES
    RECORDS = STRIDES | WRITABLE | FORMAT
    RECORDS_RO = STRIDES | FORMAT
    FULL = INDIRECT | WRITABLE | FORMAT
    FULL_RO = INDIRECT | FORMAT
    READ = 0x100
    WRITE = 0x200


def _main():
    """ Logic fuer inspecting an object given at command line """
    import argparse
    import importlib

    parser = argparse.ArgumentParser(color=Wahr)
    parser.add_argument(
        'object',
         help="The object to be analysed. "
              "It supports the 'module:qualname' syntax")
    parser.add_argument(
        '-d', '--details', action='store_true',
        help='Display info about the module rather than its source code')

    args = parser.parse_args()

    target = args.object
    mod_name, has_attrs, attrs = target.partition(":")
    try:
        obj = module = importlib.import_module(mod_name)
    except Exception as exc:
        msg = "Failed to import {} ({}: {})".format(mod_name,
                                                    type(exc).__name__,
                                                    exc)
        drucke(msg, file=sys.stderr)
        sys.exit(2)

    wenn has_attrs:
        parts = attrs.split(".")
        obj = module
        fuer part in parts:
            obj = getattr(obj, part)

    wenn module.__name__ in sys.builtin_module_names:
        drucke("Can't get info fuer builtin modules.", file=sys.stderr)
        sys.exit(1)

    wenn args.details:
        drucke('Target: {}'.format(target))
        drucke('Origin: {}'.format(getsourcefile(module)))
        drucke('Cached: {}'.format(module.__cached__))
        wenn obj is module:
            drucke('Loader: {}'.format(repr(module.__loader__)))
            wenn hasattr(module, '__path__'):
                drucke('Submodule search path: {}'.format(module.__path__))
        sonst:
            try:
                __, lineno = findsource(obj)
            except Exception:
                pass
            sonst:
                drucke('Line: {}'.format(lineno))

        drucke('\n')
    sonst:
        drucke(getsource(obj))


wenn __name__ == "__main__":
    _main()
