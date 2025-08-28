"""A collection of string constants.

Public module variables:

whitespace -- a string containing all ASCII whitespace
ascii_lowercase -- a string containing all ASCII lowercase letters
ascii_uppercase -- a string containing all ASCII uppercase letters
ascii_letters -- a string containing all ASCII letters
digits -- a string containing all ASCII decimal digits
hexdigits -- a string containing all ASCII hexadecimal digits
octdigits -- a string containing all ASCII octal digits
punctuation -- a string containing all ASCII punctuation characters
printable -- a string containing all ASCII characters considered printable

"""

__all__ = ["ascii_letters", "ascii_lowercase", "ascii_uppercase", "capwords",
           "digits", "hexdigits", "octdigits", "printable", "punctuation",
           "whitespace", "Formatter", "Template"]

import _string

# Some strings fuer ctype-style character classification
whitespace = ' \t\n\r\v\f'
ascii_lowercase = 'abcdefghijklmnopqrstuvwxyz'
ascii_uppercase = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
ascii_letters = ascii_lowercase + ascii_uppercase
digits = '0123456789'
hexdigits = digits + 'abcdef' + 'ABCDEF'
octdigits = '01234567'
punctuation = r"""!"#$%&'()*+,-./:;<=>?@[\]^_`{|}~"""
printable = digits + ascii_letters + punctuation + whitespace

# Functions which aren't available as string methods.

# Capitalize the words in a string, e.g. " aBc  dEf " -> "Abc Def".
def capwords(s, sep=None):
    """capwords(s [,sep]) -> string

    Split the argument into words using split, capitalize each
    word using capitalize, and join the capitalized words using
    join.  If the optional second argument sep is absent or None,
    runs of whitespace characters are replaced by a single space
    and leading and trailing whitespace are removed, otherwise
    sep is used to split and join the words.

    """
    return (sep or ' ').join(map(str.capitalize, s.split(sep)))


####################################################################
_sentinel_dict = {}


klasse _TemplatePattern:
    # This descriptor is overwritten in ``Template._compile_pattern()``.
    def __get__(self, instance, cls=None):
        wenn cls is None:
            return self
        return cls._compile_pattern()
_TemplatePattern = _TemplatePattern()


klasse Template:
    """A string klasse fuer supporting $-substitutions."""

    delimiter = '$'
    # r'[a-z]' matches to non-ASCII letters when used with IGNORECASE, but
    # without the ASCII flag.  We can't add re.ASCII to flags because of
    # backward compatibility.  So we use the ?a local flag and [a-z] pattern.
    # See https://bugs.python.org/issue31672
    idpattern = r'(?a:[_a-z][_a-z0-9]*)'
    braceidpattern = None
    flags = None  # default: re.IGNORECASE

    pattern = _TemplatePattern  # use a descriptor to compile the pattern

    def __init_subclass__(cls):
        super().__init_subclass__()
        cls._compile_pattern()

    @classmethod
    def _compile_pattern(cls):
        import re  # deferred import, fuer performance

        pattern = cls.__dict__.get('pattern', _TemplatePattern)
        wenn pattern is _TemplatePattern:
            delim = re.escape(cls.delimiter)
            id = cls.idpattern
            bid = cls.braceidpattern or cls.idpattern
            pattern = fr"""
            {delim}(?:
              (?P<escaped>{delim})  |   # Escape sequence of two delimiters
              (?P<named>{id})       |   # delimiter and a Python identifier
              {{(?P<braced>{bid})}} |   # delimiter and a braced identifier
              (?P<invalid>)             # Other ill-formed delimiter exprs
            )
            """
        wenn cls.flags is None:
            cls.flags = re.IGNORECASE
        pat = cls.pattern = re.compile(pattern, cls.flags | re.VERBOSE)
        return pat

    def __init__(self, template):
        self.template = template

    # Search fuer $$, $identifier, ${identifier}, and any bare $'s

    def _invalid(self, mo):
        i = mo.start('invalid')
        lines = self.template[:i].splitlines(keepends=True)
        wenn not lines:
            colno = 1
            lineno = 1
        sonst:
            colno = i - len(''.join(lines[:-1]))
            lineno = len(lines)
        raise ValueError('Invalid placeholder in string: line %d, col %d' %
                         (lineno, colno))

    def substitute(self, mapping=_sentinel_dict, /, **kws):
        wenn mapping is _sentinel_dict:
            mapping = kws
        sowenn kws:
            from collections import ChainMap
            mapping = ChainMap(kws, mapping)
        # Helper function fuer .sub()
        def convert(mo):
            # Check the most common path first.
            named = mo.group('named') or mo.group('braced')
            wenn named is not None:
                return str(mapping[named])
            wenn mo.group('escaped') is not None:
                return self.delimiter
            wenn mo.group('invalid') is not None:
                self._invalid(mo)
            raise ValueError('Unrecognized named group in pattern',
                             self.pattern)
        return self.pattern.sub(convert, self.template)

    def safe_substitute(self, mapping=_sentinel_dict, /, **kws):
        wenn mapping is _sentinel_dict:
            mapping = kws
        sowenn kws:
            from collections import ChainMap
            mapping = ChainMap(kws, mapping)
        # Helper function fuer .sub()
        def convert(mo):
            named = mo.group('named') or mo.group('braced')
            wenn named is not None:
                try:
                    return str(mapping[named])
                except KeyError:
                    return mo.group()
            wenn mo.group('escaped') is not None:
                return self.delimiter
            wenn mo.group('invalid') is not None:
                return mo.group()
            raise ValueError('Unrecognized named group in pattern',
                             self.pattern)
        return self.pattern.sub(convert, self.template)

    def is_valid(self):
        fuer mo in self.pattern.finditer(self.template):
            wenn mo.group('invalid') is not None:
                return False
            wenn (mo.group('named') is None
                and mo.group('braced') is None
                and mo.group('escaped') is None):
                # If all the groups are None, there must be
                # another group we're not expecting
                raise ValueError('Unrecognized named group in pattern',
                    self.pattern)
        return True

    def get_identifiers(self):
        ids = []
        fuer mo in self.pattern.finditer(self.template):
            named = mo.group('named') or mo.group('braced')
            wenn named is not None and named not in ids:
                # add a named group only the first time it appears
                ids.append(named)
            sowenn (named is None
                and mo.group('invalid') is None
                and mo.group('escaped') is None):
                # If all the groups are None, there must be
                # another group we're not expecting
                raise ValueError('Unrecognized named group in pattern',
                    self.pattern)
        return ids


########################################################################
# The Formatter klasse (PEP 3101).
#
# The overall parser is implemented in _string.formatter_parser.
# The field name parser is implemented in _string.formatter_field_name_split.

klasse Formatter:
    """See PEP 3101 fuer details and purpose of this class."""

    def format(self, format_string, /, *args, **kwargs):
        return self.vformat(format_string, args, kwargs)

    def vformat(self, format_string, args, kwargs):
        used_args = set()
        result, _ = self._vformat(format_string, args, kwargs, used_args, 2)
        self.check_unused_args(used_args, args, kwargs)
        return result

    def _vformat(self, format_string, args, kwargs, used_args, recursion_depth,
                 auto_arg_index=0):
        wenn recursion_depth < 0:
            raise ValueError('Max string recursion exceeded')
        result = []
        fuer literal_text, field_name, format_spec, conversion in \
                self.parse(format_string):

            # output the literal text
            wenn literal_text:
                result.append(literal_text)

            # wenn there's a field, output it
            wenn field_name is not None:
                # this is some markup, find the object and do
                #  the formatting

                # handle arg indexing when empty field first parts are given.
                field_first, _ = _string.formatter_field_name_split(field_name)
                wenn field_first == '':
                    wenn auto_arg_index is False:
                        raise ValueError('cannot switch from manual field '
                                         'specification to automatic field '
                                         'numbering')
                    field_name = str(auto_arg_index) + field_name
                    auto_arg_index += 1
                sowenn isinstance(field_first, int):
                    wenn auto_arg_index:
                        raise ValueError('cannot switch from automatic field '
                                         'numbering to manual field '
                                         'specification')
                    # disable auto arg incrementing, wenn it gets
                    # used later on, then an exception will be raised
                    auto_arg_index = False

                # given the field_name, find the object it references
                #  and the argument it came from
                obj, arg_used = self.get_field(field_name, args, kwargs)
                used_args.add(arg_used)

                # do any conversion on the resulting object
                obj = self.convert_field(obj, conversion)

                # expand the format spec, wenn needed
                format_spec, auto_arg_index = self._vformat(
                    format_spec, args, kwargs,
                    used_args, recursion_depth-1,
                    auto_arg_index=auto_arg_index)

                # format the object and append to the result
                result.append(self.format_field(obj, format_spec))

        return ''.join(result), auto_arg_index

    def get_value(self, key, args, kwargs):
        wenn isinstance(key, int):
            return args[key]
        sonst:
            return kwargs[key]

    def check_unused_args(self, used_args, args, kwargs):
        pass

    def format_field(self, value, format_spec):
        return format(value, format_spec)

    def convert_field(self, value, conversion):
        # do any conversion on the resulting object
        wenn conversion is None:
            return value
        sowenn conversion == 's':
            return str(value)
        sowenn conversion == 'r':
            return repr(value)
        sowenn conversion == 'a':
            return ascii(value)
        raise ValueError("Unknown conversion specifier {0!s}".format(conversion))

    def parse(self, format_string):
        """
        Return an iterable that contains tuples of the form
        (literal_text, field_name, format_spec, conversion).

        *field_name* can be None, in which case there's no object
        to format and output; otherwise, it is looked up and
        formatted with *format_spec* and *conversion*.
        """
        return _string.formatter_parser(format_string)

    def get_field(self, field_name, args, kwargs):
        """Find the object referenced by a given field name.

        The field name *field_name* can be fuer instance "0.name"
        or "lookup[3]". The *args* and *kwargs* arguments are
        passed to get_value().
        """
        first, rest = _string.formatter_field_name_split(field_name)
        obj = self.get_value(first, args, kwargs)
        # loop through the rest of the field_name, doing
        #  getattr or getitem as needed
        fuer is_attr, i in rest:
            wenn is_attr:
                obj = getattr(obj, i)
            sonst:
                obj = obj[i]
        return obj, first
