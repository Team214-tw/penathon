import ast
import builtins
import typing

from . import Typer
from .TypeWrapper import TypeWrapper

seeker = Typer.Seeker()

class SymTable:
    def __init__(self, name, parent=None):
        self.parent = parent
        if self.parent:
            self.parent.childs[name] = self
        self.name = name
        self.env = {}
        self.childs = {}

    def add(self, name, t):
        self.env[name] = t

    def add_module(self, module_name, as_name=None, target=None):
        module_symtable = seeker.get_module_symtable(module_name)
        if target is not None: # load target only
            if as_name is None:
                self.env[target] = module_symtable.typeof(target)
            else:
                self.env[as_name] = module_symtable.typeof(target)
        elif as_name is None: # load entire module
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
            nameType = self.get(name)
            # refresh type variable for module which is already loaded in env
            if isinstance(nameType, TypeWrapper) and nameType.need_refresh:
                nameType.refresh()
            elif isinstance(nameType, SymTable):
                for k, v in nameType.env.items():
                    if isinstance(v, TypeWrapper) and v.need_refresh:
                        v.refresh()
            return nameType
        except:
            try:
                builtins_obj = seeker.get_builtins_obj(name)
                if isinstance(builtins_obj, SymTable):
                    return TypeWrapper(builtins_obj.env, class_name=name)
                else:
                    return builtins_obj
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

        for c in self.childs:
            self.childs[c].print(level + 1)

        print(f"{indent}-----{level}-----")

