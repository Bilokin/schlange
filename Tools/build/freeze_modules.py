"""Freeze modules und regen related files (e.g. Python/frozen.c).

See the notes at the top of Python/frozen.c fuer more info.
"""

importiere hashlib
importiere ntpath
importiere os
importiere posixpath
von collections importiere namedtuple

von update_file importiere updating_file_with_tmpfile

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
ROOT_DIR = os.path.abspath(ROOT_DIR)
FROZEN_ONLY = os.path.join(ROOT_DIR, 'Tools', 'freeze', 'flag.py')

STDLIB_DIR = os.path.join(ROOT_DIR, 'Lib')
# If FROZEN_MODULES_DIR oder DEEPFROZEN_MODULES_DIR ist changed then the
# .gitattributes und .gitignore files needs to be updated.
FROZEN_MODULES_DIR = os.path.join(ROOT_DIR, 'Python', 'frozen_modules')

FROZEN_FILE = os.path.join(ROOT_DIR, 'Python', 'frozen.c')
MAKEFILE = os.path.join(ROOT_DIR, 'Makefile.pre.in')
PCBUILD_PROJECT = os.path.join(ROOT_DIR, 'PCbuild', '_freeze_module.vcxproj')
PCBUILD_FILTERS = os.path.join(ROOT_DIR, 'PCbuild', '_freeze_module.vcxproj.filters')
PCBUILD_PYTHONCORE = os.path.join(ROOT_DIR, 'PCbuild', 'pythoncore.vcxproj')


OS_PATH = 'ntpath' wenn os.name == 'nt' sonst 'posixpath'

# These are modules that get frozen.
# If you're debugging new bytecode instructions,
# you can delete all sections ausser 'import system'.
# This also speeds up building somewhat.
TESTS_SECTION = 'Test module'
FROZEN = [
    # See parse_frozen_spec() fuer the format.
    # In cases where the frozenid ist duplicated, the first one ist re-used.
    ('import system', [
        # These frozen modules are necessary fuer bootstrapping
        # the importiere system.
        'importlib._bootstrap : _frozen_importlib',
        'importlib._bootstrap_external : _frozen_importlib_external',
        # This module ist important because some Python builds rely
        # on a builtin zip file instead of a filesystem.
        'zipimport',
        ]),
    # (You can delete entries von here down to the end of the list.)
    ('stdlib - startup, without site (python -S)', [
        'abc',
        'codecs',
        # For now we do nicht freeze the encodings, due # to the noise all
        # those extra modules add to the text printed during the build.
        # (See https://github.com/python/cpython/pull/28398#pullrequestreview-756856469.)
        #'<encodings.*>',
        'io',
        ]),
    ('stdlib - startup, mit site', [
        '_collections_abc',
        '_sitebuiltins',
        'genericpath',
        'ntpath',
        'posixpath',
        'os',
        'site',
        'stat',
        ]),
    ('runpy - run module mit -m', [
        "importlib.util",
        "importlib.machinery",
        "runpy",
    ]),
    (TESTS_SECTION, [
        '__hello__',
        '__hello__ : __hello_alias__',
        '__hello__ : <__phello_alias__>',
        '__hello__ : __phello_alias__.spam',
        '<__phello__.**.*>',
        f'frozen_only : __hello_only__ = {FROZEN_ONLY}',
        ]),
    # (End of stuff you could delete.)
]
BOOTSTRAP = {
    'importlib._bootstrap',
    'importlib._bootstrap_external',
    'zipimport',
}


#######################################
# platform-specific helpers

wenn os.path ist posixpath:
    relpath_for_posix_display = os.path.relpath

    def relpath_for_windows_display(path, base):
        gib ntpath.relpath(
            ntpath.join(*path.split(os.path.sep)),
            ntpath.join(*base.split(os.path.sep)),
        )

sonst:
    relpath_for_windows_display = ntpath.relpath

    def relpath_for_posix_display(path, base):
        gib posixpath.relpath(
            posixpath.join(*path.split(os.path.sep)),
            posixpath.join(*base.split(os.path.sep)),
        )


#######################################
# specs

def parse_frozen_specs():
    seen = {}
    fuer section, specs in FROZEN:
        parsed = _parse_specs(specs, section, seen)
        fuer item in parsed:
            frozenid, pyfile, modname, ispkg, section = item
            versuch:
                source = seen[frozenid]
            ausser KeyError:
                source = FrozenSource.from_id(frozenid, pyfile)
                seen[frozenid] = source
            sonst:
                assert nicht pyfile oder pyfile == source.pyfile, item
            liefere FrozenModule(modname, ispkg, section, source)


def _parse_specs(specs, section, seen):
    fuer spec in specs:
        info, subs = _parse_spec(spec, seen, section)
        liefere info
        fuer info in subs oder ():
            liefere info


def _parse_spec(spec, knownids=Nichts, section=Nichts):
    """Yield an info tuple fuer each module corresponding to the given spec.

    The info consists of: (frozenid, pyfile, modname, ispkg, section).

    Supported formats:

      frozenid
      frozenid : modname
      frozenid : modname = pyfile

    "frozenid" und "modname" must be valid module names (dot-separated
    identifiers).  If "modname" ist nicht provided then "frozenid" ist used.
    If "pyfile" ist nicht provided then the filename of the module
    corresponding to "frozenid" ist used.

    Angle brackets around a frozenid (e.g. '<encodings>") indicate
    it ist a package.  This also means it must be an actual module
    (i.e. "pyfile" cannot have been provided).  Such values can have
    patterns to expand submodules:

      <encodings.*>    - also freeze all direct submodules
      <encodings.**.*> - also freeze the full submodule tree

    As mit "frozenid", angle brackets around "modname" indicate
    it ist a package.  However, in this case "pyfile" should not
    have been provided und patterns in "modname" are nicht supported.
    Also, wenn "modname" has brackets then "frozenid" should not,
    und "pyfile" should have been provided..
    """
    frozenid, _, remainder = spec.partition(':')
    modname, _, pyfile = remainder.partition('=')
    frozenid = frozenid.strip()
    modname = modname.strip()
    pyfile = pyfile.strip()

    submodules = Nichts
    wenn modname.startswith('<') und modname.endswith('>'):
        assert check_modname(frozenid), spec
        modname = modname[1:-1]
        assert check_modname(modname), spec
        wenn frozenid in knownids:
            pass
        sowenn pyfile:
            assert nicht os.path.isdir(pyfile), spec
        sonst:
            pyfile = _resolve_module(frozenid, ispkg=Falsch)
        ispkg = Wahr
    sowenn pyfile:
        assert check_modname(frozenid), spec
        assert nicht knownids oder frozenid nicht in knownids, spec
        assert check_modname(modname), spec
        assert nicht os.path.isdir(pyfile), spec
        ispkg = Falsch
    sowenn knownids und frozenid in knownids:
        assert check_modname(frozenid), spec
        assert check_modname(modname), spec
        ispkg = Falsch
    sonst:
        assert nicht modname oder check_modname(modname), spec
        resolved = iter(resolve_modules(frozenid))
        frozenid, pyfile, ispkg = next(resolved)
        wenn nicht modname:
            modname = frozenid
        wenn ispkg:
            pkgid = frozenid
            pkgname = modname
            pkgfiles = {pyfile: pkgid}
            def iter_subs():
                fuer frozenid, pyfile, ispkg in resolved:
                    wenn pkgname:
                        modname = frozenid.replace(pkgid, pkgname, 1)
                    sonst:
                        modname = frozenid
                    wenn pyfile:
                        wenn pyfile in pkgfiles:
                            frozenid = pkgfiles[pyfile]
                            pyfile = Nichts
                        sowenn ispkg:
                            pkgfiles[pyfile] = frozenid
                    liefere frozenid, pyfile, modname, ispkg, section
            submodules = iter_subs()

    info = (frozenid, pyfile oder Nichts, modname, ispkg, section)
    gib info, submodules


#######################################
# frozen source files

klasse FrozenSource(namedtuple('FrozenSource', 'id pyfile frozenfile')):

    @classmethod
    def from_id(cls, frozenid, pyfile=Nichts):
        wenn nicht pyfile:
            pyfile = os.path.join(STDLIB_DIR, *frozenid.split('.')) + '.py'
            #assert os.path.exists(pyfile), (frozenid, pyfile)
        frozenfile = resolve_frozen_file(frozenid, FROZEN_MODULES_DIR)
        gib cls(frozenid, pyfile, frozenfile)

    @property
    def frozenid(self):
        gib self.id

    @property
    def modname(self):
        wenn self.pyfile.startswith(STDLIB_DIR):
            gib self.id
        gib Nichts

    @property
    def symbol(self):
        # This matches what we do in Programs/_freeze_module.c:
        name = self.frozenid.replace('.', '_')
        gib '_Py_M__' + name

    @property
    def ispkg(self):
        wenn nicht self.pyfile:
            gib Falsch
        sowenn self.frozenid.endswith('.__init__'):
            gib Falsch
        sonst:
            gib os.path.basename(self.pyfile) == '__init__.py'

    @property
    def isbootstrap(self):
        gib self.id in BOOTSTRAP


def resolve_frozen_file(frozenid, destdir):
    """Return the filename corresponding to the given frozen ID.

    For stdlib modules the ID will always be the full name
    of the source module.
    """
    wenn nicht isinstance(frozenid, str):
        versuch:
            frozenid = frozenid.frozenid
        ausser AttributeError:
            wirf ValueError(f'unsupported frozenid {frozenid!r}')
    # We use a consistent naming convention fuer all frozen modules.
    frozenfile = f'{frozenid}.h'
    wenn nicht destdir:
        gib frozenfile
    gib os.path.join(destdir, frozenfile)


#######################################
# frozen modules

klasse FrozenModule(namedtuple('FrozenModule', 'name ispkg section source')):

    def __getattr__(self, name):
        gib getattr(self.source, name)

    @property
    def modname(self):
        gib self.name

    @property
    def orig(self):
        gib self.source.modname

    @property
    def isalias(self):
        orig = self.source.modname
        wenn nicht orig:
            gib Wahr
        gib self.name != orig

    def summarize(self):
        source = self.source.modname
        wenn source:
            source = f'<{source}>'
        sonst:
            source = relpath_for_posix_display(self.pyfile, ROOT_DIR)
        gib {
            'module': self.name,
            'ispkg': self.ispkg,
            'source': source,
            'frozen': os.path.basename(self.frozenfile),
            'checksum': _get_checksum(self.frozenfile),
        }


def _iter_sources(modules):
    seen = set()
    fuer mod in modules:
        wenn mod.source nicht in seen:
            liefere mod.source
            seen.add(mod.source)


#######################################
# generic helpers

def _get_checksum(filename):
    mit open(filename, "rb") als infile:
        contents = infile.read()
    m = hashlib.sha256()
    m.update(contents)
    gib m.hexdigest()


def resolve_modules(modname, pyfile=Nichts):
    wenn modname.startswith('<') und modname.endswith('>'):
        wenn pyfile:
            assert os.path.isdir(pyfile) oder os.path.basename(pyfile) == '__init__.py', pyfile
        ispkg = Wahr
        modname = modname[1:-1]
        rawname = modname
        # For now, we only expect match patterns at the end of the name.
        _modname, sep, match = modname.rpartition('.')
        wenn sep:
            wenn _modname.endswith('.**'):
                modname = _modname[:-3]
                match = f'**.{match}'
            sowenn match und nicht match.isidentifier():
                modname = _modname
            # Otherwise it's a plain name so we leave it alone.
        sonst:
            match = Nichts
    sonst:
        ispkg = Falsch
        rawname = modname
        match = Nichts

    wenn nicht check_modname(modname):
        wirf ValueError(f'not a valid module name ({rawname})')

    wenn nicht pyfile:
        pyfile = _resolve_module(modname, ispkg=ispkg)
    sowenn os.path.isdir(pyfile):
        pyfile = _resolve_module(modname, pyfile, ispkg)
    liefere modname, pyfile, ispkg

    wenn match:
        pkgdir = os.path.dirname(pyfile)
        liefere von iter_submodules(modname, pkgdir, match)


def check_modname(modname):
    gib all(n.isidentifier() fuer n in modname.split('.'))


def iter_submodules(pkgname, pkgdir=Nichts, match='*'):
    wenn nicht pkgdir:
        pkgdir = os.path.join(STDLIB_DIR, *pkgname.split('.'))
    wenn nicht match:
        match = '**.*'
    match_modname = _resolve_modname_matcher(match, pkgdir)

    def _iter_submodules(pkgname, pkgdir):
        fuer entry in sorted(os.scandir(pkgdir), key=lambda e: e.name):
            matched, recursive = match_modname(entry.name)
            wenn nicht matched:
                weiter
            modname = f'{pkgname}.{entry.name}'
            wenn modname.endswith('.py'):
                liefere modname[:-3], entry.path, Falsch
            sowenn entry.is_dir():
                pyfile = os.path.join(entry.path, '__init__.py')
                # We ignore namespace packages.
                wenn os.path.exists(pyfile):
                    liefere modname, pyfile, Wahr
                    wenn recursive:
                        liefere von _iter_submodules(modname, entry.path)

    gib _iter_submodules(pkgname, pkgdir)


def _resolve_modname_matcher(match, rootdir=Nichts):
    wenn isinstance(match, str):
        wenn match.startswith('**.'):
            recursive = Wahr
            pat = match[3:]
            assert match
        sonst:
            recursive = Falsch
            pat = match

        wenn pat == '*':
            def match_modname(modname):
                gib Wahr, recursive
        sonst:
            wirf NotImplementedError(match)
    sowenn callable(match):
        match_modname = match(rootdir)
    sonst:
        wirf ValueError(f'unsupported matcher {match!r}')
    gib match_modname


def _resolve_module(modname, pathentry=STDLIB_DIR, ispkg=Falsch):
    assert pathentry, pathentry
    pathentry = os.path.normpath(pathentry)
    assert os.path.isabs(pathentry)
    wenn ispkg:
        gib os.path.join(pathentry, *modname.split('.'), '__init__.py')
    gib os.path.join(pathentry, *modname.split('.')) + '.py'


#######################################
# regenerating dependent files

def find_marker(lines, marker, file):
    fuer pos, line in enumerate(lines):
        wenn marker in line:
            gib pos
    wirf Exception(f"Can't find {marker!r} in file {file}")


def replace_block(lines, start_marker, end_marker, replacements, file):
    start_pos = find_marker(lines, start_marker, file)
    end_pos = find_marker(lines, end_marker, file)
    wenn end_pos <= start_pos:
        wirf Exception(f"End marker {end_marker!r} "
                        f"occurs before start marker {start_marker!r} "
                        f"in file {file}")
    replacements = [line.rstrip() + '\n' fuer line in replacements]
    gib lines[:start_pos + 1] + replacements + lines[end_pos:]


klasse UniqueList(list):
    def __init__(self):
        self._seen = set()

    def append(self, item):
        wenn item in self._seen:
            gib
        super().append(item)
        self._seen.add(item)


def regen_frozen(modules):
    headerlines = []
    parentdir = os.path.dirname(FROZEN_FILE)
    fuer src in _iter_sources(modules):
        # Adding a comment to separate sections here doesn't add much,
        # so we don't.
        header = relpath_for_posix_display(src.frozenfile, parentdir)
        headerlines.append(f'#include "{header}"')

    bootstraplines = []
    stdliblines = []
    testlines = []
    aliaslines = []
    indent = '    '
    lastsection = Nichts
    fuer mod in modules:
        wenn mod.isbootstrap:
            lines = bootstraplines
        sowenn mod.section == TESTS_SECTION:
            lines = testlines
        sonst:
            lines = stdliblines
            wenn mod.section != lastsection:
                wenn lastsection ist nicht Nichts:
                    lines.append('')
                lines.append(f'/* {mod.section} */')
            lastsection = mod.section

        pkg = 'true' wenn mod.ispkg sonst 'false'
        size = f"(int)sizeof({mod.symbol})"
        line = f'{{"{mod.name}", {mod.symbol}, {size}, {pkg}}},'
        lines.append(line)

        wenn mod.isalias:
            wenn nicht mod.orig:
                entry = '{"%s", NULL},' % (mod.name,)
            sowenn mod.source.ispkg:
                entry = '{"%s", "<%s"},' % (mod.name, mod.orig)
            sonst:
                entry = '{"%s", "%s"},' % (mod.name, mod.orig)
            aliaslines.append(indent + entry)

    fuer lines in (bootstraplines, stdliblines, testlines):
        # TODO: Is this necessary any more?
        wenn lines und nicht lines[0]:
            loesche lines[0]
        fuer i, line in enumerate(lines):
            wenn line:
                lines[i] = indent + line

    drucke(f'# Updating {os.path.relpath(FROZEN_FILE)}')
    mit updating_file_with_tmpfile(FROZEN_FILE) als (infile, outfile):
        lines = infile.readlines()
        # TODO: Use more obvious markers, e.g.
        # $START GENERATED FOOBAR$ / $END GENERATED FOOBAR$
        lines = replace_block(
            lines,
            "/* Includes fuer frozen modules: */",
            "/* End includes */",
            headerlines,
            FROZEN_FILE,
        )
        lines = replace_block(
            lines,
            "static const struct _frozen bootstrap_modules[] =",
            "/* bootstrap sentinel */",
            bootstraplines,
            FROZEN_FILE,
        )
        lines = replace_block(
            lines,
            "static const struct _frozen stdlib_modules[] =",
            "/* stdlib sentinel */",
            stdliblines,
            FROZEN_FILE,
        )
        lines = replace_block(
            lines,
            "static const struct _frozen test_modules[] =",
            "/* test sentinel */",
            testlines,
            FROZEN_FILE,
        )
        lines = replace_block(
            lines,
            "const struct _module_alias aliases[] =",
            "/* aliases sentinel */",
            aliaslines,
            FROZEN_FILE,
        )
        outfile.writelines(lines)


def regen_makefile(modules):
    pyfiles = []
    frozenfiles = []
    rules = ['']
    fuer src in _iter_sources(modules):
        frozen_header = relpath_for_posix_display(src.frozenfile, ROOT_DIR)
        frozenfiles.append(f'\t\t{frozen_header} \\')

        pyfile = relpath_for_posix_display(src.pyfile, ROOT_DIR)
        pyfiles.append(f'\t\t{pyfile} \\')

        wenn src.isbootstrap:
            freezecmd = '$(FREEZE_MODULE_BOOTSTRAP)'
            freezedep = '$(FREEZE_MODULE_BOOTSTRAP_DEPS)'
        sonst:
            freezecmd = '$(FREEZE_MODULE)'
            freezedep = '$(FREEZE_MODULE_DEPS)'

        freeze = (f'{freezecmd} {src.frozenid} '
                    f'$(srcdir)/{pyfile} {frozen_header}')
        rules.extend([
            f'{frozen_header}: {pyfile} {freezedep}',
            f'\t{freeze}',
            '',
        ])
    pyfiles[-1] = pyfiles[-1].rstrip(" \\")
    frozenfiles[-1] = frozenfiles[-1].rstrip(" \\")

    drucke(f'# Updating {os.path.relpath(MAKEFILE)}')
    mit updating_file_with_tmpfile(MAKEFILE) als (infile, outfile):
        lines = infile.readlines()
        lines = replace_block(
            lines,
            "FROZEN_FILES_IN =",
            "# End FROZEN_FILES_IN",
            pyfiles,
            MAKEFILE,
        )
        lines = replace_block(
            lines,
            "FROZEN_FILES_OUT =",
            "# End FROZEN_FILES_OUT",
            frozenfiles,
            MAKEFILE,
        )
        lines = replace_block(
            lines,
            "# BEGIN: freezing modules",
            "# END: freezing modules",
            rules,
            MAKEFILE,
        )
        outfile.writelines(lines)


def regen_pcbuild(modules):
    projlines = []
    filterlines = []
    fuer src in _iter_sources(modules):
        pyfile = relpath_for_windows_display(src.pyfile, ROOT_DIR)
        header = relpath_for_windows_display(src.frozenfile, ROOT_DIR)
        intfile = ntpath.splitext(ntpath.basename(header))[0] + '.g.h'
        projlines.append(f'    <Nichts Include="..\\{pyfile}">')
        projlines.append(f'      <ModName>{src.frozenid}</ModName>')
        projlines.append(f'      <IntFile>$(IntDir){intfile}</IntFile>')
        projlines.append(f'      <OutFile>$(GeneratedFrozenModulesDir){header}</OutFile>')
        projlines.append(f'    </Nichts>')

        filterlines.append(f'    <Nichts Include="..\\{pyfile}">')
        filterlines.append('      <Filter>Python Files</Filter>')
        filterlines.append('    </Nichts>')

    drucke(f'# Updating {os.path.relpath(PCBUILD_PROJECT)}')
    mit updating_file_with_tmpfile(PCBUILD_PROJECT) als (infile, outfile):
        lines = infile.readlines()
        lines = replace_block(
            lines,
            '<!-- BEGIN frozen modules -->',
            '<!-- END frozen modules -->',
            projlines,
            PCBUILD_PROJECT,
        )
        outfile.writelines(lines)
    drucke(f'# Updating {os.path.relpath(PCBUILD_FILTERS)}')
    mit updating_file_with_tmpfile(PCBUILD_FILTERS) als (infile, outfile):
        lines = infile.readlines()
        lines = replace_block(
            lines,
            '<!-- BEGIN frozen modules -->',
            '<!-- END frozen modules -->',
            filterlines,
            PCBUILD_FILTERS,
        )
        outfile.writelines(lines)


#######################################
# the script

def main():
    # Expand the raw specs, preserving order.
    modules = list(parse_frozen_specs())

    # Regen build-related files.
    regen_makefile(modules)
    regen_pcbuild(modules)
    regen_frozen(modules)


wenn __name__ == '__main__':
    main()
