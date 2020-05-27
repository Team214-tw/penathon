import ast
import builtins
import typing

from . import Typer
from .TypeWrapper import TypeWrapper

seeker = Typer.Seeker()

class SymTable:
    def __init__(self, name, parent=None):
        self.parent = parent
        self.name = name
        self.env = {}

    def add(self, name, t):
        self.env[name] = t

    def add_module(self, module_name, as_name=None):
        module_symtable = seeker.get_module_symtable(module_name)
        if as_name is None:
            module_name_splitted = module_name.split('.')
            cur = self
            for i in module_name_splitted[:-1]:
                if i not in cur.env:
                    cur.env[i] = SymTable(i, cur)
                cur = cur.env[i]
            cur.env[module_name_splitted[-1]] = module_symtable
        else:
            self.env[as_name] = module_symtable

    def typeof(self, name):
        try:
            return self.get(name)
        except:
            try:
                builtins_symtable = seeker.get_module_symtable('builtins')
                return builtins_symtable.get(name)
            except:
                raise Exception(f"{name} not found in symbol table: {self._get_symtable_name()}")

    def get(self, name):
        if name in self.env:
            return self.env[name]
        elif self.parent is not None:
            return self.parent.get(name)
        else:
            raise Exception(f"{name} not found in symbol table: {self._get_symtable_name()}")

    def _get_symtable_name(self):
        if self.parent == None:
            return self.name
        else:
            return f"{self.parent._get_symtable_name()}.{self.name}"

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
                print(f"{indent}    {k}:")
                v.print(level + 1)
            else:
                print(f"{indent}    {k}: {TypeWrapper.reveal_type_var(v.reveal())}")

        print(f"{indent}-----{level}-----")

