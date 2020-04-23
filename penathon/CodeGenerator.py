import ast
import astor
from typing import TypeVar
from copy import deepcopy


class CodeGenerator:
    def __init__(self):
        pass

    def gen_assign(self, e, symbol):
        e.annotation = self._get_type_name(symbol.reveal())

    def gen_functionDef(self, e, symbol):
        args_type = symbol.args
        body_type = symbol.body

        for i, arg in enumerate(args_type):
            e.args.args[i].annotation = self._get_type_name(arg)
        e.returns = self._get_type_name(body_type)

    def update_functionDef(self, env, name):
        e = env.astof(name)
        t = env.typeof(name)
        if isinstance(e, ast.FunctionDef):
            args_type = list(t.__args__[:-1])
            body_type = t.__args__[-1]

            for i, arg in enumerate(args_type):
                e.args.args[i].annotation = self._get_type_name(arg)
            e.returns = self._get_type_name(body_type)

    def _get_type_name(self, t):
        # class
        if isinstance(t, str):
            return ast.Name(t)
        # TypeVar
        if isinstance(t, TypeVar):
            return self._get_type_name(t.__bound__)
        # built-in type
        elif hasattr(t, "__name__"):
            return ast.Name(t.__name__)
        # typing type
        elif hasattr(t, "_name"):
            return ast.Name(str(t))
        else:
            return ast.Name('Any')
