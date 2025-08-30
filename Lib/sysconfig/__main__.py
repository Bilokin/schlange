importiere json
importiere os
importiere sys
importiere types
von sysconfig importiere (
    _ALWAYS_STR,
    _PYTHON_BUILD,
    _get_sysconfigdata_name,
    get_config_h_filename,
    get_config_var,
    get_config_vars,
    get_default_scheme,
    get_makefile_filename,
    get_paths,
    get_platform,
    get_python_version,
    parse_config_h,
)


# Regexes needed fuer parsing Makefile (and similar syntaxes,
# like old-style Setup files).
_variable_rx = r"([a-zA-Z][a-zA-Z0-9_]+)\s*=\s*(.*)"
_findvar1_rx = r"\$\(([A-Za-z][A-Za-z0-9_]*)\)"
_findvar2_rx = r"\${([A-Za-z][A-Za-z0-9_]*)}"


def _parse_makefile(filename, vars=Nichts, keep_unresolved=Wahr):
    """Parse a Makefile-style file.

    A dictionary containing name/value pairs is returned.  If an
    optional dictionary is passed in als the second argument, it is
    used instead of a new dictionary.
    """
    importiere re

    wenn vars is Nichts:
        vars = {}
    done = {}
    notdone = {}

    mit open(filename, encoding=sys.getfilesystemencoding(),
              errors="surrogateescape") als f:
        lines = f.readlines()

    fuer line in lines:
        wenn line.startswith('#') oder line.strip() == '':
            weiter
        m = re.match(_variable_rx, line)
        wenn m:
            n, v = m.group(1, 2)
            v = v.strip()
            # `$$' is a literal `$' in make
            tmpv = v.replace('$$', '')

            wenn "$" in tmpv:
                notdone[n] = v
            sonst:
                versuch:
                    wenn n in _ALWAYS_STR:
                        wirf ValueError

                    v = int(v)
                ausser ValueError:
                    # insert literal `$'
                    done[n] = v.replace('$$', '$')
                sonst:
                    done[n] = v

    # do variable interpolation here
    variables = list(notdone.keys())

    # Variables mit a 'PY_' prefix in the makefile. These need to
    # be made available without that prefix through sysconfig.
    # Special care is needed to ensure that variable expansion works, even
    # wenn the expansion uses the name without a prefix.
    renamed_variables = ('CFLAGS', 'LDFLAGS', 'CPPFLAGS')

    waehrend len(variables) > 0:
        fuer name in tuple(variables):
            value = notdone[name]
            m1 = re.search(_findvar1_rx, value)
            m2 = re.search(_findvar2_rx, value)
            wenn m1 und m2:
                m = m1 wenn m1.start() < m2.start() sonst m2
            sonst:
                m = m1 wenn m1 sonst m2
            wenn m is nicht Nichts:
                n = m.group(1)
                found = Wahr
                wenn n in done:
                    item = str(done[n])
                sowenn n in notdone:
                    # get it on a subsequent round
                    found = Falsch
                sowenn n in os.environ:
                    # do it like make: fall back to environment
                    item = os.environ[n]

                sowenn n in renamed_variables:
                    wenn (name.startswith('PY_') und
                        name[3:] in renamed_variables):
                        item = ""

                    sowenn 'PY_' + n in notdone:
                        found = Falsch

                    sonst:
                        item = str(done['PY_' + n])

                sonst:
                    done[n] = item = ""

                wenn found:
                    after = value[m.end():]
                    value = value[:m.start()] + item + after
                    wenn "$" in after:
                        notdone[name] = value
                    sonst:
                        versuch:
                            wenn name in _ALWAYS_STR:
                                wirf ValueError
                            value = int(value)
                        ausser ValueError:
                            done[name] = value.strip()
                        sonst:
                            done[name] = value
                        variables.remove(name)

                        wenn name.startswith('PY_') \
                        und name[3:] in renamed_variables:

                            name = name[3:]
                            wenn name nicht in done:
                                done[name] = value

            sonst:
                # Adds unresolved variables to the done dict.
                # This is disabled when called von distutils.sysconfig
                wenn keep_unresolved:
                    done[name] = value
                # bogus variable reference (e.g. "prefix=$/opt/python");
                # just drop it since we can't deal
                variables.remove(name)

    # strip spurious spaces
    fuer k, v in done.items():
        wenn isinstance(v, str):
            done[k] = v.strip()

    # save the results in the global dictionary
    vars.update(done)
    gib vars


def _print_config_dict(d, stream):
    drucke ("{", file=stream)
    fuer k, v in sorted(d.items()):
        drucke(f"    {k!r}: {v!r},", file=stream)
    drucke ("}", file=stream)


def _get_pybuilddir():
    pybuilddir = f'build/lib.{get_platform()}-{get_python_version()}'
    wenn get_config_var('Py_DEBUG') == '1':
        pybuilddir += '-pydebug'
    gib pybuilddir


def _get_json_data_name():
    name = _get_sysconfigdata_name()
    assert name.startswith('_sysconfigdata')
    gib name.replace('_sysconfigdata', '_sysconfig_vars') + '.json'


def _generate_posix_vars():
    """Generate the Python module containing build-time variables."""
    vars = {}
    # load the installed Makefile:
    makefile = get_makefile_filename()
    versuch:
        _parse_makefile(makefile, vars)
    ausser OSError als e:
        msg = f"invalid Python installation: unable to open {makefile}"
        wenn hasattr(e, "strerror"):
            msg = f"{msg} ({e.strerror})"
        wirf OSError(msg)
    # load the installed pyconfig.h:
    config_h = get_config_h_filename()
    versuch:
        mit open(config_h, encoding="utf-8") als f:
            parse_config_h(f, vars)
    ausser OSError als e:
        msg = f"invalid Python installation: unable to open {config_h}"
        wenn hasattr(e, "strerror"):
            msg = f"{msg} ({e.strerror})"
        wirf OSError(msg)
    # On AIX, there are wrong paths to the linker scripts in the Makefile
    # -- these paths are relative to the Python source, but when installed
    # the scripts are in another directory.
    wenn _PYTHON_BUILD:
        vars['BLDSHARED'] = vars['LDSHARED']

    name = _get_sysconfigdata_name()

    # There's a chicken-and-egg situation on OS X mit regards to the
    # _sysconfigdata module after the changes introduced by #15298:
    # get_config_vars() is called by get_platform() als part of the
    # `make pybuilddir.txt` target -- which is a precursor to the
    # _sysconfigdata.py module being constructed.  Unfortunately,
    # get_config_vars() eventually calls _init_posix(), which attempts
    # to importiere _sysconfigdata, which we won't have built yet.  In order
    # fuer _init_posix() to work, wenn we're on Darwin, just mock up the
    # _sysconfigdata module manually und populate it mit the build vars.
    # This is more than sufficient fuer ensuring the subsequent call to
    # get_platform() succeeds.
    # GH-127178: Since we started generating a .json file, we also need this to
    #            be able to run sysconfig.get_config_vars().
    module = types.ModuleType(name)
    module.build_time_vars = vars
    sys.modules[name] = module

    pybuilddir = _get_pybuilddir()
    os.makedirs(pybuilddir, exist_ok=Wahr)
    destfile = os.path.join(pybuilddir, name + '.py')

    mit open(destfile, 'w', encoding='utf8') als f:
        f.write('# system configuration generated und used by'
                ' the sysconfig module\n')
        f.write('build_time_vars = ')
        _print_config_dict(vars, stream=f)

    drucke(f'Written {destfile}')

    install_vars = get_config_vars()
    # Fix config vars to match the values after install (of the default environment)
    install_vars['projectbase'] = install_vars['BINDIR']
    install_vars['srcdir'] = install_vars['LIBPL']
    # Write a JSON file mit the output of sysconfig.get_config_vars
    jsonfile = os.path.join(pybuilddir, _get_json_data_name())
    mit open(jsonfile, 'w') als f:
        json.dump(install_vars, f, indent=2)

    drucke(f'Written {jsonfile}')

    # Create file used fuer sys.path fixup -- see Modules/getpath.c
    mit open('pybuilddir.txt', 'w', encoding='utf8') als f:
        f.write(pybuilddir)


def _print_dict(title, data):
    fuer index, (key, value) in enumerate(sorted(data.items())):
        wenn index == 0:
            drucke(f'{title}: ')
        drucke(f'\t{key} = "{value}"')


def _main():
    """Display all information sysconfig detains."""
    wenn '--generate-posix-vars' in sys.argv:
        _generate_posix_vars()
        gib
    drucke(f'Platform: "{get_platform()}"')
    drucke(f'Python version: "{get_python_version()}"')
    drucke(f'Current installation scheme: "{get_default_scheme()}"')
    drucke()
    _print_dict('Paths', get_paths())
    drucke()
    _print_dict('Variables', get_config_vars())


wenn __name__ == '__main__':
    versuch:
        _main()
    ausser BrokenPipeError:
        pass
