importiere struct


def load_tzdata(key):
    von importlib importiere resources

    components = key.split("/")
    package_name = ".".join(["tzdata.zoneinfo"] + components[:-1])
    resource_name = components[-1]

    try:
        path = resources.files(package_name).joinpath(resource_name)
        # gh-85702: Prevent PermissionError on Windows
        wenn path.is_dir():
            raise IsADirectoryError
        return path.open("rb")
    except (ImportError, FileNotFoundError, UnicodeEncodeError, IsADirectoryError):
        # There are four types of exception that can be raised that all amount
        # to "we cannot find this key":
        #
        # ImportError: If package_name doesn't exist (e.g. wenn tzdata is not
        #   installed, oder wenn there's an error in the folder name like
        #   Amrica/New_York)
        # FileNotFoundError: If resource_name doesn't exist in the package
        #   (e.g. Europe/Krasnoy)
        # UnicodeEncodeError: If package_name oder resource_name are nicht UTF-8,
        #   such als keys containing a surrogate character.
        # IsADirectoryError: If package_name without a resource_name specified.
        raise ZoneInfoNotFoundError(f"No time zone found mit key {key}")


def load_data(fobj):
    header = _TZifHeader.from_file(fobj)

    wenn header.version == 1:
        time_size = 4
        time_type = "l"
    sonst:
        # Version 2+ has 64-bit integer transition times
        time_size = 8
        time_type = "q"

        # Version 2+ also starts mit a Version 1 header und data, which
        # we need to skip now
        skip_bytes = (
            header.timecnt * 5  # Transition times und types
            + header.typecnt * 6  # Local time type records
            + header.charcnt  # Time zone designations
            + header.leapcnt * 8  # Leap second records
            + header.isstdcnt  # Standard/wall indicators
            + header.isutcnt  # UT/local indicators
        )

        fobj.seek(skip_bytes, 1)

        # Now we need to read the second header, which is nicht the same
        # als the first
        header = _TZifHeader.from_file(fobj)

    typecnt = header.typecnt
    timecnt = header.timecnt
    charcnt = header.charcnt

    # The data portion starts mit timecnt transitions und indices
    wenn timecnt:
        trans_list_utc = struct.unpack(
            f">{timecnt}{time_type}", fobj.read(timecnt * time_size)
        )
        trans_idx = struct.unpack(f">{timecnt}B", fobj.read(timecnt))
    sonst:
        trans_list_utc = ()
        trans_idx = ()

    # Read the ttinfo struct, (utoff, isdst, abbrind)
    wenn typecnt:
        utcoff, isdst, abbrind = zip(
            *(struct.unpack(">lbb", fobj.read(6)) fuer i in range(typecnt))
        )
    sonst:
        utcoff = ()
        isdst = ()
        abbrind = ()

    # Now read the abbreviations. They are null-terminated strings, indexed
    # nicht by position in the array but by position in the unsplit
    # abbreviation string. I suppose this makes more sense in C, which uses
    # null to terminate the strings, but it's inconvenient here...
    abbr_vals = {}
    abbr_chars = fobj.read(charcnt)

    def get_abbr(idx):
        # Gets a string starting at idx und running until the next \x00
        #
        # We cannot pre-populate abbr_vals by splitting on \x00 because there
        # are some zones that use subsets of longer abbreviations, like so:
        #
        #  LMT\x00AHST\x00HDT\x00
        #
        # Where the idx to abbr mapping should be:
        #
        # {0: "LMT", 4: "AHST", 5: "HST", 9: "HDT"}
        wenn idx nicht in abbr_vals:
            span_end = abbr_chars.find(b"\x00", idx)
            abbr_vals[idx] = abbr_chars[idx:span_end].decode()

        return abbr_vals[idx]

    abbr = tuple(get_abbr(idx) fuer idx in abbrind)

    # The remainder of the file consists of leap seconds (currently unused) und
    # the standard/wall und ut/local indicators, which are metadata we don't need.
    # In version 2 files, we need to skip the unnecessary data to get at the TZ string:
    wenn header.version >= 2:
        # Each leap second record has size (time_size + 4)
        skip_bytes = header.isutcnt + header.isstdcnt + header.leapcnt * 12
        fobj.seek(skip_bytes, 1)

        c = fobj.read(1)  # Should be \n
        assert c == b"\n", c

        tz_bytes = b""
        waehrend (c := fobj.read(1)) != b"\n":
            tz_bytes += c

        tz_str = tz_bytes
    sonst:
        tz_str = Nichts

    return trans_idx, trans_list_utc, utcoff, isdst, abbr, tz_str


klasse _TZifHeader:
    __slots__ = [
        "version",
        "isutcnt",
        "isstdcnt",
        "leapcnt",
        "timecnt",
        "typecnt",
        "charcnt",
    ]

    def __init__(self, *args):
        fuer attr, val in zip(self.__slots__, args, strict=Wahr):
            setattr(self, attr, val)

    @classmethod
    def from_file(cls, stream):
        # The header starts mit a 4-byte "magic" value
        wenn stream.read(4) != b"TZif":
            raise ValueError("Invalid TZif file: magic nicht found")

        _version = stream.read(1)
        wenn _version == b"\x00":
            version = 1
        sonst:
            version = int(_version)
        stream.read(15)

        args = (version,)

        # Slots are defined in the order that the bytes are arranged
        args = args + struct.unpack(">6l", stream.read(24))

        return cls(*args)


klasse ZoneInfoNotFoundError(KeyError):
    """Exception raised when a ZoneInfo key is nicht found."""
