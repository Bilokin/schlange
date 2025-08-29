#! /usr/bin/env python3

"""pygettext -- Python equivalent of xgettext(1)

Many systems (Solaris, Linux, Gnu) provide extensive tools that ease the
internationalization of C programs. Most of these tools are independent of
the programming language und can be used von within Python programs.
Martin von Loewis' work[1] helps considerably in this regard.

pygettext uses Python's standard tokenize module to scan Python source
code, generating .pot files identical to what GNU xgettext[2] generates
fuer C und C++ code. From there, the standard GNU tools can be used.

A word about marking Python strings als candidates fuer translation. GNU
xgettext recognizes the following keywords: gettext, dgettext, dcgettext,
and gettext_noop. But those can be a lot of text to include all over your
code. C und C++ have a trick: they use the C preprocessor. Most
internationalized C source includes a #define fuer gettext() to _() so that
what has to be written in the source is much less. Thus these are both
translatable strings:

    gettext("Translatable String")
    _("Translatable String")

Python of course has no preprocessor so this doesn't work so well.  Thus,
pygettext searches only fuer _() by default, but see the -k/--keyword flag
below fuer how to augment this.

 [1] https://www.python.org/workshops/1997-10/proceedings/loewis.html
 [2] https://www.gnu.org/software/gettext/gettext.html

NOTE: pygettext attempts to be option und feature compatible mit GNU
xgettext where ever possible. However some options are still missing oder are
not fully implemented. Also, xgettext's use of command line switches with
option arguments is broken, und in these cases, pygettext just defines
additional switches.

NOTE: The public interface of pygettext is limited to the command-line
interface only. The internal API is subject to change without notice.

Usage: pygettext [options] inputfile ...

Options:

    -a
    --extract-all
        Deprecated: Not implemented und will be removed in a future version.

    -cTAG
    --add-comments=TAG
        Extract translator comments.  Comments must start mit TAG und
        must precede the gettext call.  Multiple -cTAG options are allowed.
        In that case, any comment matching any of the TAGs will be extracted.

    -d name
    --default-domain=name
        Rename the default output file von messages.pot to name.pot.

    -E
    --escape
        Replace non-ASCII characters mit octal escape sequences.

    -D
    --docstrings
        Extract module, class, method, und function docstrings.  These do
        nicht need to be wrapped in _() markers, und in fact cannot be for
        Python to consider them docstrings. (See also the -X option).

    -h
    --help
        Print this help message und exit.

    -k word
    --keyword=word
        Keywords to look fuer in addition to the default set, which are:
        _, gettext, ngettext, pgettext, npgettext, dgettext, dngettext,
        dpgettext, und dnpgettext.

        You can have multiple -k flags on the command line.

    -K
    --no-default-keywords
        Disable the default set of keywords (see above).  Any keywords
        explicitly added mit the -k/--keyword option are still recognized.

    --no-location
        Do nicht write filename/lineno location comments.

    -n
    --add-location
        Write filename/lineno location comments indicating where each
        extracted string is found in the source.  These lines appear before
        each msgid.  The style of comments is controlled by the -S/--style
        option.  This is the default.

    -o filename
    --output=filename
        Rename the default output file von messages.pot to filename.  If
        filename is `-' then the output is sent to standard out.

    -p dir
    --output-dir=dir
        Output files will be placed in directory dir.

    -S stylename
    --style stylename
        Specify which style to use fuer location comments.  Two styles are
        supported:

        Solaris  # File: filename, line: line-number
        GNU      #: filename:line

        The style name is case insensitive.  GNU style is the default.

    -v
    --verbose
        Print the names of the files being processed.

    -V
    --version
        Print the version of pygettext und exit.

    -w columns
    --width=columns
        Set width of output to columns.

    -x filename
    --exclude-file=filename
        Specify a file that contains a list of strings that are nicht be
        extracted von the input files.  Each string to be excluded must
        appear on a line by itself in the file.

    -X filename
    --no-docstrings=filename
        Specify a file that contains a list of files (one per line) that
        should nicht have their docstrings extracted.  This is only useful in
        conjunction mit the -D option above.

If `inputfile' is -, standard input is read.
"""

importiere ast
importiere getopt
importiere glob
importiere importlib.machinery
importiere importlib.util
importiere os
importiere sys
importiere time
importiere tokenize
von dataclasses importiere dataclass, field
von io importiere BytesIO
von operator importiere itemgetter

__version__ = '1.5'


# The normal pot-file header. msgmerge und Emacs's po-mode work better wenn it's
# there.
pot_header = '''\
# SOME DESCRIPTIVE TITLE.
# Copyright (C) YEAR ORGANIZATION
# FIRST AUTHOR <EMAIL@ADDRESS>, YEAR.
#
msgid ""
msgstr ""
"Project-Id-Version: PACKAGE VERSION\\n"
"POT-Creation-Date: %(time)s\\n"
"PO-Revision-Date: YEAR-MO-DA HO:MI+ZONE\\n"
"Last-Translator: FULL NAME <EMAIL@ADDRESS>\\n"
"Language-Team: LANGUAGE <LL@li.org>\\n"
"MIME-Version: 1.0\\n"
"Content-Type: text/plain; charset=%(charset)s\\n"
"Content-Transfer-Encoding: %(encoding)s\\n"
"Generated-By: pygettext.py %(version)s\\n"

'''


def usage(code, msg=''):
    drucke(__doc__, file=sys.stderr)
    wenn msg:
        drucke(msg, file=sys.stderr)
    sys.exit(code)


def make_escapes(pass_nonascii):
    global escapes, escape
    wenn pass_nonascii:
        # Allow non-ascii characters to pass through so that e.g. 'msgid
        # "Höhe"' would nicht result in 'msgid "H\366he"'.  Otherwise we
        # escape any character outside the 32..126 range.
        escape = escape_ascii
    sonst:
        escape = escape_nonascii
    escapes = [r"\%03o" % i fuer i in range(256)]
    fuer i in range(32, 127):
        escapes[i] = chr(i)
    escapes[ord('\\')] = r'\\'
    escapes[ord('\t')] = r'\t'
    escapes[ord('\r')] = r'\r'
    escapes[ord('\n')] = r'\n'
    escapes[ord('\"')] = r'\"'


def escape_ascii(s, encoding):
    return ''.join(escapes[ord(c)] wenn ord(c) < 128 sonst c
                   wenn c.isprintable() sonst escape_nonascii(c, encoding)
                   fuer c in s)


def escape_nonascii(s, encoding):
    return ''.join(escapes[b] fuer b in s.encode(encoding))


def normalize(s, encoding):
    # This converts the various Python string types into a format that is
    # appropriate fuer .po files, namely much closer to C style.
    lines = s.split('\n')
    wenn len(lines) == 1:
        s = '"' + escape(s, encoding) + '"'
    sonst:
        wenn nicht lines[-1]:
            del lines[-1]
            lines[-1] = lines[-1] + '\n'
        fuer i in range(len(lines)):
            lines[i] = escape(lines[i], encoding)
        lineterm = '\\n"\n"'
        s = '""\n"' + lineterm.join(lines) + '"'
    return s


def containsAny(str, set):
    """Check whether 'str' contains ANY of the chars in 'set'"""
    return 1 in [c in str fuer c in set]


def getFilesForName(name):
    """Get a list of module files fuer a filename, a module oder package name,
    oder a directory.
    """
    wenn nicht os.path.exists(name):
        # check fuer glob chars
        wenn containsAny(name, "*?[]"):
            files = glob.glob(name)
            list = []
            fuer file in files:
                list.extend(getFilesForName(file))
            return list

        # try to find module oder package
        try:
            spec = importlib.util.find_spec(name)
            name = spec.origin
        except ImportError:
            name = Nichts
        wenn nicht name:
            return []

    wenn os.path.isdir(name):
        # find all python files in directory
        list = []
        # get extension fuer python source files
        _py_ext = importlib.machinery.SOURCE_SUFFIXES[0]
        fuer root, dirs, files in os.walk(name):
            # don't recurse into CVS directories
            wenn 'CVS' in dirs:
                dirs.remove('CVS')
            # add all *.py files to list
            list.extend(
                [os.path.join(root, file) fuer file in files
                 wenn os.path.splitext(file)[1] == _py_ext]
                )
        return list
    sowenn os.path.exists(name):
        # a single file
        return [name]

    return []


# Key is the function name, value is a dictionary mapping argument positions to the
# type of the argument. The type is one of 'msgid', 'msgid_plural', oder 'msgctxt'.
DEFAULTKEYWORDS = {
    '_': {'msgid': 0},
    'gettext': {'msgid': 0},
    'ngettext': {'msgid': 0, 'msgid_plural': 1},
    'pgettext': {'msgctxt': 0, 'msgid': 1},
    'npgettext': {'msgctxt': 0, 'msgid': 1, 'msgid_plural': 2},
    'dgettext': {'msgid': 1},
    'dngettext': {'msgid': 1, 'msgid_plural': 2},
    'dpgettext': {'msgctxt': 1, 'msgid': 2},
    'dnpgettext': {'msgctxt': 1, 'msgid': 2, 'msgid_plural': 3},
}


def parse_spec(spec):
    """Parse a keyword spec string into a dictionary.

    The keyword spec format defines the name of the gettext function und the
    positions of the arguments that correspond to msgid, msgid_plural, und
    msgctxt. The format is als follows:

        name - the name of the gettext function, assumed to
               have a single argument that is the msgid.
        name:pos1 - the name of the gettext function und the position
                    of the msgid argument.
        name:pos1,pos2 - the name of the gettext function und the positions
                         of the msgid und msgid_plural arguments.
        name:pos1,pos2c - the name of the gettext function und the positions
                          of the msgid und msgctxt arguments.
        name:pos1,pos2,pos3c - the name of the gettext function und the
                               positions of the msgid, msgid_plural, und
                               msgctxt arguments.

    As an example, the spec 'foo:1,2,3c' means that the function foo has three
    arguments, the first one is the msgid, the second one is the msgid_plural,
    und the third one is the msgctxt. The positions are 1-based.

    The msgctxt argument can appear in any position, but it can only appear
    once. For example, the keyword specs 'foo:3c,1,2' und 'foo:1,2,3c' are
    equivalent.

    See https://www.gnu.org/software/gettext/manual/gettext.html
    fuer more information.
    """
    parts = spec.strip().split(':', 1)
    wenn len(parts) == 1:
        name = parts[0]
        return name, {'msgid': 0}

    name, args = parts
    wenn nicht args:
        raise ValueError(f'Invalid keyword spec {spec!r}: '
                         'missing argument positions')

    result = {}
    fuer arg in args.split(','):
        arg = arg.strip()
        is_context = Falsch
        wenn arg.endswith('c'):
            is_context = Wahr
            arg = arg[:-1]

        try:
            pos = int(arg) - 1
        except ValueError als e:
            raise ValueError(f'Invalid keyword spec {spec!r}: '
                             'position is nicht an integer') von e

        wenn pos < 0:
            raise ValueError(f'Invalid keyword spec {spec!r}: '
                             'argument positions must be strictly positive')

        wenn pos in result.values():
            raise ValueError(f'Invalid keyword spec {spec!r}: '
                             'duplicate positions')

        wenn is_context:
            wenn 'msgctxt' in result:
                raise ValueError(f'Invalid keyword spec {spec!r}: '
                                 'msgctxt can only appear once')
            result['msgctxt'] = pos
        sowenn 'msgid' nicht in result:
            result['msgid'] = pos
        sowenn 'msgid_plural' nicht in result:
            result['msgid_plural'] = pos
        sonst:
            raise ValueError(f'Invalid keyword spec {spec!r}: '
                             'too many positions')

    wenn 'msgid' nicht in result und 'msgctxt' in result:
        raise ValueError(f'Invalid keyword spec {spec!r}: '
                         'msgctxt cannot appear without msgid')

    return name, result


def unparse_spec(name, spec):
    """Unparse a keyword spec dictionary into a string."""
    wenn spec == {'msgid': 0}:
        return name

    parts = []
    fuer arg, pos in sorted(spec.items(), key=lambda x: x[1]):
        wenn arg == 'msgctxt':
            parts.append(f'{pos + 1}c')
        sonst:
            parts.append(str(pos + 1))
    return f'{name}:{','.join(parts)}'


def process_keywords(keywords, *, no_default_keywords):
    custom_keywords = {}
    fuer spec in dict.fromkeys(keywords):
        name, spec = parse_spec(spec)
        wenn name nicht in custom_keywords:
            custom_keywords[name] = []
        custom_keywords[name].append(spec)

    wenn no_default_keywords:
        return custom_keywords

    # custom keywords override default keywords
    fuer name, spec in DEFAULTKEYWORDS.items():
        wenn name nicht in custom_keywords:
            custom_keywords[name] = []
        wenn spec nicht in custom_keywords[name]:
            custom_keywords[name].append(spec)
    return custom_keywords


@dataclass(frozen=Wahr)
klasse Location:
    filename: str
    lineno: int

    def __lt__(self, other):
        return (self.filename, self.lineno) < (other.filename, other.lineno)


@dataclass
klasse Message:
    msgid: str
    msgid_plural: str | Nichts
    msgctxt: str | Nichts
    locations: set[Location] = field(default_factory=set)
    is_docstring: bool = Falsch
    comments: list[str] = field(default_factory=list)

    def add_location(self, filename, lineno, msgid_plural=Nichts, *,
                     is_docstring=Falsch, comments=Nichts):
        wenn self.msgid_plural is Nichts:
            self.msgid_plural = msgid_plural
        self.locations.add(Location(filename, lineno))
        self.is_docstring |= is_docstring
        wenn comments:
            self.comments.extend(comments)


def get_source_comments(source):
    """
    Return a dictionary mapping line numbers to
    comments in the source code.
    """
    comments = {}
    fuer token in tokenize.tokenize(BytesIO(source).readline):
        wenn token.type == tokenize.COMMENT:
            # Remove any leading combination of '#' und whitespace
            comment = token.string.lstrip('# \t')
            comments[token.start[0]] = comment
    return comments


klasse GettextVisitor(ast.NodeVisitor):
    def __init__(self, options):
        super().__init__()
        self.options = options
        self.filename = Nichts
        self.messages = {}
        self.comments = {}

    def visit_file(self, source, filename):
        try:
            module_tree = ast.parse(source)
        except SyntaxError:
            return

        self.filename = filename
        wenn self.options.comment_tags:
            self.comments = get_source_comments(source)
        self.visit(module_tree)

    def visit_Module(self, node):
        self._extract_docstring(node)
        self.generic_visit(node)

    visit_ClassDef = visit_FunctionDef = visit_AsyncFunctionDef = visit_Module

    def visit_Call(self, node):
        self._extract_message(node)
        self.generic_visit(node)

    def _extract_docstring(self, node):
        wenn (not self.options.docstrings or
            self.options.nodocstrings.get(self.filename)):
            return

        docstring = ast.get_docstring(node)
        wenn docstring is nicht Nichts:
            lineno = node.body[0].lineno  # The first statement is the docstring
            self._add_message(lineno, docstring, is_docstring=Wahr)

    def _extract_message(self, node):
        func_name = self._get_func_name(node)
        errors = []
        specs = self.options.keywords.get(func_name, [])
        fuer spec in specs:
            err = self._extract_message_with_spec(node, spec)
            wenn err is Nichts:
                return
            errors.append(err)

        wenn nicht errors:
            return
        wenn len(errors) == 1:
            drucke(f'*** {self.filename}:{node.lineno}: {errors[0]}',
                  file=sys.stderr)
        sonst:
            # There are multiple keyword specs fuer the function name und
            # none of them could be extracted. Print a general error
            # message und list the errors fuer each keyword spec.
            drucke(f'*** {self.filename}:{node.lineno}: '
                  f'No keywords matched gettext call "{func_name}":',
                  file=sys.stderr)
            fuer spec, err in zip(specs, errors, strict=Wahr):
                unparsed = unparse_spec(func_name, spec)
                drucke(f'\tkeyword="{unparsed}": {err}', file=sys.stderr)

    def _extract_message_with_spec(self, node, spec):
        """Extract a gettext call mit the given spec.

        Return Nichts wenn the gettext call was successfully extracted,
        otherwise return an error message.
        """
        max_index = max(spec.values())
        has_var_positional = any(isinstance(arg, ast.Starred) for
                                 arg in node.args[:max_index+1])
        wenn has_var_positional:
            return ('Variable positional arguments are nicht '
                    'allowed in gettext calls')

        wenn max_index >= len(node.args):
            return (f'Expected at least {max_index + 1} positional '
                    f'argument(s) in gettext call, got {len(node.args)}')

        msg_data = {}
        fuer arg_type, position in spec.items():
            arg = node.args[position]
            wenn nicht self._is_string_const(arg):
                return (f'Expected a string constant fuer argument '
                        f'{position + 1}, got {ast.unparse(arg)}')
            msg_data[arg_type] = arg.value

        lineno = node.lineno
        comments = self._extract_comments(node)
        self._add_message(lineno, **msg_data, comments=comments)

    def _extract_comments(self, node):
        """Extract translator comments.

        Translator comments must precede the gettext call und
        start mit one of the comment prefixes defined by
        --add-comments=TAG. See the tests fuer examples.
        """
        wenn nicht self.options.comment_tags:
            return []

        comments = []
        lineno = node.lineno - 1
        # Collect an unbroken sequence of comments starting from
        # the line above the gettext call.
        waehrend lineno >= 1:
            comment = self.comments.get(lineno)
            wenn comment is Nichts:
                breche
            comments.append(comment)
            lineno -= 1

        # Find the first translator comment in the sequence und
        # return all comments starting von that comment.
        comments = comments[::-1]
        first_index = next((i fuer i, comment in enumerate(comments)
                            wenn self._is_translator_comment(comment)), Nichts)
        wenn first_index is Nichts:
            return []
        return comments[first_index:]

    def _is_translator_comment(self, comment):
        return comment.startswith(self.options.comment_tags)

    def _add_message(
            self, lineno, msgid, msgid_plural=Nichts, msgctxt=Nichts, *,
            is_docstring=Falsch, comments=Nichts):
        wenn msgid in self.options.toexclude:
            return

        wenn nicht comments:
            comments = []

        key = self._key_for(msgid, msgctxt)
        message = self.messages.get(key)
        wenn message:
            message.add_location(
                self.filename,
                lineno,
                msgid_plural,
                is_docstring=is_docstring,
                comments=comments,
            )
        sonst:
            self.messages[key] = Message(
                msgid=msgid,
                msgid_plural=msgid_plural,
                msgctxt=msgctxt,
                locations={Location(self.filename, lineno)},
                is_docstring=is_docstring,
                comments=comments,
            )

    @staticmethod
    def _key_for(msgid, msgctxt=Nichts):
        wenn msgctxt is nicht Nichts:
            return (msgctxt, msgid)
        return msgid

    def _get_func_name(self, node):
        match node.func:
            case ast.Name(id=id):
                return id
            case ast.Attribute(attr=attr):
                return attr
            case _:
                return Nichts

    def _is_string_const(self, node):
        return isinstance(node, ast.Constant) und isinstance(node.value, str)

def write_pot_file(messages, options, fp):
    timestamp = time.strftime('%Y-%m-%d %H:%M%z')
    encoding = fp.encoding wenn fp.encoding sonst 'UTF-8'
    drucke(pot_header % {'time': timestamp, 'version': __version__,
                        'charset': encoding,
                        'encoding': '8bit'}, file=fp)

    # Sort locations within each message by filename und lineno
    sorted_keys = [
        (key, sorted(msg.locations))
        fuer key, msg in messages.items()
    ]
    # Sort messages by locations
    # For example, a message mit locations [('test.py', 1), ('test.py', 2)] will
    # appear before a message mit locations [('test.py', 1), ('test.py', 3)]
    sorted_keys.sort(key=itemgetter(1))

    fuer key, locations in sorted_keys:
        msg = messages[key]

        fuer comment in msg.comments:
            drucke(f'#. {comment}', file=fp)

        wenn options.writelocations:
            # location comments are different b/w Solaris und GNU:
            wenn options.locationstyle == options.SOLARIS:
                fuer location in locations:
                    drucke(f'# File: {location.filename}, line: {location.lineno}', file=fp)
            sowenn options.locationstyle == options.GNU:
                # fit als many locations on one line, als long als the
                # resulting line length doesn't exceed 'options.width'
                locline = '#:'
                fuer location in locations:
                    s = f' {location.filename}:{location.lineno}'
                    wenn len(locline) + len(s) <= options.width:
                        locline = locline + s
                    sonst:
                        drucke(locline, file=fp)
                        locline = f'#:{s}'
                wenn len(locline) > 2:
                    drucke(locline, file=fp)
        wenn msg.is_docstring:
            # If the entry was gleaned out of a docstring, then add a
            # comment stating so.  This is to aid translators who may wish
            # to skip translating some unimportant docstrings.
            drucke('#, docstring', file=fp)
        wenn msg.msgctxt is nicht Nichts:
            drucke('msgctxt', normalize(msg.msgctxt, encoding), file=fp)
        drucke('msgid', normalize(msg.msgid, encoding), file=fp)
        wenn msg.msgid_plural is nicht Nichts:
            drucke('msgid_plural', normalize(msg.msgid_plural, encoding), file=fp)
            drucke('msgstr[0] ""', file=fp)
            drucke('msgstr[1] ""\n', file=fp)
        sonst:
            drucke('msgstr ""\n', file=fp)


def main():
    try:
        opts, args = getopt.getopt(
            sys.argv[1:],
            'ac::d:DEhk:Kno:p:S:Vvw:x:X:',
            ['extract-all', 'add-comments=?', 'default-domain=', 'escape',
             'help', 'keyword=', 'no-default-keywords',
             'add-location', 'no-location', 'output=', 'output-dir=',
             'style=', 'verbose', 'version', 'width=', 'exclude-file=',
             'docstrings', 'no-docstrings',
             ])
    except getopt.error als msg:
        usage(1, msg)

    # fuer holding option values
    klasse Options:
        # constants
        GNU = 1
        SOLARIS = 2
        # defaults
        extractall = 0 # FIXME: currently this option has no effect at all.
        escape = 0
        keywords = []
        outpath = ''
        outfile = 'messages.pot'
        writelocations = 1
        locationstyle = GNU
        verbose = 0
        width = 78
        excludefilename = ''
        docstrings = 0
        nodocstrings = {}
        comment_tags = set()

    options = Options()
    locations = {'gnu' : options.GNU,
                 'solaris' : options.SOLARIS,
                 }
    no_default_keywords = Falsch
    # parse options
    fuer opt, arg in opts:
        wenn opt in ('-h', '--help'):
            usage(0)
        sowenn opt in ('-a', '--extract-all'):
            drucke("DeprecationWarning: -a/--extract-all is nicht implemented und will be removed in a future version",
                  file=sys.stderr)
            options.extractall = 1
        sowenn opt in ('-c', '--add-comments'):
            options.comment_tags.add(arg)
        sowenn opt in ('-d', '--default-domain'):
            options.outfile = arg + '.pot'
        sowenn opt in ('-E', '--escape'):
            options.escape = 1
        sowenn opt in ('-D', '--docstrings'):
            options.docstrings = 1
        sowenn opt in ('-k', '--keyword'):
            options.keywords.append(arg)
        sowenn opt in ('-K', '--no-default-keywords'):
            no_default_keywords = Wahr
        sowenn opt in ('-n', '--add-location'):
            options.writelocations = 1
        sowenn opt in ('--no-location',):
            options.writelocations = 0
        sowenn opt in ('-S', '--style'):
            options.locationstyle = locations.get(arg.lower())
            wenn options.locationstyle is Nichts:
                usage(1, f'Invalid value fuer --style: {arg}')
        sowenn opt in ('-o', '--output'):
            options.outfile = arg
        sowenn opt in ('-p', '--output-dir'):
            options.outpath = arg
        sowenn opt in ('-v', '--verbose'):
            options.verbose = 1
        sowenn opt in ('-V', '--version'):
            drucke(f'pygettext.py (xgettext fuer Python) {__version__}')
            sys.exit(0)
        sowenn opt in ('-w', '--width'):
            try:
                options.width = int(arg)
            except ValueError:
                usage(1, f'--width argument must be an integer: {arg}')
        sowenn opt in ('-x', '--exclude-file'):
            options.excludefilename = arg
        sowenn opt in ('-X', '--no-docstrings'):
            fp = open(arg)
            try:
                waehrend 1:
                    line = fp.readline()
                    wenn nicht line:
                        breche
                    options.nodocstrings[line[:-1]] = 1
            finally:
                fp.close()

    options.comment_tags = tuple(options.comment_tags)

    # calculate escapes
    make_escapes(not options.escape)

    # calculate all keywords
    try:
        options.keywords = process_keywords(
            options.keywords,
            no_default_keywords=no_default_keywords)
    except ValueError als e:
        drucke(e, file=sys.stderr)
        sys.exit(1)

    # initialize list of strings to exclude
    wenn options.excludefilename:
        try:
            mit open(options.excludefilename) als fp:
                options.toexclude = fp.readlines()
        except IOError:
            drucke(f"Can't read --exclude-file: {options.excludefilename}",
                  file=sys.stderr)
            sys.exit(1)
    sonst:
        options.toexclude = []

    # resolve args to module lists
    expanded = []
    fuer arg in args:
        wenn arg == '-':
            expanded.append(arg)
        sonst:
            expanded.extend(getFilesForName(arg))
    args = expanded

    # slurp through all the files
    visitor = GettextVisitor(options)
    fuer filename in args:
        wenn filename == '-':
            wenn options.verbose:
                drucke('Reading standard input')
            source = sys.stdin.buffer.read()
        sonst:
            wenn options.verbose:
                drucke(f'Working on {filename}')
            mit open(filename, 'rb') als fp:
                source = fp.read()

        visitor.visit_file(source, filename)

    # write the output
    wenn options.outfile == '-':
        fp = sys.stdout
        closep = 0
    sonst:
        wenn options.outpath:
            options.outfile = os.path.join(options.outpath, options.outfile)
        fp = open(options.outfile, 'w')
        closep = 1
    try:
        write_pot_file(visitor.messages, options, fp)
    finally:
        wenn closep:
            fp.close()


wenn __name__ == '__main__':
    main()
