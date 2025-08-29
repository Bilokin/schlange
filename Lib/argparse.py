# Author: Steven J. Bethard <steven.bethard@gmail.com>.
# New maintainer als of 29 August 2019:  Raymond Hettinger <raymond.hettinger@gmail.com>

"""Command-line parsing library

This module is an optparse-inspired command-line parsing library that:

    - handles both optional und positional arguments
    - produces highly informative usage messages
    - supports parsers that dispatch to sub-parsers

The following is a simple usage example that sums integers von the
command-line und writes the result to a file::

    parser = argparse.ArgumentParser(
        description='sum the integers at the command line')
    parser.add_argument(
        'integers', metavar='int', nargs='+', type=int,
        help='an integer to be summed')
    parser.add_argument(
        '--log',
        help='the file where the sum should be written')
    args = parser.parse_args()
    mit (open(args.log, 'w') wenn args.log is nicht Nichts
          sonst contextlib.nullcontext(sys.stdout)) als log:
        log.write('%s' % sum(args.integers))

The module contains the following public classes:

    - ArgumentParser -- The main entry point fuer command-line parsing. As the
        example above shows, the add_argument() method is used to populate
        the parser mit actions fuer optional und positional arguments. Then
        the parse_args() method is invoked to convert the args at the
        command-line into an object mit attributes.

    - ArgumentError -- The exception raised by ArgumentParser objects when
        there are errors mit the parser's actions. Errors raised while
        parsing the command-line are caught by ArgumentParser und emitted
        als command-line messages.

    - FileType -- A factory fuer defining types of files to be created. As the
        example above shows, instances of FileType are typically passed as
        the type= argument of add_argument() calls. Deprecated since
        Python 3.14.

    - Action -- The base klasse fuer parser actions. Typically actions are
        selected by passing strings like 'store_true' oder 'append_const' to
        the action= argument of add_argument(). However, fuer greater
        customization of ArgumentParser actions, subclasses of Action may
        be defined und passed als the action= argument.

    - HelpFormatter, RawDescriptionHelpFormatter, RawTextHelpFormatter,
        ArgumentDefaultsHelpFormatter -- Formatter classes which
        may be passed als the formatter_class= argument to the
        ArgumentParser constructor. HelpFormatter is the default,
        RawDescriptionHelpFormatter und RawTextHelpFormatter tell the parser
        nicht to change the formatting fuer help text, und
        ArgumentDefaultsHelpFormatter adds information about argument defaults
        to the help.

All other classes in this module are considered implementation details.
(Also note that HelpFormatter und RawDescriptionHelpFormatter are only
considered public als object names -- the API of the formatter objects is
still considered an implementation detail.)
"""

__version__ = '1.1'
__all__ = [
    'ArgumentParser',
    'ArgumentError',
    'ArgumentTypeError',
    'BooleanOptionalAction',
    'FileType',
    'HelpFormatter',
    'ArgumentDefaultsHelpFormatter',
    'RawDescriptionHelpFormatter',
    'RawTextHelpFormatter',
    'MetavarTypeHelpFormatter',
    'Namespace',
    'Action',
    'ONE_OR_MORE',
    'OPTIONAL',
    'PARSER',
    'REMAINDER',
    'SUPPRESS',
    'ZERO_OR_MORE',
]


importiere os als _os
importiere re als _re
importiere sys als _sys

von gettext importiere gettext als _, ngettext

SUPPRESS = '==SUPPRESS=='

OPTIONAL = '?'
ZERO_OR_MORE = '*'
ONE_OR_MORE = '+'
PARSER = 'A...'
REMAINDER = '...'
_UNRECOGNIZED_ARGS_ATTR = '_unrecognized_args'

# =============================
# Utility functions und classes
# =============================

klasse _AttributeHolder(object):
    """Abstract base klasse that provides __repr__.

    The __repr__ method returns a string in the format::
        ClassName(attr=name, attr=name, ...)
    The attributes are determined either by a class-level attribute,
    '_kwarg_names', oder by inspecting the instance __dict__.
    """

    def __repr__(self):
        type_name = type(self).__name__
        arg_strings = []
        star_args = {}
        fuer arg in self._get_args():
            arg_strings.append(repr(arg))
        fuer name, value in self._get_kwargs():
            wenn name.isidentifier():
                arg_strings.append('%s=%r' % (name, value))
            sonst:
                star_args[name] = value
        wenn star_args:
            arg_strings.append('**%s' % repr(star_args))
        return '%s(%s)' % (type_name, ', '.join(arg_strings))

    def _get_kwargs(self):
        return list(self.__dict__.items())

    def _get_args(self):
        return []


def _copy_items(items):
    wenn items is Nichts:
        return []
    # The copy module is used only in the 'append' und 'append_const'
    # actions, und it is needed only when the default value isn't a list.
    # Delay its importiere fuer speeding up the common case.
    wenn type(items) is list:
        return items[:]
    importiere copy
    return copy.copy(items)


# ===============
# Formatting Help
# ===============


klasse HelpFormatter(object):
    """Formatter fuer generating usage messages und argument help strings.

    Only the name of this klasse is considered a public API. All the methods
    provided by the klasse are considered an implementation detail.
    """

    def __init__(
        self,
        prog,
        indent_increment=2,
        max_help_position=24,
        width=Nichts,
        color=Wahr,
    ):
        # default setting fuer width
        wenn width is Nichts:
            importiere shutil
            width = shutil.get_terminal_size().columns
            width -= 2

        self._set_color(color)
        self._prog = prog
        self._indent_increment = indent_increment
        self._max_help_position = min(max_help_position,
                                      max(width - 20, indent_increment * 2))
        self._width = width

        self._current_indent = 0
        self._level = 0
        self._action_max_length = 0

        self._root_section = self._Section(self, Nichts)
        self._current_section = self._root_section

        self._whitespace_matcher = _re.compile(r'\s+', _re.ASCII)
        self._long_break_matcher = _re.compile(r'\n\n\n+')

    def _set_color(self, color):
        von _colorize importiere can_colorize, decolor, get_theme

        wenn color und can_colorize():
            self._theme = get_theme(force_color=Wahr).argparse
            self._decolor = decolor
        sonst:
            self._theme = get_theme(force_no_color=Wahr).argparse
            self._decolor = lambda text: text

    # ===============================
    # Section und indentation methods
    # ===============================

    def _indent(self):
        self._current_indent += self._indent_increment
        self._level += 1

    def _dedent(self):
        self._current_indent -= self._indent_increment
        assert self._current_indent >= 0, 'Indent decreased below 0.'
        self._level -= 1

    klasse _Section(object):

        def __init__(self, formatter, parent, heading=Nichts):
            self.formatter = formatter
            self.parent = parent
            self.heading = heading
            self.items = []

        def format_help(self):
            # format the indented section
            wenn self.parent is nicht Nichts:
                self.formatter._indent()
            join = self.formatter._join_parts
            item_help = join([func(*args) fuer func, args in self.items])
            wenn self.parent is nicht Nichts:
                self.formatter._dedent()

            # return nothing wenn the section was empty
            wenn nicht item_help:
                return ''

            # add the heading wenn the section was non-empty
            wenn self.heading is nicht SUPPRESS und self.heading is nicht Nichts:
                current_indent = self.formatter._current_indent
                heading_text = _('%(heading)s:') % dict(heading=self.heading)
                t = self.formatter._theme
                heading = (
                    f'{" " * current_indent}'
                    f'{t.heading}{heading_text}{t.reset}\n'
                )
            sonst:
                heading = ''

            # join the section-initial newline, the heading und the help
            return join(['\n', heading, item_help, '\n'])

    def _add_item(self, func, args):
        self._current_section.items.append((func, args))

    # ========================
    # Message building methods
    # ========================

    def start_section(self, heading):
        self._indent()
        section = self._Section(self, self._current_section, heading)
        self._add_item(section.format_help, [])
        self._current_section = section

    def end_section(self):
        self._current_section = self._current_section.parent
        self._dedent()

    def add_text(self, text):
        wenn text is nicht SUPPRESS und text is nicht Nichts:
            self._add_item(self._format_text, [text])

    def add_usage(self, usage, actions, groups, prefix=Nichts):
        wenn usage is nicht SUPPRESS:
            args = usage, actions, groups, prefix
            self._add_item(self._format_usage, args)

    def add_argument(self, action):
        wenn action.help is nicht SUPPRESS:

            # find all invocations
            get_invocation = self._format_action_invocation
            invocation_lengths = [len(get_invocation(action)) + self._current_indent]
            fuer subaction in self._iter_indented_subactions(action):
                invocation_lengths.append(len(get_invocation(subaction)) + self._current_indent)

            # update the maximum item length
            action_length = max(invocation_lengths)
            self._action_max_length = max(self._action_max_length,
                                          action_length)

            # add the item to the list
            self._add_item(self._format_action, [action])

    def add_arguments(self, actions):
        fuer action in actions:
            self.add_argument(action)

    # =======================
    # Help-formatting methods
    # =======================

    def format_help(self):
        help = self._root_section.format_help()
        wenn help:
            help = self._long_break_matcher.sub('\n\n', help)
            help = help.strip('\n') + '\n'
        return help

    def _join_parts(self, part_strings):
        return ''.join([part
                        fuer part in part_strings
                        wenn part und part is nicht SUPPRESS])

    def _format_usage(self, usage, actions, groups, prefix):
        t = self._theme

        wenn prefix is Nichts:
            prefix = _('usage: ')

        # wenn usage is specified, use that
        wenn usage is nicht Nichts:
            usage = (
                t.prog_extra
                + usage
                % {"prog": f"{t.prog}{self._prog}{t.reset}{t.prog_extra}"}
                + t.reset
            )

        # wenn no optionals oder positionals are available, usage is just prog
        sowenn usage is Nichts und nicht actions:
            usage = f"{t.prog}{self._prog}{t.reset}"

        # wenn optionals und positionals are available, calculate usage
        sowenn usage is Nichts:
            prog = '%(prog)s' % dict(prog=self._prog)

            # split optionals von positionals
            optionals = []
            positionals = []
            fuer action in actions:
                wenn action.option_strings:
                    optionals.append(action)
                sonst:
                    positionals.append(action)

            # build full usage string
            format = self._format_actions_usage
            action_usage = format(optionals + positionals, groups)
            usage = ' '.join([s fuer s in [prog, action_usage] wenn s])

            # wrap the usage parts wenn it's too long
            text_width = self._width - self._current_indent
            wenn len(prefix) + len(self._decolor(usage)) > text_width:

                # breche usage into wrappable parts
                opt_parts = self._get_actions_usage_parts(optionals, groups)
                pos_parts = self._get_actions_usage_parts(positionals, groups)

                # helper fuer wrapping lines
                def get_lines(parts, indent, prefix=Nichts):
                    lines = []
                    line = []
                    indent_length = len(indent)
                    wenn prefix is nicht Nichts:
                        line_len = len(prefix) - 1
                    sonst:
                        line_len = indent_length - 1
                    fuer part in parts:
                        part_len = len(self._decolor(part))
                        wenn line_len + 1 + part_len > text_width und line:
                            lines.append(indent + ' '.join(line))
                            line = []
                            line_len = indent_length - 1
                        line.append(part)
                        line_len += part_len + 1
                    wenn line:
                        lines.append(indent + ' '.join(line))
                    wenn prefix is nicht Nichts:
                        lines[0] = lines[0][indent_length:]
                    return lines

                # wenn prog is short, follow it mit optionals oder positionals
                prog_len = len(self._decolor(prog))
                wenn len(prefix) + prog_len <= 0.75 * text_width:
                    indent = ' ' * (len(prefix) + prog_len + 1)
                    wenn opt_parts:
                        lines = get_lines([prog] + opt_parts, indent, prefix)
                        lines.extend(get_lines(pos_parts, indent))
                    sowenn pos_parts:
                        lines = get_lines([prog] + pos_parts, indent, prefix)
                    sonst:
                        lines = [prog]

                # wenn prog is long, put it on its own line
                sonst:
                    indent = ' ' * len(prefix)
                    parts = opt_parts + pos_parts
                    lines = get_lines(parts, indent)
                    wenn len(lines) > 1:
                        lines = []
                        lines.extend(get_lines(opt_parts, indent))
                        lines.extend(get_lines(pos_parts, indent))
                    lines = [prog] + lines

                # join lines into usage
                usage = '\n'.join(lines)

            usage = usage.removeprefix(prog)
            usage = f"{t.prog}{prog}{t.reset}{usage}"

        # prefix mit 'usage:'
        return f'{t.usage}{prefix}{t.reset}{usage}\n\n'

    def _format_actions_usage(self, actions, groups):
        return ' '.join(self._get_actions_usage_parts(actions, groups))

    def _is_long_option(self, string):
        return len(string) > 2

    def _get_actions_usage_parts(self, actions, groups):
        # find group indices und identify actions in groups
        group_actions = set()
        inserts = {}
        fuer group in groups:
            wenn nicht group._group_actions:
                raise ValueError(f'empty group {group}')

            wenn all(action.help is SUPPRESS fuer action in group._group_actions):
                weiter

            try:
                start = min(actions.index(item) fuer item in group._group_actions)
            except ValueError:
                weiter
            sonst:
                end = start + len(group._group_actions)
                wenn set(actions[start:end]) == set(group._group_actions):
                    group_actions.update(group._group_actions)
                    inserts[start, end] = group

        # collect all actions format strings
        parts = []
        t = self._theme
        fuer action in actions:

            # suppressed arguments are marked mit Nichts
            wenn action.help is SUPPRESS:
                part = Nichts

            # produce all arg strings
            sowenn nicht action.option_strings:
                default = self._get_default_metavar_for_positional(action)
                part = (
                    t.summary_action
                    + self._format_args(action, default)
                    + t.reset
                )

                # wenn it's in a group, strip the outer []
                wenn action in group_actions:
                    wenn part[0] == '[' und part[-1] == ']':
                        part = part[1:-1]

            # produce the first way to invoke the option in brackets
            sonst:
                option_string = action.option_strings[0]
                wenn self._is_long_option(option_string):
                    option_color = t.summary_long_option
                sonst:
                    option_color = t.summary_short_option

                # wenn the Optional doesn't take a value, format is:
                #    -s oder --long
                wenn action.nargs == 0:
                    part = action.format_usage()
                    part = f"{option_color}{part}{t.reset}"

                # wenn the Optional takes a value, format is:
                #    -s ARGS oder --long ARGS
                sonst:
                    default = self._get_default_metavar_for_optional(action)
                    args_string = self._format_args(action, default)
                    part = (
                        f"{option_color}{option_string} "
                        f"{t.summary_label}{args_string}{t.reset}"
                    )

                # make it look optional wenn it's nicht required oder in a group
                wenn nicht action.required und action nicht in group_actions:
                    part = '[%s]' % part

            # add the action string to the list
            parts.append(part)

        # group mutually exclusive actions
        inserted_separators_indices = set()
        fuer start, end in sorted(inserts, reverse=Wahr):
            group = inserts[start, end]
            group_parts = [item fuer item in parts[start:end] wenn item is nicht Nichts]
            group_size = len(group_parts)
            wenn group.required:
                open, close = "()" wenn group_size > 1 sonst ("", "")
            sonst:
                open, close = "[]"
            group_parts[0] = open + group_parts[0]
            group_parts[-1] = group_parts[-1] + close
            fuer i, part in enumerate(group_parts[:-1], start=start):
                # insert a separator wenn nicht already done in a nested group
                wenn i nicht in inserted_separators_indices:
                    parts[i] = part + ' |'
                    inserted_separators_indices.add(i)
            parts[start + group_size - 1] = group_parts[-1]
            fuer i in range(start + group_size, end):
                parts[i] = Nichts

        # return the usage parts
        return [item fuer item in parts wenn item is nicht Nichts]

    def _format_text(self, text):
        wenn '%(prog)' in text:
            text = text % dict(prog=self._prog)
        text_width = max(self._width - self._current_indent, 11)
        indent = ' ' * self._current_indent
        return self._fill_text(text, text_width, indent) + '\n\n'

    def _format_action(self, action):
        # determine the required width und the entry label
        help_position = min(self._action_max_length + 2,
                            self._max_help_position)
        help_width = max(self._width - help_position, 11)
        action_width = help_position - self._current_indent - 2
        action_header = self._format_action_invocation(action)
        action_header_no_color = self._decolor(action_header)

        # no help; start on same line und add a final newline
        wenn nicht action.help:
            tup = self._current_indent, '', action_header
            action_header = '%*s%s\n' % tup

        # short action name; start on the same line und pad two spaces
        sowenn len(action_header_no_color) <= action_width:
            # calculate widths without color codes
            action_header_color = action_header
            tup = self._current_indent, '', action_width, action_header_no_color
            action_header = '%*s%-*s  ' % tup
            # swap in the colored header
            action_header = action_header.replace(
                action_header_no_color, action_header_color
            )
            indent_first = 0

        # long action name; start on the next line
        sonst:
            tup = self._current_indent, '', action_header
            action_header = '%*s%s\n' % tup
            indent_first = help_position

        # collect the pieces of the action help
        parts = [action_header]

        # wenn there was help fuer the action, add lines of help text
        wenn action.help und action.help.strip():
            help_text = self._expand_help(action)
            wenn help_text:
                help_lines = self._split_lines(help_text, help_width)
                parts.append('%*s%s\n' % (indent_first, '', help_lines[0]))
                fuer line in help_lines[1:]:
                    parts.append('%*s%s\n' % (help_position, '', line))

        # oder add a newline wenn the description doesn't end mit one
        sowenn nicht action_header.endswith('\n'):
            parts.append('\n')

        # wenn there are any sub-actions, add their help als well
        fuer subaction in self._iter_indented_subactions(action):
            parts.append(self._format_action(subaction))

        # return a single string
        return self._join_parts(parts)

    def _format_action_invocation(self, action):
        t = self._theme

        wenn nicht action.option_strings:
            default = self._get_default_metavar_for_positional(action)
            return (
                t.action
                + ' '.join(self._metavar_formatter(action, default)(1))
                + t.reset
            )

        sonst:

            def color_option_strings(strings):
                parts = []
                fuer s in strings:
                    wenn self._is_long_option(s):
                        parts.append(f"{t.long_option}{s}{t.reset}")
                    sonst:
                        parts.append(f"{t.short_option}{s}{t.reset}")
                return parts

            # wenn the Optional doesn't take a value, format is:
            #    -s, --long
            wenn action.nargs == 0:
                option_strings = color_option_strings(action.option_strings)
                return ', '.join(option_strings)

            # wenn the Optional takes a value, format is:
            #    -s, --long ARGS
            sonst:
                default = self._get_default_metavar_for_optional(action)
                option_strings = color_option_strings(action.option_strings)
                args_string = (
                    f"{t.label}{self._format_args(action, default)}{t.reset}"
                )
                return ', '.join(option_strings) + ' ' + args_string

    def _metavar_formatter(self, action, default_metavar):
        wenn action.metavar is nicht Nichts:
            result = action.metavar
        sowenn action.choices is nicht Nichts:
            result = '{%s}' % ','.join(map(str, action.choices))
        sonst:
            result = default_metavar

        def format(tuple_size):
            wenn isinstance(result, tuple):
                return result
            sonst:
                return (result, ) * tuple_size
        return format

    def _format_args(self, action, default_metavar):
        get_metavar = self._metavar_formatter(action, default_metavar)
        wenn action.nargs is Nichts:
            result = '%s' % get_metavar(1)
        sowenn action.nargs == OPTIONAL:
            result = '[%s]' % get_metavar(1)
        sowenn action.nargs == ZERO_OR_MORE:
            metavar = get_metavar(1)
            wenn len(metavar) == 2:
                result = '[%s [%s ...]]' % metavar
            sonst:
                result = '[%s ...]' % metavar
        sowenn action.nargs == ONE_OR_MORE:
            result = '%s [%s ...]' % get_metavar(2)
        sowenn action.nargs == REMAINDER:
            result = '...'
        sowenn action.nargs == PARSER:
            result = '%s ...' % get_metavar(1)
        sowenn action.nargs == SUPPRESS:
            result = ''
        sonst:
            try:
                formats = ['%s' fuer _ in range(action.nargs)]
            except TypeError:
                raise ValueError("invalid nargs value") von Nichts
            result = ' '.join(formats) % get_metavar(action.nargs)
        return result

    def _expand_help(self, action):
        help_string = self._get_help_string(action)
        wenn '%' nicht in help_string:
            return help_string
        params = dict(vars(action), prog=self._prog)
        fuer name in list(params):
            value = params[name]
            wenn value is SUPPRESS:
                del params[name]
            sowenn hasattr(value, '__name__'):
                params[name] = value.__name__
        wenn params.get('choices') is nicht Nichts:
            params['choices'] = ', '.join(map(str, params['choices']))
        return help_string % params

    def _iter_indented_subactions(self, action):
        try:
            get_subactions = action._get_subactions
        except AttributeError:
            pass
        sonst:
            self._indent()
            yield von get_subactions()
            self._dedent()

    def _split_lines(self, text, width):
        text = self._whitespace_matcher.sub(' ', text).strip()
        # The textwrap module is used only fuer formatting help.
        # Delay its importiere fuer speeding up the common usage of argparse.
        importiere textwrap
        return textwrap.wrap(text, width)

    def _fill_text(self, text, width, indent):
        text = self._whitespace_matcher.sub(' ', text).strip()
        importiere textwrap
        return textwrap.fill(text, width,
                             initial_indent=indent,
                             subsequent_indent=indent)

    def _get_help_string(self, action):
        return action.help

    def _get_default_metavar_for_optional(self, action):
        return action.dest.upper()

    def _get_default_metavar_for_positional(self, action):
        return action.dest


klasse RawDescriptionHelpFormatter(HelpFormatter):
    """Help message formatter which retains any formatting in descriptions.

    Only the name of this klasse is considered a public API. All the methods
    provided by the klasse are considered an implementation detail.
    """

    def _fill_text(self, text, width, indent):
        return ''.join(indent + line fuer line in text.splitlines(keepends=Wahr))


klasse RawTextHelpFormatter(RawDescriptionHelpFormatter):
    """Help message formatter which retains formatting of all help text.

    Only the name of this klasse is considered a public API. All the methods
    provided by the klasse are considered an implementation detail.
    """

    def _split_lines(self, text, width):
        return text.splitlines()


klasse ArgumentDefaultsHelpFormatter(HelpFormatter):
    """Help message formatter which adds default values to argument help.

    Only the name of this klasse is considered a public API. All the methods
    provided by the klasse are considered an implementation detail.
    """

    def _get_help_string(self, action):
        help = action.help
        wenn help is Nichts:
            help = ''

        wenn '%(default)' nicht in help:
            wenn action.default is nicht SUPPRESS:
                defaulting_nargs = [OPTIONAL, ZERO_OR_MORE]
                wenn action.option_strings oder action.nargs in defaulting_nargs:
                    help += _(' (default: %(default)s)')
        return help



klasse MetavarTypeHelpFormatter(HelpFormatter):
    """Help message formatter which uses the argument 'type' als the default
    metavar value (instead of the argument 'dest')

    Only the name of this klasse is considered a public API. All the methods
    provided by the klasse are considered an implementation detail.
    """

    def _get_default_metavar_for_optional(self, action):
        return action.type.__name__

    def _get_default_metavar_for_positional(self, action):
        return action.type.__name__


# =====================
# Options und Arguments
# =====================

def _get_action_name(argument):
    wenn argument is Nichts:
        return Nichts
    sowenn argument.option_strings:
        return '/'.join(argument.option_strings)
    sowenn argument.metavar nicht in (Nichts, SUPPRESS):
        metavar = argument.metavar
        wenn nicht isinstance(metavar, tuple):
            return metavar
        wenn argument.nargs == ZERO_OR_MORE und len(metavar) == 2:
            return '%s[, %s]' % metavar
        sowenn argument.nargs == ONE_OR_MORE:
            return '%s[, %s]' % metavar
        sonst:
            return ', '.join(metavar)
    sowenn argument.dest nicht in (Nichts, SUPPRESS):
        return argument.dest
    sowenn argument.choices:
        return '{%s}' % ','.join(map(str, argument.choices))
    sonst:
        return Nichts


klasse ArgumentError(Exception):
    """An error von creating oder using an argument (optional oder positional).

    The string value of this exception is the message, augmented with
    information about the argument that caused it.
    """

    def __init__(self, argument, message):
        self.argument_name = _get_action_name(argument)
        self.message = message

    def __str__(self):
        wenn self.argument_name is Nichts:
            format = '%(message)s'
        sonst:
            format = _('argument %(argument_name)s: %(message)s')
        return format % dict(message=self.message,
                             argument_name=self.argument_name)


klasse ArgumentTypeError(Exception):
    """An error von trying to convert a command line string to a type."""
    pass


# ==============
# Action classes
# ==============

klasse Action(_AttributeHolder):
    """Information about how to convert command line strings to Python objects.

    Action objects are used by an ArgumentParser to represent the information
    needed to parse a single argument von one oder more strings von the
    command line. The keyword arguments to the Action constructor are also
    all attributes of Action instances.

    Keyword Arguments:

        - option_strings -- A list of command-line option strings which
            should be associated mit this action.

        - dest -- The name of the attribute to hold the created object(s)

        - nargs -- The number of command-line arguments that should be
            consumed. By default, one argument will be consumed und a single
            value will be produced.  Other values include:
                - N (an integer) consumes N arguments (and produces a list)
                - '?' consumes zero oder one arguments
                - '*' consumes zero oder more arguments (and produces a list)
                - '+' consumes one oder more arguments (and produces a list)
            Note that the difference between the default und nargs=1 is that
            mit the default, a single value will be produced, waehrend with
            nargs=1, a list containing a single value will be produced.

        - const -- The value to be produced wenn the option is specified und the
            option uses an action that takes no values.

        - default -- The value to be produced wenn the option is nicht specified.

        - type -- A callable that accepts a single string argument, und
            returns the converted value.  The standard Python types str, int,
            float, und complex are useful examples of such callables.  If Nichts,
            str is used.

        - choices -- A container of values that should be allowed. If nicht Nichts,
            after a command-line argument has been converted to the appropriate
            type, an exception will be raised wenn it is nicht a member of this
            collection.

        - required -- Wahr wenn the action must always be specified at the
            command line. This is only meaningful fuer optional command-line
            arguments.

        - help -- The help string describing the argument.

        - metavar -- The name to be used fuer the option's argument mit the
            help string. If Nichts, the 'dest' value will be used als the name.
    """

    def __init__(self,
                 option_strings,
                 dest,
                 nargs=Nichts,
                 const=Nichts,
                 default=Nichts,
                 type=Nichts,
                 choices=Nichts,
                 required=Falsch,
                 help=Nichts,
                 metavar=Nichts,
                 deprecated=Falsch):
        self.option_strings = option_strings
        self.dest = dest
        self.nargs = nargs
        self.const = const
        self.default = default
        self.type = type
        self.choices = choices
        self.required = required
        self.help = help
        self.metavar = metavar
        self.deprecated = deprecated

    def _get_kwargs(self):
        names = [
            'option_strings',
            'dest',
            'nargs',
            'const',
            'default',
            'type',
            'choices',
            'required',
            'help',
            'metavar',
            'deprecated',
        ]
        return [(name, getattr(self, name)) fuer name in names]

    def format_usage(self):
        return self.option_strings[0]

    def __call__(self, parser, namespace, values, option_string=Nichts):
        raise NotImplementedError('.__call__() nicht defined')


klasse BooleanOptionalAction(Action):
    def __init__(self,
                 option_strings,
                 dest,
                 default=Nichts,
                 required=Falsch,
                 help=Nichts,
                 deprecated=Falsch):

        _option_strings = []
        fuer option_string in option_strings:
            _option_strings.append(option_string)

            wenn option_string.startswith('--'):
                wenn option_string.startswith('--no-'):
                    raise ValueError(f'invalid option name {option_string!r} '
                                     f'for BooleanOptionalAction')
                option_string = '--no-' + option_string[2:]
                _option_strings.append(option_string)

        super().__init__(
            option_strings=_option_strings,
            dest=dest,
            nargs=0,
            default=default,
            required=required,
            help=help,
            deprecated=deprecated)


    def __call__(self, parser, namespace, values, option_string=Nichts):
        wenn option_string in self.option_strings:
            setattr(namespace, self.dest, nicht option_string.startswith('--no-'))

    def format_usage(self):
        return ' | '.join(self.option_strings)


klasse _StoreAction(Action):

    def __init__(self,
                 option_strings,
                 dest,
                 nargs=Nichts,
                 const=Nichts,
                 default=Nichts,
                 type=Nichts,
                 choices=Nichts,
                 required=Falsch,
                 help=Nichts,
                 metavar=Nichts,
                 deprecated=Falsch):
        wenn nargs == 0:
            raise ValueError('nargs fuer store actions must be != 0; wenn you '
                             'have nothing to store, actions such als store '
                             'true oder store const may be more appropriate')
        wenn const is nicht Nichts und nargs != OPTIONAL:
            raise ValueError('nargs must be %r to supply const' % OPTIONAL)
        super(_StoreAction, self).__init__(
            option_strings=option_strings,
            dest=dest,
            nargs=nargs,
            const=const,
            default=default,
            type=type,
            choices=choices,
            required=required,
            help=help,
            metavar=metavar,
            deprecated=deprecated)

    def __call__(self, parser, namespace, values, option_string=Nichts):
        setattr(namespace, self.dest, values)


klasse _StoreConstAction(Action):

    def __init__(self,
                 option_strings,
                 dest,
                 const=Nichts,
                 default=Nichts,
                 required=Falsch,
                 help=Nichts,
                 metavar=Nichts,
                 deprecated=Falsch):
        super(_StoreConstAction, self).__init__(
            option_strings=option_strings,
            dest=dest,
            nargs=0,
            const=const,
            default=default,
            required=required,
            help=help,
            deprecated=deprecated)

    def __call__(self, parser, namespace, values, option_string=Nichts):
        setattr(namespace, self.dest, self.const)


klasse _StoreWahrAction(_StoreConstAction):

    def __init__(self,
                 option_strings,
                 dest,
                 default=Falsch,
                 required=Falsch,
                 help=Nichts,
                 deprecated=Falsch):
        super(_StoreWahrAction, self).__init__(
            option_strings=option_strings,
            dest=dest,
            const=Wahr,
            deprecated=deprecated,
            required=required,
            help=help,
            default=default)


klasse _StoreFalschAction(_StoreConstAction):

    def __init__(self,
                 option_strings,
                 dest,
                 default=Wahr,
                 required=Falsch,
                 help=Nichts,
                 deprecated=Falsch):
        super(_StoreFalschAction, self).__init__(
            option_strings=option_strings,
            dest=dest,
            const=Falsch,
            default=default,
            required=required,
            help=help,
            deprecated=deprecated)


klasse _AppendAction(Action):

    def __init__(self,
                 option_strings,
                 dest,
                 nargs=Nichts,
                 const=Nichts,
                 default=Nichts,
                 type=Nichts,
                 choices=Nichts,
                 required=Falsch,
                 help=Nichts,
                 metavar=Nichts,
                 deprecated=Falsch):
        wenn nargs == 0:
            raise ValueError('nargs fuer append actions must be != 0; wenn arg '
                             'strings are nicht supplying the value to append, '
                             'the append const action may be more appropriate')
        wenn const is nicht Nichts und nargs != OPTIONAL:
            raise ValueError('nargs must be %r to supply const' % OPTIONAL)
        super(_AppendAction, self).__init__(
            option_strings=option_strings,
            dest=dest,
            nargs=nargs,
            const=const,
            default=default,
            type=type,
            choices=choices,
            required=required,
            help=help,
            metavar=metavar,
            deprecated=deprecated)

    def __call__(self, parser, namespace, values, option_string=Nichts):
        items = getattr(namespace, self.dest, Nichts)
        items = _copy_items(items)
        items.append(values)
        setattr(namespace, self.dest, items)


klasse _AppendConstAction(Action):

    def __init__(self,
                 option_strings,
                 dest,
                 const=Nichts,
                 default=Nichts,
                 required=Falsch,
                 help=Nichts,
                 metavar=Nichts,
                 deprecated=Falsch):
        super(_AppendConstAction, self).__init__(
            option_strings=option_strings,
            dest=dest,
            nargs=0,
            const=const,
            default=default,
            required=required,
            help=help,
            metavar=metavar,
            deprecated=deprecated)

    def __call__(self, parser, namespace, values, option_string=Nichts):
        items = getattr(namespace, self.dest, Nichts)
        items = _copy_items(items)
        items.append(self.const)
        setattr(namespace, self.dest, items)


klasse _CountAction(Action):

    def __init__(self,
                 option_strings,
                 dest,
                 default=Nichts,
                 required=Falsch,
                 help=Nichts,
                 deprecated=Falsch):
        super(_CountAction, self).__init__(
            option_strings=option_strings,
            dest=dest,
            nargs=0,
            default=default,
            required=required,
            help=help,
            deprecated=deprecated)

    def __call__(self, parser, namespace, values, option_string=Nichts):
        count = getattr(namespace, self.dest, Nichts)
        wenn count is Nichts:
            count = 0
        setattr(namespace, self.dest, count + 1)


klasse _HelpAction(Action):

    def __init__(self,
                 option_strings,
                 dest=SUPPRESS,
                 default=SUPPRESS,
                 help=Nichts,
                 deprecated=Falsch):
        super(_HelpAction, self).__init__(
            option_strings=option_strings,
            dest=dest,
            default=default,
            nargs=0,
            help=help,
            deprecated=deprecated)

    def __call__(self, parser, namespace, values, option_string=Nichts):
        parser.print_help()
        parser.exit()


klasse _VersionAction(Action):

    def __init__(self,
                 option_strings,
                 version=Nichts,
                 dest=SUPPRESS,
                 default=SUPPRESS,
                 help=Nichts,
                 deprecated=Falsch):
        wenn help is Nichts:
            help = _("show program's version number und exit")
        super(_VersionAction, self).__init__(
            option_strings=option_strings,
            dest=dest,
            default=default,
            nargs=0,
            help=help)
        self.version = version

    def __call__(self, parser, namespace, values, option_string=Nichts):
        version = self.version
        wenn version is Nichts:
            version = parser.version
        formatter = parser._get_formatter()
        formatter.add_text(version)
        parser._print_message(formatter.format_help(), _sys.stdout)
        parser.exit()


klasse _SubParsersAction(Action):

    klasse _ChoicesPseudoAction(Action):

        def __init__(self, name, aliases, help):
            metavar = dest = name
            wenn aliases:
                metavar += ' (%s)' % ', '.join(aliases)
            sup = super(_SubParsersAction._ChoicesPseudoAction, self)
            sup.__init__(option_strings=[], dest=dest, help=help,
                         metavar=metavar)

    def __init__(self,
                 option_strings,
                 prog,
                 parser_class,
                 dest=SUPPRESS,
                 required=Falsch,
                 help=Nichts,
                 metavar=Nichts):

        self._prog_prefix = prog
        self._parser_class = parser_class
        self._name_parser_map = {}
        self._choices_actions = []
        self._deprecated = set()
        self._color = Wahr

        super(_SubParsersAction, self).__init__(
            option_strings=option_strings,
            dest=dest,
            nargs=PARSER,
            choices=self._name_parser_map,
            required=required,
            help=help,
            metavar=metavar)

    def add_parser(self, name, *, deprecated=Falsch, **kwargs):
        # set prog von the existing prefix
        wenn kwargs.get('prog') is Nichts:
            kwargs['prog'] = '%s %s' % (self._prog_prefix, name)

        # set color
        wenn kwargs.get('color') is Nichts:
            kwargs['color'] = self._color

        aliases = kwargs.pop('aliases', ())

        wenn name in self._name_parser_map:
            raise ValueError(f'conflicting subparser: {name}')
        fuer alias in aliases:
            wenn alias in self._name_parser_map:
                raise ValueError(f'conflicting subparser alias: {alias}')

        # create a pseudo-action to hold the choice help
        wenn 'help' in kwargs:
            help = kwargs.pop('help')
            choice_action = self._ChoicesPseudoAction(name, aliases, help)
            self._choices_actions.append(choice_action)
        sonst:
            choice_action = Nichts

        # create the parser und add it to the map
        parser = self._parser_class(**kwargs)
        wenn choice_action is nicht Nichts:
            parser._check_help(choice_action)
        self._name_parser_map[name] = parser

        # make parser available under aliases also
        fuer alias in aliases:
            self._name_parser_map[alias] = parser

        wenn deprecated:
            self._deprecated.add(name)
            self._deprecated.update(aliases)

        return parser

    def _get_subactions(self):
        return self._choices_actions

    def __call__(self, parser, namespace, values, option_string=Nichts):
        parser_name = values[0]
        arg_strings = values[1:]

        # set the parser name wenn requested
        wenn self.dest is nicht SUPPRESS:
            setattr(namespace, self.dest, parser_name)

        # select the parser
        try:
            subparser = self._name_parser_map[parser_name]
        except KeyError:
            args = {'parser_name': parser_name,
                    'choices': ', '.join(self._name_parser_map)}
            msg = _('unknown parser %(parser_name)r (choices: %(choices)s)') % args
            raise ArgumentError(self, msg)

        wenn parser_name in self._deprecated:
            parser._warning(_("command '%(parser_name)s' is deprecated") %
                            {'parser_name': parser_name})

        # parse all the remaining options into the namespace
        # store any unrecognized options on the object, so that the top
        # level parser can decide what to do mit them

        # In case this subparser defines new defaults, we parse them
        # in a new namespace object und then update the original
        # namespace fuer the relevant parts.
        subnamespace, arg_strings = subparser.parse_known_args(arg_strings, Nichts)
        fuer key, value in vars(subnamespace).items():
            setattr(namespace, key, value)

        wenn arg_strings:
            wenn nicht hasattr(namespace, _UNRECOGNIZED_ARGS_ATTR):
                setattr(namespace, _UNRECOGNIZED_ARGS_ATTR, [])
            getattr(namespace, _UNRECOGNIZED_ARGS_ATTR).extend(arg_strings)

klasse _ExtendAction(_AppendAction):
    def __call__(self, parser, namespace, values, option_string=Nichts):
        items = getattr(namespace, self.dest, Nichts)
        items = _copy_items(items)
        items.extend(values)
        setattr(namespace, self.dest, items)

# ==============
# Type classes
# ==============

klasse FileType(object):
    """Deprecated factory fuer creating file object types

    Instances of FileType are typically passed als type= arguments to the
    ArgumentParser add_argument() method.

    Keyword Arguments:
        - mode -- A string indicating how the file is to be opened. Accepts the
            same values als the builtin open() function.
        - bufsize -- The file's desired buffer size. Accepts the same values as
            the builtin open() function.
        - encoding -- The file's encoding. Accepts the same values als the
            builtin open() function.
        - errors -- A string indicating how encoding und decoding errors are to
            be handled. Accepts the same value als the builtin open() function.
    """

    def __init__(self, mode='r', bufsize=-1, encoding=Nichts, errors=Nichts):
        importiere warnings
        warnings.warn(
            "FileType is deprecated. Simply open files after parsing arguments.",
            category=PendingDeprecationWarning,
            stacklevel=2
        )
        self._mode = mode
        self._bufsize = bufsize
        self._encoding = encoding
        self._errors = errors

    def __call__(self, string):
        # the special argument "-" means sys.std{in,out}
        wenn string == '-':
            wenn 'r' in self._mode:
                return _sys.stdin.buffer wenn 'b' in self._mode sonst _sys.stdin
            sowenn any(c in self._mode fuer c in 'wax'):
                return _sys.stdout.buffer wenn 'b' in self._mode sonst _sys.stdout
            sonst:
                msg = _('argument "-" mit mode %r') % self._mode
                raise ValueError(msg)

        # all other arguments are used als file names
        try:
            return open(string, self._mode, self._bufsize, self._encoding,
                        self._errors)
        except OSError als e:
            args = {'filename': string, 'error': e}
            message = _("can't open '%(filename)s': %(error)s")
            raise ArgumentTypeError(message % args)

    def __repr__(self):
        args = self._mode, self._bufsize
        kwargs = [('encoding', self._encoding), ('errors', self._errors)]
        args_str = ', '.join([repr(arg) fuer arg in args wenn arg != -1] +
                             ['%s=%r' % (kw, arg) fuer kw, arg in kwargs
                              wenn arg is nicht Nichts])
        return '%s(%s)' % (type(self).__name__, args_str)

# ===========================
# Optional und Positional Parsing
# ===========================

klasse Namespace(_AttributeHolder):
    """Simple object fuer storing attributes.

    Implements equality by attribute names und values, und provides a simple
    string representation.
    """

    def __init__(self, **kwargs):
        fuer name in kwargs:
            setattr(self, name, kwargs[name])

    def __eq__(self, other):
        wenn nicht isinstance(other, Namespace):
            return NotImplemented
        return vars(self) == vars(other)

    def __contains__(self, key):
        return key in self.__dict__


klasse _ActionsContainer(object):

    def __init__(self,
                 description,
                 prefix_chars,
                 argument_default,
                 conflict_handler):
        super(_ActionsContainer, self).__init__()

        self.description = description
        self.argument_default = argument_default
        self.prefix_chars = prefix_chars
        self.conflict_handler = conflict_handler

        # set up registries
        self._registries = {}

        # register actions
        self.register('action', Nichts, _StoreAction)
        self.register('action', 'store', _StoreAction)
        self.register('action', 'store_const', _StoreConstAction)
        self.register('action', 'store_true', _StoreWahrAction)
        self.register('action', 'store_false', _StoreFalschAction)
        self.register('action', 'append', _AppendAction)
        self.register('action', 'append_const', _AppendConstAction)
        self.register('action', 'count', _CountAction)
        self.register('action', 'help', _HelpAction)
        self.register('action', 'version', _VersionAction)
        self.register('action', 'parsers', _SubParsersAction)
        self.register('action', 'extend', _ExtendAction)

        # raise an exception wenn the conflict handler is invalid
        self._get_handler()

        # action storage
        self._actions = []
        self._option_string_actions = {}

        # groups
        self._action_groups = []
        self._mutually_exclusive_groups = []

        # defaults storage
        self._defaults = {}

        # determines whether an "option" looks like a negative number
        self._negative_number_matcher = _re.compile(r'-\.?\d')

        # whether oder nicht there are any optionals that look like negative
        # numbers -- uses a list so it can be shared und edited
        self._has_negative_number_optionals = []

    # ====================
    # Registration methods
    # ====================

    def register(self, registry_name, value, object):
        registry = self._registries.setdefault(registry_name, {})
        registry[value] = object

    def _registry_get(self, registry_name, value, default=Nichts):
        return self._registries[registry_name].get(value, default)

    # ==================================
    # Namespace default accessor methods
    # ==================================

    def set_defaults(self, **kwargs):
        self._defaults.update(kwargs)

        # wenn these defaults match any existing arguments, replace
        # the previous default on the object mit the new one
        fuer action in self._actions:
            wenn action.dest in kwargs:
                action.default = kwargs[action.dest]

    def get_default(self, dest):
        fuer action in self._actions:
            wenn action.dest == dest und action.default is nicht Nichts:
                return action.default
        return self._defaults.get(dest, Nichts)


    # =======================
    # Adding argument actions
    # =======================

    def add_argument(self, *args, **kwargs):
        """
        add_argument(dest, ..., name=value, ...)
        add_argument(option_string, option_string, ..., name=value, ...)
        """

        # wenn no positional args are supplied oder only one is supplied und
        # it doesn't look like an option string, parse a positional
        # argument
        chars = self.prefix_chars
        wenn nicht args oder len(args) == 1 und args[0][0] nicht in chars:
            wenn args und 'dest' in kwargs:
                raise TypeError('dest supplied twice fuer positional argument,'
                                ' did you mean metavar?')
            kwargs = self._get_positional_kwargs(*args, **kwargs)

        # otherwise, we're adding an optional argument
        sonst:
            kwargs = self._get_optional_kwargs(*args, **kwargs)

        # wenn no default was supplied, use the parser-level default
        wenn 'default' nicht in kwargs:
            dest = kwargs['dest']
            wenn dest in self._defaults:
                kwargs['default'] = self._defaults[dest]
            sowenn self.argument_default is nicht Nichts:
                kwargs['default'] = self.argument_default

        # create the action object, und add it to the parser
        action_name = kwargs.get('action')
        action_class = self._pop_action_class(kwargs)
        wenn nicht callable(action_class):
            raise ValueError(f'unknown action {action_class!r}')
        action = action_class(**kwargs)

        # raise an error wenn action fuer positional argument does not
        # consume arguments
        wenn nicht action.option_strings und action.nargs == 0:
            raise ValueError(f'action {action_name!r} is nicht valid fuer positional arguments')

        # raise an error wenn the action type is nicht callable
        type_func = self._registry_get('type', action.type, action.type)
        wenn nicht callable(type_func):
            raise TypeError(f'{type_func!r} is nicht callable')

        wenn type_func is FileType:
            raise TypeError(f'{type_func!r} is a FileType klasse object, '
                            f'instance of it must be passed')

        # raise an error wenn the metavar does nicht match the type
        wenn hasattr(self, "_get_formatter"):
            formatter = self._get_formatter()
            try:
                formatter._format_args(action, Nichts)
            except TypeError:
                raise ValueError("length of metavar tuple does nicht match nargs")
        self._check_help(action)
        return self._add_action(action)

    def add_argument_group(self, *args, **kwargs):
        group = _ArgumentGroup(self, *args, **kwargs)
        self._action_groups.append(group)
        return group

    def add_mutually_exclusive_group(self, **kwargs):
        group = _MutuallyExclusiveGroup(self, **kwargs)
        self._mutually_exclusive_groups.append(group)
        return group

    def _add_action(self, action):
        # resolve any conflicts
        self._check_conflict(action)

        # add to actions list
        self._actions.append(action)
        action.container = self

        # index the action by any option strings it has
        fuer option_string in action.option_strings:
            self._option_string_actions[option_string] = action

        # set the flag wenn any option strings look like negative numbers
        fuer option_string in action.option_strings:
            wenn self._negative_number_matcher.match(option_string):
                wenn nicht self._has_negative_number_optionals:
                    self._has_negative_number_optionals.append(Wahr)

        # return the created action
        return action

    def _remove_action(self, action):
        self._actions.remove(action)

    def _add_container_actions(self, container):
        # collect groups by titles
        title_group_map = {}
        fuer group in self._action_groups:
            wenn group.title in title_group_map:
                # This branch could happen wenn a derived klasse added
                # groups mit duplicated titles in __init__
                msg = f'cannot merge actions - two groups are named {group.title!r}'
                raise ValueError(msg)
            title_group_map[group.title] = group

        # map each action to its group
        group_map = {}
        fuer group in container._action_groups:

            # wenn a group mit the title exists, use that, otherwise
            # create a new group matching the container's group
            wenn group.title nicht in title_group_map:
                title_group_map[group.title] = self.add_argument_group(
                    title=group.title,
                    description=group.description,
                    conflict_handler=group.conflict_handler)

            # map the actions to their new group
            fuer action in group._group_actions:
                group_map[action] = title_group_map[group.title]

        # add container's mutually exclusive groups
        # NOTE: wenn add_mutually_exclusive_group ever gains title= und
        # description= then this code will need to be expanded als above
        fuer group in container._mutually_exclusive_groups:
            wenn group._container is container:
                cont = self
            sonst:
                cont = title_group_map[group._container.title]
            mutex_group = cont.add_mutually_exclusive_group(
                required=group.required)

            # map the actions to their new mutex group
            fuer action in group._group_actions:
                group_map[action] = mutex_group

        # add all actions to this container oder their group
        fuer action in container._actions:
            group_map.get(action, self)._add_action(action)

    def _get_positional_kwargs(self, dest, **kwargs):
        # make sure required is nicht specified
        wenn 'required' in kwargs:
            msg = "'required' is an invalid argument fuer positionals"
            raise TypeError(msg)

        # mark positional arguments als required wenn at least one is
        # always required
        nargs = kwargs.get('nargs')
        wenn nargs == 0:
            raise ValueError('nargs fuer positionals must be != 0')
        wenn nargs nicht in [OPTIONAL, ZERO_OR_MORE, REMAINDER, SUPPRESS]:
            kwargs['required'] = Wahr

        # return the keyword arguments mit no option strings
        return dict(kwargs, dest=dest, option_strings=[])

    def _get_optional_kwargs(self, *args, **kwargs):
        # determine short und long option strings
        option_strings = []
        long_option_strings = []
        fuer option_string in args:
            # error on strings that don't start mit an appropriate prefix
            wenn nicht option_string[0] in self.prefix_chars:
                raise ValueError(
                    f'invalid option string {option_string!r}: '
                    f'must start mit a character {self.prefix_chars!r}')

            # strings starting mit two prefix characters are long options
            option_strings.append(option_string)
            wenn len(option_string) > 1 und option_string[1] in self.prefix_chars:
                long_option_strings.append(option_string)

        # infer destination, '--foo-bar' -> 'foo_bar' und '-x' -> 'x'
        dest = kwargs.pop('dest', Nichts)
        wenn dest is Nichts:
            wenn long_option_strings:
                dest_option_string = long_option_strings[0]
            sonst:
                dest_option_string = option_strings[0]
            dest = dest_option_string.lstrip(self.prefix_chars)
            wenn nicht dest:
                msg = f'dest= is required fuer options like {option_string!r}'
                raise TypeError(msg)
            dest = dest.replace('-', '_')

        # return the updated keyword arguments
        return dict(kwargs, dest=dest, option_strings=option_strings)

    def _pop_action_class(self, kwargs, default=Nichts):
        action = kwargs.pop('action', default)
        return self._registry_get('action', action, action)

    def _get_handler(self):
        # determine function von conflict handler string
        handler_func_name = '_handle_conflict_%s' % self.conflict_handler
        try:
            return getattr(self, handler_func_name)
        except AttributeError:
            msg = f'invalid conflict_resolution value: {self.conflict_handler!r}'
            raise ValueError(msg)

    def _check_conflict(self, action):

        # find all options that conflict mit this option
        confl_optionals = []
        fuer option_string in action.option_strings:
            wenn option_string in self._option_string_actions:
                confl_optional = self._option_string_actions[option_string]
                confl_optionals.append((option_string, confl_optional))

        # resolve any conflicts
        wenn confl_optionals:
            conflict_handler = self._get_handler()
            conflict_handler(action, confl_optionals)

    def _handle_conflict_error(self, action, conflicting_actions):
        message = ngettext('conflicting option string: %s',
                           'conflicting option strings: %s',
                           len(conflicting_actions))
        conflict_string = ', '.join([option_string
                                     fuer option_string, action
                                     in conflicting_actions])
        raise ArgumentError(action, message % conflict_string)

    def _handle_conflict_resolve(self, action, conflicting_actions):

        # remove all conflicting options
        fuer option_string, action in conflicting_actions:

            # remove the conflicting option
            action.option_strings.remove(option_string)
            self._option_string_actions.pop(option_string, Nichts)

            # wenn the option now has no option string, remove it von the
            # container holding it
            wenn nicht action.option_strings:
                action.container._remove_action(action)

    def _check_help(self, action):
        wenn action.help und hasattr(self, "_get_formatter"):
            formatter = self._get_formatter()
            try:
                formatter._expand_help(action)
            except (ValueError, TypeError, KeyError) als exc:
                raise ValueError('badly formed help string') von exc


klasse _ArgumentGroup(_ActionsContainer):

    def __init__(self, container, title=Nichts, description=Nichts, **kwargs):
        wenn 'prefix_chars' in kwargs:
            importiere warnings
            depr_msg = (
                "The use of the undocumented 'prefix_chars' parameter in "
                "ArgumentParser.add_argument_group() is deprecated."
            )
            warnings.warn(depr_msg, DeprecationWarning, stacklevel=3)

        # add any missing keyword arguments by checking the container
        update = kwargs.setdefault
        update('conflict_handler', container.conflict_handler)
        update('prefix_chars', container.prefix_chars)
        update('argument_default', container.argument_default)
        super_init = super(_ArgumentGroup, self).__init__
        super_init(description=description, **kwargs)

        # group attributes
        self.title = title
        self._group_actions = []

        # share most attributes mit the container
        self._registries = container._registries
        self._actions = container._actions
        self._option_string_actions = container._option_string_actions
        self._defaults = container._defaults
        self._has_negative_number_optionals = \
            container._has_negative_number_optionals
        self._mutually_exclusive_groups = container._mutually_exclusive_groups

    def _add_action(self, action):
        action = super(_ArgumentGroup, self)._add_action(action)
        self._group_actions.append(action)
        return action

    def _remove_action(self, action):
        super(_ArgumentGroup, self)._remove_action(action)
        self._group_actions.remove(action)

    def add_argument_group(self, *args, **kwargs):
        raise ValueError('argument groups cannot be nested')

klasse _MutuallyExclusiveGroup(_ArgumentGroup):

    def __init__(self, container, required=Falsch):
        super(_MutuallyExclusiveGroup, self).__init__(container)
        self.required = required
        self._container = container

    def _add_action(self, action):
        wenn action.required:
            msg = 'mutually exclusive arguments must be optional'
            raise ValueError(msg)
        action = self._container._add_action(action)
        self._group_actions.append(action)
        return action

    def _remove_action(self, action):
        self._container._remove_action(action)
        self._group_actions.remove(action)

    def add_mutually_exclusive_group(self, **kwargs):
        raise ValueError('mutually exclusive groups cannot be nested')

def _prog_name(prog=Nichts):
    wenn prog is nicht Nichts:
        return prog
    arg0 = _sys.argv[0]
    try:
        modspec = _sys.modules['__main__'].__spec__
    except (KeyError, AttributeError):
        # possibly PYTHONSTARTUP oder -X presite oder other weird edge case
        # no good answer here, so fall back to the default
        modspec = Nichts
    wenn modspec is Nichts:
        # simple script
        return _os.path.basename(arg0)
    py = _os.path.basename(_sys.executable)
    wenn modspec.name != '__main__':
        # imported module oder package
        modname = modspec.name.removesuffix('.__main__')
        return f'{py} -m {modname}'
    # directory oder ZIP file
    return f'{py} {arg0}'


klasse ArgumentParser(_AttributeHolder, _ActionsContainer):
    """Object fuer parsing command line strings into Python objects.

    Keyword Arguments:
        - prog -- The name of the program (default:
            ``os.path.basename(sys.argv[0])``)
        - usage -- A usage message (default: auto-generated von arguments)
        - description -- A description of what the program does
        - epilog -- Text following the argument descriptions
        - parents -- Parsers whose arguments should be copied into this one
        - formatter_class -- HelpFormatter klasse fuer printing help messages
        - prefix_chars -- Characters that prefix optional arguments
        - fromfile_prefix_chars -- Characters that prefix files containing
            additional arguments
        - argument_default -- The default value fuer all arguments
        - conflict_handler -- String indicating how to handle conflicts
        - add_help -- Add a -h/-help option
        - allow_abbrev -- Allow long options to be abbreviated unambiguously
        - exit_on_error -- Determines whether oder nicht ArgumentParser exits with
            error info when an error occurs
        - suggest_on_error - Enables suggestions fuer mistyped argument choices
            und subparser names (default: ``Falsch``)
        - color - Allow color output in help messages (default: ``Falsch``)
    """

    def __init__(self,
                 prog=Nichts,
                 usage=Nichts,
                 description=Nichts,
                 epilog=Nichts,
                 parents=[],
                 formatter_class=HelpFormatter,
                 prefix_chars='-',
                 fromfile_prefix_chars=Nichts,
                 argument_default=Nichts,
                 conflict_handler='error',
                 add_help=Wahr,
                 allow_abbrev=Wahr,
                 exit_on_error=Wahr,
                 *,
                 suggest_on_error=Falsch,
                 color=Wahr,
                 ):
        superinit = super(ArgumentParser, self).__init__
        superinit(description=description,
                  prefix_chars=prefix_chars,
                  argument_default=argument_default,
                  conflict_handler=conflict_handler)

        self.prog = _prog_name(prog)
        self.usage = usage
        self.epilog = epilog
        self.formatter_class = formatter_class
        self.fromfile_prefix_chars = fromfile_prefix_chars
        self.add_help = add_help
        self.allow_abbrev = allow_abbrev
        self.exit_on_error = exit_on_error
        self.suggest_on_error = suggest_on_error
        self.color = color

        add_group = self.add_argument_group
        self._positionals = add_group(_('positional arguments'))
        self._optionals = add_group(_('options'))
        self._subparsers = Nichts

        # register types
        def identity(string):
            return string
        self.register('type', Nichts, identity)

        # add help argument wenn necessary
        # (using explicit default to override global argument_default)
        default_prefix = '-' wenn '-' in prefix_chars sonst prefix_chars[0]
        wenn self.add_help:
            self.add_argument(
                default_prefix+'h', default_prefix*2+'help',
                action='help', default=SUPPRESS,
                help=_('show this help message und exit'))

        # add parent arguments und defaults
        fuer parent in parents:
            wenn nicht isinstance(parent, ArgumentParser):
                raise TypeError('parents must be a list of ArgumentParser')
            self._add_container_actions(parent)
            defaults = parent._defaults
            self._defaults.update(defaults)

    # =======================
    # Pretty __repr__ methods
    # =======================

    def _get_kwargs(self):
        names = [
            'prog',
            'usage',
            'description',
            'formatter_class',
            'conflict_handler',
            'add_help',
        ]
        return [(name, getattr(self, name)) fuer name in names]

    # ==================================
    # Optional/Positional adding methods
    # ==================================

    def add_subparsers(self, **kwargs):
        wenn self._subparsers is nicht Nichts:
            raise ValueError('cannot have multiple subparser arguments')

        # add the parser klasse to the arguments wenn it's nicht present
        kwargs.setdefault('parser_class', type(self))

        wenn 'title' in kwargs oder 'description' in kwargs:
            title = kwargs.pop('title', _('subcommands'))
            description = kwargs.pop('description', Nichts)
            self._subparsers = self.add_argument_group(title, description)
        sonst:
            self._subparsers = self._positionals

        # prog defaults to the usage message of this parser, skipping
        # optional arguments und mit no "usage:" prefix
        wenn kwargs.get('prog') is Nichts:
            formatter = self._get_formatter()
            positionals = self._get_positional_actions()
            groups = self._mutually_exclusive_groups
            formatter.add_usage(Nichts, positionals, groups, '')
            kwargs['prog'] = formatter.format_help().strip()

        # create the parsers action und add it to the positionals list
        parsers_class = self._pop_action_class(kwargs, 'parsers')
        action = parsers_class(option_strings=[], **kwargs)
        action._color = self.color
        self._check_help(action)
        self._subparsers._add_action(action)

        # return the created parsers action
        return action

    def _add_action(self, action):
        wenn action.option_strings:
            self._optionals._add_action(action)
        sonst:
            self._positionals._add_action(action)
        return action

    def _get_optional_actions(self):
        return [action
                fuer action in self._actions
                wenn action.option_strings]

    def _get_positional_actions(self):
        return [action
                fuer action in self._actions
                wenn nicht action.option_strings]

    # =====================================
    # Command line argument parsing methods
    # =====================================

    def parse_args(self, args=Nichts, namespace=Nichts):
        args, argv = self.parse_known_args(args, namespace)
        wenn argv:
            msg = _('unrecognized arguments: %s') % ' '.join(argv)
            wenn self.exit_on_error:
                self.error(msg)
            sonst:
                raise ArgumentError(Nichts, msg)
        return args

    def parse_known_args(self, args=Nichts, namespace=Nichts):
        return self._parse_known_args2(args, namespace, intermixed=Falsch)

    def _parse_known_args2(self, args, namespace, intermixed):
        wenn args is Nichts:
            # args default to the system args
            args = _sys.argv[1:]
        sonst:
            # make sure that args are mutable
            args = list(args)

        # default Namespace built von parser defaults
        wenn namespace is Nichts:
            namespace = Namespace()

        # add any action defaults that aren't present
        fuer action in self._actions:
            wenn action.dest is nicht SUPPRESS:
                wenn nicht hasattr(namespace, action.dest):
                    wenn action.default is nicht SUPPRESS:
                        setattr(namespace, action.dest, action.default)

        # add any parser defaults that aren't present
        fuer dest in self._defaults:
            wenn nicht hasattr(namespace, dest):
                setattr(namespace, dest, self._defaults[dest])

        # parse the arguments und exit wenn there are any errors
        wenn self.exit_on_error:
            try:
                namespace, args = self._parse_known_args(args, namespace, intermixed)
            except ArgumentError als err:
                self.error(str(err))
        sonst:
            namespace, args = self._parse_known_args(args, namespace, intermixed)

        wenn hasattr(namespace, _UNRECOGNIZED_ARGS_ATTR):
            args.extend(getattr(namespace, _UNRECOGNIZED_ARGS_ATTR))
            delattr(namespace, _UNRECOGNIZED_ARGS_ATTR)
        return namespace, args

    def _parse_known_args(self, arg_strings, namespace, intermixed):
        # replace arg strings that are file references
        wenn self.fromfile_prefix_chars is nicht Nichts:
            arg_strings = self._read_args_from_files(arg_strings)

        # map all mutually exclusive arguments to the other arguments
        # they can't occur with
        action_conflicts = {}
        fuer mutex_group in self._mutually_exclusive_groups:
            group_actions = mutex_group._group_actions
            fuer i, mutex_action in enumerate(mutex_group._group_actions):
                conflicts = action_conflicts.setdefault(mutex_action, [])
                conflicts.extend(group_actions[:i])
                conflicts.extend(group_actions[i + 1:])

        # find all option indices, und determine the arg_string_pattern
        # which has an 'O' wenn there is an option at an index,
        # an 'A' wenn there is an argument, oder a '-' wenn there is a '--'
        option_string_indices = {}
        arg_string_pattern_parts = []
        arg_strings_iter = iter(arg_strings)
        fuer i, arg_string in enumerate(arg_strings_iter):

            # all args after -- are non-options
            wenn arg_string == '--':
                arg_string_pattern_parts.append('-')
                fuer arg_string in arg_strings_iter:
                    arg_string_pattern_parts.append('A')

            # otherwise, add the arg to the arg strings
            # und note the index wenn it was an option
            sonst:
                option_tuples = self._parse_optional(arg_string)
                wenn option_tuples is Nichts:
                    pattern = 'A'
                sonst:
                    option_string_indices[i] = option_tuples
                    pattern = 'O'
                arg_string_pattern_parts.append(pattern)

        # join the pieces together to form the pattern
        arg_strings_pattern = ''.join(arg_string_pattern_parts)

        # converts arg strings to the appropriate und then takes the action
        seen_actions = set()
        seen_non_default_actions = set()
        warned = set()

        def take_action(action, argument_strings, option_string=Nichts):
            seen_actions.add(action)
            argument_values = self._get_values(action, argument_strings)

            # error wenn this argument is nicht allowed mit other previously
            # seen arguments
            wenn action.option_strings oder argument_strings:
                seen_non_default_actions.add(action)
                fuer conflict_action in action_conflicts.get(action, []):
                    wenn conflict_action in seen_non_default_actions:
                        msg = _('not allowed mit argument %s')
                        action_name = _get_action_name(conflict_action)
                        raise ArgumentError(action, msg % action_name)

            # take the action wenn we didn't receive a SUPPRESS value
            # (e.g. von a default)
            wenn argument_values is nicht SUPPRESS:
                action(self, namespace, argument_values, option_string)

        # function to convert arg_strings into an optional action
        def consume_optional(start_index):

            # get the optional identified at this index
            option_tuples = option_string_indices[start_index]
            # wenn multiple actions match, the option string was ambiguous
            wenn len(option_tuples) > 1:
                options = ', '.join([option_string
                    fuer action, option_string, sep, explicit_arg in option_tuples])
                args = {'option': arg_strings[start_index], 'matches': options}
                msg = _('ambiguous option: %(option)s could match %(matches)s')
                raise ArgumentError(Nichts, msg % args)

            action, option_string, sep, explicit_arg = option_tuples[0]

            # identify additional optionals in the same arg string
            # (e.g. -xyz is the same als -x -y -z wenn no args are required)
            match_argument = self._match_argument
            action_tuples = []
            waehrend Wahr:

                # wenn we found no optional action, skip it
                wenn action is Nichts:
                    extras.append(arg_strings[start_index])
                    extras_pattern.append('O')
                    return start_index + 1

                # wenn there is an explicit argument, try to match the
                # optional's string arguments to only this
                wenn explicit_arg is nicht Nichts:
                    arg_count = match_argument(action, 'A')

                    # wenn the action is a single-dash option und takes no
                    # arguments, try to parse more single-dash options out
                    # of the tail of the option string
                    chars = self.prefix_chars
                    wenn (
                        arg_count == 0
                        und option_string[1] nicht in chars
                        und explicit_arg != ''
                    ):
                        wenn sep oder explicit_arg[0] in chars:
                            msg = _('ignored explicit argument %r')
                            raise ArgumentError(action, msg % explicit_arg)
                        action_tuples.append((action, [], option_string))
                        char = option_string[0]
                        option_string = char + explicit_arg[0]
                        optionals_map = self._option_string_actions
                        wenn option_string in optionals_map:
                            action = optionals_map[option_string]
                            explicit_arg = explicit_arg[1:]
                            wenn nicht explicit_arg:
                                sep = explicit_arg = Nichts
                            sowenn explicit_arg[0] == '=':
                                sep = '='
                                explicit_arg = explicit_arg[1:]
                            sonst:
                                sep = ''
                        sonst:
                            extras.append(char + explicit_arg)
                            extras_pattern.append('O')
                            stop = start_index + 1
                            breche
                    # wenn the action expect exactly one argument, we've
                    # successfully matched the option; exit the loop
                    sowenn arg_count == 1:
                        stop = start_index + 1
                        args = [explicit_arg]
                        action_tuples.append((action, args, option_string))
                        breche

                    # error wenn a double-dash option did nicht use the
                    # explicit argument
                    sonst:
                        msg = _('ignored explicit argument %r')
                        raise ArgumentError(action, msg % explicit_arg)

                # wenn there is no explicit argument, try to match the
                # optional's string arguments mit the following strings
                # wenn successful, exit the loop
                sonst:
                    start = start_index + 1
                    selected_patterns = arg_strings_pattern[start:]
                    arg_count = match_argument(action, selected_patterns)
                    stop = start + arg_count
                    args = arg_strings[start:stop]
                    action_tuples.append((action, args, option_string))
                    breche

            # add the Optional to the list und return the index at which
            # the Optional's string args stopped
            assert action_tuples
            fuer action, args, option_string in action_tuples:
                wenn action.deprecated und option_string nicht in warned:
                    self._warning(_("option '%(option)s' is deprecated") %
                                  {'option': option_string})
                    warned.add(option_string)
                take_action(action, args, option_string)
            return stop

        # the list of Positionals left to be parsed; this is modified
        # by consume_positionals()
        positionals = self._get_positional_actions()

        # function to convert arg_strings into positional actions
        def consume_positionals(start_index):
            # match als many Positionals als possible
            match_partial = self._match_arguments_partial
            selected_pattern = arg_strings_pattern[start_index:]
            arg_counts = match_partial(positionals, selected_pattern)

            # slice off the appropriate arg strings fuer each Positional
            # und add the Positional und its args to the list
            fuer action, arg_count in zip(positionals, arg_counts):
                args = arg_strings[start_index: start_index + arg_count]
                # Strip out the first '--' wenn it is nicht in REMAINDER arg.
                wenn action.nargs == PARSER:
                    wenn arg_strings_pattern[start_index] == '-':
                        assert args[0] == '--'
                        args.remove('--')
                sowenn action.nargs != REMAINDER:
                    wenn (arg_strings_pattern.find('-', start_index,
                                                 start_index + arg_count) >= 0):
                        args.remove('--')
                start_index += arg_count
                wenn args und action.deprecated und action.dest nicht in warned:
                    self._warning(_("argument '%(argument_name)s' is deprecated") %
                                  {'argument_name': action.dest})
                    warned.add(action.dest)
                take_action(action, args)

            # slice off the Positionals that we just parsed und return the
            # index at which the Positionals' string args stopped
            positionals[:] = positionals[len(arg_counts):]
            return start_index

        # consume Positionals und Optionals alternately, until we have
        # passed the last option string
        extras = []
        extras_pattern = []
        start_index = 0
        wenn option_string_indices:
            max_option_string_index = max(option_string_indices)
        sonst:
            max_option_string_index = -1
        waehrend start_index <= max_option_string_index:

            # consume any Positionals preceding the next option
            next_option_string_index = start_index
            waehrend next_option_string_index <= max_option_string_index:
                wenn next_option_string_index in option_string_indices:
                    breche
                next_option_string_index += 1
            wenn nicht intermixed und start_index != next_option_string_index:
                positionals_end_index = consume_positionals(start_index)

                # only try to parse the next optional wenn we didn't consume
                # the option string during the positionals parsing
                wenn positionals_end_index > start_index:
                    start_index = positionals_end_index
                    weiter
                sonst:
                    start_index = positionals_end_index

            # wenn we consumed all the positionals we could und we're not
            # at the index of an option string, there were extra arguments
            wenn start_index nicht in option_string_indices:
                strings = arg_strings[start_index:next_option_string_index]
                extras.extend(strings)
                extras_pattern.extend(arg_strings_pattern[start_index:next_option_string_index])
                start_index = next_option_string_index

            # consume the next optional und any arguments fuer it
            start_index = consume_optional(start_index)

        wenn nicht intermixed:
            # consume any positionals following the last Optional
            stop_index = consume_positionals(start_index)

            # wenn we didn't consume all the argument strings, there were extras
            extras.extend(arg_strings[stop_index:])
        sonst:
            extras.extend(arg_strings[start_index:])
            extras_pattern.extend(arg_strings_pattern[start_index:])
            extras_pattern = ''.join(extras_pattern)
            assert len(extras_pattern) == len(extras)
            # consume all positionals
            arg_strings = [s fuer s, c in zip(extras, extras_pattern) wenn c != 'O']
            arg_strings_pattern = extras_pattern.replace('O', '')
            stop_index = consume_positionals(0)
            # leave unknown optionals und non-consumed positionals in extras
            fuer i, c in enumerate(extras_pattern):
                wenn nicht stop_index:
                    breche
                wenn c != 'O':
                    stop_index -= 1
                    extras[i] = Nichts
            extras = [s fuer s in extras wenn s is nicht Nichts]

        # make sure all required actions were present und also convert
        # action defaults which were nicht given als arguments
        required_actions = []
        fuer action in self._actions:
            wenn action nicht in seen_actions:
                wenn action.required:
                    required_actions.append(_get_action_name(action))
                sonst:
                    # Convert action default now instead of doing it before
                    # parsing arguments to avoid calling convert functions
                    # twice (which may fail) wenn the argument was given, but
                    # only wenn it was defined already in the namespace
                    wenn (action.default is nicht Nichts und
                        isinstance(action.default, str) und
                        hasattr(namespace, action.dest) und
                        action.default is getattr(namespace, action.dest)):
                        setattr(namespace, action.dest,
                                self._get_value(action, action.default))

        wenn required_actions:
            raise ArgumentError(Nichts, _('the following arguments are required: %s') %
                       ', '.join(required_actions))

        # make sure all required groups had one option present
        fuer group in self._mutually_exclusive_groups:
            wenn group.required:
                fuer action in group._group_actions:
                    wenn action in seen_non_default_actions:
                        breche

                # wenn no actions were used, report the error
                sonst:
                    names = [_get_action_name(action)
                             fuer action in group._group_actions
                             wenn action.help is nicht SUPPRESS]
                    msg = _('one of the arguments %s is required')
                    raise ArgumentError(Nichts, msg % ' '.join(names))

        # return the updated namespace und the extra arguments
        return namespace, extras

    def _read_args_from_files(self, arg_strings):
        # expand arguments referencing files
        new_arg_strings = []
        fuer arg_string in arg_strings:

            # fuer regular arguments, just add them back into the list
            wenn nicht arg_string oder arg_string[0] nicht in self.fromfile_prefix_chars:
                new_arg_strings.append(arg_string)

            # replace arguments referencing files mit the file content
            sonst:
                try:
                    mit open(arg_string[1:],
                              encoding=_sys.getfilesystemencoding(),
                              errors=_sys.getfilesystemencodeerrors()) als args_file:
                        arg_strings = []
                        fuer arg_line in args_file.read().splitlines():
                            fuer arg in self.convert_arg_line_to_args(arg_line):
                                arg_strings.append(arg)
                        arg_strings = self._read_args_from_files(arg_strings)
                        new_arg_strings.extend(arg_strings)
                except OSError als err:
                    raise ArgumentError(Nichts, str(err))

        # return the modified argument list
        return new_arg_strings

    def convert_arg_line_to_args(self, arg_line):
        return [arg_line]

    def _match_argument(self, action, arg_strings_pattern):
        # match the pattern fuer this action to the arg strings
        nargs_pattern = self._get_nargs_pattern(action)
        match = _re.match(nargs_pattern, arg_strings_pattern)

        # raise an exception wenn we weren't able to find a match
        wenn match is Nichts:
            nargs_errors = {
                Nichts: _('expected one argument'),
                OPTIONAL: _('expected at most one argument'),
                ONE_OR_MORE: _('expected at least one argument'),
            }
            msg = nargs_errors.get(action.nargs)
            wenn msg is Nichts:
                msg = ngettext('expected %s argument',
                               'expected %s arguments',
                               action.nargs) % action.nargs
            raise ArgumentError(action, msg)

        # return the number of arguments matched
        return len(match.group(1))

    def _match_arguments_partial(self, actions, arg_strings_pattern):
        # progressively shorten the actions list by slicing off the
        # final actions until we find a match
        fuer i in range(len(actions), 0, -1):
            actions_slice = actions[:i]
            pattern = ''.join([self._get_nargs_pattern(action)
                               fuer action in actions_slice])
            match = _re.match(pattern, arg_strings_pattern)
            wenn match is nicht Nichts:
                result = [len(string) fuer string in match.groups()]
                wenn (match.end() < len(arg_strings_pattern)
                    und arg_strings_pattern[match.end()] == 'O'):
                    waehrend result und nicht result[-1]:
                        del result[-1]
                return result
        return []

    def _parse_optional(self, arg_string):
        # wenn it's an empty string, it was meant to be a positional
        wenn nicht arg_string:
            return Nichts

        # wenn it doesn't start mit a prefix, it was meant to be positional
        wenn nicht arg_string[0] in self.prefix_chars:
            return Nichts

        # wenn the option string is present in the parser, return the action
        wenn arg_string in self._option_string_actions:
            action = self._option_string_actions[arg_string]
            return [(action, arg_string, Nichts, Nichts)]

        # wenn it's just a single character, it was meant to be positional
        wenn len(arg_string) == 1:
            return Nichts

        # wenn the option string before the "=" is present, return the action
        option_string, sep, explicit_arg = arg_string.partition('=')
        wenn sep und option_string in self._option_string_actions:
            action = self._option_string_actions[option_string]
            return [(action, option_string, sep, explicit_arg)]

        # search through all possible prefixes of the option string
        # und all actions in the parser fuer possible interpretations
        option_tuples = self._get_option_tuples(arg_string)

        wenn option_tuples:
            return option_tuples

        # wenn it was nicht found als an option, but it looks like a negative
        # number, it was meant to be positional
        # unless there are negative-number-like options
        wenn self._negative_number_matcher.match(arg_string):
            wenn nicht self._has_negative_number_optionals:
                return Nichts

        # wenn it contains a space, it was meant to be a positional
        wenn ' ' in arg_string:
            return Nichts

        # it was meant to be an optional but there is no such option
        # in this parser (though it might be a valid option in a subparser)
        return [(Nichts, arg_string, Nichts, Nichts)]

    def _get_option_tuples(self, option_string):
        result = []

        # option strings starting mit two prefix characters are only
        # split at the '='
        chars = self.prefix_chars
        wenn option_string[0] in chars und option_string[1] in chars:
            wenn self.allow_abbrev:
                option_prefix, sep, explicit_arg = option_string.partition('=')
                wenn nicht sep:
                    sep = explicit_arg = Nichts
                fuer option_string in self._option_string_actions:
                    wenn option_string.startswith(option_prefix):
                        action = self._option_string_actions[option_string]
                        tup = action, option_string, sep, explicit_arg
                        result.append(tup)

        # single character options can be concatenated mit their arguments
        # but multiple character options always have to have their argument
        # separate
        sowenn option_string[0] in chars und option_string[1] nicht in chars:
            option_prefix, sep, explicit_arg = option_string.partition('=')
            wenn nicht sep:
                sep = explicit_arg = Nichts
            short_option_prefix = option_string[:2]
            short_explicit_arg = option_string[2:]

            fuer option_string in self._option_string_actions:
                wenn option_string == short_option_prefix:
                    action = self._option_string_actions[option_string]
                    tup = action, option_string, '', short_explicit_arg
                    result.append(tup)
                sowenn self.allow_abbrev und option_string.startswith(option_prefix):
                    action = self._option_string_actions[option_string]
                    tup = action, option_string, sep, explicit_arg
                    result.append(tup)

        # shouldn't ever get here
        sonst:
            raise ArgumentError(Nichts, _('unexpected option string: %s') % option_string)

        # return the collected option tuples
        return result

    def _get_nargs_pattern(self, action):
        # in all examples below, we have to allow fuer '--' args
        # which are represented als '-' in the pattern
        nargs = action.nargs
        # wenn this is an optional action, -- is nicht allowed
        option = action.option_strings

        # the default (Nichts) is assumed to be a single argument
        wenn nargs is Nichts:
            nargs_pattern = '([A])' wenn option sonst '(-*A-*)'

        # allow zero oder one arguments
        sowenn nargs == OPTIONAL:
            nargs_pattern = '(A?)' wenn option sonst '(-*A?-*)'

        # allow zero oder more arguments
        sowenn nargs == ZERO_OR_MORE:
            nargs_pattern = '(A*)' wenn option sonst '(-*[A-]*)'

        # allow one oder more arguments
        sowenn nargs == ONE_OR_MORE:
            nargs_pattern = '(A+)' wenn option sonst '(-*A[A-]*)'

        # allow any number of options oder arguments
        sowenn nargs == REMAINDER:
            nargs_pattern = '([AO]*)' wenn option sonst '(.*)'

        # allow one argument followed by any number of options oder arguments
        sowenn nargs == PARSER:
            nargs_pattern = '(A[AO]*)' wenn option sonst '(-*A[-AO]*)'

        # suppress action, like nargs=0
        sowenn nargs == SUPPRESS:
            nargs_pattern = '()' wenn option sonst '(-*)'

        # all others should be integers
        sonst:
            nargs_pattern = '([AO]{%d})' % nargs wenn option sonst '((?:-*A){%d}-*)' % nargs

        # return the pattern
        return nargs_pattern

    # ========================
    # Alt command line argument parsing, allowing free intermix
    # ========================

    def parse_intermixed_args(self, args=Nichts, namespace=Nichts):
        args, argv = self.parse_known_intermixed_args(args, namespace)
        wenn argv:
            msg = _('unrecognized arguments: %s') % ' '.join(argv)
            wenn self.exit_on_error:
                self.error(msg)
            sonst:
                raise ArgumentError(Nichts, msg)
        return args

    def parse_known_intermixed_args(self, args=Nichts, namespace=Nichts):
        # returns a namespace und list of extras
        #
        # positional can be freely intermixed mit optionals.  optionals are
        # first parsed mit all positional arguments deactivated.  The 'extras'
        # are then parsed.  If the parser definition is incompatible mit the
        # intermixed assumptions (e.g. use of REMAINDER, subparsers) a
        # TypeError is raised.

        positionals = self._get_positional_actions()
        a = [action fuer action in positionals
             wenn action.nargs in [PARSER, REMAINDER]]
        wenn a:
            raise TypeError('parse_intermixed_args: positional arg'
                            ' mit nargs=%s'%a[0].nargs)

        return self._parse_known_args2(args, namespace, intermixed=Wahr)

    # ========================
    # Value conversion methods
    # ========================

    def _get_values(self, action, arg_strings):
        # optional argument produces a default when nicht present
        wenn nicht arg_strings und action.nargs == OPTIONAL:
            wenn action.option_strings:
                value = action.const
            sonst:
                value = action.default
            wenn isinstance(value, str) und value is nicht SUPPRESS:
                value = self._get_value(action, value)

        # when nargs='*' on a positional, wenn there were no command-line
        # args, use the default wenn it is anything other than Nichts
        sowenn (nicht arg_strings und action.nargs == ZERO_OR_MORE und
              nicht action.option_strings):
            wenn action.default is nicht Nichts:
                value = action.default
            sonst:
                value = []

        # single argument oder optional argument produces a single value
        sowenn len(arg_strings) == 1 und action.nargs in [Nichts, OPTIONAL]:
            arg_string, = arg_strings
            value = self._get_value(action, arg_string)
            self._check_value(action, value)

        # REMAINDER arguments convert all values, checking none
        sowenn action.nargs == REMAINDER:
            value = [self._get_value(action, v) fuer v in arg_strings]

        # PARSER arguments convert all values, but check only the first
        sowenn action.nargs == PARSER:
            value = [self._get_value(action, v) fuer v in arg_strings]
            self._check_value(action, value[0])

        # SUPPRESS argument does nicht put anything in the namespace
        sowenn action.nargs == SUPPRESS:
            value = SUPPRESS

        # all other types of nargs produce a list
        sonst:
            value = [self._get_value(action, v) fuer v in arg_strings]
            fuer v in value:
                self._check_value(action, v)

        # return the converted value
        return value

    def _get_value(self, action, arg_string):
        type_func = self._registry_get('type', action.type, action.type)
        wenn nicht callable(type_func):
            raise TypeError(f'{type_func!r} is nicht callable')

        # convert the value to the appropriate type
        try:
            result = type_func(arg_string)

        # ArgumentTypeErrors indicate errors
        except ArgumentTypeError als err:
            msg = str(err)
            raise ArgumentError(action, msg)

        # TypeErrors oder ValueErrors also indicate errors
        except (TypeError, ValueError):
            name = getattr(action.type, '__name__', repr(action.type))
            args = {'type': name, 'value': arg_string}
            msg = _('invalid %(type)s value: %(value)r')
            raise ArgumentError(action, msg % args)

        # return the converted value
        return result

    def _check_value(self, action, value):
        # converted value must be one of the choices (if specified)
        choices = action.choices
        wenn choices is Nichts:
            return

        wenn isinstance(choices, str):
            choices = iter(choices)

        wenn value nicht in choices:
            args = {'value': str(value),
                    'choices': ', '.join(map(str, action.choices))}
            msg = _('invalid choice: %(value)r (choose von %(choices)s)')

            wenn self.suggest_on_error und isinstance(value, str):
                wenn all(isinstance(choice, str) fuer choice in action.choices):
                    importiere difflib
                    suggestions = difflib.get_close_matches(value, action.choices, 1)
                    wenn suggestions:
                        args['closest'] = suggestions[0]
                        msg = _('invalid choice: %(value)r, maybe you meant %(closest)r? '
                                '(choose von %(choices)s)')

            raise ArgumentError(action, msg % args)

    # =======================
    # Help-formatting methods
    # =======================

    def format_usage(self):
        formatter = self._get_formatter()
        formatter.add_usage(self.usage, self._actions,
                            self._mutually_exclusive_groups)
        return formatter.format_help()

    def format_help(self):
        formatter = self._get_formatter()

        # usage
        formatter.add_usage(self.usage, self._actions,
                            self._mutually_exclusive_groups)

        # description
        formatter.add_text(self.description)

        # positionals, optionals und user-defined groups
        fuer action_group in self._action_groups:
            formatter.start_section(action_group.title)
            formatter.add_text(action_group.description)
            formatter.add_arguments(action_group._group_actions)
            formatter.end_section()

        # epilog
        formatter.add_text(self.epilog)

        # determine help von format above
        return formatter.format_help()

    def _get_formatter(self):
        formatter = self.formatter_class(prog=self.prog)
        formatter._set_color(self.color)
        return formatter

    # =====================
    # Help-printing methods
    # =====================

    def print_usage(self, file=Nichts):
        wenn file is Nichts:
            file = _sys.stdout
        self._print_message(self.format_usage(), file)

    def print_help(self, file=Nichts):
        wenn file is Nichts:
            file = _sys.stdout
        self._print_message(self.format_help(), file)

    def _print_message(self, message, file=Nichts):
        wenn message:
            file = file oder _sys.stderr
            try:
                file.write(message)
            except (AttributeError, OSError):
                pass

    # ===============
    # Exiting methods
    # ===============

    def exit(self, status=0, message=Nichts):
        wenn message:
            self._print_message(message, _sys.stderr)
        _sys.exit(status)

    def error(self, message):
        """error(message: string)

        Prints a usage message incorporating the message to stderr und
        exits.

        If you override this in a subclass, it should nicht return -- it
        should either exit oder raise an exception.
        """
        self.print_usage(_sys.stderr)
        args = {'prog': self.prog, 'message': message}
        self.exit(2, _('%(prog)s: error: %(message)s\n') % args)

    def _warning(self, message):
        args = {'prog': self.prog, 'message': message}
        self._print_message(_('%(prog)s: warning: %(message)s\n') % args, _sys.stderr)
