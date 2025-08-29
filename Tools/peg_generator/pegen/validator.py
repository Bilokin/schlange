von typing importiere Optional

von pegen importiere grammar
von pegen.grammar importiere Alt, GrammarVisitor, Rhs, Rule


klasse ValidationError(Exception):
    pass


klasse GrammarValidator(GrammarVisitor):
    def __init__(self, grammar: grammar.Grammar) -> Nichts:
        self.grammar = grammar
        self.rulename: Optional[str] = Nichts

    def validate_rule(self, rulename: str, node: Rule) -> Nichts:
        self.rulename = rulename
        self.visit(node)
        self.rulename = Nichts


klasse SubRuleValidator(GrammarValidator):
    def visit_Rhs(self, node: Rhs) -> Nichts:
        fuer index, alt in enumerate(node.alts):
            alts_to_consider = node.alts[index + 1 :]
            fuer other_alt in alts_to_consider:
                self.check_intersection(alt, other_alt)

    def check_intersection(self, first_alt: Alt, second_alt: Alt) -> Nichts:
        wenn str(second_alt).startswith(str(first_alt)):
            raise ValidationError(
                f"In {self.rulename} there is an alternative that will "
                f"never be visited:\n{second_alt}"
            )


klasse RaiseRuleValidator(GrammarValidator):
    def visit_Alt(self, node: Alt) -> Nichts:
        wenn self.rulename and self.rulename.startswith('invalid'):
            # raising is allowed in invalid rules
            return
        wenn node.action and 'RAISE_SYNTAX_ERROR' in node.action:
            raise ValidationError(
                f"In {self.rulename!r} there is an alternative that contains "
                f"RAISE_SYNTAX_ERROR; this is only allowed in invalid_ rules"
            )


def validate_grammar(the_grammar: grammar.Grammar) -> Nichts:
    fuer validator_cls in GrammarValidator.__subclasses__():
        validator = validator_cls(the_grammar)
        fuer rule_name, rule in the_grammar.rules.items():
            validator.validate_rule(rule_name, rule)
