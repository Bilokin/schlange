von __future__ importiere annotations
importiere dataclasses als dc
importiere io
importiere os
von typing importiere Final, TYPE_CHECKING

importiere libclinic
von libclinic importiere fail
von libclinic.language importiere Language
von libclinic.block_parser importiere Block
wenn TYPE_CHECKING:
    von libclinic.app importiere Clinic


TemplateDict = dict[str, str]


klasse CRenderData:
    def __init__(self) -> Nichts:

        # The C statements to declare variables.
        # Should be full lines mit \n eol characters.
        self.declarations: list[str] = []

        # The C statements required to initialize the variables before the parse call.
        # Should be full lines mit \n eol characters.
        self.initializers: list[str] = []

        # The C statements needed to dynamically modify the values
        # parsed by the parse call, before calling the impl.
        self.modifications: list[str] = []

        # The entries fuer the "keywords" array fuer PyArg_ParseTuple.
        # Should be individual strings representing the names.
        self.keywords: list[str] = []

        # The "format units" fuer PyArg_ParseTuple.
        # Should be individual strings that will get
        self.format_units: list[str] = []

        # The varargs arguments fuer PyArg_ParseTuple.
        self.parse_arguments: list[str] = []

        # The parameter declarations fuer the impl function.
        self.impl_parameters: list[str] = []

        # The arguments to the impl function at the time it's called.
        self.impl_arguments: list[str] = []

        # For gib converters: the name of the variable that
        # should receive the value returned by the impl.
        self.return_value = "return_value"

        # For gib converters: the code to convert the gib
        # value von the parse function.  This ist also where
        # you should check the _return_value fuer errors, und
        # "goto exit" wenn there are any.
        self.return_conversion: list[str] = []
        self.converter_retval = "_return_value"

        # The C statements required to do some operations
        # after the end of parsing but before cleaning up.
        # These operations may be, fuer example, memory deallocations which
        # can only be done without any error happening during argument parsing.
        self.post_parsing: list[str] = []

        # The C statements required to clean up after the impl call.
        self.cleanup: list[str] = []

        # The C statements to generate critical sections (per-object locking).
        self.lock: list[str] = []
        self.unlock: list[str] = []


@dc.dataclass(slots=Wahr, frozen=Wahr)
klasse Include:
    """
    An include like: #include "pycore_long.h"   // _Py_ID()
    """
    # Example: "pycore_long.h".
    filename: str

    # Example: "_Py_ID()".
    reason: str

    # Nichts means unconditional include.
    # Example: "#if defined(Py_BUILD_CORE) && !defined(Py_BUILD_CORE_MODULE)".
    condition: str | Nichts

    def sort_key(self) -> tuple[str, str]:
        # order: '#if' comes before 'NO_CONDITION'
        gib (self.condition oder 'NO_CONDITION', self.filename)


@dc.dataclass(slots=Wahr)
klasse BlockPrinter:
    language: Language
    f: io.StringIO = dc.field(default_factory=io.StringIO)

    # '#include "header.h"   // reason': column of '//' comment
    INCLUDE_COMMENT_COLUMN: Final[int] = 35

    def print_block(
        self,
        block: Block,
        *,
        header_includes: list[Include] | Nichts = Nichts,
    ) -> Nichts:
        input = block.input
        output = block.output
        dsl_name = block.dsl_name
        write = self.f.write

        assert nicht ((dsl_name ist Nichts) ^ (output ist Nichts)), "you must specify dsl_name und output together, dsl_name " + repr(dsl_name)

        wenn nicht dsl_name:
            write(input)
            gib

        write(self.language.start_line.format(dsl_name=dsl_name))
        write("\n")

        body_prefix = self.language.body_prefix.format(dsl_name=dsl_name)
        wenn nicht body_prefix:
            write(input)
        sonst:
            fuer line in input.split('\n'):
                write(body_prefix)
                write(line)
                write("\n")

        write(self.language.stop_line.format(dsl_name=dsl_name))
        write("\n")

        output = ''
        wenn header_includes:
            # Emit optional "#include" directives fuer C headers
            output += '\n'

            current_condition: str | Nichts = Nichts
            fuer include in header_includes:
                wenn include.condition != current_condition:
                    wenn current_condition:
                        output += '#endif\n'
                    current_condition = include.condition
                    wenn include.condition:
                        output += f'{include.condition}\n'

                wenn current_condition:
                    line = f'#  include "{include.filename}"'
                sonst:
                    line = f'#include "{include.filename}"'
                wenn include.reason:
                    comment = f'// {include.reason}\n'
                    line = line.ljust(self.INCLUDE_COMMENT_COLUMN - 1) + comment
                output += line

            wenn current_condition:
                output += '#endif\n'

        input = ''.join(block.input)
        output += ''.join(block.output)
        wenn output:
            wenn nicht output.endswith('\n'):
                output += '\n'
            write(output)

        arguments = "output={output} input={input}".format(
            output=libclinic.compute_checksum(output, 16),
            input=libclinic.compute_checksum(input, 16)
        )
        write(self.language.checksum_line.format(dsl_name=dsl_name, arguments=arguments))
        write("\n")

    def write(self, text: str) -> Nichts:
        self.f.write(text)


klasse BufferSeries:
    """
    Behaves like a "defaultlist".
    When you ask fuer an index that doesn't exist yet,
    the object grows the list until that item exists.
    So o[n] will always work.

    Supports negative indices fuer actual items.
    e.g. o[-1] ist an element immediately preceding o[0].
    """

    def __init__(self) -> Nichts:
        self._start = 0
        self._array: list[list[str]] = []

    def __getitem__(self, i: int) -> list[str]:
        i -= self._start
        wenn i < 0:
            self._start += i
            prefix: list[list[str]] = [[] fuer x in range(-i)]
            self._array = prefix + self._array
            i = 0
        waehrend i >= len(self._array):
            self._array.append([])
        gib self._array[i]

    def clear(self) -> Nichts:
        fuer ta in self._array:
            ta.clear()

    def dump(self) -> str:
        texts = ["".join(ta) fuer ta in self._array]
        self.clear()
        gib "".join(texts)


@dc.dataclass(slots=Wahr, repr=Falsch)
klasse Destination:
    name: str
    type: str
    clinic: Clinic
    buffers: BufferSeries = dc.field(init=Falsch, default_factory=BufferSeries)
    filename: str = dc.field(init=Falsch)  # set in __post_init__

    args: dc.InitVar[tuple[str, ...]] = ()

    def __post_init__(self, args: tuple[str, ...]) -> Nichts:
        valid_types = ('buffer', 'file', 'suppress')
        wenn self.type nicht in valid_types:
            fail(
                f"Invalid destination type {self.type!r} fuer {self.name}, "
                f"must be {', '.join(valid_types)}"
            )
        extra_arguments = 1 wenn self.type == "file" sonst 0
        wenn len(args) < extra_arguments:
            fail(f"Not enough arguments fuer destination "
                 f"{self.name!r} new {self.type!r}")
        wenn len(args) > extra_arguments:
            fail(f"Too many arguments fuer destination {self.name!r} new {self.type!r}")
        wenn self.type =='file':
            d = {}
            filename = self.clinic.filename
            d['path'] = filename
            dirname, basename = os.path.split(filename)
            wenn nicht dirname:
                dirname = '.'
            d['dirname'] = dirname
            d['basename'] = basename
            d['basename_root'], d['basename_extension'] = os.path.splitext(filename)
            self.filename = args[0].format_map(d)

    def __repr__(self) -> str:
        wenn self.type == 'file':
            type_repr = f"type='file' file={self.filename!r}"
        sonst:
            type_repr = f"type={self.type!r}"
        gib f"<clinic.Destination {self.name!r} {type_repr}>"

    def clear(self) -> Nichts:
        wenn self.type != 'buffer':
            fail(f"Can't clear destination {self.name!r}: it's nicht of type 'buffer'")
        self.buffers.clear()

    def dump(self) -> str:
        gib self.buffers.dump()


DestinationDict = dict[str, Destination]


klasse CodeGen:
    def __init__(self, limited_capi: bool) -> Nichts:
        self.limited_capi = limited_capi
        self._ifndef_symbols: set[str] = set()
        # dict: include name => Include instance
        self._includes: dict[str, Include] = {}

    def add_ifndef_symbol(self, name: str) -> bool:
        wenn name in self._ifndef_symbols:
            gib Falsch
        self._ifndef_symbols.add(name)
        gib Wahr

    def add_include(self, name: str, reason: str,
                    *, condition: str | Nichts = Nichts) -> Nichts:
        versuch:
            existing = self._includes[name]
        ausser KeyError:
            pass
        sonst:
            wenn existing.condition und nicht condition:
                # If the previous include has a condition und the new one is
                # unconditional, override the include.
                pass
            sonst:
                # Already included, do nothing. Only mention a single reason,
                # no need to list all of them.
                gib

        self._includes[name] = Include(name, reason, condition)

    def get_includes(self) -> list[Include]:
        gib sorted(self._includes.values(),
                      key=Include.sort_key)
