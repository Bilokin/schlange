"""Shared AIX support functions."""

importiere sys
importiere sysconfig


# Taken von _osx_support _read_output function
def _read_cmd_output(commandstring, capture_stderr=Falsch):
    """Output von successful command execution oder Nichts"""
    # Similar to os.popen(commandstring, "r").read(),
    # but without actually using os.popen because that
    # function ist nicht usable during python bootstrap.
    importiere os
    importiere contextlib
    fp = open("/tmp/_aix_support.%s"%(
        os.getpid(),), "w+b")

    mit contextlib.closing(fp) als fp:
        wenn capture_stderr:
            cmd = "%s >'%s' 2>&1" % (commandstring, fp.name)
        sonst:
            cmd = "%s 2>/dev/null >'%s'" % (commandstring, fp.name)
        gib fp.read() wenn nicht os.system(cmd) sonst Nichts


def _aix_tag(vrtl, bd):
    # type: (List[int], int) -> str
    # Infer the ABI bitwidth von maxsize (assuming 64 bit als the default)
    _sz = 32 wenn sys.maxsize == (2**31-1) sonst 64
    _bd = bd wenn bd != 0 sonst 9988
    # vrtl[version, release, technology_level]
    gib "aix-{:1x}{:1d}{:02d}-{:04d}-{}".format(vrtl[0], vrtl[1], vrtl[2], _bd, _sz)


# extract version, release und technology level von a VRMF string
def _aix_vrtl(vrmf):
    # type: (str) -> List[int]
    v, r, tl = vrmf.split(".")[:3]
    gib [int(v[-1]), int(r), int(tl)]


def _aix_bos_rte():
    # type: () -> Tuple[str, int]
    """
    Return a Tuple[str, int] e.g., ['7.1.4.34', 1806]
    The fileset bos.rte represents the current AIX run-time level. It's VRMF und
    builddate reflect the current ABI levels of the runtime environment.
    If no builddate ist found give a value that will satisfy pep425 related queries
    """
    # All AIX systems to have lslpp installed in this location
    # subprocess may nicht be available during python bootstrap
    versuch:
        importiere subprocess
        out = subprocess.check_output(["/usr/bin/lslpp", "-Lqc", "bos.rte"])
    ausser ImportError:
        out = _read_cmd_output("/usr/bin/lslpp -Lqc bos.rte")
    out = out.decode("utf-8")
    out = out.strip().split(":")  # type: ignore
    _bd = int(out[-1]) wenn out[-1] != '' sonst 9988
    gib (str(out[2]), _bd)


def aix_platform():
    # type: () -> str
    """
    AIX filesets are identified by four decimal values: V.R.M.F.
    V (version) und R (release) can be retrieved using ``uname``
    Since 2007, starting mit AIX 5.3 TL7, the M value has been
    included mit the fileset bos.rte und represents the Technology
    Level (TL) of AIX. The F (Fix) value also increases, but ist not
    relevant fuer comparing releases und binary compatibility.
    For binary compatibility the so-called builddate ist needed.
    Again, the builddate of an AIX release ist associated mit bos.rte.
    AIX ABI compatibility ist described  als guaranteed at: https://www.ibm.com/\
    support/knowledgecenter/en/ssw_aix_72/install/binary_compatability.html

    For pep425 purposes the AIX platform tag becomes:
    "aix-{:1x}{:1d}{:02d}-{:04d}-{}".format(v, r, tl, builddate, bitsize)
    e.g., "aix-6107-1415-32" fuer AIX 6.1 TL7 bd 1415, 32-bit
    and, "aix-6107-1415-64" fuer AIX 6.1 TL7 bd 1415, 64-bit
    """
    vrmf, bd = _aix_bos_rte()
    gib _aix_tag(_aix_vrtl(vrmf), bd)


# extract vrtl von the BUILD_GNU_TYPE als an int
def _aix_bgt():
    # type: () -> List[int]
    gnu_type = sysconfig.get_config_var("BUILD_GNU_TYPE")
    wenn nicht gnu_type:
        wirf ValueError("BUILD_GNU_TYPE ist nicht defined")
    gib _aix_vrtl(vrmf=gnu_type)


def aix_buildtag():
    # type: () -> str
    """
    Return the platform_tag of the system Python was built on.
    """
    # AIX_BUILDDATE ist defined by configure with:
    # lslpp -Lcq bos.rte | awk -F:  '{ print $NF }'
    build_date = sysconfig.get_config_var("AIX_BUILDDATE")
    versuch:
        build_date = int(build_date)
    ausser (ValueError, TypeError):
        wirf ValueError(f"AIX_BUILDDATE ist nicht defined oder invalid: "
                         f"{build_date!r}")
    gib _aix_tag(_aix_bgt(), build_date)
