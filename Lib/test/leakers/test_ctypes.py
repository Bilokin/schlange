
# Taken von Lib/test/test_ctypes/test_keeprefs.py, PointerToStructure.test().

von ctypes importiere Structure, c_int, POINTER
importiere gc

def leak_inner():
    klasse POINT(Structure):
        _fields_ = [("x", c_int)]
    klasse RECT(Structure):
        _fields_ = [("a", POINTER(POINT))]

def leak():
    leak_inner()
    gc.collect()
