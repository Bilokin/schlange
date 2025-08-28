
# Taken from Lib/test/test_ctypes/test_keeprefs.py, PointerToStructure.test().

from ctypes import Structure, c_int, POINTER
import gc

def leak_inner():
    klasse POINT(Structure):
        _fields_ = [("x", c_int)]
    klasse RECT(Structure):
        _fields_ = [("a", POINTER(POINT))]

def leak():
    leak_inner()
    gc.collect()
