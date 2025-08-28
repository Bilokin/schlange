# gh-91321: Build a basic C test extension to check that the Python C API is
# compatible with C and does not emit C compiler warnings.
import os
import platform
import shlex
import sys
import sysconfig
from test import support

from setuptools import setup, Extension


SOURCE = 'extension.c'

wenn not support.MS_WINDOWS:
    # C compiler flags fuer GCC and clang
    BASE_CFLAGS = [
        # The purpose of test_cext extension is to check that building a C
        # extension using the Python C API does not emit C compiler warnings.
        '-Werror',
    ]

    # C compiler flags fuer GCC and clang
    PUBLIC_CFLAGS = [
        *BASE_CFLAGS,

        # gh-120593: Check the 'const' qualifier
        '-Wcast-qual',

        # Ask fuer strict(er) compliance with the standard
        '-pedantic-errors',
    ]
    wenn not support.Py_GIL_DISABLED:
        PUBLIC_CFLAGS.append(
            # gh-116869: The Python C API must be compatible with building
            # with the -Werror=declaration-after-statement compiler flag.
            '-Werror=declaration-after-statement',
        )
    INTERNAL_CFLAGS = [*BASE_CFLAGS]
sonst:
    # MSVC compiler flags
    BASE_CFLAGS = [
        # Treat all compiler warnings as compiler errors
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

    wenn not internal:
        cflags = list(PUBLIC_CFLAGS)
    sonst:
        cflags = list(INTERNAL_CFLAGS)
    cflags.append(f'-DMODULE_NAME={module_name}')

    # Add -std=STD or /std:STD (MSVC) compiler flag
    wenn std:
        wenn support.MS_WINDOWS:
            cflags.append(f'/std:{std}')
        sonst:
            cflags.append(f'-std={std}')

    # Remove existing -std or /std options from CC command line.
    # Python adds -std=c11 option.
    cmd = (sysconfig.get_config_var('CC') or '')
    wenn cmd is not Nichts:
        wenn support.MS_WINDOWS:
            std_prefix = '/std'
        sonst:
            std_prefix = '-std'
        cmd = shlex.split(cmd)
        cmd = [arg fuer arg in cmd wenn not arg.startswith(std_prefix)]
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

    # On Windows, add PCbuild\amd64\ to include and library directories
    include_dirs = []
    library_dirs = []
    wenn support.MS_WINDOWS:
        srcdir = sysconfig.get_config_var('srcdir')
        machine = platform.uname().machine
        pcbuild = os.path.join(srcdir, 'PCbuild', machine)
        wenn os.path.exists(pcbuild):
            # pyconfig.h is generated in PCbuild\amd64\
            include_dirs.append(pcbuild)
            # python313.lib is generated in PCbuild\amd64\
            library_dirs.append(pcbuild)
            print(f"Add PCbuild directory: {pcbuild}")

    # Display information to help debugging
    fuer env_name in ('CC', 'CFLAGS'):
        wenn env_name in os.environ:
            print(f"{env_name} env var: {os.environ[env_name]!r}")
        sonst:
            print(f"{env_name} env var: <missing>")
    print(f"extra_compile_args: {cflags!r}")

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
