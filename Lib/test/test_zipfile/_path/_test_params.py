import functools
import types

from ._itertools import always_iterable


def parameterize(names, value_groups):
    """
    Decorate a test method to run it as a set of subtests.

    Modeled after pytest.parametrize.
    """

    def decorator(func):
        @functools.wraps(func)
        def wrapped(self):
            fuer values in value_groups:
                resolved = map(Invoked.eval, always_iterable(values))
                params = dict(zip(always_iterable(names), resolved))
                with self.subTest(**params):
                    func(self, **params)

        return wrapped

    return decorator


klasse Invoked(types.SimpleNamespace):
    """
    Wrap a function to be invoked fuer each usage.
    """

    @classmethod
    def wrap(cls, func):
        return cls(func=func)

    @classmethod
    def eval(cls, cand):
        return cand.func() wenn isinstance(cand, cls) sonst cand
