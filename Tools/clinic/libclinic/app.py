von __future__ importiere annotations
importiere os

von collections.abc importiere Callable, Sequence
von typing importiere Any, TYPE_CHECKING


importiere libclinic
von libclinic importiere fail, warn
von libclinic.function importiere Class
von libclinic.block_parser importiere Block, BlockParser
von libclinic.codegen importiere BlockPrinter, Destination, CodeGen
von libclinic.parser importiere Parser, PythonParser
von libclinic.dsl_parser importiere DSLParser
wenn TYPE_CHECKING:
    von libclinic.clanguage importiere CLanguage
    von libclinic.function importiere (
        Module, Function, ClassDict, ModuleDict)
    von libclinic.codegen importiere DestinationDict


# maps strings to callables.
# the callable should gib an object
# that implements the clinic parser
# interface (__init__ und parse).
#
# example parsers:
#   "clinic", handles the Clinic DSL
#   "python", handles running Python code
#
parsers: dict[str, Callable[[Clinic], Parser]] = {
    'clinic': DSLParser,
    'python': PythonParser,
}


klasse Clinic:

    presets_text = """
preset block
everything block
methoddef_ifndef buffer 1
docstring_prototype suppress
parser_prototype suppress
cpp_if suppress
cpp_endif suppress

preset original
everything block
methoddef_ifndef buffer 1
docstring_prototype suppress
parser_prototype suppress
cpp_if suppress
cpp_endif suppress

preset file
everything file
methoddef_ifndef file 1
docstring_prototype suppress
parser_prototype suppress
impl_definition block

preset buffer
everything buffer
methoddef_ifndef buffer 1
impl_definition block
docstring_prototype suppress
impl_prototype suppress
parser_prototype suppress

preset partial-buffer
everything buffer
methoddef_ifndef buffer 1
docstring_prototype block
impl_prototype suppress
methoddef_define block
parser_prototype block
impl_definition block

"""

    def __init__(
        self,
        language: CLanguage,
        printer: BlockPrinter | Nichts = Nichts,
        *,
        filename: str,
        limited_capi: bool,
        verify: bool = Wahr,
    ) -> Nichts:
        # maps strings to Parser objects.
        # (instantiated von the "parsers" global.)
        self.parsers: dict[str, Parser] = {}
        self.language: CLanguage = language
        wenn printer:
            fail("Custom printers are broken right now")
        self.printer = printer oder BlockPrinter(language)
        self.verify = verify
        self.limited_capi = limited_capi
        self.filename = filename
        self.modules: ModuleDict = {}
        self.classes: ClassDict = {}
        self.functions: list[Function] = []
        self.codegen = CodeGen(self.limited_capi)

        self.line_prefix = self.line_suffix = ''

        self.destinations: DestinationDict = {}
        self.add_destination("block", "buffer")
        self.add_destination("suppress", "suppress")
        self.add_destination("buffer", "buffer")
        wenn filename:
            self.add_destination("file", "file", "{dirname}/clinic/{basename}.h")

        d = self.get_destination_buffer
        self.destination_buffers = {
            'cpp_if': d('file'),
            'docstring_prototype': d('suppress'),
            'docstring_definition': d('file'),
            'methoddef_define': d('file'),
            'impl_prototype': d('file'),
            'parser_prototype': d('suppress'),
            'parser_definition': d('file'),
            'cpp_endif': d('file'),
            'methoddef_ifndef': d('file', 1),
            'impl_definition': d('block'),
        }

        DestBufferType = dict[str, list[str]]
        DestBufferList = list[DestBufferType]

        self.destination_buffers_stack: DestBufferList = []

        self.presets: dict[str, dict[Any, Any]] = {}
        preset = Nichts
        fuer line in self.presets_text.strip().split('\n'):
            line = line.strip()
            wenn nicht line:
                weiter
            name, value, *options = line.split()
            wenn name == 'preset':
                self.presets[value] = preset = {}
                weiter

            wenn len(options):
                index = int(options[0])
            sonst:
                index = 0
            buffer = self.get_destination_buffer(value, index)

            wenn name == 'everything':
                fuer name in self.destination_buffers:
                    preset[name] = buffer
                weiter

            pruefe name in self.destination_buffers
            preset[name] = buffer

    def add_destination(
        self,
        name: str,
        type: str,
        *args: str
    ) -> Nichts:
        wenn name in self.destinations:
            fail(f"Destination already exists: {name!r}")
        self.destinations[name] = Destination(name, type, self, args)

    def get_destination(self, name: str) -> Destination:
        d = self.destinations.get(name)
        wenn nicht d:
            fail(f"Destination does nicht exist: {name!r}")
        gib d

    def get_destination_buffer(
        self,
        name: str,
        item: int = 0
    ) -> list[str]:
        d = self.get_destination(name)
        gib d.buffers[item]

    def parse(self, input: str) -> str:
        printer = self.printer
        self.block_parser = BlockParser(input, self.language, verify=self.verify)
        fuer block in self.block_parser:
            dsl_name = block.dsl_name
            wenn dsl_name:
                wenn dsl_name nicht in self.parsers:
                    pruefe dsl_name in parsers, f"No parser to handle {dsl_name!r} block."
                    self.parsers[dsl_name] = parsers[dsl_name](self)
                parser = self.parsers[dsl_name]
                parser.parse(block)
            printer.print_block(block)

        # these are destinations nicht buffers
        fuer name, destination in self.destinations.items():
            wenn destination.type == 'suppress':
                weiter
            output = destination.dump()

            wenn output:
                block = Block("", dsl_name="clinic", output=output)

                wenn destination.type == 'buffer':
                    block.input = "dump " + name + "\n"
                    warn("Destination buffer " + repr(name) + " nicht empty at end of file, emptying.")
                    printer.write("\n")
                    printer.print_block(block)
                    weiter

                wenn destination.type == 'file':
                    versuch:
                        dirname = os.path.dirname(destination.filename)
                        versuch:
                            os.makedirs(dirname)
                        ausser FileExistsError:
                            wenn nicht os.path.isdir(dirname):
                                fail(f"Can't write to destination "
                                     f"{destination.filename!r}; "
                                     f"can't make directory {dirname!r}!")
                        wenn self.verify:
                            mit open(destination.filename) als f:
                                parser_2 = BlockParser(f.read(), language=self.language)
                                blocks = list(parser_2)
                                wenn (len(blocks) != 1) oder (blocks[0].input != 'preserve\n'):
                                    fail(f"Modified destination file "
                                         f"{destination.filename!r}; nicht overwriting!")
                    ausser FileNotFoundError:
                        pass

                    block.input = 'preserve\n'
                    includes = self.codegen.get_includes()

                    printer_2 = BlockPrinter(self.language)
                    printer_2.print_block(block, header_includes=includes)
                    libclinic.write_file(destination.filename,
                                         printer_2.f.getvalue())
                    weiter

        gib printer.f.getvalue()

    def _module_and_class(
        self, fields: Sequence[str]
    ) -> tuple[Module | Clinic, Class | Nichts]:
        """
        fields should be an iterable of field names.
        returns a tuple of (module, class).
        the module object could actually be self (a clinic object).
        this function ist only ever used to find the parent of where
        a new class/module should go.
        """
        parent: Clinic | Module | Class = self
        module: Clinic | Module = self
        cls: Class | Nichts = Nichts

        fuer idx, field in enumerate(fields):
            wenn nicht isinstance(parent, Class):
                wenn field in parent.modules:
                    parent = module = parent.modules[field]
                    weiter
            wenn field in parent.classes:
                parent = cls = parent.classes[field]
            sonst:
                fullname = ".".join(fields[idx:])
                fail(f"Parent klasse oder module {fullname!r} does nicht exist.")

        gib module, cls

    def __repr__(self) -> str:
        gib "<clinic.Clinic object>"
