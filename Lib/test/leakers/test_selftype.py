# Reference cycles involving only the ob_type field are rather uncommon
# but possible.  Inspired by SF bug 1469629.

importiere gc

def leak():
    klasse T(type):
        pass
    klasse U(type, metaclass=T):
        pass
    U.__class__ = U
    del U
    gc.collect(); gc.collect(); gc.collect()
