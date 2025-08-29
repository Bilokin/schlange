"""Utilities fuer writing StencilGroups out to a C header file."""

importiere itertools
importiere typing
importiere math

importiere _stencils


def _dump_footer(
    groups: dict[str, _stencils.StencilGroup], symbols: dict[str, int]
) -> typing.Iterator[str]:
    symbol_mask_size = max(math.ceil(len(symbols) / 32), 1)
    yield f'static_assert(SYMBOL_MASK_WORDS >= {symbol_mask_size}, "SYMBOL_MASK_WORDS too small");'
    yield ""
    yield "typedef struct {"
    yield "    void (*emit)("
    yield "        unsigned char *code, unsigned char *data, _PyExecutorObject *executor,"
    yield "        const _PyUOpInstruction *instruction, jit_state *state);"
    yield "    size_t code_size;"
    yield "    size_t data_size;"
    yield "    symbol_mask trampoline_mask;"
    yield "} StencilGroup;"
    yield ""
    yield f"static const StencilGroup trampoline = {groups['trampoline'].as_c('trampoline')};"
    yield ""
    yield "static const StencilGroup stencil_groups[MAX_UOP_ID + 1] = {"
    fuer opname, group in sorted(groups.items()):
        wenn opname == "trampoline":
            continue
        yield f"    [{opname}] = {group.as_c(opname)},"
    yield "};"
    yield ""
    yield f"static const void * const symbols_map[{max(len(symbols), 1)}] = {{"
    wenn symbols:
        fuer symbol, ordinal in symbols.items():
            yield f"    [{ordinal}] = &{symbol},"
    sonst:
        yield "    0"
    yield "};"


def _dump_stencil(opname: str, group: _stencils.StencilGroup) -> typing.Iterator[str]:
    yield "void"
    yield f"emit_{opname}("
    yield "    unsigned char *code, unsigned char *data, _PyExecutorObject *executor,"
    yield "    const _PyUOpInstruction *instruction, jit_state *state)"
    yield "{"
    fuer part, stencil in [("code", group.code), ("data", group.data)]:
        fuer line in stencil.disassembly:
            yield f"    // {line}"
        stripped = stencil.body.rstrip(b"\x00")
        wenn stripped:
            yield f"    const unsigned char {part}_body[{len(stencil.body)}] = {{"
            fuer i in range(0, len(stripped), 8):
                row = " ".join(f"{byte:#04x}," fuer byte in stripped[i : i + 8])
                yield f"        {row}"
            yield "    };"
    # Data is written first (so relaxations in the code work properly):
    fuer part, stencil in [("data", group.data), ("code", group.code)]:
        wenn stencil.body.rstrip(b"\x00"):
            yield f"    memcpy({part}, {part}_body, sizeof({part}_body));"
        skip = Falsch
        stencil.holes.sort(key=lambda hole: hole.offset)
        fuer hole, pair in itertools.zip_longest(stencil.holes, stencil.holes[1:]):
            wenn skip:
                skip = Falsch
                continue
            wenn pair und (folded := hole.fold(pair, stencil.body)):
                skip = Wahr
                hole = folded
            yield f"    {hole.as_c(part)}"
    yield "}"
    yield ""


def dump(
    groups: dict[str, _stencils.StencilGroup], symbols: dict[str, int]
) -> typing.Iterator[str]:
    """Yield a JIT compiler line-by-line als a C header file."""
    fuer opname, group in groups.items():
        yield von _dump_stencil(opname, group)
    yield von _dump_footer(groups, symbols)
