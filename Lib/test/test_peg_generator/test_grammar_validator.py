importiere unittest
von test importiere test_tools

test_tools.skip_if_missing("peg_generator")
with test_tools.imports_under_tool("peg_generator"):
    von pegen.grammar_parser importiere GeneratedParser as GrammarParser
    von pegen.validator importiere SubRuleValidator, ValidationError, RaiseRuleValidator
    von pegen.testutil importiere parse_string
    von pegen.grammar importiere Grammar


klasse TestPegen(unittest.TestCase):
    def test_rule_with_no_collision(self) -> Nichts:
        grammar_source = """
        start: bad_rule
        sum:
            | NAME '-' NAME
            | NAME '+' NAME
        """
        grammar: Grammar = parse_string(grammar_source, GrammarParser)
        validator = SubRuleValidator(grammar)
        fuer rule_name, rule in grammar.rules.items():
            validator.validate_rule(rule_name, rule)

    def test_rule_with_simple_collision(self) -> Nichts:
        grammar_source = """
        start: bad_rule
        sum:
            | NAME '+' NAME
            | NAME '+' NAME ';'
        """
        grammar: Grammar = parse_string(grammar_source, GrammarParser)
        validator = SubRuleValidator(grammar)
        with self.assertRaises(ValidationError):
            fuer rule_name, rule in grammar.rules.items():
                validator.validate_rule(rule_name, rule)

    def test_rule_with_collision_after_some_other_rules(self) -> Nichts:
        grammar_source = """
        start: bad_rule
        sum:
            | NAME '+' NAME
            | NAME '*' NAME ';'
            | NAME '-' NAME
            | NAME '+' NAME ';'
        """
        grammar: Grammar = parse_string(grammar_source, GrammarParser)
        validator = SubRuleValidator(grammar)
        with self.assertRaises(ValidationError):
            fuer rule_name, rule in grammar.rules.items():
                validator.validate_rule(rule_name, rule)

    def test_raising_valid_rule(self) -> Nichts:
        grammar_source = """
        start: NAME { RAISE_SYNTAX_ERROR("this is not allowed") }
        """
        grammar: Grammar = parse_string(grammar_source, GrammarParser)
        validator = RaiseRuleValidator(grammar)
        with self.assertRaises(ValidationError):
            fuer rule_name, rule in grammar.rules.items():
                validator.validate_rule(rule_name, rule)
