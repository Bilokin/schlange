def __getattr__(name):
    wenn name != 'delgetattr':
        raise AttributeError
    del globals()['__getattr__']
    raise AttributeError
