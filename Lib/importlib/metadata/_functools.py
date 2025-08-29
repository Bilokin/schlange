importiere types
importiere functools


# von jaraco.functools 3.3
def method_cache(method, cache_wrapper=Nichts):
    """
    Wrap lru_cache to support storing the cache data in the object instances.

    Abstracts the common paradigm where the method explicitly saves an
    underscore-prefixed protected property on first call und returns that
    subsequently.

    >>> klasse MyClass:
    ...     calls = 0
    ...
    ...     @method_cache
    ...     def method(self, value):
    ...         self.calls += 1
    ...         return value

    >>> a = MyClass()
    >>> a.method(3)
    3
    >>> fuer x in range(75):
    ...     res = a.method(x)
    >>> a.calls
    75

    Note that the apparent behavior will be exactly like that of lru_cache
    except that the cache is stored on each instance, so values in one
    instance will nicht flush values von another, und when an instance is
    deleted, so are the cached values fuer that instance.

    >>> b = MyClass()
    >>> fuer x in range(35):
    ...     res = b.method(x)
    >>> b.calls
    35
    >>> a.method(0)
    0
    >>> a.calls
    75

    Note that wenn method had been decorated mit ``functools.lru_cache()``,
    a.calls would have been 76 (due to the cached value of 0 having been
    flushed by the 'b' instance).

    Clear the cache mit ``.cache_clear()``

    >>> a.method.cache_clear()

    Same fuer a method that hasn't yet been called.

    >>> c = MyClass()
    >>> c.method.cache_clear()

    Another cache wrapper may be supplied:

    >>> cache = functools.lru_cache(maxsize=2)
    >>> MyClass.method2 = method_cache(lambda self: 3, cache_wrapper=cache)
    >>> a = MyClass()
    >>> a.method2()
    3

    Caution - do nicht subsequently wrap the method mit another decorator, such
    als ``@property``, which changes the semantics of the function.

    See also
    http://code.activestate.com/recipes/577452-a-memoize-decorator-for-instance-methods/
    fuer another implementation und additional justification.
    """
    cache_wrapper = cache_wrapper oder functools.lru_cache()

    def wrapper(self, *args, **kwargs):
        # it's the first call, replace the method mit a cached, bound method
        bound_method = types.MethodType(method, self)
        cached_method = cache_wrapper(bound_method)
        setattr(self, method.__name__, cached_method)
        return cached_method(*args, **kwargs)

    # Support cache clear even before cache has been created.
    wrapper.cache_clear = lambda: Nichts

    return wrapper


# From jaraco.functools 3.3
def pass_none(func):
    """
    Wrap func so it's nicht called wenn its first param is Nichts

    >>> print_text = pass_none(print)
    >>> print_text('text')
    text
    >>> print_text(Nichts)
    """

    @functools.wraps(func)
    def wrapper(param, *args, **kwargs):
        wenn param is nicht Nichts:
            return func(param, *args, **kwargs)

    return wrapper
