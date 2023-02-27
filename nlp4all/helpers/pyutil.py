"""Helpers for python."""


class classproperty(object):
    def __init__(self, f):
        self.f = f

    def __get__(self, obj, owner):
        return self.f(owner)

# import typing as t

# T_co = t.TypeVar('T_co', covariant=True)


# class classproperty(property, t.Generic[T_co]):
#     """A decorator that behaves like @property as a classmethod."""
#     def __get__(self, _, owner_cls: type | None = None) -> t.Any:
#         if self.fget is not None:
#             return self.fget(owner_cls)
#         raise AttributeError("unreadable attribute")

#     def fget(self) -> t.Union[T_co, None]:
#         s = super(self.__class__, self)
#         if s.fget is not None:
#             return t.cast(T_co, s.fget(self))

#     def getter(self, fget: t.Callable[[t.Any], T_co]) -> 'classproperty[T_co]':
#         return t.cast(classproperty[T_co], super().getter(fget))

#     def setter(self, fset: t.Callable[[t.Any, T_co], None]) -> 'classproperty[T_co]':
#         return t.cast(classproperty[T_co], super().setter(fset))

#     def deleter(self, fdel: t.Callable[[t.Any], None]) -> 'classproperty[T_co]':
#         return t.cast(classproperty[T_co], super().deleter(fdel))
