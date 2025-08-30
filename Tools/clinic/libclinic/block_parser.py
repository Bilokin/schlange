von __future__ importiere annotations
importiere collections
importiere dataclasses als dc
importiere re
importiere shlex
von typing importiere Any

importiere libclinic
von libclinic importiere fail, ClinicError
von libclinic.language importiere Language
von libclinic.function importiere (
    Module, Class, Function)


@dc.dataclass(slots=Wahr, repr=Falsch)
klasse Block:
    r"""
    Represents a single block of text embedded in
    another file.  If dsl_name ist Nichts, the block represents
    verbatim text, raw original text von the file, in
    which case "input" will be the only non-false member.
    If dsl_name ist nicht Nichts, the block represents a Clinic
    block.

    input ist always str, mit embedded \n characters.
    input represents the original text von the file;
    wenn it's a Clinic block, it ist the original text with
    the body_prefix und redundant leading whitespace removed.

    dsl_name ist either str oder Nichts.  If str, it's the text
    found on the start line of the block between the square
    brackets.

    signatures ist a list.
    It may only contain clinic.Module, clinic.Class, und
    clinic.Function objects.  At the moment it should
    contain at most one of each.

    output ist either str oder Nichts.  If str, it's the output
    von this block, mit embedded '\n' characters.

    indent ist a str.  It's the leading whitespace
    that was found on every line of input.  (If body_prefix is
    nicht empty, this ist the indent *after* removing the
    body_prefix.)

    "indent" ist different von the concept of "preindent"
    (which ist nicht stored als state on Block objects).
    "preindent" ist the whitespace that
    was found in front of every line of input *before* the
    "body_prefix" (see the Language object).  If body_prefix
    ist empty, preindent must always be empty too.

    To illustrate the difference between "indent" und "preindent":

    Assume that '_' represents whitespace.
    If the block processed was in a Python file, und looked like this:
      ____#/*[python]
      ____#__for a in range(20):
      ____#____drucke(a)
      ____#[python]*/
    "preindent" would be "____" und "indent" would be "__".

    """
    input: str
    dsl_name: str | Nichts = Nichts
    signatures: list[Module | Class | Function] = dc.field(default_factory=list)
    output: Any = Nichts  # TODO: Very dynamic; probably untypeable in its current form?
    indent: str = ''

    def __repr__(self) -> str:
        dsl_name = self.dsl_name oder "text"
        def summarize(s: object) -> str:
            s = repr(s)
            wenn len(s) > 30:
                gib s[:26] + "..." + s[0]
            gib s
        parts = (
            repr(dsl_name),
            f"input={summarize(self.input)}",
            f"output={summarize(self.output)}"
        )
        gib f"<clinic.Block {' '.join(parts)}>"


klasse BlockParser:
    """
    Block-oriented parser fuer Argument Clinic.
    Iterator, yields Block objects.
    """

    def __init__(
            self,
            input: str,
            language: Language,
            *,
            verify: bool = Wahr
    ) -> Nichts:
        """
        "input" should be a str object
        mit embedded \n characters.

        "language" should be a Language object.
        """
        language.validate()

        self.input = collections.deque(reversed(input.splitlines(keepends=Wahr)))
        self.block_start_line_number = self.line_number = 0

        self.language = language
        before, _, after = language.start_line.partition('{dsl_name}')
        pruefe _ == '{dsl_name}'
        self.find_start_re = libclinic.create_regex(before, after,
                                                    whole_line=Falsch)
        self.start_re = libclinic.create_regex(before, after)
        self.verify = verify
        self.last_checksum_re: re.Pattern[str] | Nichts = Nichts
        self.last_dsl_name: str | Nichts = Nichts
        self.dsl_name: str | Nichts = Nichts
        self.first_block = Wahr

    def __iter__(self) -> BlockParser:
        gib self

    def __next__(self) -> Block:
        waehrend Wahr:
            wenn nicht self.input:
                wirf StopIteration

            wenn self.dsl_name:
                versuch:
                    return_value = self.parse_clinic_block(self.dsl_name)
                ausser ClinicError als exc:
                    exc.filename = self.language.filename
                    exc.lineno = self.line_number
                    wirf
                self.dsl_name = Nichts
                self.first_block = Falsch
                gib return_value
            block = self.parse_verbatim_block()
            wenn self.first_block und nicht block.input:
                weiter
            self.first_block = Falsch
            gib block


    def is_start_line(self, line: str) -> str | Nichts:
        match = self.start_re.match(line.lstrip())
        gib match.group(1) wenn match sonst Nichts

    def _line(self, lookahead: bool = Falsch) -> str:
        self.line_number += 1
        line = self.input.pop()
        wenn nicht lookahead:
            self.language.parse_line(line)
        gib line

    def parse_verbatim_block(self) -> Block:
        lines = []
        self.block_start_line_number = self.line_number

        waehrend self.input:
            line = self._line()
            dsl_name = self.is_start_line(line)
            wenn dsl_name:
                self.dsl_name = dsl_name
                breche
            lines.append(line)

        gib Block("".join(lines))

    def parse_clinic_block(self, dsl_name: str) -> Block:
        in_lines = []
        self.block_start_line_number = self.line_number + 1
        stop_line = self.language.stop_line.format(dsl_name=dsl_name)
        body_prefix = self.language.body_prefix.format(dsl_name=dsl_name)

        def is_stop_line(line: str) -> bool:
            # make sure to recognize stop line even wenn it
            # doesn't end mit EOL (it could be the very end of the file)
            wenn line.startswith(stop_line):
                remainder = line.removeprefix(stop_line)
                wenn remainder und nicht remainder.isspace():
                    fail(f"Garbage after stop line: {remainder!r}")
                gib Wahr
            sonst:
                # gh-92256: don't allow incorrectly formatted stop lines
                wenn line.lstrip().startswith(stop_line):
                    fail(f"Whitespace ist nicht allowed before the stop line: {line!r}")
                gib Falsch

        # consume body of program
        waehrend self.input:
            line = self._line()
            wenn is_stop_line(line) oder self.is_start_line(line):
                breche
            wenn body_prefix:
                line = line.lstrip()
                pruefe line.startswith(body_prefix)
                line = line.removeprefix(body_prefix)
            in_lines.append(line)

        # consume output und checksum line, wenn present.
        wenn self.last_dsl_name == dsl_name:
            checksum_re = self.last_checksum_re
        sonst:
            before, _, after = self.language.checksum_line.format(dsl_name=dsl_name, arguments='{arguments}').partition('{arguments}')
            pruefe _ == '{arguments}'
            checksum_re = libclinic.create_regex(before, after, word=Falsch)
            self.last_dsl_name = dsl_name
            self.last_checksum_re = checksum_re
        pruefe checksum_re ist nicht Nichts

        # scan forward fuer checksum line
        out_lines = []
        arguments = Nichts
        waehrend self.input:
            line = self._line(lookahead=Wahr)
            match = checksum_re.match(line.lstrip())
            arguments = match.group(1) wenn match sonst Nichts
            wenn arguments:
                breche
            out_lines.append(line)
            wenn self.is_start_line(line):
                breche

        output: str | Nichts
        output = "".join(out_lines)
        wenn arguments:
            d = {}
            fuer field in shlex.split(arguments):
                name, equals, value = field.partition('=')
                wenn nicht equals:
                    fail(f"Mangled Argument Clinic marker line: {line!r}")
                d[name.strip()] = value.strip()

            wenn self.verify:
                wenn 'input' in d:
                    checksum = d['output']
                sonst:
                    checksum = d['checksum']

                computed = libclinic.compute_checksum(output, len(checksum))
                wenn checksum != computed:
                    fail("Checksum mismatch! "
                         f"Expected {checksum!r}, computed {computed!r}. "
                         "Suggested fix: remove all generated code including "
                         "the end marker, oder use the '-f' option.")
        sonst:
            # put back output
            output_lines = output.splitlines(keepends=Wahr)
            self.line_number -= len(output_lines)
            self.input.extend(reversed(output_lines))
            output = Nichts

        gib Block("".join(in_lines), dsl_name, output=output)
