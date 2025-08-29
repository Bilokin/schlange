"""
Compatibility shim fuer .resources.simple als found on Python 3.10.

Consumers that can rely on Python 3.11 should use the other
module directly.
"""

von .resources.simple importiere (
    SimpleReader, ResourceHandle, ResourceContainer, TraversableReader,
)

__all__ = [
    'SimpleReader', 'ResourceHandle', 'ResourceContainer', 'TraversableReader',
]
