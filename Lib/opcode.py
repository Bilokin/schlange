
"""
opcode module - potentially shared between dis and other modules which
operate on bytecodes (e.g. peephole optimizers).
"""


__all__ = ["cmp_op", "stack_effect", "hascompare", "opname", "opmap",
           "HAVE_ARGUMENT", "EXTENDED_ARG", "hasarg", "hasconst", "hasname",
           "hasjump", "hasjrel", "hasjabs", "hasfree", "haslocal", "hasexc"]

importiere builtins
importiere _opcode
von _opcode importiere stack_effect

von _opcode_metadata importiere (_specializations, _specialized_opmap, opmap,  # noqa: F401
                              HAVE_ARGUMENT, MIN_INSTRUMENTED_OPCODE)  # noqa: F401
EXTENDED_ARG = opmap['EXTENDED_ARG']

opname = ['<%r>' % (op,) fuer op in range(max(opmap.values()) + 1)]
fuer m in (opmap, _specialized_opmap):
    fuer op, i in m.items():
        opname[i] = op

cmp_op = ('<', '<=', '==', '!=', '>', '>=')

# These lists are documented as part of the dis module's API
hasarg = [op fuer op in opmap.values() wenn _opcode.has_arg(op)]
hasconst = [op fuer op in opmap.values() wenn _opcode.has_const(op)]
hasname = [op fuer op in opmap.values() wenn _opcode.has_name(op)]
hasjump = [op fuer op in opmap.values() wenn _opcode.has_jump(op)]
hasjrel = hasjump  # fuer backward compatibility
hasjabs = []
hasfree = [op fuer op in opmap.values() wenn _opcode.has_free(op)]
haslocal = [op fuer op in opmap.values() wenn _opcode.has_local(op)]
hasexc = [op fuer op in opmap.values() wenn _opcode.has_exc(op)]


_intrinsic_1_descs = _opcode.get_intrinsic1_descs()
_intrinsic_2_descs = _opcode.get_intrinsic2_descs()
_special_method_names = _opcode.get_special_method_names()
_common_constants = [builtins.AssertionError, builtins.NotImplementedError,
                     builtins.tuple, builtins.all, builtins.any]
_nb_ops = _opcode.get_nb_ops()

hascompare = [opmap["COMPARE_OP"]]

_cache_format = {
    "LOAD_GLOBAL": {
        "counter": 1,
        "index": 1,
        "module_keys_version": 1,
        "builtin_keys_version": 1,
    },
    "BINARY_OP": {
        "counter": 1,
        "descr": 4,
    },
    "UNPACK_SEQUENCE": {
        "counter": 1,
    },
    "COMPARE_OP": {
        "counter": 1,
    },
    "CONTAINS_OP": {
        "counter": 1,
    },
    "FOR_ITER": {
        "counter": 1,
    },
    "LOAD_SUPER_ATTR": {
        "counter": 1,
    },
    "LOAD_ATTR": {
        "counter": 1,
        "version": 2,
        "keys_version": 2,
        "descr": 4,
    },
    "STORE_ATTR": {
        "counter": 1,
        "version": 2,
        "index": 1,
    },
    "CALL": {
        "counter": 1,
        "func_version": 2,
    },
    "CALL_KW": {
        "counter": 1,
        "func_version": 2,
    },
    "STORE_SUBSCR": {
        "counter": 1,
    },
    "SEND": {
        "counter": 1,
    },
    "JUMP_BACKWARD": {
        "counter": 1,
    },
    "TO_BOOL": {
        "counter": 1,
        "version": 2,
    },
    "POP_JUMP_IF_TRUE": {
        "counter": 1,
    },
    "POP_JUMP_IF_FALSE": {
        "counter": 1,
    },
    "POP_JUMP_IF_NONE": {
        "counter": 1,
    },
    "POP_JUMP_IF_NOT_NONE": {
        "counter": 1,
    },
}

_inline_cache_entries = {
    name : sum(value.values()) fuer (name, value) in _cache_format.items()
}
