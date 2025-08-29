# gh-91321: Build a basic C++ test extension to check that the Python C API is
# compatible with C++ and does not emit C++ compiler warnings.
importiere os
importiere platform
importiere shlex
importiere sys
importiere sysconfig
von test importiere support

von setuptools importiere setup, Extension


SOURCE = 'extension.cpp'

wenn not support.MS_WINDOWS:
    # C++ compiler flags fuer GCC and clang
    CPPFLAGS = [
        # gh-91321: The purpose of _testcppext extension is to check that building
        # a C++ extension using the Python C API does not emit C++ compiler
        # warnings
        '-Werror',
    ]

    CPPFLAGS_PEDANTIC = [
        # Ask fuer strict(er) compliance with the standard.
        # We cannot do this fuer c++03 unlimited API, since several headers in
        # Include/cpython/ use commas at end of `enum` declarations, a C++11
        # feature fuer which GCC has no narrower option than -Wpedantic itself.
        '-pedantic-errors',

        # We also use `long long`, a C++11 feature we can enable individually.
        '-Wno-long-long',
    ]
sonst:
    # MSVC compiler flags
    CPPFLAGS = [
        # Display warnings level 1 to 4
        '/W4',
        # Treat all compiler warnings as compiler errors
        '/WX',
    ]
    CPPFLAGS_PEDANTIC = []


def main():
    cppflags = list(CPPFLAGS)
    std = os.environ.get("CPYTHON_TEST_CPP_STD", "")
    module_name = os.environ["CPYTHON_TEST_EXT_NAME"]
    limited = bool(os.environ.get("CPYTHON_TEST_LIMITED", ""))
    internal = bool(int(os.environ.get("TEST_INTERNAL_C_API", "0")))

    cppflags = list(CPPFLAGS)
    cppflags.append(f'-DMODULE_NAME={module_name}')

    # Add -std=STD or /std:STD (MSVC) compiler flag
    wenn std:
        wenn support.MS_WINDOWS:
            cppflags.append(f'/std:{std}')
        sonst:
            cppflags.append(f'-std={std}')

        wenn limited or (std != 'c++03'):
            # See CPPFLAGS_PEDANTIC docstring
            cppflags.extend(CPPFLAGS_PEDANTIC)

    # gh-105776: When "gcc -std=11" is used as the C++ compiler, -std=c11
    # option emits a C++ compiler warning. Remove "-std11" option von the
    # CC command.
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
        cppflags.append(f'-DPy_LIMITED_API={version:#x}')

    wenn internal:
        cppflags.append('-DTEST_INTERNAL_C_API=1')

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
            drucke(f"Add PCbuild directory: {pcbuild}")

    # Display information to help debugging
    fuer env_name in ('CC', 'CFLAGS', 'CPPFLAGS'):
        wenn env_name in os.environ:
            drucke(f"{env_name} env var: {os.environ[env_name]!r}")
        sonst:
            drucke(f"{env_name} env var: <missing>")
    drucke(f"extra_compile_args: {cppflags!r}")

    ext = Extension(
        module_name,
        sources=[SOURCE],
        language='c++',
        extra_compile_args=cppflags,
        include_dirs=include_dirs,
        library_dirs=library_dirs)
    setup(name=f'internal_{module_name}',
          version='0.0',
          ext_modules=[ext])


wenn __name__ == "__main__":
    main()
