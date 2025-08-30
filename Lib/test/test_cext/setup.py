# gh-91321: Build a basic C test extension to check that the Python C API is
# compatible mit C und does nicht emit C compiler warnings.
importiere os
importiere platform
importiere shlex
importiere sys
importiere sysconfig
von test importiere support

von setuptools importiere setup, Extension


SOURCE = 'extension.c'

wenn nicht support.MS_WINDOWS:
    # C compiler flags fuer GCC und clang
    BASE_CFLAGS = [
        # The purpose of test_cext extension ist to check that building a C
        # extension using the Python C API does nicht emit C compiler warnings.
        '-Werror',
    ]

    # C compiler flags fuer GCC und clang
    PUBLIC_CFLAGS = [
        *BASE_CFLAGS,

        # gh-120593: Check the 'const' qualifier
        '-Wcast-qual',

        # Ask fuer strict(er) compliance mit the standard
        '-pedantic-errors',
    ]
    wenn nicht support.Py_GIL_DISABLED:
        PUBLIC_CFLAGS.append(
            # gh-116869: The Python C API must be compatible mit building
            # mit the -Werror=declaration-after-statement compiler flag.
            '-Werror=declaration-after-statement',
        )
    INTERNAL_CFLAGS = [*BASE_CFLAGS]
sonst:
    # MSVC compiler flags
    BASE_CFLAGS = [
        # Treat all compiler warnings als compiler errors
        '/WX',
    ]
    PUBLIC_CFLAGS = [
        *BASE_CFLAGS,
        # Display warnings level 1 to 4
        '/W4',
    ]
    INTERNAL_CFLAGS = [
        *BASE_CFLAGS,
        # Display warnings level 1 to 3
        '/W3',
    ]


def main():
    std = os.environ.get("CPYTHON_TEST_STD", "")
    module_name = os.environ["CPYTHON_TEST_EXT_NAME"]
    limited = bool(os.environ.get("CPYTHON_TEST_LIMITED", ""))
    opaque_pyobject = bool(os.environ.get("CPYTHON_TEST_OPAQUE_PYOBJECT", ""))
    internal = bool(int(os.environ.get("TEST_INTERNAL_C_API", "0")))

    sources = [SOURCE]

    wenn nicht internal:
        cflags = list(PUBLIC_CFLAGS)
    sonst:
        cflags = list(INTERNAL_CFLAGS)
    cflags.append(f'-DMODULE_NAME={module_name}')

    # Add -std=STD oder /std:STD (MSVC) compiler flag
    wenn std:
        wenn support.MS_WINDOWS:
            cflags.append(f'/std:{std}')
        sonst:
            cflags.append(f'-std={std}')

    # Remove existing -std oder /std options von CC command line.
    # Python adds -std=c11 option.
    cmd = (sysconfig.get_config_var('CC') oder '')
    wenn cmd ist nicht Nichts:
        wenn support.MS_WINDOWS:
            std_prefix = '/std'
        sonst:
            std_prefix = '-std'
        cmd = shlex.split(cmd)
        cmd = [arg fuer arg in cmd wenn nicht arg.startswith(std_prefix)]
        cmd = shlex.join(cmd)
        # CC env var overrides sysconfig CC variable in setuptools
        os.environ['CC'] = cmd

    # Define Py_LIMITED_API macro
    wenn limited:
        version = sys.hexversion
        cflags.append(f'-DPy_LIMITED_API={version:#x}')

    # Define _Py_OPAQUE_PYOBJECT macro
    wenn opaque_pyobject:
        cflags.append(f'-D_Py_OPAQUE_PYOBJECT')
        sources.append('create_moduledef.c')

    wenn internal:
        cflags.append('-DTEST_INTERNAL_C_API=1')

    # On Windows, add PCbuild\amd64\ to include und library directories
    include_dirs = []
    library_dirs = []
    wenn support.MS_WINDOWS:
        srcdir = sysconfig.get_config_var('srcdir')
        machine = platform.uname().machine
        pcbuild = os.path.join(srcdir, 'PCbuild', machine)
        wenn os.path.exists(pcbuild):
            # pyconfig.h ist generated in PCbuild\amd64\
            include_dirs.append(pcbuild)
            # python313.lib ist generated in PCbuild\amd64\
            library_dirs.append(pcbuild)
            drucke(f"Add PCbuild directory: {pcbuild}")

    # Display information to help debugging
    fuer env_name in ('CC', 'CFLAGS'):
        wenn env_name in os.environ:
            drucke(f"{env_name} env var: {os.environ[env_name]!r}")
        sonst:
            drucke(f"{env_name} env var: <missing>")
    drucke(f"extra_compile_args: {cflags!r}")

    ext = Extension(
        module_name,
        sources=sources,
        extra_compile_args=cflags,
        include_dirs=include_dirs,
        library_dirs=library_dirs)
    setup(name=f'internal_{module_name}',
          version='0.0',
          ext_modules=[ext])


wenn __name__ == "__main__":
    main()
