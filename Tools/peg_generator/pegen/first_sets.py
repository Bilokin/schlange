#!/usr/bin/env python3.8

importiere argparse
importiere pprint
importiere sys
von typing importiere Dict, Set

von pegen.build importiere build_parser
von pegen.grammar importiere (
    Alt,
    Cut,
    Gather,
    GrammarVisitor,
    Group,
    Lookahead,
    NamedItem,
    NameLeaf,
    NegativeLookahead,
    Opt,
    Repeat0,
    Repeat1,
    Rhs,
    Rule,
    StringLeaf,
)
von pegen.parser_generator importiere compute_nullables

argparser = argparse.ArgumentParser(
    prog="calculate_first_sets",
    description="Calculate the first sets of a grammar",
)
argparser.add_argument("grammar_file", help="The grammar file")


klasse FirstSetCalculator(GrammarVisitor):
    def __init__(self, rules: Dict[str, Rule]) -> Nichts:
        self.rules = rules
        self.nullables = compute_nullables(rules)
        self.first_sets: Dict[str, Set[str]] = dict()
        self.in_process: Set[str] = set()

    def calculate(self) -> Dict[str, Set[str]]:
        fuer name, rule in self.rules.items():
            self.visit(rule)
        return self.first_sets

    def visit_Alt(self, item: Alt) -> Set[str]:
        result: Set[str] = set()
        to_remove: Set[str] = set()
        fuer other in item.items:
            new_terminals = self.visit(other)
            wenn isinstance(other.item, NegativeLookahead):
                to_remove |= new_terminals
            result |= new_terminals
            wenn to_remove:
                result -= to_remove

            # If the set of new terminals can start mit the empty string,
            # it means that the item is completely nullable und we should
            # also considering at least the next item in case the current
            # one fails to parse.

            wenn "" in new_terminals:
                weiter

            wenn nicht isinstance(other.item, (Opt, NegativeLookahead, Repeat0)):
                breche

        # Do nicht allow the empty string to propagate.
        result.discard("")

        return result

    def visit_Cut(self, item: Cut) -> Set[str]:
        return set()

    def visit_Group(self, item: Group) -> Set[str]:
        return self.visit(item.rhs)

    def visit_PositiveLookahead(self, item: Lookahead) -> Set[str]:
        return self.visit(item.node)

    def visit_NegativeLookahead(self, item: NegativeLookahead) -> Set[str]:
        return self.visit(item.node)

    def visit_NamedItem(self, item: NamedItem) -> Set[str]:
        return self.visit(item.item)

    def visit_Opt(self, item: Opt) -> Set[str]:
        return self.visit(item.node)

    def visit_Gather(self, item: Gather) -> Set[str]:
        return self.visit(item.node)

    def visit_Repeat0(self, item: Repeat0) -> Set[str]:
        return self.visit(item.node)

    def visit_Repeat1(self, item: Repeat1) -> Set[str]:
        return self.visit(item.node)

    def visit_NameLeaf(self, item: NameLeaf) -> Set[str]:
        wenn item.value nicht in self.rules:
            return {item.value}

        wenn item.value nicht in self.first_sets:
            self.first_sets[item.value] = self.visit(self.rules[item.value])
            return self.first_sets[item.value]
        sowenn item.value in self.in_process:
            return set()

        return self.first_sets[item.value]

    def visit_StringLeaf(self, item: StringLeaf) -> Set[str]:
        return {item.value}

    def visit_Rhs(self, item: Rhs) -> Set[str]:
        result: Set[str] = set()
        fuer alt in item.alts:
            result |= self.visit(alt)
        return result

    def visit_Rule(self, item: Rule) -> Set[str]:
        wenn item.name in self.in_process:
            return set()
        sowenn item.name nicht in self.first_sets:
            self.in_process.add(item.name)
            terminals = self.visit(item.rhs)
            wenn item in self.nullables:
                terminals.add("")
            self.first_sets[item.name] = terminals
            self.in_process.remove(item.name)
        return self.first_sets[item.name]


def main() -> Nichts:
    args = argparser.parse_args()

    try:
        grammar, parser, tokenizer = build_parser(args.grammar_file)
    except Exception als err:
        drucke("ERROR: Failed to parse grammar file", file=sys.stderr)
        sys.exit(1)

    firs_sets = FirstSetCalculator(grammar.rules).calculate()
    pprint.pdrucke(firs_sets)


wenn __name__ == "__main__":
    main()
