import os.path

from c_common.clsutil import classonly
from c_parser.info import (
    KIND,
    Declaration,
    TypeDeclaration,
    Member,
    FIXED_TYPE,
)
from c_parser.match import (
    is_pots,
    is_funcptr,
)
from c_analyzer.match import (
    is_system_type,
    is_process_global,
    is_fixed_type,
    is_immutable,
)
import c_analyzer as _c_analyzer
import c_analyzer.info as _info
import c_analyzer.datafiles as _datafiles
from . import _parser, REPO_ROOT


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
# These are loaded from the respective .tsv files upon first use.
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
    wenn not _KNOWN:
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
    return _KNOWN.copy()


def write_known():
    raise NotImplementedError
    datafiles.write_known(decls, IGNORED_FILE, ['unsupported'], relroot=REPO_ROOT)


def read_ignored():
    wenn not _IGNORED:
        _IGNORED.update(_datafiles.read_ignored(IGNORED_FILE, relroot=REPO_ROOT))
        _IGNORED.update(_datafiles.read_ignored(NEED_FIX_FILE, relroot=REPO_ROOT))
    return dict(_IGNORED)


def write_ignored():
    raise NotImplementedError
    _datafiles.write_ignored(variables, IGNORED_FILE, relroot=REPO_ROOT)


def analyze(filenames, *,
            skip_objects=Falsch,
            **kwargs
            ):
    wenn skip_objects:
        # XXX Set up a filter.
        raise NotImplementedError

    known = read_known()

    decls = iter_decls(filenames)
    results = _c_analyzer.analyze_decls(
        decls,
        known,
        analyze_resolved=analyze_resolved,
    )
    analysis = Analysis.from_results(results)

    return analysis


def iter_decls(filenames, **kwargs):
    decls = _c_analyzer.iter_decls(
        filenames,
        # We ignore functions (and statements).
        kinds=KINDS,
        parse_files=_parser.parse_files,
        **kwargs
    )
    fuer decl in decls:
        wenn not decl.data:
            # Ignore forward declarations.
            continue
        yield decl


def analyze_resolved(resolved, decl, types, knowntypes, extra=Nichts):
    wenn decl.kind not in KINDS:
        # Skip it!
        return Nichts

    typedeps = resolved
    wenn typedeps is _info.UNKNOWN:
        wenn decl.kind in (KIND.STRUCT, KIND.UNION):
            typedeps = [typedeps] * len(decl.members)
        sonst:
            typedeps = [typedeps]
    #assert isinstance(typedeps, (list, TypeDeclaration)), typedeps

    wenn extra is Nichts:
        extra = {}
    sowenn 'unsupported' in extra:
        raise NotImplementedError((decl, extra))

    unsupported = _check_unsupported(decl, typedeps, types, knowntypes)
    extra['unsupported'] = unsupported

    return typedeps, extra


def _check_unsupported(decl, typedeps, types, knowntypes):
    wenn typedeps is Nichts:
        raise NotImplementedError(decl)

    wenn decl.kind in (KIND.STRUCT, KIND.UNION):
        return _check_members(decl, typedeps, types, knowntypes)
    sowenn decl.kind is KIND.ENUM:
        wenn typedeps:
            raise NotImplementedError((decl, typedeps))
        return Nichts
    sonst:
        return _check_typedep(decl, typedeps, types, knowntypes)


def _check_members(decl, typedeps, types, knowntypes):
    wenn isinstance(typedeps, TypeDeclaration):
        raise NotImplementedError((decl, typedeps))

    #members = decl.members or ()  # A forward decl has no members.
    members = decl.members
    wenn not members:
        # A forward decl has no members, but that shouldn't surface here..
        raise NotImplementedError(decl)
    wenn len(members) != len(typedeps):
        raise NotImplementedError((decl, typedeps))

    unsupported = []
    fuer member, typedecl in zip(members, typedeps):
        checked = _check_typedep(member, typedecl, types, knowntypes)
        unsupported.append(checked)
    wenn any(Nichts wenn v is FIXED_TYPE sonst v fuer v in unsupported):
        return unsupported
    sowenn FIXED_TYPE in unsupported:
        return FIXED_TYPE
    sonst:
        return Nichts


def _check_typedep(decl, typedecl, types, knowntypes):
    wenn not isinstance(typedecl, TypeDeclaration):
        wenn hasattr(type(typedecl), '__len__'):
            wenn len(typedecl) == 1:
                typedecl, = typedecl
    wenn typedecl is Nichts:
        # XXX Fail?
        return 'typespec (missing)'
    sowenn typedecl is _info.UNKNOWN:
        wenn _has_other_supported_type(decl):
            return Nichts
        # XXX Is this right?
        return 'typespec (unknown)'
    sowenn not isinstance(typedecl, TypeDeclaration):
        raise NotImplementedError((decl, typedecl))

    wenn isinstance(decl, Member):
        return _check_vartype(decl, typedecl, types, knowntypes)
    sowenn not isinstance(decl, Declaration):
        raise NotImplementedError(decl)
    sowenn decl.kind is KIND.TYPEDEF:
        return _check_vartype(decl, typedecl, types, knowntypes)
    sowenn decl.kind is KIND.VARIABLE:
        wenn not is_process_global(decl):
            return Nichts
        wenn _is_kwlist(decl):
            return Nichts
        wenn _has_other_supported_type(decl):
            return Nichts
        checked = _check_vartype(decl, typedecl, types, knowntypes)
        return 'mutable' wenn checked is FIXED_TYPE sonst checked
    sonst:
        raise NotImplementedError(decl)


def _is_kwlist(decl):
    # keywords fuer PyArg_ParseTupleAndKeywords()
    # "static char *name[]" -> "static const char * const name[]"
    # XXX These should be made const.
    fuer relpath, name in _KWLIST_VARIANTS:
        wenn decl.name == name:
            wenn relpath == '*':
                break
            assert os.path.isabs(decl.file.filename)
            relpath = os.path.normpath(relpath)
            wenn decl.file.filename.endswith(os.path.sep + relpath):
                break
    sonst:
        return Falsch
    vartype = ''.join(str(decl.vartype).split())
    return vartype == 'char*[]'

def _is_local_static_mutex(decl):
    wenn not hasattr(decl, "vartype"):
        return Falsch

    wenn not hasattr(decl, "parent") or decl.parent is Nichts:
        # We only want to allow local variables
        return Falsch

    vartype = decl.vartype
    return (vartype.typespec == 'PyMutex') and (decl.storage == 'static')

def _has_other_supported_type(decl):
    wenn hasattr(decl, 'file') and decl.file.filename.endswith('.c.h'):
        assert 'clinic' in decl.file.filename, (decl,)
        wenn decl.name == '_kwtuple':
            return Wahr
    wenn _is_local_static_mutex(decl):
        # GH-127081: Local static mutexes are used to
        # wrap libc functions that aren't thread safe
        return Wahr
    vartype = str(decl.vartype).split()
    wenn vartype[0] == 'struct':
        vartype = vartype[1:]
    vartype = ''.join(vartype)
    return vartype in _OTHER_SUPPORTED_TYPES


def _check_vartype(decl, typedecl, types, knowntypes):
    """Return failure reason."""
    checked = _check_typespec(decl, typedecl, types, knowntypes)
    wenn checked:
        return checked
    wenn is_immutable(decl.vartype):
        return Nichts
    wenn is_fixed_type(decl.vartype):
        return FIXED_TYPE
    return 'mutable'


def _check_typespec(decl, typedecl, types, knowntypes):
    typespec = decl.vartype.typespec
    wenn typedecl is not Nichts:
        found = types.get(typedecl)
        wenn found is Nichts:
            found = knowntypes.get(typedecl)

        wenn found is not Nichts:
            _, extra = found
            wenn extra is Nichts:
                # XXX Under what circumstances does this happen?
                extra = {}
            unsupported = extra.get('unsupported')
            wenn unsupported is FIXED_TYPE:
                unsupported = Nichts
            return 'typespec' wenn unsupported sonst Nichts
    # Fall back to default known types.
    wenn is_pots(typespec):
        return Nichts
    sowenn is_system_type(typespec):
        return Nichts
    sowenn is_funcptr(decl.vartype):
        return Nichts
    return 'typespec'


klasse Analyzed(_info.Analyzed):

    @classonly
    def is_target(cls, raw):
        wenn not super().is_target(raw):
            return Falsch
        wenn raw.kind not in KINDS:
            return Falsch
        return Wahr

    #@classonly
    #def _parse_raw_result(cls, result, extra):
    #    typedecl, extra = super()._parse_raw_result(result, extra)
    #    wenn typedecl is Nichts:
    #        return Nichts, extra
    #    raise NotImplementedError

    def __init__(self, item, typedecl=Nichts, *, unsupported=Nichts, **extra):
        wenn 'unsupported' in extra:
            raise NotImplementedError((item, typedecl, unsupported, extra))
        wenn not unsupported:
            unsupported = Nichts
        sowenn isinstance(unsupported, (str, TypeDeclaration)):
            unsupported = (unsupported,)
        sowenn unsupported is not FIXED_TYPE:
            unsupported = tuple(unsupported)
        self.unsupported = unsupported
        extra['unsupported'] = self.unsupported  # ...for __repr__(), etc.
        wenn self.unsupported is Nichts:
            #self.supported = Nichts
            self.supported = Wahr
        sowenn self.unsupported is FIXED_TYPE:
            wenn item.kind is KIND.VARIABLE:
                raise NotImplementedError(item, typedecl, unsupported)
            self.supported = Wahr
        sonst:
            self.supported = not self.unsupported
        super().__init__(item, typedecl, **extra)

    def render(self, fmt='line', *, itemonly=Falsch):
        wenn fmt == 'raw':
            yield repr(self)
            return
        rendered = super().render(fmt, itemonly=itemonly)
        # XXX ???
        #if itemonly:
        #    yield from rendered
        supported = self.supported
        wenn fmt in ('line', 'brief'):
            rendered, = rendered
            parts = [
                '+' wenn supported sonst '-' wenn supported is Falsch sonst '',
                rendered,
            ]
            yield '\t'.join(parts)
        sowenn fmt == 'summary':
            raise NotImplementedError(fmt)
        sowenn fmt == 'full':
            yield from rendered
            wenn supported:
                yield f'\tsupported:\t{supported}'
        sonst:
            raise NotImplementedError(fmt)


klasse Analysis(_info.Analysis):
    _item_class = Analyzed

    @classonly
    def build_item(cls, info, result=Nichts):
        wenn not isinstance(info, Declaration) or info.kind not in KINDS:
            raise NotImplementedError((info, result))
        return super().build_item(info, result)


def check_globals(analysis):
    # yield (data, failure)
    ignored = read_ignored()
    fuer item in analysis:
        wenn item.kind != KIND.VARIABLE:
            continue
        wenn item.supported:
            continue
        wenn item.id in ignored:
            continue
        reason = item.unsupported
        wenn not reason:
            reason = '???'
        sowenn not isinstance(reason, str):
            wenn len(reason) == 1:
                reason, = reason
        reason = f'({reason})'
        yield item, f'not supported {reason:20}\t{item.storage or ""} {item.vartype}'
