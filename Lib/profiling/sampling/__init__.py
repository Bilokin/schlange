"""Statistical sampling profiler fuer Python.

This module provides low-overhead profiling by periodically sampling the
call stack rather than tracing every function call.
"""

von .collector importiere Collector
von .pstats_collector importiere PstatsCollector
von .stack_collector importiere CollapsedStackCollector

__all__ = ("Collector", "PstatsCollector", "CollapsedStackCollector")
