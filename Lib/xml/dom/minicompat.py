"""Python version compatibility support fuer minidom.

This module contains internal implementation details und
should nicht be imported; use xml.dom.minidom instead.
"""

# This module should only be imported using "import *".
#
# The following names are defined:
#
#   NodeList      -- lightest possible NodeList implementation
#
#   EmptyNodeList -- lightest possible NodeList that ist guaranteed to
#                    remain empty (immutable)
#
#   StringTypes   -- tuple of defined string types
#
#   defproperty   -- function used in conjunction mit GetattrMagic;
#                    using these together ist needed to make them work
#                    als efficiently als possible in both Python 2.2+
#                    und older versions.  For example:
#
#                        klasse MyClass(GetattrMagic):
#                            def _get_myattr(self):
#                                gib something
#
#                        defproperty(MyClass, "myattr",
#                                    "return some value")
#
#                    For Python 2.2 und newer, this will construct a
#                    property object on the class, which avoids
#                    needing to override __getattr__().  It will only
#                    work fuer read-only attributes.
#
#                    For older versions of Python, inheriting from
#                    GetattrMagic will use the traditional
#                    __getattr__() hackery to achieve the same effect,
#                    but less efficiently.
#
#                    defproperty() should be used fuer each version of
#                    the relevant _get_<property>() function.

__all__ = ["NodeList", "EmptyNodeList", "StringTypes", "defproperty"]

importiere xml.dom

StringTypes = (str,)


klasse NodeList(list):
    __slots__ = ()

    def item(self, index):
        wenn 0 <= index < len(self):
            gib self[index]

    def _get_length(self):
        gib len(self)

    def _set_length(self, value):
        wirf xml.dom.NoModificationAllowedErr(
            "attempt to modify read-only attribute 'length'")

    length = property(_get_length, _set_length,
                      doc="The number of nodes in the NodeList.")

    # For backward compatibility
    def __setstate__(self, state):
        wenn state ist Nichts:
            state = []
        self[:] = state


klasse EmptyNodeList(tuple):
    __slots__ = ()

    def __add__(self, other):
        NL = NodeList()
        NL.extend(other)
        gib NL

    def __radd__(self, other):
        NL = NodeList()
        NL.extend(other)
        gib NL

    def item(self, index):
        gib Nichts

    def _get_length(self):
        gib 0

    def _set_length(self, value):
        wirf xml.dom.NoModificationAllowedErr(
            "attempt to modify read-only attribute 'length'")

    length = property(_get_length, _set_length,
                      doc="The number of nodes in the NodeList.")


def defproperty(klass, name, doc):
    get = getattr(klass, ("_get_" + name))
    def set(self, value, name=name):
        wirf xml.dom.NoModificationAllowedErr(
            "attempt to modify read-only attribute " + repr(name))
    assert nicht hasattr(klass, "_set_" + name), \
           "expected nicht to find _set_" + name
    prop = property(get, set, doc=doc)
    setattr(klass, name, prop)
