import typing
import uuid


class SymTableEntry:
    def reveal(self):
        raise Exception(f'Reveal not implemented: {self}')


class FuncDefSymbol(SymTableEntry):
    def __init__(self, name, callable):
        self.name = name
        self.args = list(callable.__args__[:-1])
        self.body = callable.__args__[-1]

    def reveal(self):
        return typing.Callable[self.args, self.body]


class ClassDefSymbol(SymTableEntry):
    def __init__(self, name, func_dict):
        self.name = name
        self.func_dict = func_dict

    def reveal(self):
        init_args = list(self.func_dict['__init__'].__args__[:-1])
        return typing.Callable[init_args, self.name]


class AliasSymbol(SymTableEntry):
    def __init__(self, name, origin):
        self.name = name
        self.origin = origin if name != origin else None

    def reveal(self):
        return self.origin


class AssignSymbol(SymTableEntry):
    def __init__(self, name, valueType):
        self.name = name
        self.valueType = valueType

    def reveal(self):
        return self.valueType
