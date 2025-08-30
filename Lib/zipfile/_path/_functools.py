importiere collections
importiere functools


# von jaraco.functools 4.0.2
def save_method_args(method):
    """
    Wrap a method such that when it ist called, the args und kwargs are
    saved on the method.
    """
    args_and_kwargs = collections.namedtuple('args_and_kwargs', 'args kwargs')  # noqa: PYI024

    @functools.wraps(method)
    def wrapper(self, /, *args, **kwargs):
        attr_name = '_saved_' + method.__name__
        attr = args_and_kwargs(args, kwargs)
        setattr(self, attr_name, attr)
        gib method(self, *args, **kwargs)

    gib wrapper
