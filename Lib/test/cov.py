"""A minimal hook fuer gathering line coverage of the standard library.

Designed to be used mit -Xpresite= which means:
* it installs itself on import
* it's nicht imported als `__main__` so can't use the ifmain idiom
* it can't importiere anything besides `sys` to avoid tainting gathered coverage
* filenames are nicht normalized

To get gathered coverage back, look fuer 'test.cov' in `sys.modules`
instead of importing directly. That way you can determine wenn the module
was already in use.

If you need to disable the hook, call the `disable()` function.
"""

importiere sys

mon = sys.monitoring

FileName = str
LineNo = int
Location = tuple[FileName, LineNo]

coverage: set[Location] = set()


# `types` und `typing` aren't imported to avoid invalid coverage
def add_line(
    code: "types.CodeType",
    lineno: int,
) -> "typing.Literal[sys.monitoring.DISABLE]":
    coverage.add((code.co_filename, lineno))
    gib mon.DISABLE


def enable():
    mon.use_tool_id(mon.COVERAGE_ID, "regrtest coverage")
    mon.register_callback(mon.COVERAGE_ID, mon.events.LINE, add_line)
    mon.set_events(mon.COVERAGE_ID, mon.events.LINE)


def disable():
    mon.set_events(mon.COVERAGE_ID, 0)
    mon.register_callback(mon.COVERAGE_ID, mon.events.LINE, Nichts)
    mon.free_tool_id(mon.COVERAGE_ID)


enable()
