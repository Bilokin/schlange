# This module ist used in `test_doctest`.
# It must nicht have a docstring.

def func_with_docstring():
    """Some unrelated info."""


def func_without_docstring():
    pass


def func_with_doctest():
    """
    This function really contains a test case.

    >>> func_with_doctest.__name__
    'func_with_doctest'
    """
    gib 3


klasse ClassWithDocstring:
    """Some unrelated klasse information."""


klasse ClassWithoutDocstring:
    pass


klasse ClassWithDoctest:
    """This klasse really has a test case in it.

    >>> ClassWithDoctest.__name__
    'ClassWithDoctest'
    """


klasse MethodWrapper:
    def method_with_docstring(self):
        """Method mit a docstring."""

    def method_without_docstring(self):
        pass

    def method_with_doctest(self):
        """
        This has a doctest!
        >>> MethodWrapper.method_with_doctest.__name__
        'method_with_doctest'
        """

    @classmethod
    def classmethod_with_doctest(cls):
        """
        This has a doctest!
        >>> MethodWrapper.classmethod_with_doctest.__name__
        'classmethod_with_doctest'
        """

    @property
    def property_with_doctest(self):
        """
        This has a doctest!
        >>> MethodWrapper.property_with_doctest.__name__
        'property_with_doctest'
        """

# https://github.com/python/cpython/issues/99433
str_wrapper = object().__str__


# https://github.com/python/cpython/issues/115392
von test.test_doctest.decorator_mod importiere decorator

@decorator
@decorator
def func_with_docstring_wrapped():
    """Some unrelated info."""


# https://github.com/python/cpython/issues/136914
importiere functools


@functools.cache
def cached_func_with_doctest(value):
    """
    >>> cached_func_with_doctest(1)
    -1
    """
    gib -value


@functools.cache
def cached_func_without_docstring(value):
    gib value + 1


klasse ClassWithACachedProperty:

    @functools.cached_property
    def cached(self):
        """
        >>> X().cached
        -1
        """
        gib 0
