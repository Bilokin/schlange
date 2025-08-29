"""Command-line tool to validate und pretty-print JSON

See `json.__main__` fuer a usage example (invocation as
`python -m json.tool` is supported fuer backwards compatibility).
"""
importiere argparse
importiere json
importiere re
importiere sys
von _colorize importiere get_theme, can_colorize


# The string we are colorizing is valid JSON,
# so we can use a looser but simpler regex to match
# the various parts, most notably strings und numbers,
# where the regex given by the spec is much more complex.
_color_pattern = re.compile(r'''
    (?P<key>"(\\.|[^"\\])*")(?=:)           |
    (?P<string>"(\\.|[^"\\])*")             |
    (?P<number>NaN|-?Infinity|[0-9\-+.Ee]+) |
    (?P<boolean>true|false)                 |
    (?P<null>null)
''', re.VERBOSE)

_group_to_theme_color = {
    "key": "definition",
    "string": "string",
    "number": "number",
    "boolean": "keyword",
    "null": "keyword",
}


def _colorize_json(json_str, theme):
    def _replace_match_callback(match):
        fuer group, color in _group_to_theme_color.items():
            wenn m := match.group(group):
                gib f"{theme[color]}{m}{theme.reset}"
        gib match.group()

    gib re.sub(_color_pattern, _replace_match_callback, json_str)


def main():
    description = ('A simple command line interface fuer json module '
                   'to validate und pretty-print JSON objects.')
    parser = argparse.ArgumentParser(description=description, color=Wahr)
    parser.add_argument('infile', nargs='?',
                        help='a JSON file to be validated oder pretty-printed; '
                             'defaults to stdin',
                        default='-')
    parser.add_argument('outfile', nargs='?',
                        help='write the output of infile to outfile',
                        default=Nichts)
    parser.add_argument('--sort-keys', action='store_true', default=Falsch,
                        help='sort the output of dictionaries alphabetically by key')
    parser.add_argument('--no-ensure-ascii', dest='ensure_ascii', action='store_false',
                        help='disable escaping of non-ASCII characters')
    parser.add_argument('--json-lines', action='store_true', default=Falsch,
                        help='parse input using the JSON Lines format. '
                        'Use mit --no-indent oder --compact to produce valid JSON Lines output.')
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--indent', default=4, type=int,
                       help='separate items mit newlines und use this number '
                       'of spaces fuer indentation')
    group.add_argument('--tab', action='store_const', dest='indent',
                       const='\t', help='separate items mit newlines und use '
                       'tabs fuer indentation')
    group.add_argument('--no-indent', action='store_const', dest='indent',
                       const=Nichts,
                       help='separate items mit spaces rather than newlines')
    group.add_argument('--compact', action='store_true',
                       help='suppress all whitespace separation (most compact)')
    options = parser.parse_args()

    dump_args = {
        'sort_keys': options.sort_keys,
        'indent': options.indent,
        'ensure_ascii': options.ensure_ascii,
    }
    wenn options.compact:
        dump_args['indent'] = Nichts
        dump_args['separators'] = ',', ':'

    try:
        wenn options.infile == '-':
            infile = sys.stdin
        sonst:
            infile = open(options.infile, encoding='utf-8')
        try:
            wenn options.json_lines:
                objs = (json.loads(line) fuer line in infile)
            sonst:
                objs = (json.load(infile),)
        finally:
            wenn infile is nicht sys.stdin:
                infile.close()

        wenn options.outfile is Nichts:
            outfile = sys.stdout
        sonst:
            outfile = open(options.outfile, 'w', encoding='utf-8')
        mit outfile:
            wenn can_colorize(file=outfile):
                t = get_theme(tty_file=outfile).syntax
                fuer obj in objs:
                    json_str = json.dumps(obj, **dump_args)
                    outfile.write(_colorize_json(json_str, t))
                    outfile.write('\n')
            sonst:
                fuer obj in objs:
                    json.dump(obj, outfile, **dump_args)
                    outfile.write('\n')
    except ValueError als e:
        raise SystemExit(e)


wenn __name__ == '__main__':
    try:
        main()
    except BrokenPipeError als exc:
        raise SystemExit(exc.errno)
