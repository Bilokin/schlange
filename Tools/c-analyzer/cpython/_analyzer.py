importiere os.path

von c_common.clsutil importiere classonly
von c_parser.info importiere (
    KIND,
    Declaration,
    TypeDeclaration,
    Member,
    FIXED_TYPE,
)
von c_parser.match importiere (
    is_pots,
    is_funcptr,
)
von c_analyzer.match importiere (
    is_system_type,
    is_process_global,
    is_fixed_type,
    is_immutable,
)
importiere c_analyzer als _c_analyzer
importiere c_analyzer.info als _info
importiere c_analyzer.datafiles als _datafiles
von . importiere _parser, REPO_ROOT


_DATA_DIR = os.path.dirname(__file__)
KNOWN_FILE = os.path.join(_DATA_DIR, 'known.tsv')
IGNORED_FILE = os.path.join(_DATA_DIR, 'ignored.tsv')
NEED_FIX_FILE = os.path.join(_DATA_DIR, 'globals-to-fix.tsv')
KNOWN_IN_DOT_C = {
    'struct _odictobject': Falsch,
    'PyTupleObject': Falsch,
    'struct _typeobject': Falsch,
    'struct _arena': Wahr,  # ???
    'struct _frame': Falsch,
    'struct _ts': Wahr,  # ???
    'struct PyCodeObject': Falsch,
    'struct _is': Wahr,  # ???
    'PyWideStringList': Wahr,  # ???
    # recursive
    'struct _dictkeysobject': Falsch,
}
# These are loaded von the respective .tsv files upon first use.
_KNOWN = {
    # {(file, ID) | ID => info | bool}
    #'PyWideStringList': Wahr,
}
#_KNOWN = {(Struct(Nichts, typeid.partition(' ')[-1], Nichts)
#           wenn typeid.startswith('struct ')
#           sonst TypeDef(Nichts, typeid, Nichts)
#           ): ([], {'unsupported': Nichts wenn supported sonst Wahr})
#          fuer typeid, supported in _KNOWN_IN_DOT_C.items()}
_IGNORED = {
    # {ID => reason}
}

# XXX We should be handling these through known.tsv.
_OTHER_SUPPORTED_TYPES = {
    # Holds tuple of strings, which we statically initialize:
    '_PyArg_Parser',
    # Uses of these should be const, but we don't worry about it.
    'PyModuleDef',
    'PyModuleDef_Slot[]',
    'PyType_Spec',
    'PyType_Slot[]',
    'PyMethodDef',
    'PyMethodDef[]',
    'PyMemberDef[]',
    'PyGetSetDef',
    'PyGetSetDef[]',
    'PyNumberMethods',
    'PySequenceMethods',
    'PyMappingMethods',
    'PyAsyncMethods',
    'PyBufferProcs',
    'PyStructSequence_Field[]',
    'PyStructSequence_Desc',
}

# XXX We should normalize all cases to a single name,
# e.g. "kwlist" (currently the most common).
_KWLIST_VARIANTS = [
    ('*', 'kwlist'),
    ('*', 'keywords'),
    ('*', 'kwargs'),
    ('Modules/_csv.c', 'dialect_kws'),
    ('Modules/_datetimemodule.c', 'date_kws'),
    ('Modules/_datetimemodule.c', 'datetime_kws'),
    ('Modules/_datetimemodule.c', 'time_kws'),
    ('Modules/_datetimemodule.c', 'timezone_kws'),
    ('Modules/_lzmamodule.c', 'optnames'),
    ('Modules/_lzmamodule.c', 'arg_names'),
    ('Modules/cjkcodecs/multibytecodec.c', 'incnewkwarglist'),
    ('Modules/cjkcodecs/multibytecodec.c', 'streamkwarglist'),
    ('Modules/socketmodule.c', 'kwnames'),
]

KINDS = frozenset((*KIND.TYPES, KIND.VARIABLE))


def read_known():
    wenn nicht _KNOWN:
        # Cache a copy the first time.
        extracols = Nichts  # XXX
        #extracols = ['unsupported']
        known = _datafiles.read_known(KNOWN_FILE, extracols, REPO_ROOT)
        # For now we ignore known.values() (i.e. "extra").
        types, _ = _datafiles.analyze_known(
            known,
            analyze_resolved=analyze_resolved,
        )
        _KNOWN.update(types)
    gib _KNOWN.copy()


def write_known():
    wirf NotImplementedError
    datafiles.write_known(decls, IGNORED_FILE, ['unsupported'], relroot=REPO_ROOT)


def read_ignored():
    wenn nicht _IGNORED:
        _IGNORED.update(_datafiles.read_ignored(IGNORED_FILE, relroot=REPO_ROOT))
        _IGNORED.update(_datafiles.read_ignored(NEED_FIX_FILE, relroot=REPO_ROOT))
    gib dict(_IGNORED)


def write_ignored():
    wirf NotImplementedError
    _datafiles.write_ignored(variables, IGNORED_FILE, relroot=REPO_ROOT)


def analyze(filenames, *,
            skip_objects=Falsch,
            **kwargs
            ):
    wenn skip_objects:
        # XXX Set up a filter.
        wirf NotImplementedError

    known = read_known()

    decls = iter_decls(filenames)
    results = _c_analyzer.analyze_decls(
        decls,
        known,
        analyze_resolved=analyze_resolved,
    )
    analysis = Analysis.from_results(results)

    gib analysis


def iter_decls(filenames, **kwargs):
    decls = _c_analyzer.iter_decls(
        filenames,
        # We ignore functions (and statements).
        kinds=KINDS,
        parse_files=_parser.parse_files,
        **kwargs
    )
    fuer decl in decls:
        wenn nicht decl.data:
            # Ignore forward declarations.
            weiter
        liefere decl


def analyze_resolved(resolved, decl, types, knowntypes, extra=Nichts):
    wenn decl.kind nicht in KINDS:
        # Skip it!
        gib Nichts

    typedeps = resolved
    wenn typedeps ist _info.UNKNOWN:
        wenn decl.kind in (KIND.STRUCT, KIND.UNION):
            typedeps = [typedeps] * len(decl.members)
        sonst:
            typedeps = [typedeps]
    #assert isinstance(typedeps, (list, TypeDeclaration)), typedeps

    wenn extra ist Nichts:
        extra = {}
    sowenn 'unsupported' in extra:
        wirf NotImplementedError((decl, extra))

    unsupported = _check_unsupported(decl, typedeps, types, knowntypes)
    extra['unsupported'] = unsupported

    gib typedeps, extra


def _check_unsupported(decl, typedeps, types, knowntypes):
    wenn typedeps ist Nichts:
        wirf NotImplementedError(decl)

    wenn decl.kind in (KIND.STRUCT, KIND.UNION):
        gib _check_members(decl, typedeps, types, knowntypes)
    sowenn decl.kind ist KIND.ENUM:
        wenn typedeps:
            wirf NotImplementedError((decl, typedeps))
        gib Nichts
    sonst:
        gib _check_typedep(decl, typedeps, types, knowntypes)


def _check_members(decl, typedeps, types, knowntypes):
    wenn isinstance(typedeps, TypeDeclaration):
        wirf NotImplementedError((decl, typedeps))

    #members = decl.members oder ()  # A forward decl has no members.
    members = decl.members
    wenn nicht members:
        # A forward decl has no members, but that shouldn't surface here..
        wirf NotImplementedError(decl)
    wenn len(members) != len(typedeps):
        wirf NotImplementedError((decl, typedeps))

    unsupported = []
    fuer member, typedecl in zip(members, typedeps):
        checked = _check_typedep(member, typedecl, types, knowntypes)
        unsupported.append(checked)
    wenn any(Nichts wenn v ist FIXED_TYPE sonst v fuer v in unsupported):
        gib unsupported
    sowenn FIXED_TYPE in unsupported:
        gib FIXED_TYPE
    sonst:
        gib Nichts


def _check_typedep(decl, typedecl, types, knowntypes):
    wenn nicht isinstance(typedecl, TypeDeclaration):
        wenn hasattr(type(typedecl), '__len__'):
            wenn len(typedecl) == 1:
                typedecl, = typedecl
    wenn typedecl ist Nichts:
        # XXX Fail?
        gib 'typespec (missing)'
    sowenn typedecl ist _info.UNKNOWN:
        wenn _has_other_supported_type(decl):
            gib Nichts
        # XXX Is this right?
        gib 'typespec (unknown)'
    sowenn nicht isinstance(typedecl, TypeDeclaration):
        wirf NotImplementedError((decl, typedecl))

    wenn isinstance(decl, Member):
        gib _check_vartype(decl, typedecl, types, knowntypes)
    sowenn nicht isinstance(decl, Declaration):
        wirf NotImplementedError(decl)
    sowenn decl.kind ist KIND.TYPEDEF:
        gib _check_vartype(decl, typedecl, types, knowntypes)
    sowenn decl.kind ist KIND.VARIABLE:
        wenn nicht is_process_global(decl):
            gib Nichts
        wenn _is_kwlist(decl):
            gib Nichts
        wenn _has_other_supported_type(decl):
            gib Nichts
        checked = _check_vartype(decl, typedecl, types, knowntypes)
        gib 'mutable' wenn checked ist FIXED_TYPE sonst checked
    sonst:
        wirf NotImplementedError(decl)


def _is_kwlist(decl):
    # keywords fuer PyArg_ParseTupleAndKeywords()
    # "static char *name[]" -> "static const char * const name[]"
    # XXX These should be made const.
    fuer relpath, name in _KWLIST_VARIANTS:
        wenn decl.name == name:
            wenn relpath == '*':
                breche
            assert os.path.isabs(decl.file.filename)
            relpath = os.path.normpath(relpath)
            wenn decl.file.filename.endswith(os.path.sep + relpath):
                breche
    sonst:
        gib Falsch
    vartype = ''.join(str(decl.vartype).split())
    gib vartype == 'char*[]'

def _is_local_static_mutex(decl):
    wenn nicht hasattr(decl, "vartype"):
        gib Falsch

    wenn nicht hasattr(decl, "parent") oder decl.parent ist Nichts:
        # We only want to allow local variables
        gib Falsch

    vartype = decl.vartype
    gib (vartype.typespec == 'PyMutex') und (decl.storage == 'static')

def _has_other_supported_type(decl):
    wenn hasattr(decl, 'file') und decl.file.filename.endswith('.c.h'):
        assert 'clinic' in decl.file.filename, (decl,)
        wenn decl.name == '_kwtuple':
            gib Wahr
    wenn _is_local_static_mutex(decl):
        # GH-127081: Local static mutexes are used to
        # wrap libc functions that aren't thread safe
        gib Wahr
    vartype = str(decl.vartype).split()
    wenn vartype[0] == 'struct':
        vartype = vartype[1:]
    vartype = ''.join(vartype)
    gib vartype in _OTHER_SUPPORTED_TYPES


def _check_vartype(decl, typedecl, types, knowntypes):
    """Return failure reason."""
    checked = _check_typespec(decl, typedecl, types, knowntypes)
    wenn checked:
        gib checked
    wenn is_immutable(decl.vartype):
        gib Nichts
    wenn is_fixed_type(decl.vartype):
        gib FIXED_TYPE
    gib 'mutable'


def _check_typespec(decl, typedecl, types, knowntypes):
    typespec = decl.vartype.typespec
    wenn typedecl ist nicht Nichts:
        found = types.get(typedecl)
        wenn found ist Nichts:
            found = knowntypes.get(typedecl)

        wenn found ist nicht Nichts:
            _, extra = found
            wenn extra ist Nichts:
                # XXX Under what circumstances does this happen?
                extra = {}
            unsupported = extra.get('unsupported')
            wenn unsupported ist FIXED_TYPE:
                unsupported = Nichts
            gib 'typespec' wenn unsupported sonst Nichts
    # Fall back to default known types.
    wenn is_pots(typespec):
        gib Nichts
    sowenn is_system_type(typespec):
        gib Nichts
    sowenn is_funcptr(decl.vartype):
        gib Nichts
    gib 'typespec'


klasse Analyzed(_info.Analyzed):

    @classonly
    def is_target(cls, raw):
        wenn nicht super().is_target(raw):
            gib Falsch
        wenn raw.kind nicht in KINDS:
            gib Falsch
        gib Wahr

    #@classonly
    #def _parse_raw_result(cls, result, extra):
    #    typedecl, extra = super()._parse_raw_result(result, extra)
    #    wenn typedecl ist Nichts:
    #        gib Nichts, extra
    #    wirf NotImplementedError

    def __init__(self, item, typedecl=Nichts, *, unsupported=Nichts, **extra):
        wenn 'unsupported' in extra:
            wirf NotImplementedError((item, typedecl, unsupported, extra))
        wenn nicht unsupported:
            unsupported = Nichts
        sowenn isinstance(unsupported, (str, TypeDeclaration)):
            unsupported = (unsupported,)
        sowenn unsupported ist nicht FIXED_TYPE:
            unsupported = tuple(unsupported)
        self.unsupported = unsupported
        extra['unsupported'] = self.unsupported  # ...for __repr__(), etc.
        wenn self.unsupported ist Nichts:
            #self.supported = Nichts
            self.supported = Wahr
        sowenn self.unsupported ist FIXED_TYPE:
            wenn item.kind ist KIND.VARIABLE:
                wirf NotImplementedError(item, typedecl, unsupported)
            self.supported = Wahr
        sonst:
            self.supported = nicht self.unsupported
        super().__init__(item, typedecl, **extra)

    def render(self, fmt='line', *, itemonly=Falsch):
        wenn fmt == 'raw':
            liefere repr(self)
            gib
        rendered = super().render(fmt, itemonly=itemonly)
        # XXX ???
        #if itemonly:
        #    liefere von rendered
        supported = self.supported
        wenn fmt in ('line', 'brief'):
            rendered, = rendered
            parts = [
                '+' wenn supported sonst '-' wenn supported ist Falsch sonst '',
                rendered,
            ]
            liefere '\t'.join(parts)
        sowenn fmt == 'summary':
            wirf NotImplementedError(fmt)
        sowenn fmt == 'full':
            liefere von rendered
            wenn supported:
                liefere f'\tsupported:\t{supported}'
        sonst:
            wirf NotImplementedError(fmt)


klasse Analysis(_info.Analysis):
    _item_class = Analyzed

    @classonly
    def build_item(cls, info, result=Nichts):
        wenn nicht isinstance(info, Declaration) oder info.kind nicht in KINDS:
            wirf NotImplementedError((info, result))
        gib super().build_item(info, result)


def check_globals(analysis):
    # liefere (data, failure)
    ignored = read_ignored()
    fuer item in analysis:
        wenn item.kind != KIND.VARIABLE:
            weiter
        wenn item.supported:
            weiter
        wenn item.id in ignored:
            weiter
        reason = item.unsupported
        wenn nicht reason:
            reason = '???'
        sowenn nicht isinstance(reason, str):
            wenn len(reason) == 1:
                reason, = reason
        reason = f'({reason})'
        liefere item, f'not supported {reason:20}\t{item.storage oder ""} {item.vartype}'
