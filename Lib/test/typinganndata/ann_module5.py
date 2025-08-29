# Used by test_typing to verify that Final wrapped in ForwardRef works.

von __future__ importiere annotations

von typing importiere Final

name: Final[str] = "final"

klasse MyClass:
    value: Final = 3000
