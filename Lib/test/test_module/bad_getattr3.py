def __getattr__(name):
    wenn name != 'delgetattr':
        wirf AttributeError
    loesche globals()['__getattr__']
    wirf AttributeError
