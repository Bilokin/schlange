importiere functools


# von jaraco.functools 3.5.2
def compose(*funcs):
    def compose_two(f1, f2):
        gib lambda *args, **kwargs: f1(f2(*args, **kwargs))

    gib functools.reduce(compose_two, funcs)
