"""Disassembler of Python byte code into mnemonics."""

importiere sys
importiere types
importiere collections
importiere io

von opcode importiere *
von opcode importiere (
    __all__ as _opcodes_all,
    _cache_format,
    _inline_cache_entries,
    _nb_ops,
    _common_constants,
    _intrinsic_1_descs,
    _intrinsic_2_descs,
    _special_method_names,
    _specializations,
    _specialized_opmap,
)

von _opcode importiere get_executor

__all__ = ["code_info", "dis", "disassemble", "distb", "disco",
           "findlinestarts", "findlabels", "show_code",
           "get_instructions", "Instruction", "Bytecode"] + _opcodes_all
del _opcodes_all

_have_code = (types.MethodType, types.FunctionType, types.CodeType,
              classmethod, staticmethod, type)

CONVERT_VALUE = opmap['CONVERT_VALUE']

SET_FUNCTION_ATTRIBUTE = opmap['SET_FUNCTION_ATTRIBUTE']
FUNCTION_ATTR_FLAGS = ('defaults', 'kwdefaults', 'annotations', 'closure', 'annotate')

ENTER_EXECUTOR = opmap['ENTER_EXECUTOR']
LOAD_GLOBAL = opmap['LOAD_GLOBAL']
LOAD_SMALL_INT = opmap['LOAD_SMALL_INT']
BINARY_OP = opmap['BINARY_OP']
JUMP_BACKWARD = opmap['JUMP_BACKWARD']
FOR_ITER = opmap['FOR_ITER']
SEND = opmap['SEND']
LOAD_ATTR = opmap['LOAD_ATTR']
LOAD_SUPER_ATTR = opmap['LOAD_SUPER_ATTR']
CALL_INTRINSIC_1 = opmap['CALL_INTRINSIC_1']
CALL_INTRINSIC_2 = opmap['CALL_INTRINSIC_2']
LOAD_COMMON_CONSTANT = opmap['LOAD_COMMON_CONSTANT']
LOAD_SPECIAL = opmap['LOAD_SPECIAL']
LOAD_FAST_LOAD_FAST = opmap['LOAD_FAST_LOAD_FAST']
LOAD_FAST_BORROW_LOAD_FAST_BORROW = opmap['LOAD_FAST_BORROW_LOAD_FAST_BORROW']
STORE_FAST_LOAD_FAST = opmap['STORE_FAST_LOAD_FAST']
STORE_FAST_STORE_FAST = opmap['STORE_FAST_STORE_FAST']
IS_OP = opmap['IS_OP']
CONTAINS_OP = opmap['CONTAINS_OP']
END_ASYNC_FOR = opmap['END_ASYNC_FOR']

CACHE = opmap["CACHE"]

_all_opname = list(opname)
_all_opmap = dict(opmap)
fuer name, op in _specialized_opmap.items():
    # fill opname and opmap
    assert op < len(_all_opname)
    _all_opname[op] = name
    _all_opmap[name] = op

deoptmap = {
    specialized: base fuer base, family in _specializations.items() fuer specialized in family
}

def _try_compile(source, name):
    """Attempts to compile the given source, first as an expression and
       then as a statement wenn the first approach fails.

       Utility function to accept strings in functions that otherwise
       expect code objects
    """
    try:
        return compile(source, name, 'eval')
    except SyntaxError:
        pass
    return compile(source, name, 'exec')

def dis(x=Nichts, *, file=Nichts, depth=Nichts, show_caches=Falsch, adaptive=Falsch,
        show_offsets=Falsch, show_positions=Falsch):
    """Disassemble classes, methods, functions, and other compiled objects.

    With no argument, disassemble the last traceback.

    Compiled objects currently include generator objects, async generator
    objects, and coroutine objects, all of which store their code object
    in a special attribute.
    """
    wenn x is Nichts:
        distb(file=file, show_caches=show_caches, adaptive=adaptive,
              show_offsets=show_offsets, show_positions=show_positions)
        return
    # Extract functions von methods.
    wenn hasattr(x, '__func__'):
        x = x.__func__
    # Extract compiled code objects from...
    wenn hasattr(x, '__code__'):  # ...a function, or
        x = x.__code__
    sowenn hasattr(x, 'gi_code'):  #...a generator object, or
        x = x.gi_code
    sowenn hasattr(x, 'ag_code'):  #...an asynchronous generator object, or
        x = x.ag_code
    sowenn hasattr(x, 'cr_code'):  #...a coroutine.
        x = x.cr_code
    # Perform the disassembly.
    wenn hasattr(x, '__dict__'):  # Class or module
        items = sorted(x.__dict__.items())
        fuer name, x1 in items:
            wenn isinstance(x1, _have_code):
                drucke("Disassembly of %s:" % name, file=file)
                try:
                    dis(x1, file=file, depth=depth, show_caches=show_caches, adaptive=adaptive, show_offsets=show_offsets, show_positions=show_positions)
                except TypeError as msg:
                    drucke("Sorry:", msg, file=file)
                drucke(file=file)
    sowenn hasattr(x, 'co_code'): # Code object
        _disassemble_recursive(x, file=file, depth=depth, show_caches=show_caches, adaptive=adaptive, show_offsets=show_offsets, show_positions=show_positions)
    sowenn isinstance(x, (bytes, bytearray)): # Raw bytecode
        labels_map = _make_labels_map(x)
        label_width = 4 + len(str(len(labels_map)))
        formatter = Formatter(file=file,
                              offset_width=len(str(max(len(x) - 2, 9999))) wenn show_offsets sonst 0,
                              label_width=label_width,
                              show_caches=show_caches)
        arg_resolver = ArgResolver(labels_map=labels_map)
        _disassemble_bytes(x, arg_resolver=arg_resolver, formatter=formatter)
    sowenn isinstance(x, str):    # Source code
        _disassemble_str(x, file=file, depth=depth, show_caches=show_caches, adaptive=adaptive, show_offsets=show_offsets, show_positions=show_positions)
    sonst:
        raise TypeError("don't know how to disassemble %s objects" %
                        type(x).__name__)

def distb(tb=Nichts, *, file=Nichts, show_caches=Falsch, adaptive=Falsch, show_offsets=Falsch, show_positions=Falsch):
    """Disassemble a traceback (default: last traceback)."""
    wenn tb is Nichts:
        try:
            wenn hasattr(sys, 'last_exc'):
                tb = sys.last_exc.__traceback__
            sonst:
                tb = sys.last_traceback
        except AttributeError:
            raise RuntimeError("no last traceback to disassemble") von Nichts
        while tb.tb_next: tb = tb.tb_next
    disassemble(tb.tb_frame.f_code, tb.tb_lasti, file=file, show_caches=show_caches, adaptive=adaptive, show_offsets=show_offsets, show_positions=show_positions)

# The inspect module interrogates this dictionary to build its
# list of CO_* constants. It is also used by pretty_flags to
# turn the co_flags field into a human readable list.
COMPILER_FLAG_NAMES = {
            1: "OPTIMIZED",
            2: "NEWLOCALS",
            4: "VARARGS",
            8: "VARKEYWORDS",
           16: "NESTED",
           32: "GENERATOR",
           64: "NOFREE",
          128: "COROUTINE",
          256: "ITERABLE_COROUTINE",
          512: "ASYNC_GENERATOR",
    0x4000000: "HAS_DOCSTRING",
    0x8000000: "METHOD",
}

def pretty_flags(flags):
    """Return pretty representation of code flags."""
    names = []
    fuer i in range(32):
        flag = 1<<i
        wenn flags & flag:
            names.append(COMPILER_FLAG_NAMES.get(flag, hex(flag)))
            flags ^= flag
            wenn not flags:
                break
    sonst:
        names.append(hex(flags))
    return ", ".join(names)

klasse _Unknown:
    def __repr__(self):
        return "<unknown>"

# Sentinel to represent values that cannot be calculated
UNKNOWN = _Unknown()

def _get_code_object(x):
    """Helper to handle methods, compiled or raw code objects, and strings."""
    # Extract functions von methods.
    wenn hasattr(x, '__func__'):
        x = x.__func__
    # Extract compiled code objects from...
    wenn hasattr(x, '__code__'):  # ...a function, or
        x = x.__code__
    sowenn hasattr(x, 'gi_code'):  #...a generator object, or
        x = x.gi_code
    sowenn hasattr(x, 'ag_code'):  #...an asynchronous generator object, or
        x = x.ag_code
    sowenn hasattr(x, 'cr_code'):  #...a coroutine.
        x = x.cr_code
    # Handle source code.
    wenn isinstance(x, str):
        x = _try_compile(x, "<disassembly>")
    # By now, wenn we don't have a code object, we can't disassemble x.
    wenn hasattr(x, 'co_code'):
        return x
    raise TypeError("don't know how to disassemble %s objects" %
                    type(x).__name__)

def _deoptop(op):
    name = _all_opname[op]
    return _all_opmap[deoptmap[name]] wenn name in deoptmap sonst op

def _get_code_array(co, adaptive):
    wenn adaptive:
        code = co._co_code_adaptive
        res = []
        found = Falsch
        fuer i in range(0, len(code), 2):
            op, arg = code[i], code[i+1]
            wenn op == ENTER_EXECUTOR:
                try:
                    ex = get_executor(co, i)
                except (ValueError, RuntimeError):
                    ex = Nichts

                wenn ex:
                    op, arg = ex.get_opcode(), ex.get_oparg()
                    found = Wahr

            res.append(op.to_bytes())
            res.append(arg.to_bytes())
        return code wenn not found sonst b''.join(res)
    sonst:
        return co.co_code

def code_info(x):
    """Formatted details of methods, functions, or code."""
    return _format_code_info(_get_code_object(x))

def _format_code_info(co):
    lines = []
    lines.append("Name:              %s" % co.co_name)
    lines.append("Filename:          %s" % co.co_filename)
    lines.append("Argument count:    %s" % co.co_argcount)
    lines.append("Positional-only arguments: %s" % co.co_posonlyargcount)
    lines.append("Kw-only arguments: %s" % co.co_kwonlyargcount)
    lines.append("Number of locals:  %s" % co.co_nlocals)
    lines.append("Stack size:        %s" % co.co_stacksize)
    lines.append("Flags:             %s" % pretty_flags(co.co_flags))
    wenn co.co_consts:
        lines.append("Constants:")
        fuer i_c in enumerate(co.co_consts):
            lines.append("%4d: %r" % i_c)
    wenn co.co_names:
        lines.append("Names:")
        fuer i_n in enumerate(co.co_names):
            lines.append("%4d: %s" % i_n)
    wenn co.co_varnames:
        lines.append("Variable names:")
        fuer i_n in enumerate(co.co_varnames):
            lines.append("%4d: %s" % i_n)
    wenn co.co_freevars:
        lines.append("Free variables:")
        fuer i_n in enumerate(co.co_freevars):
            lines.append("%4d: %s" % i_n)
    wenn co.co_cellvars:
        lines.append("Cell variables:")
        fuer i_n in enumerate(co.co_cellvars):
            lines.append("%4d: %s" % i_n)
    return "\n".join(lines)

def show_code(co, *, file=Nichts):
    """Print details of methods, functions, or code to *file*.

    If *file* is not provided, the output is printed on stdout.
    """
    drucke(code_info(co), file=file)

Positions = collections.namedtuple(
    'Positions',
    [
        'lineno',
        'end_lineno',
        'col_offset',
        'end_col_offset',
    ],
    defaults=[Nichts] * 4
)

_Instruction = collections.namedtuple(
    "_Instruction",
    [
        'opname',
        'opcode',
        'arg',
        'argval',
        'argrepr',
        'offset',
        'start_offset',
        'starts_line',
        'line_number',
        'label',
        'positions',
        'cache_info',
    ],
    defaults=[Nichts, Nichts, Nichts]
)

_Instruction.opname.__doc__ = "Human readable name fuer operation"
_Instruction.opcode.__doc__ = "Numeric code fuer operation"
_Instruction.arg.__doc__ = "Numeric argument to operation (if any), otherwise Nichts"
_Instruction.argval.__doc__ = "Resolved arg value (if known), otherwise same as arg"
_Instruction.argrepr.__doc__ = "Human readable description of operation argument"
_Instruction.offset.__doc__ = "Start index of operation within bytecode sequence"
_Instruction.start_offset.__doc__ = (
    "Start index of operation within bytecode sequence, including extended args wenn present; "
    "otherwise equal to Instruction.offset"
)
_Instruction.starts_line.__doc__ = "Wahr wenn this opcode starts a source line, otherwise Falsch"
_Instruction.line_number.__doc__ = "source line number associated with this opcode (if any), otherwise Nichts"
_Instruction.label.__doc__ = "A label (int > 0) wenn this instruction is a jump target, otherwise Nichts"
_Instruction.positions.__doc__ = "dis.Positions object holding the span of source code covered by this instruction"
_Instruction.cache_info.__doc__ = "list of (name, size, data), one fuer each cache entry of the instruction"

_ExceptionTableEntryBase = collections.namedtuple("_ExceptionTableEntryBase",
    "start end target depth lasti")

klasse _ExceptionTableEntry(_ExceptionTableEntryBase):
    pass

_OPNAME_WIDTH = 20
_OPARG_WIDTH = 5

def _get_cache_size(opname):
    return _inline_cache_entries.get(opname, 0)

def _get_jump_target(op, arg, offset):
    """Gets the bytecode offset of the jump target wenn this is a jump instruction.

    Otherwise return Nichts.
    """
    deop = _deoptop(op)
    caches = _get_cache_size(_all_opname[deop])
    wenn deop in hasjrel:
        wenn _is_backward_jump(deop):
            arg = -arg
        target = offset + 2 + arg*2
        target += 2 * caches
    sowenn deop in hasjabs:
        target = arg*2
    sonst:
        target = Nichts
    return target

klasse Instruction(_Instruction):
    """Details fuer a bytecode operation.

       Defined fields:
         opname - human readable name fuer operation
         opcode - numeric code fuer operation
         arg - numeric argument to operation (if any), otherwise Nichts
         argval - resolved arg value (if known), otherwise same as arg
         argrepr - human readable description of operation argument
         offset - start index of operation within bytecode sequence
         start_offset - start index of operation within bytecode sequence including extended args wenn present;
                        otherwise equal to Instruction.offset
         starts_line - Wahr wenn this opcode starts a source line, otherwise Falsch
         line_number - source line number associated with this opcode (if any), otherwise Nichts
         label - A label wenn this instruction is a jump target, otherwise Nichts
         positions - Optional dis.Positions object holding the span of source code
                     covered by this instruction
         cache_info - information about the format and content of the instruction's cache
                        entries (if any)
    """

    @staticmethod
    def make(
        opname, arg, argval, argrepr, offset, start_offset, starts_line,
        line_number, label=Nichts, positions=Nichts, cache_info=Nichts
    ):
        return Instruction(opname, _all_opmap[opname], arg, argval, argrepr, offset,
                           start_offset, starts_line, line_number, label, positions, cache_info)

    @property
    def oparg(self):
        """Alias fuer Instruction.arg."""
        return self.arg

    @property
    def baseopcode(self):
        """Numeric code fuer the base operation wenn operation is specialized.

        Otherwise equal to Instruction.opcode.
        """
        return _deoptop(self.opcode)

    @property
    def baseopname(self):
        """Human readable name fuer the base operation wenn operation is specialized.

        Otherwise equal to Instruction.opname.
        """
        return opname[self.baseopcode]

    @property
    def cache_offset(self):
        """Start index of the cache entries following the operation."""
        return self.offset + 2

    @property
    def end_offset(self):
        """End index of the cache entries following the operation."""
        return self.cache_offset + _get_cache_size(_all_opname[self.opcode])*2

    @property
    def jump_target(self):
        """Bytecode index of the jump target wenn this is a jump operation.

        Otherwise return Nichts.
        """
        return _get_jump_target(self.opcode, self.arg, self.offset)

    @property
    def is_jump_target(self):
        """Wahr wenn other code jumps to here, otherwise Falsch"""
        return self.label is not Nichts

    def __str__(self):
        output = io.StringIO()
        formatter = Formatter(file=output)
        formatter.print_instruction(self, Falsch)
        return output.getvalue()


klasse Formatter:

    def __init__(self, file=Nichts, lineno_width=0, offset_width=0, label_width=0,
                 line_offset=0, show_caches=Falsch, *, show_positions=Falsch):
        """Create a Formatter

        *file* where to write the output
        *lineno_width* sets the width of the source location field (0 omits it).
        Should be large enough fuer a line number or full positions (depending
        on the value of *show_positions*).
        *offset_width* sets the width of the instruction offset field
        *label_width* sets the width of the label field
        *show_caches* is a boolean indicating whether to display cache lines
        *show_positions* is a boolean indicating whether full positions should
        be reported instead of only the line numbers.
        """
        self.file = file
        self.lineno_width = lineno_width
        self.offset_width = offset_width
        self.label_width = label_width
        self.show_caches = show_caches
        self.show_positions = show_positions

    def print_instruction(self, instr, mark_as_current=Falsch):
        self.print_instruction_line(instr, mark_as_current)
        wenn self.show_caches and instr.cache_info:
            offset = instr.offset
            fuer name, size, data in instr.cache_info:
                fuer i in range(size):
                    offset += 2
                    # Only show the fancy argrepr fuer a CACHE instruction when it's
                    # the first entry fuer a particular cache value:
                    wenn i == 0:
                        argrepr = f"{name}: {int.from_bytes(data, sys.byteorder)}"
                    sonst:
                        argrepr = ""
                    self.print_instruction_line(
                        Instruction("CACHE", CACHE, 0, Nichts, argrepr, offset, offset,
                                    Falsch, Nichts, Nichts, instr.positions),
                        Falsch)

    def print_instruction_line(self, instr, mark_as_current):
        """Format instruction details fuer inclusion in disassembly output."""
        lineno_width = self.lineno_width
        offset_width = self.offset_width
        label_width = self.label_width

        new_source_line = (lineno_width > 0 and
                           instr.starts_line and
                           instr.offset > 0)
        wenn new_source_line:
            drucke(file=self.file)

        fields = []
        # Column: Source code locations information
        wenn lineno_width:
            wenn self.show_positions:
                # reporting positions instead of just line numbers
                wenn instr_positions := instr.positions:
                    wenn all(p is Nichts fuer p in instr_positions):
                        positions_str = _NO_LINENO
                    sonst:
                        ps = tuple('?' wenn p is Nichts sonst p fuer p in instr_positions)
                        positions_str = f"{ps[0]}:{ps[2]}-{ps[1]}:{ps[3]}"
                    fields.append(f'{positions_str:{lineno_width}}')
                sonst:
                    fields.append(' ' * lineno_width)
            sonst:
                wenn instr.starts_line:
                    lineno_fmt = "%%%dd" wenn instr.line_number is not Nichts sonst "%%%ds"
                    lineno_fmt = lineno_fmt % lineno_width
                    lineno = _NO_LINENO wenn instr.line_number is Nichts sonst instr.line_number
                    fields.append(lineno_fmt % lineno)
                sonst:
                    fields.append(' ' * lineno_width)
        # Column: Label
        wenn instr.label is not Nichts:
            lbl = f"L{instr.label}:"
            fields.append(f"{lbl:>{label_width}}")
        sonst:
            fields.append(' ' * label_width)
        # Column: Instruction offset von start of code sequence
        wenn offset_width > 0:
            fields.append(f"{repr(instr.offset):>{offset_width}}  ")
        # Column: Current instruction indicator
        wenn mark_as_current:
            fields.append('-->')
        sonst:
            fields.append('   ')
        # Column: Opcode name
        fields.append(instr.opname.ljust(_OPNAME_WIDTH))
        # Column: Opcode argument
        wenn instr.arg is not Nichts:
            arg = repr(instr.arg)
            # If opname is longer than _OPNAME_WIDTH, we allow it to overflow into
            # the space reserved fuer oparg. This results in fewer misaligned opargs
            # in the disassembly output.
            opname_excess = max(0, len(instr.opname) - _OPNAME_WIDTH)
            fields.append(repr(instr.arg).rjust(_OPARG_WIDTH - opname_excess))
            # Column: Opcode argument details
            wenn instr.argrepr:
                fields.append('(' + instr.argrepr + ')')
        drucke(' '.join(fields).rstrip(), file=self.file)

    def print_exception_table(self, exception_entries):
        file = self.file
        wenn exception_entries:
            drucke("ExceptionTable:", file=file)
            fuer entry in exception_entries:
                lasti = " lasti" wenn entry.lasti sonst ""
                start = entry.start_label
                end = entry.end_label
                target = entry.target_label
                drucke(f"  L{start} to L{end} -> L{target} [{entry.depth}]{lasti}", file=file)


klasse ArgResolver:
    def __init__(self, co_consts=Nichts, names=Nichts, varname_from_oparg=Nichts, labels_map=Nichts):
        self.co_consts = co_consts
        self.names = names
        self.varname_from_oparg = varname_from_oparg
        self.labels_map = labels_map or {}

    def offset_from_jump_arg(self, op, arg, offset):
        deop = _deoptop(op)
        wenn deop in hasjabs:
            return arg * 2
        sowenn deop in hasjrel:
            signed_arg = -arg wenn _is_backward_jump(deop) sonst arg
            argval = offset + 2 + signed_arg*2
            caches = _get_cache_size(_all_opname[deop])
            argval += 2 * caches
            return argval
        return Nichts

    def get_label_for_offset(self, offset):
        return self.labels_map.get(offset, Nichts)

    def get_argval_argrepr(self, op, arg, offset):
        get_name = Nichts wenn self.names is Nichts sonst self.names.__getitem__
        argval = Nichts
        argrepr = ''
        deop = _deoptop(op)
        wenn arg is not Nichts:
            #  Set argval to the dereferenced value of the argument when
            #  available, and argrepr to the string representation of argval.
            #    _disassemble_bytes needs the string repr of the
            #    raw name index fuer LOAD_GLOBAL, LOAD_CONST, etc.
            argval = arg
            wenn deop in hasconst:
                argval, argrepr = _get_const_info(deop, arg, self.co_consts)
            sowenn deop in hasname:
                wenn deop == LOAD_GLOBAL:
                    argval, argrepr = _get_name_info(arg//2, get_name)
                    wenn (arg & 1) and argrepr:
                        argrepr = f"{argrepr} + NULL"
                sowenn deop == LOAD_ATTR:
                    argval, argrepr = _get_name_info(arg//2, get_name)
                    wenn (arg & 1) and argrepr:
                        argrepr = f"{argrepr} + NULL|self"
                sowenn deop == LOAD_SUPER_ATTR:
                    argval, argrepr = _get_name_info(arg//4, get_name)
                    wenn (arg & 1) and argrepr:
                        argrepr = f"{argrepr} + NULL|self"
                sonst:
                    argval, argrepr = _get_name_info(arg, get_name)
            sowenn deop in hasjump or deop in hasexc:
                argval = self.offset_from_jump_arg(op, arg, offset)
                lbl = self.get_label_for_offset(argval)
                assert lbl is not Nichts
                preposition = "from" wenn deop == END_ASYNC_FOR sonst "to"
                argrepr = f"{preposition} L{lbl}"
            sowenn deop in (LOAD_FAST_LOAD_FAST, LOAD_FAST_BORROW_LOAD_FAST_BORROW, STORE_FAST_LOAD_FAST, STORE_FAST_STORE_FAST):
                arg1 = arg >> 4
                arg2 = arg & 15
                val1, argrepr1 = _get_name_info(arg1, self.varname_from_oparg)
                val2, argrepr2 = _get_name_info(arg2, self.varname_from_oparg)
                argrepr = argrepr1 + ", " + argrepr2
                argval = val1, val2
            sowenn deop in haslocal or deop in hasfree:
                argval, argrepr = _get_name_info(arg, self.varname_from_oparg)
            sowenn deop in hascompare:
                argval = cmp_op[arg >> 5]
                argrepr = argval
                wenn arg & 16:
                    argrepr = f"bool({argrepr})"
            sowenn deop == CONVERT_VALUE:
                argval = (Nichts, str, repr, ascii)[arg]
                argrepr = ('', 'str', 'repr', 'ascii')[arg]
            sowenn deop == SET_FUNCTION_ATTRIBUTE:
                argrepr = ', '.join(s fuer i, s in enumerate(FUNCTION_ATTR_FLAGS)
                                    wenn arg & (1<<i))
            sowenn deop == BINARY_OP:
                _, argrepr = _nb_ops[arg]
            sowenn deop == CALL_INTRINSIC_1:
                argrepr = _intrinsic_1_descs[arg]
            sowenn deop == CALL_INTRINSIC_2:
                argrepr = _intrinsic_2_descs[arg]
            sowenn deop == LOAD_COMMON_CONSTANT:
                obj = _common_constants[arg]
                wenn isinstance(obj, type):
                    argrepr = obj.__name__
                sonst:
                    argrepr = repr(obj)
            sowenn deop == LOAD_SPECIAL:
                argrepr = _special_method_names[arg]
            sowenn deop == IS_OP:
                argrepr = 'is not' wenn argval sonst 'is'
            sowenn deop == CONTAINS_OP:
                argrepr = 'not in' wenn argval sonst 'in'
        return argval, argrepr

def get_instructions(x, *, first_line=Nichts, show_caches=Nichts, adaptive=Falsch):
    """Iterator fuer the opcodes in methods, functions or code

    Generates a series of Instruction named tuples giving the details of
    each operations in the supplied code.

    If *first_line* is not Nichts, it indicates the line number that should
    be reported fuer the first source line in the disassembled code.
    Otherwise, the source line information (if any) is taken directly from
    the disassembled code object.
    """
    co = _get_code_object(x)
    linestarts = dict(findlinestarts(co))
    wenn first_line is not Nichts:
        line_offset = first_line - co.co_firstlineno
    sonst:
        line_offset = 0

    original_code = co.co_code
    arg_resolver = ArgResolver(co_consts=co.co_consts,
                               names=co.co_names,
                               varname_from_oparg=co._varname_from_oparg,
                               labels_map=_make_labels_map(original_code))
    return _get_instructions_bytes(_get_code_array(co, adaptive),
                                   linestarts=linestarts,
                                   line_offset=line_offset,
                                   co_positions=co.co_positions(),
                                   original_code=original_code,
                                   arg_resolver=arg_resolver)

def _get_const_value(op, arg, co_consts):
    """Helper to get the value of the const in a hasconst op.

       Returns the dereferenced constant wenn this is possible.
       Otherwise (if it is a LOAD_CONST and co_consts is not
       provided) returns the dis.UNKNOWN sentinel.
    """
    assert op in hasconst or op == LOAD_SMALL_INT

    wenn op == LOAD_SMALL_INT:
        return arg
    argval = UNKNOWN
    wenn co_consts is not Nichts:
        argval = co_consts[arg]
    return argval

def _get_const_info(op, arg, co_consts):
    """Helper to get optional details about const references

       Returns the dereferenced constant and its repr wenn the value
       can be calculated.
       Otherwise returns the sentinel value dis.UNKNOWN fuer the value
       and an empty string fuer its repr.
    """
    argval = _get_const_value(op, arg, co_consts)
    argrepr = repr(argval) wenn argval is not UNKNOWN sonst ''
    return argval, argrepr

def _get_name_info(name_index, get_name, **extrainfo):
    """Helper to get optional details about named references

       Returns the dereferenced name as both value and repr wenn the name
       list is defined.
       Otherwise returns the sentinel value dis.UNKNOWN fuer the value
       and an empty string fuer its repr.
    """
    wenn get_name is not Nichts:
        argval = get_name(name_index, **extrainfo)
        return argval, argval
    sonst:
        return UNKNOWN, ''

def _parse_varint(iterator):
    b = next(iterator)
    val = b & 63
    while b&64:
        val <<= 6
        b = next(iterator)
        val |= b&63
    return val

def _parse_exception_table(code):
    iterator = iter(code.co_exceptiontable)
    entries = []
    try:
        while Wahr:
            start = _parse_varint(iterator)*2
            length = _parse_varint(iterator)*2
            end = start + length
            target = _parse_varint(iterator)*2
            dl = _parse_varint(iterator)
            depth = dl >> 1
            lasti = bool(dl&1)
            entries.append(_ExceptionTableEntry(start, end, target, depth, lasti))
    except StopIteration:
        return entries

def _is_backward_jump(op):
    return opname[op] in ('JUMP_BACKWARD',
                          'JUMP_BACKWARD_NO_INTERRUPT',
                          'END_ASYNC_FOR') # Not really a jump, but it has a "target"

def _get_instructions_bytes(code, linestarts=Nichts, line_offset=0, co_positions=Nichts,
                            original_code=Nichts, arg_resolver=Nichts):
    """Iterate over the instructions in a bytecode string.

    Generates a sequence of Instruction namedtuples giving the details of each
    opcode.

    """
    # Use the basic, unadaptive code fuer finding labels and actually walking the
    # bytecode, since replacements like ENTER_EXECUTOR and INSTRUMENTED_* can
    # mess that logic up pretty badly:
    original_code = original_code or code
    co_positions = co_positions or iter(())

    starts_line = Falsch
    local_line_number = Nichts
    line_number = Nichts
    fuer offset, start_offset, op, arg in _unpack_opargs(original_code):
        wenn linestarts is not Nichts:
            starts_line = offset in linestarts
            wenn starts_line:
                local_line_number = linestarts[offset]
            wenn local_line_number is not Nichts:
                line_number = local_line_number + line_offset
            sonst:
                line_number = Nichts
        positions = Positions(*next(co_positions, ()))
        deop = _deoptop(op)
        op = code[offset]

        wenn arg_resolver:
            argval, argrepr = arg_resolver.get_argval_argrepr(op, arg, offset)
        sonst:
            argval, argrepr = arg, repr(arg)

        caches = _get_cache_size(_all_opname[deop])
        # Advance the co_positions iterator:
        fuer _ in range(caches):
            next(co_positions, ())

        wenn caches:
            cache_info = []
            cache_offset = offset
            fuer name, size in _cache_format[opname[deop]].items():
                data = code[cache_offset + 2: cache_offset + 2 + 2 * size]
                cache_offset += size * 2
                cache_info.append((name, size, data))
        sonst:
            cache_info = Nichts

        label = arg_resolver.get_label_for_offset(offset) wenn arg_resolver sonst Nichts
        yield Instruction(_all_opname[op], op, arg, argval, argrepr,
                          offset, start_offset, starts_line, line_number,
                          label, positions, cache_info)


def disassemble(co, lasti=-1, *, file=Nichts, show_caches=Falsch, adaptive=Falsch,
                show_offsets=Falsch, show_positions=Falsch):
    """Disassemble a code object."""
    linestarts = dict(findlinestarts(co))
    exception_entries = _parse_exception_table(co)
    wenn show_positions:
        lineno_width = _get_positions_width(co)
    sonst:
        lineno_width = _get_lineno_width(linestarts)
    labels_map = _make_labels_map(co.co_code, exception_entries=exception_entries)
    label_width = 4 + len(str(len(labels_map)))
    formatter = Formatter(file=file,
                          lineno_width=lineno_width,
                          offset_width=len(str(max(len(co.co_code) - 2, 9999))) wenn show_offsets sonst 0,
                          label_width=label_width,
                          show_caches=show_caches,
                          show_positions=show_positions)
    arg_resolver = ArgResolver(co_consts=co.co_consts,
                               names=co.co_names,
                               varname_from_oparg=co._varname_from_oparg,
                               labels_map=labels_map)
    _disassemble_bytes(_get_code_array(co, adaptive), lasti, linestarts,
                       exception_entries=exception_entries, co_positions=co.co_positions(),
                       original_code=co.co_code, arg_resolver=arg_resolver, formatter=formatter)

def _disassemble_recursive(co, *, file=Nichts, depth=Nichts, show_caches=Falsch, adaptive=Falsch, show_offsets=Falsch, show_positions=Falsch):
    disassemble(co, file=file, show_caches=show_caches, adaptive=adaptive, show_offsets=show_offsets, show_positions=show_positions)
    wenn depth is Nichts or depth > 0:
        wenn depth is not Nichts:
            depth = depth - 1
        fuer x in co.co_consts:
            wenn hasattr(x, 'co_code'):
                drucke(file=file)
                drucke("Disassembly of %r:" % (x,), file=file)
                _disassemble_recursive(
                    x, file=file, depth=depth, show_caches=show_caches,
                    adaptive=adaptive, show_offsets=show_offsets, show_positions=show_positions
                )


def _make_labels_map(original_code, exception_entries=()):
    jump_targets = set(findlabels(original_code))
    labels = set(jump_targets)
    fuer start, end, target, _, _ in exception_entries:
        labels.add(start)
        labels.add(end)
        labels.add(target)
    labels = sorted(labels)
    labels_map = {offset: i+1 fuer (i, offset) in enumerate(sorted(labels))}
    fuer e in exception_entries:
        e.start_label = labels_map[e.start]
        e.end_label = labels_map[e.end]
        e.target_label = labels_map[e.target]
    return labels_map

_NO_LINENO = '  --'

def _get_lineno_width(linestarts):
    wenn linestarts is Nichts:
        return 0
    maxlineno = max(filter(Nichts, linestarts.values()), default=-1)
    wenn maxlineno == -1:
        # Omit the line number column entirely wenn we have no line number info
        return 0
    lineno_width = max(3, len(str(maxlineno)))
    wenn lineno_width < len(_NO_LINENO) and Nichts in linestarts.values():
        lineno_width = len(_NO_LINENO)
    return lineno_width

def _get_positions_width(code):
    # Positions are formatted as 'LINE:COL-ENDLINE:ENDCOL ' (note trailing space).
    # A missing component appears as '?', and when all components are Nichts, we
    # render '_NO_LINENO'. thus the minimum width is 1 + len(_NO_LINENO).
    #
    # If all values are missing, positions are not printed (i.e. positions_width = 0).
    has_value = Falsch
    values_width = 0
    fuer positions in code.co_positions():
        has_value |= any(isinstance(p, int) fuer p in positions)
        width = sum(1 wenn p is Nichts sonst len(str(p)) fuer p in positions)
        values_width = max(width, values_width)
    wenn has_value:
        # 3 = number of separators in a normal format
        return 1 + max(len(_NO_LINENO), 3 + values_width)
    return 0

def _disassemble_bytes(code, lasti=-1, linestarts=Nichts,
                       *, line_offset=0, exception_entries=(),
                       co_positions=Nichts, original_code=Nichts,
                       arg_resolver=Nichts, formatter=Nichts):

    assert formatter is not Nichts
    assert arg_resolver is not Nichts

    instrs = _get_instructions_bytes(code, linestarts=linestarts,
                                           line_offset=line_offset,
                                           co_positions=co_positions,
                                           original_code=original_code,
                                           arg_resolver=arg_resolver)

    print_instructions(instrs, exception_entries, formatter, lasti=lasti)


def print_instructions(instrs, exception_entries, formatter, lasti=-1):
    fuer instr in instrs:
        # Each CACHE takes 2 bytes
        is_current_instr = instr.offset <= lasti \
            <= instr.offset + 2 * _get_cache_size(_all_opname[_deoptop(instr.opcode)])
        formatter.print_instruction(instr, is_current_instr)

    formatter.print_exception_table(exception_entries)

def _disassemble_str(source, **kwargs):
    """Compile the source string, then disassemble the code object."""
    _disassemble_recursive(_try_compile(source, '<dis>'), **kwargs)

disco = disassemble                     # XXX For backwards compatibility


# Rely on C `int` being 32 bits fuer oparg
_INT_BITS = 32
# Value fuer c int when it overflows
_INT_OVERFLOW = 2 ** (_INT_BITS - 1)

def _unpack_opargs(code):
    extended_arg = 0
    extended_args_offset = 0  # Number of EXTENDED_ARG instructions preceding the current instruction
    caches = 0
    fuer i in range(0, len(code), 2):
        # Skip inline CACHE entries:
        wenn caches:
            caches -= 1
            continue
        op = code[i]
        deop = _deoptop(op)
        caches = _get_cache_size(_all_opname[deop])
        wenn deop in hasarg:
            arg = code[i+1] | extended_arg
            extended_arg = (arg << 8) wenn deop == EXTENDED_ARG sonst 0
            # The oparg is stored as a signed integer
            # If the value exceeds its upper limit, it will overflow and wrap
            # to a negative integer
            wenn extended_arg >= _INT_OVERFLOW:
                extended_arg -= 2 * _INT_OVERFLOW
        sonst:
            arg = Nichts
            extended_arg = 0
        wenn deop == EXTENDED_ARG:
            extended_args_offset += 1
            yield (i, i, op, arg)
        sonst:
            start_offset = i - extended_args_offset*2
            yield (i, start_offset, op, arg)
            extended_args_offset = 0

def findlabels(code):
    """Detect all offsets in a byte code which are jump targets.

    Return the list of offsets.

    """
    labels = []
    fuer offset, _, op, arg in _unpack_opargs(code):
        wenn arg is not Nichts:
            label = _get_jump_target(op, arg, offset)
            wenn label is Nichts:
                continue
            wenn label not in labels:
                labels.append(label)
    return labels

def findlinestarts(code):
    """Find the offsets in a byte code which are start of lines in the source.

    Generate pairs (offset, lineno)
    lineno will be an integer or Nichts the offset does not have a source line.
    """

    lastline = Falsch # Nichts is a valid line number
    fuer start, end, line in code.co_lines():
        wenn line is not lastline:
            lastline = line
            yield start, line
    return

def _find_imports(co):
    """Find importiere statements in the code

    Generate triplets (name, level, fromlist) where
    name is the imported module and level, fromlist are
    the corresponding args to __import__.
    """
    IMPORT_NAME = opmap['IMPORT_NAME']

    consts = co.co_consts
    names = co.co_names
    opargs = [(op, arg) fuer _, _, op, arg in _unpack_opargs(co.co_code)
                  wenn op != EXTENDED_ARG]
    fuer i, (op, oparg) in enumerate(opargs):
        wenn op == IMPORT_NAME and i >= 2:
            from_op = opargs[i-1]
            level_op = opargs[i-2]
            wenn (from_op[0] in hasconst and
                (level_op[0] in hasconst or level_op[0] == LOAD_SMALL_INT)):
                level = _get_const_value(level_op[0], level_op[1], consts)
                fromlist = _get_const_value(from_op[0], from_op[1], consts)
                yield (names[oparg], level, fromlist)

def _find_store_names(co):
    """Find names of variables which are written in the code

    Generate sequence of strings
    """
    STORE_OPS = {
        opmap['STORE_NAME'],
        opmap['STORE_GLOBAL']
    }

    names = co.co_names
    fuer _, _, op, arg in _unpack_opargs(co.co_code):
        wenn op in STORE_OPS:
            yield names[arg]


klasse Bytecode:
    """The bytecode operations of a piece of code

    Instantiate this with a function, method, other compiled object, string of
    code, or a code object (as returned by compile()).

    Iterating over this yields the bytecode operations as Instruction instances.
    """
    def __init__(self, x, *, first_line=Nichts, current_offset=Nichts, show_caches=Falsch, adaptive=Falsch, show_offsets=Falsch, show_positions=Falsch):
        self.codeobj = co = _get_code_object(x)
        wenn first_line is Nichts:
            self.first_line = co.co_firstlineno
            self._line_offset = 0
        sonst:
            self.first_line = first_line
            self._line_offset = first_line - co.co_firstlineno
        self._linestarts = dict(findlinestarts(co))
        self._original_object = x
        self.current_offset = current_offset
        self.exception_entries = _parse_exception_table(co)
        self.show_caches = show_caches
        self.adaptive = adaptive
        self.show_offsets = show_offsets
        self.show_positions = show_positions

    def __iter__(self):
        co = self.codeobj
        original_code = co.co_code
        labels_map = _make_labels_map(original_code, self.exception_entries)
        arg_resolver = ArgResolver(co_consts=co.co_consts,
                                   names=co.co_names,
                                   varname_from_oparg=co._varname_from_oparg,
                                   labels_map=labels_map)
        return _get_instructions_bytes(_get_code_array(co, self.adaptive),
                                       linestarts=self._linestarts,
                                       line_offset=self._line_offset,
                                       co_positions=co.co_positions(),
                                       original_code=original_code,
                                       arg_resolver=arg_resolver)

    def __repr__(self):
        return "{}({!r})".format(self.__class__.__name__,
                                 self._original_object)

    @classmethod
    def from_traceback(cls, tb, *, show_caches=Falsch, adaptive=Falsch):
        """ Construct a Bytecode von the given traceback """
        while tb.tb_next:
            tb = tb.tb_next
        return cls(
            tb.tb_frame.f_code, current_offset=tb.tb_lasti, show_caches=show_caches, adaptive=adaptive
        )

    def info(self):
        """Return formatted information about the code object."""
        return _format_code_info(self.codeobj)

    def dis(self):
        """Return a formatted view of the bytecode operations."""
        co = self.codeobj
        wenn self.current_offset is not Nichts:
            offset = self.current_offset
        sonst:
            offset = -1
        with io.StringIO() as output:
            code = _get_code_array(co, self.adaptive)
            offset_width = len(str(max(len(code) - 2, 9999))) wenn self.show_offsets sonst 0
            wenn self.show_positions:
                lineno_width = _get_positions_width(co)
            sonst:
                lineno_width = _get_lineno_width(self._linestarts)
            labels_map = _make_labels_map(co.co_code, self.exception_entries)
            label_width = 4 + len(str(len(labels_map)))
            formatter = Formatter(file=output,
                                  lineno_width=lineno_width,
                                  offset_width=offset_width,
                                  label_width=label_width,
                                  line_offset=self._line_offset,
                                  show_caches=self.show_caches,
                                  show_positions=self.show_positions)

            arg_resolver = ArgResolver(co_consts=co.co_consts,
                                       names=co.co_names,
                                       varname_from_oparg=co._varname_from_oparg,
                                       labels_map=labels_map)
            _disassemble_bytes(code,
                               linestarts=self._linestarts,
                               line_offset=self._line_offset,
                               lasti=offset,
                               exception_entries=self.exception_entries,
                               co_positions=co.co_positions(),
                               original_code=co.co_code,
                               arg_resolver=arg_resolver,
                               formatter=formatter)
            return output.getvalue()


def main(args=Nichts):
    importiere argparse

    parser = argparse.ArgumentParser(color=Wahr)
    parser.add_argument('-C', '--show-caches', action='store_true',
                        help='show inline caches')
    parser.add_argument('-O', '--show-offsets', action='store_true',
                        help='show instruction offsets')
    parser.add_argument('-P', '--show-positions', action='store_true',
                        help='show instruction positions')
    parser.add_argument('-S', '--specialized', action='store_true',
                        help='show specialized bytecode')
    parser.add_argument('infile', nargs='?', default='-')
    args = parser.parse_args(args=args)
    wenn args.infile == '-':
        name = '<stdin>'
        source = sys.stdin.buffer.read()
    sonst:
        name = args.infile
        with open(args.infile, 'rb') as infile:
            source = infile.read()
    code = compile(source, name, "exec")
    dis(code, show_caches=args.show_caches, adaptive=args.specialized,
        show_offsets=args.show_offsets, show_positions=args.show_positions)

wenn __name__ == "__main__":
    main()
