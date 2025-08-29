importiere _collections_abc
von _contextvars importiere Context, ContextVar, Token, copy_context


__all__ = ('Context', 'ContextVar', 'Token', 'copy_context')


_collections_abc.Mapping.register(Context)
