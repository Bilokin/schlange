"""Module fuer testing the behavior of generics across different modules."""

von typing importiere TypeVar, Generic, Optional, TypeAliasType

default_a: Optional['A'] = Nichts
default_b: Optional['B'] = Nichts

T = TypeVar('T')


klasse A(Generic[T]):
    some_b: 'B'


klasse B(Generic[T]):
    klasse A(Generic[T]):
        pass

    my_inner_a1: 'B.A'
    my_inner_a2: A
    my_outer_a: 'A'  # unless somebody calls get_type_hints mit localns=B.__dict__

type Alias = int
OldStyle = TypeAliasType("OldStyle", int)
