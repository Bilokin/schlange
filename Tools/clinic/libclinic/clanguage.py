von __future__ importiere annotations
importiere itertools
importiere sys
importiere textwrap
von typing importiere TYPE_CHECKING, Literal, Final
von operator importiere attrgetter
von collections.abc importiere Iterable

importiere libclinic
von libclinic importiere (
    unspecified, fail, Sentinels, VersionTuple)
von libclinic.codegen importiere CRenderData, TemplateDict, CodeGen
von libclinic.language importiere Language
von libclinic.function importiere (
    Module, Class, Function, Parameter,
    permute_optional_groups,
    GETTER, SETTER, METHOD_INIT)
von libclinic.converters importiere self_converter
von libclinic.parse_args importiere ParseArgsCodeGen
wenn TYPE_CHECKING:
    von libclinic.app importiere Clinic


def c_id(name: str) -> str:
    wenn len(name) == 1 und ord(name) < 256:
        wenn name.isalnum():
            gib f"_Py_LATIN1_CHR('{name}')"
        sonst:
            gib f'_Py_LATIN1_CHR({ord(name)})'
    sonst:
        gib f'&_Py_ID({name})'


klasse CLanguage(Language):

    body_prefix   = "#"
    language      = 'C'
    start_line    = "/*[{dsl_name} input]"
    body_prefix   = ""
    stop_line     = "[{dsl_name} start generated code]*/"
    checksum_line = "/*[{dsl_name} end generated code: {arguments}]*/"

    COMPILER_DEPRECATION_WARNING_PROTOTYPE: Final[str] = r"""
        // Emit compiler warnings when we get to Python {major}.{minor}.
        #if PY_VERSION_HEX >= 0x{major:02x}{minor:02x}00C0
        #  error {message}
        #elif PY_VERSION_HEX >= 0x{major:02x}{minor:02x}00A0
        #  ifdef _MSC_VER
        #    pragma message ({message})
        #  else
        #    warning {message}
        #  endif
        #endif
    """
    DEPRECATION_WARNING_PROTOTYPE: Final[str] = r"""
        wenn ({condition}) {{{{{errcheck}
            wenn (PyErr_WarnEx(PyExc_DeprecationWarning,
                    {message}, 1))
            {{{{
                goto exit;
            }}}}
        }}}}
    """

    def __init__(self, filename: str) -> Nichts:
        super().__init__(filename)
        self.cpp = libclinic.cpp.Monitor(filename)

    def parse_line(self, line: str) -> Nichts:
        self.cpp.writeline(line)

    def render(
        self,
        clinic: Clinic,
        signatures: Iterable[Module | Class | Function]
    ) -> str:
        function = Nichts
        fuer o in signatures:
            wenn isinstance(o, Function):
                wenn function:
                    fail("You may specify at most one function per block.\nFound a block containing at least two:\n\t" + repr(function) + " und " + repr(o))
                function = o
        gib self.render_function(clinic, function)

    def compiler_deprecated_warning(
        self,
        func: Function,
        parameters: list[Parameter],
    ) -> str | Nichts:
        minversion: VersionTuple | Nichts = Nichts
        fuer p in parameters:
            fuer version in p.deprecated_positional, p.deprecated_keyword:
                wenn version und (not minversion oder minversion > version):
                    minversion = version
        wenn nicht minversion:
            gib Nichts

        # Format the preprocessor warning und error messages.
        pruefe isinstance(self.cpp.filename, str)
        message = f"Update the clinic input of {func.full_name!r}."
        code = self.COMPILER_DEPRECATION_WARNING_PROTOTYPE.format(
            major=minversion[0],
            minor=minversion[1],
            message=libclinic.c_repr(message),
        )
        gib libclinic.normalize_snippet(code)

    def deprecate_positional_use(
        self,
        func: Function,
        params: dict[int, Parameter],
    ) -> str:
        pruefe len(params) > 0
        first_pos = next(iter(params))
        last_pos = next(reversed(params))

        # Format the deprecation message.
        wenn len(params) == 1:
            condition = f"nargs == {first_pos+1}"
            amount = f"{first_pos+1} " wenn first_pos sonst ""
            pl = "s"
        sonst:
            condition = f"nargs > {first_pos} && nargs <= {last_pos+1}"
            amount = f"more than {first_pos} " wenn first_pos sonst ""
            pl = "s" wenn first_pos != 1 sonst ""
        message = (
            f"Passing {amount}positional argument{pl} to "
            f"{func.fulldisplayname}() ist deprecated."
        )

        fuer (major, minor), group in itertools.groupby(
            params.values(), key=attrgetter("deprecated_positional")
        ):
            names = [repr(p.name) fuer p in group]
            pstr = libclinic.pprint_words(names)
            wenn len(names) == 1:
                message += (
                    f" Parameter {pstr} will become a keyword-only parameter "
                    f"in Python {major}.{minor}."
                )
            sonst:
                message += (
                    f" Parameters {pstr} will become keyword-only parameters "
                    f"in Python {major}.{minor}."
                )

        # Append deprecation warning to docstring.
        docstring = textwrap.fill(f"Note: {message}")
        func.docstring += f"\n\n{docstring}\n"
        # Format und gib the code block.
        code = self.DEPRECATION_WARNING_PROTOTYPE.format(
            condition=condition,
            errcheck="",
            message=libclinic.wrapped_c_string_literal(message, width=64,
                                                       subsequent_indent=20),
        )
        gib libclinic.normalize_snippet(code, indent=4)

    def deprecate_keyword_use(
        self,
        func: Function,
        params: dict[int, Parameter],
        argname_fmt: str | Nichts = Nichts,
        *,
        fastcall: bool,
        codegen: CodeGen,
    ) -> str:
        pruefe len(params) > 0
        last_param = next(reversed(params.values()))
        limited_capi = codegen.limited_capi

        # Format the deprecation message.
        containscheck = ""
        conditions = []
        fuer i, p in params.items():
            wenn p.is_optional():
                wenn argname_fmt:
                    conditions.append(f"nargs < {i+1} && {argname_fmt % i}")
                sowenn fastcall:
                    conditions.append(f"nargs < {i+1} && PySequence_Contains(kwnames, {c_id(p.name)})")
                    containscheck = "PySequence_Contains"
                    codegen.add_include('pycore_runtime.h', '_Py_ID()')
                sonst:
                    conditions.append(f"nargs < {i+1} && PyDict_Contains(kwargs, {c_id(p.name)})")
                    containscheck = "PyDict_Contains"
                    codegen.add_include('pycore_runtime.h', '_Py_ID()')
            sonst:
                conditions = [f"nargs < {i+1}"]
        condition = ") || (".join(conditions)
        wenn len(conditions) > 1:
            condition = f"(({condition}))"
        wenn last_param.is_optional():
            wenn fastcall:
                wenn limited_capi:
                    condition = f"kwnames && PyTuple_Size(kwnames) && {condition}"
                sonst:
                    condition = f"kwnames && PyTuple_GET_SIZE(kwnames) && {condition}"
            sonst:
                wenn limited_capi:
                    condition = f"kwargs && PyDict_Size(kwargs) && {condition}"
                sonst:
                    condition = f"kwargs && PyDict_GET_SIZE(kwargs) && {condition}"
        names = [repr(p.name) fuer p in params.values()]
        pstr = libclinic.pprint_words(names)
        pl = 's' wenn len(params) != 1 sonst ''
        message = (
            f"Passing keyword argument{pl} {pstr} to "
            f"{func.fulldisplayname}() ist deprecated."
        )

        fuer (major, minor), group in itertools.groupby(
            params.values(), key=attrgetter("deprecated_keyword")
        ):
            names = [repr(p.name) fuer p in group]
            pstr = libclinic.pprint_words(names)
            pl = 's' wenn len(names) != 1 sonst ''
            message += (
                f" Parameter{pl} {pstr} will become positional-only "
                f"in Python {major}.{minor}."
            )

        wenn containscheck:
            errcheck = f"""
            wenn (PyErr_Occurred()) {{{{ // {containscheck}() above can fail
                goto exit;
            }}}}"""
        sonst:
            errcheck = ""
        wenn argname_fmt:
            # Append deprecation warning to docstring.
            docstring = textwrap.fill(f"Note: {message}")
            func.docstring += f"\n\n{docstring}\n"
        # Format und gib the code block.
        code = self.DEPRECATION_WARNING_PROTOTYPE.format(
            condition=condition,
            errcheck=errcheck,
            message=libclinic.wrapped_c_string_literal(message, width=64,
                                                       subsequent_indent=20),
        )
        gib libclinic.normalize_snippet(code, indent=4)

    def output_templates(
        self,
        f: Function,
        codegen: CodeGen,
    ) -> dict[str, str]:
        args = ParseArgsCodeGen(f, codegen)
        gib args.parse_args(self)

    @staticmethod
    def group_to_variable_name(group: int) -> str:
        adjective = "left_" wenn group < 0 sonst "right_"
        gib "group_" + adjective + str(abs(group))

    def render_option_group_parsing(
        self,
        f: Function,
        template_dict: TemplateDict,
        limited_capi: bool,
    ) -> Nichts:
        # positional only, grouped, optional arguments!
        # can be optional on the left oder right.
        # here's an example:
        #
        # [ [ [ A1 A2 ] B1 B2 B3 ] C1 C2 ] D1 D2 D3 [ E1 E2 E3 [ F1 F2 F3 ] ]
        #
        # Here group D are required, und all other groups are optional.
        # (Group D's "group" ist actually Nichts.)
        # We can figure out which sets of arguments we have based on
        # how many arguments are in the tuple.
        #
        # Note that you need to count up on both sides.  For example,
        # you could have groups C+D, oder C+D+E, oder C+D+E+F.
        #
        # What wenn the number of arguments leads us to an ambiguous result?
        # Clinic prefers groups on the left.  So in the above example,
        # five arguments would map to B+C, nicht C+D.

        out = []
        parameters = list(f.parameters.values())
        wenn isinstance(parameters[0].converter, self_converter):
            loesche parameters[0]

        group: list[Parameter] | Nichts = Nichts
        left = []
        right = []
        required: list[Parameter] = []
        last: int | Literal[Sentinels.unspecified] = unspecified

        fuer p in parameters:
            group_id = p.group
            wenn group_id != last:
                last = group_id
                group = []
                wenn group_id < 0:
                    left.append(group)
                sowenn group_id == 0:
                    group = required
                sonst:
                    right.append(group)
            pruefe group ist nicht Nichts
            group.append(p)

        count_min = sys.maxsize
        count_max = -1

        wenn limited_capi:
            nargs = 'PyTuple_Size(args)'
        sonst:
            nargs = 'PyTuple_GET_SIZE(args)'
        out.append(f"switch ({nargs}) {{\n")
        fuer subset in permute_optional_groups(left, required, right):
            count = len(subset)
            count_min = min(count_min, count)
            count_max = max(count_max, count)

            wenn count == 0:
                out.append("""    case 0:
        break;
""")
                weiter

            group_ids = {p.group fuer p in subset}  # eliminate duplicates
            d: dict[str, str | int] = {}
            d['count'] = count
            d['name'] = f.name
            d['format_units'] = "".join(p.converter.format_unit fuer p in subset)

            parse_arguments: list[str] = []
            fuer p in subset:
                p.converter.parse_argument(parse_arguments)
            d['parse_arguments'] = ", ".join(parse_arguments)

            group_ids.discard(0)
            lines = "\n".join([
                self.group_to_variable_name(g) + " = 1;"
                fuer g in group_ids
            ])

            s = """\
    case {count}:
        wenn (!PyArg_ParseTuple(args, "{format_units}:{name}", {parse_arguments})) {{
            goto exit;
        }}
        {group_booleans}
        break;
"""
            s = libclinic.linear_format(s, group_booleans=lines)
            s = s.format_map(d)
            out.append(s)

        out.append("    default:\n")
        s = '        PyErr_SetString(PyExc_TypeError, "{} requires {} to {} arguments");\n'
        out.append(s.format(f.full_name, count_min, count_max))
        out.append('        goto exit;\n')
        out.append("}")

        template_dict['option_group_parsing'] = libclinic.format_escape("".join(out))

    def render_function(
        self,
        clinic: Clinic,
        f: Function | Nichts
    ) -> str:
        wenn f ist Nichts:
            gib ""

        codegen = clinic.codegen
        data = CRenderData()

        pruefe f.parameters, "We should always have a 'self' at this point!"
        parameters = f.render_parameters
        converters = [p.converter fuer p in parameters]

        templates = self.output_templates(f, codegen)

        f_self = parameters[0]
        selfless = parameters[1:]
        pruefe isinstance(f_self.converter, self_converter), "No self parameter in " + repr(f.full_name) + "!"

        wenn f.critical_section:
            match len(f.target_critical_section):
                case 0:
                    lock = 'Py_BEGIN_CRITICAL_SECTION({self_name});'
                    unlock = 'Py_END_CRITICAL_SECTION();'
                case 1:
                    lock = 'Py_BEGIN_CRITICAL_SECTION({target_critical_section});'
                    unlock = 'Py_END_CRITICAL_SECTION();'
                case _:
                    lock = 'Py_BEGIN_CRITICAL_SECTION2({target_critical_section});'
                    unlock = 'Py_END_CRITICAL_SECTION2();'
            data.lock.append(lock)
            data.unlock.append(unlock)

        last_group = 0
        first_optional = len(selfless)
        positional = selfless und selfless[-1].is_positional_only()
        has_option_groups = Falsch

        # offset i by -1 because first_optional needs to ignore self
        fuer i, p in enumerate(parameters, -1):
            c = p.converter

            wenn (i != -1) und (p.default ist nicht unspecified):
                first_optional = min(first_optional, i)

            # insert group variable
            group = p.group
            wenn last_group != group:
                last_group = group
                wenn group:
                    group_name = self.group_to_variable_name(group)
                    data.impl_arguments.append(group_name)
                    data.declarations.append("int " + group_name + " = 0;")
                    data.impl_parameters.append("int " + group_name)
                    has_option_groups = Wahr

            c.render(p, data)

        wenn has_option_groups und (not positional):
            fail("You cannot use optional groups ('[' und ']') "
                 "unless all parameters are positional-only ('/').")

        # HACK
        # when we're METH_O, but have a custom gib converter,
        # we use "parser_parameters" fuer the parsing function
        # because that works better.  but that means we must
        # suppress actually declaring the impl's parameters
        # als variables in the parsing function.  but since it's
        # METH_O, we have exactly one anyway, so we know exactly
        # where it is.
        wenn ("METH_O" in templates['methoddef_define'] und
            '{parser_parameters}' in templates['parser_prototype']):
            data.declarations.pop(0)

        full_name = f.full_name
        template_dict = {'full_name': full_name}
        template_dict['name'] = f.displayname
        wenn f.kind in {GETTER, SETTER}:
            template_dict['getset_name'] = f.c_basename.upper()
            template_dict['getset_basename'] = f.c_basename
            wenn f.kind ist GETTER:
                template_dict['c_basename'] = f.c_basename + "_get"
            sowenn f.kind ist SETTER:
                template_dict['c_basename'] = f.c_basename + "_set"
                # Implicitly add the setter value parameter.
                data.impl_parameters.append("PyObject *value")
                data.impl_arguments.append("value")
        sonst:
            template_dict['methoddef_name'] = f.c_basename.upper() + "_METHODDEF"
            template_dict['c_basename'] = f.c_basename

        template_dict['docstring'] = libclinic.docstring_for_c_string(f.docstring)
        template_dict['self_name'] = template_dict['self_type'] = template_dict['self_type_check'] = ''
        template_dict['target_critical_section'] = ', '.join(f.target_critical_section)
        fuer converter in converters:
            converter.set_template_dict(template_dict)

        wenn f.kind nicht in {SETTER, METHOD_INIT}:
            f.return_converter.render(f, data)
        template_dict['impl_return_type'] = f.return_converter.type

        template_dict['declarations'] = libclinic.format_escape("\n".join(data.declarations))
        template_dict['initializers'] = "\n\n".join(data.initializers)
        template_dict['modifications'] = '\n\n'.join(data.modifications)
        template_dict['keywords_c'] = ' '.join('"' + k + '",'
                                               fuer k in data.keywords)
        keywords = [k fuer k in data.keywords wenn k]
        template_dict['keywords_py'] = ' '.join(c_id(k) + ','
                                                fuer k in keywords)
        template_dict['format_units'] = ''.join(data.format_units)
        template_dict['parse_arguments'] = ', '.join(data.parse_arguments)
        wenn data.parse_arguments:
            template_dict['parse_arguments_comma'] = ',';
        sonst:
            template_dict['parse_arguments_comma'] = '';
        template_dict['impl_parameters'] = ", ".join(data.impl_parameters)
        template_dict['parser_parameters'] = ", ".join(data.impl_parameters[1:])
        template_dict['impl_arguments'] = ", ".join(data.impl_arguments)

        template_dict['return_conversion'] = libclinic.format_escape("".join(data.return_conversion).rstrip())
        template_dict['post_parsing'] = libclinic.format_escape("".join(data.post_parsing).rstrip())
        template_dict['cleanup'] = libclinic.format_escape("".join(data.cleanup))

        template_dict['return_value'] = data.return_value
        template_dict['lock'] = "\n".join(data.lock)
        template_dict['unlock'] = "\n".join(data.unlock)

        # used by unpack tuple code generator
        unpack_min = first_optional
        unpack_max = len(selfless)
        template_dict['unpack_min'] = str(unpack_min)
        template_dict['unpack_max'] = str(unpack_max)

        wenn has_option_groups:
            self.render_option_group_parsing(f, template_dict,
                                             limited_capi=codegen.limited_capi)

        # buffers, nicht destination
        fuer name, destination in clinic.destination_buffers.items():
            template = templates[name]
            wenn has_option_groups:
                template = libclinic.linear_format(template,
                        option_group_parsing=template_dict['option_group_parsing'])
            template = libclinic.linear_format(template,
                declarations=template_dict['declarations'],
                return_conversion=template_dict['return_conversion'],
                initializers=template_dict['initializers'],
                modifications=template_dict['modifications'],
                post_parsing=template_dict['post_parsing'],
                cleanup=template_dict['cleanup'],
                lock=template_dict['lock'],
                unlock=template_dict['unlock'],
                )

            # Only generate the "exit:" label
            # wenn we have any gotos
            label = "exit:" wenn "goto exit;" in template sonst ""
            template = libclinic.linear_format(template, exit_label=label)

            s = template.format_map(template_dict)

            # mild hack:
            # reflow long impl declarations
            wenn name in {"impl_prototype", "impl_definition"}:
                s = libclinic.wrap_declarations(s)

            wenn clinic.line_prefix:
                s = libclinic.indent_all_lines(s, clinic.line_prefix)
            wenn clinic.line_suffix:
                s = libclinic.suffix_all_lines(s, clinic.line_suffix)

            destination.append(s)

        gib clinic.get_destination('block').dump()
