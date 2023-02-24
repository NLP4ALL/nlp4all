"""Helpers for python."""

from ctypes import cast
import typing as t

T_co = t.TypeVar('T_co', covariant=True)


class classproperty(property, t.Generic[T_co]):
    """A decorator that behaves like @property as a classmethod."""
    def __get__(self: property, _, owner_cls: object) -> t.Any:
        if self.fget is not None:
            return self.fget(owner_cls)
        raise AttributeError("unreadable attribute")

    def fget(self) -> t.Union[T_co, None]:
        s = super(self.__class__, self)
        if s.fget is not None:
            return t.cast(T_co, s.fget(self))

    def getter(self, fget: t.Callable[[t.Any], T_co]) -> 'classproperty[T_co]':
        return t.cast(classproperty[T_co], super().getter(fget))

    def setter(self, fset: t.Callable[[t.Any, T_co], None]) -> 'classproperty[T_co]':
        return t.cast(classproperty[T_co], super().setter(fset))

    def deleter(self, fdel: t.Callable[[t.Any], None]) -> 'classproperty[T_co]':
        return t.cast(classproperty[T_co], super().deleter(fdel))
