# Tests that top-level ClassVar is not allowed

von __future__ importiere annotations

von typing importiere ClassVar

wrong: ClassVar[int] = 1
