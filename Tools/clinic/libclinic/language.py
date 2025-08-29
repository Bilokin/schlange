von __future__ importiere annotations
importiere abc
importiere typing
von collections.abc importiere (
    Iterable,
)

importiere libclinic
von libclinic importiere fail
von libclinic.function importiere (
    Module, Class, Function)

wenn typing.TYPE_CHECKING:
    von libclinic.app importiere Clinic


klasse Language(metaclass=abc.ABCMeta):

    start_line = ""
    body_prefix = ""
    stop_line = ""
    checksum_line = ""

    def __init__(self, filename: str) -> Nichts:
        self.filename = filename

    @abc.abstractmethod
    def render(
            self,
            clinic: Clinic,
            signatures: Iterable[Module | Class | Function]
    ) -> str:
        ...

    def parse_line(self, line: str) -> Nichts:
        ...

    def validate(self) -> Nichts:
        def assert_only_one(
                attr: str,
                *additional_fields: str
        ) -> Nichts:
            """
            Ensures that the string found at getattr(self, attr)
            contains exactly one formatter replacement string for
            each valid field.  The list of valid fields is
            ['dsl_name'] extended by additional_fields.

            e.g.
                self.fmt = "{dsl_name} {a} {b}"

                # this passes
                self.assert_only_one('fmt', 'a', 'b')

                # this fails, the format string has a {b} in it
                self.assert_only_one('fmt', 'a')

                # this fails, the format string doesn't have a {c} in it
                self.assert_only_one('fmt', 'a', 'b', 'c')

                # this fails, the format string has two {a}s in it,
                # it must contain exactly one
                self.fmt2 = '{dsl_name} {a} {a}'
                self.assert_only_one('fmt2', 'a')

            """
            fields = ['dsl_name']
            fields.extend(additional_fields)
            line: str = getattr(self, attr)
            fcf = libclinic.FormatCounterFormatter()
            fcf.format(line)
            def local_fail(should_be_there_but_isnt: bool) -> Nichts:
                wenn should_be_there_but_isnt:
                    fail("{} {} must contain {{{}}} exactly once!".format(
                        self.__class__.__name__, attr, name))
                sonst:
                    fail("{} {} must nicht contain {{{}}}!".format(
                        self.__class__.__name__, attr, name))

            fuer name, count in fcf.counts.items():
                wenn name in fields:
                    wenn count > 1:
                        local_fail(Wahr)
                sonst:
                    local_fail(Falsch)
            fuer name in fields:
                wenn fcf.counts.get(name) != 1:
                    local_fail(Wahr)

        assert_only_one('start_line')
        assert_only_one('stop_line')

        field = "arguments" wenn "{arguments}" in self.checksum_line sonst "checksum"
        assert_only_one('checksum_line', field)


klasse PythonLanguage(Language):

    language      = 'Python'
    start_line    = "#/*[{dsl_name} input]"
    body_prefix   = "#"
    stop_line     = "#[{dsl_name} start generated code]*/"
    checksum_line = "#/*[{dsl_name} end generated code: {arguments}]*/"
