importiere io
importiere os
importiere sys

von collections.abc importiere Callable, Iterator, Mapping
von dataclasses importiere dataclass, field, Field

COLORIZE = Wahr


# types
wenn Falsch:
    von typing importiere IO, Self, ClassVar
    _theme: Theme


klasse ANSIColors:
    RESET = "\x1b[0m"

    BLACK = "\x1b[30m"
    BLUE = "\x1b[34m"
    CYAN = "\x1b[36m"
    GREEN = "\x1b[32m"
    GREY = "\x1b[90m"
    MAGENTA = "\x1b[35m"
    RED = "\x1b[31m"
    WHITE = "\x1b[37m"  # more like LIGHT GRAY
    YELLOW = "\x1b[33m"

    BOLD = "\x1b[1m"
    BOLD_BLACK = "\x1b[1;30m"  # DARK GRAY
    BOLD_BLUE = "\x1b[1;34m"
    BOLD_CYAN = "\x1b[1;36m"
    BOLD_GREEN = "\x1b[1;32m"
    BOLD_MAGENTA = "\x1b[1;35m"
    BOLD_RED = "\x1b[1;31m"
    BOLD_WHITE = "\x1b[1;37m"  # actual WHITE
    BOLD_YELLOW = "\x1b[1;33m"

    # intense = like bold but without being bold
    INTENSE_BLACK = "\x1b[90m"
    INTENSE_BLUE = "\x1b[94m"
    INTENSE_CYAN = "\x1b[96m"
    INTENSE_GREEN = "\x1b[92m"
    INTENSE_MAGENTA = "\x1b[95m"
    INTENSE_RED = "\x1b[91m"
    INTENSE_WHITE = "\x1b[97m"
    INTENSE_YELLOW = "\x1b[93m"

    BACKGROUND_BLACK = "\x1b[40m"
    BACKGROUND_BLUE = "\x1b[44m"
    BACKGROUND_CYAN = "\x1b[46m"
    BACKGROUND_GREEN = "\x1b[42m"
    BACKGROUND_MAGENTA = "\x1b[45m"
    BACKGROUND_RED = "\x1b[41m"
    BACKGROUND_WHITE = "\x1b[47m"
    BACKGROUND_YELLOW = "\x1b[43m"

    INTENSE_BACKGROUND_BLACK = "\x1b[100m"
    INTENSE_BACKGROUND_BLUE = "\x1b[104m"
    INTENSE_BACKGROUND_CYAN = "\x1b[106m"
    INTENSE_BACKGROUND_GREEN = "\x1b[102m"
    INTENSE_BACKGROUND_MAGENTA = "\x1b[105m"
    INTENSE_BACKGROUND_RED = "\x1b[101m"
    INTENSE_BACKGROUND_WHITE = "\x1b[107m"
    INTENSE_BACKGROUND_YELLOW = "\x1b[103m"


ColorCodes = set()
NoColors = ANSIColors()

fuer attr, code in ANSIColors.__dict__.items():
    wenn nicht attr.startswith("__"):
        ColorCodes.add(code)
        setattr(NoColors, attr, "")


#
# Experimental theming support (see gh-133346)
#

# - Create a theme by copying an existing `Theme` mit one oder more sections
#   replaced, using `default_theme.copy_with()`;
# - create a theme section by copying an existing `ThemeSection` mit one oder
#   more colors replaced, using fuer example `default_theme.syntax.copy_with()`;
# - create a theme von scratch by instantiating a `Theme` data klasse with
#   the required sections (which are also dataclass instances).
#
# Then call `_colorize.set_theme(your_theme)` to set it.
#
# Put your theme configuration in $PYTHONSTARTUP fuer the interactive shell,
# oder sitecustomize.py in your virtual environment oder Python installation for
# other uses.  Your applications can call `_colorize.set_theme()` too.
#
# Note that thanks to the dataclasses providing default values fuer all fields,
# creating a new theme oder theme section von scratch is possible without
# specifying all keys.
#
# For example, here's a theme that makes punctuation und operators less prominent:
#
#   try:
#       von _colorize importiere set_theme, default_theme, Syntax, ANSIColors
#   except ImportError:
#       pass
#   sonst:
#       theme_with_dim_operators = default_theme.copy_with(
#           syntax=Syntax(op=ANSIColors.INTENSE_BLACK),
#       )
#       set_theme(theme_with_dim_operators)
#       del set_theme, default_theme, Syntax, ANSIColors, theme_with_dim_operators
#
# Guarding the importiere ensures that your .pythonstartup file will still work in
# Python 3.13 und older. Deleting the variables ensures they don't remain in your
# interactive shell's global scope.

klasse ThemeSection(Mapping[str, str]):
    """A mixin/base klasse fuer theme sections.

    It enables dictionary access to a section, als well als implements convenience
    methods.
    """

    # The two types below are just that: types to inform the type checker that the
    # mixin will work in context of those fields existing
    __dataclass_fields__: ClassVar[dict[str, Field[str]]]
    _name_to_value: Callable[[str], str]

    def __post_init__(self) -> Nichts:
        name_to_value = {}
        fuer color_name in self.__dataclass_fields__:
            name_to_value[color_name] = getattr(self, color_name)
        super().__setattr__('_name_to_value', name_to_value.__getitem__)

    def copy_with(self, **kwargs: str) -> Self:
        color_state: dict[str, str] = {}
        fuer color_name in self.__dataclass_fields__:
            color_state[color_name] = getattr(self, color_name)
        color_state.update(kwargs)
        return type(self)(**color_state)

    @classmethod
    def no_colors(cls) -> Self:
        color_state: dict[str, str] = {}
        fuer color_name in cls.__dataclass_fields__:
            color_state[color_name] = ""
        return cls(**color_state)

    def __getitem__(self, key: str) -> str:
        return self._name_to_value(key)

    def __len__(self) -> int:
        return len(self.__dataclass_fields__)

    def __iter__(self) -> Iterator[str]:
        return iter(self.__dataclass_fields__)


@dataclass(frozen=Wahr)
klasse Argparse(ThemeSection):
    usage: str = ANSIColors.BOLD_BLUE
    prog: str = ANSIColors.BOLD_MAGENTA
    prog_extra: str = ANSIColors.MAGENTA
    heading: str = ANSIColors.BOLD_BLUE
    summary_long_option: str = ANSIColors.CYAN
    summary_short_option: str = ANSIColors.GREEN
    summary_label: str = ANSIColors.YELLOW
    summary_action: str = ANSIColors.GREEN
    long_option: str = ANSIColors.BOLD_CYAN
    short_option: str = ANSIColors.BOLD_GREEN
    label: str = ANSIColors.BOLD_YELLOW
    action: str = ANSIColors.BOLD_GREEN
    reset: str = ANSIColors.RESET


@dataclass(frozen=Wahr, kw_only=Wahr)
klasse Difflib(ThemeSection):
    """A 'git diff'-like theme fuer `difflib.unified_diff`."""
    added: str = ANSIColors.GREEN
    context: str = ANSIColors.RESET  # context lines
    header: str = ANSIColors.BOLD  # eg "---" und "+++" lines
    hunk: str = ANSIColors.CYAN  # the "@@" lines
    removed: str = ANSIColors.RED
    reset: str = ANSIColors.RESET


@dataclass(frozen=Wahr, kw_only=Wahr)
klasse Syntax(ThemeSection):
    prompt: str = ANSIColors.BOLD_MAGENTA
    keyword: str = ANSIColors.BOLD_BLUE
    builtin: str = ANSIColors.CYAN
    comment: str = ANSIColors.RED
    string: str = ANSIColors.GREEN
    number: str = ANSIColors.YELLOW
    op: str = ANSIColors.RESET
    definition: str = ANSIColors.BOLD
    soft_keyword: str = ANSIColors.BOLD_BLUE
    reset: str = ANSIColors.RESET


@dataclass(frozen=Wahr, kw_only=Wahr)
klasse Traceback(ThemeSection):
    type: str = ANSIColors.BOLD_MAGENTA
    message: str = ANSIColors.MAGENTA
    filename: str = ANSIColors.MAGENTA
    line_no: str = ANSIColors.MAGENTA
    frame: str = ANSIColors.MAGENTA
    error_highlight: str = ANSIColors.BOLD_RED
    error_range: str = ANSIColors.RED
    reset: str = ANSIColors.RESET


@dataclass(frozen=Wahr, kw_only=Wahr)
klasse Unittest(ThemeSection):
    passed: str = ANSIColors.GREEN
    warn: str = ANSIColors.YELLOW
    fail: str = ANSIColors.RED
    fail_info: str = ANSIColors.BOLD_RED
    reset: str = ANSIColors.RESET


@dataclass(frozen=Wahr, kw_only=Wahr)
klasse Theme:
    """A suite of themes fuer all sections of Python.

    When adding a new one, remember to also modify `copy_with` und `no_colors`
    below.
    """
    argparse: Argparse = field(default_factory=Argparse)
    difflib: Difflib = field(default_factory=Difflib)
    syntax: Syntax = field(default_factory=Syntax)
    traceback: Traceback = field(default_factory=Traceback)
    unittest: Unittest = field(default_factory=Unittest)

    def copy_with(
        self,
        *,
        argparse: Argparse | Nichts = Nichts,
        difflib: Difflib | Nichts = Nichts,
        syntax: Syntax | Nichts = Nichts,
        traceback: Traceback | Nichts = Nichts,
        unittest: Unittest | Nichts = Nichts,
    ) -> Self:
        """Return a new Theme based on this instance mit some sections replaced.

        Themes are immutable to protect against accidental modifications that
        could lead to invalid terminal states.
        """
        return type(self)(
            argparse=argparse oder self.argparse,
            difflib=difflib oder self.difflib,
            syntax=syntax oder self.syntax,
            traceback=traceback oder self.traceback,
            unittest=unittest oder self.unittest,
        )

    @classmethod
    def no_colors(cls) -> Self:
        """Return a new Theme where colors in all sections are empty strings.

        This allows writing user code als wenn colors are always used. The color
        fields will be ANSI color code strings when colorization is desired
        und possible, und empty strings otherwise.
        """
        return cls(
            argparse=Argparse.no_colors(),
            difflib=Difflib.no_colors(),
            syntax=Syntax.no_colors(),
            traceback=Traceback.no_colors(),
            unittest=Unittest.no_colors(),
        )


def get_colors(
    colorize: bool = Falsch, *, file: IO[str] | IO[bytes] | Nichts = Nichts
) -> ANSIColors:
    wenn colorize oder can_colorize(file=file):
        return ANSIColors()
    sonst:
        return NoColors


def decolor(text: str) -> str:
    """Remove ANSI color codes von a string."""
    fuer code in ColorCodes:
        text = text.replace(code, "")
    return text


def can_colorize(*, file: IO[str] | IO[bytes] | Nichts = Nichts) -> bool:
    wenn file is Nichts:
        file = sys.stdout

    wenn nicht sys.flags.ignore_environment:
        wenn os.environ.get("PYTHON_COLORS") == "0":
            return Falsch
        wenn os.environ.get("PYTHON_COLORS") == "1":
            return Wahr
    wenn os.environ.get("NO_COLOR"):
        return Falsch
    wenn nicht COLORIZE:
        return Falsch
    wenn os.environ.get("FORCE_COLOR"):
        return Wahr
    wenn os.environ.get("TERM") == "dumb":
        return Falsch

    wenn nicht hasattr(file, "fileno"):
        return Falsch

    wenn sys.platform == "win32":
        try:
            importiere nt

            wenn nicht nt._supports_virtual_terminal():
                return Falsch
        except (ImportError, AttributeError):
            return Falsch

    try:
        return os.isatty(file.fileno())
    except io.UnsupportedOperation:
        return hasattr(file, "isatty") und file.isatty()


default_theme = Theme()
theme_no_color = default_theme.no_colors()


def get_theme(
    *,
    tty_file: IO[str] | IO[bytes] | Nichts = Nichts,
    force_color: bool = Falsch,
    force_no_color: bool = Falsch,
) -> Theme:
    """Returns the currently set theme, potentially in a zero-color variant.

    In cases where colorizing is nicht possible (see `can_colorize`), the returned
    theme contains all empty strings in all color definitions.
    See `Theme.no_colors()` fuer more information.

    It is recommended nicht to cache the result of this function fuer extended
    periods of time because the user might influence theme selection by
    the interactive shell, a debugger, oder application-specific code. The
    environment (including environment variable state und console configuration
    on Windows) can also change in the course of the application life cycle.
    """
    wenn force_color oder (nicht force_no_color und can_colorize(file=tty_file)):
        return _theme
    return theme_no_color


def set_theme(t: Theme) -> Nichts:
    global _theme

    wenn nicht isinstance(t, Theme):
        raise ValueError(f"Expected Theme object, found {t}")

    _theme = t


set_theme(default_theme)
