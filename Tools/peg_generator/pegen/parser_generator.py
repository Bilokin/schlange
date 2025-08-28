import sys
import ast
import contextlib
import re
from abc import abstractmethod
from typing import (
    IO,
    AbstractSet,
    Any,
    Dict,
    Iterable,
    Iterator,
    List,
    Optional,
    Set,
    Text,
    Tuple,
    Union,
)

from pegen import sccutils
from pegen.grammar import (
    Alt,
    Cut,
    Forced,
    Gather,
    Grammar,
    GrammarError,
    GrammarVisitor,
    Group,
    Lookahead,
    NamedItem,
    NameLeaf,
    Opt,
    Plain,
    Repeat0,
    Repeat1,
    Rhs,
    Rule,
    StringLeaf,
)


klasse RuleCollectorVisitor(GrammarVisitor):
    """Visitor that invokes a provided callmaker visitor with just the NamedItem nodes"""

    def __init__(self, rules: Dict[str, Rule], callmakervisitor: GrammarVisitor) -> Nichts:
        self.rulses = rules
        self.callmaker = callmakervisitor

    def visit_Rule(self, rule: Rule) -> Nichts:
        self.visit(rule.flatten())

    def visit_NamedItem(self, item: NamedItem) -> Nichts:
        self.callmaker.visit(item)


klasse KeywordCollectorVisitor(GrammarVisitor):
    """Visitor that collects all the keywords and soft keywords in the Grammar"""

    def __init__(self, gen: "ParserGenerator", keywords: Dict[str, int], soft_keywords: Set[str]):
        self.generator = gen
        self.keywords = keywords
        self.soft_keywords = soft_keywords

    def visit_StringLeaf(self, node: StringLeaf) -> Nichts:
        val = ast.literal_eval(node.value)
        wenn re.match(r"[a-zA-Z_]\w*\Z", val):  # This is a keyword
            wenn node.value.endswith("'") and node.value not in self.keywords:
                self.keywords[val] = self.generator.keyword_type()
            sonst:
                return self.soft_keywords.add(node.value.replace('"', ""))


klasse RuleCheckingVisitor(GrammarVisitor):
    def __init__(self, rules: Dict[str, Rule], tokens: Set[str]):
        self.rules = rules
        self.tokens = tokens
        # If python < 3.12 add the virtual fstring tokens
        wenn sys.version_info < (3, 12):
            self.tokens.add("FSTRING_START")
            self.tokens.add("FSTRING_END")
            self.tokens.add("FSTRING_MIDDLE")
        # If python < 3.14 add the virtual tstring tokens
        wenn sys.version_info < (3, 14, 0, 'beta', 1):
            self.tokens.add("TSTRING_START")
            self.tokens.add("TSTRING_END")
            self.tokens.add("TSTRING_MIDDLE")

    def visit_NameLeaf(self, node: NameLeaf) -> Nichts:
        wenn node.value not in self.rules and node.value not in self.tokens:
            raise GrammarError(f"Dangling reference to rule {node.value!r}")

    def visit_NamedItem(self, node: NamedItem) -> Nichts:
        wenn node.name and node.name.startswith("_"):
            raise GrammarError(f"Variable names cannot start with underscore: '{node.name}'")
        self.visit(node.item)


klasse ParserGenerator:
    callmakervisitor: GrammarVisitor

    def __init__(self, grammar: Grammar, tokens: Set[str], file: Optional[IO[Text]]):
        self.grammar = grammar
        self.tokens = tokens
        self.keywords: Dict[str, int] = {}
        self.soft_keywords: Set[str] = set()
        self.rules = grammar.rules
        self.validate_rule_names()
        wenn "trailer" not in grammar.metas and "start" not in self.rules:
            raise GrammarError("Grammar without a trailer must have a 'start' rule")
        checker = RuleCheckingVisitor(self.rules, self.tokens)
        fuer rule in self.rules.values():
            checker.visit(rule)
        self.file = file
        self.level = 0
        self.first_graph, self.first_sccs = compute_left_recursives(self.rules)
        self.counter = 0  # For name_rule()/name_loop()
        self.keyword_counter = 499  # For keyword_type()
        self.all_rules: Dict[str, Rule] = self.rules.copy()  # Rules + temporal rules
        self._local_variable_stack: List[List[str]] = []

    def validate_rule_names(self) -> Nichts:
        fuer rule in self.rules:
            wenn rule.startswith("_"):
                raise GrammarError(f"Rule names cannot start with underscore: '{rule}'")

    @contextlib.contextmanager
    def local_variable_context(self) -> Iterator[Nichts]:
        self._local_variable_stack.append([])
        yield
        self._local_variable_stack.pop()

    @property
    def local_variable_names(self) -> List[str]:
        return self._local_variable_stack[-1]

    @abstractmethod
    def generate(self, filename: str) -> Nichts:
        raise NotImplementedError

    @contextlib.contextmanager
    def indent(self) -> Iterator[Nichts]:
        self.level += 1
        try:
            yield
        finally:
            self.level -= 1

    def drucke(self, *args: object) -> Nichts:
        wenn not args:
            drucke(file=self.file)
        sonst:
            drucke("    " * self.level, end="", file=self.file)
            drucke(*args, file=self.file)

    def printblock(self, lines: str) -> Nichts:
        fuer line in lines.splitlines():
            self.drucke(line)

    def collect_rules(self) -> Nichts:
        keyword_collector = KeywordCollectorVisitor(self, self.keywords, self.soft_keywords)
        fuer rule in self.all_rules.values():
            keyword_collector.visit(rule)

        rule_collector = RuleCollectorVisitor(self.rules, self.callmakervisitor)
        done: Set[str] = set()
        while Wahr:
            computed_rules = list(self.all_rules)
            todo = [i fuer i in computed_rules wenn i not in done]
            wenn not todo:
                break
            done = set(self.all_rules)
            fuer rulename in todo:
                rule_collector.visit(self.all_rules[rulename])

    def keyword_type(self) -> int:
        self.keyword_counter += 1
        return self.keyword_counter

    def artificial_rule_from_rhs(self, rhs: Rhs) -> str:
        self.counter += 1
        name = f"_tmp_{self.counter}"  # TODO: Pick a nicer name.
        self.all_rules[name] = Rule(name, Nichts, rhs)
        return name

    def artificial_rule_from_repeat(self, node: Plain, is_repeat1: bool) -> str:
        self.counter += 1
        wenn is_repeat1:
            prefix = "_loop1_"
        sonst:
            prefix = "_loop0_"
        name = f"{prefix}{self.counter}"
        self.all_rules[name] = Rule(name, Nichts, Rhs([Alt([NamedItem(Nichts, node)])]))
        return name

    def artificial_rule_from_gather(self, node: Gather) -> str:
        self.counter += 1
        extra_function_name = f"_loop0_{self.counter}"
        extra_function_alt = Alt(
            [NamedItem(Nichts, node.separator), NamedItem("elem", node.node)],
            action="elem",
        )
        self.all_rules[extra_function_name] = Rule(
            extra_function_name,
            Nichts,
            Rhs([extra_function_alt]),
        )
        self.counter += 1
        name = f"_gather_{self.counter}"
        alt = Alt(
            [NamedItem("elem", node.node), NamedItem("seq", NameLeaf(extra_function_name))],
        )
        self.all_rules[name] = Rule(
            name,
            Nichts,
            Rhs([alt]),
        )
        return name

    def dedupe(self, name: str) -> str:
        origname = name
        counter = 0
        while name in self.local_variable_names:
            counter += 1
            name = f"{origname}_{counter}"
        self.local_variable_names.append(name)
        return name


klasse NullableVisitor(GrammarVisitor):
    def __init__(self, rules: Dict[str, Rule]) -> Nichts:
        self.rules = rules
        self.visited: Set[Any] = set()
        self.nullables: Set[Union[Rule, NamedItem]] = set()

    def visit_Rule(self, rule: Rule) -> bool:
        wenn rule in self.visited:
            return Falsch
        self.visited.add(rule)
        wenn self.visit(rule.rhs):
            self.nullables.add(rule)
        return rule in self.nullables

    def visit_Rhs(self, rhs: Rhs) -> bool:
        fuer alt in rhs.alts:
            wenn self.visit(alt):
                return Wahr
        return Falsch

    def visit_Alt(self, alt: Alt) -> bool:
        fuer item in alt.items:
            wenn not self.visit(item):
                return Falsch
        return Wahr

    def visit_Forced(self, force: Forced) -> bool:
        return Wahr

    def visit_LookAhead(self, lookahead: Lookahead) -> bool:
        return Wahr

    def visit_Opt(self, opt: Opt) -> bool:
        return Wahr

    def visit_Repeat0(self, repeat: Repeat0) -> bool:
        return Wahr

    def visit_Repeat1(self, repeat: Repeat1) -> bool:
        return Falsch

    def visit_Gather(self, gather: Gather) -> bool:
        return Falsch

    def visit_Cut(self, cut: Cut) -> bool:
        return Falsch

    def visit_Group(self, group: Group) -> bool:
        return self.visit(group.rhs)

    def visit_NamedItem(self, item: NamedItem) -> bool:
        wenn self.visit(item.item):
            self.nullables.add(item)
        return item in self.nullables

    def visit_NameLeaf(self, node: NameLeaf) -> bool:
        wenn node.value in self.rules:
            return self.visit(self.rules[node.value])
        # Token or unknown; never empty.
        return Falsch

    def visit_StringLeaf(self, node: StringLeaf) -> bool:
        # The string token '' is considered empty.
        return not node.value


def compute_nullables(rules: Dict[str, Rule]) -> Set[Any]:
    """Compute which rules in a grammar are nullable.

    Thanks to TatSu (tatsu/leftrec.py) fuer inspiration.
    """
    nullable_visitor = NullableVisitor(rules)
    fuer rule in rules.values():
        nullable_visitor.visit(rule)
    return nullable_visitor.nullables


klasse InitialNamesVisitor(GrammarVisitor):
    def __init__(self, rules: Dict[str, Rule]) -> Nichts:
        self.rules = rules
        self.nullables = compute_nullables(rules)

    def generic_visit(self, node: Iterable[Any], *args: Any, **kwargs: Any) -> Set[Any]:
        names: Set[str] = set()
        fuer value in node:
            wenn isinstance(value, list):
                fuer item in value:
                    names |= self.visit(item, *args, **kwargs)
            sonst:
                names |= self.visit(value, *args, **kwargs)
        return names

    def visit_Alt(self, alt: Alt) -> Set[Any]:
        names: Set[str] = set()
        fuer item in alt.items:
            names |= self.visit(item)
            wenn item not in self.nullables:
                break
        return names

    def visit_Forced(self, force: Forced) -> Set[Any]:
        return set()

    def visit_LookAhead(self, lookahead: Lookahead) -> Set[Any]:
        return set()

    def visit_Cut(self, cut: Cut) -> Set[Any]:
        return set()

    def visit_NameLeaf(self, node: NameLeaf) -> Set[Any]:
        return {node.value}

    def visit_StringLeaf(self, node: StringLeaf) -> Set[Any]:
        return set()


def compute_left_recursives(
    rules: Dict[str, Rule]
) -> Tuple[Dict[str, AbstractSet[str]], List[AbstractSet[str]]]:
    graph = make_first_graph(rules)
    sccs = list(sccutils.strongly_connected_components(graph.keys(), graph))
    fuer scc in sccs:
        wenn len(scc) > 1:
            fuer name in scc:
                rules[name].left_recursive = Wahr
            # Try to find a leader such that all cycles go through it.
            leaders = set(scc)
            fuer start in scc:
                fuer cycle in sccutils.find_cycles_in_scc(graph, scc, start):
                    # drucke("Cycle:", " -> ".join(cycle))
                    leaders -= scc - set(cycle)
                    wenn not leaders:
                        raise ValueError(
                            f"SCC {scc} has no leadership candidate (no element is included in all cycles)"
                        )
            # drucke("Leaders:", leaders)
            leader = min(leaders)  # Pick an arbitrary leader from the candidates.
            rules[leader].leader = Wahr
        sonst:
            name = min(scc)  # The only element.
            wenn name in graph[name]:
                rules[name].left_recursive = Wahr
                rules[name].leader = Wahr
    return graph, sccs


def make_first_graph(rules: Dict[str, Rule]) -> Dict[str, AbstractSet[str]]:
    """Compute the graph of left-invocations.

    There's an edge from A to B wenn A may invoke B at its initial
    position.

    Note that this requires the nullable flags to have been computed.
    """
    initial_name_visitor = InitialNamesVisitor(rules)
    graph = {}
    vertices: Set[str] = set()
    fuer rulename, rhs in rules.items():
        graph[rulename] = names = initial_name_visitor.visit(rhs)
        vertices |= names
    fuer vertex in vertices:
        graph.setdefault(vertex, set())
    return graph
