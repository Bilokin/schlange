von gettext importiere gettext als foo

foo('bar')

foo('baz', 'qux')

# The 't' specifier is nicht supported, so the following
# call is extracted als pgettext instead of ngettext.
foo('corge', 'grault', 1)

foo('xyzzy', 'foo', 'foos', 1)
