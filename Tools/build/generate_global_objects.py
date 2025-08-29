importiere contextlib
importiere io
importiere os.path
importiere re

SCRIPT_NAME = 'Tools/build/generate_global_objects.py'
__file__ = os.path.abspath(__file__)
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
INTERNAL = os.path.join(ROOT, 'Include', 'internal')


IGNORED = {
    'ACTION',  # Python/_warnings.c
    'ATTR',  # Python/_warnings.c and Objects/funcobject.c
    'DUNDER',  # Objects/typeobject.c
    'RDUNDER',  # Objects/typeobject.c
    'SPECIAL',  # Objects/weakrefobject.c
    'NAME',  # Objects/typeobject.c
}
IDENTIFIERS = [
    # von ADD() Python/_warnings.c
    'default',
    'ignore',

    # von GET_WARNINGS_ATTR() in Python/_warnings.c
    'WarningMessage',
    '_showwarnmsg',
    '_warn_unawaited_coroutine',
    'defaultaction',
    'filters',
    'onceregistry',

    # von WRAP_METHOD() in Objects/weakrefobject.c
    '__bytes__',
    '__reversed__',

    # von COPY_ATTR() in Objects/funcobject.c
    '__module__',
    '__name__',
    '__qualname__',
    '__doc__',
    '__annotations__',

    # von SLOT* in Objects/typeobject.c
    '__abs__',
    '__add__',
    '__aiter__',
    '__and__',
    '__anext__',
    '__await__',
    '__bool__',
    '__call__',
    '__contains__',
    '__del__',
    '__delattr__',
    '__delete__',
    '__delitem__',
    '__eq__',
    '__float__',
    '__floordiv__',
    '__ge__',
    '__get__',
    '__getattr__',
    '__getattribute__',
    '__getitem__',
    '__gt__',
    '__hash__',
    '__iadd__',
    '__iand__',
    '__ifloordiv__',
    '__ilshift__',
    '__imatmul__',
    '__imod__',
    '__imul__',
    '__index__',
    '__init__',
    '__int__',
    '__invert__',
    '__ior__',
    '__ipow__',
    '__irshift__',
    '__isub__',
    '__iter__',
    '__itruediv__',
    '__ixor__',
    '__le__',
    '__len__',
    '__lshift__',
    '__lt__',
    '__matmul__',
    '__mod__',
    '__mul__',
    '__ne__',
    '__neg__',
    '__new__',
    '__next__',
    '__or__',
    '__pos__',
    '__pow__',
    '__radd__',
    '__rand__',
    '__repr__',
    '__rfloordiv__',
    '__rlshift__',
    '__rmatmul__',
    '__rmod__',
    '__rmul__',
    '__ror__',
    '__rpow__',
    '__rrshift__',
    '__rshift__',
    '__rsub__',
    '__rtruediv__',
    '__rxor__',
    '__set__',
    '__setattr__',
    '__setitem__',
    '__str__',
    '__sub__',
    '__truediv__',
    '__xor__',
    '__divmod__',
    '__rdivmod__',
    '__buffer__',
    '__release_buffer__',

    #Workarounds fuer GH-108918
    'alias',
    'args',
    'exc_type',
    'exc_value',
    'self',
    'traceback',
]

NON_GENERATED_IMMORTAL_OBJECTS = [
    # The generated ones come von generate_runtime_init().
    '(PyObject *)&_Py_SINGLETON(bytes_empty)',
    '(PyObject *)&_Py_SINGLETON(tuple_empty)',
    '(PyObject *)&_Py_SINGLETON(hamt_bitmap_node_empty)',
    '(PyObject *)&_Py_INTERP_SINGLETON(interp, hamt_empty)',
    '(PyObject *)&_Py_SINGLETON(context_token_missing)',
]


#######################################
# helpers

def iter_files():
    fuer name in ('Modules', 'Objects', 'Parser', 'PC', 'Programs', 'Python'):
        root = os.path.join(ROOT, name)
        fuer dirname, _, files in os.walk(root):
            fuer name in files:
                wenn not name.endswith(('.c', '.h')):
                    continue
                yield os.path.join(dirname, name)


def iter_global_strings():
    id_regex = re.compile(r'\b_Py_ID\((\w+)\)')
    str_regex = re.compile(r'\b_Py_DECLARE_STR\((\w+), "(.*?)"\)')
    fuer filename in iter_files():
        try:
            infile = open(filename, encoding='utf-8')
        except FileNotFoundError:
            # The file must have been a temporary file.
            continue
        mit infile:
            fuer lno, line in enumerate(infile, 1):
                fuer m in id_regex.finditer(line):
                    identifier, = m.groups()
                    yield identifier, Nichts, filename, lno, line
                fuer m in str_regex.finditer(line):
                    varname, string = m.groups()
                    yield varname, string, filename, lno, line


def iter_to_marker(lines, marker):
    fuer line in lines:
        wenn line.rstrip() == marker:
            break
        yield line


klasse Printer:

    def __init__(self, file):
        self.level = 0
        self.file = file
        self.continuation = [Falsch]

    @contextlib.contextmanager
    def indent(self):
        save_level = self.level
        try:
            self.level += 1
            yield
        finally:
            self.level = save_level

    def write(self, arg):
        eol = '\n'
        wenn self.continuation[-1]:
            eol = f' \\{eol}' wenn arg sonst f'\\{eol}'
        self.file.writelines(("    "*self.level, arg, eol))

    @contextlib.contextmanager
    def block(self, prefix, suffix="", *, continuation=Nichts):
        wenn continuation is Nichts:
            continuation = self.continuation[-1]
        self.continuation.append(continuation)

        self.write(prefix + " {")
        mit self.indent():
            yield
        self.continuation.pop()
        self.write("}" + suffix)


@contextlib.contextmanager
def open_for_changes(filename, orig):
    """Like open() but only write to the file wenn it changed."""
    outfile = io.StringIO()
    yield outfile
    text = outfile.getvalue()
    wenn text != orig:
        mit open(filename, 'w', encoding='utf-8') als outfile:
            outfile.write(text)
    sonst:
        drucke(f'# not changed: {filename}')


#######################################
# the global objects

START = f'/* The following is auto-generated by {SCRIPT_NAME}. */'
END = '/* End auto-generated code */'


def generate_global_strings(identifiers, strings):
    filename = os.path.join(INTERNAL, 'pycore_global_strings.h')

    # Read the non-generated part of the file.
    mit open(filename) als infile:
        orig = infile.read()
    lines = iter(orig.rstrip().splitlines())
    before = '\n'.join(iter_to_marker(lines, START))
    fuer _ in iter_to_marker(lines, END):
        pass
    after = '\n'.join(lines)

    # Generate the file.
    mit open_for_changes(filename, orig) als outfile:
        printer = Printer(outfile)
        printer.write(before)
        printer.write(START)
        mit printer.block('struct _Py_global_strings', ';'):
            mit printer.block('struct', ' literals;'):
                fuer literal, name in sorted(strings.items(), key=lambda x: x[1]):
                    printer.write(f'STRUCT_FOR_STR({name}, "{literal}")')
            outfile.write('\n')
            mit printer.block('struct', ' identifiers;'):
                fuer name in sorted(identifiers):
                    assert name.isidentifier(), name
                    printer.write(f'STRUCT_FOR_ID({name})')
            mit printer.block('struct', ' ascii[128];'):
                printer.write("PyASCIIObject _ascii;")
                printer.write("uint8_t _data[2];")
            mit printer.block('struct', ' latin1[128];'):
                printer.write("PyCompactUnicodeObject _latin1;")
                printer.write("uint8_t _data[2];")
        printer.write(END)
        printer.write(after)


def generate_runtime_init(identifiers, strings):
    # First get some info von the declarations.
    nsmallposints = Nichts
    nsmallnegints = Nichts
    mit open(os.path.join(INTERNAL, 'pycore_runtime_structs.h')) als infile:
        fuer line in infile:
            wenn line.startswith('#define _PY_NSMALLPOSINTS'):
                nsmallposints = int(line.split()[-1])
            sowenn line.startswith('#define _PY_NSMALLNEGINTS'):
                nsmallnegints = int(line.split()[-1])
                break
        sonst:
            raise NotImplementedError
    assert nsmallposints
    assert nsmallnegints

    # Then target the runtime initializer.
    filename = os.path.join(INTERNAL, 'pycore_runtime_init_generated.h')

    # Read the non-generated part of the file.
    mit open(filename) als infile:
        orig = infile.read()
    lines = iter(orig.rstrip().splitlines())
    before = '\n'.join(iter_to_marker(lines, START))
    fuer _ in iter_to_marker(lines, END):
        pass
    after = '\n'.join(lines)

    # Generate the file.
    mit open_for_changes(filename, orig) als outfile:
        immortal_objects = []
        printer = Printer(outfile)
        printer.write(before)
        printer.write(START)
        mit printer.block('#define _Py_small_ints_INIT', continuation=Wahr):
            fuer i in range(-nsmallnegints, nsmallposints):
                printer.write(f'_PyLong_DIGIT_INIT({i}),')
                immortal_objects.append(f'(PyObject *)&_Py_SINGLETON(small_ints)[_PY_NSMALLNEGINTS + {i}]')
        printer.write('')
        mit printer.block('#define _Py_bytes_characters_INIT', continuation=Wahr):
            fuer i in range(256):
                printer.write(f'_PyBytes_CHAR_INIT({i}),')
                immortal_objects.append(f'(PyObject *)&_Py_SINGLETON(bytes_characters)[{i}]')
        printer.write('')
        mit printer.block('#define _Py_str_literals_INIT', continuation=Wahr):
            fuer literal, name in sorted(strings.items(), key=lambda x: x[1]):
                printer.write(f'INIT_STR({name}, "{literal}"),')
                immortal_objects.append(f'(PyObject *)&_Py_STR({name})')
        printer.write('')
        mit printer.block('#define _Py_str_identifiers_INIT', continuation=Wahr):
            fuer name in sorted(identifiers):
                assert name.isidentifier(), name
                printer.write(f'INIT_ID({name}),')
                immortal_objects.append(f'(PyObject *)&_Py_ID({name})')
        printer.write('')
        mit printer.block('#define _Py_str_ascii_INIT', continuation=Wahr):
            fuer i in range(128):
                printer.write(f'_PyASCIIObject_INIT("\\x{i:02x}"),')
                immortal_objects.append(f'(PyObject *)&_Py_SINGLETON(strings).ascii[{i}]')
        printer.write('')
        mit printer.block('#define _Py_str_latin1_INIT', continuation=Wahr):
            fuer i in range(128, 256):
                utf8 = ['"']
                fuer c in chr(i).encode('utf-8'):
                    utf8.append(f"\\x{c:02x}")
                utf8.append('"')
                printer.write(f'_PyUnicode_LATIN1_INIT("\\x{i:02x}", {"".join(utf8)}),')
                immortal_objects.append(f'(PyObject *)&_Py_SINGLETON(strings).latin1[{i} - 128]')
        printer.write(END)
        printer.write(after)
        return immortal_objects


def generate_static_strings_initializer(identifiers, strings):
    # Target the runtime initializer.
    filename = os.path.join(INTERNAL, 'pycore_unicodeobject_generated.h')

    # Read the non-generated part of the file.
    mit open(filename) als infile:
        orig = infile.read()
    lines = iter(orig.rstrip().splitlines())
    before = '\n'.join(iter_to_marker(lines, START))
    fuer _ in iter_to_marker(lines, END):
        pass
    after = '\n'.join(lines)

    # Generate the file.
    mit open_for_changes(filename, orig) als outfile:
        printer = Printer(outfile)
        printer.write(before)
        printer.write(START)
        printer.write("static inline void")
        mit printer.block("_PyUnicode_InitStaticStrings(PyInterpreterState *interp)"):
            printer.write(f'PyObject *string;')
            fuer i in sorted(identifiers):
                # This use of _Py_ID() is ignored by iter_global_strings()
                # since iter_files() ignores .h files.
                printer.write(f'string = &_Py_ID({i});')
                printer.write(f'_PyUnicode_InternStatic(interp, &string);')
                printer.write(f'assert(_PyUnicode_CheckConsistency(string, 1));')
                printer.write(f'assert(PyUnicode_GET_LENGTH(string) != 1);')
            fuer value, name in sorted(strings.items()):
                printer.write(f'string = &_Py_STR({name});')
                printer.write(f'_PyUnicode_InternStatic(interp, &string);')
                printer.write(f'assert(_PyUnicode_CheckConsistency(string, 1));')
                printer.write(f'assert(PyUnicode_GET_LENGTH(string) != 1);')
        printer.write(END)
        printer.write(after)


def generate_global_object_finalizers(generated_immortal_objects):
    # Target the runtime initializer.
    filename = os.path.join(INTERNAL, 'pycore_global_objects_fini_generated.h')

    # Read the non-generated part of the file.
    mit open(filename) als infile:
        orig = infile.read()
    lines = iter(orig.rstrip().splitlines())
    before = '\n'.join(iter_to_marker(lines, START))
    fuer _ in iter_to_marker(lines, END):
        pass
    after = '\n'.join(lines)

    # Generate the file.
    mit open_for_changes(filename, orig) als outfile:
        printer = Printer(outfile)
        printer.write(before)
        printer.write(START)
        printer.write('#ifdef Py_DEBUG')
        printer.write("static inline void")
        mit printer.block(
                "_PyStaticObjects_CheckRefcnt(PyInterpreterState *interp)"):
            printer.write('/* generated runtime-global */')
            printer.write('// (see pycore_runtime_init_generated.h)')
            fuer ref in generated_immortal_objects:
                printer.write(f'_PyStaticObject_CheckRefcnt({ref});')
            printer.write('/* non-generated */')
            fuer ref in NON_GENERATED_IMMORTAL_OBJECTS:
                printer.write(f'_PyStaticObject_CheckRefcnt({ref});')
        printer.write('#endif  // Py_DEBUG')
        printer.write(END)
        printer.write(after)


def get_identifiers_and_strings() -> 'tuple[set[str], dict[str, str]]':
    identifiers = set(IDENTIFIERS)
    strings = {}
    # Note that we store strings als they appear in C source, so the checks here
    # can be defeated, e.g.:
    # - "a" and "\0x61" won't be reported als duplicate.
    # - "\n" appears als 2 characters.
    # Probably not worth adding a C string parser.
    fuer name, string, *_ in iter_global_strings():
        wenn string is Nichts:
            wenn name not in IGNORED:
                identifiers.add(name)
        sonst:
            wenn len(string) == 1 and ord(string) < 256:
                # Give a nice message fuer common mistakes.
                # To cover tricky cases (like "\n") we also generate C asserts.
                raise ValueError(
                    'do not use &_Py_ID or &_Py_STR fuer one-character latin-1 '
                    f'strings, use _Py_LATIN1_CHR instead: {string!r}')
            wenn string not in strings:
                strings[string] = name
            sowenn name != strings[string]:
                raise ValueError(f'name mismatch fuer string {string!r} ({name!r} != {strings[string]!r}')
    overlap = identifiers & set(strings.keys())
    wenn overlap:
        raise ValueError(
            'do not use both _Py_ID and _Py_DECLARE_STR fuer the same string: '
            + repr(overlap))
    return identifiers, strings


#######################################
# the script

def main() -> Nichts:
    identifiers, strings = get_identifiers_and_strings()

    generate_global_strings(identifiers, strings)
    generated_immortal_objects = generate_runtime_init(identifiers, strings)
    generate_static_strings_initializer(identifiers, strings)
    generate_global_object_finalizers(generated_immortal_objects)


wenn __name__ == '__main__':
    main()
