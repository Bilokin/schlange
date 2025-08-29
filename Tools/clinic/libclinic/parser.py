von __future__ importiere annotations
importiere contextlib
importiere functools
importiere io
von types importiere NoneType
von typing importiere Any, Protocol, TYPE_CHECKING

von libclinic importiere unspecified
von libclinic.block_parser importiere Block
von libclinic.converter importiere CConverter, converters
von libclinic.converters importiere buffer, robuffer, rwbuffer
von libclinic.return_converters importiere CReturnConverter, return_converters
wenn TYPE_CHECKING:
    von libclinic.app importiere Clinic


klasse Parser(Protocol):
    def __init__(self, clinic: Clinic) -> Nichts: ...
    def parse(self, block: Block) -> Nichts: ...


@functools.cache
def _create_parser_base_namespace() -> dict[str, Any]:
    ns = dict(
        CConverter=CConverter,
        CReturnConverter=CReturnConverter,
        buffer=buffer,
        robuffer=robuffer,
        rwbuffer=rwbuffer,
        unspecified=unspecified,
        NoneType=NoneType,
    )
    fuer name, converter in converters.items():
        ns[f'{name}_converter'] = converter
    fuer name, return_converter in return_converters.items():
        ns[f'{name}_return_converter'] = return_converter
    gib ns


def create_parser_namespace() -> dict[str, Any]:
    base_namespace = _create_parser_base_namespace()
    gib base_namespace.copy()


klasse PythonParser:
    def __init__(self, clinic: Clinic) -> Nichts:
        pass

    def parse(self, block: Block) -> Nichts:
        namespace = create_parser_namespace()
        mit contextlib.redirect_stdout(io.StringIO()) als s:
            exec(block.input, namespace)
            block.output = s.getvalue()
