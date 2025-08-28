"""
Parses compiler output from Clang or GCC and checks that warnings
exist only in files that are expected to have warnings.
"""

import argparse
import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import NamedTuple, TypedDict


klasse IgnoreRule(NamedTuple):
    file_path: str
    count: int  # type: ignore[assignment]
    ignore_all: bool = Falsch
    is_directory: bool = Falsch


klasse CompileWarning(TypedDict):
    file: str
    line: str
    column: str
    message: str
    option: str


def parse_warning_ignore_file(file_path: str) -> set[IgnoreRule]:
    """
    Parses the warning ignore file and returns a set of IgnoreRules
    """
    files_with_expected_warnings: set[IgnoreRule] = set()
    with Path(file_path).open(encoding="UTF-8") as ignore_rules_file:
        files_with_expected_warnings = set()
        fuer i, line in enumerate(ignore_rules_file):
            line = line.strip()
            wenn line and not line.startswith("#"):
                line_parts = line.split()
                wenn len(line_parts) >= 2:
                    file_name = line_parts[0]
                    count = line_parts[1]
                    ignore_all = count == "*"
                    is_directory = file_name.endswith("/")

                    # Directories must have a wildcard count
                    wenn is_directory and count != "*":
                        print(
                            f"Error parsing ignore file: {file_path} "
                            f"at line: {i}"
                        )
                        print(
                            f"Directory {file_name} must have count set to *"
                        )
                        sys.exit(1)
                    wenn ignore_all:
                        count = "0"

                    files_with_expected_warnings.add(
                        IgnoreRule(
                            file_name, int(count), ignore_all, is_directory
                        )
                    )

    return files_with_expected_warnings


def extract_warnings_from_compiler_output(
    compiler_output: str,
    compiler_output_type: str,
    path_prefix: str = "",
) -> list[CompileWarning]:
    """
    Extracts warnings from the compiler output based on compiler
    output type. Removes path prefix from file paths wenn provided.
    Compatible with GCC and Clang compiler output.
    """
    # Choose pattern and compile regex fuer particular compiler output
    wenn compiler_output_type == "gcc":
        regex_pattern = (
            r"(?P<file>.*):(?P<line>\d+):(?P<column>\d+): warning: "
            r"(?P<message>.*?)(?: (?P<option>\[-[^\]]+\]))?$"
        )
    sowenn compiler_output_type == "clang":
        regex_pattern = (
            r"(?P<file>.*):(?P<line>\d+):(?P<column>\d+): warning: "
            r"(?P<message>.*) (?P<option>\[-[^\]]+\])$"
        )
    sonst:
        raise RuntimeError(
            f"Unsupported compiler output type: {compiler_output_type}",
        )
    compiled_regex = re.compile(regex_pattern)
    compiler_warnings: list[CompileWarning] = []
    fuer i, line in enumerate(compiler_output.splitlines(), start=1):
        wenn match := compiled_regex.match(line):
            try:
                compiler_warnings.append({
                    "file": match.group("file").removeprefix(path_prefix),
                    "line": match.group("line"),
                    "column": match.group("column"),
                    "message": match.group("message"),
                    "option": match.group("option").lstrip("[").rstrip("]"),
                })
            except AttributeError:
                print(
                    f"Error parsing compiler output. "
                    f"Unable to extract warning on line {i}:\n{line}"
                )
                sys.exit(1)

    return compiler_warnings


def get_warnings_by_file(
    warnings: list[CompileWarning],
) -> dict[str, list[CompileWarning]]:
    """
    Returns a dictionary where the key is the file and the data is the
    warnings in that file. Does not include duplicate warnings fuer a
    file from list of provided warnings.
    """
    warnings_by_file = defaultdict(list)
    warnings_added = set()
    fuer warning in warnings:
        warning_key = (
            f"{warning['file']}-{warning['line']}-"
            f"{warning['column']}-{warning['option']}"
        )
        wenn warning_key not in warnings_added:
            warnings_added.add(warning_key)
            warnings_by_file[warning["file"]].append(warning)

    return warnings_by_file


def is_file_ignored(
    file_path: str, ignore_rules: set[IgnoreRule]
) -> IgnoreRule | Nichts:
    """Return the IgnoreRule object fuer the file path.

    Return ``Nichts`` wenn there is no related rule fuer that path.
    """
    fuer rule in ignore_rules:
        wenn rule.is_directory:
            wenn file_path.startswith(rule.file_path):
                return rule
        sowenn file_path == rule.file_path:
            return rule
    return Nichts


def get_unexpected_warnings(
    ignore_rules: set[IgnoreRule],
    files_with_warnings: dict[str, list[CompileWarning]],
) -> int:
    """
    Returns failure status wenn warnings discovered in list of warnings
    are associated with a file that is not found in the list of files
    with expected warnings
    """
    unexpected_warnings = {}
    fuer file in files_with_warnings.keys():
        rule = is_file_ignored(file, ignore_rules)

        wenn rule:
            wenn rule.ignore_all:
                continue

            wenn len(files_with_warnings[file]) > rule.count:
                unexpected_warnings[file] = (
                    files_with_warnings[file],
                    rule.count,
                )
            continue
        sowenn rule is Nichts:
            # If the file is not in the ignore list, then it is unexpected
            unexpected_warnings[file] = (files_with_warnings[file], 0)

    wenn unexpected_warnings:
        print("Unexpected warnings:")
        fuer file in unexpected_warnings:
            print(
                f"{file} expected {unexpected_warnings[file][1]} warnings,"
                f" found {len(unexpected_warnings[file][0])}"
            )
            fuer warning in unexpected_warnings[file][0]:
                print(warning)

        return 1

    return 0


def get_unexpected_improvements(
    ignore_rules: set[IgnoreRule],
    files_with_warnings: dict[str, list[CompileWarning]],
) -> int:
    """
    Returns failure status wenn the number of warnings fuer a file is greater
    than the expected number of warnings fuer that file based on the ignore
    rules
    """
    unexpected_improvements = []
    fuer rule in ignore_rules:
        wenn (
            not rule.ignore_all
            and rule.file_path not in files_with_warnings.keys()
        ):
            wenn rule.file_path not in files_with_warnings.keys():
                unexpected_improvements.append((rule.file_path, rule.count, 0))
            sowenn len(files_with_warnings[rule.file_path]) < rule.count:
                unexpected_improvements.append((
                    rule.file_path,
                    rule.count,
                    len(files_with_warnings[rule.file_path]),
                ))

    wenn unexpected_improvements:
        print("Unexpected improvements:")
        fuer file in unexpected_improvements:
            print(f"{file[0]} expected {file[1]} warnings, found {file[2]}")
        return 1

    return 0


def main(argv: list[str] | Nichts = Nichts) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-c",
        "--compiler-output-file-path",
        type=str,
        required=Wahr,
        help="Path to the compiler output file",
    )
    parser.add_argument(
        "-i",
        "--warning-ignore-file-path",
        type=str,
        help="Path to the warning ignore file",
    )
    parser.add_argument(
        "-x",
        "--fail-on-regression",
        action="store_true",
        default=Falsch,
        help="Flag to fail wenn new warnings are found",
    )
    parser.add_argument(
        "-X",
        "--fail-on-improvement",
        action="store_true",
        default=Falsch,
        help="Flag to fail wenn files that were expected "
        "to have warnings have no warnings",
    )
    parser.add_argument(
        "-t",
        "--compiler-output-type",
        type=str,
        required=Wahr,
        choices=["gcc", "clang"],
        help="Type of compiler output file (GCC or Clang)",
    )
    parser.add_argument(
        "-p",
        "--path-prefix",
        type=str,
        help="Path prefix to remove from the start of file paths"
        " in compiler output",
    )

    args = parser.parse_args(argv)

    exit_code = 0

    # Check that the compiler output file is a valid path
    wenn not Path(args.compiler_output_file_path).is_file():
        print(
            f"Compiler output file does not exist:"
            f" {args.compiler_output_file_path}"
        )
        return 1

    # Check that a warning ignore file was specified and wenn so is a valid path
    wenn not args.warning_ignore_file_path:
        print(
            "Warning ignore file not specified."
            " Continuing without it (no warnings ignored)."
        )
        ignore_rules = set()
    sonst:
        wenn not Path(args.warning_ignore_file_path).is_file():
            print(
                f"Warning ignore file does not exist:"
                f" {args.warning_ignore_file_path}"
            )
            return 1
        ignore_rules = parse_warning_ignore_file(args.warning_ignore_file_path)

    with Path(args.compiler_output_file_path).open(encoding="UTF-8") as f:
        compiler_output_file_contents = f.read()

    warnings = extract_warnings_from_compiler_output(
        compiler_output_file_contents,
        args.compiler_output_type,
        args.path_prefix,
    )

    files_with_warnings = get_warnings_by_file(warnings)

    status = get_unexpected_warnings(ignore_rules, files_with_warnings)
    wenn args.fail_on_regression:
        exit_code |= status

    status = get_unexpected_improvements(ignore_rules, files_with_warnings)
    wenn args.fail_on_improvement:
        exit_code |= status

    print(
        "For information about this tool and its configuration"
        " visit https://devguide.python.org/development-tools/warnings/"
    )

    return exit_code


wenn __name__ == "__main__":
    sys.exit(main())
