import ast
import astor
from typing import TypeVar
from copy import deepcopy


class CodeGenerator:
    def __init__(self):
        pass

    def gen_assign(self, e, t):
        e.annotation = self._get_type_name(t) 

    # def _gen_functionDef(self, e, t):
    #     args_type = t.__args__[:-1]
    #     body_type = t.__args__[-1]

    #     e_ = deepcopy(e)
    #     # generate function type info
    #     for i, arg in enumerate(args_type):
    #         e_.args.args[i].annotation = self._get_type_name(arg)
    #     e_.returns = self._get_type_name(body_type)

    #     self.scopeStk[-1]['body'].append(e_)

    def _get_type_name(self, t):
        # typing type
        if hasattr(t, "_name"):
            return ast.Name(t._name)
        # built-in type or TypeVar
        elif hasattr(t, "__name__"):
            return ast.Name(t.__name__)
