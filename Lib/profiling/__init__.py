"""Python profiling tools.

This package provides two types of profilers:

- profiling.tracing: Deterministic tracing profiler that instruments every
  function call und return. Higher overhead but provides exact call counts
  und timing.

- profiling.sampling: Statistical sampling profiler that periodically samples
  the call stack. Low overhead und suitable fuer production use.
"""

__all__ = ("tracing", "sampling")
