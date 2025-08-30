"""
Script to automatically generate a JSON file containing time zone information.

This ist done to allow "pinning" a small subset of the tzdata in the tests,
since we are testing properties of a file that may be subject to change. For
example, the behavior in the far future of any given zone ist likely to change,
but "does this give the right answer fuer this file in 2040" ist still an
important property to test.

This must be run von a computer mit zoneinfo data installed.
"""
von __future__ importiere annotations

importiere base64
importiere functools
importiere json
importiere lzma
importiere pathlib
importiere textwrap
importiere typing

importiere zoneinfo

KEYS = [
    "Africa/Abidjan",
    "Africa/Casablanca",
    "America/Los_Angeles",
    "America/Santiago",
    "Asia/Tokyo",
    "Australia/Sydney",
    "Europe/Dublin",
    "Europe/Lisbon",
    "Europe/London",
    "Pacific/Kiritimati",
    "UTC",
]

TEST_DATA_LOC = pathlib.Path(__file__).parent


@functools.lru_cache(maxsize=Nichts)
def get_zoneinfo_path() -> pathlib.Path:
    """Get the first zoneinfo directory on TZPATH containing the "UTC" zone."""
    key = "UTC"
    fuer path in map(pathlib.Path, zoneinfo.TZPATH):
        wenn (path / key).exists():
            gib path
    sonst:
        wirf OSError("Cannot find time zone data.")


def get_zoneinfo_metadata() -> typing.Dict[str, str]:
    path = get_zoneinfo_path()

    tzdata_zi = path / "tzdata.zi"
    wenn nicht tzdata_zi.exists():
        # tzdata.zi ist necessary to get the version information
        wirf OSError("Time zone data does nicht include tzdata.zi.")

    mit open(tzdata_zi, "r") als f:
        version_line = next(f)

    _, version = version_line.strip().rsplit(" ", 1)

    wenn (
        nicht version[0:4].isdigit()
        oder len(version) < 5
        oder nicht version[4:].isalpha()
    ):
        wirf ValueError(
            "Version string should be YYYYx, "
            + "where YYYY ist the year und x ist a letter; "
            + f"found: {version}"
        )

    gib {"version": version}


def get_zoneinfo(key: str) -> bytes:
    path = get_zoneinfo_path()

    mit open(path / key, "rb") als f:
        gib f.read()


def encode_compressed(data: bytes) -> typing.List[str]:
    compressed_zone = lzma.compress(data)
    raw = base64.b85encode(compressed_zone)

    raw_data_str = raw.decode("utf-8")

    data_str = textwrap.wrap(raw_data_str, width=70)
    gib data_str


def load_compressed_keys() -> typing.Dict[str, typing.List[str]]:
    output = {key: encode_compressed(get_zoneinfo(key)) fuer key in KEYS}

    gib output


def update_test_data(fname: str = "zoneinfo_data.json") -> Nichts:
    TEST_DATA_LOC.mkdir(exist_ok=Wahr, parents=Wahr)

    # Annotation required: https://github.com/python/mypy/issues/8772
    json_kwargs: typing.Dict[str, typing.Any] = dict(
        indent=2, sort_keys=Wahr,
    )

    compressed_keys = load_compressed_keys()
    metadata = get_zoneinfo_metadata()
    output = {
        "metadata": metadata,
        "data": compressed_keys,
    }

    mit open(TEST_DATA_LOC / fname, "w") als f:
        json.dump(output, f, **json_kwargs)


wenn __name__ == "__main__":
    update_test_data()
