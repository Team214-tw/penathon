import ast
import typing
from .Typer import Typer
from .SymTableEntry import *


class SymTable:
    def __init__(self, name, parent=None):
        self.seeker = Typer()
        self.parent = parent
        self.name = name
        if name != None and parent != None:
            self.parent.childs[name] = self
        self.childs = {}
        self.env = {}

    def add(self, node, inferedType=None):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                varName = target.id
                varSymbol = self.env.get(varName)

                if isinstance(varSymbol, AssignSymbol) and isinstance(varSymbol.reveal(), typing.TypeVar):
                    tv = varSymbol.valueType
                    tv.__init__(tv.__name__, bound=inferedType)
                else:
                    self.write(varName, AssignSymbol(varName, inferedType))

        elif isinstance(node, ast.Import):
            for i in node.names:
                asname = i.asname or i.name
                self.write(asname, AliasSymbol(asname, i.name))

        elif isinstance(node, ast.ImportFrom):
            for i in node.names:
                asname = i.asname or i.name
                func_name = f"{node.module}.{i.name}"
                try:
                    self.write(asname, self.seeker.get_type(func_name))
                except KeyError:
                    raise Exception(f"Type not found: {func_name}")

        elif isinstance(node, ast.FunctionDef):
            self.write(node.name, FuncDefSymbol(node.name, inferedType))

        elif isinstance(node, ast.ClassDef):
            self.env_ast[node.name] = node
            self.write(node.name, nodeInferred)

    def typeof(self, name):
        symbol = self.get(name)

        if symbol:
            return symbol.reveal()

        else:
            try:
                func_name = self._original_func_name(name)
                return self.seeker.get_type(func_name).reveal()
            except KeyError:
                raise Exception(f"Infer failed: {name}")

    def get(self, name):
        if name in self.env:
            return self.env[name]

        elif self.parent is not None:
            return self.parent.get(name)
        elif name.find("."):
            first = name.find(".")
            return self.env.get(self.env.get(name[:first]).reveal().name).symtable.get(name[first+1:])
        else:
            return None

    def write(self, name, symbol):
        self.env[name] = symbol

    # a.append => list.append
    def _original_func_name(self, name):
        splitted_name = name.split(".")
        for i, s in enumerate(splitted_name):
            symbol = self.get(s)
            if symbol:
                ts = symbol.reveal()
                # typing.Dict => dict
                try:
                    ts = ts.__origin__.__name__.lower()
                except AttributeError:
                    pass
                splitted_name[i] = ts
        return ".".join(splitted_name)

    def print(self):
        if self.parent:
            print(f"Symbol Table: {self.name}")
            print(f"Parent Table: {self.parent.name}")
        else:
            print(f"Symbol Table: {self.name}")

        for k, v in self.env.items():
            print(f"    {k}: {v.reveal()}")

        print("-----")

        for c in self.childs:
            self.childs[c].print()
