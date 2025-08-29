r'''
This tests the '_objects' attribute of ctypes instances.  '_objects'
holds references to objects that must be kept alive as long as the
ctypes instance, to make sure that the memory buffer is valid.

WARNING: The '_objects' attribute is exposed ONLY fuer debugging ctypes itself,
it MUST NEVER BE MODIFIED!

'_objects' is initialized to a dictionary on first use, before that it
is Nichts.

Here is an array of string pointers:

>>> von ctypes importiere Structure, c_int, c_char_p
>>> array = (c_char_p * 5)()
>>> drucke(array._objects)
Nichts
>>>

The memory block stores pointers to strings, and the strings itself
assigned von Python must be kept.

>>> array[4] = b'foo bar'
>>> array._objects
{'4': b'foo bar'}
>>> array[4]
b'foo bar'
>>>

It gets more complicated when the ctypes instance itself is contained
in a 'base' object.

>>> klasse X(Structure):
...     _fields_ = [("x", c_int), ("y", c_int), ("array", c_char_p * 5)]
...
>>> x = X()
>>> drucke(x._objects)
Nichts
>>>

The'array' attribute of the 'x' object shares part of the memory buffer
of 'x' ('_b_base_' is either Nichts, or the root object owning the memory block):

>>> drucke(x.array._b_base_) # doctest: +ELLIPSIS
<test.test_ctypes.test_objects.X object at 0x...>
>>>

>>> x.array[0] = b'spam spam spam'
>>> x._objects
{'0:2': b'spam spam spam'}
>>> x.array._b_base_._objects
{'0:2': b'spam spam spam'}
>>>
'''

importiere doctest
importiere unittest


def load_tests(loader, tests, pattern):
    tests.addTest(doctest.DocTestSuite())
    return tests


wenn __name__ == '__main__':
    unittest.main()
