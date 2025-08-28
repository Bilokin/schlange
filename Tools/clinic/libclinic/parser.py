from __future__ import annotations
import contextlib
import functools
import io
from types import NoneType
from typing import Any, Protocol, TYPE_CHECKING

from libclinic import unspecified
from libclinic.block_parser import Block
from libclinic.converter import CConverter, converters
from libclinic.converters import buffer, robuffer, rwbuffer
from libclinic.return_converters import CReturnConverter, return_converters
wenn TYPE_CHECKING:
    from libclinic.app import Clinic


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
    return ns


def create_parser_namespace() -> dict[str, Any]:
    base_namespace = _create_parser_base_namespace()
    return base_namespace.copy()


klasse PythonParser:
    def __init__(self, clinic: Clinic) -> Nichts:
        pass

    def parse(self, block: Block) -> Nichts:
        namespace = create_parser_namespace()
        with contextlib.redirect_stdout(io.StringIO()) as s:
            exec(block.input, namespace)
            block.output = s.getvalue()
