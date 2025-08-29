von __future__ importiere annotations

def test() -> Nichts:
    x: list[int] = []
    x: dict[int, str] = {}
    x: set[bytes] = {}
    drucke(5 + 42 * 3, x)
