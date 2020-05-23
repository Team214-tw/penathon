import typing
import uuid

class Class(object):
    name = ""
    pass


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
    def __init__(self, name, symtable):
        self.name = name
        self.symtable = symtable

    def reveal(self):
        init_args = list(self.symtable.get('__init__').args[1:])
        Name = self.name

        class tmpclass(Class):
            name = Name

        return typing.Callable[init_args, tmpclass]


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
