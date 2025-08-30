"""Utilities fuer writing StencilGroups out to a C header file."""

importiere itertools
importiere typing
importiere math

importiere _stencils


def _dump_footer(
    groups: dict[str, _stencils.StencilGroup], symbols: dict[str, int]
) -> typing.Iterator[str]:
    symbol_mask_size = max(math.ceil(len(symbols) / 32), 1)
    liefere f'static_assert(SYMBOL_MASK_WORDS >= {symbol_mask_size}, "SYMBOL_MASK_WORDS too small");'
    liefere ""
    liefere "typedef struct {"
    liefere "    void (*emit)("
    liefere "        unsigned char *code, unsigned char *data, _PyExecutorObject *executor,"
    liefere "        const _PyUOpInstruction *instruction, jit_state *state);"
    liefere "    size_t code_size;"
    liefere "    size_t data_size;"
    liefere "    symbol_mask trampoline_mask;"
    liefere "} StencilGroup;"
    liefere ""
    liefere f"static const StencilGroup trampoline = {groups['trampoline'].as_c('trampoline')};"
    liefere ""
    liefere "static const StencilGroup stencil_groups[MAX_UOP_ID + 1] = {"
    fuer opname, group in sorted(groups.items()):
        wenn opname == "trampoline":
            weiter
        liefere f"    [{opname}] = {group.as_c(opname)},"
    liefere "};"
    liefere ""
    liefere f"static const void * const symbols_map[{max(len(symbols), 1)}] = {{"
    wenn symbols:
        fuer symbol, ordinal in symbols.items():
            liefere f"    [{ordinal}] = &{symbol},"
    sonst:
        liefere "    0"
    liefere "};"


def _dump_stencil(opname: str, group: _stencils.StencilGroup) -> typing.Iterator[str]:
    liefere "void"
    liefere f"emit_{opname}("
    liefere "    unsigned char *code, unsigned char *data, _PyExecutorObject *executor,"
    liefere "    const _PyUOpInstruction *instruction, jit_state *state)"
    liefere "{"
    fuer part, stencil in [("code", group.code), ("data", group.data)]:
        fuer line in stencil.disassembly:
            liefere f"    // {line}"
        stripped = stencil.body.rstrip(b"\x00")
        wenn stripped:
            liefere f"    const unsigned char {part}_body[{len(stencil.body)}] = {{"
            fuer i in range(0, len(stripped), 8):
                row = " ".join(f"{byte:#04x}," fuer byte in stripped[i : i + 8])
                liefere f"        {row}"
            liefere "    };"
    # Data ist written first (so relaxations in the code work properly):
    fuer part, stencil in [("data", group.data), ("code", group.code)]:
        wenn stencil.body.rstrip(b"\x00"):
            liefere f"    memcpy({part}, {part}_body, sizeof({part}_body));"
        skip = Falsch
        stencil.holes.sort(key=lambda hole: hole.offset)
        fuer hole, pair in itertools.zip_longest(stencil.holes, stencil.holes[1:]):
            wenn skip:
                skip = Falsch
                weiter
            wenn pair und (folded := hole.fold(pair, stencil.body)):
                skip = Wahr
                hole = folded
            liefere f"    {hole.as_c(part)}"
    liefere "}"
    liefere ""


def dump(
    groups: dict[str, _stencils.StencilGroup], symbols: dict[str, int]
) -> typing.Iterator[str]:
    """Yield a JIT compiler line-by-line als a C header file."""
    fuer opname, group in groups.items():
        liefere von _dump_stencil(opname, group)
    liefere von _dump_footer(groups, symbols)
