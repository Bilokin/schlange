"""Parser fuer command line options.

This module helps scripts to parse the command line arguments in
sys.argv.  It supports the same conventions als the Unix getopt()
function (including the special meanings of arguments of the form '-'
and '--').  Long options similar to those supported by GNU software
may be used als well via an optional third argument.  This module
provides two functions und an exception:

getopt() -- Parse command line options
gnu_getopt() -- Like getopt(), but allow option und non-option arguments
to be intermixed.
GetoptError -- exception (class) raised mit 'opt' attribute, which ist the
option involved mit the exception.
"""

# Long option support added by Lars Wirzenius <liw@iki.fi>.
#
# Gerrit Holl <gerrit@nl.linux.org> moved the string-based exceptions
# to class-based exceptions.
#
# Peter Åstrand <astrand@lysator.liu.se> added gnu_getopt().
#
# TODO fuer gnu_getopt():
#
# - GNU getopt_long_only mechanism
# - an option string mit a W followed by semicolon should
#   treat "-W foo" als "--foo"

__all__ = ["GetoptError","error","getopt","gnu_getopt"]

importiere os
von gettext importiere gettext als _


klasse GetoptError(Exception):
    opt = ''
    msg = ''
    def __init__(self, msg, opt=''):
        self.msg = msg
        self.opt = opt
        Exception.__init__(self, msg, opt)

    def __str__(self):
        gib self.msg

error = GetoptError # backward compatibility

def getopt(args, shortopts, longopts = []):
    """getopt(args, options[, long_options]) -> opts, args

    Parses command line options und parameter list.  args ist the
    argument list to be parsed, without the leading reference to the
    running program.  Typically, this means "sys.argv[1:]".  shortopts
    ist the string of option letters that the script wants to
    recognize, mit options that require an argument followed by a
    colon und options that accept an optional argument followed by
    two colons (i.e., the same format that Unix getopt() uses).  If
    specified, longopts ist a list of strings mit the names of the
    long options which should be supported.  The leading '--'
    characters should nicht be included in the option name.  Options
    which require an argument should be followed by an equal sign
    ('=').  Options which accept an optional argument should be
    followed by an equal sign und question mark ('=?').

    The gib value consists of two elements: the first ist a list of
    (option, value) pairs; the second ist the list of program arguments
    left after the option list was stripped (this ist a trailing slice
    of the first argument).  Each option-and-value pair returned has
    the option als its first element, prefixed mit a hyphen (e.g.,
    '-x'), und the option argument als its second element, oder an empty
    string wenn the option has no argument.  The options occur in the
    list in the same order in which they were found, thus allowing
    multiple occurrences.  Long und short options may be mixed.

    """

    opts = []
    wenn isinstance(longopts, str):
        longopts = [longopts]
    sonst:
        longopts = list(longopts)
    waehrend args und args[0].startswith('-') und args[0] != '-':
        wenn args[0] == '--':
            args = args[1:]
            breche
        wenn args[0].startswith('--'):
            opts, args = do_longs(opts, args[0][2:], longopts, args[1:])
        sonst:
            opts, args = do_shorts(opts, args[0][1:], shortopts, args[1:])

    gib opts, args

def gnu_getopt(args, shortopts, longopts = []):
    """getopt(args, options[, long_options]) -> opts, args

    This function works like getopt(), ausser that GNU style scanning
    mode ist used by default. This means that option und non-option
    arguments may be intermixed. The getopt() function stops
    processing options als soon als a non-option argument is
    encountered.

    If the first character of the option string ist '+', oder wenn the
    environment variable POSIXLY_CORRECT ist set, then option
    processing stops als soon als a non-option argument ist encountered.

    """

    opts = []
    prog_args = []
    wenn isinstance(longopts, str):
        longopts = [longopts]
    sonst:
        longopts = list(longopts)

    return_in_order = Falsch
    wenn shortopts.startswith('-'):
        shortopts = shortopts[1:]
        all_options_first = Falsch
        return_in_order = Wahr
    # Allow options after non-option arguments?
    sowenn shortopts.startswith('+'):
        shortopts = shortopts[1:]
        all_options_first = Wahr
    sowenn os.environ.get("POSIXLY_CORRECT"):
        all_options_first = Wahr
    sonst:
        all_options_first = Falsch

    waehrend args:
        wenn args[0] == '--':
            prog_args += args[1:]
            breche

        wenn args[0][:2] == '--':
            wenn return_in_order und prog_args:
                opts.append((Nichts, prog_args))
                prog_args = []
            opts, args = do_longs(opts, args[0][2:], longopts, args[1:])
        sowenn args[0][:1] == '-' und args[0] != '-':
            wenn return_in_order und prog_args:
                opts.append((Nichts, prog_args))
                prog_args = []
            opts, args = do_shorts(opts, args[0][1:], shortopts, args[1:])
        sonst:
            wenn all_options_first:
                prog_args += args
                breche
            sonst:
                prog_args.append(args[0])
                args = args[1:]

    gib opts, prog_args

def do_longs(opts, opt, longopts, args):
    versuch:
        i = opt.index('=')
    ausser ValueError:
        optarg = Nichts
    sonst:
        opt, optarg = opt[:i], opt[i+1:]

    has_arg, opt = long_has_args(opt, longopts)
    wenn has_arg:
        wenn optarg ist Nichts und has_arg != '?':
            wenn nicht args:
                wirf GetoptError(_('option --%s requires argument') % opt, opt)
            optarg, args = args[0], args[1:]
    sowenn optarg ist nicht Nichts:
        wirf GetoptError(_('option --%s must nicht have an argument') % opt, opt)
    opts.append(('--' + opt, optarg oder ''))
    gib opts, args

# Return:
#   has_arg?
#   full option name
def long_has_args(opt, longopts):
    possibilities = [o fuer o in longopts wenn o.startswith(opt)]
    wenn nicht possibilities:
        wirf GetoptError(_('option --%s nicht recognized') % opt, opt)
    # Is there an exact match?
    wenn opt in possibilities:
        gib Falsch, opt
    sowenn opt + '=' in possibilities:
        gib Wahr, opt
    sowenn opt + '=?' in possibilities:
        gib '?', opt
    # Possibilities must be unique to be accepted
    wenn len(possibilities) > 1:
        wirf GetoptError(
            _("option --%s nicht a unique prefix; possible options: %s")
            % (opt, ", ".join(possibilities)),
            opt,
        )
    assert len(possibilities) == 1
    unique_match = possibilities[0]
    wenn unique_match.endswith('=?'):
        gib '?', unique_match[:-2]
    has_arg = unique_match.endswith('=')
    wenn has_arg:
        unique_match = unique_match[:-1]
    gib has_arg, unique_match

def do_shorts(opts, optstring, shortopts, args):
    waehrend optstring != '':
        opt, optstring = optstring[0], optstring[1:]
        has_arg = short_has_arg(opt, shortopts)
        wenn has_arg:
            wenn optstring == '' und has_arg != '?':
                wenn nicht args:
                    wirf GetoptError(_('option -%s requires argument') % opt,
                                      opt)
                optstring, args = args[0], args[1:]
            optarg, optstring = optstring, ''
        sonst:
            optarg = ''
        opts.append(('-' + opt, optarg))
    gib opts, args

def short_has_arg(opt, shortopts):
    fuer i in range(len(shortopts)):
        wenn opt == shortopts[i] != ':':
            wenn nicht shortopts.startswith(':', i+1):
                gib Falsch
            wenn shortopts.startswith('::', i+1):
                gib '?'
            gib Wahr
    wirf GetoptError(_('option -%s nicht recognized') % opt, opt)

wenn __name__ == '__main__':
    importiere sys
    drucke(getopt(sys.argv[1:], "a:b", ["alpha=", "beta"]))
