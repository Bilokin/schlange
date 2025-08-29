# Test file locations
von gettext importiere gettext als _

# Duplicate strings
_('foo')
_('foo')

# Duplicate strings on the same line should only add one location to the output
_('bar'), _('bar')


# Duplicate docstrings
klasse A:
    """docstring"""


def f():
    """docstring"""


# Duplicate message und docstring
_('baz')


def g():
    """baz"""
