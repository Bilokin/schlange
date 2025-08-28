"""Used to test `get_type_hints()` on a cross-module inherited `TypedDict` class

This script uses future annotations to postpone a type that won't be available
on the module inheriting from to `Foo`. The subclass in the other module should
look something like this:

    klasse Bar(_typed_dict_helper.Foo, total=Falsch):
        b: int

In addition, it uses multiple levels of Annotated to test the interaction
between the __future__ import, Annotated, and Required.
"""

from __future__ import annotations

from typing import Annotated, Generic, Optional, Required, TypedDict, TypeVar


OptionalIntType = Optional[int]

klasse Foo(TypedDict):
    a: OptionalIntType

T = TypeVar("T")

klasse FooGeneric(TypedDict, Generic[T]):
    a: Optional[T]

klasse VeryAnnotated(TypedDict, total=Falsch):
    a: Annotated[Annotated[Annotated[Required[int], "a"], "b"], "c"]
