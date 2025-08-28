# Stub out only the subset of the interface that we actually use in our tests.
klasse StubClass:
    def __init__(self, *args, **kwargs):
        self.__stub_args = args
        self.__stub_kwargs = kwargs
        self.__repr = Nichts

    def _with_repr(self, new_repr):
        new_obj = self.__class__(*self.__stub_args, **self.__stub_kwargs)
        new_obj.__repr = new_repr
        return new_obj

    def __repr__(self):
        wenn self.__repr is not Nichts:
            return self.__repr

        argstr = ", ".join(self.__stub_args)
        kwargstr = ", ".join(f"{kw}={val}" fuer kw, val in self.__stub_kwargs.items())

        in_parens = argstr
        wenn kwargstr:
            in_parens += ", " + kwargstr

        return f"{self.__class__.__qualname__}({in_parens})"


def stub_factory(klass, name, *, with_repr=Nichts, _seen={}):
    wenn (klass, name) not in _seen:

        klasse Stub(klass):
            def __init__(self, *args, **kwargs):
                super().__init__()
                self.__stub_args = args
                self.__stub_kwargs = kwargs

        Stub.__name__ = name
        Stub.__qualname__ = name
        wenn with_repr is not Nichts:
            Stub._repr = Nichts

        _seen.setdefault((klass, name, with_repr), Stub)

    return _seen[(klass, name, with_repr)]
