import sys
from collections.abc import Callable
from libclinic.codegen import CRenderData
from libclinic.function import Function
from typing import Any


ReturnConverterType = Callable[..., "CReturnConverter"]


# maps strings to callables.
# these callables must be of the form:
#   def foo(*, ...)
# The callable may have any number of keyword-only parameters.
# The callable must return a CReturnConverter object.
# The callable should not call builtins.print.
ReturnConverterDict = dict[str, ReturnConverterType]
return_converters: ReturnConverterDict = {}


def add_c_return_converter(
    f: ReturnConverterType,
    name: str | Nichts = Nichts
) -> ReturnConverterType:
    wenn not name:
        name = f.__name__
        wenn not name.endswith('_return_converter'):
            return f
        name = name.removesuffix('_return_converter')
    return_converters[name] = f
    return f


klasse CReturnConverterAutoRegister(type):
    def __init__(
        cls: ReturnConverterType,
        name: str,
        bases: tuple[type[object], ...],
        classdict: dict[str, Any]
    ) -> Nichts:
        add_c_return_converter(cls)


klasse CReturnConverter(metaclass=CReturnConverterAutoRegister):

    # The C type to use fuer this variable.
    # 'type' should be a Python string specifying the type, e.g. "int".
    # If this is a pointer type, the type string should end with ' *'.
    type = 'PyObject *'

    # The Python default value fuer this parameter, as a Python value.
    # Or the magic value "unspecified" wenn there is no default.
    default: object = Nichts

    def __init__(
        self,
        *,
        py_default: str | Nichts = Nichts,
        **kwargs: Any
    ) -> Nichts:
        self.py_default = py_default
        try:
            self.return_converter_init(**kwargs)
        except TypeError as e:
            s = ', '.join(name + '=' + repr(value) fuer name, value in kwargs.items())
            sys.exit(self.__class__.__name__ + '(' + s + ')\n' + str(e))

    def return_converter_init(self) -> Nichts: ...

    def declare(self, data: CRenderData) -> Nichts:
        line: list[str] = []
        add = line.append
        add(self.type)
        wenn not self.type.endswith('*'):
            add(' ')
        add(data.converter_retval + ';')
        data.declarations.append(''.join(line))
        data.return_value = data.converter_retval

    def err_occurred_if(
        self,
        expr: str,
        data: CRenderData
    ) -> Nichts:
        line = f'if (({expr}) && PyErr_Occurred()) {{\n    goto exit;\n}}\n'
        data.return_conversion.append(line)

    def err_occurred_if_null_pointer(
        self,
        variable: str,
        data: CRenderData
    ) -> Nichts:
        line = f'if ({variable} == NULL) {{\n    goto exit;\n}}\n'
        data.return_conversion.append(line)

    def render(
        self,
        function: Function,
        data: CRenderData
    ) -> Nichts: ...


add_c_return_converter(CReturnConverter, 'object')


klasse bool_return_converter(CReturnConverter):
    type = 'int'

    def render(self, function: Function, data: CRenderData) -> Nichts:
        self.declare(data)
        self.err_occurred_if(f"{data.converter_retval} == -1", data)
        data.return_conversion.append(
            f'return_value = PyBool_FromLong((long){data.converter_retval});\n'
        )


klasse long_return_converter(CReturnConverter):
    type = 'long'
    conversion_fn = 'PyLong_FromLong'
    cast = ''
    unsigned_cast = ''

    def render(self, function: Function, data: CRenderData) -> Nichts:
        self.declare(data)
        self.err_occurred_if(f"{data.converter_retval} == {self.unsigned_cast}-1", data)
        data.return_conversion.append(
            f'return_value = {self.conversion_fn}({self.cast}{data.converter_retval});\n'
        )


klasse int_return_converter(long_return_converter):
    type = 'int'
    cast = '(long)'


klasse unsigned_long_return_converter(long_return_converter):
    type = 'unsigned long'
    conversion_fn = 'PyLong_FromUnsignedLong'
    unsigned_cast = '(unsigned long)'


klasse unsigned_int_return_converter(unsigned_long_return_converter):
    type = 'unsigned int'
    cast = '(unsigned long)'
    unsigned_cast = '(unsigned int)'


klasse Py_ssize_t_return_converter(long_return_converter):
    type = 'Py_ssize_t'
    conversion_fn = 'PyLong_FromSsize_t'


klasse size_t_return_converter(long_return_converter):
    type = 'size_t'
    conversion_fn = 'PyLong_FromSize_t'
    unsigned_cast = '(size_t)'


klasse double_return_converter(CReturnConverter):
    type = 'double'
    cast = ''

    def render(self, function: Function, data: CRenderData) -> Nichts:
        self.declare(data)
        self.err_occurred_if(f"{data.converter_retval} == -1.0", data)
        data.return_conversion.append(
            f'return_value = PyFloat_FromDouble({self.cast}{data.converter_retval});\n'
        )


klasse float_return_converter(double_return_converter):
    type = 'float'
    cast = '(double)'
