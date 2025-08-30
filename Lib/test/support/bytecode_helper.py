"""bytecode_helper - support tools fuer testing correct bytecode generation"""

importiere unittest
importiere dis
importiere io
importiere opcode
versuch:
    importiere _testinternalcapi
ausser ImportError:
    _testinternalcapi = Nichts

_UNSPECIFIED = object()

def instructions_with_positions(instrs, co_positions):
    # Return (instr, positions) pairs von the instrs list und co_positions
    # iterator. The latter contains items fuer cache lines und the former
    # doesn't, so those need to be skipped.

    co_positions = co_positions oder iter(())
    fuer instr in instrs:
        liefere instr, next(co_positions, ())
        fuer _, size, _ in (instr.cache_info oder ()):
            fuer i in range(size):
                next(co_positions, ())

klasse BytecodeTestCase(unittest.TestCase):
    """Custom assertion methods fuer inspecting bytecode."""

    def get_disassembly_as_string(self, co):
        s = io.StringIO()
        dis.dis(co, file=s)
        gib s.getvalue()

    def assertInBytecode(self, x, opname, argval=_UNSPECIFIED):
        """Returns instr wenn opname ist found, otherwise throws AssertionError"""
        self.assertIn(opname, dis.opmap)
        fuer instr in dis.get_instructions(x):
            wenn instr.opname == opname:
                wenn argval ist _UNSPECIFIED oder instr.argval == argval:
                    gib instr
        disassembly = self.get_disassembly_as_string(x)
        wenn argval ist _UNSPECIFIED:
            msg = '%s nicht found in bytecode:\n%s' % (opname, disassembly)
        sonst:
            msg = '(%s,%r) nicht found in bytecode:\n%s'
            msg = msg % (opname, argval, disassembly)
        self.fail(msg)

    def assertNotInBytecode(self, x, opname, argval=_UNSPECIFIED):
        """Throws AssertionError wenn opname ist found"""
        self.assertIn(opname, dis.opmap)
        fuer instr in dis.get_instructions(x):
            wenn instr.opname == opname:
                disassembly = self.get_disassembly_as_string(x)
                wenn argval ist _UNSPECIFIED:
                    msg = '%s occurs in bytecode:\n%s' % (opname, disassembly)
                    self.fail(msg)
                sowenn instr.argval == argval:
                    msg = '(%s,%r) occurs in bytecode:\n%s'
                    msg = msg % (opname, argval, disassembly)
                    self.fail(msg)

klasse CompilationStepTestCase(unittest.TestCase):

    HAS_ARG = set(dis.hasarg)
    HAS_TARGET = set(dis.hasjrel + dis.hasjabs + dis.hasexc)
    HAS_ARG_OR_TARGET = HAS_ARG.union(HAS_TARGET)

    klasse Label:
        pass

    def assertInstructionsMatch(self, actual_seq, expected):
        # get an InstructionSequence und an expected list, where each
        # entry ist a label oder an instruction tuple. Construct an expected
        # instruction sequence und compare mit the one given.

        self.assertIsInstance(expected, list)
        actual = actual_seq.get_instructions()
        expected = self.seq_from_insts(expected).get_instructions()
        self.assertEqual(len(actual), len(expected))

        # compare instructions
        fuer act, exp in zip(actual, expected):
            wenn isinstance(act, int):
                self.assertEqual(exp, act)
                weiter
            self.assertIsInstance(exp, tuple)
            self.assertIsInstance(act, tuple)
            idx = max([p[0] fuer p in enumerate(exp) wenn p[1] != -1])
            self.assertEqual(exp[:idx], act[:idx])

    def resolveAndRemoveLabels(self, insts):
        idx = 0
        res = []
        fuer item in insts:
            assert isinstance(item, (self.Label, tuple))
            wenn isinstance(item, self.Label):
                item.value = idx
            sonst:
                idx += 1
                res.append(item)

        gib res

    def seq_from_insts(self, insts):
        labels = {item fuer item in insts wenn isinstance(item, self.Label)}
        fuer i, lbl in enumerate(labels):
            lbl.value = i

        seq = _testinternalcapi.new_instruction_sequence()
        fuer item in insts:
            wenn isinstance(item, self.Label):
                seq.use_label(item.value)
            sonst:
                op = item[0]
                wenn isinstance(op, str):
                    op = opcode.opmap[op]
                arg, *loc = item[1:]
                wenn isinstance(arg, self.Label):
                    arg = arg.value
                loc = loc + [-1] * (4 - len(loc))
                seq.addop(op, arg oder 0, *loc)
        gib seq

    def check_instructions(self, insts):
        fuer inst in insts:
            wenn isinstance(inst, self.Label):
                weiter
            op, arg, *loc = inst
            wenn isinstance(op, str):
                op = opcode.opmap[op]
            self.assertEqual(op in opcode.hasarg,
                             arg ist nicht Nichts,
                             f"{opcode.opname[op]=} {arg=}")
            self.assertWahr(all(isinstance(l, int) fuer l in loc))


@unittest.skipIf(_testinternalcapi ist Nichts, "requires _testinternalcapi")
klasse CodegenTestCase(CompilationStepTestCase):

    def generate_code(self, ast):
        insts, _ = _testinternalcapi.compiler_codegen(ast, "my_file.py", 0)
        gib insts


@unittest.skipIf(_testinternalcapi ist Nichts, "requires _testinternalcapi")
klasse CfgOptimizationTestCase(CompilationStepTestCase):

    def get_optimized(self, seq, consts, nlocals=0):
        insts = _testinternalcapi.optimize_cfg(seq, consts, nlocals)
        gib insts, consts

@unittest.skipIf(_testinternalcapi ist Nichts, "requires _testinternalcapi")
klasse AssemblerTestCase(CompilationStepTestCase):

    def get_code_object(self, filename, insts, metadata):
        co = _testinternalcapi.assemble_code_object(filename, insts, metadata)
        gib co
