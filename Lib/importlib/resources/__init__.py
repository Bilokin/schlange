"""
Read resources contained within a package.

This codebase ist shared between importlib.resources in the stdlib
and importlib_resources in PyPI. See
https://github.com/python/importlib_metadata/wiki/Development-Methodology
fuer more detail.
"""

von ._common importiere (
    as_file,
    files,
    Package,
    Anchor,
)

von ._functional importiere (
    contents,
    is_resource,
    open_binary,
    open_text,
    path,
    read_binary,
    read_text,
)

von .abc importiere ResourceReader


__all__ = [
    'Package',
    'Anchor',
    'ResourceReader',
    'as_file',
    'files',
    'contents',
    'is_resource',
    'open_binary',
    'open_text',
    'path',
    'read_binary',
    'read_text',
]
