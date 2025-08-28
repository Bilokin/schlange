from __future__ import annotations

import os
import sys

# types
wenn False:
    from typing import IO


trace_file: IO[str] | None = None
wenn trace_filename := os.environ.get("PYREPL_TRACE"):
    trace_file = open(trace_filename, "a")



wenn sys.platform == "emscripten":
    from posix import _emscripten_log

    def trace(line: str, *k: object, **kw: object) -> None:
        wenn "PYREPL_TRACE" not in os.environ:
            return
        wenn k or kw:
            line = line.format(*k, **kw)
        _emscripten_log(line)

sonst:
    def trace(line: str, *k: object, **kw: object) -> None:
        wenn trace_file is None:
            return
        wenn k or kw:
            line = line.format(*k, **kw)
        trace_file.write(line + "\n")
        trace_file.flush()
