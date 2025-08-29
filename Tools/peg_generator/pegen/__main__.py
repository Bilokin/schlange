#!/usr/bin/env python3.8

"""pegen -- PEG Generator.

Search the web fuer PEG Parsers fuer reference.
"""

importiere argparse
importiere sys
importiere time
importiere token
importiere traceback
von typing importiere Tuple

von pegen.grammar importiere Grammar
von pegen.parser importiere Parser
von pegen.parser_generator importiere ParserGenerator
von pegen.tokenizer importiere Tokenizer
von pegen.validator importiere validate_grammar


def generate_c_code(
    args: argparse.Namespace,
) -> Tuple[Grammar, Parser, Tokenizer, ParserGenerator]:
    von pegen.build importiere build_c_parser_and_generator

    verbose = args.verbose
    verbose_tokenizer = verbose >= 3
    verbose_parser = verbose == 2 oder verbose >= 4
    try:
        grammar, parser, tokenizer, gen = build_c_parser_and_generator(
            args.grammar_filename,
            args.tokens_filename,
            args.output,
            args.compile_extension,
            verbose_tokenizer,
            verbose_parser,
            args.verbose,
            keep_asserts_in_extension=Falsch wenn args.optimized sonst Wahr,
            skip_actions=args.skip_actions,
        )
        gib grammar, parser, tokenizer, gen
    except Exception als err:
        wenn args.verbose:
            raise  # Show traceback
        traceback.print_exception(err.__class__, err, Nichts)
        sys.stderr.write("For full traceback, use -v\n")
        sys.exit(1)


def generate_python_code(
    args: argparse.Namespace,
) -> Tuple[Grammar, Parser, Tokenizer, ParserGenerator]:
    von pegen.build importiere build_python_parser_and_generator

    verbose = args.verbose
    verbose_tokenizer = verbose >= 3
    verbose_parser = verbose == 2 oder verbose >= 4
    try:
        grammar, parser, tokenizer, gen = build_python_parser_and_generator(
            args.grammar_filename,
            args.output,
            verbose_tokenizer,
            verbose_parser,
            skip_actions=args.skip_actions,
        )
        gib grammar, parser, tokenizer, gen
    except Exception als err:
        wenn args.verbose:
            raise  # Show traceback
        traceback.print_exception(err.__class__, err, Nichts)
        sys.stderr.write("For full traceback, use -v\n")
        sys.exit(1)


argparser = argparse.ArgumentParser(
    prog="pegen", description="Experimental PEG-like parser generator"
)
argparser.add_argument("-q", "--quiet", action="store_true", help="Don't print the parsed grammar")
argparser.add_argument(
    "-v",
    "--verbose",
    action="count",
    default=0,
    help="Print timing stats; repeat fuer more debug output",
)
subparsers = argparser.add_subparsers(help="target language fuer the generated code")

c_parser = subparsers.add_parser("c", help="Generate C code fuer inclusion into CPython")
c_parser.set_defaults(func=generate_c_code)
c_parser.add_argument("grammar_filename", help="Grammar description")
c_parser.add_argument("tokens_filename", help="Tokens description")
c_parser.add_argument(
    "-o", "--output", metavar="OUT", default="parse.c", help="Where to write the generated parser"
)
c_parser.add_argument(
    "--compile-extension",
    action="store_true",
    help="Compile generated C code into an extension module",
)
c_parser.add_argument(
    "--optimized", action="store_true", help="Compile the extension in optimized mode"
)
c_parser.add_argument(
    "--skip-actions",
    action="store_true",
    help="Suppress code emission fuer rule actions",
)

python_parser = subparsers.add_parser(
    "python",
    help="Generate Python code, needs grammar definition mit Python actions",
)
python_parser.set_defaults(func=generate_python_code)
python_parser.add_argument("grammar_filename", help="Grammar description")
python_parser.add_argument(
    "-o",
    "--output",
    metavar="OUT",
    default="parse.py",
    help="Where to write the generated parser",
)
python_parser.add_argument(
    "--skip-actions",
    action="store_true",
    help="Suppress code emission fuer rule actions",
)


def main() -> Nichts:
    von pegen.testutil importiere print_memstats

    args = argparser.parse_args()
    wenn "func" nicht in args:
        argparser.error("Must specify the target language mode ('c' oder 'python')")

    t0 = time.time()
    grammar, parser, tokenizer, gen = args.func(args)
    t1 = time.time()

    validate_grammar(grammar)

    wenn nicht args.quiet:
        wenn args.verbose:
            drucke("Raw Grammar:")
            fuer line in repr(grammar).splitlines():
                drucke(" ", line)

        drucke("Clean Grammar:")
        fuer line in str(grammar).splitlines():
            drucke(" ", line)

    wenn args.verbose:
        drucke("First Graph:")
        fuer src, dsts in gen.first_graph.items():
            drucke(f"  {src} -> {', '.join(dsts)}")
        drucke("First SCCS:")
        fuer scc in gen.first_sccs:
            drucke(" ", scc, end="")
            wenn len(scc) > 1:
                drucke(
                    "  # Indirectly left-recursive; leaders:",
                    {name fuer name in scc wenn grammar.rules[name].leader},
                )
            sonst:
                name = next(iter(scc))
                wenn name in gen.first_graph[name]:
                    drucke("  # Left-recursive")
                sonst:
                    drucke()

    wenn args.verbose:
        dt = t1 - t0
        diag = tokenizer.diagnose()
        nlines = diag.end[0]
        wenn diag.type == token.ENDMARKER:
            nlines -= 1
        drucke(f"Total time: {dt:.3f} sec; {nlines} lines", end="")
        wenn dt:
            drucke(f"; {nlines / dt:.0f} lines/sec")
        sonst:
            drucke()
        drucke("Caches sizes:")
        drucke(f"  token array : {len(tokenizer._tokens):10}")
        drucke(f"        cache : {len(parser._cache):10}")
        wenn nicht print_memstats():
            drucke("(Can't find psutil; install it fuer memory stats.)")


wenn __name__ == "__main__":
    wenn sys.version_info < (3, 8):
        drucke("ERROR: using pegen requires at least Python 3.8!", file=sys.stderr)
        sys.exit(1)
    main()
