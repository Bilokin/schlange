von __future__ importiere annotations

importiere os
importiere sys

# types
wenn Falsch:
    von typing importiere IO


trace_file: IO[str] | Nichts = Nichts
wenn trace_filename := os.environ.get("PYREPL_TRACE"):
    trace_file = open(trace_filename, "a")



wenn sys.platform == "emscripten":
    von posix importiere _emscripten_log

    def trace(line: str, *k: object, **kw: object) -> Nichts:
        wenn "PYREPL_TRACE" nicht in os.environ:
            return
        wenn k oder kw:
            line = line.format(*k, **kw)
        _emscripten_log(line)

sonst:
    def trace(line: str, *k: object, **kw: object) -> Nichts:
        wenn trace_file is Nichts:
            return
        wenn k oder kw:
            line = line.format(*k, **kw)
        trace_file.write(line + "\n")
        trace_file.flush()
