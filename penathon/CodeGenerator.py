import ast
import astor
from typing import TypeVar, Union, Callable, List
from copy import deepcopy
<<<<<<< HEAD
from .SymTableEntry import Class
=======
from .Helper import Helper
>>>>>>> 887d1f9... Organize code

class CodeGenerator(ast.NodeTransformer):
    def __init__(self):
        self.symbol_table = None

    def visit_Assign(self, node):
        return [
            ast.AnnAssign(
                target=t,
                value=node.value,
                annotation=self.get_type_ast_node(self.search(t.id)),
                lineno=node.lineno,
                simple=1,
            )
            for t in node.targets
        ]

    def visit_FunctionDef(self, node):
        t = self.search(node.name)
        args_type = list(t.__args__[:-1])
        body_type = t.__args__[-1]

        for i, arg in enumerate(args_type):
            node.args.args[i].annotation = self.get_type_ast_node(arg)
        node.returns = self.get_type_ast_node(body_type)

        if (isinstance(node, ast.FunctionDef)):
            self.symbol_table = self.symbol_table.childs[node.name]

        ast.NodeTransformer.generic_visit(self, node)

        if (isinstance(node, ast.FunctionDef)):
            self.symbol_table = self.symbol_table.parent

        return node

    def gen(self, tree, symbol_table):
        self.symbol_table = symbol_table
        return self.visit(tree)

    def search(self, name):
        return self.symbol_table.get(name).reveal()

    @staticmethod
    def get_type_ast_node(t):
        return ast.Name(CodeGenerator.reveal_inferred_type(t))

    @staticmethod
    def reveal_inferred_type(t): # return string
        # class
        if isinstance(t, str):
            return t
        # TypeVar
        elif isinstance(t, TypeVar):
            return CodeGenerator.reveal_inferred_type(Helper.reveal_type_var(t))
        # built-in type
        elif hasattr(t, "__name__"):
            return t.__name__
        # typing type
        elif hasattr(t, "_name"):
            return str(Helper.reveal_type_var(t))  # TypeVar may inside typing type
        else:
            return 'Any'
