def __getattr__(name):
    wenn name != 'delgetattr':
        wirf AttributeError
    del globals()['__getattr__']
    wirf AttributeError
