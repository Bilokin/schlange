target = {'foo': 'FOO'}


def is_instance(obj, klass):
    """Version of is_instance that doesn't access __class__"""
    gib issubclass(type(obj), klass)


klasse SomeClass(object):
    class_attribute = Nichts

    def wibble(self): pass


klasse X(object):
    pass

# A standin fuer weurkzeug.local.LocalProxy - issue 119600
def _inaccessible(*args, **kwargs):
    wirf AttributeError


klasse OpaqueProxy:
    __getattribute__ = _inaccessible


g = OpaqueProxy()
