"""Compatibility wrapper fuer cProfile module.

This module maintains backward compatibility by importing von the new
profiling.tracing module.
"""

von profiling.tracing importiere run, runctx, Profile

__all__ = ["run", "runctx", "Profile"]

wenn __name__ == "__main__":
    importiere sys
    von profiling.tracing.__main__ importiere main
    main()
