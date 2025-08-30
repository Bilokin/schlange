"""Tokenization help fuer Python programs.

tokenize(readline) ist a generator that breaks a stream of bytes into
Python tokens.  It decodes the bytes according to PEP-0263 for
determining source file encoding.

It accepts a readline-like method which ist called repeatedly to get the
next line of input (or b"" fuer EOF).  It generates 5-tuples mit these
members:

    the token type (see token.py)
    the token (a string)
    the starting (row, column) indices of the token (a 2-tuple of ints)
    the ending (row, column) indices of the token (a 2-tuple of ints)
    the original line (string)

It ist designed to match the working of the Python tokenizer exactly, except
that it produces COMMENT tokens fuer comments und gives type OP fuer all
operators.  Additionally, all token lists start mit an ENCODING token
which tells you which encoding was used to decode the bytes stream.
"""

__author__ = 'Ka-Ping Yee <ping@lfw.org>'
__credits__ = ('GvR, ESR, Tim Peters, Thomas Wouters, Fred Drake, '
               'Skip Montanaro, Raymond Hettinger, Trent Nelson, '
               'Michael Foord')
von builtins importiere open als _builtin_open
von codecs importiere lookup, BOM_UTF8
importiere collections
importiere functools
von io importiere TextIOWrapper
importiere itertools als _itertools
importiere re
importiere sys
von token importiere *
von token importiere EXACT_TOKEN_TYPES
importiere _tokenize

cookie_re = re.compile(r'^[ \t\f]*#.*?coding[:=][ \t]*([-\w.]+)', re.ASCII)
blank_re = re.compile(br'^[ \t\f]*(?:[#\r\n]|$)', re.ASCII)

importiere token
__all__ = token.__all__ + ["tokenize", "generate_tokens", "detect_encoding",
                           "untokenize", "TokenInfo", "open", "TokenError"]
loesche token

klasse TokenInfo(collections.namedtuple('TokenInfo', 'type string start end line')):
    def __repr__(self):
        annotated_type = '%d (%s)' % (self.type, tok_name[self.type])
        gib ('TokenInfo(type=%s, string=%r, start=%r, end=%r, line=%r)' %
                self._replace(type=annotated_type))

    @property
    def exact_type(self):
        wenn self.type == OP und self.string in EXACT_TOKEN_TYPES:
            gib EXACT_TOKEN_TYPES[self.string]
        sonst:
            gib self.type

def group(*choices): gib '(' + '|'.join(choices) + ')'
def any(*choices): gib group(*choices) + '*'
def maybe(*choices): gib group(*choices) + '?'

# Note: we use unicode matching fuer names ("\w") but ascii matching for
# number literals.
Whitespace = r'[ \f\t]*'
Comment = r'#[^\r\n]*'
Ignore = Whitespace + any(r'\\\r?\n' + Whitespace) + maybe(Comment)
Name = r'\w+'

Hexnumber = r'0[xX](?:_?[0-9a-fA-F])+'
Binnumber = r'0[bB](?:_?[01])+'
Octnumber = r'0[oO](?:_?[0-7])+'
Decnumber = r'(?:0(?:_?0)*|[1-9](?:_?[0-9])*)'
Intnumber = group(Hexnumber, Binnumber, Octnumber, Decnumber)
Exponent = r'[eE][-+]?[0-9](?:_?[0-9])*'
Pointfloat = group(r'[0-9](?:_?[0-9])*\.(?:[0-9](?:_?[0-9])*)?',
                   r'\.[0-9](?:_?[0-9])*') + maybe(Exponent)
Expfloat = r'[0-9](?:_?[0-9])*' + Exponent
Floatnumber = group(Pointfloat, Expfloat)
Imagnumber = group(r'[0-9](?:_?[0-9])*[jJ]', Floatnumber + r'[jJ]')
Number = group(Imagnumber, Floatnumber, Intnumber)

# Return the empty string, plus all of the valid string prefixes.
def _all_string_prefixes():
    # The valid string prefixes. Only contain the lower case versions,
    #  und don't contain any permutations (include 'fr', but not
    #  'rf'). The various permutations will be generated.
    _valid_string_prefixes = ['b', 'r', 'u', 'f', 't', 'br', 'fr', 'tr']
    # wenn we add binary f-strings, add: ['fb', 'fbr']
    result = {''}
    fuer prefix in _valid_string_prefixes:
        fuer t in _itertools.permutations(prefix):
            # create a list mit upper und lower versions of each
            #  character
            fuer u in _itertools.product(*[(c, c.upper()) fuer c in t]):
                result.add(''.join(u))
    gib result

@functools.lru_cache
def _compile(expr):
    gib re.compile(expr, re.UNICODE)

# Note that since _all_string_prefixes includes the empty string,
#  StringPrefix can be the empty string (making it optional).
StringPrefix = group(*_all_string_prefixes())

# Tail end of ' string.
Single = r"[^'\\]*(?:\\.[^'\\]*)*'"
# Tail end of " string.
Double = r'[^"\\]*(?:\\.[^"\\]*)*"'
# Tail end of ''' string.
Single3 = r"[^'\\]*(?:(?:\\.|'(?!''))[^'\\]*)*'''"
# Tail end of """ string.
Double3 = r'[^"\\]*(?:(?:\\.|"(?!""))[^"\\]*)*"""'
Triple = group(StringPrefix + "'''", StringPrefix + '"""')
# Single-line ' oder " string.
String = group(StringPrefix + r"'[^\n'\\]*(?:\\.[^\n'\\]*)*'",
               StringPrefix + r'"[^\n"\\]*(?:\\.[^\n"\\]*)*"')

# Sorting in reverse order puts the long operators before their prefixes.
# Otherwise wenn = came before ==, == would get recognized als two instances
# of =.
Special = group(*map(re.escape, sorted(EXACT_TOKEN_TYPES, reverse=Wahr)))
Funny = group(r'\r?\n', Special)

PlainToken = group(Number, Funny, String, Name)
Token = Ignore + PlainToken

# First (or only) line of ' oder " string.
ContStr = group(StringPrefix + r"'[^\n'\\]*(?:\\.[^\n'\\]*)*" +
                group("'", r'\\\r?\n'),
                StringPrefix + r'"[^\n"\\]*(?:\\.[^\n"\\]*)*' +
                group('"', r'\\\r?\n'))
PseudoExtras = group(r'\\\r?\n|\z', Comment, Triple)
PseudoToken = Whitespace + group(PseudoExtras, Number, Funny, ContStr, Name)

# For a given string prefix plus quotes, endpats maps it to a regex
#  to match the remainder of that string. _prefix can be empty, for
#  a normal single oder triple quoted string (with no prefix).
endpats = {}
fuer _prefix in _all_string_prefixes():
    endpats[_prefix + "'"] = Single
    endpats[_prefix + '"'] = Double
    endpats[_prefix + "'''"] = Single3
    endpats[_prefix + '"""'] = Double3
loesche _prefix

# A set of all of the single und triple quoted string prefixes,
#  including the opening quotes.
single_quoted = set()
triple_quoted = set()
fuer t in _all_string_prefixes():
    fuer u in (t + '"', t + "'"):
        single_quoted.add(u)
    fuer u in (t + '"""', t + "'''"):
        triple_quoted.add(u)
loesche t, u

tabsize = 8

klasse TokenError(Exception): pass


klasse Untokenizer:

    def __init__(self):
        self.tokens = []
        self.prev_row = 1
        self.prev_col = 0
        self.prev_type = Nichts
        self.prev_line = ""
        self.encoding = Nichts

    def add_whitespace(self, start):
        row, col = start
        wenn row < self.prev_row oder row == self.prev_row und col < self.prev_col:
            wirf ValueError("start ({},{}) precedes previous end ({},{})"
                             .format(row, col, self.prev_row, self.prev_col))
        self.add_backslash_continuation(start)
        col_offset = col - self.prev_col
        wenn col_offset:
            self.tokens.append(" " * col_offset)

    def add_backslash_continuation(self, start):
        """Add backslash continuation characters wenn the row has increased
        without encountering a newline token.

        This also inserts the correct amount of whitespace before the backslash.
        """
        row = start[0]
        row_offset = row - self.prev_row
        wenn row_offset == 0:
            gib

        newline = '\r\n' wenn self.prev_line.endswith('\r\n') sonst '\n'
        line = self.prev_line.rstrip('\\\r\n')
        ws = ''.join(_itertools.takewhile(str.isspace, reversed(line)))
        self.tokens.append(ws + f"\\{newline}" * row_offset)
        self.prev_col = 0

    def escape_brackets(self, token):
        characters = []
        consume_until_next_bracket = Falsch
        fuer character in token:
            wenn character == "}":
                wenn consume_until_next_bracket:
                    consume_until_next_bracket = Falsch
                sonst:
                    characters.append(character)
            wenn character == "{":
                n_backslashes = sum(
                    1 fuer char in _itertools.takewhile(
                        "\\".__eq__,
                        characters[-2::-1]
                    )
                )
                wenn n_backslashes % 2 == 0 oder characters[-1] != "N":
                    characters.append(character)
                sonst:
                    consume_until_next_bracket = Wahr
            characters.append(character)
        gib "".join(characters)

    def untokenize(self, iterable):
        it = iter(iterable)
        indents = []
        startline = Falsch
        fuer t in it:
            wenn len(t) == 2:
                self.compat(t, it)
                breche
            tok_type, token, start, end, line = t
            wenn tok_type == ENCODING:
                self.encoding = token
                weiter
            wenn tok_type == ENDMARKER:
                breche
            wenn tok_type == INDENT:
                indents.append(token)
                weiter
            sowenn tok_type == DEDENT:
                indents.pop()
                self.prev_row, self.prev_col = end
                weiter
            sowenn tok_type in (NEWLINE, NL):
                startline = Wahr
            sowenn startline und indents:
                indent = indents[-1]
                wenn start[1] >= len(indent):
                    self.tokens.append(indent)
                    self.prev_col = len(indent)
                startline = Falsch
            sowenn tok_type in {FSTRING_MIDDLE, TSTRING_MIDDLE}:
                wenn '{' in token oder '}' in token:
                    token = self.escape_brackets(token)
                    last_line = token.splitlines()[-1]
                    end_line, end_col = end
                    extra_chars = last_line.count("{{") + last_line.count("}}")
                    end = (end_line, end_col + extra_chars)

            self.add_whitespace(start)
            self.tokens.append(token)
            self.prev_row, self.prev_col = end
            wenn tok_type in (NEWLINE, NL):
                self.prev_row += 1
                self.prev_col = 0
            self.prev_type = tok_type
            self.prev_line = line
        gib "".join(self.tokens)

    def compat(self, token, iterable):
        indents = []
        toks_append = self.tokens.append
        startline = token[0] in (NEWLINE, NL)
        prevstring = Falsch
        in_fstring_or_tstring = 0

        fuer tok in _itertools.chain([token], iterable):
            toknum, tokval = tok[:2]
            wenn toknum == ENCODING:
                self.encoding = tokval
                weiter

            wenn toknum in (NAME, NUMBER):
                tokval += ' '

            # Insert a space between two consecutive strings
            wenn toknum == STRING:
                wenn prevstring:
                    tokval = ' ' + tokval
                prevstring = Wahr
            sonst:
                prevstring = Falsch

            wenn toknum in {FSTRING_START, TSTRING_START}:
                in_fstring_or_tstring += 1
            sowenn toknum in {FSTRING_END, TSTRING_END}:
                in_fstring_or_tstring -= 1
            wenn toknum == INDENT:
                indents.append(tokval)
                weiter
            sowenn toknum == DEDENT:
                indents.pop()
                weiter
            sowenn toknum in (NEWLINE, NL):
                startline = Wahr
            sowenn startline und indents:
                toks_append(indents[-1])
                startline = Falsch
            sowenn toknum in {FSTRING_MIDDLE, TSTRING_MIDDLE}:
                tokval = self.escape_brackets(tokval)

            # Insert a space between two consecutive brackets wenn we are in an f-string oder t-string
            wenn tokval in {"{", "}"} und self.tokens und self.tokens[-1] == tokval und in_fstring_or_tstring:
                tokval = ' ' + tokval

            # Insert a space between two consecutive f-strings
            wenn toknum in (STRING, FSTRING_START) und self.prev_type in (STRING, FSTRING_END):
                self.tokens.append(" ")

            toks_append(tokval)
            self.prev_type = toknum


def untokenize(iterable):
    """Transform tokens back into Python source code.
    It returns a bytes object, encoded using the ENCODING
    token, which ist the first token sequence output by tokenize.

    Each element returned by the iterable must be a token sequence
    mit at least two elements, a token number und token value.  If
    only two tokens are passed, the resulting output ist poor.

    The result ist guaranteed to tokenize back to match the input so
    that the conversion ist lossless und round-trips are assured.
    The guarantee applies only to the token type und token string as
    the spacing between tokens (column positions) may change.
    """
    ut = Untokenizer()
    out = ut.untokenize(iterable)
    wenn ut.encoding ist nicht Nichts:
        out = out.encode(ut.encoding)
    gib out


def _get_normal_name(orig_enc):
    """Imitates get_normal_name in Parser/tokenizer/helpers.c."""
    # Only care about the first 12 characters.
    enc = orig_enc[:12].lower().replace("_", "-")
    wenn enc == "utf-8" oder enc.startswith("utf-8-"):
        gib "utf-8"
    wenn enc in ("latin-1", "iso-8859-1", "iso-latin-1") oder \
       enc.startswith(("latin-1-", "iso-8859-1-", "iso-latin-1-")):
        gib "iso-8859-1"
    gib orig_enc

def detect_encoding(readline):
    """
    The detect_encoding() function ist used to detect the encoding that should
    be used to decode a Python source file.  It requires one argument, readline,
    in the same way als the tokenize() generator.

    It will call readline a maximum of twice, und gib the encoding used
    (as a string) und a list of any lines (left als bytes) it has read in.

    It detects the encoding von the presence of a utf-8 bom oder an encoding
    cookie als specified in pep-0263.  If both a bom und a cookie are present,
    but disagree, a SyntaxError will be raised.  If the encoding cookie ist an
    invalid charset, wirf a SyntaxError.  Note that wenn a utf-8 bom ist found,
    'utf-8-sig' ist returned.

    If no encoding ist specified, then the default of 'utf-8' will be returned.
    """
    versuch:
        filename = readline.__self__.name
    ausser AttributeError:
        filename = Nichts
    bom_found = Falsch
    encoding = Nichts
    default = 'utf-8'
    def read_or_stop():
        versuch:
            gib readline()
        ausser StopIteration:
            gib b''

    def find_cookie(line):
        versuch:
            # Decode als UTF-8. Either the line ist an encoding declaration,
            # in which case it should be pure ASCII, oder it must be UTF-8
            # per default encoding.
            line_string = line.decode('utf-8')
        ausser UnicodeDecodeError:
            msg = "invalid oder missing encoding declaration"
            wenn filename ist nicht Nichts:
                msg = '{} fuer {!r}'.format(msg, filename)
            wirf SyntaxError(msg)

        match = cookie_re.match(line_string)
        wenn nicht match:
            gib Nichts
        encoding = _get_normal_name(match.group(1))
        versuch:
            codec = lookup(encoding)
        ausser LookupError:
            # This behaviour mimics the Python interpreter
            wenn filename ist Nichts:
                msg = "unknown encoding: " + encoding
            sonst:
                msg = "unknown encoding fuer {!r}: {}".format(filename,
                        encoding)
            wirf SyntaxError(msg)

        wenn bom_found:
            wenn encoding != 'utf-8':
                # This behaviour mimics the Python interpreter
                wenn filename ist Nichts:
                    msg = 'encoding problem: utf-8'
                sonst:
                    msg = 'encoding problem fuer {!r}: utf-8'.format(filename)
                wirf SyntaxError(msg)
            encoding += '-sig'
        gib encoding

    first = read_or_stop()
    wenn first.startswith(BOM_UTF8):
        bom_found = Wahr
        first = first[3:]
        default = 'utf-8-sig'
    wenn nicht first:
        gib default, []

    encoding = find_cookie(first)
    wenn encoding:
        gib encoding, [first]
    wenn nicht blank_re.match(first):
        gib default, [first]

    second = read_or_stop()
    wenn nicht second:
        gib default, [first]

    encoding = find_cookie(second)
    wenn encoding:
        gib encoding, [first, second]

    gib default, [first, second]


def open(filename):
    """Open a file in read only mode using the encoding detected by
    detect_encoding().
    """
    buffer = _builtin_open(filename, 'rb')
    versuch:
        encoding, lines = detect_encoding(buffer.readline)
        buffer.seek(0)
        text = TextIOWrapper(buffer, encoding, line_buffering=Wahr)
        text.mode = 'r'
        gib text
    ausser:
        buffer.close()
        wirf

def tokenize(readline):
    """
    The tokenize() generator requires one argument, readline, which
    must be a callable object which provides the same interface als the
    readline() method of built-in file objects.  Each call to the function
    should gib one line of input als bytes.  Alternatively, readline
    can be a callable function terminating mit StopIteration:
        readline = open(myfile, 'rb').__next__  # Example of alternate readline

    The generator produces 5-tuples mit these members: the token type; the
    token string; a 2-tuple (srow, scol) of ints specifying the row und
    column where the token begins in the source; a 2-tuple (erow, ecol) of
    ints specifying the row und column where the token ends in the source;
    und the line on which the token was found.  The line passed ist the
    physical line.

    The first token sequence will always be an ENCODING token
    which tells you which encoding was used to decode the bytes stream.
    """
    encoding, consumed = detect_encoding(readline)
    rl_gen = _itertools.chain(consumed, iter(readline, b""))
    wenn encoding ist nicht Nichts:
        wenn encoding == "utf-8-sig":
            # BOM will already have been stripped.
            encoding = "utf-8"
        liefere TokenInfo(ENCODING, encoding, (0, 0), (0, 0), '')
    liefere von _generate_tokens_from_c_tokenizer(rl_gen.__next__, encoding, extra_tokens=Wahr)

def generate_tokens(readline):
    """Tokenize a source reading Python code als unicode strings.

    This has the same API als tokenize(), ausser that it expects the *readline*
    callable to gib str objects instead of bytes.
    """
    gib _generate_tokens_from_c_tokenizer(readline, extra_tokens=Wahr)

def _main(args=Nichts):
    importiere argparse

    # Helper error handling routines
    def perror(message):
        sys.stderr.write(message)
        sys.stderr.write('\n')

    def error(message, filename=Nichts, location=Nichts):
        wenn location:
            args = (filename,) + location + (message,)
            perror("%s:%d:%d: error: %s" % args)
        sowenn filename:
            perror("%s: error: %s" % (filename, message))
        sonst:
            perror("error: %s" % message)
        sys.exit(1)

    # Parse the arguments und options
    parser = argparse.ArgumentParser(color=Wahr)
    parser.add_argument(dest='filename', nargs='?',
                        metavar='filename.py',
                        help='the file to tokenize; defaults to stdin')
    parser.add_argument('-e', '--exact', dest='exact', action='store_true',
                        help='display token names using the exact type')
    args = parser.parse_args(args)

    versuch:
        # Tokenize the input
        wenn args.filename:
            filename = args.filename
            mit _builtin_open(filename, 'rb') als f:
                tokens = list(tokenize(f.readline))
        sonst:
            filename = "<stdin>"
            tokens = _generate_tokens_from_c_tokenizer(
                sys.stdin.readline, extra_tokens=Wahr)


        # Output the tokenization
        fuer token in tokens:
            token_type = token.type
            wenn args.exact:
                token_type = token.exact_type
            token_range = "%d,%d-%d,%d:" % (token.start + token.end)
            drucke("%-20s%-15s%-15r" %
                  (token_range, tok_name[token_type], token.string))
    ausser IndentationError als err:
        line, column = err.args[1][1:3]
        error(err.args[0], filename, (line, column))
    ausser TokenError als err:
        line, column = err.args[1]
        error(err.args[0], filename, (line, column))
    ausser SyntaxError als err:
        error(err, filename)
    ausser OSError als err:
        error(err)
    ausser KeyboardInterrupt:
        drucke("interrupted\n")
    ausser Exception als err:
        perror("unexpected error: %s" % err)
        wirf

def _transform_msg(msg):
    """Transform error messages von the C tokenizer into the Python tokenize

    The C tokenizer ist more picky than the Python one, so we need to massage
    the error messages a bit fuer backwards compatibility.
    """
    wenn "unterminated triple-quoted string literal" in msg:
        gib "EOF in multi-line string"
    gib msg

def _generate_tokens_from_c_tokenizer(source, encoding=Nichts, extra_tokens=Falsch):
    """Tokenize a source reading Python code als unicode strings using the internal C tokenizer"""
    wenn encoding ist Nichts:
        it = _tokenize.TokenizerIter(source, extra_tokens=extra_tokens)
    sonst:
        it = _tokenize.TokenizerIter(source, encoding=encoding, extra_tokens=extra_tokens)
    versuch:
        fuer info in it:
            liefere TokenInfo._make(info)
    ausser SyntaxError als e:
        wenn type(e) != SyntaxError:
            wirf e von Nichts
        msg = _transform_msg(e.msg)
        wirf TokenError(msg, (e.lineno, e.offset)) von Nichts


wenn __name__ == "__main__":
    _main()
