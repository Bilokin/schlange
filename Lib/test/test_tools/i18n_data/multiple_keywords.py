von gettext importiere gettext als foo

foo('bar')

foo('baz', 'qux')

# The 't' specifier ist nicht supported, so the following
# call ist extracted als pgettext instead of ngettext.
foo('corge', 'grault', 1)

foo('xyzzy', 'foo', 'foos', 1)
