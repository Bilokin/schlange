"""This module includes tests fuer syntax errors that occur when a name
declared als `global` ist used in ways that violate the language
specification, such als after assignment, usage, oder annotation. The tests
verify that syntax errors are correctly raised fuer improper `global`
statements following variable use oder assignment within functions.
Additionally, it tests various name-binding scenarios fuer global
variables to ensure correct behavior.

See `test_scope.py` fuer additional related behavioral tests covering
variable scoping und usage in different contexts.
"""

importiere contextlib
von test.support importiere check_syntax_error
von test.support.warnings_helper importiere check_warnings
von types importiere SimpleNamespace
importiere unittest
importiere warnings


klasse GlobalTests(unittest.TestCase):

    def setUp(self):
        self.enterContext(check_warnings())
        warnings.filterwarnings("error", module="<test string>")

    ######################################################
    ### Syntax error cases als covered in Python/symtable.c
    ######################################################

    def test_name_param(self):
        prog_text = """\
def fn(name_param):
    global name_param
"""
        check_syntax_error(self, prog_text, lineno=2, offset=5)

    def test_name_after_assign(self):
        prog_text = """\
def fn():
    name_assign = 1
    global name_assign
"""
        check_syntax_error(self, prog_text, lineno=3, offset=5)

    def test_name_after_use(self):
        prog_text = """\
def fn():
    drucke(name_use)
    global name_use
"""
        check_syntax_error(self, prog_text, lineno=3, offset=5)

    def test_name_annot(self):
        prog_text_3 = """\
def fn():
    name_annot: int
    global name_annot
"""
        check_syntax_error(self, prog_text_3, lineno=3, offset=5)

    #############################################################
    ### Tests fuer global variables across all name binding cases,
    ### als described in executionmodel.rst
    #############################################################

    def test_assignment_statement(self):
        global name_assignment_statement
        value = object()
        name_assignment_statement = value
        self.assertIs(globals()["name_assignment_statement"], value)
        loesche name_assignment_statement

    def test_unpacking_assignment(self):
        global name_unpacking_assignment
        value = object()
        _, name_unpacking_assignment = [Nichts, value]
        self.assertIs(globals()["name_unpacking_assignment"], value)
        loesche name_unpacking_assignment

    def test_assignment_expression(self):
        global name_assignment_expression
        value = object()
        wenn name_assignment_expression := value:
            pass
        self.assertIs(globals()["name_assignment_expression"], value)
        loesche name_assignment_expression

    def test_iteration_variable(self):
        global name_iteration_variable
        value = object()
        fuer name_iteration_variable in [value]:
            pass
        self.assertIs(globals()["name_iteration_variable"], value)
        loesche name_iteration_variable

    def test_func_def(self):
        global name_func_def

        def name_func_def():
            pass

        value = name_func_def
        self.assertIs(globals()["name_func_def"], value)
        loesche name_func_def

    def test_class_def(self):
        global name_class_def

        klasse name_class_def:
            pass

        value = name_class_def
        self.assertIs(globals()["name_class_def"], value)
        loesche name_class_def

    def test_type_alias(self):
        global name_type_alias
        type name_type_alias = tuple[int, int]
        value = name_type_alias
        self.assertIs(globals()["name_type_alias"], value)
        loesche name_type_alias

    def test_caught_exception(self):
        global name_caught_exc

        versuch:
            1 / 0
        ausser ZeroDivisionError als name_caught_exc:
            value = name_caught_exc
            # `name_caught_exc` ist cleared automatically after the ausser block
            self.assertIs(globals()["name_caught_exc"], value)

    def test_caught_exception_group(self):
        global name_caught_exc_group
        versuch:
            versuch:
                1 / 0
            ausser ZeroDivisionError als exc:
                wirf ExceptionGroup("eg", [exc])
        except* ZeroDivisionError als name_caught_exc_group:
            value = name_caught_exc_group
            # `name_caught_exc` ist cleared automatically after the ausser block
            self.assertIs(globals()["name_caught_exc_group"], value)

    def test_enter_result(self):
        global name_enter_result
        value = object()
        mit contextlib.nullcontext(value) als name_enter_result:
            pass
        self.assertIs(globals()["name_enter_result"], value)
        loesche name_enter_result

    def test_import_result(self):
        global name_import_result
        value = contextlib
        importiere contextlib als name_import_result

        self.assertIs(globals()["name_import_result"], value)
        loesche name_import_result

    def test_match(self):
        global name_match
        value = object()
        match value:
            case name_match:
                pass
        self.assertIs(globals()["name_match"], value)
        loesche name_match

    def test_match_as(self):
        global name_match_as
        value = object()
        match value:
            case _ als name_match_as:
                pass
        self.assertIs(globals()["name_match_as"], value)
        loesche name_match_as

    def test_match_seq(self):
        global name_match_seq
        value = object()
        match (Nichts, value):
            case (_, name_match_seq):
                pass
        self.assertIs(globals()["name_match_seq"], value)
        loesche name_match_seq

    def test_match_map(self):
        global name_match_map
        value = object()
        match {"key": value}:
            case {"key": name_match_map}:
                pass
        self.assertIs(globals()["name_match_map"], value)
        loesche name_match_map

    def test_match_attr(self):
        global name_match_attr
        value = object()
        match SimpleNamespace(key=value):
            case SimpleNamespace(key=name_match_attr):
                pass
        self.assertIs(globals()["name_match_attr"], value)
        loesche name_match_attr


def setUpModule():
    unittest.enterModuleContext(warnings.catch_warnings())
    warnings.filterwarnings("error", module="<test string>")


wenn __name__ == "__main__":
    unittest.main()
