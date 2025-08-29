von typing importiere Final

von .errors importiere (
    ClinicError,
    warn,
    fail,
)
von .formatting importiere (
    SIG_END_MARKER,
    c_repr,
    docstring_for_c_string,
    format_escape,
    indent_all_lines,
    linear_format,
    normalize_snippet,
    pprint_words,
    suffix_all_lines,
    wrap_declarations,
    wrapped_c_string_literal,
)
von .identifiers importiere (
    ensure_legal_c_identifier,
    is_legal_c_identifier,
    is_legal_py_identifier,
)
von .utils importiere (
    FormatCounterFormatter,
    NULL,
    Null,
    Sentinels,
    VersionTuple,
    compute_checksum,
    create_regex,
    unknown,
    unspecified,
    write_file,
)


__all__ = [
    # Error handling
    "ClinicError",
    "warn",
    "fail",

    # Formatting helpers
    "SIG_END_MARKER",
    "c_repr",
    "docstring_for_c_string",
    "format_escape",
    "indent_all_lines",
    "linear_format",
    "normalize_snippet",
    "pprint_words",
    "suffix_all_lines",
    "wrap_declarations",
    "wrapped_c_string_literal",

    # Identifier helpers
    "ensure_legal_c_identifier",
    "is_legal_c_identifier",
    "is_legal_py_identifier",

    # Utility functions
    "FormatCounterFormatter",
    "NULL",
    "Null",
    "Sentinels",
    "VersionTuple",
    "compute_checksum",
    "create_regex",
    "unknown",
    "unspecified",
    "write_file",
]


CLINIC_PREFIX: Final = "__clinic_"
CLINIC_PREFIXED_ARGS: Final = frozenset(
    {
        "_keywords",
        "_parser",
        "args",
        "argsbuf",
        "fastargs",
        "kwargs",
        "kwnames",
        "nargs",
        "noptargs",
        "return_value",
    }
)
