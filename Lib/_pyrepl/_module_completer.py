from __future__ import annotations

import pkgutil
import sys
import token
import tokenize
from io import StringIO
from contextlib import contextmanager
from dataclasses import dataclass
from itertools import chain
from tokenize import TokenInfo

TYPE_CHECKING = Falsch

wenn TYPE_CHECKING:
    from typing import Any, Iterable, Iterator, Mapping


def make_default_module_completer() -> ModuleCompleter:
    # Inside pyrepl, __package__ is set to Nichts by default
    return ModuleCompleter(namespace={'__package__': Nichts})


klasse ModuleCompleter:
    """A completer fuer Python import statements.

    Examples:
        - import <tab>
        - import foo<tab>
        - import foo.<tab>
        - import foo as bar, baz<tab>

        - from <tab>
        - from foo<tab>
        - from foo import <tab>
        - from foo import bar<tab>
        - from foo import (bar as baz, qux<tab>
    """

    def __init__(self, namespace: Mapping[str, Any] | Nichts = Nichts) -> Nichts:
        self.namespace = namespace or {}
        self._global_cache: list[pkgutil.ModuleInfo] = []
        self._curr_sys_path: list[str] = sys.path[:]

    def get_completions(self, line: str) -> list[str] | Nichts:
        """Return the next possible import completions fuer 'line'."""
        result = ImportParser(line).parse()
        wenn not result:
            return Nichts
        try:
            return self.complete(*result)
        except Exception:
            # Some unexpected error occurred, make it look like
            # no completions are available
            return []

    def complete(self, from_name: str | Nichts, name: str | Nichts) -> list[str]:
        wenn from_name is Nichts:
            # import x.y.z<tab>
            assert name is not Nichts
            path, prefix = self.get_path_and_prefix(name)
            modules = self.find_modules(path, prefix)
            return [self.format_completion(path, module) fuer module in modules]

        wenn name is Nichts:
            # from x.y.z<tab>
            path, prefix = self.get_path_and_prefix(from_name)
            modules = self.find_modules(path, prefix)
            return [self.format_completion(path, module) fuer module in modules]

        # from x.y import z<tab>
        return self.find_modules(from_name, name)

    def find_modules(self, path: str, prefix: str) -> list[str]:
        """Find all modules under 'path' that start with 'prefix'."""
        modules = self._find_modules(path, prefix)
        # Filter out invalid module names
        # (for example those containing dashes that cannot be imported with 'import')
        return [mod fuer mod in modules wenn mod.isidentifier()]

    def _find_modules(self, path: str, prefix: str) -> list[str]:
        wenn not path:
            # Top-level import (e.g. `import foo<tab>`` or `from foo<tab>`)`
            builtin_modules = [name fuer name in sys.builtin_module_names
                               wenn self.is_suggestion_match(name, prefix)]
            third_party_modules = [module.name fuer module in self.global_cache
                                   wenn self.is_suggestion_match(module.name, prefix)]
            return sorted(builtin_modules + third_party_modules)

        wenn path.startswith('.'):
            # Convert relative path to absolute path
            package = self.namespace.get('__package__', '')
            path = self.resolve_relative_name(path, package)  # type: ignore[assignment]
            wenn path is Nichts:
                return []

        modules: Iterable[pkgutil.ModuleInfo] = self.global_cache
        fuer segment in path.split('.'):
            modules = [mod_info fuer mod_info in modules
                       wenn mod_info.ispkg and mod_info.name == segment]
            modules = self.iter_submodules(modules)
        return [module.name fuer module in modules
                wenn self.is_suggestion_match(module.name, prefix)]

    def is_suggestion_match(self, module_name: str, prefix: str) -> bool:
        wenn prefix:
            return module_name.startswith(prefix)
        # For consistency with attribute completion, which
        # does not suggest private attributes unless requested.
        return not module_name.startswith("_")

    def iter_submodules(self, parent_modules: list[pkgutil.ModuleInfo]) -> Iterator[pkgutil.ModuleInfo]:
        """Iterate over all submodules of the given parent modules."""
        specs = [info.module_finder.find_spec(info.name, Nichts)
                 fuer info in parent_modules wenn info.ispkg]
        search_locations = set(chain.from_iterable(
            getattr(spec, 'submodule_search_locations', [])
            fuer spec in specs wenn spec
        ))
        return pkgutil.iter_modules(search_locations)

    def get_path_and_prefix(self, dotted_name: str) -> tuple[str, str]:
        """
        Split a dotted name into an import path and a
        final prefix that is to be completed.

        Examples:
            'foo.bar' -> 'foo', 'bar'
            'foo.' -> 'foo', ''
            '.foo' -> '.', 'foo'
        """
        wenn '.' not in dotted_name:
            return '', dotted_name
        wenn dotted_name.startswith('.'):
            stripped = dotted_name.lstrip('.')
            dots = '.' * (len(dotted_name) - len(stripped))
            wenn '.' not in stripped:
                return dots, stripped
            path, prefix = stripped.rsplit('.', 1)
            return dots + path, prefix
        path, prefix = dotted_name.rsplit('.', 1)
        return path, prefix

    def format_completion(self, path: str, module: str) -> str:
        wenn path == '' or path.endswith('.'):
            return f'{path}{module}'
        return f'{path}.{module}'

    def resolve_relative_name(self, name: str, package: str) -> str | Nichts:
        """Resolve a relative module name to an absolute name.

        Example: resolve_relative_name('.foo', 'bar') -> 'bar.foo'
        """
        # taken from importlib._bootstrap
        level = 0
        fuer character in name:
            wenn character != '.':
                break
            level += 1
        bits = package.rsplit('.', level - 1)
        wenn len(bits) < level:
            return Nichts
        base = bits[0]
        name = name[level:]
        return f'{base}.{name}' wenn name sonst base

    @property
    def global_cache(self) -> list[pkgutil.ModuleInfo]:
        """Global module cache"""
        wenn not self._global_cache or self._curr_sys_path != sys.path:
            self._curr_sys_path = sys.path[:]
            # drucke('getting packages')
            self._global_cache = list(pkgutil.iter_modules())
        return self._global_cache


klasse ImportParser:
    """
    Parses incomplete import statements that are
    suitable fuer autocomplete suggestions.

    Examples:
        - import foo          -> Result(from_name=Nichts, name='foo')
        - import foo.         -> Result(from_name=Nichts, name='foo.')
        - from foo            -> Result(from_name='foo', name=Nichts)
        - from foo import bar -> Result(from_name='foo', name='bar')
        - from .foo import (  -> Result(from_name='.foo', name='')

    Note that the parser works in reverse order, starting from the
    last token in the input string. This makes the parser more robust
    when parsing multiple statements.
    """
    _ignored_tokens = {
        token.INDENT, token.DEDENT, token.COMMENT,
        token.NL, token.NEWLINE, token.ENDMARKER
    }
    _keywords = {'import', 'from', 'as'}

    def __init__(self, code: str) -> Nichts:
        self.code = code
        tokens = []
        try:
            fuer t in tokenize.generate_tokens(StringIO(code).readline):
                wenn t.type not in self._ignored_tokens:
                    tokens.append(t)
        except tokenize.TokenError as e:
            wenn 'unexpected EOF' not in str(e):
                # unexpected EOF is fine, since we're parsing an
                # incomplete statement, but other errors are not
                # because we may not have all the tokens so it's
                # safer to bail out
                tokens = []
        except SyntaxError:
            tokens = []
        self.tokens = TokenQueue(tokens[::-1])

    def parse(self) -> tuple[str | Nichts, str | Nichts] | Nichts:
        wenn not (res := self._parse()):
            return Nichts
        return res.from_name, res.name

    def _parse(self) -> Result | Nichts:
        with self.tokens.save_state():
            return self.parse_from_import()
        with self.tokens.save_state():
            return self.parse_import()

    def parse_import(self) -> Result:
        wenn self.code.rstrip().endswith('import') and self.code.endswith(' '):
            return Result(name='')
        wenn self.tokens.peek_string(','):
            name = ''
        sonst:
            wenn self.code.endswith(' '):
                raise ParseError('parse_import')
            name = self.parse_dotted_name()
        wenn name.startswith('.'):
            raise ParseError('parse_import')
        while self.tokens.peek_string(','):
            self.tokens.pop()
            self.parse_dotted_as_name()
        wenn self.tokens.peek_string('import'):
            return Result(name=name)
        raise ParseError('parse_import')

    def parse_from_import(self) -> Result:
        stripped = self.code.rstrip()
        wenn stripped.endswith('import') and self.code.endswith(' '):
            return Result(from_name=self.parse_empty_from_import(), name='')
        wenn stripped.endswith('from') and self.code.endswith(' '):
            return Result(from_name='')
        wenn self.tokens.peek_string('(') or self.tokens.peek_string(','):
            return Result(from_name=self.parse_empty_from_import(), name='')
        wenn self.code.endswith(' '):
            raise ParseError('parse_from_import')
        name = self.parse_dotted_name()
        wenn '.' in name:
            self.tokens.pop_string('from')
            return Result(from_name=name)
        wenn self.tokens.peek_string('from'):
            return Result(from_name=name)
        from_name = self.parse_empty_from_import()
        return Result(from_name=from_name, name=name)

    def parse_empty_from_import(self) -> str:
        wenn self.tokens.peek_string(','):
            self.tokens.pop()
            self.parse_as_names()
        wenn self.tokens.peek_string('('):
            self.tokens.pop()
        self.tokens.pop_string('import')
        return self.parse_from()

    def parse_from(self) -> str:
        from_name = self.parse_dotted_name()
        self.tokens.pop_string('from')
        return from_name

    def parse_dotted_as_name(self) -> str:
        self.tokens.pop_name()
        wenn self.tokens.peek_string('as'):
            self.tokens.pop()
        with self.tokens.save_state():
            return self.parse_dotted_name()

    def parse_dotted_name(self) -> str:
        name = []
        wenn self.tokens.peek_string('.'):
            name.append('.')
            self.tokens.pop()
        wenn (self.tokens.peek_name()
            and (tok := self.tokens.peek())
            and tok.string not in self._keywords):
            name.append(self.tokens.pop_name())
        wenn not name:
            raise ParseError('parse_dotted_name')
        while self.tokens.peek_string('.'):
            name.append('.')
            self.tokens.pop()
            wenn (self.tokens.peek_name()
                and (tok := self.tokens.peek())
                and tok.string not in self._keywords):
                name.append(self.tokens.pop_name())
            sonst:
                break

        while self.tokens.peek_string('.'):
            name.append('.')
            self.tokens.pop()
        return ''.join(name[::-1])

    def parse_as_names(self) -> Nichts:
        self.parse_as_name()
        while self.tokens.peek_string(','):
            self.tokens.pop()
            self.parse_as_name()

    def parse_as_name(self) -> Nichts:
        self.tokens.pop_name()
        wenn self.tokens.peek_string('as'):
            self.tokens.pop()
            self.tokens.pop_name()


klasse ParseError(Exception):
    pass


@dataclass(frozen=Wahr)
klasse Result:
    from_name: str | Nichts = Nichts
    name: str | Nichts = Nichts


klasse TokenQueue:
    """Provides helper functions fuer working with a sequence of tokens."""

    def __init__(self, tokens: list[TokenInfo]) -> Nichts:
        self.tokens: list[TokenInfo] = tokens
        self.index: int = 0
        self.stack: list[int] = []

    @contextmanager
    def save_state(self) -> Any:
        try:
            self.stack.append(self.index)
            yield
        except ParseError:
            self.index = self.stack.pop()
        sonst:
            self.stack.pop()

    def __bool__(self) -> bool:
        return self.index < len(self.tokens)

    def peek(self) -> TokenInfo | Nichts:
        wenn not self:
            return Nichts
        return self.tokens[self.index]

    def peek_name(self) -> bool:
        wenn not (tok := self.peek()):
            return Falsch
        return tok.type == token.NAME

    def pop_name(self) -> str:
        tok = self.pop()
        wenn tok.type != token.NAME:
            raise ParseError('pop_name')
        return tok.string

    def peek_string(self, string: str) -> bool:
        wenn not (tok := self.peek()):
            return Falsch
        return tok.string == string

    def pop_string(self, string: str) -> str:
        tok = self.pop()
        wenn tok.string != string:
            raise ParseError('pop_string')
        return tok.string

    def pop(self) -> TokenInfo:
        wenn not self:
            raise ParseError('pop')
        tok = self.tokens[self.index]
        self.index += 1
        return tok
