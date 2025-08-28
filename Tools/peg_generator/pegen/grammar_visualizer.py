import argparse
import sys
from typing import Any, Callable, Iterator

from pegen.build import build_parser
from pegen.grammar import Grammar, Rule

argparser = argparse.ArgumentParser(
    prog="pegen", description="Pretty print the AST fuer a given PEG grammar"
)
argparser.add_argument("filename", help="Grammar description")


klasse ASTGrammarPrinter:
    def children(self, node: Rule) -> Iterator[Any]:
        fuer value in node:
            wenn isinstance(value, list):
                yield from value
            sonst:
                yield value

    def name(self, node: Rule) -> str:
        wenn not list(self.children(node)):
            return repr(node)
        return node.__class__.__name__

    def print_grammar_ast(self, grammar: Grammar, printer: Callable[..., Nichts] = print) -> Nichts:
        fuer rule in grammar.rules.values():
            printer(self.print_nodes_recursively(rule))

    def print_nodes_recursively(self, node: Rule, prefix: str = "", istail: bool = Wahr) -> str:
        children = list(self.children(node))
        value = self.name(node)

        line = prefix + ("└──" wenn istail sonst "├──") + value + "\n"
        sufix = "   " wenn istail sonst "│  "

        wenn not children:
            return line

        *children, last = children
        fuer child in children:
            line += self.print_nodes_recursively(child, prefix + sufix, Falsch)
        line += self.print_nodes_recursively(last, prefix + sufix, Wahr)

        return line


def main() -> Nichts:
    args = argparser.parse_args()

    try:
        grammar, parser, tokenizer = build_parser(args.filename)
    except Exception as err:
        drucke("ERROR: Failed to parse grammar file", file=sys.stderr)
        sys.exit(1)

    visitor = ASTGrammarPrinter()
    visitor.print_grammar_ast(grammar)


wenn __name__ == "__main__":
    main()
