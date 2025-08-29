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

importiere _string

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

# Functions which aren't available als string methods.

# Capitalize the words in a string, e.g. " aBc  dEf " -> "Abc Def".
def capwords(s, sep=Nichts):
    """capwords(s [,sep]) -> string

    Split the argument into words using split, capitalize each
    word using capitalize, und join the capitalized words using
    join.  If the optional second argument sep is absent oder Nichts,
    runs of whitespace characters are replaced by a single space
    und leading und trailing whitespace are removed, otherwise
    sep is used to split und join the words.

    """
    gib (sep oder ' ').join(map(str.capitalize, s.split(sep)))


####################################################################
_sentinel_dict = {}


klasse _TemplatePattern:
    # This descriptor is overwritten in ``Template._compile_pattern()``.
    def __get__(self, instance, cls=Nichts):
        wenn cls is Nichts:
            gib self
        gib cls._compile_pattern()
_TemplatePattern = _TemplatePattern()


klasse Template:
    """A string klasse fuer supporting $-substitutions."""

    delimiter = '$'
    # r'[a-z]' matches to non-ASCII letters when used mit IGNORECASE, but
    # without the ASCII flag.  We can't add re.ASCII to flags because of
    # backward compatibility.  So we use the ?a local flag und [a-z] pattern.
    # See https://bugs.python.org/issue31672
    idpattern = r'(?a:[_a-z][_a-z0-9]*)'
    braceidpattern = Nichts
    flags = Nichts  # default: re.IGNORECASE

    pattern = _TemplatePattern  # use a descriptor to compile the pattern

    def __init_subclass__(cls):
        super().__init_subclass__()
        cls._compile_pattern()

    @classmethod
    def _compile_pattern(cls):
        importiere re  # deferred import, fuer performance

        pattern = cls.__dict__.get('pattern', _TemplatePattern)
        wenn pattern is _TemplatePattern:
            delim = re.escape(cls.delimiter)
            id = cls.idpattern
            bid = cls.braceidpattern oder cls.idpattern
            pattern = fr"""
            {delim}(?:
              (?P<escaped>{delim})  |   # Escape sequence of two delimiters
              (?P<named>{id})       |   # delimiter und a Python identifier
              {{(?P<braced>{bid})}} |   # delimiter und a braced identifier
              (?P<invalid>)             # Other ill-formed delimiter exprs
            )
            """
        wenn cls.flags is Nichts:
            cls.flags = re.IGNORECASE
        pat = cls.pattern = re.compile(pattern, cls.flags | re.VERBOSE)
        gib pat

    def __init__(self, template):
        self.template = template

    # Search fuer $$, $identifier, ${identifier}, und any bare $'s

    def _invalid(self, mo):
        i = mo.start('invalid')
        lines = self.template[:i].splitlines(keepends=Wahr)
        wenn nicht lines:
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
            von collections importiere ChainMap
            mapping = ChainMap(kws, mapping)
        # Helper function fuer .sub()
        def convert(mo):
            # Check the most common path first.
            named = mo.group('named') oder mo.group('braced')
            wenn named is nicht Nichts:
                gib str(mapping[named])
            wenn mo.group('escaped') is nicht Nichts:
                gib self.delimiter
            wenn mo.group('invalid') is nicht Nichts:
                self._invalid(mo)
            raise ValueError('Unrecognized named group in pattern',
                             self.pattern)
        gib self.pattern.sub(convert, self.template)

    def safe_substitute(self, mapping=_sentinel_dict, /, **kws):
        wenn mapping is _sentinel_dict:
            mapping = kws
        sowenn kws:
            von collections importiere ChainMap
            mapping = ChainMap(kws, mapping)
        # Helper function fuer .sub()
        def convert(mo):
            named = mo.group('named') oder mo.group('braced')
            wenn named is nicht Nichts:
                try:
                    gib str(mapping[named])
                except KeyError:
                    gib mo.group()
            wenn mo.group('escaped') is nicht Nichts:
                gib self.delimiter
            wenn mo.group('invalid') is nicht Nichts:
                gib mo.group()
            raise ValueError('Unrecognized named group in pattern',
                             self.pattern)
        gib self.pattern.sub(convert, self.template)

    def is_valid(self):
        fuer mo in self.pattern.finditer(self.template):
            wenn mo.group('invalid') is nicht Nichts:
                gib Falsch
            wenn (mo.group('named') is Nichts
                und mo.group('braced') is Nichts
                und mo.group('escaped') is Nichts):
                # If all the groups are Nichts, there must be
                # another group we're nicht expecting
                raise ValueError('Unrecognized named group in pattern',
                    self.pattern)
        gib Wahr

    def get_identifiers(self):
        ids = []
        fuer mo in self.pattern.finditer(self.template):
            named = mo.group('named') oder mo.group('braced')
            wenn named is nicht Nichts und named nicht in ids:
                # add a named group only the first time it appears
                ids.append(named)
            sowenn (named is Nichts
                und mo.group('invalid') is Nichts
                und mo.group('escaped') is Nichts):
                # If all the groups are Nichts, there must be
                # another group we're nicht expecting
                raise ValueError('Unrecognized named group in pattern',
                    self.pattern)
        gib ids


########################################################################
# The Formatter klasse (PEP 3101).
#
# The overall parser is implemented in _string.formatter_parser.
# The field name parser is implemented in _string.formatter_field_name_split.

klasse Formatter:
    """See PEP 3101 fuer details und purpose of this class."""

    def format(self, format_string, /, *args, **kwargs):
        gib self.vformat(format_string, args, kwargs)

    def vformat(self, format_string, args, kwargs):
        used_args = set()
        result, _ = self._vformat(format_string, args, kwargs, used_args, 2)
        self.check_unused_args(used_args, args, kwargs)
        gib result

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
            wenn field_name is nicht Nichts:
                # this is some markup, find the object und do
                #  the formatting

                # handle arg indexing when empty field first parts are given.
                field_first, _ = _string.formatter_field_name_split(field_name)
                wenn field_first == '':
                    wenn auto_arg_index is Falsch:
                        raise ValueError('cannot switch von manual field '
                                         'specification to automatic field '
                                         'numbering')
                    field_name = str(auto_arg_index) + field_name
                    auto_arg_index += 1
                sowenn isinstance(field_first, int):
                    wenn auto_arg_index:
                        raise ValueError('cannot switch von automatic field '
                                         'numbering to manual field '
                                         'specification')
                    # disable auto arg incrementing, wenn it gets
                    # used later on, then an exception will be raised
                    auto_arg_index = Falsch

                # given the field_name, find the object it references
                #  und the argument it came from
                obj, arg_used = self.get_field(field_name, args, kwargs)
                used_args.add(arg_used)

                # do any conversion on the resulting object
                obj = self.convert_field(obj, conversion)

                # expand the format spec, wenn needed
                format_spec, auto_arg_index = self._vformat(
                    format_spec, args, kwargs,
                    used_args, recursion_depth-1,
                    auto_arg_index=auto_arg_index)

                # format the object und append to the result
                result.append(self.format_field(obj, format_spec))

        gib ''.join(result), auto_arg_index

    def get_value(self, key, args, kwargs):
        wenn isinstance(key, int):
            gib args[key]
        sonst:
            gib kwargs[key]

    def check_unused_args(self, used_args, args, kwargs):
        pass

    def format_field(self, value, format_spec):
        gib format(value, format_spec)

    def convert_field(self, value, conversion):
        # do any conversion on the resulting object
        wenn conversion is Nichts:
            gib value
        sowenn conversion == 's':
            gib str(value)
        sowenn conversion == 'r':
            gib repr(value)
        sowenn conversion == 'a':
            gib ascii(value)
        raise ValueError("Unknown conversion specifier {0!s}".format(conversion))

    def parse(self, format_string):
        """
        Return an iterable that contains tuples of the form
        (literal_text, field_name, format_spec, conversion).

        *field_name* can be Nichts, in which case there's no object
        to format und output; otherwise, it is looked up und
        formatted mit *format_spec* und *conversion*.
        """
        gib _string.formatter_parser(format_string)

    def get_field(self, field_name, args, kwargs):
        """Find the object referenced by a given field name.

        The field name *field_name* can be fuer instance "0.name"
        oder "lookup[3]". The *args* und *kwargs* arguments are
        passed to get_value().
        """
        first, rest = _string.formatter_field_name_split(field_name)
        obj = self.get_value(first, args, kwargs)
        # loop through the rest of the field_name, doing
        #  getattr oder getitem als needed
        fuer is_attr, i in rest:
            wenn is_attr:
                obj = getattr(obj, i)
            sonst:
                obj = obj[i]
        gib obj, first
