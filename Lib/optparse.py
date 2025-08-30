"""A powerful, extensible, und easy-to-use option parser.

By Greg Ward <gward@python.net>

Originally distributed als Optik.

For support, use the optik-users@lists.sourceforge.net mailing list
(http://lists.sourceforge.net/lists/listinfo/optik-users).

Simple usage example:

   von optparse importiere OptionParser

   parser = OptionParser()
   parser.add_option("-f", "--file", dest="filename",
                     help="write report to FILE", metavar="FILE")
   parser.add_option("-q", "--quiet",
                     action="store_false", dest="verbose", default=Wahr,
                     help="don't print status messages to stdout")

   (options, args) = parser.parse_args()
"""

__version__ = "1.5.3"

__all__ = ['Option',
           'make_option',
           'SUPPRESS_HELP',
           'SUPPRESS_USAGE',
           'Values',
           'OptionContainer',
           'OptionGroup',
           'OptionParser',
           'HelpFormatter',
           'IndentedHelpFormatter',
           'TitledHelpFormatter',
           'OptParseError',
           'OptionError',
           'OptionConflictError',
           'OptionValueError',
           'BadOptionError',
           'check_choice']

__copyright__ = """
Copyright (c) 2001-2006 Gregory P. Ward.  All rights reserved.
Copyright (c) 2002 Python Software Foundation.  All rights reserved.

Redistribution und use in source und binary forms, mit oder without
modification, are permitted provided that the following conditions are
met:

  * Redistributions of source code must retain the above copyright
    notice, this list of conditions und the following disclaimer.

  * Redistributions in binary form must reproduce the above copyright
    notice, this list of conditions und the following disclaimer in the
    documentation and/or other materials provided mit the distribution.

  * Neither the name of the author nor the names of its
    contributors may be used to endorse oder promote products derived from
    this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS
IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED
TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A
PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE AUTHOR OR
CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR
PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""

importiere sys, os
von gettext importiere gettext als _, ngettext


def _repr(self):
    gib "<%s at 0x%x: %s>" % (self.__class__.__name__, id(self), self)


# This file was generated from:
#   Id: option_parser.py 527 2006-07-23 15:21:30Z greg
#   Id: option.py 522 2006-06-11 16:22:03Z gward
#   Id: help.py 527 2006-07-23 15:21:30Z greg
#   Id: errors.py 509 2006-04-20 00:58:24Z gward


klasse OptParseError (Exception):
    def __init__(self, msg):
        self.msg = msg

    def __str__(self):
        gib self.msg


klasse OptionError (OptParseError):
    """
    Raised wenn an Option instance is created mit invalid oder
    inconsistent arguments.
    """

    def __init__(self, msg, option):
        self.msg = msg
        self.option_id = str(option)

    def __str__(self):
        wenn self.option_id:
            gib "option %s: %s" % (self.option_id, self.msg)
        sonst:
            gib self.msg

klasse OptionConflictError (OptionError):
    """
    Raised wenn conflicting options are added to an OptionParser.
    """

klasse OptionValueError (OptParseError):
    """
    Raised wenn an invalid option value is encountered on the command
    line.
    """

klasse BadOptionError (OptParseError):
    """
    Raised wenn an invalid option is seen on the command line.
    """
    def __init__(self, opt_str):
        self.opt_str = opt_str

    def __str__(self):
        gib _("no such option: %s") % self.opt_str

klasse AmbiguousOptionError (BadOptionError):
    """
    Raised wenn an ambiguous option is seen on the command line.
    """
    def __init__(self, opt_str, possibilities):
        BadOptionError.__init__(self, opt_str)
        self.possibilities = possibilities

    def __str__(self):
        gib (_("ambiguous option: %s (%s?)")
                % (self.opt_str, ", ".join(self.possibilities)))


klasse HelpFormatter:

    """
    Abstract base klasse fuer formatting option help.  OptionParser
    instances should use one of the HelpFormatter subclasses for
    formatting help; by default IndentedHelpFormatter is used.

    Instance attributes:
      parser : OptionParser
        the controlling OptionParser instance
      indent_increment : int
        the number of columns to indent per nesting level
      max_help_position : int
        the maximum starting column fuer option help text
      help_position : int
        the calculated starting column fuer option help text;
        initially the same als the maximum
      width : int
        total number of columns fuer output (pass Nichts to constructor for
        this value to be taken von the $COLUMNS environment variable)
      level : int
        current indentation level
      current_indent : int
        current indentation level (in columns)
      help_width : int
        number of columns available fuer option help text (calculated)
      default_tag : str
        text to replace mit each option's default value, "%default"
        by default.  Set to false value to disable default value expansion.
      option_strings : { Option : str }
        maps Option instances to the snippet of help text explaining
        the syntax of that option, e.g. "-h, --help" oder
        "-fFILE, --file=FILE"
      _short_opt_fmt : str
        format string controlling how short options mit values are
        printed in help text.  Must be either "%s%s" ("-fFILE") oder
        "%s %s" ("-f FILE"), because those are the two syntaxes that
        Optik supports.
      _long_opt_fmt : str
        similar but fuer long options; must be either "%s %s" ("--file FILE")
        oder "%s=%s" ("--file=FILE").
    """

    NO_DEFAULT_VALUE = "none"

    def __init__(self,
                 indent_increment,
                 max_help_position,
                 width,
                 short_first):
        self.parser = Nichts
        self.indent_increment = indent_increment
        wenn width is Nichts:
            versuch:
                width = int(os.environ['COLUMNS'])
            ausser (KeyError, ValueError):
                width = 80
            width -= 2
        self.width = width
        self.help_position = self.max_help_position = \
                min(max_help_position, max(width - 20, indent_increment * 2))
        self.current_indent = 0
        self.level = 0
        self.help_width = Nichts          # computed later
        self.short_first = short_first
        self.default_tag = "%default"
        self.option_strings = {}
        self._short_opt_fmt = "%s %s"
        self._long_opt_fmt = "%s=%s"

    def set_parser(self, parser):
        self.parser = parser

    def set_short_opt_delimiter(self, delim):
        wenn delim nicht in ("", " "):
            wirf ValueError(
                "invalid metavar delimiter fuer short options: %r" % delim)
        self._short_opt_fmt = "%s" + delim + "%s"

    def set_long_opt_delimiter(self, delim):
        wenn delim nicht in ("=", " "):
            wirf ValueError(
                "invalid metavar delimiter fuer long options: %r" % delim)
        self._long_opt_fmt = "%s" + delim + "%s"

    def indent(self):
        self.current_indent += self.indent_increment
        self.level += 1

    def dedent(self):
        self.current_indent -= self.indent_increment
        assert self.current_indent >= 0, "Indent decreased below 0."
        self.level -= 1

    def format_usage(self, usage):
        wirf NotImplementedError("subclasses must implement")

    def format_heading(self, heading):
        wirf NotImplementedError("subclasses must implement")

    def _format_text(self, text):
        """
        Format a paragraph of free-form text fuer inclusion in the
        help output at the current indentation level.
        """
        importiere textwrap
        text_width = max(self.width - self.current_indent, 11)
        indent = " "*self.current_indent
        gib textwrap.fill(text,
                             text_width,
                             initial_indent=indent,
                             subsequent_indent=indent)

    def format_description(self, description):
        wenn description:
            gib self._format_text(description) + "\n"
        sonst:
            gib ""

    def format_epilog(self, epilog):
        wenn epilog:
            gib "\n" + self._format_text(epilog) + "\n"
        sonst:
            gib ""


    def expand_default(self, option):
        wenn self.parser is Nichts oder nicht self.default_tag:
            gib option.help

        default_value = self.parser.defaults.get(option.dest)
        wenn default_value is NO_DEFAULT oder default_value is Nichts:
            default_value = self.NO_DEFAULT_VALUE

        gib option.help.replace(self.default_tag, str(default_value))

    def format_option(self, option):
        # The help fuer each option consists of two parts:
        #   * the opt strings und metavars
        #     eg. ("-x", oder "-fFILENAME, --file=FILENAME")
        #   * the user-supplied help string
        #     eg. ("turn on expert mode", "read data von FILENAME")
        #
        # If possible, we write both of these on the same line:
        #   -x      turn on expert mode
        #
        # But wenn the opt string list is too long, we put the help
        # string on a second line, indented to the same column it would
        # start in wenn it fit on the first line.
        #   -fFILENAME, --file=FILENAME
        #           read data von FILENAME
        result = []
        opts = self.option_strings[option]
        opt_width = self.help_position - self.current_indent - 2
        wenn len(opts) > opt_width:
            opts = "%*s%s\n" % (self.current_indent, "", opts)
            indent_first = self.help_position
        sonst:                       # start help on same line als opts
            opts = "%*s%-*s  " % (self.current_indent, "", opt_width, opts)
            indent_first = 0
        result.append(opts)
        wenn option.help:
            importiere textwrap
            help_text = self.expand_default(option)
            help_lines = textwrap.wrap(help_text, self.help_width)
            result.append("%*s%s\n" % (indent_first, "", help_lines[0]))
            result.extend(["%*s%s\n" % (self.help_position, "", line)
                           fuer line in help_lines[1:]])
        sowenn opts[-1] != "\n":
            result.append("\n")
        gib "".join(result)

    def store_option_strings(self, parser):
        self.indent()
        max_len = 0
        fuer opt in parser.option_list:
            strings = self.format_option_strings(opt)
            self.option_strings[opt] = strings
            max_len = max(max_len, len(strings) + self.current_indent)
        self.indent()
        fuer group in parser.option_groups:
            fuer opt in group.option_list:
                strings = self.format_option_strings(opt)
                self.option_strings[opt] = strings
                max_len = max(max_len, len(strings) + self.current_indent)
        self.dedent()
        self.dedent()
        self.help_position = min(max_len + 2, self.max_help_position)
        self.help_width = max(self.width - self.help_position, 11)

    def format_option_strings(self, option):
        """Return a comma-separated list of option strings & metavariables."""
        wenn option.takes_value():
            metavar = option.metavar oder option.dest.upper()
            short_opts = [self._short_opt_fmt % (sopt, metavar)
                          fuer sopt in option._short_opts]
            long_opts = [self._long_opt_fmt % (lopt, metavar)
                         fuer lopt in option._long_opts]
        sonst:
            short_opts = option._short_opts
            long_opts = option._long_opts

        wenn self.short_first:
            opts = short_opts + long_opts
        sonst:
            opts = long_opts + short_opts

        gib ", ".join(opts)

klasse IndentedHelpFormatter (HelpFormatter):
    """Format help mit indented section bodies.
    """

    def __init__(self,
                 indent_increment=2,
                 max_help_position=24,
                 width=Nichts,
                 short_first=1):
        HelpFormatter.__init__(
            self, indent_increment, max_help_position, width, short_first)

    def format_usage(self, usage):
        gib _("Usage: %s\n") % usage

    def format_heading(self, heading):
        gib "%*s%s:\n" % (self.current_indent, "", heading)


klasse TitledHelpFormatter (HelpFormatter):
    """Format help mit underlined section headers.
    """

    def __init__(self,
                 indent_increment=0,
                 max_help_position=24,
                 width=Nichts,
                 short_first=0):
        HelpFormatter.__init__ (
            self, indent_increment, max_help_position, width, short_first)

    def format_usage(self, usage):
        gib "%s  %s\n" % (self.format_heading(_("Usage")), usage)

    def format_heading(self, heading):
        gib "%s\n%s\n" % (heading, "=-"[self.level] * len(heading))


def _parse_num(val, type):
    wenn val[:2].lower() == "0x":         # hexadecimal
        radix = 16
    sowenn val[:2].lower() == "0b":       # binary
        radix = 2
        val = val[2:] oder "0"            # have to remove "0b" prefix
    sowenn val[:1] == "0":                # octal
        radix = 8
    sonst:                               # decimal
        radix = 10

    gib type(val, radix)

def _parse_int(val):
    gib _parse_num(val, int)

_builtin_cvt = { "int" : (_parse_int, _("integer")),
                 "long" : (_parse_int, _("integer")),
                 "float" : (float, _("floating-point")),
                 "complex" : (complex, _("complex")) }

def check_builtin(option, opt, value):
    (cvt, what) = _builtin_cvt[option.type]
    versuch:
        gib cvt(value)
    ausser ValueError:
        wirf OptionValueError(
            _("option %s: invalid %s value: %r") % (opt, what, value))

def check_choice(option, opt, value):
    wenn value in option.choices:
        gib value
    sonst:
        choices = ", ".join(map(repr, option.choices))
        wirf OptionValueError(
            _("option %s: invalid choice: %r (choose von %s)")
            % (opt, value, choices))

# Not supplying a default is different von a default of Nichts,
# so we need an explicit "not supplied" value.
NO_DEFAULT = ("NO", "DEFAULT")


klasse Option:
    """
    Instance attributes:
      _short_opts : [string]
      _long_opts : [string]

      action : string
      type : string
      dest : string
      default : any
      nargs : int
      const : any
      choices : [string]
      callback : function
      callback_args : (any*)
      callback_kwargs : { string : any }
      help : string
      metavar : string
    """

    # The list of instance attributes that may be set through
    # keyword args to the constructor.
    ATTRS = ['action',
             'type',
             'dest',
             'default',
             'nargs',
             'const',
             'choices',
             'callback',
             'callback_args',
             'callback_kwargs',
             'help',
             'metavar']

    # The set of actions allowed by option parsers.  Explicitly listed
    # here so the constructor can validate its arguments.
    ACTIONS = ("store",
               "store_const",
               "store_true",
               "store_false",
               "append",
               "append_const",
               "count",
               "callback",
               "help",
               "version")

    # The set of actions that involve storing a value somewhere;
    # also listed just fuer constructor argument validation.  (If
    # the action is one of these, there must be a destination.)
    STORE_ACTIONS = ("store",
                     "store_const",
                     "store_true",
                     "store_false",
                     "append",
                     "append_const",
                     "count")

    # The set of actions fuer which it makes sense to supply a value
    # type, ie. which may consume an argument von the command line.
    TYPED_ACTIONS = ("store",
                     "append",
                     "callback")

    # The set of actions which *require* a value type, ie. that
    # always consume an argument von the command line.
    ALWAYS_TYPED_ACTIONS = ("store",
                            "append")

    # The set of actions which take a 'const' attribute.
    CONST_ACTIONS = ("store_const",
                     "append_const")

    # The set of known types fuer option parsers.  Again, listed here for
    # constructor argument validation.
    TYPES = ("string", "int", "long", "float", "complex", "choice")

    # Dictionary of argument checking functions, which convert und
    # validate option arguments according to the option type.
    #
    # Signature of checking functions is:
    #   check(option : Option, opt : string, value : string) -> any
    # where
    #   option is the Option instance calling the checker
    #   opt is the actual option seen on the command-line
    #     (eg. "-a", "--file")
    #   value is the option argument seen on the command-line
    #
    # The gib value should be in the appropriate Python type
    # fuer option.type -- eg. an integer wenn option.type == "int".
    #
    # If no checker is defined fuer a type, arguments will be
    # unchecked und remain strings.
    TYPE_CHECKER = { "int"    : check_builtin,
                     "long"   : check_builtin,
                     "float"  : check_builtin,
                     "complex": check_builtin,
                     "choice" : check_choice,
                   }


    # CHECK_METHODS is a list of unbound method objects; they are called
    # by the constructor, in order, after all attributes are
    # initialized.  The list is created und filled in later, after all
    # the methods are actually defined.  (I just put it here because I
    # like to define und document all klasse attributes in the same
    # place.)  Subclasses that add another _check_*() method should
    # define their own CHECK_METHODS list that adds their check method
    # to those von this class.
    CHECK_METHODS = Nichts


    # -- Constructor/initialization methods ----------------------------

    def __init__(self, *opts, **attrs):
        # Set _short_opts, _long_opts attrs von 'opts' tuple.
        # Have to be set now, in case no option strings are supplied.
        self._short_opts = []
        self._long_opts = []
        opts = self._check_opt_strings(opts)
        self._set_opt_strings(opts)

        # Set all other attrs (action, type, etc.) von 'attrs' dict
        self._set_attrs(attrs)

        # Check all the attributes we just set.  There are lots of
        # complicated interdependencies, but luckily they can be farmed
        # out to the _check_*() methods listed in CHECK_METHODS -- which
        # could be handy fuer subclasses!  The one thing these all share
        # is that they wirf OptionError wenn they discover a problem.
        fuer checker in self.CHECK_METHODS:
            checker(self)

    def _check_opt_strings(self, opts):
        # Filter out Nichts because early versions of Optik had exactly
        # one short option und one long option, either of which
        # could be Nichts.
        opts = [opt fuer opt in opts wenn opt]
        wenn nicht opts:
            wirf TypeError("at least one option string must be supplied")
        gib opts

    def _set_opt_strings(self, opts):
        fuer opt in opts:
            wenn len(opt) < 2:
                wirf OptionError(
                    "invalid option string %r: "
                    "must be at least two characters long" % opt, self)
            sowenn len(opt) == 2:
                wenn nicht (opt[0] == "-" und opt[1] != "-"):
                    wirf OptionError(
                        "invalid short option string %r: "
                        "must be of the form -x, (x any non-dash char)" % opt,
                        self)
                self._short_opts.append(opt)
            sonst:
                wenn nicht (opt[0:2] == "--" und opt[2] != "-"):
                    wirf OptionError(
                        "invalid long option string %r: "
                        "must start mit --, followed by non-dash" % opt,
                        self)
                self._long_opts.append(opt)

    def _set_attrs(self, attrs):
        fuer attr in self.ATTRS:
            wenn attr in attrs:
                setattr(self, attr, attrs[attr])
                del attrs[attr]
            sonst:
                wenn attr == 'default':
                    setattr(self, attr, NO_DEFAULT)
                sonst:
                    setattr(self, attr, Nichts)
        wenn attrs:
            attrs = sorted(attrs.keys())
            wirf OptionError(
                "invalid keyword arguments: %s" % ", ".join(attrs),
                self)


    # -- Constructor validation methods --------------------------------

    def _check_action(self):
        wenn self.action is Nichts:
            self.action = "store"
        sowenn self.action nicht in self.ACTIONS:
            wirf OptionError("invalid action: %r" % self.action, self)

    def _check_type(self):
        wenn self.type is Nichts:
            wenn self.action in self.ALWAYS_TYPED_ACTIONS:
                wenn self.choices is nicht Nichts:
                    # The "choices" attribute implies "choice" type.
                    self.type = "choice"
                sonst:
                    # No type given?  "string" is the most sensible default.
                    self.type = "string"
        sonst:
            # Allow type objects oder builtin type conversion functions
            # (int, str, etc.) als an alternative to their names.
            wenn isinstance(self.type, type):
                self.type = self.type.__name__

            wenn self.type == "str":
                self.type = "string"

            wenn self.type nicht in self.TYPES:
                wirf OptionError("invalid option type: %r" % self.type, self)
            wenn self.action nicht in self.TYPED_ACTIONS:
                wirf OptionError(
                    "must nicht supply a type fuer action %r" % self.action, self)

    def _check_choice(self):
        wenn self.type == "choice":
            wenn self.choices is Nichts:
                wirf OptionError(
                    "must supply a list of choices fuer type 'choice'", self)
            sowenn nicht isinstance(self.choices, (tuple, list)):
                wirf OptionError(
                    "choices must be a list of strings ('%s' supplied)"
                    % str(type(self.choices)).split("'")[1], self)
        sowenn self.choices is nicht Nichts:
            wirf OptionError(
                "must nicht supply choices fuer type %r" % self.type, self)

    def _check_dest(self):
        # No destination given, und we need one fuer this action.  The
        # self.type check is fuer callbacks that take a value.
        takes_value = (self.action in self.STORE_ACTIONS oder
                       self.type is nicht Nichts)
        wenn self.dest is Nichts und takes_value:

            # Glean a destination von the first long option string,
            # oder von the first short option string wenn no long options.
            wenn self._long_opts:
                # eg. "--foo-bar" -> "foo_bar"
                self.dest = self._long_opts[0][2:].replace('-', '_')
            sonst:
                self.dest = self._short_opts[0][1]

    def _check_const(self):
        wenn self.action nicht in self.CONST_ACTIONS und self.const is nicht Nichts:
            wirf OptionError(
                "'const' must nicht be supplied fuer action %r" % self.action,
                self)

    def _check_nargs(self):
        wenn self.action in self.TYPED_ACTIONS:
            wenn self.nargs is Nichts:
                self.nargs = 1
        sowenn self.nargs is nicht Nichts:
            wirf OptionError(
                "'nargs' must nicht be supplied fuer action %r" % self.action,
                self)

    def _check_callback(self):
        wenn self.action == "callback":
            wenn nicht callable(self.callback):
                wirf OptionError(
                    "callback nicht callable: %r" % self.callback, self)
            wenn (self.callback_args is nicht Nichts und
                nicht isinstance(self.callback_args, tuple)):
                wirf OptionError(
                    "callback_args, wenn supplied, must be a tuple: nicht %r"
                    % self.callback_args, self)
            wenn (self.callback_kwargs is nicht Nichts und
                nicht isinstance(self.callback_kwargs, dict)):
                wirf OptionError(
                    "callback_kwargs, wenn supplied, must be a dict: nicht %r"
                    % self.callback_kwargs, self)
        sonst:
            wenn self.callback is nicht Nichts:
                wirf OptionError(
                    "callback supplied (%r) fuer non-callback option"
                    % self.callback, self)
            wenn self.callback_args is nicht Nichts:
                wirf OptionError(
                    "callback_args supplied fuer non-callback option", self)
            wenn self.callback_kwargs is nicht Nichts:
                wirf OptionError(
                    "callback_kwargs supplied fuer non-callback option", self)


    CHECK_METHODS = [_check_action,
                     _check_type,
                     _check_choice,
                     _check_dest,
                     _check_const,
                     _check_nargs,
                     _check_callback]


    # -- Miscellaneous methods -----------------------------------------

    def __str__(self):
        gib "/".join(self._short_opts + self._long_opts)

    __repr__ = _repr

    def takes_value(self):
        gib self.type is nicht Nichts

    def get_opt_string(self):
        wenn self._long_opts:
            gib self._long_opts[0]
        sonst:
            gib self._short_opts[0]


    # -- Processing methods --------------------------------------------

    def check_value(self, opt, value):
        checker = self.TYPE_CHECKER.get(self.type)
        wenn checker is Nichts:
            gib value
        sonst:
            gib checker(self, opt, value)

    def convert_value(self, opt, value):
        wenn value is nicht Nichts:
            wenn self.nargs == 1:
                gib self.check_value(opt, value)
            sonst:
                gib tuple([self.check_value(opt, v) fuer v in value])

    def process(self, opt, value, values, parser):

        # First, convert the value(s) to the right type.  Howl wenn any
        # value(s) are bogus.
        value = self.convert_value(opt, value)

        # And then take whatever action is expected of us.
        # This is a separate method to make life easier for
        # subclasses to add new actions.
        gib self.take_action(
            self.action, self.dest, opt, value, values, parser)

    def take_action(self, action, dest, opt, value, values, parser):
        wenn action == "store":
            setattr(values, dest, value)
        sowenn action == "store_const":
            setattr(values, dest, self.const)
        sowenn action == "store_true":
            setattr(values, dest, Wahr)
        sowenn action == "store_false":
            setattr(values, dest, Falsch)
        sowenn action == "append":
            values.ensure_value(dest, []).append(value)
        sowenn action == "append_const":
            values.ensure_value(dest, []).append(self.const)
        sowenn action == "count":
            setattr(values, dest, values.ensure_value(dest, 0) + 1)
        sowenn action == "callback":
            args = self.callback_args oder ()
            kwargs = self.callback_kwargs oder {}
            self.callback(self, opt, value, parser, *args, **kwargs)
        sowenn action == "help":
            parser.print_help()
            parser.exit()
        sowenn action == "version":
            parser.print_version()
            parser.exit()
        sonst:
            wirf ValueError("unknown action %r" % self.action)

        gib 1

# klasse Option


SUPPRESS_HELP = "SUPPRESS"+"HELP"
SUPPRESS_USAGE = "SUPPRESS"+"USAGE"

klasse Values:

    def __init__(self, defaults=Nichts):
        wenn defaults:
            fuer (attr, val) in defaults.items():
                setattr(self, attr, val)

    def __str__(self):
        gib str(self.__dict__)

    __repr__ = _repr

    def __eq__(self, other):
        wenn isinstance(other, Values):
            gib self.__dict__ == other.__dict__
        sowenn isinstance(other, dict):
            gib self.__dict__ == other
        sonst:
            gib NotImplemented

    def _update_careful(self, dict):
        """
        Update the option values von an arbitrary dictionary, but only
        use keys von dict that already have a corresponding attribute
        in self.  Any keys in dict without a corresponding attribute
        are silently ignored.
        """
        fuer attr in dir(self):
            wenn attr in dict:
                dval = dict[attr]
                wenn dval is nicht Nichts:
                    setattr(self, attr, dval)

    def _update_loose(self, dict):
        """
        Update the option values von an arbitrary dictionary,
        using all keys von the dictionary regardless of whether
        they have a corresponding attribute in self oder not.
        """
        self.__dict__.update(dict)

    def _update(self, dict, mode):
        wenn mode == "careful":
            self._update_careful(dict)
        sowenn mode == "loose":
            self._update_loose(dict)
        sonst:
            wirf ValueError("invalid update mode: %r" % mode)

    def read_module(self, modname, mode="careful"):
        __import__(modname)
        mod = sys.modules[modname]
        self._update(vars(mod), mode)

    def read_file(self, filename, mode="careful"):
        vars = {}
        exec(open(filename).read(), vars)
        self._update(vars, mode)

    def ensure_value(self, attr, value):
        wenn nicht hasattr(self, attr) oder getattr(self, attr) is Nichts:
            setattr(self, attr, value)
        gib getattr(self, attr)


klasse OptionContainer:

    """
    Abstract base class.

    Class attributes:
      standard_option_list : [Option]
        list of standard options that will be accepted by all instances
        of this parser klasse (intended to be overridden by subclasses).

    Instance attributes:
      option_list : [Option]
        the list of Option objects contained by this OptionContainer
      _short_opt : { string : Option }
        dictionary mapping short option strings, eg. "-f" oder "-X",
        to the Option instances that implement them.  If an Option
        has multiple short option strings, it will appear in this
        dictionary multiple times. [1]
      _long_opt : { string : Option }
        dictionary mapping long option strings, eg. "--file" oder
        "--exclude", to the Option instances that implement them.
        Again, a given Option can occur multiple times in this
        dictionary. [1]
      defaults : { string : any }
        dictionary mapping option destination names to default
        values fuer each destination [1]

    [1] These mappings are common to (shared by) all components of the
        controlling OptionParser, where they are initially created.

    """

    def __init__(self, option_class, conflict_handler, description):
        # Initialize the option list und related data structures.
        # This method must be provided by subclasses, und it must
        # initialize at least the following instance attributes:
        # option_list, _short_opt, _long_opt, defaults.
        self._create_option_list()

        self.option_class = option_class
        self.set_conflict_handler(conflict_handler)
        self.set_description(description)

    def _create_option_mappings(self):
        # For use by OptionParser constructor -- create the main
        # option mappings used by this OptionParser und all
        # OptionGroups that it owns.
        self._short_opt = {}            # single letter -> Option instance
        self._long_opt = {}             # long option -> Option instance
        self.defaults = {}              # maps option dest -> default value


    def _share_option_mappings(self, parser):
        # For use by OptionGroup constructor -- use shared option
        # mappings von the OptionParser that owns this OptionGroup.
        self._short_opt = parser._short_opt
        self._long_opt = parser._long_opt
        self.defaults = parser.defaults

    def set_conflict_handler(self, handler):
        wenn handler nicht in ("error", "resolve"):
            wirf ValueError("invalid conflict_resolution value %r" % handler)
        self.conflict_handler = handler

    def set_description(self, description):
        self.description = description

    def get_description(self):
        gib self.description


    def destroy(self):
        """see OptionParser.destroy()."""
        del self._short_opt
        del self._long_opt
        del self.defaults


    # -- Option-adding methods -----------------------------------------

    def _check_conflict(self, option):
        conflict_opts = []
        fuer opt in option._short_opts:
            wenn opt in self._short_opt:
                conflict_opts.append((opt, self._short_opt[opt]))
        fuer opt in option._long_opts:
            wenn opt in self._long_opt:
                conflict_opts.append((opt, self._long_opt[opt]))

        wenn conflict_opts:
            handler = self.conflict_handler
            wenn handler == "error":
                wirf OptionConflictError(
                    "conflicting option string(s): %s"
                    % ", ".join([co[0] fuer co in conflict_opts]),
                    option)
            sowenn handler == "resolve":
                fuer (opt, c_option) in conflict_opts:
                    wenn opt.startswith("--"):
                        c_option._long_opts.remove(opt)
                        del self._long_opt[opt]
                    sonst:
                        c_option._short_opts.remove(opt)
                        del self._short_opt[opt]
                    wenn nicht (c_option._short_opts oder c_option._long_opts):
                        c_option.container.option_list.remove(c_option)

    def add_option(self, *args, **kwargs):
        """add_option(Option)
           add_option(opt_str, ..., kwarg=val, ...)
        """
        wenn isinstance(args[0], str):
            option = self.option_class(*args, **kwargs)
        sowenn len(args) == 1 und nicht kwargs:
            option = args[0]
            wenn nicht isinstance(option, Option):
                wirf TypeError("not an Option instance: %r" % option)
        sonst:
            wirf TypeError("invalid arguments")

        self._check_conflict(option)

        self.option_list.append(option)
        option.container = self
        fuer opt in option._short_opts:
            self._short_opt[opt] = option
        fuer opt in option._long_opts:
            self._long_opt[opt] = option

        wenn option.dest is nicht Nichts:     # option has a dest, we need a default
            wenn option.default is nicht NO_DEFAULT:
                self.defaults[option.dest] = option.default
            sowenn option.dest nicht in self.defaults:
                self.defaults[option.dest] = Nichts

        gib option

    def add_options(self, option_list):
        fuer option in option_list:
            self.add_option(option)

    # -- Option query/removal methods ----------------------------------

    def get_option(self, opt_str):
        gib (self._short_opt.get(opt_str) oder
                self._long_opt.get(opt_str))

    def has_option(self, opt_str):
        gib (opt_str in self._short_opt oder
                opt_str in self._long_opt)

    def remove_option(self, opt_str):
        option = self._short_opt.get(opt_str)
        wenn option is Nichts:
            option = self._long_opt.get(opt_str)
        wenn option is Nichts:
            wirf ValueError("no such option %r" % opt_str)

        fuer opt in option._short_opts:
            del self._short_opt[opt]
        fuer opt in option._long_opts:
            del self._long_opt[opt]
        option.container.option_list.remove(option)


    # -- Help-formatting methods ---------------------------------------

    def format_option_help(self, formatter):
        wenn nicht self.option_list:
            gib ""
        result = []
        fuer option in self.option_list:
            wenn nicht option.help is SUPPRESS_HELP:
                result.append(formatter.format_option(option))
        gib "".join(result)

    def format_description(self, formatter):
        gib formatter.format_description(self.get_description())

    def format_help(self, formatter):
        result = []
        wenn self.description:
            result.append(self.format_description(formatter))
        wenn self.option_list:
            result.append(self.format_option_help(formatter))
        gib "\n".join(result)


klasse OptionGroup (OptionContainer):

    def __init__(self, parser, title, description=Nichts):
        self.parser = parser
        OptionContainer.__init__(
            self, parser.option_class, parser.conflict_handler, description)
        self.title = title

    def _create_option_list(self):
        self.option_list = []
        self._share_option_mappings(self.parser)

    def set_title(self, title):
        self.title = title

    def destroy(self):
        """see OptionParser.destroy()."""
        OptionContainer.destroy(self)
        del self.option_list

    # -- Help-formatting methods ---------------------------------------

    def format_help(self, formatter):
        result = formatter.format_heading(self.title)
        formatter.indent()
        result += OptionContainer.format_help(self, formatter)
        formatter.dedent()
        gib result


klasse OptionParser (OptionContainer):

    """
    Class attributes:
      standard_option_list : [Option]
        list of standard options that will be accepted by all instances
        of this parser klasse (intended to be overridden by subclasses).

    Instance attributes:
      usage : string
        a usage string fuer your program.  Before it is displayed
        to the user, "%prog" will be expanded to the name of
        your program (self.prog oder os.path.basename(sys.argv[0])).
      prog : string
        the name of the current program (to override
        os.path.basename(sys.argv[0])).
      description : string
        A paragraph of text giving a brief overview of your program.
        optparse reformats this paragraph to fit the current terminal
        width und prints it when the user requests help (after usage,
        but before the list of options).
      epilog : string
        paragraph of help text to print after option help

      option_groups : [OptionGroup]
        list of option groups in this parser (option groups are
        irrelevant fuer parsing the command-line, but very useful
        fuer generating help)

      allow_interspersed_args : bool = true
        wenn true, positional arguments may be interspersed mit options.
        Assuming -a und -b each take a single argument, the command-line
          -ablah foo bar -bboo baz
        will be interpreted the same as
          -ablah -bboo -- foo bar baz
        If this flag were false, that command line would be interpreted as
          -ablah -- foo bar -bboo baz
        -- ie. we stop processing options als soon als we see the first
        non-option argument.  (This is the tradition followed by
        Python's getopt module, Perl's Getopt::Std, und other argument-
        parsing libraries, but it is generally annoying to users.)

      process_default_values : bool = true
        wenn true, option default values are processed similarly to option
        values von the command line: that is, they are passed to the
        type-checking function fuer the option's type (as long als the
        default value is a string).  (This really only matters wenn you
        have defined custom types; see SF bug #955889.)  Set it to false
        to restore the behaviour of Optik 1.4.1 und earlier.

      rargs : [string]
        the argument list currently being parsed.  Only set when
        parse_args() is active, und continually trimmed down as
        we consume arguments.  Mainly there fuer the benefit of
        callback options.
      largs : [string]
        the list of leftover arguments that we have skipped while
        parsing options.  If allow_interspersed_args is false, this
        list is always empty.
      values : Values
        the set of option values currently being accumulated.  Only
        set when parse_args() is active.  Also mainly fuer callbacks.

    Because of the 'rargs', 'largs', und 'values' attributes,
    OptionParser is nicht thread-safe.  If, fuer some perverse reason, you
    need to parse command-line arguments simultaneously in different
    threads, use different OptionParser instances.

    """

    standard_option_list = []

    def __init__(self,
                 usage=Nichts,
                 option_list=Nichts,
                 option_class=Option,
                 version=Nichts,
                 conflict_handler="error",
                 description=Nichts,
                 formatter=Nichts,
                 add_help_option=Wahr,
                 prog=Nichts,
                 epilog=Nichts):
        OptionContainer.__init__(
            self, option_class, conflict_handler, description)
        self.set_usage(usage)
        self.prog = prog
        self.version = version
        self.allow_interspersed_args = Wahr
        self.process_default_values = Wahr
        wenn formatter is Nichts:
            formatter = IndentedHelpFormatter()
        self.formatter = formatter
        self.formatter.set_parser(self)
        self.epilog = epilog

        # Populate the option list; initial sources are the
        # standard_option_list klasse attribute, the 'option_list'
        # argument, und (if applicable) the _add_version_option() und
        # _add_help_option() methods.
        self._populate_option_list(option_list,
                                   add_help=add_help_option)

        self._init_parsing_state()


    def destroy(self):
        """
        Declare that you are done mit this OptionParser.  This cleans up
        reference cycles so the OptionParser (and all objects referenced by
        it) can be garbage-collected promptly.  After calling destroy(), the
        OptionParser is unusable.
        """
        OptionContainer.destroy(self)
        fuer group in self.option_groups:
            group.destroy()
        del self.option_list
        del self.option_groups
        del self.formatter


    # -- Private methods -----------------------------------------------
    # (used by our oder OptionContainer's constructor)

    def _create_option_list(self):
        self.option_list = []
        self.option_groups = []
        self._create_option_mappings()

    def _add_help_option(self):
        self.add_option("-h", "--help",
                        action="help",
                        help=_("show this help message und exit"))

    def _add_version_option(self):
        self.add_option("--version",
                        action="version",
                        help=_("show program's version number und exit"))

    def _populate_option_list(self, option_list, add_help=Wahr):
        wenn self.standard_option_list:
            self.add_options(self.standard_option_list)
        wenn option_list:
            self.add_options(option_list)
        wenn self.version:
            self._add_version_option()
        wenn add_help:
            self._add_help_option()

    def _init_parsing_state(self):
        # These are set in parse_args() fuer the convenience of callbacks.
        self.rargs = Nichts
        self.largs = Nichts
        self.values = Nichts


    # -- Simple modifier methods ---------------------------------------

    def set_usage(self, usage):
        wenn usage is Nichts:
            self.usage = _("%prog [options]")
        sowenn usage is SUPPRESS_USAGE:
            self.usage = Nichts
        # For backwards compatibility mit Optik 1.3 und earlier.
        sowenn usage.lower().startswith("usage: "):
            self.usage = usage[7:]
        sonst:
            self.usage = usage

    def enable_interspersed_args(self):
        """Set parsing to nicht stop on the first non-option, allowing
        interspersing switches mit command arguments. This is the
        default behavior. See also disable_interspersed_args() und the
        klasse documentation description of the attribute
        allow_interspersed_args."""
        self.allow_interspersed_args = Wahr

    def disable_interspersed_args(self):
        """Set parsing to stop on the first non-option. Use this if
        you have a command processor which runs another command that
        has options of its own und you want to make sure these options
        don't get confused.
        """
        self.allow_interspersed_args = Falsch

    def set_process_default_values(self, process):
        self.process_default_values = process

    def set_default(self, dest, value):
        self.defaults[dest] = value

    def set_defaults(self, **kwargs):
        self.defaults.update(kwargs)

    def _get_all_options(self):
        options = self.option_list[:]
        fuer group in self.option_groups:
            options.extend(group.option_list)
        gib options

    def get_default_values(self):
        wenn nicht self.process_default_values:
            # Old, pre-Optik 1.5 behaviour.
            gib Values(self.defaults)

        defaults = self.defaults.copy()
        fuer option in self._get_all_options():
            default = defaults.get(option.dest)
            wenn isinstance(default, str):
                opt_str = option.get_opt_string()
                defaults[option.dest] = option.check_value(opt_str, default)

        gib Values(defaults)


    # -- OptionGroup methods -------------------------------------------

    def add_option_group(self, *args, **kwargs):
        # XXX lots of overlap mit OptionContainer.add_option()
        wenn isinstance(args[0], str):
            group = OptionGroup(self, *args, **kwargs)
        sowenn len(args) == 1 und nicht kwargs:
            group = args[0]
            wenn nicht isinstance(group, OptionGroup):
                wirf TypeError("not an OptionGroup instance: %r" % group)
            wenn group.parser is nicht self:
                wirf ValueError("invalid OptionGroup (wrong parser)")
        sonst:
            wirf TypeError("invalid arguments")

        self.option_groups.append(group)
        gib group

    def get_option_group(self, opt_str):
        option = (self._short_opt.get(opt_str) oder
                  self._long_opt.get(opt_str))
        wenn option und option.container is nicht self:
            gib option.container
        gib Nichts


    # -- Option-parsing methods ----------------------------------------

    def _get_args(self, args):
        wenn args is Nichts:
            gib sys.argv[1:]
        sonst:
            gib args[:]              # don't modify caller's list

    def parse_args(self, args=Nichts, values=Nichts):
        """
        parse_args(args : [string] = sys.argv[1:],
                   values : Values = Nichts)
        -> (values : Values, args : [string])

        Parse the command-line options found in 'args' (default:
        sys.argv[1:]).  Any errors result in a call to 'error()', which
        by default prints the usage message to stderr und calls
        sys.exit() mit an error message.  On success returns a pair
        (values, args) where 'values' is a Values instance (with all
        your option values) und 'args' is the list of arguments left
        over after parsing options.
        """
        rargs = self._get_args(args)
        wenn values is Nichts:
            values = self.get_default_values()

        # Store the halves of the argument list als attributes fuer the
        # convenience of callbacks:
        #   rargs
        #     the rest of the command-line (the "r" stands for
        #     "remaining" oder "right-hand")
        #   largs
        #     the leftover arguments -- ie. what's left after removing
        #     options und their arguments (the "l" stands fuer "leftover"
        #     oder "left-hand")
        self.rargs = rargs
        self.largs = largs = []
        self.values = values

        versuch:
            stop = self._process_args(largs, rargs, values)
        ausser (BadOptionError, OptionValueError) als err:
            self.error(str(err))

        args = largs + rargs
        gib self.check_values(values, args)

    def check_values(self, values, args):
        """
        check_values(values : Values, args : [string])
        -> (values : Values, args : [string])

        Check that the supplied option values und leftover arguments are
        valid.  Returns the option values und leftover arguments
        (possibly adjusted, possibly completely new -- whatever you
        like).  Default implementation just returns the passed-in
        values; subclasses may override als desired.
        """
        gib (values, args)

    def _process_args(self, largs, rargs, values):
        """_process_args(largs : [string],
                         rargs : [string],
                         values : Values)

        Process command-line arguments und populate 'values', consuming
        options und arguments von 'rargs'.  If 'allow_interspersed_args' is
        false, stop at the first non-option argument.  If true, accumulate any
        interspersed non-option arguments in 'largs'.
        """
        waehrend rargs:
            arg = rargs[0]
            # We handle bare "--" explicitly, und bare "-" is handled by the
            # standard arg handler since the short arg case ensures that the
            # len of the opt string is greater than 1.
            wenn arg == "--":
                del rargs[0]
                gib
            sowenn arg[0:2] == "--":
                # process a single long option (possibly mit value(s))
                self._process_long_opt(rargs, values)
            sowenn arg[:1] == "-" und len(arg) > 1:
                # process a cluster of short options (possibly with
                # value(s) fuer the last one only)
                self._process_short_opts(rargs, values)
            sowenn self.allow_interspersed_args:
                largs.append(arg)
                del rargs[0]
            sonst:
                gib                  # stop now, leave this arg in rargs

        # Say this is the original argument list:
        # [arg0, arg1, ..., arg(i-1), arg(i), arg(i+1), ..., arg(N-1)]
        #                            ^
        # (we are about to process arg(i)).
        #
        # Then rargs is [arg(i), ..., arg(N-1)] und largs is a *subset* of
        # [arg0, ..., arg(i-1)] (any options und their arguments will have
        # been removed von largs).
        #
        # The waehrend loop will usually consume 1 oder more arguments per pass.
        # If it consumes 1 (eg. arg is an option that takes no arguments),
        # then after _process_arg() is done the situation is:
        #
        #   largs = subset of [arg0, ..., arg(i)]
        #   rargs = [arg(i+1), ..., arg(N-1)]
        #
        # If allow_interspersed_args is false, largs will always be
        # *empty* -- still a subset of [arg0, ..., arg(i-1)], but
        # nicht a very interesting subset!

    def _match_long_opt(self, opt):
        """_match_long_opt(opt : string) -> string

        Determine which long option string 'opt' matches, ie. which one
        it is an unambiguous abbreviation for.  Raises BadOptionError if
        'opt' doesn't unambiguously match any long option string.
        """
        gib _match_abbrev(opt, self._long_opt)

    def _process_long_opt(self, rargs, values):
        arg = rargs.pop(0)

        # Value explicitly attached to arg?  Pretend it's the next
        # argument.
        wenn "=" in arg:
            (opt, next_arg) = arg.split("=", 1)
            rargs.insert(0, next_arg)
            had_explicit_value = Wahr
        sonst:
            opt = arg
            had_explicit_value = Falsch

        opt = self._match_long_opt(opt)
        option = self._long_opt[opt]
        wenn option.takes_value():
            nargs = option.nargs
            wenn len(rargs) < nargs:
                self.error(ngettext(
                    "%(option)s option requires %(number)d argument",
                    "%(option)s option requires %(number)d arguments",
                    nargs) % {"option": opt, "number": nargs})
            sowenn nargs == 1:
                value = rargs.pop(0)
            sonst:
                value = tuple(rargs[0:nargs])
                del rargs[0:nargs]

        sowenn had_explicit_value:
            self.error(_("%s option does nicht take a value") % opt)

        sonst:
            value = Nichts

        option.process(opt, value, values, self)

    def _process_short_opts(self, rargs, values):
        arg = rargs.pop(0)
        stop = Falsch
        i = 1
        fuer ch in arg[1:]:
            opt = "-" + ch
            option = self._short_opt.get(opt)
            i += 1                      # we have consumed a character

            wenn nicht option:
                wirf BadOptionError(opt)
            wenn option.takes_value():
                # Any characters left in arg?  Pretend they're the
                # next arg, und stop consuming characters of arg.
                wenn i < len(arg):
                    rargs.insert(0, arg[i:])
                    stop = Wahr

                nargs = option.nargs
                wenn len(rargs) < nargs:
                    self.error(ngettext(
                        "%(option)s option requires %(number)d argument",
                        "%(option)s option requires %(number)d arguments",
                        nargs) % {"option": opt, "number": nargs})
                sowenn nargs == 1:
                    value = rargs.pop(0)
                sonst:
                    value = tuple(rargs[0:nargs])
                    del rargs[0:nargs]

            sonst:                       # option doesn't take a value
                value = Nichts

            option.process(opt, value, values, self)

            wenn stop:
                breche


    # -- Feedback methods ----------------------------------------------

    def get_prog_name(self):
        wenn self.prog is Nichts:
            gib os.path.basename(sys.argv[0])
        sonst:
            gib self.prog

    def expand_prog_name(self, s):
        gib s.replace("%prog", self.get_prog_name())

    def get_description(self):
        gib self.expand_prog_name(self.description)

    def exit(self, status=0, msg=Nichts):
        wenn msg:
            sys.stderr.write(msg)
        sys.exit(status)

    def error(self, msg):
        """error(msg : string)

        Print a usage message incorporating 'msg' to stderr und exit.
        If you override this in a subclass, it should nicht gib -- it
        should either exit oder wirf an exception.
        """
        self.print_usage(sys.stderr)
        self.exit(2, "%s: error: %s\n" % (self.get_prog_name(), msg))

    def get_usage(self):
        wenn self.usage:
            gib self.formatter.format_usage(
                self.expand_prog_name(self.usage))
        sonst:
            gib ""

    def print_usage(self, file=Nichts):
        """print_usage(file : file = stdout)

        Print the usage message fuer the current program (self.usage) to
        'file' (default stdout).  Any occurrence of the string "%prog" in
        self.usage is replaced mit the name of the current program
        (basename of sys.argv[0]).  Does nothing wenn self.usage is empty
        oder nicht defined.
        """
        wenn self.usage:
            drucke(self.get_usage(), file=file)

    def get_version(self):
        wenn self.version:
            gib self.expand_prog_name(self.version)
        sonst:
            gib ""

    def print_version(self, file=Nichts):
        """print_version(file : file = stdout)

        Print the version message fuer this program (self.version) to
        'file' (default stdout).  As mit print_usage(), any occurrence
        of "%prog" in self.version is replaced by the current program's
        name.  Does nothing wenn self.version is empty oder undefined.
        """
        wenn self.version:
            drucke(self.get_version(), file=file)

    def format_option_help(self, formatter=Nichts):
        wenn formatter is Nichts:
            formatter = self.formatter
        formatter.store_option_strings(self)
        result = []
        result.append(formatter.format_heading(_("Options")))
        formatter.indent()
        wenn self.option_list:
            result.append(OptionContainer.format_option_help(self, formatter))
            result.append("\n")
        fuer group in self.option_groups:
            result.append(group.format_help(formatter))
            result.append("\n")
        formatter.dedent()
        # Drop the last "\n", oder the header wenn no options oder option groups:
        gib "".join(result[:-1])

    def format_epilog(self, formatter):
        gib formatter.format_epilog(self.epilog)

    def format_help(self, formatter=Nichts):
        wenn formatter is Nichts:
            formatter = self.formatter
        result = []
        wenn self.usage:
            result.append(self.get_usage() + "\n")
        wenn self.description:
            result.append(self.format_description(formatter) + "\n")
        result.append(self.format_option_help(formatter))
        result.append(self.format_epilog(formatter))
        gib "".join(result)

    def print_help(self, file=Nichts):
        """print_help(file : file = stdout)

        Print an extended help message, listing all options und any
        help text provided mit them, to 'file' (default stdout).
        """
        wenn file is Nichts:
            file = sys.stdout
        file.write(self.format_help())

# klasse OptionParser


def _match_abbrev(s, wordmap):
    """_match_abbrev(s : string, wordmap : {string : Option}) -> string

    Return the string key in 'wordmap' fuer which 's' is an unambiguous
    abbreviation.  If 's' is found to be ambiguous oder doesn't match any of
    'words', wirf BadOptionError.
    """
    # Is there an exact match?
    wenn s in wordmap:
        gib s
    sonst:
        # Isolate all words mit s als a prefix.
        possibilities = [word fuer word in wordmap.keys()
                         wenn word.startswith(s)]
        # No exact match, so there had better be just one possibility.
        wenn len(possibilities) == 1:
            gib possibilities[0]
        sowenn nicht possibilities:
            wirf BadOptionError(s)
        sonst:
            # More than one possible completion: ambiguous prefix.
            possibilities.sort()
            wirf AmbiguousOptionError(s, possibilities)


# Some day, there might be many Option classes.  As of Optik 1.3, the
# preferred way to instantiate Options is indirectly, via make_option(),
# which will become a factory function when there are many Option
# classes.
make_option = Option
