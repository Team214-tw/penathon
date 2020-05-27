import ast
import typing


class SymTable:
    def __init__(self, name, parent=None):
        self.parent = parent
        self.name = name
        self.env = {}

    def add(self, name, t):
        self.env[name] = t

    def typeof(self, name):
        t = self.get(name)
        if t is None:
            raise Exception(f"{name} not found in symbol table: {self._get_symtable_name()}")
        return t

    def get(self, name):
        if name in self.env:
            return self.env[name]
        elif self.parent is not None:
            return self.parent.get(name)
        else:
            return None

    def _get_symtable_name(self):
        if self.parent == None:
            return self.name
        else:
            return f"{self.parent._get_symtable_name()}.{self.name}"

    # a.append => list.append
    # def _original_func_name(self, name):
    #     splitted_name = name.split(".")
    #     for i, s in enumerate(splitted_name):
    #         symbol = self.get(s)
    #         if symbol:
    #             ts = symbol.reveal()
    #             # typing.Dict => dict
    #             try:
    #                 ts = ts.__origin__.__name__.lower()
    #             except AttributeError:
    #                 pass
    #             splitted_name[i] = ts
    #     return ".".join(splitted_name)

    def print(self, level=0):
        indent = '    ' * level
        print(f"{indent}-----{level}-----")

        if self.parent:
            print(f"{indent}Symbol Table: {self.name}")
            print(f"{indent}Parent Table: {self.parent.name}")
        else:
            print(f"{indent}Symbol Table: {self.name}")

        for k, v in self.env.items():
            if isinstance(v, SymTable):
                v.print(level + 1)
            else:
                print(f"{indent}    {k}: {v.reveal()}")

        print(f"{indent}-----{level}-----")

