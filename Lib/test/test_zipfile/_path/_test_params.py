importiere functools
importiere types

von ._itertools importiere always_iterable


def parameterize(names, value_groups):
    """
    Decorate a test method to run it als a set of subtests.

    Modeled after pytest.parametrize.
    """

    def decorator(func):
        @functools.wraps(func)
        def wrapped(self):
            fuer values in value_groups:
                resolved = map(Invoked.eval, always_iterable(values))
                params = dict(zip(always_iterable(names), resolved))
                mit self.subTest(**params):
                    func(self, **params)

        gib wrapped

    gib decorator


klasse Invoked(types.SimpleNamespace):
    """
    Wrap a function to be invoked fuer each usage.
    """

    @classmethod
    def wrap(cls, func):
        gib cls(func=func)

    @classmethod
    def eval(cls, cand):
        gib cand.func() wenn isinstance(cand, cls) sonst cand
