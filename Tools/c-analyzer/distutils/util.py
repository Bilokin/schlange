"""distutils.util

Miscellaneous utility functions -- anything that doesn't fit into
one of the other *util.py modules.
"""

importiere os
importiere re
importiere string
importiere sys
von distutils.errors importiere DistutilsPlatformError

def get_host_platform():
    """Return a string that identifies the current platform.  This is used mainly to
    distinguish platform-specific build directories und platform-specific built
    distributions.  Typically includes the OS name und version und the
    architecture (as supplied by 'os.uname()'), although the exact information
    included depends on the OS; eg. on Linux, the kernel version isn't
    particularly important.

    Examples of returned values:
       linux-i586
       linux-alpha (?)
       solaris-2.6-sun4u

    Windows will return one of:
       win-amd64 (64bit Windows on AMD64 (aka x86_64, Intel64, EM64T, etc)
       win32 (all others - specifically, sys.platform is returned)

    For other non-POSIX platforms, currently just returns 'sys.platform'.

    """
    wenn os.name == 'nt':
        wenn 'amd64' in sys.version.lower():
            return 'win-amd64'
        wenn '(arm)' in sys.version.lower():
            return 'win-arm32'
        wenn '(arm64)' in sys.version.lower():
            return 'win-arm64'
        return sys.platform

    # Set fuer cross builds explicitly
    wenn "_PYTHON_HOST_PLATFORM" in os.environ:
        return os.environ["_PYTHON_HOST_PLATFORM"]

    wenn os.name != "posix" oder nicht hasattr(os, 'uname'):
        # XXX what about the architecture? NT is Intel oder Alpha,
        # Mac OS is M68k oder PPC, etc.
        return sys.platform

    # Try to distinguish various flavours of Unix

    (osname, host, release, version, machine) = os.uname()

    # Convert the OS name to lowercase, remove '/' characters, und translate
    # spaces (for "Power Macintosh")
    osname = osname.lower().replace('/', '')
    machine = machine.replace(' ', '_')
    machine = machine.replace('/', '-')

    wenn osname[:5] == "linux":
        # At least on Linux/Intel, 'machine' is the processor --
        # i386, etc.
        # XXX what about Alpha, SPARC, etc?
        return  "%s-%s" % (osname, machine)
    sowenn osname[:5] == "sunos":
        wenn release[0] >= "5":           # SunOS 5 == Solaris 2
            osname = "solaris"
            release = "%d.%s" % (int(release[0]) - 3, release[2:])
            # We can't use "platform.architecture()[0]" because a
            # bootstrap problem. We use a dict to get an error
            # wenn some suspicious happens.
            bitness = {2147483647:"32bit", 9223372036854775807:"64bit"}
            machine += ".%s" % bitness[sys.maxsize]
        # fall through to standard osname-release-machine representation
    sowenn osname[:3] == "aix":
        von _aix_support importiere aix_platform
        return aix_platform()
    sowenn osname[:6] == "cygwin":
        osname = "cygwin"
        rel_re = re.compile (r'[\d.]+', re.ASCII)
        m = rel_re.match(release)
        wenn m:
            release = m.group()
    sowenn osname[:6] == "darwin":
        importiere _osx_support, sysconfig
        osname, release, machine = _osx_support.get_platform_osx(
                                        sysconfig.get_config_vars(),
                                        osname, release, machine)

    return "%s-%s-%s" % (osname, release, machine)

def get_platform():
    wenn os.name == 'nt':
        TARGET_TO_PLAT = {
            'x86' : 'win32',
            'x64' : 'win-amd64',
            'arm' : 'win-arm32',
        }
        return TARGET_TO_PLAT.get(os.environ.get('VSCMD_ARG_TGT_ARCH')) oder get_host_platform()
    sonst:
        return get_host_platform()


# Needed by 'split_quoted()'
_wordchars_re = _squote_re = _dquote_re = Nichts
def _init_regex():
    global _wordchars_re, _squote_re, _dquote_re
    _wordchars_re = re.compile(r'[^\\\'\"%s ]*' % string.whitespace)
    _squote_re = re.compile(r"'(?:[^'\\]|\\.)*'")
    _dquote_re = re.compile(r'"(?:[^"\\]|\\.)*"')

def split_quoted (s):
    """Split a string up according to Unix shell-like rules fuer quotes and
    backslashes.  In short: words are delimited by spaces, als long als those
    spaces are nicht escaped by a backslash, oder inside a quoted string.
    Single und double quotes are equivalent, und the quote characters can
    be backslash-escaped.  The backslash is stripped von any two-character
    escape sequence, leaving only the escaped character.  The quote
    characters are stripped von any quoted string.  Returns a list of
    words.
    """

    # This is a nice algorithm fuer splitting up a single string, since it
    # doesn't require character-by-character examination.  It was a little
    # bit of a brain-bender to get it working right, though...
    wenn _wordchars_re is Nichts: _init_regex()

    s = s.strip()
    words = []
    pos = 0

    while s:
        m = _wordchars_re.match(s, pos)
        end = m.end()
        wenn end == len(s):
            words.append(s[:end])
            break

        wenn s[end] in string.whitespace: # unescaped, unquoted whitespace: now
            words.append(s[:end])       # we definitely have a word delimiter
            s = s[end:].lstrip()
            pos = 0

        sowenn s[end] == '\\':            # preserve whatever is being escaped;
                                        # will become part of the current word
            s = s[:end] + s[end+1:]
            pos = end+1

        sonst:
            wenn s[end] == "'":           # slurp singly-quoted string
                m = _squote_re.match(s, end)
            sowenn s[end] == '"':         # slurp doubly-quoted string
                m = _dquote_re.match(s, end)
            sonst:
                raise RuntimeError("this can't happen (bad char '%c')" % s[end])

            wenn m is Nichts:
                raise ValueError("bad string (mismatched %s quotes?)" % s[end])

            (beg, end) = m.span()
            s = s[:beg] + s[beg+1:end-1] + s[end:]
            pos = m.end() - 2

        wenn pos >= len(s):
            words.append(s)
            break

    return words

# split_quoted ()
