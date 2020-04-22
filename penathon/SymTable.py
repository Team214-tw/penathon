import ast
import typing
from .Typer import Typer
from .SymTableEntry import *


class SymTable:
    def __init__(self, parent=None):
        self.seeker = Typer()
        self.parent = parent
        self.env_ast = {}
        self.env = {}

    def add(self, node, nodeInferred=None):
        if isinstance(node, ast.AnnAssign):
            varName = node.target.id
            varSymbol = self.env.get(varName)

            if isinstance(varSymbol, AssignSymbol) and isinstance(varSymbol.reveal(), typing.TypeVar):
                tv = varSymbol.valueType
                tv.__init__(tv.__name__, bound=nodeInferred.reveal())
            else:
                self.write(varName, nodeInferred)

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
            self.write(node.name, nodeInferred)

    def typeof(self, name):
        if name in self.env:
            return self.env[name].reveal()

        # find upper level's symbol table
        elif self.parent is not None:
            return self.parent.typeof(name)

        else:
            try:
                func_name = self._original_func_name(name)
                return self.seeker.get_type(func_name).reveal()
            except KeyError:
                raise Exception(f"Infer failed: {name}")

    def write(self, name, symbol):
        self.env[name] = symbol

    # a.append => list.append
    def _original_func_name(self, name):
        splitted_name = name.split(".")
        for i, s in enumerate(splitted_name):
            if s in self.env:
                ts = self.env[s].reveal()
                # typing.Dict => dict
                try:
                    ts = ts.__origin__.__name__.lower()
                except AttributeError:
                    pass
                splitted_name[i] = ts
        return ".".join(splitted_name)
