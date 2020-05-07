import ast
from typing import TypeVar
from .SymTableEntry import *


class Helper:
    def __init__(self):
        self.tvid = 0

    @staticmethod
    def type_to_symbol(name, t):
        if isinstance(t, dict):
            return ClassDefSymbol(name, t)
        elif Helper.is_callable(t):
            return FuncDefSymbol(name, t)
        else:
            return AssignSymbol(name, t)

    # -------
    # TypeVar
    def _get_tvid(self):
        self.tvid += 1
        return f"T{str(self.tvid)}"

    def create_type_var(self):
        return TypeVar(self._get_tvid())

    @staticmethod
    def bound_type_var(tv, t):
        tv.__init__(tv.__name__, bound=t)

    # --------------------
    # conditional checking
    @staticmethod
    def is_callable(t):  # caveat: can't use isinstance
        return hasattr(t, '_name') and t._name == 'Callable'

    @staticmethod
    def can_coerce(p, q):  # check p can coerce to q
        if p is int and q is float:
            return True

        elif p is int and q is complex:
            return True

        elif p is float and q is complex:
            return True

        else:
            return False

    # ------
    # reveal
    @staticmethod
    def reveal_real_type(t):
        if isinstance(t, TypeVar):
            return t.__bound__
        else:
            return t

    # return original type of typing type. e.g. typing.Dict => dict
    @staticmethod
    def reveal_original_type(t):
        t = Helper.reveal_real_type(t)
        try:
            return t.__origin__
        except AttributeError:
            return t

    @staticmethod
    def reveal_real_func_name(func):
        # a.b.c()
        if isinstance(func, ast.Attribute):
            return f"{Helper.reveal_real_func_name(func.value)}.{func.attr}"
        # a()
        elif isinstance(func, ast.Name):
            return func.id
        # [].append
        else:
            return type(func).__name__.lower()

    @staticmethod
    def reveal_magic_func(op):
        magics = {
            "Add": "__add__",
            "Sub": "__sub__",
            "Mult": "__mul__",
            "Div": "__div__",
            "Mod": "__mod__",
            "Or": "__or__",
            "And": "__and__",
        }
        return magics[type(op).__name__]
