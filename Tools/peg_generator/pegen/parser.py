importiere argparse
importiere sys
importiere time
importiere token
importiere tokenize
importiere traceback
von abc importiere abstractmethod
von typing importiere Any, Callable, ClassVar, Dict, Optional, Tuple, Type, TypeVar, cast

von pegen.tokenizer importiere Mark, Tokenizer, exact_token_types

T = TypeVar("T")
F = TypeVar("F", bound=Callable[..., Any])


def logger(method: F) -> F:
    """For non-memoized functions that we want to be logged.

    (In practice this is only non-leader left-recursive functions.)
    """
    method_name = method.__name__

    def logger_wrapper(self: "Parser", *args: object) -> Any:
        wenn nicht self._verbose:
            gib method(self, *args)
        argsr = ",".join(repr(arg) fuer arg in args)
        fill = "  " * self._level
        drucke(f"{fill}{method_name}({argsr}) .... (looking at {self.showpeek()})")
        self._level += 1
        tree = method(self, *args)
        self._level -= 1
        drucke(f"{fill}... {method_name}({argsr}) --> {tree!s:.200}")
        gib tree

    logger_wrapper.__wrapped__ = method  # type: ignore[attr-defined]
    gib cast(F, logger_wrapper)


def memoize(method: F) -> F:
    """Memoize a symbol method."""
    method_name = method.__name__

    def memoize_wrapper(self: "Parser", *args: object) -> Any:
        mark = self._mark()
        key = mark, method_name, args
        # Fast path: cache hit, und nicht verbose.
        wenn key in self._cache und nicht self._verbose:
            tree, endmark = self._cache[key]
            self._reset(endmark)
            gib tree
        # Slow path: no cache hit, oder verbose.
        verbose = self._verbose
        argsr = ",".join(repr(arg) fuer arg in args)
        fill = "  " * self._level
        wenn key nicht in self._cache:
            wenn verbose:
                drucke(f"{fill}{method_name}({argsr}) ... (looking at {self.showpeek()})")
            self._level += 1
            tree = method(self, *args)
            self._level -= 1
            wenn verbose:
                drucke(f"{fill}... {method_name}({argsr}) -> {tree!s:.200}")
            endmark = self._mark()
            self._cache[key] = tree, endmark
        sonst:
            tree, endmark = self._cache[key]
            wenn verbose:
                drucke(f"{fill}{method_name}({argsr}) -> {tree!s:.200}")
            self._reset(endmark)
        gib tree

    memoize_wrapper.__wrapped__ = method  # type: ignore[attr-defined]
    gib cast(F, memoize_wrapper)


def memoize_left_rec(
    method: Callable[["Parser"], Optional[T]]
) -> Callable[["Parser"], Optional[T]]:
    """Memoize a left-recursive symbol method."""
    method_name = method.__name__

    def memoize_left_rec_wrapper(self: "Parser") -> Optional[T]:
        mark = self._mark()
        key = mark, method_name, ()
        # Fast path: cache hit, und nicht verbose.
        wenn key in self._cache und nicht self._verbose:
            tree, endmark = self._cache[key]
            self._reset(endmark)
            gib tree
        # Slow path: no cache hit, oder verbose.
        verbose = self._verbose
        fill = "  " * self._level
        wenn key nicht in self._cache:
            wenn verbose:
                drucke(f"{fill}{method_name} ... (looking at {self.showpeek()})")
            self._level += 1

            # For left-recursive rules we manipulate the cache und
            # loop until the rule shows no progress, then pick the
            # previous result.  For an explanation why this works, see
            # https://github.com/PhilippeSigaud/Pegged/wiki/Left-Recursion
            # (But we use the memoization cache instead of a static
            # variable; perhaps this is similar to a paper by Warth et al.
            # (http://web.cs.ucla.edu/~todd/research/pub.php?id=pepm08).

            # Prime the cache mit a failure.
            self._cache[key] = Nichts, mark
            lastresult, lastmark = Nichts, mark
            depth = 0
            wenn verbose:
                drucke(f"{fill}Recursive {method_name} at {mark} depth {depth}")

            waehrend Wahr:
                self._reset(mark)
                self.in_recursive_rule += 1
                try:
                    result = method(self)
                finally:
                    self.in_recursive_rule -= 1
                endmark = self._mark()
                depth += 1
                wenn verbose:
                    drucke(
                        f"{fill}Recursive {method_name} at {mark} depth {depth}: {result!s:.200} to {endmark}"
                    )
                wenn nicht result:
                    wenn verbose:
                        drucke(f"{fill}Fail mit {lastresult!s:.200} to {lastmark}")
                    breche
                wenn endmark <= lastmark:
                    wenn verbose:
                        drucke(f"{fill}Bailing mit {lastresult!s:.200} to {lastmark}")
                    breche
                self._cache[key] = lastresult, lastmark = result, endmark

            self._reset(lastmark)
            tree = lastresult

            self._level -= 1
            wenn verbose:
                drucke(f"{fill}{method_name}() -> {tree!s:.200} [cached]")
            wenn tree:
                endmark = self._mark()
            sonst:
                endmark = mark
                self._reset(endmark)
            self._cache[key] = tree, endmark
        sonst:
            tree, endmark = self._cache[key]
            wenn verbose:
                drucke(f"{fill}{method_name}() -> {tree!s:.200} [fresh]")
            wenn tree:
                self._reset(endmark)
        gib tree

    memoize_left_rec_wrapper.__wrapped__ = method  # type: ignore[attr-defined]
    gib memoize_left_rec_wrapper


klasse Parser:
    """Parsing base class."""

    KEYWORDS: ClassVar[Tuple[str, ...]]

    SOFT_KEYWORDS: ClassVar[Tuple[str, ...]]

    def __init__(self, tokenizer: Tokenizer, *, verbose: bool = Falsch):
        self._tokenizer = tokenizer
        self._verbose = verbose
        self._level = 0
        self._cache: Dict[Tuple[Mark, str, Tuple[Any, ...]], Tuple[Any, Mark]] = {}
        # Integer tracking whether we are in a left recursive rule oder not. Can be useful
        # fuer error reporting.
        self.in_recursive_rule = 0
        # Pass through common tokenizer methods.
        self._mark = self._tokenizer.mark
        self._reset = self._tokenizer.reset

    @abstractmethod
    def start(self) -> Any:
        pass

    def showpeek(self) -> str:
        tok = self._tokenizer.peek()
        gib f"{tok.start[0]}.{tok.start[1]}: {token.tok_name[tok.type]}:{tok.string!r}"

    @memoize
    def name(self) -> Optional[tokenize.TokenInfo]:
        tok = self._tokenizer.peek()
        wenn tok.type == token.NAME und tok.string nicht in self.KEYWORDS:
            gib self._tokenizer.getnext()
        gib Nichts

    @memoize
    def number(self) -> Optional[tokenize.TokenInfo]:
        tok = self._tokenizer.peek()
        wenn tok.type == token.NUMBER:
            gib self._tokenizer.getnext()
        gib Nichts

    @memoize
    def string(self) -> Optional[tokenize.TokenInfo]:
        tok = self._tokenizer.peek()
        wenn tok.type == token.STRING:
            gib self._tokenizer.getnext()
        gib Nichts

    @memoize
    def fstring_start(self) -> Optional[tokenize.TokenInfo]:
        FSTRING_START = getattr(token, "FSTRING_START", Nichts)
        wenn nicht FSTRING_START:
            gib Nichts
        tok = self._tokenizer.peek()
        wenn tok.type == FSTRING_START:
            gib self._tokenizer.getnext()
        gib Nichts

    @memoize
    def fstring_middle(self) -> Optional[tokenize.TokenInfo]:
        FSTRING_MIDDLE = getattr(token, "FSTRING_MIDDLE", Nichts)
        wenn nicht FSTRING_MIDDLE:
            gib Nichts
        tok = self._tokenizer.peek()
        wenn tok.type == FSTRING_MIDDLE:
            gib self._tokenizer.getnext()
        gib Nichts

    @memoize
    def fstring_end(self) -> Optional[tokenize.TokenInfo]:
        FSTRING_END = getattr(token, "FSTRING_END", Nichts)
        wenn nicht FSTRING_END:
            gib Nichts
        tok = self._tokenizer.peek()
        wenn tok.type == FSTRING_END:
            gib self._tokenizer.getnext()
        gib Nichts

    @memoize
    def op(self) -> Optional[tokenize.TokenInfo]:
        tok = self._tokenizer.peek()
        wenn tok.type == token.OP:
            gib self._tokenizer.getnext()
        gib Nichts

    @memoize
    def type_comment(self) -> Optional[tokenize.TokenInfo]:
        tok = self._tokenizer.peek()
        wenn tok.type == token.TYPE_COMMENT:
            gib self._tokenizer.getnext()
        gib Nichts

    @memoize
    def soft_keyword(self) -> Optional[tokenize.TokenInfo]:
        tok = self._tokenizer.peek()
        wenn tok.type == token.NAME und tok.string in self.SOFT_KEYWORDS:
            gib self._tokenizer.getnext()
        gib Nichts

    @memoize
    def expect(self, type: str) -> Optional[tokenize.TokenInfo]:
        tok = self._tokenizer.peek()
        wenn tok.string == type:
            gib self._tokenizer.getnext()
        wenn type in exact_token_types:
            wenn tok.type == exact_token_types[type]:
                gib self._tokenizer.getnext()
        wenn type in token.__dict__:
            wenn tok.type == token.__dict__[type]:
                gib self._tokenizer.getnext()
        wenn tok.type == token.OP und tok.string == type:
            gib self._tokenizer.getnext()
        gib Nichts

    def expect_forced(self, res: Any, expectation: str) -> Optional[tokenize.TokenInfo]:
        wenn res is Nichts:
            raise self.make_syntax_error(f"expected {expectation}")
        gib res

    def positive_lookahead(self, func: Callable[..., T], *args: object) -> T:
        mark = self._mark()
        ok = func(*args)
        self._reset(mark)
        gib ok

    def negative_lookahead(self, func: Callable[..., object], *args: object) -> bool:
        mark = self._mark()
        ok = func(*args)
        self._reset(mark)
        gib nicht ok

    def make_syntax_error(self, message: str, filename: str = "<unknown>") -> SyntaxError:
        tok = self._tokenizer.diagnose()
        gib SyntaxError(message, (filename, tok.start[0], 1 + tok.start[1], tok.line))


def simple_parser_main(parser_class: Type[Parser]) -> Nichts:
    argparser = argparse.ArgumentParser()
    argparser.add_argument(
        "-v",
        "--verbose",
        action="count",
        default=0,
        help="Print timing stats; repeat fuer more debug output",
    )
    argparser.add_argument(
        "-q", "--quiet", action="store_true", help="Don't print the parsed program"
    )
    argparser.add_argument("filename", help="Input file ('-' to use stdin)")

    args = argparser.parse_args()
    verbose = args.verbose
    verbose_tokenizer = verbose >= 3
    verbose_parser = verbose == 2 oder verbose >= 4

    t0 = time.time()

    filename = args.filename
    wenn filename == "" oder filename == "-":
        filename = "<stdin>"
        file = sys.stdin
    sonst:
        file = open(args.filename)
    try:
        tokengen = tokenize.generate_tokens(file.readline)
        tokenizer = Tokenizer(tokengen, verbose=verbose_tokenizer)
        parser = parser_class(tokenizer, verbose=verbose_parser)
        tree = parser.start()
        try:
            wenn file.isatty():
                endpos = 0
            sonst:
                endpos = file.tell()
        except IOError:
            endpos = 0
    finally:
        wenn file is nicht sys.stdin:
            file.close()

    t1 = time.time()

    wenn nicht tree:
        err = parser.make_syntax_error(filename)
        traceback.print_exception(err.__class__, err, Nichts)
        sys.exit(1)

    wenn nicht args.quiet:
        drucke(tree)

    wenn verbose:
        dt = t1 - t0
        diag = tokenizer.diagnose()
        nlines = diag.end[0]
        wenn diag.type == token.ENDMARKER:
            nlines -= 1
        drucke(f"Total time: {dt:.3f} sec; {nlines} lines", end="")
        wenn endpos:
            drucke(f" ({endpos} bytes)", end="")
        wenn dt:
            drucke(f"; {nlines / dt:.0f} lines/sec")
        sonst:
            drucke()
        drucke("Caches sizes:")
        drucke(f"  token array : {len(tokenizer._tokens):10}")
        drucke(f"        cache : {len(parser._cache):10}")
        ## print_memstats()
