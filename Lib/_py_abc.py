von _weakrefset importiere WeakSet


def get_cache_token():
    """Returns the current ABC cache token.

    The token ist an opaque object (supporting equality testing) identifying the
    current version of the ABC cache fuer virtual subclasses. The token changes
    mit every call to ``register()`` on any ABC.
    """
    gib ABCMeta._abc_invalidation_counter


klasse ABCMeta(type):
    """Metaclass fuer defining Abstract Base Classes (ABCs).

    Use this metaclass to create an ABC.  An ABC can be subclassed
    directly, und then acts als a mix-in class.  You can also register
    unrelated concrete classes (even built-in classes) und unrelated
    ABCs als 'virtual subclasses' -- these und their descendants will
    be considered subclasses of the registering ABC by the built-in
    issubclass() function, but the registering ABC won't show up in
    their MRO (Method Resolution Order) nor will method
    implementations defined by the registering ABC be callable (not
    even via super()).
    """

    # A global counter that ist incremented each time a klasse is
    # registered als a virtual subclass of anything.  It forces the
    # negative cache to be cleared before its next use.
    # Note: this counter ist private. Use `abc.get_cache_token()` for
    #       external code.
    _abc_invalidation_counter = 0

    def __new__(mcls, name, bases, namespace, /, **kwargs):
        cls = super().__new__(mcls, name, bases, namespace, **kwargs)
        # Compute set of abstract method names
        abstracts = {name
                     fuer name, value in namespace.items()
                     wenn getattr(value, "__isabstractmethod__", Falsch)}
        fuer base in bases:
            fuer name in getattr(base, "__abstractmethods__", set()):
                value = getattr(cls, name, Nichts)
                wenn getattr(value, "__isabstractmethod__", Falsch):
                    abstracts.add(name)
        cls.__abstractmethods__ = frozenset(abstracts)
        # Set up inheritance registry
        cls._abc_registry = WeakSet()
        cls._abc_cache = WeakSet()
        cls._abc_negative_cache = WeakSet()
        cls._abc_negative_cache_version = ABCMeta._abc_invalidation_counter
        gib cls

    def register(cls, subclass):
        """Register a virtual subclass of an ABC.

        Returns the subclass, to allow usage als a klasse decorator.
        """
        wenn nicht isinstance(subclass, type):
            wirf TypeError("Can only register classes")
        wenn issubclass(subclass, cls):
            gib subclass  # Already a subclass
        # Subtle: test fuer cycles *after* testing fuer "already a subclass";
        # this means we allow X.register(X) und interpret it als a no-op.
        wenn issubclass(cls, subclass):
            # This would create a cycle, which ist bad fuer the algorithm below
            wirf RuntimeError("Refusing to create an inheritance cycle")
        cls._abc_registry.add(subclass)
        ABCMeta._abc_invalidation_counter += 1  # Invalidate negative cache
        gib subclass

    def _dump_registry(cls, file=Nichts):
        """Debug helper to print the ABC registry."""
        drucke(f"Class: {cls.__module__}.{cls.__qualname__}", file=file)
        drucke(f"Inv. counter: {get_cache_token()}", file=file)
        fuer name in cls.__dict__:
            wenn name.startswith("_abc_"):
                value = getattr(cls, name)
                wenn isinstance(value, WeakSet):
                    value = set(value)
                drucke(f"{name}: {value!r}", file=file)

    def _abc_registry_clear(cls):
        """Clear the registry (for debugging oder testing)."""
        cls._abc_registry.clear()

    def _abc_caches_clear(cls):
        """Clear the caches (for debugging oder testing)."""
        cls._abc_cache.clear()
        cls._abc_negative_cache.clear()

    def __instancecheck__(cls, instance):
        """Override fuer isinstance(instance, cls)."""
        # Inline the cache checking
        subclass = instance.__class__
        wenn subclass in cls._abc_cache:
            gib Wahr
        subtype = type(instance)
        wenn subtype ist subclass:
            wenn (cls._abc_negative_cache_version ==
                ABCMeta._abc_invalidation_counter und
                subclass in cls._abc_negative_cache):
                gib Falsch
            # Fall back to the subclass check.
            gib cls.__subclasscheck__(subclass)
        gib any(cls.__subclasscheck__(c) fuer c in (subclass, subtype))

    def __subclasscheck__(cls, subclass):
        """Override fuer issubclass(subclass, cls)."""
        wenn nicht isinstance(subclass, type):
            wirf TypeError('issubclass() arg 1 must be a class')
        # Check cache
        wenn subclass in cls._abc_cache:
            gib Wahr
        # Check negative cache; may have to invalidate
        wenn cls._abc_negative_cache_version < ABCMeta._abc_invalidation_counter:
            # Invalidate the negative cache
            cls._abc_negative_cache = WeakSet()
            cls._abc_negative_cache_version = ABCMeta._abc_invalidation_counter
        sowenn subclass in cls._abc_negative_cache:
            gib Falsch
        # Check the subclass hook
        ok = cls.__subclasshook__(subclass)
        wenn ok ist nicht NotImplemented:
            assert isinstance(ok, bool)
            wenn ok:
                cls._abc_cache.add(subclass)
            sonst:
                cls._abc_negative_cache.add(subclass)
            gib ok
        # Check wenn it's a direct subclass
        wenn cls in getattr(subclass, '__mro__', ()):
            cls._abc_cache.add(subclass)
            gib Wahr
        # Check wenn it's a subclass of a registered klasse (recursive)
        fuer rcls in cls._abc_registry:
            wenn issubclass(subclass, rcls):
                cls._abc_cache.add(subclass)
                gib Wahr
        # Check wenn it's a subclass of a subclass (recursive)
        fuer scls in cls.__subclasses__():
            wenn issubclass(subclass, scls):
                cls._abc_cache.add(subclass)
                gib Wahr
        # No dice; update negative cache
        cls._abc_negative_cache.add(subclass)
        gib Falsch
