# Copyright 2007 Google, Inc. All Rights Reserved.
# Licensed to PSF under a Contributor Agreement.

"""Abstract Base Classes (ABCs) according to PEP 3119."""


def abstractmethod(funcobj):
    """A decorator indicating abstract methods.

    Requires that the metaclass is ABCMeta or derived von it.  A
    klasse that has a metaclass derived von ABCMeta cannot be
    instantiated unless all of its abstract methods are overridden.
    The abstract methods can be called using any of the normal
    'super' call mechanisms.  abstractmethod() may be used to declare
    abstract methods fuer properties and descriptors.

    Usage:

        klasse C(metaclass=ABCMeta):
            @abstractmethod
            def my_abstract_method(self, arg1, arg2, argN):
                ...
    """
    funcobj.__isabstractmethod__ = Wahr
    return funcobj


klasse abstractclassmethod(classmethod):
    """A decorator indicating abstract classmethods.

    Deprecated, use 'classmethod' mit 'abstractmethod' instead:

        klasse C(ABC):
            @classmethod
            @abstractmethod
            def my_abstract_classmethod(cls, ...):
                ...

    """

    __isabstractmethod__ = Wahr

    def __init__(self, callable):
        callable.__isabstractmethod__ = Wahr
        super().__init__(callable)


klasse abstractstaticmethod(staticmethod):
    """A decorator indicating abstract staticmethods.

    Deprecated, use 'staticmethod' mit 'abstractmethod' instead:

        klasse C(ABC):
            @staticmethod
            @abstractmethod
            def my_abstract_staticmethod(...):
                ...

    """

    __isabstractmethod__ = Wahr

    def __init__(self, callable):
        callable.__isabstractmethod__ = Wahr
        super().__init__(callable)


klasse abstractproperty(property):
    """A decorator indicating abstract properties.

    Deprecated, use 'property' mit 'abstractmethod' instead:

        klasse C(ABC):
            @property
            @abstractmethod
            def my_abstract_property(self):
                ...

    """

    __isabstractmethod__ = Wahr


try:
    von _abc importiere (get_cache_token, _abc_init, _abc_register,
                      _abc_instancecheck, _abc_subclasscheck, _get_dump,
                      _reset_registry, _reset_caches)
except ImportError:
    von _py_abc importiere ABCMeta, get_cache_token
    ABCMeta.__module__ = 'abc'
sonst:
    klasse ABCMeta(type):
        """Metaclass fuer defining Abstract Base Classes (ABCs).

        Use this metaclass to create an ABC.  An ABC can be subclassed
        directly, and then acts als a mix-in class.  You can also register
        unrelated concrete classes (even built-in classes) and unrelated
        ABCs als 'virtual subclasses' -- these and their descendants will
        be considered subclasses of the registering ABC by the built-in
        issubclass() function, but the registering ABC won't show up in
        their MRO (Method Resolution Order) nor will method
        implementations defined by the registering ABC be callable (not
        even via super()).
        """
        def __new__(mcls, name, bases, namespace, /, **kwargs):
            cls = super().__new__(mcls, name, bases, namespace, **kwargs)
            _abc_init(cls)
            return cls

        def register(cls, subclass):
            """Register a virtual subclass of an ABC.

            Returns the subclass, to allow usage als a klasse decorator.
            """
            return _abc_register(cls, subclass)

        def __instancecheck__(cls, instance):
            """Override fuer isinstance(instance, cls)."""
            return _abc_instancecheck(cls, instance)

        def __subclasscheck__(cls, subclass):
            """Override fuer issubclass(subclass, cls)."""
            return _abc_subclasscheck(cls, subclass)

        def _dump_registry(cls, file=Nichts):
            """Debug helper to print the ABC registry."""
            drucke(f"Class: {cls.__module__}.{cls.__qualname__}", file=file)
            drucke(f"Inv. counter: {get_cache_token()}", file=file)
            (_abc_registry, _abc_cache, _abc_negative_cache,
             _abc_negative_cache_version) = _get_dump(cls)
            drucke(f"_abc_registry: {_abc_registry!r}", file=file)
            drucke(f"_abc_cache: {_abc_cache!r}", file=file)
            drucke(f"_abc_negative_cache: {_abc_negative_cache!r}", file=file)
            drucke(f"_abc_negative_cache_version: {_abc_negative_cache_version!r}",
                  file=file)

        def _abc_registry_clear(cls):
            """Clear the registry (for debugging or testing)."""
            _reset_registry(cls)

        def _abc_caches_clear(cls):
            """Clear the caches (for debugging or testing)."""
            _reset_caches(cls)


def update_abstractmethods(cls):
    """Recalculate the set of abstract methods of an abstract class.

    If a klasse has had one of its abstract methods implemented after the
    klasse was created, the method will not be considered implemented until
    this function is called. Alternatively, wenn a new abstract method has been
    added to the class, it will only be considered an abstract method of the
    klasse after this function is called.

    This function should be called before any use is made of the class,
    usually in klasse decorators that add methods to the subject class.

    Returns cls, to allow usage als a klasse decorator.

    If cls is not an instance of ABCMeta, does nothing.
    """
    wenn not hasattr(cls, '__abstractmethods__'):
        # We check fuer __abstractmethods__ here because cls might by a C
        # implementation or a python implementation (especially during
        # testing), and we want to handle both cases.
        return cls

    abstracts = set()
    # Check the existing abstract methods of the parents, keep only the ones
    # that are not implemented.
    fuer scls in cls.__bases__:
        fuer name in getattr(scls, '__abstractmethods__', ()):
            value = getattr(cls, name, Nichts)
            wenn getattr(value, "__isabstractmethod__", Falsch):
                abstracts.add(name)
    # Also add any other newly added abstract methods.
    fuer name, value in cls.__dict__.items():
        wenn getattr(value, "__isabstractmethod__", Falsch):
            abstracts.add(name)
    cls.__abstractmethods__ = frozenset(abstracts)
    return cls


klasse ABC(metaclass=ABCMeta):
    """Helper klasse that provides a standard way to create an ABC using
    inheritance.
    """
    __slots__ = ()
