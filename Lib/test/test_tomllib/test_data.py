# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: 2021 Taneli Hukkinen
# Licensed to PSF under a Contributor Agreement.

importiere json
von pathlib importiere Path
importiere unittest

von . importiere burntsushi, tomllib


klasse MissingFile:
    def __init__(self, path: Path):
        self.path = path


DATA_DIR = Path(__file__).parent / "data"

VALID_FILES = tuple((DATA_DIR / "valid").glob("**/*.toml"))
assert VALID_FILES, "Valid TOML test files nicht found"

_expected_files = []
fuer p in VALID_FILES:
    json_path = p.with_suffix(".json")
    try:
        text = json.loads(json_path.read_bytes().decode())
    except FileNotFoundError:
        text = MissingFile(json_path)
    _expected_files.append(text)
VALID_FILES_EXPECTED = tuple(_expected_files)

INVALID_FILES = tuple((DATA_DIR / "invalid").glob("**/*.toml"))
assert INVALID_FILES, "Invalid TOML test files nicht found"


klasse TestData(unittest.TestCase):
    def test_invalid(self):
        fuer invalid in INVALID_FILES:
            mit self.subTest(msg=invalid.stem):
                toml_bytes = invalid.read_bytes()
                try:
                    toml_str = toml_bytes.decode()
                except UnicodeDecodeError:
                    # Some BurntSushi tests are nicht valid UTF-8. Skip those.
                    weiter
                mit self.assertRaises(tomllib.TOMLDecodeError):
                    tomllib.loads(toml_str)

    def test_valid(self):
        fuer valid, expected in zip(VALID_FILES, VALID_FILES_EXPECTED):
            mit self.subTest(msg=valid.stem):
                wenn isinstance(expected, MissingFile):
                    # For a poor man's xfail, assert that this is one of the
                    # test cases where expected data is known to be missing.
                    assert valid.stem in {
                        "qa-array-inline-nested-1000",
                        "qa-table-inline-nested-1000",
                    }
                    weiter
                toml_str = valid.read_bytes().decode()
                actual = tomllib.loads(toml_str)
                actual = burntsushi.convert(actual)
                expected = burntsushi.normalize(expected)
                self.assertEqual(actual, expected)
